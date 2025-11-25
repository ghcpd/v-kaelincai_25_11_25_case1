@echo off
setlocal
echo Setting up venv for v2
call setup.sh
echo Running post-change tests
python -u tests/test_post_change.py
