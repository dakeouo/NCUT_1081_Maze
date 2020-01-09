#========程式匯入區========
import cv2
import numpy as np
from PIL import Image #<= 這個是贈品需要匯入的東西

#========純副程式區========
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
		#變數：狀態變數(這些變數[由UI端傳來的]狀態變數)
		self.WINDOWS_IS_ACTIVE = True #UI狀態
		self.MAZE_IS_RUN = False #當前系統是否在執行
		self.OPEN_CAMERA_WINDOW = False #影像視窗狀態
		self.CAM_IS_CONN = True #當前鏡頭是否連線
		# WINDOWS_IS_ACTIVE 	=> setInterfaceStatus()
		# MAZE_IS_RUN 			=> setMazeStatus()/getMazeStatus()  (這個兩邊都有控制權)
		# OPEN_CAMERA_WINDOW 	=> setCameraWindow()
		# CAM_IS_CONN			=> getCameraStatus()

		#變數：迷宮相關變數(這些變數[由UI端傳來的]迷宮相關變數)
		self.filePath = "" #寫入的檔案路徑+檔名
		self.RatID = "" #老鼠編號
		self.TotalFood = 0 #總食物個數
		self.Food = [] #存放食物在哪臂
		# filePath 			=> setFilePath()
		# RatID 			=> setRatID()
		# TotalFood, Food	=> setFoodWithArm()

		#變數：迷宮相關變數(這些[都要傳到UI端]讓它知道的)
		self.ARM_UNIT = 8 #迷宮臂數
		self.ViewSize = (480, 480) #虛擬視窗顯示大小
		self.TargetPos = [-1, -1] #目標變數
		self.ARMS_POS = [] #八臂遮罩
		self.Route = [] #記錄進出臂
		self.ShortTerm = [] #短期記憶陣列
		self.LongTerm = [] #長期記憶陣列
		self.Latency = 0 #總時間長度
		# ARM_UNIT 				=> getArmUnit()
		# ViewSize 				=> getViewHW()
		# TargetPos				=> getTargetPos()
		# ARMS_POS 				=> getMazeArmsPos()
		# Route 				=> getRoute()
		# ShortTerm,LongTerm	=> getTerm()
		# Latency				=> getLatency()

		#變數：迷宮相關變數(這些[不用傳給UI端]但這個程式應該用的上)
		self.InLineGate = [] #進入門檻陣列
		self.OutLineGate = [] #退出門檻陣列
		self.TotalShortTerm = 0 #總短期記憶
		self.TotalLongTerm = 0 #總長期記憶
		#然後其他你有需要的變數就再自己加

	#========GET副程式區========
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

	#其他如果你有要用GET開頭的你也可以放在這裡

	#========SET副程式區========
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

	#其他如果你有要用SET開頭的你也可以放在這裡

	#========其他的副程式========
	def CameraMain(self): #這個副程式是"主程式"呦~~~~~
		
		#程式一執行[第一次要跑的東西]放這裡

		while self.WINDOWS_IS_ACTIVE:
			pass
			#把[影像擷取的東西]放這裡

			if self.MAZE_IS_RUN:
				pass
				#把[影像擷取過後，開始辨識的東西]放這裡
			else:
				pass

			#開視窗查看影像
			if self.OPEN_CAMERA_WINDOW:
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