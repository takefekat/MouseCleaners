
import sys
import time
import multiprocessing as mp
import socket
import json

from ShareResouce import ShareResouce, NUM_MOUSE

MAZE_SIZE = 16

class ProcessObjRecog():
    def __init__(self, share_resouce:ShareResouce) -> None:
        self.share_resouce = share_resouce
        self.port = 1260
        self._process_wifi = mp.Process(target=self.setup, name="ProcessObjRecog")
        print(f"[obj recog]: ProcessObjRecog.__init__")


    def setup(self):
        print(f"[obj recog]: ProcessObjRecog.setup", self.port)
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.s.bind(('192.168.251.3', self.port))  # IPとポート番号を指定します
        self.s.listen(5)

        # 定常処理
        while True:
            time.sleep(0.1)

            self.clientsocket, address = self.s.accept()
            print(f"[obj recog]: Connection from {address} has been established.")

            # マウス新規接続時初期化
            if self.clientsocket:
                print("[obj recog] socket connected.")

            # self.clientsocket が有効の場合、以下の処理を実行
            while self.clientsocket:
                time.sleep(0.1)
                try:    
                    # クライアントからのメッセージを受信
                    msg_json = self.clientsocket.recv(810)
                    #print(len(msg_json))
                    if not msg_json:
                        print("[obj recog] Received empty message, closing connection.")
                        self.clientsocket.close()
                        break

                    print(f"[obj recog] recv: {msg_json}")

                    msg_list = json.loads(msg_json.decode('utf-8'))
                    #print('msg_lsit: ', msg_list)

                    if self.share_resouce._obj_update.value == 1:
                        obj_idx = 0
                        for y in range(MAZE_SIZE):
                            for x in range(MAZE_SIZE):
                                if msg_list[x][y] == 1:
                                    self.share_resouce._field_obj[obj_idx] = x
                                    obj_idx += 1
                                    self.share_resouce._field_obj[obj_idx] = y
                                    obj_idx += 1
                        self.share_resouce._field_obj[obj_idx] = 255

                except BrokenPipeError: # リモートのクライアントが接続を閉じた後にデータを送信しようとした場合
                    print(f"[obj recog]: Connection closed by client.")
                    self.clientsocket.close()
                    break
                except ConnectionResetError: # クライアントが切断した場合
                    print(f"[obj recog]: Connection reset by client.")
                    self.clientsocket.close()
                    break

                
            print(f"[obj recog]: socket closed.")

            self.clientsocket.close()

    def start(self):
        self._process_wifi.start()

    def close(self):
        try:
            self.clientsocket.close()
            self.s.close()
        except:
            pass
