# -*- coding: utf-8 -*-
"""12/84 sayfa içi animasyonu: 15 seçenekten 276 seçeneğe.

Her iki duvar noktası arasında bir mekân kurulabilir; seçenek sayısı nokta
çiftlerinin sayısıdır. Geleneksel sistemde 6 duvar noktası 15 çift verir,
12/84'te 24 duvar noktası 276 çift (sayfadaki Mekansal Uyum İndeksi).

Noktalar iki panelde de aynı hızla eklenir; her yeni nokta öncekilerin
hepsine bir yayla bağlanır. Sol panel 6. noktada durur, sağ panel 24'e
kadar büyümeye devam eder. Sayaçlar yaylarla birlikte artar.

Kullanım:  python motion/1284-pairs.py            -> motion/1284-pairs.svg
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit                                              # noqa: E402
from kit import f, pc, seg, quad, draw_path, text       # noqa: E402

kit.seed(276)
NS = "m1284p"

# ------------------------------------------------------------------ geometri
W, H = 1200, 390
PX = (40, 640)             # panellerin sol kenarı
BX0, BX1 = 20, 500         # ilk ve son duvar noktası (panel içi)
BY = 300                   # yayların oturduğu çizgi
BT = 10                    # cephe bandının kalınlığı
N_L, N_R = 6, 24           # duvar noktası sayıları

# döngüde sırayla öne çıkan örnek mekânlar (nokta çiftleri)
SHOW_L = [(1, 3), (0, 1), (2, 5), (0, 5), (3, 4)]
SHOW_R = [(5, 17), (2, 6), (9, 21), (0, 23), (14, 15)]

# ------------------------------------------------------------------ zamanlama (sn)
T0 = 1.2                   # ilk noktanın eklendiği an
DT = 0.24                  # iki nokta arası
ARC_T = 0.4                # bir yayın çizilme süresi
HL_STEP = 1.6              # bir örnek mekânın ekranda kaldığı süre
T_HL0 = T0 + N_R * DT + 0.7


def px(n, k):
    return BX0 + (BX1 - BX0) * k / (n - 1)


def pairs(k):
    return k * (k - 1) // 2


# ------------------------------------------------------------------ panel
def arc(x_from, x_to):
    r = abs(x_to - x_from) / 2
    return f"M{f(x_from)} {BY}A{f(r)} {f(r)} 0 0 0 {f(x_to)} {BY}"


def panel(idx, n, title, shows, d0):
    side = "pl" if idx == 0 else "pr"
    o = [f'<g class="p p{idx + 1} {side}">']
    o.append(text(BX0 - 6, 28, title, "ttl fade", "CONVENTIONAL" if idx == 0 else None, f' style="--d:{pc(d0 + 0.2)}s"'))

    # sayaç ve birimi
    o.append(f'<text class="num" x="{BX0 - 8}" y="84" data-count="">{pairs(n)}</text>')
    o.append(text(BX0 - 6, 106, "seçenek", "unit", "options"))

    # cephe bandı
    o.append(f'<rect class="poche fade" x="{BX0 - 12}" y="{BY}" width="{BX1 - BX0 + 24}" height="{BT}" style="--d:{pc(d0 + 0.6)}s"/>')
    o.append(draw_path("ink", seg(BX0 - 18, BY, BX1 + 19, BY, 0.4, 0, 1.0), d0 + 0.1))
    o.append(draw_path("ink", seg(BX0 - 16, BY + BT, BX1 + 17, BY + BT, 0.4, 0, 1.0), d0 + 0.18))

    # yaylar: her yeni nokta öncekilerin hepsine bağlanır
    o.append('<g class="arcs">')
    for k in range(1, n):
        t = T0 + k * DT
        # yay başına bir yol: çizilme hareketi her yayda baştan başlasın
        o.append(f'<g style="--d:{pc(t)}s;--t:{pc(ARC_T)}s">'
                 + "".join(f'<path class="arc draw" pathLength="1" d="{arc(px(n, k), px(n, i))}"/>' for i in range(k - 1, -1, -1))
                 + "</g>")
    o.append("</g>")

    # örnek mekânlar: bir yay, iki duvar ve aralarındaki açıklık
    pw = 10 if n == N_L else 5
    for j, (a, b) in enumerate(shows):
        xa, xb = px(n, a), px(n, b)
        o.append(f'<g class="hl{" hl0" if j == 0 else ""}" style="--d:{pc(T_HL0 + j * HL_STEP)}s">'
                 f'<path class="hla" d="{arc(xb, xa)}"/>'
                 f'<rect class="hlb" x="{f(xa)}" y="{BY + BT + 9}" width="{f(xb - xa)}" height="8" rx="4"/>'
                 f'<rect class="hlw" x="{f(xa - pw / 2 - 1)}" y="{BY - 2}" width="{pw + 2}" height="{BT + 22}" rx="1.5"/>'
                 f'<rect class="hlw" x="{f(xb - pw / 2 - 1)}" y="{BY - 2}" width="{pw + 2}" height="{BT + 22}" rx="1.5"/>'
                 f'</g>')

    # duvar noktaları
    for k in range(n):
        o.append(f'<path class="solid pop" d="{quad(px(n, k), BY + BT / 2, pw, BT + 2, 0.4)}" '
                 f'style="--d:{pc(T0 + k * DT - 0.05)}s;--t:.3s"/>')

    label_tr = f"{n} duvar noktası"
    label_en = f"{n} wall points"
    o.append(text((BX0 + BX1) / 2, BY + BT + 56, label_tr, "unit mid fade", label_en, f' style="--d:{pc(d0 + 0.9)}s"'))
    o.append("</g>")
    return o


# ------------------------------------------------------------------ stil
def kf_count(name, n):
    rows = "".join(f"{pc(k / n * 100)}%{{--motion-count:{pairs(k)}}}" for k in range(n + 1))
    return f"@keyframes {NS}-{name}{{{rows}}}"


def css():
    cyc = HL_STEP * len(SHOW_L)
    on0, on1, off0 = 0.25 / cyc * 100, (HL_STEP - 0.05) / cyc * 100, (HL_STEP + 0.25) / cyc * 100
    return f"""
{kit.base_css(NS)}
.{NS} .p1{{transform:translate({PX[0]}px,0)}}
.{NS} .p2{{transform:translate({PX[1]}px,0)}}
.{NS} .arc{{fill:none;stroke-linecap:round}}
.{NS} .pl .arc{{stroke:var(--ink2);stroke-width:1.3;opacity:.85}}
.{NS} .pr .arc{{stroke:var(--hot);stroke-width:1;opacity:.6}}
.{NS} .ttl{{font-size:15px;letter-spacing:.1em;fill:var(--ink3)}}
.{NS} .num{{font-size:46px;font-weight:600;fill:var(--ink);--motion-count:{pairs(N_L)};animation:{NS}-cl {pc(N_L * DT)}s linear {T0}s both}}
.{NS} .pr .num{{fill:var(--hot);--motion-count:{pairs(N_R)};animation:{NS}-cr {pc(N_R * DT)}s linear {T0}s both}}
.{NS} .unit{{font-size:14px;fill:var(--ink3)}}
.{NS} .mid{{text-anchor:middle}}
.{NS} .hl{{opacity:0;animation:{NS}-hl {pc(cyc)}s linear var(--d) infinite backwards}}
.{NS} .hl0{{opacity:1}}
.{NS} .hla{{fill:none;stroke:var(--ink);stroke-width:2.6;stroke-linecap:round}}
.{NS} .hlb{{fill:var(--ink);fill-opacity:.85}}
.{NS} .hlw{{fill:var(--ink)}}
@keyframes {NS}-hl{{0%{{opacity:0}}{pc(on0)}%,{pc(on1)}%{{opacity:1}}{pc(off0)}%,100%{{opacity:0}}}}
{kf_count("cl", N_L)}
{kf_count("cr", N_R)}
@media (min-width:769px) and (max-width:1100px){{.{NS} .ttl{{font-size:19px}}.{NS} .unit{{font-size:18px}}}}
@media (max-width:768px){{.{NS} .root{{transform:scale(2)}}.{NS} .p2{{transform:translate({PX[0]}px,{H}px)}}{kit.base_css_mobile(NS)}.{NS} .pl .arc{{stroke-width:1.9}}.{NS} .pr .arc{{stroke-width:1.5}}.{NS} .hla{{stroke-width:3.4}}.{NS} .ttl{{font-size:19px}}.{NS} .unit{{font-size:20px}}}}
""".strip()


# ------------------------------------------------------------------ çizim
def build():
    o = [kit.svg_open(NS, W, H, "xMidYMin meet"), f"<style>{css()}</style>", '<g class="root">']
    o += panel(0, N_L, "GELENEKSEL", SHOW_L, 0)
    o += panel(1, N_R, "12/84", SHOW_R, 0.15)
    o.append("</g></svg>")
    return "\n".join(o)


if __name__ == "__main__":
    assert pairs(N_L) == 15 and pairs(N_R) == 276
    assert len(SHOW_L) == len(SHOW_R)
    here = os.path.dirname(os.path.abspath(__file__))
    kit.write(sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, "1284-pairs.svg"), build())
