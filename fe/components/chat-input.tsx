"use client";

import { useState } from "react";
import { ArrowUp } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

type Props = {
  disabled?: boolean;
  placeholder?: string;
  onSubmit: (text: string) => void;
};

export const ChatInput = ({
  disabled,
  placeholder = "Ask the agent — e.g. find 5 high-value personal-loan prospects in Mumbai",
  onSubmit,
}: Props) => {
  const [text, setText] = useState("");

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    const t = text.trim();
    if (!t || disabled) return;
    onSubmit(t);
    setText("");
  };

  return (
    <form onSubmit={submit} className="flex w-full items-center gap-2">
      <Input
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder={placeholder}
        disabled={disabled}
        className="flex-1"
        autoFocus
      />
      <Button type="submit" disabled={disabled || !text.trim()} size="icon">
        <ArrowUp />
      </Button>
    </form>
  );
};
