import { useTranslations } from "next-intl";
import { LanguageSwitcher } from "@/features/language-switcher";

export default function HomePage() {
  const t = useTranslations("home");

  return (
    <div className="relative">
      <header className="absolute top-4 right-4 z-10">
        <LanguageSwitcher />
      </header>

      <main className="flex min-h-screen flex-col items-center justify-center gap-6 p-8 text-center">
        <h1 className="text-4xl font-bold md:text-6xl">{t("title")}</h1>
        <p className="text-muted-foreground text-xl">{t("description")}</p>

        <button className="bg-primary text-primary-foreground hover:bg-primary/90 mt-4 rounded-lg px-6 py-3 font-semibold transition-colors">
          {t("getStarted")}
        </button>
      </main>
    </div>
  );
}
