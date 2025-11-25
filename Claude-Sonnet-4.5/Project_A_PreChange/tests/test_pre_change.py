"""
Test harness for Project A (Pre-Change)
Tests legacy v1 API integration
"""
import json
import sys
import os
import time
import unittest
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from cart_service_v1 import CartServiceV1


class TestPreChange(unittest.TestCase):
    """Test suite for v1 API integration"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures"""
        cls.service = CartServiceV1(api_base_url="http://localhost:5001")
        
        # Load test data
        test_data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'test_data.json')
        with open(test_data_path, 'r') as f:
            cls.test_data = json.load(f)
        
        cls.results = []
        cls.start_time = time.time()
        
    def run_test_case(self, test_case):
        """Execute a single test case"""
        test_id = test_case['test_id']
        test_name = test_case['name']
        input_data = test_case['input']
        expected_v1 = test_case['expected_v1_response']
        expected_outcome = test_case['expected_outcome']
        
        print(f"\n{'='*60}")
        print(f"Running: {test_id} - {test_name}")
        print(f"{'='*60}")
        
        # Execute API call
        result = self.service.check_availability(
            sku=input_data['sku'],
            quantity=input_data.get('quantity', 1)
        )
        
        print(f"Result: {json.dumps(result, indent=2)}")
        
        # Validate result
        passed = True
        errors = []
        
        # Check HTTP status
        expected_status = test_case.get('expected_status', 200)
        if result['status_code'] != expected_status:
            passed = False
            errors.append(f"Status mismatch: expected {expected_status}, got {result['status_code']}")
        
        # For successful cases, validate data
        if expected_status == 200:
            if 'error' not in expected_v1:
                # Validate availability matches expected
                expected_available = expected_outcome.get('available', False)
                if result['available'] != expected_available:
                    passed = False
                    errors.append(f"Availability mismatch: expected {expected_available}, got {result['available']}")
                
                # Validate quantity
                expected_qty = expected_outcome.get('quantity', 0)
                if result['quantity'] != expected_qty:
                    passed = False
                    errors.append(f"Quantity mismatch: expected {expected_qty}, got {result['quantity']}")
        
        # Record result
        test_result = {
            "test_id": test_id,
            "test_name": test_name,
            "passed": passed,
            "errors": errors,
            "result": result,
            "expected": expected_outcome,
            "latency_ms": result.get('latency_ms', 0)
        }
        
        self.results.append(test_result)
        
        if passed:
            print(f"[PASSED]")
        else:
            print(f"[FAILED]")
            for error in errors:
                print(f"  - {error}")
        
        return passed
    
    def test_all_cases(self):
        """Run all test cases"""
        for test_case in self.test_data:
            self.run_test_case(test_case)
    
    @classmethod
    def tearDownClass(cls):
        """Save results and generate report"""
        elapsed = time.time() - cls.start_time
        
        # Calculate statistics
        total_tests = len(cls.results)
        passed_tests = sum(1 for r in cls.results if r['passed'])
        failed_tests = total_tests - passed_tests
        
        latencies = [r['latency_ms'] for r in cls.results]
        latencies.sort()
        
        p50 = latencies[len(latencies)//2] if latencies else 0
        p95 = latencies[int(len(latencies)*0.95)] if latencies else 0
        p99 = latencies[int(len(latencies)*0.99)] if latencies else 0
        avg_latency = sum(latencies) / len(latencies) if latencies else 0
        
        # Build summary
        summary = {
            "project": "Project_A_PreChange",
            "api_version": "v1",
            "timestamp": datetime.now().isoformat(),
            "execution_time_seconds": round(elapsed, 2),
            "total_tests": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "pass_rate": round(passed_tests / total_tests * 100, 2) if total_tests > 0 else 0,
            "latency_stats": {
                "avg_ms": round(avg_latency, 2),
                "p50_ms": round(p50, 2),
                "p95_ms": round(p95, 2),
                "p99_ms": round(p99, 2),
                "min_ms": round(min(latencies), 2) if latencies else 0,
                "max_ms": round(max(latencies), 2) if latencies else 0
            },
            "test_results": cls.results
        }
        
        # Save to file
        results_dir = os.path.join(os.path.dirname(__file__), '..', 'results')
        os.makedirs(results_dir, exist_ok=True)
        
        results_path = os.path.join(results_dir, 'results_pre.json')
        with open(results_path, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"\n{'='*60}")
        print(f"TEST SUMMARY - Project A (Pre-Change)")
        print(f"{'='*60}")
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Pass Rate: {summary['pass_rate']}%")
        print(f"Avg Latency: {avg_latency:.2f}ms")
        print(f"P95 Latency: {p95:.2f}ms")
        print(f"Execution Time: {elapsed:.2f}s")
        print(f"\nResults saved to: {results_path}")


def main():
    """Run tests"""
    # Run unittest suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestPreChange)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)


if __name__ == '__main__':
    main()
