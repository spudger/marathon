"""Tests for render.py, with kicad-cli replaced at the process boundary and the CadQuery steps
replaced by stand-ins, so they run without uv:

    python3 -m unittest discover -s case/tests -p 'test_render.py'
"""

import io
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import render

BOARD = (render.PCB / 'marathon.kicad_pcb').read_text()


class FakeKicad:
    """Stands in for subprocess.run: writes the image kicad-cli would write, and keeps the board
    file each call rendered."""

    def __init__(self, fail_on=None, write=True):
        self.calls, self.boards = [], []
        self.fail_on, self.write = fail_on, write

    def __call__(self, argv, **kwargs):
        self.calls.append(argv)
        self.boards.append(Path(argv[-1]).read_text())
        out = Path(argv[argv.index('--output') + 1])
        if self.fail_on and out.name == self.fail_on:
            return subprocess.CompletedProcess(argv, 1, '', 'Failed to load board\n')
        if self.write:
            out.write_bytes(b'\x89PNG fake')
        return subprocess.CompletedProcess(argv, 0, '', '')


def fake_build(out):
    out.mkdir(parents=True)
    for name in render.GROUPS:
        (out / f'{name}.step').write_text('ISO-10303-21;')
    return {}


def fake_section(parts, scratch, png):
    png.write_bytes(b'\x89PNG section')


class Footprint(unittest.TestCase):
    def test_carries_each_model_board_only_at_its_offset(self):
        fp = render.footprint([('${KIPRJMOD}/case/caps.step', 39.0, 1.0),
                               ('${KIPRJMOD}/case/lens.step', -1.0, 0.25)])
        self.assertIn('(attr board_only exclude_from_pos_files exclude_from_bom)', fp)
        self.assertIn('(layer "F.Cu")', fp)
        self.assertIn('(at 0 0)', fp)
        self.assertIn('(model "${KIPRJMOD}/case/caps.step"', fp)
        self.assertIn('(offset (xyz 0 0 39))', fp)
        self.assertIn('(offset (xyz 0 0 -1))', fp)
        self.assertEqual(fp.count('(opacity 0.25)'), 1)
        self.assertEqual(fp.count('(model '), 2)

    def test_assembled_models_sit_1_mm_down_from_the_front(self):
        # The case's z = 0 is the board's back; KiCad puts a front footprint's z = 0 on its front.
        for path, z, _ in render.models(exploded=False):
            with self.subTest(path=path):
                self.assertEqual(z, -1.0)

    def test_exploded_view_drops_the_back_and_lifts_the_front(self):
        z = {Path(p).stem: z for p, z, _ in render.models(exploded=True)}
        self.assertLess(z['back-shell'], -1.0)
        self.assertGreater(z['caps'], z['front-shell'])
        self.assertGreater(z['front-shell'], z['lens'])
        self.assertGreater(z['lens'], -1.0)


class AddFootprint(unittest.TestCase):
    def test_adds_one_footprint_inside_the_board(self):
        text = render.add_footprint(BOARD, '\t(footprint "X")\n')
        self.assertEqual(text.count('\n\t(footprint '), BOARD.count('\n\t(footprint ') + 1)
        self.assertTrue(text.rstrip().endswith('\t(footprint "X")\n)'))

    def test_refuses_a_file_that_is_not_a_board(self):
        with self.assertRaises(ValueError):
            render.add_footprint('(kicad_sch)', '\t(footprint "X")\n')


class Main(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.out = Path(self.tmp.name) / 'renders'

    def tearDown(self):
        self.tmp.cleanup()

    def run_main(self, fake):
        err = io.StringIO()
        with redirect_stderr(err), redirect_stdout(io.StringIO()):
            code = render.main(['--out', str(self.out)], runner=fake, build=fake_build,
                               section=fake_section)
        return code, err.getvalue()

    def test_writes_the_four_views_and_the_section(self):
        code, _ = self.run_main(FakeKicad())
        self.assertEqual(code, 0)
        self.assertEqual(sorted(p.name for p in self.out.iterdir()),
                         ['angle-back.png', 'angle-front.png', 'exploded.png', 'section.png',
                          'social-preview.png'])

    def test_renders_a_scratch_copy_with_the_case_and_leaves_pcb_alone(self):
        fake = FakeKicad()
        self.run_main(fake)
        self.assertEqual((render.PCB / 'marathon.kicad_pcb').read_text(), BOARD)
        for argv, text in zip(fake.calls, fake.boards):
            with self.subTest(view=argv[argv.index('--output') + 1]):
                self.assertFalse(argv[-1].startswith(str(render.PCB)))
                self.assertIn('(footprint "Marathon:Case_Render"', text)

    def test_social_preview_is_1280_by_640(self):
        fake = FakeKicad()
        self.run_main(fake)
        argv = next(a for a in fake.calls if a[a.index('--output') + 1].endswith('social-preview.png'))
        self.assertEqual(argv[argv.index('--width') + 1], '1280')
        self.assertEqual(argv[argv.index('--height') + 1], '640')

    def test_a_failed_view_fails_the_run_and_is_named(self):
        code, err = self.run_main(FakeKicad(fail_on='exploded.png'))
        self.assertEqual(code, 1)
        self.assertIn('exploded', err)
        self.assertIn('Failed to load board', err)
        self.assertFalse(self.out.exists())

    def test_a_view_that_writes_nothing_fails_the_run(self):
        code, err = self.run_main(FakeKicad(write=False))
        self.assertEqual(code, 1)
        self.assertIn('not written', err)


if __name__ == '__main__':
    unittest.main()
