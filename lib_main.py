# -*- coding: utf-8 -*-
__author__ = 'LiYuanhe'

from machine import Pin, Signal
import time
import socket
import machine
import network
import micropython
import os
from collections import OrderedDict


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


def show_time(time_sec, prefix, flash = False, flash_chr=chr(7)):
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
        ret = flash_chr*len(ret)

    if len(ret) < 6:
        ret = prefix + " " + ret
    else:
        ret = prefix + ret

    if len(ret) < 9:
        if flash:
            ret = ret + flash_chr * (9 - len(ret))
        else:
            ret = ret + " " * (9 - len(ret))
    return ret

