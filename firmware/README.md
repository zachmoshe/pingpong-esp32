# firmware/

Place your MicroPython firmware `.bin` file here, matching your exact chip:
- ESP32 (classic), ESP32-S3, ESP32-C3, etc.

Then flash with:
```
make flash BIN=firmware/<your-firmware>.bin
```
