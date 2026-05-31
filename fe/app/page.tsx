import { AppShell } from "@/components/app-shell";
import { ChatThread } from "@/components/chat-thread";

export default function Home() {
  return (
    <AppShell>
      <ChatThread />
    </AppShell>
  );
}
