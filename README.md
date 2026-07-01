# UTAR WiFi Auto-Login Helper

A lightweight, native Windows automated captive portal login utility for Universiti Tunku Abdul Rahman (UTAR) wireless network (`utarwifi`). It scans, connects, and logs in automatically using your credentials stored securely on your local machine.

---

## Features

- **Auto-Scan & Connect:** Automatically scans for and connects to the open `utarwifi` network.
- **Captive Portal Detection:** Detects the UTAR login portal automatically.
- **Secure Local Storage:** Keeps your credentials locally in `%APPDATA%\UtarWifiHelper\config.json` and encrypts your password via RC4 before sending it to the UTAR login portal. **Your login details are never shared or sent to any external server.**
- **Native Win32 GUI:** Built using native Win32 APIs (no bulky runtime or HTML rendering) with a high-performance, anti-aliased Morphing Square loading animation powered by GDI+.
- **Zero Antivirus Blocks:** Written in C++ with static linking (`/MT`) to prevent false-positive blocks and keep the file size under 500 KB.
- **Background Execution:** Closes automatically once a stable internet connection is established.

---

## How to Use (Recommended)

1. Download the latest compiled **`utarwifihelper.exe`** from the [Releases](https://github.com/khor0000/utarwifiloginhelper/releases) section.
2. Run `utarwifihelper.exe`.
3. Enter your UTAR credentials on the first run. The helper will securely save them to `%APPDATA%\UtarWifiHelper\config.json`.
4. In the future, you can simply run `utarwifihelper.exe` (or add a shortcut to your Windows Startup folder) and it will log you in automatically in the background without prompting for credentials!

---

## Compiling from Source (C++)

If you prefer to compile the application yourself:

### Prerequisites

Make sure you have Visual Studio installed with the **Desktop development with C++** workload.

### Build Executable

1. Open a PowerShell or Command Prompt.
2. Run the build batch script:
   ```powershell
   .\build.bat
   ```
   *(This will automatically locate the Visual Studio compiler environment (`cl.exe` / `rc.exe`), compile the source files with static linking, embed the custom icon, and output the optimized `utarwifihelper.exe`.)*

---

## Disclaimer

- This application is an open-source, independent tool developed by **[@khor0000](https://github.com/khor0000)**.
- It is **not** officially affiliated with, endorsed, or supported by Universiti Tunku Abdul Rahman (UTAR).
- Use this software at your own discretion.
