"""字の幅（セルの数）の表。@lievre/tui が使う string-width 8 の決まりを、1文字ずつに当てはめたもの。

string-width（ambiguousIsNarrow は既定の true）が1文字に返す値は次のとおり。

  0  表示しない文字：Default_Ignorable_Code_Point、一般カテゴリが Cc・Cf・Mn・Me・Cs
  2  RGI の絵文字（emoji-sequences.txt の Basic_Emoji のうち1文字のもの）
  2  East Asian Width が W（Wide）か F（Fullwidth）
  1  それ以外。幅のあいまいな A（Ambiguous）も 1。私用領域も A なので 1

元にするのは Unicode 18.0.0 の UCD（get-east-asian-width 1.7.0 と同じ版）。
"""

import json
from pathlib import Path

UNICODE_VERSION = '18.0.0'
MAX_CP = 0x10FFFF
ZERO_CATEGORIES = {'Cc', 'Cf', 'Mn', 'Me', 'Cs'}


def _ranges(path: Path):
    """UCD の 'XXXX..YYYY ; 値 # 説明' の行を (start, end, 値) で返す。"""
    for line in path.read_text(encoding='utf-8').splitlines():
        line = line.split('#', 1)[0].strip()
        if not line:
            continue
        cps, value = (part.strip() for part in line.split(';')[:2])
        if '..' in cps:
            a, b = cps.split('..')
        else:
            a = b = cps
        yield int(a, 16), int(b, 16), value


def _basic_emoji(path: Path):
    for line in path.read_text(encoding='utf-8').splitlines():
        line = line.split('#', 1)[0].strip()
        if not line:
            continue
        fields = [f.strip() for f in line.split(';')]
        if fields[1] != 'Basic_Emoji' or ' ' in fields[0]:
            continue  # FE0F の付く並びは1文字ではない
        if '..' in fields[0]:
            a, b = fields[0].split('..')
        else:
            a = b = fields[0]
        yield int(a, 16), int(b, 16)


def compute(ucd: Path) -> bytearray:
    """全符号位置の幅を、符号位置を添字にした bytearray で返す。"""
    width = bytearray([1]) * (MAX_CP + 1)
    for a, b, v in _ranges(ucd / 'EastAsianWidth.txt'):
        if v in ('W', 'F'):
            width[a : b + 1] = bytes([2]) * (b - a + 1)
    for a, b in _basic_emoji(ucd / 'emoji-sequences.txt'):
        width[a : b + 1] = bytes([2]) * (b - a + 1)
    for a, b, v in _ranges(ucd / 'DerivedGeneralCategory.txt'):
        if v in ZERO_CATEGORIES:
            width[a : b + 1] = bytes(b - a + 1)
    for a, b, v in _ranges(ucd / 'DerivedCoreProperties.txt'):
        if v == 'Default_Ignorable_Code_Point':
            width[a : b + 1] = bytes(b - a + 1)
    return width


def _runs(width: bytearray, value: int):
    out = []
    start = None
    for cp, w in enumerate(width):
        if w == value and start is None:
            start = cp
        elif w != value and start is not None:
            out.append([start, cp - 1])
            start = None
    if start is not None:
        out.append([start, len(width) - 1])
    return out


def to_json(width: bytearray) -> dict:
    return {
        'format': 1,
        'unicode': UNICODE_VERSION,
        'rule': 'string-width 8 (ambiguousIsNarrow: true) per code point',
        'default': 1,
        'zero': _runs(width, 0),
        'wide': _runs(width, 2),
    }


def from_json(data: dict) -> bytearray:
    width = bytearray([data['default']]) * (MAX_CP + 1)
    for key, value in (('zero', 0), ('wide', 2)):
        for a, b in data[key]:
            width[a : b + 1] = bytes([value]) * (b - a + 1)
    return width


def write(ucd: Path, out: Path):
    out.write_text(json.dumps(to_json(compute(ucd)), separators=(',', ':')) + '\n', encoding='utf-8')
