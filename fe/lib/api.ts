import type { Chat, ChatSummary } from "./types";

export const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function listChats(): Promise<ChatSummary[]> {
  const res = await fetch(`${API_BASE}/chats`, { cache: "no-store" });
  if (!res.ok) throw new Error(`listChats: ${res.status}`);
  return res.json();
}

export async function getChat(id: string): Promise<Chat> {
  const res = await fetch(`${API_BASE}/chats/${id}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`getChat: ${res.status}`);
  return res.json();
}

export async function createChat(title?: string): Promise<ChatSummary> {
  const res = await fetch(`${API_BASE}/chats`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title }),
  });
  if (!res.ok) throw new Error(`createChat: ${res.status}`);
  return res.json();
}
