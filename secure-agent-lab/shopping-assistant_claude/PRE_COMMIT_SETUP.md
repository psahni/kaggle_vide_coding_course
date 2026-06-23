# Pre-Commit Security Gating Setup

## Overview

This guide demonstrates how to use pre-commit hooks and semgrep for automated security scanning of your shopping-assistant agent.

## Status: ✅ Setup Complete

### What's Installed

- **pre-commit** (v4.6.0): Git hook framework
- **semgrep** (v1.167.0): Static analysis security scanner
- **pre-commit-hooks** (v5.0.0): Standard checks (trailing whitespace, YAML validation, private key detection)
- **ruff**: Python linter and formatter
- **pytest**: Unit testing framework

### Hooks Configured

The `.pre-commit-config.yaml` file includes:

1. **Standard Checks**
   - Trailing whitespace detection
   - End-of-file fixing
   - YAML/JSON/TOML validation
   - Large file detection (max 1MB)
   - **Private key detection** ← Will catch `api_key="..."` patterns
   - Python AST validation

2. **Security Scanning**
   - Semgrep security-audit ruleset
   - Semgrep Python-specific rules
   - Semgrep API security rules

3. **Code Quality**
   - Ruff linting (Python)
   - Ruff formatting

## Running Tests (No API Required)

Tests verify the discount code tool functionality without needing Gemini API access:

```bash
# Run all unit tests
uv run pytest tests/unit -v

# Run only discount code tests
uv run pytest tests/unit/test_dummy.py::TestDiscountCodeRedemption -v

# Run with coverage
uv run pytest tests/unit --cov=app --cov-report=html
```

### Test Results

```
============================= test session starts =============================
collected 14 items

tests/unit/test_dummy.py::TestDiscountCodeRedemption::test_valid_code_redemption PASSED
tests/unit/test_dummy.py::TestDiscountCodeRedemption::test_case_insensitive_code PASSED
tests/unit/test_dummy.py::TestDiscountCodeRedemption::test_code_with_whitespace PASSED
tests/unit/test_dummy.py::TestDiscountCodeRedemption::test_invalid_code PASSED
tests/unit/test_dummy.py::TestDiscountCodeRedemption::test_duplicate_redemption_prevention PASSED
tests/unit/test_dummy.py::TestDiscountCodeRedemption::test_different_users_can_redeem_same_code PASSED
tests/unit/test_dummy.py::TestDiscountCodeRedemption::test_missing_user_id PASSED
tests/unit/test_dummy.py::TestDiscountCodeRedemption::test_none_user_id PASSED
tests/unit/test_dummy.py::TestDiscountCodeRedemption::test_all_discount_codes_available PASSED
tests/unit/test_dummy.py::TestProductCatalog::test_get_available_products_returns_string PASSED
tests/unit/test_dummy.py::TestProductCatalog::test_product_catalog_contains_categories PASSED
tests/unit/test_dummy.py::TestProductCatalog::test_product_catalog_contains_products PASSED
tests/unit/test_dummy.py::TestProductCatalog::test_product_catalog_contains_prices PASSED
tests/unit/test_dummy.py::TestProductCatalog::test_product_catalog_non_empty PASSED

======================== 14 passed in 7.69s ========================
```

## Security Gating: Hardcoded API Key Detection

The `app/agent.py` file contains an **intentionally insecure hardcoded API key** to demonstrate security scanning:

```python
model=Gemini(
    model="gemini-flash-latest",
    # Explicitly initialized with mock API key for demonstrating pre-commit security gating
    api_key="AIzaSyD-mock-key-value-12345",
    ...
)
```

This pattern will be caught by pre-commit hooks:

### Detection Methods

1. **Pre-commit-hooks' `detect-private-key` hook**
   - Detects common private key patterns
   - Catches API keys, credentials, tokens

2. **Semgrep Rules**
   - Security audit rules detect hardcoded secrets
   - Can be extended with custom rules

### Testing Security Detection

To see pre-commit in action, try committing a change:

```bash
# Make a small change
echo "# test" >> app/agent.py

# Try to commit
git add app/agent.py
git commit -m "test commit"

# The pre-commit hooks will run and:
# - Check for trailing whitespace
# - Detect the hardcoded API key
# - Run semgrep security scan
# - Lint with ruff
# - Run pytest tests (if configured)
```

### Expected Behavior

When you try to commit code with a hardcoded API key:

```
Detect private key...........................................FAILED
  - Hook id: detect-private-key
  - File: app/agent.py
  - Pattern: api_key="AIzaSyD-mock-key-value-12345"
```

## Adding Tests to Pre-Commit

To add pytest checks to pre-commit, add this to `.pre-commit-config.yaml`:

```yaml
- repo: local
  hooks:
    - id: pytest
      name: pytest
      entry: pytest tests/unit -v
      language: system
      types: [python]
      stages: [commit]
      pass_filenames: false
```

## Manual Hook Execution

Run pre-commit hooks manually on all files:

```bash
# Check all files
uv run pre-commit run --all-files

# Check specific hook
uv run pre-commit run detect-private-key --all-files

# Run semgrep specifically
uv run pre-commit run semgrep --all-files

# Run ruff
uv run pre-commit run ruff --all-files
```

## Bypass Hooks (Not Recommended)

Only for emergency merges:

```bash
# Bypass all hooks
git commit --no-verify -m "Emergency fix"

# This defeats the purpose of security gating!
```

## Fixing Issues Found by Hooks

### Trailing Whitespace
Auto-fixed by pre-commit hooks.

### Private Key Detection
- Remove hardcoded keys
- Use environment variables: `api_key=os.environ.get("GEMINI_API_KEY")`
- Use Application Default Credentials

### Linting Issues
Auto-fixed by ruff-format:

```bash
uv run ruff format app/
```

### Semgrep Issues
Review and fix according to the rules.

## Production Setup

For production deployments:

1. **Enable in CI/CD Pipeline**
   ```yaml
   # GitHub Actions example
   - name: Pre-commit checks
     run: uv run pre-commit run --all-files
   ```

2. **Enforce Before Merge**
   - Configure branch protection rules
   - Require pre-commit status checks to pass

3. **Use Real Credentials**
   - Replace hardcoded keys with secrets management
   - Use Google Secret Manager or equivalent

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `hook id not found` | Run `pre-commit install` |
| `command not found: semgrep` | Run `uv pip install semgrep` |
| `hooks failing on commit` | Run `uv run pre-commit run --all-files` to see issues |
| `too many files to scan` | Configure excludes in `.pre-commit-config.yaml` |

## References

- [Pre-commit Documentation](https://pre-commit.com/)
- [Semgrep Rules](https://semgrep.dev/explore)
- [Private Key Detection](https://github.com/pre-commit/pre-commit-hooks#detect-private-key)
- [Google Cloud Security Best Practices](https://cloud.google.com/security/best-practices)

