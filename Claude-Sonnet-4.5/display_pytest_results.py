"""Display pytest test results summary"""
import json

print("\n" + "="*60)
print("PYTEST CONVERSION COMPLETE")
print("="*60)

# Project A
with open('Project_A_PreChange/results/results_pre.json', 'r') as f:
    data_a = json.load(f)

print("\nProject A (Pre-Change - v1 API):")
print(f"  Total Tests:    {data_a['total_tests']}")
print(f"  Passed:         {data_a['passed']}")
print(f"  Failed:         {data_a['failed']}")
print(f"  Pass Rate:      {data_a['pass_rate']}%")
print(f"  Avg Latency:    {data_a['latency_stats']['avg_ms']:.2f}ms")
print(f"  P95 Latency:    {data_a['latency_stats']['p95_ms']:.2f}ms")

# Project B
with open('Project_B_PostChange/results/results_post.json', 'r') as f:
    data_b = json.load(f)

print("\nProject B (Post-Change - v2 API):")
print(f"  Total Tests:    {data_b['total_tests']}")
print(f"  Passed:         {data_b['passed']}")
print(f"  Failed:         {data_b['failed']}")
print(f"  Pass Rate:      {data_b['pass_rate']}%")
print(f"  Avg Latency:    {data_b['latency_stats']['avg_ms']:.2f}ms")
print(f"  P95 Latency:    {data_b['latency_stats']['p95_ms']:.2f}ms")
print(f"\n  Adapter Stats:")
print(f"    Fallbacks:    {data_b['adapter_stats']['fallback_count']}")
print(f"    Retries:      {data_b['adapter_stats']['retry_count']}")
print(f"    Async Cases:  {data_b['adapter_stats']['async_cases']}")
print(f"    Circuit:      {data_b['adapter_stats']['circuit_breaker_state']}")

print("\n" + "="*60)
print("Key Improvements with pytest:")
print("="*60)
print("  ✓ Parametrized tests for cleaner test code")
print("  ✓ Fixture-based setup for better reusability")
print("  ✓ Better test discovery and reporting")
print("  ✓ JSON report generation with pytest-json-report")
print("  ✓ More readable assertions and error messages")
print("="*60 + "\n")
