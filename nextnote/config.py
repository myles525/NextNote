"""Central tunable constants for audio capture, DSP, and UI behavior."""

# --- Audio capture ---
SAMPLE_RATE = 44100
CHANNELS = 1
BLOCK_SIZE = 1024          # frames per sounddevice callback (~23ms)
DEVICE = None              # None = system default input device
QUEUE_MAX_CHUNKS = 50      # ~1.2s of audio buffered between capture and analysis threads

# --- Analysis buffer / FFT ---
FFT_WINDOW_SIZE = 8192     # samples analyzed per frame (~186ms @ 44.1kHz)
ZERO_PAD_FACTOR = 2        # zero-pad to FFT_WINDOW_SIZE * this, smooths peak shape for interpolation
HOP_SIZE = 2048            # samples advanced between analysis frames (~46ms hop, ~21-22 updates/sec)

# --- Harmonic Product Spectrum pitch detection ---
HPS_HARMONICS = 5
MIN_FREQ_HZ = 70.0         # below low E2 (82.4Hz) with margin for flat tuning
MAX_FREQ_HZ = 1200.0       # covers high frets on guitar
MIN_NOTE_RMS = 0.01        # noise floor gate; below this, treat as silence

# --- Tuning reference / display ---
A4_FREQ = 440.0
IN_TUNE_CENTS_THRESHOLD = 5.0
CENTS_DISPLAY_RANGE = 50.0

# --- Onset detection ---
ONSET_MIN_INTERVAL_SEC = 0.12
ONSET_FLUX_THRESHOLD_MULT = 1.5
ONSET_HISTORY_SEC = 1.0
MIN_NOTE_DURATION_SEC = 0.08

# --- Pitch confirmation (debounce transient noise before logging a note) ---
PITCH_CONFIRM_FRAMES = 2
PITCH_CONFIRM_TOLERANCE_CENTS = 50.0

# --- Recommendation ---
RECOMMEND_COUNT = 4
RECENCY_DECAY_NOTES = 8
RECENCY_PENALTY = 0.5

# --- UI ---
SEQUENCE_LOG_MAX_ITEMS = 500
