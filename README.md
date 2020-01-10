# 8 Arm Maze System with User Interface (Ver.1)

國立勤益科大陳啟鈞教授團隊與台南市奇美醫院產學合作，進行【以路徑預測失智症之八臂迷宮系統】計畫，目的是探討使用紀錄被測者行走路徑來判斷出被測者是否有失智症傾向，以協助醫師診斷被測者是否罹患失智症。

![image](https://i.imgur.com/XrAZRnR.png)

## Steps for System
### Python Libarary
Python需安裝下列套件才可成功執行：
```bash
pip install opencv-python #OpenCV(import cv2)
pip install Pillow #PIL(from PIL impory Image)
```

### Prepare
1. 開啟紅外線攝像視窗，確認八臂迷宮是否對齊預設框線
2. 設定**寫入檔案路徑**以及**老鼠編號(RatID)**
3. 勾選放置食物的臂腳位
4. 點擊開始按鈕，開始計時

### Run
1. 系統會記錄進臂順序並顯示於[Route]輸入框
2. 當老鼠將所有食物吃完時，時間暫停並記錄總時間
3. 紀錄該老鼠的短期記憶錯誤(Short Term)、長期記憶錯誤(Long Term)以及完成總時間(Latency)
4. 將老鼠編號(RatID)、記憶錯誤(Short Term)、長期記憶錯誤(Long Term)、完成總時間(Latency)以及進臂順序(Route)寫入紀錄檔案

> 短期記憶錯誤(Short Term)：當該臂進入兩次(含)以上，則紀錄錯誤乙次

> 長期記憶錯誤(Long Term)：當第一次進入無食物臂，則紀錄錯誤乙次

## Designer
National Chin-Yi University of Techology Department of Electronic Engineering 
- Master [Wang, Jian-Yung](https://github.com/s92475mark)
- Master [Hong, Liang-Jyun](https://github.com/louishong)