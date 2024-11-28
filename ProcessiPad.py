
import sys
import time
import multiprocessing as mp
import socket

from ShareResouce import ShareResouce, NUM_MOUSE
import json

MAZE_SIZE = 16

class ProcessiPad():
    def __init__(self, share_resouce:ShareResouce) -> None:
        print("[iPad   ]: ProcessiPad.__init__")
        self.share_resouce = share_resouce
        self._process_ipad = mp.Process(target=self.setup, name="iPadProcess")

    def setup(self):
        print("[iPad   ]: ProcessiPad start")

        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
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
                                self.share_resouce._field_mode.value = 3 # MODE_3 経路全体を表示

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
                                self.share_resouce._field_mode.value = 4 # MODE_4: 往路 

                            elif msg_json["signal"] == "stop":           
                                print("[iPad   ]: stop")
                                # 走行停止イベントをセット
                                for i in range(NUM_MOUSE):
                                    self.share_resouce._stop_event[i] = 1

                            elif msg_json["signal"] == "mode:home":           
                                self.share_resouce._field_mode.value = 7 # MODE_7: ぴかぴかクリーナーズ

                            elif msg_json["signal"] == "mode:objRcg":           
                                self.share_resouce._obj_update.value = 1 # 障害物更新フラグをON
                                self.share_resouce._field_mode.value = 8 # MODE_8: 障害物表示

                            elif msg_json["signal"] == "get_path":
                                self.share_resouce._obj_update.value = 0 # 障害物更新フラグをOFF
                                time.sleep(0.1)
                                
                                # 障害物情報をjson encode & 送信
                                obj_list = {"objs": []}
                                for i in range(1024):
                                    if self.share_resouce._field_obj[2*i] == 255 or self.share_resouce._field_obj[2*i+1] == 255:
                                        break
                                    point = {}
                                    point["x"] = self.share_resouce._field_obj[2*i]
                                    point["y"] = MAZE_SIZE - self.share_resouce._field_obj[2*i+1] - 1
                                    obj_list["objs"].append(point)
                                
                                # デバッグ用に追加
                                obj_list["objs"].append({"x": 0, "y": MAZE_SIZE - 1 - 1})
                                obj_list["objs"].append({"x": 0, "y": MAZE_SIZE - 2 - 1})
                                obj_list["objs"].append({"x": 10, "y": MAZE_SIZE - 2 - 1})
                                #obj_list["objs"].append({"x": 14, "y": MAZE_SIZE - 14 - 1}) # NG
                                obj_list["objs"].append({"x": 14, "y": MAZE_SIZE - 13 - 1})
                                #obj_list["objs"].append({"x": 6, "y": MAZE_SIZE - 8 - 1}) # NG
                                #obj_list["objs"].append({"x": 6, "y": MAZE_SIZE - 9 - 1}) # NG
                                obj_list["objs"].append({"x": 2, "y": MAZE_SIZE - 14 - 1}) # NG
                                self.clientsocket.send(json.dumps(obj_list).encode('utf-8'))

                    except json.JSONDecodeError:
                        print("[iPad   ]: Failed to decode JSON message")

                    self.clientsocket.close()
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
        