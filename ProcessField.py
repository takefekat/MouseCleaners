

import sys
import time
import multiprocessing as mp
from ShareResouce import ShareResouce, NUM_MOUSE
import serial
import itertools

# ===== 定義
FIELD_SIZE_IS_8X8 = 0
FIELD_SIZE_IS_32X32 = 1

DATA_LEN = 3
LED_BRIGHTNESS_MAX = 255
LED_BRIGHTNESS_MIN = 0

BLUE = 0
GREEN = 1
RED = 2
COLOR_MAX_NUM = 2

MODE_0 = 0
MODE_1 = 1
MODE_2 = 2
MODE_3 = 3
MODE_4 = 4

# ===== 設定変数
SELECT_FIELD_SIZE = FIELD_SIZE_IS_32X32
SELECT_SERIAL_SPEED = 1843200    #7372800 # 1843200 # 921600  # 115200    
interval = 0.03333

# ===== 設定によるパラメータ初期化
if SELECT_FIELD_SIZE == FIELD_SIZE_IS_8X8:
    LED_NUM_X = 8
    LED_NUM_Y = 8
elif SELECT_FIELD_SIZE == FIELD_SIZE_IS_32X32:
    LED_NUM_X = 32
    LED_NUM_Y = 32

LED_NUM = LED_NUM_X * LED_NUM_Y


class ProcessField():
    def __init__(self, share_resouce:ShareResouce) -> None:
        print("ProcessField.__init__")
        self.share_resouce = share_resouce
        self.process_field = mp.Process(target=self.setup, name="FieldProcess")
        self.share_resouce._field_mode.value = MODE_2

    def setup(self):
        print("ProcessField.setup")
        self.display_map = [[0 for j in range(DATA_LEN)] for i in range(LED_NUM)]
        self.display_map.append([0x01])      #最終のエンドフラグは書き込み済み

        color = RED

        try:
            self.ser = serial.Serial('/dev/tty.usbmodem2101', SELECT_SERIAL_SPEED)  # シリアルポートとボーレートの設定
        except:
            print("[Warning] Serial port can't open: /dev/cu.usbmodem2101")
            pass # シリアルポートが開けない場合は無視(debug用)

        led_no=0

        while True:
            start_time = time.time()

            if self.share_resouce._field_mode.value == MODE_0:
                for i in range(LED_NUM):
                    for j in range(DATA_LEN):
                        self.display_map[i][j] = 0

                if color < COLOR_MAX_NUM:
                    color += 1
                else:
                    color = BLUE

                if self.display_map[0][color] == LED_BRIGHTNESS_MAX:
                    for i in range(LED_NUM):
                        self.display_map[i][color] = LED_BRIGHTNESS_MIN
                else:
                    for i in range(LED_NUM):
                        self.display_map[i][color] = LED_BRIGHTNESS_MAX

                self.serial_send()

                # print(self.display_map)
                # print(bytes(list(itertools.chain.from_iterable(self.display_map))))
                # print(len(self.display_map))
                
            elif self.share_resouce._field_mode.value == MODE_1:
                color = BLUE

                if self.display_map[led_no][color] == LED_BRIGHTNESS_MAX:
                    self.display_map[led_no][color] = LED_BRIGHTNESS_MIN
                else:
                    self.display_map[led_no][color] = LED_BRIGHTNESS_MAX

                self.serial_send()

                led_no += 1
                if led_no > LED_NUM-1:
                    led_no = 0
                
            elif self.share_resouce._field_mode.value == MODE_2:
                if self.display_map[led_no][color] == LED_BRIGHTNESS_MAX:
                    self.display_map[led_no][color] = LED_BRIGHTNESS_MIN
                else:
                    self.display_map[led_no][color] = LED_BRIGHTNESS_MAX

                self.serial_send()

                led_no += 1
                if led_no > LED_NUM-1:
                    led_no = 0
                
                if color < COLOR_MAX_NUM:
                    color += 1
                else:
                    color = BLUE
            
            # 経路全体を表示
            elif self.share_resouce._field_mode.value == MODE_3:
                # 全部白
                for i in range(LED_NUM):
                    for j in range(DATA_LEN):
                        self.display_map[i][j] = LED_BRIGHTNESS_MIN
                for i in range(1024):
                    # マウス1: 赤
                    x = self.share_resouce._path0[2 * i]
                    y = self.share_resouce._path0[2 * i + 1]
                    if x < 32 and y < 32:
                        self.display_map[x * 32 + y][RED] = LED_BRIGHTNESS_MAX
                    # マウス2: 青
                    x = self.share_resouce._path1[2 * i]
                    y = self.share_resouce._path1[2 * i + 1]
                    if x < 32 and y < 32:
                        self.display_map[x * 32 + y][BLUE] = LED_BRIGHTNESS_MAX
                    # マウス3: 緑
                    x = self.share_resouce._path2[2 * i]
                    y = self.share_resouce._path2[2 * i + 1]
                    if x < 32 and y < 32:
                        self.display_map[x * 32 + y][GREEN] = LED_BRIGHTNESS_MAX

                self.serial_send()

            # 経路を時刻に合わせて順に表示
            elif self.share_resouce._field_mode.value == MODE_4:
                # 全部白
                for i in range(LED_NUM):
                    for j in range(DATA_LEN):
                        self.display_map[i][j] = LED_BRIGHTNESS_MIN

                # 表示する経路の長さ
                self.share_resouce._field_timer_count.value += 1
                display_path_len = self.share_resouce._field_timer_count.value
                #print(display_path_len)

                # マウス1: 赤
                #print("path0:", end=" ")
                for i in range(min(display_path_len, LED_NUM)):
                    x = self.share_resouce._path0[2 * i]
                    y = self.share_resouce._path0[2 * i + 1]
                    if x < 32 and y < 32:
                        #print("(", x, y, ")", end=" ")
                        self.display_map[x * 32 + y][RED] = LED_BRIGHTNESS_MAX
                #print("")
                # マウス2: 青
                for i in range(min(display_path_len, LED_NUM)):
                    x = self.share_resouce._path1[2 * i]
                    y = self.share_resouce._path1[2 * i + 1]
                    if x < 32 and y < 32:
                        self.display_map[x * 32 + y][BLUE] = LED_BRIGHTNESS_MAX
                # マウス3: 緑
                for i in range(min(display_path_len, LED_NUM)):
                    x = self.share_resouce._path2[2 * i]
                    y = self.share_resouce._path2[2 * i + 1]
                    if x < 32 and y < 32:
                        self.display_map[x * 32 + y][GREEN] = LED_BRIGHTNESS_MAX

                self.serial_send()

                
            elapsed_time = time.time() - start_time
            sleep_time = interval - elapsed_time

            if sleep_time > 0:
                time.sleep(sleep_time)

            # reply = ser.read_all()
            # print(reply)

    
    def start(self):
        self.process_field.start()

    def serial_send(self):
        try:
            self.ser.write(bytes(list(itertools.chain.from_iterable(self.display_map))))
        except:
            pass