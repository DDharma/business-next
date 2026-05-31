import { API_BASE } from "@/utils/constants";
import type { Chat, ChatSummary } from "./types";

export const listChats = async (): Promise<ChatSummary[]> => {
  const res = await fetch(`${API_BASE}/chats`, { cache: "no-store" });
  if (!res.ok) throw new Error(`listChats: ${res.status}`);
  return res.json();
};

export const getChat = async (id: string): Promise<Chat> => {
  const res = await fetch(`${API_BASE}/chats/${id}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`getChat: ${res.status}`);
  return res.json();
};

export const createChat = async (title?: string): Promise<ChatSummary> => {
  const res = await fetch(`${API_BASE}/chats`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title }),
  });
  if (!res.ok) throw new Error(`createChat: ${res.status}`);
  return res.json();
};
