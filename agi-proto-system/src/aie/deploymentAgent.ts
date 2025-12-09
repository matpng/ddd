/**
 * DeploymentAgent – handles canary deployment and monitoring.
 */

import { CIService } from "../integrations/ciService";
import { MetricsService } from "../integrations/metricsService";
import { Logger } from "../core/logger";

export class DeploymentAgent {
    private ci = new CIService();
    private metrics = new MetricsService();
    private log = new Logger("DeploymentAgent");

    async deployCanary(branchName: string): Promise<boolean> {
        this.log.info("Starting canary deployment...", { branchName });
        const pipelineId = await this.ci.triggerPipeline(branchName);

        const status = await this.ci.getPipelineStatus(pipelineId);
        if (status !== "succeeded") {
            this.log.error("Canary pipeline failed", { pipelineId, status });
            return false;
        }

        const runtimeMetrics = await this.metrics.getRuntimeMetrics();
        this.log.info("Canary metrics snapshot", runtimeMetrics);

        if (runtimeMetrics.errorRate > 0.05) {
            this.log.error("Canary shows too high error rate – should rollback.");
            return false;
        }

        this.log.info("Canary looks good.");
        return true;
    }
}
