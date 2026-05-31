export const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export const SAMPLE_PROMPTS: readonly string[] = [
  "Find 5 high-value personal-loan prospects in Mumbai",
  "Show me 3 credit card prospects in Bengaluru",
  "Top customers for a home loan, salaried, above ₹1L/mo",
];

export const SCORE_THRESHOLDS = {
  high: 80,
  mid: 65,
} as const;

export const SIDEBAR_CHAT_LIMIT = 50;

export const HISTORY_TURNS_FOR_INTENT = 6;
