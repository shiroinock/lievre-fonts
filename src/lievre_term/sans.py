"""Lievre Sans：本文の書体。IBM Plex Sans JP の行の箱だけを変えたもの。

字形・送り幅・カーニング・OpenType の機能（GSUB・GPOS・BASE・縦組みの寸法）は変えない。変えるのは次だけ。

  行の箱  ascent 1130・descent 370・line gap 0（hhea と OS/2 の typo）。高さ 1.5em は Plex Sans JP と同じで、
          中心はベースラインの 0.38em 上（表意文字の字面の枠の中央）。Lievre Term と同じ行の中央になる
  名前    Lievre Sans。Plex は OFL の予約された名前なので使わない
"""

from pathlib import Path

from fontTools.ttLib import TTFont

from . import config as C


def set_names(font: TTFont, family: str, style: str, copyright_: str):
    ps = f'{family.replace(" ", "")}-{style}'
    legacy_family = family if style == 'Regular' else f'{family} {style}'
    names = {
        0: copyright_,
        1: legacy_family,
        2: 'Regular',
        3: f'{C.VERSION};LVRE;{ps}',
        4: f'{family} {style}',
        5: f'Version {C.VERSION}; from IBM Plex Sans JP 3.0.0',
        6: ps,
        13: 'This Font Software is licensed under the SIL Open Font License, Version 1.1.',
        14: 'https://openfontlicense.org',
        16: family,
        17: style,
    }
    table = font['name']
    table.names = []
    for nid, value in names.items():
        table.setName(value, nid, 3, 1, 0x409)


def build_sans(sources: Path, weight: C.Weight, epoch: int) -> TTFont:
    font = TTFont(sources / f'jp/IBMPlexSansJP-{weight.jp}.ttf')
    for tag in ('DSIG',):  # 書き換えると署名は無効になる
        if tag in font:
            del font[tag]
    hhea = font['hhea']
    hhea.ascent, hhea.descent, hhea.lineGap = C.SANS_ASCENT, C.SANS_DESCENT, 0
    os2 = font['OS/2']
    os2.version = max(os2.version, 4)
    os2.sTypoAscender, os2.sTypoDescender, os2.sTypoLineGap = C.SANS_ASCENT, C.SANS_DESCENT, 0
    os2.usWinAscent = max(os2.usWinAscent, C.SANS_ASCENT)
    os2.usWinDescent = max(os2.usWinDescent, -C.SANS_DESCENT)
    os2.fsSelection |= 1 << 7  # USE_TYPO_METRICS
    os2.achVendID = 'LVRE'
    set_names(
        font,
        C.SANS.family,
        weight.style,
        'Copyright 2017 IBM Corp. Lievre Sans: line metrics changed 2026 by shiroinock.',
    )
    head = font['head']
    head.fontRevision = float(C.VERSION.rsplit('.', 1)[0])
    head.created = head.modified = epoch + 2082844800
    font.recalcTimestamp = False
    return font
