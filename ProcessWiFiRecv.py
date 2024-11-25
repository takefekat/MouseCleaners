
import sys
import time
import multiprocessing as mp
import socket

from ShareResouce import ShareResouce, NUM_MOUSE

RECV_BUF_SIZE = 20
MOUCE_NAME = ["赤", "青", "緑", "黄"]

class ProcessWiFiRecv():
    def __init__(self, share_resouce:ShareResouce, mouse_idx:int) -> None:
        self.share_resouce = share_resouce
        self.mouse_idx = mouse_idx
        self.port = 1235 + mouse_idx + 10
        self._process_wifi = mp.Process(target=self.setup, name="ProcessWiFiRecv")
        print(f"[mouce {self.mouse_idx} recv]: ProcessWiFiRecv.__init__")


    def setup(self):
        print(f"[mouce {self.mouse_idx} recv]: ProcessWiFiRecv.setup", self.port)
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.s.bind(('192.168.251.3', self.port))  # IPとポート番号を指定します
        self.s.listen(5)

        # 定常処理
        while True:
            time.sleep(1)

            self.clientsocket, address = self.s.accept()
            print(f"[mouce {self.mouse_idx} recv]: Connection from {address} has been established.")

            # マウス新規接続時初期化
            if self.clientsocket:
                self.share_resouce._send_path_event[self.mouse_idx] = 0
                self.share_resouce._start_event[self.mouse_idx] = 0
                self.share_resouce._stop_event[self.mouse_idx] = 0
                self.share_resouce._return_event[self.mouse_idx] = 0
                self.share_resouce._field_mode5_is_goal[self.mouse_idx] = 0
                self.share_resouce._connected_mice[self.mouse_idx] = 1
                mouce_num = sum(self.share_resouce._connected_mice)
                print("[mouce {self.mouse_idx} connected. MOUCE_NUM =", mouce_num)

            msg_buf = [0] * RECV_BUF_SIZE            
            msg_idx = 0
            check_sum = 0
            # self.clientsocket が有効の場合、以下の処理を実行
            while self.clientsocket:
                self.share_resouce._connected_mice[self.mouse_idx] = 1  # ソケット接続中 --> マウスあり
                time.sleep(1/40)
                try:    
                    # クライアントからのメッセージを受信
                    # プロトコルに従って解釈
                    msg = self.clientsocket.recv(20)
                    for c in msg:
                        if msg_idx == 0: # header: < が来たら受信開始
                            if c == 60:                        
                                msg_buf[0] = 60
                                msg_idx += 1
                            else:
                                msg_buf = [0] * RECV_BUF_SIZE
                                msg_idx = 0
                                check_sum = 0
                                print(f"[mouce {self.mouse_idx} recv]: protocol header error. recv --> ", c)
                        elif msg_idx == 1: # data_len
                            msg_buf[1] = c
                            msg_idx += 1
                        elif msg_idx < msg_buf[1] + 2: # data
                            msg_buf[msg_idx] = c
                            msg_idx += 1
                            check_sum = (check_sum + c) % 256
                        elif msg_idx == msg_buf[1] + 2: # check_sum
                            msg_buf[msg_idx] = c
                            msg_idx += 1
                            if check_sum % 256 == c:
                                #print(f"[mouce {self.mouse_idx} recv]: rcv :", msg_buf[:msg_idx])
                                self.success_recv(msg_buf)
                                msg_buf = [0] * RECV_BUF_SIZE
                                msg_idx = 0
                                check_sum = 0
                            else: # check_sum error --> reset buffer
                                msg_buf = [0] * RECV_BUF_SIZE
                                msg_idx = 0
                                check_sum = 0
                                print(f"[mouce {self.mouse_idx} recv]: check_sum error")
                        else:
                            msg_buf = [0] * RECV_BUF_SIZE
                            msg_idx = 0
                            check_sum = 0
                            print(f"[mouce {self.mouse_idx} recv]: protocol error")

                except BrokenPipeError:
                    print(f"[mouce {self.mouse_idx} recv]: Connection closed by client.")
                    self.clientsocket.close()
                    break
                
            print(f"[mouce {self.mouse_idx} recv]: Connection closed.")
            self.share_resouce._connected_mice[self.mouse_idx] = 0  # マウスなし

            self.clientsocket.close()
            time.sleep(1)

    # マウスからの位置情報を受信したときの処理
    #  0: heddar <
    #  1: length
    #  2: x座標(1byte目)  unit=mm (0-1440mm) の理論値
    #  3: x座標(2byte目)  unit=mm (0-1440mm) の理論値
    #  4: y座標(1byte目)  unit=mm (0-1440mm) の理論値
    #  5: y座標(2byte目)  unit=mm (0-1440mm) の理論値
    #  6: theta(1byte): 0をX軸として255で360degの角度
    #  7: velocity(1byte): 車速[m/s]の10倍
    #  8: battery(1byte): バッテリー電圧[V]の10倍 <-- 11V(110)以下は充電を促す
    #  9: state(1byte): 走行中とかの状態
    # 10: error(1byte): エラーフラグ(正常時はfalse)
    # 11: check_sum
    def success_recv(self, msg_buf):
        x = ((msg_buf[2] * 256 ) + msg_buf[3]) // 90 # 1440mm -> 16
        y = ((msg_buf[4] * 256 ) + msg_buf[5]) // 90 # 1440mm -> 16 
        if self.mouse_idx == 0:
            #if  self.share_resouce._mouse0_pos[0] != x:
                self.share_resouce._mouse0_pos[0] = x
            #if  self.share_resouce._mouse0_pos[1] != y:
                self.share_resouce._mouse0_pos[1] = y
        elif self.mouse_idx == 1:
            #if  self.share_resouce._mouse1_pos[0] != x:
                self.share_resouce._mouse1_pos[0] = x
            #if  self.share_resouce._mouse1_pos[1] != y:
                self.share_resouce._mouse1_pos[1] = y
        elif self.mouse_idx == 2:
            #if  self.share_resouce._mouse2_pos[0] != x:
                self.share_resouce._mouse2_pos[0] = x
            #if  self.share_resouce._mouse2_pos[1] != y:
                self.share_resouce._mouse2_pos[1] = y
        elif self.mouse_idx == 3:
            #if  self.share_resouce._mouse3_pos[0] != x:
                self.share_resouce._mouse3_pos[0] = x
            #if  self.share_resouce._mouse3_pos[1] != y:
                self.share_resouce._mouse3_pos[1] = y
        else:
            print(f"[mouce {self.mouse_idx}]: mouse_id error")

        # バッテリー電圧が低い場合は警告
        if msg_buf[8] < 110:
            print(f"[mouce {MOUCE_NAME[self.mouse_idx]}]: ##### WARNING ##### Low battery !!", msg_buf[8] / 10, "V") 

        # エラーがある場合は全マウスを停止
        if msg_buf[10] == 1:
            print(f"[mouce {MOUCE_NAME[self.mouse_idx]}]: ##### ERROR ##### MOUSE ")
            for i in range(NUM_MOUSE):
                self.share_resouce._stop_event[i] = 1
    
    def start(self):
        self._process_wifi.start()

    def close(self):
        print(f"[mouce {self.mouse_idx} recv]: ProcessWiFiRecv.close")
        try:
            self.clientsocket.close()
            self.s.close()
        except:
            pass
