import json
import logging
import sqlite3
from typing import Any
from backend.app.utils.dates import utc_now_iso

logger = logging.getLogger(__name__)

class BriefService:
    def create_brief_from_opportunity(self, conn: sqlite3.Connection, opportunity_id: int) -> tuple[int, dict[str, Any]]:
        # Fetch opportunity
        opp_row = conn.execute(
            """
            SELECT id, title, reason, primary_keyword, search_volume, confidence, status, evidence
            FROM content_opportunities
            WHERE id = ?
            """,
            (opportunity_id,)
        ).fetchone()

        if not opp_row:
            return 404, {"detail": "Opportunity not found."}

        opp = dict(opp_row)
        if opp["status"] != "approved":
            return 409, {
                "detail": f"Only approved opportunities can become content briefs. Current status: '{opp['status']}'."
            }

        # Check duplicate brief
        existing_brief = conn.execute(
            "SELECT id FROM content_briefs WHERE opportunity_id = ?",
            (opportunity_id,)
        ).fetchone()

        if existing_brief:
            return 409, {"detail": "A content brief already exists for this opportunity."}

        title = opp["title"]
        primary_keyword = opp["primary_keyword"] or title.lower()
        search_vol = opp["search_volume"]

        # Parse evidence
        try:
            evidence_list = json.loads(opp.get("evidence") or "[]")
        except Exception:
            evidence_list = []

        # Determine search intent and suggested sections dynamically based on title & keyword
        if " vs " in title.lower() or "difference" in title.lower():
            search_intent = "commercial / comparison"
            target_audience = "Shoppers deciding between two active skincare formulations"
            suggested_angle = "Head-to-head ingredient comparison focusing on efficacy, skin type compatibility, and routine layering"
            sections = [
                "Introduction: The Battle of Daily Active Serums",
                "Key Differences at a Glance",
                "Ingredient Profiles & How They Work",
                "Which One Should You Choose for Your Skin Type?",
                "Can You Use Both Together in the Same Routine?",
                "Final Verdict & Product Recommendations"
            ]
        else:
            search_intent = "informational / transactional"
            target_audience = "Consumers looking to address specific skin concerns and optimize product usage"
            suggested_angle = "Educational authority guide establishing clear product benefits and step-by-step usage instructions"
            sections = [
                f"What Is {primary_keyword.title()}?",
                "Primary Skin Benefits & Expected Outcomes",
                "How to Correctly Apply & Layer into Your Regimen",
                "Complementary Ingredients & What to Avoid",
                "Frequently Asked Questions"
            ]

        # Find related keywords in catalog
        kw_rows = conn.execute(
            "SELECT keyword FROM keywords WHERE keyword != ? LIMIT 3",
            (primary_keyword,)
        ).fetchall()
        related_keywords = [r[0] for r in kw_rows]

        objective = (
            f"Create a high-value, comprehensive article based on the approved opportunity '{title}'. "
            f"Address '{search_intent}' intent for '{primary_keyword}', build organic authority, "
            f"and guide readers seamlessly to relevant store products."
        )

        now = utc_now_iso()
        cursor = conn.execute(
            """
            INSERT INTO content_briefs (
                opportunity_id, title, objective, primary_keyword, search_volume,
                search_intent, target_audience, suggested_sections, suggested_angle,
                related_keywords, opportunity_evidence, status, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'draft', ?, ?)
            """,
            (
                opportunity_id,
                title,
                objective,
                primary_keyword,
                search_vol,
                search_intent,
                target_audience,
                json.dumps(sections),
                suggested_angle,
                json.dumps(related_keywords),
                json.dumps(evidence_list),
                now,
                now
            )
        )
        conn.commit()

        brief_id = cursor.lastrowid
        return 201, {
            "id": brief_id,
            "opportunity_id": opportunity_id,
            "title": title,
            "objective": objective,
            "primary_keyword": primary_keyword,
            "search_volume": search_vol,
            "search_intent": search_intent,
            "target_audience": target_audience,
            "suggested_sections": sections,
            "suggested_angle": suggested_angle,
            "related_keywords": related_keywords,
            "opportunity_evidence": evidence_list,
            "status": "draft",
            "created_at": now,
            "updated_at": now
        }

    def get_brief(self, conn: sqlite3.Connection, brief_id: int) -> dict[str, Any] | None:
        row = conn.execute(
            """
            SELECT id, opportunity_id, title, objective, primary_keyword, search_volume,
                   search_intent, target_audience, suggested_sections, suggested_angle,
                   related_keywords, opportunity_evidence, status, created_at, updated_at
            FROM content_briefs
            WHERE id = ?
            """,
            (brief_id,)
        ).fetchone()
        if not row:
            return None
        return self._format_brief_row(dict(row))

    def list_briefs(self, conn: sqlite3.Connection) -> list[dict[str, Any]]:
        rows = conn.execute(
            """
            SELECT id, opportunity_id, title, objective, primary_keyword, search_volume,
                   search_intent, target_audience, suggested_sections, suggested_angle,
                   related_keywords, opportunity_evidence, status, created_at, updated_at
            FROM content_briefs
            ORDER BY id DESC
            """
        ).fetchall()
        return [self._format_brief_row(dict(r)) for r in rows]

    def _format_brief_row(self, d: dict[str, Any]) -> dict[str, Any]:
        for field in ("suggested_sections", "related_keywords", "opportunity_evidence"):
            val = d.get(field)
            if isinstance(val, str):
                try:
                    d[field] = json.loads(val)
                except Exception:
                    d[field] = []
            elif val is None:
                d[field] = []
        return d

brief_service = BriefService()
