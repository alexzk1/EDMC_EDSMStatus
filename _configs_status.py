import collections
import json
import logging
import tkinter as tk
from enum import Enum
from config import config

import myNotebook as nb
import _gui_builder_status as gb
import _logger as lgr
from _logger import logger

try:
    from EDMCOverlay import edmcoverlay
except ImportError:
    try:
        from edmcoverlay import edmcoverlay
    except ImportError:
        edmcoverlay = None


class OverlayOutputType(Enum):
    EDSM_INFO = (1,)
    STATION_INFO = (2,)


class ConfigVars:
    __TJsonFieldMapper = collections.namedtuple(
        "__TJsonFieldMapper", "json_name field_ref"
    )
    __json_config_name: str = "edmc_edsm_status_json"
    __kMaximimumSecondsToShowMessage = 90

    iOverlay = None

    # Simple config fields
    iXPos: tk.IntVar = tk.IntVar(value=150)
    iYPos: tk.IntVar = tk.IntVar(value=100)
    iEdsmTimeoutSeconds: tk.IntVar = tk.IntVar(value=10)
    iNoReportOnFirst: tk.BooleanVar = tk.BooleanVar(value=False)
    iSoundVolume: tk.IntVar = tk.IntVar(value=100)
    iDebug: tk.BooleanVar = tk.BooleanVar(value=False)
    iReportDockedEconomyOnOverlay: tk.BooleanVar = tk.BooleanVar(value=True)
    iEnableOverlay: tk.BooleanVar = tk.BooleanVar(value=True)
    _iNoSoundOverlay: tk.BooleanVar = tk.BooleanVar(value=False)
    _iOverlayFadeSeconds: tk.IntVar = tk.IntVar(value=8)
    _iStationOverlayFadeSeconds: tk.IntVar = tk.IntVar(value=20)

    def __init__(self) -> None:
        self.iDebug.trace_add("write", self.__debug_switched)
        if edmcoverlay:
            self.iOverlay = edmcoverlay.Overlay()

    # This must be in sync with declared fields.
    def __getJson2FieldMapper(self):
        return [
            self.__TJsonFieldMapper("xpos", self.iXPos),
            self.__TJsonFieldMapper("ypos", self.iYPos),
            self.__TJsonFieldMapper("edsmtimeout", self.iEdsmTimeoutSeconds),
            self.__TJsonFieldMapper("noreporton1st", self.iNoReportOnFirst),
            self.__TJsonFieldMapper("soundvolume", self.iSoundVolume),
            self.__TJsonFieldMapper("debug", self.iDebug),
            self.__TJsonFieldMapper("enable_overlay", self.iEnableOverlay),
            self.__TJsonFieldMapper("nosoundoverlay", self._iNoSoundOverlay),
            self.__TJsonFieldMapper("iOverlayFadeSeconds", self._iOverlayFadeSeconds),
            self.__TJsonFieldMapper(
                "iStationOverlayFadeSeconds", self._iStationOverlayFadeSeconds
            ),
            self.__TJsonFieldMapper(
                "iReportDockedEconomyOnOverlay", self.iReportDockedEconomyOnOverlay
            ),
        ]

    def __debug_switched(self, var, index, mode):
        # Debug switch changes output in log.
        if self.iDebug.get():
            logger.setLevel(logging.DEBUG)
        else:
            logger.setLevel(lgr.DEFAULT_LOG_LEVEL)
        logger.info("Set loglevel to: %i", logger.level)

    def loadFromSettings(self):
        """Loads stored settings."""

        loaded_str = config.get_str(self.__json_config_name)
        if loaded_str is not None:
            obj = json.loads(loaded_str)
            for m in self.__getJson2FieldMapper():
                if m.json_name in obj:
                    if isinstance(obj[m.json_name], dict):
                        for k in obj[m.json_name]:
                            m.field_ref[k].set(obj[m.json_name][k])
                    else:
                        m.field_ref.set(obj[m.json_name])
        self.__debug_switched("", 0, "")

    def saveToSettings(self):
        """Saves variables to settings. Returns True if binary must be reloaded."""

        # Building python's dictionary which will be dumped to the single json.
        output = {}
        for var in self.__getJson2FieldMapper():
            if isinstance(var.field_ref, dict):
                d = {}
                for k in var.field_ref:
                    d[k] = var.field_ref[k].get()
                output[var.json_name] = d
            else:
                output[var.json_name] = var.field_ref.get()
        config.set(self.__json_config_name, json.dumps(output, separators=(",", ":")))

    def getVisualInputs(self):
        listThisPlugin: list[gb.TTextAndInputRow] = [
            gb.TTextAndInputRow("Debug", self.iDebug, False),
            gb.TTextAndInputRow(
                "No report on 1st star in new route", self.iNoReportOnFirst, False
            ),
            gb.TTextAndInputRow(
                "EDSM Timeout (seconds)", self.iEdsmTimeoutSeconds, False
            ),
            gb.TTextAndInputRow("Sound Volume", self.iSoundVolume, True),
        ]

        listOverlay: list[gb.TTextAndInputRow] = []
        stationOverlay: list[gb.TTextAndInputRow] = []

        if self.iOverlay:
            listOverlay = [
                gb.TTextAndInputRow("Overlay Configuration:", None, False),
                gb.TTextAndInputRow("Enable Overlay ", self.iEnableOverlay, False),
                gb.TTextAndInputRow("Text Without Sound", self._iNoSoundOverlay, False),
                gb.TTextAndInputRow("Text X Position", self.iXPos, False),
                gb.TTextAndInputRow("Text Y Position", self.iYPos, False),
                gb.TTextAndInputRow(
                    "Text Fadeout (seconds)", self._iOverlayFadeSeconds, False
                ),
            ]
            stationOverlay = [
                gb.TTextAndInputRow("Docked Station on Overlay:", None, False),
                gb.TTextAndInputRow("(overlay should be enabled above)", None, False),
                gb.TTextAndInputRow(
                    "Show Station Economy On Docking",
                    self.iReportDockedEconomyOnOverlay,
                    True,
                ),
                gb.TTextAndInputRow(
                    "Station Info Fadeout (seconds)",
                    self._iStationOverlayFadeSeconds,
                    False,
                ),
            ]

        return listThisPlugin + listOverlay + stationOverlay

    def showTextOnOverlay(
        self,
        text: str,
        color: str,
        messageType: OverlayOutputType = OverlayOutputType.EDSM_INFO,
    ):
        if self.iOverlay and self.iEnableOverlay.get() and self.iOverlay.connect():
            self.iOverlay.send_message(
                "EdsmStatusMessage",
                text,
                color,
                self.iXPos.get(),
                self.iYPos.get(),
                min(
                    self.__kMaximimumSecondsToShowMessage,
                    max(1, self.getTextPause(messageType)),
                ),
                "normal",
            )

    def isMuted(self) -> bool:
        return self.iOverlay and self._iNoSoundOverlay.get()

    def getTextPause(self, forType: OverlayOutputType):
        if forType == OverlayOutputType.STATION_INFO:
            return self._iStationOverlayFadeSeconds.get()
        return self._iOverlayFadeSeconds.get()
