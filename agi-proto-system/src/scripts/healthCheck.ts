#!/usr/bin/env node
/**
 * Health check script - Quick status check of all systems
 */

import { SetupValidator } from "../core/setupValidator";
import { ErrorHandler } from "../core/errorHandler";
import { Logger } from "../core/logger";

const log = new Logger("HealthCheck");

async function main() {
    console.log("\n🏥 AGI Proto-System - Health Check\n");

    // Run setup validation
    const validator = new SetupValidator();
    const result = await validator.validate();

    // Check circuit breaker states
    const circuitStates = ErrorHandler.getCircuitBreakerStates();

    console.log("🔌 Circuit Breakers:");
    if (Object.keys(circuitStates).length === 0) {
        console.log("   No active circuit breakers\n");
    } else {
        for (const [name, state] of Object.entries(circuitStates)) {
            const emoji = state === "closed" ? "✅" : state === "open" ? "❌" : "⚠️";
            console.log(`   ${emoji} ${name}: ${state}`);
        }
        console.log();
    }

    // Overall health
    const isHealthy = result.valid &&
        Object.values(circuitStates).every(s => s === "closed" || s === "half-open");

    if (isHealthy) {
        console.log("✅ SYSTEM HEALTHY\n");
        process.exit(0);
    } else {
        console.log("⚠️  SYSTEM DEGRADED - Check errors above\n");
        process.exit(1);
    }
}

main().catch(error => {
    console.error("Health check failed:", error);
    process.exit(1);
});
