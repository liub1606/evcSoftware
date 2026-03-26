import numpy as np
import requests
import random
import math


def volts2soc_agm(v):
	volts = [10.5, 11.51, 11.66, 11.81, 11.95, 12.05, 12.15, 12.3, 12.5, 12.75, 12.8, 13.]
	soc = [0., 10., 20., 30., 40., 50., 60., 70., 80., 90., 99., 100.]

	# i = np.interp(volts, v)
	s = np.interp(v, volts, soc)

	return s

def index_newline(record):
	for i, val in enumerate(record):
		if val == 10 or val == 13: # LF (unix), CR (win)
			return i

class Uploader:
	def __init__(self, cache_size, address, debug):
		self.cache = []
		self.cache_size = cache_size
		self.address = address
		self.debug = debug

	def new_record(self, record):
		self.cache.append(record)
		if len(self.cache) >= self.cache_size:
			self.debug.log(f"sending {self.cache_size} records to {self.address}")
			res = requests.post(f"{self.address}/new-entries", json={
				"records": self.cache})
			self.cache = []

# def post_record(record, address, debug):
# 	debug.log(f"sending {record} to {address}")
# 	res = requests.post(f"{address}/new-entry", json=record)
# 	debug.log(f"request response: {res.status_code}")

class RandomNoise:
	def __init__(self, freqs, speed, minimum, maximum):
		self.freqs = [random.random() for _ in range(freqs)]
		self.speed = speed
		self.t = 0
		self.minimum = minimum
		self.maximum = maximum

	def get_noise(self):
		self.t += self.speed
		n = 0
		for freq in self.freqs: # add a bunch of sins to make smooth noise
			n += math.sin(self.t * freq) / len(self.freqs)
		n = (n + 1) / 2 * (self.maximum - self.minimum) + self.minimum
		return n

class Debugger:
	def __init__(self, verbose):
		self.verbose = verbose

	def log(self, text):
		if self.verbose:
			print(text)
