/**
 * Entry point.
 * - Initializes DB schema
 * - Starts periodic AIE and PAK cycles
 */

import { initSchema } from "./integrations/db";
import { AIECycle } from "./aie/aieCycle";
import { PAKLongHorizon } from "./pak/pakLongHorizon";
import { CONFIG } from "./config";
import { Logger } from "./core/logger";

const log = new Logger("main");

async function main() {
    log.info("Initializing AGI Proto-System...");
    await initSchema();

    const aie = new AIECycle();
    const pak = new PAKLongHorizon();

    // Run PAK once at startup; in real deployment use a scheduler
    pak.runOnce().catch((err) => {
        log.error("PAK long-horizon cycle error", err);
    });

    // AIE cycle – run every N seconds (10 minutes default)
    setInterval(() => {
        aie.runOnce().catch((err) => {
            log.error("AIE cycle error", err);
        });
    }, CONFIG.AIE_CYCLE_INTERVAL_SECONDS * 1000);

    log.info("AGI Proto-System started.");
}

main().catch((err) => {
    log.error("Fatal error in main", err);
});
