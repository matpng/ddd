/**
 * DiagnosticsAgent – chooses the most impactful problem to tackle next.
 * In a real implementation, this would call an LLM with metrics + history.
 */

import { MetricsService } from "../integrations/metricsService";
import { Logger } from "../core/logger";

export interface DiagnosticsIssue {
    id: string;
    description: string;
    severity: "low" | "medium" | "high" | "critical";
    suggestedTargetModuleIds: string[];
}

export class DiagnosticsAgent {
    private metricsService = new MetricsService();
    private log = new Logger("DiagnosticsAgent");

    async analyze(): Promise<DiagnosticsIssue[]> {
        const runtimeMetrics = await this.metricsService.getRuntimeMetrics();
        const businessMetrics = await this.metricsService.getBusinessMetrics();

        this.log.info("Analyzing metrics for issues", { runtimeMetrics, businessMetrics });

        const issues: DiagnosticsIssue[] = [];

        if (runtimeMetrics.errorRate > 0.05) {
            issues.push({
                id: "high_error_rate",
                description: "Error rate is above 5% – investigate failing endpoints.",
                severity: "critical",
                suggestedTargetModuleIds: ["api/error-prone-endpoints"]
            });
        }

        if ((businessMetrics.conversionRate ?? 0) < 0.1) {
            issues.push({
                id: "low_conversion",
                description: "Conversion rate is low – checkout/onboarding optimization needed.",
                severity: "high",
                suggestedTargetModuleIds: ["ui/onboarding-flow", "api/checkout"]
            });
        }

        return issues;
    }
}
