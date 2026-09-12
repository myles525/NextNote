#!/bin/bash
# Double-click this file in Finder to launch NextNote.
cd "$(dirname "$0")"

# Prefer Homebrew's Python. Xcode's bundled Python3.framework (often what
# plain `python3` resolves to) gets hard-killed by macOS when it tries to
# access the microphone, instead of showing the normal permission prompt.
if [ -x "/opt/homebrew/bin/python3" ]; then
    PYTHON3="/opt/homebrew/bin/python3"
elif [ -x "/usr/local/bin/python3" ]; then
    PYTHON3="/usr/local/bin/python3"
else
    PYTHON3="python3"
fi

if [ ! -d ".venv" ]; then
    echo "First run: setting up NextNote..."
    "$PYTHON3" -m venv .venv
    ".venv/bin/pip" install --upgrade pip -q
    ".venv/bin/pip" install -q -r requirements.txt
fi

".venv/bin/python" main.py
status=$?

if [ $status -ne 0 ]; then
    echo ""
    echo "NextNote exited with an error (see above)."
    read -p "Press Enter to close this window..."
fi
