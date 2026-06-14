"""LangGraph multi-agent orchestration graph.

Builds a StateGraph: a router node selects the relevant specialists, every
specialist runs as its own node (fanned out in parallel from the router and
fanned back into a single synthesis node), and the synthesis node composes one
prioritised plan. Returns ``None`` if LangGraph isn't installed, so the
Orchestrator falls back to its asyncio engine.

NOTE: this module deliberately does NOT use ``from __future__ import
annotations``. LangGraph calls ``get_type_hints()`` on each node function, which
must resolve the locally-defined ``State`` TypedDict — that only works when the
annotations are real objects (evaluated at def-time), not deferred strings.
"""
import operator
from typing import Annotated, Callable, Optional, TypedDict


def build_graph(
    agents: dict,
    route_fn: Callable[[Optional[str]], list],
    synthesize_fn: Callable[[list, dict, Optional[str]], tuple],
):
    try:
        from langgraph.graph import END, START, StateGraph
    except Exception:  # pragma: no cover - optional dependency
        return None

    class State(TypedDict, total=False):
        profile: dict
        query: Optional[str]
        params: dict
        selected: list
        results: Annotated[list, operator.add]
        synthesis: str
        generated_by: str

    def router(state: State) -> dict:
        return {"selected": route_fn(state.get("query"))}

    def make_node(name: str) -> Callable[[State], dict]:
        def node(state: State) -> dict:
            if name not in state.get("selected", []):
                return {}
            res = agents[name].run(state["profile"], state.get("params") or {})
            return {"results": [res]}

        return node

    def synthesize(state: State) -> dict:
        text, by = synthesize_fn(state.get("results", []), state["profile"], state.get("query"))
        return {"synthesis": text, "generated_by": by}

    g = StateGraph(State)
    g.add_node("router", router)
    g.add_node("synthesize", synthesize)
    g.add_edge(START, "router")
    for name in agents:
        g.add_node(name, make_node(name))
        g.add_edge("router", name)
        g.add_edge(name, "synthesize")
    g.add_edge("synthesize", END)
    return g.compile()
