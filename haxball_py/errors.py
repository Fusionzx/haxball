class HaxballError(RuntimeError):
    """Base error for the library."""

class HaxballBridgeError(HaxballError):
    """Raised when the browser bridge fails."""

class HaxballNotReadyError(HaxballError):
    """Raised when a room method is used before initialization."""

class HaxballTimeoutError(HaxballError):
    """Raised when the browser bridge times out."""
