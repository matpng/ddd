/**
 * Self Model Agent - Tracks system capabilities, limitations, and performance.
 * Enables self-awareness and confidence calibration.
 */

import { llmClient, LLMMessage } from "../core/llmClient";
import { ExperienceStore, Experience } from "../core/experienceStore";
import { Logger } from "../core/logger";
import { query } from "../integrations/db";
import { v4 as uuid } from "uuid";

const log = new Logger("SelfModelAgent");

export interface Capability {
    name: string;
    description: string;
    confidence: number;
    evidence: string[];
    successRate: number;
    lastDemonstrated?: string;
}

export interface Limitation {
    area: string;
    description: string;
    severity: "low" | "medium" | "high";
    workaround?: string;
    evidence: string[];
}

export interface SelfModel {
    capabilities: Capability[];
    limitations: Limitation[];
    overallConfidence: number;
    learningProgress: {
        totalExperiences: number;
        successRate: number;
        improvementTrend: string;
    };
    lastUpdated: string;
}

export class SelfModelAgent {
    private experienceStore: ExperienceStore;

    constructor() {
        this.experienceStore = new ExperienceStore();
    }

    /**
     * Update and return current self model
     */
    async updateSelfModel(): Promise<SelfModel> {
        log.info("Updating self model");

        const capabilities = await this.assessCapabilities();
        const limitations = await this.identifyLimitations();
        const learningProgress = await this.trackLearningProgress();
        const overallConfidence = this.calculateOverallConfidence(capabilities, limitations);

        const selfModel: SelfModel = {
            capabilities,
            limitations,
            overallConfidence,
            learningProgress,
            lastUpdated: new Date().toISOString()
        };

        // Store capability assessments
        await this.storeCapabilityAssessments(capabilities);

        log.info("Self model updated", {
            capabilities: capabilities.length,
            limitations: limitations.length,
            confidence: overallConfidence.toFixed(2)
        });

        return selfModel;
    }

    /**
     * Get confidence for a specific plan
     */
    async getConfidence(plan: any): Promise<number> {
        log.info("Calculating confidence for plan", { planId: plan.id });

        // Load current self model
        const selfModel = await this.updateSelfModel();

        // Find relevant capabilities
        const relevantCapabilities = selfModel.capabilities.filter(cap =>
            plan.description.toLowerCase().includes(cap.name.toLowerCase()) ||
            plan.title.toLowerCase().includes(cap.name.toLowerCase())
        );

        if (relevantCapabilities.length === 0) {
            // No direct match, use overall confidence
            return selfModel.overallConfidence * 0.7; // Reduce for uncertainty
        }

        // Average confidence of relevant capabilities
        const avgConfidence = relevantCapabilities.reduce((sum, cap) => sum + cap.confidence, 0) / relevantCapabilities.length;

        // Check for relevant limitations
        const relevantLimitations = selfModel.limitations.filter(lim =>
            plan.description.toLowerCase().includes(lim.area.toLowerCase())
        );

        if (relevantLimitations.some(l => l.severity === "high")) {
            // Reduce confidence for high-severity limitations
            return avgConfidence * 0.5;
        }

        if (relevantLimitations.some(l => l.severity === "medium")) {
            return avgConfidence * 0.75;
        }

        return avgConfidence;
    }

    // Private methods

    private async assessCapabilities(): Promise<Capability[]> {
        // Get successful experiences
        const successes = await this.experienceStore.getExperimentsByStatus("success", 50);

        if (successes.length === 0) {
            return [
                {
                    name: "Initial Capability",
                    description: "System is learning its capabilities",
                    confidence: 0.3,
                    evidence: [],
                    successRate: 0.5
                }
            ];
        }

        // Use LLM to categorize capabilities
        const messages: LLMMessage[] = [
            {
                role: "system",
                content: "Analyze successful experiences to identify system capabilities."
            },
            {
                role: "user",
                content: `Analyze these successful experiences and identify distinct capabilities:

${successes.slice(0, 20).map((exp, idx) => `${idx + 1}. ${this.summarizeExperience(exp)}`).join("\n")}

For each capability,provide:
CAPABILITY:
Name: Brief name
Description: What the system can do
Evidence: List of relevant experience IDs or descriptions

Output 3-7 distinct capabilities.`
            }
        ];

        const response = await llmClient.complete(messages, {
            temperature: 0.5,
            maxTokens: 2048
        });

        const capabilities = this.parseCapabilities(response.content, successes);

        // Calculate success rates for each capability
        for (const cap of capabilities) {
            cap.successRate = await this.calculateSuccessRate(cap.name);
            cap.confidence = this.calculateCapabilityConfidence(cap, successes);
        }

        return capabilities;
    }

    private async identifyLimitations(): Promise<Limitation[]> {
        // Get failed/problematic experiences
        const failures = await this.experienceStore.getExperimentsByStatus(["failure", "partial_success"], 50);

        if (failures.length === 0) {
            return [];
        }

        const messages: LLMMessage[] = [
            {
                role: "system",
                content: "Identify patterns in failures to understand system limitations."
            },
            {
                role: "user",
                content: `Analyze these failure/partial success experiences to identify limitations:

${failures.slice(0, 20).map((exp, idx) => `${idx + 1}. ${this.summarizeExperience(exp)}`).join("\n")}

For each limitation, provide:
LIMITATION:
Area: What area this limitation affects
Description: What the system struggles with
Severity: low/medium/high
Workaround: Possible workaround (or "none")
Evidence: Relevant experience descriptions

Output 2-5 key limitations.`
            }
        ];

        const response = await llmClient.complete(messages, {
            temperature: 0.4,
            maxTokens: 2048
        });

        return this.parseLimitations(response.content);
    }

    private async trackLearningProgress(): Promise<{
        totalExperiences: number;
        successRate: number;
        improvementTrend: string;
    }> {
        const allExperiences = await this.experienceStore.getRecentExperiences(100);

        const totalExperiences = allExperiences.length;
        const successes = allExperiences.filter(e => e.type === "success").length;
        const successRate = totalExperiences > 0 ? successes / totalExperiences : 0;

        // Calculate trend (comparing first half vs second half)
        const midpoint = Math.floor(allExperiences.length / 2);
        const recentHalf = allExperiences.slice(0, midpoint);
        const olderHalf = allExperiences.slice(midpoint);

        const recentSuccessRate = recentHalf.filter(e => e.type === "success").length / Math.max(1, recentHalf.length);
        const olderSuccessRate = olderHalf.filter(e => e.type === "success").length / Math.max(1, olderHalf.length);

        let improvementTrend = "stable";
        if (recentSuccessRate > olderSuccessRate + 0.1) {
            improvementTrend = "improving";
        } else if (recentSuccessRate < olderSuccessRate - 0.1) {
            improvementTrend = "declining";
        }

        return {
            totalExperiences,
            successRate,
            improvementTrend
        };
    }

    private calculateOverallConfidence(capabilities: Capability[], limitations: Limitation[]): number {
        if (capabilities.length === 0) {
            return 0.3; // Low confidence if no demonstrated capabilities
        }

        // Average capability confidence
        const avgCapabilityConfidence = capabilities.reduce((sum, cap) => sum + cap.confidence, 0) / capabilities.length;

        // Reduce for high-severity limitations
        const highSevLimitations = limitations.filter(l => l.severity === "high").length;
        const reductionFactor = Math.max(0.5, 1 - (highSevLimitations * 0.15));

        return avgCapabilityConfidence * reductionFactor;
    }

    private async calculateSuccessRate(capabilityName: string): Promise<number> {
        // Simplified: use overall success rate
        // In production, filter experiences related to this capability
        return await this.experienceStore.getSuccessRate("issue");
    }

    private calculateCapabilityConfidence(cap: Capability, experiences: Experience[]): number {
        // Confidence based on evidence strength and recency
        const evidenceCount = cap.evidence.length;
        const baseConfidence = Math.min(1.0, evidenceCount / 10);

        // Check recency
        const recentCount = cap.evidence.filter(e => {
            const exp = experiences.find(ex => this.summarizeExperience(ex).includes(e));
            if (!exp) return false;
            const daysSince = (Date.now() - new Date(exp.timestamp).getTime()) / (1000 * 60 * 60 * 24);
            return daysSince < 7;
        }).length;

        const recencyFactor = recentCount > 0 ? 1.0 : 0.7;

        return baseConfidence * recencyFactor;
    }

    private parseCapabilities(content: string, experiences: Experience[]): Capability[] {
        const capabilities: Capability[] = [];
        const capabilityBlocks = content.split(/CAPABILITY:/i).slice(1);

        for (const block of capabilityBlocks) {
            const name = this.extractField(block, /Name:\s*(.+)/i) || "Unknown";
            const description = this.extractField(block, /Description:\s*(.+)/i) || "";
            const evidenceText = this.extractField(block, /Evidence:\s*([\s\S]+?)(?=CAPABILITY:|$)/i) || "";

            const evidence = evidenceText
                .split("\n")
                .map(l => l.trim().replace(/^[-*]\s*/, ""))
                .filter(l => l.length > 0);

            capabilities.push({
                name,
                description,
                confidence: 0.5, // Will be calculated later
                evidence,
                successRate: 0.5 // Will be calculated later
            });
        }

        return capabilities;
    }

    private parseLimitations(content: string): Limitation[] {
        const limitations: Limitation[] = [];
        const limitationBlocks = content.split(/LIMITATION:/i).slice(1);

        for (const block of limitationBlocks) {
            const area = this.extractField(block, /Area:\s*(.+)/i) || "Unknown";
            const description = this.extractField(block, /Description:\s*(.+)/i) || "";
            const severityText = this.extractField(block, /Severity:\s*(.+)/i) || "medium";
            const severity = severityText.toLowerCase().includes("high") ? "high"
                : severityText.toLowerCase().includes("low") ? "low"
                    : "medium";
            const workaround = this.extractField(block, /Workaround:\s*(.+)/i);
            const evidenceText = this.extractField(block, /Evidence:\s*([\s\S]+?)(?=LIMITATION:|$)/i) || "";

            const evidence = evidenceText
                .split("\n")
                .map(l => l.trim().replace(/^[-*]\s*/, ""))
                .filter(l => l.length > 0);

            limitations.push({
                area,
                description,
                severity: severity as "low" | "medium" | "high",
                workaround: workaround && !workaround.toLowerCase().includes("none") ? workaround : undefined,
                evidence
            });
        }

        return limitations;
    }

    private async storeCapabilityAssessments(capabilities: Capability[]): Promise<void> {
        for (const cap of capabilities) {
            try {
                await query(
                    `INSERT INTO capability_assessments 
                     (id, assessed_at, capability_name, confidence, evidence, limitations)
                     VALUES ($1, NOW(), $2, $3, $4, NULL)`,
                    [
                        uuid(),
                        cap.name,
                        cap.confidence,
                        JSON.stringify({
                            description: cap.description,
                            evidence: cap.evidence,
                            successRate: cap.successRate
                        })
                    ]
                );
            } catch (error) {
                log.warn(`Failed to store capability ${cap.name}`, error);
            }
        }
    }

    private extractField(text: string, pattern: RegExp): string | null {
        const match = text.match(pattern);
        return match ? match[1].trim() : null;
    }

    private summarizeExperience(exp: Experience): string {
        let summary = `[${exp.type}] `;
        if (exp.context.issue) {
            summary += exp.context.issue.description;
        } else if (exp.context.plan) {
            summary += exp.context.plan.title;
        }
        summary += ` → ${exp.outcome.status}`;
        return summary;
    }
}
