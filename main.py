
import sys
import time
import multiprocessing as mp

from ShareResouce import ShareResouce, NUM_MOUSE
from ProcessGUI import ProcessGUI
from ProcessWiFi import ProcessWiFi
from ProcessWiFiRecv import ProcessWiFiRecv
from ProcessWiFiSend import ProcessWiFiSend
from ProcessField import ProcessField
from ProcessiPad import ProcessiPad
from ProcessObjRecog import ProcessObjRecog

def main():
    # プロセス間共有リソースの生成
    share_resouce = ShareResouce()

    # プロセスの生成
    process_field   = ProcessField(share_resouce=share_resouce) # フィールド描画プロセス
    #process_gui     = ProcessGUI(share_resouce=share_resouce)   # GUIプロセス
    process_ipad    = ProcessiPad(share_resouce=share_resouce)  # iPadプロセス
    process_obj_recog = ProcessObjRecog(share_resouce=share_resouce) # 物体認識プロセス

    process_wifi_send = [] # マウスWiFi送信プロセス
    process_wifi_recv = [] # マウスWiFi受信プロセス
    for i in range(NUM_MOUSE):
        process_wifi_send.append(ProcessWiFiRecv(share_resouce=share_resouce, mouse_idx=i))
        process_wifi_recv.append(ProcessWiFiSend(share_resouce=share_resouce, mouse_idx=i))

    # プロセスの開始
    #process_gui.start()
    process_field.start()
    process_ipad.start()
    process_obj_recog.start()
    process_wifi_send[0].start() # 赤
    process_wifi_recv[0].start()
    process_wifi_send[1].start() # 青
    process_wifi_recv[1].start()
    process_wifi_send[2].start() # 緑
    process_wifi_recv[2].start()
    process_wifi_send[3].start() # 黄
    process_wifi_recv[3].start()
    
    # プロセスの終了
    while not share_resouce._gui_close_event.is_set():
        pass

    #process_gui._gui_process.terminate()
    #process_gui._gui_process.join()
    process_field.process_field.terminate()
    process_field.process_field.join()   
    process_ipad._process_ipad.terminate()
    process_ipad._process_ipad.join() 
    process_obj_recog._process_wifi.terminate()
    process_obj_recog._process_wifi.join()
    for i in range(NUM_MOUSE):
        process_wifi_send[i].close()
        process_wifi_send[i]._process_wifi.terminate()
        process_wifi_send[i]._process_wifi.join()
        process_wifi_recv[i].close()
        process_wifi_recv[i]._process_wifi.terminate()
        process_wifi_recv[i]._process_wifi.join()    

if __name__ == "__main__":
    main()