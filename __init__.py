import gc
import json
import re
import time

import buttons
import display
import mch22
import system
import urequests as requests
import wifi

sample_json = ""

# mastadon api response and current selection
toots = []
toot_index = 0
# a translation table for common characters that the badge has issues with (str.translate is not supported)
char_replacements = {'ä': 'ae', 'ö': 'oe', 'ü': 'ue', 'ß': 'ss', 'Ä': 'Ae', 'Ö': 'Oe', 'Ü': 'Ue'}
# some common html entities, since we don't have a full html unescape function in micropython
html_entities = {
    '&amp;': '&',
    '&quot;': '"',
    '&#39;': '\'',
    '&nbsp;': ' ',
}
# font stuff
font = 'Roboto_Regular12'
font_height = display.getTextHeight("Happy", font)
max_text_width = display.width() - 10
line_margin = 3


def wlan_connect():
    if not wifi.status():
        wifi.connect()
        display.drawFill(display.WHITE)
        display.drawText(10, 10, "Connecting to WiFi...", 0x000000, font)
        display.flush()
        if not wifi.wait(10):
            display.drawFill(display.WHITE)
            display.drawText(10, 10, "Sorry, WiFi connection failed :(", 0x000000, font)
            display.drawText(10, 25, "Try getting closer to the next Datenklo and", 0x000000, font)
            display.drawText(10, 40, "avoid blocking the WiFi chip with the battery.", 0x000000, font)
            display.drawText(10, 65, "Exit with HOME button", 0x000000, font)
            display.flush()
            while True:
                time.sleep(1)
        else:
            print("connected!")


def draw_splash():
    display.drawFill(display.WHITE)
    display.drawText(10, 10, "Getting #mch2022 toots from chaos.social ...", 0x000000, font)
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
        switch_toot(toot_index + 1)


def callback_prev_toot(p):
    if p:
        switch_toot(toot_index - 1)


def switch_toot(index):
    if index >= len(toots):
        index = 0
    if index < 0:
        index = len(toots) - 1
    print(f"toot #{index}")
    global toot_index
    toot_index = index
    print_toot(toots[index])


def print_toot(toot_json):
    # get content
    content_html = toot_json['content']
    content_plain = simplify_text(content_html)
    author = toot_json['account']['username']
    created = toot_json['created_at']
    # author & date
    display.drawFill(0xFFFFFF)
    display.drawText(5, 5, f"{toot_index + 1}/{len(toots)}: @{author}, {created}:", 0x000000, font)
    # print content lines
    lines = text_to_lines(content_plain)
    for i, line in enumerate(lines):
        y = 10 + ((i + 1) * (font_height + line_margin))
        display.drawText(5, y, line, 0x000000, font)
    display.flush()


def simplify_text(text):
    # strip html tags
    plain = re.sub('<br.*?>', ' ', text)
    plain = re.sub('<[^<]+?>', '', plain)
    # replace non-ascii chars (not supported by badge)
    plain = ''.join(char_replacements.get(c, c) for c in plain)
    plain = ''.join(c if isascii(c) else '?' for c in plain)
    # replace common html entities
    if '&' in plain:
        for html_entity, replacement in html_entities.items():
            plain = plain.replace(html_entity, replacement)
    return plain


def text_to_lines(text):
    words = text.split()
    line = ''
    lines = []
    for word in words:
        line_tmp = line + ' ' + word
        line_width = display.getTextWidth(line_tmp, font)
        if line_width > max_text_width:
            lines.append(line)
            line = word
        else:
            line = line_tmp
    if (not lines) or (lines[-1] != line):
        lines.append(line)
    return lines


def isascii(c):
    return 0 <= ord(c) <= 0x7F


def main(debug=False):
    global toots
    buttons.attach(buttons.BTN_HOME, button_exit_app)
    if debug:
        draw_splash()
        toots = json.loads(sample_json)
    else:
        wlan_connect()
        draw_splash()
        toots = fetch_toots()

    if not toots:
        display.drawFill(display.WHITE)
        display.drawText(10, 10, "No toots received :'(", 0x000000, font)
        display.flush()
    else:
        print_toot(toots[0])
        buttons.attach(buttons.BTN_A, callback_next_toot)
        buttons.attach(buttons.BTN_UP, callback_prev_toot)
        buttons.attach(buttons.BTN_DOWN, callback_next_toot)
        buttons.attach(buttons.BTN_LEFT, callback_prev_toot)
        buttons.attach(buttons.BTN_RIGHT, callback_next_toot)
        while True:
            time.sleep(1)


main(debug=False)
