# ==============================
# ==== 使用者頁面(UI)處理程式 ====
# ==============================
import random
import datetime
import tkinter as tk
import tkinter.messagebox
from tkinter import filedialog
import threading

# ==== 要連接的程式檔案 ====
# from ThermalCAM import ThermalCAM as TCAM
from InfraredCAM import InfraredCAM as TCAM # 影像處理程式
import DebugVideo as DBGV # 影片紀錄程式
import IPCAM_Frame as IPCAM # 攝像機程式

import logging
import sys
import traceback
import csv
from PIL import Image, ImageTk
import tkinter.ttk as ttk
from _Timer import Timer1
from functools import partial

IPCAM_Info_FileName = "./IPCAM_INFO.csv"
Disease_List_FileName = "./NEW_MODEL_LIST.csv"
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
		IPCAM_Info[i][7] = int(IPCAM_Info[i][7])
		IPCAM_Info[i][8] = int(IPCAM_Info[i][8])
	# print(IPCAM_Info)

def LoadDiseaseFile(): #將[疾病分組檔案]匯入[疾病分組資訊陣列]
	global Disease_List, Disease_List_FileName
	Disease_List = readCSV2List(Disease_List_FileName)
	newDiseaseData = []
	for row in Disease_List:
		if row[0] == "Model":
			newDiseaseData.append([int(row[1]), row[2], []])
		elif row[0] == "Groups":
			for mod in newDiseaseData:
				if mod[0] == int(row[1]):
					mod[2].append([int(row[2]), row[3]])
					mod[2].sort()
	newDiseaseData.sort()
	# print(newDiseaseData)
	return newDiseaseData

def WriteDiseaseFile(data):	#將目前[疾病分組資訊陣列]重新寫入[疾病分組檔案]
	global Disease_List, Disease_List_FileName
	newModel = []
	newGroup = []
	for row in data:
		newModel.append(["Model", row[0], row[1]])
		for gp in row[2]:
			newGroup.append(["Groups", row[0], gp[0], gp[1]])
	if len(newModel) > 0:
		writeData2CSV(Disease_List_FileName, "w", newModel[0])
		for i in range(1, len(newModel)):
			writeData2CSV(Disease_List_FileName, "a", newModel[i])
		if len(newGroup) > 0:
			for i in range(len(newGroup)):
				writeData2CSV(Disease_List_FileName, "a", newGroup[i])

def findDiseaseArray(disArray, text): #找尋目前輸入的內容是否在陣列疾病分組資訊陣列內(有:回傳index+model編號/無:回傳-1,0)
	for i in range(len(disArray)):
		if disArray[i][1] == text:
			return i+1, disArray[i][0]
	return 0, -1

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

def CreateModelRTStr(OpType, OpM, OpD, Model, Group, RatID): #將實驗參數轉換成要傳給DBGV的格式
	#執行一次副程式就重新整理所有實驗參數
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
		# self.BT_* => 他是UI上的按鈕變數
		# (二) 執行緒
		# self.*Thread => 執行緒變數
		# self.CoodiTimer => 他也是執行緒，只是我們教授覺得他是Timer不是執行緒@@
		# (三) 其它
		# 要接我程式碼的人，剩下的自己看啦，我設的變數都有機可循的，英文不會就請自己翻譯
		#============================

		#攝相機執行緒
		self.IPCAM = IPCAM
		self.CAMThread = threading.Thread(target = self.IPCAM.Main) # 執行該子執行緒
		self.CAMThread.setDaemon(True) #將Thread設定為daemon thread(一種在背景執行的thread，具有和main thread一同終止的特性)
		self.CAMThread.start()  # 執行該子執行緒
		DBGV.CheckP_UI = "2-1"

		#主要影像處理執行緒
		self.TCAM = TCAM()
		self.thread = threading.Thread(target = self.TCAM.CameraMain) # 執行該子執行緒
		self.thread.setDaemon(True) #將Thread設定為daemon thread(一種在背景執行的thread，具有和main thread一同終止的特性)
		self.thread.start()  # 執行該子執行緒
		DBGV.CheckP_UI = "2-2"

		#狀態顯示&錄影程式執行緒
		self.DBGV = DBGV
		self.DBGVThread = threading.Thread(target = self.DBGV.DBGV_Main) # 執行該子執行緒
		self.DBGVThread.setDaemon(True) #將Thread設定為daemon thread(一種在背景執行的thread，具有和main thread一同終止的特性)
		self.DBGVThread.start()  # 執行該子執行緒
		DBGV.CheckP_UI = "2-3"

		#取點計時器
		self.CoodiTimer = Timer1(0.046, self.TCAM.saveCoodinate2Arr)
		self.CoodiTimer.setDaemon(True) #將Thread設定為daemon thread(一種在背景執行的thread，具有和main thread一同終止的特性)
		DBGV.CheckP_UI = "2-4"

		#變數：迷宮系統相關
		self.ARM_UNIT = self.TCAM.ARM_UNIT #迷宮臂數
		self.ARMS_POS = self.TCAM.ARMS_POS #迷宮臂座標點
		self.OPEN_CAMERA_WINDOW = False #影像視窗狀態
		self.TotalFood = 0 #放食物的總數
		self.Food = [] #放食物的臂
		self.Route = [] #紀錄進臂順序
		self.S_Term = [] #各臂短期記憶錯誤
		self.L_Term = [] #各臂長期記憶錯誤
		self.TargetPos = self.TCAM.TargetPos #影像處理後取得的座標
		self.nowPos = self.TargetPos
		self.Latency = 0 #總時間長度

		#變數：視窗相關
		self.WinSize = (1040, 560) #UI介面顯示大小
		self.BALL_SIZE = 20
		self.ViewSize = self.TCAM.ViewSize #虛擬視窗顯示大小
		self.MAZE_IS_RUN = False #當前系統是否在執行
		self.CAM_IS_RUN = False #當前相機程式是否在執行
		self.CAM_IS_RUN_First = True #相機程式執行的第一次
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
		self.TK_SHOW_Rat_ID = ""
		self.TK_SHOW_SYS_Msg = ""
		self.TKC_Food = []

		self.InfoCombo = ""
		self.BT_Rat_ID = ""
		self.mazeTitle = "" # UI顯示目前攝影機名稱與其IP位置

		#實驗設定變數統整
		self.OperaType = "" #目前使用模式(前期訓練/正式測試)
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
		self.MENU_OPEN = False #要修改下拉式選單時為TRUE
		self.MENU_INFO = ["", ""] #紀錄要修改的下拉項目資訊
		self.MENU_Modify_Item = ["", "", "", "", "", "", "", "", "", ""] #下拉項目的項目
		DBGV.CheckP_UI = "5"

		self.tkWin = tk.Tk()
		self.tkWin.title('圖像化自動追蹤紀錄動物軌跡%d臂迷宮系統平台 (Ver. %s)' %(self.ARM_UNIT, self.DBGV.SYSTEM_VER)) #窗口名字
		self.tkWin.geometry('%dx%d+10+10' %(self.WinSize[0],self.WinSize[1])) #窗口大小(寬X高+X偏移量+Y偏移量)
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
	
	# ===========================
	# ===== UI主視窗顯示設定 =====
	# ===========================

	def setEachVariable(self): #[初始化] 設定各項變數預設值
		for i in range(0,self.ARM_UNIT):
			self.Food.append(0)
			self.TK_Food.append(0)
			self.L_Term.append(0)
			self.S_Term.append(0)
			self.TK_L_Term.append("0")
			self.TK_S_Term.append("0")

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

	def setArmInLine(self): #設定並繪製進臂線
		DBGV.CheckP_UI = "45"
		ARMS_IN_LINE = self.TCAM.ARMS_IN_LINE
		while len(ARMS_IN_LINE) == 0:
			ARMS_IN_LINE = self.TCAM.ARMS_IN_LINE
			print("ARMS_IN_LINE is null!!")

		for i in range(0, self.ARM_UNIT):
			self.mazeCanvas.create_line(ARMS_IN_LINE[i][0][0], ARMS_IN_LINE[i][0][1], ARMS_IN_LINE[i][1][0], ARMS_IN_LINE[i][1][1], fill="DarkGoldenrod4", width=3)

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

	def SetRatID(self): #設定老鼠編號
		DBGV.CheckP_UI = "24"
		RAT_ID = self.TK_Rat_ID.get()
		Unit = countStr(RAT_ID)
		if RAT_ID != "":
			self.TKS_Show_Rat_ID.config(text="RatID: {}".format(RAT_ID), fg="black")
		else:
			self.TKS_Show_Rat_ID.config(text="RatID: (not set)", fg="gray35")
		self.Rat_ID = RAT_ID
		self.DBGV.Data_ModelRT_Str = CreateModelRTStr(self.OperaType, self.DisDays[1], self.DisDays[2], self.DiseaseType, self.DisGroupType, self.Rat_ID)
		# print(len(RAT_ID))

	def SetUserName(self): #設定使用者名稱
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
		self.TotalFood = ct #統計食物臂有幾個

		# 將哪幾臂是食物臂顯示在UI視窗上
		if ct == 0:
			self.TK_SHOW_Food.config(text="Food: (not set)", fg="gray35")
		else:
			self.TK_SHOW_Food.config(text="Food: {}".format(hadFood), fg="black")
		# self.TK_SHOW_Food.place(x=750, y=260,anchor="nw")	

	# ============================

	def ConnectClick(self): #"Link"按鈕按下時負責處理的副程式
		if self.CAM_IS_RUN:
			# 關閉攝影機連線
			DBGV.CheckP_UI = "26-1"
			
			# 將UI回歸到未連線狀態
			self.BT_Connect.config(text="Link", bg="DarkOliveGreen2", fg="dark green")
			self.Link_State.config(text="IPCAM Link: Unlinked", fg="gray35")
			# self.CAM_IS_CONN = False
			self.BT_Start.config(bg="gray85", state="disabled")
			self.BT_Camera.config(state="disabled")
			self.BT_Setting.config(state="disabled")
			for i in range(1, self.ARM_UNIT+1):
				self.TKC_Food[i-1].config(state="disabled")
			# 將連線的相關參數回歸到未連線狀態
			self.TCAM.CAM_IS_RUN = False
			self.TCAM.CAM_IS_CONN = False
			self.IPCAM.CAM_IS_RUN = False
			self.IPCAM.FIRST_RUN = True
			self.BT_Camera.config(bg="gray85")
			self.OPEN_CAMERA_WINDOW = False
			self.TCAM.OPEN_CAMERA_WINDOW = self.OPEN_CAMERA_WINDOW
			self.makeBall()
			# 如果設定的視窗有開起來就必須將它關閉
			if self.SETTING_OPEN:
				self.SETTING_OPEN = False
				self.DBGV.Maze_SetState = False
				self.BT_Setting.config(state="disabled")
				self.tkSetting.destroy()
			self.CAM_IS_RUN = False
		else:
			# 開啟攝影機連線
			DBGV.CheckP_UI = "26-2"
			self.BT_Connect.config(text="Unlink", bg="tomato", fg="brown4")
			self.Link_State.config(text="IPCAM Link: Linked",fg="green4")
			self.CAM_IS_RUN = True
			self.BT_Start.config(bg="DarkOliveGreen2", state="normal")
			self.BT_Camera.config(state="normal")
			self.BT_Setting.config(state="normal")
			for i in range(1, self.ARM_UNIT+1):
				self.TKC_Food[i-1].config(state="normal")
			self.TCAM.CAM_IS_RUN = True
			self.IPCAM.CAM_IS_RUN = True

	def MazeStartCheck(self): #按下"start"，實驗開始執行前檢查
		HaveError = False
		if self.MAZE_IS_RUN:
			# 手動結束實驗
			DBGV.CheckP_UI = "27-1"
			self.Maze_State.config(text="Maze State: Preparing...", fg="gray35")
			# self.Maze_State.place(x=750, y=200,anchor="nw")
			self.BT_Start.config(text="Start", bg="DarkOliveGreen2")
			self.MAZE_IS_RUN = False
		else:
			# 檢查實驗參數是否都有選填
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
			# 是否有任何實驗參數沒選填的
			if HaveError:
				tk.messagebox.showwarning(title='Warning!!', message=ErrMsg)
			else:
				# 傳送實驗相關設定(放食物的總數/食物臂/老鼠ID/使用者名稱)
				self.TCAM.TotalFood = self.TotalFood
				self.TCAM.Food = self.Food
				self.TCAM.RatID = self.Rat_ID
				self.TCAM.Rec_UserName = self.Rec_UserName

				# 傳送實驗相關設定(手術前後/Model/Group/時間點)
				self.TCAM.OperaType = self.OperaType
				self.TCAM.DiseaseType = self.DiseaseType
				self.TCAM.DisGroupType = self.DisGroupType
				self.TCAM.DisDays = self.DisDays

				# 更新實驗狀態
				self.Maze_State.config(text="Maze State: Recording...", fg="green4")
				# self.Maze_State.place(x=750, y=200, anchor="nw")
				self.BT_Start.config(text="Stop", bg="IndianRed1")

				# 如果是前期訓練則記錄一下老鼠ID
				self.MAZE_IS_RUN = True
				# if self.EXP_DATA_MODE == "TRAINING":
				# 	self.OldTrain_Rat_ID = self.Rat_ID
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

	def updateData(self): #更新各項顯示資訊(包含LongTerm ShortTerm Latency 進出臂順序)
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

	def LockInput(self, state): #輸入鎖(鎖上可以輸入/勾選/點擊實驗相關的控制項，避免不必要的麻煩)
		if state:
			DBGV.CheckP_UI = "31-1"
			if self.MAZE_IS_RUN:
				self.BT_Connect.config(state="disabled")

			if self.MENU_OPEN:
				self.BT_Start.config(state="disabled")
				self.BT_Connect.config(state="disabled")

			if self.DBGV.Maze_SetState and self.EXP_DATA_MODE != "NONE":
				self.TKS_Btn0_Mode1.config(state="disabled")
				self.TKS_Btn0_Mode2.config(state="disabled")
				self.TKS_Disease.config(state="disabled")
				self.TKS_DisGroup.config(state="disabled")
				self.TK_User_Name.config(state="disabled")
				self.BT_User_Name.config(state="disabled")
				self.TKS_BT_DisConfirm.config(state="disabled")
				self.TKS_BT_DisModify.config(state="disabled")
				self.TK_Rat_ID.config(state="disabled")
				self.BT_Rat_ID.config(state="disabled")
				if self.EXP_DATA_MODE == "EXPERIMENT":
					self.TKS_Btn1_Opera1.config(state="disabled")
					self.TKS_Btn1_Opera2.config(state="disabled")
					self.TKS_OpDay_Month.config(state="disabled")
					self.TKS_OpDay_Day.config(state="disabled")
					self.TKS_DisGroup.config(state="disabled")
					self.TKS_BT_OpDayConfirm.config(state="disabled")
					self.TKS_BT_DisGroupConfirm.config(state="disabled")
					self.TKS_BT_DisGroupModify.config(state="disabled")
					
				
				
			for i in range(0,self.ARM_UNIT):
				self.TKC_Food[i].config(state="disabled")
		else:
			DBGV.CheckP_UI = "31-2"
			self.BT_Connect.config(state="normal")
			self.BT_Start.config(state="normal")

			if self.DBGV.Maze_SetState and self.EXP_DATA_MODE != "NONE":
				self.TKS_Btn0_Mode1.config(state="normal")
				self.TKS_Btn0_Mode2.config(state="normal")
				self.TKS_Disease.config(state="readonly")
				self.TKS_BT_DisConfirm.config(state="normal")
				self.TKS_BT_DisModify.config(state="normal")
				self.TK_User_Name.config(state="normal")
				self.BT_User_Name.config(state="normal")
				self.TK_Rat_ID.config(state="normal")
				self.BT_Rat_ID.config(state="normal")
				if self.EXP_DATA_MODE == "EXPERIMENT":
					self.TKS_Btn1_Opera1.config(state="normal")
					self.TKS_Btn1_Opera2.config(state="normal")
					self.TKS_OpDay_Month.config(state="normal")
					self.TKS_OpDay_Day.config(state="normal")
					self.TKS_BT_OpDayConfirm.config(state="normal")
					if self.DiseaseType != "":
						self.TKS_DisGroup.config(state="readonly")
						self.TKS_BT_DisGroupConfirm.config(state="normal")
						self.TKS_BT_DisGroupModify.config(state="normal")

			for i in range(0,self.ARM_UNIT):
				self.TKC_Food[i].config(state="normal")

	def setIPCAMInfo(self): #設定要匯入IPCAM那隻程式的資訊(當點下Load按鈕時會執行的副程式)
		if(self.InfoCombo.current() != 0):
			DBGV.CheckP_UI = "32-1"
			IPCAM_ID, IPCAM_Name = self.InfoCombo.current()-1, self.InfoCombo.get()

			# 將取得的資訊分別記錄到參數中
			IPCAM_Username = IPCAM_Info[IPCAM_ID][1]
			IPCAM_Password = IPCAM_Info[IPCAM_ID][2]
			IPCAM_IP = IPCAM_Info[IPCAM_ID][3]
			IPCAM_Bar = IPCAM_Info[IPCAM_ID][4]
			IPCAM_NewP1 = [IPCAM_Info[IPCAM_ID][5], IPCAM_Info[IPCAM_ID][6]]
			IPCAM_Port = IPCAM_Info[IPCAM_ID][7]
			IPCAM_RecSize = IPCAM_Info[IPCAM_ID][8]
			self.CAM_INIT_SUCCESS = True

			# 將這些參數傳給IPCAM程式碼參數，使它可以成功連線(RTSP)
			self.IPCAM.IPCAM_Username = IPCAM_Username
			self.IPCAM.IPCAM_Password = IPCAM_Password
			self.IPCAM.IPCAM_IP = IPCAM_IP
			self.IPCAM.IPCAM_Name = IPCAM_Name
			self.IPCAM.IPCAM_Bar = IPCAM_Bar
			self.IPCAM.IPCAM_Port = IPCAM_Port
			self.IPCAM.IPCAM_RecSize = IPCAM_RecSize
			self.IPCAM.IPCAM_NewP1 = [IPCAM_NewP1[0], IPCAM_NewP1[1]]
			self.IPCAM.CAM_INIT_SUCCESS = self.CAM_INIT_SUCCESS

			# 更新UI畫面上的狀態
			DBGV.CheckP_UI = "32-2"
			self.mazeTitle.config(text="IPCAM: {} ({})".format(IPCAM_Name, IPCAM_IP)) #寫上現在連線哪一台裝置
			self.BT_Connect.config(state="normal", bg="DarkOliveGreen2")
			self.BT_LoadCAM.config(state="disabled")
			self.InfoCombo.config(state="disabled")

	def LoopMain(self): #主UI執行後一直跑的迴圈
		try:
			DBGV.CheckP_UI = "11"

			# 攝影機初始化成功(但只能執行一次)
			# 換句話說，如果你要切換攝影機，目前就必須關掉重開系統程式
			if self.CAM_INIT_SUCCESS:
				DBGV.CheckP_UI = "12"
				self.makeBall() #更新中間那個視窗的紅色圓形
				self.CAM_IS_CONN = self.TCAM.CAM_IS_CONN #更新"目前攝影機是否連線成功"
				
				# 如果攝影機現在是 連線狀態 而且是 連線成功 的狀態
				if self.CAM_IS_RUN and self.CAM_IS_CONN:
					# 開啟"實驗開始(start)"按鈕
					if self.MAZE_IS_RUN:
						self.BT_Start.config(bg="IndianRed1")
					else:
						self.BT_Start.config(bg="DarkOliveGreen2")
					self.BT_Start.config(state="normal")
					
					# 第一次執行這個區塊的程式
					# 主要是用來開啟"定時紀錄座標點"的執行緒(我們教授覺得他是Timer就是了)
					if self.CAM_IS_RUN_First:
						# print("CoodiTimer Start")
						self.CAM_IS_RUN_First = False
						
						# 檢查是否這個執行緒還活著
						# 避免重複開啟執行緒
						if not self.CoodiTimer.is_alive():
							self.CoodiTimer.start()
				else:
					if not self.CAM_IS_RUN_First:
						# print("CoodiTimer Cancel")
						self.CAM_IS_RUN_First = True
						# 關閉記錄座標點執行緒，並重建該執行緒
						# 基本上關閉(cancel)該執行緒就不能再重複開啟(start)，必須在新建一次執行緒
						self.CoodiTimer.cancel()
						self.CoodiTimer = Timer1(0.046, self.TCAM.saveCoodinate2Arr)
						self.CoodiTimer.setDaemon(True) #將Thread設定為daemon thread(一種在背景執行的thread，具有和main thread一同終止的特性)
					# 鎖住"實驗開始(start)"按鈕
					self.BT_Start.config(bg="gray85")
					self.BT_Start.config(state="disabled")
				# print(self.CoodiTimer.is_alive())

				# 判斷是否實驗開始
				if self.MAZE_IS_RUN:
					DBGV.CheckP_UI = "13-1"

					# 是不是第一次執行該區域。看起來好像沒用，但好像攸關其他地方的樣子
					# 如果你後來發現他真的沒用，那就麻煩你幫我把下面這兩行註解調或是刪了吧XD
					if self.firstMazeRun:
						self.firstMazeRun = False

					self.LockInput(True) #開啟輸入鎖(避免亂按@@)
					DBGV.CheckP_UI = "13-2"
					newMazeStatus = self.TCAM.MAZE_IS_RUN #看看實驗是否結束了
					self.updateData() #更新實驗數據在主UI上
					DBGV.CheckP_UI = "13-3"

					# 實驗是否結束(老鼠是否把全部時務臂都走過了)
					if newMazeStatus == False:
						self.Maze_State.config(text="Maze State: Preparing...", fg="gray35")
						# self.Maze_State.place(x=750, y=200,anchor="nw")
						self.BT_Start.config(text="Start", bg="DarkOliveGreen2")
						self.MAZE_IS_RUN = False
						self.Maze_StartState = False
				else:
					# 實驗還沒開始
					DBGV.CheckP_UI = "14"
					
					# 實驗還沒開始但攝影機已經連上了
					if self.CAM_IS_CONN:
						self.LockInput(False)
						# 如果是前期訓練而且老鼠ID與舊的相同(前期訓練老鼠ID編號用)
						# 目的是當前期訓練老鼠實驗正式結束時，會在重新取的新的老鼠ID
						# if (self.EXP_DATA_MODE == "TRAINING") and (self.OldTrain_Rat_ID == self.Rat_ID):
						# 	self.Rat_ID = datetime.datetime.now().strftime("T%H%M%S") #老鼠ID是"T開頭+二位數時分秒"的結構
						# 	self.TKS_Show_Rat_ID.config(text="RatID: %s" %(self.Rat_ID), fg="black")
					else:
						# 還沒連上就將輸入相關的控制項鎖住
						self.LockInput(True)

					# 開啟"修改下拉式選單模式"時會鎖定輸入
					if self.MENU_OPEN:
						self.LockInput(True)
					else:
						self.LockInput(False)
						
					self.firstMazeRun = True
					
				# 更新攝影機連線狀態於UI畫面上
				if self.CAM_IS_CONN:
					self.Cam_State.config(text="Camera State: Connecting...", fg="green4")
					# self.Cam_State.place(x=750, y=170, anchor="nw")
					self.BT_Camera.config(state="normal")
				else:
					self.Cam_State.config(text="Camera State: Unconnect", fg="gray35")
					# self.Cam_State.place(x=750, y=170, anchor="nw")
					self.BT_Camera.config(state="disabled")

				# 更新系統狀態(這個狀態列主要是顯示攝影機的連線狀態)
				DBGV.CheckP_UI = "15"
				IPCAM_MsgColor = self.IPCAM.IPCAM_MsgColor
				IPCAM_Messenage = self.IPCAM.IPCAM_Messenage
				self.TK_SHOW_SYS_Msg.set("Messenage: {}".format(IPCAM_Messenage))
				
				# 將系統狀態文字上色(綠色：成功/ 藍色：警告/ 紅色：錯誤)
				if(IPCAM_MsgColor == 0):
					self.TK_SHOW_SYS_Msg_Text.config(fg="green4")
				elif(IPCAM_MsgColor == 1):
					self.TK_SHOW_SYS_Msg_Text.config(fg="blue2")
				elif(IPCAM_MsgColor == 2):
					self.TK_SHOW_SYS_Msg_Text.config(fg="red2")
				
				# 更新三按鈕的狀態到DBGV(錄影畫面的狀態區域)
				self.DBGV.Maze_StartState = self.MAZE_IS_RUN
				self.DBGV.Maze_LinkState = self.CAM_IS_RUN
				self.DBGV.Maze_CameraState = self.OPEN_CAMERA_WINDOW
				DBGV.CheckP_UI = "16"

				if self.SETTING_OPEN:
					self.tkSetting_CheckFillNull()

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
		if self.CAM_IS_RUN_First:
			self.CAM_IS_RUN_First = True
			self.CoodiTimer.cancel()

	def ClearSettingMenuList(self): #清除"修改下拉式選單項目"該區域設定
		for i in range(len(self.MENU_Modify_Item)):
			self.SettingMenuNo[i].config(bg="gray85", state="disabled")
			self.SettingMenuList[i].delete(0, "end")
			self.SettingMenuList[i].insert(0, "")
			self.SettingMenuList[i].config(state="disabled")
			self.SettingMenuNew[i].config(bg="gray85", state="disabled")
			self.SettingMenuDel[i].config(bg="gray85", state="disabled")
			self.SettingMenuUp[i].config(bg="gray85", state="disabled")
			self.SettingMenuDown[i].config(bg="gray85", state="disabled")

	def updateSettingMenuList(self): #更新"修改下拉式選單項目"該區域設定
		# 清除
		self.ClearSettingMenuList()

		# 重新
		for i in range(len(self.MENU_Modify_Item)):
			if self.MENU_Modify_Item[i] == "":
				if i == 0:
					self.SettingMenuNo[0].config(bg="DarkOliveGreen3" ,state="normal")
					self.SettingMenuList[0].config(state="normal")
					self.SettingMenuList[0].delete(0, "end")
					self.SettingMenuList[0].insert(0, "")
					self.SettingMenuNew[0].config(bg="DarkOliveGreen2", state="normal")
				break
			self.SettingMenuNo[i].config(bg="gray65" ,state="normal")
			self.SettingMenuList[i].config(state="normal")
			self.SettingMenuList[i].delete(0, "end")
			self.SettingMenuList[i].insert(0, self.MENU_Modify_Item[i])
			self.SettingMenuDel[i].config(bg="tomato", state="normal")
			if i > 0:
				self.SettingMenuUp[i].config(bg="gray65", state="normal")
			if (i < len(self.MENU_Modify_Item)-1):
				if (self.MENU_Modify_Item[i+1] != ""):
					self.SettingMenuDown[i].config(bg="gray65", state="normal")
				else:
					self.SettingMenuNo[i+1].config(bg="DarkOliveGreen3" ,state="normal")
					self.SettingMenuList[i+1].config(state="normal")
					self.SettingMenuList[i+1].delete(0, "end")
					self.SettingMenuList[i+1].insert(0, "")
					self.SettingMenuNew[i+1].config(bg="DarkOliveGreen2", state="normal")

	def SettingMenuModify(self, type_): #"修改下拉式選單項目"並初始化該區域設定
		self.MENU_OPEN = True
		self.SettingMenuFinish.config(state="normal")
		nowItem = 0
		if type_ == "Model":
			self.SettingMenuType.config(text="Model")
			self.MENU_INFO = ["Model", ""]
			nowItem = len(self.DiseaseCombo)
			for i in range(1, nowItem):
				self.MENU_Modify_Item[i-1] = self.DiseaseCombo[i]
		elif type_ == "Group":
			self.SettingMenuType.config(text="Group (%s)" %(self.DiseaseType))
			self.MENU_INFO = ["Group", self.DiseaseType]
			nowItem = len(self.DisGroupCombo)
			for i in range(1, nowItem):
				self.MENU_Modify_Item[i-1] = self.DisGroupCombo[i]
		self.updateSettingMenuList()
		
	# ==============================
	# ===== 設定視窗頁面設定參數 =====
	# ==============================

	def tkSetting_CheckFillNull(self):
		SetFillList = ["User", "Model", "Group", "Operation", "TimePoint", "Rat ID"]
		SetFillData = [self.Rec_UserName, self.DiseaseType, self.DisGroupType, self.OperaType, [self.DisDays[1], self.DisDays[2]],  self.Rat_ID]

		for i in range(6):
			isNull = False
			if SetFillList[i] == "TimePoint":
				if SetFillData[i][0] == -1 or SetFillData[i][1] == -1:
					isNull = True
			else:
				if SetFillData[i] == "":
					isNull = True
			if isNull:
				self.Show_SetFill[i].config(text="%s 未填寫!" %(SetFillList[i]), fg="red2")
			else:
				self.Show_SetFill[i].config(text="%s 已填寫!" %(SetFillList[i]), fg="green4")


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
		self.CSV_DiseaseFile = LoadDiseaseFile()
		DBGV.CheckP_UI = "33-4"
		if ListType == "Model":
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

		if self.EXP_DATA_MODE == "EXPERIMENT":
			self.DisGroupCombo = ['請選擇...']
			self.TKS_DisGroup.current(0)
			self.DisGroupType = ""
		if self.TKS_Disease.current() != 0:
			self.DiseaseType = self.TKS_Disease.get()
			self.TKS_Show_Disease.config(text="Model: %s%s" %(self.DiseaseType,newSpace), fg="black")
			if self.EXP_DATA_MODE == "EXPERIMENT":
				self.TKS_BT_DisGroupModify.config(state="normal")
				self.TKS_BT_DisGroupConfirm.config(state="normal")
				combo_idx, mod_idx = findDiseaseArray(self.CSV_DiseaseFile, self.DiseaseType)
				if combo_idx > 0:
					for row in self.CSV_DiseaseFile[combo_idx-1][2]:
						self.DisGroupCombo.append(row[1])
				self.TKS_DisGroup.config(state="readonly", values=self.DisGroupCombo)
		else:
			if self.EXP_DATA_MODE == "EXPERIMENT":
				self.TKS_BT_DisGroupModify.config(state="disabled")
				self.TKS_BT_DisGroupConfirm.config(state="disabled")
				self.TKS_DisGroup.config(state="disabled", values=self.DisGroupCombo)
				self.TKS_DisGroup.current(0)
				self.DisGroupType = ""
				self.TKS_Show_DisGroup.config(text="Group: (not set)%s" %(newSpace), fg="gray35")
			self.TKS_Disease.current(0)
			self.DiseaseType = ""
			self.TKS_Show_Disease.config(text="Model: (not set)%s" %(newSpace), fg="gray35")
		self.DBGV.Data_ModelRT_Str = CreateModelRTStr(self.OperaType, self.DisDays[1], self.DisDays[2], self.DiseaseType, self.DisGroupType, self.Rat_ID)

	def tkSetting_DisGroupConfirm(self): #設定UI視窗點擊[確認疾病組別]按鈕後處理副程式
		DBGV.CheckP_UI = "36"
		self.DBGV.Data_SettingClick[2] = self.DBGV.Data_SettingClick[2] + 1
		newSpace = ""
		for i in range(15):
			newSpace = newSpace + " "
		if self.TKS_DisGroup.current() != 0:
			self.DisGroupType = self.TKS_DisGroup.get()
			self.TKS_Show_DisGroup.config(text="Group: %s%s" %(self.DisGroupType,newSpace), fg="black")
		else:
			self.TKS_DisGroup.current(0)
			self.DisGroupType = ""
			self.TKS_Show_DisGroup.config(text="Group: (not set)%s" %(newSpace), fg="gray35")
		self.DBGV.Data_ModelRT_Str = CreateModelRTStr(self.OperaType, self.DisDays[1], self.DisDays[2], self.DiseaseType, self.DisGroupType, self.Rat_ID)
	
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

		# 解除項目編輯鎖定狀態
		self.MENU_OPEN = False
		for i in range(len(self.MENU_Modify_Item)):
			self.MENU_Modify_Item[i] = ""
		self.ClearSettingMenuList()
		self.SettingMenuFinish.config(state="disabled")

		self.tkSetting.destroy()

	def tkSetting_Menu_Finish(self): #下拉式選單編輯完成
		self.MENU_OPEN = False
		self.SettingMenuFinish.config(state="disabled")
		self.SettingMenuType.config(text="")

		# print(self.CSV_DiseaseFile)
		# print(self.MENU_Modify_Item)
		# print(self.MENU_INFO)

		# 修改下拉式選單項目時只會更動"self.MENU_Modify_Item"的陣列
		# 更新"self.MENU_Modify_Item"的陣列
		if self.MENU_INFO[0] == "Model":
			# 要儲存Model項目

			# 更換順序以及新增
			for i in range(len(self.MENU_Modify_Item)):
				if self.MENU_Modify_Item[i] == "":
					break
				self.MENU_Modify_Item[i] = self.SettingMenuList[i].get()
				combo_idx, mod_idx = findDiseaseArray(self.CSV_DiseaseFile, self.MENU_Modify_Item[i])
				# print(self.MENU_Modify_Item[i], combo_idx, mod_idx, i)
				if combo_idx == 0 and  mod_idx == -1:
					self.CSV_DiseaseFile.append([i+1, self.MENU_Modify_Item[i], []])
				else:
					self.CSV_DiseaseFile[combo_idx-1][0] = i+1
			self.CSV_DiseaseFile.sort()
			# 檢查不在名單上的項目
			findArr = []
			for i in range(len(self.CSV_DiseaseFile)):
				try:
					idx = self.MENU_Modify_Item.index(self.CSV_DiseaseFile[i][1])
				except:
					idx = -1
				findArr.append(idx)
			# 刪除不在名單上的項目
			for i in range(len(findArr)):
				if i >= len(findArr):
					break
				if findArr[i] == -1:
					self.CSV_DiseaseFile.pop(i)
					findArr.pop(i)
					if i == len(findArr)-1:
						if findArr[i] == -1:
							self.CSV_DiseaseFile[combo_idx-1][2].pop(i)
							findArr.pop(i)
			self.CSV_DiseaseFile.sort()

		elif self.MENU_INFO[0] == "Group":
			# 要儲存Group項目

			# 先找出是哪個Model的Group => 找出在陣列ID(combo_idx)以及該項目編號(mod_idx)
			combo_idx, mod_idx = findDiseaseArray(self.CSV_DiseaseFile, self.MENU_INFO[1])

			# 更換順序以及新增
			# print(self.MENU_Modify_Item)
			# print(self.CSV_DiseaseFile[combo_idx-1][2])
			for i in range(len(self.MENU_Modify_Item)):
				if self.MENU_Modify_Item[i] == "":
					break
				self.MENU_Modify_Item[i] = self.SettingMenuList[i].get()
				gp_combo_idx, gp_idx = findDiseaseArray(self.CSV_DiseaseFile[combo_idx-1][2], self.MENU_Modify_Item[i])
				if gp_combo_idx == 0 and  gp_idx == -1:
					self.CSV_DiseaseFile[combo_idx-1][2].append([i+1, self.MENU_Modify_Item[i]])
				else:
					self.CSV_DiseaseFile[combo_idx-1][2][gp_combo_idx-1][0] = i+1
			self.CSV_DiseaseFile[combo_idx-1][2].sort()
			# print(self.CSV_DiseaseFile[combo_idx-1][2])
			# 檢查不在名單上的項目
			findArr = []
			for i in range(len(self.CSV_DiseaseFile[combo_idx-1][2])):
				try:
					idx = self.MENU_Modify_Item.index(self.CSV_DiseaseFile[combo_idx-1][2][i][1])
				except:
					idx = -1
				findArr.append(idx)
			# 刪除不在名單上的項目
			for i in range(len(findArr)):
				if i >= len(findArr):
					break
				if findArr[i] == -1:
					self.CSV_DiseaseFile[combo_idx-1][2].pop(i)
					findArr.pop(i)
					if i == len(findArr)-1:
						if findArr[i] == -1:
							self.CSV_DiseaseFile[combo_idx-1][2].pop(i)
							findArr.pop(i)
			self.CSV_DiseaseFile[combo_idx-1][2].sort()
		# print(self.CSV_DiseaseFile)

		# 更新完"self.MENU_Modify_Item"的陣列，即可寫入檔案後並重讀陣列(self.CSV_DiseaseFile)
		WriteDiseaseFile(self.CSV_DiseaseFile)
		self.CSV_DiseaseFile = LoadDiseaseFile()

		# Model下拉是選單重置
		self.DiseaseCombo = ['請選擇...']
		for row in self.CSV_DiseaseFile:
			self.DiseaseCombo.append(row[1])
		self.TKS_Disease.config(values=self.DiseaseCombo)
		self.TKS_Disease.current(0)
		self.DiseaseType = ""
		self.TKS_Show_Disease.config(text="Model: (not set)          ", fg="gray35")
		# Group下拉式選單重置
		self.DisGroupCombo = ['請選擇...']
		self.TKS_BT_DisGroupModify.config(state="disabled")
		self.TKS_BT_DisGroupConfirm.config(state="disabled")
		self.TKS_DisGroup.config(state="disabled", values=self.DisGroupCombo)
		self.TKS_DisGroup.current(0)
		if self.EXP_DATA_MODE == "EXPERIMENT":
			self.DisGroupType = ""
			self.TKS_Show_DisGroup.config(text="Group: (not set)          ", fg="gray35")
		elif self.EXP_DATA_MODE == "TRAINING":
			self.DisGroupType = "Training"
			self.TKS_Show_DisGroup.config(text="Group: Training          ", fg="black")

		# 清除放置[修改下拉式選單項目]的陣列以及輸入框
		for i in range(len(self.MENU_Modify_Item)):
			self.MENU_Modify_Item[i] = ""
		self.ClearSettingMenuList()

	def tkSetting_Menu_ItemUpDown(self, up_down, mid): #修改下拉式選單項目按下[向上/向下]後會執行的程式
		buff = self.MENU_Modify_Item[mid]
		if up_down == "Up":
			self.MENU_Modify_Item[mid] = self.MENU_Modify_Item[mid-1]
			self.MENU_Modify_Item[mid-1] = buff
		elif up_down == "Down":
			self.MENU_Modify_Item[mid] = self.MENU_Modify_Item[mid+1]
			self.MENU_Modify_Item[mid+1] = buff
		self.updateSettingMenuList()

	def tkSetting_Menu_ItemNewDel(self, new_del, mid): #修改下拉式選單項目按下[新增/刪除]後會執行的程式
		if new_del == "New":
			self.MENU_Modify_Item[mid] = self.SettingMenuList[mid].get()
		elif new_del == "Delete":
			flag = mid
			while flag < len(self.MENU_Modify_Item):
				if flag == len(self.MENU_Modify_Item)-1:
					self.MENU_Modify_Item[flag] = ""
				else:
					self.MENU_Modify_Item[flag] = self.MENU_Modify_Item[flag+1]
				flag = flag + 1
		self.updateSettingMenuList()

	def tkSetting_SetupUI(self): #設定UI視窗主要程式
		global Disease_List
		DBGV.CheckP_UI = "18"
		try:
			self.DBGV.Maze_SetState = True

			self.CSV_DiseaseFile = LoadDiseaseFile()
			# WriteDiseaseFile(self.CSV_DiseaseFile)

			self.SETTING_OPEN = True
			settingSize = (800, self.WinSize[1])
			self.tkSetting = tk.Tk()
			self.tkSetting.title('追蹤紀錄軌跡系統平台 - 實驗參數設定') #窗口名字
			self.tkSetting.geometry('%dx%d+120+120' %(settingSize[0],settingSize[1])) #窗口大小(寬X高+X偏移量+Y偏移量)
			self.tkSetting.resizable(False, False) #禁止變更視窗大小

			self.TKS_RadValue = tk.IntVar()

			SettingShowX = 10
			tk.Label(self.tkSetting, text="Model Configuration", font=('Arial', 14), bg="gray75").place(x=SettingShowX+140, y=20, anchor="n")

			# 選擇訓練中還是行為測試
			SettingShowY = 60
			self.TKS_title1_0 = tk.Label(self.tkSetting, text="Step1. 請選擇使用目的", font=('微軟正黑體', 12, "bold"), bg="gray75")
			self.TKS_title1_0.place(x=SettingShowX+140, y=SettingShowY, anchor="n")
			if self.EXP_DATA_MODE == "TRAINING":
				self.TKS_Btn0_Mode1 = tk.Button(self.tkSetting, text='前期訓練', width=10, font=('微軟正黑體', 14, "bold"), bg="DarkOliveGreen2", command=lambda: self.SystemModeSet('TRAINING'))
			else:
				self.TKS_Btn0_Mode1 = tk.Button(self.tkSetting, text='前期訓練', width=10, font=('微軟正黑體', 14, "bold"), bg="gray90", command=lambda: self.SystemModeSet('TRAINING'))
			self.TKS_Btn0_Mode1.place(x=SettingShowX + 10, y=SettingShowY + 30, anchor="nw")

			if self.EXP_DATA_MODE == "EXPERIMENT":
				self.TKS_Btn0_Mode2 = tk.Button(self.tkSetting, text='正式測試', width=10, font=('微軟正黑體', 14, "bold"), bg="DarkOliveGreen2", command=lambda: self.SystemModeSet('EXPERIMENT'))
			else:
				self.TKS_Btn0_Mode2 = tk.Button(self.tkSetting, text='正式測試', width=10, font=('微軟正黑體', 14, "bold"), bg="gray90", command=lambda: self.SystemModeSet('EXPERIMENT'))
			self.TKS_Btn0_Mode2.place(x=SettingShowX + 145, y=SettingShowY + 30, anchor="nw")

			if self.EXP_DATA_MODE != "NONE":
				self.TKS_Btn0_Mode1.config(state="disabled")
				self.TKS_Btn0_Mode2.config(state="disabled")
				self.TKS_title1_0.config(fg="gray35", bg="gray85")

			SettingShowY = 150
			self.TKS_title1_1 = tk.Label(self.tkSetting, text="Step2. 請輸入以下資訊", font=('微軟正黑體', 12, "bold"))
			self.TKS_title1_1.place(x=SettingShowX+140,y=SettingShowY,anchor="n")
			if self.EXP_DATA_MODE == "NONE":
				self.TKS_title1_1.config(fg="gray35", bg="gray85")
			else:
				self.TKS_title1_1.config(fg="black", bg="gray75")
			# 設定使用者名稱
			SettingShowY = 190
			tk.Label(self.tkSetting,text="User", font=('Arial', 12), bg="gray75").place(x=SettingShowX, y=SettingShowY,anchor="nw")
			self.TK_User_Name = tk.Entry(self.tkSetting, font=('Arial', 12), width=12)
			self.TK_User_Name.place(x=SettingShowX+56,y=SettingShowY+1,anchor="nw")
			if self.Rec_UserName != "":
				self.TK_User_Name.delete(0, "end")
				self.TK_User_Name.insert(0, self.Rec_UserName)
			self.BT_User_Name = tk.Button(self.tkSetting, text='Set User', width=9, font=('Arial', 10), bg="gray90", command=self.SetUserName)
			self.BT_User_Name.place(x=SettingShowX+172,y=SettingShowY-3,anchor="nw")
			if self.EXP_DATA_MODE == "NONE":
				self.TK_User_Name.config(state="disabled")
				self.BT_User_Name.config(state="disabled")

			#疾病模組資訊
			SettingShowY = 230
			self.DiseaseCombo = ['請選擇...']
			for row in self.CSV_DiseaseFile:
				self.DiseaseCombo.append(row[1])
			self.TKS_title3 = tk.Label(self.tkSetting, text="Model", font=('Arial', 12), bg="gray75")
			self.TKS_title3.place(x=SettingShowX,y=SettingShowY,anchor="nw")
			self.TKS_Disease = ttk.Combobox(self.tkSetting, values=self.DiseaseCombo, font=('Arial', 11), width=10, state="readonly")
			self.TKS_Disease.place(x=SettingShowX+56,y=SettingShowY+1,anchor="nw")
			if self.DiseaseType != "":
				combo_idx, mod_idx = findDiseaseArray(self.CSV_DiseaseFile, self.DiseaseType)
				self.TKS_Disease.current(combo_idx)
			else:
				self.TKS_Disease.current(0)
			self.TKS_BT_DisConfirm = tk.Button(self.tkSetting, text='Set', width=6, font=('Arial', 10), bg="gray90", command=self.tkSetting_DiseaseConfirm)
			self.TKS_BT_DisConfirm.place(x=SettingShowX+172,y=SettingShowY-3,anchor="nw")
			self.TKS_BT_DisModify = tk.Button(self.tkSetting, text='Modify', width=6, font=('Arial', 10), bg="gray90", command=lambda: self.SettingMenuModify('Model'))
			self.TKS_BT_DisModify.place(x=SettingShowX+232,y=SettingShowY-3,anchor="nw")
			if self.EXP_DATA_MODE == "NONE":
				self.TKS_Disease.config(state="disabled")
				self.TKS_BT_DisConfirm.config(state="disabled")
				self.TKS_BT_DisModify.config(state="disabled")

			#復健分組資訊
			SettingShowY = 270
			self.DisGroupCombo = ['請選擇...']
			combo_idx = 0
			if self.DiseaseType != "":
				combo_idx, mod_idx = findDiseaseArray(self.CSV_DiseaseFile, self.DiseaseType)
				if combo_idx > 0:
					for row in self.CSV_DiseaseFile[combo_idx-1][2]:
						self.DisGroupCombo.append(row[1])
			# print(self.DisGroupCombo)

			self.TKS_title3 = tk.Label(self.tkSetting, text="Group", font=('Arial', 12), bg="gray75")
			self.TKS_title3.place(x=SettingShowX,y=SettingShowY,anchor="nw")
			self.TKS_DisGroup = ttk.Combobox(self.tkSetting, values=self.DisGroupCombo, font=('Arial', 11), width=10, state="disabled")
			self.TKS_DisGroup.place(x=SettingShowX+56,y=SettingShowY+1,anchor="nw")
			if self.DisGroupType != "":
				gp_combo_idx, gp_idx = findDiseaseArray(self.CSV_DiseaseFile[combo_idx-1][2], self.DisGroupType)
				self.TKS_DisGroup.current(gp_combo_idx)
			else:
				self.TKS_DisGroup.current(0)
			self.TKS_BT_DisGroupConfirm = tk.Button(self.tkSetting, text='Set', width=6, font=('Arial', 10), bg="gray90", command=self.tkSetting_DisGroupConfirm)
			self.TKS_BT_DisGroupConfirm.place(x=SettingShowX+172,y=SettingShowY-3,anchor="nw")
			self.TKS_BT_DisGroupModify = tk.Button(self.tkSetting, text='Modify', width=6, font=('Arial', 10), bg="gray90", command=lambda: self.SettingMenuModify('Group'))
			self.TKS_BT_DisGroupModify.place(x=SettingShowX+232,y=SettingShowY-3,anchor="nw")
			if (self.EXP_DATA_MODE == "NONE") or (self.EXP_DATA_MODE == "TRAINING"):
				self.TKS_DisGroup.config(state="disabled")
				self.TKS_BT_DisGroupConfirm.config(state="disabled")
				self.TKS_BT_DisGroupModify.config(state="disabled")
			if (self.EXP_DATA_MODE == "EXPERIMENT") and self.DiseaseType != "":
				self.TKS_DisGroup.config(state="readonly")
			else: 
				self.TKS_DisGroup.config(state="disabled")

			# 選擇狀態是手術前後
			SettingShowY = 310
			self.TKS_title1 = tk.Label(self.tkSetting, text="Operation", font=('Arial', 12), bg="gray75")
			self.TKS_title1.place(x=SettingShowX,y=SettingShowY+6,anchor="nw")
			if self.OperaType == 'pre':
				self.TKS_Btn1_Opera1 = tk.Button(self.tkSetting, text='pre-Op\n(手術前)', width=10, font=('Arial', 10), bg="DarkOliveGreen2", command=lambda: self.tkSetting_BtnOpera('pre-Op'))
			else:
				self.TKS_Btn1_Opera1 = tk.Button(self.tkSetting, text='pre-Op\n(手術前)', width=10, font=('Arial', 10), bg="gray90", command=lambda: self.tkSetting_BtnOpera('pre-Op'))
			self.TKS_Btn1_Opera1.place(x=SettingShowX + 80, y=SettingShowY - 5, anchor="nw")
			if self.OperaType == 'past':
				self.TKS_Btn1_Opera2 = tk.Button(self.tkSetting, text='past-Op\n(手術後)', width=10, font=('Arial', 10), bg="DarkOliveGreen2", command=lambda: self.tkSetting_BtnOpera('past-Op'))
			else:
				self.TKS_Btn1_Opera2 = tk.Button(self.tkSetting, text='past-Op\n(手術後)', width=10, font=('Arial', 10), bg="gray90", command=lambda: self.tkSetting_BtnOpera('past-Op'))
			self.TKS_Btn1_Opera2.place(x=SettingShowX + 175, y=SettingShowY - 5, anchor="nw")
			if (self.EXP_DATA_MODE == "NONE") or (self.EXP_DATA_MODE == "TRAINING"):
				self.TKS_Btn1_Opera1.config(state="disabled")
				self.TKS_Btn1_Opera2.config(state="disabled")

			# 設定天數
			SettingShowY = 350
			self.TKS_title2 = tk.Label(self.tkSetting, text="TimePoint", font=('Arial', 12), bg="gray75")
			self.TKS_title2.place(x=SettingShowX,y=SettingShowY+16,anchor="nw")
			self.TKS_OpDay_Month = tk.Entry(self.tkSetting, font=('Arial', 12), width=6, justify="right")
			self.TKS_OpDay_Month.place(x=SettingShowX+82,y=SettingShowY+7,anchor="nw")
			tk.Label(self.tkSetting, text="Month", font=('Arial', 10)).place(x=SettingShowX+140,y=SettingShowY+7,anchor="nw")
			self.TKS_OpDay_Day = tk.Entry(self.tkSetting, font=('Arial', 12), width=6, justify="right")
			self.TKS_OpDay_Day.place(x=SettingShowX+82,y=SettingShowY+35,anchor="nw")
			tk.Label(self.tkSetting, text="Day", font=('Arial', 10)).place(x=SettingShowX+140,y=SettingShowY+35,anchor="nw")
			if self.DisDays[1] != -1:
				self.TKS_OpDay_Month.delete(0, "end")
				self.TKS_OpDay_Month.insert(0, self.DisDays[1])
			if self.DisDays[2] != -1:
				self.TKS_OpDay_Day.delete(0, "end")
				self.TKS_OpDay_Day.insert(0, self.DisDays[2])
			self.TKS_BT_OpDayConfirm = tk.Button(self.tkSetting, text='Confirm', width=9, font=('Arial', 10), bg="gray90", command=self.tkSetting_OperaDays)
			self.TKS_BT_OpDayConfirm.place(x=SettingShowX+180,y=SettingShowY+15,anchor="nw")
			if (self.EXP_DATA_MODE == "NONE") or (self.EXP_DATA_MODE == "TRAINING"):
				self.TKS_OpDay_Month.config(state="disabled")
				self.TKS_OpDay_Day.config(state="disabled")
				self.TKS_BT_OpDayConfirm.config(state="disabled")

			# 設定老鼠編號
			SettingShowY = 390
			tk.Label(self.tkSetting,text="Rat ID", font=('Arial', 12), bg="gray75").place(x=SettingShowX,y=SettingShowY+25,anchor="nw")
			self.TK_Rat_ID = tk.Entry(self.tkSetting, font=('Arial', 12), width=14)
			self.TK_Rat_ID.place(x=SettingShowX+60,y=SettingShowY+27,anchor="nw")
			if self.Rat_ID != "":
				self.TK_Rat_ID.delete(0, "end")
				self.TK_Rat_ID.insert(0, self.Rat_ID)
			self.BT_Rat_ID = tk.Button(self.tkSetting, text='Set ID', width=7, font=('Arial', 10), bg="gray90", command=self.SetRatID)
			self.BT_Rat_ID.place(x=SettingShowX+200,y=SettingShowY+22,anchor="nw")
			if (self.EXP_DATA_MODE == "NONE"):
				self.TK_Rat_ID.config(state="disabled")
				self.BT_Rat_ID.config(state="disabled")
			
			# 修改下拉式選單處
			MenuX = 320
			MenuY = 20
			MenuItemRange = 35
			tk.Label(self.tkSetting,text="Modify Drop-down Menu List", font=('Arial', 13), bg="gray75").place(x=MenuX,y=MenuY,anchor="nw")
			
			tk.Label(self.tkSetting,text="Type:", font=('Arial', 12)).place(x=MenuX,y=MenuY+30,anchor="nw")
			self.SettingMenuType = tk.Label(self.tkSetting,text="", font=('Arial', 13, 'bold'))
			self.SettingMenuType.place(x=MenuX+40,y=MenuY+30,anchor="nw")

			MenuItemY = MenuY + 60
			self.SettingMenuNo = []
			self.SettingMenuList = []
			self.SettingMenuNew = []
			self.SettingMenuDel = []
			self.SettingMenuUp = []
			self.SettingMenuDown = []
			for i in range(10):
				self.SettingMenuNo.append("")
				self.SettingMenuList.append("")
				self.SettingMenuNew.append("")
				self.SettingMenuDel.append("")
				self.SettingMenuUp.append("")
				self.SettingMenuDown.append("")

				self.SettingMenuNo[i] = tk.Label(self.tkSetting,text="%02d" %(i+1), font=('Arial', 13), bg="gray85", state="disabled")
				self.SettingMenuNo[i].place(x=MenuX,y=MenuItemY + MenuItemRange*i,anchor="nw")
				self.SettingMenuList[i] = tk.Entry(self.tkSetting, font=('Arial', 13), width=20, state="disabled")
				self.SettingMenuList[i].place(x=MenuX+30,y=MenuItemY + MenuItemRange*i,anchor="nw")
				self.SettingMenuNew[i] = tk.Button(self.tkSetting, text='New', width=5, font=('Arial', 10), command=partial(self.tkSetting_Menu_ItemNewDel, 'New', i), state="disabled", bg="gray85")
				self.SettingMenuNew[i].place(x=MenuX+220,y=MenuItemY - 2 + MenuItemRange*i,anchor="nw")
				self.SettingMenuDel[i] = tk.Button(self.tkSetting, text='Delete', width=5, font=('Arial', 10), command=partial(self.tkSetting_Menu_ItemNewDel, 'Delete', i), state="disabled", bg="gray85")
				self.SettingMenuDel[i].place(x=MenuX+275,y=MenuItemY - 2 + MenuItemRange*i,anchor="nw")
				self.SettingMenuUp[i] = tk.Button(self.tkSetting, text='▲', font=('Arial', 10), bg="gray85", command=partial(self.tkSetting_Menu_ItemUpDown, 'Up', i), state="disabled")
				self.SettingMenuUp[i].place(x=MenuX+330,y=MenuItemY - 2 + MenuItemRange*i ,anchor="nw")
				self.SettingMenuDown[i] = tk.Button(self.tkSetting, text='▼', font=('Arial', 10), bg="gray85", command=partial(self.tkSetting_Menu_ItemUpDown, 'Down', i), state="disabled")
				self.SettingMenuDown[i].place(x=MenuX+360,y=MenuItemY - 2 + MenuItemRange*i,anchor="nw")
			self.SettingMenuFinish = tk.Button(self.tkSetting, text='Finish', font=('Arial', 12), bg="gray85", command=self.tkSetting_Menu_Finish, state="disabled")
			self.SettingMenuFinish.place(x=MenuX,y=MenuItemY - 2 + MenuItemRange*10,anchor="nw")

			# 下拉式選單註解處
			MenuCommandX = 380
			MenuCommandY = 430
			MenuCommandRange = 22
			CommandLine = [
			"1.若有修改Model名稱，則該Model下的Group項目將會全數刪除。",
			"   需重新新增原Model下的Group項目。", 
			"2.當更動任何Model和Group的下拉式選項時，在按下[Finish]存檔",
			"   時，需重新選擇Model以及Group項目。"]
			tk.Label(self.tkSetting,text="●注意事項：", font=('Arial', 11, 'bold')).place(x=MenuCommandX,y=MenuCommandY,anchor="nw")
			for i in range(len(CommandLine)):
				tk.Label(self.tkSetting,text=CommandLine[i], font=('Arial', 10)).place(x=MenuCommandX, y=MenuCommandY + (22 + MenuCommandRange*i),anchor="nw")

			# 設定頁面填寫檢查
			FillCheck = [10, 450]
			LabelSet = [150, 22]
			self.Show_SetFill = ["", "", "", "", "", ""]
			tk.Label(self.tkSetting, text="●目前設定參數輸入狀態：", font=('Arial', 11)).place(x=FillCheck[0],y=FillCheck[1],anchor="nw")
			for i in range(6):
				nowX = FillCheck[0] + LabelSet[0]*int(i/3)
				nowY = 20 + FillCheck[1] + LabelSet[1]*int(i%3)
				self.Show_SetFill[i] = tk.Label(self.tkSetting,text="", font=('Arial', 11))
				self.Show_SetFill[i].place(x=nowX,y=nowY,anchor="nw")

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
	
	# ============================

	def CleanExpSettingData(self):
		self.Rec_UserName = ""
		self.DisGroupType = ""
		self.DiseaseType = ""
		self.DisDays = [False, -1, -1]
		self.OperaType = ""
		self.Rat_ID = ""

		self.TK_User_Name.delete(0, "end")
		self.TK_User_Name.insert(0, self.Rec_UserName)
		self.TKS_Disease.current(0)
		self.DisGroupCombo = ['請選擇...']
		self.TKS_DisGroup.config(state="disabled", values=self.DisGroupCombo)
		self.TKS_DisGroup.current(0)
		self.TKS_Btn1_Opera1.config(bg="gray90")
		self.TKS_Btn1_Opera2.config(bg="gray90")
		self.TKS_OpDay_Month.delete(0, "end")
		self.TKS_OpDay_Month.insert(0, "")
		self.TKS_OpDay_Day.delete(0, "end")
		self.TKS_OpDay_Day.insert(0, "")
		self.TK_Rat_ID.delete(0, "end")
		self.TK_Rat_ID.insert(0, self.Rat_ID)

		self.TKS_Show_UserName.config(text="Users: (not set)", fg="gray35")
		self.TKS_Show_Disease.config(text="Model: (not set)", fg="gray35")
		self.TKS_Show_DisGroup.config(text="Group: (not set)", fg="gray35")
		self.TKS_Show_OpDay.config(text="TimePoint: (not set)", fg="gray35")
		self.TKS_Show_Opera.config(text="Operation Type: (not set)", fg="gray35")
		self.TKS_Show_Rat_ID.config(text="RatID: (not set)", fg="gray35")


	def InitExpMode(self, mode): #初始化實驗模式(前期訓練/後期測試)，訓練(使用者只需填入 使用者名稱 與 Model名稱)
		self.CleanExpSettingData()

		if mode == "EXPERIMENT":
			self.TKS_Btn1_Opera1.config(state="normal")
			self.TKS_Btn1_Opera2.config(state="normal")
			self.TKS_OpDay_Month.config(state="normal")
			self.TKS_OpDay_Day.config(state="normal")
			self.TKS_BT_OpDayConfirm.config(state="normal")
			# self.TKS_BT_DisGroupConfirm.config(state="normal")
			# self.TKS_BT_DisGroupModify.config(state="normal")
		elif mode == "TRAINING":
			# self.TK_Rat_ID.config(state="disabled")
			# self.BT_Rat_ID.config(state="disabled")
			self.TKS_Btn1_Opera1.config(state="disabled")
			self.TKS_Btn1_Opera2.config(state="disabled")
			self.TKS_OpDay_Month.config(state="disabled")
			self.TKS_OpDay_Day.config(state="disabled")
			self.TKS_BT_OpDayConfirm.config(state="disabled")

			self.DisGroupType = "Training"
			self.DisDays = [self.DisDays[0], 99, 99]
			self.OperaType = "Training"
			# self.Rat_ID = datetime.datetime.now().strftime("T%H%M%S")

			self.TKS_Show_DisGroup.config(text="Group: %s" %(self.DisGroupType), fg="black")
			self.TKS_Show_OpDay.config(text="TimePoint: %2d Month %2d Day" %(self.DisDays[1], self.DisDays[2]), fg="black")
			self.TKS_Show_Opera.config(text="Operation Type: %s" %(self.OperaType), fg="black")
			# self.TKS_Show_Rat_ID.config(text="RatID: %s" %(self.Rat_ID), fg="black")

		self.TK_Rat_ID.config(state="normal")
		self.BT_Rat_ID.config(state="normal")
		self.TK_User_Name.config(state="normal")
		self.BT_User_Name.config(state="normal")
		self.TKS_Disease.config(state="readonly")
		# self.TKS_DisGroup.config(state="readonly")
		self.TKS_BT_DisConfirm.config(state="normal")
		self.TKS_BT_DisModify.config(state="normal")

	def SystemModeSet(self, mode): #設定實驗模式： 前期訓練/後期測試
		self.EXP_DATA_MODE = mode
		self.InitExpMode(mode)
		if mode == "EXPERIMENT":
			self.TKS_Btn0_Mode2.config(bg="DarkOliveGreen2")
			self.TKS_Btn0_Mode1.config(bg="gray85")
		elif mode == "TRAINING":
			self.TKS_Btn0_Mode1.config(bg="DarkOliveGreen2")
			self.TKS_Btn0_Mode2.config(bg="gray85")
		# self.TKS_Btn0_Mode1.config(state="disabled")
		# self.TKS_Btn0_Mode2.config(state="disabled")
		self.TKS_title1_0.config(fg="gray35", bg="gray85")
		self.TKS_title1_1.config(fg="black", bg="gray75")

	def setupUI(self): #主UI視窗主程式
		global IPCAM_Info
		DBGV.CheckP_UI = "8"
		
		#========左側：紀錄變數========
		LoadCamInfo()
		#攝影機資訊選擇(下拉選單)
		CamInfo = ['choose IPCAM...']
		for i in range(len(IPCAM_Info)):
			CamInfo.append(IPCAM_Info[i][0])
		# print(CamInfo)
		self.InfoCombo = ttk.Combobox(self.tkWin, values=CamInfo, width=17, state="readonly")
		self.InfoCombo.place(x=20,y=25,anchor="w")
		self.InfoCombo.current(0)

		self.BT_LoadCAM = tk.Button(self.tkWin, text='Load', width=8, font=('Arial', 10), command=self.setIPCAMInfo)
		self.BT_LoadCAM.place(x=170,y=25,anchor="w")

		#========左側：按鈕1======== #, bg="DarkOliveGreen2"
		ButtonCateX1 = 20
		ButtonCateY1 = 50
		self.BT_Setting = tk.Button(self.tkWin, text='Setting', width=9, font=('Arial', 14), bg="gray85", command=self.tkSetting_SetupUI, state="disabled")
		# self.BT_Setting = tk.Button(self.tkWin, text='Setting', width=9, font=('Arial', 14), bg="gray85", command=self.OpenSetting, state="disabled")
		self.BT_Setting.place(x=ButtonCateX1+110, y=ButtonCateY1, anchor="nw")
		self.BT_Connect = tk.Button(self.tkWin, text='Link', width=9, font=('Arial', 14),bg="gray85", fg="dark green", command=self.ConnectClick, state="disabled")
		self.BT_Connect.place(x=ButtonCateX1, y=ButtonCateY1, anchor="nw")

		#========左側：按鈕2======== #, bg="DarkOliveGreen2"
		ButtonCateX2 = 20
		ButtonCateY2 = 480
		self.BT_Camera = tk.Button(self.tkWin, text='Camera', width=9, font=('Arial', 14), bg="gray85", command=self.CameraCheck, state="disabled")
		self.BT_Camera.place(x=ButtonCateX2+110, y=ButtonCateY2, anchor="nw")
		self.BT_Start = tk.Button(self.tkWin, text='Start', width=9, font=('Arial', 14),bg="gray85", command=self.MazeStartCheck, state="disabled")
		self.BT_Start.place(x=ButtonCateX2, y=ButtonCateY2, anchor="nw")

		#========左側：紀錄食物位置和詳細記憶錯誤========
		recFoodTX = 20
		recFoodTY = 110
		tk.Label(self.tkWin,text="Food/Term", font=('Arial', 12), bg="gray75").place(x=recFoodTX,y=recFoodTY,anchor="nw")
		tk.Label(self.tkWin,text="Long\nTerm", font=('Arial', 10)).place(x=recFoodTX + 125,y=recFoodTY - 5,anchor="n")
		tk.Label(self.tkWin,text="Short\nTerm", font=('Arial', 10)).place(x=recFoodTX + 190,y=recFoodTY - 5,anchor="n")
		for i in range(1, self.ARM_UNIT+1):
			self.TK_Food[i-1] = tk.IntVar()
			self.TK_L_Term[i-1] = tk.StringVar()
			self.TK_S_Term[i-1] = tk.StringVar()
			self.TK_L_Term[i-1].set(str(self.L_Term[i-1]))
			self.TK_S_Term[i-1].set(str(self.S_Term[i-1]))
			self.TKC_Food.append(0)
			posY = (recFoodTY + 35) + 42*(i-1)
			tk.Label(self.tkWin,text="Arm "+str(i), font=('Arial', 12)).place(x=recFoodTX,y=posY,anchor="nw")
			self.TKC_Food[i-1] = tk.Checkbutton(self.tkWin, variable=self.TK_Food[i-1], onvalue = 1, offvalue = 0, command=self.setFood, state="disabled")
			self.TKC_Food[i-1].place(x=recFoodTX + 60,y=posY,anchor="nw")
			tk.Label(self.tkWin,textvariable=self.TK_L_Term[i-1], font=('Arial', 12)).place(x=recFoodTX + 125,y=posY,anchor="n")
			tk.Label(self.tkWin,textvariable=self.TK_S_Term[i-1], font=('Arial', 12)).place(x=recFoodTX + 190,y=posY,anchor="n")

		#========中間：虛擬視窗顯示區域========
		self.mazeCanvas = tk.Canvas(bg="black", width = self.ViewSize[0], height = self.ViewSize[1])
		p1 = [int(self.TargetPos[0]/2 - self.BALL_SIZE/2), int(self.TargetPos[1]/2 - self.BALL_SIZE/2)]
		p2 = [int(self.TargetPos[0]/2 + self.BALL_SIZE/2), int(self.TargetPos[1]/2 + self.BALL_SIZE/2)]
		self.TBall = self.mazeCanvas.create_oval(p1[0], p1[1], p2[0], p2[1], fill='red')  #创建一个圆，填充色为`red`红色
		self.setArmNumber()
		self.setArmInLine()

		pViewX = 255 #虛擬視窗左上定位點X
		pViewY = 40 #虛擬視窗左上定位點Y
		self.setArmLine()
		self.mazeCanvas.place(x=pViewX, y=pViewY,anchor="nw")
		self.mazeTitle = tk.Label(self.tkWin,text="IPCAM:", font=('Arial', 12))
		self.mazeTitle.place(x=pViewX, y=pViewY-27,anchor="nw")

		#========右側：狀態顯示========
		StatusCateX = 750
		StatusCateY = 50
		StatusRange = 28
		tk.Label(self.tkWin,text="Status", font=('Arial', 12), bg="gray75").place(x=StatusCateX, y=StatusCateY-30,anchor="nw")
		self.Link_State = tk.Label(self.tkWin,text="IPCAM Link: Unlinked", font=('Arial', 13), fg="gray35")
		self.Link_State.place(x=StatusCateX, y=StatusCateY,anchor="nw")
		self.Cam_State = tk.Label(self.tkWin,text="Camera State: Unconnect", font=('Arial', 13), fg="gray35")
		self.Cam_State.place(x=StatusCateX, y=StatusCateY+StatusRange,anchor="nw")
		self.Maze_State = tk.Label(self.tkWin,text="Maze State: Preparing...", font=('Arial', 13), fg="gray35")
		self.Maze_State.place(x=StatusCateX, y=StatusCateY+StatusRange*2,anchor="nw")

		#========右側：顯示變數區域=======
		SettingShowX = 750
		SettingShowY = 120
		SettingLineRange = 26
		self.TKS_title5 = tk.Label(self.tkWin, text="Setting", font=('Arial', 12), bg="gray75")
		self.TKS_title5.place(x=SettingShowX,y=SettingShowY + 20,anchor="nw")
		
		if self.Rec_UserName != "":
			self.TKS_Show_UserName = tk.Label(self.tkWin, text="Users: %s" %(self.Rec_UserName), font=('Arial', 13), fg="black")
		else:
			self.TKS_Show_UserName = tk.Label(self.tkWin, text="Users: (not set)", font=('Arial', 13), fg="gray35")
		self.TKS_Show_UserName.place(x=SettingShowX+60,y=SettingShowY + 20,anchor="nw")

		self.TK_SHOW_Food = tk.Label(self.tkWin,text="Food: (not set)", font=('Arial', 12), fg="gray35")
		self.TK_SHOW_Food.place(x=SettingShowX, y=SettingShowY + (50 + SettingLineRange*0),anchor="nw")

		if self.DiseaseType != "":
			self.TKS_Show_Disease = tk.Label(self.tkWin, text="Model: {}".format(self.DiseaseType), font=('Arial', 13), fg="black")
		else:
			self.TKS_Show_Disease = tk.Label(self.tkWin, text="Model: (not set)", font=('Arial', 13), fg="gray35")
		self.TKS_Show_Disease.place(x=SettingShowX,y=SettingShowY + (50 + SettingLineRange*1),anchor="nw")

		if self.DisGroupType != "":
			self.TKS_Show_DisGroup = tk.Label(self.tkWin, text="Group: {}".format(self.DisGroupType), font=('Arial', 13), fg="black")
		else:
			self.TKS_Show_DisGroup = tk.Label(self.tkWin, text="Group: (not set)", font=('Arial', 13), fg="gray35")
		self.TKS_Show_DisGroup.place(x=SettingShowX,y=SettingShowY + (50 + SettingLineRange*2),anchor="nw")

		if self.OperaType != "":
			self.TKS_Show_Opera = tk.Label(self.tkWin, text="Operation Type: %s-Op" %(self.OperaType), font=('Arial', 13), fg="black")
		else:
			self.TKS_Show_Opera = tk.Label(self.tkWin, text="Operation Type: (not set)", font=('Arial', 13), fg="gray35")
		self.TKS_Show_Opera.place(x=SettingShowX,y=SettingShowY + (50 + SettingLineRange*3),anchor="nw")
		
		if self.DisDays[1] != -1 and self.DisDays[2] != -1:
			self.TKS_Show_OpDay = tk.Label(self.tkWin, text="TimePoint: %2d Month %2d Day" %(self.DisDays[1], self.DisDays[2]), font=('Arial', 13), fg="black")
		else:
			self.TKS_Show_OpDay = tk.Label(self.tkWin, text="TimePoint: (not set)", font=('Arial', 13), fg="gray35")
		self.TKS_Show_OpDay.place(x=SettingShowX, y=SettingShowY + (50 + SettingLineRange*4),anchor="nw")

		#========右側：紀錄變數========
		recValX = 750
		recValY = 310
		StatusRange = 30
		self.TK_Total_L_Term = tk.StringVar()
		self.TK_Total_S_Term = tk.StringVar()
		self.TK_Latency = tk.StringVar()
		nLate = Second2Datetime(0)
		self.TK_Latency.set("Latency: %02d:%02d:%02d" %(nLate[0],nLate[1],nLate[2]))
		self.TK_Total_L_Term.set("Total Long Term: %d" %(0))
		self.TK_Total_S_Term.set("Total Short Term: %d" %(0))
		tk.Label(self.tkWin,text="Statistics", font=('Arial', 12), bg="gray75").place(x=recValX,y=recValY,anchor="nw")
		tk.Label(self.tkWin,textvariable=self.TK_Total_L_Term, font=('Arial', 14)).place(x=recValX,y=recValY + (30 + StatusRange*0),anchor="nw")
		tk.Label(self.tkWin,textvariable=self.TK_Total_S_Term, font=('Arial', 14)).place(x=recValX,y=recValY + (30 + StatusRange*1),anchor="nw")
		tk.Label(self.tkWin,textvariable=self.TK_Latency, font=('Arial', 14)).place(x=recValX,y=recValY + (30 + StatusRange*2),anchor="nw")


		#========右側：顯示進出臂路徑========
		RouteShowX = 750
		RouteShowY = 440

		if self.Rat_ID != "":
			self.TKS_Show_Rat_ID = tk.Label(self.tkWin, text="RatID: %s" %(self.Rat_ID), font=('Arial', 13), fg="black")
		else:
			self.TKS_Show_Rat_ID = tk.Label(self.tkWin, text="RatID: (not set)", font=('Arial', 13), fg="gray35")
		self.TKS_Show_Rat_ID.place(x=RouteShowX+80, y=RouteShowY,anchor="nw")

		tk.Label(self.tkWin,text="Rat Route", font=('Arial', 12), bg="gray75").place(x=RouteShowX,y=RouteShowY,anchor="nw")
		self.RouteScroll = tk.Scrollbar(self.tkWin)
		self.RouteScroll.place(x=RouteShowX+260,y=RouteShowY+30,anchor="nw", height=57)
		self.RouteText = tk.Text(self.tkWin, font=('Arial', 11), width=32, height=3, yscrollcommand=self.RouteScroll.set)
		self.RouteText.place(x=RouteShowX,y=RouteShowY+30,anchor="nw")
		self.RouteScroll.config(command=self.RouteText.yview)

		#========下方：顯示各項資訊========
		# self.TK_SHOW_FileDir = tk.StringVar()
		self.TK_SHOW_SYS_Msg = tk.StringVar()
		self.TK_SHOW_SYS_Msg.set("Messenage: " + str(self.SYS_MSG))
		# tk.Label(self.tkWin,textvariable=self.TK_SHOW_FileDir, font=('Arial', 10)).place(x=20,y=self.WinSize[1]-10,anchor="sw")
		self.TK_SHOW_SYS_Msg_Text = tk.Label(self.tkWin,textvariable=self.TK_SHOW_SYS_Msg, font=('Arial', 10))
		self.TK_SHOW_SYS_Msg_Text.place(x=int(self.WinSize[0]/2),y=self.WinSize[1]-7,anchor="sw")

		DBGV.CheckP_UI = "9"

		self.tkWin.protocol("WM_DELETE_WINDOW", self.windowsClosing) # 關閉視窗=>protocol(關閉視窗參數，按下右上角的"X"關閉視窗會執行的程式)
		self.tkWin.after(10,self.LoopMain) # after為TKINTER版的sleep(延遲副程式)，為?ms後執行某個程式=>after(延遲?ms, 要執行的副程式)
		self.tkWin.mainloop()
		
		# join()等待子執行緒結束
		self.thread.join() 
		self.CAMThread.join()
		self.DBGVThread.join()

		DBGV.CheckP_UI = "10"
		
if __name__ == '__main__':
  MazeMouseTrack()
