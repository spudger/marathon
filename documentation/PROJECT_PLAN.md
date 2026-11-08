# Marathon - Project Plan

## Context

Marathon is a DIY retro gaming handheld built around a Raspberry Pi Zero 2 W. The design prioritizes battery life by integrating all ICs (power management, DAC, amplifier) as bare chips on a custom PCB, dedicating maximum internal volume to a high-capacity LiPo cell.

The goal is a thin, sleek handheld that fits comfortably in a pocket, with battery life long enough to game without worrying about it. Thinness and battery capacity win over other layout choices.

This is a multi-phase hardware project spanning: component identification, schematic capture, PCB layout, case design, firmware/software setup, and final assembly.

---

## Architecture

| Subsystem | Component | Notes |
|-----------|-----------|-------|
| **Compute** | Raspberry Pi Zero 2 W | Quad-core, WiFi, Bluetooth 4.2. Mounts on the back of the PCB on 5 mm standoffs, joined by long-tail header pins soldered through both boards |
| **Display** | ILI9341 3.2" SPI LCD | 18-pin FPC ribbon soldered direct to PCB |
| **Audio DAC** | PCM5102A (bare IC) | I2S input from Pi, line-level output to amplifier |
| **Audio Amp** | PAM8403 (bare IC) | Class-D stereo, drives two speakers |
| **Power** | BQ25616 + TPS61023 + LTC2954 + MAX17048 (bare ICs) | 0.9 A charging with a 0 to 45 °C cutoff and power path, 5 V boost, power key with clean shutdown, battery level over I2C |
| **Battery** | 3.7V LiPo, about 4000 mAh target | 105060-class cell, about 10 mm thick, in a 67 x 59 mm space on the back of the PCB, 3-pin JST-PH connector with NTC |
| **Audio Out** | 2x speakers + mute switch | SPDT switch holds the amp in shutdown. Bluetooth available for private listening |
| **Buttons** | Silicone membranes + SMD switches | Direct GPIO, no expander IC. Membrane pads press on bare ENIG contacts on the PCB |
| **Case** | Custom 3D print | First concept in CadQuery: two shells, 164.2 x 79.2 x 20.4 mm, clamping the board with four M2 screws (`case/`, spec `planning/specs/027-CASE-CONCEPT.md`) |

---

## Design Decisions

### 1. Integrated PCB Design
All ICs (power section, PCM5102A, PAM8403) are placed directly on a custom PCB as bare chips, to be soldered by JLCPCB's assembly service when the final board is fabricated. This:
- Reclaims ~15-20cm² of surface area (more room for battery)
- Eliminates fragile board-to-board solder connections
- Results in a cleaner, more reliable build
- Only requires hand-soldering for: Pi Zero, display ribbon, battery, speakers, buttons/switches

### 2. Power Management
The final board replaced the prototype's IP5306 (spec `planning/specs/011-POWER-DESIGN.md`):
- BQ25616 charger: 0.9 A from USB-C, charging only between 0 °C and 45 °C, power path for play while charging
- TPS61023 boost: 5.06 V for the Pi, amp and backlight, switched off completely when the device is off
- LTC2954 power key controller: hold to turn on, short press for a clean Linux shutdown, long hold to force off
- MAX17048 fuel gauge: battery percentage for an on-screen level and a clean low-battery shutdown

### 3. Battery Life (High Priority)
Target: about 4000 mAh, 4+ hours of demanding games and about 8 hours of light ones (estimated). The "Marathon" name comes from this goal.
Strategy: use the whole free area beside the Pi on the back of the board, and a cell about 10 mm thick. With tolerance, mounting tape and room to swell, the case clears about 11.3 mm over it, about 1.3 mm more than the Pi's own stack. Spec: `planning/specs/022-BATTERY-SPACE.md`.

### 4. Display
Prototype uses a TN-panel ILI9341 3.2" SPI LCD. An IPS variant with the same ILI9341 controller and 18-pin FPC pinout exists as a drop-in upgrade and will be evaluated during final build if TN viewing angles prove inadequate in the case.

### 5. Simplified Audio
- **No headphone jack** -- Bluetooth 4.2 on Pi Zero 2W for private listening
- **Speakers** -- zero-latency audio for gameplay
- **Mute switch** -- SPDT switch drives the PAM8403 SHDN/MUTE pins (0% or 100%). The amp stays powered.
- **Fine volume control** -- software via RetroPie
- Audio chain: Pi (I2S) -> PCM5102A (DAC) -> PAM8403 (amp) -> Speakers

### 6. USB-C
Proper 5.1k CC pulldown resistors for spec compliance. Works with all USB-C cables, not just A-to-C.

---

## Project Phases

### Phase 1: Component Identification & Research
**Goal**: Identify every IC, connector, and component needed
**Status**: MOSTLY COMPLETE

Resolved:
- [x] Install KiCad (Flatpak, v9.0.7)
- [x] Confirm all buttons are direct GPIO (no I2C expander)
- [x] Choose power management solution (IP5306)
- [x] Decide on audio architecture (no headphone jack, speakers + mute switch)
- [x] Confirm PAM8403 as amplifier
- [x] Confirm PCM5102A as DAC
- [x] Create full GPIO pin mapping (see PIN_MAPPING.md)
- [x] Create Bill of Materials (see `bom/`)
- [x] Identify exact ILI9341 display module -- 3.2" bare 18-pin FPC screen, same listing for prototype (with adapter board) and final build (bare). [AliExpress](https://www.aliexpress.com/item/1005003005329598.html)
- [x] Identify speaker specs -- 8 ohm, 1W, ~10-15mm pre-wired. Commodity part, exact size matched to case cutouts later.
- [x] Source prototype modules -- ordered 2026-03-22 from Amazon (IP5306, battery) + AliExpress (PCM5102A, PAM8403, display, speakers)
- [x] Confirm I2S pin assignments -- BCK=GPIO18, LRCK=GPIO19, DIN=GPIO21. Verified via `dtoverlay=hifiberry-dac` during prototype testing (2026-04-03).
- [x] Confirm button driver approach -- mk_arcade_joystick_rpi kernel module (NOT retrogame). Verified during prototype testing (2026-04-04).

Remaining:
- [ ] Identify silicone button pad dimensions and mounting style -- **IN PROGRESS**. Design uses 2x identical cross-shaped pads (D-pad and ABXY). The PCB currently uses 5 mm contacts with 24 mm between opposite contacts, which still needs a fit check against real pads.
- [x] Identify tactile switch specs -- Alps Alpine SKTHACE010 (top-push) for Start, Select, and the power key. Alps Alpine SKSCLDE010 (side-push) for L and R.
- [ ] Finalize battery cell -- PCB reserves 67 x 59 mm for a 105060-class cell up to 57 x 65 mm with its protection board, about 10 mm thick. Provisional pick: Bihuade 105063, 4000 mAh, until it passes the arrival checks in spec 022.

### Phase 2: Breadboard Prototype
**Goal**: Verify all subsystems work together before designing PCB
**Status**: COMPLETE (2026-04-04)

- [x] Order prototype components (ordered 2026-03-22):
  - Amazon: IP5306 boards (10-pack, $10), 500mAh LiPo battery ($7.09)
  - AliExpress: PCM5102A DAC (x2, ~$2), PAM8403 amp (5-pack, ~$3.55), ILI9341 3.2" SPI display ($7.60), speakers ($2.87)
  - Using generic tactile buttons + owned SS12F15-G5 SPDT switches for prototype
- [x] Flash RetroPie to SD card (reused GamePi20 image, Raspbian Buster based)
- [x] Wire up power subsystem (IP5306 + battery → 5V rail). Verified 5.1V output
- [x] Boot Pi Zero from IP5306 power. Confirmed, IP5306 auto-starts under load
- [x] Wire up Pi Zero to display (SPI). ILI9341 breakout, fbcp-ili9341 compiled and working
- [ ] Tune display resolution. Currently 640x480 scaled to 320x240, looks blurry. Set HDMI output to native 320x240 for pixel-perfect rendering.
- [x] Wire up audio chain (I2S → DAC → amp → speakers). PCM5102A and PAM8403 soldered together, audio confirmed working
- [x] Wire up buttons to GPIO. Tested LEFT (GPIO4) and RIGHT (GPIO17), confirmed working in EmulationStation
- [x] Verify play-while-charging works. Confirmed, IP5306 passes through wall power while charging battery
- [x] Document any issues or changes needed

### Phase 2 Notes
- IP5306 board has no USB port; USB-C cable soldered directly to VIN/GND pads
- 500mAh LiPo soldered directly to BAT/GND pads
- IP5306 auto-shuts down with no load; stays on once Pi is drawing current. Also shuts down when battery is dead. Wall charger works better than MacBook USB for charging.
- Raspbian Buster repos are archived; had to point apt at legacy.raspbian.org
- fbcp-ili9341 build flags: `-DILI9341=ON -DGPIO_TFT_DATA_CONTROL=24 -DGPIO_TFT_RESET_PIN=25 -DSPI_BUS_CLOCK_DIVISOR=6 -DSTATISTICS=0`
- Display rotation: no rotation flag needed (0 degrees) with pins on left side of screen
- GamePi20 image had `dtoverlay=audremap,pins_18_19` -- this is NOT the right overlay for PCM5102A. Replaced with `dtoverlay=hifiberry-dac` which enables I2S on GPIO18/19/21.
- Also disabled `dtparam=audio=on` (commented out) to prevent conflicts with I2S
- PCM5102A config pins: FLT, DMP, FMT, SCL all to GND; XMT to 5V (unmute)
- PCM5102A L/R audio outputs soldered directly to PAM8403 L/G/R inputs
- **Button driver: mk_arcade_joystick_rpi kernel module (NOT retrogame).** Retrogame creates a virtual keyboard that EmulationStation on this Buster image won't recognize. The mk_arcade_joystick_rpi module (from the GamePi20 image) creates a joystick device that ES natively supports.
- mk_arcade_joystick_rpi config: `map=5 gpio=12,20,4,17,26,16,23,14,6,22,27,5` (custom GPIO mode, pin order: UP,DOWN,LEFT,RIGHT,START,SELECT,A,B,X,Y,L,R)
- Modprobe config at `/etc/modprobe.d/joystick.conf`, module loaded via `/etc/modules`
- ES input config at `~/.emulationstation/es_input.cfg` (symlinked to `/opt/retropie/configs/all/emulationstation/es_input.cfg`)

### Phase 3: Schematic Capture (KiCad)
**Goal**: Create a complete, verified schematic
**Status**: MOSTLY COMPLETE. Source: `pcb/marathon.kicad_sch`.

- [x] Create schematic with these subsystems:
  - Pi Zero 2W header + mounting holes
  - ILI9341 display interface (SPI + backlight through R30, 22 ohm from 5V)
  - PCM5102A DAC (I2S, bare IC + supporting components)
  - PAM8403 amplifier (bare IC + supporting components)
  - Power section: BQ25616 charger, TPS61023 boost, LTC2954 power key controller, MAX17048 fuel gauge
  - USB-C connector with CC resistors
  - Battery connector
  - Button pads (direct GPIO, silicone membranes)
  - Tactile switches (start, select, shoulders, power key)
  - SPDT mute switch (drives PAM8403 SHDN/MUTE)
  - Speaker pads
  - Power distribution (3.3V from Pi, 5V from the TPS61023 boost)
- [x] Cross-reference against PIN_MAPPING.md -- all 40 Pi header pins match (checked 2026-10-07)
- [x] Add test points for debugging -- TP1 to TP13 on the power, power key, backlight and I2C nets (2026-11-04)
- [x] Run ERC (Electrical Rules Check) -- 0 violations
- [ ] Clean up the sheet layout for readability (overlapping symbols and notes), then export a PDF to `schematics/`

### Phase 4: PCB Layout (KiCad)
**Goal**: Design a PCB for a compact handheld form factor.
**Status**: IN PROGRESS. Not ready for fabrication.

- [x] Import schematic to PCB editor
- [x] Define board outline -- 160 x 75 mm landscape, 6 mm corner radius. Four plated M2 case holes, 5 mm in from each edge (2026-11-04).
- [x] Place components -- the Raspberry Pi sits on its back-side guide, inside the outline and clear of the battery envelope
- [x] Route traces (2-layer board) -- all nets routed, with ground pours on both layers
- [x] Determine final battery size from available area -- 67 x 59 mm reserved for a 105060-class cell, about 10 mm thick (2026-11-07, spec 022)
- [x] Add test points and a Pi antenna copper keep-out (2026-11-04)
- [ ] Add silkscreen artwork
- [x] Fix the U2 (PCM5102A) and U3 (PAM8403) footprints, which were mirrored on the back side (2026-11-06)
- [x] Run DRC (Design Rules Check) -- 0 errors, 0 warnings and 0 unrouted connections as of 2026-11-06
- [x] Fix the defects from the 2026-10-31 design review -- switch footprints, mute circuit, audio level, inductor rating, battery clearance, power and audio layout
- [x] Build the power design (spec 011) -- charger, boost, power key controller, fuel gauge, backlight switch, 3-pin battery connector (2026-11-02)
- [ ] Verify provisional footprints (LCD tail) against real parts or manufacturer drawings. The Alps switch footprints now follow Alps' land patterns.
- [ ] Generate Gerber + BOM + pick-and-place files for JLCPCB

### Phase 5: Case Design
**Goal**: Design a case for the Marathon PCB
**Status**: IN PROGRESS. First concept modeled (spec `planning/specs/027-CASE-CONCEPT.md`).

- [x] Design a first case concept around the board -- CadQuery, two shells, printed caps, STLs and renders in `case/` (2026-11-08)
- [x] Account for component placement (no headphone jack hole, battery fitment, USB-C position). The back clears 11.3 mm over the battery, about 1.3 mm more than the Pi's stack (spec 022).
- [x] Verify fit with PCB dimensions -- in the model, against KiCad's STEP export of the board (`case/tests/test_case.py`)
- [ ] Revise the concept once the silicone pads, speakers, mute switch, LCD panel and Alps switches arrive
- [ ] Choose the case's artwork and where it goes
- [ ] Test-print the parts and record the fit
- [ ] 3D print and potentially order final print from PCBWay

### Phase 6: Software Setup
**Goal**: Configure RetroPie with proper drivers
**Note**: Most of this was validated during Phase 2 prototype. Key configs documented in Phase 2 Notes and PROTOTYPE_BUILD_GUIDE.md.

- [x] Flash RetroPie image to SD card -- reused GamePi20 image (Raspbian Buster based)
- [x] Configure fbcp-ili9341 for the ILI9341 display -- compiled with ILI9341 flags, installed to /usr/local/bin
- [x] Configure I2S audio overlay for PCM5102A -- `dtoverlay=hifiberry-dac` in config.txt
- [x] Set up button input driver -- mk_arcade_joystick_rpi kernel module with custom GPIO map
- [ ] Configure software volume control
- [ ] Configure Bluetooth audio (optional, for wireless headphones)
- [ ] Test with ROMs
- [ ] Consider fresh RetroPie image for final build (current Buster image has archived repos)

### Phase 7: Fabrication & Assembly
**Goal**: Build the final device

- [ ] Order PCBs + assembly from JLCPCB (they solder all SMD components)
- [ ] Order remaining components (battery, display, speakers, buttons, Pi)
- [ ] Hand-solder: Pi Zero, display ribbon, battery wires, speakers, buttons/switches
- [ ] Assemble into case
- [ ] Test all subsystems
- [ ] Final integration testing

---

## Tools Needed

| Tool | Purpose | Status |
|------|---------|--------|
| **KiCad 10.0.6** (Flatpak) | Schematic capture + PCB layout | INSTALLED |
| **CadQuery 2.5.2** (through uv, Python 3.12) | Case model, stand-in 3D models | RUNS THROUGH uv |
| **RetroPie** | OS image for the Pi | CONFIGURED (GamePi20 image, Buster) |
| **fbcp-ili9341** | Display driver (SPI framebuffer copy) | COMPILED AND INSTALLED |
| **mk_arcade_joystick_rpi** | GPIO button driver (kernel module) | CONFIGURED |
| **Soldering iron + supplies** | Assembly | OWNED |
| **Multimeter** | Testing and verification | OWNED |
| **Breadboard + jumper wires** | Prototyping | OWNED |

## Immediate Next Steps

1. ~~**Source prototype modules**~~ -- DONE (ordered 2026-03-22)
2. ~~**Build breadboard prototype**~~ -- DONE (2026-04-03 to 2026-04-04). All subsystems verified.
3. ~~**Begin schematic capture in KiCad**~~ -- DONE. ERC clean, pin mapping verified.
4. ~~**Fix the Raspberry Pi placement**~~ -- DONE (2026-10-30). The Pi sits on its back-side guide.
5. ~~**Finish routing**~~ -- DONE (2026-10-30). DRC reports 0 errors and 0 unrouted connections.
6. ~~**Fix design review defects**~~ -- DONE (2026-10-31).
7. ~~**Power design step**~~ -- hardware DONE (2026-11-02). The Pi software settings and the on-screen battery level and brightness control come with Phase 6.
8. **Verify parts against the real hardware** -- LCD tail pitch and contact side, silicone pad fit, Alps switches.

## Key Risks & Unknowns

- ~~**I2S pin assignments**~~ -- RESOLVED: BCK=GPIO18, LRCK=GPIO19, DIN=GPIO21. Confirmed via `dtoverlay=hifiberry-dac` during prototype.
- **Display ribbon pinout** -- Using an 18-pin FPC bare ILI9341 screen. The exact panel's pinout and backlight rating are not confirmed yet.
- ~~**Button driver approach**~~ -- RESOLVED: mk_arcade_joystick_rpi kernel module, NOT retrogame.
- **Battery fitment** -- A 67 x 59 mm space is reserved on the back of the PCB for a cell up to 57 x 65 mm, about 10 mm thick. The cell must meet the requirements in `bom/README.md`, and its connector pin order must match the board's.
- **Unverified footprints** -- The LCD tail and Alps switch footprints were built from documentation and have not been checked against physical parts yet.
- **LCD over the Pi header** -- The LCD's outline covers about 12 pin pairs of the Pi's long-tail header, whose soldered ends stick out on the front at y 30 to 33. Default fix: trim those pins flush after soldering and cover them with Kapton tape, so the panel sits nearly flat. Settle it before the case design. The renders assume a 1.5 mm gap.
- **Open design review items** -- The B button on the UART TX pin. The power design's checks that need a built board are listed in spec 011's finish condition.
- **Case design** -- The first concept fits the board as laid out today, but rests on provisional sizes for the silicone pads, speakers, mute switch, LCD panel and Alps switches. It has no vents, so the Pi's temperature needs checking on the prototype. Spec 027's "Risks and known limits" has the rest.
- **Bluetooth audio latency** -- ~100-300ms, fine for passive games, not ideal for timing-sensitive gameplay. Speakers remain the primary audio output.
- **Display resolution** -- Currently 640x480 HDMI scaled to 320x240 SPI, looks blurry. Need to set HDMI to native 320x240 for pixel-perfect rendering. Low priority.

## Related Documentation

- **PIN_MAPPING.md** -- Complete 40-pin GPIO mapping, subsystem breakdowns, display/audio/button pin assignments
- **bom/** -- Full bill of materials with status, costs, sourcing, and decision log
- **PROTOTYPE_BUILD_GUIDE.md** -- Step-by-step breadboard prototype build guide
