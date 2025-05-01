# EDMC_EDSMStatus

EDMC plugin that checks if a selected system has been uploaded to EDSM yet.

When in game open either the Galaxy map or the navigation window and select a system and lock onto it. You don't need to be able to jump to it. This tool will check if that system has been uploaded to EDSM yet and give you and audio cue if it has already been uploaded, "Dicovered", or has not been uploaded yet, "New System".

# Updates by alexzk version:

* What it do, when you select system on map it talks (plays mp3 there) if your current selection is known for EDSM. Also it is shown in "Jump to".
I added automatic distancing. If you click 2 stars on galaxy map and both are known to edsm it will calculate distance and show there.
So cool tool to measure of farmost sides.
* Now it can use `EDSMOverlay` to display information too.
* If `EDSMOverlay` is detected, sound can be disabled.
* Now it can show just docked station's economics list on overlay. It is usable with construction update.

When I say "click" I mean "select as jump target".

Also on Linux you can regulate volume in settings. Did not implement on win/mac as I don't have them.
