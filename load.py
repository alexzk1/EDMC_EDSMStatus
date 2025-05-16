import math
import os
import sys
import tkinter as tk
from datetime import datetime
from typing import Optional
from urllib.parse import quote

import myNotebook as nb
import requests
from ttkHyperlinkLabel import HyperlinkLabel

import _configs_status as cfv
import _gui_builder_status as gb
from _logger import logger
from playsound import playsound

__configVars: cfv.ConfigVars = cfv.ConfigVars()

this = sys.modules[__name__]  # For holding module globals

this.edsm_session = None
this.next_is_route = False
this.next_jump_label = None
this.frame = None
this.dist1 = None
this.dist2 = None
this.dist = None
this.dist_overlay: str = ""

this.coord1 = None
this.coord2 = None

__registeredColor: str = "green"
__unregisteredColor: str = "yellow"

__station_economy_color: str = "#DDFFB450"

__CaptionText = "EDSM System Checker With Overlay"
__ShortCaptionText = "EDSM Checker"


def __makeLabelAndHyperLabelOnMainPage(frame, r, label_text):
    tk.Label(frame, text=label_text).grid(row=r, column=0, sticky=tk.W)
    hl = HyperlinkLabel(frame, text="", foreground="yellow", popup_copy=True)
    hl.grid(row=r, column=1, sticky=tk.W)
    return hl


def __isStrEmpty(str):
    return "".__eq__(str)


def __play_sound_file(file_name):
    global __configVars
    if not __configVars.isMuted():
        playsound(
            os.path.join(os.path.dirname(os.path.realpath(__file__)), file_name),
            __configVars.iSoundVolume.get(),
        )


def __calculateDistance(x1, y1, z1, x2, y2, z2):
    return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2 + (z1 - z2) ** 2)


def __requestEdsm(system):
    global __configVars

    # https://www.edsm.net/api-v1/system?systemName=Oochoss%20RI-B%20d13-0&showCoordinates=1&showInformation=0
    if not this.edsm_session:
        this.edsm_session = requests.Session()
    edsm_data = None
    try:
        response = this.edsm_session.get(
            "https://www.edsm.net/api-v1/system?&showCoordinates=1&showInformation=0&systemName=%s"
            % quote(system),
            timeout=min(90, max(3, __configVars.iEdsmTimeoutSeconds.get())),
        )
        response.raise_for_status()
        edsm_data = response.json() or None  # Unknown system represented as empty list
    except:  # noqa: E722
        edsm_data = None

    return edsm_data


def __setLabelSystem(label, system):
    label["text"] = system
    label["url"] = "https://www.edsm.net/show-system?systemName={}".format(
        quote(system)
    )


def __isLabelSameSystem(label, system):
    t = label["text"]
    if __isStrEmpty(system) or __isStrEmpty(t):
        return False
    return system.__eq__(t)


def __extractCoord(edsm_data):
    return edsm_data["coords"] if (edsm_data and "coords" in edsm_data) else None


def __updateDistancing(system, edsm_data):
    global __registeredColor
    global __unregisteredColor

    if __isStrEmpty(this.dist1["text"]):
        __setLabelSystem(this.dist1, system)
        this.coord1 = __extractCoord(edsm_data)
        this.dist1["foreground"] = (
            __registeredColor if edsm_data and this.coord1 else __unregisteredColor
        )

    else:
        if not __isLabelSameSystem(this.dist2, system):
            if not __isStrEmpty(this.dist2["text"]):
                __setLabelSystem(this.dist1, this.dist2["text"])
                this.dist1["foreground"] = this.dist2["foreground"]
                this.coord1 = this.coord2

            __setLabelSystem(this.dist2, system)
            this.coord2 = __extractCoord(edsm_data)
            this.dist2["foreground"] = (
                __registeredColor if edsm_data and this.coord2 else __unregisteredColor
            )

    if this.coord1 and this.coord2:
        d = __calculateDistance(
            this.coord1["x"],
            this.coord1["y"],
            this.coord1["z"],
            this.coord2["x"],
            this.coord2["y"],
            this.coord2["z"],
        )
        this.dist_overlay = "{:.2f} (ly)".format(d)
        this.dist["text"] = this.dist_overlay
    else:
        this.dist_overlay = ""
        this.dist["text"] = "?"


def __uknownSystem(system: str):
    global __configVars
    global __unregisteredColor
    __configVars.showTextOnOverlay(
        "EDSM does not know {}".format(system), __unregisteredColor
    )
    __play_sound_file("Unregistered_System.mp3")


def __visitedSystem(system: str):
    global __configVars
    global __unregisteredColor

    if not this.dist_overlay:
        __configVars.showTextOnOverlay(
            "EDSM knows {}".format(system), __registeredColor
        )
    else:
        __configVars.showTextOnOverlay(
            "EDSM knows {}.{}Distance between last 2 selected: {}".format(
                system,
                "\n\t" if __configVars.iOverlayHasMultiline else " ",
                this.dist_overlay,
            ),
            __registeredColor,
        )
    __play_sound_file("Registered_System.mp3")


def __display_economy_type_on_overlay(entry):
    if __configVars.iReportDockedEconomyOnOverlay.get():
        station_economies = entry.get("StationEconomies", [])
        main_economy_localised = entry.get("StationEconomy_Localised")
        lines = [
            f"{'* ' if eco.get('Name_Localised') == main_economy_localised else '  '}"
            f"{eco.get('Name_Localised', 'Unknown Economy')}: {eco.get('Proportion', 0.0):.1%}"
            for eco in station_economies
        ]
        has_main = any(
            eco.get("Name_Localised") == main_economy_localised
            for eco in station_economies
        )
        if not has_main and main_economy_localised:
            lines.append(f"(Economy '{main_economy_localised}' is not found in list.)")
        __configVars.showTextOnOverlay(
            text="\n".join(lines)
            if __configVars.iOverlayHasMultiline
            else "; ".join(lines),
            color=__station_economy_color,
            messageType=cfv.OverlayOutputType.STATION_INFO,
        )


def journal_entry(cmdr, is_beta, system, station, entry, state):
    global __registeredColor
    global __unregisteredColor
    global __configVars

    if entry["event"] == "NavRoute":
        this.next_is_route = __configVars.iNoReportOnFirst.get()

    if entry["event"] == "FSDTarget":
        systemName: str = entry["Name"]

        __setLabelSystem(this.next_jump_label, systemName)
        edsm_data = __requestEdsm(systemName)
        __updateDistancing(systemName, edsm_data)

        if edsm_data is None:
            this.next_jump_label["foreground"] = __unregisteredColor
            if not this.next_is_route:
                __uknownSystem(systemName)
        else:
            this.next_jump_label["foreground"] = __registeredColor
            if not this.next_is_route:
                __visitedSystem(systemName)
        this.next_is_route = False

    if entry["event"] == "Docked":
        __display_economy_type_on_overlay(entry)


def plugin_start3(plugin_dir: str) -> str:
    global __configVars
    global __ShortCaptionText

    __configVars.loadFromSettings()
    return __ShortCaptionText


def plugin_stop() -> None:
    """
    EDMC is closing
    """


def plugin_app(parent: tk.Frame):
    this.frame = tk.Frame(parent)
    this.frame.columnconfigure(1, weight=1)

    this.next_jump_label = __makeLabelAndHyperLabelOnMainPage(this.frame, 0, "Jump to:")
    # __makeSeparatorOnMainPage(this.frame, 1)

    this.dist1 = __makeLabelAndHyperLabelOnMainPage(this.frame, 2, "EDSM Distance Src:")
    this.dist2 = __makeLabelAndHyperLabelOnMainPage(this.frame, 3, "EDSM Distance Dst:")
    this.dist = __makeLabelAndHyperLabelOnMainPage(
        this.frame, 4, "EDSM Distance Src<->Dst:"
    )

    return this.frame


def prefs_changed(cmdr: str, is_beta: bool) -> None:
    """
    Save settings.
    """
    global __configVars
    __configVars.saveToSettings()


def plugin_prefs(parent: nb.Notebook, cmdr: str, is_beta: bool) -> Optional[tk.Frame]:
    """
    Return a TK Frame for adding to the EDMC settings dialog.
    """
    global __configVars

    mainFrame = nb.Frame(parent)
    mainFrame.columnconfigure(0, weight=1)

    linkFrame = nb.Frame(mainFrame)
    declareLink = [
        gb.TTextAndInputRow(
            HyperlinkLabel(
                linkFrame,
                text=__CaptionText,
                url="https://github.com/alexzk1/EDMC_EDSMStatus",
                background=nb.Label().cget("background"),
                underline=True,
            ),
            None,
            False,
        ),
        gb.TTextAndInputRow("by Steven Bjerke, Oleksiy Zakharov", None, False),
    ]
    gb.MakeGuiTable(parent=linkFrame, defines=declareLink, initialRaw=0)
    linkFrame.grid(sticky=tk.EW)

    gb.AddMainSeparator(mainFrame)

    inputsFrame = nb.Frame(mainFrame)
    gb.MakeGuiTable(
        parent=inputsFrame, defines=__configVars.getVisualInputs(), initialRaw=0
    )
    inputsFrame.grid(sticky=tk.EW)

    gb.AddMainSeparator(mainFrame)

    testFrame = nb.Frame(mainFrame)
    declareButtons = [
        gb.TTextAndInputRow("", None, False),
        gb.TTextAndInputRow(
            nb.Button(
                testFrame,
                text="Test Known",
                command=lambda: __visitedSystem("TestSystemName"),
            ),
            nb.Button(
                testFrame,
                text="Test Unknown",
                command=lambda: __uknownSystem("TestSystemName"),
            ),
            False,
        ),
    ]
    gb.MakeGuiTable(parent=testFrame, defines=declareButtons, initialRaw=0)
    testFrame.grid(sticky=tk.EW)

    gb.AddMainSeparator(mainFrame)

    return mainFrame
