from backend.app.agents.state import (
    ResearchState,
    EvidenceItem,
    EvidenceType,
    SourceType,
    ResearchBudget,
    ConfidenceLevel,
    OpportunityDraft,
)

def test_research_state_defaults():
    state = ResearchState(research_run_id=1, store_id="test-store")
    assert state.research_run_id == 1
    assert state.store_id == "test-store"
    assert len(state.evidence) == 0
    assert not state.is_evidence_sufficient()

def test_add_evidence_and_query():
    state = ResearchState(research_run_id=42, store_id="demo-store")
    item1 = EvidenceItem(
        evidence_type=EvidenceType.STORE_PRODUCT,
        source_type=SourceType.STORE_DATABASE,
        data={"name": "Serum"},
    )
    item2 = EvidenceItem(
        evidence_type=EvidenceType.KEYWORD,
        source_type=SourceType.KEYWORD_PROVIDER,
        data={"keyword": "best serum"},
    )
    state.add_evidence(item1)
    state.add_evidence(item2)

    assert state.has_evidence_of_type(EvidenceType.STORE_PRODUCT)
    assert state.has_evidence_of_type(EvidenceType.KEYWORD)
    assert not state.has_evidence_of_type(EvidenceType.EXISTING_CONTENT)

    counts = state.evidence_count_by_type()
    assert counts[EvidenceType.STORE_PRODUCT.value] == 1
    assert counts[EvidenceType.KEYWORD.value] == 1

    fetched = state.get_evidence_by_ids([item1.id])
    assert len(fetched) == 1
    assert fetched[0].data["name"] == "Serum"

def test_evidence_sufficiency():
    state = ResearchState()
    assert not state.is_evidence_sufficient()

    state.add_evidence(EvidenceItem(
        evidence_type=EvidenceType.STORE_PRODUCT,
        source_type=SourceType.STORE_DATABASE,
    ))
    assert not state.is_evidence_sufficient()

    state.add_evidence(EvidenceItem(
        evidence_type=EvidenceType.KEYWORD,
        source_type=SourceType.KEYWORD_PROVIDER,
    ))
    assert not state.is_evidence_sufficient()

    state.add_evidence(EvidenceItem(
        evidence_type=EvidenceType.EXISTING_CONTENT,
        source_type=SourceType.STORE_DATABASE,
    ))
    assert state.is_evidence_sufficient()

def test_research_budget_exhaustion():
    budget = ResearchBudget(max_iterations=3, max_searches=2)
    exhausted, _ = budget.is_exhausted()
    assert not exhausted

    budget.iterations_used = 3
    exhausted, reason = budget.is_exhausted()
    assert exhausted
    assert "max_iterations" in reason

    budget.iterations_used = 0
    budget.searches_used = 2
    exhausted, reason = budget.is_exhausted()
    assert exhausted
    assert "max_searches" in reason

def test_opportunity_draft_model():
    draft = OpportunityDraft(
        topic="Vitamin C Guide",
        primary_keyword="vitamin c serum",
        why_it_matters="High search volume with catalog match",
        confidence_level=ConfidenceLevel.STRONG,
    )
    assert draft.topic == "Vitamin C Guide"
    assert draft.confidence_level == ConfidenceLevel.STRONG
