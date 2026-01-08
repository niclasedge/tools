# Tools

Collection of utility tools, scripts, and agents for development workflows.

## Overview

This repository contains a diverse set of development tools, utilities, and AI agents designed to enhance productivity and automate common workflows. Inspired by [Simon Willison's tools repository](https://github.com/simonw/tools), this collection includes Python scripts, HTML utilities, and advanced agent frameworks.

## Key Components

### Agent Frameworks

- **agent_hub/** - Central hub for managing and deploying AI agents
- **agents-vercel-sdk/** - Integration with Vercel AI SDK for agent deployment
- **diagram_agent/** - Specialized agent for generating diagrams and visualizations

### Utilities & Scripts

- **build_index.py** - Build and index tool collections
- **db_to_json.py** - Database to JSON conversion utility
- **gather_links.py** - Link gathering and organization tool
- **dataflow_comparison.py** - Compare dataflow patterns across frameworks
- **diagram_benchmark.py** - Performance benchmarking for diagram generation

### Web Tools

- **base64-encoder.html** - Browser-based Base64 encoding/decoding
- **color-wheel.html** - Interactive color selection and palette generation

### Benchmarking

Performance benchmarks and comparisons:

- Google ADK benchmark results: `benchmark_google_adk.json`
- Vercel SDK benchmark results: `benchmark_vercel_sdk.json`
- Diagram generation benchmarks in `diagram_benchmark/`

## Documentation

- [Changelog](CHANGELOG.md) - Version history and updates
- [Performance Report](PERFORMANCE_REPORT.md) - Detailed performance analysis
- [DotViz Generator](dotviz-generator-README.md) - Graphviz diagram generation
- [Agent Framework Comparison](agent_framework_comparison.md) - Comparison of different agent frameworks

## Getting Started

### Prerequisites

- Python 3.8+
- pip for package management
- Modern web browser for HTML tools

### Usage

Each tool can be run independently:

```bash
# Example: Build index
python build_index.py

# Example: Database conversion
python db_to_json.py

# Example: Run dataflow comparison
python dataflow_comparison.py
```

For web-based tools, simply open the HTML files in your browser.

## Development

This is an experimental collection of tools, continuously evolving with new utilities and agents.

### Contributing

Tools are added as needed for specific workflows. Each tool should be:

- Self-contained
- Well-documented
- Focused on a single purpose

## Tags

`python` `utilities` `agents` `automation` `development-tools` `diagrams` `benchmarking`

## Owner

niclasedge
