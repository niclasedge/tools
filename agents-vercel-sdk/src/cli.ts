#!/usr/bin/env node
/**
 * Diagram Agent CLI
 *
 * Command-line interface for the diagram generation agent system.
 * Built with Vercel AI SDK.
 */

import { Command } from "commander";
import chalk from "chalk";
import * as fs from "fs/promises";
import * as path from "path";
import * as readline from "readline/promises";
import { stdin as input, stdout as output } from "process";

import { DiagramOrchestrator, createDiagram, quickDiagram, PipelineResult } from "./orchestrator.js";
import { validateDiagram, renderDiagram, DiagramFormat } from "./tools.js";

const program = new Command();

program
  .name("diagram-agent")
  .description("Multi-agent diagram generation with Vercel AI SDK + Ollama")
  .version("1.0.0");

// Generate command
program
  .argument("[description]", "Text description of the diagram to generate")
  .option("-f, --format <type>", "Diagram format (graphviz, mermaid, plantuml)", "graphviz")
  .option("-m, --model <name>", "Ollama model name", "gemma3:4b")
  .option("-o, --output <file>", "Output PNG filename")
  .option("-d, --output-dir <dir>", "Output directory", "./diagram_output")
  .option("-q, --quick", "Quick mode - skip analysis, single pass")
  .option("--max-iterations <n>", "Max improvement iterations", "3")
  .option("--validate <file>", "Validate an existing diagram file")
  .option("--render <file>", "Render an existing diagram file to PNG")
  .option("--code-only", "Output only the diagram code, no PNG")
  .option("--json", "Output results as JSON")
  .option("-i, --interactive", "Interactive mode")
  .action(async (description, options) => {
    if (options.validate) {
      await validateFile(options.validate, options.json);
      return;
    }

    if (options.render) {
      await renderFile(options.render, options.output, options.outputDir, options.json);
      return;
    }

    if (options.interactive) {
      await interactiveMode(options);
      return;
    }

    if (!description) {
      program.help();
      return;
    }

    await generateDiagram(description, options);
  });

async function generateDiagram(description: string, options: any) {
  if (options.quick) {
    console.log(chalk.blue(`Generating ${options.format} diagram (quick mode)...`));
    const code = await quickDiagram(description, options.format);

    if (options.codeOnly) {
      console.log(code);
      return;
    }

    const validation = validateDiagram(code, options.format);

    if (validation.valid) {
      await fs.mkdir(options.outputDir, { recursive: true });
      const timestamp = new Date().toISOString().replace(/[:.]/g, "").slice(0, 15);
      const filename = options.output || `diagram_${timestamp}.png`;
      const outputPath = path.join(options.outputDir, filename);

      const result = await renderDiagram(code, outputPath, DiagramFormat.GRAPHVIZ);

      if (result.success) {
        console.log(chalk.green(`✓ Saved: ${result.outputPath}`));
        if (options.json) {
          console.log(JSON.stringify({ success: true, path: result.outputPath, code }, null, 2));
        }
      } else {
        console.log(chalk.red(`✗ Render failed: ${result.error}`));
      }
    } else {
      console.log(chalk.red(`✗ Invalid code: ${validation.errors.join(", ")}`));
      console.log("\nGenerated code:");
      console.log(code);
    }
  } else {
    const orchestrator = new DiagramOrchestrator({
      modelName: options.model,
      outputDir: options.outputDir,
      maxImprovementIterations: parseInt(options.maxIterations),
      preferredFormat: options.format,
    });

    const result = await orchestrator.run(description, options.output);

    if (options.json) {
      console.log(JSON.stringify(result, null, 2));
    } else {
      printResult(result);
    }
  }
}

function printResult(result: PipelineResult) {
  console.log("\n" + "=".repeat(50));
  console.log("DIAGRAM GENERATION RESULT");
  console.log("=".repeat(50));

  const status = result.success
    ? chalk.green("✓ SUCCESS")
    : chalk.red("✗ FAILED");
  console.log(`\nStatus: ${status}`);

  if (result.format) {
    console.log(`Format: ${result.format}`);
  }

  console.log(`Iterations: ${result.iterations}`);
  console.log(`Duration: ${result.durationSeconds.toFixed(2)}s`);

  if (result.outputPath) {
    console.log(chalk.green(`\nOutput: ${result.outputPath}`));
  }

  if (result.errors.length > 0) {
    console.log(chalk.red("\nErrors:"));
    for (const err of result.errors) {
      console.log(chalk.red(`  - ${err}`));
    }
  }

  if (result.diagramCode) {
    console.log("\nGenerated Code:");
    console.log("-".repeat(40));
    const code = result.diagramCode.length > 1000
      ? result.diagramCode.slice(0, 1000) + "\n... (truncated)"
      : result.diagramCode;
    console.log(code);
  }

  console.log();
}

async function validateFile(filepath: string, asJson: boolean = false) {
  try {
    const code = await fs.readFile(filepath, "utf-8");
    const result = validateDiagram(code);

    if (asJson) {
      console.log(JSON.stringify({
        valid: result.valid,
        format: result.format,
        errors: result.errors,
        suggestions: result.suggestions,
      }, null, 2));
    } else {
      if (result.valid) {
        console.log(chalk.green(`✓ Valid ${result.format} code`));
      } else {
        console.log(chalk.red(`✗ Invalid ${result.format} code`));
        console.log("\nErrors:");
        for (const err of result.errors) {
          console.log(chalk.red(`  - ${err}`));
        }
        if (result.suggestions.length > 0) {
          console.log("\nSuggestions:");
          for (const sug of result.suggestions) {
            console.log(chalk.yellow(`  - ${sug}`));
          }
        }
      }
    }
  } catch (e) {
    console.log(chalk.red(`Error reading file: ${e}`));
    process.exit(1);
  }
}

async function renderFile(
  filepath: string,
  output?: string,
  outputDir: string = "./diagram_output",
  asJson: boolean = false
) {
  try {
    const code = await fs.readFile(filepath, "utf-8");
    await fs.mkdir(outputDir, { recursive: true });

    const outputFile = output
      ? path.join(outputDir, output)
      : path.join(outputDir, path.basename(filepath, path.extname(filepath)) + ".png");

    const result = await renderDiagram(code, outputFile);

    if (asJson) {
      console.log(JSON.stringify({
        success: result.success,
        outputPath: result.outputPath,
        error: result.error,
        format: result.format,
      }, null, 2));
    } else {
      if (result.success) {
        console.log(chalk.green(`✓ Rendered: ${result.outputPath}`));
      } else {
        console.log(chalk.red(`✗ Render failed: ${result.error}`));
      }
    }
  } catch (e) {
    console.log(chalk.red(`Error reading file: ${e}`));
    process.exit(1);
  }
}

async function interactiveMode(options: any) {
  console.log("\n" + "=".repeat(50));
  console.log("DIAGRAM AGENT - Interactive Mode");
  console.log("=".repeat(50));
  console.log(`\nModel: ${options.model}`);
  console.log(`Format: ${options.format}`);
  console.log("\nCommands:");
  console.log("  /format <graphviz|mermaid|plantuml> - Change format");
  console.log("  /model <name> - Change model");
  console.log("  /quick - Toggle quick mode");
  console.log("  /help - Show help");
  console.log("  /quit - Exit");
  console.log("\nOr just type a diagram description to generate.\n");

  const rl = readline.createInterface({ input, output });

  let quickMode = options.quick || false;
  let currentFormat = options.format;
  let currentModel = options.model;

  while (true) {
    try {
      const userInput = await rl.question("diagram> ");
      const trimmed = userInput.trim();

      if (!trimmed) continue;

      if (trimmed.startsWith("/")) {
        const [command, ...args] = trimmed.split(" ");

        switch (command.toLowerCase()) {
          case "/quit":
          case "/exit":
            console.log("Bye!");
            rl.close();
            return;

          case "/format":
            if (args[0] && ["graphviz", "mermaid", "plantuml"].includes(args[0])) {
              currentFormat = args[0];
              console.log(`Format set to: ${currentFormat}`);
            } else {
              console.log("Invalid format. Use: graphviz, mermaid, or plantuml");
            }
            break;

          case "/model":
            if (args[0]) {
              currentModel = args[0];
              console.log(`Model set to: ${currentModel}`);
            }
            break;

          case "/quick":
            quickMode = !quickMode;
            console.log(`Quick mode: ${quickMode ? "ON" : "OFF"}`);
            break;

          case "/help":
            console.log("\nCommands:");
            console.log("  /format <graphviz|mermaid|plantuml>");
            console.log("  /model <ollama-model-name>");
            console.log("  /quick - Toggle quick mode");
            console.log("  /quit - Exit");
            break;

          default:
            console.log(`Unknown command: ${command}`);
        }
      } else {
        console.log(chalk.blue(`\nGenerating ${currentFormat} diagram...`));

        if (quickMode) {
          const code = await quickDiagram(trimmed, currentFormat);
          const validation = validateDiagram(code, currentFormat);

          if (validation.valid) {
            console.log(chalk.green("\n✓ Valid code generated:"));
            console.log("-".repeat(40));
            console.log(code);
          } else {
            console.log(chalk.yellow("\n⚠ Code has issues:"));
            for (const err of validation.errors) {
              console.log(chalk.red(`  - ${err}`));
            }
            console.log("\nGenerated code:");
            console.log(code);
          }
        } else {
          const orchestrator = new DiagramOrchestrator({
            modelName: currentModel,
            outputDir: options.outputDir,
            preferredFormat: currentFormat,
          });
          const result = await orchestrator.run(trimmed);
          printResult(result);
        }

        console.log();
      }
    } catch (e) {
      if ((e as NodeJS.ErrnoException).code === "ERR_USE_AFTER_CLOSE") {
        break;
      }
      console.log("Bye!");
      break;
    }
  }
}

program.parse();
