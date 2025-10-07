import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Dating - Telegram Dating App",
  description: "Dating application in Telegram",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return children;
}
