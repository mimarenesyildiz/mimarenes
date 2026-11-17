# -*- coding: utf-8 -*-
"""12/84 sayfa içi animasyonu: her ölçü 12 cm'lik modülün tam katı.

Sayfadaki ispat görselinde geçen ölçüler birer çubuk olarak çizilir; her
çubuk 12 cm'lik kutulardan oluşur ve kutular tek tek dolar:

    duvar 12 · malzeme 60 · kullanım 84 · aks 96 · koridor 180 · tavan 264

Aks, bir duvar ile bir kullanım modülünün toplamıdır (12 + 84 = 96);
koridor iki kullanım modülü ile bir duvardır (2 x 84 + 12 = 180). Bu iki
çubukta duvar kutusu dolu, kullanım kutuları soluk vurgu rengindedir.

Kullanım:  python motion/1284-module.py            -> motion/1284-module.svg
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit                                        # noqa: E402
from kit import f, pc, seg, quad, text            # noqa: E402

kit.seed(1296)
NS = "m1284m"
M = 12                         # temel modül (cm)

# (ad, İngilizce ad, ölçü cm, kutu deseni: W duvar, O kullanım, . sade)
ROWS = [
    ("DUVAR", "WALL", 12, "W"),
    ("MALZEME", "MATERIAL", 60, "." * 5),
    ("KULLANIM", "USABLE", 84, "O" * 7),
    ("AKS", "AXIS", 96, "W" + "O" * 7),
    ("KORİDOR", "CORRIDOR", 180, "O" * 7 + "W" + "O" * 7),
    ("TAVAN", "CEILING", 264, "." * 22),
]

# ------------------------------------------------------------------ geometri
W, H = 1200, 372
X_NAME, X_VAL = 20, 172        # ad sola, ölçü sağa yaslı
BX = 190                       # çubukların başladığı yer
CP, CW, CH = 40, 35, 24        # kutu aralığı, eni, boyu
ROW_Y0, ROW_P = 46, 54         # ilk satır, satır aralığı
# dar ekran: ad üstte, çubuk altta ve daha kalın
M_ROW_Y0, M_ROW_P = 30, 122
M_DX = X_NAME - BX             # çubuğun sola kayması
M_BAR_Y, M_SY = 46, 1.7

# ------------------------------------------------------------------ zamanlama (sn)
T = 13.0
D0 = 0.9
T_FIRST, CELL_T, ROW_GAP = 1.0, 0.07, 0.25
T_DIP0, T_DIP1, T_RESET, T_UP0, T_UP1 = 11.4, 11.8, 12.0, 12.2, 12.6


def p(t):
    return pc(t / T * 100)


R0, R1 = p(T_RESET - 0.01), p(T_RESET)


def row_times():
    """Her satırın dolmaya başladığı ve bittiği an."""
    out, t = [], T_FIRST
    for _, _, cm, _ in ROWS:
        n = cm // M
        out.append((t, t + n * CELL_T))
        t += n * CELL_T + ROW_GAP
    return out


# ------------------------------------------------------------------ satır
def row(k, name, name_en, cm, pattern):
    n = len(pattern)
    x_end = BX + n * CP - (CP - CW)
    o = [f'<g class="row" style="--i:{k}">']
    o.append(text(X_NAME, 17, name, "nm fade", name_en, f' style="--d:{pc(0.2 + k * 0.07)}s"'))
    o.append(text(X_VAL, 17, str(cm), "vl fade", None, f' style="--d:{pc(0.25 + k * 0.07)}s"'))

    o.append('<g class="bar"><g class="cells">')
    for j, kind in enumerate(pattern):
        cls = {"W": "cw", "O": "co", ".": "cp"}[kind]
        o.append(f'<path class="{cls}" d="{quad(BX + j * CP + CW / 2, CH / 2, CW, CH, 0.7)}"/>')
    o.append("</g>")
    o.append(f'<rect class="cv cv{k}" x="{BX - 3}" y="-3" width="{f(x_end - BX + 6)}" height="{CH + 6}"/>')
    o.append("</g>")

    # çubuğun altındaki cetvel çizgisi: her 12 cm'de bir çentik
    ticks = "".join(f"M{BX + j * CP - (CP - CW) / 2 if j else BX} {CH + 3}v5" for j in range(n))
    ticks += f"M{f(x_end)} {CH + 3}v5"
    o.append(f'<g class="rule fade" style="--d:{pc(0.5 + k * 0.07)}s">'
             f'<path class="ink" d="{seg(BX - 4, CH + 5, x_end + 5, CH + 5, 0.4, 0, 0.6)}"/>'
             f'<path class="tk" d="{ticks}"/></g>')

    o.append(f'<g class="dyn">{text(x_end + 14, 17, f"{n} × {M}", f"ml ml{k}")}</g>')
    o.append("</g>")
    return o


# ------------------------------------------------------------------ stil
def keyframes():
    out = []
    for k, ((t0, t1), (_, _, cm, _)) in enumerate(zip(row_times(), ROWS)):
        n = cm // M
        out.append(f"@keyframes {NS}-cv{k}{{0%,{p(t0)}%{{transform:scaleX(1);animation-timing-function:steps({n},end)}}"
                   f"{p(t1)}%,{R0}%{{transform:scaleX(0)}}{R1}%,100%{{transform:scaleX(1)}}}}")
        out.append(f"@keyframes {NS}-ml{k}{{0%,{p(t1)}%{{opacity:0}}{p(t1 + 0.25)}%,{R0}%{{opacity:1}}{R1}%,100%{{opacity:0}}}}")
    out.append(f"@keyframes {NS}-dip{{0%,{p(T_DIP0)}%{{opacity:1}}{p(T_DIP1)}%,{p(T_UP0)}%{{opacity:0}}{p(T_UP1)}%,100%{{opacity:1}}}}")
    return "\n".join(out)


def css():
    loop = "var(--T) linear var(--d0) infinite backwards"
    per_row = "".join(f".{NS} .cv{k}{{animation:{NS}-cv{k} {loop}}}.{NS} .ml{k}{{animation:{NS}-ml{k} {loop}}}"
                      for k in range(len(ROWS)))
    return f"""
{kit.base_css(NS)}
.{NS}{{--T:{T}s;--d0:{D0}s}}
.{NS} .row{{transform:translateY(calc({ROW_Y0}px + var(--i) * {ROW_P}px))}}
.{NS} .nm{{font-size:14px;letter-spacing:.1em;fill:var(--ink3)}}
.{NS} .vl{{font-size:17px;font-weight:600;fill:var(--ink);text-anchor:end}}
.{NS} .ml{{font-size:14px;fill:var(--ink2)}}
.{NS} .cmu{{font-size:12px;fill:var(--ink3);text-anchor:end}}
.{NS} .cw{{fill:var(--hot)}}
.{NS} .co{{fill:var(--hot);fill-opacity:.3}}
.{NS} .cp{{fill:var(--ink);fill-opacity:.15}}
.{NS} .tk{{fill:none;stroke:var(--ink2);stroke-width:1.2;stroke-linecap:round}}
.{NS} .cv{{fill:var(--paper);transform:scaleX(0);transform-box:fill-box;transform-origin:100% 50%}}
.{NS} .cells,.{NS} .dyn{{animation:{NS}-dip {loop}}}
{per_row}
{keyframes()}
@media (min-width:769px) and (max-width:1100px){{.{NS} .nm{{font-size:18px}}.{NS} .ml{{font-size:18px}}.{NS} .vl{{font-size:21px}}.{NS} .cmu{{font-size:15px}}}}
@media (max-width:768px){{.{NS} .row{{transform:translateY(calc({M_ROW_Y0}px + var(--i) * {M_ROW_P}px))}}.{NS} .nm{{font-size:34px;transform:translateY(14px)}}.{NS} .vl{{font-size:38px;transform:translate(158px,14px)}}.{NS} .bar{{transform:translate({M_DX}px,{M_BAR_Y}px) scaleY({M_SY})}}.{NS} .rule{{transform:translate({M_DX}px,{pc(M_BAR_Y + CH * M_SY - CH)}px)}}.{NS} .ml{{font-size:34px;transform:translate({M_DX}px,{pc(M_BAR_Y + CH * M_SY / 2 - 6)}px)}}.{NS} .cmu{{font-size:30px;transform:translate(158px,-2px)}}.{NS} .ink{{stroke-width:3.6}}.{NS} .tk{{stroke-width:3}}}}
""".strip()


# ------------------------------------------------------------------ çizim
def build():
    o = [kit.svg_open(NS, W, H, "xMidYMin meet"), f"<style>{css()}</style>"]
    o.append(text(X_VAL, ROW_Y0 - 16, "cm", "cmu fade", None, ' style="--d:.2s"'))
    for k, (name, name_en, cm, pattern) in enumerate(ROWS):
        o += row(k, name, name_en, cm, pattern)
    o.append("</svg>")
    return "\n".join(o)


if __name__ == "__main__":
    for name, _, cm, pattern in ROWS:
        assert cm % M == 0 and len(pattern) == cm // M, name
    assert row_times()[-1][1] < T_DIP0 - 2
    here = os.path.dirname(os.path.abspath(__file__))
    kit.write(sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, "1284-module.svg"), build())
