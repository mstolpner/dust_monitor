import PySimpleGUI as sg
from PMS import PMS
import time

class Dashboard:

	# Data collection
	_timeSeriesHours = 4	# 4 hours of graphing
	_averageOverSeconds = 60
	_maxDataPoints = None
	_xAxisMin = 0			# Leave room for ticks
	_xAxisMax = None
	_yAxisMin = 0			# Leave room for ticks
	_yAxisMax = None
	_plotData = []			# Data for Plot
	_series = []			
	_seriesStartTimeSeconds = None

	# Window Configuration
	_xScreenSize = None
	_yScreenSize = None
	_windowLoopDelayMs = 100

	# Look and feel
	_backgrounColor	= 'black'
	_font 			= 'Helvetica'
	_textColor 		= "white"
	_labelColor 	= "grey"
	_plotBackground	= "black"
	_plotColor 		= "grey"
	_plotAxisColor 	= "grey"
	_plotLabelColor	= "darkcyan"
	_fontSizeFractionOfScreenY = 0.12
	_fontSize = None
	_labelFontSize = None
	_axisLabelFontSize = None

	# Active GUI Objects
	_v03  = None
	_v05  = None
	_v10  = None
	_v25  = None
	_v50  = None
	_v100 = None
	_pm10  = None
	_pm25  = None
	_pm100 = None
	_graph = None
	_window = None

	def __init__(self):
		# Initialize All Variables
		self._xScreenSize, self._yScreenSize = sg.Window.get_screen_size()
		self._fontSize = int(self._yScreenSize * self._fontSizeFractionOfScreenY)
		self._labelFontSize = round(self._fontSize * .5)
		self._axisLabelFontSize = round(self._fontSize * .3)
		self._maxDataPoints = int(self._timeSeriesHours * 60 * 60 / self._averageOverSeconds)
		self._xAxisMax = self._maxDataPoints
		self._seriesStartTimeSeconds = round(time.time())

		# Build the screen layout
		sg.theme(self._backgrounColor)

		# Volume Title Fields
		vtfont = (self._font, self._labelFontSize)
		vtcolor = self._labelColor
		vtsize = (6,1)
		vt03  = sg.Text('>0.3 µ', font=vtfont, text_color=vtcolor, size=vtsize)
		vt05  = sg.Text('>0.5 µ', font=vtfont, text_color=vtcolor, size=vtsize)
		vt10  = sg.Text('>1.0 µ', font=vtfont, text_color=vtcolor, size=vtsize)
		vt25  = sg.Text('>2.5 µ', font=vtfont, text_color=vtcolor, size=vtsize)
		vt50  = sg.Text('>5.0 µ', font=vtfont, text_color=vtcolor, size=vtsize)
		vt100 = sg.Text('>10. µ', font=vtfont, text_color=vtcolor, size=vtsize)

		# Volume Cells
		vfont = (self._font, self._fontSize)
		vcolor = self._textColor
		vsize = (6,1)
		self._v03  = sg.Text('0', font=vfont, text_color=vcolor, size=vsize)
		self._v05  = sg.Text('0', font=vfont, text_color=vcolor, size=vsize)
		self._v10  = sg.Text('0', font=vfont, text_color=vcolor, size=vsize)
		self._v25  = sg.Text('0', font=vfont, text_color=vcolor, size=vsize)
		self._v50  = sg.Text('0', font=vfont, text_color=vcolor, size=vsize)
		self._v100 = sg.Text('0', font=vfont, text_color=vcolor, size=vsize)

		# PM Title Cells 
		pmtfont = (self._font, self._labelFontSize)
		pmtcolor = self._labelColor
		pmtsize = (7,1)
		pmt10  = sg.Text('PM 1.0',  font=pmtfont, text_color=pmtcolor, size=pmtsize)
		pmt25  = sg.Text('PM 2.5',  font=pmtfont, text_color=pmtcolor, size=pmtsize)
		pmt100 = sg.Text('PM 10',   font=pmtfont, text_color=pmtcolor, size=pmtsize)

		# PM Cells
		pmfont = (self._font, self._fontSize)
		pmcolor = self._textColor
		pmsize = (4,1)
		self._pm10  = sg.Text('', font=pmfont, text_color=pmcolor, size=pmsize)
		self._pm25  = sg.Text('', font=pmfont, text_color=pmcolor, size=pmsize)
		self._pm100 = sg.Text('', font=pmfont, text_color=pmcolor, size=pmsize)

		# PM Unit Cells
		pufont = (self._font, self._labelFontSize)
		pucolor = self._labelColor
		pusize = (8,1)
		pu10  = sg.Text('µg/m³', font=pufont, text_color=pucolor, size=pusize)
		pu25  = sg.Text('µg/m³', font=pufont, text_color=pucolor, size=pusize)
		pu100 = sg.Text('µg/m³', font=pufont, text_color=pucolor, size=pusize)

		# Plot area, logical space will be dynamically redefined during execution
		self._graph = sg.Graph( canvas_size=(int(self._xScreenSize/1.9), int(self._yScreenSize/2.2)),
								graph_bottom_left=(self._xAxisMin, self._yAxisMin),
								graph_top_right=(self._xAxisMax, self._yAxisMax), 
								expand_x=True, expand_y=True, 
								background_color=self._backgrounColor)

		leftColumn = [
			[vt03, self._v03],
			[vt05, self._v05],
			[vt10, self._v10],
			[vt25, self._v25],
			[vt50, self._v50],
			[vt100, self._v100]
		]

		rightColumn = [
			[pmt10, self._pm10 ,pu10],
			[pmt25, self._pm25, pu25],
			[pmt100, self._pm100 ,pu100],
			[self._graph]
		]

		layout = [
			[ sg.Column(leftColumn), sg.Column(rightColumn) ]
		]

		# Create the Window
		self._window = sg.Window('Air Dust Monitor', layout, 
									location=(0,0), size=(self._xScreenSize, self._yScreenSize), 
									keep_on_top=True, finalize=True) 
		self._window.set_cursor("none")
		self._window.Maximize()

	def _addDataPoint(self, value):
		self._series.append(value)
		if round(time.time()) - self._seriesStartTimeSeconds >= self._averageOverSeconds:
			self._seriesStartTimeSeconds = round(time.time())
			self._plotData.append(int(sum(self._series)/len(self._series)))
			self._series = []
			# trancate array to keep only maxDataPoints
			if len(self._plotData) > self._maxDataPoints:
				self._plotData = self._plotData[1:]
			return True
		# Data has not changed yet
		return False

	def _drawPlot(self):
		if len(self._plotData) > 0:
			self._graph.erase()
			# Recalculate Y scale based on newly acquired data 
			self._yAxisMax = max(self._plotData)
			self._yAxisMin = int(self._yAxisMax * 0.1) * -1
			self._graph.change_coordinates((self._xAxisMin, self._yAxisMin), (self._xAxisMax, self._yAxisMax))
			# plot
			for i, value in enumerate(self._plotData):
				self._graph.DrawLine((i, 0), (i, value), color=self._plotColor)
			# draw X axis
			self._graph.DrawLine((0, 0), (self._xAxisMax, 0), self._plotAxisColor)
			for i in range(1, self._timeSeriesHours + 1):
				x = int(self._xAxisMax/4*i)
				self._graph.DrawLine((x-1, -int(self._yAxisMin)/10), (x-1, int(self._yAxisMin)/10), color=self._plotAxisColor)
			self._graph.DrawText(str(self._timeSeriesHours) + 'hours  ', (self._xAxisMax, 0), color=self._plotLabelColor, 
							font = (self._font, self._axisLabelFontSize), text_location=sg.TEXT_LOCATION_BOTTOM_RIGHT)
			# draw Y axis after drawing the plot so the ticks are over the bars
			self._graph.DrawLine((0, 0), (0, self._yAxisMax), color=self._plotAxisColor)
			self._graph.DrawText(self._yAxisMax, (10, int(self._yAxisMax*.95)), color=self._plotLabelColor, font = (self._font, self._axisLabelFontSize), text_location=sg.TEXT_LOCATION_TOP_LEFT)

	def monitor(self, sensor):
		while True:
			event, values = self._window.read(timeout=self._windowLoopDelayMs)
			if event == sg.WIN_CLOSED: 
				self._window.close()
				break

			if sensor.recievePmsTransmission(debug=False):
				# Update Values on the screen
				self._v03.Update(value=str(sensor.gt03um)) # - sensor.gt05um - sensor.gt10um - sensor.gt25um - sensor.gt50um - sensor.gt100um))
				self._v05.Update(value=str(sensor.gt05um)) # - sensor.gt10um - sensor.gt25um - sensor.gt50um - sensor.gt100um))
				self._v10.Update(value=str(sensor.gt10um)) # - sensor.gt25um - sensor.gt50um - sensor.gt100um))
				self._v25.Update(value=str(sensor.gt25um)) # - sensor.gt50um - sensor.gt100um))
				self._v50.Update(value=str(sensor.gt50um)) # - sensor.gt100um))
				self._v100.Update(value=str(sensor.gt100um))
				self._pm10.Update(value=str(sensor.pm10))
				self._pm25.Update(value=str(sensor.pm25))
				self._pm100.Update(value=str(sensor.pm100))

				if sensor.pm25 <= sensor.EPA_PM25_GOOD:
					self._pm25.Update(text_color='green')
				elif sensor.pm25 <= sensor.EPA_PM25_MODERATE:
					self._pm25.Update(text_color='yellow')
				elif sensor.pm25 <= sensor.EPA_PM25_UNHEALTHY:
					self._pm25.Update(text_color='orange')
				else:
					self._pm25.Update(text_color='red')

				if sensor.pm10 <= sensor.EPA_PM10_24HR_MODERATE:
					self._pm10.Update(text_color='green')
				else:
					self._pm10.Update(text_color='red')

				if self._addDataPoint(sensor.gt03um):
					self._drawPlot()

		return True
		

