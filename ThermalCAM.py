import cv2
import numpy as np
import time
import datetime
from PIL import Image
import os
import csv

def convert(list): 
	return tuple(list)

def contrast_brightness_image(img, a, b): #img, 對比度, 亮度
	h, w, ch = img.shape
	blank = np.zeros([h, w, ch], img.dtype)
	dst = cv2.addWeighted(img, a, blank, 1-a, 1-b)

	return dst

def makeBlackImage(): #製造出全黑圖片(10x10)
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

def Dot2Dot(pA, pB, pos): #點到點的距離
	B1 = np.sqrt(np.square(pA[0] - pos[0]) + np.square(pA[1] - pos[1]))
	B2 = np.sqrt(np.square(pB[0] - pos[0]) + np.square(pB[1] - pos[1]))

	return int((B1+B2)/2)

def line2gate(pA, pB, cm): #設定門檻線
	B = np.sqrt(np.square(pB[0] - pA[0]) + np.square(pB[1] - pA[1]))
	rX = (cm*(pB[0] - pA[0]) + B*pA[0]) / B
	rY = (cm*(pB[1] - pA[1]) + B*pA[1]) / B

	return [int(rX), int(rY)]

def writeData2CSV(fileName, type_, dataRow): #寫入CSV檔
	with open(fileName, type_, newline='') as csvfile:
		# 建立 CSV 檔寫入器
		writer = csv.writer(csvfile)

		# 寫入一列資料
		writer.writerow(dataRow) 

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

class ThermalCAM:
	def __init__(self):
		#變數：狀態變數
		self.WINDOWS_IS_ACTIVE = True #UI狀態
		self.MAZE_IS_RUN = False #當前系統是否在執行
		self.OPEN_CAMERA_WINDOW = False #影像視窗狀態
		self.CAM_IS_CONN = True #當前鏡頭是否連線

		#變數：迷宮相關變數
		self.NOW_STATUS = 0 #目前狀態
		self.ARM_UNIT = 3 #迷宮臂數
		self.TotalFood = 0 #總食物個數
		self.ViewSize = (480, 385) #虛擬視窗顯示大小
		self.TargetPos = [-1, -1] #目標變數
		self.ARMS_POS = [ #三臂遮罩-For0106(480x385)
    		[236, 122], [419,  19], [446,  63], 
    		[257, 173], [256, 366], [209, 367], 
    		[211, 174], [ 30,  67], [ 55,  27]
		]
		self.ARMS_LINE_POS = [ #三臂遮罩邊-For0106(480x385)
    		[self.ARMS_POS[0], self.ARMS_POS[1],self.ARMS_POS[3],self.ARMS_POS[2]],
    		[self.ARMS_POS[3], self.ARMS_POS[4],self.ARMS_POS[6],self.ARMS_POS[5]],
    		[self.ARMS_POS[6], self.ARMS_POS[7],self.ARMS_POS[0],self.ARMS_POS[8]]
		]
		self.MASK_POS = np.array(self.ARMS_POS)
		self.Food = [] #存放食物在哪臂
		self.FirstIn = [] #第一次進入
		self.Route = [] #記錄進出臂
		self.InLineGate = [] #進入門檻陣列
		self.OutLineGate = [] #退出門檻陣列
		self.ShortTerm = [] #短期記憶陣列
		self.LongTerm = [] #長期記憶陣列
		self.TotalShortTerm = 0 #總短期記憶
		self.TotalLongTerm = 0 #總長期記憶
		self.Latency = 0 #總時間長度
		self.filePath = "" #寫入的檔案路徑
		self.RatID = "" #老鼠編號
		self.setTime = datetime.datetime.now() #開始前時間
		self.nowTime = datetime.datetime.now() #現在時間

	def getArmUnit(self): #取得迷宮臂數
		return self.ARM_UNIT

	def getMazeArmsPos(self): #取得迷宮座標點
		return self.ARMS_POS

	def getViewHW(self): #取得虛擬視窗顯示大小
		return self.ViewSize

	def getCameraStatus(self): #取得鏡頭狀態
		return self.CAM_IS_CONN

	def getTargetPos(self): #取得經過處理後取得的座標
		return self.TargetPos

	def getMazeStatus(self): #取得系統運行狀態
		return self.MAZE_IS_RUN

	def getTerm(self): #取得短期/長期記憶
		return self.ShortTerm, self.LongTerm

	def getRoute(self): #取得進出臂順序
		return self.Route

	def getLatency(self): #取得目前總時間長度
		return self.Latency

	def getArmMask(self): #取得壁迷宮遮罩
		image = makeBlackImage()
		image = cv2.resize(image, (self.ViewSize[0],self.ViewSize[1]), interpolation=cv2.INTER_CUBIC) #圖片放大
		image = cv2.fillPoly(image, [self.MASK_POS], (255, 255, 255)) #實心多邊形
		gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) #灰階影像
		ret,th1 = cv2.threshold(gray,25,255,cv2.THRESH_BINARY) #二值化

		return th1

	def setMazeStatus(self, status): #設定系統運行狀態
		self.MAZE_IS_RUN = status

	def setInterfaceStatus(self, status): #設定UI狀態
		self.WINDOWS_IS_ACTIVE = status

	def setCameraWindow(self, status): #設定影像視窗狀態
		self.OPEN_CAMERA_WINDOW = status

	def setFoodWithArm(self, total, food): #設定食物陣列
		self.TotalFood = total
		self.Food = food

	def setFilePath(self, filepath): #設定檔案寫入路徑
		self.filePath = filepath

	def setRatID(self, ratid): #設定老鼠編號
		self.RatID = ratid

	def setArmGate(self, cm): #設定臂門檻線
		result = []
		for x in range(0,self.ARM_UNIT):
			xA = line2gate(self.ARMS_LINE_POS[x][0], self.ARMS_LINE_POS[x][1], cm)
			xB = line2gate(self.ARMS_LINE_POS[x][2], self.ARMS_LINE_POS[x][3], cm)
			result.append([xA, xB])

		return result

	def virtualCam(self, pid): #模擬鏡頭運行
		speed = 10
		image = cv2.imread("./test/0106/0106-%d.png" %(int(pid/speed) + 1))
		if pid < (60 - 1)*speed:
			pid = pid + 1
		else:
			pid = 1

		return pid, image

	def CatchItemPos(self, img):
		mask = self.getArmMask() #取得遮罩
		original = cv2.bitwise_and(img, img, mask = mask) #圖片套用遮罩
		newPhoto = contrast_brightness_image(original,3.2,100)
		#影像分層
		grayR = newPhoto[:,:,2]
		grayG = newPhoto[:,:,1]
		grayB = newPhoto[:,:,0]
		#取得白色區域
		ret,thR = cv2.threshold(grayR,200,255,cv2.THRESH_BINARY) #有貼紅標記點
		ret,thG = cv2.threshold(grayG,200,255,cv2.THRESH_BINARY)
		ret,thB = cv2.threshold(grayB,200,255,cv2.THRESH_BINARY)
		thA = thR & thG & thB

		contours,hierarchy = cv2.findContours(thA,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE) #取得物體邊緣做標

		mid = [-1, -1]
		for i in range(0,len(contours)):
		    cnt=contours[i]
		    pt1 = np.min(cnt, axis=0) #左上座標
		    pt2 = np.max(cnt, axis=0) #右下座標
		    midX = (pt2[0][0] - pt1[0][0])/2 + pt1[0][0]
		    midY = (pt2[0][1] - pt1[0][1])/2 + pt1[0][1]
		    mid = [int(midX), int(midY)]
		    # cv2.rectangle(img, convert(pt1[0]), convert(pt2[0]), (0,255,0), 1) #繪製矩形
		    
		return mid

	def initDefault(self):
		self.Route = []
		self.FirstIn = []
		self.ShortTerm = []
		self.LongTerm = []
		self.setTime = datetime.datetime.now()
		self.TotalShortTerm = 0
		self.TotalLongTerm = 0
		for i in range(0,self.ARM_UNIT):
			self.FirstIn.append(0)
			self.ShortTerm.append(0)
			self.LongTerm.append(0)

	def computeTerm(self, arm): #紀錄記憶錯誤
		if self.FirstIn[arm] == 0:
			if(self.Food[arm] == 1):
				self.TotalFood = self.TotalFood - 1
			else:
				self.LongTerm[arm] = self.LongTerm[arm] + 1
				self.TotalLongTerm = self.TotalLongTerm + 1
			self.FirstIn[arm] = 1
		else:
			self.ShortTerm[arm] = self.ShortTerm[arm] + 1
			self.TotalShortTerm = self.TotalShortTerm + 1

	def checkGate(self, st):
		newDot = [self.TargetPos[0], self.TargetPos[1]]
		if(st == 0):
			for x in range(0,self.ARM_UNIT):
				d = Dot2Dot(self.InLineGate[x][0],self.InLineGate[x][1], newDot)
				# print("d%d = %d" %(x,d))
				if(d < 30):
					# print("d%d = %d" %(x,d))
					self.computeTerm(x)
					st = x+1
					return st
		else:
			x = st - 1
			d = Dot2Dot(self.OutLineGate[x][0],self.OutLineGate[x][1], newDot)
			if(d < 30):
				self.Route.append(st)
				st = 0
		return st

	def DataRecord(self):  #寫入csv
		csvTitle = ["Rat ID", "Food", "Total LongTerm", "Total ShortTerm", "Route", "Latency"]
		nLate = Second2Datetime(self.Latency)
		newLatency = "%02d:%02d:%02d" %(nLate[0],nLate[1],nLate[2])
		MazeData = [self.RatID, self.Food, self.TotalLongTerm, self.TotalShortTerm, self.Route, newLatency]
		if os.path.isfile(self.filePath):
			csvData = readCSV2List(self.filePath)
			if not (listAllSame(csvData[0],csvTitle)):
				writeData2CSV(self.filePath, "w", csvTitle)
		else:
			writeData2CSV(self.filePath, "w", csvTitle)
		writeData2CSV(self.filePath, "a", MazeData)

	def CameraMain(self): #這個副程式是"主程式"呦~~~~~
		pid = 1
		#設定門檻線
		self.InLineGate = self.setArmGate(60) #設定進入門檻線
		self.OutLineGate = self.setArmGate(10) #設定退出門檻線
		self.initDefault() #初始化變數

		RUN_FIRST_TIME = False
		while self.WINDOWS_IS_ACTIVE:

			#影像擷取
			pid, frame = self.virtualCam(pid)
			frame = cv2.resize(frame, (self.ViewSize[0],self.ViewSize[1]), interpolation=cv2.INTER_CUBIC)
			
			self.TargetPos = self.CatchItemPos(frame) #取得目標座標
			if self.MAZE_IS_RUN:
				if not RUN_FIRST_TIME:
					self.initDefault() #初始化變數
					RUN_FIRST_TIME = True
				else:
					self.NOW_STATUS = self.checkGate(self.NOW_STATUS) #檢查目前狀態
					if self.TotalFood != 0:
						self.nowTime = datetime.datetime.now()
						self.Latency = (self.nowTime - self.setTime).seconds

					if self.NOW_STATUS == 0 and self.TotalFood == 0:
						self.DataRecord()
						self.MAZE_IS_RUN = False
						RUN_FIRST_TIME = False
			else:
				RUN_FIRST_TIME = False

			#開視窗查看影像
			if self.OPEN_CAMERA_WINDOW:
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
			