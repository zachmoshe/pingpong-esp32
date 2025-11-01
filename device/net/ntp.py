# Minimal NTP settime for MicroPython
import time, socket
NTP_DELTA = 2208988800

def settime(host="pool.ntp.org"):
    import struct
    addr = socket.getaddrinfo(host, 123)[0][-1]
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        msg = b'\x1b' + 47*b'\0'
        s.settimeout(2)
        s.sendto(msg, addr)
        msg = s.recv(48)
    finally:
        s.close()
    val = int.from_bytes(msg[40:44], "big") - NTP_DELTA
    import machine
    tm = time.gmtime(val)
    machine.RTC().datetime((tm[0], tm[1], tm[2], tm[6]+1, tm[3], tm[4], tm[5], 0))
