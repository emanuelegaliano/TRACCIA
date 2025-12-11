# traccia/interfaces/footstep.py
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from .footprint import Footprint, FootprintMetadata

F = TypeVar("F", bound=Footprint)


class Footstep(Generic[F], ABC):
    """
    Abstract base class representing a single node (step) in a TRACCIA pipeline.

    A Footstep receives a Footprint, performs some work (read/transform/enrich),
    and returns the same Footprint instance (typically mutated), or in advanced
    scenarios, a compatible Footprint.

    The actual chaining and orchestration of footsteps is the responsibility
    of the Pipeline implementation, not of the Footstep itself. This keeps
    each Footstep focused on *what* it does, not on *where* it goes next.

    Design goals:
      - Minimal and easy to subclass.
      - Generic over the concrete Footprint type (F).
      - Provides a `name` for introspection, logging and metadata.
      - Provides a standard hook (`enrich_metadata`) that can be overridden.
    """

    def __init__(self, name: str | None = None) -> None:
        """
        Initialize the footstep with an optional human-readable name.

        If no name is provided, the concrete class name is used.
        """
        self._name: str = name or self.__class__.__name__

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
    def run(self, footprint: F) -> F:
        """
        Execute this footstep on the given Footprint.

        Implementations should:
          - perform their domain-specific logic,
          - mutate or enrich the Footprint as needed,
          - return the (same) Footprint instance.

        Any exception-raising or error-handling behavior is left to the
        concrete implementation or to the orchestrating Pipeline.
        """
        ...

    def __call__(self, footprint: F) -> F:
        """
        Entry point for executing this footstep on a Footprint.

        This method:
          1. Enriches the metadata using `enrich_metadata(footprint)`.
          2. Runs the concrete logic via `run(footprint)`.

        Pipelines and user code are encouraged to call the Footstep
        instance directly (`footstep(footprint)`) instead of calling
        `run()` manually, so that metadata enrichment always happens.
        """
        self.enrich_metadata(footprint)
        return self.run(footprint)