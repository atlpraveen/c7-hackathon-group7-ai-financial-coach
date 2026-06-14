from abc import ABC, abstractmethod

class BaseAgent(ABC):
    def __init__(self, name:str):
        self.name = name

    @abstractmethod
    async def execute(self, payload:dict):
        pass
