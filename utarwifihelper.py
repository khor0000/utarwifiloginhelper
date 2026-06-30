#!/usr/bin/env python3
"""
UTAR WiFi Full Auto-Login
- Scans for 'utarwifi' SSID
- Connects to it (open network)
- Performs captive portal login
"""

import subprocess
import platform
import re
import time
import requests
from urllib.parse import urljoin, urlparse
import sys
import json
import os
import threading
import pywifi
from pywifi import const
import urllib3
import tkinter as tk
from tkinter import messagebox
import ctypes
import webbrowser

# Fix blurriness on high-DPI screens
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except:
    pass

# Suppress insecure request warnings from captive portal redirects
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ================== GUI Login Window ==================
class UtarLoginWindow:
    def __init__(self, callback, error_msg=None):
        self.callback = callback
        self.result = None
        self.root = tk.Tk()
        self.root.title("Welcome to UTAR Wireless Network")
        
        # Exact dimensions from UTAR portal CSS
        window_width = 360
        window_height = 440
        self.root.geometry(f"{window_width}x{window_height}")
        self.root.configure(bg="white")
        self.root.resizable(False, False)

        # Ensure it shows up in Alt+Tab and Taskbar
        # Set window icon using embedded Base64 PNG data of Concept 1 (Transparent Background)
        try:
            self.app_icon_data = """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"""
            self.app_icon = tk.PhotoImage(data=self.app_icon_data)
            self.root.iconphoto(True, self.app_icon)
        except Exception:
            pass

        # Center the window
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2)
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")

        self.log_var = tk.StringVar()
        self.mode = "login"
        self.setup_ui(error_msg)

    def setup_ui(self, error_msg):
        # 1. Header Tab Section
        self.header_frame = tk.Frame(self.root, bg="white", height=50)
        self.header_frame.pack(fill="x")
        self.header_frame.pack_propagate(False)
        tk.Frame(self.root, height=1, bg="#dddddd").pack(fill="x")

        tab_item = tk.Frame(self.header_frame, bg="white")
        tab_item.pack(expand=True, fill="y")
        tk.Label(tab_item, text="Sign in to UTARWIFI.", font=("Microsoft Yahei", 12), bg="white", fg="#1a1a1a").pack(side="top", pady=(12, 0))
        tk.Frame(tab_item, height=2, bg="#1D4B9E", width=160).pack(side="bottom")

        # 2. Body Frame (This will contain either login or progress)
        self.body_frame = tk.Frame(self.root, bg="white", width=312, height=320)
        self.body_frame.pack(pady=(20, 0))
        self.body_frame.pack_propagate(False)

        # Login UI Container
        self.login_container = tk.Frame(self.body_frame, bg="white")
        
        # Progress UI Container
        self.progress_container = tk.Frame(self.body_frame, bg="white")
        self.log_label = tk.Label(
            self.progress_container,
            textvariable=self.log_var,
            font=("Microsoft Yahei", 9),
            bg="white",
            fg="#444444",
            justify="center",
            wraplength=300
        )
        self.log_label.pack(expand=True, fill="both", pady=(50, 10))

        self.retry_btn = tk.Button(
            self.progress_container,
            text="Retry Connection",
            font=("Microsoft Yahei", 9, "bold"),
            bg="#1D4B9E",
            fg="white",
            activebackground="#2e5fb5",
            relief="flat",
            cursor="hand2",
            pady=8,
            padx=20
        )
        # Hidden by default
        
        # 3. Footer Section (Git link & Disclaimer)
        self.footer = tk.Label(
            self.root,
            text="Open Source on GitHub • Developed by @khor0000\nNot affiliated with UTAR",
            font=("Microsoft Yahei", 7),
            bg="white",
            fg="#999999",
            cursor="hand2",
            justify="center"
        )
        self.footer.pack(side="bottom", pady=(0, 15))
        self.footer.bind("<Button-1>", lambda e: webbrowser.open("https://github.com/khor0000/utarwifiloginhelper"))
        
        def on_enter(e):
            self.footer.config(fg="#1D4B9E", font=("Microsoft Yahei", 7, "underline"))
        def on_leave(e):
            self.footer.config(fg="#999999", font=("Microsoft Yahei", 7))
            
        self.footer.bind("<Enter>", on_enter)
        self.footer.bind("<Leave>", on_leave)

        self.build_login_ui(error_msg)

    def build_login_ui(self, error_msg):
        # Clear existing login UI if any
        for widget in self.login_container.winfo_children():
            widget.destroy()

        tk.Label(
            self.login_container, 
            text="Please login with UTAR username and password", 
            font=("Microsoft Yahei", 8), 
            bg="white", 
            fg="#666666"
        ).pack(anchor="w", pady=(0, 15))

        if error_msg:
            err_frame = tk.Frame(self.login_container, bg="#FFF4F4", bd=1, highlightthickness=1, highlightbackground="#f9e5e5")
            err_frame.pack(fill="x", pady=(0, 10))
            tk.Label(err_frame, text=error_msg, font=("Microsoft Yahei", 8), bg="#FFF4F4", fg="#CC5555", pady=3).pack()

        self.user_entry = self.create_utar_entry(self.login_container, "Login ID")
        self.pass_entry = self.create_utar_entry(self.login_container, "Password", show="\u25cf")
        
        self.root.bind('<Return>', lambda e: self.submit())

        login_btn = tk.Button(
            self.login_container,
            text="Log In",
            font=("Microsoft Yahei", 10, "bold"),
            bg="#1D4B9E",
            fg="white",
            activebackground="#2e5fb5",
            relief="flat",
            cursor="hand2",
            command=self.submit,
            height=1,
            pady=8
        )
        login_btn.pack(fill="x", pady=(20, 0))

    def show_login(self, error_msg=None):
        self.progress_container.pack_forget()
        if error_msg:
            self.build_login_ui(error_msg)
        self.login_container.pack(fill="both", expand=True)
        self.mode = "login"
        self.root.update()

    def show_progress(self, initial_msg="Starting..."):
        self.login_container.pack_forget()
        self.retry_btn.pack_forget() # Hide retry on fresh start
        self.progress_container.pack(fill="both", expand=True)
        self.log_var.set(initial_msg)
        self.mode = "progress"
        self.root.update()

    def show_retry(self, msg):
        self.log_var.set(msg)
        self.retry_btn.pack(pady=20)
        self.root.update()

    def create_utar_entry(self, parent, label_text, show=None):
        li_frame = tk.Frame(parent, bg="white", bd=0, highlightthickness=1, highlightbackground="#cccccc")
        li_frame.pack(fill="x", pady=5)
        
        char = "\U0001f464" if "ID" in label_text else "\U0001f512"
        tk.Label(li_frame, text=char, bg="white", fg="#aaaaaa", font=("Segoe UI Symbol", 10)).pack(side="left", padx=(12, 0))

        entry = tk.Entry(li_frame, font=("Microsoft Yahei", 8), bg="white", relief="flat", insertbackground="#1D4B9E")
        entry.pack(side="left", fill="x", expand=True, padx=8, pady=6)
        
        if show: entry._actual_show = show
        entry.insert(0, label_text)
        entry.config(fg="#999999")
        
        def on_focus_in(e):
            if entry.get() == label_text:
                entry.delete(0, tk.END)
                entry.config(fg="black")
                if hasattr(entry, '_actual_show'): entry.config(show=entry._actual_show)
        def on_focus_out(e):
            if not entry.get():
                if hasattr(entry, '_actual_show'): entry.config(show="")
                entry.insert(0, label_text)
                entry.config(fg="#999999")

        entry.bind("<FocusIn>", on_focus_in)
        entry.bind("<FocusOut>", on_focus_out)
        return entry

    def submit(self):
        username = self.user_entry.get().strip()
        password = self.pass_entry.get().strip()
        
        if username == "Login ID" or password == "Password" or not username or not password:
            messagebox.showerror("Input Error", "Please enter your Login ID and Password.")
            return
            
        self.result = (username, password)
        self.show_progress("Verifying...")

    def close(self):
        self.root.destroy()

    def get_result(self):
        self.root.mainloop()
        return self.result

    def update_log(self, text):
        self.root.after(0, lambda: self.log_var.set(text))


# ================== RC4 encryption (matching portal) ==================
def rc4_encrypt(key: str, plaintext: str) -> str:
    """RC4 encryption returning hex string."""
    key_bytes = [ord(c) for c in key]
    sbox = list(range(256))
    j = 0
    for i in range(256):
        j = (j + sbox[i] + key_bytes[i % len(key_bytes)]) & 0xFF
        sbox[i], sbox[j] = sbox[j], sbox[i]

    out = []
    i = j = 0
    for ch in plaintext:
        i = (i + 1) & 0xFF
        j = (j + sbox[i]) & 0xFF
        sbox[i], sbox[j] = sbox[j], sbox[i]
        k = sbox[(sbox[i] + sbox[j]) & 0xFF]
        cipher_byte = ord(ch) ^ k
        out.append(f"{cipher_byte:02x}")
    return "".join(out)


# ================== Platform‑specific Wi‑Fi control ==================
def get_current_ssid() -> str | None:
    """Return currently connected SSID or None."""
    try:
        wifi = pywifi.PyWiFi()
        ifaces = wifi.interfaces()
        if not ifaces:
            return None
            
        iface = ifaces[0]
        if iface.status() == const.IFACE_CONNECTED:
            # On Windows, pywifi doesn't always provide the SSID of the active connection easily.
            # We'll try netsh first as it's faster if it works.
            system = platform.system()
            if system == "Windows":
                try:
                    out = subprocess.check_output(
                        ["netsh", "wlan", "show", "interfaces"],
                        universal_newlines=True, stderr=subprocess.DEVNULL
                    )
                    for line in out.splitlines():
                        if "SSID" in line and "BSSID" not in line:
                            parts = line.split(":", 1)
                            if len(parts) == 2:
                                return parts[1].strip()
                except:
                    pass
        return None
    except Exception:
        return None


def scan_and_connect(target_ssid: str, log_callback=None) -> bool:
    """Scan for SSID using pywifi, if found, connect to it (open network)."""
    def log(msg):
        if log_callback:
            log_callback(msg)
        else:
            print(msg)

    log(f"Scanning for '{target_ssid}'...")
    
    try:
        wifi = pywifi.PyWiFi()
        ifaces = wifi.interfaces()
        if not ifaces:
            log("No WiFi hardware detected.")
            return False
            
        iface = ifaces[0]
        
        # Check if WiFi is disabled/off
        if iface.status() == const.IFACE_INACTIVE:
            log("WiFi is OFF. Attempting to enable...")
            subprocess.run(["netsh", "interface", "set", "interface", "name=Wi-Fi", "admin=enabled"], capture_output=True)
            time.sleep(2)
        
        # Trigger scan
        iface.scan()
        time.sleep(3) # Wait for scan results
        
        scan_results = iface.scan_results()
        found = False
        for network in scan_results:
            try:
                # Some SSIDs might have weird encodings
                ssid = network.ssid
                if ssid == target_ssid:
                    found = True
                    break
            except:
                continue
        
        profile = pywifi.Profile()
        profile.ssid = target_ssid
        profile.auth = const.AUTH_ALG_OPEN
        profile.akm.append(const.AKM_TYPE_NONE)
        profile.cipher = const.CIPHER_TYPE_NONE
        
        # Remove existing profiles for the same SSID to avoid conflicts
        iface.remove_all_network_profiles()
        tmp_profile = iface.add_network_profile(profile)
        
        iface.connect(tmp_profile)
        
        # Wait for connection
        timeout = 15
        start_time = time.time()
        while time.time() - start_time < timeout:
            if iface.status() == const.IFACE_CONNECTED:
                log(f"  Successfully connected to '{target_ssid}'.")
                time.sleep(2) # Extra time for DHCP
                return True
            time.sleep(1)
            
        log("  Connection timed out.")
        return False
        
    except Exception as e:
        log(f"  WiFi tool error: {e}")
        # Fallback to netsh if pywifi fails
        log("  Using 'netsh' to connect...")
        if platform.system() == "Windows":
            try:
                # Try to enable WiFi first via netsh just in case
                subprocess.run(["netsh", "interface", "set", "interface", "name=Wi-Fi", "admin=enabled"], capture_output=True)
                time.sleep(2)
                subprocess.run(["netsh", "wlan", "connect", f"name={target_ssid}"], capture_output=True, check=True)
                time.sleep(5)
                return True
            except:
                log(f"[!] Error: Could not connect to '{target_ssid}'. Please make sure you are in range and WiFi is turned on.")
                return False
        return False


# ================== Internet Connectivity Check ==================
def check_internet() -> bool:
    """Check if we have real internet access using Google's 204 service."""
    try:
        # A status code of 204 means we have direct internet access.
        # Captive portals will either redirect (302) or return a login page (200).
        resp = requests.get("http://connectivitycheck.gstatic.com/generate_204", timeout=5, allow_redirects=False)
        return resp.status_code == 204
    except Exception:
        return False


# ================== Captive portal detection & login ==================
def detect_portal_url() -> str:
    """Get the actual login page URL using HTTP redirects with retries."""
    test_urls = [
        "http://connectivitycheck.gstatic.com/generate_204",
        "http://www.msftconnecttest.com/redirect",
        "http://captive.apple.com/hotspot-detect.html",
        "http://203.0.144.1/generate_204",
        "http://203.0.113.1/generate_204",
    ]
    
    # Try multiple times to account for DHCP delay
    for attempt in range(5):
        if attempt > 0:
            time.sleep(3)
            
        session = requests.Session()
        session.max_redirects = 5
        session.verify = False

        for url in test_urls:
            try:
                # Check for 302 redirect
                resp = session.get(url, timeout=5, allow_redirects=False)
                if resp.status_code in [302, 301] and "Location" in resp.headers:
                    loc = resp.headers["Location"]
                    if "/ac_portal/" in loc:
                        # Ensure it's an absolute URL
                        if loc.startswith("/"):
                            parsed = urlparse(url)
                            loc = f"{parsed.scheme}://{parsed.netloc}{loc}"
                        return loc
                
                # Check for meta-refresh or script redirects in 200 responses
                resp = session.get(url, timeout=5, allow_redirects=True)
                if "/ac_portal/" in resp.url and "pc.html" in resp.url:
                    return resp.url
            except Exception:
                continue
                
    raise RuntimeError("Could not connect to UTAR login page. Are you in range of UTAR WiFi?")


def login(portal_url: str, username: str, password: str) -> bool:
    """Submit credentials to the portal."""
    parsed = urlparse(portal_url)
    base = f"{parsed.scheme}://{parsed.netloc}/ac_portal/"
    login_url = urljoin(base, "login.php")

    sess = requests.Session()
    sess.verify = False
    # Get initial cookies
    try:
        sess.get(portal_url, timeout=10)
    except Exception:
        pass

    rckey = str(int(time.time() * 1000))
    encrypted_pwd = rc4_encrypt(rckey, password)

    payload = {
        "opr": "pwdLogin",
        "userName": username,
        "pwd": encrypted_pwd,
        "auth_tag": rckey,
        "rememberPwd": "0",
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Content-Type": "application/x-www-form-urlencoded",
        "Referer": portal_url,
    }

    resp = sess.post(login_url, data=payload, headers=headers, timeout=15)
    try:
        data = resp.json()
    except Exception:
        print("Login failed: Server did not return JSON.")
        return False

    if data.get("success"):
        if data.get("action") == "location" and data.get("location"):
            final = data["location"]
            print(f"  Following final redirect: {final}")
            try:
                sess.get(final, timeout=10)
            except Exception as e:
                print(f"  Note: Failed to follow redirect ({e}), but login was successful.")
        return True
    else:
        print(f"  Login error: {data.get('msg', 'Unknown error')}")
        return False


# ================== Main ==================
def save_config(path, username, password, ssid):
    try:
        with open(path, "w") as f:
            json.dump({
                "username": username,
                "password": password,
                "target_ssid": ssid
            }, f, indent=4)
    except Exception as e:
        print(f"Error saving config: {e}")

    # Locate config.json relative to the executable (sys.argv[0]) when compiled,
    # or next to the script (__file__) when running raw.
    try:
        if sys.argv[0]:
            exe_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        else:
            exe_dir = os.path.dirname(os.path.abspath(__file__))
    except:
        exe_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(exe_dir, "config.json")
    config = {}
    gui = None
    
    # Load configuration
    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                config = json.load(f)
        except Exception as e:
            print(f"Error loading config.json: {e}")

    TARGET_SSID = config.get("target_ssid", "utarwifi")
    USERNAME = config.get("username")
    PASSWORD = config.get("password")

    def run_logic():
        nonlocal USERNAME, PASSWORD, portal
        
        # 0. Check if internet already works
        if check_internet():
            log_progress("[✓] Internet is active.")
            time.sleep(1)
            gui.root.after(0, gui.close)
            return

        # 1. Connect to WiFi
        current = get_current_ssid()
        if current != TARGET_SSID:
            if not scan_and_connect(TARGET_SSID, log_callback=log_progress):
                log_progress("Could not connect. Please make sure WiFi is turned on and you are in range.")
                gui.root.after(0, lambda: gui.show_retry("Could not connect.\nPlease make sure WiFi is turned on\nand you are in range."))
                return
            else:
                log_progress("Waiting for network...")
                # Dynamic wait: Check for connectivity every second for up to 10 seconds
                for _ in range(10):
                    if check_internet():
                        break
                    try:
                        # Try a quick portal detection check
                        detect_portal_url()
                        break
                    except:
                        pass
                    time.sleep(1)

        # 2. Detect portal URL
        log_progress("Detecting portal...")
        try:
            portal = detect_portal_url()
        except RuntimeError as e:
            if check_internet():
                log_progress("[✓] Internet is active.")
                time.sleep(1)
                gui.root.after(0, gui.close)
                return
            err_msg = str(e)
            log_progress(f"Error: {err_msg}")
            gui.root.after(0, lambda: gui.show_retry(f"Error: {err_msg}"))
            return

        # 3. Perform login
        log_progress("Logging in...")
        if login(portal, USERNAME, PASSWORD):
            time.sleep(2)
            if check_internet():
                log_progress("[✓] Login successful!")
                save_config(config_path, USERNAME, PASSWORD, TARGET_SSID)
                time.sleep(1)
                gui.root.after(0, gui.close)
            else:
                log_progress("[!] Verification failed.")
                gui.root.after(0, lambda: gui.show_login(error_msg="Login failed. Check credentials."))
        else:
            log_progress("[✗] Invalid credentials.")
            gui.root.after(0, lambda: gui.show_login(error_msg="Invalid credentials."))

    # Always show the window
    gui = UtarLoginWindow(None)
    portal = None

    def start_worker():
        gui.retry_btn.pack_forget() # Hide retry when working
        threading.Thread(target=run_logic, daemon=True).start()

    gui.retry_btn.config(command=start_worker)

    # We need a custom way to handle the submit from the UI
    def on_gui_submit():
        nonlocal USERNAME, PASSWORD
        res = gui.result
        if res:
            USERNAME, PASSWORD = res
            save_config(config_path, USERNAME, PASSWORD, TARGET_SSID)
            start_worker()
    
    # Override the submit behavior to start worker instead of quitting mainloop
    # This must happen before mainloop() and regardless of the initial state
    gui.submit = lambda: [gui.real_submit(), on_gui_submit()]
    gui.real_submit = UtarLoginWindow.submit.__get__(gui, UtarLoginWindow)

    # If missing credentials, show Login UI first
    if not USERNAME or not PASSWORD:
        gui.show_login()
    else:
        # If we have credentials, skip login UI and show progress immediately
        gui.show_progress("Checking internet...")
        gui.root.after(100, start_worker)

    def log_progress(text):
        print(text)
        if gui:
            gui.update_log(text)

    # Start the GUI
    gui.root.mainloop()


if __name__ == "__main__":
    main()