#!/usr/bin/python3
"""Check and render the Marathon KiCad project in a sealed KiCad Flatpak sandbox."""

import argparse
import csv
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
APP = 'org.kicad.KiCad'
SCH = 'pcb/marathon.kicad_sch'
PCB = 'pcb/marathon.kicad_pcb'
FEATURES = ('erc', 'drc', 'bom', 'render')
PREFIX = 'verify-marathon-'
# Path variables KiCad resolves inside the Flatpak; anything else could point outside the sandbox.
PATH_VARS = {
    'KIPRJMOD',
    'PROJECTNAME',
    'KICAD10_3DMODEL_DIR',
    'KICAD10_FOOTPRINT_DIR',
    'KICAD10_SYMBOL_DIR',
}
# Global library tables for the throwaway config: KiCad's own libraries inside the Flatpak.
TABLES = {
    'fp-lib-table': '(fp_lib_table\n\t(version 7)\n\t(lib (name "KiCad") (type "Table") '
    '(uri "/app/extensions/Library/template/fp-lib-table") (options "") '
    '(descr "KiCad Default Libraries"))\n)\n',
    'sym-lib-table': '(sym_lib_table\n\t(version 7)\n\t(lib (name "KiCad") (type "Table") '
    '(uri "/app/extensions/Library/template/sym-lib-table") (options "") '
    '(descr "KiCad Default Libraries"))\n)\n',
}
PROBES = ('config', 'net', 'root', 'home', 'project', 'tables')


def git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ['/usr/bin/git', '-C', str(root), *args],
        env={'PATH': '/usr/bin:/bin', 'GIT_CONFIG_NOSYSTEM': '1', 'GIT_CONFIG_GLOBAL': '/dev/null'},
        capture_output=True,
        text=True,
        timeout=30,
        check=True,
    )
    return result.stdout.strip()


def require_worktree(root: Path, *, git_dir=None, common_dir=None) -> None:
    git_dir = git_dir or git(root, 'rev-parse', '--absolute-git-dir')
    common_dir = common_dir or git(root, 'rev-parse', '--path-format=absolute', '--git-common-dir')
    if Path(git_dir).resolve() == Path(common_dir).resolve():
        raise ValueError('launch from a linked worktree, not the main checkout')


def branch_folder(branch: str) -> str:
    """The branch as one evidence folder name: each / becomes -, so t3/x is one folder."""
    name = branch.replace('/', '-')
    if name in ('', '.', '..'):
        raise ValueError('unsafe branch name; choose a normal task branch')
    return name


def project_files(root: Path) -> list[Path]:
    """Tracked and untracked files under pcb/, minus what .gitignore excludes (KiCad caches)."""
    names = git(root, 'ls-files', '--cached', '--others', '--exclude-standard', 'pcb').splitlines()
    return [root / n for n in sorted(set(names)) if (root / n).is_file()]


def fingerprints(root: Path, files: list[Path]) -> dict[str, str]:
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}


def bad_path(value: str) -> bool:
    if any(var not in PATH_VARS for var in re.findall(r'\$\{([^}]*)\}', value)):
        return True
    if value.startswith('${'):
        return False
    return value.startswith(('/', '~')) or bool(re.match(r'[A-Za-z]:[\\/]', value))


def path_values(node, under_path_key=False):
    """Strings in a .kicad_pro under keys that name a file, path, folder or URI."""
    if isinstance(node, dict):
        for key, value in node.items():
            hit = under_path_key or bool(re.search(r'file|path|dir|uri', key, re.I))
            yield from path_values(value, hit)
    elif isinstance(node, list):
        for value in node:
            yield from path_values(value, under_path_key)
    elif isinstance(node, str) and under_path_key and node:
        yield node


def path_findings(files: list[Path]) -> list[str]:
    """File references that could reach outside the project or KiCad's own libraries."""
    found = []
    for path in files:
        text = path.read_text(errors='replace')
        if path.suffix == '.kicad_pro':
            values = list(path_values(json.loads(text)))
        else:
            values = re.findall(r'\((?:uri|model)\s+"([^"]*)"', text)
        found += [f'{path.name}: {v}' for v in values if bad_path(v)]
    return found


def parse_erc(text: str) -> dict:
    match = re.search(r'ERC messages: (\d+)\s+Errors (\d+)\s+Warnings (\d+)', text)
    if not match:
        raise ValueError('ERC report has no message counts')
    types = {}
    for kind in re.findall(r'^\[([a-z_]+)\]:', text, re.M):
        types[kind] = types.get(kind, 0) + 1
    messages, errors, warnings = map(int, match.groups())
    return {'messages': messages, 'errors': errors, 'warnings': warnings, 'types': types}


def parse_drc(text: str) -> dict:
    counts = {}
    for label, key in (
        ('DRC violations', 'violations'),
        ('unconnected pads', 'unconnected'),
        ('Footprint errors', 'parity'),
    ):
        match = re.search(rf'\*\* Found (\d+) {label} \*\*', text)
        if not match:
            raise ValueError(f'DRC report has no "{label}" count')
        counts[key] = int(match.group(1))
    violations = text.split('** Found', 2)[1].split('** Found', 1)[0]
    counts['errors'] = len(re.findall(r'; error$', violations, re.M))
    types = {}
    for kind in re.findall(r'^\[([a-z_]+)\]:', text, re.M):
        types[kind] = types.get(kind, 0) + 1
    return {**counts, 'types': dict(sorted(types.items()))}


def probe_lines(text: str, scratch: Path) -> list[str]:
    """PASS or FAIL per sandbox guard, from the probe script's key=value output."""
    seen = dict(line.split('=', 1) for line in text.splitlines() if '=' in line)
    want = {
        'config': (str(scratch / 'config'), 'KiCad config is not the throwaway one'),
        'net': ('lo', 'the sandbox has a network interface besides lo'),
        'root': ('hidden', 'the sandbox can see this worktree'),
        'home': ('hidden', 'the sandbox can see the home folder'),
        'project': ('visible', 'the sandbox cannot see the project snapshot'),
        'tables': ('present', 'the throwaway config has no library tables'),
    }
    lines = []
    for key in PROBES:
        expected, problem = want[key]
        if seen.get(key) == expected:
            lines.append(f'PASS doctor {key}')
        else:
            lines.append(f'FAIL doctor {key}: {problem} ({seen.get(key, "no answer")}); relaunch')
    return lines


def sandbox(scratch: Path) -> list[str]:
    """The Flatpak flags every KiCad call runs with: no network, no home, throwaway config."""
    return [
        'flatpak',
        'run',
        '--unshare=network',
        '--nofilesystem=home',
        '--nofilesystem=host',
        f'--filesystem={scratch}',
        f'--env=KICAD_CONFIG_HOME={scratch / "config"}',
    ]


def run_cmd(argv: list[str], timeout: int = 300) -> dict:
    print('$ ' + ' '.join(argv), flush=True)
    result = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
    stderr = '\n'.join(l for l in result.stderr.splitlines() if not l.startswith('F: '))
    return {'argv': argv, 'exit': result.returncode, 'stdout': result.stdout, 'stderr': stderr}


def kicad(data: dict, *args: str) -> dict:
    return run_cmd([*data['sandbox'], '--command=kicad-cli', APP, *args])


def launch(root: Path, evidence_root: Path) -> Path:
    require_worktree(root)
    for tool in ('flatpak', 'pdftoppm'):
        if not shutil.which(tool):
            raise ValueError(f'{tool} is not installed')
    info = run_cmd(['flatpak', 'info', APP])
    version = re.search(r'Version:\s*(\S+)', info['stdout'])
    if info['exit'] or not version or not version.group(1).startswith('10.'):
        raise ValueError(f'{APP} 10.x is not installed as a Flatpak')
    files = project_files(root)
    findings = path_findings(files)
    if findings:
        raise ValueError('project references paths outside the sandbox: ' + '; '.join(findings))
    branch = branch_folder(git(root, 'branch', '--show-current') or 'detached')
    run = evidence_root / branch / datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')
    run.mkdir(parents=True, exist_ok=False)
    scratch = Path(tempfile.mkdtemp(prefix=PREFIX))
    (scratch / 'owner').write_text(str(run.resolve()))
    try:
        for f in files:
            dest = scratch / 'head' / f.relative_to(root)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, dest)
        baseline = None
        try:
            baseline = git(root, 'rev-parse', 'origin/main')
            archive = subprocess.run(
                ['/usr/bin/git', '-C', str(root), 'archive', baseline, 'pcb'],
                capture_output=True,
                check=True,
                timeout=60,
            )
            (scratch / 'main').mkdir()
            subprocess.run(
                ['tar', '-x', '-C', str(scratch / 'main')], input=archive.stdout, check=True
            )
        except subprocess.CalledProcessError:
            baseline = None
        (scratch / 'config/10.0').mkdir(parents=True)
        for name, text in TABLES.items():
            (scratch / 'config/10.0' / name).write_text(text)
        (scratch / 'out').mkdir()
        data = {
            'root': str(root),
            'scratch': str(scratch),
            'branch': branch,
            'head': git(root, 'rev-parse', 'HEAD'),
            'baseline': baseline,
            'kicad': version.group(1),
            'sources': fingerprints(root, files),
            'sandbox': sandbox(scratch),
        }
        (run / 'run.json').write_text(json.dumps(data, indent=2) + '\n')
        if not doctor(run, root):
            raise ValueError('doctor failed on a fresh instance')
    except Exception:
        cleanup(run, root)
        raise
    print(f'PASS launch: {run}')
    return run


def state(run: Path, root: Path) -> tuple[dict, Path]:
    data = json.loads((run / 'run.json').read_text())
    scratch = Path(data['scratch'])
    if (
        data['root'] != str(root)
        or scratch.parent != Path(tempfile.gettempdir())
        or not scratch.name.startswith(PREFIX)
        or scratch.is_symlink()
    ):
        raise ValueError('foreign scratch path; refuse cleanup or drive')
    if scratch.exists() and (scratch / 'owner').read_text() != str(run.resolve()):
        raise ValueError('scratch owner mismatch; inspect without deleting')
    return data, scratch


def doctor(run: Path, root: Path) -> bool:
    data, scratch = state(run, root)
    if not scratch.is_dir():
        raise ValueError('instance is cleaned up; launch another run')
    lines = []
    if git(root, 'rev-parse', 'HEAD') != data['head']:
        lines.append('FAIL doctor commit: HEAD moved since launch; clean up and relaunch')
    elif fingerprints(root, project_files(root)) != data['sources']:
        lines.append('FAIL doctor snapshot: pcb/ changed since launch; clean up and relaunch')
    else:
        lines.append('PASS doctor snapshot')
    probe = (
        'echo config=$KICAD_CONFIG_HOME; '
        "echo net=$(tail -n +3 /proc/net/dev | cut -d: -f1 | tr -d ' ' | paste -sd,); "
        f'test -e {root} && echo root=visible || echo root=hidden; '
        f'test -e {Path.home()}/Software && echo home=visible || echo home=hidden; '
        f'test -r {scratch}/head/{SCH} && echo project=visible || echo project=hidden; '
        '[ -r "$KICAD_CONFIG_HOME/10.0/fp-lib-table" ] && echo tables=present || echo tables=none'
    )
    row = run_cmd([*data['sandbox'], '--command=sh', APP, '-c', probe], timeout=60)
    lines += probe_lines(row['stdout'], scratch)
    for line in lines:
        print(line)
    return all(line.startswith('PASS') for line in lines)


def sides(data: dict, scratch: Path) -> list[tuple[str, Path]]:
    found = [('head', scratch / 'head')]
    if data['baseline'] and (scratch / 'main' / SCH).is_file():
        found.append(('main', scratch / 'main'))
    return found


def drive(run: Path, root: Path, feature: str) -> None:
    data, scratch = state(run, root)
    if (run / f'{feature}-proof.json').exists():
        raise ValueError(f'{feature} already driven in this run; launch another run to repeat it')
    if not doctor(run, root):
        raise ValueError('doctor failed; clean up and relaunch')
    out = scratch / 'out'
    records, proof = [], {}
    for side, base in sides(data, scratch):
        sch, pcb = str(base / SCH), str(base / PCB)
        if feature == 'erc':
            report = out / f'{side}-erc.rpt'
            records.append(kicad(data, 'sch', 'erc', '-o', str(report), sch))
            proof[side] = parse_erc(report.read_text())
            files = [report]
        elif feature == 'drc':
            report = out / f'{side}-drc.rpt'
            records.append(
                kicad(data, 'pcb', 'drc', '--refill-zones', '--schematic-parity',
                      '-o', str(report), pcb)
            )
            proof[side] = parse_drc(report.read_text())
            files = [report]
        elif feature == 'bom':
            report = out / f'{side}-bom.csv'
            fields = 'Reference,Value,Footprint,${QUANTITY}'
            records.append(
                kicad(data, 'sch', 'export', 'bom', '--fields', fields,
                      '--group-by', 'Value,Footprint', '-o', str(report), sch)
            )
            rows = list(csv.reader(report.read_text().splitlines()))[1:]
            proof[side] = {'rows': len(rows), 'parts': sum(int(r[3]) for r in rows)}
            files = [report]
        else:
            files = []
            exports = (
                ('schematic', ['sch', 'export', 'pdf'], sch),
                ('front', ['pcb', 'export', 'pdf', '--mode-single',
                           '--layers', 'F.Cu,F.SilkS,F.Fab,Edge.Cuts'], pcb),
                ('back', ['pcb', 'export', 'pdf', '--mode-single', '--mirror',
                          '--layers', 'B.Cu,B.SilkS,B.Fab,Edge.Cuts'], pcb),
            )
            for name, args, src in exports:
                pdf = out / f'{side}-{name}.pdf'
                records.append(kicad(data, *args, '-o', str(pdf), src))
                records.append(run_cmd(['pdftoppm', '-png', '-r', '100', '-singlefile',
                                        str(pdf), str(out / f'{side}-{name}')]))
                files += [pdf, out / f'{side}-{name}.png']
            for view in ('top', 'bottom'):
                png = out / f'{side}-3d-{view}.png'
                records.append(kicad(data, 'pcb', 'render', '--side', view, '--width', '1600',
                                     '--height', '900', '-o', str(png), pcb))
                files.append(png)
            proof[side] = {'images': [f.name for f in files if f.suffix == '.png']}
        for f in files:
            if not f.is_file():
                raise ValueError(f'{f.name} was not written')
            shutil.copy2(f, run / f.name)
    (run / f'{feature}.json').write_text(json.dumps(records, indent=2) + '\n')
    failed = [r for r in records if r['exit']]
    if failed:
        raise ValueError(f'{len(failed)} command(s) exited non-zero; see {feature}.json')
    (run / f'{feature}-proof.json').write_text(json.dumps(proof, indent=2) + '\n')
    for side, result in proof.items():
        print(f'{side}: {json.dumps(result)}')
    print(f'PASS drive {feature}: {run}')


def evidence(run: Path) -> None:
    if not (run / 'run.json').is_file():
        raise ValueError('no run.json; launch a run first')
    if not any((run / f'{f}-proof.json').is_file() for f in FEATURES):
        raise ValueError('no drive evidence; drive a mapped feature before cleanup')
    print(f'PASS evidence: {run}')


def cleanup(run: Path, root: Path) -> None:
    _, scratch = state(run, root)
    if scratch.exists():
        subprocess.run(['/bin/ls', '-lah', str(scratch)], check=True)
        shutil.rmtree(scratch)
    if not (run / 'run.json').is_file():
        raise ValueError('evidence disappeared; recover it before reporting success')
    print(f'PASS cleanup: evidence retained at {run}')


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('launch', 'doctor', 'drive', 'evidence', 'cleanup'))
    parser.add_argument('--run', type=Path)
    parser.add_argument('--feature', choices=FEATURES)
    args = parser.parse_args()
    if args.action != 'launch' and not args.run:
        parser.error('--run is required after launch')
    if args.action == 'drive' and not args.feature:
        parser.error('--feature is required for drive')
    try:
        if args.action == 'launch':
            launch(ROOT, Path.home() / '.local/state/verify-marathon')
        elif args.action == 'doctor':
            return 0 if doctor(args.run.resolve(), ROOT) else 1
        elif args.action == 'drive':
            drive(args.run.resolve(), ROOT, args.feature)
        elif args.action == 'evidence':
            evidence(args.run.resolve())
        else:
            cleanup(args.run.resolve(), ROOT)
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as error:
        print(f'FAIL {args.action}: {error}')
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
