# **T.R.A.C.C.I.A.**

**Transformation & Reactive Actions Chain-based Component Integration Architecture**

**TRACCIA** is a lightweight and extensible Python framework for building modular and domain-agnostic pipelines using a clean and expressive Chain of Responsibility architecture.

**TRACCIA** is built around a simple idea:
a *Footprint* (your data or state) is passed through a sequence of *Footsteps* (processing units), forming a *Path* - a modular and composable pipeline where every step can transform, enrich, or react to the incoming payload.
The framework provides a clean structure for chaining operations, tracking execution metadata, and building expressive workflows using the Chain of Responsibility pattern.

## **Installation**

### **From GitHub (latest version)**

```bash
pip install "git+https://github.com/emanuelegaliano/TRACCIA.git"
```

Install a specific tag or branch:

```bash
pip install "git+https://github.com/emanuelegaliano/TRACCIA.git@v0.1.0"
```