import json, time, urllib.parse, urllib.request, os, re, sys
OUT = r"D:\proyectos\expertia\training\datasets\physics_raw\ti_parts.jsonl"
os.makedirs(os.path.dirname(OUT), exist_ok=True)
LOCK = os.path.join(os.path.dirname(OUT), ".harvest_ti.lock")
if os.path.exists(LOCK):
    print("lock exists, exit.")
    sys.exit(0)
open(LOCK, "w").write(str(os.getpid()))
import atexit
atexit.register(lambda: os.path.exists(LOCK) and os.remove(LOCK))
UA = {"User-Agent": "Expertia/1.0 (electronics dataset harvest)"}
PARTS = """NE555,SA555,LM555,LM741,LM358,LM386,LM393,LM339,LM317,LM7805,LM7812,LM7905,LM1117,TL071,TL072,TL082,TL084,
OPA2134,OPA2604,OPA134,OPA627,INA128,INA125,TL431,LM4040,REF5025,LM285,TPS54360,TPS561201,LM2596,LM2576,MC34063,
LMR33630,LMZ14201,SN74HC00,SN74HC04,SN74HC08,SN74HC32,SN74HC74,SN74HC595,SN74HC165,SN74HC245,SN74HC138,SN74HC573,
CD4017,CD4021,CD4040,CD4060,CD4071,CD4081,CD4511,CD4011,CD4001,CD4049,CD4050,CD4066,CD4051,CD4052,CD4053,
TLC5940,TLC5916,TPIC6B595,ULN2003,ULN2803,L293D,L298N,DRV8825,DRV8833,A4988,TMC2209,TAS5612,LM386N,TDA2050,TDA7294,
TDA7498,PCM5102,PCM1808,ADS1115,ADS1015,MCP3008,MCP4725,DAC0808,ADC0804,TLV5618,MAX232,MAX485,SN65HVD230,TCAN1042,
ISO1540,ISO7221,HCPL-2630,6N137,PC817,TLP281,MOC3021,MOC3041,LM35,TMP36,TMP102,DS18B20,HDC1080,BMP280,BME280,MPU6050,
HMC5883L,ADXL345,LIS3DH,VL53L0X,HC-SR04,TSOP38238,IRF540,IRF9540,IRLZ44N,IRF3205,IRFZ44N,TIP120,TIP122,2N7000,BS170,
BSS138,IRLML2502,AO3400,BC547,BC557,BD139,BD140,MJE3055,MJE2955,2N3055,MJ15003,1N4007,1N4148,1N5819,1N5822,1N4733A,
BZX55C5V1,1N4742A,1N5408,FR107,UF4007,HER108,BAT54,BAT85,LED,Crystal,Quartz,Resonator,Relay,G5V-1,SRD-05VDC,LY2N-J,
Contactor,Transformer,EI33,Flyback,Common-mode-choke,Ferrite-bead,Inductor,Capacitor,MLCC,Tantalum,Electrolytic,
Potentiometer,Trimmer,Thermistor,NTCLE100E3,PTC,Varistor,MOV,Fuse,Polyfuse,Diode-bridge,KBPC3510,W04,ESD,TVS,SMAJ5.0A,
P6KE,Crystal-oscillator,TCXO,OCXO,PLL,CD4046,74HC4046,LM567,NE567,XR2206,ICL8038,AD9850,Si5351,DS1307,DS3231,PCF8523,
AT24C256,24LC256,25LC256,W25Q32,FM24C256,CAT24C08,DS2431,ESP32,ESP8266,RP2040,MSP430G2553,MSP430G2231,TM4C123GH6PM,
CC2530,CC2540,nRF24L01,NRF52840,HC-05,HC-06,JDY-08,HM-10,ESP32-CAM,OV7670,OV2640,GC0308,LCD1602,LCD2004,SSD1306,
SH1106,ST7735,ILI9341,HX8357,WS2812B,SK6812,TM1637,MAX7219,HT16K33,PCA9685,ADS7830,PCF8591,MCP23017,PCF8574,TCA9548A,
INA219,INA226,ACS712,ZMPT101B,SCT-013,HX711,Load-cell,Strain-gauge,Flex-sensor,FSR402,Potentiometer-slider,Rotary-encoder,
KY-040,Joystick,PS2-PS2,Keypad-4x4,Buzzer,Active-buzzer,Passive-buzzer,Speaker,Vibration-motor,Servo-motor,SG90,MG996R,
Stepper-motor,NEMA17,28BYJ-48,DC-motor,TT-motor,Encoder,Hall-sensor,A3144,SS49E,Reed-switch,Float-switch,PIR-sensor,
HC-SR501,DHT22,DHT11,SHT31,BH1750,TSL2561,TCS34725,Color-sensor,UV-sensor,ML8511,Sound-sensor,KY-038,Flame-sensor,
Gas-sensor,MQ-2,MQ-135,Soil-moisture,Capacitive-soil,YL-69,Water-level,Flow-sensor,YF-S201,Pressure-sensor,MPX4115A,
BMP180,Altimeter,Compass,QMC5883L,Gyroscope,Accelerometer,IMU,BNO055,MPU9250,LSM6DS3,GPS-module,NEO-6M,NEO-M8N,SIM800L,
A6-GPRS,ESP32-SIM,LoRa,SX1278,RA-02,NRF905,CC1101,RFID,RC522,PN532,NFC-tag,Smart-card,Finger-sensor,AS608,R307,
Camera-module,USB-TTL,CP2102,CH340G,FT232RL,PL2303,Logic-analyzer,Multimeter,Oscilloscope,Function-generator,
Bench-supply,Soldering-station,Helping-hands,Breadboard,Jumper-wires,Perfboard,PCB,FR4,Copper-clad,Ferric-chloride,
Solder-wire,Flux,Solder-paste,Hot-air,Desoldering-pump,Tweezers,Wire-stripper,Crimper,Harness,Terminal-block,
Screw-terminal,Barrel-jack,USB-C-connector,Micro-USB,Mini-USB,USB-A,USB-B,HDMI,DP-connector,VGA,DB9,RJ45,Ethernet,
W5500,ENC28J60,ESP32-Ethernet,PoE,Splitter,Optocoupler-relay,Solid-state-relay,Fotek-SSR,Zero-crossing,Triac,BTA16,
BT136,Diac,DB3,Thyristor,SCR,IGBT,SiC-MOSFET,GaN-FET,EPC2034,Driver-IC,IR2104,IR2110,TC4420,MCP1407,UCC27211,
Gate-driver,Half-bridge,Full-bridge,H-bridge,Charge-pump,Bootstrap,Snubber,Flyback-diode,TVS-diode,Zener-regulator,
Shunt-regulator,Series-regulator,LDO,Buck,Boost,Buck-boost,SEPIC,Cuk,Flyback-converter,Forward-converter,Push-pull,
Half-bridge-converter,LLC-resonant,Phase-shifted,PFC,Active-PFC,Bridge-rectifier,Voltage-doubler,Charge-pump-voltage,
Super-capacitor,Lithium-battery,LiPo,NiMH,NiCd,Lead-acid,Alkaline,Zinc-carbon,Silver-oxide,CR2032,18650,21700,
Battery-holder,Battery-charger,TP4056,CN3791,BQ24074,Power-bank,Solar-panel,MPPT,Wind-turbine,Dynamo,Peltier,TEC1-12706,
Heatsink,Thermal-paste,Fan,Blower,Pump,Reservoir,Radiator,Fitting,Tubing,Coolant,Flow-meter,Level-sensor,Leak-detector""".replace("\n", "").split(",")


def fetch(url):
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read().decode("utf-8", "ignore")
        except Exception as e:
            if attempt == 2:
                return ""
            time.sleep(2 * (attempt + 1))
    return ""


seen, total = set(), 0
with open(OUT, "a", encoding="utf-8") as f:
    for i, part in enumerate([p.strip() for p in PARTS if p.strip()]):
        if part in seen:
            continue
        seen.add(part)
        html = fetch("https://www.ti.com/product/%s" % urllib.parse.quote(part))
        if not html or len(html) < 50000:
            continue
        m = re.search(r'"description"\s*:\s*"([^"]{10,300})"', html)
        desc = m.group(1) if m else ""
        variants = re.findall(r'"name"\s*:\s*"([A-Z0-9][^"]{2,40})"\s*,\s*"description"\s*:\s*"([^"]{5,200})"', html)
        if not desc and not variants:
            continue
        body = "Componente: %s. Descripcion: %s." % (part, desc)
        for vn, vd in variants[:12]:
            body += " Variante %s: %s." % (vn, vd)
        if len(body) < 120:
            continue
        f.write(json.dumps({"qid": "ti-%s" % part.lower(), "label": part,
                            "formula": body[:2000], "instance_of": "ti-part",
                            "source": "ti_datasheet"}, ensure_ascii=False) + "\n")
        total += 1
        if i % 10 == 0:
            print("part %d: total=%d" % (i, total))
        time.sleep(1.0)
print("DONE total=%d" % total)
