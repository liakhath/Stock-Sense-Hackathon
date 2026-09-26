class StockError(Exception):
    """Base error for the stock engine."""


class NotFound(StockError):
    """Product, location or operation does not exist."""


class InvalidOperation(StockError):
    """The action isn't allowed in the current state."""


class InsufficientStock(StockError):
    """Not enough stock to complete the move."""


class ApprovalRequired(StockError):
    """A large adjustment needs a manager's approval first."""