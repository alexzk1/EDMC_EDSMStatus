import sys
import collections
import tkinter as tk
from tkinter import ttk

import myNotebook as nb

__PAD_X: int = 10
__PAD_Y: int = 2

TTextAndInputRow = collections.namedtuple(
    "TTextAndInputRow", "iColCaption iColVariable iMakePercentsScroll"
)
"""Defines 2 slots on the 1 raw. Left slot (iColCaption) can be text or any object from myNotebook.py. 
If it is object, it will be just assigned to the grid. 
Right slot (iColVariable) can be variable, None or input control like Button. Entry field is created for it."""


class Scale(sys.platform == "darwin" and tk.Scale or ttk.Scale):  # type: ignore
    """Custom t(t)k.Scale class to fix some display issues."""

    def __init__(self, master: ttk.Frame | None = None, **kw):
        if sys.platform == "darwin":
            kw["foreground"] = kw.pop("foreground", nb.PAGEFG)
            kw["background"] = kw.pop("background", nb.PAGEBG)
            tk.Scale.__init__(self, master, **kw)
        elif sys.platform == "win32":
            ttk.Scale.__init__(self, master, **kw)
        else:
            ttk.Scale.__init__(self, master, **kw)


def MakeGuiTable(parent, defines: list[TTextAndInputRow], initialRaw: int):
    """Processes list of TTextAndInputRow and assigns it to the grid.
    Entries are created for right slots and text Labels for the left texts."""  # noqa: E999

    for item in defines:
        missSecond = item.iColVariable is None

        if isinstance(item.iColCaption, (str)):
            if missSecond:
                nb.Label(parent, text=item.iColCaption).grid(
                    row=initialRaw,
                    column=0,
                    padx=__PAD_X,
                    pady=(__PAD_Y, 0),
                    sticky=tk.W,
                    columnspan=3,
                )
            else:
                nb.Label(parent, text=item.iColCaption).grid(
                    row=initialRaw,
                    column=0,
                    padx=__PAD_X,
                    pady=(__PAD_Y, 0),
                    sticky=tk.E,
                )
        else:
            if missSecond:
                item.iColCaption.grid(
                    row=initialRaw,
                    column=0,
                    padx=__PAD_X,
                    pady=(__PAD_Y, 0),
                    sticky=tk.W,
                    columnspan=3,
                )
            else:
                item.iColCaption.grid(
                    row=initialRaw,
                    column=0,
                    padx=__PAD_X,
                    pady=(__PAD_Y, 0),
                    sticky=tk.E,
                )

        if not missSecond:
            isSecondVar = isinstance(
                item.iColVariable,
                (tk.DoubleVar, tk.IntVar, tk.StringVar, tk.BooleanVar, tk.Variable),
            )
            if isSecondVar:
                if isinstance(item.iColVariable, (tk.BooleanVar)):
                    nb.Checkbutton(parent, variable=item.iColVariable).grid(
                        row=initialRaw,
                        column=1,
                        columnspan=3,
                        padx=(0, __PAD_X),
                        pady=__PAD_Y,
                        sticky=tk.W,
                    )
                else:
                    if (
                        isinstance(item.iColVariable, tk.IntVar)
                        and item.iMakePercentsScroll
                    ):
                        Scale(
                            parent,
                            from_=1,
                            to=150,
                            variable=item.iColVariable,
                            orient=tk.HORIZONTAL,
                        ).grid(
                            row=initialRaw,
                            column=1,
                            columnspan=3,
                            padx=(0, __PAD_X),
                            pady=__PAD_Y,
                            sticky=tk.W,
                        )
                    else:
                        nb.Entry(parent, textvariable=item.iColVariable).grid(
                            row=initialRaw,
                            column=1,
                            columnspan=3,
                            padx=(0, __PAD_X),
                            pady=__PAD_Y,
                            sticky=tk.W,
                        )
            else:
                item.iColVariable.grid(
                    row=initialRaw,
                    column=1,
                    columnspan=3,
                    padx=(0, __PAD_X),
                    pady=__PAD_Y,
                    sticky=tk.W,
                )
        initialRaw += 1


def AddMainSeparator(frame):
    ttk.Separator(frame, orient=tk.HORIZONTAL).grid(
        padx=__PAD_X, pady=2 * __PAD_Y, sticky=tk.EW
    )
