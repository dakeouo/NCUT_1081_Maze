import random
import tkinter as tk
import tkinter.messagebox
from tkinter import filedialog
import threading
# from ThermalCAM import ThermalCAM as TCAM
from InfraredCAM import InfraredCAM as TCAM

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

class MazeMouseTrack(object):
	def __init__(self):
		#熱影像相機的類別
		self.TCAM = TCAM()
		self.thread = threading.Thread(target = self.TCAM.CameraMain) # 執行該子執行緒
		self.thread.start()  # 執行該子執行緒

		#變數：迷宮系統相關
		self.ARM_UNIT = self.TCAM.getArmUnit() #迷宮臂數
		self.ARMS_POS = self.TCAM.getMazeArmsPos() #迷宮臂座標點
		self.OPEN_CAMERA_WINDOW = False #影像視窗狀態
		self.TotalFood = 0 #放食物的總數
		self.Food = [] #放食物的臂
		self.Route = [] #紀錄進臂順序
		self.S_Term = [] #各臂短期記憶錯誤
		self.L_Term = [] #各臂長期記憶錯誤
		self.FilePath = "" #存入的路徑
		self.FileName = "" #存入的檔案
		self.TargetPos = self.TCAM.getTargetPos() #影像處理後取得的座標
		self.nowPos = self.TargetPos
		self.Latency = 0 #總時間長度

		#變數：視窗相關
		self.WinSize = (1152, 560) #UI介面顯示大小
		self.BALL_SIZE = 20
		self.ViewSize = self.TCAM.getViewHW() #虛擬視窗顯示大小
		self.MAZE_IS_RUN = False #當前系統是否在執行
		self.CAM_IS_CONN = self.TCAM.getCameraStatus() #當前鏡頭是否連線
		self.TK_Food = [] #勾選放食物的臂
		self.TK_S_Term = [] #顯示各臂短期記憶錯誤
		self.TK_L_Term = [] #顯示各臂長期記憶錯誤
		self.TK_Total_S_Term = 0 #顯示短期記憶錯誤總和
		self.TK_Total_L_Term = 0 #顯示長期記憶錯誤總和
		self.TK_File_Dir = "" #顯示存入的檔案(含路徑)
		self.TK_Rat_ID = "" #顯示老鼠編號
		self.ERROR_MSG = "" #顯示錯誤訊息
		self.TK_Latency = 0 #顯示總時間長度

		#變數：顯示目前設定狀態
		self.TK_SHOW_Food = []
		self.TK_SHOW_FileDir = ""
		self.TK_SHOW_Rat_ID = ""
		self.TK_SHOW_Error_Msg = ""
		self.TKE_Dir = ""
		self.TKC_Food = []

		self.tkWin = tk.Tk()
		self.tkWin.title('%d Arms Maze Tracking' %(self.ARM_UNIT)) #窗口名字
		self.tkWin.geometry('%dx%d+20+20' %(self.WinSize[0],self.WinSize[1])) #窗口大小(寬X高+X偏移量+Y偏移量)
		self.tkWin.resizable(False, False) #禁止變更視窗大小
		self.setEachVariable() #各項變數初始化
		self.setupUI() #視窗主程式

	def setArmLine(self): #繪製迷宮框
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
		RAT_ID = self.TK_Rat_ID.get()
		Unit = countStr(RAT_ID)
		str1 = "# RatID: {}".format(RAT_ID)
		move = 288 - (Unit[0]*11 + (Unit[1] + Unit[2] + Unit[3])*9)
		self.TK_SHOW_Rat_ID.config(text=str1)
		self.TK_SHOW_Rat_ID.place(x=self.WinSize[0]-move,y=200,anchor="ne")
		# print(len(RAT_ID))

	def setFood(self): #設定食物放在哪個臂
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
		if(ct == 0):
			str1 = "# Food: "
			move = 290
		else:
			str1 = "# Food: {}".format(hadFood)
			move = 290 - ct*17

		self.TK_SHOW_Food.config(text=str1)
		self.TK_SHOW_Food.place(x=self.WinSize[0]-move,y=170,anchor="ne")

	def MazeStartCheck(self): #執行前檢查
		HaveError = False
		if self.MAZE_IS_RUN:
			self.Maze_State.config(text="Maze State: Preparing...", fg="gray35")
			self.Maze_State.place(x=self.WinSize[0]-170,y=140,anchor="ne")
			self.BT_Start.config(text="Start", bg="DarkOliveGreen2")
			self.MAZE_IS_RUN = False
		else:
			ErrMsg = ""
			if self.FilePath == "":
				ErrMsg = ErrMsg + "File Path not filled!!\n"
				HaveError = True
			if self.TK_Rat_ID.get() == "":
				ErrMsg = ErrMsg + "Rat ID not filled!!\n"
				HaveError = True
			if self.TotalFood == 0:
				ErrMsg = ErrMsg + "You don't have click any food!!\n"
				HaveError = True
			
			if HaveError:
				tk.messagebox.showwarning(title='Warning!!', message=ErrMsg)
			else:
				self.TCAM.setFoodWithArm(self.TotalFood, self.Food)
				self.TCAM.setRatID(self.TK_Rat_ID.get())
				self.TCAM.setFilePath(str(self.FilePath)+str(self.FileName))
				self.Maze_State.config(text="Maze State: Recording...", fg="green4")
				self.Maze_State.place(x=self.WinSize[0]-167,y=140,anchor="ne")
				self.BT_Start.config(text="Stop", bg="IndianRed1")
				self.MAZE_IS_RUN = True
		self.TCAM.setMazeStatus(self.MAZE_IS_RUN)

	def CameraCheck(self): #實體影像檢查
		if self.OPEN_CAMERA_WINDOW:
			self.BT_Camera.config(bg="gray85")
			self.OPEN_CAMERA_WINDOW = False
		else:
			self.BT_Camera.config(bg="lemon chiffon")
			self.OPEN_CAMERA_WINDOW = True
		self.TCAM.setCameraWindow(self.OPEN_CAMERA_WINDOW)

	def Choose_Dir(self): #選擇CSV檔要存至哪個位置
		FileDir = filedialog.asksaveasfilename(
			initialdir = self.FilePath,title = "Select file", 
			filetypes = (("csv files","*.csv"),("all files","*.*")),
			defaultextension='.csv'
		)
		if str(FileDir) != "":
			PATH = FileDir.split("/")
			self.FilePath = ""
			for i in range(0,len(PATH)-1):
				self.FilePath = self.FilePath + PATH[i] + "/"
			self.FileName = PATH[len(PATH)-1]
		self.TK_File_Dir.set(str(self.FilePath)+str(self.FileName))
		self.TK_SHOW_FileDir.set("# FileDir: {}{}".format(self.FilePath, self.FileName))
		# print(self.FilePath)
		# print(self.FileName)

	def makeBall(self): #變更目標位置
		self.TargetPos = self.TCAM.getTargetPos()
		self.mazeCanvas.move(self.TBall, int(self.TargetPos[0] - self.nowPos[0]), int(self.TargetPos[1] - self.nowPos[1]))
		self.nowPos = self.TargetPos

	def updateData(self): #更新各項顯示資訊
		self.S_Term, self.L_Term = self.TCAM.getTerm()
		self.Route = self.TCAM.getRoute()
		self.Latency = self.TCAM.getLatency()
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

	def LockInput(self, state):
		if state:
			self.TKE_Dir.config(state="disabled")
			self.TK_Rat_ID.config(state="disabled")
			for i in range(0,self.ARM_UNIT):
				self.TKC_Food[i].config(state="disabled")
		else:
			self.TKE_Dir.config(state="normal")
			self.TK_Rat_ID.config(state="normal")
			for i in range(0,self.ARM_UNIT):
				self.TKC_Food[i].config(state="normal")

	def LoopMain(self): #UI執行後一直跑的迴圈
		self.makeBall()
		self.CAM_IS_CONN = self.TCAM.getCameraStatus()

		if self.MAZE_IS_RUN:
			self.LockInput(True)
			newMazeStatus = self.TCAM.getMazeStatus()
			self.updateData()
			if newMazeStatus == False:
				self.Maze_State.config(text="Maze State: Preparing...", fg="gray35")
				self.Maze_State.place(x=self.WinSize[0]-170,y=140,anchor="ne")
				self.BT_Start.config(text="Start", bg="DarkOliveGreen2")
				self.MAZE_IS_RUN = False
		else:
			self.LockInput(False)
			
		if self.CAM_IS_CONN:
			self.Cam_State.config(text="Camera State: Connecting...", fg="green4")
			self.Cam_State.place(x=self.WinSize[0]-140,y=110,anchor="ne")
			self.BT_Camera.config(state="normal")
		else:
			self.Cam_State.config(text="Camera State: Unconnect", fg="gray35")
			self.Cam_State.place(x=self.WinSize[0]-160,y=110,anchor="ne")
			self.BT_Camera.config(state="disabled")

		self.tkWin.after(10,self.LoopMain)

	def windowsClosing(self):
		self.TCAM.setInterfaceStatus(False) #傳送視窗關閉狀態
		self.tkWin.destroy()

	def PreparingTesting(self):
		#=======食物位置設置========
		hadFood = []
		ct = 0
		for i in range(0,self.ARM_UNIT):
			num = random.randint(0,1)
			if(num == 1): 
				hadFood.append((i+1))
				self.Food[i] = 1
				ct = ct + 1
			else:
				self.Food[i] = 0
			self.TK_Food[i].set(num)
		self.TotalFood = ct
		if(ct == 0):
			str1 = "# Food: "
			move = 290
		else:
			str1 = "# Food: {}".format(hadFood)
			move = 290 - ct*17

		self.TK_SHOW_Food.config(text=str1)
		self.TK_SHOW_Food.place(x=self.WinSize[0]-move,y=170,anchor="ne")
		#========檔案存放位置設置========
		self.FilePath = "D:/4A813024/"
		self.FileName = "testing%0d.csv" %(random.randint(1,3))
		self.TK_File_Dir.set(str(self.FilePath)+str(self.FileName))
		self.TK_SHOW_FileDir.set("# FileDir: {}{}".format(self.FilePath, self.FileName))
		#========老鼠編號設置========
		RAT_ID = "TEST%0d" %(random.randint(1,20))
		self.TK_Rat_ID.delete(first=0,last=22)
		self.TK_Rat_ID.insert('end',RAT_ID)
		Unit = countStr(RAT_ID)
		str1 = "# RatID: {}".format(RAT_ID)
		move = 288 - (Unit[0]*11 + (Unit[1] + Unit[2] + Unit[3])*9)
		self.TK_SHOW_Rat_ID.config(text=str1)
		self.TK_SHOW_Rat_ID.place(x=self.WinSize[0]-move,y=200,anchor="ne")

	def setupUI(self):
		#========測試用========
		# tk.Button(self.tkWin, text='Testing', width=10, font=('Arial', 8), command=self.PreparingTesting).place(x=100,y=10,anchor="nw")

		#========左側：紀錄變數========
		self.TK_Total_L_Term = tk.StringVar()
		self.TK_Total_S_Term = tk.StringVar()
		self.TK_Latency = tk.StringVar()
		nLate = Second2Datetime(0)
		self.TK_Latency.set("Latency: %02d:%02d:%02d" %(nLate[0],nLate[1],nLate[2]))
		self.TK_Total_L_Term.set("Total Long Term: %d" %(0))
		self.TK_Total_S_Term.set("Total Short Term: %d" %(0))
		tk.Label(self.tkWin,text="Statistics", font=('Arial', 12), bg="gray75").place(x=20,y=10,anchor="nw")
		tk.Label(self.tkWin,textvariable=self.TK_Total_L_Term, font=('Arial', 14)).place(x=20,y=40,anchor="nw")
		tk.Label(self.tkWin,textvariable=self.TK_Total_S_Term, font=('Arial', 14)).place(x=20,y=80,anchor="nw")
		tk.Label(self.tkWin,textvariable=self.TK_Latency, font=('Arial', 14)).place(x=20,y=120,anchor="nw")

		#========左側：紀錄食物位置和詳細記憶錯誤========
		tk.Label(self.tkWin,text="Food/Term", font=('Arial', 12), bg="gray75").place(x=20,y=170,anchor="nw")
		tk.Label(self.tkWin,text="Long Term", font=('Arial', 10)).place(x=160,y=175,anchor="n")
		tk.Label(self.tkWin,text="Short Term", font=('Arial', 10)).place(x=240,y=175,anchor="n")
		for i in range(1, self.ARM_UNIT+1):
			self.TK_Food[i-1] = tk.IntVar()
			self.TK_L_Term[i-1] = tk.StringVar()
			self.TK_S_Term[i-1] = tk.StringVar()
			self.TK_L_Term[i-1].set(str(self.L_Term[i-1]))
			self.TK_S_Term[i-1].set(str(self.S_Term[i-1]))
			self.TKC_Food.append(0)
			posY = 215 + 40*(i-1)
			tk.Label(self.tkWin,text="Arm "+str(i), font=('Arial', 12)).place(x=20,y=posY,anchor="nw")
			self.TKC_Food[i-1] = tk.Checkbutton(self.tkWin, variable=self.TK_Food[i-1], onvalue = 1, offvalue = 0, command=self.setFood)
			self.TKC_Food[i-1].place(x=80,y=posY,anchor="nw")
			tk.Label(self.tkWin,textvariable=self.TK_L_Term[i-1], font=('Arial', 12)).place(x=160,y=posY,anchor="n")
			tk.Label(self.tkWin,textvariable=self.TK_S_Term[i-1], font=('Arial', 12)).place(x=240,y=posY,anchor="n")

		#========中間：虛擬視窗顯示區域========
		self.mazeCanvas = tk.Canvas(bg="black", width = self.ViewSize[0], height = self.ViewSize[1])
		p1 = [int(self.TargetPos[0]/2 - self.BALL_SIZE/2), int(self.TargetPos[1]/2 - self.BALL_SIZE/2)]
		p2 = [int(self.TargetPos[0]/2 + self.BALL_SIZE/2), int(self.TargetPos[1]/2 + self.BALL_SIZE/2)]
		self.TBall = self.mazeCanvas.create_oval(p1[0], p1[1], p2[0], p2[1], fill='red')  #创建一个圆，填充色为`red`红色

		pViewX = int((self.WinSize[0]-self.ViewSize[0])*0.45) #虛擬視窗左上定位點X
		pViewY = int((self.WinSize[1]-self.ViewSize[1])*0.45) #虛擬視窗左上定位點Y
		self.setArmLine()
		self.mazeCanvas.place(x=pViewX, y=pViewY,anchor="nw")

		#========右側：按鈕========
		self.BT_Camera = tk.Button(self.tkWin, text='Camera', width=14, font=('Arial', 14), bg="gray85", command=self.CameraCheck)
		self.BT_Camera.place(x=self.WinSize[0]-20,y=20,anchor="ne")
		self.BT_Start = tk.Button(self.tkWin, text='Start', width=14, font=('Arial', 14), bg="DarkOliveGreen2", command=self.MazeStartCheck)
		self.BT_Start.place(x=self.WinSize[0]-190,y=20,anchor="ne")

		#========右側：狀態顯示========
		tk.Label(self.tkWin,text="Status", font=('Arial', 12), bg="gray75").place(x=self.WinSize[0]-300,y=80,anchor="ne")
		self.Cam_State = tk.Label(self.tkWin,text="Camera State: Unconnect", font=('Arial', 13), fg="gray35")
		self.Cam_State.place(x=self.WinSize[0]-160,y=110,anchor="ne")
		self.Maze_State = tk.Label(self.tkWin,text="Maze State: Preparing...", font=('Arial', 13), fg="gray35")
		self.Maze_State.place(x=self.WinSize[0]-170,y=140,anchor="ne")

		self.TK_SHOW_Food = tk.Label(self.tkWin,text="# Food: ", font=('Arial', 12))
		self.TK_SHOW_Food.place(x=self.WinSize[0]-290,y=170,anchor="ne")
		self.TK_SHOW_Rat_ID = tk.Label(self.tkWin,text="# RatID: ", font=('Arial', 12))
		self.TK_SHOW_Rat_ID.place(x=self.WinSize[0]-288,y=200,anchor="ne")

		#========右側：選擇檔案存放位置========
		self.TK_File_Dir = tk.StringVar()
		tk.Label(self.tkWin,text="Record File Directory", font=('Arial', 12), bg="gray75").place(x=self.WinSize[0]-197,y=240,anchor="ne")
		self.TKE_Dir = tk.Entry(self.tkWin, textvariable=self.TK_File_Dir, font=('Arial', 11), width=30)
		self.TKE_Dir.place(x=self.WinSize[0]-107,y=270,anchor="ne")
		tk.Button(self.tkWin, text='Choose...', width=10,command=self.Choose_Dir).place(x=self.WinSize[0]-20,y=267,anchor="ne")

		#========右側：設定老鼠編號========
		tk.Label(self.tkWin,text="Rat ID", font=('Arial', 12), bg="gray75").place(x=self.WinSize[0]-302,y=305,anchor="ne")
		self.TK_Rat_ID = tk.Entry(self.tkWin, font=('Arial', 12), width=20)
		self.TK_Rat_ID.place(x=self.WinSize[0]-107,y=307,anchor="ne")
		tk.Button(self.tkWin, text='Set ID', width=10,command=self.SetRatID).place(x=self.WinSize[0]-20,y=305,anchor="ne")

		#========右側：顯示進出臂路徑========
		tk.Label(self.tkWin,text="Rat Route", font=('Arial', 12), bg="gray75").place(x=self.WinSize[0]-277,y=340,anchor="ne")
		self.RouteScroll = tk.Scrollbar(self.tkWin)
		self.RouteScroll.place(x=self.WinSize[0]-20,y=370,anchor="ne", height=125)
		self.RouteText = tk.Text(self.tkWin, font=('Arial', 11), width=39, height=7, yscrollcommand=self.RouteScroll.set)
		self.RouteText.place(x=self.WinSize[0]-37,y=370,anchor="ne")
		self.RouteScroll.config(command=self.RouteText.yview)

		#========下方：顯示各項資訊========
		self.TK_SHOW_FileDir = tk.StringVar()
		self.TK_SHOW_Error_Msg = tk.StringVar()
		self.TK_SHOW_FileDir.set("# FileDir: {}{}".format(self.FilePath, self.FileName))
		self.TK_SHOW_Error_Msg.set("# ERROR Message: " + str(self.ERROR_MSG))
		tk.Label(self.tkWin,textvariable=self.TK_SHOW_FileDir, font=('Arial', 10)).place(x=20,y=self.WinSize[1]-10,anchor="sw")
		if(self.ERROR_MSG):
			tk.Label(self.tkWin,textvariable=self.TK_SHOW_Error_Msg, font=('Arial', 10), fg="red").place(x=int(self.WinSize[0]/2),y=self.WinSize[1]-10,anchor="sw")
		else:
			tk.Label(self.tkWin,textvariable=self.TK_SHOW_Error_Msg, font=('Arial', 10)).place(x=int(self.WinSize[0]/2),y=self.WinSize[1]-10,anchor="sw")

		
		self.tkWin.protocol("WM_DELETE_WINDOW", self.windowsClosing)
		self.tkWin.after(10,self.LoopMain)
		self.tkWin.mainloop()
		self.thread.join() # 等待子執行緒結束
		
if __name__ == '__main__':
  MazeMouseTrack()
