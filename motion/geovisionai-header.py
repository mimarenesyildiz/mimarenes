# -*- coding: utf-8 -*-
"""GeoVisionAI başlık animasyonunun üreteci.

Taranmış oda (solda) altı yüzeyine açılır; her yüzey bir görünüş olur
(ortada). Tarama çizgisi geçerken pencere ve kapılar maskelenir, sonra
yüzeyler temiz çizgili bir NURBS model olarak yeniden kapanır (sağda).

Örnek oda sayfadaki şekillerle aynıdır: doğu ve güney duvarında birer
pencere, kuzey duvarında bir kapı; batı duvarında yalnızca bir tablo vardır
ve yapı elemanı olmadığı için maskelenmez. Tavan ve tabanda eleman yoktur.

Geniş ekranda üç durak yan yana durur; dar ekranda üçü de ortada, aynı
yerde gerçekleşir (--xl ve --xr sıfırlanır).

Kullanım:  python motion/geovisionai-header.py     -> motion/geovisionai-header.svg
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit                                           # noqa: E402
from kit import f, pc, rect_sk, blob                 # noqa: E402

kit.seed(3501)
NS = "mgv"

# ------------------------------------------------------------------ geometri
W, H = 1200, 420
CX, CY = 600, 210          # ortadaki durağın merkezi
L = 120                    # odanın kenarı (küp) ve bir görünüşün kenarı
GAP = 16                   # görünüşler arası boşluk
STAGE = 410                # sol ve sağ durağın ortadan uzaklığı
C30, S30 = 0.866, 0.5

# yüzeyler: ad -> izometrik matris (a, b, c, d, e, f); (u, v) yüzeyin kendi düzlemi
ISO = {
    "floor": (C30, S30, -C30, S30, CX, CY),
    "N": (C30, S30, 0, 1, CX, CY - L),               # arka sağ duvar
    "W": (-C30, S30, 0, 1, CX, CY - L),              # arka sol duvar
    "S": (C30, S30, 0, 1, CX - C30 * L, CY - S30 * L),   # ön sol duvar
    "E": (C30, -S30, 0, 1, CX, CY),                  # ön sağ duvar
    "ceil": (C30, S30, -C30, S30, CX, CY - L),
}
ORDER = ["floor", "N", "W", "S", "E", "ceil"]        # arkadan öne çizim sırası
FRONT = ("S", "E", "ceil")                           # kutuda dışarıdan görünen yüzeyler

# görünüş ızgarası (3 x 2): üstte kuzey, doğu, tavan; altta güney, batı, taban
GRID = {"N": (0, 0), "E": (1, 0), "ceil": (2, 0), "S": (0, 1), "W": (1, 1), "floor": (2, 1)}
GX0 = CX - (3 * L + 2 * GAP) / 2
GY0 = CY - (2 * L + GAP) / 2

# yapı elemanları: yüzey -> (tür, x, y, en, boy), yüzeyin kendi düzleminde
PARTS = {
    "E": ("window", 28, 30, 64, 46),
    "S": ("window", 24, 32, 72, 44),
    "N": ("door", 72, 40, 30, 78),
}
PICTURE = ("W", 38, 40, 44, 26)                      # tablo: yapı elemanı değil, maskelenmez

# ------------------------------------------------------------------ zamanlama (sn)
T = 13.0
D0 = 1.5
T_OPEN0, T_OPEN1 = 0.9, 2.3          # kutu görünüşlere açılır
T_SCAN0, T_SCAN1 = 2.7, 4.2          # tarama çizgisi ızgarayı geçer
T_FOLD0, T_FOLD1 = 5.3, 6.7          # görünüşler modele kapanır
T_DIP0, T_DIP1, T_RESET, T_UP0, T_UP1 = 11.3, 11.7, 11.9, 12.1, 12.5
EASE = "cubic-bezier(.65,0,.25,1)"


def p(t):
    return pc(t / T * 100)


R0, R1 = p(T_RESET - 0.01), p(T_RESET)


def tile_xy(name):
    col, row = GRID[name]
    return GX0 + col * (L + GAP), GY0 + row * (L + GAP)


def mat(m):
    return "matrix(" + ",".join(pc(v) for v in m) + ")"


# ------------------------------------------------------------------ yüzey
def face(name):
    o = [f'<g class="face f{name}">']
    o.append(f'<rect class="bg" width="{L}" height="{L}"/>')
    o.append(f'<rect class="tex raw" width="{L}" height="{L}" fill="url(#{NS}-dots)"/>')
    if name in PARTS:
        kind, x, y, w, h = PARTS[name]
        col = "ab"[GRID[name][0]]                     # maskenin belirdiği sütun
        # taramada görünen ham çizgi
        d = rect_sk(x, y, w, h, 0.35, 1.4)
        if kind == "window":
            d += f"M{f(x + w / 2)} {y}V{y + h}"
        else:
            d += f"M{f(x + w - 6)} {f(y + h / 2)}h.1"
        o.append(f'<path class="obj raw" d="{d}"/>')
        # maske: kenarı oynak leke + sınırlayıcı kutu
        pts = []
        for k in range(14):
            t = k / 14
            if t < 0.25:
                pts.append((x + w * t * 4, y))
            elif t < 0.5:
                pts.append((x + w, y + h * (t - 0.25) * 4))
            elif t < 0.75:
                pts.append((x + w - w * (t - 0.5) * 4, y + h))
            else:
                pts.append((x, y + h - h * (t - 0.75) * 4))
        o.append(f'<path class="mask m{col}" d="{blob(pts, 1.2, 2.2)}"/>')
        o.append(f'<rect class="bbox m{col}" x="{x - 6}" y="{y - 6}" width="{w + 12}" height="{h + 12}"/>')
        # NURBS eğrisi: keskin dikdörtgen
        o.append(f'<rect class="crv" x="{x}" y="{y}" width="{w}" height="{h}"/>')
    if name == PICTURE[0]:
        _, x, y, w, h = PICTURE
        o.append(f'<path class="obj raw" d="{rect_sk(x, y, w, h, 0.35, 1.2)}"/>')
    o.append(f'<path class="frame" d="{rect_sk(0, 0, L, L, 0.4, 2.0)}"/>')
    o.append("</g>")
    return o


def ghost_box(dx):
    """Kutunun silueti: altıgen ve üç iç kenar."""
    pts = [(0, -L), (C30 * L, -S30 * L), (C30 * L, S30 * L), (0, L), (-C30 * L, S30 * L), (-C30 * L, -S30 * L)]
    d = "M" + "L".join(f"{f(CX + dx + x)} {f(CY + y)}" for x, y in pts) + "Z"
    d += f"M{f(CX + dx)} {CY}L{f(CX + dx)} {CY + L}M{f(CX + dx)} {CY}L{f(CX + dx + C30 * L)} {f(CY - S30 * L)}"
    d += f"M{f(CX + dx)} {CY}L{f(CX + dx - C30 * L)} {f(CY - S30 * L)}"
    return f'<path class="ghost side" d="{d}"/>'


# ------------------------------------------------------------------ stil
def kf(name, *rows):
    return f"@keyframes {NS}-{name}{{{''.join(rows)}}}"


def keyframes():
    out = []
    for name in ORDER:
        iso = mat(ISO[name])
        tx, ty = tile_xy(name)
        flat = mat((1, 0, 0, 1, tx, ty))
        out.append(kf(f"f{name}",
                      f"0%,{p(T_OPEN0)}%{{transform:translate(var(--xl),0px) {iso};animation-timing-function:{EASE}}}",
                      f"{p(T_OPEN1)}%,{p(T_FOLD0)}%{{transform:translate(0px,0px) {flat};animation-timing-function:{EASE}}}",
                      f"{p(T_FOLD1)}%,{R0}%{{transform:translate(var(--xr),0px) {iso}}}",
                      f"{R1}%,100%{{transform:translate(var(--xl),0px) {iso}}}"))
    # ham tarama (doku ve ham çizgiler) modelde kaybolur
    out.append(kf("raw", f"0%,{p(T_FOLD0)}%{{opacity:1}}", f"{p(T_FOLD0 + 0.9)}%,{R0}%{{opacity:0}}", f"{R1}%,100%{{opacity:1}}"))
    # maske ve sınırlayıcı kutu: tarama çizgisi sütuna gelince belirir, modelde kaybolur
    for col, t in (("a", T_SCAN0 + (T_SCAN1 - T_SCAN0) / 6), ("b", T_SCAN0 + (T_SCAN1 - T_SCAN0) / 2)):
        out.append(kf(f"m{col}", f"0%,{p(t)}%{{opacity:0}}", f"{p(t + 0.25)}%,{p(T_FOLD0)}%{{opacity:1}}",
                      f"{p(T_FOLD0 + 0.7)}%,100%{{opacity:0}}"))
    # NURBS eğrisi: kapanırken belirir
    out.append(kf("crv", f"0%,{p(T_FOLD0 + 0.3)}%{{opacity:0}}", f"{p(T_FOLD0 + 1.0)}%,{R0}%{{opacity:1}}", f"{R1}%,100%{{opacity:0}}"))
    # tarama çizgisi
    span = 3 * L + 2 * GAP + 16
    out.append(kf("scan", f"0%,{p(T_SCAN0 - 0.15)}%{{opacity:0;transform:translateX(0px)}}",
                  f"{p(T_SCAN0)}%{{opacity:1;transform:translateX(0px)}}",
                  f"{p(T_SCAN1)}%{{opacity:1;transform:translateX({pc(span)}px)}}",
                  f"{p(T_SCAN1 + 0.2)}%,100%{{opacity:0;transform:translateX({pc(span)}px)}}"))
    out.append(kf("dip", f"0%,{p(T_DIP0)}%{{opacity:1}}", f"{p(T_DIP1)}%,{p(T_UP0)}%{{opacity:0}}", f"{p(T_UP1)}%,100%{{opacity:1}}"))
    return "\n".join(out)


def css():
    loop = "var(--T) linear var(--d0) infinite backwards"
    faces = ""
    for k, name in enumerate(ORDER):
        delay = 0.35 + (0.15 * FRONT.index(name) if name in FRONT else 0)
        faces += (f".{NS} .f{name}{{transform:translate(0px,0px) {mat(ISO[name])};"
                  f"animation:{NS}-fade .5s ease {pc(delay)}s backwards,{NS}-f{name} {loop}}}")
    return f"""
{kit.base_css(NS)}
.{NS}{{--T:{T}s;--d0:{D0}s;--xl:-{STAGE}px;--xr:{STAGE}px}}
.{NS} .bg{{fill:var(--paper)}}
.{NS} .frame{{fill:none;stroke:var(--ink);stroke-width:1.7;stroke-linecap:round}}
.{NS} .tex{{fill-opacity:.55}}
.{NS} .obj{{fill:none;stroke:var(--ink2);stroke-width:1.3;stroke-linecap:round;stroke-linejoin:round}}
.{NS} .mask{{fill:var(--hot);fill-opacity:.42}}
.{NS} .bbox{{fill:none;stroke:var(--hot);stroke-width:1.2;stroke-dasharray:4 3}}
.{NS} .crv{{fill:var(--hot);fill-opacity:.2;stroke:var(--hot);stroke-width:2}}
.{NS} .ghost{{fill:none;stroke:var(--ink3);stroke-width:1.1;stroke-dasharray:1.5 5;stroke-linecap:round;opacity:.7}}
.{NS} .arrow{{fill:none;stroke:var(--ink3);stroke-width:1.4;stroke-linecap:round;stroke-linejoin:round}}
.{NS} .scan{{stroke:var(--hot);stroke-width:2;stroke-linecap:round;opacity:0;animation:{NS}-scan {loop}}}
.{NS} .dots{{fill:var(--ink3)}}
.{NS} .dyn{{animation:{NS}-dip {loop}}}
.{NS} .raw{{opacity:0;animation:{NS}-raw {loop}}}
.{NS} .ma{{opacity:0;animation:{NS}-ma {loop}}}
.{NS} .mb{{opacity:0;animation:{NS}-mb {loop}}}
.{NS} .crv{{animation:{NS}-crv {loop}}}
{faces}
{keyframes()}
@media (max-width:768px){{.{NS}{{--xl:0px;--xr:0px}}.{NS} .ghost,.{NS} .arrow{{display:none}}.{NS} .frame{{stroke-width:2.2}}.{NS} .obj{{stroke-width:1.9}}.{NS} .bbox{{stroke-width:1.8}}.{NS} .crv{{stroke-width:2.8}}.{NS} .scan{{stroke-width:3}}}}
""".strip()


# ------------------------------------------------------------------ çizim
def build():
    o = [kit.svg_open(NS, W, H, "xMidYMid slice"), f"<style>{css()}</style>"]
    o.append(f'<defs><pattern id="{NS}-dots" width="8" height="8" patternUnits="userSpaceOnUse">'
             f'<circle class="dots" cx="2" cy="2" r=".9"/><circle class="dots" cx="6" cy="6" r=".9"/></pattern></defs>')

    # duraklar: solda tarama, ortada altı görünüş, sağda model
    o.append('<g class="fade" style="--d:.1s">')
    o.append(ghost_box(-STAGE))
    o.append(ghost_box(STAGE))
    for name in ORDER:
        tx, ty = tile_xy(name)
        o.append(f'<rect class="ghost" x="{f(tx)}" y="{f(ty)}" width="{L}" height="{L}"/>')
    for x in (CX - STAGE + C30 * L + 26, CX + (3 * L + 2 * GAP) / 2 + 22):
        o.append(f'<path class="arrow" d="M{f(x)} {CY}h34m-8 -7l8 7l-8 7"/>')
    o.append("</g>")

    o.append('<g class="dyn">')
    for name in ORDER:
        o += face(name)
    o.append(f'<path class="scan" d="M{f(GX0 - 8)} {f(GY0 - 12)}V{f(GY0 + 2 * L + GAP + 12)}"/>')
    o.append("</g></svg>")
    return "\n".join(o)


if __name__ == "__main__":
    for name, (_, x, y, w, h) in PARTS.items():
        assert 0 < x and x + w < L and 0 < y and y + h <= L, name    # eleman yüzeyin içinde
    assert PICTURE[0] not in PARTS                                   # tablo maskelenmez
    here = os.path.dirname(os.path.abspath(__file__))
    kit.write(sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, "geovisionai-header.svg"), build())
