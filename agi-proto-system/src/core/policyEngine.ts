/**
 * PolicyEngine – enforces safety, compliance, and risk-based rules.
 * This is where you encode "cannot touch auth", "no data exfiltration", etc.
 */

import { PolicyCheckResult, RiskLevel } from "../types";

export class PolicyEngine {
    checkChange(filesTouched: string[], riskLevel: RiskLevel): PolicyCheckResult {
        const reasons: string[] = [];

        // Example policy: critical files cannot be touched automatically.
        const criticalPatterns = ["auth", "payment", "billing", "encryption"];
        const criticalTouched = filesTouched.some((file) =>
            criticalPatterns.some((pat) => file.toLowerCase().includes(pat))
        );

        if (criticalTouched) {
            reasons.push("Change affects CRITICAL module (auth/payment/etc.).");
            return { result: "blocked", reasons };
        }

        if (riskLevel === "caution") {
            reasons.push("Caution-level change – extra monitoring recommended.");
            return { result: "warn", reasons };
        }

        return { result: "allowed", reasons };
    }
}
