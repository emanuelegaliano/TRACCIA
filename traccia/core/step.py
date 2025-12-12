# traccia/core/step.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Generic, TypeVar

from traccia.interfaces.footprint import Footprint

F = TypeVar("F", bound=Footprint)


@dataclass(frozen=True, slots=True)
class Step(Generic[F]):
    """A named callable that records its execution in the footprint metadata."""

    name: str
    fn: Callable[[F], F]

    def __call__(self, footprint: F) -> F:
        try:
            footprint.get_metadata().add_handler(self.name)
        except Exception:
            # Metadata is best-effort; never break the step execution.
            pass
        return self.fn(footprint)


def step(name: str | None = None):
    """
    Decorator to create a Step from a function.

    Usage:
        @step()
        def my_step(fp): ...

        @step("custom_name")
        def my_step(fp): ...
    """

    def wrap(fn: Callable[[F], F]) -> Step[F]:
        return Step(name=name or getattr(fn, "__name__", "step"), fn=fn)

    return wrap