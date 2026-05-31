"use client";

import { useState } from "react";
import { Check, Copy } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import type { CustomerCard as Card_ } from "@/lib/types";

function formatINR(v: number) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(v);
}

function scoreColor(score: number) {
  if (score >= 80) return "bg-emerald-500/10 text-emerald-400 border-emerald-500/30";
  if (score >= 65) return "bg-amber-500/10 text-amber-400 border-amber-500/30";
  return "bg-zinc-500/10 text-zinc-400 border-zinc-500/30";
}

export function CustomerCard({ card }: { card: Card_ }) {
  const [copied, setCopied] = useState(false);

  async function copyMessage() {
    await navigator.clipboard.writeText(card.whatsapp_message);
    setCopied(true);
    setTimeout(() => setCopied(false), 1600);
  }

  return (
    <Card className="overflow-hidden">
      <CardHeader className="flex-row items-start justify-between gap-3 space-y-0">
        <div className="min-w-0">
          <CardTitle className="truncate text-base">{card.name}</CardTitle>
          <div className="mt-1 flex items-center gap-2 text-xs text-muted-foreground">
            <span>{card.city}</span>
            <span>·</span>
            <span>{formatINR(card.monthly_income)} / mo</span>
          </div>
        </div>
        <div
          className={`shrink-0 rounded-md border px-2 py-1 text-xs font-medium tabular-nums ${scoreColor(card.score)}`}
        >
          {card.score.toFixed(1)}
        </div>
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
                <span className="text-zinc-300">
                  {f.name.replace(/_/g, " ")}
                </span>
                <span className="text-zinc-500 tabular-nums">
                  {f.raw.toFixed(0)}/100
                  <span className="ml-1 text-zinc-600">· w {f.weight.toFixed(2)}</span>
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
}
