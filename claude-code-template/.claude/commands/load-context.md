# Load Project Context

Initialize the session with full project context.

## What This Command Does

1. Shows current git status
2. Lists recent commits
3. Displays TODO items
4. Shows open issues (if gh CLI available)

## Execution

```bash
echo "=== Git Status ==="
git status --short

echo ""
echo "=== Recent Commits ==="
git log --oneline -5

echo ""
echo "=== TODO Items ==="
cat TODO.md 2>/dev/null || echo "No TODO.md found"

echo ""
echo "=== Branch Info ==="
git branch -v
```

## Usage

Run this command at the start of new coding sessions to understand:
- What files have been modified
- What work was done recently
- What tasks are pending
