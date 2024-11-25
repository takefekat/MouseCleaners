
import sys
import time
import multiprocessing as mp
import socket

from ShareResouce import ShareResouce


class ProcessWiFiSend():
    def __init__(self, share_resouce:ShareResouce, mouse_idx:int) -> None:
        self.share_resouce = share_resouce
        self.mouse_idx = mouse_idx
        self.port = 1235 + mouse_idx 
        self._process_wifi = mp.Process(target=self.setup, name="ProcessWiFiSend")
        print(f"[mouce {self.mouse_idx} send]: ProcessWiFiSend.__init__")


    def setup(self):
        print(f"[mouce {self.mouse_idx} send]: ProcessWiFiSend.setup", self.port)
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.s.bind(('192.168.251.3', self.port))  # IPとポート番号を指定します
        self.s.listen(5)

        # 定常処理
        while True:
            time.sleep(1)

            self.clientsocket, address = self.s.accept()
            print(f"[mouce {self.mouse_idx} send]: Connection from {address} has been established.")
            
            # マウス新規接続時初期化: share_resouceの初期化をしたほうがいい。
            if self.clientsocket:
                self.share_resouce._send_path_event[self.mouse_idx] = 0
                self.share_resouce._start_event[self.mouse_idx] = 0
                self.share_resouce._stop_event[self.mouse_idx] = 0
                self.share_resouce._return_event[self.mouse_idx] = 0
                self.share_resouce._field_mode5_is_goal[self.mouse_idx] = 0
                self.share_resouce._connected_mice[self.mouse_idx] = 1
                mouce_num = sum(self.share_resouce._connected_mice)
                print("[mouce {self.mouse_idx} connected. MOUCE_NUM =", mouce_num)

            # self.clientsocket が有効の場合、以下の処理を実行
            while self.clientsocket:
                self.share_resouce._connected_mice[self.mouse_idx] = 1  # ソケット接続中 --> マウスあり
                time.sleep(0.5)
                try:
                    # mouse_idx の経路が設定されていれば送信
                    if self.share_resouce._send_path_event[self.mouse_idx] == 1:
                        self.share_resouce._send_path_event[self.mouse_idx] = 0
                        send_data = self.send_path()

                    # mouse_idx の走行開始イベントがあれば送信
                    elif self.share_resouce._start_event[self.mouse_idx] == 1:
                        self.share_resouce._start_event[self.mouse_idx] = 0
                        send_data = b'START'

                    # mouse_idx の走行停止イベントがあれば送信
                    elif self.share_resouce._stop_event[self.mouse_idx] == 1:
                        self.share_resouce._stop_event[self.mouse_idx] = 0
                        send_data = b'STOP'

                    # mouse_idx の走行停止イベントがあれば送信
                    elif self.share_resouce._return_event[self.mouse_idx] == 1:
                        self.share_resouce._return_event[self.mouse_idx] = 0
                        send_data = b'RETURN'

                    else:
                        continue
                    
                    send_msg = self.make_send_msg(send_data)
                    self.clientsocket.send(send_msg)
                    print(f"[mouce {self.mouse_idx} send]: send :", send_msg)


                except BrokenPipeError:
                    print(f"[mouce {self.mouse_idx} send]: Connection closed by client.")
                    self.clientsocket.close()
                    break
                
            print(f"[mouce {self.mouse_idx} send]: Connection closed.")

            self.clientsocket.close()
            self.share_resouce._connected_mice[self.mouse_idx] = 0  # マウスなし
            time.sleep(1)

    def make_send_msg(self, data:bytes):
        data_len = len(data)
        check_sum = 0
        for i in range(len(data)):
            check_sum += data[i]
        check_sum = check_sum % 256

        return b'>' + data_len.to_bytes(2, "big") + data + check_sum.to_bytes(1, "big")

    def send_path(self):
        print(f"[mouce {self.mouse_idx} send]: send_path", self.mouse_idx)
        path = bytes()
        for i in range(1024):
            # TODO: マウスの識別がダサいので修正する
            index = 0
            if self.mouse_idx == 0:
                index = self.share_resouce._path0[i]
            elif self.mouse_idx == 1:
                index = self.share_resouce._path1[i]
            elif self.mouse_idx == 2:
                index = self.share_resouce._path2[i]
            elif self.mouse_idx == 3:
                index = self.share_resouce._path3[i]
            else:
                break

            # 経路の終端を示す0があれば終了
            if index == 255:
                break
            
            path = path + index.to_bytes(1, "big")
        return path
    
    def start(self):
        self._process_wifi.start()

    def close(self):
        print(f"[mouce {self.mouse_idx} send]: ProcessWiFiSend.close")
        try:
            self.clientsocket.close()
            self.s.close()
        except:
            pass
