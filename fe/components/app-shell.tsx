"use client";

import { createContext, useCallback, useContext, useState } from "react";

import { ChatSidebar } from "@/components/chat-sidebar";
import { useChatStream, type UseChatStream } from "@/hooks/use-chat-stream";

type AppShellCtx = UseChatStream & {
  sidebarRefreshKey: number;
  bumpSidebar: () => void;
};

const Ctx = createContext<AppShellCtx | null>(null);

export const useAppShell = (): AppShellCtx => {
  const c = useContext(Ctx);
  if (!c) throw new Error("useAppShell must be used inside <AppShell>");
  return c;
};

type Props = { children: React.ReactNode };

export const AppShell = ({ children }: Props) => {
  const stream = useChatStream();
  const [sidebarRefreshKey, setKey] = useState(0);
  const bumpSidebar = useCallback(() => setKey((k) => k + 1), []);

  return (
    <Ctx.Provider value={{ ...stream, sidebarRefreshKey, bumpSidebar }}>
      <div className="grid h-svh grid-cols-[260px_1fr] bg-background">
        <ChatSidebar refreshKey={sidebarRefreshKey} />
        <main className="flex min-h-0 flex-col">{children}</main>
      </div>
    </Ctx.Provider>
  );
};
