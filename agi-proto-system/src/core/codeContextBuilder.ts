/**
 * Code Context Builder - Gathers relevant code context for LLM understanding.
 * Analyzes TypeScript/JavaScript files, builds dependency graphs, and prepares
 * context for AI agents.
 */

import * as fs from "fs/promises";
import * as path from "path";
import { parse } from "@babel/parser";
import traverse from "@babel/traverse";
import { Logger } from "./logger";
import { llmClient } from "./llmClient";

const log = new Logger("CodeContextBuilder");

export interface FileContext {
    path: string;
    relativePath: string;
    content: string;
    imports: string[];
    exports: string[];
    functions: FunctionInfo[];
    classes: ClassInfo[];
    complexity: number;
}

export interface FunctionInfo {
    name: string;
    params: string[];
    lineStart: number;
    lineEnd: number;
}

export interface ClassInfo {
    name: string;
    methods: string[];
    lineStart: number;
    lineEnd: number;
}

export interface DependencyGraph {
    nodes: Map<string, DependencyNode>;
    edges: Map<string, string[]>;
}

export interface DependencyNode {
    path: string;
    type: "internal" | "external" | "builtin";
}

export interface CodeContext {
    files: FileContext[];
    dependencies: DependencyGraph;
    totalTokens: number;
    tokenBudget: number;
}

export interface ContextOptions {
    targetModuleIds: string[];
    maxFiles?: number;
    maxTokens?: number;
    includeTests?: boolean;
    includeDependencies?: boolean;
    basePath?: string;
}

export class CodeContextBuilder {
    private basePath: string;

    constructor(basePath?: string) {
        this.basePath = basePath || process.cwd();
    }

    async buildContext(options: ContextOptions): Promise<CodeContext> {
        const {
            targetModuleIds,
            maxFiles = 20,
            maxTokens = 8000,
            includeTests = true,
            includeDependencies = true
        } = options;

        log.info("Building code context", { targetModuleIds, maxTokens });

        // 1. Gather target files
        const targetFiles = await this.gatherFiles(targetModuleIds, maxFiles);

        // 2. Parse files and extract metadata
        const fileContexts = await Promise.all(
            targetFiles.map(f => this.analyzeFile(f))
        );

        // 3. Build dependency graph
        const dependencies = includeDependencies
            ? await this.buildDependencyGraph(fileContexts)
            : { nodes: new Map(), edges: new Map() };

        // 4. Include test files if requested
        if (includeTests) {
            const testFiles = await this.findTestFiles(targetFiles);
            const testContexts = await Promise.all(
                testFiles.map(f => this.analyzeFile(f))
            );
            fileContexts.push(...testContexts);
        }

        // 5. Truncate to token budget
        const truncated = this.truncateToTokenBudget(fileContexts, maxTokens);

        log.info(`Built context: ${truncated.files.length} files, ${truncated.totalTokens} tokens`);

        return {
            files: truncated.files,
            dependencies,
            totalTokens: truncated.totalTokens,
            tokenBudget: maxTokens
        };
    }

    private async gatherFiles(moduleIds: string[], maxFiles: number): Promise<string[]> {
        const files: string[] = [];

        for (const moduleId of moduleIds) {
            // Convert module ID to file path
            const filePath = this.resolveModulePath(moduleId);

            if (await this.fileExists(filePath)) {
                files.push(filePath);
            } else {
                log.warn(`File not found: ${filePath}`);
            }

            if (files.length >= maxFiles) {
                break;
            }
        }

        return files;
    }

    private async analyzeFile(filePath: string): Promise<FileContext> {
        const content = await fs.readFile(filePath, "utf-8");
        const relativePath = path.relative(this.basePath, filePath);

        // Parse to AST
        let ast;
        try {
            ast = parse(content, {
                sourceType: "module",
                plugins: ["typescript", "jsx"]
            });
        } catch (error) {
            log.warn(`Failed to parse ${filePath}`, error);
            return {
                path: filePath,
                relativePath,
                content,
                imports: [],
                exports: [],
                functions: [],
                classes: [],
                complexity: 0
            };
        }

        const imports: string[] = [];
        const exports: string[] = [];
        const functions: FunctionInfo[] = [];
        const classes: ClassInfo[] = [];
        let complexity = 0;

        traverse(ast, {
            ImportDeclaration(path) {
                imports.push(path.node.source.value);
            },
            ExportNamedDeclaration(path) {
                if (path.node.declaration) {
                    if (path.node.declaration.type === "FunctionDeclaration") {
                        const name = path.node.declaration.id?.name;
                        if (name) exports.push(name);
                    } else if (path.node.declaration.type === "ClassDeclaration") {
                        const name = path.node.declaration.id?.name;
                        if (name) exports.push(name);
                    }
                }
            },
            FunctionDeclaration(path) {
                const name = path.node.id?.name || "anonymous";
                const params = path.node.params.map(p => {
                    if (p.type === "Identifier") return p.name;
                    return "...";
                });

                functions.push({
                    name,
                    params,
                    lineStart: path.node.loc?.start.line || 0,
                    lineEnd: path.node.loc?.end.line || 0
                });

                complexity += 1;
            },
            ClassDeclaration(path) {
                const name = path.node.id?.name || "anonymous";
                const methods: string[] = [];

                path.node.body.body.forEach(member => {
                    if (member.type === "ClassMethod" && member.key.type === "Identifier") {
                        methods.push(member.key.name);
                        complexity += 1;
                    }
                });

                classes.push({
                    name,
                    methods,
                    lineStart: path.node.loc?.start.line || 0,
                    lineEnd: path.node.loc?.end.line || 0
                });
            },
            IfStatement() {
                complexity += 1;
            },
            ForStatement() {
                complexity += 1;
            },
            WhileStatement() {
                complexity += 1;
            },
            SwitchCase() {
                complexity += 1;
            }
        });

        return {
            path: filePath,
            relativePath,
            content,
            imports,
            exports,
            functions,
            classes,
            complexity
        };
    }

    private async buildDependencyGraph(files: FileContext[]): Promise<DependencyGraph> {
        const nodes = new Map<string, DependencyNode>();
        const edges = new Map<string, string[]>();

        for (const file of files) {
            // Add file as node
            nodes.set(file.path, {
                path: file.path,
                type: "internal"
            });

            // Add dependencies as edges
            const deps: string[] = [];
            for (const imp of file.imports) {
                const depType = this.classifyImport(imp);
                const resolvedPath = this.resolveImport(imp, file.path);

                nodes.set(resolvedPath, {
                    path: resolvedPath,
                    type: depType
                });

                deps.push(resolvedPath);
            }

            edges.set(file.path, deps);
        }

        return { nodes, edges };
    }

    private classifyImport(importPath: string): "internal" | "external" | "builtin" {
        if (importPath.startsWith(".") || importPath.startsWith("/")) {
            return "internal";
        }
        if (importPath.startsWith("node:") || ["fs", "path", "http", "https", "crypto"].includes(importPath)) {
            return "builtin";
        }
        return "external";
    }

    private resolveImport(importPath: string, fromFile: string): string {
        if (this.classifyImport(importPath) === "internal") {
            const dir = path.dirname(fromFile);
            return path.resolve(dir, importPath);
        }
        return importPath;
    }

    private async findTestFiles(sourceFiles: string[]): Promise<string[]> {
        const testFiles: string[] = [];

        for (const file of sourceFiles) {
            const dir = path.dirname(file);
            const basename = path.basename(file, path.extname(file));

            // Common test file patterns
            const patterns = [
                path.join(dir, `${basename}.test.ts`),
                path.join(dir, `${basename}.spec.ts`),
                path.join(dir, "__tests__", `${basename}.test.ts`),
                path.join(dir, "..", "tests", `${basename}.test.ts`)
            ];

            for (const testPath of patterns) {
                if (await this.fileExists(testPath)) {
                    testFiles.push(testPath);
                    break;
                }
            }
        }

        return testFiles;
    }

    private truncateToTokenBudget(
        files: FileContext[],
        maxTokens: number
    ): { files: FileContext[]; totalTokens: number } {
        // Sort by complexity (more complex = more important)
        const sorted = [...files].sort((a, b) => b.complexity - a.complexity);

        const result: FileContext[] = [];
        let totalTokens = 0;

        for (const file of sorted) {
            const fileTokens = llmClient.countTokens(file.content);

            if (totalTokens + fileTokens <= maxTokens) {
                result.push(file);
                totalTokens += fileTokens;
            } else {
                // Try to include truncated version
                const remainingBudget = maxTokens - totalTokens;
                if (remainingBudget > 500) {
                    const truncatedContent = this.truncateContent(file.content, remainingBudget);
                    result.push({
                        ...file,
                        content: truncatedContent + "\n\n// ... (truncated)"
                    });
                    totalTokens = maxTokens;
                }
                break;
            }
        }

        return { files: result, totalTokens };
    }

    private truncateContent(content: string, maxTokens: number): string {
        const lines = content.split("\n");
        let truncated = "";
        let tokens = 0;

        for (const line of lines) {
            const lineTokens = llmClient.countTokens(line);
            if (tokens + lineTokens > maxTokens) {
                break;
            }
            truncated += line + "\n";
            tokens += lineTokens;
        }

        return truncated;
    }

    private resolveModulePath(moduleId: string): string {
        // Handle various module ID formats
        if (path.isAbsolute(moduleId)) {
            return moduleId;
        }

        // Assume moduleId is relative to src directory
        const withExtensions = [
            `${moduleId}.ts`,
            `${moduleId}.js`,
            `${moduleId}/index.ts`,
            `${moduleId}/index.js`
        ];

        for (const variant of withExtensions) {
            const fullPath = path.join(this.basePath, "src", variant);
            return fullPath;
        }

        return path.join(this.basePath, "src", moduleId);
    }

    private async fileExists(filePath: string): Promise<boolean> {
        try {
            await fs.access(filePath);
            return true;
        } catch {
            return false;
        }
    }

    /**
     * Generate a formatted context string for LLM consumption
     */
    formatForLLM(context: CodeContext): string {
        let formatted = "# Code Context\n\n";

        formatted += `Files: ${context.files.length}\n`;
        formatted += `Total Tokens: ${context.totalTokens}\n\n`;

        for (const file of context.files) {
            formatted += `## ${file.relativePath}\n\n`;

            if (file.functions.length > 0) {
                formatted += "**Functions:**\n";
                file.functions.forEach(f => {
                    formatted += `- ${f.name}(${f.params.join(", ")}) [lines ${f.lineStart}-${f.lineEnd}]\n`;
                });
                formatted += "\n";
            }

            if (file.classes.length > 0) {
                formatted += "**Classes:**\n";
                file.classes.forEach(c => {
                    formatted += `- ${c.name}: ${c.methods.join(", ")} [lines ${c.lineStart}-${c.lineEnd}]\n`;
                });
                formatted += "\n";
            }

            formatted += "```typescript\n";
            formatted += file.content;
            formatted += "\n```\n\n";
        }

        return formatted;
    }
}
