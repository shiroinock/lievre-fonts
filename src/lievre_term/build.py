"""Lievre Term を組み立てる。

  lievre-term-build fonts  --sources DIR --ucd DIR --out DIR [--variant ID ...] [--weight 400 ...]
  lievre-term-build widths --ucd DIR --out widths.json

字形は次の順に取る（先に取ったものが勝つ）。

  1. lievre 専用の字形（U+E500–E509）
  2. IBM Plex Mono。横だけ縮めて線を補ったもの（condense.py）を、幅 500・英大文字の高さ 733 にする。
     罫線とブロック（U+2500–259F）は静的な Plex Mono から取り、縦もセルに合わせる
  3. IBM Plex Sans JP（JP1・JP のとき）。JP_SHIFT だけ縦に動かす（既定は 0）。幅の表で 1 の字は半角に収める
  4. Symbols Nerd Font Mono（NF のとき）。Powerline の区切りはセルいっぱいに引き伸ばす

どの字も、送り幅は幅の表（widths.py）のセルの数 × 500 にする。
"""

import argparse
import os
import sys
from pathlib import Path

from fontTools.fontBuilder import FontBuilder
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont, newTable
from fontTools.ttLib.woff2 import compress

from . import condense, jis, web
from . import config as C
from . import glyphs as G
from . import widths as W

HEIGHT = C.ASCENT - C.DESCENT
JP_MARGIN = 20  # 全角の字を半角に収めるときに左右に残す余白
PUA = (0xE000, 0xF8FF)


class Source:
    def __init__(self, path: Path | TTFont, key: str):
        self.key = key
        self.font = path if isinstance(path, TTFont) else TTFont(path)
        self.cmap = self.font.getBestCmap()
        self.glyph_set = self.font.getGlyphSet()
        self.hmtx = self.font['hmtx']

    def advance(self, name):
        return self.hmtx[name][0]

    def bounds(self, name):
        pen = BoundsPen(self.glyph_set)
        self.glyph_set[name].draw(pen)
        return pen.bounds

    def outline(self, name, transform):
        rec = DecomposingRecordingPen(self.glyph_set)
        self.glyph_set[name].draw(rec)
        pen = TTGlyphPen(None)
        rec.replay(TransformPen(pen, transform))
        return pen.glyph()


def scale_about(s, cx_from, cy_from, cx_to, cy_to):
    """(cx_from, cy_from) を (cx_to, cy_to) に移し、そのまわりを s 倍する変換。"""
    return (s, 0, 0, s, cx_to - cx_from * s, cy_to - cy_from * s)


def place_box(src: Source, cp, name, w):
    """罫線とブロック。横は 5/6、縦はセルの高さいっぱいに。"""
    if not 0x2500 <= cp <= 0x259F:
        return None
    s = C.LATIN_SCALE
    target = w * C.CELL
    dx = (target - src.advance(name) * s) / 2
    sy = HEIGHT / (C.MONO_BOX_TOP - C.MONO_BOX_BOTTOM)
    return (s, 0, 0, sy, dx, C.DESCENT - C.MONO_BOX_BOTTOM * sy), target


def place_mono(src: Source, cp, name, w):
    """英数字。横は 5/6、縦は 733/698（線の太さは condense.py で補ってある）。"""
    adv = src.advance(name)
    sx, sy = C.LATIN_SX, C.LATIN_SY
    if adv == 0:
        # 結合文字など。幅の表でも 0 のときだけ残す（U+2028 などは表では 1 なので落とす）。
        return ((sx, 0, 0, sy, 0, 0), 0) if w == 0 else None
    if w == 0:
        return (sx, 0, 0, sy, -adv * sx, 0), 0
    target = w * C.CELL
    return (sx, 0, 0, sy, (target - adv * sx) / 2, 0), target


def place_jp(src: Source, cp, name, w):
    adv = src.advance(name)
    if w == 0:
        return (1, 0, 0, 1, -adv, C.JP_SHIFT), 0
    target = w * C.CELL
    box = src.bounds(name)
    if adv == target or box is None:
        return (1, 0, 0, 1, (target - adv) / 2, C.JP_SHIFT), target
    xmin, _, xmax, _ = box
    avail = target - 2 * JP_MARGIN
    s = min(1.0, avail / (xmax - xmin)) if xmax > xmin else 1.0
    # 字面の中心をセルの中心に置き、そのまわりで縮める（○ などの形を保つため縦横同じ比率）。
    return scale_about(s, (xmin + xmax) / 2, C.CELL_CENTER - C.JP_SHIFT, target / 2, C.CELL_CENTER), target


def place_nf(src: Source, cp, name, w):
    target = max(w, 1) * C.CELL
    if cp in C.POWERLINE_SEPARATORS:
        xmin, _, xmax, _ = src.bounds(name)
        sx = (target + 2 * C.BLEED) / (xmax - xmin)
        sy = HEIGHT / (C.NF_TOP - C.NF_BOTTOM)
        return (sx, 0, 0, sy, -C.BLEED - xmin * sx, C.DESCENT - C.NF_BOTTOM * sy), target
    s = target / C.NF_UPM
    adv = src.advance(name)
    return scale_about(s, adv / 2, (C.NF_TOP + C.NF_BOTTOM) / 2, target / 2, C.CELL_CENTER), target


def wanted_jp(variant: C.Variant, cp):
    if PUA[0] <= cp <= PUA[1] or cp >= 0xF0000:
        return False
    if variant.cjk == 'jp1' and jis.is_ideograph(cp):
        return cp in jis.level1()
    return True


def source_epoch():
    return int(os.environ.get('SOURCE_DATE_EPOCH', '1767225600'))  # 2026-01-01


def build_font(variant: C.Variant, weight: C.Weight, sources: Path, width: bytearray) -> TTFont:
    mono = Source(sources / f'mono/IBMPlexMono-{weight.mono}.ttf', 'mono')
    latin_font, wx, wy = condense.condensed(sources / 'mono-var/IBMPlexMonoVar-Roman.ttf', weight.css)
    latin = Source(latin_font, f'latin-{weight.css}')
    order = ['.notdef']
    glyf = {}
    hmtx = {}
    cmap = {}
    cache = {}

    def add(src_key, src_name, transform, adv, make):
        key = (src_key, src_name, tuple(round(v, 4) for v in transform), adv)
        if key not in cache:
            gname = f'g{len(order)}'
            order.append(gname)
            glyf[gname] = make()
            hmtx[gname] = adv
            cache[key] = gname
        return cache[key]

    # .notdef は Plex Mono のものを縮めて使う。
    glyf['.notdef'] = latin.outline('.notdef', (C.LATIN_SX, 0, 0, C.LATIN_SY, 0, 0))
    hmtx['.notdef'] = C.CELL

    for cp, name in G.CODEPOINTS.items():
        gname = add('lievre', name, (1, 0, 0, 1, 0, 0), C.CELL, lambda n=name: G.glyph(n))
        cmap[cp] = gname

    layers = [
        (mono, place_box, lambda cp: True),
        (latin, place_mono, lambda cp: not (PUA[0] <= cp <= PUA[1])),
    ]
    if variant.cjk:
        jp = Source(sources / f'jp/IBMPlexSansJP-{weight.jp}.ttf', 'jp')
        layers.append((jp, place_jp, lambda cp: wanted_jp(variant, cp)))
    if variant.nerd:
        nf = Source(sources / 'nf/SymbolsNerdFontMono-Regular.ttf', 'nf')
        layers.append((nf, place_nf, lambda cp: True))

    for src, place, wanted in layers:
        for cp, name in sorted(src.cmap.items()):
            if cp in cmap or cp < 0x20 or 0x7F <= cp < 0xA0 or not wanted(cp):
                continue
            placed = place(src, cp, name, width[cp])
            if placed is None:
                continue
            transform, adv = placed
            cmap[cp] = add(src.key, name, transform, adv, lambda s=src, n=name, t=transform: s.outline(n, t))

    print(f'  {weight.css}: 英数字の x 座標は wght {wx:.0f}、y 座標は wght {wy:.0f} から', flush=True)
    return assemble(variant, weight, order, glyf, hmtx, cmap, mono)


def assemble(variant, weight, order, glyf, hmtx, cmap, mono: Source):
    fb = FontBuilder(C.UPM, isTTF=True)
    fb.setupGlyphOrder(order)
    fb.setupCharacterMap(cmap)
    fb.setupGlyf(glyf)
    glyf_table = fb.font['glyf']
    metrics = {}
    for name in order:
        g = glyf_table[name]
        g.recalcBounds(glyf_table)
        metrics[name] = (hmtx[name], getattr(g, 'xMin', 0) if g.numberOfContours else 0)
    fb.setupHorizontalMetrics(metrics)
    fb.setupHorizontalHeader(ascent=C.ASCENT, descent=C.DESCENT, lineGap=0)

    family = variant.family
    style = weight.style
    ps = f'{variant.file_stem}-{style}'
    legacy_family = family if style == 'Regular' else f'{family} {style}'
    copyright_ = 'Copyright 2017 IBM Corp. Lievre Term glyphs (U+E500–E509) copyright 2026 shiroinock.'
    if variant.nerd:
        copyright_ += ' Nerd Fonts symbols copyright their authors (see LICENSES).'
    names = {
        'copyright': copyright_,
        'familyName': legacy_family,
        'styleName': 'Regular',
        'uniqueFontIdentifier': f'{C.VERSION};LVRE;{ps}',
        'fullName': f'{family} {style}',
        'version': f'Version {C.VERSION}; from {C.SOURCES}',
        'psName': ps,
        'licenseDescription': 'This Font Software is licensed under the SIL Open Font License, Version 1.1.',
        'licenseInfoURL': 'https://openfontlicense.org',
        'typographicFamily': family,
        'typographicSubfamily': style,
    }
    fb.setupNameTable(names, mac=False)

    ymin = min(getattr(glyf_table[n], 'yMin', 0) for n in order)
    ymax = max(getattr(glyf_table[n], 'yMax', 0) for n in order)
    mono_os2 = mono.font['OS/2']
    panose = mono_os2.panose
    panose.bProportion = 9  # 等幅
    fs_selection = (1 << 7) | ((1 << 6) if weight.css == 400 else 0)  # USE_TYPO_METRICS / REGULAR
    fb.setupOS2(
        version=4,
        achVendID='LVRE',
        usWeightClass=weight.css,
        fsType=0,
        fsSelection=fs_selection,
        xAvgCharWidth=C.CELL,
        sTypoAscender=C.ASCENT,
        sTypoDescender=C.DESCENT,
        sTypoLineGap=0,
        usWinAscent=max(C.ASCENT, ymax),
        usWinDescent=max(-C.DESCENT, -ymin),
        sxHeight=round(mono_os2.sxHeight * C.LATIN_SY),
        sCapHeight=round(mono_os2.sCapHeight * C.LATIN_SY),
        panose=panose,
        ulCodePageRange1=(1 << 0) | ((1 << 17) if variant.cjk else 0),  # Latin 1 / JIS
        ulCodePageRange2=0,
    )
    post = mono.font['post']
    fb.setupPost(
        keepGlyphNames=False,
        isFixedPitch=1,
        underlinePosition=round(post.underlinePosition * C.LATIN_SY),
        underlineThickness=round(post.underlineThickness * C.LATIN_SY),
    )
    font = fb.font
    font['OS/2'].recalcUnicodeRanges(font)
    font['head'].fontRevision = float(C.VERSION.rsplit('.', 1)[0])
    font['head'].macStyle = 0
    epoch = source_epoch() + 2082844800  # 1904 年起点
    font['head'].created = font['head'].modified = epoch
    font.recalcTimestamp = False
    gasp = newTable('gasp')
    gasp.version = 1
    gasp.gaspRange = {0xFFFF: 0x000F}  # ヒントは持たないので、どの大きさでも滑らかに
    font['gasp'] = gasp
    return font


def cmd_fonts(args):
    width = W.compute(args.ucd)
    out = args.out
    (out / 'ttf').mkdir(parents=True, exist_ok=True)
    if not args.no_woff2:
        (out / 'woff2').mkdir(parents=True, exist_ok=True)
    for vid in args.variant or list(C.VARIANTS):
        variant = C.VARIANTS[vid]
        ttfs = {}
        for css in args.weight or list(C.WEIGHTS):
            weight = C.WEIGHTS[css]
            font = build_font(variant, weight, args.sources, width)
            stem = f'{variant.file_stem}-{weight.style}'
            ttf = out / 'ttf' / f'{stem}.ttf'
            font.save(ttf)
            ttfs[css] = ttf
            line = f'{ttf.name}: {len(font.getBestCmap())} 字, {ttf.stat().st_size} バイト'
            if not args.no_woff2:
                woff2 = out / 'woff2' / f'{stem}.woff2'
                compress(str(ttf), str(woff2))
                line += f', woff2 {woff2.stat().st_size} バイト'
            print(line, flush=True)
        if not args.no_woff2:
            css_path = web.write_web(variant, ttfs, out / 'web')
            print(f'{css_path.name}: Web 用に分けた woff2 と @font-face', flush=True)


def cmd_widths(args):
    args.out.parent.mkdir(parents=True, exist_ok=True)
    W.write(args.ucd, args.out)
    print(f'{args.out}: Unicode {W.UNICODE_VERSION}')


def main(argv=None):
    parser = argparse.ArgumentParser(prog='lievre-term-build', description='Lievre Term を組み立てる')
    sub = parser.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('fonts', help='フォントを書き出す')
    p.add_argument('--sources', type=Path, required=True, help='元のフォント（mono/・jp/・nf/）')
    p.add_argument('--ucd', type=Path, required=True, help='Unicode のデータ')
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--variant', action='append', choices=list(C.VARIANTS))
    p.add_argument('--weight', action='append', type=int, choices=list(C.WEIGHTS))
    p.add_argument('--no-woff2', action='store_true', help='woff2 と Web 用の CSS を書かない')
    p.set_defaults(func=cmd_fonts)
    p = sub.add_parser('widths', help='幅の表を JSON で書き出す')
    p.add_argument('--ucd', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    p.set_defaults(func=cmd_widths)
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == '__main__':
    sys.exit(main())
