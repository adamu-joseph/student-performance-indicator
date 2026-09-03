# Security Implementation

This document outlines the security tools and practices for the **Student Performance Indicator** project. We use industry-standard security scanners to identify and prevent vulnerabilities before they reach production.

## Overview

Our security pipeline consists of two complementary tools:

1. **Bandit** - Code Security Scanner
2. **pip-audit** - Dependency Vulnerability Scanner

Each tool serves a specific purpose in maintaining application security.

---

## 1. Bandit - Code Security Scanner

### What it does

Bandit is a Python security linter that scans Python code for common security vulnerabilities and issues. It analyzes your code for dangerous patterns that could lead to security exploits or bad security practices.

**Key Features:**

- Detects hardcoded passwords and secrets
- Identifies SQL injection vulnerabilities
- Finds insecure cryptographic usage
- Detects weak random number generation
- Warns about dangerous function calls (e.g., `eval()`, `exec()`)
- Identifies insecure deserialization patterns
- Checks for insecure file permissions
- Detects use of temporary files without proper security

### Why we use it

- **Vulnerability Prevention:** Catches security issues before code is deployed
- **Best Practices:** Enforces secure coding standards
- **Proactive Security:** Identifies potential exploits early
- **Fast & Automated:** No manual security code reviews needed
- **Actionable Feedback:** Clear explanations of security risks

### Usage

```bash
# Scan a single file
bandit src/components/data_ingestion.py

# Scan entire project
bandit -r src/

# Generate JSON report (for CI/CD integration)
bandit -r src/ -f json -o security_report.json

# Show severity levels (HIGH, MEDIUM, LOW)
bandit -r src/ -v

# Exclude specific test files
bandit -r src/ --skip B101  # Skip test assertions check
```

### Common Security Issues Detected

| Issue | Code | Risk Level | Example |
|-------|------|-----------|---------|
| Hardcoded password | B105, B106 | HIGH | `password = "admin123"` |
| SQL Injection | B608 | HIGH | `query = f"SELECT * FROM users WHERE id = {user_id}"` |
| Insecure random | B311 | MEDIUM | `random.random()` for secrets |
| Use of `eval()` | B307 | HIGH | `eval(user_input)` |
| Insecure deserialization | B301 | HIGH | `pickle.loads(data)` |
| Insecure temp files | B108 | MEDIUM | `/tmp/` with predictable names |

### Configuration

Bandit can be configured via `.bandit` file or `pyproject.toml`:

```toml
[tool.bandit]
exclude_dirs = ["tests", "docs"]
skips = ["B101"]  # Skip test assertions
tests = ["B201", "B301", "B302"]  # Specific tests to run
```

---

## 2. pip-audit - Dependency Vulnerability Scanner

### What it does

pip-audit scans your project dependencies for known security vulnerabilities. It checks the installed packages against the PyPA advisory database to find any insecure versions.

**Key Features:**

- Scans all installed dependencies
- Checks against PyPA vulnerability database
- Reports known CVEs in dependencies
- Suggests updated versions
- Generates detailed vulnerability reports
- Integrates with CI/CD pipelines

### Why we use it

- **Dependency Security:** Ensures third-party libraries are secure
- **Vulnerability Database:** Uses official PyPA advisory database
- **Up-to-date:** Regularly updated with new CVEs
- **Easy Integration:** Simple to use in CI/CD
- **Risk Management:** Identifies packages that need updates

### Usage

```bash
# Scan all dependencies
pip-audit

# Scan excluding editable packages
pip-audit --skip-editable

# Generate JSON report
pip-audit --format json -o audit_report.json

# Show only HIGH severity vulnerabilities
pip-audit --format markdown

# Fix vulnerabilities automatically (dry-run first)
pip-audit --fix
```

### Output Example

``` yaml
Found 2 vulnerabilities in 1 package:

Name: requests
Version: 2.25.1
Vulnerability: CVE-2021-33503
  Description: urllib3 before 1.26.5 does not properly validate ...
  Fixed in: 2.26.0
  
Name: cryptography
Version: 3.1.1
Vulnerability: CVE-2020-36242
  Description: Potential integer overflow in ECDH key derivation
  Fixed in: 3.1.2
```

---

## Integration & Workflow

### Pre-commit Configuration

Both security tools are integrated into `.pre-commit-config.yaml`:

```yaml
- repo: https://github.com/PyCQA/bandit
  rev: 1.7.10
  hooks:
    - id: bandit
      # Runs automatically on every commit

- repo: local
  hooks:
    - id: pip-audit
      name: pip-audit
      entry: pip-audit
      args: ["--skip-editable"]
      language: system
      pass_filenames: false
      stages: [pre-push]  # Runs on git push only
```

**Note:** pip-audit runs on pre-push (before pushing to remote), while Bandit runs on every commit.

### Development Workflow

#### For Individual Developers

1. **Before committing:**
   ```bash

   # Pre-commit hooks run automatically
   # Bandit scans for code vulnerabilities
   git add .
   git commit -m "feature: add data processing"  # Bandit runs here
   ```

2. **Before pushing:**
   ```bash
   # pip-audit runs automatically on pre-push
   git push origin feature-branch  # pip-audit runs here
   ```

3. **Manual checks:**
   ```bash
   # Run both manually if needed
   bandit -r src/
   pip-audit
   ```

#### Quick Commands

```bash
# Run all security checks manually
bandit -r src/ && pip-audit

# Run with verbose output
bandit -r src/ -v && pip-audit

# Generate reports for review
bandit -r src/ -f json -o bandit_report.json
pip-audit --format json -o audit_report.json
```

---

## Best Practices

### Writing Secure Code

#### 1. Never Hardcode Secrets

```python
# ❌ BAD - Hardcoded password
database_password = "super_secret_123"

# ✓ GOOD - Use environment variables
import os
database_password = os.getenv("DB_PASSWORD")
```

#### 2. Avoid Dynamic Code Execution

```python
# ❌ BAD - Using eval() with user input
user_code = request.args.get("code")
result = eval(user_code)

# ✓ GOOD - Use safer alternatives
import ast
user_code = request.args.get("code")
# Parse safely without execution
ast.literal_eval(user_code)
```

#### 3. Use Parameterized Queries

```python
# ❌ BAD - SQL Injection vulnerability
query = f"SELECT * FROM users WHERE id = {user_id}"
result = db.execute(query)

# ✓ GOOD - Parameterized query
query = "SELECT * FROM users WHERE id = ?"
result = db.execute(query, (user_id,))
```

#### 4. Secure Random Generation

```python
# ❌ BAD - Weak random for secrets
import random
token = ''.join([random.choice('0123456789') for _ in range(32)])

# ✓ GOOD - Cryptographically secure random
import secrets
token = secrets.token_urlsafe(32)
```

#### 5. Use Secure Deserialization

```python
# ❌ BAD - Unsafe pickle deserialization
import pickle
data = pickle.loads(untrusted_data)

# ✓ GOOD - Use JSON for untrusted data
import json
data = json.loads(untrusted_data)
```

### Handling Bandit Issues

#### Suppressing False Positives

```python
# Suppress a specific Bandit issue
def safe_eval_context(code):  # noqa: B102
    """Safe eval in restricted context."""
    # Limited context for eval
    return eval(code, {"__builtins__": {}})

# Or use Bandit comment
try:
    exec(trusted_code)  # nosec B102
except Exception:
    pass
```

#### Configuration File

Create `.bandit` to skip certain checks:
```json
{
  "exclude_dirs": ["tests", "docs"],
  "tests": ["B201", "B301", "B302"],
  "skips": []
}
```

### Handling pip-audit Issues

#### Fixing Vulnerable Dependencies

```bash
# Check what needs updating
pip-audit

# Update to safe version
pip install --upgrade vulnerable-package

# Or let pip-audit suggest fixes
pip-audit --fix
```

#### Allowing Known Issues (Temporary)

```bash
# Generate requirements with ignore list
pip-audit --ignore CVE-2021-12345
```

---

## Security Checklist

Before deploying to production:

- [ ] Run `bandit -r src/` - No HIGH severity issues
- [ ] Run `pip-audit` - No vulnerable dependencies
- [ ] Review all security findings and resolve them
- [ ] Update dependencies to patched versions
- [ ] Remove any hardcoded secrets/credentials
- [ ] Verify all external inputs are validated
- [ ] Confirm secure cryptography usage
- [ ] Check file permissions and temp file handling
- [ ] Document any security exceptions

---

## Resources

- **Bandit Documentation:** https://bandit.readthedocs.io/
- **pip-audit Documentation:** https://github.com/pypa/pip-audit
- **OWASP Top 10:** https://owasp.org/www-project-top-ten/
- **CWE List:** https://cwe.mitre.org/
- **Python Security:** https://python.readthedocs.io/en/latest/library/security_warnings.html
- **PyPA Advisory Database:** https://github.com/pypa/advisory-database

---

## Installation

```bash
# Install security tools
pip install bandit pip-audit

# Or from requirements
pip install -r requirements.txt
```

---

**Last Updated:** 2026-09-01  
**Maintainer:** Adamu Joseph Ohigwere