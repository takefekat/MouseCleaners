# ⚡️電光石火⭐︎ぴかぴかクリーナーズ



#### 起動時処理(プロセス起動)

```mermaid
sequenceDiagram
    participant main as main
    participant gui as GUI(Qt)<br>Process
    participant field as パリピ迷路<br>Process
    participant wifi as WiFi<br>Process

    # 初期化
    main ->>+ gui: プロセス起動
    Note over gui:  描画スタート<br>ユーザ操作待ち

    main ->>+ field: プロセス起動
    Note over field:  自動描画モードで描画

    main ->>+ wifi: プロセス起動
    Note over wifi: マウス接続待ち
```

#### マウスWiFi接続
目的：
- システムに接続しているマウスの数をGUIで表示する
- 経路計算で必要なマウスの数を経路計算を行うGUIプロセスへ通知する

```mermaid
sequenceDiagram
    participant main as main
    participant gui as GUI(Qt)<br>Process
    participant field as パリピ迷路<br>Process
    participant wifi as WiFi<br>Process
    participant mouse1 as Mouse 1<br>M5Stamp
    participant mouseN as Mouse N<br>M5Stamp

    # 初期化
    mouse1 ->>+ wifi: socket接続
    Note over wifi: 接続マウス数++
    wifi ->>+ gui: 接続数更新
    Note over gui: 接続マウス数 描画更新

    
    mouseN ->>+ wifi: socket接続
    Note over wifi: 接続マウス数++
    wifi ->>+ gui: 接続数更新
    Note over gui: 接続マウス数 描画更新
```

#### 経路選択ボタン/経路決定ボタン押下
目的：
- ユーザに経路を選択させる（連続して押下した場合は前回値はリセットする）

（Want: ユーザに自由に経路引かせられたら楽しいかも。）

```mermaid
sequenceDiagram

    participant main as main
    participant gui as GUI(Qt)<br>Process
    participant field as パリピ迷路<br>Process
    participant wifi as WiFi<br>Process
    participant mouse1 as Mouse 1<br>M5Stamp
    participant mouseN as Mouse N<br>M5Stamp
    participant user as 操作者

    # 走行経路選択
    user ->>+ gui: 走行経路選択ボタン押下
    Note over gui: 各マウスの走行経路計算
    Note over gui: 各マウスの走行経路を描画
    gui ->>+ field: 各マウスの走行経路
    Note over field: 各マウスの走行経路を描画

    # 走行経路決定
    user ->>+ gui: 走行経路決定ボタン押下
    gui ->>+ wifi: 各マウスの走行経路
    wifi ->>+ mouse1: マウス1の走行経路
    Note over mouse1: 走行経路記憶
    wifi ->>+ mouseN: マウスNの走行経路
    Note over mouseN: 走行経路記憶
```

#### 走行開始ボタン押下
目的：
- 走行開始ボタン押下で、掃除を開始する
- 走行中の

走行停止ボタンも同様の流れ。
```mermaid
sequenceDiagram

    participant main as main
    participant gui as GUI(Qt)<br>Process
    participant field as パリピ迷路<br>Process
    participant wifi as WiFi<br>Process
    participant mouse1 as Mouse 1<br>M5Stamp
    participant mouseN as Mouse N<br>M5Stamp
    participant user as 操作者
    
    # 走行経路決定
    user ->>+ gui: 走行開始ボタン押下
    gui ->>+ wifi: 走行開始指示
    wifi ->>+ mouse1: 走行開始指示
    Note over mouse1: 走行開始
    wifi ->>+ mouseN: 走行開始指示
    Note over mouseN: 走行開始

    # 走行開始
    gui ->>+ field: 走行開始指示
    Note over field: 一定周期で描画更新
    Note over gui: 一定周期で描画更新
```

#### 走行停止ボタン押下
目的：
- 走行中のマウスを止める

```mermaid
sequenceDiagram

    participant main as main
    participant gui as GUI(Qt)<br>Process
    participant field as パリピ迷路<br>Process
    participant wifi as WiFi<br>Process
    participant mouse1 as Mouse 1<br>M5Stamp
    participant mouseN as Mouse N<br>M5Stamp
    participant user as 操作者
    
    # 走行経路決定
    user ->>+ gui: 走行停止ボタン押下
    gui ->>+ wifi: 走行停止指示
    wifi ->>+ mouse1: 走行停止指示
    Note over mouse1: 走行停止
    wifi ->>+ mouseN: 走行停止指示
    Note over mouseN: 走行停止

    # 走行開始
    gui ->>+ field: 走行停止指示
    Note over field: 描画更新を中断
    Note over gui: 描画更新を中断
```