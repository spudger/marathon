"""Tests for board.py, which reads the case's inputs from the KiCad board.

Run: python3 -m unittest discover -s case/tests -p 'test_board.py'

Expected values come from documentation/PROJECT_PLAN.md (Phase 4: a 160 x 75 mm outline with
6 mm corners, M2 case holes 5 mm in from each edge) and from spec 027, which names each part's
position.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import board

PCB = board.read()


class Outline(unittest.TestCase):
    def test_is_the_160_by_75_mm_board_with_6_mm_corners(self):
        self.assertEqual((PCB.x0, PCB.y0, PCB.x1, PCB.y1), (20, 20, 180, 95))
        self.assertAlmostEqual(PCB.radius, 6.0, places=3)

    def test_board_is_1_mm_thick(self):
        self.assertAlmostEqual(PCB.thickness, 1.0, places=6)


class Holes(unittest.TestCase):
    def test_four_case_holes_5_mm_in_from_each_edge(self):
        self.assertEqual(sorted(PCB.holes), [(25, 25), (25, 90), (175, 25), (175, 90)])


class Parts(unittest.TestCase):
    def test_positions_of_the_parts_the_case_serves(self):
        expected = {
            'SW1': (24, 78), 'SW18': (106, 84), 'SW19': (94, 84), 'SW20': (45, 23.5),
            'SW21': (155, 23.5), 'SW2': (162, 91.5), 'J4': (100, 92.5),
            'SW10': (43, 41), 'SW11': (43, 65), 'SW12': (31, 53), 'SW13': (55, 53),
            'SW14': (169, 53), 'SW15': (157, 65), 'SW16': (157, 41), 'SW17': (145, 53),
        }
        for ref, xy in expected.items():
            with self.subTest(ref=ref):
                self.assertEqual(PCB.at(ref), xy)

    def test_side_of_the_board(self):
        self.assertEqual(PCB.side('SW1'), 'front')
        self.assertEqual(PCB.side('J1'), 'back')

    def test_every_reference_is_listed(self):
        # pcb/marathon.kicad_pcb holds 100 footprints.
        self.assertEqual(len(PCB.refs()), 100)

    def test_an_unknown_reference_names_itself(self):
        with self.assertRaisesRegex(KeyError, 'SW99'):
            PCB.at('SW99')


class Text(unittest.TestCase):
    def test_a_board_with_no_outline_is_refused(self):
        with self.assertRaisesRegex(ValueError, 'Edge.Cuts'):
            board.parse('(kicad_pcb (general (thickness 1.0)))')


if __name__ == '__main__':
    unittest.main()
