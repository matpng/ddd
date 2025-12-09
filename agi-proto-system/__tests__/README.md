# Test Suite - AGI Proto-System

## Running Tests

```bash
# Install dependencies first
npm install

# Run all tests
npm test

# Run tests in watch mode (auto-rerun on changes)
npm run test:watch

# Run tests with coverage report
npm run test:coverage
```

## Test Structure

### Unit Tests

- **`llmClient.test.ts`** - LLM client functionality
  - Message formatting
  - Options validation
  - Provider selection
  - Cost tracking

- **`experienceStore.test.ts`** - Experience recording and retrieval
  - Recording success/failure/learning experiences
  - Experience retrieval with filters
  - Reflection addition
  - Success rate calculation

- **`valueAlignment.test.ts`** - Value alignment system
  - Default value initialization
  - Plan evaluation
  - Value scoring
  - Conflict detection
  - Recommendations

- **`reflectionAgent.test.ts`** - Learning and reflection
  - Experience reflection  
  - Lesson extraction
  - Pattern identification
  - Confidence scoring

### Integration Tests

- **`integration.test.ts`** - End-to-end testing
  - Full AIE cycle execution
  - Learning loop integration
  - Error handling
  - Component integration

## Test Coverage

Run coverage report:
```bash
npm run test:coverage
```

Coverage reports are generated in the `coverage/` directory.

## Mocking Strategy

### External Dependencies

All external API calls are mocked:
- **Database queries**: Mocked with `jest.mock('../src/integrations/db')`
- **LLM calls**: Mocked with `jest.mock('../src/core/llmClient')`
- **OpenAI embeddings**: Mocked with `jest.mock('openai')`

### Integration Tests

For real API testing (requires valid API keys):
- Tests are marked with `.skip` by default
- Remove `.skip` to run with real APIs
- Set `OPENAI_API_KEY` and `ANTHROPIC_API_KEY` in environment

## Writing New Tests

### Test File Template

```typescript
/**
 * Tests for MyComponent
 */

import { MyComponent } from '../src/path/to/component';

// Mock dependencies
jest.mock('../src/integrations/db');

describe('MyComponent', () => {
    let component: MyComponent;

    beforeEach(() => {
        component = new MyComponent();
        jest.clearAllMocks();
    });

    describe('Feature Name', () => {
        it('should do something specific', () => {
            // Arrange
            const input = 'test';

            // Act
            const result = component.method(input);

            // Assert
            expect(result).toBe('expected');
        });
    });
});
```

## Test Environment

- **Framework**: Jest 29.7
- **TypeScript**: ts-jest
- **Timeout**: 30s (for LLM calls)
- **Node**: 18+

## Continuous Testing

For development:
```bash
# Watch mode - automatically reruns tests on file changes
npm run test:watch
```

## Debugging Tests

### VS Code

Add to `.vscode/launch.json`:
```json
{
    "type": "node",
    "request": "launch",
    "name": "Jest Debug",
    "program": "${workspaceFolder}/node_modules/.bin/jest",
    "args": ["--runInBand", "--no-cache"],
    "console": "integratedTerminal",
    "internalConsoleOptions": "neverOpen"
}
```

### Command Line

```bash
# Run specific test file
npm test -- llmClient.test.ts

# Run tests matching pattern
npm test -- --testNamePattern="should record experience"

# Verbose output
npm test -- --verbose
```

## Coverage Goals

| Component | Target | Current |
|-----------|--------|---------|
| Core (llmClient, experienceStore) | 80% | ✅ |
| PAK Agents | 70% | ✅ |
| AIE Agents | 70% | ⚠️ Partial |
| Integrations | 50% | ⚠️ Mocked |
| Overall | 70% | ⚠️ Run coverage |

## Known Limitations

1. **External APIs**: Most tests use mocks, not real APIs
2. **Database**: Database queries are mocked
3. **File System**: Code analysis tests use mocked files
4. **Time-Dependent**: Some tests may be time-sensitive

## Future Enhancements

- [ ] Add tests for diagnostics agent
- [ ] Add tests for engineer agent (code generation)
- [ ] Add tests for architect agent
- [ ] Add tests for world model
- [ ] Add tests for self model
- [ ] E2E tests with test database
- [ ] Performance/load testing
- [ ] Contract testing for LLM responses

## Troubleshooting

### "Cannot find module" errors
```bash
npm install
```

### Tests timing out
- Increase timeout in jest.config.js
- Check if API calls are properly mocked

### Coverage not generated
```bash
# Clear Jest cache
npm test -- --clearCache
npm run test:coverage
```

---

**All tests passing = AGI system is healthy!** ✅
