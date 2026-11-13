# Outdoor code batch six (2026-11-13, morning): the list

From Harmondale's round three (`devdocs/map_studio/briefs/mm7_7out02/L4/NOTES.md`, "Round three") and what
`rounds/NEXT_CODE_BATCH.md` still has open for outdoor maps. In order:

1. **Steps the party cannot climb (a playability fault, first).** The build draws steps (a dais of `parts`, `stairs`
   without `ramp`) without the hidden sloping face the originals put over every outdoor flight: Harmondale's fort
   (`Fort__1`) has an invisible face with attributes 0x3108 over each flight, and the party walks up it in 0.8 s; the
   rebuild's party stops at the first riser, with steps of 32 or a block of 128 alike. Read what the originals do
   (the face's flags, where it lies, how the game's outdoor movement uses it), and build the same for every flight
   and stepped part a party should climb. Prove it on a copy of Harmondale with the walk climbing the dais on foot.
2. **A headless walk that hangs:** with the dais as one 64-high part the game sat at 100 % CPU in `walk_to` for
   minutes without a line (`output/studio_cal/mm7_7out02/repro/fort_step/run.sh
   output/studio_cal/mm7_7out02/repro/fort_step/one64_project one64`). If the cause is in the game (likely), say
   exactly where and stop; if it is in what the build writes, fix it.
3. **Ground one cell wide** (`ground[].line` with a width): grass strips along ridges and dykes.
4. **Ids for scattered decorations** (`scatter[].id` usable by `set_sprite` and `hide`): the seasonal trees.
5. **A hanging sign and an event with no title** (the gate sign).
6. **The measure pairs models one to one:** a model of four ring pieces pairs with one wall and the rest count as
   only in the rebuild; the castle's 16 models against one plot (`cmp_final3/differences.json`, `buildings`). Pair
   by footprint coverage, as a building made of several models is still one building.
7. **`heights.ridges` with `width: 2` on a diagonal** raises the floor nodes beside the line.
8. From NEXT_CODE_BATCH.md, outdoor, still open: one roof over a hall that is not convex (the Sanctum), an arcade;
   a described rim that reads as well as a grid (Harmondale's agent showed the described west rim puts a cone where
   the original has a long snow-capped shoulder: `output/studio_s4f/pics/rim_desc_h/diff/07-rim-w.png`); the
   empty-hint events of the measure.
