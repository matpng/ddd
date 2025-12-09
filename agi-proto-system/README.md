# AGI Proto-System

**AI Improvement Engine (AIE) + Proto-AGI Kernel (PAK)**

A reference implementation skeleton for an autonomous code improvement system with goal-directed planning.

## Overview

This system combines two major components:

### 🤖 AIE (AI Improvement Engine)
- **10-minute improvement cycles** that autonomously:
  - Analyze metrics to identify problems
  - Create change plans
  - Generate code diffs
  - Evaluate changes with policy + CI
  - Deploy via canary releases

### 🧠 PAK (Proto-AGI Kernel)  
- **Long-horizon planning** (daily/weekly) that:
  - Manages system goals
  - Links goals to metrics
  - Prioritizes objectives
  - Guides AIE's tactical decisions

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         PAK Layer                            │
│  Goal Engine · Value/Ethics · World Model · Self Model      │
│  (Long-horizon planning: days/weeks)                        │
└──────────────────────────┬──────────────────────────────────┘
                           │ Goals & Constraints
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                         AIE Layer                            │
│  Diagnostics → Architect → Engineer → QA → Deployment       │
│  (Short-horizon execution: 10-min cycles)                   │
└──────────────────────────┬──────────────────────────────────┘
                           │ Code Changes
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    Your Application                          │
│  Web App · API · Services · Database                        │
└─────────────────────────────────────────────────────────────┘
```

## Directory Structure

```
agi-proto-system/
├── src/
│   ├── index.ts              # Main entry point
│   ├── config.ts             # Configuration
│   ├── types.ts              # Shared types
│   │
│   ├── core/                 # Core infrastructure
│   │   ├── logger.ts
│   │   ├── policyEngine.ts   # Safety rules
│   │   ├── riskClassifier.ts
│   │   └── system Snapshot.ts
│   │
│   ├── integrations/         # External service integrations
│   │   ├── db.ts             # Postgres database
│   │   ├── gitService.ts     # GitHub/GitLab
│   │   ├── ciService.ts      # CI/CD pipelines
│   │   ├── metricsService.ts # Prometheus/Datadog
│   │   └── webResearchService.ts
│   │
│   ├── aie/                  # AI Improvement Engine
│   │   ├── diagnosticsAgent.ts  # Problem identification
│   │   ├── architectAgent.ts    # Change planning
│   │   ├── engineerAgent.ts     # Code generation
│   │   ├── qaAgent.ts           # Quality assurance
│   │   ├── deploymentAgent.ts   # Canary deployment
│   │   └── aieCycle.ts          # Main orchestrator
│   │
│   ├── pak/                  # Proto-AGI Kernel
│   │   ├── goalEngineAgent.ts
│   │   └── pakLongHorizon.ts
│   │
│   └── models/
│       └── pakModels.ts      # Goal & Value types
│
├── package.json
├── tsconfig.json
└── .env.example
```

## Quick Start

### 1. Install Dependencies

```bash
npm install
```

### 2. Configure Environment

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Required configuration:
- `OPENAI_API_KEY` - For LLM-powered agents
- `DB_URL` - Postgres connection string
- `GIT_ACCESS_TOKEN` - GitHub/GitLab token
- `CI_API_TOKEN` - CI/CD system token
- `METRICS_API_KEY` - Metrics provider key

### 3. Build

```bash
npm run build
```

### 4. Run

```bash
# Development mode
npm run dev

# Production mode
npm start
```

## How It Works

### AIE Cycle (Every 10 minutes)

1. **Diagnostics**: Analyze runtime/business metrics → identify issues
2. **Architect**: Convert issue → change plan with success criteria
3. **Engineer**: Generate code diff to address the plan
4. **QA**: Evaluate diff against:
   - Policy rules (safety constraints)
   - CI test results
   - Risk classification
5. **Deployment**: If approved → create PR → canary deploy → monitor

### PAK Cycle (Daily/Weekly)

1. **Goal Review**: List active system goals
2. **Goal Creation**: If needed, create new goals based on metrics
3. **Prioritization**: Adjust goal priorities based on world state
4. **Guidance**: Goals inform AIE's improvement priorities

## Safety & Policy

The system includes multiple safety layers:

- **PolicyEngine**: Blocks changes to critical files (auth, payment, etc.)
- **RiskClassifier**: Categorizes changes as safe/caution/critical
- **QAAgent**: Enforces CI tests + policy before deployment
- **Canary Deployment**: Monitors metrics before full rollout

## Customization

### Adding New Policy Rules

Edit `src/core/policyEngine.ts`:

```typescript
const criticalPatterns = ["auth", "payment", "your-critical-module"];
```

### Adjusting Cycle Intervals

In `.env`:

```bash
AIE_CYCLE_INTERVAL_SECONDS=600      # 10 minutes
PAK_LONG_HORIZON_INTERVAL_HOURS=24  # 24 hours
```

### Custom Integrations

Implement your own service integrations in `src/integrations/`:
- Replace `GitService` with your Git provider
- Replace `CIService` with your CI/CD system
- Replace `MetricsService` with your APM provider

## Development

```bash
# Run in development mode with auto-reload
npm run dev

# Build TypeScript
npm run build

# Lint code
npm run lint
```

## Database Schema

The system creates these main tables:

### Core Tables
- `system_state_snapshots` - Periodic system state captures
- `experiments` - Track improvement experiments
- `goals` - PAK goal hierarchy
- `values_table` - Ethical/value alignment data (with examples)

### AGI Enhancement Tables
- `experiences` - Learning & memory with vector embeddings for semantic search
- `world_observations` - External factor tracking
- `capability_assessments` - Self-model capability tracking
- `value_evaluations` - Ethical alignment audit trail
- `predictions` - Proactive issue forecasting

Requires **PostgreSQL with pgvector extension** for semantic search capabilities.

Initialize with:

```typescript
import { initSchema } from "./integrations/db";
await initSchema();
```

## Production Deployment

1. Set `NODE_ENV=production`
2. Configure production database
3. Set up proper API keys and tokens
4. Deploy to your infrastructure
5. Monitor AIE cycle outputs
6. Review auto-generated PRs before merge

## AGI Capabilities

This system now includes **fully implemented AGI features**:

### ✅ Implemented

- **LLM Integration**: Real OpenAI GPT-4 + Anthropic Claude with automatic fallback
- **Learning & Memory**: Experience store with semantic search (vector embeddings)
- **Self-Awareness**: Tracks capabilities, limitations, and confidence levels
- **Value Alignment**: 6 default ethical values with conflict detection
- **World Model**: Researches external factors, detects trends, generates predictions
- **Reflection**: Analyzes every experience to extract actionable lessons
- **Proactive Planning**: Creates goals before problems occur based on predictions
- **Self-Improvement**: Addresses self-identified limitations autonomously

### 🔧 Integration Status

- ✅ **Architecture**: Complete and fully integrated
- ✅ **LLM Agents**: Real AI-powered code generation and planning
- ✅ **PAK Layer**: World model, self model, value alignment active
- ✅ **Learning Loop**: Continuous improvement from experience
- ⚠️ **External Services**: Git/CI/Metrics use mock implementations (customizable)
- ⚠️ **Testing**: Manual verification recommended before full autonomy

## Getting Started

### Prerequisites

1. **Node.js** 18+ and npm
2. **PostgreSQL** with pgvector extension
3. **API Keys**:
   - OpenAI API key (required)
   - Anthropic API key (optional, for fallback)

### Installation

```bash
# Install dependencies
npm install

# Set up environment
cp .env.example .env
# Edit .env and add your API keys

# Install pgvector in PostgreSQL
psql your_database -c "CREATE EXTENSION vector;"

# Build and run
npm run build
npm start

# Or development mode
npm run dev
```

### First Run

The system will:
1. Initialize database schema automatically
2. Create default ethical values
3. Run PAK cycle to create initial goals
4. Begin AIE improvement cycles every 10 minutes

### Customization

1. **Adjust Value Weights**: Edit default values in `valueAlignmentAgent.ts`
2. **Add Policy Rules**: Customize `policyEngine.ts` for your critical files
3. **Set Cycle Intervals**: Configure in `.env`
4. **Connect Real Services**: Implement your Git/CI/Metrics integrations

## Production Readiness

### What's Ready for Production

✅ Core AGI loop (learning, reflection, improvement)  
✅ LLM integration with retry and fallback  
✅ Value alignment and ethical constraints  
✅ Self-awareness and confidence scoring  
✅ Experience-based learning  
✅ Proactive goal creation  

### Before Going Live

1. **Test Thoroughly**: Run in staging environment first
2. **Connect Real Services**: Implement actual Git/CI/Metrics APIs  
3. **Monitor Closely**: Review first few autonomous changes manually
4. **Set Thresholds**: Adjust confidence and alignment thresholds
5. **Define Values**: Customize ethical values for your domain
6. **Enable Logging**: Monitor AIE/PAK cycles and experiences

## License

MIT

## Contributing

This is a reference implementation. Feel free to adapt for your needs!

---

**Built with**: TypeScript · Node.js · PostgreSQL

**Inspired by**: Autonomous AI research, self-improving systems, goal-directed planning
