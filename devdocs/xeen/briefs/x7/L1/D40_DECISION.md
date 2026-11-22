# X7 Mount Firestone L1: decision (D-40)

Decider D-40, 2026-11-20. Wins over the L1 plan and NOTES.md where they differ.

**APPROVAL: approved with changes.** Geometry (L2/L3) may start. The changes, each owned by the lane named:

1. **Chest levels by who reaches them.** The map's treasure level of 5 stays for the north only. The south is reachable from X1 at party level 4–7, so its chests get their own levels (`chest: {level: N}`):
   - the orc outpost and the orcs' den: 1;
   - the watch's pay chest: 2;
   - the miner's cache (an Act II party can reach it from X4's road): 3;
   - the knight's remains and the hydras' wallow: 5;
   - the dragon's hoard: 6.

   Owner: A5.
2. **The south's orcs count in Act I.** The south orcs (about 0.5k) are the act whose party meets them, Act I, not Act V. This is D-1.2's rule turned round for monsters below a map's band. Act I is at 1.10 today, so it would come to about 1.16.
   - If Act I is then over 1.15, the trim comes first from X7's south: 10 markers down to 8, dropping the ones farthest from the arrivals. Both arrivals must keep a first fight within 2,000–6,000. X1 stays as built.
   - X7's Act V share becomes about 75.4k of 76.4k, inside the band.
   - A2 counts it; A5 trims if needed.
3. **Lava must be lava before L4 is done.** A1 adds a lava tile set to the Xeen world's outdoor tileset, so that `tile_set: lavtyl` passes validation. The engine's `liquids.yml` already has a lava entry for `lavtyl`. The lava burns as MM7's lava does.
   - The lake, the crater and the rivers are never left as water: a party must not be able to swim to the island.
   - The 8 golems stay on the island, either standing or with a home radius inside it.
   - Owners: A1 for the tile set, A5 for the map.
4. **The deadly north is announced.** The Gap's signpost carries a short warning, for example "North: Mount Firestone. Dragons. Turn back."
5. **POIs:** at most 28 at L4. Merge first (the idols into XD-16's door, the outpost chest into the outpost, giving 22). If that is not enough, take the click off the third signpost.
   - Spacing between POIs: the median is 3,280, above the 1,300–2,600 band. This is accepted for a trap map, with one line in NOTES: the north is sparse by design, and the 6,000 rule (farthest 5,700) and the wild-land figure (0.085) both hold.
   - Owner: A5.
6. **X1's side of the reopened edge.** When X1's north edge reopens, A5 measures the first fight from X1's `entrance:north_road` (2,000–6,000). If it is under 2,000, one X1 pair moves.
7. **Concept corrections at L3 (the plan wins).** In the arrival view:
   - the range should be bare peaks, with the Gap's saddle visible from the X1 road;
   - the road should be 3–4 m of pebbles, not cobbles;
   - the Dragon Tower stays small at its planned distance.

   In the signature view:
   - the rim should be a cove seen across, not a straight rim seen side-on;
   - the hut and the mesa castle leaked from X6's reference picture; ignore them.

   Owner: A5.
8. **Correct the Speed claim.** The Well of Speed is not the world's only permanent Speed: XD-08's juices give +2 and DD-09's black barrel gives +1. A2 lists the well in the permanent-stat ledger under Act I, since the party can reach it from X1.

**Checks against the figures:**
- **Kill XP:** 75.9k against the planned 76.4k (−1 %). The arithmetic checks out: 27 dragons, 38 hydras, 8 golems and 28 orcs, 101 hostiles. 101 is inside the trap band of 90–110.
- **First fight:** 4,400 from the X1 road and 4,900 from the X4 road, both inside 2,000–6,000.
- **POIs:** 24, inside the trap band of 22–28.
- **Sablewing:** 4,400 from any fight, well above the 2,500 town buffer.
- **The north:** monsters are 5,200 from the north road and 5,400 from the Gap. Dragons are 8,600 from the tax road and 6,100 from the Volcano Cave.
- **Relief:** 3,360 inside the box.
- **The rims:** the north rim at y 24 matches X4's, and the east rim at x 104 matches X1's. The edge spans and heights match X1 (1,850 at x 69) and X4 (1,300 at y 66).

---

**1. The south slopes' band**
- **DECISION:** (a). Orcs 5–10 at difficulty 1, as drawn. D-5.2's "levels 20–30" is the party's level for Sablewing's Master teaching: `teachers_plan.yml` already puts him in Act III at level 25. No warband on X7.
- **WHY:** MAPS makes the south the safe edge of a trap map, and an Act I party reaches it through X1's road and XD-05's back gate. The warband (16–26) belongs to the Darkside's Temple of Bark. On X7 it would be a second trap for Act I and II parties, and it would put Act I's budget further over.
- **WHO ACTS:**
  - A5: nothing beyond change 2.
  - A2: the map's rows as requested, and the Act I count.
  - Orchestrator: change MAPS X7 from "orcs 5–12 / 6–12" to "orcs 5–10", and note D-5.2's clarification.
- **REVERSIBLE:** yes, cheaply (one slot).

**2. The Shrine of Fire twice**
- **DECISION:** (a). X7's Shrine of Fire is daily: a temporary Fire resistance before the fire north. The Well of Speed (+2 Speed, once per character) is the map's permanent device. X4's permanent shrine stays as built.
- **WHY:** A daily fire ward just below the fire dragons and lava golems is useful where it stands, and X4 needs no rebuild or re-bake.
- **WHO ACTS:**
  - A5: draws the two events.
  - A3: the texts. "Shrine of Fire" / "You don't think anyone is listening." (aaze0018:5-6) is the reply after use.
  - A2: the ledger (change 8).
- **REVERSIBLE:** yes (an event change).

**3. The way back into Shangri-La**
- **DECISION:** (c), not (a). The cleft at [73, 48] is a rockfall from the X7 side. The first time a party leaves the valley by its back passage, it opens from inside: a new qbit is set, for example `xd17.cleft_open`. From then on it is a two-way door. Before that, X7's side says only: "Fallen rock chokes the cleft. Cool air, and a smell of grass, seeps between the stones."
  - XD-17's back-passage exit arrives at the cleft.
  - No spawn marker within 2,000 of the cleft's arrival point.
  - Dragons at least 4,000 from it.
- **WHY:** The first way in stays the source's reveal through XD-16, "Beyond the last cave, cool air". The shortcut follows the house pattern: opened from the far side, as XD-05's back gate and X6's coach-yard gate are. The rock on the X7 side shows two states (closed and open), swapped by the qbit.
- **WHO ACTS:**
  - A5: X7's door condition and rockfall swap, and XD-17's back passage and its event.
  - A3: the qbit, the door's two texts and Q-C26's `where`.
- **REVERSIBLE:** yes (only the condition on the door changes).

**4. The Ever-Hot Lava Rock**
- **DECISION:** (a). On the cooled-flow island in the lava lake, reached by its causeway and guarded by the 8 placed Lava Golems (55).
- **WHY:** It matches MAPS. Q-C14 is a level-45 quest, so the walk through hydra country (mean level 52) is the right test, and the Widget is not needed before M40.
- **WHO ACTS:**
  - A3: Q-C14's `where` reads "on the cooled-flow island in the lava lake under the north rim", and the hook's text uses the original line aaze0018:8.
  - A5: the island and the golems; change 3.
  - A1: the lava tile set.
- **REVERSIBLE:** yes (a hook's place).

**5. The north's mix**
- **DECISION:** (a). Hydras at difficulty 3 [1, 3], dragons at difficulty 5 [1, 2], 8 placed golems: 101 hostiles and 75.9k. The Frost Dragon (85) stays in XD-18.
- **WHY:** Both figures are inside their bands. Difficulty 5 gives MAPS's acid and fire dragons, where difficulty 4 would mostly give water dragons. Dropping to 90 hostiles would cost XP for no gain.
- **WHO ACTS:** A2 writes the X7 map row: the three slots with weights 21/40/39, perception 5, MOUNTAINS, the placed rows 11593 ×8, 11030 ×2 and 11032 ×1, `row_before_install: true`, and the Act V recount.
- **REVERSIBLE:** yes (slot changes).

**6. The Dragon Cave track**
- **DECISION:** (a). The track runs through hydra land as drawn. "Before the first dragon" in D-5.2 means inside XD-18. Dragons stay at least 6,000 from the track and from the tax office's mouth; they are at 8,600 now.
- **WHY:** The Great Wyrm promotion is at about level 50, inside the hydras' band. A corridor kept clear of monsters would undo the trap map for no reason.
- **WHO ACTS:** A5 keeps the distances. A7 builds the tax office inside XD-18's mouth (phase 6).
- **REVERSIBLE:** yes (moving markers).

**7. The signature view**
- **DECISION:** (a). The lava cove from its west lip at [67, 25], with the Gap's view of the whole north as an extra tour shot.
  - Three lava falls on the cove's south wall, at least 1,500 apart, pouring north.
  - Their faces must read from the camera at L3: A1's decoration facing has landed, so use it.
  - The near lip must not hide the falls.
- **WHY:** The view is earned and the falls face the camera, which is D-35's lesson applied from the start.
- **WHO ACTS:**
  - S: a lava preset of the sand-fall model (`presets.py` already takes one); emissive and scrolling.
  - A5: places the falls, takes the tour shots and checks them.
- **REVERSIBLE:** yes (a camera and decorations).

**8. The dwarves' watch**
- **DECISION:** (a). Abandoned, with no NPC. The warning lives in the place itself: a short note with the pay chest (for example "The dragons came south. Pay owed to the end of the month. Nobody stays.") and the Gap's signpost (change 4).
- **WHY:** `x7.yml` has no people, and an abandoned post needs no extra NPC. The note does the warning a lookout would have done.
- **WHO ACTS:**
  - A5: the watch and the note's event.
  - A3: optionally, the note's text.
  - A4: nothing.
  - Orchestrator: MAPS's "dwarf outpost" becomes "the abandoned dwarves' watch".
- **REVERSIBLE:** yes (A4 can add a lookout later).

**9. The sky**
- **DECISION:** (a). Cloudside's fair preset with the `ashen` theme (already mapped in the world's `sky.yml`), and ash fall on about 40 % of days.
  - The ash chance lives in X7's own files: an ash word in `atmosphere.yml`, carried into the scene's weather and read as the map's ash chance. It does not go in the engine's `weather.yml`.
  - D6 uses the same word.
  - MM6–MM9 stay unchanged.
- **WHY:** The lanes' rule is that Cloudside maps use the shipped presets. `ember` is the Act V failing-sun look, and `plane_fire` belongs to the planes; either would blur the faces.
- **WHO ACTS:**
  - A1: the ash word and how the game reads it.
  - A5: `ash: 40` in `atmosphere.yml`.
  - Orchestrator: MAPS X7's sky line becomes "fair, ashen theme, ash fall".
- **REVERSIBLE:** yes (one data field).

---

**Other actions this approval relies on:**
- **A1:**
  - X7's edge-span and outdoor-travel rows once X7 is installed (generated).
  - The lava tile set (change 3).
  - The ash word (question 9).
- **A3:**
  - The orc outpost's burn hook (`x7.orc_outpost`, aaze0018:3-4, with its +1,000 XP scaled).
  - The idols' hint as flavour text.
  - The texts for questions 3, 4 and 8.
- **A4:** confirms Sablewing (4720) at [76, 90]. No lookout.
- **A6 / S:**
  - the lava-fall preset;
  - the demon and devil idols (MM6 engine statues if they serve; otherwise new models);
  - black basalt rock for the Dragon Tower's crag.
- **A7:**
  - door heights and footprints for L3: XD-16 at [66, 45] facing west, XD-18 at [56, 30] facing south with the tax office just inside, FD-04 at [29, 32] facing south;
  - XD-05's back-gate rockfall opened, its exit pointed at [88, 100] once X7 is installed.
- **A5:**
  - reopen X1's north edge when X7 is installed (change 6);
  - keep XD-16, XD-17, XD-18 and FD-04 sealed until each map exists.
- **Orchestrator:** the MAPS X7 sheet edits listed under questions 1, 3, 8 and 9.
