# bom

## Sub-features

The bill of materials from the schematic, one row per value and footprint, with references and
quantities.

## How to get to it

In KiCad: Schematic Editor, Tools, Generate Bill of Materials. On the command line:
`kicad-cli sch export bom pcb/marathon.kicad_sch`.

## Driving it

```sh
python3 .claude/skills/verify-marathon/verify.py drive --run "$run" --feature bom
```

## What proves it works

`PASS drive bom`, and `head-bom.csv` differs from `main-bom.csv` only in the rows the change meant
to touch (`diff` the two files). When values change, `bom/README.md` must match the new rows. As
of 2026-10-30, `main` has 39 rows and 49 parts.
