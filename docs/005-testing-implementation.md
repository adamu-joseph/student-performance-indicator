# Testing Implementation

This document outlines the testing practices and tools for the **Student Performance Indicator** project. We use industry-standard testing frameworks to ensure code quality, reliability, and regression prevention.

## Overview

Our testing pipeline consists of complementary tools:

1. **pytest** - Testing Framework & Test Runner
2. **pytest-cov** - Code Coverage Analysis
3. **pip-audit** - Dependency Vulnerability Testing (Security)

Each tool serves a specific purpose in maintaining application reliability and security.

---

## 1. pytest - Testing Framework

### What it does

pytest is a mature, feature-rich Python testing framework that makes it easy to write small, readable tests and complex functional testing. It's used for unit testing, integration testing, and end-to-end testing.

**Key Features:**

- Simple test discovery and execution
- Powerful assertions with helpful error messages
- Fixtures for test setup and teardown
- Parametrized testing (run tests with different inputs)
- Plugin ecosystem for extended functionality
- Parallel test execution support
- Detailed test reports and statistics
- Easy integration with CI/CD pipelines

### Why we use it

- **Simplicity:** Minimal boilerplate, easy to write tests
- **Readability:** Tests are clear and maintainable
- **Powerful:** Supports simple to complex testing scenarios
- **Fixtures:** Reusable test setup/teardown logic
- **Reporting:** Detailed test results and failure analysis
- **Integration:** Works seamlessly with coverage and CI/CD tools

### Test Structure

Tests should be organized in a `tests/` directory mirroring the source structure:

```
project/
├── src/
│   ├── components/
│   │   ├── data_ingestion.py
│   │   └── data_transformation.py
│   └── pipeline/
│       └── train_pipeline.py
├── tests/
│   ├── components/
│   │   ├── test_data_ingestion.py
│   │   └── test_data_transformation.py
│   └── pipeline/
│       └── test_train_pipeline.py
└── pytest.ini
```

### Writing Tests

#### Basic Test Example
```python
# tests/components/test_data_ingestion.py
import pytest
import pandas as pd
from src.components.data_ingestion import load_data

def test_load_data_returns_dataframe():
    """Test that load_data returns a DataFrame."""
    df = load_data("artifacts/raw.csv")
    assert isinstance(df, pd.DataFrame)
    assert len(df) > 0

def test_load_data_correct_columns():
    """Test that loaded data has expected columns."""
    df = load_data("artifacts/raw.csv")
    expected_cols = ["student_id", "math_score", "reading_score"]
    assert all(col in df.columns for col in expected_cols)
```

#### Using Fixtures
```python
# tests/components/test_data_ingestion.py
import pytest
import pandas as pd

@pytest.fixture
def sample_data():
    """Fixture providing sample DataFrame for testing."""
    return pd.DataFrame({
        "student_id": [1, 2, 3],
        "math_score": [90, 85, 88],
        "reading_score": [92, 88, 91]
    })

def test_data_transform(sample_data):
    """Test data transformation with fixture."""
    from src.components.data_transformation import transform_data
    result = transform_data(sample_data)
    assert result is not None
    assert len(result) == len(sample_data)
```

#### Parametrized Tests
```python
# tests/components/test_data_transformation.py
import pytest

@pytest.mark.parametrize("input_value,expected", [
    (10, 100),
    (20, 400),
    (30, 900),
])
def test_square_calculation(input_value, expected):
    """Test calculation with multiple inputs."""
    from src.utils import square
    assert square(input_value) == expected
```

#### Testing Exceptions
```python
# tests/components/test_data_ingestion.py
import pytest
from src.exception import CustomException

def test_load_nonexistent_file_raises_error():
    """Test that loading missing file raises exception."""
    from src.components.data_ingestion import load_data
    
    with pytest.raises(FileNotFoundError):
        load_data("nonexistent_file.csv")

def test_invalid_data_raises_custom_exception():
    """Test that invalid data raises CustomException."""
    from src.components.data_transformation import transform_data
    
    with pytest.raises(CustomException):
        transform_data(None)
```

### Usage

```bash
# Run all tests
pytest

# Run tests in a specific file
pytest tests/components/test_data_ingestion.py

# Run tests matching a pattern
pytest tests/ -k "test_load"

# Run with verbose output
pytest -v

# Stop on first failure
pytest -x

# Show print statements (useful for debugging)
pytest -s

# Run tests in parallel (faster)
pytest -n auto

# Run with specific markers
pytest -m "not slow"

# Generate HTML report
pytest --html=report.html

# Show coverage report
pytest --cov=src --cov-report=html
```

### Configuration

pytest configuration in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
python_classes = "Test*"
python_functions = "test_*"
addopts = "-v --strict-markers"
markers = [
    "slow: marks tests as slow",
    "integration: marks tests as integration tests",
    "unit: marks tests as unit tests",
]
```

---

## 2. pytest-cov - Code Coverage Analysis

### What it does

pytest-cov measures code coverage, showing which lines of code are executed by your tests. It helps identify untested code and ensures critical paths have test coverage.

**Key Features:**

- Tracks which code lines are executed
- Reports coverage percentage by file
- Identifies missing coverage
- Multiple report formats (HTML, XML, JSON)
- Branch coverage analysis
- Integration with CI/CD and quality gates

### Why we use it

- **Quality Metrics:** Ensures code is properly tested
- **Risk Identification:** Highlights untested critical paths
- **Improvement Tracking:** Monitor coverage trends over time
- **CI/CD Integration:** Enforce minimum coverage requirements
- **Visual Reports:** HTML reports for easy analysis

### Usage

```bash
# Run tests with coverage report
pytest --cov=src

# Generate HTML coverage report
pytest --cov=src --cov-report=html

# Coverage report in terminal
pytest --cov=src --cov-report=term-missing

# Generate XML report for CI/CD
pytest --cov=src --cov-report=xml

# Set minimum coverage threshold
pytest --cov=src --cov-fail-under=80

# Coverage for specific module
pytest --cov=src.components tests/components/
```

### Coverage Goals

```
Minimum Coverage Targets:
- Critical modules (ML models, data pipeline): 85%+
- Utility functions: 80%+
- Core business logic: 80%+
- General modules: 70%+
- Overall project: 75%+
```

### HTML Report

After running `pytest --cov=src --cov-report=html`, open `htmlcov/index.html` to see:
- Coverage percentage per file
- Uncovered lines highlighted in red
- Branch coverage details
- Trend analysis

---

## 3. pip-audit - Dependency Testing (Security)

pip-audit is documented in [security-implementation.md](security-implementation.md). It's integrated into the testing pipeline to ensure dependencies don't have known vulnerabilities.

---

## Integration & Workflow

### Pre-commit Configuration

Tests are configured in `.pre-commit-config.yaml`:

```yaml
- repo: local
  hooks:
    - id: pytest
      name: pytest
      entry: pytest
      language: system
      pass_filenames: false
      stages: [pre-push]  # Runs on git push only

    - id: pip-audit
      name: pip-audit
      entry: pip-audit
      args: ["--skip-editable"]
      language: system
      pass_filenames: false
      stages: [pre-push]  # Runs on git push only
```

**Note:** Tests run on `pre-push` (before pushing to remote), not on every commit. This allows developers to commit work-in-progress without test failures.

### CI/CD Integration

Add testing to your CI/CD pipeline:

```bash
#!/bin/bash
# test-suite.sh

echo "Running comprehensive test suite..."

# Unit and integration tests
echo "🧪 Running pytest..."
pytest tests/ -v --cov=src --cov-report=html --cov-fail-under=75
if [ $? -ne 0 ]; then
  echo "❌ Tests failed"
  exit 1
fi

# Generate coverage badge
coverage-badge -o coverage.svg

echo "✓ All tests passed"
```

### Development Workflow

#### For Individual Developers

1. **Write tests alongside code:**
   ```bash
   # Create test file
   touch tests/components/test_new_feature.py
   # Write tests following fixtures and parametrization patterns
   ```

2. **Run tests locally before pushing:**
   ```bash
   # Run all tests
   pytest

   # Run specific test file
   pytest tests/components/test_data_ingestion.py

   # Run with coverage
   pytest --cov=src --cov-report=html
   ```

3. **Pre-push verification:**
   ```bash
   # pytest runs automatically on pre-push
   git push origin feature-branch  # Tests run here
   ```

#### Quick Commands

```bash
# Run all tests
pytest

# Run with coverage and stop on first failure
pytest --cov=src -x

# Run specific test
pytest tests/components/test_data_ingestion.py::test_load_data_returns_dataframe

# Run tests matching pattern
pytest -k "test_transform" -v

# Run with detailed output
pytest -vv -s

# Run in parallel (faster)
pytest -n auto

# Generate comprehensive reports
pytest --cov=src --cov-report=html --html=report.html -v
```

---

## Best Practices

### Test Organization

1. **One test file per module:**
   ```
   src/components/data_ingestion.py → tests/components/test_data_ingestion.py
   ```

2. **Clear test names:**
   ```python
   # ✓ GOOD - Describes what is being tested
   def test_load_data_returns_dataframe_with_correct_shape():
       pass

   # ❌ BAD - Unclear
   def test_data():
       pass
   ```

3. **Use fixtures for reusable setup:**
   ```python
   @pytest.fixture
   def model():
       """Fixture for model instances."""
       return ModelClass()

   def test_model_prediction(model):
       result = model.predict(data)
       assert result is not None
   ```

### Test Types

#### Unit Tests
Test individual functions in isolation:
```python
def test_calculate_mean():
    """Test mean calculation function."""
    from src.utils import calculate_mean
    result = calculate_mean([1, 2, 3, 4, 5])
    assert result == 3.0
```

#### Integration Tests
Test multiple components working together:
```python
@pytest.mark.integration
def test_pipeline_end_to_end():
    """Test complete training pipeline."""
    from src.pipeline.train_pipeline import TrainPipeline
    pipeline = TrainPipeline()
    model = pipeline.run()
    assert model is not None
```

#### Slow Tests
Mark slow tests to skip in quick runs:
```python
@pytest.mark.slow
def test_model_training_with_large_dataset():
    """Slow test - only run in CI."""
    # Long-running test
    pass

# Skip slow tests: pytest -m "not slow"
```

### Coverage Best Practices

1. **Aim for 80%+ coverage** for critical paths
2. **100% coverage not always necessary** - test logic, not trivial getters
3. **Focus on edge cases** - test boundaries and error conditions
4. **Avoid testing third-party code** - you don't need to test pandas
5. **Use coverage reports to identify gaps** - review uncovered lines

Example:
```python
# ✓ GOOD - Testing logic and edge cases
def test_data_validation_with_empty_dataframe():
    """Test validation with empty input."""
    result = validate_data(pd.DataFrame())
    assert result is False

def test_data_validation_with_missing_columns():
    """Test validation with missing required columns."""
    df = pd.DataFrame({"col1": [1, 2, 3]})
    with pytest.raises(ValueError):
        validate_data(df)

# ❌ BAD - Testing trivial code
def test_get_name():
    """Don't test simple getters."""
    obj = MyClass(name="test")
    assert obj.get_name() == "test"
```

### Debugging Tests

```bash
# Print debug output
pytest -s tests/test_module.py

# Stop on first failure
pytest -x

# Drop into debugger on failure
pytest --pdb

# Show local variables on failure
pytest -l

# Verbose output
pytest -vv
```

---

## Test Checklist

Before committing code:

- [ ] Write tests for new functions/features
- [ ] Run full test suite: `pytest`
- [ ] Check coverage: `pytest --cov=src`
- [ ] Coverage above 75%: `pytest --cov=src --cov-fail-under=75`
- [ ] No test failures: All tests pass
- [ ] Edge cases covered: Test boundaries and errors
- [ ] Clear test names: Describe what is tested
- [ ] Fixtures used: Avoid code duplication
- [ ] Mocking external dependencies: Don't test third-party code

---

## Resources

- **pytest Documentation:** https://docs.pytest.org/
- **pytest Fixtures:** https://docs.pytest.org/en/latest/fixture.html
- **pytest-cov:** https://pytest-cov.readthedocs.io/
- **Testing Best Practices:** https://docs.python-guide.org/writing/tests/
- **Python Testing:** https://realpython.com/python-testing/

---

## Installation

```bash
# Install testing tools
pip install pytest pytest-cov

# Or from requirements
pip install -r requirements.txt
```

---

**Last Updated:** 2026-09-01  
**Maintainer:** Development Team
