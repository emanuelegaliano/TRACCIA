# traccia/core/trail.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Generic, TypeVar

from traccia.core.step import Step
from traccia.interfaces.footprint import Footprint

F = TypeVar("F", bound=Footprint)


@dataclass(slots=True)
class Trail(Generic[F]):
    """
    A user-friendly, fluent pipeline.

    Intentionally simple: a Trail is just an ordered list of Steps.
    Execution is a plain `for` loop.
    """

    steps: list[Step[F]] = field(default_factory=list)
    name: str = "Trail"
    run_id: str | None = None
    default_tags: dict[str, str] = field(default_factory=dict)
    trace_enabled: bool = False

    # ------------------------------------------------------------------
    # Fluent construction / editing
    # ------------------------------------------------------------------

    def then(self, *steps: Step[F]) -> "Trail[F]":
        """Append one or more steps to the end of this Trail."""
        if steps:
            self.steps.extend(steps)
        return self

    def _index_of(self, step_name: str) -> int | None:
        """Return the index of the first step with the given name, or None."""
        for i, s in enumerate(self.steps):
            if s.name == step_name:
                return i
        return None

    def insert_before(self, step_name: str, *new_steps: Step[F]) -> "Trail[F]":
        """Insert steps before the first step matching `step_name`."""
        if not new_steps:
            return self
        idx = self._index_of(step_name)
        if idx is None:
            return self
        for offset, s in enumerate(new_steps):
            self.steps.insert(idx + offset, s)
        return self

    def insert_after(self, step_name: str, *new_steps: Step[F]) -> "Trail[F]":
        """Insert steps after the first step matching `step_name`."""
        if not new_steps:
            return self
        idx = self._index_of(step_name)
        if idx is None:
            return self
        insert_pos = idx + 1
        for offset, s in enumerate(new_steps):
            self.steps.insert(insert_pos + offset, s)
        return self

    def remove(self, step_name: str) -> "Trail[F]":
        """Remove the first step matching `step_name`."""
        idx = self._index_of(step_name)
        if idx is None:
            return self
        del self.steps[idx]
        return self

    def replace(self, step_name: str, *new_steps: Step[F]) -> "Trail[F]":
        """Replace the first step matching `step_name` with one or more steps."""
        if not new_steps:
            return self
        idx = self._index_of(step_name)
        if idx is None:
            return self
        del self.steps[idx]
        for offset, s in enumerate(new_steps):
            self.steps.insert(idx + offset, s)
        return self

    # ------------------------------------------------------------------
    # Metadata / configuration helpers
    # ------------------------------------------------------------------

    def with_run_id(self, run_id: str | None) -> "Trail[F]":
        """Set the run id and return self (fluent)."""
        self.run_id = run_id
        return self

    def with_tag(self, key: str, value: str) -> "Trail[F]":
        """Set a default pipeline tag and return self (fluent)."""
        self.default_tags[key] = value
        return self

    def trace(self, enabled: bool = True) -> "Trail[F]":
        """Enable/disable simple stdout tracing during run/dry_run."""
        self.trace_enabled = enabled
        return self

    # ------------------------------------------------------------------
    # Inspection / validation
    # ------------------------------------------------------------------

    def describe(self) -> dict[str, object]:
        """Return a structured description of this Trail."""
        return {
            "name": self.name,
            "run_id": self.run_id,
            "step_count": len(self.steps),
            "steps": [s.name for s in self.steps],
            "default_tags": dict(self.default_tags),
            "trace_enabled": self.trace_enabled,
        }

    def pretty(self) -> str:
        """Return a human-readable multi-line description."""
        lines: list[str] = [
            f"Trail: {self.name}",
            f"  run_id: {self.run_id}",
            f"  steps ({len(self.steps)}):",
        ]
        for i, s in enumerate(self.steps):
            lines.append(f"    {i + 1}. {s.name}")

        if self.default_tags:
            lines.append("  default tags:")
            for k, v in self.default_tags.items():
                lines.append(f"    - {k} = {v}")

        lines.append(f"  trace: {self.trace_enabled}")
        return "\n".join(lines)

    def validate(self) -> list[str]:
        """Perform basic checks and return a list of issues (empty == ok)."""
        issues: list[str] = []
        if not self.steps:
            issues.append("Trail has no steps.")

        names = [s.name for s in self.steps]
        if len(set(names)) != len(names):
            issues.append("Trail contains duplicate step names. Consider making them unique.")

        return issues

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    def _enrich_pipeline_metadata(self, footprint: F) -> None:
        """Apply pipeline-level metadata (run_id, tags, trail name)."""
        meta = footprint.get_metadata()

        if self.run_id is not None:
            meta.run_id = self.run_id

        meta.add_tag("trail", self.name)

        for k, v in self.default_tags.items():
            meta.add_tag(k, v)

    def dry_run(self, footprint: F) -> F:
        """
        Simulate a run without executing step business logic.

        It only enriches metadata and appends step names to handlers.
        """
        meta = footprint.get_metadata()
        self._enrich_pipeline_metadata(footprint)

        if meta.started_at is None:
            meta.mark_started()

        try:
            for s in self.steps:
                if self.trace_enabled:
                    print(f"[TRACCIA][dry-run] -> {s.name}")
                meta.add_handler(s.name)
        finally:
            meta.mark_finished()

        return footprint

    def run(self, footprint: F) -> F:
        """Execute the Trail against the given footprint."""
        meta = footprint.get_metadata()
        self._enrich_pipeline_metadata(footprint)

        if meta.started_at is None:
            meta.mark_started()

        if self.trace_enabled:
            print(f"[TRACCIA] Trail '{self.name}' starting")

        try:
            for s in self.steps:
                if self.trace_enabled:
                    print(f"[TRACCIA] -> {s.name}")
                footprint = s(footprint)
        finally:
            meta.mark_finished()

        if self.trace_enabled:
            print(f"[TRACCIA] Trail '{self.name}' finished (handlers={meta.handlers})")

        return footprint