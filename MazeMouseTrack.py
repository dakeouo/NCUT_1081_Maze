import random
import datetime
import tkinter as tk
import tkinter.messagebox
from tkinter import filedialog
import threading
# from ThermalCAM import ThermalCAM as TCAM
from InfraredCAM import InfraredCAM as TCAM
import DebugVideo as DBGV
import IPCAM_Frame as IPCAM
import logging
import sys
import traceback
import csv
from PIL import Image, ImageTk
import tkinter.ttk as ttk

IPCAM_Info_FileName = "./IPCAM_INFO.csv"
Disease_List_FileName = "./DISEASE_LIST.csv"
IPCAM_Info = []
Disease_List = []

FORMAT = '%(asctime)s [%(filename)s] %(levelname)s: %(message)s'
logging.basicConfig(level=logging.WARNING, filename='MazeLog.log', filemode='a', format=FORMAT)
DBGV.CheckP_UI = "1"

def convert(list): #轉換資料型態(list -> tuple)
    return tuple(list)

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

def LoadCamInfo():	#將[攝相機資訊檔案]匯入[攝相機資訊陣列]
	global IPCAM_Info
	#名稱, 帳號, 密碼, IP, RTSP, Ax, Ay
	IPCAM_Info = readCSV2List(IPCAM_Info_FileName)
	for i in range(len(IPCAM_Info)):
		IPCAM_Info[i][5] = int(IPCAM_Info[i][5])
		IPCAM_Info[i][6] = int(IPCAM_Info[i][6])
	# print(IPCAM_Info)

def LoadDiseaseFile(): #將[疾病分組檔案]匯入[疾病分組資訊陣列]
	global Disease_List, Disease_List_FileName
	Disease_List = readCSV2List(Disease_List_FileName)
	# print(Disease_List)

def WriteDiseaseFile(data):	#將目前[疾病分組資訊陣列]重新寫入[疾病分組檔案]
	global Disease_List, Disease_List_FileName
	writeData2CSV(Disease_List_FileName, "w", data[0])
	for i in range(1, len(data)):
		writeData2CSV(Disease_List_FileName, "a", data[i])

def findDiseaseArray(arr, Dtype, text): #找尋目前輸入的內容是否在陣列疾病分組資訊陣列內(有:回傳index/無:回傳-1)
	# print(Dtype, text)
	for i in range(0,len(arr)):
		if arr[i][1] == text and arr[i][0] == Dtype:
			return i
	return -1

def countStr(Str): #算出字串中大小寫字母與數字及其他符號的個數
	Unit = [0, 0, 0, 0] #大寫字母/小寫字母/數字/其他符號
	for i in range(0,len(Str)):
		if (ord(Str[i]) >= 65) and (ord(Str[i]) <= 90):
			Unit[0] = Unit[0] + 1
		elif (ord(Str[i]) >= 97) and (ord(Str[i]) <= 122):
			Unit[1] = Unit[1] + 1
		elif Str[i].isdigit():
			Unit[2] = Unit[2] + 1
		else:
			Unit[3] = Unit[3] + 1
	
	return Unit

def Second2Datetime(sec): #秒數轉換成時間
	return int(sec/3600), int((sec%3600)/60), int((sec%3600)%60) 	

def CreateModelRTStr(OpType, OpM, OpD, Model, Group, RatID):
	if OpType != "":
		OpTypeStr = "%sOp" %(OpType)
	else:
		OpTypeStr = ""
	if OpM != -1:
		OpMStr = "%02dM" %(OpM)
	else:
		OpMStr = ""
	if OpD != -1:
		OpDStr = "%02dD" %(OpD)
	else:
		OpDStr = ""
	if Model != "":
		ModelStr = Model
	else:
		ModelStr = ""
	if Group != "":
		GroupStr = "(%s)" %(Group)
	else:
		GroupStr = ""
	if str(RatID) != "":
		RatIDStr = "ID%s" %(str(RatID))
	else:
		RatIDStr = ""
	return "%s %s%s %s%s %s" %(OpTypeStr, OpMStr, OpDStr, ModelStr, GroupStr, RatIDStr)

class MazeMouseTrack(object):
	def __init__(self):
		#=======變數命名規則說明=======
		# (一) UI變數(它算式UI的物件。因為其他副程式也要用到，所以必須要將物件命名)
		# self.TK_* => 用在主UI視窗的變數
		# self.TKS_* => 用在設定UI視窗的變數
		# self.*Combo => 下拉式選單變數
		# self.TKC_* => 主UI視窗的Checkbox(核選方塊)變數
		# (二) 執行緒
		# self.*Thread => 執行緒變數
		# (三) 其它
		# 剩下的自己看啦，我設的變數都有機可循的，英文不會就請自己翻譯
		#============================

		#紅外線攝相機執行緒
		self.IPCAM = IPCAM
		self.CAMThread = threading.Thread(target = self.IPCAM.Main) # 執行該子執行緒
		self.CAMThread.start()  # 執行該子執行緒
		DBGV.CheckP_UI = "2"

		#熱影像相機執行緒
		self.TCAM = TCAM()
		self.thread = threading.Thread(target = self.TCAM.CameraMain) # 執行該子執行緒
		self.thread.start()  # 執行該子執行緒
		DBGV.CheckP_UI = "3"

		#狀態顯示&錄影程式執行緒
		self.DBGV = DBGV
		self.DBGVThread = threading.Thread(target = self.DBGV.DBGV_Main) # 執行該子執行緒
		self.DBGVThread.start()  # 執行該子執行緒
		DBGV.CheckP_UI = "4"

		#變數：迷宮系統相關
		self.ARM_UNIT = self.TCAM.ARM_UNIT #迷宮臂數
		self.ARMS_POS = self.TCAM.ARMS_POS #迷宮臂座標點
		self.OPEN_CAMERA_WINDOW = False #影像視窗狀態
		self.TotalFood = 0 #放食物的總數
		self.Food = [] #放食物的臂
		self.Route = [] #紀錄進臂順序
		self.S_Term = [] #各臂短期記憶錯誤
		self.L_Term = [] #各臂長期記憶錯誤
		self.FilePath = "" #存入的路徑
		self.FileName = "" #存入的檔案
		self.TargetPos = self.TCAM.TargetPos #影像處理後取得的座標
		self.nowPos = self.TargetPos
		self.Latency = 0 #總時間長度

		#變數：視窗相關
		self.WinSize = (1152, 560) #UI介面顯示大小
		self.BALL_SIZE = 20
		self.ViewSize = self.TCAM.ViewSize #虛擬視窗顯示大小
		self.MAZE_IS_RUN = False #當前系統是否在執行
		self.CAM_IS_RUN = False #當前相機程式是否在執行
		self.CAM_INIT_SUCCESS = False #CAM是否初始化成功
		self.CAM_IS_CONN = self.TCAM.CAM_IS_CONN #當前鏡頭是否連線
		self.EXP_DATA_MODE = "NONE" #當前實驗模式
		self.TK_Food = [] #勾選放食物的臂
		self.TK_S_Term = [] #顯示各臂短期記憶錯誤
		self.TK_L_Term = [] #顯示各臂長期記憶錯誤
		self.TK_Total_S_Term = 0 #顯示短期記憶錯誤總和
		self.TK_Total_L_Term = 0 #顯示長期記憶錯誤總和
		self.TK_File_Dir = "" #顯示存入的檔案(含路徑)
		self.TK_Rat_ID = "" #顯示老鼠編號
		self.Rat_ID = "" #顯示老鼠編號
		self.OldTrain_Rat_ID = "" #舊訓練用老鼠編號
		self.SYS_MSG = "" #顯示錯誤訊息
		self.TK_Latency = 0 #顯示總時間長度
		self.Rec_UserName = "" #顯示使用者名稱

		#變數：顯示目前設定狀態
		self.TK_SHOW_Food = []
		# self.TK_SHOW_FileDir = ""
		self.TK_SHOW_Rat_ID = ""
		self.TK_SHOW_SYS_Msg = ""
		self.TKE_Dir = ""
		self.TKC_Food = []

		self.InfoCombo = ""
		self.BT_Choose_Dir = ""
		self.BT_Rat_ID = ""
		self.mazeTitle = ""

		#實驗設定變數統整
		self.OperaType = "" #目前使用模式(訓練期/正式實驗期)
		self.DiseaseType = "" #老鼠病症組別
		self.DisGroupType = "" #老鼠病症組別復鍵(含 健康、無復健 等)
		self.DisDays = [False, -1, -1] #老鼠病症天數(是否手術, 月, 天)
		self.SETTING_OPEN = False	#設定視窗是否開啟

		#顯示在設定視窗上的所有數值/文字變數
		self.TKS_Show_Opera = ""
		self.TKS_Show_OpDay = ""
		self.TKS_Show_Disease = ""
		self.TKS_Show_DisGroup = ""
		self.DiseaseCombo = ""
		self.DisGroupCombo = ""
		self.TKS_DCM_Name_val = ""
		self.TKS_DCM_Description_val = ""
		self.TKS_DGCM_Name_val = ""
		self.TKS_DGCM_Description_val = ""

		self.CSV_DiseaseFile = [] #存放CSV讀進來的內容
		self.NOW_DiseaseList = [-1, '', '', ''] #目前編輯條目(index, 分類[疾病/分組], 名稱, 敘述)
		DBGV.CheckP_UI = "5"

		self.tkWin = tk.Tk()
		self.tkWin.title('%d臂迷宮路徑追蹤系統' %(self.ARM_UNIT)) #窗口名字
		self.tkWin.geometry('%dx%d+20+20' %(self.WinSize[0],self.WinSize[1])) #窗口大小(寬X高+X偏移量+Y偏移量)
		self.tkWin.resizable(False, False) #禁止變更視窗大小
		DBGV.CheckP_UI = "6"

		try:
			self.setEachVariable() #各項變數初始化
			DBGV.CheckP_UI = "7"
			self.setupUI() #視窗主程式
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

		self.firstMazeRun = True

	def setArmLine(self): #繪製迷宮框
		DBGV.CheckP_UI = "23"
		DrawArms = self.ARMS_POS
		DrawArms.append(DrawArms[0])
		for i in range(1,len(DrawArms)):
			p1 = (int(DrawArms[i-1][0]), int(DrawArms[i-1][1]))
			p2 = (int(DrawArms[i][0]), int(DrawArms[i][1]))
			# arr = "{0},{1}".format(p1,p2)
			# print(arr)
			self.mazeCanvas.create_line(p1[0], p1[1], p2[0], p2[1], fill="yellow",width=2)

	def setEachVariable(self): #設定各項變數預設值
		for i in range(0,self.ARM_UNIT):
			self.Food.append(0)
			self.TK_Food.append(0)
			self.L_Term.append(0)
			self.S_Term.append(0)
			self.TK_L_Term.append("0")
			self.TK_S_Term.append("0")

	def SetRatID(self): #設定老鼠編號
		DBGV.CheckP_UI = "24"
		RAT_ID = self.TK_Rat_ID.get()
		Unit = countStr(RAT_ID)
		# str1 = "# RatID: {}".format(RAT_ID)
		# move = 288 - (Unit[0]*11 + (Unit[1] + Unit[2] + Unit[3])*9)
		if RAT_ID != "":
			self.TKS_Show_Rat_ID.config(text="RatID: {}".format(RAT_ID), fg="black")
		else:
			self.TKS_Show_Rat_ID.config(text="RatID: (not set)", fg="gray35")
		self.Rat_ID = RAT_ID
		self.DBGV.Data_ModelRT_Str = CreateModelRTStr(self.OperaType, self.DisDays[1], self.DisDays[2], self.DiseaseType, self.DisGroupType, self.Rat_ID)
		# print(len(RAT_ID))

	def SetUserName(self):
		DBGV.CheckP_UI = "24-1"
		Rec_UserName = self.TK_User_Name.get()
		if Rec_UserName != "":
			self.TKS_Show_UserName.config(text="Users: %s" %(Rec_UserName), fg="black")
		else:
			self.TKS_Show_UserName.config(text="Users: (not set)", fg="gray35")
		self.Rec_UserName = Rec_UserName
		self.DBGV.Rec_UserName = Rec_UserName

	def setFood(self): #設定食物放在哪個臂
		DBGV.CheckP_UI = "25"
		hadFood = []
		ct = 0
		for i in range(0,self.ARM_UNIT):
			if(self.TK_Food[i].get() == 1): 
				hadFood.append((i+1))
				self.Food[i] = 1
				ct = ct + 1
			else:
				self.Food[i] = 0
		self.TotalFood = ct
		# if(ct == 0):
		# 	str1 = "# Food: "
		# 	# move = 290
		# else:
		# 	str1 = "# Food: {}".format(hadFood)
		# 	# move = 290 - ct*17

		if ct == 0:
			self.TK_SHOW_Food.config(text="Food: (not set)", fg="gray35")
		else:
			self.TK_SHOW_Food.config(text="Food: {}".format(hadFood), fg="black")
		# self.TK_SHOW_Food.place(x=800, y=260,anchor="nw")

	def ConnectClick(self): #"Link"按鈕按下時負責處理的副程式
		if self.CAM_IS_RUN:
			DBGV.CheckP_UI = "26-1"
			self.BT_Connect.config(text="Link", bg="DarkOliveGreen2", fg="dark green")
			self.Link_State.config(text="IPCAM Link: Unlinked", fg="gray35")
			self.CAM_IS_RUN = False
			self.BT_Start.config(bg="gray85", state="disabled")
			self.BT_Camera.config(state="disabled")
			self.BT_Setting.config(state="disabled")
			for i in range(1, self.ARM_UNIT+1):
				self.TKC_Food[i-1].config(state="disabled")
			# self.BT_Rat_ID.config(state="disabled")
			# self.TK_Rat_ID.config(state="disabled")
			# self.BT_User_Name.config(state="disabled")
			# self.TK_User_Name.config(state="disabled")
			self.TCAM.CAM_IS_RUN = False
			self.TCAM.CAM_IS_CONN = False
			self.IPCAM.CAM_IS_RUN = False
			self.BT_Camera.config(bg="gray85")
			self.OPEN_CAMERA_WINDOW = False
			self.TCAM.OPEN_CAMERA_WINDOW = self.OPEN_CAMERA_WINDOW
			self.makeBall()
			if self.SETTING_OPEN:
				self.SETTING_OPEN = False
				self.DBGV.Maze_SetState = False
				self.BT_Setting.config(state="disabled")
				self.tkSetting.destroy()
		else:
			DBGV.CheckP_UI = "26-2"
			self.BT_Connect.config(text="Unlink", bg="tomato", fg="brown4")
			self.Link_State.config(text="IPCAM Link: Linked",fg="green4")
			self.CAM_IS_RUN = True
			self.BT_Start.config(bg="DarkOliveGreen2", state="normal")
			self.BT_Camera.config(state="normal")
			self.BT_Setting.config(state="normal")
			for i in range(1, self.ARM_UNIT+1):
				self.TKC_Food[i-1].config(state="normal")
			# self.BT_Rat_ID.config(state="normal")
			# self.TK_Rat_ID.config(state="normal")
			# self.BT_User_Name.config(state="normal")
			# self.TK_User_Name.config(state="normal")
			self.TCAM.CAM_IS_RUN = True
			self.IPCAM.CAM_IS_RUN = True

	def MazeStartCheck(self): #執行前檢查
		HaveError = False
		if self.MAZE_IS_RUN:
			DBGV.CheckP_UI = "27-1"
			self.Maze_State.config(text="Maze State: Preparing...", fg="gray35")
			self.Maze_State.place(x=800, y=200,anchor="nw")
			self.BT_Start.config(text="Start", bg="DarkOliveGreen2")
			self.MAZE_IS_RUN = False
		else:
			DBGV.CheckP_UI = "27-2"
			ErrMsg = ""
			if self.OperaType == "":
				ErrMsg = ErrMsg + "You don't have set Operation Type!!\n"
				HaveError = True
			if self.DisDays[1] == -1 and self.DisDays[2] == -1:
				ErrMsg = ErrMsg + "You don't set Operation TimePoint!!\n"
				HaveError = True
			else:
				if(self.DisDays[1] == -1):
					self.DisDays[1] = 0
				if(self.DisDays[2] == -1):
					self.DisDays[2] = 0

			DBGV.CheckP_UI = "27-3"
			if self.DiseaseType == "":
				ErrMsg = ErrMsg + "You don't set Model Type!!\n"
				HaveError = True
			if self.DisGroupType == "":
				ErrMsg = ErrMsg + "You don't set Model Group Type!!\n"
				HaveError = True
			if self.Rat_ID == "":
				ErrMsg = ErrMsg + "Rat ID not filled!!\n"
				HaveError = True
			if self.Rec_UserName == "":
				ErrMsg = ErrMsg + "Username not filled!!\n"
				HaveError = True
			if self.TotalFood == 0:
				ErrMsg = ErrMsg + "You don't have click any food!!\n"
				HaveError = True
			
			DBGV.CheckP_UI = "27-4"
			if HaveError:
				tk.messagebox.showwarning(title='Warning!!', message=ErrMsg)
			else:
				self.TCAM.TotalFood = self.TotalFood
				self.TCAM.Food = self.Food
				self.TCAM.RatID = self.Rat_ID
				self.TCAM.Rec_UserName = self.Rec_UserName
				# self.TCAM.filePath = (str(self.FilePath)+str(self.FileName))

				self.TCAM.OperaType = self.OperaType
				self.TCAM.DiseaseType = self.DiseaseType
				self.TCAM.DisGroupType = self.DisGroupType
				self.TCAM.DisDays = self.DisDays

				self.Maze_State.config(text="Maze State: Recording...", fg="green4")
				self.Maze_State.place(x=800, y=200, anchor="nw")
				self.BT_Start.config(text="Stop", bg="IndianRed1")

				self.MAZE_IS_RUN = True
				if self.EXP_DATA_MODE == "TRAINING":
					self.OldTrain_Rat_ID = self.Rat_ID
		self.TCAM.MAZE_IS_RUN = self.MAZE_IS_RUN

	def CameraCheck(self): #實體影像檢查
		if self.OPEN_CAMERA_WINDOW:
			DBGV.CheckP_UI = "28-1"
			self.BT_Camera.config(bg="gray85")
			self.OPEN_CAMERA_WINDOW = False
		else:
			DBGV.CheckP_UI = "28-2"
			self.BT_Camera.config(bg="lemon chiffon")
			self.OPEN_CAMERA_WINDOW = True
		self.TCAM.OPEN_CAMERA_WINDOW = self.OPEN_CAMERA_WINDOW
		self.DBGV.Maze_CameraState = self.OPEN_CAMERA_WINDOW

	def makeBall(self): #變更目標位置
		DBGV.CheckP_UI = "29"
		self.TargetPos = self.TCAM.TargetPos
		self.mazeCanvas.move(self.TBall, int(self.TargetPos[0] - self.nowPos[0]), int(self.TargetPos[1] - self.nowPos[1]))
		self.nowPos = self.TargetPos

	def updateData(self): #更新各項顯示資訊
		DBGV.CheckP_UI = "30"
		self.S_Term = self.TCAM.ShortTerm
		self.L_Term = self.TCAM.LongTerm
		self.Route = self.TCAM.Route
		self.Latency = self.TCAM.Latency
		TLT = 0 #Total Long Term
		TST = 0 #Total Short Term
		for i in range(1, self.ARM_UNIT+1):
			TLT = TLT + self.L_Term[i-1]
			TST = TST + self.S_Term[i-1]
			self.TK_L_Term[i-1].set(str(self.L_Term[i-1]))
			self.TK_S_Term[i-1].set(str(self.S_Term[i-1]))
		self.TK_Total_S_Term.set("Total Short Term: %d" %(TST))
		self.TK_Total_L_Term.set("Total Long Term: %d" %(TLT))
		nLate = Second2Datetime(self.Latency)
		self.TK_Latency.set("Latency: %02d:%02d:%02d" %(nLate[0],nLate[1],nLate[2]))
		self.RouteText.delete('0.0','end')
		self.RouteText.insert('end',self.Route)

	def LockInput(self, state): #輸入鎖(避免不必要的麻煩)
		if state:
			DBGV.CheckP_UI = "31-1"
			# self.TKE_Dir.config(state="disabled")
			if self.MAZE_IS_RUN:
				self.BT_Connect.config(state="disabled")

			if self.DBGV.Maze_SetState and self.EXP_DATA_MODE != "NONE":
				self.TKS_Disease.config(state="disabled")
				self.TK_User_Name.config(state="disabled")
				self.BT_User_Name.config(state="disabled")
				self.TKS_BT_DisConfirm.config(state="disabled")
				if self.EXP_DATA_MODE == "EXPERIMENT":
					self.TKS_Btn1_Opera1.config(state="disabled")
					self.TKS_Btn1_Opera2.config(state="disabled")
					self.TKS_OpDay_Month.config(state="disabled")
					self.TKS_OpDay_Day.config(state="disabled")
					self.TKS_DisGroup.config(state="disabled")
					self.TKS_BT_OpDayConfirm.config(state="disabled")
					self.TKS_BT_DisGroupConfirm.config(state="disabled")
					self.TK_Rat_ID.config(state="disabled")
					self.BT_Rat_ID.config(state="disabled")
				
				
			for i in range(0,self.ARM_UNIT):
				self.TKC_Food[i].config(state="disabled")
		else:
			DBGV.CheckP_UI = "31-2"
			# self.TKE_Dir.config(state="normal")
			self.BT_Connect.config(state="normal")

			if self.DBGV.Maze_SetState and self.EXP_DATA_MODE != "NONE":
				self.TKS_Disease.config(state="normal")
				self.TKS_BT_DisConfirm.config(state="normal")
				self.TK_User_Name.config(state="normal")
				self.BT_User_Name.config(state="normal")
				if self.EXP_DATA_MODE == "EXPERIMENT":
					self.TKS_Btn1_Opera1.config(state="normal")
					self.TKS_Btn1_Opera2.config(state="normal")
					self.TKS_OpDay_Month.config(state="normal")
					self.TKS_OpDay_Day.config(state="normal")
					self.TKS_DisGroup.config(state="normal")
					self.TKS_BT_OpDayConfirm.config(state="normal")
					self.TKS_BT_DisGroupConfirm.config(state="normal")
					self.TK_Rat_ID.config(state="normal")
					self.BT_Rat_ID.config(state="normal")

			for i in range(0,self.ARM_UNIT):
				self.TKC_Food[i].config(state="normal")

	def setIPCAMInfo(self): #設定要匯入IPCAM那隻程式的資訊
		if(self.InfoCombo.current() != 0):
			DBGV.CheckP_UI = "32-1"
			IPCAM_ID, IPCAM_Name = self.InfoCombo.current()-1, self.InfoCombo.get()

			IPCAM_Username = IPCAM_Info[IPCAM_ID][1]
			IPCAM_Password = IPCAM_Info[IPCAM_ID][2]
			IPCAM_IP = IPCAM_Info[IPCAM_ID][3]
			IPCAM_Bar = IPCAM_Info[IPCAM_ID][4]
			IPCAM_NewP1 = [IPCAM_Info[IPCAM_ID][5], IPCAM_Info[IPCAM_ID][6]]
			self.CAM_INIT_SUCCESS = True

			self.IPCAM.IPCAM_Username = IPCAM_Username
			self.IPCAM.IPCAM_Password = IPCAM_Password
			self.IPCAM.IPCAM_IP = IPCAM_IP
			self.IPCAM.IPCAM_Name = IPCAM_Name
			self.IPCAM.IPCAM_Bar = IPCAM_Bar
			self.IPCAM.IPCAM_NewP1 = [IPCAM_NewP1[0], IPCAM_NewP1[1]]

			self.IPCAM.CAM_INIT_SUCCESS = self.CAM_INIT_SUCCESS

			DBGV.CheckP_UI = "32-2"
			self.mazeTitle.config(text="IPCAM: {} ({})".format(IPCAM_Name, IPCAM_IP))
			# for i in range(1, self.ARM_UNIT+1):
			# 	self.TKC_Food[i-1].config(state="normal")
			self.BT_Connect.config(state="normal", bg="DarkOliveGreen2")
			# self.BT_Setting.config(state="normal")
			# self.BT_Choose_Dir.config(state="normal")
			# self.BT_Rat_ID.config(state="normal")
			# self.TK_Rat_ID.config(state="normal")
			# self.TKE_Dir.config(state="normal")

			self.BT_LoadCAM.config(state="disabled")
			self.InfoCombo.config(state="disabled")

	def LoopMain(self): #UI執行後一直跑的迴圈
		try:
			DBGV.CheckP_UI = "11"
			if  self.CAM_INIT_SUCCESS:
				DBGV.CheckP_UI = "12"
				self.makeBall()
				self.CAM_IS_CONN = self.TCAM.CAM_IS_CONN
				if self.CAM_IS_RUN and self.CAM_IS_CONN:
					self.BT_Start.config(bg="DarkOliveGreen2")
					self.BT_Start.config(state="normal")
				else:
					self.BT_Start.config(bg="gray85")
					self.BT_Start.config(state="disabled")

				if self.MAZE_IS_RUN:
					DBGV.CheckP_UI = "13-1"
					if self.firstMazeRun:
						self.firstMazeRun = False
					self.LockInput(True)
					DBGV.CheckP_UI = "13-2"
					newMazeStatus = self.TCAM.MAZE_IS_RUN
					self.updateData()
					DBGV.CheckP_UI = "13-3"
					if newMazeStatus == False:
						self.Maze_State.config(text="Maze State: Preparing...", fg="gray35")
						self.Maze_State.place(x=800, y=200,anchor="nw")
						self.BT_Start.config(text="Start", bg="DarkOliveGreen2")
						self.MAZE_IS_RUN = False
						self.Maze_StartState = False
				else:
					DBGV.CheckP_UI = "14"
					if self.CAM_IS_CONN:
						self.LockInput(False)
						if (self.EXP_DATA_MODE == "TRAINING") and (self.OldTrain_Rat_ID == self.Rat_ID):
							self.Rat_ID = datetime.datetime.now().strftime("T%H%M%S")
							self.TKS_Show_Rat_ID.config(text="RatID: %s" %(self.Rat_ID), fg="black")
					else:
						self.LockInput(True)
					self.firstMazeRun = True
					
				if self.CAM_IS_CONN:
					self.Cam_State.config(text="Camera State: Connecting...", fg="green4")
					self.Cam_State.place(x=800, y=170, anchor="nw")
					self.BT_Camera.config(state="normal")
				else:
					self.Cam_State.config(text="Camera State: Unconnect", fg="gray35")
					self.Cam_State.place(x=800, y=170, anchor="nw")
					self.BT_Camera.config(state="disabled")

				DBGV.CheckP_UI = "15"
				IPCAM_MsgColor = self.IPCAM.IPCAM_MsgColor
				IPCAM_Messenage = self.IPCAM.IPCAM_Messenage

				self.TK_SHOW_SYS_Msg.set("Messenage: {}".format(IPCAM_Messenage))
				
				if(IPCAM_MsgColor == 0):
					self.TK_SHOW_SYS_Msg_Text.config(fg="green4")
				elif(IPCAM_MsgColor == 1):
					self.TK_SHOW_SYS_Msg_Text.config(fg="blue2")
				elif(IPCAM_MsgColor == 2):
					self.TK_SHOW_SYS_Msg_Text.config(fg="red2")
				
				self.DBGV.Maze_StartState = self.MAZE_IS_RUN
				self.DBGV.Maze_LinkState = self.CAM_IS_RUN
				self.DBGV.Maze_CameraState = self.OPEN_CAMERA_WINDOW
				DBGV.CheckP_UI = "16"

			self.tkWin.after(10,self.LoopMain)
			DBGV.CheckP_UI = "17"

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

	def windowsClosing(self): #UI總關閉處
		DBGV.CheckP_UI = "21"
		self.TCAM.WINDOWS_IS_ACTIVE = False #傳送視窗關閉狀態
		self.IPCAM.WINDOWS_IS_ACTIVE = False #傳送視窗關閉狀態
		self.DBGV.WINDOWS_IS_ACTIVE = False #傳送視窗關閉狀態
		self.tkWin.destroy()
		if self.SETTING_OPEN:
			self.tkSetting.destroy()

	def PreparingTesting(self): #測試按鈕(偷懶用，但現在也沒在用，留著)
		if self.WinSize[0] == 1152:
			self.WinSize[0] = 1280
		else:
			self.WinSize[0] = 1152
		self.tkWin.geometry('%dx%d+20+20' %(self.WinSize[0],self.WinSize[1])) #窗口大小(寬X高+X偏移量+Y偏移量)

	def setArmNumber(self): #設定虛擬視窗上臂的編號
		DBGV.CheckP_UI = "44"
		mov = 15
		for i in range(0, self.ARM_UNIT):
			textA = self.ARMS_POS[((i+1)*4)-3]
			textB = self.ARMS_POS[((i+1)*4)-2]
			textXY = [int((textA[0] - textB[0])/2) + textB[0], int((textA[1] - textB[1])/2) + textB[1]]
			if textA[0] < int(self.ViewSize[0]*(1/3)):
				textXY[0] = textXY[0] + mov
			elif textA[0] > int(self.ViewSize[0]*(2/3)):
				textXY[0] = textXY[0] - mov
			if textA[1] < int(self.ViewSize[1]*(1/3)):
				textXY[1] = textXY[1] + mov
			elif textA[1] > int(self.ViewSize[1]*(2/3)):
				textXY[1] = textXY[1] - mov
			self.mazeCanvas.create_text(textXY[0], textXY[1], fill="gold", font="Arial 14", text=str(i+1))

	def setArmInLine(self): #設定進臂線
		DBGV.CheckP_UI = "45"
		ARMS_IN_LINE = self.TCAM.ARMS_IN_LINE
		while len(ARMS_IN_LINE) == 0:
			ARMS_IN_LINE = self.TCAM.ARMS_IN_LINE
			print("ARMS_IN_LINE is null!!")

		for i in range(0, self.ARM_UNIT):
			self.mazeCanvas.create_line(ARMS_IN_LINE[i][0][0], ARMS_IN_LINE[i][0][1], ARMS_IN_LINE[i][1][0], ARMS_IN_LINE[i][1][1], fill="DarkGoldenrod4", width=3)

	def tkSetting_UploadDisease(self, ListType, DList): #設定UI視窗更新[疾病分組資訊](疾病/組別, 目前疾病分組陣列)
		DBGV.CheckP_UI = "33-1"
		idx = DList[0]
		if idx == -1:
			self.CSV_DiseaseFile.append(DList[1:])
		else:
			self.CSV_DiseaseFile[idx] = DList[1:]
		
		DBGV.CheckP_UI = "33-2"
		WriteDiseaseFile(self.CSV_DiseaseFile)
		DBGV.CheckP_UI = "33-3"
		LoadDiseaseFile()
		DBGV.CheckP_UI = "33-4"
		if ListType == "Disease":
			DiseaseInfo = ['choose Disease...']
			for i in range(len(self.CSV_DiseaseFile)):
				if self.CSV_DiseaseFile[i][0] == 'Disease':
					DiseaseInfo.append(self.CSV_DiseaseFile[i][1])
			self.DiseaseCombo.config(values=DiseaseInfo)
			self.ModifyDCM.config(values=DiseaseInfo)
			self.DiseaseCombo.current(0)
			self.ModifyDCM.current(0)
		else:
			DisGroupInfo = ['choose Group...']
			for i in range(len(self.CSV_DiseaseFile)):
				if self.CSV_DiseaseFile[i][0] == 'DisGroup':
					DisGroupInfo.append(self.CSV_DiseaseFile[i][1])
			self.DisGroupCombo.config(values=DisGroupInfo)
			self.ModifyDGCM.config(values=DisGroupInfo)
			self.DisGroupCombo.current(0)
			self.ModifyDGCM.current(0)
		
		DBGV.CheckP_UI = "33-5"
		self.NOW_DiseaseList = [-1, '', '', '']

	def tkSetting_BtnOpera(self, val): #設定UI視窗點擊[手術前/後]按鈕後處理副程式
		DBGV.CheckP_UI = "34"
		if val == 'pre-Op':
			self.TKS_Btn1_Opera1.config(bg="DarkOliveGreen2")
			self.TKS_Btn1_Opera2.config(bg="gray90")
			self.DisDays[0] = False
			self.OperaType = 'pre'
		elif val == 'past-Op':
			self.TKS_Btn1_Opera1.config(bg="gray90")
			self.TKS_Btn1_Opera2.config(bg="DarkOliveGreen2")
			self.DisDays[0] = True
			self.OperaType = 'past'
		self.TKS_Show_Opera.config(text="Operation Type: %s-Op  " %(self.OperaType), fg="black")
		self.DBGV.Data_ModelRT_Str = CreateModelRTStr(self.OperaType, self.DisDays[1], self.DisDays[2], self.DiseaseType, self.DisGroupType, self.Rat_ID)

	def tkSetting_DiseaseConfirm(self): #設定UI視窗點擊[確認病因]按鈕後處理副程式
		DBGV.CheckP_UI = "35"
		self.DBGV.Data_SettingClick[1] = self.DBGV.Data_SettingClick[1] + 1
		newSpace = ""
		for i in range(15):
			newSpace = newSpace + " "
		if self.TKS_Disease.get() != "":
			self.DiseaseType = self.TKS_Disease.get()
			self.TKS_Show_Disease.config(text="Model: %s%s" %(self.DiseaseType,newSpace), fg="black")
			self.DBGV.Data_ModelRT_Str = CreateModelRTStr(self.OperaType, self.DisDays[1], self.DisDays[2], self.DiseaseType, self.DisGroupType, self.Rat_ID)
		# if(self.DiseaseCombo.current() != 0):
		# 	self.DiseaseType = self.DiseaseCombo.get()
		# 	self.TKS_Show_Disease.config(text="Model: %s" %(self.DiseaseType), fg="black")

	def tkSetting_DisGroupConfirm(self): #設定UI視窗點擊[確認疾病組別]按鈕後處理副程式
		DBGV.CheckP_UI = "36"
		self.DBGV.Data_SettingClick[2] = self.DBGV.Data_SettingClick[2] + 1
		newSpace = ""
		for i in range(15):
			newSpace = newSpace + " "
		if self.TKS_DisGroup.get() != "":
			self.DisGroupType = self.TKS_DisGroup.get()
			self.TKS_Show_DisGroup.config(text="Group: %s%s" %(self.DisGroupType,newSpace), fg="black")
			self.DBGV.Data_ModelRT_Str = CreateModelRTStr(self.OperaType, self.DisDays[1], self.DisDays[2], self.DiseaseType, self.DisGroupType, self.Rat_ID)
		# if(self.DisGroupCombo.current() != 0):
		# 	self.DisGroupType = self.DisGroupCombo.get()
		# 	self.TKS_Show_DisGroup.config(text="Group: %s" %(self.DisGroupType), fg="black")
	
	def tkSetting_ModifyDisease(self, val): #設定UI視窗在[修改病因陣列]區域點擊[新增/修改病因]按鈕後處理副程式
		DBGV.CheckP_UI = "37"
		if val == 'new':
			self.TKS_Btn2_DCM1.config(bg="DarkOliveGreen2")
			self.TKS_Btn2_DCM2.config(bg="gray90")
			self.TKS_DCM_Name.config(state="normal")
			self.TKS_DCM_Description.config(state="normal")
			self.ModifyDCM.config(state="disabled")
			self.TKS_Btn2_DCM1.config(state="disabled")
			self.TKS_Btn2_DCM2.config(state="disabled")
			self.NOW_DiseaseList[0] = -1
			self.TKS_DCM_Confirm.config(state="normal")
			self.TKS_DCM_Cancel.config(state="normal")
		elif val == 'edit':
			if(self.ModifyDCM.current() != 0):
				self.TKS_Btn2_DCM1.config(bg="gray90")
				self.TKS_Btn2_DCM2.config(bg="DarkOliveGreen2")
				self.TKS_DCM_Name.config(state="normal")
				self.TKS_DCM_Description.config(state="normal")
				idx = findDiseaseArray(self.CSV_DiseaseFile, 'Disease', self.ModifyDCM.get())
				if idx != -1:
					self.TKS_DCM_Name.insert(0, self.CSV_DiseaseFile[idx][1])
					self.TKS_DCM_Description.insert(0, self.CSV_DiseaseFile[idx][2])
					self.NOW_DiseaseList = [idx, 'Disease', self.CSV_DiseaseFile[idx][1], self.CSV_DiseaseFile[idx][2]]
				self.ModifyDCM.config(state="disabled")
				self.TKS_Btn2_DCM1.config(state="disabled")
				self.TKS_Btn2_DCM2.config(state="disabled")
				self.TKS_DCM_Confirm.config(state="normal")
			self.TKS_DCM_Cancel.config(state="normal")
	
	def tkSetting_ModifyGroupDisease(self, val): #設定UI視窗在[修改疾病組別陣列]區域點擊[新增/修改疾病組別陣列]按鈕後處理副程式
		DBGV.CheckP_UI = "38"
		if val == 'new':
			self.TKS_Btn2_DGCM1.config(bg="DarkOliveGreen2")
			self.TKS_Btn2_DGCM2.config(bg="gray90")
			self.TKS_DGCM_Name.config(state="normal")
			self.TKS_DGCM_Description.config(state="normal")
			self.ModifyDGCM.config(state="disabled")
			self.TKS_Btn2_DGCM1.config(state="disabled")
			self.TKS_Btn2_DGCM2.config(state="disabled")
			self.NOW_DiseaseList[0] = -1
			self.TKS_DGCM_Confirm.config(state="normal")
			self.TKS_DGCM_Cancel.config(state="normal")
		elif val == 'edit':
			if(self.ModifyDGCM.current() != 0):
				self.TKS_Btn2_DGCM1.config(bg="gray90")
				self.TKS_Btn2_DGCM2.config(bg="DarkOliveGreen2")
				self.TKS_DGCM_Name.config(state="normal")
				self.TKS_DGCM_Description.config(state="normal")
				idx = findDiseaseArray(self.CSV_DiseaseFile, 'DisGroup', self.ModifyDGCM.get())
				if idx != -1:
					self.TKS_DGCM_Name.insert(0, self.CSV_DiseaseFile[idx][1])
					self.TKS_DGCM_Description.insert(0, self.CSV_DiseaseFile[idx][2])
					self.NOW_DiseaseList = [idx, 'DisGroup', self.CSV_DiseaseFile[idx][1], self.CSV_DiseaseFile[idx][2]]
				self.ModifyDGCM.config(state="disabled")
				self.TKS_Btn2_DGCM1.config(state="disabled")
				self.TKS_Btn2_DGCM2.config(state="disabled")
				self.TKS_DGCM_Confirm.config(state="normal")
			self.TKS_DGCM_Cancel.config(state="normal")

	def tkSetting_DiseaseModify(self): #設定UI視窗點擊[修改病因陣列]按鈕後處理副程式
		DBGV.CheckP_UI = "38"
		self.DiseaseCombo.current(0)
		self.DiseaseCombo.config(state="disabled")
		self.TKS_BT_DisConfirm.config(state="disabled")
		self.TKS_BT_DisModify.config(state="disabled")
		self.TKS_Btn2_DCM1.config(state="normal")
		self.TKS_Btn2_DCM2.config(state="normal")
		self.ModifyDCM.config(state="readonly")
		self.TKS_DCM_Cancel.config(state="normal")
		self.TKS_title6.config(bg="gray75")

	def tkSetting_ModifyDiseaseConfirm(self): #設定UI視窗在[修改病因陣列]區域點擊[確認]按鈕後處理副程式
		DBGV.CheckP_UI = "39"
		self.DiseaseCombo.config(state="readonly")
		self.TKS_BT_DisConfirm.config(state="normal")
		self.TKS_BT_DisModify.config(state="normal")
		self.TKS_Btn2_DCM1.config(state="disabled")
		self.TKS_Btn2_DCM2.config(state="disabled")
		self.TKS_Btn2_DCM1.config(bg="gray90")
		self.TKS_Btn2_DCM2.config(bg="gray90")

		self.NOW_DiseaseList[1:] = ['Disease', self.TKS_DCM_Name.get(), self.TKS_DCM_Description.get()]
		self.tkSetting_UploadDisease('Disease', self.NOW_DiseaseList)

		self.TKS_DCM_Name.delete(first=0,last=50)
		self.TKS_DCM_Description.delete(first=0,last=50)
		self.TKS_DCM_Name.config(state="disabled")
		self.TKS_DCM_Description.config(state="disabled")

		self.ModifyDCM.config(state="disabled")
		self.TKS_DCM_Confirm.config(state="disabled")
		self.TKS_DCM_Cancel.config(state="disabled")
		self.TKS_title6.config(bg="gray85")

	def tkSetting_ModifyDiseaseCancel(self): #設定UI視窗在[修改病因陣列]區域點擊[取消]按鈕後處理副程式
		DBGV.CheckP_UI = "39"
		self.DiseaseCombo.config(state="readonly")
		self.TKS_BT_DisConfirm.config(state="normal")
		self.TKS_BT_DisModify.config(state="normal")
		self.TKS_Btn2_DCM1.config(state="disabled")
		self.TKS_Btn2_DCM2.config(state="disabled")
		self.TKS_Btn2_DCM1.config(bg="gray90")
		self.TKS_Btn2_DCM2.config(bg="gray90")
		self.TKS_DCM_Name.delete(first=0,last=50)
		self.TKS_DCM_Description.delete(first=0,last=50)
		self.TKS_DCM_Name.config(state="disabled")
		self.TKS_DCM_Description.config(state="disabled")
		self.ModifyDCM.current(0)
		self.ModifyDCM.config(state="disabled")
		self.TKS_DCM_Confirm.config(state="disabled")
		self.TKS_DCM_Cancel.config(state="disabled")
		self.TKS_title6.config(bg="gray85")

	def tkSetting_DisGroupModify(self): #設定UI視窗點擊[修改疾病組別陣列]按鈕後處理副程式
		DBGV.CheckP_UI = "40"
		self.DisGroupCombo.current(0)
		self.DisGroupCombo.config(state="disabled")
		self.TKS_BT_DisGroupConfirm.config(state="disabled")
		self.TKS_BT_DisGroupModify.config(state="disabled")
		self.TKS_Btn2_DGCM1.config(state="normal")
		self.TKS_Btn2_DGCM2.config(state="normal")
		self.ModifyDGCM.config(state="readonly")
		self.TKS_DGCM_Cancel.config(state="normal")
		self.TKS_title7.config(bg="gray75")

	def tkSetting_ModifyDisGroupConfirm(self): #設定UI視窗在[修改疾病組別陣列]區域點擊[確認]按鈕後處理副程式
		DBGV.CheckP_UI = "41"
		self.DisGroupCombo.config(state="readonly")
		self.TKS_BT_DisGroupConfirm.config(state="normal")
		self.TKS_BT_DisGroupModify.config(state="normal")
		self.TKS_Btn2_DGCM1.config(state="disabled")
		self.TKS_Btn2_DGCM2.config(state="disabled")
		self.TKS_Btn2_DGCM1.config(bg="gray90")
		self.TKS_Btn2_DGCM2.config(bg="gray90")

		self.NOW_DiseaseList[1:] = ['DisGroup', self.TKS_DGCM_Name.get(), self.TKS_DGCM_Description.get()]
		self.tkSetting_UploadDisease('DisGroup', self.NOW_DiseaseList)

		self.TKS_DGCM_Name.delete(first=0,last=50)
		self.TKS_DGCM_Description.delete(first=0,last=50)
		self.TKS_DGCM_Name.config(state="disabled")
		self.TKS_DGCM_Description.config(state="disabled")

		self.ModifyDGCM.config(state="disabled")
		self.TKS_DGCM_Confirm.config(state="disabled")
		self.TKS_DGCM_Cancel.config(state="disabled")
		self.TKS_title7.config(bg="gray85")
	
	def tkSetting_ModifyDisGroupCancel(self): #設定UI視窗在[修改疾病組別陣列]區域點擊[取消]按鈕後處理副程式
		DBGV.CheckP_UI = "42"
		self.DisGroupCombo.config(state="readonly")
		self.TKS_BT_DisGroupConfirm.config(state="normal")
		self.TKS_BT_DisGroupModify.config(state="normal")
		self.TKS_Btn2_DGCM1.config(state="disabled")
		self.TKS_Btn2_DGCM2.config(state="disabled")
		self.TKS_Btn2_DGCM1.config(bg="gray90")
		self.TKS_Btn2_DGCM2.config(bg="gray90")
		self.TKS_DGCM_Name.delete(first=0,last=50)
		self.TKS_DGCM_Description.delete(first=0,last=50)
		self.TKS_DGCM_Name.config(state="disabled")
		self.TKS_DGCM_Description.config(state="disabled")
		self.ModifyDGCM.current(0)
		self.ModifyDGCM.config(state="disabled")
		self.TKS_DGCM_Confirm.config(state="disabled")
		self.TKS_DGCM_Cancel.config(state="disabled")
		self.TKS_title7.config(bg="gray85")

	
	def tkSetting_OperaDays(self): #設定UI視窗點擊[確認天數]按鈕後處理副程式
		DBGV.CheckP_UI = "43"
		self.DBGV.Data_SettingClick[0] = self.DBGV.Data_SettingClick[0] + 1
		if self.TKS_OpDay_Month.get() == "":
			self.DisDays[1] = 0
		else:
			self.DisDays[1] = int(self.TKS_OpDay_Month.get())
		if self.TKS_OpDay_Day.get() == "":
			self.DisDays[2] = 0
		else:
			self.DisDays[2] = int(self.TKS_OpDay_Day.get())
		self.TKS_Show_OpDay.config(text="TimePoint: %2d Month %2d Day     " %(self.DisDays[1], self.DisDays[2]), fg="black")
		self.DBGV.Data_ModelRT_Str = CreateModelRTStr(self.OperaType, self.DisDays[1], self.DisDays[2], self.DiseaseType, self.DisGroupType, self.Rat_ID)

	def tkSetting_Closing(self): #設定UI視窗關閉副程式
		DBGV.CheckP_UI = "22"
		self.SETTING_OPEN = False
		self.DBGV.Maze_SetState = False
		self.BT_Setting.config(state="normal")
		self.tkSetting.destroy()

	def tkSetting_SetupUI(self): #設定UI視窗主要程式
		global Disease_List
		DBGV.CheckP_UI = "18"
		try:
			self.DBGV.Maze_SetState = True
			LoadDiseaseFile()
			self.CSV_DiseaseFile = Disease_List

			self.SETTING_OPEN = True
			settingSize = (768, 400)
			self.tkSetting = tk.Tk()
			self.tkSetting.title('%d臂迷宮路徑追蹤系統設定' %(self.ARM_UNIT)) #窗口名字
			self.tkSetting.geometry('%dx%d+120+120' %(settingSize[0],settingSize[1])) #窗口大小(寬X高+X偏移量+Y偏移量)
			self.tkSetting.resizable(False, False) #禁止變更視窗大小

			self.TKS_RadValue = tk.IntVar()

			# 選擇狀態是手術前後
			self.TKS_title1 = tk.Label(self.tkSetting, text="Operation", font=('Arial', 12), bg="gray75")
			self.TKS_title1.place(x=20,y=20,anchor="nw")
			self.TKS_Btn1_Opera1 = tk.Button(self.tkSetting, text='pre-Op (手術前)', width=14, font=('Arial', 10), bg="gray90", command=lambda: self.tkSetting_BtnOpera('pre-Op'))
			self.TKS_Btn1_Opera1.place(x=100,y=18,anchor="nw")
			self.TKS_Btn1_Opera2 = tk.Button(self.tkSetting, text='past-Op (手術後)', width=14, font=('Arial', 10), bg="gray90", command=lambda: self.tkSetting_BtnOpera('past-Op'))
			self.TKS_Btn1_Opera2.place(x=225,y=18,anchor="nw")
			
			# 設定天數
			self.TKS_title2 = tk.Label(self.tkSetting, text="Op. Days", font=('Arial', 12), bg="gray75")
			self.TKS_title2.place(x=20,y=55,anchor="nw")
			self.TKS_OpDay_Month = tk.Entry(self.tkSetting, font=('Arial', 12), width=6, justify="right")
			self.TKS_OpDay_Month.place(x=100,y=56,anchor="nw")
			tk.Label(self.tkSetting, text="Month", font=('Arial', 10)).place(x=160,y=56,anchor="nw")
			self.TKS_OpDay_Day = tk.Entry(self.tkSetting, font=('Arial', 12), width=6, justify="right")
			self.TKS_OpDay_Day.place(x=220,y=56,anchor="nw")
			tk.Label(self.tkSetting, text="Day", font=('Arial', 10)).place(x=280,y=56,anchor="nw")
			self.TKS_BT_OpDayConfirm = tk.Button(self.tkSetting, text='Confirm', width=9, font=('Arial', 10), bg="gray90", command=self.tkSetting_OperaDays)
			self.TKS_BT_OpDayConfirm.place(x=320,y=53,anchor="nw")

			#疾病資訊選擇(下拉選單)
			DiseaseInfo = ['choose Model...']
			self.TKS_title3 = tk.Label(self.tkSetting, text="Model", font=('Arial', 12), bg="gray75")
			self.TKS_title3.place(x=20,y=90,anchor="nw")
			for i in range(len(self.CSV_DiseaseFile)):
				if self.CSV_DiseaseFile[i][0] == 'Model':
					DiseaseInfo.append(self.CSV_DiseaseFile[i][1])
			self.DiseaseCombo = ttk.Combobox(self.tkSetting, values=DiseaseInfo, state="readonly")
			self.DiseaseCombo.place(x=92,y=93,anchor="nw")
			self.DiseaseCombo.current(0)
			self.TKS_BT_DisConfirm = tk.Button(self.tkSetting, text='Confirm', width=9, font=('Arial', 10), bg="gray90", command=self.tkSetting_DiseaseConfirm)
			self.TKS_BT_DisConfirm.place(x=260,y=87,anchor="nw")
			self.TKS_BT_DisModify = tk.Button(self.tkSetting, text='Modify', width=9, font=('Arial', 10), bg="gray90", command=self.tkSetting_DiseaseModify)
			self.TKS_BT_DisModify.place(x=345,y=87,anchor="nw")

			#復健資訊選擇(下拉選單)
			DisGroupInfo = ['choose Group...']
			self.TKS_title4 = tk.Label(self.tkSetting, text="Group", font=('Arial', 12), bg="gray75")
			self.TKS_title4.place(x=20,y=125,anchor="nw")
			for i in range(len(self.CSV_DiseaseFile)):
				if self.CSV_DiseaseFile[i][0] == 'DisGroup':
					DisGroupInfo.append(self.CSV_DiseaseFile[i][1])
			self.DisGroupCombo = ttk.Combobox(self.tkSetting, values=DisGroupInfo, state="readonly")
			self.DisGroupCombo.place(x=92,y=127,anchor="nw")
			self.DisGroupCombo.current(0)
			self.TKS_BT_DisGroupConfirm = tk.Button(self.tkSetting, text='Confirm', width=9, font=('Arial', 10), bg="gray90", command=self.tkSetting_DisGroupConfirm)
			self.TKS_BT_DisGroupConfirm.place(x=260,y=122,anchor="nw")
			self.TKS_BT_DisGroupModify = tk.Button(self.tkSetting, text='Modify', width=9, font=('Arial', 10), bg="gray90", command=self.tkSetting_DisGroupModify)
			self.TKS_BT_DisGroupModify.place(x=345,y=122,anchor="nw")
			
			# 顯示變數區域
			self.TKS_title5 = tk.Label(self.tkSetting, text="Setting Status", font=('Arial', 12), bg="gray75")
			self.TKS_title5.place(x=450,y=20,anchor="nw")
			if self.OperaType != "":
				self.TKS_Show_Opera = tk.Label(self.tkSetting, text="Operation Type: {}".format(self.OperaType), font=('Arial', 13), fg="black")
			else:
				self.TKS_Show_Opera = tk.Label(self.tkSetting, text="Operation Type: (not set)", font=('Arial', 13), fg="gray35")
			self.TKS_Show_Opera.place(x=450,y=50,anchor="nw")
			
			if self.DisDays[1] != -1 and self.DisDays[2] != -1:
				self.TKS_Show_OpDay = tk.Label(self.tkSetting, text="Operation Days: %2d Month %2d Day" %(self.DisDays[1], self.DisDays[2]), font=('Arial', 13), fg="black")
			else:
				self.TKS_Show_OpDay = tk.Label(self.tkSetting, text="Operation Days: (not set)", font=('Arial', 13), fg="gray35")
			self.TKS_Show_OpDay.place(x=450,y=80,anchor="nw")
			if self.DiseaseType != "":
				self.TKS_Show_Disease = tk.Label(self.tkSetting, text="Operation Type: {}".format(self.DiseaseType), font=('Arial', 13), fg="black")
			else:
				self.TKS_Show_Disease = tk.Label(self.tkSetting, text="Model: (not set)", font=('Arial', 13), fg="gray35")
			self.TKS_Show_Disease.place(x=450,y=110,anchor="nw")
			if self.DisGroupType != "":
				self.TKS_Show_DisGroup = tk.Label(self.tkSetting, text="Group: {}".format(self.DisGroupType), font=('Arial', 13), fg="black")
			else:
				self.TKS_Show_DisGroup = tk.Label(self.tkSetting, text="Group: (not set)", font=('Arial', 13), fg="gray35")
			self.TKS_Show_DisGroup.place(x=450,y=140,anchor="nw")

			# 修改病因區域
			self.TKS_DCM_Name_val = tk.StringVar()
			self.TKS_DCM_Description_val = tk.StringVar()
			# self.TKS_DCM_Name_val = "111"
			# self.TKS_DCM_Description_val = "111"
			self.TKS_title6 = tk.Label(self.tkSetting, text="Model Combobox Modify", font=('Arial', 12), bg="gray85")
			self.TKS_title6.place(x=20,y=180,anchor="nw")
			self.ModifyDCM = ttk.Combobox(self.tkSetting, values=DiseaseInfo, state="disabled")
			self.ModifyDCM.place(x=20,y=214,anchor="nw")
			self.ModifyDCM.current(0)
			self.TKS_Btn2_DCM1 = tk.Button(self.tkSetting, text='New Item', width=9, state="disabled", font=('Arial', 10), bg="gray90", command=lambda: self.tkSetting_ModifyDisease('new'))
			self.TKS_Btn2_DCM1.place(x=273,y=210,anchor="nw")
			self.TKS_Btn2_DCM2 = tk.Button(self.tkSetting, text='Edit Item', width=9, state="disabled", font=('Arial', 10), bg="gray90", command=lambda: self.tkSetting_ModifyDisease('edit'))
			self.TKS_Btn2_DCM2.place(x=190,y=210,anchor="nw")
			tk.Label(self.tkSetting, text="Model Name", font=('Arial', 9)).place(x=20,y=240,anchor="nw")
			self.TKS_DCM_Name = tk.Entry(self.tkSetting, font=('Arial', 12), textvariable=self.TKS_DCM_Name_val, state="disabled")
			self.TKS_DCM_Name.place(x=20,y=257,anchor="nw")
			tk.Label(self.tkSetting, text="Model Description (Optional)", font=('Arial', 9)).place(x=20,y=285,anchor="nw")
			self.TKS_DCM_Description = tk.Entry(self.tkSetting, font=('Arial', 12), textvariable=self.TKS_DCM_Description_val, width=35, state="disabled")
			self.TKS_DCM_Description.place(x=20,y=303,anchor="nw")
			tk.Label(self.tkSetting, text="※請敘述一下疾病中文名稱", font=('Arial', 9)).place(x=20,y=325,anchor="nw")
			self.TKS_DCM_Confirm = tk.Button(self.tkSetting, text='Confirm', width=9, font=('Arial', 10), bg="gray90", state="disabled", command=self.tkSetting_ModifyDiseaseConfirm)
			self.TKS_DCM_Confirm.place(x=20,y=350,anchor="nw")
			self.TKS_DCM_Cancel = tk.Button(self.tkSetting, text='Cancel', width=9, font=('Arial', 10), bg="gray90", state="disabled", command=self.tkSetting_ModifyDiseaseCancel)
			self.TKS_DCM_Cancel.place(x=110,y=350,anchor="nw")

			# 修改病因組別區域
			self.TKS_DGCM_Name_val = tk.StringVar()
			self.TKS_DGCM_Description_val = tk.StringVar()
			# self.TKS_DGCM_Name_val = ""
			# self.TKS_DGCM_Description_val = ""
			self.TKS_title7 = tk.Label(self.tkSetting,text="Group Combobox Modify", font=('Arial', 12), bg="gray85")
			self.TKS_title7.place(x=390,y=180,anchor="nw")
			self.ModifyDGCM = ttk.Combobox(self.tkSetting, values=DisGroupInfo, state="disabled")
			self.ModifyDGCM.place(x=390,y=214,anchor="nw")
			self.ModifyDGCM.current(0)
			self.TKS_Btn2_DGCM1 = tk.Button(self.tkSetting, text='New Item', width=9, state="disabled", font=('Arial', 10), bg="gray90", command=lambda: self.tkSetting_ModifyGroupDisease('new'))
			self.TKS_Btn2_DGCM1.place(x=643,y=210,anchor="nw")
			self.TKS_Btn2_DGCM2 = tk.Button(self.tkSetting, text='Edit Item', width=9, state="disabled", font=('Arial', 10), bg="gray90", command=lambda: self.tkSetting_ModifyGroupDisease('edit'))
			self.TKS_Btn2_DGCM2.place(x=560,y=210,anchor="nw")
			tk.Label(self.tkSetting, text="Group Name", font=('Arial', 9)).place(x=390,y=240,anchor="nw")
			self.TKS_DGCM_Name = tk.Entry(self.tkSetting, font=('Arial', 12), textvariable=self.TKS_DGCM_Name_val, state="disabled")
			self.TKS_DGCM_Name.place(x=390,y=257,anchor="nw")
			tk.Label(self.tkSetting, text="Group Description (Optional)", font=('Arial', 9)).place(x=390,y=285,anchor="nw")
			self.TKS_DGCM_Description = tk.Entry(self.tkSetting, font=('Arial', 12), width=35, textvariable=self.TKS_DGCM_Description_val, state="disabled")
			self.TKS_DGCM_Description.place(x=390,y=303,anchor="nw")
			tk.Label(self.tkSetting, text="※請敘述一下疾病復健組別內容", font=('Arial', 9)).place(x=390,y=325,anchor="nw")
			self.TKS_DGCM_Confirm = tk.Button(self.tkSetting, text='Confirm', width=9, font=('Arial', 10), bg="gray90", state="disabled", command=self.tkSetting_ModifyDisGroupConfirm)
			self.TKS_DGCM_Confirm.place(x=390,y=350,anchor="nw")
			self.TKS_DGCM_Cancel = tk.Button(self.tkSetting, text='Cancel', width=9, font=('Arial', 10), bg="gray90", state="disabled", command=self.tkSetting_ModifyDisGroupCancel)
			self.TKS_DGCM_Cancel.place(x=480,y=350,anchor="nw")
			
			DBGV.CheckP_UI = "19"
			self.BT_Setting.config(state="disabled")
			self.tkSetting.protocol("WM_DELETE_WINDOW", self.tkSetting_Closing)
			self.tkSetting.mainloop()
			DBGV.CheckP_UI = "20"
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
	
	def InitExpMode(self, mode):
		if mode == "EXPERIMENT":
			self.TK_Rat_ID.config(state="normal")
			self.BT_Rat_ID.config(state="normal")
			self.TKS_Btn1_Opera1.config(state="normal")
			self.TKS_Btn1_Opera2.config(state="normal")
			self.TKS_OpDay_Month.config(state="normal")
			self.TKS_OpDay_Day.config(state="normal")
			self.TKS_DisGroup.config(state="normal")
			self.TKS_BT_OpDayConfirm.config(state="normal")
			self.TKS_BT_DisGroupConfirm.config(state="normal")
		elif mode == "TRAINING":
			self.DisGroupType = "Training"
			self.DisDays = [self.DisDays[0], 99, 99]
			self.OperaType = "Training"
			self.Rat_ID = datetime.datetime.now().strftime("T%H%M%S")

			self.TKS_Show_DisGroup.config(text="Group: %s" %(self.DisGroupType), fg="black")
			self.TKS_Show_OpDay.config(text="TimePoint: %2d Month %2d Day" %(self.DisDays[1], self.DisDays[2]), fg="black")
			self.TKS_Show_Opera.config(text="Operation Type: %s" %(self.OperaType), fg="black")
			self.TKS_Show_Rat_ID.config(text="RatID: %s" %(self.Rat_ID), fg="black")

		self.TK_User_Name.config(state="normal")
		self.BT_User_Name.config(state="normal")
		self.TKS_Disease.config(state="normal")
		self.TKS_BT_DisConfirm.config(state="normal")

	def SystemModeSet(self, mode):
		self.EXP_DATA_MODE = mode
		self.InitExpMode(mode)
		if mode == "EXPERIMENT":
			self.TKS_Btn0_Mode2.config(bg="DarkOliveGreen2")
		elif mode == "TRAINING":
			self.TKS_Btn0_Mode1.config(bg="DarkOliveGreen2")
		self.TKS_Btn0_Mode1.config(state="disabled")
		self.TKS_Btn0_Mode2.config(state="disabled")
		self.TKS_title1_0.config(fg="gray35", bg="gray85")
		self.TKS_title1_1.config(fg="black", bg="gray75")

	def drawSetting(self):
		SettingShowX = self.WinSize[0] + 10
		tk.Label(self.tkWin, text="Model/Group Configuration", font=('Arial', 14), bg="gray75").place(x=SettingShowX + 180,y=20,anchor="n")

		# 選擇訓練中還是行為測試
		SettingShowY = 60
		self.TKS_title1_0 = tk.Label(self.tkWin, text="Step1. 請選擇使用目的", font=('微軟正黑體', 12, "bold"), bg="gray75")
		self.TKS_title1_0.place(x=SettingShowX+180,y=SettingShowY,anchor="n")
		if self.EXP_DATA_MODE == "TRAINING":
			self.TKS_Btn0_Mode1 = tk.Button(self.tkWin, text='大鼠訓練', width=14, font=('微軟正黑體', 14, "bold"), bg="DarkOliveGreen2", command=lambda: self.SystemModeSet('TRAINING'))
		else:
			self.TKS_Btn0_Mode1 = tk.Button(self.tkWin, text='大鼠訓練', width=14, font=('微軟正黑體', 14, "bold"), bg="gray90", command=lambda: self.SystemModeSet('TRAINING'))
		self.TKS_Btn0_Mode1.place(x=SettingShowX + 10, y=SettingShowY + 30, anchor="nw")

		if self.EXP_DATA_MODE == "EXPERIMENT":
			self.TKS_Btn0_Mode2 = tk.Button(self.tkWin, text='行為測試', width=14, font=('微軟正黑體', 14, "bold"), bg="DarkOliveGreen2", command=lambda: self.SystemModeSet('EXPERIMENT'))
		else:
			self.TKS_Btn0_Mode2 = tk.Button(self.tkWin, text='行為測試', width=14, font=('微軟正黑體', 14, "bold"), bg="gray90", command=lambda: self.SystemModeSet('EXPERIMENT'))
		self.TKS_Btn0_Mode2.place(x=SettingShowX + 190, y=SettingShowY + 30, anchor="nw")

		if self.EXP_DATA_MODE != "NONE":
			self.TKS_Btn0_Mode1.config(state="disabled")
			self.TKS_Btn0_Mode2.config(state="disabled")
			self.TKS_title1_0.config(fg="gray35", bg="gray85")

		SettingShowY = 150
		self.TKS_title1_1 = tk.Label(self.tkWin, text="Step2. 請輸入以下資訊", font=('微軟正黑體', 12, "bold"))
		self.TKS_title1_1.place(x=SettingShowX+180,y=SettingShowY,anchor="n")
		if self.EXP_DATA_MODE == "NONE":
			self.TKS_title1_1.config(fg="gray35", bg="gray85")
		else:
			self.TKS_title1_1.config(fg="black", bg="gray75")
		# 設定使用者名稱
		SettingShowY = 190
		Rec_UserName_Def = tk.StringVar()
		tk.Label(self.tkWin,text="User", font=('Arial', 12), bg="gray75").place(x=SettingShowX, y=SettingShowY,anchor="nw")
		self.TK_User_Name = tk.Entry(self.tkWin, font=('Arial', 12), width=15, textvariable=Rec_UserName_Def)
		self.TK_User_Name.place(x=SettingShowX+56,y=SettingShowY+1,anchor="nw")
		if self.Rec_UserName != "":
			Rec_UserName_Def.set(self.Rec_UserName)
		self.BT_User_Name = tk.Button(self.tkWin, text='Set User', width=9, font=('Arial', 10), bg="gray90", command=self.SetUserName)
		self.BT_User_Name.place(x=SettingShowX+200,y=SettingShowY-3,anchor="nw")
		if self.EXP_DATA_MODE == "NONE":
			self.TK_User_Name.config(state="disabled")
			self.BT_User_Name.config(state="disabled")

		#疾病模組資訊
		SettingShowY = 230
		Disease_Def = tk.StringVar()
		self.TKS_title3 = tk.Label(self.tkWin, text="Model", font=('Arial', 12), bg="gray75")
		self.TKS_title3.place(x=SettingShowX,y=SettingShowY,anchor="nw")
		self.TKS_Disease = tk.Entry(self.tkWin, font=('Arial', 12), width=15, textvariable=Disease_Def)
		self.TKS_Disease.place(x=SettingShowX+57,y=SettingShowY+1,anchor="nw")
		if self.DiseaseType != "":
			Disease_Def.set(self.DiseaseType)
		self.TKS_BT_DisConfirm = tk.Button(self.tkWin, text='Confirm', width=9, font=('Arial', 10), bg="gray90", command=self.tkSetting_DiseaseConfirm)
		self.TKS_BT_DisConfirm.place(x=SettingShowX+205,y=SettingShowY-3,anchor="nw")
		if self.EXP_DATA_MODE == "NONE":
			self.TKS_Disease.config(state="disabled")
			self.TKS_BT_DisConfirm.config(state="disabled")

		#復健分組資訊
		SettingShowY = 270
		DisGroup_Def = tk.StringVar()
		self.TKS_title3 = tk.Label(self.tkWin, text="Group", font=('Arial', 12), bg="gray75")
		self.TKS_title3.place(x=SettingShowX,y=SettingShowY,anchor="nw")
		self.TKS_DisGroup = tk.Entry(self.tkWin, font=('Arial', 12), width=15, textvariable=DisGroup_Def)
		self.TKS_DisGroup.place(x=SettingShowX+57,y=SettingShowY+1,anchor="nw")
		if self.DisGroupType != "":
			DisGroup_Def.set(self.DisGroupType)
		self.TKS_BT_DisGroupConfirm = tk.Button(self.tkWin, text='Confirm', width=9, font=('Arial', 10), bg="gray90", command=self.tkSetting_DisGroupConfirm)
		self.TKS_BT_DisGroupConfirm.place(x=SettingShowX+205,y=SettingShowY-3,anchor="nw")
		if (self.EXP_DATA_MODE == "NONE") or (self.EXP_DATA_MODE == "TRAINING"):
			self.TKS_DisGroup.config(state="disabled")
			self.TKS_BT_DisGroupConfirm.config(state="disabled")

		# 選擇狀態是手術前後
		SettingShowY = 310
		self.TKS_title1 = tk.Label(self.tkWin, text="Operation", font=('Arial', 12), bg="gray75")
		self.TKS_title1.place(x=SettingShowX,y=SettingShowY,anchor="nw")
		if self.OperaType == 'pre':
			self.TKS_Btn1_Opera1 = tk.Button(self.tkWin, text='pre-Op (手術前)', width=14, font=('Arial', 10), bg="DarkOliveGreen2", command=lambda: self.tkSetting_BtnOpera('pre-Op'))
		else:
			self.TKS_Btn1_Opera1 = tk.Button(self.tkWin, text='pre-Op (手術前)', width=14, font=('Arial', 10), bg="gray90", command=lambda: self.tkSetting_BtnOpera('pre-Op'))
		self.TKS_Btn1_Opera1.place(x=SettingShowX + 80, y=SettingShowY - 2, anchor="nw")
		if self.OperaType == 'past':
			self.TKS_Btn1_Opera2 = tk.Button(self.tkWin, text='past-Op (手術後)', width=14, font=('Arial', 10), bg="DarkOliveGreen2", command=lambda: self.tkSetting_BtnOpera('past-Op'))
		else:
			self.TKS_Btn1_Opera2 = tk.Button(self.tkWin, text='past-Op (手術後)', width=14, font=('Arial', 10), bg="gray90", command=lambda: self.tkSetting_BtnOpera('past-Op'))
		self.TKS_Btn1_Opera2.place(x=SettingShowX + 205, y=SettingShowY - 2, anchor="nw")
		if (self.EXP_DATA_MODE == "NONE") or (self.EXP_DATA_MODE == "TRAINING"):
			self.TKS_Btn1_Opera1.config(state="disabled")
			self.TKS_Btn1_Opera2.config(state="disabled")

		# 設定天數
		SettingShowY = 350
		OpDayM_Def = tk.StringVar()
		OpDayD_Def = tk.StringVar()
		self.TKS_title2 = tk.Label(self.tkWin, text="TimePoint", font=('Arial', 12), bg="gray75")
		self.TKS_title2.place(x=SettingShowX,y=SettingShowY+2,anchor="nw")
		self.TKS_OpDay_Month = tk.Entry(self.tkWin, font=('Arial', 12), width=5, justify="right", textvariable=OpDayM_Def)
		self.TKS_OpDay_Month.place(x=SettingShowX+82,y=SettingShowY+3,anchor="nw")
		tk.Label(self.tkWin, text="Month", font=('Arial', 10)).place(x=SettingShowX+135,y=SettingShowY+3,anchor="nw")
		self.TKS_OpDay_Day = tk.Entry(self.tkWin, font=('Arial', 12), width=5, justify="right", textvariable=OpDayD_Def)
		self.TKS_OpDay_Day.place(x=SettingShowX+180,y=SettingShowY+3,anchor="nw")
		tk.Label(self.tkWin, text="Day", font=('Arial', 10)).place(x=SettingShowX+235,y=SettingShowY+3,anchor="nw")
		if self.DisDays[1] != -1:
			OpDayM_Def.set(self.DisDays[1])
		if self.DisDays[2] != -1:
			OpDayD_Def.set(self.DisDays[2])
		self.TKS_BT_OpDayConfirm = tk.Button(self.tkWin, text='Confirm', width=9, font=('Arial', 10), bg="gray90", command=self.tkSetting_OperaDays)
		self.TKS_BT_OpDayConfirm.place(x=SettingShowX+270,y=SettingShowY,anchor="nw")
		if (self.EXP_DATA_MODE == "NONE") or (self.EXP_DATA_MODE == "TRAINING"):
			self.TKS_OpDay_Month.config(state="disabled")
			self.TKS_OpDay_Day.config(state="disabled")
			self.TKS_BT_OpDayConfirm.config(state="disabled")

		# 設定老鼠編號
		SettingShowY = 390
		RatID_Def = tk.StringVar()
		tk.Label(self.tkWin,text="Rat ID", font=('Arial', 12), bg="gray75").place(x=SettingShowX,y=SettingShowY,anchor="nw")
		self.TK_Rat_ID = tk.Entry(self.tkWin, font=('Arial', 12), width=10, textvariable=RatID_Def)
		self.TK_Rat_ID.place(x=SettingShowX+60,y=SettingShowY+1,anchor="nw")
		if self.Rat_ID != "":
			RatID_Def.set(self.Rat_ID)
		self.BT_Rat_ID = tk.Button(self.tkWin, text='Set ID', width=9, font=('Arial', 10), bg="gray90", command=self.SetRatID)
		self.BT_Rat_ID.place(x=SettingShowX+160,y=SettingShowY-3,anchor="nw")
		if (self.EXP_DATA_MODE == "NONE") or (self.EXP_DATA_MODE == "TRAINING"):
			self.TK_Rat_ID.config(state="disabled")
			self.BT_Rat_ID.config(state="disabled")

	def OpenSetting(self):
		if not self.DBGV.Maze_SetState:
			self.tkWin.geometry('%dx%d+20+20' %(self.WinSize[0]+400,self.WinSize[1])) #窗口大小(寬X高+X偏移量+Y偏移量)
			self.DBGV.Maze_SetState = True
			self.drawSetting()
		else:
			self.tkWin.geometry('%dx%d+20+20' %(self.WinSize[0],self.WinSize[1])) #窗口大小(寬X高+X偏移量+Y偏移量)
			self.DBGV.Maze_SetState = False

	def setupUI(self): #主UI視窗主程式
		global IPCAM_Info
		DBGV.CheckP_UI = "8"
		#========測試用========
		# tk.Button(self.tkWin, text='Testing', width=10, font=('Arial', 8), command=self.PreparingTesting).place(x=300,y=10,anchor="nw")

		#========左上：紀錄變數========
		LoadCamInfo()
		#攝影機資訊選擇(下拉選單)
		CamInfo = ['choose IPCAM...']
		for i in range(len(IPCAM_Info)):
			CamInfo.append(IPCAM_Info[i][0])
		# print(CamInfo)
		self.InfoCombo = ttk.Combobox(self.tkWin, values=CamInfo, state="readonly")
		self.InfoCombo.place(x=20,y=25,anchor="w")
		self.InfoCombo.current(0)

		self.BT_LoadCAM = tk.Button(self.tkWin, text='Load', width=9, font=('Arial', 10), command=self.setIPCAMInfo)
		self.BT_LoadCAM.place(x=190,y=25,anchor="w")

		#========左側：紀錄變數========
		recValX = 20
		recValY = 50
		self.TK_Total_L_Term = tk.StringVar()
		self.TK_Total_S_Term = tk.StringVar()
		self.TK_Latency = tk.StringVar()
		nLate = Second2Datetime(0)
		self.TK_Latency.set("Latency: %02d:%02d:%02d" %(nLate[0],nLate[1],nLate[2]))
		self.TK_Total_L_Term.set("Total Long Term: %d" %(0))
		self.TK_Total_S_Term.set("Total Short Term: %d" %(0))
		tk.Label(self.tkWin,text="Statistics", font=('Arial', 12), bg="gray75").place(x=recValX,y=recValY,anchor="nw")
		tk.Label(self.tkWin,textvariable=self.TK_Total_L_Term, font=('Arial', 14)).place(x=recValX,y=recValY + 30,anchor="nw")
		tk.Label(self.tkWin,textvariable=self.TK_Total_S_Term, font=('Arial', 14)).place(x=recValX,y=recValY + 65,anchor="nw")
		tk.Label(self.tkWin,textvariable=self.TK_Latency, font=('Arial', 14)).place(x=recValX,y=recValY + 100,anchor="nw")

		#========左側：紀錄食物位置和詳細記憶錯誤========
		recFoodTX = 20
		recFoodTY = 195
		tk.Label(self.tkWin,text="Food/Term", font=('Arial', 12), bg="gray75").place(x=recFoodTX,y=recFoodTY,anchor="nw")
		tk.Label(self.tkWin,text="Long Term", font=('Arial', 10)).place(x=recFoodTX + 140,y=recFoodTY + 5,anchor="n")
		tk.Label(self.tkWin,text="Short Term", font=('Arial', 10)).place(x=recFoodTX + 220,y=recFoodTY + 5,anchor="n")
		for i in range(1, self.ARM_UNIT+1):
			self.TK_Food[i-1] = tk.IntVar()
			self.TK_L_Term[i-1] = tk.StringVar()
			self.TK_S_Term[i-1] = tk.StringVar()
			self.TK_L_Term[i-1].set(str(self.L_Term[i-1]))
			self.TK_S_Term[i-1].set(str(self.S_Term[i-1]))
			self.TKC_Food.append(0)
			posY = (recFoodTY + 35) + 38*(i-1)
			tk.Label(self.tkWin,text="Arm "+str(i), font=('Arial', 12)).place(x=recFoodTX,y=posY,anchor="nw")
			self.TKC_Food[i-1] = tk.Checkbutton(self.tkWin, variable=self.TK_Food[i-1], onvalue = 1, offvalue = 0, command=self.setFood, state="disabled")
			self.TKC_Food[i-1].place(x=recFoodTX + 60,y=posY,anchor="nw")
			tk.Label(self.tkWin,textvariable=self.TK_L_Term[i-1], font=('Arial', 12)).place(x=recFoodTX + 140,y=posY,anchor="n")
			tk.Label(self.tkWin,textvariable=self.TK_S_Term[i-1], font=('Arial', 12)).place(x=recFoodTX + 220,y=posY,anchor="n")

		#========中間：虛擬視窗顯示區域========
		self.mazeCanvas = tk.Canvas(bg="black", width = self.ViewSize[0], height = self.ViewSize[1])
		p1 = [int(self.TargetPos[0]/2 - self.BALL_SIZE/2), int(self.TargetPos[1]/2 - self.BALL_SIZE/2)]
		p2 = [int(self.TargetPos[0]/2 + self.BALL_SIZE/2), int(self.TargetPos[1]/2 + self.BALL_SIZE/2)]
		self.TBall = self.mazeCanvas.create_oval(p1[0], p1[1], p2[0], p2[1], fill='red')  #创建一个圆，填充色为`red`红色
		self.setArmNumber()
		self.setArmInLine()

		pViewX = 296 #虛擬視窗左上定位點X
		pViewY = 40 #虛擬視窗左上定位點Y
		self.setArmLine()
		self.mazeCanvas.place(x=pViewX, y=pViewY,anchor="nw")
		self.mazeTitle = tk.Label(self.tkWin,text="IPCAM:", font=('Arial', 12))
		self.mazeTitle.place(x=pViewX, y=pViewY-27,anchor="nw")

		#========右側：按鈕======== #, bg="DarkOliveGreen2"
		self.BT_Camera = tk.Button(self.tkWin, text='Show Camera', width=14, font=('Arial', 14), bg="gray85", command=self.CameraCheck, state="disabled")
		self.BT_Camera.place(x=self.WinSize[0]-20,y=65,anchor="ne")
		# self.BT_Setting = tk.Button(self.tkWin, text='Setting', width=14, font=('Arial', 14), bg="gray85", command=self.tkSetting_SetupUI, state="disabled")
		self.BT_Setting = tk.Button(self.tkWin, text='Setting', width=14, font=('Arial', 14), bg="gray85", command=self.OpenSetting, state="disabled")
		self.BT_Setting.place(x=self.WinSize[0]-190,y=65,anchor="ne")
		self.BT_Start = tk.Button(self.tkWin, text='Start', width=14, font=('Arial', 14),bg="gray85", command=self.MazeStartCheck, state="disabled")
		self.BT_Start.place(x=self.WinSize[0]-20,y=20,anchor="ne")
		self.BT_Connect = tk.Button(self.tkWin, text='Link IPCAM', width=14, font=('Arial', 14),bg="gray85", fg="dark green", command=self.ConnectClick, state="disabled")
		self.BT_Connect.place(x=self.WinSize[0]-190,y=20,anchor="ne")

		#========右側：狀態顯示========
		StatusCateX = 800
		StatusCateY = 140
		StatusLineRange = 28
		tk.Label(self.tkWin,text="Status", font=('Arial', 12), bg="gray75").place(x=StatusCateX, y=110,anchor="nw")
		self.Link_State = tk.Label(self.tkWin,text="IPCAM Link: Unlinked", font=('Arial', 13), fg="gray35")
		self.Link_State.place(x=StatusCateX, y=140,anchor="nw")
		self.Cam_State = tk.Label(self.tkWin,text="Camera State: Unconnect", font=('Arial', 13), fg="gray35")
		self.Cam_State.place(x=StatusCateX, y=170,anchor="nw")
		self.Maze_State = tk.Label(self.tkWin,text="Maze State: Preparing...", font=('Arial', 13), fg="gray35")
		self.Maze_State.place(x=StatusCateX, y=200,anchor="nw")

		# 顯示變數區域
		SettingShowX = 800
		SettingShowY = 220
		SettingLineRange = 28
		self.TKS_title5 = tk.Label(self.tkWin, text="Setting Status", font=('Arial', 12), bg="gray75")
		self.TKS_title5.place(x=SettingShowX,y=SettingShowY + 20,anchor="nw")
		
		self.TK_SHOW_Food = tk.Label(self.tkWin,text="Food: (not set)", font=('Arial', 12), fg="gray35")
		self.TK_SHOW_Food.place(x=SettingShowX, y=SettingShowY + (50 + SettingLineRange*0),anchor="nw")

		if self.Rec_UserName != "":
			self.TKS_Show_UserName = tk.Label(self.tkWin, text="Users: %s" %(self.Rec_UserName), font=('Arial', 13), fg="black")
		else:
			self.TKS_Show_UserName = tk.Label(self.tkWin, text="Users: (not set)", font=('Arial', 13), fg="gray35")
		self.TKS_Show_UserName.place(x=SettingShowX,y=SettingShowY + (50 + SettingLineRange*1),anchor="nw")

		if self.DiseaseType != "":
			self.TKS_Show_Disease = tk.Label(self.tkWin, text="Model: {}".format(self.DiseaseType), font=('Arial', 13), fg="black")
		else:
			self.TKS_Show_Disease = tk.Label(self.tkWin, text="Model: (not set)", font=('Arial', 13), fg="gray35")
		self.TKS_Show_Disease.place(x=SettingShowX,y=SettingShowY + (50 + SettingLineRange*2),anchor="nw")

		if self.DisGroupType != "":
			self.TKS_Show_DisGroup = tk.Label(self.tkWin, text="Group: {}".format(self.DisGroupType), font=('Arial', 13), fg="black")
		else:
			self.TKS_Show_DisGroup = tk.Label(self.tkWin, text="Group: (not set)", font=('Arial', 13), fg="gray35")
		self.TKS_Show_DisGroup.place(x=SettingShowX,y=SettingShowY + (50 + SettingLineRange*3),anchor="nw")

		if self.OperaType != "":
			self.TKS_Show_Opera = tk.Label(self.tkWin, text="Operation Type: %s-Op" %(self.OperaType), font=('Arial', 13), fg="black")
		else:
			self.TKS_Show_Opera = tk.Label(self.tkWin, text="Operation Type: (not set)", font=('Arial', 13), fg="gray35")
		self.TKS_Show_Opera.place(x=SettingShowX,y=SettingShowY + (50 + SettingLineRange*4),anchor="nw")
		
		if self.DisDays[1] != -1 and self.DisDays[2] != -1:
			self.TKS_Show_OpDay = tk.Label(self.tkWin, text="TimePoint: %2d Month %2d Day" %(self.DisDays[1], self.DisDays[2]), font=('Arial', 13), fg="black")
		else:
			self.TKS_Show_OpDay = tk.Label(self.tkWin, text="TimePoint: (not set)", font=('Arial', 13), fg="gray35")
		self.TKS_Show_OpDay.place(x=SettingShowX,y=SettingShowY + (50 + SettingLineRange*5),anchor="nw")

		#========右側：顯示進出臂路徑========
		RouteShowX = 800
		RouteShowY = 440
		if self.Rat_ID != "":
			self.TKS_Show_Rat_ID = tk.Label(self.tkWin, text="RatID: %s" %(self.Rat_ID), font=('Arial', 13), fg="black")
		else:
			self.TKS_Show_Rat_ID = tk.Label(self.tkWin, text="RatID: (not set)", font=('Arial', 13), fg="gray35")
		self.TKS_Show_Rat_ID.place(x=RouteShowX+90,y=RouteShowY,anchor="nw")

		tk.Label(self.tkWin,text="Rat Route", font=('Arial', 12), bg="gray75").place(x=RouteShowX,y=RouteShowY,anchor="nw")
		self.RouteScroll = tk.Scrollbar(self.tkWin)
		self.RouteScroll.place(x=RouteShowX+317,y=RouteShowY+30,anchor="nw", height=57)
		self.RouteText = tk.Text(self.tkWin, font=('Arial', 11), width=39, height=3, yscrollcommand=self.RouteScroll.set)
		self.RouteText.place(x=RouteShowX,y=RouteShowY+30,anchor="nw")
		self.RouteScroll.config(command=self.RouteText.yview)

		#========下方：顯示各項資訊========
		# self.TK_SHOW_FileDir = tk.StringVar()
		self.TK_SHOW_SYS_Msg = tk.StringVar()
		# self.TK_SHOW_FileDir.set("# FileDir: {}{}".format(self.FilePath, self.FileName))
		self.TK_SHOW_SYS_Msg.set("Messenage: " + str(self.SYS_MSG))
		# tk.Label(self.tkWin,textvariable=self.TK_SHOW_FileDir, font=('Arial', 10)).place(x=20,y=self.WinSize[1]-10,anchor="sw")
		self.TK_SHOW_SYS_Msg_Text = tk.Label(self.tkWin,textvariable=self.TK_SHOW_SYS_Msg, font=('Arial', 10))
		self.TK_SHOW_SYS_Msg_Text.place(x=int(self.WinSize[0]/2),y=self.WinSize[1]-7,anchor="sw")

		DBGV.CheckP_UI = "9"

		self.tkWin.protocol("WM_DELETE_WINDOW", self.windowsClosing)
		self.tkWin.after(10,self.LoopMain)
		self.tkWin.mainloop()
		self.thread.join() # 等待子執行緒結束
		self.CAMThread.join()
		self.DBGVThread.join()

		DBGV.CheckP_UI = "10"
		
if __name__ == '__main__':
  MazeMouseTrack()
