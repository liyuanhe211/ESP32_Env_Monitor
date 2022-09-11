# -*- coding: utf-8 -*-
__author__ = 'LiYuanhe'

from machine import Pin, Signal
import time
import socket
import machine
import network
import micropython
import os

micropython.alloc_emergency_exception_buf(100)


def output_signal(pin_number, invert=False):
    return Signal(Pin(pin_number, Pin.OUT), invert=invert)


def input_pin(pin_number):
    return Signal(Pin(pin_number, Pin.IN))


def disable_irq(pin_object):
    pin_object.irq(trigger=0)


def isfile(filename):
    # only filename in the root folder
    return filename in os.listdir('.')


def read_int_file(filename, default=0):
    ret = default
    if isfile(filename):
        content = open(filename).read()
        if content.strip():
            try:
                int(content)
                ret = int(content)
            except Exception as e:
                print(e)
    return ret


def save_int_as_file(filename, int):
    with open(filename, 'w') as output_file:
        output_file.write(str(int))


# a time keeping method
# one file keeps current time in seconds after this boot, which will be written every cycle
# the second file keeps cumulative time before this boot

def write_current_time():
    # print("write_current_time")
    after_boot_time_file = "after_boot_time.txt"
    before_boot_cum_time_file = "before_boot_cum_time_file.txt"

    after_boot_time = read_int_file(after_boot_time_file)
    before_boot_cum_time = read_int_file(before_boot_cum_time_file)

    current_time = time.time()
    save_int_as_file(after_boot_time_file, current_time)

    # print("Stored after boot time:",after_boot_time)
    # print("Stored before boot cum time:",before_boot_cum_time)
    # print("Current boot time:", current_time)

    if current_time < after_boot_time:
        new_before_boot_cum_time = before_boot_cum_time + after_boot_time
        # print("New before boot cum time:",new_before_boot_cum_time)
        save_int_as_file(before_boot_cum_time_file, new_before_boot_cum_time)


def get_current_time():
    before_boot_cum_time_file = "before_boot_cum_time_file.txt"
    before_boot_cum_time = read_int_file(before_boot_cum_time_file)

    return before_boot_cum_time + time.time()


last_feed_time_read = 0
feed_times_file = "feed_time_file.txt"
feed_times = open(feed_times_file).read()
feed_times = feed_times.splitlines()
if not feed_times:
    feed_time = 0
else:
    feed_time = int(feed_times[-1])


def read_time_since_feed():  # in seconds
    global last_feed_time_read, feed_time, feed_times_file
    if time.time() - last_feed_time_read > 60:  # 读这个很耗时，60秒读一次
        current_feed_times = open(feed_times_file).read()
        current_feed_times = current_feed_times.splitlines()
        if not current_feed_times:
            feed_time = 0
        else:
            feed_time = int(current_feed_times[-1])

    ret = get_current_time() - feed_time
    if ret < 0:
        print("Feed record error! Feed record error! Feed record error! Feed record error! Feed record error! ")
        with open(feed_times_file, 'a') as feed_times_file_object:
            feed_times_file_object.write(str(time.time()) + '\n')
        ret = 0
    # print("Last Feed Record:",get_current_time()-feed_time,get_current_time(),feed_time)
    return ret


def feed_button_pressed():
    print("feed_button_pressed Function")
    global lcd, pushbutton, feed_times_file
    # 长按才有效
    for _ in range(10):
        print(pushbutton.value())
        time.sleep(0.02)
        if pushbutton.value() == 0:
            return False
    # print('======================= New feed time:',get_current_time())
    with open(feed_times_file, 'a') as feed_times_file_object:
        feed_times_file_object.write(str(get_current_time()) + '\n')
    # pushbutton = Pin(pushbutton_pin, Pin.IN, pull=Pin.PULL_UP)
    # pushbutton.irq(button_pressed,trigger=Pin.IRQ_FALLING)
    lcd.puts("                    ", 0, 0)
    lcd.puts("        Feed        ", 0, 1)
    lcd.puts("      Received      ", 0, 2)
    lcd.puts("                    ", 0, 3)
    machine.reset()


def interpret_list(input_list):
    # read a list of numbers, if all of them are -1, return -1, if there are non -1 terms, read the last non -1 term
    ret = -1
    for i in input_list:
        if i != -1:
            ret = i
    return ret


def save_machine_reset_time():
    save_int_as_file('machine_reset_time.txt', time.time())


def get_machine_reset_time():
    return read_int_file('machine_reset_time.txt', 0)


#
# def show_time(time_sec):
#
#     # if <99s show number
#     # if <60m show minutes in xmx to show x.x minutes
#     # if <24h show minutes in xhx to show x.x hour
#     # if >1d show minutes in xdx to show x.x day
#
#     if time_sec<=99:
#         ret = str(time_sec)
#     elif time_sec<60*60:
#         ret =str(int(time_sec/60))+"m"
#     elif time_sec<36000:
#         ret = "%1.1f" % (time_sec/3600,)+'h'
#     elif time_sec<86400:
#         ret = str(int(time_sec/3600))+"h"
#     else:
#         ret = "%1.1f" % (time_sec/86400,)+'d'
#     ret = " "*(4-len(ret))+ret
#     # print(len(ret)-3)
#     return ret

# def show_time(time_sec):
#     # if <99s show number
#     # if <60m show minutes in xmx to show x.x minutes
#     # if <24h show minutes in xhx to show x.x hour
#     # if >1d show minutes in xdx to show x.x day
#
#     sec = str(time_sec%60)
#     min = str(int((time_sec/60)%60))
#     hour = str(int((time_sec/3600)%24))
#     day = int(time_sec/86400)
#
#     if len(sec)==1:
#         sec = "0" + sec
#     if len(min)==1:
#         min = "0" + min
#     if len(hour)==1:
#         hour = "0" + hour
#
#     # ret = "Fed %s d %s:%s:%s" % (day,hour,min,sec)
#     if day:
#         ret = "Fed %s d %s:%s:%s" % (day,hour,min,sec)
#     else:
#         ret = "Fed today %s:%s:%s" % (hour,min,sec)
#
#     length = len(ret)
#     if len(ret)%2==0:
#         pad_left = int((20-length)/2)
#     else:
#         pad_left = int((21-length)/2)
#     pad_right = 20-pad_left-length
#
#     print(length,pad_left,pad_right)
#
#     ret = (" "*pad_left) + ret+ (" "*pad_right)
#     return ret


def show_time(time_sec):
    # if <99s show number
    # if <60m show minutes in xmx to show x.x minutes
    # if <24h show minutes in xhx to show x.x hour
    # if >1d show minutes in xdx to show x.x day

    sec = str(time_sec % 60)
    min = str(int((time_sec / 60) % 60))
    hour = str(int((time_sec / 3600) % 24))
    day = str(int(time_sec / 86400))

    if time_sec <= 60:
        ret = sec + 's'
    elif time_sec < 60 * 60:
        ret = min + 'm'
    elif time_sec < 86400:
        ret = hour + 'h'
    else:
        ret = day + "d" + hour + 'h'
    if len(ret) < 6:
        ret = "Fed " + ret
    else:
        ret = "Fed" + ret
    if len(ret) < 9:
        ret = " " * (9 - len(ret)) + ret
    return ret


# print(1,show_time(2),1)
# print(1,show_time(15),1)
# print(1,show_time(89),1)
# print(1,show_time(189),1)
# print(1,show_time(1189),1)
# print(1,show_time(11189),1)
# print(1,show_time(111189),1)
# print(1,show_time(1111189),1)


def read_t_and_h(AHT_i2c_object, ts, hs):
    # print(4,time.ticks_ms()-last_tick)
    # last_tick = time.ticks_ms()
    # print(1)
    try:
        AHT10_A = AHT10(AHT_i2c_object)
        t = AHT10_A.temperature
        h = AHT10_A.relative_humidity
        if h > 99:
            h = 99
        if t < 0:
            t = -1
        # print("A",t1,h1)
    except Exception as e:
        print(4, e)
        t = -1
        h = -1
    ts.append(t)
    hs.append(h)
    ts = ts[-10:]
    hs = hs[-10:]
    return ts, hs


# A standard thermometer and humidity monitor with screen
# Connection for ESP32

# Connect a [Parallel to I2C Chip] to a LCD2004 screen
# Just solder all pins sequentially to the screen, Direction: (pin towards [GND, VCC, SDA, SCL] pin connects to the VSS pin of the Screen

# Connect [Parallel to I2C Chip] to ESP8266
# GND - GND
# VCC - VIN
# SCL - 26
# SDA - 27
# Also
# SDA - 10K resister - GND
# SCL - 10K resister - GND


# Connect Three AHT10 chip to ESP32, without pull-up resister, using internal pull up resister
# AHT10-A: SCL 19 SDA 22
# AHT10-B: SCL 18 SDA 23
# AHT10-C: SCL 16 SDA 17
# AHT10-D: SCL 2 SDA 4
# AHT10-E: SCL 32 SDA 33


# Connect a Pushbutton between 35 and 3V3, pull down 35 with 2k resister


scl_pin = 26
sda_pin = 27

from lib_AHT10 import AHT10
from lib_lcd1602_2004_with_i2c import LCD
import utime
from machine import Pin, SoftI2C

lcd = LCD(SoftI2C(scl=Pin(scl_pin), sda=Pin(sda_pin), freq=100000))
lcd.puts("                    ", )
lcd.puts("     Voldemort      ", 1)
lcd.puts("    Life Support    ", 2)

custom_char_0 = [
    0b00000,
    0b00000,
    0b00000,
    0b00000,
    0b00000,
    0b00000,
    0b00000,
    0b11111]

custom_char_1 = [
    0b00000,
    0b00000,
    0b00000,
    0b00000,
    0b00000,
    0b00000,
    0b11111,
    0b11111]

custom_char_2 = [
    0b00000,
    0b00000,
    0b00000,
    0b00000,
    0b00000,
    0b11111,
    0b11111,
    0b11111]

custom_char_3 = [
    0b00000,
    0b00000,
    0b00000,
    0b00000,
    0b11111,
    0b11111,
    0b11111,
    0b11111]

custom_char_4 = [
    0b00000,
    0b00000,
    0b00000,
    0b11111,
    0b11111,
    0b11111,
    0b11111,
    0b11111]

custom_char_5 = [
    0b00000,
    0b00000,
    0b11111,
    0b11111,
    0b11111,
    0b11111,
    0b11111,
    0b11111]

custom_char_6 = [
    0b00000,
    0b11111,
    0b11111,
    0b11111,
    0b11111,
    0b11111,
    0b11111,
    0b11111]

custom_char_7 = [
    0b11111,
    0b11111,
    0b11111,
    0b11111,
    0b11111,
    0b11111,
    0b11111,
    0b11111]

lcd.create_charactor(0, custom_char_0)
lcd.create_charactor(1, custom_char_1)
lcd.create_charactor(2, custom_char_2)
lcd.create_charactor(3, custom_char_3)
lcd.create_charactor(4, custom_char_4)
lcd.create_charactor(5, custom_char_5)
lcd.create_charactor(6, custom_char_6)
lcd.create_charactor(7, custom_char_7)

# AHT10-A: SCL 19 SDA 22
# AHT10-B: SCL 18 SDA 23
# AHT10-C: SCL 16 SDA 17
# AHT10-D: SCL 2 SDA 4
# AHT10-E: SCL 32 SDA 33

AHT10_A_i2c = SoftI2C(scl=Pin(19, pull=Pin.PULL_UP), sda=Pin(22, pull=Pin.PULL_UP), freq=100000)
utime.sleep(0.05)
AHT10_B_i2c = SoftI2C(scl=Pin(18, pull=Pin.PULL_UP), sda=Pin(23, pull=Pin.PULL_UP), freq=100000)
utime.sleep(0.05)
AHT10_C_i2c = SoftI2C(scl=Pin(16, pull=Pin.PULL_UP), sda=Pin(17, pull=Pin.PULL_UP), freq=100000)
utime.sleep(0.05)
AHT10_D_i2c = SoftI2C(scl=Pin(2, pull=Pin.PULL_UP), sda=Pin(4, pull=Pin.PULL_UP), freq=100000)
utime.sleep(0.05)
AHT10_E_i2c = SoftI2C(scl=Pin(32, pull=Pin.PULL_UP), sda=Pin(33, pull=Pin.PULL_UP), freq=100000)
utime.sleep(0.05)
# Create the sensor object using I2C

# Connect a Pushbutton between 25 and ground, Internal pull up 25

pushbutton_pin = 35
pushbutton = Pin(pushbutton_pin, Pin.IN)

cycle_count = 0
cycle_time = 0.1  # refresh rate
last_write_time = 0
last_LCD_refresh = 0
last_tick = 0
last_reset_time = get_machine_reset_time()


def main():
    write_current_time()

    t1s = []
    h1s = []
    t2s = []
    h2s = []
    t3s = []
    h3s = []
    t4s = []
    h4s = []
    t5s = []
    h5s = []

    global cycle_time, cycle_count, pushbutton, lcd, last_write_time, last_LCD_refresh, last_tick, last_reset_time
    global AHT10_A_i2c, AHT10_B_i2c, AHT10_C_i2c, AHT10_D_i2c, AHT10_E_i2c
    # pushbutton.irq(button_pressed,trigger=Pin.IRQ_FALLING)

    while True:
        if pushbutton.value() == 1:
            feed_button_pressed()
            lcd = LCD(SoftI2C(scl=Pin(scl_pin), sda=Pin(sda_pin), freq=100000))
        print(pushbutton.value())
        cycle_count += 1

        # 30秒备份一次时间，因为备份时间耗时几百毫秒，不能太频繁
        if time.time() - last_write_time > 30:
            write_current_time()
            last_write_time = time.time()

        # 防止屏幕数据不全，300秒重置一次屏幕
        if time.time() != last_LCD_refresh and time.time() % 300 == 1:
            print("Screen reset")
            last_LCD_refresh = time.time()
            lcd = LCD(SoftI2C(scl=Pin(scl_pin), sda=Pin(sda_pin), freq=100000))

        # print(1, time.ticks_ms())

        # read_t_h 消耗0.7s
        t1s, h1s = read_t_and_h(AHT10_A_i2c, t1s, h1s)
        t2s, h2s = read_t_and_h(AHT10_B_i2c, t2s, h2s)
        t3s, h3s = read_t_and_h(AHT10_C_i2c, t3s, h3s)
        t4s, h4s = read_t_and_h(AHT10_D_i2c, t4s, h4s)
        t5s, h5s = read_t_and_h(AHT10_E_i2c, t5s, h5s)

        # print(2, time.ticks_ms())

        t1 = interpret_list(t1s)
        t2 = interpret_list(t2s)
        t3 = interpret_list(t3s)
        t4 = interpret_list(t4s)
        t5 = interpret_list(t5s)
        h1 = interpret_list(h1s)
        h2 = interpret_list(h2s)
        h3 = interpret_list(h3s)
        h4 = interpret_list(h4s)
        h5 = interpret_list(h5s)

        def h_to_bar(humidity):
            if humidity == -1:
                return " "
            ret = int(humidity / (100 / 8))
            if ret > 7:
                ret = 7
            if ret < 0:
                ret = 0
            return chr(ret)

        def t_to_bar(temp):
            if temp == -1:
                return " "
            ret = int((temp - 20) / (10 / 8))
            if ret > 7:
                ret = 7
            if ret < 0:
                ret = 0
            return chr(ret)

        # print(3, time.ticks_ms())

        line1 = "%2.1f    %2.1f    %2.1f" % (t1, t3, t5)
        line1 = line1.replace('-1.0', '--- ')
        line2 = "    %2.1f    %2.1f  " % (t2, t4)
        line2 = line2.replace('-1.0', '--- ')
        # line3 = "17"+chr(0)+"18"+chr(1)+"18"+chr(2)+"18"+chr(3)+"18"+chr(4)+"18"+chr(5)
        line3 = "%2.0f  %2.0f  %2.0f  %2.0f  %2.0f %%" % (h1, h2, h3, h4, h5)
        line3 = line3.replace('-1%', '---')
        # line4 = "                "
        # line4 = line4.replace('-1%','---')

        if cycle_count % 2 == 0:
            line2 += chr(223) + 'C'
        else:
            line2 += " C"
        time_since_feed = read_time_since_feed()
        line4 = "%s%s%s%s%s %s%s%s%s%s%s" % (t_to_bar(t1),
                                             t_to_bar(t2),
                                             t_to_bar(t3),
                                             t_to_bar(t4),
                                             t_to_bar(t5),
                                             h_to_bar(h1),
                                             h_to_bar(h2),
                                             h_to_bar(h3),
                                             h_to_bar(h4),
                                             h_to_bar(h5),
                                             show_time(time_since_feed))

        print(4, time.ticks_ms())

        # 如果有气温传感器超出绝对安全范围（18~32.5），给出发光警告
        if cycle_count % 2 == 0 and (max(t1, t2, t3, t4, t5) > 32.5 or min(t1, t2, t3, t4, t5) < 18):
            line1 = chr(7) * 20
            line2 = chr(7) * 20
            line3 = chr(7) * 20
            line4 = chr(7) * 20

        # puts 消耗0.2s
        lcd.puts(line1)
        lcd.puts(line2, 1)
        lcd.puts(line3, 2)
        lcd.puts(line4, 3)

        print(5, time.ticks_ms())

        # automatic reboot
        if time.time() < last_reset_time:
            last_reset_time = 0
        if time.time() - last_reset_time > 30 * 60:
            # print(time.time(),last)
            save_machine_reset_time()
            machine.reset()


main()
