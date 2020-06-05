import cv2
import numpy as np
from PIL import Image
from PIL import ImageChops
import datetime
import os
import time
import logging
import sys
import traceback

FORMAT = '%(asctime)s [%(filename)s] %(levelname)s: %(message)s'
logging.basicConfig(level=logging.WARNING, filename='MazeLog.log', filemode='a', format=FORMAT)

WINDOWS_CLOSED = False 		#視窗是否關閉
CAM_INIT_SUCCESS = False 	#攝相機是否初始化成功
WINDOWS_IS_ACTIVE = True	#UI是否在執行中
CAM_IS_RUN = False			#是否按下Link按鈕

IPCAM_Username = ""		#攝影機帳戶
IPCAM_Password = ""		#攝相機密碼
IPCAM_IP = ""			#攝相機IP
IPCAM_FrameCount = 0	#測試每秒禎數
IPCAM_Name = ""			#攝相機名稱
IPCAM_Bar = ""			#RTSP參數
IPCAM_Image = []		#攝相機影像
IPCAM_NewP1 = [0, 0]	#矩形框左上座標點
IPCAM_NowTime = datetime.datetime.now()	#現在時間

IPCAM_Messenage = ""	#顯示在UI上訊息內容
IPCAM_MsgColor = 0		#顯示在UI上訊息顏色

def convert(list):
    return tuple(list)

def makeBlackImage(): #製造出全黑圖片(10x10) <= 這個贈品很好用，送你XD
	pixels = []
	for i in range(0,10):
		row = []
		for j in range(0,10):
			row.append((0,0,0))
		pixels.append(row)
	array = np.array(pixels, dtype=np.uint8)
	newBlack = Image.fromarray(array)
	newBlack = cv2.cvtColor(np.asarray(newBlack),cv2.COLOR_RGB2BGR)  
	return newBlack

def setMessenage(color, messenge):
	global IPCAM_MsgColor, IPCAM_Messenage
	time.sleep(0.2)
	IPCAM_MsgColor = color
	IPCAM_Messenage = messenge

def Main():
	global IPCAM_Image, IPCAM_FrameCount
	global IPCAM_Username, IPCAM_Password, IPCAM_Name, IPCAM_IP, IPCAM_Frame, IPCAM_NewP1, IPCAM_NowTime
	global CAM_INIT_SUCCESS, CAM_IS_RUN

	try:
		FIRST_RUN = True
		newTime = datetime.datetime.now() #啟始時間
		while WINDOWS_IS_ACTIVE:
			if CAM_INIT_SUCCESS:			
				if CAM_IS_RUN:
					if FIRST_RUN:
						IPCAM_Image = []
						FrameCount = 0
						rtsp = "rtsp://{0}:{1}@{2}:554/{3}".format(IPCAM_Username, IPCAM_Password, IPCAM_IP, IPCAM_Bar) #1920x1080
						cap = cv2.VideoCapture(rtsp)
						FIRST_RUN = False

					nowTime = datetime.datetime.now()
					if cap.isOpened():
						ret,frame = cap.read()
					else:
						setMessenage(2, "[ERROR] Camera Not Open!!")
						cap = cv2.VideoCapture(rtsp)

					if frame is not None:
						IPCAM_Image = frame
						FrameCount = FrameCount + 1
						IPCAM_NowTime = datetime.datetime.now() #影像讀取成功的時間
						if (nowTime - newTime).seconds > 0:
							IPCAM_FrameCount = FrameCount
							FrameCount = 0
							newTime = datetime.datetime.now() #更新啟始時間
					else:
						setMessenage(2, "[ERROR] Frame is NULL! Reconnecting...")
						cap = cv2.VideoCapture(rtsp)
				else:
					setMessenage(1, "[INFO] CAMERA Unlink")
					FIRST_RUN = True
					IPCAM_Image = []
					FrameCount = 0

	except Warning as e:
		detail = e.args[0] #取得詳細內容
		cl, exc, tb = sys.exc_info() #取得Call Stack
		lastCallStack = traceback.extract_tb(tb)[-1] #取得Call Stack的最後一筆資料
		# fileName = lastCallStack[0] #取得發生的檔案名稱
		lineNum = lastCallStack[1] #取得發生的行號
		funcName = lastCallStack[2] #取得發生的函數名稱
		logging.warning("{} line {}, in '{}': {}".format(cl, lineNum, funcName, detail))

	except Exception as e:
		detail = e.args[0] #取得詳細內容
		cl, exc, tb = sys.exc_info() #取得Call Stack
		lastCallStack = traceback.extract_tb(tb)[-1] #取得Call Stack的最後一筆資料
		# fileName = lastCallStack[0] #取得發生的檔案名稱
		lineNum = lastCallStack[1] #取得發生的行號
		funcName = lastCallStack[2] #取得發生的函數名稱
		logging.error("{} line {}, in '{}': {}".format(cl, lineNum, funcName, detail))