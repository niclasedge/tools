/**
 * Diagram Agent Definitions
 *
 * Multi-agent system for diagram generation using Vercel AI SDK.
 * Each agent has a specific role in the pipeline.
 */

import { generateText, streamText, tool, LanguageModel } from "ai";
import { createOllama } from "ollama-ai-provider";
import { z } from "zod";
import {
  validateDiagramTool,
  renderDiagramTool,
  extractCodeTool,
  validateDiagram,
  extractCodeFromResponse,
} from "./tools.js";

// ============== Model Configuration ==============

export function getOllamaModel(modelName: string = "gemma3:4b"): LanguageModel {
  const ollama = createOllama({
    baseURL: process.env.OLLAMA_BASE_URL || "http://localhost:11434/api",
  });
  return ollama(modelName);
}

// ============== Agent Prompts ==============

export const ANALYZER_INSTRUCTION = `You are a Diagram Analyzer Agent. Your job is to analyze text descriptions and determine:

1. What type of diagram would best represent the information (flowchart, architecture, sequence, etc.)
2. What format to use (graphviz for complex flows, mermaid for simple diagrams)
3. Key elements and relationships to include

When analyzing, output a structured analysis:
- DIAGRAM_TYPE: [flowchart/architecture/sequence/mindmap/etc]
- FORMAT: [graphviz/mermaid/plantuml]
- ELEMENTS: List of nodes/components
- RELATIONSHIPS: List of connections between elements
- STYLE_NOTES: Any styling recommendations

Be concise and structured in your analysis.`;

export const GENERATOR_INSTRUCTION = `You are a Diagram Generator Agent. You create valid diagram code from descriptions.

CRITICAL RULES FOR GRAPHVIZ:
1. Start with: digraph DiagramName {
2. Node names MUST be alphanumeric with underscores only (no dots, no special chars)
3. Use: env_file NOT .env, config_yaml NOT config.yaml
4. Labels can have special chars in quotes: [label="config.yaml"]
5. End with a closing }

CRITICAL RULES FOR MERMAID:
1. Start with: flowchart LR or flowchart TD
2. Use subgraph Name ... end for grouping
3. Node syntax: ID["Label"] or ID[("Cylinder")]
4. Every subgraph needs a closing 'end'

OUTPUT FORMAT:
Return ONLY the diagram code, no explanations. Start directly with the code.
For graphviz: Start with 'digraph'
For mermaid: Start with 'flowchart'

Use appropriate shapes:
- cylinder for databases
- folder for file outputs
- diamond for decisions
- box for processes
- ellipse for start/end`;

export const VALIDATOR_INSTRUCTION = `You are a Diagram Validator Agent. Your job is to check diagram code for errors.

Use the validate_diagram tool to check the code syntax.

After validation:
1. If VALID: Report success and the format detected
2. If INVALID: List all errors and suggest specific fixes

Be precise about what line or element has the error.`;

export const IMPROVER_INSTRUCTION = `You are a Diagram Improver Agent. Your job is to fix invalid diagram code.

When given invalid code with errors:
1. Analyze each error carefully
2. Apply the specific fix needed
3. Return the COMPLETE fixed code

COMMON FIXES:
- Node names with dots (.env) → Use underscores (env_file)
- Missing closing braces → Add }
- Port syntax errors → Remove or fix port references
- Unbalanced subgraph/end → Add missing 'end' statements

OUTPUT: Return ONLY the fixed code, no explanations.`;

// ============== Agent Classes ==============

export interface AgentResult {
  text: string;
  usage?: {
    promptTokens: number;
    completionTokens: number;
    totalTokens: number;
  };
  finishReason?: string;
}

export class BaseAgent {
  protected model: LanguageModel;
  protected instruction: string;
  protected name: string;
  protected tools: Record<string, ReturnType<typeof tool>>;

  constructor(
    name: string,
    instruction: string,
    model?: LanguageModel,
    tools: Record<string, ReturnType<typeof tool>> = {}
  ) {
    this.name = name;
    this.instruction = instruction;
    this.model = model || getOllamaModel();
    this.tools = tools;
  }

  async run(prompt: string): Promise<AgentResult> {
    const result = await generateText({
      model: this.model,
      system: this.instruction,
      prompt,
      tools: this.tools,
      maxSteps: 5,
      temperature: 0.3,
    });

    return {
      text: result.text,
      usage: result.usage,
      finishReason: result.finishReason,
    };
  }

  async *stream(prompt: string): AsyncGenerator<string> {
    const result = streamText({
      model: this.model,
      system: this.instruction,
      prompt,
      temperature: 0.3,
    });

    for await (const chunk of result.textStream) {
      yield chunk;
    }
  }
}

export class AnalyzerAgent extends BaseAgent {
  constructor(model?: LanguageModel) {
    super("analyzer", ANALYZER_INSTRUCTION, model);
  }

  async analyze(description: string): Promise<AgentResult> {
    const prompt = `Analyze this diagram request and provide a structured analysis:

${description}

Output your analysis in the structured format specified in your instructions.`;

    return this.run(prompt);
  }
}

export class GeneratorAgent extends BaseAgent {
  constructor(model?: LanguageModel) {
    super("generator", GENERATOR_INSTRUCTION, model);
  }

  async generate(
    description: string,
    formatType: string = "graphviz",
    analysis?: string
  ): Promise<AgentResult> {
    const prompt = `Generate a ${formatType.toUpperCase()} diagram for:

${description}

${analysis ? `Analysis context: ${analysis}` : ""}

Remember: Output ONLY the diagram code, starting with 'digraph' for graphviz or 'flowchart' for mermaid.
NO explanations, NO markdown code blocks, just the raw code.`;

    return this.run(prompt);
  }
}

export class ValidatorAgent extends BaseAgent {
  constructor(model?: LanguageModel) {
    super("validator", VALIDATOR_INSTRUCTION, model, {
      validate_diagram: validateDiagramTool,
    });
  }

  async validate(code: string): Promise<AgentResult> {
    const prompt = `Validate this diagram code:

\`\`\`
${code}
\`\`\`

Use the validate_diagram tool to check the syntax.`;

    return this.run(prompt);
  }
}

export class ImproverAgent extends BaseAgent {
  constructor(model?: LanguageModel) {
    super("improver", IMPROVER_INSTRUCTION, model);
  }

  async improve(
    code: string,
    errors: string[],
    suggestions: string[]
  ): Promise<AgentResult> {
    const prompt = `Fix this invalid diagram code:

\`\`\`
${code}
\`\`\`

ERRORS:
${errors.map((e) => `- ${e}`).join("\n")}

SUGGESTIONS:
${suggestions.map((s) => `- ${s}`).join("\n")}

Return ONLY the fixed code, no explanations.`;

    return this.run(prompt);
  }
}

export class RendererAgent extends BaseAgent {
  constructor(model?: LanguageModel) {
    super(
      "renderer",
      "You render diagrams to PNG files. Use the render_diagram tool.",
      model,
      {
        render_diagram: renderDiagramTool,
      }
    );
  }

  async render(code: string, outputPath: string): Promise<AgentResult> {
    const prompt = `Render this diagram code to: ${outputPath}

\`\`\`
${code}
\`\`\``;

    return this.run(prompt);
  }
}

// ============== Agent Registry ==============

export type AgentFactory = (model?: LanguageModel) => BaseAgent;

export class AgentRegistry {
  private agents: Map<string, AgentFactory> = new Map();
  private model: LanguageModel;

  constructor(modelName: string = "gemma3:4b") {
    this.model = getOllamaModel(modelName);
    this.registerBuiltinAgents();
  }

  private registerBuiltinAgents() {
    this.register("analyzer", (m) => new AnalyzerAgent(m));
    this.register("generator", (m) => new GeneratorAgent(m));
    this.register("validator", (m) => new ValidatorAgent(m));
    this.register("improver", (m) => new ImproverAgent(m));
    this.register("renderer", (m) => new RendererAgent(m));
  }

  register(name: string, factory: AgentFactory) {
    this.agents.set(name, factory);
  }

  get(name: string): BaseAgent {
    const factory = this.agents.get(name);
    if (!factory) {
      throw new Error(
        `Unknown agent: ${name}. Available: ${Array.from(this.agents.keys()).join(", ")}`
      );
    }
    return factory(this.model);
  }

  list(): string[] {
    return Array.from(this.agents.keys());
  }

  createCustomAgent(
    name: string,
    instruction: string,
    tools: Record<string, ReturnType<typeof tool>> = {}
  ): BaseAgent {
    const agent = new BaseAgent(name, instruction, this.model, tools);
    this.register(name, () => agent);
    return agent;
  }
}

// ============== Convenience Functions ==============

export async function quickGenerate(
  description: string,
  formatType: string = "graphviz",
  modelName: string = "gemma3:4b"
): Promise<string> {
  const model = getOllamaModel(modelName);

  const prompt = `Generate valid ${formatType.toUpperCase()} diagram code for:

${description}

RULES:
- For graphviz: Start with 'digraph Name {', use alphanumeric node names only
- For mermaid: Start with 'flowchart LR' or 'flowchart TD'
- Output ONLY the code, no explanations

CODE:`;

  const result = await generateText({
    model,
    prompt,
    temperature: 0.3,
  });

  const extracted = extractCodeFromResponse(result.text, formatType);
  return extracted || result.text;
}
