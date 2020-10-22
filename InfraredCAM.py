#========程式匯入區========
import cv2
import numpy as np
from PIL import Image #<= 這個是贈品需要匯入的東西
import time
import math
from datetime import datetime
import os
import csv
import winsound
import threading
import IPCAM_Frame as IPCAM
import DebugVideo as DBGV
import logging
import sys
import traceback
import shutil

FORMAT = '%(asctime)s [%(filename)s] %(levelname)s: %(message)s'
logging.basicConfig(level=logging.WARNING, filename='MazeLog.log', filemode='a', format=FORMAT)
fistimeinline = True #第一次跑進臂線判斷
Inlinepoint1 = []	#八個進臂線座標點1
Inlinepoint2 = []	#八個進臂線座標點2
Inlinepoint_long = [0,0,0,0,0,0,0,0,0] #八個臂的進臂線長
dangchianjiuli = [0,0,0,0,0,0,0,0,0]  #八個進壁線距離

#========純副程式區========
def writeData2CSV(fileName, type_, dataRow): #寫入CSV檔
	with open(fileName, type_, newline='') as csvfile:
		# 建立 CSV 檔寫入器
		writer = csv.writer(csvfile)

		# 寫入一列資料
		writer.writerow(dataRow) 
def readCSV2ARME(filename): #讀取八壁32點座標
	w = []
	with open('ARMS_LINE.csv',newline='') as csvfile:
		rows = csv.reader(csvfile,  delimiter=',')
		for row in rows: # for x in range(0,len(rows)):
			for x in range(int(len(row)/2)):
				w.append([int(row[x*2]), int(row[x*2 + 1])])
	# print(w)
	return w

def readCSV2List(fileName): #讀取CSV檔
	AllData = []
	with open(fileName, newline='') as csvfile:
	  # 以冒號分隔欄位，讀取檔案內容
	  rows = csv.reader(csvfile, delimiter=',')

	  for row in rows:
	    AllData.append(row)

	return AllData

def listAllSame(list1, list2): #檢查兩陣列是否完全一樣
	if(len(list1) != len(list2)):
		return False
	else:
		for i in range(0,len(list1)):
			if list1[i] != list2[i]:
				return False
		return True

def Second2Datetime(sec): #秒數轉換成時間
	return int(sec/3600), int((sec%3600)/60), int((sec%3600)%60)
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

#其他跟迷宮程式沒相關的都可以擺在這裡

#========主要類別撰寫區========
#類別內所有的[變數/副程式INPUT第一個變數/呼叫副程式的時候]都要加"self"，代表要互叫這個類別內的變數
class InfraredCAM:
	def __init__(self):
		self.IPCAM = IPCAM
		self.DBGV = DBGV

		self.myTime = datetime.now()
		# self.myTimeMsec = int(self.myTime.strftime("%S"))
		self.myTimeMsec = int(self.myTime.strftime("%f")[:2])
		self.nowSec = int(self.myTime.strftime("%S"))
		self.RouteArrFlag = 0
		self.myRouteArr = []
		self.IPCAM = IPCAM

		#變數：狀態變數(這些變數[由UI端傳來的]狀態變數)
		self.WINDOWS_IS_ACTIVE = True #UI狀態
		self.MAZE_IS_RUN = False #當前系統是否在執行
		self.OPEN_CAMERA_WINDOW = False #影像視窗狀態
		self.CAM_IS_CONN = False #當前鏡頭是否連線
		self.CAM_IS_RUN = False #當前相機程式是否在執行

		#變數：迷宮相關變數(這些變數[由UI端傳來的]迷宮相關變數)
		self.RatID = "" #老鼠編號
		self.TotalFood = 0 #總食物個數
		self.Food = [] #存放食物在哪臂

		#變數：迷宮相關變數(這些[都要傳到UI端]讓它知道的)
		self.ARM_UNIT = 8 #迷宮臂數
		self.ARM_LINE_DISTANCE = 65/46  #老鼠進臂線距離
		self.ARMS_IN_LINE = []
		self.ViewSize = (480, 480) #虛擬視窗顯示大小
		self.TargetPos = [-1, -1] #目標變數
		self.TargetPos_All = [] #一次抓取到的所有白色物體座標
		self.ARMS_POS = readCSV2ARME("ARMS_LINE.csv")
		self.ARMS_LINE = [
			[self.ARMS_POS[0],self.ARMS_POS[1],self.ARMS_POS[3],self.ARMS_POS[2]],
			[self.ARMS_POS[4],self.ARMS_POS[5],self.ARMS_POS[7],self.ARMS_POS[6]],
			[self.ARMS_POS[8],self.ARMS_POS[9],self.ARMS_POS[11],self.ARMS_POS[10]],
			[self.ARMS_POS[12],self.ARMS_POS[13],self.ARMS_POS[15],self.ARMS_POS[14]],
			[self.ARMS_POS[16],self.ARMS_POS[17],self.ARMS_POS[19],self.ARMS_POS[18]],
			[self.ARMS_POS[20],self.ARMS_POS[21],self.ARMS_POS[23],self.ARMS_POS[22]],
			[self.ARMS_POS[24],self.ARMS_POS[25],self.ARMS_POS[27],self.ARMS_POS[26]],
			[self.ARMS_POS[28],self.ARMS_POS[29],self.ARMS_POS[31],self.ARMS_POS[30]],
			]
		self.Mouse_coordinates = []  #老鼠路徑座標
		self.MASK_POS = np.array(self.ARMS_POS)
		self.Route = [] #進臂順序
		self.ShortTerm = [] #短期記憶陣列
		self.LongTerm = [] #長期記憶陣列
		self.Latency = 0 #總時間長度

		self.food1 = []  #有食物的臂判斷結束用
		self.foodtest = [] #長期工作記憶基準
		#變數：迷宮相關變數(這些[不用傳給UI端]但這個程式應該用的上)
		self.InLineGate1 = [] #進入門檻陣列
		self.InLineGate2 = []
		self.OutLineGate = [] #退出門檻陣列
		self.TotalShortTerm = 0 #總短期記憶
		self.TotalLongTerm = 0 #總長期記憶
		#然後其他你有需要的變數就再自己加
		self.WIDTH = 640
		self.HEIGHT = int(self.WIDTH*(9/16))  #1080
		self.MID_POS = [520, 540]
		self.SegRate = (4/11)
		# self.newP1 = (int(self.MID_POS[0]-int(self.HEIGHT)/2),0)
		# self.newP1 = (250,0)
		self.newP1 = [320,0]
		# self.newP2 = (int(self.MID_POS[0]+int(self.HEIGHT/2)),int(self.HEIGHT))
		# self.newP2 = (970,720)
		self.newP2 = [self.newP1[0] + self.HEIGHT, self.newP1[1] + self.HEIGHT]
		self.O = np.array([[1,1,1,1,1],
	 			 [1,1,1,1,1],
				 [1,1,1,1,1],
				 [1,1,1,1,1],
				 [1,1,1,1,1]], dtype="uint8")
		self.oo = np.ones([10,10])
		self.READ_FOOD = False #第一次讀取哪壁有食物
		self.frequency = []  #進臂次數
		self.NOW_STATUS = 0 #進臂or出臂
		self.dangchianbi = 0
		self.rat_XY = [] #放至白色物體外圍座標點
		self.timestart = datetime.now() #起始時間

		self.RR2C = []
		self.RR2C_Time = datetime.now()
		self.RR2C_FirstTime = True

		#實驗設定變數統整
		self.Rec_UserName = "" #操作系統的使用者名稱
		self.OperaType = "" #目前使用模式(訓練期/正式實驗期)
		self.DiseaseType = "" #老鼠病症組別
		self.DisGroupType = "" #老鼠病症組別復鍵(含 健康、無復健 等)
		self.DisDays = [False, -1, -1] #老鼠病症天數(是否手術, 月, 天)
		self.SingleFileName = "" #固定檔名
		self.CSVfilePath = '' #CSV路徑
							

	#========其他的副程式========
	def checkSaveDirPath(self): #檢查儲存路徑
		self.DBGV.CheckP_ICAM = 1044
		nowDatePath = './ChiMei_{}/'.format(datetime.now().strftime("%Y%m%d"))
		RecNamePath = "{}/".format(self.Rec_UserName)
		DiseaseTypePath = '%s(%s_%02d_%02d)/' %(self.DiseaseType, self.OperaType, self.DisDays[1], self.DisDays[2])
		CSV_Path = 'CSV_{}({})/'.format(self.DiseaseType, datetime.now().strftime("%Y%m%d"))
		IMG_Path = 'IMG_{}({})/'.format(self.DiseaseType, datetime.now().strftime("%Y%m%d"))
		self.DBGV.CheckP_ICAM = 1045
		if not os.path.exists(nowDatePath):
			os.mkdir(nowDatePath)
		if not os.path.exists(nowDatePath + RecNamePath):
			os.mkdir(nowDatePath + RecNamePath)	
		if not os.path.exists(nowDatePath + RecNamePath + DiseaseTypePath):
			os.mkdir(nowDatePath + RecNamePath + DiseaseTypePath)
		if not os.path.exists(nowDatePath + RecNamePath + DiseaseTypePath + CSV_Path):
			os.mkdir(nowDatePath + RecNamePath + DiseaseTypePath + CSV_Path)
		if not os.path.exists(nowDatePath + RecNamePath + DiseaseTypePath + IMG_Path):
			os.mkdir(nowDatePath + RecNamePath + DiseaseTypePath + IMG_Path)

	def recordRoute2CSV(self):
		self.DBGV.CheckP_ICAM = 1046
		DiseaseTypePath = '%s(%s_%02d_%02d)' %(self.DiseaseType, self.OperaType, self.DisDays[1], self.DisDays[2])
		CSV_Path = './ChiMei_{0}/{3}/{2}/CSV_{1}({0})/'.format(datetime.now().strftime("%Y%m%d"), self.DiseaseType, DiseaseTypePath, self.Rec_UserName)
		CSV_Name = self.SingleFileName + ".csv"
		self.DBGV.CheckP_ICAM = 1047
		if self.RR2C_FirstTime:
			self.DBGV.CheckP_ICAM = 1048
			writeData2CSV(CSV_Path + CSV_Name, "w", self.RR2C)
			self.RR2C_FirstTime = False
			self.DBGV.CheckP_ICAM = 1049
		else:
			# print(self.RR2C)
			self.DBGV.CheckP_ICAM = 1050
			writeData2CSV(CSV_Path + CSV_Name, "a", self.RR2C)
			self.DBGV.CheckP_ICAM = 1051

	def saveCoodinate2Arr(self):
		if self.MAZE_IS_RUN:
			self.Mouse_coordinates.append([int(self.TargetPos[0]), int(self.TargetPos[1])])
			if len(self.RR2C) < 20:
				self.RR2C.append([int(self.TargetPos[0]), int(self.TargetPos[1])])
			else:
				self.recordRoute2CSV()
				self.RR2C = []

	def coordinate(self,rat_XY):  #白色物體座標
		self.DBGV.CheckP_ICAM = 1052
		X = rat_XY
		Xa = np.max(X,axis=0)
		Ya = np.min(X,axis=0)
		coo = (((Xa - Ya)/2) + Ya)
		doo = [int(coo[0][0]), int(coo[0][1])]
		area = cv2.contourArea(X)
		self.DBGV.CheckP_ICAM = 1053
		return doo,Xa[0],Ya[0],area

	def initDefault(self): #初始化
		self.DBGV.CheckP_ICAM = 1054
		self.NOW_STATUS = 0
		self.dangchianbi = 0
		self.foodtest = []
		self.Latency = 0
		self.food1 = []
		self.Route = []
		self.frequency = []
		self.ShortTerm = []
		self.LongTerm = []
		for i in range(0,self.ARM_UNIT):
			self.DBGV.CheckP_ICAM = 1055
			self.ShortTerm.append(0)
			self.LongTerm.append(0)
			self.frequency.append(0)
	def examination(self,NOW_STATUS,TargetPos): #進臂判斷
		#八壁32點
		#mask = [[[x11,y11],[x12,y12]],...]
		global fistimeinline,Inlinepoint1,Inlinepoint2,Inlinepoint_long,dangchianjiuli,maskkk
		Ratinline = 65/20	
		self.NOW_STATUS = 0
		self.DBGV.CheckP_ICAM = 1056
		if fistimeinline == True:  #計算八臂進臂線座標點與進臂線的距離(只會跑一次)
			self.DBGV.CheckP_ICAM = 1057
			Inlinepoint1 = []	#八個進臂線座標點1
			Inlinepoint2 = []	#八個進臂線座標點2
			maskkk = [[[0,0],[0,0]],[[0,0],[0,0]],[[0,0],[0,0]],[[0,0],[0,0]],[[0,0],[0,0]],[[0,0],[0,0]],[[0,0],[0,0]],[[0,0],[0,0]],[[0,0],[0,0]]] #每臂進臂線的兩點座標
			
			Inlinepoint_long = [0,0,0,0,0,0,0,0,0] #八個臂的進臂線長

			for i in range(0,self.ARM_UNIT):
				self.DBGV.CheckP_ICAM = 1058
				mask1 = [int(self.ARMS_LINE[i][0][0] -(self.ARMS_LINE[i][0][0] - self.ARMS_LINE[i][1][0])/self.ARM_LINE_DISTANCE) , int(self.ARMS_LINE[i][0][1]-(self.ARMS_LINE[i][0][1] - self.ARMS_LINE[i][1][1])/self.ARM_LINE_DISTANCE)]
				mask2 = [int(self.ARMS_LINE[i][2][0]-(self.ARMS_LINE[i][2][0] - self.ARMS_LINE[i][3][0])/self.ARM_LINE_DISTANCE) , int(self.ARMS_LINE[i][2][1]-(self.ARMS_LINE[i][2][1] - self.ARMS_LINE[i][3][1])/self.ARM_LINE_DISTANCE)]
				#mask1,mask2 為計算每臂進臂線座標
				ans4 = math.sqrt(pow(mask2[0] - mask1[0],2) + pow(mask2[1] - mask1[1],2))
				Inlinepoint1.append(mask1)
				Inlinepoint2.append(mask2)
				maskkk[i][0] = mask1
				maskkk[i][1] = mask2
				# maskkk = [mask1,mask2]
				self.DBGV.Data_ArmInOutPosLine = maskkk #進出臂線座標 丟給DBGV
				Inlinepoint_long[i] = int(ans4)
				fistimeinline = False
				self.DBGV.CheckP_ICAM = 1059
			# print(self.DBGV.Data_ArmInOutPosLine)
			# print(Inlinepoint1)
			# print(Inlinepoint2)
			# print(Inlinepoint_long)
			
		else:
			self.DBGV.CheckP_ICAM = 1060
			maskkk[8][0] = [0,0] #將出壁線移走
			maskkk[8][1] = [0,1]
			# print(maskkk)
			for i in range(0,self.ARM_UNIT):
				self.DBGV.CheckP_ICAM = 1061
				ans1 = math.sqrt(pow(self.TargetPos[0] - Inlinepoint1[i][0],2) + pow(self.TargetPos[1] - Inlinepoint1[i][1],2))
				ans2 = math.sqrt(pow(self.TargetPos[0] - Inlinepoint2[i][0],2) + pow(self.TargetPos[1] - Inlinepoint2[i][1],2))
				# print("NOW_STATUS{}".format(self.NOW_STATUS))
			# print("進壁線%d %s"%(i,ans4))
				ans3 = ans1 + ans2    #白色與一臂的距離
				dangchianjiuli[i] = ans3 #將白色與一臂的距離寫入
				# print("ans%d %s" %(i, ans3))
				self.DBGV.CheckP_ICAM = 1062
				if ans3 < Inlinepoint_long[i]+10:
					self.DBGV.CheckP_ICAM = 1063
					self.NOW_STATUS = 1
					self.dangchianbi= (i + 1)
					self.food1[i] = 0
					break
			# print("Inlinepoint_long: {}".format(Inlinepoint_long))
			# print("dangchianjiuli: {}".format(dangchianjiuli))

		return self.NOW_STATUS,self.dangchianbi
	def leave(self,TargetPos): #出臂判斷
		global Inlinepoint_long,dangchianjiuli,maskkk
		# print("NOW_STATUS{}".format(self.NOW_STATUS))
		self.DBGV.CheckP_ICAM = 1064
		i1 = [0,4,8,12,16,20,24,28]
		i2 = [3,7,11,15,19,23,27,31]
		Ix1 = [int(self.ARMS_POS[i1[self.dangchianbi-1]][0]),int(self.ARMS_POS[i1[self.dangchianbi-1]][1])]
		Ix2 = [int(self.ARMS_POS[i2[self.dangchianbi-1]][0]),int(self.ARMS_POS[i2[self.dangchianbi-1]][1])]
		ans1 = math.sqrt(pow(self.TargetPos[0] - Ix1[0],2) + pow(self.TargetPos[1] - Ix1[1],2))
		ans2 = math.sqrt(pow(self.TargetPos[0] - Ix2[0],2) + pow(self.TargetPos[1] - Ix2[1],2))
		ans4 = math.sqrt(pow(Ix1[0] - Ix2[0],2) + pow(Ix1[1] - Ix2[1],2))
		Inlinepoint_long[8] = int(ans4)
		ans = ans1 + ans2
		dangchianjiuli[8] = ans 
		# print("Inlinepoint_long: {}".format(Inlinepoint_long))
		# print("dangchianjiuli: {}".format(dangchianjiuli))
		# self.DBGV.CheckP_ICAM = 1051
		# cv2.line(self.DBGV.FrameView,(int(Ix1[0]*(680/480)),int(Ix1[1]*(680/480))), (int(Ix2[0]*(680/480)),int(Ix2[1]*(680/480))), (0, 255, 125), 1)  #畫出臂線
		self.DBGV.CheckP_ICAM = 1052

		# print("出臂線距離: {}".format(ans))
		# print("出臂線長度: {}".format(ans4))
		maskkk[8][0] = Ix1	#出臂線兩點之一寫入
		maskkk[8][1] = Ix2 	#出臂線兩點之一寫入
		self.DBGV.Data_ArmInOutPosLine = maskkk #進出臂線座標 丟給DBGV
		# print(maskkk)
		self.DBGV.CheckP_ICAM = 1065
		if ans < ans4+10:
			self.DBGV.CheckP_ICAM = 1066
			self.NOW_STATUS = 0
			
			self.Route.append(self.dangchianbi) #寫入進臂順序
			self.frequency[self.dangchianbi-1] = self.frequency[self.dangchianbi-1]+1 #短期工作記憶+1
			if self.foodtest[self.dangchianbi-1] == 1:	#長期工作記憶判斷
				pass
			elif self.foodtest[self.dangchianbi-1] == 0:
				self.foodtest[self.dangchianbi-1] = self.foodtest[self.dangchianbi-1] + 1
				self.LongTerm[(self.dangchianbi)-1] = self.LongTerm[self.dangchianbi-1] + 1
			else:
				pass
			self.dangchianbi = 0

			self.DBGV.CheckP_ICAM = 1067
		return self.NOW_STATUS,self.dangchianbi	


	def sterm(self):  #短期工作記憶錯誤判斷
		self.DBGV.CheckP_ICAM = 1067
		for i in range(0,8):
			self.DBGV.CheckP_ICAM = 1068
			if self.frequency[i]>0:
				self.DBGV.CheckP_ICAM = 1069
				self.ShortTerm[i] = self.frequency[i]-1

	def DataRecord(self):  #寫入csv
		self.DBGV.CheckP_ICAM = 1070
		csvTitle = ["Group", "Rat ID", "Food", "Total LongTerm", "Total ShortTerm", "Route", "Latency"]
		nLate = Second2Datetime(self.Latency)
		newLatency = "%02d:%02d:%02d" %(nLate[0],nLate[1],nLate[2])
		MazeData = [self.DisGroupType, self.RatID, self.Food, self.TotalLongTerm, self.TotalShortTerm, self.Route, newLatency]
		self.DBGV.CheckP_ICAM = 1071
		if os.path.isfile(self.CSVfilePath):
			self.DBGV.CheckP_ICAM = 1072
			csvData = readCSV2List(self.CSVfilePath)
			if not (listAllSame(csvData[0],csvTitle)):
				self.DBGV.CheckP_ICAM = 1073
				writeData2CSV(self.CSVfilePath, "w", csvTitle)
		else:
			self.DBGV.CheckP_ICAM = 1074
			writeData2CSV(self.CSVfilePath, "w", csvTitle)
		writeData2CSV(self.CSVfilePath, "a", MazeData)
	

	def CameraMain(self): #這個副程式是"主程式"呦~~~~~
		global Inlinepoint_long,dangchianjiuli
		try:
			
			#遮罩形成
			copy = makeBlackImage() #產生黑色的圖
			copy = cv2.resize(copy,(480,480),interpolation=cv2.INTER_CUBIC) #放大成480x480
			cv2.fillPoly(copy, [self.MASK_POS],  (255, 255, 255))  #加上八臂輔助線
			copy = cv2.cvtColor(copy, cv2.COLOR_BGR2GRAY)  #灰階
			B2 , copy = cv2.threshold(copy, 127,255,cv2.THRESH_BINARY) #二值化
			# cv2.imshow ("copy",copy)
			self.DBGV.CheckP_ICAM = 1005

			self.initDefault() #變數初始化
			self.DBGV.CheckP_ICAM = 1006
			#程式一執行[第一次要跑的東西]放這裡
			for i in range(0,self.ARM_UNIT):
				self.DBGV.CheckP_ICAM = 1007
				mask1 = [int(self.ARMS_LINE[i][0][0] -(self.ARMS_LINE[i][0][0] - self.ARMS_LINE[i][1][0])/self.ARM_LINE_DISTANCE) , int(self.ARMS_LINE[i][0][1]-(self.ARMS_LINE[i][0][1] - self.ARMS_LINE[i][1][1])/self.ARM_LINE_DISTANCE)]
				mask2 = [int(self.ARMS_LINE[i][2][0]-(self.ARMS_LINE[i][2][0] - self.ARMS_LINE[i][3][0])/self.ARM_LINE_DISTANCE) , int(self.ARMS_LINE[i][2][1]-(self.ARMS_LINE[i][2][1] - self.ARMS_LINE[i][3][1])/self.ARM_LINE_DISTANCE)]
				# ARMS_IN_LINE1 = [mask1,mask2]
				self.ARMS_IN_LINE.append([mask1,mask2])
				self.DBGV.CheckP_ICAM = 1008
			# print(self.ARMS_IN_LINE)
			self.DBGV.Data_ArmInOutPosLine[0:8] = self.ARMS_IN_LINE
			# print(self.ARMS_IN_LINE)
			while self.WINDOWS_IS_ACTIVE:
				#確定要連線時才會跑這個
				if self.CAM_IS_RUN:
					self.DBGV.CheckP_ICAM = 1009
					frame = self.IPCAM.IPCAM_Image
					IPCAM_LoadTime = (datetime.now() - self.IPCAM.IPCAM_NowTime).seconds
					self.DBGV.CheckP_ICAM = 1010
					if len(frame) == 0:
						frame = cv2.resize(makeBlackImage(),(1280,720),interpolation=cv2.INTER_CUBIC)
						self.IPCAM.setMessenage(2, "[ERROR] CAMERA isn't CONNECT!")
						# print("CAMERA isn't CONNECT! At {}".format(datetime.now()))
						self.CAM_IS_CONN = False
						self.DBGV.CheckP_ICAM = 1011
					else:
						self.WIDTH,self.HEIGHT = (frame.shape[1], frame.shape[0])
						frame = cv2.resize(frame,(self.WIDTH,self.HEIGHT),interpolation=cv2.INTER_CUBIC) #調整大小1024*576

						if IPCAM_LoadTime > 3:
							self.IPCAM.setMessenage(1, "[WAIT] CAMERA is TIMEOUT!")
							self.DBGV.CheckP_ICAM = 1012
							# print("CAMERA is TIMEOUT! At {}".format(datetime.now()))
						else:
							self.IPCAM.setMessenage(0, "[GOOD] CAMERA is connecting!")
							self.DBGV.CheckP_ICAM = 1013
						self.CAM_IS_CONN = True
						# cv2.imshow ("copy",copy)
					# cv2.rectangle(frame, convert(self.newP1), convert(self.newP2), (0,255,0), 1) #繪製矩形
					# cv2.imshow("frame",frame)
					# print(rtsp)
					self.DBGV.CheckP_ICAM = 1014
					self.newP1 = [IPCAM.IPCAM_NewP1[0], IPCAM.IPCAM_NewP1[1]]
					self.newP2 = [self.newP1[0] + self.HEIGHT, self.newP1[1] + self.HEIGHT]
					self.DBGV.CheckP_ICAM = 1015
					frame = frame[self.newP1[1]:self.newP2[1], self.newP1[0]:self.newP2[0]] #擷取兩個點的範圍
					# cv2.polylines(frame, [self.MASK_POS], True, (0, 255, 255), 2)  #加上3臂輔助線
					frame = cv2.resize(frame,(480,480),interpolation=cv2.INTER_CUBIC) #放大成480x480
					frame1 = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)	
					B2,frame1 = cv2.threshold(frame1, 127,255,cv2.THRESH_BINARY)
					self.DBGV.CheckP_ICAM = 1016
					# cv2.imshow("frame1",frame1)
					pr = cv2.bitwise_and(frame1,frame1, mask= copy ) #遮罩覆蓋到影像上
					# cv2.imshow("pr",pr)
					frame1 = cv2.morphologyEx(pr,cv2.MORPH_OPEN,self.O)
					frame1 = cv2.morphologyEx(frame1,cv2.MORPH_CLOSE,self.oo)
					
					# cv2.imshow("frame",frame1)

					# cv2.waitKey(1)
					self.rat_XY,wh = cv2.findContours(frame1,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE) #圈出白色物體 self.rat_XY=所有座標
					
					self.DBGV.CheckP_ICAM = 1017
					if len(self.rat_XY) == 0:
						self.DBGV.NO_RAT = True #有無白色物體
						self.TargetPos = [-20,-20]
					else:
						self.DBGV.NO_RAT = False #有無白色物體
						self.TargetPos_All = []
						self.White_ContourArea_All = []
						self.DBGV.CheckP_ICAM = 1018
						for row in self.rat_XY:
							self.TargetPos, x, y, area = self.coordinate(row)
							self.White_ContourArea_All.append(int(area))	#面積寫入
							self.TargetPos_All.append(self.TargetPos)
							self.DBGV.CheckP_ICAM = 1019
						if self.DBGV.White_PosShowFinish == True:
							self.DBGV.White_CenterPos = self.TargetPos_All  			#將所有白色物體"座標"丟給DebugVideo
							self.DBGV.White_ContourArea = self.White_ContourArea_All	#將所有白色物體"面積"丟給DebugVideo
							self.DBGV.White_Contours = self.rat_XY 						#將所有白色物體"邊緣"丟給DebugVideo
							self.DBGV.CheckP_ICAM = 1020
						self.TargetPos = self.TargetPos_All[0]
						self.DBGV.CheckP_ICAM = 1021

					# self.DBGV.CheckP_ICAM = 1017
					# if len(self.rat_XY) == 0:
					# 	self.DBGV.NO_RAT = True #有無白色物體
					# 	self.TargetPos = [-20,-20]
					# if len(self.rat_XY):
					# 	self.DBGV.NO_RAT = False #有無白色物體
					# 	self.TargetPos_All = []
					# 	self.White_ContourArea_All = []
					# 	self.DBGV.CheckP_ICAM = 1018
					# 	for i in range(0,len(self.rat_XY)):
					# 		self.TargetPos,x,y,area = self.coordinate(self.rat_XY[i])
					# 		self.White_ContourArea_All.append(int(area))	#面積寫入
					# 		self.TargetPos_All.append(self.TargetPos)
					# 		self.DBGV.CheckP_ICAM = 1019
					# 	if self.DBGV.White_PosShowFinish == True:
					# 		self.DBGV.White_CenterPos = self.TargetPos_All  			#將所有白色物體"座標"丟給DebugVideo
					# 		self.DBGV.White_ContourArea = self.White_ContourArea_All	#將所有白色物體"面積"丟給DebugVideo
					# 		self.DBGV.White_Contours = self.rat_XY 						#將所有白色物體"邊緣"丟給DebugVideo
					# 		self.DBGV.CheckP_ICAM = 1020
					# 	# print(self.White_ContourArea_All)
					# 	# print(len(self.TargetPos_All))
					# 	# print(self.TargetPos_All)
					# 	self.DBGV.Data_TargetPos = self.TargetPos_All[0]   #將座標丟給DebugVideo
					# 	self.TargetPos = self.TargetPos_All[0]
					# 	if self.DBGV.NO_RAT == False:
					# 		self.Mouse_coordinates.append(self.TargetPos_All[0])
					# 	self.DBGV.CheckP_ICAM = 1021
					#
					# pass
					#把[影像擷取的東西]放這裡	
					if self.MAZE_IS_RUN: #UI start 後動作
						shutil.copyfile("IPCAM_INFO.csv", "./ChiMei_{}/IPCAM_INFO.csv".format(datetime.now().strftime("%Y%m%d"))) #複製攝影機資訊
						shutil.copyfile("ARMS_LINE.csv", "./ChiMei_{}/ARMS_LINE.csv".format(datetime.now().strftime("%Y%m%d"))) #複製攝影機資訊
						shutil.copyfile("MazeLog.log", "./ChiMei_{}/MazeLog.log".format(datetime.now().strftime("%Y%m%d"))) #複製LOG檔資訊
						# shutil.copyfile("DISEASE_LIST.csv", "./ChiMei_{}/DISEASE_LIST.txt".format(datetime.now().strftime("%Y%m%d"))) #複製疾病分組資訊
						# shutil.copyfile("IPCAM_INFO.csv", "IPCAM_INFO1.txt") #複製攝影機資訊
						# shutil.move("IPCAM_INFO1.txt", "./ChiMei_{}".format(datetime.now().strftime("%Y%m%d")))
						# shutil.copyfile("ARMS_LINE.csv", "ARMS_LINE1.txt")	#複製八臂32點
						# shutil.move("ARMS_LINE1.txt", "./ChiMei_{}".format(datetime.now().strftime("%Y%m%d")))


						self.DBGV.CheckP_ICAM = 1022
						self.sterm()
						if not self.READ_FOOD: #把Food食物狀態寫進判斷狀態
							mousepath = []  
							mousepath = makeBlackImage()	#產生畫老鼠路徑用圖
							mousepath = cv2.resize(mousepath,(480,480),interpolation=cv2.INTER_CUBIC)
							# cv2.imshow("mousepath",mousepath)
							self.Mouse_coordinates = []
							self.initDefault()
							self.DBGV.CheckP_ICAM = 1023
							for i in range (0,self.ARM_UNIT):
								self.food1.append(self.Food[i])
								self.foodtest.append(self.Food[i])
								self.DBGV.CheckP_ICAM = 1024
							self.READ_FOOD = True
							self.timestart = datetime.now() #起始時間
							self.RouteArrFlag = 0
							# print("起始時間: " +str(self.timestart))
							self.DBGV.CheckP_ICAM = 1025
							self.checkSaveDirPath() #檢查所有儲存路徑
							self.DBGV.CheckP_ICAM = 1026
							DiseaseTypePath = '%s(%s_%02d_%02d)' %(self.DiseaseType, self.OperaType, self.DisDays[1], self.DisDays[2])
							self.SingleFileName = "{}_{}_{}_{}".format(datetime.now().strftime("%Y%m%d"), self.DiseaseType, self.DisGroupType, self.RatID) #固定檔名
							self.CSVfilePath = './ChiMei_{0}/{3}/{2}/{0}.csv'.format(datetime.now().strftime("%Y%m%d"), self.DiseaseType, DiseaseTypePath, self.Rec_UserName)
							
							self.RR2C_FirstTime = True #這個是我寫的
							self.DBGV.CheckP_ICAM = 1027
						else:
							pass 
						self.time_now = datetime.now()  #當下時間
						# self.getTimePoint(self.time_now)
						self.Latency = (self.time_now - self.timestart).seconds
						# self.recordRoute2CSV() #這個是我寫的
						self.DBGV.CheckP_ICAM = 1028
						##############################################進臂##############################################
						if self.NOW_STATUS == 0:
							self.DBGV.CheckP_ICAM = 1029
							self.NOW_STATUS, self.dangchianbi = self.examination(self.NOW_STATUS,self.TargetPos)
							# print(self.food1)
							food1max = np.max(self.food1)
							self.DBGV.CheckP_ICAM = 1030

							if food1max == 0:
								self.DBGV.CheckP_ICAM = 1031
								self.NOW_STATUS = 0 #進臂or出臂
								self.Route.append(self.dangchianbi)
								self.Latency = (self.time_now - self.timestart).seconds 
								self.TotalShortTerm = 0
								self.TotalLongTerm = 0
								self.DBGV.CheckP_ICAM = 1032
								for i in range(0,len(self.ShortTerm)):
									self.DBGV.CheckP_ICAM = 1033
									self.TotalShortTerm = self.TotalShortTerm + self.ShortTerm[i]
								# print(self.TotalShortTerm)
								for i in range(0,len(self.LongTerm)):
									self.DBGV.CheckP_ICAM = 1034
									self.TotalLongTerm = self.TotalLongTerm + self.LongTerm[i]
								# print(self.TotalLongTerm)
								self.DBGV.CheckP_ICAM = 1035
								self.DataRecord()
								self.DBGV.CheckP_ICAM = 1036
								winsound.Beep(442,1000)
								# print(self.Mouse_coordinates)
								self.MAZE_IS_RUN = False
								self.DBGV.CheckP_ICAM = 1037
								for i in range (1,len(self.Mouse_coordinates)):   #畫路徑圖
									self.DBGV.CheckP_ICAM = 1038
									# cv2.line(mousepath,convert(self.Mouse_coordinates[i-1]),convert(self.Mouse_coordinates[i]),(20,65,213),1) #白色物體路徑
									cv2.circle(mousepath, convert(self.Mouse_coordinates[i]), 1, (0,255,0), -1)
									# print(self.Mouse_coordinates[i])
								# cv2.imwrite(self.RatID,mousepath)	#儲存路徑圖
								DiseaseTypePath = '%s(%s_%02d_%02d)' %(self.DiseaseType, self.OperaType, self.DisDays[1], self.DisDays[2])
								IMG_Path = './ChiMei_{0}/{3}/{2}/IMG_{1}({0})/'.format(datetime.now().strftime("%Y%m%d"), self.DiseaseType, DiseaseTypePath, self.Rec_UserName)
								IMG_Name = self.SingleFileName + ".jpg"
								cv2.imencode('.jpg', mousepath)[1].tofile(IMG_Path + IMG_Name)
								# cv2.imshow("mouse path",mousepath)
								self.DBGV.CheckP_ICAM = 1039

							else:
								pass
						elif self.NOW_STATUS == 1: #出臂
							self.DBGV.CheckP_ICAM = 1040
							self.NOW_STATUS, self.dangchianbi = self.leave(self.TargetPos_All[0])

						else:
							self.DBGV.CheckP_ICAM = 1041
							pass

						#把[影像擷取過後，開始辨識的東西]放這裡
					else:
						self.DBGV.CheckP_ICAM = 1042
						self.READ_FOOD = False
						# pass
				else:
					self.DBGV.CheckP_ICAM = 1043
					self.CAM_IS_CONN = False
					self.TargetPos = (-1, -1)

				# ==== 給DBGV的參數 ====
				self.DBGV.Exp_Food = self.Food
				self.DBGV.Exp_Disense = self.DiseaseType
				self.DBGV.Exp_DisGroup = self.DisGroupType
				self.DBGV.Exp_DisDay = self.DisDays[:]
				self.DBGV.Exp_RatID = self.RatID	
				self.DBGV.Exp_StartTime = self.timestart
				self.DBGV.Data_ArmInOutLen = Inlinepoint_long
				self.DBGV.Data_ArmInOutDistance = dangchianjiuli
				self.DBGV.Data_TargetPos = self.TargetPos
				self.DBGV.Data_Route = self.Route
				self.DBGV.Data_LongTerm = self.LongTerm
				self.DBGV.Data_ShortTerm = self.ShortTerm
				self.DBGV.Data_TotalTerm = [self.TotalLongTerm, self.TotalShortTerm]
				self.DBGV.Data_ArmState = self.NOW_STATUS
				self.DBGV.Data_CurrentArm = self.dangchianbi
				# self.DBGV.Rec_UserName = self.Rec_UserName

				self.DBGV.Data_ArmState = self.NOW_STATUS
				#開視窗查看影像
				if self.OPEN_CAMERA_WINDOW and self.CAM_IS_RUN:
					#這個我就先留下來
					#frame => 從相機擷取出來的圖片
					#其他的不會影響到你的程式
					
					showFrame = cv2.resize(frame, (self.ViewSize[0],self.ViewSize[1]), interpolation=cv2.INTER_CUBIC)
					cv2.polylines(showFrame, [self.MASK_POS], True, (0, 255, 255), 2)  #加上3臂輔助線

					msgBoard = makeBlackImage()
					msgBoard = cv2.resize(msgBoard, (self.ViewSize[0],30), interpolation=cv2.INTER_CUBIC)
					msgText = "If you want to exit, press 'Camera' Button again to exit."
					cv2.putText(msgBoard, msgText, (10,20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,255))

					CamBoard = np.vstack([showFrame, msgBoard])
					cv2.imshow('Camera Image', CamBoard)
					
					if cv2.waitKey(1) and (not self.OPEN_CAMERA_WINDOW):
						cv2.destroyWindow("Camera Image")
				else:
					cv2.destroyWindow("Camera Image")


				# self.CAMThread.join()
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
