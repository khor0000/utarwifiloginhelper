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

        # Embed and set custom app icon (32x32 PNG)
        icon_b64 = "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"
        try:
            app_icon = tk.PhotoImage(data=icon_b64)
            self.root.iconphoto(True, app_icon)
        except:
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

def main():
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
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