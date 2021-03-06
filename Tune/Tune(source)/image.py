import serial
import matplotlib
matplotlib.use("tkagg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.animation as animation
import tkinter as tk
from PIL import Image, ImageTk
import time
import os
import struct
from ctypes import c_uint8

def open_port(Port_no,self,com_status):
    global ser
    comPort = "COM" + Port_no
    baudRate = 115200
    try:
        ser = serial.Serial(comPort,baudRate,timeout=5)
        com_status.config(text = "Connected")
    except serial.SerialException as e:
        if "OSError" in str(e.args):
            com_status.config(text = "TImeOut")
        else:
            com_status.config(text = "Bluetooth is off")
    except:
        com_status.config(text = "Error")
    self.newWindow = tk.Toplevel(self)
    self.app = video_page(self.newWindow)

def close_port(self,com_status):
    if self.newWindow:
        self.newWindow.destroy()
    ser.close()
    com_status.config(text = "Disconnect")

def start(mode,self):
    global status
    if ser.inWaiting() != 0:
        ser.reset_input_buffer()
        time.sleep(.5)
        ser.reset_input_buffer()
    status = True

    if mode == "video":
        global width,imageSize,height
        ser.write(b'c')
        num = ser.readline().decode("ascii")
        width = int(num[0:-1])
        self.width_label.config(text = "Width: " + str(width))
        num = ser.readline().decode("ascii")
        imageSize = int(num[0:-1])
        height = int(imageSize * 8 / width)
        self.height_label.config(text = "Height: " + str(height))
        video_animate()
    elif mode == "PID":
        ser.write(b'g')

def stop():
    global status
    ser.write(b's')
    status = False

def sendData(text):
    buffer = text.split(',')
    for data in buffer:
        if data == '':
            continue
        try:
            data = float(data)
            data_array = bytearray(struct.pack(">f", data))
            for b in data_array:
                ser.write(c_uint8(b))
        except ValueError:
            data = str(data)
            ser.write(data.encode(encoding= 'ascii'))
        time.sleep(0.05)

def sendPID(self):
    global kp,kd,ki
    m_kp = self.kp_entry.get()
    m_ki = self.ki_entry.get()
    m_kd = self.kd_entry.get()
    if kp != float(m_kp):
        kp = float(m_kp)
        data = bytearray(struct.pack(">f", kp))
        ser.write(b'p')
        for b in data:
            while(True):
                if(ser.read() == b'\n'):
                    ser.write(c_uint8(b))
                    break
    time.sleep(0.05)
    if ki != float(m_ki):
        ki = float(m_ki)
        data = bytearray(struct.pack(">f", ki))
        ser.write(b'i')
        for b in data:
            while(True):
                if(ser.read() == b'\n'):
                    ser.write(c_uint8(b))
                    break
    time.sleep(0.05)
    if kd != float(m_kd):
        kd = float(m_kd)
        data = bytearray(struct.pack(">f", kd))
        ser.write(b'd')
        for b in data:
            while(True):
                if(ser.read() == b'\n'):
                    ser.write(c_uint8(b))
                    break

def save_status(save_mode):
    global save
    save = not save

    if save:
        save_mode.config(text = "On")
    else:
        save_mode.config(text = "Off")

def video_animate():
    global image,img,pixels,frameNo
    if status:
        pixels = ser.read(size = int(imageSize))
    image = Image.frombytes('1',(width,height),pixels)
    img = ImageTk.PhotoImage(image)
    if save:
        image.save(newpath + r'\frame'+str(frameNo)+'.bmp')
        frameNo+=1
    fig.itemconfig(fig.image,image = img)
    app.update_idletasks()
    app.after(50,video_animate)

def PID_animate(i):
    global x_value
    if ser.in_waiting == 0 or not status:
        return
    data = ser.readline().decode("ascii").strip('\n')
    if data != '':
        a,b = data.split(",")
        target_line.append(target)
        target_line1.append(target1)
        x.append(x_value)
        x_value+=1
        value1.append(int(a[2:]))
        value2.append(int(b))
    ax.clear()
    ax.plot(x,value1,'b-',x,target_line,'r',x,value2,'g',x,target_line1,'y')

def switch_win(mode,frame):
    frame.newWindow.destroy()
    frame.newWindow = tk.Toplevel(frame)
    global status
    if status:
        ser.write(b's')
        status = False

    if mode == "PID":
        frame.app = PID_page(frame.newWindow)
    elif mode == "video":
        frame.app = video_page(frame.newWindow)

def change_setting(output,self):
    global contrast,brightness
    if output == "c+":
        ser.write(b"e")
        contrast+=1
    elif output == "c-":
        ser.write(b"r")
        contrast-=1
    elif output == "b+":
        ser.write(b"q")
        brightness+=1
    elif output == "b-":
        ser.write(b"w")
        brightness-=1
    self.c_label.config(text = contrast)
    self.b_label.config(text = brightness)

def change_target(input_value):
    global target,target1
    target = int(input_value)
    target1 = -int(input_value)
    if target < 0:
        data = bytearray(struct.pack(">I", -target))
        ser.write(b't')
        for b in data:
            while(True):
                if(ser.read() == b'\n'):
                    ser.write(c_uint8(b))
                    break
        time.sleep(0.5)
        ser.write(b'n')
    else:
        data = bytearray(struct.pack(">I", target))
        ser.write(b't')
        for b in data:
            while(True):
                if(ser.read() == b'\n'):
                    ser.write(c_uint8(b))
                    break

def reset():
    global x_value,value1,x,target_line,value2,target_line1
    x_value = 1
    value1 = [0]
    value2 = [0]
    x =[1]
    target_line =[target]
    target_line1 =[target1]
    ser.reset_input_buffer()
    ax.clear()

class GUI(tk.Tk):
    def __init__(self,*args,**kwargs):
        tk.Tk.__init__(self,*args,**kwargs)

        container = tk.Frame(self)
        container.pack(side ="top",fill = "both", expand = True)

        frame = main_page(container,self)
        frame.grid(row = 0 ,column = 0 , sticky = "nsew")
        frame.tkraise()

class main_page(tk.Frame):
    def __init__(self,parent,controller):
        tk.Frame.__init__(self,parent)

        status_frame = tk.Frame(self)
        com_status = tk.Label(status_frame,text = "Disconnect",font =("Helvetica",15))

        main_frame = tk.Frame(self)
        com_label = tk.Label(main_frame,text = "Com Port:",font =("Helvetica",15),padx = 10)
        com_entry = tk.Entry(main_frame,width = 7)
        connect = tk.Button(main_frame,text ="open",font =("Helvetica",10),padx = 5, command = lambda : open_port(com_entry.get(),self,com_status))
        disconnect = tk.Button(main_frame,text ="close",font =("Helvetica",10),padx = 5,command = lambda : close_port(self,com_status))

        com_label.pack(side = tk.LEFT)
        com_entry.pack(side = tk.LEFT)
        connect.pack(side = tk.LEFT, padx = 5)
        disconnect.pack(side = tk.LEFT, padx = 5)
        com_status.pack()

        page_frame = tk.Frame(self)
        pid = tk.Button(page_frame,text = "PID",command = lambda: switch_win("PID",self),font =("Helvetica",9))
        video = tk.Button(page_frame,text = "Image",command = lambda: switch_win("video",self),font =("Helvetica",9))
        pid.pack(side = tk.RIGHT,padx = [20,0])
        video.pack(side = tk.RIGHT)

        main_frame.pack(fill= tk.X,pady = [15,5])
        status_frame.pack(fill= tk.X,pady=10)
        page_frame.pack(pady = [0,15])

class video_page(tk.Frame):
    def __init__(self,parent):
        global fig,img
        self.parent = parent
        self.frame = tk.Frame(parent)
        self.fig_frame = tk.Frame(parent)
        self.value_frame = tk.Frame(parent)
        self.setting_frame = tk.Frame(parent)
        self.save_frame = tk.Frame(parent)

        self.width_label = tk.Label(self.value_frame,text = "Width: ",font =("Helvetica",9))
        self.height_label = tk.Label(self.value_frame,text = "Height: ",font =("Helvetica",9))
        self.c_label = tk.Label(self.setting_frame,text= "0",font =("Helvetica",9))
        self.b_label = tk.Label(self.setting_frame,text= "0",font =("Helvetica",9))

        connect = tk.Button(self.frame,text ="Start", command = lambda:start("video",self),font =("Helvetica",11))
        stop_button = tk.Button(self.frame,text ="Stop", command = stop,font =("Helvetica",11))
        c_plus = tk.Button(self.setting_frame,text ="contrast +", command = lambda: change_setting("c+",self),font =("Helvetica",9))
        c_minus = tk.Button(self.setting_frame,text ="contrast -", command = lambda: change_setting("c-",self),font =("Helvetica",9))
        b_plus = tk.Button(self.setting_frame,text ="brightness +", command = lambda: change_setting("b+",self),font =("Helvetica",9))
        b_minus = tk.Button(self.setting_frame,text ="brightness -", command = lambda: change_setting("b-",self),font =("Helvetica",9))
        fig = tk.Canvas(self.fig_frame, width=width, height=height)
        img = ImageTk.PhotoImage(image)
        fig.image = fig.create_image(100,80,image = img)

        save_mode = tk.Label(self.save_frame,text = "Off", font =("Helvetica",10))
        save_image = tk.Button(self.save_frame,text ="save", command = lambda: save_status(save_mode), font =("Helvetica",10))

        connect.pack(side = tk.LEFT)
        stop_button.pack( side = tk.LEFT,padx = 15)
        self.frame.pack(pady = [20,10])
        fig.pack(padx= [70,0])
        self.fig_frame.pack()
        self.width_label.pack(padx = [0,10],side = tk.LEFT)
        self.height_label.pack(side = tk.LEFT)
        self.value_frame.pack()
        c_plus.pack(side = tk.LEFT,padx = [10,0])
        self.c_label.pack(side = tk.LEFT,padx = 10)
        c_minus.pack(side = tk.LEFT)
        b_plus.pack(side = tk.LEFT,padx = 10)
        self.b_label.pack(side = tk.LEFT)
        b_minus.pack(side = tk.LEFT,padx = 10)
        self.setting_frame.pack(pady=10)
        save_image.pack(side = tk.LEFT)
        save_mode.pack(side = tk.LEFT,padx =[5,0])
        self.save_frame.pack()

class PID_page(tk.Frame):
    def __init__(self,parent):
        self.parent = parent
        global ani

        canvas_frame = tk.Frame(parent)
        canvas = FigureCanvasTkAgg(graph_fig,canvas_frame)
        canvas.show()
        ani = animation.FuncAnimation(graph_fig, PID_animate, interval= 5)

        action_frame = tk.Frame(parent)
        start_button = tk.Button(action_frame,text = "Start", command = lambda : start("PID",self),width = 10)
        stop_button = tk.Button(action_frame,text = "Stop", command = stop,width = 10)
        reset_button = tk.Button(action_frame,text = "reset",command = reset)
        set_target = tk.Label(action_frame, text = "Target Speed: ",font =("Helvetica",10))
        target_display = tk.Entry(action_frame,width = 7)
        target_button = tk.Button(action_frame,width = 5,text = "Set",font =("Helvetica",10), command = lambda: change_target(target_display.get()))
        target_display.insert(0,target)
        value_frame = tk.Frame(parent)
        kp_label = tk.Label(value_frame,text = "Kp")
        self.kp_entry = tk.Entry(value_frame,width = 10)
        self.kp_entry.insert(0,kp)
        kd_label = tk.Label(value_frame,text = "Kd")
        self.kd_entry = tk.Entry(value_frame,width = 10)
        self.kd_entry.insert(0,kd)
        ki_label = tk.Label(value_frame,text = "Ki")
        self.ki_entry = tk.Entry(value_frame,width = 10)
        self.ki_entry.insert(0,ki)
        ok = tk.Button(value_frame,text="Set",width = 15,command = lambda: sendPID(self))

        Data_frame = tk.Frame(parent)
        input_box = tk.Text(Data_frame,width = 50,height = 10,wrap = "word")
        send_data = tk.Button(Data_frame,text = "Send",width = 10,command = lambda: sendData(input_box.get("1.0",tk.END)))

        canvas_frame.pack(fill= tk.X)
        action_frame.pack(fill= tk.X)
        value_frame.pack(fill= tk.X)
        Data_frame.pack(fill = tk.X)
        canvas.get_tk_widget().pack()
        start_button.pack(padx= 10,side = tk.LEFT)
        stop_button.pack(padx= 5,side = tk.LEFT)
        reset_button.pack(padx = [6,0],side = tk.LEFT)
        set_target.pack(padx = [75,0],side = tk.LEFT)
        target_display.pack(side = tk.LEFT,padx = 5)
        target_button.pack(side = tk.LEFT)
        kp_label.pack(padx = 5,side =tk.LEFT)
        self.kp_entry.pack(padx = 5,side =tk.LEFT)
        kd_label.pack(padx = 5,side =tk.LEFT)
        self.kd_entry.pack(padx = 5,side =tk.LEFT)
        ki_label.pack(padx = 5,side =tk.LEFT)
        self.ki_entry.pack(padx = 5,side =tk.LEFT)
        ok.pack(pady = 10)
        input_box.pack(side = tk.LEFT,padx = [30,10], pady = [0,10])
        send_data.pack(side = tk.LEFT)

#start of the program
global img,fig,ser,ani

status = False
save = False
width = 320
height = 180
imageSize = width*height /8
contrast = 0
brightness = 0
frameNo = 0
value1 =[0]
value2 =[0]
x = [1]
x_value = 1
kp = 0.0
kd = 0.0
ki = 0.0
target = 0
target_line = [target]
target1 = 0
target_line1 = [target1]
image_path = r'.\image\sample'
folder_no = 1
newpath= image_path +  str(folder_no)
while os.path.exists(newpath) and len(os.listdir(newpath)):
    folder_no+=1
    newpath = image_path + str(folder_no)
if not os.path.exists(newpath):
    os.makedirs(newpath)

graph_fig = Figure(figsize = (5,3),dpi = 100)
ax = graph_fig.add_subplot(111)

pixels = b'\x00' * int(imageSize)
image = Image.frombytes('1',(width,height),pixels)

app = GUI()
app.mainloop()

if ser.isOpen():
    ser.close()
'''
ser = serial.Serial("COM8",115200,timeout=5)
ser.write(b'e')
ser.read_all()
pixels = ser.read(size = int(imageSize))
image = Image.frombytes('1',(width,height),pixels)
ser.inWaiting()
ser.flushInput()
ser.close()
'''
