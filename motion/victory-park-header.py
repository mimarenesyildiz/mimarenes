# -*- coding: utf-8 -*-
"""Victory Park başlık animasyonunun üreteci.

Solda cepheden bir parça: kat silmelerinin önünden yukarı uzanan taş kılıflar
(düşey dikmeler). Kılıflar sırayla seçilir; her biri, üç yüzü yan yana açılmış
ve panellere bölünmüş bir imalat paftasına dönüşüp ortadaki yığına iner.
Sayaç 7.436'ya ulaşır; sağda beş kule sırayla dolar.

Sayılar sayfadan: beş konut kulesi için toplam 7.436 teknik çizim. Pafta,
sayfadaki montaj şemasına benzer: üstte antet, ortada üç panel şeridi.
Yığındaki on pafta 7.436 çizimi temsil eder; birebir sayı değildir.

Geniş ekranda cephe, yığın ve kuleler yan yana görünür; dar ekranda çizimin
ortası (cephenin sağ yarısı ile yığın) büyütülür.

Kullanım:  python motion/victory-park-header.py   -> motion/victory-park-header.svg
"""
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit                                           # noqa: E402
from kit import f, pc, seg, draw_path, text          # noqa: E402

kit.seed(7436)
NS = "mvp"
TOTAL = 7436
TOWERS = 5

# ------------------------------------------------------------------ geometri
W, H = 1200, 420
GY = 372                        # zemin çizgisi
FLOOR_H, FLOORS = 54, 6
TOP = GY - FLOOR_H * FLOORS     # cephe parçasının üstü
PX0, PSTEP, PN, PW = 78, 36, 16, 9      # ilk kılıfın ekseni, aralık, sayı, en
BAND = 8                        # kat silmesi
PANEL = 12                      # bir taş panelin boyu (yaklaşık 72 cm)

SHEET_W, SHEET_H = 62, 88       # pafta (dik)
PILE_X, PILE_Y = 742, 300       # yığındaki ilk paftanın merkezi
PILE_DX, PILE_DY = 2.2, -5.5    # her yeni paftanın kayması
PICKS = [8, 12, 3, 10, 14, 6, 11, 1, 13, 9]     # seçilen kılıfların sırası

TW_X0, TW_STEP, TW_W = 962, 40, 26
TW_H = [150, 172, 190, 172, 150]

# ------------------------------------------------------------------ zamanlama (sn)
T = 14.0
D0 = 1.6
T_F0, DT, FLY = 0.8, 0.75, 0.7  # ilk uçuş, uçuşlar arası, uçuş süresi
T_END = T_F0 + (len(PICKS) - 1) * DT + FLY
T_DIP0, T_DIP1, T_RESET, T_UP0, T_UP1 = 12.4, 12.8, 13.0, 13.2, 13.6
EASE = "cubic-bezier(.6,0,.25,1)"

rot = random.Random(11)
PILE_ROT = [round(rot.uniform(-3.5, 3.5), 1) for _ in PICKS]


def p(t):
    return pc(t / T * 100)


R0, R1 = p(T_RESET - 0.01), p(T_RESET)


def pil_x(k):
    return PX0 + PSTEP * k


def pile_xy(j):
    return PILE_X + PILE_DX * j, PILE_Y + PILE_DY * j


# ------------------------------------------------------------------ cephe
def facade():
    o = []
    x0, x1 = pil_x(0) - PW / 2, pil_x(PN - 1) + PW / 2
    o.append(draw_path("ink", seg(x0 - 34, GY, x1 + 36, GY, 0.5, 0, 1.2), 0.1, 0.9))
    o.append(draw_path("ink h", seg(x0 - 22, GY + 4, x1 + 20, GY + 4.6, 0.5, 0, 1.2), 0.2, 0.9))
    # cam: kılıfların arası, kat silmelerinin altı
    glass = ""
    for k in range(PN - 1):
        gx = pil_x(k) + PW / 2 + 2.5
        gw = PSTEP - PW - 5
        for j in range(FLOORS):
            gy = TOP + FLOOR_H * j + BAND + 3
            glass += f"M{f(gx)} {f(gy)}h{f(gw)}v{FLOOR_H - BAND - 6}h{f(-gw)}z"
    o.append(f'<path class="glass fade" d="{glass}" style="--d:.9s;--t:.7s"/>')
    # kat silmeleri
    for j in range(FLOORS + 1):
        y = TOP + FLOOR_H * j
        if j < FLOORS:
            o.append(draw_path("ink h", seg(x0, y + BAND, x1, y + BAND, 0.3, 0, 0.8), 0.3 + j * 0.05, 0.8))
        if 0 < j < FLOORS:
            o.append(draw_path("ink h", seg(x0, y, x1, y, 0.3, 0, 0.8), 0.3 + j * 0.05, 0.8))
    o.append(draw_path("ink", seg(x0 - 4, TOP, x1 + 5, TOP, 0.4, 0, 1.0), 0.3, 0.8))
    # taş kılıflar: iki düşey çizgi ve panel derzleri
    n_joint = int((GY - TOP) // PANEL)
    for k in range(PN):
        x = pil_x(k)
        d = seg(x - PW / 2, TOP - 5, x - PW / 2, GY, 0.3, 0, 0.5) + seg(x + PW / 2, TOP - 4, x + PW / 2, GY, 0.3, 0, 0.5)
        d += "".join(f"M{f(x - PW / 2)} {GY - PANEL * (i + 1)}h{PW}" for i in range(n_joint - 1))
        o.append(f'<g class="fade" style="--d:{pc(0.45 + k * 0.04)}s;--t:.35s">'
                 f'<rect class="cover" x="{f(x - PW / 2)}" y="{TOP}" width="{PW}" height="{GY - TOP}"/>'
                 f'<path class="pil" d="{d}"/></g>')
    return o


# ------------------------------------------------------------------ pafta
def sheet_def():
    """Dik pafta: üstte antet, ortada üç panel şeridi, solda ölçü çizgisi, altta kesit ve not kutusu."""
    hw, hh = SHEET_W / 2, SHEET_H / 2
    y0, y1 = -hh + 16, hh - 20                       # şeritlerin üstü ve altı
    lines = (f"M{-hw} {-hh + 9}H{hw}M-8 {-hh}v9M12 {-hh}v9"          # antet
             f"M{-hw} {hh - 8}H{hw}M4 {hh - 8}v8"                     # not kutusu
             f"M-27 {y0}V{y1}M-29 {y0}h4M-29 {y1}h4"                  # ölçü çizgisi
             f"M-23 {hh - 16}l4 4h7v-5")                              # kesit
    strips = ""
    for x, w in ((-22, 13), (-4, 8.5), (10, 7)):
        joints = "".join(f"M{x} {y0 + 6 * i}h{w}" for i in range(1, int((y1 - y0) // 6)))
        strips += (f'<rect class="{NS}-st" x="{x}" y="{y0}" width="{w}" height="{y1 - y0}"/>'
                   f'<path class="{NS}-sl" d="{joints}"/>')
    return (f'<g id="{NS}-sheet"><rect class="{NS}-sh" x="{-hw}" y="{-hh}" width="{SHEET_W}" height="{SHEET_H}" rx="1.5"/>'
            f'{strips}<path class="{NS}-sl" d="{lines}"/></g>')


# ------------------------------------------------------------------ kuleler
def towers():
    o = []
    x0 = TW_X0 - 18
    x1 = TW_X0 + TW_STEP * (TOWERS - 1) + TW_W + 18
    o.append(draw_path("ink", seg(x0, GY, x1, GY, 0.4, 0, 0.8), 0.9, 0.6))
    for k in range(TOWERS):
        x, h = TW_X0 + TW_STEP * k, TW_H[k]
        d = seg(x, GY, x, GY - h, 0.3, 0, 0.4) + seg(x, GY - h, x + TW_W, GY - h, 0.3, 1.5, 0.3) + seg(x + TW_W, GY - h, x + TW_W, GY, 0.3, 0, 0.4)
        fins = "".join(f"M{f(x + TW_W * i / 5)} {GY - h + 4}V{GY - 3}" for i in range(1, 5))
        o.append(f'<path class="tw fade" d="{d}" style="--d:{pc(1.0 + k * 0.07)}s"/>')
        o.append(f'<path class="twl fade" d="{fins}" style="--d:{pc(1.1 + k * 0.07)}s"/>')
    return o


# ------------------------------------------------------------------ keyframe'ler
def kf(name, *rows):
    return f"@keyframes {NS}-{name}{{{''.join(rows)}}}"


def keyframes():
    out = []
    ymid = (TOP + GY) / 2
    sx0, sy0 = PW / SHEET_W, (GY - TOP) / SHEET_H
    fx, fy = [], []
    for j, k in enumerate(PICKS):
        t = T_F0 + j * DT
        px, (ex, ey) = pil_x(k), pile_xy(j)
        start = f"translateY({pc(ymid)}px) rotate(0deg) scale({pc(sx0)},{pc(sy0)})"
        end = f"translateY({pc(ey)}px) rotate({PILE_ROT[j]}deg) scale(1,1)"
        fx.append(f"{p(t)}%{{transform:translateX({pc(px)}px);animation-timing-function:{EASE}}}")
        fx.append(f"{p(t + FLY)}%{{transform:translateX({pc(ex)}px)}}")
        fy.append(f"{p(t - 0.01)}%{{transform:{start};opacity:0}}")
        fy.append(f"{p(t)}%{{transform:{start};opacity:1;animation-timing-function:{EASE}}}")
        fy.append(f"{p(t + FLY)}%{{transform:{end};opacity:1}}")
        fy.append(f"{p(t + FLY + 0.01)}%{{transform:{end};opacity:0}}")
        # seçilen kılıf: önce parlar, çizimi çıkınca soluk kalır
        out.append(kf(f"sel{j}", f"0%,{p(t - 0.3)}%{{opacity:0}}", f"{p(t - 0.05)}%,{p(t + 0.1)}%{{opacity:1}}",
                      f"{p(t + FLY)}%,{R0}%{{opacity:.3}}", f"{R1}%,100%{{opacity:0}}"))
        # yığındaki pafta: uçan pafta indiği an belirir
        out.append(kf(f"ps{j}", f"0%,{p(t + FLY)}%{{opacity:0}}", f"{p(t + FLY + 0.01)}%,{R0}%{{opacity:1}}", f"{R1}%,100%{{opacity:0}}"))
    first_x = f"translateX({pc(pil_x(PICKS[0]))}px)"
    out.append(kf("fx", f"0%{{transform:{first_x}}}", *fx, f"100%{{transform:{first_x}}}"))
    out.append(kf("fy", *fy, "100%{opacity:0}"))
    # sayaç: uçuşlar boyunca 0'dan 7.436'ya
    out.append(kf("cnt", f"0%,{p(T_F0)}%{{--motion-count:0}}", f"{p(T_END)}%,{R0}%{{--motion-count:{TOTAL}}}", f"{R1}%,100%{{--motion-count:0}}"))
    # kuleler: sayaç her beşte birini geçtikçe biri dolar
    for k in range(TOWERS):
        t = T_F0 + (T_END - T_F0) * (k + 1) / TOWERS
        out.append(kf(f"tw{k}", f"0%,{p(t - 0.3)}%{{opacity:0}}", f"{p(t)}%,{R0}%{{opacity:1}}", f"{R1}%,100%{{opacity:0}}"))
    out.append(kf("dip", f"0%,{p(T_DIP0)}%{{opacity:1}}", f"{p(T_DIP1)}%,{p(T_UP0)}%{{opacity:0}}", f"{p(T_UP1)}%,100%{{opacity:1}}"))
    return "\n".join(out)


# ------------------------------------------------------------------ stil
def css():
    loop = "var(--T) linear var(--d0) infinite backwards"
    per = "".join(f".{NS} .sel{j}{{animation:{NS}-sel{j} {loop}}}.{NS} .ps{j}{{animation:{NS}-ps{j} {loop}}}" for j in range(len(PICKS)))
    per += "".join(f".{NS} .twf{k}{{animation:{NS}-tw{k} {loop}}}" for k in range(TOWERS))
    return f"""
{kit.base_css(NS)}
.{NS}{{--T:{T}s;--d0:{D0}s}}
.{NS} .glass{{fill:var(--ink);fill-opacity:.07}}
.{NS} .pil{{fill:none;stroke:var(--ink);stroke-width:1.2;stroke-linecap:round}}
.{NS} .sel{{fill:var(--hot);opacity:.3}}
.{NS}-sh{{fill:var(--paper);stroke:var(--ink);stroke-width:1.3}}
.{NS}-st{{fill:var(--hot);fill-opacity:.22;stroke:var(--ink2);stroke-width:.9}}
.{NS}-sl{{fill:none;stroke:var(--ink2);stroke-width:.9;stroke-linecap:round;stroke-linejoin:round}}
.{NS} .fy{{opacity:0;animation:{NS}-fy {loop}}}
.{NS} .fx{{animation:{NS}-fx {loop}}}
.{NS} .num{{font-size:50px;font-weight:600;fill:var(--hot);--motion-count:{TOTAL};animation:{NS}-cnt {loop}}}
.{NS} .unit{{font-size:14px;fill:var(--ink3)}}
.{NS} .tw{{fill:none;stroke:var(--ink);stroke-width:1.5;stroke-linecap:round}}
.{NS} .twl{{fill:none;stroke:var(--ink3);stroke-width:1}}
.{NS} .twf{{fill:var(--hot);fill-opacity:.3}}
.{NS} .dyn{{animation:{NS}-dip {loop}}}
{per}
{keyframes()}
@media (min-width:769px) and (max-width:1100px){{.{NS} .unit{{font-size:18px}}}}
@media (max-width:768px){{{kit.base_css_mobile(NS)}.{NS} .pil{{stroke-width:1.7}}.{NS}-sh{{stroke-width:1.8}}.{NS}-st,.{NS}-sl{{stroke-width:1.3}}.{NS} .unit{{font-size:21px}}}}
""".strip()


# ------------------------------------------------------------------ çizim
def build():
    o = [kit.svg_open(NS, W, H, "xMidYMid slice"), f"<style>{css()}</style>", f"<defs>{sheet_def()}</defs>"]
    o += facade()
    o += towers()

    o.append('<g class="dyn">')
    for k in range(TOWERS):
        o.append(f'<rect class="twf twf{k}" x="{TW_X0 + TW_STEP * k}" y="{GY - TW_H[k]}" width="{TW_W}" height="{TW_H[k]}"/>')
    for j, k in enumerate(PICKS):
        o.append(f'<rect class="sel sel{j}" x="{f(pil_x(k) - PW / 2)}" y="{TOP}" width="{PW}" height="{GY - TOP}"/>')
    for j in range(len(PICKS)):
        x, y = pile_xy(j)
        o.append(f'<use class="ps{j}" href="#{NS}-sheet" transform="translate({f(x)} {f(y)}) rotate({PILE_ROT[j]})"/>')
    o.append(f'<g class="fx"><g class="fy"><use href="#{NS}-sheet"/></g></g>')
    o.append(f'<text class="num" x="{PILE_X - 42}" y="128" data-count="">7.436</text>')
    o.append("</g>")
    o.append(text(PILE_X - 40, 152, "teknik çizim", "unit fade", "technical drawings", ' style="--d:1.1s"'))
    o.append("</svg>")
    return "\n".join(o)


if __name__ == "__main__":
    assert len(set(PICKS)) == len(PICKS) and all(0 <= k < PN for k in PICKS)
    assert T_END < T_DIP0 - 2                         # sonuç en az iki saniye ekranda kalsın
    top_of_pile = pile_xy(len(PICKS) - 1)[1] - SHEET_H / 2
    assert top_of_pile > 160                          # yığın, sayaç ve etiketin altında kalsın
    here = os.path.dirname(os.path.abspath(__file__))
    kit.write(sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, "victory-park-header.svg"), build())
