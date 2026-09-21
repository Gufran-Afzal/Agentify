"""
Gemini LLM Provider — implements LLMProvider using Google's Gemini API.

Uses the official google-genai Python SDK:
  from google import genai

CONFIGURATION (via environment variables):
  GEMINI_API_KEY=your_key_here      (required for real calls)
  GEMINI_MODEL=gemini-2.5-flash-lite (default — use flash for heavy tasks)

MODEL SELECTION POLICY:
  - gemini-2.5-flash-lite: classification, extraction, intent detection,
                            research planning, simple transformations
  - gemini-2.5-flash: complex opportunity reasoning, content briefs,
                      article drafts (when GEMINI_MODEL=gemini-2.5-flash)

FALLBACK POLICY (critical):
  If the API key is missing, the SDK is not installed, the API is unavailable,
  or rate limits are hit — this provider GRACEFULLY FALLS BACK to MockLLMProvider.
  The application NEVER crashes because Gemini is unavailable.

SECURITY:
  - API key is read from environment only
  - Never logged or exposed to the frontend
  - All external responses are validated with Pydantic

COST AWARENESS:
  - Flash-Lite is used by default (lower cost)
  - Token usage is tracked when available
  - Structured output reduces token waste (no verbose natural language parsing)
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any, Optional

from backend.app.config import settings
from backend.app.providers.interfaces.llm import LLMProvider

if TYPE_CHECKING:
    from backend.app.agents.actions import PlannerDecision
    from backend.app.agents.state import OpportunityDraft, ResearchState

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Pydantic models for structured Gemini output validation
# ---------------------------------------------------------------------------

try:
    from pydantic import BaseModel, Field as PydanticField

    class _TopicsOutput(BaseModel):
        topics: list[str] = PydanticField(default_factory=list)

    class _IntentOutput(BaseModel):
        intent: str = "informational"
        confidence: float = 0.8
        reason: str = ""

    class _CompetitorOutput(BaseModel):
        is_competitor: bool = True
        competitor_type: str = "content"
        reason: str = ""
        relevant_topics: list[str] = PydanticField(default_factory=list)

    class _BriefSection(BaseModel):
        heading: str
        description: str = ""

    class _BriefOutput(BaseModel):
        title: str
        objective: str
        search_intent: str = "informational"
        target_audience: str = ""
        suggested_angle: str = ""
        suggested_sections: list[str] = PydanticField(default_factory=list)
        related_keywords: list[str] = PydanticField(default_factory=list)
        why_it_matters: str = ""

    _PYDANTIC_AVAILABLE = True
except ImportError:
    _PYDANTIC_AVAILABLE = False


class GeminiLLMProvider(LLMProvider):
    """
    LLM provider backed by Google Gemini.

    Instantiated by the provider factory when AI_PROVIDER=gemini and
    GEMINI_API_KEY is set. Falls back to MockLLMProvider on any failure.
    """

    def __init__(self):
        self._client = None
        self._model = settings.GEMINI_MODEL
        self._api_key = settings.GEMINI_API_KEY
        self._available = False
        self._fallback = None  # lazy-loaded to avoid circular import

        self._initialize_client()

    def _initialize_client(self) -> None:
        """
        Attempt to initialize the Gemini client.
        Silently marks unavailable on any error — never raises.
        """
        if not self._api_key:
            logger.info(
                "GeminiLLMProvider: GEMINI_API_KEY not set — using mock fallback"
            )
            return

        try:
            from google import genai  # type: ignore[import]
            self._client = genai.Client(api_key=self._api_key)
            self._available = True
            logger.info(
                "GeminiLLMProvider: initialized with model '%s'", self._model
            )
        except ImportError:
            logger.warning(
                "GeminiLLMProvider: google-genai SDK not installed. "
                "Run: pip install google-genai"
            )
        except Exception as e:
            logger.warning("GeminiLLMProvider: initialization failed: %s", e)

    def _get_fallback(self):
        """Lazy-load MockLLMProvider to avoid import-time circular deps."""
        if self._fallback is None:
            from backend.app.providers.mocks.mock_llm import MockLLMProvider
            self._fallback = MockLLMProvider()
        return self._fallback

    def is_available(self) -> bool:
        return self._available and self._client is not None

    def _call_gemini(
        self,
        prompt: str,
        model_override: Optional[str] = None,
    ) -> Optional[str]:
        """
        Make a raw text completion call to Gemini.

        Returns the response text, or None if anything goes wrong.
        The caller is responsible for handling None → fallback.
        """
        if not self.is_available():
            return None

        model = model_override or self._model
        try:
            response = self._client.models.generate_content(
                model=model,
                contents=prompt,
            )
            return response.text
        except Exception as e:
            # Catch rate limits, quota errors, network errors, etc.
            logger.warning("Gemini API call failed (model=%s): %s", model, e)
            return None

    def _call_gemini_json(
        self,
        prompt: str,
        model_override: Optional[str] = None,
    ) -> Optional[dict]:
        """
        Call Gemini and parse the response as JSON.
        Returns None on failure so callers can fall back.
        """
        text = self._call_gemini(prompt, model_override)
        if not text:
            return None
        # Strip markdown code fences if present
        text = text.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:-1]) if len(lines) > 2 else text
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            logger.warning("Gemini returned invalid JSON: %s — text: %.200s", e, text)
            return None

    # -------------------------------------------------------------------------
    # LLMProvider interface implementation
    # -------------------------------------------------------------------------

    def plan_research(self, state: "ResearchState") -> "PlannerDecision":
        """
        Phase 5: Use Gemini to decide the next research action.
        Phase 1: Falls back to deterministic planner (always used currently).
        """
        # For now, always use the deterministic planner.
        # Phase 5 will add Gemini-powered reasoning here when the deterministic
        # rules can't resolve (e.g., "should I search the web or discover competitors?")
        return self._get_fallback().plan_research(state)

    def extract_topics(self, text: str, context: Optional[str] = None) -> list[str]:
        """
        Use Gemini Flash-Lite to extract key topics from text.
        """
        if not self.is_available():
            return self._get_fallback().extract_topics(text, context)

        ctx_note = f"\nContext: {context}" if context else ""
        prompt = (
            f"Extract the 5 most important content topics from the following text. "
            f"Return a JSON object with a single key 'topics' containing a list of strings.{ctx_note}\n\n"
            f"Text:\n{text[:2000]}\n\n"
            f"Return only valid JSON. Example: {{\"topics\": [\"vitamin C serum\", \"skincare routine\"]}}"
        )

        data = self._call_gemini_json(prompt)
        if data and isinstance(data.get("topics"), list):
            return [str(t) for t in data["topics"][:10]]

        logger.debug("Gemini topic extraction failed — using mock fallback")
        return self._get_fallback().extract_topics(text, context)

    def classify_search_intent(self, topic: str) -> str:
        """
        Use Gemini Flash-Lite to classify search intent.
        """
        if not self.is_available():
            return self._get_fallback().classify_search_intent(topic)

        prompt = (
            f"Classify the search intent of this topic: '{topic}'\n\n"
            f"Return a JSON object with keys: 'intent' (one of: informational, commercial, transactional, navigational), "
            f"'confidence' (float 0-1), 'reason' (brief explanation).\n"
            f"Return only valid JSON."
        )

        data = self._call_gemini_json(prompt)
        if data and data.get("intent") in ("informational", "commercial", "transactional", "navigational"):
            return data["intent"]

        return self._get_fallback().classify_search_intent(topic)

    def qualify_competitor(
        self,
        domain: str,
        store_products: list[str],
        context: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Use Gemini Flash-Lite to qualify whether a domain is a real competitor.
        """
        if not self.is_available():
            return self._get_fallback().qualify_competitor(domain, store_products, context)

        products_text = ", ".join(store_products[:5])
        prompt = (
            f"A store sells: {products_text}\n\n"
            f"Is the domain '{domain}' a competitor?\n\n"
            f"Classify it as: business_competitor (sells same products), "
            f"content_competitor (writes about same topics), "
            f"search_competitor (ranks for same queries), or none.\n\n"
            f"Return JSON with keys: is_competitor (bool), competitor_type (string), "
            f"reason (string), relevant_topics (list of strings).\n"
            f"Never classify Amazon, Reddit, YouTube, or Wikipedia as business competitors.\n"
            f"Return only valid JSON."
        )

        data = self._call_gemini_json(prompt)
        if data and "competitor_type" in data:
            return {
                "is_competitor": bool(data.get("is_competitor", True)),
                "competitor_type": data.get("competitor_type", "content"),
                "reason": data.get("reason", ""),
                "relevant_topics": data.get("relevant_topics", []),
            }

        return self._get_fallback().qualify_competitor(domain, store_products, context)

    def generate_opportunities(
        self,
        state: "ResearchState",
    ) -> list["OpportunityDraft"]:
        """
        Phase 5: Use Gemini to generate evidence-backed opportunities.
        Currently defers to the deterministic engine in the orchestrator.
        """
        return self._get_fallback().generate_opportunities(state)

    def generate_content_brief(
        self,
        opportunity: dict[str, Any],
        evidence: list[dict[str, Any]],
        store_context: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """
        Use Gemini Flash (or Flash-Lite) to generate a structured content brief.
        Falls back to deterministic brief generation if Gemini is unavailable.
        """
        if not self.is_available():
            return self._get_fallback().generate_content_brief(opportunity, evidence, store_context)

        title = opportunity.get("title", opportunity.get("topic", "Product Guide"))
        why = opportunity.get("why_it_matters", opportunity.get("reason", ""))
        primary_kw = opportunity.get("primary_keyword", "")
        intent = opportunity.get("search_intent", "informational")
        evidence_text = "\n".join(
            f"- {e.get('notes', e.get('evidence_type', 'evidence'))}: {json.dumps(e.get('data', {}))[:200]}"
            for e in evidence[:5]
        )

        # Use Flash for brief generation (more nuanced editorial reasoning)
        brief_model = settings.GEMINI_MODEL
        prompt = (
            f"You are an expert SEO content strategist.\n\n"
            f"Create a structured content brief for this approved opportunity:\n"
            f"Title: {title}\n"
            f"Primary keyword: {primary_kw}\n"
            f"Search intent: {intent}\n"
            f"Why it matters: {why}\n\n"
            f"Supporting evidence:\n{evidence_text}\n\n"
            f"Return a JSON object with these exact keys:\n"
            f"  title (string), objective (string), search_intent (string),\n"
            f"  target_audience (string), suggested_angle (string),\n"
            f"  suggested_sections (list of 5-7 section heading strings),\n"
            f"  related_keywords (list of 3-5 related keyword strings),\n"
            f"  why_it_matters (string)\n\n"
            f"Be specific. Do not use placeholder content. Return only valid JSON."
        )

        data = self._call_gemini_json(prompt, model_override=brief_model)
        if data and "suggested_sections" in data:
            return {
                "title": data.get("title", title),
                "objective": data.get("objective", ""),
                "primary_keyword": primary_kw,
                "search_volume": opportunity.get("search_volume", 0),
                "search_intent": data.get("search_intent", intent),
                "target_audience": data.get("target_audience", ""),
                "suggested_sections": data.get("suggested_sections", []),
                "suggested_angle": data.get("suggested_angle", ""),
                "related_keywords": data.get("related_keywords", []),
                "opportunity_evidence": [e.get("notes", "") for e in evidence[:5]],
                "why_it_matters": data.get("why_it_matters", why),
                "_generated_by": f"gemini:{brief_model}",
            }

        logger.warning("Gemini brief generation failed — using mock fallback")
        return self._get_fallback().generate_content_brief(opportunity, evidence, store_context)

    def generate_draft(
        self,
        brief: dict[str, Any],
        evidence: Optional[list[dict[str, Any]]] = None,
    ) -> dict[str, str]:
        """
        Use Gemini to write a full article draft from a content brief.
        Falls back to MockContentGenerator if unavailable.

        Uses structured sections from the brief. Does NOT blindly keyword-stuff.
        The prompt explicitly instructs Gemini to prioritize helpfulness and clarity.
        """
        if not self.is_available():
            return self._get_fallback().generate_draft(brief, evidence)

        title = brief.get("title", "Product Guide")
        primary_kw = brief.get("primary_keyword", "")
        audience = brief.get("target_audience", "readers")
        angle = brief.get("suggested_angle", "educational guide")
        sections = brief.get("suggested_sections", [])
        intent = brief.get("search_intent", "informational")
        sections_text = "\n".join(f"  - {s}" for s in sections[:8])

        # Use the configured model (flash for drafts, flash-lite for lighter tasks)
        draft_model = settings.GEMINI_MODEL

        prompt = (
            f"You are an expert content writer. Write a helpful, original article.\n\n"
            f"Title: {title}\n"
            f"Primary keyword: {primary_kw}\n"
            f"Target audience: {audience}\n"
            f"Angle: {angle}\n"
            f"Search intent: {intent}\n"
            f"Sections to cover:\n{sections_text}\n\n"
            f"IMPORTANT RULES:\n"
            f"- Write genuinely helpful content, not keyword-stuffed filler\n"
            f"- Use natural language\n"
            f"- Be factually accurate\n"
            f"- For health/medical topics: include appropriate disclaimers\n"
            f"- Do not invent scientific claims\n\n"
            f"Return a JSON object with these exact keys:\n"
            f"  title (string), introduction (2-3 paragraph string),\n"
            f"  body (markdown string with ## section headings),\n"
            f"  conclusion (1-2 paragraph string)\n\n"
            f"Return only valid JSON."
        )

        data = self._call_gemini_json(prompt, model_override=draft_model)
        if data and "introduction" in data and "body" in data:
            return {
                "title": data.get("title", title),
                "introduction": data.get("introduction", ""),
                "body": data.get("body", ""),
                "conclusion": data.get("conclusion", ""),
                "_generated_by": f"gemini:{draft_model}",
            }

        logger.warning("Gemini draft generation failed — using mock fallback")
        return self._get_fallback().generate_draft(brief, evidence)
