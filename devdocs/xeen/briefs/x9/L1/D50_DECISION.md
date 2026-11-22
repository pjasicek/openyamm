# X9 and XD-17 L1 mock-ups, D3's signature camera: decisions (D-50)

> Orchestrator note (2026-11-21): change 4's 4,000 dragon-distance rule is replaced by D-54 (`devdocs/xeen/reviews/D54_DECISION.md`):
> the landing stays, the lake dragons move and are leashed, leash circles ≥ 5,888 from fall landings and Darzog's door.

Decider D-50, 2026-11-21. Where this file differs from the L1 plans and the two NOTES.md files, this file wins. Geometry (L2) may start on both maps once A5 has applied the changes below and the blockers in the NOTES are cleared: A2's row 9107 and 9120, and A7's gate footprint.

---

## APPROVAL

### X9 Clouds of Xeen: approved with changes

1. **The unseen way stays faint but can be followed (Q1).** It is 768 wide, not 512, still on the sign's line due north.
   - Its wisp top is hard to see from the signature distance but readable underfoot, within about 1,000.
   - A cloud-stone lip marks each end: one at the sign's foot, one under "Now entering Xeendom".
   - A 512 path walked blind for 4,600 needs aim to within 3°, and every miss costs the climb back through XD-12. The sign gives the answer; the walk should not then punish slightly crooked keyboard steering.
   - Owners: A5 (geometry), A6 (wisp texture).
2. **Slick's plaza is smaller (Q7).** It shrinks from 7,680 × 6,144 to about 6,144 × 4,608 round the four booths.
   - The booths stay at least 1,024 apart.
   - The shooting line keeps its 1,536, with the bullseye on the plaza's west rim.
   - The Xeen road still runs up its east side.
   - Nothing else shrinks. The spans stay inside D-6.2's 3,500–4,000; the aviary stair stays at 4,130.
   - Owner: A5.
3. **The gate uses the `exit` preset (D-24).**
   - Its condition is `m34.gate`: the fail text when there is no doll, and with the doll the game's own leave window.
   - "Enter Castle Xeen?" (aaze0027:40) goes into the ledger as the window's meaning. No second map question.
   - Owners: A5, A3.
4. **The falls are tested (D-6.4) and the landing is named (D-37).**
   - On X2, the landing at (-14592, 2816) is named `entrance:x9_fall`, with a keep-clear at X2's next install.
   - At L4, measure the landing against each lake dragon's placement plus its home radius: it must be at least 4,000 away. The nearest placement, [31, 50.5], is about 4,700 away. If the check fails, move the point along the island toward the tower door, never into the lake.
   - The playtest falls once from each region (the stair clouds, a chain, Xeendom) and checks that each lands at the point and the party lives.
   - Owner: A5.
5. **The castle shell is closed on every side, roof included.** XD-19's open aviary court belongs to XD-19's own map. On X9 nobody can see over the shell (no Fly).
6. **Concept corrections at L3 (the plan wins).**
   - The castle stays at the plan's distance (about 23,000 from the brink). It is never moved nearer or scaled up.
   - The booths are spread over the plaza, not in a row.
   - No gryphon statues at the gate.
   - The painted banner is allowed only as shipped flag dressing (`7tws1f`).
7. **The Dragon Clouds are built now, empty (Q8).**
   - No click, no chest, no light, no POI, no monster.
   - The dragon-head rock is studio masses until Q-F1.
   - `entrance:fd04_roof` is named and sealed.
8. **Textures.** X9 is classed as Dungeon L: cap 70, at most 14 new.
   - Shipped MM6–MM8 tent or awning canvas comes first. If none fits, a new striped canvas.
   - New: the straw bullseye and the wisp top.
   - So 2–3 new textures; the world goes from about 145 to at most 148 of 450.
9. **The castle-gone stage, the return point and the aviary sign stay as drawn**, following D-47 Q14.

### XD-17 Shangri-La: approved with changes

1. **Lacey and Stumpy are placed peaceful actors on shipped bodies (Q2, changed from A5's (c)).** Neither is counted. Both use A1's NPC-on-placed-monster word (already asked for by D-47).
   - Lacey: MM8's unicorn (`mm8_m544`, descriptor Unicorn A). She wanders within 512 of her spot by the well.
   - Stumpy: the MM7 Treant, immobile (`move: stand`), in the orchard, as Leafpoint (D-36 (5)).
   - No new models, no Meshy.
2. **The well pays a fixed amount of experience (Q1, changed).**
   - Once per character (a player bit): 20,000 experience and the award "Found Shangri-La".
   - It keeps "Congratulations, You found Shangri-La!" from aaze0049:27. A3's line replaces "+1 Level (permanent)". After that it says :4.
   - It is not "experience to the next level". That is a permanent +1 level under another name, and it varies with the drinker, so the ledger cannot audit it.
3. **The pyramid's arrival is renamed (D-37).** `entrance:pyramid` becomes `entrance:d6_pyramid`.
4. **The ways out use the `exit` preset (D-24).**
   - "Leave Shangri-La?" (aaze0049:32) is the window's meaning in the ledger. The map asks no question of its own.
   - The first exit at the rockfall still calls `xd17.cleft_opened` before it moves the party.
5. **Eight doors are renamed** to `door:maurice`, `door:alexander`, `door:pilar`, `door:benedict`, `door:elona`, `door:murray`, `door:sally` and `door:martok`. This is A4's file.
6. **POIs are 18 by D-20.** The falls are a landmark with no event, so they are not a POI. If the falls get a click, they count and the total is 19.
7. **Concept corrections at L3 (the plan wins).**
   - The valley keeps its depth: about 8,800 to the pyramid and 7,600 to the tower from the arrival.
   - The anvil stands against the forge wall between the two doors, not on the square.
   - Pilar's pavilion is a small house with a door, not an open gazebo.
8. **Textures.** XD-17 is also Dungeon L: cap 70, at most 14 new. None is named; the estimate is 40–55 distinct.

### D3 signature camera: keep north-north-west

The rim glow gets its own named view instead. See the answer at the end of ANSWERS.

---

## ANSWERS

### X9

**Q1 The unseen way**
- **DECISION:** (a) with change 1: a faint wisp path 768 wide, readable underfoot, with a cloud-stone lip at each end. "Xeen--9N." stays word for word. Both chains stay as the visible way round.
- **WHY:** The sign states the answer, so no outside knowledge is needed (the riddle rule). The wider path and the close-up visibility keep the "step out on faith" moment without making a 3° steering error cost a long climb back.
- **WHO ACTS:** A5 (path, lips), A6 (wisp texture).
- **REVERSIBLE:** yes (a texture and a width).

**Q2 Where falls land on X2**
- **DECISION:** (a). One point on Darzog's island at (-14592, 2816), ground 768, facing east, with falling damage, named `entrance:x9_fall`, with change 4's dragon check and tests.
- **WHY:** The way back up (the tower door, the disc, the cloud stair) is ten steps away. A water landing would strand the party behind Medin's boat or Water Walk. At level 46 the damage is small. D-6.4's distance rule is kept by measuring against the dragons.
- **WHO ACTS:** A5 (both maps), A3 (`Xeen.skyFall` with the point).
- **REVERSIBLE:** yes (one point).

**Q3 "Xeen's Aviary"**
- **DECISION:** (a). At the head of the aviary stair, by the rookery.
- **WHY:** This is the source's (26,26), and D-47 already places it on X9. XD-19 may sign its own court inside.
- **WHO ACTS:** A5, A3 (sign text).
- **REVERSIBLE:** yes.

**Q4 The monster mix**
- **DECISION:** (a). Rocs 38 ×38, Griffins 48 ×6 (in the aviary), Cloud Golems 50 ×6. That is 26.0k per member (−0.4 %), all placed, in 19 groups.
- **WHY:** The two kinds are the source's, plus the great birds' own C tier. The total is on budget. The 55 elementals belong to XD-19's generators (D-47 Q10) and would blur the castle's reveal.
- **WHO ACTS:** A5 (placement), A2 (recount).
- **REVERSIBLE:** yes, until placement.

**Q5 Offering statues and nests**
- **DECISION:** (a). Six offering statues (Crusaders get one treasure-level-5 item, once per party; anyone else is struck, as on X8) and five roc nests.
  - Each nest asks "Roc Nest. Destroy?" (aaze0027:0; Yes/No is a real choice).
  - Each pays **2,000 experience per member**, once: X8's 500 scaled by L(L+10) from level 19 to 47 is about 2,400, rounded down.
  - Five nests is one over QUESTS 4.3's 2–4, accepted as the source's rookery (it has seven).
- **WHY:** This keeps the source's hub of nests and offerings at MM6–MM8 size: 10k per member in Act V's quest budget, against the source's 50,000 per nest. 29 POIs is inside the 20–50 band.
- **WHO ACTS:** A3 (hooks, 2,000 each), A2 (Act V quest ledger +10k), A5.
- **REVERSIBLE:** yes (hook values).

**Q6 Slick's figure**
- **DECISION:** (a), shown as (b) until the binding lands. A peaceful, placed-only, immobile, uncounted, NoArena row "Slick the Gamemaster" stands behind the prize stand. The booths and the stand stay the clicks. No NPC id.
- **WHY:** This is the pattern of Corak, Leafpoint and the tethered griffin. A talking Slick would duplicate m34's booth texts.
- **WHO ACTS:** A2 (row), S (a recolour of a shipped merchant body), A5 (placement).
- **REVERSIBLE:** yes.

**Q7 Size and fill**
- **DECISION:** (a), with change 2 (the plaza at about 6,144 × 4,608). No extra rocs. The quiet zones stay as designed.
- **WHY:** At 70 % of an outdoor map's side, X9 expects about 1.36 times X8's 124 M, about 170 M. The plaza was the largest empty surface that carries nothing. Shrinking the islands, as option (b) does, would break D-6.2's span limits.
- **WHO ACTS:** A5.
- **REVERSIBLE:** yes, until L2.

**Q8 The Dragon Clouds**
- **DECISION:** (a), with change 7: built now, empty and sealed, `entrance:fd04_roof` named.
- **WHY:** Building now avoids rebuilding X9 in phase 6, and the island is unreachable (3,892 away and 1,024 up, with no Fly). Q-F1 fills it later.
- **WHO ACTS:** A5. S and A3 act when Q-F1 has a brief.
- **REVERSIBLE:** yes.

### XD-17

**Q1 The well's +1 level**
- **DECISION:** Changed (a): a fixed 20,000 experience once per character, plus the award "Found Shangri-La". The town still has no training hall.
- **WHY:** QUESTS forbids permanent levels, and "experience to the next level" is one in disguise. A fixed sum (about 0.4 of a level at 48, under Act V's 0.75 cap) can be audited, and D-42's Soul Waters already set experience as the rescale.
- **WHO ACTS:** A3 (`xd17.well`, player bit, award, lines), A2 (Act V quest ledger; trim to 15,000 if Act V's quest experience goes over its 15 % rule).
- **REVERSIBLE:** yes (one value).

**Q2 Stumpy and Lacey**
- **DECISION:** (a) on shipped bodies (change 1): Lacey on MM8's unicorn, wandering within 512 of the well; Stumpy on the MM7 Treant, immobile. Both are peaceful, placed-only and uncounted.
- **WHY:** Both bodies are installed (MM8 and MM7 are dependencies under D-44). Leafpoint (D-36) is the same talking-tree case. "A tree does not walk" is handled by `stand`, without a second mechanism.
- **WHO ACTS:** A2 (two rows), S (bindings, an optional skin), A1 (NPC on a placed monster, already asked by D-47), A4 (confirm places), A5.
- **REVERSIBLE:** yes.

**Q3 Firestone's summit**
- **DECISION:** (a). A backdrop cone beyond the north-east crest, 5,600 above the floor, with `view_distance_scale` 1.25. Smoke only once A6 or S have an effect for it.
- **WHY:** The summit places the valley in the world and makes the green read as hidden.
- **WHO ACTS:** A5, A1 (confirm the cost of 1.25), A6/S (smoke, optional).
- **REVERSIBLE:** yes.

**Q4 The signature view**
- **DECISION:** (a). From the library steps, looking east-north-east.
- **WHY:** It shows the court, the well with Lacey, the pool, the falls, the dome and the summit in one frame. Option (b) puts the summit behind the camera.
- **WHO ACTS:** A5.
- **REVERSIBLE:** yes.

**Q5 The hidden crystal**
- **DECISION:** (a). In the cliff by the cave mouth, at eye height, with A3's short line in Benedict's voice. It is a shipped crystal decoration, or a studio mass with a shipped crystal face. No new texture.
- **WHY:** It pays off Benedict's joke from the first step and costs one click.
- **WHO ACTS:** A5, A3 (`xd17.crystal`).
- **REVERSIBLE:** yes.

**Q6 The sky inside**
- **DECISION:** (a). The fair preset, no theme, no ash, no weather.
- **WHY:** The valley that clears is the point. This needs no engine question about sky themes on open-air BLVs.
- **WHO ACTS:** A5.
- **REVERSIBLE:** yes (one line in `atmosphere.yml`).

**Q7 The water**
- **DECISION:** (a). The pool, a white fall from the east cliff (S's `xeen_waterfall`, a water preset of the sand-fall build) and a stream to a sinkhole. If S cannot make the fall, (b).
- **WHY:** The fall carries the signature, and the build already exists.
- **WHO ACTS:** S, A5, AU.
- **REVERSIBLE:** yes.

**Q8 The back passage**
- **DECISION:** (a). A slot open to the sky, 384 wide and 2,087 long. The first exit opens the rockfall (D-40 (3)), and it is two-way after.
- **WHY:** It is cheaper, it stays one sky room, and it matches X7's cleft.
- **WHO ACTS:** A5, A3 (`xd17.cleft_opened`).
- **REVERSIBLE:** yes.

**Q9 The pyramid's far end**
- **DECISION:** (a). On D6, outside Castle Alamar's gate (Lua key `alamar_gate`).
  - D6's approved plan has only the broken pyramid, so **A6 adds a working travel pyramid** on Alamar's approach, outside the moat, with its click (`Xeen.travelPyramid("alamar_gate")`) and an arrival named `entrance:xd17_pyramid`.
  - No spawn marker within 2,000 of that arrival.
  - It counts inside D-49's D6 cap of 28 POIs, with D-49's merge order if needed.
  - XD-17's arrival is `entrance:d6_pyramid`.
- **WHY:** Landing inside DD-17 would skip Castle Alamar's way in. The Lua and ROADMAP 5.6 already name the gate, and an outdoor landing matches the first pair.
- **WHO ACTS:** A6 (D6), A3 (both `PyramidArrivals` rows), A5 (the neighbour row), orchestrator (WORLD_DESIGN 3.3 text).
- **REVERSIBLE:** yes, until D6's L3.

### D3 signature camera

- **DECISION:** Keep the signature facing north-north-west (yaw 2.0344 from (22272, -4096, 1300)).
  - Add a second named view, `rim_glow`, to `gen_tour.py`: the rim looking east at night (`sheet_below15.jpg` 04, `sheet_rim_east.jpg` 02). Frame it so the rim's grass or the falls' lip fills the lower-left foreground, not the bare slab and rock.
  - D-28's "glow as a band above the east rim" and D-36's re-shoot apply to that view.
- **WHY:** The north-north-west frame holds the map's identity: falls, meadows and the Eastern Tower. In the north-east frame (`sheet_rim_east.jpg` 03–04) two-thirds is empty water and sky, the falls are a sliver at the left edge, and by day the glow does not read at all. The glow is a night feature and is shown best on its own.
- **WHO ACTS:** A5 (tour, NOTES line).
- **REVERSIBLE:** yes (one yaw).

---

## ROWS AND NUMBERS

| Map | Monsters | Kill XP per member | POIs | Chests | Other |
| --- | --- | --- | --- | --- | --- |
| X9 | 50 placed, 19 groups: Roc 11561 (38) ×38, Griffin 11562 (48) ×6, Cloud Golem 11592 (50) ×6; Slick not counted | 26.0k (target 26.1k, −0.4 %) | 29: 4 signs, 4 rhymes, 5 nests, 6 offerings, 4 booths, stand, gate, 4 chests | 4 at treasure level 5 | Quest XP +10k per member (nests); textures 2–3 new |
| XD-17 | 0 hostile; Lacey and Stumpy peaceful, not counted | 0 | 18 (well, pyramid, crystal, 15 doors) | 0 | Quest XP +20k per member (well); textures 0 new named |
| D6 | unchanged (D-49) | unchanged | +1 (the pyramid), at most 28 | unchanged | arrival `entrance:xd17_pyramid` |

**MAPS changes (orchestrator):**
- §0 X9 row: kill XP becomes "26.1k (L1 26.0k, −0.4 %, D-50)".
- §3 X9 row: monsters become "Rocs 38, Griffins 48, Cloud Golems 50; 50 placed".
- XD-17 row: notes become "Open-air BLV valley: a hidden town (5 services, 10 residences, no monsters); the well 20,000 experience once per character; the pyramid to D6's Alamar gate after M30 (D-50)".
- D6 outdoor content: add "a travel pyramid outside Alamar's gate (to Shangri-La after M30, D-50)".

**WORLD_DESIGN (orchestrator):**
- §3.3: "the one in Castle Alamar's dungeon (D6)" becomes "the one outside Castle Alamar's gate on D6".
- §5.1: "+1 level well rescaled" becomes "the well (20,000 experience once per character and an award)".

---

## RELAYS

- **A1:**
  - Confirm that `view_distance_scale` 1.25 is affordable on XD-17.
  - Confirm that house doors in an open-air BLV enter by `evt.EnterHouse` from a door face (XD-07 and XD-13 already do).
  - The NPC-on-placed-monster word (D-47) now also covers Lacey and Stumpy.
  - The leave after `evt.PlayCinematic` (D-47 Q14) still gates X9's direct return.
  - `texture_budget.py` classes X9 and XD-17 as Dungeon L (cap 70).
  - No new words.
- **A2:**
  - Row 9107 as in X9's project.yml (slots Roc tier 1 [2, 3] weight 80, Golem tier 2 [1, 3] weight 20) and its bolster_maps row.
  - Row 9120 (no slots, encounter 0, music 51).
  - Placed-only, peaceful, uncounted rows: "Slick the Gamemaster" (NoArena), Lacey (MM8 Unicorn A), Stumpy (MM7 Treant, stand).
  - Act V recount: X9 26.0k.
  - Quest ledger: X9 nests 5 × 2,000; XD-17 well 20,000 per character (trim to 15,000 if Act V's quest experience goes over its 15 % rule).
- **A3:**
  - m34's `where` texts matched to the drawn booths; the gate as `exit` preset plus `m34.gate` (aaze0027:40 in the ledger).
  - Hooks for five nests (aaze0027:0, Yes/No, 2,000 each, once) and six offering statues (as X8).
  - The four sign texts, aaze0027:44, and first-arrival lines for X9 and XD-17.
  - `Xeen.skyFall` to X2's `entrance:x9_fall` (-14592, 2816, 768, east).
  - XD-17 hooks: `xd17.well` (20,000 XP, award "Found Shangri-La", player bit, :27's first half verbatim then :4), `xd17.crystal`, the pyramid hook reading `m30.done`, `PyramidArrivals.shangrila` (0, 3200, 256, 1536, `xeen_xd17.blv`) and `alamar_gate` (A6's D6 point).
  - `q-c26.way`'s `where` names `entrance:xd16_way`; `xd17.cleft_opened`.
  - ORIGINAL_LINES rows for aaze0027:0, :6–10, :33, :40, :44 and aaze0049:4, :25, :27 (rescaled), :32 (window meaning).
  - The shared Linguist gate (with X8).
- **A4:**
  - In `towns/xd17.yml`, rename the eight `door:houses#n` to `door:maurice`, `door:alexander`, `door:pilar`, `door:benedict`, `door:elona`, `door:murray`, `door:sally`, `door:martok`.
  - Confirm Lacey by the well at (448, -384) and Stumpy in the orchard at (4608, -2304), now on shipped bodies.
  - No NPC id for Slick.
- **A5:**
  - X9: apply changes 1–9 and the Q answers, then start L2 once rows 9107 and A7's footprint land.
  - X2 at its next install: `entrance:x9_fall` and its keep-clear, plus the dragon distance check.
  - XD-17: apply changes 1–8 and start L2 after row 9120.
  - D3: keep the signature and add the `rim_glow` tour view, with a NOTES line.
- **A6:**
  - X9 textures: shipped canvas first, then the bullseye and the wisp top, registered in `source/textures.yml`; the castle shell in XD-19's exterior kit (closed roof); `xccloud`, `xccloudsd`, `7tws1f`.
  - XD-17: ground layers (grass, flagstone, packed earth, X7's basalt slope), pale marble, gilded dome; optional summit smoke.
  - D6: a working travel pyramid outside Alamar's gate with `entrance:xd17_pyramid`, no marker within 2,000 of it, inside the 28-POI cap.
- **A7:**
  - XD-16: the cool passage's end uses the `exit` preset to XD-17's `entrance:xd16_way`, and names `entrance:xd17_way` about 256 inside the far end, facing back down.
  - XD-19: send the gate footprint (width, height, `gnecdr1l`/`r` both faces) and confirm the shell of 7,168 × 6,656 with walls of 2,688; the shell's roof stays closed on X9.
  - XD-19's exit preset and the scepter's leave go to X9's `entrance:xd19_gate` (0, 11264, 768, facing 1536); X9's gate leads to `entrance:x9_gate`.
- **A8:** Once X9 is installed, point XD-12's `exit:clouds_of_xeen` at X9's `entrance:xd12_roof` (0, -17920, 320, facing 512).
- **S:**
  - Slick: a recolour of a shipped merchant body.
  - Lacey: MM8 unicorn binding, a white skin if needed.
  - Stumpy: MM7 Treant binding, a fruit-tree skin optional.
  - `xeen_waterfall` (water preset, about 1,700 high).
  - Optional: a high-striker pole, a doll shelf, ground models for dolls 12367–12371 if missing.
  - The dragon-head rock with Q-F1.
  - No Meshy.
- **AU:**
  - X9: wind bed (`pan: false`, D-48), roc cries, the high-striker's DING, a fairground loop at the plaza.
  - XD-17: the fall and the stream (point sounds), the forge hammer, tavern murmur, day birds; music 51.
- **Orchestrator:**
  - Add `xeen_x9.blv` and `xeen_xd17.blv` to `world.yml` `openAirMaps`.
  - The MAPS and WORLD_DESIGN edits above.

---

## SUMMARY ROW

| D-50 | 2026-11-21 | X9 and XD-17 L1 mock-ups; D3's signature camera | Both approved with changes; A5's default on 14 of 17. X9: the unseen way 768 wide, faint but readable underfoot, lipped at both ends; the plaza trimmed to ~6,144 × 4,608; 50 monsters at 26.0k; five nests at 2,000 each; Slick a placed figure; the gate an `exit` preset with `m34.gate`; falls to X2's `entrance:x9_fall`, tested. XD-17: the well 20,000 XP once per character with an award; Lacey and Stumpy peaceful actors on MM8's unicorn and MM7's treant; the pyramid to a new D6 pyramid outside Alamar's gate; `entrance:d6_pyramid`; doors renamed. D3: the signature stays north-north-west; a `rim_glow` night view added | A5, A2, A3, A4, A6, A7, A8, S, AU, A1, orchestrator |
