"""Tests for render.py, with kicad-cli replaced at the process boundary.

Run: python3 -m unittest discover -s tools/render/tests -p 'test_render.py'
"""

import io
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import render


class FakeKicad:
    """Stands in for subprocess.run: writes the image kicad-cli would write."""

    def __init__(self, fail_on=None, write=True):
        self.calls = []
        self.fail_on = fail_on
        self.write = write

    def __call__(self, argv, **kwargs):
        self.calls.append(argv)
        out = Path(argv[argv.index('--output') + 1])
        if self.fail_on and out.name == self.fail_on:
            return subprocess.CompletedProcess(argv, 1, '', 'Failed to load board\n')
        if self.write:
            out.write_bytes(b'\x89PNG fake')
        return subprocess.CompletedProcess(argv, 0, '', '')


class Render(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.out = Path(self.tmp.name) / 'renders'

    def tearDown(self):
        self.tmp.cleanup()

    def run_main(self, fake):
        err = io.StringIO()
        with redirect_stderr(err):
            code = render.main(['--out', str(self.out)], runner=fake)
        return code, err.getvalue()

    def test_writes_the_four_views(self):
        fake = FakeKicad()
        code, _ = self.run_main(fake)
        self.assertEqual(code, 0)
        self.assertEqual(sorted(p.name for p in self.out.iterdir()),
                         ['angle-back.png', 'angle-front.png', 'bottom.png', 'top.png'])

    def test_uses_the_board_stackup_colors_at_high_quality(self):
        fake = FakeKicad()
        self.run_main(fake)
        self.assertEqual(len(fake.calls), 4)
        for argv in fake.calls:
            self.assertIn('--use-board-stackup-colors', argv)
            self.assertEqual(argv[argv.index('--quality') + 1], 'high')

    def test_a_failed_view_fails_the_run_and_is_named(self):
        code, err = self.run_main(FakeKicad(fail_on='bottom.png'))
        self.assertEqual(code, 1)
        self.assertIn('bottom', err)
        self.assertIn('Failed to load board', err)

    def test_a_view_that_writes_nothing_fails_the_run(self):
        code, err = self.run_main(FakeKicad(write=False))
        self.assertEqual(code, 1)
        self.assertIn('not written', err)


if __name__ == '__main__':
    unittest.main()
