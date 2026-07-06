"""Custom exception for MemoryRepository errors."""


class MemoryRepositoryError(Exception):
    """Wraps all storage-layer errors so callers are decoupled from SQLite."""
    pass
