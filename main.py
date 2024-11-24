
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

def main():
    # プロセス間共有リソースの生成
    share_resouce = ShareResouce()

    # プロセスの生成
    process_field   = ProcessField(share_resouce=share_resouce) # フィールド描画プロセス
    #process_gui     = ProcessGUI(share_resouce=share_resouce)   # GUIプロセス
    process_ipad    = ProcessiPad(share_resouce=share_resouce)  # iPadプロセス

    #process_wifi = [] # マウスWiFiプロセス
    #process_wifi.append(ProcessWiFi(share_resouce=share_resouce, mouse_idx=0))
    #process_wifi.append(ProcessWiFi(share_resouce=share_resouce, mouse_idx=1))
    #process_wifi.append(ProcessWiFi(share_resouce=share_resouce, mouse_idx=2))
    process_wifi_send = [] # マウスWiFiプロセス
    process_wifi_send.append(ProcessWiFiRecv(share_resouce=share_resouce, mouse_idx=0))
    process_wifi_send.append(ProcessWiFiRecv(share_resouce=share_resouce, mouse_idx=1))
    process_wifi_send.append(ProcessWiFiRecv(share_resouce=share_resouce, mouse_idx=2))
    process_wifi_recv = [] # マウスWiFiプロセス
    process_wifi_recv.append(ProcessWiFiSend(share_resouce=share_resouce, mouse_idx=0))
    process_wifi_recv.append(ProcessWiFiSend(share_resouce=share_resouce, mouse_idx=1))
    process_wifi_recv.append(ProcessWiFiSend(share_resouce=share_resouce, mouse_idx=2))

    # プロセスの開始
    #process_gui.start()
    process_field.start()
    process_ipad.start()
    process_wifi_send[0].start()
    process_wifi_send[1].start()
    process_wifi_send[2].start()
    process_wifi_recv[0].start()
    process_wifi_recv[1].start()
    process_wifi_recv[2].start()
    
    # プロセスの終了
    while not share_resouce._gui_close_event.is_set():
        pass

    #process_gui._gui_process.terminate()
    #process_gui._gui_process.join()
    process_field.process_field.terminate()
    process_field.process_field.join()   
    process_ipad._process_ipad.terminate()
    process_ipad._process_ipad.join() 
    for i in range(NUM_MOUSE):
        process_wifi_send[i].close()
        process_wifi_send[i]._process_wifi.terminate()
        process_wifi_send[i]._process_wifi.join()
        process_wifi_recv[i].close()
        process_wifi_recv[i]._process_wifi.terminate()
        process_wifi_recv[i]._process_wifi.join()    

if __name__ == "__main__":
    main()