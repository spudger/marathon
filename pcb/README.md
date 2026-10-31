# PCB

KiCad 10 project for the Marathon main board. Open `marathon.kicad_pro`. The schematic lives here with the layout because KiCad keeps a project's files in one folder.

**Status:** Phase 4, in progress. **Not ready for fabrication.**

- 160 x 75 mm, 2 layers.
- Placed: every part. The Raspberry Pi mounts on the back, inside the outline and clear of the battery area.
- Routed: every net, with ground pours on both layers.
- Footprints named `PROVISIONAL` still need checking against the real parts. The Alps switch footprints follow Alps' published land patterns.

## Checks

| Check | Result |
|-------|--------|
| ERC | 0 violations |
| DRC | 0 errors, 9 library-mismatch warnings |
| Unrouted connections | 0 |
| Schematic / PCB parity | 0 issues |

To re-run them from the repo root:

```bash
kicad-cli sch erc pcb/marathon.kicad_sch
kicad-cli pcb drc --refill-zones --schematic-parity pcb/marathon.kicad_pcb
```

## Planned

- Board renders (top, bottom, 3D).
- A `fab/` folder with Gerbers, drill files, BOM, and pick-and-place files for JLCPCB.
