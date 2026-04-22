# Marathon - Bill of Materials

Prototype work also uses a standard breadboard, jumper wires, and tactile push buttons for GPIO testing. These are commodity items and are not listed as line items below.

---

## 1. Compute

| Component | Spec | Est. Cost | Notes |
|-----------|------|-----------|-------|
| Raspberry Pi Zero 2 W | ARM Cortex-A53, WiFi/BT | ~$15 | No-headers variant recommended for the final PCB (solders direct). The WH (with headers) is fine for breadboard prototyping but headers have to be desoldered for the final build. |

## 2. Power

| Component | Spec | Est. Cost | Notes |
|-----------|------|-----------|-------|
| IP5306 breakout board (prototype) | 5V 2A boost + LiPo charger + load sharing | $10 (10-pack) | Outputs 5.1V. No USB port on this board variant; USB-C cable soldered directly to VIN/GND. Auto-shuts down with no load, auto-starts when Pi draws current. Play-while-charging confirmed. |
| IP5306 IC (final PCB) | QFN/SOP-8 package | <$1 | Soldered by JLCPCB/PCBWay assembly service. Supporting circuit: inductor, caps, resistors from datasheet reference design. |
| LiPo Battery (prototype) | 3.7V 500mAh, 702540, JST-PH 2.0 | $7.09 | Soldered directly to IP5306 BAT/GND pads. Charges from wall USB charger (MacBook USB was unreliable for charging). |
| LiPo Battery (final) | 3.7V, 2000-3000mAh target, ≤6mm thick | ~$5-10 | **Size TBD after PCB layout.** By integrating breakout boards as bare chips, we reclaim major surface area for the battery. Thickness ≤6mm to keep case slim. Minimum target: 505060 (5x50x60mm, 2000mAh). Stretch goal: fit a 2500-3000mAh cell. |
| USB-C connector | With proper 5.1k CC pulldown resistors | <$1 | For spec-compliant charging. IP5306 board likely has USB-C or micro-USB input already. Final PCB will have its own connector. |

**Why IP5306**: Single chip handles charging, 3.7V-to-5V boost, load sharing (play while charging), and battery protection. Simpler than using separate charging and boost ICs.

## 3. Display

| Component | Spec | Est. Cost | Notes |
|-----------|------|-----------|-------|
| ILI9341 3.2" SPI LCD (prototype) | 240x320, SPI, 14-pin breakout module with header pins | $7.60 | 14-pin header (9 used + 5 touch pins unused). Driven by fbcp-ili9341 over SPI. VCC on 3.3V, not 5V. Display resolution slightly blurry (640x480 scaled to 320x240); fixable by tuning HDMI config. |
| ILI9341 3.2" SPI LCD (bare screen only) | 240x320, SPI, 18-pin FPC ribbon, no adapter board | ~$7 | For final PCB. FPC ribbon solders directly to pads on custom board. |

## 4. Audio

| Component | Spec | Est. Cost | Notes |
|-----------|------|-----------|-------|
| PCM5102A DAC breakout (prototype) | I2S input, line-level output, 11-pin left + 3-pin right (R/G/L) | ~$2 | Config pins: FLT, DMP, FMT, SCL to GND; XMT to 5V (unmute). I2S via `dtoverlay=hifiberry-dac`. L/R audio outputs soldered directly to PAM8403. |
| PCM5102A IC (final PCB) | TSSOP-20 package | <$2 | Integrated directly onto final PCB as bare chip (~4x4mm). Eliminates bulky breakout board. JLCPCB assembly. |
| PAM8403 amp breakout (prototype) | Class-D stereo, 3W per channel | ~$3.55 (5-pack) | Input pins labeled L/G/R (note: "R" may look like "B" on silkscreen). PCM5102A L/R outputs soldered directly to PAM8403 L/R inputs, G to G. POWER+ to 5V, POWER- to GND. |
| PAM8403 IC (final PCB) | SOP-16 package | <$1 | Integrated directly onto final PCB as bare chip (~3x3mm). Eliminates bulky breakout board. JLCPCB assembly. |
| Speakers (x2) | 8 ohm, 1W, 15mm, pre-wired | $2.87 | Both channels verified working in prototype. Connected to PAM8403 LOUT+/-, ROUT+/-. |
| Mute switch | SPDT slide switch (SS12F15-G5) | <$1 | Mounted on edge of PCB. Cuts power to PAM8403 to silence speakers. Simple on/off, fine volume control handled via RetroPie software. |

**No headphone jack** - Bluetooth audio available via Pi Zero 2W's BT 4.2 for private listening. Speakers are the primary audio output. Note: BT audio has latency (~100-300ms), fine for passive games but not ideal for timing-sensitive gameplay.

**Audio chain**: Pi (I2S) → PCM5102A (DAC) → PAM8403 (amp) → Speakers. Mute switch kills amp power for silence.

## 5. Buttons / Input

| Component | Spec | Est. Cost | Notes |
|-----------|------|-----------|-------|
| Silicone membrane pads (x2) | Cross/diamond-shaped, 4-way conductive rubber, identical pads for D-pad and ABXY | ~$3-5 | Two identical cross-shaped pads needed (one for D-pad, one for ABXY). Options: generic cross pads, GBC D-pad pads, SNES-style pads, or DS-style pads. Buy pads first, then design PCB contact pad spacing to match. Search AliExpress: "conductive silicone rubber button pad cross". See also: [ZedLabz GBC pads](https://www.zedlabz.com/products/conductive-silicone-rubber-button-membrane-contact-pads-for-nintendo-game-boy-color-cgb-gbc-zedlabz), [AliExpress conductive silicone buttons](https://www.aliexpress.com/w/wholesale-conductive-silicone-rubber-button.html). |
| SMD tactile switches (x2) | For Start and Select | <$1 | Surface mount, low profile. |
| Right-angled tactile buttons (x3) | For L shoulder, R shoulder, Z (System) | <$1 | Mount on back of PCB, actuated from case edge. |

**All buttons are direct GPIO** - no I2C expander needed. Each button shorts its GPIO to ground (active low) using the Pi's internal pull-up resistors.

## 6. Passive Components (Final PCB)

| Component | Spec | Est. Cost | Notes |
|-----------|------|-----------|-------|
| R1 - Backlight resistor | 3.9 ohm (3R9) SMD | <$0.10 | Current limiting for display backlight LED array. |
| IP5306 support components | Inductor + caps + resistors per datasheet | <$2 total | Reference design from IP5306 datasheet. Values TBD. |
| PCM5102A support components | Decoupling caps, pull-up/down resistors per datasheet | <$1 total | SCK to GND, FMT to GND (I2S mode), FLT/DMP config resistors. |
| PAM8403 support components | Input/output coupling caps, filter components | <$1 total | Per datasheet reference design. |
| USB-C CC resistors (x2) | 5.1k ohm | <$0.10 | Required for USB-C spec compliance. |

## 7. Mechanical / Case

| Component | Spec | Est. Cost | Notes |
|-----------|------|-----------|-------|
| 3D printed case | Custom design, in progress | TBD | STL files will be uploaded to this repo when complete. |
| M3 bolts + nuts (x4) | 20mm, acrylic or metal | <$2 | Holds case together. |
| Micro SD card | 32GB+ Class 10 | ~$8 | For RetroPie image. |

---

## Estimated Cost Summary

### Prototype Order (2026-03-22)

| Item | Source | Cost |
|------|--------|------|
| IP5306 breakout (10-pack) | Amazon | $10.00 |
| LiPo battery 500mAh | Amazon | $7.09 |
| PCM5102A DAC breakout (x2) | AliExpress | ~$2.00 |
| PAM8403 amp breakout (5-pack) | AliExpress | ~$3.55 |
| ILI9341 3.2" SPI display | AliExpress | $7.60 |
| Speakers 15mm (pair) | AliExpress | $2.87 |
| **Prototype total** | | **~$33** |

Amazon order: ~$17 | AliExpress order: ~$19 (may be split across multiple carts due to AE's Dollar Express vs regular marketplace).

### Final Build (Future — estimates only)

| Category | Est. Cost |
|----------|-----------|
| Display (bare screen for PCB) | ~$7 |
| Battery (2000-3000mAh) | ~$5-10 |
| Buttons / input (silicone pads, tactile switches) | $5-7 |
| Case / mechanical | TBD |
| PCB fabrication (JLCPCB) | ~$5-15 |
| PCB assembly (JLCPCB) | ~$10-20 |
| Passive components | <$3 |
| **Final build estimate** | **~$35-60** |

---

## Sourcing

| Supplier | What to buy there |
|----------|-------------------|
| **Amazon** | IP5306 breakout boards, LiPo battery (prototype) |
| **AliExpress** | PCM5102A, PAM8403, ILI9341 display, speakers. Future: buttons, silicone pads, final battery |
| **JLCPCB/PCBWay** | PCB fabrication + SMT assembly for final board |
| **In-house** | 3D-printed case. Custom design is in progress; STL files will be uploaded to this repo when complete. |

---

## Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-03-03 | IP5306 for power management | Handles charging + boost + load sharing in one chip. Cheap breakout boards available for prototyping. Same chip integrates onto final PCB. |
| 2026-03-03 | Prototype with breadboard + IP5306 boards | Tactile learning experience, no bench supply needed, cheap to iterate. |
| 2026-03-03 | JLCPCB/PCBWay for final assembly | They can solder SMD components (IP5306, passives) onto the custom PCB. |
| 2026-03-03 | Integrate ALL breakout boards as bare chips on final PCB | By integrating IP5306 + PAM8403 + PCM5102A as bare ICs directly on the PCB instead of using breakout boards, we reclaim ~15-20cm² of space for a larger battery. Prototype with breakout boards, final build uses integrated chips. |
| 2026-03-03 | Battery: maximize area, keep thin (≤6mm) | No extra width available in case. Instead of going thicker, reclaim board space and use a wider/longer thin cell. Minimum target 2000mAh, stretch 3000mAh. Final size TBD after PCB layout. |
| 2026-03-03 | Ditch headphone jack, keep speakers + mute switch | No 3.5mm devices owned. Bluetooth available via Pi Zero 2W for private listening (with latency tradeoff). Speakers for gameplay audio. Mute switch for quick silence. Software volume via RetroPie for fine control. Saves board space and simplifies audio circuit. |
| 2026-03-05 | ILI9341 display: bare 18-pin FPC screen + adapter board | Same listing for both prototype and final build. Adapter board breaks 18-pin FPC to 14-pin header for breadboard use (with F-M jumper wires). Bare screen ribbon solders to final PCB. [AliExpress](https://www.aliexpress.com/item/1005003005329598.html). Buy 1x with adapter + 1x bare. ~$7 each. |
| 2026-03-05 | Speakers: 8 ohm, 1W, ~10-15mm pre-wired | Commodity part, not mission-critical. Any 8 ohm small speaker works with PAM8403. Exact size to be matched to case cutouts later. ~$2 for a pair. |
| 2026-03-05 | Silicone membrane pads for D-pad + ABXY | Two identical cross-shaped pads for D-pad and ABXY. Plan: buy pads first, design PCB contact spacing to match. Still researching exact source — options include generic cross pads or repurposed console pads (GBC, SNES, DS). |
| 2026-03-22 | Prototype order placed (Amazon + AliExpress) | All prototype components ordered. Amazon: IP5306 boards (10-pack) + 500mAh LiPo. AliExpress: PCM5102A (x2), PAM8403 (5-pack), ILI9341 3.2" display, speakers. Total ~$36. |
| 2026-03-22 | Prototype display: all-in-one module (not bare FPC + adapter) | Found an ILI9341 3.2" SPI module with screen and pins on a single rigid board — plugs directly into breadboard. Easier for prototyping than the bare FPC + adapter approach. Bare FPC screen still planned for final PCB. |
| 2026-04-03 | Breadboard prototype: all subsystems verified | Power (IP5306, 5.1V output, play-while-charging), display (ILI9341 via SPI/fbcp-ili9341), audio (PCM5102A DAC + PAM8403 amp, I2S via hifiberry-dac overlay), buttons (mk_arcade_joystick_rpi kernel module). Full prototype build guide in documentation/PROTOTYPE_BUILD_GUIDE.md. |
| 2026-04-04 | Button driver: mk_arcade_joystick_rpi, NOT retrogame | Retrogame creates a virtual keyboard device that EmulationStation (on this Buster image) does not recognize. mk_arcade_joystick_rpi creates a proper joystick device that ES natively supports. Config: map=5 with custom GPIO list. |
| 2026-04-21 | Pi Zero 2 W (no headers) for final build | Final PCB solders the Pi direct. WH variant is fine for prototyping but headers have to be desoldered before the final build. Plain W is cheaper and saves the desolder step for anyone replicating this. |
| 2026-04-21 | Case: custom 3D-printed design | Earlier plan was to base the case on existing Thingiverse STLs. Decision changed to designing the case from scratch to fit the custom PCB footprint, battery, and component layout exactly. STL files will be published in this repo when the design is complete. |
