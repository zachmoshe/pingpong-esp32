print("Booting...")

SAFE_BOOT_PIN = 23
SAFE_MODE = False

try:
    import machine
    if machine.reset_cause() == machine.SOFT_RESET:
        SAFE_MODE = True
        print("SAFE MODE: soft reset detected; main.py will not start.")

    from machine import Pin
    safe_btn = Pin(SAFE_BOOT_PIN, Pin.IN, Pin.PULL_DOWN)
    if safe_btn.value() == 1:
        SAFE_MODE = True
        print("SAFE MODE: button held; main.py will not start.")

    if not SAFE_MODE:
        print("Normal boot.")
except Exception as e:
    print("Safe-boot error:", e)