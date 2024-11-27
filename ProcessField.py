

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
MODE_3 = 3 # 経路全体を表示
MODE_4 = 4 # 往路 赤-->ピンク のように通過した経路を薄い色にする
MODE_5 = 5 # 復路 ピンク-->赤 のように通過した経路を元の色にする
MODE_6 = 6 # 全マウスゴール到達 パフォーマンス表示

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
        self.share_resouce._field_mode.value = MODE_1

        image_directory = 'img'
        image_files = ['GOAL_1.png', 'GOAL_2.png', 'GOAL_3.png', 'GOAL_4.png', 'GOAL_5.png']

        # 画像を順番に読み込んで処理
        self.images = []
        for filename in image_files:
            # 画像ファイルのパスを作成
            image_path = os.path.join(image_directory, filename)
            
            # 画像をカラーで読み込む
            image = cv2.imread(image_path, cv2.IMREAD_COLOR)  # カラー画像として読み込む
            
            # 画像が読み込めたか確認
            if image is not None:
                self.images.append(image.reshape(-1, 3))
            else:
                print(f"Failed to load {filename}")

        print(len(self.images))
        for i in range(len(self.images)):
            for j in range(len(self.images[i])):
                print('(', self.images[i][j][0], self.images[i][j][1], self.images[i][j][2], ')', end=' ')

    def setup(self):
        print("ProcessField.setup")
        self.display_map = [[0 for j in range(DATA_LEN)] for i in range(LED_NUM)]
        self.display_map.append([0x01])      #最終のエンドフラグは書き込み済み

        color = RED

        try:
            self.ser = serial.Serial('/dev/tty.usbmodem2201', SELECT_SERIAL_SPEED)  # シリアルポートとボーレートの設定
        except:
            print("[Warning] Serial port can't open. ls /dev/tty.*")
            pass # シリアルポートが開けない場合は無視(debug用)

        led_no=0

        while True:
            start_time = time.time()

            ################################
            # MODE 0: 
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
            # MODE 1: 
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
            # MODE 2: 
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
            
            ################################
            # MODE 3: 経路全体を表示
            ################################
            elif self.share_resouce._field_mode.value == MODE_3:
                # 全部白
                for i in range(LED_NUM):
                    for j in range(DATA_LEN):
                        self.display_map[i][j] = LED_BRIGHTNESS_MIN
                
                # 障害物を表示
                for i in range(1024):
                    y = self.share_resouce._field_obj[2 * i]
                    x = self.share_resouce._field_obj[2 * i + 1]
                    if x < 16 and y < 16:
                        self.display_map[(2 * x) * 32 + (2 * y)][RED] = LED_BRIGHTNESS_MAX
                        self.display_map[(2 * x + 1) * 32 + (2 * y)][RED] = LED_BRIGHTNESS_MAX
                        self.display_map[(2 * x) * 32 + (2 * y + 1)][RED] = LED_BRIGHTNESS_MAX
                        self.display_map[(2 * x + 1) * 32 + (2 * y + 1)][RED] = LED_BRIGHTNESS_MAX
                        self.display_map[(2 * x) * 32 + (2 * y)][GREEN] = LED_BRIGHTNESS_MAX
                        self.display_map[(2 * x + 1) * 32 + (2 * y)][GREEN] = LED_BRIGHTNESS_MAX
                        self.display_map[(2 * x) * 32 + (2 * y + 1)][GREEN] = LED_BRIGHTNESS_MAX
                        self.display_map[(2 * x + 1) * 32 + (2 * y + 1)][GREEN] = LED_BRIGHTNESS_MAX
                        self.display_map[(2 * x) * 32 + (2 * y)][BLUE] = LED_BRIGHTNESS_MAX
                        self.display_map[(2 * x + 1) * 32 + (2 * y)][BLUE] = LED_BRIGHTNESS_MAX
                        self.display_map[(2 * x) * 32 + (2 * y + 1)][BLUE] = LED_BRIGHTNESS_MAX
                        self.display_map[(2 * x + 1) * 32 + (2 * y + 1)][BLUE] = LED_BRIGHTNESS_MAX
                    else:
                        break

                # マウス1: 赤
                for i in range(1024):
                    y = self.share_resouce._path0[2 * i]
                    x = self.share_resouce._path0[2 * i + 1]
                    if x < 16 and y < 16:
                        self.display_map[(2 * x) * 32 + (2 * y)][RED] = LED_BRIGHTNESS_MAX
                        self.display_map[(2 * x + 1) * 32 + (2 * y)][RED] = LED_BRIGHTNESS_MAX
                        self.display_map[(2 * x) * 32 + (2 * y + 1)][RED] = LED_BRIGHTNESS_MAX
                        self.display_map[(2 * x + 1) * 32 + (2 * y + 1)][RED] = LED_BRIGHTNESS_MAX
                    else:
                        break
                # マウス2: 青
                for i in range(1024):
                    y = self.share_resouce._path1[2 * i]
                    x = self.share_resouce._path1[2 * i + 1]
                    if x < 16 and y < 16:
                        self.display_map[(2 * x) * 32 + (2 * y)][BLUE] = LED_BRIGHTNESS_MAX
                        self.display_map[(2 * x + 1) * 32 + (2 * y)][BLUE] = LED_BRIGHTNESS_MAX
                        self.display_map[(2 * x) * 32 + (2 * y + 1)][BLUE] = LED_BRIGHTNESS_MAX
                        self.display_map[(2 * x + 1) * 32 + (2 * y + 1)][BLUE] = LED_BRIGHTNESS_MAX
                    else:  
                        break
                # マウス3: 緑
                for i in range(1024):
                    y = self.share_resouce._path2[2 * i]
                    x = self.share_resouce._path2[2 * i + 1]
                    if x < 16 and y < 16:
                        self.display_map[(2 * x) * 32 + (2 * y)][GREEN] = LED_BRIGHTNESS_MAX
                        self.display_map[(2 * x + 1) * 32 + (2 * y)][GREEN] = LED_BRIGHTNESS_MAX
                        self.display_map[(2 * x) * 32 + (2 * y + 1)][GREEN] = LED_BRIGHTNESS_MAX
                        self.display_map[(2 * x + 1) * 32 + (2 * y + 1)][GREEN] = LED_BRIGHTNESS_MAX
                    else:
                        break
                # マウス4: 黄色
                for i in range(1024):
                    y = self.share_resouce._path3[2 * i]
                    x = self.share_resouce._path3[2 * i + 1]
                    if x < 16 and y < 16:
                        self.display_map[(2 * x) * 32 + (2 * y)][RED] = LED_BRIGHTNESS_MAX
                        self.display_map[(2 * x + 1) * 32 + (2 * y)][RED] = LED_BRIGHTNESS_MAX
                        self.display_map[(2 * x) * 32 + (2 * y + 1)][RED] = LED_BRIGHTNESS_MAX
                        self.display_map[(2 * x + 1) * 32 + (2 * y + 1)][RED] = LED_BRIGHTNESS_MAX

                        self.display_map[(2 * x) * 32 + (2 * y)][GREEN] = LED_BRIGHTNESS_MAX
                        self.display_map[(2 * x + 1) * 32 + (2 * y)][GREEN] = LED_BRIGHTNESS_MAX
                        self.display_map[(2 * x) * 32 + (2 * y + 1)][GREEN] = LED_BRIGHTNESS_MAX
                        self.display_map[(2 * x + 1) * 32 + (2 * y + 1)][GREEN] = LED_BRIGHTNESS_MAX
                    else:
                        break

                self.serial_send()

            #########################################################
            # MODE 4: 往路 赤-->ピンク のように通過した経路を薄い色にする
            #########################################################
            elif self.share_resouce._field_mode.value == MODE_4:
                # 全部白
                for i in range(LED_NUM):
                    for j in range(DATA_LEN):
                        self.display_map[i][j] = LED_BRIGHTNESS_MIN

                # 障害物を表示
                for i in range(1024):
                    y = self.share_resouce._field_obj[2 * i]
                    x = self.share_resouce._field_obj[2 * i + 1]
                    if x < 16 and y < 16:
                        self.display_map[(2 * x) * 32 + (2 * y)][RED] = LED_BRIGHTNESS_MAX
                        self.display_map[(2 * x + 1) * 32 + (2 * y)][RED] = LED_BRIGHTNESS_MAX
                        self.display_map[(2 * x) * 32 + (2 * y + 1)][RED] = LED_BRIGHTNESS_MAX
                        self.display_map[(2 * x + 1) * 32 + (2 * y + 1)][RED] = LED_BRIGHTNESS_MAX
                        self.display_map[(2 * x) * 32 + (2 * y)][GREEN] = LED_BRIGHTNESS_MAX
                        self.display_map[(2 * x + 1) * 32 + (2 * y)][GREEN] = LED_BRIGHTNESS_MAX
                        self.display_map[(2 * x) * 32 + (2 * y + 1)][GREEN] = LED_BRIGHTNESS_MAX
                        self.display_map[(2 * x + 1) * 32 + (2 * y + 1)][GREEN] = LED_BRIGHTNESS_MAX
                        self.display_map[(2 * x) * 32 + (2 * y)][BLUE] = LED_BRIGHTNESS_MAX
                        self.display_map[(2 * x + 1) * 32 + (2 * y)][BLUE] = LED_BRIGHTNESS_MAX
                        self.display_map[(2 * x) * 32 + (2 * y + 1)][BLUE] = LED_BRIGHTNESS_MAX
                        self.display_map[(2 * x + 1) * 32 + (2 * y + 1)][BLUE] = LED_BRIGHTNESS_MAX
                    else:
                        break

                # マウス1: 赤
                for i in range(1024):
                    y = self.share_resouce._path0[2 * i]
                    x = self.share_resouce._path0[2 * i + 1]
                    if x < 16 and y < 16:
                        self.display_map[(2 * x) * 32 + (2 * y)][RED] = LED_BRIGHTNESS_MAX
                        self.display_map[(2 * x + 1) * 32 + (2 * y)][RED] = LED_BRIGHTNESS_MAX
                        self.display_map[(2 * x) * 32 + (2 * y + 1)][RED] = LED_BRIGHTNESS_MAX
                        self.display_map[(2 * x + 1) * 32 + (2 * y + 1)][RED] = LED_BRIGHTNESS_MAX
                    else:
                        break
                    if self.share_resouce._mouse0_pos[0] == y and self.share_resouce._mouse0_pos[1] == x:
                        next_y = self.share_resouce._path0[2 * (i + 1)]     # 次のマウスのy位置
                        next_x = self.share_resouce._path0[2 * (i + 1) + 1] # 次のマウスのx位置
                        if next_x == 255 or next_y == 255:                  # 経路の終端 --> ゴールに到達した
                            self.share_resouce._field_mode5_is_goal[0] = 1  # ゴール到達フラグを立てる
                        if self.share_resouce._field_mode5_is_goal[0] == 0: # ゴールに到達していない場合は、マウスの位置までを表示
                            break
                # マウス2: 青
                for i in range(1024):
                    y = self.share_resouce._path1[2 * i]
                    x = self.share_resouce._path1[2 * i + 1]
                    if x < 16 and y < 16:
                        self.display_map[(2 * x) * 32 + (2 * y)][BLUE] = LED_BRIGHTNESS_MAX
                        self.display_map[(2 * x + 1) * 32 + (2 * y)][BLUE] = LED_BRIGHTNESS_MAX
                        self.display_map[(2 * x) * 32 + (2 * y + 1)][BLUE] = LED_BRIGHTNESS_MAX
                        self.display_map[(2 * x + 1) * 32 + (2 * y + 1)][BLUE] = LED_BRIGHTNESS_MAX
                    else:  
                        break
                    if self.share_resouce._mouse1_pos[0] == y and self.share_resouce._mouse1_pos[1] == x:
                        next_y = self.share_resouce._path1[2 * (i + 1)]     # 次のマウスのy位置
                        next_x = self.share_resouce._path1[2 * (i + 1) + 1] # 次のマウスのx位置
                        if next_x == 255 or next_y == 255:                  # 経路の終端 --> ゴールに到達した
                            self.share_resouce._field_mode5_is_goal[1] = 1  # ゴール到達フラグを立てる
                        if self.share_resouce._field_mode5_is_goal[1] == 0: # ゴールに到達していない場合は、マウスの位置までを表示
                            break
                # マウス3: 緑
                for i in range(1024):
                    y = self.share_resouce._path2[2 * i]
                    x = self.share_resouce._path2[2 * i + 1]
                    if x < 16 and y < 16:
                        self.display_map[(2 * x) * 32 + (2 * y)][GREEN] = LED_BRIGHTNESS_MAX
                        self.display_map[(2 * x + 1) * 32 + (2 * y)][GREEN] = LED_BRIGHTNESS_MAX
                        self.display_map[(2 * x) * 32 + (2 * y + 1)][GREEN] = LED_BRIGHTNESS_MAX
                        self.display_map[(2 * x + 1) * 32 + (2 * y + 1)][GREEN] = LED_BRIGHTNESS_MAX
                    else:
                        break
                    if self.share_resouce._mouse2_pos[0] == y and self.share_resouce._mouse2_pos[1] == x:
                        next_y = self.share_resouce._path2[2 * (i + 1)]     # 次のマウスのy位置
                        next_x = self.share_resouce._path2[2 * (i + 1) + 1] # 次のマウスのx位置
                        if next_x == 255 or next_y == 255:                  # 経路の終端 --> ゴールに到達した
                            self.share_resouce._field_mode5_is_goal[2] = 1  # ゴール到達フラグを立てる
                        if self.share_resouce._field_mode5_is_goal[2] == 0: # ゴールに到達していない場合は、マウスの位置までを表示
                            break
                # マウス4: 黄色
                for i in range(1024):
                    y = self.share_resouce._path3[2 * i]
                    x = self.share_resouce._path3[2 * i + 1]
                    if x < 16 and y < 16:
                        self.display_map[(2 * x) * 32 + (2 * y)][RED] = LED_BRIGHTNESS_MAX
                        self.display_map[(2 * x + 1) * 32 + (2 * y)][RED] = LED_BRIGHTNESS_MAX
                        self.display_map[(2 * x) * 32 + (2 * y + 1)][RED] = LED_BRIGHTNESS_MAX
                        self.display_map[(2 * x + 1) * 32 + (2 * y + 1)][RED] = LED_BRIGHTNESS_MAX
                        
                        self.display_map[(2 * x) * 32 + (2 * y)][GREEN] = LED_BRIGHTNESS_MAX
                        self.display_map[(2 * x + 1) * 32 + (2 * y)][GREEN] = LED_BRIGHTNESS_MAX
                        self.display_map[(2 * x) * 32 + (2 * y + 1)][GREEN] = LED_BRIGHTNESS_MAX
                        self.display_map[(2 * x + 1) * 32 + (2 * y + 1)][GREEN] = LED_BRIGHTNESS_MAX
                    else:
                        break
                    if self.share_resouce._mouse3_pos[0] == y and self.share_resouce._mouse3_pos[1] == x:
                        next_y = self.share_resouce._path3[2 * (i + 1)]     # 次のマウスのy位置
                        next_x = self.share_resouce._path3[2 * (i + 1) + 1] # 次のマウスのx位置
                        if next_x == 255 or next_y == 255:                  # 経路の終端 --> ゴールに到達した
                            self.share_resouce._field_mode5_is_goal[3] = 1  # ゴール到達フラグを立てる
                        if self.share_resouce._field_mode5_is_goal[3] == 0: # ゴールに到達していない場合は、マウスの位置までを表示
                            break

                self.serial_send()

                # 全マウスがゴールに到達した場合、MODE 6 パフォーマンス表示に移行
                is_all_goal = True
                for i in range(NUM_MOUSE):
                    #print(i, ': ', self.share_resouce._connected_mice[i], ' ', self.share_resouce._field_mode5_is_goal[i])
                    if self.share_resouce._connected_mice[i] == 1 and self.share_resouce._field_mode5_is_goal[i] == 0:
                        is_all_goal = False
                        break
                #print('is_all_goal:', is_all_goal)
                if is_all_goal:
                    self.share_resouce._field_mode.value = MODE_6
                    self.mode6_timer = 0


            #########################################################
            # MODE 6: 全マウスゴール到達 パフォーマンス表示
            #########################################################
            elif self.share_resouce._field_mode.value == MODE_6:
                self.mode6_timer += 1
                print('mode6_timer:', self.mode6_timer)
                
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
            # MODE 5: 往路 赤-->ピンク のように通過した経路を薄い色にする
            #########################################################
            elif self.share_resouce._field_mode.value == MODE_4 or self.share_resouce._field_mode.value == MODE_5:
                # 全部白
                for i in range(LED_NUM):
                    for j in range(DATA_LEN):
                        self.display_map[i][j] = LED_BRIGHTNESS_MIN

                # 障害物を表示
                for i in range(1024):
                    y = self.share_resouce._field_obj[2 * i]
                    x = self.share_resouce._field_obj[2 * i + 1]
                    if x < 16 and y < 16:
                        self.display_map[(2 * x) * 32 + (2 * y)][RED] = LED_BRIGHTNESS_MAX
                        self.display_map[(2 * x + 1) * 32 + (2 * y)][RED] = LED_BRIGHTNESS_MAX
                        self.display_map[(2 * x) * 32 + (2 * y + 1)][RED] = LED_BRIGHTNESS_MAX
                        self.display_map[(2 * x + 1) * 32 + (2 * y + 1)][RED] = LED_BRIGHTNESS_MAX
                        self.display_map[(2 * x) * 32 + (2 * y)][GREEN] = LED_BRIGHTNESS_MAX
                        self.display_map[(2 * x + 1) * 32 + (2 * y)][GREEN] = LED_BRIGHTNESS_MAX
                        self.display_map[(2 * x) * 32 + (2 * y + 1)][GREEN] = LED_BRIGHTNESS_MAX
                        self.display_map[(2 * x + 1) * 32 + (2 * y + 1)][GREEN] = LED_BRIGHTNESS_MAX
                        self.display_map[(2 * x) * 32 + (2 * y)][BLUE] = LED_BRIGHTNESS_MAX
                        self.display_map[(2 * x + 1) * 32 + (2 * y)][BLUE] = LED_BRIGHTNESS_MAX
                        self.display_map[(2 * x) * 32 + (2 * y + 1)][BLUE] = LED_BRIGHTNESS_MAX
                        self.display_map[(2 * x + 1) * 32 + (2 * y + 1)][BLUE] = LED_BRIGHTNESS_MAX
                    else:
                        break

                # マウス1: 赤
                for i in range(1024):
                    y = self.share_resouce._path0[2 * i]
                    x = self.share_resouce._path0[2 * i + 1]
                    if x < 16 and y < 16:
                        self.display_map[(2 * x) * 32 + (2 * y)][RED] = LED_BRIGHTNESS_MAX
                        self.display_map[(2 * x + 1) * 32 + (2 * y)][RED] = LED_BRIGHTNESS_MAX
                        self.display_map[(2 * x) * 32 + (2 * y + 1)][RED] = LED_BRIGHTNESS_MAX
                        self.display_map[(2 * x + 1) * 32 + (2 * y + 1)][RED] = LED_BRIGHTNESS_MAX
                    else:
                        break
                    if self.share_resouce._mouse0_pos[0] == y and self.share_resouce._mouse0_pos[1] == x:
                        break
                # マウス2: 青
                for i in range(1024):
                    y = self.share_resouce._path1[2 * i]
                    x = self.share_resouce._path1[2 * i + 1]
                    if x < 16 and y < 16:
                        self.display_map[(2 * x) * 32 + (2 * y)][BLUE] = LED_BRIGHTNESS_MAX
                        self.display_map[(2 * x + 1) * 32 + (2 * y)][BLUE] = LED_BRIGHTNESS_MAX
                        self.display_map[(2 * x) * 32 + (2 * y + 1)][BLUE] = LED_BRIGHTNESS_MAX
                        self.display_map[(2 * x + 1) * 32 + (2 * y + 1)][BLUE] = LED_BRIGHTNESS_MAX
                    else:  
                        break
                    if self.share_resouce._mouse1_pos[0] == y and self.share_resouce._mouse1_pos[1] == x:
                            break
                # マウス3: 緑
                for i in range(1024):
                    y = self.share_resouce._path2[2 * i]
                    x = self.share_resouce._path2[2 * i + 1]
                    if x < 16 and y < 16:
                        self.display_map[(2 * x) * 32 + (2 * y)][GREEN] = LED_BRIGHTNESS_MAX
                        self.display_map[(2 * x + 1) * 32 + (2 * y)][GREEN] = LED_BRIGHTNESS_MAX
                        self.display_map[(2 * x) * 32 + (2 * y + 1)][GREEN] = LED_BRIGHTNESS_MAX
                        self.display_map[(2 * x + 1) * 32 + (2 * y + 1)][GREEN] = LED_BRIGHTNESS_MAX
                    else:
                        break
                    if self.share_resouce._mouse2_pos[0] == y and self.share_resouce._mouse2_pos[1] == x:
                            break
                # マウス4: 黄色
                for i in range(1024):
                    y = self.share_resouce._path3[2 * i]
                    x = self.share_resouce._path3[2 * i + 1]
                    if x < 16 and y < 16:
                        self.display_map[(2 * x) * 32 + (2 * y)][RED] = LED_BRIGHTNESS_MAX
                        self.display_map[(2 * x + 1) * 32 + (2 * y)][RED] = LED_BRIGHTNESS_MAX
                        self.display_map[(2 * x) * 32 + (2 * y + 1)][RED] = LED_BRIGHTNESS_MAX
                        self.display_map[(2 * x + 1) * 32 + (2 * y + 1)][RED] = LED_BRIGHTNESS_MAX
                        
                        self.display_map[(2 * x) * 32 + (2 * y)][GREEN] = LED_BRIGHTNESS_MAX
                        self.display_map[(2 * x + 1) * 32 + (2 * y)][GREEN] = LED_BRIGHTNESS_MAX
                        self.display_map[(2 * x) * 32 + (2 * y + 1)][GREEN] = LED_BRIGHTNESS_MAX
                        self.display_map[(2 * x + 1) * 32 + (2 * y + 1)][GREEN] = LED_BRIGHTNESS_MAX
                    else:
                        break
                    if self.share_resouce._mouse3_pos[0] == y and self.share_resouce._mouse3_pos[1] == x:
                            break

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
