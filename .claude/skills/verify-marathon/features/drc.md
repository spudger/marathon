# drc

## Sub-features

The board's design rules check with zones refilled: violations, error-severity violations,
unrouted connections, schematic/board parity issues, and a count per rule type.

## How to get to it

In KiCad: PCB Editor, Inspect, Design Rules Checker, with "Test for parity between PCB and
schematic" on. On the command line:
`kicad-cli pcb drc --refill-zones --schematic-parity pcb/marathon.kicad_pcb`.

## Driving it

```sh
python3 .claude/skills/verify-marathon/verify.py drive --run "$run" --feature drc
```

## What proves it works

`PASS drive drc`, `"errors": 0` and `"parity": 0` on the `head:` line, and every change in
`unconnected` or `types` against `main:` explained by the change. A routing change should lower
`unconnected`. As of 2026-10-30, `main` has 12 `lib_footprint_mismatch` warnings, 48 unrouted
connections and 0 parity issues. `head-drc.rpt` lists each item with its location.
