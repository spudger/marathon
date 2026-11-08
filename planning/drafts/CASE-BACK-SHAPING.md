# Shaping the case's back

Research whether a shaped back would make Marathon more comfortable to hold, before designing one.
The owner asked for this on 2026-11-08, to follow the slimming in spudger/marathon#30.

## Where it starts

- The case is 18.5 mm thick with a flat back (spec 027, "Slimming"). Its depth is set by the
  battery's 11.3 mm and the Pi's stack of about 10 mm behind the board.
- The battery fills x 112 to 175 and y 28 to 88, and the Pi x 34 to 99 and y 28 to 58 (board
  coordinates). Every other part on the back is 3.2 mm tall or less.
- A chamfer or rounded edge of about 5 mm around the back fits around the battery. The edges would
  then read about 15 mm while the center stays at full depth. That figure is an estimate from the
  part positions, not a model, and the corner screw counterbores would sit in that band.

## What to find out

- How hand size, grip, and session length relate to edge thickness, back curvature, and grips on
  handhelds of about this size and weight.
- What a chamfer, a rounded edge, a curved back, and grips under each end would each change in how
  it holds, and what each costs in print time and in the design.
- Whether the left end, which has only short parts behind it, can be thinner than the rest.

The design flow takes it from there, if the research says shaping is worth it.
