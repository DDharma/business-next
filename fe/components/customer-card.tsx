"use client";

import { useState } from "react";
import { Check, Copy } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardAction,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import type { CustomerCard as Card_ } from "@/lib/types";
import { SCORE_THRESHOLDS } from "@/utils/constants";

const formatINR = (v: number): string =>
  new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(v);

const scoreColor = (score: number): string => {
  if (score >= SCORE_THRESHOLDS.high)
    return "bg-emerald-500/10 text-emerald-400 border-emerald-500/30";
  if (score >= SCORE_THRESHOLDS.mid)
    return "bg-amber-500/10 text-amber-400 border-amber-500/30";
  return "bg-zinc-500/10 text-zinc-400 border-zinc-500/30";
};

type Props = { card: Card_ };

export const CustomerCard = ({ card }: Props) => {
  const [copied, setCopied] = useState(false);

  const copyMessage = async () => {
    await navigator.clipboard.writeText(card.whatsapp_message);
    setCopied(true);
    setTimeout(() => setCopied(false), 1600);
  };

  return (
    <Card className="overflow-hidden">
      <CardHeader>
        <CardTitle className="truncate text-base">{card.name}</CardTitle>
        <div className="mt-1 flex items-center gap-2 text-xs text-muted-foreground">
          <span>{card.city}</span>
          <span>·</span>
          <span>{formatINR(card.monthly_income)} / mo</span>
        </div>
        <CardAction>
          <div
            className={`flex items-baseline gap-1.5 rounded-lg border px-3 py-1.5 ${scoreColor(card.score)}`}
          >
            <span className="text-[10px] uppercase tracking-widest opacity-70">
              Score
            </span>
            <span className="text-xl font-semibold leading-none tabular-nums">
              {card.score.toFixed(1)}
            </span>
          </div>
        </CardAction>
      </CardHeader>

      <CardContent className="space-y-4">
        <div>
          <div className="mb-1.5 text-xs uppercase tracking-wider text-muted-foreground">
            Recommended
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="secondary" className="font-medium">
              {card.product_name}
            </Badge>
          </div>
          <p className="mt-2 text-sm text-muted-foreground">{card.reason}</p>
        </div>

        <Separator />

        <div>
          <div className="mb-2 text-xs uppercase tracking-wider text-muted-foreground">
            Top factors
          </div>
          <div className="space-y-1.5">
            {card.top_factors.map((f) => (
              <div
                key={f.name}
                className="flex items-center justify-between text-xs"
              >
                <span className="text-zinc-300">{f.name.replace(/_/g, " ")}</span>
                <span className="text-zinc-500 tabular-nums">
                  {f.raw.toFixed(0)}/100
                  <span className="ml-1 text-zinc-600">
                    · w {f.weight.toFixed(2)}
                  </span>
                </span>
              </div>
            ))}
          </div>
        </div>

        <Separator />

        <div>
          <div className="mb-1.5 flex items-center justify-between">
            <div className="text-xs uppercase tracking-wider text-muted-foreground">
              WhatsApp draft
            </div>
            <Button
              variant="ghost"
              size="xs"
              onClick={copyMessage}
              aria-label="Copy WhatsApp message"
            >
              {copied ? <Check /> : <Copy />}
              {copied ? "Copied" : "Copy"}
            </Button>
          </div>
          {card.opener && (
            <p className="mb-2 text-xs italic text-zinc-400">
              Opener: {card.opener}
            </p>
          )}
          <p className="whitespace-pre-wrap rounded-md border bg-zinc-950/40 p-3 text-sm leading-relaxed text-zinc-200">
            {card.whatsapp_message}
          </p>
        </div>
      </CardContent>
    </Card>
  );
};
