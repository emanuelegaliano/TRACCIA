# traccia/interfaces/footprint.py
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Protocol, runtime_checkable


def utc_now() -> datetime:
    """Return a timezone-aware UTC datetime."""
    return datetime.now(timezone.utc)


@dataclass(slots=True)
class FootprintMetadata:
    """
    Standard metadata attached to a Footprint while it flows through a pipeline.

    Keep this object small, predictable, and easy to serialize. Anything domain-
    specific can go into `extra`.
    """

    run_id: str | None = None

    # Always use timezone-aware UTC timestamps for consistency.
    created_at: datetime = field(default_factory=utc_now)
    started_at: datetime | None = None
    finished_at: datetime | None = None

    # Execution history
    handlers: list[str] = field(default_factory=list)

    # Lightweight string tags (good for filtering)
    tags: dict[str, str] = field(default_factory=dict)

    # Free-form metadata (debug info, counters, etc.)
    extra: dict[str, Any] = field(default_factory=dict)

    # --- Lifecycle ---------------------------------------------------------

    def mark_started(self, when: datetime | None = None, *, overwrite: bool = False) -> None:
        """
        Mark processing as started.

        By default this is idempotent (it won't overwrite an existing timestamp)
        unless `overwrite=True`.
        """
        if self.started_at is not None and not overwrite:
            return
        self.started_at = when or utc_now()

    def mark_finished(self, when: datetime | None = None, *, overwrite: bool = False) -> None:
        """
        Mark processing as finished.

        By default this is idempotent (it won't overwrite an existing timestamp)
        unless `overwrite=True`.
        """
        if self.finished_at is not None and not overwrite:
            return
        self.finished_at = when or utc_now()

    @property
    def duration_seconds(self) -> float | None:
        """
        Return processing duration in seconds, if both started_at and finished_at are set.
        """
        if self.started_at is None or self.finished_at is None:
            return None
        return (self.finished_at - self.started_at).total_seconds()

    # --- History / tagging -------------------------------------------------

    def add_handler(self, name: str) -> None:
        """Append a step/handler name to the execution history."""
        self.handlers.append(name)

    def add_tag(self, key: str, value: str) -> None:
        """Add or update a string tag."""
        self.tags[key] = value

    def add_extra(self, key: str, value: Any) -> None:
        """Add or update a free-form metadata entry."""
        self.extra[key] = value

    # --- Serialization -----------------------------------------------------

    def as_dict(self) -> dict[str, Any]:
        """
        Return a JSON-friendly representation.

        Datetimes are emitted as ISO 8601 strings.
        """
        return {
            "run_id": self.run_id,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "duration_seconds": self.duration_seconds,
            "handlers": list(self.handlers),
            "tags": dict(self.tags),
            "extra": dict(self.extra),
        }


@runtime_checkable
class Footprint(Protocol):
    """
    Shared mutable state that moves through a TRACCIA pipeline.

    A Footprint can be any user-defined object, but it MUST expose a stable
    FootprintMetadata instance via get_metadata().
    """

    def get_metadata(self) -> FootprintMetadata:
        """
        Return the metadata object associated with this Footprint.

        Requirements:
        - Must return the same object for the lifetime of the Footprint instance.
        - The returned metadata must be mutable and shared across steps.
        """
        ...