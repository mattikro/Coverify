import busio
import time
import board
from digitalio import DigitalInOut
import adafruit_requests as requests
import adafruit_esp32spi.adafruit_esp32spi_socket as socket
from adafruit_esp32spi import adafruit_esp32spi
import adafruit_esp32spi.adafruit_esp32spi_wsgiserver as server
from adafruit_wsgi.wsgi_app import WSGIApp
import supervisor
import json
from secrets import secrets

esp32_cs = DigitalInOut(board.ESP_CS)
esp32_ready = DigitalInOut(board.ESP_BUSY)
esp32_reset = DigitalInOut(board.ESP_RESET)
spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
esp = adafruit_esp32spi.ESP_SPIcontrol(spi, esp32_cs, esp32_ready, esp32_reset, debug=0)
requests.set_socket(socket, esp)
addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
web_app = WSGIApp()
server.set_interface(esp)
wsgiServer = server.WSGIServer(80, application=web_app)

dataUpdated = False
rebootOnUpdate = False


@web_app.route("/wifi")
def wifi(request):
    with open('wifi.html', 'r') as f:
        page = f.read()
        options = ''
        for networks in esp.get_scan_networks():
            options += '<option value="' + networks['ssid'].decode() + '">' + networks['ssid'].decode() + '</option>'
        page = page[:page.find('</select>')] + options + page[page.find('</select>'):]
        print(page)
        return ('200 OK', [], [page.encode()])


@web_app.route("/data")
def data(request):
    updateData(request.query_params)
    return ('200 OK', [], [
        '<body style="background: #222222"><br><br><h1 style="justify-content: center;text-align: center;color: white">SPOTIFY AUTHENTICATED</h1><h4 style="justify-content: center;text-align: center;color: white">YOU CAN CLOSE THIS TAB</h4></body>'])


def updateData(data):
    print(data)
    if 'error' in data:
        raise ValueError
    for key in data:
        secrets[key] = data[key]
    f = open('secrets.py', 'w')
    f.write('secrets = ' + json.dumps(secrets))
    f.close()
    if rebootOnUpdate:
        supervisor.reload()


def currentlyPlaying():
    r = requests.get('https://coverify.makro.ca/currentlyPlaying?token=' + secrets['access_token'])
    return r.text
    # headers = {
    #     "Authorization": "Bearer " + secrets['access_token'],
    #     "Content-Type": "application/json",
    #     'Accept': 'application/json'
    # }
    # print('ABOUT TO REQUEST')
    # r = requests.get('https://api.spotify.com/v1/me/player/currently-playing', headers=headers)
    # print('request made')
    # try:
    #     data = r.json()
    #     print('json loaded')
    #     r.close()
    #     print(data['progress_ms'])
    #     return data['item']['album']['images'][2]['url']
    # except (TypeError, ValueError) as e:
    #     r.close()
    #     print('error')
    #     print(e)
    #     return None


def connect(timeout):
    for i in range(timeout):
        try:
            esp.connect_AP(secrets['ssid'], secrets['password'])
            print("Connected to", str(esp.ssid, "utf-8"), "\tRSSI:", esp.rssi)
            print("My IP address is", esp.pretty_ip(esp.ip_address))
            return True
        except RuntimeError as e:
            print("could not connect to AP, retrying: ", e)
            continue
    print('Timeout exceeded')
    return False


def startServer():
    wsgiServer.start()


def updateServer():
    wsgiServer.update_poll()


def ip():
    return esp.pretty_ip(esp.ip_address)


def clock():
    try:
        r = requests.get('http://worldtimeapi.org/api/ip')
        time = str(r.json()['datetime'])
        r.close()
        return time[time.find('T') + 1:time.find('T') + 6]
    except Exception as e:
        print(e)


def image(url):
    requesturl = 'https://io.adafruit.com/api/v2/MaKroe/integrations/image-formatter?x-aio-key=' + secrets[
        'adafruitIo_Key'] + '&width=64&height=64&output=BMP32&url=https://coverify.makro.ca/image?url=' + url

    print(requesturl)

    r = requests.get(requesturl)

    headers = {}
    for title, content in r.headers.items():
        headers[title.lower()] = content

    remaining = int(headers["content-length"])
    with open('img.bmp', "wb") as file:
        for i in r.iter_content(min(remaining, 4096)):  # huge chunks!
            remaining -= len(i)
            file.write(i)
            print(".", end="")
            if not remaining:
                break
    r.close()
