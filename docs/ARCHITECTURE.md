# Architecture Documentation - AGI + Discovery Integration

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          User Interface                              │
│                    http://localhost:5000                            │
└────────────────────────────┬────────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────────┐
│                    Discovery System (Python/Flask)                   │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  Web Application (app.py - 2,536 lines)                        │ │
│  │  - Dashboard UI                                                 │ │
│  │  - Analysis endpoints                                           │ │
│  │  - Discovery management                                         │ │
│  └────────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  AGI Integration API (3 new endpoints)                         │ │
│  │  - /api/agi/metrics  (runtime & business metrics)              │ │
│  │  - /api/agi/health   (health check & status)                   │ │
│  │  - /api/agi/code/*   (secure code file access)                 │ │
│  └────────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  Core Engine                                                    │ │
│  │  - orion_octave_test.py (geometric analysis)                   │ │
│  │  - discovery_manager.py (discovery tracking)                   │ │
│  │  - pak_agents.py (Python PAK agents)                           │ │
│  └────────────────────────────────────────────────────────────────┘ │
└────────────────────────────┬────────────────────────────────────────┘
                             │ HTTP/JSON
                             │ (30s polling)
┌────────────────────────────▼────────────────────────────────────────┐
│                      AGI System (TypeScript/Node.js)                 │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  Integration Services                                           │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │ │
│  │  │ MetricsService│  │  GitService  │  │  CIService   │         │ │
│  │  │ - Monitors   │  │ - Read code  │  │ - Trigger CI │         │ │
│  │  │ - Caches 30s │  │ - Create PRs │  │ - Monitor    │         │ │
│  │  │ - Retry 3x   │  │ - Octokit API│  │ - Poll status│         │ │
│  │  └───────┬──────┘  └──────┬───────┘  └──────┬───────┘         │ │
│  └──────────┼─────────────────┼──────────────────┼────────────────┘ │
│             │                 │                  │                   │
│  ┌──────────▼─────────────────▼──────────────────▼────────────────┐ │
│  │  AIE (Autonomous Improvement Engine)                            │ │
│  │  - ArchitectAgent  (planning)                                   │ │
│  │  - EngineerAgent   (code generation)                            │ │
│  │  - QAAgent         (testing)                                    │ │
│  │  - DiagnosticsAgent (root cause analysis)                       │ │
│  │  - DeploymentAgent (rollout strategies)                         │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │  PAK (Proto-AGI Kernel)                                         │ │
│  │  - GoalEngineAgent      (goal creation & prioritization)        │ │
│  │  - ValueAlignmentAgent  (ethical decision making)               │ │
│  │  - WorldModelAgent      (external knowledge)                    │ │
│  │  - SelfModelAgent       (capability assessment)                 │ │
│  │  - ReflectionAgent      (learning from experience)              │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │  Experience Store                                                │ │
│  │  - Past successes/failures                                       │ │
│  │  - Semantic search (embeddings)                                  │ │
│  │  - Lessons learned                                               │ │
│  └─────────────────────────────────────────────────────────────────┘ │
└────────────────────────────┬────────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────────┐
│                    External Integrations                             │
│  ┌───────────────┐  ┌────────────────┐  ┌─────────────────┐        │
│  │  GitHub API   │  │  LLM Providers │  │  Web Research   │        │
│  │  - Read code  │  │  - OpenAI      │  │  - DuckDuckGo   │        │
│  │  - Create PRs │  │  - Anthropic   │  │  - Content ext  │        │
│  │  - CI/CD      │  │  - Generate    │  │  - Summarize    │        │
│  └───────────────┘  └────────────────┘  └─────────────────┘        │
└─────────────────────────────────────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────────┐
│                    Data Layer                                        │
│  ┌──────────────────────┐     ┌─────────────────────────────────┐  │
│  │  SQLite (Current)    │ ──→ │  PostgreSQL + pgvector (Future) │  │
│  │  - Discoveries       │     │  - Unified schema               │  │
│  │  - PAK data          │     │  - Vector embeddings            │  │
│  │  - Goals & values    │     │  - Shared experiences           │  │
│  └──────────────────────┘     └─────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

## Data Flow: Autonomous Improvement Loop

```
1. MONITOR
   AGI MetricsService → /api/agi/metrics (every 30s)
   ↓
   Detects: High error rate (errorRate > 0.05)

2. ANALYZE
   AGI retrieves code → /api/agi/code/orion_octave_test.py
   ↓
   CodeContextBuilder analyzes dependencies
   ↓
   AIE ArchitectAgent plans fix using LLM

3. GENERATE FIX
   AIE EngineerAgent generates code changes
   ↓
   Self-critique and refinement loop
   ↓
   Create CodeDiff with reasoning

4. CREATE PR
   GitService.createBranch("agi-fix-errors")
   ↓
   GitService.createPatchAndPR(diff, ...)
   ↓
   GitHub PR created

5. TRIGGER CI
   CIService.triggerPipeline("agi-fix-errors")
   ↓
   GitHub Actions runs tests
   ↓
   CIService.waitForCompletion()

6. LEARN
   If tests pass → Record success in ExperienceStore
   If tests fail → ReflectionAgent analyzes why
   ↓
   Update self-model and value weights
   ↓
   Loop back to step 1
```

## Component Interactions

### Discovery → AGI Communication

```typescript
// AGI polls Discovery every 30s
const metrics = new MetricsService();
setInterval(async () => {
  const runtime = await metrics.getRuntimeMetrics();
  
  if (runtime.errorRate > 0.05) {
    // Trigger improvement cycle
    await aie.runCycle({
      goal: 'Fix high error rate',
      context: `Error rate: ${runtime.errorRate}`
    });
  }
}, 30000);
```

### AGI → GitHub → CI/CD Flow

```typescript
// Complete improvement workflow
async function improveDiscoverySystem() {
  // 1. Get metrics
  const metrics = await metricsService.getRuntimeMetrics();
  
  // 2. If issues detected, analyze code
  if (metrics.errorRate > threshold) {
    const code = await fetch('/api/agi/code/app.py');
    
    // 3. Generate fix
    const fix = await engineerAgent.generateFix(code);
    
    // 4. Create PR
    const prUrl = await gitService.createPatchAndPR(
      fix,
      'agi-performance-fix',
      'AGI: Optimize slow endpoint',
      'Detected 500ms avg latency...'
    );
    
    // 5. Trigger CI
    const pipelineId = await ciService.triggerPipeline('agi-performance-fix');
    
    // 6. Wait for results
    const status = await ciService.waitForCompletion(pipelineId);
    
    // 7. Learn
    if (status === 'succeeded') {
      await experienceStore.recordSuccess(fix);
    } else {
      await reflectionAgent.analyzeFailure(fix);
    }
  }
}
```

## Security Architecture

### Current (Development)
- ❌ No API authentication
- ✅ Rate limiting via `@rate_limit`
- ✅ Directory traversal protection
- ✅ Input validation

### Planned (Production)
- 🔒 Token-based API authentication
- 🔒 HTTPS only
- 🔒 Secrets management (Vault)
- 🔒 IP whitelist (optional)
- 🔒 Request signing

## Deployment Architecture

### Docker Compose Stack

```yaml
services:
  postgres:         # Shared database
    ↓
  discovery:        # Python/Flask web app
    ↓
  agi:              # TypeScript/Node.js services
```

### Network Flow
- User → Discovery (port 5000)
- AGI → Discovery (internal network)
- AGI → GitHub API (external)
- Both → PostgreSQL (internal)

## Performance Characteristics

### Metrics Caching
- Cache duration: 30 seconds
- Reduces load by 95%
- Stale-while-revalidate pattern

### Retry Strategy
- Max retries: 3
- Backoff: Exponential (1s, 2s, 4s)
- Timeout: 5 seconds per attempt

### Database
- SQLite: Local file, no setup
- PostgreSQL: Shared, scalable, vector search

## Scalability Considerations

### Current Limits
- Single Discovery instance
- Single AGI instance
- SQLite (single writer)

### Future Scaling
- Multiple Discovery replicas (load balanced)
- AGI worker pool (distributed)
- PostgreSQL (connection pooling)
- Message queue for async tasks
- Redis for distributed caching

---

**Architecture Status**: ✅ Functional, 🟡 PostgreSQL migration pending  
**Scale**: Single instance, suitable for development & small production  
**Next Evolution**: Database migration → horizontal scaling
