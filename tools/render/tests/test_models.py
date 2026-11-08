"""Tests for models.py. They need CadQuery, so run them through uv:

    uv run --no-project --python 3.12 --with cadquery==2.5.2 python -m unittest discover -s tools/render/tests -p 'test_models.py'

Each model is read back from the STEP file it writes, so the tests check the file KiCad loads.
Expected sizes come from the datasheets, the footprints and the specs, as each test says.
"""

import re
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import cadquery as cq

import models

TMP = tempfile.TemporaryDirectory()
OUT = Path(TMP.name)
models.write_all(OUT)


def tearDownModule():
    TMP.cleanup()


def shape(name):
    """Every solid in the file, as one compound."""
    wp = cq.importers.importStep(str(OUT / name))
    return cq.Compound.makeCompound([s for v in wp.vals() for s in v.Solids()])


def size(name):
    bb = shape(name).BoundingBox()
    return bb, (round(bb.xlen, 2), round(bb.ylen, 2), round(bb.zlen, 2))


def inside(compound, x, y, z):
    return any(s.isInside(cq.Vector(x, y, z)) for s in compound.Solids())


class Files(unittest.TestCase):
    def test_writes_one_step_file_per_stand_in(self):
        self.assertEqual(sorted(p.name for p in OUT.iterdir()), [
            'Battery_LiPo_105063_StandIn.step',
            'LCD_3.2in_ILI9341_StandIn.step',
            'RaspberryPi_Zero_2W_StandIn.step',
            'SS12F15_G5_StandIn.step',
            'SW_Alps_SKSCLDE010_StandIn.step',
            'SW_Alps_SKTHACE010_StandIn.step',
        ])

    def test_each_file_keeps_its_part_colors(self):
        # KiCad renders a STEP model in the colors the file carries; without them every part is
        # the same grey. The Pi has its green board, gold pins and white standoffs.
        text = (OUT / 'RaspberryPi_Zero_2W_StandIn.step').read_text()
        colors = {tuple(round(float(v), 2) for v in m)
                  for m in re.findall(r"COLOUR_RGB\('[^']*',([-0-9.Ee]+),([-0-9.Ee]+),([-0-9.Ee]+)\)",
                                      text.replace('\n', '').replace(' ', ''))}
        self.assertIn((0.08, 0.42, 0.2), colors)
        self.assertIn((0.85, 0.65, 0.2), colors)
        self.assertIn((0.93, 0.93, 0.9), colors)


class Switches(unittest.TestCase):
    def test_top_push_switch_is_3_5_by_3_2_by_1_8(self):
        # Alps SKTHACE010, as the footprint's description quotes it.
        bb, dims = size('SW_Alps_SKTHACE010_StandIn.step')
        self.assertEqual(dims[2], 1.8)
        self.assertEqual((round(bb.zmin, 2)), 0)
        # The body is 3.5 x 3.2; only the terminals reach past it, to the pads' outer edge.
        body = shape('SW_Alps_SKTHACE010_StandIn.step')
        self.assertTrue(inside(body, 1.7, 1.55, 0.5))
        self.assertFalse(inside(body, 0, 1.7, 0.5))

    def test_side_push_switch_is_1_25_tall_with_its_plunger_toward_minus_y(self):
        # Alps SKSCLDE010: 3.5 x 3.55 x 1.25. The footprint puts the plunger at footprint +y,
        # which is model -y, since KiCad models are y-up.
        bb, dims = size('SW_Alps_SKSCLDE010_StandIn.step')
        self.assertEqual(dims[2], 1.25)
        self.assertLess(bb.ymin, -1.775)
        self.assertAlmostEqual(bb.ymax, 1.775, places=2)

    def test_slide_switch_fills_its_19_5_by_5_6_outline(self):
        # SS12F15_G5_THT footprint: 19.5 x 5.6 mm outline.
        bb, dims = size('SS12F15_G5_StandIn.step')
        self.assertEqual(dims[:2], (19.5, 5.6))

    def test_slide_switch_actuator_stands_5_mm_above_its_body(self):
        # G5 is the 5 mm actuator. The body's top is at z 3.8 (an estimate in models.py).
        sw = shape('SS12F15_G5_StandIn.step')
        self.assertAlmostEqual(sw.BoundingBox().zmax, 3.8 + 5.0, places=2)
        self.assertTrue(inside(sw, 0, 0, 8.6))


class Lcd(unittest.TestCase):
    def test_body_covers_the_lcd_outline_on_the_board(self):
        # Board F.Fab: LCD body x 61.3 to 138.7, y 25 to 79, and J2 sits at (100, 78).
        # In J2's model frame that is x -38.7 to 38.7 and y -1 to 53.
        lcd = shape('LCD_3.2in_ILI9341_StandIn.step')
        bb = lcd.BoundingBox()
        self.assertAlmostEqual(bb.xmin, -38.7, places=2)
        self.assertAlmostEqual(bb.xmax, 38.7, places=2)
        self.assertAlmostEqual(bb.ymax, 53, places=2)
        self.assertTrue(inside(lcd, 0, 26, 3))

    def test_sits_above_the_header_pin_tails(self):
        # The Pi header's pins come through the front at board y 30.2 to 32.8 (J2 model y 45 to
        # 48); the panel must start above them.
        lcd = shape('LCD_3.2in_ILI9341_StandIn.step')
        self.assertFalse(inside(lcd, -20, 46.5, 1.0))
        self.assertGreaterEqual(lcd.BoundingBox().zmin, 0)


class Pi(unittest.TestCase):
    def setUp(self):
        self.pi = shape('RaspberryPi_Zero_2W_StandIn.step')

    def test_stack_is_about_10_mm_deep(self):
        # spec 022: the Pi on 5 mm standoffs is about 10.0 mm deep, 9.7 to 10.4 mm.
        bb = self.pi.BoundingBox()
        self.assertGreaterEqual(bb.zmax, 9.7)
        self.assertLessEqual(bb.zmax, 10.4)

    def test_board_holes_line_up_with_the_footprint_holes(self):
        # Footprint holes at (-1.27, -4.87), (-1.27, 53.13), (21.73, -4.87), (21.73, 53.13) in
        # the model frame. Inside the Pi's board (z 5.5) a hole's centre is empty (the standoff
        # screw is not modeled), while 2.5 mm away is board.
        for x, y in ((-1.27, -4.87), (-1.27, 53.13), (21.73, -4.87), (21.73, 53.13)):
            with self.subTest(x=x, y=y):
                self.assertFalse(inside(self.pi, x, y, 5.5))
                self.assertTrue(inside(self.pi, x + 2.5, y + (2.5 if y < 0 else -2.5), 5.5))

    def test_standoffs_fill_the_gap_at_each_hole(self):
        for x, y in ((-1.27, -4.87), (21.73, 53.13)):
            with self.subTest(x=x, y=y):
                self.assertTrue(inside(self.pi, x + 1.8, y, 2.5))

    def test_mini_hdmi_is_12_4_mm_from_the_sd_end(self):
        # Raspberry Pi Zero 2 W mechanical drawing: mini-HDMI centre 12.4 mm from the left edge.
        # The left (SD) edge is model y -8.47, the port edge is model x 25.33.
        self.assertTrue(inside(self.pi, 23.5, -8.47 + 12.4, 7.5))
        self.assertFalse(inside(self.pi, 23.5, -8.47 + 26.0, 7.5))


class Battery(unittest.TestCase):
    def test_is_the_63_by_50_by_10_cell(self):
        # bom/README.md: provisional pick Bihuade 105063, 10 x 50 x 63 mm, 63 along the board.
        _, dims = size('Battery_LiPo_105063_StandIn.step')
        self.assertEqual(dims, (63.0, 50.0, 10.0))


if __name__ == '__main__':
    unittest.main()
