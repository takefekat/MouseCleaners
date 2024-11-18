
import sys
import time
import multiprocessing as mp

from ShareResouce import ShareResouce, NUM_MOUSE
from ProcessGUI import ProcessGUI
from ProcessWiFi import ProcessWiFi
from ProcessField import ProcessField

def main():
    # プロセス間共有リソースの生成
    share_resouce = ShareResouce()

    # プロセスの生成
    process_field   = ProcessField(share_resouce=share_resouce) # フィールド描画プロセス
    process_gui     = ProcessGUI(share_resouce=share_resouce)   # GUIプロセス

    process_wifi = [] # マウスWiFiプロセス
    for i in range(NUM_MOUSE):
        process_wifi.append(ProcessWiFi(share_resouce=share_resouce, mouse_idx=i))

    # プロセスの開始
    process_gui.start()
    process_field.start()
    for i in range(NUM_MOUSE):
        process_wifi[i].start()
    
    # プロセスの終了
    while not share_resouce._gui_close_event.is_set():
        pass

    process_gui._gui_process.terminate()
    process_gui._gui_process.join()
    process_field.process_field.terminate()
    process_field.process_field.join()    
    for i in range(NUM_MOUSE):
        process_wifi[i].close()
        process_wifi[i]._process_wifi.terminate()
        process_wifi[i]._process_wifi.join()    

if __name__ == "__main__":
    main()