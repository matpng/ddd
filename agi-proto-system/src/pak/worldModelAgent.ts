/**
 * World Model Agent - Understands the system's environment and context.
 * Tracks trends, external factors, and makes predictions.
 */

import { llmClient, LLMMessage } from "../core/llmClient";
import { Logger } from "../core/logger";
import { MetricsService } from "../integrations/metricsService";
import { WebResearchService } from "../integrations/webResearchService";
import { query } from "../integrations/db";
import { v4 as uuid } from "uuid";

const log = new Logger("WorldModelAgent");

export interface WorldModel {
    systemState: SystemStateView;
    externalFactors: ExternalFactor[];
    trends: Trend[];
    predictions: Prediction[];
    uncertainties: Uncertainty[];
    lastUpdated: string;
}

export interface SystemStateView {
    health: "healthy" | "degraded" | "critical";
    errorRate: number;
    latency: number;
    activeIssues: number;
    recentChanges: number;
}

export interface ExternalFactor {
    id: string;
    type: "security" | "technology" | "dependency" | "industry";
    description: string;
    relevance: number;
    source: string;
    discovered: string;
}

export interface Trend {
    name: string;
    direction: "improving" | "stable" | "declining";
    confidence: number;
    metric: string;
    timeframe: string;
}

export interface Prediction {
    id: string;
    description: string;
    confidence: number;
    impact: number; // 0-1
    timeHorizon: "short" | "medium" | "long";
    reasoning: string;
    evidence: string[];
}

export interface Uncertainty {
    area: string;
    description: string;
    level: number; // 0-1, higher = more uncertain
}

export class WorldModelAgent {
    private metricsService: MetricsService;
    private researchService: WebResearchService;

    constructor() {
        this.metricsService = new MetricsService();
        this.researchService = new WebResearchService();
    }

    /**
     * Update and return the current world model
     */
    async updateWorldModel(): Promise<WorldModel> {
        log.info("Updating world model");

        const systemState = await this.getCurrentSystemState();
        const externalFactors = await this.researchExternalFactors();
        const trends = await this.detectTrends();
        const predictions = await this.generatePredictions(trends, externalFactors);
        const uncertainties = await this.identifyUncertainties(predictions);

        const worldModel: WorldModel = {
            systemState,
            externalFactors,
            trends,
            predictions,
            uncertainties,
            lastUpdated: new Date().toISOString()
        };

        // Store observations
        await this.storeObservations(worldModel);

        log.info("World model updated", {
            trends: trends.length,
            predictions: predictions.length,
            externalFactors: externalFactors.length
        });

        return worldModel;
    }

    // Private methods

    private async getCurrentSystemState(): Promise<SystemStateView> {
        const runtimeMetrics = await this.metricsService.getRuntimeMetrics();
        const businessMetrics = await this.metricsService.getBusinessMetrics();

        // Simplified health assessment
        let health: "healthy" | "degraded" | "critical" = "healthy";
        if (runtimeMetrics.errorRate > 0.05) {
            health = "critical";
        } else if (runtimeMetrics.errorRate > 0.02 || runtimeMetrics.avgLatencyMs > 1000) {
            health = "degraded";
        }

        return {
            health,
            errorRate: runtimeMetrics.errorRate,
            latency: runtimeMetrics.avgLatencyMs,
            activeIssues: runtimeMetrics.errorRate > 0.02 ? 1 : 0,
            recentChanges: 0 // Would track from deployment history
        };
    }

    private async researchExternalFactors(): Promise<ExternalFactor[]> {
        log.info("Researching external factors");

        const queries = [
            "latest security vulnerabilities in Node.js dependencies 2024",
            "PostgreSQL performance optimization techniques",
            "best practices for AI system safety 2024"
        ];

        const factors: ExternalFactor[] = [];

        for (const searchQuery of queries) {
            try {
                const results = await this.researchService.search(searchQuery);

                // Use LLM to extract relevant factors
                const messages: LLMMessage[] = [
                    {
                        role: "system",
                        content: "Extract relevant external factors that could impact a software system."
                    },
                    {
                        role: "user",
                        content: `Search Query: ${searchQuery}

Results:
${JSON.stringify(results.slice(0, 3), null, 2)}

Extract 1-2 relevant factors. For each:
FACTOR:
Type: security/technology/dependency/industry
Description: Brief description
Relevance: 0.0-1.0
`
                    }
                ];

                const response = await llmClient.complete(messages, {
                    temperature: 0.4,
                    maxTokens: 1024
                });

                const extracted = this.parseFactors(response.content, searchQuery);
                factors.push(...extracted);

            } catch (error) {
                log.warn(`Research failed for "${searchQuery}"`, error);
            }
        }

        return factors.slice(0, 10); // Limit to top 10
    }

    private parseFactors(content: string, source: string): ExternalFactor[] {
        const factors: ExternalFactor[] = [];
        const factorBlocks = content.split(/FACTOR:/i).slice(1);

        for (const block of factorBlocks) {
            const typeMatch = block.match(/Type:\s*(.+)/i);
            const descMatch = block.match(/Description:\s*(.+)/i);
            const relevanceMatch = block.match(/Relevance:\s*([0-9.]+)/i);

            if (descMatch) {
                factors.push({
                    id: uuid(),
                    type: this.parseFactorType(typeMatch?.[1]),
                    description: descMatch[1].trim(),
                    relevance: relevanceMatch ? parseFloat(relevanceMatch[1]) : 0.5,
                    source,
                    discovered: new Date().toISOString()
                });
            }
        }

        return factors;
    }

    private parseFactorType(text?: string): "security" | "technology" | "dependency" | "industry" {
        if (!text) return "technology";
        const lower = text.toLowerCase();
        if (lower.includes("security")) return "security";
        if (lower.includes("dependency") || lower.includes("depend")) return "dependency";
        if (lower.includes("industry")) return "industry";
        return "technology";
    }

    private async detectTrends(): Promise<Trend[]> {
        // Get historical metrics and identify trends
        // In production, query time-series data

        // Placeholder implementation
        return [
            {
                name: "Error Rate Trend",
                direction: "stable",
                confidence: 0.7,
                metric: "error_rate",
                timeframe: "7d"
            },
            {
                name: "Latency Trend",
                direction: "improving",
                confidence: 0.6,
                metric: "avg_latency",
                timeframe: "7d"
            }
        ];
    }

    private async generatePredictions(
        trends: Trend[],
        externalFactors: ExternalFactor[]
    ): Promise<Prediction[]> {
        log.info("Generating predictions");

        const messages: LLMMessage[] = [
            {
                role: "system",
                content: "You are a predictive analyst for software systems. Generate realistic predictions."
            },
            {
                role: "user",
                content: `Based on these trends and external factors, predict potential future issues or opportunities:

Trends:
${trends.map(t => `- ${t.name}: ${t.direction} (confidence: ${t.confidence})`).join("\n")}

External Factors:
${externalFactors.slice(0, 5).map(f => `- [${f.type}] ${f.description} (relevance: ${f.relevance})`).join("\n")}

Generate 2-4 predictions. For each:
PREDICTION:
Description: What will likely happen
Confidence: 0.0-1.0
Impact: 0.0-1.0
TimeHorizon: short/medium/long (weeks/months/quarters)
Reasoning: Why this is predicted
Evidence: Supporting evidence
`
            }
        ];

        const response = await llmClient.complete(messages, {
            temperature: 0.6,
            maxTokens: 2048
        });

        const predictions = this.parsePredictions(response.content);

        // Store predictions in database
        for (const pred of predictions) {
            await this.storePrediction(pred);
        }

        return predictions;
    }

    private parsePredictions(content: string): Prediction[] {
        const predictions: Prediction[] = [];
        const predBlocks = content.split(/PREDICTION:/i).slice(1);

        for (const block of predBlocks) {
            const descMatch = block.match(/Description:\s*(.+)/i);
            const confidenceMatch = block.match(/Confidence:\s*([0-9.]+)/i);
            const impactMatch = block.match(/Impact:\s*([0-9.]+)/i);
            const horizonMatch = block.match(/TimeHorizon:\s*(.+)/i);
            const reasoningMatch = block.match(/Reasoning:\s*(.+?)(?=Evidence:|$)/is);
            const evidenceMatch = block.match(/Evidence:\s*([\s\S]+?)(?=PREDICTION:|$)/i);

            if (descMatch) {
                const evidence = evidenceMatch
                    ? evidenceMatch[1].split("\n").map(l => l.trim()).filter(l => l.length > 0)
                    : [];

                predictions.push({
                    id: uuid(),
                    description: descMatch[1].trim(),
                    confidence: confidenceMatch ? parseFloat(confidenceMatch[1]) : 0.5,
                    impact: impactMatch ? parseFloat(impactMatch[1]) : 0.5,
                    timeHorizon: this.parseTimeHorizon(horizonMatch?.[1]),
                    reasoning: reasoningMatch ? reasoningMatch[1].trim() : "",
                    evidence
                });
            }
        }

        return predictions;
    }

    private parseTimeHorizon(text?: string): "short" | "medium" | "long" {
        if (!text) return "medium";
        const lower = text.toLowerCase();
        if (lower.includes("short") || lower.includes("week")) return "short";
        if (lower.includes("long") || lower.includes("quarter") || lower.includes("year")) return "long";
        return "medium";
    }

    private async identifyUncertainties(predictions: Prediction[]): Promise<Uncertainty[]> {
        // Identify areas with high uncertainty
        const uncertainties: Uncertainty[] = [];

        // High uncertainty if predictions have low confidence
        for (const pred of predictions) {
            if (pred.confidence < 0.5) {
                uncertainties.push({
                    area: pred.description,
                    description: `Low confidence prediction: ${pred.description}`,
                    level: 1 - pred.confidence
                });
            }
        }

        return uncertainties;
    }

    private async storeObservations(worldModel: WorldModel): Promise<void> {
        // Store external factors as observations
        for (const factor of worldModel.externalFactors) {
            try {
                await query(
                    `INSERT INTO world_observations 
                     (id, timestamp, source, observation_type, data, relevance_score)
                     VALUES ($1, NOW(), $2, $3, $4, $5)`,
                    [
                        uuid(),
                        factor.source,
                        factor.type,
                        JSON.stringify({ description: factor.description }),
                        factor.relevance
                    ]
                );
            } catch (error) {
                log.warn("Failed to store observation", error);
            }
        }
    }

    private async storePrediction(prediction: Prediction): Promise<void> {
        try {
            await query(
                `INSERT INTO predictions
                 (id, created_at, prediction_type, description, confidence, impact_score, time_horizon, evidence)
                 VALUES ($1, NOW(), $2, $3, $4, $5, $6, $7)`,
                [
                    prediction.id,
                    "system_prediction",
                    prediction.description,
                    prediction.confidence,
                    prediction.impact,
                    prediction.timeHorizon,
                    JSON.stringify({ reasoning: prediction.reasoning, evidence: prediction.evidence })
                ]
            );
        } catch (error) {
            log.warn("Failed to store prediction", error);
        }
    }
}
