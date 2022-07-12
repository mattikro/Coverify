import board
import busio
import time
from digitalio import DigitalInOut
import binascii
from secrets import secrets
import network
import display
from adafruit_display_text import label
import terminalio
import gc
import json

try:
    f = open('t.txt', 'w')
    f.write('')
except OSError:
    print('DEV MODE')
    display.image('dev.bmp')
    while True:
        time.sleep(1)

old = ''
try:
    display.image()
except Exception:
    print('whoops')

if not network.connect(1):
    network.esp.create_AP('COVERIFY', '12345678')
    print('AVAILABLE AT: ' + network.ip())
    network.startServer()
    network.rebootOnUpdate = True
    while network.dataUpdated is False:
        network.updateServer()

# print(binascii.hexlify(network.esp.MAC_address))
# print(network.esp.MAC_address_actual)
#
# while True:
#     pass
while True:
    try:
        print('trying to refresh token')
        r = network.requests.get(
            'https://coverify.makro.ca/refreshToken?refresh_token=' + secrets['refresh_token'] + '&ip=' + network.ip())
        network.updateData(r.json())
        r.close()
    except ValueError or KeyError:
        gc.collect()
        print('refreshing token failed')
        topText = label.Label(terminalio.FONT, text=' AUTHORIZE', color=0x00FF00, x=0, y=4)
        bottomText = label.Label(terminalio.FONT, text='  SPOTIFY', color=0x00FF00, x=0, y=58)
        display.qrcode('coverify.makro.ca/auth?ip=' + network.ip(), text=[topText, bottomText])

        network.startServer()
        network.rebootOnUpdate = True
        while network.dataUpdated is False:
            network.updateServer()

    current = network.currentlyPlaying()
    last = time.monotonic()
    try:
        while True:
            print('TOP OF IMAGE LOOP')
            while old == current:
                while time.monotonic() - last < 2:
                    pass
                last = time.monotonic()
                print('requesting')
                current = network.currentlyPlaying()
                print(time.monotonic() - last)

            print('UPDATING IMAGE')
            print(current)
            network.image(current)
            print('attempting to display')
            display.image()
            old = current
    except Exception as e:
        print(e)
