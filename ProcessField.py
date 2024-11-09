

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

# ===== 設定変数
SELECT_FIELD_SIZE = FIELD_SIZE_IS_8X8
SELECT_MODE = MODE_2
SELECT_SERIAL_SPEED = 1843200    #7372800 # 1843200 # 921600  # 115200    
interval = 1.0 # 0.03333

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
        self._field_process = mp.Process(target=self.setup, name="FieldProcess")
    
    def setup(self):
        print("ProcessField.setup")
        display_map = [[0 for j in range(DATA_LEN)] for i in range(LED_NUM)]
        display_map.append([0x01])      #最終のエンドフラグは書き込み済み

        color = RED

        ser = serial.Serial('/dev/cu.usbmodem1201', SELECT_SERIAL_SPEED)  # シリアルポートとボーレートの設定
        led_no=0

        while True:
            start_time = time.time()

            if SELECT_MODE == MODE_0:
                for i in range(LED_NUM):
                    for j in range(DATA_LEN):
                        display_map[i][j] = 0

                if color < COLOR_MAX_NUM:
                    color += 1
                else:
                    color = BLUE

                if display_map[0][color] == LED_BRIGHTNESS_MAX:
                    for i in range(LED_NUM):
                        display_map[i][color] = LED_BRIGHTNESS_MIN
                else:
                    for i in range(LED_NUM):
                        display_map[i][color] = LED_BRIGHTNESS_MAX

                ser.write(bytes(list(itertools.chain.from_iterable(display_map))))

                # print(display_map)
                # print(bytes(list(itertools.chain.from_iterable(display_map))))
                # print(len(display_map))
                
            elif SELECT_MODE == MODE_1:
                color = BLUE

                if display_map[led_no][color] == LED_BRIGHTNESS_MAX:
                    display_map[led_no][color] = LED_BRIGHTNESS_MIN
                else:
                    display_map[led_no][color] = LED_BRIGHTNESS_MAX

                ser.write(bytes(list(itertools.chain.from_iterable(display_map))))

                led_no += 1
                if led_no > LED_NUM-1:
                    led_no = 0
                
            elif SELECT_MODE == MODE_2:
                if display_map[led_no][color] == LED_BRIGHTNESS_MAX:
                    display_map[led_no][color] = LED_BRIGHTNESS_MIN
                else:
                    display_map[led_no][color] = LED_BRIGHTNESS_MAX

                ser.write(bytes(list(itertools.chain.from_iterable(display_map))))

                led_no += 1
                if led_no > LED_NUM-1:
                    led_no = 0
                
                if color < COLOR_MAX_NUM:
                    color += 1
                else:
                    color = BLUE

            elapsed_time = time.time() - start_time
            sleep_time = interval - elapsed_time

            if sleep_time > 0:
                time.sleep(sleep_time)

            # reply = ser.read_all()
            # print(reply)

    
    def start(self):
        self._field_process.start()