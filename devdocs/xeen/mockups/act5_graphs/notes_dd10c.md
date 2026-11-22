## DD-10C Gemstone Mines, north pocket (Act V update)

D6 · S · party 48 → 51 · 40–50 · 20 · treasure 5 · Q-D7 (diamonds), repeatable · D-27

![DD-10C](act5_graphs/dd10c.svg)

The pocket is **built** (phase 3, in scratch: `briefs/dd10c/L4/NOTES.md`, `output/studio_cal/dd10c/`) from the Act III
graph as D-27 approved it ("layout as drawn; moves to Act V"). It has 6 rooms = 6 sectors, 10.94 M units², 3 plank
doors, 1 chest and one loop, and its audit is 0 / 0. This update covers only what phase 5 adds: the monsters on
gen.py's 20 marked spots, the live exit to D6's adit and the Act V map row. It also gives the roach nest a story, now
that D-27 has taken the roaches out. The layout is not redrawn.

- **What it is.** The diamond quarter of the source's Gemstone Mines (dark maze0039, aaze0039), reached by its own
  adit in D6's southern crags. Hector's diamonds come only from here (D-27: "Few who go there come back.").
- **Critical path.** The north adit (`entrance:d6_adit`, quiet), the lava gallery, the diamond cavern's five veins
  (`q-d7.diamond_veins`).
- **Way back.** Through the cold nest and the collapse to the lava gallery, round the loop.
- **Off the path.** The crystal grotto: a dead end with the miner's chest (T5). The collapse's rubble. The cold nest.
- **Loop (1).** The lava gallery, the diamond cavern, the cold nest and the collapse (built).
- **Set piece.** The diamond cavern: five `xdvdiam` veins with white glints in black glittering rock, the seam's red
  light at its west end, and the false vein ("A gem exploded!", 28 fire to every member once; built and scaled to
  Act V).
- **Monsters (20) and kill XP.** Floating Eye 40 (11570) × 14, Terrible Eye 50 (11571) × 4 and Patrol 50 (11610) × 2,
  the three families MAPS §0 names. By room: lava gallery 3 + 1 Patrol, cavern 4 + 2, grotto 1 + 1, collapse 3 + 1
  Patrol, nest 3 + 1.
  - XP: **11.50k per member** (46,000 / 4), MAPS §0's 11.5k: **0.0 %**.
  - Groups of 2–4 on gen.py's spots, as built. Quiet: the adit (D-11.3). D-32: every opening is 320–400 high, and
    none of these is a big monster.
  - Rest encounters: 10 % from the two eye rows (D-39).
- **Treasure.** The grotto's chest is T5 (built). The map card's treasure level is 5.
- **Original lines.** "Exit the Gemstone Mines?" (aaze0039:0, the exit preset's meaning), "Diamond vein" (:1),
  "You've got all this vein has to offer." (:10), "A gem exploded!" (:11).
- **Door to D6.** D6's `door:dd10c`, `thing:dd10c_adit`: a cave mouth in its timber frame, asking "Enter the mine?".
  - **Inside arrival:** `entrance:d6_adit` (the name D6 assumes) at the map's start, (0, 192, 0) in the map's frame
    (the mouth at y 0), facing north (512).
  - **Return:** the exit preset in the adit's south wall, replacing the boarded panel and its line, to D6's installed
    `entrance:dd10c_adit` (−9216, −16384, 2688) facing 512. That point is one cell north of the mouth (mouth at sketch
    y 97, point at y 96), facing away from it. **It matches.** gen.py sets `D6_LIVE = True` and `D6_ARRIVAL` to this
    point; `playtest_exit.yml` measures it.
  - The height disagrees between sources: D6's NOTES write z 2624 and the installed sidecar writes 2688. The exit
    uses the sidecar's value; A6 confirms which is right.
- **Hooks.** `q-d7.diamond_veins` on the five veins (built). The refill reads `q-d7.refill_c` 113143 on entry
  (built). Map qbit 117240 `arrived_once` stays in DD-10C's own block, 117240–117279.
- **Textures.** As built: the mines family, MM7 7d35 with 6d18's black lava rock, `lavatyl`, d37 `gcrysc3` and
  `xdvdiam`. 16 of S's 30, 0 of 4 new.

**DECIDE items** (options in the graph file; the proposed default first)

1. **The mix.** (a, proposed) Floating Eye × 14 on the 'a' spots. On the 'b' spots, Terrible Eye × 4 and Patrol × 2
   (one in each drift nearest the adit): 11.50k, 0.0 %. gen.py gains a third slot for the two Patrol spots. (b) Eyes
   only, Terrible Eye × 6 on 'b', gen.py unchanged: 11.50k. (c) Floating Eye × 12 and Patrol × 8: 12.00k, +4.3 %.
   Evidence: MAPS §0 names all three families. Depends: A2's recount.
2. **The roach nest without roaches.** (a, proposed) Keep the built egg cases as the cold nest: cracked and empty,
   hover "Empty egg cases", the line "Split and cold. Whatever hatched here was eaten by whatever lives here now.",
   the warm ash glow made cold. (b) Drop the egg cases. (c) Keep them, no line. Depends: A3 (one map-local line).
3. **Rest encounters.** (a, proposed) 10 % from the two eye rows (D-39); the Patrols are placed only. (b) 0.

**Requests to other lanes**
- **A2:**
  - The map row 9161 to Act V: party 48–51, levels 40–50, treasure 5, 20 monsters. `source/maps.yml`'s DD-10C row
    already says Act V; check `map_rows.yml`.
  - The Act V recount: DD-10C 20 at 11.50k. The Act III group DD-10+11 no longer counts it (D-27).
- **A3:** under 2 (a), the cold nest's line (map-local). Hector's D-27 line, if it is not in yet.
- **A6:**
  - Confirm `entrance:dd10c_adit`'s height (NOTES 2624, sidecar 2688).
  - D6's `door:dd10c` names `arrival: entrance:d6_adit` and drops its placeholder text at DD-10C's install. Its
    `project.yml` neighbour already says D6's door lands at the start.
- **S:** nothing new. The eyes and the Patrol are D6's bound rows.

**State and next steps.** This update was written on 2026-11-21. The graph, the SVG and these notes are new; the PNG
`output/studio_cal/a8_s11/png/dd10c.png` (headless Chrome) has been checked. The map itself is unchanged in scratch.
Once the decider answers, phase 5 sets `PHASE5_ROWS` (and the third slot under 1 (a)), `PHASE5_MONSTERS`, `D6_LIVE`
and `D6_ARRIVAL` in `output/studio_cal/dd10c/tools/gen.py`, the map card slots, the playtests (hostility, exit), then
install, bake and 4 of 4 (`briefs/dd10c/L4/NOTES.md`, "What phase 5 adds").
