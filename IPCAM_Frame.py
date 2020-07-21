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
DBGV.CheckP_IPCAM = "1"

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
IPCAM_Port = 0			#攝影機port
IPCAM_NowTime = datetime.datetime.now()	#現在時間

IPCAM_Messenage = ""	#顯示在UI上訊息內容
IPCAM_MsgColor = 0		#顯示在UI上訊息顏色

def convert(list): #轉換資料型態(list -> tuple)
    return tuple(list)

def makeBlackImage(): #製造出全黑圖片(10x10)
	DBGV.CheckP_IPCAM = "14"
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

def setMessenage(color, messenge): #UI訊息顯示(顏色, 訊息)
	DBGV.CheckP_IPCAM = "15"
	global IPCAM_MsgColor, IPCAM_Messenage
	time.sleep(0.01)
	IPCAM_MsgColor = color
	IPCAM_Messenage = messenge

def Main():
	global IPCAM_Image, IPCAM_FrameCount
	global IPCAM_Username, IPCAM_Password, IPCAM_Name, IPCAM_IP, IPCAM_Frame, IPCAM_NewP1, IPCAM_NowTime,IPCAM_Port
	global CAM_INIT_SUCCESS, CAM_IS_RUN, DBGV

	try:
		FIRST_RUN = True
		newTime = datetime.datetime.now() #紀錄啟始時間
		DBGV.CheckP_IPCAM = "2"
		while WINDOWS_IS_ACTIVE:	#UI開啟
			DBGV.CheckP_IPCAM = "3"
			if CAM_INIT_SUCCESS:	#LOAD按鈕匯入IPCAM資訊
				DBGV.CheckP_IPCAM = "4"		
				if CAM_IS_RUN:		#LINK按鈕啟動IPCAM
					DBGV.CheckP_IPCAM = "5"
					if FIRST_RUN:	#第一次執行
						DBGV.CheckP_IPCAM = "6-1"
						IPCAM_Image = []	#影像儲存變數清空
						frame = []			#frame變數宣告
						FrameCount = 0		#幀數計數歸零
						rtsp = "rtsp://{0}:{1}@{2}:{4}/{3}".format(IPCAM_Username, IPCAM_Password, IPCAM_IP, IPCAM_Bar,IPCAM_Port) #RTSP連結

						cap = cv2.VideoCapture(rtsp)	#IPCAM視訊串流
						FIRST_RUN = False
						DBGV.CheckP_IPCAM = "6-2"

					nowTime = datetime.datetime.now()	#紀錄現在時間
					DBGV.CheckP_IPCAM = "7"
					if cap.isOpened():
						DBGV.CheckP_IPCAM = "8-1"
						ret,frame = cap.read()			#IPCAM視訊截取(ret->True有圖片/False無圖片 frame->影像圖片)
						DBGV.IPCAM_Name = IPCAM_Name
						DBGV.IPCAM_IP = IPCAM_IP
						DBGV.IPCAM_NewP1 = IPCAM_NewP1
						DBGV.CheckP_IPCAM = "8-2"
					else:
						DBGV.CheckP_IPCAM = "9-1"
						setMessenage(2, "[ERROR] Camera Not Open!!")
						cap = cv2.VideoCapture(rtsp)	#IPCAM視訊截取
						DBGV.CheckP_IPCAM = "9-2"

					if frame is not None:	#如果影像有截取到
						DBGV.CheckP_IPCAM = "10-1"
						IPCAM_Image = frame
						DBGV.IPCAM_Image = frame.copy()
						DBGV.CheckP_IPCAM = "10-2"
						FrameCount = FrameCount + 1
						IPCAM_NowTime = datetime.datetime.now() #影像讀取成功的時間
						DBGV.IPCAM_NowTime = IPCAM_NowTime
						if (nowTime - newTime).seconds > 0:
							DBGV.CheckP_IPCAM = "10-3"
							IPCAM_FrameCount = FrameCount
							DBGV.IPCAM_FrameCount = FrameCount
							FrameCount = 0
							newTime = datetime.datetime.now() #更新啟始時間
							DBGV.CheckP_IPCAM = "10-4"
					else:
						DBGV.CheckP_IPCAM = "11-1"
						setMessenage(2, "[ERROR] Frame is NULL! Reconnecting...")
						cap = cv2.VideoCapture(rtsp)	#IPCAM視訊截取
						DBGV.CheckP_IPCAM = "11-2"
				else:
					DBGV.CheckP_IPCAM = "13-1"
					setMessenage(1, "[INFO] CAMERA Unlink")
					FIRST_RUN = True
					IPCAM_Image = []
					DBGV.IPCAM_Image = []
					FrameCount = 0
					DBGV.CheckP_IPCAM = "13-2"

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