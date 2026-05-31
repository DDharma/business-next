"use client";

import { useCallback, useRef, useState } from "react";

import { getChat } from "@/lib/api";
import { streamChat } from "@/lib/stream";
import type { Chat, CustomerCard, StepEvent } from "@/lib/types";
import { MessageRole, StreamStatus } from "@/utils/enums";

export type AssistantTurn = {
  events: StepEvent[];
  cards: CustomerCard[];
  durationMs?: number;
  status: StreamStatus;
  error?: string;
};

export type Turn = {
  id: string;
  user: string;
  assistant: AssistantTurn;
};

export type UseChatStream = {
  chatId: string | null;
  turns: Turn[];
  isStreaming: boolean;
  isLoadingHistory: boolean;
  send: (message: string) => Promise<string | null>;
  cancel: () => void;
  loadChat: (id: string | null) => Promise<void>;
};

const newTurnId = (): string => Math.random().toString(36).slice(2, 10);

const turnsFromChat = (chat: Chat): Turn[] => {
  const out: Turn[] = [];
  const msgs = [...chat.messages].sort(
    (a, b) => a.created_at.localeCompare(b.created_at),
  );
  for (let i = 0; i < msgs.length; i++) {
    const m = msgs[i];
    if (m.role !== MessageRole.User) continue;
    const next = msgs[i + 1];
    const assistant = next?.role === MessageRole.Assistant ? next : null;
    out.push({
      id: m.id,
      user: m.content,
      assistant: {
        events: assistant?.metadata?.events ?? [],
        cards: assistant?.metadata?.cards ?? [],
        durationMs: assistant?.metadata?.duration_ms,
        status: assistant?.metadata?.error ? StreamStatus.Error : StreamStatus.Done,
        error: assistant?.metadata?.error ?? undefined,
      },
    });
  }
  return out;
};

export const useChatStream = (): UseChatStream => {
  const [chatId, setChatId] = useState<string | null>(null);
  const [turns, setTurns] = useState<Turn[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [isLoadingHistory, setLoadingHistory] = useState(false);

  const chatIdRef = useRef<string | null>(null);
  chatIdRef.current = chatId;

  const abortRef = useRef<AbortController | null>(null);
  const loadInflightRef = useRef<string | null>(null);

  const loadChat = useCallback(async (id: string | null) => {
    // No-op if we already have this chat loaded (or are loading it).
    // This is what kills the post-stream remount flash: router.replace
    // fires AFTER chatId is set internally, so by the time URL→loadChat
    // runs, the id matches and we bail out.
    if (id === chatIdRef.current) return;
    if (id && loadInflightRef.current === id) return;

    abortRef.current?.abort();
    abortRef.current = null;

    setChatId(id);
    setTurns([]);
    setIsStreaming(false);

    if (!id) {
      setLoadingHistory(false);
      loadInflightRef.current = null;
      return;
    }

    loadInflightRef.current = id;
    setLoadingHistory(true);
    try {
      const chat = await getChat(id);
      if (loadInflightRef.current === id) {
        setTurns(turnsFromChat(chat));
      }
    } catch (e) {
      console.error("rehydrate failed", e);
    } finally {
      if (loadInflightRef.current === id) {
        loadInflightRef.current = null;
        setLoadingHistory(false);
      }
    }
  }, []);

  const cancel = useCallback(() => {
    abortRef.current?.abort();
    abortRef.current = null;
  }, []);

  const send = useCallback(
    async (message: string): Promise<string | null> => {
      const text = message.trim();
      if (!text || isStreaming) return chatIdRef.current;

      const turnId = newTurnId();
      setTurns((prev) => [
        ...prev,
        {
          id: turnId,
          user: text,
          assistant: { events: [], cards: [], status: StreamStatus.Streaming },
        },
      ]);
      setIsStreaming(true);

      const ac = new AbortController();
      abortRef.current = ac;

      const patchTurn = (mutator: (a: AssistantTurn) => AssistantTurn) => {
        setTurns((prev) => {
          if (prev.length === 0) return prev;
          const last = prev[prev.length - 1];
          if (last.id !== turnId) return prev;
          return [
            ...prev.slice(0, -1),
            { ...last, assistant: mutator(last.assistant) },
          ];
        });
      };

      await streamChat(
        { chat_id: chatIdRef.current, message: text },
        {
          signal: ac.signal,
          onEvent: (ev) => {
            if (ev.type === "chat_id") {
              setChatId(ev.chat_id);
              return;
            }
            if (ev.type === "done") {
              patchTurn((a) => ({
                ...a,
                durationMs: ev.duration_ms,
                status: a.error ? StreamStatus.Error : StreamStatus.Done,
              }));
              return;
            }
            patchTurn((a) => {
              const next: AssistantTurn = { ...a, events: [...a.events, ev] };
              if (ev.type === "card") next.cards = [...a.cards, ev.card];
              if (ev.type === "error") {
                next.error = ev.message;
                next.status = StreamStatus.Error;
              }
              return next;
            });
          },
          onError: (e) => {
            patchTurn((a) => ({ ...a, status: StreamStatus.Error, error: e.message }));
          },
          onClose: () => {
            setIsStreaming(false);
            patchTurn((a) =>
              a.status === StreamStatus.Streaming ? { ...a, status: StreamStatus.Done } : a,
            );
          },
        },
      );

      return chatIdRef.current;
    },
    [isStreaming],
  );

  return { chatId, turns, isStreaming, isLoadingHistory, send, cancel, loadChat };
};
