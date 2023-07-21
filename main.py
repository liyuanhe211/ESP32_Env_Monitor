# -*- coding: utf-8 -*-

# SCD40 CO2不能用，一直显示Exception "NoneType" object isn't iterable，应该是measure函数不对
# 中途拔下SCD40会导致直接报错死机，应该修正

__author__ = 'LiYuanhe'

import time

import utime
from machine import SoftI2C
from lib_main import *
from Secret import WIFI_SSID, WIFI_PASSWORD

micropython.alloc_emergency_exception_buf(100)

LCD_SCL_PIN = 26
LCD_SDA_PIN = 27

FED_PUSHBUTTON_PIN = 35
FED_PUSHBUTTON = Pin(FED_PUSHBUTTON_PIN, Pin.IN)

WATER_PUSHBUTTON_PIN = 13
WATER_PUSHBUTTON = Pin(WATER_PUSHBUTTON_PIN, Pin.IN)

FED_TIMES_FILE = "feed_time_file.txt"
MACHINE_FED_TIME, RTC_FED_TIME = read_times_file(FED_TIMES_FILE)
log("Read fed time:", MACHINE_FED_TIME, RTC_FED_TIME)
fed_time_is_RTC = False

WATER_TIMES_FILE = "water_time_file.txt"
MACHINE_WATER_TIME, RTC_WATER_TIME = read_times_file(WATER_TIMES_FILE)
log("Read water time:", MACHINE_WATER_TIME, RTC_WATER_TIME)
water_time_is_RTC = False


def get_time_since_feed_s():
    global fed_time_is_RTC
    if RTC_has_been_set() and RTC_FED_TIME:
        fed_time_is_RTC = True
        print("Calc feed RTC time:", rtc.datetime(), RTC_FED_TIME, mktime_from_RTC_datetime(rtc.datetime()), mktime_from_RTC_datetime(RTC_FED_TIME))
        ret = mktime_from_RTC_datetime(rtc.datetime()) - mktime_from_RTC_datetime(RTC_FED_TIME)
    else:
        print("Calc feed machine time", get_current_time(), MACHINE_FED_TIME)
        ret = get_current_time() - MACHINE_FED_TIME

    if ret < 0:
        log("Feed record error! Feed record error!")
        log("Last line of fed_time_file:", open(FED_TIMES_FILE).readlines()[-1])
        with open(FED_TIMES_FILE, 'a') as feed_times_file_object:
            feed_times_file_object.write(str(time.time()) + '\n')
        return 0
    return ret


def feed_button_pressed():
    log("Enter feed_button_pressed Function")
    # 长按才有效
    for _ in range(10):
        time.sleep(0.02)
        if FED_PUSHBUTTON.value() == 0:
            log("Abort feed_button_pressed")
            return False

    lcd.puts("                    ")
    lcd.puts("                    ", 1)
    lcd.puts("   Feed Received    ", 2)
    lcd.puts("     Rebooting      ", 3)

    log("Hold Triggered feed_button_pressed")
    set_RTC_time(lcd)
    current_time_int = get_current_time()
    current_RTC = rtc.datetime()

    save_time_int_and_RTC_to_file(FED_TIMES_FILE, current_time_int, current_RTC, append=True)
    log('New feed time:', current_time_int, current_RTC)

    lcd.puts(center_align(time_string_from_RTC_time_tuple(current_RTC), 20), 1)

    time.sleep(1.5)
    machine.reset()


### Water time process ###

def get_time_since_water_s():
    global water_time_is_RTC
    if RTC_has_been_set() and RTC_WATER_TIME:
        water_time_is_RTC = True
        print("Calc water RTC time:", rtc.datetime(), RTC_WATER_TIME, mktime_from_RTC_datetime(rtc.datetime()), mktime_from_RTC_datetime(RTC_WATER_TIME))
        ret = mktime_from_RTC_datetime(rtc.datetime()) - mktime_from_RTC_datetime(RTC_WATER_TIME)
    else:
        print("Calc water machine time:", get_current_time(), MACHINE_WATER_TIME)
        ret = get_current_time() - MACHINE_WATER_TIME

    if ret < 0:
        log("Water record error! Water record error!")
        log("Last line of water_time_file:", open(WATER_TIMES_FILE).readlines()[-1])
        with open(WATER_TIMES_FILE, 'a') as water_times_file_object:
            water_times_file_object.write(str(time.time()) + '\n')
        return 0
    return ret


def water_button_pressed():
    log("Enter water_button_pressed Function")
    # 长按才有效
    for _ in range(10):
        time.sleep(0.02)
        if WATER_PUSHBUTTON.value() == 0:
            log("Abort water_button_pressed")
            return False

    log("Hold Triggered water_button_pressed")

    lcd.puts("                    ")
    lcd.puts("                    ", 1)
    lcd.puts("   Water Changed    ", 2)
    lcd.puts("     Rebooting      ", 3)

    set_RTC_time(lcd)
    current_time_int = get_current_time()
    current_RTC = rtc.datetime()

    save_time_int_and_RTC_to_file(WATER_TIMES_FILE, current_time_int, current_RTC, append=True)
    log('New water time:', current_time_int, current_RTC)

    time.sleep(1.5)
    machine.reset()


######################################

def initiate_lcd():
    lcd = LCD(SoftI2C(scl=Pin(LCD_SCL_PIN), sda=Pin(LCD_SDA_PIN), freq=100000))
    lcd.puts("                    ", )
    lcd.puts("     Voldemort      ", 1)
    lcd.puts("    Life Support    ", 2)
    for bar_char_count, bar_char in enumerate(custom_bar_chars):
        lcd.create_character(bar_char_count, bar_char)
    return lcd


lcd = initiate_lcd()

time.sleep(0.5)

WIFI = connect_wifi(WIFI_SSID, WIFI_PASSWORD, lcd)
set_RTC_time(lcd)

# i2c-A: SCL 19 SDA 22
# i2c-B: SCL 18 SDA 23
# i2c-C: SCL 16 SDA 17
# i2c-D: SCL 2 SDA 4
# i2c-E: SCL 32 SDA 33

# 每一个i2c上连一个AHT10或者SHT20，如果存在，SHT20排在AHT10前面

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


def main():
    write_current_time()

    AHT10_t_lists = [[] for _ in range(5)]
    AHT10_h_lists = [[] for _ in range(5)]
    SHT20_t_lists = [[] for _ in range(5)]
    SHT20_h_lists = [[] for _ in range(5)]

    global cycle_time, cycle_count
    global last_write_time, last_LCD_refresh, last_tick
    global lcd, SCD40_object, SGP30_object

    CO2, VOC = '----', '----'  # CO2和VOC更新太快，每两个周期更新一次
    # fed_pushbutton.irq(button_pressed,trigger=Pin.IRQ_FALLING)

    # html server
    addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
    s = socket.socket()
    s.bind(addr)
    s.listen(1)

    while True:
        print("-------------------------------------------------------")
        if FED_PUSHBUTTON.value() == 1:
            feed_button_pressed()
            lcd = initiate_lcd()

        if WATER_PUSHBUTTON.value() == 1:
            water_button_pressed()
            lcd = initiate_lcd()

        # print(6)
        cycle_count += 1
        # 30秒备份一次时间，因为备份时间耗时几百毫秒，不能太频繁
        if boot_time_s() - last_write_time > 30:
            write_current_time()
            last_write_time = boot_time_s()

        # 防止屏幕数据不全，600秒重置一次屏幕
        if boot_time_s() != last_LCD_refresh and boot_time_s() % 600 == 1:
            log("Screen reset")
            last_LCD_refresh = boot_time_s()
            lcd = initiate_lcd()

        # print(7)
        for i2c_count, i2c_object in enumerate(i2c_list):
            # print("I2C:",i2c_count)
            SHT20_t_h, AHT10_t_h = read_t_and_h(i2c_object)
            SHT20_t, SHT20_h = SHT20_t_h
            AHT10_t, AHT10_h = AHT10_t_h
            SHT20_t_lists[i2c_count].append(SHT20_t)
            SHT20_h_lists[i2c_count].append(SHT20_h)
            AHT10_t_lists[i2c_count].append(AHT10_t)
            AHT10_h_lists[i2c_count].append(AHT10_h)
            # 保留5个最后结果，如果短暂中断不影响显示
            SHT20_t_lists[i2c_count] = SHT20_t_lists[i2c_count][-5:]
            SHT20_h_lists[i2c_count] = SHT20_h_lists[i2c_count][-5:]
            AHT10_t_lists[i2c_count] = AHT10_t_lists[i2c_count][-5:]
            AHT10_h_lists[i2c_count] = AHT10_h_lists[i2c_count][-5:]
        # print(8)
        # 从SGP30 读取VOC，因为SGP30的CO2质量很差，不要它的CO2
        if cycle_count % 2 == 0:
            print("Measuring CO2, VOC")
            if not SGP30_object:
                SGP30_object = find_SGP30_object(i2c_list)
            try:
                CO2_dump, VOC = SGP30_object.indoor_air_quality
                print("VOC:", CO2_dump, VOC)
            except Exception as e:
                log("SGP30 Exception", e, "\n")
                SGP30_object = find_SGP30_object(i2c_list)
                try:
                    CO2_dump, VOC = SGP30_object.indoor_air_quality
                except Exception as e:
                    log("SGP30 Exception 2", e, "\n")
                    CO2_dump, VOC = -1, -1

            if VOC > 9999:
                VOC = 9999

            if VOC == -1:
                VOC = '----'
            else:
                VOC = str(int(VOC)) + " " * (4 - len(str(int(VOC))))

            if cycle_count < 24:  # 前15秒没有信号
                VOC = "init"

            if not SCD40_object:
                SCD40_object = find_SCD40_object(i2c_list)
            try:
                CO2, CO2_Temp, CO2_Humid = SCD40_object.measure()
                print("CO2:", CO2, CO2_Temp, CO2_Humid)
            except Exception as e:
                print("SCD40 Exception", e, "\n")
                SCD40_object = find_SCD40_object(i2c_list)
                try:
                    CO2, CO2_Temp, CO2_Humid = SCD40_object.measure()
                except Exception as e:
                    print("SCD40 Exception 2", e, "\n")
                    CO2, CO2_Temp, CO2_Humid = -1, -1, -1

            if CO2 == -1:
                CO2 = '----'
            elif CO2 <= 400:
                CO2 = 'low '
            else:
                CO2 = str(int(CO2)) + " " * (4 - len(str(int(CO2))))

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

        # print(10)

        # log(2, time.ticks_ms())
        SHT20_t_results = [interpret_list(x) for x in SHT20_t_lists]
        SHT20_h_results = [interpret_list(x) for x in SHT20_h_lists]
        AHT10_t_results = [interpret_list(x) for x in AHT10_t_lists]
        AHT10_h_results = [interpret_list(x) for x in AHT10_h_lists]

        print("SHT20_t", [int(x * 10) / 10 for x in SHT20_t_results], "SHT20_h", [int(x * 10) / 10 for x in SHT20_h_results])
        print("AHT10_t", [int(x * 10) / 10 for x in AHT10_t_results], "AHT10_h", [int(x * 10) / 10 for x in AHT10_h_results])

        # 一共最多10个结果[SHT1,AHT1,SHT2,AHT2...]，选其中五个显示
        ret_t = [-1, -1, -1, -1, -1]
        ret_h = [-1, -1, -1, -1, -1]
        ret_marker = [False, False, False, False, False]  # 用于记录该结果是不是SHT20带来的，如果是，为True

        # 如果结果中的某位置有至少一个结果，填进去
        for i in range(5):
            if SHT20_t_results[i] != -1:
                ret_marker[i] = True
                ret_t[i] = SHT20_t_results[i]
                ret_h[i] = SHT20_h_results[i]
                SHT20_t_results[i] = -1
                SHT20_h_results[i] = -1
                ret_marker[i] = True
            elif AHT10_t_results[i] != -1:
                ret_t[i] = AHT10_t_results[i]
                ret_h[i] = AHT10_h_results[i]
                AHT10_t_results[i] = -1
                AHT10_h_results[i] = -1
        # 如果没有，看看两边有没有多的给匀一匀，优先找前面的，此时SHT20的结果必然被用光，只可能是AHT10的结果
        for i in range(5):
            if ret_t[i] == -1:
                if i > 0 and AHT10_t_results[i - 1] != -1:
                    ret_t[i] = AHT10_t_results[i - 1]
                    ret_h[i] = AHT10_h_results[i - 1]
                    AHT10_t_results[i - 1] = -1
                    AHT10_h_results[i - 1] = -1
                elif i < 4 and AHT10_t_results[i + 1] != -1:
                    ret_t[i] = AHT10_t_results[i + 1]
                    ret_h[i] = AHT10_h_results[i + 1]
                    AHT10_t_results[i + 1] = -1
                    AHT10_h_results[i + 1] = -1

        # log(3, time.ticks_ms())
        t1, t2, t3, t4, t5 = ret_t
        h1, h2, h3, h4, h5 = ret_h
        line1 = "%s %s %s %s %s %s%s%s%s%s" % (two_digis(t1), two_digis(t2), two_digis(t3), two_digis(t4), two_digis(t5),
                                               t_to_bar(t1), t_to_bar(t2), t_to_bar(t3), t_to_bar(t4), t_to_bar(t5))
        line1 = line1.replace('-1', '--')
        line2 = "%s %s %s %s %s %s%s%s%s%s" % (two_digis(h1), two_digis(h2), two_digis(h3), two_digis(h4), two_digis(h5),
                                               h_to_bar(h1), h_to_bar(h2), h_to_bar(h3), h_to_bar(h4), h_to_bar(h5))
        line2 = line2.replace('-1', '--')

        line1 = list(line1)
        line2 = list(line2)
        # 如果当前位置是SHT20测得，后面加个点
        for count, i in enumerate(ret_marker):
            if i:
                line1[2 + count * 3] = "."
                line2[2 + count * 3] = "."
        line1 = "".join(line1)
        line2 = "".join(line2)

        if cycle_count % 2 == 0:
            line3 = "CO2  %s.VOC  %s" % (CO2, VOC)
        else:
            line3 = "CO2  %s VOC  %s" % (CO2, VOC)

        time_since_feed = get_time_since_feed_s()
        time_since_water = get_time_since_water_s()

        if fed_time_is_RTC:
            fed_text = show_time(time_since_feed, prefix="Fed:")
        else:
            fed_text = show_time(time_since_feed, prefix="Fed ")

        if water_time_is_RTC:
            water_text = show_time(time_since_water, prefix="H2O:", flash=(cycle_count % 2 == 0 and time_since_water > 86400 * 1.5))
        else:
            water_text = show_time(time_since_water, prefix="H2O ", flash=(cycle_count % 2 == 0 and time_since_water > 86400 * 1.5))

        line4 = fed_text + water_text
        line4 = line4 + " " * (20 - len(line4)) if len(line4) < 20 else line4

        # 如果有气温传感器超出绝对安全范围（18~35），给出发光警告
        temp_list = [x for x in [t1, t2, t3, t4, t5] if x != -1]
        temp_warning = False
        if max(temp_list) > 35:
            temp_warning = True
        if min(temp_list) < 18:
            temp_warning = True
        # 如果>31°C的探头达到3个（晒点一个，热区一个，其他不应该超过31）
        if len([x for x in temp_list if x>31])>=3:
            temp_warning = True
        # 如果全栖地超过30，Warning
        if len([x for x in temp_list if x>30])==5:
            temp_warning = True
        if temp_list and cycle_count % 2 == 0 and temp_warning:
            line1 = chr(7) * 20
            line2 = chr(7) * 20
            line3 = chr(7) * 20
            line4 = chr(7) * 20

        line1 = line1 + " "*(20-len(line1)) if len(line1)<20 else line1
        line2 = line2 + " "*(20-len(line2)) if len(line2)<20 else line2
        line3 = line3 + " "*(20-len(line3)) if len(line3)<20 else line3
        line4 = line4 + " "*(20-len(line4)) if len(line4)<20 else line4

        # print(11)
        #TODO: 显示完 log 11 后 Mobaxterm 报错Error reading from serial device
        try:
            lcd.puts(line1[:20])
            lcd.puts(line2[:20], 1)
            lcd.puts(line3[:20], 2)
            lcd.puts(line4[:20], 3)
        except Exception as e:
            log("LCD Error.")
            time.sleep(2)
            lcd = initiate_lcd()

        # print(12)
        screen_content_log = "--------------------\n" + \
                             line1 + "\n" + \
                             line2 + "\n" + \
                             line3 + "\n" + \
                             line4 + "\n" + \
                             "--------------------\n"

        # print(screen_content_log)

        if cycle_count % 50 == 5:
            log(screen_content_log)

        # print(13)
        # log(5, time.ticks_ms())

        # HTML_server
        # print("Waiting for html")
        # cl, addr = s.accept()
        # log('Client connected from', addr)
        # req = cl.recv(1024)
        # if req:
        #     cl.send('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
        #     cl.send(screen_content_log + open(LOG_FILE).read())
        # cl.close()
        # time.sleep(10)

        # log(12)
        # automatic reboot
        if boot_time_s() > 3600:
            # log(boot_time_s(),last)
            save_machine_reset_time()
            machine.reset()


main()
