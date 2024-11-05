
import sys
import time
import multiprocessing as mp
from PyQt5.QtWidgets import QApplication,QGridLayout,QLabel,QPushButton,QMainWindow
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget

from ShareResouce import ShareResouce

class GUIProcess():
    def __init__(self, share_resouce:ShareResouce) -> None:
        self.share_resouce = share_resouce
        self._gui_process = mp.Process(target=self.setup, name="GUIProcess")

    def setup(self):
        self.app = QApplication(sys.argv)
        self.window = MainWindow(self.share_resouce)
        self.window.closeEvent = lambda _: self.close()
        self.window.show()
        self.app.processEvents()
        while True:
            if self.share_resouce._gui_update_event.is_set():
                self.window.update_timer()
                self.share_resouce._gui_update_event.clear
            self.app.processEvents()
        
    def start(self):
        self._gui_process.start()

    def close(self):
        self.share_resouce._gui_close_event.set()

class MainWindow(QMainWindow):
    def __init__(self,share_resouce:ShareResouce) -> None:
        super().__init__()
        self.share_resouce = share_resouce
        self.setup_gui()

    def setup_gui(self):
        # GUIのタイトル
        self.setWindowTitle("Qt CountDownTimer")

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        layout = QGridLayout(central_widget)

        self.time_label = QLabel(self.make_display_time())
        self.time_label.setAlignment(Qt.AlignCenter)  
        layout.addWidget(self.time_label,0,0)

        start_count_down_button_widget = QPushButton("Start",self)
        start_count_down_button_widget.clicked.connect(self.start_count_down)
        layout.addWidget(start_count_down_button_widget,1,0)

    def update_timer(self):
        self.time_label.setText(self.make_display_time())

    def start_count_down(self):
        self.share_resouce.count_down_time.value = TIMER_DUARATION
        self.share_resouce._count_down_exec_event.set()

    def make_display_time(self):
        return f'{self.share_resouce.count_down_time.value:>5.3f}'
