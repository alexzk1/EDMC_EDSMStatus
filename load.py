from datetime import datetime
from playsound import playsound
from config import appname, applongname, appcmdname, appversion, copyright, config
import requests
import os
import sys
import math

try:
    # Python 2
    from urllib2 import quote
    import Tkinter as tk
    import ttk
except ModuleNotFoundError:
    # Python 3
    from urllib.parse import quote
    import tkinter as tk
    import tkinter.ttk as ttk

from ttkHyperlinkLabel import HyperlinkLabel
from typing import Optional
import myNotebook as nb
from config import config
from l10n import Locale
this = sys.modules[__name__]  # For holding module globals

# For compatibility with pre-5.0.0
if not hasattr(config, 'get_int'):
    config.get_int = config.getint

if not hasattr(config, 'get_str'):
    config.get_str = config.get

if not hasattr(config, 'get_bool'):
    config.get_bool = lambda key: bool(config.getint(key))

if not hasattr(config, 'get_list'):
    config.get_list = config.get

# This could also be returned from plugin_start3()
plugin_name = os.path.basename(os.path.dirname(__file__))

this.edsm_session = None
this.sound_value = tk.IntVar(value=100)
this.no_sound_on1st_route = tk.IntVar(value=0)
this.next_is_route = False
this.next_jump_label = None
this.frame = None
this.dist1 = None
this.dist2 = None
this.dist = None
this.coord1 = None
this.coord2 = None


def plugin_start3(plugin_dir: str) -> str:
    """
    Load this plugin into EDMC
    """

    # Retrieve saved value from config
    loadConfigValues()

    return "EDSM System Checker v2"


def plugin_stop() -> None:
    """
    EDMC is closing
    """


def makeLabelAndHyperLabel(frame, r, label_text):
    tk.Label(frame, text=label_text).grid(row=r, column=0, sticky=tk.W)
    hl = HyperlinkLabel(frame, text="", foreground="yellow", popup_copy=True)
    hl.grid(row=r, column=1, sticky=tk.W)
    return hl


def makeSeparator(frame, r):
    tk.Frame(frame, highlightthickness=1).grid(
        row=r, pady=3, columnspan=2, sticky=tk.EW)


def isStrEmpty(str):
    return "".__eq__(str)


def plugin_app(parent: tk.Frame):
    this.frame = tk.Frame(parent)
    this.frame.columnconfigure(1, weight=1)

    
    this.next_jump_label = makeLabelAndHyperLabel(this.frame, 0, "Jump to:")
    makeSeparator(this.frame, 1)

    this.dist1 = makeLabelAndHyperLabel(this.frame, 2, "Distance src:")
    this.dist2 = makeLabelAndHyperLabel(this.frame, 3, "Distance dst:")
    this.dist = makeLabelAndHyperLabel(this.frame, 4, "Distance:")

    return this.frame


def play_sound_file(file_name):
    playsound(os.path.join(os.path.dirname(
        os.path.realpath(__file__)), file_name), this.sound_value.get())


def calculateDistance(x1, y1, z1, x2, y2, z2):
    return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2 + (z1 - z2) ** 2)


def requestEdsm(system):
    # https://www.edsm.net/api-v1/system?systemName=Oochoss%20RI-B%20d13-0&showCoordinates=1&showInformation=0
    if not this.edsm_session:
        this.edsm_session = requests.Session()
    edsm_data = None
    try:
        r = this.edsm_session.get(
            'https://www.edsm.net/api-v1/system?&showCoordinates=1&showInformation=0&systemName=%s' % quote(system), timeout=10)
        r.raise_for_status()
        edsm_data = r.json() or None  # Unknown system represented as empty list
    except:
        edsm_data = None

    return edsm_data


def setLabelSystem(label, system):
    label["text"] = system
    label["url"] = "https://www.edsm.net/show-system?systemName={}".format(
        quote(system))


def isLabelSameSystem(label, system):
    t = label["text"]
    if isStrEmpty(system) or isStrEmpty(t):
        return False
    return system.__eq__(t)


def extractCoord(edsm_data):
    return edsm_data["coords"] if (edsm_data and "coords" in edsm_data) else None


def updateDistancing(system, edsm_data):
    if isStrEmpty(this.dist1["text"]):

        setLabelSystem(this.dist1, system)
        this.coord1 = extractCoord(edsm_data)
        this.dist1["foreground"] = "green" if edsm_data and this.coord1 else "yellow"

    else:
        if not isLabelSameSystem(this.dist2, system):
            if not isStrEmpty(this.dist2["text"]):
                setLabelSystem(this.dist1, this.dist2["text"])
                this.dist1["foreground"] = this.dist2["foreground"]
                this.coord1 = this.coord2

            setLabelSystem(this.dist2, system)
            this.coord2 = extractCoord(edsm_data)
            this.dist2["foreground"] = "green" if edsm_data and this.coord2 else "yellow"

    if this.coord1 and this.coord2:
        d = calculateDistance(this.coord1["x"], this.coord1["y"], this.coord1["z"],
                              this.coord2["x"], this.coord2["y"], this.coord2["z"])
        this.dist["text"] = "{:.2f} (ly)".format(d)
    else:
        this.dist["text"] = "?"


def journal_entry(cmdr, is_beta, system, station, entry, state):

    if entry['event'] == 'NavRoute':
        this.next_is_route = this.no_sound_on1st_route.get()

    if entry['event'] == 'FSDTarget':
        setLabelSystem(this.next_jump_label, entry['Name'])
        edsm_data = requestEdsm(entry['Name'])
        updateDistancing(entry['Name'], edsm_data)

        if edsm_data == None:
            this.next_jump_label["foreground"] = "yellow"
            if not this.next_is_route:
                play_sound_file("Unregistered_System.mp3")
        else:
            this.next_jump_label["foreground"] = "green"
            if not this.next_is_route:
                play_sound_file("Registered_System.mp3")

        this.next_is_route = False


def test_sound_func():
    play_sound_file("Registered_System.mp3")


def loadConfigValues():
    val = config.getint("EDMSStatus_sound_value")
    if val != 0:
        this.sound_value.set(val)
    val = config.getint("EDMSStatus_sound_1stonroute")
    this.no_sound_on1st_route.set(val)


def saveConfigValues():
    config.set("EDMSStatus_sound_value",
               this.sound_value.get())  # Store new value in config

    config.set("EDMSStatus_sound_1stonroute",
               this.no_sound_on1st_route.get())


def plugin_prefs(parent: nb.Notebook, cmdr: str, is_beta: bool) -> Optional[tk.Frame]:
    """
    Return a TK Frame for adding to the EDMC settings dialog.
    """

    frame = nb.Frame(parent)
    frame.columnconfigure(0, weight=1)

    test_snd = nb.Button(frame, text="Test Sound")
    test_snd.grid(sticky=tk.W)
    test_snd.config(command=test_sound_func)

    scale = tk.Scale(frame, from_=1, to=150, variable=this.sound_value,
                     length=250, showvalue=1, label="Sound Volume", orient=tk.HORIZONTAL)
    scale.set(this.sound_value.get())
    scale.grid(sticky=tk.W)

    nb.Checkbutton(frame, text="No Sound on 1st In Route",
                   variable=this.no_sound_on1st_route).grid(sticky=tk.W)

    # Retrieve saved value from config
    loadConfigValues()

    return frame


def prefs_changed(cmdr: str, is_beta: bool) -> None:
    """
    Save settings.
    """
    saveConfigValues()
