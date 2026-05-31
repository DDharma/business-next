"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { Plus } from "lucide-react";

import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Skeleton } from "@/components/ui/skeleton";
import { listChats } from "@/lib/api";
import type { ChatSummary } from "@/lib/types";

function relativeTime(iso: string): string {
  const then = new Date(iso).getTime();
  const diff = Date.now() - then;
  const m = Math.floor(diff / 60_000);
  if (m < 1) return "just now";
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  const d = Math.floor(h / 24);
  if (d < 7) return `${d}d ago`;
  return new Date(iso).toLocaleDateString();
}

export function ChatSidebar({ refreshKey = 0 }: { refreshKey?: number }) {
  const pathname = usePathname();
  const [chats, setChats] = useState<ChatSummary[] | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const data = await listChats();
        if (!cancelled) setChats(data);
      } catch {
        if (!cancelled) setChats([]);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [refreshKey]);

  const activeId = pathname?.startsWith("/chat/")
    ? pathname.split("/")[2]
    : null;

  return (
    <aside className="flex h-svh w-[260px] shrink-0 flex-col border-r bg-zinc-950/40">
      <div className="flex items-center justify-between px-3 py-3">
        <div className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">
          Chats
        </div>
        <Button asChild variant="outline" size="xs" aria-label="Start new chat">
          <Link href="/">
            <Plus />
            New
          </Link>
        </Button>
      </div>

      <ScrollArea className="flex-1 px-2 pb-3">
        {chats === null ? (
          <div className="space-y-2 px-1">
            {Array.from({ length: 6 }).map((_, i) => (
              <Skeleton key={i} className="h-10 w-full rounded-md" />
            ))}
          </div>
        ) : chats.length === 0 ? (
          <div className="px-2 py-6 text-center text-xs text-muted-foreground">
            No chats yet. Start one →
          </div>
        ) : (
          <ul className="space-y-0.5">
            {chats.map((c) => {
              const active = c.id === activeId;
              return (
                <li key={c.id}>
                  <Link
                    href={`/chat/${c.id}`}
                    className={`block rounded-md px-2 py-2 text-sm transition-colors ${
                      active
                        ? "bg-muted text-foreground"
                        : "text-zinc-400 hover:bg-muted/50 hover:text-foreground"
                    }`}
                  >
                    <div className="flex-1">{c.title}</div>
                    <div className="mt-0.5 text-[10px] text-muted-foreground">
                      {relativeTime(c.updated_at)}
                    </div>
                  </Link>
                </li>
              );
            })}
          </ul>
        )}
      </ScrollArea>
    </aside>
  );
}
