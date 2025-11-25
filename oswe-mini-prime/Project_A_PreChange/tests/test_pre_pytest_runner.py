import json
import importlib.util
import os


def _load_harness(module_name: str, relpath: str):
    path = os.path.join(os.path.dirname(__file__), relpath)
    spec = importlib.util.spec_from_file_location(module_name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_pre_change_harness():
    """Runs the pre-change harness and fails the pytest run if any case fails."""
    # Ensure expected test-case count
    import json as _json, os as _os
    with open(_os.path.join(_os.path.dirname(__file__), '..', 'data', 'test_data.json')) as f:
        cases = _json.load(f)
    assert len(cases) == 5, f'Expected 5 test cases in data/test_data.json, found {len(cases)}'

    # Ensure ports are free before running harness: 5000 (service), 5001 (v1)
    import subprocess as _subp
    for _port in (5000, 5001):
        try:
            out = _subp.check_output(['netstat', '-ano']).decode('utf-8')
            for _line in out.splitlines():
                if f':{_port}' in _line and 'LISTENING' in _line:
                    _pid = int(_line.strip().split()[-1])
                    try:
                        import signal
                        _subp.check_call(['taskkill', '/PID', str(_pid), '/F'])
                    except Exception:
                        pass
        except Exception:
            pass

    mod = _load_harness('pre_test_pre_change', 'test_pre_change.py')
    results = mod.run_tests()
    # Persist results for debugging
    with open('results/results_pre.json', 'w') as f:
        json.dump(results, f, indent=2)
    failures = [r for r in results if not r.get('pass')]
    assert not failures, f"Pre-change harness had failing cases: {failures}"
