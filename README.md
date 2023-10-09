# ESP32 Environment Monitor
A `ESP32` Micropython script with 5 temperature/humidity sensors, a CO2 sensor, and a VOC sensor. The main use case is for animal enclosure for something like turtles, geckos, or other reptiles.

## Features
<p align="center"><img src="https://user-images.githubusercontent.com/18537705/189532100-be7e42fc-0c2c-44f3-90f5-0855ee6ebf16.png" width="30%" height="30%" align="center"></img></p>

 - Display 5 temperatures and humidities from 5 `AHT10` probes. (Results rounded to 0.1 °C and 1% RH.)
 - Draw a graphical representation of the temperatures with bars.
 - Connects a button to record the time since an event. (The time keeping is kept if power to the `ESP32` is lost, and will be resumed on the next power-up. So basically no RTC is needed, unless prolonged power outage is a problem.)
 - Flash-screen warning if temperature is out of range.

## Electrical connections
The components are soldered to a prototyping board, illustrated below. The left part is an independent circuit for blinking LEDs with NE555P. The connection of this part to the ESP32 is only the 5V power lines. 
<p align="center"><img src="https://user-images.githubusercontent.com/18537705/189532858-6f847828-7ec4-4595-93ca-2afe75395624.png" width="70%" height="70%" align="center"></img></p>

# A standard thermometer and humidity monitor with screen
# Connection for ESP32

# Connect a [Parallel to I2C Chip] to a LCD2004 screen
# Just solder all pins sequentially to the screen, Direction: (pin towards [GND, VCC, SDA, SCL] pin connects to the VSS pin of the Screen

Connect [Parallel to I2C Chip] to ESP8266
GND - GND
VCC - VIN
SCL - 26
SDA - 27
Also
SDA - 10K resister - GND
SCL - 10K resister - GND


Connect Five AHT10 chip to ESP32, without pull-up resister, using internal pull up resister
Sensor-i2c A: SCL 19 SDA 22
Sensor-i2c A: SCL 18 SDA 23
Sensor-i2c A: SCL 16 SDA 17
Sensor-i2c A: SCL 2 SDA 4
Sensor-i2c A: SCL 32 SDA 33

Attach any SCD40 to any one of the AHT10 I2C channel (G-G, V-V, SCL-SCL, SDA-SDA)

Connect a Fed Pushbutton between 35 and 3V3, pull down 35 with 2k resister
Connect a Water Pushbutton between 13 and 3V3, pull down 13 with 2k resister

 - `[5V]  - [LCD2004-VCC]`
 - `[3.3V]  - [AHT10-VCCs] - [Button_Pin1]`
 - `[GND]  - [AHT10-GNDs] - [LCD2004-GND] - [Button-Pulldown-Resister_Pin1]`
 - `[ESP32-GPIO35] - [Button_Pin2] - [Button-Pulldown-Resister_Pin2]`
 - `[Sensor-A-SCL] - [GPIO19]`
 - `[Sensor-A-SDA] - [GPIO22]`
 - `[Sensor-B-SCL] - [GPIO18]`
 - `[Sensor-B-SDA] - [GPIO23]`
 - `[Sensor-C-SCL] - [GPIO16]`
 - `[Sensor-C-SDA] - [GPIO17]`
 - `[Sensor-D-SCL] - [GPIO2]`
 - `[Sensor-D-SDA] - [GPIO4]`
 - `[Sensor-E-SCL] - [GPIO32]`
 - `[Sensor-E-SDA] - [GPIO33]`
 - `[PCF8574-SCL] - [GPIO26]`
 - `[PCF8574-SDA] - [GPIO27]`
 - `[PCF8574] ≡ [LCD2004] follow PCF8574 chip instruction`


 
---

Light sub panel

S9014, DC current gain = 280, 
Collector-emitter voltage = 12 V
IB = 0.1 ~ 0.16 mA
Base-Emitter satuation current  = 600~800 mA

Assuming IC = 100 mA
Gain  = 50
IB = 2 mA
VB = 3 V
RB = 1Kohm

Using RB = 300 ohm