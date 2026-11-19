import time
import serial

with serial.Serial("/dev/ttyACM0", 115200, timeout=1) as ser:
	while True:
		ser.write(f"{int(time.time())}\r\n".encode("utf-8"))
		time.sleep(5)
		print(ser.read_all().decode(errors="ignore"))
		time.sleep(5)
