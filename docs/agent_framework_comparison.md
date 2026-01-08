# Agent Framework Vergleich 2025

## Übersicht

| Framework | Anbieter | Sprachen | Multi-Agent | MCP Support | Produktion |
|-----------|----------|----------|-------------|-------------|------------|
| **LangGraph** | LangChain | Python, JS | ✓ Hierarchisch | ✓ | ✓ LinkedIn, Uber |
| **Google ADK** | Google | Python, TS, Go | ✓ Sequential/Parallel/Loop | ✓ | ✓ Vertex AI |
| **CrewAI** | Community | Python | ✓ Rollen-basiert | ✓ | ✓ Fortune 500 |
| **AutoGen** | Microsoft | Python | ✓ Konversations-basiert | ✓ | ✓ |
| **Pydantic AI** | Pydantic | Python | ○ Delegation | ✓ | ✓ |
| **OpenAI Agents** | OpenAI | Python | ✓ Handoffs | ○ | ✓ |
| **Claude Agent SDK** | Anthropic | Python, TS | ○ | ✓ | ✓ |

---

## 1. LangGraph

### Vorteile
- ✅ **Graph-basierte Architektur**: Präzise Kontrolle über Verzweigungen und Fehlerbehandlung
- ✅ **Robustes Checkpointing**: Pause, Resume, Rewind von Workflows
- ✅ **Reife**: Erste stable V1.0 (Oktober 2025), 4.2M Downloads/Monat
- ✅ **Produktions-erprobt**: LinkedIn, Uber, 400+ Unternehmen
- ✅ **Flexibles Memory**: In-thread + Cross-thread Memory

### Nachteile
- ❌ **Steile Lernkurve**: Viele Abstraktionsebenen
- ❌ **Overhead**: Für einfache Tasks zu komplex
- ❌ **LangChain-Abhängigkeit**: Teil des LangChain-Ökosystems

### Best für
- Komplexe, multi-step Workflows
- Produktions-kritische Anwendungen
- Teams mit LangChain-Erfahrung

---

## 2. Google ADK (Agent Development Kit)

### Vorteile
- ✅ **Modell-agnostisch**: Gemini, Vertex AI, LiteLLM (100+ Modelle)
- ✅ **Multi-Agent Workflow Agents**: SequentialAgent, ParallelAgent, LoopAgent
- ✅ **Rich Tool Ecosystem**: MCP, LangChain, LlamaIndex Integration
- ✅ **Bidirektionales Streaming**: Audio/Video in Echtzeit
- ✅ **Multi-Language**: Python, TypeScript, Go
- ✅ **Vertex AI Integration**: Managed Deployment

### Nachteile
- ❌ **Neu**: Erst April 2025 released, weniger Community-Support
- ❌ **Google-optimiert**: Beste Experience mit Google Cloud
- ❌ **Dokumentation**: Noch im Aufbau

### Best für
- Multi-Agent Systeme
- Google Cloud Umgebungen
- Projekte die Modell-Flexibilität brauchen

---

## 3. CrewAI

### Vorteile
- ✅ **Einfache Rollen-Definition**: Researcher, Developer, Writer etc.
- ✅ **Built-in Memory**: ChromaDB (short-term), SQLite (long-term)
- ✅ **Große Community**: 30k+ GitHub Stars
- ✅ **Parallel Execution**: Task-Parallelisierung
- ✅ **Unabhängig**: Keine LangChain-Abhängigkeit

### Nachteile
- ❌ **Weniger Kontrolle**: Abstrahiert viel weg
- ❌ **Debugging**: Schwieriger bei komplexen Flows
- ❌ **Vendor Lock-in Risiko**: $18M Funding, kommerzielle Ausrichtung

### Best für
- Multi-Agent Kollaboration
- Content-Erstellung Pipelines
- Teams ohne tiefes AI-Wissen

---

## 4. Microsoft AutoGen

### Vorteile
- ✅ **Asynchron**: Nicht-blockierende Agent-Kommunikation
- ✅ **Konversations-basiert**: Natürliche Multi-Agent Interaktion
- ✅ **Microsoft Integration**: Azure, Semantic Kernel Merge
- ✅ **Event-driven**: Gut für lange Tasks mit externen Events
- ✅ **Große Community**: 40k+ GitHub Stars

### Nachteile
- ❌ **Kein Built-in Persistent Memory**: Nur context_variables
- ❌ **Microsoft-zentriert**: Beste Experience im MS-Ökosystem
- ❌ **Komplexität**: Kann für einfache Tasks überdimensioniert sein

### Best für
- Konversations-basierte Agents
- Azure/Microsoft Umgebungen
- Lange, asynchrone Tasks

---

## 5. Pydantic AI

### Vorteile
- ✅ **Type-Safety**: Volle IDE-Unterstützung, Auto-Completion
- ✅ **Dependency Injection**: Wie FastAPI für Agents
- ✅ **Structured Output**: Validierte JSON-Ausgaben
- ✅ **A2A Protocol**: Agent-to-Agent Kommunikation
- ✅ **Human-in-the-Loop**: Built-in Approval Workflows
- ✅ **Lightweight**: Minimale Dependencies

### Nachteile
- ❌ **Neu**: V1 erst September 2025
- ❌ **Weniger Multi-Agent**: Fokus auf Single-Agent Tasks
- ❌ **Kleinere Community**: Noch im Wachstum

### Best für
- Structured Output Tasks (z.B. Code-Generierung)
- Type-safe Anwendungen
- Schnelle Prototypen mit Validierung

---

## 6. OpenAI Agents SDK

### Vorteile
- ✅ **Einfach**: Minimale Primitives (Agents, Handoffs, Guardrails)
- ✅ **Built-in Tracing**: Visualisierung und Debugging
- ✅ **Provider-agnostisch**: 100+ LLMs via Chat Completions API
- ✅ **Sessions**: Automatische History-Verwaltung
- ✅ **Produktion-ready**: Ersetzt experimentelles Swarm

### Nachteile
- ❌ **OpenAI-optimiert**: Beste Experience mit OpenAI Modellen
- ❌ **Weniger Kontrolle**: Abstrahiert viel für Einfachheit
- ❌ **Begrenzte Workflows**: Nicht für komplexe Graph-Flows

### Best für
- Rapid Prototyping
- OpenAI-basierte Projekte
- Einfache Agent-Anwendungen

---

## 7. Claude Agent SDK

### Vorteile
- ✅ **Computer Use**: Agents können wie Menschen arbeiten
- ✅ **Code-fokussiert**: Excellent für Development Tasks
- ✅ **Claude Integration**: Beste Claude-Performance
- ✅ **Multi-Platform Auth**: Bedrock, Vertex AI

### Nachteile
- ❌ **Claude-abhängig**: Nur mit Claude Modellen
- ❌ **Weniger Multi-Agent**: Fokus auf einzelne Agents
- ❌ **Neu**: Dokumentation noch im Aufbau

### Best für
- Code-Generierung und Editing
- Development Automation
- Claude-basierte Projekte

---

## Empfehlungsmatrix

| Use Case | Empfehlung | Alternative |
|----------|------------|-------------|
| **Komplexe Workflows** | LangGraph | Google ADK |
| **Multi-Agent Kollaboration** | CrewAI | Google ADK |
| **Structured Output** | Pydantic AI | LangGraph |
| **Rapid Prototyping** | OpenAI Agents | Pydantic AI |
| **Code Generation** | Claude Agent SDK | Pydantic AI |
| **Google Cloud** | Google ADK | LangGraph |
| **Microsoft/Azure** | AutoGen | LangGraph |
| **Type-Safety** | Pydantic AI | - |

---

## Für Diagram-Agent Empfehlung

Für einen **Diagram-Agent** (Graphviz/PlantUML/Mermaid Generierung) empfehle ich:

### 1. Wahl: **Pydantic AI**
- ✅ Perfekt für Structured Output (Diagram Code)
- ✅ Type-safe Validierung des generierten Codes
- ✅ Einfache Tool-Integration
- ✅ Funktioniert mit Ollama (lokal)

### 2. Wahl: **Google ADK**
- ✅ Multi-Agent für verschiedene Diagram-Formate
- ✅ Modell-agnostisch
- ✅ SequentialAgent für Pipeline (Analyse → Generierung → Validierung)

---

## Quellen

- [Turing: AI Agent Frameworks Comparison](https://www.turing.com/resources/ai-agent-frameworks)
- [Langfuse: Open-Source AI Agent Comparison](https://langfuse.com/blog/2025-03-19-ai-agent-comparison)
- [Google ADK Documentation](https://google.github.io/adk-docs/)
- [Pydantic AI](https://ai.pydantic.dev/)
- [ZenML: Pydantic AI vs LangGraph](https://www.zenml.io/blog/pydantic-ai-vs-langgraph)
- [OpenAI Agents SDK](https://openai.github.io/openai-agents-python/)
- [Claude Agent SDK](https://platform.claude.com/docs/en/agent-sdk/overview)
