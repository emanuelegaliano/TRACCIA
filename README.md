<p align="center">
  <img src="docs/assets/cover.png" alt="TRACCIA cover" width="100%" />
</p>

# TRACCIA

**Transformation & Reactive Actions Chain-based Component Integration Architecture**

---

## Description

TRACCIA is a lightweight, extensible Python framework for building **modular processing pipelines**
based on the **Chain of Responsibility** pattern.

It is designed around three core concepts:

- **Footprint** – a shared, mutable state flowing through the pipeline
- **Step** – a small processing unit that operates on the footprint
- **Trail** – a composable pipeline that orchestrates step execution

TRACCIA emphasizes:
- clarity over complexity
- explicit contracts
- composability and extensibility
- testability by design

---

## Installation

To install the latest version of the repository directly from GitHub:

```bash
pip install git+https://github.com/emanuelegaliano/TRACCIA.git
```

This will always install the current state of the `main` branch.

---

## Repository Structure

Below is an overview of the main directories in the repository.

### [`traccia/`](./traccia/)

The core library package.

It contains:

* the `Trail` implementation
* the `Step` abstraction and decorator
* the metadata and execution logic
* all core building blocks required to define pipelines

---

### [`traccia/routes/`](traccia/routes/)

Built-in extensions and route modules.

Each subdirectory represents a **self-contained extension** composed of one or more steps
that can be imported and composed into a `Trail`.

> Note: this section is not yet implemented. It will be updated as soon as the first extension is added.

---

### [`tests/`](./tests/)

The complete test suite for the project.

It includes:

* core tests validating the fundamental contracts
* extension-specific tests
* integration tests covering full pipeline behavior

All tests follow standard **pytest** conventions.

In order to run tests, go into the directory [`tests/`](./tests/) and, in the terminal, print:
```bash
python run_all.py
```

---

### [`examples/`](./examples/)

Executable examples and Jupyter notebooks.

These notebooks demonstrate:

* how to define custom footprints
* how to compose trails
* how to extend the library
* how to test extensions

They are intended for learning and exploration. An example can be seen in [`examples/text_cleaning.ipynb`](examples/text_cleaning.ipynb)

---

### [`docs/`](./docs/)

Project documentation.

This directory contains conceptual guides, contribution guidelines, and extension documentation.

---

## Extension Guides

### `extending.md`

Located under [`docs/extending.md`](./docs/extending.md).

This document explains **how to extend TRACCIA locally**, focusing on:

* creating custom footprints
* defining new steps
* composing and modifying trails
* using the library within your own projects

It is intended for **library users**.

---

### `contribute.md`

Located under [`docs/contribute.md`](./docs/contribute.md).

This document explains **how to contribute extensions to the project** via Pull Requests.

It defines:

* the required directory structure
* testing requirements
* documentation expectations
* versioning rules

It is intended for **contributors**.

---

## License

This project is licensed under the MIT License.

---

## Final Note

> *Simplicity is a prerequisite for reliability.*  
> — **Edsger W. Dijkstra**
