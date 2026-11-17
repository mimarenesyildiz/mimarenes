# -*- coding: utf-8 -*-
"""Tasarım Fakültesi başlık animasyonunun üreteci.

Solda kentin 8 metrelik parsel ritmi; içlerinden bir ölçü ayrılır ve 8 x 40
metrelik modül olur. Modül, 20 metre yarıçaplı çekirdeğin çevresinde her
adımda 30 derece dönerek çoğalır; altı adım sonra ilk modüle paralel, ama
kaymış yedinci modül oluşur. Sağda modüllerin üç yüksekliği: 8, 12, 16 metre.

Yedi modülün yeri ve açısı sayfadaki program organizasyon eskizinden
(tasarim-fakultesi-5) alınmıştır; ölçüler (8 m, 40 m, 20 m, 30 derece) modül
ölçü diyagramındandır. Hangi kolun hangi yükseklikte olduğu sayfada
yazmadığı için yükseklikler kollara dağıtılmadan, ayrı bir şema olarak çizilir.

Kullanım:  python motion/tasarim-fakultesi-header.py   -> motion/tasarim-fakultesi-header.svg
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit                                                   # noqa: E402
from kit import f, pc, seg, rect_sk, quad, draw_path, text   # noqa: E402

kit.seed(2013)
NS = "mtf"

# ------------------------------------------------------------------ geometri
W, H = 1200, 420
U = 3.75                       # 1 metre = 3,75 birim
MOD_W, MOD_L = 8 * U, 40 * U   # modül: 8 m x 40 m
R = 20 * U                     # çekirdek: 20 m yarıçap
CX, CY = 600, 212              # çekirdeğin merkezi
STEP = 30                      # her adımda dönüş (derece)

# eskizdeki yedi modül: (merkez x, merkez y) eskiz pikseli, açı sırasıyla 0, 30, ... 180
SK_C, SK_S = (515, 322), 0.5   # eskizde çekirdeğin merkezi ve piksel -> birim
SKETCH = [(255, 248), (417, 125), (597, 185), (633, 343), (522, 442), (385, 396), (350, 322)]
MODS = [(CX + (x - SK_C[0]) * SK_S, CY + (y - SK_C[1]) * SK_S, STEP * k) for k, (x, y) in enumerate(SKETCH)]

LOT_X0, LOT_Y0, LOT_N, LOT_D = 78, 150, 8, 96      # parsel sırası: 8 m'lik parseller
LOT_PICK = 5                                       # modüle dönüşen parsel
HEIGHTS = [8, 12, 16]
HX0, HY0, HGAP = 772, 306, 14

# ------------------------------------------------------------------ zamanlama (sn)
T = 14.0
D0 = 1.5
T_S0, S_DT, S_T = 0.9, 0.95, 0.75      # ilk çoğalma, adımlar arası, bir adımın süresi
T_H0 = T_S0 + S_DT * 5 + S_T + 0.2     # yükseklikler
T_DIP0, T_DIP1, T_RESET, T_UP0, T_UP1 = 12.4, 12.8, 13.0, 13.2, 13.6
EASE = "cubic-bezier(.6,0,.25,1)"


def p(t):
    return pc(t / T * 100)


R0, R1 = p(T_RESET - 0.01), p(T_RESET)


def pose(k):
    x, y, a = MODS[k]
    return f"translate({pc(x)}px,{pc(y)}px) rotate({a}deg)"


# ------------------------------------------------------------------ parçalar
def module(k):
    hl, hw = MOD_L / 2, MOD_W / 2
    cls = "mod" if k == 0 else f"mod m{k}"
    return (f'<g class="{cls}"><rect class="mfill" x="{f(-hl)}" y="{f(-hw)}" width="{f(MOD_L)}" height="{f(MOD_W)}"/>'
            f'<path class="mline" d="{rect_sk(-hl, -hw, MOD_L, MOD_W, 0.4, 2.2)}"/></g>')


def lots():
    """Kentin ritmi: yan yana 8 metrelik parseller, içlerinde farklı derinlikte yapılar."""
    o = []
    x1 = LOT_X0 + LOT_N * MOD_W
    o.append(draw_path("ink", seg(LOT_X0 - 14, LOT_Y0, x1 + 14, LOT_Y0, 0.4, 0, 0.8), 0.15, 0.7))       # sokak çizgisi
    depth = [70, 84, 62, 78, 90, 96, 66, 80]
    for i in range(LOT_N + 1):
        x = LOT_X0 + i * MOD_W
        o.append(draw_path("ink h", seg(x, LOT_Y0, x, LOT_Y0 + LOT_D, 0.3, 0, 0.4), 0.3 + i * 0.04, 0.5))
    for i in range(LOT_N):
        x = LOT_X0 + i * MOD_W
        cls = "lot pick" if i == LOT_PICK else "lot"
        o.append(f'<path class="{cls} fade" d="{quad(x + MOD_W / 2, LOT_Y0 + depth[i] / 2 + 2, MOD_W - 7, depth[i], 0.5)}" '
                 f'style="--d:{pc(0.55 + i * 0.05)}s"/>')
    # ölçü: 8 m
    xa, xb, yd = LOT_X0 + LOT_PICK * MOD_W, LOT_X0 + (LOT_PICK + 1) * MOD_W, LOT_Y0 - 14
    o.append(f'<g class="fade" style="--d:1s"><path class="dim" d="M{f(xa)} {yd}H{f(xb)}M{f(xa)} {yd - 5}v10M{f(xb)} {yd - 5}v10"/>'
             + text((xa + xb) / 2, yd - 9, "8", "num mid") + "</g>")
    # parselden modüle giden ok
    ax0, ay = LOT_X0 + LOT_N * MOD_W + 14, LOT_Y0 + 26
    ax1 = MODS[0][0] - MOD_L / 2 - 16
    o.append(f'<path class="arrow fade" d="M{f(ax0)} {ay}H{f(ax1)}m-9 -7l9 7l-9 7" style="--d:1.2s"/>')
    return o


def core():
    o = []
    hatch = "".join(f"M{f(CX - R + i * 14 - 60)} {f(CY + R)}l{f(2 * R * 0.9)} {f(-2 * R)}" for i in range(14))
    o.append(f'<g class="fade" style="--d:.7s" clip-path="url(#{NS}-core)"><path class="hatch" d="{hatch}"/></g>')
    o.append(f'<circle class="core draw" pathLength="1" cx="{CX}" cy="{CY}" r="{f(R)}" style="--d:.35s;--t:.9s"/>')
    # yarıçap: 20 m (çekirdeğin altında, modüllerin dışında)
    yd = CY + R + 26
    o.append(f'<g class="fade" style="--d:1.1s"><path class="dim" d="M{CX} {f(yd)}H{f(CX + R)}M{CX} {f(yd - 5)}v10M{f(CX + R)} {f(yd - 5)}v10"/>'
             + text(CX + R / 2, yd + 19, "20", "num mid") + "</g>")
    # dönüş: iki modül ekseni arasındaki 30 derece
    ax, ay, rl, ra = 392, 96, 66, 44
    a = math.radians(STEP)
    o.append(f'<g class="fade" style="--d:1.2s"><path class="dim" d="M{ax + rl} {ay}H{ax}L{f(ax + rl * math.cos(a))} {f(ay + rl * math.sin(a))}"/>'
             f'<path class="arrow" d="M{ax + ra} {ay}A{ra} {ra} 0 0 1 {f(ax + ra * math.cos(a))} {f(ay + ra * math.sin(a))}"/>'
             + text(ax + ra + 26, ay + 20, "30°", "num mid") + "</g>")
    return o


def heights():
    """Üç yükseklik: 8, 12, 16 m (modülün dar yüzünden bakış)."""
    o = []
    x1 = HX0 + 3 * MOD_W + 2 * HGAP
    o.append(draw_path("ink", seg(HX0 - 12, HY0, x1 + 12, HY0, 0.4, 0, 0.6), 0.9, 0.6))
    for i, h in enumerate(HEIGHTS):
        x, hu = HX0 + i * (MOD_W + HGAP), h * U
        o.append(f'<g class="hb h{i}"><rect class="mfill" x="{f(x)}" y="{f(HY0 - hu)}" width="{f(MOD_W)}" height="{f(hu)}"/>'
                 f'<path class="mline" d="{rect_sk(x, HY0 - hu, MOD_W, hu, 0.4, 1.8)}"/>'
                 + text(x + MOD_W / 2, HY0 - hu - 9, str(h), "num mid") + "</g>")
    return o


# ------------------------------------------------------------------ stil
def kf(name, *rows):
    return f"@keyframes {NS}-{name}{{{''.join(rows)}}}"


def keyframes():
    out = []
    for k in range(1, len(MODS)):
        t = T_S0 + (k - 1) * S_DT
        a, b = pose(k - 1), pose(k)
        out.append(kf(f"m{k}",
                      f"0%,{p(t)}%{{transform:{a};opacity:0;color:var(--hot)}}",
                      f"{p(t + 0.02)}%{{transform:{a};opacity:1;color:var(--hot);animation-timing-function:{EASE}}}",
                      f"{p(t + S_T)}%{{transform:{b};opacity:1;color:var(--hot)}}",
                      f"{p(t + S_T + 0.4)}%,{R0}%{{transform:{b};opacity:1;color:var(--ink)}}",
                      f"{R1}%,100%{{transform:{a};opacity:0;color:var(--hot)}}"))
    for i in range(len(HEIGHTS)):
        t = T_H0 + i * 0.3
        out.append(kf(f"h{i}", f"0%,{p(t)}%{{transform:scaleY(0);opacity:0}}", f"{p(t + 0.02)}%{{transform:scaleY(0);opacity:1;animation-timing-function:{EASE}}}",
                      f"{p(t + 0.6)}%,{R0}%{{transform:scaleY(1);opacity:1}}", f"{R1}%,100%{{transform:scaleY(0);opacity:0}}"))
    out.append(kf("dip", f"0%,{p(T_DIP0)}%{{opacity:1}}", f"{p(T_DIP1)}%,{p(T_UP0)}%{{opacity:0}}", f"{p(T_UP1)}%,100%{{opacity:1}}"))
    return "\n".join(out)


def css():
    loop = "var(--T) linear var(--d0) infinite backwards"
    mods = "".join(f".{NS} .m{k}{{transform:{pose(k)};animation:{NS}-m{k} {loop}}}" for k in range(1, len(MODS)))
    hbs = "".join(f".{NS} .h{i}{{animation:{NS}-h{i} {loop}}}" for i in range(len(HEIGHTS)))
    return f"""
{kit.base_css(NS)}
.{NS}{{--T:{T}s;--d0:{D0}s}}
.{NS} .mod{{color:var(--ink);transform:{pose(0)}}}
.{NS} .mfill{{fill:var(--hot);fill-opacity:.13}}
.{NS} .mline{{fill:none;stroke:currentColor;stroke-width:1.8;stroke-linecap:round}}
.{NS} .lot{{fill:var(--ink);fill-opacity:.1}}
.{NS} .lot.pick{{fill:var(--hot);fill-opacity:.45}}
.{NS} .core{{fill:none;stroke:var(--hot);stroke-width:1.8}}
.{NS} .hatch{{fill:none;stroke:var(--hot);stroke-width:1;opacity:.35}}
.{NS} .dim{{fill:none;stroke:var(--ink2);stroke-width:1.1;stroke-linecap:round}}
.{NS} .arrow{{fill:none;stroke:var(--ink2);stroke-width:1.4;stroke-linecap:round;stroke-linejoin:round}}
.{NS} .num{{font-size:15px;fill:var(--ink2)}}
.{NS} .mid{{text-anchor:middle}}
.{NS} .hb{{color:var(--ink);transform-box:fill-box;transform-origin:50% 100%}}
.{NS} .dyn{{animation:{NS}-dip {loop}}}
{mods}
{hbs}
{keyframes()}
@media (min-width:769px) and (max-width:1100px){{.{NS} .num{{font-size:19px}}}}
@media (max-width:768px){{.{NS} .lots{{display:none}}{kit.base_css_mobile(NS)}.{NS} .mline{{stroke-width:2.4}}.{NS} .core{{stroke-width:2.4}}.{NS} .dim{{stroke-width:1.6}}.{NS} .arrow{{stroke-width:2}}.{NS} .num{{font-size:22px}}}}
""".strip()


# ------------------------------------------------------------------ çizim
def build():
    o = [kit.svg_open(NS, W, H, "xMidYMid slice"), f"<style>{css()}</style>"]
    o.append(f'<defs><clipPath id="{NS}-core"><circle cx="{CX}" cy="{CY}" r="{f(R)}"/></clipPath></defs>')
    o.append('<g class="lots">')
    o += lots()
    o.append("</g>")
    o += core()
    # ilk modül: parselden gelen ölçü
    o.append(f'<g class="fade" style="--d:1.3s">{module(0)}</g>')
    o.append('<g class="dyn">')
    for k in range(1, len(MODS)):
        o.append(module(k))
    o += heights()
    o.append("</g></svg>")
    return "\n".join(o)


if __name__ == "__main__":
    assert MOD_L / MOD_W == 5 and R == MOD_L / 2                      # 8 x 40 m modül, 20 m yarıçap
    assert [m[2] for m in MODS] == [STEP * k for k in range(7)]       # her adım 30 derece
    for x, y, _ in MODS:                                              # modüller şeridin içinde kalsın
        assert 40 < x - MOD_L / 2 and x + MOD_L / 2 < W - 40 and 30 < y - MOD_L / 2 and y + MOD_L / 2 < H - 20, (x, y)
    here = os.path.dirname(os.path.abspath(__file__))
    kit.write(sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, "tasarim-fakultesi-header.svg"), build())
