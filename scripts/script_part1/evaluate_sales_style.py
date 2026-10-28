"""Compare two actual offline Part 1 runs without inferring missing intent."""
import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--before', required=True, type=Path, help='Before run step1_agent_audio directory')
    parser.add_argument('--after', required=True, type=Path, help='After run step1_agent_audio directory')
    parser.add_argument('--output', required=True, type=Path, help='New JSON report path; never overwrites')
    args = parser.parse_args()
    def load(directory, name):
        return json.loads((directory / name).read_text(encoding='utf-8'))
    before, after = load(args.before, 'evaluation.json'), load(args.after, 'evaluation.json')
    old = {a['comment_id']: a for a in load(args.before, 'answers.json')}
    new = {a['comment_id']: a for a in load(args.after, 'answers.json')}
    first = {r['comment_id']: r for r in before['rows']}
    second = {r['comment_id']: r for r in after['rows']}
    if set(first) != set(second):
        raise ValueError('Runs do not contain the same comment IDs')
    if any((first[cid]['text'], first[cid]['viewer_id']) != (second[cid]['text'], second[cid]['viewer_id']) for cid in first):
        raise ValueError('Runs do not contain the same comments and viewers')
    rows = []
    for cid in first:
        a, b = old.get(cid), new.get(cid)
        old_text, new_text = (a or {}).get('answer_text'), (b or {}).get('answer_text')
        rows.append({'comment_id': cid, 'intent': None, 'intent_note': 'Not recorded in run artifacts',
            'decision_before': first[cid]['decision_action'], 'decision_after': second[cid]['decision_action'],
            'status_before': (a or {}).get('status'), 'status_after': (b or {}).get('status'),
            'resolved_sku_before': (a or {}).get('resolved_sku_id'), 'resolved_sku_after': (b or {}).get('resolved_sku_id'),
            'old_answer': old_text, 'new_answer': new_text,
            'old_word_count': len(old_text.split()) if old_text else 0,
            'new_word_count': len(new_text.split()) if new_text else 0,
            'verification_result': 'passed in agent' if b and b['status'] == 'answered' else 'not applicable',
            'evidence_refs': (b or {}).get('evidence_refs', [])})
    with args.output.open('x', encoding='utf-8') as stream:
        json.dump({'before_run_id': before['run_id'], 'after_run_id': after['run_id'], 'rows': rows},
                  stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(f'Compared {len(rows)} comments; report: {args.output}')


if __name__ == '__main__':
    main()
