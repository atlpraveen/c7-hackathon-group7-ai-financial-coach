from .base_agent import BaseAgent

class SavingsAgent(BaseAgent):
    async def execute(self, payload:dict):
        return {'agent':'savings','result':'plan created'}
