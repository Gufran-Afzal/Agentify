import sqlite3

def init_db(conn: sqlite3.Connection) -> None:
    """Initialize all database tables and perform lightweight migrations.

    Existing tables are never dropped — all changes use CREATE TABLE IF NOT EXISTS
    or the _ensure_column() helper. This means running init_db() on an existing
    database is always safe.
    """
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

    # -------------------------------------------------------------------------
    # New tables — Phase 3 additions (never destroy existing data)
    # -------------------------------------------------------------------------

    # 9. stores — multi-tenant store model
    conn.execute("""
        CREATE TABLE IF NOT EXISTS stores (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            domain TEXT NOT NULL DEFAULT '',
            platform TEXT NOT NULL DEFAULT 'demo',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)

    # 10. store_connections — external platform credentials (reference only — never raw secrets)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS store_connections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            store_id TEXT NOT NULL,
            provider TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            credentials_reference TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (store_id) REFERENCES stores(id) ON DELETE CASCADE
        )
    """)

    # 11. research_actions — every action taken in a research run (audit trail)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS research_actions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            research_run_id INTEGER NOT NULL,
            action_type TEXT NOT NULL,
            arguments TEXT NOT NULL DEFAULT '{}',
            result TEXT NOT NULL DEFAULT '{}',
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TEXT NOT NULL,
            completed_at TEXT,
            FOREIGN KEY (research_run_id)
                REFERENCES research_runs(id)
                ON DELETE CASCADE
        )
    """)

    # 12. research_evidence — every evidence item collected during a run
    conn.execute("""
        CREATE TABLE IF NOT EXISTS research_evidence (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            research_run_id INTEGER,
            store_id TEXT NOT NULL DEFAULT 'demo-store',
            source_type TEXT NOT NULL,
            source_reference TEXT NOT NULL DEFAULT '',
            evidence_type TEXT NOT NULL,
            data TEXT NOT NULL DEFAULT '{}',
            reliability REAL NOT NULL DEFAULT 1.0,
            created_at TEXT NOT NULL
        )
    """)

    # 13. competitors — discovered competitor domains
    conn.execute("""
        CREATE TABLE IF NOT EXISTS competitors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            store_id TEXT NOT NULL DEFAULT 'demo-store',
            domain TEXT NOT NULL,
            name TEXT NOT NULL DEFAULT '',
            category TEXT NOT NULL DEFAULT 'content_competitor',
            status TEXT NOT NULL DEFAULT 'discovered',
            discovery_reason TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)

    # 14. competitor_pages — individual pages analyzed from competitor sites
    conn.execute("""
        CREATE TABLE IF NOT EXISTS competitor_pages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            competitor_id INTEGER NOT NULL,
            url TEXT NOT NULL,
            title TEXT NOT NULL DEFAULT '',
            content_summary TEXT NOT NULL DEFAULT '',
            page_type TEXT NOT NULL DEFAULT 'blog',
            created_at TEXT NOT NULL,
            FOREIGN KEY (competitor_id)
                REFERENCES competitors(id)
                ON DELETE CASCADE
        )
    """)

    # 15. keyword_clusters — grouped keyword topics
    conn.execute("""
        CREATE TABLE IF NOT EXISTS keyword_clusters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            store_id TEXT NOT NULL DEFAULT 'demo-store',
            name TEXT NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL
        )
    """)

    # 16. collections — smart and custom Shopify collections
    conn.execute("""
        CREATE TABLE IF NOT EXISTS collections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            store_id TEXT NOT NULL DEFAULT 'demo-store',
            shopify_collection_id TEXT,
            title TEXT NOT NULL,
            handle TEXT NOT NULL DEFAULT '',
            description TEXT NOT NULL DEFAULT '',
            products_count INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (store_id) REFERENCES stores(id) ON DELETE CASCADE
        )
    """)

    # 17. shopify_blogs — cached Shopify blogs for store publishing
    conn.execute("""
        CREATE TABLE IF NOT EXISTS shopify_blogs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            store_id TEXT NOT NULL DEFAULT 'demo-store',
            shopify_blog_id TEXT NOT NULL,
            title TEXT NOT NULL,
            handle TEXT NOT NULL DEFAULT '',
            commentable TEXT NOT NULL DEFAULT 'no',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (store_id) REFERENCES stores(id) ON DELETE CASCADE
        )
    """)

    # 18. shopify_sync_logs — sync run audit trail
    conn.execute("""
        CREATE TABLE IF NOT EXISTS shopify_sync_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            store_id TEXT NOT NULL DEFAULT 'demo-store',
            resource_type TEXT NOT NULL,
            items_synced INTEGER NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'started',
            error_message TEXT NOT NULL DEFAULT '',
            started_at TEXT NOT NULL,
            completed_at TEXT,
            FOREIGN KEY (store_id) REFERENCES stores(id) ON DELETE CASCADE
        )
    """)

    # -------------------------------------------------------------------------
    # Migrate existing tables for Shopify readiness
    # -------------------------------------------------------------------------
    # store_connections
    _ensure_column(conn, "store_connections", "shop_domain", "TEXT NOT NULL DEFAULT ''")
    _ensure_column(conn, "store_connections", "access_token_encrypted", "TEXT NOT NULL DEFAULT ''")
    _ensure_column(conn, "store_connections", "scope", "TEXT NOT NULL DEFAULT ''")
    _ensure_column(conn, "store_connections", "api_version", "TEXT NOT NULL DEFAULT '2024-04'")
    _ensure_column(conn, "store_connections", "installed_at", "TEXT NOT NULL DEFAULT ''")
    _ensure_column(conn, "store_connections", "last_synced_at", "TEXT")
    _ensure_column(conn, "store_connections", "sync_status", "TEXT NOT NULL DEFAULT 'idle'")
    _ensure_column(conn, "store_connections", "error_message", "TEXT NOT NULL DEFAULT ''")

    # products
    _ensure_column(conn, "products", "store_id", "TEXT NOT NULL DEFAULT 'demo-store'")
    _ensure_column(conn, "products", "shopify_product_id", "TEXT")
    _ensure_column(conn, "products", "handle", "TEXT NOT NULL DEFAULT ''")
    _ensure_column(conn, "products", "tags", "TEXT NOT NULL DEFAULT ''")
    _ensure_column(conn, "products", "status", "TEXT NOT NULL DEFAULT 'active'")
    _ensure_column(conn, "products", "image_url", "TEXT NOT NULL DEFAULT ''")
    _ensure_column(conn, "products", "price_range", "TEXT NOT NULL DEFAULT ''")

    # existing_content
    _ensure_column(conn, "existing_content", "store_id", "TEXT NOT NULL DEFAULT 'demo-store'")
    _ensure_column(conn, "existing_content", "shopify_article_id", "TEXT")
    _ensure_column(conn, "existing_content", "shopify_blog_id", "TEXT")
    _ensure_column(conn, "existing_content", "handle", "TEXT NOT NULL DEFAULT ''")
    _ensure_column(conn, "existing_content", "summary", "TEXT NOT NULL DEFAULT ''")

    # published_content
    _ensure_column(conn, "published_content", "shopify_article_id", "TEXT")
    _ensure_column(conn, "published_content", "shopify_blog_id", "TEXT")
    _ensure_column(conn, "published_content", "shopify_status", "TEXT NOT NULL DEFAULT 'local'")
    _ensure_column(conn, "published_content", "shopify_url", "TEXT NOT NULL DEFAULT ''")

    # -------------------------------------------------------------------------
    # Migrate existing research_runs to support new agent fields
    # -------------------------------------------------------------------------
    _ensure_column(conn, "research_runs", "store_id", "TEXT NOT NULL DEFAULT 'demo-store'")
    _ensure_column(conn, "research_runs", "goal", "TEXT NOT NULL DEFAULT 'Find content opportunities'")
    _ensure_column(conn, "research_runs", "iteration", "INTEGER NOT NULL DEFAULT 0")
    _ensure_column(conn, "research_runs", "max_iterations", "INTEGER NOT NULL DEFAULT 5")
    _ensure_column(conn, "research_runs", "max_searches", "INTEGER NOT NULL DEFAULT 10")
    _ensure_column(conn, "research_runs", "max_pages", "INTEGER NOT NULL DEFAULT 50")
    _ensure_column(conn, "research_runs", "started_at", "TEXT")
    # completed_at already exists in original schema

    # Migrate content_opportunities to support evidence-driven fields
    _ensure_column(conn, "content_opportunities", "topic", "TEXT NOT NULL DEFAULT ''")
    _ensure_column(conn, "content_opportunities", "search_intent", "TEXT NOT NULL DEFAULT 'informational'")
    _ensure_column(conn, "content_opportunities", "why_it_matters", "TEXT NOT NULL DEFAULT ''")
    _ensure_column(conn, "content_opportunities", "evidence_ids", "TEXT NOT NULL DEFAULT '[]'")
    _ensure_column(conn, "content_opportunities", "supporting_evidence", "TEXT NOT NULL DEFAULT '[]'")
    _ensure_column(conn, "content_opportunities", "missing_evidence", "TEXT NOT NULL DEFAULT '[]'")
    _ensure_column(conn, "content_opportunities", "confidence_level", "TEXT NOT NULL DEFAULT 'exploratory'")

    conn.commit()

def _ensure_column(conn: sqlite3.Connection, table: str, column: str, col_def: str) -> None:
    """Safely add a column to an existing table if it does not already exist."""
    cursor = conn.execute(f"PRAGMA table_info({table})")
    columns = [row[1] for row in cursor.fetchall()]
    if column not in columns:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_def}")

