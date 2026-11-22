"""寸法・太さ・バリエーションの決まり。数を変えるときはここだけを触る。"""

from dataclasses import dataclass

# 全角の幅を 1em（1000）にし、英数字はその半分の 500 にする。
UPM = 1000
CELL = 500

# Plex Mono（字幅 600）を 5/6 に縮めて 500 にする。Web の Lievre Mono の size-adjust: 83.333% と同じ。
LATIN_SCALE = 5 / 6

# 端末のセル（行）の高さは 1.2em。中心は Plex Mono の行の中心（(1025 - 275) / 2 = 375）を
# 5/6 にした 312.5 に置き、整数に丸めて 912 / -288 にする（中心は 312）。
ASCENT = 912
DESCENT = -288
CELL_CENTER = (ASCENT + DESCENT) / 2

# Plex Sans JP の全角の字面（BASE の icfb / icft、-75〜835）の中心は 380 で、
# そのままだとセルの中心より 68（0.068em）上に寄る。日本語の字形をまとめてこれだけ下げる。
# 0 にすると Plex Sans JP の元の位置のまま。
JP_SHIFT = -68

# lievre の字形の線の太さ。試作（字幅 600 で 50）を 5/6 にしたもの。Plex Mono の罫線と同じく、
# 字の太さが変わっても線の太さは変えない（─ と並べて使うので、太さがずれると継ぎ目が目立つ）。
STROKE = 42

# lievre の字形の線がセルの外へはみ出す量。隣のセルと重ねて継ぎ目の細い隙間を消す。
BLEED = 10

# Plex Mono の罫線（U+2500–259F）が前提にしているセルの縦の範囲。U+2502 が -350〜950 に描かれている。
MONO_BOX_BOTTOM, MONO_BOX_TOP = -350, 950

# Symbols Nerd Font Mono の升目（UPM 2048、-410〜1638）。
NF_UPM = 2048
NF_BOTTOM, NF_TOP = -410, 1638

# Powerline の区切り（三角や半円など）は、セルの高さいっぱいに引き伸ばす。
POWERLINE_SEPARATORS = range(0xE0B0, 0xE0D8)


@dataclass(frozen=True)
class Weight:
    css: int
    style: str  # 書体名に付く名前
    mono: str  # IBM Plex Mono のファイル名の太さ
    jp: str  # IBM Plex Sans JP のファイル名の太さ


# トークンの --lv-weight-* と同じ 400 / 500 / 600。
WEIGHTS = {
    400: Weight(400, 'Regular', 'Regular', 'Regular'),
    500: Weight(500, 'Medium', 'Medium', 'Medium'),
    600: Weight(600, 'SemiBold', 'SemiBold', 'SemiBold'),
}


@dataclass(frozen=True)
class Variant:
    id: str
    family: str
    cjk: str | None  # None / 'jp1'（JIS 第1水準まで）/ 'jp'（Plex Sans JP の全部）
    nerd: bool

    @property
    def file_stem(self) -> str:
        return self.family.replace(' ', '')


VARIANTS = {
    v.id: v
    for v in [
        Variant('lievre-term', 'Lievre Term', None, False),
        Variant('lievre-term-nf', 'Lievre Term NF', None, True),
        Variant('lievre-term-jp1', 'Lievre Term JP1', 'jp1', False),
        Variant('lievre-term-jp1-nf', 'Lievre Term JP1 NF', 'jp1', True),
        Variant('lievre-term-jp', 'Lievre Term JP', 'jp', False),
        Variant('lievre-term-jp-nf', 'Lievre Term JP NF', 'jp', True),
    ]
}

VERSION = '0.1.0'
SOURCES = 'IBM Plex Mono 2.5.0, IBM Plex Sans JP 3.0.0, Nerd Fonts 3.5.1'
