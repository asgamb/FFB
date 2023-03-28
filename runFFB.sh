#!/usr/bin/env bash

set -e

source "venv/bin/activate"
screen -dmS ffb -T xterm sh -c "python3 5grfbbAPI.py"

