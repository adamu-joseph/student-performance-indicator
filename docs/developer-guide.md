# Developer Guide

Quick technical setup guide for the **Student Performance Indicator** project.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Development Setup](#development-setup)

> For project architecture, structure details, components, and workflow information, see [architecture](architecture.md).

---

## Getting Started

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Git (for version control)

### Installation

1. **Clone the repository** (if applicable)

   ```bash
   git clone <repository-url>
   cd student-performance-indicator
   ```

2. **Create a virtual environment** (recommended)

   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.in
   ```

---

## Development Setup

### Environment Variables

Create a `.env` file in the root directory (if needed) for sensitive configuration:

``` python
# Example:
# LOG_LEVEL=DEBUG
# MODEL_PATH=artifacts/model
```

### Running Tests

```bash
pytest tests/
```

### Code Quality

- Follow PEP 8 style guidelines
- Use type hints where applicable
- Write docstrings for functions and classes
- Keep functions focused and modular

---

**Last Updated:** 2026-09-01  
**Maintainer:** Adamu Joseph Ohigwere