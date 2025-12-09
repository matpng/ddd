/**
 * Reflection Agent - Analyzes experiences to extract insights and lessons.
 * Enables the system to learn from both successes and failures.
 */

import { llmClient, LLMMessage } from "../core/llmClient";
import { Experience, Reflection, Lesson } from "../core/experienceStore";
import { Logger } from "../core/logger";
import { v4 as uuid } from "uuid";

const log = new Logger("ReflectionAgent");

export class ReflectionAgent {
    /**
     * Reflect on an experience to extract insights
     */
    async reflect(experience: Experience): Promise<Reflection> {
        log.info("Reflecting on experience", { experienceId: experience.id, type: experience.type });

        const messages: LLMMessage[] = [
            {
                role: "system",
                content: this.getReflectionSystemPrompt()
            },
            {
                role: "user",
                content: this.buildReflectionPrompt(experience)
            }
        ];

        const response = await llmClient.complete(messages, {
            temperature: 0.6,
            maxTokens: 2048,
            provider: "openai"
        });

        return this.parseReflection(response.content);
    }

    /**
     * Extract actionable lessons from an experience
     */
    async extractLessons(experience: Experience, reflection: Reflection): Promise<Lesson[]> {
        log.info("Extracting lessons", { experienceId: experience.id });

        const messages: LLMMessage[] = [
            {
                role: "system",
                content: "You are an AI system that learns from experience. Extract specific, actionable lessons that can improve future decision-making."
            },
            {
                role: "user",
                content: this.buildLessonExtractionPrompt(experience, reflection)
            }
        ];

        const response = await llmClient.complete(messages, {
            temperature: 0.5,
            maxTokens: 1536,
            provider: "openai"
        });

        return this.parseLessons(response.content, experience.id);
    }

    /**
     * Analyze multiple experiences to identify patterns
     */
    async identifyPatterns(experiences: Experience[]): Promise<{
        successPatterns: string[];
        failurePatterns: string[];
        insights: string[];
    }> {
        log.info("Identifying patterns across experiences", { count: experiences.length });

        if (experiences.length === 0) {
            return { successPatterns: [], failurePatterns: [], insights: [] };
        }

        const messages: LLMMessage[] = [
            {
                role: "system",
                content: "You are a pattern recognition expert. Analyze experiences to identify recurring patterns and insights."
            },
            {
                role: "user",
                content: this.buildPatternAnalysisPrompt(experiences)
            }
        ];

        const response = await llmClient.complete(messages, {
            temperature: 0.4,
            maxTokens: 2048,
            provider: "openai"
        });

        return this.parsePatterns(response.content);
    }

    /**
     * Compare current situation with past similar experiences
     */
    async compareWithPast(
        currentContext: any,
        pastExperiences: Experience[]
    ): Promise<{
        similarities: string[];
        differences: string[];
        recommendations: string[];
    }> {
        log.info("Comparing with past experiences", { pastCount: pastExperiences.length });

        const messages: LLMMessage[] = [
            {
                role: "system",
                content: "Compare the current situation with past experiences to provide informed recommendations."
            },
            {
                role: "user",
                content: `Current Context:
${JSON.stringify(currentContext, null, 2)}

Past Experiences:
${pastExperiences.map(e => this.summarizeExperience(e)).join("\n\n")}

Identify:
1. SIMILARITIES: What is similar to past experiences?
2. DIFFERENCES: What is different or unique?
3. RECOMMENDATIONS: What should we do based on past learnings?`
            }
        ];

        const response = await llmClient.complete(messages, {
            temperature: 0.5,
            maxTokens: 1536
        });

        return this.parseComparison(response.content);
    }

    // Private helper methods

    private getReflectionSystemPrompt(): string {
        return `You are a reflective AI system analyzing past experiences to extract insights.

Your task:
1. Identify what went well and why
2. Identify what could be improved
3. Note any unexpected outcomes
4. Connect this experience to broader patterns
5. Assess confidence in the analysis

Be honest about failures and celebrate successes. Focus on actionable insights.

Output format:
SUMMARY: Brief overall reflection
WHAT_WORKED: List of positive outcomes and why
WHAT_FAILED: List of issues and root causes
UNEXPECTED: Any surprising outcomes
CONNECTIONS: Links to other concepts or experiences
CONFIDENCE: 0.0-1.0 score of confidence in this analysis`;
    }

    private buildReflectionPrompt(experience: Experience): string {
        let prompt = `# Experience to Reflect On\n\n`;
        prompt += `**Type:** ${experience.type}\n`;
        prompt += `**Timestamp:** ${experience.timestamp}\n\n`;

        if (experience.context.issue) {
            prompt += `## Issue\n`;
            prompt += `${experience.context.issue.description} (Severity: ${experience.context.issue.severity})\n\n`;
        }

        if (experience.context.plan) {
            prompt += `## Plan\n`;
            prompt += `${experience.context.plan.title}\n`;
            prompt += `${experience.context.plan.description}\n\n`;
        }

        if (experience.context.diff) {
            prompt += `## Changes Made\n`;
            prompt += `${experience.context.diff.summary}\n`;
            prompt += `Files: ${experience.context.diff.filesTouched.join(", ")}\n`;
            prompt += `Risk Level: ${experience.context.diff.riskLevel}\n\n`;
        }

        prompt += `## Action\n`;
        prompt += `${experience.action.attempted}\n`;
        if (experience.action.deployed) {
            prompt += `Deployed: Yes (${experience.action.branchName})\n`;
        }
        prompt += `\n`;

        prompt += `## Outcome\n`;
        prompt += `Status: ${experience.outcome.status}\n`;
        if (experience.outcome.reason) {
            prompt += `Reason: ${experience.outcome.reason}\n`;
        }
        if (experience.outcome.metricsImpact) {
            prompt += `\n**Metrics Impact:**\n`;
            const m = experience.outcome.metricsImpact;
            prompt += `- Error Rate: ${(m.errorRateBefore * 100).toFixed(2)}% → ${(m.errorRateAfter * 100).toFixed(2)}%\n`;
            prompt += `- Latency: ${m.latencyBefore}ms → ${m.latencyAfter}ms\n`;
        }

        prompt += `\n---\n\nReflect on this experience now:`;
        return prompt;
    }

    private buildLessonExtractionPrompt(experience: Experience, reflection: Reflection): string {
        return `# Experience
Type: ${experience.type}
Context: ${JSON.stringify(experience.context, null, 2)}
Outcome: ${JSON.stringify(experience.outcome, null, 2)}

# Reflection
${reflection.summary}

What worked: ${reflection.whatWorked.join(", ")}
What failed: ${reflection.whatFailed.join(", ")}

---

Extract 3-5 specific, actionable lessons from this experience.

For each lesson, provide:
LESSON:
Category: (e.g., "code_quality", "risk_assessment", "deployment", "monitoring")
Insight: Specific, actionable insight
Applicability: When/where this lesson applies
Confidence: 0.0-1.0

Output one lesson per block.`;
    }

    private buildPatternAnalysisPrompt(experiences: Experience[]): string {
        let prompt = `# Experiences to Analyze\n\n`;

        experiences.forEach((exp, idx) => {
            prompt += `## Experience ${idx + 1}\n`;
            prompt += `Type: ${exp.type}\n`;
            if (exp.context.issue) {
                prompt += `Issue: ${exp.context.issue.description}\n`;
            }
            if (exp.outcome.reason) {
                prompt += `Outcome: ${exp.outcome.status} - ${exp.outcome.reason}\n`;
            } else {
                prompt += `Outcome: ${exp.outcome.status}\n`;
            }
            if (exp.reflection) {
                prompt += `Reflection: ${exp.reflection.summary}\n`;
            }
            prompt += `\n`;
        });

        prompt += `---\n\nAnalyze these experiences and identify:\n\n`;
        prompt += `SUCCESS_PATTERNS: What consistently leads to success?\n`;
        prompt += `FAILURE_PATTERNS: What consistently leads to failure?\n`;
        prompt += `INSIGHTS: Broader insights from the data\n`;

        return prompt;
    }

    private parseReflection(content: string): Reflection {
        const extract = (pattern: RegExp): string => {
            const match = content.match(pattern);
            return match ? match[1].trim() : "";
        };

        const extractList = (pattern: RegExp): string[] => {
            const match = content.match(pattern);
            if (!match) return [];
            return match[1]
                .split("\n")
                .map(l => l.trim())
                .filter(l => l.length > 0 && !l.startsWith("//"));
        };

        const summary = extract(/SUMMARY:\s*(.*)/i);
        const whatWorked = extractList(/WHAT_WORKED:\s*([\s\S]+?)(?=WHAT_FAILED:|UNEXPECTED:|$)/i);
        const whatFailed = extractList(/WHAT_FAILED:\s*([\s\S]+?)(?=UNEXPECTED:|CONNECTIONS:|$)/i);
        const unexpectedOutcomes = extractList(/UNEXPECTED:\s*([\s\S]+?)(?=CONNECTIONS:|CONFIDENCE:|$)/i);
        const connections = extractList(/CONNECTIONS:\s*([\s\S]+?)(?=CONFIDENCE:|$)/i);

        const confidenceText = extract(/CONFIDENCE:\s*([0-9.]+)/i);
        const confidence = confidenceText ? parseFloat(confidenceText) : 0.5;

        return {
            summary,
            whatWorked,
            whatFailed,
            unexpectedOutcomes,
            connections,
            confidence: Math.max(0, Math.min(1, confidence))
        };
    }

    private parseLessons(content: string, experienceId: string): Lesson[] {
        const lessons: Lesson[] = [];

        // Split by LESSON: markers
        const lessonBlocks = content.split(/LESSON:/i).slice(1);

        for (const block of lessonBlocks) {
            const category = this.extractField(block, /Category:\s*(.+)/i) || "general";
            const insight = this.extractField(block, /Insight:\s*(.+)/i) || "";
            const applicability = this.extractField(block, /Applicability:\s*(.+)/i) || "";
            const confidenceText = this.extractField(block, /Confidence:\s*([0-9.]+)/i);
            const confidence = confidenceText ? parseFloat(confidenceText) : 0.7;

            if (insight) {
                lessons.push({
                    id: uuid(),
                    category,
                    insight,
                    applicability,
                    confidence: Math.max(0, Math.min(1, confidence)),
                    relatedExperiences: [experienceId]
                });
            }
        }

        return lessons;
    }

    private parsePatterns(content: string): {
        successPatterns: string[];
        failurePatterns: string[];
        insights: string[];
    } {
        const extractList = (pattern: RegExp): string[] => {
            const match = content.match(pattern);
            if (!match) return [];
            return match[1]
                .split("\n")
                .map(l => l.trim().replace(/^[-*]\s*/, ""))
                .filter(l => l.length > 0);
        };

        return {
            successPatterns: extractList(/SUCCESS_PATTERNS:\s*([\s\S]+?)(?=FAILURE_PATTERNS:|INSIGHTS:|$)/i),
            failurePatterns: extractList(/FAILURE_PATTERNS:\s*([\s\S]+?)(?=INSIGHTS:|$)/i),
            insights: extractList(/INSIGHTS:\s*([\s\S]+?)$/i)
        };
    }

    private parseComparison(content: string): {
        similarities: string[];
        differences: string[];
        recommendations: string[];
    } {
        const extractList = (pattern: RegExp): string[] => {
            const match = content.match(pattern);
            if (!match) return [];
            return match[1]
                .split("\n")
                .map(l => l.trim().replace(/^[-*]\s*/, ""))
                .filter(l => l.length > 0);
        };

        return {
            similarities: extractList(/SIMILARITIES:\s*([\s\S]+?)(?=DIFFERENCES:|$)/i),
            differences: extractList(/DIFFERENCES:\s*([\s\S]+?)(?=RECOMMENDATIONS:|$)/i),
            recommendations: extractList(/RECOMMENDATIONS:\s*([\s\S]+?)$/i)
        };
    }

    private extractField(text: string, pattern: RegExp): string | null {
        const match = text.match(pattern);
        return match ? match[1].trim() : null;
    }

    private summarizeExperience(exp: Experience): string {
        let summary = `[${exp.type}] `;
        if (exp.context.issue) {
            summary += exp.context.issue.description;
        }
        summary += ` → ${exp.outcome.status}`;
        if (exp.reflection) {
            summary += `\nReflection: ${exp.reflection.summary}`;
        }
        return summary;
    }
}
