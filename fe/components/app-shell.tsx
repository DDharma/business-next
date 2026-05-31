"use client";

import { useState } from "react";

import { ChatSidebar } from "@/components/chat-sidebar";

/**
 * Two-column shell — sidebar on the left, child content on the right.
 * Children may call `onChatsChanged()` (via the AppShellContext) when a new
 * chat is created so the sidebar refetches. Kept dead simple for now by
 * lifting a `refreshKey` here and using a context provider would be the next
 * step if more places need to trigger refresh.
 */
export function AppShell({ children }: { children: React.ReactNode }) {
  const [refreshKey] = useState(0);
  return (
    <div className="grid h-svh grid-cols-[260px_1fr] bg-background">
      <ChatSidebar refreshKey={refreshKey} />
      <main className="flex min-h-0 flex-col">{children}</main>
    </div>
  );
}
