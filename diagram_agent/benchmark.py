#!/usr/bin/env python3
"""
Diagram Agent Benchmark - Google ADK Implementation

Performance tests for diagram generation pipeline.
"""

import time
import json
from dataclasses import dataclass, asdict
from typing import List

from orchestrator import DiagramOrchestrator, quick_diagram
from tools import validate_diagram


@dataclass
class BenchmarkResult:
    name: str
    description: str
    format: str
    success: bool
    duration_ms: float
    code_length: int
    valid: bool
    errors: List[str]
    iterations: int


TEST_CASES = [
    {
        "name": "Simple Pipeline",
        "description": "A data pipeline: Input -> Validate -> Process -> Output",
        "format": "graphviz",
    },
    {
        "name": "Microservices",
        "description": "Microservices: API Gateway connects to User Service, Order Service, Payment Service. All connect to PostgreSQL.",
        "format": "graphviz",
    },
    {
        "name": "Login Flow",
        "description": "User login: Start -> Enter credentials -> Validate -> If valid go to Dashboard else Error -> End",
        "format": "mermaid",
    },
    {
        "name": "Web Architecture",
        "description": "Web app: Browser -> Load Balancer -> 3 Web Servers -> Redis Cache -> PostgreSQL -> Backup",
        "format": "graphviz",
    },
    {
        "name": "CI/CD Pipeline",
        "description": "CI/CD: Code Push -> Build -> Test -> Deploy to Staging -> E2E Tests -> Deploy to Production",
        "format": "graphviz",
    },
]


def run_quick_benchmark() -> List[BenchmarkResult]:
    print("\n=== Quick Mode Benchmark (Google ADK) ===\n")
    results = []

    for test_case in TEST_CASES:
        print(f"Testing: {test_case['name']}...")
        start_time = time.time()

        try:
            code = quick_diagram(test_case["description"], test_case["format"])
            duration_ms = (time.time() - start_time) * 1000
            validation = validate_diagram(code, test_case["format"])

            result = BenchmarkResult(
                name=test_case["name"],
                description=test_case["description"],
                format=test_case["format"],
                success=validation.valid,
                duration_ms=duration_ms,
                code_length=len(code),
                valid=validation.valid,
                errors=validation.errors,
                iterations=0,
            )
            results.append(result)

            status = "✓" if validation.valid else "✗"
            print(f"  {status} {duration_ms:.0f}ms, {len(code)} chars")

        except Exception as e:
            result = BenchmarkResult(
                name=test_case["name"],
                description=test_case["description"],
                format=test_case["format"],
                success=False,
                duration_ms=(time.time() - start_time) * 1000,
                code_length=0,
                valid=False,
                errors=[str(e)],
                iterations=0,
            )
            results.append(result)
            print(f"  ✗ Error: {e}")

    return results


def run_full_benchmark() -> List[BenchmarkResult]:
    print("\n=== Full Pipeline Benchmark (Google ADK) ===\n")
    results = []

    for test_case in TEST_CASES:
        print(f"Testing: {test_case['name']}...")

        orchestrator = DiagramOrchestrator(
            preferred_format=test_case["format"],
            skip_analysis=True,
            max_improvement_iterations=3,
        )

        start_time = time.time()

        try:
            pipeline_result = orchestrator.run(test_case["description"])
            duration_ms = (time.time() - start_time) * 1000

            result = BenchmarkResult(
                name=test_case["name"],
                description=test_case["description"],
                format=test_case["format"],
                success=pipeline_result.success,
                duration_ms=duration_ms,
                code_length=len(pipeline_result.diagram_code or ""),
                valid=pipeline_result.validation_result.valid if pipeline_result.validation_result else False,
                errors=pipeline_result.errors,
                iterations=pipeline_result.iterations,
            )
            results.append(result)

            status = "✓" if pipeline_result.success else "✗"
            print(f"  {status} {duration_ms:.0f}ms, {pipeline_result.iterations} iterations")

        except Exception as e:
            result = BenchmarkResult(
                name=test_case["name"],
                description=test_case["description"],
                format=test_case["format"],
                success=False,
                duration_ms=(time.time() - start_time) * 1000,
                code_length=0,
                valid=False,
                errors=[str(e)],
                iterations=0,
            )
            results.append(result)
            print(f"  ✗ Error: {e}")

    return results


def main():
    print("=" * 60)
    print("DIAGRAM AGENT BENCHMARK")
    print("Google ADK Implementation")
    print("=" * 60)

    quick_results = run_quick_benchmark()
    full_results = run_full_benchmark()

    # Calculate stats
    quick_success = sum(1 for r in quick_results if r.success)
    quick_avg_time = sum(r.duration_ms for r in quick_results) / len(quick_results)

    full_success = sum(1 for r in full_results if r.success)
    full_avg_time = sum(r.duration_ms for r in full_results) / len(full_results)
    avg_iterations = sum(r.iterations for r in full_results) / len(full_results)

    # Print summary
    print("\n" + "=" * 60)
    print("BENCHMARK SUMMARY - Google ADK")
    print("=" * 60)

    print("\n[Quick Mode]")
    print(f"  Success Rate: {quick_success}/{len(quick_results)}")
    print(f"  Avg Duration: {quick_avg_time:.0f}ms")

    print("\n[Full Pipeline]")
    print(f"  Success Rate: {full_success}/{len(full_results)}")
    print(f"  Avg Duration: {full_avg_time:.0f}ms")
    print(f"  Avg Iterations: {avg_iterations:.1f}")

    # Export JSON
    export_data = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "sdk": "Google ADK",
        "model": "gemma3:4b",
        "quickMode": {
            "successRate": quick_success / len(quick_results),
            "avgDurationMs": quick_avg_time,
            "results": [asdict(r) for r in quick_results],
        },
        "fullPipeline": {
            "successRate": full_success / len(full_results),
            "avgDurationMs": full_avg_time,
            "avgIterations": avg_iterations,
            "results": [asdict(r) for r in full_results],
        },
    }

    # Save to file
    with open("benchmark_google_adk.json", "w") as f:
        json.dump(export_data, f, indent=2)

    print(f"\nResults saved to: benchmark_google_adk.json")


if __name__ == "__main__":
    main()
