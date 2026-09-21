"""
Mock LLM Provider — deterministic responses for local development and testing.

Used when AI_PROVIDER=mock (the default). Returns structurally correct
responses without making any network calls or requiring API keys.

This ensures the complete research lifecycle works offline with zero credentials.

DESIGN: Every method returns the same structure a real LLM would return,
just with deterministic content. This makes it trivially easy to swap in
the real Gemini provider later.
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any, Optional

from backend.app.agents.actions import (
    ActionType,
    PlannerDecision,
    PlannerDecisionType,
    ResearchAction,
)
from backend.app.agents.state import ConfidenceLevel, EvidenceType, OpportunityDraft
from backend.app.providers.interfaces.llm import LLMProvider
from backend.app.services.generators.mock_generator import MockContentGenerator

if TYPE_CHECKING:
    from backend.app.agents.state import ResearchState

logger = logging.getLogger(__name__)


class MockLLMProvider(LLMProvider):
    """
    Deterministic mock implementation of LLMProvider.

    All methods return structurally valid, reasonable responses
    without calling any external API.
    """

    def __init__(self):
        self._mock_generator = MockContentGenerator()

    def is_available(self) -> bool:
        # Mock is always available
        return True

    def plan_research(self, state: "ResearchState") -> PlannerDecision:
        """
        Mock planner: delegates to the deterministic ResearchPlanner.
        In Phase 5, this will be where Gemini provides nuanced planning.
        """
        from backend.app.agents.planner import ResearchPlanner
        planner = ResearchPlanner()
        return planner.decide(state)

    def extract_topics(self, text: str, context: Optional[str] = None) -> list[str]:
        """
        Mock topic extraction: split on newlines and return non-empty lines.
        Simulates what an LLM would return for topic extraction.
        """
        words = text.split()[:10]
        # Simple heuristic: return noun-like words
        topics = [w.strip(".,!?") for w in words if len(w) > 4][:5]
        logger.debug("Mock extract_topics: %s", topics)
        return topics if topics else ["skincare", "routine", "ingredients"]

    def classify_search_intent(self, topic: str) -> str:
        """
        Mock intent classification using simple keyword rules.
        Real Gemini would do nuanced semantic classification.
        """
        topic_lower = topic.lower()
        if any(w in topic_lower for w in ["buy", "shop", "price", "order", "purchase"]):
            return "transactional"
        if any(w in topic_lower for w in ["vs", "versus", "compare", "difference", "best"]):
            return "commercial"
        if any(w in topic_lower for w in ["how to", "what is", "why", "guide", "tips", "benefits"]):
            return "informational"
        return "informational"

    def qualify_competitor(
        self,
        domain: str,
        store_products: list[str],
        context: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Mock competitor qualification.
        Real Gemini would analyze domain content, compare with store products.
        """
        # Mock: large platforms are never business competitors
        non_competitors = {"amazon.com", "reddit.com", "youtube.com", "wikipedia.org"}
        if domain in non_competitors:
            return {
                "is_competitor": True,
                "competitor_type": "search",
                "reason": f"{domain} is a major search-visible platform, not a direct business competitor.",
                "relevant_topics": [],
            }
        return {
            "is_competitor": True,
            "competitor_type": "content",
            "reason": f"{domain} appears in search results for relevant product queries.",
            "relevant_topics": store_products[:2],
        }

    def generate_opportunities(
        self,
        state: "ResearchState",
    ) -> list[OpportunityDraft]:
        """
        Mock opportunity generation: returns empty list.
        The orchestrator's _execute_generate_opportunities handles
        this deterministically in Phase 1.
        """
        logger.debug("MockLLMProvider.generate_opportunities: deferring to deterministic engine")
        return []

    def generate_content_brief(
        self,
        opportunity: dict[str, Any],
        evidence: list[dict[str, Any]],
        store_context: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """
        Mock brief generation: produces a structurally valid brief using
        the same deterministic logic as the existing brief_service.
        Real Gemini would add editorial insight and nuanced angle selection.
        """
        title = opportunity.get("title", opportunity.get("topic", "Product Guide"))
        primary_kw = opportunity.get("primary_keyword", title.lower())
        why = opportunity.get("why_it_matters", opportunity.get("reason", ""))
        search_vol = opportunity.get("search_volume", 0)
        search_intent = opportunity.get("search_intent", "informational")

        if " vs " in title.lower() or "difference" in title.lower():
            intent = "commercial / comparison"
            audience = "Shoppers deciding between two complementary products"
            angle = "Head-to-head comparison focusing on efficacy, compatibility, and use case"
            sections = [
                "Introduction: Key Differences at a Glance",
                "Ingredient Profiles & How Each Works",
                "Skin Type & Use Case Comparison",
                "Can You Use Both Together?",
                "Final Verdict & Product Recommendations",
            ]
        else:
            intent = f"{search_intent} / educational"
            audience = "Consumers researching product benefits and usage"
            angle = "Educational guide establishing benefits and step-by-step usage"
            sections = [
                f"What Is {primary_kw.title()}?",
                "Key Benefits & Expected Outcomes",
                "How to Apply & Layer into Your Routine",
                "Compatible Ingredients & What to Avoid",
                "Frequently Asked Questions",
            ]

        return {
            "title": title,
            "objective": (
                f"Create an authoritative article for '{title}' that satisfies "
                f"'{intent}' intent, builds organic authority for '{primary_kw}', "
                f"and guides readers to relevant store products."
            ),
            "primary_keyword": primary_kw,
            "search_volume": search_vol,
            "search_intent": intent,
            "target_audience": audience,
            "suggested_sections": sections,
            "suggested_angle": angle,
            "related_keywords": [],
            "opportunity_evidence": [e.get("notes", "") for e in evidence[:5] if "notes" in e],
            "why_it_matters": why,
            "_generated_by": "mock_llm",
        }

    def generate_draft(
        self,
        brief: dict[str, Any],
        evidence: Optional[list[dict[str, Any]]] = None,
    ) -> dict[str, str]:
        """
        Mock draft generation: delegates to MockContentGenerator.
        Real Gemini would write a unique, evidence-grounded article.
        """
        logger.debug("MockLLMProvider.generate_draft: using MockContentGenerator")
        result = self._mock_generator.generate(brief)
        result["_generated_by"] = "mock_llm"
        return result
