#!/usr/bin/env python3
"""
Entry point for running Life-Assistant tests
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from eval.evaluator import TestRunner

def main():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    test_cases_file = os.path.join(current_dir, "test_cases.json")
    template_dir = os.path.join(current_dir, "template_life_system")
    test_runs_dir = os.path.join(current_dir, "test_runs")

    # Run tests
    runner = TestRunner(test_cases_file, template_dir, test_runs_dir)
    runner.run_all()

if __name__ == "__main__":
    main()
