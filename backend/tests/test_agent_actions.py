from backend.app.agents.actions import (
    ActionType,
    ResearchAction,
    PlannerDecision,
    PlannerDecisionType,
)
from backend.app.agents.state import ResearchBudget

def test_research_action_budget_allowed():
    budget = ResearchBudget(max_searches=10)
    action = ResearchAction(
        action_type=ActionType.DISCOVER_KEYWORDS,
        arguments={"limit": 10},
        reason="Find keywords",
    )
    allowed, msg = action.can_execute(budget)
    assert allowed
    assert msg == "ok"

def test_research_action_budget_blocked():
    budget = ResearchBudget(max_searches=1, searches_used=1)
    action = ResearchAction(
        action_type=ActionType.DISCOVER_KEYWORDS,
        reason="Find keywords",
    )
    allowed, reason = action.can_execute(budget)
    assert not allowed
    assert "max_searches" in reason

def test_planner_decision_terminal():
    dec_more = PlannerDecision(
        decision=PlannerDecisionType.RESEARCH_MORE,
        reason="Need more keywords",
        action=ResearchAction(action_type=ActionType.DISCOVER_KEYWORDS),
    )
    assert not dec_more.is_terminal()

    dec_gen = PlannerDecision(
        decision=PlannerDecisionType.GENERATE_OPPORTUNITIES,
        reason="Evidence sufficient",
    )
    assert dec_gen.is_terminal()

    dec_stop = PlannerDecision(
        decision=PlannerDecisionType.STOP,
        reason="Budget exhausted",
    )
    assert dec_stop.is_terminal()
