#!/usr/bin/env node
/**
 * Diagram Agent Web Server
 *
 * REST API for diagram generation using Hono.
 */

import { serve } from "@hono/node-server";
import { Hono } from "hono";
import { cors } from "hono/cors";
import { logger } from "hono/logger";

import { DiagramOrchestrator, quickDiagram } from "./orchestrator.js";
import { validateDiagram, renderDiagram, DiagramFormat } from "./tools.js";
import * as fs from "fs/promises";
import * as path from "path";
import * as os from "os";

const app = new Hono();

// Middleware
app.use("*", logger());
app.use("*", cors());

// Health check
app.get("/", (c) => {
  return c.json({
    name: "Diagram Agent API",
    version: "1.0.0",
    sdk: "Vercel AI SDK",
    endpoints: [
      "POST /generate - Generate diagram from description",
      "POST /validate - Validate diagram code",
      "POST /render - Render diagram to PNG",
      "POST /quick - Quick diagram generation",
    ],
  });
});

// Generate diagram (full pipeline)
app.post("/generate", async (c) => {
  try {
    const body = await c.req.json();
    const { description, format = "graphviz", model = "gemma3:4b" } = body;

    if (!description) {
      return c.json({ error: "description is required" }, 400);
    }

    const orchestrator = new DiagramOrchestrator({
      modelName: model,
      preferredFormat: format,
      outputDir: os.tmpdir(),
    });

    const result = await orchestrator.run(description);

    return c.json({
      success: result.success,
      code: result.diagramCode,
      format: result.format,
      outputPath: result.outputPath,
      iterations: result.iterations,
      duration: result.durationSeconds,
      errors: result.errors,
    });
  } catch (e) {
    const error = e instanceof Error ? e.message : String(e);
    return c.json({ error }, 500);
  }
});

// Quick generation
app.post("/quick", async (c) => {
  try {
    const body = await c.req.json();
    const { description, format = "graphviz" } = body;

    if (!description) {
      return c.json({ error: "description is required" }, 400);
    }

    const startTime = Date.now();
    const code = await quickDiagram(description, format);
    const validation = validateDiagram(code, format);
    const duration = (Date.now() - startTime) / 1000;

    return c.json({
      success: validation.valid,
      code,
      format: validation.format,
      valid: validation.valid,
      errors: validation.errors,
      suggestions: validation.suggestions,
      duration,
    });
  } catch (e) {
    const error = e instanceof Error ? e.message : String(e);
    return c.json({ error }, 500);
  }
});

// Validate code
app.post("/validate", async (c) => {
  try {
    const body = await c.req.json();
    const { code, format } = body;

    if (!code) {
      return c.json({ error: "code is required" }, 400);
    }

    const result = validateDiagram(code, format);

    return c.json({
      valid: result.valid,
      format: result.format,
      errors: result.errors,
      suggestions: result.suggestions,
    });
  } catch (e) {
    const error = e instanceof Error ? e.message : String(e);
    return c.json({ error }, 500);
  }
});

// Render to PNG
app.post("/render", async (c) => {
  try {
    const body = await c.req.json();
    const { code, format } = body;

    if (!code) {
      return c.json({ error: "code is required" }, 400);
    }

    const tmpFile = path.join(os.tmpdir(), `diagram_${Date.now()}.png`);
    const fmt = format
      ? DiagramFormat[format.toUpperCase() as keyof typeof DiagramFormat]
      : undefined;

    const result = await renderDiagram(code, tmpFile, fmt);

    if (result.success && result.outputPath) {
      const imageData = await fs.readFile(result.outputPath);
      const base64 = imageData.toString("base64");

      // Clean up temp file
      await fs.unlink(result.outputPath).catch(() => {});

      return c.json({
        success: true,
        format: result.format,
        image: `data:image/png;base64,${base64}`,
      });
    }

    return c.json({
      success: false,
      error: result.error,
      format: result.format,
    });
  } catch (e) {
    const error = e instanceof Error ? e.message : String(e);
    return c.json({ error }, 500);
  }
});

// Render and return image directly
app.post("/render/image", async (c) => {
  try {
    const body = await c.req.json();
    const { code, format } = body;

    if (!code) {
      return c.json({ error: "code is required" }, 400);
    }

    const tmpFile = path.join(os.tmpdir(), `diagram_${Date.now()}.png`);
    const fmt = format
      ? DiagramFormat[format.toUpperCase() as keyof typeof DiagramFormat]
      : undefined;

    const result = await renderDiagram(code, tmpFile, fmt);

    if (result.success && result.outputPath) {
      const imageData = await fs.readFile(result.outputPath);
      await fs.unlink(result.outputPath).catch(() => {});

      return new Response(imageData, {
        headers: {
          "Content-Type": "image/png",
          "Content-Disposition": "inline; filename=diagram.png",
        },
      });
    }

    return c.json({ error: result.error }, 500);
  } catch (e) {
    const error = e instanceof Error ? e.message : String(e);
    return c.json({ error }, 500);
  }
});

// Start server
const port = parseInt(process.env.PORT || "7860");

console.log(`
╔═══════════════════════════════════════════════════╗
║         Diagram Agent API Server                  ║
║         Powered by Vercel AI SDK                  ║
╠═══════════════════════════════════════════════════╣
║  Endpoints:                                       ║
║    POST /generate  - Full pipeline generation     ║
║    POST /quick     - Quick single-pass generation ║
║    POST /validate  - Validate diagram code        ║
║    POST /render    - Render to PNG (base64)       ║
╚═══════════════════════════════════════════════════╝

Server running at http://localhost:${port}
`);

serve({
  fetch: app.fetch,
  port,
});
