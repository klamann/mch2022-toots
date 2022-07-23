import json
import system, wifi, time, display, gc
from time import sleep, localtime
import urequests as requests
import buttons
import mch22
import re

sample_json = ""

DEBUG = True
toot_counter = 0

# a translation table for common characters that the badge has issues with (str.translate is not supported)
char_replacements = {'ä': 'ae', 'ö': 'oe', 'ü': 'ue', 'ß': 'ss', 'Ä': 'Ae', 'Ö': 'Oe', 'Ü': 'Ue'}
# some common html entities, since we don't have a full html unescape function in micropython
html_entities = {
    '&amp;': '&',
    '&quot;': '"',
    '&#39;': '\'',
    '&nbsp;': ' ',
}


def connectToWifi():
    if not wifi.status():
        wifi.connect()
        display.drawFill(display.WHITE)
        display.drawText(10, 10, "Connecting to WiFi...", 0x000000, "Roboto_Regular12")
        display.flush()
        if not wifi.wait():
            system.home()


def drawSplash():
    display.drawFill(display.WHITE)
    display.drawText(10, 10, "Getting #mch2022 toots from chaos.social ...", 0x000000, "Roboto_Regular12")
    display.flush()


def fetch_toots():
    r = requests.get("https://chaos.social/api/v1/timelines/tag/mch2022")
    gc.collect()
    data = r.json()
    r.close()
    return data



def button_exit_app(pressed):
    if pressed:
        mch22.exit_python()


def callback_next_toot(p):
    if p:
        global toot_counter
        if toot_counter >= len(data):
            toot_counter = 0
        print(f"toot #{toot_counter}")
        print_toot(data[toot_counter])
        toot_counter += 1


def isascii(c):
    return 0 <= ord(c) <= 0x7F


def print_toot(toot_json):
    content_html = toot_json['content']
    content_plain = re.sub('<br.*?>', ' ', content_html)
    content_plain = re.sub('<[^<]+?>', '', content_plain)
    content_plain = ''.join(char_replacements.get(c, c) for c in content_plain)
    content_plain = ''.join(c if isascii(c) else '?' for c in content_plain)
    if '&' in content_plain:
        for html_entity, replacement in html_entities.items():
            content_plain = content_plain.replace(html_entity, replacement)
    author = toot_json['account']['username']
    created = toot_json['created_at']

    display.drawFill(0xFFFFFF)
    #display.drawLine(0, 26, display.width(), 26, 0x000000)
    #display.drawLine(0, 44, display.width(), 44, 0x000000)
    display.drawText(5, 5, f"@{author} ({created}):", 0x000000, "pixelade13")

    line_height = 16
    chars_per_line = 45
    words = content_plain.split()
    line = ''
    lines = []
    for word in words:
        line_tmp = line + ' ' + word
        if len(line_tmp) > chars_per_line:
            lines.append(line)
            line = word
        else:
            line = line_tmp
    if (not lines) or (lines[-1] != line):
        lines.append(line)

    for i, line in enumerate(lines):
        y = 10 + ((i + 1) * line_height)
        display.drawText(5, y, line, 0x000000, "pixelade13")

    display.flush()


buttons.attach(buttons.BTN_HOME, button_exit_app)
if DEBUG:
    drawSplash()
    data = json.loads(sample_json)
else:
    connectToWifi()
    drawSplash()
    data = fetch_toots()

if not data:
    display.drawFill(display.WHITE)
    display.drawText(10, 10, "No toots received :'(", 0x000000, "Roboto_Regular12")
    display.flush()
else:
    toot = data[toot_counter]
    print_toot(toot)
    toot_counter += 1
    buttons.attach(buttons.BTN_A, callback_next_toot)
    while True:
        time.sleep(1)
