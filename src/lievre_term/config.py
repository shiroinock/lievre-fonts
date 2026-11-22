"""寸法・太さ・バリエーションの決まり。数を変えるときはここだけを触る。"""

from dataclasses import dataclass

# 全角の幅を 1em（1000）にし、英数字はその半分の 500 にする。
UPM = 1000
CELL = 500

# Plex Mono（字幅 600）を 5/6 に縮めて 500 にする。Web の Lievre Mono の size-adjust: 83.333% と同じ。
LATIN_SCALE = 5 / 6

# 縦の位置の決まり：表意文字の字面の枠を、行（セル）の箱の中央に置く。
# Plex Sans JP の表意文字の枠は -120〜880（BASE の ideo、字面は icfb / icft の -75〜835）で、
# どちらも中心はベースラインの 380 上。Plex Sans JP そのままの行（1060 / -440）の中心は 310 なので、
# 0.07em 上に寄っていた。Web の 'Lievre Sans'（ascent-override: 113%、descent-override: 37%）と同じく、
# 字形は動かさず、行の箱のほうを動かして中心を 380 にする。
CELL_CENTER = 380

# 端末のセル（行）の高さは 1.2em。中心が 380 になるように 980 / -220 にする。
ASCENT = 980
DESCENT = -220

# 日本語の字形を縦に動かす量。0 のままにしておくと、Plex Sans JP と同じ行に並べたとき
# （Web で本文の中の等幅など）、ベースラインでそろえても漢字の高さがずれない。
JP_SHIFT = 0

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
