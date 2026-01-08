#!/usr/bin/env python3
"""
Dataflow Visualization Comparison Tool

Compares Graphviz (DOT) and PlantUML output for complex data flow diagrams.
Tests multiple Ollama models and generates an HTML comparison page.
"""

import subprocess
import os
import json
import tempfile
import base64
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
import time

# ============== Reference Diagrams ==============

# The YouTube Summary Pipeline Data Flow (manually created reference)
REFERENCE_DOT = '''digraph YouTubeSummaryPipeline {
    // Global Settings
    rankdir=TB;
    splines=ortho;
    nodesep=0.6;
    ranksep=0.8;
    fontname="Arial";
    fontsize=11;

    // Default styles
    node [shape=box, style="rounded,filled", fontname="Arial", fontsize=10];
    edge [fontname="Arial", fontsize=9, color=gray40];

    // ============ Data Sources ============
    subgraph cluster_sources {
        label="Datenquellen";
        style=filled;
        fillcolor="#E3F2FD";
        fontsize=11;
        fontname="Arial Bold";

        YouTube [label="YouTube API", shape=cylinder, fillcolor="#FF0000", fontcolor=white];
        Config [label="config/\\nchannels.yaml", shape=note, fillcolor="#FFF9C4"];
        ENV [label=".env\\nCredentials", shape=note, fillcolor="#FFCDD2"];
    }

    // ============ Phase 1: Import ============
    subgraph cluster_import {
        label="Phase 1: Video Import";
        style=filled;
        fillcolor="#E8F5E9";
        fontsize=11;
        fontname="Arial Bold";

        LoadChannels [label="load_channels()", fillcolor="#A5D6A7"];
        ImportVideos [label="import_all_channels()", fillcolor="#81C784"];
        CheckNew [label="Neue Videos?", shape=diamond, fillcolor="#FFEB3B"];
    }

    // ============ Database ============
    subgraph cluster_database {
        label="SQLite Datenbank";
        style=filled;
        fillcolor="#F3E5F5";
        fontsize=11;
        fontname="Arial Bold";

        DB [label="videos.db", shape=cylinder, fillcolor="#CE93D8"];
        VideosTable [label="videos\\n(url, title, channel)", shape=box3d, fillcolor="#E1BEE7"];
        TranscriptsCol [label="transcript\\ncolumn", shape=box3d, fillcolor="#E1BEE7"];
        SummariesCol [label="summary\\ncolumn", shape=box3d, fillcolor="#E1BEE7"];
    }

    // ============ Phase 2: Processing ============
    subgraph cluster_processing {
        label="Phase 2: Video Processing (per video)";
        style=filled;
        fillcolor="#FFF3E0";
        fontsize=11;
        fontname="Arial Bold";

        GetTranscript [label="get_transcript()\\nYouTube Transcript API", fillcolor="#FFCC80"];
        HasTranscript [label="Transcript\\nvorhanden?", shape=diamond, fillcolor="#FFEB3B"];
        GenerateSummary [label="generate_summary()\\nOllama LLM", fillcolor="#FFB74D"];
        FormatHTML [label="format_summary_html()", fillcolor="#FFA726"];
        ExportMD [label="export_to_markdown()\\nObsidian", fillcolor="#FF9800"];
    }

    // ============ Phase 3: Export ============
    subgraph cluster_export {
        label="Phase 3: Ghost Export";
        style=filled;
        fillcolor="#E0F7FA";
        fontsize=11;
        fontname="Arial Bold";

        ExportGhost [label="export_to_ghost()\\nGhost API", fillcolor="#80DEEA"];
        CreatePost [label="Create/Update\\nBlog Post", fillcolor="#4DD0E1"];
    }

    // ============ Outputs ============
    subgraph cluster_outputs {
        label="Ausgaben";
        style=filled;
        fillcolor="#ECEFF1";
        fontsize=11;
        fontname="Arial Bold";

        MDFiles [label="Markdown Files\\n(Obsidian Vault)", shape=folder, fillcolor="#90A4AE"];
        GhostBlog [label="Ghost Blog\\nPosts", shape=tab, fillcolor="#78909C"];
        Logs [label="logs/\\nSession Logs", shape=note, fillcolor="#B0BEC5"];
    }

    // ============ Monitoring ============
    subgraph cluster_monitoring {
        label="Monitoring & Notifications";
        style=filled;
        fillcolor="#FCE4EC";
        fontsize=11;
        fontname="Arial Bold";

        HealthCheck [label="healthchecks.io\\nPings", shape=ellipse, fillcolor="#F48FB1"];
        Notifications [label="notify()\\n(new videos, errors)", shape=ellipse, fillcolor="#F06292"];
    }

    // ============ Edges ============

    // Data Sources -> Import
    Config -> LoadChannels [xlabel="channel list"];
    YouTube -> ImportVideos [xlabel="API calls", penwidth=2, color="#FF0000"];
    LoadChannels -> ImportVideos;

    // Import -> Database
    ImportVideos -> CheckNew;
    CheckNew -> VideosTable [xlabel="ja", color=green];
    CheckNew -> Notifications [xlabel="notify", style=dashed];

    // Database structure
    DB -> VideosTable [style=dotted, arrowhead=none];
    VideosTable -> TranscriptsCol [style=dotted, arrowhead=none];
    VideosTable -> SummariesCol [style=dotted, arrowhead=none];

    // Processing Flow
    VideosTable -> GetTranscript [xlabel="videos\\nwithout transcript", penwidth=1.5];
    GetTranscript -> HasTranscript;
    HasTranscript -> TranscriptsCol [xlabel="ja", color=green];
    HasTranscript -> GenerateSummary [xlabel="nein\\n(skip)", style=dashed, color=red];

    TranscriptsCol -> GenerateSummary [xlabel="transcript text", penwidth=1.5];
    GenerateSummary -> FormatHTML;
    FormatHTML -> SummariesCol [xlabel="HTML summary", color=blue];

    SummariesCol -> ExportMD [penwidth=1.5];
    ExportMD -> MDFiles [xlabel="write files", color=green];

    // Ghost Export
    SummariesCol -> ExportGhost [xlabel="summaries\\nlast 7 days", penwidth=1.5];
    ExportGhost -> CreatePost;
    CreatePost -> GhostBlog [xlabel="API POST", color=blue];

    // Monitoring
    ImportVideos -> HealthCheck [style=dashed, color=gray];
    ExportGhost -> HealthCheck [style=dashed, color=gray];
    GenerateSummary -> Logs [style=dashed, color=gray];

    // Environment
    ENV -> ImportVideos [style=dotted, xlabel="API keys"];
    ENV -> ExportGhost [style=dotted, xlabel="Ghost JWT"];
}'''

REFERENCE_PLANTUML = '''@startuml YouTubeSummaryPipeline
!theme plain
skinparam backgroundColor #FEFEFE
skinparam shadowing false

title YouTube Summary Pipeline - Datenfluss

' Styling
skinparam rectangle {
    BackgroundColor #E3F2FD
    BorderColor #1976D2
}
skinparam database {
    BackgroundColor #F3E5F5
    BorderColor #7B1FA2
}
skinparam cloud {
    BackgroundColor #E8F5E9
    BorderColor #388E3C
}

' Data Sources
package "Datenquellen" #E3F2FD {
    [YouTube API] as YouTube #FF0000
    [channels.yaml] as Config #FFF9C4
    [.env Credentials] as ENV #FFCDD2
}

' Database
database "SQLite DB" as DB #F3E5F5 {
    [videos table] as Videos
    [transcript] as Transcript
    [summary] as Summary
}

' Phase 1: Import
package "Phase 1: Import" #E8F5E9 {
    [load_channels()] as LoadChannels
    [import_all_channels()] as ImportVideos
}

' Phase 2: Processing
package "Phase 2: Processing" #FFF3E0 {
    [get_transcript()] as GetTranscript
    [generate_summary()] as GenSummary
    [format_summary_html()] as FormatHTML
    [export_to_markdown()] as ExportMD
}

' Phase 3: Export
package "Phase 3: Export" #E0F7FA {
    [export_to_ghost()] as ExportGhost
}

' Outputs
cloud "Ausgaben" #ECEFF1 {
    [Markdown Files\\n(Obsidian)] as MDFiles
    [Ghost Blog] as GhostBlog
    [Session Logs] as Logs
}

' Monitoring
package "Monitoring" #FCE4EC {
    [healthchecks.io] as Health
    [Notifications] as Notify
}

' Relationships - Phase 1
Config --> LoadChannels : channel list
LoadChannels --> ImportVideos
YouTube --> ImportVideos : API calls
ImportVideos --> Videos : neue Videos
ImportVideos --> Notify : new videos
ImportVideos ..> Health : ping

' Relationships - Phase 2
Videos --> GetTranscript : videos without transcript
GetTranscript --> Transcript : save transcript
Transcript --> GenSummary : transcript text
GenSummary --> FormatHTML
FormatHTML --> Summary : HTML summary
Summary --> ExportMD
ExportMD --> MDFiles : write files
GenSummary ..> Logs : log

' Relationships - Phase 3
Summary --> ExportGhost : last 7 days
ExportGhost --> GhostBlog : API POST
ExportGhost ..> Health : ping

' Environment
ENV ..> ImportVideos : API keys
ENV ..> ExportGhost : Ghost JWT

@enduml'''

# Simplified prompt for Ollama models
DATAFLOW_PROMPT = '''Create a Graphviz DOT diagram for a YouTube Video Summary Pipeline with these data flows:

DATA SOURCES:
- YouTube API (red cylinder) → imports videos
- channels.yaml config file → list of channels
- .env file → API credentials

PHASE 1 - IMPORT:
- load_channels() reads config
- import_all_channels() fetches from YouTube API
- Stores new videos in SQLite database

PHASE 2 - PROCESSING (per video):
- get_transcript() → fetches YouTube transcript
- generate_summary() → calls Ollama LLM with transcript
- format_summary_html() → formats as HTML
- export_to_markdown() → saves to Obsidian vault

PHASE 3 - EXPORT:
- export_to_ghost() → publishes to Ghost blog via API

MONITORING:
- healthchecks.io pings on import/export
- Notifications for new videos
- Session logging

Use:
- Clusters/subgraphs for each phase
- Proper shapes (cylinder for DB, folder for files, diamond for decisions)
- Color coding (green for success paths, red for errors, blue for data)
- Edge labels for data descriptions

Output ONLY valid DOT code, no explanations.'''


def check_graphviz() -> bool:
    """Check if graphviz is installed."""
    try:
        result = subprocess.run(["dot", "-V"], capture_output=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False


def check_plantuml() -> Optional[str]:
    """Check if plantuml is available - returns 'web' if web service available."""
    # Check if web service is accessible
    try:
        import urllib.request
        req = urllib.request.Request(
            "https://www.plantuml.com/plantuml/png/SyfFKj2rKt3CoKnELR1Io4ZDoSa70000",
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        response = urllib.request.urlopen(req, timeout=5)
        if response.status == 200:
            return "web"
    except Exception:
        pass

    # Try local installations
    possible_paths = [
        "/opt/homebrew/Cellar/plantuml/*/libexec/plantuml.jar",
        "/usr/local/Cellar/plantuml/*/libexec/plantuml.jar",
        "/usr/share/plantuml/plantuml.jar",
        os.path.expanduser("~/plantuml.jar"),
    ]

    import glob
    for pattern in possible_paths:
        matches = glob.glob(pattern)
        if matches:
            return matches[0]

    # Try running plantuml command directly
    try:
        result = subprocess.run(["plantuml", "-version"], capture_output=True)
        if result.returncode == 0:
            return "plantuml"
    except FileNotFoundError:
        pass

    return None


def render_dot_to_png(dot_code: str, output_path: str) -> bool:
    """Render DOT code to PNG."""
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.dot', delete=False) as f:
            f.write(dot_code)
            temp_path = f.name

        result = subprocess.run(
            ["dot", "-Tpng", "-Gdpi=150", temp_path, "-o", output_path],
            capture_output=True,
            text=True
        )

        os.unlink(temp_path)
        return result.returncode == 0
    except Exception as e:
        print(f"Error rendering DOT: {e}")
        return False


def render_plantuml_to_png(puml_code: str, output_path: str, plantuml_path: str = None) -> bool:
    """Render PlantUML code to PNG using web service or local installation."""
    import urllib.request
    import urllib.parse
    import zlib

    def encode_plantuml(text):
        """Encode PlantUML for URL."""
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
        if b < 10:
            return chr(48 + b)
        b -= 10
        if b < 26:
            return chr(65 + b)
        b -= 26
        if b < 26:
            return chr(97 + b)
        b -= 26
        if b == 0:
            return '-'
        if b == 1:
            return '_'
        return '?'

    try:
        # Try web service first
        encoded = encode_plantuml(puml_code)
        url = f"https://www.plantuml.com/plantuml/png/{encoded}"

        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        response = urllib.request.urlopen(req, timeout=30)

        with open(output_path, 'wb') as f:
            f.write(response.read())

        return True

    except Exception as e:
        print(f"PlantUML web service failed: {e}")

        # Try local installation as fallback
        if plantuml_path:
            try:
                with tempfile.NamedTemporaryFile(mode='w', suffix='.puml', delete=False) as f:
                    f.write(puml_code)
                    temp_path = f.name

                if plantuml_path == "plantuml":
                    cmd = ["plantuml", "-tpng", temp_path]
                else:
                    cmd = ["java", "-jar", plantuml_path, "-tpng", temp_path]

                result = subprocess.run(cmd, capture_output=True, text=True)

                generated_png = temp_path.replace('.puml', '.png')
                if os.path.exists(generated_png):
                    os.rename(generated_png, output_path)
                    os.unlink(temp_path)
                    return True

                os.unlink(temp_path)
            except Exception as e2:
                print(f"Local PlantUML also failed: {e2}")

        return False


def validate_dot_code(dot_code: str) -> tuple[bool, List[str]]:
    """Validate DOT code syntax."""
    errors = []

    # Basic checks
    if not any(kw in dot_code.lower() for kw in ['digraph', 'graph']):
        errors.append("No graph definition found")

    open_braces = dot_code.count('{')
    close_braces = dot_code.count('}')
    if open_braces != close_braces:
        errors.append(f"Unbalanced braces: {open_braces} {{ vs {close_braces} }}")

    # Try actual validation with dot
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.dot', delete=False) as f:
            f.write(dot_code)
            temp_path = f.name

        result = subprocess.run(
            ["dot", "-Tcanon", temp_path],
            capture_output=True,
            text=True
        )

        os.unlink(temp_path)

        if result.returncode != 0:
            errors.extend(result.stderr.strip().split('\n'))
            return False, errors

        return True, []
    except Exception as e:
        errors.append(str(e))
        return False, errors


def extract_dot_code(text: str) -> Optional[str]:
    """Extract DOT code from model response."""
    import re

    # Try markdown code blocks first
    patterns = [
        r'```(?:dot|graphviz)\s*\n(.*?)\n```',
        r'```\s*\n((?:di)?graph\s+\w+\s*\{.*?\})\s*\n```',
        r'((?:di)?graph\s+\w+\s*\{[^}]*(?:\{[^}]*\}[^}]*)*\})',
    ]

    for pattern in patterns:
        matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
        if matches:
            return matches[0].strip()

    return None


def test_ollama_model(model: str, prompt: str, timeout: int = 180) -> Dict[str, Any]:
    """Test an Ollama model with the given prompt."""
    try:
        import ollama
    except ImportError:
        return {"model": model, "error": "ollama package not installed", "success": False}

    result = {
        "model": model,
        "success": False,
        "response": None,
        "dot_code": None,
        "valid": False,
        "errors": [],
        "time": 0
    }

    try:
        start = time.time()
        response = ollama.generate(
            model=model,
            prompt=prompt,
            options={"num_predict": 4096}
        )
        result["time"] = time.time() - start
        result["success"] = True
        result["response"] = response.get("response", "")

        # Extract and validate DOT code
        dot_code = extract_dot_code(result["response"])
        result["dot_code"] = dot_code

        if dot_code:
            is_valid, errors = validate_dot_code(dot_code)
            result["valid"] = is_valid
            result["errors"] = errors
        else:
            result["errors"] = ["No DOT code found in response"]

    except Exception as e:
        result["error"] = str(e)

    return result


def get_available_models() -> List[str]:
    """Get list of available Ollama models."""
    try:
        import ollama
        models = ollama.list()
        return [m.get('name', m.get('model', '')) for m in models.get('models', [])]
    except:
        return []


def image_to_base64(path: str) -> Optional[str]:
    """Convert image to base64 for embedding in HTML."""
    try:
        with open(path, 'rb') as f:
            return base64.b64encode(f.read()).decode('utf-8')
    except:
        return None


def generate_html_report(
    results: List[Dict[str, Any]],
    output_dir: Path,
    reference_graphviz_png: Optional[str] = None,
    reference_plantuml_png: Optional[str] = None
) -> str:
    """Generate HTML comparison report."""

    # Count statistics
    total = len(results)
    valid = sum(1 for r in results if r.get("valid", False))

    html = f'''<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Graphviz vs PlantUML - Dataflow Comparison</title>
    <style>
        :root {{
            --bg-primary: #1a1a2e;
            --bg-secondary: #16213e;
            --bg-card: #0f3460;
            --text-primary: #eaeaea;
            --text-secondary: #a0a0a0;
            --accent: #e94560;
            --success: #4ade80;
            --warning: #fbbf24;
            --error: #f87171;
            --border: #2d4059;
        }}

        * {{ box-sizing: border-box; margin: 0; padding: 0; }}

        body {{
            font-family: 'Segoe UI', system-ui, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.6;
        }}

        .container {{
            max-width: 1600px;
            margin: 0 auto;
            padding: 2rem;
        }}

        header {{
            text-align: center;
            padding: 2rem 0;
            border-bottom: 1px solid var(--border);
            margin-bottom: 2rem;
        }}

        h1 {{
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
            background: linear-gradient(135deg, var(--accent), #ff6b6b);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}

        .subtitle {{
            color: var(--text-secondary);
            font-size: 1.1rem;
        }}

        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
        }}

        .stat-card {{
            background: var(--bg-card);
            padding: 1.5rem;
            border-radius: 12px;
            text-align: center;
            border: 1px solid var(--border);
        }}

        .stat-value {{
            font-size: 2.5rem;
            font-weight: bold;
            color: var(--accent);
        }}

        .stat-label {{
            color: var(--text-secondary);
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}

        section {{
            margin-bottom: 3rem;
        }}

        h2 {{
            font-size: 1.8rem;
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid var(--accent);
        }}

        h3 {{
            font-size: 1.3rem;
            margin-bottom: 0.5rem;
            color: var(--text-secondary);
        }}

        .comparison-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(600px, 1fr));
            gap: 2rem;
        }}

        .diagram-card {{
            background: var(--bg-secondary);
            border-radius: 12px;
            overflow: hidden;
            border: 1px solid var(--border);
        }}

        .diagram-header {{
            background: var(--bg-card);
            padding: 1rem 1.5rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .diagram-title {{
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}

        .badge {{
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 500;
        }}

        .badge-success {{ background: var(--success); color: #000; }}
        .badge-error {{ background: var(--error); color: #000; }}
        .badge-warning {{ background: var(--warning); color: #000; }}

        .diagram-image {{
            padding: 1rem;
            text-align: center;
            background: #fff;
            min-height: 400px;
            display: flex;
            align-items: center;
            justify-content: center;
        }}

        .diagram-image img {{
            max-width: 100%;
            max-height: 600px;
            height: auto;
        }}

        .diagram-meta {{
            padding: 1rem 1.5rem;
            background: var(--bg-card);
            font-size: 0.9rem;
            color: var(--text-secondary);
        }}

        .model-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
            gap: 1.5rem;
        }}

        .model-card {{
            background: var(--bg-secondary);
            border-radius: 12px;
            overflow: hidden;
            border: 1px solid var(--border);
            transition: transform 0.2s, box-shadow 0.2s;
        }}

        .model-card:hover {{
            transform: translateY(-4px);
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }}

        .model-header {{
            padding: 1rem;
            background: var(--bg-card);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .model-name {{
            font-weight: 600;
            font-size: 1.1rem;
        }}

        .model-image {{
            background: #fff;
            padding: 0.5rem;
            min-height: 250px;
            display: flex;
            align-items: center;
            justify-content: center;
        }}

        .model-image img {{
            max-width: 100%;
            max-height: 300px;
        }}

        .model-stats {{
            padding: 1rem;
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 0.5rem;
            text-align: center;
            font-size: 0.85rem;
        }}

        .model-stat-value {{
            font-weight: bold;
            color: var(--accent);
        }}

        .error-box {{
            background: rgba(248, 113, 113, 0.1);
            border: 1px solid var(--error);
            border-radius: 8px;
            padding: 1rem;
            margin-top: 0.5rem;
        }}

        .error-list {{
            list-style: none;
            font-size: 0.85rem;
            color: var(--error);
        }}

        .code-block {{
            background: var(--bg-primary);
            padding: 1rem;
            border-radius: 8px;
            overflow-x: auto;
            font-family: 'Fira Code', monospace;
            font-size: 0.85rem;
            max-height: 400px;
            overflow-y: auto;
        }}

        pre {{
            white-space: pre-wrap;
            word-break: break-word;
        }}

        .tabs {{
            display: flex;
            gap: 0.5rem;
            margin-bottom: 1rem;
        }}

        .tab {{
            padding: 0.75rem 1.5rem;
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 8px 8px 0 0;
            cursor: pointer;
            transition: background 0.2s;
        }}

        .tab:hover, .tab.active {{
            background: var(--accent);
        }}

        .tab-content {{
            display: none;
        }}

        .tab-content.active {{
            display: block;
        }}

        footer {{
            text-align: center;
            padding: 2rem;
            color: var(--text-secondary);
            border-top: 1px solid var(--border);
            margin-top: 3rem;
        }}

        .no-image {{
            color: var(--text-secondary);
            font-style: italic;
        }}

        /* Responsive */
        @media (max-width: 768px) {{
            .comparison-grid, .model-grid {{
                grid-template-columns: 1fr;
            }}

            .stats-grid {{
                grid-template-columns: repeat(2, 1fr);
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Graphviz vs PlantUML Comparison</h1>
            <p class="subtitle">Datenfluss-Visualisierung: YouTube Summary Pipeline</p>
            <p class="subtitle">Generiert am {datetime.now().strftime("%d.%m.%Y %H:%M")}</p>
        </header>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{total}</div>
                <div class="stat-label">Modelle getestet</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" style="color: var(--success)">{valid}</div>
                <div class="stat-label">Valide Ergebnisse</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" style="color: var(--error)">{total - valid}</div>
                <div class="stat-label">Fehlgeschlagen</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{valid/total*100:.0f}%</div>
                <div class="stat-label">Erfolgsrate</div>
            </div>
        </div>

        <section>
            <h2>Referenz-Diagramme (manuell erstellt)</h2>
            <div class="comparison-grid">
                <div class="diagram-card">
                    <div class="diagram-header">
                        <span class="diagram-title">Graphviz (DOT)</span>
                        <span class="badge badge-success">Reference</span>
                    </div>
                    <div class="diagram-image">
'''

    # Add reference Graphviz image
    if reference_graphviz_png and os.path.exists(reference_graphviz_png):
        b64 = image_to_base64(reference_graphviz_png)
        if b64:
            html += f'<img src="data:image/png;base64,{b64}" alt="Graphviz Reference">'
        else:
            html += '<p class="no-image">Bild konnte nicht geladen werden</p>'
    else:
        html += '<p class="no-image">Kein Referenzbild vorhanden</p>'

    html += '''
                    </div>
                    <div class="diagram-meta">
                        <strong>Format:</strong> DOT (Graphviz) | <strong>Engine:</strong> dot
                    </div>
                </div>

                <div class="diagram-card">
                    <div class="diagram-header">
                        <span class="diagram-title">PlantUML</span>
                        <span class="badge badge-success">Reference</span>
                    </div>
                    <div class="diagram-image">
'''

    # Add reference PlantUML image
    if reference_plantuml_png and os.path.exists(reference_plantuml_png):
        b64 = image_to_base64(reference_plantuml_png)
        if b64:
            html += f'<img src="data:image/png;base64,{b64}" alt="PlantUML Reference">'
        else:
            html += '<p class="no-image">Bild konnte nicht geladen werden</p>'
    else:
        html += '<p class="no-image">PlantUML nicht installiert oder Rendering fehlgeschlagen</p>'

    html += '''
                    </div>
                    <div class="diagram-meta">
                        <strong>Format:</strong> PlantUML | <strong>Engine:</strong> PlantUML Server
                    </div>
                </div>
            </div>
        </section>

        <section>
            <h2>Ollama Modell-Ergebnisse</h2>
            <div class="model-grid">
'''

    # Add model results
    for result in sorted(results, key=lambda x: (not x.get("valid", False), x.get("time", 999))):
        model_name = result.get("model", "Unknown")
        is_valid = result.get("valid", False)
        gen_time = result.get("time", 0)
        errors = result.get("errors", [])

        badge_class = "badge-success" if is_valid else "badge-error"
        badge_text = "Valid" if is_valid else "Invalid"

        # Get image if exists
        safe_name = model_name.replace(":", "_").replace("/", "_")
        png_path = output_dir / f"{safe_name}_output.png"

        html += f'''
                <div class="model-card">
                    <div class="model-header">
                        <span class="model-name">{model_name}</span>
                        <span class="badge {badge_class}">{badge_text}</span>
                    </div>
                    <div class="model-image">
'''

        if is_valid and png_path.exists():
            b64 = image_to_base64(str(png_path))
            if b64:
                html += f'<img src="data:image/png;base64,{b64}" alt="{model_name} output">'
            else:
                html += '<p class="no-image">Bild konnte nicht geladen werden</p>'
        elif not is_valid and errors:
            html += f'''
                        <div class="error-box">
                            <ul class="error-list">
'''
            for error in errors[:3]:
                html += f'<li>{error[:100]}...</li>' if len(error) > 100 else f'<li>{error}</li>'
            html += '''
                            </ul>
                        </div>
'''
        else:
            html += '<p class="no-image">Kein Output generiert</p>'

        html += f'''
                    </div>
                    <div class="model-stats">
                        <div>
                            <div class="model-stat-value">{gen_time:.1f}s</div>
                            <div>Zeit</div>
                        </div>
                        <div>
                            <div class="model-stat-value">{"Yes" if result.get("dot_code") else "No"}</div>
                            <div>DOT Code</div>
                        </div>
                        <div>
                            <div class="model-stat-value">{"Yes" if is_valid else "No"}</div>
                            <div>Valide</div>
                        </div>
                    </div>
                </div>
'''

    html += '''
            </div>
        </section>

        <section>
            <h2>Referenz-Code</h2>

            <div class="tabs">
                <div class="tab active" onclick="showTab('graphviz-code')">Graphviz DOT</div>
                <div class="tab" onclick="showTab('plantuml-code')">PlantUML</div>
            </div>

            <div id="graphviz-code" class="tab-content active">
                <div class="code-block">
                    <pre>''' + REFERENCE_DOT.replace('<', '&lt;').replace('>', '&gt;') + '''</pre>
                </div>
            </div>

            <div id="plantuml-code" class="tab-content">
                <div class="code-block">
                    <pre>''' + REFERENCE_PLANTUML.replace('<', '&lt;').replace('>', '&gt;') + '''</pre>
                </div>
            </div>
        </section>

        <footer>
            <p>Generiert mit dataflow_comparison.py</p>
            <p>Graphviz: Strukturierte Diagramme mit voller Kontrolle | PlantUML: Schnelle UML-Diagramme mit einfacher Syntax</p>
        </footer>
    </div>

    <script>
        function showTab(tabId) {
            // Hide all tabs and content
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

            // Show selected
            document.getElementById(tabId).classList.add('active');
            event.target.classList.add('active');
        }
    </script>
</body>
</html>'''

    return html


def main():
    """Main function."""
    output_dir = Path("./dataflow_tests")
    output_dir.mkdir(exist_ok=True)

    print("=" * 60)
    print("Dataflow Visualization Comparison")
    print("=" * 60)

    # Check tools
    has_graphviz = check_graphviz()
    plantuml_path = check_plantuml()

    print(f"\nGraphviz: {'Installed' if has_graphviz else 'NOT FOUND'}")
    print(f"PlantUML: {plantuml_path if plantuml_path else 'NOT FOUND'}")

    if not has_graphviz:
        print("\nERROR: Graphviz is required. Install with: brew install graphviz")
        return

    # Render reference diagrams
    print("\n" + "-" * 40)
    print("Rendering reference diagrams...")

    ref_graphviz_png = str(output_dir / "reference_graphviz.png")
    ref_plantuml_png = str(output_dir / "reference_plantuml.png")

    if render_dot_to_png(REFERENCE_DOT, ref_graphviz_png):
        print(f"  Graphviz: {ref_graphviz_png}")
    else:
        print("  Graphviz: FAILED")
        ref_graphviz_png = None

    if plantuml_path:
        if render_plantuml_to_png(REFERENCE_PLANTUML, ref_plantuml_png, plantuml_path):
            print(f"  PlantUML: {ref_plantuml_png}")
        else:
            print("  PlantUML: FAILED")
            ref_plantuml_png = None
    else:
        print("  PlantUML: Skipped (not installed)")
        ref_plantuml_png = None

    # Save reference code
    with open(output_dir / "reference.dot", "w") as f:
        f.write(REFERENCE_DOT)
    with open(output_dir / "reference.puml", "w") as f:
        f.write(REFERENCE_PLANTUML)

    # Test Ollama models
    print("\n" + "-" * 40)
    print("Testing Ollama models...")

    models = get_available_models()
    if not models:
        print("No Ollama models found. Skipping model tests.")
        results = []
    else:
        # Select a subset of models for testing
        test_models = [
            m for m in models
            if any(x in m.lower() for x in ['gemma3:4b', 'qwen2.5-coder', 'gpt-oss', 'mistral'])
        ][:5]  # Limit to 5 models

        if not test_models:
            test_models = models[:3]  # Just take first 3

        print(f"Testing {len(test_models)} models: {', '.join(test_models)}")

        results = []
        for model in test_models:
            print(f"\n  Testing {model}...")
            result = test_ollama_model(model, DATAFLOW_PROMPT)
            results.append(result)

            if result.get("valid") and result.get("dot_code"):
                safe_name = model.replace(":", "_").replace("/", "_")
                png_path = output_dir / f"{safe_name}_output.png"
                dot_path = output_dir / f"{safe_name}_output.dot"

                with open(dot_path, "w") as f:
                    f.write(result["dot_code"])

                if render_dot_to_png(result["dot_code"], str(png_path)):
                    print(f"    Valid - saved to {png_path}")
                else:
                    print(f"    Valid code but rendering failed")
            else:
                status = "Invalid" if result.get("success") else "Error"
                errors = result.get("errors", [result.get("error", "Unknown")])
                print(f"    {status}: {errors[0][:50]}...")

    # Save results
    with open(output_dir / "results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)

    # Generate HTML report
    print("\n" + "-" * 40)
    print("Generating HTML report...")

    html = generate_html_report(
        results,
        output_dir,
        ref_graphviz_png,
        ref_plantuml_png
    )

    html_path = output_dir / "comparison.html"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Report saved: {html_path}")

    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    valid_count = sum(1 for r in results if r.get("valid", False))
    print(f"Models tested: {len(results)}")
    print(f"Valid results: {valid_count}/{len(results)}")
    print(f"\nOpen {html_path} in a browser to view the comparison.")


if __name__ == "__main__":
    main()
