/**
 * Diagram Agent Orchestrator
 *
 * Coordinates the multi-agent pipeline for diagram generation.
 * Supports: Analysis → Generation → Validation → Improvement (if needed) → Rendering
 */

import * as fs from "fs/promises";
import * as path from "path";
import {
  AgentRegistry,
  AnalyzerAgent,
  GeneratorAgent,
  ImproverAgent,
  getOllamaModel,
  quickGenerate,
} from "./agents.js";
import {
  validateDiagram,
  renderDiagram,
  extractCodeFromResponse,
  DiagramFormat,
  ValidationResult,
  RenderResult,
} from "./tools.js";

// ============== Types ==============

export interface PipelineResult {
  success: boolean;
  diagramCode: string | null;
  format: DiagramFormat | null;
  outputPath: string | null;
  validationResult: ValidationResult | null;
  analysis: string | null;
  iterations: number;
  errors: string[];
  durationSeconds: number;
  tokenUsage?: {
    prompt: number;
    completion: number;
    total: number;
  };
}

export interface OrchestratorOptions {
  modelName?: string;
  outputDir?: string;
  maxImprovementIterations?: number;
  skipAnalysis?: boolean;
  preferredFormat?: string;
}

// ============== Orchestrator ==============

export class DiagramOrchestrator {
  private modelName: string;
  private outputDir: string;
  private maxIterations: number;
  private skipAnalysis: boolean;
  private preferredFormat: string;
  private registry: AgentRegistry;

  constructor(options: OrchestratorOptions = {}) {
    this.modelName = options.modelName || "gemma3:4b";
    this.outputDir = options.outputDir || "./diagram_output";
    this.maxIterations = options.maxImprovementIterations || 3;
    this.skipAnalysis = options.skipAnalysis || false;
    this.preferredFormat = options.preferredFormat || "graphviz";
    this.registry = new AgentRegistry(this.modelName);
  }

  private async ensureOutputDir(): Promise<void> {
    await fs.mkdir(this.outputDir, { recursive: true });
  }

  async analyze(description: string): Promise<string> {
    if (this.skipAnalysis) {
      return `FORMAT: ${this.preferredFormat}\nSkipped detailed analysis.`;
    }

    const analyzer = this.registry.get("analyzer") as AnalyzerAgent;
    const result = await analyzer.analyze(description);
    return result.text;
  }

  async generate(
    description: string,
    formatType?: string,
    analysis?: string
  ): Promise<string> {
    const format = formatType || this.preferredFormat;
    const generator = this.registry.get("generator") as GeneratorAgent;
    const result = await generator.generate(description, format, analysis);

    const code = extractCodeFromResponse(result.text, format);
    return code || result.text;
  }

  validate(code: string): ValidationResult {
    return validateDiagram(code);
  }

  async improve(
    code: string,
    errors: string[],
    suggestions: string[]
  ): Promise<string> {
    const improver = this.registry.get("improver") as ImproverAgent;
    const result = await improver.improve(code, errors, suggestions);

    const fixed = extractCodeFromResponse(result.text);
    return fixed || result.text;
  }

  async render(code: string, filename?: string): Promise<RenderResult> {
    await this.ensureOutputDir();

    if (!filename) {
      const timestamp = new Date().toISOString().replace(/[:.]/g, "").slice(0, 15);
      filename = `diagram_${timestamp}.png`;
    }

    const outputPath = path.join(this.outputDir, filename);
    return renderDiagram(code, outputPath);
  }

  async run(
    description: string,
    outputFilename?: string
  ): Promise<PipelineResult> {
    const startTime = Date.now();
    const errors: string[] = [];
    let iterations = 0;
    let totalTokens = { prompt: 0, completion: 0, total: 0 };

    // Step 1: Analyze
    console.log("[1/4] Analyzing description...");
    let analysis: string | null = null;
    try {
      analysis = await this.analyze(description);
      console.log("      Analysis complete");
    } catch (e) {
      const error = e instanceof Error ? e.message : String(e);
      errors.push(`Analysis failed: ${error}`);
      console.log(`      Analysis skipped: ${error}`);
    }

    // Determine format from analysis
    let formatType = this.preferredFormat;
    if (analysis && analysis.includes("FORMAT:")) {
      for (const fmt of ["graphviz", "mermaid", "plantuml"]) {
        if (analysis.toLowerCase().includes(fmt)) {
          formatType = fmt;
          break;
        }
      }
    }

    // Step 2: Generate
    console.log(`[2/4] Generating ${formatType} diagram...`);
    let code: string;
    try {
      code = await this.generate(description, formatType, analysis || undefined);
      console.log(`      Generated ${code.length} chars of code`);
    } catch (e) {
      const error = e instanceof Error ? e.message : String(e);
      return {
        success: false,
        diagramCode: null,
        format: null,
        outputPath: null,
        validationResult: null,
        analysis,
        iterations: 0,
        errors: [`Generation failed: ${error}`],
        durationSeconds: (Date.now() - startTime) / 1000,
      };
    }

    // Step 3 & 4: Validate and Improve loop
    console.log("[3/4] Validating...");
    let validation = this.validate(code);

    while (!validation.valid && iterations < this.maxIterations) {
      iterations++;
      console.log(
        `      Invalid! Improving (attempt ${iterations}/${this.maxIterations})...`
      );

      code = await this.improve(code, validation.errors, validation.suggestions);
      validation = this.validate(code);

      if (validation.valid) {
        console.log(`      Fixed after ${iterations} iteration(s)`);
      } else {
        console.log(`      Still invalid: ${validation.errors[0]?.slice(0, 50)}...`);
      }
    }

    if (!validation.valid) {
      errors.push(...validation.errors);
      console.log(`      Could not fix after ${this.maxIterations} attempts`);
    }

    // Step 5: Render
    let outputPath: string | null = null;
    if (validation.valid) {
      console.log("[4/4] Rendering to PNG...");
      const renderResult = await this.render(code, outputFilename);

      if (renderResult.success) {
        outputPath = renderResult.outputPath;
        console.log(`      Saved: ${outputPath}`);
      } else {
        errors.push(`Render failed: ${renderResult.error}`);
        console.log(`      Render failed: ${renderResult.error}`);
      }
    } else {
      console.log("[4/4] Skipping render (invalid code)");
    }

    const duration = (Date.now() - startTime) / 1000;

    return {
      success: validation.valid && outputPath !== null,
      diagramCode: code,
      format: validation.format,
      outputPath,
      validationResult: validation,
      analysis,
      iterations,
      errors,
      durationSeconds: duration,
      tokenUsage: totalTokens,
    };
  }
}

// ============== Convenience Functions ==============

export async function createDiagram(
  description: string,
  options: {
    model?: string;
    format?: string;
    outputDir?: string;
    outputFilename?: string;
  } = {}
): Promise<PipelineResult> {
  const orchestrator = new DiagramOrchestrator({
    modelName: options.model,
    outputDir: options.outputDir,
    preferredFormat: options.format,
    skipAnalysis: true,
  });

  return orchestrator.run(description, options.outputFilename);
}

export async function quickDiagram(
  description: string,
  formatType: string = "graphviz"
): Promise<string> {
  return quickGenerate(description, formatType);
}
