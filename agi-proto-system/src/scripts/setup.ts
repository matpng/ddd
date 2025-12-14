#!/usr/bin/env node
/**
 * Interactive setup script - Helps configure the system
 */

import * as fs from "fs";
import * as path from "path";
import { validateSetup } from "../core/setupValidator";

async function main() {
    console.log("=".repeat(60));
    console.log("  AGI Proto-System - Interactive Setup");
    console.log("=".repeat(60) + "\n");

    const envPath = path.join(process.cwd(), ".env");
    const envExamplePath = path.join(process.cwd(), ".env.example");

    // Check if .env exists
    if (!fs.existsSync(envPath)) {
        console.log("📝 No .env file found. Creating from .env.example...\n");

        if (fs.existsSync(envExamplePath)) {
            fs.copyFileSync(envExamplePath, envPath);
            console.log("✅ Created .env file\n");
            console.log("⚠️  IMPORTANT: You must edit .env and add your credentials:\n");
            console.log("   1. OPENAI_API_KEY - Required for LLM operations");
            console.log("   2. DB_URL - PostgreSQL connection string");
            console.log("   3. GIT_ACCESS_TOKEN - GitHub personal access token");
            console.log("   4. Other optional API keys\n");
        } else {
            console.error("❌ .env.example not found!");
            process.exit(1);
        }
    } else {
        console.log("✅ .env file exists\n");
    }

    console.log("Running validation checks...\n");

    const isValid = await validateSetup();

    if (!isValid) {
        console.log("\n📋 Next steps:");
        console.log("   1. Edit .env and add missing credentials");
        console.log("   2. Install PostgreSQL if not already installed");
        console.log("   3. Create database: createdb agi_proto");
        console.log("   4. Enable pgvector: psql agi_proto -c 'CREATE EXTENSION vector;'");
        console.log("   5. Run 'npm run validate' again\n");
        process.exit(1);
    }

    console.log("\n🎉 Setup complete! You can now run:\n");
    console.log("   npm run dev    - Start in development mode");
    console.log("   npm start      - Start in production mode");
    console.log("   npm test       - Run tests\n");

    process.exit(0);
}

main().catch(error => {
    console.error("Setup failed:", error);
    process.exit(1);
});
