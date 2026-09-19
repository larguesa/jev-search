# jev-search

Experimental v0.1.0: bounded, line-by-line semantic search for small text files and logs. Original Python implementation, inspired by [uehaj/jev-semgrep](https://github.com/uehaj/jev-semgrep). It does not import or execute that project.

Uses `typesafe/jev-1.13` through OpenRouter's [Decisions API](https://openrouter.ai/docs/api/api-reference/alphadecisions/submit-a-decisions-questions-and-answers-request.md), not chat completions or embeddings. No indexing, recursion, service, MCP or runtime dependencies.

**Linux only, Python 3.11+.** Uses POSIX safe-open flags; Windows and macOS are not supported/tested. [Português](README.pt-BR.md).

## Install from the Git tag

Requires Git and either uv or pipx. This is a Git installation, not a PyPI release.

```sh
uv tool install 'git+https://github.com/larguesa/jev-search.git@v0.1.0'
# Alternative:
pipx install 'git+https://github.com/larguesa/jev-search.git@v0.1.0'
jev-search --help
```

Installation may download build tools. The installed CLI uses only the Python standard library. The benchmark and example files are in the source checkout, not installed as commands.

## Review locally, then explicitly send

```sh
# Use a small, nonprivate UTF-8 file you have reviewed.
jev-search --query 'A customer requests their money back for a duplicate charge.' sample.log
```

Default **dry-run** does not access the network or read credentials. It prints JSON containing the selected lines and exact request payload. Review it before sending:

```sh
# Set JEV_SEARCH_API_KEY securely to a budget-limited inference key.
jev-search --send --max-requests 1 --query 'A customer requests their money back for a duplicate charge.' sample.log
```

Never supply a management key. Only `JEV_SEARCH_API_KEY` is read, only for `--send`; no `.env` loading or credential provisioning. Enforce spending limits on the key, not with this client. A send can incur charges even if the response fails validation or the connection fails.

The send uploads **all selected nonblank lines and the query**, not just matches, to `https://openrouter.ai/api/alpha/decisions` and its model provider. File paths are not included in the request, but content can itself reveal paths or personal data. Secret-pattern checks are incomplete: human review is required. Do not use private files.

Output includes absolute local paths, original text and, after sending, provider response metadata including a generation ID. Treat output as private; do not commit or publish it. Each result includes a 1-based `line`, `probability` and `match` (`probability >= 0.5`). Nonmatches remain in order. The score is not established as a calibrated probability. JSON escapes non-ASCII/control characters. Shell redirection can overwrite an existing file.

## Bounds and failure behavior

- 1 to 8 explicit `.txt`, `.md`, `.csv`, `.jsonl` or `.log` files. UTF-8 only; CSV/JSON are treated as lines, not parsed records.
- Combined maximum: 16,384 bytes, 64 physical lines, 2,048 bytes per line, 512 bytes per query, serialized request at most 60,000 bytes. Blank lines are skipped but count toward the physical-line limit. Exceeding limits fails, never truncates silently.
- Rejects hidden/suspicious path components, symlinks (including ancestors), duplicate inodes, nonregular files, common secret patterns and binary controls. Ancestor checks are not a sandbox against concurrent local directory changes.
- One request per CLI invocation; no retries or redirects. 30-second socket timeout, not a total wall-clock deadline. Response limit 256 KiB. Errors return a nonzero exit status.
- Validates model, response IDs, exact answer set, `noul` type, finite scores, cost and token counts. Requests only `typesafe`, with no fallbacks, `data_collection: deny`, maximum input price USD 0.042 per million tokens and output price zero. These are routing constraints, not a guarantee of privacy or a total spending cap.
- The API is alpha. Model availability, response format and prices can change; incompatible responses fail rather than silently relaxing constraints.

## Small synthetic experiment, not an accuracy claim

The fixed `synthetic.txt` has 20 invented PT/EN lines; `intents.json` has 3 intents with labels and lexical terms fixed before the pilot. Each intent was sent twice: 6 requests, 60 unique line/intent pairs, 120 decisions. The threshold was 0.5. Cases include paraphrases, negation, historical/resolved issues and one adversarial instruction.

| Method | Micro precision | Micro recall | TP / FP / FN |
|---|---:|---:|---:|
| Jev | 1.00 | 1.00 | 18 / 0 / 0 |
| Lexical OR substring baseline | 0.40 | 0.667 | 12 / 18 / 6 |

The completed pilot reported USD **0.000655704** total cost and **0.556 s** median HTTP latency. [Aggregate metrics](benchmark-summary.json) omit generation IDs, account metadata, paths and raw responses. The raw pilot evidence is not published; these aggregates are author-reported, not independently reproducible without a new paid run. No live inference runs in CI.

This tiny synthetic smoke experiment does **not** establish production accuracy, calibrated confidence, injection resistance, multilingual quality or superiority to BM25, embeddings or stronger rules. Repetitions are not independent samples. Lines share one request state and may influence each other.

```sh
git clone --branch v0.1.0 https://github.com/larguesa/jev-search.git
cd jev-search
python3 -m unittest -v
python3 jev_search.py --query 'refund request' synthetic.txt
python3 benchmark.py  # offline design summary, no API calls
# Optional, paid: review the fixtures and configure a limited key first.
python3 benchmark.py --send --output benchmark-run-01
```

The optional benchmark makes up to six requests, writes aggregate metrics only, and requires a new output directory. Existing directories are never overwritten; a failure leaves the directory reserved. It stops after reported cumulative cost exceeds USD 0.09, but that is an after-the-fact check, not a budget guarantee. Never rerun with the old pilot key. Failed/partial runs do not produce a complete summary.

## Development and license

Offline tests: `python3 -m unittest -v`. Build: `python3 -m build` (requires the `build` package). CI installs build tooling, then tests/builds and checks a fresh-venv CLI install without inference calls. Only `jev_search` is packaged as a runtime module; source archives use an explicit allowlist.

MIT, copyright Ricardo Pupo Larguesa. See [LICENSE](LICENSE).
