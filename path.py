# 必要なモジュールのインポート
from graphillion import GraphSet
import graphillion.tutorial as tl


FIELD_SIZE_IS_8X8 = 0
FIELD_SIZE_IS_32X32 = 1

MOUSE_NUM = 4

# グリッドのサイズを指定
universe = tl.grid(32, 32)
GraphSet.set_universe(universe)
tl.draw(universe)