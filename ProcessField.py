

import sys
import time
import multiprocessing as mp
from ShareResouce import ShareResouce


class ProcessField():
    def __init__(self, state_and_data:StateManagerProcess) -> None:
        self.state_and_data = state_and_data
        self._field_process = mp.Process(target=self.setup, name="FieldProcess")
    
    def setup(self):
        while True:
            if self.state_and_data._field_exec_event.is_set():
                self.state_and_data._field_exec_event.clear()
                # Fieldの処理
                time.sleep(1)
                self.state_and_data._field_update_event.set()
    
    def start(self):
        self._field_process.start()