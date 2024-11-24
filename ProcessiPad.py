
import sys
import time
import multiprocessing as mp
import socket

from ShareResouce import ShareResouce, NUM_MOUSE
import json

class ProcessiPad():
    def __init__(self, share_resouce:ShareResouce) -> None:
        print("[iPad   ]: ProcessiPad.__init__")
        self.share_resouce = share_resouce
        self._process_ipad = mp.Process(target=self.setup, name="iPadProcess")

    def setup(self):
        print("[iPad   ]: ProcessiPad start")

        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.bind(('192.168.251.3', 1251))  # IPとポート番号を指定します
        self.s.listen(5)

        while True:
            self.clientsocket, address = self.s.accept()
            print(f"[iPad   ]: Connection from {address} has been established.")

            # clientsocket が有効の場合、以下の処理を実行
            while self.clientsocket:
                try:
                    # クライアントからのメッセージを受信
                    msg = self.clientsocket.recv(10000)
                    print("[iPad   ]: rcv :", msg.decode("utf-8", errors="ignore"))

                    # msgをjson形式に変換
                    msg = msg.decode("utf-8", errors="ignore")
                    try:
                        msg_json = json.loads(msg)

                        # "paths"が含まれている場合、パスを更新
                        if "paths" in msg_json:
                            print("[iPad   ]: get paths from iPad")
                            for path in msg_json["paths"]:
                                if path['mouse_id'] == 0:
                                    for i in range(len(path['path'])):
                                        self.share_resouce._path0[i] = path['path'][i]
                                    self.share_resouce._path0[len(path['path'])] = 255
                                elif path['mouse_id'] == 1:
                                    for i in range(len(path['path'])):
                                        self.share_resouce._path1[i] = path['path'][i]
                                    self.share_resouce._path1[len(path['path'])] = 255
                                elif path['mouse_id'] == 2:
                                    for i in range(len(path['path'])):
                                        self.share_resouce._path2[i] = path['path'][i]
                                    self.share_resouce._path2[len(path['path'])] = 255
                                elif path['mouse_id'] == 3:
                                    for i in range(len(path['path'])):
                                        self.share_resouce._path3[i] = path['path'][i]
                                    self.share_resouce._path3[len(path['path'])] = 255
                                else:
                                    print("[iPad   ]: mouse_id error")

                                # 走行経路送信イベントをセット
                                self.share_resouce._send_path_event[path['mouse_id']] = 1

                                # フィールドモードを経路全体表示に変更
                                self.share_resouce._field_mode.value = 3 # 経路全体を表示

                            # GUI更新イベントをセット
                            self.share_resouce._gui_update_event.set()

    
                        elif "signal" in msg_json:
                            if msg_json["signal"] == "start":
                                print("[iPad   ]: start")
                                # 走行開始イベントをセット
                                for i in range(NUM_MOUSE):
                                    self.share_resouce._start_event[i] = 1          # 走行開始イベントをセット
                                    self.share_resouce._field_mode5_is_goal[i] = 0  # ゴールフラグをリセット

                                # フィールドモードを経路全体表示に変更
                                self.share_resouce._field_mode.value = 5 # 経路を時間にあわせて表示(マウス自己位置までの経路を表示)

                            elif msg_json["signal"] == "stop":           
                                print("[iPad   ]: stop")
                                # 走行停止イベントをセット
                                for i in range(NUM_MOUSE):
                                    self.share_resouce._stop_event[i] = 1

                    except json.JSONDecodeError:
                        print("[iPad   ]: Failed to decode JSON message")

                    break # 一度受信したら終了

                except BrokenPipeError:
                    print("[iPad   ]: Connection closed by client.")
                    self.clientsocket.close()
                    break

    def start(self):
        self._process_ipad.start()
    
    def close(self):
        print("[iPad   ]: ProcessiPad.close")
        try:
            self.clientsocket.close()
            self.s.close()
        except:
            pass
        