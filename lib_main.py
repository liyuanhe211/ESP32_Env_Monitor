# -*- coding: utf-8 -*-
__author__ = 'LiYuanhe'

from machine import Pin, Signal, RTC
import time
import socket
import machine
import network
import ntptime
import micropython
import os
from collections import OrderedDict

from lib_AHT10 import AHT10
from lib_SCD40 import SCD4X
from lib_SGP30 import SGP30
from lib_SHT20 import SHT2x
from lib_lcd1602_2004_with_i2c import LCD

LOG_FILE = "log.txt"
AFTER_BOOT_TIME_FILE = "after_boot_time.txt"
BEFORE_BOOT_CUM_TIME_FILE = "before_boot_cum_time_file.txt"
rtc = RTC()


def output_signal(pin_number, invert=False):
    return Signal(Pin(pin_number, Pin.OUT), invert=invert)


def input_pin(pin_number):
    return Signal(Pin(pin_number, Pin.IN))


def disable_irq(pin_object):
    pin_object.irq(trigger=0)


def isfile(filename):
    # only filename in the root folder
    return filename in os.listdir('.')


def boot_time_s():
    # 注意在不设置RTC的情况下，这个等于time.time()，但是在设置了RTC之后就不一样了
    return int(time.ticks_ms() / 1000)


def read_times_file(filename):
    """
    Read a file written by save_time_int_and_RTC_to_file
    Return a two-tuple, the first element is the machine clock as an int,
    the second element is the NTP corrected realtime clock, returns tuple like (2023,5,19,4,6,57,44,0) = 2023.5.19 14:57
    :param filename:
    :return: Return a two-tuple, the first element is the machine clock as an int,
    the second element is the NTP corrected realtime clock, returns tuple like (2023,5,19,4,6,57,44,0) = 2023.5.19 14:57
    """
    ret = [0, ()]
    if isfile(filename):
        content = open(filename).readlines()
        content = [x for x in content if x.strip()]
        if not content:
            return ret
        content = content[-1]
        content = content.split("|")
        try:
            ret[0] = int(content[0])
        except Exception as e:
            log("read_times_file Exception 1", e, content)
        if len(content) == 2:
            try:
                ret[1] = eval(content[1])
            except Exception as e:
                log("read_times_file Exception 2", e, content)
    return ret


def center_align(text, width):
    """
    "abcde" --> "       abcde        "
    Args:
        text:
        width:

    Returns:

    """

    front = int((width - len(text)) / 2)
    behind = width - len(text) - front
    if front < 0:
        front = 0
    if behind < 0:
        behind = 0
    return " " * front + text + " " * behind


def connect_wifi(WIFI_SSID, WIFI_PASSWORD, lcd=None, timeout=10, effective_IP_start="192.168."):
    """
    :return: a connected network.WLAN object
    """
    WLAN = network.WLAN(network.STA_IF)
    WLAN.active(True)

    lcd.puts(" Connecting WIFI... ")
    lcd.puts(center_align(WIFI_SSID, 20), 1)
    lcd.puts("                    ", 2)
    lcd.puts("                    ", 3)

    log("Connecting WIFI...")
    WLAN.connect(WIFI_SSID, WIFI_PASSWORD)
    if wait_WIFI_connection(WLAN, timeout, effective_IP_start):
        lcd.puts(" Connection Success ", 2)
        lcd.puts(center_align(WLAN.ifconfig()[0], 20), 3)
    else:
        lcd.puts(" Connection Failed. ", 2)
    return WLAN


def wait_WIFI_connection(wlan, timeout=10, effective_IP_start="192.168."):
    """
    Args:
        wlan: a network.WLAN object
        effective_IP_start:
        timeout:
    """
    wifi_connection_start_time = boot_time_s()
    while not wlan.isconnected():
        if boot_time_s() - wifi_connection_start_time > timeout:
            log("WIFI Connection Failed. wlan.isconnected() is False")
            return False
        pass
    if not wlan.status() == network.STAT_GOT_IP:
        log("WIFI Connection Failed. wlan.status() is ", wlan.status())
        return False
    if not wlan.ifconfig()[0].startswith(effective_IP_start):
        log("WIFI Connection Failed. IPConfig:", wlan.ifconfig())
        return False
    log("WIFI Connected. IPConfig:", wlan.ifconfig())
    return True


def set_RTC_time(lcd):
    before_NTP = rtc.datetime()
    lcd.puts(" Accessing NTP Time ")
    lcd.puts("                    ", 1)
    try:
        ntptime.host = "ntp.aliyun.com"
        ntptime.settime()  # set the RTC's time using ntptime
        # 如果失败会是2000/1/1
        after_NTP = rtc.datetime()
    except Exception as e:
        log("set_RTC_time failure. Error", e)
        lcd.puts("  RTC Time Failure  ", 1)
        return None

    if after_NTP[:-1] != before_NTP[:-1]:
        log("RTC reset by NTP:")
        log("Before NTP setting:", rtc.datetime())
        log("After NTP setting", rtc.datetime())
        log(time_string_from_RTC_time_tuple(rtc.datetime()))
        lcd.puts("    RTC Time Set    ", 0)
        lcd.puts(center_align(time_string_from_RTC_time_tuple(rtc.datetime()), 20), 1)
    else:
        log("NTP time check passed. Time not changed.")  # print the current time from the RTC
        log(time_string_from_RTC_time_tuple(rtc.datetime()))

    time.sleep(1)


def mktime_from_RTC_datetime(rtc_datetime_tuple):
    """
    RTC.datetime() 返回 (2023,5,19,4,6,57,44,0) = 2023.5.19 14:57
    time.mktime(), time.localtime() 使用/返回 (year, month, mday, hour, minute, second, weekday, yearday)
    Returns:

    """
    year, month, day, weekday, h, m, s, I_DONT_KNOW = rtc_datetime_tuple
    return time.mktime((year, month, day, h, m, s, 0, 0))


def RTC_has_been_set():
    """
    RTC设置成功就是2023年多少，RTC设置失败是2000/1/1
    Returns:

    """
    return rtc.datetime()[0] != 2000


def fill_two_digits(number):
    if number < 10:
        return "0" + str(number)
    else:
        return str(number)


def time_string_from_RTC_time_tuple(time_tuple):
    """

    Args:
        time_tuple: (2023,5,19,4,6,57,44,0)
        注意时间是UTC+0时间 = 2023.5.19 14:57

    Returns: 5-19 14:57

    """
    # print("Input time tuple:", time_tuple)
    year, month, day, weekday, h, m, s, I_DONT_KNOW = time_tuple

    if h<16:
        mktime = time.mktime((year, month, day, weekday, h+8, m, s, I_DONT_KNOW))
    else:
        mktime = time.mktime((year, month, day+1, (weekday+1)%7, h-16, m, s, I_DONT_KNOW))

    UTC_8_time_tuple = time.localtime(mktime)
    # print("Time tuple with UTC+8:", UTC_8_time_tuple)
    year, month, day, weekday, h, m, s, _ = UTC_8_time_tuple
    ret = fill_two_digits(month) + "-" + \
          fill_two_digits(day) + " " + \
          fill_two_digits(h) + ":" + \
          fill_two_digits(m)
    return ret


def log(*objects):
    # keep 50 kB
    print("LOG:", *objects)
    if not isfile(LOG_FILE):
        with open(LOG_FILE, "w") as log_file_object:
            log_file_object.write("")

    cap_file_size(LOG_FILE, 50)
    if RTC_has_been_set():
        log_time = str(get_current_time()) + " | " + time_string_from_RTC_time_tuple(rtc.datetime()) + '  |  '
    else:
        log_time = str(get_current_time()) + '  |  '
    with open(LOG_FILE, 'a') as log_file_object:
        log_file_object.write(log_time + " ".join(str(x) for x in objects).strip("\n") + '\n')


def get_file_size(filepath):
    """
    If file exist, return file size in bytes
    If not, return -1
    Returns:

    """

    try:
        open(filepath)
    except OSError:
        return -1
    return os.stat(filepath)[6]


def cap_file_size(file, filesize_kB):
    """
    for a log file with lines, if the filesize is larger than filesize_kB,
    truncate the file so the first 200 lines are deleted.
    :return:
    """
    # os.stat(file)[6]
    file_size_kB = get_file_size(file) / 1024
    new_filename = file + ".temp"
    if file_size_kB > filesize_kB:
        with open(new_filename, "w") as new_file_object:
            with open(file) as file_object:
                line_count = 0
                for line in file_object:
                    line_count += 1
                    if line_count < 200:
                        continue
                    new_file_object.write(line)

        os.remove(file)
        os.rename(new_filename, file)


def read_int_file(filename, default=0):
    ret = default
    if isfile(filename):
        content = open(filename).read()
        if content.strip():
            try:
                int(content)
                ret = int(content)
            except Exception as e:
                log("read_int_file Exception", e, content)
    return ret


def save_int_as_file(filename, number_int):
    with open(filename, 'w') as output_file:
        output_file.write(str(number_int))


def save_time_int_and_RTC_to_file(filename, machine_time_int, RTC_time_tuple=(), append=False):
    print("save_time_int_and_RTC_to_file", filename, machine_time_int, RTC_time_tuple)
    ret = str(machine_time_int) + "|" + repr(RTC_time_tuple) + "\n"
    if append:
        with open(filename, 'a') as output_file:
            output_file.write(ret)
    else:
        with open(filename, 'w') as output_file:
            output_file.write(ret)


# a time keeping method
# one file keeps current time in seconds after this boot, which will be written every cycle
# the second file keeps cumulative time before this boot

def write_current_time():
    # log("write_current_time")

    after_boot_time = read_int_file(AFTER_BOOT_TIME_FILE)
    before_boot_cum_time = read_int_file(BEFORE_BOOT_CUM_TIME_FILE)

    current_time = boot_time_s()
    save_int_as_file(AFTER_BOOT_TIME_FILE, current_time)

    # log("Stored after boot time:", after_boot_time)
    # log("Stored before boot cum time:", before_boot_cum_time)
    # log("Current boot time:", current_time)

    if current_time < after_boot_time:
        if boot_time_s() < after_boot_time:
            if boot_time_s() < after_boot_time:
                new_before_boot_cum_time = before_boot_cum_time + after_boot_time
                log("New before boot cum time:", new_before_boot_cum_time)
                save_int_as_file(BEFORE_BOOT_CUM_TIME_FILE, new_before_boot_cum_time)


def get_current_time():
    before_boot_cum_time_file = "before_boot_cum_time_file.txt"
    before_boot_cum_time = read_int_file(before_boot_cum_time_file)

    return before_boot_cum_time + boot_time_s()


def interpret_list(input_list):
    # read a list of numbers, if all of them are -1, return -1, if there are non -1 terms, read the last non -1 term
    ret = -1
    for i in input_list:
        if i != -1:
            ret = i
    return ret


def save_machine_reset_time():
    save_int_as_file('machine_reset_time.txt', boot_time_s())


def get_machine_reset_time():
    return read_int_file('machine_reset_time.txt', 0)


def find_SGP30_object(i2c_object_list):
    """
    Among a list of i2c_list, find which one has the SGP30 attached to
    :param i2c_object_list:
    :return:
    """

    for i2c in i2c_object_list:
        devices = i2c.scan()
        if 0x58 in devices:
            try:
                return SGP30(i2c)
            except Exception as e:
                print("Find SGP30 Object Failed.",e)


def find_SCD40_object(i2c_object_list):
    """
    Among a list of i2c_list, find which one has the SCD40 attached to
    :param i2c_object_list:
    :return:
    """

    for i2c in i2c_object_list:
        devices = i2c.scan()
        if 0x62 in devices:
            try:
                ret = SCD4X(i2c)
                ret.start_periodic_measurement()
                return ret
            except Exception as e:
                print("Find SCD40 Object Failed.",e)


def read_t_and_h(i2c_object):
    """
    Assume there is SHT20 or AHT10 attached on that i2c line, and do measurement on both
    :param i2c_object:
    :return:
    if there is both SHT20 and AHT10, return ((SHT20-T, SHT20-H),(AHT10-T, AHT10-H))
    if there not both present, fill with -1, e.g. ((-1,-1),(AHT10-T, AHT10-H))
    """

    AHT10_ADDR = 0x38
    SHT20_ADDR = 0b1000000

    devices = i2c_object.scan()
    ret = [[-1, -1], [-1, -1]]

    # print(devices)

    if SHT20_ADDR in devices:
        # print("SHT20:",SHT20_ADDR)
        try:
            # print("SHT20",1)
            sht20 = SHT2x(i2c_object)
            # print("SHT20",2)
            t, h = sht20.measure()
            # print("SHT20",3)
            if h > 99:
                h = 99
            if t < 0:
                t = -1
            if h < 0:
                h = -1
            ret[0] = [t, h]
        except Exception as e:
            log("SHT20 Exception", e)
    if AHT10_ADDR in devices:
        # print("AHT10:",AHT10_ADDR)
        try:
            aht10 = AHT10(i2c_object)
            t, h = aht10.measure()
            if h > 99:
                h = 99
            if t < 0:
                t = -1
            if h < 0:
                h = -1
            ret[1] = [t, h]
        except Exception as e:
            log("AHT10 Exception", e)
    return ret


custom_bar_chars = [
    [
        0b00000,
        0b00000,
        0b00000,
        0b00000,
        0b00000,
        0b00000,
        0b00000,
        0b11111
    ],
    [
        0b00000,
        0b00000,
        0b00000,
        0b00000,
        0b00000,
        0b00000,
        0b11111,
        0b11111
    ],
    [
        0b00000,
        0b00000,
        0b00000,
        0b00000,
        0b00000,
        0b11111,
        0b11111,
        0b11111
    ],
    [
        0b00000,
        0b00000,
        0b00000,
        0b00000,
        0b11111,
        0b11111,
        0b11111,
        0b11111
    ],
    [
        0b00000,
        0b00000,
        0b00000,
        0b11111,
        0b11111,
        0b11111,
        0b11111,
        0b11111
    ],
    [
        0b00000,
        0b00000,
        0b11111,
        0b11111,
        0b11111,
        0b11111,
        0b11111,
        0b11111
    ],
    [
        0b00000,
        0b11111,
        0b11111,
        0b11111,
        0b11111,
        0b11111,
        0b11111,
        0b11111
    ],
    [
        0b11111,
        0b11111,
        0b11111,
        0b11111,
        0b11111,
        0b11111,
        0b11111,
        0b11111
    ]]


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


def two_digis(number):
    """
    110 ->99
    50 ->50
    1 ->" 1"
    -1 -> -1

    Args:
        number:

    Returns:

    """

    if number>99:
        number = 99
    if number<-9:
        number = -9
    ret = str(int(number))
    if 0<=number<10:
        ret = " "+ret
    return ret


def show_time(time_sec, prefix, flash=False, flash_chr=chr(7), optimal_length=9, max_length=10):
    """

    :param flash_chr: 警示时闪烁什么字符
    :param time_sec:
    :param prefix:
    :param flash: 用于警示，如果flash是True，时间值返回一个全亮字符
    :return:
    """
    # if <99s show number
    # if <60m show minutes in xmx to show x.x minutes
    # if <24h show minutes in xhx to show x.x hour
    # if >1d show minutes in xdx to show x.x day

    sec = str(time_sec % 60)
    minute = str(int((time_sec / 60) % 60))
    hour = str(int((time_sec / 3600) % 24))
    day = str(int(time_sec / 86400))

    if time_sec <= 60:
        ret = sec + 's'
    elif time_sec < 60 * 60:
        ret = minute + 'm'
    elif time_sec < 86400:
        ret = hour + 'h'
    else:
        ret = day + "d" + hour + 'h'

    if flash:
        ret = flash_chr * len(ret)

    if len(ret)+len(prefix) < optimal_length:
        ret = prefix + " " + ret
    else:
        ret = prefix + ret

    if len(ret) < max_length:
        if flash:
            ret = ret + flash_chr * (max_length - len(ret))
        else:
            ret = ret + " " * (max_length - len(ret))
    return ret
