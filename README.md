# UTAR WiFi Auto-Login Helper

A lightweight, automated captive portal login utility for Universiti Tunku Abdul Rahman (UTAR) wireless network (`utarwifi`). It scans, connects, and logs in automatically using your credentials stored securely on your local machine.

---

## Features

- **Auto-Scan & Connect:** Automatically scans for and connects to the open `utarwifi` network.
- **Captive Portal Detection:** Detects the UTAR login portal automatically.
- **Secure Local Storage:** Keeps your credentials locally in `config.json` and encrypts your password via RC4 before sending it to the UTAR login portal. **Your login details are never shared or sent to any external server.**
- **Clean Tkinter GUI:** High-DPI aware, clean login interface.
- **Background Execution:** Closes automatically once internet connection is established.

---

## How to Use (Recommended)

1. Download the latest compiled **`utarwifihelper.exe`** from the [Releases](https://github.com/khor0000/utarwifiloginhelper/releases) section.
2. Place the `.exe` in a dedicated folder on your computer.
3. Run `utarwifihelper.exe`.
4. Enter your UTAR credentials on the first run. The helper will save it to a local `config.json` in the same directory.
5. In the future, you can simply run `utarwifihelper.exe` or add it to your Windows startup folder, and it will log you in automatically in the background without prompting for credentials!

---

## Running from Source (Python)

If you prefer to run it manually using Python:

### Prerequisites

Make sure you have Python 3.10+ installed and the required dependencies:

```powershell
pip install -r requirements.txt
```
*(Dependencies: `pywifi`, `requests`, `urllib3`)*

### Run Script

```powershell
python utarwifihelper.py
```

---

## Compiling to `.exe`

If you want to package the Python script yourself, we recommend using **Nuitka** (which translates code to C++ and compiles to a native binary to prevent Antivirus false positives):

```powershell
pip install nuitka
python -m nuitka --standalone --onefile --enable-plugins=tk-inter --windows-console-mode=disable --assume-yes-for-downloads utarwifihelper.py
```

---

## Disclaimer

- This application is an open-source, independent tool developed by **[@khor0000](https://github.com/khor0000)**.
- It is **not** officially affiliated with, endorsed, or supported by Universiti Tunku Abdul Rahman (UTAR).
- Use this software at your own discretion.
