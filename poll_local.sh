#!/bin/zsh
# Local helper: log the online flag every 30 s (used to measure how fast it flips).
set -a; . ~/.salus.env; set +a; export SALUS_DEVID=117466316
while true; do echo "$(date +%H:%M:%S) $(python3 salus_watch.py 2>&1 | tail -1)"; sleep 30; done
