# Extending the Library

This document describes **how to extend the library from a conceptual and architectural perspective**.

Concrete, runnable examples are intentionally omitted here and are instead provided in a dedicated notebook:

👉 **See the practical walkthrough:**  
[`examples/text_cleaning_pipeline.ipynb`](../examples/text_cleaning_pipeline.ipynb)

---

## Overview

The library is designed to be **lightweight, modular, and extensible**.  
Its extension model is based on three core abstractions:

- **Footprint** – shared mutable state
- **Step** – a unit of processing
- **Trail** – an executable pipeline

Extending the library means implementing or composing these abstractions while respecting their contracts.

---

## The Footprint Extension Model

### Purpose of the Footprint

A `Footprint` represents the **state that flows through the pipeline**.  
All steps operate on the same footprint instance.

Typical responsibilities of a footprint include:
- holding domain data
- accumulating intermediate results
- exposing execution metadata

### Required Contract

Any custom footprint **must**:

1. Implement a `get_metadata()` method
2. Always return the **same metadata instance**
3. Be mutable

The metadata object is used internally to track:
- executed steps
- execution order
- tags, run identifiers, and tracing information

Breaking this contract (for example by returning a new metadata instance each time) will lead to incorrect or incomplete tracing.

### Design Guidelines

- Keep the footprint focused on *state*, not behavior
- Avoid embedding business logic in the footprint
- Prefer explicit attributes over nested or implicit structures

---

## The Step Extension Model

### What Is a Step

A `Step` is a **processing unit** that:
- receives a footprint
- optionally mutates or enriches it
- returns a footprint

Steps are executed sequentially by a `Trail`.

### Functional Steps (Recommended)

The most common and idiomatic way to define a step is as a function.

Conceptually, a functional step should:
- be small and focused
- perform a single transformation
- avoid hidden side effects
- be easy to test in isolation

Functional steps are ideal when:
- no configuration is required
- no internal state is needed
- behavior is purely derived from input

---

### Class-Based Steps (Callable Objects)

Steps can also be implemented as **callable objects**.

This approach is recommended when:
- configuration parameters are required
- dependencies must be injected
- internal state is needed across executions

From the pipeline’s perspective, class-based steps behave exactly like functional ones, as long as they are callable and respect the step contract.

The notebook demonstrates when and why this approach is preferable.

---

## The Trail Extension Model

### Role of the Trail

A `Trail` represents a **chain of responsibility**:
- it defines execution order
- it manages step metadata
- it executes validation, dry-runs, and tracing

Trails are intentionally mutable to support advanced composition patterns.

---

### Dynamic Composition

A key design feature of the library is that a `Trail` can be modified **after its initial definition**.

This enables:
- conditional pipelines
- plugin-style extensions
- environment-specific behavior

Common operations include:
- inserting steps before or after others
- replacing existing steps
- removing steps entirely

This model allows users to extend behavior **without copying or rewriting pipelines**.

---

## Recommended Extension Patterns

### Factory Functions for Trails

Instead of instantiating trails inline, prefer using factory functions:

- improves readability
- enables reuse
- centralizes configuration

### Small, Composable Steps

Steps should be:
- single-purpose
- easily reorderable
- independent whenever possible

This maximizes flexibility when modifying trails dynamically.

---

## Separation of Theory and Practice

This document intentionally focuses on **architecture and design principles**.

A full, step-by-step implementation — including:
- a custom footprint
- multiple step types
- trail composition and execution
- metadata inspection

is available in the companion notebook:

📘 **Practical Example Notebook**  
[`examples/text_cleaning_pipeline.ipynb`](../examples/text_cleaning.ipynb)

Reading both together is strongly recommended.