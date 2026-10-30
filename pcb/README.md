# PCB

KiCad 10 project for the Marathon main board. Open `marathon.kicad_pro`. The schematic lives here with the layout because KiCad keeps a project's files in one folder.

**Status:** Phase 4, in progress. **Not ready for fabrication.**

- 160 x 75 mm, 2 layers.
- Placed: everything except the Raspberry Pi, which overhangs the top edge and has to move inside the outline.
- Routed: power, audio, and I²S. Not routed: the LCD, buttons, and IP5306 power key.
- Footprints named `PROVISIONAL` are sized for placement and still need checking against the real parts.

## Checks

| Check | Result |
|-------|--------|
| ERC | 0 violations |
| DRC | 0 errors, 12 library-mismatch warnings |
| Unrouted connections | 48 (LCD, buttons, power key) |
| Schematic / PCB parity | 0 issues |

To re-run them from the repo root:

```bash
kicad-cli sch erc pcb/marathon.kicad_sch
kicad-cli pcb drc --refill-zones --schematic-parity pcb/marathon.kicad_pcb
```

## Planned

- Board renders (top, bottom, 3D).
- A `fab/` folder with Gerbers, drill files, BOM, and pick-and-place files for JLCPCB.
