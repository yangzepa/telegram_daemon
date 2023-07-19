# telegram_daemon
- currently working on it from time to time (Jan 18, 2023)
- Draft 0.8 version 

## Purpose
This is a Windows Tray bar-based utility, developed to manage VPN or Wifi connections to remote computers for diverse purposes, including but not limited to remote access to a PC within an internal intranet network. The application was constructed using Python and converted into an executable file using Pyinstaller for easy deployment. A unique feature of this software is its integration with a Telegram bot, which allows users to relay messages directly to the program. This tool has been designed for convenience, offering an efficient way to handle various connectivity-related tasks.

## Requirement
- Basically this is Windows software. developed and tested in windows 10.
- Software needs Admin authority for getting the VPN and Wifi information, and handling.
- **you need to make your own telegram bot via botfather.**
you can make your own bot via this reference https://core.telegram.org/bots/tutorial
we need the **token** of the bot. 
token patterns are vary; however it will shape like <chat ID of the bot>:<Some random ascii-like texts>

## Execution
you can download the exe file from [here](https://github.com/yangzepa/telegram_daemon/blob/2caa6acdc8016df5154c5ecf7b90e2587ec860ab/dist/mytelegramdaemon.exe), which is in the dist folder of above. 

<img src="https://github.com/yangzepa/telegram_daemon/blob/453a22896c2017dac90316464dd418da99e8d42a/readme_images/Settings.png" width="200">

in First execution, you can see the settings screen since we don't have the tokens entered into it.
all the informations are saved in settings.json file (not encoded yet; we can solve it later)

- **token** : can be acquired from telegram bot via botfather.
- **VPN** : your VPN connection setting should be done before use in Windows network setting. 
If your VPN settings were made before, then the name of the VPN will show up on drop-down menu.
- **VPN user name** : username and password method is used in this version.
- **VPN password** : username and password method is used in this version.
- **Wifi Name** : target Wifi connection needs to be made before use in Windows network setting.
If your Wifi were connected before AND it is searchable in current location, then the name of the VPN will show up on drop-down menu.
we're using windows Wifi Profile, so you need to connect to it at least once.

After saving the setting, notification message will show up with Tray-bar icon.

<img src="https://github.com/yangzepa/telegram_daemon/blob/f5cacced25069d7676821d3cc29aa66768794972/readme_images/Traybar.png" width="200">
<img src="https://github.com/yangzepa/telegram_daemon/blob/f5cacced25069d7676821d3cc29aa66768794972/readme_images/Alert1.png" width="200">

And, you can type in the below commands into bot chat room, and the function will be executed.
<img src="https://github.com/yangzepa/telegram_daemon/blob/f5cacced25069d7676821d3cc29aa66768794972/readme_images/Telegram_bot_window.png" width="400">

## commands
- **/status** : show the VPN or Wifi has connected or not.
- **/startwifi** : start wifi connection to selected wifi
- **/stopwifi** : stop wifi connection
- **/startvpn** : start vpn connection to selected vpn server
- **/stopvpn** : stop vpn connection
- */stopdaemon* : (debug purpose) stop the daemon execution
- */test* : testmessage send

## Todo list : 
- VPN Selection (done)
- Wifi Selection (done)
- Detailed configure windows (currently it has bug) (done)
- password/token security (json --> environment set) 
- build command optimization (exe file size)