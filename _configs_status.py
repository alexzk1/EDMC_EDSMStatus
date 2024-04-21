import collections
import json
import logging
import tkinter as tk

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


class ConfigVars:
    __TJsonFieldMapper = collections.namedtuple(
        "__TJsonFieldMapper", "json_name field_ref"
    )
    __json_config_name: str = "edmc_edsm_status_json"

    iOverlay = None

    # Simple config fields
    iXPos: tk.IntVar = tk.IntVar(value=150)
    iYPos: tk.IntVar = tk.IntVar(value=100)
    iEdsmTimeoutSeconds: tk.IntVar = tk.IntVar(value=10)
    iNoReportOnFirst: tk.BooleanVar = tk.BooleanVar(value=False)
    iSoundVolume: tk.IntVar = tk.IntVar(value=100)
    iDebug: tk.BooleanVar = tk.BooleanVar(value=False)
    iEnableOverlay: tk.BooleanVar = tk.BooleanVar(value=True)
    _iNoSoundOverlay: tk.BooleanVar = tk.BooleanVar(value=False)
    _iOverlayFadeSeconds: tk.IntVar = tk.IntVar(value=8)

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
            gb.TTextAndInputRow(
                "No report on 1st star in new route", self.iNoReportOnFirst, False
            ),
            gb.TTextAndInputRow(
                "EDSM Timeout (seconds)", self.iEdsmTimeoutSeconds, False
            ),
            gb.TTextAndInputRow("Sound Volume", self.iSoundVolume, True),
            gb.TTextAndInputRow("", None, False),
            gb.TTextAndInputRow("Debug", self.iDebug, False),
        ]

        listOverlay: list[gb.TTextAndInputRow] = []
        if self.iOverlay:
            listOverlay = [
                gb.TTextAndInputRow("Overlay Configuration:", None, False),
                gb.TTextAndInputRow("Enable Overlay", self.iEnableOverlay, False),
                gb.TTextAndInputRow("Text Without Sound", self._iNoSoundOverlay, False),
                gb.TTextAndInputRow("Text X Position", self.iXPos, False),
                gb.TTextAndInputRow("Text Y Position", self.iYPos, False),
                gb.TTextAndInputRow(
                    "Text Fadeout (seconds)", self._iOverlayFadeSeconds, False
                ),
            ]

        return listThisPlugin + listOverlay

    def showTextOnOverlay(self, text: str, color: str):
        if self.iOverlay and self.iEnableOverlay.get() and self.iOverlay.connect():
            self.iOverlay.send_message(
                "is_visited_star",
                text,
                color,
                self.iXPos.get(),
                self.iYPos.get(),
                min(60, max(1, self._iOverlayFadeSeconds.get())),
                "normal",
            )

    def isMuted(self) -> bool:
        return self.iOverlay and self._iNoSoundOverlay.get()
