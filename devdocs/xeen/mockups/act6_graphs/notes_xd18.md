## XD-18 Dragon Cave

X7 · M (few, strong) · party 60 → 64 · 66–85, Dragon King 110 · 40 + the King · treasure 6 · Q-C25 (the Dragon Tax,
the library of Dragon Lore, the Dragon King), optional

![XD-18](act6_graphs/xd18.svg)

The source's Dragon Cave (xeen maze0050 with mazex130–132, one 32 × 32 level, aaze0050) as one BLV of two floors in
the black crag at X7's north rim, 1,024 apart (0, −1,024; z 0 is X7's mouth floor 2,150). It has 25 review rooms,
about 33 sectors, about 44 M units² and 7 doors.

- **What it is.** The dragons' cave behind the tax road. The Dragon Tax Office stands in its mouth before the first
  dragon (D-5.2). Scaldrith takes 2,000 gold and 20 gems once, and the inner door throws out anyone who has not paid.
  Beyond it are the upper halls, the great roost, the starwell open on the world's rim, and the library of Dragon
  Lore with the Dragon King's hall behind it.
- **Critical path.**
  1. The mouth (`entrance:x7_mouth`, quiet) and the tax office's hall. Scaldrith's door (house 4852) for the tax,
     and the waiting room's lectern (volume 1).
  2. The inner door (`q-c25.inner_door`), the scorched passage, the bone hall and the roost ledge.
  3. The fire crossing and the stair head. The stair is walked down to the stair foot.
  4. The great roost, the ember gallery and the library's east leaves (volumes 2–4, the ledger).
  5. The King's door with shelf 5 beside it, then the Dragon King's hall.
- **Off the path.** These rooms lie off the critical path:
  - The acid hollows and the last taxpayer: a knight's remains, his strongbox (a chest) and a tax receipt.
  - The sulphur vents (the floor-0 loop) and the egg cave (a chest).
  - The steaming pools, the east den (a chest) and the old roost.
  - The starwell, the frost den and the rime cave (a chest).
  - The King's hoard behind his dais, open at his death (a chest).
- **Loops (3).**
  - Floor 0: from the bone hall to the stair head by the ledge and the fire crossing, or by the acid hollows and the
    sulphur vents.
  - Floor −1 east: into the roost directly, or round by the steaming pools and the old roost.
  - To the library: by the ember gallery to its east leaves, or by the starwell and the frost den to its west leaves.
- **Set pieces.**
  - The great roost: a cavern 3,072 × 2,560, 2,048 high through both floors, with the upper floor's ledge along its
    wall and three pairs of dragons wheeling in it.
  - The starwell: a cold hall whose north wall breaks onto the void beyond X7's rim, a slot of stars 2,048 wide with
    its sill 640 above the floor, so nobody walks out (`sky: true` on the slot).
  - The library of Dragon Lore (d16's worked stone, shelves at claw height) and, behind it, the King on a dais of
    heaped gold under a 1,536 roof.
- **Dragons and their halls (D-32).** The cloud dragons' bodies are 487 high, radius 238, and they fly.
  - **Low openings.** Every party passage between two dragon halls is 256 wide and 288 high, and so are the library's
    two pairs of leaves and the King's door (two bronze leaves 512 × 288). A dragon does not pass any of them. This
    covers the scorched passage into the bone hall, the hollows, the vents, the den, the pools, the old roost, the
    frost den and the rime cave.
  - **Dragon roads.** Only the dragon roads are 768 high: bone hall to ledge, roost to ember gallery, roost to
    starwell. So the roost's flyers range over the roost, the ledge, the gallery and the starwell, and no further.
  - **Heights.** Hall heights fit the bodies: 896 (the egg cave), 1,024 (caves and dens), 1,280 (the bone hall, the
    old roost, the library), 1,536 (the starwell, the King's hall) and 2,048 (the roost).
  - **Office.** The stair is a low tunnel, so the floors keep their own dragons, and nothing big reaches the office.
- **Monsters and kill XP.** Acid Dragon 66 (11641) × 9, Fire Dragon 75 (11642) × 17, Frost Dragon 85 (11643) × 14 and
  the Dragon King 110 (11645). These are the source's 17 Fire and 14 Frost Dragons, with the Acid tier as the young
  near the mouth. There are no Water Dragons: 60 is under the band, and they are X2's lake dragons (D-54).
  - XP: **66.64k per member** (266,569 / 4) against MAPS's 64.6k (+3.2 %); **69.94k with the King** (+8.3 %).
  - Floor counts: floor 0 12 (Acid 9, Fire 3), floor −1 28 (Fire 14, Frost 14) and the King with two Frost Dragons.
  - Groups of 1–2: pairs, and a pair and one in the three-dragon rooms.
  - Quiet rooms (D-11.3): the mouth, the tax hall, the waiting room, the scorched passage and the King's door
    antechamber.
  - 40 is under M's floor of 45: a NOTES exception line (DECIDE 1). Rest encounters are 10 % from the dragons at Dif 5
    (DECIDE 5).
- **Treasure.** Five chests at T6: the last taxpayer, the egg cave, the east den, the rime cave and the King's hoard.
  The urn on the counter is dressing.
- **Original lines.** These are used as follows:
  - aaze0017:0 "The Dragon Cave smells pretty bad.  Are you sure you wish to enter?": X7's door (A5).
  - aaze0050:0 "Dragon tax!  2000 gold pieces and 20 gems fly from your packs and into the urn. …": the meaning of
    Scaldrith's payment.
  - aaze0050:1 "The urn is empty and powerless.": the urn's click once the tax is paid.
  - aaze0050:2 "Not having enough money to pay the Dragon Tax, you are teleported outside.": the meaning of the inner
    door's fail.
  - aaze0050:5–10: the hovers "Dragon Lore Volume 1" to "Volume 5" and "The Art of Taxation".
  - aaze0050:12–16, :18: the Loremaster titles to "Taxman Emeritus" (A3's six awards). The 50,000–500,000 experience
    is dropped.
  - aaze0050:3: the Intellect refusal, ledger only, because A3's hooks have none.
  - aaze0050:17 "Exit Dragon Cave?": the exit preset's meaning (D-24).
- **Door to X7.** A5's `thing:xd18_mouth` (`door:xd18`) at [56.5, 29] is a 768 × 640 mouth in the rim crag. Its
  front is at (−3840, 17408, 2150), facing south.
  - **Inside arrival proposed:** `entrance:x7_mouth`, about 384 inside the mouth, facing north (512) toward the
    office's front and the urn.
  - **Return:** the exit preset to X7's `entrance:xd18_mouth` (56, 31) = (−4096, 16896, 2150), facing south (1536).
- **Hooks.** The graph places these:
  - `q-c25.inner_door`: the inner door in the tax hall's north wall. With `tax_paid` (112500) it opens for good. Without
    it, the hook's fail_text plays and `{exit: x7}` moves the party to `entrance:xd18_mouth`. From inside the door
    always opens.
  - `q-c25.volume1`: the waiting room's lectern.
  - `q-c25.volume2` to `volume4` and `q-c25.taxation`: the library's shelves and its ledger stand.
  - `q-c25.volume5`: shelf 5 in the King's door antechamber.
  - Scaldrith (5702) is behind `door:tax_office` (house 4852) in the tax hall: the tax, the Great Wyrm promotion and
    the Dragon Grandmaster.

  Map qbits: 118100 the inner door drawn open; 118101 the King slain (the hoard's grate open). 118102–118109 are free.
- **Textures.** MM8 Dragon Cave d17, as A6 assigned. On the shipped BLV it is only three textures: `t68a02b` (walls,
  roofs, floors), `t68a02a` (worn floors, the dragon roads) and `solid01`.
  - The office, the waiting room, the library and the King's door form one worked area in MM8 Dragon Hunter's Camp
    d16: `gtrlwal3`, `gtrlflr`, `tfb11`, `gtrlrf2`, `gtrlrf3`, `gtrltrm2`, `t1books1`, `hhr1p`, `trim9_32`.
  - The steaming pools use `wtrtyl`.
  - About 15 of 45, with at most one new texture (`xdhoard`, heaped gold for the dais and the hoard; optional).
  - XD-10 on X5 uses the same `t68a02b` rock. XD-18 reads apart by its worked rooms, scorched floors and the hoard
    (DECIDE 6).
  - Music 13, map id 9143.

**DECIDE items (XD-18)** (options in the graph file; the proposed default first)

1. **Count.** (a) 40 cloud dragons (Acid 9, Fire 17, Frost 14), 66.64k (+3.2 %), 69.94k with the King (+8.3 %), with a
   NOTES exception under M's 45 (as XD-16, D-47 Q1). (b) Five Great Hydras 65 for five Acid Dragons, 66.47k.
   (c) 45 dragons, 72.91k (+12.9 %).
2. **The tax and the ejection.** (a) The inner door's click: with `tax_paid` it opens for good; without it, the
   fail_text and `{exit: x7}`. The office stays open to all. (b) A step plate behind an always-open door. (c) A plain
   refusal, no ejection.
3. **The Dragon King's look.** (a) His own recolour skin on `xeen_cdr1` (for example `xcdr_king`, black with gold),
   as Xeen's Pet's `xcdr_pet`, no Meshy. (b) The Fire Dragon's skin, scaled.
4. **The dragons' reach (D-32).** (a) Low openings (288) on every party passage, the library's leaves and the King's
   door; 768 dragon roads only between the roost, the ledge, the ember gallery and the starwell; a headless check that
   a dragon stays in the roost. (b) Tall openings everywhere.
5. **Rest encounters (9143).** (a) 10 % cloud dragons at Dif 5 (never the Water Dragon or the King). (b) 0.
6. **Textures.** (a) d17's rock, with the worked area in MM8 d16 and optional `xdhoard`. (b) MM6 Caves of the Dragon
   Riders 6d20 (`vlcwl1lg`, the mouth shell's rock) with d16. (c) d17 alone.

**Requests to other lanes**

- **A2:** the Act VI recount (40 + the King, 66.64k / 69.94k); row 9143 (rest 10 %, cloud dragons at Dif 5).
- **A3:** ORIGINAL_LINES rows aaze0050:0–3, :5–18 and aaze0017:0 (ledger, hovers, exit meaning). Map-local lines for
  the urn before payment and the knight's receipt. Confirm that `q-c25.inner_door`'s fail is followed by
  `{exit: x7}` to `entrance:xd18_mouth`.
- **A4:** confirm `door:tax_office` in the tax hall as the office's house door; nothing else.
- **A5 (X7):** `door:xd18` into `entrance:x7_mouth` once XD-18 is installed; the return `entrance:xd18_mouth` is
  unchanged.
- **A6:** the d17 line in detail, with the d16 worked area; `xdhoard` registered if it is made.
- **S:** the Dragon King's own recolour skin (DECIDE 3).
- **AU:** nothing required (shipped wind for the starwell, a coin clink for the urn).
- **A1:** nothing (house doors, `{exit: x7}` from an event, kill events and `sky: true` exist).

**State and next steps.** The graph, the SVG and these notes are written (lane A7's graph sub-agent, 2026-11-21,
sixteenth session). The render printed no overlap. The PNG from headless Chrome
(`output/studio_cal/a7/phase6_graphs/xd18.png`) was looked at. Nothing is built or installed. Next: the decider
answers the DECIDE items, then L1.
