# -*- coding: utf-8 -*-
"""MaskRCNN in Grasshopper başlık animasyonunun üreteci.

Eklentinin sekiz modülü, sayfada anlatıldığı sırayla, soldan sağa bir
Grasshopper zinciri olarak durur. Veri telden tele ilerledikçe her bileşen
çalışır ve yanında ne yaptığı küçük bir sahneyle görünür:

  Setup      beş bağımlılık tek tek kurulur (Git, Miniconda, Mask R-CNN, COCO, Python)
  Splitter   etiketli görseller eğitim ve doğrulama setine ayrılır
  Merger     yeni görseller dağılımı bozmadan iki sete eklenir
  Cleaner    kendini kesen, çerçeve dışına taşan etiket onarılır (altı tanılama kontrolü)
  Training   kayıp eğrisi düşer
  Detection  cephede pencere ve kapı maskelenir, kutulanır, etiketlenir
  Analyzer   sınıf bazlı çubuklar, mAP
  Comparator modeller tabloda karşılaştırılır, en iyisi işaretlenir; CSV, MD, LaTeX

Sayfada olmayan hiçbir sayı yazılmaz: bölme oranı, güven skoru, mAP değeri ve
bileşen sayısı (sayfada 95 ve 8 diye iki farklı sayı var) çizimde yoktur.
Çubukların, eğrilerin ve tablo satırlarının boyu yalnızca şemadır.

Dar ekranda şerit zincirin yarısını gösterir; görüntü, çalışan bileşeni
izleyerek soldan sağa kayar.

Kullanım:  python motion/maskrcnn-header.py     -> motion/maskrcnn-header.svg
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit                                           # noqa: E402
from kit import f, pc, seg, draw_path, text          # noqa: E402

kit.seed(101)
NS = "mmr"

# ------------------------------------------------------------------ yerleşim
W, H = 1200, 420
NAMES = ["Setup", "Splitter", "Merger", "Cleaner", "Training", "Detection", "Analyzer", "Comparator"]
N = len(NAMES)
PITCH = 150
NY = 206
DY = [-7, 6, -5, 8, -6, 7, -8, 5]        # gerçek bir kanvastaki gibi hafif şaşırtmalı
BW, BH = 78, 54
GRIP = 10                                # bağlantı uçlarının bileşen eksenine uzaklığı
# teller: (çıkış ucu, giriş ucu) — veri seti hattında eğitim ve doğrulama iki ayrı tel
LINKS = [[(1, -1)], [(-1, -1), (1, 1)], [(-1, -1), (1, 1)], [(-1, -1), (1, 1)], [(-1, 1)], [(1, -1)], [(-1, -1), (1, 1)]]
SETUP = ["Git", "Miniconda", "Mask R-CNN", "COCO", "Python"]          # tek butonla kurulanlar
CHECKS = 6                               # Dataset Cleaner'ın tanılama kontrolü sayısı
EXPORTS = ["CSV", "MD", "LaTeX"]
MOB_PAN = 285                            # dar ekranda görünen pencere: 630 birim (şeridin yarısı)


def cx(i):
    return 75 + PITCH * i


def cy(i):
    return NY + DY[i]


def above(i):
    """Sahnesi bileşenin üstünde duranların alt sınırı."""
    return cy(i) - BH / 2 - 14


def below(i):
    """Sahnesi bileşenin altında duranların üst sınırı (adın altı)."""
    return cy(i) + BH / 2 + 34


# ------------------------------------------------------------------ zamanlama (sn)
T = 16.0
D0 = 1.6
T0, STEP = 0.5, 1.35
T_DIP0, T_DIP1, T_RESET, T_UP0, T_UP1 = 14.2, 14.6, 14.7, 15.0, 15.4


def ts(i):
    """i. bileşenin çalışmaya başladığı an."""
    return T0 + STEP * i


def p(t):
    return pc(t / T * 100)


R0, R1 = p(T_RESET - 0.01), p(T_RESET)


# ------------------------------------------------------------------ hareket kayıtları
class Moves:
    """Her (tür, an, süre) üçlüsü için bir sınıf ve bir keyframes üretir; aynısı yeniden kullanılır."""

    BASE = {"show": "", "hide": " h0", "pop": " pp", "grow": " gr", "draw": " dr", "fly": " pp", "pulse": " pl", "scan": " h0"}

    def __init__(self):
        self.keys = {}

    def cls(self, kind, t, dur=0.35):
        key = (kind, round(t, 3), round(dur, 3))
        if key not in self.keys:
            self.keys[key] = f"k{len(self.keys)}"
        return self.keys[key] + self.BASE[kind]

    def css(self):
        loop = "var(--T) linear var(--d0) infinite backwards"
        out = []
        for (kind, t, dur), name in self.keys.items():
            a, b = p(t), p(t + dur)
            if kind == "show":
                rows = f"0%,{a}%{{opacity:0}}{b}%,{R0}%{{opacity:1}}{R1}%,100%{{opacity:0}}"
            elif kind == "hide":
                rows = f"0%,{a}%{{opacity:1}}{b}%,{R0}%{{opacity:0}}{R1}%,100%{{opacity:1}}"
            elif kind == "pop":
                rows = (f"0%,{a}%{{transform:scale(0);animation-timing-function:cubic-bezier(.3,1.5,.5,1)}}"
                        f"{b}%,{R0}%{{transform:scale(1)}}{R1}%,100%{{transform:scale(0)}}")
            elif kind == "grow":
                rows = (f"0%,{a}%{{transform:scaleY(0);animation-timing-function:cubic-bezier(.3,1.3,.5,1)}}"
                        f"{b}%,{R0}%{{transform:scaleY(1)}}{R1}%,100%{{transform:scaleY(0)}}")
            elif kind == "draw":
                rows = (f"0%,{a}%{{stroke-dashoffset:1.01;animation-timing-function:cubic-bezier(.45,0,.2,1)}}"
                        f"{b}%,{R0}%{{stroke-dashoffset:0}}{R1}%,100%{{stroke-dashoffset:1.01}}")
            elif kind == "fly":
                start = "transform:translate(var(--dx),var(--dy)) scale(.4);opacity:0"
                rows = (f"0%,{a}%{{{start};animation-timing-function:cubic-bezier(.3,0,.2,1)}}{p(t + 0.12)}%{{opacity:1}}"
                        f"{b}%,{R0}%{{transform:translate(0,0) scale(1);opacity:1}}{R1}%,100%{{{start}}}")
            elif kind == "pulse":
                rows = f"0%,{a}%{{stroke-dashoffset:.3}}{b}%,100%{{stroke-dashoffset:-1.05}}"
            else:                                      # scan: tarama çizgisi cepheyi boydan boya geçer
                rows = (f"0%,{a}%{{transform:translateX(0);opacity:0}}{p(t + 0.02)}%{{opacity:1}}"
                        f"{b}%{{transform:translateX(var(--sw));opacity:1}}{p(t + dur + 0.15)}%,100%{{transform:translateX(var(--sw));opacity:0}}")
            out.append(f"@keyframes {NS}-{name}{{{rows}}}.{NS} .{name}{{animation:{NS}-{name} {loop}}}")
        return "\n".join(out)


A = Moves()


def dyn(*parts):
    """Her turda sönüp baştan başlayan parçalar."""
    return '<g class="dyn">' + "".join(parts) + "</g>"


# ------------------------------------------------------------------ zincir
def wire_d(i, a, b):
    x1, y1 = cx(i) + BW / 2 + 3.2, cy(i) + a * GRIP
    x2, y2 = cx(i + 1) - BW / 2 - 3.2, cy(i + 1) + b * GRIP
    h = (x2 - x1) * 0.55
    return f"M{f(x1)} {f(y1)}C{f(x1 + h)} {f(y1)} {f(x2 - h)} {f(y2)} {f(x2)} {f(y2)}"


def wires():
    o = []
    for i, link in enumerate(LINKS):
        for a, b in link:
            d = wire_d(i, a, b)
            o.append(draw_path("wire", d, 0.35 + i * 0.12, 0.5))
            o.append(f'<path class="{A.cls("pulse", ts(i + 1) - 0.6, 0.55)}" pathLength="1" d="{d}"/>')
    return o


def node(i):
    x, y = cx(i), cy(i)
    x0, y0 = x - BW / 2, y - BH / 2
    o = [f'<g class="fade" style="--d:{pc(0.15 + i * 0.12)}s">']
    o.append(f'<path class="cover" d="M{f(x0)} {f(y0)}h{BW}v{BH}h{-BW}Z"/>')
    o.append(dyn(f'<g class="{A.cls("show", ts(i), 0.3)}">{kit.wash(x0, y0, BW, BH)}</g>'))
    o.append(f'<path class="ink" d="{kit.rect_sk(x0, y0, BW, BH, 0.4, 2.0)}"/>')
    o.append(f'<path class="solid" d="{kit.quad(x, y, 15, BH - 14, 0.5)}"/>')            # ad şeridi
    for side, has in ((-1, i > 0), (1, i < N - 1)):
        if has:
            for g in (-1, 1):
                o.append(f'<circle class="grip" cx="{f(x + side * BW / 2)}" cy="{f(y + g * GRIP)}" r="3.2"/>')
    o.append(text(x, y + BH / 2 + 20, NAMES[i], "nm", None, ' text-anchor="middle"'))
    o.append("</g>")
    return o


def tile(x, y, cls, start=None, t=None):
    """Küçük görsel karosu; start verilirse oradan uçarak gelir."""
    if start is None:
        return f'<rect class="tile {cls}" x="{f(x)}" y="{f(y)}" width="18" height="13" rx="1.5"/>'
    dx, dy = start[0] - (x + 9), start[1] - (y + 6.5)
    return (f'<rect class="tile {cls} {A.cls("fly", t, 0.6)}" x="{f(x)}" y="{f(y)}" width="18" height="13" rx="1.5" '
            f'style="--dx:{f(dx)}px;--dy:{f(dy)}px"/>')


TICK = "M-3.4 .2l2.5 2.7l4.4 -5.6"


# ------------------------------------------------------------------ sahneler
def scene_setup(i):
    x, y, t = cx(i), below(i), ts(i)
    o = [f'<g class="fade" style="--d:{pc(0.5 + i * 0.12)}s">']
    for k, name in enumerate(SETUP):
        ry = y + 14 + 23 * k
        o.append(f'<circle class="ring" cx="{f(x - 46)}" cy="{f(ry - 4)}" r="6"/>')
        o.append(text(x - 34, ry, name, "sm"))
        o.append(dyn(f'<g transform="translate({f(x - 46)} {f(ry - 4)})"><path class="tick {A.cls("pop", t + 0.1 + k * 0.13, 0.3)}" d="{TICK}"/></g>'))
    o.append("</g>")
    return o


def scene_splitter(i):
    x, y, t = cx(i), above(i), ts(i)
    src = (x, cy(i) - BH / 2 - 4)                     # karolar bileşenden çıkar
    cols, rows = (x - 50, x - 29, x - 8), (y - 62, y - 46)
    o = [f'<g class="fade" style="--d:{pc(0.5 + i * 0.12)}s">']
    o.append(text(x - 20, y - 69, "eğitim", "sm", "train", ' text-anchor="middle"'))
    o.append(text(x + 35, y - 14, "doğrulama", "sm", "val", ' text-anchor="middle"'))
    parts = []
    for k, (tx, ty) in enumerate([(c, r) for r in rows for c in cols]):
        parts.append(tile(tx, ty, "a", src, t + 0.05 * k))
    for k, ty in enumerate(rows):
        parts.append(tile(x + 26, ty, "b", src, t + 0.35 + 0.08 * k))
    o.append(dyn(*parts))
    o.append("</g>")
    return o


def scene_merger(i):
    x, y, t = cx(i), below(i), ts(i)
    src = (x, cy(i) + BH / 2 + 4)
    cols, rows = (x - 50, x - 29, x - 8), (y + 8, y + 24)
    o = [f'<g class="fade" style="--d:{pc(0.5 + i * 0.12)}s">']
    o += [tile(c, r, "a") for r in rows for c in cols] + [tile(x + 26, r, "b") for r in rows]
    new = [tile(c, y + 40, "n", src, t + 0.08 * k) for k, c in enumerate(cols)] + [tile(x + 26, y + 40, "n", src, t + 0.3)]
    plus = f'<path class="plus {A.cls("pop", t + 0.45, 0.3)}" d="M{f(x - 66)} {f(y + 46.5)}h9M{f(x - 61.5)} {f(y + 42)}v9"/>'
    o.append(dyn(*new, plus))
    o.append("</g>")
    return o


def scene_cleaner(i):
    x, y, t = cx(i) - 8, above(i), ts(i)              # dar ekranın son karesinde çerçeve kenarda kalmasın diye hafif solda
    fx, fy, fw, fh = x - 48, y - 78, 96, 66           # görsel çerçevesi
    good = [(x - 30, fy + 12), (x + 26, fy + 9), (x + 30, fy + 54), (x - 33, fy + 56)]
    bad = [good[0], good[2], (x + 62, fy + 3), good[3]]                # kendini keser, bir köşesi çerçevenin dışında
    assert bad[2][0] > fx + fw
    pd = lambda pts: "M" + "L".join(f"{f(a)} {f(b)}" for a, b in pts) + "Z"      # noqa: E731
    o = [f'<g class="fade" style="--d:{pc(0.5 + i * 0.12)}s">']
    o.append(f'<path class="ink h" d="{kit.rect_sk(fx, fy, fw, fh, 0.4, 1.8)}"/>')
    dots = "".join(f'<circle class="vtx" cx="{f(a)}" cy="{f(b)}" r="2.2"/>' for a, b in bad)
    o.append(dyn(f'<g class="{A.cls("hide", t + 0.1, 0.4)}"><path class="bad" d="{pd(bad)}"/>{dots}</g>',
                 f'<path class="fixf {A.cls("show", t + 0.75, 0.35)}" d="{pd(good)}"/>',
                 f'<path class="fix {A.cls("draw", t + 0.25, 0.7)}" pathLength="1" d="{pd(good)}"/>'))
    for k in range(CHECKS):                            # altı tanılama kontrolü
        dx = x + (k - (CHECKS - 1) / 2) * 14
        o.append(f'<circle class="ring" cx="{f(dx)}" cy="{f(fy - 12)}" r="3.6"/>')
        o.append(dyn(f'<circle class="okd {A.cls("pop", t + 0.2 + k * 0.1, 0.25)}" cx="{f(dx)}" cy="{f(fy - 12)}" r="3.6"/>'))
    o.append("</g>")
    return o


def scene_training(i):
    x, y, t = cx(i) + 6, below(i), ts(i)              # dar ekranın ilk karesinde eksen kenarda kalmasın diye hafif sağda
    ox, oy, top, right = x - 48, y + 122, y + 12, x + 50
    o = [f'<g class="fade" style="--d:{pc(0.5 + i * 0.12)}s">']
    o.append(f'<path class="ink h" d="{seg(ox, top, ox, oy, 0.3, 2, 0.4)}{seg(ox, oy, right, oy, 0.3, 2, 0.4)}"/>')
    o.append(text(right, top + 12, "kayıp", "sm", "loss", ' text-anchor="end"'))
    span = oy - top - 14
    tr, va = [], []
    for k in range(23):                                # şematik: hızla düşüp yataylaşan iki eğri
        px = ox + 5 + k * 4.0
        tr.append((px, oy - 6 - span * math.exp(-k / 5.2) + kit.rnd.uniform(-2.2, 2.2) * math.exp(-k / 9)))
        va.append((px, oy - 15 - (span - 12) * math.exp(-k / 6.4) + kit.rnd.uniform(-2.6, 2.6) * math.exp(-k / 14)))
    line = lambda pts: "M" + "L".join(f"{f(a)} {f(b)}" for a, b in pts)           # noqa: E731
    o.append(dyn(f'<g class="{A.cls("show", t + 0.2, 0.9)}"><path class="val" d="{line(va)}"/></g>',
                 f'<path class="loss {A.cls("draw", t + 0.05, 1.0)}" pathLength="1" d="{line(tr)}"/>'))
    o.append("</g>")
    return o


def scene_detection(i):
    x, y, t = cx(i), above(i), ts(i)
    wx, wt, ww, gy = x - 70, y - 136, 140, y - 22     # duvar: sol, üst, genişlik; zemin çizgisi
    sweep = 0.9
    objs = [(x - 56, wt + 14, 29, 36), (x - 14.5, wt + 14, 29, 36), (x + 27, wt + 14, 29, 36),      # üst pencereler
            (x - 56, wt + 68, 29, 32), (x + 27, wt + 68, 29, 32), (x - 15, wt + 64, 30, gy - wt - 64)]   # alt pencereler, kapı
    o = [f'<g class="fade" style="--d:{pc(0.5 + i * 0.12)}s">']
    o.append(f'<path class="ink h" d="{seg(wx - 9, gy, wx + ww + 9, gy, 0.3, 0, 0.4)}{seg(wx, gy, wx, wt, 0.3, 1.5, 0.3)}'
             f'{seg(wx - 4, wt, wx + ww + 4, wt, 0.3, 0, 0.4)}{seg(wx + ww, wt, wx + ww, gy, 0.3, 1.5, 0.3)}"/>')
    o.append('<path class="fur" d="' + "".join(kit.rect_sk(a, b, c, d, 0.3, 1.2) for a, b, c, d in objs[:5])
             + seg(objs[5][0], gy, objs[5][0], objs[5][1], 0.3, 1.2, 0.3) + seg(objs[5][0], objs[5][1], objs[5][0] + 30, objs[5][1], 0.3, 1.2, 0.3)
             + seg(objs[5][0] + 30, objs[5][1], objs[5][0] + 30, gy, 0.3, 1.2, 0.3) + '"/>')
    parts = []
    for a, b, c, d in objs:                            # tarama çizgisi üstünden geçince maske ve kutu belirir
        hit = t + 0.1 + sweep * (a + c / 2 - wx) / ww
        parts.append(f'<rect class="mask {A.cls("show", hit, 0.25)}" x="{f(a + 1)}" y="{f(b + 1)}" width="{f(c - 2)}" height="{f(d - 2)}"/>')
        parts.append(f'<rect class="bbox {A.cls("show", hit + 0.1, 0.25)}" x="{f(a - 3)}" y="{f(b - 3)}" width="{f(c + 6)}" height="{f(d + 6)}"/>')
    parts.append(f'<path class="scan {A.cls("scan", t + 0.1, sweep)}" d="M{f(wx)} {f(wt - 5)}V{f(gy + 4)}" style="--sw:{ww}px"/>')
    parts.append(f'<g class="{A.cls("show", t + 0.45, 0.3)}">' + text(objs[0][0] - 3, wt - 7, "pencere", "tag", "window") + "</g>")
    parts.append(f'<g class="{A.cls("show", t + 0.75, 0.3)}">' + text(x, gy + 15, "kapı", "tag", "door", ' text-anchor="middle"') + "</g>")
    o.append(dyn(*parts))
    o.append("</g>")
    return o


def scene_analyzer(i):
    x, y, t = cx(i), below(i), ts(i)
    base = y + 122
    o = [f'<g class="fade" style="--d:{pc(0.5 + i * 0.12)}s">']
    o.append(f'<path class="ink h" d="{seg(x - 50, base, x + 50, base, 0.3, 0, 0.4)}"/>')
    o.append(text(x - 50, y + 14, "mAP", "sm"))
    parts = []
    for k, (gx, h1, h2) in enumerate(((x - 30, 66, 54), (x, 80, 62), (x + 30, 52, 70))):         # şematik: sınıf başına iki çubuk
        parts.append(f'<rect class="bar1 {A.cls("grow", t + 0.1 + k * 0.14, 0.45)}" x="{f(gx - 11)}" y="{f(base - h1)}" width="10" height="{h1}"/>')
        parts.append(f'<rect class="bar2 {A.cls("grow", t + 0.18 + k * 0.14, 0.45)}" x="{f(gx + 1)}" y="{f(base - h2)}" width="10" height="{h2}"/>')
    o.append(dyn(*parts))
    o.append("</g>")
    return o


def scene_comparator(i):
    x, y, t = cx(i), above(i), ts(i)
    top = y - 108
    rows = [top + 16, top + 36, top + 56]
    best = 1
    o = [f'<g class="fade" style="--d:{pc(0.5 + i * 0.12)}s">']
    o.append(f'<path class="ink h" d="{seg(x - 64, top, x + 60, top, 0.3, 0, 0.4)}{seg(x - 64, top + 68, x + 60, top + 68, 0.3, 0, 0.4)}"/>')
    parts = [f'<path class="top {A.cls("show", t + 0.65, 0.3)}" d="{kit.blob([(x - 66, rows[best] - 9), (x - 2, rows[best] - 10), (x + 62, rows[best] - 9), (x + 62, rows[best] + 9), (x - 2, rows[best] + 10), (x - 66, rows[best] + 9)], 0.8, 1.6)}"/>']
    for k, ry in enumerate(rows):                      # her satır bir model; hücrelerin boyu şematik
        cells = "".join(f"M{f(x + a)} {f(ry)}h{f(b + kit.rnd.uniform(-5, 3))}" for a, b in ((-42, 26), (-6, 22), (26, 20)))
        parts.append(f'<g class="{A.cls("show", t + 0.1 + k * 0.14, 0.3)}"><circle class="{"okd" if k == best else "ring"}" cx="{f(x - 55)}" cy="{f(ry)}" r="3.6"/>'
                     f'<path class="cell" d="{cells}"/></g>')
    parts.append(f'<g transform="translate({f(x + 55)} {f(rows[best])})"><path class="tick {A.cls("pop", t + 0.75, 0.3)}" d="{TICK}"/></g>')
    tx = x - 63
    for k, name in enumerate(EXPORTS):                 # etiket kutuları dar ekrandaki yazı boyuna göre açılır
        w = len(name) * 8.4 + 10
        parts.append(f'<g class="{A.cls("pop", t + 0.85 + k * 0.14, 0.3)}"><rect class="chip" x="{f(tx)}" y="{f(y - 24)}" width="{f(w)}" height="19" rx="4"/>'
                     + text(tx + w / 2, y - 10.5, name, "chp", None, ' text-anchor="middle"') + "</g>")
        tx += w + 6
    assert tx - 6 <= W - 10
    o.append(dyn(*parts))
    o.append("</g>")
    return o


SCENES = [scene_setup, scene_splitter, scene_merger, scene_cleaner, scene_training, scene_detection, scene_analyzer, scene_comparator]


# ------------------------------------------------------------------ stil
def css():
    loop = "var(--T) linear var(--d0) infinite backwards"
    pan0, pan1 = ts(1) + 0.3, ts(6) - 0.3
    return f"""
{kit.base_css(NS)}
.{NS}{{--T:{T}s;--d0:{D0}s}}
.{NS} .wire{{fill:none;stroke:var(--ink2);stroke-width:1.2;stroke-linecap:round}}
.{NS} .pl{{fill:none;stroke:var(--hot);stroke-width:3;stroke-linecap:round;stroke-dasharray:.3 2;stroke-dashoffset:.3}}
.{NS} .grip{{fill:var(--paper);stroke:var(--ink);stroke-width:1.3}}
.{NS} .nm{{font-size:13px;fill:var(--ink)}}
.{NS} .sm{{font-size:11.5px;fill:var(--ink3)}}
.{NS} .ring{{fill:var(--paper);stroke:var(--ink3);stroke-width:1.1}}
.{NS} .tick{{fill:none;stroke:var(--hot);stroke-width:2;stroke-linecap:round;stroke-linejoin:round}}
.{NS} .okd{{fill:var(--hot)}}
.{NS} .tile{{fill:var(--paper);stroke:var(--ink2);stroke-width:1.1}}
.{NS} .tile.b{{stroke-dasharray:2.5 2}}
.{NS} .tile.n{{fill:var(--hot);fill-opacity:.22;stroke:var(--hot);stroke-width:1.4}}
.{NS} .plus{{fill:none;stroke:var(--hot);stroke-width:1.8;stroke-linecap:round}}
.{NS} .bad{{fill:none;stroke:var(--ink2);stroke-width:1.2;stroke-dasharray:3 2.5;stroke-linejoin:round}}
.{NS} .vtx{{fill:var(--ink2)}}
.{NS} .fix{{fill:none;stroke:var(--hot);stroke-width:1.9;stroke-linejoin:round}}
.{NS} .fixf{{fill:var(--hot);fill-opacity:.17}}
.{NS} .loss{{fill:none;stroke:var(--hot);stroke-width:1.9;stroke-linecap:round;stroke-linejoin:round}}
.{NS} .val{{fill:none;stroke:var(--ink3);stroke-width:1.2;stroke-dasharray:3 3;stroke-linejoin:round}}
.{NS} .mask{{fill:var(--hot);fill-opacity:.34}}
.{NS} .bbox{{fill:none;stroke:var(--hot);stroke-width:1.2}}
.{NS} .scan{{fill:none;stroke:var(--hot);stroke-width:1.6;stroke-linecap:round}}
.{NS} .tag{{font-size:11px;fill:var(--hot)}}
.{NS} .bar1{{fill:var(--hot);fill-opacity:.8}}
.{NS} .bar2{{fill:var(--paper);stroke:var(--ink2);stroke-width:1.1}}
.{NS} .cell{{fill:none;stroke:var(--ink2);stroke-width:1.5;stroke-linecap:round}}
.{NS} .chip{{fill:var(--paper);stroke:var(--hot);stroke-width:1.2}}
.{NS} .chp{{font-size:11px;fill:var(--hot)}}
.{NS} .dr{{stroke-dasharray:1 2}}
.{NS} .pp{{transform-box:fill-box;transform-origin:50% 50%}}
.{NS} .gr{{transform-box:fill-box;transform-origin:50% 100%}}
.{NS} .h0{{opacity:0}}
.{NS} .dyn{{animation:{NS}-dip {loop}}}
@keyframes {NS}-dip{{0%,{p(T_DIP0)}%{{opacity:1}}{p(T_DIP1)}%,{p(T_UP0)}%{{opacity:0}}{p(T_UP1)}%,100%{{opacity:1}}}}
@keyframes {NS}-pan{{0%,{p(pan0)}%{{transform:translateX({MOB_PAN}px)}}{p(pan1)}%,{p(T_DIP0)}%{{transform:translateX(-{MOB_PAN}px);animation-timing-function:cubic-bezier(.6,0,.3,1)}}{p(T_UP0)}%,100%{{transform:translateX({MOB_PAN}px)}}}}
{A.css()}
@media (min-width:769px) and (max-width:1100px){{.{NS} .nm{{font-size:15.5px}}.{NS} .sm{{font-size:13.5px}}.{NS} .tag{{font-size:13px}}.{NS} .chp{{font-size:12.5px}}}}
@media (max-width:768px){{.{NS} .root{{transform:translateX(-{MOB_PAN}px);animation:{NS}-pan {loop}}}{kit.base_css_mobile(NS)}.{NS} .wire{{stroke-width:1.8}}.{NS} .pl{{stroke-width:4}}.{NS} .grip{{stroke-width:1.8}}.{NS} .ring{{stroke-width:1.6}}.{NS} .tile{{stroke-width:1.6}}.{NS} .bad{{stroke-width:1.7}}.{NS} .fix,.{NS} .loss{{stroke-width:2.6}}.{NS} .val{{stroke-width:1.7}}.{NS} .bbox{{stroke-width:1.7}}.{NS} .cell{{stroke-width:2}}.{NS} .bar2{{stroke-width:1.6}}.{NS} .chip{{stroke-width:1.6}}.{NS} .nm{{font-size:19px}}.{NS} .sm{{font-size:16px}}.{NS} .tag{{font-size:15.5px}}.{NS} .chp{{font-size:14px}}}}
""".strip()


# ------------------------------------------------------------------ çizim
def build():
    body = wires()
    for i in range(N):
        body += node(i)
    for i, scene in enumerate(SCENES):
        body += scene(i)
    return "\n".join([kit.svg_open(NS, W, H, "xMidYMid slice"), f"<style>{css()}</style>", '<g class="root">'] + body + ["</g></svg>"])


def check():
    assert N == 8 and len(SCENES) == N and len(LINKS) == N - 1
    assert cx(0) - BW / 2 > 0 and cx(N - 1) + BW / 2 < W
    for i in range(N):                                 # çalışan bileşen dar ekrandaki pencerede kalır
        t = ts(i)
        pan0, pan1 = ts(1) + 0.3, ts(6) - 0.3
        shift = MOB_PAN - 2 * MOB_PAN * min(1.0, max(0.0, (t - pan0) / (pan1 - pan0)))
        assert 285 + 45 <= cx(i) + shift <= 915 - 45, (i, cx(i) + shift)
    assert ts(N - 1) + 1.4 < T_DIP0 and T_DIP1 <= T_RESET <= T_UP0
    assert cx(3) - 8 + 48 < 570 and cx(4) + 6 - 48 > 630        # dar ekranın ilk (0 – 630) ve son (570 – 1200) penceresi


if __name__ == "__main__":
    check()
    here = os.path.dirname(os.path.abspath(__file__))
    kit.write(sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, "maskrcnn-header.svg"), build())
