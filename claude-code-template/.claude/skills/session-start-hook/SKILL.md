# Session Start Hook Skill

Configure startup hooks for Claude Code sessions, especially for Claude Code on the web.

## When to Use

Activate when user wants to:
- Set up repository for Claude Code on web
- Ensure tests/linters run during web sessions
- Load context automatically at session start

## SessionStart Hook Configuration

Add to `.claude/settings.json`:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "type": "command",
        "command": "git status --short && echo '---' && cat TODO.md 2>/dev/null || true"
      }
    ]
  }
}
```

## Environment Variables

SessionStart hooks can set environment variables via `CLAUDE_ENV_FILE`:

```bash
#!/bin/bash
# .claude/hooks/session-start.sh

# Write env vars to the file Claude provides
echo "PROJECT_ROOT=$(pwd)" >> "$CLAUDE_ENV_FILE"
echo "GIT_BRANCH=$(git branch --show-current)" >> "$CLAUDE_ENV_FILE"
```

## Web vs Local Detection

Check if running in Claude Code Web:

```bash
if [ "$CLAUDE_CODE_REMOTE" = "true" ]; then
  echo "Running in Claude Code Web"
  # Web-specific setup
else
  echo "Running locally"
  # Local-specific setup
fi
```

## Common Patterns

### Load Project Context
```json
{
  "type": "command",
  "command": "cat CLAUDE.md && git log --oneline -3"
}
```

### Install Dependencies
```json
{
  "type": "command",
  "command": "uv sync --quiet || npm ci --silent"
}
```

### Check Test Status
```json
{
  "type": "command",
  "command": "uv run pytest --collect-only -q 2>/dev/null | tail -1 || echo 'No tests configured'"
}
```
