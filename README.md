
# Tools Repository

A collection of utility tools, scripts, and AI agents for development workflows. Inspired by [Simon Willison's tools repository](https://github.com/simonw/tools).

## Overview

This repository contains various development tools including:
- Python scripts and utilities
- HTML-based tools
- AI agent frameworks
- Benchmarking and comparison tools
- TypeScript/Node.js SDKs

## Repository Structure

### AI Agents
- **agent_hub/** - Core agent hub application
- **diagram_agent/** - Agent for diagram generation with orchestrator
- **health-agent/** - Health-focused agent with API client

### SDKs and Frameworks
- **agents-vercel-sdk/** - Multi-agent diagram generation using Vercel AI SDK
  - TypeScript implementation
  - Supports OpenAI, Anthropic, and Ollama providers
  - Includes CLI, server, and benchmarking tools

### Tools and Utilities
- **HTML Tools:**
  - `base64-encoder.html` - Base64 encoding/decoding utility
  - `color-wheel.html` - Color picker and wheel tool
  - `image-analysis.html` - Image analysis interface

- **Python Scripts:**
  - `build_index.py` - Index building utility
  - `db_to_json.py` - Database to JSON converter
  - `gather_links.py` - Link gathering script
  - `graphviz_tool.py` - Graphviz diagram tool

### Benchmarking and Testing
- **benchmark_google_adk.json** & **benchmark_vercel_sdk.json** - Performance benchmarks
- **dataflow_tests/** - Data flow testing and comparisons
- **diagram_benchmark/** - Diagram generation benchmarks across different models
- **model_tests/** - Testing various AI models (Gemma, GPT-OSS, Mistral, Qwen, etc.)

### Documentation
- **docs/** - Project documentation including:
  - CHANGELOG.md with detailed version history
  - Performance reports
  - Agent framework comparisons
  - MkDocs configuration for TechDocs

### Research and Examples
- **nushell-research/** - Nushell script examples and utilities

## Technology Stack
- **Python** - Core scripts and utilities
- **TypeScript/Node.js** - SDK development
- **HTML/CSS/JavaScript** - Web-based tools
- **AI/ML Frameworks:**
  - Vercel AI SDK
  - Ollama integration
  - OpenAI/Anthropic APIs

## Getting Started

### Python Dependencies
```bash
pip install -r requirements.txt
```

### TypeScript SDK
```bash
cd agents-vercel-sdk
npm install
npm run dev
```

## Status
- Repository: Active development
- Core functionality: Working and stable
- Agent frameworks: Fully operational
- Documentation: Complete with TechDocs integration

## Recent Updates
See [CHANGELOG.md](CHANGELOG.md) for detailed version history and recent changes.

## Inspiration
Inspired by: https://github.com/simonw/tools