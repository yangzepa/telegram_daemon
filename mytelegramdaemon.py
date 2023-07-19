import sys
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QAction, QDialog, QLineEdit, QVBoxLayout, QPushButton, QLabel, QComboBox
from PyQt5.QtGui import QIcon
from telegram import Update, error
from telegram.ext import Updater, CommandHandler, CallbackContext
import os
import threading
import time
import json
import subprocess
import winreg
import re

settings = {
    'token': '',
    'vpnname' : '',
    'vpnuser' : '',
    'vpnpass' : '',
    'wifiname' : '',
    'wifipass' : ''
}    

import winreg

def get_vpn_list():
    registry_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Internet Settings\\Connections')
    i = 0
    vpn_list = []
    while True:
        try:
            vpn_name = winreg.EnumValue(registry_key, i)
            vpn_list.append(vpn_name)
            i += 1
        except WindowsError:
            break
    return vpn_list


def get_wifi_list():
    result = subprocess.run(['netsh', 'wlan', 'show', 'networks'], capture_output=True, text=True)
    wifi_list = result.stdout.split('\n')
    wifi_list = [line.split(':')[1][1:] for line in wifi_list if 'SSID' in line]

    output = subprocess.check_output(['netsh', 'wlan', 'show', 'profiles']).decode('utf-8', 'ignore')
    wifi_names = re.findall(r': (.*)\r', output)

    # find match between wifi_list and wifi_names
    wifi_list2 = []
    for i in range(len(wifi_list)):
        for j in range(len(wifi_names)):
            if wifi_list[i] == wifi_names[j]:
                wifi_list2.append(wifi_list[i])

    # get password for each wifi
    passwordlist = []
    for i in range(len(wifi_list2)):
        try:
            results = subprocess.check_output(['netsh', 'wlan', 'show', 'profile', wifi_list2[i], 'key=clear']).decode('utf-8', 'ignore').split('\n')
            results = [b.split(':')[1][1:-1] for b in results if 'Key Content' in b or '키 콘텐츠' in b]
            try:
                passwordlist.append(results[0])
            except IndexError:
                passwordlist.append('<NO PW Needed>')
        except subprocess.CalledProcessError:
            passwordlist.append('<NO PW FOUND>')

        
    return wifi_list2, passwordlist



def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
        
    return os.path.join(base_path, relative_path)

class SettingsDialog(QDialog):
    def __init__(self, on_accept, parent=None):
        super(SettingsDialog, self).__init__(parent)
        self.on_accept = on_accept
        #self.setAttribute(Qt.WA_DeleteOnClose, False)
        layout = QVBoxLayout(self)
        self.label_token = QLabel("Enter your token")
        self.token_input = QLineEdit(self)
        self.label_vpnname = QLabel("Select your VPN")
        
        #dropdown menu for vpn list
        self.vpnname_input = QComboBox(self)
        self.label_vpnuser = QLabel("Enter your VPN user name")
        self.vpnuser_input = QLineEdit(self)
        self.label_vpnpass = QLabel("Enter your VPN password")
        self.vpnpass_input = QLineEdit(self)

        
        self.label_wifiname = QLabel("Select your Wi-Fi name")
        self.wifiname_input = QComboBox(self)
        
        self.label_wifipass = QLabel("password of selected Wi-Fi")        
        self.wifipass_input = QLineEdit(self)

        vpn_list = get_vpn_list()        
        vpn_list2 = [vpn_list[i][0] for i in range(len(vpn_list))]
        self.vpnname_input.addItems(vpn_list2)
        self.wifi_list, self.passwordlist = get_wifi_list() 
        self.wifiname_input.addItems(self.wifi_list)       

        # read settings from settings.json
        try:
            with open('settings.json', 'r') as f:
                settings = json.load(f)
                self.token_input.setText(settings['token'])
                # find index of vpnname in vpn_list2
                try:
                    idx = vpn_list2.index(settings['vpnname'])
                    self.vpnname_input.setCurrentIndex(idx)
                except ValueError:
                    pass
                self.vpnuser_input.setText(settings['vpnuser'])
                self.vpnpass_input.setText(settings['vpnpass'])
                # find index of wifiname in wifi_list
                try:
                    idx = self.wifi_list.index(settings['wifiname'])
                    self.wifiname_input.setCurrentIndex(idx)
                except ValueError:
                    pass
                self.wifipass_input.setText(settings['wifipass'])

        except (FileNotFoundError, json.JSONDecodeError):
            self.wifiname_input.currentIndexChanged.connect(self.update_wifi_password)
            tempidx = self.wifiname_input.currentIndex()
            if(tempidx != -1):
                self.update_wifi_password(self.wifiname_input.currentIndex())

        self.save_button = QPushButton("Save")
        layout.addWidget(self.label_token)
        layout.addWidget(self.token_input)
        layout.addWidget(self.label_vpnname)
        layout.addWidget(self.vpnname_input)
        layout.addWidget(self.label_vpnuser)
        layout.addWidget(self.vpnuser_input)
        layout.addWidget(self.label_vpnpass)
        layout.addWidget(self.vpnpass_input)
        layout.addWidget(self.label_wifiname)
        layout.addWidget(self.wifiname_input)
        layout.addWidget(self.label_wifipass)
        layout.addWidget(self.wifipass_input)

        layout.addWidget(self.save_button)
        self.setWindowIcon(QIcon(resource_path('techtoast.png')))
        self.setWindowTitle("Settings")
        self.save_button.clicked.connect(self.accept)
    
    def accept(self):
        token = self.token_input.text()
        vpn_name = self.vpnname_input.currentText()
        vpn_user = self.vpnuser_input.text()
        vpn_pass = self.vpnpass_input.text()
        wifi_name = self.wifiname_input.currentText()
        wifi_pass = self.wifipass_input.text()

        self.on_accept(token, vpn_name, vpn_user, vpn_pass, wifi_name, wifi_pass)

        super(SettingsDialog, self).accept()


        super(SettingsDialog, self).accept()

    def update_wifi_password(self, index):
        # edit the value of the self.wifipass_input to the password of selected wifi
        self.wifipass_input.setText(self.passwordlist[index])

        #self.wifipass_input = self.passwordlist[index]


    
class SystemTrayIcon(QSystemTrayIcon):
    def __init__(self, icon, parent=None):
        QSystemTrayIcon.__init__(self, icon, parent)
        menu = QMenu(parent)

        self.MAX_RETRIES = 10  # The number of retries before giving up
        self.RETRY_DELAY = 1  # The delay between each retry in seconds
        self.retries = 0
        self.running = threading.Event()
        self.running.set()

        self.bot_thread = None
        self.token = ''        
        self.vpnname = ''
        self.vpnuser = ''
        self.vpnpass = ''

        self.wifiname = ''        
        self.wifipass = ''

        self.settings_dialog = None #SettingsDialog(None)
        self.settings_action = QAction("Settings", triggered=self.open_settings)
        self.exit_action = QAction("Exit", triggered=self.exit)

        try:
            with open('settings.json', 'r') as f:
                settings = json.load(f)
                self.token = settings['token']
                self.vpnname = settings['vpnname']
                self.vpnuser = settings['vpnuser']
                self.vpnpass = settings['vpnpass']
                self.wifiname = settings['wifiname']
                self.wifipass = settings['wifipass']                

        except (FileNotFoundError, json.JSONDecodeError):
            # settings.json 파일이 없거나, 파일이 유효한 JSON이 아닌 경우
            # 빈 토큰으로 설정하고 설정 창을 열기            
            self.open_settings()

        # manually starting functions are disabled for now:
        # this function should be re-developed since we cannot use Updater and Context in this class
        # since it is simple function; re-developing is not a big deal

        #self.start_vpn_action = QAction("Start VPN", triggered=self.start_vpn)
        #self.stop_vpn_action = QAction("Stop VPN", triggered=self.stop_vpn)
        #self.start_wifi_action = QAction("Start WiFi", triggered=self.start_wifi)
        #self.stop_wifi_action = QAction("Stop WiFi", triggered=self.stop_wifi)        

        #menu.addAction(self.start_vpn_action)
        #menu.addAction(self.stop_vpn_action)
        #menu.addAction(self.start_wifi_action)
        #menu.addAction(self.stop_wifi_action)  
              
        menu.addAction(self.settings_action)
        menu.addAction(self.exit_action)

        self.updater = None
        self.setContextMenu(menu)    
        self.show()
        self.init_telegram_bot()        
        
    def open_settings(self):
        self.settings_dialog = SettingsDialog(self.on_settings_dialog_accept)
        self.settings_dialog.token_input.setText(self.token)
        self.settings_dialog.exec_()

    def on_settings_dialog_accept(self, token, vpnname, vpnuser, vpnpass, wifiname, wifipass):
        self.token = token
        self.vpnname = vpnname
        self.vpnuser = vpnuser
        self.vpnpass = vpnpass
        self.wifiname = wifiname
        self.wifipass = wifipass
        
        # 토큰을 settings.json 파일에 저장
        settings = {'token': self.token, 
                    'vpnname': self.vpnname,
                    'vpnuser': self.vpnuser,
                    'vpnpass': self.vpnpass,
                    'wifiname': self.wifiname,
                    'wifipass': self.wifipass                    
                    }
        with open('settings.json', 'w') as f:
            json.dump(settings, f)
        self.init_telegram_bot()


    def exit(self):
        self.running.clear()
        QApplication.instance().quit()  # Terminate the PyQt event loop

    def init_telegram_bot(self):
        
        if self.bot_thread is not None and self.bot_thread.is_alive():
            self.running.clear()
            self.bot_thread.join()  # Wait for the thread to stop        
        
        def run_bot():
            try:
                self.updater = Updater(self.token, use_context=True)            
            except Exception as e:                
                if(str(e) == 'Invalid token'):                    
                    self.showMessage("Techtoast","Invalid Token")
                    return                
            
            dp = self.updater.dispatcher

            dp.add_handler(CommandHandler("test", self.test))
            dp.add_handler(CommandHandler("stopdaemon", self.stopdaemon))
            dp.add_handler(CommandHandler("startvpn", self.start_vpn))
            dp.add_handler(CommandHandler("stopvpn", self.stop_vpn))
            dp.add_handler(CommandHandler("startwifi", self.start_wifi))
            dp.add_handler(CommandHandler("stopwifi", self.stop_wifi))
            dp.add_handler(CommandHandler("status", self.check_status))
            
            # getting user chat id for only to send the 'init' message? maybe not efficient. 
            # so blocking this function for now, maybe later.
            #chat_id = <user_chat_id>
            #self.updater.bot.send_message(chat_id=chat_id, text="Telegram Daemon executed")
            
            try:
                self.updater.start_polling()  
            except error.Unauthorized:
                self.showMessage("Techtoast", "Unauthorized token")
                return

            self.showMessage("Techtoast", "Telegram Daemon executed")

            while self.running.is_set():
                try:
                    time.sleep(0.1)                    
                except error.NetworkError:
                    # If a network error happens, we wait a bit and retry
                    time.sleep(self.RETRY_DELAY)
                    self.retries += 1
                    # If we retried too much, we give up and raise an exception
                    if self.retries >= self.MAX_RETRIES:
                        raise Exception("Cannot connect to network after multiple retries.")
            
            self.updater.stop()       

        self.bot_thread = threading.Thread(target=run_bot)
        self.bot_thread.start()

    def safe_send_message(self, update: Update, text: str) -> None:
        for i in range(self.MAX_RETRIES):
            try:
                update.message.reply_text(text)
                break
            except (error.TimedOut, error.NetworkError):
                if i < self.MAX_RETRIES - 1:
                    time.sleep(self.RETRY_DELAY)
                else:
                    raise

    def check_status(self, update: Update, context: CallbackContext) -> None:
        # Check VPN status
        try:
            vpn_output = subprocess.check_output("rasdial", shell=True).decode('cp949')
            if "연결 대상" in vpn_output or "Connected" in vpn_output:
                results = [b for b in vpn_output if '연결 대상' not in b or 'Connected' not in b]
                results = results[0] # 첫번째 줄 정보만 땡기게
                #self.showMessage("Techtoast", f"VPN to {results} is already connected")
                vpn_status = f"VPN : Connected to {results}"
            else:
                vpn_status = "VPN : disconnected"            
        except Exception:             
            vpn_status = "Cannot check VPN status"

        # Check Wi-Fi status
        try:
            
            ret = subprocess.check_output("netsh wlan show interfaces", shell=True).decode('cp949')
            if "Connected" in ret or "연결됨" in ret:
                # check line-by-line
                ret = ret.split('\n')
                results = [line.split(':')[1][1:] for line in ret if 'SSID' in line and 'BSSID' not in line][0].split('\r')[0]            
                wifi_status =  f"Wi-Fi : Connected to {results}"
            else:                
                wifi_status = "Wi-Fi : disconnected"
        except Exception:
            wifi_status = "Cannot check Wi-Fi status"

        # Send status
        update.message.reply_text(f"{vpn_status}\n{wifi_status}")

    def test(self, update: Update, context: CallbackContext) -> None:
        self.showMessage("Techtoast", "test message received")
        self.safe_send_message(update, 'test message received')

    def stopdaemon(self, update: Update, context: CallbackContext) -> None:        
        self.safe_send_message(update, 'daemon stop requested')        
        self.exit()
        
    def start_vpn(self, update: Update, context: CallbackContext) -> None:
        # check vpn connection
        ret = subprocess.check_output("rasdial", shell=True).decode('cp949')
        if "연결 대상" in ret or "Connected" in ret:
            results = [b for b in ret if '연결 대상' not in b or 'Connected' not in b]
            results = results[0]
            self.showMessage("Techtoast", f"VPN to {results} is already connected")
            self.safe_send_message(update, f"VPN to {results} is already connected")
            return

        command = f'rasdial {self.vpnname} {self.vpnuser} {self.vpnpass}'
        ret = subprocess.check_output(command, shell=True).decode('cp949')
        if "명령을 완료했습니다." in ret or "Command completed successfully" in ret:
            time.sleep(0.5)
            ret = subprocess.check_output("rasdial", shell=True).decode('cp949')
            if self.vpnname in ret:
                self.showMessage("Techtoast", f"VPN to {self.vpnname} has been turned ON")
                self.safe_send_message(update, f"VPN to {self.vpnname} has been turned ON")
            else:
                self.showMessage("Techtoast", f"not connected to {self.vpnname}")
                self.safe_send_message(update, f"not connected to {self.vpnname}")
        else:
            self.showMessage("Techtoast", f"not connected to {self.vpnname}")
            self.safe_send_message(update, f"not connected to {self.vpnname}")            
    
    def stop_vpn(self, update: Update, context: CallbackContext) -> None:
        command = 'rasdial gmscvpn /DISCONNECT'
        ret = subprocess.check_output(command, shell=True).decode('cp949')
        if "명령을 완료했습니다." in ret or "Command completed successfully" in ret:
            time.sleep(0.5)
            ret = subprocess.check_output("rasdial", shell=True).decode('cp949')
            if "No Connections" in ret or "연결 안 됨" in ret:
                self.showMessage("Techtoast", "VPN has been turned OFF")
                self.safe_send_message(update, 'VPN has been turned OFF')
            else:
                self.showMessage("Techtoast", "problem with disconnection")
                self.safe_send_message(update, "problem with disconnection")
        else:
            self.showMessage("Techtoast", "problem with disconnection")
            self.safe_send_message(update, "problem with disconnection")
        

    def start_wifi(self, update: Update, context: CallbackContext) -> None:
        # check wifi connection
        ret = subprocess.check_output("netsh wlan show interfaces", shell=True).decode('cp949')
        if "Connected" in ret or "연결됨" in ret:
            # check line-by-line
            rt = ret.split('\n')
            results = [line.split(':')[1][1:] for line in rt if 'SSID' in line and 'BSSID' not in line][0].split('\r')[0]            
            self.showMessage("Techtoast", f"Wi-Fi is already connected to {results}")
            self.safe_send_message(update, f"Wi-Fi is already connected to {results}")
            return

        if(self.wifipass == '<NO PW Needed>' or self.wifipass == '<NO PW FOUND>'):
            command = f'netsh wlan connect name={self.wifiname}'
        else:
            command = f'netsh wlan connect name={self.wifiname} ssid={self.wifiname} key={self.wifipass}'
        
        ret = subprocess.check_output(command, shell=True).decode('cp949')
        # check the return value of os.system is properly connected
        # return texts are in korean "연결 요청을 완료했습니다."
        if "Connection request was completed" in ret or  "연결 요청을 완료했습니다." in ret:
            time.sleep(0.5) # wait for 0.5 sec
            # check connection via netsh wlan show interfaces
            ret = subprocess.check_output("netsh wlan show interfaces", shell=True).decode('cp949')
            if "Connected" in ret or "연결됨" in ret:
                self.showMessage("Techtoast", f"Wi-Fi connection to {self.wifiname} has been connected")
                self.safe_send_message(update, f"Wi-Fi connection to {self.wifiname} has been connected")
            else:
                self.showMessage("Techtoast", f"not connected to {self.wifiname}")
                self.safe_send_message(update, f"not connected to {self.wifiname}")
        else:
            self.showMessage("Techtoast", f"not connected to {self.wifiname}")
            self.safe_send_message(update, f"not connected to {self.wifiname}")



    def stop_wifi(self, update: Update, context: CallbackContext) -> None:
        command = 'netsh wlan disconnect'
        ret = subprocess.check_output(command, shell=True).decode('cp949')
        if "연결 끊기 요청을 완료했습니다." in ret or "The disconnect request was completed successfully" in ret: 
            time.sleep(0.5) # wait for 0.5 sec
            ret = subprocess.check_output("netsh wlan show interfaces", shell=True).decode('cp949')
            if "Disconnected" in ret or "연결되지 않음" in ret:              
                self.showMessage("Techtoast", "Wi-Fi has been disconnected")
                self.safe_send_message(update, 'Wi-Fi has been disconnected')
            else:
                self.showMessage("Techtoast", "problem with disconnection")
                self.safe_send_message(update, "problem with disconnection")
        else:
            self.showMessage("Techtoast", "problem with disconnection")
            self.safe_send_message(update, "problem with disconnection")

def main(image):
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    w = SystemTrayIcon(QIcon(image))
    sys.exit(app.exec_())

if __name__ == '__main__':
    main(resource_path('techtoast.png'))
