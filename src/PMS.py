# Copyright 2022 Mikhail Stolpner
# Licensed under Apache 2.0 License https://www.apache.org/licenses/LICENSE-2.0

#!/usr/bin/env python3

import time
import datetime
import random


# This class encapsulates PMS functionality and AQI limits
# Documentation on PMS sensor can be found here https://github.com/ZIOCC/Zio-Qwiic-PM2.5-Air-Quality-Sensor-Adapter-Board/blob/master/PMSA003%20series%20data%20manua_English_V2.6.pdf

class PMS:

  # AQI standard limits
  EPA_PM25_GOOD =                          12.0 
  EPA_PM25_MODERATE =                      35.4 
  EPA_PM25_UNHEALTHY_FOR_SENSITIVE_GROUP = 55.4
  EPA_PM25_UNHEALTHY =                     150.4
  EPA_PM25_VERY_UNHEALTHY =                250.4
  EPA_PM25_HAZARDOUS =                     500

  EPA_PM10_24HR_MODERATE =                 150 

  CAN_PM25_ANNUAL_GREEN =                  4.0 # less than 4
  CAN_PM25_ANNUAL_YELLOW =                 6.4 # 4-6.4
  CAN_PM25_ANNUAL_ORANGE =                 8.8 # 6.5-8.8
  #CAN_PM25_ANNUAL_RED =                        # Over 8.8

  CAN_PM25_24HR_GREEN =                  10.0  
  CAN_PM25_24HR_YELLOW =                 19.0  
  CAN_PM25_24HR_ORANGE =                 27.0  
  #CAN_PM25_24HR_RED =                    

  # PMS Configuratopm
  _port = None          # Port
  _rstPin = None        # Reset pin
  _setPin = None        # Set pin
  _mode = "streaming"   # Default mode is streaming
  
  # Operational variables
  _status = None
  _buffer = b''
  _simulate = False
  _gpio = None

  # PMS Data
  apm10 = None
  apm25 = None
  apm100 = None
  pm10 = None
  pm25 = None
  pm100 = None
  gt03um = None
  gt05um = None
  gt10um = None
  gt25um = None
  gt50um = None
  gt100um = None

  # Initialization code. When simulate is set to True, PMS sensor is not required. 
  def __init__(self, portname, rstPin, setPin, simulate = False):
    if simulate:
      self._simulate = simulate
      return
    
    import RPi.GPIO as GPIO
    import serial

    self._rstPin = rstPin
    self._setPin = setPin
    # Init GPIO
    self._gpio = GPIO
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(self._rstPin, GPIO.OUT)
    GPIO.setup(self._setPin, GPIO.OUT)
    # Reset sensor
    GPIO.output(self._rstPin, GPIO.LOW) 
    GPIO.output(self._rstPin, GPIO.HIGH) 
    # Not sleep
    GPIO.output(self._setPin, GPIO.LOW) 
    GPIO.output(self._setPin, GPIO.HIGH)
    # Init port
    self._port = serial.Serial(portname, baudrate=9600, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS, timeout=10)

  # Release hardware
  def release(self):
    if self._simulate:
      return    
    self.sleep()
    self._gpio.cleanup()

  # Set PMS sensor to sleep. Helpful to prolongue its life.
  def sleep(self):
    if self._simulate:
      return    
    self._port.write(b'\x42\x4D\xE4\x00\x00\x01\x73')

  # Wake up sensor hardware
  def wakeup(self):
    if self._simulate:
      return    
    # Operating mode. Stable data should should start coming at least 30 seconds after the sensor wakeup from the sleep mode because of the fan's performance.
    self._port.write(b'\x42\x4D\xE4\x00\x01\x01\x74')

  # Sets streaming mode. Refer to PMS documentatiom.
  def setStreamingMode(self):
    if self._simulate:
      return    
    # Default mode after power up. In this mode sensor would send serial data to the host automatically.
    self._port.write(b'\x42\x4D\xE1\x00\x01\x01\x71')
    self._mode = 'streaming'

  # Sets On-Demand mode. Refer to PMS documentatiom.
  def setOnDemandMode(self):
    if self._simulate:
      return    
    # In this mode sensor would send serial data to the host upon request.
    self._port.write(b'\x42\x4D\xE1\x00\x00\x01\x70')
    self._mode = 'on-demand'

  # Request new data. Refer to PMS documentatiom.
  def requestData(self):
    if self._simulate:
      return    
    if self._mode == 'on-demand':
      # Request read in Passive Mode.
      self._port.write(b'\x42\x4D\xE2\x00\x00\x01\x71')
    else:
      raise Exception("PMS does not allows to request data on demand in Active/Streaming mode.")

  # Receive PMS transmission in any mode
  def recievePmsTransmission(self, timeout=10000, debug=False):
    if self._simulate:
      # Produce random data
      maxpm = 50
      maxgt = 3000
      self.apm10 = random.randint(0, maxpm)
      self.apm25 = random.randint(0, maxpm)
      self.apm100 = random.randint(0, maxpm)
      self.pm10 = random.randint(0, maxpm)
      self.pm25 = random.randint(0, maxpm)
      self.pm100 = random.randint(0, maxpm)
      self.gt03um = random.randint(0, maxgt)
      self.gt05um = random.randint(0, maxgt)
      self.gt10um = random.randint(0, maxgt)
      self.gt25um = random.randint(0, maxgt)
      self.gt50um = random.randint(0, maxgt)
      self.gt100um = random.randint(0, maxgt)
      if(debug):
        self._printDebug()
      return True 

    # Start timeout timer
    start_time = round(time.time()*1000)
    self._buffer = b''

    # Read until start markers to sync with the input stream
    while True:
      ch1 = self._port.read()
      if ch1 == b'\x42':
        ch2 = self._port.read()
        if ch2 == b'\x4D':
          break
      # Check for exceeding timeout
      if round(time.time()*1000) - start_time >= timeout:
        return False

    # We are in sync. Read frame length
    ch3 = self._port.read()
    framelen = ord(ch3) << 8;
    ch4 = self._port.read()
    framelen |= ord(ch4);
    if framelen != 2 * 13 + 2:
      # Unsupported sensor, unexpected frame length, transmission error e.t.c.
      return False;

    # Read the rest of the data
    self._buffer = self._port.read(26)

    # Verify Checksum
    calculatedChecksum = ord(ch1) + ord(ch2) + ord(ch3) + ord(ch4)
    for i in range(0, len(self._buffer)-1):
      calculatedChecksum += self._buffer[i]
    cs1 = self._port.read()
    cs2 = self._port.read()
    csum = ord(cs1) << 8
    csum |= ord(cs2)

    if (csum != calculatedChecksum):
      return False

    # process received Data
    self.apm10 = self._buffer[0] * 256 + self._buffer[1]
    self.apm25 = self._buffer[2] * 256 + self._buffer[3]
    self.apm100 = self._buffer[4] * 256 + self._buffer[5]
    self.pm10 = self._buffer[6] * 256 + self._buffer[7]
    self.pm25 = self._buffer[8] * 256 + self._buffer[9]
    self.pm100 = self._buffer[10] * 256 + self._buffer[11]
    self.gt03um = self._buffer[12] * 256 + self._buffer[13]
    self.gt05um = self._buffer[14] * 256 + self._buffer[15]
    self.gt10um = self._buffer[16] * 256 + self._buffer[17]
    self.gt25um = self._buffer[18] * 256 + self._buffer[19]
    self.gt50um = self._buffer[20] * 256 + self._buffer[21]
    self.gt100um = self._buffer[22] * 256 + self._buffer[23]

    if(debug):
      self._printDebug()

    return True

  def _printDebug(self):
    print('===============\n'
            'PM1.0(CF=1): {}\n'
            'PM2.5(CF=1): {}\n'
            'PM10 (CF=1): {}\n'
            'PM1.0 (STD): {}\n'
            'PM2.5 (STD): {}\n'
            'PM10  (STD): {}\n'
            '>0.3um     : {}\n'
            '>0.5um     : {}\n'
            '>1.0um     : {}\n'
            '>2.5um     : {}\n'
            '>5.0um     : {}\n'
            '>10um      : {}'.format(self.apm10, self.apm25, self.apm100,
                                     self.pm10, self.pm25, self.pm100,
                                     self.gt03um, self.gt05um, self.gt10um, self.gt25um, self.gt50um, self.gt100um))


