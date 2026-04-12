from helpers import *
import threading
import serial
import time
import os

class VirtualSerial:
	def __init__(self, port, freq, vals, debug):
		# self.controller, self.endpoint = pty.openpty()
		# self.endpoint_name = os.ttyname(self.endpoint)
		self.port = port
		self.freq = freq
		self.debug = debug
		self.vals = [(val[0], RandomNoise(5, val[1][2], val[1][0], val[1][1])) for val in vals]
		self.kill_flag = False

	def start(self):
		self.debug.log(f"EMULATOR: connecting to serial port {self.port}")
		self.ser = serial.Serial(self.port, baudrate=9600, timeout=0)
		self.debug.log(f"EMULATOR: successfully connected")
		self.serial_thread = threading.Thread(target=self.async_send)
		self.serial_thread.start()
		self.debug.log(f"EMULATOR: thread running async @{self.port}")

	def send_record(self):
		nums = [str(val[1].get_noise()) for val in self.vals]
		record = ','.join(nums) + '\n'
		self.debug.log(record)
		bytecount = self.ser.write(record.encode("utf-8"))
		self.debug.log(f"EMULATOR: sent {bytecount} bytes")

	def async_send(self):
		while 1:
			start = time.time()
			self.send_record()
			time.sleep(max(0, 1 / self.freq - (time.time() - start)))
			if self.kill_flag:
				break

	def kill(self):
		self.ser.close()
		self.kill_flag = True
