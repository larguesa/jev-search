# Deeper ranking evaluation (aggregate-only)

## Decision

A completed **amended exploratory study** supports offering score ranking as an **opt-in** view, not changing default search or claiming general superiority. The numeric improvement gate passed. Manual transport recovery was required; this was not an uninterrupted execution of the original protocol.

The earlier six-task synthetic study remains unchanged in `RANKING_REPORT.md`: it measured six ties. It had little competition for the selected positions and did not establish absence of benefit on harder tasks.

## Design

- Twelve Portuguese queries: six over authoritative public technical documents and six over passages selected from actual knowledge-base retrievals.
- 160 candidate instances, 156 distinct visible texts, 10–16 candidates per query. Sources, task definitions and facet labels were independently reviewed and frozen before inference.
- Grade 2 directly supports at least one required evidence facet; grade 1 is related context; grade 0 is not relevant. Each question requires at least three facets. Some contextual prefixes preserve source API identity or distinguish editorial proposals from verified execution.
- Two live scoring repetitions per task, with reversed task execution order in repetition two. Both ranking arms reuse exactly the same validated scores.
- Baseline: first three matches in candidate order. Treatment: first three matches after stable descending-score ranking. Threshold 0.5. This compares constrained passage selection, not the current CLI's complete unbounded result view.
- Primary metric: fraction of required evidence facets covered by selected passages. Also check fixed-k precision, graded nDCG, candidate-pool recall, text bytes and redundancy. Facet contribution is not complete-answer correctness.
- Numeric gate: all 24 logical evaluations present; more than three matches in both repetitions for at least eight tasks; mean coverage gain at least five percentage points; no precision/nDCG loss overall and no mean coverage loss in either source group.

## Completed comparison

Task means weight the two repetitions equally. Win/tie/loss counts classify each task's mean coverage difference, not individual repetitions.

| Group | First matches: coverage | Ranked: coverage | Wins / ties / losses |
|---|---:|---:|---:|
| Public documentation | 44.44% | 69.44% | 4 / 2 / 0 |
| Retrieved knowledge passages | 54.17% | 69.44% | 3 / 3 / 0 |
| Overall | 49.31% | 69.44% | 7 / 5 / 0 |

Eleven of twelve tasks had more than three matches in both repetitions. Overall fixed-k precision remained 1.0 in this relevance-rich sample; nDCG improved from 0.9739 to 1.0. Candidate-pool recall remained 0.2335. Mean selected UTF-8 text was 806.5 versus 744.875 bytes; this is not token accounting or a reduction in the full JSON response.

## Sensitivity and limitations

Predeclared offline replays reuse scores; they do not show that model scores themselves are insensitive to input order.

| Diagnostic | First matches: coverage | Ranked: coverage |
|---|---:|---:|
| Reversed candidate order, k=3 | 65.28% | 69.44% |
| Seeded shuffled order, k=3 | 73.61% | 69.44% |
| Original candidate order, k=1 | 32.64% | 40.97% |
| Original candidate order, k=5 | 68.06% | 90.28% |

**The seeded-order baseline beat ranking.** Individual relevance scores do not optimize complementary evidence. Keep ranking optional, preserve all original results, and read source context. This small curated corpus, partly sharing sources across queries, is not a representative retrieval benchmark, a statistical superiority result, a factual verification system or a demonstrated answer-quality improvement. One task cannot fit all required facets into three passages.

## Transport failures and amendment

Two earlier attempts with a 30-second socket timeout stopped after 20 and five validated responses, respectively. Their failed requests and partial results were retained separately and were not incorporated into the completed comparison.

The user authorized a longer timeout and completion of the test. The CLI now uses a 300-second socket timeout and reports exception class names without exposing raw error messages. The subsequent run preserved fourteen valid responses before one request returned `TimeoutError`. A separately documented manual continuation issued the ten missing logical evaluations, including an explicit repeat of that failed slot. It did not replace any successful result or select among competing successful responses. A private source manifest maps every logical slot to its original raw response.

Thus the completed amended comparison contains 24 valid responses from 25 attempted requests. The client still does not automatically retry. All three failed historical requests may have incurred unknown charges. Timeout increase did not establish the cause of the earlier generic errors or eliminate transient transport failure. The original inputs, labels, queries, model request, threshold, metrics and numeric gate were not tuned after seeing results. Prior outcomes were already visible when the transport amendment was made; this limitation is explicit.

## Privacy and reproducibility boundary

This public report contains aggregate methodology and results only. Detailed queries, source excerpts, knowledge URIs, private paths, labels, individual scores, request IDs, raw provider responses and private hashes remain outside the repository. They were retained for internal independent verification. The public synthetic benchmark and offline unit tests remain runnable; these aggregate-only private-corpus results cannot be fully reproduced from this repository alone.
