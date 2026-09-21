import sqlite3

def init_db(conn: sqlite3.Connection) -> None:
    """Initialize all database tables and perform lightweight migrations."""
    conn.execute("PRAGMA foreign_keys = ON")

    # 1. products
    conn.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            description TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)

    # 2. keywords
    conn.execute("""
        CREATE TABLE IF NOT EXISTS keywords (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            keyword TEXT NOT NULL UNIQUE,
            search_volume INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)

    # 3. existing_content
    conn.execute("""
        CREATE TABLE IF NOT EXISTS existing_content (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            url TEXT NOT NULL,
            primary_keyword TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)

    # 4. research_runs
    conn.execute("""
        CREATE TABLE IF NOT EXISTS research_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            completed_at TEXT
        )
    """)

    # 5. content_opportunities
    conn.execute("""
        CREATE TABLE IF NOT EXISTS content_opportunities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            research_run_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            reason TEXT NOT NULL,
            primary_keyword TEXT,
            search_volume INTEGER NOT NULL,
            confidence TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TEXT NOT NULL DEFAULT '',
            evidence TEXT NOT NULL DEFAULT '[]',
            FOREIGN KEY (research_run_id)
                REFERENCES research_runs(id)
                ON DELETE CASCADE
        )
    """)

    # 6. content_briefs
    conn.execute("""
        CREATE TABLE IF NOT EXISTS content_briefs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            opportunity_id INTEGER NOT NULL UNIQUE,
            title TEXT NOT NULL,
            objective TEXT NOT NULL,
            primary_keyword TEXT,
            search_volume INTEGER NOT NULL,
            search_intent TEXT NOT NULL DEFAULT 'informational',
            target_audience TEXT NOT NULL DEFAULT 'General audience',
            suggested_sections TEXT NOT NULL DEFAULT '[]',
            suggested_angle TEXT NOT NULL DEFAULT '',
            related_keywords TEXT NOT NULL DEFAULT '[]',
            opportunity_evidence TEXT NOT NULL DEFAULT '[]',
            status TEXT NOT NULL DEFAULT 'draft',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL DEFAULT '',
            FOREIGN KEY (opportunity_id)
                REFERENCES content_opportunities(id)
                ON DELETE CASCADE
        )
    """)

    # 7. content_drafts
    conn.execute("""
        CREATE TABLE IF NOT EXISTS content_drafts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            brief_id INTEGER NOT NULL UNIQUE,
            title TEXT NOT NULL,
            primary_keyword TEXT,
            introduction TEXT NOT NULL,
            body TEXT NOT NULL,
            conclusion TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'draft',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL DEFAULT '',
            FOREIGN KEY (brief_id)
                REFERENCES content_briefs(id)
                ON DELETE CASCADE
        )
    """)

    # 8. published_content
    conn.execute("""
        CREATE TABLE IF NOT EXISTS published_content (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            draft_id INTEGER NOT NULL UNIQUE,
            title TEXT NOT NULL,
            slug TEXT NOT NULL UNIQUE,
            url TEXT NOT NULL,
            published_at TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'published',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (draft_id)
                REFERENCES content_drafts(id)
                ON DELETE CASCADE
        )
    """)

    # Migrate missing columns for tables that may already exist in an older schema
    _ensure_column(conn, "content_opportunities", "primary_keyword", "TEXT DEFAULT NULL")
    _ensure_column(conn, "content_opportunities", "status", "TEXT NOT NULL DEFAULT 'pending'")
    _ensure_column(conn, "content_opportunities", "created_at", "TEXT NOT NULL DEFAULT ''")
    _ensure_column(conn, "content_opportunities", "evidence", "TEXT NOT NULL DEFAULT '[]'")

    _ensure_column(conn, "content_briefs", "search_intent", "TEXT NOT NULL DEFAULT 'informational'")
    _ensure_column(conn, "content_briefs", "target_audience", "TEXT NOT NULL DEFAULT 'General audience'")
    _ensure_column(conn, "content_briefs", "suggested_sections", "TEXT NOT NULL DEFAULT '[]'")
    _ensure_column(conn, "content_briefs", "suggested_angle", "TEXT NOT NULL DEFAULT ''")
    _ensure_column(conn, "content_briefs", "related_keywords", "TEXT NOT NULL DEFAULT '[]'")
    _ensure_column(conn, "content_briefs", "opportunity_evidence", "TEXT NOT NULL DEFAULT '[]'")
    _ensure_column(conn, "content_briefs", "updated_at", "TEXT NOT NULL DEFAULT ''")

    _ensure_column(conn, "content_drafts", "updated_at", "TEXT NOT NULL DEFAULT ''")

    conn.commit()

def _ensure_column(conn: sqlite3.Connection, table: str, column: str, col_def: str) -> None:
    """Safely add a column to an existing table if it does not already exist."""
    cursor = conn.execute(f"PRAGMA table_info({table})")
    columns = [row[1] for row in cursor.fetchall()]
    if column not in columns:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_def}")
