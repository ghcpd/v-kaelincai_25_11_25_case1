# API Change Comparison Report

## Summary

- Pre pass rate: **1.0**
- Post pass rate: **1.0**
- Fallbacks (post): **2**

## Latency (ms)

| Metric | Pre | Post | Delta (Pre-Post) |
|--------|-----|------|------------------|
| p50 | 8.633250021375716 | 2.614200027892366 | 6.01904999348335 |
| p95 | 24.079900002107024 | 870.1245299656875 | -846.0446299635805 |
| min | 0 | 0 | 0 |
| max | 20.303400000557303 | 528.8106999942102 | -508.50729999365285 |

## Per-Case Comparison

| ID | Pre Pass | Post Pass | Pre Avail | Post Avail | Pre Latency | Post Latency | Δ ms |
|----|----------|-----------|-----------|------------|-------------|--------------|------|
| TC1 | True | True | {'available': True, 'quantity': 12, 'note': 'legacy-confirmed'} | {'available': True, 'quantity': 12, 'note': 'confirmed'} | 20.3 | 2.47 | 17.83 |
| TC2 | True | True | {'available': True, 'quantity': 2, 'note': 'legacy-threshold-met'} | {'available': True, 'quantity': 2, 'note': 'confirmed'} | 13.59 | 2.76 | 10.83 |
| TC3 | True | True | {'available': False, 'quantity': 0, 'note': 'legacy-no-region'} | {'available': True, 'quantity': 5, 'note': 'confirmed-after-poll'} | 3.68 | 528.81 | -525.14 |
| TC4 | True | True | {'available': True, 'quantity': 7, 'note': 'legacy-ignores-region'} | {'available': False, 'quantity': 0, 'note': 'invalid-input'} | 2.67 | 0 | 2.67 |
| TC5 | True | True | {'available': False, 'quantity': 0, 'note': 'legacy-error'} | {'available': True, 'quantity': 3, 'note': 'fallback-to-v1'} | 14.49 | 3.71 | 10.78 |
| TC6 | True | True | {'available': False, 'quantity': 0, 'note': 'legacy-validation-error'} | {'available': False, 'quantity': 0, 'note': 'invalid-input'} | 0 | 0 | 0 |

## Observations
- Pending handling and polling are exercised in TC3; post-change succeeds with `confirmed-after-poll`.
- Invalid input (TC4) is explicitly rejected; fallback flag is set to signal degradation path.
- ERR500 (TC5) falls back to v1 and returns availability from legacy.

## Rollout Recommendations
- Use a feature flag to gate v2, with automatic fallback to v1 on errors/timeouts.
- Monitor latency and fallback rates; alert if fallback >1%.
- Gradual traffic shift (canary) and compare metrics using this harness.
- Add circuit breakers and exponential backoff for v2 polling in production.