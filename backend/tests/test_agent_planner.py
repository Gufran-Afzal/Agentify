from backend.app.agents.planner import ResearchPlanner
from backend.app.agents.state import (
    ResearchState,
    EvidenceItem,
    EvidenceType,
    SourceType,
    ResearchBudget,
)
from backend.app.agents.actions import ActionType, PlannerDecisionType

def test_planner_priority_flow():
    planner = ResearchPlanner()
    state = ResearchState()

    # 1. No products -> ANALYZE_STORE
    dec1 = planner.decide(state)
    assert dec1.decision == PlannerDecisionType.RESEARCH_MORE
    assert dec1.action.action_type == ActionType.ANALYZE_STORE

    # Add product
    state.add_evidence(EvidenceItem(
        evidence_type=EvidenceType.STORE_PRODUCT,
        source_type=SourceType.STORE_DATABASE,
    ))

    # 2. Has products, no content -> ANALYZE_EXISTING_CONTENT
    dec2 = planner.decide(state)
    assert dec2.decision == PlannerDecisionType.RESEARCH_MORE
    assert dec2.action.action_type == ActionType.ANALYZE_EXISTING_CONTENT

    # Add existing content
    state.add_evidence(EvidenceItem(
        evidence_type=EvidenceType.EXISTING_CONTENT,
        source_type=SourceType.STORE_DATABASE,
    ))

    # 3. Has products & content, no keywords -> DISCOVER_KEYWORDS
    dec3 = planner.decide(state)
    assert dec3.decision == PlannerDecisionType.RESEARCH_MORE
    assert dec3.action.action_type == ActionType.DISCOVER_KEYWORDS

    # Add keyword
    state.add_evidence(EvidenceItem(
        evidence_type=EvidenceType.KEYWORD,
        source_type=SourceType.KEYWORD_PROVIDER,
    ))

    # 4. All minimum evidence present -> GENERATE_OPPORTUNITIES
    dec4 = planner.decide(state)
    assert dec4.decision == PlannerDecisionType.GENERATE_OPPORTUNITIES

def test_planner_budget_stop():
    planner = ResearchPlanner()
    state = ResearchState(
        research_budget=ResearchBudget(max_iterations=1, iterations_used=1)
    )
    dec = planner.decide(state)
    assert dec.decision == PlannerDecisionType.STOP
    assert "budget exhausted" in dec.reason.lower()
