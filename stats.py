import time
import smbus2
import logging
from ina219 import INA219,DeviceRangeError

import Adafruit_GPIO.SPI as SPI
import Adafruit_SSD1306

from PIL import Image, ImageDraw, ImageFont

import subprocess

DEVICE_BUS = 1
DEVICE_ADDR = 0x17
PROTECT_VOLT = 3700
SAMPLE_TIME = 2

RST = None

disp = Adafruit_SSD1306.SSD1306_128_64(rst=RST)

disp.begin()

disp.clear()
disp.display()

width = disp.width
height = disp.height
image = Image.new('1', (width, height))

draw = ImageDraw.Draw(image)

draw.rectangle((0,0,width,height), outline=0, fill=0)

padding = -2
top = padding
bottom = height-padding

x = 0

dispC = 0

font = ImageFont.load_default()

while True:
    draw.rectangle((0,0,width,height), outline=0, fill=0)

    cmd = "hostname -I | cut -d\' \' -f1"
    IP = subprocess.check_output(cmd, shell=True)
    cmd = "top -bn1 | grep load | awk '{printf \"CPU: %.2f\", $(NF-2)}'"
    CPU = subprocess.check_output(cmd, shell=True)
    cmd = "free -m | awk 'NR==2{printf \"Mem: %s/%sMB %.2f%%\", $3,$2,$3*100/$2 }'"
    MemUsage = subprocess.check_output(cmd, shell=True)
    cmd = "df -h | awk '$N==\"/\"{printf \"Disk: %d/%dGB %s\", $3,$2,$5}'"
    Disk = subprocess.check_output(cmd, shell=True)
    cmd = "vcgencmd measure_temp | cut -f 2 -d '='"
    temp = subprocess.check_output(cmd, shell=True)

    ina = INA219(0.00725, address=0x40)
    ina.configure()
    piVolts = round(ina.voltage(),2)
    piCurrent = round(ina.current())

    ina = INA219(0.005,address=0x45)
    ina.configure()
    battVolts = round(ina.voltage(),2)

    try:
        battCur = round(ina.current())
        battPow = round(ina.power()/1000,1)

    except:
        battCur = 0
        battPow = 0

    bus = smbus2.SMBus(DEVICE_BUS)

    aReceiveBuf = []
    aReceiveBuf.append(0x00)

    for i in range(1,255):
        aReceiveBuf.append(bus.read_byte_data(DEVICE_ADDR, i))

    if (aReceiveBuf[8] << 8 | aReceiveBuf[7]) > 4000:
        chargeStat = "Charging USB C"
    elif (aReceiveBuf[10] << 8 | aREceiveBuf[9]) > 4000:
        chargeStat = "Charging Micro USB."
    else:
        chargeStat = "Not charging"

    battTemp = (aReceiveBuf[12] << 8 | aReceiveBuf[11])

    battCap = (aReceiveBuf[20] << 8 | aReceiveBuf[19])

    if (dispC <= 15):
        draw.text((x, top+2), "IP: " + str(IP, 'utf-8'), font=font, fill=255)
        draw.text((x, top+18), str(CPU, 'utf-8') + "%", font=font, fill=255)
        draw.text((x+80, top+18), str(temp, 'utf-8'), font=font, fill=255)
        draw.text((x, top+34), str(MemUsage, 'utf-8'), font=font, fill=255)
        draw.text((x, top+50), str(Disk, 'utf-8'), font=font, fill=255)
        dispC+=1
    else:
        draw.text((x, top+2), "PI: " + str(piVolts) + "V " + str(piCurrent) + "mA", font=font, fill=255)
        draw.text((x, top+18), "Batt: " + str(battVolts) + "V " + str(battCap) + "%", font=font, fill=255)
        if (battCur > 0):
            draw.text((x, top+34), "Chrg: " + str(battCur) + "mA " + str(battPow) + "W", font=font, fill=255)
        else:
            draw.text((x, top+34), "Dchrg: " + str(0-battCur) + "mA " + str(battPow) + "W", font=font, fill=255)
        draw.text((x+15, top+50), chargeStat, font=font, fill=255)
        dispC+=1
        if (dispC == 30):
            dispC = 0
    disp.image(image)
    disp.display()
    time.sleep(.1)
    
