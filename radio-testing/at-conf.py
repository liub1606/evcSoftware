import time
import serial

with serial.Serial("/dev/ttyACM0", 115200, timeout=1) as ser:
	time.sleep(1.0)
	ser.write(b"+++\r\n")
	time.sleep(0.5)
	print(ser.read_all().decode(errors="ignore"))

	ser.write(b"AT+VER\r\n")
	time.sleep(0.2)
	print(ser.read_all().decode(errors="ignore"))

	ser.write(b"AT+SF=12\r\n")
	time.sleep(0.2)
	print(ser.read_all().decode(errors="ignore"))

	ser.write(b"AT+EXIT\r\n")
	time.sleep(0.2)
	print(ser.read_all().decode(errors="ignore"))
