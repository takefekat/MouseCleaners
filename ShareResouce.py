

import sys
import time
import multiprocessing as mp

NUM_MOUSE = 4

class ShareResouce():
    def __init__(self) -> None:

        # GUI操作イベント
        self._send_path_event   = mp.Array("i",[0]*NUM_MOUSE)   # 走行経路送信イベント
        self._start_event       = mp.Array("i",[0]*NUM_MOUSE)   # 往路走行開始イベント
        self._stop_event        = mp.Array("i",[0]*NUM_MOUSE)   # 走行停止イベント
        self._return_event      = mp.Array("i",[0]*NUM_MOUSE)   # 復路走行停止イベント
        self._dummy_event      = mp.Array("i",[0]*NUM_MOUSE)   # 復路走行停止イベント
        self._gui_update_event  = mp.Event()                    # GUI更新イベント

        self._gui_close_event = mp.Event()   # 全プロセス終了イベント(GUI終了イベント)

        # 接続マウス数
        self._connected_mice = mp.Array("i",[0]*NUM_MOUSE)

        # フィールド更新用
        self._field_mode = mp.Value("i",0)
        self._field_mode5_is_goal = mp.Array("i",[0]*NUM_MOUSE)
        self._field_timer_count = mp.Value("i",0)

        # 障害物更新用
        self._obj_update = mp.Value("i",0)

        # 走行経路
        self._path0 = mp.Array("i",[255]*1024*2) # マウス0の走行経路(x,y)の列
        self._path1 = mp.Array("i",[255]*1024*2) # マウス1の走行経路(x,y)の列
        self._path2 = mp.Array("i",[255]*1024*2) # マウス2の走行経路(x,y)の列
        self._path3 = mp.Array("i",[255]*1024*2) # マウス3の走行経路(x,y)の列
        self._field_obj   = mp.Array("i",[255]*1024*2) # 障害物(x,y)の列
        # マウスの現在位置
        self._mouse0_pos = mp.Array("i",[0]*2)
        self._mouse1_pos = mp.Array("i",[0]*2)
        self._mouse2_pos = mp.Array("i",[0]*2)
        self._mouse3_pos = mp.Array("i",[0]*2)

        # GUIマップ
        self._map_r = mp.Array("i",[0]*32*32)
        self._map_g = mp.Array("i",[0]*32*32)
        self._map_b = mp.Array("i",[0]*32*32)
