# Create Commit

Create a well-formatted git commit with conventional commit message.

## Arguments

- $1: Type (feat, fix, docs, style, refactor, test, chore)
- $2: Scope (optional, e.g., api, ui, auth)
- $3: Description

## Pre-Commit Checklist

Before committing:

1. Run formatter:
   ```bash
   uv run black . && uv run isort .
   ```

2. Run tests:
   ```bash
   uv run pytest
   ```

3. Check status:
   ```bash
   git status
   git diff --staged
   ```

## Commit Message Format

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting
- `refactor`: Code restructuring
- `test`: Adding tests
- `chore`: Maintenance

## Example

```bash
git add .
git commit -m "feat(api): add user authentication endpoint"
```
