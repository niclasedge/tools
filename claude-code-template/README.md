# Claude Code Project Template

A ready-to-use template for projects using Claude Code, based on best practices from Simon Willison and the Claude Code community.

## Quick Start

```bash
# Copy template to your project
cp -r claude-code-template/.claude your-project/
cp claude-code-template/CLAUDE.md your-project/
cp claude-code-template/AGENTS.md your-project/

# Edit CLAUDE.md with your project details
# Update .gitignore to exclude .claude/settings.local.json
```

## Structure

```
your-project/
├── CLAUDE.md                    # Main project context (auto-loaded)
├── AGENTS.md                    # Development guidelines (import via @AGENTS.md)
└── .claude/
    ├── settings.json            # Project hooks & permissions (commit this)
    ├── settings.local.json      # Local overrides (DO NOT commit)
    ├── skills/                  # Auto-activated capabilities
    │   ├── run-tests/SKILL.md
    │   └── format-code/SKILL.md
    ├── commands/                # Slash commands (/command-name)
    │   ├── load-context.md
    │   └── create-commit.md
    └── agents/                  # Subagent configurations
        ├── researcher.md
        └── code-reviewer.md
```

## Features

### CLAUDE.md
Persistent context loaded at every session start. Include:
- Project overview
- Tech stack
- Development commands
- Architecture notes
- Conventions

### Thinking Triggers
Control Claude's reasoning depth:

| Keyword | Tokens | Use Case |
|---------|--------|----------|
| `think` | 4,000 | Simple tasks |
| `think hard` | 10,000 | Moderate complexity |
| `think harder` | 31,999 | Complex decisions |
| `ultrathink` | 31,999 | Hardest problems |

### Hooks (settings.json)

| Hook | Trigger | Use Case |
|------|---------|----------|
| `SessionStart` | Session begins | Load context, check git status |
| `PreToolUse` | Before tool runs | Validate commands |
| `PostToolUse` | After tool runs | Auto-format, notify |
| `UserPromptSubmit` | User sends message | Enrich prompts |

### Skills vs Commands vs Agents

| Feature | Activation | Purpose |
|---------|------------|---------|
| **Skills** | Automatic (context-based) | Specialized capabilities |
| **Commands** | Manual (`/command`) | Repeatable workflows |
| **Agents** | `Task` tool | Autonomous subtasks |

## Claude Code for Web

### Teleport Feature
Copy web session to local CLI:
1. Start task on claude.ai/code
2. Use "teleport" to download files + transcript
3. Continue locally with full context

### Background Tasks
- `Ctrl+B`: Send running agent to background
- `&` prefix: Start task in web background
- Check status anytime in Claude Code Web

### Remote-Only Hooks
```bash
# In hook script
if [ "$CLAUDE_CODE_REMOTE" = "true" ]; then
  # Only run in web environment
fi
```

## Best Practices

1. **Plan First**: Use "think harder" for complex tasks
2. **TDD Workflow**: Write failing test → implement → refactor
3. **Frequent Commits**: Bundle test + code + docs
4. **Format Before Commit**: Always run formatter

## Sources

- [Claude Skills are awesome](https://simonwillison.net/2025/Oct/16/claude-skills/)
- [Claude Code Best Practices](https://simonwillison.net/2025/Apr/19/claude-code-best-practices/)
- [Claude Code for Web](https://simonwillison.net/2025/Oct/20/claude-code-for-web/)
- [Hooks Reference](https://code.claude.com/docs/en/hooks)
- [Understanding Claude Code Full Stack](https://alexop.dev/posts/understanding-claude-code-full-stack/)
