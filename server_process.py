
import socket
from multiprocessing import Process, Event, Queue
import time

def server_process(data_queue):

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('192.168.251.3', 1235))  # IPとポート番号を指定します
    s.listen(5)

    while True:
        clientsocket, address = s.accept()
        print(f"Connection from {address} has been established.")

        # clientsocket が有効の場合、以下の処理を実行
        while clientsocket:
            try:
                # キューからデータを取得
                data = data_queue.get(True)
                if data == "0":
                    send_msg = "invalid\0"
                if data == "1":
                    path_list = [str(i) for i in range(1, 10)] 
                    send_msg = ",".join(path_list) + "\0"
                elif data == "2":
                    path_list = [str(i) for i in range(1, 1024)]
                    send_msg = ",".join(path_list) + "\0"
                elif data == "3":
                    send_msg = "START\0"
                elif data == "4":
                    send_msg = "STOP\0"
                else:
                    send_msg = "INVALID\0"
                    pass
                clientsocket.send(send_msg.encode("utf-8"))
                print("send :", send_msg)

                time.sleep(0.5)

                # クライアントからのメッセージを受信
                msg = clientsocket.recv(10000)
                print("rcv:", msg.decode("utf-8", errors="ignore"))

                # クライアントからのメッセージがcloseの場合、通信を終了
                if msg == "CLOSE":
                    break
                   

            except BrokenPipeError:
                print("Connection closed by client.")
                clientsocket.close()
                break
            
        print("Connection closed.")
        clientsocket.close()
        time.sleep(1)
        


def std_input(data_queue):
    while True:
        # 標準入力を受け付ける
        print("1,2,3,4: ",end="")
        msg_type = input()
        data_queue.put(msg_type)





def main():
    # イベントとキューの作成
    data_queue = Queue()

    # プロセスを作成します
    #user_p = Process(target=std_input, args=(data_queue,))
    server_p = Process(target=server_process, args=(data_queue,))

    # プロセスを開始します
    server_p.start()

    std_input(data_queue)

    # 各プロセスの終了を待ちます
    #p1.join()
    #p2.join()

    # prは無限ループなので、強制終了
    server_p.terminate()

if __name__ == '__main__':
    main()