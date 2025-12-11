# traccia/interfaces/footprint.py
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Protocol, runtime_checkable


@dataclass
class FootprintMetadata:
    """
    Standardized metadata attached to a Footprint as it travels
    through a TRACCIA pipeline.

    This structure is meant to be shared across all Footprint
    implementations so that handlers, loggers, and monitoring tools
    can rely on a common shape for metadata.

    Fields:
        run_id:
            Optional identifier for the current pipeline execution.
            Can be used to correlate logs or external monitoring data.

        created_at:
            Timestamp when this metadata instance was created.
            Typically corresponds to the moment the Footprint is initialized.

        started_at:
            Optional timestamp for when the pipeline (or a specific
            execution) actually started processing this Footprint.

        finished_at:
            Optional timestamp for when the pipeline (or a specific
            execution) finished processing this Footprint.

        handlers:
            Ordered list of handler names that have processed this
            Footprint so far. Handlers are expected to append their
            own name when they successfully run.

        tags:
            Lightweight string-based tags for quick classification
            or filtering (e.g. {"environment": "dev", "mode": "debug"}).

        extra:
            Free-form additional metadata. This is the place for
            arbitrary, non-structured information that does not fit
            the other fields but is still relevant for debugging or
            auditing.
    """

    run_id: str | None = None

    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: datetime | None = None
    finished_at: datetime | None = None

    handlers: list[str] = field(default_factory=list)
    tags: dict[str, str] = field(default_factory=dict)
    extra: dict[str, Any] = field(default_factory=dict)

    # --- Convenience methods ---------------------------------------------

    def mark_started(self, when: datetime | None = None) -> None:
        """
        Mark the footprint as having started its pipeline journey.

        If `when` is not provided, the current UTC time is used.
        """
        self.started_at = when or datetime.now(timezone.utc)

    def mark_finished(self, when: datetime | None = None) -> None:
        """
        Mark the footprint as having finished its pipeline journey.

        If `when` is not provided, the current UTC time is used.
        """
        self.finished_at = when or datetime.now(timezone.utc)

    def add_handler(self, handler_name: str) -> None:
        """
        Append the given handler name to the handlers history.

        Handlers are encouraged to call this once they have
        successfully processed the footprint.
        """
        self.handlers.append(handler_name)

    def add_tag(self, key: str, value: str) -> None:
        """
        Add or update a string-based tag.
        """
        self.tags[key] = value

    def add_extra(self, key: str, value: Any) -> None:
        """
        Add or update an entry in the free-form extra metadata.
        """
        self.extra[key] = value

    def to_dict(self) -> dict[str, Any]:
        """
        Return a JSON-serializable representation of this metadata.

        Datetime fields are converted to ISO 8601 strings. All other
        fields are returned as-is, assuming they are themselves
        serializable or will be handled downstream.
        """
        return {
            "run_id": self.run_id,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "handlers": list(self.handlers),
            "tags": dict(self.tags),
            "extra": dict(self.extra),
        }


@runtime_checkable
class Footprint(Protocol):
    """
    Core protocol for the shared state that moves along a TRACCIA pipeline.

    A Footprint instance represents the mutable, shared state that each
    handler receives, possibly mutates, and passes along. While the
    concrete structure of the state is intentionally left to the user,
    all implementations MUST expose a standardized metadata object.

    This is achieved through the `get_metadata()` method, which returns
    a `FootprintMetadata` instance. This gives all handlers and tooling
    a common place to:
      - inspect execution history,
      - attach tags,
      - record timestamps,
      - store debugging or auditing information.

    Typical usage in handlers:

        def process(self, footprint: Footprint) -> Footprint:
            meta = footprint.get_metadata()
            meta.add_handler(self.name)
            # ... do the actual work ...
            return footprint

    Implementors are free to store the metadata internally in whatever
    way they find convenient (attribute, internal dict, etc.), as long
    as successive calls to `get_metadata()` return the same object
    for a given Footprint instance.
    """

    def get_metadata(self) -> FootprintMetadata:
        """
        Return the `FootprintMetadata` associated with this footprint.

        Implementations must guarantee that:
          - The same metadata instance is returned for the lifetime
            of this footprint object.
          - The metadata object is mutable, so handlers can enrich it
            over time without replacing it.
        """
        ...