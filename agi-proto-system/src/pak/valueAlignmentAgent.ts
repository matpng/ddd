/**
 * Value Alignment Agent - Ensures system actions align with human values and ethics.
 * Critical component for safe and beneficial AGI behavior.
 */

import { llmClient, LLMMessage } from "../core/llmClient";
import { Logger } from "../core/logger";
import { query } from "../integrations/db";
import { v4 as uuid } from "uuid";

const log = new Logger("ValueAlignmentAgent");

export interface Value {
    id: string;
    name: string;
    description: string;
    weight: number;
    source: "human_defined" | "system_derived" | "world_model_inferred";
    examples?: string[];
    lastUpdatedAt?: string;
}

export interface ValueScore {
    valueId: string;
    valueName: string;
    score: number; // -1 (harmful) to 1 (beneficial)
    reasoning: string;
    concerns: string[];
    opportunities: string[];
    confidence: number;
}

export interface AlignmentResult {
    overallAlignment: number;
    individualScores: ValueScore[];
    conflicts: ValueConflict[];
    resolution?: ConflictResolution;
    recommendation: "proceed" | "proceed_with_caution" | "human_review" | "reject";
    reasoning: string;
}

export interface ValueConflict {
    value1: string;
    value2: string;
    description: string;
    severity: "low" | "medium" | "high";
}

export interface ConflictResolution {
    resolved: boolean;
    strategy: string;
    recommendation: string;
}

export class ValueAlignmentAgent {
    /**
     * Evaluate whether a plan aligns with system values
     */
    async evaluateAlignment(plan: any, context?: any): Promise<AlignmentResult> {
        log.info("Evaluating value alignment for plan", { planId: plan.id });

        // 1. Load active values
        const values = await this.getActiveValues();

        if (values.length === 0) {
            log.warn("No values defined, initializing defaults");
            await this.initializeDefaultValues();
            const newValues = await this.getActiveValues();
            if (newValues.length === 0) {
                // Fallback if DB not ready
                return this.createPermissiveResult();
            }
        }

        // 2. Score against each value
        const valueScores = await Promise.all(
            values.map(v => this.scoreAgainstValue(plan, v, context))
        );

        // 3. Detect conflicts
        const conflicts = this.detectConflicts(valueScores);

        // 4. Calculate overall alignment
        const overallAlignment = this.calculateOverallAlignment(valueScores, values);

        // 5. Generate recommendation
        const recommendation = this.generateRecommendation(overallAlignment, conflicts);
        const reasoning = this.generateReasoning(valueScores, conflicts, overallAlignment);

        // 6. Resolve conflicts if needed
        let resolution: ConflictResolution | undefined;
        if (conflicts.length > 0) {
            resolution = await this.resolveConflicts(conflicts, plan, valueScores);
        }

        const result: AlignmentResult = {
            overallAlignment,
            individualScores: valueScores,
            conflicts,
            resolution,
            recommendation,
            reasoning
        };

        // Store evaluation for audit trail
        await this.storeEvaluation(plan.id, result);

        log.info("Value alignment evaluated", {
            planId: plan.id,
            alignment: overallAlignment.toFixed(2),
            recommendation
        });

        return result;
    }

    /**
     * Initialize default ethical values
     */
    async initializeDefaultValues(): Promise<void> {
        log.info("Initializing default value system");

        const defaultValues: Omit<Value, "id" | "lastUpdatedAt">[] = [
            {
                name: "User Benefit",
                description: "Changes should primarily benefit users, not just metrics. Prioritize genuine user value over vanity metrics.",
                weight: 1.0,
                source: "human_defined",
                examples: [
                    "Improving actual user experience",
                    "Reducing user confusion or friction",
                    "Protecting user time and attention"
                ]
            },
            {
                name: "Privacy",
                description: "Respect user privacy and data protection. Minimize data collection and maximize transparency.",
                weight: 1.0,
                source: "human_defined",
                examples: [
                    "Not collecting unnecessary data",
                    "Securing user information",
                    "Being transparent about data use"
                ]
            },
            {
                name: "Reliability",
                description: "Maintain system stability and predictability. Avoid changes that could cause unexpected failures.",
                weight: 0.9,
                source: "human_defined",
                examples: [
                    "Maintaining backward compatibility",
                    "Thorough testing before deployment",
                    "Graceful error handling"
                ]
            },
            {
                name: "Fairness",
                description: "Avoid creating or amplifying biases. Ensure equitable treatment of all users.",
                weight: 0.9,
                source: "human_defined",
                examples: [
                    "Not discriminating based on user characteristics",
                    "Providing equal access to features",
                    "Avoiding algorithmic bias"
                ]
            },
            {
                name: "Transparency",
                description: "Changes should be understandable and auditable. Maintain clear reasoning and documentation.",
                weight: 0.8,
                source: "human_defined",
                examples: [
                    "Clear documentation of changes",
                    "Explainable algorithms",
                    "Honest about limitations"
                ]
            },
            {
                name: "Sustainability",
                description: "Consider long-term maintainability and technical debt. Avoid quick fixes that create future problems.",
                weight: 0.7,
                source: "human_defined",
                examples: [
                    "Clean, maintainable code",
                    "Reducing technical debt",
                    "Planning for future scalability"
                ]
            }
        ];

        for (const value of defaultValues) {
            try {
                await this.createValue(value);
            } catch (error) {
                log.warn(`Failed to create value ${value.name}`, error);
            }
        }
    }

    // Private methods

    private async getActiveValues(): Promise<Value[]> {
        try {
            const rows = await query<any>("SELECT * FROM values_table WHERE weight > 0 ORDER BY weight DESC");
            return rows.map(r => ({
                id: r.id,
                name: r.name,
                description: r.description,
                weight: r.weight,
                source: r.source,
                examples: r.examples ? JSON.parse(r.examples) : undefined,
                lastUpdatedAt: r.last_updated_at
            }));
        } catch (error) {
            log.error("Failed to fetch values from database", error);
            return [];
        }
    }

    private async createValue(value: Omit<Value, "id" | "lastUpdatedAt">): Promise<Value> {
        const id = uuid();
        const now = new Date().toISOString();

        const fullValue: Value = {
            id,
            ...value,
            lastUpdatedAt: now
        };

        try {
            await query(
                `INSERT INTO values_table (id, name, description, source, weight, last_updated_at, examples)
                 VALUES ($1, $2, $3, $4, $5, $6, $7)
                 ON CONFLICT (name) DO UPDATE SET 
                    description = $3, weight = $5, last_updated_at = $6`,
                [
                    id,
                    value.name,
                    value.description,
                    value.source,
                    value.weight,
                    now,
                    value.examples ? JSON.stringify(value.examples) : null
                ]
            );
        } catch (error) {
            log.warn(`Database insert failed for value ${value.name}, might not have table yet`, error);
        }

        return fullValue;
    }

    private async scoreAgainstValue(
        plan: any,
        value: Value,
        context?: any
    ): Promise<ValueScore> {
        const messages: LLMMessage[] = [
            {
                role: "system",
                content: `You are an ethics and values assessment AI. Evaluate how this plan aligns with the value: "${value.name}"

Value Description: ${value.description}

${value.examples ? `Examples of alignment:\n${value.examples.map(e => `- ${e}`).join("\n")}` : ""}

Score from -1 (harmful) to +1 (beneficial). Consider both direct impact and second-order effects.`
            },
            {
                role: "user",
                content: `Plan:
Title: ${plan.title}
Description: ${plan.description}
${plan.approach ? `Approach: ${plan.approach}` : ""}
Target Modules: ${plan.targetModuleIds?.join(", ") || "N/A"}

${context ? `Context:\n${JSON.stringify(context, null, 2)}` : ""}

Evaluate alignment with "${value.name}".

Output format:
SCORE: -1.0 to 1.0
REASONING: Detailed explanation
CONCERNS: List any concerns (or "none")
OPPORTUNITIES: List opportunities to enhance value (or "none")
CONFIDENCE: 0.0-1.0`
            }
        ];

        const response = await llmClient.complete(messages, {
            temperature: 0.4,
            maxTokens: 1024
        });

        return this.parseValueScore(response.content, value);
    }

    private parseValueScore(content: string, value: Value): ValueScore {
        const scoreMatch = content.match(/SCORE:\s*([-+]?[0-9.]+)/i);
        const score = scoreMatch ? parseFloat(scoreMatch[1]) : 0;

        const reasoningMatch = content.match(/REASONING:\s*(.+?)(?=CONCERNS:|OPPORTUNITIES:|$)/is);
        const reasoning = reasoningMatch ? reasoningMatch[1].trim() : "";

        const concernsMatch = content.match(/CONCERNS:\s*([\s\S]+?)(?=OPPORTUNITIES:|CONFIDENCE:|$)/i);
        const concernsText = concernsMatch ? concernsMatch[1].trim() : "";
        const concerns = concernsText.toLowerCase().includes("none")
            ? []
            : concernsText.split("\n").map(l => l.trim().replace(/^[-*]\s*/, "")).filter(l => l.length > 0);

        const opportunitiesMatch = content.match(/OPPORTUNITIES:\s*([\s\S]+?)(?=CONFIDENCE:|$)/i);
        const opportunitiesText = opportunitiesMatch ? opportunitiesMatch[1].trim() : "";
        const opportunities = opportunitiesText.toLowerCase().includes("none")
            ? []
            : opportunitiesText.split("\n").map(l => l.trim().replace(/^[-*]\s*/, "")).filter(l => l.length > 0);

        const confidenceMatch = content.match(/CONFIDENCE:\s*([0-9.]+)/i);
        const confidence = confidenceMatch ? parseFloat(confidenceMatch[1]) : 0.7;

        return {
            valueId: value.id,
            valueName: value.name,
            score: Math.max(-1, Math.min(1, score)),
            reasoning,
            concerns,
            opportunities,
            confidence: Math.max(0, Math.min(1, confidence))
        };
    }

    private detectConflicts(scores: ValueScore[]): ValueConflict[] {
        const conflicts: ValueConflict[] = [];

        // Find values with opposing scores
        for (let i = 0; i < scores.length; i++) {
            for (let j = i + 1; j < scores.length; j++) {
                const score1 = scores[i];
                const score2 = scores[j];

                // Conflict if one highly positive and one highly negative
                if ((score1.score > 0.5 && score2.score < -0.3) ||
                    (score1.score < -0.3 && score2.score > 0.5)) {

                    const severity = Math.abs(score1.score - score2.score) > 1.2 ? "high" : "medium";

                    conflicts.push({
                        value1: score1.valueName,
                        value2: score2.valueName,
                        description: `Conflict between ${score1.valueName} (${score1.score.toFixed(2)}) and ${score2.valueName} (${score2.score.toFixed(2)})`,
                        severity
                    });
                }
            }
        }

        return conflicts;
    }

    private calculateOverallAlignment(scores: ValueScore[], values: Value[]): number {
        let weightedSum = 0;
        let totalWeight = 0;

        for (const score of scores) {
            const value = values.find(v => v.id === score.valueId);
            if (value) {
                weightedSum += score.score * value.weight * score.confidence;
                totalWeight += value.weight * score.confidence;
            }
        }

        return totalWeight > 0 ? weightedSum / totalWeight : 0;
    }

    private generateRecommendation(
        overallAlignment: number,
        conflicts: ValueConflict[]
    ): "proceed" | "proceed_with_caution" | "human_review" | "reject" {
        // Reject if overall alignment is negative
        if (overallAlignment < -0.2) {
            return "reject";
        }

        // Require human review for high-severity conflicts
        if (conflicts.some(c => c.severity === "high")) {
            return "human_review";
        }

        // Proceed with caution if alignment is low or there are medium conflicts
        if (overallAlignment < 0.4 || conflicts.some(c => c.severity === "medium")) {
            return "proceed_with_caution";
        }

        return "proceed";
    }

    private generateReasoning(scores: ValueScore[], conflicts: ValueConflict[], overall: number): string {
        let reasoning = `Overall alignment: ${overall.toFixed(2)}\n\n`;

        reasoning += "Value Scores:\n";
        scores.forEach(s => {
            reasoning += `- ${s.valueName}: ${s.score.toFixed(2)} (${s.reasoning.substring(0, 100)}...)\n`;
        });

        if (conflicts.length > 0) {
            reasoning += `\nConflicts detected: ${conflicts.length}\n`;
            conflicts.forEach(c => {
                reasoning += `- ${c.description} [${c.severity}]\n`;
            });
        }

        return reasoning;
    }

    private async resolveConflicts(
        conflicts: ValueConflict[],
        plan: any,
        scores: ValueScore[]
    ): Promise<ConflictResolution> {
        // Use LLM to suggest conflict resolution
        const messages: LLMMessage[] = [
            {
                role: "system",
                content: "You are an ethics advisor helping resolve value conflicts."
            },
            {
                role: "user",
                content: `Plan: ${plan.title}

Conflicts:
${conflicts.map(c => `- ${c.description}`).join("\n")}

Value Scores:
${scores.map(s => `${s.valueName}: ${s.score.toFixed(2)} - ${s.reasoning}`).join("\n\n")}

Can these conflicts be resolved? Suggest a resolution strategy.

Format:
RESOLVED: yes/no
STRATEGY: Description of how to resolve
RECOMMENDATION: Final recommendation`
            }
        ];

        const response = await llmClient.complete(messages, {
            temperature: 0.5,
            maxTokens: 1024
        });

        const content = response.content;
        const resolvedMatch = content.match(/RESOLVED:\s*(yes|no)/i);
        const resolved = resolvedMatch ? resolvedMatch[1].toLowerCase() === "yes" : false;

        const strategyMatch = content.match(/STRATEGY:\s*(.+?)(?=RECOMMENDATION:|$)/is);
        const strategy = strategyMatch ? strategyMatch[1].trim() : "";

        const recommendationMatch = content.match(/RECOMMENDATION:\s*(.+)/is);
        const recommendation = recommendationMatch ? recommendationMatch[1].trim() : "";

        return {
            resolved,
            strategy,
            recommendation
        };
    }

    private async storeEvaluation(planId: string, result: AlignmentResult): Promise<void> {
        try {
            await query(
                `INSERT INTO value_evaluations (id, plan_id, evaluated_at, value_scores, overall_alignment, conflicts, resolution)
                 VALUES ($1, $2, NOW(), $3, $4, $5, $6)`,
                [
                    uuid(),
                    planId,
                    JSON.stringify(result.individualScores),
                    result.overallAlignment,
                    JSON.stringify(result.conflicts),
                    result.resolution ? JSON.stringify(result.resolution) : null
                ]
            );
        } catch (error) {
            log.warn("Failed to store value evaluation", error);
        }
    }

    private createPermissiveResult(): AlignmentResult {
        return {
            overallAlignment: 0.7,
            individualScores: [],
            conflicts: [],
            recommendation: "proceed_with_caution",
            reasoning: "No values configured, proceeding with caution"
        };
    }
}
