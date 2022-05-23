# ESP8266 - AWS IoT

Example project of how to make an ESP8266 device communicate with AWS IoT service via MQTT protocol.

## Requirements
Building the project requires:
- NodeMCU ESP8266
- DHT11 Sensor (Pin 14 - D5)
- OLED Display 0.96 (SDA Pin 4 - D2, SCK Pin 5 - D1)

## Flash

One of the following alternatives can be used to flash the project:
- [Adafuit-Ampy](https://pypi.org/project/adafruit-ampy/)
- [Pymakr](https://github.com/pycom/pymakr-vsc/)

## Decode certificates

Before flashing the certificates, it is necessary to decode them with the following commands:

```openssl x509 -in 8266-01.cert.pem -out 8266-01.cert.der -outform DER```

```openssl rsa -in 8266-01.private.key -out 8266-01.key.der -outform DER```