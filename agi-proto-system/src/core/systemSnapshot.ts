/**
 * System snapshot – ties metrics into a SystemStateSnapshot record.
 */

import { v4 as uuid } from "uuid";
import { MetricsService } from "../integrations/metricsService";
import { query } from "../integrations/db";
import { SystemStateSnapshot } from "../types";

export class SystemSnapshotService {
    private metricsService = new MetricsService();

    async captureSnapshot(appVersion: string, gitCommitHash: string): Promise<SystemStateSnapshot> {
        const runtimeMetrics = await this.metricsService.getRuntimeMetrics();
        const businessMetrics = await this.metricsService.getBusinessMetrics();

        const snapshot: SystemStateSnapshot = {
            id: uuid(),
            timestamp: new Date().toISOString(),
            appVersion,
            gitCommitHash,
            runtimeMetrics,
            businessMetrics,
            featureFlags: {},
            notes: "Auto-snapshot"
        };

        await query(
            `INSERT INTO system_state_snapshots
      (id, timestamp, app_version, git_commit_hash, runtime_metrics, business_metrics, feature_flags, notes)
      VALUES ($1, $2, $3, $4, $5, $6, $7, $8)`,
            [
                snapshot.id,
                snapshot.timestamp,
                snapshot.appVersion,
                snapshot.gitCommitHash,
                JSON.stringify(snapshot.runtimeMetrics),
                JSON.stringify(snapshot.businessMetrics),
                JSON.stringify(snapshot.featureFlags),
                snapshot.notes
            ]
        );

        return snapshot;
    }
}
