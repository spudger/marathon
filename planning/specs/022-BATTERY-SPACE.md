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

Grow the battery space so it takes an in-stock cell of about 4000 mAh, without making the case
thicker than the rear-mounted Pi already makes it, and pick that cell.

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
flat. Open: the Pi's stack depth, from the official mechanical drawing and then calipers on the
real board.

## Cell requirements

Spec 011's requirements stand, except the size:

| Requirement | Value |
|---|---|
| Size, including PCM and tolerance | at most 57 x 65 mm, no thicker than the Pi's stack depth |
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

Started 2026-11-07.

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
| 4000 mAh cell | about 7.8 h | about 4.2 h |

Measuring the real draw on the prototype replaces these figures.

## Decisions

1. The target is about 4000 mAh, for 4 hours or more even in demanding games.
2. The cell is bought in stock, not made to order.
3. The case does not get thicker for the battery: the cell is no thicker than the Pi's stack.

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

1. The Pi's stack depth, which sets the cell's maximum thickness.
2. Which cell: see "Cell search".
