import { AppShell } from "@/components/app-shell";
import { ChatThread } from "@/components/chat-thread";

type Props = { params: Promise<{ id: string }> };

const ChatPage = async ({ params }: Props) => {
  const { id } = await params;
  return (
    <AppShell>
      <ChatThread chatId={id} />
    </AppShell>
  );
};

export default ChatPage;
