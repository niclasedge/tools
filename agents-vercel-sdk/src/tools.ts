/**
 * Diagram Agent Tools
 *
 * Reusable tools for diagram validation, rendering, and file operations.
 * TypeScript implementation using Vercel AI SDK patterns.
 */

import { tool } from "ai";
import { z } from "zod";
import { exec } from "child_process";
import { promisify } from "util";
import * as fs from "fs/promises";
import * as path from "path";
import * as os from "os";

const execAsync = promisify(exec);

// ============== Types ==============

export enum DiagramFormat {
  GRAPHVIZ = "graphviz",
  PLANTUML = "plantuml",
  MERMAID = "mermaid",
}

export interface ValidationResult {
  valid: boolean;
  format: DiagramFormat;
  errors: string[];
  code: string;
  suggestions: string[];
}

export interface RenderResult {
  success: boolean;
  outputPath: string | null;
  error: string | null;
  format: DiagramFormat;
}

// ============== Validation Functions ==============

export function validateGraphviz(code: string): ValidationResult {
  const errors: string[] = [];
  const suggestions: string[] = [];

  // Basic syntax checks
  if (!/(di)?graph\s+\w+\s*\{/i.test(code)) {
    errors.push(
      "No valid graph definition found (digraph Name { or graph Name {)"
    );
    suggestions.push("Start with: digraph MyDiagram {");
  }

  // Check brace balance
  const openBraces = (code.match(/\{/g) || []).length;
  const closeBraces = (code.match(/\}/g) || []).length;
  if (openBraces !== closeBraces) {
    errors.push(`Unbalanced braces: ${openBraces} '{' vs ${closeBraces} '}'`);
    suggestions.push("Ensure every '{' has a matching '}'");
  }

  // Check for common LLM mistakes
  if (/\.\w+\s*\[/.test(code)) {
    errors.push("Node names cannot start with dots (e.g., .env is invalid)");
    suggestions.push("Use underscores: env_file instead of .env");
  }

  if (/:\w+\s*->/.test(code)) {
    errors.push("Port syntax (:port) in node names may cause issues");
    suggestions.push("Define ports separately using record shapes");
  }

  return {
    valid: errors.length === 0,
    format: DiagramFormat.GRAPHVIZ,
    errors,
    code,
    suggestions,
  };
}

export function validateMermaid(code: string): ValidationResult {
  const errors: string[] = [];
  const suggestions: string[] = [];

  const codeStripped = code.trim().toLowerCase();

  // Check for valid start
  const validStarts = [
    "flowchart",
    "graph",
    "sequencediagram",
    "classdiagram",
    "erdiagram",
    "gantt",
    "pie",
    "statediagram",
  ];

  const hasValidStart = validStarts.some((s) => codeStripped.startsWith(s));
  if (!hasValidStart) {
    errors.push(
      "Must start with a valid diagram type (flowchart, graph, etc.)"
    );
    suggestions.push("Start with: flowchart LR or graph TD");
  }

  // Check bracket balance
  const openSquare = (code.match(/\[/g) || []).length;
  const closeSquare = (code.match(/\]/g) || []).length;
  if (openSquare !== closeSquare) {
    errors.push(
      `Unbalanced square brackets: ${openSquare} '[' vs ${closeSquare} ']'`
    );
    suggestions.push("Ensure every '[' has a matching ']'");
  }

  // Check subgraph/end balance
  const subgraphCount = (code.match(/\bsubgraph\b/gi) || []).length;
  const endCount = (code.match(/\bend\b/gi) || []).length;
  if (subgraphCount !== endCount) {
    errors.push(
      `Unbalanced subgraph/end: ${subgraphCount} subgraph vs ${endCount} end`
    );
    suggestions.push("Every 'subgraph' needs a closing 'end'");
  }

  return {
    valid: errors.length === 0,
    format: DiagramFormat.MERMAID,
    errors,
    code,
    suggestions,
  };
}

export function validatePlantuml(code: string): ValidationResult {
  const errors: string[] = [];
  const suggestions: string[] = [];

  const codeLower = code.toLowerCase();

  if (!codeLower.includes("@startuml")) {
    errors.push("Missing @startuml at the beginning");
    suggestions.push("Start with: @startuml");
  }

  if (!codeLower.includes("@enduml")) {
    errors.push("Missing @enduml at the end");
    suggestions.push("End with: @enduml");
  }

  if (codeLower.includes("@startuml") && codeLower.includes("@enduml")) {
    const startPos = codeLower.indexOf("@startuml");
    const endPos = codeLower.indexOf("@enduml");
    if (startPos > endPos) {
      errors.push("@startuml must come before @enduml");
    }
  }

  return {
    valid: errors.length === 0,
    format: DiagramFormat.PLANTUML,
    errors,
    code,
    suggestions,
  };
}

export function validateDiagram(
  code: string,
  formatHint?: string
): ValidationResult {
  code = code.trim();

  // Auto-detect format
  let detectedFormat: string;
  if (formatHint) {
    detectedFormat = formatHint.toLowerCase();
  } else if (code.toLowerCase().includes("@startuml")) {
    detectedFormat = "plantuml";
  } else if (
    code.toLowerCase().startsWith("flowchart") ||
    code.toLowerCase().startsWith("graph ")
  ) {
    detectedFormat = "mermaid";
  } else if (/(di)?graph\s+\w+\s*\{/i.test(code)) {
    detectedFormat = "graphviz";
  } else {
    detectedFormat = "graphviz";
  }

  const validators: Record<string, (code: string) => ValidationResult> = {
    graphviz: validateGraphviz,
    plantuml: validatePlantuml,
    mermaid: validateMermaid,
  };

  return validators[detectedFormat]?.(code) || validateGraphviz(code);
}

// ============== Rendering Functions ==============

export async function renderGraphviz(
  code: string,
  outputPath: string
): Promise<RenderResult> {
  try {
    const tmpFile = path.join(os.tmpdir(), `diagram_${Date.now()}.dot`);
    await fs.writeFile(tmpFile, code);

    await execAsync(`dot -Tpng -Gdpi=150 "${tmpFile}" -o "${outputPath}"`);
    await fs.unlink(tmpFile);

    return {
      success: true,
      outputPath,
      error: null,
      format: DiagramFormat.GRAPHVIZ,
    };
  } catch (error) {
    return {
      success: false,
      outputPath: null,
      error: error instanceof Error ? error.message : String(error),
      format: DiagramFormat.GRAPHVIZ,
    };
  }
}

export async function renderMermaid(
  code: string,
  outputPath: string
): Promise<RenderResult> {
  try {
    const encoded = Buffer.from(code).toString("base64url");
    const url = `https://mermaid.ink/img/${encoded}?type=png&bgColor=white`;

    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const buffer = await response.arrayBuffer();
    await fs.writeFile(outputPath, Buffer.from(buffer));

    return {
      success: true,
      outputPath,
      error: null,
      format: DiagramFormat.MERMAID,
    };
  } catch (error) {
    return {
      success: false,
      outputPath: null,
      error: error instanceof Error ? error.message : String(error),
      format: DiagramFormat.MERMAID,
    };
  }
}

export async function renderPlantuml(
  code: string,
  outputPath: string
): Promise<RenderResult> {
  try {
    // PlantUML encoding
    const deflate = await import("zlib");
    const compressed = deflate.deflateSync(code);
    const encoded = encodePlantUML(compressed.subarray(2, -4));
    const url = `https://www.plantuml.com/plantuml/png/${encoded}`;

    const response = await fetch(url, {
      headers: { "User-Agent": "Mozilla/5.0" },
    });
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const buffer = await response.arrayBuffer();
    await fs.writeFile(outputPath, Buffer.from(buffer));

    return {
      success: true,
      outputPath,
      error: null,
      format: DiagramFormat.PLANTUML,
    };
  } catch (error) {
    return {
      success: false,
      outputPath: null,
      error: error instanceof Error ? error.message : String(error),
      format: DiagramFormat.PLANTUML,
    };
  }
}

function encodePlantUML(data: Buffer): string {
  const encode6bit = (b: number): string => {
    if (b < 10) return String.fromCharCode(48 + b);
    b -= 10;
    if (b < 26) return String.fromCharCode(65 + b);
    b -= 26;
    if (b < 26) return String.fromCharCode(97 + b);
    b -= 26;
    return b === 0 ? "-" : b === 1 ? "_" : "?";
  };

  let result = "";
  for (let i = 0; i < data.length; i += 3) {
    const b1 = data[i] || 0;
    const b2 = data[i + 1] || 0;
    const b3 = data[i + 2] || 0;
    result += encode6bit(b1 >> 2);
    result += encode6bit(((b1 & 0x3) << 4) | (b2 >> 4));
    result += encode6bit(((b2 & 0xf) << 2) | (b3 >> 6));
    result += encode6bit(b3 & 0x3f);
  }
  return result;
}

export async function renderDiagram(
  code: string,
  outputPath: string,
  formatType?: DiagramFormat
): Promise<RenderResult> {
  if (!formatType) {
    const validation = validateDiagram(code);
    formatType = validation.format;
  }

  const renderers: Record<
    DiagramFormat,
    (code: string, outputPath: string) => Promise<RenderResult>
  > = {
    [DiagramFormat.GRAPHVIZ]: renderGraphviz,
    [DiagramFormat.PLANTUML]: renderPlantuml,
    [DiagramFormat.MERMAID]: renderMermaid,
  };

  return renderers[formatType](code, outputPath);
}

// ============== Code Extraction ==============

export function extractCodeFromResponse(
  text: string,
  formatType?: string
): string | null {
  // Remove markdown code blocks
  const patterns = [
    /```(?:dot|graphviz)\s*\n([\s\S]*?)\n```/i,
    /```(?:mermaid)\s*\n([\s\S]*?)\n```/i,
    /```(?:plantuml|puml)\s*\n([\s\S]*?)\n```/i,
    /```\s*\n((di)?graph\s+\w+\s*\{[\s\S]*?\})\s*```/i,
    /```\s*\n(flowchart\s+\w+[\s\S]*?)\n```/i,
    /```\s*\n(@startuml[\s\S]*?@enduml)\s*```/i,
  ];

  for (const pattern of patterns) {
    const match = text.match(pattern);
    if (match) {
      return match[1].trim();
    }
  }

  // Fallback: look for raw diagram code
  if (formatType === "graphviz" || /(di)?graph\s+\w+\s*\{/i.test(text)) {
    const match = text.match(/((?:di)?graph\s+\w+\s*\{[\s\S]*\})/i);
    if (match) return match[1].trim();
  }

  if (
    formatType === "mermaid" ||
    text.trim().toLowerCase().startsWith("flowchart") ||
    text.trim().toLowerCase().startsWith("graph ")
  ) {
    let cleaned = text.trim();
    cleaned = cleaned.replace(/^```\w*\s*\n?/, "");
    cleaned = cleaned.replace(/\n?```\s*$/, "");
    return cleaned || null;
  }

  if (formatType === "plantuml" || text.toLowerCase().includes("@startuml")) {
    const match = text.match(/(@startuml[\s\S]*?@enduml)/i);
    if (match) return match[1].trim();
  }

  return null;
}

// ============== AI SDK Tool Definitions ==============

export const validateDiagramTool = tool({
  description:
    "Validate diagram code and check for syntax errors. Returns validation result with errors and suggestions.",
  parameters: z.object({
    code: z.string().describe("The diagram code to validate"),
    formatHint: z
      .enum(["graphviz", "mermaid", "plantuml"])
      .optional()
      .describe("Optional format hint"),
  }),
  execute: async ({ code, formatHint }) => {
    const result = validateDiagram(code, formatHint);
    return {
      valid: result.valid,
      format: result.format,
      errors: result.errors,
      suggestions: result.suggestions,
    };
  },
});

export const renderDiagramTool = tool({
  description: "Render diagram code to PNG file.",
  parameters: z.object({
    code: z.string().describe("The diagram code to render"),
    outputPath: z.string().describe("Path for output PNG file"),
    formatType: z
      .enum(["graphviz", "mermaid", "plantuml"])
      .optional()
      .describe("Diagram format"),
  }),
  execute: async ({ code, outputPath, formatType }) => {
    const fmt = formatType
      ? (DiagramFormat[
          formatType.toUpperCase() as keyof typeof DiagramFormat
        ] as DiagramFormat)
      : undefined;
    const result = await renderDiagram(code, outputPath, fmt);
    return {
      success: result.success,
      outputPath: result.outputPath,
      error: result.error,
      format: result.format,
    };
  },
});

export const extractCodeTool = tool({
  description: "Extract diagram code from LLM response text.",
  parameters: z.object({
    responseText: z.string().describe("The LLM response containing diagram code"),
    expectedFormat: z
      .enum(["graphviz", "mermaid", "plantuml"])
      .optional()
      .describe("Expected format"),
  }),
  execute: async ({ responseText, expectedFormat }) => {
    const code = extractCodeFromResponse(responseText, expectedFormat);
    return code || "ERROR: Could not extract diagram code from response";
  },
});
