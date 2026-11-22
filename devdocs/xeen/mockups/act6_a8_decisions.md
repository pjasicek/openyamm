# DD-26 graph and A8's build notes: decisions (D-65)

Decider D-65, 2026-11-21. Where this answer and `mockups/act6_graphs/dd26.graph.yml`, `notes_dd26.md` or `act6_dungeon_graphs_a8.md` disagree, this answer wins. DD-26 can go to L1 now. DD-22's L1 is unblocked: DD-26's share is fixed at 18.76k, inside D-62's 13.0k–19.6k.

**APPROVAL**

- **DD-26 Olympus Sewer: approved with changes.** A8's default on every question except Q58, where the price changes.
  - **The plan stands.** It keeps one level of 10 rooms with the ring loop round Cyrano's den. It has 2 T6 chests (spillway, vault), the bed find (117806) and four drain pieces of lore (117801–117804). The tribble door sets 117805 and is kept open by a load event. The first room is quiet (D-11.3), and every dead end holds something.
  - **The way in.** The arrival is `entrance:d7_stair` at (0, 0, 0), facing north (512). It matches the name in D7's `project.yml` and L4 wiring (D-37). The way out uses the exit preset to D7's installed `entrance:dd26_stair` (−8704, 8192, 1808), facing 0. D-58's "both ways" holds.
  - **Map qbit block:** 117800–117839, after DD-22's 117760–117799.
  - **Change 1, the scroll.** The stair's line is on a pinned scroll. A shipped note or scroll decoration hangs by the wall, its hover is "Scroll" (aaze0038:10, the source's word next to :11) and its click shows "Search the drains." (:11). That also gives :10 its place in the ledger.
  - **Change 2, the tribble door's prompt.** The prompt's own text is the voice line (aaze0038:5). The event shows no message before it (see B1: the engine drops a choice's own text after a message).
  - **Change 3, walking room.** The fit audit must pass the Water Elemental's body on every walking line: 202 high, radius 100 (`monster_descriptors.txt` 11710). That means ceilings over the walkways of at least 320, and walking sides at least 256 wide. As in DD-21 (B2), the den's door, the two grates, the drains and the tribble door's landing all open onto dry walkways.
  - **Change 4, Cyrano's ids.** Cyrano's house and npc go in a **new `source/towns/dd26.yml` that shares D7's block**, as DD-25 shares D5's. They do not go in `d7.yml`: `house_data.txt` writes the map's own map_id per house (TOWNS_FORMAT), so a house listed under D7 would point at D7, not 9178. The proposed ids are 4815 and 5614, both unused today.

**General rules**
- **Quest XP.** No experience is added. Act VI quest XP is unchanged, and Q-D28 pays the pet, the vault and the bed.
- **Rows.** No new monster rows, no new bodies, no Meshy.
- **Textures.** None new. DD-26 uses about 20 of 30, and the world count is unchanged.
- **A1.** No new engine words: a text prompt, a one-way door by qbit, finds, a house door and a gold-checked topic (D-61's paid answers) all exist.

---

**DD-26 Olympus Sewer**

| # | DECISION | WHY | WHO ACTS | REVERSIBLE |
| --- | --- | --- | --- | --- |
| Q56 | **(a)** Lesser Water Elemental 55 (11625) × 16 and Water Elemental 62 (11710) × 4, placed by room as drawn. That is 18.76k per member (75,056 / 4); the DD-22 + DD-26 row is 35.96k against 33.5k (+7.3 %). | It is inside D-62's 13.0k–19.6k and the ±10 % row. Both rows exist, and so do their bodies (MM7's water elemental with S's tier skins, D-58). Both share one faction (`water_elementals`), so there is no infighting. "Sky-water in the gods' drains" fits the place. (b) puts two factions side by side, needs a hostility check and borrows DD-14's octopods. (c) invents a level-50 "Sewer Lord" for a family that ends at 35, with a new row and skin, to gain about 1.6k. The 62s guard the cistern and the vault. | A2: Act VI recount, and DD-26 added to the `where` of both families (`elementals` for 11625's tier F, `water_elementals` for 11710). | Cheap |
| Q57 | **(a), with the ids moved to a DD-26 file.** A walk-in den with Cyrano's counter as the house door:<br>- house 4815 "Pets Unlimited", kind residence, residents [5614], in a new `towns/dd26.yml` sharing D7's block 4801 / 5601;<br>- npc 5614 "Cyrano Jones", title "the Salesman" (aaze0038:13), `talks: true`, with a portrait;<br>- A8 names the counter's door at L1 (for example `door:pets_unlimited`);<br>- "Pets Unlimited" (:19) over the counter, and "Cyrano sells the password." (:12) on the den's map door. | It is the source's closed room with its bed, using DD-25's King's Hall pattern. It needs no actor row, no faction and no body. A residence shows his topics. The house must be in its own file because `house_data` takes the map's map_id. | A4: `towns/dd26.yml`, the npc, the portrait, and `towns.py` counting 1 residence for DD-26. A3: the topics (Q58). A8: the door and the counter. | Cheap until the ids are used (ids never renumber) |
| Q58 | **Changed: 25,000 gold** (neither 10,000 nor 100,000). The Tribble 12362 keeps its value of 5,000.<br>- **The sale** is an A3 topic in `q-d28.yml`: it asks, checks the gold, takes 25,000, gives 12362 and sets a Q-D28 qbit `bought`. It is repeatable.<br>- **"No", or too little gold,** gets "Maybe some other time." (:18).<br>- **After the first purchase,** a topic shows the TRIBBLES line (:15).<br>- **:14 is rescaled** to "only 25,000 gold" in ORIGINAL_LINES.<br>- **The pet does nothing else.** (c) is rejected. | D7 keeps the source's **10,000 gold tolls** (`npcs/d7.yml`, D-58). At 10,000 the "expensive pet" would cost one toll, and the joke would be lost. The source's 100,000 (ten tolls) is a heavy price for a hint the drains give free, and most parties would never see the item. 25,000 is 2.5 tolls and five times the item's value, so it clearly reads as expensive, yet stays affordable in Act VI. The merchant buys it back for less, so the sale is only a gold sink. (c) would make the purchase a way past the riddle, and the source does not do that. | A3: the topic, the qbit, :14 rescaled, the :15 and :18 rows. A2: a ledger line (a gold sink, no experience). | Cheap (a number) |
| Q59 | **(a)** The offering vault: the set piece, a T6 chest and the goal, guarded by 2 × 62 and 1 × 55. | The password needs a payoff, and the map needs a goal. (b) would leave the map with one chest and no set piece behind the riddle. | A8. A2: treasure count (2 T6 + 1 find). | Cheap |
| Q60 | **(a)** No experience. | QUESTS gives the pet as Q-D28's reward. It is an optional joke quest, and the vault's T6 chest and the bed pay for it. Act VI's quest-XP headroom is kept for its main lines (D-53/D-60: a later overrun goes to a decider). | — | Cheap |
| Q61 | **(a)** 10 % from `water_elementals` at **Dif 0**, weight 100: Water Elemental 62 only. | Dif 0 is 100/0/0, which matches a placed mix with no tier C (D-61's rule). Dif 1 and above can roll the Tidal Terror 70, over 48–65. The 55s are placed-only tier F of another family, so they never roll. The body fits every walking line under change 3 (D-57). | A2: map row 9178 (encounter 10, treasure 6). | Cheap |
| Q62 | **(a)** As A6 assigned: about 20 of 30, 0 new.<br>- MM7 d01's stone-channel face;<br>- the t3s2b / t3s2b1 marble shafts (stair, conduit walls, tribble-door surround);<br>- MM8 `gtempw1` / `gtempflr` in the vault;<br>- a shipped bronze two-leaf door. | It is distinct from XD-21, DD-21 and DD-01/18/20: DD-26 is the only marble sewer. A tribble relief is polish the map does not need. | A6: confirm the assign, and recount at install. | Cheap |

**A8's build notes (DD-21, DD-25)**

| # | DECISION | WHY | WHO ACTS | REVERSIBLE |
| --- | --- | --- | --- | --- |
| B1 | **Accepted.** DD-21's dais shows `q-d23.sandro`'s heart text over the Yes/No buttons, without "Give Sandro his heart?".<br>- **A rule for every lane:** when a hook's message comes before a choice, the engine drops the choice's own text, so the hook's text must end on the request.<br>- The heart text already does ("… Give it to me, and I will be free of this life.").<br>- The ritual question still shows, because no message comes before it.<br>- The heart-first playtest's header comment drops "and 'Give Sandro his heart?'" so that it says what the screen shows. | The line asks the same thing in Sandro's own voice. Appending a second question, or skipping the hook, would change approved A3 text for no gain. | A8: the playtest comment. A3: keep the heart text ending on the request. All map lanes: the rule (DD-26's tribble prompt, change 2). | Cheap |
| B2 | **Accepted.** DD-21's sewage channels run along one wall of each arm (north walls in the arms, outer walls in the culverts). Doorways, culvert mouths, the sluice room and the Box's niche are on dry walkways, and the sewage cannot be waded.<br>- The floor of 17.7 M units² against the graph's "about 11" is noted and accepted (S's cap is 20). | Every walking line stays on walkways, so the reach audit holds. The channel still reads as a sewer, which is what MM6's sewers do. | A8 (as built). DD-26's L1 follows the same pattern (change 3). | Cheap |
| B3 | **Accepted.** DD-25's King's Hall door (4704) stands on the dais south of the throne, in the west wall. This amends D-62 Q33's "behind the dais". | Straight behind the throne, the throne's back would hide the door. The audit shows the throne's hover and click and the door's click as separate targets. The empty throne still faces the hall. | A8 (as built). Orchestrator: note the amendment on D-62's row. | Cheap |
| B4 | **Accepted.** Striking one townsfolk turns all four Peasant Dwarves (MM7's peasant faction; they flee as Wimps), and the guards stay peaceful. Striking a gate guard turns only the two gate guards. The hostility playtest asserts exactly this. | Hostility spreads by actor group and faction (D-25: peaceful groups are their own rows and factions; D-62 Q34). It needs no relations entry and stays local. If guards defending townsfolk is wanted later, it is one `relations.yml` line (A2), not a map change. | A8 (as built). | Cheap |

---

**ROWS AND NUMBERS**

| Map | Monsters (counted) | Uncounted | Kill XP per member | Target | Rest | Chests | Textures |
| --- | --- | --- | --- | --- | --- | --- | --- |
| DD-26 (9178) | 20: Lesser Water Elemental 55 × 16, Water Elemental 62 × 4 | — (Cyrano is a house npc, not an actor) | **18.76k** | group DD-22 + 26 33.5k: **35.96k, +7.3 %** | `water_elementals` Dif 0, 10 % | 2 T6 + the bed find (and 4 lore drains) | about 20 of 30, 0 new |

- **Kill XP arithmetic** (L(L+10) per kill, over four): 16 × 3,575 + 4 × 4,464 = 75,056, so 18.76k. The rejected mixes came to (b) 17.01k and (c) 17.20k.
- **Act VI kill XP** was planned at 334.8k of 333.0k (1.01). DD-26 at 18.76k is about 2.5k over the row's centre, so Act VI moves by at most about +0.8 %. A2 recounts.
- **New rows:** none.
- **New ids:**
  - house 4815 "Pets Unlimited" and npc 5614 Cyrano Jones, in `towns/dd26.yml` on D7's block;
  - portrait `npc15614.png`.
- **Quest XP:** unchanged.
- **Gold:** the Tribble sells for 25,000 (repeatable). The item's value stays 5,000.
- **Map qbits:**
  - 117800 `dd26_arrived_once`;
  - 117801–117804 the drains;
  - 117805 the tribble door;
  - 117806 the bed;
  - 117807–117839 free.
- **Q-D28's `bought` qbit** comes from A3's quest block.
- **Permanent stats:** none.

**MAPS and QUESTS changes (orchestrator)**
- **MAPS §0 row DD-22, DD-26:** "40 (DD-22 20; DD-26 20, D-65)" and "33.5k (35.96k, +7.3 %: DD-22 17.20k, DD-26 18.76k, D-65)".
- **MAPS dungeon list, DD-26:** "A marble ring of channels round Cyrano's Pets Unlimited; the tribble door opens the offering vault".
- **QUESTS Q-D28:** "the whole word on Cyrano's own note" becomes "the whole word in Cyrano's patter to a tribble's owner (aaze0038:15); the Tribble sells for 25,000 (D-65)".

---

**RELAYS**

- **A1:** none.
- **A2:**
  - Act VI recount with DD-26 at 18.76k (row 35.96k, +7.3 %);
  - DD-26 added to `where` in `elementals` (11625) and `water_elementals` (11710);
  - map row 9178: `water_elementals` Dif 0, weight 100, encounter 10 %, treasure 6;
  - `maps.yml` monster text for DD-26;
  - ledger: the Tribble at 25,000 as a gold sink, no experience.
- **A3:** `source/quests/q-d28.yml`:
  - Cyrano's topics: the sale at 25,000 with `bought`, repeatable; "Maybe some other time." (:18) on No or short gold; the TRIBBLES line (:15) after `bought`;
  - the tribble door's prompt with :5 as its own text, accepting tribbles / tribble in any case (:6, :7), :8 wrong, :9 correct;
  - the drains (:1–:4 once, then :0);
  - the scroll (:10 hover, :11 click) and the bed (:16, :17);
  - "The tribble note" as an optional autonote of the four pieces;
  - register 117800–117839;
  - ORIGINAL_LINES rows for aaze0038:0–19 (:14 rescaled to 25,000);
  - the way up's meaning, "Climb up to Olympus?";
  - D7's grate question "Descend into the sewer?" (aaze0037:1) at DD-26's install.
- **A4:**
  - a new `source/towns/dd26.yml` (key DD-26, stem `xeen_dd26.blv`, blocks 4801–4850 / 5601–5700 shared with `d7.yml`);
  - house 4815 "Pets Unlimited", residence, residents [5614], with the door A8 names;
  - npc 5614 Cyrano Jones, "the Salesman", `talks: true`, a greeting, and the portrait `npc15614.png`;
  - `towns.py`: 1 residence for DD-26.
- **A5:** none.
- **A6:**
  - At DD-26's install, D7's `evt:sewer_grate` drops "The grate is fast in its frame." It asks "Descend into the sewer?" and moves to `xeen_dd26.blv` `entrance:d7_stair`.
  - Confirm d01's face and the t3s2 marble shafts, and recount (0 new).
- **A7:** none.
- **A8:**
  - DD-26's L1 from the graph plus this answer: the scroll (change 1), the prompt without a message before it (change 2), the walking room and dry walkways (change 3), Cyrano's counter door named for A4's house.
  - Playtests: the password wrong then right, with a reload (117805 keeps the door open); each drain once; the bed once; buying the tribble with and without 25,000 gold; the TRIBBLES line after `bought`; the exit to D7 and back.
  - DD-22's L1 with D-62's drive-room find.
  - DD-21's heart-first playtest comment (B1).
  - B2–B4 stand as built.
- **S:** nothing. The water elemental bindings already exist.
- **AU:** optional tribble purring in the den; otherwise shipped water beds and drips.
- **Orchestrator:**
  - the MAPS and QUESTS changes above;
  - the DECISIONS row;
  - D-62's Q33 amended ("on the dais, south of the throne", D-65 B3);
  - STATUS: DD-26 to L1, and DD-22's L1 unblocked.

---

**SUMMARY ROW**

| D-65 | 2026-11-21 | A8's DD-26 graph and build notes | DD-26 approved: 20 water elementals (55 × 16, 62 × 4) 18.76k, row 35.96k (+7.3 %); Cyrano a residence in a new `towns/dd26.yml` (4815/5614, D7's block); Tribble 25,000 gold (D7 tolls are 10,000); vault behind the tribble door; no XP; rests Dif 0; 0 new textures; "Scroll" hover (:10). B1–B4 accepted (hook text must end on the choice). DD-22 L1 unblocked. Detail: `mockups/act6_a8_decisions.md` | A2, A3, A4, A6, A8, orchestrator |
