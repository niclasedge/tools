# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## About

**Tools** is a collection of utility tools, scripts, and AI agents for development workflows. Inspired by [Simon Willison's tools repository](https://github.com/simonw/tools), this project provides Python scripts, HTML utilities, and advanced agent frameworks for diagram generation, benchmarking, and workflow automation.

**Technology Stack:** Python, TypeScript/Node.js, HTML/CSS/JavaScript, Vercel AI SDK, Ollama, OpenAI/Anthropic APIs

## [Unreleased]

### Status
- Repository in active development with experimental lifecycle
- Core functionality: Working and stable
- Agent frameworks: Fully operational
- Documentation: Complete with TechDocs integration

## [2026-01-08] - Latest Release

### Added
- Backstage integration with catalog-info.yaml configuration
- TechDocs documentation system with MkDocs
- Documentation index page with comprehensive overview
- Repository metadata and component annotations

### Changed
- Updated owner annotation to `user:niclasedge` in catalog-info.yaml
- Enhanced documentation structure with centralized index

### Fixed
- Corrected owner annotation format for Backstage compatibility

## [2026-01-04] - Agent Framework & Graphviz Tools

### Added
- **Graphviz Visualization Tool** with Ollama model testing
  - Interactive diagram generation using dot notation
  - Mindmap generation capabilities
  - Multi-model testing support (Ollama integration)
  - Comprehensive README documentation
- **agents-vercel-sdk** - Multi-agent diagram generation framework
  - Vercel AI SDK integration (v4.3.0)
  - Support for OpenAI, Anthropic, and Ollama providers
  - CLI interface for diagram generation
  - Web server with Hono framework
  - Benchmark testing capabilities
  - TypeScript-based implementation

### Merged
- Pull request #1: Graphviz visualization tool implementation

## [2025-04-04] - Color Analysis & Image Processing

### Added
- **Image Color Analysis Feature** to color-wheel.html
  - Load and display images from images.json
  - Grid display of first 12 images with thumbnails
  - Image selection for detailed analysis
  - Color extraction algorithm identifying 10 dominant colors
  - RGB composition display with percentage bars
  - Value percentage calculations for color brightness
- **Image Carousel Navigation**
  - Previous/next buttons for image navigation
  - Pagination display showing current position
  - Dynamic loading of images in batches of 12
  - Random image selection for variety
- **Enhanced Color Visualization**
  - Numbered indicators replacing line connections
  - Horizontal color card layout
  - Full-width responsive layout (1400px)
  - Optimized space utilization

### Changed
- Split functionality into separate HTML files:
  - `color-wheel.html` - Color wheel and mixing only
  - `image-analysis.html` - Dedicated image color analysis
- Updated page title to "Image Color Analysis"
- Increased displayed colors from 5 to 10 in analysis
- Improved layout with image on left, color cards on right
- Minimized vertical padding for compact display
- Changed from sequential to random image display
- Removed sqlite3 from requirements.txt

### Fixed
- RGB percentage calculation to ensure 100% total
- Inverted value percentage for proper darkness representation
- Black color handling to avoid division by zero
- Standardized color card sizes for consistency
- Color palette layout displaying exactly 5 colors per row
- Value bar percentage label alignment
- Image loading to correctly parse images.json structure
- RGB composition display accuracy
- Image grid thumbnail display in containers

### Removed
- Image color analysis functionality from color-wheel.html
- Unnecessary HTML markup, CSS styles, and JavaScript
- Raw RGB values for cleaner interface

## [2025-04-02] - Initial Tools Collection

### Added
- **Base64 Encoder/Decoder Tool** (base64-encoder.html)
  - Browser-based encoding/decoding utility
  - Client-side processing for security
- **Interactive Color Wheel** (color-wheel.html)
  - Color selection and palette generation
  - Color mixing capabilities
- **Reverse Color Picker**
  - Color identification from hex/RGB values
- **Build System**
  - build_index.py (formerly build_colophon.py)
  - Automated tool indexing and organization
- **Database Utilities**
  - db_to_json.py for database export
  - history.db SQLite database
- **Link Management**
  - gather_links.py for link organization
- **Development Tools**
  - gather_links.py
  - images.json data storage

### Changed
- Renamed build_colophon.py to build_index.py for clarity
- Updated repository URLs to niclasedge fork
- Renamed workflow file extension to .yml

### Fixed
- String issues in initialization
- Missing newline at end of files

## Project Structure

### Core Components

#### Agent Frameworks
- **agents-vercel-sdk/** - Vercel AI SDK integration with multi-provider support
- **diagram_agent/** - Specialized diagram generation agent with orchestration
- **health-agent/** - Health check and monitoring agent system
- **agent_hub/** - Central hub for agent management and deployment

#### Python Scripts
- **graphviz_tool.py** - Graphviz diagram generation with AI
- **diagram_benchmark.py** - Performance testing for diagram generation
- **dataflow_comparison.py** - Framework dataflow pattern comparison
- **build_index.py** - Tool collection indexing
- **db_to_json.py** - Database conversion utility
- **gather_links.py** - Link aggregation tool

#### Web Utilities
- **base64-encoder.html** - Base64 encoding/decoding
- **color-wheel.html** - Interactive color tools
- **image-analysis.html** - Color extraction from images

#### Data & Configuration
- **history.db** - SQLite database for tool history
- **images.json** - Image data storage
- **requirements.txt** - Python dependencies (requests)
- **catalog-info.yaml** - Backstage component configuration
- **mkdocs.yml** - Documentation configuration

#### Documentation
- **docs/index.md** - Main documentation index
- **docs/PERFORMANCE_REPORT.md** - Performance analysis
- **docs/dotviz-generator-README.md** - Graphviz tool guide
- **docs/agent_framework_comparison.md** - Framework comparison

### Benchmarking Results
- **benchmark_google_adk.json** - Google ADK performance data
- **benchmark_vercel_sdk.json** - Vercel SDK performance data
- **diagram_benchmark/** - Diagram generation benchmarks
- **diagram_output/** - Generated diagram outputs

## Known Issues

### In Progress
- Agent orchestration refinement
- Additional model provider integrations
- Extended benchmark coverage

### Future Enhancements
- Web UI for agent management
- Additional visualization tools
- Enhanced benchmarking dashboard
- More comprehensive test coverage

## Dependencies

### Python
- requests
- Additional dependencies per agent framework

### Node.js (agents-vercel-sdk)
- ai (Vercel AI SDK) ^4.3.0
- @ai-sdk/openai ^1.3.0
- @ai-sdk/anthropic ^1.2.0
- ollama-ai-provider ^1.2.0
- zod ^3.24.0
- hono ^4.7.0
- commander ^13.1.0
- chalk ^5.4.1
- dotenv ^16.5.0

## Installation

### Python Tools
```bash
pip install -r requirements.txt
```

### Vercel SDK Agents
```bash
cd agents-vercel-sdk
npm install
```

## Usage

### Python Scripts
```bash
# Graphviz tool
python graphviz_tool.py

# Database conversion
python db_to_json.py

# Diagram benchmarking
python diagram_benchmark.py
```

### Agent Frameworks
```bash
# Vercel SDK agents
cd agents-vercel-sdk
npm run dev          # Development mode
npm run test         # Run benchmarks
npm run web          # Start web server
```

### Web Tools
Open HTML files directly in a modern web browser:
- base64-encoder.html
- color-wheel.html
- image-analysis.html

## Development Setup

### Prerequisites
- Python 3.8+
- Node.js 20.0.0+
- Modern web browser
- Git

### Quick Start
```bash
# Clone repository
git clone https://github.com/niclasedge/tools.git
cd tools

# Install Python dependencies
pip install -r requirements.txt

# Set up Vercel SDK agents
cd agents-vercel-sdk
npm install
npm run dev
```

## Tags
`python` `typescript` `utilities` `agents` `automation` `development-tools` `diagrams` `benchmarking` `ai` `ollama` `vercel-sdk`

## Owner
niclasedge

## Lifecycle
Experimental - Active development with frequent updates

---

For more information, see the [full documentation](https://github.com/niclasedge/tools).
