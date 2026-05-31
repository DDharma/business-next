"use client";

import { CustomerCard } from "@/components/customer-card";
import { ReasoningSummary } from "@/components/reasoning-summary";
import { Skeleton } from "@/components/ui/skeleton";
import type { AssistantTurn } from "@/hooks/use-chat-stream";
import { StreamStatus } from "@/utils/enums";

type Props = { turn: AssistantTurn };

export const MessageAssistant = ({ turn }: Props) => (
  <div className="flex flex-col gap-3">
    <ReasoningSummary turn={turn} />

    {turn.error && (
      <div className="rounded-md border border-rose-500/30 bg-rose-500/10 px-3 py-2 text-sm text-rose-300">
        {turn.error}
      </div>
    )}

    {turn.cards.length > 0 && (
      <div className="flex flex-col gap-3">
        {turn.cards.map((c) => (
          <CustomerCard key={c.customer_id} card={c} />
        ))}
      </div>
    )}

    {turn.status === StreamStatus.Streaming && turn.cards.length === 0 && (
      <div className="flex flex-col gap-3">
        <Skeleton className="h-56 w-full rounded-xl" />
      </div>
    )}
  </div>
);
