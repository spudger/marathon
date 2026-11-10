"""Render the board in its case into case/renders/ (spec 027, "Renders").

    uv run --no-project --python 3.12 --with cadquery==2.5.2 --with matplotlib python case/render.py [--out DIR]

The 3D views come from kicad-cli, run in tools/render/render.py's sandbox, on a scratch copy of
pcb/ with one board-only footprint added that carries the case's STEP models. pcb/ itself is never
written. The section comes from KiCad's STEP export of the board, cut with the case in CadQuery and
drawn with matplotlib.
"""

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PCB = ROOT / 'pcb'
sys.path.insert(0, str(HERE))
import board

PROJECT = ['marathon.kicad_pcb', 'marathon.kicad_pro', 'fp-lib-table', 'sym-lib-table',
           'Marathon.3dshapes', 'Marathon.pretty']
# The footprint's origin is on the board's front; the case's z = 0 is the board's back.
FRONT_Z = -1.0
SECTION_Y = 53.0

# Groups of parts, each one STEP model: its parts, its rise in the exploded view, its opacity.
GROUPS = {
    'back-shell': (['back-shell'], -45, 1.0),
    'pads': (['pad-dpad', 'pad-abxy'], 12, 1.0),
    'speakers': (['speaker-l', 'speaker-r'], 12, 1.0),
    'gasket': (['gasket'], 18, 1.0),
    'lens': (['lens'], 25, 0.4),
    'front-shell': (['front-shell'], 36, 1.0),
    'caps': (['cap-dpad', 'cap-abxy', 'cap-start', 'cap-select', 'cap-power', 'shoulder-l',
              'shoulder-r'], 52, 1.0),
}

ANGLED = ['--floor', '--background', 'opaque', '--perspective']
LIGHTS = ['--light-side', '0.6', '--light-camera', '0.3', '--light-side-elevation', '35']
VIEWS = {
    'angle-front': ('assembled', ['--width', '1920', '--height', '1200', '--side', 'top',
                                  '--rotate', '-35,0,-25', '--zoom', '0.9']),
    'angle-back': ('assembled', ['--width', '1920', '--height', '1200', '--side', 'bottom',
                                 '--rotate', '-35,0,-25', '--zoom', '0.9']),
    'exploded': ('exploded', ['--width', '1920', '--height', '1200', '--side', 'top',
                              '--rotate', '-70,0,-25', '--zoom', '0.68']),
    'social-preview': ('assembled', ['--width', '1280', '--height', '640', '--side', 'top',
                                     '--rotate', '-35,0,-25', '--zoom', '0.8']),
}


def footprint(models):
    """A board-only footprint at the origin that carries models: (path, z offset, opacity)."""
    blocks = ''.join(
        f'\t\t(model "{path}"\n'
        + (f'\t\t\t(opacity {opacity})\n' if opacity < 1 else '')
        + f'\t\t\t(offset (xyz 0 0 {z:g}))\n\t\t\t(scale (xyz 1 1 1))\n'
        f'\t\t\t(rotate (xyz 0 0 0))\n\t\t)\n'
        for path, z, opacity in models)
    prop = '\t\t(property "{}" "{}"\n\t\t\t(at 0 0 0)\n\t\t\t(layer "F.Fab")\n\t\t\t(hide yes)\n' \
           '\t\t\t(uuid "{}")\n\t\t\t(effects (font (size 1 1) (thickness 0.15)))\n\t\t)\n'
    return ('\t(footprint "Marathon:Case_Render"\n\t\t(layer "F.Cu")\n'
            f'\t\t(uuid "{uuid.uuid4()}")\n\t\t(at 0 0)\n'
            + prop.format('Reference', 'CASE1', uuid.uuid4())
            + prop.format('Value', 'Case', uuid.uuid4())
            + '\t\t(attr board_only exclude_from_pos_files exclude_from_bom)\n'
            '\t\t(embedded_fonts no)\n' + blocks + '\t)\n')


def add_footprint(board_text, fp):
    """The board file's text with one more footprint before its closing parenthesis."""
    end = board_text.rstrip().rfind(')')
    if end < 0 or not board_text.lstrip().startswith('(kicad_pcb'):
        raise ValueError('not a KiCad board file')
    return board_text[:end] + fp + ')\n'


def models(exploded):
    return [(f'${{KIPRJMOD}}/case/{name}.step', FRONT_Z + (rise if exploded else 0), opacity)
            for name, (_, rise, opacity) in GROUPS.items()]


def write_models(out):
    """One STEP model per group, in the case's colors."""
    import cadquery as cq
    import case
    parts = case.build()
    out.mkdir(parents=True, exist_ok=True)
    for name, (members, _, _) in GROUPS.items():
        assy = cq.Assembly(name=f'{name}-group')
        for m in members:
            assy.add(parts[m].shape, name=m, color=parts[m].color)
        assy.export(str(out / f'{name}.step'), exportType='STEP')
    return parts


def draw_section(parts, scratch, png):
    """Cut the board's STEP export and the case at y = SECTION_Y and draw the faces."""
    import cadquery as cq
    import case
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon

    step = board.export_step(scratch / 'board.step')
    board_solids = [s for v in cq.importers.importStep(str(step)).vals() for s in v.Solids()]
    slab = cq.Solid.makeBox(400, 0.02, 100, cq.Vector(-100, -SECTION_Y - 0.01, -50))

    fig, ax = plt.subplots(figsize=(16, 4.2))

    def draw(shape, color):
        for face in shape.intersect(slab).Faces():
            if abs(face.normalAt().y) < 0.99:
                continue
            for i, wire in enumerate([face.outerWire(), *face.innerWires()]):
                pts = [(p.x, p.z) for p in (wire.positionAt(t / 400) for t in range(400))]
                ax.add_patch(Polygon(pts, closed=True, fc=color if i == 0 else 'white',
                                     ec='#222222', lw=0.3))

    for s in board_solids:
        bb = s.BoundingBox()
        is_board = bb.xlen > 150 and bb.zmax <= 1.01 and bb.zmin >= -0.01
        draw(s, '#2f6b3a' if is_board else '#9a9a9a')
    colors = {'printed': '#1c1c1e', 'bought': '#6f6f74'}
    for p in parts.values():
        draw(p.shape, '#c41414' if p.color == parts['cap-dpad'].color else colors[p.kind])

    for z, nudge, label in ((case.FRONT, 0.7, 'front face'),
                            (case.PLATE_IN, -0.5, 'inside of the plate'),
                            (1.0, 0, 'board 0 to'), (case.BACK_IN, 0.7, 'inside of the back'),
                            (case.BACK, -0.9, 'back face')):
        ax.axhline(z, color='#4a7bd0', lw=0.5, ls='--')
        ax.text(186, z + nudge, f'{label} {z:.1f}', va='center', fontsize=8, color='#2a4f8f')
    ax.annotate('', xy=(13, case.FRONT), xytext=(13, case.BACK),
                arrowprops=dict(arrowstyle='<->', color='#2a4f8f', lw=0.8))
    ax.text(11.5, (case.FRONT + case.BACK) / 2, f'{case.FRONT - case.BACK:.1f} mm', rotation=90,
            va='center', ha='right', fontsize=9, color='#2a4f8f')
    ax.set_xlim(5, 215)
    ax.set_ylim(-15, 11)
    ax.set_aspect('equal')
    ax.set_xlabel('board x (mm)')
    ax.set_ylabel('z from the board\'s back (mm)')
    ax.set_title(f'Section at board y = {SECTION_Y:g} mm: D-pad, Pi, LCD, ABXY, battery')
    fig.savefig(png, dpi=150, bbox_inches='tight')
    plt.close(fig)


def main(argv=None, runner=subprocess.run, build=write_models, section=draw_section) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--out', type=Path, default=HERE / 'renders')
    args = parser.parse_args(argv)
    env = {k: os.environ[k] for k in ('PATH', 'HOME', 'XDG_RUNTIME_DIR', 'LANG') if k in os.environ}
    scratch = Path(tempfile.mkdtemp(prefix='marathon-case-render-'))
    try:
        (scratch / 'config').mkdir()
        project = scratch / 'pcb'
        project.mkdir()
        for name in PROJECT:
            src = PCB / name
            (shutil.copytree if src.is_dir() else shutil.copyfile)(src, project / name)
        parts = build(project / 'case')
        text = (PCB / 'marathon.kicad_pcb').read_text()
        for variant, exploded in (('assembled', False), ('exploded', True)):
            (project / f'{variant}.kicad_pcb').write_text(
                add_footprint(text, footprint(models(exploded))))
            shutil.copyfile(PCB / 'marathon.kicad_pro', project / f'{variant}.kicad_pro')

        for view, (variant, opts) in VIEWS.items():
            png = scratch / f'{view}.png'
            argv = board.board_render.kicad_cli(
                scratch, 'pcb', 'render', '--quality', 'high', '--use-board-stackup-colors',
                *ANGLED, *LIGHTS, *opts, '--output', str(png), str(project / f'{variant}.kicad_pcb'))
            result = runner(argv, capture_output=True, text=True, env=env)
            if result.returncode != 0:
                print(f'FAIL {view}: kicad-cli exited {result.returncode}\n{result.stderr}',
                      file=sys.stderr)
                return 1
            if not png.is_file():
                print(f'FAIL {view}: not written: {png}', file=sys.stderr)
                return 1
        section(parts, scratch, scratch / 'section.png')

        args.out.mkdir(parents=True, exist_ok=True)
        for view in [*VIEWS, 'section']:
            shutil.copyfile(scratch / f'{view}.png', args.out / f'{view}.png')
            print(f'wrote {args.out / f"{view}.png"}')
        return 0
    finally:
        shutil.rmtree(scratch)


if __name__ == '__main__':
    sys.exit(main())
