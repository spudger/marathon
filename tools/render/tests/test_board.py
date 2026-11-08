"""Checks that the board and its project footprints are set up for the renders.

Run: python3 -m unittest discover -s tools/render/tests -p 'test_board.py'
"""

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PCB = ROOT / 'pcb'
BOARD = (PCB / 'marathon.kicad_pcb').read_text()
MODEL_DIR = '${KIPRJMOD}/Marathon.3dshapes/'


def block(text, start):
    """The balanced s-expression that opens at index start."""
    depth = 0
    for i in range(start, len(text)):
        if text[i] == '(':
            depth += 1
        elif text[i] == ')':
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
    raise ValueError('unbalanced')


def footprint(ref):
    for m in re.finditer(r'\n\t\(footprint "', BOARD):
        fp = block(BOARD, m.start() + 2)
        if re.search(r'\(property "Reference" "%s"' % re.escape(ref), fp):
            return fp
    raise AssertionError(f'no footprint {ref} on the board')


def models(text):
    return re.findall(r'\(model "([^"]+)"', text)


class Stackup(unittest.TestCase):
    def setUp(self):
        m = re.search(r'\(stackup\b', BOARD)
        self.assertIsNotNone(m, 'the board defines no stackup')
        self.stackup = block(BOARD, m.start())

    def layer(self, name):
        m = re.search(r'\(layer "%s"' % re.escape(name), self.stackup)
        self.assertIsNotNone(m, f'stackup has no {name}')
        return block(self.stackup, m.start())

    def test_both_masks_are_opaque_black(self):
        # KiCad's "Black" preset is translucent enough that the board's tan core shows through and
        # renders brown, so the masks use a near-black at 95% opacity: #RRGGBBAA, each RGB at most
        # 0x14 and alpha at least 0xF0.
        for name in ('F.Mask', 'B.Mask'):
            m = re.search(r'\(color "#([0-9A-Fa-f]{8})"\)', self.layer(name))
            self.assertIsNotNone(m, f'{name} has no #RRGGBBAA color')
            r, g, b, a = (int(m.group(1)[i:i + 2], 16) for i in (0, 2, 4, 6))
            self.assertLessEqual(max(r, g, b), 0x14)
            self.assertGreaterEqual(a, 0xF0)

    def test_finish_is_enig(self):
        # bom/README.md decision log, 2026-09-22: ENIG finish.
        self.assertIn('(copper_finish "ENIG")', self.stackup)

    def test_layers_add_up_to_the_1_mm_board(self):
        # bom/README.md decision log, 2026-09-22: 1.0 mm board.
        total = sum(float(t) for t in re.findall(r'\(thickness ([0-9.]+)\)', self.stackup))
        self.assertAlmostEqual(total, 1.0, places=6)


class StandInModels(unittest.TestCase):
    PARTS = {
        'J1': 'RaspberryPi_Zero_2W_StandIn.step',
        'J2': 'LCD_3.2in_ILI9341_StandIn.step',
        'SW1': 'SW_Alps_SKTHACE010_StandIn.step',
        'SW18': 'SW_Alps_SKTHACE010_StandIn.step',
        'SW19': 'SW_Alps_SKTHACE010_StandIn.step',
        'SW20': 'SW_Alps_SKSCLDE010_StandIn.step',
        'SW21': 'SW_Alps_SKSCLDE010_StandIn.step',
        'SW2': 'SS12F15_G5_StandIn.step',
        'BT1': 'Battery_LiPo_105063_StandIn.step',
    }

    def test_each_part_on_the_board_points_at_its_model(self):
        for ref, name in self.PARTS.items():
            with self.subTest(ref=ref):
                self.assertEqual(models(footprint(ref)), [MODEL_DIR + name])

    def test_each_model_file_exists(self):
        for name in set(self.PARTS.values()):
            with self.subTest(name=name):
                self.assertTrue((PCB / 'Marathon.3dshapes' / name).is_file())

    def test_library_footprints_match_the_board(self):
        # An update from the library must keep the models.
        for ref, name in self.PARTS.items():
            lib = re.search(r'"Marathon:([^"]+)"', footprint(ref)).group(1)
            text = (PCB / 'Marathon.pretty' / f'{lib}.kicad_mod').read_text()
            with self.subTest(ref=ref):
                self.assertEqual(models(text), [MODEL_DIR + name])


class BatteryStandIn(unittest.TestCase):
    def setUp(self):
        self.fp = footprint('BT1')

    def test_is_board_only_and_left_out_of_bom_and_placement(self):
        attr = re.search(r'\(attr ([^)]*)\)', self.fp).group(1).split()
        for flag in ('board_only', 'exclude_from_bom', 'exclude_from_pos_files'):
            self.assertIn(flag, attr)

    def test_has_no_pads(self):
        self.assertNotIn('(pad ', self.fp)

    def test_sits_on_the_back_in_the_middle_of_the_free_block(self):
        # spec 022: the free block is x 112 to 179, y 28 to 87.
        self.assertIn('(layer "B.Cu")', self.fp)
        at = re.search(r'\n\t\t\(at ([-0-9.]+) ([-0-9.]+)', self.fp)
        self.assertEqual((float(at.group(1)), float(at.group(2))), (145.5, 57.5))


if __name__ == '__main__':
    unittest.main()
