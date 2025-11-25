import json
import sys
from statistics import median

def p50(values):
    if not values: return None
    return median(values)

def summarize(results):
    latencies = [r.get('elapsed',0) for r in results]
    errors = sum(1 for r in results if r.get('status')!='ok')
    passed = sum(1 for r in results if r.get('passed'))
    total = len(results)
    return {'total': total, 'passed': passed, 'errors': errors, 'p50': p50(latencies), 'p95': (sorted(latencies)[int(len(latencies)*0.95)] if latencies else None)}

def main(pre_path, post_path):
    pre = json.load(open(pre_path))
    post = json.load(open(post_path))
    s_pre = summarize(pre)
    s_post = summarize(post)
    print('# Compare Report')
    print('')
    print('## Summary Metrics')
    print('')
    print('|metric|pre|post|')
    print('|---|---:|---:|')
    for k in ['total','passed','errors','p50','p95']:
        print(f'|{k}|{s_pre.get(k)}|{s_post.get(k)}|')
    print('')
    print('## Case-level diffs')
    for pr,po in zip(pre, post):
        print(f"- {pr['case']}: pre_passed={pr['passed']} post_passed={po['passed']} pre_status={pr['status']} post_status={po['status']}")

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print('usage: generate_report.py pre.json post.json', file=sys.stderr)
        sys.exit(2)
    main(sys.argv[1], sys.argv[2])
