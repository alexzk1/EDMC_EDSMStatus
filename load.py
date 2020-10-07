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

this = sys.modules[__name__]  # For holding module globals
this.edsm_session = None
this.edsm_data = None


def plugin_start3(plugin_dir: str) -> str:
    """
    Load this plugin into EDMC
    """
    return "EDSM System Checker Python 3.x"


def plugin_stop() -> None:
    """
    EDMC is closing
    """


def journal_entry(cmdr, is_beta, system, station, entry, state):
    if entry['event'] == 'FSDTarget':
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
            #print("We didn't find:" + entry['Name'])
            # LogUnregisteredSystem(entry['Name'])
            playsound(os.path.join(os.path.dirname(
                os.path.realpath(__file__)), "Unregistered_System.mp3"))
        else:
            print("We found:" + entry['Name'])
            playsound(os.path.join(os.path.dirname(
                os.path.realpath(__file__)), "Registered_System.mp3"))
