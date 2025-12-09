/**
 * Shared types for the AGI Proto-System.
 * These are simplified versions for clarity – expand for real use.
 */

export type RiskLevel = "safe" | "caution" | "critical";

export interface RuntimeMetrics {
    errorRate: number;
    avgLatencyMs: number;
    requestsPerMin: number;
    [key: string]: number;
}

export interface BusinessMetrics {
    conversionRate?: number;
    activeUsers?: number;
    churnRate?: number;
    [key: string]: number | undefined;
}

export interface SystemStateSnapshot {
    id: string;
    timestamp: string;
    appVersion: string;
    gitCommitHash: string;
    runtimeMetrics: RuntimeMetrics;
    businessMetrics: BusinessMetrics;
    featureFlags: Record<string, unknown>;
    notes?: string;
}

export interface PolicyCheckResult {
    result: "allowed" | "blocked" | "warn";
    reasons: string[];
}

export interface CodeDiff {
    summary: string;
    patch: string; // unified diff string
    filesTouched: string[];
    riskLevel: RiskLevel;
}
