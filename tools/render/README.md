# Board renders

Renders of the Marathon board, and the stand-in 3D models they need.

| File | What it does |
|------|--------------|
| `render.py` | Renders the board from four fixed views into `pcb/renders/` |
| `models.py` | Builds the stand-in models in `pcb/Marathon.3dshapes/` |

## Render

```bash
python3 tools/render/render.py
```

Needs the `org.kicad.KiCad` Flatpak. It runs `kicad-cli` sandboxed, with no network, `pcb/` read-only, and a throwaway KiCad config. It writes `top.png` and `bottom.png` on a transparent background, plus `angle-front.png` and `angle-back.png` with a floor and shadows. Each is 1920 x 1200. The board uses its stackup colors: black mask, ENIG (gold) pads, and white silkscreen. Rerun it after any layout change and commit the images.

## Stand-in models

```bash
uv run --no-project --python 3.12 --with cadquery==2.5.2 python tools/render/models.py
```

The Raspberry Pi Zero 2 W, the LCD, the Alps switches, the slide switch, and the battery have no 3D models in KiCad's library, so these are simple shapes, not vendor models. Outlines come from the footprints and the specs. The Pi's port positions come from its mechanical drawing. Thicknesses and the other Pi parts are estimates; each function's docstring says which. They're good enough for renders and for fitting the case. Don't use them to check clearances to a fraction of a millimeter.

The battery is a board-only footprint, BT1, so it carries a model without entering the schematic, the BOM, or the placement file. The LCD sits 0.5 mm off the board, on the Pi header's pins, which are trimmed to about 0.3 mm on the front and covered in Kapton tape (spec 027).

A rebuild rewrites every STEP file, even with no change, because OpenCASCADE orders a file's color records differently on each run. Commit the models only when a shape changes.

## Tests

```bash
python3 -m unittest discover -s tools/render/tests -p 'test_board.py'
python3 -m unittest discover -s tools/render/tests -p 'test_render.py'
uv run --no-project --python 3.12 --with cadquery==2.5.2 python -m unittest discover -s tools/render/tests -p 'test_models.py'
```
