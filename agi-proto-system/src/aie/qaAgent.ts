/**
 * QAAgent – evaluates proposed diffs using policy + test results.
 */

import { CodeDiff, PolicyCheckResult } from "../types";
import { PolicyEngine } from "../core/policyEngine";

export interface QAResult {
    verdict: "approve" | "reject" | "needs_human_review";
    reasons: string[];
}

export class QAAgent {
    private policy = new PolicyEngine();

    async evaluate(diff: CodeDiff, ciStatus: "pending" | "running" | "failed" | "succeeded"): Promise<QAResult> {
        const policyResult: PolicyCheckResult = this.policy.checkChange(diff.filesTouched, diff.riskLevel);
        const reasons: string[] = [];

        reasons.push(...policyResult.reasons);

        if (policyResult.result === "blocked") {
            reasons.push("PolicyEngine blocked this change.");
            return { verdict: "reject", reasons };
        }

        if (ciStatus === "failed") {
            reasons.push("CI tests failed for this change.");
            return { verdict: "reject", reasons };
        }

        if (policyResult.result === "warn") {
            reasons.push("Policy suggests caution – human review recommended.");
            return { verdict: "needs_human_review", reasons };
        }

        reasons.push("Policy and CI checks passed.");
        return { verdict: "approve", reasons };
    }
}
