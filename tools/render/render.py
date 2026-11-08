"""Render the Marathon board from fixed views into pcb/renders/.

    python3 tools/render/render.py [--out DIR]

Runs kicad-cli from the org.kicad.KiCad Flatpak, sandboxed: no network, the pcb/ folder read-only,
a throwaway KiCad config, and a scratch folder for the images, which are then copied to the
output folder. The board is drawn in its stackup colors: black mask, ENIG pads, white silkscreen.
"""

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PCB = ROOT / 'pcb'
BOARD = 'marathon.kicad_pcb'
APP = 'org.kicad.KiCad'

COMMON = ['--width', '1920', '--height', '1200', '--quality', 'high', '--use-board-stackup-colors']
FLAT = ['--background', 'transparent']
ANGLED = ['--floor', '--background', 'opaque', '--perspective', '--rotate', '-35,0,-25',
          '--zoom', '0.9']
VIEWS = {
    'top': ['--side', 'top', *FLAT],
    'bottom': ['--side', 'bottom', *FLAT],
    'angle-front': ['--side', 'top', *ANGLED],
    'angle-back': ['--side', 'bottom', *ANGLED],
}


def kicad_cli(scratch: Path, *args: str) -> list:
    return ['flatpak', 'run', '--sandbox', '--unshare=network',
            f'--filesystem={PCB}:ro', f'--filesystem={scratch}',
            f'--env=KICAD_CONFIG_HOME={scratch / "config"}',
            '--command=kicad-cli', APP, *args]


def main(argv=None, runner=subprocess.run) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--out', type=Path, default=PCB / 'renders')
    args = parser.parse_args(argv)
    env = {k: os.environ[k] for k in ('PATH', 'HOME', 'XDG_RUNTIME_DIR', 'LANG') if k in os.environ}
    scratch = Path(tempfile.mkdtemp(prefix='marathon-render-'))
    try:
        (scratch / 'config').mkdir()
        for view, opts in VIEWS.items():
            png = scratch / f'{view}.png'
            argv = kicad_cli(scratch, 'pcb', 'render', *COMMON, *opts,
                             '--output', str(png), str(PCB / BOARD))
            result = runner(argv, capture_output=True, text=True, env=env)
            if result.returncode != 0:
                print(f'FAIL {view}: kicad-cli exited {result.returncode}\n{result.stderr}',
                      file=sys.stderr)
                return 1
            if not png.is_file():
                print(f'FAIL {view}: not written: {png}', file=sys.stderr)
                return 1
        args.out.mkdir(parents=True, exist_ok=True)
        for view in VIEWS:
            shutil.copyfile(scratch / f'{view}.png', args.out / f'{view}.png')
            print(f'wrote {args.out / f"{view}.png"}')
        return 0
    finally:
        shutil.rmtree(scratch)


if __name__ == '__main__':
    sys.exit(main())
