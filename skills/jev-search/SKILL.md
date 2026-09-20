---
name: jev-search
description: Use for semantic search alongside lexical search.
version: 0.2.0
author: Ricardo Pupo Larguesa (larguesa), Hermes Agent
platforms: [linux, windows]
license: MIT
---

# Jev complementary search

## When to use

Find intent expressed in different words in selected documents, notes or logs.
Keep lexical search for exact names, symbols and references; Jev complements it,
not replaces it. No recursive scan, index, MCP server or native vault connector.

## Install CLI and skill

Use Linux or Windows and Python 3.11+ with Git and uv or pipx. Review the source and
[installation guide](https://github.com/larguesa/jev-search/blob/main/docs/install.md)
at the chosen revision before installation. v0.2.0 is not yet published: use a
reviewed local v0.2.0 checkout, or verify publication before selecting its tag.
Record the reviewed revision; do not silently substitute a moving branch.

From that pinned checkout, run `uv tool install .` (or `pipx install .`) through
the agent's shell tool, then `jev-search --help`. Ask before replacing an install.
Installing the CLI or pip wheel does not automatically install agent skills.
Use the agent's current documentation to identify its supported skill discovery
directory for the intended project/user/profile. There is no universal discovery directory.
Using agent-native file tools, copy `skills/jev-search/SKILL.md` from the same
pinned checkout into `<documented discovery directory>/jev-search/SKILL.md`.
First inspect existing Jev skills and reuse/update overlapping guidance without
duplicates or loss of local policy. Preserve other skills and instructions; verify discovery with that agent's
documented listing/loading mechanism (reload only as documented). If skills are
unsupported, use a named section in existing supported instructions as a fallback
and report it rather than claiming native skill installation.

## Configure once

Have the user create a dedicated OpenRouter **inference** key at
https://openrouter.ai/settings/keys with suitable provider-side spending controls.
Inject it as `JEV_SEARCH_API_KEY` through a protected process environment or
approved secret store into the process running the CLI. Never use a management
key, provision keys automatically, or ask for a key in chat. Never inspect/print
its value or place it in prompts, command arguments, instructions, Git or logs.
The CLI does not load `.env` or fall back to other provider key variables.

Record user-authorized content scope, provider and budget once. Routine searches
within that scope need no new human approval per search; preserve agent sandbox
and approval rules and ask before expanding scope, provider or budget. A key
alone does not authorize files. Follow the user/organization's confidentiality
policy rather than imposing a blanket private-file ban.

OpenRouter is the default: model `typesafe/jev-1.13`, native Decisions API, not
chat completions. Optional direct TypeSafe uses `--provider typesafe`, model
`jev-1.13.0` and a TypeSafe-issued inference key in the same variable. Select a
persistent provider/model via `JEV_SEARCH_PROVIDER`/`JEV_SEARCH_MODEL`; flags
`--provider`/`--model` override them. Keys are not interchangeable; model overrides
must support the native `state`/`questions`/`answers`/`noul` contract.
Direct TypeSafe local contract tests passed; live tests remain pending because
the maintainer lacks direct API access. Missing cost is unavailable, not free.

## Procedure

1. Orient with agent-native filename, lexical search and reading tools. Select
   bounded relevant files, not only literal keyword hits. Review content scope.
2. Supply **1 to 8 explicit UTF-8 files**: `.txt`, `.md`, `.csv`, `.jsonl`, `.log`.
   Combined limits: **16,384 bytes**, **64 physical lines**; **2,048 bytes per
   line**, **512 bytes per query**, **60,000 bytes per serialized request**.
   Blank lines count toward limits but are not evaluated. CSV/JSON are lines,
   not parsed records. No silent truncation. If needed, create smaller reviewed
   excerpts using native file tools and retain source/line provenance separately.
3. Run through the agent's shell tool:
   ```sh
   jev-search --query 'A customer requests a refund for a duplicate charge.' sample.log
   ```
   **Real search is the default** and can incur charges. Optional `--dry-run`
   previews the payload offline without reading credentials or evaluating meaning;
   `--send` is only a legacy explicit-send alias. Setup is offline first.
4. Merge semantic and lexical candidates, deduplicate by source/line, and read
   original context before answering. Cite sources, not scores as proof. Output
   has 1-based lines, original text, `probability` and `match` at threshold 0.5;
   scores are not established as calibrated for these tasks.

## Optional ranking

Use `--rank` or `--top-k 1..64` only when ordered or bounded selection is useful.
All original `results` remain; `ranked_results` contains matches in stable
score-descending order. The added view increases JSON size; it does not by itself
save tokens. Verify installed help before using these flags.
The small initial test tied; a deeper amended study found improved evidence
coverage in natural order but regressions against a shuffled-order baseline.
Keep ranking opt-in, not a sufficiency or diversity guarantee. See
`tests/RANKING_DEPTH_REPORT.md` for aggregate results and transport-recovery limits.
Dry-run/error `unjudged.candidates` map to nonblank row order; null means rows
could not be loaded. Unjudged rows are not negative matches. No extra query runs.

## Pitfalls

All selected nonblank lines and the query are uploaded, not just matches:
OpenRouter and TypeSafe on the default route, or TypeSafe alone when direct.
Secret checks are incomplete. Hidden/suspicious paths, symlinks (including
ancestors), duplicate inodes, nonregular files and binary controls are rejected;
do not bypass checks. Output/dry-runs contain text and local paths: protect them.

One request per invocation, no retry or redirect. `--max-requests 1` is not a
monetary cap; failed calls may still cost money. Respect provider spending limits.
TypeSafe states no training/fine tuning on Input in its
[privacy policy](https://typesafe.ai/legal/privacy-policy); its
[legal docs](https://docs.typesafe.ai/legal) offer enterprise ZDR, not universal
zero retention. Apply the relevant account terms, including OpenRouter's.

## Verification

At setup, verify installed package metadata is version 0.2.0, CLI help and skill
discovery. Create a tiny synthetic `sample.txt` with an agent-native file tool in
a safe temporary directory, then run:

```sh
jev-search --dry-run --query 'greeting' /path/to/sample.txt
```

Parse JSON and confirm `mode: dry-run`, selected rows and intended provider/model.
Report exact CLI/skill locations and any remaining key/scope/budget setup without
secrets. Dry-run does not validate credentials or live inference. Only with
user-authorized provider, content and budget, optionally run one tiny nonprivate
live smoke test and report it separately; never run a paid benchmark for setup.
For authorized searches, check exit status
and returned lines; report failures instead of inventing results.
