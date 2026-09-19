# Jev search: exploratory test report

## Takeaway

In a small, handselected real-knowledge pilot, adding Jev results to a simple lexical search recovered **7 additional relevant text units with 0 additional false positives**, across **4 of 6 tasks**. Recall increased from **64.71% to 85.29%** against predeclared relevance labels.

This is evidence of complementarity within a curated candidate pool, not proof of better search overall. The seven text units are **not seven independent discoveries**. Several were adjacent to, or continuations of, lexical hits. Reading surrounding context could recover some of the same material; lexical search plus context was not tested.

## What was measured

Two completed experiments are reported separately:

- **Synthetic check:** 20 lines, 3 intents, 2 repetitions per intent, 6 requests. Counts are aggregated across requests, including repetitions.
- **Real-knowledge pilot:** 6 simulated tasks using public technical documentation and knowledge-base excerpts, 16 candidate text units per task, one run per task. The resulting **96 query-text pair evaluations are not 96 unique documents**. Candidate pools were reused across queries.

The real pilot used the installed v0.1.0 CLI. Queries, lexical terms, candidate text and author-defined relevance labels were fixed before inference. Labels were not blind or independently adjudicated and included partial or context-dependent relevance. The Jev threshold was fixed at **0.5**, with no post-result tuning.

The real pilot's lexical baseline used OR matching over fixed substrings, without stemming, synonym expansion or contextual expansion. The combined method is the set union of lexical and Jev hits: it adds results but does not remove lexical false positives.

TP means a retrieved unit labeled relevant; FP means a retrieved unit labeled irrelevant; FN means a relevant unit not retrieved. Precision is TP / (TP + FP); recall is TP / (TP + FN). Percentages below are microaggregated and rounded to two decimal places.

## Synthetic results

| Method | TP | FP | FN | Precision | Recall |
|---|---:|---:|---:|---:|---:|
| Lexical baseline | 12 | 18 | 6 | 40.00% | 66.67% |
| Jev | 18 | 0 | 0 | 100.00% | 100.00% |

These results demonstrate behavior on this small synthetic example, not expected accuracy on arbitrary documents. Repeated evaluations of the same intents are not independent evidence of generalization.

## Real-knowledge results

| Method | TP | FP | FN | Precision | Recall |
|---|---:|---:|---:|---:|---:|
| Lexical baseline | 22 | 5 | 12 | 81.48% | 64.71% |
| Jev alone | 25 | 0 | 9 | 100.00% | 73.53% |
| Lexical + Jev union | 29 | 5 | 5 | 85.29% | 85.29% |

There were 34 relevant query-text pairs according to the frozen labels. The union recovered 29 rather than the lexical baseline's 22. It retained **all 5 lexical false positives** and still missed **5 relevant pairs**. Zero additional false positives does not mean zero total false positives.

Additional relevant units per task were **2, 2, 0, 2, 0 and 1**, respectively. Two tasks showed no additional relevant retrieval. In one task, lexical search and Jev each found the same number of relevant units but different subsets; their union recovered all labeled relevant units for that task. Jev alone also missed relevant units found by lexical search, supporting a complementary rather than replacement role.

### Failures and context dependence

- A relevant statement about input size limits received a Jev score of **0.49**, below the fixed **0.5** threshold. Both methods missed it. The threshold was not lowered after observing this failure.
- Isolated lines can lose meaning when a heading, preceding sentence or continuation is omitted. Some additional hits were neighboring pieces of material that lexical search had already located. Counting these as separate text units is valid for this evaluation, but not as independent discoveries.
- Some knowledge-base excerpts had typographic line breaks joined before evaluation. This context-preserving preparation happened outside the CLI and should not be attributed to it. Only visible retrieved content was used where source reads were truncated.

## Recorded cost and latency

| Experiment | Requests | Recorded inference cost (USD) | Median HTTP latency (seconds) |
|---|---:|---:|---:|
| Synthetic | 6 | 0.000655704 | 0.5561357871629298 |
| Real knowledge | 6 | 0.000639114 | 0.5362411406822503 |

Values above preserve the recorded aggregates. HTTP latency measures the Jev calls, not total research time. Costs exclude corpus preparation, candidate discovery, labeling, evaluation and the broader agent workflow. These observations are not a latency guarantee or evidence of time or cost savings over lexical search.

## Interpretation and limits

- **Small, curated sample:** six real tasks and one run per task cannot establish stability, statistical significance or performance across large repositories, whole knowledge bases, source code or languages generally. Some documentation was closely related to the evaluated workflow, limiting sample independence.
- **Limited comparator:** this is a comparison with a simple lexical baseline, not an agent's full iterative search process, lexical search plus surrounding context, or a tuned retrieval system.
- **No OpenViking superiority claim:** OpenViking supplied candidate documents for part of the pilot. Jev selected passages within the extracted pool. The experiment did not compare Jev with OpenViking's standalone semantic ranking, find documents outside that pool or measure global recall.
- **No end-to-end benefit claim:** final-answer quality, agent token savings, human reading time and end-to-end search performance were not measured.
- **Labels and source verification:** relevance depends on predeclared author judgments rather than blind expert review. A separate read-only audit confirmed the reported counts and highlighted context dependence. Full originals for part of the knowledge-base material were not available to that audit, limiting independent source comparison.

## Reproduce the synthetic benchmark

The public [synthetic aggregate](fixtures/benchmark-summary.json), [text fixture](fixtures/synthetic.txt) and [intents with labels](fixtures/intents.json) are included in this repository.

```sh
git clone --branch v0.1.1 https://github.com/larguesa/jev-search.git
cd jev-search
python3 -m tests
python3 -m tests.benchmark  # offline design summary; no API call
# Optional and paid: review the fixture and configure a budget-limited
# JEV_SEARCH_API_KEY before running this command.
python3 -m tests.benchmark --send --output benchmark-run-01
```

The paid runner makes up to six requests and saves aggregates to a new output directory. Existing directories are not overwritten; failures leave the directory reserved and do not produce a complete summary. A stop after reported cumulative cost exceeds USD 0.09 is an after-the-charge safeguard, not a hard spending cap. Enforce the budget on a dedicated inference key and disable temporary keys afterwards. No live inference runs in CI. A new run can differ from the historical results above.

## Evidence and verification

The synthetic table and accounting come from the original saved aggregate. Real-pilot counts were independently recalculated from saved gold labels, lexical hit sets and Jev scores at the fixed threshold; the union, additional hits, cost sum and latency median agree with the saved summary. No new inference was performed to prepare this report.

This is a sanitized public summary. It does not publish the real empirical corpus, private evidence, raw responses or local metadata. The real-pilot evidence is therefore **not publicly reproducible from this report alone**.

**Practical conclusion:** Jev showed a useful complementary signal on these selected passages. Retain lexical search, inspect surrounding context and verify retrieved material. A larger, independently labeled evaluation against lexical search with context is needed before making broader claims.
