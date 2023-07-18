import sys
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QAction, QWidget, QDialog, QLineEdit, QVBoxLayout, QPushButton, QLabel, QMessageBox, QErrorMessage
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt
from telegram import Bot, Update, error
from telegram.ext import Updater, CommandHandler, CallbackContext
import os
import sys
import threading
import time
import json
import subprocess
import winreg

settings = {
    'token': '',
    'vpnname' : '',
    'vpnuser' : '',
    'vpnpass' : '',
    'wifiname' : '',
    'wifipass' : ''
}    

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
        self.label_vpnname = QLabel("Enter your VPN name")
        self.vpnname_input = QLineEdit(self)
        self.label_vpnuser = QLabel("Enter your VPN user name")
        self.vpnuser_input = QLineEdit(self)
        self.label_vpnpass = QLabel("Enter your VPN password")
        self.vpnpass_input = QLineEdit(self)
        self.label_wifiname = QLabel("Enter your Wi-Fi name")
        self.wifiname_input = QLineEdit(self)
        self.label_wifipass = QLabel("Enter your Wi-Fi password")
        self.wifipass_input = QLineEdit(self)

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
        self.on_accept(self.token_input.text())
        super(SettingsDialog, self).accept()

    
class SystemTrayIcon(QSystemTrayIcon):
    def __init__(self, icon, parent=None):
        QSystemTrayIcon.__init__(self, icon, parent)
        menu = QMenu(parent)

        self.MAX_RETRIES = 10  # The number of retries before giving up
        self.RETRY_DELAY = 1  # The delay between each retry in seconds
        self.retries = 0

        self.bot_thread = None
        self.token = ''        
        self.vpnname = ''
        self.vpnuser = ''
        self.vpnpass = ''

        self.wifiname = ''        
        self.wifipass = ''

        self.running = threading.Event()
        self.running.set()

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
            if "No Connections" in vpn_output or "연결 안 됨" in vpn_output:
                vpn_status = "VPN is disconnected"
            else:
                vpn_status = "VPN is connected"
        except Exception as e:             
            vpn_status = "Cannot check VPN status"

        # Check Wi-Fi status
        try:
            wifi_output = subprocess.check_output("netsh interface show interface", shell=True).decode('cp949')
            if "Disconnected" in wifi_output:
                wifi_status = "Wi-Fi is disconnected"
            else:
                wifi_status = "Wi-Fi is connected"
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
        command = 'rasdial gmscvpn gmscvpn3 gmscvpn3'
        os.system(command)
        self.showMessage("Techtoast", "VPN has been turned ON")
        self.safe_send_message(update, 'VPN has been turned ON')
    
    def stop_vpn(self, update: Update, context: CallbackContext) -> None:
        command = 'rasdial gmscvpn /DISCONNECT'
        os.system(command)        
        self.showMessage("Techtoast", "VPN has been turned OFF")
        self.safe_send_message(update, 'VPN has been turned OFF')

    def start_wifi(self, update: Update, context: CallbackContext) -> None:
        command = 'netsh wlan connect name=FREE_KUMC_GURO_Wifi'
        os.system(command)
        self.showMessage("Techtoast", "Wi-Fi has been connected")
        self.safe_send_message(update, 'Wi-Fi has been connected')

    def stop_wifi(self, update: Update, context: CallbackContext) -> None:
        command = 'netsh wlan disconnect'
        os.system(command)
        self.showMessage("Techtoast", "Wi-Fi has been disconnected")
        self.safe_send_message(update, 'Wi-Fi has been disconnected')

def main(image):
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    w = SystemTrayIcon(QIcon(image))
    sys.exit(app.exec_())

if __name__ == '__main__':
    main(resource_path('techtoast.png'))
