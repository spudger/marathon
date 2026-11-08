# First case concept

- **Status:** draft
- **Issue:** spudger/marathon#27
- **PRs:** none yet
- **Draft:** planning/drafts/README-HERO-RENDER.md
- **Plans:** none yet

## Problem

Phase 5 of `documentation/PROJECT_PLAN.md` needs a case, and none exists. `case/README.md` is a
placeholder. The board's outline, its four M2 case holes, and the stand-in models for the Pi, the
LCD, the switches, and the battery are now in place (spudger/marathon#25), so the case can be fitted
to them. The README still opens with the bare board, and the repo has no social preview image
(the draft this spec grew from).

## Goal

A first case concept, modeled in CadQuery as code, that holds the board and every part on it with
the clearances on record, prints at home without supports, and renders well enough to become the
README's hero image.

It is a concept. The LCD tail, the silicone pads, the Alps switches, the speakers, and the cell
are not in hand, and several of their figures below are assumptions. The case is revised once the
parts arrive; "Provisional figures" lists what each assumption waits on.

## Decisions

From the ask round on 2026-11-07 (spudger/marathon#27):

1. The case prints at home on an FDM printer: 0.4 mm nozzle, PETG or PLA, every part printable
   without supports.
2. Two shells clamp the board, joined by four M2 screws from the back, through the board's case
   holes, into brass heat-set inserts in the front shell.
3. The back is flat, at the battery's 11.3 mm clearance (spec 022) across the whole board. No grips.
4. The screen gets a window over the LCD's active area and a place for a 1 mm clear lens, added
   at assembly.
5. Every button cap is printed: D-pad, ABXY, Start, Select, power, L, and R. They sit on the board's
   current contact and switch positions.
6. Two 15 mm speakers fire out the front, through printed grilles, one below the D-pad and one
   below ABXY.
7. The microSD card is reached only with the back shell off. No hatch.
8. The case assumes the 1.5 mm LCD gap the renders use, and a foam gasket keeps the panel firm if
   it sits lower.
9. Four renders: the assembled case from the front (the README hero) and from the back, an
   exploded view, and a cross section. Also a 1280 x 640 social preview image, which the owner
   uploads.
10. KiCad renders first. Blender is pre-approved if KiCad's renders fall short.
11. The case is black, possibly clear later, with red buttons; gold is the alternative.
12. One PR: this spec first, then the model, the renders, and the docs on the same branch.

Artwork on the case is wanted, but what and where is not decided: **experience open**. The flat back
and the front face stay plain until then.

## Approaches

**Where the case gets the board's geometry.**

- Read it from `pcb/marathon.kicad_pcb` at build time: the outline, the holes, and the position of
  each part the case serves, looked up by reference. A part that moves on the board moves its
  opening with it. **Chosen.**
- Copy the figures into the case code as constants, with a test that fails when the board drifts.
  Two copies of the same numbers, and every layout change becomes a case edit.
- Derive openings from KiCad's STEP export of the board. Works for clearance, but an opening is a
  design choice (a cap, a slot, a grille), not an offset of a part's shape.

The STEP export is still used, as the ground truth for the clearance tests.

**How the board and case are rendered together.** Tried on 2026-11-07 with a rough prototype case:

- `kicad-cli pcb render` on a scratch copy of the board, with the case added as a board-only
  footprint that carries the case's STEP models. Renders in about 3 s with the board's real
  silkscreen and gold pads, through the same sandbox `tools/render/render.py` uses. Each model takes
  its own offset, so the exploded view needs no second tool, and its own opacity, for the lens.
  Black plastic reads flat under the default lights; a near-black of sRGB 0.11 with stronger side
  lights fixes it. **Chosen.**
- Blender with KiCad's GLB export. Better materials, at the cost of a new install and a second
  pipeline. Kept for a final-design hero if the concept's renders are not enough.
- CadQuery with a VTK renderer. No silkscreen or pad finish on the board.

KiCad cannot cut the board, so the cross section is a 2D drawing: CadQuery cuts the case and the
board's STEP export at one y, and matplotlib draws the result with its clearances labeled.

**Where the lens sits.** A recess in the front face would print over air when the front shell
prints face down, its usual orientation. A pocket on the inside of the front plate prints cleanly,
and also keeps the lens from being pried off. **Chosen:** the inside pocket.

## The design

Coordinates are the board's: x and y in mm as in `pcb/marathon.kicad_pcb` (the outline runs from
(20, 20) to (180, 95)), and z up from the board's back surface, so the board's front is z = 1.0.
Every figure here is a starting value for the code, which owns the final geometry.

### Stack

| Level | z (mm) | Source |
|---|---|---|
| Back face of the case | -12.9 | 1.6 mm floor |
| Inside of the back | -11.3 | spec 022's battery clearance |
| Pi's stack, deepest point | about -10.0 to -10.4 | spec 022, estimate |
| Board | 0 to 1.0 | board stackup |
| LCD glass | 5.0 | `tools/render/models.py`, 1.5 mm gap assumed |
| Inside of the front plate, underside of the lens | 5.5 | 0.5 mm over the glass, filled by the gasket |
| Top of the lens | 6.5 | 1.0 mm lens |
| Front face | 7.5 | 1.0 mm over the lens |
| Tops of the caps | 8.5 to 9.0 | 1.0 to 1.5 mm proud |
| Top of the mute switch's actuator | 9.8 | SS12F15-G5 stand-in |

The case body is **20.4 mm** thick and **164.2 x 79.2 mm**, with 8.1 mm corner radii: the board's
outline plus 0.3 mm of clearance and a 1.8 mm wall.

### Shells and fasteners

The shells split at the board's back surface, z = 0. The front shell's wall runs from z = 0 to the
front face, so the board drops into it face down. The inner 0.8 mm of that wall continues 1.5 mm
below the split as a skirt, which fits a matching rebate in the back shell's wall and keeps the long
shells aligned.

At each case hole (25, 25), (175, 25), (25, 90), and (175, 90):

- **Back shell:** a 5.5 mm boss from the floor to the board, with a 2.4 mm clearance hole and a
  counterbore in the back face for the screw head.
- **Front shell:** a 5.5 mm boss from the front plate to the board. A 3.2 mm hole for an M2 x 3 mm
  heat-set insert runs from the boss's end at z = 1.0 to z = 5.0, and the insert is pressed in from
  the board side. A 2.0 mm bore continues to z = 6.0 for the screw tip.
- **Screw:** M2 x 16 mm socket head (DIN 912), seated 2.0 mm deep (z = -10.9), so the head sits
  flush. Its tip reaches z = 5.1, 0.9 mm short of the bore's end.

The board is clamped between the bosses' ends. The 5.5 mm boss leaves about 1.15 mm of wall
around the insert, and the front boss at (175, 90) clears the mute switch's plate by 0.5 mm.

### Front

- **Screen.**
  - window: the LCD's active area (x 67.6 to 132.4, y 27.7 to 76.3) plus 0.5 mm a side,
    65.8 x 49.6 mm;
  - lens pocket: the window plus 3 mm a side, 1.0 mm deep, on the inside of the front plate;
  - lens: 1.0 mm clear acrylic or polycarbonate, 0.1 mm smaller a side than the pocket, held by
    thin double-sided tape;
  - gasket: closed-cell foam on the panel's border, outside the active area, about twice as thick
    as the gap between the lens and the glass, measured at assembly. At the assumed 1.5 mm LCD gap
    that gap is 0.5 mm, so 1.0 mm foam. A panel sitting flat on trimmed pins leaves about 2.0 mm,
    so about 4 mm of stacked foam.
- **Cap flanges.** Every cap has a flange 1.5 mm wider than its body all round, 1.0 mm thick, at
  z 4.5 to 5.5. Its top is flat for 0.75 mm out from the body and bears on the inside of the front
  plate; a 0.75 mm, 45° chamfer runs from there to the flange's edge. The holes clear the bodies by
  0.25 mm a side and have no chamfer, so each flange bears on 0.5 mm of plate all round.
- **D-pad.** One cross cap centered on (43, 53), 29 mm across with 9 mm arms, 1.5 mm proud. The
  pad's domes hold its flange up against the plate. A press on one arm tips the cap about the outer
  edge of the opposite arm's flat bearing face, 15.25 mm from the center. A center nub stops 0.7 mm
  above the pad at rest. When the pressed arm's dome, 27.25 mm from the pivot, bottoms out after its
  1 mm of travel, the nub, 15.25 mm from it, has come down about 0.56 mm and has not landed. A
  press on the middle sinks the cap 0.7 mm onto the nub, short of the 1 mm a contact needs.
- **ABXY.** Four 10 mm round caps, on SW14 to SW17's contacts, 1.5 mm proud.
- **Silicone pads.** Both are the same provisional cross (see "Provisional figures"). Four short
  posts from the front plate press each pad's center onto the board, between the caps.
- **Start and Select.** 8 x 3.5 mm pill caps on SW19 (94, 84) and SW18 (106, 84), 1.0 mm proud,
  each with a stem down to its switch. Their flanges are 1 mm apart.
- **Power key.** A 5 mm round cap on SW1 (24, 78), flush with the front face, so a pocket does not
  press it. The LTC2954 already needs a 1 s hold to turn on.
- **Mute switch.** A slot in the front plate over SW2 (162, 91.5) for its actuator and travel. The
  actuator stands 2.3 mm proud of the face.
- **Speakers.** Each sits in a ring on the inside of the front plate, face against the plate,
  glued in. Grilles are 1.2 mm holes on a hex grid inside an 11 mm circle. Left at (48, 82), right at
  (152, 79), both clear of the pads, the caps, and the front-side parts. Their leads run to J5 and J6.

### Edges

- **USB-C.** J4's receptacle reaches 0.9 mm past the board's edge (KiCad's STEP export: y 89.0 to
  95.9, z 1.0 to 4.26). A notch in the front shell's bottom wall, open at the split and through the
  skirt, lets it pass as the board drops in. A tab on the back shell fills the notch below the
  receptacle, leaving a 9.6 x 3.9 mm opening. A 12.5 x 6.5 mm pocket, 0.6 mm deep, around the
  opening on the outside lets a plug's overmold reach within 0.6 mm of the receptacle's mouth.
- **L and R.** SW20 and SW21 push toward the top edge; their plungers end at y = 21.0. A printed
  shoulder button slides in a slot in the front shell's top wall. A flange inside the wall holds it
  in, and the flange's inner face rests on the plunger. The button stands 1.5 mm proud of the edge.

### Back

The floor is flat at z = -11.3 inside. Over the battery that is spec 022's clearance; over the Pi
it leaves about 0.9 to 1.3 mm. Nothing holds the cell but its adhesive pad, as spec 022 assumes.
The microSD card and the Pi's ports face the inside of the board, so they are reached with the back
shell off.

### Printing

PETG or PLA, 0.4 mm nozzle, 0.2 mm layers. Every part prints without supports:

| Part | Orientation | Why it needs no supports |
|---|---|---|
| Front shell | front face down | the window, grilles, and holes are open at the bed; the lens pocket and bosses face up; the USB-C notch and shoulder slots bridge at most 16 mm |
| Back shell | back face down | the counterbores open at the bed; the bosses face up |
| Caps | top face down | the flange's flat bearing face overhangs the body by only 0.75 mm, and its 45° chamfer takes the rest |
| Shoulder buttons | flat on a side | |

All are black except the caps and shoulder buttons, which are red.

### Hardware

Bought, not printed: four M2 x 16 mm DIN 912 screws, four M2 x 3 mm heat-set inserts, the 1 mm lens,
1 mm closed-cell foam tape for the gasket (stacked for a lower panel), and thin double-sided tape for
the lens.

### Provisional figures

| Figure | Assumed | Replaced by |
|---|---|---|
| Silicone pads | a cross 34 mm across, 9 mm arms, a 20 mm center square, 0.8 mm sheet, domes rising to 3.5 mm off the board, 1 mm of travel | the bought pads (`bom/README.md`) |
| Speakers | 15 mm across, 4.0 mm thick, glued | the bought speakers |
| Mute switch travel | 3 mm, actuator 2.0 x 1.5 mm | the SS12F15-G5 drawing |
| LCD gap and panel | 1.5 mm gap, 2.5 mm panel (`tools/render/models.py`) | the real panel, and the Pi header's trimmed pins |
| Alps switch heights and plunger | the footprints and the stand-in models | the real switches |
| Pi's stack | 10.0 to 10.4 mm (spec 022) | calipers |
| Cell | 10.3 mm with tolerance, 11.3 mm installed (spec 022) | the arrival checks in spec 022 |
| Insert hole | 3.2 mm across, 4.0 mm deep | the insert maker's figure |
| Fit clearances | 0.3 mm board to wall, 0.25 mm a side around caps, 0.15 mm in the skirt | a test print |

## Renders

`case/render.py` writes into `case/renders/`:

| File | View |
|---|---|
| `angle-front.png` | assembled, front, the README hero |
| `angle-back.png` | assembled, back |
| `exploded.png` | the back shell dropped, the front shell, pads, caps, and lens raised, the board in place |
| `section.png` | a cut at y = 53, through the D-pad, the LCD, ABXY, the Pi, and the battery, with the clearances labeled |
| `social-preview.png` | 1280 x 640, front, for the repo's settings |

The 3D views come from `kicad-cli pcb render` on a scratch copy of `pcb/`, with a board-only
footprint carrying the case's STEP models, run in `tools/render/render.py`'s sandbox. `pcb/` is never
written. The section comes from KiCad's STEP export of the board, cut in CadQuery.

## Code and files

| Path | What it is |
|---|---|
| `case/board.py` | Reads the outline, the case holes, and part positions from `pcb/marathon.kicad_pcb` |
| `case/case.py` | Builds every part and writes `case/step/marathon-case.step` (the assembly, for FreeCAD or any CAD tool) and one STL per printed part in `case/stl/` |
| `case/render.py` | Writes the renders |
| `case/tests/` | The tests in "Finish condition" |

Each runs through uv, as the stand-in models do, pinned to Python 3.12: CadQuery 2.5.2 has no
wheels for the 3.14 uv now picks by default, so the command in `tools/render/README.md` fails as
written.

## Risks and known limits

- **Heat.** The case has no vents. The Pi Zero 2 W throttles when hot; measure it on the prototype.
- **USB-C plugs.** The receptacle's mouth sits 1.2 mm in from the wall's outer face, 0.6 mm past
  the pocket. Plugs with short shells or wide overmolds may not seat; try several cables.
- **Inserts in thin bosses.** About 1.15 mm of wall can bulge as an insert goes in. Use a guide
  tip and a light touch, or thread-forming screws if a boss splits.
- **Two parts have no 3D model.** KiCad's library has none for B1 and U7, so the clearance test
  cannot see them. Both are on the back, low, and far from the case: B1 sits beside the cell, which
  is taller, and U7 is a 0.75 mm package.
- **The model is only as good as the stand-ins,** which `tools/render/README.md` says not to trust
  to a fraction of a millimeter.

## Changes

One PR, on this spec's branch, through the build flow:

1. **Case.** `case/board.py`, `case/case.py`, and `case/render.py`, their tests, and their outputs:
   the STEP assembly, the STLs, and the renders.
2. **README.** The hero image becomes `case/renders/angle-front.png`. The status list, the phases
   table, the repository layout, and the case row say the concept exists.
3. **Docs.** `case/README.md` covers the build, the renders, printing, the hardware, and assembly
   order. `documentation/PROJECT_PLAN.md`'s case row, Phase 5, Tools table, and "Case design" risk,
   and `bom/README.md`'s case rows and hardware, match this spec.
4. **The uv command.** `tools/render/README.md`, `tools/render/models.py`, and
   `tools/render/tests/test_models.py` add `--python 3.12`.
5. **This spec** becomes `approved` before the build and `built` when the PR merges.

## Finish condition

- No case part overlaps any part in KiCad's STEP export of the board, or another case part, by more
  than 0.01 mm³.
- No case part enters spec 022's battery space: x 112 to 179, y 28 to 87, z -11.3 to 0.
- Each cap comes within 0.2 mm of what it presses: its switch's actuator, or its pad's dome. Each
  shoulder button's flange comes within 0.2 mm of its plunger.
- The first check also holds through each part's motion: the D-pad tipped about each arm until its
  dome has traveled 1 mm, and each other cap and each shoulder button pressed through its switch's
  or dome's travel. The actuator, plunger, or dome a part presses is left out of this check, since
  the real one moves with it; the switch's body stays in. The mute switch's actuator, modeled on its
  own from the stand-in's figures, is checked against its slot at both ends of its travel.
- The case body measures 164.2 x 79.2 x 20.4 mm.
- Every printed part is one valid closed solid, and its STL is written.
- The renders exist, and each shows what its row in "Renders" says, checked by eye.
- The existing tests in `tools/render/tests` still pass.
- A test print is inconclusive here: the owner prints the parts and records the fit.

## What else uses this

Searches run on `e38a91c`, leaving out this spec:

- `git grep -n -i -E "freecad|openscad|cadquery|case/|3d.print|phase 5|case design"` finds
  `README.md:92`, `:112`, `:117`, and `:137`, `bom/README.md:86`, `:130`, and `:152` (a dated
  decision, which stays), `case/README.md:3` to `:9`, `documentation/PROJECT_PLAN.md:25`, `:164`
  to `:170`, and `:229`, and the uv commands in `tools/render/README.md:21` and `:35`,
  `tools/render/models.py:3`, and `tools/render/tests/test_models.py:3`. It also finds
  `documentation/PROJECT_PLAN.md:9`, which only lists the phases, and spec 022's change list at
  `planning/specs/022-BATTERY-SPACE.md:239`, which is history. Neither changes.
- `git grep -n -E "angle-front|hero|social preview"` finds the README's hero at `README.md:7`.
  `pcb/README.md:22`, `tools/render/README.md:16`, `tools/render/render.py:30`, and
  `tools/render/tests/test_render.py:56` name the board's own renders, which stay.
- `git grep -n "LCD over the Pi header" -- documentation` finds the risk at
  `documentation/PROJECT_PLAN.md:227`. It stays open: decision 8 designs around it.

## Open questions

1. **Experience open:** the artwork on the case, and where it goes.
2. Red or gold caps, and black or clear shells. The renders use black and red.
