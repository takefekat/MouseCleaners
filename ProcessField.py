

import sys
import time
import multiprocessing as mp
from ShareResouce import ShareResouce, NUM_MOUSE
import serial
import itertools
import cv2
import os

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
MODE_3 = 3 # 経路&障害物を表示
MODE_4 = 4 # 往路 赤-->ピンク のように通過した経路を薄い色にする
MODE_5 = 5 # 復路 ピンク-->赤 のように通過した経路を元の色にする
MODE_6 = 6 # 全マウスゴール到達 パフォーマンス表示
MODE_7 = 7 # ぴかぴかクリーナーズ
MODE_8 = 8 # 障害物表示モード

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

def read_image(dir, image_filename):
    # 画像ファイルのパスを作成
    image_path = os.path.join(dir, image_filename)
    
    # 画像をカラーで読み込む
    image = cv2.imread(image_path, cv2.IMREAD_COLOR)  # カラー画像として読み込む
    
    # 画像が読み込めたか確認
    if image is  None:
        print(f"Failed to load {image_filename}")
        return [[0] * DATA_LEN for _ in range(LED_NUM)]

    image = image.reshape(-1, 3)

    # LED_NUM_X * DATA_LEN の配列に変換
    ret_image = [[0] * DATA_LEN for _ in range(LED_NUM)]
    for x in range(32):
        for y in range(32):
            in_led_idx = x + (y * 32)
            out_led_idx = (31- x) + (y * 32) # 上下反転
            for rgb in range(DATA_LEN):
                ret_image[out_led_idx][rgb] = image[in_led_idx][rgb]
    return ret_image

class ProcessField():
    def __init__(self, share_resouce:ShareResouce) -> None:
        print("ProcessField.__init__")
        self.share_resouce = share_resouce
        self.process_field = mp.Process(target=self.setup, name="FieldProcess")
        self.share_resouce._field_mode.value = MODE_7 # MODE 7: ホーム画面 ぴかぴかクリーナーズ

        image_directory = 'img'
        #image_files = ['GOAL_1.png', 'GOAL_2.png', 'GOAL_3.png', 'GOAL_4.png', 'GOAL_5.png']
        image_files = ['1_goal.png', '2_goal.png', '3_goal.png', '4_goal.png', '5_goal.png', '6_goal.png', '7_goal.png', '8_goal.png', '9_goal.png', '10_goal.png']
        pikapika_files = ['pikapika.png']

        self.images = [ read_image(image_directory, image_filename) for image_filename in image_files ]
        self.pika_images = [ read_image(image_directory, image_filename) for image_filename in pikapika_files ]

    def setup(self):
        print("ProcessField.setup")
        self.display_map = [[0 for j in range(DATA_LEN)] for i in range(LED_NUM)]
        self.display_map.append([0x01])      #最終のエンドフラグは書き込み済み

        color = RED
        mode_cnt = 0

        try:
            self.ser = serial.Serial('/dev/tty.usbmodem2201', SELECT_SERIAL_SPEED)  # シリアルポートとボーレートの設定
        except:
            print("[Warning] Serial port can't open. ls /dev/tty.*")
            pass # シリアルポートが開けない場合は無視(debug用)

        led_no=0

        while True:
            start_time = time.time()

            ################################
            # MODE 0: やばいやつ
            ################################
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
                
            ################################
            # MODE 1: 青が順に点灯していく
            ################################
            elif self.share_resouce._field_mode.value == MODE_1:
                chg_img_interval = 15 # 約0.5s
                goal_idx = (led_no // 10) % len(self.images)
                for i in range(LED_NUM):
                    for j in range(DATA_LEN):
                        self.display_map[i][j] = self.images[goal_idx][i][j]

                self.serial_send()

                led_no += 1
                
            ################################
            # MODE 2: 赤、緑、青が順に点灯していく
            ################################
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
            
            #########################################################
            # MODE 7: ホーム画面 ぴかぴかクリーナーズ
            #########################################################
            elif self.share_resouce._field_mode.value == MODE_7:

                chg_img_interval = 15 # 約0.5s
                goal_idx = (mode_cnt // 15) % len(self.pika_images)
                for i in range(LED_NUM):
                    for j in range(DATA_LEN):
                        self.display_map[i][j] = self.pika_images[goal_idx][i][j]

                self.serial_send()
                mode_cnt += 1
                if mode_cnt >= 1e6:
                    mode_cnt = 0

            #########################################################
            # MODE 8: 障害物表示モード
            #########################################################
            elif self.share_resouce._field_mode.value == MODE_8:
                # 初期化: 黒
                for i in range(LED_NUM):
                    for j in range(DATA_LEN):
                        self.display_map[i][j] = LED_BRIGHTNESS_MIN
                
                # 障害物: 白
                for i in range(1024):
                    x = self.share_resouce._field_obj[2 * i]
                    y = self.share_resouce._field_obj[2 * i + 1]
                    if x >= 16 or y >= 16:
                        break # 障害物おわり
                    self.set_4led_brightness(15 - x, 15 - y, LED_BRIGHTNESS_MAX, LED_BRIGHTNESS_MAX, LED_BRIGHTNESS_MAX) # 白
                
                # マウス初期値
                self.set_4led_brightness(0, 0, LED_BRIGHTNESS_MIN, LED_BRIGHTNESS_MAX, LED_BRIGHTNESS_MIN) # 緑
                self.set_4led_brightness(0, 15, LED_BRIGHTNESS_MAX, LED_BRIGHTNESS_MAX, LED_BRIGHTNESS_MIN) # 黄
                self.set_4led_brightness(15, 0, LED_BRIGHTNESS_MAX, LED_BRIGHTNESS_MIN, LED_BRIGHTNESS_MIN) # 赤
                self.set_4led_brightness(15, 15, LED_BRIGHTNESS_MIN, LED_BRIGHTNESS_MIN, LED_BRIGHTNESS_MAX) # 青
                self.set_4led_brightness(0, 1, LED_BRIGHTNESS_MIN, LED_BRIGHTNESS_MAX, LED_BRIGHTNESS_MIN) # 緑
                self.set_4led_brightness(0, 14, LED_BRIGHTNESS_MAX, LED_BRIGHTNESS_MAX, LED_BRIGHTNESS_MIN) # 黄
                self.set_4led_brightness(15, 1, LED_BRIGHTNESS_MAX, LED_BRIGHTNESS_MIN, LED_BRIGHTNESS_MIN) # 赤
                self.set_4led_brightness(15, 14, LED_BRIGHTNESS_MIN, LED_BRIGHTNESS_MIN, LED_BRIGHTNESS_MAX) # 青
                self.set_4led_brightness(1, 0, LED_BRIGHTNESS_MIN, LED_BRIGHTNESS_MAX, LED_BRIGHTNESS_MIN) # 緑
                self.set_4led_brightness(1, 15, LED_BRIGHTNESS_MAX, LED_BRIGHTNESS_MAX, LED_BRIGHTNESS_MIN) # 黄
                self.set_4led_brightness(14, 0, LED_BRIGHTNESS_MAX, LED_BRIGHTNESS_MIN, LED_BRIGHTNESS_MIN) # 赤
                self.set_4led_brightness(14, 15, LED_BRIGHTNESS_MIN, LED_BRIGHTNESS_MIN, LED_BRIGHTNESS_MAX) # 青
                self.set_4led_brightness(1, 1, LED_BRIGHTNESS_MIN, LED_BRIGHTNESS_MAX, LED_BRIGHTNESS_MIN) # 緑
                self.set_4led_brightness(1, 14, LED_BRIGHTNESS_MAX, LED_BRIGHTNESS_MAX, LED_BRIGHTNESS_MIN) # 黄
                self.set_4led_brightness(14, 1, LED_BRIGHTNESS_MAX, LED_BRIGHTNESS_MIN, LED_BRIGHTNESS_MIN) # 赤
                self.set_4led_brightness(14, 14, LED_BRIGHTNESS_MIN, LED_BRIGHTNESS_MIN, LED_BRIGHTNESS_MAX) # 青
                
                self.serial_send()

            ################################
            # MODE 3: 経路全体を表示
            ################################
            elif self.share_resouce._field_mode.value == MODE_3:
                # 初期化: 黒
                for i in range(LED_NUM):
                    for j in range(DATA_LEN):
                        self.display_map[i][j] = LED_BRIGHTNESS_MIN
                
                # 障害物: 白
                for i in range(1024):
                    x = self.share_resouce._field_obj[2 * i]
                    y = self.share_resouce._field_obj[2 * i + 1]
                    if x >= 16 or y >= 16:
                        break # 障害物おわり
                    self.set_4led_brightness(15 - x, 15 - y, LED_BRIGHTNESS_MAX, LED_BRIGHTNESS_MAX, LED_BRIGHTNESS_MAX) # 白

                # マウス1: 赤
                for i in range(1024):
                    x = self.share_resouce._path0[2 * i]
                    y = self.share_resouce._path0[2 * i + 1]
                    if x >= 16 and y >= 16:
                        break # 経路おわり
                    self.set_4led_brightness(15 - x, 15 - y, LED_BRIGHTNESS_MAX, LED_BRIGHTNESS_MIN, LED_BRIGHTNESS_MIN) # 赤

                # マウス2: 青
                for i in range(1024):
                    x = self.share_resouce._path1[2 * i]
                    y = self.share_resouce._path1[2 * i + 1]
                    if x >= 16 and y >= 16:
                        break # 経路おわり
                    self.set_4led_brightness(15 - x, 15 - y, LED_BRIGHTNESS_MIN, LED_BRIGHTNESS_MIN, LED_BRIGHTNESS_MAX) # 青

                # マウス3: 緑
                for i in range(1024):
                    x = self.share_resouce._path2[2 * i]
                    y = self.share_resouce._path2[2 * i + 1]
                    if x >= 16 and y >= 16:
                        break # 経路おわり
                    self.set_4led_brightness(15 - x, 15 - y, LED_BRIGHTNESS_MIN, LED_BRIGHTNESS_MAX, LED_BRIGHTNESS_MIN) # 緑

                # マウス4: 黄
                for i in range(1024):
                    x = self.share_resouce._path3[2 * i]
                    y = self.share_resouce._path3[2 * i + 1]
                    if x >= 16 and y >= 16:
                        break # 経路おわり
                    self.set_4led_brightness(15 - x, 15 - y, LED_BRIGHTNESS_MAX, LED_BRIGHTNESS_MAX, LED_BRIGHTNESS_MIN) # 黄
                self.serial_send()

            #########################################################
            # MODE 4: 往路 赤-->ピンク のように通過した経路を薄い色にする
            #########################################################
            elif self.share_resouce._field_mode.value == MODE_4:
                # 初期化: 黒
                for i in range(LED_NUM):
                    for j in range(DATA_LEN):
                        self.display_map[i][j] = LED_BRIGHTNESS_MIN

                # 障害物: 白
                for i in range(1024):
                    x = self.share_resouce._field_obj[2 * i]
                    y = self.share_resouce._field_obj[2 * i + 1]
                    if x >= 16 or y >= 16: # 障害物おわり
                        break
                    self.set_4led_brightness(15 - x, 15 - y, LED_BRIGHTNESS_MAX, LED_BRIGHTNESS_MAX, LED_BRIGHTNESS_MAX) # 白

                # マウス1: 赤(255,0,0) ピンク(255,120,120)
                set_r = LED_BRIGHTNESS_MAX
                set_g = 120
                set_b = 120
                for i in range(1024):
                    x = self.share_resouce._path0[2 * i]
                    y = self.share_resouce._path0[2 * i + 1]
                    if x >= 16 or y >= 16: # 経路おわり
                        break

                    self.set_4led_brightness(15 - x, 15 - y, set_r, set_g, set_b)

                    # 経路の中でマウスの位置を探す
                    if self.share_resouce._mouse0_pos[0] == x and self.share_resouce._mouse0_pos[1] == y: # マウスの位置
                        set_r = LED_BRIGHTNESS_MAX
                        set_g = LED_BRIGHTNESS_MIN
                        set_b = LED_BRIGHTNESS_MIN
                        
                        if self.share_resouce._path0[2 * (i + 1)] == 255 or self.share_resouce._path0[2 * (i + 1) + 1] == 255: 
                            self.share_resouce._field_mode5_is_goal[0] = 1  # ゴール到達フラグを立てる

                # マウス2: 青(0,0,255) 薄い青(120,255,255)
                set_r = 120
                set_g = LED_BRIGHTNESS_MAX
                set_b = LED_BRIGHTNESS_MAX
                for i in range(1024):
                    x = self.share_resouce._path1[2 * i]
                    y = self.share_resouce._path1[2 * i + 1]
                    if x >= 16 or y >= 16: # 経路おわり
                        break

                    self.set_4led_brightness(15 - x, 15 - y, set_r, set_g, set_b)

                    # 経路の中でマウスの位置を探す
                    if self.share_resouce._mouse1_pos[0] == x and self.share_resouce._mouse1_pos[1] == y: # マウスの位置
                        set_r = LED_BRIGHTNESS_MIN
                        set_g = LED_BRIGHTNESS_MIN
                        set_b = LED_BRIGHTNESS_MAX

                        if self.share_resouce._path1[2 * (i + 1)] == 255 or self.share_resouce._path1[2 * (i + 1) + 1] == 255: 
                            self.share_resouce._field_mode5_is_goal[1] = 1  # ゴール到達フラグを立てる

                # マウス3: 緑(0,255,0) うすい緑(120,255,120)
                set_r = 120
                set_g = LED_BRIGHTNESS_MAX
                set_b = 120
                for i in range(1024):
                    x = self.share_resouce._path2[2 * i]
                    y = self.share_resouce._path2[2 * i + 1]
                    if x >= 16 or y >= 16: # 経路おわり
                        break

                    self.set_4led_brightness(15 - x, 15 - y, set_r, set_g, set_b)

                    # 経路の中でマウスの位置を探す
                    if self.share_resouce._mouse2_pos[0] == x and self.share_resouce._mouse2_pos[1] == y: # マウスの位置
                        set_r = LED_BRIGHTNESS_MIN
                        set_g = LED_BRIGHTNESS_MAX
                        set_b = LED_BRIGHTNESS_MIN

                        if self.share_resouce._path2[2 * (i + 1)] == 255 or self.share_resouce._path2[2 * (i + 1) + 1] == 255: 
                            self.share_resouce._field_mode5_is_goal[2] = 1  # ゴール到達フラグを立てる

                # マウス4: 黄(255,255,0) オレンジ(255,170,0)
                set_r = LED_BRIGHTNESS_MAX
                set_g = 170
                set_b = LED_BRIGHTNESS_MIN
                for i in range(1024):
                    x = self.share_resouce._path3[2 * i]
                    y = self.share_resouce._path3[2 * i + 1]
                    if x >= 16 or y >= 16: # 経路おわり
                        break

                    self.set_4led_brightness(15 - x, 15 - y, set_r, set_g, set_b)

                    # 経路の中でマウスの位置を探す
                    if self.share_resouce._mouse3_pos[0] == x and self.share_resouce._mouse3_pos[1] == y: # マウスの位置
                        set_r = LED_BRIGHTNESS_MAX
                        set_g = LED_BRIGHTNESS_MAX
                        set_b = LED_BRIGHTNESS_MIN

                        if self.share_resouce._path3[2 * (i + 1)] == 255 or self.share_resouce._path3[2 * (i + 1) + 1] == 255: 
                            self.share_resouce._field_mode5_is_goal[3] = 1  # ゴール到達フラグを立てる

                self.serial_send()

                # 全マウスがゴールに到達した場合、MODE 6 パフォーマンス表示に移行
                is_all_goal = True
                print("goal mouce:")
                for i in range(NUM_MOUSE):
                    print(i, ': ', self.share_resouce._connected_mice[i], ' ', self.share_resouce._field_mode5_is_goal[i], " --> ", end="")
                    print((self.share_resouce._connected_mice[i] == 0 or self.share_resouce._field_mode5_is_goal[i] == 1))
                    if self.share_resouce._connected_mice[i] == 1 and self.share_resouce._field_mode5_is_goal[i] == 0:
                        is_all_goal = False
                        break
                print("")
                if is_all_goal:
                    self.share_resouce._field_mode.value = MODE_6
                    self.mode6_timer = 0


            #########################################################
            # MODE 6: 全マウスゴール到達 パフォーマンス表示
            #########################################################
            elif self.share_resouce._field_mode.value == MODE_6:
                self.mode6_timer += 1
                #print('mode6_timer:', self.mode6_timer)
                
                chg_img_interval = 15 # 約0.5s
                goal_idx = (self.mode6_timer // 15) % len(self.images)
                for i in range(LED_NUM):
                    for j in range(DATA_LEN):
                        self.display_map[i][j] = self.images[goal_idx][i][j]

                self.serial_send()
                if self.mode6_timer > 100: # 3.3秒
                    for i in range(NUM_MOUSE):
                        self.share_resouce._return_event[i] = 1
                        #self.share_resouce._stop_event[i] = 1 # debug
                    self.share_resouce._field_mode.value = MODE_5

            #########################################################
            # MODE 5: 復路 赤-->ピンク のように通過した経路を薄い色にする
            #########################################################
            elif  self.share_resouce._field_mode.value == MODE_5:
                # 初期化: 黒
                for i in range(LED_NUM):
                    for j in range(DATA_LEN):
                        self.display_map[i][j] = LED_BRIGHTNESS_MIN

                # 障害物: 白
                for i in range(1024):
                    x = self.share_resouce._field_obj[2 * i]
                    y = self.share_resouce._field_obj[2 * i + 1]
                    if x >= 16 or y >= 16: # 障害物おわり
                        break
                    self.set_4led_brightness(15 - x, 15 - y, LED_BRIGHTNESS_MAX, LED_BRIGHTNESS_MAX, LED_BRIGHTNESS_MAX) # 白

                # マウス1: 赤(255,0,0) ピンク(255,120,120)
                set_r = LED_BRIGHTNESS_MAX
                set_g = 120
                set_b = 120
                for i in range(1024):
                    x = self.share_resouce._path0[2 * i]
                    y = self.share_resouce._path0[2 * i + 1]
                    if x >= 16 or y >= 16: # 経路おわり
                        break

                    # 経路の中でマウスの位置を探す
                    if self.share_resouce._mouse0_pos[0] == x and self.share_resouce._mouse0_pos[1] == y: # マウスの位置
                        set_r = LED_BRIGHTNESS_MAX
                        set_g = LED_BRIGHTNESS_MIN
                        set_b = LED_BRIGHTNESS_MIN
                                            
                    self.set_4led_brightness(15 - x, 15 - y, set_r, set_g, set_b)

                # マウス2: 青(0,0,255) 薄い青(120,255,255)
                set_r = 120
                set_g = LED_BRIGHTNESS_MAX
                set_b = LED_BRIGHTNESS_MAX
                for i in range(1024):
                    x = self.share_resouce._path1[2 * i]
                    y = self.share_resouce._path1[2 * i + 1]
                    if x >= 16 or y >= 16: # 経路おわり
                        break

                    # 経路の中でマウスの位置を探す
                    if self.share_resouce._mouse1_pos[0] == x and self.share_resouce._mouse1_pos[1] == y: # マウスの位置
                        set_r = LED_BRIGHTNESS_MIN
                        set_g = LED_BRIGHTNESS_MIN
                        set_b = LED_BRIGHTNESS_MAX

                    self.set_4led_brightness(15 - x, 15 - y, set_r, set_g, set_b)

                # マウス3: 緑(0,255,0) うすい緑(120,255,120)
                set_r = 120
                set_g = LED_BRIGHTNESS_MAX
                set_b = 120
                for i in range(1024):
                    x = self.share_resouce._path2[2 * i]
                    y = self.share_resouce._path2[2 * i + 1]
                    if x >= 16 or y >= 16: # 経路おわり
                        break

                    # 経路の中でマウスの位置を探す
                    if self.share_resouce._mouse2_pos[0] == x and self.share_resouce._mouse2_pos[1] == y: # マウスの位置
                        set_r = LED_BRIGHTNESS_MIN
                        set_g = LED_BRIGHTNESS_MAX
                        set_b = LED_BRIGHTNESS_MIN

                    self.set_4led_brightness(15 - x, 15 - y, set_r, set_g, set_b)

                # マウス4: 黄(255,255,0) オレンジ(255,170,0)
                set_r = LED_BRIGHTNESS_MAX
                set_g = 170
                set_b = LED_BRIGHTNESS_MIN
                for i in range(1024):
                    x = self.share_resouce._path3[2 * i]
                    y = self.share_resouce._path3[2 * i + 1]
                    if x >= 16 or y >= 16: # 経路おわり
                        break

                    # 経路の中でマウスの位置を探す
                    if self.share_resouce._mouse3_pos[0] == x and self.share_resouce._mouse3_pos[1] == y: # マウスの位置
                        set_r = LED_BRIGHTNESS_MAX
                        set_g = LED_BRIGHTNESS_MAX
                        set_b = LED_BRIGHTNESS_MIN

                    self.set_4led_brightness(15 - x, 15 - y, set_r, set_g, set_b)

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
    
    def set_4led_brightness(self, x, y, r, g, b):
        self.display_map[(2 * y) * 32 +     (2 * x)][RED] = r
        self.display_map[(2 * y + 1) * 32 + (2 * x)][RED] = r
        self.display_map[(2 * y) * 32 +     (2 * x + 1)][RED] = r
        self.display_map[(2 * y + 1) * 32 + (2 * x + 1)][RED] = r
        self.display_map[(2 * y) * 32 +     (2 * x)][GREEN] = g
        self.display_map[(2 * y + 1) * 32 + (2 * x)][GREEN] = g
        self.display_map[(2 * y) * 32 +     (2 * x + 1)][GREEN] = g
        self.display_map[(2 * y + 1) * 32 + (2 * x + 1)][GREEN] = g
        self.display_map[(2 * y) * 32 +     (2 * x)][BLUE] = b
        self.display_map[(2 * y + 1) * 32 + (2 * x)][BLUE] = b
        self.display_map[(2 * y) * 32 +     (2 * x + 1)][BLUE] = b
        self.display_map[(2 * y + 1) * 32 + (2 * x + 1)][BLUE] = b

