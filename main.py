# -*- coding: utf-8 -*-
__author__ = 'LiYuanhe'

from machine import Pin, Signal
import time
import socket
import machine
import network
import micropython
from lib_AHT10 import AHT10
from lib_lcd1602_2004_with_i2c import LCD
import utime
from machine import Pin, SoftI2C
from lib_SCD40 import SCD4X
from lib_SGP30 import SGP30
from lib_SHT20 import SHT2x
import os
from lib_main import *

micropython.alloc_emergency_exception_buf(100)

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


# Connect Five AHT10 chip to ESP32, without pull-up resister, using internal pull up resister
# AHT10-A: SCL 19 SDA 22
# AHT10-B: SCL 18 SDA 23
# AHT10-C: SCL 16 SDA 17
# AHT10-D: SCL 2 SDA 4
# AHT10-E: SCL 32 SDA 33

# Attach any SCD40 to any one of the AHT10 I2C channel (G-G, V-V, SCL-SCL, SDA-SDA)

# Connect a Fed Pushbutton between 35 and 3V3, pull down 35 with 2k resister
# Connect a Water Pushbutton between 13 and 3V3, pull down 13 with 2k resister


lcd_scl_pin = 26
lcd_sda_pin = 27

fed_pushbutton_pin = 35
fed_pushbutton = Pin(fed_pushbutton_pin, Pin.IN)

water_pushbutton_pin = 13
water_pushbutton = Pin(water_pushbutton_pin, Pin.IN)

### Fed time process ###

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
    global lcd, fed_pushbutton, feed_times_file
    # 长按才有效
    for _ in range(10):
        print(fed_pushbutton.value())
        time.sleep(0.02)
        if fed_pushbutton.value() == 0:
            return False
    # print('======================= New feed time:',get_current_time())
    with open(feed_times_file, 'a') as feed_times_file_object:
        feed_times_file_object.write(str(get_current_time()) + '\n')
    # pushbutton = Pin(fed_pushbutton_pin, Pin.IN, pull=Pin.PULL_UP)
    # pushbutton.irq(button_pressed,trigger=Pin.IRQ_FALLING)
    lcd.puts("        Feed        ")
    lcd.puts("      Received      ", 1)
    lcd.puts("                    ", 2)
    lcd.puts("      Rebooting     ", 3)
    time.sleep(1.5)
    # while True:
    #     print("Water")
    #     time.sleep_ms(100)
    #     if time.time()-start_showing_time>3:
    machine.reset()



### Water time process ###

last_water_time_read = 0
water_times_file = "water_time_file.txt"
water_times = open(water_times_file).read()
water_times = water_times.splitlines()
if not water_times:
    water_time = 0
else:
    water_time = int(water_times[-1])


def read_time_since_water():  # in seconds
    global last_water_time_read, water_time, water_times_file
    if time.time() - last_water_time_read > 60:  # 读这个很耗时，60秒读一次
        current_water_times = open(water_times_file).read()
        current_water_times = current_water_times.splitlines()
        if not current_water_times:
            water_time = 0
        else:
            water_time = int(current_water_times[-1])

    ret = get_current_time() - water_time
    if ret < 0:
        print("Water record error! Water record error! Water record error! Water record error! Water record error! ")
        with open(water_times_file, 'a') as water_times_file_object:
            water_times_file_object.write(str(time.time()) + '\n')
        ret = 0
    return ret


def water_button_pressed():
    print("water_button_pressed Function")
    global lcd, water_pushbutton, water_times_file
    # 长按才有效
    for _ in range(10):
        print(water_pushbutton.value())
        time.sleep(0.02)
        if water_pushbutton.value() == 0:
            return False
    with open(water_times_file, 'a') as water_times_file_object:
        water_times_file_object.write(str(get_current_time()) + '\n')

    # start_showing_time = time.time()

    lcd.puts("       Water        ")
    lcd.puts("      Changed       ", 1)
    lcd.puts("                    ", 2)
    lcd.puts("     Rebooting      ", 3)
    time.sleep(1.5)
    # while True:
    #     print("Water")
    #     time.sleep_ms(100)
    #     if time.time()-start_showing_time>3:
    machine.reset()


def read_t_and_h(i2c_object):
    """
    Assume there is SHT20 or AHT10 attached on that i2c line, and do measurement on both
    :param i2c_object:
    :param ts:
    :param hs:
    :return:
    if there is both SHT20 and AHT10, return ((SHT20-T, SHT20-H),(AHT10-T, AHT10-H))
    if there not both present, fill with -1, e.g. ((-1,-1),(AHT10-T, AHT10-H))
    """

    AHT10_ADDR = 0x38
    SHT20_ADDR = 0b1000000

    devices = i2c_object.scan()
    ret = [[-1,-1],[-1,-1]]

    if SHT20_ADDR in devices:
        try:
            sht20 = SHT2x(i2c_object)
            t,h = sht20.measure()
            if h > 99:
                h = 99
            if t < 0:
                t = -1
            ret[0] = [t,h]
        except Exception as e:
            print("SHT20", e)
    if AHT10_ADDR in devices:
        try:
            aht10 = AHT10(i2c_object)
            t,h = aht10.measure()
            if h > 99:
                h = 99
            if t < 0:
                t = -1
            ret[1] = [t,h]
        except Exception as e:
            print("AHT10", e)
    return ret


def find_SGP30_object(i2c_object_list):
    """
    Among a list of i2c_list, find which one has the SGP30 attached to
    :param i2c_object_list:
    :return:
    """

    for i2c in i2c_object_list:
        devices = i2c.scan()
        if 0x58 in devices:
            return SGP30(i2c)

def find_SCD40_object(i2c_object_list):
    """
    Among a list of i2c_list, find which one has the SCD40 attached to
    :param i2c_object_list:
    :return:
    """

    for i2c in i2c_object_list:
        devices = i2c.scan()
        if 0x62 in devices:
            ret =SCD4X(i2c)
            ret.start_periodic_measurement()
            return ret


######################################

lcd = LCD(SoftI2C(scl=Pin(lcd_scl_pin), sda=Pin(lcd_sda_pin), freq=100000))
lcd.puts("                    ", )
lcd.puts("     Voldemort      ", 1)
lcd.puts("    Life Support    ", 2)

from lib_main import custom_bar_chars

for count,i in enumerate(custom_bar_chars):
    lcd.create_charactor(count,i)

# i2c-A: SCL 19 SDA 22
# i2c-B: SCL 18 SDA 23
# i2c-C: SCL 16 SDA 17
# i2c-D: SCL 2 SDA 4
# i2c-E: SCL 32 SDA 33

#每一个i2c上连一个AHT10或者SHT20，如果存在，SHT20排在AHT10前面

i2c_A = SoftI2C(scl=Pin(19, pull=Pin.PULL_UP), sda=Pin(22, pull=Pin.PULL_UP), freq=100000)
utime.sleep(0.05)
i2c_B = SoftI2C(scl=Pin(18, pull=Pin.PULL_UP), sda=Pin(23, pull=Pin.PULL_UP), freq=100000)
utime.sleep(0.05)
i2c_C = SoftI2C(scl=Pin(16, pull=Pin.PULL_UP), sda=Pin(17, pull=Pin.PULL_UP), freq=100000)
utime.sleep(0.05)
i2c_D = SoftI2C(scl=Pin(2, pull=Pin.PULL_UP), sda=Pin(4, pull=Pin.PULL_UP), freq=100000)
utime.sleep(0.05)
i2c_E = SoftI2C(scl=Pin(32, pull=Pin.PULL_UP), sda=Pin(33, pull=Pin.PULL_UP), freq=100000)
utime.sleep(0.05)
# Create the sensor object using I2C

i2c_list = [i2c_A, i2c_B, i2c_C, i2c_D, i2c_E]
SCD40_object = find_SCD40_object(i2c_list)
SGP30_object = find_SGP30_object(i2c_list)

cycle_count = 0
cycle_time = 0.1  # refresh rate
last_write_time = 0
last_LCD_refresh = 0
last_tick = 0
last_reset_time = get_machine_reset_time()


def main():
    write_current_time()

    AHT10_t_lists = [[] for _ in range(5)]
    AHT10_h_lists = [[] for _ in range(5)]
    SHT20_t_lists = [[] for _ in range(5)]
    SHT20_h_lists = [[] for _ in range(5)]

    global cycle_time, cycle_count, fed_pushbutton, water_pushbutton, lcd
    global last_write_time, last_LCD_refresh, last_tick, last_reset_time
    global i2c_list, SCD40_object, SGP30_object

    CO2, VOC = '-----', '-----' # CO2和VOC更新太快，每两个周期更新一次
    # fed_pushbutton.irq(button_pressed,trigger=Pin.IRQ_FALLING)

    while True:
        if fed_pushbutton.value() == 1:
            feed_button_pressed()
            lcd = LCD(SoftI2C(scl=Pin(lcd_scl_pin), sda=Pin(lcd_sda_pin), freq=100000))

        if water_pushbutton.value() == 1:
            water_button_pressed()
            lcd = LCD(SoftI2C(scl=Pin(lcd_scl_pin), sda=Pin(lcd_sda_pin), freq=100000))

        cycle_count += 1

        # 30秒备份一次时间，因为备份时间耗时几百毫秒，不能太频繁
        if time.time() - last_write_time > 30:
            write_current_time()
            last_write_time = time.time()

        # 防止屏幕数据不全，600秒重置一次屏幕
        if time.time() != last_LCD_refresh and time.time() % 600 == 1:
            print("Screen reset")
            last_LCD_refresh = time.time()
            lcd = LCD(SoftI2C(scl=Pin(lcd_scl_pin), sda=Pin(lcd_sda_pin), freq=100000))


        for count,i2c_object in enumerate(i2c_list):
            SHT20_t_h, AHT10_t_h =  read_t_and_h(i2c_object)
            SHT20_t,SHT20_h = SHT20_t_h
            AHT10_t,AHT10_h = AHT10_t_h
            SHT20_t_lists[count].append(SHT20_t)
            SHT20_h_lists[count].append(SHT20_h)
            AHT10_t_lists[count].append(AHT10_t)
            AHT10_h_lists[count].append(AHT10_h)
            # 保留5个最后结果，如果短暂中断不影响显示
            SHT20_t_lists[count] = SHT20_t_lists[count][-5:]
            SHT20_h_lists[count] = SHT20_h_lists[count][-5:]
            AHT10_t_lists[count] = AHT10_t_lists[count][-5:]
            AHT10_h_lists[count] = AHT10_h_lists[count][-5:]


        # 从SGP30 读取VOC，因为SGP30的CO2质量很差，不要它的CO2
        if cycle_count % 2 == 0:
            if not SGP30_object:
                SGP30_object = find_SGP30_object(i2c_list)
            try:
                CO2_dump, VOC = SGP30_object.indoor_air_quality
                print("VOC:",CO2_dump, VOC)
            except Exception as e:
                print("\n\n\n", e, "\n\n\n")
                SGP30_object = find_SGP30_object(i2c_list)
                try:
                    CO2_dump, VOC = SGP30_object.indoor_air_quality
                except Exception as e:
                    print("\n\n\n", e, "\n\n\n")
                    CO2_dump, VOC = -1, -1

            if VOC == -1:
                VOC = '-----'
            else:
                VOC = str(int(VOC)) + " " * (5 - len(str(int(VOC))))

            if cycle_count<24: #前15秒没有信号
                VOC = "init "


        if cycle_count % 2 == 0:
            if not SCD40_object:
                SCD40_object = find_SCD40_object(i2c_list)
            try:
                CO2, CO2_Temp, CO2_Humid = SCD40_object.measure()
                print("CO2:",CO2, CO2_Temp, CO2_Humid)
            except Exception as e:
                print("\n\n\n", e, "\n\n\n")
                SCD40_object = find_SCD40_object(i2c_list)
                try:
                    CO2, CO2_Temp, CO2_Humid = SCD40_object.measure()
                except Exception as e:
                    print("\n\n\n", e, "\n\n\n")
                    CO2, CO2_Temp, CO2_Humid = -1, -1, -1

            if CO2 == -1:
                CO2 = '-----'
            elif CO2 <= 400:
                CO2 = 'low  '
            else:
                CO2 = str(int(CO2)) + " " * (5 - len(str(int(CO2))))

            # CO2_Temp = str(int(CO2_Temp))
            # CO2_Humid = str(int(CO2_Humid)) if CO2_Humid<100 else "99"
            # CO2_Temp = CO2_Temp + " " * (5 - len(CO2_Temp))
            # CO2_Humid = CO2_Humid + " " * (5 - len(CO2_Humid))
            #
            # if CO2_Temp=="-1":
            #     CO2_Temp='--'
            # if CO2_Humid=="-1":
            #     CO2_Humid='--'

            # Cor = CO2_Temp+" "+CO2_Humid

            # if cycle_count<24: #前15秒没有信号
            #     CO2 = "init "
            #     Cor = "init "

        # print(2, time.ticks_ms())

        SHT20_t_results = [interpret_list(x) for x in SHT20_t_lists]
        SHT20_h_results = [interpret_list(x) for x in SHT20_h_lists]
        AHT10_t_results = [interpret_list(x) for x in AHT10_t_lists]
        AHT10_h_results = [interpret_list(x) for x in AHT10_h_lists]

        print("SHT20_t",SHT20_t_results)
        print("SHT20_h",SHT20_h_results)
        print("AHT10_t",AHT10_t_results)
        print("AHT10_h",AHT10_h_results)

        # 一共最多10个结果[SHT1,AHT1,SHT2,AHT2...]，选其中五个显示
        ret_t = [-1,-1,-1,-1,-1]
        ret_h = [-1,-1,-1,-1,-1]
        ret_marker = [False,False,False,False,False] # 用于记录该结果是不是SHT20带来的，如果是，为True

        # 如果结果中的某位置有至少一个结果，填进去
        for i in range(5):
            if SHT20_t_results[i]!=-1:
                ret_marker[i]=True
                ret_t[i] = SHT20_t_results[i]
                ret_h[i] = SHT20_h_results[i]
                SHT20_t_results[i] = -1
                SHT20_h_results[i] = -1
                ret_marker[i] = True
            elif AHT10_t_results[i]!=-1:
                ret_t[i] = AHT10_t_results[i]
                ret_h[i] = AHT10_h_results[i]
                AHT10_t_results[i] = -1
                AHT10_h_results[i] = -1
        # 如果没有，看看两边有没有多的给匀一匀，优先找前面的，此时SHT20的结果必然被用光，只可能是AHT10的结果
        for i in range(5):
            if ret_t[i]==-1:
                if i>0 and AHT10_t_results[i-1]!=-1:
                    ret_t[i] = AHT10_t_results[i-1]
                    ret_h[i] = AHT10_h_results[i-1]
                    AHT10_t_results[i-1] = -1
                    AHT10_h_results[i-1] = -1
                elif i<4 and AHT10_t_results[i+1]!=-1:
                    ret_t[i] = AHT10_t_results[i+1]
                    ret_h[i] = AHT10_h_results[i+1]
                    AHT10_t_results[i+1] = -1
                    AHT10_h_results[i+1] = -1

        # print(3, time.ticks_ms())
        t1, t2, t3, t4, t5 = ret_t
        h1, h2, h3, h4, h5 = ret_h
        line1 = "%i %i %i %i %i %s%s%s%s%s" % (t1, t2, t3, t4, t5, t_to_bar(t1), t_to_bar(t2), t_to_bar(t3), t_to_bar(t4), t_to_bar(t5))
        line1 = line1.replace('-1', '--')
        line2 = "%i %i %i %i %i %s%s%s%s%s" % (h1, h2, h3, h4, h5, h_to_bar(h1), h_to_bar(h2), h_to_bar(h3), h_to_bar(h4), h_to_bar(h5))
        line2 = line2.replace('-1', '--')

        line1 = list(line1)
        line2 = list(line2)
        #如果当前位置是SHT20测得，后面加个点
        for count,i in enumerate(ret_marker):
            if i:
                line1[2+count*3]="."
                line2[2+count*3]="."
        line1 = "".join(line1)
        line2 = "".join(line2)

        if cycle_count % 2 == 0:
            line3 = "CO2 %s. VOC %s" % (CO2, VOC)
        else:
            line3 = "CO2 %s  VOC %s" % (CO2, VOC)

        time_since_feed = read_time_since_feed()
        time_since_water = read_time_since_water()


        fed_text = show_time(time_since_feed, prefix="Fed")
        if len(fed_text)==9 and "Fed " not in fed_text:
            fed_text = fed_text.replace('Fed',"Fed ")
        else:
            fed_text += " "

        if cycle_count % 2 == 0 and time_since_water>86400*3: # 换水超过3天时闪烁警示
            line4 = fed_text + " " + show_time(time_since_water, prefix="H2O", flash=True)
        else:
            line4 = fed_text + " " + show_time(time_since_water, prefix="H2O")


        line4 = line4 + " " * (20 - len(line4)) if len(line4) < 20 else line4

        # print(4, time.ticks_ms())

        # 如果有气温传感器超出绝对安全范围（18~32.5），给出发光警告
        temp_list = [x for x in [t1, t2, t3, t4, t5] if x != -1]
        if temp_list and cycle_count % 2 == 0 and (max(temp_list) > 32.5 or min(temp_list) < 18):
            line1 = chr(7) * 20
            line2 = chr(7) * 20
            line3 = chr(7) * 20
            line4 = chr(7) * 20

        lcd.puts(line1)
        lcd.puts(line2, 1)
        lcd.puts(line3, 2)
        lcd.puts(line4, 3)

        #print(5, time.ticks_ms())

        # automatic reboot
        if time.time() < last_reset_time:
            last_reset_time = 0
        if time.time() - last_reset_time > 2*3600:
            # print(time.time(),last)
            save_machine_reset_time()
            machine.reset()


main()
