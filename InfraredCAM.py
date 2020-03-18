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

#========純副程式區========
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
		self.filePath = "" #寫入的檔案路徑+檔名
		self.RatID = "" #老鼠編號
		self.TotalFood = 0 #總食物個數
		self.Food = [] #存放食物在哪臂

		#變數：迷宮相關變數(這些[都要傳到UI端]讓它知道的)
		self.ARM_UNIT = 8 #迷宮臂數
		self.ARM_LINE_DISTANCE = 65/20  #老鼠進臂線距離
		self.ARMS_IN_LINE = []
		self.ViewSize = (480, 480) #虛擬視窗顯示大小
		self.TargetPos = [-1, -1] #目標變數
		self.ARMS_POS = [[287,227],[478,227],[478,264],[289,263], #I11,O11,O12,I12
						[283,271],[426,414],[402,440],[259,297], #I21,O21,O22,I22
						[252,298],[252,479],[219,479],[219,301], #I31,O31,O32,I32
						[212,298],[68,441],[40,419],[184,270], #I41,O41,O42,I42
						[182,266],[1,266],[1,228],[183,228], #I51,O51,O52,I52
						[188,222],[37,71],[60,47],[212,197], #I61,O61,O62,I62
						[218,195],[217,2],[253,2],[253,194], #I71,O71,O72,I72
						[257,197],[406,48],[432,73],[284,218]
						] #八壁遮罩
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
		self.WIDTH = 1024
		self.HEIGHT = int(self.WIDTH*(9/16))  #576
		self.MID_POS = [520, 540]
		self.SegRate = (4/11)
		self.newP1 = (int(self.MID_POS[0]-int(self.HEIGHT)/2),0)
		# self.newP1 = (self.MID_POS[0] - int((self.WIDTH*self.SegRate)/2), self.MID_POS[1] - int((self.WIDTH*self.SegRate)/2))
		self.newP2 = (int(self.MID_POS[0]+int(self.HEIGHT/2)),int(self.HEIGHT))
		# self.newP2 = (self.MID_POS[0] + int((self.WIDTH*self.SegRate)/2), self.MID_POS[1] + int((self.WIDTH*self.SegRate)/2))
		self.O = np.array([[1,1,1,1,1],
	 			 [1,1,1,1,1],
				 [1,1,1,1,1],
				 [1,1,1,1,1],
				 [1,1,1,1,1]], dtype="uint8")
		self.READ_FOOD = False #第一次讀取哪壁有食物
		self.frequency = []  #進臂次數
		self.NOW_STATUS = 0 #進臂or出臂
		self.dangchianbi = 0

	#========其他的副程式========

	def coordinate(self,rat_XY):  #白色物體座標
		X = rat_XY[0]
		Xa = np.max(X,axis=0)
		Ya = np.min(X,axis=0)
		coo = (((Xa - Ya)/2) + Ya)
		doo = [int(coo[0][0]), int(coo[0][1])]
		return doo,Xa[0],Ya[0]

	def initDefault(self): #初始化
		self.foodtest = []
		self.Latency = 0
		self.food1 = []
		self.Route = []
		self.frequency = []
		self.ShortTerm = []
		self.LongTerm = []
		for i in range(0,self.ARM_UNIT):
			self.ShortTerm.append(0)
			self.LongTerm.append(0)
			self.frequency.append(0)
	def examination(self,NOW_STATUS,TargetPos): #進臂判斷
		#八壁32點
		
		#mask = [[[x11,y11],[x12,y12]],...]
		mask = []
		Ratinline = 65/20
		self.NOW_STATUS = 0
		for i in range(0,self.ARM_UNIT):
			# mask1 = [int(ARMS_LINE[i][0][0] -(ARMS_LINE[i][0][0] - ARMS_LINE[i][1][0])/Ratinline) , int(ARMS_LINE[i][0][1]-(ARMS_LINE[i][0][1] - ARMS_LINE[i][1][1])/Ratinline)]
			# mask2 = [int(ARMS_LINE[i][2][0]-(ARMS_LINE[i][2][0] - ARMS_LINE[i][3][0])/Ratinline) , int(ARMS_LINE[i][2][1]-(ARMS_LINE[i][2][1] - ARMS_LINE[i][3][1])/Ratinline)]
			mask1 = [int(self.ARMS_LINE[i][0][0] -(self.ARMS_LINE[i][0][0] - self.ARMS_LINE[i][1][0])/self.ARM_LINE_DISTANCE) , int(self.ARMS_LINE[i][0][1]-(self.ARMS_LINE[i][0][1] - self.ARMS_LINE[i][1][1])/self.ARM_LINE_DISTANCE)]
			mask2 = [int(self.ARMS_LINE[i][2][0]-(self.ARMS_LINE[i][2][0] - self.ARMS_LINE[i][3][0])/self.ARM_LINE_DISTANCE) , int(self.ARMS_LINE[i][2][1]-(self.ARMS_LINE[i][2][1] - self.ARMS_LINE[i][3][1])/self.ARM_LINE_DISTANCE)]
			ans1 = math.sqrt(pow(self.TargetPos[0] - mask1[0],2) + pow(self.TargetPos[1] - mask1[1],2))
			ans2 = math.sqrt(pow(self.TargetPos[0] - mask2[0],2) + pow(self.TargetPos[1] - mask2[1],2))
			ans3 = ans1 + ans2    #白色與一臂的距離
			# print("ans%d %s" %(i, ans3))
			if ans3 < 40:
				self.NOW_STATUS = 1
				self.dangchianbi= (i + 1)
				self.food1[i] = 0
				break
		return self.NOW_STATUS,self.dangchianbi
	def leave(self,dangchianbi,TargetPos): #出臂判斷

		I11 = [int(self.ARMS_POS[0][0]),int(self.ARMS_POS[0][1])]
		I12 = [int(self.ARMS_POS[3][0]),int(self.ARMS_POS[3][1])]
		I21 = [int(self.ARMS_POS[4][0]),int(self.ARMS_POS[4][1])]
		I22 = [int(self.ARMS_POS[7][0]),int(self.ARMS_POS[7][1])]
		I31 = [int(self.ARMS_POS[8][0]),int(self.ARMS_POS[8][1])]
		I32 = [int(self.ARMS_POS[11][0]),int(self.ARMS_POS[11][1])]
		I41 = [int(self.ARMS_POS[12][0]),int(self.ARMS_POS[12][1])]
		I42 = [int(self.ARMS_POS[15][0]),int(self.ARMS_POS[15][1])]
		I51 = [int(self.ARMS_POS[16][0]),int(self.ARMS_POS[16][1])]
		I52 = [int(self.ARMS_POS[19][0]),int(self.ARMS_POS[19][1])]
		I61 = [int(self.ARMS_POS[20][0]),int(self.ARMS_POS[20][1])]
		I62 = [int(self.ARMS_POS[23][0]),int(self.ARMS_POS[23][1])]
		I71 = [int(self.ARMS_POS[24][0]),int(self.ARMS_POS[24][1])]
		I72 = [int(self.ARMS_POS[27][0]),int(self.ARMS_POS[27][1])]
		I81 = [int(self.ARMS_POS[28][0]),int(self.ARMS_POS[28][1])]
		I82 = [int(self.ARMS_POS[31][0]),int(self.ARMS_POS[31][1])]

		# self.NOW_STATUS = 1



		if self.dangchianbi == 1:
			ans11 = math.sqrt(pow(self.TargetPos[0] - I11[0],2) + pow(self.TargetPos[1] - I11[1],2))
			ans12 = math.sqrt(pow(self.TargetPos[0] - I12[0],2) + pow(self.TargetPos[1] - I12[1],2))
			ans1 = ans11 + ans12	
			# print("ans00"+str(ans0))
			if ans1<40:
				self.NOW_STATUS = 0
				self.dangchianbi = 0
				self.Route.append(1) #寫入進臂順序
				self.frequency[0] = self.frequency[0]+1  #短期工作記憶+1
				if self.foodtest[0] == 1: #長期工作記憶判斷
					pass
				elif self.foodtest[0] == 0:					
					self.foodtest[0] = self.foodtest[0] + 1
					self.LongTerm[0] = self.LongTerm[0] +1
				else:
					pass
		elif self.dangchianbi == 2:
			ans21 = math.sqrt(pow(self.TargetPos[0] - I21[0],2) + pow(self.TargetPos[1] - I21[1],2))
			ans22 = math.sqrt(pow(self.TargetPos[0] - I22[0],2) + pow(self.TargetPos[1] - I22[1],2))
			ans2 = ans21 + ans22	
			# print("ans11"+str(ans1))
			if ans2<40:
				self.NOW_STATUS=0
				self.dangchianbi = 0
				self.Route.append(2)
				self.frequency[1] = self.frequency[1]+1
				if self.foodtest[1] == 1:#長期工作記憶判斷
					pass
				elif self.foodtest[1] == 0:
					self.foodtest[1] = self.foodtest[1]+1
					self.LongTerm[1] = self.LongTerm[1] + 1
				# else:
				# 	pass	
			else:
				pass
		elif self.dangchianbi == 3:
			ans31 = math.sqrt(pow(self.TargetPos[0] - I31[0],2) + pow(self.TargetPos[1] - I31[1],2))
			ans32 = math.sqrt(pow(self.TargetPos[0] - I32[0],2) + pow(self.TargetPos[1] - I32[1],2))
			ans3 = ans31 + ans32	
			# print("ans22"+str(ans2))
			if ans3 < 40:
				self.NOW_STATUS = 0
				self.dangchianbi = 0
				self.Route.append(3)
				self.frequency[2]=self.frequency[2]+1
				if self.foodtest[2] == 1:#長期工作記憶
					pass
				elif self.foodtest[2] == 0:
					self.foodtest[2] = self.foodtest[2] + 1
					self.LongTerm[2] = self.LongTerm[2] + 1
				else:
					pass
		elif self.dangchianbi == 4:
			ans41 = math.sqrt(pow(self.TargetPos[0] - I41[0],2) + pow(self.TargetPos[1] - I41[1],2))
			ans42 = math.sqrt(pow(self.TargetPos[0] - I42[0],2) + pow(self.TargetPos[1] - I42[1],2))
			ans4 = ans41 + ans42	
			# print("ans22"+str(ans2))
			if ans4 < 40:
				self.NOW_STATUS = 0
				self.dangchianbi = 0
				self.Route.append(4)
				self.frequency[3]=self.frequency[3]+1
				if self.foodtest[3] == 1:#長期工作記憶
					pass
				elif self.foodtest[3] == 0:
					self.foodtest[3] = self.foodtest[3] + 1
					self.LongTerm[3] = self.LongTerm[3] + 1
				else:
					pass
		elif self.dangchianbi == 5:
			ans51 = math.sqrt(pow(self.TargetPos[0] - I51[0],2) + pow(self.TargetPos[1] - I51[1],2))
			ans52 = math.sqrt(pow(self.TargetPos[0] - I52[0],2) + pow(self.TargetPos[1] - I52[1],2))
			ans5 = ans51 + ans52	
			# print("ans22"+str(ans2))
			if ans5 < 40:
				self.NOW_STATUS = 0
				self.dangchianbi = 0
				self.Route.append(5)
				self.frequency[4]=self.frequency[4]+1
				if self.foodtest[4] == 1:#長期工作記憶
					pass
				elif self.foodtest[4] == 0:
					self.foodtest[4] = self.foodtest[4] + 1
					self.LongTerm[4] = self.LongTerm[4] + 1
				else:
					pass
		elif self.dangchianbi == 6:
			ans61 = math.sqrt(pow(self.TargetPos[0] - I61[0],2) + pow(self.TargetPos[1] - I61[1],2))
			ans62 = math.sqrt(pow(self.TargetPos[0] - I62[0],2) + pow(self.TargetPos[1] - I62[1],2))
			ans6 = ans61 + ans62	
			# print("ans6"+str(ans6))
			if ans6 < 40:
				self.NOW_STATUS = 0
				self.dangchianbi = 0
				self.Route.append(6)
				self.frequency[5]=self.frequency[5]+1
				if self.foodtest[5] == 1:#長期工作記憶
					pass
				elif self.foodtest[5] == 0:
					self.foodtest[5] = self.foodtest[5] + 1
					self.LongTerm[5] = self.LongTerm[5] + 1
				else:
					pass
		elif self.dangchianbi == 7:
			ans71 = math.sqrt(pow(self.TargetPos[0] - I71[0],2) + pow(self.TargetPos[1] - I71[1],2))
			ans72 = math.sqrt(pow(self.TargetPos[0] - I72[0],2) + pow(self.TargetPos[1] - I72[1],2))
			ans7 = ans71 + ans72	
			# print("ans22"+str(ans2))
			if ans7 < 40:
				self.NOW_STATUS = 0
				self.dangchianbi = 0
				self.Route.append(7)
				self.frequency[6]=self.frequency[6]+1
				if self.foodtest[6] == 1:#長期工作記憶
					pass
				elif self.foodtest[6] == 0:
					self.foodtest[6] = self.foodtest[6] + 1
					self.LongTerm[6] = self.LongTerm[6] + 1
				else:
					pass
		elif self.dangchianbi == 8:
			ans81 = math.sqrt(pow(self.TargetPos[0] - I81[0],2) + pow(self.TargetPos[1] - I81[1],2))
			ans82 = math.sqrt(pow(self.TargetPos[0] - I82[0],2) + pow(self.TargetPos[1] - I82[1],2))
			ans8 = ans81 + ans82	
			# print("ans22"+str(ans2))
			if ans8 < 40:
				self.NOW_STATUS = 0
				self.dangchianbi = 0
				self.Route.append(8)
				self.frequency[7]=self.frequency[7]+1
				if self.foodtest[7] == 1:#長期工作記憶
					pass
				elif self.foodtest[7] == 0:
					self.foodtest[7] = self.foodtest[7] + 1
					self.LongTerm[7] = self.LongTerm[7] + 1
				else:
					pass
		else:
			pass

		return self.NOW_STATUS,self.dangchianbi	


	def sterm(self):  #短期工作記憶錯誤判斷
		for i in range(0,8):
			if self.frequency[i]>0:
				self.ShortTerm[i] = self.frequency[i]-1

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
		

		#遮罩形成
		copy = makeBlackImage() #產生黑色的圖
		copy = cv2.resize(copy,(480,480),interpolation=cv2.INTER_CUBIC) #放大成480x480
		cv2.fillPoly(copy, [self.MASK_POS],  (255, 255, 255))  #加上八臂輔助線
		copy = cv2.cvtColor(copy, cv2.COLOR_BGR2GRAY)  #灰階
		B2 , copy = cv2.threshold(copy, 127,255,cv2.THRESH_BINARY) #二值化
		# cv2.imshow ("copy",copy)

		self.initDefault()
		#程式一執行[第一次要跑的東西]放這裡
		for i in range(0,self.ARM_UNIT):
			mask1 = [int(self.ARMS_LINE[i][0][0] -(self.ARMS_LINE[i][0][0] - self.ARMS_LINE[i][1][0])/self.ARM_LINE_DISTANCE) , int(self.ARMS_LINE[i][0][1]-(self.ARMS_LINE[i][0][1] - self.ARMS_LINE[i][1][1])/self.ARM_LINE_DISTANCE)]
			mask2 = [int(self.ARMS_LINE[i][2][0]-(self.ARMS_LINE[i][2][0] - self.ARMS_LINE[i][3][0])/self.ARM_LINE_DISTANCE) , int(self.ARMS_LINE[i][2][1]-(self.ARMS_LINE[i][2][1] - self.ARMS_LINE[i][3][1])/self.ARM_LINE_DISTANCE)]
			# ARMS_IN_LINE1 = [mask1,mask2]
			self.ARMS_IN_LINE.append([mask1,mask2])
		# print(self.ARMS_IN_LINE)
		while self.WINDOWS_IS_ACTIVE:
			#確定要連線時才會跑這個
			if self.CAM_IS_RUN:
				frame = self.IPCAM.IPCAM_Image
				IPCAM_LoadTime = (datetime.now() - self.IPCAM.IPCAM_NowTime).seconds
				
				if len(frame) == 0:
					frame = cv2.resize(makeBlackImage(),(1280,720),interpolation=cv2.INTER_CUBIC)
					self.IPCAM.setMessenage(2, "[ERROR] CAMERA isn't CONNECT!")
					# print("CAMERA isn't CONNECT! At {}".format(datetime.now()))
					self.CAM_IS_CONN = False
				else:
					frame = cv2.resize(frame,(self.WIDTH,self.HEIGHT),interpolation=cv2.INTER_CUBIC) #調整大小1024*576
					if IPCAM_LoadTime > 3:
						self.IPCAM.setMessenage(1, "[WAIT] CAMERA is TIMEOUT!")
						# print("CAMERA is TIMEOUT! At {}".format(datetime.now()))
					else:
						self.IPCAM.setMessenage(0, "[GOOD] CAMERA is connecting!")
					self.CAM_IS_CONN = True
				
				# cv2.rectangle(frame, convert(self.newP1), convert(self.newP2), (0,255,0), 1) #繪製矩形
				# cv2.imshow("frame",frame)
				frame = frame[self.newP1[1]:self.newP2[1], self.newP1[0]:self.newP2[0]] #擷取兩個點的範圍
				# cv2.polylines(frame, [self.MASK_POS], True, (0, 255, 255), 2)  #加上3臂輔助線
				frame = cv2.resize(frame,(480,480),interpolation=cv2.INTER_CUBIC) #放大成480x480
				frame1 = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)	
				B2,frame1 = cv2.threshold(frame1, 127,255,cv2.THRESH_BINARY)
				pr = cv2.bitwise_and(frame1,frame1, mask=copy ) #遮罩覆蓋到影像上
				frame1 = cv2.morphologyEx(pr,cv2.MORPH_OPEN,self.O)
				# cv2.imshow("frame1",frame1)
				self.rat_XY,wh = cv2.findContours(frame1,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE) #圈出白色物體 W=所有座標
				if len(self.rat_XY):
					self.TargetPos,x,y = self.coordinate(self.rat_XY)
				cv2.waitKey(1)
				# pass
				#把[影像擷取的東西]放這裡
				if self.MAZE_IS_RUN: #UI start 後動作

					self.sterm()
					if not self.READ_FOOD: #把Food食物狀態寫進判斷狀態
						mousepath = []  
						mousepath = makeBlackImage()	#產生畫老鼠路徑用圖
						mousepath = cv2.resize(mousepath,(480,480),interpolation=cv2.INTER_CUBIC)
						cv2.imshow("mousepath",mousepath)
						self.Mouse_coordinates = []
						self.initDefault()
						for i in range (0,self.ARM_UNIT):
							self.food1.append(self.Food[i])
							self.foodtest.append(self.Food[i])
						self.READ_FOOD = True
						self.timestart = datetime.now() #起始時間
						self.RouteArrFlag = 0
						print("起始時間: " +str(self.timestart))
						

					else:
						pass 
					self.time_now = datetime.now()  #當下時間
					# self.getTimePoint(self.time_now)
					self.Latency = (self.time_now - self.timestart).seconds  
					##############################################進臂##############################################
					if self.NOW_STATUS == 0:
						self.NOW_STATUS, self.dangchianbi = self.examination(self.NOW_STATUS,self.TargetPos)
						# print(self.food1)
						food1max = np.max(self.food1)
						if food1max == 0:
							self.Latency = (self.time_now - self.timestart).seconds 
							self.TotalShortTerm = 0
							self.TotalLongTerm = 0
							for i in range(0,len(self.ShortTerm)):
								self.TotalShortTerm = self.TotalShortTerm + self.ShortTerm[i]
							# print(self.TotalShortTerm)
							for i in range(1,len(self.LongTerm)):
								self.TotalLongTerm = self.TotalLongTerm + self.LongTerm[i]
							# print(self.TotalLongTerm)
							self.DataRecord()
							winsound.Beep(442,1000)
							print(self.Mouse_coordinates)
							self.MAZE_IS_RUN = False
							for i in range (1,len(self.Mouse_coordinates)):   #畫路徑圖
								# cv2.line(mousepath,convert(self.Mouse_coordinates[i-1]),convert(self.Mouse_coordinates[i]),(20,65,213),1) #白色物體路徑
								cv2.circle(mousepath, convert(self.Mouse_coordinates[i]), 0.5, -1)
							# cv2.imwrite(self.RatID,mousepath)	#儲存路徑圖
							
							cv2.imwrite(self.timestart.strftime("%m%d%H%M%S")+self.RatID+'.jpg',mousepath)
							cv2.imshow("mouse path",mousepath)
						else:
							pass
					elif self.NOW_STATUS == 1: #出臂
						self.NOW_STATUS, self.dangchianbi = self.leave(self.NOW_STATUS,self.TargetPos)
					else:
						pass

					#把[影像擷取過後，開始辨識的東西]放這裡
				else:
					self.READ_FOOD = False
					# pass
			else:
				self.CAM_IS_CONN = False
				self.TargetPos = (-1, -1)

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