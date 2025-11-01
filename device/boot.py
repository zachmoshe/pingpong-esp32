print("Booting...")

SAFE_BOOT_PIN = 23
# Safe-boot: hold BOOT/IO0 at power-up to skip app
try:
    from machine import Pin
    safe_btn = Pin(SAFE_BOOT_PIN, Pin.IN, Pin.PULL_UP)
    if safe_btn.value() == 0:
        print("SAFE MODE: button held; skipping app.")
        raise KeyboardInterrupt()
    else:
        print("Normal boot.")
except Exception as e:
    print("Safe-boot error:", e)
