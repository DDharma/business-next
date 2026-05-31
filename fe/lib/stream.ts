import { API_BASE } from "@/utils/constants";
import type { StepEvent } from "./types";

export type StreamEvent =
  | { type: "chat_id"; chat_id: string }
  | { type: "done"; chat_id: string; cards: number; duration_ms: number }
  | StepEvent;

export type StreamCallbacks = {
  onEvent: (ev: StreamEvent) => void;
  onError?: (err: Error) => void;
  onClose?: () => void;
  signal?: AbortSignal;
};

export const streamChat = async (
  body: { chat_id?: string | null; message: string },
  cb: StreamCallbacks,
): Promise<void> => {
  let res: Response;
  try {
    res = await fetch(`${API_BASE}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal: cb.signal,
    });
  } catch (e) {
    if ((e as Error).name !== "AbortError") cb.onError?.(e as Error);
    cb.onClose?.();
    return;
  }

  if (!res.ok || !res.body) {
    cb.onError?.(new Error(`POST /chat → ${res.status}`));
    cb.onClose?.();
    return;
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buf = "";

  try {
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buf += decoder.decode(value, { stream: true });

      let idx: number;
      while ((idx = buf.indexOf("\n")) !== -1) {
        const line = buf.slice(0, idx).trim();
        buf = buf.slice(idx + 1);
        if (!line) continue;
        try {
          cb.onEvent(JSON.parse(line) as StreamEvent);
        } catch {
          // skip malformed line
        }
      }
    }
    const tail = buf.trim();
    if (tail) {
      try {
        cb.onEvent(JSON.parse(tail) as StreamEvent);
      } catch {
        // ignore
      }
    }
  } catch (e) {
    if ((e as Error).name !== "AbortError") cb.onError?.(e as Error);
  } finally {
    cb.onClose?.();
  }
};
