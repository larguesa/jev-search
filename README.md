# jev-search

**Find by meaning what keywords miss.** Complementary semantic search for agents exploring documents and knowledge bases alongside their existing tools.

Exact search finds names, symbols and literal references. `jev-search` adds another perspective: whether a line expresses the intent you are looking for, even with different wording. Keep both, then read the surrounding context.

## Why complementary search?

- **Repository documentation:** explore design intentions and trade-offs, then inspect the actual source with your usual tools.
- **LLM Wiki and second brains:** find related ideas expressed differently in selected Markdown notes, then follow links and original sources.
- **Obsidian and OpenViking workflows:** evaluate selected, nonprivate passages alongside existing search, tags and navigation. No native plugin or connector is included.

Illustrative example: a query for *decisions that reduce vendor dependence* could surface *we adopted open formats to make migration easier*. This example is not a measured result.

### Early evidence

In six simulated tasks over selected real technical text, combining a simple lexical search with Jev recovered **29 of 34 labeled relevant passages**, versus **22 of 34** for lexical search alone: **seven additional relevant text units, with no additional false positives**. Six requests cost **USD 0.000639114**, with **0.536 s median HTTP latency**.

These are small, manually curated experiments, not a general accuracy claim. Several extra text units are adjacent to lexical hits and might already be found by reading their context. The union retained five lexical false positives and missed five relevant passages. **We have not demonstrated an advantage over lexical search plus context reading.**

Read the **[test and benchmark report](tests/REPORT.md)** for both the synthetic pilot and real-text experiment, methods, omissions and limitations.

## Install

**Linux or Windows, Python 3.11+, Git and either [uv](https://docs.astral.sh/uv/) or [pipx](https://pipx.pypa.io/).** macOS is not supported/tested. The installed CLI uses only the Python standard library; installation may download build tools.

Windows support is currently an **unreleased source change**; tag `v0.1.1` remains Linux-only. From this reviewed checkout, install with `uv tool install .`. Use `python` instead of `python3` on Windows. Only local regular files in trusted directories are supported: UNC/device paths, alternate data streams, reserved device names and reparse points (including junctions and cloud placeholders) are rejected. These checks do not protect against hostile concurrent filesystem mutation. Do not remove these restrictions to make a path work; select a reviewed local copy instead.

### Install from the Git tag

```sh
uv tool install 'git+https://github.com/larguesa/jev-search.git@v0.1.1'
# Alternative:
pipx install 'git+https://github.com/larguesa/jev-search.git@v0.1.1'
jev-search --help
```

This is a Git installation, not a PyPI release. For an existing installation, use `uv tool install --force` with the same pinned URL. If the executable is not found, follow your tool manager's PATH instructions and open a new terminal.

### Install through your agent

Use the **[agent installation guide](docs/install.md#install-through-an-agent)** for **Hermes, OpenClaw, OpenCode, Pi coding agent, ChatGPT/Codex and Claude Code**, plus other terminal-capable agents. It supplies a shared setup prompt and the commands that actually invoke each agent.

The setup prompt tells the agent to install the pinned release, preserve existing instructions, register **complementary** use, configure a budget-limited OpenRouter inference key securely and verify a local dry-run. It does not authorize uploading a repository or spending money automatically.

### Configure the inference key

This version runs **TypeSafe Jev through OpenRouter**, using `typesafe/jev-1.13` on the [Decisions API](https://openrouter.ai/docs/api/api-reference/alphadecisions/submit-a-decisions-questions-and-answers-request.md). It does not use chat completions or embeddings.

Create a dedicated, spending-limited **OpenRouter inference key** and expose it as `JEV_SEARCH_API_KEY`. Do not use a management key or assume an agent's own provider login supplies this key. **A direct TypeSafe API key is not supported by this client and is not interchangeable with an OpenRouter key.**

For secret-safe terminal entry, agent environment setup and provider details, see [key configuration](docs/install.md#configure-the-key-without-sharing-it-in-chat).

## Use

```sh
# A small, nonprivate UTF-8 file you have reviewed.
jev-search --query 'A customer requests money back for a duplicate charge.' sample.log
```

Default **dry-run** does not access the network, read credentials or evaluate meaning. It prints JSON containing selected lines and the exact request payload. Review it before explicitly authorizing a paid request:

```sh
jev-search --send --query 'A customer requests money back for a duplicate charge.' sample.log
```

Only `JEV_SEARCH_API_KEY` is read, only with `--send`. The CLI does not load `.env`, provision keys or enforce a total monetary budget. Set spending limits on the key. A failed connection or rejected response may still incur a charge.

### How an agent should use it

Orient using filenames, indexes, tags, links and exact search. Select a bounded set of reviewed passages, apply Jev as another retrieval pass, merge the candidates and read the original context before answering. Do not limit the entire candidate pool to literal keyword hits, or semantic search cannot recover excluded material.

The tool evaluates **lines**, not an entire document, knowledge graph or codebase. If PDF line wrapping splits a statement, any passage reconstruction must preserve provenance and be documented separately; the CLI does not perform that preprocessing.

## Privacy and output

`--send` uploads **all selected nonblank lines and the query**, not just matches, to `https://openrouter.ai/api/alpha/decisions` and its model provider, TypeSafe. File paths are not included in the request, but content may itself reveal paths or personal data. Secret-pattern checks are incomplete. Human review is required; do not use private files, confidential repositories or private vaults.

Output includes absolute local paths, original text and, after sending, provider metadata including a generation ID. **Treat output as private; do not commit or publish it.** Results include a 1-based `line`, `probability` and `match` (`probability >= 0.5`). Nonmatches remain in the original order. Scores are not established as calibrated probabilities. JSON escapes non-ASCII/control characters. Shell redirection can overwrite files.

## Scope and limits

Experimental **v0.1.1** keeps a small surface: no indexing, recursive traversal, service, MCP, source-code parsing or runtime dependencies.

- **Inputs:** 1 to 8 explicit `.txt`, `.md`, `.csv`, `.jsonl` or `.log` files. UTF-8 only; CSV/JSON are treated as lines, not parsed records.
- **Bounds:** 16,384 bytes and 64 physical lines combined; 2,048 bytes per line; 512 bytes per query; serialized request at most 60,000 bytes. Blank lines count toward the physical limit but are skipped during evaluation. Exceeding limits fails, without silent truncation.
- **Files:** rejects hidden/suspicious path components, symlinks including ancestors, duplicate inodes, nonregular files, common secret patterns and binary controls. Checks are not a sandbox against concurrent local directory changes.
- **Network:** one request per invocation; no retries or redirects. Socket timeout 30 seconds, not a total deadline. Response limit 256 KiB. Errors return nonzero status.
- **Validation:** checks model, response IDs, exact answer set, `noul` type, finite scores, cost and token counts.
- **Routing:** only `typesafe`, no fallbacks, `data_collection: deny`, maximum input price USD 0.042 per million tokens and output price zero. Routing constraints are not a privacy guarantee or total spending cap.
- **API stability:** the Decisions API is alpha. Availability, format and prices can change; incompatible responses fail rather than silently relaxing constraints.

## Repository layout

```text
jev_search.py        CLI implementation
pyproject.toml       Package metadata and console entry point
MANIFEST.in          Explicit source-distribution allowlist
docs/                Installation and agent setup guide
tests/               Offline tests, benchmark runner, fixtures and report
.github/workflows/   Offline CI checks
```

The root also contains this README, the license and Git ignore rules. Only `jev_search` is installed as a runtime module.

## Development

From a source checkout:

```sh
python3 -m tests  # offline discovery; fails if no tests are found
python3 -m tests.benchmark  # offline experiment description, no inference
python3 jev_search.py --query 'refund request' tests/fixtures/synthetic.txt
```

Build with `python3 -m build` after installing the `build` package. CI runs offline tests, builds distributions and checks an isolated CLI installation without inference. See [tests/REPORT.md](tests/REPORT.md) for optional paid benchmark reproduction and its budget safeguards.

## Credits and license

Original Python implementation inspired by [uehaj/jev-semgrep](https://github.com/uehaj/jev-semgrep), without importing or executing that project. MIT; see [LICENSE](LICENSE).
