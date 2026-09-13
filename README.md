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

**macOS gotcha:** create the virtual environment with Homebrew's Python (or
python.org's installer), not Xcode's bundled `Python3.framework`. If `python3`
on your PATH resolves to Xcode's copy, macOS's privacy system hard-crashes
the process the moment it touches the microphone instead of showing the
normal permission prompt. `Run NextNote.command` already prefers
`/opt/homebrew/bin/python3` for this reason; if you set up the venv manually
run `which python3` first and make sure it's not under `Xcode.app`.

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
