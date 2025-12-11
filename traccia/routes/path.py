# traccia/concretes/path.py
from __future__ import annotations

from typing import Generic, List, TypeVar

from ..interfaces.footprint import Footprint
from ..interfaces.footstep import Footstep

F = TypeVar("F", bound=Footprint)


class Path(Generic[F]):
    """
    Abstract base class representing a TRACCIA Path, i.e. a pipeline
    that orchestrates a sequence of Footsteps on a shared Footprint.

    This Path follows a Chain of Responsibility philosophy:
      - it wires an ordered list of Footsteps into a chain using the
        internal `_set_next` hook;
      - `run(...)` triggers ONLY the first Footstep in the chain;
      - each Footstep is then responsible for delegating to the next
        one (if any), so the rest of the process happens "automatically".

    The Path itself:
      - handles high-level metadata at the beginning and end of the run,
      - exposes a simple, single entry point (`run`) for the whole chain.
    """

    def __init__(
        self,
        *footsteps: Footstep[F],
        name: str | None = None,
        run_id: str | None = None,
    ) -> None:
        """
        Initialize the Path with an ordered list of Footsteps.

        Args:
            *footsteps:
                The footsteps that will be chained in the given order.
            name:
                Optional human-readable name for this Path. Defaults to
                the concrete class name.
            run_id:
                Optional identifier for this particular run or pipeline
                configuration. If provided, it will be written into the
                Footprint metadata when `run` is called.
        """
        self._name: str = name or self.__class__.__name__
        self._run_id: str | None = run_id
        self._footsteps: List[Footstep[F]] = list(footsteps)

        self._link_chain()

    # ---------------------------------------------------------------------
    # Introspection
    # ---------------------------------------------------------------------

    @property
    def name(self) -> str:
        """
        Human-readable name of this Path.
        """
        return self._name

    @property
    def footsteps(self) -> tuple[Footstep[F], ...]:
        """
        Immutable view of the footsteps that compose this Path.
        """
        return tuple(self._footsteps)

    # ---------------------------------------------------------------------
    # Internal wiring (Chain of Responsibility)
    # ---------------------------------------------------------------------

    def _link_chain(self) -> None:
        """
        Wire the internal sequence of footsteps into a chain using each
        Footstep's `_set_next` hook.

        After this method:
          - footsteps[0] will delegate to footsteps[1],
          - footsteps[1] will delegate to footsteps[2],
          - ...
          - the last Footstep will have no next Footstep (end of chain).

        Concrete Path implementations may override this method if they
        need different routing, but the default is a simple linear chain.
        """
        if not self._footsteps:
            return

        prev = self._footsteps[0]
        for current in self._footsteps[1:]:
            prev._set_next(current)  # type: ignore[attr-defined]
            prev = current
        # Last footstep keeps its `_next_footstep` as None.

    # ---------------------------------------------------------------------
    # Metadata API (pipeline-level)
    # ---------------------------------------------------------------------

    def enrich_metadata(self, footprint: F) -> None:
        """
        Pipeline-level hook to update the Footprint's metadata before
        executing the chain.

        Default behavior:
          - if a `run_id` was provided, write it into the metadata;
          - add a `"path"` tag with this Path's name.

        Concrete Paths may override this method to add more pipeline-level
        information (e.g. environment, version, configuration hash), but
        are encouraged to call `super().enrich_metadata(footprint)` to
        preserve the default behavior.
        """
        meta = footprint.get_metadata()

        if self._run_id is not None:
            meta.run_id = self._run_id

        meta.add_tag("path", self.name)

    # ---------------------------------------------------------------------
    # Execution API
    # ---------------------------------------------------------------------

    def run(self, footprint: F) -> F:
        """
        Execute the Path on the given Footprint.

        Chain-of-Responsibility philosophy:
          - This method only triggers the FIRST Footstep in the chain.
          - It is the responsibility of each Footstep to call the next
            one (if any), so the rest of the process happens implicitly.

        Execution flow:
          1. Obtain the metadata from the Footprint.
          2. Enrich metadata with pipeline-level information.
          3. Record the start timestamp via `mark_started()` if not set.
          4. If there is at least one Footstep, call the first one:
                footsteps[0](footprint)
             and let the chain propagate.
          5. Once the whole chain has completed and control returns here,
             record the end timestamp via `mark_finished()`.
          6. Return the (mutated) Footprint.
        """
        meta = footprint.get_metadata()

        # 1–2. Pipeline-level metadata enrichment.
        self.enrich_metadata(footprint)

        # 3. Mark the beginning of the journey if not already started.
        if meta.started_at is None:
            meta.mark_started()

        # 4. Trigger only the first footstep; the rest of the chain is
        #    expected to be handled by the footsteps themselves.
        if self._footsteps:
            result = self._footsteps[0](footprint)
        else:
            result = footprint

        # 5. After the whole chain has run, record the end timestamp.
        meta.mark_finished()

        # 6. Return the final footprint.
        return result