#!/usr/bin/env python3
"""
Diagram Format Benchmark Tool

Compares Graphviz (DOT), PlantUML, and Mermaid for LLM code generation.
Tests multiple Ollama models with optimized prompts.
"""

import subprocess
import os
import json
import tempfile
import base64
import urllib.request
import urllib.parse
import zlib
import re
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

# ============== Configuration ==============

OUTPUT_DIR = Path("./diagram_benchmark")

class DiagramFormat(Enum):
    GRAPHVIZ = "graphviz"
    PLANTUML = "plantuml"
    MERMAID = "mermaid"

# ============== Reference Diagrams ==============

REFERENCE_GRAPHVIZ = '''digraph YouTubePipeline {
    rankdir=LR;
    node [shape=box, style="filled,rounded", fontname="Arial", fontsize=10];
    edge [fontname="Arial", fontsize=9];

    subgraph cluster_sources {
        label="Data Sources";
        style=filled; fillcolor="#E3F2FD";
        YouTubeAPI [label="YouTube API", shape=cylinder, fillcolor="#FF6B6B"];
        ConfigYAML [label="channels.yaml", shape=note, fillcolor="#FFF9C4"];
        EnvFile [label="env credentials", shape=note, fillcolor="#FFCDD2"];
    }

    subgraph cluster_import {
        label="Phase 1: Import";
        style=filled; fillcolor="#E8F5E9";
        LoadChannels [label="load_channels()", fillcolor="#A5D6A7"];
        ImportVideos [label="import_all_channels()", fillcolor="#81C784"];
    }

    subgraph cluster_db {
        label="Database";
        style=filled; fillcolor="#F3E5F5";
        SQLiteDB [label="SQLite DB", shape=cylinder, fillcolor="#CE93D8"];
    }

    subgraph cluster_process {
        label="Phase 2: Processing";
        style=filled; fillcolor="#FFF3E0";
        GetTranscript [label="get_transcript()", fillcolor="#FFCC80"];
        GenerateSummary [label="generate_summary()\\nOllama LLM", fillcolor="#FFB74D"];
        FormatHTML [label="format_summary_html()", fillcolor="#FFA726"];
        ExportMarkdown [label="export_to_markdown()", fillcolor="#FF9800"];
    }

    subgraph cluster_export {
        label="Phase 3: Export";
        style=filled; fillcolor="#E0F7FA";
        ExportGhost [label="export_to_ghost()", fillcolor="#80DEEA"];
    }

    subgraph cluster_output {
        label="Outputs";
        style=filled; fillcolor="#ECEFF1";
        ObsidianVault [label="Obsidian Vault", shape=folder, fillcolor="#90A4AE"];
        GhostBlog [label="Ghost Blog", shape=tab, fillcolor="#78909C"];
    }

    subgraph cluster_monitor {
        label="Monitoring";
        style=filled; fillcolor="#FCE4EC";
        HealthCheck [label="healthchecks.io", shape=ellipse, fillcolor="#F48FB1"];
        Notify [label="Notifications", shape=ellipse, fillcolor="#F06292"];
    }

    ConfigYAML -> LoadChannels;
    EnvFile -> ImportVideos [style=dashed];
    YouTubeAPI -> ImportVideos [color=red, penwidth=2];
    LoadChannels -> ImportVideos;
    ImportVideos -> SQLiteDB [label="store"];
    ImportVideos -> Notify [label="new videos", style=dashed];
    ImportVideos -> HealthCheck [style=dashed];

    SQLiteDB -> GetTranscript;
    GetTranscript -> GenerateSummary;
    GenerateSummary -> FormatHTML;
    FormatHTML -> SQLiteDB [label="save"];
    SQLiteDB -> ExportMarkdown;
    ExportMarkdown -> ObsidianVault;

    SQLiteDB -> ExportGhost;
    ExportGhost -> GhostBlog;
    ExportGhost -> HealthCheck [style=dashed];
}'''

REFERENCE_PLANTUML = '''@startuml
!theme plain
skinparam backgroundColor #FEFEFE
title YouTube Summary Pipeline

package "Data Sources" #E3F2FD {
    [YouTube API] as YT #FF6B6B
    [channels.yaml] as Config #FFF9C4
    [env credentials] as Env #FFCDD2
}

package "Phase 1: Import" #E8F5E9 {
    [load_channels()] as Load
    [import_all_channels()] as Import
}

database "SQLite DB" as DB #F3E5F5

package "Phase 2: Processing" #FFF3E0 {
    [get_transcript()] as Transcript
    [generate_summary()] as Summary
    [format_summary_html()] as Format
    [export_to_markdown()] as ExportMD
}

package "Phase 3: Export" #E0F7FA {
    [export_to_ghost()] as Ghost
}

cloud "Outputs" #ECEFF1 {
    [Obsidian Vault] as Obsidian
    [Ghost Blog] as Blog
}

package "Monitoring" #FCE4EC {
    [healthchecks.io] as Health
    [Notifications] as Notify
}

Config --> Load
Env ..> Import
YT --> Import
Load --> Import
Import --> DB : store
Import ..> Notify : new videos
Import ..> Health

DB --> Transcript
Transcript --> Summary
Summary --> Format
Format --> DB : save
DB --> ExportMD
ExportMD --> Obsidian

DB --> Ghost
Ghost --> Blog
Ghost ..> Health
@enduml'''

REFERENCE_MERMAID = '''flowchart LR
    subgraph Sources["Data Sources"]
        YT[("YouTube API")]
        Config["channels.yaml"]
        Env["env credentials"]
    end

    subgraph Import["Phase 1: Import"]
        Load["load_channels()"]
        ImportFn["import_all_channels()"]
    end

    subgraph DB["Database"]
        SQLite[("SQLite DB")]
    end

    subgraph Process["Phase 2: Processing"]
        Transcript["get_transcript()"]
        Summary["generate_summary()<br>Ollama LLM"]
        Format["format_summary_html()"]
        ExportMD["export_to_markdown()"]
    end

    subgraph Export["Phase 3: Export"]
        Ghost["export_to_ghost()"]
    end

    subgraph Outputs["Outputs"]
        Obsidian[/"Obsidian Vault"/]
        Blog[/"Ghost Blog"/]
    end

    subgraph Monitor["Monitoring"]
        Health(["healthchecks.io"])
        Notify(["Notifications"])
    end

    Config --> Load
    Env -.-> ImportFn
    YT ==> ImportFn
    Load --> ImportFn
    ImportFn --> SQLite
    ImportFn -.-> Notify
    ImportFn -.-> Health

    SQLite --> Transcript
    Transcript --> Summary
    Summary --> Format
    Format --> SQLite
    SQLite --> ExportMD
    ExportMD --> Obsidian

    SQLite --> Ghost
    Ghost --> Blog
    Ghost -.-> Health

    style YT fill:#FF6B6B
    style Sources fill:#E3F2FD
    style Import fill:#E8F5E9
    style DB fill:#F3E5F5
    style Process fill:#FFF3E0
    style Export fill:#E0F7FA
    style Outputs fill:#ECEFF1
    style Monitor fill:#FCE4EC'''

# ============== Optimized Prompts ==============

# Simple prompt for basic diagram
PROMPT_SIMPLE = '''Create a {format} diagram for a YouTube video processing pipeline.

The pipeline has 3 phases:
1. IMPORT: load_channels() reads config, import_all_channels() fetches from YouTube API, stores in SQLite
2. PROCESS: get_transcript() fetches transcript, generate_summary() calls LLM, export_to_markdown() saves files
3. EXPORT: export_to_ghost() publishes to Ghost blog

Also include: healthchecks.io monitoring, notifications for new videos.

Output ONLY valid {format} code. No explanations.'''

# Graphviz-specific optimized prompt
PROMPT_GRAPHVIZ_OPTIMIZED = '''Generate valid Graphviz DOT code for a data pipeline.

RULES - FOLLOW EXACTLY:
1. Start with: digraph PipelineName {
2. Node names must be alphanumeric (no dots, no special chars)
3. Use underscores instead of dots: env_file NOT .env
4. Cluster names start with cluster_: subgraph cluster_import
5. Labels can have special chars in quotes: label="load_channels()"

STRUCTURE:
- Data Sources: YouTubeAPI, ConfigFile, EnvFile
- Phase 1 Import: LoadChannels, ImportVideos -> SQLiteDB
- Phase 2 Process: GetTranscript -> GenerateSummary -> FormatHTML -> ExportMarkdown -> ObsidianVault
- Phase 3 Export: ExportGhost -> GhostBlog
- Monitoring: HealthCheck, Notifications

Use shapes: cylinder for databases, folder for file outputs, box for functions.
Use colors: fillcolor for nodes, style=filled.

Output ONLY the DOT code starting with "digraph" - no markdown, no explanations.'''

# PlantUML-specific optimized prompt
PROMPT_PLANTUML_OPTIMIZED = '''Generate valid PlantUML code for a data pipeline.

RULES:
1. Start with @startuml and end with @enduml
2. Use package for grouping, database for DB, cloud for outputs
3. Arrows: --> for flow, ..> for optional/monitoring
4. Use [Component] syntax for components

STRUCTURE:
- Data Sources: YouTube API, channels.yaml, env credentials
- Phase 1 Import: load_channels(), import_all_channels() -> SQLite DB
- Phase 2 Process: get_transcript() -> generate_summary() -> format_summary_html() -> export_to_markdown() -> Obsidian
- Phase 3 Export: export_to_ghost() -> Ghost Blog
- Monitoring: healthchecks.io, Notifications

Output ONLY PlantUML code starting with @startuml - no markdown, no explanations.'''

# Mermaid-specific optimized prompt
PROMPT_MERMAID_OPTIMIZED = '''Generate valid Mermaid flowchart code for a data pipeline.

RULES:
1. Start with: flowchart LR
2. Use subgraph Name["Label"] for grouping
3. Node syntax: ID["Label"] for boxes, ID[("Label")] for cylinders, ID[/"Label"/] for parallelograms
4. Arrows: --> for flow, -.-> for dashed, ==> for thick
5. End subgraphs with: end

STRUCTURE:
- Sources subgraph: YT[("YouTube API")], Config["channels.yaml"], Env["env credentials"]
- Import subgraph: Load["load_channels()"], ImportFn["import_all_channels()"]
- Database: SQLite[("SQLite DB")]
- Process subgraph: Transcript, Summary, Format, ExportMD -> Obsidian
- Export subgraph: Ghost -> Blog
- Monitor subgraph: Health, Notify

CONNECTIONS:
Config --> Load --> ImportFn
YT ==> ImportFn --> SQLite
SQLite --> Transcript --> Summary --> Format --> SQLite
SQLite --> ExportMD --> Obsidian
SQLite --> Ghost --> Blog
ImportFn -.-> Health
Ghost -.-> Health

Output ONLY Mermaid code starting with "flowchart" - no markdown code blocks, no explanations.'''


# ============== Rendering Functions ==============

def render_graphviz(dot_code: str, output_path: str) -> bool:
    """Render DOT code to PNG."""
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.dot', delete=False) as f:
            f.write(dot_code)
            temp_path = f.name

        result = subprocess.run(
            ["dot", "-Tpng", "-Gdpi=150", temp_path, "-o", output_path],
            capture_output=True, text=True
        )
        os.unlink(temp_path)
        return result.returncode == 0
    except Exception as e:
        print(f"  Graphviz error: {e}")
        return False


def render_plantuml(puml_code: str, output_path: str) -> bool:
    """Render PlantUML via web service."""
    def encode_plantuml(text):
        compressed = zlib.compress(text.encode('utf-8'))[2:-4]
        res = ""
        for i in range(0, len(compressed), 3):
            if i + 2 < len(compressed):
                b1, b2, b3 = compressed[i], compressed[i+1], compressed[i+2]
            elif i + 1 < len(compressed):
                b1, b2, b3 = compressed[i], compressed[i+1], 0
            else:
                b1, b2, b3 = compressed[i], 0, 0
            res += encode6bit(b1 >> 2)
            res += encode6bit(((b1 & 0x3) << 4) | (b2 >> 4))
            res += encode6bit(((b2 & 0xF) << 2) | (b3 >> 6))
            res += encode6bit(b3 & 0x3F)
        return res

    def encode6bit(b):
        if b < 10: return chr(48 + b)
        b -= 10
        if b < 26: return chr(65 + b)
        b -= 26
        if b < 26: return chr(97 + b)
        b -= 26
        return '-' if b == 0 else '_' if b == 1 else '?'

    try:
        encoded = encode_plantuml(puml_code)
        url = f"https://www.plantuml.com/plantuml/png/{encoded}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        response = urllib.request.urlopen(req, timeout=30)
        with open(output_path, 'wb') as f:
            f.write(response.read())
        return True
    except Exception as e:
        print(f"  PlantUML error: {e}")
        return False


def render_mermaid(mermaid_code: str, output_path: str) -> bool:
    """Render Mermaid via mermaid.ink web service."""
    try:
        # Use mermaid.ink service
        import base64
        encoded = base64.urlsafe_b64encode(mermaid_code.encode('utf-8')).decode('utf-8')
        url = f"https://mermaid.ink/img/{encoded}?type=png&bgColor=white"

        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        response = urllib.request.urlopen(req, timeout=30)
        with open(output_path, 'wb') as f:
            f.write(response.read())
        return True
    except Exception as e:
        print(f"  Mermaid error: {e}")
        return False


# ============== Validation Functions ==============

def validate_graphviz(code: str) -> Tuple[bool, List[str]]:
    """Validate Graphviz DOT code."""
    errors = []

    if not re.search(r'(di)?graph\s+\w+\s*\{', code, re.IGNORECASE):
        errors.append("No valid graph definition found")

    if code.count('{') != code.count('}'):
        errors.append(f"Unbalanced braces: {code.count('{')} {{ vs {code.count('}')} }}")

    # Check for common LLM mistakes
    if re.search(r'\.\w+\s*\[', code):
        errors.append("Node names cannot start with dots")

    if errors:
        return False, errors

    # Try actual validation
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.dot', delete=False) as f:
            f.write(code)
            temp_path = f.name

        result = subprocess.run(["dot", "-Tcanon", temp_path], capture_output=True, text=True)
        os.unlink(temp_path)

        if result.returncode != 0:
            errors.extend([e for e in result.stderr.strip().split('\n') if e])
            return False, errors
        return True, []
    except Exception as e:
        return False, [str(e)]


def validate_plantuml(code: str) -> Tuple[bool, List[str]]:
    """Validate PlantUML code (basic syntax check)."""
    errors = []

    if '@startuml' not in code.lower():
        errors.append("Missing @startuml")
    if '@enduml' not in code.lower():
        errors.append("Missing @enduml")

    # Try rendering to validate
    if not errors:
        try:
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
                temp_path = f.name
            if render_plantuml(code, temp_path):
                os.unlink(temp_path)
                return True, []
            else:
                errors.append("PlantUML rendering failed")
        except Exception as e:
            errors.append(str(e))

    return len(errors) == 0, errors


def validate_mermaid(code: str) -> Tuple[bool, List[str]]:
    """Validate Mermaid code (basic syntax check)."""
    errors = []

    code_lower = code.lower().strip()
    if not any(code_lower.startswith(x) for x in ['flowchart', 'graph', 'sequencediagram', 'classDiagram']):
        errors.append("Must start with flowchart, graph, sequenceDiagram, or classDiagram")

    # Check for balanced brackets
    if code.count('[') != code.count(']'):
        errors.append("Unbalanced square brackets")
    if code.count('(') != code.count(')'):
        errors.append("Unbalanced parentheses")

    # Check subgraph/end balance
    subgraph_count = len(re.findall(r'\bsubgraph\b', code, re.IGNORECASE))
    end_count = len(re.findall(r'\bend\b', code, re.IGNORECASE))
    if subgraph_count != end_count:
        errors.append(f"Unbalanced subgraph/end: {subgraph_count} subgraph vs {end_count} end")

    if not errors:
        # Try rendering
        try:
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
                temp_path = f.name
            if render_mermaid(code, temp_path):
                os.unlink(temp_path)
                return True, []
            else:
                errors.append("Mermaid rendering failed")
        except Exception as e:
            errors.append(str(e))

    return len(errors) == 0, errors


# ============== Code Extraction ==============

def extract_code(text: str, format_type: DiagramFormat) -> Optional[str]:
    """Extract diagram code from LLM response."""

    # Remove markdown code blocks
    patterns = {
        DiagramFormat.GRAPHVIZ: [
            r'```(?:dot|graphviz)\s*\n(.*?)\n```',
            r'```\s*\n((?:di)?graph\s+\w+\s*\{.*?\})\s*```',
            r'((?:di)?graph\s+\w+\s*\{[\s\S]*?\})\s*$',
        ],
        DiagramFormat.PLANTUML: [
            r'```(?:plantuml|puml)\s*\n(.*?)\n```',
            r'```\s*\n(@startuml.*?@enduml)\s*```',
            r'(@startuml[\s\S]*?@enduml)',
        ],
        DiagramFormat.MERMAID: [
            r'```mermaid\s*\n(.*?)\n```',
            r'```\s*\n((?:flowchart|graph)\s+\w+[\s\S]*?)\n```',
            r'((?:flowchart|graph)\s+\w+[\s\S]*?)$',
        ],
    }

    for pattern in patterns.get(format_type, []):
        matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
        if matches:
            return matches[0].strip()

    # Fallback: return cleaned text
    text = text.strip()
    text = re.sub(r'^```\w*\s*\n?', '', text)
    text = re.sub(r'\n?```\s*$', '', text)
    return text if text else None


# ============== Model Testing ==============

def test_ollama_model(model: str, prompt: str, format_type: DiagramFormat) -> Dict[str, Any]:
    """Test an Ollama model with a specific prompt."""
    try:
        import ollama
    except ImportError:
        return {"model": model, "error": "ollama not installed", "valid": False}

    result = {
        "model": model,
        "format": format_type.value,
        "valid": False,
        "code": None,
        "errors": [],
        "time": 0,
    }

    try:
        start = time.time()
        response = ollama.generate(
            model=model,
            prompt=prompt,
            options={"num_predict": 4096, "temperature": 0.3}
        )
        result["time"] = time.time() - start
        result["response"] = response.get("response", "")

        # Extract code
        code = extract_code(result["response"], format_type)
        result["code"] = code

        if not code:
            result["errors"] = ["No code extracted from response"]
            return result

        # Validate
        validators = {
            DiagramFormat.GRAPHVIZ: validate_graphviz,
            DiagramFormat.PLANTUML: validate_plantuml,
            DiagramFormat.MERMAID: validate_mermaid,
        }

        is_valid, errors = validators[format_type](code)
        result["valid"] = is_valid
        result["errors"] = errors

    except Exception as e:
        result["errors"] = [str(e)]

    return result


def get_ollama_models() -> List[str]:
    """Get list of available Ollama models."""
    try:
        import ollama
        models = ollama.list()
        return [m.get('name', m.get('model', '')) for m in models.get('models', [])]
    except:
        return []


# ============== HTML Report ==============

def image_to_base64(path: str) -> Optional[str]:
    """Convert image to base64."""
    try:
        with open(path, 'rb') as f:
            return base64.b64encode(f.read()).decode('utf-8')
    except:
        return None


def generate_html_report(results: Dict[str, List[Dict]], output_dir: Path) -> str:
    """Generate comprehensive HTML comparison report."""

    # Calculate stats per format
    format_stats = {}
    for fmt, res_list in results.items():
        valid = sum(1 for r in res_list if r.get("valid", False))
        total = len(res_list)
        avg_time = sum(r.get("time", 0) for r in res_list) / max(total, 1)
        format_stats[fmt] = {"valid": valid, "total": total, "avg_time": avg_time}

    html = f'''<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Diagram Format Benchmark - Graphviz vs PlantUML vs Mermaid</title>
    <style>
        :root {{
            --bg: #0f0f23;
            --card: #1a1a3e;
            --border: #2d2d5a;
            --text: #e0e0e0;
            --muted: #8888aa;
            --accent: #00d4aa;
            --graphviz: #4CAF50;
            --plantuml: #2196F3;
            --mermaid: #FF9800;
            --success: #4ade80;
            --error: #f87171;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: 'Segoe UI', system-ui, sans-serif;
            background: var(--bg);
            color: var(--text);
            line-height: 1.6;
        }}
        .container {{ max-width: 1800px; margin: 0 auto; padding: 2rem; }}

        header {{
            text-align: center;
            padding: 2rem 0 3rem;
            border-bottom: 1px solid var(--border);
        }}
        h1 {{
            font-size: 2.5rem;
            background: linear-gradient(135deg, var(--graphviz), var(--plantuml), var(--mermaid));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.5rem;
        }}
        .subtitle {{ color: var(--muted); }}

        .stats-row {{
            display: flex;
            gap: 1rem;
            justify-content: center;
            margin: 2rem 0;
            flex-wrap: wrap;
        }}
        .stat-card {{
            background: var(--card);
            padding: 1.5rem 2rem;
            border-radius: 12px;
            text-align: center;
            border-left: 4px solid;
            min-width: 200px;
        }}
        .stat-card.graphviz {{ border-color: var(--graphviz); }}
        .stat-card.plantuml {{ border-color: var(--plantuml); }}
        .stat-card.mermaid {{ border-color: var(--mermaid); }}
        .stat-value {{
            font-size: 2.5rem;
            font-weight: bold;
        }}
        .stat-card.graphviz .stat-value {{ color: var(--graphviz); }}
        .stat-card.plantuml .stat-value {{ color: var(--plantuml); }}
        .stat-card.mermaid .stat-value {{ color: var(--mermaid); }}
        .stat-label {{ color: var(--muted); text-transform: uppercase; font-size: 0.8rem; letter-spacing: 1px; }}

        section {{ margin: 3rem 0; }}
        h2 {{
            font-size: 1.6rem;
            margin-bottom: 1.5rem;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid var(--accent);
        }}

        .reference-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 1.5rem;
        }}
        @media (max-width: 1200px) {{
            .reference-grid {{ grid-template-columns: 1fr; }}
        }}

        .diagram-card {{
            background: var(--card);
            border-radius: 12px;
            overflow: hidden;
            border: 1px solid var(--border);
        }}
        .diagram-header {{
            padding: 1rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid var(--border);
        }}
        .diagram-title {{
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}
        .format-badge {{
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
        }}
        .format-badge.graphviz {{ background: var(--graphviz); color: #000; }}
        .format-badge.plantuml {{ background: var(--plantuml); color: #fff; }}
        .format-badge.mermaid {{ background: var(--mermaid); color: #000; }}

        .diagram-image {{
            background: #fff;
            padding: 1rem;
            min-height: 300px;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        .diagram-image img {{
            max-width: 100%;
            max-height: 500px;
        }}

        .results-table {{
            width: 100%;
            border-collapse: collapse;
            background: var(--card);
            border-radius: 12px;
            overflow: hidden;
        }}
        .results-table th, .results-table td {{
            padding: 1rem;
            text-align: left;
            border-bottom: 1px solid var(--border);
        }}
        .results-table th {{
            background: rgba(0,0,0,0.3);
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.8rem;
            letter-spacing: 1px;
        }}
        .results-table tr:hover {{
            background: rgba(255,255,255,0.02);
        }}

        .status-badge {{
            padding: 0.25rem 0.75rem;
            border-radius: 12px;
            font-size: 0.85rem;
            font-weight: 500;
        }}
        .status-badge.valid {{ background: var(--success); color: #000; }}
        .status-badge.invalid {{ background: var(--error); color: #000; }}

        .model-outputs {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 1.5rem;
            margin-top: 2rem;
        }}

        .model-card {{
            background: var(--card);
            border-radius: 12px;
            overflow: hidden;
            border: 1px solid var(--border);
        }}
        .model-header {{
            padding: 1rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid var(--border);
        }}
        .model-name {{ font-weight: 600; }}
        .model-image {{
            background: #fff;
            padding: 0.5rem;
            min-height: 200px;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        .model-image img {{ max-width: 100%; max-height: 250px; }}
        .model-meta {{
            padding: 0.75rem 1rem;
            font-size: 0.85rem;
            color: var(--muted);
            display: flex;
            justify-content: space-between;
        }}

        .error-text {{
            color: var(--error);
            font-size: 0.85rem;
            padding: 1rem;
        }}

        .tabs {{
            display: flex;
            gap: 0.5rem;
            margin-bottom: 1rem;
        }}
        .tab {{
            padding: 0.75rem 1.5rem;
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.2s;
        }}
        .tab:hover {{ background: rgba(255,255,255,0.05); }}
        .tab.active {{ background: var(--accent); color: #000; }}
        .tab-content {{ display: none; }}
        .tab-content.active {{ display: block; }}

        .code-block {{
            background: #000;
            padding: 1rem;
            border-radius: 8px;
            overflow-x: auto;
            font-family: 'Fira Code', monospace;
            font-size: 0.8rem;
            max-height: 400px;
            overflow-y: auto;
        }}
        pre {{ white-space: pre-wrap; }}

        footer {{
            text-align: center;
            padding: 2rem;
            color: var(--muted);
            border-top: 1px solid var(--border);
            margin-top: 3rem;
        }}

        .winner-badge {{
            display: inline-block;
            padding: 0.5rem 1rem;
            background: linear-gradient(135deg, gold, orange);
            color: #000;
            border-radius: 20px;
            font-weight: bold;
            font-size: 0.9rem;
            margin-left: 0.5rem;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Diagram Format Benchmark</h1>
            <p class="subtitle">Graphviz vs PlantUML vs Mermaid - LLM Code Generation Test</p>
            <p class="subtitle">Generiert am {datetime.now().strftime("%d.%m.%Y %H:%M")}</p>
        </header>

        <div class="stats-row">
'''

    # Add stats cards
    for fmt, stats in format_stats.items():
        rate = stats["valid"] / max(stats["total"], 1) * 100
        html += f'''
            <div class="stat-card {fmt}">
                <div class="stat-value">{rate:.0f}%</div>
                <div class="stat-label">{fmt.upper()}</div>
                <div style="color: var(--muted); font-size: 0.9rem; margin-top: 0.5rem;">
                    {stats["valid"]}/{stats["total"]} valid | {stats["avg_time"]:.1f}s avg
                </div>
            </div>
'''

    html += '''
        </div>

        <section>
            <h2>Referenz-Diagramme (manuell erstellt)</h2>
            <div class="reference-grid">
'''

    # Add reference diagrams
    for fmt, label in [("graphviz", "Graphviz (DOT)"), ("plantuml", "PlantUML"), ("mermaid", "Mermaid")]:
        png_path = output_dir / f"reference_{fmt}.png"
        html += f'''
                <div class="diagram-card">
                    <div class="diagram-header">
                        <span class="diagram-title">{label}</span>
                        <span class="format-badge {fmt}">Reference</span>
                    </div>
                    <div class="diagram-image">
'''
        if png_path.exists():
            b64 = image_to_base64(str(png_path))
            if b64:
                html += f'<img src="data:image/png;base64,{b64}" alt="{label}">'
        else:
            html += f'<span style="color: var(--muted)">Nicht verfügbar</span>'
        html += '''
                    </div>
                </div>
'''

    html += '''
            </div>
        </section>

        <section>
            <h2>Modell-Ergebnisse Vergleich</h2>
            <table class="results-table">
                <thead>
                    <tr>
                        <th>Modell</th>
                        <th>Graphviz</th>
                        <th>PlantUML</th>
                        <th>Mermaid</th>
                        <th>Gesamt</th>
                    </tr>
                </thead>
                <tbody>
'''

    # Build comparison table
    models = set()
    for fmt_results in results.values():
        for r in fmt_results:
            models.add(r.get("model", ""))

    for model in sorted(models):
        html += f'<tr><td><strong>{model}</strong></td>'
        total_valid = 0
        for fmt in ["graphviz", "plantuml", "mermaid"]:
            model_result = next((r for r in results.get(fmt, []) if r.get("model") == model), None)
            if model_result:
                is_valid = model_result.get("valid", False)
                if is_valid:
                    total_valid += 1
                status_class = "valid" if is_valid else "invalid"
                time_str = f'{model_result.get("time", 0):.1f}s'
                html += f'<td><span class="status-badge {status_class}">{"✓" if is_valid else "✗"}</span> {time_str}</td>'
            else:
                html += '<td>-</td>'
        html += f'<td><strong>{total_valid}/3</strong></td></tr>'

    html += '''
                </tbody>
            </table>
        </section>
'''

    # Add model output sections for each format
    for fmt in ["graphviz", "plantuml", "mermaid"]:
        fmt_results = results.get(fmt, [])
        if not fmt_results:
            continue

        html += f'''
        <section>
            <h2>{fmt.upper()} Modell-Outputs</h2>
            <div class="model-outputs">
'''
        for r in sorted(fmt_results, key=lambda x: (not x.get("valid", False), x.get("time", 999))):
            model = r.get("model", "Unknown")
            is_valid = r.get("valid", False)
            gen_time = r.get("time", 0)

            safe_name = model.replace(":", "_").replace("/", "_")
            png_path = output_dir / f"{safe_name}_{fmt}.png"

            html += f'''
                <div class="model-card">
                    <div class="model-header">
                        <span class="model-name">{model}</span>
                        <span class="status-badge {"valid" if is_valid else "invalid"}">{"Valid" if is_valid else "Invalid"}</span>
                    </div>
                    <div class="model-image">
'''
            if is_valid and png_path.exists():
                b64 = image_to_base64(str(png_path))
                if b64:
                    html += f'<img src="data:image/png;base64,{b64}" alt="{model}">'
            elif r.get("errors"):
                html += f'<span class="error-text">{r["errors"][0][:100]}...</span>'
            else:
                html += '<span style="color: var(--muted)">Kein Output</span>'

            html += f'''
                    </div>
                    <div class="model-meta">
                        <span>Zeit: {gen_time:.1f}s</span>
                        <span class="format-badge {fmt}">{fmt}</span>
                    </div>
                </div>
'''
        html += '''
            </div>
        </section>
'''

    # Determine winner
    best_format = max(format_stats.items(), key=lambda x: x[1]["valid"] / max(x[1]["total"], 1))

    html += f'''
        <section>
            <h2>Fazit</h2>
            <div style="background: var(--card); padding: 2rem; border-radius: 12px; border: 1px solid var(--border);">
                <h3 style="margin-bottom: 1rem;">
                    Bestes Format für LLM-Generierung:
                    <span class="winner-badge">{best_format[0].upper()}</span>
                </h3>
                <p style="color: var(--muted); margin-bottom: 1rem;">
                    Mit einer Erfolgsrate von {best_format[1]["valid"]}/{best_format[1]["total"]}
                    ({best_format[1]["valid"]/max(best_format[1]["total"],1)*100:.0f}%) ist {best_format[0].upper()}
                    das am besten für LLM-Code-Generierung geeignete Format.
                </p>
                <table style="width: 100%; color: var(--text);">
                    <tr>
                        <th style="text-align: left; padding: 0.5rem;">Format</th>
                        <th style="text-align: left; padding: 0.5rem;">Vorteile</th>
                        <th style="text-align: left; padding: 0.5rem;">Nachteile</th>
                    </tr>
                    <tr>
                        <td style="padding: 0.5rem;"><strong style="color: var(--graphviz);">Graphviz</strong></td>
                        <td style="padding: 0.5rem;">Volle Kontrolle, viele Shapes, professionell</td>
                        <td style="padding: 0.5rem;">Komplexere Syntax, mehr Fehlerquellen</td>
                    </tr>
                    <tr>
                        <td style="padding: 0.5rem;"><strong style="color: var(--plantuml);">PlantUML</strong></td>
                        <td style="padding: 0.5rem;">UML-nativ, gute Dokumentation</td>
                        <td style="padding: 0.5rem;">Weniger flexibel, Server-abhängig</td>
                    </tr>
                    <tr>
                        <td style="padding: 0.5rem;"><strong style="color: var(--mermaid);">Mermaid</strong></td>
                        <td style="padding: 0.5rem;">Einfache Syntax, Markdown-kompatibel</td>
                        <td style="padding: 0.5rem;">Weniger Styling-Optionen</td>
                    </tr>
                </table>
            </div>
        </section>

        <footer>
            <p>Generiert mit diagram_benchmark.py</p>
        </footer>
    </div>

    <script>
        function showTab(tabId) {{
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            document.getElementById(tabId).classList.add('active');
            event.target.classList.add('active');
        }}
    </script>
</body>
</html>'''

    return html


# ============== Main ==============

def main():
    OUTPUT_DIR.mkdir(exist_ok=True)

    print("=" * 70)
    print("DIAGRAM FORMAT BENCHMARK")
    print("Graphviz vs PlantUML vs Mermaid - LLM Generation Test")
    print("=" * 70)

    # Render reference diagrams
    print("\n[1/4] Rendering reference diagrams...")

    ref_files = {
        "graphviz": (REFERENCE_GRAPHVIZ, render_graphviz),
        "plantuml": (REFERENCE_PLANTUML, render_plantuml),
        "mermaid": (REFERENCE_MERMAID, render_mermaid),
    }

    for fmt, (code, renderer) in ref_files.items():
        output_path = OUTPUT_DIR / f"reference_{fmt}.png"
        code_path = OUTPUT_DIR / f"reference.{fmt[:3]}"

        with open(code_path, "w") as f:
            f.write(code)

        if renderer(code, str(output_path)):
            print(f"  ✓ {fmt}: {output_path}")
        else:
            print(f"  ✗ {fmt}: rendering failed")

    # Get models
    print("\n[2/4] Getting available models...")
    all_models = get_ollama_models()

    if not all_models:
        print("  No Ollama models found!")
        return

    # Select models for testing - prioritize good code generators
    priority_patterns = ['gemma3:4b', 'qwen2.5-coder', 'gpt-oss', 'mistral', 'qwen3', 'deepseek']
    test_models = []

    for pattern in priority_patterns:
        for model in all_models:
            if pattern in model.lower() and model not in test_models:
                test_models.append(model)
                if len(test_models) >= 6:
                    break
        if len(test_models) >= 6:
            break

    if len(test_models) < 3:
        test_models = all_models[:5]

    print(f"  Testing {len(test_models)} models: {', '.join(test_models)}")

    # Test each format
    print("\n[3/4] Testing models with each format...")

    results = {"graphviz": [], "plantuml": [], "mermaid": []}

    prompts = {
        DiagramFormat.GRAPHVIZ: PROMPT_GRAPHVIZ_OPTIMIZED,
        DiagramFormat.PLANTUML: PROMPT_PLANTUML_OPTIMIZED,
        DiagramFormat.MERMAID: PROMPT_MERMAID_OPTIMIZED,
    }

    renderers = {
        DiagramFormat.GRAPHVIZ: render_graphviz,
        DiagramFormat.PLANTUML: render_plantuml,
        DiagramFormat.MERMAID: render_mermaid,
    }

    for fmt in [DiagramFormat.GRAPHVIZ, DiagramFormat.PLANTUML, DiagramFormat.MERMAID]:
        print(f"\n  --- {fmt.value.upper()} ---")

        for model in test_models:
            print(f"  Testing {model}...", end=" ", flush=True)

            result = test_ollama_model(model, prompts[fmt], fmt)
            results[fmt.value].append(result)

            # Save and render if valid
            if result.get("valid") and result.get("code"):
                safe_name = model.replace(":", "_").replace("/", "_")
                code_path = OUTPUT_DIR / f"{safe_name}_{fmt.value}.txt"
                png_path = OUTPUT_DIR / f"{safe_name}_{fmt.value}.png"

                with open(code_path, "w") as f:
                    f.write(result["code"])

                renderers[fmt](result["code"], str(png_path))
                print(f"✓ Valid ({result['time']:.1f}s)")
            else:
                error = result.get("errors", ["Unknown"])[0][:40]
                print(f"✗ Invalid: {error}...")

    # Save results JSON
    with open(OUTPUT_DIR / "results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)

    # Generate HTML report
    print("\n[4/4] Generating HTML report...")
    html = generate_html_report(results, OUTPUT_DIR)

    html_path = OUTPUT_DIR / "benchmark.html"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"  Report: {html_path}")

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    for fmt, res_list in results.items():
        valid = sum(1 for r in res_list if r.get("valid", False))
        total = len(res_list)
        print(f"  {fmt.upper():12} {valid}/{total} valid ({valid/max(total,1)*100:.0f}%)")

    print(f"\nOpen {html_path} in a browser to view the full comparison.")


if __name__ == "__main__":
    main()
