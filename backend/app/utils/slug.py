import re
import sqlite3

def generate_base_slug(text: str) -> str:
    """Convert arbitrary text into a safe, clean, hyphenated slug."""
    if not text:
        return "untitled"
    # Lowercase
    slug = text.lower().strip()
    # Replace non-alphanumeric chars with hyphens
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    # Collapse multiple hyphens
    slug = re.sub(r"-+", "-", slug)
    # Trim hyphens from edges
    slug = slug.strip("-")
    return slug or "untitled"

def generate_unique_slug(conn: sqlite3.Connection, text: str, current_published_id: int | None = None) -> str:
    """
    Generate a unique slug based on title text, querying published_content table for collisions.
    Appends -2, -3, etc. if collisions exist.
    """
    base_slug = generate_base_slug(text)
    candidate_slug = base_slug
    counter = 2

    while True:
        if current_published_id:
            row = conn.execute(
                "SELECT id FROM published_content WHERE slug = ? AND id != ?",
                (candidate_slug, current_published_id)
            ).fetchone()
        else:
            row = conn.execute(
                "SELECT id FROM published_content WHERE slug = ?",
                (candidate_slug,)
            ).fetchone()

        if not row:
            return candidate_slug

        candidate_slug = f"{base_slug}-{counter}"
        counter += 1
