# Installation and agent setup

## Requirements and direct installation

Use **Linux or Windows, Python 3.11+, Git and uv or pipx** for the v0.2.0 source checkout. Tag `v0.1.1` remains Linux-only. Use `python` on Windows and local regular files in trusted directories, not network paths, reparse points or alternate streams. The agent itself must already be installed, authenticated and permitted to use a shell. Model-provider authentication for the agent is separate from the inference key used by `jev-search`.

**The v0.2.0 code is available on `main`, without a published v0.2.0 tag/release.** Obtain a checkout with `git clone --branch main https://github.com/larguesa/jev-search.git`, review it and record `git rev-parse HEAD`. Install both components from that same reviewed local checkout; do not silently follow later changes to `main`:

```sh
cd /path/to/jev-search
uv tool install .
# Alternative: pipx install .
jev-search --help
```

After the tag is published, a pinned Git installation is available:

```sh
uv tool install 'git+https://github.com/larguesa/jev-search.git@v0.2.0'
# Alternative:
pipx install 'git+https://github.com/larguesa/jev-search.git@v0.2.0'
jev-search --help
```

Inspect an existing installation before replacing it. To deliberately replace a uv installation, use `uv tool install --force` with the pinned URL above. Follow the tool manager's PATH instructions if the command is not found. No PyPI release, native agent plugin or MCP server is implied.

## Install the portable skill alongside the CLI

The source archive includes `skills/jev-search/SKILL.md`; a pip wheel does not automatically install agent skills. From the same reviewed pinned checkout used for the CLI, use agent-native file tools to copy that file into `<documented discovery directory>/jev-search/SKILL.md`. Consult the agent documentation for the actual discovery directory and intended project/user/profile scope; no universal path is assumed. Inspect existing Jev skills first: reuse/update overlapping guidance without creating duplicates or discarding local policy. Preserve unrelated instructions. Verify that the agent can discover and load the skill, using its documented mechanism.

Prefer native skill discovery. Only if the agent has no skill support, add a small named complementary-search section to its existing supported instructions (such as `AGENTS.md` where documented), and report that fallback rather than claiming native skill installation. Never invent agent installation commands. The shared prompt below performs both CLI and skill setup.

## Configure the key without sharing it in chat

### OpenRouter versus TypeSafe

`jev-search` supports two backends with the same native `state`/`questions`/`answers`/`noul` contract, not chat completions:

| Selection | Endpoint | Default model | Required key issuer |
|---|---|---|---|
| `--provider openrouter` (default) | `https://openrouter.ai/api/alpha/decisions` | `typesafe/jev-1.13` | OpenRouter |
| `--provider typesafe` | `https://api.typesafe.ai/v1/systemone` | `jev-1.13.0` | TypeSafe |

Set the persistent choice with `JEV_SEARCH_PROVIDER`; set a compatible model with `JEV_SEARCH_MODEL` or `--model`. Explicit flags override the corresponding environment settings. These switches do not enable arbitrary providers or chat models: the model must support native typed decisions and this client's validation. TypeSafe's [API reference](https://docs.typesafe.ai/api) and [model list](https://docs.typesafe.ai/models) document the direct endpoint and pinned model. Its `jev-latest`/`jev-preview` aliases can move over time. The official model guide describes versioned response IDs, while the API examples also show an unchanged alias; this client accepts both documented response forms.

1. Create a dedicated **inference API key** from the selected provider: [OpenRouter key settings](https://openrouter.ai/settings/keys) or your TypeSafe account. Configure provider-side spending controls suitable for the approved budget. Do not use a management/provisioning key. This public setup does not automatically provision keys.
2. Make that key available as `JEV_SEARCH_API_KEY` to the process that runs the CLI. Use a protected process environment or your deployment's secret store. Neither `OPENROUTER_API_KEY` nor `TYPESAFE_API_KEY` is read automatically; no provider-secret fallback occurs. Only map a suitable authorized inference key, never a management key.
3. Keep keys out of prompts, agent instructions, Git, shell history and logs. Do not ask the agent to print or inspect the value. The CLI does not read `.env` files itself.

For a temporary **Bash session**, the user can enter the key directly in their terminal, outside any agent conversation:

```bash
read -r -s -p 'Selected provider inference key: ' JEV_SEARCH_API_KEY
printf '\n'
export JEV_SEARCH_API_KEY
```

The input is hidden and the secret is not part of the command text. Run the CLI or launch the agent from that session. For a running Gateway, service or container, configure its approved secret-injection mechanism instead; exporting a variable in another terminal does not update an existing process. If the agent's subprocess environment filters the variable, arrange an approved environment mapping rather than putting the value in a command or disabling redaction.

For persistent setup, use a protected secret store or the agent/service's documented environment configuration in the intended scope. The setup agent should explain any required reload without restarting services unasked. The key must reach the process that invokes `jev-search`, not merely the agent's chat provider configuration.

**Keys are not interchangeable.** For direct TypeSafe, select `--provider typesafe` or export `JEV_SEARCH_PROVIDER=typesafe` before using a TypeSafe-issued key. Switching the provider does not replace the key or translate an explicit model override; configure both consistently. OpenRouter is the default when no provider is selected.

Real search is the default and can incur charges. Use `--dry-run` for an offline payload preview without reading credentials or making a request; `--send` is only a backward-compatible explicit real-search flag. Direct TypeSafe responses may omit cost: missing cost means unavailable, not zero. The CLI does not enforce a monetary budget, and `--max-requests 1` is only a request-count bound.

After temporary use:

```sh
unset JEV_SEARCH_API_KEY
```

Unsetting an environment variable is not revocation. Disable or revoke a temporary key with its issuer when finished. A deliberately configured ongoing-use key can remain in the approved secret store. Normal user installation does not require a management key.

## Install through an agent

Run from the intended workspace. Remote agents, Gateways and containers install in **their execution environment**, not automatically on your laptop. Keep normal approval prompts enabled. These instructions invoke an existing agent and ask it to install a shell tool; they do not install the agent itself.

### Shared setup prompt

Set this variable in your shell, then run **one** of the agent commands below. It contains no credential:

```sh
INSTALL_PROMPT='Install and configure jev-search v0.2.0 for this execution environment. First inspect existing instructions, installed version, Linux/Python 3.11+/Git/uv prerequisites, permissions and target paths. The v0.2.0 tag is not published yet in these instructions. If a reviewed local v0.2.0 checkout is provided, review its documentation and source before building and install with uv tool install . from that checkout. Otherwise verify that https://github.com/larguesa/jev-search has tag v0.2.0; only if published, review the pinned source and install with uv tool install "git+https://github.com/larguesa/jev-search.git@v0.2.0". If neither is available, the documented current source is main: clone https://github.com/larguesa/jev-search.git with --branch main, record git rev-parse HEAD, review that exact local revision, confirm package version 0.2.0, and install both components from that checkout. Do not claim it is a tagged release or silently install another version. Ask before replacing an existing installation. Do not use sudo, bypass approvals or sandbox restrictions, change the agent chat provider, existing search tools or unrelated configuration.
Install both the CLI and skills/jev-search/SKILL.md from the same reviewed pinned checkout. Installing a pip wheel does not automatically install agent skills. Consult this agent documentation for its actual skill discovery directory and intended project/user/profile scope; do not assume a universal path. Use agent-native file tools to copy the skill there. Inspect and reuse/update overlapping Jev skills without duplicates or loss of local policy. Preserve existing instructions and verify native skill discovery/loading. Only if native skills are unsupported, add a named section to existing supported instructions and report that fallback. Report exact paths and changes. Use jev-search as functional complementary semantic search over small, explicitly selected authorized text files, alongside exact search, navigation and source reading. Merge useful candidates and inspect original context. It is not a replacement for existing search, a recursive indexer, an MCP server or an Obsidian plugin. Benchmarks are exploratory, not a restriction to testing-only use.
Configure --provider openrouter|typesafe or JEV_SEARCH_PROVIDER and optionally --model or JEV_SEARCH_MODEL. OpenRouter defaults to typesafe/jev-1.13 at https://openrouter.ai/api/alpha/decisions; direct TypeSafe defaults to jev-1.13.0 at https://api.typesafe.ai/v1/systemone. Both use native state/questions/answers/noul, not arbitrary chat models. Supply a key from the selected provider as JEV_SEARCH_API_KEY; keys are not interchangeable and other provider secret variables are not automatic fallbacks. Never request, paste, print or log a key in chat, prompts, command arguments, instructions or Git. Explain how the user can inject a dedicated inference key with suitable provider-side spending controls through the target process environment or an approved secret store outside the conversation. Never use management credentials or automatically provision keys. The CLI does not load .env itself. Do not inspect secret values. No key is needed for --dry-run validation.
Verify installed package metadata is version 0.2.0 and run jev-search --help. Create a tiny synthetic nonprivate text fixture in a safe temporary location and run jev-search --dry-run --query "greeting" with its explicit path. Inspect the JSON and report results and blockers. Real search is the default; --dry-run is explicit offline mode and --send is backward compatibility only. A dry-run does not test credentials or live inference; report that distinction. Setup is offline first. Only when the user authorizes the provider, content and budget, optionally run one tiny nonprivate live smoke test and report its actual result separately. Never run a paid benchmark for installation. Record the user-authorized content scope, provider and budget for ongoing use; if not established, report those as remaining setup actions. Within that configured scope, agents may search routinely without a new human approval for each search, while preserving normal permission and sandbox rules. Ask before expanding scope or budget. Use --max-requests 1; provider-side limits, not request counts or missing response cost, control monetary exposure. Missing direct TypeSafe cost is unavailable, not zero. Explain that all selected nonblank lines and the query, not only matches, go to OpenRouter and TypeSafe when routed, or TypeSafe alone when direct. The user or organization decides confidential-content policy. TypeSafe states no training or fine tuning on Input at https://typesafe.ai/legal/privacy-policy; https://docs.typesafe.ai/legal offers enterprise ZDR, not universal zero retention. Apply the relevant provider terms without a blanket ban on private files. Preserve safeguards and report remaining user actions.'
```

### Hermes

```sh
hermes chat -q "$INSTALL_PROMPT"
```

Use a separate usage skill in the active Hermes profile's skills directory, preserving existing skills and search behavior. The default home is `~/.hermes`, but honor the actual profile/home rather than assuming it. [CLI reference](https://hermes-agent.nousresearch.com/docs/reference/cli-commands), [skills](https://hermes-agent.nousresearch.com/docs/user-guide/features/skills).

### OpenClaw

Choose an existing configured agent ID for `OPENCLAW_AGENT_ID` before running:

```sh
openclaw agent --agent "$OPENCLAW_AGENT_ID" --message "$INSTALL_PROMPT"
```

This invokes an agent turn through its Gateway in the configured workspace. Install the portable skill using the selected agent's documented discovery mechanism; use existing workspace `AGENTS.md` conventions only as a fallback when skills are unsupported. `openclaw message send` sends an outbound channel message; it is not the installer invocation. Do not add `--local` blindly: that is a different execution path with state-ownership requirements. [Agent CLI](https://docs.openclaw.ai/cli/agent), [workspace](https://docs.openclaw.ai/concepts/agent-workspace).

### OpenCode

```sh
opencode --prompt "$INSTALL_PROMPT"
# Noninteractive alternative, with permissions already configured:
# opencode run "$INSTALL_PROMPT"
```

Prefer the documented native skill mechanism. If unavailable, preserve project `AGENTS.md`, or use `~/.config/opencode/AGENTS.md` only when global scope is intended. [CLI](https://opencode.ai/docs/cli/), [rules](https://opencode.ai/docs/rules/).

### Pi coding agent (pi.dev)

```sh
pi "$INSTALL_PROMPT"
```

Prefer documented native skill discovery; only as a fallback use the applicable project `AGENTS.md` or `CLAUDE.md`, or `~/.pi/agent/AGENTS.md` for explicitly intended global guidance. Inspect overrides and preserve existing instructions. Pi's project trust is not a runtime sandbox; run in an appropriate environment without automatically adding approval flags. [Official README](https://github.com/badlogic/pi-mono/blob/main/packages/coding-agent/README.md).

### ChatGPT / Codex

Use **Codex CLI** for a local, terminal-capable OpenAI workflow:

```sh
codex --sandbox workspace-write --ask-for-approval on-request "$INSTALL_PROMPT"
```

A user-level uv installation or network request may require permission beyond the workspace sandbox. Approve the specific operation after inspection; do not disable the sandbox to force success. Prefer documented native skill discovery; for an instruction fallback preserve project `AGENTS.md`, taking account of `AGENTS.override.md` precedence. Global guidance belongs in the configured Codex home only when intended. [CLI reference](https://developers.openai.com/codex/cli/reference), [AGENTS.md](https://developers.openai.com/codex/guides/agents-md).

An ordinary ChatGPT browser conversation does not by itself have a shell on your computer. For a hosted coding task or explicitly connected execution environment, paste the shared prompt there and verify where commands run. Installation in a cloud container is not installation on your laptop.

### Claude

Use **Claude Code** for a local terminal workflow:

```sh
claude "$INSTALL_PROMPT"
```

Prefer documented native skill discovery. For an instruction fallback preserve the loaded `CLAUDE.md` hierarchy: project `CLAUDE.md` or `.claude/CLAUDE.md`, or `~/.claude/CLAUDE.md` for intended user-wide guidance. Ordinary Claude chat likewise does not imply local shell access; use Claude Code or an explicitly connected environment. [CLI reference](https://code.claude.com/docs/en/cli-reference), [memory and instructions](https://code.claude.com/docs/en/memory).

### Other terminal-capable agents

Paste the shared prompt into an agent that has an approved Linux shell, or pass it using that agent's documented initial-prompt option. Do not invent a plugin installation command or assume every product uses `AGENTS.md`. If shell access or persistent instructions are unavailable, report the limitation instead of claiming installation.

## Verify the outcome

The installation agent must report:

- The installed version, executable location and actual host/container/workspace.
- A successful `jev-search --help` and parsed `--dry-run` JSON with `mode: dry-run` on a synthetic fixture.
- The exact skill location and verified discovery/loading (or documented instruction fallback), preserving existing content and making complementary use explicit. Reuse overlapping Jev guidance rather than duplicating it.
- The configured provider/model, authorized content scope and budget, or which of these still needs user action. Do not print key values. A successful dry-run does **not** validate credentials or live inference.

Do not run the paid benchmark merely to validate installation. No paid calls are needed for the checks above. After offline checks, one tiny nonprivate live smoke test is optional only with user-authorized provider, content and budget; report its outcome separately. See the [usage and privacy contract](../README.md#privacy-and-output) for ongoing real searches, which no longer require `--send`.

## Verification scope of these instructions

OpenRouter v0.2.0 real setup smoke testing passed (not a benchmark). Direct TypeSafe local contract tests passed; direct live tests remain pending because the maintainer lacks direct API access. These results do not establish successful installation through every agent.

Hermes invocation was checked against local `--help` and official documentation. Other agent commands and instruction locations were checked against official documentation/source, **not by executing installations through every agent**. OpenCode's hosted docs were unavailable during checking, so its [official CLI source](https://github.com/anomalyco/opencode/blob/dev/packages/web/src/content/docs/cli.mdx) and [rules source](https://github.com/anomalyco/opencode/blob/dev/packages/web/src/content/docs/rules.mdx) were used. Agent versions, permissions and deployment configurations may differ; inspect current help before changing an installation.
