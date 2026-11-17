# -*- coding: utf-8 -*-
"""Üsküdar Meydanı başlık animasyonunun üreteci.

Sayfadaki altı katmanlı harita (uskudar-meydani-2) tek bir eskiz haritada
birleşir: kıyı ve yollar, ağaçlandırılabilir alan, önerilen kamusal alanlar,
tanımlı yollar, metro çıkışları, çıkışların önündeki noktalar ve seçilen ana
noktalar. Sonra optimizasyon oynar:

  1. Metro çıkışı noktalarından ana noktalara görüş çizgileri çekilir.
  2. Ağaçlar aralığın üst ucuna kadar dikilir (224). Araya giren ağaç görüş
     çizgisini keser; kesilen çizgi söner.
  3. Çözücü seyreltir: 45 ağaç, yarı boyutta kalır; çizgiler yeniden açılır.

Sağdaki sayılar sayfadakilerdir: ağaç aralığı 43 – 224, sonuç 45 ağaç ve 0,5
boyut çarpanı; görünürlük 74 – 244 aralığında 221.

Sayfada yazmadığı için sayı verilmeden gösterilenler:
  - Ağaçların yeri. Sonuç görselindeki ağaçlar haritaya güvenle oturtulamadı;
    ağaçlar ölçülen ağaçlandırılabilir alanın içine eşit aralıklı serpilir
    (yollar, tanımlı yollar, kamusal alanlar ve çıkışlar boş kalır).
  - Görüş çizgileri: 7 çıkış noktası x 4 ana nokta = 28 çizgi. Sayfadaki 56
    görüş açısının hangi çiftler olduğu yazmadığı için çizgi sayısı yazılmaz.
  - Yoğun durumda ağaç boyutu aralığın ortasındadır (1,0); sonda 0,5.
  - Sonda 28 çizgiden 25'i açık kalır (221 / 244 oranına en yakın tam sayı).

Geometri motion/uskudar-header.json dosyasındadır (görsellerden ölçüldü).

Kullanım:  python motion/uskudar-header.py     -> motion/uskudar-header.svg
"""
import itertools
import json
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit                                           # noqa: E402
from kit import f, pc, seg, draw_path, text          # noqa: E402

kit.seed(221)
NS = "mus"
HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(HERE, "uskudar-header.json"), encoding="utf-8") as fh:
    GEO = json.load(fh)

# ------------------------------------------------------------------ sayfadaki sayılar
TREES_MIN, TREES_MAX, TREES_OPT = 43, 224, 45        # ağaç sayısı aralığı ve sonuç
SIZE_OPT = 0.5                                       # sonuçtaki ağaç boyut çarpanı
VIS_MIN, VIS_MAX, VIS_OPT = 74, 244, 221             # görünürlük: en az, en çok, sonuç

# ------------------------------------------------------------------ yerleşim
W, H = 1200, 420
SC = 1.1                       # harita pikseli (yaklaşık 1 m) -> çizim birimi
OX, OY = 144.0, -32.1          # haritanın sol üst köşesi
MOB_SHIFT = 285 - (OX + 2 * SC)        # dar ekranda harita şeridi doldurur (görünen x: 285 – 915)
CX = 822                       # sağdaki sayı sütununun sol kenarı
BAR_X0, BAR_LEN, BAR_Y = CX + 2, 220, 258


def X(px):
    return OX + px * SC


def Y(py):
    return OY + py * SC


ZONES = GEO["tree_area"]
ROADS = GEO["roads"]
PATHS = GEO["paths"]
PUBLIC = GEO["public"]
EXITS = GEO["exits"]
METRO = sorted(GEO["metro_points"])                  # batıdan doğuya
KEYS = GEO["key_points"]

# ağaç: üç ağaç modeli (sayfada: "üç farklı ağaç modeli"), yarıçap çizim biriminde
R_BASE = 5.4
MODELS = (0.85, 1.0, 1.2)
K_MOB = 1.3                    # dar ekranda ağaçlar bu kadar iri çizilir (orantı aynı kalır)
PATH_HALF = 3.2                # tanımlı yolların ağaçsız kalan yarı genişliği (piksel)

# ------------------------------------------------------------------ zamanlama (sn)
T = 17.0
D0 = 2.6
T_LN0, LN_STEP, LN_SUB, LN_DUR = 0.2, 0.26, 0.07, 0.6        # görüş çizgileri çıkış noktası sırasıyla çekilir
NW = 14                                                      # ağaçlar bu kadar dalgada gelir ve gider
T_IN0, IN_STEP, POP_IN = 2.9, 0.22, 0.32
T_OUT0, OUT_STEP, POP_OUT, SHRINK = 7.5, 0.2, 0.28, 0.5
JIT = (0.0, 0.07, 0.14, 0.21)                                # dalga içinde küçük gecikmeler
T_RES = T_OUT0 + NW * OUT_STEP + 0.6
T_DIP0, T_DIP1, T_RESET, T_UP0, T_UP1 = 15.1, 15.5, 15.56, 15.9, 16.3


def p(t):
    return pc(t / T * 100)


R0, R1 = p(T_RESET - 0.01), p(T_RESET)


# ------------------------------------------------------------------ geometri yardımcıları
def inside(pt, poly):
    x, y = pt
    c = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            c = not c
    return c


def seg_dist(pt, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    t = max(0.0, min(1.0, ((pt[0] - a[0]) * dx + (pt[1] - a[1]) * dy) / (dx * dx + dy * dy)))
    return math.hypot(pt[0] - a[0] - t * dx, pt[1] - a[1] - t * dy)


def box(poly):
    return (min(q[0] for q in poly), min(q[1] for q in poly), max(q[0] for q in poly), max(q[1] for q in poly))


ZONE_BOX = [box(z) for z in ZONES]
ROAD_BOX = [box(r) for r in ROADS]


def in_any(pt, polys, boxes):
    return any(b[0] <= pt[0] <= b[2] and b[1] <= pt[1] <= b[3] and inside(pt, q) for q, b in zip(polys, boxes))


def plantable(pt):
    """Ağaç dikilebilir mi: alanın içinde, yolların, kamusal alanların ve çıkışların dışında."""
    if not in_any(pt, ZONES, ZONE_BOX) or in_any(pt, ROADS, ROAD_BOX):
        return False
    if any(seg_dist(pt, a, b) < PATH_HALF for a, b in PATHS):
        return False
    if any(math.hypot(pt[0] - cx, pt[1] - cy) < r + 1.5 for cx, cy, r in PUBLIC):
        return False
    if any(math.hypot(pt[0] - mx, pt[1] - my) < 6.5 for mx, my in METRO):
        return False
    return not any(math.hypot(pt[0] - e[0], pt[1] - e[1]) < e[2] / 2 + 3 for e in EXITS)


# ------------------------------------------------------------------ ağaçlar ve görüş çizgileri
def spread(cands, d):
    """Adaylardan, birbirine d'den yakın olmayanları sırayla seçer."""
    grid, out = {}, []
    for q in cands:
        gx, gy = int(q[0] // d), int(q[1] // d)
        near = (r for ix in (gx - 1, gx, gx + 1) for iy in (gy - 1, gy, gy + 1) for r in grid.get((ix, iy), ()))
        if all((q[0] - r[0]) ** 2 + (q[1] - r[1]) ** 2 >= d * d for r in near):
            out.append(q)
            grid.setdefault((gx, gy), []).append(q)
    return out


def plant():
    """Ağaçlandırılabilir alana 224 ağaç: konum (piksel), model, dalga, gecikme sınıfı."""
    rng = random.Random(224)
    x0 = min(b[0] for b in ZONE_BOX)
    y0 = min(b[1] for b in ZONE_BOX)
    x1 = max(b[2] for b in ZONE_BOX)
    y1 = max(b[3] for b in ZONE_BOX)
    step = 1.6
    cands = []
    for iy in range(int((y1 - y0) / step) + 1):
        for ix in range(int((x1 - x0) / step) + 1):
            q = (x0 + ix * step + rng.uniform(-0.5, 0.5), y0 + iy * step + rng.uniform(-0.5, 0.5))
            if plantable(q):
                cands.append(q)
    rng.shuffle(cands)
    lo, hi = 5.0, 14.0
    for _ in range(18):                               # 224 ağacın sığdığı en geniş aralık
        mid = (lo + hi) / 2
        if len(spread(cands, mid)) >= TREES_MAX:
            lo = mid
        else:
            hi = mid
    pts = spread(cands, lo)
    while len(pts) > TREES_MAX:                       # fazlaysa en sıkışık olanı çıkar
        def crowd(i):
            return min(math.hypot(pts[i][0] - q[0], pts[i][1] - q[1]) for j, q in enumerate(pts) if j != i)
        pts.pop(min(range(len(pts)), key=crowd))
    # süpürme yönü: meydanın uzun ekseni, batıdan doğuya
    order = sorted(range(len(pts)), key=lambda i: 0.906 * pts[i][0] - 0.423 * pts[i][1])
    wave = {i: k * NW // len(pts) for k, i in enumerate(order)}
    return [{"p": q, "m": rng.choice(MODELS), "w": wave[i], "j": rng.randrange(len(JIT))} for i, q in enumerate(pts)], lo


TREES, SPACING = plant()
LINES = [(mi, ki, METRO[mi], KEYS[ki]) for mi in range(len(METRO)) for ki in range(len(KEYS))]


def radius_px(tree, k=1.0):
    return R_BASE * tree["m"] * k / SC


def blocked_by(line, scale):
    """Verilen ağaç ölçeğinde çizgiyi kesen ağaçlar (dar ekrandaki iri çizime göre, payıyla)."""
    return {i for i, t in enumerate(TREES)
            if seg_dist(t["p"], line[2], line[3]) < radius_px(t, K_MOB) * scale + 0.4}


DENSE = [blocked_by(ln, 1.0) for ln in LINES]         # yoğun durumda her çizgiyi kesen ağaçlar
FINAL = [blocked_by(ln, SIZE_OPT) for ln in LINES]    # aynı ağaç yarı boyutta kalsa keser miydi
N_OPEN = round(len(LINES) * VIS_OPT / VIS_MAX)        # sonda açık kalan çizgi sayısı


def choose_final():
    """Sonda kalan 45 ağaç: görüş çizgilerinden uzak, alana yayılmış; birkaç çizgi bilerek kapalı kalır."""
    cuts = {}
    for li, s in enumerate(FINAL):
        for i in s:
            cuts.setdefault(i, set()).add(li)
    free = [i for i in range(len(TREES)) if i not in cuts]
    single = [(i, next(iter(s))) for i, s in cuts.items() if len(s) == 1]
    best = None
    for combo in itertools.combinations(single, len(LINES) - N_OPEN):
        lines = [LINES[li] for _, li in combo]
        if len({ln[0] for ln in lines}) < len(combo) or len({ln[1] for ln in lines}) < len(combo):
            continue                                   # kapanan çizgiler farklı çıkışlardan, farklı noktalara
        gap = min(math.hypot(TREES[a[0]]["p"][0] - TREES[b[0]]["p"][0], TREES[a[0]]["p"][1] - TREES[b[0]]["p"][1])
                  for a, b in itertools.combinations(combo, 2))
        if best is None or gap > best[0]:
            best = (gap, combo)
    keep = [i for i, _ in best[1]]
    while len(keep) < TREES_OPT:                      # kalanlar: seçilmişlere en uzak olan sırayla
        def far(i):
            return min(math.hypot(TREES[i]["p"][0] - TREES[j]["p"][0], TREES[i]["p"][1] - TREES[j]["p"][1]) for j in keep)
        keep.append(max((i for i in free if i not in keep), key=far))
    return set(keep), {li for _, li in best[1]}


KEEP, SHUT = choose_final()


def t_in(tree):
    return T_IN0 + tree["w"] * IN_STEP + JIT[tree["j"]]


def t_out(tree):
    return T_OUT0 + tree["w"] * OUT_STEP + JIT[tree["j"]]


# ------------------------------------------------------------------ parçalar
def poly_d(points, r=0.0):
    return "M" + "L".join(f"{f(kit.jit(X(x), r))} {f(kit.jit(Y(y), r))}" for x, y in points) + "Z"


def resample(points, step):
    out = []
    for (x1, y1), (x2, y2) in zip(points, points[1:]):
        n = max(1, round(math.hypot(x2 - x1, y2 - y1) / step))
        out += [(x1 + (x2 - x1) * k / n, y1 + (y2 - y1) * k / n) for k in range(n)]
    return out


def base_map():
    o = []
    coast = [(X(x), Y(y)) for x, y in reversed(GEO["water"][1:])]      # soldan kuzeydoğuya
    top = 8.0
    cut = next(i for i, q in enumerate(coast) if q[1] < top)           # şeridin üstüne çıkan ilk nokta
    a, b = coast[cut - 1], coast[cut]
    edge = (a[0] + (b[0] - a[0]) * (a[1] - top) / (a[1] - b[1]), top)
    y0 = coast[0][1]                                                    # sol uç fırça izi gibi eğik biter
    ring = ([(X(34), top), edge] + coast[cut - 1::-1]
            + [(X(3), y0), (X(5), y0 - 45), (X(13), top + 75), (X(24), top + 28), (X(34), top)])
    wash = kit.blob([(x + 1.2, y + 1.0) for x, y in resample(ring, 17)], 0.5, 1.6)
    o.append(f'<path class="sea fade" d="{wash}" style="--d:.3s;--t:.7s"/>')
    for x, y in ((62, 152), (176, 146), (128, 92), (262, 122), (236, 62), (332, 72)):
        o.append(f'<path class="ink h wv fade" d="M{f(X(x))} {f(Y(y))}q4 -3 8 0t8 0t8 0" style="--d:{pc(0.5 + x / 900)}s"/>')
    for k, road in enumerate(ROADS):
        o.append(f'<path class="poche fade" d="{poly_d(road)}" style="--d:{pc(0.3 + k * 0.08)}s;--t:.6s"/>')
    line = "M" + "L".join(f"{f(kit.jit(x, 0.5))} {f(kit.jit(y, 0.5))}" for x, y in coast)
    o.append(draw_path("ink coast", line, 0.1, 1.2))
    for k, zone in enumerate(ZONES):
        o.append(f'<path class="zone fade" d="{poly_d(zone, 0.35)}" style="--d:{pc(0.9 + k * 0.03)}s"/>')
    for k, (cx, cy, r) in enumerate(PUBLIC):
        o.append(f'<circle class="pub fade" cx="{f(X(cx))}" cy="{f(Y(cy))}" r="{f(r * SC)}" style="--d:{pc(1.2 + k * 0.03)}s"/>')
    for k, (a, b) in enumerate(PATHS):
        o.append(f'<path class="pth fade" d="M{f(X(a[0]))} {f(Y(a[1]))}L{f(X(b[0]))} {f(Y(b[1]))}" style="--d:{pc(1.5 + k * 0.08)}s"/>')
    return o


def view_lines():
    o = []
    for i, (mi, ki, m, k) in enumerate(LINES):
        x1, y1, x2, y2 = X(m[0]), Y(m[1]), X(k[0]), Y(k[1])
        ln = math.hypot(x2 - x1, y2 - y1)
        ux, uy = (x2 - x1) / ln, (y2 - y1) / ln
        d = f"M{f(x1 + ux * 4.5)} {f(y1 + uy * 4.5)}L{f(x2 - ux * 8)} {f(y2 - uy * 8)}"
        o.append(f'<path class="vl{" x" if i in SHUT else ""} l{i}" pathLength="1" d="{d}"/>')
    return o


def trees():
    o = []
    for keep in (False, True):                         # kalan ağaçlar üstte çizilir
        for i, t in enumerate(TREES):
            if (i in KEEP) == keep:
                o.append(f'<circle class="t{" f" if keep else ""} w{t["w"]} j{t["j"]}" cx="{f(X(t["p"][0]))}" '
                         f'cy="{f(Y(t["p"][1]))}" r="{f(R_BASE * t["m"])}"/>')
    return o


def markers():
    o = []
    for k, (cx, cy, ln, wd, ang) in enumerate(EXITS):                  # metro çıkışı: merdivenli küçük dikdörtgen
        hl, hw = ln * SC / 2, wd * SC / 2
        rect = f"M{f(-hl)} {f(-hw)}H{f(hl)}V{f(hw)}H{f(-hl)}Z"
        edge = (seg(-hl, -hw, hl, -hw, 0.3, 1.2, 0.3) + seg(hl, -hw, hl, hw, 0.3, 1.2, 0.3)
                + seg(hl, hw, -hl, hw, 0.3, 1.2, 0.3) + seg(-hl, hw, -hl, -hw, 0.3, 1.2, 0.3))
        steps = "".join(f"M{f(u * hl)} {f(-hw)}V{f(hw)}" for u in (-0.5, 0, 0.5))
        o.append(f'<g transform="translate({f(X(cx))} {f(Y(cy))}) rotate({f(ang)})"><g class="pop" style="--d:{pc(1.8 + k * 0.04)}s">'
                 f'<path class="cover" d="{rect}"/><path class="ex" d="{edge}{steps}"/></g></g>')
    for k, (mx, my) in enumerate(METRO):
        o.append(f'<circle class="mp pop" cx="{f(X(mx))}" cy="{f(Y(my))}" r="3.4" style="--d:{pc(2.0 + k * 0.03)}s"/>')
    for k, (kx, ky) in enumerate(KEYS):
        o.append(f'<g class="pop" style="--d:{pc(2.15 + k * 0.06)}s"><circle class="kr" cx="{f(X(kx))}" cy="{f(Y(ky))}" r="7"/>'
                 f'<circle class="kd" cx="{f(X(kx))}" cy="{f(Y(ky))}" r="2.8"/></g>')
    for k, h in enumerate(GEO["historic"]):
        o.append(f'<path class="solid pop" d="{poly_d(h, 0.4)}" style="--d:{pc(0.5 + k * 0.07)}s"/>')
    return o


def column():
    """Sağda: ağaç sayacı ve görünürlük ölçeği."""
    vx = BAR_X0 + BAR_LEN * (VIS_OPT - VIS_MIN) / (VIS_MAX - VIS_MIN)
    o = ['<g class="col">', '<g class="cnt">']
    o.append(f'<g class="dyn"><text class="hd" x="{CX + 98}" y="176" text-anchor="end" data-count="">{TREES_OPT}</text></g>')
    o.append('<g class="hl fade" style="--d:1s">' + text(CX + 110, 154, "ağaç", "hlt", "trees")
             + text(CX + 110, 174, f"aralık {TREES_MIN} – {TREES_MAX}", "rng", f"range {TREES_MIN} – {TREES_MAX}") + "</g>")
    o.append('</g><g class="bar">')
    o.append(text(BAR_X0 - 2, BAR_Y - 22, "görünürlük", "cap fade", "visibility", ' style="--d:1.1s"'))
    o.append(draw_path("ink", seg(BAR_X0, BAR_Y, BAR_X0 + BAR_LEN, BAR_Y, 0.3, 0, 0.5), 1.1, 0.7))
    for x, v in ((BAR_X0, VIS_MIN), (BAR_X0 + BAR_LEN, VIS_MAX)):
        o.append(f'<path class="tk fade" d="M{x} {BAR_Y - 5}V{BAR_Y + 5}" style="--d:1.4s"/>')
        o.append(text(x, BAR_Y + 20, str(v), "ax fade", None, ' text-anchor="middle" style="--d:1.4s"'))
    o.append(f'<g class="dyn"><g class="res"><circle class="rd" cx="{f(vx)}" cy="{BAR_Y}" r="6.5"/>'
             + text(vx, BAR_Y - 15, str(VIS_OPT), "rv", None, ' text-anchor="middle"') + "</g></g>")
    o.append("</g></g>")
    return o


# ------------------------------------------------------------------ stil
def kf(name, *rows):
    return f"@keyframes {NS}-{name}{{{''.join(rows)}}}"


def keyframes():
    out = []
    pop = "animation-timing-function:cubic-bezier(.3,1.5,.5,1)"
    big, small = "scale(var(--k,1))", f"scale(calc(var(--k,1)*{SIZE_OPT}))"
    for w in range(NW):
        ti, to = T_IN0 + w * IN_STEP, T_OUT0 + w * OUT_STEP
        out.append(kf(f"d{w}", f"0%,{p(ti)}%{{transform:scale(0);{pop}}}",
                      f"{p(ti + POP_IN)}%,{p(to)}%{{transform:{big};animation-timing-function:ease-in}}",
                      f"{p(to + POP_OUT)}%,100%{{transform:scale(0)}}"))
        out.append(kf(f"f{w}", f"0%,{p(ti)}%{{transform:scale(0);fill-opacity:.28;{pop}}}",
                      f"{p(ti + POP_IN)}%,{p(to)}%{{transform:{big};fill-opacity:.28;animation-timing-function:ease-in-out}}",
                      f"{p(to + SHRINK)}%,{R0}%{{transform:{small};fill-opacity:.92}}",
                      f"{R1}%,100%{{transform:scale(0);fill-opacity:.28}}"))
    # görüş çizgileri: çekilir; kesen ilk ağaç gelince söner, kesen son ağaç gidince yeniden açılır
    on, off = ".85", ".13"
    for i, (mi, ki, _, _) in enumerate(LINES):
        td = T_LN0 + mi * LN_STEP + ki * LN_SUB
        rows = [f"0%,{p(td)}%{{stroke-dashoffset:1.01;opacity:{on};animation-timing-function:cubic-bezier(.45,0,.2,1)}}",
                f"{p(td + LN_DUR)}%{{stroke-dashoffset:0;opacity:{on}}}"]
        last = on
        if DENSE[i]:
            tb = min(t_in(TREES[j]) for j in DENSE[i]) + POP_IN / 2
            rows += [f"{p(tb)}%{{stroke-dashoffset:0;opacity:{on}}}", f"{p(tb + 0.25)}%{{stroke-dashoffset:0;opacity:{off}}}"]
            last = off
            if i not in SHUT:
                tc = max(t_out(TREES[j]) + (SHRINK * 0.7 if j in KEEP else POP_OUT * 0.7) for j in DENSE[i])
                rows += [f"{p(tc)}%{{stroke-dashoffset:0;opacity:{off}}}", f"{p(tc + 0.3)}%{{stroke-dashoffset:0;opacity:{on}}}"]
                last = on
        rows += [f"{R0}%{{stroke-dashoffset:0;opacity:{last}}}", f"{R1}%,100%{{stroke-dashoffset:1.01;opacity:{on}}}"]
        out.append(kf(f"l{i}", *rows))
    # sayaç: o anda haritada duran ağaç sayısı
    per_wave = [sum(1 for t in TREES if t["w"] == w) for w in range(NW)]
    gone = [sum(1 for i, t in enumerate(TREES) if t["w"] == w and i not in KEEP) for w in range(NW)]
    rows, n = [f"0%,{p(T_IN0)}%{{--motion-count:0}}"], 0
    for w in range(NW):
        n += per_wave[w]
        rows.append(f"{p(T_IN0 + (w + 1) * IN_STEP)}%{{--motion-count:{n}}}")
    rows.append(f"{p(T_OUT0)}%{{--motion-count:{n}}}")
    for w in range(NW):
        n -= gone[w]
        rows.append(f"{p(T_OUT0 + (w + 1) * OUT_STEP)}%{{--motion-count:{n}}}")
    rows += [f"{R0}%{{--motion-count:{n}}}", f"{R1}%,100%{{--motion-count:0}}"]
    out.append(kf("cnt", *rows))
    out.append(kf("res", f"0%,{p(T_RES)}%{{opacity:0}}", f"{p(T_RES + 0.35)}%,{R0}%{{opacity:1}}", f"{R1}%,100%{{opacity:0}}"))
    out.append(kf("dip", f"0%,{p(T_DIP0)}%{{opacity:1}}", f"{p(T_DIP1)}%,{p(T_UP0)}%{{opacity:0}}", f"{p(T_UP1)}%,100%{{opacity:1}}"))
    return "\n".join(out)


def css():
    loop = "var(--T) linear var(--d0) infinite backwards"
    tloop = "var(--T) linear calc(var(--d0) + var(--j,0s)) infinite backwards"
    waves = "".join(f".{NS} .w{w}{{animation:{NS}-d{w} {tloop}}}.{NS} .f.w{w}{{animation-name:{NS}-f{w}}}" for w in range(NW))
    jit = "".join(f".{NS} .j{k}{{--j:{pc(v)}s}}" for k, v in enumerate(JIT) if v)
    lines = "".join(f".{NS} .l{i}{{animation:{NS}-l{i} {loop}}}" for i in range(len(LINES)))
    cnt_x = 397 - (CX + 98) - MOB_SHIFT                # dar ekranda sayaç suyun üstüne taşınır
    bar_x = 306 - BAR_X0 - MOB_SHIFT
    return f"""
{kit.base_css(NS)}
.{NS}{{--T:{T}s;--d0:{D0}s}}
.{NS} .sea{{fill:var(--hot);fill-opacity:.1}}
.{NS} .zone{{fill:var(--hot);fill-opacity:.06;stroke:var(--ink3);stroke-width:1;stroke-linejoin:round}}
.{NS} .pub{{fill:var(--paper);stroke:var(--ink3);stroke-width:1.2;stroke-dasharray:1.5 3.6;stroke-linecap:round}}
.{NS} .pth{{fill:none;stroke:var(--ink3);stroke-width:1;stroke-dasharray:6 5;opacity:.8}}
.{NS} .ex{{fill:none;stroke:var(--ink);stroke-width:1;stroke-linecap:round}}
.{NS} .mp{{fill:var(--ink);stroke:var(--paper);stroke-width:1.4}}
.{NS} .kr{{fill:var(--paper);stroke:var(--hot);stroke-width:2}}
.{NS} .kd{{fill:var(--hot)}}
.{NS} .vl{{fill:none;stroke:var(--hot);stroke-width:1.15;stroke-linecap:round;stroke-dasharray:1 2;opacity:.85}}
.{NS} .vl.x{{opacity:.13}}
.{NS} .t{{fill:var(--hot);fill-opacity:.28;transform-box:fill-box;transform-origin:50% 50%;transform:scale(0)}}
.{NS} .t.f{{transform:scale(calc(var(--k,1)*{SIZE_OPT}));fill-opacity:.92}}
.{NS} .tk{{fill:none;stroke:var(--ink);stroke-width:1.3;stroke-linecap:round}}
.{NS} .ax{{font-size:12px;fill:var(--ink3)}}
.{NS} .cap{{font-size:13px;fill:var(--ink3)}}
.{NS} .hd{{font-size:54px;font-weight:600;fill:var(--hot);--motion-count:{TREES_OPT};animation:{NS}-cnt {loop}}}
.{NS} .hlt{{font-size:15px;fill:var(--ink2)}}
.{NS} .rng{{font-size:13px;fill:var(--ink3)}}
.{NS} .rd{{fill:var(--hot);stroke:var(--paper);stroke-width:2}}
.{NS} .rv{{font-size:17px;font-weight:600;fill:var(--hot)}}
.{NS} .res{{animation:{NS}-res {loop}}}
.{NS} .dyn{{animation:{NS}-dip {loop}}}
{waves}
{jit}
{lines}
{keyframes()}
@media (min-width:769px) and (max-width:1100px){{.{NS} .ax{{font-size:15px}}.{NS} .cap{{font-size:16px}}.{NS} .hlt{{font-size:18px}}.{NS} .rng{{font-size:15px}}.{NS} .rv{{font-size:20px}}}}
@media (max-width:768px){{.{NS}{{--k:{K_MOB}}}.{NS} .root{{transform:translateX({pc(MOB_SHIFT)}px)}}.{NS} .cnt{{transform:translate({pc(cnt_x)}px,-112px)}}.{NS} .bar{{transform:translate({pc(bar_x)}px,-128px)}}.{NS} .hl{{transform:translateY(20px)}}.{NS} .rng,.{NS} .wv{{display:none}}{kit.base_css_mobile(NS)}.{NS} .zone{{stroke-width:1.5}}.{NS} .pub{{stroke-width:1.8}}.{NS} .pth{{stroke-width:1.5}}.{NS} .ex{{stroke-width:1.8}}.{NS} .vl{{stroke-width:1.7}}.{NS} .kr{{stroke-width:2.8}}.{NS} .tk{{stroke-width:1.9}}.{NS} .ax{{font-size:18px}}.{NS} .cap{{font-size:19px}}.{NS} .hlt{{font-size:22px}}.{NS} .rv{{font-size:23px}}}}
""".strip()


# ------------------------------------------------------------------ çizim
def build():
    o = [kit.svg_open(NS, W, H, "xMidYMid slice"), f"<style>{css()}</style>", '<g class="root">']
    o += base_map()
    o.append('<g class="dyn">')
    o += view_lines()
    o += trees()
    o.append("</g>")
    o += markers()
    o += column()
    o.append("</g></svg>")
    return "\n".join(o)


def check():
    assert len(TREES) == TREES_MAX and len(KEEP) == TREES_OPT
    assert TREES_MIN <= TREES_OPT <= TREES_MAX and VIS_MIN <= VIS_OPT <= VIS_MAX
    assert all(plantable(t["p"]) for t in TREES)                       # ağaçlar yalnızca dikilebilir alanda
    shut = {li for li in range(len(LINES)) if FINAL[li] & KEEP}        # sonda kalan ağaçların kestiği çizgiler
    assert shut == SHUT and len(LINES) - len(shut) == N_OPEN
    for li in set(range(len(LINES))) - SHUT:                           # açık çizgiye hiçbir kalan ağaç değmez
        assert all(seg_dist(TREES[i]["p"], LINES[li][2], LINES[li][3]) > radius_px(TREES[i], K_MOB) * SIZE_OPT for i in KEEP)
    assert max(t_in(t) for t in TREES) + POP_IN < T_OUT0 and max(t_out(t) for t in TREES) + SHRINK < T_RES + 0.4
    assert T_DIP1 <= T_RESET and T_RESET + max(JIT) <= T_UP0           # sıfırlama görünmezken olur
    assert T_LN0 + (len(METRO) - 1) * LN_STEP + (len(KEYS) - 1) * LN_SUB + LN_DUR < T_IN0
    print(f"ağaç {len(TREES)} (aralık {SPACING:.2f} px), kalan {len(KEEP)}; çizgi {len(LINES)}, "
          f"yoğunken kesilen {sum(1 for s in DENSE if s)}, sonda açık {N_OPEN}")


if __name__ == "__main__":
    check()
    kit.write(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "uskudar-header.svg"), build())
