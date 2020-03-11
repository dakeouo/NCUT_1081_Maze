import cv2
import numpy as np
from PIL import Image
from PIL import ImageChops
import datetime
import os
import time

WINDOWS_CLOSED = False #視窗是否關閉
MSG_Print = False #是否傳送訊息
IPCAM_Username = ""
IPCAM_Password = ""
IPCAM_IP = ""
IPCAM_FrameCount = 0
IPCAM_Frame = 0
IPCAM_Name = ""
IPCAM_Bar = ""
IPCAM_Image = []
IPCAM_Messenage = ""
IPCAM_ConfigStatus = 0
IPCAM_NowTime = datetime.datetime.now()

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

def getCamName():
	global IPCAM_Name
	return IPCAM_Name

def getCamFrame():
	global IPCAM_Frame, IPCAM_FrameCount
	return (IPCAM_Frame, IPCAM_FrameCount)

def getCamIP():
	global IPCAM_IP
	return IPCAM_IP

def getCamImage():
	global IPCAM_Image
	return IPCAM_Image
	# return []

def getMsgPrint():
	global MSG_Print
	return MSG_Print

def getNowTime():
	global IPCAM_NowTime
	return IPCAM_NowTime

def getMessenage():
	global IPCAM_Messenage
	Messenger = IPCAM_Messenage
	IPCAM_Messenage = ""
	return Messenger

def getConfigStatus():
	global IPCAM_ConfigStatus
	return IPCAM_ConfigStatus

def setWindowsStatus(status):
	global WINDOWS_CLOSED
	WINDOWS_CLOSED = status

def sendMsg(msg):
	global IPCAM_Messenage, MSG_Print
	time.sleep(0.2)
	IPCAM_Messenage = msg
	MSG_Print = True
	# print(msg)

def Main():
	global count, IPCAM_Image,  MSG_Print, IPCAM_Messenage, IPCAM_FrameCount, IPCAM_NowTime, IPCAM_ConfigStatus
	global IPCAM_Username, IPCAM_Password, IPCAM_Name, IPCAM_IP, IPCAM_Frame

	# IPCAM_Image = cv2.resize(makeBlackImage(),(1280,720),interpolation=cv2.INTER_CUBIC)
	IPCAM_Image = []
	newTime = datetime.datetime.now()
	
	CAM_INIT_SUCCESS = False
	FIRST_RUN = True
	InitFile = "./config.txt"
	# sendMsg("Please create 'config.txt' file at EXECUTION FILE FOLDER and fill in camera information:")
	# sendMsg("[Username],[Password],[Camera Name],[Camera IP],[Camera FPS]")
	while WINDOWS_IS_ACTIVE:
		if not CAM_INIT_SUCCESS:
			if os.path.isfile(InitFile):
				fp = open(InitFile, "r")
				lines = fp.readlines()
				fp.close()
				if lines == []:
					IPCAM_ConfigStatus = 1
					# print("CONFIG EMPTY!")
				else:
					data = lines[0].split(",")
					if len(data) != 6:
						IPCAM_ConfigStatus = 2
						# print("CONFIG ERROR!")
					else:
						IPCAM_Username = data[0]
						IPCAM_Password = data[1]
						IPCAM_Name = data[2]
						IPCAM_IP = data[3]
						IPCAM_Frame = int(data[4])
						IPCAM_Bar = data[5]
						# str1 = "{},{},{},{},{}".format(IPCAM_Username, IPCAM_Password, IPCAM_Name, IPCAM_IP, IPCAM_Frame)
						# print(str1)
						IPCAM_ConfigStatus = 3
						# print("CONFIG SUCCESS!")
						CAM_INIT_SUCCESS = True
			else:
				IPCAM_ConfigStatus = 0
				# print("NO CONFIG FILE!")
		else:
			if CAM_IS_RUN:
				# print("IPCAM RUN!")
				if FIRST_RUN:
					rtsp = "rtsp://{0}:{1}@{2}:554/{3}".format(IPCAM_Username, IPCAM_Password, IPCAM_IP, IPCAM_Bar) #1920x1080
					cap = cv2.VideoCapture(rtsp)
					ret,frame = cap.read()
					FrameCount = 0
					FIRST_RUN = False

				nowTime = datetime.datetime.now()
				IPCAM_NowTime = datetime.datetime.now()
				if cap.isOpened():
					# print("IPCAM OPEN!")
					ret,frame = cap.read()
					# print("IPCAM GET!")
					# IPCAM_ConfigStatus = 6
				else:
					print("IPCAM NOT OPEN!")
					# sendMsg("Camera Not Open!!")
				
				if frame is not None:
					IPCAM_Image = frame
					FrameCount = FrameCount + 1
					if (nowTime - newTime).seconds > 0:
						IPCAM_FrameCount = FrameCount
						FrameCount = 0
						newTime = datetime.datetime.now()

				else:
					# IPCAM_Image = cv2.resize(makeBlackImage(),(1280,720),interpolation=cv2.INTER_CUBIC)
					IPCAM_Image = []
					# sendMsg("Frame is NULL! Reconnecting...")
					cap = cv2.VideoCapture(rtsp)
					# sendMsg("Setup the IP Camera")
			else:
				# print("NO LINKED!!")
				# IPCAM_Image = cv2.resize(makeBlackImage(),(1280,720),interpolation=cv2.INTER_CUBIC)
				IPCAM_Image = []
