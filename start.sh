#!/bin/bash

tmux new-session -d -s LabWebpage
tmux send-keys -t LabWebpage 'cd /LabWebpage' C-m
tmux send-keys -t LabWebpage 'source .venv/bin/activate' C-m
tmux send-keys -t LabWebpage 'python3 -m flask run --host 0.0.0.0 --port 80' C-m