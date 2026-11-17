# -*- coding: utf-8 -*-
"""Toplu Konutta Gün Işığı Optimizasyonu başlık animasyonunun üreteci.

Ortada vaziyet planı: D Blok, içinde gün ışığı ölçülen yedi salonla, komşu
binaların arasında. Sırayla üç senaryo oynar ve her biri sağdaki ölçeğe
gerçek değeriyle işlenir (sayfadaki tablo, DA150 ortalaması):

    mevcut 59,7  ·  taşıma 59,8  ·  döndürme 62,6  ·  döndürme + taşıma 66,5

Taşıma neredeyse hiçbir şey değiştirmez; döndürme sırasında Galapagos'un
denediği yönelimler ince çizgilerle iz bırakır. Sonunda yıllık kazanç yazılır:
yaklaşık 250 saat daha az yapay aydınlatma.

Ölçülerin kaynağı:
  - Blok izi, komşu binalar, dönüş ve kaymalar senaryo görselinden
    (toplukonut-6) ölçüldü. Blok görselde saat yönünde 126 derece (ters yönde
    234 derece) dönmüştür; animasyonda açı yazılmaz.
  - Salonların yeri 1. kat planındaki (toplukonut-5) salonlardan alındı.
    Salon başına optimize değer sayfada olmadığı için salonlar tek tek değil,
    ortalamayla birlikte, hepsi aynı oranda koyulaşır.
  - Ara açıların DA değeri bilinmediği için ölçekte yalnızca dört senaryonun
    değeri durur; sayı akarak değişmez.

Kullanım:  python motion/toplukonut-header.py     -> motion/toplukonut-header.svg
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit                                           # noqa: E402
from kit import f, pc, seg, draw_path, text          # noqa: E402

kit.seed(597)
NS = "mtk"

# ------------------------------------------------------------------ geometri
W, H = 1200, 420
SC = 0.75                      # senaryo görselinin pikseli -> çizim birimi
OX, OY = 202.5, -44.75         # vaziyetin sol üst köşesi (blok şeridin ortasına gelsin)
SHIFT_DESKTOP = 32             # geniş ekranda bütün çizim ortalanır


def X(px):
    return OX + px * SC


def Y(py):
    return OY + py * SC


# blok izi (mevcut durum), senaryo görselinin panel pikseli
BLOCK = [(290, 208), (416, 208), (416, 276), (432, 276), (432, 344), (440, 344), (440, 380), (452, 380),
         (452, 460), (416, 460), (416, 476), (392, 476), (392, 460), (354, 460), (354, 388), (176, 388),
         (176, 298), (290, 298)]
CENTROID = (340, 333)
# salonlar (1. kat planından, aynı piksel düzlemine taşınmış): x0, y0, x1, y1
SALONS = [(202, 311, 225, 354), (236, 306, 269, 351), (295, 221, 331, 262), (367, 225, 408, 255),
          (382, 292, 430, 326), (320, 339, 358, 370), (395, 380, 448, 408)]

MOVE_ONLY = (4, -7)                    # taşıma senaryosu: yaklaşık 0,5 m sağa, 0,7 m yukarı
ROT1, SHIFT1 = -234, (0, -11)          # döndürme: ters yönde 234 derece (saat yönünde 126)
ROT2, SHIFT2 = -235, (-5, -45)         # döndürme + taşıma
GHOSTS = [-39, -78, -117, -156, -195]  # döndürme sırasında iz bırakan aday yönelimler

# komşu binalar: (merkez x, merkez y, boy, en, açı)
NEIGHBOURS = [
    (278, 71, 190, 76, 34.6),
    (161, 190, 108, 66, -46.1),
    (58, 196, 130, 70, -45.0),
    (117, 478, 130, 125, 0.0),
    (351, 594, 120, 62, 14.9),
    (498, 532, 139, 65, -53.9),
    (565, 320, 60, 60, 30.0),
    (565, 449, 46, 42, 30.0),
]

# senaryo ölçeği (sağda): değer, Türkçe ad, İngilizce ad
GX = 716
G_Y55, G_PER = 250, 12                 # %55'in y'si, yüzde başına birim
SCEN = [(59.7, "mevcut", "current"), (59.8, "taşıma", "move"), (62.6, "döndürme", "rotate"),
        (66.5, "döndürme + taşıma", "rotate + move")]
SAVING = 250                           # yılda saat



def gy(v):
    return G_Y55 - (v - 55) * G_PER


# ------------------------------------------------------------------ zamanlama (sn)
T = 16.0
D0 = 1.6
T_MV0, T_MV1, T_MVB0, T_MVB1 = 0.8, 1.6, 2.2, 2.8      # taşıma: git, bekle, geri dön
T_ROT0, T_ROT1 = 2.8, 5.6                              # döndürme
T_FIN0, T_FIN1 = 6.4, 7.4                              # döndürme + taşıma
T_CNT0, T_CNT1 = 7.8, 9.6                              # yıllık kazanç sayacı
T_DIP0, T_DIP1, T_RESET, T_UP0, T_UP1 = 14.2, 14.6, 14.8, 15.0, 15.4
EASE = "cubic-bezier(.65,0,.25,1)"
EASE_PTS = (0.65, 0.0, 0.25, 1.0)


def p(t):
    return pc(t / T * 100)


R0, R1 = p(T_RESET - 0.01), p(T_RESET)


def ease_time(progress):
    """EASE eğrisinde verilen ilerlemeye (0..1) ulaşılan zaman oranı."""
    x1, y1, x2, y2 = EASE_PTS

    def at(t):
        return (3 * (1 - t) ** 2 * t * x1 + 3 * (1 - t) * t * t * x2 + t ** 3,
                3 * (1 - t) ** 2 * t * y1 + 3 * (1 - t) * t * t * y2 + t ** 3)
    lo, hi = 0.0, 1.0
    for _ in range(50):
        mid = (lo + hi) / 2
        if at(mid)[1] < progress:
            lo = mid
        else:
            hi = mid
    return at((lo + hi) / 2)[0]


# ------------------------------------------------------------------ parçalar
def poly(points):
    return "M" + "L".join(f"{f(X(x))} {f(Y(y))}" for x, y in points) + "Z"


def neighbour(cx, cy, ln, wd, ang, k):
    """Kırma çatılı komşu bina: dış çizgi, mahya ve dört sırt."""
    a = math.radians(ang)
    ca, sa = math.cos(a), math.sin(a)

    def pt(u, v):
        return (X(cx + u * ca - v * sa), Y(cy + u * sa + v * ca))

    hl, hw = ln / 2, wd / 2
    c = [pt(-hl, -hw), pt(hl, -hw), pt(hl, hw), pt(-hl, hw)]
    r = max(hl - hw, 0)
    r0, r1 = pt(-r, 0), pt(r, 0)
    d = "".join(seg(c[i][0], c[i][1], c[(i + 1) % 4][0], c[(i + 1) % 4][1], 0.4, 1.8, 0.4) for i in range(4))
    ridge = f"M{f(r0[0])} {f(r0[1])}L{f(r1[0])} {f(r1[1])}"
    for corner, end in ((c[0], r0), (c[3], r0), (c[1], r1), (c[2], r1)):
        ridge += f"M{f(corner[0])} {f(corner[1])}L{f(end[0])} {f(end[1])}"
    fill = "M" + "L".join(f"{f(x)} {f(y)}" for x, y in c) + "Z"
    return (f'<g class="fade" style="--d:{pc(0.3 + k * 0.07)}s"><path class="poche" d="{fill}"/>'
            f'<path class="ink" d="{d}"/><path class="ridge" d="{ridge}"/></g>')


def salons():
    d = "".join(f"M{f(X(a))} {f(Y(b))}H{f(X(c))}V{f(Y(e))}H{f(X(a))}Z" for a, b, c, e in SALONS)
    return f'<path class="salon" d="{d}"/><path class="salonl" d="{d}"/>'


def scale():
    o = ['<g class="col">']
    o.append(draw_path("ink", seg(GX, gy(55) + 6, GX, gy(70) - 6, 0.3, 0, 0.5), 0.6, 0.7))
    for v in (55, 60, 65, 70):
        o.append(f'<path class="tk fade" d="M{GX - 5} {f(gy(v))}H{GX}" style="--d:.9s"/>')
        o.append(text(GX - 10, gy(v) + 4, str(v), "ax fade", None, ' text-anchor="end" style="--d:.9s"'))
    o.append(text(GX - 30, gy(70) - 22, "DA₁₅₀ (%)", "cap fade", None, ' style="--d:1s"'))
    # dört senaryonun noktası ve etiketi
    dy = [16, -7, 5, 5]                # mevcut ve taşıma neredeyse üst üste: etiketleri ayır
    o.append('<g class="dyn">')
    for k, (v, tr, en) in enumerate(SCEN):
        y = gy(v)
        num = f"{v:.1f}".replace(".", ",")
        wrap = f'<g class="sc s{k}">' if k else '<g class="fade" style="--d:1.2s">'
        o.append(wrap + f'<circle class="dot d{k}" cx="{GX}" cy="{f(y)}" r="{7 if k == 3 else 5}"/>'
                 + text(GX + 15, y + dy[k], num, f"vn v{k}", f"{v:.1f}")
                 + text(GX + 60, y + dy[k], tr, "nm", en) + "</g>")
    # yıllık kazanç
    o.append(f'<g class="gain"><text class="hd" x="{GX - 30}" y="336" data-count="">{SAVING}</text>'
             f'<g class="hl">' + text(GX + 72, 314, "saat / yıl daha az", "hlt", "hours / year less")
             + text(GX + 72, 334, "yapay aydınlatma", "hlt", "artificial lighting") + "</g></g>")
    o.append("</g></g>")
    return o


# ------------------------------------------------------------------ stil
def kf(name, *rows):
    return f"@keyframes {NS}-{name}{{{''.join(rows)}}}"


def pose(rot, shift):
    return f"translate({pc(shift[0] * SC)}px,{pc(shift[1] * SC)}px) rotate({rot}deg)"


def keyframes():
    out = []
    p0, pm, p1, p2 = pose(0, (0, 0)), pose(0, MOVE_ONLY), pose(ROT1, SHIFT1), pose(ROT2, SHIFT2)
    out.append(kf("blk",
                  f"0%,{p(T_MV0)}%{{transform:{p0};animation-timing-function:{EASE}}}",
                  f"{p(T_MV1)}%,{p(T_MVB0)}%{{transform:{pm};animation-timing-function:{EASE}}}",
                  f"{p(T_MVB1)}%{{transform:{p0};animation-timing-function:{EASE}}}",
                  f"{p(T_ROT1)}%,{p(T_FIN0)}%{{transform:{p1};animation-timing-function:{EASE}}}",
                  f"{p(T_FIN1)}%,{R0}%{{transform:{p2}}}",
                  f"{R1}%,100%{{transform:{p0}}}"))
    # dönerken blok yalnızca çizgi olarak görünür; yerleşince dolar
    out.append(kf("bfill",
                  f"0%,{p(T_ROT0)}%{{opacity:1}}", f"{p(T_ROT0 + 0.3)}%,{p(T_ROT1 - 0.3)}%{{opacity:.25}}",
                  f"{p(T_ROT1)}%,100%{{opacity:1}}"))
    # salonlar: ortalama arttıkça koyulaşır
    out.append(kf("lit", f"0%,{p(T_ROT1 - 0.3)}%{{fill-opacity:.2}}", f"{p(T_ROT1)}%,{p(T_FIN1 - 0.3)}%{{fill-opacity:.38}}",
                  f"{p(T_FIN1)}%,{R0}%{{fill-opacity:.62}}", f"{R1}%,100%{{fill-opacity:.2}}"))
    # denenen yönelimler: blok o açıdan geçerken belirir, döndürme bitince solar
    for i, ang in enumerate(GHOSTS):
        t = T_ROT0 + (T_ROT1 - T_ROT0) * ease_time(ang / ROT1)
        out.append(kf(f"g{i}", f"0%,{p(t)}%{{opacity:0}}", f"{p(t + 0.15)}%,{p(T_ROT1 + 0.5)}%{{opacity:.75}}",
                      f"{p(T_ROT1 + 1.2)}%,100%{{opacity:0}}"))
    # ölçekteki noktalar: senaryo bitince belirir
    for k, t in ((1, T_MV1), (2, T_ROT1), (3, T_FIN1)):
        out.append(kf(f"s{k}", f"0%,{p(t)}%{{opacity:0}}", f"{p(t + 0.3)}%,{R0}%{{opacity:1}}", f"{R1}%,100%{{opacity:0}}"))
    # yıllık kazanç: sayaç 0'dan 250'ye
    out.append(kf("gain", f"0%,{p(T_CNT0 - 0.3)}%{{opacity:0}}", f"{p(T_CNT0)}%,{R0}%{{opacity:1}}", f"{R1}%,100%{{opacity:0}}"))
    out.append(kf("cnt", f"0%,{p(T_CNT0)}%{{--motion-count:0}}", f"{p(T_CNT1)}%,{R0}%{{--motion-count:{SAVING}}}",
                  f"{R1}%,100%{{--motion-count:0}}"))
    out.append(kf("dip", f"0%,{p(T_DIP0)}%{{opacity:1}}", f"{p(T_DIP1)}%,{p(T_UP0)}%{{opacity:0}}", f"{p(T_UP1)}%,100%{{opacity:1}}"))
    return "\n".join(out)


def css():
    loop = "var(--T) linear var(--d0) infinite backwards"
    cx, cy = X(CENTROID[0]), Y(CENTROID[1])
    ghosts = "".join(f".{NS} .g{i}{{animation:{NS}-g{i} {loop}}}" for i in range(len(GHOSTS)))
    dots = "".join(f".{NS} .s{k}{{animation:{NS}-s{k} {loop}}}" for k in (1, 2, 3))
    return f"""
{kit.base_css(NS)}
.{NS}{{--T:{T}s;--d0:{D0}s}}
.{NS} .root{{transform:translateX({SHIFT_DESKTOP}px)}}
.{NS} .ridge{{fill:none;stroke:var(--ink3);stroke-width:1;stroke-linecap:round}}
.{NS} .was{{fill:none;stroke:var(--ink2);stroke-width:1.3;stroke-dasharray:5 4}}
.{NS} .ghost{{fill:none;stroke:var(--hot);stroke-width:1.1;opacity:0}}
.{NS} .blk{{transform-origin:{pc(cx)}px {pc(cy)}px;transform:{pose(ROT2, SHIFT2)};animation:{NS}-blk {loop}}}
.{NS} .bfill{{fill:var(--paper);animation:{NS}-bfill {loop}}}
.{NS} .bwash{{fill:var(--hot);fill-opacity:.1}}
.{NS} .bline{{fill:none;stroke:var(--hot);stroke-width:2.6;stroke-linejoin:round}}
.{NS} .salon{{fill:var(--hot);fill-opacity:.62;animation:{NS}-lit {loop}}}
.{NS} .salonl{{fill:none;stroke:var(--hot);stroke-width:1.1}}
.{NS} .tk{{fill:none;stroke:var(--ink);stroke-width:1.3;stroke-linecap:round}}
.{NS} .ax{{font-size:12px;fill:var(--ink3)}}
.{NS} .cap{{font-size:13px;fill:var(--ink3)}}
.{NS} .dot{{fill:var(--paper);stroke:var(--ink);stroke-width:1.8}}
.{NS} .d0{{fill:var(--ink)}}
.{NS} .d2{{stroke:var(--hot)}}
.{NS} .d3{{fill:var(--hot);stroke:var(--hot)}}
.{NS} .vn{{font-size:16px;font-weight:600;fill:var(--ink)}}
.{NS} .v3{{fill:var(--hot)}}
.{NS} .nm{{font-size:13px;fill:var(--ink3)}}
.{NS} .hd{{font-size:54px;font-weight:600;fill:var(--hot);--motion-count:{SAVING};animation:{NS}-cnt {loop}}}
.{NS} .hlt{{font-size:14px;fill:var(--ink2)}}
.{NS} .gain{{animation:{NS}-gain {loop}}}
.{NS} .dyn{{animation:{NS}-dip {loop}}}
{ghosts}
{dots}
{keyframes()}
@media (min-width:769px) and (max-width:1100px){{.{NS} .ax{{font-size:15px}}.{NS} .cap{{font-size:16px}}.{NS} .vn{{font-size:19px}}.{NS} .nm{{font-size:16px}}.{NS} .hlt{{font-size:17px}}}}
@media (max-width:768px){{.{NS} .root{{transform:none}}.{NS} .col{{transform:translateX(-8px)}}{kit.base_css_mobile(NS)}.{NS} .ridge{{stroke-width:1.5}}.{NS} .was{{stroke-width:1.9}}.{NS} .ghost{{stroke-width:1.6}}.{NS} .bline{{stroke-width:3.4}}.{NS} .salonl{{stroke-width:1.6}}.{NS} .tk{{stroke-width:1.9}}.{NS} .dot{{stroke-width:2.4}}.{NS} .ax{{font-size:18px}}.{NS} .cap{{font-size:19px}}.{NS} .vn{{font-size:22px}}.{NS} .nm{{display:none}}.{NS} .hlt{{font-size:19px}}.{NS} .hl{{transform:translate(-102px,46px)}}}}
""".strip()


# ------------------------------------------------------------------ çizim
def build():
    cx, cy = X(CENTROID[0]), Y(CENTROID[1])
    o = [kit.svg_open(NS, W, H, "xMidYMid slice"), f"<style>{css()}</style>", '<g class="root">']

    # vaziyet planı
    for k, n in enumerate(NEIGHBOURS):
        o.append(neighbour(*n, k))
    o.append(f'<path class="was fade" d="{poly(BLOCK)}" style="--d:1s"/>')
    o.append('<g class="dyn">')
    for i, ang in enumerate(GHOSTS):
        o.append(f'<path class="ghost g{i}" d="{poly(BLOCK)}" transform="rotate({ang} {pc(cx)} {pc(cy)})"/>')
    o.append(f'<g class="fade" style="--d:1.1s"><g class="blk">'
             f'<g class="bfill"><path d="{poly(BLOCK)}"/><path class="bwash" d="{poly(BLOCK)}"/>{salons()}</g>'
             f'<path class="bline" d="{poly(BLOCK)}"/></g></g>')
    o.append("</g>")

    o += scale()
    o.append("</g></svg>")
    return "\n".join(o)


if __name__ == "__main__":
    assert abs((ROT1 % 360) - 126) <= 1 and abs((ROT2 % 360) - 125) <= 1      # görselde ölçülen dönüş
    assert round((SCEN[3][0] - SCEN[0][0]) / SCEN[0][0] * 100, 1) == 11.4      # sayfadaki iyileşme oranı
    for a, b, c, e in SALONS:                                                  # salonlar blok izinin kutusunda
        assert 176 <= a < c <= 452 and 208 <= b < e <= 476
    here = os.path.dirname(os.path.abspath(__file__))
    kit.write(sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, "toplukonut-header.svg"), build())
