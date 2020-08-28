# 產生影片並錄製
import cv2
import numpy as np
from PIL import Image
import datetime
import logging
import sys
import os
import traceback
import random as rand
import DebugVideo as DBGV

WINDOWS_IS_ACTIVE = True	#UI是否在執行中
SAVE_PAST_DATA = True #儲存上次記錄
SET_VIDEO_PATH = False #是否已設定影片路徑
nowDatePath = './ChiMei_{}/'.format(datetime.datetime.now().strftime("%Y%m%d"))
VideoDir = 'Video_{}/'.format(datetime.datetime.now().strftime("%Y%m%d"))

# IPCAM Information
IPCAM_Name = ""			#攝相機名稱
IPCAM_IP = ""			#攝相機IP
IPCAM_FrameCount = 0	#測試每秒禎數
IPCAM_NewP1 = [0, 0]	#矩形框左上座標點
IPCAM_Image = []		#攝相機影像
IPCAM_FrameSize = [0, 0]#攝相機影像大小
IPCAM_Status = False	#攝相機連上狀態
IPCAM_NowTime = datetime.datetime.now()	#IPCAM時間
Maze_DateTime = datetime.datetime.now() #現在時間

# Maze Button State
Maze_LinkState = False
Maze_StartState = False
Maze_CameraState = False
Maze_SetState = False
Maze_FrameLoadTime = (Maze_DateTime - IPCAM_NowTime).microseconds

# Experiment Information
Exp_Food = [0, 0, 0, 0, 0, 0, 0, 0]	#食物臂
Exp_Disense = ""					#病因
Exp_DisGroup = ""					#病因分組
Exp_DisDay = [False, 0, 0] 			#老鼠病症天數(是否手術, 月, 天)
Exp_RatID = ""						#老鼠ID
Exp_StartTime = None				#實驗啟始時間

# Experiment Data
Data_TargetPos = [0, 0]		#老鼠座標點
Data_ArmInOutPosLine = [
	[[-1, -1], [-1, -1]], [[-1, -1], [-1, -1]], [[-1, -1], [-1, -1]], [[-1, -1], [-1, -1]], 
	[[-1, -1], [-1, -1]], [[-1, -1], [-1, -1]], [[-1, -1], [-1, -1]], [[-1, -1], [-1, -1]], 
	[[-1, -1], [-1, -1]]
] 	#老鼠進出臂線繪製(進1, 進2, 進3, 進4, 進5, 進6, 進7, 進8, 出)
Data_Old_ArmInOutPosLine = [ #舊的進出臂線
	[[-1, -1], [-1, -1]], [[-1, -1], [-1, -1]], [[-1, -1], [-1, -1]], [[-1, -1], [-1, -1]], 
	[[-1, -1], [-1, -1]], [[-1, -1], [-1, -1]], [[-1, -1], [-1, -1]], [[-1, -1], [-1, -1]], 
	[[-1, -1], [-1, -1]]
]
NEW_Data_ArmInOutPosLine = [
	[[-1, -1], [-1, -1]], [[-1, -1], [-1, -1]], [[-1, -1], [-1, -1]], [[-1, -1], [-1, -1]], 
	[[-1, -1], [-1, -1]], [[-1, -1], [-1, -1]], [[-1, -1], [-1, -1]], [[-1, -1], [-1, -1]], 
	[[-1, -1], [-1, -1]]
]
Data_ArmInOutLen = [0, 0, 0, 0, 0, 0, 0, 0, 0] 		#老鼠進出臂線長度(進1, 進2, 進3, 進4, 進5, 進6, 進7, 進8, 出)
Data_ArmInOutDistance = [0, 0, 0, 0, 0, 0, 0, 0, 0]	#老鼠進出臂線距離(進1, 進2, 進3, 進4, 進5, 進6, 進7, 進8, 出)
Data_Route = [] 			#進臂順序
Data_LongTerm = [0, 0, 0, 0, 0, 0, 0, 0] 	#長期工作記憶錯誤
Data_ShortTerm = [0, 0, 0, 0, 0, 0, 0, 0] 	#短期工作記憶錯誤
Data_TotalTerm = [0, 0] 	#總工作記憶錯誤(長期, 短期)
Data_ArmState = 0 			#進出臂狀態
Data_CurrentArm = 0			#當前臂
Data_InLineChange = False	#進臂線有更動
Data_OutLineChange = False	#出臂線有更動

# Previous Data
PastData_RatID = ""				#老鼠ID
PastData_StartTime = None		#實驗啟始時間
PastData_TotalTerm = [0, 0] 	#總工作記憶錯誤(長期, 短期)
PastData_Latency = 0  			#總時間長度

# 白色物體
White_TotalItem = 0			#白色物體總數
White_Contours = []			#白色物體邊緣
White_ContourArea = []		#白色物體面積大小
White_CenterPos = []		#白色物體中心座標
White_PosShowFinish = False #白色物體的點是否皆顯示完成
WOI_Color = [(0,128,230), (0,230,230), (0,230,0), (230,230,0), (230,0,230)]
WOI_Count = 5000

# 檢查點
CheckP_UI = "0"		#UI程式檢查點
CheckP_ICAM = "0"		#影像處理程式檢查點
CheckP_IPCAM = "0"	#IPCAM程式檢查點

NO_RAT = False #是否沒白色物體

FORMAT = '%(asctime)s [%(filename)s] %(levelname)s: %(message)s'
logging.basicConfig(level=logging.WARNING, filename='MazeLog.log', filemode='a', format=FORMAT)

def convert(list):
    return tuple(list)

def makeSingaleColorImage(color): #製造單色圖片(10x10)
	pixels = []
	for i in range(0,10):
		row = []
		for j in range(0,10):
			row.append(color)
		pixels.append(row)
	array = np.array(pixels, dtype=np.uint8)
	newBlack = Image.fromarray(array)
	newBlack = cv2.cvtColor(np.asarray(newBlack),cv2.COLOR_RGB2BGR)  
	return newBlack

def checkVideoDir():
	global nowDatePath, VideoDir
	nowDatePath = './ChiMei_{}/'.format(datetime.datetime.now().strftime("%Y%m%d"))
	VideoDir = 'Video_{}/'.format(datetime.datetime.now().strftime("%Y%m%d"))
	if not os.path.exists(nowDatePath):
		os.mkdir(nowDatePath)
	if not os.path.exists(nowDatePath + VideoDir):
		os.mkdir(nowDatePath + VideoDir)

def Second2Datetime(sec): #秒數轉換成時間
	return int(sec/3600), int((sec%3600)/60), int((sec%3600)%60)

def checkInOutLine(newLine, oldLine): #檢查檢查臂線是否更動
	InLineC = False
	OutLineC = False

	for i in range(len(newLine)):
		if (newLine[i][0][0] != oldLine[i][0][0] or newLine[i][0][1] != oldLine[i][0][1]) or (newLine[i][1][0] != oldLine[i][1][0] or newLine[i][1][1] != oldLine[i][1][1]):
			oldLine[i] = [[newLine[i][0][0], newLine[i][0][1]], [newLine[i][1][0], newLine[i][1][1]]]
			if i == len(newLine) - 1:
				OutLineC = True
			else:
				InLineC = True
	return InLineC, OutLineC, oldLine

def exchangeArmsLine(InOut, changeLine, nowLine, size): #進出臂線轉換
	if not InOut:
		for i in range(len(nowLine)-1):
			changeLine[i] = [[int((nowLine[i][0][0]/480)*size), int((nowLine[i][0][1]/480)*size)], [int((nowLine[i][1][0]/480)*size), int((nowLine[i][1][1]/480)*size)]]
	else:
		i = len(nowLine)-1
		changeLine[i] = [[int((nowLine[i][0][0]/480)*size), int((nowLine[i][0][1]/480)*size)], [int((nowLine[i][1][0]/480)*size), int((nowLine[i][1][1]/480)*size)]]

	return changeLine

def exchangeContours(Contours, size):
	new_Contours = []
	for i in range(len(Contours)):
		# print(len(Contours[i]))
		if len(Contours[i]) == 1:
			if len(Contours[i][0]) != 2:
				print(len(Contours[i][0]))
			# new_Contours.append([Contours[i][0][0], Contours[i][0][1]])
			new_Contours.append([int((Contours[i][0][0]/480)*size), int((Contours[i][0][1]/480)*size)])

	return new_Contours

def randWhiteData(unit):
	global White_ContourArea, White_CenterPos
	White_ContourArea = []	#白色物體面積大小
	White_CenterPos = []	#白色物體中心座標

	for i in range(unit):
		White_ContourArea.append(rand.randint(10,400))
		White_CenterPos.append([rand.randint(0,480),rand.randint(0,480)])

def makeFrameView(frame):
	global IPCAM_NewP1, SAVE_PAST_DATA
	global White_CenterPos, WOI_Color, White_PosShowFinish, White_Contours, White_TotalItem
	global Data_TargetPos, Data_ArmInOutPosLine, NEW_Data_ArmInOutPosLine, Data_InLineChange, Data_OutLineChange, Data_Old_ArmInOutPosLine

	FrameStatus = False
	FrameSize = [0, 0]

	if len(frame) == 0:
		FrameSize = [720, 720]
		frame = makeSingaleColorImage((0, 0, 128))
		frame = cv2.resize(frame, (FrameSize[0], FrameSize[1]), interpolation=cv2.INTER_CUBIC)
		cv2.putText(frame, "NO SIGNAL", (147, 360), cv2.FONT_HERSHEY_DUPLEX, 2.5, (255,255,255), 2, cv2.LINE_AA)
		FrameStatus = False
		newFrameSize = (680, 680)
	else:
		FrameStatus = True
		FrameSize = [frame.shape[1], frame.shape[0]]
		newP1 = IPCAM_NewP1
		newP2 = [newP1[0] + FrameSize[1], newP1[1] + FrameSize[1]]
		frame = frame[newP1[1]:newP2[1], newP1[0]:newP2[0]]

		newFrameSize = (int(FrameSize[1] * (680/FrameSize[1])), int(FrameSize[1] * (680/FrameSize[1])))

		Data_InLineChange, Data_OutLineChange, Data_Old_ArmInOutPosLine = checkInOutLine(Data_ArmInOutPosLine, Data_Old_ArmInOutPosLine)
		if Data_InLineChange:
			NEW_Data_ArmInOutPosLine = exchangeArmsLine(False, NEW_Data_ArmInOutPosLine, Data_ArmInOutPosLine, FrameSize[1])
		if Data_OutLineChange:
			NEW_Data_ArmInOutPosLine = exchangeArmsLine(True, NEW_Data_ArmInOutPosLine, Data_ArmInOutPosLine, FrameSize[1])

		newPos = (int(Data_TargetPos[0] * (FrameSize[1]/480)), int(Data_TargetPos[1] * (FrameSize[1]/480)))

		White_PosShowFinish = False
		NEW_White_Contours = []
		NEW_newPos = []
		White_TotalItem = len(White_CenterPos)
		for i in range(White_TotalItem):
			# White_Contours[i] = exchangeContours(White_Contours[i], FrameSize[1])
			NEW_White_Contours.append(exchangeContours(White_Contours[i], FrameSize[1])) #計算邊緣座標點
			NEW_newPos.append((int(White_CenterPos[i][0] * (FrameSize[1]/480)), int(White_CenterPos[i][1] * (FrameSize[1]/480))))


		if not NO_RAT:
			cv2.circle(frame, newPos, 12, (0,0,255), -1)
			for i in range(len(White_CenterPos)):
				if i < 5:
					pointColor = WOI_Color[i]
				else:
					pointColor = (64,64,64)
				# newPos = (int(White_CenterPos[i][0] * (FrameSize[1]/480)), int(White_CenterPos[i][1] * (FrameSize[1]/480)))
				# print(White_Contours[i])
				# cv2.drawContours(frame, White_Contours[i], -1, pointColor, 3)
				cv2.polylines(frame, np.array([NEW_White_Contours[i]]), True, pointColor, 2)

				cv2.circle(frame, NEW_newPos[i], 9, (255,255,255), -1)
				cv2.circle(frame, NEW_newPos[i], 8, pointColor, -1)
		White_PosShowFinish = True

		for i in range(len(NEW_Data_ArmInOutPosLine)):
			cv2.line(frame, convert(NEW_Data_ArmInOutPosLine[i][0]), convert(NEW_Data_ArmInOutPosLine[i][1]), (0, 0, 255), 3)

	frame = cv2.resize(frame, newFrameSize, interpolation=cv2.INTER_CUBIC)

	return FrameStatus, FrameSize, frame

def makeDashBoard():
	global Maze_DateTime
	global IPCAM_Name, IPCAM_IP, IPCAM_FrameCount, IPCAM_FrameSize, IPCAM_NewP1, IPCAM_NowTime, IPCAM_Status
	global Maze_StartState, Maze_LinkState, Maze_SetState, Maze_CameraState, Maze_FrameLoadTime
	global Exp_Disense, Exp_DisGroup, Exp_DisDay, Exp_Food, Exp_RatID, Exp_StartTime
	global Data_ArmInOutLen, Data_ArmInOutDistance, Data_TargetPos, Data_LongTerm, Data_ShortTerm, Data_TotalTerm, Data_Route, Data_ArmState, Data_CurrentArm, Data_ArmInOutPosLine
	global PastData_RatID, PastData_TotalTerm, PastData_StartTime, PastData_Latency
	global White_Contours, White_ContourArea, White_CenterPos, WOI_Count, White_PosShowFinish, White_TotalItem
	global CheckP_UI, CheckP_ICAM, CheckP_IPCAM

	#欄位初始點
	BasicPos1 = 10 	#第一欄
	BasicPos2 = 250	#第二欄
	BasicPos3 = 490	#第三欄

	#字體顏色
	unSetFontColor = (128, 128, 128)

	result = makeSingaleColorImage((0,0,0))
	result = cv2.resize(result, (720, 680), interpolation=cv2.INTER_CUBIC)
	cv2.putText(result, "DateTime: {}".format(Maze_DateTime.strftime("%Y%m%d %H:%M:%S")), (BasicPos1, 20), cv2.FONT_HERSHEY_DUPLEX, 0.5, (255,255,255), 0, cv2.LINE_AA)
	cv2.putText(result, IPCAM_Name, (BasicPos1, 40), cv2.FONT_HERSHEY_DUPLEX, 0.5, (255,255,255), 0, cv2.LINE_AA)
	
	# IPCAM Information
	cv2.putText(result, "=IPCAM Info=", (BasicPos1, 60), cv2.FONT_HERSHEY_DUPLEX, 0.5, (0,255,255), 0, cv2.LINE_AA)
	cv2.putText(result, "-IP: {}".format(IPCAM_IP), (BasicPos1, 80), cv2.FONT_HERSHEY_DUPLEX, 0.5, (255,255,255), 0, cv2.LINE_AA)
	cv2.putText(result, "-FrameSize: {}".format(IPCAM_FrameSize), (BasicPos1, 100), cv2.FONT_HERSHEY_DUPLEX, 0.5, (255,255,255), 0, cv2.LINE_AA)
	cv2.putText(result, "-FrameCount: {}".format(IPCAM_FrameCount), (BasicPos1, 120), cv2.FONT_HERSHEY_DUPLEX, 0.5, (255,255,255), 0, cv2.LINE_AA)
	cv2.putText(result, "-newP1: {}".format(IPCAM_NewP1), (BasicPos1, 140), cv2.FONT_HERSHEY_DUPLEX, 0.5, (255,255,255), 0, cv2.LINE_AA)
	cv2.putText(result, "-Status:", (BasicPos1, 160), cv2.FONT_HERSHEY_DUPLEX, 0.5, (255,255,255), 0, cv2.LINE_AA)
	if IPCAM_Status:
		cv2.putText(result, "Connect", (BasicPos1 + 75, 160), cv2.FONT_HERSHEY_DUPLEX, 0.5, (0,255,0), 0, cv2.LINE_AA)
	else:
		cv2.putText(result, "Unlink", (BasicPos1 + 75, 160), cv2.FONT_HERSHEY_DUPLEX, 0.5, (0,0,255), 0, cv2.LINE_AA)

	# Maze State
	cv2.putText(result, "=Maze Btn State=", (BasicPos2, 60), cv2.FONT_HERSHEY_DUPLEX, 0.5, (0,255,255), 0, cv2.LINE_AA)
	cv2.putText(result, "-Link:", (BasicPos2, 80), cv2.FONT_HERSHEY_DUPLEX, 0.5, (255,255,255), 0, cv2.LINE_AA)
	cv2.putText(result, "-Start:", (BasicPos2, 100), cv2.FONT_HERSHEY_DUPLEX, 0.5, (255,255,255), 0, cv2.LINE_AA)
	cv2.putText(result, "-Camera:", (BasicPos2, 120), cv2.FONT_HERSHEY_DUPLEX, 0.5, (255,255,255), 0, cv2.LINE_AA)
	cv2.putText(result, "-Setting:", (BasicPos2, 140), cv2.FONT_HERSHEY_DUPLEX, 0.5, (255,255,255), 0, cv2.LINE_AA)
	loadSec = Maze_FrameLoadTime/pow(10,6)
	if loadSec < 1.0:
		cv2.putText(result, "-LoadTime: < 1.0s", (BasicPos2, 160), cv2.FONT_HERSHEY_DUPLEX, 0.5, (255,255,255), 0, cv2.LINE_AA)
	else:
		cv2.putText(result, "-LoadTime: %.1fs" %(loadSec), (BasicPos2, 160), cv2.FONT_HERSHEY_DUPLEX, 0.5, (255,255,255), 0, cv2.LINE_AA)
	MazeBtnArr = [Maze_LinkState, Maze_StartState, Maze_CameraState, Maze_SetState]
	MazeBtnLeft = [BasicPos2 + 55, BasicPos2 + 60, BasicPos2 + 85, BasicPos2 + 80]
	for i in range(len(MazeBtnArr)):
		if MazeBtnArr[i]:
			cv2.putText(result, "True", (MazeBtnLeft[i], 80 + 20*i), cv2.FONT_HERSHEY_DUPLEX, 0.5, (0,255,0), 0, cv2.LINE_AA)
		else:
			cv2.putText(result, "False", (MazeBtnLeft[i], 80 + 20*i), cv2.FONT_HERSHEY_DUPLEX, 0.5, (0,0,255), 0, cv2.LINE_AA)

	# Experiment Information
	cv2.putText(result, "=Experiment Information=", (BasicPos1, 200), cv2.FONT_HERSHEY_DUPLEX, 0.5, (0,255,255), 0, cv2.LINE_AA)
	cv2.putText(result, "-TargetPos: {}".format(Data_TargetPos), (BasicPos2, 200), cv2.FONT_HERSHEY_DUPLEX, 0.5, (255,255,255), 0, cv2.LINE_AA)
	if Maze_StartState:
		cv2.putText(result, "-Food: {}".format(Exp_Food), (BasicPos1, 220), cv2.FONT_HERSHEY_DUPLEX, 0.5, (255,255,255), 0, cv2.LINE_AA)
		cv2.putText(result, "-Disence: {}".format(Exp_Disense), (BasicPos1, 240), cv2.FONT_HERSHEY_DUPLEX, 0.5, (255,255,255), 0, cv2.LINE_AA)
		cv2.putText(result, "-DisGroup: {}".format(Exp_DisGroup), (BasicPos2, 240), cv2.FONT_HERSHEY_DUPLEX, 0.5, (255,255,255), 0, cv2.LINE_AA)
		cv2.putText(result, "-ArmState:", (BasicPos1, 280), cv2.FONT_HERSHEY_DUPLEX, 0.5, (255,255,255), 0, cv2.LINE_AA)
		if Data_ArmState == 0:
			cv2.putText(result, "Not Entry", (BasicPos1 + 100, 280), cv2.FONT_HERSHEY_DUPLEX, 0.5, (0,0,255), 0, cv2.LINE_AA)
		elif Data_ArmState == 1:
			cv2.putText(result, "Entry", (BasicPos1 + 100, 280), cv2.FONT_HERSHEY_DUPLEX, 0.5, (0,255,0), 0, cv2.LINE_AA)
		else:
			cv2.putText(result, "%d" %(Data_ArmState), (BasicPos1, 280), cv2.FONT_HERSHEY_DUPLEX, 0.5, (255,255,255), 0, cv2.LINE_AA)
		cv2.putText(result, "-RatID: {}".format(Exp_RatID), (BasicPos1, 300), cv2.FONT_HERSHEY_DUPLEX, 0.5, (255,255,255), 0, cv2.LINE_AA)

		if Exp_DisDay[0]:
			cv2.putText(result, "-DisType: PastOP", (BasicPos1, 260), cv2.FONT_HERSHEY_DUPLEX, 0.5, (255,255,255), 0, cv2.LINE_AA)
		else:
			cv2.putText(result, "-DisType: PreOP" , (BasicPos1, 260), cv2.FONT_HERSHEY_DUPLEX, 0.5, (255,255,255), 0, cv2.LINE_AA)
		cv2.putText(result, "-DisDay: %02dM %02dD" %(Exp_DisDay[1], Exp_DisDay[2]), (BasicPos2, 260), cv2.FONT_HERSHEY_DUPLEX, 0.5, (255,255,255), 0, cv2.LINE_AA)

		nowLatency = Second2Datetime((Maze_DateTime - Exp_StartTime).seconds)
		cv2.putText(result, "-Latency: %02d:%02d:%02d" %(nowLatency), (BasicPos2, 300), cv2.FONT_HERSHEY_DUPLEX, 0.5, (255,255,255), 0, cv2.LINE_AA)
		cv2.putText(result, "-CurrentArm:", (BasicPos2, 280), cv2.FONT_HERSHEY_DUPLEX, 0.5, (255,255,255), 0, cv2.LINE_AA)
		if Data_CurrentArm == 0:
			cv2.putText(result, "None", (BasicPos2 + 120, 280), cv2.FONT_HERSHEY_DUPLEX, 0.5, (255,255,255), 0, cv2.LINE_AA)
		else:
			cv2.putText(result, "Arm%d" %(Data_CurrentArm), (BasicPos2 + 120, 280), cv2.FONT_HERSHEY_DUPLEX, 0.5, (0,255,255), 0, cv2.LINE_AA)
	else:
		cv2.putText(result, "-Food: None", (BasicPos1, 220), cv2.FONT_HERSHEY_DUPLEX, 0.5, unSetFontColor, 0, cv2.LINE_AA)
		cv2.putText(result, "-Disence: None", (BasicPos1, 240), cv2.FONT_HERSHEY_DUPLEX, 0.5, unSetFontColor, 0, cv2.LINE_AA)
		cv2.putText(result, "-DisType: None", (BasicPos1, 260), cv2.FONT_HERSHEY_DUPLEX, 0.5, unSetFontColor, 0, cv2.LINE_AA)
		cv2.putText(result, "-ArmState: None", (BasicPos1, 280), cv2.FONT_HERSHEY_DUPLEX, 0.5, unSetFontColor, 0, cv2.LINE_AA)
		cv2.putText(result, "-RatID: None", (BasicPos1, 300), cv2.FONT_HERSHEY_DUPLEX, 0.5, unSetFontColor, 0, cv2.LINE_AA)

		cv2.putText(result, "-DisGroup: None", (BasicPos2, 240), cv2.FONT_HERSHEY_DUPLEX, 0.5, unSetFontColor, 0, cv2.LINE_AA)
		cv2.putText(result, "-DisDay: None", (BasicPos2, 260), cv2.FONT_HERSHEY_DUPLEX, 0.5, unSetFontColor, 0, cv2.LINE_AA)
		cv2.putText(result, "-CurrentArm: None", (BasicPos2, 280), cv2.FONT_HERSHEY_DUPLEX, 0.5, unSetFontColor, 0, cv2.LINE_AA)
		cv2.putText(result, "-Latency: None", (BasicPos2, 300), cv2.FONT_HERSHEY_DUPLEX, 0.5, unSetFontColor, 0, cv2.LINE_AA)

	# Experiment Data
	TableColPos = 360
	TableColLen = 21
	TableRowPos = [BasicPos1, BasicPos1 + 60, BasicPos1 + 130, BasicPos1 + 200, BasicPos1 + 300]
	TableTitle = ['', 'LTerm', 'STerm', 'ArmInLen', 'ArmInDis']
	for i in range(len(TableRowPos)):
		cv2.putText(result, TableTitle[i], (TableRowPos[i], TableColPos - 20), cv2.FONT_HERSHEY_DUPLEX, 0.5, (0,255,255), 0, cv2.LINE_AA)
	for i in range(8):
		if Data_ArmInOutDistance[i] == min(Data_ArmInOutDistance[0:7]) and Data_ArmInOutDistance[i] < 150 and Maze_StartState:
			AIOD_Color = (0,128,255)
		else:
			AIOD_Color = (255,255,255)
		cv2.putText(result, "Arm%d" %(i+1), (TableRowPos[0], TableColPos + i*TableColLen), cv2.FONT_HERSHEY_DUPLEX, 0.5, (0,255,255), 0, cv2.LINE_AA)
		cv2.putText(result, "%3d" %(Data_LongTerm[i]), (TableRowPos[1] + 10, TableColPos + i*TableColLen), cv2.FONT_HERSHEY_DUPLEX, 0.5, (255,255,255), 0, cv2.LINE_AA)
		cv2.putText(result, "%3d" %(Data_ShortTerm[i]), (TableRowPos[2] + 10, TableColPos + i*TableColLen), cv2.FONT_HERSHEY_DUPLEX, 0.5, (255,255,255), 0, cv2.LINE_AA)
		cv2.putText(result, "%4.2f" %(Data_ArmInOutLen[i]), (TableRowPos[3] + 20, TableColPos + i*TableColLen), cv2.FONT_HERSHEY_DUPLEX, 0.5, (255,255,255), 0, cv2.LINE_AA)
		cv2.putText(result, "%4.2f" %(Data_ArmInOutDistance[i]), (TableRowPos[4] + 20, TableColPos + i*TableColLen), cv2.FONT_HERSHEY_DUPLEX, 0.5, AIOD_Color, 0, cv2.LINE_AA)
	cv2.putText(result, "ArmOutLen:", (TableRowPos[0], TableColPos + 8*TableColLen), cv2.FONT_HERSHEY_DUPLEX, 0.5, (0,255,255), 0, cv2.LINE_AA)
	cv2.putText(result, "%4.2f" %(Data_ArmInOutLen[8]), (TableRowPos[0] + 120, TableColPos + 8*TableColLen), cv2.FONT_HERSHEY_DUPLEX, 0.5, (255,255,255), 0, cv2.LINE_AA)
	cv2.putText(result, "ArmOutDis:", (TableRowPos[3], TableColPos + 8*TableColLen), cv2.FONT_HERSHEY_DUPLEX, 0.5, (0,255,255), 0, cv2.LINE_AA)
	cv2.putText(result, "%4.2f" %(Data_ArmInOutDistance[8]), (TableRowPos[3] + 120, TableColPos + 8*TableColLen), cv2.FONT_HERSHEY_DUPLEX, 0.5, (255,255,255), 0, cv2.LINE_AA)
	
	cv2.putText(result, "Total LongTerm:", (TableRowPos[0], TableColPos + 9*TableColLen), cv2.FONT_HERSHEY_DUPLEX, 0.5, (0,255,255), 0, cv2.LINE_AA)
	cv2.putText(result, "%3d" %(Data_TotalTerm[0]), (TableRowPos[0] + 140, TableColPos + 9*TableColLen), cv2.FONT_HERSHEY_DUPLEX, 0.5, (255,255,255), 0, cv2.LINE_AA)
	cv2.putText(result, "Total ShortTerm:", (TableRowPos[3], TableColPos + 9*TableColLen), cv2.FONT_HERSHEY_DUPLEX, 0.5, (0,255,255), 0, cv2.LINE_AA)
	cv2.putText(result, "%3d" %(Data_TotalTerm[1]), (TableRowPos[3] + 140, TableColPos + 9*TableColLen), cv2.FONT_HERSHEY_DUPLEX, 0.5, (255,255,255), 0, cv2.LINE_AA)

	# Experiment Route
	RouteColPos = TableColPos + 11*TableColLen
	RouteColLen = 20
	RouteRowPos = 21
	RouteNewLine = 20
	cv2.putText(result, "=Entry Route=", (BasicPos1, RouteColPos - 22), cv2.FONT_HERSHEY_DUPLEX, 0.5, (0,255,255), 0, cv2.LINE_AA)
	# Data_Route = []
	# for i in range(50):
	# 	Data_Route.append(rand.randint(1,8))
	for i in range(len(Data_Route)):
		cv2.putText(result, str(Data_Route[i]), (BasicPos1 + RouteRowPos*(i%RouteNewLine), RouteColPos + RouteColLen*int(i/RouteNewLine)), cv2.FONT_HERSHEY_DUPLEX, 0.5, (255,255,255), 0, cv2.LINE_AA)

	# Previous Exp Data
	cv2.putText(result, "=Previous Data=", (BasicPos3, 60), cv2.FONT_HERSHEY_DUPLEX, 0.5, (0,128,255), 0, cv2.LINE_AA)
	if Maze_StartState:
		PED_FColor = unSetFontColor
	else:
		PED_FColor = (255,255,255)
	cv2.putText(result, "RatID : {}".format(PastData_RatID), (BasicPos3, 80), cv2.FONT_HERSHEY_DUPLEX, 0.5, PED_FColor, 0, cv2.LINE_AA)
	if PastData_StartTime is not None:
		cv2.putText(result, "StartTime : {}".format(PastData_StartTime.strftime("%m%d %H:%M:%S")), (BasicPos3, 100), cv2.FONT_HERSHEY_DUPLEX, 0.5, PED_FColor, 0, cv2.LINE_AA)
	else:
		cv2.putText(result, "StartTime : None", (BasicPos3, 100), cv2.FONT_HERSHEY_DUPLEX, 0.5, PED_FColor, 0, cv2.LINE_AA)
	nowLatency = Second2Datetime(PastData_Latency)
	cv2.putText(result, "Latency: %02d:%02d:%02d" %(nowLatency), (BasicPos3, 120), cv2.FONT_HERSHEY_DUPLEX, 0.5, PED_FColor, 0, cv2.LINE_AA)
	cv2.putText(result, "Total LongTerm: %2d" %(PastData_TotalTerm[0]), (BasicPos3, 140), cv2.FONT_HERSHEY_DUPLEX, 0.5, PED_FColor, 0, cv2.LINE_AA)
	cv2.putText(result, "Total ShortTerm: %2d" %(PastData_TotalTerm[1]), (BasicPos3, 160), cv2.FONT_HERSHEY_DUPLEX, 0.5, PED_FColor, 0, cv2.LINE_AA)
	
	# White Object Information
	cv2.putText(result, "=White Object Info=", (BasicPos3, 200), cv2.FONT_HERSHEY_DUPLEX, 0.5, (0,255,255), 0, cv2.LINE_AA)
	cv2.putText(result, "Total Item: %d" %(White_TotalItem), (BasicPos3, 220), cv2.FONT_HERSHEY_DUPLEX, 0.5, (255,255,255), 0, cv2.LINE_AA)
	WOI_ColLen = 65
	# if WOI_Count < 500:
	# 	WOI_Count = WOI_Count + 1
	# else:
	# 	randWhiteData(10)
	# 	WOI_Count = 0
	White_PosShowFinish = False
	for i in range(len(WOI_Color)):
		if i < len(White_ContourArea):
			cv2.putText(result, "Index: %d" %(i), (BasicPos3, 240 + WOI_ColLen*i), cv2.FONT_HERSHEY_DUPLEX, 0.5, WOI_Color[i], 0, cv2.LINE_AA)
			cv2.putText(result, "CenterPos: [%d,%d]" %(White_CenterPos[i][0],White_CenterPos[i][1]), (BasicPos3, 260 + WOI_ColLen*i), cv2.FONT_HERSHEY_DUPLEX, 0.5, WOI_Color[i], 0, cv2.LINE_AA)
			cv2.putText(result, "ContourArea: %d" %(White_ContourArea[i]), (BasicPos3, 280 + WOI_ColLen*i), cv2.FONT_HERSHEY_DUPLEX, 0.5, WOI_Color[i], 0, cv2.LINE_AA)
		else:
			cv2.putText(result, "Index: None", (BasicPos3, 240 + WOI_ColLen*i), cv2.FONT_HERSHEY_DUPLEX, 0.5, unSetFontColor, 0, cv2.LINE_AA)
			cv2.putText(result, "CenterPos: [%d,%d]" %(0,0), (BasicPos3, 260 + WOI_ColLen*i), cv2.FONT_HERSHEY_DUPLEX, 0.5, unSetFontColor, 0, cv2.LINE_AA)
			cv2.putText(result, "ContourArea: None", (BasicPos3, 280 + WOI_ColLen*i), cv2.FONT_HERSHEY_DUPLEX, 0.5, unSetFontColor, 0, cv2.LINE_AA)
	White_PosShowFinish = True

	# Function Check Point
	checkBasicPos = 570
	cv2.putText(result, "=Check Point=", (BasicPos3, checkBasicPos), cv2.FONT_HERSHEY_DUPLEX, 0.5, (0,255,255), 0, cv2.LINE_AA)
	cv2.putText(result, "MMT-UI:", (BasicPos3, checkBasicPos + 20), cv2.FONT_HERSHEY_DUPLEX, 0.5, (255,255,255), 0, cv2.LINE_AA)
	cv2.putText(result, "ICAM:", (BasicPos3, checkBasicPos + 40), cv2.FONT_HERSHEY_DUPLEX, 0.5, (255,255,255), 0, cv2.LINE_AA)
	cv2.putText(result, "IPCAM:", (BasicPos3, checkBasicPos + 60), cv2.FONT_HERSHEY_DUPLEX, 0.5, (255,255,255), 0, cv2.LINE_AA)
	cv2.putText(result, str(CheckP_UI), (BasicPos3 + 70, checkBasicPos + 20), cv2.FONT_HERSHEY_DUPLEX, 0.5, (255,255,255), 0, cv2.LINE_AA)
	cv2.putText(result, str(CheckP_ICAM), (BasicPos3 + 70, checkBasicPos + 40), cv2.FONT_HERSHEY_DUPLEX, 0.5, (255,255,255), 0, cv2.LINE_AA)
	cv2.putText(result, str(CheckP_IPCAM), (BasicPos3 + 70, checkBasicPos + 60), cv2.FONT_HERSHEY_DUPLEX, 0.5, (255,255,255), 0, cv2.LINE_AA)

	return result

def DBGV_Main(): #DBGV主程式
	global WINDOWS_IS_ACTIVE, Maze_DateTime, Maze_FrameLoadTime, SAVE_PAST_DATA, SET_VIDEO_PATH
	global IPCAM_Image, IPCAM_Status, IPCAM_FrameSize, IPCAM_IP, IPCAM_FrameCount, IPCAM_NewP1, IPCAM_Name
	global Maze_StartState, Maze_LinkState, Maze_SetState, Maze_CameraState, Maze_FrameLoadTime
	global Data_TotalTerm, Exp_StartTime, Exp_RatID
	global PastData_RatID, PastData_TotalTerm, PastData_StartTime, PastData_Latency
	global VideoDir, nowDatePath, DBGV ,FrameView

	try:
		videoTime = datetime.datetime.now()
		while WINDOWS_IS_ACTIVE:
			Maze_DateTime = datetime.datetime.now()
			Maze_FrameLoadTime = (Maze_DateTime - IPCAM_NowTime).microseconds

			IPCAM_Status, IPCAM_FrameSize, FrameView = makeFrameView(IPCAM_Image)
			DashBoard = makeDashBoard()
			TotalBoard = np.hstack([DashBoard, FrameView])

			if not IPCAM_Status:
				IPCAM_Name = ""			#攝相機名稱
				IPCAM_IP = ""			#攝相機IP
				IPCAM_FrameCount = 0	#測試每秒禎數
				IPCAM_NewP1 = [0, 0]	#矩形框左上座標點
			
			if Maze_StartState:
				SAVE_PAST_DATA = False
			else:
				if not SAVE_PAST_DATA:
					PastData_RatID = Exp_RatID
					if Exp_StartTime is not None:
						PastData_StartTime = Exp_StartTime
						PastData_Latency = (Maze_DateTime - Exp_StartTime).seconds
					PastData_TotalTerm = [Data_TotalTerm[0], Data_TotalTerm[1]]
					SAVE_PAST_DATA = True

			if SET_VIDEO_PATH:
				if (Maze_DateTime - videoTime).seconds > 6000:
					VideoOut.release()
					SET_VIDEO_PATH = False
				else:
					VideoOut.write(TotalBoard)
			else:
				checkVideoDir() #影片資料夾檢查
				videoFullName = "{}{}_{}.avi".format(nowDatePath + VideoDir, 'ChiMei', datetime.datetime.now().strftime("%Y-%m-%d %H-%M-%S"))
				VideoOut = cv2.VideoWriter(videoFullName,cv2.VideoWriter_fourcc(*'DIVX'), 30, (TotalBoard.shape[1], TotalBoard.shape[0]))
				videoTime = datetime.datetime.now()
				SET_VIDEO_PATH = True

			# if Maze_StartState:
			# 	print(Data_ArmInOutPosLine)
			# print(Data_ArmInOutPosLine)



			cv2.imshow("DashBoard Video", TotalBoard)
			cv2.waitKey(1)

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
