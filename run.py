import can
import time
import numpy as np

# bus1_filters = []

# bus1_filters.append({"can_id": int()})

# bus1 = can.interface.Bus('can1', bustype='socketcan_native')

FRONT_LEFT_DOOR_BIT = 0x80
FRONT_RIGHT_DOOR_BIT = 0x40
BACK_LEFT_DOOR_BIT = 0x20
BACK_RIGHT_DOOR_BIT = 0x10
BACK_TRUNK_BIT = 0x08

def main ():
  bus0 = can.interface.Bus(channel='can0', bustype='socketcan_ctypes')
  manager = DataManager()
  listener = MyListener(manager)
  lcd_manager = LCDManager(bus0)

  notifier = can.Notifier(bus0, [listener])

  counter = 0

  try:
    while True:
      lcd_manager.message = manager.getMessage()
      #counter += 1
      #if counter == 30:
      #  counter = 0
      lcd_manager.show()
      time.sleep(0.1)
  except KeyboardInterrupt:
    bus0.shutdown()
    notifier.stop()



class MyListener (can.Listener):
  def __init__ (self, manager):
    self.manager = manager

  def on_message_received (self, msg):
    if msg.arbitration_id == 0x433:
      self.manager.doorByte = msg.data[0]


class DataManager:

  def __init__ (self):
    self.doorByte = 0x00
    self.blinkerData = 0x0000

  def setDoorByte (self, b):
    self.doorByte = b

  def setBlinkerData (self, data):
    self.blinkerData = data

  def isDoorOpen (self):
    return self.doorByte is not 0x00

  def isBlinkerOn (self):
    return self.blinkerData is not 0x8000

  def getMessage (self):
    if self.isDoorOpen():
      if self.doorByte & FRONT_LEFT_DOOR_BIT:
        return "FL Door Open"
      elif self.doorByte & FRONT_RIGHT_DOOR_BIT:
        return "FR Door Open"
      elif self.doorByte & BACK_LEFT_DOOR_BIT:
        return "BL Door Open"
      elif self.doorByte & BACK_RIGHT_DOOR_BIT:
        return "BR Door Open"
      elif self.doorByte & BACK_TRUNK_BIT:
        return "Trunk Open"
      else:
        return "Mystery Door"
    else:
      return ""

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
    a = [0xC0] + list(bytearray(self.message[0:5]))
    a += [20] * (8 - len(a))
    return a

  def getLastSeven (self):
    a = [0x85] + list(bytearray(self.message[5:12]))
    a += [0] * (8 - len(a))
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


if __name__ == '__main__':
  main()

