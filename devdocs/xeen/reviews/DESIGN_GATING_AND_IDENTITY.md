# Xeen: dungeon gating (F17) and dungeon identity (F12)

Design session, 2026-11-21 (~23:50, fourth orchestrator). Read-only on game files; this file is the only output.
Inputs: [USER_FEEDBACK_20261121.md](USER_FEEDBACK_20261121.md) (F12, F17, the user's rule "fix it structurally"),
WORLD_DESIGN, QUESTS, MAPS, DECISIONS (U-1 to U-5, D-44, D-68, D-72, D-81), ORIGINAL_LINES, `research/`, every
`assets_dev/worlds/xeen/source/quests/*.yml` and `source/npcs/*.yml` hook, every
`assets_dev/worlds/xeen/events/maps/*.lua` event that moves the party into a dungeon, the exported MM6–MM8 map Lua,
`level_generation/xeen_art/kits/dungeon_families.yml`, each dungeon's `briefs/<key>/L1/plan.yml` and `L4/NOTES.md`, and
the review pictures under `output/studio_cal/<key>/`. Four read-only reviewers looked at the pictures of the 66 BLVs
(27 XD, 30 DD with the six pockets, 4 FD, 5 P); I checked the worst ones myself (XD-18, XD-13, DD-09).

## SUMMARY: the decisions that matter

1. **One rule for every Xeen dungeon:** the party can walk in and clear every dungeon's monsters and loot without a
   story item, a quest bit or a conversation. A story item or bit may only guard the story beat itself (a vault with
   the quest item, the boss's audience, the next act's door), or the gate becomes a key found in plain sight nearby
   that the game points to in its refusal line. Today **32 of the 66 BLVs** sit behind such a condition. MM6–MM8 gate
   about one map change in ten (counted in the exported Lua: MM6 4 of 43 transitions into a BLV, MM7 10 of 104, MM8
   12 of 62). Most of those keys are found as loot in another dungeon, such as MM6's Goblinwatch key and Cloak of Baa.
2. **Open 16 dungeons outright or move their lock inward.** XD-04, XD-06, XD-08, XD-09, XD-15, DD-02, DD-06, DD-07,
   DD-08 and DD-09 lose their outer lock. The Sandcaster pass goes, which opens DD-18 and DD-19. XD-07's cellar opens
   without Artemus's key. Four locks move inside to the beat they guard:
   - XD-11: the Enchanted Key opens the study with the Skeleton Key.
   - XD-18: the dragon tax opens only the Dragon King's door and the Great Wyrm promotion.
   - DD-12: Megan's key opens the Songbird's cage.
   - DD-15: the Queen's key opens the Pharaoh's lift.

   Most of this is an A3 edit to the hooks with no map rebuild, because the door events only call
   `XeenQuests.hook(...)`.
3. **Keep 16 gates, each because it is the story itself,** each with a refusal line that names where the way in comes
   from:
   - nine late-story seals: XD-19's cupie doll, FD-01, FD-02, FD-03, FD-04, DD-16, DD-17, DD-21's Necropolis pass and
     DD-22;
   - seven earlier gates:
     - XD-01: the warehouse key, moved onto the rain barrel in sight;
     - XD-07: the Crusader title;
     - XD-12: the Skeleton Key, the Act IV hinge, which keeps a level-30–48 no-magic tower away from the Act II hub;
     - XD-13: the party's own staged castle;
     - XD-24: the sundial puzzle at the door, without the night condition;
     - DD-03: the out-of-phase castle;
     - DD-14: the griffin flight.

   Castleview's town pass stays (M14's arrival beat, two routes).
4. **No refused door ever moves the party.** The Dragon Cave's "throw" is the F12 door that "takes the party outside".
   It goes, and the rule goes into the quest format.
5. **The check that keeps it fixed:**
   - `tools/xeen/quests.py` refuses any condition on a dungeon's outer-door hook that is not on the sealed list (with
     its reason and pointer);
   - a map-Lua scan catches direct qbit checks on dungeon entrances (X2's Yak door);
   - every condition inside a dungeon carries a tag (`beat`, `puzzle`, `order`, `faction`, `shortcut`).
6. **Effect:**
   - Tests: about 20 segments change (§1.4): main 09, 19, 23, 25–35, 45, 47, 49, 55, 57, 65 and 69; promotions 35 and
     67; side quests q-c8/9, q-c12, q-c25, q-d8, q-d9, q-d17 and q-d18.
   - Balance: only DD-07 and DD-12 become reachable about one act early. That is at most 34.7k of Act IV's 290.7k kill
     XP per member (12 %), inside the 15 % rule, and both are hard for an early party.
7. **The user is right about the Dragon Cave, and the fault is structural.**
   - The cave opens on a stone-and-plank tax office.
   - Its dragon halls are rectangular rooms with flat floors and ceilings, papered in one rock texture.
   - The hoard is a flat coin floor, and the starwell at the world's rim shows a blue day sky.

   The same fault runs through the world:
   - The studio has cave tools (`floor_points` uneven floors, `ceiling_points`, `rough` walls, `stalactites`), but no
     cave, lair or mine room of any Xeen dungeon uses an uneven floor.
   - No tower has a round or polygonal outer wall.
   - Several dungeons drifted off their assigned shipped family: XD-23 not d13, DD-11 not d43, XD-24 not d21, and
     FD-03 too pale for "Darkstone".

   One dungeon contradicts its name (XD-18). Four nearly do: XD-13 Newcastle's "ruin" is a roofed box, DD-09 the
   Temple of Bark reads as a log cabin, FD-03 the Darkstone Tower is pale, and DD-14 Castle Blackfang reads as a
   manor. 21 read weakly (§2).
8. **Structural identity fixes:**
   - A1 adds cave-shape metrics to `oymap metrics` and an audit warning for cave-, mine- and lair-family maps, with
     targets measured on MM8 d17, MM7 7d07, MM6 6d05/6d09 and MM8 d12/d13.
   - Every brief gets an `identity:` block (shape, family, three things seen) and an L4 "name test" (the arrival, the
     first fight room and the signature room must read as the name).
   - Further rules: towers get a polygonal outer wall with sky windows, walls get bands and a cornice instead of one
     texture from floor to ceiling, set pieces are built as geometry rather than boxes, and sky openings take the
     map's sky.
9. **Order of work:**
   1. A3 gate edits, which are cheap and immediate.
   2. Then XD-18 (rebuild the dragon spaces as caves, §2.2), followed by XD-13, DD-09, FD-03 and DD-14.
   3. Then the cave maps through the new audit: XD-05, XD-10, XD-16, XD-23, XD-26, DD-10, DD-11 and DD-23.
   4. Then towers, castles and sewers by cost.

---

## 1. F17: gating

### 1.1 What gates what today

Every way in was read from the map Lua: an event that calls `evt.MoveToMap` into `xeen_xd*`, `xeen_dd*` or
`xeen_fd*`, and its conditions. Each hook's `requires`/`needs` was read from the quest and NPC sources. 74 outdoor
entrance events lead into the 66 BLVs:
- 42 ask nothing, or ask only the D-72 entry question;
- 6 are shortcuts that open from inside: XD-01's culvert, XD-03's shaft, XD-02's west adit, XD-05's back gate, the
  DD-01 outfall and DD-18's desert grate. These are fine and MM-like;
- the rest are the gates below.

Inside dungeons, the conditions that stop a clear are XD-07's crusaders' portcullis and cellar door, and XD-18's inner
door, which throws the party out. Conditions inside that guard only a beat, a puzzle or a boss order are listed in
§1.3 and kept.

Templates used in the proposal column:
- **OPEN**: the outer condition goes and the key item is retired; its giver's reward is re-pointed (gold,
  experience, a line that says where the dungeon is).
- **INWARD**: the outer door opens, and the same item or bit locks only the room holding the story beat. That room
  holds the beat and nothing else: no monster group counted in the map's kill XP, no chest but the beat's.
- **KEEP**: the gate is the story itself. The key is found in plain sight nearby, or given in the same step, and the
  refusal line says plainly where it comes from.

### 1.2 Per entrance

Map lanes: A5 owns X1–X4, X6, X7, X9 and D3; A6 owns X5, D1, D2 and D4–D7; A7 and A8 own the dungeons as their lane
files list. "Hook only" means that the map's door event already does nothing but call `XeenQuests.hook("…")`: the A3
change in the quest file regenerates `quest_hooks.yml` and needs no map rebuild. The map lane only confirms it in one
run.

| Site | Now (gate; why) | Proposal | Who acts | Cost |
| --- | --- | --- | --- | --- |
| XD-01 Joe's Warehouse (X1) | `m2.warehouse_door` needs `warehouse_key`, hidden under the rain barrel in Joe's yard. The source's locked warehouse; the drunk's clue. Refusal: "KEEP OUT. THIS MEANS YOU, GUNTHER." (no pointer) | **KEEP**, as MM6's Goblinwatch key: the key lies **on** the barrel's lid as a ground item, in sight from the door. The refusal adds: "A rain barrel stands by the door. Joe is the kind of man who hides keys in rain barrels." | A3 (line), A5 (X1: the key as a world item on the lid, not a click) | S |
| XD-04 Witch Tower (X1) | `m4.tower_door` needs `crystal_key`, given by Valia on her first topic with no other condition. The source's engine key check | **OPEN.** The tower stands open. Valia's first line loses "Here is the key to their tower" and says the witches "fear nothing, and lock nothing". The Crusader title is still hers (Alacorn plus Head Witch). `crystal_key` is retired. XD-04's cloud stair to X8 reads `m4.head_witch_slain` instead of `m4.done`: the beat is the witch's death, not the visit home | A3 (m4.yml), A2 (retire item row), A7 (XD-04 stair condition) | S |
| XD-06 Temple of Yak (X2) | X2's door event tests qbit 110101 (`q-c12.yak_stone`) directly; Mirabeth gives the Yak Stone (Q-C12). The source's dungeon stone | **OPEN.** Mirabeth's Q-C12 keeps its point (bring her the Elixir from the reliquary) and only names the temple. The Yak Stone is retired. The 6 Megacredits are plain loot | A5 (X2 event: drop the qbit test, a map rebuild), A3 (q-c12, m10), A2 (item) | S |
| XD-07 Castle Burlock (X4) | (a) the portcullis inside the door: `m5.crusaders_gate`, `m4.done`. The source's "Only Crusaders are allowed to enter Castle Burlock." (b) the cellar's cell-block door: `xd07.dungeon_door`, a bit set by Artemus's "The dungeon" topic | (a) **KEEP**: it is the Act I→II beat, a title earned rather than an item, and the line is the source's. The refusal adds: "Old Valia of Toad Meadow names Crusaders." (b) **OPEN**: the cellar door is unlocked. Artemus's topic stays as the hint ("nobody has gone down since") without handing over a key | A3 (m5 line; xd07.yml), A7 (confirm the cellar door event) | S |
| XD-08 Tomb of a Thousand Terrors (X3) | `m10.tomb_door` needs `stone_of_terrors`, from Emerson after the walls (M9). The source's stone; it orders the Megacredit chain | **OPEN.** The Megacredits are already `map_gives` loot (XD-06 6, XD-08 5, XD-09 5; 15 needed for M9, M11 and M22), so Emerson's stages stay ordered by the count alone. Emerson's stage lines become directions (an autonote naming the next site). Both stones are retired | A3 (m9, m10, m11), A2 (items) | S (hook only) |
| XD-09 Golem Dungeon (X5) | `m10.golem_door` needs `golem_stone` (after the keep, M11) | **OPEN**, as XD-08 | A3, A2 | S (hook only) |
| XD-10 Cave of Illusion (X5) | Open. Inside, the bronze plug needs Might 30 and leads to the skull (M12) | Keep the plug, as an MM-style stat check. Its refusal says what helps: "A stronger arm, or a potion of Might, might shift it." D-68 already covers the chain test | A8 (line) | S |
| XD-11 Tower of High Magic (X3) | `m13.tower_door` needs `enchanted_key`, sold by XD-10's skull for 10 gems (M12) | **INWARD.** The tower door opens. The Enchanted Key locks only the L4 study that holds the Skeleton Key chest (the source's chest at 7,12). The study holds no monsters and no other chest. M12 keeps its meaning | A3 (hook moves to XD-11), A8 (XD-11: the study door event; the door on X3 loses its call), A5 (X3 confirm) | M |
| XD-12 Darzog's Tower (X2) | `m13.darzog_door` needs `skeleton_key` (or the held item 12100). M21 ◆: the Act IV hinge, an L dungeon at 30–48 with no spells inside, on the Act II hub's lake | **KEEP**: the key is found as loot in XD-11, the MM-style chain. Opening it would put a level-30–48 no-magic tower in front of a level-11 party at the hub. The refusal names it: "The Skeleton Key that fits it went up the Tower of High Magic with the King's alchemists, they say." A5's own SimpleMessage says the same | A3, A5 (X2 text) | S |
| XD-13 Newcastle Keep (X3) | Qbit 111160 (the deed); the board says "CROWN LAND. FOR SALE. ENQUIRE AT EBENEZER'S TENT." The party's own castle, staged | **KEEP**: the castle project is the story, and the board already points plainly | — | — |
| XD-15 The Sphinx (X6) | `q-c9.door` needs `northern_sphinx_amulet`, Arie's reward for Q-C8 | **OPEN.** The beats inside are already guarded by the name "Golux" (said by Arie and by a Basenji prisoner), which is the riddle the game answers. Arie's reward keeps its gold and experience; the amulet is retired, or kept as a ring-slot artifact on a shipped skin (U-1) if A2 wants loot there | A3 (q-c8, q-c9), A2, A5 (X6 confirm; the `entered` qbit test stays harmless) | S |
| XD-18 Dragon Cave (X7) | The mouth is open, but the inner door (`q-c25.inner_door`, `tax_paid`: 2,000 gold and 20 gems, D-81) guards the whole interior, and a refusal **throws the party onto the mountain** | **INWARD.** The inner door opens and stays open. The tax buys only the Great Wyrm promotion and the Dragon King's door ("Tax first," says the door, and it stays shut; no throw). Scaldrith's Grandmaster teaching stays untaxed, as D-81 has it. The library's volumes and every dragon hall can be cleared without paying. This supersedes D-81's "and XD-18's interior" | A3 (q-c25), A7 (XD-18: remove `leave`, move the condition to the King's door), A2 (D-81 note) | M |
| XD-19 Castle Xeen (X9) | `m34.gate` needs `lord_xeen_doll`; Slick's prize stand on the same causeway. The source's "No one may enter Castle Xeen without a cupie doll!" | **KEEP**: the key is won about 2,000 units away, and the joke is the source's | — | — |
| XD-24 Nightshadow Crypt (X3) | `q-c7.coffin`: the dials set **and** night (21:00–6:00). The square's sign "The Count wakes at nine and sleeps at nine." and the rhyme answer the dials | **KEEP the dials** (a puzzle at the door, answered in sight) and **drop the night condition**: no other Xeen dungeon makes the party wait for the clock, and the rhyme still colours the Count | A3 (q-c7) | S (hook only) |
| FD-01 Alamar Depths (D6) | `m39.depths_door` needs the Cube of Power (finale) | **KEEP**: a finale seal. The refusal ("sealed with Sheltem's mark") is plain | — | — |
| FD-02 Southern Sphinx (X6) | `m40.sphinx_door` needs Roland's amulet (M40) | **KEEP**: a finale seal; the refusal names an amulet-shaped hollow | — | — |
| FD-03 Darkstone Tower (X5) | `m41.tower_door` needs `m39.darkstone_key` (M41) | **KEEP**: a finale seal | — | — |
| FD-04 Dragon Tower and Dungeon of Death (X7) | `q-f1.tower_door` needs `dragon_tower_key` (found in FD-01, Act VI); the lower half needs Sandro's `death_dungeon_key` (Q-D23's end) | **KEEP** both: optional endgame at 65–100, keys found or earned as the source does (as MM8's Prison keys). The tower's refusal adds where: "…The dragons say its key lies under Castle Alamar." | A3 (line) | S |
| Castleview (D1, town) and DD-02 inside it | `m14.gate`: the pass (Justine, 1,000 gold) or the gremlin court won (M14, the Darkside arrival beat). D-30's let-out machinery | **KEEP**: a town gate with two routes, and the guard already names both | — | — |
| DD-01 Castleview Sewer (D1) | Hatch open; the outfall opens from inside | Fine | — | — |
| DD-02 Ellinger's Tower (D1) | `m17.tower_door` needs `ellinger_key`, Nadia's reward for her necklace (M16, DD-01) | **OPEN.** The tower is its own test: the moral question at the door, and the top study's password "Ellinger", which Oorla says plainly. Nadia's reward becomes gold and experience plus "Ellinger owes me a favour. Tell him Nadia sent you." M16 stays on the journal as Castleview's errand. The key is retired | A3 (m16, m17), A2 | S (hook only) |
| DD-03 Castle Kalindra (D1) | `m19.ghost_castle` until stage 1 (5 disks) | **KEEP**: the out-of-phase castle is the story; staged content | — | — |
| DD-05 Western Tower of Mok (D1) | The front door needs `west_tower_key`, which lies inside at the top; the heretics' rope on the north wall is open (the source's route) | **KEEP** (the right pattern). The refusal adds the rope: "…The key is upstairs, with the heretics. A rope hangs from a window on the north wall." | A3 (q-d6 line) | S |
| DD-06 Southern Tower (D2) | `q-d19.tower_door` needs `south_tower_key`, given by Thaddeus at the start of Q-D19 | **OPEN**; key retired, Thaddeus's request unchanged | A3, A2 | S (hook only) |
| DD-07 Eastern Tower (D3) | `q-d18.tower_door` needs `east_tower_key`, in DD-06's Ali Baba chest; Q-D18 starts after `q-d19.chest_opened` | **OPEN.** The Jewel of Ages on L3 stays Thaddeus's beat; Q-D18's `after` becomes `q-d19.started`. The Ali Baba chest keeps its own treasure | A3 (q-d18, q-d19), A2 | S (hook only) |
| DD-08 Northern Tower (D5) | `q-d17.tower_door` reads the bit `key`, set by Bosco when Q-D17 starts | **OPEN.** The beat inside (the voice, the Chalice, the oath) is unchanged | A3 | S (hook only) |
| DD-09 Temple of Bark (D2) | `q-d9.bark_door` needs `bark_key`, Nibbler's reward for the Monga melons | **OPEN.** Nibbler's melons pay his hints and a treasure-3 item instead (the running joke stays). Key retired | A3 (q-d9), A2 | S (hook only) |
| DD-10A/B/C, DD-11A/B/C, DD-13 (D1, D2, D6) | Open (`q-d13.troll_holes` has no condition) | Fine | — | — |
| DD-12 Dungeon of Lost Souls (D4 isle) | `m24.isle_door` needs `lost_souls_key`, Megan's at Kalindra stage 2 (10 disks). The ferry runs daily (D-12.1) | **INWARD.** The isle gate opens; Megan's key opens the Songbird's cage on the fifth floor (M24's beat). Ferris Gull warns: "The Isle eats parties. Come back stronger if you value your boots." | A3 (m20, m24), A8 (cage condition), A6 (D4 confirm) | M |
| DD-14 Castle Blackfang (D4) | Only Ambrose's griffin flies the party in (`m25.gate_flight`); the gate never opens on foot | **KEEP**: the flight is M25's beat, and the castle on the crag is the story | — | — |
| DD-15 Great Pyramid (D5) | `m28.door` needs the Queen's `pyramid_key` (M27) | **INWARD.** The door opens; L1–L3 (the dragons, the torches, the registry lock, the pad maze) can be cleared. The key goes on the Pharaoh's lift (`m28.lift`, which already reads `throne_reached`) and on the antechamber's door on L4. D5 is an Act V map either way | A3 (m28), A8 (DD-15 door events) | M |
| DD-16 Corak's Pod (D6) | `m29.pod_door`: lava cooled by the Pharaoh | **KEEP**: a main-story set piece (7 monsters) | — | — |
| DD-17 Castle Alamar (D6, D7 roof) | `m33.arrival` needs Corak's Soul Box | **KEEP**: the finale | — | — |
| Sandcaster (D3, town): DD-18, DD-19 inside it | `q-d8.sandcaster_gate` needs `sandcaster_pass`, Vespar's reward for the emerald handle (Q-D8). D-28(3) kept it | **OPEN** the town (supersedes D-28(3)): a second pass town in one act is the tedium the research warned of (MM5_DARKSIDE_CONTENT, "keep them only where the story needs them"), and it also gated M25's Natasha. Vespar's reward keeps its gold and experience plus his staff's teaching line; the pass is retired | A3 (q-d8), A2, A5 (D3 confirm) | S (hook only) |
| Necropolis (D6, town): DD-21 inside it | `d6.necropolis_gate` needs `necropolis_pass`, which lies in the Head Witch's chest (DD-20) | **KEEP** (a key found as loot, Act V). The refusal points to it: "The living need a pass. The dead need nothing. The Lakeside witches write passes for both." | A3/A4 (d6.yml line) | S |
| DD-20 Lakeside Coven (D4) | The guild's back stair waits for the front door's riddle; the sewer shaft is open | Fine (open by the sewer) | — | — |
| DD-22 Sheltem's Pod (D6) | `d6.sheltem_hatch` after M33 | **KEEP**: sealed from inside until its master falls. Optional lore, Act VI | — | — |
| DD-23, DD-24, DD-25, XD-14, XD-16, XD-20, XD-21, XD-22, XD-23, XD-25, XD-26, XD-27, XD-02, XD-05 | Open (D-72 question at most) | Fine | — | — |
| XD-17 Shangri-La (X7) | Hidden: reached through XD-16's skulls; the cleft opens from inside | **KEEP**: a hidden town with no monsters; the way is a puzzle in XD-16 itself | — | — |
| D7 and P1–P4 | The Dark Grove rope and the tower roofs need `m30.done` (the Chosen) | **KEEP**: the sky is Act VI's map, sealed by the story | — | — |

Count after the change: 16 sealed sites (9 of them Acts V–VI finale seals) against 32 today. Two town passes stay
(Castleview, Necropolis).

### 1.3 Conditions inside dungeons: kept, with a tag

These do not stop a clear, so they stay. Each one gets a tag in its hook (§1.5):
- **beat** (guards only the story beat): XD-07 Roxanne's bedroom chest (her reward), XD-15's four thrones (after
  Golux), XD-19's barrier (four generators in the same map), DD-15's torches stair, DD-21's grille, FD-03's chime seal,
  FD-04's crossword descent, and after this change the XD-11 study, the XD-18 King's door, the DD-12 cage and the DD-15
  lift.
- **puzzle** (answered in the same map, or by a named answer-giver in the riddle table): XD-13 "laboratory" (Crodo
  at M21), XD-14 "There wolf" (Arie's note), XD-25's pedestals (Asp's rhyme), DD-02 "Ellinger" (Oorla), DD-06 "open
  sesame" (the guild memo), DD-12's five "think positive" gates, DD-17's true name (the Olympus plaque), DD-21's wheel.
- **order** (boss first): DD-14's stair to the dungeon after the Count.
- **faction**: DD-13 Graalg's strongbox, DD-24's hoard, DD-20's witch chest and DD-11C's hoard. Both routes reach each
  one; the violent route opens it.
- **stat checks on chests** (MM-style, kept): XD-06's coffin, XD-08's great coffin, XD-15's sarcophagus and FD-02's
  sarcophagi. One fix: XD-06 tests `BaseMight 25`, so a Might potion does not help. It should test `ActualMight`, as
  the others do (A8).
- **refusals that move the party:** none may remain. The XD-18 throw is the only one today.

### 1.4 Effect on the tests

| Chain | Segments | Change (owner A3; A3-promo for promotions) |
| --- | --- | --- |
| Main (`tests/playthrough/xeen/`) | 09_witch_tower | No key step; the door opens without Valia; the cloud stair reads `head_witch_slain` |
| | 19_the_deed, 23_temple_of_yak | No Yak Stone step |
| | 25_the_walls, 27_the_tomb, 29_the_keep, 31_golem_dungeon | No stone steps or refusals; the Megacredit count alone orders the stages |
| | 33_cave_of_illusion, 35_tower_of_high_magic | The Enchanted Key is used at XD-11's study, not at X3's door |
| | 37_darzogs_door | Unchanged apart from the refusal line, if asserted |
| | 45_castleview_sewer, 47_ellingers_tower | No Ellinger key |
| | 49_temple_of_bark, 55_southern_tower, 65_jewel_of_ages | No keys; Q-D18's `after` changes |
| | 57_lost_souls | The key is used at the cage |
| | 69_great_pyramid | The key is used at the lift and the L4 door |
| Promotions | 35_voweless_oath (Bosco's key), 67_dragon_tax (no throw; the tax at the King's door and the promotion) | as left |
| Side quests (`tests/scenarios/xeen/side_quests/`) | q-c8_q-c9 (amulet), q-c12 (Yak Stone), q-c25 (tax), q-d8 (pass), q-d9 (key), q-d17 ×2 (key), q-d18 (key) | as left |
| New | one scenario per opened site: enter without the old item, reach the boss room. One per moved lock: refused at the beat, allowed with the item. One for "no refusal moves the party" (XD-18) | A3 |

Run only the affected segments (`run.py NN`), as the playthrough rules say.

### 1.5 The structural fix and its check

1. **Format rule** (A3, `formats/QUESTS_FORMAT.md` §7):
   - A hook whose `where` is a dungeon's outer door may carry `requires`/`needs` only with `sealed: "<reason>"` and a
     `fail_text` that names where the key or the way in comes from.
   - A hook on a dungeon map with `requires` carries one tag: `beat`, `puzzle`, `order`, `faction` or `shortcut`.
   - A `beat` room holds no counted monster group and no chest but the beat's.
   - No `fail_text` path may move the party.
2. **Audit** (A3, `tools/xeen/quests.py`): it enforces item 1 and prints the sealed list. The list starts as the KEEP
   rows of §1.2; a new seal needs a decider.
3. **Map-Lua scan** (A3 writes it, A1 adds it to `tools/xeen/regressions.sh`): every event in
   `events/maps/xeen_*.lua` that moves into a `xeen_(xd|dd|fd)*.blv` while testing a qbit, an item or a conditional
   hook must be on the sealed list, or be a shortcut whose bit is set by the same dungeon. This catches X2's direct Yak
   test, which the hook audit cannot see.
4. **Pointer check**: the audit prints every sealed refusal line, and the riddle table's "said_by" must name an
   answer-giver reachable before the gate.

### 1.6 Act balance

| Opened site | Dungeon's act | Earliest reach before → after | Effect |
| --- | --- | --- | --- |
| XD-04 | I | Valia (free at start) → start | none |
| XD-06, XD-08, XD-09, XD-11 | II | after Q-C12, M9, M11, M12 → on arrival at X2, X3, X5 | order within Act II only; Megacredits and quest XP unchanged |
| XD-15 | IV | after Q-C8 → X6 (an Act IV map) | none |
| XD-18 interior | optional, 60–64 | after the tax → at the cave | none (the party is at the cave anyway) |
| DD-02, DD-06, DD-09 | III | after M16, Q-D19 start, Q-D9 → arrival | none |
| DD-08 | V | after Q-D17 start → D5 (an Act V map) | none |
| DD-15 L1–L3 | V | after M27 → D5 | none |
| DD-18, DD-19 | III / IV | after Q-D8 (level 21) → Sandcaster's arrival | none in practice |
| **DD-07** | IV (28–48) | after DD-06's chest → D3 (an Act III map, 27–30) | up to 11.2k kill XP per member about one act early |
| **DD-12** | IV (35–55) | after Kalindra stage 2 → the daily ferry | up to 23.5k kill XP per member early; its monsters punish a level-25–30 party, and the ferryman warns |

Worst case: 34.7k of Act IV's 290.7k (12 %), under the 15 % act rule. A2 recounts once, after the change. No monster
levels change.

---

## 2. F12: dungeon identity

### 2.1 What is wrong, world-wide

The user asked whether the Dragon Cave is really a dragon cave. It is not. The same faults recur across the world,
so the fix is structural first and per map second.

- **Caves built as rooms.**
  - Natural spaces are rectangles with flat floors and flat ceilings, one rock texture tiled over walls and ceiling:
    XD-05, XD-10, XD-16, XD-18, XD-23, XD-26, DD-10, DD-11, DD-23, the deep parts of XD-02, XD-06 and XD-07, and
    DD-04's burrows.
  - The studio already draws caves: `floor_points` uneven floors, `ceiling_points`, `rough` walls, `stalactites`,
    `path` sections.
  - In the built projects, uneven floors appear only in XD-01, XD-02, XD-03, XD-12 and XD-17. No cave, lair or troll
    map has one.
  - MM8's own Dragon Cave (d17), MM7 Thunderfist (7d07) and MM6 Snergle's mines (6d05, 6d09) are sloped, broken and
    irregular.
- **Towers do not read as towers.** Only DD-05's chapel, DD-07's well and XD-12's Well break the box. None of DD-02,
  DD-05 to DD-08, XD-04, XD-11 or FD-03 has a round or polygonal outer wall with windows to the sky. The four Towers of
  Mok share MM8 d27, and their lower floors look identical.
- **The assigned family drifted.** XD-23 never used d13, DD-11 never used d43, XD-24 not d21, and XD-08 is not laid
  as 6d14. FD-03 is pale for "Darkstone". DD-09 laid bark over boxes rather than 7d22's hill-and-root shapes.
- **One texture from floor to ceiling.** DD-06, DD-08, DD-11, DD-12, DD-19, DD-20 and DD-26 show no base course,
  band or cornice. The studio has `bands`; shipped BLVs always have them.
- **The set piece that carries the name is a cuboid or missing.** Examples: XD-18's flat coin hoard and caged King;
  XD-05's drum hall; XD-09's wood "trunk"; XD-13's "ruin", a roofed box; DD-14's plank-box coffins; the gym in DD-18;
  the transformer in XD-25; the thrones in DD-08 and DD-11C; the Gremlin Court's missing heap of stolen things.
- **First impression wrong.** XD-18 opens on a d16 stone-and-plank office before any rock.
- **Skies and vistas off.**
  - XD-18's starwell at the world's rim shows a blue day sky.
  - The green-meadow exit picture `xodaylt` stands at the mouths of volcanic, desert and Darkside maps: XD-16, XD-18,
    XD-25 and DD-13. F12's exit item may make these black MM6–MM8 exits. If so, this point lapses; if not, each region
    needs its own vista.
- **Stand-in bodies weaken names.**
  - Every XD-09 golem tier is one recoloured body.
  - XD-13's wood golems wear the MM7 pharaoh golem's headdress.
  - XD-07's "caged fire dragon" stands in a bare box with no bars and no heat.
- **Dressing thins with depth.** The signature rooms are dressed, but the back rooms are empty boxes with box
  furniture.

### 2.2 Per dungeon, worst first

Severity: 5 means the name is contradicted, 3 weak, 2 thin, 1 reads right. Cost: S is textures and dressing, M is
some rooms reshaped, L a rebuild. Who acts: the map lane (A7 or A8 as owned; A5 XD-17 and P5; A6 P1–P4). A6 joins
where a texture or vista enters the registry, and S where a body changes. Every fix uses engine, MM6, MM7 or MM8 art
(D-44), adds no item art (U-1), and registers any new texture with A6 inside the per-map caps (S 4, M 8, L 14).

| Site | Now | Proposal | Who acts | Cost |
| --- | --- | --- | --- | --- |
| **XD-18 Dragon Cave** (5) | Mouth → a full d16 stone-and-plank office with crates (`xd18/shots_sheet1.jpg` 02–03), then rectangular dragon halls in `t68a02a/b` with flat floors and ceilings; a flat `xncoins` floor for the hoard; a caged King that is a recoloured Fire Dragon; the starwell's slot shows a blue day sky; the library has plank walls; Dragon Lore lies on a bare beige cube (F12's "empty podium") | (1) **Carve the office into the rock**: a rock antechamber in d17 `t68a02b` with the counter, the urn and Scaldrith's door as plank fittings; no plank walls or ceiling. (2) **Rebuild the dragon spaces as caves**, as MM8 d17 is built: the bone hall, roost, egg cave, starwell, dens and the King's hall get 7–12-sided rough outlines, `floor_points` slopes and rubble ramps, `ceiling_points` vaults and rock pillars. Only the 288-high party tunnels stay square (D-32). (3) **Dress for dragons**: char and scorch (`xoburn`, `xochar`), bones and dead adventurers' armour in the bone hall, 7d07 lava cracks at the fire crossing and vents, MM8 snow and rime in the frost dens, green pools in the acid hollows, the eggs (S). (4) **The hoard as a mound**: sloped `floor_points` under `xncoins` (or `xdhoard`, which D-57 allowed), with the King on top, uncaged, his skin pending with S. (5) **The starwell shows stars**: the slot takes a night or stars preset (A6/A1; one new picture at most). Replace the mouth vista with a scorched one (DD-23's `xdcraglt`), or use F12's black exit. (6) The library cut into the rock, with rock above the shelves; the volumes on a shipped lectern or book-stand decoration, never a bare cube. Together with §1's inward tax door | A7, A6 (sky, vista), S (King) | M |
| **XD-13 Newcastle Keep** (4) | Stage 0's "ruin" is an intact, roofed sandstone room with a darker ceiling inset for a "hole"; two small rubble piles; the wood golems are MM7's pharaoh golem (`xd13/look1_a.jpg`); the stage-3 cellar and lab are bare brick | Open the hall's middle to the sky as XD-12's Well does: broken rafters, a fallen wall corner, sloped rubble mounds (`floor_points`), the woodpile. Lay 7d29's ruined Harmondale walls as dungeon_families assigns. Wood golems on a wooden golem body or tint (S). A real laboratory (7d12 benches and bottles) and a heavy steel vault door at stage 3 | A7, S | M |
| **DD-09 Temple of Bark** (4) | Bark texture on the flat walls of rectangular rooms, plank floors, a grass-floored box for the "crown", brick barracks rooms (`dd09/shots/baked_a.jpg`): a log cabin, not a temple grown in a tree | The Hall of the Trunk and the ring stair round (12–16 sides) under a bark dome (`ceiling_points`). The root level in 7d22 earth (`c2b`, `cfb1`), irregular and sloped, with root pillars as geometry. The limbs as narrow, tapering branch walks open to leaves and sky. The crown open to the sky, as DD-11's pit is. The "feed me" alcoves as knots in the trunk | A8 | L |
| **FD-03 Darkstone Tower** (4) | Pale green-grey granite tiles, a light scale-tile ceiling and plank doors: a light-stone keep (`fd03/sheet1.jpg`) | Black walls: the darkest MM8 d29 ashlar or 7d07 `c2b` with `swankdk` iron trim; dark ceilings; iron doors; the central well as an open shaft through every floor | A7 | S–M |
| **DD-14 Castle Blackfang** (4) | Tan and green brick boxes with yellow tiles and bookcases; coffins are plank boxes; one torn-polygon fault (`dd14/shots/baked_s9_a.jpg`): a manor | 7d13 crypt stone and dark flags on the upper floor (dungeon_families: 7d32 with 7d13 crypts); ribbed and pointed vaults (`ceiling_points`); lidded six-sided biers on plinths; red and black banners; bats and guano in the roost; fix the torn faces | A8 | M |
| XD-05 Orc Caves (3) | The palisade reads; behind it are brown rectangular "caves" with flat floors, and the drum hall is a plank table in a box | MM8 Ogre Fortress d12 as d12 lays it: irregular rooms, sloped floors, low uneven ceilings, two or three of its rocks plus mud. The drum hall as a real bowl with terraces (`levels`). Hide curtains, skull totems, soot over the cookfire. S checks the orcs' bodies against the Orc family | A7, S | M |
| XD-08 Tomb of a Thousand Terrors (3) | A tan brick barracks; a torture gallery of bare poles; brick-box coffins | 6d14 (Tomb of Ethric) as it is laid: dark stone, skull friezes, burial niches with bones; shipped coffins and sarcophagi; chains, cages and stocks so the devices read; a skull throne on a dais | A7 | M |
| XD-09 Golem Dungeon (3) | The hub and quarry read. The wood home is a plank box with no trunk; iron is a dark brick room; diamond is a bright blue tile box; every golem tier is one recoloured body | Wood: a round trunk plan with 6d16 bough beams. Iron: anvils, bellows, 6d18 forge glow. Diamond: MM8 d37 `gcrysc3` crystal pillars and clusters as geometry. Distinct tier tints or sizes (S) | A8, S | M |
| XD-10 Cave of Illusion (3) | Boxy caves in one grey rock with flat floors; the illusory walls are blue glass grids that give the trick away | Irregular outlines and slopes across d33's several rocks. The illusory walls wear their neighbours' rock. Weed and silt on the drained floor; ice only at the two mouths | A8 | M |
| XD-11 Tower of High Magic (3) | Rectangular plaster rooms; the laboratories are empty but for one cauldron and blood; the coils are iron boxes; the roof is a flat yard | Round or octagonal floors round the lift shaft. MM7 Clanker's Laboratory and School of Sorcery furniture (tables, bottles, glowing crystals), a coloured light per laboratory, no blood. A crenellated roof. With §1's study door | A8 | M |
| XD-16 Volcano Cave (3) | Rectangular 7d07 brown boxes; lava only in the magma pit; a pink-brick demon shrine; a green-meadow mouth vista | Rough, sloped cave rooms; lava channels and cracks (7d07 `lava`) in the gallery, the fissure and the lake; MM6 6d04 `vlcwl*` for the shrine; a scorched vista or F12's black exit | A7 | M |
| XD-19 Castle Xeen (3) | Large grey rectangular halls with pale ceilings, gold friezes and Ancient panels | MM8 d35's darkest wall and ceiling set (black under gold); dark vaults; a raised stepped throne dais with pillars toward the Mirror; open battlements and sky in the aviary; apse and cross-hall shapes | A7 | S–M |
| XD-22 Ninja Pagoda (3) | Plank rooms with a cobble-and-bone wainscot and frosted-glass "paper": a timber lodge | Dark timber full height with red-lacquer trim (2 of the S 4 new). Sloped eave ceilings (`ceiling_slope`) shrinking per storey; an open moon gallery over the mere; screens lit warm like paper | A7, A6 | M |
| XD-24 Nightshadow Crypt (3) | Tan and grey flagstone boxes: a castle cellar | MM8 d21 vampire crypt (dark stone, coffin niches) as assigned; low ribbed vaults; coffins in rows; bone heaps; a black sarcophagus in the vault | A7 | S–M |
| DD-02 Ellinger's Tower (3) | MM6 6d19 rose marble done well, but a mansion: a straight corridor for the "walk round the outer wall"; straight stairs | Floors 3–4 within an octagonal outer wall; the trapped walk bent round it with windows to the sky; the bat roost's broken window open to the sky; bookcase walls (`t1books`) | A8 | M |
| DD-04 Gremlin Court (3) | Straight burrows in Tularean earth; the court a brick hall; the town's stolen things (the dungeon's joke) barely visible | The hall heaped with the town's missing things (stacked crates, barrels, cart wheels, rope coils, sacks, the mill's gears if a shipped model exists). Low (about 192), crooked burrows with a child-size first door | A8 | S–M |
| DD-06 Southern Tower (3) | Large empty d27 tile boxes: neither thieves' den nor tower | Plank partitions, floors and walks (MM7 7d17's weathered planks); bunks, loot tables, lamps, sacks; a polygonal outer wall. Its own accent (it is the only Mok tower without one) | A7 | M |
| DD-10A/B/C Gemstone Mines (3) | A timbered adit with rails, then rock boxes with flat vein panels; B's crystal god and C's lava seam are good | Nighon timber sets (`trim9_32`, `trim9_32a`) along every gallery; rails and the cart deeper; irregular stopes with slopes and rock pillars; each vein framed by shipped `gcrys` clusters | A8 | M |
| DD-11A/B/C Troll Holes (3) | `7dirttyl` on every face of box rooms; Hobstadt's hall an empty dirt box | MM8 d43 (Ancient Troll Home) cut stone and carved slabs for Hobstadt's hall and guard rooms, as assigned; irregular burrows with root ceilings; 7d08 `cwb1`/`cfb1` so walls and floors differ; a shaped throne | A7 | M |
| DD-12 Dungeon of Lost Souls (3) | Good bone-and-rubble entrance, then tan brick storerooms on every floor; a hedge maze | MM7 d02's darker wet rock on floors 3–5; pillars, low arches, side cells; broken masonry in the maze | A8 | M |
| DD-19 Wizard Quarter (3) | A walled precinct of one pink brick; two rival guilds don't read | The Mirage Guild with bookcases, a magic circle and the crystal stand; the Sorceress HQ with violet braziers and skull shelves; a base course and cornice in the court | A8 | S–M |
| DD-20 Lakeside Coven and Sewer (3) | Huge empty brown-brick halls with a few cauldrons; one rock throughout the sewer | Halve the halls; drying herbs, jar shelves, a pentagram floor; the sewer in 7d17 wet stone with plank walks (as assigned) | A8 | M |
| DD-23 Gargoyle Lair (3) | 7d07 rock with rectangular sections, against D-39's "natural cave" | Slanted walls, varied floor heights and broken corners; perches as rock ledges with guano; the ring of roosting rocks and bones round the snow | A7 | M |
| DD-25 Bosco's Hall (3) | Brick corridors with timber house fronts: a town street, not a dwarf hall in the crag | 7d24's raw-rock vaults over the great hall and the lane, brick only on the house fronts; rock-cut pillars and a higher hall; forge glow and anvils in the smiths' gallery | A8 | M |
| P3 Plane of Earth (3) | A dim brown bowl of box slabs; the quarry, geodes and Anvil do not stand out | Cut-stone faces on the quarry; large crystal clusters for the geodes; strata bands; lighter dust, closer to MM8's Plane of Earth | A6 | M |
| XD-02 Red Dwarf Mines (2) | A mine (rails, turntable, stope ledge), but straight flat drifts in one red rock; the tally room is a dressed-stone hall | Darker 6d09 rock deeper, 6d05 red near the adit; sloped floors and broken wall lines in the drifts; ore piles and picks; rock and planks in the tally room | A7 | S |
| XD-04 Witch Tower (2) | A pale stone manor; the "crooked black-timbered tower" does not show | 7d12's dark planks as the main wall; each floor's rooms turned off the grid as the plan's quarter turn says; herbs, toad cages, more cauldrons, green steam up the shaft | A7 | S–M |
| XD-06 Temple of Yak (2) | The nave reads; the pool caves are flat boxes; the idol is a small MM7 statue | Barrow I (mdt03) rock with an irregular shore and sloped banks, sick-green light; a large shipped statue on a stepped plinth between braziers | A8 | S–M |
| XD-07 Castle Burlock (2) | Royal above; the dungeon is grey-brick boxes; the "caged fire dragon" is in a bare box | The pit as a hot cave (6d18 `vlcwl3a`, `6voltyl`, red glow) behind a visible portcullis and the "Do not pull" sign; a cold cistern for the ice trolls | A7 | S |
| XD-14, XD-17, XD-20, XD-23, XD-25, XD-26 (2) | Read as named, but thin: Basenji's campfire hearth and plain battlements; Shangri-La's brown houses where the pitch says white plaster, and green rim cliffs; an empty arena; box troll rooms; a garish transformer and a meadow vista in a desert; a dark, plain eyrie shaft | Basenji: a built fireplace, kennel straw and bones, crenels. Shangri-La: Firestone's black rim rock, white plaster, the waterfall. Warzone: 7d05 stands, banners, racks. Troll Warren: rough rooms in d13 as assigned. Asp: the transformer from sci-fi.blv panels, a desert vista. Eyrie: stepped rough shaft walls, nests on every ledge | A7; A5 (XD-17) | S–M each |
| FD-04 Dragon Tower and Dungeon of Death (2) | The tower (6d04 `vlc`) works; Sandro's lower halls are grey boxes with flat shrines | A lich's home: candelabra, carpets and coffins in the ballroom; the Shrines of Evil as carved altars and gongs in geometry | A7 | S–M |
| DD-01, DD-03, DD-05, DD-07, DD-08 (2) | Read as named, thin: a sewer with flat-ceilinged crossings; Kalindra's empty rooms; the Mok towers' bare lower floors | DD-01: barrel vaults at the cross (`ceiling_points`, as MM6 `sewer.blv`) and a rubble-cave nest. DD-03: 7d33 furnishing (throne, runner, benches, beds). DD-05/07/08: dressed lower floors; 7d14 furniture in DD-07's lab; racks and a drill yard in DD-08; carved throne silhouettes | A8 (DD-01, 03, 05, 08), A7 (DD-07) | S |
| DD-13, DD-15, DD-16, DD-18, DD-21, DD-24, DD-26, P1, P2 (2) | Read as named, with one gap each | DD-13: log posts, a palisade yard. DD-15: corbelled ceilings on the processional and grand stair (MM6 pyramid.blv), inward-sloping apex walls, sarcophagi. DD-16: one tilted corridor or a lava breach (it lies nose-up in lava). DD-18: the gym's racks as geometry and a real collapse. DD-21: sewer.blv wet flags and a green glow round the jar. DD-24: oversized props. DD-26: sewer-width channels and walkways, d01 flags below the marble. P1: leaning, stepped cliffs and glowing cracks. P2: white wind-carved stone and clouds under the islands | A7 (DD-13, 16, 24), A8 (DD-15, 18, 21, 26), A6 (P1, P2) | S each |
| XD-01, XD-03, XD-12, XD-15, XD-21, XD-27, FD-01, FD-02, DD-17, DD-22, P4, P5 (1) | Read right | Small notes only: XD-03's plain barracks in 6d18 soot brick; XD-12 a dark Gloaming rug (`tfb1r4`); XD-15 darker lower galleries; XD-21 one tall vault over the race; XD-27 log geometry for the gate; FD-01 scorch; FD-02 steel blades with slots; DD-17 console tops on the dial plinths; DD-22 metal canisters, not barrels | as owned | S |

### 2.3 The structural fixes and their checks

| Fix | What | Who acts | Cost |
| --- | --- | --- | --- |
| Cave-shape metrics and audit | A1 adds three numbers per room and per map to `oymap metrics`: the share of floor area that is not level, the spread of ceiling heights, and the share of wall length that is `rough`. A6 measures them on shipped caves (MM8 d17, d12, d13; MM7 7d07, 7d08; MM6 6d05, 6d09) and sets the targets. `oymap audit` warns when a map whose family in `dungeon_families.yml` is under "caves" or "mines" falls below them | A1, A6 | M |
| Identity block in every brief | L1 gains `identity: {shape: cave/tower/temple/castle/sewer/ship/hall, family: <the assigned shipped BLV>, seen: [three things the party must see]}`. The audit warns when the built map's textures are mostly outside its assigned family, which catches drift such as XD-23's missing d13 | orchestrator (format), A1 (audit), A7/A8 (fill) | S |
| Name test at L4 | Three captures in every NOTES "Pictures": the arrival, the first fight room and the signature room. The reviewer answers one question per dungeon: "does it read as <name>?" The G3 review gets one row per dungeon. The first room past the arrival must be in the dungeon's main kit (no office before the cave) | orchestrator, A7/A8 | S |
| Towers are towers | A tower's floors stand inside one polygonal outer wall (8–16 sides) with windows to the sky on every floor. The four Towers of Mok each take their own accent on every floor, not only the top | A7, A8 | M |
| Walls have structure | Every room wall gets a base course and a band or cornice (`bands`), as shipped BLVs do; no single texture from floor to ceiling in a room taller than 384. The audit reports the share of one-texture walls | A1 (metric), map lanes | S |
| Set pieces in geometry | The object that carries the name (hoard, throne, coffin, transformer, drum scaffold, trunk) is built as geometry or a shipped decoration model, never a cuboid. Each NOTES names its set piece and shows it in the name test | map lanes, S | S–M |
| Sky openings take the right sky | A sky opening takes its map's or region's preset (stars at the world's rim; X7's `ashen`), never the default day sky. A1 checks that every `sky: true` face has an explicit preset | A1, A6 | S |
| Exit look | Follows F12's exit decision (black MM6–MM8 exits). If vistas stay, each region gets its own: scorched, desert, snow, Darkside | F12 agent, A6 | S |
| Stand-in bodies | XD-09's golem tiers, XD-13's wood golems and XD-05's orcs get bodies or tints that match the name | S | M |

These are the lasting part of the fix. The per-dungeon rows in §2.2 are the first pass through the new audit, worst
first:
1. XD-18;
2. XD-13, DD-09, FD-03 and DD-14;
3. the cave set: XD-05, XD-10, XD-16, XD-23, XD-26, DD-10, DD-11 and DD-23;
4. towers, castles and sewers.

Each rebuild takes the per-map lock and a single full reconversion per batch. Its NOTES answers the name test before
the map is reported.
