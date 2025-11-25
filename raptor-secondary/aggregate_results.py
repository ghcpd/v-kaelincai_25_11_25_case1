import json
import statistics
from pathlib import Path

ROOT = Path(__file__).parent
PRE_PATH = ROOT / "Project_A_PreChange" / "results" / "results_pre.json"
POST_PATH = ROOT / "Project_B_PostChange" / "results" / "results_post.json"
OUT_DIR = ROOT / "results"
OUT_DIR.mkdir(exist_ok=True)
AGG_JSON = OUT_DIR / "aggregated_metrics.json"
REPORT_MD = ROOT / "compare_report.md"


def load_results(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["results"], data.get("metrics", {})


def percentile(values, p):
    if not values:
        return None
    k = (len(values) - 1) * (p / 100)
    f = int(k)
    c = min(f + 1, len(values) - 1)
    if f == c:
        return values[int(k)]
    d0 = values[f] * (c - k)
    d1 = values[c] * (k - f)
    return d0 + d1


def main():
    pre_results, pre_metrics = load_results(PRE_PATH)
    post_results, post_metrics = load_results(POST_PATH)

    # Index by case id for comparison
    pre_by_id = {r["id"]: r for r in pre_results}
    post_by_id = {r["id"]: r for r in post_results}

    comparison = []
    latency_improvements = []
    fallback_changes = []

    for cid, pre in pre_by_id.items():
        post = post_by_id.get(cid)
        if not post:
            continue
        pre_latency = pre.get("actual", {}).get("latency_ms")
        post_latency = post.get("actual", {}).get("latency_ms")
        if pre_latency is not None and post_latency is not None:
            latency_improvements.append(pre_latency - post_latency)
        pre_fallback = bool(pre.get("actual", {}).get("fallback_used"))
        post_fallback = bool(post.get("actual", {}).get("fallback_used"))
        fallback_changes.append((cid, pre_fallback, post_fallback))
        comparison.append({
            "id": cid,
            "pre_passed": pre.get("passed"),
            "post_passed": post.get("passed"),
            "pre_availability": pre.get("actual", {}).get("availability"),
            "post_availability": post.get("actual", {}).get("availability"),
            "pre_latency_ms": pre_latency,
            "post_latency_ms": post_latency,
            "latency_delta_ms": (pre_latency - post_latency) if (pre_latency is not None and post_latency is not None) else None,
        })

    agg = {
        "pre_metrics": pre_metrics,
        "post_metrics": post_metrics,
        "latency_improvement_ms": {
            "p50": percentile(latency_improvements, 50) if latency_improvements else None,
            "p95": percentile(latency_improvements, 95) if latency_improvements else None,
            "avg": statistics.mean(latency_improvements) if latency_improvements else None,
        },
        "comparison": comparison,
    }

    with open(AGG_JSON, "w", encoding="utf-8") as f:
        json.dump(agg, f, indent=2)

    # Generate report markdown
    lines = []
    lines.append("# API Change Comparison Report")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Pre pass rate: **{pre_metrics.get('pass_rate', 'N/A')}**")
    lines.append(f"- Post pass rate: **{post_metrics.get('pass_rate', 'N/A')}**")
    lines.append(f"- Fallbacks (post): **{post_metrics.get('fallback_count', 'N/A')}**")
    lines.append("")
    lines.append("## Latency (ms)")
    lines.append("")
    lines.append("| Metric | Pre | Post | Delta (Pre-Post) |")
    lines.append("|--------|-----|------|------------------|")
    for m in ["p50", "p95", "min", "max"]:
        pre_val = pre_metrics.get("latency_ms", {}).get(m)
        post_val = post_metrics.get("latency_ms", {}).get(m)
        delta = None
        if pre_val is not None and post_val is not None:
            delta = pre_val - post_val
        lines.append(f"| {m} | {pre_val} | {post_val} | {delta} |")
    lines.append("")
    lines.append("## Per-Case Comparison")
    lines.append("")
    lines.append("| ID | Pre Pass | Post Pass | Pre Avail | Post Avail | Pre Latency | Post Latency | Δ ms |")
    lines.append("|----|----------|-----------|-----------|------------|-------------|--------------|------|")
    for c in comparison:
        lines.append(
            "| {id} | {pre_passed} | {post_passed} | {pre_avail} | {post_avail} | {pre_lat} | {post_lat} | {delta} |".format(
                id=c.get("id"),
                pre_passed=c.get("pre_passed"),
                post_passed=c.get("post_passed"),
                pre_avail=c.get("pre_availability"),
                post_avail=c.get("post_availability"),
                pre_lat=round(c.get("pre_latency_ms") or 0, 2) if c.get("pre_latency_ms") is not None else "-",
                post_lat=round(c.get("post_latency_ms") or 0, 2) if c.get("post_latency_ms") is not None else "-",
                delta=round(c.get("latency_delta_ms") or 0, 2) if c.get("latency_delta_ms") is not None else "-",
            )
        )
    lines.append("")

    lines.append("## Observations")
    lines.append("- Pending handling and polling are exercised in TC3; post-change succeeds with `confirmed-after-poll`.")
    lines.append("- Invalid input (TC4) is explicitly rejected; fallback flag is set to signal degradation path.")
    lines.append("- ERR500 (TC5) falls back to v1 and returns availability from legacy.")
    lines.append("")
    lines.append("## Rollout Recommendations")
    lines.append("- Use a feature flag to gate v2, with automatic fallback to v1 on errors/timeouts.")
    lines.append("- Monitor latency and fallback rates; alert if fallback >1%.")
    lines.append("- Gradual traffic shift (canary) and compare metrics using this harness.")
    lines.append("- Add circuit breakers and exponential backoff for v2 polling in production.")

    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
