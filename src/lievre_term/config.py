"""寸法・太さ・バリエーションの決まり。数を変えるときはここだけを触る。"""

from dataclasses import dataclass

# 全角の幅を 1em（1000）にし、英数字はその半分の 500 にする。
UPM = 1000
CELL = 500

# 英数字は Plex Mono（字幅 600、英大文字の高さ 698）を、横は字幅 500 に、縦は英大文字の高さが
# Plex Sans JP と同じ 733 になるように縮める（横 5/6、縦 733/698）。縦と横で倍率が違うので、
# 線の太さは condense.py で補う。
LATIN_SX = CELL / 600
LATIN_CAP = 733
LATIN_SY = LATIN_CAP / 698
# 罫線とブロック、.notdef は、縦横同じ 5/6 で縮める。
LATIN_SCALE = 5 / 6

# Plex Sans JP 3.0.0 の 'H' の縦の線と横の線の太さ（400 / 500 / 600）。
SANS_STEMS = {400: (84, 74), 500: (113, 100), 600: (132, 116)}
# 英数字の線は、本文（Plex Sans JP）の線のこの割合にする。等幅は字の中の空きが小さく、
# 同じ太さでも黒く見えるので、少し細くして本文と同じ濃さに見せる（見比べて決めた値）。
STROKE_RATIO = 0.93

# 縦の位置の決まり：表意文字の字面の枠を、行（セル）の箱の中央に置く。
# Plex Sans JP の表意文字の枠は -120〜880（BASE の ideo、字面は icfb / icft の -75〜835）で、
# どちらも中心はベースラインの 380 上。Plex Sans JP そのままの行（1060 / -440）の中心は 310 なので、
# 0.07em 上に寄っていた。Web の 'Lievre Sans'（ascent-override: 113%、descent-override: 37%）と同じく、
# 字形は動かさず、行の箱のほうを動かして中心を 380 にする。
CELL_CENTER = 380

# 端末のセル（行）の高さは 1.2em。中心が 380 になるように 980 / -220 にする。
ASCENT = 980
DESCENT = -220

# Lievre Sans（本文の書体）の行の箱。Plex Sans JP そのまま（1060 / -440、中心 310）の高さ 1.5em は保ち、
# 中心を Lievre Term と同じ 380 にする（Web の ascent-override: 113%・descent-override: 37% と同じ）。
SANS_ASCENT = 1130
SANS_DESCENT = -370

# 日本語の字形を縦に動かす量。0 のままにしておくと、Plex Sans JP と同じ行に並べたとき
# （Web で本文の中の等幅など）、ベースラインでそろえても漢字の高さがずれない。
JP_SHIFT = 0

# 英数字の字形は縦に動かさない。英大文字の高さが Plex Sans JP と同じなので、ベースラインを
# 本文と共有したまま、英大文字の中央が本文と同じ位置（行の中央の 0.013em 下）に来る。

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

# 本文の書体。Plex Sans JP の字形とカーニングはそのままで、行の箱と名前だけを変える（sans.py）。
SANS = Variant('lievre-sans', 'Lievre Sans', 'jp', False)

VERSION = '0.1.0'
SOURCES = 'IBM Plex Mono 2.5.0, IBM Plex Mono Variable 1.0.0, IBM Plex Sans JP 3.0.0, Nerd Fonts 3.5.1'
