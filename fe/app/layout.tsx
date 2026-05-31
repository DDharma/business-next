import type { Metadata } from "next";
import { Geist, Geist_Mono, Inter } from "next/font/google";
import "./globals.css";
import { cn } from "@/lib/utils";

const inter = Inter({ subsets: ["latin"], variable: "--font-sans" });

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Lakshya — Banking CRM Agent",
  description:
    "Lakshya is an agentic AI co-pilot for bank Relationship Managers — find your next prospect.",
};

type Props = Readonly<{ children: React.ReactNode }>;

const RootLayout = ({ children }: Props) => (
  <html
    lang="en"
    className={cn(
      "h-full",
      "antialiased",
      "dark",
      geistSans.variable,
      geistMono.variable,
      "font-sans",
      inter.variable,
    )}
  >
    <body className="min-h-full flex flex-col">{children}</body>
  </html>
);

export default RootLayout;
