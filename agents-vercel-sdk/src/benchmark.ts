#!/usr/bin/env node
/**
 * Diagram Agent Benchmark
 *
 * Performance comparison between Vercel AI SDK and Google ADK implementations.
 */

import { DiagramOrchestrator, quickDiagram } from "./orchestrator.js";
import { validateDiagram } from "./tools.js";

interface BenchmarkResult {
  name: string;
  description: string;
  format: string;
  success: boolean;
  durationMs: number;
  codeLength: number;
  valid: boolean;
  errors: string[];
  iterations: number;
}

const TEST_CASES = [
  {
    name: "Simple Pipeline",
    description: "A data pipeline: Input -> Validate -> Process -> Output",
    format: "graphviz",
  },
  {
    name: "Microservices",
    description:
      "Microservices: API Gateway connects to User Service, Order Service, Payment Service. All connect to PostgreSQL.",
    format: "graphviz",
  },
  {
    name: "Login Flow",
    description:
      "User login: Start -> Enter credentials -> Validate -> If valid go to Dashboard else Error -> End",
    format: "mermaid",
  },
  {
    name: "Web Architecture",
    description:
      "Web app: Browser -> Load Balancer -> 3 Web Servers -> Redis Cache -> PostgreSQL -> Backup",
    format: "graphviz",
  },
  {
    name: "CI/CD Pipeline",
    description:
      "CI/CD: Code Push -> Build -> Test -> Deploy to Staging -> E2E Tests -> Deploy to Production",
    format: "graphviz",
  },
];

async function runQuickBenchmark(): Promise<BenchmarkResult[]> {
  console.log("\n=== Quick Mode Benchmark ===\n");
  const results: BenchmarkResult[] = [];

  for (const testCase of TEST_CASES) {
    console.log(`Testing: ${testCase.name}...`);
    const startTime = Date.now();

    try {
      const code = await quickDiagram(testCase.description, testCase.format);
      const durationMs = Date.now() - startTime;
      const validation = validateDiagram(code, testCase.format);

      results.push({
        name: testCase.name,
        description: testCase.description,
        format: testCase.format,
        success: validation.valid,
        durationMs,
        codeLength: code.length,
        valid: validation.valid,
        errors: validation.errors,
        iterations: 0,
      });

      console.log(
        `  ${validation.valid ? "✓" : "✗"} ${durationMs}ms, ${code.length} chars`
      );
    } catch (e) {
      const error = e instanceof Error ? e.message : String(e);
      results.push({
        name: testCase.name,
        description: testCase.description,
        format: testCase.format,
        success: false,
        durationMs: Date.now() - startTime,
        codeLength: 0,
        valid: false,
        errors: [error],
        iterations: 0,
      });
      console.log(`  ✗ Error: ${error}`);
    }
  }

  return results;
}

async function runFullBenchmark(): Promise<BenchmarkResult[]> {
  console.log("\n=== Full Pipeline Benchmark ===\n");
  const results: BenchmarkResult[] = [];

  for (const testCase of TEST_CASES) {
    console.log(`Testing: ${testCase.name}...`);

    const orchestrator = new DiagramOrchestrator({
      preferredFormat: testCase.format,
      skipAnalysis: true,
      maxImprovementIterations: 3,
    });

    const startTime = Date.now();

    try {
      const result = await orchestrator.run(testCase.description);
      const durationMs = Date.now() - startTime;

      results.push({
        name: testCase.name,
        description: testCase.description,
        format: testCase.format,
        success: result.success,
        durationMs,
        codeLength: result.diagramCode?.length || 0,
        valid: result.validationResult?.valid || false,
        errors: result.errors,
        iterations: result.iterations,
      });

      console.log(
        `  ${result.success ? "✓" : "✗"} ${durationMs}ms, ${result.iterations} iterations`
      );
    } catch (e) {
      const error = e instanceof Error ? e.message : String(e);
      results.push({
        name: testCase.name,
        description: testCase.description,
        format: testCase.format,
        success: false,
        durationMs: Date.now() - startTime,
        codeLength: 0,
        valid: false,
        errors: [error],
        iterations: 0,
      });
      console.log(`  ✗ Error: ${error}`);
    }
  }

  return results;
}

async function printSummary(
  quickResults: BenchmarkResult[],
  fullResults: BenchmarkResult[]
) {
  console.log("\n" + "=".repeat(60));
  console.log("BENCHMARK SUMMARY - Vercel AI SDK");
  console.log("=".repeat(60));

  // Quick mode stats
  const quickSuccess = quickResults.filter((r) => r.success).length;
  const quickAvgTime =
    quickResults.reduce((sum, r) => sum + r.durationMs, 0) / quickResults.length;

  console.log("\n[Quick Mode]");
  console.log(`  Success Rate: ${quickSuccess}/${quickResults.length}`);
  console.log(`  Avg Duration: ${quickAvgTime.toFixed(0)}ms`);

  // Full pipeline stats
  const fullSuccess = fullResults.filter((r) => r.success).length;
  const fullAvgTime =
    fullResults.reduce((sum, r) => sum + r.durationMs, 0) / fullResults.length;
  const avgIterations =
    fullResults.reduce((sum, r) => sum + r.iterations, 0) / fullResults.length;

  console.log("\n[Full Pipeline]");
  console.log(`  Success Rate: ${fullSuccess}/${fullResults.length}`);
  console.log(`  Avg Duration: ${fullAvgTime.toFixed(0)}ms`);
  console.log(`  Avg Iterations: ${avgIterations.toFixed(1)}`);

  // Detailed results table
  console.log("\n[Detailed Results]");
  console.log("-".repeat(60));
  console.log(
    "| Test Case          | Quick    | Full     | Iterations |"
  );
  console.log("-".repeat(60));

  for (let i = 0; i < TEST_CASES.length; i++) {
    const name = TEST_CASES[i].name.padEnd(18);
    const quick = quickResults[i];
    const full = fullResults[i];

    const quickStatus = quick.success
      ? `${quick.durationMs}ms`.padEnd(8)
      : "FAIL".padEnd(8);
    const fullStatus = full.success
      ? `${full.durationMs}ms`.padEnd(8)
      : "FAIL".padEnd(8);
    const iterations = full.iterations.toString().padEnd(10);

    console.log(`| ${name} | ${quickStatus} | ${fullStatus} | ${iterations} |`);
  }

  console.log("-".repeat(60));

  // Export results as JSON
  const exportData = {
    timestamp: new Date().toISOString(),
    sdk: "Vercel AI SDK",
    quickMode: {
      successRate: quickSuccess / quickResults.length,
      avgDurationMs: quickAvgTime,
      results: quickResults,
    },
    fullPipeline: {
      successRate: fullSuccess / fullResults.length,
      avgDurationMs: fullAvgTime,
      avgIterations,
      results: fullResults,
    },
  };

  // Save to file
  const fs = await import("fs/promises");
  await fs.writeFile(
    "benchmark_vercel_sdk.json",
    JSON.stringify(exportData, null, 2)
  );
  console.log("\nResults saved to: benchmark_vercel_sdk.json");
}

async function main() {
  console.log("=".repeat(60));
  console.log("DIAGRAM AGENT BENCHMARK");
  console.log("Vercel AI SDK Implementation");
  console.log("=".repeat(60));

  const quickResults = await runQuickBenchmark();
  const fullResults = await runFullBenchmark();

  await printSummary(quickResults, fullResults);
}

main().catch(console.error);
