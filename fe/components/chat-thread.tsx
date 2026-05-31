"use client";

import { useCallback, useEffect, useRef } from "react";
import { useParams, useRouter } from "next/navigation";

import { useAppShell } from "@/components/app-shell";
import { ChatInput } from "@/components/chat-input";
import { MessageAssistant } from "@/components/message-assistant";
import { MessageUser } from "@/components/message-user";
import { Skeleton } from "@/components/ui/skeleton";
import { SAMPLE_PROMPTS } from "@/utils/constants";

type EmptyStateProps = { onPick: (text: string) => void };

const EmptyState = ({ onPick }: EmptyStateProps) => (
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

export const ChatThread = () => {
  const router = useRouter();
  const params = useParams();
  const urlChatId =
    typeof params?.id === "string" ? params.id : null;

  const { loadChat, send, bumpSidebar, chatId, turns, isStreaming, isLoadingHistory } =
    useAppShell();
  const scrollRef = useRef<HTMLDivElement>(null);

  // URL → state. loadChat is a no-op when the ctx already holds this id,
  // which makes the post-send router.replace round-trip free.
  useEffect(() => {
    loadChat(urlChatId);
  }, [urlChatId, loadChat]);

  // Imperative navigation: only after send() resolves, and only when the
  // resulting chatId differs from what the URL already shows.
  const handleSubmit = useCallback(
    async (text: string) => {
      const fromUrl = urlChatId;
      const newId = await send(text);
      if (newId && newId !== fromUrl) {
        router.replace(`/chat/${newId}`, { scroll: false });
        bumpSidebar();
      }
    },
    [urlChatId, send, router, bumpSidebar],
  );

  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    el.scrollTop = el.scrollHeight;
  }, [turns.length, turns[turns.length - 1]?.assistant.events.length]);

  const empty = !isLoadingHistory && turns.length === 0;

  return (
    <div className="flex h-full min-h-0 flex-col">
      <header className="flex items-baseline border-b px-6 py-3">
        <div className="text-base font-semibold tracking-tight">Lakshya</div>
        <div className="ml-2 text-xs uppercase tracking-widest text-muted-foreground">
          Find your next prospect
        </div>
        <div className="ml-auto text-xs text-muted-foreground">
          {chatId ? `Chat · ${chatId.slice(0, 8)}` : "New chat"}
        </div>
      </header>

      <div ref={scrollRef} className="flex-1 overflow-y-auto">
        <div className="mx-auto w-full max-w-3xl px-4 py-6">
          {isLoadingHistory && (
            <div className="space-y-6">
              {Array.from({ length: 2 }).map((_, i) => (
                <div key={i} className="space-y-2">
                  <Skeleton className="ml-auto h-10 w-2/3 rounded-2xl" />
                  <Skeleton className="h-10 w-full rounded-md" />
                </div>
              ))}
            </div>
          )}

          {empty && <EmptyState onPick={handleSubmit} />}

          {!isLoadingHistory && turns.length > 0 && (
            <ol className="space-y-6">
              {turns.map((turn) => (
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
          <ChatInput disabled={isStreaming} onSubmit={handleSubmit} />
        </div>
      </div>
    </div>
  );
};
