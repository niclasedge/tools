# Run Tests Skill

Run the project test suite with coverage reporting.

## When to Use

Activate this skill when:
- User asks to run tests
- After implementing new features
- Before committing code
- When debugging test failures

## Instructions

1. Run the full test suite:
   ```bash
   uv run pytest -v --tb=short
   ```

2. For coverage report:
   ```bash
   uv run pytest --cov=src --cov-report=term-missing
   ```

3. For specific test file:
   ```bash
   uv run pytest tests/test_<module>.py -v
   ```

4. For failed tests only:
   ```bash
   uv run pytest --lf -v
   ```

## Interpreting Results

- Green: Test passed
- Red: Test failed - show the failure message
- Yellow: Test skipped or xfailed

Always report:
- Number of tests passed/failed
- Any error messages
- Suggestions for fixes if tests fail
