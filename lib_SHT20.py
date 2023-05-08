
# https://github.com/liduor/Micropython--sht2x/blob/main/sht2x.py

# This program is distributed under Apache License Version 2.0
#
# © Albertas Mickenas, 2016
# mic@wemakethings.net
# albertas@technariumas.lt
#

import time

class SHT2x:
    i2c = []
    ADDR = 64

    POLYNOMIAL = 0x131                  # POLYNOMIAL x8 + x5 + x4 +1.

    CMD_READ_TEMPERATURE_hold = 0xE3
    CMD_READ_HUMIDITY_hold    = 0xE5

    CMD_READ_TEMPERATURE = 0xF3
    CMD_READ_HUMIDITY    = 0xF5
    CMD_READ_REGISTER    = 0xE7
    CMD_WRITE_REGISTER   = 0xE6
    CMD_RESET 			 = 0xFE

    def __init__(self, _i2c):
        self.i2c = _i2c

    def CheckCRC(self, buf):
        POLYNOMIAL = 0x131  # POLYNOMIAL x8 + x5 + x4 +1.
        crc = 0
        for i in range(2):
            crc ^= buf[i]
            for bit in range(8):
                if (crc & 0x80):
                    crc = (crc << 1) ^ POLYNOMIAL
                else:
                    crc = (crc << 1)
        return  crc

    def toTemperature(self, buf):
        if buf == False:
            print("CRC Error...\r\n")
            return False
        else:
            return -46.85 + 175.72 * ((buf[0] << 8) + buf[1]) /2**16

    def toHumidity(self, buf):
        if buf == False:
            print("CRC Error...\r\n")
            return False
        else:
            return -6 + 125.0 * ((buf[0] << 8) + buf[1]) / 2**16

    def decodeUserReg(self, buf):
        reg = buf[0]
        ret = []
        if(0b10000001 & reg == 0b10000001):
            ret.append("11bits")
        elif(0b10000001 & reg == 0b10000000):
            ret.append("RH 10bit T 13bit")
        elif(0b10000001 & reg == 0b00000001):
            ret.append("RH 8bit T 12bit")
        elif(0b10000001 & reg == 0b00000000):
            ret.append("RH 12bit T 14bit")

        if(0b01000000 & reg == 0b01000000):
            ret.append("VDD < 2.5")
        else:
            ret.append("VDD > 2.5")

        if(0b00000100 & reg == 0b00000100):
            ret.append("heater ON")
        else:
            ret.append("heater OFF")

        if(0b00000010 & reg == 0b00000010):
            ret.append("OTP reload disabled")
        else:
            ret.append("OTP reload enabled")

        return ret

    def runI2CCommand(self, command, bytesToRead):
        b = bytearray(1)
        b[0] = command

        self.i2c.writeto(self.ADDR, b)

        if(bytesToRead > 0):
            recv = bytearray(bytesToRead)
            retryCounter = 0
            done = False
            while retryCounter < 15 and not done:
                try:
                    self.i2c.readfrom_into(self.ADDR, recv)
                    done = True
                    retryCounter = retryCounter + 1
                except:
                    time.sleep(0.01)
            #print(hex(recv[0])+' '+hex(recv[1])+' '+hex(recv[2]))
            #print("\r\n")
            if (self.CheckCRC(recv) == recv[2]):
                #print('success...\r\n')
                pass
            else:
                #print('Failed...')
                return False
            return recv

    def getTemperature(self):
        return self.toTemperature(self.runI2CCommand(self.CMD_READ_TEMPERATURE, 3))

    def getHumidity(self):
        return self.toHumidity(self.runI2CCommand(self.CMD_READ_HUMIDITY, 3))

    def measure(self):
        return self.getTemperature(),self.getHumidity()

    def getUserRegister(self):
        return self.decodeUserReg(self.runI2CCommand(self.CMD_READ_REGISTER, 1))

    def setUserRegister(self, register):
        b = bytearray(2)
        b[0] = self.CMD_WRITE_REGISTER
        b[1] = register & 0b11000111
        self.i2c.writeto(self.ADDR, b)

    def reset(self):
        self.runI2CCommand(self.CMD_RESET, 0)
