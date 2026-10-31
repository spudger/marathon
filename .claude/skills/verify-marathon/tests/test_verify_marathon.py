"""Tests for the verify-marathon helper.

Run: python3 -m unittest discover -s .claude/skills/verify-marathon/tests
"""

import json
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import verify

ROOT = HERE.parents[3]

ERC_REPORT = """ERC report (2026-10-30T19:56:02, Encoding UTF8)
Report includes: Errors, Warnings, Exclusions

***** Sheet /
[pin_not_connected]: Pin not connected
    ; error
    @(30.4800 mm, 20.3200 mm): Symbol U1 Pin 2 [LED1, Passive, Line]

 ** ERC messages: 3  Errors 1  Warnings 2
"""

DRC_REPORT = """** Drc report for marathon.kicad_pcb **
** Created on 2026-10-30T19:56:10 **

** Found 3 DRC violations **
[lib_footprint_mismatch]: Footprint 'X' does not match copy in library 'Marathon'
    Local override; warning
[lib_footprint_mismatch]: Footprint 'Y' does not match copy in library 'Marathon'
    Local override; warning
[clearance]: Clearance violation
    Rule: netclass 'Default'; error

** Found 2 unconnected pads **
[unconnected_items]: Missing connection between items
[unconnected_items]: Missing connection between items

** Found 1 Footprint errors **
[extra_footprint]: Footprint not in schematic
"""


class BranchFolder(unittest.TestCase):
    def test_slashes_become_dashes(self):
        self.assertEqual(verify.branch_folder('feat/5-verify-skill'), 'feat-5-verify-skill')

    def test_refuses_empty_and_dot_names(self):
        for name in ('', '.', '..'):
            with self.assertRaises(ValueError):
                verify.branch_folder(name)


class Worktree(unittest.TestCase):
    def test_refuses_main_checkout(self):
        with self.assertRaises(ValueError):
            verify.require_worktree(ROOT, git_dir='/r/.git', common_dir='/r/.git')

    def test_accepts_linked_worktree(self):
        verify.require_worktree(ROOT, git_dir='/r/.git/worktrees/w', common_dir='/r/.git')


class ProjectPaths(unittest.TestCase):
    def scan(self, name, text):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / name
            path.write_text(text)
            return verify.path_findings([path])

    def test_project_relative_and_kicad_library_paths_pass(self):
        table = '(lib (name "M")(type "KiCad")(uri "${KIPRJMOD}/m.pretty"))\n'
        model = '(model "${KICAD10_3DMODEL_DIR}/C.3dshapes/C.step")\n'
        self.assertEqual(self.scan('fp-lib-table', table + model), [])

    def test_net_names_are_not_paths(self):
        self.assertEqual(self.scan('b.kicad_pcb', '(net "/BTN_A")\n(path "/ba06")\n'), [])

    def test_absolute_home_and_unknown_variable_paths_fail(self):
        text = (
            '(lib (name "A")(type "KiCad")(uri "/home/someone/libs/a.pretty"))\n'
            '(model "~/models/b.step")\n'
            '(lib (name "C")(type "KiCad")(uri "${MY_LIBS}/c.pretty"))\n'
        )
        self.assertEqual(len(self.scan('fp-lib-table', text)), 3)

    def test_project_file_paths_are_scanned(self):
        pro = json.dumps({'schematic': {'page_layout_descr_file': '/opt/sheets/a.kicad_wks'}})
        self.assertEqual(len(self.scan('m.kicad_pro', pro)), 1)

    def test_committed_project_reaches_nothing_outside(self):
        # Fails when the project gains a library, model or sheet path the sandbox does not cover.
        files = sorted(p for p in (ROOT / 'pcb').rglob('*') if p.is_file())
        self.assertTrue(files)
        self.assertEqual(verify.path_findings(files), [])


class Reports(unittest.TestCase):
    def test_erc_counts(self):
        self.assertEqual(
            verify.parse_erc(ERC_REPORT),
            {'messages': 3, 'errors': 1, 'warnings': 2, 'types': {'pin_not_connected': 1}},
        )

    def test_drc_counts(self):
        self.assertEqual(
            verify.parse_drc(DRC_REPORT),
            {
                'violations': 3,
                'unconnected': 2,
                'parity': 1,
                'errors': 1,
                'types': {
                    'clearance': 1,
                    'extra_footprint': 1,
                    'lib_footprint_mismatch': 2,
                    'unconnected_items': 2,
                },
            },
        )

    def test_unreadable_report_fails(self):
        with self.assertRaises(ValueError):
            verify.parse_drc('no counts here\n')


class SandboxProbe(unittest.TestCase):
    scratch = Path('/tmp/verify-marathon-abc')
    root = Path('/home/someone/.t3/worktrees/marathon/w')

    def probe(self, **change):
        values = {
            'config': f'{self.scratch}/config',
            'net': 'lo',
            'root': 'hidden',
            'home': 'hidden',
            'project': 'visible',
            'tables': 'present',
        }
        values.update(change)
        return ''.join(f'{k}={v}\n' for k, v in values.items())

    def failures(self, text):
        return [line for line in verify.probe_lines(text, self.scratch) if line.startswith('FAIL')]

    def test_sealed_sandbox_passes(self):
        self.assertEqual(self.failures(self.probe()), [])

    def test_network_interface_fails(self):
        self.assertEqual(len(self.failures(self.probe(net='lo,eth0'))), 1)

    def test_visible_worktree_or_home_fails(self):
        self.assertEqual(len(self.failures(self.probe(root='visible', home='visible'))), 2)

    def test_real_config_fails(self):
        real = '/home/someone/.var/app/org.kicad.KiCad/config'
        self.assertEqual(len(self.failures(self.probe(config=real))), 1)

    def test_missing_probe_line_fails(self):
        text = self.probe().replace('tables=present\n', '')
        self.assertEqual(len(self.failures(text)), 1)


class Ownership(unittest.TestCase):
    def test_foreign_scratch_path_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp)
            data = {'root': str(ROOT), 'scratch': '/home/someone/important'}
            (run / 'run.json').write_text(json.dumps(data))
            with self.assertRaises(ValueError):
                verify.state(run, ROOT)

    def test_owner_mismatch_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp)
            scratch = Path(tempfile.mkdtemp(prefix='verify-marathon-'))
            try:
                (scratch / 'owner').write_text('/somewhere/else')
                data = {'root': str(ROOT), 'scratch': str(scratch)}
                (run / 'run.json').write_text(json.dumps(data))
                with self.assertRaises(ValueError):
                    verify.state(run, ROOT)
            finally:
                (scratch / 'owner').unlink()
                scratch.rmdir()


if __name__ == '__main__':
    unittest.main()
