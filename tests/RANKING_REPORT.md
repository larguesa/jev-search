# Optional ranking experiment

## Decision

**No measured gain. Do not publish or deploy on the strength of this study.**

The prototype adds optional `--rank` and `--top-k 1..64`, preserves every original result, and explicitly identifies unjudged candidates in dry-run/error output. The new flags are experimental local changes, not an installed release. No answer-sufficiency classifier or prompt-injection detector was added.

## Frozen design

- Baseline source: `a1462624ac982190518f40673ad9b0981cd85de9`.
- Fixture: [`fixtures/ranking.json`](fixtures/ranking.json), SHA-256 `d526f88dd19ffa47c354d440d48b83ffbef96e055079d4295ea590b06aa4f455`.
- Six fictional synthetic tasks, eight candidates each, one completed live OpenRouter request per task using `typesafe/jev-1.13`.
- Three tasks put complete evidence after partial material; two controls put complete evidence first; one task has no complete answer.
- Labels and order were fixed before inference: grade 0 unrelated/contradictory, grade 1 related but incomplete, grade 2 individually supplies all requested facts.
- Paired replay, not two independent model runs: both arms reuse the exact same live response and filter `match >= 0.5`. Baseline takes the first two matching rows in input order; treatment sorts the matching rows by descending score, stably, then takes two.
- Acceptance: strictly higher macro nDCG@2, no decrease in relevance precision@2, and no increase in the hypothetical false-sufficiency count. No post-result tuning.

## Actual results

The machine-readable evidence is [`fixtures/ranking-results.json`](fixtures/ranking-results.json), including per-task provider scores and usage but excluding generation IDs and local paths.

| Metric | Input-order baseline | Ranked |
|---|---:|---:|
| Macro precision@2 | 0.833333 | 0.833333 |
| Macro candidate-pool recall@2 | 0.333333 | 0.333333 |
| Macro nDCG@2 | 0.833333 | 0.833333 |
| Complete-answer passage precision@2 | 0.833333 | 0.833333 |
| Hypothetical false-sufficient cases | 0 | 0 |
| Hypothetical false-insufficient cases | 0 | 0 |

**Zero wins, six ties, zero losses. Acceptance gate: false.** Each task selected exactly the same passages in both arms. The existing line classifier already rejected partial material for the specific queries, so sorting added no benefit here. The no-answer task returned no matches in both arms.

Six completed requests cost **USD 0.000307146**. Median HTTP latency was **0.346683 s**, mean **0.361542 s**, minimum **0.306384 s**, maximum **0.448072 s**. These measure shared inference, not an incremental ranking request; sorting is local. No token saving is demonstrated: `ranked_results` duplicates selected text while `results` retains all original rows.

## Failed attempt and intervention

An earlier attempt stopped on its first invocation with a network failure, no scores and no automatic retry. Its raw stdout/stderr, frozen fixture and incomplete status are retained privately. The potential charge for that failed invocation is unknown, so the completed-run cost above is not a verified total for all attempts.

Public endpoint checks then succeeded and the configured inference key was valid. A separate fresh run used the identical frozen fixture and acceptance criteria, retaining the runtime's TLS certificate environment alongside the minimal CLI environment. Both environments could reach a public endpoint, so the cause of the first failure is **not established**. This was an explicitly recorded second study attempt, not a hidden retry or deletion of failed evidence. Across both attempts there were seven CLI inference invocations, six successful and one failed.

## What is and is not supported

- The implementation preserves original results and provenance; ranking does not discard the full evidence pool.
- Dry-runs and failures report candidate IDs `l0`, `l1`, etc., aligned with nonblank rows. `candidates: null` means loading did not complete. Failed response validation remains all-or-nothing and exits nonzero.
- Relevance is not answer sufficiency. The experiment's hypothetical probe marks selected nonempty lists with no individually complete passage as false-sufficient; it does not evaluate generated answers, multi-passage composition or calibrated answerability.
- No sufficiency score was shipped. An empty match list is grounds to reconsider the query/candidates, not proof that the answer does not exist.
- This small English-only, deliberately structured synthetic sample cannot establish global recall, production performance, Portuguese performance, improved OpenViking retrieval, or general uselessness of ranking.
- Results do not justify another tuned benchmark merely to obtain a positive outcome. Keep the existing production tool unchanged.

## Reproduce

Offline by default:

```sh
python3 -m tests
python3 -m tests.ranking_benchmark --dry-run
```

Only with explicitly authorized inference, suitable `JEV_SEARCH_API_KEY`, and a fresh private directory:

```sh
python3 -m tests.ranking_benchmark --send --output /absolute/path/new-ranking-study
```

The runner uses the actual CLI, persists its raw output, rejects an existing output directory, stops on failure, and makes no automatic retries. Do not overwrite the frozen fixture or historical results when reproducing. Windows-specific filesystem tests require Windows; Linux skips are not Windows execution evidence.
