import json
import statistics
import sys

def load(file):
    with open(file) as f:
        return json.load(f)


def compute_metrics(results):
    latencies = sorted([r['latency'] for r in results if isinstance(r.get('latency'), (int, float))])
    counts = len(results)
    errors = sum(1 for r in results if r['status'] == 'error' or (isinstance(r['status'], int) and r['status'] >= 500))
    fallback = sum(1 for r in results if isinstance(r.get('body'), dict) and r.get('body', {}).get('note','').startswith('v1'))
    passes = sum(1 for r in results if r.get('pass'))
    metrics = {
        'count': counts,
        'errors': errors,
        'fallbacks': fallback,
        'passes': passes,
        'latency_p50': statistics.median(latencies) if latencies else None,
        'latency_p95': (latencies[int(len(latencies)*0.95)-1] if len(latencies) else None)
    }
    return metrics

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('Usage: aggregate_metrics.py results_pre.json results_post.json')
        sys.exit(2)
    pre = load(sys.argv[1])
    post = load(sys.argv[2])
    m_pre = compute_metrics(pre)
    m_post = compute_metrics(post)
    out = {'pre': m_pre, 'post': m_post}
    print(json.dumps(out, indent=2))
    with open('results/aggregated_metrics.json', 'w') as f:
        json.dump(out, f, indent=2)
