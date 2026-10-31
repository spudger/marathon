# erc

## Sub-features

The schematic's electrical rules check: total messages, errors, warnings and a count per rule
type, on the snapshot and on `main`.

## How to get to it

In KiCad: Schematic Editor, Inspect, Electrical Rules Checker. On the command line:
`kicad-cli sch erc pcb/marathon.kicad_sch`.

## Driving it

```sh
python3 .claude/skills/verify-marathon/verify.py drive --run "$run" --feature erc
```

## What proves it works

`PASS drive erc`, and a `head:` line whose counts are no worse than `main:`, or whose new messages
the change explains. `head-erc.rpt` lists each message with its location. As of 2026-10-30, `main`
has 0 messages.
