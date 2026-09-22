# Developer Guide

Quick technical setup guide for the **Student Performance Indicator** project.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Development Setup](#development-setup)

> For project architecture, structure details, components, and workflow information, see [architecture](architecture.md).

---

## Getting Started

> Find detailed getting started instructions at [setup](../setup.txt)
---

## Development Setup

### Code Quality

- Follow PEP 8 style guidelines
- Use type hints on all function signatures (parameters and return types)
- Write Google-style docstrings (with `Args:` / `Returns:`) for public functions and classes
- Keep functions and classes focused and modular
- Use object-oriented programming as the programming paradigm to keep code clean and modular
- Use configuration-driven architecture to ensure reusability

> Get the tools documentation at [code quality implementation](./003-code-quality-implementation.md)

### Coding Patterns

These patterns are established across the codebase — follow them when writing new code.

- **Module layout:** module docstring → `from __future__ import annotations` → stdlib → third-party → project imports → constants → classes/functions → `__all__` export list
- **Type hints:** add `from __future__ import annotations` in every module; use `X | Y` over `Union`, `X | None` over `Optional`
- **Paths:** always use `pathlib.Path`, never `os.path`; define `PROJECT_ROOT = Path(__file__).resolve().parents[N]` at module level
- **Config pattern:** frozen dataclasses with a `from_yaml()` classmethod that validates required fields via `ClassVar[frozenset]`
- **Component pattern:** `__init__` takes a config path, delegates parsing to the config dataclass (`self.config = MyConfig.from_yaml(path)`)
- **Structured logging:** use the project logger with keyword arguments — `logger.info("Loading data", path=str(p))`, not f-strings in the message
- **Error handling:** log with structured context first, then raise a specific exception (`ValueError`, `FileNotFoundError`, etc.) with a descriptive message; chain with `from` when wrapping lower-level errors
- **Naming:** `PascalCase` classes, `snake_case` functions, `_prefixed` private helpers, `UPPER_SNAKE_CASE` constants, `Config` suffix for config dataclasses
- **Exports:** end every module with an explicit `__all__` listing public names only

### Security

- Use Bandit to scan for common Python security vulnerabilities
- Use pip-audit to detect vulnerable dependency versions before release
- Fix security issues promptly and review findings before merging

> Get the tools documentation at [security implementation](./004-security-implementation.md)

### Testing

- Use pytest for unit and integration testing across the project
- Write clear tests for data processing, model logic, and regression prevention

> Get the tools documentation at [testing implementation](./005-testing-implementation.md)

---

**Last Updated:** 2026-09
**Maintainer:** Adamu Joseph Ohigwere
