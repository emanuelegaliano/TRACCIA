# traccia/concretes/path.py
from __future__ import annotations

from typing import TypeVar

from ..interfaces.footprint import Footprint
from ..interfaces.footstep import Footstep
from ..routes.path import Path

F = TypeVar("F", bound=Footprint)

class Trail(Path[F]):
    """
    User-friendly, fluent pipeline built on top of `Path`.

    A Trail is a concrete, configurable Path with additional utilities:

      - Fluent construction:
          - `then(step1, step2, ...)`
          - `insert_before("StepName", ...)`
          - `insert_after("StepName", ...)`
          - `remove("StepName")`
          - `replace("OldStepName", new_step)`

      - Metadata helpers:
          - `with_run_id("run-123")` (clone with a different run id)
          - `with_tag("env", "dev")` (pipeline-level default tags)
          - `describe()` / `pretty()` for human-readable inspection

      - Debug / validation helpers:
          - `validate_chain()` to check consistency of the chain
          - `dry_run(footprint)` to simulate a run without executing
            business logic (only metadata enrichment)
          - `trace(enabled=True)` to emit simple console logs during run

    It is intended as the main entry point for end users building
    TRACCIA-based pipelines.
    """

    def __init__(
        self,
        *footsteps: Footstep[F],
        name: str | None = None,
        run_id: str | None = None,
        default_tags: dict[str, str] | None = None,
    ) -> None:
        """
        Initialize a Trail with an ordered list of footsteps.

        Args:
            *footsteps:
                Initial footsteps that compose the Trail, in execution order.
            name:
                Optional human-readable name. Defaults to the class name.
            run_id:
                Optional run identifier. If set, it will be stored in the
                Footprint metadata when the Trail is run.
            default_tags:
                Optional dictionary of tags that will be applied at the
                pipeline level (via metadata) before execution.
        """
        super().__init__(*footsteps, name=name, run_id=run_id)
        self._default_tags: dict[str, str] = dict(default_tags or {})
        self._trace_enabled: bool = False

    # ------------------------------------------------------------------
    # Fluent construction / editing
    # ------------------------------------------------------------------

    def then(self, *footsteps: Footstep[F]) -> Trail[F]:
        """
        Append one or more footsteps to the end of this Trail, relinking
        the internal chain. Returns `self` to allow fluent usage.

        Example:
            trail = (
                Trail(step1, step2)
                .then(step3)
                .then(step4, step5)
            )
        """
        if footsteps:
            self._footsteps.extend(footsteps)
            self._link_chain()
        return self

    def _index_of(self, step_name: str) -> int | None:
        """
        Return the index of the first footstep whose `name` matches
        the given `step_name`, or None if not found.
        """
        for idx, step in enumerate(self._footsteps):
            if step.name == step_name:
                return idx
        return None

    def insert_before(self, step_name: str, *new_steps: Footstep[F]) -> Trail[F]:
        """
        Insert one or more footsteps BEFORE the first footstep with
        the given name. If no matching step is found, the Trail is
        left unchanged.

        Returns `self` for fluent chaining.
        """
        if not new_steps:
            return self

        idx = self._index_of(step_name)
        if idx is None:
            return self

        for offset, step in enumerate(new_steps):
            self._footsteps.insert(idx + offset, step)
        self._link_chain()
        return self

    def insert_after(self, step_name: str, *new_steps: Footstep[F]) -> Trail[F]:
        """
        Insert one or more footsteps AFTER the first footstep with
        the given name. If no matching step is found, the Trail is
        left unchanged.

        Returns `self` for fluent chaining.
        """
        if not new_steps:
            return self

        idx = self._index_of(step_name)
        if idx is None:
            return self

        insert_pos = idx + 1
        for offset, step in enumerate(new_steps):
            self._footsteps.insert(insert_pos + offset, step)
        self._link_chain()
        return self

    def remove(self, step_name: str) -> Trail[F]:
        """
        Remove the first footstep whose `name` matches `step_name`.
        If no such footstep exists, the Trail remains unchanged.

        Returns `self` for fluent chaining.
        """
        idx = self._index_of(step_name)
        if idx is None:
            return self

        del self._footsteps[idx]
        self._link_chain()
        return self

    def replace(self, step_name: str, *new_steps: Footstep[F]) -> Trail[F]:
        """
        Replace the first footstep whose `name` matches `step_name`
        with one or more new footsteps.

        If no such footstep exists, the Trail remains unchanged.

        Returns `self` for fluent chaining.
        """
        if not new_steps:
            return self

        idx = self._index_of(step_name)
        if idx is None:
            return self

        # Remove the old step and insert the new ones in its place.
        del self._footsteps[idx]
        for offset, step in enumerate(new_steps):
            self._footsteps.insert(idx + offset, step)
        self._link_chain()
        return self

    # ------------------------------------------------------------------
    # Metadata / configuration helpers
    # ------------------------------------------------------------------

    def with_run_id(self, run_id: str) -> Trail[F]:
        """
        Return a NEW Trail instance with the same footsteps, name and
        default tags, but with a different run_id.

        Useful for reusing a trail definition across multiple runs.
        """
        clone = Trail(
            *self._footsteps,
            name=self.name,
            run_id=run_id,
            default_tags=self._default_tags,
        )
        clone._trace_enabled = self._trace_enabled
        return clone

    def with_tag(self, key: str, value: str) -> Trail[F]:
        """
        Add or update a default pipeline-level tag that will be applied
        to the Footprint metadata when the Trail is run.

        Returns `self` for fluent chaining.
        """
        self._default_tags[key] = value
        return self

    def enrich_metadata(self, footprint: F) -> None:
        """
        Override of Path.enrich_metadata.

        In addition to the base behavior (run_id + "path" tag), this
        also applies any default tags configured on the Trail.
        """
        super().enrich_metadata(footprint)
        meta = footprint.get_metadata()
        for key, value in self._default_tags.items():
            meta.add_tag(key, value)

    # ------------------------------------------------------------------
    # Debug / validation / inspection
    # ------------------------------------------------------------------

    def trace(self, enabled: bool = True) -> Trail[F]:
        """
        Enable or disable simple console tracing for this Trail.

        When tracing is enabled, `run()` and `dry_run()` will emit
        basic messages to stdout before and after each step.
        """
        self._trace_enabled = enabled
        return self

    def describe(self) -> dict[str, object]:
        """
        Return a structured description of this Trail, including:
          - name
          - run_id
          - number of footsteps
          - list of footstep names
          - default tags
        """
        return {
            "name": self.name,
            "run_id": getattr(self, "_run_id", None),
            "footstep_count": len(self._footsteps),
            "footsteps": [step.name for step in self._footsteps],
            "default_tags": dict(self._default_tags),
        }

    def pretty(self) -> str:
        """
        Return a human-readable, multi-line string describing this Trail.
        """
        desc = self.describe()
        lines: list[str] = [
            f"Trail: {desc['name']}",
            f"  run_id: {desc['run_id']}",
            f"  footsteps ({desc['footstep_count']}):",
        ]
        for idx, step_name in enumerate(desc["footsteps"]):  # type: ignore[arg-type]
            lines.append(f"    {idx + 1}. {step_name}")
        if desc["default_tags"]:
            lines.append("  default tags:")
            for k, v in desc["default_tags"].items():  # type: ignore[union-attr]
                lines.append(f"    - {k} = {v}")
        return "\n".join(lines)

    def validate_chain(self) -> list[str]:
        """
        Perform basic validation checks on the Trail and return a list
        of warning/error messages. An empty list means no issues have
        been detected at this level.

        Checks performed:
          - Trail has at least one footstep.
          - The chain defined by `_next_footstep` (if used) is
            consistent with the internal order of `_footsteps`.
        """
        issues: list[str] = []

        if not self._footsteps:
            issues.append("Trail has no footsteps.")

        # Optional: validate that the `_next_footstep` chain is consistent.
        if self._footsteps:
            visited: list[Footstep[F]] = []
            current: Footstep[F] | None = self._footsteps[0]
            while current is not None:
                visited.append(current)
                current = getattr(current, "_next_footstep", None)  # type: ignore[assignment]

            if len(visited) != len(self._footsteps):
                issues.append(
                    "Mismatch between internal footsteps list and "
                    "_next_footstep chain length."
                )
            else:
                # They should be in the same order.
                for a, b in zip(self._footsteps, visited):
                    if a is not b:
                        issues.append(
                            "Order mismatch between internal footsteps list and "
                            "_next_footstep chain."
                        )
                        break

        return issues

    # ------------------------------------------------------------------
    # Execution variants
    # ------------------------------------------------------------------

    def dry_run(self, footprint: F) -> F:
        """
        Simulate a run of this Trail without executing the business logic
        inside each Footstep.

        This method:
          - enriches metadata at the pipeline level,
          - initializes `started_at` if needed,
          - calls `enrich_metadata` on each Footstep (but NOT `run`),
          - updates `finished_at` at the end.

        This is useful for debugging, testing metadata behavior, or
        documenting execution order without touching real data.
        """
        meta = footprint.get_metadata()

        # Pipeline-level metadata enrichment.
        self.enrich_metadata(footprint)

        # Mark the beginning of the journey if not already started.
        if meta.started_at is None:
            meta.mark_started()

        # Step-level metadata enrichment only (no business logic).
        for step in self._footsteps:
            if self._trace_enabled:
                print(f"[TRACCIA][dry-run] entering {step.name}")
            step.enrich_metadata(footprint)
            if self._trace_enabled:
                print(f"[TRACCIA][dry-run] leaving  {step.name}")

        # Mark the end of the journey.
        meta.mark_finished()
        return footprint

    # Override run to add optional tracing, but keep Path semantics.
    def run(self, footprint: F) -> F:
        """
        Execute the Trail on the given Footprint, with optional console
        tracing if enabled.

        This behaves like `Path.run`, but emits simple messages when
        tracing is turned on via `trace(True)`.
        """
        if self._trace_enabled:
            print(f"[TRACCIA] Trail '{self.name}' starting run")

        result = super().run(footprint)

        if self._trace_enabled:
            meta = result.get_metadata()
            print(
                f"[TRACCIA] Trail '{self.name}' finished run "
                f"(handlers={meta.handlers})"
            )

        return result
