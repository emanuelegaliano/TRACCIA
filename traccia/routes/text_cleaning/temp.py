# example_text_cleaning_stats.py
"""
Simple TRACCIA example: text cleaning + stats.

Copy/paste this file into a notebook cell (or import it) and run.
It demonstrates:
- a custom Footprint holding state + metadata
- steps defined with @step()
- a Trail that runs the steps in order
- stats stored in metadata.extra
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from traccia import Footprint, Trail, FootprintMetadata, step


# ---------------------------------------------------------------------------
# Footprint
# ---------------------------------------------------------------------------

@dataclass
class TextFootprint(Footprint):
    """A minimal footprint carrying text plus standardized metadata."""
    text: str
    meta: FootprintMetadata = field(default_factory=FootprintMetadata)

    def get_metadata(self) -> FootprintMetadata:
        return self.meta


# ---------------------------------------------------------------------------
# Steps
# ---------------------------------------------------------------------------

@step()
def strip_text(fp: TextFootprint) -> TextFootprint:
    """Trim leading/trailing whitespace."""
    fp.text = fp.text.strip()
    return fp


@step()
def normalize_spaces(fp: TextFootprint) -> TextFootprint:
    """Collapse multiple whitespace into a single space."""
    fp.text = re.sub(r"\s+", " ", fp.text)
    return fp


@step()
def to_lower(fp: TextFootprint) -> TextFootprint:
    """Lowercase the text."""
    fp.text = fp.text.lower()
    return fp


@step()
def stats(fp: TextFootprint) -> TextFootprint:
    """
    Compute simple stats and store them in metadata.extra.
    """
    t = fp.text
    fp.get_metadata().add_extra("char_count", len(t))
    fp.get_metadata().add_extra("word_count", 0 if not t else len(t.split(" ")))
    fp.get_metadata().add_extra("is_empty", t == "")
    return fp


# ---------------------------------------------------------------------------
# Pipeline factory
# ---------------------------------------------------------------------------

def build_trail(*, run_id: str | None = None, trace: bool = False) -> Trail[TextFootprint]:
    """Create a ready-to-use pipeline."""
    return (
        Trail[TextFootprint](name="TextCleaning", run_id=run_id)
        .with_tag("example", "text-cleaning")
        .then(strip_text, normalize_spaces, to_lower, stats)
        .trace(trace)
    )


# ---------------------------------------------------------------------------
# Quick demo (safe to run in a notebook)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    trail = build_trail(run_id="demo-001", trace=True)

    fp = TextFootprint("   Ciao   MONDO!\nCome   va?   ")
    out = trail.run(fp)

    print("\n--- Result ---")
    print("text:", out.text)
    print("handlers:", out.get_metadata().handlers)
    print("tags:", out.get_metadata().tags)
    print("extra:", out.get_metadata().extra)

    # dry_run demo (metadata only, no text mutation)
    fp2 = TextFootprint("   Another   TEXT   ")
    trail.dry_run(fp2)
    print("\n--- Dry run (no text changes) ---")
    print("text:", fp2.text)
    print("handlers:", fp2.get_metadata().handlers)
    print("extra:", fp2.get_metadata().extra)
