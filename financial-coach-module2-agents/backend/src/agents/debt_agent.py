from .base_agent import BaseAgent

class DebtAgent(BaseAgent):
    async def execute(self, payload:dict):
        return {'agent':'debt','result':'analysis complete'}
