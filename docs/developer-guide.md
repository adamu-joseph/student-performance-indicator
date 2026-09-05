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
- Use type hints where applicable
- Write docstrings for functions and classes
- Keep functions and classes focused and modular

> Get the tools documentation at [code quality implementation](./003-code-quality-implementation.md)

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
