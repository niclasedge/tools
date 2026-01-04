# Format Code Skill

Automatically format code before commits using project standards.

## When to Use

Activate this skill when:
- User asks to format code
- Before creating commits
- After significant code changes
- When code style issues are detected

## Instructions

### Python Projects

```bash
# Format with Black
uv run black .

# Sort imports
uv run isort .

# Check with Ruff
uv run ruff check . --fix
```

### JavaScript/TypeScript Projects

```bash
# Format with Prettier
npm run format
# or
npx prettier --write .

# Lint with ESLint
npm run lint -- --fix
```

## Verification

After formatting, run:
```bash
git diff --stat
```

Report what files were changed and summary of changes.
