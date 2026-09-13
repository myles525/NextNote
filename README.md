# NextNote

A PyQt5 practice tool for solo guitarists: a real-time chromatic tuner on top
(FFT-based pitch detection from the microphone), and on the bottom, a scale
picker plus a live log of the notes you've played, color-coded by whether
each one belongs to your chosen scale — with a suggested correction whenever
you play a note outside it.

## Setup

```
pip install -r requirements.txt
python main.py
```

(or `python -m nextnote` from the repo root)

Requires a working microphone recognized as the system's default input
device.

On macOS, double-click `Run NextNote.command` instead of using the terminal —
it sets up the virtual environment on first run and launches the app.

**macOS gotcha:** any "framework build" of Python (Homebrew's and
python.org's default on macOS, and Xcode's bundled copy) ships its own
`Python.app` bundle. That bundle's `Info.plist` doesn't declare microphone
usage, so macOS hard-aborts the process the instant it touches the mic
instead of showing the normal permission prompt. `Run NextNote.command`
detects this automatically and patches the bundle's `Info.plist` to declare
mic usage, then re-signs it ad-hoc (idempotent — a no-op on later runs, and
self-healing after a Homebrew upgrade replaces the bundle). If you set up
the venv manually and hit a crash mentioning `abort() called` and a
`Python.app` path, apply the same fix yourself:

```
PY_APP=$(python3 -c "import os,sys; print(os.path.dirname(os.path.dirname(os.path.realpath(sys.executable))) + '/Resources/Python.app')")
/usr/libexec/PlistBuddy -c "Add :NSMicrophoneUsageDescription string 'NextNote uses the microphone.'" "$PY_APP/Contents/Info.plist"
codesign --force --deep --sign - "$PY_APP"
```

## How it works

- **Tuner**: audio is captured continuously via `sounddevice`, windowed and
  run through an FFT; pitch is estimated with a Harmonic Product Spectrum
  (robust to guitar's strong harmonic overtones) plus parabolic interpolation
  for sub-bin (cents-level) accuracy.
- **Note log**: a spectral-flux onset detector segments the continuous audio
  into discrete note events (so a held note isn't logged repeatedly), and a
  short pitch-stabilization step avoids logging the noisy attack transient of
  a pluck.
- **Scale picker**: pick a root note and scale type (Major, Natural Minor,
  Major/Minor Pentatonic, Blues) from the dropdowns. Every confirmed note is
  checked against that fixed scale — in-scale notes show green in the log; an
  out-of-scale note shows red and the panel suggests the nearest note (by
  semitone distance) that would have been in the scale.

## Configuration

All tunable constants (sample rate, FFT/hop size, onset sensitivity, in-tune
threshold, etc.) live in `nextnote/config.py`. Scale definitions live in
`nextnote/theory/scales.py`.
