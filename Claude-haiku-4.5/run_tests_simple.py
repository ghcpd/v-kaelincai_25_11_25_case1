#!/usr/bin/env python3
"""
Simple test runner without excessive output
"""

import subprocess
import sys
import os

def run_tests(project_name, project_path, test_file):
    print(f"\n{'='*80}")
    print(f" {project_name}")
    print(f"{'='*80}\n")
    
    os.chdir(project_path)
    
    # Run tests
    result = subprocess.run(
        [sys.executable, '-m', 'pytest', f'tests/{test_file}', '-q', '--tb=no'],
        capture_output=True,
        text=True,
        timeout=30
    )
    
    output = result.stdout + (result.stderr if result.stderr else "")
    print(output)
    
    # Return status
    return result.returncode == 0, output

def main():
    os.chdir(r'c:\workSpace')
    
    print("\n" + "#" * 80)
    print("# COMPREHENSIVE PROJECT VALIDATION")
    print("#" * 80)
    
    # Test Project A
    success_a, output_a = run_tests(
        "PROJECT A: v1 API (Legacy)",
        r'c:\workSpace\Project_A_PreChange',
        'test_pre_change.py'
    )
    
    # Test Project B
    success_b, output_b = run_tests(
        "PROJECT B: v2 API (Modern)",
        r'c:\workSpace\Project_B_PostChange',
        'test_post_change.py'
    )
    
    # Final summary
    print("\n" + "=" * 80)
    print(" FINAL VALIDATION RESULTS")
    print("=" * 80)
    print(f"\nProject A (v1 API):  {'PASSED' if success_a else 'FAILED'}")
    print(f"Project B (v2 API):  {'PASSED' if success_b else 'FAILED'}")
    print(f"\nOverall Status:      {'ALL PASSED' if (success_a and success_b) else 'SOME FAILED'}")
    print("\n" + "=" * 80)
    
    return 0 if (success_a and success_b) else 1

if __name__ == '__main__':
    sys.exit(main())
