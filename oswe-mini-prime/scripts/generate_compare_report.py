import json
import sys

if __name__ == '__main__':
    if len(sys.argv) != 4:
        print('Usage: generate_compare_report.py results_pre.json results_post.json aggregated_metrics.json')
        sys.exit(2)
    pre = json.load(open(sys.argv[1]))
    post = json.load(open(sys.argv[2]))
    agg = json.load(open(sys.argv[3]))

    def status_ok(r):
        return r.get('status') == 200

    correct_pre = sum(1 for r in pre if status_ok(r))
    correct_post = sum(1 for r in post if status_ok(r))

    lines = []
    lines.append('# Compare Report: Pre-change vs Post-change')
    lines.append('')
    lines.append('## Summary')
    lines.append('')
    lines.append(f'- Pre-change success count: {correct_pre}/{len(pre)}')
    lines.append(f'- Post-change success count: {correct_post}/{len(post)}')
    lines.append('')
    lines.append('## Metrics')
    lines.append('')
    lines.append('Aggregated metrics:')
    lines.append('')
    lines.append('```json')
    lines.append(json.dumps(agg, indent=2))
    lines.append('```')
    lines.append('')
    lines.append('## Case details')
    lines.append('')
    lines.append('| id | pre.status | pre.body | post.status | post.body |')
    lines.append('|---|---:|---|---:|---|')
    for p, q in zip(pre, post):
        lines.append(f"| {p['id']} | {p['status']} | `{p.get('body')}` | {q['status']} | `{q.get('body')}` |")

    lines.append('')
    lines.append('## Observations')
    lines.append('')
    lines.append('- Post-change implemented region/warehouse-aware call and polling for async v2 responses.')
    lines.append('- Fallback behavior uses v1 to preserve availability decisions where v2 fails or times out.')
    lines.append('- A real rollout should add feature flags, canary traffic, and tracing for correlation IDs.')
    lines.append('')
    # compute improvements based on aggregated metrics
    try:
        pre_metrics = agg['pre']
        post_metrics = agg['post']
        lines.append('## Comparative Metrics')
        lines.append('')
        lines.append(f"- Pre-change passes: {pre_metrics.get('passes')} / {pre_metrics.get('count')}\n- Post-change passes: {post_metrics.get('passes')} / {post_metrics.get('count')}")
        lines.append(f"- Pre-change p50 latency: {pre_metrics.get('latency_p50')}s  | Post-change p50: {post_metrics.get('latency_p50')}s")
        lines.append(f"- Pre-change p95 latency: {pre_metrics.get('latency_p95')}s  | Post-change p95: {post_metrics.get('latency_p95')}s")
        lines.append(f"- Pre-change fallbacks: {pre_metrics.get('fallbacks')} | Post-change fallbacks: {post_metrics.get('fallbacks')}")
    except Exception:
        pass

    print('\n'.join(lines))
