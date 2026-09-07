# -*- coding: utf-8 -*-
"""Expert Partners Marketing 30秒CM: 映像フレームのレンダリング。"""
import math, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from timeline import (FPS, DURATION, W, H, S1, S2, S3, S4, S5, S6,
                      CARD_TIMES, IMPACT_T)

HERE = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(HERE, "build")
F_JP = "/usr/share/fonts/opentype/ipafont-gothic/ipagp.ttf"
F_EN = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

WHITE = (255, 255, 255)
MUTED = (166, 186, 208)
EMER = (46, 222, 160)
BLUE = (72, 146, 255)
WARN = (255, 112, 94)
INK = (7, 20, 36)

BW, BH = 2200, 1240          # 背景テクスチャ（パン用に画面より大きく作る）


# ---------------------------------------------------------------- utilities
def clamp01(x):
    return 0.0 if x < 0 else (1.0 if x > 1 else x)


def eo(x, p=3.0):
    return 1 - (1 - clamp01(x)) ** p


def ei(x, p=3.0):
    return clamp01(x) ** p


def eio(x):
    x = clamp01(x)
    return x * x * (3 - 2 * x)


def fadeout(t, t0, dur=0.3):
    return 1 - clamp01((t - t0) / dur)


_fonts = {}


def font(size, kind="jp"):
    key = (size, kind)
    if key not in _fonts:
        _fonts[key] = ImageFont.truetype(F_JP if kind == "jp" else F_EN, size)
    return _fonts[key]


_sprites = {}
_m = ImageDraw.Draw(Image.new("L", (4, 4)))


def adv(s, size, kind="jp", track=0.0):
    """文字送り幅（描画位置計算用）。"""
    f = font(size, kind)
    return sum(_m.textlength(c, font=f) for c in s) + track * max(0, len(s) - 1)


def sprite_run(parts, size, kind="jp", bold=True, track=0.0, shadow=None):
    """(文字列, 色) の並びを1枚のRGBAスプライトにする（キャッシュ付き）。"""
    key = (tuple(parts), size, kind, bold, track, shadow)
    sp = _sprites.get(key)
    if sp is not None:
        return sp
    f = font(size, kind)
    sw = max(1, size // 28) if bold else 0
    asc, desc = f.getmetrics()
    chars = [(c, col) for s, col in parts for c in s]
    w = sum(_m.textlength(c, font=f) for c, _ in chars) + track * max(0, len(chars) - 1)
    im = Image.new("RGBA", (int(w) + 2 * sw + 8, asc + desc + 2 * sw + 8), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    x = sw + 4
    for c, col in chars:
        d.text((x, sw + 4), c, font=f, fill=col + (255,),
               stroke_width=sw, stroke_fill=col + (255,))
        x += _m.textlength(c, font=f) + track

    if shadow is None:
        shadow = max(0, size // 9) if size >= 40 else 0
    if shadow:
        pad = shadow * 3
        out = Image.new("RGBA", (im.width + 2 * pad, im.height + 2 * pad), (0, 0, 0, 0))
        sh = Image.new("RGBA", out.size, (0, 0, 0, 0))
        sh.paste(Image.new("RGBA", im.size, (2, 9, 20, 205)),
                 (pad, pad + int(shadow * 0.55)), im.getchannel("A"))
        out.alpha_composite(sh.filter(ImageFilter.GaussianBlur(shadow)))
        out.alpha_composite(im, (pad, pad))
        im = out
    _sprites[key] = im
    return im


def sprite(text, size, color=WHITE, kind="jp", bold=True, track=0.0, shadow=None):
    return sprite_run(((text, color),), size, kind, bold, track, shadow)


def blit(img, sp, x, y, alpha=1.0, scale=1.0, anchor="mm"):
    if alpha <= 0.004:
        return
    if scale != 1.0:
        sp = sp.resize((max(1, int(sp.width * scale)), max(1, int(sp.height * scale))),
                       Image.LANCZOS)
    if alpha < 0.996:
        sp = sp.copy()
        sp.putalpha(sp.getchannel("A").point(lambda v: int(v * alpha)))
    ax = {"l": 0.0, "m": 0.5, "r": 1.0}[anchor[0]]
    ay = {"t": 0.0, "m": 0.5, "b": 1.0}[anchor[1]]
    img.alpha_composite(sp, (int(x - sp.width * ax), int(y - sp.height * ay)))


def text(img, s, size, x, y, color=WHITE, kind="jp", alpha=1.0, scale=1.0,
         anchor="mm", track=0.0, bold=True, shadow=None):
    blit(img, sprite(s, size, color, kind, bold, track, shadow), x, y, alpha, scale, anchor)


def rrect(img, box, radius, fill=None, outline=None, width=3, alpha=1.0):
    x0, y0, x1, y1 = [int(v) for v in box]
    w, h = max(1, x1 - x0), max(1, y1 - y0)
    a = int(255 * clamp01(alpha))
    if a == 0:
        return
    ov = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(ov).rounded_rectangle(
        [0, 0, w - 1, h - 1], radius=radius,
        fill=(fill + (a,)) if fill else None,
        outline=(outline + (a,)) if outline else None, width=width)
    img.alpha_composite(ov, (x0, y0))


_glows = {}


def glow(size, color):
    key = (size, color)
    g = _glows.get(key)
    if g is None:
        m = Image.new("L", (size, size), 0)
        ImageDraw.Draw(m).ellipse([size * .28, size * .28, size * .72, size * .72], fill=255)
        m = m.filter(ImageFilter.GaussianBlur(size * 0.11))
        g = Image.new("RGBA", (size, size), color + (0,))
        g.putalpha(m)
        _glows[key] = g
    return g


# ---------------------------------------------------------------- background
def build_bg(bright: bool) -> np.ndarray:
    top = np.array([10, 21, 39] if not bright else [12, 30, 55], float)
    bot = np.array([16, 38, 66] if not bright else [19, 52, 90], float)
    g = np.linspace(0, 1, BH)[:, None, None]
    base = top[None, None, :] * (1 - g) + bot[None, None, :] * g
    img = Image.fromarray(np.repeat(base, BW, axis=1).astype(np.uint8), "RGB").convert("RGBA")

    blobs = [(0.18, 0.14, 900, BLUE, 150), (0.86, 0.86, 1000, EMER, 80),
             (0.62, 1.02, 820, BLUE, 105), (0.05, 0.72, 700, EMER, 60)]
    if bright:
        blobs += [(0.50, 0.30, 1250, BLUE, 125), (0.30, 0.95, 800, EMER, 70)]
    for fx, fy, sz, col, inten in blobs:
        gl = glow(sz, col).copy()
        gl.putalpha(gl.getchannel("A").point(lambda v, i=inten: int(v * i / 255)))
        img.alpha_composite(gl, (int(BW * fx - sz / 2), int(BH * fy - sz / 2)))

    ov = Image.new("RGBA", (BW, BH), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    for x in range(0, BW, 96):                       # 薄いグリッド
        d.line([(x, 0), (x, BH)], fill=(120, 165, 220, 7), width=1)
    for y in range(0, BH, 96):
        d.line([(0, y), (BW, y)], fill=(120, 165, 220, 7), width=1)
    for i in range(-6, 12):                          # やわらかい斜めの光筋
        x = i * 340
        d.line([(x, BH + 200), (x + 760, -200)], fill=(150, 200, 255, 7), width=170)
    ov = ov.filter(ImageFilter.GaussianBlur(26))
    img.alpha_composite(ov)

    a = np.asarray(img.convert("RGB")).astype(np.float32)
    yy, xx = np.mgrid[0:BH, 0:BW]
    r = np.sqrt(((xx / BW - .5) * 1.05) ** 2 + ((yy / BH - .5) * 1.15) ** 2)
    a *= np.clip(1.14 - r * 0.92, 0.46, 1.0)[:, :, None]      # ビネット
    a += np.random.default_rng(3).normal(0, 2.0, (BH, BW, 1))  # 微細なグレイン
    return np.clip(a, 0, 255).astype(np.uint8)


BG_DARK = None
BG_BRIGHT = None


def bg_frame(t):
    ox = int(140 + 130 * math.sin(2 * math.pi * t / 52 + 0.4))
    oy = int(80 + 70 * math.cos(2 * math.pi * t / 41))
    src = BG_BRIGHT if t >= IMPACT_T else BG_DARK
    return src[oy:oy + H, ox:ox + W]


# ---------------------------------------------------------------- scenes
def swipe(img, t, t0, dur=0.38):
    """シーン転換のライトスイープ。"""
    if not (t0 <= t < t0 + dur):
        return
    p = (t - t0) / dur
    cx = -420 + p * (W + 840)
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    for wd, al, col in ((360, 22, (170, 210, 255)), (150, 40, (170, 210, 255)), (9, 140, EMER)):
        d.polygon([(cx - wd + 120, 0), (cx + wd + 120, 0),
                   (cx + wd - 120, H), (cx - wd - 120, H)], fill=col + (al,))
    img.alpha_composite(ov.filter(ImageFilter.GaussianBlur(7)))


def scene1(img, t):
    out = fadeout(t, 4.05)
    text(img, "マーケティングの現場で、いま", 40, W / 2, 352, MUTED,
         alpha=eo((t - 0.25) / 0.5) * out)

    chips = (("広告運用", 0.72), ("SEO", 1.62), ("SNS", 2.42))
    widths = [adv(c, 62) for c, _ in chips]
    gap = 44
    total = sum(w + 96 for w in widths) + gap * 2
    x = W / 2 - total / 2
    for (label, ct), tw in zip(chips, widths):
        p = eo((t - ct) / 0.42)
        cw = tw + 96
        if p > 0:
            a = p * out
            dy = (1 - p) * 26
            rrect(img, (x, 444 + dy, x + cw, 566 + dy), 61, fill=(22, 46, 80),
                  outline=BLUE, width=3, alpha=a * 0.92)
            text(img, label, 62, x + cw / 2, 505 + dy, WHITE, alpha=a)
        x += cw + gap

    p = eo((t - 3.02) / 0.5)
    if p > 0:
        text(img, "やることは、増え続ける。", 78, W / 2, 700 + (1 - p) * 22, WHITE, alpha=p * out)


def scene2(img, t):
    p = eo((t - 4.62) / 0.55)
    if p <= 0:
        return
    a = p * fadeout(t, 7.35)
    sc = 0.965 + 0.035 * p
    dy = (1 - p) * 24
    text(img, "任せられるマーケターが、", 88, W / 2, 458 + dy, WHITE, alpha=a, scale=sc)

    run = sprite_run((("社内に", WHITE), ("いない", WARN), ("。", WHITE)), 96)
    blit(img, run, W / 2, 596 + dy, a, sc, "mm")

    q = eo((t - 5.5) / 0.45)
    if q > 0:                                        # 「いない」の下線
        left = W / 2 - adv("社内にいない。", 96) * sc / 2 + adv("社内に", 96) * sc
        rrect(img, (left, 664 + dy, left + adv("いない", 96) * sc * q, 672 + dy),
              4, fill=WARN, alpha=a * 0.9)

    r = eo((t - 5.9) / 0.5)
    if r > 0:
        text(img, "採用しても、育てても、時間が足りない。", 40, W / 2, 772, MUTED,
             alpha=r * fadeout(t, 7.35))


def scene3(img, t):
    build = clamp01((t - 10.0) / 2.0)
    sc = 1.0 + 0.11 * ei(build, 2.2)
    out = fadeout(t, 11.62, 0.36)

    g = int(560 + 1000 * ei(build, 1.7))             # 中央のグロー（クライマックス）
    blit(img, glow(g, BLUE), W / 2, 560, 0.10 + 0.80 * ei(build, 2.0), 1.0, "mm")

    if build > 0:                                    # 中心へ収束する集中線
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(ov)
        for i in range(22):
            ang = i * math.pi / 11 + build * 0.35
            r1 = 1150 * (1 - eio(build)) + 40
            r2 = r1 + 260 * (1 - 0.55 * build)
            cx, cy = W / 2, 560
            d.line([(cx + math.cos(ang) * r1, cy + math.sin(ang) * r1 * 0.72),
                    (cx + math.cos(ang) * r2, cy + math.sin(ang) * r2 * 0.72)],
                   fill=(200, 230, 255, int(120 * build * (1 - build * 0.4))), width=3)
        img.alpha_composite(ov.filter(ImageFilter.GaussianBlur(3)))

    text(img, "その課題、", 60, W / 2, 402, MUTED, alpha=eo((t - 7.95) / 0.45) * out, scale=sc)
    p2 = eo((t - 8.30) / 0.5)
    if p2 > 0:
        text(img, "プロのフリーランスが、", 92, W / 2, 528 + (1 - p2) * 20, WHITE,
             alpha=p2 * out, scale=sc)
    p3 = eo((t - 8.85) / 0.5)
    if p3 > 0:
        text(img, "解決する。", 104, W / 2, 668 + (1 - p3) * 20, EMER, alpha=p3 * out, scale=sc)
    p4 = eo((t - 9.30) / 0.55)
    if p4 > 0:
        bw = 300 * p4 * sc
        rrect(img, (W / 2 - bw / 2, 752, W / 2 + bw / 2, 760), 4, fill=EMER, alpha=p4 * out)


def logo_lockup(img, t, t0, cx, cy, big, alpha=1.0, scale=1.0):
    """Expert Partners / MARKETING のロゴ組み。"""
    p = eo((t - t0) / 0.5)
    sc = scale * (1.05 - 0.05 * p)
    a = alpha * clamp01((t - t0) / 0.22)
    text(img, "Expert Partners", int(big), cx, cy, WHITE, "en", a, sc, "mm", track=big * 0.045)
    q = eo((t - t0 - 0.18) / 0.45)
    if q > 0:
        text(img, "MARKETING", int(big * 0.52), cx, cy + big * 0.78 * sc, EMER, "en",
             a * q, sc, "mm", track=big * 0.30)


def scene4(img, t):
    fl = clamp01(1 - (t - IMPACT_T) / 0.45)          # 登場フラッシュ
    if fl > 0:
        img.alpha_composite(Image.new("RGBA", (W, H), (255, 255, 255, int(215 * ei(fl, 1.6)))))
    out = fadeout(t, 14.65, 0.35)
    blit(img, glow(1150, BLUE), W / 2, 520, 0.32 * out, 1.0, "mm")
    logo_lockup(img, t, 12.05, W / 2, 470, 124, alpha=out)
    p = eo((t - 12.55) / 0.5)
    if p > 0:
        bw = 520 * p
        rrect(img, (W / 2 - bw / 2, 646, W / 2 + bw / 2, 652), 3, fill=EMER, alpha=p * out)
    q = eo((t - 12.75) / 0.5)
    if q > 0:
        text(img, "フリーランスマーケター特化型エージェント", 48, W / 2, 726 + (1 - q) * 16,
             WHITE, alpha=q * out * 0.95)


CARDS = [
    ("01", "登録マーケター", "10,000人以上",
     "2023年のサービス開始から\n累計登録者数が1万人を突破"),
    ("02", "現役マーケターが厳選", "即戦力のプロ",
     "副業アシスタントではなく、\n成果にコミットする人材をご紹介"),
    ("03", "戦略設計から実行まで", "ワンストップ",
     "広告運用・SEO・SNS・\nアフィリエイトなど幅広く対応"),
]
CW, CHH, GAP = 480, 470, 60
CX0 = (W - (CW * 3 + GAP * 2)) / 2
CY = 372


def draw_cards(img, t, alpha=1.0, dy_all=0.0):
    # 表示枚数に応じてカード群が中央から左右に広がるレイアウト
    ps = [eo((t - ct) / 0.55) for ct in CARD_TIMES]
    count = sum(ps)
    x = W / 2 - (CW * count + GAP * max(0.0, count - 1)) / 2
    for i, (num, title, kick, desc) in enumerate(CARDS):
        p = ps[i]
        if p <= 0:
            continue
        a = p * alpha
        y = CY + (1 - p) * 40 + dy_all
        rrect(img, (x, y, x + CW, y + CHH), 26, fill=(15, 33, 58), alpha=a * 0.90)
        rrect(img, (x, y, x + CW, y + CHH), 26, outline=(62, 98, 148), width=2, alpha=a * 0.9)
        rrect(img, (x + 2, y + 30, x + 8, y + CHH - 30), 3, fill=EMER, alpha=a)
        text(img, num, 34, x + 42, y + 58, EMER, "en", a, 1.0, "lm", track=2)
        text(img, title, 38, x + 36, y + 134, WHITE, alpha=a, anchor="lm")
        text(img, kick, 54, x + 34, y + 216, EMER, alpha=a, anchor="lm")
        rrect(img, (x + 42, y + 272, x + CW - 42, y + 274), 1, fill=(76, 110, 156), alpha=a)
        for k, line in enumerate(desc.split("\n")):
            text(img, line, 26, x + 42, y + 316 + k * 42, MUTED, alpha=a * 0.95,
                 anchor="lm", bold=False, shadow=0)
        x += (CW + GAP) * p


def scene5(img, t):
    a = fadeout(t, 24.42, 0.28)
    logo_lockup(img, t, 15.0, W / 2, 176, 46, alpha=0.9 * a)
    draw_cards(img, t, alpha=a, dy_all=(1 - a) * 30)
    text(img, "マーケティング人材の課題を、まるごと解決。", 34, W / 2, 906, MUTED,
         alpha=eo((t - 15.6) / 0.6) * a * 0.92, bold=False)


def scene6(img, t):
    p = eo((t - 24.82) / 0.5)
    fade = 1 - clamp01((t - 29.62) / 0.38)
    blit(img, glow(1300, BLUE), W / 2, 560, 0.30 * p * fade, 1.0, "mm")

    ch = clamp01((t - 27.10) / 1.1)                  # 締めのきらめき
    if 0 < ch < 1:
        blit(img, glow(1000, EMER), W / 2, 500, 0.22 * (1 - ch) * fade, 1.0, "mm")

    if p > 0:
        text(img, "まずは無料で、ご相談ください。", 74, W / 2, 372 + (1 - p) * 20, WHITE,
             alpha=p * fade)

    q = eo((t - 25.35) / 0.45)
    if q > 0:
        pop = 1.06 - 0.06 * q
        pulse = 1 + 0.012 * math.sin((t - 25.35) * 5.0)
        bw, bh = 640 * pop * pulse, 116 * pop * pulse
        blit(img, glow(int(bw * 1.5), EMER), W / 2, 546, 0.28 * q * fade, 1.0, "mm")
        rrect(img, (W / 2 - bw / 2, 546 - bh / 2, W / 2 + bw / 2, 546 + bh / 2),
              int(bh / 2), fill=EMER, alpha=q * fade)
        text(img, "無料相談はこちら", 48, W / 2, 546, INK, alpha=q * fade, scale=pop, shadow=0)

    r = eo((t - 25.95) / 0.5)
    if r > 0:
        logo_lockup(img, t, 25.95, W / 2, 730, 54, alpha=r * fade)
        s = eo((t - 26.35) / 0.5)
        if s > 0:
            text(img, "expertpartners.jp", 40, W / 2, 866, EMER, "en", s * fade,
                 1.0, "mm", track=2)


def frame(t):
    img = Image.fromarray(bg_frame(t), "RGB").convert("RGBA")
    if t < S1[1]:
        scene1(img, t)
    elif t < S2[1]:
        scene2(img, t)
    elif t < S3[1]:
        scene3(img, t)
    elif t < S4[1]:
        scene4(img, t)
    elif t < S5[1]:
        scene5(img, t)
    else:
        scene6(img, t)

    swipe(img, t, S2[0] - 0.20)
    swipe(img, t, S3[0] - 0.20)
    swipe(img, t, S6[0] - 0.20)

    k = min(clamp01(t / 0.45), 1 - clamp01((t - 29.65) / 0.35))
    if k < 0.999:
        img.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, int(255 * (1 - k)))))
    return img.convert("RGB")


def main():
    global BG_DARK, BG_BRIGHT
    BG_DARK = build_bg(False)
    BG_BRIGHT = build_bg(True)

    if len(sys.argv) > 2 and sys.argv[1] == "--preview":
        os.makedirs(os.path.join(BUILD, "preview"), exist_ok=True)
        for s in sys.argv[2].split(","):
            tt = float(s)
            frame(tt).save(os.path.join(BUILD, "preview", f"t{tt:05.2f}.png"))
            print("preview", tt)
        return

    import imageio_ffmpeg
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    out = os.path.join(BUILD, "ep_marketing_cm_30s_1080p.mp4")
    cmd = [ff, "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-i", os.path.join(BUILD, "mix.wav"),
           "-c:v", "libx264", "-preset", "slow", "-crf", "19", "-pix_fmt", "yuv420p",
           "-profile:v", "high", "-level", "4.1", "-movflags", "+faststart",
           "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-shortest", out]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL)
    total = int(DURATION * FPS)
    for i in range(total):
        proc.stdin.write(frame(i / FPS).tobytes())
        if i % 120 == 0:
            print(f"  {i}/{total}", flush=True)
    proc.stdin.close()
    proc.wait()
    print("wrote", out)


if __name__ == "__main__":
    main()
