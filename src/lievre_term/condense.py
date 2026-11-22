"""英数字を横だけ縮め、細くなる縦の線を太い字の x 座標で補う。

Plex Mono（字幅 600、英大文字の高さ 698）を、字幅 500・英大文字の高さ 733（Plex Sans JP と同じ）にすると、
横は 5/6、縦は 733/698 倍になる。そのまま縮めると縦の線だけが細くなるので、縦の線の位置（x 座標）と
横の線の位置（y 座標）を、Plex Mono の太さを変えられる版の別々の太さから取る。

  x 座標：縮めたあとの縦の線が、Plex Sans JP の同じ太さの縦の線の STROKE_RATIO 倍になる太さ
  y 座標：縮めたあとの横の線が、Plex Sans JP の同じ太さの横の線の STROKE_RATIO 倍になる太さ

同じ variable font の別の太さなので点の数と並びは同じで、点ごとに x と y を組み合わせられる。
"""

from functools import cache
from itertools import pairwise
from pathlib import Path

from fontTools.ttLib import TTFont
from fontTools.ttLib.tables import ttProgram
from fontTools.ttLib.tables._g_l_y_f import Glyph, GlyphCoordinates
from fontTools.varLib.instancer import instantiateVariableFont

from . import config as C

MEASURE_WEIGHTS = (100, 200, 300, 400, 500, 600, 700)


def stems(font: TTFont, name: str = 'H') -> tuple[int, int]:
    """'H' の縦の線の太さ（左の線）と横の線の太さ。"""
    glyf = font['glyf']
    coords = glyf[name].getCoordinates(glyf)[0]
    xs = sorted({round(x) for x, _ in coords})
    ys = sorted({round(y) for _, y in coords})
    return xs[1] - xs[0], ys[2] - ys[1]


@cache
def instance(path: Path, wght: float) -> TTFont:
    return instantiateVariableFont(TTFont(path), {'wght': wght})


@cache
def stem_tables(path: Path) -> tuple[dict, dict]:
    v, h = {}, {}
    for w in MEASURE_WEIGHTS:
        v[w], h[w] = stems(instance(path, w))
    return v, h


def weight_for(table: dict, stem: float) -> float:
    """太さごとの線の表を折れ線とみて、線の太さが stem になる wght。"""
    ws = sorted(table)
    for a, b in pairwise(ws):
        if stem <= table[b] or b == ws[-1]:
            w = a + (stem - table[a]) * (b - a) / (table[b] - table[a])
            break
    if not ws[0] <= w <= ws[-1]:
        raise ValueError(f'線の太さ {stem:.0f} は Plex Mono の太さの範囲（{ws[0]}〜{ws[-1]}）に収まらない')
    return w


def condensed(path: Path, css_weight: int) -> tuple[TTFont, float, float]:
    """縦と横を別の太さから取った Plex Mono（縮める前の寸法のまま）と、使った x・y の太さ。"""
    v_table, h_table = stem_tables(path)
    sans_v, sans_h = C.SANS_STEMS[css_weight]
    wx = weight_for(v_table, sans_v * C.STROKE_RATIO / C.LATIN_SX)
    wy = weight_for(h_table, sans_h * C.STROKE_RATIO / C.LATIN_SY)
    fx = instance(path, round(wx, 1))
    fy = instantiateVariableFont(TTFont(path), {'wght': round(wy, 1)})  # 書き換えるので別に作る
    gx, gy = fx['glyf'], fy['glyf']
    mixed = {}
    for name in fy.getGlyphOrder():
        cy, ends, flags = gy[name].getCoordinates(gy)
        cx, ends_x, _ = gx[name].getCoordinates(gx)
        g = Glyph()
        if len(cy) == 0:
            g.numberOfContours = 0
        else:
            assert list(ends) == list(ends_x), f'{name} の点の並びが太さで違う'
            g.coordinates = GlyphCoordinates([(x, y) for (x, _), (_, y) in zip(cx, cy)])
            g.endPtsOfContours = list(ends)
            g.flags = bytearray(f & 1 for f in flags)
            g.numberOfContours = len(ends)
            g.program = ttProgram.Program()
            g.program.fromBytecode(b'')
        mixed[name] = g
    for name, g in mixed.items():
        gy[name] = g
    return fy, wx, wy
