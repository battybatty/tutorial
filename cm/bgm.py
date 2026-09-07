# -*- coding: utf-8 -*-
"""30秒CM用のBGM・効果音をnumpyで合成する（外部音源を使わないオリジナル楽曲）。"""
import os, wave
import numpy as np

SR = 48000
DUR = 30.0
BPM = 120.0
BEAT = 60.0 / BPM      # 0.5s
BAR = BEAT * 4         # 2.0s
N = int(SR * DUR)
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "build")

buf = np.zeros(N + SR, dtype=np.float64)


def note(name: str) -> float:
    """音名(例: C4, A3, F#4)を周波数に変換。"""
    base = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
    n = base[name[0]]
    i = 1
    if name[1] in "#b":
        n += 1 if name[1] == "#" else -1
        i = 2
    octv = int(name[i:])
    midi = 12 * (octv + 1) + n
    return 440.0 * 2 ** ((midi - 69) / 12)


def add(x: np.ndarray, t0: float, gain: float = 1.0) -> None:
    i = int(t0 * SR)
    if i < 0:
        x = x[-i:]; i = 0
    j = min(len(buf), i + len(x))
    buf[i:j] += x[: j - i] * gain


def env_ad(n: int, a: float, d: float, curve: float = 3.0) -> np.ndarray:
    """アタック/ディケイ包絡。"""
    t = np.arange(n) / SR
    atk = np.clip(t / max(a, 1e-4), 0, 1)
    dec = np.exp(-t / max(d, 1e-4) * curve)
    return atk * dec


def lp(x: np.ndarray, k: int) -> np.ndarray:
    """移動平均によるローパス。"""
    if k <= 1:
        return x
    return np.convolve(x, np.ones(k) / k, mode="same")


def hp(x: np.ndarray, k: int) -> np.ndarray:
    return x - lp(x, k)


# ---------- 音色 ----------
def pluck(f: float, dur: float, gain: float = 1.0) -> np.ndarray:
    n = int(dur * SR); t = np.arange(n) / SR
    y = (np.sin(2 * np.pi * f * t)
         + 0.42 * np.sin(2 * np.pi * 2 * f * t)
         + 0.18 * np.sin(2 * np.pi * 3 * f * t)
         + 0.07 * np.sin(2 * np.pi * 5 * f * t))
    y *= env_ad(n, 0.004, dur * 0.42, 3.2)
    return y * gain * 0.25


def pad(freqs, dur: float, gain: float = 1.0) -> np.ndarray:
    n = int(dur * SR); t = np.arange(n) / SR
    y = np.zeros(n)
    for f in freqs:
        for det in (-0.16, 0.0, 0.16):      # デチューンで厚みを出す
            ph = 2 * np.pi * (f + det) * t
            y += (np.sin(ph) + 0.3 * np.sin(2 * ph) + 0.12 * np.sin(3 * ph))
    y = lp(y / (len(freqs) * 3), 26)
    a = min(0.55, dur * 0.35)
    e = np.clip(t / a, 0, 1) * np.clip((dur - t) / 0.5, 0, 1)
    return y * e * gain * 0.30


def bass(f: float, dur: float, gain: float = 1.0) -> np.ndarray:
    n = int(dur * SR); t = np.arange(n) / SR
    y = np.sin(2 * np.pi * f * t) + 0.25 * np.sin(4 * np.pi * f * t)
    y = np.tanh(y * 1.5)
    e = np.clip(t / 0.01, 0, 1) * np.clip((dur - t) / 0.08, 0, 1) * np.exp(-t / (dur * 1.6))
    return y * e * gain * 0.42


def kick(gain: float = 1.0) -> np.ndarray:
    n = int(0.34 * SR); t = np.arange(n) / SR
    f = 118 * np.exp(-t / 0.035) + 46
    y = np.sin(2 * np.pi * np.cumsum(f) / SR)
    y *= np.exp(-t / 0.11)
    y += 0.30 * np.random.default_rng(1).standard_normal(n) * np.exp(-t / 0.006)
    return np.tanh(y * 1.4) * gain * 0.62


def hat(dur: float = 0.045, gain: float = 1.0, seed: int = 2) -> np.ndarray:
    n = int(dur * SR)
    y = np.random.default_rng(seed).standard_normal(n)
    y = hp(y, 9) * np.exp(-np.arange(n) / SR / (dur * 0.35))
    return y * gain * 0.16


def clap(gain: float = 1.0) -> np.ndarray:
    n = int(0.26 * SR); t = np.arange(n) / SR
    rng = np.random.default_rng(7)
    y = np.zeros(n)
    for off, g in ((0.000, 0.7), (0.012, 0.85), (0.024, 1.0)):
        i = int(off * SR)
        seg = rng.standard_normal(n - i) * np.exp(-np.arange(n - i) / SR / 0.012)
        y[i:] += seg * g
    y += rng.standard_normal(n) * np.exp(-t / 0.075) * 0.45
    y = hp(lp(y, 5), 55)
    return y * gain * 0.24


def whoosh(dur: float, gain: float = 1.0, rise: bool = True, seed: int = 11) -> np.ndarray:
    n = int(dur * SR); t = np.arange(n) / SR
    y = np.random.default_rng(seed).standard_normal(n)
    y = hp(y, 40) * 0.6 + hp(y, 8) * 0.4
    shape = (t / dur) ** 2 if rise else (1 - t / dur) ** 2
    e = shape * np.clip((dur - t) / 0.05, 0, 1)
    return y * e * gain * 0.30


def riser(dur: float, gain: float = 1.0) -> np.ndarray:
    n = int(dur * SR); t = np.arange(n) / SR
    f = 220 * 2 ** (t / dur * 2.4)
    y = 0.5 * np.sin(2 * np.pi * np.cumsum(f) / SR)
    nz = np.random.default_rng(21).standard_normal(n)
    y += hp(nz, 30) * 0.8
    return y * ((t / dur) ** 2.2) * gain * 0.26


def impact(gain: float = 1.0) -> np.ndarray:
    n = int(1.5 * SR); t = np.arange(n) / SR
    f = 90 * np.exp(-t / 0.09) + 40
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.42)
    nz = np.random.default_rng(31).standard_normal(n)
    y += hp(nz, 12) * np.exp(-t / 0.10) * 0.5
    return np.tanh(y * 1.2) * gain * 0.55


def chime(f: float, dur: float, gain: float = 1.0) -> np.ndarray:
    n = int(dur * SR); t = np.arange(n) / SR
    y = np.zeros(n)
    for mult, amp, dec in ((1.0, 1.0, 1.0), (2.01, 0.5, 0.7), (3.02, 0.28, 0.5),
                           (4.98, 0.14, 0.35), (6.9, 0.07, 0.25)):
        y += amp * np.sin(2 * np.pi * f * mult * t) * np.exp(-t / (dur * dec * 0.4))
    return y * np.clip(t / 0.003, 0, 1) * gain * 0.20


def tick(gain: float = 1.0, seed: int = 5) -> np.ndarray:
    """テロップ表示に合わせる小さなUI音。"""
    n = int(0.10 * SR); t = np.arange(n) / SR
    y = np.sin(2 * np.pi * 1850 * t) * np.exp(-t / 0.012)
    y += hp(np.random.default_rng(seed).standard_normal(n), 6) * np.exp(-t / 0.005) * 0.5
    return y * gain * 0.13


# ---------- 編曲 ----------
CH = {                                   # 1小節ごとのコード
    "F":  (["F3", "A3", "C4", "F4"], "F2"),
    "G":  (["G3", "B3", "D4", "G4"], "G2"),
    "Am": (["A3", "C4", "E4", "A4"], "A2"),
    "C":  (["C4", "E4", "G4", "C5"], "C2"),
}
PROG = ["F", "G", "Am", "Am", "F", "G", "C", "C", "F", "G", "Am", "F", "F", "G", "C"]
ARP = {"F": ["F4", "A4", "C5", "A4"], "G": ["G4", "B4", "D5", "B4"],
       "Am": ["A4", "C5", "E5", "C5"], "C": ["C5", "E5", "G5", "E5"]}

for b, name in enumerate(PROG):
    t0 = b * BAR
    notes, root = CH[name]
    # セクション別の音量
    if b < 2:      pg, ag, dg = 0.55, 0.45, 0.0      # イントロ
    elif b < 6:    pg, ag, dg = 0.70, 0.62, 0.55     # 課題提起
    elif b < 12:   pg, ag, dg = 0.95, 0.85, 1.0      # 本編
    elif b < 14:   pg, ag, dg = 0.75, 0.55, 0.30     # CTA
    else:          pg, ag, dg = 0.85, 0.30, 0.0      # エンディング

    add(pad([note(x) for x in notes], BAR * 1.02, pg), t0)
    if dg > 0:
        add(bass(note(root), BEAT * 1.6, 0.9 * dg), t0)
        add(bass(note(root), BEAT * 1.1, 0.6 * dg), t0 + BEAT * 2.5)
    # アルペジオ（8分音符）
    seq = ARP[name]
    for k in range(8):
        if ag <= 0:
            break
        f = note(seq[k % 4]) * (0.5 if k >= 4 and b % 2 == 1 else 1.0)
        add(pluck(f, BEAT * 0.9, ag * (0.9 if k % 2 == 0 else 0.55)), t0 + k * BEAT / 2)
    # ドラム
    if dg > 0:
        for k in (0, 2):
            add(kick(dg), t0 + k * BEAT)
        add(kick(dg * 0.8), t0 + BEAT * 3.5)
        for k in (1, 3):
            add(clap(dg), t0 + k * BEAT)
        for k in range(8):
            add(hat(0.05, dg * (1.0 if k % 2 == 0 else 0.6), seed=2 + k), t0 + k * BEAT / 2)

# 効果音・シーン転換
add(whoosh(0.9, 1.0, rise=True), 0.0)          # オープニング
add(riser(2.0, 0.9), 10.0)                     # ロゴ前のライザー
add(impact(1.0), 12.0)                         # ロゴ登場
add(whoosh(0.5, 0.6, rise=False, seed=13), 12.0)
for t in (4.4, 7.7, 24.4):                     # シーン転換
    add(whoosh(0.45, 0.5, rise=False, seed=int(t * 7)), t)
for t in (15.15, 18.05, 21.55):                # 特徴カード表示
    add(tick(1.0, seed=int(t * 3)), t)
add(chime(note("C5"), 2.6, 1.0), 27.1)         # 締め
add(chime(note("G5"), 2.4, 0.55), 27.1)
add(chime(note("E6"), 2.0, 0.30), 27.18)

y = buf[:N]
# 全体をやわらかく整える
y = np.tanh(y * 1.15) / 1.15
y *= np.clip(np.arange(N) / (0.05 * SR), 0, 1)                  # フェードイン
y *= np.clip((N - np.arange(N)) / (1.1 * SR), 0, 1) ** 1.4      # フェードアウト
y = y / (np.abs(y).max() or 1.0) * 0.85

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    st = np.stack([y, y], axis=1)   # ステレオ（アルペジオを軽く広げる）
    d = np.roll(y, 260) * 0.18
    st[:, 0] += d; st[:, 1] -= d
    st = st / (np.abs(st).max() or 1.0) * 0.85
    p = os.path.join(OUT, "bgm.wav")
    with wave.open(p, "wb") as f:
        f.setnchannels(2); f.setsampwidth(2); f.setframerate(SR)
        f.writeframes((np.clip(st, -1, 1) * 32767).astype(np.int16).tobytes())
    print("wrote", p, f"{len(y)/SR:.2f}s")
