#!/usr/bin/env node
/**
 * Setup validation script - Run this before first startup
 */

import { validateSetup } from "../core/setupValidator";

async function main() {
    console.log("🚀 AGI Proto-System - Setup Validation\n");

    const isValid = await validateSetup();

    process.exit(isValid ? 0 : 1);
}

main().catch(error => {
    console.error("Fatal error during validation:", error);
    process.exit(1);
});
