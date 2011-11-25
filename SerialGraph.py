import os
import sys
import time
import optparse
import serial
import SerialData
import wx
import matplotlib

matplotlib.use('WXAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import \
	FigureCanvasWxAgg as FigCanvas, \
	NavigationToolbar2WxAgg as NavigationToolbar
	
import numpy as np
import pylab

REFRESH_INTERVAL_MS = 10
DEBUG = False

def processArguments():
	"""Handle cli args"""
	parser = optparse.OptionParser(version="%prog 0.1")
	parser.set_usage("%prog [options]\nGraph arbitrary data received from serial port")
	parser.add_option("-p", "--port", dest="port", default="/dev/tty.usbserial", help="Serial port. Default: %default")
	parser.add_option("-b", "--baudrate", dest="baudrate", default=9600, help="Baud rate. Default: %default")
	parser.add_option("-d", "--debug", action="store_true", dest="debug", help="Enable debugging messages")
	(options, args) = parser.parse_args()
	return options, args

class GraphFrame(wx.Frame):
	title = 'SerialGraph'
	def __init__(self, data):
		self.datasource = data
		self.data = [self.datasource.next()]
		wx.Frame.__init__(self, None, -1, self.title)
		self.create_main_panel()
		self.redraw_timer = wx.Timer(self)
		self.Bind(wx.EVT_TIMER, self.on_redraw_timer, self.redraw_timer)
		self.redraw_timer.Start(REFRESH_INTERVAL_MS)
		self.paused = False
		self.max = 0.0
		
	def create_main_panel(self):
		self.panel = wx.Panel(self)
		self.init_plot()
		self.canvas = FigCanvas(self.panel, -1, self.fig)

		self.pause_button = wx.Button(self.panel, -1, "Pause")
		self.Bind(wx.EVT_BUTTON, self.on_pause_button, self.pause_button)
		self.Bind(wx.EVT_UPDATE_UI, self.on_update_pause_button, self.pause_button)
		
		self.reset_button = wx.Button(self.panel, -1, "Reset")
		self.Bind(wx.EVT_BUTTON, self.on_reset_button, self.reset_button)
		self.Bind(wx.EVT_UPDATE_UI, self.on_update_reset_button, self.reset_button)
		
		self.hbox1 = wx.BoxSizer(wx.HORIZONTAL)
		self.hbox1.Add(self.pause_button, border=5, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL)
		self.hbox1.AddSpacer(20)
		self.hbox1.Add(self.reset_button, border=5, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL)
#		self.hbox1.AddSpacer(20)

		self.vbox = wx.BoxSizer(wx.VERTICAL)
		self.vbox.Add(self.canvas, 1, flag=wx.LEFT | wx.TOP | wx.GROW)
		self.vbox.Add(self.hbox1, 0, flag=wx.ALIGN_LEFT | wx.TOP)
		
		self.panel.SetSizer(self.vbox)
		self.vbox.Fit(self)
	
	def init_plot(self):
		self.dpi = 200
		self.fig = Figure((5.0, 3.0), dpi=self.dpi)
		self.axes = self.fig.add_subplot(111, xlabel="ms", ylabel="mW")
		self.axes.set_axis_bgcolor('black')
		self.axes.set_title('test', size=12)
		pylab.setp(self.axes.get_xticklabels(), fontsize=8)
		pylab.setp(self.axes.get_yticklabels(), fontsize=8)
		self.plot_data = self.axes.plot (
			self.data,
			linewidth = 1,
			color = (1, 1, 0)
		)[0]
		
	def on_pause_button(self, event):
		self.paused = not self.paused
		
	def on_reset_button(self, event):
		self.data = []
		self.max = 0
		
	def on_update_pause_button(self, event):
		if self.paused:
			label = "Resume"
		else:
			label = "Pause"
		self.pause_button.SetLabel(label)
		
	def on_update_reset_button(self, event):
		pass
	
	def on_redraw_timer(self, event):
		if not self.paused:
			self.data.append(self.datasource.next())
		
		self.draw_plot()
	
	def draw_plot(self):
		"""Redraws the plot"""
		width = 50
		xmax = len(self.data) if len(self.data) > width else width
		xmin = xmax - width
#		ymin = round(min(self.data), 0) - 1
		ymin = 0

		if len(self.data) > width:
			visible_max = max(self.data[-width:])
			ymax = int(max(visible_max*1.2, 5))
#			ymax = max(max(self.data[-width:]), 5) + 1
		else:
			ymax = max(round(max(self.data), 0), 4) + 1
		

		self.axes.set_xbound(lower=xmin, upper=xmax)
		self.axes.set_ybound(lower=ymin, upper=ymax)
		self.axes.grid(True, color='green')

		self.plot_data.set_xdata(np.arange(len(self.data)))
		self.plot_data.set_ydata(np.array(self.data))
		if self.data[-1] > self.max:
			self.max = self.data[-1]
		self.axes.set_title('Current Value: %s.   Max Value: %s.' % (self.data[-1], self.max), size=12)	
		self.canvas.draw()

def main():
	global DEBUG
	options = processArguments()
	DEBUG = options[0].debug
	s = SerialData.SerialData(
		port=options[0].port, 
		baudrate=options[0].baudrate, 
		bytesize=serial.EIGHTBITS,
		parity=serial.PARITY_NONE,
		stopbits=serial.STOPBITS_ONE,
		xonxoff=0,
		rtscts=0,
		debug=DEBUG
	)
	app = wx.PySimpleApp()
	app.frame = GraphFrame(s)
	app.frame.Show()
	app.MainLoop()

if __name__ == '__main__':
	main()