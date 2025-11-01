import json, network, time

def load_secrets():
    try:
        with open('secrets.json') as f:
            return json.load(f)
    except OSError:
        return {}

def connect(timeout_s=15):
    secrets = load_secrets()
    cred = secrets.get("wifi", {})
    ssid, pwd = cred.get("ssid"), cred.get("password")

    sta = network.WLAN(network.STA_IF)

    if not sta.active():
        sta.active(True)

    if not ssid:
        print("No WiFi credentials found.")
        return None
    
    if not sta.isconnected():
        print(f"Connecting to {ssid}...")
        sta.connect(ssid, pwd)
        while not sta.isconnected():
            time.sleep_ms(200)
    print(f"Connected: {sta.ifconfig()=}")

    return sta

# def provision_if_needed():
#     sta = network.WLAN(network.STA_IF)
#     if hasattr(sta, "isconnected") and sta.isconnected():
#         return sta
#     # fallback AP for quick provisioning
#     ap = network.WLAN(network.AP_IF)
#     ap.active(True)
#     try:
#         ap.config(essid="ESP32-Provision", authmode=network.AUTH_OPEN)
#     except Exception:
#         pass
#     return ap
