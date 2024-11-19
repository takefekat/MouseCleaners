
import sys
import time
import multiprocessing as mp
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QHBoxLayout, QVBoxLayout, QPushButton, QMainWindow, QGridLayout
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPainter, QColor, QFont
from datetime import datetime

from ShareResouce import ShareResouce, NUM_MOUSE

WHITE = 0
RED = 1
BLUE = 2
GREEN = 3
YELLOW = 4
BLACK = 5

PATH_PATTERN_INV = 0  # 無効
PATH_PATTERN1 = 1     # 2台 外周から螺旋で中心へ
PATH_PATTERN2 = 2     # 1台 全部塗る 
#PATH_PATTERN3 = 3     # 4台 外周から中心へ
PATH_PATTERN_MAX = 3  # パスパターンの最大値

# メインプロセス
class ProcessGUI():
    def __init__(self, share_resouce:ShareResouce) -> None:
        print("ProcessGUI.__init__")
        self.share_resouce = share_resouce
        self._gui_process = mp.Process(target=self.setup, name="ProcessGUI")

    # GUIの設定処理(プロセス開始時に呼び出される)
    def setup(self):
        print("ProcessGUI.setup")
        self.app = QApplication(sys.argv)
        self.window = MainWindow(self.share_resouce)
        self.window.closeEvent = lambda _: self.close()
        self.window.show()
        self.app.processEvents()
        while True:
            # TimerWidgetからのトリガで一定周期でGUIを更新
            if self.share_resouce._gui_update_event.is_set():
                self.share_resouce._gui_update_event.clear()
                self.window.update_gui_map()
            self.app.processEvents()
        
    # GUIの開始処理(プロセスの開始)
    def start(self):
        print("ProcessGUI.start")
        self._gui_process.start()

    # GUIの終了処理
    def close(self):
        print("ProcessGUI.close")
        self.share_resouce._gui_close_event.set()

# メインウィンドウ
class MainWindow(QMainWindow):
    def __init__(self, share_resouce:ShareResouce) -> None:
        print("MainWindow.__init__")
        super().__init__()
        self.share_resouce = share_resouce

        self.path_pattern = PATH_PATTERN_INV
        
        # GUIのタイトル
        self.setWindowTitle("⚡️電光石火⭐︎ぴかぴかクリーナーズ")

         # 中央ウィジェットを設定
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # ウィジェット
        self.map_widget = MapWidget(share_resouce)     # 迷路ウィジェット
        timer_widget = TimerWidget(share_resouce)
        start_button = QPushButton("Start")
        stop_button = QPushButton("Stop")

        # ボタンクリック時の処理を設定
        start_button.clicked.connect(self.start_run)
        stop_button.clicked.connect(self.stop_run)

        # ウィジェットをレイアウトに配置
        layout = QHBoxLayout()
        central_widget.setLayout(layout)
        # 左側にマップウィジェット
        layout.addWidget(self.map_widget)      # 左にマップウィジェット

        # 右側にタイマーウィジェット、ボタンなどを配置
        layout_right = QVBoxLayout() 
        layout_right.addWidget(timer_widget)  # 右にタイマーラベル
        layout_right.addWidget(start_button)  # スタートボタン
        layout_right.addWidget(stop_button)   # ストップボタン
        layout.addLayout(layout_right)    # レイアウトを追加
    # スタートボタンが押されたときの処理
    def start_run(self):
        print("MainWindow.start_run")
        for i in range(NUM_MOUSE):
            self.share_resouce._start_event[i] = 1

        self.share_resouce._field_mode.value = 4 # 経路を時刻に応じて更新モード
        self.share_resouce._field_timer_count.value = 0 # 経路を時刻に応じて更新モード


    # ストップボタンが押されたときの処理
    def stop_run(self):
        print("MainWindow.stop_run")
        for i in range(NUM_MOUSE):
            self.share_resouce._stop_event[i] = 1

    # self.share_resouce._path の内容をマップウィジェットに反映
    def update_gui_map(self):
        print("MainWindow.update_gui_map")
        # 初期化
        for y in range(32):
            for x in range(32):
                self.map_widget.set_map(x, y, WHITE)
        # 障害物
        for x in range(32):
            self.map_widget.set_map(x, 0, BLACK)
            self.map_widget.set_map(x, 31, BLACK)
            self.map_widget.set_map(0, x, BLACK)
            self.map_widget.set_map(31, x, BLACK)

        # マウス1: 赤
        for index in range(len(self.share_resouce._path0) // 2):
            if self.share_resouce._path0[2 * index] == 255:
                break
            x = self.share_resouce._path0[2 * index]
            y = self.share_resouce._path0[2 * index + 1]
            self.map_widget.set_map(x, y, RED)
        # マウス2: 青
        for index in range(len(self.share_resouce._path1) // 2):
            if self.share_resouce._path1[2 * index] == 255:
                break
            x = self.share_resouce._path1[2 * index]
            y = self.share_resouce._path1[2 * index + 1]
            self.map_widget.set_map(x, y, BLUE)
        # マウス3: 緑
        for index in range(len(self.share_resouce._path2) // 2):
            if self.share_resouce._path2[2 * index] == 255:
                break
            x = self.share_resouce._path2[2 * index]
            y = self.share_resouce._path2[2 * index + 1]
            self.map_widget.set_map(x, y, GREEN)
        # マウス4: 黄色
        for index in range(len(self.share_resouce._path3) // 2):
            if self.share_resouce._path3[2 * index] == 255:
                break
            x = self.share_resouce._path3[2 * index]
            y = self.share_resouce._path3[2 * index + 1]
            self.map_widget.set_map(x, y, YELLOW)

        self.map_widget.update_map()


class MapWidget(QWidget):
    def __init__(self, share_resouce:ShareResouce) -> None:
        print("MapWidget.__init__")
        super().__init__()
        self.share_resouce = share_resouce
        self.map_data = [[0 for _ in range(32)] for _ in range(32)]  # 32x32のマップを0で初期化
        self.cell_size = 20  # 1セルのサイズ
        self.setFixedSize(len(self.map_data[0]) * self.cell_size, len(self.map_data) * self.cell_size)

    def paintEvent(self, event):
        print("MapWidget.paintEvent")
        painter = QPainter(self)

        # 32x32の配列を描画
        for y, row in enumerate(self.map_data):
            for x, cell in enumerate(row):
                if cell == WHITE:
                    painter.setBrush(QColor(255, 255, 255))  # 白
                elif cell == RED:
                    painter.setBrush(QColor(255, 0, 0))  # 赤
                elif cell == GREEN:
                    painter.setBrush(QColor(0, 255, 0)) # 緑
                elif cell == BLUE:
                    painter.setBrush(QColor(0, 0, 255)) # 青
                elif cell == YELLOW:
                    painter.setBrush(QColor(255, 255, 0)) # 黄
                else:
                    painter.setBrush(QColor(0, 0, 0))  # 黒
                painter.drawRect(x * self.cell_size, y * self.cell_size, self.cell_size, self.cell_size)

    def set_map(self, x, y, value):
        self.map_data[y][x] = value  # 任意の座標の値を更新
    
    def update_map(self):
        print("MapWidget.update_map")
        self.update()  # 再描画


class TimerWidget(QWidget):
    def __init__(self, share_resouce:ShareResouce) -> None:
        super().__init__()
        print("TimerWidget.__init__")
        self.share_resouce = share_resouce
        self.start_time = datetime.now()

        # ラベルを作成して初期化
        self.timer_label = QLabel("Time: 0s", self)

        # フォントサイズを大きく設定
        font = QFont("Arial", 20, QFont.Bold)  # フォントサイズ20、太字
        self.timer_label.setFont(font)
        self.setFixedSize(150,100)

    def timer_start(self, interval):
        print("TimerWidget.timer_start")

        # タイマーを設定
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer)  # タイムアウトごとにupdate_timerを呼び出す
        self.timer.start(1000)  # 1秒ごとに更新

    def update_timer(self):
        #print("TimerWidget.update_timer")
        # 経過時間を計算
        elapsed_time = (datetime.now() - self.start_time).total_seconds()
        # ラベルに経過時間を表示
        self.timer_label.setText(f"Time: {int(elapsed_time)}s")
