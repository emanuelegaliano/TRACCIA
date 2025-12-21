# Contributing Extensions

This document describes the **official and supported way to contribute extensions to the library**.

Contributions are expected to follow a well-defined structure so that new functionality
integrates cleanly with the existing codebase and remains easy to test, document, and maintain.

An extension typically introduces new processing logic that can be composed into a `Trail`
and reused across different pipelines.

---

## Overview

When contributing a new extension, the following elements are required:

1. A new module under [routes](../traccia/routes/)
2. A corresponding test suite under [tests](../tests)
3. A usage example in the form of a notebook
4. Dedicated user documentation under [docs](.)
5. A version bump in the project configuration

All five steps are mandatory for a contribution to be considered complete.

---

## 1. Adding a New Route Module

Extensions are contributed as **route modules**.

### Directory Structure

Each extension must live in its own subdirectory under [routes](../traccia/routes/):

```text
routes/
└── my_extension/
    ├── __init__.py
    ├── step_a.py
    └── step_b.py
```


### `__init__.py`

Once your extension is complete, make sure it is exposed through the routes package by updating
[`traccia/routes/__init__.py`](../traccia/routes/__init__.py).

Add the relevant imports and include them in `__all__` so the extension can be discovered and imported consistently.

Example:

```python
from .step_a import step_a
from .step_b import step_b

__all__ = [
    "step_a",
    "step_b",
]
```

This ensures:

* a stable and explicit public API
* predictable imports
* easier discovery of available extensions

After adding the new module, the top-level `routes/__init__.py` must be updated accordingly
to expose the extension.

---

## 2. Adding Tests for the Extension

Every contributed extension **must include its own test suite**.

### Test Directory Structure

The test directory must mirror the name of the route module:

```
tests/
  my_extension/
    test_step_a.py
    test_step_b.py
    test_trail_integration.py
```

### Testing Rules

* All test files must start with `test_` (pytest standard)
* Each step must have at least one dedicated test
* Trail-related behavior must be tested explicitly
* Tests must be deterministic and isolated

Typical test categories include:

* unit tests for individual `Step` implementations or callable classes
* integration tests validating how steps behave when composed inside a `Trail`

---

## 3. Providing a Usage Notebook

Each contributed extension must include a **Jupyter notebook** demonstrating its usage.

### Notebook Location and Naming

Notebooks must be placed in the `examples/` directory and named after the extension:

```
examples/
  my_extension.ipynb
```

### Notebook Purpose

The notebook should:

* demonstrate realistic usage scenarios
* show how steps are composed into a `Trail`
* illustrate expected inputs and outputs
* avoid internal implementation details

The notebook serves as an executable reference for users and reviewers.

---

## 4. Writing Extension Documentation

Each contributed extension must include user-facing documentation under `docs/`.

### Documentation File

Create a Markdown file named after the extension:

```
docs/
  my_extension.md
```

### Documentation Content

The documentation should focus on **how to use the extension** and include:

* a high-level description of the extension
* the problem it addresses
* a list of available steps
* a minimal usage example
* references to the example notebook

Implementation details should be avoided in favor of usage-oriented explanations.

---

## 5. Updating the Project Version

Any contribution that adds a new extension requires a **version bump**.

### Versioning Rules

* Update the project version in the configuration file (e.g. `pyproject.toml`)
* Increment the **patch version** (the third number)

Example:

```toml
version = "1.2.3"  →  "1.2.4"
```

This signals the addition of new, backward-compatible functionality.

---

## Summary Checklist

Before submitting a Pull Request for an extension, ensure that:

* [ ] A new module exists under `routes/`
* [ ] The route module is exported via `__init__.py`
* [ ] A dedicated test suite exists under `tests/`
* [ ] All tests follow pytest conventions
* [ ] A usage notebook is provided under `examples/`
* [ ] User documentation exists under `docs/`
* [ ] The project version has been updated

Following these guidelines ensures that contributions integrate cleanly with the core library
and remain easy to review, understand, and maintain over time.
