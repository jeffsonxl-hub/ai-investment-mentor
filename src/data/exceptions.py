"""Custom exceptions for the data layer."""


class DataFetchError(Exception):
    """Wraps data source failures with the source name and original exception.

    Used by TuShareClient for all fetch errors. AkShareClient returns empty
    results instead of raising — this exception is used by TuShareClient only.
    """

    def __init__(self, source: str, message: str, original: Exception | None = None):
        self.source = source
        self.original = original
        super().__init__(f"{source}: {message}")
