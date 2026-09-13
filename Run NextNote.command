#!/bin/bash
# Double-click this file in Finder to launch NextNote.
cd "$(dirname "$0")"

# Prefer Homebrew's Python over Xcode's bundled copy (see fix_microphone_framework_app below).
if [ -x "/opt/homebrew/bin/python3" ]; then
    PYTHON3="/opt/homebrew/bin/python3"
elif [ -x "/usr/local/bin/python3" ]; then
    PYTHON3="/usr/local/bin/python3"
else
    PYTHON3="python3"
fi

# macOS "framework build" Python (Homebrew's and python.org's default on
# macOS, as well as Xcode's bundled copy) ships its own Python.app bundle.
# That bundle's Info.plist doesn't declare microphone usage, so macOS
# hard-aborts the process the moment it touches the mic instead of showing
# the normal permission prompt. This patches the Info.plist to declare it
# and re-signs the bundle ad-hoc so the fix takes effect. It's idempotent
# (skips already-patched bundles) and self-heals after e.g. a Homebrew
# upgrade replaces the bundle.
fix_microphone_framework_app() {
    local framework_app
    framework_app=$("$PYTHON3" -c "
import os, sys
exe = os.path.realpath(sys.executable)
parts = exe.split(os.sep)
if 'Python.framework' in parts and 'Versions' in parts:
    fi = parts.index('Python.framework')
    vi = parts.index('Versions', fi)
    version = parts[vi + 1]
    base = os.sep.join(parts[:fi + 1])
    app = os.path.join(base, 'Versions', version, 'Resources', 'Python.app')
    print(app if os.path.isdir(app) else '')
else:
    print('')
" 2>/dev/null)

    if [ -z "$framework_app" ]; then
        return
    fi

    local plist="$framework_app/Contents/Info.plist"
    if ! /usr/libexec/PlistBuddy -c "Print :NSMicrophoneUsageDescription" "$plist" >/dev/null 2>&1; then
        echo "One-time setup: enabling microphone access for $framework_app..."
        /usr/libexec/PlistBuddy -c "Add :NSMicrophoneUsageDescription string 'NextNote uses the microphone to listen to guitar playing for tuning and note detection.'" "$plist" 2>/dev/null
        codesign --force --deep --sign - "$framework_app" 2>/dev/null
    fi
}

fix_microphone_framework_app

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
