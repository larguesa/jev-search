# Installation and agent setup

## Requirements and direct installation

Use **Linux, Python 3.11+, Git and uv or pipx** for the published tag below. The unreleased source branch also supports Windows via `uv tool install .` from a reviewed checkout; `v0.1.1` does not include that change. Use `python` on Windows and local regular files in trusted directories, not network paths, reparse points or alternate streams. The agent itself must already be installed, authenticated and permitted to use a shell. Model-provider authentication for the agent is separate from the inference key used by `jev-search`.

```sh
uv tool install 'git+https://github.com/larguesa/jev-search.git@v0.1.1'
# Alternative:
pipx install 'git+https://github.com/larguesa/jev-search.git@v0.1.1'
jev-search --help
```

Inspect an existing installation before replacing it. To deliberately replace a uv installation, use `uv tool install --force` with the pinned URL above. Follow the tool manager's PATH instructions if the command is not found. No PyPI release, native agent plugin or MCP server is implied.

## Configure the key without sharing it in chat

### OpenRouter versus TypeSafe

`jev-search` calls OpenRouter's Decisions API with model `typesafe/jev-1.13`. **TypeSafe is the model provider; OpenRouter is the supported API and credential issuer for this client.**

1. Create a dedicated **inference API key** in [OpenRouter's key settings](https://openrouter.ai/settings/keys) and set a spending limit suitable for your approved usage. Do not use a management/provisioning key.
2. Make that key available as `JEV_SEARCH_API_KEY` to the process that runs the CLI. Use a protected process environment or your deployment's secret store. An existing `OPENROUTER_API_KEY` is not read automatically; reuse only an appropriately scoped, spending-limited inference key, never a management key.
3. Keep keys out of prompts, agent instructions, Git, shell history and logs. Do not ask the agent to print or inspect the value. The CLI does not read `.env` files itself.

For a temporary **Bash session**, the user can enter the key directly in their terminal, outside any agent conversation:

```bash
read -r -s -p 'OpenRouter inference key: ' JEV_SEARCH_API_KEY
printf '\n'
export JEV_SEARCH_API_KEY
```

The input is hidden and the secret is not part of the command text. Run the CLI or launch the agent from that session. For a running Gateway, service or container, configure its approved secret-injection mechanism instead; exporting a variable in another terminal does not update an existing process. If the agent's subprocess environment filters the variable, arrange an approved environment mapping rather than putting the value in a command or disabling redaction.

For persistent setup, use a protected secret store or the agent/service's documented environment configuration in the intended scope. The setup agent should explain any required reload without restarting services unasked. The key must reach the process that invokes `jev-search`, not merely the agent's chat provider configuration.

A **direct TypeSafe API key does not work with this release**. There is no direct TypeSafe endpoint/backend switch. If you only have a TypeSafe key, stop at dry-run and obtain an OpenRouter inference key for this client; never disguise or substitute the credential. Supporting TypeSafe directly would require a separately implemented and tested adapter.

After temporary use:

```sh
unset JEV_SEARCH_API_KEY
```

Unsetting an environment variable is not revocation. Disable or revoke a temporary key in OpenRouter when finished. Normal user installation does not require a management key.

## Install through an agent

Run from the intended workspace. Remote agents, Gateways and containers install in **their execution environment**, not automatically on your laptop. Keep normal approval prompts enabled. These instructions invoke an existing agent and ask it to install a shell tool; they do not install the agent itself.

### Shared setup prompt

Set this variable in your shell, then run **one** of the agent commands below. It contains no credential:

```sh
INSTALL_PROMPT='Install and configure jev-search for this execution environment. First inspect the existing instructions, installed version, Linux/Python 3.11+/Git/uv prerequisites, permissions and target paths. Verify that https://github.com/larguesa/jev-search has tag v0.1.1; stop if it does not. Review the pinned release documentation and source before executing its build. Install with uv tool install "git+https://github.com/larguesa/jev-search.git@v0.1.1"; ask before replacing an existing installation. Do not use sudo, bypass approvals, change model providers, existing search tools or unrelated configuration.
Configure durable guidance through the supported instruction or skill mechanism of this agent in the intended scope. Preserve existing instructions and append a small named section or create a separate skill; report exact paths and changes. Use jev-search only as complementary semantic search over small, explicitly selected nonprivate text files, alongside exact search, navigation and source reading. Merge useful candidates and inspect original context. It is not a replacement for existing search, a recursive indexer, an MCP server or an Obsidian plugin.
This release supports TypeSafe Jev only through OpenRouter Decisions, using an OpenRouter inference key supplied as JEV_SEARCH_API_KEY. Direct TypeSafe credentials are not supported or interchangeable. Never request, paste, print or log a key in chat, prompts, command arguments, instructions or Git. Explain how the user can inject a dedicated spending-limited key through the target process environment or an approved secret store outside the conversation. The CLI does not load .env itself. Do not inspect secret values. No key is needed for dry-run validation.
Verify the installed version and jev-search --help, create a tiny synthetic nonprivate text fixture in a safe temporary location and run a default dry-run without --send. Inspect its JSON and report results and blockers. Do not claim credentials or live inference were tested. Do not make paid inference calls during installation. Future --send requires explicit approval of the query, all selected content and a budget-limited key; use --max-requests 1. The provider key limit, not the request-count flag, controls the monetary budget. Explain that all selected nonblank lines and the query go to OpenRouter and its TypeSafe model provider, not only matches. Preserve safeguards and report remaining user actions.'
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

This invokes an agent turn through its Gateway in the configured workspace. Put persistent guidance in the selected workspace's existing `AGENTS.md` conventions. `openclaw message send` sends an outbound channel message; it is not the installer invocation. Do not add `--local` blindly: that is a different execution path with state-ownership requirements. [Agent CLI](https://docs.openclaw.ai/cli/agent), [workspace](https://docs.openclaw.ai/concepts/agent-workspace).

### OpenCode

```sh
opencode --prompt "$INSTALL_PROMPT"
# Noninteractive alternative, with permissions already configured:
# opencode run "$INSTALL_PROMPT"
```

Preserve project `AGENTS.md`, or use `~/.config/opencode/AGENTS.md` only when global scope is intended. [CLI](https://opencode.ai/docs/cli/), [rules](https://opencode.ai/docs/rules/).

### Pi coding agent (pi.dev)

```sh
pi "$INSTALL_PROMPT"
```

Use the applicable project `AGENTS.md` or `CLAUDE.md`, or `~/.pi/agent/AGENTS.md` for explicitly intended global guidance. Inspect overrides and preserve existing instructions. Pi's project trust is not a runtime sandbox; run in an appropriate environment without automatically adding approval flags. [Official README](https://github.com/badlogic/pi-mono/blob/main/packages/coding-agent/README.md).

### ChatGPT / Codex

Use **Codex CLI** for a local, terminal-capable OpenAI workflow:

```sh
codex --sandbox workspace-write --ask-for-approval on-request "$INSTALL_PROMPT"
```

A user-level uv installation or network request may require permission beyond the workspace sandbox. Approve the specific operation after inspection; do not disable the sandbox to force success. Preserve project `AGENTS.md`, taking account of `AGENTS.override.md` precedence. Global guidance belongs in the configured Codex home only when intended. [CLI reference](https://developers.openai.com/codex/cli/reference), [AGENTS.md](https://developers.openai.com/codex/guides/agents-md).

An ordinary ChatGPT browser conversation does not by itself have a shell on your computer. For a hosted coding task or explicitly connected execution environment, paste the shared prompt there and verify where commands run. Installation in a cloud container is not installation on your laptop.

### Claude

Use **Claude Code** for a local terminal workflow:

```sh
claude "$INSTALL_PROMPT"
```

Preserve the loaded `CLAUDE.md` hierarchy: project `CLAUDE.md` or `.claude/CLAUDE.md`, or `~/.claude/CLAUDE.md` for intended user-wide guidance. Ordinary Claude chat likewise does not imply local shell access; use Claude Code or an explicitly connected environment. [CLI reference](https://code.claude.com/docs/en/cli-reference), [memory and instructions](https://code.claude.com/docs/en/memory).

### Other terminal-capable agents

Paste the shared prompt into an agent that has an approved Linux shell, or pass it using that agent's documented initial-prompt option. Do not invent a plugin installation command or assume every product uses `AGENTS.md`. If shell access or persistent instructions are unavailable, report the limitation instead of claiming installation.

## Verify the outcome

The installation agent must report:

- The installed version, executable location and actual host/container/workspace.
- A successful `jev-search --help` and parsed local dry-run JSON with `mode: dry-run` on a synthetic fixture.
- The exact instruction/skill location changed, preserving existing content and making complementary use explicit.
- Whether key injection still requires user action. A successful dry-run does **not** validate credentials or live inference.

Do not run the paid benchmark merely to validate installation. No paid calls are needed for the checks above. See the [usage and privacy contract](../README.md#privacy-and-output) before any later `--send`.

## Verification scope of these instructions

Hermes invocation was checked against local `--help` and official documentation. Other agent commands and instruction locations were checked against official documentation/source, **not by executing installations through every agent**. OpenCode's hosted docs were unavailable during checking, so its [official CLI source](https://github.com/anomalyco/opencode/blob/dev/packages/web/src/content/docs/cli.mdx) and [rules source](https://github.com/anomalyco/opencode/blob/dev/packages/web/src/content/docs/rules.mdx) were used. Agent versions, permissions and deployment configurations may differ; inspect current help before changing an installation.
