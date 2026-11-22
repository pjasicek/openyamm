# D5 and D6 L1 mock-ups: decisions (D-49)

Decider D-49, 2026-11-21. Where this file differs from the L1 plans and the two NOTES.md files, this file wins. Geometry (L2/L3) may start on both maps once A6 has applied the changes below.

---

## APPROVAL

### D5 Desert of Doom: approved with changes

1. **Two boulder clusters instead of one field (Q3).**
   - The east cluster holds the weathered sign and boulders 3–6, by the desert road where the plan's field is.
   - The west cluster holds boulders 1, 2 and 7 (7 asks the riddle), by the west road in the Desert of Doom. It stands at least 2,600 from the obelisk knoll and from the Last Water.
   - Within each cluster, every boulder stands within 400 of the next (a chained ring), so each cluster counts as one spot in the D-15 census. POIs: 24.
   - The concept's "fewer, smaller" boulders become four great boulders on the east side.
   - Owner: A6.
2. **The broken pyramid is one spot.** The fallen capstone (the obelisk hoard) lies at the broken pyramid's foot, within 400 of its click ("The pyramid portal has been destroyed.", aaze0013:12). One POI. Owner: A6.
3. **The monster band follows its named families (Q2).** MAPS D5 changes from "A 32–42, C 55" to "A 30–42, C 62".
   - The 30 is the Vulture Roc, the great birds' A tier; D4 already has it.
   - The 62 is the Elder Giant, the wild giants' C tier. At difficulty 1 it rolls 2 % of the time (about 0.5 at load).
   - MAPS's own rule is that a sheet's band contains its named families' tiers. These are installed families with fixed tiers, unlike D-47's new People rows.
   - Owner: orchestrator.
4. **The rim.** D5's project carries the rim rule, as D6 and X7 do: `rim: {cliff_y: 24, fall: death, sides: [north]}`.
   - The Barrier's frames and curtain are a blocking BModel up to the map's fly ceiling.
   - A party that still flies past the Barrier's ends falls to its death at the rim.
   - Owner: A6.
5. **POI spacing.** The median of 6,250 is accepted, with one NOTES line: 20–25 POIs on about 7,200 land cells cannot reach a 1,300–2,600 median. The 6,000 rule (farthest 5,540) and the wild-land figure (0.11) both hold. As D-40's line for X7.
6. **Relief re-measured at L4 inside the box.** The plan measures 2,579 on the drawing's model, too close to 2,500 to trust.
   - If it comes out under 2,500, raise the highland crest or the western hills.
   - Never deepen the salt pan.
   - The pyramid is a BModel and does not count. As D-31.
7. **Concept corrections at L3 (the plan wins).** In the arrival view (from (105, 80), looking west):
   - the road is a stony earth track 3–4 m wide (`soil_stony`), not paving;
   - the broken pyramid stays at its planned distance (about 6,500);
   - the Great Pyramid is about 21,200 away.

   In the signature view (from (82, 98), about 11,300 from the apex):
   - the pyramid has smooth-faced courses of MM6 Tomb of VARN stone (`egybigb`/`egybiga`) under the gilded capstone. No visible steps, so it does not read as climbable.
   - At most one frieze band may run round the foot, seamless along its axis, from shipped `egytrma` or kin. No new texture.
   - The trees on the left are not in the plan.
8. **Textures:** `xdpyrdor` (the green-stone wing, mirrored on the pair) and `xdvowel` (the Voweless Knights' lintel, placed once) are approved: 2 of 12.
   - `xdgiantd` is counted with DD-24 (A7).
   - Bosco's door uses shipped MM7 Stone City dwarf doors (7d24) or `t09a03a`/`t09a03b`.
   - The Northern Tower uses `hkm1dl`/`hkm1dr`.
9. **Peaceful People at the hold.** Six placed on D-47's rows 11083–11085 (faction `xeen_giants_people`). They are not in the 110 at load (Q1).

### D6 The Forbidden Zone: approved with changes

1. **No Freeda on D6.** Freeda the Mountaineer is already NPC 4527, the Master Body Building teacher on X5's high pass (`x5.yml`, `teachers_plan.yml`). Body Building's three teachers are taken.
   - Her camp at (100, 69) is dropped. A6 may leave an empty climbers' camp there as dressing (no click, no NPC).
   - MAPS D6's outdoor content loses "Freeda the Mountaineer's camp".
   - A4 makes no row.
   - Owners: A6, orchestrator.
2. **The monster band follows its named families.** MAPS D6 changes from "A 38–50, C 65" to "A 30–50, C 75".
   - Vulture Roc 30 is 10 % of the difficulty-5 birds.
   - Autobot 75 is 2 % of the difficulty-1 robots, on the Alamar approach only (about 0.4 at load).
   - It is the same rule as D5 change 3. DD-17 already holds 50–75.
   - Owner: orchestrator.
3. **DD-10C's adit is clear.** The adit lies inside E4a (the measure gives 0 to the nearest fight).
   - No spawn marker within 2,000 of DD-10C's return point outside the adit, as D-40's cleft.
   - The first fight from that point must stay under 6,000.
   - Owner: A6.
4. **The hatch is clear.** No placed lava dweller's home, plus its home radius, within 2,500 of DD-16's return point on the crust.
   - The measure gives 1,676 to the lava-dweller area, against the NOTES' "none within 2,500".
   - Measured at L3 against actors and their radii.
   - Owner: A6.
5. **POIs:** 27, capped at 28 at L4.
   - If the count goes over, merge first. Then take the click off the fork signpost.
   - The archers' burn hook goes on the strongbox spot (no new POI).
   - The median spacing of 4,050 is accepted with one NOTES line, as X7's 3,280.
   - Owner: A6.
6. **Ambrose's camp has two states.** Ambrose 5512 and the tethered griffin are shown until `m25.done`, then hidden. After that he waits at DD-14 and at D4's gate (D-42). The tent and the cold fire stay.
   - The griffin is a peaceful, placed-only, immobile, not-counted row on the MM7 griffin body, as Leafpoint (D-36) and Corak (D-47).
   - Owners: A2 row, S binding, A3 hook, A6 placement.
7. **The robots are hidden on load after `m33.done`**, by D-36's coven pattern (no refill rule). Their kill XP stays counted in Act V. Owners: A3, A6.
8. **Necropolis runs `town_feel --small`** (5 services), with exception lines as D-20. Its gate:
   - opens on item 12336;
   - otherwise refuses with A3's line;
   - is always open from inside.

   A party that arrives by mirror is inside without a pass, as D-30's "no skip".
9. **The zone sign warns.** The source's "The Forbidden Zone." stays verbatim, plus one short warning line in A3's voice (for example "Beyond: Castle Alamar. The dead keep the road."), as D-40 (4).
10. **Concept corrections at L3 (the plan wins).**
    - Castle Alamar stays at the plan's distances: about 26,500 in the arrival view, 20,700 in the signature view. Never moved nearer.
    - It is built in the Ancient kit's teal steel (`xahull` on `gn_mtl`, `xaenergy` pylons, `xafield` curtains): square towers, every window lit. Never grey Gothic stone.
    - The four energy pylons stand on the approach ramp only, not along the road.
    - The islet's genie lamp stays on its islet, not beside the pod.
    - In the signature view, the moat's glow must read as a line under the walls. If the far shore hides it, raise the camera or move it along the shore; never move the castle.
    - At L4 the castle must read at its distance (lit windows, fields), as D-36's Blackfang. If fog hides it, tune the atmosphere, not the distance.
11. **Textures:** `xnpgate` (the gatehouse crest, placed once) and `xnpbook` (the lectern book) are approved.
    - `xcrust` is not made: the crust BModel (Q4) uses a shipped cooled-rock face, the one on X7's cooled-flow island or kin.
    - The Necropolis gate uses a pair different from the Northern Tower's (`chb1dl`/`chb1dr` preferred).
    - Alamar's gate: shipped `swdoora`-family leaves first; a new pair only if none fits, counted in the 12.
12. **The pods and Castle Alamar** (whole and ruin) are BModels from the Ancient kit, built by A6, with the two states swapped by qbit. No S models, no Meshy.

**Textures, both maps:** 4 new, so the world goes from 141 to 145 of 450.

---

## ANSWERS

### D5

**Q1 The People while peaceful**
- **DECISION:** (a). Six placed at the hold on 11083 Cyclops 38 ×3, 11084 Giant 50 ×2 and 11085 Elder Giant 58 ×1, faction `xeen_giants_people`.
  - They are not in the 110 at load.
  - Their 3.9k per member counts only on the war route, as a note in A2's recount.
  - One blow here or in DD-24 turns both (D-47 Q22, fix 3).
- **WHY:** These are D-23's Graalg pattern: peaceful figures are not counted. Counting them would put D5 at 59.4k (+13.6 %), over the ±10 % guidance.
- **WHO ACTS:** A2 (rows exist from D-47; the war-route note in the recount), A6 (placement; the sketch moves from 11080–11082 to 11083–11085 once A2's rows validate), A3 (the hall-attacked hook covers D5).
- **REVERSIBLE:** yes, cheaply.

**Q2 The Quivering Forest's giants**
- **DECISION:** (a). Wild cyclopes on the ordinary rows 11080–11082 (36/50/62) at difficulty 1, round the source's C1 lair with its "Destroy?" burn device and hoard.
  - Their faction is hostile and untouched by Q-D16's relations. Killing them never sets `hall_attacked`.
  - Band per D5 change 3.
- **WHY:** The lair is the source's own. A second People camp would empty the forest of fights and add a third state to Q-D16. The forest is about 13,800 from the hold, so no fight drags the People in.
- **WHO ACTS:**
  - A2: the wild rows' faction, kept separate from `xeen_giants_people`.
  - A3: the lair's burn hook (aaze0009:1-2), rescaled.
  - A6: placement.
  - Orchestrator: the MAPS line "Giants (the highlands; peaceful if Q-D16)" becomes "wild cyclopes in the Quivering Forest; the People at Gurodel's hold (peaceful until war)".
- **REVERSIBLE:** yes (slot and faction).

**Q3 The Enchanted Boulders**
- **DECISION:** (b′). Two clusters per D5 change 1 (sign + 3–6 east; 1, 2, 7 west), each chained within 400: 24 POIs. No chests.
  - After `q-d24.solved`, each of the six other boulders, clicked, crumbles ("The boulder crumbles to sand and leaves behind …") and gives one random item at treasure level 5 from the MM6–MM8 tables, then is hidden.
  - The seventh gives the paladin's armour (12529).
- **WHY:**
  - Seven boulders spread over about 3,000 units do not merge by D-15's 400 rule, so counting them as one spot was not honest.
  - Two clusters keep a small hunt across the desert, as the source's C2/D2 split, and stay inside the 20–25 band without cutting the dwarf camp or a lamp.
  - The second cluster also fills the sparse west.
- **WHO ACTS:** A6 (clusters, hide by qbit), A3 (crumble hooks and lines), A2 (item level; no new items), S (the boulder model).
- **REVERSIBLE:** yes, until L3.

**Q4 The Parabolic Barrier**
- **DECISION:** (a). A landmark: a bowed line of Ancient frames (`gn_mtl`, `xaenergy`) with an `xafield` curtain.
  - No event, no click, not a POI.
  - It blocks walking and flying (D5 change 4).
  - A faint hum as a point sound along it.
- **WHY:** The source gives only the name. A shock device would add a POI and a rule for nothing; event-less landmarks are not POIs (D-20).
- **WHO ACTS:** A6, AU (hum).
- **REVERSIBLE:** yes (an event can be added later).

**Q5 A fourth +2 Endurance**
- **DECISION:** (b). The Last Water gives **+2 Accuracy**, permanent, once per character. A short line of A3's, for example "The water is cold and very clear. Your eyes sharpen."
  - The Fountain of Energy Resistance (+5 Air, permanent) stays.
- **WHY:**
  - Endurance already has X6's oasis, X3's spring, DD-18's brew and D-25's Troll Juice.
  - Permanent Accuracy appears nowhere in the decisions so far.
  - QUESTS §4.3 still wants one +2 stat fountain per map.
- **WHO ACTS:** A3 (event, text), A2 (ledger, Act V). If the ledger shows Accuracy is not the least-served permanent stat, A2 swaps in the least-served one before L4 and says so in STATUS.
- **REVERSIBLE:** yes (one value).

**Q6 The Great Pyramid's size**
- **DECISION:** (a). 12 × 12 cells (about 6,100 at the foot) and about 3,600 high, standing alone in the dunes. The faces are too steep to walk. The door at the north face's foot is to human scale (two leaves).
- **WHY:** It is the map's name and story (M28–M30) and must read from both arrivals, about 21,000 away. A 2,400-high pyramid would sink into the dunes at that distance. DD-15's inside is independent.
- **WHO ACTS:** A6.
- **REVERSIBLE:** medium after L3.

**Q7 The broken travel pyramid**
- **DECISION:** (a). It stays in the east valley by the road (95, 72), with the capstone at its foot (D5 change 2).
- **WHY:** The D4 arrival sees it, and the obelisk hoard can be reached without the cliffs. Moving source places to where the design needs them is the house practice (D-31, D-40).
- **WHO ACTS:** A6, A3 (the line on the capstone spot).
- **REVERSIBLE:** yes.

**Q8 The rescaled devices**
- **DECISION:** Accepted.
  - Shrine of Great Power: +15 to all stats until rest, once a day.
  - Fountain of Might: +20 Might until rest, once a day.
  - Fountain of Energy Resistance: +5 Air resistance, permanent, once per character.
  - If two temporary bonuses meet on one stat, the engine's existing rule applies; no new rule.
- **WHY:** D1's prayer shrine gives +10 to all stats in Act III, so +15 fits Act V. Temporary bonuses last until rest and permanent ones are small (D-4, the brief's constraint).
- **WHO ACTS:** A3 (hooks and lines aaze0009:3-5, aaze0013:9-11, aaze0010).
- **REVERSIBLE:** yes.

### D6

**Q1 Griffin Pass on the south**
- **DECISION:** (a). Griffin Pass at the top of D1's mountain road (64, 96), with Ambrose's camp there (D6 change 6).
- **WHY:** QUESTS M25 already says "Griffin Pass (D6 south edge)". The arrival concept and the D1 road depend on it. An Act IV party reaches Ambrose about 5,100 from the D1 arrival, past one bird group.
- **WHO ACTS:** A6, A4 (confirm 5512 at the pass), A3 (`m25.flight` and the hide on `m25.done`).
- **REVERSIBLE:** yes.

**Q2 The lava dwellers**
- **DECISION:** (a). 14 placed fire elementals on the existing rows: Lesser Elemental 11620 (55) ×11 and Elemental 11621 (62) ×3.
  - Each has a home radius over the lake and its shores.
  - None within 2,500 of the hatch (D6 change 4).
  - No new family.
- **WHY:** Both rows exist, are fire-immune flyers and sit inside D6's band. MONSTERS_AND_ITEMS already lists Elementals for D6, and A7 chose the same for DD-16. Lava Golems (55) are X7's island guards.
- **WHO ACTS:** A2 (no new row; listed in the recount), A6.
- **REVERSIBLE:** yes, cheaply.

**Q3 The archers' camp**
- **DECISION:** (a). Two new placed rows, Barbarian Archer 44 (11104) ×9 and Archer Chief 50 (11105) ×3, with arrows.
  - They are shown on the archer body `xeen_arc1` in barbarian colours, not on the sword-armed `mm6_bar1`.
  - Their own hostile faction, untouched by Q-D12's Sardaj peace.
  - The burn hook sits on the strongbox spot.
- **WHY:** In-band rows for a placed camp follow D-25. A bow attack needs a body that holds a bow. QUESTS §4.3 lists barbarian camps among the camps to burn.
- **WHO ACTS:** A2 (rows, faction), S (two colour skins on `xeen_arc1`), A3 (burn hook), A6.
- **REVERSIBLE:** yes.

**Q4 The cooled crust**
- **DECISION:** (a). A crust BModel over the lava round the hatch, shown on `lava_cooled` 111564 (`set:pod_lava`), in a shipped cooled-rock texture.
  - A1 only confirms two things: a party standing on a BModel floor over a lava tile takes no lava damage, and a hidden BModel has no collision.
  - If the first fails, A1 makes a small general fix (lava burns only when the party's floor is the lava terrain).
- **WHY:** It uses existing state words (D-23's forts, D-31). A tile swap by qbit would be a new engine feature for one spot.
- **WHO ACTS:** A6, A1 (confirmation).
- **REVERSIBLE:** yes.

**Q5 The ruin's stair**
- **DECISION:** Gatehouse. FD-01's stair (`m39.depths_door`) is in the broken gatehouse's floor, on DD-17's gate spot, shown only in the ruin state and sealed until FD-01 exists. One POI.
- **WHY:** One spot for both states, and the party knows where Alamar's way in was. A stair in the court would be a second POI behind rubble.
- **WHO ACTS:** A6, A8 (FD-01's arrival, phase 6).
- **REVERSIBLE:** yes.

**Q6 The D5 corner**
- **DECISION:** (a). The shared file `edge_d5_d6.json` changes at y 106–109 to 2,636 / 2,440 / 2,260 / 2,176, D1's installed (109, 19). It stays as it is from y 105 north.
  - Both maps carry it: D5's x 19 column blends the last four cells too.
  - D5's south row then meets D2's (19, 19) at 2,496, within 320, as now.
  - One NOTES line in both maps: the installed D1 and D2 disagree at the four-map point (2,176 against 2,496). There is no crossing there; it is left as is.
- **WHY:** D1 is installed and has a crossing on this edge, so it wins. The file is A6's lead and "both maps move together".
- **WHO ACTS:** A6 (file, D5 and D6).
- **REVERSIBLE:** yes, until L3.

**Q7 Lucio on D6**
- **DECISION:** None on D6. MAPS D6's arrivals become "D5 (east), D1 (south, a long mountain road); mirror".
- **WHY:** D-5.3 puts the boats at Castleview, Sandcaster and Lakeside only.
- **WHO ACTS:** orchestrator.
- **REVERSIBLE:** yes.

**Q8 42 spawn markers**
- **DECISION:** Keep 42 (84 hostiles) plus 26 placed: 110. One NOTES exception line against MAPS's 45–70.
- **WHY:** "Few and strong": the two placed camps do the markers' work. Three more markers would push the map over 110 or thin its groups. Under-floor counts are kept with a NOTES line, as in D-47.
- **WHO ACTS:** A6.
- **REVERSIBLE:** yes, cheaply.

---

## ROWS AND NUMBERS

| | D5 Desert of Doom | D6 The Forbidden Zone |
| --- | --- | --- |
| Hostiles at load | 110: 47 markers (15 lizards ×2.5, 21 birds ×2, 11 cyclopes ×2.5) plus 3 placed griffins | 110: 42 markers (84) plus 26 placed (14 elementals, 12 archers) |
| Kill XP per member | 55.6k of 52.3k (+6.2 %); the People +3.9k on the war route only | 73.4k of 71.1k (+3.2 %) |
| POIs | 24 (desert band 20–25; cap 25 at L4) | 27 (trap band 22–28; cap 28 at L4) |
| Chests / entrances | 6 / 5 | 6 / 6, plus Necropolis's gate |
| Permanent devices | +2 Accuracy (the Last Water), +5 Air resistance | the Books of the Dead (+3,000 XP and +8 years per book, three books, once per character each) |

**MAPS changes (orchestrator):**
- D5 band "A 30–42, C 62" (§0 row: 30–62).
- D5's giants line per Q2.
- D6 band "A 30–50, C 75" (§0 row: 30–75).
- D6's arrivals lose Lucio.
- D6's outdoor content loses Freeda's camp.

**Act V recount:** D5 +3.3k and D6 +2.3k over the table, both inside ±10 %.

---

## RELAYS

- **A1:**
  - Confirm that a party on a BModel floor over lava takes no lava damage and that a hidden BModel has no collision. Only if the first fails, the small general fix (Q4).
  - The ash word (D-40) also serves D6's `atmosphere.yml`.
  - Edge and travel rows when D5 and D6 are installed.
- **A2:**
  - Rows 9112 and 9113 with the planned slots.
  - D5's six People on 11083–11085 (not counted); the wild giants 11080–11082 in a hostile faction outside Q-D16's relations.
  - New rows 11104 (Barbarian Archer 44) and 11105 (Archer Chief 50), arrow attack, own hostile faction outside Q-D12.
  - Lava dwellers on the existing 11620/11621.
  - A peaceful, placed-only, immobile "Tethered Griffin" row.
  - The boulders' six treasures as random treasure-level-5 items.
  - The ledger: D5's +2 Accuracy (or the least-served stat, Q5), +5 Air resistance, the Books of the Dead.
  - The Act V recount: D5 55.6k, D6 73.4k.
- **A3:**
  - D5: Q-D27 hooks for its two lamps; the Shrine of Great Power and three fountains as rescaled (Q8), including the Last Water's Accuracy line; the lair's burn hook; the munchies line; the six crumble hooks after `q-d24.solved`; "The pyramid portal has been destroyed." on the capstone spot; check the qbit numbers in D5's `project.yml`.
  - D6: the Necropolis gate hook (12336) and its refusal; the skull's story; the Books' text; the zone sign plus its warning line; Sheltem's sealed-hatch line; three genie-lamp hooks; robots and Ambrose with his griffin hidden on load after `m33.done` and `m25.done`; the archers' burn hook.
- **A4:** No Freeda row (she is 4527 on X5). Confirm Ambrose 5512 at Griffin Pass until `m25.done`. Necropolis houses 4751–4762 as in `d6.yml`.
- **A5:** nothing (the lava-fall preset is shared with X7, as D-40).
- **A6:**
  - Apply both maps' change lists.
  - The edge file at y 106–109 and D5's matching column.
  - D5's rim rule; the two boulder clusters; the capstone merge.
  - D6's clear zones round the adit and the hatch.
  - NOTES exception lines: spacing, 42 markers, the four-map corner, `town_feel`.
  - Register `xdpyrdor`, `xdvowel`, `xnpgate`, `xnpbook`.
  - Then L2–L4.
- **A7:**
  - DD-24's `entrance:d5_hold`, with the return at D5 (86, 43) facing south, about 1,500 from Gurodel.
  - DD-16's `entrance:d6_hatch` (settled), with its way out on the crust about 384 before the hatch, facing south-east.
- **A8:**
  - Inside arrivals for DD-15 (the green door, facing south), DD-08 and DD-25.
  - DD-17's arrival, and its refusal returning to the gate.
  - DD-21's stair foot.
  - DD-10C's `D6_ARRIVAL` (A6 gives the point with no marker within 2,000).
  - DD-18's `exit:d5_grate` at D5 (101, 102), facing north.
  - FD-01's stair arrival in phase 6.
- **S:**
  - One Enchanted Boulder model (a great rock with a weathered face; static; Meshy prop ≤ 30 credits or hand-built).
  - One genie lamp model for all Q-D27 lamps.
  - The tethered griffin's binding on MM7's griffin.
  - Two barbarian colour skins on `xeen_arc1`.
  - The People and the wild giants on the MM8 cyclops body only (D-44: no MM9), the People with their own recolour.
  - The lava-fall preset reused.
  - No models for the pods or Alamar (they are BModels).
- **AU:**
  - D5: desert wind, the aspens' tremble, the Barrier's hum as point sounds along the line (panning, D-48).
  - D6: lava bubbling, falls and ash wind, a Necropolis bed (bed beds `pan: false`).
  - Shipped sounds first.

---

## SUMMARY ROW

D5 and D6 L1 both approved with changes; A6's default on 13 of 16 questions. D5: the People (6 at the hold) uncounted; wild cyclopes in the Quivering Forest; boulders in two 400-chained clusters (24 POIs), six crumbling to treasure-level-5 items after the answer; the Barrier a landmark that blocks walking and flying, with a rim rule; the Last Water +2 Accuracy; pyramid 12×12 and 3,600 high; band 30–62. D6: Griffin Pass south; fire elementals 11620/11621 as lava dwellers; archer rows 11104/11105 on `xeen_arc1`; a crust BModel by qbit; FD-01 in the gatehouse; the D5 corner follows D1 (file y 106–109 changed); no Lucio, no Freeda (she is X5's); 42 markers kept; band 30–75. 4 new textures. Detail: `briefs/d5/L1/D49_DECISION.md`.
