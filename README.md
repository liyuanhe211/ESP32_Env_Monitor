# ESP32 Environment Monitor
A `ESP32` Micropython script with 5 temperature/humidity sensors, CO2 sensor, and VOC sensor.

## Features
<p align="center"><img src="https://user-images.githubusercontent.com/18537705/189532100-be7e42fc-0c2c-44f3-90f5-0855ee6ebf16.png" width="30%" height="30%" align="center"></img></p>

 - Display 5 temperatures and humidities from 5 `AHT10` probes. (Results rounded to 0.1 °C and 1% RH.)
 - Draw a graphical representation of the temperatures with bars.
 - Connects a button to record the time since an event. (The time keeping is kept if power to the `ESP32` is lost, and will be resumed on the next power-up. So basically no RTC is needed, unless prolonged power outage is a problem.)
 - Flash-screen warning if temperature is out of range.

## Electrical connections
The components are soldered to a prototyping board, illustrated below. The left part is an independent circuit for blinking LEDs with NE555P. The connection of this part to the ESP32 is only the 5V power lines. 
<p align="center"><img src="https://user-images.githubusercontent.com/18537705/189532858-6f847828-7ec4-4595-93ca-2afe75395624.png" width="70%" height="70%" align="center"></img></p>

 - `[5V]  - [LCD2004-VCC]`
 - `[3.3V]  - [AHT10-VCCs] - [Button_Pin1]`
 - `[GND]  - [AHT10-GNDs] - [LCD2004-GND] - [Button-Pulldown-Resister_Pin1]`
 - `[ESP32-GPIO35] - [Button_Pin2] - [Button-Pulldown-Resister_Pin2]`
 - `[AHT10-A-SCL] - [GPIO19]`
 - `[AHT10-A-SDA] - [GPIO22]`
 - `[AHT10-B-SCL] - [GPIO18]`
 - `[AHT10-B-SDA] - [GPIO23]`
 - `[AHT10-C-SCL] - [GPIO16]`
 - `[AHT10-C-SDA] - [GPIO17]`
 - `[AHT10-D-SCL] - [GPIO2]`
 - `[AHT10-D-SDA] - [GPIO4]`
 - `[AHT10-E-SCL] - [GPIO32]`
 - `[AHT10-E-SDA] - [GPIO33]`
 - `[PCF8574-SCL] - [GPIO26]`
 - `[PCF8574-SDA] - [GPIO27]`
 - `[PCF8574] ≡ [LCD2004] follow PCF8574 chip instruction`

