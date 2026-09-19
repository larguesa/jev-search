"""Fixed synthetic experiment; public output contains aggregate metrics only."""
import json
import statistics
import time
from pathlib import Path
import jev_search as j


def metrics(predicted, expected):
    tp = len(predicted & expected)
    fp = len(predicted - expected)
    fn = len(expected - predicted)
    return {'tp': tp, 'fp': fp, 'fn': fn,
            'precision': tp / (tp + fp) if tp + fp else 0,
            'recall': tp / (tp + fn) if tp + fn else 0}


def run(key, output=None):
    root = Path(__file__).resolve().parent
    out = Path(output) if output is not None else root.parent / 'evidence'
    # Exclusive creation protects prior evidence, including interrupted runs.
    out.mkdir(parents=True, exist_ok=False)
    rows = j.load_files([str(root / 'fixtures' / 'synthetic.txt')])
    intents = json.loads((root / 'fixtures' / 'intents.json').read_text(encoding='utf8'))
    runs = []
    for repetition in range(2):
        for intent in intents:
            start = time.perf_counter()
            lexical = {r['line'] for r in rows if any(term in r['original'].lower() for term in intent['lexical_terms'])}
            lex_latency = time.perf_counter() - start
            raw, latency = j.send_request(j.build_request(rows, intent['query']), key)
            data = json.loads(raw)
            results = j.validate_response(data, rows)
            expected = set(intent['positive_lines'])
            predicted = {r['line'] for r in results if r['match']}
            runs.append({'latency_seconds': latency, 'cost_usd': data['usage']['cost'],
                         'semantic': metrics(predicted, expected),
                         'lexical': metrics(lexical, expected),
                         'lexical_latency_seconds': lex_latency,
                         'probabilities': [r['probability'] for r in results]})
            if sum(r['cost_usd'] for r in runs) > 0.09:
                raise ValueError('conservative stop; no more calls; charges already incurred')
    summary = {'requests': len(runs), 'lines': len(rows), 'intents': len(intents),
               'repetitions': 2, 'threshold': 0.5,
               'cost_usd': sum(r['cost_usd'] for r in runs),
               'latency_seconds': {name: function(r['latency_seconds'] for r in runs)
                                   for name, function in [('mean', statistics.mean), ('median', statistics.median), ('min', min), ('max', max)]}}
    for method in ['semantic', 'lexical']:
        tp, fp, fn = (sum(r[method][field] for r in runs) for field in ['tp', 'fp', 'fn'])
        summary[method] = {'tp': tp, 'fp': fp, 'fn': fn,
                           'precision': tp / (tp + fp) if tp + fp else 0,
                           'recall': tp / (tp + fn) if tp + fn else 0}
    summary['repeat_max_probability_delta'] = max(
        abs(a - b) for i in range(len(intents))
        for a, b in zip(runs[i]['probabilities'], runs[i + len(intents)]['probabilities']))
    (out / 'benchmark.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf8')
    return summary


def main():
    import argparse
    import os
    import sys
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--send', action='store_true', help='authorize six paid synthetic OpenRouter requests')
    mode.add_argument('--dry-run', action='store_true', help='offline experiment description (also the default)')
    parser.add_argument('--output', type=Path, help='new directory for aggregate results')
    args = parser.parse_args()
    try:
        if not args.send:
            print(json.dumps({'mode': 'dry-run', 'requests': 6, 'lines': 20,
                              'intents': 3, 'repetitions': 2, 'threshold': 0.5}))
        else:
            key = os.environ.get('JEV_SEARCH_API_KEY', '')
            if not key or args.output is None:
                raise ValueError('--send requires JEV_SEARCH_API_KEY and --output NEW_DIRECTORY')
            print(json.dumps(run(key, output=args.output), allow_nan=False))
        return 0
    except (ValueError, OSError) as error:
        print(json.dumps({'error': str(error)}), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
