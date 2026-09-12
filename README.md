# NextNote

A PyQt5 practice tool for solo guitarists: a real-time chromatic tuner on top
(FFT-based pitch detection from the microphone), and on the bottom, a live log
of the notes you've played, an automatically detected key/scale, and a short
list of recommended notes to play next.

## Setup

```
pip install -r requirements.txt
python main.py
```

(or `python -m nextnote` from the repo root)

Requires a working microphone recognized as the system's default input
device.

## How it works

- **Tuner**: audio is captured continuously via `sounddevice`, windowed and
  run through an FFT; pitch is estimated with a Harmonic Product Spectrum
  (robust to guitar's strong harmonic overtones) plus parabolic interpolation
  for sub-bin (cents-level) accuracy.
- **Note log**: a spectral-flux onset detector segments the continuous audio
  into discrete note events (so a held note isn't logged repeatedly), and a
  short pitch-stabilization step avoids logging the noisy attack transient of
  a pluck.
- **Key/scale detection**: a 12-bin pitch-class histogram of your recently
  played notes is correlated against 24 major/minor key templates
  (Krumhansl-Schmuckler-style); the best match is shown.
- **Recommendations**: from the detected scale's 7 notes, the app suggests a
  few you haven't played recently, nudging you toward using the whole scale.

## Known limitation

Natural minor and its relative major share identical pitch classes (e.g. A
minor and C major), so pitch-content-only key detection cannot distinguish
between them. This is expected, not a bug.

## Configuration

All tunable constants (sample rate, FFT/hop size, onset sensitivity, in-tune
threshold, key-detection window, etc.) live in `nextnote/config.py`.
