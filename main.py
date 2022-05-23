from machine import I2C, Pin, RTC, reset, freq
import ssd1306
import dht
import ntptime
import json
import time
from wifi_manager import WifiManager
from umqtt.simple import MQTTClient

# ESP8266 - 160 MHz
freq(160000000)

# Wifi Manager
wm = WifiManager('WiFiManager', 'wifimanager')

# OLED SSD1306
i2c = I2C(sda=Pin(4), scl=Pin(5))
display = ssd1306.SSD1306_I2C(128, 64, i2c)

# DHT11
sensor = dht.DHT11(Pin(14))

# RTC
rtc = RTC()

# AWS IoT Core - MQTT
CLIENT_ID = b'esp8266'
AWS_ENDPOINT = b'a2p90nfxm9qc10-ats.iot.eu-west-1.amazonaws.com'
PUBLISH_TOPIC = b'weather'
SUBSCRIBE_TOPIC = b'message'
KEY_FILE = b'/certs/private.pem.key.der'
CERT_FILE = b"/certs/certificate.pem.crt.der"
PUBLISH_EVERY_N_SECONDS = 5

def show_oled(line1='', line2='', line3='', center=False, wait=False, sleep_ms=2000):
    display.fill(0)
    display.text(f"{'AWS IoT Core'[:16]:^16}", 0, 0, 1)
    display.text(f"{'ESP8266'[:16]:^16}", 0, 8, 2)

    y_pos = 32

    if line2 != '' and line3 != '':
        y_pos-=8
    elif line2 != '' and line3 == '':
        y_pos-=4

    display.text(f"{line1[:16]:16}" if not center else f"{line1[:16]:^16}", 0, y_pos, 3)
    display.text(f"{line2[:16]:16}" if not center else f"{line2[:16]:^16}", 0, y_pos + 8, 4)
    display.text(f"{line3[:16]:16}" if not center else f"{line3[:16]:^16}", 0, y_pos + 16, 4)

    display.text(f"{wm.get_address()[0] if wm.is_connected() else 'Not connected':^16}", 0, 56, 4)
    display.show()

    if wait:
        time.sleep_ms(sleep_ms)

def get_timestamp():
    return time.time() + 946684800 # MicroPython epoch starts from 01/01/2000, we add 30 years

def connect_aws_iot():
    show_oled('Connectint to', 'AWS IoT Core...')
    try:
        with open(KEY_FILE, 'r') as k:
            with open(CERT_FILE, 'r') as c:
                cert = c.read()
                key = k.read()
                mqtt = MQTTClient(CLIENT_ID, AWS_ENDPOINT,
                    port = 8883,
                    keepalive = 1000,
                    ssl = True,
                    ssl_params = {'key': key, 'cert': cert, 'server_side': False})
                mqtt.set_callback(on_data_received)
                mqtt.connect(clean_session=False)
                show_oled('Connected to', 'AWS IoT Core!', wait=True)
                mqtt.subscribe(SUBSCRIBE_TOPIC)
                return mqtt
    except Exception as err:
        print('Error connecting AWS IoT Core', err)
        show_oled('Error', 'connecting', 'AWS IoT Core!', wait=True)
        return None

def on_data_received(topic, data):
    print(f'Received data from topic {topic}: {data}')
    data = json.loads(data)
    line1 = data.get('line1', '')
    line2 = data.get('line2', '')
    line3 = data.get('line3', '')
    center = data.get('center', False)
    wait = data.get('wait', True)
    sleep_ms = data.get('sleep_ms', 2000)
    show_oled(line1=line1, line2=line2, line3=line3, center=center, wait=wait, sleep_ms=sleep_ms)

# Connect to Wifi
wm.connect()
show_oled('Connecting to', 'Wifi...', center=True)

while not wm.is_connected():
    pass
else:
    ntptime.settime()
    show_oled('Connected to', 'Wifi!', center=True, wait=True)

# Connect to AWS IoT Core
mqtt = connect_aws_iot()

last_publish_timestamp = get_timestamp()

while wm.is_connected():
    sensor.measure()
    temp = sensor.temperature()
    hum = sensor.humidity()
    current_timestamp = get_timestamp()
    if mqtt and current_timestamp >= last_publish_timestamp + PUBLISH_EVERY_N_SECONDS:
        mqtt.check_msg() # check new messages
        mqtt.publish(topic=PUBLISH_TOPIC, msg=json.dumps({'temp': temp, 'hum': hum, 'timestamp': current_timestamp}), qos = 0 )
        last_publish_timestamp = current_timestamp
    show_oled('Temper.: %2.1f C' %temp, 'Humidity: %3.1f %%' %hum)
    time.sleep_ms(200)
else:
    show_oled('Disconnected', 'from Wifi!', 'Rebooting...', center=True, wait=False)
    reset()
