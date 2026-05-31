import type { MessageRole } from "@/utils/enums";

export type ScoreFactor = {
  name: string;
  weight: number;
  raw: number;
  contribution: number;
};

export type CustomerCard = {
  customer_id: string;
  name: string;
  city: string;
  monthly_income: number;
  score: number;
  top_factors: ScoreFactor[];
  product_code: string;
  product_name: string;
  reason: string;
  whatsapp_message: string;
  opener: string | null;
};

export type StepEvent =
  | { type: "node_started"; node: string; label: string }
  | { type: "tool_call"; node: string; tool: string; args: Record<string, unknown> }
  | { type: "tool_result"; node: string; tool: string; preview: string }
  | { type: "node_finished"; node: string; ms: number }
  | { type: "card"; card: CustomerCard }
  | { type: "error"; message: string };

export type ChatSummary = {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
};

export type ChatMessage = {
  id: string;
  chat_id: string;
  role: MessageRole;
  content: string;
  metadata: {
    cards?: CustomerCard[];
    events?: StepEvent[];
    duration_ms?: number;
    error?: string | null;
  };
  created_at: string;
};

export type Chat = ChatSummary & { messages: ChatMessage[] };
