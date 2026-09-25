#!/bin/bash
set -euo pipefail
mkdir -p /logs/verifier
chmod 700 /tests
python -I -B /tests/test_behavior.py > /logs/verifier/checks.log 2>&1
cat /logs/verifier/checks.log
