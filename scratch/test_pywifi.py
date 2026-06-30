import pywifi
import time

def test_scan():
    wifi = pywifi.PyWiFi()
    iface = wifi.interfaces()[0]
    print(f"Using interface: {iface.name()}")
    
    iface.scan()
    time.sleep(2)
    results = iface.scan_results()
    
    print("Available networks:")
    for network in results:
        print(f"- {network.ssid}")

if __name__ == "__main__":
    try:
        test_scan()
    except Exception as e:
        print(f"Error: {e}")
