# -*- coding: utf-8 -*-
"""12/84 sayfa içi animasyonu: aynı duvar iki sistemde 96 cm kaydırılıyor.

Sol panel (geleneksel): duvar camın ortasına denk gelir, iki odanın tavanı
(karolaj, aydınlatma, sprinkler) baştan çizilir, iş 2 hafta sürer.
Sağ panel (12/84): duvar dikmeye oturur, yalnızca iki tavan şeridi yer
değiştirir, iş 2 gün sürer.

Sayılar sayfadaki tablodan: duvar taşıma süresi 2 hafta / 2 gün; tavan
revizyonu tam yenileme / şerit değişim; pencere çakışması olası / imkânsız.

Çizimde 1 birim = 1 cm. Tavan öğeleri plana yansıtılmış olarak çizilir.

Kullanım:  python motion/1284-wall.py            -> motion/1284-wall.svg
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit                                                    # noqa: E402
from kit import f, pc, seg, quad, circ, draw_path, text       # noqa: E402

kit.seed(84)
NS = "m1284w"

# ------------------------------------------------------------------ geometri
W, H = 1200, 430
PX = (40, 640)                 # panellerin sol kenarı
X0, X1 = 14, 506               # cephenin / odanın dış sınırı (panel içi)
FY0, FY1 = 60, 80              # cephe dış / iç yüzü
FYM = (FY0 + FY1) / 2
RY = 330                       # koridor duvarının oda yüzü
WT = 12                        # duvar kalınlığı: 12 cm
IN0, IN1 = X0 + WT, X1 - WT    # odanın iç genişliği
SHIFT = 96                     # duvarın kaydığı mesafe
TILE = 60                      # asma tavan karosu
ROWS_Y = [FY1 + 5 + TILE * (k + 0.5) for k in range(4)]   # tavan öğelerinin sıra eksenleri

# geleneksel cephe: geniş dikmeler arasında geniş camlar
TRAD_PIERS = [(14, 50), (230, 290), (470, 506)]
TRAD_WALL = 260                # duvar başlangıçta orta dikmenin ekseninde
# 12/84 cephesi: 96 cm'de bir 12 cm dikme, arada 84 cm cam
AXES = [20 + 96 * k for k in range(6)]
MOD_WALL = AXES[2]             # duvar başlangıçta 3. aksta
MOD_SWAP = AXES[3]             # yer değiştireceği tavan şeridinin aksı

DAY_Y, DAY_W, DAY_PITCH, DAYS = 372, 20, 25, 14
MARK_Y = 36

# ------------------------------------------------------------------ zamanlama (sn)
T = 12.0                       # döngü
D0 = 2.0                       # açılış çizimi bittikten sonra döngünün başladığı an
T_MOVE0, T_MOVE1 = 1.0, 2.1    # duvarın kayması
T_MARK = 2.15                  # sonuç işareti
T_OLD_HOT, T_OLD_OUT0, T_OLD_OUT1 = 2.3, 2.9, 3.4   # eski tavan işaretlenir, sökülür
T_NEW0, T_NEW1 = 3.3, 3.9      # yeni karolaj belirir
T_LIGHT0, LIGHT_STEP, LIGHT_T = 3.5, 0.18, 0.5      # yeni aydınlatmalar çizilir
T_DAY0, DAY_STEP = 2.6, 0.3    # gün kutuları dolmaya başlar
T_DIP0, T_DIP1, T_RESET, T_UP0, T_UP1 = 10.4, 10.8, 11.0, 11.2, 11.6   # döngü sonu
EASE = "cubic-bezier(.7,0,.2,1)"
BOUNCE = "cubic-bezier(.3,1.5,.5,1)"


def p(t):
    return pc(t / T * 100)


R0, R1 = p(T_RESET - 0.01), p(T_RESET)   # sıfırlama, katman görünmezken yapılır


# ------------------------------------------------------------------ kabuk
def shell(piers, d0):
    """Cephe, yan duvarlar ve koridor duvarı. piers: [(x0, x1), ...]"""
    o = []
    o.append(draw_path("ink", seg(X0 - 7, FY0, X1 + 8, FY0, 0.5, 0, 1.0), d0 + 0.10))
    o.append(draw_path("ink h", seg(X0 - 4, FY0 + 0.8, X1 + 5, FY0 - 0.6, 0.6, 0, 1.2), d0 + 0.16))
    o.append(draw_path("ink", seg(X0 - 4, FY1, X1 + 6, FY1, 0.5, 0, 1.0), d0 + 0.20))
    for (a, b), (c, _) in zip(piers, piers[1:]):       # dikmeler arasındaki cam çizgisi
        o.append(draw_path("ink h", seg(b, FYM, c, FYM, 0.3, 0, 0.4), d0 + 0.3))
    for x in (X0, X1 - WT):                            # yan duvarlar
        o.append(f'<rect class="poche fade" x="{f(x)}" y="{FY1}" width="{WT}" height="{RY - FY1}" '
                 f'style="--d:{pc(d0 + 0.5)}s"/>')
        o.append(draw_path("ink", seg(x, FY1 - 4, x, RY + WT + 6, 0.4, 0, 0.8), d0 + 0.25, 0.55))
        o.append(draw_path("ink", seg(x + WT, FY1 - 3, x + WT, RY + WT + 4, 0.4, 0, 0.8), d0 + 0.31, 0.55))
    o.append(f'<rect class="poche fade" x="{X0}" y="{RY}" width="{X1 - X0}" height="{WT}" style="--d:{pc(d0 + 0.8)}s"/>')
    o.append(draw_path("ink", seg(X0 - 6, RY, X1 + 7, RY, 0.4, 0, 1.0), d0 + 0.5))
    o.append(draw_path("ink", seg(X0 - 4, RY + WT, X1 + 6, RY + WT, 0.4, 0, 1.0), d0 + 0.56))
    for k, (a, b) in enumerate(piers):
        o.append(f'<path class="solid pop" d="{quad((a + b) / 2, FYM, b - a, FY1 - FY0, 0.5)}" '
                 f'style="--d:{pc(d0 + 0.25 + k * 0.06)}s;--t:.3s"/>')
    return o


# ------------------------------------------------------------------ tavan öğeleri
def tiles(x0, x1):
    """Odaya ortalanmış 60x60 karolaj. Çizim yolunu ve sütun eksenlerini döndürür."""
    n = int((x1 - x0) // TILE)
    m = ((x1 - x0) - n * TILE) / 2
    xs = [x0 + m + TILE * k for k in range(n + 1)]
    ys = [FY1 + 5 + TILE * k for k in range(5)]
    d = "".join(f"M{f(x)} {f(ys[0])}V{f(ys[-1])}" for x in xs)
    d += "".join(f"M{f(xs[0])} {f(y)}H{f(xs[-1])}" for y in ys)
    cols = [x + TILE / 2 for x in xs[:-1]]
    return f'<path class="tile" d="{d}"/>', cols


def light(cx, cy, cls="cl", s=44):
    """Kare gömme armatür: leke + çerçeve."""
    return [kit.wash(cx - s / 2, cy - s / 2, s, s),
            f'<path class="{cls}" pathLength="1" d="{quad(cx, cy, s, s, 0.6)}"/>']


def sprinkler(cx, cy, r=5.5):
    return (f'<path class="cl" d="{circ(cx, cy, r)}M{f(cx - r - 2.5)} {f(cy)}H{f(cx + r + 2.5)}'
            f'M{f(cx)} {f(cy - r - 2.5)}V{f(cy + r + 2.5)}"/>')


def spine(light_x, spr_x, light_cls="cl"):
    """Bir odanın tavan omurgası: aydınlatma, sprinkler, aydınlatma, sprinkler."""
    o = []
    o += light(light_x, ROWS_Y[0], light_cls)
    o.append(sprinkler(spr_x, ROWS_Y[1]))
    o += light(light_x, ROWS_Y[2], light_cls)
    o.append(sprinkler(spr_x, ROWS_Y[3]))
    return o


def strip(x):
    """12 cm'lik tavan şeridi: iki çizgi arasında lineer spot ve sprinkler."""
    h = WT / 2
    d = f"M{f(x - h)} {FY1 + 6}V{RY - 6}M{f(x + h)} {FY1 + 6}V{RY - 6}"
    o = [f'<path class="tile" d="{d}"/>']
    for y in (ROWS_Y[0], ROWS_Y[2]):
        o.append(f'<rect class="cl spot" x="{f(x - 2.5)}" y="{f(y - 26)}" width="5" height="52" rx="2.5"/>')
    for y in (ROWS_Y[1], ROWS_Y[3]):
        o.append(f'<path class="cl" d="{circ(x, y, 4.5)}"/>')
    return o


# ------------------------------------------------------------------ ortak parçalar
def wall(x, cls):
    return f'<path class="wall {cls}" pathLength="1" d="M{f(x)} {FY1}V{RY}"/>'


def mark(x, kind):
    """Sonuç işareti: çarpı (cama denk geldi) ya da onay (dikmeye oturdu)."""
    y = MARK_Y
    if kind == "x":
        d = f"M{f(x - 6)} {f(y - 6)}L{f(x + 6)} {f(y + 6)}M{f(x + 6)} {f(y - 6)}L{f(x - 6)} {f(y + 6)}"
    else:
        d = f"M{f(x - 7)} {f(y + 0.5)}L{f(x - 2)} {f(y + 6)}L{f(x + 7.5)} {f(y - 5.5)}"
    return (f'<g class="mark"><circle cx="{f(x)}" cy="{y}" r="15"/><path d="{d}"/>'
            f'<path class="stem" d="M{f(x)} {y + 15.5}V{FY0 - 3}"/></g>')


def days(cls, label_tr, label_en, label_cls, d0):
    """14 günlük kutu sırası; dolan kutular işin süresini gösterir."""
    o = []
    for k in range(DAYS):
        o.append(f'<rect class="fur fade" x="{X0 + k * DAY_PITCH}" y="{DAY_Y}" width="{DAY_W}" height="{DAY_W}" rx="2" '
                 f'style="--d:{pc(d0 + 1.2 + k * 0.03)}s;--t:.3s"/>')
    o.append(f'<g class="dyn"><g clip-path="url(#{NS}-days)">'
             f'<rect class="df {cls}" x="{X0}" y="{DAY_Y}" width="{DAYS * DAY_PITCH}" height="{DAY_W}"/></g>')
    o.append(text(X0 + DAYS * DAY_PITCH + 8, DAY_Y + 15, label_tr, f"lbl {label_cls}", label_en) + "</g>")
    return o


# ------------------------------------------------------------------ paneller
def panel_trad():
    o = ['<g class="p p1">']
    o.append(text(X0, 30, "GELENEKSEL", "ttl fade", "CONVENTIONAL", ' style="--d:.2s"'))
    o += shell(TRAD_PIERS, 0)

    xw0, xw1 = TRAD_WALL, TRAD_WALL + SHIFT
    o.append('<g class="dyn">')
    # eski tavan: iki oda, her biri kendi içinde ortalanmış
    o.append('<g class="fade" style="--d:.9s"><g class="co">')
    for a, b in ((IN0, xw0 - WT / 2), (xw0 + WT / 2, IN1)):
        path, cols = tiles(a, b)
        o.append(path)
        mid = cols[len(cols) // 2]
        o += spine(mid, mid)
    o.append("</g></g>")
    # yeni tavan: duvar kaydıktan sonra iki oda da yeniden ortalanır
    o.append('<g class="cn">')
    for a, b in ((IN0, xw1 - WT / 2), (xw1 + WT / 2, IN1)):
        path, cols = tiles(a, b)
        o.append(path)
        if len(cols) >= 3:
            mid = cols[len(cols) // 2]
            o += spine(mid, mid, "cl nl")
        else:                       # dar odada aydınlatma ve sprinkler yan yana
            o += spine(cols[0], cols[-1], "cl nl")
    o.append("</g>")
    o.append(wall(xw0, "wl"))
    o.append(f'<g class="mk">{mark(xw1, "x")}</g>')
    o.append("</g>")

    o += days("dl", "2 hafta", "2 weeks", "ll", 0)
    o.append("</g>")
    return o


def panel_mod():
    o = ['<g class="p p2">']
    o.append(text(X0, 30, "12/84", "ttl fade", None, ' style="--d:.35s"'))
    piers = [(x - WT / 2, x + WT / 2) for x in AXES]
    o += shell(piers, 0.15)

    # ölçü: 12 cm dikme, 84 cm açıklık
    a, b = AXES[1], AXES[2]
    yd = FY0 - 9
    o.append(f'<g class="fade" style="--d:1.3s"><path class="dimline" d="M{f(a - 6)} {yd}H{f(b - 6)}'
             f'M{f(a - 6)} {yd - 4}V{yd + 4}M{f(a + 6)} {yd - 4}V{yd + 4}M{f(b - 6)} {yd - 4}V{yd + 4}"/>'
             + text(a, yd - 7, "12", "dim") + text((a + b) / 2, yd - 7, "84", "dim") + "</g>")

    # yerinde kalan tavan şeritleri
    o.append('<g class="strip fade" style="--d:1.05s">')
    for x in AXES[1:-1]:
        if x not in (MOD_WALL, MOD_SWAP):
            o += strip(x)
    o.append("</g>")

    o.append('<g class="dyn">')
    # duvarla yer değiştiren şerit: son konumunda (duvarın eski yerinde) çizilir
    o.append('<g class="fade" style="--d:1.05s"><g class="strip sr">')
    o += strip(MOD_WALL)
    o.append("</g></g>")
    o.append(wall(MOD_WALL, "wr"))
    o.append(f'<g class="mk">{mark(MOD_WALL + SHIFT, "v")}</g>')
    o.append("</g>")

    o += days("dr", "2 gün", "2 days", "lr", 0.15)
    o.append("</g>")
    return o


# ------------------------------------------------------------------ keyframe'ler
def kf(name, *rows):
    return f"@keyframes {NS}-{name}{{{''.join(rows)}}}"


def keyframes():
    out = []
    # duvar: iki panelde de aynı mesafe
    out.append(kf("wall",
                  f"0%,{p(T_MOVE0)}%{{transform:translateX(0);animation-timing-function:{EASE}}}",
                  f"{p(T_MOVE1)}%,{R0}%{{transform:translateX({SHIFT}px)}}",
                  f"{R1}%,100%{{transform:translateX(0)}}"))
    # 12/84: tavan şeridi duvarın bıraktığı yere geçer
    out.append(kf("swap",
                  f"0%,{p(T_MOVE0)}%{{transform:translateX({SHIFT}px);color:var(--ink2);animation-timing-function:{EASE}}}",
                  f"{p(T_MOVE1)}%,{p(T_MOVE1 + 0.1)}%{{transform:translateX(0);color:var(--ink2)}}",
                  f"{p(T_MOVE1 + 0.4)}%,{R0}%{{transform:translateX(0);color:var(--hot)}}",
                  f"{R1}%,100%{{transform:translateX({SHIFT}px);color:var(--ink2)}}"))
    # geleneksel: eski tavan işaretlenir ve sökülür
    out.append(kf("old",
                  f"0%,{p(T_OLD_HOT)}%{{opacity:1;color:var(--ink2)}}",
                  f"{p(T_OLD_HOT + 0.3)}%,{p(T_OLD_OUT0)}%{{opacity:1;color:var(--hot)}}",
                  f"{p(T_OLD_OUT1)}%,{R0}%{{opacity:0;color:var(--hot)}}",
                  f"{R1}%,100%{{opacity:1;color:var(--ink2)}}"))
    # geleneksel: yeni tavan çizilir
    out.append(kf("new",
                  f"0%,{p(T_NEW0)}%{{opacity:0}}", f"{p(T_NEW1)}%,{R0}%{{opacity:1}}", f"{R1}%,100%{{opacity:0}}"))
    for i in range(4):
        t0 = T_LIGHT0 + i * LIGHT_STEP
        out.append(kf(f"nl{i}",
                      f"0%,{p(t0)}%{{stroke-dashoffset:1.01}}", f"{p(t0 + LIGHT_T)}%,{R0}%{{stroke-dashoffset:0}}",
                      f"{R1}%,100%{{stroke-dashoffset:1.01}}"))
    # sonuç işareti
    out.append(kf("mark",
                  f"0%,{p(T_MARK)}%{{transform:scale(0);animation-timing-function:{BOUNCE}}}",
                  f"{p(T_MARK + 0.35)}%,{R0}%{{transform:scale(1)}}", f"{R1}%,100%{{transform:scale(0)}}"))
    # gün kutuları: iki panelde de aynı hızla dolar, sağda 2. günde durur
    t_l = T_DAY0 + DAYS * DAY_STEP
    t_r = T_DAY0 + 2 * DAY_STEP
    out.append(kf("dl",
                  f"0%,{p(T_DAY0)}%{{transform:scaleX(0);animation-timing-function:steps({DAYS},end)}}",
                  f"{p(t_l)}%,{R0}%{{transform:scaleX(1)}}", f"{R1}%,100%{{transform:scaleX(0)}}"))
    out.append(kf("dr",
                  f"0%,{p(T_DAY0)}%{{transform:scaleX(0);animation-timing-function:steps(2,end)}}",
                  f"{p(t_r)}%,{R0}%{{transform:scaleX({pc(2 / DAYS)})}}", f"{R1}%,100%{{transform:scaleX(0)}}"))
    for name, t in (("ll", t_l), ("lr", t_r)):
        out.append(kf(name, f"0%,{p(t)}%{{opacity:0}}", f"{p(t + 0.3)}%,{R0}%{{opacity:1}}", f"{R1}%,100%{{opacity:0}}"))
    # döngü sonu: değişen her şey solar, başa döner, yeniden belirir
    out.append(kf("dip", f"0%,{p(T_DIP0)}%{{opacity:1}}", f"{p(T_DIP1)}%,{p(T_UP0)}%{{opacity:0}}",
                  f"{p(T_UP1)}%,100%{{opacity:1}}"))
    return "\n".join(out)


# ------------------------------------------------------------------ stil
def css():
    loop = "var(--T) linear var(--d0) infinite backwards"
    return f"""
{kit.base_css(NS)}
.{NS}{{--T:{T}s;--d0:{D0}s}}
.{NS} .p1{{transform:translate({PX[0]}px,0)}}
.{NS} .p2{{transform:translate({PX[1]}px,0)}}
.{NS} .tile{{fill:none;stroke:currentColor;stroke-width:1;opacity:.4}}
.{NS} .cl{{fill:none;stroke:currentColor;stroke-width:1.5;stroke-linecap:round;stroke-linejoin:round}}
.{NS} .spot{{fill:currentColor;fill-opacity:.18}}
.{NS} .strip{{color:var(--ink2)}}
.{NS} .wall{{fill:none;stroke:var(--hot);stroke-width:{WT};stroke-dasharray:1 2}}
.{NS} .mark circle{{fill:var(--paper);stroke:var(--ink);stroke-width:1.7}}
.{NS} .mark path{{fill:none;stroke:var(--ink);stroke-width:2.3;stroke-linecap:round;stroke-linejoin:round}}
.{NS} .mark .stem{{stroke-width:1.2}}
.{NS} .ttl{{font-size:15px;letter-spacing:.1em;fill:var(--ink3)}}
.{NS} .dim{{font-size:14px;fill:var(--ink2);text-anchor:middle}}
.{NS} .dimline{{fill:none;stroke:var(--ink2);stroke-width:1}}
.{NS} .lbl{{font-size:15px;fill:var(--ink2)}}
.{NS} .df{{fill:var(--hot);transform-box:fill-box;transform-origin:0 50%}}
.{NS} .dyn{{animation:{NS}-dip {loop}}}
.{NS} .wl,.{NS} .wr{{transform:translateX({SHIFT}px);animation:{NS}-draw .5s cubic-bezier(.45,0,.2,1) 1.3s backwards,{NS}-wall {loop}}}
.{NS} .sr{{color:var(--hot);animation:{NS}-swap {loop}}}
.{NS} .co{{opacity:0;color:var(--hot);animation:{NS}-old {loop}}}
.{NS} .cn{{color:var(--hot);animation:{NS}-new {loop}}}
.{NS} .nl{{stroke-dasharray:1 2}}
.{NS} .nl0{{animation:{NS}-nl0 {loop}}}
.{NS} .nl1{{animation:{NS}-nl1 {loop}}}
.{NS} .nl2{{animation:{NS}-nl2 {loop}}}
.{NS} .nl3{{animation:{NS}-nl3 {loop}}}
.{NS} .mk{{transform-box:fill-box;transform-origin:50% 50%;animation:{NS}-mark {loop}}}
.{NS} .dl{{animation:{NS}-dl {loop}}}
.{NS} .dr{{transform:scaleX({pc(2 / DAYS)});animation:{NS}-dr {loop}}}
.{NS} .ll{{animation:{NS}-ll {loop}}}
.{NS} .lr{{animation:{NS}-lr {loop}}}
{keyframes()}
@media (min-width:769px) and (max-width:1100px){{.{NS} .ttl{{font-size:19px}}.{NS} .dim{{font-size:18px}}.{NS} .lbl{{font-size:19px}}}}
@media (max-width:768px){{.{NS} .root{{transform:scale(2)}}.{NS} .p2{{transform:translate({PX[0]}px,{H}px)}}{kit.base_css_mobile(NS)}.{NS} .tile{{stroke-width:1.4}}.{NS} .cl{{stroke-width:2}}.{NS} .dimline{{stroke-width:1.5}}.{NS} .ttl{{font-size:19px}}.{NS} .dim{{font-size:19px}}.{NS} .lbl{{font-size:20px}}}}
""".strip()


# ------------------------------------------------------------------ çizim
def build():
    o = [kit.svg_open(NS, W, H, "xMidYMin meet"), f"<style>{css()}</style>"]
    clip = "".join(f'<rect x="{X0 + k * DAY_PITCH + 1.5}" y="{DAY_Y + 1.5}" width="{DAY_W - 3}" height="{DAY_W - 3}" rx="1"/>'
                   for k in range(DAYS))
    o.append(f'<defs><clipPath id="{NS}-days">{clip}</clipPath></defs>')
    o.append('<g class="root">')
    o += panel_trad()
    o += panel_mod()
    o.append("</g></svg>")
    svg = "\n".join(o)
    # yeni aydınlatmalar sırayla çizilsin diye numaralandır
    for i in range(4):
        svg = svg.replace('class="cl nl"', f'class="cl nl nl{i}"', 1)
    assert 'class="cl nl"' not in svg
    return svg


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    kit.write(sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, "1284-wall.svg"), build())
