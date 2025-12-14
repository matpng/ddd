/**
 * Enhanced Risk Classifier - Analyzes code changes for risk level
 * Uses multiple signals: file paths, complexity, breaking changes, history
 */

import { RiskLevel } from "../types";
import { Logger } from "./logger";
import { query } from "../integrations/db";

const log = new Logger("RiskClassifier");

export interface RiskAnalysis {
    level: RiskLevel;
    score: number; // 0-100
    reasons: string[];
    signals: RiskSignal[];
    recommendations: string[];
}

export interface RiskSignal {
    name: string;
    weight: number;
    value: number;
    description: string;
}

export interface ChangeMetrics {
    linesAdded: number;
    linesRemoved: number;
    filesChanged: number;
    functionsModified: number;
}

export class RiskClassifier {
    // Configurable risk thresholds
    private readonly thresholds = {
        safe: 0,
        caution: 30,
        critical: 70
    };

    // File pattern weights (higher = more risky)
    private readonly criticalKeywords = [
        { pattern: "auth", weight: 40, description: "Authentication system" },
        { pattern: "payment", weight: 50, description: "Payment processing" },
        { pattern: "billing", weight: 45, description: "Billing system" },
        { pattern: "encryption", weight: 40, description: "Encryption/security" },
        { pattern: "security", weight: 35, description: "Security components" },
        { pattern: "user", weight: 25, description: "User management" },
        { pattern: "admin", weight: 30, description: "Admin functionality" }
    ];

    private readonly cautionKeywords = [
        { pattern: "db", weight: 20, description: "Database operations" },
        { pattern: "repository", weight: 15, description: "Data repositories" },
        { pattern: "service", weight: 10, description: "Core services" },
        { pattern: "api", weight: 15, description: "API endpoints" },
        { pattern: "integration", weight: 15, description: "External integrations" }
    ];

    /**
     * Main classification method with detailed analysis
     */
    async classifyWithAnalysis(
        filesTouched: string[],
        patch?: string,
        metrics?: ChangeMetrics
    ): Promise<RiskAnalysis> {
        const signals: RiskSignal[] = [];
        const reasons: string[] = [];
        const recommendations: string[] = [];

        // Signal 1: File pattern matching
        const fileSignal = this.analyzeFilePatterns(filesTouched);
        signals.push(fileSignal);
        if (fileSignal.value > 0) {
            reasons.push(fileSignal.description);
        }

        // Signal 2: Change complexity
        if (metrics) {
            const complexitySignal = this.analyzeComplexity(metrics);
            signals.push(complexitySignal);
            if (complexitySignal.value > 0) {
                reasons.push(complexitySignal.description);
            }
        }

        // Signal 3: Breaking changes detection
        if (patch) {
            const breakingSignal = this.analyzeBreakingChanges(patch);
            signals.push(breakingSignal);
            if (breakingSignal.value > 0) {
                reasons.push(breakingSignal.description);
            }
        }

        // Signal 4: Historical failure rate
        const historySignal = await this.analyzeHistoricalRisk(filesTouched);
        signals.push(historySignal);
        if (historySignal.value > 0) {
            reasons.push(historySignal.description);
        }

        // Signal 5: Multiple critical files
        if (filesTouched.length > 5) {
            const multiFileSignal: RiskSignal = {
                name: "multiple_files",
                weight: 10,
                value: Math.min(filesTouched.length, 20),
                description: `Changes affect ${filesTouched.length} files`
            };
            signals.push(multiFileSignal);
            reasons.push(multiFileSignal.description);
        }

        // Calculate weighted risk score
        const score = this.calculateRiskScore(signals);

        // Determine level based on score
        const level = this.scoreToLevel(score);

        // Generate recommendations
        if (level === "critical") {
            recommendations.push("Manual review required before deployment");
            recommendations.push("Comprehensive test coverage essential");
            recommendations.push("Consider splitting into smaller changes");
        } else if (level === "caution") {
            recommendations.push("Automated tests should cover all changes");
            recommendations.push("Monitor metrics closely after deployment");
        } else {
            recommendations.push("Standard deployment process can proceed");
        }

        if (filesTouched.length > 10) {
            recommendations.push("Consider breaking into multiple smaller PRs");
        }

        log.info(`Risk analysis complete: ${level} (score: ${score})`, {
            files: filesTouched.length,
            reasons: reasons.length
        });

        return {
            level,
            score,
            reasons,
            signals,
            recommendations
        };
    }

    /**
     * Legacy method for backward compatibility
     */
    classify(filesTouched: string[]): RiskLevel {
        // Use synchronous analysis for simple cases
        const fileSignal = this.analyzeFilePatterns(filesTouched);
        const score = fileSignal.weight * (fileSignal.value / 100);
        return this.scoreToLevel(score);
    }

    /**
     * Analyze file patterns for critical/caution keywords
     */
    private analyzeFilePatterns(filesTouched: string[]): RiskSignal {
        let maxWeight = 0;
        let matchedPattern = "";

        for (const file of filesTouched) {
            const lowerFile = file.toLowerCase();

            // Check critical patterns
            for (const { pattern, weight, description } of this.criticalKeywords) {
                if (lowerFile.includes(pattern) && weight > maxWeight) {
                    maxWeight = weight;
                    matchedPattern = description;
                }
            }

            // Check caution patterns
            for (const { pattern, weight, description } of this.cautionKeywords) {
                if (lowerFile.includes(pattern) && weight > maxWeight) {
                    maxWeight = weight;
                    matchedPattern = description;
                }
            }
        }

        return {
            name: "file_patterns",
            weight: maxWeight,
            value: maxWeight > 0 ? 100 : 0,
            description: matchedPattern || "No critical file patterns detected"
        };
    }

    /**
     * Analyze change complexity
     */
    private analyzeComplexity(metrics: ChangeMetrics): RiskSignal {
        const totalLines = metrics.linesAdded + metrics.linesRemoved;

        // High complexity if changing many lines or functions
        let complexityScore = 0;

        if (totalLines > 500) {
            complexityScore = 30;
        } else if (totalLines > 200) {
            complexityScore = 20;
        } else if (totalLines > 100) {
            complexityScore = 10;
        }

        if (metrics.functionsModified > 10) {
            complexityScore += 20;
        } else if (metrics.functionsModified > 5) {
            complexityScore += 10;
        }

        return {
            name: "complexity",
            weight: 15,
            value: complexityScore,
            description: `Change complexity: ${totalLines} lines, ${metrics.functionsModified} functions`
        };
    }

    /**
     * Detect breaking changes in the patch
     */
    private analyzeBreakingChanges(patch: string): RiskSignal {
        const breakingIndicators = [
            { pattern: /^-\s*(export\s+)?function\s+\w+/gm, severity: 30, desc: "Function removal" },
            { pattern: /^-\s*(export\s+)?(class|interface)\s+\w+/gm, severity: 30, desc: "Type removal" },
            { pattern: /^-\s*(export\s+)?const\s+\w+/gm, severity: 20, desc: "Constant removal" },
            { pattern: /function\s+\w+\([^)]*\)[^{]*{[^}]*throw\s+new\s+Error/g, severity: 15, desc: "New error paths" },
            { pattern: /\bDROP\s+(TABLE|COLUMN|INDEX)\b/gi, severity: 40, desc: "Database schema drop" },
            { pattern: /\bALTER\s+TABLE\b/gi, severity: 25, desc: "Database schema alteration" }
        ];

        let maxSeverity = 0;
        let detectedChange = "";

        for (const { pattern, severity, desc } of breakingIndicators) {
            if (pattern.test(patch) && severity > maxSeverity) {
                maxSeverity = severity;
                detectedChange = desc;
            }
        }

        return {
            name: "breaking_changes",
            weight: 25,
            value: maxSeverity,
            description: detectedChange || "No breaking changes detected"
        };
    }

    /**
     * Analyze historical failure rate for these files
     */
    private async analyzeHistoricalRisk(filesTouched: string[]): Promise<RiskSignal> {
        try {
            // Query experiences table for historical failures involving these files
            const result = await query<{ total: number; failures: number }>(
                `SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN type = 'failure' THEN 1 ELSE 0 END) as failures
                FROM experiences
                WHERE context->>'diff' IS NOT NULL
                AND created_at > NOW() - INTERVAL '30 days'
                LIMIT 1000`
            );

            if (result.length > 0) {
                const { total, failures } = result[0];
                const failureRate = total > 0 ? (failures / total) * 100 : 0;

                return {
                    name: "historical_risk",
                    weight: 20,
                    value: failureRate,
                    description: `${failureRate.toFixed(1)}% failure rate in similar changes (last 30 days)`
                };
            }
        } catch (error: any) {
            log.warn(`Could not fetch historical risk data: ${error.message}`);
        }

        return {
            name: "historical_risk",
            weight: 0,
            value: 0,
            description: "No historical data available"
        };
    }

    /**
     * Calculate weighted risk score from signals
     */
    private calculateRiskScore(signals: RiskSignal[]): number {
        let weightedSum = 0;
        let totalWeight = 0;

        for (const signal of signals) {
            if (signal.weight > 0) {
                weightedSum += (signal.value / 100) * signal.weight;
                totalWeight += signal.weight;
            }
        }

        return totalWeight > 0 ? (weightedSum / totalWeight) * 100 : 0;
    }

    /**
     * Convert numeric score to risk level
     */
    private scoreToLevel(score: number): RiskLevel {
        if (score >= this.thresholds.critical) {
            return "critical";
        } else if (score >= this.thresholds.caution) {
            return "caution";
        }
        return "safe";
    }
}
