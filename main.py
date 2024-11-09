
import sys
import time
import multiprocessing as mp

from ShareResouce import ShareResouce, NUM_MOUSE
from ProcessGUI import ProcessGUI
from ProcessWiFi import ProcessWiFi

def main():
    share_resouce = ShareResouce()
    process_gui     = ProcessGUI(share_resouce=share_resouce)
    #process_field   = ProcessField(share_resouce=share_resouce)

    process_wifi = []
    for i in range(NUM_MOUSE):
        process_wifi.append(ProcessWiFi(share_resouce=share_resouce, mouse_idx=i))

    process_gui.start()
    for i in range(NUM_MOUSE):
        process_wifi[i].start()
    
    #process_field.start()

    while not share_resouce._gui_close_event.is_set():
        pass

    process_gui._gui_process.terminate()
    process_gui._gui_process.join()
    for i in range(NUM_MOUSE):
        process_wifi[i].close()
        process_wifi[i]._process_wifi.terminate()
        process_wifi[i]._process_wifi.join()    
    #process_field._process_field.terminate()
    #process_field._process_field.join()    

if __name__ == "__main__":
    main()