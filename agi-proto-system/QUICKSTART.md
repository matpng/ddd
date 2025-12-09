# Quick Start Guide - AGI Proto-System

## Installation (5 minutes)

```bash
# 1. Navigate to project
cd c:\Users\fc\Documents\GitHub\ddd\agi-proto-system

# 2. Install dependencies
npm install

# 3. Copy environment template
copy .env.example .env

# 4. Build
npm run build
```

## Configuration

Edit `.env` with your credentials:

```bash
# Required
OPENAI_API_KEY=sk-...                    # OpenAI API key
DB_URL=postgres://localhost:5432/agi_proto  # PostgreSQL

# Optional (can use defaults for testing)
GIT_ACCESS_TOKEN=                         # GitHub token
CI_API_TOKEN=                             # CI/CD token
METRICS_API_KEY=                          # Metrics provider
```

## Run

```bash
# Development mode (with auto-reload)
npm run dev

# Production mode
npm start
```

## What Happens

1. **Database Init**: Creates 4 tables automatically
2. **PAK Cycle**: Runs once, creates initial goals
3. **AIE Cycle**: Runs every 10 minutes, looking for improvements

## First Steps After Install

### 1. Check Logs

Watch for:
- `[PAKLongHorizon] Starting PAK long-horizon planning cycle...`
- `[AIECycle] Starting AIE cycle...`
- `[DiagnosticsAgent] Analyzing metrics for issues`

### 2. Inspect Database

```sql
-- View created goals
SELECT * FROM goals;

-- View system snapshots
SELECT * FROM system_state_snapshots;
```

### 3. Customize Policy

Edit `src/core/policyEngine.ts`:

```typescript
const criticalPatterns = [
  "auth",
  "payment",
  "your-critical-module"  // Add your modules
];
```

### 4. Add Real Integrations

Replace stubs in:
- `src/integrations/gitService.ts` - GitHub API
- `src/integrations/ciService.ts` - Your CI/CD
- `src/integrations/metricsService.ts` - Prometheus/Datadog

### 5. Implement LLM Calls

In `src/aie/engineerAgent.ts`:

```typescript
import OpenAI from "openai";
import { CONFIG } from "../config";

const openai = new OpenAI({ apiKey: CONFIG.OPENAI_API_KEY });

async proposeDiff(plan: ChangePlan): Promise<CodeDiff> {
  const response = await openai.chat.completions.create({
    model: "gpt-4",
    messages: [
      {
        role: "system",
        content: "You are a code improvement engineer."
      },
      {
        role: "user",
        content: `Create a code diff for: ${plan.description}`
      }
    ]
  });
  
  // Parse response into CodeDiff
  // ...
}
```

## Testing Without Real Services

The system works out of the box with mocked services:

- **Metrics**: Returns fake data
- **Git**: Logs operations without actual API calls  
- **CI**: Always returns "succeeded"
- **LLM**: Returns stub diffs

This lets you test the architecture before connecting real services.

## Troubleshooting

**"Cannot connect to database"**
```bash
# Create database first
createdb agi_proto

# Or use existing database
DB_URL=postgres://user:pass@localhost:5432/existing_db
```

**"Module not found"**
```bash
npm install
npm run build
```

**"AIE cycle not running"**
- Check logs for errors
- Verify `AIE_CYCLE_INTERVAL_SECONDS` in .env
- Default is 600 seconds (10 minutes)

## Next Steps

1. ✅ Install and run
2. ⏳ Add real API integrations
3. ⏳ Implement LLM calls
4. ⏳ Test with your codebase
5. ⏳ Deploy to production

---

**Ready to start!** Run `npm run dev` to begin.
