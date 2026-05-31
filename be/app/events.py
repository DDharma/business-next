"""
Event emitter helpers + an EventBus used by the streaming /chat endpoint.

Nodes push StepEvents via a sync `emit` callable on the GraphState. For the
CLI driver this is just `print`. For the HTTP endpoint we use `EventBus`:
nodes (running in a worker thread) push into a thread-safe queue.Queue,
and the async NDJSON generator drains the queue via `run_in_executor` so
events stream to the browser in real time.
"""

from __future__ import annotations

import asyncio
import queue
from typing import Any, AsyncIterator, Callable

from .schemas import CustomerCard, StepEvent

EmitFn = Callable[[StepEvent], None]


# ── module-level helpers used by the nodes ───────────────────────────────

def _emit(state: dict, event: StepEvent) -> None:
    emit: EmitFn | None = state.get("emit")
    if emit is not None:
        try:
            emit(event)
        except Exception:
            # Never let an emit failure break graph execution
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


# ── EventBus for streaming ───────────────────────────────────────────────

_SENTINEL = object()


class EventBus:
    """
    Thread-safe pub/sub for a single request. The graph (running in a
    worker thread) calls `bus.emit(event)`; the async NDJSON generator
    calls `async for ev in bus.stream(): ...`.
    """

    def __init__(self, max_size: int = 1024) -> None:
        self._q: queue.Queue = queue.Queue(maxsize=max_size)
        self._closed = False

    # Called from the worker thread (sync context)
    def emit(self, event: StepEvent) -> None:
        if self._closed:
            return
        try:
            self._q.put_nowait(event)
        except queue.Full:
            # Drop oldest, keep latest — better than blocking the graph
            try:
                self._q.get_nowait()
            except queue.Empty:
                pass
            self._q.put_nowait(event)

    def close(self) -> None:
        """Signal end-of-stream to consumers."""
        if not self._closed:
            self._closed = True
            try:
                self._q.put_nowait(_SENTINEL)  # type: ignore[arg-type]
            except queue.Full:
                pass

    async def stream(self) -> AsyncIterator[StepEvent]:
        """Drain the queue from an async context until close()."""
        loop = asyncio.get_running_loop()
        while True:
            item = await loop.run_in_executor(None, self._q.get)
            if item is _SENTINEL:
                return
            yield item  # type: ignore[misc]
