/**
 * PAK Long-Horizon Planning workflow – daily/weekly.
 * NOW WITH: World Model, Self Model, Predictive Planning, Value Alignment
 */

import { GoalEngineAgent } from "./goalEngineAgent";
import { WorldModelAgent } from "./worldModelAgent";
import { SelfModelAgent } from "./selfModelAgent";
import { ValueAlignmentAgent } from "./valueAlignmentAgent";
import { Logger } from "../core/logger";

const log = new Logger("PAKLongHorizon");

export class PAKLongHorizon {
    private goals = new GoalEngineAgent();
    private worldModel = new WorldModelAgent();
    private selfModel = new SelfModelAgent();
    private valueAlignment = new ValueAlignmentAgent();

    async runOnce(): Promise<void> {
        log.info("Starting PAK long-horizon planning cycle with AGI enhancements...");

        try {
            // STEP 1: Update World Model - Understand environment
            const worldState = await this.worldModel.updateWorldModel();
            log.info("World model updated", {
                systemHealth: worldState.systemState.health,
                predictions: worldState.predictions.length,
                externalFactors: worldState.externalFactors.length
            });

            // STEP 2: Update Self Model - Understand capabilities
            const selfState = await this.selfModel.updateSelfModel();
            log.info("Self model updated", {
                capabilities: selfState.capabilities.length,
                limitations: selfState.limitations.length,
                overallConfidence: selfState.overallConfidence.toFixed(2),
                learningTrend: selfState.learningProgress.improvementTrend
            });

            // STEP 3: Initialize Value System if needed
            await this.valueAlignment.initializeDefaultValues();

            // STEP 4: Review existing goals
            const activeGoals = await this.goals.listActiveGoals();
            log.info(`Active goals before planning: ${activeGoals.length}`);

            // STEP 5: Create proactive goals based on predictions
            const proactiveGoals = await this.createProactiveGoals(worldState);
            log.info(`Created ${proactiveGoals.length} proactive goals`);

            // STEP 6: Create goals based on self-identified limitations
            const improvementGoals = await this.createImprovementGoals(selfState);
            log.info(`Created ${improvementGoals.length} self-improvement goals`);

            // STEP 7: Create default goals if none exist
            if (activeGoals.length === 0 && proactiveGoals.length === 0) {
                log.info("No goals exist, creating defaults");
                await this.createDefaultGoals();
            }

            // STEP 8: Reprioritize goals based on world state and self model
            await this.goals.reprioritizeGoalsBasedOnMetrics();

            // STEP 9: Report summary
            const finalGoals = await this.goals.listActiveGoals();
            log.info("PAK long-horizon planning cycle complete", {
                totalGoals: finalGoals.length,
                systemHealth: worldState.systemState.health,
                selfConfidence: selfState.overallConfidence.toFixed(2),
                learningProgress: selfState.learningProgress.successRate.toFixed(2)
            });

        } catch (error) {
            log.error("PAK long-horizon cycle error", error);
        }
    }

    /**
     * Create proactive goals based on world model predictions
     */
    private async createProactiveGoals(worldState: any): Promise<any[]> {
        const proactiveGoals: any[] = [];

        // Create goals for high-confidence, high-impact predictions
        for (const prediction of worldState.predictions) {
            if (prediction.confidence > 0.7 && prediction.impact > 0.6) {
                log.info("Creating proactive goal for prediction", {
                    description: prediction.description
                });

                const goal = await this.goals.createGoal(
                    `Prepare for: ${prediction.description}`,
                    `Proactive goal based on prediction (confidence: ${prediction.confidence.toFixed(2)}, impact: ${prediction.impact.toFixed(2)}): ${prediction.reasoning}`
                );

                proactiveGoals.push(goal);
            }
        }

        // Create goals for critical external factors
        for (const factor of worldState.externalFactors) {
            if (factor.type === "security" && factor.relevance > 0.7) {
                log.info("Creating security goal for external factor", {
                    description: factor.description
                });

                const goal = await this.goals.createGoal(
                    `Address: ${factor.description}`,
                    `Security goal based on external research: ${factor.description} (Source: ${factor.source})`
                );

                proactiveGoals.push(goal);
            }
        }

        // Address system health if degraded/critical
        if (worldState.systemState.health !== "healthy") {
            log.info("Creating health improvement goal", {
                health: worldState.systemState.health
            });

            const goal = await this.goals.createGoal(
                `Restore System Health`,
                `System health is ${worldState.systemState.health}. Error rate: ${(worldState.systemState.errorRate * 100).toFixed(2)}%, Latency: ${worldState.systemState.latency}ms`
            );

            proactiveGoals.push(goal);
        }

        return proactiveGoals;
    }

    /**
     * Create goals to address self-identified limitations
     */
    private async createImprovementGoals(selfState: any): Promise<any[]> {
        const improvementGoals: any[] = [];

        // Create goals for high-severity limitations
        for (const limitation of selfState.limitations) {
            if (limitation.severity === "high") {
                log.info("Creating improvement goal for limitation", {
                    area: limitation.area
                });

                const goal = await this.goals.createGoal(
                    `Overcome Limitation: ${limitation.area}`,
                    `Self-identified limitation: ${limitation.description}${limitation.workaround ? ` Potential workaround: ${limitation.workaround}` : ""}`
                );

                improvementGoals.push(goal);
            }
        }

        // If learning progress is declining, create improvement goal
        if (selfState.learningProgress.improvementTrend === "declining") {
            log.info("Creating learning improvement goal due to declining trend");

            const goal = await this.goals.createGoal(
                "Improve Learning Effectiveness",
                `Recent success rate (${(selfState.learningProgress.successRate * 100).toFixed(1)}%) shows declining trend. Need to analyze and improve decision-making processes.`
            );

            improvementGoals.push(goal);
        }

        return improvementGoals;
    }

    /**
     * Create default system goals
     */
    private async createDefaultGoals(): Promise<void> {
        await this.goals.createGoal(
            "Improve System Reliability",
            "Ensure error rate stays below 2% across all critical endpoints. Maintain system stability and reduce unexpected failures."
        );

        await this.goals.createGoal(
            "Enhance User Experience",
            "Improve key user-facing metrics while ensuring genuine user benefit. Focus on reducing friction and improving actual value delivery."
        );

        await this.goals.createGoal(
            "Maintain Security Posture",
            "Keep dependencies updated, address security vulnerabilities promptly, and maintain secure coding practices."
        );
    }
}
