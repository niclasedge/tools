# Diagram Agent - Vercel AI SDK

Multi-agent diagram generation system built with Vercel AI SDK. This is a TypeScript port of the Python Google ADK implementation.

## Features

- Multi-agent pipeline: Analyzer → Generator → Validator → Improver → Renderer
- Support for Graphviz, Mermaid, and PlantUML formats
- Ollama integration for local LLM inference
- CLI, REST API, and programmatic interfaces
- Auto-validation and improvement loop

## Installation

```bash
cd agents-vercel-sdk
npm install
```

## Prerequisites

- Node.js 20+
- Ollama running locally with a model (e.g., `gemma3:4b`)
- Graphviz installed (`brew install graphviz` on macOS)

## Usage

### CLI

```bash
# Generate a diagram
npm run dev "A pipeline: Input -> Process -> Output"

# Quick mode (faster, single pass)
npm run dev -- -q "User login flow"

# Specify format
npm run dev -- -f mermaid "Database schema"

# Interactive mode
npm run dev -- -i

# Validate existing code
npm run dev -- --validate diagram.dot

# Render to PNG
npm run dev -- --render diagram.dot
```

### REST API

```bash
# Start server
npm run web

# Generate diagram
curl -X POST http://localhost:7860/generate \
  -H "Content-Type: application/json" \
  -d '{"description": "A data pipeline", "format": "graphviz"}'

# Quick generation
curl -X POST http://localhost:7860/quick \
  -H "Content-Type: application/json" \
  -d '{"description": "User login flow", "format": "mermaid"}'

# Validate code
curl -X POST http://localhost:7860/validate \
  -H "Content-Type: application/json" \
  -d '{"code": "digraph G { A -> B }"}'
```

### Programmatic

```typescript
import { DiagramOrchestrator, quickDiagram } from "./src/index.js";

// Quick generation
const code = await quickDiagram("A -> B -> C", "graphviz");

// Full pipeline
const orchestrator = new DiagramOrchestrator({
  modelName: "gemma3:4b",
  preferredFormat: "graphviz",
});

const result = await orchestrator.run("Complex system architecture");
console.log(result.diagramCode);
```

## Benchmark

```bash
npm run test
```

Runs performance benchmarks comparing quick mode vs full pipeline.

## Project Structure

```
agents-vercel-sdk/
├── src/
│   ├── tools.ts       # Diagram validation & rendering
│   ├── agents.ts      # Agent definitions (Analyzer, Generator, etc.)
│   ├── orchestrator.ts # Pipeline coordination
│   ├── cli.ts         # Command-line interface
│   ├── server.ts      # REST API server
│   ├── benchmark.ts   # Performance tests
│   └── index.ts       # Main exports
├── COMPARISON.md      # SDK comparison document
├── package.json
└── tsconfig.json
```

## Comparison with Google ADK

See [COMPARISON.md](./COMPARISON.md) for a detailed comparison between Vercel AI SDK and Google ADK implementations.

| Aspect | This Implementation | Google ADK Version |
|--------|---------------------|-------------------|
| Language | TypeScript | Python |
| Streaming | Native support | Via Runner |
| Type Safety | Full TypeScript | Python hints |
| Web Ready | Yes (Hono) | Yes (Gradio) |

## License

MIT
