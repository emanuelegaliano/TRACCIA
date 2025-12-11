# traccia/interfaces/footstep.py
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from .footprint import Footprint

F = TypeVar("F", bound=Footprint)


class Footstep(Generic[F], ABC):
    """
    Abstract base class representing a single node (step) in a TRACCIA pipeline.

    A Footstep receives a Footprint, performs some work (read/transform/enrich),
    and returns the same Footprint instance (typically mutated), or in advanced
    scenarios, a compatible Footprint.

    The actual chaining and orchestration of footsteps is handled cooperatively
    by the Path (which wires the chain) and by this base class (which forwards
    to the next footstep when present).

    Design goals:
      - Minimal and easy to subclass.
      - Generic over the concrete Footprint type (F).
      - Provides a `name` for introspection, logging and metadata.
      - Provides a standard hook (`enrich_metadata`) that can be overridden.
      - Provides a template method (`execute`) for business logic, while
        `run` takes care of chaining to the next Footstep.
    """

    def __init__(self, name: str | None = None) -> None:
        """
        Initialize the footstep with an optional human-readable name.

        If no name is provided, the concrete class name is used.
        """
        self._name: str = name or self.__class__.__name__
        self._next_footstep: Footstep[F] | None = None

    @property
    def name(self) -> str:
        """
        Human-readable name of this footstep.

        This is intended for:
          - logging,
          - debugging,
          - storing execution history in the Footprint metadata.

        Subclasses generally do not need to override this property.
        """
        return self._name

    # ---------------------------------------------------------------------
    # Template-style API
    # ---------------------------------------------------------------------

    def enrich_metadata(self, footprint: F) -> None:
        """
        Standard hook to update the Footprint's metadata before running
        the actual business logic.

        Default behavior:
          - retrieve the metadata via `footprint.get_metadata()`;
          - register this footstep's name into the handlers history.

        Subclasses may override this method to customize how metadata
        is enriched (e.g. adding tags, timestamps, custom fields), but
        are encouraged to call `super().enrich_metadata(footprint)` to
        preserve the default behavior.
        """
        meta = footprint.get_metadata()
        meta.add_handler(self.name)

    @abstractmethod
    def execute(self, footprint: F) -> F:
        """
        Core business logic for this footstep.

        This method is responsible for:
          - reading from the Footprint,
          - mutating or enriching it as needed,
          - returning the (typically same) Footprint instance.

        IMPORTANT:
          - `execute` MUST NOT call the next footstep in the chain.
            Chaining is handled centrally by `run`, to keep behavior
            consistent across all footsteps.
        """
        ...

    def run(self, footprint: F) -> F:
        """
        Execute this footstep and, if present, the rest of the chain.

        Execution flow:
          1. Call `execute(footprint)` to perform this step's logic.
          2. If a next footstep has been wired via `_set_next`, forward
             the resulting Footprint to `next.run(result)` (which will
             in turn propagate along the chain).
          3. If there is no next footstep, return the result as-is.

        This method should generally not be overridden by subclasses:
        override `execute` for business logic and `enrich_metadata`
        for metadata customization.
        """
        result = self.execute(footprint)

        if self._next_footstep is not None:
            return self._next_footstep.run(result)

        return result

    def __call__(self, footprint: F) -> F:
        """
        Entry point for executing this footstep on a Footprint.

        This method:
          1. Enriches the metadata using `enrich_metadata(footprint)`.
          2. Runs the chain starting from this footstep via `run(footprint)`.

        Pipelines and user code are encouraged to call the Footstep
        instance directly (`footstep(footprint)`) instead of calling
        `run()` manually, so that metadata enrichment always happens.
        """
        self.enrich_metadata(footprint)
        return self.run(footprint)

    def _set_next(self, next_footstep: Footstep[F] | None) -> None:
        """
        Internal method to set the next footstep in the pipeline.

        This method is intended for use by Path implementations that
        manage footstep chaining. It is not part of the public Footstep
        API and should not be called by user code.
        """
        self._next_footstep = next_footstep