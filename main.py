
import sys
import time
import multiprocessing as mp

from ShareResouce import ShareResouce
from ProcessGUI import ProcessGUI

def main():
    share_resouce = ShareResouce()
    process_gui     = ProcessGUI(share_resouce=share_resouce)
    #process_field   = ProcessField(share_resouce=share_resouce)
    #process_wifi    = ProcessWiFi(share_resouce=share_resouce)

    process_gui.start()
    #process_wifi.start()
    #process_field.start()

    while not share_resouce._gui_close_event.is_set():
        pass

    process_gui._gui_process.terminate()
    process_gui._gui_process.join()
    #process_wifi._process_wifi.terminate()
    #process_wifi._process_wifi.join()    
    #process_field._process_field.terminate()
    #process_field._process_field.join()    

if __name__ == "__main__":
    main()