from .base_agent import BaseAgent

class BudgetAgent(BaseAgent):
    async def execute(self, payload:dict):
        return {'agent':'budget','result':'budget optimized'}
