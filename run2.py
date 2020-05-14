import can
import time
import math
import numpy as np

# bus1_filters = []

# bus1_filters.append({"can_id": int()})

# bus1 = can.interface.Bus('can1', bustype='socketcan_native')

FRONT_LEFT_DOOR_BIT = 0x80
FRONT_RIGHT_DOOR_BIT = 0x40
BACK_LEFT_DOOR_BIT = 0x20
BACK_RIGHT_DOOR_BIT = 0x10
BACK_TRUNK_BIT = 0x08

NEUTRAL_STOPPED_GEAR_BIT = 0x00
NEUTRAL_MOVING_GEAR_BIT = 0x01
REVERSE_GEAR_BIT = 0xE1
FIRST_GEAR_BIT = 0x11
SECOND_GEAR_BIT = 0x20
THIRD_GEAR_BIT = 0x30
FOURTH_GEAR_BIT = 0x40
FIFTH_GEAR_BIT = 0x50

def main ():
  bus0 = can.interface.Bus(channel='can0', bustype='socketcan_native')
  bus1 = can.interface.Bus(channel='can1', bustype='socketcan_native')
  manager = DataManager()
  listener = MyListener(manager)
  listener2 = MyListener2(manager)
  lcd_manager = LCDManager(bus0)
  ac_lcd_manager = ACLCDManager(bus0, manager)

  notifier = can.Notifier(bus0, [listener])
  notifier2 = can.Notifier(bus1, [listener2])

  counter = 0

  try:
    while True:
      lcd_manager.message = manager.getMessage()

      lcd_manager.show()
      ac_lcd_manager.show()
      time.sleep(0.1)
  except KeyboardInterrupt:
    bus0.shutdown()
    notifier.stop()
    notifier2.stop()


def transformNum (b):
  return (b[0] << 8) + b[1]

def convertKMpLtoMPG (val):
  return float(val) * 2.35214583

def convertKMpHtoMPH (val):
  return float(val) * 0.621371

def twos_comp(val, bits):
  if (val & (1 << (bits - 1))) != 0:
    val = val - (1 << bits)
  return val

def clamp(mn, mx, x):
  return max(min(x, mx), mn)


class MyListener (can.Listener):
  def __init__ (self, manager):
    self.manager = manager

  def on_message_received (self, msg):
    if msg.arbitration_id == 0x201:
      self.manager.setVehicleSpeed(msg.data[4:6])
    if msg.arbitration_id == 0x433:
      self.manager.doorByte = msg.data[0]
    elif msg.arbitration_id == 0x265:
      self.manager.blinkerByte = msg.data[0]
    elif msg.arbitration_id == 0x400:
      self.manager.setInstantConsumption(msg.data[2:4])
      self.manager.setAverageConsumption(msg.data[4:6])


class MyListener2 (can.Listener):
  def __init__ (self, manager):
    self.manager = manager

  def on_message_received (self, msg):
    if msg.arbitration_id == 0x201:
      self.manager.setVehicleSpeed(msg.data[4:6])
    elif msg.arbitration_id == 0x231:
      self.manager.gearByte = msg.data[0]
    # elif msg.arbitration_id == 0x433:
    #   self.manager.doorByte = msg.data[0]
    # elif msg.arbitration_id == 0x400:
    #   self.manager.setInstantConsumption(msg.data[2:4])
    #   self.manager.setAverageConsumption(msg.data[4:6])


class DataManager:

  def __init__ (self):
    self.doorByte = 0x00
    self.gearByte = 0x00
    self.blinkerByte = 0x00
    self.vehicleSpeed = 0.0
    self.instantConsumption = 0.0
    self.averageConsumption = 0.0

  def setDoorByte (self, b):
    self.doorByte = b

  def setGearByte (self, b):
    self.gearByte = b

  def setBlinkerData (self, data):
    self.blinkerData = data

  def setVehicleSpeed (self, data):
    self.vehicleSpeed = convertKMpHtoMPH(transformNum(data)/100)

  def setInstantConsumption (self, data):
    d = transformNum(data)
    if d == 0xFFFE:
      d = 0.0

    self.instantConsumption = convertKMpLtoMPG(d/100)

  def setAverageConsumption (self, data):
    self.averageConsumption = convertKMpLtoMPG(transformNum(data)/100)

  def isDoorOpen (self):
    return self.doorByte is not 0x00

  def isBlinkerOn (self):
    return self.blinkerByte is not 0x80 and self.blinkerByte is not 0x00

  def getBlinkerChar (self):
    if self.isBlinkerOn() is not True:
      return " "

    if self.blinkerByte == 0xC0:
      return ">"
    elif self.blinkerByte == 0xA0:
      return "<"
    else:
      return "?"

  def getGear (self):
    if self.gearByte == NEUTRAL_STOPPED_GEAR_BIT or self.gearByte == NEUTRAL_MOVING_GEAR_BIT:
      return "N"
    elif self.gearByte == REVERSE_GEAR_BIT:
      return "R"
    elif self.gearByte == FIRST_GEAR_BIT:
      return "1"
    elif self.gearByte == SECOND_GEAR_BIT:
      return "2"
    elif self.gearByte == THIRD_GEAR_BIT:
      return "3"
    elif self.gearByte == FOURTH_GEAR_BIT:
      return "4"
    elif self.gearByte == FIFTH_GEAR_BUT:
      return "5"
    else:
      return "?"


  def getMessage (self):
    if self.isDoorOpen():
      if self.doorByte & FRONT_LEFT_DOOR_BIT:
        return "FL Door Open"
      elif self.doorByte & BACK_LEFT_DOOR_BIT:
        return "BL Door Open"
      elif self.doorByte & BACK_RIGHT_DOOR_BIT:
        return "BR Door Open"
      elif self.doorByte & BACK_TRUNK_BIT:
        return "Trunk Open"
      elif self.doorByte & FRONT_RIGHT_DOOR_BIT:
        return "FR Door Open"
      else:
        return "Mystery Door"
    else:
      return self.getBlinkerChar()

class LCDManager:

  def __init__ (self, bus):
    self.bus = bus

    # First Byte
    self.flag_af = False
    self.flag_rdm = False
    self.flag_rpt = False
    self.flag_dolby = False
    self.flag_st = False
    self.flag_md_in = False
    self.flag_cd_in = False

    self.byte1 = [True, self.flag_cd_in, self.flag_md_in, self.flag_st, self.flag_dolby, self.flag_rpt, self.flag_rdm, self.flag_af]

    # Second Byte
    self.flag_auto_m = False
    self.flag_tp = False
    self.flag_ta = False
    self.flag_pty = False

    self.byte2 = [self.flag_pty, self.flag_ta, self.flag_tp, self.flag_auto_m, False, False, False, False]

    # Third Byte
    self.byte3 = [False, False, False, False, False, False, False, False]

    # Fourth Byte
    self.flag_dot_1 = False
    self.flag_dot_2 = False
    self.flag_apos_1 = False
    self.flag_colon_1 = False

    self.byte4 = [False, False, self.flag_colon_1, self.flag_apos_1, False, self.flag_dot_2, self.flag_dot_1, True]

    # Fifth Byte
    self.flag_info_btn = False
    self.flag_clock_btn = False

    self.byte5 = [False, False, True, self.flag_clock_btn, self.flag_info_btn, False, False, False]

    # Sixth Byte
    self.byte6 = [False, False, False, False, False, False, False, False]

    # Seventh Byte
    self.byte7 = [False, False, False, False, False, False, False, False]

    # Eighth Byte
    self.byte8 = [False, False, False, False, False, False, False, False]

    # Total Array
    self.byte_array = [self.byte1, self.byte2, self.byte3, self.byte4, self.byte5, self.byte6, self.byte7, self.byte8]

    self.message = ""

  def getFirstFive (self):
    a = [0xC0] + list(bytearray(self.message[0:5], 'utf8'))
    a += [0x20] * (8 - len(a))
    return a

  def getLastSeven (self):
    a = [0x85] + list(bytearray(self.message[5:12], 'utf8'))
    a += [0x20] * (8 - len(a))
    return a

  def show (self):
    data = list(np.packbits(np.uint8(self.byte_array)))
    msg = can.Message(arbitration_id=0x28F, data=data, extended_id=False)
    self.bus.send(msg)

    data = self.getFirstFive()
    msg = can.Message(arbitration_id=0x290, data=data, extended_id=False)
    self.bus.send(msg)

    data = self.getLastSeven()
    msg = can.Message(arbitration_id=0x291, data=data, extended_id=False)
    self.bus.send(msg)

class ACLCDManager:
  def __init__ (self, bus, manager):
    self.bus = bus
    self.manager = manager

    self.display_on_flag = True
    self.fresh_air_flag = False
    self.reycle_air_flag = False
    self.auto_flag = False
    self.eco_flag = False
    self.ac_eco_flag = False
    self.symbols_flag = False

    self.byte2 = [False, False, False, False, False, False, False, False]

    self.right_decimal_flag = True
    self.airflow_windshield_flag = False
    self.person_flag = False
    self.airflow_face_flag = False

    self.byte3 = [self.right_decimal_flag, False, False, False, False, self.airflow_windshield_flag, self.person_flag, self.airflow_face_flag]

    self.airflow_feet_flag = False
    self.dual_flag = False

    self.byte5 = [False, False, False, False, False, False, False, False]

    self.left_decimal_flag = True

    self.byte6 = [self.left_decimal_flag, False, False, False, False, False, False, False]

    self.byte7 = [False, False, False, False, False, False, False, False]
    self.byte8 = [False, False, False, False, False, False, False, False]


  def genByteArray (self):

    self.byte1 = [self.display_on_flag, self.fresh_air_flag, self.reycle_air_flag, self.auto_flag, self.eco_flag, self.ac_eco_flag, self.symbols_flag, self.symbols_flag]
    self.byte4 = [self.airflow_feet_flag, False, False, False, False, False, self.dual_flag, False]
    self.byte_array = [self.byte1, self.byte2, self.byte3, self.byte4, self.byte5, self.byte6, self.byte7, self.byte8]

    return self.byte_array

  def show (self):

    # print(self.manager.instantConsumption/100)
    frac, whole = math.modf(clamp(0.0, 99.9, self.manager.vehicleSpeed))
    whole = int(whole)
    top = int(whole / 10)
    bottom = int(whole % 10)
    self.byte5[0:4] = [int(x) for x in np.binary_repr(top, width=4)]
    self.byte5[4:8] = [int(x) for x in np.binary_repr(bottom, width=4)]
    frac = int(frac * 10)
    self.byte6[1:5] = [int(x) for x in np.binary_repr(frac, width=4)][0:5]

    frac, whole = math.modf(clamp(0.0, 99.9, self.manager.instantConsumption))
    whole = int(whole)
    top = int(whole / 10)
    bottom = int(whole % 10)
    self.byte2[0:4] = [int(x) for x in np.binary_repr(top, width=4)]
    self.byte2[4:8] = [int(x) for x in np.binary_repr(bottom, width=4)]
    frac = int(frac * 10)
    self.byte3[1:5] = [int(x) for x in np.binary_repr(frac, width=4)][0:5]

    data = self.genByteArray()
    # print(repr(data))

    data = list(np.packbits(np.uint8(data)))
    msg = can.Message(arbitration_id=0x2a0, data=data, extended_id=False)
    self.bus.send(msg)

if __name__ == '__main__':
  main()

