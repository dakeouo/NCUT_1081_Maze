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

WINDOWS_CLOSED = False #視窗是否關閉
CAM_INIT_SUCCESS = False
MSG_Print = False #是否傳送訊息
IPCAM_Username = ""
IPCAM_Password = ""
IPCAM_IP = ""
IPCAM_FrameCount = 0
IPCAM_Frame = 15
IPCAM_Name = ""
IPCAM_Bar = ""
IPCAM_Image = []
IPCAM_ConfigStatus = 0
IPCAM_NewP1 = [0, 0]
IPCAM_NowTime = datetime.datetime.now()

IPCAM_Messenage = ""
IPCAM_MsgColor = 0

VideoDir = './video_{}/'.format(datetime.datetime.now().strftime("%Y%m%d"))

WINDOWS_IS_ACTIVE = True
CAM_IS_RUN = False

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

def TwoImageisSame(img1, img2):
	img1 = Image.fromarray(cv2.cvtColor(img1,cv2.COLOR_BGR2RGB))
	img2 = Image.fromarray(cv2.cvtColor(img2,cv2.COLOR_BGR2RGB))
	diff = ImageChops.difference(img1, img2)
	if diff.getbbox() is None:
		return True
	else:
		return False

def checkVideoDir():
	global VideoDir
	VideoDir = './video_{}/'.format(datetime.datetime.now().strftime("%Y%m%d"))
	if not os.path.exists(VideoDir):
		os.mkdir(VideoDir)

def setMessenage(color, messenge):
	global IPCAM_MsgColor, IPCAM_Messenage
	time.sleep(0.2)
	IPCAM_MsgColor = color
	IPCAM_Messenage = messenge

def Main():
	global count, IPCAM_Image,  MSG_Print, IPCAM_Messenage, IPCAM_FrameCount, IPCAM_NowTime, IPCAM_ConfigStatus, VideoDir
	global IPCAM_Username, IPCAM_Password, IPCAM_Name, IPCAM_IP, IPCAM_Frame, IPCAM_NewP1, CAM_INIT_SUCCESS

	try:
		IPCAM_Image = []
		newTime = datetime.datetime.now()
		videoTime = datetime.datetime.now()
		
		FIRST_RUN = True
		InitFile = "./config.txt"
		# print(VideoDir)
		# sendMsg("Please create 'config.txt' file at EXECUTION FILE FOLDER and fill in camera information:")
		# sendMsg("[Username],[Password],[Camera Name],[Camera IP],[Camera FPS]")
		while WINDOWS_IS_ACTIVE:
			# print(IPCAM_Messenage)

			if CAM_INIT_SUCCESS:
				
				if CAM_IS_RUN:
					if FIRST_RUN:
						rtsp = "rtsp://{0}:{1}@{2}:554/{3}".format(IPCAM_Username, IPCAM_Password, IPCAM_IP, IPCAM_Bar) #1920x1080
						cap = cv2.VideoCapture(rtsp)
						ret,frame = cap.read()
						FrameCount = 0
						FIRST_RUN = False

						checkVideoDir() #影片資料夾檢查
						VideoOut = cv2.VideoWriter("{}{}_{}.avi".format(VideoDir,IPCAM_Name,datetime.datetime.now().strftime("%Y-%m-%d %H-%M-%S")),cv2.VideoWriter_fourcc(*'DIVX'), IPCAM_Frame, (frame.shape[1], frame.shape[0]))

					nowTime = datetime.datetime.now()
					IPCAM_NowTime = datetime.datetime.now()
					if cap.isOpened():
						ret,frame = cap.read()
					else:
						setMessenage(2, "[ERROR] Camera Not Open!!")
					
					if (nowTime - videoTime).seconds > 6000:
						VideoOut.release()
						checkVideoDir() #影片資料夾檢查
						VideoOut = cv2.VideoWriter("{}{}_{}.avi".format(VideoDir,IPCAM_Name,datetime.datetime.now().strftime("%Y-%m-%d %H-%M-%S")),cv2.VideoWriter_fourcc(*'DIVX'), IPCAM_Frame, (frame.shape[1], frame.shape[0]))
						videoTime = nowTime
					else:
						if len(IPCAM_Image) == 0:
							VideoOut.write(cv2.resize(makeBlackImage(),(frame.shape[1], frame.shape[0]),interpolation=cv2.INTER_CUBIC))
						else:
							VideoOut.write(IPCAM_Image)

					if frame is not None:
						IPCAM_Image = frame
						FrameCount = FrameCount + 1
						if (nowTime - newTime).seconds > 0:
							IPCAM_FrameCount = FrameCount
							FrameCount = 0
							newTime = datetime.datetime.now()

					else:
						IPCAM_Image = []
						setMessenage(2, "[ERROR] Frame is NULL! Reconnecting...")
						cap = cv2.VideoCapture(rtsp)
						setMessenage(1, "[WAIT] Setup the IP Camera")

				else:
					# CAM_INIT_SUCCESS = False
					IPCAM_Image = []

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