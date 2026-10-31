# render

## Sub-features

Images of what a person sees in KiCad: the schematic sheet, the front (F.Cu, F.SilkS, F.Fab,
Edge.Cuts) and back (B.Cu, B.SilkS, B.Fab, Edge.Cuts, mirrored) of the board, and 3D views of the
top and bottom.

## How to get to it

In KiCad: the Schematic Editor and PCB Editor views, and View, 3D Viewer. On the command line:
`kicad-cli sch export pdf`, `kicad-cli pcb export pdf` and `kicad-cli pcb render`.

## Driving it

```sh
python3 .claude/skills/verify-marathon/verify.py drive --run "$run" --feature render
```

## What proves it works

`PASS drive render`, then open each `head-*.png` beside its `main-*.png` and show the pairs the
change affects inline in the thread. The change must be visible where it was made, and nothing
else should move. Placement and outline changes show on `front` and `back`; the Pi and battery
outlines are on the back Fab layer. The 2D PNGs keep the full sheet, so the board fills only
the top of each image.
