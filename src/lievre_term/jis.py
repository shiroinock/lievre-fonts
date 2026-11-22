"""JIS X 0208 の第1水準の漢字（2965字）。Python の EUC-JP の表から引くので、ネットワークも外部の表も要らない。"""

from functools import cache

# 第1水準は 16 区から 47 区（47 区は 51 点まで）。EUC-JP では区・点にそれぞれ 0xA0 を足した2バイト。
LEVEL1_ROWS = range(16, 48)


@cache
def level1() -> frozenset[int]:
    out = set()
    for row in LEVEL1_ROWS:
        for cell in range(1, 95):
            try:
                ch = bytes([0xA0 + row, 0xA0 + cell]).decode('euc_jp')
            except UnicodeDecodeError:
                continue
            out.add(ord(ch))
    return frozenset(out)


IDEOGRAPH_RANGES = [
    (0x3400, 0x4DBF),  # 拡張 A
    (0x4E00, 0x9FFF),  # 統合漢字
    (0xF900, 0xFAFF),  # 互換漢字
    (0x20000, 0x3FFFF),  # 第2面・第3面
]


def is_ideograph(cp: int) -> bool:
    return any(a <= cp <= b for a, b in IDEOGRAPH_RANGES)
