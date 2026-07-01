#pragma comment(linker,"\"/manifestdependency:type='win32' \
name='Microsoft.Windows.Common-Controls' version='6.0.0.0' \
processorArchitecture='*' publicKeyToken='6595b64144ccf1df' language='*'\"")

#ifndef UNICODE
#define UNICODE
#endif
#ifndef _UNICODE
#define _UNICODE
#endif

#include <windows.h>
#include <wininet.h>
#include <shlobj.h>
#include <shlwapi.h>
#include <shellapi.h>
#include <gdiplus.h>
#include <netlistmgr.h>
#include <string>
#include <vector>
#include <thread>
#include <chrono>
#include <sstream>
#include <fstream>
#include <iomanip>
#include <algorithm>

#pragma comment(lib, "wininet.lib")
#pragma comment(lib, "shlwapi.lib")
#pragma comment(lib, "gdi32.lib")
#pragma comment(lib, "user32.lib")
#pragma comment(lib, "gdiplus.lib")
#pragma comment(lib, "shell32.lib")
#pragma comment(lib, "ole32.lib")
#pragma comment(lib, "oleaut32.lib")

// Window IDs
#define ID_BTN_LOGIN 101
#define ID_BTN_RETRY 102
#define ID_EDIT_USER 103
#define ID_EDIT_PASS 104
#define ID_TIMER_ANIM 105

// App modes
enum AppMode {
    MODE_LOGIN,
    MODE_PROGRESS
};

// Global variables
HWND g_hwnd = NULL;
HWND g_hwndUser = NULL;
HWND g_hwndPass = NULL;
HWND g_hwndLoginBtn = NULL;
HWND g_hwndRetryBtn = NULL;
HWND g_hwndStatusLabel = NULL;
HWND g_hwndFooter = NULL;

HFONT g_hFontTitle = NULL;
HFONT g_hFontNormal = NULL;
HFONT g_hFontStatus = NULL;
HFONT g_hFontButton = NULL;
HFONT g_hFontFooter = NULL;

AppMode g_mode = MODE_PROGRESS;
bool g_animating = false;
std::wstring g_statusText = L"Checking internet...";

std::wstring g_username = L"";
std::wstring g_password = L"";
std::wstring g_targetSsid = L"utarwifi";
std::wstring g_configPath = L"";

// RC4 Encryption
std::string rc4_encrypt(const std::string& key, const std::string& plaintext) {
    std::vector<unsigned char> sbox(256);
    for (int i = 0; i < 256; i++) {
        sbox[i] = i;
    }
    int j = 0;
    for (int i = 0; i < 256; i++) {
        j = (j + sbox[i] + (unsigned char)key[i % key.length()]) & 0xFF;
        std::swap(sbox[i], sbox[j]);
    }
    int i = 0;
    j = 0;
    std::string ciphertext = "";
    for (size_t k = 0; k < plaintext.length(); k++) {
        i = (i + 1) & 0xFF;
        j = (j + sbox[i]) & 0xFF;
        std::swap(sbox[i], sbox[j]);
        unsigned char K = sbox[(sbox[i] + sbox[j]) & 0xFF];
        unsigned char cipher_byte = (unsigned char)plaintext[k] ^ K;
        char hex[3];
        sprintf_s(hex, "%02x", cipher_byte);
        ciphertext += hex;
    }
    return ciphertext;
}

// URL encoding
std::string url_encode(const std::string& value) {
    std::ostringstream escaped;
    escaped.fill('0');
    escaped.setf(std::ios::hex, std::ios::basefield);
    for (char c : value) {
        if (isalnum((unsigned char)c) || c == '-' || c == '_' || c == '.' || c == '~') {
            escaped << c;
        } else {
            escaped << '%' << std::setw(2) << int((unsigned char)c);
        }
    }
    return escaped.str();
}

// Convert String Helper
std::wstring to_wstring(const std::string& str) {
    if (str.empty()) return L"";
    int size_needed = MultiByteToWideChar(CP_UTF8, 0, &str[0], (int)str.size(), NULL, 0);
    std::wstring wstrTo(size_needed, 0);
    MultiByteToWideChar(CP_UTF8, 0, &str[0], (int)str.size(), &wstrTo[0], size_needed);
    return wstrTo;
}

std::string to_string(const std::wstring& wstr) {
    if (wstr.empty()) return "";
    int size_needed = WideCharToMultiByte(CP_UTF8, 0, &wstr[0], (int)wstr.size(), NULL, 0, NULL, NULL);
    std::string strTo(size_needed, 0);
    WideCharToMultiByte(CP_UTF8, 0, &wstr[0], (int)wstr.size(), &strTo[0], size_needed, NULL, NULL);
    return strTo;
}

// Silent CLI runner
std::string exec_cmd_silent(const std::wstring& cmd) {
    HANDLE hChildStd_OUT_Rd = NULL;
    HANDLE hChildStd_OUT_Wr = NULL;
    SECURITY_ATTRIBUTES saAttr;
    saAttr.nLength = sizeof(SECURITY_ATTRIBUTES);
    saAttr.bInheritHandle = TRUE;
    saAttr.lpSecurityDescriptor = NULL;

    if (!CreatePipe(&hChildStd_OUT_Rd, &hChildStd_OUT_Wr, &saAttr, 0)) return "";
    if (!SetHandleInformation(hChildStd_OUT_Rd, HANDLE_FLAG_INHERIT, 0)) return "";

    PROCESS_INFORMATION piProcInfo;
    STARTUPINFOW siStartInfo;
    ZeroMemory(&piProcInfo, sizeof(PROCESS_INFORMATION));
    ZeroMemory(&siStartInfo, sizeof(STARTUPINFOW));
    siStartInfo.cb = sizeof(STARTUPINFOW);
    siStartInfo.hStdError = hChildStd_OUT_Wr;
    siStartInfo.hStdOutput = hChildStd_OUT_Wr;
    siStartInfo.dwFlags |= STARTF_USESTDHANDLES | STARTF_USESHOWWINDOW;
    siStartInfo.wShowWindow = SW_HIDE;

    std::wstring cmdCopy = cmd;
    if (!CreateProcessW(NULL, &cmdCopy[0], NULL, NULL, TRUE, CREATE_NO_WINDOW, NULL, NULL, &siStartInfo, &piProcInfo)) {
        CloseHandle(hChildStd_OUT_Rd);
        CloseHandle(hChildStd_OUT_Wr);
        return "";
    }
    CloseHandle(hChildStd_OUT_Wr);

    std::string result = "";
    char chBuf[4096];
    DWORD dwRead;
    while (ReadFile(hChildStd_OUT_Rd, chBuf, sizeof(chBuf), &dwRead, NULL) && dwRead > 0) {
        result.append(chBuf, dwRead);
    }
    WaitForSingleObject(piProcInfo.hProcess, INFINITE);
    CloseHandle(piProcInfo.hProcess);
    CloseHandle(piProcInfo.hThread);
    CloseHandle(hChildStd_OUT_Rd);
    return result;
}

// Get current network name using Network List Manager COM API
std::string get_current_ssid() {
    HRESULT hr = CoInitializeEx(NULL, COINIT_APARTMENTTHREADED);
    bool coInit = SUCCEEDED(hr) || hr == RPC_E_CHANGED_MODE;

    INetworkListManager* pNetworkListManager = NULL;
    hr = CoCreateInstance(CLSID_NetworkListManager, NULL, CLSCTX_ALL, IID_INetworkListManager, (void**)&pNetworkListManager);
    
    std::string current_name = "";
    if (SUCCEEDED(hr)) {
        IEnumNetworks* pEnumNetworks = NULL;
        hr = pNetworkListManager->GetNetworks(NLM_ENUM_NETWORK_CONNECTED, &pEnumNetworks);
        if (SUCCEEDED(hr)) {
            INetwork* pNetwork = NULL;
            ULONG cFetched = 0;
            while (pEnumNetworks->Next(1, &pNetwork, &cFetched) == S_OK) {
                BSTR bstrName = NULL;
                if (SUCCEEDED(pNetwork->GetName(&bstrName))) {
                    std::wstring wname(bstrName);
                    current_name = to_string(wname);
                    SysFreeString(bstrName);
                }
                pNetwork->Release();
                if (!current_name.empty()) {
                    break;
                }
            }
            pEnumNetworks->Release();
        }
        pNetworkListManager->Release();
    }
    if (coInit) CoUninitialize();
    return current_name;
}

// Helper to check if current network profile matches target SSID (handles Windows numbered profiles like "utarwifi 9")
bool is_matching_ssid(const std::string& current, const std::string& target) {
    if (current == target) return true;
    if (current.find(target + " ") == 0) return true;
    return false;
}

// Connect to WiFi
bool scan_and_connect(const std::string& target_ssid) {
    exec_cmd_silent(L"netsh wlan show networks"); // triggers scan
    Sleep(2000);
    std::wstring cmd = L"netsh wlan connect name=" + to_wstring(target_ssid);
    exec_cmd_silent(cmd);
    for (int i = 0; i < 10; i++) {
        Sleep(1000);
        if (is_matching_ssid(get_current_ssid(), target_ssid)) {
            Sleep(2000); // extra time for DHCP
            return true;
        }
    }
    return false;
}

// Config file utilities
std::wstring escape_json_str(const std::wstring& str) {
    std::wstring out = L"";
    for (wchar_t c : str) {
        if (c == L'\\' || c == L'"') {
            out += L'\\';
        }
        out += c;
    }
    return out;
}

std::wstring extract_json_value(const std::wstring& json, const std::wstring& key) {
    size_t pos = json.find(L"\"" + key + L"\"");
    if (pos == std::wstring::npos) return L"";
    pos = json.find(L":", pos);
    if (pos == std::wstring::npos) return L"";
    size_t start = json.find(L"\"", pos);
    if (start == std::wstring::npos) return L"";
    size_t end = json.find(L"\"", start + 1);
    if (end == std::wstring::npos) return L"";
    std::wstring val = json.substr(start + 1, end - start - 1);
    std::wstring unescaped = L"";
    for (size_t i = 0; i < val.length(); i++) {
        if (val[i] == L'\\' && i + 1 < val.length()) {
            if (val[i+1] == L'\\' || val[i+1] == L'"') {
                unescaped += val[i+1];
                i++;
                continue;
            }
        }
        unescaped += val[i];
    }
    return unescaped;
}

void load_config() {
    wchar_t appDataPath[MAX_PATH];
    if (SUCCEEDED(SHGetFolderPathW(NULL, CSIDL_APPDATA, NULL, 0, appDataPath))) {
        g_configPath = std::wstring(appDataPath) + L"\\UtarWifiHelper\\config.json";
        std::wifstream f(g_configPath);
        if (f.is_open()) {
            std::wstringstream ss;
            ss << f.rdbuf();
            std::wstring json = ss.str();
            g_username = extract_json_value(json, L"username");
            g_password = extract_json_value(json, L"password");
            std::wstring ssid = extract_json_value(json, L"target_ssid");
            if (!ssid.empty()) g_targetSsid = ssid;
        }
    }
}

void save_config(const std::wstring& username, const std::wstring& password, const std::wstring& ssid) {
    wchar_t appDataPath[MAX_PATH];
    if (SUCCEEDED(SHGetFolderPathW(NULL, CSIDL_APPDATA, NULL, 0, appDataPath))) {
        std::wstring dir = std::wstring(appDataPath) + L"\\UtarWifiHelper";
        CreateDirectoryW(dir.c_str(), NULL);
        g_configPath = dir + L"\\config.json";
        std::wofstream f(g_configPath);
        if (f.is_open()) {
            f << L"{\n";
            f << L"    \"username\": \"" << escape_json_str(username) << L"\",\n";
            f << L"    \"password\": \"" << escape_json_str(password) << L"\",\n";
            f << L"    \"target_ssid\": \"" << escape_json_str(ssid) << L"\"\n";
            f << L"}\n";
        }
    }
}

// Network logic
bool check_internet() {
    HINTERNET hSession = InternetOpenA("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36", INTERNET_OPEN_TYPE_PRECONFIG, NULL, NULL, 0);
    if (!hSession) return false;
    DWORD timeout = 3000; // 3s
    InternetSetOptionA(hSession, INTERNET_OPTION_CONNECT_TIMEOUT, &timeout, sizeof(timeout));
    InternetSetOptionA(hSession, INTERNET_OPTION_SEND_TIMEOUT, &timeout, sizeof(timeout));
    InternetSetOptionA(hSession, INTERNET_OPTION_RECEIVE_TIMEOUT, &timeout, sizeof(timeout));

    HINTERNET hUrl = InternetOpenUrlA(hSession, "http://connectivitycheck.gstatic.com/generate_204", NULL, 0, INTERNET_FLAG_RELOAD | INTERNET_FLAG_NO_AUTO_REDIRECT, 0);
    bool active = false;
    if (hUrl) {
        char status_code[32] = {0};
        DWORD buffer_len = sizeof(status_code);
        if (HttpQueryInfoA(hUrl, HTTP_QUERY_STATUS_CODE, status_code, &buffer_len, NULL)) {
            if (atoi(status_code) == 204) {
                active = true;
            }
        }
        InternetCloseHandle(hUrl);
    }
    InternetCloseHandle(hSession);
    return active;
}

std::string detect_portal_url() {
    const char* test_urls[3] = {
        "http://connectivitycheck.gstatic.com/generate_204",
        "http://www.msftconnecttest.com/redirect",
        "http://captive.apple.com/hotspot-detect.html"
    };
    for (int attempt = 0; attempt < 2; attempt++) {
        if (attempt > 0) Sleep(2000);
        HINTERNET hSession = InternetOpenA("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36", INTERNET_OPEN_TYPE_PRECONFIG, NULL, NULL, 0);
        if (!hSession) continue;
        DWORD timeout = 5000; // 5s timeout for slow portal redirection DNS
        InternetSetOptionA(hSession, INTERNET_OPTION_CONNECT_TIMEOUT, &timeout, sizeof(timeout));
        InternetSetOptionA(hSession, INTERNET_OPTION_SEND_TIMEOUT, &timeout, sizeof(timeout));
        InternetSetOptionA(hSession, INTERNET_OPTION_RECEIVE_TIMEOUT, &timeout, sizeof(timeout));

        for (int i = 0; i < 3; i++) {
            HINTERNET hUrl = InternetOpenUrlA(hSession, test_urls[i], NULL, 0, INTERNET_FLAG_RELOAD | INTERNET_FLAG_NO_AUTO_REDIRECT, 0);
            if (hUrl) {
                char headers[4096] = {0};
                DWORD headers_len = sizeof(headers);
                if (HttpQueryInfoA(hUrl, HTTP_QUERY_RAW_HEADERS_CRLF, headers, &headers_len, NULL)) {
                    std::string h_str(headers);
                    size_t loc_pos = h_str.find("Location: ");
                    if (loc_pos == std::string::npos) {
                        loc_pos = h_str.find("location: ");
                    }
                    if (loc_pos != std::string::npos) {
                        size_t end_pos = h_str.find("\r\n", loc_pos);
                        std::string loc = h_str.substr(loc_pos + 10, end_pos - (loc_pos + 10));
                        if (loc.find("/ac_portal/") != std::string::npos) {
                            InternetCloseHandle(hUrl);
                            InternetCloseHandle(hSession);
                            return loc;
                        }
                    }
                }
                InternetCloseHandle(hUrl);
            }
            // Try with redirects enabled for meta-refresh pages
            hUrl = InternetOpenUrlA(hSession, test_urls[i], NULL, 0, INTERNET_FLAG_RELOAD, 0);
            if (hUrl) {
                char final_url[2048] = {0};
                DWORD final_url_len = sizeof(final_url);
                if (InternetQueryOptionA(hUrl, INTERNET_OPTION_URL, final_url, &final_url_len)) {
                    std::string f_url(final_url);
                    if (f_url.find("/ac_portal/") != std::string::npos && f_url.find("pc.html") != std::string::npos) {
                        InternetCloseHandle(hUrl);
                        InternetCloseHandle(hSession);
                        return f_url;
                    }
                }
                InternetCloseHandle(hUrl);
            }
        }
        InternetCloseHandle(hSession);
    }
    return "";
}

bool login(const std::string& portal_url, const std::string& username, const std::string& password) {
    URL_COMPONENTSA urlComp = {0};
    urlComp.dwStructSize = sizeof(urlComp);
    char host[256] = {0};
    char path[2048] = {0};
    urlComp.lpszHostName = host;
    urlComp.dwHostNameLength = sizeof(host);
    urlComp.lpszUrlPath = path;
    urlComp.dwUrlPathLength = sizeof(path);

    if (!InternetCrackUrlA(portal_url.c_str(), 0, 0, &urlComp)) return false;

    std::string base_path = "/ac_portal/login.php";

    HINTERNET hSession = InternetOpenA("UtarWifiHelper", INTERNET_OPEN_TYPE_PRECONFIG, NULL, NULL, 0);
    if (!hSession) return false;
    
    // Disable SSL verification warnings
    DWORD flags = SECURITY_FLAG_IGNORE_UNKNOWN_CA | 
                  SECURITY_FLAG_IGNORE_WRONG_USAGE | 
                  SECURITY_FLAG_IGNORE_CERT_CN_INVALID | 
                  SECURITY_FLAG_IGNORE_CERT_DATE_INVALID |
                  SECURITY_FLAG_IGNORE_REVOCATION;
    InternetSetOptionA(hSession, INTERNET_OPTION_SECURITY_FLAGS, &flags, sizeof(flags));

    HINTERNET hConnect = InternetConnectA(hSession, host, urlComp.nPort, NULL, NULL, INTERNET_SERVICE_HTTP, 0, 0);
    if (!hConnect) {
        InternetCloseHandle(hSession);
        return false;
    }

    DWORD reqFlags = INTERNET_FLAG_RELOAD | INTERNET_FLAG_IGNORE_CERT_CN_INVALID | INTERNET_FLAG_IGNORE_CERT_DATE_INVALID;
    if (urlComp.nScheme == INTERNET_SCHEME_HTTPS) reqFlags |= INTERNET_FLAG_SECURE;

    HINTERNET hRequest = HttpOpenRequestA(hConnect, "POST", base_path.c_str(), NULL, portal_url.c_str(), NULL, reqFlags, 0);
    if (!hRequest) {
        InternetCloseHandle(hConnect);
        InternetCloseHandle(hSession);
        return false;
    }
    InternetSetOptionA(hRequest, INTERNET_OPTION_SECURITY_FLAGS, &flags, sizeof(flags));

    auto now = std::chrono::system_clock::now();
    auto ms = std::chrono::duration_cast<std::chrono::milliseconds>(now.time_since_epoch()).count();
    std::string rckey = std::to_string(ms);
    std::string encrypted_pwd = rc4_encrypt(rckey, password);

    std::string payload = "opr=pwdLogin&userName=" + url_encode(username) + 
                          "&pwd=" + url_encode(encrypted_pwd) + 
                          "&auth_tag=" + url_encode(rckey) + 
                          "&rememberPwd=0";

    const char* headers = "Content-Type: application/x-www-form-urlencoded\r\n"
                          "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36\r\n";

    bool success = HttpSendRequestA(hRequest, headers, (DWORD)-1, (void*)payload.c_str(), (DWORD)payload.length());
    if (!success) {
        InternetCloseHandle(hRequest);
        InternetCloseHandle(hConnect);
        InternetCloseHandle(hSession);
        return false;
    }

    std::string response_data = "";
    char buffer[1024];
    DWORD read = 0;
    while (InternetReadFile(hRequest, buffer, sizeof(buffer), &read) && read > 0) {
        response_data.append(buffer, read);
    }

    InternetCloseHandle(hRequest);
    InternetCloseHandle(hConnect);

    bool login_ok = false;
    size_t succ_pos = response_data.find("\"success\"");
    if (succ_pos != std::string::npos) {
        size_t col_pos = response_data.find(":", succ_pos);
        if (col_pos != std::string::npos) {
            size_t true_pos = response_data.find("true", col_pos);
            size_t false_pos = response_data.find("false", col_pos);
            if (true_pos != std::string::npos && (false_pos == std::string::npos || true_pos < false_pos)) {
                login_ok = true;
            }
        }
    }

    if (login_ok) {
        size_t loc_pos = response_data.find("\"location\"");
        if (loc_pos != std::string::npos) {
            size_t start = response_data.find("\"", response_data.find(":", loc_pos));
            if (start != std::string::npos) {
                size_t end = response_data.find("\"", start + 1);
                if (end != std::string::npos) {
                    std::string final_redirect = response_data.substr(start + 1, end - start - 1);
                    std::string clean_redirect = "";
                    for (size_t k = 0; k < final_redirect.length(); k++) {
                        if (final_redirect[k] == '\\' && k + 1 < final_redirect.length()) {
                            clean_redirect += final_redirect[k+1];
                            k++;
                        } else {
                            clean_redirect += final_redirect[k];
                        }
                    }
                    HINTERNET hFinalReq = InternetOpenUrlA(hSession, clean_redirect.c_str(), NULL, 0, INTERNET_FLAG_RELOAD, 0);
                    if (hFinalReq) InternetCloseHandle(hFinalReq);
                }
            }
        }
    }

    InternetCloseHandle(hSession);
    return login_ok;
}

// UI State modifiers
void set_status(const std::wstring& text) {
    g_statusText = text;
    if (g_hwndStatusLabel) {
        SetWindowTextW(g_hwndStatusLabel, text.c_str());
    }
}

void switch_mode(AppMode mode) {
    g_mode = mode;
    if (mode == MODE_LOGIN) {
        g_animating = false;
        ShowWindow(g_hwndUser, SW_SHOW);
        ShowWindow(g_hwndPass, SW_SHOW);
        ShowWindow(g_hwndLoginBtn, SW_SHOW);
        ShowWindow(g_hwndStatusLabel, SW_HIDE);
        ShowWindow(g_hwndRetryBtn, SW_HIDE);
    } else { // PROGRESS
        ShowWindow(g_hwndUser, SW_HIDE);
        ShowWindow(g_hwndPass, SW_HIDE);
        ShowWindow(g_hwndLoginBtn, SW_HIDE);
        ShowWindow(g_hwndStatusLabel, SW_SHOW);
        ShowWindow(g_hwndRetryBtn, SW_HIDE);
        g_animating = true;
    }
    InvalidateRect(g_hwnd, NULL, TRUE);
}

void show_retry(const std::wstring& err_msg) {
    g_animating = false;
    set_status(err_msg);
    ShowWindow(g_hwndRetryBtn, SW_SHOW);
    InvalidateRect(g_hwnd, NULL, TRUE);
}

// Time helper
double GetTimeSeconds() {
    auto now = std::chrono::high_resolution_clock::now();
    auto ms = std::chrono::duration_cast<std::chrono::milliseconds>(now.time_since_epoch()).count();
    return ms / 1000.0;
}

// Rounded polygon points computation
std::vector<Gdiplus::PointF> GetRoundedSquarePoints(double cx, double cy, double size, double radius, double angle_deg) {
    std::vector<Gdiplus::PointF> points;
    double angle_rad = angle_deg * 3.1415926535 / 180.0;
    double cos_a = cos(angle_rad);
    double sin_a = sin(angle_rad);

    struct Corner {
        double cx_c;
        double cy_c;
        double start_angle;
    };
    Corner corners[4] = {
        { size - radius, size - radius, 0.0 },       // bottom-right
        { -size + radius, size - radius, 90.0 },     // bottom-left
        { -size + radius, -size + radius, 180.0 },   // top-left
        { size - radius, -size + radius, 270.0 }     // top-right
    };

    int num_points_per_corner = 6;
    for (int c = 0; c < 4; c++) {
        for (int i = 0; i <= num_points_per_corner; i++) {
            double theta = (corners[c].start_angle + (i * 90.0 / num_points_per_corner)) * 3.1415926535 / 180.0;
            double x = corners[c].cx_c + radius * cos(theta);
            double y = corners[c].cy_c + radius * sin(theta);

            // Rotate
            double rx = x * cos_a - y * sin_a;
            double ry = x * sin_a + y * cos_a;

            points.push_back(Gdiplus::PointF((float)(cx + rx), (float)(cy + ry)));
        }
    }
    return points;
}

// Core app execution logic
void run_logic() {
    // 0. Check if internet already works
    if (check_internet()) {
        set_status(L"[✓] Internet is active.");
        Sleep(1000);
        PostMessage(g_hwnd, WM_CLOSE, 0, 0);
        return;
    }

    // 1. Connect to WiFi
    std::string current = get_current_ssid();
    std::string target_str = to_string(g_targetSsid);
    if (!is_matching_ssid(current, target_str)) {
        set_status(L"Scanning for 'utarwifi'...");
        if (!scan_and_connect(target_str)) {
            show_retry(L"Could not connect.\nPlease make sure WiFi is turned on\nand you are in range.");
            return;
        } else {
            set_status(L"Waiting for network...");
            for (int i = 0; i < 10; i++) {
                if (check_internet()) break;
                Sleep(1000);
            }
        }
    }

    // 2. Detect portal
    set_status(L"Detecting portal...");
    std::string portal = detect_portal_url();
    if (portal.empty()) {
        if (check_internet()) {
            set_status(L"[✓] Internet is active.");
            Sleep(1000);
            PostMessage(g_hwnd, WM_CLOSE, 0, 0);
            return;
        }
        show_retry(L"Could not detect portal login page.\nAre you in range of UTAR WiFi?");
        return;
    }

    // 3. Login
    set_status(L"Logging in...");
    if (login(portal, to_string(g_username), to_string(g_password))) {
        Sleep(2000);
        if (check_internet()) {
            set_status(L"[✓] Login successful!");
            save_config(g_username, g_password, g_targetSsid);
            
            // Send a passive probe helper request to Microsoft NCSI server
            // to trick Windows passive probing into updating the taskbar icon immediately.
            HINTERNET hSession = InternetOpenA("UtarWifiHelperPassive", INTERNET_OPEN_TYPE_PRECONFIG, NULL, NULL, 0);
            if (hSession) {
                HINTERNET hUrl = InternetOpenUrlA(hSession, "http://www.msftconnecttest.com/connecttest.txt", NULL, 0, INTERNET_FLAG_RELOAD, 0);
                if (hUrl) InternetCloseHandle(hUrl);
                InternetCloseHandle(hSession);
            }

            Sleep(1000);
            PostMessage(g_hwnd, WM_CLOSE, 0, 0);
        } else {
            show_retry(L"Login failed. Check credentials.");
        }
    } else {
        show_retry(L"Invalid credentials.");
        Sleep(1500);
        switch_mode(MODE_LOGIN);
    }
}

// Start async thread
void start_worker() {
    switch_mode(MODE_PROGRESS);
    set_status(L"Checking internet...");
    std::thread(run_logic).detach();
}

// Window procedure
LRESULT CALLBACK WndProc(HWND hwnd, UINT message, WPARAM wParam, LPARAM lParam) {
    switch (message) {
    case WM_CREATE:
    {
        // Define Segoe UI fonts
        g_hFontTitle = CreateFontW(22, 0, 0, 0, FW_BOLD, FALSE, FALSE, FALSE, ANSI_CHARSET, OUT_DEFAULT_PRECIS, CLIP_DEFAULT_PRECIS, DEFAULT_QUALITY, DEFAULT_PITCH | FF_SWISS, L"Microsoft YaHei");
        g_hFontNormal = CreateFontW(16, 0, 0, 0, FW_NORMAL, FALSE, FALSE, FALSE, ANSI_CHARSET, OUT_DEFAULT_PRECIS, CLIP_DEFAULT_PRECIS, DEFAULT_QUALITY, DEFAULT_PITCH | FF_SWISS, L"Microsoft YaHei");
        g_hFontStatus = CreateFontW(19, 0, 0, 0, FW_MEDIUM, FALSE, FALSE, FALSE, ANSI_CHARSET, OUT_DEFAULT_PRECIS, CLIP_DEFAULT_PRECIS, DEFAULT_QUALITY, DEFAULT_PITCH | FF_SWISS, L"Microsoft YaHei");
        g_hFontButton = CreateFontW(16, 0, 0, 0, FW_BOLD, FALSE, FALSE, FALSE, ANSI_CHARSET, OUT_DEFAULT_PRECIS, CLIP_DEFAULT_PRECIS, DEFAULT_QUALITY, DEFAULT_PITCH | FF_SWISS, L"Microsoft YaHei");
        g_hFontFooter = CreateFontW(12, 0, 0, 0, FW_NORMAL, FALSE, FALSE, FALSE, ANSI_CHARSET, OUT_DEFAULT_PRECIS, CLIP_DEFAULT_PRECIS, DEFAULT_QUALITY, DEFAULT_PITCH | FF_SWISS, L"Microsoft YaHei");

        // UI Controls
        g_hwndUser = CreateWindowExW(0, L"EDIT", L"", WS_CHILD | WS_BORDER | ES_AUTOHSCROLL, 40, 110, 264, 32, hwnd, (HMENU)ID_EDIT_USER, NULL, NULL);
        g_hwndPass = CreateWindowExW(0, L"EDIT", L"", WS_CHILD | WS_BORDER | ES_AUTOHSCROLL | ES_PASSWORD, 40, 155, 264, 32, hwnd, (HMENU)ID_EDIT_PASS, NULL, NULL);
        
        SendMessageW(g_hwndUser, WM_SETFONT, (WPARAM)g_hFontNormal, TRUE);
        SendMessageW(g_hwndPass, WM_SETFONT, (WPARAM)g_hFontNormal, TRUE);

        // Native placeholder text
        SendMessageW(g_hwndUser, 0x1501, FALSE, (LPARAM)L"Login ID");
        SendMessageW(g_hwndPass, 0x1501, FALSE, (LPARAM)L"Password");

        g_hwndLoginBtn = CreateWindowExW(0, L"BUTTON", L"Log In", WS_CHILD | BS_OWNERDRAW, 40, 210, 264, 36, hwnd, (HMENU)ID_BTN_LOGIN, NULL, NULL);
        g_hwndRetryBtn = CreateWindowExW(0, L"BUTTON", L"Retry Connection", WS_CHILD | BS_OWNERDRAW, 100, 280, 144, 36, hwnd, (HMENU)ID_BTN_RETRY, NULL, NULL);

        g_hwndStatusLabel = CreateWindowExW(0, L"STATIC", L"Checking internet...", WS_CHILD | SS_CENTER, 20, 180, 304, 80, hwnd, NULL, NULL, NULL);
        SendMessageW(g_hwndStatusLabel, WM_SETFONT, (WPARAM)g_hFontStatus, TRUE);

        g_hwndFooter = CreateWindowExW(0, L"STATIC", L"Open Source on GitHub • Developed by @khor0000\nNot affiliated with UTAR", WS_CHILD | WS_VISIBLE | SS_CENTER | SS_NOTIFY, 0, 360, 344, 30, hwnd, (HMENU)201, NULL, NULL);
        SendMessageW(g_hwndFooter, WM_SETFONT, (WPARAM)g_hFontFooter, TRUE);

        // Preload config values
        if (!g_username.empty()) SetWindowTextW(g_hwndUser, g_username.c_str());
        if (!g_password.empty()) SetWindowTextW(g_hwndPass, g_password.c_str());

        // Animation Timer (16ms = ~60FPS)
        SetTimer(hwnd, ID_TIMER_ANIM, 16, NULL);

        if (g_username.empty() || g_password.empty()) {
            switch_mode(MODE_LOGIN);
        } else {
            start_worker();
        }
        break;
    }
    case WM_TIMER:
    {
        if (g_animating) {
            // Trigger repaint of the canvas area
            RECT r = { 100, 80, 240, 200 };
            InvalidateRect(hwnd, &r, FALSE);
        }
        break;
    }
    case WM_SETCURSOR:
    {
        HWND hwndChild = (HWND)wParam;
        if (hwndChild == g_hwndFooter) {
            SetCursor(LoadCursor(NULL, IDC_HAND));
            return TRUE;
        }
        return DefWindowProc(hwnd, message, wParam, lParam);
    }
    case WM_CTLCOLORSTATIC:
    {
        HDC hdc = (HDC)wParam;
        HWND hwndStatic = (HWND)lParam;
        SetBkMode(hdc, TRANSPARENT);
        if (hwndStatic == g_hwndFooter) {
            SetTextColor(hdc, RGB(0x99, 0x99, 0x99));
        } else {
            SetTextColor(hdc, RGB(0x44, 0x44, 0x44));
        }
        return (LRESULT)GetStockObject(WHITE_BRUSH);
    }
    case WM_DRAWITEM:
    {
        LPDRAWITEMSTRUCT lpDrawItem = (LPDRAWITEMSTRUCT)lParam;
        if (lpDrawItem->CtlType == ODT_BUTTON) {
            HDC hdc = lpDrawItem->hDC;
            RECT rect = lpDrawItem->rcItem;
            HBRUSH hBrush;
            if (lpDrawItem->itemState & ODS_SELECTED) {
                hBrush = CreateSolidBrush(RGB(0x2e, 0x5f, 0xb5));
            } else {
                hBrush = CreateSolidBrush(RGB(0x1D, 0x4B, 0x9E));
            }
            FillRect(hdc, &rect, hBrush);
            DeleteObject(hBrush);

            SetTextColor(hdc, RGB(255, 255, 255));
            SetBkMode(hdc, TRANSPARENT);

            wchar_t text[128];
            GetWindowTextW(lpDrawItem->hwndItem, text, 128);
            SelectObject(hdc, g_hFontButton);
            DrawTextW(hdc, text, -1, &rect, DT_CENTER | DT_VCENTER | DT_SINGLELINE);
            return TRUE;
        }
        break;
    }
    case WM_COMMAND:
    {
        if (LOWORD(wParam) == ID_BTN_LOGIN) {
            wchar_t user[128];
            wchar_t pass[128];
            GetWindowTextW(g_hwndUser, user, 128);
            GetWindowTextW(g_hwndPass, pass, 128);
            
            std::wstring user_str(user);
            std::wstring pass_str(pass);
            
            if (user_str.empty() || pass_str.empty() || user_str == L"Login ID" || pass_str == L"Password") {
                MessageBoxW(hwnd, L"Please enter your Login ID and Password.", L"Input Error", MB_OK | MB_ICONERROR);
            } else {
                g_username = user_str;
                g_password = pass_str;
                save_config(g_username, g_password, g_targetSsid);
                start_worker();
            }
        } else if (LOWORD(wParam) == ID_BTN_RETRY) {
            start_worker();
        } else if (LOWORD(wParam) == 201 && HIWORD(wParam) == STN_CLICKED) {
            ShellExecuteW(NULL, L"open", L"https://github.com/khor0000/utarwifiloginhelper", NULL, NULL, SW_SHOWNORMAL);
        }
        break;
    }
    case WM_PAINT:
    {
        PAINTSTRUCT ps;
        HDC hdc = BeginPaint(hwnd, &ps);

        // Double buffering
        RECT rect;
        GetClientRect(hwnd, &rect);
        int width = rect.right - rect.left;
        int height = rect.bottom - rect.top;

        HDC memDC = CreateCompatibleDC(hdc);
        HBITMAP memBitmap = CreateCompatibleBitmap(hdc, width, height);
        SelectObject(memDC, memBitmap);

        HBRUSH hBg = CreateSolidBrush(RGB(255, 255, 255));
        FillRect(memDC, &rect, hBg);
        DeleteObject(hBg);

        // Header Section
        SelectObject(memDC, g_hFontTitle);
        SetTextColor(memDC, RGB(0x1a, 0x1a, 0x1a));
        SetBkMode(memDC, TRANSPARENT);
        RECT rTitle = { 0, 12, width, 40 };
        DrawTextW(memDC, L"Sign in to UTARWIFI.", -1, &rTitle, DT_CENTER);

        HBRUSH hBlueBar = CreateSolidBrush(RGB(0x1D, 0x4B, 0x9E));
        RECT rBlueBar = { width / 2 - 80, 48, width / 2 + 80, 50 };
        FillRect(memDC, &rBlueBar, hBlueBar);
        DeleteObject(hBlueBar);

        HPEN hBorderPen = CreatePen(PS_SOLID, 1, RGB(221, 221, 221));
        SelectObject(memDC, hBorderPen);
        MoveToEx(memDC, 0, 51, NULL);
        LineTo(memDC, width, 51);
        DeleteObject(hBorderPen);

        // Animation Drawer
        if (g_mode == MODE_PROGRESS && g_animating) {
            Gdiplus::Graphics graphics(memDC);
            graphics.SetSmoothingMode(Gdiplus::SmoothingModeAntiAlias);

            double t = GetTimeSeconds();
            double duration = 2.0;
            double p = fmod(t, duration) / duration;

            double eased_p = (1.0 - cos(3.1415926535 * p)) / 2.0;
            double angle = eased_p * 360.0;
            double radius_factor = 0.06 + 0.44 * sin(3.1415926535 * eased_p);

            double size = 12.0;
            double radius = size * radius_factor;

            double cx = width / 2.0;
            double cy = 120.0;

            std::vector<Gdiplus::PointF> points = GetRoundedSquarePoints(cx, cy, size, radius, angle);

            Gdiplus::SolidBrush brush(Gdiplus::Color(255, 0x1D, 0x4B, 0x9E));
            graphics.FillPolygon(&brush, points.data(), (int)points.size());
        }

        BitBlt(hdc, 0, 0, width, height, memDC, 0, 0, SRCCOPY);
        DeleteObject(memBitmap);
        DeleteDC(memDC);
        EndPaint(hwnd, &ps);
        break;
    }
    case WM_CLOSE:
        DestroyWindow(hwnd);
        break;
    case WM_DESTROY:
        KillTimer(hwnd, ID_TIMER_ANIM);
        DeleteObject(g_hFontTitle);
        DeleteObject(g_hFontNormal);
        DeleteObject(g_hFontStatus);
        DeleteObject(g_hFontButton);
        DeleteObject(g_hFontFooter);
        PostQuitMessage(0);
        break;
    default:
        return DefWindowProc(hwnd, message, wParam, lParam);
    }
    return 0;
}
int WINAPI WinMain(HINSTANCE hInstance, HINSTANCE hPrevInstance, LPSTR lpCmdLine, int nCmdShow) {
    // Enable DPI awareness
    SetProcessDPIAware();

    // Initialize GDI+
    Gdiplus::GdiplusStartupInput gdiplusStartupInput;
    ULONG_PTR gdiplusToken;
    Gdiplus::GdiplusStartup(&gdiplusToken, &gdiplusStartupInput, NULL);

    load_config();

    WNDCLASSEXW wcex;
    ZeroMemory(&wcex, sizeof(WNDCLASSEXW));
    wcex.cbSize = sizeof(WNDCLASSEXW);
    wcex.style = CS_HREDRAW | CS_VREDRAW;
    wcex.lpfnWndProc = WndProc;
    wcex.hInstance = hInstance;
    wcex.hCursor = LoadCursor(NULL, IDC_ARROW);
    wcex.hbrBackground = (HBRUSH)GetStockObject(WHITE_BRUSH);
    wcex.lpszClassName = L"UtarWifiHelperWindow";
    wcex.hIcon = LoadIconW(hInstance, MAKEINTRESOURCEW(101));

    if (!RegisterClassExW(&wcex)) {
        return 1;
    }

    int winWidth = 360;
    int winHeight = 440;

    RECT r = { 0, 0, winWidth, winHeight };
    AdjustWindowRectEx(&r, WS_OVERLAPPED | WS_CAPTION | WS_SYSMENU | WS_MINIMIZEBOX, FALSE, 0);

    g_hwnd = CreateWindowExW(
        0,
        L"UtarWifiHelperWindow",
        L"Welcome to UTAR Wireless Network",
        WS_OVERLAPPED | WS_CAPTION | WS_SYSMENU | WS_MINIMIZEBOX,
        CW_USEDEFAULT, CW_USEDEFAULT,
        r.right - r.left, r.bottom - r.top,
        NULL, NULL, hInstance, NULL
    );

    if (!g_hwnd) {
        return 1;
    }

    // Set Window position to center of screen
    int screenWidth = GetSystemMetrics(SM_CXSCREEN);
    int screenHeight = GetSystemMetrics(SM_CYSCREEN);
    int x = (screenWidth - winWidth) / 2;
    int y = (screenHeight - winHeight) / 2;
    SetWindowPos(g_hwnd, NULL, x, y, 0, 0, SWP_NOSIZE | SWP_NOZORDER);

    ShowWindow(g_hwnd, nCmdShow);
    UpdateWindow(g_hwnd);

    MSG msg;
    while (GetMessage(&msg, NULL, 0, 0)) {
        TranslateMessage(&msg);
        DispatchMessage(&msg);
    }

    Gdiplus::GdiplusShutdown(gdiplusToken);
    return (int)msg.wParam;
}
