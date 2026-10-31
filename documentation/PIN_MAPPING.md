# Marathon - Complete Pin Mapping Reference

## Overview

Complete GPIO pin mapping for the Marathon handheld. The Pi Zero 2W's 40-pin GPIO header is the central hub -- every subsystem (display, audio, buttons, power) connects through it.

---

## 1. Full 40-Pin Header Mapping

The Pi Zero 2 W uses the standard Raspberry Pi 40-pin GPIO header. Below maps each
physical pin to its GPIO number, the signal name, and what it connects to.

### Left Side (Odd Pins)

| Phys Pin | Pi Function     | GPIO | Signal | Subsystem | Destination               |
|----------|-----------------|------|---------------|-----------|---------------------------|
| 1        | 3V3 Power       | -    | 3V3           | Power     | Display VCC, DAC VCC      |
| 3        | GPIO2 (SDA1)    | 2    | (unused)      | -         | -                         |
| 5        | GPIO3 (SCL1)    | 3    | (unused)      | -         | -                         |
| 7        | GPIO4 (GCLK)    | 4    | LEFT          | Buttons   | D-pad Left (active low)   |
| 9        | GND             | -    | (GND)         | Power     | Ground                    |
| 11       | GPIO17 (GEN0)   | 17   | RIGHT         | Buttons   | D-pad Right (active low)  |
| 13       | GPIO27 (GEN2)   | 27   | L             | Buttons   | Left shoulder button      |
| 15       | GPIO22 (GEN3)   | 22   | Y             | Buttons   | Y button (active low)     |
| 17       | 3V3 Power       | -    | (3V3)         | Power     | 3.3V rail (second pin)    |
| 19       | GPIO10 (MOSI)   | 10   | SDI           | Display   | ILI9341 SPI data in       |
| 21       | GPIO9 (MISO)    | 9    | SDO           | Display   | ILI9341 SPI data out      |
| 23       | GPIO11 (SCLK)   | 11   | SCL           | Display   | ILI9341 SPI clock         |
| 25       | GND             | -    | (GND)         | Power     | Ground                    |
| 27       | ID_SD           | 0    | (reserved)    | -         | HAT EEPROM; do not use    |
| 29       | GPIO5           | 5    | R             | Buttons   | Right shoulder button     |
| 31       | GPIO6           | 6    | X             | Buttons   | X button (active low)     |
| 33       | GPIO13          | 13   | (unused)      | -         | -                         |
| 35       | GPIO19          | 19   | LCK           | Audio     | I2S word clock (LRCK)     |
| 37       | GPIO26          | 26   | START         | Buttons   | Start button              |
| 39       | GND             | -    | (GND)         | Power     | Ground                    |

### Right Side (Even Pins)

| Phys Pin | Pi Function     | GPIO | Signal | Subsystem | Destination               |
|----------|-----------------|------|---------------|-----------|---------------------------|
| 2        | 5V Power        | -    | 5V            | Power     | Main 5V rail from battery |
| 4        | 5V Power        | -    | 5V            | Power     | Main 5V rail (second pin) |
| 6        | GND             | -    | (GND)         | Power     | Ground                    |
| 8        | GPIO14 (TXD)    | 14   | B             | Buttons   | B button (active low)     |
| 10       | GPIO15 (RXD)    | 15   | (unused)      | -         | -                         |
| 12       | GPIO18 (PCM_CLK)| 18   | BCK           | Audio     | I2S bit clock             |
| 14       | GND             | -    | (GND)         | Power     | Ground                    |
| 16       | GPIO23          | 23   | A             | Buttons   | A button (active low)     |
| 18       | GPIO24          | 24   | D/CX          | Display   | ILI9341 Data/Command      |
| 20       | GND             | -    | (GND)         | Power     | Ground                    |
| 22       | GPIO25          | 25   | RESET         | Display   | ILI9341 Reset             |
| 24       | GPIO8 (CE0)     | 8    | CSX           | Display   | ILI9341 Chip Select       |
| 26       | GPIO7 (CE1)     | 7    | (unused)      | -         | -                         |
| 28       | ID_SC           | 1    | (reserved)    | -         | HAT EEPROM; do not use    |
| 30       | GND             | -    | GND           | Power     | Ground                    |
| 32       | GPIO12          | 12   | UP            | Buttons   | D-pad Up (active low)     |
| 34       | GND             | -    | GND           | Power     | Ground                    |
| 36       | GPIO16          | 16   | SELECT        | Buttons   | Select button             |
| 38       | GPIO20          | 20   | DOWN          | Buttons   | D-pad Down (active low)   |
| 40       | GPIO21          | 21   | DIN           | Audio     | I2S data to DAC           |

### I2S Pin Assignments -- CONFIRMED (2026-04-03)

The I2S pin assignments have been verified during breadboard prototype testing using
`dtoverlay=hifiberry-dac` in /boot/config.txt. Audio output through the PCM5102A DAC
was confirmed working with these standard I2S GPIO assignments:

- **BCK (Bit Clock)**: GPIO18, Pin 12 -- CONFIRMED
- **LRCK (Word Clock)**: GPIO19, Pin 35 -- CONFIRMED
- **DIN (Data)**: GPIO21, Pin 40 -- CONFIRMED

The standard `hifiberry-dac` overlay uses GPIO18/19/21 and works correctly.

### Notes on Reserved and Unused Pins

- **Pin 27 (ID_SD / GPIO0)** and **Pin 28 (ID_SC / GPIO1)** are reserved for the Pi's
  HAT EEPROM interface. Leave them unconnected on the custom PCB.
- **Pins 3 / 5 (GPIO2 / GPIO3)**, **Pin 10 (GPIO15)**, **Pin 26 (GPIO7)**, and
  **Pin 33 (GPIO13)** are unused in the Marathon design. GPIO2/3 remain available
  as I2C (SDA1/SCL1) if a future revision adds an I2C peripheral.

---

## 2. Subsystem Breakdowns

### Display - ILI9341 3.2" SPI LCD (240x320)

The display connects via SPI plus a few control signals. The display connector on the
schematic shows these pins (top to bottom on the ribbon cable):

| Display Pin | Signal | Pi GPIO | Description                        |
|-------------|--------|---------|------------------------------------|
| P$1         | GND    | -       | Ground                             |
| P$2         | RESET  | GPIO25  | Hardware reset (active low)        |
| P$3         | SCL    | GPIO11  | SPI Clock (SCLK)                   |
| P$4         | D/CX   | GPIO24  | Data/Command select (DC/RS)        |
| P$5         | CSX    | GPIO8   | Chip Select (CE0, active low)      |
| P$6         | SDI    | GPIO10  | SPI MOSI (data Pi → display)       |
| P$7         | SDO    | GPIO9   | SPI MISO (data display → Pi)       |
| P$8         | GND2   | -       | Second ground                      |
| P$9         | VCC    | -       | 3.3V power (from 3V3 rail)         |
| P$10        | LEDA   | -       | LED backlight anode                 |
| P$11        | LED_K1 | -       | LED backlight cathode 1            |
| P$12        | LED_K2 | -       | LED backlight cathode 2            |
| P$13        | LED_K3 | -       | LED backlight cathode 3            |
| P$14        | LED_K4 | -       | LED backlight cathode 4            |
| P$15        | XL     | -       | Touch panel (unused)               |
| P$18        | YU     | -       | Touch panel (unused)               |
| P$16        | XR     | -       | Touch panel (unused)               |
| P$17        | YD     | -       | Touch panel (unused)               |

**Backlight circuit**: LEDA is fed from the 5V rail through R30, a 22 ohm 0.5W resistor.
The four LED_K cathodes are tied together and return to ground through R31, a 0 ohm link.
With the panel's backlight at about 3.1V / 90 mA, 22 ohm gives roughly 86 mA. The breadboard
display module had its own current limiting and ran from 3.3V; the bare panel needs R30.

**fbcp-ili9341 config** (from project plan):
- SPI clock divider: 6
- DC pin: GPIO24
- RST pin: GPIO25
- Uses SPI0 (CE0 = GPIO8)

### Audio - PCM5102A DAC + PAM8403 Amplifier

The audio chain is: **Pi (I2S) → PCM5102A (DAC) → PAM8403 (amplifier) → Speakers**

#### PCM5102A DAC (I2S Input)

| DAC Pin | Signal | Pi GPIO | Description                    |
|---------|--------|---------|--------------------------------|
| VCC     | 5V     | -       | 5V power (breakout module only) |
| 3.3V    | 3V3    | -       | 3.3V power                     |
| GND     | GND    | -       | Ground                         |
| DIN     | DIN    | GPIO21  | I2S serial data                |
| BCK     | BCK    | GPIO18  | I2S bit clock                  |
| LCK     | LCK    | GPIO19  | I2S word clock (LRCK)          |
| SCK     | -      | -       | System clock (tied to GND for auto) |
| FLT     | -      | -       | Filter select (tied high/low)  |
| DMP     | -      | -       | De-emphasis (tied high/low)    |
| FMT     | -      | -       | Format select (I2S = low)      |
| XMT     | -      | -       | Mute control (active low)      |

The table above lists the breakout module's pins as wired on the breadboard. The module
regulates its 5V VCC down on board.

**Final design**: PCM5102A integrated as bare IC on the custom PCB. All three supplies
(AVDD, CPVDD, DVDD) run on 3.3V; the bare chip must never see 5V. SCK, FMT, FLT, and DEMP
are tied to GND, and XSMT is tied to 3.3V. No headphone jack.

#### PAM8403 Amplifier (Line → Speaker)

| Amp Pin | Signal | Description                          |
|---------|--------|--------------------------------------|
| L IN    | -      | Left channel input (from DAC L out)  |
| R IN    | -      | Right channel input (from DAC R out) |
| L OUT+  | -      | Left speaker positive                |
| L OUT-  | -      | Left speaker negative                |
| R OUT+  | -      | Right speaker positive               |
| R OUT-  | -      | Right speaker negative               |
| VCC     | 5V     | 5V power                             |
| GND     | GND    | Ground                               |

**Final design**: PAM8403 integrated as bare IC on the custom PCB. Mute switch (SPDT)
drives the PAM8403 SHDN/MUTE pins for silence; the amp stays on 5V. Breakout module version used for breadboard
prototyping only.

**Audio output path**:
- Speakers: PAM8403 L/R outputs → 2x small speakers
- Mute switch: SPDT slide switch on PCB edge, drives PAM8403 SHDN/MUTE
- No headphone jack (Bluetooth available for private listening via Pi Zero 2W's BT 4.2)
- Volume control: software via RetroPie (mute switch = 0% or 100%)

### Buttons - Direct GPIO (No Expander)

All buttons connect directly to Pi GPIO pins with internal pull-ups enabled. No I2C GPIO
expander is needed. Each button shorts its GPIO pin to ground when pressed (active low).
The `mk_arcade_joystick_rpi` kernel module reads these GPIOs and presents them to the OS
as a standard joystick device that EmulationStation consumes directly.

| Button      | GPIO | Phys Pin | Type                  |
|-------------|------|----------|-----------------------|
| D-pad Up    | 12   | 32       | Silicone membrane pad |
| D-pad Down  | 20   | 38       | Silicone membrane pad |
| D-pad Left  | 4    | 7        | Silicone membrane pad |
| D-pad Right | 17   | 11       | Silicone membrane pad |
| A           | 23   | 16       | Silicone membrane pad |
| B           | 14   | 8        | Silicone membrane pad |
| X           | 6    | 31       | Silicone membrane pad |
| Y           | 22   | 15       | Silicone membrane pad |
| Start       | 26   | 37       | SMD tactile switch    |
| Select      | 16   | 36       | SMD tactile switch    |
| L Shoulder  | 27   | 13       | Side-push SMD switch  |
| R Shoulder  | 5    | 29       | Side-push SMD switch  |

The row order matches the `mk_arcade_joystick_rpi` module options:
`map=5 gpio=12,20,4,17,26,16,23,14,6,22,27,5` (UP, DOWN, LEFT, RIGHT, START, SELECT,
A, B, X, Y, L, R). Button-to-action mapping is handled by EmulationStation's own input
configuration (`es_input.cfg`), not by the kernel module.

**Button types**:
- 2x SMD tactile switches (Alps SKTHACE010) → Start and Select
- 2x side-push SMD switches (Alps SKSCLDE010) → L and R shoulders, on the top edge of the PCB
- Silicone membrane pads → D-pad (4 directions) and face buttons (A, B, X, Y)

Marathon does not include a dedicated hotkey/system button. The RetroPie hotkey
role (quit-emulator, save-state, etc.) is assigned to Select in EmulationStation,
which works fine without a dedicated modifier key.

### Power Circuit (IP5306)

```
USB-C → IP5306 ←→ LiPo 2000-3000mAh (TBD)
           │
           ├→ 5V output → Pi Zero 5V pins (2, 4)
           │              + PAM8403 VCC (mute switch drives SHDN/MUTE)
           │              + LCD backlight (through R30)
           │
Pi 3.3V regulator (pins 1, 17) → LCD VCC + PCM5102A (all supplies)
           │
           └→ Charging + boost + load sharing + protection
              all handled by one chip
```

**Key features**:
- Play while charging (load sharing built into IP5306)
- Clean 5V boost from 3.7V battery voltage
- Low battery protection (won't over-discharge and kill the battery)
- Battery level indication available (up to 4 LEDs). The current PCB leaves these pins
  unconnected, so there is no charge indicator yet.

---

## 3. Remaining Unknowns

These need to be resolved before schematic capture is complete:

1. ~~**5V boost regulation**~~ - RESOLVED: IP5306 handles 3.7V->5V boost.

2. ~~**I2S pin assignments**~~ - RESOLVED (2026-04-03): BCK=GPIO18, LRCK=GPIO19,
   DIN=GPIO21. Standard hifiberry-dac overlay. Confirmed working during prototype.

3. ~~**Backlight circuit details**~~ - RESOLVED: 5V through R30 (22 ohm) to LEDA, cathodes
   to GND through R31 (0 ohm). No brightness-control transistor on this revision.

4. ~~**Headphone jack wiring**~~ - RESOLVED: No headphone jack. Bluetooth for private audio.

5. ~~**Mute switch circuit**~~ - RESOLVED: SPDT switch drives PAM8403 SHDN/MUTE. Cutting amp power instead would leave the DAC driving an unpowered amp.

6. ~~**Button input method**~~ - RESOLVED (2026-04-04): mk_arcade_joystick_rpi kernel
   module with `map=5` (custom GPIO mode). NOT retrogame (ES doesn't recognize
   retrogame's virtual keyboard on this Buster image). GPIO pin order configured in
   `/etc/modprobe.d/joystick.conf`. Module loaded at boot via `/etc/modules`.
   Pin order: UP,DOWN,LEFT,RIGHT,START,SELECT,A,B,X,Y,L,R mapped to GPIOs:
   `gpio=12,20,4,17,26,16,23,14,6,22,27,5`

7. ~~**Display backlight power**~~ - RESOLVED: 5V rail. 3.3V would leave only about 0.2V of
   headroom over the backlight's forward voltage.
