import cv2
import numpy as np

class ThermalCAM:
	def __init__(self):
		super().__init__()
		self.ARM_UNIT = 3
		self.ARMS_POS = [ #三臂遮罩-For0106(480x385)
    		[236, 122], [419,  19], [446,  63], 
    		[257, 173], [256, 366], [209, 367], 
    		[211, 174], [ 30,  67], [ 55,  27]
		]

	def getArmUnit(self):
		return self.ARM_UNIT

	def getMazeArmsPos(self):
		return self.ARMS_POS