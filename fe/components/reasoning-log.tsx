"use client";

import { useEffect, useRef } from "react";

import { ScrollArea } from "@/components/ui/scroll-area";
import type { StepEvent } from "@/lib/types";

const renderEvent = (ev: StepEvent, i: number) => {
  switch (ev.type) {
    case "node_started":
      return (
        <div key={i} className="mt-3">
          <span className="text-emerald-400">┌─ </span>
          <span className="font-semibold text-emerald-300">{ev.node}</span>
          <span className="text-zinc-500"> · {ev.label}</span>
        </div>
      );
    case "tool_call": {
      const args = Object.entries(ev.args ?? {})
        .map(([k, v]) => `${k}=${typeof v === "object" ? JSON.stringify(v) : v}`)
        .join(", ");
      return (
        <div key={i} className="text-zinc-400">
          <span className="text-zinc-600">│  → </span>
          <span className="text-amber-300">{ev.tool}</span>
          <span className="text-zinc-500">({args})</span>
        </div>
      );
    }
    case "tool_result":
      return (
        <div key={i} className="text-zinc-300">
          <span className="text-zinc-600">│  ← </span>
          {ev.preview}
        </div>
      );
    case "node_finished":
      return (
        <div key={i} className="text-zinc-500">
          <span className="text-emerald-400">└─ </span>
          {ev.node} done in {ev.ms} ms
        </div>
      );
    case "card":
      return (
        <div key={i} className="text-sky-400">
          <span className="text-zinc-600">·  </span>
          card: {ev.card.name} ({ev.card.score.toFixed(1)})
        </div>
      );
    case "error":
      return (
        <div key={i} className="text-rose-400">
          !! {ev.message}
        </div>
      );
    default:
      return null;
  }
};

type Props = { events: StepEvent[]; isStreaming: boolean };

export const ReasoningLog = ({ events, isStreaming }: Props) => {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = ref.current?.querySelector(
      "[data-radix-scroll-area-viewport]",
    ) as HTMLElement | null;
    if (el) el.scrollTop = el.scrollHeight;
  }, [events.length]);

  return (
    <div ref={ref} className="h-full">
      <ScrollArea className="h-full rounded-md border bg-zinc-950 px-4 py-3">
        <div className="font-mono text-xs leading-relaxed text-zinc-300">
          {events.length === 0 && !isStreaming && (
            <div className="text-zinc-600">
              The agent&apos;s reasoning will stream here.
            </div>
          )}
          {events.map(renderEvent)}
          {isStreaming && (
            <div className="mt-2 inline-block animate-pulse text-emerald-400">
              ▌
            </div>
          )}
        </div>
      </ScrollArea>
    </div>
  );
};
