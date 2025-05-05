

class AgentException(Exception):
    pass

class LLMError(AgentException):
    
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)
        