"""Tiny publish/subscribe bus for decoupled gameplay reactions."""

from collections.abc import Callable
from typing import Any


Subscriber = Callable[..., None]


class EventBus:
    def __init__(self) -> None:
        self._subscribers: dict[str, list[Subscriber]] = {}

    def subscribe(self, event_name: str, callback: Subscriber) -> None:
        self._subscribers.setdefault(event_name, []).append(callback)

    def publish(self, event_name: str, **payload: Any) -> None:
        for callback in tuple(self._subscribers.get(event_name, ())):
            callback(**payload)

    def clear(self) -> None:
        self._subscribers.clear()
