from .base_agent import BaseAgent

class InvestmentAgent(BaseAgent):
    async def execute(self, payload:dict):
        return {'agent':'investment','result':'allocation generated'}
