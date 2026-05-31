from __future__ import annotations

import asyncio
import queue
from typing import Any, AsyncIterator, Callable

from .schemas import CustomerCard, StepEvent

EmitFn = Callable[[StepEvent], None]


def _emit(state: dict, event: StepEvent) -> None:
    emit: EmitFn | None = state.get("emit")
    if emit is None:
        return
    try:
        emit(event)
    except Exception:
        # An emit failure must never break graph execution.
        pass


def node_started(state: dict, node: str, label: str) -> None:
    _emit(state, StepEvent(type="node_started", node=node, label=label))


def node_finished(state: dict, node: str, ms: int) -> None:
    _emit(state, StepEvent(type="node_finished", node=node, ms=ms))


def tool_call(state: dict, node: str, tool: str, args: dict[str, Any]) -> None:
    _emit(state, StepEvent(type="tool_call", node=node, tool=tool, args=args))


def tool_result(state: dict, node: str, tool: str, preview: str) -> None:
    _emit(state, StepEvent(type="tool_result", node=node, tool=tool, preview=preview))


def card(state: dict, c: CustomerCard) -> None:
    _emit(state, StepEvent(type="card", card=c))


def done(state: dict) -> None:
    _emit(state, StepEvent(type="done"))


def error(state: dict, message: str) -> None:
    _emit(state, StepEvent(type="error", message=message))


_SENTINEL = object()


class EventBus:
    """Thread-safe pub/sub between the sync graph (worker thread) and the
    async NDJSON generator."""

    def __init__(self, max_size: int = 1024) -> None:
        self._q: queue.Queue = queue.Queue(maxsize=max_size)
        self._closed = False

    def emit(self, event: StepEvent) -> None:
        if self._closed:
            return
        try:
            self._q.put_nowait(event)
        except queue.Full:
            # Drop oldest, keep latest — never block the graph thread.
            try:
                self._q.get_nowait()
            except queue.Empty:
                pass
            self._q.put_nowait(event)

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        try:
            self._q.put_nowait(_SENTINEL)  # type: ignore[arg-type]
        except queue.Full:
            pass

    async def stream(self) -> AsyncIterator[StepEvent]:
        loop = asyncio.get_running_loop()
        while True:
            item = await loop.run_in_executor(None, self._q.get)
            if item is _SENTINEL:
                return
            yield item  # type: ignore[misc]
