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
import DebugVideo as DBGV

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
	global CAM_INIT_SUCCESS, CAM_IS_RUN, DBGV

	try:
		FIRST_RUN = True
		newTime = datetime.datetime.now() #啟始時間
		while WINDOWS_IS_ACTIVE:
			DBGV.CheckP_IPCAM = "1"
			if CAM_INIT_SUCCESS:
				DBGV.CheckP_IPCAM = "2"			
				if CAM_IS_RUN:
					DBGV.CheckP_IPCAM = "3"
					if FIRST_RUN:
						DBGV.CheckP_IPCAM = "4"
						IPCAM_Image = []
						FrameCount = 0
						rtsp = "rtsp://{0}:{1}@{2}:554/{3}".format(IPCAM_Username, IPCAM_Password, IPCAM_IP, IPCAM_Bar) #1920x1080

						DBGV.CheckP_IPCAM = "5"
						cap = cv2.VideoCapture(rtsp)
						FIRST_RUN = False
						DBGV.CheckP_IPCAM = "6"

					nowTime = datetime.datetime.now()
					if cap.isOpened():
						DBGV.CheckP_IPCAM = "7"
						ret,frame = cap.read()
						DBGV.CheckP_IPCAM = "8"
						DBGV.IPCAM_Name = IPCAM_Name
						DBGV.IPCAM_IP = IPCAM_IP
						DBGV.IPCAM_NewP1 = IPCAM_NewP1
						DBGV.CheckP_IPCAM = "9"
					else:
						DBGV.CheckP_IPCAM = "10"
						setMessenage(2, "[ERROR] Camera Not Open!!")
						cap = cv2.VideoCapture(rtsp)
						DBGV.CheckP_IPCAM = "11"

					if frame is not None:
						DBGV.CheckP_IPCAM = "12"
						IPCAM_Image = frame
						DBGV.IPCAM_Image = frame.copy()
						FrameCount = FrameCount + 1
						IPCAM_NowTime = datetime.datetime.now() #影像讀取成功的時間
						DBGV.IPCAM_NowTime = IPCAM_NowTime
						if (nowTime - newTime).seconds > 0:
							IPCAM_FrameCount = FrameCount
							DBGV.IPCAM_FrameCount = FrameCount
							FrameCount = 0
							newTime = datetime.datetime.now() #更新啟始時間
					else:
						DBGV.CheckP_IPCAM = "13"
						setMessenage(2, "[ERROR] Frame is NULL! Reconnecting...")
						cap = cv2.VideoCapture(rtsp)
						DBGV.CheckP_IPCAM = "14"
				else:
					DBGV.CheckP_IPCAM = "15"
					setMessenage(1, "[INFO] CAMERA Unlink")
					FIRST_RUN = True
					IPCAM_Image = []
					DBGV.IPCAM_Image = []
					FrameCount = 0
					DBGV.CheckP_IPCAM = "16"

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