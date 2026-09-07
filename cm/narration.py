# -*- coding: utf-8 -*-
"""Expert Partners Marketing 30秒CM: ナレーション音声の生成 (Open JTalk / mei voice)."""
import os, wave
import numpy as np
import pyopenjtalk

SR = 48000
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "build")

# (id, テロップ用テキスト, 読み上げテキスト, 話速)
LINES = [
    ("l1", "広告運用も、SEOも、SNSも。",              "広告運用も、エスイーオーも、エスエヌエスも。", 1.05),
    ("l2", "任せられるマーケターが、社内にいない。",    "任せられるマーケターが、社内にいない。",       1.05),
    ("l3", "その課題、プロのフリーランスが解決します。", "その課題、プロのフリーランスが解決します。",   1.02),
    ("l4", "Expert Partners Marketing",              "エキスパートパートナーズ、マーケティング。",   0.98),
    ("l5", "登録マーケター 10,000人以上",             "登録マーケター、一万人以上。",                1.00),
    ("l6", "現役マーケターが厳選した即戦力",           "現役マーケターが厳選した、即戦力。",          1.02),
    ("l7", "戦略設計から実行まで。",                  "戦略設計から、実行まで。",                   1.02),
    ("l8", "まずは無料でご相談ください。",             "まずは無料で、ご相談ください。",              1.00),
]


def synth(text: str, speed: float) -> np.ndarray:
    x, sr = pyopenjtalk.tts(text, speed=speed)
    assert sr == SR, sr
    x = x / 32768.0
    # 無音トリム
    env = np.abs(x)
    idx = np.where(env > env.max() * 0.01)[0]
    if len(idx):
        x = x[max(0, idx[0] - 480): idx[-1] + 2400]
    return x


def polish(x: np.ndarray) -> np.ndarray:
    """こもりがちなHMM音声に軽いプレゼンス補正とコンプをかける。"""
    # ハイシェルフ相当: 原音 + 高域成分
    hp = x - np.convolve(x, np.ones(24) / 24, mode="same")
    y = x + 0.55 * hp
    # ローカット (DC/低域のもたつき除去)
    lf = np.convolve(y, np.ones(220) / 220, mode="same")
    y = y - 0.85 * lf
    # ソフトコンプ + リミッタ
    y = np.tanh(y * 2.6) / 2.6
    peak = np.abs(y).max() or 1.0
    return (y / peak * 0.92).astype(np.float64)


def write_wav(path: str, x: np.ndarray, sr: int = SR) -> None:
    d = (np.clip(x, -1, 1) * 32767).astype(np.int16)
    with wave.open(path, "wb") as f:
        f.setnchannels(1); f.setsampwidth(2); f.setframerate(sr)
        f.writeframes(d.tobytes())


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for lid, telop, yomi, sp in LINES:
        y = polish(synth(yomi, sp))
        write_wav(os.path.join(OUT, f"{lid}.wav"), y)
        print(f"{lid}\t{len(y)/SR:6.2f}s\t{telop}")
