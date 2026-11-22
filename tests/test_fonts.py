"""書き出したフォントの幅と寸法を確かめる。

LIEVRE_TERM_FONTS に、ビルドの出力（ttf/・web/・widths.json のある場所。nix build の result/share/lievre-term）を渡す。
LIEVRE_TERM_UCD を渡すと、widths.json が Unicode のデータから作り直したものと同じかも確かめる。
"""

import json
import os
import re
from functools import cache
from pathlib import Path

import pytest
from fontTools.ttLib import TTFont

from lievre_term import condense, jis, web
from lievre_term import config as C
from lievre_term import glyphs as G
from lievre_term import widths as W

OUT = Path(os.environ.get('LIEVRE_TERM_FONTS', 'result/share/lievre-term'))
CASES = [(v, w) for v in C.VARIANTS.values() for w in C.WEIGHTS.values()]
IDS = [f'{v.id}-{w.css}' for v, w in CASES]

if not (OUT / 'ttf').is_dir():
    pytest.skip(f'{OUT}/ttf がありません（先に nix build する）', allow_module_level=True)


@cache
def font(variant: C.Variant, weight: C.Weight) -> TTFont:
    return TTFont(OUT / 'ttf' / f'{variant.file_stem}-{weight.style}.ttf')


@cache
def table() -> bytearray:
    return W.from_json(json.loads((OUT / 'widths.json').read_text()))


def advance(f: TTFont, cp: int) -> int:
    return f['hmtx'][f.getBestCmap()[cp]][0]


def bounds(f: TTFont, cp: int):
    g = f['glyf'][f.getBestCmap()[cp]]
    g.recalcBounds(f['glyf'])
    return g.xMin, g.yMin, g.xMax, g.yMax


@pytest.mark.parametrize(('variant', 'weight'), CASES, ids=IDS)
def test_every_advance_matches_width_table(variant, weight):
    f = font(variant, weight)
    w = table()
    wrong = [
        f'U+{cp:04X} は {f["hmtx"][g][0]}（表では {w[cp]} セル）'
        for cp, g in f.getBestCmap().items()
        if f['hmtx'][g][0] != w[cp] * C.CELL
    ]
    assert not wrong, '\n'.join(wrong[:20])


@pytest.mark.parametrize(('variant', 'weight'), CASES, ids=IDS)
def test_latin_is_half_of_japanese(variant, weight):
    f = font(variant, weight)
    for ch in 'Aa0@~ ':
        assert advance(f, ord(ch)) == C.UPM // 2
    if variant.cjk:
        for ch in 'あア日本語漢、。　':
            assert advance(f, ord(ch)) == C.UPM
        assert advance(f, ord('ｱ')) == C.UPM // 2  # 半角カナ


@pytest.mark.parametrize(('variant', 'weight'), CASES, ids=IDS)
def test_metrics_are_the_cell(variant, weight):
    f = font(variant, weight)
    assert (f['hhea'].ascent, f['hhea'].descent, f['hhea'].lineGap) == (C.ASCENT, C.DESCENT, 0)
    os2 = f['OS/2']
    assert (os2.sTypoAscender, os2.sTypoDescender, os2.sTypoLineGap) == (C.ASCENT, C.DESCENT, 0)
    assert os2.fsSelection & (1 << 7), 'USE_TYPO_METRICS'
    assert os2.usWeightClass == weight.css
    assert f['post'].isFixedPitch == 1
    assert f['head'].unitsPerEm == C.UPM


@pytest.mark.parametrize(('variant', 'weight'), CASES, ids=IDS)
def test_lievre_glyphs_fill_the_cell(variant, weight):
    f = font(variant, weight)
    lo, hi = C.DESCENT, C.ASCENT
    b = C.BLEED
    for cp in G.CODEPOINTS:
        assert advance(f, cp) == C.CELL
        x0, y0, x1, y1 = bounds(f, cp)
        assert x0 >= -b and x1 <= C.CELL + b and y0 >= lo - b and y1 <= hi + b, f'U+{cp:04X} がセルの外へ出ている'

    def reach(cp, left=False, right=False, bottom=False, top=False):
        x0, y0, x1, y1 = bounds(f, cp)
        for flag, ok in ((left, x0 <= 0), (right, x1 >= C.CELL), (bottom, y0 <= lo), (top, y1 >= hi)):
            if flag:
                assert ok, f'U+{cp:04X} がセルの端に届いていない: {(x0, y0, x1, y1)}'

    reach(0xE500, right=True, bottom=True)  # 左上の角
    reach(0xE501, left=True, bottom=True)
    reach(0xE502, right=True, top=True)
    reach(0xE503, left=True, top=True)
    reach(0xE504, left=True, right=True)  # 横の辺
    reach(0xE505, bottom=True, top=True)  # 縦の辺
    reach(0xE506, right=True, bottom=True, top=True)  # ボタンの左端
    reach(0xE507, left=True, bottom=True, top=True)
    reach(0xE508, right=True)  # フォーカスの括弧
    reach(0xE509, left=True)


@pytest.mark.parametrize(('variant', 'weight'), CASES, ids=IDS)
def test_box_drawing_connects(variant, weight):
    f = font(variant, weight)
    x0, _, x1, _ = bounds(f, 0x2500)
    assert x0 <= 0 and x1 >= C.CELL
    _, y0, _, y1 = bounds(f, 0x2502)
    assert y0 <= C.DESCENT and y1 >= C.ASCENT
    assert bounds(f, 0x2588) == (0, C.DESCENT, C.CELL, C.ASCENT)
    # 網はセルの左下の角から升目を刻み、セルの外へ出ない（隣のセルと模様がつながる）。
    # 中と濃はセルの端から端まで届く。
    for cp in G.SHADES:
        x0, y0, x1, y1 = bounds(f, cp)
        assert (x0, y0) == (0, C.DESCENT) and x1 <= C.CELL and y1 <= C.ASCENT, f'U+{cp:04X}'
    for cp in (0x2592, 0x2593):
        assert bounds(f, cp) == (0, C.DESCENT, C.CELL, C.ASCENT), f'U+{cp:04X}'


@pytest.mark.parametrize(
    ('variant', 'weight'), [c for c in CASES if c[0].cjk], ids=[i for c, i in zip(CASES, IDS) if c[0].cjk]
)
def test_kanji_sit_on_the_cell_center(variant, weight):
    f = font(variant, weight)
    centers = []
    for ch in '永国東語漢字日本田中十':
        _, y0, _, y1 = bounds(f, ord(ch))
        centers.append((y0 + y1) / 2)
    mean = sum(centers) / len(centers)
    assert abs(mean - C.CELL_CENTER) <= 12, f'漢字の中心 {mean:.1f}、セルの中心 {C.CELL_CENTER}'


@pytest.mark.parametrize(('variant', 'weight'), CASES, ids=IDS)
def test_coverage_follows_the_variant(variant, weight):
    cmap = font(variant, weight).getBestCmap()
    kanji = {cp for cp in cmap if jis.is_ideograph(cp)}
    if variant.cjk is None:
        assert not kanji and ord('あ') not in cmap
    elif variant.cjk == 'jp1':
        assert kanji <= jis.level1() and len(kanji) == len(jis.level1()) == 2965
        assert ord('亜') in cmap and ord('弌') not in cmap  # 第1水準の最初と第2水準の最初
    else:
        assert ord('弌') in cmap and len(kanji) > 10000
    nerd = {0xE0B0, 0xE0A0, 0xF015, 0xF0001}
    assert (nerd <= set(cmap)) if variant.nerd else not (nerd & set(cmap))
    # lievre の私用領域には lievre の字形しかない。
    assert {cp for cp in cmap if 0xE500 <= cp <= 0xE53F} == set(G.CODEPOINTS)


@pytest.mark.parametrize(('variant', 'weight'), CASES, ids=IDS)
def test_names_avoid_reserved_font_names(variant, weight):
    f = font(variant, weight)
    for record in f['name'].names:
        if record.nameID in (1, 3, 4, 6, 16):
            text = record.toUnicode()
            assert 'Plex' not in text and 'Pomicons' not in text, text
    assert f['name'].getDebugName(16) == variant.family
    assert f['name'].getDebugName(17) == weight.style


def test_width_table_samples():
    w = table()
    # 見えない字や私用領域の字を生で書くと整形で読めなくなるので、符号位置で書く。
    samples = {
        ord('A'): 1, 0x25CB: 1, 0x00D7: 1, 0x2212: 1, 0x2191: 1, 0x2193: 1,  # A ○ × − ↑ ↓
        0x2500: 1, 0x2502: 1, 0x256D: 1, 0x2026: 1,  # ─ │ ╭ …
        0x30FB: 2, 0x3042: 2, 0x6F22: 2, 0x3000: 2, 0xFF71: 1,  # ・ あ 漢 全角空白 半角ｱ
        0x0301: 0, 0x200B: 0, 0xE500: 1, 0xF0001: 1, 0x26A1: 2,  # 結合文字 ゼロ幅空白 lievre Nerd ⚡
    }  # fmt: skip
    wrong = {f'U+{cp:04X}': w[cp] for cp, n in samples.items() if w[cp] != n}
    assert not wrong


@pytest.mark.skipif('LIEVRE_TERM_UCD' not in os.environ, reason='LIEVRE_TERM_UCD がない')
def test_width_table_is_built_from_ucd():
    assert W.compute(Path(os.environ['LIEVRE_TERM_UCD'])) == table()


def font_faces(css: str):
    """CSS の @font-face を {'font-family': ..., ...} の並びで返す。"""
    faces = []
    for block in re.findall(r'@font-face \{(.*?)\}', css, re.DOTALL):
        decl = {}
        for line in block.strip().splitlines():
            key, _, value = line.strip().rstrip(';').partition(':')
            decl[key.strip()] = value.strip()
        faces.append(decl)
    return faces


@pytest.mark.parametrize('variant', list(C.VARIANTS.values()), ids=list(C.VARIANTS))
def test_web_css_covers_the_font(variant):
    css = (OUT / 'web' / f'{variant.id}.css').read_text()
    faces = font_faces(css)
    assert {f['font-family'] for f in faces} == {f"'{variant.family}'"}
    for weight in C.WEIGHTS.values():
        mine = [f for f in faces if f['font-weight'] == str(weight.css)]
        assert mine, f'{weight.css} の @font-face がない'
        ttf = font(variant, weight)
        cmap = ttf.getBestCmap()
        seen = set()
        for face in mine:
            assert face['font-display'] == 'swap' and face['font-style'] == 'normal'
            ranges = web.parse_unicode_range(face['unicode-range'])
            assert not (ranges & seen), 'unicode-range が重なっている'
            seen |= ranges
            path = OUT / 'web' / re.fullmatch(r"url\('(.+)'\) format\('woff2'\)", face['src'])[1]
            part = TTFont(path)
            assert part.flavor == 'woff2'
            assert set(part.getBestCmap()) == ranges, f'{path.name} の字が unicode-range と違う'
            assert (part['hhea'].ascent, part['hhea'].descent) == (C.ASCENT, C.DESCENT)
            for cp, g in part.getBestCmap().items():
                assert part['hmtx'][g][0] == ttf['hmtx'][cmap[cp]][0]
        assert seen == set(cmap), 'unicode-range を合わせてもフォントの字にならない'


def test_line_center_is_the_ideographic_center():
    # 表意文字の字面の枠（Plex Sans JP の BASE、-120〜880）の中央を、行の箱の中央に置く。Web の 'Lievre Sans' と同じ。
    assert (C.ASCENT + C.DESCENT) / 2 == C.CELL_CENTER == (-120 + 880) / 2


@pytest.mark.parametrize(('variant', 'weight'), CASES, ids=IDS)
def test_latin_matches_the_body_text(variant, weight):
    # 英大文字の高さは本文（Plex Sans JP）と同じ 733、ベースラインは動かさない。
    f = font(variant, weight)
    _, y0, _, y1 = bounds(f, ord('H'))
    assert (y0, y1) == (0, C.LATIN_CAP)
    # 英大文字の中央は、本文と同じく行の中央の少し下（0.38 − 0.733 / 2 ≒ 0.013em）。
    assert abs((y0 + y1) / 2 - C.CELL_CENTER) <= 15


@pytest.mark.parametrize(('variant', 'weight'), CASES, ids=IDS)
def test_latin_strokes_follow_the_body_text(variant, weight):
    # 縦の線も横の線も、本文の同じ太さの線の STROKE_RATIO 倍（丸めの分だけ許す）。
    v, h = condense.stems(font(variant, weight), font(variant, weight).getBestCmap()[ord('H')])
    sans_v, sans_h = C.SANS_STEMS[weight.css]
    assert abs(v - sans_v * C.STROKE_RATIO) <= 2, f'縦の線 {v}'
    assert abs(h - sans_h * C.STROKE_RATIO) <= 2, f'横の線 {h}'
