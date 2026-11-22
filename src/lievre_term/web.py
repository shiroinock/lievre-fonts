"""Web 用の woff2 を unicode-range ごとに分け、そのまま読み込める @font-face の CSS を書く。

ブラウザは、ページに出る字を含む unicode-range のファイルだけを読み込む。分け方は次のとおり。

  base      英数字・記号・罫線・lievre の字形など（日本語と Nerd Fonts 以外のすべて）
  kana      かな・全角の記号と英数字・半角カナ（U+2E80–33FF、U+FE30–FE4F、U+FF00–FFEF の漢字以外）
  kanji1-N  JIS 第1水準の漢字を、符号位置の順に 500 字ずつ
  kanji2-N  そのほかの漢字（第1面まで）を 1000 字ずつ
  kanji3-N  第2面・第3面の漢字を 1000 字ずつ
  nf-pl     Powerline の記号（U+E0A0–E0D7）
  nf-md     Material Design（U+F0001 から）
  nf        そのほかの Nerd Fonts の記号
"""

from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont

from . import config as C
from . import jis

KANA_RANGES = [(0x2E80, 0x33FF), (0xFE30, 0xFE4F), (0xFF00, 0xFFEF)]
LIEVRE_PUA = (0xE500, 0xE53F)


def group(cp: int) -> str:
    if LIEVRE_PUA[0] <= cp <= LIEVRE_PUA[1]:
        return 'base'
    if 0xE0A0 <= cp <= 0xE0D7:
        return 'nf-pl'
    if cp >= 0xF0000:
        return 'nf-md'
    if 0xE000 <= cp <= 0xF8FF:
        return 'nf'
    if jis.is_ideograph(cp):
        if cp in jis.level1():
            return 'kanji1'
        return 'kanji3' if cp >= 0x20000 else 'kanji2'
    if any(a <= cp <= b for a, b in KANA_RANGES):
        return 'kana'
    return 'base'


CHUNK = {'kanji1': 500, 'kanji2': 1000, 'kanji3': 1000}
ORDER = ['base', 'kana', 'kanji1', 'kanji2', 'kanji3', 'nf-pl', 'nf', 'nf-md']


def subsets(cps) -> list[tuple[str, list[int]]]:
    """(名前, 符号位置の並び) を、CSS に書く順に返す。"""
    groups: dict[str, list[int]] = {}
    for cp in sorted(cps):
        groups.setdefault(group(cp), []).append(cp)
    out = []
    for name in ORDER:
        members = groups.get(name)
        if not members:
            continue
        size = CHUNK.get(name)
        if size is None:
            out.append((name, members))
        else:
            for i in range(0, len(members), size):
                out.append((f'{name}-{i // size}', members[i : i + size]))
    return out


def unicode_range(cps: list[int]) -> str:
    parts = []
    start = prev = cps[0]
    for cp in cps[1:] + [None]:
        if cp is not None and cp == prev + 1:
            prev = cp
            continue
        parts.append(f'U+{start:X}' if start == prev else f'U+{start:X}-{prev:X}')
        if cp is not None:
            start = prev = cp
    return ', '.join(parts)


def parse_unicode_range(text: str) -> set[int]:
    out = set()
    for part in text.split(','):
        part = part.strip().removeprefix('U+')
        a, _, b = part.partition('-')
        out.update(range(int(a, 16), int(b or a, 16) + 1))
    return out


def write_subset(ttf: Path, cps: list[int], out: Path):
    opts = subset.Options()
    opts.flavor = 'woff2'
    opts.layout_features = []
    opts.name_IDs = ['*']
    opts.name_languages = ['*']
    opts.notdef_outline = True
    opts.recalc_timestamp = False
    opts.prune_unicode_ranges = True
    font = TTFont(ttf)
    sub = subset.Subsetter(opts)
    sub.populate(unicodes=cps)
    sub.subset(font)
    font.flavor = 'woff2'
    font.save(out)


def write_web(variant: C.Variant, ttfs: dict[int, Path], out: Path) -> Path:
    """variant の CSS（out/<id>.css）と分けた woff2（out/files/）を書き、CSS の場所を返す。"""
    files = out / 'files'
    files.mkdir(parents=True, exist_ok=True)
    blocks = [
        f'/* {variant.family} {C.VERSION}. SIL Open Font License 1.1（LICENSES/OFL.txt）。 */',
        f"/* 使い方：font-family: '{variant.family}', monospace; */",
    ]
    for css_weight, ttf in sorted(ttfs.items()):
        weight = C.WEIGHTS[css_weight]
        cmap = TTFont(ttf).getBestCmap()
        for name, cps in subsets(cmap):
            fname = f'{variant.file_stem}-{weight.style}.{name}.woff2'
            write_subset(ttf, cps, files / fname)
            blocks.append(
                '@font-face {\n'
                f"  font-family: '{variant.family}';\n"
                '  font-style: normal;\n'
                f'  font-weight: {css_weight};\n'
                '  font-display: swap;\n'
                f"  src: url('files/{fname}') format('woff2');\n"
                f'  unicode-range: {unicode_range(cps)};\n'
                '}'
            )
    css = out / f'{variant.id}.css'
    css.write_text('\n\n'.join(blocks) + '\n', encoding='utf-8')
    return css
