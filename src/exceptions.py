class InvalidActionError(Exception):
    pass

class InsufficientFundsError(Exception):
    pass

class GameError(Exception):
    pass

class InvalidHandError(Exception):
    def __init__(self, message="ręka jest niepoprawna."):
        self.message = message
        super().__init__(self.message)