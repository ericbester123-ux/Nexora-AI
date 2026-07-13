"""
Slug generation utility.

Produces URL-safe slugs from arbitrary strings, ensuring uniqueness by
appending a short suffix when a collision is detected.
"""

import re
import uuid


def slugify(value: str) -> str:
    """
    Convert an arbitrary string into a lowercase, URL-safe slug.

    Removes or replaces non-alphanumeric characters, collapses whitespace
    and dashes, and strips leading/trailing separators.

    Example:
        >>> slugify("  Hello   World!  ")
        'hello-world'
    """
    value = value.lower().strip()
    value = re.sub(r"[^\w\s-]", "", value)
    value = re.sub(r"[-\s]+", "-", value)
    return value.strip("-")


async def unique_slug(base: str, exists: callable, max_length: int = 120) -> str:
    """
    Generate a unique slug from *base* by appending a short suffix if needed.

    *exists* is an async callable ``exists(slug: str) -> bool`` that returns
    ``True`` when the slug is already taken.

    Example:
        >>> seen = {"hello-world"}
        >>> unique_slug("Hello World!", seen.__contains__)
        'hello-world-abc123'
    """
    raw = slugify(base)[:max_length]
    if not raw:
        raw = "untitled"

    candidate = raw
    while await exists(candidate):
        suffix = uuid.uuid4().hex[:6]
        candidate = f"{raw[: max_length - 7]}-{suffix}"

    return candidate
