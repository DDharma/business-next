"use client";

import { useEffect, useRef } from "react";
import { useRouter } from "next/navigation";

import { ChatInput } from "@/components/chat-input";
import { MessageAssistant } from "@/components/message-assistant";
import { MessageUser } from "@/components/message-user";
import { Skeleton } from "@/components/ui/skeleton";
import { useChatStream } from "@/hooks/use-chat-stream";

type Props = { chatId?: string };

const SAMPLE_PROMPTS = [
  "Find 5 high-value personal-loan prospects in Mumbai",
  "Show me 3 credit card prospects in Bengaluru",
  "Top customers for a home loan, salaried, above ₹1L/mo",
];

export function ChatThread({ chatId: initialId }: Props) {
  const router = useRouter();
  const stream = useChatStream(initialId ?? null);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Push the new chat_id into the URL once the backend assigns one
  useEffect(() => {
    if (stream.chatId && stream.chatId !== initialId) {
      router.replace(`/chat/${stream.chatId}`, { scroll: false });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [stream.chatId]);

  // Auto-scroll to bottom when turns grow or stream updates
  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    el.scrollTop = el.scrollHeight;
  }, [stream.turns.length, stream.turns[stream.turns.length - 1]?.assistant.events.length]);

  const empty = !stream.isLoadingHistory && stream.turns.length === 0;

  return (
    <div className="flex h-full min-h-0 flex-col">
      <header className="flex items-center border-b px-6 py-3">
        <div className="text-sm font-semibold tracking-wide">Banking CRM Agent</div>
        <div className="ml-3 text-xs text-muted-foreground">
          {stream.chatId ? `Chat · ${stream.chatId.slice(0, 8)}` : "New chat"}
        </div>
      </header>

      <div ref={scrollRef} className="flex-1 overflow-y-auto">
        <div className="mx-auto w-full max-w-3xl px-4 py-6">
          {stream.isLoadingHistory && (
            <div className="space-y-6">
              {Array.from({ length: 2 }).map((_, i) => (
                <div key={i} className="space-y-2">
                  <Skeleton className="ml-auto h-10 w-2/3 rounded-2xl" />
                  <Skeleton className="h-10 w-full rounded-md" />
                </div>
              ))}
            </div>
          )}

          {empty && (
            <EmptyState
              onPick={(p) => {
                stream.send(p);
              }}
            />
          )}

          {!stream.isLoadingHistory && stream.turns.length > 0 && (
            <ol className="space-y-6">
              {stream.turns.map((turn) => (
                <li key={turn.id} className="space-y-3">
                  <MessageUser text={turn.user} />
                  <MessageAssistant turn={turn.assistant} />
                </li>
              ))}
            </ol>
          )}
        </div>
      </div>

      <div className="border-t bg-background/60 px-4 py-3 backdrop-blur">
        <div className="mx-auto max-w-3xl">
          <ChatInput
            disabled={stream.isStreaming}
            onSubmit={(text) => stream.send(text)}
          />
        </div>
      </div>
    </div>
  );
}

function EmptyState({ onPick }: { onPick: (text: string) => void }) {
  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center text-center">
      <div className="text-xl font-semibold tracking-tight">
        Find your next high-value prospect
      </div>
      <p className="mt-2 max-w-md text-sm text-muted-foreground">
        Ask in plain English — the agent retrieves customers, scores them, and
        drafts a personalized WhatsApp message for each.
      </p>
      <div className="mt-6 flex w-full max-w-xl flex-col gap-2">
        {SAMPLE_PROMPTS.map((p) => (
          <button
            key={p}
            type="button"
            onClick={() => onPick(p)}
            className="rounded-lg border bg-card px-4 py-3 text-left text-sm transition-colors hover:bg-muted"
          >
            {p}
          </button>
        ))}
      </div>
    </div>
  );
}
