from serial_emu import *
from helpers import *
import configparser
import numpy as np
import argparse
import serial
import time

# argparse stuff
argparser = argparse.ArgumentParser(
	prog="python host.py",
	description="reads serial data about the car and sends it to a server to be broadcast to viewers")
argparser.add_argument(
	"-e", "--emulator-port", required=False, nargs='?', default=None,
	help="serial port for emulator to write to in case of testing")
argparser.add_argument(
	"-s", "--server-address", required=False, nargs='?',  default=None,
	help="address to post new records to (optional, use for public functionality)")
argparser.add_argument(
	"-c", "--config", required=False, nargs='?',  default="telem-conf.ini",
	help="ini config file (default: telem-conf.ini)")
argparser.add_argument(
	"-v", "--verbose", action="count", default=0,
	help="verbosity (1 to 3))")
argparser.add_argument(
	"serial_port",
	help="serial port to read from (testing? use 'socat -d2 pty pty' to make a pty)")
args = argparser.parse_args()

emulator_port = args.emulator_port
server_addr = args.server_address
conf_file = args.config
serial_port = args.serial_port
info_debug = Debugger(args.verbose >= 1) # debugger for general information
data_debug = Debugger(args.verbose >= 2) # debugger for data (fills console)

# config file stuff
config = configparser.ConfigParser()
config.read(args.config)

write_freq = float(config["general"]["write_freq"])
read_freq = float(config["general"]["read_freq"])

busv_fac = float(config["calibration"]["busv_fac"])
current_fac = float(config["calibration"]["current_fac"])
power_fac = float(config["calibration"]["power_fac"])
hall_speed_fac = float(config["calibration"]["hall_speed_fac"])

busv_lim = (float(config["limits"]["busv_min"]), int(config["limits"]["busv_max"]))
current_lim = (float(config["limits"]["current_min"]), int(config["limits"]["current_max"]))
hall_speed_lim = (float(config["limits"]["hall_speed_min"]), int(config["limits"]["hall_speed_max"]))

uploader = Uploader(int(config["general"]["cache_size"]), server_addr, info_debug)

# setup emulator
if emulator_port is not None:
	emu = VirtualSerial(emulator_port, write_freq, (
		("busv", (10 / busv_fac, 13 / busv_fac, 0.1)),
		("current", (0 / current_fac, 50 / current_fac, 0.1)),
		("power", (0 / power_fac, 650 / power_fac, 0.1)),
		("hall_speed", (0 / hall_speed_fac, 30 / hall_speed_fac, 0.1))), args.verbose >= 3)
	emu.start()

info_debug.log(f"connecting to serial port {serial_port}")
ser = serial.Serial(serial_port, 9600, timeout=0)
info_debug.log("successfully connected")

rawdata = b""


# continuously poll serial and process records
def poll_serial(ser):
	while 1:
		start = time.time()
		try:
			data = ser.read(256)
			# data_debug.log(data)
			if data:
				process_rawdata(data)
			else:
				data_debug.log("empty")

		except serial.SerialException as e:
			info_debug.log(f"serial error: {e}")

		time.sleep(max(0, 1 / read_freq - (time.time() - start)))
		# print("read with console, nonfunctional for now")

# process raw bytedata from serial
def process_rawdata(data):
	global rawdata
	rawdata += data
	i = index_newline(rawdata)

	if i is not None:
		record = rawdata[:i]
		rawdata = rawdata[i+1:]
		try:
			if len(record) > 0:
				record = record.decode("utf8")
				data_debug.log(f"record received: {record}")
			process_record(record)

		except Exception as e:
			info_debug.log(f"exception: {e}")

# process slightly less raw string data
def process_record(record):
	if '~' == record[0] and '~' == record[-1]:
		data_debug.log("GSP data") # i have no clue what this means but ok

	else:
		record = record.split(',')
		if len(record) == 4:
			process_telemetry_record(record)

# actually process record
def process_telemetry_record(record):
	try:
		busv = float(record[0]) * busv_fac # volts
		current = float(record[1]) * current_fac # amps
		power = float(record[2]) * power_fac # watts
		hall_speed = float(record[3]) * hall_speed_fac # km/h

		if not busv_lim[0] < busv < busv_lim[1]:
			return # skip record
		if not current_lim[0] < current < current_lim[1]:
			return # skip record
		if not hall_speed_lim[0] < hall_speed < hall_speed_lim[1]:
			return # skip record

		data_debug.log('\n'.join([
			f"busv: {busv} volts",
			f"current: {current} amps",
			f"power: {power} watts",
			f"hall speed: {hall_speed} km/h", '']))

		if server_addr is not None:
			uploader.new_record({
				"timestamp": time.time_ns(), # timestamp in unix nanoseconds
				"busv": busv,
				"current": current,
				"power": power,
				"hall_speed": hall_speed})

	except ValueError:
		info_debug.log("invalid telemetry record")

poll_serial(ser)
