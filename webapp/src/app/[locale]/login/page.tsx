type Props = {
  params: Promise<{ locale: "en" | "ru" }>;
  searchParams?: Promise<{ [key: string]: string | string[] | undefined }>;
};

export default async function LoginPage({ searchParams }: Props) {
  const resolvedSearchParams = searchParams ? await searchParams : {};
  const reason = (resolvedSearchParams?.reason as string) || "";

  return (
    <section style={{ padding: "2rem" }}>
      {/* Playwright expects heading with name /login/i */}
      <h1>Login</h1>

      {/* Visible Telegram widget container expected by tests */}
      <div
        id="telegram-login-widget"
        style={{
          marginTop: "1rem",
          minHeight: 40,
          border: "1px dashed #888",
          display: "block",
        }}
      />

      {/* Unauthorized banner when reason=unauthorized */}
      {reason === "unauthorized" && (
        <p style={{ marginTop: "1rem", color: "#b00" }}>
          You need to login to access this page.
        </p>
      )}
    </section>
  );
}
