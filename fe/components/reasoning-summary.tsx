"use client";

import { useState } from "react";
import { ChevronDown, ChevronRight, Loader2, Sparkles } from "lucide-react";

import { ReasoningLog } from "@/components/reasoning-log";
import type { AssistantTurn } from "@/hooks/use-chat-stream";

function fmtSeconds(ms?: number): string {
  if (!ms) return "…";
  const s = ms / 1000;
  return s >= 10 ? `${s.toFixed(0)}s` : `${s.toFixed(1)}s`;
}

function liveSummary(turn: AssistantTurn): string {
  // While streaming, show the current node label
  for (let i = turn.events.length - 1; i >= 0; i--) {
    const ev = turn.events[i];
    if (ev.type === "node_started") return ev.label;
    if (ev.type === "tool_result" && ev.preview)
      return ev.preview.length > 60 ? ev.preview.slice(0, 57) + "…" : ev.preview;
  }
  return "Thinking…";
}

export function ReasoningSummary({ turn }: { turn: AssistantTurn }) {
  const [expanded, setExpanded] = useState(false);
  const streaming = turn.status === "streaming";
  const cardsCount = turn.cards.length;

  const headerLabel = streaming
    ? liveSummary(turn)
    : turn.error
      ? "Failed — click to inspect"
      : `Thought for ${fmtSeconds(turn.durationMs)} · ${cardsCount} card${cardsCount === 1 ? "" : "s"}`;

  return (
    <div className="rounded-md border bg-zinc-950/40">
      <button
        type="button"
        onClick={() => setExpanded((v) => !v)}
        className="flex w-full items-center gap-2 px-3 py-2 text-left text-xs hover:bg-muted/40"
        aria-expanded={expanded}
      >
        {streaming ? (
          <Loader2 className="size-3.5 shrink-0 animate-spin text-amber-400" />
        ) : turn.error ? (
          <span className="size-2 shrink-0 rounded-full bg-rose-500" />
        ) : (
          <Sparkles className="size-3.5 shrink-0 text-emerald-400" />
        )}
        <span
          className={`truncate ${
            streaming ? "text-amber-300" : turn.error ? "text-rose-300" : "text-zinc-300"
          }`}
        >
          {headerLabel}
        </span>
        <span className="ml-auto text-zinc-500">
          {expanded ? <ChevronDown className="size-3.5" /> : <ChevronRight className="size-3.5" />}
        </span>
      </button>

      {expanded && (
        <div className="border-t p-2">
          <div className="h-64">
            <ReasoningLog events={turn.events} isStreaming={streaming} />
          </div>
        </div>
      )}
    </div>
  );
}
