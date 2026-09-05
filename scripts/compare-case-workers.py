#!/usr/bin/env python3
"""Evaluate two preserved workers with one coordinator and prepare a bound review.

The plan must already exist. This command never grants review approval.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parent.parent


def read(path):
    return json.loads(path.read_text())


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()


def write(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--coordinator', type=Path, required=True)
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--plan', type=Path, required=True)
    parser.add_argument('--case-dir', type=Path, default=ROOT / 'cases/cards')
    parser.add_argument('--corpus', type=Path, default=ROOT / 'cases/corpus/corpus.json')
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=False)
    plan = read(args.plan)
    write(output / 'plan.json', plan)
    coordinator = str(args.coordinator.resolve())
    campaigns = {}
    for name, worker in [('baseline', args.baseline), ('candidate', args.candidate)]:
        command = [coordinator, 'case', 'campaign', '--case-dir', str(args.case_dir.resolve()),
                   '--corpus', str(args.corpus.resolve()), '--worker', str(worker.resolve()),
                   '--output-dir', str(output / name)]
        with (output / f'{name}.log').open('x') as log:
            completed = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)
        # A nonzero campaign exit can mean retained violations; absent artifacts are a setup failure.
        receipts = read(output / name / 'campaign.json')
        campaigns[name] = {receipt['case_id']: receipt for receipt in receipts}
        for receipt in receipts:
            subprocess.run([coordinator, 'case', 'verify', '--receipt',
                            str(output / name / receipt['case_id'] / 'receipt.json')],
                           check=True, stdout=subprocess.DEVNULL)
        print(f'{name}: {len(receipts)} cases; exit {completed.returncode}', flush=True)
    target = plan['case_id']
    baseline, candidate = campaigns['baseline'][target], campaigns['candidate'][target]
    rows = [{'case_id': case_id, 'title': read(output / 'candidate' / case_id / 'case.json')['title'],
             'baseline': campaigns['baseline'][case_id]['result'], 'candidate': receipt['result']}
            for case_id, receipt in campaigns['candidate'].items()]
    write(output / 'comparison.json', {'plan_id': digest(plan), 'cases': rows})
    write(output / 'review-template.json', {
        'plan_id': digest(plan), 'baseline_receipt_id': digest(baseline),
        'candidate_receipt_id': digest(candidate), 'reviewer': '', 'rationale': '', 'decision': 'reject'})
    command = [coordinator, 'case', 'accept', '--case', str(output / 'baseline' / target / 'case.json'),
               '--plan', str(output / 'plan.json'), '--baseline', str(output / 'baseline' / target / 'receipt.json'),
               '--candidate', str(output / 'candidate' / target / 'receipt.json')]
    for case_id in plan['regression_case_ids'] + plan['holdout_case_ids']:
        command += ['--gate', str(output / 'candidate' / case_id / 'receipt.json')]
    command += ['--review', str(output / 'review-approved.json'),
                '--baseline-build', str(args.baseline.resolve().parent),
                '--candidate-build', str(args.candidate.resolve().parent),
                '--output-dir', str(output / 'accepted')]
    write(output / 'accept-command.json', command)
    print(f'Comparison and review template: {output}')
    passed = all(receipt['result']['kind'] == 'satisfied' and receipt['repeatability'] == 'verified'
                 for receipt in campaigns['candidate'].values())
    raise SystemExit(0 if passed and baseline['result']['kind'] == 'violated' else 1)


if __name__ == '__main__':
    main()
