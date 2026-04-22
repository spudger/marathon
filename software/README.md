# Software

Firmware, OS configuration, and setup scripts for Marathon.

**Status:** Phase 6, partially validated during Phase 2 (breadboard prototype). See [`../documentation/PROTOTYPE_BUILD_GUIDE.md`](../documentation/PROTOTYPE_BUILD_GUIDE.md) for the current working configuration.

Will contain:
- Final `/boot/config.txt` with SPI, I2S (`hifiberry-dac`), and HDMI framebuffer settings.
- `/etc/rc.local` with the `fbcp-ili9341` startup entry.
- `mk_arcade_joystick_rpi` module configuration (`/etc/modprobe.d/joystick.conf`, `/etc/modules`).
- EmulationStation input config (`es_input.cfg`).
- Any setup / install scripts.

Released under the MIT License when added.
