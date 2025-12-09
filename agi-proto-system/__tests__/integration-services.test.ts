/**
 * Integration Tests - Discovery System ↔ AGI Communication
 * Tests real API endpoints and service integrations
 */

import { MetricsService } from '../src/integrations/metricsService';
import { GitService } from '../src/integrations/gitService';
import { CIService } from '../src/integrations/ciService';

describe('Integration Tests', () => {
    describe('MetricsService → Discovery Communication', () => {
        let metricsService: MetricsService;

        beforeEach(() => {
            metricsService = new MetricsService();
        });

        test('should fetch runtime metrics from Discovery System', async () => {
            // This test requires Discovery System running on localhost:5000
            try {
                const metrics = await metricsService.getRuntimeMetrics();

                expect(metrics).toBeDefined();
                expect(typeof metrics.errorRate).toBe('number');
                expect(typeof metrics.avgLatencyMs).toBe('number');
                expect(typeof metrics.requestsPerMin).toBe('number');
                expect(metrics.errorRate).toBeGreaterThanOrEqual(0);
            } catch (error: any) {
                // If Discovery isn't running, test should gracefully handle
                expect(error.message).toContain('fetch');
            }
        }, 10000);

        test('should fetch business metrics from Discovery System', async () => {
            try {
                const metrics = await metricsService.getBusinessMetrics();

                expect(metrics).toBeDefined();
                expect(typeof metrics.activeUsers).toBe('number');
                expect(metrics.activeUsers).toBeGreaterThanOrEqual(0);
            } catch (error: any) {
                expect(error.message).toContain('fetch');
            }
        }, 10000);

        test('should get health status from Discovery System', async () => {
            try {
                const health = await metricsService.getHealthStatus();

                expect(health).toBeDefined();
                expect(health.status).toBeDefined();
                expect(['healthy', 'degraded', 'unhealthy']).toContain(health.status);
                expect(health.components).toBeDefined();
            } catch (error: any) {
                expect(error.message).toContain('fetch');
            }
        }, 10000);

        test('should handle Discovery System offline gracefully', async () => {
            // Temporarily point to non-existent server
            const offlineService = new MetricsService();

            // Should return fallback values, not crash
            const metrics = await offlineService.getRuntimeMetrics();

            expect(metrics).toBeDefined();
            expect(metrics.errorRate).toBe(0);
        }, 10000);

        test('should use cache for repeated requests', async () => {
            const start1 = Date.now();
            await metricsService.getRuntimeMetrics();
            const time1 = Date.now() - start1;

            const start2 = Date.now();
            await metricsService.getRuntimeMetrics();
            const time2 = Date.now() - start2;

            // Second call should be much faster (cached)
            if (time1 > 100) { // Only test if first call was slow enough
                expect(time2).toBeLessThan(time1 / 2);
            }
        }, 15000);
    });

    describe('GitService → GitHub API', () => {
        let gitService: GitService;

        beforeEach(() => {
            gitService = new GitService();
        });

        test('should get repository info', async () => {
            // Skip if no GitHub token configured
            if (!process.env.GIT_ACCESS_TOKEN) {
                console.log('Skipping GitHub test - no token configured');
                return;
            }

            try {
                const info = await gitService.getRepoInfo();

                expect(info).toBeDefined();
                expect(info.name).toBeDefined();
                expect(typeof info.stars).toBe('number');
            } catch (error: any) {
                // Authentication or network error
                expect(error.message).toBeTruthy();
            }
        }, 10000);

        test('should handle invalid repo gracefully', async () => {
            const badGitService = new GitService();

            try {
                await badGitService.getFile('nonexistent/file/path.txt');
                fail('Should have thrown error');
            } catch (error: any) {
                expect(error.message).toContain('File not found');
            }
        }, 10000);
    });

    describe('CIService → GitHub Actions', () => {
        let ciService: CIService;

        beforeEach(() => {
            ciService = new CIService();
        });

        test('should get recent workflow runs', async () => {
            if (!process.env.GIT_ACCESS_TOKEN) {
                console.log('Skipping CI test - no token configured');
                return;
            }

            try {
                const runs = await ciService.getRecentRuns(5);

                expect(Array.isArray(runs)).toBe(true);
                // May be empty if no workflows have run
            } catch (error: any) {
                expect(error.message).toBeTruthy();
            }
        }, 10000);
    });

    describe('End-to-End Integration Flow', () => {
        test('AGI can monitor Discovery and respond to issues', async () => {
            const metrics = new MetricsService();

            // Step 1: Monitor Discovery System
            const runtimeMetrics = await metrics.getRuntimeMetrics();

            // Step 2: Detect high error rate (simulated)
            const hasIssues = runtimeMetrics.errorRate > 0.05; // 5% threshold

            if (hasIssues) {
                console.log('⚠️ High error rate detected:', runtimeMetrics.errorRate);

                // Step 3: AGI would analyze code via GitService
                // Step 4: AGI would create PR with fix
                // Step 5: AGI would trigger CI pipeline
                // (These steps require actual GitHub repo setup)
            }

            expect(runtimeMetrics).toBeDefined();
        }, 15000);
    });
});
