type Props = { text: string };

export const MessageUser = ({ text }: Props) => (
  <div className="flex justify-end">
    <div className="max-w-[80%] rounded-2xl rounded-br-md bg-primary px-4 py-2.5 text-sm text-primary-foreground">
      {text}
    </div>
  </div>
);
