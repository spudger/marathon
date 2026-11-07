# Battery space for a 4000 mAh cell

- **Status:** draft
- **Issue:** spudger/marathon#22
- **PRs:** none yet
- **Draft:** none
- **Plans:** none yet

## Problem

Spec 011 reserves 63 x 50 mm on the back of the board, at most 6 mm thick. A search on
2026-11-07 found no in-stock cell that fits that space and meets spec 011's requirements. The cells
that come close hold 1800 to 2000 mAh, which gives roughly 2 to 3.5 hours of play (see "Runtime").
The project goal is 4 to 6 hours or more (`documentation/PROJECT_PLAN.md`, "Battery Life").

## Goal

Grow the battery space so it takes an in-stock cell of about 4000 mAh, and pick that cell. The
case may get about 1 mm deeper than the rear-mounted Pi already makes it (decision 3).

## Free space on the back

Measured from `pcb/marathon.kicad_pcb` at `0c61d2f`: each part's courtyard, or its bounding box
where it has none, for every part that reaches past x = 95 mm. Board coordinates, in mm; the
outline runs from (20, 20) to (180, 95).

| Part | Side | What limits the battery |
|---|---|---|
| Power circuit (U4, U5, L1, B1 and their passives) | back | right edge at x = 111.6 (B1) |
| H3, H4 case holes | through | x 172.5 to 177.5, at y 22.5 to 27.5 and y 87.5 to 92.5 |
| SW21, R shoulder button | front, through-hole | x 152.2 to 157.8, down to y = 25.6 |
| J6, speaker wire pads | front, through-hole | x 139 to 147, from y = 87.7 |
| SW2, power slide switch | front, through-hole | x 152 to 172, from y = 88.4 |

Through-hole parts and holes count on the back too: their leads, solder joints and the case
standoffs sit there.

The free block is therefore about x 112 to 179 by y 28 to 87, roughly 67 x 59 mm. It reaches
past the holes' x range because the holes sit only at the top and bottom corners. Leaving 0.5 to
1 mm on each side, a cell fits if it measures at most **57 x 65 mm including its PCM**, with
the 65 mm side along the board's long axis.

The current 63 x 50 mm space (x 112 to 175, y 38 to 88) already touches J6 and H4 at its bottom
edge, by up to 0.5 mm.

## Thickness

The Pi Zero 2 W mounts on the back on 5 mm standoffs, component side outward
(`documentation/PROJECT_PLAN.md`). The case back has to clear the standoff gap, the Pi's board
and its tallest part, so a cell up to that depth costs no thickness, if the back of the case is
flat.

Raspberry Pi publishes no heights and no 3D model for the Zero 2 W: its downloads page, mechanical
drawing and product brief give only X and Y dimensions
(https://pip.raspberrypi.com/categories/584-raspberry-pi-zero-2-w). The figures found online for
the Pi's height, from the bottom of its board to the top of its mini-HDMI connector, the tallest
part:

| Source | Height |
|---|---|
| Community STEP model of the Zero 2 W (https://github.com/AndrewK0val/CAD-Models), parsed | 5.05 mm; micro-USB 4.28 mm; nothing modeled under the board |
| Caliper measurement of a Zero W (https://forums.raspberrypi.com/viewtopic.php?t=203435) | 4.76 mm |
| "Maximum z-height" of the Zero 2 W, source not given (https://picockpit.com/raspberry-pi/everything-about-raspberry-pi-zero-2-w/) | 5.2 mm |
| Lab measurement of the original Zero (https://raspi.tv/2015/raspberry-pi-zero-free-on-the-cover-of-this-months-magpi-magazine) | 5.4 mm, probably including connector legs under the board |

So the Pi is about 5.0 mm tall (4.7 to 5.4 mm). With the 5 mm standoffs (`bom/README.md`), the
stack is about **10.0 mm** deep from the back of the main board, 9.7 to 10.4 mm. A typical
2 x 20 long-tail header ends about 8 mm out, below the HDMI connector, so it adds nothing. Calipers
on the real parts replace these figures.

A pouch cell swells over its life, so it needs room above it, about 8% of its thickness. A
10 mm cell therefore needs about 10.8 mm, about 1 mm more than the Pi's stack (decision 3).

## Cell requirements

Spec 011's requirements stand, except the size:

| Requirement | Value |
|---|---|
| Size, including PCM and tolerance | at most 57 x 65 mm, about 10 mm thick (105060 class) |
| Capacity | about 4000 mAh |
| Chemistry | LiPo, 4.2 V full charge, not a 4.35 V high-voltage cell |
| Maximum charge current | at least 1.0 A (the charger runs at 0.90 A typical, 0.96 A worst case) |
| Continuous discharge | at least 2 A |
| Protection (PCM) | included, with overcurrent trip above 3 A |
| Temperature sensor | 10 kΩ NTC, B = 3435 (103AT type), on a third wire. Otherwise, add one to the harness against the cell |
| Availability | in stock, buyable in ones and twos, not made to order |

A cell of 2000 mAh or more rated at 1C meets the charge and discharge rows, so at 4000 mAh only
the PCM trip and the sensor need checking.

## Cell search

Searched 2026-11-07. "Read" means the page or datasheet was opened; "snippet" means it was only
seen in search results. AliExpress and Amazon item pages refused automated fetches, so their
figures are snippets or come from search result pages.

### What the space can hold

Listing titles often overstate capacity. A good pouch cell stores about 0.12 to 0.14 mAh per cubic
mm of body, not counting about 2 mm of PCM on its end. By size class:

| Class (thickness x width x length, mm) | Fits 57 x 65? | Realistic capacity | Fits under the Pi's depth? |
|---|---|---|---|
| 805060 (8 x 50 x 60) | yes | 2800 to 3250 mAh | yes |
| 905060 (9 x 50 x 60) | yes | 3100 to 3650 mAh | yes |
| 105060 (10 x 50 x 60) | yes | 3500 to 4050 mAh | no, about 1 mm deeper |
| 955565 (9.5 x 55 x 65) | no: 66 to 67 mm long with its PCM | 3950 to 4600 mAh | no |

A true 4000 mAh cell needs about 10 mm of thickness in this footprint. At the Pi's depth the most
the space holds is about 3000 to 3500 mAh.

### Candidates

| Cell | Size with PCM (mm) | Capacity | NTC | Ratings | Connector | Price, 1 piece | Evidence |
|---|---|---|---|---|---|---|---|
| MikroE MIKROE-4474 (805660), DigiKey, 276 in stock | 8.1 x 57.0 x 63.0 max, from its drawing | 3000 mAh minimum | no | 1C charge and discharge (3 A); PCM trips at 3.0 to 4.0 A; OVP 4.28 V | JST-XH, 2-pin | $26 | read: [DigiKey](https://www.digikey.com/en/products/detail/mikroelektronika/MIKROE-4474/13679437), [datasheet](https://download.mikroe.com/documents/datasheets/MLP805660%203000mAh%203.7V.pdf) |
| Bihuade (Liter Energy store) 805060 | about 8 x 50 x 60; PCM inclusion not stated | 3000 mAh | option: JST-PH 3-pin with NTC, value not stated | not stated | JST-PH, 2- or 3-pin | $6.35 | read: [page](https://bihuade.com/products/37v-3000mah-805060-polymer-lithium-lipo-rechargeable-battery-for-gps-psp-dvd-e-book-tablet-pc-power-bank-speaker-camera-pad) |
| GeB 805060, LaskaKit, 81 in stock | 8 x 50 x 60 | 3000 mAh | no | 1C charge, 0.5C discharge (1.5 A, under the 2 A rule) | JST-PH, 2-pin | €8.13 | read: [page](https://www.laskakit.cz/en/geb-lipol-baterie-805060-3000mah-3-7v-jst-ph-2-0/) |
| Easylander 905060, AliExpress | 9 x 50 x 60 nominal | 3500 mAh plausible | third wire offered, value not confirmed | not stated | JST-PH 3-pin option | about $9.69 to $15.69 | snippet: [listing](https://www.aliexpress.us/item/3256812165960549.html) |
| 955060 with PCB, AliExpress | 9.5 x 50 x 60 nominal | 4000 claimed, 3300 to 3850 plausible | not stated | not stated | JST-PH or XH option | $12.55 to $13.05 | search results: [1](https://www.aliexpress.us/item/3256812201363679.html), [2](https://www.aliexpress.us/item/3256812324315768.html) |
| YTKavq 105060, Amazon B08TTR1291 | 10 x 50 x 60 nominal | 3300 mAh | no | not stated | JST-PH, 2-pin | not seen | snippet; its listed 30 g weight is implausible |

The second pass looked only at the 105060 class, for decision 3:

| Cell | Size (mm) | Capacity | NTC | Ratings | Price, 1 piece | Evidence |
|---|---|---|---|---|---|---|
| Bihuade 105063 | "about 63 x 50 x 10"; PCM inclusion not stated | 4000 mAh | option: JST-PH 3-pin with NTC, value not stated | 4.2 V; PCM fitted, thresholds not stated; currents not stated | $9.90, "0 sold", stock not shown | read: [page](https://bihuade.com/products/37v-105063-4000mah) |
| Bihuade 105060 | "about 60 x 50 x 10" | 3500 mAh | same option | same as above | $6.59, "1 sold" | read: [page](https://bihuade.com/products/polymer-lithium-battery-37v-105060-3500mah-mobile-power-led-instrument-flat-panel-universal) |
| YDL 105060 | 10 x 50 x 62 max | 3300 mAh | option: 10 kΩ, B25/50 = 3435 K | 1.65 A discharge, under the 2 A rule; PCM trips at 5 to 9 A; 58 g, light for its rating | $7.02, minimum of 4 | read: [page](https://ydlbattery.com/products/copy-of-ydl-3-7v-3300mah-105060-rechargeable-lipo-battery-with-jst-connector), [datasheet](https://ydlbattery.com/cdn/shop/files/YDL-105060-3300mAh-specification.pdf) |
| Ufine 105063 | not listed | 4000 mAh | no | 4 A charge and discharge; PCM trips at 2.5 to 4.5 A; 74 g | quote only | read: [page](https://www.ufinebattery.com/products/3-7-v-4000mah-lithium-ion-battery-105063/) |

Ufine's 74 g for the same size suggests a real 105063 can hold 4000 mAh. The Bihuade cells come
from Liter Energy's factory store. A Hadex 105565 (64 x 55 x 10 overall, measured at 4493 mAh)
would fit, but its sellers show it out of stock or discontinued.

If the cell's own NTC is not 10 kΩ B3435, a Semitec 103AT-2 (10 kΩ ±1%, B25/85 = 3435 K ±1%)
taped to the cell replaces it: [DigiKey 4316-103AT-2-ND](https://www.digikey.com/en/products/detail/semitec-usa-corp/103AT-2/16579059),
$0.68, read.

### Recommended cell

The Bihuade 105063, 4000 mAh, with the JST-PH 3-pin NTC option. It is the only 4000 mAh cell
found that is sold singly with an NTC fitted. Unconfirmed: its length with the PCM (65 mm is the
limit), the NTC's value and B constant, the pin order, the current ratings and the PCM trip. The
Bihuade 105060, 3500 mAh, is the fallback if the 105063 runs too long: same store, same option,
3 mm shorter.

Near misses:

- 955565 "5000 mAh" cells (Amazon: Meshnology, OCTelect, HXJNLDC; Bihuade with a 3-pin NTC option
  at $7.59): 66 to 67 mm long with the PCM, and about 4000 to 4500 mAh in reality. Snippets.
- AliExpress 905068, 4000 mAh, 3-wire NTC, JST 3-pin, $9.49: 68 mm long. Search results.
- PiShop 755060, 3000 mAh: out of stock. Read.
- LP105065 from lipobattery.us, 4000 mAh with a 10k NTC: made to order, and 65 mm excludes the PCM.
  Snippet.

### Checks when a cell arrives

1. Calipers on thickness, width and length, PCM and tape included; look for swelling.
2. Weight: about 55 to 60 g for a real 3000 mAh 805060, about 70 g for 4000 mAh. Much lighter
   means the capacity is overstated.
3. Open-circuit voltage of 3.7 to 3.9 V, and a 4.2 V label, not 4.35 V.
4. Polarity and pin order at the connector before plugging it in: 3-pin order varies by seller.
5. The NTC reads about 10 kΩ at 25 °C.
6. A capacity test: charge to 4.2 V, discharge at 0.2C to 3.0 V.
7. A 2 to 3 A load test, to confirm the PCM doesn't trip early.

## Runtime

Estimates, not measurements. The backlight figure is from `documentation/PIN_MAPPING.md`; the
Pi's draw is a guess from published Pi Zero 2 W measurements. Usable energy assumes 3.7 V
nominal, 90% of the rated capacity before the fuel gauge shuts down, and 88% boost efficiency.

| Load at 5 V | Light play (NES, GB), mid brightness | Heavy play (SNES, GBA), full brightness and volume |
|---|---|---|
| Pi Zero 2 W | about 1.0 W | about 2.0 W |
| Backlight | about 0.25 W | about 0.43 W |
| Audio, DAC, display | about 0.25 W | about 0.4 W |
| From the cell | about 1.7 W | about 3.2 W |
| 1800 mAh cell | about 3.5 h | about 1.9 h |
| 3000 mAh cell | about 5.9 h | about 3.1 h |
| 3500 mAh cell | about 6.9 h | about 3.6 h |
| 4000 mAh cell | about 7.8 h | about 4.2 h |

Measuring the real draw on the prototype replaces these figures.

## Decisions

1. The target is about 4000 mAh, for 4 hours or more even in demanding games.
2. The cell is bought in stock, not made to order.
3. The case may get about 1 mm deeper for the battery, to take a 105060-class cell, about 10 mm
   thick. The owner chose this on 2026-11-07 over staying at the Pi's depth, which holds only
   about 3000 to 3500 mAh.

## What else uses this

Searches run on `0c61d2f`:

- `git grep -n -i -E "63 ?x ?50|505060|battery (space|envelope|target|area)|60 x 50|6 mm thick|6\.0 mm"`
  finds `README.md:26`, `bom/README.md:23`, `documentation/PIN_MAPPING.md:220`,
  `documentation/PROJECT_PLAN.md:22`, `:88`, `:154`, `:225`, and spec 011's decision 6 and cell
  requirements (`planning/specs/011-POWER-DESIGN.md:38`, `:183`, `:190-192`, `:303`).
- `git grep -n -i -E "63x50|505060|BATTERY" -- pcb/marathon.kicad_pcb` finds the two battery
  labels on B.Fab, and the battery outline is the B.Fab rectangle from (112, 38) to (175, 88).
- `git grep -n -i battery -- .claude` finds `.claude/skills/verify-marathon/features/render.md:24`,
  which only names the battery area in the back render.

## Open questions

1. The Pi's stack depth, about 10.0 mm estimated, until calipers measure the real parts.
2. Which cell: see "Cell search".
