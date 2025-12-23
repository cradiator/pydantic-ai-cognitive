from collections.abc import Iterable, Iterator

from pydantic_ai.messages import ModelMessage, ModelRequestPart, ModelResponsePart


class EnumerateMessageWithParts:
    """
    Enumerable over all parts in the message history.
    """

    def __init__(self, history: Iterable[ModelMessage]):
        self.history = history

    def __iter__(self) -> Iterator[tuple[ModelMessage, list[ModelRequestPart | ModelResponsePart]]]:
        """
        Yields:
            A tuple containing the message and the list of parts.
        """
        for message in self.history:
            parts = getattr(message, "parts", [])
            yield message, parts
