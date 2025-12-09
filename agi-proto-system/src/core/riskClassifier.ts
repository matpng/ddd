/**
 * Risk classifier – classifies change risk based on file paths, patterns, etc.
 * Here we use simple heuristics; you can extend this with ML if needed.
 */

import { RiskLevel } from "../types";

export class RiskClassifier {
    classify(filesTouched: string[]): RiskLevel {
        const criticalKeywords = ["auth", "payment", "billing", "encryption"];
        const cautionKeywords = ["db", "repository", "service"];

        if (filesTouched.some((f) => criticalKeywords.some((k) => f.toLowerCase().includes(k)))) {
            return "critical";
        }

        if (filesTouched.some((f) => cautionKeywords.some((k) => f.toLowerCase().includes(k)))) {
            return "caution";
        }

        return "safe";
    }
}
