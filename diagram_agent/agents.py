"""
Diagram Agent Definitions

Multi-agent system for diagram generation using Google ADK.
Each agent has a specific role in the pipeline.
"""

from google.adk.agents import LlmAgent, SequentialAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools import FunctionTool
from typing import Optional
import json

try:
    from .tools import (
        validate_diagram,
        render_diagram,
        extract_code_from_response,
        ValidationResult,
        RenderResult,
        DiagramFormat
    )
except ImportError:
    from tools import (
        validate_diagram,
        render_diagram,
        extract_code_from_response,
        ValidationResult,
        RenderResult,
        DiagramFormat
    )


# ============== Model Configuration ==============

def get_ollama_model(model_name: str = "gemma3:4b") -> LiteLlm:
    """
    Get an Ollama model via LiteLLM.

    Args:
        model_name: Ollama model name (e.g., "gemma3:4b", "qwen2.5-coder:7b")

    Returns:
        LiteLlm model instance
    """
    # Use ollama_chat prefix to avoid tool call loops
    return LiteLlm(model=f"ollama_chat/{model_name}")


# ============== Tool Functions ==============

def validate_diagram_tool(code: str, format_hint: str = None) -> str:
    """
    Validate diagram code and return validation result.

    Args:
        code: The diagram code to validate
        format_hint: Optional format hint (graphviz, mermaid, plantuml)

    Returns:
        JSON string with validation result
    """
    result = validate_diagram(code, format_hint)
    return json.dumps({
        "valid": result.valid,
        "format": result.format.value,
        "errors": result.errors,
        "suggestions": result.suggestions
    }, indent=2)


def render_diagram_tool(code: str, output_path: str, format_type: str = None) -> str:
    """
    Render diagram code to PNG file.

    Args:
        code: The diagram code to render
        output_path: Path for output PNG file
        format_type: Diagram format (graphviz, mermaid, plantuml)

    Returns:
        JSON string with render result
    """
    fmt = DiagramFormat(format_type) if format_type else None
    result = render_diagram(code, output_path, fmt)
    return json.dumps({
        "success": result.success,
        "output_path": result.output_path,
        "error": result.error,
        "format": result.format.value
    }, indent=2)


def extract_code_tool(response_text: str, expected_format: str = None) -> str:
    """
    Extract diagram code from LLM response.

    Args:
        response_text: The LLM response containing diagram code
        expected_format: Expected format (graphviz, mermaid, plantuml)

    Returns:
        Extracted code or error message
    """
    code = extract_code_from_response(response_text, expected_format)
    if code:
        return code
    return "ERROR: Could not extract diagram code from response"


# ============== Agent Definitions ==============

# Prompts for each agent role
ANALYZER_INSTRUCTION = """You are a Diagram Analyzer Agent. Your job is to analyze text descriptions and determine:

1. What type of diagram would best represent the information (flowchart, architecture, sequence, etc.)
2. What format to use (graphviz for complex flows, mermaid for simple diagrams)
3. Key elements and relationships to include

When analyzing, output a structured analysis:
- DIAGRAM_TYPE: [flowchart/architecture/sequence/mindmap/etc]
- FORMAT: [graphviz/mermaid/plantuml]
- ELEMENTS: List of nodes/components
- RELATIONSHIPS: List of connections between elements
- STYLE_NOTES: Any styling recommendations

Be concise and structured in your analysis."""


GENERATOR_INSTRUCTION = """You are a Diagram Generator Agent. You create valid diagram code from descriptions.

CRITICAL RULES FOR GRAPHVIZ:
1. Start with: digraph DiagramName {
2. Node names MUST be alphanumeric with underscores only (no dots, no special chars)
3. Use: env_file NOT .env, config_yaml NOT config.yaml
4. Labels can have special chars in quotes: [label="config.yaml"]
5. End with a closing }

CRITICAL RULES FOR MERMAID:
1. Start with: flowchart LR or flowchart TD
2. Use subgraph Name ... end for grouping
3. Node syntax: ID["Label"] or ID[("Cylinder")]
4. Every subgraph needs a closing 'end'

OUTPUT FORMAT:
Return ONLY the diagram code, no explanations. Start directly with the code.
For graphviz: Start with 'digraph'
For mermaid: Start with 'flowchart'

Use appropriate shapes:
- cylinder for databases
- folder for file outputs
- diamond for decisions
- box for processes
- ellipse for start/end"""


VALIDATOR_INSTRUCTION = """You are a Diagram Validator Agent. Your job is to check diagram code for errors.

Use the validate_diagram_tool to check the code syntax.

After validation:
1. If VALID: Report success and the format detected
2. If INVALID: List all errors and suggest specific fixes

Be precise about what line or element has the error."""


IMPROVER_INSTRUCTION = """You are a Diagram Improver Agent. Your job is to fix invalid diagram code.

When given invalid code with errors:
1. Analyze each error carefully
2. Apply the specific fix needed
3. Return the COMPLETE fixed code

COMMON FIXES:
- Node names with dots (.env) → Use underscores (env_file)
- Missing closing braces → Add }
- Port syntax errors → Remove or fix port references
- Unbalanced subgraph/end → Add missing 'end' statements

OUTPUT: Return ONLY the fixed code, no explanations."""


def create_analyzer_agent(model: LiteLlm = None) -> LlmAgent:
    """Create the Analyzer Agent."""
    if model is None:
        model = get_ollama_model()

    return LlmAgent(
        name="analyzer",
        model=model,
        instruction=ANALYZER_INSTRUCTION,
        description="Analyzes text to determine diagram type and structure"
    )


def create_generator_agent(model: LiteLlm = None) -> LlmAgent:
    """Create the Generator Agent."""
    if model is None:
        model = get_ollama_model()

    return LlmAgent(
        name="generator",
        model=model,
        instruction=GENERATOR_INSTRUCTION,
        description="Generates diagram code from descriptions"
    )


def create_validator_agent(model: LiteLlm = None) -> LlmAgent:
    """Create the Validator Agent with validation tools."""
    if model is None:
        model = get_ollama_model()

    return LlmAgent(
        name="validator",
        model=model,
        instruction=VALIDATOR_INSTRUCTION,
        description="Validates diagram code syntax",
        tools=[
            FunctionTool(validate_diagram_tool)
        ]
    )


def create_improver_agent(model: LiteLlm = None) -> LlmAgent:
    """Create the Improver Agent for fixing invalid code."""
    if model is None:
        model = get_ollama_model()

    return LlmAgent(
        name="improver",
        model=model,
        instruction=IMPROVER_INSTRUCTION,
        description="Fixes invalid diagram code"
    )


def create_renderer_agent(model: LiteLlm = None) -> LlmAgent:
    """Create the Renderer Agent with rendering tools."""
    if model is None:
        model = get_ollama_model()

    return LlmAgent(
        name="renderer",
        model=model,
        instruction="You render diagrams to PNG files. Use the render_diagram_tool.",
        description="Renders diagram code to image files",
        tools=[
            FunctionTool(render_diagram_tool)
        ]
    )


# ============== Agent Registry ==============

class AgentRegistry:
    """
    Registry for managing available agents.
    Makes it easy to add new agents to the system.
    """

    def __init__(self, default_model: str = "gemma3:4b"):
        self.default_model = default_model
        self._agents = {}
        self._model = get_ollama_model(default_model)

        # Register built-in agents
        self._register_builtin_agents()

    def _register_builtin_agents(self):
        """Register the built-in diagram agents."""
        self.register("analyzer", create_analyzer_agent)
        self.register("generator", create_generator_agent)
        self.register("validator", create_validator_agent)
        self.register("improver", create_improver_agent)
        self.register("renderer", create_renderer_agent)

    def register(self, name: str, factory_fn):
        """
        Register a new agent factory.

        Args:
            name: Agent name/identifier
            factory_fn: Function that creates the agent (takes model as param)
        """
        self._agents[name] = factory_fn

    def get(self, name: str) -> LlmAgent:
        """
        Get an agent instance by name.

        Args:
            name: Agent name

        Returns:
            LlmAgent instance
        """
        if name not in self._agents:
            raise ValueError(f"Unknown agent: {name}. Available: {list(self._agents.keys())}")

        return self._agents[name](self._model)

    def list_agents(self) -> list:
        """List all registered agent names."""
        return list(self._agents.keys())

    def create_custom_agent(
        self,
        name: str,
        instruction: str,
        description: str,
        tools: list = None
    ) -> LlmAgent:
        """
        Create and register a custom agent.

        Args:
            name: Agent name
            instruction: System instruction for the agent
            description: Agent description
            tools: Optional list of tools

        Returns:
            The created LlmAgent
        """
        def factory(model):
            return LlmAgent(
                name=name,
                model=model,
                instruction=instruction,
                description=description,
                tools=tools or []
            )

        self.register(name, factory)
        return self.get(name)
