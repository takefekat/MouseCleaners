

import sys
import time
import multiprocessing as mp

NUM_MOUSE = 4

class ShareResouce():
    def __init__(self) -> None:

        # GUI操作イベント
        self._send_path_event   = mp.Array("i",[0]*NUM_MOUSE)   # 走行経路送信イベント
        self._start_event       = mp.Array("i",[0]*NUM_MOUSE)   # 走行開始イベント
        self._stop_event        = mp.Array("i",[0]*NUM_MOUSE)   # 走行停止イベント
        self._gui_update_event  = mp.Event()                    # GUI更新イベント

        self._gui_close_event = mp.Event()   # 全プロセス終了イベント(GUI終了イベント)

        # 接続マウス数
        self._connected_mice = mp.Value("i",0)

        # 走行経路
        self._path0 = mp.Array("i",[0]*1024*2)
        self._path1 = mp.Array("i",[0]*1024*2)
        self._path2 = mp.Array("i",[0]*1024*2)
        self._path3 = mp.Array("i",[0]*1024*2)
