# AGENTS.md - Development Guidelines

> Note: Claude Code doesn't officially support AGENTS.md yet.
> Import this file from CLAUDE.md using: @AGENTS.md
> Or create symlink: ln -s AGENTS.md CLAUDE.md

## Development Methodology

### Test-Driven Development (TDD)

1. Write a failing test first
2. Watch the test fail (verify it tests the right thing)
3. Write minimal code to make it pass
4. Refactor if needed
5. Repeat

### Commit Strategy

- Make frequent, atomic commits
- Each commit should bundle:
  - Test code
  - Implementation
  - Documentation updates
- Write descriptive commit messages

### Code Quality

Before every commit:

```bash
# Format
uv run black .
uv run isort .

# Lint
uv run ruff check .

# Type check
uv run mypy .

# Test
uv run pytest
```

## Task Execution Guidelines

### Planning Phase

1. Understand the full scope before coding
2. Break down into subtasks
3. Identify potential blockers
4. Ask clarifying questions if needed

### Implementation Phase

1. Start with the simplest working solution
2. Add complexity only when needed
3. Keep functions small and focused
4. Write self-documenting code

### Review Phase

1. Run all tests
2. Check for edge cases
3. Verify error handling
4. Update documentation

## Communication

- Be concise in explanations
- Show don't tell (code examples)
- Flag assumptions explicitly
- Ask before making breaking changes
