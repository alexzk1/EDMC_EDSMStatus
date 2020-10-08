from datetime import datetime
from playsound import playsound
from config import appname, applongname, appcmdname, appversion, copyright, config
import requests
import os
import sys

try:
    # Python 2
    from urllib2 import quote
    import Tkinter as tk
except ModuleNotFoundError:
    # Python 3
    from urllib.parse import quote
    import tkinter as tk

from ttkHyperlinkLabel import HyperlinkLabel
from typing import Optional
import myNotebook as nb
from config import config
from l10n import Locale
from tkinter import *


this = sys.modules[__name__]  # For holding module globals
this.edsm_session = None
this.edsm_data = None
this.sound_value = IntVar(value=100)
this.next_is_route = False


def plugin_start3(plugin_dir: str) -> str:
    """
    Load this plugin into EDMC
    """
    return "EDSM System Checker v2"


def plugin_stop() -> None:
    """
    EDMC is closing
    """


def play_sound_file(file_name):
    playsound(os.path.join(os.path.dirname(
        os.path.realpath(__file__)), file_name), this.sound_value.get())


def journal_entry(cmdr, is_beta, system, station, entry, state):

    if entry['event'] == 'NavRoute':
        this.next_is_route = True

    if entry['event'] == 'FSDTarget':
        if not this.next_is_route:
            if not this.edsm_session:
                this.edsm_session = requests.Session()

            try:
                r = this.edsm_session.get(
                    'https://www.edsm.net/api-system-v1/bodies?systemName=%s' % quote(entry['Name']), timeout=10)
                r.raise_for_status()
                this.edsm_data = r.json() or None  # Unknown system represented as empty list
            except:
                this.edsm_data = None

            if this.edsm_data == '[]' or this.edsm_data == None:
                play_sound_file("Unregistered_System.mp3")
            else:
                play_sound_file("Registered_System.mp3")
        this.next_is_route = False


def test_sound_func():
    play_sound_file("Registered_System.mp3")


def loadSoundValue():
    val = config.getint("EDMSStatus_sound_value")
    if val != 0:
        this.sound_value.set(val)


def saveSoundValue():
    config.set("EDMSStatus_sound_value",
               this.sound_value.get())  # Store new value in config


def plugin_prefs(parent: nb.Notebook, cmdr: str, is_beta: bool) -> Optional[tk.Frame]:
    """
    Return a TK Frame for adding to the EDMC settings dialog.
    """

    # Retrieve saved value from config
    loadSoundValue()

    frame = nb.Frame(parent)
    test_snd = nb.Button(frame, text="Test Sound")
    test_snd.grid()
    test_snd.config(command=test_sound_func)

    scale = Scale(frame, from_=1, to=150, variable=this.sound_value,
                  length=250, showvalue=1, label="Sound Volume", orient=HORIZONTAL)
    scale.set(this.sound_value.get())
    scale.grid()

    return frame


def prefs_changed(cmdr: str, is_beta: bool) -> None:
    """
    Save settings.
    """
    saveSoundValue()
