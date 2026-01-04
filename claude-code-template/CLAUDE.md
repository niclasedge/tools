# Project: [PROJECT_NAME]

> This file provides persistent context for Claude Code. It's read automatically at session start.

## Project Overview

[Brief description of what this project does]

## Tech Stack

- Language: [e.g., Python 3.11, TypeScript 5.x]
- Framework: [e.g., FastAPI, Next.js]
- Package Manager: [e.g., uv, npm, pnpm]
- Database: [e.g., PostgreSQL, SQLite]

## Development Commands

```bash
# Install dependencies
uv sync  # or: npm install

# Run tests
uv run pytest  # or: npm test

# Run development server
uv run python main.py  # or: npm run dev

# Format code before commits
uv run black .  # or: npm run format

# Lint code
uv run ruff check .  # or: npm run lint
```

## Development Workflow

1. **Test-Driven Development**: Write a failing test, watch it fail, then make it pass
2. **Frequent Commits**: Bundle test code, implementation, and docs in single commits
3. **Format Before Commit**: Always run formatter before committing

## Architecture Notes

[Document key architectural decisions, patterns used, etc.]

## File Structure

```
src/
  main.py          # Entry point
  config.py        # Configuration
  models/          # Data models
  services/        # Business logic
tests/
  test_*.py        # Test files
```

## Conventions

- Use type hints for all functions
- Docstrings for public APIs
- Max line length: 88 characters (Black default)
- Import sorting: isort compatible

## Thinking Triggers

Use these keywords to control Claude's reasoning depth:

| Keyword | Token Budget | Use For |
|---------|-------------|---------|
| `think` | 4,000 | Simple tasks |
| `think hard` | 10,000 | Moderate complexity |
| `think harder` | 31,999 | Complex architecture |
| `ultrathink` | 31,999 | Hardest problems |

## Agent Files

@AGENTS.md

## Important Notes

- [Any critical warnings or gotchas]
- [Security considerations]
- [Performance constraints]
