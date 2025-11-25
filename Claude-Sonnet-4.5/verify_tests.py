import json

# Load results
with open('results/results_post.json', 'r') as f:
    data = json.load(f)

# Find TC003 (Async test)
tc3 = [t for t in data['test_results'] if t['test_id']=='TC003'][0]
print('TC003 Async Test:')
print(f'  Passed: {tc3["passed"]}')
print(f'  Requires Polling: {tc3["result"].get("requiresPolling", False)}')
print(f'  Status: {tc3["result"].get("availabilityStatus", "N/A")}')

# Find TC004 (Fallback test)
tc4 = [t for t in data['test_results'] if t['test_id']=='TC004'][0]
print('\nTC004 Fallback Test:')
print(f'  Passed: {tc4["passed"]}')
print(f'  Fallback: {tc4["result"].get("fallback", False)}')
print(f'  API Version: {tc4["result"].get("api_version", "N/A")}')

# Find TC005 (Error/Retry test)
tc5 = [t for t in data['test_results'] if t['test_id']=='TC005'][0]
print('\nTC005 Error/Retry Test:')
print(f'  Passed: {tc5["passed"]}')
print(f'  Fallback: {tc5["result"].get("fallback", False)}')
print(f'  Retryable: {tc5["result"].get("retryable", False)}')
