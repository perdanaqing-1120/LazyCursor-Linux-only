# **LazyCursor 🖱️⌨️**

LazyCursor is a kernel-level keyboard-to-mouse controller for Linux. This program allows you to control the mouse cursor, perform clicks, and scroll seamlessly using only your keyboard.

Unlike conventional mouse emulator programs (such as pyautogui or xdotool), LazyCursor interacts directly with Linux's /dev/input (evdev). This makes it **100% immune to Wayland security restrictions** and prevents input "leaks" to background application windows (making it incredibly safe and stable for modern KDE Plasma & GNOME environments).

## **✨ Key Features**

* **Wayland & X11 Safe:** Runs at the kernel level, tricking the OS into recognizing it as a genuine physical mouse.  
* **Exclusive Keyboard Grabbing:** When active, arrow key inputs are exclusively captured for cursor movement. No more background web pages or applications scrolling unintentionally while moving the cursor\!    
* **RAM Usage:** (\<20MB) Designed to run flawlessly as a Systemd daemon with extremely low RAM usage.

## **🎮 Shortcuts Guide**

| Shortcut | Action |
| :---- | :---- |
| Ctrl \+ M | **Toggle LazyCursor Mode (Active/Inactive)** |
| Arrow Keys | Move cursor |
| Shift \+ Arrow | Move slower (-5 speed) |
| Ctrl \+ Left | Left Click |
| Ctrl \+ Right | Right Click |
| Alt \+ Up | Scroll Up |
| Alt \+ Down | Scroll Down |
| Ctrl \+ Up | Increase base sensitivity |
| Ctrl \+ Down | Decrease base sensitivity |
| Ctrl \+ H | Open help terminal (View all shortcuts) |

## **🛠️ Prerequisites**

* Linux operating system (Tested on Debian 13 KDE Plasma Wayland and Arch Linux).  
* Python 3.x  
* sudo (root) privileges.

## **🚀 Installation & Autostart Setup (Systemd)**

To make LazyCursor run automatically every time your computer boots up, follow these steps:

**1\. Clone the Repository and Create a Virtual Environment**

git clone \[https://github.com/YOUR\_USERNAME/LazyCursor.git\](https://github.com/YOUR\_USERNAME/LazyCursor.git)  
cd LazyCursor  
python3 \-m venv .venv  
sudo .venv/bin/pip install evdev

**2\. Create a Systemd Service File**

Open your terminal and create a new service file:

sudo nano /etc/systemd/system/lazycursor.service

Paste the following configuration (Adjust /path/to/LazyCursor to your actual folder path, for example /home/perdana/perdara/LazyCursor):

\[Unit\]  
Description=LazyCursor Auto-Reload Controller  
After=multi-user.target

\[Service\]  
Type=simple  
User=root  
WorkingDirectory=/path/to/LazyCursor  
ExecStart=/path/to/LazyCursor/.venv/bin/python3 /path/to/LazyCursor/main.py  
Restart=always  
RestartSec=1

\[Install\]  
WantedBy=multi-user.target

**3\. Enable and Start the Service**

Run the following sequence of commands to reload, enable, and start the service:

sudo systemctl daemon-reload  
sudo systemctl enable lazycursor.service  
sudo systemctl start lazycursor.service

Now you can simply press Ctrl \+ M anywhere to start using LazyCursor\!

## **📝 Modification Notes**

Thanks to the *Hot-Reload* feature, if you want to change shortcuts or base speed, simply edit the main.py file and save it. The background service will automatically apply your new configuration instantly.
