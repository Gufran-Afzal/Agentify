"""
Research Orchestrator — the bounded research loop.

ARCHITECTURE:

  initialize state
        ↓
  planner decides
        ↓
  validate action (budget check)
        ↓
  execute deterministic tool
        ↓
  convert result → evidence items
        ↓
  update state
        ↓
  planner again → (repeat until stop condition)

STOP CONDITIONS (checked in order):
  1. budget_exhausted — any hard limit reached
  2. max_iterations_reached — safety net
  3. planner_requests_stop — planner says STOP
  4. planner_requests_generate — enough evidence, move on
  5. research_failed — unrecoverable error

Every action is recorded in state.actions_taken for full auditability.
Every evidence item gets persisted to the database by the orchestrator.

The orchestrator depends on:
  - ResearchPlanner (stateless, testable)
  - Action executors (one per ActionType — pure, deterministic functions)
  - SQLite connection (for loading data and persisting evidence)

The LLM is NOT called by the orchestrator directly.
It is called by the planner (Phase 5) and the opportunity generator.
"""

from __future__ import annotations

import json
import logging
import sqlite3
from datetime import datetime, timezone
from typing import Any, Optional

from backend.app.agents.actions import (
    ActionType,
    PlannerDecisionType,
    ResearchAction,
)
from backend.app.agents.planner import ResearchPlanner
from backend.app.agents.state import (
    ConfidenceLevel,
    EvidenceItem,
    EvidenceType,
    OpportunityDraft,
    ResearchBudget,
    ResearchState,
    ResearchStatus,
    SourceType,
)
from backend.app.utils.dates import utc_now_iso

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Action executors — one function per ActionType
# Each returns a list of EvidenceItems created from its results.
# ---------------------------------------------------------------------------

def _execute_analyze_store(
    state: ResearchState,
    arguments: dict[str, Any],
    conn: sqlite3.Connection,
) -> list[EvidenceItem]:
    """
    Load products from the store database and convert to evidence.

    Why this is deterministic:
      - We simply read from SQLite — no LLM, no network call.
      - Each product becomes an EvidenceItem with type STORE_PRODUCT.
    """
    rows = conn.execute(
        "SELECT id, name, category, description FROM products"
    ).fetchall()

    items: list[EvidenceItem] = []
    for row in rows:
        product = dict(row)
        state.products.append(product)
        items.append(
            EvidenceItem(
                evidence_type=EvidenceType.STORE_PRODUCT,
                source_type=SourceType.STORE_DATABASE,
                source_reference="products table",
                data={
                    "product_id": product["id"],
                    "name": product["name"],
                    "category": product["category"],
                    "description": product["description"],
                },
                reliability=1.0,
                notes=f"Product: {product['name']} ({product['category']})",
            )
        )

    logger.info("ANALYZE_STORE: loaded %d products as evidence", len(items))
    return items


def _execute_analyze_existing_content(
    state: ResearchState,
    arguments: dict[str, Any],
    conn: sqlite3.Connection,
) -> list[EvidenceItem]:
    """
    Load existing content from the database and convert to evidence.

    This gives the planner visibility into what's already published,
    enabling duplicate prevention at the opportunity level.
    """
    rows = conn.execute(
        "SELECT id, title, url, primary_keyword FROM existing_content"
    ).fetchall()

    items: list[EvidenceItem] = []
    for row in rows:
        content = dict(row)
        state.existing_content.append(content)
        items.append(
            EvidenceItem(
                evidence_type=EvidenceType.EXISTING_CONTENT,
                source_type=SourceType.STORE_DATABASE,
                source_reference="existing_content table",
                data={
                    "content_id": content["id"],
                    "title": content["title"],
                    "url": content["url"],
                    "primary_keyword": content.get("primary_keyword"),
                },
                reliability=1.0,
                notes=f"Existing article: {content['title']}",
            )
        )

    logger.info("ANALYZE_EXISTING_CONTENT: loaded %d articles as evidence", len(items))
    return items


def _execute_discover_keywords(
    state: ResearchState,
    arguments: dict[str, Any],
    conn: sqlite3.Connection,
) -> list[EvidenceItem]:
    """
    Load keywords from the database and convert to evidence.

    In Phase 1, keywords come from the local database (seeded/user-provided).
    In Phase 6, this will call the KeywordProvider interface which can
    reach real search APIs.

    Each keyword becomes an evidence item with search volume signal.
    """
    rows = conn.execute(
        "SELECT id, keyword, search_volume FROM keywords"
    ).fetchall()

    items: list[EvidenceItem] = []
    for row in rows:
        kw = dict(row)
        state.keywords.append(kw)
        items.append(
            EvidenceItem(
                evidence_type=EvidenceType.KEYWORD,
                source_type=SourceType.KEYWORD_PROVIDER,
                source_reference="keywords table (seeded)",
                data={
                    "keyword_id": kw["id"],
                    "keyword": kw["keyword"],
                    "search_volume": kw["search_volume"],
                },
                # Reliability is moderate for seeded/mock data
                # Real keyword API data would get reliability=0.9
                reliability=0.7,
                notes=f"Keyword: '{kw['keyword']}' ({kw['search_volume']:,}/mo)",
            )
        )

    state.research_budget.searches_used += 1
    logger.info("DISCOVER_KEYWORDS: loaded %d keywords as evidence", len(items))
    return items


def _execute_generate_opportunities(
    state: ResearchState,
    arguments: dict[str, Any],
    conn: sqlite3.Connection,
) -> list[EvidenceItem]:
    """
    Generate content opportunities from collected evidence.

    This is the key Phase 5 step. In Phase 1 we use deterministic
    matching (product ↔ keyword overlap + duplicate check).
    In Phase 5, the LLM will reason over the evidence to produce
    more nuanced opportunities with rich 'why_it_matters' explanations.

    Returns evidence items of type CONTENT_GAP representing each
    identified opportunity (for auditability).
    """
    from backend.app.services.content_analysis_service import content_analysis_service
    from backend.app.utils.text import tokenize

    opportunities: list[OpportunityDraft] = []
    gap_evidence: list[EvidenceItem] = []

    # Group evidence by type for easier matching
    product_evidence = [e for e in state.evidence if e.evidence_type == EvidenceType.STORE_PRODUCT]
    keyword_evidence = [e for e in state.evidence if e.evidence_type == EvidenceType.KEYWORD]
    content_evidence = [e for e in state.evidence if e.evidence_type == EvidenceType.EXISTING_CONTENT]

    existing_articles = [e.data for e in content_evidence]

    # Normalize existing_articles for ContentAnalysisService
    normalized_existing = [
        {
            "id": a.get("content_id"),
            "title": a.get("title", ""),
            "url": a.get("url", ""),
            "primary_keyword": a.get("primary_keyword"),
        }
        for a in existing_articles
    ]

    # --- Product-specific opportunities ---
    for prod_ev in product_evidence:
        p_data = prod_ev.data
        p_name = p_data.get("name", "")
        p_tokens = tokenize(p_name, remove_stopwords=True)

        # Duplicate check
        content_check = content_analysis_service.check_existing_content(
            p_name,
            existing_articles=normalized_existing,
        )

        if content_check["exists"]:
            logger.info(
                "Skipping product '%s': existing content overlap — %s",
                p_name,
                content_check["similarity_reason"],
            )
            continue

        # Find matching keywords
        matching_kw_evidence: list[EvidenceItem] = []
        for kw_ev in keyword_evidence:
            kw_text = kw_ev.data.get("keyword", "")
            kw_tokens = tokenize(kw_text, remove_stopwords=True)
            if p_tokens.issubset(kw_tokens) or len(p_tokens.intersection(kw_tokens)) >= len(p_tokens):
                matching_kw_evidence.append(kw_ev)

        total_search_volume = sum(
            e.data.get("search_volume", 0) for e in matching_kw_evidence
        )
        primary_kw = (
            matching_kw_evidence[0].data.get("keyword")
            if matching_kw_evidence
            else f"{p_name.lower()} guide"
        )

        # Build evidence ID list for this opportunity
        supporting_ev_ids = [prod_ev.id] + [e.id for e in matching_kw_evidence]
        supporting_bullets = [
            f"✓ Product '{p_name}' is in the active store catalog ({p_data.get('category', '')})",
        ]

        if matching_kw_evidence:
            kw_list = ", ".join(e.data.get("keyword", "") for e in matching_kw_evidence[:3])
            supporting_bullets.append(
                f"✓ Search demand: ~{total_search_volume:,}/mo across keywords: {kw_list}"
            )
        else:
            supporting_bullets.append("⚠ Limited direct keyword evidence in current dataset")

        supporting_bullets.append(f"✓ Duplicate check: {content_check['similarity_reason']}")

        missing = []
        if not matching_kw_evidence:
            missing.append("No keyword demand data — consider enabling keyword search provider")
        if not any(e.evidence_type == EvidenceType.COMPETITOR_DOMAIN for e in state.evidence):
            missing.append("No competitor content analysis yet")
        if not any(e.evidence_type == EvidenceType.SEARCH_CONSOLE for e in state.evidence):
            missing.append("No Search Console data available")

        # Confidence: based on actual evidence quality
        # strong = product + meaningful keyword + clean duplicate check
        # moderate = product + some keyword signal
        # exploratory = product only
        if total_search_volume > 1000 and matching_kw_evidence:
            confidence = ConfidenceLevel.STRONG
            confidence_legacy = "high"
        elif matching_kw_evidence:
            confidence = ConfidenceLevel.MODERATE
            confidence_legacy = "medium"
        else:
            confidence = ConfidenceLevel.EXPLORATORY
            confidence_legacy = "low"

        why_it_matters = (
            f"The store sells {p_name} and there is relevant search evidence indicating "
            f"customer interest (approx. {total_search_volume:,} monthly searches). "
            f"No existing article covers this specific topic."
        )

        opp = OpportunityDraft(
            topic=f"What Is {p_name} Good For?",
            title=f"What Is {p_name} Good For?",
            primary_keyword=primary_kw,
            search_intent="informational",
            why_it_matters=why_it_matters,
            evidence_ids=supporting_ev_ids,
            supporting_evidence=supporting_bullets,
            missing_evidence=missing,
            confidence_level=confidence,
            reason=why_it_matters,
            search_volume=total_search_volume,
            confidence=confidence_legacy,
        )
        opportunities.append(opp)

        # Record this gap as evidence for auditability
        gap_ev = EvidenceItem(
            evidence_type=EvidenceType.CONTENT_GAP,
            source_type=SourceType.INTERNAL,
            source_reference="opportunity_generator",
            data={
                "topic": opp.topic,
                "primary_keyword": primary_kw,
                "confidence": confidence.value,
                "supporting_evidence_count": len(supporting_ev_ids),
            },
            notes=f"Opportunity: {opp.topic}",
        )
        gap_evidence.append(gap_ev)

    # --- Comparison opportunities ---
    if len(product_evidence) >= 2:
        prod_a = product_evidence[0].data.get("name", "")
        prod_b = product_evidence[1].data.get("name", "")
        comp_title = f"{prod_a} vs {prod_b}: What's the Difference?"

        comp_check = content_analysis_service.check_existing_content(
            comp_title,
            existing_articles=normalized_existing,
        )

        if not comp_check["exists"]:
            comp_kw_evidence = [
                e for e in keyword_evidence
                if "vs" in e.data.get("keyword", "").lower()
                or "versus" in e.data.get("keyword", "").lower()
            ]
            comp_volume = sum(e.data.get("search_volume", 0) for e in comp_kw_evidence)

            comparison_missing = []
            if not comp_kw_evidence:
                comparison_missing.append("No comparison keyword evidence found")
            if not any(e.evidence_type == EvidenceType.SEARCH_CONSOLE for e in state.evidence):
                comparison_missing.append("No Search Console data to validate comparison demand")

            conf = ConfidenceLevel.MODERATE if comp_kw_evidence else ConfidenceLevel.EXPLORATORY
            why = (
                f"The store sells both {prod_a} and {prod_b}, "
                f"creating a high-converting comparison topic for shoppers deciding between them."
            )
            opp = OpportunityDraft(
                topic=comp_title,
                title=comp_title,
                primary_keyword=comp_kw_evidence[0].data.get("keyword") if comp_kw_evidence else f"{prod_a.lower()} vs {prod_b.lower()}",
                search_intent="commercial",
                why_it_matters=why,
                evidence_ids=[product_evidence[0].id, product_evidence[1].id] + [e.id for e in comp_kw_evidence],
                supporting_evidence=[
                    f"✓ Both products ({prod_a}, {prod_b}) are in the store catalog",
                    f"✓ Comparison search volume: ~{comp_volume:,}/mo",
                    f"✓ Duplicate check: {comp_check['similarity_reason']}",
                ],
                missing_evidence=comparison_missing,
                confidence_level=conf,
                reason=why,
                search_volume=comp_volume,
                confidence="medium" if conf == ConfidenceLevel.MODERATE else "low",
            )
            opportunities.append(opp)

    state.opportunities = opportunities
    logger.info("GENERATE_OPPORTUNITIES: found %d opportunities", len(opportunities))
    return gap_evidence


# ---------------------------------------------------------------------------
# Action executor dispatch table
# ---------------------------------------------------------------------------

ACTION_EXECUTORS = {
    ActionType.ANALYZE_STORE: _execute_analyze_store,
    ActionType.ANALYZE_EXISTING_CONTENT: _execute_analyze_existing_content,
    ActionType.DISCOVER_KEYWORDS: _execute_discover_keywords,
    ActionType.GENERATE_OPPORTUNITIES: _execute_generate_opportunities,
}


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

class ResearchOrchestrator:
    """
    The bounded research loop.

    Responsibilities:
      - Initialize and carry the ResearchState across iterations
      - Call the planner to decide what to do next
      - Validate the decision (budget, action type)
      - Execute the deterministic action
      - Convert results into EvidenceItems
      - Persist evidence to the database
      - Update state
      - Repeat until a stop condition is met

    The orchestrator is responsible for all I/O (DB reads/writes).
    The planner and executors are pure functions (no side effects).
    """

    def __init__(
        self,
        planner: Optional[ResearchPlanner] = None,
        budget: Optional[ResearchBudget] = None,
    ):
        self.planner = planner or ResearchPlanner()
        self.default_budget = budget or ResearchBudget()

    def run(
        self,
        conn: sqlite3.Connection,
        run_id: int,
        store_id: str = "demo-store",
        goal: str = "Find content opportunities",
        budget: Optional[ResearchBudget] = None,
    ) -> ResearchState:
        """
        Execute the full research loop for a given run.

        Returns the final ResearchState with all evidence, opportunities,
        and audit trail populated.
        """
        now = utc_now_iso()
        effective_budget = budget or ResearchBudget(started_at=now)
        effective_budget.started_at = now

        state = ResearchState(
            research_run_id=run_id,
            store_id=store_id,
            goal=goal,
            research_budget=effective_budget,
            status=ResearchStatus.RUNNING,
        )

        logger.info(
            "Orchestrator starting run_id=%d store=%s goal='%s'",
            run_id,
            store_id,
            goal,
        )

        # Update run status to 'running' in DB
        conn.execute(
            "UPDATE research_runs SET status = 'running', started_at = ? WHERE id = ?",
            (now, run_id),
        )
        conn.commit()

        # --- Main research loop ---
        while True:
            state.iteration += 1
            state.research_budget.iterations_used += 1

            # Safety net — should never be reached if budget check works
            if state.iteration > state.research_budget.max_iterations + 1:
                logger.error("Safety net triggered: iteration %d exceeds max", state.iteration)
                state.status = ResearchStatus.MAX_ITERATIONS_REACHED
                state.stop_reason = f"Safety net: iteration {state.iteration}"
                break

            # Ask the planner what to do
            try:
                decision = self.planner.decide(state)
            except Exception as e:
                logger.exception("Planner raised an error: %s", e)
                state.errors.append(f"Planner error on iteration {state.iteration}: {e}")
                state.status = ResearchStatus.FAILED
                state.stop_reason = f"Planner error: {e}"
                break

            logger.info(
                "Iteration %d decision: %s — %s",
                state.iteration,
                decision.decision.value,
                decision.reason,
            )

            # Terminal decisions — exit the loop
            if decision.decision == PlannerDecisionType.STOP:
                state.status = ResearchStatus.STOPPED
                state.stop_reason = decision.reason
                state.record_action("STOP", {}, decision.reason)
                break

            if decision.decision == PlannerDecisionType.GENERATE_OPPORTUNITIES:
                # Run opportunity generation as one final action
                state.record_action(
                    "GENERATE_OPPORTUNITIES",
                    {},
                    "Evidence sufficient — generating opportunities",
                )
                generate_action = ResearchAction(
                    action_type=ActionType.GENERATE_OPPORTUNITIES,
                    arguments={},
                    reason=decision.reason,
                )
                new_evidence = self._execute_action(generate_action, state, conn)
                for ev in new_evidence:
                    state.add_evidence(ev)
                self._persist_evidence(new_evidence, conn)
                state.record_action(
                    "GENERATE_OPPORTUNITIES",
                    {},
                    f"Generated {len(state.opportunities)} opportunities",
                )
                state.status = ResearchStatus.COMPLETED
                state.stop_reason = decision.reason
                break

            # Action decision — validate and execute
            if decision.decision == PlannerDecisionType.RESEARCH_MORE:
                action = decision.action
                if not action:
                    logger.error("Planner returned RESEARCH_MORE without an action")
                    state.status = ResearchStatus.FAILED
                    state.stop_reason = "Planner returned RESEARCH_MORE without an action"
                    break

                # Validate budget
                allowed, reason = action.can_execute(state.research_budget)
                if not allowed:
                    logger.warning("Action %s blocked by budget: %s", action.action_type.value, reason)
                    state.status = ResearchStatus.BUDGET_EXHAUSTED
                    state.stop_reason = f"Action {action.action_type.value} blocked: {reason}"
                    break

                # Persist action record
                db_action_id = self._persist_action(action, run_id, conn)

                # Execute the action
                try:
                    new_evidence = self._execute_action(action, state, conn)
                except Exception as e:
                    logger.exception("Action %s failed: %s", action.action_type.value, e)
                    state.errors.append(f"Action {action.action_type.value} failed: {e}")
                    self._update_action_status(db_action_id, "failed", str(e), conn)
                    state.record_action(action.action_type.value, action.arguments, f"FAILED: {e}", "failed")
                    # Non-fatal: continue to next iteration
                    continue

                # Convert results to evidence and persist
                for ev in new_evidence:
                    state.add_evidence(ev)
                self._persist_evidence(new_evidence, conn)
                self._update_action_status(
                    db_action_id,
                    "completed",
                    json.dumps({"evidence_created": len(new_evidence)}),
                    conn,
                )
                state.record_action(
                    action.action_type.value,
                    action.arguments,
                    f"Created {len(new_evidence)} evidence items",
                )

            # Check budget after each action
            exhausted, reason = state.research_budget.is_exhausted()
            if exhausted:
                state.status = ResearchStatus.BUDGET_EXHAUSTED
                state.stop_reason = reason
                break

        # --- Loop ended ---
        completed_at = utc_now_iso()
        conn.execute(
            "UPDATE research_runs SET status = ?, completed_at = ?, iteration = ? WHERE id = ?",
            (state.status.value, completed_at, state.iteration, run_id),
        )
        conn.commit()

        logger.info(
            "Orchestrator finished run_id=%d status=%s reason='%s' opportunities=%d",
            run_id,
            state.status.value,
            state.stop_reason,
            len(state.opportunities),
        )
        return state

    def _execute_action(
        self,
        action: ResearchAction,
        state: ResearchState,
        conn: sqlite3.Connection,
    ) -> list[EvidenceItem]:
        """Route an action to its executor function."""
        executor = ACTION_EXECUTORS.get(action.action_type)
        if not executor:
            raise ValueError(
                f"No executor registered for action type '{action.action_type.value}'. "
                "This is a programming error — add the executor to ACTION_EXECUTORS."
            )
        return executor(state, action.arguments, conn)

    def _persist_action(
        self,
        action: ResearchAction,
        run_id: int,
        conn: sqlite3.Connection,
    ) -> Optional[int]:
        """Persist a research action record to the database."""
        try:
            cursor = conn.execute(
                """
                INSERT INTO research_actions (
                    research_run_id, action_type, arguments, result, status, created_at
                ) VALUES (?, ?, ?, ?, 'running', ?)
                """,
                (
                    run_id,
                    action.action_type.value,
                    json.dumps(action.arguments),
                    "{}",
                    utc_now_iso(),
                ),
            )
            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            logger.warning("Could not persist action record: %s", e)
            return None

    def _update_action_status(
        self,
        action_id: Optional[int],
        status: str,
        result: str,
        conn: sqlite3.Connection,
    ) -> None:
        """Update an action record with its result."""
        if action_id is None:
            return
        try:
            conn.execute(
                """
                UPDATE research_actions
                SET status = ?, result = ?, completed_at = ?
                WHERE id = ?
                """,
                (status, result, utc_now_iso(), action_id),
            )
            conn.commit()
        except Exception as e:
            logger.warning("Could not update action record %s: %s", action_id, e)

    def _persist_evidence(
        self,
        evidence: list[EvidenceItem],
        conn: sqlite3.Connection,
    ) -> None:
        """Persist evidence items to the research_evidence table."""
        for item in evidence:
            try:
                conn.execute(
                    """
                    INSERT INTO research_evidence (
                        research_run_id, store_id, source_type, source_reference,
                        evidence_type, data, reliability, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        item.research_run_id,
                        item.store_id,
                        item.source_type.value,
                        item.source_reference,
                        item.evidence_type.value,
                        json.dumps(item.data),
                        item.reliability,
                        item.collected_at,
                    ),
                )
            except Exception as e:
                logger.warning("Could not persist evidence item %s: %s", item.id, e)
        try:
            conn.commit()
        except Exception as e:
            logger.warning("Could not commit evidence batch: %s", e)
