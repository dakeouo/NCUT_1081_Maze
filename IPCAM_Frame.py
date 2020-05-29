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

Record_Frame = []

IPCAM_Messenage = ""
IPCAM_MsgColor = 0

nowDatePath = './ChiMei_{}/'.format(datetime.datetime.now().strftime("%Y%m%d"))
VideoDir = 'Video_{}/'.format(datetime.datetime.now().strftime("%Y%m%d"))

WINDOWS_IS_ACTIVE = True
CAM_IS_RUN = False

SHOW_StartFlag = False
SHOW_CurrentArm = 0
SHOW_MazeState = 0

SHOW_DiseaseType = "" #老鼠病症組別
SHOW_DisGroupType = "" #老鼠病症組別復鍵(含 健康、無復健 等)
SHOW_DisDays = [False, -1, -1] #老鼠病症天數(是否手術, 月, 天)
SHOW_RatID = "" #老鼠ID

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

def TwoImageisSame(img1, img2):
	img1 = Image.fromarray(cv2.cvtColor(img1,cv2.COLOR_BGR2RGB))
	img2 = Image.fromarray(cv2.cvtColor(img2,cv2.COLOR_BGR2RGB))
	diff = ImageChops.difference(img1, img2)
	if diff.getbbox() is None:
		return True
	else:
		return False

def checkVideoDir():
	global nowDatePath, VideoDir
	nowDatePath = './ChiMei_{}/'.format(datetime.datetime.now().strftime("%Y%m%d"))
	VideoDir = 'Video_{}/'.format(datetime.datetime.now().strftime("%Y%m%d"))
	if not os.path.exists(nowDatePath):
		os.mkdir(nowDatePath)
	if not os.path.exists(nowDatePath + VideoDir):
		os.mkdir(nowDatePath + VideoDir)

def setMessenage(color, messenge):
	global IPCAM_MsgColor, IPCAM_Messenage
	time.sleep(0.2)
	IPCAM_MsgColor = color
	IPCAM_Messenage = messenge

def addExpInfo2img(img):
	global SHOW_StartFlag, SHOW_CurrentArm, SHOW_MazeState
	global SHOW_DiseaseType, SHOW_DisGroupType, SHOW_DisDays, SHOW_RatID, IPCAM_Name

	imgX, imgY = (img.shape[1], img.shape[0])

	nowTime = datetime.datetime.now().strftime("%m%d %H:%M:%S")
	if SHOW_StartFlag:
		cv2.rectangle(img, (20, 40), (300, 240), (0, 0, 0), -1)
		cv2.putText(img, "StartFlag: {}".format(SHOW_StartFlag), (30, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255))
		cv2.putText(img, "CurrentArm: {}".format(SHOW_CurrentArm), (30, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255))
		cv2.putText(img, "MazeState: {}".format(SHOW_MazeState), (30, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255))
		if not SHOW_DisDays[0]:
			DisText = "Dis: pre %02dM%02dD" %(SHOW_DisDays[1], SHOW_DisDays[2])
		else:
			DisText = "Dis: past %02dM%02dD" %(SHOW_DisDays[1], SHOW_DisDays[2])
		cv2.putText(img, DisText, (30, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255))
		cv2.putText(img, "DiseaseType: {}".format(SHOW_DiseaseType), (30, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255))
		cv2.putText(img, "DisGroupType: {}".format(SHOW_DisGroupType), (30, 170), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255))
		cv2.putText(img, "RatID: {}".format(SHOW_RatID), (30, 190), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255))
		cv2.putText(img, "nowTime: {}".format(nowTime), (30, 210), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255))
	else:
		cv2.rectangle(img, (20, 40), (300, 120), (0, 0, 0), -1)
		cv2.putText(img, "StartFlag: {}".format(SHOW_StartFlag), (30, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255))
		cv2.putText(img, "IPCAM: {}".format(IPCAM_Name), (30, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255))
		cv2.putText(img, "nowTime: {}".format(nowTime), (30, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255))

	return img

def Main():
	global count, IPCAM_Image,  MSG_Print, IPCAM_Messenage, IPCAM_FrameCount, IPCAM_NowTime, IPCAM_ConfigStatus
	global IPCAM_Username, IPCAM_Password, IPCAM_Name, IPCAM_IP, IPCAM_Frame, IPCAM_NewP1, CAM_INIT_SUCCESS
	global nowDatePath, VideoDir

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
						# cap = cv2.VideoCapture(1)
						ret,frame = cap.read()
						FrameCount = 0
						FIRST_RUN = False

						checkVideoDir() #影片資料夾檢查
						VideoOut = cv2.VideoWriter("{}{}_{}.avi".format(nowDatePath + VideoDir, IPCAM_Name, datetime.datetime.now().strftime("%Y-%m-%d %H-%M-%S")),cv2.VideoWriter_fourcc(*'DIVX'), IPCAM_Frame, (frame.shape[1], frame.shape[0]))

					nowTime = datetime.datetime.now()
					IPCAM_NowTime = datetime.datetime.now()
					if cap.isOpened():
						ret,frame = cap.read()
					else:
						setMessenage(2, "[ERROR] Camera Not Open!!")
					
					if (nowTime - videoTime).seconds > 6000:
						VideoOut.release()
						checkVideoDir() #影片資料夾檢查
						VideoOut = cv2.VideoWriter("{}{}_{}.avi".format(nowDatePath + VideoDir, IPCAM_Name, datetime.datetime.now().strftime("%Y-%m-%d %H-%M-%S")),cv2.VideoWriter_fourcc(*'DIVX'), IPCAM_Frame, (frame.shape[1], frame.shape[0]))
						videoTime = nowTime
					else:
						# if len(IPCAM_Image) == 0:
						# 	VideoOut.write(cv2.resize(makeBlackImage(),(frame.shape[1], frame.shape[0]),interpolation=cv2.INTER_CUBIC))
						# else:
						# 	VideoOut.write(IPCAM_Image)
						
						if len(Record_Frame) == 0:
							Record_Frame = cv2.resize(makeBlackImage(),(frame.shape[1], frame.shape[0]),interpolation=cv2.INTER_CUBIC)
						recordBroad = addExpInfo2img(Record_Frame)
						VideoOut.write(Record_Frame)
						# cv2.imshow('recordBroad', recordBroad)
						# cv2.waitKey(1)

					if frame is not None:
						IPCAM_Image = frame
						Record_Frame = frame.copy()
						FrameCount = FrameCount + 1
						if (nowTime - newTime).seconds > 0:
							IPCAM_FrameCount = FrameCount
							FrameCount = 0
							newTime = datetime.datetime.now()

					else:
						IPCAM_Image = []
						setMessenage(2, "[ERROR] Frame is NULL! Reconnecting...")
						cap = cv2.VideoCapture(rtsp)
						# cap = cv2.VideoCapture(1)
						setMessenage(1, "[WAIT] Setup the IP Camera")

				else:
					# CAM_INIT_SUCCESS = False
					IPCAM_Image = []
					Record_Frame = []

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