

import sys
import time
import multiprocessing as mp

class ShareResouce():
    def __init__(self) -> None:

        # GUI操作イベント
        self._path_ok_event = mp.Event()    # 走行経路確定イベント
        self._start_event = mp.Event()      # 走行開始イベント
        self._stop_event = mp.Event()       # 走行停止イベント
        self._gui_update_event = mp.Event() # GUI更新イベント

        self._gui_close_event = mp.Event()   # 全プロセス終了イベント(GUI終了イベント)

        # 接続マウス数
        self._connected_mice = mp.Value("i",0)

        # 走行経路
        self._path1 = mp.Array("i",[0]*1024)
        self._path2 = mp.Array("i",[0]*1024)
        self._path3 = mp.Array("i",[0]*1024)
        self._path4 = mp.Array("i",[0]*1024)
