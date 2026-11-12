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

## Findings, 2026-11-09

A desk review of published studies and handheld reviews. Nothing was modeled or printed. The owner
will decide what to do with it later.

**Answer:** shaping probably helps, but by adding a rest behind each end for the middle fingers,
not by thinning the back. The evidence is hands-on reviews, not measured studies.

- **No study fits.** No published study tests back shape or edge thickness on a two-handed console
  of this size. The nearest are one-handed phone studies.
- **Flat backs draw complaints over long sessions.** Reviewers say so of the RGB30 (usable, not for
  hours), the TrimUI Smart Pro S, and the Retroid Pocket 4 Pro. One reviewer who tried the same
  Retroid with a flat and a gripped backplate preferred the gripped one, which "fills my hands
  better". The XF40H's slight rear curve gave the middle fingers "something comfortable to rest on".
- **Add-on grips sell well** for flat devices such as the RG35XX H and Miyoo Mini Plus. Buyers
  credit them with ending cramps; one maker claims sessions went from 40 to over 90 minutes. These
  are seller and buyer claims.
- **Rear bumps divide opinion.** One RG405M reviewer's fingers rarely reached its bumps, and one
  RG353M reviewer found them ugly.
- **Thinner does not mean more comfortable.** The thicker shapes get the praise (the XF40H at
  29 mm, the launch DS), and a rollable-display study found grip comfort rose with thickness.
- **Edge rounding matters a little.** A 72-person study (Lee et al., 2019) tested phone edge
  roundness from 0 to 4 mm and recommended 2.5 mm, but found width and thickness mattered more.
  That it carries over to a two-handed grip is an inference.

Comparable devices, from their makers or spec pages:

| Device | Size (mm) | Weight |
|---|---|---|
| Marathon | 164.2 x 79.2 x 18.5 | not known |
| Game Boy Advance | 144.5 x 82 x 24.5 | 140 g |
| Anbernic RG35XX H | 145 x 69 x 16 | 180 g |
| Retroid Pocket (reviewed above) | 169.9 x 84.1 x 15.6 | 255 g |
| Analogue Pocket | 86 x 149 x 22 | 275 g |

### Options for Marathon

- **A rounder back edge,** from the 1.0 mm fillet to a chamfer of about 2.5 mm (the estimate above).
  Small gain, small model change, and it still prints without supports.
- **Finger rests behind each end.** The largest gain, by the reviews. They add depth locally, and
  the back shell would no longer print flat on the bed unless the rests are separate glued or
  screwed parts.
- **A thinner left end.** It fits, but nothing supports a comfort gain, and the device would be
  lopsided.
- **A curved back overall.** It doesn't fit: the battery and the Pi fill the back.

### Still unknown

- How Marathon feels in hand. Only a print settles it.
- How tall a finger rest should be. No source gave a figure.
- Marathon's weight, guessed at 200 to 230 g.

The recommendation on 2026-11-09: print the flat 18.5 mm case and hold it before deciding on finger
rests, and add only the rounder back edge now.

### Sources

- [Retroid Pocket review, flat and gripped backplates](https://retrohandhelds.gg/retroid-pocket-nova-review/)
- [Game Console XF40H review](https://retrohandhelds.gg/game-console-xf40h-review/)
- [RGB30 review](https://retrohandhelds.gg/rgb30-unhinged-review/)
- [TrimUI Smart Pro S review](https://steamdeckhq.com/news/trimui-smart-pro-s-review/)
- [TrimUI Smart Pro review](https://www.miyoodiy.com/blog/i-love-this-handheld-trimui-smart-pro-review)
- [Retroid Pocket roundup](https://stealpicks.com/retroid-pocket-review/)
- [RG405M review](https://retrododo.com/anbernic-rg405m/)
- [RG353M review](https://retrododo.com/rg353m/)
- [RG35XX H grip, Printables](https://www.printables.com/model/1209522-anbernic-rg35xx-h-xbox-style-grip)
- [Comfort grip, Etsy](https://www.etsy.com/listing/1433111724/comfort-grip-for-miyoo-mini-plus-and)
- [Lee et al., Human Factors, 2019](https://journals.sagepub.com/doi/10.1177/0018720818792758)
- [Anbernic RG35XX H specs](https://anbernic.com/products/rg35xx-h)
- [Nintendo technical data](https://www.nintendo.com/en-gb/Support/Legacy-system/Technical-data-619479.html)
- [Analogue Pocket, Wikipedia](https://en.wikipedia.org/wiki/Analogue_Pocket)
