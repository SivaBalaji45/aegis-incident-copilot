from aegis.agents.graph import _route_after_critic, build_graph
from aegis.config import settings
from aegis.guardrails.schemas import CriticVerdict


def test_graph_compiles_with_expected_nodes():
    graph = build_graph()
    node_names = set(graph.get_graph().nodes.keys())

    assert {"triage", "retrieval", "diagnosis", "critic", "draft"} <= node_names


def test_route_after_critic_proceeds_to_draft_when_grounded():
    state = {
        "critic": CriticVerdict(grounded=True, groundedness_score=0.9),
        "critic_iterations": 1,
    }
    assert _route_after_critic(state) == "draft"


def test_route_after_critic_retries_when_ungrounded_and_budget_remains():
    state = {
        "critic": CriticVerdict(grounded=False, groundedness_score=0.3, refined_query="q"),
        "critic_iterations": 1,
    }
    assert settings.aegis_max_critic_retries >= 2
    assert _route_after_critic(state) == "retry"


def test_route_after_critic_gives_up_after_max_retries():
    state = {
        "critic": CriticVerdict(grounded=False, groundedness_score=0.2),
        "critic_iterations": settings.aegis_max_critic_retries,
    }
    assert _route_after_critic(state) == "give_up"
