
import sys
import time
import multiprocessing as mp

from ShareResouce import ShareResouce
from ProcessGUI import ProcessGUI
from ProcessWiFi import ProcessWiFi
from ProcessField import ProcessField


def main():
    state_manager_process = ShareResouce()
    process_gui     = ProcessGUI(state_and_data=state_manager_process)
    process_wifi    = ProcessWiFi(state_and_data=state_manager_process)
    process_field   = ProcessField(state_and_data=state_manager_process)

    process_gui.start()
    process_wifi.start()
    process_field.start()

    while not state_manager_process._all_exit_event.is_set():
        pass

    count_down_process._count_down_process.terminate()
    count_down_process._count_down_process.join()
    gui_process._gui_process.terminate()
    gui_process._gui_process.join()    

if __name__ == "__main__":
    main()