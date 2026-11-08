"""Build the stand-in 3D models for the Marathon board's project footprints.

    uv run --no-project --with cadquery==2.5.2 python tools/render/models.py

Writes one STEP file per part into pcb/Marathon.3dshapes/. These are simple shapes for renders and
case fitting, not vendor models: outlines come from the footprints and the specs, and heights
come from the datasheets where the comment says so, otherwise they are estimates.

Each model is in its footprint's frame, as KiCad expects: millimetres, origin at the footprint
origin, x right, y up (footprint y down is model -y), z out of the board surface the footprint
sits on. KiCad flips models on back-side footprints.
"""

import sys
from pathlib import Path

import cadquery as cq

OUT = Path(__file__).resolve().parents[2] / 'pcb' / 'Marathon.3dshapes'

def srgb(r, g, b):
    """A color from sRGB values, the space STEP files and KiCad use. cq.Color takes linear values
    and the STEP writer converts them back to sRGB."""
    def linear(c):
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return cq.Color(linear(r), linear(g), linear(b))


BLACK = srgb(0.08, 0.08, 0.08)
SILVER = srgb(0.55, 0.56, 0.58)
GOLD = srgb(0.85, 0.65, 0.20)
PI_GREEN = srgb(0.08, 0.42, 0.20)
NYLON = srgb(0.93, 0.93, 0.90)
GLASS = srgb(0.10, 0.10, 0.11)
SCREEN = srgb(0.02, 0.02, 0.03)
PANEL_BACK = srgb(0.62, 0.62, 0.62)
FLEX = srgb(0.80, 0.45, 0.05)
POUCH = srgb(0.58, 0.60, 0.64)
KAPTON = srgb(0.90, 0.68, 0.10)


def box(x0, x1, y0, y1, z0, z1):
    """An axis-aligned box from its corner coordinates."""
    return cq.Workplane().box(x1 - x0, y1 - y0, z1 - z0, centered=False).translate((x0, y0, z0))


def assembly(name, parts):
    assy = cq.Assembly(name=name)
    for i, (shape, color) in enumerate(parts):
        assy.add(shape, name=f'{name}_{i}', color=color)
    return assy


def sktha():
    """Alps SKTHACE010 top-push switch, 3.5 x 3.2 x 1.8 mm (Alps datasheet, via the footprint)."""
    parts = [
        (box(-1.75, 1.75, -1.6, 1.6, 0, 0.6), BLACK),
        (box(-1.75, 1.75, -1.6, 1.6, 0.6, 1.0), SILVER),
        (cq.Workplane().circle(0.8).extrude(0.8).translate((0, 0, 1.0)), BLACK),
    ]
    for sx in (-1, 1):
        for y in (-0.65, 0.65):
            x0, x1 = sorted((sx * 1.75, sx * 2.3))
            parts.append((box(x0, x1, y - 0.3, y + 0.3, 0, 0.2), SILVER))
    return assembly('SW_Alps_SKTHACE010_StandIn', parts)


def sksc():
    """Alps SKSCLDE010 side-push switch, 3.5 x 3.55 x 1.25 mm (Alps datasheet, via the footprint).

    The plunger points to model -y, footprint +y, where the footprint's silkscreen marks it.
    """
    parts = [
        (box(-1.75, 1.75, -1.775, 1.775, 0, 0.5), BLACK),
        (box(-1.75, 1.75, -1.775, 1.775, 0.5, 1.25), SILVER),
        (box(-0.7, 0.7, -2.475, -1.775, 0.25, 0.95), BLACK),
    ]
    for sx in (-1, 1):
        for y in (-0.65, 0.65):
            x0, x1 = sorted((sx * 1.75, sx * 2.4))
            parts.append((box(x0, x1, y - 0.3, y + 0.3, 0, 0.2), SILVER))
    return assembly('SW_Alps_SKSCLDE010_StandIn', parts)


def ss12f15():
    """SS12F15-G5 slide switch on its 19.5 x 5.6 mm mounting plate (footprint outline).

    Body and actuator sizes are estimates; G5 is the 5 mm actuator.
    """
    plate = box(-9.75, 9.75, -2.8, 2.8, 0, 0.3)
    for x in (-7.5, 7.5):
        plate = plate.cut(cq.Workplane().circle(1.1).extrude(1).translate((x, 0, -0.5)))
    parts = [
        (plate, SILVER),
        (box(-5, 5, -2.2, 2.2, 0.3, 3.8), BLACK),
        (box(-1, 1, -0.75, 0.75, 3.8, 8.8), BLACK),
    ]
    return assembly('SS12F15_G5_StandIn', parts)


def lcd():
    """3.2 inch ILI9341 bare panel, in J2's frame (J2, the flex tail, sits at board (100, 78)).

    The body and active area are the board's F.Fab outlines: body x 61.3 to 138.7, y 25 to 79;
    active area x 67.6 to 132.4, y 27.7 to 76.3. The panel thickness is an estimate. The panel
    sits 1.5 mm off the board, an assumed gap, to clear the Pi header's pin tails, which come
    through the front under its top edge.
    """
    z0, z1, z2 = 1.5, 3.6, 3.95
    parts = [
        (box(-38.7, 38.7, -1, 53, z0, z1), PANEL_BACK),
        (box(-38.7, 38.7, -1, 53, z1, z2), GLASS),
        (box(-32.4, 32.4, 1.7, 50.3, z2, 4.0), SCREEN),
        # The flex tail leaves the panel's bottom edge and folds back under it to the pads.
        (box(-7.6, 7.6, -1.5, -1.0, 0.12, z0 + 1.0), FLEX),
        (box(-7.6, 7.6, -1.5, 1.2, 0, 0.12), FLEX),
    ]
    return assembly('LCD_3.2in_ILI9341_StandIn', parts)


def pi():
    """Raspberry Pi Zero 2 W on 5 mm standoffs, component side outward, in J1's frame.

    J1 sits on the back of the board, so z is away from the back surface. The Pi's board is the
    footprint's inner F.Fab outline, x -4.77 to 25.23 and y -8.37 to 56.63: the GPIO header runs
    along x = -1.27, the ports along the x = 25.23 edge, and the microSD end is y = -8.37. Port
    centres are from the Raspberry Pi Zero 2 W mechanical drawing (mini-HDMI 12.4 mm, micro USB
    41.4 and 54 mm from the SD end). The board thickness, the other parts' sizes and positions,
    and the heights are estimates, set so the stack is about 10.0 mm deep, as spec 022 finds.
    """
    x_edge, y_sd = 25.23, -8.37  # port edge and SD end of the Pi's board

    def at(xs0, xs1, ys0, ys1, z0, z1):
        """A box placed by distance along the Pi from the SD end (xs) and in from the port edge (ys)."""
        return box(x_edge - ys1, x_edge - ys0, y_sd + xs0, y_sd + xs1, z0, z1)

    holes = [(-1.27, -4.87), (-1.27, 53.13), (21.73, -4.87), (21.73, 53.13)]
    base, top = 5.0, 6.2
    pcb = (cq.Workplane().box(30, 65, top - base, centered=False)
           .edges('|Z').fillet(3).translate((-4.77, -8.37, base)))
    for x, y in holes:
        pcb = pcb.cut(cq.Workplane().circle(1.375).extrude(3).translate((x, y, base - 1)))
    parts = [(pcb, PI_GREEN)]
    for x, y in holes:
        standoff = cq.Workplane().polygon(6, 5.0).extrude(base).translate((x, y, 0))
        standoff = standoff.cut(cq.Workplane().circle(1.25).extrude(base + 2).translate((x, y, -1)))
        parts.append((standoff, NYLON))
    parts += [
        (at(6.8, 18.0, -0.5, 7.0, top, 10.0), SILVER),     # mini-HDMI
        (at(37.65, 45.15, -1.0, 4.5, top, 8.8), SILVER),   # micro USB, data
        (at(50.25, 57.75, -1.0, 4.5, top, 8.8), SILVER),   # micro USB, power
        (at(1.0, 13.0, 9.5, 21.0, top, 7.6), SILVER),      # microSD slot
        (at(-2.5, 1.0, 10.0, 20.5, top, 7.2), BLACK),      # microSD card
        (at(19.5, 34.5, 8.5, 22.5, top, 7.5), SILVER),     # RP3A0 shield
        (at(60.5, 64.5, 7.0, 23.0, top, 7.4), BLACK),      # camera connector
    ]
    # Long-tail 2x20 header: the plastic spacer sits between the boards; the pins pass through
    # both, 1.2 mm proud of the main board's front (main board 1.0 mm, so z -2.2) and of the Pi.
    parts.append((box(-2.54 - 1.27, 1.27, -1.27, 48.26 + 1.27, 0, 2.5), BLACK))
    pins = None
    for row in (0, -2.54):
        for i in range(20):
            pin = box(row - 0.32, row + 0.32, i * 2.54 - 0.32, i * 2.54 + 0.32, -2.2, top + 1.5)
            pins = pin if pins is None else pins.union(pin)
    parts.append((pins, GOLD))
    return assembly('RaspberryPi_Zero_2W_StandIn', parts)


def battery():
    """LiPo cell, Bihuade 105063: 10 x 50 x 63 mm (bom/README.md's provisional pick).

    The protection board end is the kapton-wrapped 4 mm at model -x, so it faces B1, the battery
    connector, at the cell's left end. KiCad flips a back-side model across the board's x axis,
    so model x stays board x.
    """
    pouch = box(-27.5, 31.5, -25, 25, 0, 10).edges('|X or |Y').fillet(1.0)
    parts = [
        (pouch, POUCH),
        (box(-31.5, -27.5, -23, 23, 0.5, 9.5), KAPTON),
    ]
    return assembly('Battery_LiPo_105063_StandIn', parts)


MODELS = {
    'SW_Alps_SKTHACE010_StandIn': sktha,
    'SW_Alps_SKSCLDE010_StandIn': sksc,
    'SS12F15_G5_StandIn': ss12f15,
    'LCD_3.2in_ILI9341_StandIn': lcd,
    'RaspberryPi_Zero_2W_StandIn': pi,
    'Battery_LiPo_105063_StandIn': battery,
}

def write_all(out: Path = OUT) -> None:
    """Write every model. OpenCASCADE orders a file's color records differently on each run, so a
    rebuild rewrites every file even when no shape changed."""
    out.mkdir(parents=True, exist_ok=True)
    for name, build in MODELS.items():
        path = out / f'{name}.step'
        build().export(str(path), exportType='STEP')
        print(f'wrote {path}')


if __name__ == '__main__':
    write_all(Path(sys.argv[1]) if len(sys.argv) > 1 else OUT)
