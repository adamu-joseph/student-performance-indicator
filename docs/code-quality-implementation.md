# Code Quality Implementation

This document outlines the code quality tools and practices for the **Student Performance Indicator** project. We use industry-standard tools to ensure code consistency, correctness, and maintainability.

## Overview

Our code quality pipeline consists of three complementary tools:

1. **Black** - Code Formatter
2. **Ruff** - Fast Python Linter
3. **MyPy** - Static Type Checker

Each tool serves a specific purpose in maintaining high code standards.

---

## 1. Black - Code Formatter

### What it does

Black is an opinionated code formatter that automatically formats Python code to ensure consistent style across the entire codebase.

**Key Features:**

- Removes manual formatting decisions
- Ensures line length consistency (default: 88 characters)
- Standardizes quotes, spacing, and indentation
- Deterministic formatting (same output every time)

### Why we use it

- **Consistency:** Eliminates style debates; everyone follows the same format
- **Automation:** No need for manual code style reviews
- **Time-saving:** Developers focus on logic, not formatting
- **Readability:** Consistent formatting makes code easier to read

### Usage

```bash
# Format a single file
black src/components/data_ingestion.py

# Format entire project
black src/

# Check formatting without changes (dry-run)
black --check src/
```

---

## 2. Ruff - Fast Python Linter

### What it does

Ruff is an extremely fast Python linter that detects code issues, logic bugs, and import problems.

**Key Features:**

- Detects unused imports, variables, and undefined names (PyFlakes)
- Identifies logic errors and potential bugs (Bugbear)
- Maintains consistent import ordering (Isort)
- Extremely fast (10-100x faster than traditional linters like Pylint)

### Why we use it

- **Speed:** Lightning-fast analysis, even for large projects
- **Bug Detection:** Focuses on actual errors and logical issues
- **Low false positives:** Accurate error detection
- **Actionable feedback:** Clear error messages and solutions

### Usage

```bash
# Lint a single file
ruff check src/components/data_ingestion.py

# Lint entire project
ruff check src/

# Fix auto-fixable issues
ruff check --fix src/

# Show detailed error information
ruff check --show-source src/
```

### Common Checks

- `F` - PyFlakes errors (undefined names, unused imports)
- `B` - Bugbear (potential bugs and design problems)
- `UP` - Upgrades (modernize Python syntax)

---

## 3. MyPy - Static Type Checker

### What it does

MyPy performs static type checking on Python code. It analyzes type hints in your code to catch type-related bugs before runtime, similar to how TypeScript works for JavaScript.

**Key Features:**

- Verifies type annotations are correct
- Catches type mismatch errors
- Provides type inference for unannotated code
- Integrates with type hints (Python 3.5+)
- Reports potential runtime errors

### Why we use it

- **Bug Prevention:** Catches type errors before they reach production
- **Documentation:** Type hints serve as inline documentation
- **IDE Support:** Better autocomplete and error highlighting
- **Refactoring Safety:** Type checking helps ensure refactoring doesn't break code

### Usage

```bash
# Check a single file
mypy src/components/data_ingestion.py

# Check entire project
mypy src/

# Strict mode (most strict checking)
mypy --strict src/

# Show error codes
mypy --show-error-codes src/
```

### Type Hints Example

```python
def load_data(file_path: str, sep: str = ",") -> pd.DataFrame:
    """Load data from CSV file."""
    return pd.read_csv(file_path, sep=sep)
```

---

## Integration & Workflow

### Configuration Files

#### `pyproject.toml` - Ruff Configuration

Ruff is configured to detect bugs and errors only, avoiding any formatting rules that would conflict with Black:

```toml
[tool.ruff.lint]
select = ["F", "B", "UP", "I"]  # Bug detection only
ignore = ["E", "W"]                # Formatting handled by Black
```

#### `pyproject.toml` - Black & MyPy Configuration

```toml
[tool.black]
line-length = 88

[tool.mypy]
python_version = "3.13"
strict = false
```

### Pre-commit Hooks (Optional)

Set up Git hooks to run these tools automatically before commits:

```bash
pip install pre-commit
pre-commit install
```

Add `.pre-commit-config.yaml`

**Order matters:** Black runs first to format code, then Ruff checks for bugs.

### CI/CD Integration
Add to your CI/CD pipeline:

```bash
# Run all checks (validation)
black --check src/
ruff check src/       # Bug detection only
mypy src/

# Fix issues automatically
black src/            # Handles all formatting
ruff check --fix src/ # Fixes bugs and imports only
mypy src/             # Type checking (read-only)
```

**Order matters:** Always run Black first, then Ruff, then MyPy.

---

## Development Workflow

### For Individual Developers

1. Write code with type hints
2. Run `black` to format code (all style/formatting)
3. Run `ruff check --fix` to fix bugs and errors (no formatting conflicts)
4. Run `mypy` to verify type correctness
5. Commit and push

### Quick Commands

```bash
# Run all checks in correct order (Black → Ruff → MyPy)
black src/ && ruff check --fix src/ && mypy src/

# Or create an alias in your shell (PowerShell):
# Set-Alias -Name lint -Value {black src/ ; ruff check --fix src/ ; mypy src/}

# Or in bash:
alias lint="black src/ && ruff check --fix src/ && mypy src/"
```

**Remember:** Black handles ALL formatting, Ruff handles bugs only.

### Installation

```bash
pip install black ruff mypy
```

---

## Best Practices

### Writing Type-Friendly Code

- Always add type hints to function parameters and return types
- Use `Optional[T]` for nullable values
- Use `Union[T1, T2]` for multiple possible types
- Use type aliases for complex types

Example:

```python
from typing import Optional, List

def process_students(students: List[str], filter_active: bool = True) -> Optional[List[dict]]:
    """Process student data."""
    if not students:
        return None
    return [{"name": s, "active": filter_active} for s in students]
```

### Handling Strict Type Checking

If MyPy reports too many errors initially:

1. Run with `--no-error-summary` to see all issues
2. Use `# type: ignore` for unavoidable issues
3. Gradually increase strictness as code is improved

### Ignoring Specific Issues

When necessary, suppress specific checks:

```python
# For Ruff (avoid if possible - only for legitimate bugs)
# ruff: noqa: F841  (unused variable)
value = compute()  # ruff: noqa: F841

# Don't use ruff: noqa for style issues - Black handles those
# Don't override Black's formatting - let it work

# For MyPy
x = func()  # type: ignore[return-value]
```

---

## Resources

- **Black Documentation:** https://black.readthedocs.io/
- **Ruff Documentation:** https://docs.astral.sh/ruff/
- **MyPy Documentation:** https://mypy.readthedocs.io/
- **PEP 8 Style Guide:** https://pep8.org/
- **Python Type Hints:** https://docs.python.org/3/library/typing.html

---

**Last Updated:** 2026-09-01  
**Maintainer:** Adamu Joseph Ohigwere
