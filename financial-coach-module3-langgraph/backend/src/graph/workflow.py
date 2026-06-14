from langgraph.graph import StateGraph
from .state import FinancialState
from .router_node import router_node

def build_workflow():
    workflow = StateGraph(FinancialState)
    workflow.add_node('router', router_node)
    workflow.set_entry_point('router')
    return workflow.compile()
