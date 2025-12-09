/**
 * Git integration – for reading code context and creating patches/PRs.
 * Now uses real GitHub API via Octokit.
 */

import { CONFIG } from "../config";
import { CodeDiff } from "../types";
import { Logger } from "../core/logger";
import { Octokit } from "@octokit/rest";

const logger = new Logger("GitService");

interface GitHubFileResponse {
    content: string;
    encoding: string;
    sha: string;
    path: string;
}

export class GitService {
    private octokit: Octokit;
    private owner: string;
    private repo: string;
    private repoUrl: string;

    constructor() {
        this.repoUrl = CONFIG.GIT_REPO_URL;
        const token = CONFIG.GIT_ACCESS_TOKEN;

        if (!token) {
            logger.warn("No GitHub token provided - some operations may fail");
        }

        this.octokit = new Octokit({
            auth: token,
            userAgent: 'AGI-Proto-System/1.0',
            log: {
                debug: (msg) => logger.debug(msg),
                info: (msg) => logger.info(msg),
                warn: (msg) => logger.warn(msg),
                error: (msg) => logger.error(msg)
            }
        });

        // Parse repo URL to extract owner and repo name
        // Supports: https://github.com/owner/repo or owner/repo
        const match = this.repoUrl.match(/(?:github\.com\/)?([^\/]+)\/([^\/\.]+)/);
        if (match) {
            this.owner = match[1];
            this.repo = match[2];
            logger.info(`GitService initialized for ${this.owner}/${this.repo}`);
        } else {
            this.owner = "unknown";
            this.repo = "unknown";
            logger.error(`Invalid GitHub repo URL: ${this.repoUrl}`);
        }
    }

    /**
     * Get file content from GitHub repository
     */
    async getFile(path: string, ref: string = "main"): Promise<string> {
        logger.info(`Fetching file ${path} at ref ${ref}`);

        try {
            const response = await this.octokit.repos.getContent({
                owner: this.owner,
                repo: this.repo,
                path,
                ref
            });

            // Check if it's a file (not a directory)
            if (Array.isArray(response.data)) {
                throw new Error(`Path ${path} is a directory, not a file`);
            }

            const file = response.data as GitHubFileResponse;

            // Decode content (GitHub returns base64 encoded)
            if (file.encoding === 'base64') {
                const content = Buffer.from(file.content, 'base64').toString('utf-8');
                logger.info(`Retrieved ${path} (${content.length} bytes)`);
                return content;
            }

            return file.content;
        } catch (error: any) {
            if (error.status === 404) {
                logger.error(`File not found: ${path}`);
                throw new Error(`File not found: ${path}`);
            }
            logger.error(`Error fetching file ${path}: ${error.message}`);
            throw error;
        }
    }

    /**
     * Create a new branch from an existing ref
     */
    async createBranch(branchName: string, fromRef: string = "main"): Promise<void> {
        logger.info(`Creating branch ${branchName} from ${fromRef}`);

        try {
            // Get the SHA of the ref we're branching from
            const refResponse = await this.octokit.git.getRef({
                owner: this.owner,
                repo: this.repo,
                ref: `heads/${fromRef}`
            });

            const sha = refResponse.data.object.sha;

            // Create new branch
            await this.octokit.git.createRef({
                owner: this.owner,
                repo: this.repo,
                ref: `refs/heads/${branchName}`,
                sha
            });

            logger.info(`Branch ${branchName} created successfully`);
        } catch (error: any) {
            if (error.status === 422) {
                logger.warn(`Branch ${branchName} may already exist`);
            } else {
                logger.error(`Error creating branch: ${error.message}`);
                throw error;
            }
        }
    }

    /**
     * Create a patch and pull request
     */
    async createPatchAndPR(
        diff: CodeDiff,
        branchName: string,
        title: string,
        body: string
    ): Promise<string> {
        logger.info(`Creating PR: ${title}`);

        try {
            // 1. Create branch
            await this.createBranch(branchName);

            // 2. Get current file content and SHA
            const currentFile = await this.octokit.repos.getContent({
                owner: this.owner,
                repo: this.repo,
                path: diff.filePath,
                ref: branchName
            });

            if (Array.isArray(currentFile.data)) {
                throw new Error(`${diff.filePath} is a directory`);
            }

            const fileData = currentFile.data as GitHubFileResponse;
            const currentContent = Buffer.from(fileData.content, 'base64').toString('utf-8');

            // 3. Apply the diff (simple replacement for now)
            // In production, would use proper patch application
            const newContent = this.applyDiff(currentContent, diff);

            // 4. Commit the change
            await this.octokit.repos.createOrUpdateFileContents({
                owner: this.owner,
                repo: this.repo,
                path: diff.filePath,
                message: `AGI: ${title}\n\n${diff.reasoning}`,
                content: Buffer.from(newContent).toString('base64'),
                branch: branchName,
                sha: fileData.sha
            });

            logger.info(`Committed changes to ${branchName}`);

            // 5. Create pull request
            const prResponse = await this.octokit.pulls.create({
                owner: this.owner,
                repo: this.repo,
                title,
                body: this.formatPRBody(diff, body),
                head: branchName,
                base: "main"
            });

            const prUrl = prResponse.data.html_url;
            logger.info(`Pull request created: ${prUrl}`);

            return prUrl;
        } catch (error: any) {
            logger.error(`Error creating PR: ${error.message}`);
            throw error;
        }
    }

    /**
     * Apply a diff to content (simplified - in production use proper patch lib)
     */
    private applyDiff(content: string, diff: CodeDiff): string {
        // For now, just replace the entire content with newCode
        // In production, would:
        // 1. Parse the diff properly
        // 2. Apply line-by-line changes
        // 3. Handle conflicts
        return diff.newCode;
    }

    /**
     * Format PR body with AGI context
     */
    private formatPRBody(diff: CodeDiff, userBody: string): string {
        return `${userBody}

---

## 🤖 AGI-Generated Change

**File**: \`${diff.filePath}\`

**Reasoning**: ${diff.reasoning}

**Risk Level**: ${diff.riskLevel}

**Testing**: ${diff.testingStrategy || 'Manual testing required'}

---

*This PR was automatically generated by the AGI Proto-System.*
*Please review carefully before merging.*
`;
    }

    /**
     * List files in a directory
     */
    async listFiles(path: string = "", ref: string = "main"): Promise<string[]> {
        logger.info(`Listing files in ${path || '/'} at ref ${ref}`);

        try {
            const response = await this.octokit.repos.getContent({
                owner: this.owner,
                repo: this.repo,
                path,
                ref
            });

            if (!Array.isArray(response.data)) {
                return [response.data.path];
            }

            return response.data
                .filter((item: any) => item.type === 'file')
                .map((item: any) => item.path);
        } catch (error: any) {
            logger.error(`Error listing files: ${error.message}`);
            throw error;
        }
    }

    /**
     * Get repository info
     */
    async getRepoInfo(): Promise<any> {
        try {
            const response = await this.octokit.repos.get({
                owner: this.owner,
                repo: this.repo
            });

            return {
                name: response.data.name,
                full_name: response.data.full_name,
                description: response.data.description,
                default_branch: response.data.default_branch,
                language: response.data.language,
                stars: response.data.stargazers_count,
                forks: response.data.forks_count
            };
        } catch (error: any) {
            logger.error(`Error getting repo info: ${error.message}`);
            throw error;
        }
    }
}
