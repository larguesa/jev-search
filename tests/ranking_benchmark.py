"""Frozen public synthetic ranking study; source-only, offline unless --send."""
import math
import statistics
import hashlib
import json
from pathlib import Path


FIXTURE = Path(__file__).parent / 'fixtures/ranking.json'


def main():
    import argparse
    import sys
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--dry-run', action='store_true')
    mode.add_argument('--send', action='store_true', help='run six paid synthetic requests; no retries')
    parser.add_argument('--output', type=Path, help='new private evidence directory')
    args = parser.parse_args()
    try:
        if args.send:
            if args.output is None:
                raise ValueError('--send requires --output NEW_DIRECTORY')
            print(json.dumps(run(args.output)['summary'], allow_nan=False))
        else:
            raw = FIXTURE.read_bytes()
            print(json.dumps({'mode': 'dry-run', 'fixture_sha256': hashlib.sha256(raw).hexdigest(),
                              'design': json.loads(raw)['design']}))
        return 0
    except (ValueError, OSError) as error:
        print(json.dumps({'error': str(error)}), file=sys.stderr)
        return 1


def run(output):
    import subprocess
    import sys
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=False, mode=0o700)
    raw_fixture = FIXTURE.read_bytes()
    (output / 'frozen.json').write_bytes(raw_fixture)
    fixture = json.loads(raw_fixture)
    design = fixture['design']
    runs = []
    for task in fixture['tasks']:
        path = output / (task['id'] + '.txt')
        path.write_text('\n'.join(c['text'] for c in task['candidates']) + '\n', encoding='utf8')
        command = [sys.executable, '-m', 'jev_search', '--provider', design['provider'],
                   '--model', design['model'], '--top-k', str(design['k']), '--query', task['query'], str(path)]
        result = subprocess.run(command, capture_output=True, text=True, cwd=FIXTURE.resolve().parents[2])
        (output / (task['id'] + '.stdout.json')).write_text(result.stdout, encoding='utf8')
        (output / (task['id'] + '.stderr.json')).write_text(result.stderr, encoding='utf8')
        (output / 'status.json').write_text(json.dumps({'complete': False, 'attempts': len(runs) + 1,
            'task': task['id'], 'exit_code': result.returncode}), encoding='utf8')
        if result.returncode:
            raise ValueError('study incomplete; failed invocation preserved; no retries')
        data = json.loads(result.stdout)
        baseline = [r['line'] - 1 for r in data['results'] if r['match']][:design['k']]
        ranked = [r['line'] - 1 for r in data['ranked_results']]
        response = data['raw_response']
        grades = [c['grade'] for c in task['candidates']]
        # Public allowlist: native scores/usage retained; generation IDs and local paths stay private.
        runs.append({'task': task['id'], 'latency_seconds': data['latency_seconds'],
                     'cost_usd': response['usage']['cost'],
                     'provider_response': {'model': response['model'],
                         'answers': {name: {field: answer[field] for field in ['type', 'noul']}
                                     for name, answer in response['answers'].items()},
                         'usage': {field: response['usage'][field] for field in ['cost', 'input_tokens', 'output_tokens']}},
                     'selected': {'baseline': baseline, 'ranked': ranked},
                     'baseline': metrics(baseline, grades, design['k']),
                     'ranked': metrics(ranked, grades, design['k'])})
    evidence = {'experiment': fixture['experiment'], 'fixture_sha256': hashlib.sha256(raw_fixture).hexdigest(),
                'comparison': design['comparison'], 'runs': runs, 'summary': summarize(runs)}
    (output / 'public-results.json').write_text(json.dumps(evidence, indent=2, allow_nan=False) + '\n', encoding='utf8')
    (output / 'status.json').write_text(json.dumps({'complete': True, 'attempts': len(runs)}), encoding='utf8')
    return evidence


def summarize(runs):
    summary = {'requests': len(runs), 'cost_usd': sum(r['cost_usd'] for r in runs),
               'latency_seconds': {name: function(r['latency_seconds'] for r in runs)
                   for name, function in [('mean', statistics.mean), ('median', statistics.median), ('min', min), ('max', max)]}}
    for arm in ['baseline', 'ranked']:
        summary[arm] = {field: statistics.mean(r[arm][field] for r in runs)
                       for field in ['precision_at_k', 'recall', 'ndcg_at_k', 'answer_complete_precision_at_k']}
        summary[arm].update({field: sum(r[arm][field] for r in runs)
                            for field in ['false_sufficient', 'false_insufficient']})
    deltas = [r['ranked']['ndcg_at_k'] - r['baseline']['ndcg_at_k'] for r in runs]
    summary['ndcg_outcomes'] = {'wins': sum(d > 0 for d in deltas),
                                'ties': sum(d == 0 for d in deltas),
                                'losses': sum(d < 0 for d in deltas)}
    baseline, ranked = summary['baseline'], summary['ranked']
    summary['passes_exploratory_gate'] = (ranked['ndcg_at_k'] > baseline['ndcg_at_k']
        and ranked['precision_at_k'] >= baseline['precision_at_k']
        and ranked['false_sufficient'] <= baseline['false_sufficient'])
    return summary


def metrics(selected, grades, k):
    relevant = sum(grade > 0 for grade in grades)
    tp = sum(grades[i] > 0 for i in selected)
    complete = sum(grades[i] == 2 for i in selected)
    dcg = sum((2 ** grades[i] - 1) / math.log2(rank + 2)
              for rank, i in enumerate(selected))
    ideal = sum((2 ** grade - 1) / math.log2(rank + 2)
                for rank, grade in enumerate(sorted(grades, reverse=True)[:k]))
    return {'precision_at_k': tp / k,
            'recall': tp / relevant if relevant else 0,
            'ndcg_at_k': dcg / ideal if ideal else 0,
            'answer_complete_precision_at_k': complete / k,
            'false_sufficient': bool(selected) and not complete,
            'false_insufficient': not selected and 2 in grades}


if __name__ == '__main__':
    raise SystemExit(main())
