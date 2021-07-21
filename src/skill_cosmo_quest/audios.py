import urllib.parse
from typing import Dict


class VkAudio:
    def __init__(self, id):
        self.id = id

    def get_tag(self):
        return f'<speaker audio_vk_id="{self.id}">'


class UrlAudio:
    def __init__(self, id):
        self.id = id

    def get_tag(self):
        return f'<speaker audio_url="{self.id}">'


vk_audios: Dict[str, VkAudio] = {}


def get_vk(name):
    return vk_audios[name]


url_audios: Dict[str, UrlAudio] = {}

audios_tags = {}


def get_url(audio_name):
    global AUDIO_FILES_PATH
    return url_audios[audio_name]


def add_file(name, file_name):
    global AUDIO_FILES_PATH
    url_audio = UrlAudio(
        AUDIO_FILES_PATH.format(file_name=urllib.parse.quote(file_name))
    )
    url_audios[name] = url_audio


def init(audio_files_template):
    global AUDIO_FILES_PATH
    AUDIO_FILES_PATH = audio_files_template
    add_file("audio_1", "01 Do you hear me v4.mp3")
    add_file("audio_2", "02 Metronome.mp3")
    add_file("audio_3", "03 Metonome and helicopter.mp3")
    add_file("audio_4", "04 Takeoff v1.mp3")
    add_file("audio_5", "05 Superengine v3.mp3")
    add_file("audio_6", "06 Positive v2.mp3")
    add_file("audio_7", "07 Landing.mp3")
    add_file("audio_8", "08 Boarding.mp3")
    add_file("audio_9", "09 Probe multiple.mp3")
    add_file("audio_10", "10 Probe single.mp3")
    add_file("audio_11", "11 Dance Music v2.mp3")
    add_file("audio_12", "12 Engines v2.mp3")
    add_file("audio_13", "13 Shoots.mp3")
    add_file("audio_14", "14 Atmospheric drop.mp3")
    add_file("audio_15", "15 Parachute.mp3")
    add_file("audio_16", "16.1 Falling v4 (impact).mp3")
    add_file("audio_16_t", "16.2 Falling v5 (trees).mp3")
    add_file("audio_17", "17 Helicopters.mp3")
    add_file("audio_18", "18 Knocking v3.mp3")
    add_file("audio_19", "19 Hatch Opening v2.mp3")
    add_file("audio_20", "20 Welcome home.mp3")
    add_file("audio_21", "21 Alarm v2.mp3")
    add_file("audio_22", "22 Air Licking v3.mp3")
    add_file("audio_23", "23 Welding.mp3")
    add_file("audio_24", "24 Morse code v2.mp3")
    add_file("audio_25", "25 Space Suit.mp3")
    add_file("audio_26", "26 Helmet v2.mp3")
    add_file("audio_27", "27 Hatch closing.mp3")
    add_file("audio_28", "28 Carabiner.mp3")
    add_file("audio_29", "29 Mission control center speaking v2.mp3")
    add_file("audio_30", "30 Water Landing v3.mp3")

    for key, value in url_audios.items():
        audios_tags[key] = value.get_tag()
