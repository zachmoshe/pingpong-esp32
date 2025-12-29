# PORT ?= $(shell python tools/detect_port.py)
PORT = /dev/cu.SLAB_USBtoUART
# BIN = firmware/ESP32_GENERIC-20250911-v1.26.1.bin
BIN = firmware/ESP32_GENERIC-20251011-v1.24.0-with-ulab.bin

.PHONY: repl sync run flash wipe reset tree

repl:
	uv run mpremote connect $(PORT) repl

sync:
	uv run mpremote connect $(PORT) sleep 1 fs cp -r device/* :            

run-backend:
	docker build -t backend-server . && docker run -it --rm -p ${BACKEND_PORT}:12345 -v $(PWD)/.env:/app/.env backend-server

run: sync reset

reset:
	uv run mpremote connect $(PORT) reset

flash:
	@[ -n "$(BIN)" ] || (echo "Set BIN=firmware/<file>.bin"; exit 1)
	uv run esptool --chip auto --port $(PORT) erase-flash
	uv run esptool --chip auto --port $(PORT) --baud 460800 write-flash 0x1000 $(BIN)

wipe:
	uv run mpremote connect $(PORT) fs rm :main.py || true
	uv run mpremote connect $(PORT) fs rm :boot.py || true
	uv run mpremote connect $(PORT) fs rmdir :drivers || true
	uv run mpremote connect $(PORT) fs rmdir :modules || true
	uv run mpremote connect $(PORT) fs rmdir :net || true
	uv run mpremote connect $(PORT) fs rmdir :lib || true

tree:
	@ls -R
