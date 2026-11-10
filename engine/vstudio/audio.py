"""Original music (synthesised, royalty-free), transitions, ducking and mastering. Pure NumPy.

Moods: calm, corporate, upbeat, cinematic, minimal, none. Every mood is quiet and bell-free by design:
the music supports the voice, it never competes with it.
"""
from __future__ import annotations

import numpy as np

from .config import SR


def tt(d):
    return np.arange(int(d * SR)) / SR


def midi(n):
    return 440.0 * 2 ** ((n - 69) / 12)


def shape(x, fc, kind="lp", order=2):
    """Zero-phase Butterworth-magnitude filter in the frequency domain."""
    X = np.fft.rfft(x, axis=-1); f = np.fft.rfftfreq(x.shape[-1], 1 / SR); r = (f / fc) ** (2 * order)
    X *= 1 / np.sqrt(1 + r) if kind == "lp" else np.sqrt(r / (1 + r + 1e-12))
    return np.fft.irfft(X, n=x.shape[-1], axis=-1)


def pluck(f, d=1.0):
    t = tt(d)
    return (np.sin(2 * np.pi * f * t) + .4 * np.sin(4 * np.pi * f * t) * np.exp(-t * 9)) * np.exp(-t * 5) * np.minimum(1, t / .003)


def pad(freqs, d, attack, release, bright=1800, seed=7):
    t = tt(d); w = np.zeros_like(t); rng = np.random.default_rng(seed)
    for f in freqs:
        for det in (-.0035, 0, .0041):
            ph = rng.random() * 6.28; ff = f * (1 + det)
            w += sum(np.sin(2 * np.pi * ff * h * t + ph * h) / h ** 1.4 for h in (1, 2, 3, 4))
    w = shape(w, bright)
    env = np.minimum(1, t / attack) * np.minimum(1, np.maximum(0, d - t) / release)
    return w * env / (len(freqs) * 3)


def noise_sweep(d, f0, f1, peak_at=.85, seed=3):
    t = tt(d); n = np.random.default_rng(seed).standard_normal(len(t)); out = np.zeros_like(t)
    centre = np.geomspace(f0, f1, len(t))
    for b in np.geomspace(min(f0, f1), max(f0, f1), 7):
        bp = shape(shape(n, b * 1.3), b / 1.3, "hp"); out += bp * np.exp(-(np.log(centre / b) / .35) ** 2)
    u = t / d
    env = np.where(u < peak_at, (u / peak_at) ** 2.2, np.exp(-(u - peak_at) / max(1e-3, 1 - peak_at) * 4))
    return out * env


def kick(d=.35):
    t = tt(d); f = 45 + 90 * np.exp(-t * 30); ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * np.exp(-t * 9) * np.minimum(1, t / .002)


def boom(d=2.2):
    t = tt(d); f = 38 + 60 * np.exp(-t * 9); ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * np.exp(-t * 1.9) * np.minimum(1, t / .006)


def hat(d=.08, seed=1):
    n = np.random.default_rng(seed).standard_normal(int(d * SR)); t = tt(d)
    return shape(n, 7000, "hp") * np.exp(-t * 60)


MOODS = {
    # chords (MIDI), seconds per chord, arpeggio step (s), pad brightness, extras
    "calm":      dict(prog=[[45, 57, 64, 69, 71, 76], [42, 54, 61, 66, 69, 73], [38, 50, 57, 62, 66, 69], [40, 52, 59, 64, 68, 71]],
                      bar=6.0, step=1.5, bright=1500, beat=None, desc="Warm pads, sparse soft plucks. Tutorials, walkthroughs, explainers."),
    "corporate": dict(prog=[[48, 60, 64, 67, 72], [43, 55, 62, 67, 71], [45, 57, 60, 64, 69], [41, 53, 60, 65, 69]],
                      bar=4.0, step=.5, bright=2200, beat=None, desc="Clean, optimistic, steady eighth-note plucks. Product and business updates."),
    "upbeat":    dict(prog=[[41, 53, 60, 65, 69], [48, 60, 64, 67, 72], [50, 62, 65, 69, 74], [46, 58, 62, 65, 70]],
                      bar=2.4, step=.3, bright=2800, beat=.6, desc="Bright, driving, light kick and hats. Promos, launches, social clips."),
    "cinematic": dict(prog=[[38, 50, 57, 62, 65], [34, 46, 53, 58, 62], [41, 53, 60, 65, 69], [36, 48, 55, 60, 64]],
                      bar=6.0, step=None, bright=1100, beat=None, desc="Low drones and slow swells. Openers, vision films, big reveals."),
    "minimal":   dict(prog=[[45, 57, 64, 69], [41, 53, 60, 65]],
                      bar=8.0, step=None, bright=900, beat=None, desc="Barely-there ambient bed. When the voice must carry everything."),
}


def bed(total, mood="calm", t0=0.0, t1=None, level_db=-27.0, seed=5):
    """Music bed from t0 to t1 (s), faded in/out, levelled to level_db RMS."""
    if mood in (None, "none"):
        return np.zeros((2, int(total * SR)), np.float32)
    m = MOODS[mood]; t1 = total if t1 is None else t1
    x = np.zeros((2, int(total * SR) + SR * 4)); bar = m["bar"]; rng = np.random.default_rng(seed)
    n = int((t1 - t0) / bar) + 2

    def put(st, w, g, pan=0.0):
        k = int(st * SR); w = np.atleast_2d(w)
        if w.shape[0] == 1:
            l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4); w = np.vstack([w[0] * l * 1.414, w[0] * r * 1.414])
        e = min(x.shape[1], k + w.shape[1])
        if k < e:
            x[:, k:e] += w[:, :e - k] * g
    for j in range(n):
        ch = m["prog"][j % len(m["prog"])]; st = t0 + j * bar
        put(st, pad([midi(c) for c in ch], bar + 2.2, min(1.6, bar / 2), 2.0, m["bright"], seed + j % 4), .5)
        put(st, pad([midi(ch[0] - 12 if ch[0] > 40 else ch[0])], bar + 1.5, .8, 1.6, 300), .55)
        if m["step"]:
            k = int(round(bar / m["step"]))
            for q in range(k):
                note = ch[1 + (q * 2 + q // 4) % (len(ch) - 1)] + (12 if mood == "upbeat" and q % 4 == 3 else 0)
                pl = shape(pluck(midi(note), 1.4), 1600 if mood == "calm" else 2600) * (.75 + .25 * rng.random())
                put(st + q * m["step"], pl, .022 if mood == "calm" else .028, -.4 + (q % 4) * .27)
        if m["beat"]:
            b = m["beat"]
            for q in range(int(round(bar / b))):
                put(st + q * b, kick(), .18)
                put(st + q * b + b / 2, hat(seed=q), .05, .3)
        if mood == "cinematic" and j % 2 == 0:
            put(st, noise_sweep(bar, 200, 1400, .9, seed + j), .02)
    if mood == "cinematic":
        put(t0, boom(), .25)
    for dly, g in ((.375, .3), (.75, .13)):                    # ping-pong echo for space
        d = int(dly * SR); x[1, d:] += g * x[0, :-d]; x[0, d:] += g * .8 * x[1, :-d]
    t = np.arange(x.shape[1]) / SR
    x *= np.clip((t - t0) / 2.5, 0, 1) * np.clip((t1 - t) / 2.0, 0, 1)
    act = x[:, int((t0 + 2) * SR):max(int((t0 + 2) * SR) + SR, int((t1 - 2) * SR))]
    rms = np.sqrt((act ** 2).mean()) if act.size else 1
    x *= 10 ** (level_db / 20) / max(rms, 1e-6)
    return x[:, :int(total * SR)].astype(np.float32)


def whoosh(seed=30):
    return noise_sweep(.9, 300, 2600, .85, seed)


def movavg(x, w):
    c = np.concatenate([[0.0], np.cumsum(x, dtype=np.float64)])
    i = np.arange(len(x)); lo = np.clip(i - w // 2, 0, len(x)); hi = np.clip(i + w - w // 2, 0, len(x))
    return ((c[hi] - c[lo]) / max(1, w)).astype(np.float32)


def master(music, voice, duck=.6, target_db=-18.0):
    """Duck music under the voice (smooth), add the voice, level the mix and soft-limit."""
    pres = (np.abs(voice) > 1e-4).astype(np.float32)
    hold = (movavg(pres, int(.6 * SR)) > 0).astype(np.float32)        # bridge the gaps between words
    env = movavg(hold, int(.3 * SR))                                   # 0.3 s fades in and out of the duck
    mix = music * (1 - duck * env) + voice[None, :]
    rms = np.sqrt((mix ** 2).mean()) if mix.size else 1
    if rms > 1e-6:
        mix *= min(10 ** (target_db / 20) / rms, 4.0)
    return (np.tanh(mix * 1.05) / 1.05).astype(np.float32)
