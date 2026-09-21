import json
import logging
import sqlite3
from typing import Any
from backend.app.services.opportunity_service import opportunity_service
from backend.app.utils.dates import utc_now_iso

logger = logging.getLogger(__name__)

class ResearchService:
    def create_run(self, conn: sqlite3.Connection) -> dict[str, Any]:
        now = utc_now_iso()
        cursor = conn.execute(
            "INSERT INTO research_runs (status, created_at) VALUES (?, ?)",
            ("created", now)
        )
        conn.commit()
        return {
            "id": cursor.lastrowid,
            "status": "created",
            "created_at": now,
            "completed_at": None
        }

    def get_run(self, conn: sqlite3.Connection, run_id: int) -> dict[str, Any] | None:
        row = conn.execute(
            "SELECT id, status, created_at, completed_at FROM research_runs WHERE id = ?",
            (run_id,)
        ).fetchone()
        return dict(row) if row else None

    def list_runs(self, conn: sqlite3.Connection) -> list[dict[str, Any]]:
        rows = conn.execute(
            "SELECT id, status, created_at, completed_at FROM research_runs ORDER BY id DESC"
        ).fetchall()
        return [dict(r) for r in rows]

    def execute_run(self, conn: sqlite3.Connection, run_id: int) -> tuple[int, dict[str, Any]]:
        run = self.get_run(conn, run_id)
        if not run:
            return 404, {"detail": "Research run not found."}

        if run["status"] == "completed":
            return 409, {"detail": "This research run has already been completed."}

        if run["status"] == "running":
            return 409, {"detail": "This research run is already currently running."}

        # Mark running
        conn.execute("UPDATE research_runs SET status = 'running' WHERE id = ?", (run_id,))
        conn.commit()

        try:
            raw_opps = opportunity_service.discover_opportunities(conn)
            saved_opportunities = []
            now = utc_now_iso()

            for opp in raw_opps:
                # Check for duplicate opportunity title in this run
                existing = conn.execute(
                    "SELECT id FROM content_opportunities WHERE research_run_id = ? AND title = ?",
                    (run_id, opp["title"])
                ).fetchone()

                if existing:
                    continue

                evidence_json = json.dumps(opp.get("evidence", []))
                cursor = conn.execute(
                    """
                    INSERT INTO content_opportunities (
                        research_run_id, title, reason, primary_keyword,
                        search_volume, confidence, status, created_at, evidence
                    )
                    VALUES (?, ?, ?, ?, ?, ?, 'pending', ?, ?)
                    """,
                    (
                        run_id,
                        opp["title"],
                        opp["reason"],
                        opp.get("primary_keyword"),
                        opp["search_volume"],
                        opp["confidence"],
                        now,
                        evidence_json
                    )
                )

                saved_opportunities.append({
                    "id": cursor.lastrowid,
                    "research_run_id": run_id,
                    "title": opp["title"],
                    "reason": opp["reason"],
                    "primary_keyword": opp.get("primary_keyword"),
                    "search_volume": opp["search_volume"],
                    "confidence": opp["confidence"],
                    "status": "pending",
                    "created_at": now,
                    "evidence": opp.get("evidence", [])
                })

            completed_at = utc_now_iso()
            conn.execute(
                "UPDATE research_runs SET status = 'completed', completed_at = ? WHERE id = ?",
                (completed_at, run_id)
            )
            conn.commit()

            return 200, {
                "id": run_id,
                "status": "completed",
                "completed_at": completed_at,
                "opportunities_count": len(saved_opportunities),
                "opportunities": saved_opportunities
            }

        except Exception as e:
            logger.exception("Error executing research run %s: %s", run_id, e)
            conn.execute("UPDATE research_runs SET status = 'failed' WHERE id = ?", (run_id,))
            conn.commit()
            return 500, {"detail": f"Research run failed during execution: {str(e)}"}

    def get_run_opportunities(self, conn: sqlite3.Connection, run_id: int) -> tuple[int, Any]:
        run = self.get_run(conn, run_id)
        if not run:
            return 404, {"detail": "Research run not found."}

        rows = conn.execute(
            """
            SELECT id, research_run_id, title, reason, primary_keyword,
                   search_volume, confidence, status, created_at, evidence
            FROM content_opportunities
            WHERE research_run_id = ?
            ORDER BY id ASC
            """,
            (run_id,)
        ).fetchall()

        opps = []
        for r in rows:
            d = dict(r)
            try:
                d["evidence"] = json.loads(d["evidence"]) if d.get("evidence") else []
            except Exception:
                d["evidence"] = []
            opps.append(d)

        return 200, opps

research_service = ResearchService()
