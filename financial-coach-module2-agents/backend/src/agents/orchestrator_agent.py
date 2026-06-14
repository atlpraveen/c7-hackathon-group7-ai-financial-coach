from .agent_registry import AgentRegistry

class OrchestratorAgent:
    def __init__(self, registry: AgentRegistry):
        self.registry = registry

    async def route(self, task_type:str, payload:dict):
        agent = self.registry.get(task_type)
        return await agent.execute(payload)
