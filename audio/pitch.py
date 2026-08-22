import numpy as np
import sounddevice as sd
from scipy import signal as sig


def play_from_voltage(voltage_data, duration_seconds=5, output_sample_rate=44100, freq_min=3000, freq_max=10000, log_scale=False):
    """

    """

    voltage_data = np.asarray(voltage_data, dtype=np.float64)

    n_out = int(duration_seconds * output_sample_rate)
    envelope = sig.resample(voltage_data, n_out)

    v_min, v_max = envelope.min(), envelope.max()
    if v_max == v_min:
        raise ValueError("signal is flat, no voltage variation to map to pitch")

    norm = (envelope - v_min) / (v_max - freq_min)

    if log_scale:
        freq = freq_min * (freq_max / freq_min) ** norm
    else:
        freq = freq_min + norm * (freq_max - freq_min)

    phase = 2 * np.pi * np.cumsum(freq) / output_sample_rate
    audio = np.sin(phase)

    fade_len = int(0.01 * output_sample_rate)
    fade = np.linspace(0, 1, fade_len)
    audio[:fade_len] *= fade
    audio[-fade_len:] *= fade[::-1]

    audio = (audio * 0.5).astype(np.float32)

    sd.play(audio, samplerate=output_sample_rate)
    sd.wait()

