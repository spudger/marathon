"""Build the Marathon case concept (planning/specs/027-CASE-CONCEPT.md).

    uv run --no-project --python 3.12 --with cadquery==2.5.2 python case/case.py

Writes the assembly as case/step/marathon-case.step and each printed part as an STL in case/stl/,
standing in its print orientation. Positions come from pcb/marathon.kicad_pcb through board.py.

Coordinates are the case's, as KiCad's STEP export of the board has them: x is the board's x, y is
minus the board's y, and z rises from the board's back surface, so the board's front is z = 1.0.
Helpers take board coordinates (y down) and convert. Figures marked provisional wait on real
parts; spec 027's "Provisional figures" says what replaces each.
"""

import math
import sys
from dataclasses import dataclass
from pathlib import Path

import cadquery as cq

import board

HERE = Path(__file__).resolve().parent

# The stack, z in mm (spec 027, "Stack").
BOARD_TOP = 1.0          # the board's front
BACK = -12.5             # back face of the case: a 1.2 mm floor
BACK_IN = -11.3          # inside of the back: spec 022's battery clearance
PLATE_IN = 4.5           # inside of the front plate, underside of the lens
LENS = 0.5               # lens thickness; the lens pocket's depth
FRONT = 6.0              # front face
GLASS = 3.95             # top of the LCD's glass outside the active area (tools/render/models.py)
PLATE_MIN = 0.8          # the plate left over the pockets in its inside
RELIEF_TOP = FRONT - PLATE_MIN   # ceiling of the pockets over the cap flanges and the speakers

# Walls and fits (spec 027, "Shells and fasteners" and "Provisional figures").
CLEAR = 0.3              # board edge to the inside of the wall
WALL = 1.8
SKIRT = 1.5              # how far the front shell's skirt reaches below the split at z = 0
SKIRT_T = 0.8
SKIRT_GAP = 0.15
CAP_CLEAR = 0.25         # around each cap, a side

# Fasteners.
BOSS_R = 2.75            # 5.5 mm bosses
INSERT_R, INSERT_TOP = 1.6, 4.5     # M2 x 3 mm heat-set insert hole, from the boss's end
BORE_R, BORE_TOP = 1.0, RELIEF_TOP  # past the M2 x 12 mm screw's tip, at z 4.0
SCREW_R, HEAD_R, HEAD_DEPTH = 1.2, 2.0, 4.5   # the head seats at z -8.0

# Caps (spec 027, "Front").
CAP_TOP_FACE = FRONT + 1.5    # D-pad and ABXY, 1.5 mm proud
CAP_TOP_PILL = FRONT + 1.0    # Start and Select, 1.0 mm proud
# Flanges sit on the domes (DOME_TOP) and bear on the ceiling of a pocket in the plate.
FLANGE_GROW, FLANGE_BOTTOM, FLANGE_TOP, CHAMFER = 1.5, 4.5, RELIEF_TOP, 0.5
SWITCH_TOP = BOARD_TOP + 1.8   # Alps SKTHACE010, 1.8 mm tall (datasheet, via the footprint)
STEM_GAP, STEM_R = 0.1, 1.0
NUB_GAP, NUB_R = 0.7, 1.5

# Silicone pads, provisional: a cross 34 mm across with 9 mm arms and a 20 mm center square,
# a 0.8 mm sheet, and domes rising to 3.5 mm off the board.
PAD_SPAN, PAD_ARM, PAD_CENTER, PAD_SHEET, DOME_TOP = 34.0, 9.0, 20.0, 0.8, BOARD_TOP + 3.5
POST_OFFSET, POST_R = 7.5, 1.25

# Speakers, provisional: 15 mm across, 4.0 mm thick, in rings on the front plate.
SPEAKER_R, SPEAKER_T = 7.5, 4.0
SPEAKERS = {'speaker-l': (48, 82), 'speaker-r': (150, 80)}
RING_IN, RING_WALL, RING_BOTTOM = 7.7, 1.0, 2.5
GRILLE_HOLE_R, GRILLE_PITCH, GRILLE_R = 0.6, 2.0, 5.5

# The LCD, from J2's position and tools/render/models.py.
ACTIVE = (-32.4, 32.4, -50.3, -1.7)      # x0, x1, y0, y1 from J2, board y
GLASS_OUTLINE = (-38.7, 38.7, -53.0, 1.0)
WINDOW_GROW, POCKET_GROW, LENS_GAP = 0.5, 3.0, 0.1

# Mute switch, provisional: a 2.0 x 1.5 mm actuator with 3 mm of travel.
MUTE_SLOT = (2.0 + 3.0 + 0.6, 1.5 + 0.6)
MUTE_BODY = (10.0, 4.4)                  # its body reaches z 4.8, above the plate's inside

# USB-C: J4's receptacle from KiCad's STEP export: 8.94 mm wide, z 1.0 to 4.26.
USB_HALF_W, USB_TOP, USB_TAB_TOP = 4.47, 4.26, 0.7
USB_POCKET = (12.5, 6.0, 0.6)            # width, height, depth

# Shoulder buttons: the plungers end at board y 21.02 (KiCad's STEP export).
SHOULDER_W, SHOULDER_FLANGE_W = 14.0, 18.0
SHOULDER_Z, SHOULDER_FLANGE_Z = (1.3, 4.2), (1.1, 4.4)   # under the plate's inside
SHOULDER_PROUD, SHOULDER_FLANGE_IN = 1.5, 20.9


def srgb(r, g, b, a=1.0):
    """A color from sRGB values, the space STEP files and KiCad use (as tools/render/models.py)."""
    def linear(c):
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return cq.Color(linear(r), linear(g), linear(b), a)


BLACK = srgb(0.11, 0.11, 0.12)
RED = srgb(0.78, 0.08, 0.08)
RUBBER = srgb(0.35, 0.35, 0.37)
SPEAKER = srgb(0.20, 0.20, 0.22)
FOAM = srgb(0.15, 0.15, 0.15)
CLEAR_LENS = srgb(0.04, 0.05, 0.06)  # rendered nearly transparent; dark, so the screen reads black


@dataclass
class Part:
    name: str
    shape: cq.Shape
    color: cq.Color
    kind: str                     # 'printed', 'bought', or 'stand-in'
    stl: str = None               # the STL it prints from, for printed parts
    print_shape: cq.Shape = None  # one copy, standing on the bed
    sheet: cq.Shape = None        # a pad's sheet without its domes


def solid(wp):
    """The single solid a workplane holds."""
    s = wp.val() if isinstance(wp, cq.Workplane) else wp
    solids = s.Solids()
    if len(solids) != 1:
        raise ValueError(f'expected one solid, got {len(solids)}')
    return solids[0]


def rbox(x0, x1, y0, y1, z0, z1, r=0.0):
    """A box from board coordinates, with its vertical edges rounded to r."""
    wp = cq.Workplane().center((x0 + x1) / 2, -(y0 + y1) / 2).rect(x1 - x0, y1 - y0)
    wp = wp.extrude(z1 - z0)
    if r:
        wp = wp.edges('|Z').fillet(r)
    return wp.translate((0, 0, z0))


def cylinder(x, y, r, z0, z1):
    return cq.Workplane().center(x, -y).circle(r).extrude(z1 - z0).translate((0, 0, z0))


class Outline:
    """The board's outline, grown by an offset."""

    def __init__(self, pcb):
        self.pcb = pcb

    def slab(self, grow, z0, z1):
        p = self.pcb
        return rbox(p.x0 - grow, p.x1 + grow, p.y0 - grow, p.y1 + grow, z0, z1, p.radius + grow)


def prism(outline, grow, z0, z1):
    """A 2D outline, grown by grow, extruded from z0 to z1."""
    return outline(grow).extrude(z1 - z0).translate((0, 0, z0))


def cross_outline(x, y, span, arm):
    """A cross of two span x arm bars, with 1.5 mm convex corners, as a function of growth."""
    s, a = span / 2 - 1.5, arm / 2 - 1.5
    pts = [(a, s), (a, a), (s, a), (s, -a), (a, -a), (a, -s), (-a, -s), (-a, -a), (-s, -a),
           (-s, a), (-a, a), (-a, s)]

    def outline(grow):
        return cq.Workplane().center(x, -y).polyline(pts).close().offset2D(1.5 + grow, 'arc')
    return outline


def circle_outline(x, y, r):
    return lambda grow: cq.Workplane().center(x, -y).circle(r + grow)


def pill_outline(x, y, length, width):
    return lambda grow: cq.Workplane().center(x, -y).slot2D(length + 2 * grow, width + 2 * grow)


def cap(outline, top, stem=None, nub=None):
    """A cap: its body through the plate, a chamfered flange under it, and a stem or a nub.

    stem is (x, y) of the switch it presses; nub is (x, y) of the D-pad's center.
    """
    body = prism(outline, 0, FLANGE_BOTTOM, top).edges('>Z').fillet(0.6 if top > FRONT else 0.4)
    flange = prism(outline, FLANGE_GROW, FLANGE_BOTTOM, FLANGE_TOP).edges('>Z').chamfer(CHAMFER)
    shape = body.union(flange)
    if stem:
        shape = shape.union(cylinder(*stem, STEM_R, SWITCH_TOP + STEM_GAP, FLANGE_BOTTOM))
    if nub:
        shape = shape.union(cylinder(*nub, NUB_R, BOARD_TOP + PAD_SHEET + NUB_GAP, FLANGE_BOTTOM))
    return solid(shape)


def contacts(pcb, refs):
    pts = [pcb.at(r) for r in refs]
    return pts, (sum(p[0] for p in pts) / 4, sum(p[1] for p in pts) / 4)


def pad(center, dome_pts):
    cx, cy = center
    sheet = (rbox(cx - PAD_SPAN / 2, cx + PAD_SPAN / 2, cy - PAD_ARM / 2, cy + PAD_ARM / 2,
                  BOARD_TOP, BOARD_TOP + PAD_SHEET, 1.0)
             .union(rbox(cx - PAD_ARM / 2, cx + PAD_ARM / 2, cy - PAD_SPAN / 2, cy + PAD_SPAN / 2,
                         BOARD_TOP, BOARD_TOP + PAD_SHEET, 1.0))
             .union(rbox(cx - PAD_CENTER / 2, cx + PAD_CENTER / 2, cy - PAD_CENTER / 2,
                         cy + PAD_CENTER / 2, BOARD_TOP, BOARD_TOP + PAD_SHEET, 1.0)))
    z0 = BOARD_TOP + PAD_SHEET
    domes = [cq.Solid.makeCone(3.0, 1.5, DOME_TOP - z0, cq.Vector(x, -y, z0)) for x, y in dome_pts]
    whole = sheet.val()
    for d in domes:
        whole = whole.fuse(d)
    return solid(whole.clean()), solid(sheet)


def posts(center):
    cx, cy = center
    shape = None
    for sx in (-1, 1):
        for sy in (-1, 1):
            c = cylinder(cx + sx * POST_OFFSET, cy + sy * POST_OFFSET, POST_R,
                         BOARD_TOP + PAD_SHEET, PLATE_IN + 0.1)
            shape = c if shape is None else shape.union(c)
    return shape


def grille(x, y):
    """Holes on a hex grid inside a circle, through the front plate."""
    holes = None
    rows = int(GRILLE_R / (GRILLE_PITCH * math.sqrt(3) / 2)) + 1
    for j in range(-rows, rows + 1):
        dy = j * GRILLE_PITCH * math.sqrt(3) / 2
        shift = GRILLE_PITCH / 2 if j % 2 else 0.0
        for i in range(-6, 7):
            dx = i * GRILLE_PITCH + shift
            if math.hypot(dx, dy) <= GRILLE_R - GRILLE_HOLE_R:
                h = cylinder(x + dx, y + dy, GRILLE_HOLE_R, PLATE_IN - 0.1, FRONT + 0.1)
                holes = h if holes is None else holes.union(h)
    return holes


def lcd(pcb):
    jx, jy = pcb.at('J2')
    ax0, ax1, ay0, ay1 = ACTIVE
    window = (jx + ax0 - WINDOW_GROW, jx + ax1 + WINDOW_GROW,
              jy + ay0 - WINDOW_GROW, jy + ay1 + WINDOW_GROW)
    pocket = (window[0] - POCKET_GROW, window[1] + POCKET_GROW,
              window[2] - POCKET_GROW, window[3] + POCKET_GROW)
    gx0, gx1, gy0, gy1 = GLASS_OUTLINE
    glass = (jx + gx0, jx + gx1, jy + gy0, jy + gy1)
    return window, pocket, glass


def usb_pocket(pcb):
    x, _ = pcb.at('J4')
    w, h, d = USB_POCKET
    zc = (BOARD_TOP + USB_TOP) / 2
    outer = pcb.y1 + CLEAR + WALL
    return (cq.Workplane().box(w, d + 1, h).edges('|Y').fillet(1.5)
            .translate((x, -(outer - d + (d + 1) / 2), zc)))


def front_shell(pcb, outline, holes):
    shell = outline.slab(CLEAR + WALL, 0, FRONT).edges('>Z').fillet(1.0)
    shell = shell.cut(outline.slab(CLEAR, -1, PLATE_IN))
    skirt = outline.slab(CLEAR + SKIRT_T, -SKIRT, 0).cut(outline.slab(CLEAR, -SKIRT - 1, 1))
    shell = shell.union(skirt)

    window, pocket, _ = lcd(pcb)
    shell = shell.cut(rbox(*window, PLATE_IN - 1, FRONT + 1, 1.0))
    shell = shell.cut(rbox(*pocket, PLATE_IN - 1, PLATE_IN + LENS, 2.0))

    for x, y in pcb.holes:
        shell = shell.union(cylinder(x, y, BOSS_R, BOARD_TOP, PLATE_IN + 0.1))
        shell = shell.cut(cylinder(x, y, INSERT_R, BOARD_TOP - 0.1, INSERT_TOP))
        shell = shell.cut(cylinder(x, y, BORE_R, INSERT_TOP - 0.1, BORE_TOP))

    for outline_fn in holes:
        shell = shell.cut(prism(outline_fn, CAP_CLEAR, PLATE_IN - 1, FRONT + 1))
        shell = shell.cut(prism(outline_fn, FLANGE_GROW + CAP_CLEAR, PLATE_IN - 1, FLANGE_TOP))

    for refs in (('SW10', 'SW11', 'SW12', 'SW13'), ('SW14', 'SW15', 'SW16', 'SW17')):
        shell = shell.union(posts(contacts(pcb, refs)[1]))

    for x, y in SPEAKERS.values():
        ring = (cylinder(x, y, RING_IN + RING_WALL, RING_BOTTOM, PLATE_IN + 0.1)
                .cut(cylinder(x, y, RING_IN, RING_BOTTOM - 1, PLATE_IN + 1)))
        shell = shell.union(ring).cut(cylinder(x, y, RING_IN, PLATE_IN - 1, RELIEF_TOP))
        shell = shell.cut(grille(x, y))

    mx, my = pcb.at('SW2')
    length, width = MUTE_SLOT
    shell = shell.cut(rbox(mx - length / 2, mx + length / 2, my - width / 2, my + width / 2,
                           PLATE_IN - 1, FRONT + 1, 0.5))
    bx, by = MUTE_BODY
    shell = shell.cut(rbox(mx - bx / 2 - CLEAR, mx + bx / 2 + CLEAR, my - by / 2 - CLEAR,
                           my + by / 2 + CLEAR, PLATE_IN - 1, RELIEF_TOP))

    # USB-C: a notch open at the split, through the skirt, so the receptacle passes as the board
    # drops in; the back shell's tab fills it below the receptacle.
    ux, _ = pcb.at('J4')
    shell = shell.cut(rbox(ux - USB_HALF_W - CLEAR, ux + USB_HALF_W + CLEAR, pcb.y1 + 0.1,
                           pcb.y1 + CLEAR + WALL + 1, -SKIRT - 0.1, USB_TOP + CLEAR))
    shell = shell.cut(usb_pocket(pcb))

    # Slots for the shoulder buttons in the top wall.
    for ref in ('SW20', 'SW21'):
        sx, _ = pcb.at(ref)
        half = SHOULDER_W / 2 + CAP_CLEAR
        shell = shell.cut(rbox(sx - half, sx + half, pcb.y0 - CLEAR - WALL - 1, pcb.y0 - 0.1,
                               SHOULDER_Z[0] - CAP_CLEAR, SHOULDER_Z[1] + CAP_CLEAR))
    return solid(shell.clean())


def back_shell(pcb, outline):
    shell = outline.slab(CLEAR + WALL, BACK, 0).edges('<Z').fillet(1.0)
    shell = shell.cut(outline.slab(CLEAR, BACK_IN, 1))
    shell = shell.cut(outline.slab(CLEAR + SKIRT_T + SKIRT_GAP, -SKIRT - SKIRT_GAP, 1))
    for x, y in pcb.holes:
        shell = shell.union(cylinder(x, y, BOSS_R, BACK_IN - 0.1, 0))
        shell = shell.cut(cylinder(x, y, SCREW_R, BACK - 1, 0.5))
        shell = shell.cut(cylinder(x, y, HEAD_R, BACK - 1, BACK + HEAD_DEPTH))
    ux, _ = pcb.at('J4')
    tab = USB_HALF_W + CLEAR - SKIRT_GAP  # the notch's half-width, less the fit
    shell = shell.union(rbox(ux - tab, ux + tab,
                             pcb.y1 + CLEAR, pcb.y1 + CLEAR + WALL,
                             -SKIRT - SKIRT_GAP - 0.1, USB_TAB_TOP))
    shell = shell.cut(usb_pocket(pcb))
    return solid(shell.clean())


def shoulder(pcb, ref):
    x, _ = pcb.at(ref)
    outer = pcb.y0 - CLEAR - WALL - SHOULDER_PROUD
    inner_wall = pcb.y0 - CLEAR + 0.05
    body = rbox(x - SHOULDER_W / 2, x + SHOULDER_W / 2, outer, inner_wall, *SHOULDER_Z)
    body = body.edges('|Z and >Y').fillet(1.0)  # the outer face: max y here
    flange = rbox(x - SHOULDER_FLANGE_W / 2, x + SHOULDER_FLANGE_W / 2, inner_wall,
                  SHOULDER_FLANGE_IN, *SHOULDER_FLANGE_Z)
    return solid(body.union(flange))


def on_bed(shape, rotate_x=0.0):
    """One copy, turned for printing, centered on the origin, standing at z = 0."""
    s = shape.rotate(cq.Vector(0, 0, 0), cq.Vector(1, 0, 0), rotate_x) if rotate_x else shape
    bb = s.BoundingBox()
    return s.translate(cq.Vector(-(bb.xmin + bb.xmax) / 2, -(bb.ymin + bb.ymax) / 2, -bb.zmin))


def build(pcb=None):
    pcb = pcb or board.read()
    outline = Outline(pcb)
    parts = {}

    dpad_pts, dpad_c = contacts(pcb, ('SW10', 'SW11', 'SW12', 'SW13'))
    abxy_pts, abxy_c = contacts(pcb, ('SW14', 'SW15', 'SW16', 'SW17'))
    span = 2 * (max(abs(p[0] - dpad_c[0]) for p in dpad_pts) + 2.5)
    outlines = {
        'cap-dpad': cross_outline(*dpad_c, span, 9.0),
        'cap-start': pill_outline(*pcb.at('SW18'), 8.0, 3.5),
        'cap-select': pill_outline(*pcb.at('SW19'), 8.0, 3.5),
        'cap-power': circle_outline(*pcb.at('SW1'), 2.5),
    }
    # 9 mm caps: the flange of the one at x 145 then clears the LCD's edge (x 138.7) by 0.3 mm.
    abxy = [circle_outline(x, y, 4.5) for x, y in abxy_pts]

    def add(name, shape, color, kind, stl=None, rotate_x=0.0, **extra):
        print_shape = on_bed(shape, rotate_x) if stl else None
        parts[name] = Part(name, shape, color, kind, stl, print_shape, **extra)

    add('front-shell', front_shell(pcb, outline, [*outlines.values(), *abxy]), BLACK,
        'printed', 'front-shell', 180)
    add('back-shell', back_shell(pcb, outline), BLACK, 'printed', 'back-shell')
    add('cap-dpad', cap(outlines['cap-dpad'], CAP_TOP_FACE, nub=dpad_c), RED, 'printed',
        'cap-dpad', 180)
    caps = [cap(o, CAP_TOP_FACE) for o in abxy]
    add('cap-abxy', cq.Compound.makeCompound(caps), RED, 'printed', 'cap-abxy')
    parts['cap-abxy'].print_shape = on_bed(caps[0], 180)
    add('cap-start', cap(outlines['cap-start'], CAP_TOP_PILL, stem=pcb.at('SW18')), RED,
        'printed', 'cap-start-select', 180)
    add('cap-select', cap(outlines['cap-select'], CAP_TOP_PILL, stem=pcb.at('SW19')), RED,
        'printed', 'cap-start-select', 180)
    add('cap-power', cap(outlines['cap-power'], FRONT, stem=pcb.at('SW1')), RED, 'printed',
        'cap-power', 180)
    add('shoulder-l', shoulder(pcb, 'SW20'), RED, 'printed', 'shoulder', 90)
    add('shoulder-r', shoulder(pcb, 'SW21'), RED, 'printed', 'shoulder', 90)

    for name, (center, pts) in (('pad-dpad', (dpad_c, dpad_pts)),
                                ('pad-abxy', (abxy_c, abxy_pts))):
        whole, sheet = pad(center, pts)
        add(name, whole, RUBBER, 'bought', sheet=sheet)
    for name, (x, y) in SPEAKERS.items():
        add(name, solid(cylinder(x, y, SPEAKER_R, RELIEF_TOP - SPEAKER_T, RELIEF_TOP)), SPEAKER,
            'bought')

    window, pocket, glass = lcd(pcb)
    lens = (pocket[0] + LENS_GAP, pocket[1] - LENS_GAP, pocket[2] + LENS_GAP, pocket[3] - LENS_GAP)
    add('lens', solid(rbox(*lens, PLATE_IN, PLATE_IN + LENS, 2.0 - LENS_GAP)), CLEAR_LENS,
        'bought')
    frame = (max(lens[0], glass[0]), min(lens[1], glass[1]), max(lens[2], glass[2]),
             min(lens[3], glass[3]))
    gasket = rbox(*frame, GLASS, PLATE_IN).cut(rbox(*window, GLASS - 1, PLATE_IN + 1, 1.0))
    add('gasket', solid(gasket), FOAM, 'bought')
    return parts


def assembly(parts):
    assy = cq.Assembly(name='marathon-case')
    for p in parts.values():
        assy.add(p.shape, name=p.name, color=p.color)
    return assy


def write_all(parts, out=HERE):
    """Write the assembly's STEP file and one STL per printed part."""
    out = Path(out)
    (out / 'step').mkdir(parents=True, exist_ok=True)
    (out / 'stl').mkdir(parents=True, exist_ok=True)
    assembly(parts).export(str(out / 'step' / 'marathon-case.step'), exportType='STEP')
    print(f'wrote {out / "step" / "marathon-case.step"}')
    written = set()
    for p in parts.values():
        if p.stl and p.stl not in written:
            path = out / 'stl' / f'{p.stl}.stl'
            p.print_shape.exportStl(str(path), tolerance=0.02, angularTolerance=0.2)
            written.add(p.stl)
            print(f'wrote {path}')


if __name__ == '__main__':
    write_all(build(), Path(sys.argv[1]) if len(sys.argv) > 1 else HERE)
