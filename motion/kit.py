# -*- coding: utf-8 -*-
"""Motion animasyonlarının ortak çizim yardımcıları.

Bütün animasyonlar aynı kalemle çizilsin diye çizgi, leke ve giriş
hareketleri burada durur. Her üreteç (ör. 1284-header.py) bu dosyayı içe
aktarır, kendi tohumunu verir ve tek bir SVG dosyası yazar.

Ortak dil:
  - ince mürekkep çizgisi, hafif yaylı, köşelerde birbirini aşan uçlar
  - kalıcı olan siyah dolu, değişen şey sayfanın vurgu renginde (--accent)
  - çizginin dışına hafif taşan soluk leke
  - yazı yok ya da çok az; sayılar mono yazı tipiyle
"""
import math
import random

rnd = random.Random()


def seed(n):
    """Sabit tohum: aynı betik her çalıştırmada aynı çizimi üretir."""
    rnd.seed(n)


# ------------------------------------------------------------------ sayı biçimleri
def f(v):
    s = f"{v:.1f}"
    return s[:-2] if s.endswith(".0") else s


def pc(v):
    s = f"{v:.3f}".rstrip("0").rstrip(".")
    return s if s else "0"


def jit(v, r):
    return v + rnd.uniform(-r, r)


# ------------------------------------------------------------------ çizgi
def seg(x1, y1, x2, y2, r=0.5, over=0.0, bow=0.9):
    """Elle çekilmiş gibi hafif yaylı, uçları hafif oynak tek bir çizgi."""
    dx, dy = x2 - x1, y2 - y1
    ln = math.hypot(dx, dy)
    ux, uy = dx / ln, dy / ln
    x1, y1, x2, y2 = x1 - ux * over, y1 - uy * over, x2 + ux * over, y2 + uy * over
    b = rnd.uniform(-bow, bow) * min(1.0, ln / 240)
    cx, cy = (x1 + x2) / 2 - uy * b, (y1 + y2) / 2 + ux * b
    return f"M{f(jit(x1, r))} {f(jit(y1, r))}Q{f(cx)} {f(cy)} {f(jit(x2, r))} {f(jit(y2, r))}"


def rect_sk(x, y, w, h, r=0.45, over=2.4):
    """Köşeleri hafif taşan eskiz dikdörtgen."""
    return (seg(x, y, x + w, y, r, over, 0.5) + seg(x + w, y, x + w, y + h, r, over, 0.5)
            + seg(x + w, y + h, x, y + h, r, over, 0.5) + seg(x, y + h, x, y, r, over, 0.5))


def quad(cx, cy, w, h, r=0.5):
    """Köşeleri hafif oynak dolu dörtgen (kolon, dikme)."""
    pts = [(cx - w / 2, cy - h / 2), (cx + w / 2, cy - h / 2),
           (cx + w / 2, cy + h / 2), (cx - w / 2, cy + h / 2)]
    return "M" + "L".join(f"{f(jit(x, r))} {f(jit(y, r))}" for x, y in pts) + "Z"


def circ(cx, cy, r):
    return f"M{f(cx - r)} {f(cy)}a{r} {r} 0 1 0 {2 * r} 0a{r} {r} 0 1 0 {-2 * r} 0Z"


# ------------------------------------------------------------------ leke
def blob(pts, grow=1.6, rough=2.4):
    """Noktaları merkezden dışarı rastgele itip yumuşak kapalı bir eğri çizer."""
    n = len(pts)
    cx = sum(q[0] for q in pts) / n
    cy = sum(q[1] for q in pts) / n
    moved = []
    for px, py in pts:
        vx, vy = px - cx, py - cy
        ln = math.hypot(vx, vy) or 1
        off = grow + rnd.uniform(-rough, rough)
        moved.append((px + vx / ln * off, py + vy / ln * off))
    mids = [((moved[i][0] + moved[(i + 1) % n][0]) / 2, (moved[i][1] + moved[(i + 1) % n][1]) / 2)
            for i in range(n)]
    d = f"M{round(mids[-1][0])} {round(mids[-1][1])}"
    for i in range(n):
        d += f"Q{round(moved[i][0])} {round(moved[i][1])} {round(mids[i][0])} {round(mids[i][1])}"
    return d + "Z"


def wash(x, y, w, h, rx=0):
    """Çizginin dışına hafif taşan, kenarları oynak suluboya lekesi."""
    x, y = x + 1.8, y + 1.4
    step = 15
    pts = []

    def edge(x1, y1, x2, y2):
        n = max(2, round(math.hypot(x2 - x1, y2 - y1) / step))
        for k in range(n):
            pts.append((x1 + (x2 - x1) * k / n, y1 + (y2 - y1) * k / n))

    def arc(cx, cy, a0, a1):
        n = max(3, round(abs(a1 - a0) * rx / step))
        for k in range(n):
            a = a0 + (a1 - a0) * k / n
            pts.append((cx + rx * math.cos(a), cy + rx * math.sin(a)))

    if rx:
        edge(x + rx, y, x + w - rx, y)
        arc(x + w - rx, y + rx, -math.pi / 2, math.pi / 2)
        edge(x + w - rx, y + h, x + rx, y + h)
        arc(x + rx, y + rx, math.pi / 2, 3 * math.pi / 2)
    else:
        edge(x, y, x + w, y)
        edge(x + w, y, x + w, y + h)
        edge(x + w, y + h, x, y + h)
        edge(x, y + h, x, y)
    return f'<path class="top" d="{blob(pts, 0.8, 1.7)}"/>'


def wash_round(cx, cy, r):
    n = 9
    pts = []
    for k in range(n):
        a = 2 * math.pi * (k + rnd.uniform(0.1, 0.6)) / n
        pts.append((cx + 1.8 + r * math.cos(a), cy + 1.4 + r * math.sin(a)))
    return f'<path class="top" d="{blob(pts, 1.2, 1.8)}"/>'


# ------------------------------------------------------------------ ortak stil
def base_css(ns):
    """Her animasyonda aynı olan kalem, renk ve giriş kuralları.

    ns: animasyonun kök sınıfı (ör. "m1284w"); kurallar onun altına yazılır
    ki sayfaya gömülen birden çok SVG birbirine karışmasın.
    """
    return f"""
.{ns}{{--ink:var(--gray-900,#1a1a1a);--ink2:var(--gray-600,#444);--ink3:var(--gray-400,#6b6b6b);--paper:var(--bg,#f8f8f8);--hot:var(--accent,#C56F34)}}
.{ns} .ink{{fill:none;stroke:var(--ink);stroke-width:1.7;stroke-linecap:round}}
.{ns} .ink.h{{stroke-width:1.2;opacity:.5}}
.{ns} .solid{{fill:var(--ink)}}
.{ns} .poche{{fill:var(--ink);fill-opacity:.1}}
.{ns} .fur{{fill:none;stroke:var(--ink2);stroke-width:1.4;stroke-linecap:round;stroke-linejoin:round}}
.{ns} .top{{fill:var(--hot);fill-opacity:.17;stroke:none}}
.{ns} .cover{{fill:var(--paper);stroke:none}}
.{ns} text{{font-family:var(--mono,'SF Mono','Fira Code',monospace);letter-spacing:0;font-variant-numeric:tabular-nums;user-select:none}}
.{ns} .draw{{stroke-dasharray:1 2;animation:{ns}-draw var(--t,.8s) cubic-bezier(.45,0,.2,1) var(--d,0s) backwards}}
.{ns} .pop{{transform-box:fill-box;transform-origin:50% 50%;animation:{ns}-pop var(--t,.35s) cubic-bezier(.3,1.5,.5,1) var(--d,0s) backwards}}
.{ns} .fade{{animation:{ns}-fade var(--t,.5s) ease var(--d,0s) backwards}}
@keyframes {ns}-draw{{from{{stroke-dashoffset:1.01}}}}
@keyframes {ns}-pop{{from{{transform:scale(0)}}}}
@keyframes {ns}-fade{{from{{opacity:0}}}}
""".strip()


def base_css_mobile(ns):
    """Dar ekranda çizim küçüldüğü için kalemi biraz kalınlaştırır (media sorgusunun içine konur)."""
    return (f".{ns} .ink{{stroke-width:2.2}}.{ns} .ink.h{{stroke-width:1.8}}"
            f".{ns} .fur{{stroke-width:2}}")


# ------------------------------------------------------------------ SVG parçaları
def draw_path(cls, d, delay, t=0.9):
    """Açılışta kendini çizen çizgi."""
    return f'<path class="{cls} draw" pathLength="1" d="{d}" style="--d:{pc(delay)}s;--t:{pc(t)}s"/>'


def text(x, y, tr, cls, en=None, extra=""):
    """Metin. İngilizce karşılığı verilirse js/motion.js İngilizce sayfada onu yazar."""
    data = f' data-en="{en}"' if en else ""
    return f'<text class="{cls}" x="{f(x)}" y="{f(y)}"{data}{extra}>{tr}</text>'


def svg_open(ns, w, h, par="xMidYMid meet"):
    return (f'<svg class="{ns}" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
            f'preserveAspectRatio="{par}" aria-hidden="true" focusable="false">')


def write(path, svg):
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(svg + "\n")
    print(f"{path}: {len(svg) / 1024:.1f} KB")
