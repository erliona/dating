import { NextIntlClientProvider } from "next-intl";
import { getMessages } from "next-intl/server";
import { notFound } from "next/navigation";
import { routing } from "@/i18n/routing";
import { QueryProvider } from "@/shared/providers/query-provider";
import { TelegramAuth } from "@/features/telegram-auth";
import "../globals.css";

export default async function LocaleLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;

  // Ensure that the incoming `locale` is valid
  if (!routing.locales.includes(locale as "ru" | "en")) {
    notFound();
  }

  const messages = await getMessages();

  return (
    <html lang={locale}>
      <body className="antialiased">
        <QueryProvider>
          <NextIntlClientProvider messages={messages}>
            <TelegramAuth>{children}</TelegramAuth>
          </NextIntlClientProvider>
        </QueryProvider>
      </body>
    </html>
  );
}
