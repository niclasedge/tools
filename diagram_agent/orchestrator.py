"""
Diagram Agent Orchestrator

Coordinates the multi-agent pipeline for diagram generation.
Supports: Analysis → Generation → Validation → Improvement (if needed) → Rendering
"""

import asyncio
import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime

try:
    from .agents import (
        AgentRegistry,
        get_ollama_model,
        create_analyzer_agent,
        create_generator_agent,
        create_validator_agent,
        create_improver_agent,
    )
    from .tools import (
        validate_diagram,
        render_diagram,
        extract_code_from_response,
        ValidationResult,
        RenderResult,
        DiagramFormat
    )
except ImportError:
    from agents import (
        AgentRegistry,
        get_ollama_model,
        create_analyzer_agent,
        create_generator_agent,
        create_validator_agent,
        create_improver_agent,
    )
    from tools import (
        validate_diagram,
        render_diagram,
        extract_code_from_response,
        ValidationResult,
        RenderResult,
        DiagramFormat
    )


@dataclass
class PipelineResult:
    """Result of the diagram generation pipeline."""
    success: bool
    diagram_code: Optional[str]
    format: Optional[DiagramFormat]
    output_path: Optional[str]
    validation_result: Optional[ValidationResult]

    # Pipeline metadata
    analysis: Optional[str] = None
    iterations: int = 0
    errors: List[str] = field(default_factory=list)
    duration_seconds: float = 0.0

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "diagram_code": self.diagram_code,
            "format": self.format.value if self.format else None,
            "output_path": self.output_path,
            "validation": {
                "valid": self.validation_result.valid if self.validation_result else None,
                "errors": self.validation_result.errors if self.validation_result else [],
            },
            "analysis": self.analysis,
            "iterations": self.iterations,
            "errors": self.errors,
            "duration_seconds": self.duration_seconds
        }


class DiagramOrchestrator:
    """
    Orchestrates the diagram generation pipeline.

    Pipeline Steps:
    1. Analyze: Understand the input and determine diagram type
    2. Generate: Create diagram code
    3. Validate: Check syntax
    4. Improve: Fix errors if validation fails (up to max_iterations)
    5. Render: Create PNG output
    """

    def __init__(
        self,
        model_name: str = "gemma3:4b",
        output_dir: str = "./diagram_output",
        max_improvement_iterations: int = 3,
        skip_analysis: bool = False,
        preferred_format: str = "graphviz"
    ):
        """
        Initialize the orchestrator.

        Args:
            model_name: Ollama model to use
            output_dir: Directory for output files
            max_improvement_iterations: Max attempts to fix invalid code
            skip_analysis: Skip analysis step for faster generation
            preferred_format: Default diagram format
        """
        self.model_name = model_name
        self.output_dir = Path(output_dir)
        self.max_iterations = max_improvement_iterations
        self.skip_analysis = skip_analysis
        self.preferred_format = preferred_format

        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize agent registry
        self.registry = AgentRegistry(default_model=model_name)

        # Pipeline state
        self._current_code = None
        self._current_format = None

    async def _run_agent(self, agent_name: str, prompt: str) -> str:
        """
        Run a single agent with a prompt.

        Args:
            agent_name: Name of the agent to run
            prompt: Input prompt for the agent

        Returns:
            Agent response text
        """
        agent = self.registry.get(agent_name)

        # Use ADK's async interface
        from google.adk.runners import Runner

        runner = Runner(agent=agent, app_name="diagram_agent")

        # Create a simple session and run
        response_parts = []
        async for event in runner.run_async(user_id="user", session_id="session", new_message=prompt):
            if hasattr(event, 'content') and event.content:
                if hasattr(event.content, 'parts'):
                    for part in event.content.parts:
                        if hasattr(part, 'text') and part.text:
                            response_parts.append(part.text)

        return "\n".join(response_parts)

    def _run_agent_sync(self, agent_name: str, prompt: str) -> str:
        """
        Synchronous wrapper for running an agent.
        Uses direct LLM call for simplicity.
        """
        import litellm

        agent = self.registry.get(agent_name)

        # Direct LiteLLM call
        response = litellm.completion(
            model=f"ollama_chat/{self.model_name}",
            messages=[
                {"role": "system", "content": agent.instruction},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )

        return response.choices[0].message.content

    def analyze(self, description: str) -> str:
        """
        Analyze the input description.

        Args:
            description: Text description of desired diagram

        Returns:
            Analysis result
        """
        if self.skip_analysis:
            return f"FORMAT: {self.preferred_format}\nSkipped detailed analysis."

        prompt = f"""Analyze this diagram request and provide a structured analysis:

{description}

Output your analysis in the structured format specified in your instructions."""

        return self._run_agent_sync("analyzer", prompt)

    def generate(self, description: str, format_type: str = None, analysis: str = None) -> str:
        """
        Generate diagram code.

        Args:
            description: Text description
            format_type: Desired format (graphviz, mermaid, plantuml)
            analysis: Optional analysis from analyzer agent

        Returns:
            Generated diagram code
        """
        format_type = format_type or self.preferred_format

        prompt = f"""Generate a {format_type.upper()} diagram for:

{description}

{"Analysis context: " + analysis if analysis else ""}

Remember: Output ONLY the diagram code, starting with 'digraph' for graphviz or 'flowchart' for mermaid.
NO explanations, NO markdown code blocks, just the raw code."""

        response = self._run_agent_sync("generator", prompt)

        # Extract code from response
        code = extract_code_from_response(response, format_type)
        return code or response

    def validate(self, code: str) -> ValidationResult:
        """
        Validate diagram code.

        Args:
            code: Diagram code to validate

        Returns:
            ValidationResult
        """
        return validate_diagram(code)

    def improve(self, code: str, errors: List[str], suggestions: List[str]) -> str:
        """
        Improve/fix invalid diagram code.

        Args:
            code: Invalid code
            errors: List of errors
            suggestions: Fix suggestions

        Returns:
            Fixed code
        """
        prompt = f"""Fix this invalid diagram code:

```
{code}
```

ERRORS:
{chr(10).join(f"- {e}" for e in errors)}

SUGGESTIONS:
{chr(10).join(f"- {s}" for s in suggestions)}

Return ONLY the fixed code, no explanations."""

        response = self._run_agent_sync("improver", prompt)

        # Extract code from response
        code = extract_code_from_response(response)
        return code or response

    def render(self, code: str, filename: str = None) -> RenderResult:
        """
        Render diagram code to PNG.

        Args:
            code: Valid diagram code
            filename: Output filename (auto-generated if None)

        Returns:
            RenderResult
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"diagram_{timestamp}.png"

        output_path = str(self.output_dir / filename)
        return render_diagram(code, output_path)

    def run(self, description: str, output_filename: str = None) -> PipelineResult:
        """
        Run the complete diagram generation pipeline.

        Args:
            description: Text description of desired diagram
            output_filename: Optional output filename

        Returns:
            PipelineResult with all details
        """
        import time
        start_time = time.time()

        errors = []
        iterations = 0

        # Step 1: Analyze
        print(f"[1/4] Analyzing description...")
        try:
            analysis = self.analyze(description)
            print(f"      Analysis complete")
        except Exception as e:
            analysis = None
            errors.append(f"Analysis failed: {e}")
            print(f"      Analysis skipped: {e}")

        # Determine format from analysis
        format_type = self.preferred_format
        if analysis and "FORMAT:" in analysis:
            for fmt in ["graphviz", "mermaid", "plantuml"]:
                if fmt in analysis.lower():
                    format_type = fmt
                    break

        # Step 2: Generate
        print(f"[2/4] Generating {format_type} diagram...")
        try:
            code = self.generate(description, format_type, analysis)
            print(f"      Generated {len(code)} chars of code")
        except Exception as e:
            return PipelineResult(
                success=False,
                diagram_code=None,
                format=None,
                output_path=None,
                validation_result=None,
                analysis=analysis,
                iterations=0,
                errors=[f"Generation failed: {e}"],
                duration_seconds=time.time() - start_time
            )

        # Step 3 & 4: Validate and Improve loop
        print(f"[3/4] Validating...")
        validation = self.validate(code)

        while not validation.valid and iterations < self.max_iterations:
            iterations += 1
            print(f"      Invalid! Improving (attempt {iterations}/{self.max_iterations})...")

            code = self.improve(code, validation.errors, validation.suggestions)
            validation = self.validate(code)

            if validation.valid:
                print(f"      Fixed after {iterations} iteration(s)")
            else:
                print(f"      Still invalid: {validation.errors[0][:50]}...")

        if not validation.valid:
            errors.extend(validation.errors)
            print(f"      Could not fix after {self.max_iterations} attempts")

        # Step 5: Render
        output_path = None
        if validation.valid:
            print(f"[4/4] Rendering to PNG...")
            render_result = self.render(code, output_filename)

            if render_result.success:
                output_path = render_result.output_path
                print(f"      Saved: {output_path}")
            else:
                errors.append(f"Render failed: {render_result.error}")
                print(f"      Render failed: {render_result.error}")
        else:
            print(f"[4/4] Skipping render (invalid code)")

        duration = time.time() - start_time

        return PipelineResult(
            success=validation.valid and output_path is not None,
            diagram_code=code,
            format=validation.format,
            output_path=output_path,
            validation_result=validation,
            analysis=analysis,
            iterations=iterations,
            errors=errors,
            duration_seconds=duration
        )


# ============== Convenience Functions ==============

def create_diagram(
    description: str,
    model: str = "gemma3:4b",
    format_type: str = "graphviz",
    output_dir: str = "./diagram_output",
    output_filename: str = None
) -> PipelineResult:
    """
    Convenience function to create a diagram from a description.

    Args:
        description: Text description of the diagram
        model: Ollama model name
        format_type: Diagram format (graphviz, mermaid, plantuml)
        output_dir: Output directory
        output_filename: Optional output filename

    Returns:
        PipelineResult
    """
    orchestrator = DiagramOrchestrator(
        model_name=model,
        output_dir=output_dir,
        preferred_format=format_type,
        skip_analysis=True  # Skip for faster generation
    )

    return orchestrator.run(description, output_filename)


def quick_diagram(description: str, format_type: str = "graphviz") -> str:
    """
    Quick diagram generation without the full pipeline.
    Returns the diagram code directly.

    Args:
        description: Text description
        format_type: Diagram format

    Returns:
        Diagram code string
    """
    import litellm

    QUICK_PROMPT = f"""Generate valid {format_type.upper()} diagram code for:

{description}

RULES:
- For graphviz: Start with 'digraph Name {{', use alphanumeric node names only
- For mermaid: Start with 'flowchart LR' or 'flowchart TD'
- Output ONLY the code, no explanations

CODE:"""

    response = litellm.completion(
        model="ollama_chat/gemma3:4b",
        messages=[{"role": "user", "content": QUICK_PROMPT}],
        temperature=0.3
    )

    code = response.choices[0].message.content
    extracted = extract_code_from_response(code, format_type)
    return extracted or code
