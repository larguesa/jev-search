# jev-search

**Find by meaning what keywords miss.** Complementary semantic search for agents exploring documents and knowledge bases alongside their existing tools.

Exact search finds names, symbols and literal references. `jev-search` adds another perspective: whether a line expresses the intent you are looking for, even with different wording. Keep both, then read the surrounding context.

## Why complementary search?

- **Repository documentation:** explore design intentions and trade-offs, then inspect the actual source with your usual tools.
- **LLM Wiki and second brains:** find related ideas expressed differently in selected Markdown notes, then follow links and original sources.
- **Obsidian and OpenViking workflows:** evaluate selected, authorized passages alongside existing search, tags and navigation. No native plugin or connector is included.

Illustrative example: a query for *decisions that reduce vendor dependence* could surface *we adopted open formats to make migration easier*. This example is not a measured result.

### Early evidence

In six simulated tasks over selected real technical text, combining a simple lexical search with Jev recovered **29 of 34 labeled relevant passages**, versus **22 of 34** for lexical search alone: **seven additional relevant text units, with no additional false positives**. Six requests cost **USD 0.000639114**, with **0.536 s median HTTP latency**.

These are small, manually curated experiments, not a general accuracy claim. Several extra text units are adjacent to lexical hits and might already be found by reading their context. The union retained five lexical false positives and missed five relevant passages. **We have not demonstrated an advantage over lexical search plus context reading.**

Read the **[test and benchmark report](tests/REPORT.md)** for both the synthetic pilot and real-text experiment, methods, omissions and limitations.

## Install

**Linux or Windows, Python 3.11+, Git and either [uv](https://docs.astral.sh/uv/) or [pipx](https://pipx.pypa.io/).** macOS is not supported/tested. The installed CLI uses only the Python standard library; installation may download build tools.

Windows support is included in the v0.2.0 source checkout; tag `v0.1.1` remains Linux-only. From this reviewed checkout, install with `uv tool install .`. Use `python` instead of `python3` on Windows. Only local regular files in trusted directories are supported: UNC/device paths, alternate data streams, reserved device names and reparse points (including junctions and cloud placeholders) are rejected. These checks do not protect against hostile concurrent filesystem mutation. Do not remove these restrictions to make a path work; select a reviewed local copy instead.

### Install v0.2.0

**The v0.2.0 code is on `main`; a v0.2.0 tag/release has not been published.** Obtain a local checkout with `git clone --branch main https://github.com/larguesa/jev-search.git`, review it, and record `git rev-parse HEAD` inside that checkout. Use that same reviewed revision for both the CLI and skill; `main` can change. Then install:

```sh
cd /path/to/jev-search
uv tool install .
# Alternative: pipx install .
jev-search --help
```

After publication, use the pinned Git tag (these commands require that tag to exist):

```sh
uv tool install 'git+https://github.com/larguesa/jev-search.git@v0.2.0'
# Alternative:
pipx install 'git+https://github.com/larguesa/jev-search.git@v0.2.0'
jev-search --help
```

This is a Git installation, not a PyPI release. For an existing installation, use `uv tool install --force` with the same pinned URL. If the executable is not found, follow your tool manager's PATH instructions and open a new terminal.

### Install through your agent

Use the **[agent installation guide](docs/install.md#install-through-an-agent)** for **Hermes, OpenClaw, OpenCode, Pi coding agent, ChatGPT/Codex and Claude Code**, plus other terminal-capable agents. It supplies a shared setup prompt and the commands that actually invoke each agent.

The setup prompt installs **both the CLI and the [portable skill](skills/jev-search/SKILL.md)** from the same reviewed pinned checkout. A pip wheel does not automatically install agent skills: the agent copies the skill using its native file tools into its documented discovery directory for the intended scope, with no universal path assumed. Reuse/update overlapping Jev guidance without duplicating it or discarding local policy. The prompt preserves existing instructions, registers **complementary** use, configures the selected provider securely and verifies an explicit offline dry-run. Once the user has authorized the content scope, provider and budget, agents can use real search routinely within those boundaries, without a new human approval for every search. Normal agent permissions and sandbox rules still apply; setup is offline first, with one tiny live smoke test only if the user authorizes its provider, content and budget; never run a paid benchmark for installation.

### Configure the inference key

Choose one of two native structured-decision backends; neither uses chat completions or embeddings:

| Provider | Endpoint | CLI default model | Credential issuer |
|---|---|---|---|
| `openrouter` (default) | `https://openrouter.ai/api/alpha/decisions` | `typesafe/jev-1.13` | OpenRouter |
| `typesafe` | `https://api.typesafe.ai/v1/systemone` | `jev-1.13.0` | TypeSafe |

Set `--provider openrouter|typesafe` or `JEV_SEARCH_PROVIDER`, and optionally `--model` or `JEV_SEARCH_MODEL`. Explicit flags take precedence over environment settings. Both backends send native `state` and `questions` and read `answers` containing `noul` scores. A model override must support that contract and the selected backend's response validation; it does not enable arbitrary chat models or additional providers.

Sources: [OpenRouter Decisions](https://openrouter.ai/docs/api/api-reference/alphadecisions/submit-a-decisions-questions-and-answers-request.md), [TypeSafe API](https://docs.typesafe.ai/api), [TypeSafe models](https://docs.typesafe.ai/models). The direct default pins TypeSafe's documented `jev-1.13.0`; its `jev-latest` and `jev-preview` aliases can resolve to a versioned response model. OpenRouter v0.2.0 real setup smoke testing passed (not a benchmark). Direct TypeSafe local contract tests passed; direct live tests remain pending because the maintainer lacks API access. Documentation and offline validation do not establish live account access.

Expose an **inference key issued by the selected provider** as `JEV_SEARCH_API_KEY`. Keys are not interchangeable. Use a dedicated key and provider-side spending controls appropriate to the authorized budget. Do not use a management key or assume an agent's own provider login supplies this key. There is no automatic fallback to `OPENROUTER_API_KEY`, `TYPESAFE_API_KEY` or other provider secrets.

For secret-safe terminal entry, agent environment setup and provider details, see [key configuration](docs/install.md#configure-the-key-without-sharing-it-in-chat).

## Use

```sh
# Real search: a small UTF-8 file within the authorized content scope.
jev-search --query 'A customer requests money back for a duplicate charge.' sample.log
```

**Real search is the default** and may incur charges. For an explicit offline preview, add `--dry-run`; it does not access the network, read credentials or evaluate meaning. It prints JSON containing selected lines and the request payload:

```sh
jev-search --dry-run --query 'A customer requests money back for a duplicate charge.' sample.log
# Direct TypeSafe search, with a TypeSafe key already injected:
jev-search --provider typesafe --model jev-1.13.0 --query 'refund request' sample.log
```

`--send` remains only as a backward-compatible explicit real-search flag; it is no longer needed. Only `JEV_SEARCH_API_KEY` supplies the inference credential, and it is read only for real search. The CLI does not load `.env`, provision keys or enforce a total monetary budget. `--max-requests 1` bounds requests, not money. Set provider-side spending limits. A failed connection or rejected response may still incur a charge.

### How an agent should use it

Orient using filenames, indexes, tags, links and exact search. Select a bounded set of reviewed passages, apply Jev as another retrieval pass, merge the candidates and read the original context before answering. Do not limit the entire candidate pool to literal keyword hits, or semantic search cannot recover excluded material.

The tool evaluates **lines**, not an entire document, knowledge graph or codebase. If PDF line wrapping splits a statement, any passage reconstruction must preserve provenance and be documented separately; the CLI does not perform that preprocessing.

## Privacy and output

Real search uploads **all selected nonblank lines and the query**, not just matches. With `openrouter`, they go to OpenRouter and its model provider, TypeSafe; with `typesafe`, they go directly to TypeSafe. File paths are not included in the request, but content may itself reveal paths or personal data. Secret-pattern checks are incomplete.

The user or organization decides which confidential content may be processed by which provider. Apply that policy and the authorized budget as with other external inference tools; private files are not categorically forbidden, nor does configuring a key authorize every file. Once configured, agents may select bounded inputs and search within the approved scope without per-search human review. Ask before expanding content scope, provider authorization or budget. Never bypass agent sandbox restrictions or expose keys.

[TypeSafe's Privacy Policy](https://typesafe.ai/legal/privacy-policy) states that it will not train or fine tune models on prompts or other Input. Its [legal documentation](https://docs.typesafe.ai/legal) offers zero data retention for **enterprise customers**; this is not a universal zero-retention guarantee. No-training and no-retention are different claims. Review the applicable provider terms and account arrangements, including OpenRouter's when using that route.

Output includes absolute local paths, original text and, after sending, provider metadata. OpenRouter returns a generation ID and cost; direct TypeSafe responses need not include them. **Missing direct-provider cost means unavailable, not zero or free inference.** Treat output according to the input's confidentiality policy and review it before committing or publishing. Results include a 1-based `line`, `probability` and `match` (`probability >= 0.5`). Nonmatches remain in the original order. Scores are not established as calibrated probabilities for these search tasks. JSON escapes non-ASCII/control characters. Shell redirection can overwrite files.

## Scope and limits

**v0.2.0 is a functional search CLI**, not a testing-only tool. Its benchmarks remain exploratory. It keeps a small surface: no indexing, recursive traversal, service, MCP, source-code parsing or runtime dependencies.

- **Inputs:** 1 to 8 explicit `.txt`, `.md`, `.csv`, `.jsonl` or `.log` files. UTF-8 only; CSV/JSON are treated as lines, not parsed records.
- **Bounds:** 16,384 bytes and 64 physical lines combined; 2,048 bytes per line; 512 bytes per query; serialized request at most 60,000 bytes. Blank lines count toward the physical limit but are skipped during evaluation. Exceeding limits fails, without silent truncation.
- **Files:** rejects hidden/suspicious path components, symlinks including ancestors, duplicate inodes, nonregular files, common secret patterns and binary controls. Checks are not a sandbox against concurrent local directory changes.
- **Network:** one request per invocation; no retries or redirects. Socket timeout 30 seconds, not a total deadline. Response limit 256 KiB. Errors return nonzero status.
- **Validation:** checks the selected model, exact answer set, `noul` type, finite scores and token counts; OpenRouter also requires generation ID and cost. Direct TypeSafe cost is not fabricated when absent.
- **OpenRouter routing:** only `typesafe`, no fallbacks, `data_collection: deny`. These OpenRouter-specific fields are not sent to direct TypeSafe. Routing constraints are not a privacy guarantee or total spending cap; use provider-side budget controls and check current pricing.
- **API stability:** OpenRouter's Decisions API is alpha. Availability, model names, formats and prices can change on either backend; incompatible responses fail rather than silently relaxing constraints.

## Repository layout

```text
jev_search.py        CLI implementation
pyproject.toml       Package metadata and console entry point
MANIFEST.in          Explicit source-distribution allowlist
docs/                Installation and agent setup guide
skills/jev-search/   Portable agent skill (copied separately)
tests/               Offline tests, benchmark runner, fixtures and report
.github/workflows/   Offline CI checks
```

The root also contains this README, the license and Git ignore rules. Only `jev_search` is installed as a runtime module.

## Development

From a source checkout:

```sh
python3 -m tests  # offline discovery; fails if no tests are found
python3 -m tests.benchmark  # offline experiment description, no inference
python3 jev_search.py --dry-run --query 'refund request' tests/fixtures/synthetic.txt
```

Build with `python3 -m build` after installing the `build` package. CI runs offline tests, builds distributions and checks an isolated CLI installation without inference. See [tests/REPORT.md](tests/REPORT.md) for optional paid benchmark reproduction and its budget safeguards.

## Credits and license

Original Python implementation inspired by [uehaj/jev-semgrep](https://github.com/uehaj/jev-semgrep), without importing or executing that project. MIT; see [LICENSE](LICENSE).
