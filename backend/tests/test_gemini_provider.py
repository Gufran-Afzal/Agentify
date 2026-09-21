from backend.app.providers.implementations.provider_factory import get_llm_provider, clear_provider_cache
from backend.app.providers.implementations.gemini_llm import GeminiLLMProvider
from backend.app.providers.mocks.mock_llm import MockLLMProvider

def test_provider_factory_mock():
    clear_provider_cache()
    llm = get_llm_provider(force_refresh=True)
    assert isinstance(llm, MockLLMProvider)
    assert llm.is_available()

def test_gemini_provider_safe_fallback():
    # When no API key is provided, Gemini provider gracefully degrades
    gemini = GeminiLLMProvider()
    assert not gemini.is_available()

    # Calling methods on fallback should still return valid data
    topics = gemini.extract_topics("Vitamin C serum benefits for bright skin")
    assert isinstance(topics, list)
    assert len(topics) > 0

    intent = gemini.classify_search_intent("best vitamin c serum")
    assert intent in ("informational", "commercial", "transactional", "navigational")

    comp = gemini.qualify_competitor("competitor.com", ["Vitamin C Serum"])
    assert "is_competitor" in comp

    brief = gemini.generate_content_brief({"title": "Vitamin C Guide"}, [])
    assert "suggested_sections" in brief

    draft = gemini.generate_draft({"title": "Vitamin C Guide", "suggested_sections": ["Intro"]})
    assert "body" in draft
