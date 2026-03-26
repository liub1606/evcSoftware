import tkinter as tk
from tkinter import ttk
# pip3 install matplotlib
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
import numpy as np
import utm
# pip3 install utm
import serial
# pip3 install pyserial
import os
import datetime
import time

serialport = '/dev/cu.usbserial-CMCHb112318'

playbacktick_ms = 100
# TODO: comment this line out to record a live session
#playbackfilename = 'data/20250515_rollingtrial1/evclog_20250515T153252.txt'
#playbackfilename = 'data/20250515_rollingtrial1/evclog_20250515T150324.txt'
#playbackfilename = 'data/20250515_rollingtrial1/evclog_20250515T153252.txt'
#playbackfilename = 'data/20250520_rollingtrial2/evclog_20250520T150340.txt'
playbackfilename = None # this is for live data


# open a log file to save all recorded data
# TODO: do not log a playbackfilename
if playbackfilename is None:
    t = datetime.datetime.now()
    datetimecode = t.strftime("%Y%m%dT%H%M%S")
    logfilename = 'evclog_{}.txt'.format( datetimecode )
    print( 'logfile: {}'.format( logfilename ) )
    logfile = open( logfilename, "wb", buffering=0 )

# 2023 UW EVC Track Near UW Terminal centreline estimate
# x = 537241 .. 537029
# y = 4813834 .. 4813580
# local datum origin [537000 4813000]
# xlim=(0, 265), ylim=(550, 860)

# LHSS Test Track Lat Lon
# x: 532773 .. 532716
# y: 4813263 .. 4813202
# local datum origin [532000 4813000]
# xlim=(710, 780), ylim=(195, 270)

# Old Oak Park Test Track Lat Lon
# x: 533698 .. 533451
# y: 4813303 .. 4813078
# local datum origin [533000 4813000]
# xlim=(425, 725), ylim=(50, 330)


def volts2soc_agm( v ):
    volts = [10.5, 11.51, 11.66, 11.81, 11.95, 12.05, 12.15, 12.3, 12.5, 12.75, 12.8, 13.]
    soc = [0., 10., 20., 30., 40., 50., 60., 70., 80., 90., 99., 100.]

    i = np.searchsorted( volts, v )
    
    if i == 0:
        s = soc[0]
    if i == len(volts):
        s = soc[-1]
    else:
        x1 = volts[i-1]
        x2 = volts[i]
        y1 = soc[i-1]
        y2 = soc[i]
        m = (y2 - y1) / (x2 - x1)
        s = y1 + (v - x1) * m
    return s


class App(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        #self.pack(side="top", fill="both", expand=True)
        self.grid()

        # Create the application variable.
        self.nowVolts = tk.StringVar()
        self.nowVoltsMax1 = tk.StringVar()
        self.nowVoltsMin1 = tk.StringVar()
        self.nowAmps = tk.StringVar()
        self.nowPower = tk.StringVar()
        self.nowSpeed = tk.StringVar()
        self.nowSpeedAvg = tk.StringVar()
        self.nowAcceleration = tk.StringVar()
        self.nowLat = tk.StringVar()
        self.nowLon = tk.StringVar()
        self.nowX = tk.StringVar()
        self.nowY = tk.StringVar()
        self.nowBatt0 = tk.StringVar()
        self.nowBattSOC = tk.StringVar()
        self.nowBattIntR = tk.StringVar()
        self.nowAh = tk.StringVar()
        self.nowWh = tk.StringVar()
        self.Ah = 0.
        self.Wh = 0.
        self.lastChartDraw = np.datetime64( time.time_ns(), 'ns')

        # initialize some data stores
        self.data_time = np.array([], dtype='datetime64[ms]')
        self.data_volts = np.array([], dtype=float)
        self.data_amps = np.array([], dtype=float)
        self.data_power = np.array([], dtype=float)
        self.data_speed = np.array([], dtype=float)
        self.data_acceleration = np.array([], dtype=float)
        self.data_Ah = np.array([], dtype=float)
        self.data_Wh = np.array([], dtype=float)

        # create GUI frames
        self.frameNow = tk.Frame(self)
        self.frameNow.grid(column=0, row=0)

        self.frameGraphs = tk.Frame(self)
        self.frameGraphs.grid(column=1, row=0)

        # left side text data
        tk.Label(self.frameNow, text="Voltage").grid(column=0, row=0, padx=10, pady=10)
        tk.Entry(self.frameNow, width=13, justify="right", textvariable=self.nowVolts).grid(column=1, row=0, padx=10, pady=10)
        tk.Label(self.frameNow, text="(max 1-min)").grid(column=0, row=1, padx=10, pady=10)
        tk.Entry(self.frameNow, width=13, justify="right", textvariable=self.nowVoltsMax1).grid(column=1, row=1, padx=10, pady=(0,10))
        tk.Label(self.frameNow, text="(min 1-min)").grid(column=0, row=2, padx=10, pady=10)
        tk.Entry(self.frameNow, width=13, justify="right", textvariable=self.nowVoltsMin1).grid(column=1, row=2, padx=10, pady=(0,10))
        tk.Label(self.frameNow, text="Amps").grid(column=0, row=3, padx=10, pady=(0,10))
        tk.Entry(self.frameNow, width=13, justify="right", textvariable=self.nowAmps).grid(column=1, row=3, padx=10, pady=(0,10))
        tk.Label(self.frameNow, text="Power").grid(column=0, row=4, padx=10, pady=(0,10))
        tk.Entry(self.frameNow, width=13, justify="right", textvariable=self.nowPower).grid(column=1, row=4, padx=10, pady=(0,10))

        tk.Label(self.frameNow, text="Speed").grid(column=0, row=5, padx=10, pady=(0,10))
        tk.Entry(self.frameNow, width=13, justify="right", textvariable=self.nowSpeed).grid(column=1, row=5, padx=10, pady=(0,10))
        tk.Label(self.frameNow, text="(avg. 1-min)").grid(column=0, row=6, padx=10, pady=(0,10))
        tk.Entry(self.frameNow, width=13, justify="right", textvariable=self.nowSpeedAvg).grid(column=1, row=6, padx=10, pady=(0,10))
        tk.Label(self.frameNow, text="Acceleration").grid(column=0, row=7, padx=10, pady=(0,10))
        tk.Entry(self.frameNow, width=13, justify="right", textvariable=self.nowAcceleration).grid(column=1, row=7, padx=10, pady=(0,10))

        tk.Label(self.frameNow, text="Latitude").grid(column=0, row=8, padx=10, pady=(0,10))
        tk.Entry(self.frameNow, width=13, justify="right", textvariable=self.nowLat).grid(column=1, row=8, padx=10, pady=(0,10))
        tk.Label(self.frameNow, text="Longitude").grid(column=0, row=9, padx=10, pady=(0,10))
        tk.Entry(self.frameNow, width=13, justify="right", textvariable=self.nowLon).grid(column=1, row=9, padx=10, pady=(0,10))
        tk.Label(self.frameNow, text="UTM Easting").grid(column=0, row=10, padx=10, pady=(0,10))
        tk.Entry(self.frameNow, width=13, justify="right", textvariable=self.nowX).grid(column=1, row=10, padx=10, pady=(0,10))
        tk.Label(self.frameNow, text="UTM Northing").grid(column=0, row=11, padx=10, pady=(0,10))
        tk.Entry(self.frameNow, width=13, justify="right", textvariable=self.nowY).grid(column=1, row=11, padx=10, pady=(0,10))

        tk.Label(self.frameNow, text="Batt. Unl. V").grid(column=0, row=12, padx=10, pady=(0,10))
        tk.Entry(self.frameNow, width=13, justify="right", textvariable=self.nowBatt0).grid(column=1, row=12, padx=10, pady=(0,10))
        tk.Label(self.frameNow, text="Batt. SOC").grid(column=0, row=13, padx=10, pady=(0,10))
        tk.Entry(self.frameNow, width=13, justify="right", textvariable=self.nowBattSOC).grid(column=1, row=13, padx=10, pady=(0,10))
        tk.Label(self.frameNow, text="Batt. Int. R").grid(column=0, row=14, padx=10, pady=(0,10))
        tk.Entry(self.frameNow, width=13, justify="right", textvariable=self.nowBattIntR).grid(column=1, row=14, padx=10, pady=(0,10))

        tk.Label(self.frameNow, text="Capacity").grid(column=0, row=15, padx=10, pady=(0,10))
        tk.Entry(self.frameNow, width=13, justify="right", textvariable=self.nowAh).grid(column=1, row=15, padx=10, pady=(0,10))
        tk.Label(self.frameNow, text="Energy").grid(column=0, row=16, padx=10, pady=(0,10))
        tk.Entry(self.frameNow, width=13, justify="right", textvariable=self.nowWh).grid(column=1, row=16, padx=10, pady=(0,10))

        # telemetry charts
        self.figChart, (self.ax1, self.ax2, self.ax3) = plt.subplots(3,1, figsize=(12,4.5), dpi=50)
        self.ax1.set_ylabel( 'Voltage' )
        self.ax2.set_ylabel( 'Amps' )
        self.ax3.set_ylabel( 'Speed' )
        self.canvas1 = FigureCanvasTkAgg(self.figChart, master = self.frameGraphs)
        self.canvas1.get_tk_widget().grid(row = 0, column = 0)

        # map, transfer functions
        self.figMap, (self.ax4, self.ax5, self.ax6) = plt.subplots(1,3, figsize=(12,3), dpi=50)
        self.ax4.set_ylabel( 'Northing [m]' )
        self.ax4.set_xlabel( 'Easting [m]' )
        self.ax4.axis( 'equal' )
        self.ax4.set(xlim=(0, 265), ylim=(550, 860))

        self.canvas2 = FigureCanvasTkAgg(self.figMap, master = self.frameGraphs)
        self.canvas2.get_tk_widget().grid(row = 1, column = 0)


    def update_charts( self ):
            xlabels = [f'{x:}' for x in range(-5,1,1)]
            #xticks = xticks * 60000 + self.current_timestamp_ms
            xticks = [np.timedelta64( x, 'm' ) for x in range(-5,1,1)] + self.current_timestamp_ns

            # find time slice index
            index1min = np.searchsorted( self.data_time, xticks[4] )
            index5min = np.searchsorted( self.data_time, xticks[0] )

            self.ax1.clear()
            self.ax1.set_ylabel( 'Voltage' )
            self.ax1.set( xlim=(xticks[0], xticks[5]) )
            self.ax1.tick_params(axis='both', labelbottom=False, labelleft=True)
            self.ax1.set_xticks( xticks,  labels=xlabels )
            self.ax1.plot( self.data_time[index5min:index1min+1], self.data_volts[index5min:index1min+1] )
            self.ax1.plot( self.data_time[index1min:], self.data_volts[index1min:] )
            imax1 = np.argmax( self.data_volts[index1min:] )
            imin1 = np.argmin( self.data_volts[index1min:] )
            self.ax1.scatter( [self.data_time[index1min:][imax1]], [self.data_volts[index1min:][imax1]], color='g' )
            self.ax1.scatter( [self.data_time[index1min:][imin1]], [self.data_volts[index1min:][imin1]], color='r' )
            self.ax1.grid()
            self.nowVoltsMax1.set( '{:.3f} V'.format(self.data_volts[index1min:][imax1]) )
            self.nowVoltsMin1.set( '{:.3f} V'.format(self.data_volts[index1min:][imin1]) )

            self.ax2.clear()
            self.ax2.set_ylabel( 'Amps' )
            self.ax2.set( xlim=(xticks[0], xticks[5]) )
            self.ax2.tick_params(axis='both', labelbottom=False, labelleft=True)
            self.ax2.set_xticks( xticks,  labels=xlabels )
            self.ax2.plot( self.data_time[index5min:index1min+1], self.data_amps[index5min:index1min+1] )
            self.ax2.plot( self.data_time[index1min:], self.data_amps[index1min:] )
            self.ax2.grid()

            self.ax3.clear()
            self.ax3.set_ylabel( 'Speed' )
            self.ax3.set_xlabel( 'Minutes' )
            self.ax3.set( xlim=(xticks[0], xticks[5]) )
            self.ax3.set_xticks( xticks,  labels=xlabels )
            self.ax3.plot( self.data_time[index5min:index1min+1], self.data_speed[index5min:index1min+1] )
            avgspeed = np.average(self.data_speed[index1min:])
            self.ax3.plot( self.data_time[index1min:], self.data_speed[index1min:] )
            self.ax3.plot( [xticks[-2], xticks[-1]], [avgspeed, avgspeed], linestyle='dashed', linewidth=1.5, color='r' )
            self.ax3.grid()

            self.nowSpeedAvg.set( '{:.1f} km/h'.format(avgspeed) )

            self.canvas1.draw()

            self.ax5.clear()
            self.ax5.set_ylabel( 'Voltage' )
            self.ax5.set_xlabel( 'Amps' )
            self.ax5.scatter( self.data_amps[index5min:index1min+1], self.data_volts[index5min:index1min+1], marker='.' )
            self.ax5.scatter( self.data_amps[index1min:], self.data_volts[index1min:], marker='.' )
            m,b = np.polyfit( self.data_amps[index1min:], self.data_volts[index1min:], 1 )
            self.nowBatt0.set( '{:.2f} V'.format( b ) )
            if b > 17:
                # 24V configuration
                soc = volts2soc_agm(b/2)
            else:
                # 12V configuration
                soc = volts2soc_agm(b)
            self.nowBattSOC.set( '{:.1f} %'.format( soc ) )
            self.nowBattIntR.set( '{:.1f} mΩ'.format(-1000*m) )
            x2 = np.max( self.data_amps[index1min:] )
            y2 = b + m * x2
            self.ax5.plot( [0, x2], [b, y2], linestyle='dashed', linewidth=1.5, color='black' )
            
            self.ax6.clear()
            #self.ax6.set_ylabel( 'Amps' )
            self.ax6.set_xlabel( 'Acceleration' )
            #self.ax6.scatter( self.data_acceleration, self.data_amps[1:-1], marker='.' )
            self.ax6.hist( self.data_acceleration[index1min:], bins=20, edgecolor="white" )

            self.canvas2.draw()


    def process_telemetry_record( self, record ):
        #self.current_timestamp_ms = np.datetime64('now', 'ms') # 'now' seems to only have second-resolution
        self.current_timestamp_ns = np.datetime64( time.time_ns(), 'ns')
        try:
            # TODO: relocate the software calibration settings ...
            BusV = float( record[0] )
            Current = float( record[1] ) * 0.25
            Power = float( record[2] ) * 0.25
            HallSpeed = float( record[3] ) * 1.75

            # TODO: move sanity check limits elsewhere
            # Note: 12V battery maximum charge voltage 14.7V (6x 2.45V/cell)
            # Sanity check using 30V max for 24V race
            if BusV > 30 or BusV < 0:
                return # skip record
            if Current > 75 or Current < 0:
                return # skip record
            if HallSpeed > 50 or HallSpeed < 0:
                return # skip record


            if len(self.data_speed) >= 2 and len(self.data_time) >= 2:
                # calculate accelerator using central difference method; calculation is lagging by one measurement
                dt = (self.current_timestamp_ns - self.data_time[-2]) / np.timedelta64( 1, 's' )
                Acceleration = (HallSpeed - self.data_speed[-2]) / dt
                #Acceleration = (HallSpeed - self.data_speed[-2])
                # km / h / s
                # *1000  km -> m
                # /3600  h -> s
                Acceleration = Acceleration / 3.6     # unit converstion to m/s2
                self.nowAcceleration.set( '{:.2f} m/s²'.format(Acceleration) )
                self.data_acceleration = np.append( self.data_acceleration, Acceleration )

                # calculate capacity and energy
                dth = (self.current_timestamp_ns - self.data_time[-1]) / np.timedelta64( 1, 'h' )
                self.Ah = self.Ah + (self.data_amps[-1] + Current) / 2. * dth
                self.Wh = self.Wh + (self.data_power[-1] + Power) / 2. * dth
                self.nowAh.set( '{:.3f} Ah'.format(self.Ah) )
                self.nowWh.set( '{:.1f} Wh'.format(self.Wh) )
                self.data_Ah = np.append( self.data_Ah, self.Ah )
                self.data_Wh = np.append( self.data_Wh, self.Wh )

            # put data on display
            self.nowVolts.set( record[0] + ' V' )
            #self.nowAmps.set( record[1] + ' A' )
            self.nowAmps.set( '{:.2f} A'.format(Current) )
            #self.nowPower.set( record[2] +' W' )
            self.nowPower.set( '{:.0f} W'.format(Power) )
            #self.nowSpeed.set( record[3] + ' km/h' )
            self.nowSpeed.set( '{:.1f} km/h'.format(HallSpeed) )


            # append data and update plots
            self.data_time = np.append( self.data_time, self.current_timestamp_ns )
            self.data_volts = np.append( self.data_volts, BusV )
            self.data_amps = np.append( self.data_amps, Current )
            self.data_power = np.append( self.data_power, Power )
            self.data_speed = np.append( self.data_speed, HallSpeed )

################
            t_draw = self.current_timestamp_ns - self.lastChartDraw
            if t_draw > np.timedelta64( 5, 's' ):
                print( 'redraw charts' )
                self.update_charts()
                self.lastChartDraw = self.current_timestamp_ns


        except ValueError:
            #None
            print( 'not a valid telemetry record' )


def process_record( record ):
    global myapp
    if '~' == record[0] and '~' == record[-1]:
        print( 'GSP data' )
    else:
        record = record.split(',')
        if len(record) == 4:
            myapp.process_telemetry_record( record )


# this works on string objects not bytes
def index_newline_str( record ):
    i = None
    if '\r' in record:
        i = record.index( '\r' )
    if '\n' in record:
        i2 = record.index( '\n' )
        if i == None:
            i = i2
        else:
            i = min( i, i2 )
    return i


def index_newline( record ):
    for i,val in enumerate(record):
        if val == 10:
            return i
        if val == 13:
            return i


raw_data = b''
def process_rawdata( data ):
    global raw_data
    raw_data = raw_data + data

    i = index_newline( raw_data )

    if i is not None:
        record = raw_data[:i]
        raw_data = raw_data[i+1:]
        try:
            if len(record) > 0:
                record = record.decode('utf8')
                print( 'recieved: {}'.format( record ) )
            process_record( record )
        except:
           None


def data_event( file, mask ):
    if mask & tk.READABLE:
        while True:
            data = os.read( file.fileno(), 256 )
            if playbackfilename is None:
                logfile.write( data )
            if len(data) == 0:
                break
            #print( 'read: {}'.format( data ) )
            process_rawdata(data)

    if mask & tk.EXCEPTION:
        print( 'exception on serial port' )


def playbackfile_tick( playbackfile, root ):
    c = playbackfile.read(1)
    # clear space and newlines
    while c.isspace():
        c = playbackfile.read(1)

    # process until space and newlines
    while not c.isspace() and c != b'':
        process_rawdata( c )
        c = playbackfile.read(1)

    process_rawdata( b'\r' )
    process_rawdata( b'\n' )

    # setup next line read
    root.after( playbacktick_ms, playbackfile_tick, playbackfile, root )
	

root = tk.Tk()
root.title("LHSS Bolt Telemetry")
#root.config(bg="skyblue")
myapp = App(root)

if playbackfilename is not None:
    print( 'opening playback file: {}'.format( playbackfilename ) )
    playbackfile = open( playbackfilename, 'rb' )
    root.after( playbacktick_ms, playbackfile_tick, playbackfile, root )
    
else:
    print( 'opening serial port: {}'.format( serialport ) )
    # open serial port and connect event to callback
    ser = serial.Serial( serialport, 9600 )
    root.createfilehandler( ser, tk.READABLE | tk.EXCEPTION, data_event )


try:
    myapp.mainloop()
except Exception as err:
    print(Exception, err)

# close files and write big data file
if playbackfilename is not None:
    logfile.close()

# playbackfilename = None
npz_filename = logfilename[:-3]+'npz'
print( 'writing: {}'.format( npz_filename ) )
np.savez( npz_filename,
        data_time         = myapp.data_time,
	data_volts        = myapp.data_volts,
        data_amps         = myapp.data_amps,
        data_power        = myapp.data_power,
        data_speed        = myapp.data_speed,
        data_acceleration = myapp.data_acceleration,
        data_Ah           = myapp.data_Ah,
        data_Wh           = myapp.data_Wh )
