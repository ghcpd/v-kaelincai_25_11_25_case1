@echo off
setlocal
echo Setting up venv
call setup.sh
echo Running pre-change tests
python -u tests/test_pre_change.py
