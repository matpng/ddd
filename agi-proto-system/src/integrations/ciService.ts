/**
 * CI/CD integration – trigger pipelines, check status, etc.
 * Now integrates with GitHub Actions via Octokit.
 */

import { CONFIG } from "../config";
import { Logger } from "../core/logger";
import { Octokit } from "@octokit/rest";

const logger = new Logger("CIService");

type PipelineStatus = "pending" | "running" | "failed" | "succeeded";

interface WorkflowRun {
    id: number;
    status: string | null;
    conclusion: string | null;
    html_url: string;
    created_at: string;
}

export class CIService {
    private octokit: Octokit;
    private owner: string;
    private repo: string;
    private baseUrl: string;
    private token: string;

    constructor() {
        this.baseUrl = CONFIG.CI_API_BASE_URL || "https://api.github.com";
        this.token = CONFIG.CI_API_TOKEN || CONFIG.GIT_ACCESS_TOKEN || "";

        if (!this.token) {
            logger.warn("No CI token provided - workflow triggers may fail");
        }

        this.octokit = new Octokit({
            auth: this.token,
            baseUrl: this.baseUrl
        });

        // Parse repo URL from Git config
        const repoUrl = CONFIG.GIT_REPO_URL;
        const match = repoUrl.match(/(?:github\.com\/)?([^\/]+)\/([^\/\.]+)/);
        if (match) {
            this.owner = match[1];
            this.repo = match[2];
            logger.info(`CIService initialized for ${this.owner}/${this.repo}`);
        } else {
            this.owner = "unknown";
            this.repo = "unknown";
            logger.error(`Invalid repo URL: ${repoUrl}`);
        }
    }

    /**
     * Trigger a pipeline for a specific branch using workflow dispatch
     */
    async triggerPipeline(branchName: string, workflowId?: string): Promise<string> {
        logger.info(`Triggering pipeline for branch ${branchName}`);

        try {
            // If no workflow ID specified, use default (e.g., 'ci.yml' or 'test.yml')
            const workflow = workflowId || 'ci.yml';

            // Trigger workflow dispatch event
            await this.octokit.actions.createWorkflowDispatch({
                owner: this.owner,
                repo: this.repo,
                workflow_id: workflow,
                ref: branchName,
                inputs: {
                    triggered_by: 'agi-proto-system'
                }
            });

            // Get the most recent workflow run for this branch
            const runsResponse = await this.octokit.actions.listWorkflowRuns({
                owner: this.owner,
                repo: this.repo,
                workflow_id: workflow,
                branch: branchName,
                per_page: 1
            });

            if (runsResponse.data.workflow_runs.length > 0) {
                const runId = runsResponse.data.workflow_runs[0].id.toString();
                logger.info(`Pipeline triggered: run ID ${runId}`);
                return runId;
            }

            // If we can't get the run ID immediately, return a placeholder
            logger.warn("Pipeline triggered but run ID not immediately available");
            return `pending-${branchName}-${Date.now()}`;
        } catch (error: any) {
            logger.error(`Error triggering pipeline: ${error.message}`);

            // Check if it's a workflow not found error
            if (error.status === 404) {
                throw new Error(`Workflow not found. Create .github/workflows/ci.yml in your repository`);
            }

            throw error;
        }
    }

    /**
     * Get the status of a pipeline run
     */
    async getPipelineStatus(pipelineId: string): Promise<PipelineStatus> {
        logger.info(`Checking pipeline status for ${pipelineId}`);

        try {
            // Handle pending placeholder IDs
            if (pipelineId.startsWith('pending-')) {
                return "pending";
            }

            const runId = parseInt(pipelineId, 10);
            if (isNaN(runId)) {
                logger.error(`Invalid pipeline ID: ${pipelineId}`);
                return "failed";
            }

            const response = await this.octokit.actions.getWorkflowRun({
                owner: this.owner,
                repo: this.repo,
                run_id: runId
            });

            const run = response.data;

            // Map GitHub Actions status to our pipeline status
            const status = this.mapGitHubStatus(run.status, run.conclusion);

            logger.info(`Pipeline ${pipelineId}: ${status} (GitHub: ${run.status}/${run.conclusion})`);
            return status;
        } catch (error: any) {
            if (error.status === 404) {
                logger.warn(`Pipeline ${pipelineId} not found`);
                return "failed";
            }

            logger.error(`Error getting pipeline status: ${error.message}`);
            return "failed";
        }
    }

    /**
     * Wait for pipeline completion with timeout
     */
    async waitForCompletion(
        pipelineId: string,
        timeoutMs: number = 300000, // 5 minutes default
        pollIntervalMs: number = 10000 // 10 seconds
    ): Promise<PipelineStatus> {
        logger.info(`Waiting for pipeline ${pipelineId} completion (timeout: ${timeoutMs}ms)`);

        const startTime = Date.now();

        while (Date.now() - startTime < timeoutMs) {
            const status = await this.getPipelineStatus(pipelineId);

            if (status === "succeeded" || status === "failed") {
                logger.info(`Pipeline ${pipelineId} completed with status: ${status}`);
                return status;
            }

            logger.debug(`Pipeline ${pipelineId} still ${status}, polling again in ${pollIntervalMs}ms`);
            await new Promise(resolve => setTimeout(resolve, pollIntervalMs));
        }

        logger.warn(`Pipeline ${pipelineId} timed out after ${timeoutMs}ms`);
        return "failed";
    }

    /**
     * Get recent workflow runs
     */
    async getRecentRuns(limit: number = 10): Promise<WorkflowRun[]> {
        try {
            const response = await this.octokit.actions.listWorkflowRunsForRepo({
                owner: this.owner,
                repo: this.repo,
                per_page: limit
            });

            return response.data.workflow_runs.map(run => ({
                id: run.id,
                status: run.status,
                conclusion: run.conclusion,
                html_url: run.html_url,
                created_at: run.created_at
            }));
        } catch (error: any) {
            logger.error(`Error fetching recent runs: ${error.message}`);
            return [];
        }
    }

    /**
     * Cancel a running workflow
     */
    async cancelPipeline(pipelineId: string): Promise<boolean> {
        logger.info(`Cancelling pipeline ${pipelineId}`);

        try {
            const runId = parseInt(pipelineId, 10);
            if (isNaN(runId)) {
                logger.error(`Invalid pipeline ID: ${pipelineId}`);
                return false;
            }

            await this.octokit.actions.cancelWorkflowRun({
                owner: this.owner,
                repo: this.repo,
                run_id: runId
            });

            logger.info(`Pipeline ${pipelineId} cancelled successfully`);
            return true;
        } catch (error: any) {
            logger.error(`Error cancelling pipeline: ${error.message}`);
            return false;
        }
    }

    /**
     * Map GitHub Actions status/conclusion to our simplified status
     */
    private mapGitHubStatus(status: string | null, conclusion: string | null): PipelineStatus {
        // GitHub status can be: queued, in_progress, completed, waiting
        // conclusion can be: success, failure, cancelled, skipped, timed_out, action_required, neutral

        if (status === "queued" || status === "waiting") {
            return "pending";
        }

        if (status === "in_progress") {
            return "running";
        }

        if (status === "completed") {
            if (conclusion === "success") {
                return "succeeded";
            }
            // Any other conclusion is treated as failed
            return "failed";
        }

        // Default to pending for unknown states
        return "pending";
    }
}
