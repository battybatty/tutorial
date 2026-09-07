# -*- coding: utf-8 -*-
"""BGMとナレーションをミックス（ナレーション時のBGMダッキング付き）。"""
import os, wave
import numpy as np
from timeline import NARRATION, DURATION

SR = 48000
HERE = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(HERE, "build")
N = int(SR * DURATION)


def read_wav(path):
    with wave.open(path, "rb") as f:
        ch, sw, sr, n = f.getnchannels(), f.getsampwidth(), f.getframerate(), f.getnframes()
        d = np.frombuffer(f.readframes(n), dtype=np.int16).astype(np.float64) / 32768.0
    return d.reshape(-1, ch) if ch > 1 else d.reshape(-1, 1), sr


def smooth(x, k):
    return np.convolve(x, np.ones(k) / k, mode="same")


def main():
    bgm, _ = read_wav(os.path.join(BUILD, "bgm.wav"))
    if bgm.shape[0] < N:
        bgm = np.pad(bgm, ((0, N - bgm.shape[0]), (0, 0)))
    bgm = bgm[:N]

    vox = np.zeros(N)
    for lid, (t0, _) in NARRATION.items():
        y, _ = read_wav(os.path.join(BUILD, f"{lid}.wav"))
        y = y[:, 0]
        i = int(t0 * SR)
        j = min(N, i + len(y))
        vox[i:j] += y[: j - i]

    # ダッキング: ナレーションの包絡からBGMのゲインを作る
    env = smooth(np.abs(vox), 2001)
    env = env / (env.max() or 1.0)
    duck = 1.0 - 0.62 * np.clip(env * 3.5, 0, 1)
    duck = smooth(duck, 4001)

    mix = bgm * duck[:, None] * 0.72 + np.stack([vox, vox], axis=1) * 0.90
    mix = np.tanh(mix * 1.05) / 1.05
    mix = mix / (np.abs(mix).max() or 1.0) * 0.94
    mix *= np.clip((N - np.arange(N))[:, None] / (0.5 * SR), 0, 1)

    out = os.path.join(BUILD, "mix.wav")
    with wave.open(out, "wb") as f:
        f.setnchannels(2); f.setsampwidth(2); f.setframerate(SR)
        f.writeframes((np.clip(mix, -1, 1) * 32767).astype(np.int16).tobytes())
    rms = 20 * np.log10(np.sqrt((mix ** 2).mean()) + 1e-9)
    print(f"wrote {out}  {N/SR:.2f}s  RMS {rms:.1f} dBFS")


if __name__ == "__main__":
    main()
