import cv2
import numpy as np
import time
from PIL import Image

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

class ThermalCAM:
	def __init__(self):
		self.WINDOWS_IS_ACTIVE = True #UI狀態
		self.OPEN_CAMERA_WINDOW = False #影像視窗狀態
		self.CAM_IS_CONN = True #當前鏡頭是否連線
		self.ARM_UNIT = 3 #迷宮臂數
		self.ViewSize = (480, 385) #虛擬視窗顯示大小
		self.TargetPos = [-1, -1]
		self.ARMS_POS = [ #三臂遮罩-For0106(480x385)
    		[236, 122], [419,  19], [446,  63], 
    		[257, 173], [256, 366], [209, 367], 
    		[211, 174], [ 30,  67], [ 55,  27]
		]
		self.MASK_POS = np.array(self.ARMS_POS)

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

	def setInterfaceStatus(self, status): #設定UI狀態
		self.WINDOWS_IS_ACTIVE = status

	def setCameraWindow(self, status): #設定影像視窗狀態
		self.OPEN_CAMERA_WINDOW = status

	def getArmMask(self): #取得壁迷宮遮罩
		image = makeBlackImage()
		image = cv2.resize(image, (self.ViewSize[0],self.ViewSize[1]), interpolation=cv2.INTER_CUBIC) #圖片放大
		image = cv2.fillPoly(image, [self.MASK_POS], (255, 255, 255)) #實心多邊形
		gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) #灰階影像
		ret,th1 = cv2.threshold(gray,25,255,cv2.THRESH_BINARY) #二值化

		return th1

	def virtualCam(self, pid): #模擬鏡頭運行
		speed = 12
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


	def CameraMain(self): #這個副程式是"主程式"呦~~~~~
		pid = 1
		while self.WINDOWS_IS_ACTIVE:
			pid, frame = self.virtualCam(pid)
			frame = cv2.resize(frame, (self.ViewSize[0],self.ViewSize[1]), interpolation=cv2.INTER_CUBIC)
			self.TargetPos = self.CatchItemPos(frame)

			if self.OPEN_CAMERA_WINDOW:
				showFrame = cv2.resize(frame, (self.ViewSize[0],self.ViewSize[1]), interpolation=cv2.INTER_CUBIC)
				cv2.polylines(showFrame, [self.MASK_POS], True, (0, 255, 255), 2)  #加上3臂輔助線

				msgBoard = makeBlackImage()
				msgBoard = cv2.resize(msgBoard, (self.ViewSize[0],30), interpolation=cv2.INTER_CUBIC)
				msgText = "If you want to exit, press 'Camera' Button again to exit."
				cv2.putText(msgBoard, msgText, (10,20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,255))

				CamBoard = np.vstack([showFrame, msgBoard])
				cv2.imshow('Camera Image', CamBoard)
				
				if cv2.waitKey(1) & (not self.OPEN_CAMERA_WINDOW):
					cv2.destroyAllWindows()
			