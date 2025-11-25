#!/usr/bin/env python3
"""
Comprehensive validation script for the API migration project
Runs all tests and generates validation report
"""

import subprocess
import sys
import os
import json
import time
from pathlib import Path
from typing import Dict, Any, List, Tuple

class ProjectValidator:
    def __init__(self):
        self.workspace = Path('c:\\workSpace')
        self.results = {
            'project_a': {
                'status': 'pending',
                'tests_run': 0,
                'tests_passed': 0,
                'tests_failed': 0,
                'error': None,
                'duration_sec': 0
            },
            'project_b': {
                'status': 'pending',
                'tests_run': 0,
                'tests_passed': 0,
                'tests_failed': 0,
                'error': None,
                'duration_sec': 0
            },
            'overall_status': 'pending',
            'timestamp': None
        }
    
    def print_header(self, title: str):
        print("\n" + "=" * 80)
        print(f" {title}")
        print("=" * 80)
    
    def print_status(self, message: str, status: str = "INFO"):
        symbol = {
            'OK': '[OK]',
            'PASS': '[PASS]',
            'FAIL': '[FAIL]',
            'INFO': '[...]',
            'WARN': '[!]',
            'ERROR': '[ERROR]'
        }.get(status, '[?]')
        print(f"{symbol} {message}")
    
    def check_files_exist(self) -> bool:
        self.print_header("STEP 1: Verifying Project Structure")
        
        required_files = {
            'Project A': [
                'Project_A_PreChange/src/cart_service_v1.py',
                'Project_A_PreChange/mocks/mock_api_v1.py',
                'Project_A_PreChange/tests/test_pre_change.py',
                'Project_A_PreChange/requirements.txt',
            ],
            'Project B': [
                'Project_B_PostChange/src/cart_service_v2.py',
                'Project_B_PostChange/mocks/mock_api_v2.py',
                'Project_B_PostChange/tests/test_post_change.py',
                'Project_B_PostChange/requirements.txt',
            ],
            'Shared': [
                'test_data.json',
                'run_all.sh',
            ]
        }
        
        all_exist = True
        for category, files in required_files.items():
            for file in files:
                path = self.workspace / file
                if path.exists():
                    self.print_status(f"{category}: {file}", "OK")
                else:
                    self.print_status(f"{category}: {file} - NOT FOUND", "FAIL")
                    all_exist = False
        
        return all_exist
    
    def run_project_a_tests(self) -> Tuple[bool, str]:
        self.print_header("STEP 2: Running Project A Tests (v1 API)")
        
        start_time = time.time()
        
        try:
            os.chdir(self.workspace / 'Project_A_PreChange')
            
            # Run tests with minimal output
            cmd = [
                sys.executable, '-m', 'pytest',
                'tests/test_pre_change.py',
                '-v', '--tb=line',
                '--color=no',
                '-q'
            ]
            
            self.print_status("Executing tests...", "INFO")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            duration = time.time() - start_time
            self.results['project_a']['duration_sec'] = round(duration, 2)
            
            # Parse output
            output = result.stdout + result.stderr
            
            # Count test results
            passed = output.count(' PASSED')
            failed = output.count(' FAILED')
            
            self.results['project_a']['tests_run'] = passed + failed
            self.results['project_a']['tests_passed'] = passed
            self.results['project_a']['tests_failed'] = failed
            
            if result.returncode == 0:
                self.results['project_a']['status'] = 'passed'
                self.print_status(f"Project A: {passed} tests passed in {duration:.2f}s", "PASS")
                return True, output
            else:
                self.results['project_a']['status'] = 'failed'
                self.print_status(f"Project A: {failed} tests failed in {duration:.2f}s", "FAIL")
                self.results['project_a']['error'] = output[-500:] if len(output) > 500 else output
                return False, output
        
        except subprocess.TimeoutExpired:
            self.results['project_a']['status'] = 'timeout'
            self.print_status("Project A tests timed out (60s)", "ERROR")
            return False, "Tests timed out"
        except Exception as e:
            self.results['project_a']['status'] = 'error'
            self.results['project_a']['error'] = str(e)
            self.print_status(f"Project A error: {e}", "ERROR")
            return False, str(e)
    
    def run_project_b_tests(self) -> Tuple[bool, str]:
        self.print_header("STEP 3: Running Project B Tests (v2 API)")
        
        start_time = time.time()
        
        try:
            os.chdir(self.workspace / 'Project_B_PostChange')
            
            # Run tests with minimal output
            cmd = [
                sys.executable, '-m', 'pytest',
                'tests/test_post_change.py',
                '-v', '--tb=line',
                '--color=no',
                '-q'
            ]
            
            self.print_status("Executing tests...", "INFO")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            duration = time.time() - start_time
            self.results['project_b']['duration_sec'] = round(duration, 2)
            
            # Parse output
            output = result.stdout + result.stderr
            
            # Count test results
            passed = output.count(' PASSED')
            failed = output.count(' FAILED')
            
            self.results['project_b']['tests_run'] = passed + failed
            self.results['project_b']['tests_passed'] = passed
            self.results['project_b']['tests_failed'] = failed
            
            if result.returncode == 0:
                self.results['project_b']['status'] = 'passed'
                self.print_status(f"Project B: {passed} tests passed in {duration:.2f}s", "PASS")
                return True, output
            else:
                self.results['project_b']['status'] = 'failed'
                self.print_status(f"Project B: {failed} tests failed in {duration:.2f}s", "FAIL")
                self.results['project_b']['error'] = output[-500:] if len(output) > 500 else output
                return False, output
        
        except subprocess.TimeoutExpired:
            self.results['project_b']['status'] = 'timeout'
            self.print_status("Project B tests timed out (60s)", "ERROR")
            return False, "Tests timed out"
        except Exception as e:
            self.results['project_b']['status'] = 'error'
            self.results['project_b']['error'] = str(e)
            self.print_status(f"Project B error: {e}", "ERROR")
            return False, str(e)
    
    def verify_test_data(self) -> bool:
        self.print_header("STEP 4: Verifying Test Data")
        
        try:
            with open(self.workspace / 'test_data.json') as f:
                data = json.load(f)
            
            test_cases = data.get('test_cases', [])
            self.print_status(f"Test cases loaded: {len(test_cases)}", "OK")
            
            for tc in test_cases:
                tc_id = tc.get('id', 'unknown')
                category = tc.get('category', 'unknown')
                self.print_status(f"  {tc_id}: {category}", "OK")
            
            return True
        except Exception as e:
            self.print_status(f"Error loading test data: {e}", "ERROR")
            return False
    
    def generate_report(self, output_a: str = "", output_b: str = "") -> Dict[str, Any]:
        self.print_header("VALIDATION REPORT")
        
        # Determine overall status
        if (self.results['project_a']['status'] == 'passed' and 
            self.results['project_b']['status'] == 'passed'):
            self.results['overall_status'] = 'passed'
        else:
            self.results['overall_status'] = 'failed'
        
        # Print summary
        print()
        print("PROJECT A (v1 API):")
        print(f"  Status: {self.results['project_a']['status'].upper()}")
        print(f"  Tests: {self.results['project_a']['tests_passed']}/{self.results['project_a']['tests_run']} passed")
        print(f"  Duration: {self.results['project_a']['duration_sec']}s")
        
        print()
        print("PROJECT B (v2 API):")
        print(f"  Status: {self.results['project_b']['status'].upper()}")
        print(f"  Tests: {self.results['project_b']['tests_passed']}/{self.results['project_b']['tests_run']} passed")
        print(f"  Duration: {self.results['project_b']['duration_sec']}s")
        
        print()
        print("OVERALL RESULT:")
        print(f"  Status: {self.results['overall_status'].upper()}")
        
        # Final status
        print()
        print("=" * 80)
        if self.results['overall_status'] == 'passed':
            print("SUCCESS: All tests passed!")
        else:
            print("FAILURE: Some tests did not pass")
            if self.results['project_a']['error']:
                print(f"\nProject A Error: {self.results['project_a']['error']}")
            if self.results['project_b']['error']:
                print(f"\nProject B Error: {self.results['project_b']['error']}")
        print("=" * 80)
        
        return self.results
    
    def run_full_validation(self):
        """Run complete validation"""
        print("\n" + "#" * 80)
        print("# API MIGRATION PROJECT - FULL VALIDATION")
        print("#" * 80)
        
        os.chdir(self.workspace)
        
        # Step 1: Check files
        if not self.check_files_exist():
            self.print_status("File check failed", "FAIL")
            return False
        
        # Step 2: Verify test data
        if not self.verify_test_data():
            self.print_status("Test data verification failed", "FAIL")
            return False
        
        # Step 3: Run Project A tests
        output_a = ""
        success_a = False
        try:
            success_a, output_a = self.run_project_a_tests()
        except Exception as e:
            self.print_status(f"Exception in Project A: {e}", "ERROR")
        
        # Step 4: Run Project B tests
        output_b = ""
        success_b = False
        try:
            success_b, output_b = self.run_project_b_tests()
        except Exception as e:
            self.print_status(f"Exception in Project B: {e}", "ERROR")
        
        # Step 5: Generate report
        results = self.generate_report(output_a, output_b)
        
        return success_a and success_b


def main():
    validator = ProjectValidator()
    success = validator.run_full_validation()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
