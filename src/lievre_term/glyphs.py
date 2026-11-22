"""lievre 専用の字形（私用領域 U+E500–E509）。

どれも1セル（幅 CELL、下端 DESCENT から上端 ASCENT まで）に描き、線は隣のセルへつながる。

  U+E500–E503  カードの角。半径はセルの幅の 1/3
  U+E504–E505  カードの辺。角と同じ太さの線をセルの中心線に
  U+E506–E507  ボタンの両端。セルをボタンの色で塗り、外側の角を丸める
  U+E508–E509  フォーカスの括弧。キャップとの間をあけた細い括弧（outline-offset に当たる）

U+E500–U+E53F は Nerd Fonts 3.5.1 が使っていない隙間（U+E3E3 で終わり U+E5FA から再開）。
寸法は lievre の試作（spikes/tui/font/build.py、字幅 600・高さ 1300）を、幅 500・高さ 1200 に移したもの。
"""

import math
from dataclasses import dataclass

from fontTools.pens.ttGlyphPen import TTGlyphPen

from .config import ASCENT, BLEED, CELL, DESCENT, STROKE

CODEPOINTS = {
    0xE500: 'lievre.frame.topLeft',
    0xE501: 'lievre.frame.topRight',
    0xE502: 'lievre.frame.bottomLeft',
    0xE503: 'lievre.frame.bottomRight',
    0xE504: 'lievre.frame.horizontal',
    0xE505: 'lievre.frame.vertical',
    0xE506: 'lievre.button.capLeft',
    0xE507: 'lievre.button.capRight',
    0xE508: 'lievre.focus.left',
    0xE509: 'lievre.focus.right',
}

# 試作（幅 600・高さ 1300）からの縮尺。
KX = CELL / 600
KY = (ASCENT - DESCENT) / 1300


@dataclass(frozen=True)
class Cell:
    stroke: float = STROKE
    w: float = CELL
    top: float = ASCENT
    bottom: float = DESCENT
    bleed: float = BLEED

    @property
    def mid_x(self):
        return self.w / 2

    @property
    def mid_y(self):
        return (self.top + self.bottom) / 2

    @property
    def radius(self):
        return self.w / 3


def rect(pen, x0, y0, x1, y1):
    pen.moveTo((x0, y0))
    pen.lineTo((x0, y1))
    pen.lineTo((x1, y1))
    pen.lineTo((x1, y0))
    pen.closePath()


def arc_points(cx, cy, r, start, end):
    """start から end の角度までの 1/4 円を、2本の2次曲線で（1本では平たく見える）。"""
    a0, a1 = math.radians(start), math.radians(end)
    am = (a0 + a1) / 2
    ctrl = r / math.cos((a1 - a0) / 4)
    q1 = (cx + ctrl * math.cos((a0 + am) / 2), cy + ctrl * math.sin((a0 + am) / 2))
    mid = (cx + r * math.cos(am), cy + r * math.sin(am))
    q2 = (cx + ctrl * math.cos((am + a1) / 2), cy + ctrl * math.sin((am + a1) / 2))
    end_pt = (cx + r * math.cos(a1), cy + r * math.sin(a1))
    return [(q1, mid), (q2, end_pt)]


def reverse(path):
    """('line', pt) と ('q', ctrl, pt) の並びを逆向きにする。"""
    out = [('line', path[-1][-1])]
    for i in range(len(path) - 1, 0, -1):
        prev_pt = path[i - 1][-1]
        if path[i][0] == 'q':
            out.append(('q', path[i][1], prev_pt))
        else:
            out.append(('line', prev_pt))
    return out


def draw(pen, path):
    pen.moveTo(path[0][-1])
    for seg in path[1:]:
        if seg[0] == 'line':
            pen.lineTo(seg[1])
        else:
            pen.qCurveTo(seg[1], seg[2])
    pen.closePath()


def corner(pen, c: Cell, sx, sy):
    """左上の角を sx / sy で鏡映したもの。右端へ伸びる横線と下端へ伸びる縦線を、
    セルの中心線上の半径 c.radius の弧でつなぐ。"""
    h = c.stroke / 2
    ro, ri = c.radius + h, c.radius - h
    cx, cy = c.mid_x + c.radius, c.mid_y - c.radius

    def p(x, y):
        return (c.mid_x + (x - c.mid_x) * sx, c.mid_y + (y - c.mid_y) * sy)

    path = [('line', p(c.mid_x - h, c.bottom - c.bleed)), ('line', p(c.mid_x - h, cy))]
    path += [('q', p(*a), p(*b)) for a, b in arc_points(cx, cy, ro, 180, 90)]
    path += [
        ('line', p(c.w + c.bleed, c.mid_y + h)),
        ('line', p(c.w + c.bleed, c.mid_y - h)),
        ('line', p(cx, c.mid_y - h)),
    ]
    path += [('q', p(*a), p(*b)) for a, b in arc_points(cx, cy, ri, 90, 180)]
    path += [('line', p(c.mid_x + h, c.bottom - c.bleed))]
    # 1回だけ鏡映すると回り方が逆になる。TrueType の外側の輪郭は時計回り。
    if sx * sy < 0:
        path = reverse(path)
    draw(pen, path)


def cap(pen, c: Cell, left):
    """ボタンの端。セルを塗り、外側の角を丸める。"""
    r = 150 * KX
    x_out, x_in = (150 * KX, c.w + c.bleed) if left else (c.w - 150 * KX, -c.bleed)
    y0, y1 = c.bottom - c.bleed, c.top + c.bleed
    if left:
        path = [('line', (x_in, y0)), ('line', (x_out + r, y0))]
        path += [('q', a, b) for a, b in arc_points(x_out + r, y0 + r, r, 270, 180)]
        path += [('line', (x_out, y1 - r))]
        path += [('q', a, b) for a, b in arc_points(x_out + r, y1 - r, r, 180, 90)]
        path += [('line', (x_in, y1))]
        draw(pen, path)
    else:
        path = [('line', (x_in, y0)), ('line', (x_out - r, y0))]
        path += [('q', a, b) for a, b in arc_points(x_out - r, y0 + r, r, 270, 360)]
        path += [('line', (x_out, y1 - r))]
        path += [('q', a, b) for a, b in arc_points(x_out - r, y1 - r, r, 0, 90)]
        path += [('line', (x_in, y1))]
        draw(pen, reverse(path))


def bracket(pen, c: Cell, left):
    """フォーカスの括弧。キャップの手前に細い線を引き、両端はボタンの側へ曲がってセルの端で止まる。"""
    r = 50 * KX
    h = c.stroke / 2
    xc = c.w - r if left else r
    y0, y1 = c.bottom + 60 * KY, c.top - 60 * KY
    sign = 1 if left else -1
    cx_top, cy_top = xc + sign * r, y1 - r
    cx_bot, cy_bot = xc + sign * r, y0 + r
    end_x = c.w + c.bleed if left else -c.bleed
    if left:
        path = [('line', (end_x, y0 - h)), ('line', (cx_bot, y0 - h))]
        path += [('q', a, b) for a, b in arc_points(cx_bot, cy_bot, r + h, 270, 180)]
        path += [('line', (xc - h, cy_top))]
        path += [('q', a, b) for a, b in arc_points(cx_top, cy_top, r + h, 180, 90)]
        path += [('line', (end_x, y1 + h)), ('line', (end_x, y1 - h)), ('line', (cx_top, y1 - h))]
        path += [('q', a, b) for a, b in arc_points(cx_top, cy_top, r - h, 90, 180)]
        path += [('line', (xc + h, cy_bot))]
        path += [('q', a, b) for a, b in arc_points(cx_bot, cy_bot, r - h, 180, 270)]
        path += [('line', (end_x, y0 + h))]
        draw(pen, path)
    else:
        path = [('line', (end_x, y0 - h)), ('line', (cx_bot, y0 - h))]
        path += [('q', a, b) for a, b in arc_points(cx_bot, cy_bot, r + h, 270, 360)]
        path += [('line', (xc + h, cy_top))]
        path += [('q', a, b) for a, b in arc_points(cx_top, cy_top, r + h, 0, 90)]
        path += [('line', (end_x, y1 + h)), ('line', (end_x, y1 - h)), ('line', (cx_top, y1 - h))]
        path += [('q', a, b) for a, b in arc_points(cx_top, cy_top, r - h, 90, 0)]
        path += [('line', (xc - h, cy_bot))]
        path += [('q', a, b) for a, b in arc_points(cx_bot, cy_bot, r - h, 360, 270)]
        path += [('line', (end_x, y0 + h))]
        draw(pen, reverse(path))


def glyph(name):
    """名前の字形を TrueType の字形として返す。"""
    c = Cell()
    pen = TTGlyphPen(None)
    h = c.stroke / 2
    if name == 'lievre.frame.horizontal':
        rect(pen, -c.bleed, c.mid_y - h, c.w + c.bleed, c.mid_y + h)
    elif name == 'lievre.frame.vertical':
        rect(pen, c.mid_x - h, c.bottom - c.bleed, c.mid_x + h, c.top + c.bleed)
    elif name.startswith('lievre.frame.'):
        which = name.split('.')[-1]
        sx = 1 if 'Left' in which else -1
        sy = 1 if which.startswith('top') else -1
        corner(pen, c, sx, sy)
    elif name.startswith('lievre.button.'):
        cap(pen, c, name.endswith('Left'))
    else:
        bracket(pen, c, name.endswith('left'))
    return pen.glyph()
