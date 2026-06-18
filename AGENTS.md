# Agent Instructions for EDMC_EDSMStatus

This repository is an Elite Dangerous Market Connector (EDMC) plugin that provides audio cues and on-screen information regarding whether a selected system has been uploaded to EDSM.

## Critical Context
* **Environment Dependency**: This code depends heavily on the EDMC framework environment, specifically the modules `myNotebook` and `config`. Running or testing these files in isolation will fail unless these modules are available in the `PYTHONPATH`.
* **Main Entry Point**: The primary logic for the plugin (journal event handling and UI initialization) is located in `load.py`.

## Key Components
* **Core Logic (`load.py`)**: Handles EDMC journal events (`FSDTarget`, `Docked`, etc.), interacts with the EDSM API, calculates distances between systems, and manages audio cues/UI updates.
* **Configuration (`_configs_status.py`)**: Manages plugin settings (position, timeout, volume, etc.) via a JSON configuration stored under the key `edmc_edsm_status_json` through the `config` module.
* **GUI & Overlay (`_gui_builder_status.py`, `load.py`)**: Uses `tkinter` for the main settings window and has optional support for an on-screen overlay if `EDMCOverlay` or `edmcoverlay` is detected in the environment.

## Technical Details
* **API Usage**: Fetches system data from `https://www.edsm.net/api-v1/system?`.
* **Audio Cues**: Uses the `playsound` library to play `.mp3` files (`Registered_System.mp3`, `Unregistered_System.mp3`) based on EDSM status.
* **Event Flow**: The plugin listens for `FSDTarget` events to trigger system checks and `Docked` events to show station economy information via an overlay.