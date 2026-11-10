"""Tests for case.py, against KiCad's STEP export of the board. They need CadQuery and the
org.kicad.KiCad Flatpak, so run them through uv:

    uv run --no-project --python 3.12 --with cadquery==2.5.2 python -m unittest discover -s case/tests -p 'test_case.py'

Expected values come from spec 027 (planning/specs/027-CASE-CONCEPT.md) and spec 022, as each test
says. Coordinates are the case's: board x, minus board y, and z up from the board's back.
"""

import math
import struct
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import cadquery as cq

import board
import case

PCB = board.read()
PARTS = case.build(PCB)
TMP = tempfile.TemporaryDirectory()
SCRATCH = Path(TMP.name)
# The switches a cap or shoulder button presses, and the mute switch, whose actuator moves.
PRESSED = ['SW1', 'SW18', 'SW19', 'SW20', 'SW21', 'SW2']
TOLERANCE = 0.01  # mm³ of overlap allowed for faces that touch


def solids(path):
    return [s for v in cq.importers.importStep(str(path)).vals() for s in v.Solids()]


BOARD_ALL = solids(board.export_step(SCRATCH / 'all.step'))
BOARD_STILL = solids(board.export_step(
    SCRATCH / 'still.step', refs=[r for r in PCB.refs() if r not in PRESSED]))
SWITCH = {ref: solids(board.export_step(SCRATCH / f'{ref}.step', refs=[ref], body=False))
          for ref in PRESSED}


def tearDownModule():
    TMP.cleanup()


def overlap(a, b):
    """Volume of the overlap of two shapes, 0 when their bounding boxes miss."""
    ba, bb = a.BoundingBox(), b.BoundingBox()
    if (ba.xmax < bb.xmin or bb.xmax < ba.xmin or ba.ymax < bb.ymin or bb.ymax < ba.ymin
            or ba.zmax < bb.zmin or bb.zmax < ba.zmin):
        return 0.0
    return a.intersect(b).Volume()


def box(x0, x1, y0, y1, z0, z1):
    """A box in board coordinates (y down), z up from the board's back."""
    return cq.Solid.makeBox(x1 - x0, y1 - y0, z1 - z0, cq.Vector(x0, -y1, z0))


def shape(name):
    return PARTS[name].shape


class Parts(unittest.TestCase):
    def test_builds_every_part_spec_027_names(self):
        self.assertEqual(sorted(PARTS), sorted([
            'front-shell', 'back-shell', 'cap-dpad', 'cap-abxy', 'cap-start', 'cap-select',
            'cap-power', 'shoulder-l', 'shoulder-r', 'pad-dpad', 'pad-abxy', 'speaker-l',
            'speaker-r', 'lens', 'gasket']))


class AtRest(unittest.TestCase):
    def test_no_case_part_overlaps_the_board_or_its_parts(self):
        for name in PARTS:
            for i, s in enumerate(BOARD_ALL):
                with self.subTest(part=name, solid=i):
                    self.assertLessEqual(overlap(shape(name), s), TOLERANCE)

    def test_no_two_case_parts_overlap(self):
        names = list(PARTS)
        for i, a in enumerate(names):
            for b in names[i + 1:]:
                with self.subTest(a=a, b=b):
                    self.assertLessEqual(overlap(shape(a), shape(b)), TOLERANCE)

    def test_battery_space_is_clear(self):
        # Spec 022: x 112 to 179, y 28 to 87, 11.3 mm deep from the board's back.
        space = box(112, 179, 28, 87, -11.3, 0)
        for name in PARTS:
            with self.subTest(part=name):
                self.assertLessEqual(overlap(shape(name), space), TOLERANCE)


class Reach(unittest.TestCase):
    """Spec 027: each cap and shoulder button comes within 0.2 mm of what it presses."""

    def gap(self, low, high):
        self.assertGreaterEqual(round(high - low, 3), 0.0)
        self.assertLessEqual(round(high - low, 3), 0.2)

    def test_stems_reach_their_switches(self):
        for name, ref in (('cap-power', 'SW1'), ('cap-start', 'SW18'), ('cap-select', 'SW19')):
            with self.subTest(cap=name):
                top = max(s.BoundingBox().zmax for s in SWITCH[ref])
                self.gap(top, shape(name).BoundingBox().zmin)

    def test_face_caps_rest_on_their_domes(self):
        for cap, pad, refs in (('cap-dpad', 'pad-dpad', ('SW10', 'SW11', 'SW12', 'SW13')),
                               ('cap-abxy', 'pad-abxy', ('SW14', 'SW15', 'SW16', 'SW17'))):
            for ref in refs:
                x, y = PCB.at(ref)
                column = box(x - 1, x + 1, y - 1, y + 1, -1, 20)
                with self.subTest(ref=ref):
                    dome = shape(pad).intersect(column).BoundingBox().zmax
                    self.gap(dome, shape(cap).intersect(column).BoundingBox().zmin)

    def test_shoulder_flanges_reach_their_plungers(self):
        for name, ref in (('shoulder-l', 'SW20'), ('shoulder-r', 'SW21')):
            with self.subTest(button=name):
                plunger = -max(s.BoundingBox().ymax for s in SWITCH[ref])  # board y of its tip
                flange = -shape(name).BoundingBox().ymin
                self.gap(flange, plunger)


class InMotion(unittest.TestCase):
    """Spec 027: the first check holds through each part's motion. What a part presses is left
    out, since the real one moves with it; the switch's body stays in."""

    # Switch bodies without their actuators, from tools/render/models.py's stand-ins.
    BODIES = {
        'SW1': (3.5, 3.2, 1.0), 'SW18': (3.5, 3.2, 1.0), 'SW19': (3.5, 3.2, 1.0),
        'SW20': (3.5, 3.55, 1.25), 'SW21': (3.5, 3.55, 1.25), 'SW2': (10.0, 4.4, 3.8),
    }

    @classmethod
    def setUpClass(cls):
        still = list(BOARD_STILL)
        for ref, (w, d, h) in cls.BODIES.items():
            x, y = PCB.at(ref)
            still.append(box(x - w / 2, x + w / 2, y - d / 2, y + d / 2, 1.0, 1.0 + h))
        cls.still = still
        cls.others = {n: p.shape for n, p in PARTS.items()}

    def clear(self, name, moved):
        for i, s in enumerate(self.still):
            self.assertLessEqual(overlap(moved, s), TOLERANCE, f'{name} hits board solid {i}')
        for other, s in self.others.items():
            if other == name or other.startswith('pad-'):
                continue
            self.assertLessEqual(overlap(moved, s), TOLERANCE, f'{name} hits {other}')
        # The pad's sheet stays in; its domes move with the cap.
        for pad in ('pad-dpad', 'pad-abxy'):
            self.assertLessEqual(overlap(moved, PARTS[pad].sheet), TOLERANCE, f'{name} hits {pad}')

    def test_dpad_tipped_about_each_arm(self):
        # Spec 027: the pivot is the far arm's bearing edge, 15.25 mm out, at the ceiling of the
        # flange's pocket (z 5.2); the pressed arm's dome, 27.25 mm from it, travels 1 mm.
        cx, cy = 43, 53
        angle = math.degrees(math.asin(1.0 / 27.25))
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            with self.subTest(arm=(dx, dy)):
                px, py = cx - 15.25 * dx, cy - 15.25 * dy
                pivot = cq.Vector(px, -py, 5.2)
                # The arm points along (dx, -dy) here; z cross that tips it down.
                axis = cq.Vector(dy, dx, 0)
                moved = shape('cap-dpad').rotate(pivot, pivot + axis, angle)
                low = moved.intersect(box(cx + 12 * dx - 1, cx + 12 * dx + 1,
                                          cy + 12 * dy - 1, cy + 12 * dy + 1, -1, 20))
                self.assertAlmostEqual(low.BoundingBox().zmin, 3.5, delta=0.05)  # pressed 1 mm
                self.clear('cap-dpad', moved)

    # A switch press closes the gap to the actuator, up to the 0.2 mm spec 027 allows, and then
    # the Alps switch's travel, 0.25 mm (assumed, provisional).
    SWITCH_STROKE = 0.2 + 0.25

    def test_caps_pressed_through_their_travel(self):
        # Domes travel 1 mm (spec 027) and the caps rest on them.
        for name, travel in (('cap-abxy', 1.0), ('cap-start', self.SWITCH_STROKE),
                             ('cap-select', self.SWITCH_STROKE), ('cap-power', self.SWITCH_STROKE)):
            with self.subTest(cap=name):
                self.clear(name, shape(name).translate(cq.Vector(0, 0, -travel)))

    def test_shoulders_pressed_through_their_travel(self):
        for name in ('shoulder-l', 'shoulder-r'):
            with self.subTest(button=name):
                # Toward the board: +y in board coordinates is -y here.
                self.clear(name, shape(name).translate(cq.Vector(0, -self.SWITCH_STROKE, 0)))

    def test_mute_actuator_at_both_ends_of_its_slot(self):
        # The SS12F15-G5 stand-in's actuator: 2.0 x 1.5 mm, from its body's top (z 4.8) to 9.8;
        # 3 mm of travel (spec 027, provisional).
        x, y = PCB.at('SW2')
        for shift in (-1.5, 1.5):
            with self.subTest(shift=shift):
                actuator = box(x + shift - 1, x + shift + 1, y - 0.75, y + 0.75, 4.8, 9.8)
                self.assertLessEqual(overlap(actuator, shape('front-shell')), TOLERANCE)


class Size(unittest.TestCase):
    def test_body_is_164_2_by_79_2_by_18_5_mm(self):
        # Spec 027: the board plus 0.3 mm and a 1.8 mm wall; 18.5 mm from back face to front face.
        bb = shape('front-shell').fuse(shape('back-shell')).BoundingBox()
        self.assertAlmostEqual(bb.xlen, 164.2, places=2)
        self.assertAlmostEqual(bb.ylen, 79.2, places=2)
        self.assertAlmostEqual(bb.zmin, -12.5, places=2)
        self.assertAlmostEqual(bb.zmax, 6.0, places=2)


class Plate(unittest.TestCase):
    """Spec 027: pockets in the front plate's inside make room for the cap flanges (to z 5.2), the
    speakers, and the mute switch's body, and leave at least 0.8 mm of plate over them."""

    def assert_pocket_under_plate(self, x, y):
        shell = shape('front-shell')
        self.assertFalse(shell.isInside(cq.Vector(x, -y, 5.1)))   # the pocket
        for z in (5.3, 5.9):                                      # 0.8 mm of plate
            self.assertTrue(shell.isInside(cq.Vector(x, -y, z)), z)

    def test_plate_over_the_cap_flanges(self):
        # A point over each flange's flat: the cap's edge plus 0.5 mm. The D-pad's arms end
        # 14.5 mm from its center at (43, 53); ABXY caps are 9 mm round; Start and Select are
        # 8 x 3.5 mm pills; the power cap is 5 mm round.
        points = {'cap-dpad': (43 + 15.0, 53)}
        for ref in ('SW14', 'SW15', 'SW16', 'SW17'):
            x, y = PCB.at(ref)
            points[f'cap-abxy {ref}'] = (x + 5.0, y)
        for name, ref in (('cap-start', 'SW18'), ('cap-select', 'SW19')):
            x, y = PCB.at(ref)
            points[name] = (x, y + 2.25)
        x, y = PCB.at('SW1')
        points['cap-power'] = (x + 3.0, y)
        for name, (x, y) in points.items():
            with self.subTest(cap=name):
                self.assert_pocket_under_plate(x, y)

    def test_plate_over_the_speakers(self):
        # A point inside each speaker's ring, outside its grille (5.5 mm across its holes).
        for x, y in ((48, 82), (150, 80)):
            with self.subTest(speaker=(x, y)):
                self.assert_pocket_under_plate(x + 6.5, y)

    def test_plate_over_the_mute_switch(self):
        # The SS12F15-G5 stand-in's body is 10 x 4.4 mm and reaches z 4.8; a point over it,
        # 4 mm along from the switch's center, outside the actuator's slot.
        x, y = PCB.at('SW2')
        self.assert_pocket_under_plate(x + 4.0, y)

    def test_usb_pocket_stays_under_the_front_edge_fillet(self):
        # Spec 027: the 0.6 mm deep pocket around the USB-C opening ends at z 5.0, where the
        # front edge's 1.0 mm fillet starts, so no thin lip is left over it. The wall's outer
        # face is at board y 97.1 (the board's edge, 0.3 mm, and a 1.8 mm wall).
        x, _ = PCB.at('J4')
        shell = shape('front-shell')
        self.assertFalse(shell.isInside(cq.Vector(x + 5.0, -96.8, 4.9)))  # the pocket
        self.assertTrue(shell.isInside(cq.Vector(x + 5.0, -96.8, 5.1)))   # wall over it

    def test_gasket_bears_on_the_lcd_glass_under_the_lens(self):
        # On the glass outside the active area, at board (135, 53): the gasket starts at the
        # glass's top, and the lens sits at least 0.5 mm above it.
        column = box(134.5, 135.5, 52.5, 53.5, -1, 20)
        glass = max(s.intersect(column).BoundingBox().zmax for s in BOARD_ALL
                    if overlap(s, column) > 0)
        self.assertAlmostEqual(shape('gasket').BoundingBox().zmin, glass, places=2)
        self.assertGreaterEqual(shape('lens').BoundingBox().zmin - glass, 0.5)


class Fasteners(unittest.TestCase):
    """Spec 027: the insert hole runs from z 1.0 to 4.5, a 2 mm bore on to 5.2; the M2 x 12 mm
    screw's head seats 4.5 mm into the back face, at z -8.0, so its tip ends at z 4.0."""

    def inside(self, name, x, y, z):
        return shape(name).isInside(cq.Vector(x, -y, z))

    def test_front_boss_is_open_to_the_bore_s_end(self):
        for x, y in PCB.holes:
            with self.subTest(hole=(x, y)):
                for z in (1.2, 3.0, 4.4, 5.1):
                    self.assertFalse(self.inside('front-shell', x, y, z), z)
                self.assertTrue(self.inside('front-shell', x, y, 5.3))
                self.assertTrue(self.inside('front-shell', x + 1.9, y, 3.0))  # insert wall

    def test_back_boss_has_a_counterbore_and_a_clearance_hole(self):
        for x, y in PCB.holes:
            with self.subTest(hole=(x, y)):
                self.assertFalse(self.inside('back-shell', x + 1.6, y, -8.1))  # counterbore
                self.assertTrue(self.inside('back-shell', x + 1.6, y, -7.9))   # seat
                self.assertFalse(self.inside('back-shell', x, y, -5.0))        # clearance hole
                self.assertTrue(self.inside('back-shell', x + 2.0, y, -5.0))   # boss wall


class Printed(unittest.TestCase):
    # Spec 027, "Printing": every printed part, as one STL each, in its print orientation, with
    # its height on the bed: shells 7.5 mm (front face to skirt) and 13.2 mm (back face to the
    # USB-C tab), caps from flange or stem to top, shoulder buttons standing on the flange's face.
    HEIGHTS = {
        'front-shell': 7.5, 'back-shell': 13.2, 'cap-dpad': 5.0, 'cap-abxy': 3.0,
        'cap-start-select': 4.1, 'cap-power': 3.1, 'shoulder': 4.5,
    }

    @classmethod
    def setUpClass(cls):
        cls.out = SCRATCH / 'out'
        case.write_all(PARTS, cls.out)

    def test_each_printed_part_is_one_valid_solid(self):
        for name, part in PARTS.items():
            if part.stl:
                with self.subTest(part=name):
                    self.assertTrue(part.shape.isValid())
                    self.assertTrue(part.print_shape.isValid())
                    self.assertEqual(len(part.print_shape.Solids()), 1)

    def test_writes_one_stl_per_printed_part_on_the_bed(self):
        self.assertEqual(sorted(p.name for p in (self.out / 'stl').iterdir()),
                         sorted(f'{n}.stl' for n in self.HEIGHTS))
        for name, height in self.HEIGHTS.items():
            with self.subTest(part=name):
                zs = stl_z(self.out / 'stl' / f'{name}.stl')
                self.assertAlmostEqual(min(zs), 0.0, places=3)
                self.assertAlmostEqual(max(zs), height, places=2)

    def test_writes_the_assembly_as_step(self):
        step = self.out / 'step' / 'marathon-case.step'
        self.assertEqual(len(solids(step)), len(solids_in(PARTS)))


def stl_z(path):
    """Every vertex's z in a binary STL."""
    data = path.read_bytes()
    (count,) = struct.unpack_from('<I', data, 80)
    if len(data) != 84 + 50 * count:
        raise ValueError(f'{path}: not a binary STL of {count} triangles')
    return [struct.unpack_from('<f', data, 84 + 50 * i + 12 + 12 * v + 8)[0]
            for i in range(count) for v in range(3)]


def solids_in(parts):
    return [s for p in parts.values() for s in p.shape.Solids()]


if __name__ == '__main__':
    unittest.main()
