/**
 * ArchitectAgent – converts an issue into a concrete change plan.
 * Now with REAL LLM reasoning over code context & goals.
 */

import { DiagnosticsIssue } from "./diagnosticsAgent";
import { llmClient, LLMMessage } from "../core/llmClient";
import { CodeContextBuilder } from "../core/codeContextBuilder";
import { Logger } from "../core/logger";
import { query } from "../integrations/db";
import { Goal } from "../models/pakModels";

const log = new Logger("ArchitectAgent");

export interface ChangePlan {
    id: string;
    issueId: string;
    title: string;
    description: string;
    tier: "tactical" | "operational" | "strategic";
    targetModuleIds: string[];
    successCriteria: Record<string, unknown>;
    approach: string;
    alternatives: string[];
    risks: string[];
    estimatedImpact: string;
}

export class ArchitectAgent {
    private contextBuilder: CodeContextBuilder;

    constructor() {
        this.contextBuilder = new CodeContextBuilder();
    }

    async createPlan(issue: DiagnosticsIssue): Promise<ChangePlan> {
        log.info("Creating change plan for issue", { issueId: issue.id });

        // 1. Get context from codebase
        const codeContext = await this.contextBuilder.buildContext({
            targetModuleIds: issue.suggestedTargetModuleIds,
            maxTokens: 5000,
            includeTests: false,
            includeDependencies: true
        });

        // 2. Get active goals for alignment
        const activeGoals = await this.getActiveGoals();

        // 3. Generate plan with LLM
        const plan = await this.generatePlan(issue, codeContext, activeGoals);

        log.info("Plan created", { planId: plan.id, tier: plan.tier });

        return plan;
    }

    private async getActiveGoals(): Promise<Goal[]> {
        try {
            const goals = await query<Goal>("SELECT * FROM goals WHERE status = 'active' LIMIT 5");
            return goals;
        } catch (error) {
            log.warn("Failed to fetch goals, continuing without them", error);
            return [];
        }
    }

    private async generatePlan(
        issue: DiagnosticsIssue,
        codeContext: any,
        goals: Goal[]
    ): Promise<ChangePlan> {
        const messages: LLMMessage[] = [
            {
                role: "system",
                content: this.getArchitectSystemPrompt()
            },
            {
                role: "user",
                content: this.buildPlanningPrompt(issue, codeContext, goals)
            }
        ];

        const response = await llmClient.complete(messages, {
            temperature: 0.4,
            maxTokens: 3072,
            provider: "openai"
        });

        return this.parsePlanFromResponse(response.content, issue);
    }

    private getArchitectSystemPrompt(): string {
        return `You are a system architect for autonomous code improvement.

Your role:
1. Analyze problems holistically using root cause analysis
2. Design minimal, effective solutions that address the core issue
3. Consider long-term maintainability and technical debt
4. Align changes with system goals and values
5. Identify dependencies, risks, and alternative approaches

Think step-by-step:
1. **Root Cause Analysis:** What is the underlying problem?
2. **Alternative Approaches:** What are 2-3 different ways to solve this?
3. **Selected Approach:** Which approach is best and why?
4. **Success Criteria:** How will we know this worked?
5. **Risks:** What could go wrong?
6. **Rollback Strategy:** How do we undo this if needed?

Output format:
TITLE: Brief, descriptive title
APPROACH: Detailed description of selected approach
ALTERNATIVES: List alternative approaches considered
TARGET_MODULES: Comma-separated module IDs
SUCCESS_CRITERIA: Measurable outcomes (format: key=value)
RISKS: Potential risks and mitigations
IMPACT: Expected impact (low/medium/high)
TIER: tactical/operational/strategic`;
    }

    private buildPlanningPrompt(
        issue: DiagnosticsIssue,
        codeContext: any,
        goals: Goal[]
    ): string {
        const goalsContext = goals.length > 0
            ? goals.map(g => `- ${g.title}: ${g.description}`).join("\n")
            : "No active goals available";

        const contextSummary = this.contextBuilder.formatForLLM(codeContext);

        return `# Issue to Address

**ID:** ${issue.id}
**Description:** ${issue.description}
**Severity:** ${issue.severity}
**Suggested Modules:** ${issue.suggestedTargetModuleIds.join(", ")}

---

# Active System Goals

${goalsContext}

---

# Code Context

${contextSummary.substring(0, 4000)} ${contextSummary.length > 4000 ? "...(truncated)" : ""}

---

**Task:** Create a comprehensive change plan to address this issue.

Consider:
- How does this align with system goals?
- What is the minimal effective solution?
- What are the risks and trade-offs?
- How do we measure success?

Generate the plan now:`;
    }

    private parsePlanFromResponse(content: string, issue: DiagnosticsIssue): ChangePlan {
        const extract = (pattern: RegExp, defaultValue: string = ""): string => {
            const match = content.match(pattern);
            return match ? match[1].trim() : defaultValue;
        };

        const title = extract(/TITLE:\s*(.+)/i, `Address: ${issue.description}`);
        const approach = extract(/APPROACH:\s*([\s\S]+?)(?=ALTERNATIVES:|TARGET_MODULES:|$)/i,
            `Plan automatically generated for issue: ${issue.description}`);

        const alternativesText = extract(/ALTERNATIVES:\s*([\s\S]+?)(?=TARGET_MODULES:|SUCCESS_CRITERIA:|$)/i);
        const alternatives = alternativesText
            ? alternativesText.split("\n").map(l => l.trim()).filter(l => l.length > 0 && l !== "-")
            : [];

        const targetModulesText = extract(/TARGET_MODULES:\s*(.+)/i, issue.suggestedTargetModuleIds.join(", "));
        const targetModuleIds = targetModulesText.split(",").map(m => m.trim());

        const successCriteriaText = extract(/SUCCESS_CRITERIA:\s*([\s\S]+?)(?=RISKS:|IMPACT:|$)/i);
        const successCriteria = this.parseSuccessCriteria(successCriteriaText, issue);

        const risksText = extract(/RISKS:\s*([\s\S]+?)(?=IMPACT:|TIER:|$)/i);
        const risks = risksText
            ? risksText.split("\n").map(l => l.trim()).filter(l => l.length > 0)
            : [];

        const impact = extract(/IMPACT:\s*(.+)/i, "medium");
        const tierText = extract(/TIER:\s*(.+)/i, "");
        const tier = this.determineTier(tierText, issue.severity);

        return {
            id: `plan_${issue.id}_${Date.now()}`,
            issueId: issue.id,
            title,
            description: approach,
            tier,
            targetModuleIds,
            successCriteria,
            approach,
            alternatives,
            risks,
            estimatedImpact: impact
        };
    }

    private parseSuccessCriteria(text: string, issue: DiagnosticsIssue): Record<string, unknown> {
        const criteria: Record<string, unknown> = {};

        if (!text || text.length === 0) {
            // Default criteria based on issue severity
            return {
                maxErrorRate: 0.02,
                minConversionRate: 0.2,
                maxResponseTimeMs: 500
            };
        }

        // Parse format like "errorRate < 2%, latency < 500ms"
        const lines = text.split("\n");
        for (const line of lines) {
            const match = line.match(/(\w+)\s*[:<>=]+\s*([0-9.]+)(%|ms|s)?/i);
            if (match) {
                const [, key, value, unit] = match;
                let numValue = parseFloat(value);

                // Convert percentages
                if (unit === "%") {
                    numValue = numValue / 100;
                }

                criteria[key] = numValue;
            }
        }

        return criteria;
    }

    private determineTier(tierText: string, severity: string): ChangePlan["tier"] {
        if (tierText) {
            const lower = tierText.toLowerCase();
            if (lower.includes("strategic")) return "strategic";
            if (lower.includes("operational")) return "operational";
            if (lower.includes("tactical")) return "tactical";
        }

        // Fall back to severity-based determination
        if (severity === "critical" || severity === "high") {
            return "operational";
        }
        return "tactical";
    }

    /**
     * Validate plan against goals and constraints
     */
    async validatePlan(plan: ChangePlan, goals: Goal[]): Promise<{ isValid: boolean; issues: string[] }> {
        const issues: string[] = [];

        // Check if plan aligns with at least one goal
        if (goals.length > 0) {
            const aligned = goals.some(goal =>
                plan.description.toLowerCase().includes(goal.title.toLowerCase()) ||
                plan.title.toLowerCase().includes(goal.title.toLowerCase())
            );

            if (!aligned) {
                issues.push("Plan does not clearly align with any active system goal");
            }
        }

        // Check for empty target modules
        if (plan.targetModuleIds.length === 0) {
            issues.push("No target modules specified");
        }

        // Check for missing success criteria
        if (Object.keys(plan.successCriteria).length === 0) {
            issues.push("No success criteria defined");
        }

        return {
            isValid: issues.length === 0,
            issues
        };
    }

    /**
     * Refine plan based on validation issues
     */
    async refinePlan(plan: ChangePlan, issues: string[]): Promise<ChangePlan> {
        const messages: LLMMessage[] = [
            {
                role: "system",
                content: "You are a system architect. Refine the plan to address the identified issues."
            },
            {
                role: "user",
                content: `Original Plan:
${JSON.stringify(plan, null, 2)}

Issues:
${issues.join("\n")}

Generate an improved plan that addresses these issues.`
            }
        ];

        const response = await llmClient.complete(messages, {
            temperature: 0.3,
            maxTokens: 2048
        });

        // Parse refined plan (keeping original issue ref)
        const issueRef: DiagnosticsIssue = {
            id: plan.issueId,
            description: plan.description,
            severity: "medium",
            suggestedTargetModuleIds: plan.targetModuleIds
        };

        return this.parsePlanFromResponse(response.content, issueRef);
    }
}
