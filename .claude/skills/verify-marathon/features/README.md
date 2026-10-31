# Marathon project proofs

Each needs a launched run (`verify.py launch`) and a passing Doctor. For a full sweep, drive them in
this order:

- [erc](erc.md): schematic electrical rules, with counts per rule type.
- [drc](drc.md): board design rules, unrouted connections and schematic/board parity.
- [bom](bom.md): the parts list grouped by value and footprint.
- [render](render.md): schematic, front, back and 3D images of the board.
