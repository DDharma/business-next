export const StreamStatus = {
  Idle: "idle",
  Streaming: "streaming",
  Done: "done",
  Error: "error",
} as const;
export type StreamStatus = (typeof StreamStatus)[keyof typeof StreamStatus];

export const MessageRole = {
  User: "user",
  Assistant: "assistant",
} as const;
export type MessageRole = (typeof MessageRole)[keyof typeof MessageRole];

export const ProductCode = {
  PersonalLoan: "personal_loan",
  CreditCard: "credit_card",
  SavingsPlus: "savings_plus",
  HomeLoan: "home_loan",
} as const;
export type ProductCode = (typeof ProductCode)[keyof typeof ProductCode];

export const IntentType = {
  FindProspects: "find_prospects",
  Refine: "refine",
  RewriteMessage: "rewrite_message",
  Explain: "explain",
} as const;
export type IntentType = (typeof IntentType)[keyof typeof IntentType];

export const StepEventType = {
  NodeStarted: "node_started",
  ToolCall: "tool_call",
  ToolResult: "tool_result",
  NodeFinished: "node_finished",
  Card: "card",
  Error: "error",
  ChatId: "chat_id",
  Done: "done",
} as const;
export type StepEventType = (typeof StepEventType)[keyof typeof StepEventType];
