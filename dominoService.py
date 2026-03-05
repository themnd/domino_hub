from __future__ import annotations

import logging
import serial
import time
import threading

_LOGGER = logging.getLogger(__name__)

_exchange_lock = threading.Lock() 

def readMessage(ser):
  #maxWait = 20
  #timeToSleep = 0.5
  #maxWait = 40
  #timeToSleep = 0.25
  maxWait = 100
  wait = maxWait
  timeToSleep = 0.1
  bytesToRead = ser.inWaiting()
  #print ('bytesToRead: ' + str(bytesToRead))
  while (bytesToRead == 0):
    time.sleep(timeToSleep)
    bytesToRead = ser.inWaiting()
    #print ('bytesToRead: ' + str(bytesToRead))
    wait -= 1
    if (wait == 0):
      raise Exception("timeout")
  if (bytesToRead > 0):
    #_LOGGER.info("Reading " + str(bytesToRead) + " bytes from serial after waiting " + str((maxWait - wait) * timeToSleep) + " seconds")
    return ser.read(bytesToRead)
  else:
    return None

def calcMessage(values):
  c = 0
  b = bytearray()
  #print(b)
  for v in values:
    c += v
    b.append(v)
  c = c & 0xFF
  c = 0xFF - c
  b.append(c)
  return bytes(b)

def dumpMessage(msg):
  s = ''
  for c in msg:
    #s += hex(ord(c)) + ' '
    if (isinstance(c, int)):
      s += hex(c) + ' '
    else:
      s += hex(ord(c)) + ' '
  #print (s)

def sendReqStatus(modNumber, func, d1 = 0x33, d2 = 0x33):
  values = [
    0x55,
    0x82,
    func,
    modNumber,
    d1,
    d2
  ]
  s = calcMessage(values)
  return s

def sendMessage(ser, msg):
    #print( "writing " + str(len(msg)))
    dumpMessage(msg)
    return ser.write(msg)

def exchangeMsg(ser, msg):
    with _exchange_lock:
      sendMessage(ser, msg)

      ans = readMessage(ser)
      #if (ord(ans[2]) == 0x0 and ord(ans[5]) == 0xf0):
      if (ans[2] == 0x0 and ans[5] == 0xf0):
        return None
      if (ans[2] == 0x0 and ans[5] == 0xff):
        return None
      dumpMessage(ans)
      return ans

def getMsgData(ans):
  return ans[4], ans[5]

def evaluteMsgAsLong(ans):
  (d1, d2) = getMsgData(ans)
  return (d1 << 8) + d2

class DominoService:
  def __init__(self, com_port, com_baud):
    self.com_port = com_port
    self.com_baud = com_baud
    self.ser = None
    self.openCount = 0
    _LOGGER.info(f"DominoService initialized with com_port: {com_port}, com_baud: {com_baud}")
  
  def open(self):
    if (self.ser is None):
      self.ser = serial.Serial(self.com_port, baudrate = self.com_baud,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
            rtscts=False,
            dsrdtr=False,
            xonxoff=False,
            timeout=5)
    self.openCount += 1
    _LOGGER.debug(f"DominoService open called. openCount: {self.openCount}")
    return self.ser

  def close(self):
    if (self.ser is not None):
      self.openCount -= 1
      _LOGGER.debug(f"DominoService close called. openCount: {self.openCount}")
      if (self.openCount == 0):
        self.ser.close()
        self.ser = None
        _LOGGER.debug("DominoService serial connection closed.")

class RoomTemperature:
  def __init__(self, mod):
    self.mod = mod
    self.lastStatus = None
    self.lastStatusTime = 0
    self.cacheTime = 60
  
  def status(self, svc: DominoService):
    statusTime = int(round(time.time()))
    if ((self.lastStatus is None) or ((statusTime - self.lastStatusTime) > self.cacheTime)):
      ser = svc.open()
      try:
        self.lastStatus = self.readStatus(ser)
        self.lastStatusTime = statusTime
      finally:
        svc.close()
    return self.lastStatus
  
  def readStatus(self, ser):
    #d1 = exchangeMsg(ser, sendReqStatus(self.mod, 0x30))
    d2 = exchangeMsg(ser, sendReqStatus(self.mod + 1, 0x30))
    kelvin = evaluteMsgAsLong(d2)
    #print (kelvin)
    return RoomTemperature.Status(kelvin)

  class Status:
    def __init__(self, kelvin):
      self.kelvinValue = kelvin
    
    def getKelvin(self):
      return round(self.kelvinValue / 10, 2)
    
    def getCelsius(self):
      return round(self.getKelvin() - 273.15, 2)
    
    def __str__(self):
      return "RoomTemperature.Status: " + str(self.getCelsius()) + "°C / " + str(self.getKelvin()) + "K"

class Meteo:
  def __init__(self, mod, num = None):
    self.mod = mod
    self.num = num
    self.lastStatus = None
    self.lastStatusTime = 0
    self.cacheTime = 60
  
  def status(self, svc: DominoService):
    statusTime = int(round(time.time()))
    if ((self.lastStatus is None) or ((statusTime - self.lastStatusTime) > self.cacheTime)):
      ser = svc.open()
      try:
        self.lastStatus = self.readStatus(ser)
        self.lastStatusTime = statusTime
      finally:
        svc.close()
    return self.lastStatus
  
  def readStatus(self, ser):
    # contains temperature in kelvin (x 10)
    d1 = exchangeMsg(ser, sendReqStatus(self.mod, 0x30))
    kelvin = evaluteMsgAsLong(d1)
    # contains lux in decine di lux (so you have to divide by 10)
    d2 = exchangeMsg(ser, sendReqStatus(self.mod + 1, 0x30))
    lux = evaluteMsgAsLong(d2)
    # contains wind in decimi di m/s (so you have to multiple by 10 for m/s)
    d3 = exchangeMsg(ser, sendReqStatus(self.mod + 2, 0x30))
    wind = evaluteMsgAsLong(d3)
    #b1, b2 = getMsgData(d3)
    #_LOGGER.info(f"Meteo1 b1: {hex(b1)}, b2: {hex(b2)}, wind: {wind}")
    d4 = exchangeMsg(ser, sendReqStatus(self.mod + 3, 0x30))
    b1, b2 = getMsgData(d4)
    isRain = (b2 & 0x01) != 0
    isTwilight = (b2 & 0x02) != 0
    tempOver = (b2 & 0x04) != 0
    luxOver = (b2 & 0x08) != 0
    windOver = (b2 & 0x10) != 0
    lightS = (b2 & 0x20) != 0
    lightW = (b2 & 0x40) != 0
    lightE = (b2 & 0x80) != 0
    badSensor = (b1 & 0x40) != 0
    _LOGGER.debug(f"Meteo2 b1: {hex(b1)}, b2: {hex(b2)}, isRain: {isRain}, isTwilight: {isTwilight}, tempOver: {tempOver}, luxOver: {luxOver}, windOver: {windOver}, lightS: {lightS}, lightW: {lightW}, lightE: {lightE}, badSensor: {badSensor}")
    if (windOver or badSensor):
      # skip this value since it's likely an error in the sensor, but only if we already have some valid wind measurements
      wind = 0
    if (badSensor):
      _LOGGER.warning(f"Meteo2 b1: {hex(b1)}, b2: {hex(b2)}, isRain: {isRain}, isTwilight: {isTwilight}, tempOver: {tempOver}, luxOver: {luxOver}, windOver: {windOver}, lightS: {lightS}, lightW: {lightW}, lightE: {lightE}, badSensor: {badSensor}")
    return Meteo.MeteoStatus(kelvin, lux, wind, isRain, isTwilight)

  class MeteoStatus:
    def __init__(self, kelvin, lux, wind, isRaining, isTwilight):
      self.kelvinValue = kelvin
      self.luxValue = lux
      self.windValue = wind
      self.isRaining = isRaining
      self.isTwilight = isTwilight
    
    def getKelvin(self):
      return round(self.kelvinValue / 10, 2)
    
    def getCelsius(self):
      return round(self.getKelvin() - 273.15, 2)

    def getLux(self):
      return round(self.luxValue * 10, 2)

    def getWind(self):
      return round(self.windValue / 10, 2)
    
    def getIsRaining(self):
      return self.isRaining
    
    def getIsTwilight(self):
      return self.isTwilight

    def __str__(self):
      return "MeteoStatus: " + str(self.getCelsius()) + "°C / " + str(self.getKelvin()) + "K" + " / " + str(self.getLux()) + " lux" + " / " + str(self.getWind()) + " m/s" + " / " + ("raining" if self.isRaining else "not raining") + " / " + ("twilight" if self.isTwilight else "day")  

class Dimmer:
  def __init__(self, mod, num = None):
    self.mod = mod
    self.num = num

  def status(self, svc: DominoService):
    ser = svc.open()
    try:
      return self.readStatus(ser)
    finally:
      svc.close()

  def readStatus(self, ser):
    d1 = exchangeMsg(ser, sendReqStatus(self.mod, 0x31))
    b1, b2 = getMsgData(d1)
    return b2 if b1 == 0 else 0

  def setLight(self, svc: DominoService, pct):
    ser = svc.open()
    try:
      return self._setLight(ser, pct)
    finally:
      svc.close()

  def _setLight(self, ser, pct):
    pct = min(max(0, pct), 100)
    return exchangeMsg(ser, sendReqStatus(self.mod, 0x10, d1 = 0, d2 = pct))

class LightContainer:
  def __init__(self, mod):
    self.mod = mod
    self.lastStatus = None
    self.lastStatusTime = 0
    self.cacheTime = 60

  def status(self, svc: DominoService):
    statusTime = int(round(time.time()))
    if ((self.lastStatus is None) or ((statusTime - self.lastStatusTime) > self.cacheTime)):
      ser = svc.open()
      try:
        self.lastStatus = self.readStatus(ser)
        self.lastStatusTime = statusTime
      finally:
        svc.close()
    return self.lastStatus

  def readStatus(self, ser):
    d1 = exchangeMsg(ser, sendReqStatus(self.mod, 0x31))
    b1, b2 = getMsgData(d1)
    return b2

  def setLight(self, svc: DominoService, num, pct):
    ser = svc.open()
    try:
      if (pct == 0):
        return self.off(ser, num)
      else:
        return self.on(ser, num)
    finally:
      svc.close()
      self.lastStatus = None

  def on(self, ser, num):
    #print ("num: " + str(num))
    bit = 1 << (num - 1)
    #print (hex(bit))
    b2 = (bit << 4) | bit
    #print (hex(b2))
    exchangeMsg(ser, sendReqStatus(self.mod, 0x10, 0, b2))

  def off(self, ser, num):
    #print ("num: " + str(num))
    bit = 1 << (num - 1)
    #print (hex(bit))
    b2 = (bit << 4)
    #print (hex(b2))
    exchangeMsg(ser, sendReqStatus(self.mod, 0x10, 0, b2))

class Light:
  def __init__(self, container:LightContainer, num):
    self.container = container
    self.num = num

  @property
  def mod(self):
      return self.container.mod
    
  def status(self, svc: DominoService):
    status = self.container.status(svc)
    bit = 1 << (self.num - 1)
    #print (hex(bit))
    isOn = (status & bit) != 0
    return isOn

  def setLight(self, svc: DominoService, pct):
    self.container.setLight(svc, self.num, pct)

class Light2:
  def __init__(self, mod, num):
    self.mod = mod
    self.num = num

  def status(self, svc: DominoService):
    ser = svc.open()
    try:
      return self.readStatus(ser)
    finally:
      svc.close()

  def readStatus(self, ser):
    d1 = exchangeMsg(ser, sendReqStatus(self.mod, 0x31))
    b1, b2 = getMsgData(d1)
    bit = 1 << (self.num - 1)
    #print (hex(bit))
    isOn = (b2 & bit) != 0
    return isOn

  def setLight(self, svc: DominoService, pct):
    ser = svc.open()
    try:
      if (pct == 0):
        return self.off(ser)
      else:
        return self.on(ser)
    finally:
      svc.close()

  def on(self, ser):
    #print ("num: " + str(self.num))
    bit = 1 << (self.num - 1)
    #print (hex(bit))
    b2 = (bit << 4) | bit
    #print (hex(b2))
    exchangeMsg(ser, sendReqStatus(self.mod, 0x10, 0, b2))

  def off(self, ser):
    #print ("num: " + str(self.num))
    bit = 1 << (self.num - 1)
    #print (hex(bit))
    b2 = (bit << 4)
    #print (hex(b2))
    exchangeMsg(ser, sendReqStatus(self.mod, 0x10, 0, b2))


class MotorContainer:
  def __init__(self, mod):
    self.mod = mod
    self.lastStatus = None
    self.lastStatusTime = 0
    self.cacheTime = 10

  def status(self, svc: DominoService):
    statusTime = int(round(time.time()))
    if ((self.lastStatus is None) or ((statusTime - self.lastStatusTime) > self.cacheTime)):
      ser = svc.open()
      try:
        self.lastStatus = self.readStatus(ser)
        self.lastStatusTime = statusTime
      finally:
        svc.close()
    return self.lastStatus

  def readStatus(self, ser) -> MotorContainer.MotorStatus:
    d = exchangeMsg(ser, sendReqStatus(self.mod, 0x31))
    b1, b2 = getMsgData(d)
    _LOGGER.debug(f"Motor {self.mod} -> b1: {hex(b1)}, b2: {hex(b2)}")
    
    m1o = (b2 & 0x01) != 0
    m1c = (b2 & 0x02) != 0
    m2o = (b2 & 0x04) != 0
    m2c = (b2 & 0x08) != 0

    m1stopped = not m1o and not m1c
    m2stopped = not m2o and not m2c

    if (m1stopped):
      m1s = MotorContainer.MotorStatus.MotorMovement.STOPPED
    elif (m1o):
      m1s = MotorContainer.MotorStatus.MotorMovement.OPENING
    elif (m1c):
      m1s = MotorContainer.MotorStatus.MotorMovement.CLOSING
    else:
      m1s = None
    
    if (m2stopped):
      m2s = MotorContainer.MotorStatus.MotorMovement.STOPPED
    elif (m2o):
      m2s = MotorContainer.MotorStatus.MotorMovement.OPENING
    elif (m2c):
      m2s = MotorContainer.MotorStatus.MotorMovement.CLOSING
    else:
      m2s = None

    return MotorContainer.MotorStatus(m1s, m2s)
    
    # d1 = exchangeMsg(ser, sendReqStatus(self.mod + 1, 0x30))
    # b1, b2 = getMsgData(d1)
    # if (self.mod == 17 and num == 2):
    #   _LOGGER.info(f"Motor3 {self.mod + 1} - {num} -> b1: {hex(b1)}, b2: {hex(b2)}")
    # d1 = exchangeMsg(ser, sendReqStatus(self.mod + 1, 0x31))
    # b1, b2 = getMsgData(d1)
    # if (self.mod == 17 and num == 2):
    #   _LOGGER.info(f"Motor4 {self.mod + 1} - {num} -> b1: {hex(b1)}, b2: {hex(b2)}")
    return b2

  def setPosition(self, svc: DominoService, num, pct):
    ser = svc.open()
    try:
      return self._setPosition(ser, num, pct)
    finally:
      svc.close()

  def _setPosition(self, ser, num, pct):
    d1 = 0x01 if num == 1 else 0x02
    pct = min(max(0, pct), 100)
    d2 = int(pct * 55 / 100)
    _LOGGER.info(f"setPosition on {self.mod}, num: {num}, pct: {pct}, d2: {d2}, d2hex: {hex(d2)}")
    return exchangeMsg(ser, sendReqStatus(self.mod, 0x10, d1 = d1, d2 = d2))

  def doOpen(self, svc: DominoService, num):
    ser = svc.open()
    try:
      return self._doOpen(ser, num)
    finally:
      svc.close()

  def _doOpen(self, ser, num):
    d1 = 0x01 if num == 1 else 0x04
    d2 = 0x01 if num == 1 else 0x04
    _LOGGER.info(f"doOpen on {self.mod}, num: {num}, d1: {hex(d1)}, d2: {hex(d2)}")
    return exchangeMsg(ser, sendReqStatus(self.mod, 0x10, d1 = d1, d2 = d2))

  def doClose(self, svc: DominoService, num):
    ser = svc.open()
    try:
      return self._doClose(ser, num)
    finally:
      svc.close()

  def _doClose(self, ser, num):
    d1 = 0x01 if num == 1 else 0x08
    d2 = 0x02 if num == 2 else 0x08
    _LOGGER.info(f"doClose on {self.mod}, num: {num}, d1: {hex(d1)}, d2: {hex(d2)}")
    return exchangeMsg(ser, sendReqStatus(self.mod, 0x10, d1 = d1, d2 = d2))

  def doStop(self, svc: DominoService, num):
    ser = svc.open()
    try:
      return self._doStop(ser, num)
    finally:
      svc.close()
  
  def _doStop(self, ser, num):
    d1 = 0x03 if num == 1 else 0x0C
    d2 = 0
    _LOGGER.info(f"doStop on {self.mod}, num: {num}, d1: {hex(d1)}, d2: {hex(d2)}")
    return exchangeMsg(ser, sendReqStatus(self.mod, 0x10, d1 = d1, d2 = d2))

  class MotorStatus:

    class MotorMovement:
      OPENING = 1
      CLOSING = 2
      STOPPED = 3
    
    def __init__(self, motor1: MotorMovement, motor2: MotorMovement):
      self.motor1 = motor1
      self.motor2 = motor2

    def getMotor1(self) -> MotorMovement:
      return self.motor1

    def getMotor2(self) -> MotorMovement:
      return self.motor2

    def __str__(self):
      return "MotorStatus: motor 1 " + str(self.getMotor1()) + " motor 2 " + str(self.getMotor2())

class Motor:
  def __init__(self, motor:MotorContainer, num):
    self.motor = motor
    self.num = num
  
  @property
  def mod(self):
      return self.motor.mod
  
  def status(self, svc: DominoService):
    status = self.motor.status(svc)
    return status.getMotor1() if self.num == 1 else status.getMotor2()
  
  def setPosition(self, svc: DominoService, pct):
    self.motor.setPosition(svc, self.num, pct)
  
  def doOpen(self, svc: DominoService):
    self.motor.doOpen(svc, self.num)
  
  def doClose(self, svc: DominoService):
    self.motor.doClose(svc, self.num)
  
  def doStop(self, svc: DominoService):
    self.motor.doStop(svc, self.num)
