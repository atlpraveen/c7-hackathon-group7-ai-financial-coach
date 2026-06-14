from typing import TypedDict, List

class FinancialState(TypedDict):
    query: str
    tasks: List[str]
    results: dict
