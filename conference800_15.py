##
## 2025.05.09
# 1. 拿掉time.sleep
# 2. 加入二個主席
# 3. 攝影機修正
# 4. camera com port 退出
## 2025.05.12
# 新增攝影機Home
## 2025.05.13
# 修改錯誤
## 2025.05.14
# 新增攝影機
## 2025.05.15
# 1. 修改訊息
# 2. FIFO
## 2025.05.16
# 1. 新增計時佇列長度
# 2. 修改bug
## 2025.05.29
# 1. 測試camera 由mic com port傳出
## 2025.05.30
# 1.
##

import tkinter as tk
from tkinter import messagebox, ttk
import serial, threading, os, json, time, sys
import serial.tools.list_ports
#from collections import deque

# 全域佇列，只保留最新2個 mic_id (倒數計時)
#mic_id_queue = deque(maxlen=3)

CONFIG_FILE = "mic_base_config.json"
CONFIG_MIC_FILE = "mic_config.json"
CONFIG_TIME_FILE = "time_config.json"
CONFIG_CAMERA_FILE = "camera_base_config.json"
CONFIG_QUEUE_LIMIT_FILE = "queue_limit_config.json"
CONFIG_QUEUE_TIMER_LIMIT_FILE = "queue_timer_limit_config.json"
##
## 常用工具
class CommonTool:
    def __init__(self, root):
        self.root = root
        self.serial_port = None  # 串口連線物件
        self.camera_serial_port = None   # 攝影機串口連線物件
        self.mic_count_var = 0
        self.com_port_var = None
        self.display_to_value = {"主席": 1, "列席": 2}
        self.name_comboboxes = []

    ## 以下函式
    # 判斷 serial_port是否連線
    def is_serial_connected(self):
        return self.serial_port is not None and self.serial_port.is_open


    # 判斷 camera_serial_port是否連線
    def is_camera_serial_connected(self):
        return self.camera_serial_port is not None and self.camera_serial_port.is_open


    # MIC 的 COM PORT的連線
    def on_ok(self, com_port):
        #com_port = self.config.get("com_port", "COM1")
        try:
            #self.serial_port = serial.Serial(port=com_port, baudrate=9600, timeout=1)
            # 嘗試連線前先確認此 COM port 是否存在
            available_ports = [p.device for p in serial.tools.list_ports.comports()]
            if com_port not in available_ports:
                messagebox.showwarning("警告", f"找不到 COM PORT：{com_port}，請確認設備連接")
                return None

            self.serial_port = serial.Serial(
                port=com_port,
                baudrate=9600,
                bytesize=8,
                parity=serial.PARITY_EVEN,
                stopbits=1,
                timeout=1
            )
            if self.serial_port.is_open:
                # 切換至軟體控制模式
                self.switch_software_control_mode(1)
                messagebox.showinfo("成功", f"已連接到麥克風 {com_port} 並且進入軟體控制模式")

            return self.serial_port
        except serial.SerialException as e:
            messagebox.showerror("錯誤", f"無法開啟麥克風 {com_port}：\n{e}")

            self.serial_port = None
            return None
            #self.root.destroy()  # 或者 self.root.destroy() 如果你是在 Class 裡面
            #sys.exit(0)  # 完全結束程式

    # CAMERA 的 COM PORT的連線
    def connect_visca_serial(self, com_port):
        try:
            camera_serial_por_tmp = serial.Serial(
                port=com_port,
                baudrate=9600,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=1
            )

            if camera_serial_por_tmp.is_open:
                print(f"成功連線至 {com_port}")
                messagebox.showinfo("成功", f"已連接到攝影機 {com_port}")

            return camera_serial_por_tmp
        except serial.SerialException as e:
            #messagebox.showerror("錯誤", f"無法開啟攝影機 {com_port}：\n{e}")
            messagebox.showerror("錯誤", f"尚未連線 COM PORT: {com_port}，請先設定")
            camera_serial_por_tmp = None
            print(f"連線錯誤: {e}")
            return None



    # 登出和關掉視窗(退出至軟體控制模式)
    def on_cancel(self, mode):
        if self.serial_port and self.serial_port.is_open:
            print('準備結束serial port')
            self.switch_software_control_mode(0) # 切換/退出至軟體控制模式。0是退出
            self.serial_port.close()
            if mode == 'show':
                messagebox.showinfo("關閉", "已關閉Serial Port並離開軟體控制模式")
        else:
            print("尚未連接串口，無需關閉")


    # 載入紀錄
    def load_config(self, mode):
        #config_path = os.path.join(config_dir, "time_config.json")
        if os.path.exists( self.resource_path(CONFIG_FILE) ):
            try:
                #file_name = CONFIG_FILE if type == 'base' else CONFIG_MIC_FILE
                file_name = ''
                if mode == 'base':
                    file_name = CONFIG_FILE
                elif mode == 'mic':
                    file_name = CONFIG_MIC_FILE
                elif mode == 'time':
                    file_name = CONFIG_TIME_FILE
                elif mode == 'camera':
                    file_name = CONFIG_CAMERA_FILE
                elif mode == 'queue':
                    file_name = CONFIG_QUEUE_LIMIT_FILE
                elif mode == 'timer_limit':
                    file_name = CONFIG_QUEUE_TIMER_LIMIT_FILE
                #print(file_name)
                with open(self.resource_path(file_name), "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print("讀取 config.json 發生錯誤：", e)
        return {"mic_count": 1, "com_port": "COM1"}  # 預設值


    # 儲存基本紀錄
    #def save_config(self, mic_count_var, com_port_var):
    def save_config(self, com_port_var):
        config = {
            #"mic_count": mic_count_var,
            "com_port": com_port_var
        }
        try:
            with open(self.resource_path(CONFIG_FILE), "w", encoding="utf-8") as f:
                json.dump(config, f)
            messagebox.showinfo("儲存成功", f"序列埠設定成功")
            # 進入軟體連線
            #if not self.is_serial_connected():
            #    self.serial_port = self.on_ok(com_port_var)

            return self.serial_port
        except Exception as e:
            messagebox.showerror("儲存錯誤", f"儲存發生錯誤： {e}")


    # 設定攝影機模式
    def save_camera_base_config(self, mic_count_var, com_port_var):
        config = {
            "camera_count": mic_count_var,
            "com_port": com_port_var
        }
        try:
            with open(self.resource_path(CONFIG_CAMERA_FILE), "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
            messagebox.showinfo("儲存成功", f"已儲存攝影機設定")
        except Exception as e:
            messagebox.showerror("儲存錯誤", f"發生錯誤：{e}")


    # 設定主席
    def set_master_config(self, mic_id_var1, mic_id_var2):
        try:
            mic_id_list = self.load_config('mic')  # 載入設定
            print(f'var1: {mic_id_var1}, type: {type(mic_id_var1)}, var2: {mic_id_var2}, type: {type(mic_id_var2)}')
            mic_id_var1 = self.convert_str_to_int(mic_id_var1)
            mic_id_var2 = self.convert_str_to_int(mic_id_var2)
            print(f'var1: {mic_id_var1}, type: {type(mic_id_var1)}, var2: {mic_id_var2}, type: {type(mic_id_var2)}')
            chair1 = self.decimal_to_hex(mic_id_var1)
            chair2 = self.decimal_to_hex(mic_id_var2)
            new_config = []

            for item in mic_id_list:
                mic_id = item.get("mic_id")
                if mic_id == chair1 or mic_id == chair2:
                    item["type"] = 1
                else:
                    item["type"] = 2
                new_config.append(item)

            with open(self.resource_path(CONFIG_MIC_FILE), "w", encoding="utf-8") as f:
                json.dump(new_config, f, indent=4)
            messagebox.showinfo("儲存成功", f"已儲存主席設定")
        except Exception as e:
            messagebox.showerror("錯誤", f"儲存失敗：{e}")


    # 設定時間
    def set_time_config(self, hour_var, second_var):
        config = {
            "hour": hour_var,
            "second": second_var,
            "secondValue": self.convertSecond(hour_var, second_var)
        }
        try:
            with open(self.resource_path(CONFIG_TIME_FILE), "w", encoding="utf-8") as f:
                json.dump(config, f)
            messagebox.showinfo("儲存成功", f"計數時間已儲存")
        except Exception as e:
            messagebox.showerror("儲存錯誤", f"儲存發生錯誤： {e}")


    # 轉換秒數
    def convertSecond(self, minutes, seconds):
        total_seconds = minutes * 60 + seconds

        return total_seconds


    # 取出Serial_Port
    def getSerialPort(self):
        return self.serial_port


    # 儲存麥克風設定
    def save_mic_settings(self, name_comboboxes):
        result = []
        #for mic_id, combobox, name_var in self.name_comboboxes:
        for mic_id, combobox, name_var in name_comboboxes:
            display_text = name_var.get()
            type_value = self.display_to_value.get( display_text, 2)  # 預設列席
            result.append({
                "mic_id": mic_id,
                "type": type_value
            })

        try:
            with open(self.resource_path(CONFIG_MIC_FILE), "w", encoding="utf-8") as f:
                json.dump(result, f)
            #messagebox.showinfo("儲存成功",f"已儲存設定： {result}")
            messagebox.showinfo("儲存成功", f"已儲存麥克風數量設定")
        except Exception as e:
            messagebox.showerror("儲存錯誤",f"儲存發生錯誤： {e}")


    # 儲存FIFO佇列表度限制設定
    def save_queue_limit_config(self, mic_count_var1):
        config = {
            "queue_limit_count": mic_count_var1,
        }
        try:
            with open(self.resource_path(CONFIG_QUEUE_LIMIT_FILE), "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
            messagebox.showinfo("儲存成功", "已設定麥克風數量")
        except Exception as e:
            messagebox.showerror("儲存錯誤", f"發生錯誤：{e}")


    # 儲存倒數計時佇列表度限制設定
    def save_timer_queue_limit_config(self, mic_count_var1):
        config = {
            "queue_limit_count": mic_count_var1,
        }
        try:
            with open(self.resource_path(CONFIG_QUEUE_TIMER_LIMIT_FILE), "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
            messagebox.showinfo("儲存成功", "已設定麥克風數量")
        except Exception as e:
            messagebox.showerror("儲存錯誤", f"發生錯誤：{e}")


    # 切換/退出至軟體控制模式
    def switch_software_control_mode(self, mode):
        """
        傳送切換到軟體控制模式的指令：CC FF 22 22
        :param: switch: 0 退出軟體控制, 1 進入軟體控制
        """
        if not self.serial_port or not self.serial_port.is_open:
            print("無法切換控制模式，serial port 未連接")
            return
        # 將 HEX 字串轉換為 bytes
        hex_command = "CC FF 22 22" if mode == 1 else "CC FE 79 79"
        command_bytes = bytes.fromhex(hex_command)
        print(f"傳送指令: {hex_command}")
        if hasattr(self, 'debug_window') and self.debug_window:
            self.debug_window.add_log(f"傳送指令: {hex_command}")

        self.serial_port.write(command_bytes)

        #if mode == 0:
        #    self.serial_port.close()
        # 可選：讀取設備回應（根據設備是否會有回應決定）
        #response = self.serial_port.read(8)


    # 開啟Debug視窗
    def open_debug_window(self):
        if not hasattr(self, 'debug_window') or not (self.debug_window and tk.Toplevel.winfo_exists(self.debug_window.window)):
            self.debug_window = ConferenceDebugWindow(self.root, self)

    # 十進制轉成十六進制
    def decimal_to_hex(self, n):
        return f"{n:02X}"  # 補 0 並轉大寫

    # 十六進制轉成十進制
    def hex_to_decimal(self, hex_str):
        value = int(hex_str, 16)
        return f"{value:02d}"  # 回傳補零後的兩位字串

    # 處理字串為數值
    def process_string(self, s):
        if len(s) == 2 and s.startswith("0"):
            s = s[1:]  # 去掉開頭的 0
        return int(s)

    # 儲存攝影機
    def save_camera_mic_mapping(self, selected_camera_var, mic_vars):
        mic_config = self.load_config('mic')  # 載入設定

        selected_camera = selected_camera_var.get()
        if not selected_camera.isdigit():
            messagebox.showwarning("未選擇攝影機", "請先選擇攝影機ID")
            return

        selected_camera_id = int(selected_camera)
        selected_mics = [mic_id for mic_id, var in mic_vars.items() if var["var"].get() and not var["disabled"]]
        #print(selected_mics)
        """
        if not selected_mics:
            messagebox.showwarning("未選擇麥克風", "所有攝影機未選擇任何麥克風")
            return
        """
        for mic in mic_config:
            mic_id = mic.get("mic_id")
            if mic_id in selected_mics:
                mic["camera_id"] = selected_camera_id
            elif mic.get("camera_id") == selected_camera_id:
                mic["camera_id"] = 0

        try:
            with open(self.resource_path(CONFIG_MIC_FILE), "w", encoding="utf-8") as f:
                json.dump(mic_config, f, indent=4, ensure_ascii=False)
            #messagebox.showinfo("儲存成功", f"Camera-Mic 配對已儲存至 {CONFIG_MIC_FILE}")
            messagebox.showinfo("儲存成功", "攝影機與麥克風配對資料儲存")
        except Exception as e:
            messagebox.showerror("儲存錯誤", f"寫入 {CONFIG_MIC_FILE} 發生錯誤：{e}")


    # 取Mic_ID
    def getMicID(self, text):
        parts = text.split(" ")
        value = parts[1]
        return value


    # 檔案路徑
    def resource_path(self, relative_path):
        """取得資源檔案的絕對路徑，可支援 PyInstaller 打包後的執行"""
        if hasattr(sys, '_MEIPASS'):
            # PyInstaller 打包後會有此屬性
            #documents = os.path.expanduser("~\Documents")
            local_appdata = os.getenv("LOCALAPPDATA")
            base_path = os.path.join(local_appdata, "Conference")
            if not os.path.exists(base_path):
                os.makedirs(base_path)
        else:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)
    

    # 字串轉數字並且移除0
    def convert_str_to_int(self, s):
        if s.startswith("0") and len(s) == 2:
            s = s[1:]
        return int(s)



##
## 開啟視窗進入的畫面
class ConferenceApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Conference System")
        self.root.geometry("730x530")
        self.root.resizable(False, False)

        self.serial_port = None
        self.common = CommonTool(self.root)

        self.create_widgets()


    ## 以下是畫面
    # 建立主畫面
    def create_widgets(self):
        # 主容器
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # 上部按鈕區
        self.create_top_buttons(self.main_frame)

        # 中部按鈕區
        self.create_middle_buttons(self.main_frame)


    # TOP
    def create_top_buttons(self, parent):
        top_frame = tk.Frame(parent)
        top_frame.pack(fill="x", pady=10)

        # 左邊的按鈕區
        left_btn_frame = tk.Frame(top_frame)
        left_btn_frame.pack(side="left")

        tk.Button(left_btn_frame, text="麥克風設定", width=12, command=self.go_to_setting_page).pack(side="left", padx=5)
        tk.Button(left_btn_frame, text="攝影機設定", width=12, command=self.go_to_camera_page).pack(side="left", padx=5)
        tk.Button(left_btn_frame, text="攝影機歸位", width=12, command=self.go_to_camera_come_back).pack(side="left", padx=5)
        tk.Button(left_btn_frame, text="FIFO模式麥克風設定", width=15, command=self.go_to_fifoSet_page).pack(side="left", padx=5)
        tk.Button(left_btn_frame, text="計時模式麥克風設定", width=15, command=self.go_to_timerSet_page).pack(side="left", padx=5)

        # 右邊的按鈕區
        right_btn_frame = tk.Frame(top_frame)
        right_btn_frame.pack(side="right")

        #tk.Button(right_btn_frame, text="Debug模式", width=12, fg="red").pack(side="right", padx=5)

        return top_frame


    def create_middle_buttons(self, parent):
        middle_frame = tk.Frame(parent)
        middle_frame.pack(pady=100)

        tk.Button(middle_frame, text="進入計時會議", width=15, height=5, font=("Arial", 16, "bold"), fg="blue", command=self.go_to_conference_page).pack(side="left", padx=10)
        tk.Button(middle_frame, text="進入FIFO會議", width=15, height=5, font=("Arial", 16, "bold"), fg="blue", command=self.go_to_fifoconference_page).pack(side="left", padx=10)
        tk.Button(middle_frame, text="離開", width=15, height=5, fg="blue", font=("Arial", 16, "bold"), command=self.close_window).pack(side="left", padx=10)



    ## 以下函式
    # 關閉視窗
    def close_window(self):
        if self.common:
            if self.common.is_camera_serial_connected():
                mic_id = 63
                for i in range(1, 7):
                    # mic_id += 1
                    far_mic_id = self.common.decimal_to_hex(mic_id)
                    hex_command = f'8{str(i)} 01 04 3F 02 {far_mic_id} FF'
                    command_bytes = bytes.fromhex(hex_command)
                    self.common.camera_serial_port.write(command_bytes)
                    time.sleep(0.1)

                self.common.camera_serial_port.close()  # 執行關閉攝影機 serial port

            self.common.on_cancel('show')  # 呼叫 CommonTool 裡的 on_cancel
        #self.common.switch_software_control_mode(0)
        self.root.destroy()


    # 轉到麥克風設定畫面
    def go_to_setting_page(self):
        # 清空主畫面
        self.main_frame.pack_forget()
        # 顯示第二頁
        self.second_page = SettingPage(self.root, self)
        # 顯示會議系統頁
        #self.conference_page = entryConferencePage(self.root, self)


    # 轉到會議系統設定畫面
    def go_to_conference_page(self):
        if os.path.exists(self.common.resource_path(CONFIG_MIC_FILE) ):
            # 清空主畫面
            self.main_frame.pack_forget()
            # 顯示第二頁
            self.conference_page = entryConferencePage(self.root, self)
        else:
            messagebox.showwarning("警告", "請先進行麥克風設定")
            return


    # 轉到Camera設定畫面
    def go_to_camera_page(self):
        # 清空主畫面
        self.main_frame.pack_forget()
        # 顯示第二頁
        self.camera_page = CameraMicMappingPage(self.root, self)


    # 轉到FIFO模式麥克風設定畫面
    def go_to_fifoSet_page(self):
        # 清空主畫面
        self.main_frame.pack_forget()
        # 顯示第二頁
        self.fifoset_page = FIFOSettingPage(self.root, self)


    # 轉到FIFO模式會議畫面
    def go_to_fifoconference_page(self):
        print(f"1")
        if os.path.exists(self.common.resource_path(CONFIG_MIC_FILE)):
            # 清空主畫面
            self.main_frame.pack_forget()
            print(f"2")
            # 顯示第二頁
            self.fifoconference_page = FIFOConferencePage(self.root, self)
            print(f"3")
        else:
            messagebox.showwarning("警告", "請先進行麥克風設定")
            return


    # 轉到倒數模式麥克風設定畫面
    def go_to_timerSet_page(self):
        # 清空主畫面
        self.main_frame.pack_forget()
        # 顯示第二頁
        self.timerset_page = TimerSettingPage(self.root, self)


    # 返回主頁 ##
    def show_main_page(self, mode):
        #self.second_page.frame.pack_forget() if mode == 'mic_set' else self.conference_page.frame.pack_forget()
        if mode == 'mic_set':
            self.second_page.frame.pack_forget()
        elif mode == 'conference':
            self.conference_page.frame.pack_forget()
        elif mode == 'camera':
            self.camera_page.frame.pack_forget()
        elif mode == 'queue_set':
            self.fifoset_page.frame.pack_forget()
        elif mode == 'queue_conference':
            self.fifoconference_page.frame.pack_forget()
        elif mode == 'timer_set':
            self.timerset_page.frame.pack_forget()

        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)


    # 攝影機歸位
    def go_to_camera_come_back(self):
        #self.camera_config = self.common.load_config('camera')  # 載入設定
        self.camera_config = self.common.load_config('base')  # 載入設定
        print(self.camera_config)
        self.common.camera_serial_port = self.common.on_ok(self.camera_config.get("com_port", "COM1"))
        time.sleep(0.1)  # 稍微等一下
        if self.common.is_serial_connected():
            # 關閉攝影機
            mic_id = 63
            far_mic_id = self.common.decimal_to_hex(mic_id)
            #hex_command = f'81 01 04 3F 02 {far_mic_id} FF'
            #command_bytes = bytes.fromhex(hex_command)
            #self.common.serial_port.write(command_bytes)
            #time.sleep(0.3)  # 稍微等一下
            for i in range(1, 7):
            #for i in range(6, 0, -1):
                for j in range(2):
                    #mic_id += 1
                    hex_command = f'8{str(i)} 01 04 3F 02 {far_mic_id} FF'
                    try:
                        command_bytes = bytes.fromhex(hex_command)
                        #self.common.camera_serial_port.write(command_bytes)
                        self.common.serial_port.write(command_bytes)
                        time.sleep(0.05)  # 稍微等一下
                    except ValueError as e:
                        #print(f"hex_command 失敗，指令內容有誤：{command_bytes}")
                        if hasattr(self.common, 'debug_window') and self.common.debug_window:
                            self.common.debug_window.add_log(f"無效 hex 指令: {hex_command}")
                        return
                time.sleep(0.05)
                # Log
                if hasattr(self.common, 'debug_window') and self.common.debug_window:
                    self.common.debug_window.add_log(f"攝影機{str(i)} 指令已送出： {hex_command}")

            # 關閉Camera Serial Port
            if self.common.is_serial_connected():
                #self.common.serial_port.close() #執行關閉攝影機 serial port
                self.common.on_cancel('hide')  # 呼叫 CommonTool 裡的 on_cancel

##
## 設定頁面
class SettingPage:
    def __init__(self, root, main_app):
        self.root = root
        self.main_app = main_app

        self.frame = tk.Frame(root)
        self.frame.pack(fill="both", expand=True)
        self.serial_port = None
        # 預設載入設定檔內容
        self.common = main_app.common
        self.comportSettingPage()

    ## 以下是畫面
    # 麥克風設定頁面
    def micSettingPage(self):
        #print(self.common.getSerialPort())
        #self.serial_port = self.common.getSerialPort()

        self.clear_frame()  # ← 新增這行
        tk.Label(self.frame, text="麥克風設定", font=("Arial", 16)).pack(pady=30)
        middle_frame = tk.Frame(self.frame)
        middle_frame.pack(pady=10)

        # Option
        self.com_port_button = tk.Button(middle_frame, text="序列埠設定", width=12, command=self.comportSettingPage)
        self.com_port_button.pack(side="left", padx=10)
        self.com_port_button.config(state="normal")

        self.mic_count_button = tk.Button(middle_frame, text="數量設定", width=12, command=self.micSettingPage)
        self.mic_count_button.pack(side="left", padx=10)
        self.mic_count_button.config(state="normal")

        self.set_master_button = tk.Button(middle_frame, text="主席設定", width=12, command=self.masterSettingPage)
        self.set_master_button.pack(side="left", padx=10)
        self.set_master_button.config(state="normal")

        self.set_time_button = tk.Button(middle_frame, text="時間設定", width=12, command=self.timeSettingPage)
        self.set_time_button.pack(side="left", padx=10)
        self.set_time_button.config(state="normal")

        self.set_exist_button = tk.Button(middle_frame, text="離開設定", width=12, command=self.back_to_main)
        self.set_exist_button.pack(side="left", padx=10)
        self.set_exist_button.config(state="normal")
        tk.Button(middle_frame, text="Debug模式", width=12, fg="blue", command=self.common.open_debug_window).pack(side="left",
                                                                                                            padx=10)

        # 創建一個高度為 1 像素，背景色為灰色的 Frame 作為水平線
        separator = tk.Frame(self.frame, height=1, bg="gray")
        separator.pack(fill="x", padx=5)  # fill="x" 使其水平填充可用寬度

        # 搜尋按鈕
        middle1_frame = tk.Frame(self.frame)
        middle1_frame.pack(pady=25)

        self.search_mic_button = tk.Button(middle1_frame, text="搜尋", width=12, command=self.search_mic_list)
        self.search_mic_button.pack(side="left", padx=10)
        self.search_mic_button.config(state="normal")
        # 切換表格容器區塊 -- MIC 列表
        self.list_content_frame = tk.Frame(self.frame)
        self.list_content_frame.pack(pady=10, fill="both", expand=True)

        self.frame.pack(fill="both", expand=True)
        # 預設載入設定檔內容
        self.build_generate_table(use_mic_list=False)


    # 序列埠設定頁面
    def comportSettingPage(self):
        self.clear_frame()  # 新增這行

        self.config = self.common.load_config('base')  # 載入設定
        tk.Label(self.frame, text="麥克風設定", font=("Arial", 16)).pack(pady=30)
        middle_frame = tk.Frame(self.frame)
        middle_frame.pack(pady=10)

        # Option
        tk.Button(middle_frame, text="序列埠設定", width=12, command=self.comportSettingPage).pack(side="left", padx=10)
        tk.Button(middle_frame, text="數量設定", width=12, command=self.micSettingPage).pack(side="left", padx=10)
        tk.Button(middle_frame, text="主席設定", width=12, command=self.masterSettingPage).pack(side="left", padx=10)
        tk.Button(middle_frame, text="時間設定", width=12, command=self.timeSettingPage).pack(side="left", padx=10)
        tk.Button(middle_frame, text="離開設定", width=12, command=self.back_to_main).pack(side="left", padx=10)
        tk.Button(middle_frame, text="Debug模式", width=12, fg="blue", command=self.common.open_debug_window).pack(side="left",
                                                                                                            padx=10)

        # 創建一個高度為 1 像素，背景色為灰色的 Frame 作為水平線
        separator = tk.Frame(self.frame, height=1, bg="gray")
        separator.pack(fill="x", padx=5)  # fill="x" 使其水平填充可用寬度

        # 以下設定表單
        middle1_frame = tk.Frame(self.frame)
        middle1_frame.pack(pady=25)

        # 調整 grid 欄寬比例，讓欄位置中對齊
        middle1_frame.columnconfigure(0, weight=1)
        middle1_frame.columnconfigure(1, weight=1)

        # 麥克風數量表單
        """
        mic_id_list = self.common.load_config('mic')  # 載入設定
        mic_count = len(mic_id_list) if os.path.exists( self.common.resource_path(CONFIG_MIC_FILE) ) else 0
        print(f'mic_count: {mic_count}')
        tk.Label(middle1_frame, text="麥克風數量：", font=("Arial", 12)).grid(row=0, column=0, sticky="e", pady=5,
                                                                               padx=10)
        self.mic_count_var = tk.IntVar(value=mic_count)
        mic_count_entry = tk.Entry(middle1_frame, textvariable=self.mic_count_var, width=12)
        mic_count_entry.grid(row=0, column=1, sticky="w", pady=5, padx=10)
        """
        # COM PORT 下拉選單
        tk.Label(middle1_frame, text="COM PORT：", font=("Arial", 12)).grid(row=1, column=0, sticky="e", pady=5,
                                                                             padx=10)
        com_ports = [f"COM{i}" for i in range(1, 101)]
        self.com_port_var = tk.StringVar(value=self.config.get("com_port", "COM1"))
        com_dropdown = ttk.Combobox(middle1_frame, textvariable=self.com_port_var, values=com_ports, width=12,
                                    state="readonly")
        com_dropdown.grid(row=1, column=1, sticky="w", pady=5, padx=10)
        # 儲存按鈕
        #save_button = tk.Button(self.frame, text="儲存", width=12, command=lambda: self.common.save_config(self.mic_count_var.get(), self.com_port_var.get()))
        save_button = tk.Button(self.frame, text="儲存", width=12, command=lambda: self.common.save_config(self.com_port_var.get()))
        save_button.pack(pady=20)


    # 主席設定
    def masterSettingPage(self):
        self.clear_frame()  # 新增這行

        self.config = self.common.load_config('base')  # 載入設定
        tk.Label(self.frame, text="麥克風設定", font=("Arial", 16)).pack(pady=30)
        middle_frame = tk.Frame(self.frame)
        middle_frame.pack(pady=10)

        # Option
        tk.Button(middle_frame, text="序列埠設定", width=12, command=self.comportSettingPage).pack(side="left", padx=10)
        tk.Button(middle_frame, text="數量設定", width=12, command=self.micSettingPage).pack(side="left", padx=10)
        tk.Button(middle_frame, text="主席設定", width=12, command=self.masterSettingPage).pack(side="left", padx=10)
        tk.Button(middle_frame, text="時間設定", width=12, command=self.timeSettingPage).pack(side="left", padx=10)
        tk.Button(middle_frame, text="離開設定", width=12, command=self.back_to_main).pack(side="left", padx=10)
        tk.Button(middle_frame, text="Debug模式", width=12, fg="blue", command=self.common.open_debug_window).pack(side="left",
                                                                                                            padx=10)

        # 創建一個高度為 1 像素，背景色為灰色的 Frame 作為水平線
        separator = tk.Frame(self.frame, height=1, bg="gray")
        separator.pack(fill="x", padx=5)  # fill="x" 使其水平填充可用寬度

        # 以下設定表單
        middle1_frame = tk.Frame(self.frame)
        middle1_frame.pack(pady=25)

        # 調整 grid 欄寬比例，讓欄位置中對齊
        middle1_frame.columnconfigure(0, weight=1)
        middle1_frame.columnconfigure(1, weight=1)

        ## MIC ID 下拉選單
        if not os.path.exists( self.common.resource_path(CONFIG_MIC_FILE)):
            messagebox.showwarning("警告", "請先進行數量設定")
            return
        # 讀取 mic_config.json
        mic_id_list = self.common.load_config('mic')
        current_chairs = [item for item in mic_id_list if item.get("type") == 1]

        # 所有 mic_id（HEX 形式）與 Decimal 對應
        mic_ids_hex = [str(item.get("mic_id", "")) for item in mic_id_list]
        mic_ids_decimal = list(map(self.common.hex_to_decimal, mic_ids_hex))
        print(f'mic_ids_decimal: {mic_ids_decimal}')
        # 預設值（若有現存兩個主席，分別預設）
        default_1 = self.common.hex_to_decimal(current_chairs[0]['mic_id']) if len(current_chairs) > 0 else mic_ids_decimal[0]
        default_2 = self.common.hex_to_decimal(current_chairs[1]['mic_id']) if len(current_chairs) > 1 else mic_ids_decimal[1]
        #default_1 = mic_ids_decimal[0]
        #default_2 = mic_ids_decimal[2]
        #self.common.convert_str_to_int(self.mic_id_var1.get())
        print(f'default_1: {default_1}')
        print(f'default_2: {default_2}')
        print(f'default_2: {type(default_2) }') # return str

        # 第一位主席
        tk.Label(middle1_frame, text="主席 MIC ID 1：", font=("Arial", 12)).grid(row=1, column=0, sticky="e", pady=5,
                                                                                padx=10)
        self.mic_id_var1 = tk.StringVar(value=default_1)
        mic_dropdown1 = ttk.Combobox(middle1_frame, textvariable=self.mic_id_var1, values=mic_ids_decimal, width=12,
                                     state="readonly")
        mic_dropdown1.grid(row=1, column=1, sticky="w", pady=5, padx=10)

        # 第二位主席
        tk.Label(middle1_frame, text="主席 MIC ID 2：", font=("Arial", 12)).grid(row=2, column=0, sticky="e", pady=5,
                                                                                padx=10)
        self.mic_id_var2 = tk.StringVar(value=default_2)
        mic_dropdown2 = ttk.Combobox(middle1_frame, textvariable=self.mic_id_var2, values=mic_ids_decimal, width=12,
                                     state="readonly")
        mic_dropdown2.grid(row=2, column=1, sticky="w", pady=5, padx=10)
        """
        ## MIC ID 下拉選單
        # 讀取 mic_config.json
        mic_id_list = self.common.load_config('mic')
        result = next((item for item in mic_id_list if item['type'] == 1), mic_id_list[0])
        print(result)
        mic_id_list = [str(item.get("mic_id", "")) for item in mic_id_list]
        mic_id_list1 = list(map(self.common.hex_to_decimal, mic_id_list))

        tk.Label(middle1_frame, text="主席 MIC ID：", font=("Arial", 12)).grid(row=1, column=0, sticky="e", pady=5, padx=10)

        # 下拉選單變數
        self.mic_id_var2 = tk.StringVar(value=self.common.hex_to_decimal(result['mic_id']))
        mic_dropdown = ttk.Combobox(middle1_frame, textvariable=self.mic_id_var2, values=mic_id_list1, width=12, state="readonly")
        mic_dropdown.grid(row=1, column=1, sticky="w", pady=5, padx=10)
        """
        # 儲存按鈕
        #var1 = self.common.convert_str_to_int(self.mic_id_var1.get())
        #var2 = self.common.convert_str_to_int(self.mic_id_var2.get())
        #print(f'var1: {self.mic_id_var1.get()}, var2: {self.mic_id_var2.get()}')
        #save_button = tk.Button(self.frame, text="儲存", width=12)
        save_button = tk.Button(self.frame, text="儲存", width=12, command=lambda: self.common.set_master_config( self.mic_id_var1.get(), self.mic_id_var2.get() ))
        save_button.pack(pady=20)


    # Time設定
    def timeSettingPage(self):
        self.clear_frame()  # 新增這行

        self.config = self.common.load_config('base')  # 載入設定
        tk.Label(self.frame, text="麥克風設定", font=("Arial", 16)).pack(pady=30)
        middle_frame = tk.Frame(self.frame)
        middle_frame.pack(pady=10)

        # Option
        tk.Button(middle_frame, text="序列埠設定", width=12, command=self.comportSettingPage).pack(side="left",
                                                                                                   padx=10)
        tk.Button(middle_frame, text="數量設定", width=12, command=self.micSettingPage).pack(side="left", padx=10)
        tk.Button(middle_frame, text="主席設定", width=12, command=self.masterSettingPage).pack(side="left",
                                                                                                padx=10)
        tk.Button(middle_frame, text="時間設定", width=12, command=self.timeSettingPage).pack(side="left", padx=10)
        tk.Button(middle_frame, text="離開設定", width=12, command=self.back_to_main).pack(side="left", padx=10)
        tk.Button(middle_frame, text="Debug模式", width=12, fg="blue", command=self.common.open_debug_window).pack(side="left", padx=10)

        # 創建一個高度為 1 像素，背景色為灰色的 Frame 作為水平線
        separator = tk.Frame(self.frame, height=1, bg="gray")
        separator.pack(fill="x", padx=5)  # fill="x" 使其水平填充可用寬度

        # 以下設定表單
        middle1_frame = tk.Frame(self.frame)
        middle1_frame.pack(pady=25)

        # 調整 grid 欄寬比例，讓欄位置中對齊
        middle1_frame.columnconfigure(0, weight=1)
        middle1_frame.columnconfigure(1, weight=1)

        self.config = self.common.load_config('time')  # 載入設定
        ##
        # 小時下拉選單在標籤前
        hour_var = tk.IntVar()
        hour_combobox = ttk.Combobox(middle1_frame, textvariable=hour_var, values=[str(i) for i in range(0, 61)], width=5,
                                     state="readonly")
        hour_combobox.pack(side="left", padx=5)
        hour_combobox.set(self.config.get("hour", 1))
        tk.Label(middle1_frame, text="分", font=("Arial", 12)).pack(side="left", padx=5)

        # 秒數下拉選單在標籤前
        second_var = tk.IntVar()
        second_combobox = ttk.Combobox(middle1_frame, textvariable=second_var, values=[str(i) for i in range(0, 61)],
                                       width=5, state="readonly")
        second_combobox.pack(side="left", padx=15)
        second_combobox.set(self.config.get("second", 0))
        tk.Label(middle1_frame, text="秒", font=("Arial", 12)).pack(side="left", padx=5)


        # 儲存按鈕
        save_button = tk.Button(self.frame, text="儲存", width=12, command=lambda: self.common.set_time_config( int(hour_var.get()) , int(second_var.get()) ))
        save_button.pack(pady=20)


    ## 以下函式
    # 清空畫面
    def clear_frame(self):
        for widget in self.frame.winfo_children():
            widget.destroy()

    # 回到主頁
    def back_to_main(self):
        #self.common.on_cancel('hide')  # 呼叫 CommonTool 裡的 on_cancel
        self.main_app.show_main_page('mic_set')

    # 搜尋 mic 列表
    def search_mic_list(self):
        #print("✅ search_mic_list 被呼叫")
        # self.common
        if not self.common.is_serial_connected():
            base_config = self.common.load_config('base')
            print(base_config.get("com_port", "COM1"))
            self.common.serial_port = self.common.on_ok(base_config.get("com_port", "COM1"))

        # 檢查是否成功連線
        #if not self.common.is_serial_connected():
        #    messagebox.showerror("錯誤", "請先連線主機！")
        #    return

        # 1. 清空表格內容
        for widget in self.list_content_frame.winfo_children():
            widget.destroy()

        # 上方按鈕列Disable
        self.com_port_button.config(state="disabled")
        self.mic_count_button.config(state="disabled")
        self.set_master_button.config(state="disabled")
        self.set_time_button.config(state="disabled")
        self.set_exist_button.config(state="disabled")

        # 搜尋按鈕Disable
        self.search_mic_button.config(state="disabled")

        # 顯示「設備搜尋中」訊息
        self.searching_label = tk.Label(self.list_content_frame, text="設備搜尋中", font=("Arial", 16, "bold"), fg="red", padx=20, pady=10)
        self.searching_label.pack(pady=(10, 5))

        def task():
            self.mic_list = []

            # 如果 serial port 尚未連線，直接跳出任務
            if not self.common.is_serial_connected():
                print("Serial port 尚未連線，無法執行搜尋")
                self.frame.after(0, lambda: messagebox.showerror("錯誤", "尚未連線 COM PORT，請先設定。"))
                # 按鈕狀態還原
                # 搜尋按鈕 open
                self.search_mic_button.config(state="normal")

                # 上方按鈕列 open
                self.com_port_button.config(state="normal")
                self.mic_count_button.config(state="normal")
                self.set_master_button.config(state="normal")
                self.set_time_button.config(state="normal")
                self.set_exist_button.config(state="normal")
                self.searching_label.config(text=f"設備搜尋取消")
                return

            for i in range(1, 61):
            #for i in range(1, 10):
                #mic_id = f"{i :02d}"
                mic_id = self.common.decimal_to_hex(i)
                hex_command = f"CC {mic_id} 55 AA"
                command_bytes = bytes.fromhex(hex_command)
                print(f"傳送指令: {hex_command}")
                # 顯示「設備搜尋中」訊息
                dec_id = self.common.hex_to_decimal(mic_id)
                self.searching_label.config(text=f"設備搜尋中 { dec_id }")

                # Log
                if hasattr(self.common, 'debug_window') and self.common.debug_window:
                    self.common.debug_window.add_log(f"傳送指令:  {hex_command}")

                self.common.serial_port.write(command_bytes)

                # 可選：讀取設備回應（根據設備是否會有回應決定）
                response = self.common.serial_port.read(8)

                if response:
                    print("裝置回應：", response.hex().upper())
                    # Log
                    if hasattr(self.common, 'debug_window') and self.common.debug_window:
                        self.common.debug_window.add_log(f"裝置回應： {response.hex().upper()}")

                    self.mic_list.append(mic_id)
                else:
                    print("沒有收到回應")

            # 執行 UI 更新（回主執行緒）
            self.frame.after(0, self.on_search_complete)

        # 在背景執行 task 避免卡住 UI
        threading.Thread(target=task).start()


    # 搜尋完成，顯示表格
    def on_search_complete(self):
        #self.searching_label.pack_forget()  # 隱藏搜尋中標籤
        # 關掉連線
        self.common.on_cancel('hide')

        # 移除「設備搜尋中」訊息
        if hasattr(self, 'searching_label') and self.searching_label.winfo_exists():
            self.searching_label.destroy()

        # 搜尋按鈕 open
        self.search_mic_button.config(state="normal")

        # 上方按鈕列 open
        self.com_port_button.config(state="normal")
        self.mic_count_button.config(state="normal")
        self.set_master_button.config(state="normal")
        self.set_time_button.config(state="normal")
        self.set_exist_button.config(state="normal")

        self.build_generate_table(use_mic_list=True)


    # 產生表格
    def build_generate_table(self, use_mic_list=False):
        try:
            # 取得 mic ID 列表
            if use_mic_list:
                if not hasattr(self, 'mic_list') or not self.mic_list:
                    raise ValueError("搜尋未找到任何麥克風裝置")
                mic_ids = self.mic_list
            else:
                if not os.path.exists(self.common.resource_path(CONFIG_MIC_FILE)):
                    print("mic_config.json 檔案不存在，不顯示表格。")
                    return

                self.config = self.common.load_config("mic") or []
                if not self.config:
                    print("mic_config.json 是空陣列，不顯示表格。")
                    return

                #self.config = self.load_config("mic") if os.path.exists(CONFIG_MIC_FILE) else []
                mic_ids = [item["mic_id"] for item in self.config]

            # 建立 Canvas + Scrollbar 架構
            canvas = tk.Canvas(self.list_content_frame, height=250)  # 可以依照需要調整高度
            scrollbar = tk.Scrollbar(self.list_content_frame, orient="vertical", command=canvas.yview)

            # 建立捲動內容容器 scrollable_frame
            scrollable_frame = tk.Frame(canvas)

            scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(
                    scrollregion=canvas.bbox("all")
                )
            )

            self.canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="n")
            #canvas.create_window((canvas.winfo_reqwidth() // 2, 0), window=scrollable_frame, anchor="n")
            #canvas.configure(yscrollcommand=scrollbar.set)

            # 當 canvas 改變大小時，置中 scrollable_frame
            def center_canvas_content(event):
                canvas_width = event.width
                canvas.itemconfig(self.canvas_window, width=canvas_width)
                canvas.coords(self.canvas_window, canvas_width // 2, 0)

            canvas.bind("<Configure>", center_canvas_content)

            canvas.pack(side="left", fill="both", expand=True)
            #scrollbar.pack(side="right", fill="y")
            scrollbar.pack(fill="both", expand=True)

            # 新增內層容器以置中表格
            self.inner_frame = tk.Frame(scrollable_frame)
            self.inner_frame.pack()  # 這裡是關鍵：置中對齊


            # 標題列
            tk.Label(self.inner_frame, text="Mic ID", font=("Arial", 10, "bold"), width=15, bg="#d6dbf5").grid(row=0, column=0, padx=5, pady=2)
            tk.Label(self.inner_frame, text="代表", font=("Arial", 10, "bold"), width=15, bg="#d6dbf5").grid(row=0, column=1, padx=5, pady=2)

            # 預設對應值轉換：顯示 -> 實際值
            self.display_to_value = {"主席": 1, "列席": 2}
            self.value_to_display = {v: k for k, v in self.display_to_value.items()}
            self.name_comboboxes = []

            self.config = self.common.load_config("mic") if os.path.exists( self.common.resource_path(CONFIG_MIC_FILE) ) else []

            # 資料列
            for row, mic_id in enumerate(mic_ids):
                # mic_id = f"{i + 1:02d}"
                # name = "主席" if i == 0 else "列席"
                # tk.Label(self.inner_frame, text=mic_id, width=15, font=("Arial", 12)).grid(row=i+1, column=0, padx=5, pady=2)
                tk.Label(self.inner_frame, text=self.common.hex_to_decimal(mic_id), width=15, font=("Arial", 12)).grid(row=row + 1, column=0, padx=5, pady=2)

                # 代表
                name_var = tk.StringVar()
                # UI 顯示用下拉值
                display_options = ["主席", "列席"]

                # 從 config 中找出對應 mic_id 的設定值
                #existing = next((c for c in self.config if c.get("mic_id") == mic_id), None)
                existing = next((item for item in getattr(self, 'config', []) if item.get("mic_id") == mic_id), None)
                type_value = existing.get("type") if existing else "2"
                display_value = self.value_to_display.get(int(type_value), "列席")
                name_var.set(display_value)

                # 使用 Label 顯示文字
                name_label = tk.Label(self.inner_frame, textvariable=name_var, width=15, font=("Arial", 12),
                                      anchor="center")
                name_label.grid(row=row + 1, column=1, padx=5, pady=2)
                #name_combobox = ttk.Combobox(self.inner_frame, textvariable=name_var, values=display_options, width=15, state="readonly")
                #name_combobox.grid(row=row + 1, column=1, padx=5, pady=2)

                # 儲存 tuple: (Mic ID, Combobox, 對應的實際值 StringVar)
                self.name_comboboxes.append((mic_id, name_label, name_var))

            # 儲存按鈕放在捲動區下方，避免被滾走
            #save_button = tk.Button(scrollable_frame, text="儲存", width=12, command=lambda: self.save_system_settings() )
            save_button = tk.Button(scrollable_frame, text="儲存", width=12, command=lambda: self.common.save_mic_settings(self.name_comboboxes) )
            save_button.pack(pady=10, anchor="center")

        except ValueError:
            from tkinter import messagebox
            messagebox.showerror("輸入錯誤", "沒有找到任何麥克風設備")


##
## 進入會議設定頁面
class entryConferencePage:
    def __init__(self, root, main_app):
        self.root = root
        self.main_app = main_app

        self.frame = tk.Frame(root)
        self.frame.pack(fill="both", expand=True)
        #self.serial_port = None
        self.timer_seconds = 0 # 計時器
        self.timer_label_frame = None
        # 預設載入設定檔內容
        self.common = main_app.common
        # 以下連線com port
        self.config = self.common.load_config('base')  # 載入設定
        self.camera_config = self.common.load_config('camera')  # 載入設定
        # 取出主席ID
        self.mic_id_list = self.common.load_config('mic')
        #self.master = next((item for item in self.mic_id_list if item['type'] == 1), self.mic_id_list[0])
        self.mic_id_queue = []
        self.config_queue = self.common.load_config('timer_limit')
        self.queue_limit = self.config_queue.get('queue_limit_count', 0)
        print(f'timer conference: {self.queue_limit}')
        #self.queue_limit = 2
        #self.ser = None       # serial port 連線
        self.running = False  # 讓監聽自己跳出 while 迴圈
        self.is_timer_running = False  # 加一個旗標
        self.is_sending_command = False  # 追蹤是否正在送指令

        self.timer_flags = {}  # mic_id 專屬倒數啟動與停止 flag
        self.timer_flags_temp = {}  # mic_id 專屬倒數啟動與停止 flag

        self.conferencePage()  # 預設頁面

    ## 以下是畫面
    # 會議系統控制頁面
    def conferencePage(self):
        # 判斷 serial port 是否連線
        if not self.common.is_serial_connected():
            messagebox.showinfo("提醒", "Serial port 尚未開啟，請在右上方按下「Serial Port連線」按鈕。")

        self.clear_frame()  # ← 新增這行
        self.create_top_buttons(self.frame)

        # 標題
        tk.Label(self.frame, text="計時會議系統控制", font=("Arial", 16)).pack(pady=20)
        middle_frame = tk.Frame(self.frame)
        middle_frame.pack(pady=5)
        # timer_label
        # 創建一個高度為 1 像素，背景色為灰色的 Frame 作為水平線
        separator = tk.Frame(self.frame, height=1, bg="gray").pack(fill="x", padx=5)  # fill="x" 使其水平填充可用寬度
        # 麥克風列表區塊
        canvas_frame = tk.Frame(self.frame)
        canvas_frame.pack(pady=15, fill="both", expand=True)

        # 建立 Canvas 和 Scrollbar
        canvas = tk.Canvas(canvas_frame, height=300)
        scrollbar = tk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        # 可捲動 Frame（內容）
        scrollable_frame = tk.Frame(canvas)

        # 建立 window 並靠左對齊 (anchor="nw")
        canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

        # 自動更新 scrollregion
        def update_scrollregion(event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        scrollable_frame.bind("<Configure>", update_scrollregion)

        mic_id_list = self.common.load_config('mic')  # 載入設定
        sorted_data = sorted(mic_id_list, key=lambda x: x['type'])  # 依 type 為1排序

        total_buttons = len(mic_id_list)
        buttons_per_row = 5
        self.mic_timer_labels = {}  # 新增：每個 mic_id 對應的 label
        # for i in range(total_buttons):
        #print(f'queue: { list(mic_id_queue) }')
        # command=lambda: self.execDevice(item['mic_id'])
        for index, item in enumerate(sorted_data):
            mic_id = item['mic_id']
            dec_id = self.common.hex_to_decimal(mic_id)
            # btn = tk.Button(scrollable_frame, text=f"主席: 麥克風 { self.common.hex_to_decimal(item['mic_id']) }", width=12, fg="red") if index == 0 else tk.Button(scrollable_frame, text=f"麥克風 { self.common.hex_to_decimal(item['mic_id']) }", width=12)
            row = index // buttons_per_row
            col = index % buttons_per_row
            # 按鈕
            btn_text = f"主席: 麥克風 {dec_id}" if item['type'] == 1 else f"麥克風 {dec_id}"
            btn_fg = "red" if item['type'] == 1 else "black"
            btn = tk.Button(scrollable_frame, text=btn_text, width=15, fg=btn_fg)
            btn.grid(row=row * 2, column=col, padx=10, pady=(10, 5))
            # 計時器
            timer_label = tk.Label(scrollable_frame, text="", font=("Arial", 10), fg="blue")
            timer_label.grid(row=row * 2 + 1, column=col, pady=(0, 10))

            self.mic_timer_labels[mic_id] = timer_label

    # 按鈕執行動作
    #def execDevice(self, mic_id):
    #    print(f'queue: { list(mic_id_queue) }')

    # TOP
    def create_top_buttons(self, parent):
        top_frame = tk.Frame(parent)
        top_frame.pack(fill="x", pady=5)

        # 右邊的按鈕區
        right_btn_frame = tk.Frame(top_frame)
        right_btn_frame.pack(side="right")
        # self.common.on_ok(self.config.get("com_port", "COM1")
        tk.Button(right_btn_frame, text="Debug模式", width=12, command=self.common.open_debug_window).pack(side="right", padx=5)
        self.exitout = tk.Button(right_btn_frame, text="離開", width=12, command=self.back_to_main).pack(side="right", padx=5)
        self.connection = tk.Button(right_btn_frame, text="Serial Port連線", width=12, command=self.connectionSerial)
        self.connection.pack(side="right", padx=5)
        #self.connection = tk.Button(right_btn_frame, text="Serial Port連線", width=12, command=self.connectionSerial).pack(side="right", padx=5)


    ## 以下函式
    # 清空畫面
    def clear_frame(self):
        for widget in self.frame.winfo_children():
            widget.destroy()


    # 回到主頁
    def back_to_main(self):
        print("離開頁面，準備關閉執行緒...")
        self.running = False  # 讓監聽自己跳出 while 迴圈
        time.sleep(0.1)  # 稍微等一下（給 thread time 結束）
        #if self.common.camera_serial_port and self.common.camera_serial_port.is_open:
        if self.common.is_serial_connected():
            mic_id = 63
            #for i in range(6, 0, -1):
            for i in range(1, 7):
                # mic_id += 1
                for j in range(2):
                    far_mic_id = self.common.decimal_to_hex(mic_id)
                    hex_command = f'8{str(i)} 01 04 3F 02 {far_mic_id} FF'
                    command_bytes = bytes.fromhex(hex_command)
                    #self.common.camera_serial_port.write(command_bytes)
                    self.common.serial_port.write(command_bytes)
                    time.sleep(0.05)
                time.sleep(0.05)

            #self.common.camera_serial_port.close() #執行關閉攝影機 serial port
        time.sleep(0.1)
        self.common.on_cancel('show')   #執行關閉麥克風 serial port
        #self.common.switch_software_control_mode(0)
        #self.ser.close()
        self.main_app.show_main_page('conference')


    # serial port 連線
    def connectionSerial(self):
        if not self.common.is_serial_connected():
            self.common.serial_port = self.common.on_ok(self.config.get("com_port", "COM1"))
            time.sleep(0.1)
            # 連線成功後更新按鈕
            self.connection.config(text="Serial Port已連線", fg="green")
            ## ***
            #self.common.camera_serial_port = self.common.connect_visca_serial(self.camera_config.get("com_port", "COM1"))
            mic_id = 63
            far_mic_id = self.common.decimal_to_hex(mic_id)
            # hex_command = f'81 01 04 3F 02 {far_mic_id} FF'
            # command_bytes = bytes.fromhex(hex_command)
            # self.common.serial_port.write(command_bytes)
            # time.sleep(0.3)  # 稍微等一下
            #for i in range(6, 0, -1):
            for i in range(1, 7):
                #mic_id += 1
                #far_mic_id = self.common.decimal_to_hex(mic_id)
                for j in range(2):
                    hex_command = f'8{str(i)} 01 04 3F 02 {far_mic_id} FF'
                    command_bytes = bytes.fromhex(hex_command)
                    self.common.serial_port.write(command_bytes)
                    time.sleep(0.05)
                #self.common.camera_serial_port.write(command_bytes)
                time.sleep(0.05)
                # Log
                if hasattr(self.common, 'debug_window') and self.common.debug_window:
                    self.common.debug_window.add_log(f"攝影機{str(i)} 指令已送出： {hex_command}")
            # 判斷攝影機和麥克風設定 (here)
            #if self.common.serial_port is None or self.camera_serial_port is None:
            #if not self.common.is_camera_serial_connected():
            #    return
            #time.sleep(1)
            self.start_listening()
        else:
            messagebox.showinfo("提醒", "Serial port 已經開啟")
            return
        # print("Serial port 開啟") if self.ser and self.ser.is_open else print("Serial port 尚未開啟")


    # 持續監聽Serial資料
    def start_listening(self):
        # 如果 serial port 尚未連線，直接跳出任務
        if not self.common.is_serial_connected():
        #if not self.common.is_serial_connected() or not self.common.is_camera_serial_connected():  (here)
            print("Serial port 尚未連線，無法執行監聽")
            self.frame.after(0, lambda: messagebox.showerror("錯誤", "尚未連線 MIC COM PORT，請先設定。"))
            return
        #elif not self.common.is_camera_serial_connected():
        #    print("Camera Serial port 尚未連線，無法執行監聽")
        #    self.frame.after(0, lambda: messagebox.showerror("錯誤", "尚未連線 Camera COM PORT，請先設定。"))
        #    return

        self.running = True  # 每次啟動監聽前先設定 running=True
        def listen_task():
            # 連線訊息
            print("開始監聽訊息...")
            if hasattr(self.common, 'debug_window') and self.common.debug_window:
                self.common.debug_window.add_log("開始監聽訊息...")

            #time_config = self.common.load_config('time')  # 載入設定
            #self.timer_seconds = time_config.get("secondValue", 0)
            #print(f'timer_seconds: {self.timer_seconds}')
            last_data = b''

            received_data_buffer = bytearray()
            while self.common.is_serial_connected() and self.running:
                try:
                    incoming = self.common.serial_port.read(1)  # 根據協定抓長度
                    print(f"len(incoming)={len(incoming)}")
                    if len(received_data_buffer) < 4:
                        received_data_buffer += incoming
                    else:
                        if len(incoming) > 0:
                            del received_data_buffer[0]
                            received_data_buffer += incoming
                    # print(f"len(received_data_buffer)={len(received_data_buffer)}  received_data_buffer = {received_data_buffer.hex(' ').upper()}")
                    if received_data_buffer and len(received_data_buffer) == 4:
                        # print(f'incoming: {received_data_buffer}   len: {len(received_data_buffer)}')
                        hex_msg = received_data_buffer.hex(' ').upper()
                        if hex_msg != last_data:  # 避免重複列印
                            #print(f'hex_msg: {hex_msg}')
                            last_data = hex_msg  # 更新紀錄
                            #if "EE EE" not in hex_msg:
                            print(f"*** 收到訊息：{hex_msg}   len: { len(hex_msg) }")
                            if hasattr(self.common, 'debug_window') and self.common.debug_window:
                                self.common.debug_window.add_log(f"收到訊息：{hex_msg}")

                            mic_id = self.common.getMicID(hex_msg)
                            # 取得mic_id
                            mic_item = next((item for item in self.mic_id_list if item.get("mic_id") == mic_id), None)
                            #print(f'mic_item: {mic_item}')
                            if not mic_item:
                                continue

                            # 目前mic_id的Type
                            mic_type = mic_item.get("type", 2)
                            #print(f'mic_type: {mic_type}')

                            # 取得 master mic_id
                            filtered_ids = [item.get('mic_id') for item in self.mic_id_list if item.get("type") == 1]

                            parts = hex_msg.split()
                            # 以下收到命令
                            #if "88 88" in hex_msg: # 優先按下
                            if len(parts) >= 4 and parts[2] == '88' and parts[3] == '88':
                                print(f'{mic_id} PRIOR')
                                # close other mic
                                # Master Label
                                print(f'---------------quere: {self.mic_id_queue}')
                                label = self.mic_timer_labels.get(mic_id)
                                #if label:
                                label.config(text="麥克風開啟", fg="blue")
                                # Clear other Device
                                print(f'***********quere: {self.mic_id_queue}')
                                sorted_queue = sorted(self.mic_id_queue, key=lambda x: int(x, 16), reverse=True)
                                for item in sorted_queue:
                                    if item != mic_id:
                                        print(f'+++++++++++quere item: {item} type={type(item)} len={len(item)}  mic_id={mic_id}  type={type(mic_id)} len={len(mic_id)}')
                                        #self.send_mic_command(item, 0)  # 關閉
                                        self.process_queue(item, 0)
                                        label = self.mic_timer_labels.get(item)
                                        if label:
                                            label.config(text="麥克風關閉", fg="red")
                                        self.timer_flags[item] = False  # 強制中止其他 mic 的倒數
                                        self.controlCamera(item)
                                        time.sleep(0.05)
                                    #else:
                                    #    self.controlCamera(mic_id)    
                                time.sleep(0.05)
                            #elif "38 38" in hex_msg: # 優先放開
                            elif len(parts) >= 4 and parts[2] == '38' and parts[3] == '38':
                                print(f'!!!{mic_id} master close, hex_msg: {hex_msg}')
                                label = self.mic_timer_labels.get(mic_id)
                                #if label:
                                label.config(text="麥克風關閉", fg="red")        

                                # Clear master
                                self.process_queue(mic_id, 0)
                                self.controlCamera(mic_id)
                                print(f'38 38 mic_id: {mic_id}')
                                #self.timer_flags[mic_id] = False  # 停止倒數
                                #self.send_mic_command(mic_id, 0)
                            #elif "AA AA" in hex_msg: # 開啟
                            elif len(parts) >= 4 and parts[2] == 'AA' and parts[3] == 'AA':
                                print(f'//// time_flag: {self.timer_flags.keys()}')

                                if str(mic_id) not in self.timer_flags_temp.keys() or self.timer_flags_temp[str(mic_id)] == False:
                                    # 第一階段：type==1 或 queue中非type==1未滿
                                    print(f'quere length: {len([mid for mid in self.mic_id_queue if mid not in filtered_ids])}')
                                    if mic_type == 1 or len([mid for mid in self.mic_id_queue if mid not in filtered_ids]) < self.queue_limit:
                                        print(f'{mic_id} open, hex_msg: {hex_msg}')
                                        self.send_mic_command(mic_id, 1)                                       
                                    else:
                                        self.send_mic_command(mic_id, 0)  # 關閉
                            #elif "33 33" in hex_msg:
                            elif len(parts) >= 4 and parts[2] == '33' and parts[3] == '33':
                                #print(f'{mic_id} close, hex_msg: {hex_msg}')
                                self.send_mic_command(mic_id, 0)
                                self.timer_flags[mic_id] = False  # 停止該 mic 的倒數
                                # Label
                                #label = self.mic_timer_labels.get(mic_id)
                                #if label:
                                #    label.config(text="麥克風關閉", fg="red")

                except Exception as e:
                    print(f"監聽錯誤：{e}")
                    #break
            print("停止監聽")

        threading.Thread(target=listen_task, daemon=True).start()


    # 更新倒數計時, timer
    def update_timer(self, micID):
        mic_item = next((item for item in self.mic_id_list if item.get("mic_id") == micID), None)
        if not mic_item or mic_item.get("type") == 1:
            return  # 主席不進行倒數

        label = self.mic_timer_labels.get(micID)
        if not label:
            return

        time_config = self.common.load_config('time')
        timer_seconds = time_config.get("secondValue", 0)
        seconds_left = timer_seconds
        #print(f'seconds_left: {seconds_left}')
        self.timer_flags[micID] = True

        def timer_task():
            nonlocal seconds_left
            self.timer_flags_temp[micID] = True
            while seconds_left >= 0 and self.timer_flags.get(micID, False):
                minutes = seconds_left // 60
                seconds = seconds_left % 60
                label.config(text=f"倒數：{minutes:02d}:{seconds:02d}", fg="blue")
                time.sleep(1)
                seconds_left -= 1

            if self.timer_flags.get(micID):
                label.config(text="麥克風關閉", fg="red")
                self.send_mic_command(micID, 0)
                

            self.timer_flags[micID] = False
            self.timer_flags_temp[micID] = False

        threading.Thread(target=timer_task, daemon=True).start()


    # 送出 mic 命令 (here)
    # param: mic_number: mic id, mode: 0 關閉, 1 開啟
    def send_mic_command(self, mic_number, mode):
        if not self.common.is_serial_connected():
            #messagebox.showwarning("未連線", "尚未連接 COM PORT，請先設定。")
            # Log
            if hasattr(self.common, 'debug_window') and self.common.debug_window:
                self.common.debug_window.add_log("尚未連接 COM PORT，請先設定。")
            print('尚未連接 COM PORT，請先設定。')
            return

        # 取得 master mic_id
        filtered_ids = [item.get('mic_id') for item in self.mic_id_list if item.get("type") == 1]
        print(f'master filtered_ids: {filtered_ids}')
        # all mic_id list
        #mic_ids = [item['mic_id'] for item in self.mic_id_list]
        #
        # Send CMD and queue
        hex_command = f"CC {mic_number} 99 99" if mode == 1 else f"CC {mic_number} 33 33"
        print(f'dddd hex_command: {hex_command}')
        mic_item = next((item for item in self.mic_id_list if item.get("mic_id") == mic_number), None)
        if mic_item is None:
            print(f"找不到 mic_id: {mic_number} 的設定")
            return

        # 目前mic 類型。佇列程序
        mic_type = mic_item.get("type", 2)

        try:

            if mode == 0:
                if mic_number in self.mic_id_queue:  # 先確認有在 queue 裡
                    self.mic_id_queue.remove(mic_number)
                    if mic_type == 2:
                        self.is_timer_running = False  
                    
                    # label    
                    label = self.mic_timer_labels.get(mic_number)
                    if label:
                        label.config(text="麥克風關閉", fg="red")    
            else:
                if not mic_number in self.mic_id_queue:  # 先確認有在 queue 裡
                    self.mic_id_queue.append(mic_number)
                    # startup timer
                    if mic_type == 2:
                        self.is_timer_running = True
                        self.update_timer(mic_number)
                    else:
                        # label    
                        label = self.mic_timer_labels.get(mic_number)
                        if label:
                            label.config(text="麥克風開啟", fg="blue")


            command_bytes = bytes.fromhex(hex_command)
            self.common.serial_port.write(command_bytes)
            time.sleep(0.05)
            self.common.serial_port.write(command_bytes)
        except ValueError as e:
            print(f"❌ 指令格式錯誤：{hex_command}")
            if hasattr(self.common, 'debug_window') and self.common.debug_window:
                self.common.debug_window.add_log(f"❌ 指令格式錯誤：{hex_command}")
            return
        if hasattr(self.common, 'debug_window') and self.common.debug_window:
            self.common.debug_window.add_log(f"指令已送出： {hex_command}")

        self.controlCamera(mic_number)



    # 處理佇列
    def process_queue(self, mic_number, mode):
        ## label
        label = self.mic_timer_labels.get(mic_number)
        if mode == 0:
            if mic_number in self.mic_id_queue:  # 先確認有在 queue 裡
                self.mic_id_queue.remove(mic_number)
        else:
            if not mic_number in self.mic_id_queue:  # 先確認有在 queue 裡
                self.mic_id_queue.append(mic_number)



    # 控制攝影機
    def controlCamera(self, mic_id):
        # 取得目前 mic 對應的 camera 設定
        specify_camera_item = next((item for item in self.mic_id_list if "mic_id" in item and item["mic_id"] == mic_id), None)
        if not specify_camera_item:
            print(f"❌ 找不到 mic_id: {mic_id} 的設定")
            return

        target_camera_id = specify_camera_item.get("camera_id")
        print(f'🎯 指定 camera_id: {target_camera_id}')

        # 找出所有與此 camera_id 綁定的 mic_id（含 mic_id 本身）
        camera_group = [item['mic_id'] for item in self.mic_id_list if item.get("camera_id") == target_camera_id and item.get("camera_id") != 0]
        print(f'📋 camera_group mic_ids: {camera_group}')

        # 找出目前佇列中與此 camera_id 對應的 mic_id
        matched = [mid for mid in self.mic_id_queue if mid in camera_group]
        print(f'✅ matched mic_ids in queue: {matched}')

        if matched:
            # 有其他相同 camera_id 的 mic，執行轉向至最後一個
            last_mic = matched[-1]
            print(f"🎥 執行轉向最後一個 mic_id: {last_mic}")
            camera_id = target_camera_id
            hex_command = f'8{str(camera_id)} 01 04 3F 02 {last_mic} FF'
        else:
            # 沒有使用此 camera 的 mic，回原位（mic_id: 63）
            hex_number = self.common.decimal_to_hex(63)
            print(f"↩️ 無對應 mic，攝影機 {target_camera_id} 回原位")
            hex_command = f'8{str(target_camera_id)} 01 04 3F 02 {hex_number} FF'

        command_bytes = bytes.fromhex(hex_command)
        self.common.serial_port.write(command_bytes)
        time.sleep(0.05)
        self.common.serial_port.write(command_bytes)
        print(f'📤 camera_cmd: {hex_command}')

        # Debug Log
        if hasattr(self.common, 'debug_window') and self.common.debug_window:
            self.common.debug_window.add_log(f"攝影機{target_camera_id} 指令已送出： {hex_command}")


##
## 進入Camera設定的頁面
class CameraMicMappingPage:
    def __init__(self, root, main_app):
        self.root = root
        self.main_app = main_app

        self.frame = tk.Frame(self.root)
        self.frame.pack(fill="both", expand=True)

        # 預設載入設定檔內容
        self.common = main_app.common

        self.camera_count_var = tk.IntVar()
        #self.selected_camera_var = tk.StringVar()
        self.camera_ids = []
        self.camera_mic_map = {}  # {camera_id: [mic_ids]}
        self.mic_vars = {}  # mic_id: tk.BooleanVar()
        self.save_button = None

        self.build_page()

    ## 以下是畫面
    # Camera配置頁面
    def build_page(self):
        if not os.path.exists( self.common.resource_path(CONFIG_MIC_FILE) ):
            messagebox.showwarning("警告", "請先進行數量設定")

        self.clear_frame()  # ← 新增這行
        self.create_top_buttons(self.frame)

        # 讀取Camera資料
        self.camera_config = self.common.load_config('camera')  # 載入設定
        # 標題
        tk.Label(self.frame, text="攝影機配對麥克風設定", font=("Arial", 16)).pack(pady=15)

        ## 攝影機數量
        #camera_option_top = tk.Frame(self.frame)
        #camera_option_top.pack(pady=5)

        # 攝影機數量
        """
        tk.Label(camera_option_top, text="攝影機數量：", font=("Arial", 12)).grid(row=0, column=0, sticky="e", padx=5,
                                                                                   pady=5)
        #self.camera_count_var = tk.IntVar(self.camera_config.get("camera_count", 0))
        self.camera_count_var.set(self.camera_config.get("camera_count", 1))
        count_dropdown = ttk.Combobox(
            camera_option_top, textvariable=self.camera_count_var,
            values=[str(i) for i in range(1, 7)],
            width=5, state="readonly"
        )
        """
        #count_dropdown.grid(row=0, column=1, sticky="w", padx=5, pady=5)
        #count_dropdown.bind("<<ComboboxSelected>>", self.update_camera_id_list)

        # COM PORT（序列埠）下拉
        """
        tk.Label(camera_option_top, text="COM PORT：", font=("Arial", 12)).grid(row=2, column=0, sticky="e", padx=5,
                                                                                 pady=5)
        self.com_port_var = tk.StringVar(value=self.camera_config.get("com_port", "COM1"))  # 預設值，可從 config 載入
        com_ports = [f"COM{i}" for i in range(1, 101)]
        com_dropdown = ttk.Combobox(
            camera_option_top, textvariable=self.com_port_var,
            values=com_ports, width=8, state="readonly"
        )
        """
        #com_dropdown.grid(row=2, column=1, sticky="w", padx=5)

        # 儲存 base config 按鈕
        #save_base_btn = tk.Button(self.frame, text="儲存攝影機基本設定", command=lambda: self.common.save_camera_base_config(self.camera_count_var.get(), self.com_port_var.get()) )
        #save_base_btn.pack(pady=10)

        # 分隔線
        #separator = tk.Frame(self.frame, height=1, bg="gray")
        #separator.pack(fill="x", pady=5)

        camera_option_bottom = tk.Frame(self.frame)
        camera_option_bottom.pack(pady=10)

        # 選擇攝影機
        self.selected_camera_var = tk.StringVar()
        #self.selected_camera_var.set("1")
        tk.Label(camera_option_bottom, text="選擇攝影機：", font=("Arial", 12)).grid(row=1, column=0, sticky="e", padx=5,
                                                                                   pady=2)
        self.camera_dropdown = ttk.Combobox(
            camera_option_bottom,
            textvariable=self.selected_camera_var,
            width=8, state="readonly"
        )
        self.camera_dropdown.grid(row=1, column=1, sticky="w", padx=5, pady=2)
        self.camera_dropdown['values'] = [str(i) for i in range(1, 7)]  # 加上這行
        self.selected_camera_var.set("1")
        self.camera_dropdown.bind("<<ComboboxSelected>>", self.update_mic_checkboxes)
        # Scrollable MIC checkbox 區域
        mic_scroll_container = tk.Frame(self.frame)
        mic_scroll_container.pack(fill="both", expand=True, padx=10, pady=3)

        mic_canvas = tk.Canvas(mic_scroll_container, height=130)
        mic_scrollbar = tk.Scrollbar(mic_scroll_container, orient="vertical", command=mic_canvas.yview)
        self.mic_scrollable_frame = tk.Frame(mic_canvas)

        self.mic_scrollable_frame.bind(
            "<Configure>", lambda e: mic_canvas.configure(scrollregion=mic_canvas.bbox("all"))
        )

        mic_canvas.create_window((0, 0), window=self.mic_scrollable_frame, anchor="nw")
        mic_canvas.configure(yscrollcommand=mic_scrollbar.set)
        mic_canvas.pack(side="left", fill="both", expand=True)
        mic_scrollbar.pack(side="right", fill="y")

        self.mic_check_frame = self.mic_scrollable_frame
        if os.path.exists( self.common.resource_path(CONFIG_MIC_FILE) ):
            self.generate_mic_checkboxes()
            # 儲存按鈕
            self.save_buttonsave_button = tk.Button(self.frame, text="儲存", width=12, command=lambda: self.common.save_camera_mic_mapping(self.selected_camera_var, self.mic_vars))
            self.save_buttonsave_button.pack(pady=10)
            #self.generate_mic_checkboxes()

    # TOP
    def create_top_buttons(self, parent):
        top_frame = tk.Frame(parent)
        top_frame.pack(fill="x", pady=5)

        # 右邊的按鈕區
        right_btn_frame = tk.Frame(top_frame)
        right_btn_frame.pack(side="right")

        tk.Button(right_btn_frame, text="離開", width=12, command=self.back_to_main).pack(side="right", padx=5)
        #tk.Button(right_btn_frame, text="Debug模式", width=12, fg="blue", command=self.common.open_debug_window).pack(side="right", padx=5)


    ## 以下函式
    # 清空畫面
    def clear_frame(self):
        for widget in self.frame.winfo_children():
            widget.destroy()

    # 回到主頁
    def back_to_main(self):
        #self.common.on_cancel('hide')  # 呼叫 CommonTool 裡的 on_cancel
        self.main_app.show_main_page('camera')


    # 產出 MIC 核取選單
    def generate_mic_checkboxes(self):
        mic_ids = self.load_mic_ids()
        for widget in self.mic_check_frame.winfo_children():
            widget.destroy()
        self.mic_vars = {}

        mic_config = self.common.load_config('mic')
        """
        for index in range(60):
            mic_id = f"{index + 1:02d}"
            row = index // 6
            col = index % 6
            var = tk.BooleanVar()
            chk = tk.Checkbutton(self.mic_check_frame, text=f"麥克風 {mic_id}", variable=var, font=("Arial", 11))
            chk.grid(row=row, column=col, padx=4, pady=5)
            self.mic_vars[mic_id] = var
        """
        for index, mic_id in enumerate(mic_ids):
            row = index // 5
            col = index % 5
            var = tk.BooleanVar()
            chk = tk.Checkbutton(self.mic_check_frame, text=f"麥克風 {self.common.hex_to_decimal(mic_id)}", variable=var, font=("Arial", 12))
            chk.grid(row=row, column=col, padx=15, pady=5)
            self.mic_vars[mic_id] = {"var": var, "widget": chk, "disabled": False}

        self.update_mic_checkboxes()


    # 載入MIC
    def load_mic_ids(self):
        config_file = self.common.resource_path(CONFIG_MIC_FILE)
        if os.path.exists( self.common.resource_path(config_file) ):
            config = self.common.load_config('mic')  # 載入設定
            return [item.get("mic_id") for item in config]
        #else:
        #    return [f"{i:02d}" for i in range(1, 11)]  # 預設10支Mic


    #
    def load_mic_selection(self, event=None):
        cam_id = self.selected_camera_var.get()
        selected = self.camera_mic_map.get(cam_id, [])

        for mic_id, var in self.mic_vars.items():
            var.set(mic_id in selected)


    # 更新核取選單
    def update_mic_checkboxes(self, event=None):
        selected_camera_id = self.selected_camera_var.get()
        if not selected_camera_id.isdigit():
            return
        selected_camera_id = int(selected_camera_id)

        mic_config = []
        if os.path.exists(self.common.resource_path(CONFIG_MIC_FILE)):
            with open(self.common.resource_path(CONFIG_MIC_FILE), "r", encoding="utf-8") as f:
                mic_config = json.load(f)

        for mic in mic_config:
            mic_id = mic.get("mic_id")
            assigned_camera = mic.get("camera_id", 0)
            if mic_id in self.mic_vars:
                var_info = self.mic_vars[mic_id]
                if assigned_camera == 0:
                    var_info["widget"].configure(state="normal")
                    var_info["var"].set(False)
                    var_info["disabled"] = False
                elif assigned_camera == selected_camera_id:
                    var_info["widget"].configure(state="normal")
                    var_info["var"].set(True)
                    var_info["disabled"] = False
                else:
                    var_info["widget"].configure(state="disabled")
                    var_info["var"].set(False)
                    var_info["disabled"] = True


##
## 進入FIFO設定的頁面
class FIFOSettingPage:
    def __init__(self, root, main_app):
        self.root = root
        self.main_app = main_app

        self.frame = tk.Frame(self.root)
        self.frame.pack(fill="both", expand=True)

        # 預設載入設定檔內容
        self.common = main_app.common
        self.mic_count_var1 = tk.IntVar()

        self.build_set_page()

    ## 以下是畫面
    # FIFO配置頁面
    def build_set_page(self):
        self.clear_frame()  # ← 新增這行
        self.create_top_buttons(self.frame)

        # 讀取MIC資料
        self.mic_config = self.common.load_config('queue')  # 載入設定
        print(self.mic_config.get("queue_limit_count", 0))
        # 標題
        tk.Label(self.frame, text="FIFO對麥克風設定", font=("Arial", 16)).pack(pady=15)

        ## 攝影機數量
        camera_option_top = tk.Frame(self.frame)
        camera_option_top.pack(pady=5)

        # 攝影機數量
        tk.Label(camera_option_top, text="限制麥克風數量：", font=("Arial", 12)).grid(row=0, column=0, sticky="e", padx=5, pady=5)
        #self.camera_count_var1 = tk.IntVar(self.camera_config.get("camera_count", 0))
        self.mic_count_var1.set( self.mic_config.get("queue_limit_count", 1) )
        count_dropdown = ttk.Combobox(
            camera_option_top, textvariable=self.mic_count_var1,
            values=[str(i) for i in range(1, 7)],
            width=5, state="readonly"
        )
        count_dropdown.grid(row=0, column=1, sticky="w", padx=5, pady=5)
        # 儲存 base config 按鈕 # , command=lambda: self.common.save_queue_limit_config(self.mic_count_var1.get())
        #save_base_btn = tk.Button(self.frame, text="儲存攝影機基本設定", command=lambda: self.common.save_camera_base_config(self.camera_count_var.get(), self.com_port_var.get()))
        save_base_btn = tk.Button(self.frame, text="儲存", width=12, command=lambda: self.common.save_queue_limit_config(self.mic_count_var1.get() ) )
        save_base_btn.pack(pady=10)


    ## 以下函式
    # 清空畫面
    def clear_frame(self):
        for widget in self.frame.winfo_children():
            widget.destroy()

    # 回到主頁
    def back_to_main(self):
        #self.common.on_cancel('hide')  # 呼叫 CommonTool 裡的 on_cancel
        self.main_app.show_main_page('queue_set')


    # TOP
    def create_top_buttons(self, parent):
        top_frame = tk.Frame(parent)
        top_frame.pack(fill="x", pady=5)

        # 右邊的按鈕區
        right_btn_frame = tk.Frame(top_frame)
        right_btn_frame.pack(side="right")

        tk.Button(right_btn_frame, text="離開", width=12, command=self.back_to_main).pack(side="right", padx=5)

##
## 進入FIFO會議的頁面
class FIFOConferencePage:
    def __init__(self, root, main_app):
        self.root = root
        self.main_app = main_app
        self.frame = tk.Frame(self.root)
        self.frame.pack(fill="both", expand=True)
        # 預設載入設定檔內容
        self.common = main_app.common
        # 以下連線com port
        self.config = self.common.load_config('base')  # 載入設定
        self.camera_config = self.common.load_config('camera')  # 載入設定
        # 取出主席ID
        self.mic_id_list = self.common.load_config('mic')
        self.master = next((item for item in self.mic_id_list if item['type'] == 1), self.mic_id_list[0])
        # 取得佇列限制長度
        self.config_queue = self.common.load_config('queue')
        self.queue_limit = self.config_queue.get('queue_limit_count', 0)
        self.mic_id_queue1 = []
        # 紀錄佇列第一個元素
        self.first_queue_element = None
        # self.ser = None       # serial port 連線
        self.running = False  # 讓監聽自己跳出 while 迴圈
        self.build_canference_page()

    ## 以下是畫面
    # FIFO配置頁面
    def build_canference_page(self):
        # 判斷 serial port 是否連線
        if not self.common.is_serial_connected():
            messagebox.showinfo("提醒", "Serial port 尚未開啟，請在右上方按下「Serial Port連線」按鈕。")

        self.clear_frame()  # ← 新增這行
        self.create_top_buttons(self.frame)

        # 標題
        tk.Label(self.frame, text="FIFO會議系統控制", font=("Arial", 16)).pack(pady=20)
        middle_frame = tk.Frame(self.frame)
        middle_frame.pack(pady=5)

        # 創建一個高度為 1 像素，背景色為灰色的 Frame 作為水平線
        separator = tk.Frame(self.frame, height=1, bg="gray").pack(fill="x", padx=5)  # fill="x" 使其水平填充可用寬度
        # 麥克風列表區塊
        canvas_frame = tk.Frame(self.frame)
        canvas_frame.pack(pady=15, fill="both", expand=True)

        # 建立 Canvas 和 Scrollbar
        canvas = tk.Canvas(canvas_frame, height=300)
        scrollbar = tk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        # 可捲動 Frame（內容）
        scrollable_frame = tk.Frame(canvas)

        # 建立 window 並靠左對齊 (anchor="nw")
        canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

        # 自動更新 scrollregion
        def update_scrollregion(event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        scrollable_frame.bind("<Configure>", update_scrollregion)

        mic_id_list = self.common.load_config('mic')  # 載入設定
        sorted_data = sorted(mic_id_list, key=lambda x: x['type'])  # 依 type 為1排序

        total_buttons = len(mic_id_list)
        buttons_per_row = 5
        # for i in range(total_buttons):
        self.mic_buttons = {}  # 加入這行
        # command=lambda: self.execDevice(item['mic_id'])
        for index, item in enumerate(sorted_data):
            btn = tk.Button(scrollable_frame, text=f"主席: 麥克風 { self.common.hex_to_decimal(item['mic_id']) }", width=15, fg="red") if item['type'] == 1 else tk.Button(scrollable_frame, text=f"麥克風 { self.common.hex_to_decimal(item['mic_id']) }", width=15)
            row = index // buttons_per_row
            col = index % buttons_per_row
            btn.grid(row=row, column=col, padx=10, pady=5)
            # 儲存按鈕參照
            self.mic_buttons[item['mic_id']] = btn

    ## 以下函式
    # 清空畫面
    def clear_frame(self):
        for widget in self.frame.winfo_children():
            widget.destroy()


    # 回到主頁
    def back_to_main(self):
        print("離開頁面，準備關閉執行緒...")
        self.running = False  # 讓監聽自己跳出 while 迴圈
        time.sleep(0.1)  # 稍微等一下（給 thread time 結束）
        # if self.common.camera_serial_port and self.common.camera_serial_port.is_open:
        #print(f'check port: {self.common.is_camera_serial_connected()}')
        if self.common.is_serial_connected():
            mic_id = 63
            for i in range(1, 7):
            #for i in range(6, 0, -1):
                for j in range(2):
                    # mic_id += 1
                    far_mic_id = self.common.decimal_to_hex(mic_id)
                    hex_command = f'8{str(i)} 01 04 3F 02 {far_mic_id} FF'
                    command_bytes = bytes.fromhex(hex_command)
                    #self.common.camera_serial_port.write(command_bytes)
                    self.common.serial_port.write(command_bytes)
                    time.sleep(0.05)
                time.sleep(0.05)    

            #self.common.camera_serial_port.close()  # 執行關閉攝影機 serial port
            #print(f'判斷式內 camera port: {self.common.camera_serial_port}')
            #print(f"checkclosecam = {checkclosecam}")
        time.sleep(0.1)
        self.common.on_cancel('show')  # 執行關閉麥克風 serial port
        #self.common.on_cancel('hide')  # 呼叫 CommonTool 裡的 on_cancel
        self.main_app.show_main_page('queue_conference')

    # TOP
    def create_top_buttons(self, parent):
        top_frame = tk.Frame(parent)
        top_frame.pack(fill="x", pady=5)

        # 右邊的按鈕區
        right_btn_frame = tk.Frame(top_frame)
        right_btn_frame.pack(side="right")
        # self.common.on_ok(self.config.get("com_port", "COM1")
        tk.Button(right_btn_frame, text="Debug模式", width=12, command=self.common.open_debug_window).pack(side="right", padx=5)
        self.exitout = tk.Button(right_btn_frame, text="離開", width=12, command=self.back_to_main).pack(side="right", padx=5)
        self.connection = tk.Button(right_btn_frame, text="Serial Port連線", width=12, command=self.connectionSerial)
        self.connection.pack(side="right", padx=5)
        #self.connection = tk.Button(right_btn_frame, text="Serial Port連線", width=12, command=self.connectionSerial).pack(side="right", padx=5)


    # serial port 連線
    def connectionSerial(self):
        #print(f"self.common.is_serial_connected()={self.common.is_serial_connected()}")
        if not self.common.is_serial_connected():
            self.common.serial_port = self.common.on_ok(self.config.get("com_port", "COM1"))
            time.sleep(0.1)
            # 連線成功後更新按鈕
            self.connection.config(text="Serial Port已連線", fg="green")
            ## ***
            #self.common.camera_serial_port = self.common.connect_visca_serial(self.camera_config.get("com_port", "COM1"))
            #print(f'camera port: {self.common.camera_serial_port}' )
            mic_id = 63
            far_mic_id = self.common.decimal_to_hex(mic_id)
            #hex_command = f'81 01 04 3F 02 {far_mic_id} FF'
            #command_bytes = bytes.fromhex(hex_command)
            #self.common.serial_port.write(command_bytes)
            #time.sleep(0.1)  # 稍微等一下
            for i in range(1, 7):
            #for i in range(6, 0, -1):
                #mic_id += 1
                for j in range(2):
                    hex_command = f'8{str(i)} 01 04 3F 02 {far_mic_id} FF'
                    command_bytes = bytes.fromhex(hex_command)
                    #self.common.camera_serial_port.write(command_bytes)
                    self.common.serial_port.write(command_bytes)
                    time.sleep(0.05)
                time.sleep(0.05)
                # Log
                if hasattr(self.common, 'debug_window') and self.common.debug_window:
                    self.common.debug_window.add_log(f"攝影機{str(i)} 指令已送出： {hex_command}")

            # 判斷攝影機和麥克風設定 (here)
            #if self.common.serial_port is None or self.camera_serial_port is None:
            #if not self.common.is_camera_serial_connected():
            #    return
            #time.sleep(1)
            self.start_listening()
        else:
            messagebox.showinfo("提醒", "Serial port 已經開啟")
            return

    # 持續監聽Serial資料
    def start_listening(self):
        # 如果 serial port 尚未連線，直接跳出任務
        if not self.common.is_serial_connected():
            # if not self.common.is_serial_connected() or not self.common.is_camera_serial_connected():  (here)
            print("Serial port 尚未連線，無法執行監聽")
            self.frame.after(0, lambda: messagebox.showerror("錯誤", "尚未連線 MIC COM PORT，請先設定。"))
            return
        #elif not self.common.is_camera_serial_connected():
        #    print("Camera Serial port 尚未連線，無法執行監聽")
        #    self.frame.after(0, lambda: messagebox.showerror("錯誤", "尚未連線 Camera COM PORT，請先設定。"))
        #    return

        self.running = True  # 每次啟動監聽前先設定 running=True

        def listen_task():
            # 連線訊息
            print("開始監聽訊息...")
            if hasattr(self.common, 'debug_window') and self.common.debug_window:
                self.common.debug_window.add_log("開始監聽訊息...")

            last_data = b''

            while self.common.is_serial_connected() and self.running:
                try:
                    incoming = self.common.serial_port.read(4)  # 根據協定抓長度
                    if incoming and len(incoming) == 4:
                        hex_msg = incoming.hex(' ').upper()
                        if hex_msg != last_data:  # 避免重複列印
                            # print(f"收到訊息：{hex_msg}")
                            last_data = hex_msg  # 更新紀錄
                            print(f"*** 收到訊息：{hex_msg}   len: {len(hex_msg)}")
                            if hasattr(self.common, 'debug_window') and self.common.debug_window:
                                self.common.debug_window.add_log(f"收到訊息：{hex_msg}")

                            mic_id = self.common.getMicID(hex_msg) # 取得CMD的ID
                            print(f'mic_id: {mic_id}')
                            parts = hex_msg.split()
                            # 以下收到命令
                            # if "88 88" in hex_msg: # 優先按下
                            if len(parts) >= 4 and parts[2] == '88' and parts[3] == '88':
                                print(f'{mic_id} PRIOR')
                                # 主席開啟
                                # self.send_mic_command(mic_id, 1)
                                btn = self.mic_buttons[mic_id]
                                mic_id_decimal = self.common.hex_to_decimal(mic_id)
                                btn.config(text=f"主席: 麥克風 {mic_id_decimal} 開啟中", fg="green", width=18)
                                #mic_ids = [item['mic_id'] for item in self.mic_id_list] # 取出綁定mic的所有ID值
                                print(f'mic_id_queue1: {self.mic_id_queue1}')
                                # 取得 master mic_id
                                filtered_ids = [item.get('mic_id') for item in self.mic_id_list if item.get("type") == 1]
                                #print(f'mic_id_queue1: {self.mic_id_queue1[:]}')
                                for micID in self.mic_id_queue1[:]:
                                    print(f'>>> mic_id: {micID}')
                                    if micID != mic_id:
                                        btn = self.mic_buttons[micID]
                                        #btn.config(text="麥克風關閉", fg="gray")
                                        btn.config(text=f"主席: 麥克風 {mic_id_decimal} 已關閉", fg="gray", width=18) if micID in filtered_ids else btn.config(text=f"麥克風 {mic_id_decimal} 已關閉", fg="gray")

                                        self.process_queue(micID, 0)
                                        self.controlCamera(micID) 
                                        #self.send_mic_command(micID, 0)
                                        time.sleep(0.05)

                                #time.sleep(0.05)
                            elif len(parts) >= 4 and parts[2] == '38' and parts[3] == '38':
                                print(f'{mic_id} master close, hex_msg: {hex_msg}')
                                btn = self.mic_buttons[mic_id]
                                btn.config(text=f"主席: 麥克風 {mic_id} 已關閉", fg="gray", width=18)                                
                                # 主席關閉
                                #self.send_mic_command(mic_id, 0)
                            elif len(parts) >= 4 and parts[2] == 'AA' and parts[3] == 'AA':
                                print(f'{mic_id} open, hex_msg: {hex_msg}')
                                self.send_mic_command(mic_id, 1)
                            elif len(parts) >= 4 and parts[2] == '33' and parts[3] == '33':
                                print(f'{mic_id} close, hex_msg: {hex_msg}')
                                #print(f'333 queue: {self.mic_id_queue1}')
                                self.send_mic_command(mic_id, 0)

                except Exception as e:
                    print(f"監聽錯誤：{e}")
                    #break
            print("停止監聽")

        threading.Thread(target=listen_task, daemon=True).start()


    # 送出 mic 命令 (here)
    # param: mic_number: mic id, mode: 0 關閉, 1 開啟
    def send_mic_command(self, mic_number, mode):

        def change_button(mic_number_tmp,tmp_mode, filtered_ids):
            #print(f"---> change_button = {mic_number_tmp} mode={tmp_mode}")
            #print(f"---> self.mic_buttons = {self.mic_buttons}")
            if mic_number_tmp in self.mic_buttons.keys():
                #print(f'555 Label mic_number_tmp: {mic_number_tmp}')
                # 判斷是否有 mic_id 為 '01' 的項目
                # found = any(item.get('mic_id') == mic_number for item in filtered)
                # found = any(item == mic_number for item in filtered_ids)
                btn = self.mic_buttons[mic_number_tmp]
                mic_id_decimal = self.common.hex_to_decimal(mic_number_tmp)
                # print(f'mic_id_decimal: {mic_id_decimal}')
                #print(f"btn={btn}")
                if tmp_mode == 1:
                    btn.config(text=f"主席: 麥克風 {mic_id_decimal} 開啟中", fg="green",
                               width=18) if mic_number_tmp in filtered_ids else btn.config(
                        text=f"麥克風 {mic_id_decimal} 開啟中", fg="green")
                else:
                    btn.config(text=f"主席: 麥克風 {mic_id_decimal} 已關閉", fg="gray",
                               width=18) if mic_number_tmp in filtered_ids else btn.config(
                        text=f"麥克風 {mic_id_decimal} 已關閉", fg="gray")

        if not self.common.is_serial_connected():
            #messagebox.showwarning("未連線", "尚未連接 COM PORT，請先設定。")
            # Log
            if hasattr(self.common, 'debug_window') and self.common.debug_window:
                self.common.debug_window.add_log("尚未連接 COM PORT，請先設定。")
            print('尚未連接 COM PORT，請先設定。')
            return

        # 取得 master mic_id
        filtered_ids = [item.get('mic_id') for item in self.mic_id_list if item.get("type") == 1]
        #print(f'master filtered_ids: {filtered_ids}')
        # all mic_id list
        #mic_ids = [item['mic_id'] for item in self.mic_id_list]
        #
        # Send CMD and queue
        hex_command = f"CC {mic_number} 99 99" if mode == 1 else f"CC {mic_number} 33 33"
        print(f'*** 指令已送出: {hex_command}')

        try:
            command_bytes = bytes.fromhex(hex_command)
            print(f'*** try 裡面 指令已送出: {hex_command}')
            self.common.serial_port.write(command_bytes)
            if mode == 0:
                if mic_number in self.mic_id_queue1:  # 先確認有在 queue 裡
                    print(f"從佇列移除: {mic_number}")
                    self.mic_id_queue1.remove(mic_number)
            else:
                if not mic_number in self.mic_id_queue1:  # 先確認有在 queue 裡
                    print(f"新增至佇列: {mic_number}")

                    ## 先判斷是否佇列已滿
                    if len(self.mic_id_queue1) >= self.queue_limit:  # 檢查佇列是否滿額度
                        print(f"11 self.mic_id_queue1={self.mic_id_queue1}")
                        self.first_queue_element = self.mic_id_queue1[0]
                        #print(f'取出第一個佇列: {self.first_queue_element}')
                        mic_to_remove = self.mic_id_queue1.pop(0)
                        print(f"22 self.mic_id_queue1={self.mic_id_queue1}")
                        print(f"🔁 佇列滿，移除並關閉: {mic_to_remove}")
                        hex_command1 = f"CC {mic_to_remove} 33 33"
                        time.sleep(0.2)
                        command_bytes1 = bytes.fromhex(hex_command1)

                        change_button(mic_to_remove, 0, filtered_ids)

                        self.common.serial_port.write(command_bytes1)

                        print(f'*** 移除佇列已滿第一個指令已送出: {hex_command1}')
                        print(f'取出第一個佇列: {self.first_queue_element}')
                        time.sleep(0.1)
                        #執行攝影機
                        self.controlCamera(self.first_queue_element)

                    self.mic_id_queue1.append(mic_number)

        except ValueError as e:
            print(f"❌ 指令格式錯誤：{hex_command}")
            if hasattr(self.common, 'debug_window') and self.common.debug_window:
                self.common.debug_window.add_log(f"❌ 指令格式錯誤：{hex_command}")
            return

        if hasattr(self.common, 'debug_window') and self.common.debug_window:
            self.common.debug_window.add_log(f"指令已送出： {hex_command}")

        ## 以下處理標簽
        change_button(mic_number,mode, filtered_ids)

        print(f'12345 mic_id_queue1: {self.mic_id_queue1}')
        # 設定設影機
        self.controlCamera(mic_number)



    # 處理佇列
    def process_queue(self, mic_number, mode):
        ## label
        #label = self.mic_timer_labels.get(mic_number)
        if mode == 0:
            if mic_number in self.mic_id_queue1:  # 先確認有在 queue 裡
                self.mic_id_queue1.remove(mic_number)
        else:
            if not mic_number in self.mic_id_queue1:  # 先確認有在 queue 裡
                self.mic_id_queue1.append(mic_number)    



    # 控制攝影機
    def controlCamera(self, mic_id):
        # 取得目前 mic 對應的 camera 設定
        specify_camera_item = next((item for item in self.mic_id_list if "mic_id" in item and item["mic_id"] == mic_id), None)
        if not specify_camera_item:
            print(f"❌ 找不到 mic_id: {mic_id} 的設定")
            return

        target_camera_id = specify_camera_item.get("camera_id")
        print(f'🎯 指定 camera_id: {target_camera_id}')

        # 找出所有與此 camera_id 綁定的 mic_id（含 mic_id 本身）
        camera_group = [item['mic_id'] for item in self.mic_id_list if item.get("camera_id") == target_camera_id and item.get("camera_id") != 0]
        print(f'📋 camera_group mic_ids: {camera_group}')

        # 找出目前佇列中與此 camera_id 對應的 mic_id
        matched = [mid for mid in self.mic_id_queue1 if mid in camera_group]
        print(f'✅ matched mic_ids in queue: {matched}')

        if matched:
            # 有其他相同 camera_id 的 mic，執行轉向至最後一個
            last_mic = matched[-1]
            print(f"🎥 執行轉向最後一個 mic_id: {last_mic}")
            camera_id = target_camera_id
            hex_command = f'8{str(camera_id)} 01 04 3F 02 {last_mic} FF'
        else:
            # 沒有使用此 camera 的 mic，回原位（mic_id: 63）
            hex_number = self.common.decimal_to_hex(63)
            print(f"↩️ 無對應 mic，攝影機 {target_camera_id} 回原位")
            hex_command = f'8{str(target_camera_id)} 01 04 3F 02 {hex_number} FF'

        command_bytes = bytes.fromhex(hex_command)
        self.common.serial_port.write(command_bytes)
        time.sleep(0.05)
        self.common.serial_port.write(command_bytes)
        print(f'📤 camera_cmd: {hex_command}')

        # Debug Log
        if hasattr(self.common, 'debug_window') and self.common.debug_window:
            self.common.debug_window.add_log(f"攝影機{target_camera_id} 指令已送出： {hex_command}")



##
## 進入FIFO設定的頁面
class TimerSettingPage:
    def __init__(self, root, main_app):
        self.root = root
        self.main_app = main_app

        self.frame = tk.Frame(self.root)
        self.frame.pack(fill="both", expand=True)

        # 預設載入設定檔內容
        self.common = main_app.common
        self.mic_count_var1 = tk.IntVar()

        self.build_set_page()

    ## 以下是畫面
    # 倒數計時配置頁面
    def build_set_page(self):
        self.clear_frame()  # ← 新增這行
        self.create_top_buttons(self.frame)

        # 讀取MIC資料
        self.mic_config = self.common.load_config('timer_limit')  # 載入設定
        print(self.mic_config.get("queue_limit_count", 1))
        # 標題
        tk.Label(self.frame, text="倒數計時對麥克風設定", font=("Arial", 16)).pack(pady=15)

        ## 攝影機數量
        camera_option_top = tk.Frame(self.frame)
        camera_option_top.pack(pady=5)

        # 攝影機數量
        tk.Label(camera_option_top, text="限制麥克風數量：", font=("Arial", 12)).grid(row=0, column=0, sticky="e", padx=5, pady=5)
        #self.camera_count_var1 = tk.IntVar(self.camera_config.get("camera_count", 0))
        self.mic_count_var1.set( self.mic_config.get("queue_limit_count", 1) )
        count_dropdown = ttk.Combobox(
            camera_option_top, textvariable=self.mic_count_var1,
            values=[str(i) for i in range(1, 7)],
            width=5, state="readonly"
        )
        count_dropdown.grid(row=0, column=1, sticky="w", padx=5, pady=5)
        # 儲存 base config 按鈕 # , command=lambda: self.common.save_queue_limit_config(self.mic_count_var1.get())
        #save_base_btn = tk.Button(self.frame, text="儲存攝影機基本設定", command=lambda: self.common.save_camera_base_config(self.camera_count_var.get(), self.com_port_var.get()))
        save_base_btn = tk.Button(self.frame, text="儲存", width=12, command=lambda: self.common.save_timer_queue_limit_config(self.mic_count_var1.get() ) )
        #save_base_btn = tk.Button(self.frame, text="儲存", width=12)
        save_base_btn.pack(pady=10)


    ## 以下函式
    # 清空畫面
    def clear_frame(self):
        for widget in self.frame.winfo_children():
            widget.destroy()

    # 回到主頁
    def back_to_main(self):
        #self.common.on_cancel('hide')  # 呼叫 CommonTool 裡的 on_cancel
        self.main_app.show_main_page('timer_set')


    # TOP
    def create_top_buttons(self, parent):
        top_frame = tk.Frame(parent)
        top_frame.pack(fill="x", pady=5)

        # 右邊的按鈕區
        right_btn_frame = tk.Frame(top_frame)
        right_btn_frame.pack(side="right")

        tk.Button(right_btn_frame, text="離開", width=12, command=self.back_to_main).pack(side="right", padx=5)


##
## 進入Debug頁面
class ConferenceDebugWindow:
    def __init__(self, root, parent_page):
        self.parent_page = parent_page  # 傳入 entryConferencePage
        self.window = tk.Toplevel(root)
        self.window.title("會議系統 Debug 訊息")
        self.window.geometry("600x400")

        # 主框架
        frame = tk.Frame(self.window)
        frame.pack(fill='both', expand=True)

        # Text區
        self.text_area = tk.Text(frame, state='disabled', wrap='none')
        self.text_area.pack(side='left', fill='both', expand=True)

        # Scrollbar
        scrollbar = tk.Scrollbar(frame, command=self.text_area.yview)
        scrollbar.pack(side='right', fill='y')
        self.text_area.config(yscrollcommand=scrollbar.set)

        # 清空按鈕
        clear_btn = tk.Button(self.window, text="清空訊息", command=self.clear_log)
        clear_btn.pack(pady=5)

        # 關閉時的行為
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)

    def add_log(self, message):
        timestamp = time.strftime('%H:%M:%S')
        formatted_message = f"[{timestamp}] {message}\n"  # 加上換行

        self.text_area.config(state='normal')
        self.text_area.insert('end', formatted_message)
        self.text_area.config(state='disabled')
        self.text_area.see('end')


    def clear_log(self):
        self.text_area.config(state='normal')
        self.text_area.delete('1.0', tk.END)
        self.text_area.config(state='disabled')


    def on_close(self):
        # 關閉視窗時清除內容，並通知 parent_page
        self.clear_log()
        self.parent_page.debug_window = None
        self.window.destroy()

    def load_mic_ids(self):
        #config_file = "mic_config.json"
        if os.path.exists(self.common.resource_path(CONFIG_MIC_FILE)):
            with open(self.common.resource_path(CONFIG_MIC_FILE), "r", encoding="utf-8") as f:
                config = json.load(f)
                return [item.get("mic_id") for item in config]
        else:
            return [f"{i:02d}" for i in range(1, 11)]  # 預設10支Mic

    def clear_frame(self):
        for widget in self.frame.winfo_children():
            widget.destroy()

    def destroy(self):
        self.frame.destroy()


# 主程式入口
if __name__ == "__main__":
    root = tk.Tk()
    app = ConferenceApp(root)
    root.protocol("WM_DELETE_WINDOW", app.close_window)  # 關閉視窗時執行 app.on_close()
    root.mainloop()
