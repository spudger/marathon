---
name: verify-marathon
description: Verify changes to the Marathon KiCad project (schematic, PCB layout, project libraries) by running ERC, DRC with schematic parity and a BOM export, and rendering the schematic and board, beside the same results from main. Use for any change under pcb/.
---

# Verify Marathon

## Launch

Marathon's user-facing surface is the KiCad 10 project in `pcb/`: the schematic, the board and the
project libraries. There is no app to start. A run checks and renders a snapshot of the project
with `kicad-cli`, inside the KiCad Flatpak. The docs are prose and are checked by reading them
against these results.

From the task's linked worktree, run:

```sh
python3 .claude/skills/verify-marathon/verify.py launch
```

Save the folder printed by `PASS launch` as `run`. Launch refuses the main checkout, needs the
`org.kicad.KiCad` Flatpak at 10.x and `pdftoppm`, and refuses a project whose library tables, 3D
models or project file point outside `${KIPRJMOD}` and KiCad's own libraries. It copies the
working tree's `pcb/` files (committed or not, minus what `.gitignore` excludes) into a scratch
folder in `/tmp`, extracts `origin/main`'s `pcb/` beside it as the baseline, and seeds a throwaway
KiCad config whose library tables point at the Flatpak's bundled libraries. Launch fails when
there is no baseline; run `git fetch origin` and launch again.

Every KiCad call runs as `flatpak run --sandbox --unshare=network --filesystem=<scratch>
--env=KICAD_CONFIG_HOME=<scratch>/config`, with the host environment cut down to `PATH`, `HOME`,
`XDG_RUNTIME_DIR` and `LANG`. `--sandbox` drops every folder the KiCad Flatpak is normally
granted (the home folder, `/media`, `/run/media`) and its own data folder in
`~/.var/app/org.kicad.KiCad`. KiCad sees no network, no credentials and none of the user's KiCad
settings, and reads and writes only the scratch folder. The helper copies outputs into the
evidence folder.

## Doctor

```sh
python3 .claude/skills/verify-marathon/verify.py doctor --run "$run"
```

Expect ten `PASS doctor` lines. `snapshot` fails when HEAD or any `pcb/` file changed since
launch. The rest come from a probe run inside the same sandbox the drives use: `config` (KiCad's
config is the throwaway one), `net` (only `lo`), `root`, `home`, `media` and `appdata` (the
worktree, home folder, removable media and KiCad's real data folder are hidden), `env` (no
variable beyond what the Flatpak sets itself), `project` (the snapshot is readable) and `tables`
(the library tables exist). Every
drive runs Doctor first. Edits to `pcb/` need a fresh launch.

## Drive

```sh
python3 .claude/skills/verify-marathon/verify.py drive --run "$run" --feature erc
python3 .claude/skills/verify-marathon/verify.py drive --run "$run" --feature drc
python3 .claude/skills/verify-marathon/verify.py drive --run "$run" --feature bom
python3 .claude/skills/verify-marathon/verify.py drive --run "$run" --feature render
```

Each drive runs on the working-tree snapshot (`head`) and on the baseline (`main`), prints one
summary line per side and ends with `PASS drive <feature>`. A drive fails when a `kicad-cli` or
`pdftoppm` call exits non-zero or writes no output; its command records and any partial output
are still saved. Violations do not fail a drive; compare the
two sides to judge the change. Each feature runs once per run, so evidence is never overwritten.

## Evidence

```sh
python3 .claude/skills/verify-marathon/verify.py evidence --run "$run"
```

Expect `PASS evidence`. Each run's folder is
`~/.local/state/verify-marathon/<branch>/<UTC timestamp>/`, with each `/` in the branch name
replaced by `-`. It is outside every worktree and survives cleanup and `wt sweep`.

- `run.json`: the source checkout, HEAD, baseline commit, KiCad version, the sandbox flags and a
  hash of every snapshot file.
- `<feature>.json`: each command's argv, exit code, stdout and stderr.
- `<feature>-proof.json`: the summary counts per side.
- Reports and exports per side: `head-erc.rpt`, `head-drc.rpt`, `head-bom.csv`, and for render
  `head-schematic`, `head-front`, `head-back` (PDF and PNG), `head-3d-top.png` and
  `head-3d-bottom.png`, each with its `main-` twin.

Show the before and after PNGs inline in the T3 thread; never upload them. Put the helper commands
and their PASS and FAIL lines in the PR's Evidence fold, with the run folder's path.

## Cleanup

Always clean up, including after a failed drive:

```sh
python3 .claude/skills/verify-marathon/verify.py cleanup --run "$run"
python3 .claude/skills/verify-marathon/verify.py evidence --run "$run"
```

Cleanup checks the run owns the scratch folder, runs `ls -lah` on its exact path, then removes
only that folder. It starts no lasting processes; each Flatpak call ends before the next begins.
It ends with `PASS cleanup: evidence retained at ...`. The helper never deletes evidence; remove
old runs only when the user asks.

## Parallel instances

Each launch gets its own scratch folder, KiCad config and evidence folder, with no ports or shared
state, so runs can go side by side in one worktree or several.

## Feature map

See [features/README.md](features/README.md). A proof covers every feature the change touches:
a schematic change needs `erc`, `drc` (parity) and `bom`; a layout change needs `drc` and
`render`; a library or footprint change needs `drc` and `render`.

Helper tests: `python3 -m unittest discover -s .claude/skills/verify-marathon/tests`.
