import json
import logging
import sqlite3
from typing import Any
from backend.app.services.content_analysis_service import content_analysis_service
from backend.app.utils.text import tokenize

logger = logging.getLogger(__name__)

class OpportunityService:
    def discover_opportunities(self, conn: sqlite3.Connection) -> list[dict[str, Any]]:
        """
        Analyze products, keywords, and existing content in SQLite.
        Detects product guides and comparison topics with transparent scoring and evidence.
        """
        products = [dict(r) for r in conn.execute("SELECT id, name, category, description FROM products").fetchall()]
        keywords = [dict(r) for r in conn.execute("SELECT id, keyword, search_volume FROM keywords").fetchall()]
        existing_articles = [dict(r) for r in conn.execute("SELECT id, title, url, primary_keyword FROM existing_content").fetchall()]

        opportunities: list[dict[str, Any]] = []

        # 1. Product-specific opportunities
        for product in products:
            p_name = product["name"]
            p_desc = product["description"]
            p_tokens = tokenize(p_name, remove_stopwords=True)

            # Check existing content collision
            content_check = content_analysis_service.check_existing_content(
                p_name,
                existing_articles=existing_articles
            )

            # Find matching keywords
            matching_keywords: list[dict[str, Any]] = []
            for kw in keywords:
                kw_tokens = tokenize(kw["keyword"], remove_stopwords=True)
                # If product tokens are a subset of or have strong overlap with keyword tokens
                if p_tokens.issubset(kw_tokens) or len(p_tokens.intersection(kw_tokens)) >= len(p_tokens):
                    matching_keywords.append(kw)

            total_search_volume = sum(k["search_volume"] for k in matching_keywords)
            primary_kw = matching_keywords[0]["keyword"] if matching_keywords else f"{p_name.lower()} guide"

            # Transparent Scoring Calculation
            # product_relevance: 40 points if present in catalog
            product_relevance = 40.0
            # search_demand_signal: up to 35 points normalized by search volume (capped at 20,000)
            search_demand_signal = min(35.0, (total_search_volume / 20000.0) * 35.0) if total_search_volume > 0 else 5.0
            # keyword_relevance: 25 points if specific high-intent keywords match
            keyword_relevance = 25.0 if matching_keywords else 10.0
            # duplicate_content_penalty: 80 points deducted if existing content covers this
            duplicate_penalty = 80.0 if content_check["exists"] else 0.0

            opportunity_score = product_relevance + search_demand_signal + keyword_relevance - duplicate_penalty

            # If duplicate content exists, skip creating a new article opportunity
            if content_check["exists"]:
                logger.info("Skipping opportunity for %s: %s", p_name, content_check["similarity_reason"])
                continue

            # Confidence determination
            if opportunity_score >= 80:
                confidence = "high"
            elif opportunity_score >= 50:
                confidence = "medium"
            else:
                confidence = "low"

            evidence = [
                f"Product in active store catalog: {p_name} ({product['category']})",
                f"Search demand identified: {total_search_volume:,} estimated monthly searches across {len(matching_keywords)} keyword(s)" if matching_keywords else "Low direct keyword volume detected in demo catalog",
                f"Content audit: {content_check['similarity_reason']}",
                f"Opportunity score: {opportunity_score:.1f}/100 (Relevance: {product_relevance:.0f}, Demand: {search_demand_signal:.1f}, Keywords: {keyword_relevance:.0f})"
            ]

            title = f"What Is {p_name} Good For?"
            reason = f"The store sells {p_name} and there is relevant search demand without overlapping articles."

            opportunities.append({
                "title": title,
                "reason": reason,
                "primary_keyword": primary_kw,
                "search_volume": total_search_volume,
                "confidence": confidence,
                "evidence": evidence,
                "matching_keywords": matching_keywords
            })

        # 2. Product Comparison opportunities (e.g. Vitamin C vs Hyaluronic Acid)
        if len(products) >= 2:
            prod_a = products[0]["name"]
            prod_b = products[1]["name"]

            comp_keywords = [
                kw for kw in keywords
                if "vs" in kw["keyword"].lower() or "versus" in kw["keyword"].lower()
            ]
            comp_search_volume = sum(k["search_volume"] for k in comp_keywords)
            comp_title = f"{prod_a} vs {prod_b}: What's the Difference?"

            comp_check = content_analysis_service.check_existing_content(
                comp_title,
                existing_articles=existing_articles
            )

            if not comp_check["exists"]:
                comp_score = 40.0 + min(35.0, (comp_search_volume / 10000.0) * 35.0) + (25.0 if comp_keywords else 10.0)
                confidence = "high" if comp_score >= 75 else "medium"

                evidence = [
                    f"Catalog features both complementary products: '{prod_a}' and '{prod_b}'",
                    f"Direct comparison search volume: {comp_search_volume:,} searches/month",
                    f"Content audit: {comp_check['similarity_reason']}",
                    f"Opportunity score: {comp_score:.1f}/100"
                ]

                primary_kw = comp_keywords[0]["keyword"] if comp_keywords else f"{prod_a.lower()} vs {prod_b.lower()}"
                opportunities.append({
                    "title": comp_title,
                    "reason": f"The store sells both {prod_a} and {prod_b}, creating a high-converting comparative topic for shoppers.",
                    "primary_keyword": primary_kw,
                    "search_volume": comp_search_volume,
                    "confidence": confidence,
                    "evidence": evidence,
                    "matching_keywords": comp_keywords
                })

        return opportunities

    def get_opportunity(self, conn: sqlite3.Connection, opportunity_id: int) -> dict[str, Any] | None:
        row = conn.execute(
            """
            SELECT id, research_run_id, title, reason, primary_keyword,
                   search_volume, confidence, status, created_at, evidence
            FROM content_opportunities
            WHERE id = ?
            """,
            (opportunity_id,)
        ).fetchone()
        if not row:
            return None
        res = dict(row)
        try:
            res["evidence"] = json.loads(res["evidence"]) if res.get("evidence") else []
        except Exception:
            res["evidence"] = []
        return res

    def list_opportunities(self, conn: sqlite3.Connection, status: str | None = None) -> list[dict[str, Any]]:
        query = """
            SELECT id, research_run_id, title, reason, primary_keyword,
                   search_volume, confidence, status, created_at, evidence
            FROM content_opportunities
        """
        params: list[Any] = []
        if status:
            query += " WHERE status = ?"
            params.append(status)
        query += " ORDER BY id DESC"

        rows = conn.execute(query, params).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            try:
                d["evidence"] = json.loads(d["evidence"]) if d.get("evidence") else []
            except Exception:
                d["evidence"] = []
            result.append(d)
        return result

    def approve_opportunity(self, conn: sqlite3.Connection, opportunity_id: int) -> tuple[int, str]:
        """
        Transitions opportunity status: pending -> approved.
        Returns: (http_status_code, message_or_error)
        """
        opp = self.get_opportunity(conn, opportunity_id)
        if not opp:
            return 404, "Content opportunity not found."
        if opp["status"] != "pending":
            return 409, f"Cannot approve opportunity with status '{opp['status']}'. Only 'pending' opportunities can be approved."

        conn.execute("UPDATE content_opportunities SET status = 'approved' WHERE id = ?", (opportunity_id,))
        conn.commit()
        return 200, "approved"

    def reject_opportunity(self, conn: sqlite3.Connection, opportunity_id: int) -> tuple[int, str]:
        """
        Transitions opportunity status: pending -> rejected.
        Returns: (http_status_code, message_or_error)
        """
        opp = self.get_opportunity(conn, opportunity_id)
        if not opp:
            return 404, "Content opportunity not found."
        if opp["status"] != "pending":
            return 409, f"Cannot reject opportunity with status '{opp['status']}'. Only 'pending' opportunities can be rejected."

        conn.execute("UPDATE content_opportunities SET status = 'rejected' WHERE id = ?", (opportunity_id,))
        conn.commit()
        return 200, "rejected"

opportunity_service = OpportunityService()
