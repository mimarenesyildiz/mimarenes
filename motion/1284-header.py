# -*- coding: utf-8 -*-
"""12/84 başlık animasyonunun üreteci.

Bir ofis katının planı: kolonlar ve cephe ritmi sabit kalır, iç duvarlar her
beş yılda 96 cm'lik akslara oturarak yeni bir düzene kayar.

Sistemin kuralları çizimde de geçerlidir: duvarlar akslara (12 cm'lik
şeritlere) oturur; kapı bir modüle oturur. Kolonlar yalnızca cephe
sırasındadır ve iki aksın arasındaki 84 cm'lik açıklığı doldurur: ilk ve son
kolon ilk ve son açıklığa yaslanır, aradakiler eşit aralıkla dizilir.
Kolonun olduğu açıklıkta pencere yoktur.

Çıktı, kendi <style> bloğunu taşıyan tek bir SVG dosyasıdır; js/motion.js onu
sayfaya gömer. Renkler sayfanın tema değişkenlerinden gelir.

Kullanım:  python motion/1284-header.py            -> motion/1284-header.svg
           python motion/1284-header.py <çıktı.svg>

Hızı değiştirmek için S (bir adımın süresi) ve MOVE (duvarların kayma süresi)
yeterlidir. Düzenleri değiştirmek için STATES tablosuna bakın.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit                                                          # noqa: E402
from kit import f, pc, seg, rect_sk, quad, circ, wash, wash_round   # noqa: E402

kit.seed(1284)   # sabit tohum: her çalıştırmada aynı çizim

# ------------------------------------------------------------------ geometri
W, H = 1200, 420
M = 40                      # 1 aks = 96 cm (12 cm duvar + 84 cm açıklık)
N = 28                      # aks sayısı
X0 = (W - N * M) / 2        # ilk aks
Y_FO, Y_FI = 28, 38         # cephe dış / iç yüzü
Y_GL = (Y_FO + Y_FI) / 2    # cam çizgisi
DEPTH = 6 * M
Y_C = Y_FI + DEPTH          # koridor duvarı ekseni
WALL = 5                    # 12 cm duvar
COL = M - WALL              # kolon iki aksın arasındaki 84 cm'lik açıklığı doldurur
COL_STEP = 9                # iki kolon arası (modül); N - 1'i tam bölmeli
COL_MODS = list(range(0, N, COL_STEP))   # 0, 9, 18, 27: ilk ve son açıklığa yaslı, araları eşit.
                                         # Yalnızca cephe sırasında; bu açıklıklarda pencere yok.

TL_Y = 356                  # zaman çizgisi
TL_X0, TL_STEP, TL_N = 330, 36, 16   # 2025 .. 2100, beş yıllık adımlar
YEAR0 = 2025

# her durum: (ad, beş hareketli duvarın aksı, oda tipleri)
STATES = [
    ("a", [4, 8, 12, 19, 24], ["duo", "round", "duo", "open", "meet", "duo"]),
    ("b", [3, 6, 14, 21, 25], ["solo", "solo", "board", "open", "round", "solo"]),
    ("c", [5, 10, 13, 16, 23], ["duo", "meet", "solo", "solo", "open", "meet"]),
    ("d", [6, 9, 16, 20, 25], ["team", "solo", "open", "round", "meet", "solo"]),
]

# ------------------------------------------------------------------ zamanlama (sn)
S = 3.2          # bir adım (5 yıl)
MOVE = 1.0       # duvarların kayma süresi
D0 = 2.7         # ilk kaymanın başladığı an
MK = 0.6         # zaman işaretçisinin ilerleme süresi
L = 4 * S        # plan döngüsü
B = TL_N * S     # 75 yıllık büyük döngü
EASE = "cubic-bezier(.7,0,.2,1)"


def ax(i):
    return X0 + M * i


def tx(j):
    return TL_X0 + TL_STEP * j


# ------------------------------------------------------------------ mobilya
SEAT = 7
YD = Y_FI + 70      # çalışma masası ekseni
YT = Y_FI + 108     # toplantı masası ekseni


def seats(points):
    return f'<path class="seat" d="{"".join(circ(x, y, SEAT) for x, y in points)}"/>'


def desk(cx, cy, w=66, h=32):
    x, y = cx - w / 2, cy - h / 2
    return [wash(x, y, w, h), f'<path class="fur" d="{rect_sk(x, y, w, h)}"/>',
            seats([(cx, cy + h / 2 + 11)])]


def cabinet(x, y=166, w=14, h=62):
    return [f'<path class="fur" d="{rect_sk(x, y, w, h, 0.3, 1.2)}"/>']


def stadium(cx, cy, w, h):
    x, y = cx - w / 2, cy - h / 2
    return [wash(x, y, w, h, h / 2),
            f'<rect class="fur" x="{f(x)}" y="{f(y)}" width="{w}" height="{h}" rx="{h / 2}"/>']


def bench_v(cx, cy, w=64, h=132):
    x, y = cx - w / 2, cy - h / 2
    d = rect_sk(x, y, w, h) + seg(cx, y, cx, y + h, 0.3, 0, 0.4) + seg(x, cy, x + w, cy, 0.3, 0, 0.3)
    pts = [(cx - w / 2 - 12, cy - h / 4), (cx - w / 2 - 12, cy + h / 4),
           (cx + w / 2 + 12, cy - h / 4), (cx + w / 2 + 12, cy + h / 4)]
    return [wash(x, y, w, h), f'<path class="fur" d="{d}"/>', seats(pts)]


def bench_h(cx, cy, w=132, h=64):
    x, y = cx - w / 2, cy - h / 2
    d = rect_sk(x, y, w, h) + seg(x, cy, x + w, cy, 0.3, 0, 0.4) + seg(cx, y, cx, y + h, 0.3, 0, 0.3)
    pts = [(cx - w / 4, cy - h / 2 - 12), (cx + w / 4, cy - h / 2 - 12),
           (cx - w / 4, cy + h / 2 + 12), (cx + w / 4, cy + h / 2 + 12)]
    return [wash(x, y, w, h), f'<path class="fur" d="{d}"/>', seats(pts)]


def round_table(cx, cy, r=27, n=4, rot=45):
    pts = []
    for k in range(n):
        a = math.radians(rot + 360 / n * k)
        pts.append((cx + (r + 14) * math.cos(a), cy + (r + 14) * math.sin(a)))
    return [wash_round(cx, cy, r), f'<circle class="fur" cx="{f(cx)}" cy="{f(cy)}" r="{r}"/>', seats(pts)]


DOOR = M - WALL     # kapı da bir modüle oturur: 84 cm


def door_side(kind, idx):
    """Kapı odanın hangi ucunda: True sağ uç, False sol uç."""
    return kind != "team" and idx % 2 == 1


def door_module(i0, i1, flip):
    """Kapının oturduğu modül: odanın sol ya da sağ ucundaki açıklık."""
    return (i1 - 1) if flip else i0


def door(mod, flip=False):
    """Koridor duvarında açık kapı: bir modülün açıklığını doldurur (boşluk + kanat + yay)."""
    xa, xb = ax(mod) + WALL / 2, ax(mod + 1) - WALL / 2
    xh, x1 = (xb, xa) if flip else (xa, xb)     # menteşe duvar tarafında
    return [
        f'<rect class="cover" x="{f(min(xh, x1))}" y="{f(Y_C - 5)}" width="{DOOR}" height="10"/>',
        f'<path class="jamb" d="M{f(xh)} {f(Y_C - 3.3)}V{f(Y_C + 3.3)}M{f(x1)} {f(Y_C - 3.3)}V{f(Y_C + 3.3)}"/>',
        f'<path class="fur" d="{seg(xh, Y_C - 2.5, xh, Y_C - DOOR, 0.3, 0, 0.3)}"/>',
        f'<path class="fur arc" d="M{f(xh)} {f(Y_C - DOOR)}A{DOOR} {DOOR} 0 0 {0 if flip else 1} {f(x1)} {f(Y_C)}"/>',
    ]


def room(kind, i0, i1, idx):
    xl, xr = ax(i0), ax(i1)
    cx = (xl + xr) / 2
    wmod = i1 - i0
    flip = door_side(kind, idx)
    out = []
    if kind == "solo":
        out += desk(cx, YD)
        out += cabinet(xl + 9) if flip else cabinet(xr - 9 - 14)
    elif kind == "duo":
        off = 37 if wmod <= 4 else 46
        out += desk(cx - off, YD) + desk(cx + off, YD)
    elif kind == "round":
        out += round_table(cx, YT + 2, 27, 4, 45 if idx % 2 else 0)
    elif kind == "meet":
        out += stadium(cx, YT, 116, 46)
        out.append(seats([(cx + dx, YT + sy * 36) for sy in (-1, 1) for dx in (-34, 0, 34)]
                         + [(cx - 71, YT), (cx + 71, YT)]))
    elif kind == "board":
        out += stadium(cx, YT, 214, 52)
        out.append(seats([(cx + dx, YT + sy * 39) for sy in (-1, 1) for dx in (-80, -40, 0, 40, 80)]
                         + [(cx - 120, YT), (cx + 120, YT)]))
    elif kind == "open":
        out += bench_v(cx - 70, Y_FI + 110) + bench_v(cx + 70, Y_FI + 110)   # cephe kolonuna pay bırak
    elif kind == "team":
        out += bench_h(cx - 18, Y_FI + 112)
        out += round_table(xr - 48, Y_C - 56, 17, 2, 180)
    out += door(door_module(i0, i1, flip), flip)
    return out


# ------------------------------------------------------------------ keyframe'ler
def kf_wall(k):
    pos = [st[1][k] for st in STATES]
    mv = MOVE / L * 100
    rows = []
    for s in range(4):
        cur = (pos[s] - pos[0]) * M
        nxt = (pos[(s + 1) % 4] - pos[0]) * M
        rows.append(f"{pc(s * 25)}%{{transform:translateX({cur}px);animation-timing-function:{EASE}}}")
        rows.append(f"{pc(s * 25 + mv)}%{{transform:translateX({nxt}px)}}")
    rows.append("100%{transform:translateX(0)}")
    return f"@keyframes m1284-w{k + 1}{{{''.join(rows)}}}"


def kf_state(s):
    """Durum s, (s-1). adımın sonunda yerleşir, s. adımın başında toplanır."""
    def p(t):
        return pc(t / L * 100)
    ta = ((s - 1) % 4) * S + MOVE
    hidden = "opacity:0;transform:translateY(6px)"
    shown = "opacity:1;transform:translateY(0)"
    if s == 0:
        rows = [f"0%{{{shown}}}", f"{p(0.28)}%{{opacity:0;transform:translateY(0)}}",
                f"{p(ta - 0.2)}%{{{hidden}}}", f"{p(ta + 0.3)}%{{{shown}}}", f"100%{{{shown}}}"]
    else:
        td = s * S
        rows = [f"0%{{{hidden}}}", f"{p(ta - 0.2)}%{{{hidden}}}", f"{p(ta + 0.3)}%{{{shown}}}",
                f"{p(td)}%{{{shown}}}", f"{p(td + 0.28)}%{{opacity:0;transform:translateY(0)}}",
                f"100%{{opacity:0;transform:translateY(0)}}"]
    return f"@keyframes m1284-s{STATES[s][0]}{{{''.join(rows)}}}"


def kf_hit():
    def p(t):
        return pc(t / L * 100)
    return ("@keyframes m1284-hit{"
            f"0%,{p(MOVE - 0.14)}%{{opacity:0;transform:scale(.6)}}"
            f"{p(MOVE)}%{{opacity:1;transform:scale(1.9)}}"
            f"{p(MOVE + 0.8)}%,100%{{opacity:0;transform:scale(1)}}}}")


def kf_grid():
    def p(t):
        return pc(t / S * 100)
    base = "stroke:var(--ink3);opacity:.6"
    return (f"@keyframes m1284-grid{{0%{{{base}}}{p(MOVE * 0.35)}%,{p(MOVE)}%{{stroke:var(--hot);opacity:1}}"
            f"{p(MOVE + 0.7)}%,100%{{{base}}}}}")


def kf_marker(prop):
    """prop: 'x' işaretçi için öteleme, 'sx' ilerleme çubuğu için ölçek."""
    def p(t):
        return pc(t / B * 100)

    def val(j):
        return f"translateX({TL_STEP * j}px)" if prop == "x" else f"scaleX({pc(j / (TL_N - 1))})"
    rows = []
    for j in range(TL_N - 1):
        rows.append(f"{p(j * S)}%{{transform:{val(j)};animation-timing-function:{EASE}}}")
        rows.append(f"{p(j * S + MK)}%{{transform:{val(j + 1)}}}")
    t = (TL_N - 1) * S
    last = TL_N - 1
    rows.append(f"{p(t)}%{{transform:{val(last)};opacity:1}}")
    rows.append(f"{p(t + 0.25)}%{{transform:{val(last)};opacity:0}}")
    rows.append(f"{p(t + 0.26)}%{{transform:{val(0)};opacity:0}}")
    rows.append(f"{p(t + 0.6)}%,100%{{transform:{val(0)};opacity:1}}")
    return f"@keyframes m1284-{'mk' if prop == 'x' else 'pg'}{{{''.join(rows)}}}"


def kf_years():
    def p(t):
        return pc(t / B * 100)
    t = (TL_N - 1) * S
    return (f"@keyframes m1284-yr{{0%,{p(MK - 0.15)}%{{opacity:0}}{p(MK + 0.1)}%,{p(S)}%{{opacity:1}}"
            f"{p(S + 0.2)}%,100%{{opacity:0}}}}"
            f"@keyframes m1284-yr0{{0%{{opacity:1}}{p(0.2)}%,{p(t + 0.3)}%{{opacity:0}}"
            f"{p(t + 0.6)}%,100%{{opacity:1}}}}")


# ------------------------------------------------------------------ stil
def css():
    sg = [0, 0.07, 0.14, 0.21, 0.28]   # duvarlar soldan sağa hafif gecikmeli
    walls = "".join(
        f".m1284 .w{k + 1}{{animation:m1284-draw .5s cubic-bezier(.45,0,.2,1) {pc(1.35 + k * 0.09)}s backwards,"
        f"m1284-w{k + 1} calc(var(--s)*4) linear calc(var(--d0) + {pc(sg[k])}s) infinite}}"
        for k in range(5))
    states = "".join(
        f".m1284 .st-{STATES[s][0]}{{animation:m1284-s{STATES[s][0]} calc(var(--s)*4) linear var(--d0) infinite}}"
        for s in range(1, 4))
    return f"""
.m1284{{--s:{S}s;--d0:{D0}s;--ink:var(--gray-900,#1a1a1a);--ink2:var(--gray-600,#444);--ink3:var(--gray-400,#6b6b6b);--paper:var(--bg,#f8f8f8);--hot:var(--accent,#C56F34)}}
.m1284 .ink{{fill:none;stroke:var(--ink);stroke-width:1.7;stroke-linecap:round}}
.m1284 .ink.h{{stroke-width:1.2;opacity:.5}}
.m1284 .poche{{fill:var(--ink);fill-opacity:.1}}
.m1284 .jamb{{fill:none;stroke:var(--ink);stroke-width:1.6;stroke-linecap:round}}
.m1284 .solid{{fill:var(--ink)}}
.m1284 .grid{{fill:none;stroke:var(--ink3);stroke-width:1;stroke-dasharray:1.5 6;opacity:.6}}
.m1284 .wall{{fill:none;stroke:var(--hot);stroke-width:{WALL};stroke-dasharray:1 2}}
.m1284 .fur{{fill:none;stroke:var(--ink2);stroke-width:1.4;stroke-linecap:round;stroke-linejoin:round}}
.m1284 .top{{fill:var(--hot);fill-opacity:.17;stroke:none}}
.m1284 .seat{{fill:var(--paper);stroke:var(--ink2);stroke-width:1.3}}
.m1284 .cover{{fill:var(--paper);stroke:none}}
.m1284 .arc{{stroke-width:1;stroke-dasharray:2 3.5}}
.m1284 .hit{{fill:var(--hot);opacity:0;transform-box:fill-box;transform-origin:50% 50%;animation:m1284-hit calc(var(--s)*4) linear var(--d) infinite}}
.m1284 text{{font-family:var(--mono,'SF Mono','Fira Code',monospace);text-anchor:middle;letter-spacing:0;font-variant-numeric:tabular-nums;user-select:none}}
.m1284 .end{{font-size:16px;fill:var(--ink3)}}
.m1284 .yr{{font-size:26px;font-weight:600;fill:var(--hot);opacity:0;animation:m1284-yr calc(var(--s)*{TL_N}) linear var(--d) infinite}}
.m1284 .yr.y0{{opacity:1;animation:m1284-fade .4s ease 2.05s backwards,m1284-yr0 calc(var(--s)*{TL_N}) linear var(--d0) infinite}}
.m1284 .tick{{fill:none;stroke:var(--ink);stroke-width:1.6;stroke-linecap:round}}
.m1284 .pg{{fill:var(--hot);transform:scaleX(0);transform-box:fill-box;transform-origin:0 50%;animation:m1284-pg calc(var(--s)*{TL_N}) linear var(--d0) infinite}}
.m1284 .mk{{animation:m1284-mk calc(var(--s)*{TL_N}) linear var(--d0) infinite}}
.m1284 .dot{{fill:var(--hot);stroke:var(--paper);stroke-width:2.5}}
.m1284 .draw{{stroke-dasharray:1 2;animation:m1284-draw var(--t,.8s) cubic-bezier(.45,0,.2,1) var(--d,0s) backwards}}
.m1284 .pop{{transform-box:fill-box;transform-origin:50% 50%;animation:m1284-pop var(--t,.35s) cubic-bezier(.3,1.5,.5,1) var(--d,0s) backwards}}
.m1284 .fade{{animation:m1284-fade var(--t,.5s) ease var(--d,0s) backwards}}
.m1284 .grid{{animation:m1284-fade .5s ease var(--d,0s) backwards,m1284-grid var(--s) linear var(--d0) infinite}}
.m1284 .st{{opacity:0}}
.m1284 .st-a{{opacity:1;animation:m1284-rise .55s ease 1.75s backwards,m1284-sa calc(var(--s)*4) linear var(--d0) infinite}}
{states}
{walls}
@keyframes m1284-draw{{from{{stroke-dashoffset:1.01}}}}
@keyframes m1284-pop{{from{{transform:scale(0)}}}}
@keyframes m1284-fade{{from{{opacity:0}}}}
@keyframes m1284-rise{{from{{opacity:0;transform:translateY(6px)}}}}
{''.join(kf_wall(k) for k in range(5))}
{''.join(kf_state(s) for s in range(4))}
{kf_hit()}
{kf_grid()}
{kf_marker('x')}
{kf_marker('sx')}
{kf_years()}
@media (max-width:768px){{.m1284 .ink{{stroke-width:2.2}}.m1284 .ink.h{{stroke-width:1.8}}.m1284 .jamb{{stroke-width:2.2}}.m1284 .fur{{stroke-width:2}}.m1284 .seat{{stroke-width:1.8}}.m1284 .arc{{stroke-width:1.5}}.m1284 .grid{{stroke-width:1.6}}.m1284 .tick{{stroke-width:2.2}}.m1284 .yr{{font-size:30px}}.m1284 .end{{font-size:21px}}}}
""".strip()


# ------------------------------------------------------------------ çizim
def build():
    o = []
    o.append(f'<svg class="m1284" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
             f'preserveAspectRatio="xMidYMid slice" aria-hidden="true" focusable="false">')
    o.append(f"<style>{css()}</style>")

    # 1. aks ızgarası
    o.append('<g class="g-grid">')
    for i in range(1, N):
        o.append(f'<path class="grid fade" d="M{f(ax(i))} {Y_FI + 5}V{Y_C - 5}" style="--d:{pc(0.9 + i * 0.012)}s"/>')
    o.append("</g>")

    # 2. sabit kabuk: cephe, yan duvarlar, koridor duvarı
    def draw(cls, d, delay, t=0.9):
        return f'<path class="{cls} draw" pathLength="1" d="{d}" style="--d:{pc(delay)}s;--t:{pc(t)}s"/>'
    o.append('<g class="g-shell">')
    o.append(draw("ink", seg(ax(0) - 8, Y_FO, ax(N) + 8, Y_FO, 0.5, 0, 1.2), 0.10))
    o.append(draw("ink h", seg(ax(0) - 5, Y_FO + 0.8, ax(N) + 6, Y_FO - 0.6, 0.6, 0, 1.4), 0.16))
    o.append(draw("ink", seg(ax(0) - 4, Y_FI, ax(N) + 6, Y_FI, 0.5, 0, 1.2), 0.20))
    o.append(draw("ink h", seg(ax(0), Y_GL, ax(N), Y_GL, 0.3, 0, 0.6), 0.30))
    hw = WALL / 2
    for x, d0 in ((ax(0), 0.25), (ax(N), 0.85)):
        o.append(f'<rect class="poche fade" x="{f(x - hw)}" y="{Y_FI}" width="{WALL}" height="{f(Y_C - Y_FI)}" '
                 f'style="--d:{pc(d0 + 0.3)}s"/>')
        o.append(draw("ink", seg(x - hw, Y_FO - 6, x - hw, Y_C + 7, 0.4, 0, 0.9), d0, 0.55))
        o.append(draw("ink", seg(x + hw, Y_FO - 4, x + hw, Y_C + 6, 0.4, 0, 0.9), d0 + 0.06, 0.55))
    o.append(f'<rect class="poche fade" x="{f(ax(0))}" y="{f(Y_C - hw)}" width="{f(ax(N) - ax(0))}" height="{WALL}" '
             f'style="--d:1s"/>')
    o.append(draw("ink", seg(ax(0) - 7, Y_C - hw, ax(N) + 8, Y_C - hw, 0.4, 0, 1.1), 0.55))
    o.append(draw("ink", seg(ax(0) - 5, Y_C + hw, ax(N) + 6, Y_C + hw, 0.4, 0, 1.1), 0.62))
    o.append("</g>")

    # 3. her düzenin mobilyası ve kapıları
    for name, pos, kinds in STATES:
        bounds = [0] + pos + [N]
        o.append(f'<g class="st st-{name}">')
        for idx, kind in enumerate(kinds):
            o.extend(room(kind, bounds[idx], bounds[idx + 1], idx))
        o.append("</g>")

    # 4. hareketli duvarlar (a düzeninin konumunda çizilir, döngüyle ötelenir)
    o.append('<g class="g-walls">')
    for k, i in enumerate(STATES[0][1]):
        o.append(f'<path class="wall w{k + 1}" pathLength="1" d="M{f(ax(i))} {Y_FI}V{f(Y_C - WALL / 2)}"/>')
    o.append("</g>")

    # 5. cephe dikmeleri ve kolonlar
    o.append('<g class="g-struct">')
    for i in range(N + 1):
        o.append(f'<path class="solid pop" d="{quad(ax(i), Y_GL, WALL, Y_FI - Y_FO, 0.35)}" '
                 f'style="--d:{pc(0.25 + i * 0.024)}s;--t:.25s"/>')
    for m in COL_MODS:      # kolon iki aksın arasında, yalnızca cephe sırasında
        o.append(f'<path class="solid pop" d="{quad(ax(m) + M / 2, Y_FO + COL / 2, COL, COL, 0.9)}" '
                 f'style="--d:{pc(0.3 + m / N * 0.75)}s"/>')
    o.append("</g>")

    # 6. duvarın dikmeye oturduğu an
    sg = [0, 0.07, 0.14, 0.21, 0.28]
    o.append('<g class="g-hits">')
    for s, (name, pos, _) in enumerate(STATES):
        step = (s - 1) % 4
        prev = STATES[step][1]
        for k, i in enumerate(pos):
            if i == prev[k]:
                continue
            delay = f"calc(var(--d0) + var(--s)*{step} + {pc(sg[k])}s)"
            o.append(f'<rect class="hit" x="{f(ax(i) - 3.5)}" y="{Y_FO - 2}" width="7" height="{Y_FI - Y_FO + 4}" '
                     f'style="--d:{delay}"/>')
    o.append("</g>")

    # 7. zaman çizgisi: 75 yıl, beş yıllık adımlar
    o.append('<g class="g-time">')
    o.append(draw("ink", seg(tx(0) - 7, TL_Y, tx(TL_N - 1) + 7, TL_Y, 0.4, 0, 0.8), 1.2, 0.8))
    for j in range(TL_N):
        hgt = 7 if j in (0, TL_N - 1) else 4.5
        o.append(f'<path class="tick fade" d="M{f(tx(j))} {f(TL_Y - hgt)}V{f(TL_Y + hgt)}" '
                 f'style="--d:{pc(1.3 + j * 0.035)}s;--t:.3s"/>')
    o.append(f'<text class="end fade" x="{tx(0)}" y="{TL_Y + 27}" style="--d:1.9s">{YEAR0}</text>')
    o.append(f'<text class="end fade" x="{tx(TL_N - 1)}" y="{TL_Y + 27}" style="--d:1.95s">{YEAR0 + 5 * (TL_N - 1)}</text>')
    o.append(f'<rect class="pg" x="{tx(0)}" y="{TL_Y - 1.5}" width="{TL_STEP * (TL_N - 1)}" height="3"/>')
    o.append(f'<text class="yr y0" x="{tx(0)}" y="{TL_Y - 16}">{YEAR0}</text>')
    for j in range(1, TL_N):
        o.append(f'<text class="yr" x="{tx(j)}" y="{TL_Y - 16}" '
                 f'style="--d:calc(var(--d0) + var(--s)*{j - 1})">{YEAR0 + 5 * j}</text>')
    o.append(f'<g class="mk"><circle class="dot pop" cx="{tx(0)}" cy="{TL_Y}" r="7.5" style="--d:2s;--t:.4s"/></g>')
    o.append("</g>")

    o.append("</svg>")
    return "\n".join(o)


def check():
    """Her adımda her duvar yer değiştirmeli, sıra bozulmamalı, mobilya odaya sığmalı."""
    # kolonlar ilk ve son açıklığa yaslı, araları eşit
    assert COL_MODS[0] == 0 and COL_MODS[-1] == N - 1, COL_MODS
    need = {"solo": (3, 3), "duo": (4, 5), "round": (4, 4), "meet": (5, 5),
            "board": (8, 8), "open": (7, 7), "team": (6, 6)}
    for s in range(4):
        name, cur, kinds = STATES[s]
        nxt = STATES[(s + 1) % 4][1]
        assert cur == sorted(cur) and len(set(cur)) == 5, name
        assert all(a != b for a, b in zip(cur, nxt)), (name, cur, nxt)
        bounds = [0] + cur + [N]
        for i, kind in enumerate(kinds):
            lo, hi = need[kind]
            i0, i1 = bounds[i], bounds[i + 1]
            assert lo <= i1 - i0 <= hi, (name, kind)
            assert i0 <= door_module(i0, i1, door_side(kind, i)) < i1, (name, kind)


if __name__ == "__main__":
    check()
    here = os.path.dirname(os.path.abspath(__file__))
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, "1284-header.svg")
    out = build()
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(out + "\n")
    print(f"{path}: {len(out) / 1024:.1f} KB")
