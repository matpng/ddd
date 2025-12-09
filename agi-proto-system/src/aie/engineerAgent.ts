/**
 * EngineerAgent – creates code diffs based on change plans.
 * Now with REAL LLM integration for intelligent code generation.
 */

import { CodeDiff } from "../types";
import { ChangePlan } from "./architectAgent";
import { llmClient, LLMMessage } from "../core/llmClient";
import { CodeContextBuilder } from "../core/codeContextBuilder";
import { Logger } from "../core/logger";

const log = new Logger("EngineerAgent");

interface CritiqueResult {
    hasIssues: boolean;
    issues: string[];
    suggestions: string[];
}

export class EngineerAgent {
    private contextBuilder: CodeContextBuilder;

    constructor() {
        this.contextBuilder = new CodeContextBuilder();
    }

    async proposeDiff(plan: ChangePlan): Promise<CodeDiff> {
        log.info("Generating code diff for plan", { planId: plan.id });

        // 1. Gather code context
        const codeContext = await this.contextBuilder.buildContext({
            targetModuleIds: plan.targetModuleIds,
            maxTokens: 6000,
            includeTests: true,
            includeDependencies: true
        });

        const formattedContext = this.contextBuilder.formatForLLM(codeContext);

        // 2. Generate initial diff
        let diff = await this.generateDiff(plan, formattedContext);

        // 3. Self-critique
        const critique = await this.critiqueDiff(diff, plan);

        // 4. Refine if needed
        if (critique.hasIssues && critique.issues.length > 0) {
            log.info("Refining diff based on self-critique");
            diff = await this.refineDiff(diff, plan, critique, formattedContext);
        }

        log.info("Diff generation complete", {
            filesTouched: diff.filesTouched.length,
            hasIssues: critique.hasIssues
        });

        return diff;
    }

    private async generateDiff(plan: ChangePlan, context: string): Promise<CodeDiff> {
        const messages: LLMMessage[] = [
            {
                role: "system",
                content: this.getSystemPrompt()
            },
            {
                role: "user",
                content: this.buildEngineeringPrompt(plan, context)
            }
        ];

        const response = await llmClient.complete(messages, {
            temperature: 0.2,
            maxTokens: 4096,
            provider: "openai"
        });

        return this.parseDiffFromResponse(response.content, plan);
    }

    private getSystemPrompt(): string {
        return `You are an expert software engineer specializing in autonomous code improvement.

Your responsibilities:
1. Generate MINIMAL, FOCUSED diffs that address the specific issue
2. Maintain code quality and consistency with existing patterns
3. Include comprehensive test coverage modifications
4. Consider edge cases and error handling
5. Document non-obvious changes with comments

Constraints:
- Never touch authentication, payment, or security-critical code
- Always maintain backward compatibility unless explicitly requested
- Prefer refactoring over rewriting
- Follow existing code style and patterns
- Keep changes atomic and reviewable

Output Format:
Return a valid unified diff format (git diff style) for each file that needs modification.
Use this structure:

FILE: path/to/file.ts
\`\`\`diff
diff --git a/path/to/file.ts b/path/to/file.ts
index 1111111..2222222 100644
--- a/path/to/file.ts
+++ b/path/to/file.ts
@@ -linenum,count +linenum,count @@
 context line
-removed line
+added line
 context line
\`\`\`

SUMMARY: Brief description of changes

After all files, include:
FILES_TOUCHED: comma-separated list of file paths`;
    }

    private buildEngineeringPrompt(plan: ChangePlan, context: string): string {
        return `# Change Plan

**Title:** ${plan.title}
**Description:** ${plan.description}
**Tier:** ${plan.tier}
**Target Modules:** ${plan.targetModuleIds.join(", ")}

**Success Criteria:**
${JSON.stringify(plan.successCriteria, null, 2)}

---

${context}

---

**Task:** Generate a precise, minimal code diff to implement this plan.

Think step-by-step:
1. What is the root cause we're addressing?
2. What is the minimal change needed?
3. What tests need to be updated?
4. What edge cases should be considered?
5. Are there any side effects?

Generate the diff now:`;
    }

    private parseDiffFromResponse(content: string, plan: ChangePlan): CodeDiff {
        // Extract files touched
        const filesTouchedMatch = content.match(/FILES_TOUCHED:\s*(.+)/i);
        const filesTouched = filesTouchedMatch
            ? filesTouchedMatch[1].split(",").map(f => f.trim())
            : plan.targetModuleIds.map(id => `src/${id}.ts`);

        // Extract summary
        const summaryMatch = content.match(/SUMMARY:\s*(.+)/i);
        const summary = summaryMatch
            ? summaryMatch[1].trim()
            : `Auto patch for plan ${plan.id}`;

        // Extract diff patches (everything between ```diff markers)
        const diffMatches = content.matchAll(/```diff\n([\s\S]*?)```/g);
        const patches: string[] = [];

        for (const match of diffMatches) {
            patches.push(match[1].trim());
        }

        const patch = patches.length > 0
            ? patches.join("\n\n")
            : this.generateFallbackPatch(plan);

        return {
            summary,
            patch,
            filesTouched,
            riskLevel: "safe" // Will be overridden by RiskClassifier
        };
    }

    private generateFallbackPatch(plan: ChangePlan): string {
        // Fallback if LLM didn't generate proper diff
        return `diff --git a/src/placeholder.ts b/src/placeholder.ts
index 1111111..2222222 100644
--- a/src/placeholder.ts
+++ b/src/placeholder.ts
@@ -1,1 +1,2 @@
+// Auto-improvement: ${plan.title}
 // Plan ID: ${plan.id}`;
    }

    private async critiqueDiff(diff: CodeDiff, plan: ChangePlan): Promise<CritiqueResult> {
        const messages: LLMMessage[] = [
            {
                role: "system",
                content: "You are a senior code reviewer. Identify potential issues, bugs, and improvement opportunities."
            },
            {
                role: "user",
                content: `Review this proposed diff:

**Plan:** ${plan.description}

**Diff:**
${diff.patch}

**Files Touched:** ${diff.filesTouched.join(", ")}

Analyze for:
1. Correctness - Does it solve the problem?
2. Safety - Any security or stability concerns?
3. Quality - Follows best practices?
4. Completeness - Are tests included?
5. Side effects - Any unintended consequences?

Output format:
ISSUES: list critical problems (or "none")
SUGGESTIONS: list improvements (or "none")`
            }
        ];

        const response = await llmClient.complete(messages, {
            temperature: 0.3,
            maxTokens: 2048,
            provider: "openai"
        });

        return this.parseCritique(response.content);
    }

    private parseCritique(content: string): CritiqueResult {
        const issuesMatch = content.match(/ISSUES:\s*(.+?)(?=SUGGESTIONS:|$)/is);
        const suggestionsMatch = content.match(/SUGGESTIONS:\s*(.+)/is);

        const issuesText = issuesMatch ? issuesMatch[1].trim() : "";
        const suggestionsText = suggestionsMatch ? suggestionsMatch[1].trim() : "";

        const hasIssues = !issuesText.toLowerCase().includes("none") && issuesText.length > 0;

        const issues = hasIssues
            ? issuesText.split("\n").map(l => l.trim()).filter(l => l.length > 0)
            : [];

        const suggestions = !suggestionsText.toLowerCase().includes("none")
            ? suggestionsText.split("\n").map(l => l.trim()).filter(l => l.length > 0)
            : [];

        return {
            hasIssues,
            issues,
            suggestions
        };
    }

    private async refineDiff(
        originalDiff: CodeDiff,
        plan: ChangePlan,
        critique: CritiqueResult,
        context: string
    ): Promise<CodeDiff> {
        const messages: LLMMessage[] = [
            {
                role: "system",
                content: this.getSystemPrompt()
            },
            {
                role: "user",
                content: `# Original Plan
${plan.description}

# Original Diff
${originalDiff.patch}

# Critique Issues
${critique.issues.join("\n")}

# Suggestions
${critique.suggestions.join("\n")}

# Code Context
${context}

**Task:** Generate an IMPROVED diff that addresses the critique issues while maintaining the original goal.`
            }
        ];

        const response = await llmClient.complete(messages, {
            temperature: 0.2,
            maxTokens: 4096,
            provider: "openai"
        });

        return this.parseDiffFromResponse(response.content, plan);
    }
}
