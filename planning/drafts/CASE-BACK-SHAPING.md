# Shaping the case's back

Research whether a shaped back would make Marathon more comfortable to hold, before designing one.
The owner asked for this on 2026-11-08, to follow the slimming in spudger/marathon#30.

## Where it starts

- The case is 18.5 mm thick with a flat back (spec 027, "Slimming"). Its depth is set by the
  battery's 11.3 mm and the Pi's stack of about 10 mm behind the board.
- In board coordinates, spec 022 reserves x 112 to 179 and y 28 to 87 for the battery, 11.3 mm
  deep; the stand-in cell fills x 114 to 177 and y 32.5 to 82.5. The Pi fills x 34 to 99 and
  y 28 to 58, about 10 mm deep. Every other part on the back is 3.2 mm tall or less.
- The case's outer walls are at x 17.9 and 182.1, and y 17.9 and 97.1. A 45° chamfer on the back
  edge that keeps 1.2 mm of wall over the battery space could be about 2.5 mm at the right end,
  where that space comes within 3.1 mm of the wall (about 4.5 mm over the stand-in cell alone),
  and up to about 9 mm along the long edges. These are estimates from the positions, not a model.
  The corner screw counterbores, 7.1 mm in from the walls, sit in that band.

## What to find out

- How hand size, grip, and session length relate to edge thickness, back curvature, and grips on
  handhelds of about this size and weight.
- What a chamfer, a rounded edge, a curved back, and grips under each end would each change in how
  it holds, and what each costs in print time and in the design.
- Whether the left end, which has only short parts behind it, can be thinner than the rest.

The design flow takes it from there, if the research says shaping is worth it.
