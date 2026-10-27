import { FormEvent, useEffect, useState } from "react";
import { api } from "@/lib/api";

const BASE_URL = "https://modelflare.dev/v1";
const MODEL = "gpt-6-sol";
const SIGNUP = "http://modelflare.dev/sign-up?utm_source=github&utm_campaign=mf_Vibe-Trading";

/**
 * One password field for a Modelflare key. Shown only when LLM settings have
 * no API key. Strings are bilingual on purpose so locale files stay untouched.
 */
export function ModelflareKeyCard() {
  const [visible, setVisible] = useState(false);
  const [apiKey, setApiKey] = useState("");
  const [busy, setBusy] = useState(false);
  const [tone, setTone] = useState<"idle" | "ok" | "error">("idle");
  const [message, setMessage] = useState("");

  useEffect(() => {
    let cancelled = false;
    api
      .getLLMSettings()
      .then((settings) => {
        if (!cancelled && !settings.api_key_configured) setVisible(true);
      })
      .catch(() => {
        if (!cancelled) setVisible(true);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (!visible) return null;

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    const key = apiKey.trim();
    if (!key || busy) return;
    setBusy(true);
    setTone("idle");
    setMessage("");
    try {
      let temperature = 0;
      let timeoutSeconds = 120;
      let maxRetries = 2;
      let reasoningEffort: string | undefined;
      try {
        const current = await api.getLLMSettings();
        temperature = current.temperature;
        timeoutSeconds = current.timeout_seconds;
        maxRetries = current.max_retries;
        reasoningEffort = current.reasoning_effort || undefined;
      } catch {
        // Server defaults match UpdateLLMSettingsRequest.
      }
      await api.updateLLMSettings({
        provider: "modelflare",
        model_name: MODEL,
        base_url: BASE_URL,
        api_key: key,
        temperature,
        timeout_seconds: timeoutSeconds,
        max_retries: maxRetries,
        reasoning_effort: reasoningEffort,
      });
      const listed = await api.listLLMModels({
        provider: "modelflare",
        base_url: BASE_URL,
        api_key: key,
      });
      if (listed.warning_detail) {
        setTone("error");
        setMessage(listed.warning_detail);
        return;
      }
      if (listed.warning_code) {
        setTone("error");
        setMessage("无法连接 Modelflare。 / Could not reach Modelflare.");
        return;
      }
      setTone("ok");
      setMessage(`已连通 / Connected (${listed.models.length})`);
    } catch (error) {
      setTone("error");
      setMessage(error instanceof Error ? error.message : "无法连接 Modelflare。 / Could not reach Modelflare.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <form
      onSubmit={onSubmit}
      className="mx-auto mt-6 w-full max-w-md rounded-xl border border-border/60 bg-card px-4 py-3 text-left"
    >
      <p className="text-sm font-medium text-foreground">Modelflare API Key</p>
      <p className="mt-1 text-xs leading-snug text-muted-foreground">
        一把 Key 调用 GPT-6-Sol。{" "}
        <a className="underline hover:text-foreground" href={SIGNUP} target="_blank" rel="noreferrer">
          注册 / Sign up
        </a>
      </p>
      <label className="mt-3 block text-xs text-muted-foreground" htmlFor="modelflare-api-key">
        API Key
      </label>
      <input
        id="modelflare-api-key"
        type="password"
        autoComplete="off"
        value={apiKey}
        onChange={(event) => setApiKey(event.target.value)}
        className="mt-1 w-full rounded-lg border border-border/60 bg-background px-3 py-2 text-sm text-foreground outline-none focus-visible:ring-2 focus-visible:ring-primary/40"
      />
      <button
        type="submit"
        disabled={busy || !apiKey.trim()}
        className="mt-3 inline-flex items-center rounded-full border border-primary/30 bg-primary/[0.08] px-4 py-2 text-sm text-primary transition-colors hover:border-primary/50 hover:bg-primary/15 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {busy ? "连接中… / Connecting…" : "保存并测试 / Save and test"}
      </button>
      {message && (
        <p
          className={
            tone === "ok"
              ? "mt-2 whitespace-pre-wrap text-xs text-primary"
              : "mt-2 whitespace-pre-wrap text-xs text-destructive"
          }
        >
          {message}
        </p>
      )}
    </form>
  );
}
