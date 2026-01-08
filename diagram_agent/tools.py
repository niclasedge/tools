"""
Diagram Agent Tools

Reusable tools for diagram validation, rendering, and file operations.
"""

import subprocess
import tempfile
import os
import re
import base64
import urllib.request
import zlib
from typing import Optional, Tuple, List
from dataclasses import dataclass
from enum import Enum


class DiagramFormat(Enum):
    GRAPHVIZ = "graphviz"
    PLANTUML = "plantuml"
    MERMAID = "mermaid"


@dataclass
class ValidationResult:
    """Result of diagram validation."""
    valid: bool
    format: DiagramFormat
    errors: List[str]
    code: str
    suggestions: List[str] = None

    def __post_init__(self):
        if self.suggestions is None:
            self.suggestions = []


@dataclass
class RenderResult:
    """Result of diagram rendering."""
    success: bool
    output_path: Optional[str]
    error: Optional[str]
    format: DiagramFormat


# ============== Validation Tools ==============

def validate_graphviz(code: str) -> ValidationResult:
    """
    Validate Graphviz DOT code.

    Args:
        code: The DOT code to validate

    Returns:
        ValidationResult with validation details
    """
    errors = []
    suggestions = []

    # Basic syntax checks
    if not re.search(r'(di)?graph\s+\w+\s*\{', code, re.IGNORECASE):
        errors.append("No valid graph definition found (digraph Name { or graph Name {)")
        suggestions.append("Start with: digraph MyDiagram {")

    # Check brace balance
    open_braces = code.count('{')
    close_braces = code.count('}')
    if open_braces != close_braces:
        errors.append(f"Unbalanced braces: {open_braces} '{{' vs {close_braces} '}}'")
        suggestions.append("Ensure every '{' has a matching '}'")

    # Check for common LLM mistakes
    if re.search(r'\.\w+\s*\[', code):
        errors.append("Node names cannot start with dots (e.g., .env is invalid)")
        suggestions.append("Use underscores: env_file instead of .env")

    if re.search(r':\w+\s*->', code):
        errors.append("Port syntax (:port) in node names may cause issues")
        suggestions.append("Define ports separately using record shapes")

    # If basic checks pass, try actual validation with dot
    if not errors:
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.dot', delete=False) as f:
                f.write(code)
                temp_path = f.name

            result = subprocess.run(
                ["dot", "-Tcanon", temp_path],
                capture_output=True,
                text=True,
                timeout=10
            )

            os.unlink(temp_path)

            if result.returncode != 0:
                for line in result.stderr.strip().split('\n'):
                    if line.strip():
                        errors.append(line.strip())

        except FileNotFoundError:
            errors.append("Graphviz not installed. Install with: brew install graphviz")
        except subprocess.TimeoutExpired:
            errors.append("Validation timed out - code may be too complex")
        except Exception as e:
            errors.append(f"Validation error: {str(e)}")

    return ValidationResult(
        valid=len(errors) == 0,
        format=DiagramFormat.GRAPHVIZ,
        errors=errors,
        code=code,
        suggestions=suggestions
    )


def validate_mermaid(code: str) -> ValidationResult:
    """
    Validate Mermaid diagram code.

    Args:
        code: The Mermaid code to validate

    Returns:
        ValidationResult with validation details
    """
    errors = []
    suggestions = []

    code_stripped = code.strip()

    # Check for valid start
    valid_starts = ['flowchart', 'graph', 'sequencediagram', 'classdiagram',
                   'erdiagram', 'gantt', 'pie', 'statediagram']

    has_valid_start = any(code_stripped.lower().startswith(s) for s in valid_starts)
    if not has_valid_start:
        errors.append("Must start with a valid diagram type (flowchart, graph, etc.)")
        suggestions.append("Start with: flowchart LR or graph TD")

    # Check bracket balance
    if code.count('[') != code.count(']'):
        errors.append(f"Unbalanced square brackets: {code.count('[')} '[' vs {code.count(']')} ']'")
        suggestions.append("Ensure every '[' has a matching ']'")

    if code.count('(') != code.count(')'):
        errors.append(f"Unbalanced parentheses: {code.count('(')} '(' vs {code.count(')')} ')'")

    # Check subgraph/end balance
    subgraph_count = len(re.findall(r'\bsubgraph\b', code, re.IGNORECASE))
    end_count = len(re.findall(r'\bend\b', code, re.IGNORECASE))
    if subgraph_count != end_count:
        errors.append(f"Unbalanced subgraph/end: {subgraph_count} subgraph vs {end_count} end")
        suggestions.append("Every 'subgraph' needs a closing 'end'")

    return ValidationResult(
        valid=len(errors) == 0,
        format=DiagramFormat.MERMAID,
        errors=errors,
        code=code,
        suggestions=suggestions
    )


def validate_plantuml(code: str) -> ValidationResult:
    """
    Validate PlantUML diagram code.

    Args:
        code: The PlantUML code to validate

    Returns:
        ValidationResult with validation details
    """
    errors = []
    suggestions = []

    # Check for @startuml/@enduml
    if '@startuml' not in code.lower():
        errors.append("Missing @startuml at the beginning")
        suggestions.append("Start with: @startuml")

    if '@enduml' not in code.lower():
        errors.append("Missing @enduml at the end")
        suggestions.append("End with: @enduml")

    # Check order
    if '@startuml' in code.lower() and '@enduml' in code.lower():
        start_pos = code.lower().find('@startuml')
        end_pos = code.lower().find('@enduml')
        if start_pos > end_pos:
            errors.append("@startuml must come before @enduml")

    return ValidationResult(
        valid=len(errors) == 0,
        format=DiagramFormat.PLANTUML,
        errors=errors,
        code=code,
        suggestions=suggestions
    )


def validate_diagram(code: str, format_hint: str = None) -> ValidationResult:
    """
    Validate diagram code, auto-detecting format if not specified.

    Args:
        code: The diagram code to validate
        format_hint: Optional format hint ("graphviz", "mermaid", "plantuml")

    Returns:
        ValidationResult with validation details
    """
    code = code.strip()

    # Auto-detect format
    if format_hint:
        detected_format = format_hint.lower()
    elif '@startuml' in code.lower():
        detected_format = 'plantuml'
    elif code.lower().startswith(('flowchart', 'graph ', 'sequencediagram')):
        detected_format = 'mermaid'
    elif re.search(r'(di)?graph\s+\w+\s*\{', code, re.IGNORECASE):
        detected_format = 'graphviz'
    else:
        # Default to graphviz
        detected_format = 'graphviz'

    validators = {
        'graphviz': validate_graphviz,
        'plantuml': validate_plantuml,
        'mermaid': validate_mermaid,
    }

    return validators.get(detected_format, validate_graphviz)(code)


# ============== Rendering Tools ==============

def render_graphviz(code: str, output_path: str) -> RenderResult:
    """Render Graphviz DOT code to PNG."""
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.dot', delete=False) as f:
            f.write(code)
            temp_path = f.name

        result = subprocess.run(
            ["dot", "-Tpng", "-Gdpi=150", temp_path, "-o", output_path],
            capture_output=True,
            text=True,
            timeout=30
        )

        os.unlink(temp_path)

        if result.returncode == 0:
            return RenderResult(True, output_path, None, DiagramFormat.GRAPHVIZ)
        else:
            return RenderResult(False, None, result.stderr, DiagramFormat.GRAPHVIZ)

    except Exception as e:
        return RenderResult(False, None, str(e), DiagramFormat.GRAPHVIZ)


def render_mermaid(code: str, output_path: str) -> RenderResult:
    """Render Mermaid code to PNG using web service."""
    try:
        encoded = base64.urlsafe_b64encode(code.encode('utf-8')).decode('utf-8')
        url = f"https://mermaid.ink/img/{encoded}?type=png&bgColor=white"

        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        response = urllib.request.urlopen(req, timeout=30)

        with open(output_path, 'wb') as f:
            f.write(response.read())

        return RenderResult(True, output_path, None, DiagramFormat.MERMAID)

    except Exception as e:
        return RenderResult(False, None, str(e), DiagramFormat.MERMAID)


def render_plantuml(code: str, output_path: str) -> RenderResult:
    """Render PlantUML code to PNG using web service."""
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

            def encode6bit(b):
                if b < 10: return chr(48 + b)
                b -= 10
                if b < 26: return chr(65 + b)
                b -= 26
                if b < 26: return chr(97 + b)
                b -= 26
                return '-' if b == 0 else '_' if b == 1 else '?'

            res += encode6bit(b1 >> 2)
            res += encode6bit(((b1 & 0x3) << 4) | (b2 >> 4))
            res += encode6bit(((b2 & 0xF) << 2) | (b3 >> 6))
            res += encode6bit(b3 & 0x3F)
        return res

    try:
        encoded = encode_plantuml(code)
        url = f"https://www.plantuml.com/plantuml/png/{encoded}"

        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        response = urllib.request.urlopen(req, timeout=30)

        with open(output_path, 'wb') as f:
            f.write(response.read())

        return RenderResult(True, output_path, None, DiagramFormat.PLANTUML)

    except Exception as e:
        return RenderResult(False, None, str(e), DiagramFormat.PLANTUML)


def render_diagram(code: str, output_path: str, format_type: DiagramFormat = None) -> RenderResult:
    """
    Render diagram code to PNG.

    Args:
        code: The diagram code
        output_path: Path for output PNG
        format_type: The diagram format (auto-detected if None)

    Returns:
        RenderResult with rendering details
    """
    if format_type is None:
        validation = validate_diagram(code)
        format_type = validation.format

    renderers = {
        DiagramFormat.GRAPHVIZ: render_graphviz,
        DiagramFormat.PLANTUML: render_plantuml,
        DiagramFormat.MERMAID: render_mermaid,
    }

    return renderers[format_type](code, output_path)


# ============== Code Extraction Tools ==============

def extract_code_from_response(text: str, format_type: str = None) -> Optional[str]:
    """
    Extract diagram code from LLM response text.

    Args:
        text: The LLM response text
        format_type: Expected format ("graphviz", "mermaid", "plantuml")

    Returns:
        Extracted code or None
    """
    # Remove markdown code blocks
    patterns = [
        # Specific language blocks
        r'```(?:dot|graphviz)\s*\n(.*?)\n```',
        r'```(?:mermaid)\s*\n(.*?)\n```',
        r'```(?:plantuml|puml)\s*\n(.*?)\n```',
        # Generic blocks with graph content
        r'```\s*\n((?:di)?graph\s+\w+\s*\{.*?\})\s*```',
        r'```\s*\n(flowchart\s+\w+.*?)\n```',
        r'```\s*\n(@startuml.*?@enduml)\s*```',
    ]

    for pattern in patterns:
        matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
        if matches:
            return matches[0].strip()

    # Fallback: look for raw diagram code
    if format_type == 'graphviz' or re.search(r'(di)?graph\s+\w+\s*\{', text, re.IGNORECASE):
        match = re.search(r'((?:di)?graph\s+\w+\s*\{[\s\S]*\})', text, re.IGNORECASE)
        if match:
            return match.group(1).strip()

    if format_type == 'mermaid' or text.strip().lower().startswith(('flowchart', 'graph ')):
        # Return the whole text if it looks like mermaid
        cleaned = text.strip()
        cleaned = re.sub(r'^```\w*\s*\n?', '', cleaned)
        cleaned = re.sub(r'\n?```\s*$', '', cleaned)
        return cleaned if cleaned else None

    if format_type == 'plantuml' or '@startuml' in text.lower():
        match = re.search(r'(@startuml[\s\S]*?@enduml)', text, re.IGNORECASE)
        if match:
            return match.group(1).strip()

    return None
