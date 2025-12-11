"""
Metadata for the TRACCIA package.

By default this module tries to read information from the project's
`pyproject.toml` so that there is a single source of truth for things
like version, description, author, etc.

If `pyproject.toml` is not available at runtime (e.g. in some installed
environments), it falls back to reasonable defaults.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Mapping, Optional


@dataclass(frozen=True)
class PackageMetadata:
    title: str = "TRACCIA"
    version: str = "0.0.0"
    description: str = ""
    url: str = ""
    author: str = ""
    author_email: str = ""
    license: str = ""


def _load_pyproject() -> Optional[Mapping[str, Any]]:
    """Attempt to load pyproject.toml located at the project root."""
    import pathlib

    # This file lives in `traccia/__about__.py`
    here = pathlib.Path(__file__).resolve()
    # Project root = one level up from the package folder
    project_root = here.parent.parent
    pyproject_path = project_root / "pyproject.toml"

    if not pyproject_path.is_file():
        return None

    try:
        # Python 3.11+ has tomllib in the stdlib
        import tomllib  # type: ignore[attr-defined]

        with pyproject_path.open("rb") as f:
            return tomllib.load(f)
    except Exception:
        # Any error (no tomllib, parse error, etc.) → treat as missing
        return None


def _parse_metadata(data: Mapping[str, Any]) -> PackageMetadata:
    project = data.get("project") or {}

    title = str(project.get("name", "TRACCIA"))
    version = str(project.get("version", "0.0.0"))
    description = str(project.get("description", ""))

    # license can be { text = "MIT" } or { file = "LICENSE" } etc.
    license_field = project.get("license") or {}
    license_text = ""
    if isinstance(license_field, dict):
        license_text = str(
            license_field.get("text")
            or license_field.get("file")
            or ""
        )

    # authors = [{ name = "...", email = "..." }, ...]
    authors = project.get("authors") or []
    author_name = ""
    author_email = ""
    if isinstance(authors, list) and authors:
        first = authors[0] or {}
        if isinstance(first, dict):
            author_name = str(first.get("name", "") or "")
            author_email = str(first.get("email", "") or "")

    # urls = { "Homepage" = "...", "Source" = "...", ... }
    urls: Dict[str, Any] = project.get("urls") or {}
    url = ""
    if isinstance(urls, dict):
        url = str(
            urls.get("Homepage")
            or urls.get("Source")
            or urls.get("Repository")
            or ""
        )

    return PackageMetadata(
        title=title,
        version=version,
        description=description,
        url=url,
        author=author_name,
        author_email=author_email,
        license=license_text,
    )


def _load_metadata() -> PackageMetadata:
    data = _load_pyproject()
    if not data:
        # Fallback defaults if pyproject.toml is not available at runtime
        return PackageMetadata()
    try:
        return _parse_metadata(data)
    except Exception:
        # In case of unexpected structure, don't break imports
        return PackageMetadata()


_meta = _load_metadata()

__title__ = _meta.title
__version__ = _meta.version
__description__ = _meta.description
__url__ = _meta.url
__author__ = _meta.author
__author_email__ = _meta.author_email
__license__ = _meta.license

__all__ = [
    "__title__",
    "__version__",
    "__description__",
    "__url__",
    "__author__",
    "__author_email__",
    "__license__",
    "PackageMetadata",
]