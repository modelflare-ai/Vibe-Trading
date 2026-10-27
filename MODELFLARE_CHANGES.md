# Modelflare Edition changes

Fork of HKUDS/Vibe-Trading (snapshot 3cbb167). No secrets are stored in the repo.

## Already present (kept)

- `agent/src/providers/llm_providers.json` — `modelflare` is the first provider. Label "Modelflare (recommended)", key `MODELFLARE_API_KEY`, base `MODELFLARE_BASE_URL`, default model `gpt-6-sol`, default base `https://modelflare.dev/v1`. `model_options` lists only verified strong models (this change also adds `claude-opus-5-5` and `grok-4.7`).
- `agent/src/providers/capabilities.py` — `modelflare` capabilities near the top of `_PROVIDERS`. Reasoning flags stay off (the gpt-5.6 `top_level_reasoning_effort` note is for the OpenAI provider, not gpt-6-sol on Modelflare).
- `agent/src/config/env_schema.py` — default `LANGCHAIN_PROVIDER` is `modelflare`.
- `agent/src/api/settings_routes.py` — settings fallback provider `modelflare`.
- `agent/.env.example` — active block is Modelflare; the old OpenRouter block is commented, not deleted.

## This change

- `agent/src/providers/modelflare_errors.py` — `explain(status, message, model, base_url)` returns a bilingual hint only when the host is `modelflare.dev` or a subdomain. 401 key, 403 / 503 `model_not_found` / `分组` group, 402 or quota/balance wording balance. Anything else, including other hosts, returns `None`.
- `agent/src/providers/llm.py` — streaming (`_stream`, `_astream`) and non-streaming (`_generate`, `_agenerate`) re-raise paths call that helper. `build_llm` is unchanged. A Modelflare hint is `ModelflareAPIError` and keeps `status_code` so retry policy still sees 401/402/403.
- `agent/src/api/settings_routes.py` — `POST /settings/llm/models` puts the hint on `warning_detail` (HTTP 200). The Web UI's 401/403 client replaces those statuses with a generic auth string, so the friendly text has to ride the existing model-list response.
- `frontend/src/components/onboarding/ModelflareKeyCard.tsx` — one password field. `WelcomeScreen.tsx` mounts it with one line on the empty chat state. The card hides itself when `getLLMSettings().api_key_configured` is true. Submit `PUT /settings/llm` (`modelflare`, `gpt-6-sol`, `https://modelflare.dev/v1`) then `POST /settings/llm/models` (there is no `/models/test`). Shows `已连通` or `warning_detail`. Copy is bilingual in the component so locale files stay in parity.
- `frontend/src/lib/api.ts` — optional `warning_detail` on the model-list type.
- `agent/cli/mf_onboard.py` — if the provider is modelflare and `MODELFLARE_API_KEY` is missing, print `http://modelflare.dev/sign-up?utm_source=github&utm_campaign=mf_Vibe-Trading`, accept a pasted key on a TTY (skip the prompt otherwise), `GET {base}/models`, print the model count or the friendly error, and return non-zero. The key is written to the first existing dotenv (`~/.vibe-trading/.env`, else `agent/.env`, else a new home file) with mode 0600. `python -m cli.mf_onboard` from `agent/` runs the same function.
- `agent/cli/main.py` — after the existing wizard, two lines call that hook on interactive entry.
- `agent/cli/_legacy.py` — `provider doctor` calls the same hook, then still prints redacted diagnostics.
- `README.md`, `README_ar.md`, `README_es.md`, `README_id.md`, `README_ja.md`, `README_ko.md` — English `<!-- MF-START -->` … `<!-- MF-END -->` block at the top, including `<!-- MF-SCREENSHOT -->` and no image. Original bytes below the block are unchanged.
- `README_zh.md` — same markers; English blurb plus the Chinese marketing paragraphs.
- `.github/workflows/mf-upstream-sync.yml` — Mondays 02:00 UTC and `workflow_dispatch`. Merges (never rebases) `https://github.com/HKUDS/Vibe-Trading.git`, pushes `sync/upstream-DATE`, opens a PR. On conflict, `git merge --abort` and `gh issue create`. Does not delete `docker-build.yml`.
- `docker-compose.yml` — comment only. `env_file: agent/.env` already forwards `MODELFLARE_API_KEY` into the container. An `environment:` passthrough was not added: Compose would substitute an empty shell value and override the file.
- `agent/tests/test_modelflare_errors.py` — 401/402/403/503 and non-Modelflare `None`. No network.
- `agent/tests/test_env_schema.py`, `agent/tests/test_dotenv_observability.py` — default-provider assertions now expect `modelflare`.
- `agent/tests/test_llm_provider_defaults.py` — catalog expectation includes `modelflare` / `gpt-6-sol` so the registry set still matches.

## Not changed on purpose

Agent loop, tools, swarm presets, backtest, other provider entries, LICENSE, and NOTICE.

## Gaps

- There is no `POST /settings/llm/models/test`. The card probes with the existing `POST /settings/llm/models` list call.
- `agent/cli/onboard.py` lists Modelflare first (default index 0) with strong model ids only. OpenRouter stays available and is no longer labeled recommended.
- `docker-compose.modelflare.yml` passes `MODELFLARE_API_KEY` from the shell. The main `docker-compose.yml` still loads `agent/.env` and does not override it with an empty shell value.
- `POST /settings/llm/models` returns only the Modelflare strong presets, so live discovery cannot add cheap model ids to the picker.
- `vibe-trading provider doctor` with provider `modelflare` and no key probes the network and returns non-zero. `vibe-trading serve` is not hooked, so the Web card can still collect the key.
- Swarm public metadata (`agent/src/swarm/models.py` `_PUBLIC_PROVIDERS`) does not list `modelflare`, so run metadata may redact the provider name. Swarm presets were left untouched.
- `docker compose` does not inject a shell `MODELFLARE_API_KEY` into the container. Put the key in `agent/.env`, or use `docker run -e MODELFLARE_API_KEY=...`. Compose interpolation can see the shell variable, but this file does not reference it, so an empty override cannot hide `env_file`.
- `<!-- MF-SCREENSHOT -->` is a placeholder. No image was added.
