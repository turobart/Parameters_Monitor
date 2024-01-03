'''
Author: Bartłomiej Turowski
International Research Centre MagTop, Institute of Physics, Polish Academy of Sciences
Aleja Lotnikow 32/46, PL-02668 Warsaw, Poland
Date: 13.07.2018
'''

# -*- coding: utf-8 -*-

import wx
import serial.tools.list_ports
import datetime
import os.path
from wx.lib.masked import NumCtrl
import gc
import wx.lib.scrolledpanel as scrolled
import time
import sys

#bunch of globals to keep everything together
global time_list, water_list, temp1_list, temp2_list, values, time_old, currentDirectory, discard_ard_war
global main_frame, water_window, water_flow_value, plugged, ser, n_ard, T_in, T_out, W_flow
global pump1_ser, pump1_ser_old, pump1_com_id_old, pump1_starting, freq1
global pump2_ser, pump2_ser_old, pump2_com_id_old, pump2_starting, freq2
global pump_delay, save_delay
global cryo1_ser, cryo1_ser_old, cryo1_com_id_old, cryo1_1st_ch, cryo1_2nd_ch, c_2nd_ch_1st
global cryo2_ser, cryo2_ser_old, cryo2_com_id_old, cryo2_1st_ch, cryo2_2nd_ch
global side_T, LL_T, top_T, buffer_T, c_1st_ch_1st, alarm_sent, side_alarm, buffer_alarm, top_alarm
global side_font_war, top_font_war, buffer_font_war, power1, alarm_enabled, ll_font_war
global count, current_date

alarm_enabled = True
#change font colour if warning 
ll_font_war = False
side_font_war = False
top_font_war = False
buffer_font_war = False
# does pump rise an alarm
side_alarm = False
buffer_alarm = False
top_alarm = False
LL_alarm = False

alarm_sent = False
c_1st_ch_1st = False #channels are read alternately
T_in = float("nan")
T_out = float("nan")
W_flow = float("nan")
discard_ard_war = False #discard warning by user
#data initialisation for data saving purposes
power1 = 0
freq1 = 0
freq2 = 0
side_T = None
LL_T = None
top_T = None
buffer_T = None
#delays for orderly data aquisition and savig
pump_delay = 0
save_delay = 0
# GUI related
pump1_com_id_old = None
pump2_com_id_old = None
pump1_ser = None
pump2_ser = None
pump1_ser_old = None
pump2_ser_old = None
pump1_starting = False
pump2_starting = False
cryo1_ser = None
cryo1_ser_old = None
cryo1_com_id_old = None
cryo1_1st_ch = False
cryo1_2nd_ch = False
cryo2_ser = None
cryo2_ser_old = None
cryo2_com_id_old = None
# cryo pump has two channels; one or two may be active
cryo2_1st_ch = False
cryo2_2nd_ch = False

ser = None # arduino serial port
n_ard = None # no arduino warnign window

water_window = None #water setpoint window

time_old = datetime.date(datetime.datetime.now().year, datetime.datetime.now().month, datetime.datetime.now().day)

time_list = []
water_list = []
temp1_list = []
temp2_list = []

values = [0,0,0] #data initialisation of water data

#main window dimensions
size_x = 285
size_y = 260+50+55

count = datetime.datetime.now().time().strftime("%H:%M:%S") #datastamp of the saved data

#current day file creation
now = datetime.datetime.now()
dd = now.day
mm = now.month
yy = now.year
year_t = str(yy)
if dd<10: day_t = '0'+str(dd)
else: day_t = str(dd)
if mm<10: month_t = '0'+str(mm)
else: month_t = str(mm)
current_date = year_t+'_'+month_t+'_'+day_t+'.txt'

currentDirectory = os.path.dirname(os.path.realpath(__file__))+'\\PM_GM1_data'
saveDirectory = os.path.join(currentDirectory, current_date)  

data_path = getattr(sys, '_MEIPASS', os.getcwd())

if not os.path.exists(currentDirectory):
    os.makedirs(currentDirectory)
if not os.path.exists(saveDirectory):
    f = open(saveDirectory,'w')
    f.write('Time\t\tT_in\tT_out\tWater\tLL pump\tLL VA\tC side\tC top\tC buff\tC load lock\n[hh:mm:ss]\t[°C]\t[°C]\t[l/min]\t[RPS]\t[VA]\t[K]\t[K]\t[K]\t[K]\n')
    #f.write('Time\t\tT_in\tT_out\tWater\tLL pump\tPM pump\tLL VA\tPM VA\tC top\tC side\tC buffer\n[hh:mm:ss]\t[°C]\t[°C]\t[l/min]\t[RPS]\t[RPS]\t[VA]\t[VA]\t[K]\t[K]\t[K]\n') #GM2
    f.close()

#look for and connect to Arduino
arduino_ports = [
    p.device
    for p in serial.tools.list_ports.comports()
    if 'Arduino' in p.description
]
if len(arduino_ports)!= 0:
    ser = serial.Serial(arduino_ports[0], 9600)
    water_flow_value = float("nan")
    plugged = True
else:
    water_flow_value = float("nan")
    plugged = False

# IDs fo GUI
APP_EXIT = 1
ID_PLOT = 2
ID_WATER = 3
ID_INFO = 4
ID_TURBO = 5
ID_P1 = 6
ID_P2 = 7
ID_P1_COM_CHANGE = 8
ID_P2_COM_CHANGE = 9
ID_PLOT_SETUP = 10
ID_T_C = 11
ID_P_C = 12
ID_CRYO = 13
ID_C1_COM_CHANGE = 14
ID_C1 = 15
ID_C2 = 16
ID_C2_COM_CHANGE = 17
ID_ALARM = 18

# Main winodow GUI. Commented out code snippets are left for when (if) new pumps are installed in available slots.
class main_window(wx.Frame):
  
    def __init__(self, parent, title):
        super(main_window, self).__init__(parent, title = title, size = (size_x, size_y))
          
        self.InitUI()    
        self.Centre()
        self.Show()    
        
    def InitUI(self):
        self.cell_size = (70,20)
        
        self.menubar = wx.MenuBar()
        self.fileMenu = wx.Menu()
        
        self.set_water = wx.MenuItem(self.fileMenu, ID_WATER, '&Set alarm setpoint\tCtrl+W')
        self.Bind(wx.EVT_MENU, self.SetWater, id = ID_WATER)
        self.dis_en_alarm = wx.MenuItem(self.fileMenu, ID_ALARM, 'Disable cryo pumps alarm')
        self.Bind(wx.EVT_MENU, self.AlarmControl, id = ID_ALARM)
        
        self.qmi = wx.MenuItem(self.fileMenu, APP_EXIT, '&Quit\tCtrl+Q')
        self.Bind(wx.EVT_MENU, self.OnQuit, id = APP_EXIT)
        
        self.fileMenu.Append(self.set_water)
        self.fileMenu.Append(self.dis_en_alarm)
        self.fileMenu.AppendSeparator()
        self.fileMenu.Append(self.qmi)
        
        self.turbo_menu = wx.Menu(ID_TURBO)
        
        
        self.pump1_COM = wx.Menu(ID_P1)
#         self.pump2_COM = wx.Menu(ID_P2)
        self.cryo1_COM = wx.Menu(ID_C1)
        self.cryo2_COM = wx.Menu(ID_C2)
        
        ports = ['COM%s' % (i + 1) for i in range(256)]

        self.com_ports = ['None']
        for port in ports:
            try:
                s = serial.Serial(port)
                s.close()
                self.com_ports.append(port)
            except (OSError, serial.SerialException):
                pass
        del ports
        
        self.pump1_com_id_list = []
        for com_port in self.com_ports:
            new_item = wx.MenuItem(self.turbo_menu, wx.NewId(), com_port, kind = wx.ITEM_RADIO)
            new_id = self.pump1_COM.Append(new_item)
            self.Bind(wx.EVT_MENU, self.p1_connect_COM, new_item)    
            self.pump1_com_id_list.append(new_id.GetId())
            
#         self.pump2_com_id_list = []
#         for com_port in self.com_ports:
#             new_item = wx.MenuItem(self.turbo_menu, wx.NewId(), com_port, kind = wx.ITEM_RADIO)
#             new_id = self.pump2_COM.Append(new_item)
#             self.Bind(wx.EVT_MENU, self.p2_connect_COM, new_item)    
#             self.pump2_com_id_list.append(new_id.GetId())
            
        self.p1_COM_dis_en = wx.MenuItem(self.turbo_menu, ID_P1_COM_CHANGE, 'Disable COM change: LL pump')
        self.Bind(wx.EVT_MENU, self.P1_COM_change, id = ID_P1_COM_CHANGE)
#         self.p2_COM_dis_en = wx.MenuItem(self.turbo_menu, ID_P2_COM_CHANGE, 'Disable COM change: PM pump')
#         self.Bind(wx.EVT_MENU, self.P2_COM_change, id = ID_P2_COM_CHANGE)
        
        self.turbo_menu.Append(ID_P1, 'LL pump: None', self.pump1_COM)
#         self.turbo_menu.Append(ID_P2, 'PM pump: None', self.pump2_COM)
        self.turbo_menu.AppendSeparator()
        self.turbo_menu.Append(self.p1_COM_dis_en)
#         self.turbo_menu.Append(self.p2_COM_dis_en)
        self.pump1_COM.Check(self.pump1_com_id_list[0], True)
#         self.pump2_COM.Check(self.pump2_com_id_list[0], True)
        
        self.cryo_menu = wx.Menu(ID_CRYO)
        
        self.cryo1_com_id_list = []
        for com_port in self.com_ports:
            new_item = wx.MenuItem(self.cryo_menu, wx.NewId(), com_port, kind = wx.ITEM_RADIO)
            new_id = self.cryo1_COM.Append(new_item)
            self.Bind(wx.EVT_MENU, self.c1_connect_COM, new_item)    
            self.cryo1_com_id_list.append(new_id.GetId())
            
        self.cryo2_com_id_list = []
        for com_port in self.com_ports:
            new_item = wx.MenuItem(self.cryo_menu, wx.NewId(), com_port, kind = wx.ITEM_RADIO)
            new_id = self.cryo2_COM.Append(new_item)
            self.Bind(wx.EVT_MENU, self.c2_connect_COM, new_item)    
            self.cryo2_com_id_list.append(new_id.GetId())
            
        self.c1_COM_dis_en = wx.MenuItem(self.cryo_menu, ID_C1_COM_CHANGE, 'Disable COM change: Top/Side pump')
        self.c2_COM_dis_en = wx.MenuItem(self.cryo_menu, ID_C2_COM_CHANGE, 'Disable COM change: Buffer/Load Lock pump')
        self.Bind(wx.EVT_MENU, self.C1_COM_change, id = ID_C1_COM_CHANGE)
        self.Bind(wx.EVT_MENU, self.C2_COM_change, id = ID_C2_COM_CHANGE)    
        
        self.cryo_menu.Append(ID_C1, 'Side/top pump: None', self.cryo1_COM)
        self.cryo_menu.Append(ID_C2, 'Buffer/Load Lock pump: None', self.cryo2_COM)
        self.cryo_menu.AppendSeparator()
        self.cryo_menu.Append(self.c1_COM_dis_en)       
        self.cryo_menu.Append(self.c2_COM_dis_en)
        self.cryo1_COM.Check(self.cryo1_com_id_list[0], True)
        self.cryo2_COM.Check(self.cryo2_com_id_list[0], True)
        
        self.info_menu = wx.Menu(ID_INFO)
        
        self.menubar.Append(self.fileMenu, '&Menu')
        self.menubar.Append(self.turbo_menu, '&Turbo setup')
        self.menubar.Append(self.cryo_menu, '&Cryo setup')
        self.menubar.Append(self.info_menu, '&Info')
        
        self.Bind(wx.EVT_MENU_OPEN, self.menuAction)

        self.SetMenuBar(self.menubar)
        
        self.main_panel = wx.Panel(self)
        self.main_panel.SetBackgroundColour('#ffffff')
        outer_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer = wx.FlexGridSizer(5, 2, 10, 10)
        
        text_font = wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.NORMAL, wx.BOLD)
        unit_font = wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.NORMAL, wx.NORMAL)
        number_font = wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.NORMAL, wx.NORMAL) 
        small_font = wx.Font(6, wx.FONTFAMILY_DEFAULT, wx.NORMAL, wx.BOLD)     
        
        self.T1_value = wx.StaticText(self.main_panel, label = 'None', style = wx.ST_NO_AUTORESIZE|wx.ALIGN_CENTER, size = self.cell_size)
        self.T2_value = wx.StaticText(self.main_panel, label = 'None', style = wx.ST_NO_AUTORESIZE|wx.ALIGN_CENTER, size = self.cell_size)
        self.water_value = wx.StaticText(self.main_panel, label = 'None', style = wx.ST_NO_AUTORESIZE|wx.ALIGN_CENTER, size = self.cell_size)
        self.water_setpoint_value = wx.StaticText(self.main_panel, label = "None", style = wx.ST_NO_AUTORESIZE|wx.ALIGN_CENTER, size = self.cell_size)
        self.cryo1_T_value = wx.StaticText(self.main_panel, label = 'None', style = wx.ST_NO_AUTORESIZE|wx.ALIGN_CENTER, size = self.cell_size)
        self.cryo2_T_value = wx.StaticText(self.main_panel, label = 'None', style = wx.ST_NO_AUTORESIZE|wx.ALIGN_CENTER, size = self.cell_size)
        self.cryo3_T_value = wx.StaticText(self.main_panel, label = 'None', style = wx.ST_NO_AUTORESIZE|wx.ALIGN_CENTER, size = self.cell_size)
        self.cryo4_T_value = wx.StaticText(self.main_panel, label = 'None', style = wx.ST_NO_AUTORESIZE|wx.ALIGN_CENTER, size = self.cell_size)
        
        self.temp1_unit = wx.StaticText(self.main_panel, label = ' °C', size = (40,15))
        self.temp2_unit = wx.StaticText(self.main_panel, label = ' °C', size = (40,15))
        self.water_unit = wx.StaticText(self.main_panel, label = ' l/min', size = (40,15))
        self.water_setpoint_unit = wx.StaticText(self.main_panel, label = ' l/min', size = (40,15))
        self.cryo1_temp_unit = wx.StaticText(self.main_panel, label = ' K', size = (40,15))
        self.cryo2_temp_unit = wx.StaticText(self.main_panel, label = ' K', size = (40,15))
        self.cryo3_temp_unit = wx.StaticText(self.main_panel, label = ' K', size = (40,15))
        self.cryo4_temp_unit = wx.StaticText(self.main_panel, label = ' K', size = (40,15))
        
        self.T1_text = wx.StaticBox(self.main_panel, label = "Temperature In")
        self.T1_text_sizer = wx.StaticBoxSizer(self.T1_text, wx.HORIZONTAL)
        self.T1_text_sizer.Add(self.T1_value)
        self.T1_text_sizer.Add(self.temp1_unit, flag = wx.TOP, border = 4)
        
        self.T2_text = wx.StaticBox(self.main_panel, label = "Temperature Out")
        self.T2_text_sizer = wx.StaticBoxSizer(self.T2_text, wx.HORIZONTAL)
        self.T2_text_sizer.Add(self.T2_value)
        self.T2_text_sizer.Add(self.temp2_unit, flag = wx.TOP, border = 4)
        
        self.water_text = wx.StaticBox(self.main_panel, label = "Water flow")
        self.water_text_sizer = wx.StaticBoxSizer(self.water_text, wx.HORIZONTAL)
        self.water_text_sizer.Add(self.water_value)
        self.water_text_sizer.Add(self.water_unit, flag = wx.TOP, border = 4)
        
        self.water_setpoint_text = wx.StaticBox(self.main_panel, label = "Alarm setpoint")
        self.water_setpoint_text_sizer = wx.StaticBoxSizer(self.water_setpoint_text, wx.HORIZONTAL)
        self.water_setpoint_text_sizer.Add(self.water_setpoint_value)
        self.water_setpoint_text_sizer.Add(self.water_setpoint_unit, flag = wx.TOP, border = 4)
        
        self.pump1_text = wx.StaticBox(self.main_panel, label = "LL pump (None)", size = self.cell_size)
        self.pump1_text_sizer = wx.StaticBoxSizer(self.pump1_text, wx.VERTICAL)
        self.progres1_sizer = wx.GridBagSizer(0, 0)
        self.pump1_value = wx.StaticText(self.pump1_text, label = 'None', style = wx.ST_NO_AUTORESIZE|wx.ALIGN_CENTER, size = self.cell_size)
        self.pump1_unit = wx.StaticText(self.pump1_text, label = ' RPS', size = (40,15))
        self.progress1_value = wx.StaticText(self.pump1_text, label = '0%', style = wx.ST_NO_AUTORESIZE|wx.ALIGN_CENTER,size = (40,15))
        self.p1_power_vlue = wx.StaticText(self.pump1_text, label = '0'+' VA', size = (40,8), style = wx.ALIGN_RIGHT)
        self.progres1_sizer.Add(self.p1_power_vlue,pos = (0, 0), span = (0,2), flag = wx.ALIGN_RIGHT|wx.RIGHT, border = 8)
        self.progres1_sizer.Add(self.pump1_value,pos = (1, 0))
        self.progres1_sizer.Add(self.pump1_unit,pos = (1, 1), flag = wx.TOP, border = 2)
        self.pump_percent1 = wx.Gauge(self.pump1_text, range = 980, size = (self.cell_size[0],10), style = wx.GA_HORIZONTAL|wx.GA_SMOOTH)
        self.progres1_sizer.Add(self.pump_percent1, pos = (2, 0), flag = wx.ALIGN_CENTER)
        self.progres1_sizer.Add(self.progress1_value, pos = (2, 1), flag = wx.ALIGN_CENTER)
        self.pump1_text_sizer.Add(self.progres1_sizer)
         
        self.pump2_text = wx.StaticBox(self.main_panel, label = "PM pump (None)", size = self.cell_size)
        self.pump2_text_sizer = wx.StaticBoxSizer(self.pump2_text, wx.VERTICAL)
        self.progres2_sizer = wx.GridBagSizer(0, 0)
        self.pump2_value = wx.StaticText(self.pump2_text, label = 'None', style = wx.ST_NO_AUTORESIZE|wx.ALIGN_CENTER, size = self.cell_size)
        self.pump2_unit = wx.StaticText(self.pump2_text, label = ' RPS', size = (40,15))
        self.progress2_value = wx.StaticText(self.pump2_text, label = '0%', style = wx.ST_NO_AUTORESIZE|wx.ALIGN_CENTER,size = (40,15))
        self.p2_power_vlue = wx.StaticText(self.pump2_text, label = '0'+' VA', size = (40,8), style = wx.ALIGN_RIGHT)
        self.progres2_sizer.Add(self.p2_power_vlue,pos = (0, 0), span = (0,2), flag = wx.ALIGN_RIGHT|wx.RIGHT, border = 8)
        self.progres2_sizer.Add(self.pump2_value,pos = (1, 0))
        self.progres2_sizer.Add(self.pump2_unit,pos = (1, 1), flag = wx.TOP, border = 2)
        self.pump_percent2 = wx.Gauge(self.pump2_text, range = 980, size = (self.cell_size[0],10), style = wx.GA_HORIZONTAL|wx.GA_SMOOTH)
        self.progres2_sizer.Add(self.pump_percent2, pos = (2, 0), flag = wx.ALIGN_CENTER)
        self.progres2_sizer.Add(self.progress2_value, pos = (2, 1), flag = wx.ALIGN_CENTER)
        self.pump2_text_sizer.Add(self.progres2_sizer)
        
        self.cryo1_T_text = wx.StaticBox(self.main_panel, label = "Side (None)")
        self.cryo1_T_text_sizer = wx.StaticBoxSizer(self.cryo1_T_text, wx.HORIZONTAL)
        self.cryo1_T_text_sizer.Add(self.cryo1_T_value)
        self.cryo1_T_text_sizer.Add(self.cryo1_temp_unit, flag = wx.TOP, border = 4)
        
        self.cryo2_T_text = wx.StaticBox(self.main_panel, label = "Top (None)")
        self.cryo2_T_text_sizer = wx.StaticBoxSizer(self.cryo2_T_text, wx.HORIZONTAL)
        self.cryo2_T_text_sizer.Add(self.cryo2_T_value)
        self.cryo2_T_text_sizer.Add(self.cryo2_temp_unit, flag = wx.TOP, border = 4)
        
        self.cryo3_T_text = wx.StaticBox(self.main_panel, label = "Load Lock (None)")
        self.cryo3_T_text_sizer = wx.StaticBoxSizer(self.cryo3_T_text, wx.HORIZONTAL)
        self.cryo3_T_text_sizer.Add(self.cryo3_T_value)
        self.cryo3_T_text_sizer.Add(self.cryo3_temp_unit, flag = wx.TOP, border = 4)
        
        self.cryo4_T_text = wx.StaticBox(self.main_panel, label = "Buffer (None)")
        self.cryo4_T_text_sizer = wx.StaticBoxSizer(self.cryo4_T_text, wx.HORIZONTAL)
        self.cryo4_T_text_sizer.Add(self.cryo4_T_value)
        self.cryo4_T_text_sizer.Add(self.cryo4_temp_unit, flag = wx.TOP, border = 4)
        
        self.cryo1_T_value.SetLabel(str(side_T))
        self.cryo2_T_value.SetLabel(str(top_T))
        self.cryo3_T_value.SetLabel(str(LL_T))
        self.cryo4_T_value.SetLabel(str(buffer_T))
         
        self.pump2_value.Hide()
        self.pump2_text.Hide()
        self.pump2_unit.Hide()
         
        self.T1_text.SetFont(text_font)
        self.T2_text.SetFont(text_font)
        self.water_text.SetFont(text_font)
        self.water_setpoint_text.SetFont(text_font)
        self.pump1_text.SetFont(text_font)
        self.pump2_text.SetFont(text_font)
        self.cryo1_T_text.SetFont(text_font)
        self.cryo2_T_text.SetFont(text_font)
        self.cryo3_T_text.SetFont(text_font)
        self.cryo4_T_text.SetFont(text_font)
        
        self.temp1_unit.SetFont(unit_font)
        self.temp2_unit.SetFont(unit_font)
        self.water_unit.SetFont(unit_font)
        self.water_setpoint_unit.SetFont(unit_font)
        self.pump1_unit.SetFont(unit_font)
        self.pump2_unit.SetFont(unit_font)
        self.cryo1_temp_unit.SetFont(unit_font)
        self.cryo2_temp_unit.SetFont(unit_font)
        self.cryo3_temp_unit.SetFont(unit_font)
        self.cryo4_temp_unit.SetFont(unit_font)
        
        self.T1_value.SetFont(number_font)
        self.T2_value.SetFont(number_font)
        self.water_value.SetFont(number_font)
        self.water_setpoint_value.SetFont(number_font)
        self.pump1_value.SetFont(number_font)
        self.pump2_value.SetFont(number_font)
        self.cryo1_T_value.SetFont(number_font)
        self.cryo2_T_value.SetFont(number_font)
        self.cryo3_T_value.SetFont(number_font)
        self.cryo4_T_value.SetFont(number_font)
        
        self.p1_power_vlue.SetFont(small_font)
        self.p2_power_vlue.SetFont(small_font)
        
        main_sizer.Add(self.water_text_sizer)
        main_sizer.Add(self.water_setpoint_text_sizer)
        main_sizer.Add(self.T1_text_sizer)
        main_sizer.Add(self.T2_text_sizer)
        main_sizer.Add(self.pump1_text_sizer)
        main_sizer.Add(self.pump2_text_sizer)
        main_sizer.Add(self.cryo1_T_text_sizer)
        main_sizer.Add(self.cryo3_T_text_sizer)
        main_sizer.Add(self.cryo2_T_text_sizer)
        main_sizer.Add(self.cryo4_T_text_sizer)
        
        outer_sizer.Add(main_sizer, flag = wx.ALL, border = 10)
        
        self.main_panel.SetSizer(outer_sizer)
        
        os.chdir(data_path)
        ico = wx.Icon('ikona2.ico', wx.BITMAP_TYPE_ICO)
        self.SetIcon(ico)
          
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnTimer, self.timer)
        self.timer.Start(500)

        self.Bind(wx.EVT_CLOSE, self.CloseSelf)
        
        self.SetMinSize((size_x, size_y))
        self.SetMaxSize((size_x, size_y))
        
        self.test_time2 = datetime.datetime.now() 
    
    def AlarmControl(self, event):
        if alarm_enabled:
            alarm_enabled = False
            self.dis_en_alarm.SetItemLabel('Enable cryo pumps alarm')
            if alarm_sent and side_alarm or buffer_alarm or top_alarm or LL_alarm:
                stop_alarm = '$A0'
                stop_alarm_b = stop_alarm.encode()
                ser.write(stop_alarm_b)
                alarm_sent = False       
        else:
            alarm_enabled = True
            self.dis_en_alarm.SetItemLabel('Disable cryo pumps alarm') 
        
    def P1_COM_change(self, event):
        to_find = 'Disable'
        com_str = self.p1_COM_dis_en.GetItemLabel().find(to_find, 0, 7)
        if com_str<0:
            self.turbo_menu.Enable(ID_P1,True)
            self.p1_COM_dis_en.SetItemLabel('Disable COM change: LL pump')
        else:
            self.turbo_menu.Enable(ID_P1,False)
            self.p1_COM_dis_en.SetItemLabel('Enable COM change: LL pump') 
            
#     def P2_COM_change(self, event):
#         to_find = 'Disable'
#         com_str = self.p2_COM_dis_en.GetItemLabel().find(to_find, 0, 7)
#         if com_str<0:
#             self.turbo_menu.Enable(ID_P2,True)
#             self.p2_COM_dis_en.SetItemLabel('Disable COM change: LL pump')
#         else:
#             self.turbo_menu.Enable(ID_P2,False)
#             self.p2_COM_dis_en.SetItemLabel('Enable COM change: LL pump') 
    
    def C1_COM_change(self, event):
        to_find = 'Disable'
        com_str = self.c1_COM_dis_en.GetItemLabel().find(to_find, 0, 7)
        if com_str<0:
            self.cryo_menu.Enable(ID_C1,True)
            self.c1_COM_dis_en.SetItemLabel('Disable COM change: Top/Side pump')
        else:
            self.cryo_menu.Enable(ID_C1,False)
            self.c1_COM_dis_en.SetItemLabel('Enable COM change: Top/Side pump') 
            
    def C2_COM_change(self, event):
        to_find = 'Disable'
        com_str = self.c2_COM_dis_en.GetItemLabel().find(to_find, 0, 7)
        if com_str<0:
            self.cryo_menu.Enable(ID_C2,True)
            self.c2_COM_dis_en.SetItemLabel('Disable COM change: Buffer/Load Lock pump')
        else:
            self.cryo_menu.Enable(ID_C2,False)
            self.c2_COM_dis_en.SetItemLabel('Enable COM change: Buffer/Load Lock pump')
    
    def p1_connect_COM(self, event):
        position = self.pump1_com_id_list.index(event.GetId())
        p1_COM = self.com_ports[position]
        if p1_COM == "None":
            pump1_ser.close()
            pump1_ser = None
            pump1_ser_old = None
            if pump1_com_id_old: 
                self.cryo1_COM.Enable(self.cryo1_com_id_list[self.pump1_com_id_list.index(pump1_com_id_old)], True)
                self.cryo2_COM.Enable(self.cryo2_com_id_list[self.pump1_com_id_list.index(pump1_com_id_old)], True)
            pump1_com_id_old = None
            self.pump1_text.SetLabel('LL pump ('+p1_COM+')')
            warning_message = 'LL pump disconnected.'
            dlg = wx.MessageBox(warning_message, 'Information', wx.OK) 
        else:
            try:
                if pump1_ser: pump1_ser.close()
                pump1_ser = serial.Serial(p1_COM, 19200, 
                            parity = serial.PARITY_EVEN, 
                            stopbits = serial.STOPBITS_ONE,
                            bytesize = serial.EIGHTBITS)
                question = bytes([2,22,0,0,0,0,0,0,0,0,0,0,0,3,212,0,0,0,0,0,0,0,0,195])
                pump1_ser.write(question)
                time.sleep(0.2)
                if pump1_ser.in_waiting == 0:
                    if not pump1_com_id_old: self.turbo_menu.Check(self.pump1_com_id_list[0], True)
                    else: self.turbo_menu.Check(pump1_com_id_old, True)
                    warning_message = 'No pump found'
                    dlg = wx.MessageBox(warning_message, 'Information', wx.OK)   
                    pump1_ser.close()
                    pump1_ser = pump1_ser_old
                elif pump1_ser.in_waiting>0:
                    pump1_ser_old = pump1_ser
                    if pump1_com_id_old: 
                        self.pump2_COM.Enable(self.pump2_com_id_list[self.pump1_com_id_list.index(pump1_com_id_old)], True)
                        self.cryo1_COM.Enable(self.cryo1_com_id_list[self.pump1_com_id_list.index(pump1_com_id_old)], True)
                    pump1_com_id_old = event.GetId()
                    self.turbo_menu.SetLabel(ID_P1, 'LL pump: '+p1_COM)
                    self.pump1_text.SetLabel('LL pump ('+p1_COM+')')
                    self.cryo1_COM.Enable(self.cryo1_com_id_list[position], False)
                    self.cryo2_COM.Enable(self.cryo2_com_id_list[position], False)
                
            except (OSError, serial.SerialException):
                if pump1_ser: pump1_ser.close()
                pump1_ser = None
                self.turbo_menu.SetLabel(ID_P1, 'LL pump: '+self.com_ports[0])
                self.turbo_menu.Check(self.pump1_com_id_list[0], True)
                warning_message = 'This COM is occupied!'
                dlg = wx.MessageBox(warning_message, 'Information', wx.OK)
                pass
           
    def c1_connect_COM(self, event):
        position = self.cryo1_com_id_list.index(event.GetId())
        c1_COM = self.com_ports[position]
        if c1_COM == "None":
            cryo1_ser.reset_input_buffer()
            cryo1_ser.reset_output_buffer()
            cryo1_ser.close()
            cryo1_ser = None
            cryo1_ser_old = None
            if cryo1_com_id_old: 
                self.pump1_COM.Enable(self.pump1_com_id_list[self.cryo1_com_id_list.index(cryo1_com_id_old)], True)
                self.cryo2_COM.Enable(self.cryo2_com_id_list[self.cryo1_com_id_list.index(cryo1_com_id_old)], True)
            cryo1_com_id_old = None
            cryo1_1st_ch = False
            cryo1_2nd_ch = False
            self.cryo1_T_text.SetLabel('Side ('+c1_COM+')')
            self.cryo2_T_text.SetLabel('Top ('+c1_COM+')')
            self.cryo_menu.SetLabel(ID_C1, 'Side/Top pump: None')
            self.cryo2_T_value.SetLabel('None')
            self.cryo1_T_value.SetLabel('None')
            warning_message = 'Top/Side cryo pump disconnected.'
            dlg = wx.MessageBox(warning_message, 'Information', wx.OK) 
        else:
            try:
                if cryo1_ser: cryo1_ser.close()
                cryo1_ser = serial.Serial(c1_COM, 19200, 
                            parity = serial.PARITY_NONE, 
                            stopbits = serial.STOPBITS_ONE,
                            bytesize = serial.EIGHTBITS)
                comm = '$GetTemp 1'
                c1_question = comm.encode()+bytes([13,10])
                cryo1_ser.write(c1_question)
                time.sleep(0.2)
                if cryo1_ser.in_waiting>0:
                    c1_temp2 = str(cryo1_ser.readline())
                    if c1_temp2[3:len(c1_temp2)-5]!= 'OOR':
                        cryo1_1st_ch = True
                    cryo1_ser.reset_input_buffer()
                time.sleep(0.2)
                
                comm = '$GetTemp 2'
                c1_question = comm.encode()+bytes([13,10])
                cryo1_ser.write(c1_question)
                time.sleep(0.2)
                if cryo1_ser.in_waiting>0:
                    c1_temp1 = str(cryo1_ser.readline())
                    if c1_temp1[3:len(c1_temp1)-5]!= 'OOR':
                        cryo1_2nd_ch = True
                if cryo1_1st_ch == True: 
                    comm = '$GetTemp 1'
                    c1_question = comm.encode()+bytes([13,10])
                    cryo1_ser.reset_input_buffer()
                    time.sleep(0.2)
                    cryo1_ser.write(c1_question)
                elif cryo1_2nd_ch == True:
                    comm = '$GetTemp 2'
                    c1_question = comm.encode()+bytes([13,10])
                    cryo1_ser.reset_input_buffer()
                    time.sleep(0.2)
                    cryo1_ser.write(c1_question)
                
                if cryo1_ser.in_waiting == 0 and not cryo1_1st_ch:
                    if not cryo1_com_id_old: self.cryo_menu.Check(self.cryo1_com_id_list[0], True)
                    else: self.cryo_menu.Check(cryo1_com_id_old, True)
                    warning_message = 'No cryo pump found'
                    dlg = wx.MessageBox(warning_message, 'Information', wx.OK)   
                    cryo1_ser.close()
                    cryo1_ser = cryo1_ser_old
                elif cryo1_1st_ch or cryo1_2nd_ch:
                    if cryo1_com_id_old: 
                        self.cryo2_COM.Enable(self.cryo2_com_id_list[self.cryo1_com_id_list.index(cryo1_com_id_old)], True)
                        self.pump1_COM.Enable(self.pump1_com_id_list[self.cryo1_com_id_list.index(cryo1_com_id_old)], True)
                    cryo1_ser_old = cryo1_ser
                    cryo1_com_id_old = event.GetId()
                    self.cryo_menu.SetLabel(ID_C1, 'Side/Top pump: '+c1_COM)
                    if cryo1_1st_ch: self.cryo1_T_text.SetLabel('Side ('+c1_COM+')')
                    if cryo1_2nd_ch: self.cryo2_T_text.SetLabel('Top ('+c1_COM+')')
                    self.cryo2_COM.Enable(self.cryo2_com_id_list[position], False)
                    self.pump1_COM.Enable(self.pump1_com_id_list[position], False)
                
            except (OSError, serial.SerialException):
                self.cryo_menu.SetLabel(ID_C1, 'Top/Side: '+self.com_ports[0])
                self.cryo_menu.Check(self.cryo1_com_id_list[0], True)
                warning_message = 'This COM is occupied!'
                dlg = wx.MessageBox(warning_message, 'Information', wx.OK)
                pass
    
    def c2_connect_COM(self, event):
        global cryo2_ser, cryo2_ser_old, cryo2_com_id_old, cryo2_1st_ch, cryo2_2nd_ch
        position = self.cryo2_com_id_list.index(event.GetId())
        c2_COM = self.com_ports[position]
        if c2_COM == "None":
            cryo2_ser.reset_input_buffer()
            cryo2_ser.reset_output_buffer()
            cryo2_ser.close()
            cryo2_ser = None
            cryo2_ser_old = None
            if cryo2_com_id_old: 
                self.pump1_COM.Enable(self.pump1_com_id_list[self.cryo2_com_id_list.index(cryo2_com_id_old)], True)
                self.cryo1_COM.Enable(self.cryo1_com_id_list[self.cryo2_com_id_list.index(cryo2_com_id_old)], True)
            cryo2_com_id_old = None
            cryo2_1st_ch = False
            cryo2_2nd_ch = False
            self.cryo3_text.SetLabel('LL ('+c2_COM+')')
            self.cryo4_T_text.SetLabel('Buffer ('+c2_COM+')')
            self.cryo_menu.SetLabel(ID_C2, 'Buffer/Load Lock pump: None')
            self.cryo3_T_value.SetLabel('None')
            self.cryo4_T_value.SetLabel('None')
            warning_message = 'Buffer/Load Lock cryo pump disconnected.'
            dlg = wx.MessageBox(warning_message, 'Information', wx.OK) 
        else:
            try:
                if cryo2_ser: cryo2_ser.close()
                cryo2_ser = serial.Serial(c2_COM, 19200, 
                            parity = serial.PARITY_NONE, 
                            stopbits = serial.STOPBITS_ONE,
                            bytesize = serial.EIGHTBITS)
                comm = '$GetTemp 2'
                c2_question = comm.encode()+bytes([13,10])
                cryo2_ser.write(c2_question)
                time.sleep(0.2)
                if cryo2_ser.in_waiting>0:
                    c2_temp2 = str(cryo2_ser.readline())
                    if c2_temp2[3:len(c2_temp2)-5]!= 'OOR':
                        cryo2_2nd_ch = True
                        cryo2_ser.write(c2_question)
                        time.sleep(0.2)
                comm = '$GetTemp 1'
                c2_question = comm.encode()+bytes([13,10])
                cryo2_ser.write(c2_question)
                time.sleep(0.2)
                if cryo2_ser.in_waiting>0:
                    c2_temp1 = str(cryo2_ser.readline())
                    if c2_temp1[3:len(c2_temp1)-5]!= 'OOR':
                        cryo2_1st_ch = True
                
                if cryo2_ser.in_waiting == 0:
                    if not cryo2_com_id_old: self.cryo_menu.Check(self.cryo2_com_id_list[0], True)
                    else: self.cryo_menu.Check(cryo2_com_id_old, True)
                    warning_message = 'No cryo pump found'
                    dlg = wx.MessageBox(warning_message, 'Information', wx.OK)   
                    cryo2_ser.close()
                    cryo2_ser = cryo2_ser_old
                elif cryo2_2nd_ch or cryo2_1st_ch:
                    if cryo2_com_id_old: 
                        self.cryo1_COM.Enable(self.cryo1_com_id_list[self.cryo2_com_id_list.index(cryo2_com_id_old)], True)
                        self.pump1_COM.Enable(self.pump1_com_id_list[self.pump1_com_id_list.index(cryo2_com_id_old)], True)
                    cryo2_ser_old = cryo2_ser
                    cryo2_com_id_old = event.GetId()
                    self.cryo_menu.SetLabel(ID_C2, 'Buffer pump: '+c2_COM)
                    if cryo2_2nd_ch:self.cryo3_T_text.SetLabel('Load Lock ('+c2_COM+')')
                    if cryo2_2nd_ch:self.cryo4_T_text.SetLabel('Buffer ('+c2_COM+')')
                    self.cryo1_COM.Enable(self.cryo1_com_id_list[position], False)
                    self.pump1_COM.Enable(self.pump1_com_id_list[position], False)
                    
            except (OSError, serial.SerialException):
                self.cryo_menu.SetLabel(ID_C2, 'Buffer/Load Lock: '+self.com_ports[0])
                self.cryo_menu.Check(self.cryo2_com_id_list[0], True)
                warning_message = 'This COM is occupied!'
                dlg = wx.MessageBox(warning_message, 'Information', wx.OK)
                pass    
        
    def CloseSelf(self, event):
        warning_message = "Are you sure you want to exit?"
        dlg = wx.MessageBox(warning_message, 'Confirmation', wx.YES_NO)
        if dlg  ==  wx.YES:
            if ser: ser.close()
            if pump1_ser: pump1_ser.close()
            if pump2_ser: pump2_ser.close()
            if cryo1_ser: cryo1_ser.close()
            if cryo2_ser: cryo2_ser.close()
            if water_window: water_window.Destroy()
            self.Destroy()
        
    def OnQuit(self, event):
        self.CloseSelf(event)
    
    def menuAction(self, event):
        if event.GetMenu() == self.info_menu:
            self.infoWindow(event)
            
    def infoWindow(self, event):
            info_window(main_frame, title = "Info")
    
    def OnTimer(self,event):
        global plugged, ser, n_ard, pump_delay, save_delay, discard_ard_war, c_1st_ch_1st
        arduino_ports = [
                p.device
                for p in serial.tools.list_ports.comports()
                if 'Arduino' in p.description
                ]
        if arduino_ports == []: 
            plugged = False
            if ser: ser.close()
            self.set_water.Enable(False)
            self.T1_value.SetLabel('None')
            self.T2_value.SetLabel('None')
            self.water_value.SetLabel('None')
            self.water_setpoint_value.SetLabel('None')
            warning_message = "Arduino not detected!"
            if n_ard == None and not discard_ard_war:
                n_ard = wx.GenericMessageDialog(main_frame, warning_message, 'Warning',wx.OK|wx.ICON_ERROR|wx.CANCEL)
                n_ard.SetOKCancelLabels("OK", "Discard warning")
                modal = n_ard.ShowModal()                 
                if modal  ==  wx.ID_OK:
                    n_ard.Destroy()
                    n_ard = None
                elif modal == wx.ID_CANCEL:
                    discard_ard_war = True
                    n_ard.Destroy()
                    n_ard = None
                    
        if plugged == False and len(arduino_ports)!= 0:
            if n_ard: 
                n_ard.Destroy()
                n_ard = None
            discard_ard_war = False
            ser = serial.Serial(arduino_ports[0], 9600)
            plugged = True
            self.set_water.Enable(True)
            
        pump_delay+= 1
        save_delay+= 1
        
        if pump_delay == 2:
            if cryo1_1st_ch or cryo2_1st_ch:self.cyro_side_LL_T()
        elif pump_delay == 3:
            if plugged:
                self.arduino_ask()
        elif pump_delay == 4:
            if pump1_ser: self.pump1_freq()
#             if pump2_ser: self.pump2_freq()
        elif pump_delay == 6:
            if cryo1_2nd_ch or cryo2_2nd_ch:
                if c_1st_ch_1st:self.cyro_top_buffer_T()
        elif pump_delay == 7:
            if plugged:
                if ser.in_waiting>0:
                    self.arduino_collect()
        elif pump_delay == 8:
            if pump1_ser: self.pump1_freq()
#             if pump2_ser: self.pump2_freq()
        elif pump_delay == 10:
            if plugged and alarm_enabled: pump_alarm()
            pump_delay = 0
            
        if save_delay == 20:
            self.save_to_file()
            save_delay = 0
            
    def arduino_ask(self):
        arduino_value = '$G'
        arduino_com = arduino_value.encode()
        ser.write(arduino_com)
        
    def arduino_collect(self):
        global T_in, T_out, W_flow
        values = [0,0,0]
        value = str(str(ser.readline()))
        value = value[2:len(value)-5]
        values = value.split()
        T_in = values[0]
        T_out = values[1]
        W_flow = values[2]
        water_flow_value = float(values[3])/10
        
        self.T1_value.SetLabel(str(T_in))
        self.T2_value.SetLabel(str(T_out))
        self.water_value.SetLabel(str(W_flow))
        self.water_setpoint_value.SetLabel(str(water_flow_value))
        
    def save_to_file(self):
        global time_old, current_date, saveDirectory
        global T_in, T_out, W_flow, count, freq1, side_T, LL_T, top_T, buffer_T
        global power1
        now = datetime.datetime.now()
        time_now = datetime.date(now.year, now.month, now.day)
        
        if time_old<time_now:
            dd = now.day
            mm = now.month
            yy = now.year
            year_t = str(yy)
            if dd<10: day_t = '0'+str(dd)
            else: day_t = str(dd)
            if mm<10: month_t = '0'+str(mm)
            else: month_t = str(mm)
            current_date = year_t+'_'+month_t+'_'+day_t+'.txt'
            
            saveDirectory = os.path.join(currentDirectory, current_date)
            f = open(saveDirectory,'w')
            f.write('Time\t\tT_in\tT_out\tWater\tLL pump\tLL VA\tC side\tC top\tC buff\tC load lock\n[hh:mm:ss]\t[°C]\t[°C]\t[l/min]\t[RPS]\t[VA]\t[K]\t[K]\t[K]\t[K]\n')
            #f.write('Time\t\tT_in\tT_out\tWater\tLL pump\tPM pump\tLL VA\tPM VA\tC top\tC side\tC buffer\n[hh:mm:ss]\t[°C]\t[°C]\t[l/min]\t[RPS]\t[RPS]\t[VA]\t[VA]\t[K]\t[K]\t[K]\n') #GM2
            f.close()
        time_old = time_now

        count = datetime.datetime.now().time().strftime("%H:%M:%S")
        
        if not plugged:
            T_in = float('nan')
            T_out = float('nan')
            W_flow = float('nan')
        if not pump1_ser:
            freq1 = float('nan')    
        if not cryo1_1st_ch: side_T = 'nan'
        if not cryo1_2nd_ch: top_T = 'nan'
        if not cryo2_1st_ch: LL_T = 'nan'
        if not cryo2_2nd_ch: buffer_T = 'nan'
        with open(saveDirectory, "a") as myfile:
            myfile.write(str(count)+'\t'+str(T_in)+'\t'+str(T_out)+'\t'+str(W_flow)+'\t'+str(freq1)+'\t'+str(power1)+'\t'+side_T+'\t'+top_T+'\t'+buffer_T+'\t'+LL_T+'\n')
            #myfile.write(str(count)+'\t'+str(T_in)+'\t'+str(T_out)+'\t'+str(W_flow)+'\t'+str(freq1)+'\t'+str(freq2)+'\t'+str(power1)+'\t'+str(power2)+'\t'+top_T+'\t'+side_T+'\t'+buffer_T+'\n') #GM2
            
        gc.collect()
                  
    def pump1_freq(self):
        global pump1_starting, pump1_ser, freq1, power1
        
        question = bytes([2,22,0,0,0,0,0,0,0,0,0,0,0,3,212,0,0,0,0,0,0,0,0,195])
        if pump1_ser:
            if pump1_ser.in_waiting>23:
                recieved = pump1_ser.read(size = 24)
                freq1 = recieved[13]*256+recieved[14]
                power1 = round((recieved[17]*256+recieved[18])*(recieved[21]*256+recieved[22])/100,2)
            else:
                self.pump1_value.SetLabel('None')
                self.p1_power_vlue.SetLabel(' VA')
                self.pump1_text.SetLabel("LL pump (None)") 
                self.turbo_menu.SetLabel(ID_P1, 'LL pump: None')
                turbo_item_id = self.pump1_COM.FindItem('None')
                self.pump1_COM.Check(turbo_item_id, True)()
                self.cryo1_COM.Enable(self.cryo1_com_id_list[self.pump1_com_id_list.index(turbo_item_id)], True)
                self.cryo2_COM.Enable(self.cryo2_com_id_list[self.pump1_com_id_list.index(turbo_item_id)], True)
                pump1_ser.close()
                pump1_ser = None
                return
            pump1_ser.write(question)
            
        else:
            return
            
        if freq1 == 0:
            self.pump_percent1.Hide()
            self.progress1_value.Hide()
            pump1_starting = True
        elif pump1_starting == True and freq1>0 and freq1<980:
            self.pump_percent1.SetValue(int(freq1))
            self.progress1_value.SetLabel("%s" % round(self.pump_percent1.GetValue()/980*100,2) +'%')
            self.pump_percent1.Show()
            self.progress1_value.Show()
        elif freq1 > 0 and freq1 < 950:
            self.pump_percent1.SetValue(int(freq1))
            self.progress1_value.SetLabel("%s" % round(self.pump_percent1.GetValue()/980*100,2) +'%')
            self.pump_percent1.Show()
            self.progress1_value.Show()   
        elif freq1 >= 980:
            self.pump_percent1.Hide()
            self.progress1_value.Hide()
            pump1_starting = False
            
        
        self.pump1_value.SetLabel(str(freq1))
        self.p1_power_vlue.SetLabel(str(power1)+' VA')
        
#     def pump2_freq(self):
#         global pump2_starting, pump2_ser, freq2
#         power2 = 0
#         question = bytes([2,22,0,0,0,0,0,0,0,0,0,0,0,3,212,0,0,0,0,0,0,0,0,195])
#         if pump2_ser:
#             if pump2_ser.in_waiting>23:
#                 recieved = pump2_ser.read(size = 24)
#                 freq2 = recieved[13]*256+recieved[14]
#                 power2 = round((recieved[17]*256+recieved[18])*(recieved[21]*256+recieved[22])/100,2)
#             else:
#                 return
#             pump2_ser.write(question)
# 
#         if freq2 =  = 0:
#             self.pump_percent2.Hide()
#             self.progress2_value.Hide()
#             pump2_starting = True
#         elif pump2_starting =  = True and freq2>0 and freq2<980:
#             self.pump_percent2.Show()
#             self.progress2_value.Show()
#         elif freq2>0 and freq2<950:
#             self.pump_percent2.Show()
#             self.progress2_value.Show()   
#         elif freq2> = 980:
#             self.pump_percent2.Hide()
#             self.progress2_value.Hide()
#             pump2_starting = False
#             
#         self.pump_percent2.SetValue(freq2)
#         self.progress2_value.SetLabel("%s" % round(self.pump_percent2.GetValue()/980*100,2) +'%')
#         self.pump2_value.SetLabel(str(freq2))
#         self.p2_power_vlue.SetLabel(str(power2)+' VA')

    def cyro_side_LL_T(self):
        c_1st_ch_1st = True
        
        if cryo1_2nd_ch:
            comm = '$GetTemp 2' #channels are read alternately
            question1_side_LL = comm.encode()+bytes([13,10])
        else:
            comm = '$GetTemp 1' #channels are read alternately
            question1_side_LL = comm.encode()+bytes([13,10])
            
        if cryo2_2nd_ch:
            comm = '$GetTemp 2' #channels are read alternatelye
            question2_side_LL = comm.encode()+bytes([13,10])
        else:
            comm = '$GetTemp 1' #channels are read alternately
            question2_side_LL = comm.encode()+bytes([13,10])    
            
        if cryo1_1st_ch:
            if cryo1_ser.in_waiting > 0:
                recieved1 = str(str(cryo1_ser.readline()))
                side_T = recieved1[3:len(recieved1)-5]
            else:
                self.cryo1_T_value.SetLabel('None')
                self.cryo1_T_text.SetLabel("Side pump (None)") 
                self.cryo_menu.SetLabel(ID_C1, 'Side/top pump: None')
                cryo1_item_id = self.cryo1_COM.FindItem('None')
                self.cryo1_COM.Check(cryo1_item_id, True)
                self.pump1_COM.Enable(self.pump1_com_id_list[self.cryo1_com_id_list.index(cryo1_item_id)], True)
                self.cryo2_COM.Enable(self.cryo2_com_id_list[self.cryo1_com_id_list.index(cryo1_item_id)], True)
                if cryo1_ser: cryo1_ser.close()
                cryo1_ser = None
                cryo1_1st_ch = False
                return
            cryo1_ser.write(question1_side_LL)
            
            if float(side_T) < 18:
                if side_font_war:
                    self.cryo1_T_value.SetForegroundColour('#000000')
                    side_font_war = False
            elif float(side_T) > 17.9 and float(side_T)<25.1:
                if not side_font_war:
                    self.cryo1_T_value.SetForegroundColour('#ff5f00')
                    side_font_war = True
            elif float(side_T) > 25:
                if not side_font_war:
                    self.cryo1_T_value.SetForegroundColour('#ff0000')
                    side_font_war = True
                    
            self.cryo1_T_value.SetLabel(side_T)
        if cryo2_1st_ch:
            if cryo2_ser.in_waiting > 0:
                recieved2 = str(cryo2_ser.readline())
                LL_T = recieved2[3:len(recieved2)-5]
            else:
                self.cryo3_T_value.SetLabel('None')
                self.cryo3_T_text.SetLabel("Load Lock pump (None)") 
                self.cryo_menu.SetLabel(ID_C2, 'Buffer/Load Lock pump: None')
                cryo2_item_id = self.cryo2_COM.FindItem('None')
                self.cryo2_COM.Check(cryo2_item_id, True)
                self.pump1_COM.Enable(self.pump1_com_id_list[self.cryo2_com_id_list.index(cryo2_item_id)], True)
                self.cryo1_COM.Enable(self.cryo1_com_id_list[self.cryo2_com_id_list.index(cryo2_item_id)], True)
                if cryo2_ser: cryo2_ser.close()
                cryo2_ser = None
                cryo2_2nd_ch = False
                return   
            
            if float(LL_T) < 18:
                if ll_font_war:
                    self.cryo3_T_value.SetForegroundColour('#000000')
                    ll_font_war = False
            elif float(LL_T) > 17.9 and float(LL_T)<25.1:
                if not side_font_war:
                    self.cryo3_T_value.SetForegroundColour('#ff5f00')
                    ll_font_war = True
            elif float(LL_T) > 25:
                if not side_font_war:
                    self.cryo3_T_value.SetForegroundColour('#ff0000')
                    ll_font_war = True
            cryo2_ser.write(question2_side_LL)
            self.cryo3_T_value.SetLabel(LL_T)
        
    def cyro_top_buffer_T(self):
        c_2nd_ch_1st = True
        
        if cryo1_1st_ch:
            comm = '$GetTemp 1' #channels are read alternately
            question1_TB = comm.encode()+bytes([13,10])
        else:
            comm = '$GetTemp 2' #channels are read alternately
            question1_TB = comm.encode()+bytes([13,10])
        
        if cryo2_1st_ch:
            comm = '$GetTemp 1' #channels are read alternately
            question2_TB = comm.encode()+bytes([13,10])
        else:
            comm = '$GetTemp 2' #channels are read alternately
            question2_TB = comm.encode()+bytes([13,10])
        
        if cryo1_2nd_ch:
            if cryo1_ser.in_waiting>0:
                recieved1 = str(str(cryo1_ser.readline()))
                top_T = recieved1[3:len(recieved1)-5]
            else:
                self.cryo2_T_value.SetLabel('None')
                self.cryo2_T_text.SetLabel("Top pump (None)") 
                self.cryo_menu.SetLabel(ID_C1, 'Side/top pump: None')
                cryo1_item_id = self.cryo1_COM.FindItem('None')
                self.cryo1_COM.Check(cryo1_item_id, True)
                self.pump1_COM.Enable(self.pump1_com_id_list[self.cryo1_com_id_list.index(cryo1_item_id)], True)
                self.cryo2_COM.Enable(self.cryo2_com_id_list[self.cryo1_com_id_list.index(cryo1_item_id)], True)
                if cryo1_ser: cryo1_ser.close()
                cryo1_ser = None
                cryo1_2nd_ch = False
                return
            cryo1_ser.write(question1_TB)
            
            if float(top_T) < 18:
                if top_font_war:
                    self.cryo2_T_value.SetForegroundColour('#000000')
                    top_font_war = False
            elif float(top_T) > 17.9 and float(top_T) < 25.1:
                if not top_font_war:
                    self.cryo2_T_value.SetForegroundColour('#ff5f00')
                    top_font_war = True
            elif float(top_T) > 25:
                if not top_font_war:
                    self.cryo2_T_value.SetForegroundColour('#ff0000')
                    top_font_war = True
            self.cryo2_T_value.SetLabel(top_T)
        
        if cryo2_2nd_ch:
            if cryo2_ser.in_waiting > 0:
                recieved2 = str(str(cryo2_ser.readline()))
                buffer_T = recieved2[3:len(recieved2)-5]
            else:
                self.cryo4_T_value.SetLabel('None')
                self.cryo4_T_text.SetLabel("Buffer pump (None)") 
                self.cryo_menu.SetLabel(ID_C2, 'Buffer pump: None')
                cryo2_item_id = self.cryo2_COM.FindItem('None')
                self.cryo2_COM.Check(cryo2_item_id, True)
                self.pump1_COM.Enable(self.pump1_com_id_list[self.cryo2_com_id_list.index(cryo2_item_id)], True)
                self.cryo1_COM.Enable(self.cryo1_com_id_list[self.cryo2_com_id_list.index(cryo2_item_id)], True)
                if cryo2_ser: cryo2_ser.close()
                cryo2_ser = None
                cryo2_2nd_ch = False
                return
            cryo2_ser.write(question2_TB)
            
            if float(buffer_T) < 18:
                if buffer_font_war:
                    self.cryo4_T_value.SetForegroundColour('#000000')
                    buffer_font_war = False
            elif float(buffer_T) > 17.9 and float(buffer_T) < 25.1:
                if not buffer_font_war:
                    self.cryo4_T_value.SetForegroundColour('#ff5f00')
                    buffer_font_war = True
            elif float(buffer_T) > 25:
                if not buffer_font_war:
                    self.cryo4_T_value.SetForegroundColour('#ff0000')
                    buffer_font_war = True
            self.cryo4_T_value.SetLabel(buffer_T)
        
    def SetWater(self, event):
        global water_window
        water_window = FlowControlFrame(main_frame, title = '') 
        
class FlowControlFrame(wx.Frame):
    def __init__(self, parent, title):
        super(FlowControlFrame, self).__init__(parent, title = title, size = (150, 150))
        
        self.InitUI()       
        self.CentreOnParent()  
        self.SetWindowStyle(wx.STAY_ON_TOP)  
        self.Show()
        
    def InitUI(self):
        self.main_panel = wx.Panel(self)
        self.main_panel.SetSize(300,300)
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        self.info_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.fields_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        font = wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.NORMAL, wx.NORMAL) 
        
        self.info_text = wx.StaticText(self.main_panel, label = 'Alarm setpoint', size = (130,15))
        self.info_text.SetFont(font)
        
        self.input = NumCtrl(self.main_panel, fractionWidth = 1, integerWidth = 2, size = (50, 20)) 
        self.input.SetFont(font)
        
        self.text = wx.StaticText(self.main_panel, label = ' l/min', size = (70,15))
        self.text.SetBackgroundColour('#ededed')
        self.text.SetFont(font)
        
        self.ok_button = wx.Button(self.main_panel, label = 'OK', size = (60, 30))
        self.cancel_button = wx.Button(self.main_panel, label = 'Cancel', size = (60, 30))
        
        self.ok_button.Bind(wx.EVT_BUTTON, self.OkClicked)
        self.cancel_button.Bind(wx.EVT_BUTTON, self.CancelClicked)
        
        self.info_sizer.Add(self.info_text,flag = wx.TOP, border = 10)
        
        self.fields_sizer.Add(self.input, flag = wx.TOP|wx.LEFT|wx.BOTTOM, border = 10)
        self.fields_sizer.Add(self.text, flag = wx.TOP, border = 13)
        
        self.button_sizer.Add(self.ok_button)
        self.button_sizer.Add(self.cancel_button)
        
        self.main_sizer.Add(self.info_sizer, flag = wx.ALIGN_CENTER)
        self.main_sizer.Add(self.fields_sizer, flag = wx.ALIGN_CENTER)
        self.main_sizer.Add(self.button_sizer, flag = wx.ALIGN_CENTER)
        
        self.SetSizer(self.main_sizer)
        
        self.ok_button.SetDefault()
        
        self.SetMinSize((150,150))
        self.SetMaxSize((150,150))
        
        self.input.SetMax(10)
        self.input.SetMin(1)
        self.input.SetValue(float(main_frame.water_setpoint_value.GetLabel()))
        
    def OkClicked(self, event):
        global water_flow_value
        if self.input.GetValue() >= self.input.GetMin() and self.input.GetValue() <= self.input.GetMax():
            water_flow_value = self.input.GetValue()
            arduino_value = '$S'+str(int(water_flow_value*10))
            arduino_com = arduino_value.encode()
            ser.write(arduino_com)
            main_frame.water_setpoint_value.SetLabel(str(water_flow_value))
            self.Close()
        else:
            warning_message = "Wrong alarm setpoint. It must be set between %s and %s l/min."
            wx.MessageBox(warning_message %(str(self.input.GetMin()), str(self.input.GetMax())), 'Warning', wx.OK | wx.ICON_WARNING)
        main_frame.water_setpoint_value.SetLabel(str(water_flow_value)) 
        
        
    def CancelClicked(self, event):
        self.Close()

class info_window(wx.Dialog):
   
    def __init__(self, parent, title):
        super(info_window, self).__init__(parent, title = title, size = (400,400))
           
        self.InitUI()    
        self.Centre()
        self.Show()
         
    def InitUI(self):
        main_panel = wx.Panel(self)
        main_panel.SetBackgroundColour('#ededed')
        main_sizer = wx.BoxSizer(wx.VERTICAL)
         
        scroll_panel = scrolled.ScrolledPanel(main_panel, size = (350,420))
        scroll_panel.SetAutoLayout(1)
        scroll_panel.SetupScrolling(scroll_x = False)
        scroll_panel.SetBackgroundColour('#ededed')
        scroll_sizer = wx.BoxSizer(wx.VERTICAL)
        
        text_panel = wx.Panel(scroll_panel)
        
        infopath = os.path.join(data_path,'info.txt')
        label = open(infopath, 'r').read()
        self.txt = wx.StaticText(text_panel, label = label, style = wx.ST_NO_AUTORESIZE | wx.ALIGN_LEFT)
        self.txt.SetSize((320,420))
        scroll_sizer.Add(text_panel)
        scroll_panel.SetSizer(scroll_sizer)
         
        main_sizer.Add(scroll_panel,flag = wx.ALL|wx.ALIGN_CENTER, border = 10)   
       
        main_panel.SetSizer(main_sizer)
        
def pump_alarm():
    global side_T, buffer_T, top_T, alarm_sent, side_alarm, buffer_alarm, top_alarm, ser, LL_alarm, LL_T
    if side_T:
        if float(side_T)>25:
            side_alarm = True
        elif float(side_T)<24.5:
            side_alarm = False
    if buffer_T:
        if float(buffer_T)>25:
            buffer_alarm = True
        elif float(buffer_T)<24.5:
            buffer_alarm = False
    if top_T:
        if float(top_T)>25:
            top_alarm = True
        elif float(top_T)<24.5:
            top_alarm = False
    if LL_T:
        if float(LL_T)>25:
            LL_alarm = True
        elif float(LL_T)<24.5:
            LL_alarm = False       
            
    if side_alarm or buffer_alarm or top_alarm or LL_alarm:
        cryo_alarm = True
    elif not side_alarm and not buffer_alarm and not top_alarm and not LL_alarm:
        cryo_alarm = False
        
    if cryo_alarm and not alarm_sent:
        start_alarm = '$A1'
        start_alarm_b = start_alarm.encode()
        ser.write(start_alarm_b)
        alarm_sent = True
    elif not cryo_alarm and alarm_sent:
        stop_alarm = '$A0'
        stop_alarm_b = stop_alarm.encode()
        ser.write(stop_alarm_b)
        alarm_sent = False

if __name__  ==  '__main__':
    
    app = wx.App()
    main_frame = main_window(None, title = 'Parameters monitor')
    
    main_frame.pump_percent1.Hide()
    main_frame.progress1_value.Hide()
    main_frame.pump_percent2.Hide()
    main_frame.progress2_value.Hide()
    
    app.MainLoop()