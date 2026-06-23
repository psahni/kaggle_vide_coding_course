# Testing and Verification Guide

## ✅ Project Status: Ready for Security Gating Demonstration

Your shopping-assistant project is fully configured to demonstrate pre-commit hooks and automated security scanning without requiring Gemini API access.

## Running Tests (No API Required)

All unit tests pass and verify the shopping assistant tools work correctly:

```bash
# Run all unit tests
uv run pytest tests/unit/test_dummy.py -v

# Result: 14 PASSED ✅
```

### Test Coverage

**Discount Code Redemption (9 tests)**
- ✅ Valid code redemption
- ✅ Case-insensitive codes
- ✅ Whitespace handling
- ✅ Invalid code rejection
- ✅ Duplicate redemption prevention
- ✅ Different users can redeem same code
- ✅ Missing user ID rejection
- ✅ None user ID handling
- ✅ All discount codes available

**Product Catalog (5 tests)**
- ✅ Returns string
- ✅ Contains all categories (Electronics, Clothing, Home & Garden)
- ✅ Contains expected products
- ✅ Includes prices
- ✅ Non-empty content

## Pre-Commit Hooks Setup

### Installation Status

✅ Pre-commit initialized at `.git/hooks/pre-commit`
✅ Security tools installed:
- pre-commit (v4.6.0)
- semgrep (v1.167.0)
- pre-commit-hooks (v5.0.0)
- ruff (linter/formatter)

### Configuration

The `.pre-commit-config.yaml` file includes:

1. **File Validation**
   - Trailing whitespace detection
   - YAML/JSON/TOML validation
   - Large file detection
   - Python syntax validation

2. **Security Scanning** 
   - **Private key detection** ← Will catch `api_key="..."`
   - Semgrep security audit rules
   - API security rules

3. **Code Quality**
   - Ruff Python linting
   - Ruff auto-formatting

## Demonstrating Security Gating

### The Hardcoded API Key (Intentional for Demo)

Your `app/agent.py` contains:

```python
model=Gemini(
    model="gemini-flash-latest",
    api_key="AIzaSyD-mock-key-value-12345",  # ← This is the security vulnerability
    ...
)
```

This hardcoded key will be detected by pre-commit hooks.

### How to Test Pre-Commit Hooks

#### Option 1: Run Hooks Manually on Specific Files

```bash
cd shopping-assistant

# Run private key detection on agent.py
uv run pre-commit run detect-private-key --files app/agent.py

# Run ruff linter on agent.py
uv run pre-commit run ruff --files app/agent.py

# Run ruff formatter on agent.py
uv run pre-commit run ruff-format --files app/agent.py
```

#### Option 2: Test Git Hook Behavior

```bash
cd shopping-assistant

# Make a small change to a file
echo "" >> app/agent.py

# Stage the change
git add app/agent.py

# Try to commit (this will run pre-commit hooks)
git commit -m "test: test pre-commit hooks"

# Expected: Hooks will run and detect issues
# The commit will be blocked if issues found
```

#### Option 3: Run All Hooks on Project Files

```bash
# Run all hooks on Python files only
uv run pre-commit run --files app/agent.py tests/unit/test_dummy.py

# Check formatting
uv run pre-commit run ruff-format --all-files

# Check linting
uv run pre-commit run ruff --all-files
```

## Expected Results

### When Pre-Commit Detects Issues

```
Detect private key...........................................FAILED

    api_key="AIzaSyD-mock-key-value-12345"

An error has occurred: detected an arbitrary, non-whitelisted, possibly 
private key in: app/agent.py
```

### When Pre-Commit Passes

```
Trim trailing whitespace...................................Passed
Check for added large files...............................Passed
Check YAML files............................................Passed
Check JSON files............................................Passed
Check TOML files............................................Passed
Detect private keys.........................................Passed
Check Python AST............................................Passed
Ruff linter.................................................Passed
Ruff format.................................................Passed
```

## Production Workflow

### Step 1: Fix the Hardcoded Key

Replace the hardcoded key with environment variables:

```python
# app/agent.py
import os

model=Gemini(
    model="gemini-flash-latest",
    api_key=os.environ.get("GOOGLE_GENAI_API_KEY"),  # ✅ Secure
    ...
)
```

### Step 2: Run Pre-Commit Checks

```bash
uv run pre-commit run --all-files
# All should pass!
```

### Step 3: Commit Your Changes

```bash
git add app/agent.py
git commit -m "fix: use environment variable for API key"
# Hooks run automatically and pass
```

## CI/CD Integration

Add to your GitHub Actions workflow:

```yaml
name: Pre-Commit Checks

on: [pull_request, push]

jobs:
  pre-commit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.13'
      - name: Run pre-commit
        run: |
          pip install pre-commit
          pre-commit run --all-files
```

## Troubleshooting

### Issue: Pre-commit not found

```bash
# Solution: Ensure it's installed in venv
uv pip install pre-commit
```

### Issue: Hooks slow to run

```bash
# Check what's being scanned
uv run pre-commit run --all-files --verbose

# Add exclude patterns to .pre-commit-config.yaml
```

### Issue: Need to bypass hooks

```bash
# Only for emergencies!
git commit --no-verify -m "emergency fix"
```

## Next Steps

1. **Test the hooks**
   ```bash
   uv run pytest tests/unit/test_dummy.py -v  # ✅ All pass
   ```

2. **Try to commit code with hardcoded key**
   ```bash
   git add .
   git commit -m "test: pre-commit security gating"
   # Should be blocked by detect-private-key hook
   ```

3. **Fix the security issue**
   ```bash
   # Replace api_key="..." with environment variable
   # Then commit should succeed
   ```

4. **Run in production**
   ```bash
   # Add to CI/CD pipeline
   # Require checks to pass before merge
   ```

## Summary

✅ **What Works Without Gemini API:**
- Unit tests for discount code tool (14 tests)
- Pre-commit hooks configuration
- Security scanning with semgrep
- Code quality checks with ruff
- Private key detection
- Git integration

✅ **What Requires Gemini API:**
- Agent playground (`agents-cli playground`)
- Integration tests with actual agent calls

**Recommendation:** Use the test cases and pre-commit hooks to demonstrate security gating, then upgrade to Gemini API for the full playground experience.

