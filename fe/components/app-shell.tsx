"use client";

import { useState } from "react";

import { ChatSidebar } from "@/components/chat-sidebar";

type Props = { children: React.ReactNode };

export const AppShell = ({ children }: Props) => {
  const [refreshKey] = useState(0);
  return (
    <div className="grid h-svh grid-cols-[260px_1fr] bg-background">
      <ChatSidebar refreshKey={refreshKey} />
      <main className="flex min-h-0 flex-col">{children}</main>
    </div>
  );
};
