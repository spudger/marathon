"""Read the case's inputs from the KiCad board: the outline, the case holes, and where each part
sits. The case follows the board, so a part that moves on the board moves its opening with it.

Coordinates are the board's, in mm, with y down, as KiCad shows them.
"""

import importlib.util
import math
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / 'pcb' / 'marathon.kicad_pcb'


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# tools/render/render.py holds the sandboxed kicad-cli command the board renders use. It loads
# under its own name, since case/render.py is also called render.
board_render = _load('board_render', ROOT / 'tools' / 'render' / 'render.py')
CASE_HOLE = 'MountingHole:MountingHole_2.2mm_M2'


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
    raise ValueError('unbalanced s-expression')


def top_level(text, kind):
    """Each top-level item of one kind in the board file."""
    return [block(text, m.start() + 2) for m in re.finditer(r'\n\t\(%s\b' % kind, text)]


def circumradius(a, b, c):
    """The radius of the circle through three points."""
    ab, bc, ca = math.dist(a, b), math.dist(b, c), math.dist(c, a)
    area2 = abs((b[0] - a[0]) * (c[1] - a[1]) - (c[0] - a[0]) * (b[1] - a[1]))
    return ab * bc * ca / (2 * area2)


def point(item, name):
    m = re.search(r'\(%s ([-0-9.]+) ([-0-9.]+)\)' % name, item)
    return (float(m.group(1)), float(m.group(2))) if m else None


def number(value):
    """A coordinate as KiCad writes it: an int when it is whole, so 45 reads as 45."""
    v = float(value)
    return int(v) if v.is_integer() else v


@dataclass
class Board:
    x0: float
    y0: float
    x1: float
    y1: float
    radius: float
    thickness: float
    holes: list
    parts: dict

    def at(self, ref):
        """(x, y) of a part's origin."""
        if ref not in self.parts:
            raise KeyError(f'no part {ref} on the board')
        return self.parts[ref][:2]

    def side(self, ref):
        if ref not in self.parts:
            raise KeyError(f'no part {ref} on the board')
        return self.parts[ref][2]

    def refs(self):
        return sorted(self.parts)


def parse(text):
    edges = [g for kind in ('gr_line', 'gr_arc') for g in top_level(text, kind)
             if '(layer "Edge.Cuts")' in g]
    if not edges:
        raise ValueError('the board has no outline on Edge.Cuts')
    points = [p for g in edges for p in (point(g, 'start'), point(g, 'end')) if p]
    arcs = [g for g in edges if g.startswith('(gr_arc')]
    # KiCad writes an arc's mid point to 0.001 mm, so the radius is good to about 0.01 mm.
    radius = round(circumradius(point(arcs[0], 'start'), point(arcs[0], 'mid'),
                                point(arcs[0], 'end')), 2) if arcs else 0.0
    xs, ys = [p[0] for p in points], [p[1] for p in points]

    m = re.search(r'\(general\s*\(thickness ([0-9.]+)\)', text)
    thickness = float(m.group(1)) if m else 0.0

    parts, holes = {}, []
    for fp in top_level(text, 'footprint'):
        ref = re.search(r'\(property "Reference" "([^"]+)"', fp).group(1)
        at = re.search(r'\n\t\t\(at ([-0-9.]+) ([-0-9.]+)', fp)
        layer = re.search(r'\n\t\t\(layer "([^"]+)"\)', fp).group(1)
        xy = (number(at.group(1)), number(at.group(2)))
        parts[ref] = (*xy, 'front' if layer == 'F.Cu' else 'back')
        if fp.startswith(f'(footprint "{CASE_HOLE}'):
            holes.append(xy)
    return Board(min(xs), min(ys), max(xs), max(ys), radius, thickness, holes, parts)


def read(path=BOARD):
    return parse(Path(path).read_text())


def export_step(out, refs=None, body=True, runner=subprocess.run):
    """Export the board's 3D models as STEP, in board x, -y, and z up from the board's back.

    out must sit in a scratch folder, which the sandbox mounts read-write. refs limits the
    export to those parts; body=False leaves the board itself out.
    """
    out = Path(out)
    (out.parent / 'config').mkdir(exist_ok=True)
    args = ['pcb', 'export', 'step', '--force', '--user-origin', '0x0mm']
    if refs is not None:
        args += ['--component-filter', ','.join(refs)]
    if not body:
        args.append('--no-board-body')
    argv = board_render.kicad_cli(out.parent, *args, '--output', str(out), str(BOARD))
    env = {k: os.environ[k] for k in ('PATH', 'HOME', 'XDG_RUNTIME_DIR', 'LANG') if k in os.environ}
    result = runner(argv, capture_output=True, text=True, env=env)
    if result.returncode != 0 or not out.is_file():
        raise RuntimeError(f'kicad-cli STEP export failed ({result.returncode}): {result.stderr}')
    return out
