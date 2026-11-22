# Phase 5, lane A8's graphs DD-25, DD-21, DD-10C, DD-22: decisions (D-62)

> Orchestrator note (2026-11-21): Q33's King's Hall door stands on the dais, south of the throne (D-65 B3, `act6_a8_decisions.md`).

Decider D-62, 2026-11-21. Where this answer and the graphs in `act5_graphs/` (`dd25`, `dd21`, `dd10c`, `dd22`) or `act5_dungeon_graphs_a8b.md` disagree, this answer wins. DD-25, DD-21 and DD-10C can go to L1 (or, for DD-10C, to phase-5 completion) now. DD-22's L1 waits for DD-26's graph in phase 6.

**APPROVAL**

- **DD-25 Bosco's Hall: approved with changes.** A8's default on every question. Q34 keeps (a) but uses different rows.
  - **Guards.** The four guards use a new Xeen row, **11054 "Bosco's Guard"**, in the mad dwarves block. It is peaceful, has its own faction, is placed only, has NoArena and is not counted. It uses the `xeen_dwa1` body with a new S recolour. They do not use the engine's Dwarven Soldier row: that row is MM7 data, and `balance.py` would count it as hostile.
  - **Townsfolk.** The four townsfolk use MM7's Peasant Dwarf rows (313–330). S binds two male and two female looks in Xeen's `actors.yml` to the shipped MM7 bodies. Xeen already points at `worlds/mm6` and `worlds/mm7` models. `balance.py` already treats these rows as townsfolk by their name.
  - **Bosco's later greeting** is a `greet_after` (TOWNS_FORMAT has it, see Q36), not a topic text.
  - **The empty throne** gets a hover and a line (Q33).
  - **`towns.py`** takes 3 residences for DD-25: WORLD_DESIGN's 2 plus the King's Hall.
- **DD-21 Necropolis Sewer: approved with changes.** A8's default except Q47.
  - **Cinder Roach (Q42).** It is a placed-only tier D. Rests never roll tier D (D-61 Q10), so the reason "ordinary so that rests can draw it" falls away. Its body is the installed `xeen_mantis.glb` (the Lava Roach's), with a new recolour of `mantis_lava`. It needs no new mesh and no Meshy.
  - **Risen Sandro (Q41).** He is row **11926**. His show/hide is keyed on a new map qbit, **117727 `sandro_fell`**, not on `q-d23.beaten`: a party that already carries the heart at the first fall never sets `beaten`. The fall event hides the fallen body's group as it shows the risen one.
  - **Dead Food roaches (Q43).** They are shown once by the pry. No load event shows them again: per D-18, a looted corpse is a dead invisible actor, and the map state keeps them shown.
  - **Rest encounters (Q47).** They come from the pyramid mummies at Dif 0. Neither proposed slot can roll an in-band tier.
  - **A3's texts.** The heart state of the `sandro` hook must also read right at a first fall. ORIGINAL_LINES' Luna row loses aaze0035:29 to DD-21.
- **DD-10C Gemstone Mines, north pocket: approved with changes.** A8's default, with Q50 at Dif 0.
  - **Map card.** gen.py's provisional slots go: eyes Dif 5 w60, robots Dif 5 w40 and encounter 0. Dif 5 rolls the Gamma Gazer 65 and the Autobot 75, both over 40–50. The card becomes one slot, eyes Dif 0 w100, with encounter 10 %. The Patrols are placed by row id only.
  - **The Act V update** is otherwise as drawn. The layout is unchanged (D-27).
- **DD-22 Sheltem's Pod: approved with changes.** A8's default on every question.
  - **The drive room is a dead end with nothing in it**, which breaks the dead-end rule. It gets a find: one random T6 item in the stasis generator's tool rack, map qbit 117762, then "Nothing here.".
  - **L1 timing.** L1 follows DD-26's graph (phase 6). DD-26 must land 20 monsters at **13.0k–19.6k** so that the DD-22 + DD-26 row stays within ±10 % of 33.5k.

**General rules for all four**
- **No experience is added.** Act V quest XP stays at 231.5k on the counted route (1.11) and 239.5k on the most-experience line (1.146). DD-22's log pays no experience (Q54).
- **Permanent stats.** The Dead Food adds +2 Endurance per character. Act V comes to about +27 per character, against Act IV's +45.
- **Rest encounters.** 10 % from one hostile, in-band slot per map, at the Dif whose share of tier C is closest to the placed mix (D-61). Tier D never rolls. DD-25 has none (encounter 0, no hostile row).
- **Textures.** 2 new in all: `xdbosban` and `xdsandro`. The world comes to about 198 of 450. A6 recounts.
- **A1.** No new engine words and no confirmations. Q41 (a) uses words that exist: `show_actors`/`hide_actors`, a timer with a `kills` condition, and a timer showing a hidden actor (A1 confirmed this under D-47).

---

**DD-25 Bosco's Hall**

| # | DECISION | WHY | WHO ACTS | REVERSIBLE |
| --- | --- | --- | --- | --- |
| Q32 | **(a)** About 12 sectors and 9.9 M units², 8 doors, one loop, a walk-in throne hall, and the Deep Guild one stair down. | It is inside S's figures and under the shipped measure, Stone City's quarter (18 doors in 14 M). It has a loop. WORLD_DESIGN's 3 services and 2 residences win over TOWN_FEEL's ranges, and the gaps go into "Town feel exceptions" lines. | A8: L1 and the NOTES exception lines. A4: `towns.py` takes 3 residences. | Cheap |
| Q33 | **(a)** A walk-in throne hall with `door:kings_hall` (4704) behind the dais. The throne stays empty.<br>- The throne's hover is "Bosco's throne".<br>- Its click line (A3): "The King's throne, empty. He takes his meals in his chambers, where the cups can be watched." | It is Stone City's pattern. The empty throne tells his story: a king afraid of poison who keeps to his rooms. (c) adds a row and a body for a figure who would say what his house screen says. | A8. A3: one map-local line. | Cheap |
| Q34 | **(a), changed rows.** Eight peaceful dwarves, uncounted:<br>- four guards on the new row 11054 "Bosco's Guard" (faction `xeen_bosco_hall`, friendly; placed only; NoArena; not counted; `xeen_dwa1` with an S recolour);<br>- four townsfolk on MM7's Peasant Dwarf rows.<br>None stands on a walking line, and the 384 and 256 clearances apply. | D-25: peaceful groups are their own rows and factions. Dwarven Soldier is MM7 data, and `balance.py` would count it as hostile (its name is not a townsfolk name). The peasant rows already count as townsfolk by name. | A2: row 11054, its faction, and a recount check that DD-25 stays at 0. S: the guard recolour and four Peasant Dwarf bindings for Xeen. A8: placement. | Cheap |
| Q35 | **(a)** 7d24's town quarter, about 24 of 30, plus 1 new (`xdbosban`). | It is the MM dwarf city, and no Xeen map uses its house fronts. `d41` is MM8's hostile Dark Dwarves and would mean two sources. 6d09 is XD-02's. | A6: a `dungeon_families.yml` line, and register `xdbosban`. | Cheap |
| Q36 | **(a)** through TOWNS_FORMAT's `greet_after`: Bosco (5401) after `q-d17.done` greets with "Ah, the taste testers! Please, please, sit down and drink with me for awhile! My halls will always be open to you." The later greeting is "My halls will always be open to you." | The format already has greetings by qbit (Roland's 4406). It is the source's line in its own place. | A4: `greet_after` with a free greeting id from 5407–5500. A3: Q-D17's done step calls `evt.SetNPCGreeting`, plus an ORIGINAL_LINES row for aaze0013:17. | Cheap |
| Q37 | **(a)** A shipped goblet decoration on the tasting table, shown by the load event from 113343. | It is a visible payoff at no cost. | A8 | Cheap |
| Q38 | **(a)** No change in the map. His topic says "Get out." | MM6–MM8 residences do not lock, and the services must stay open. | — | Cheap |
| Q39 | **(a)** A plain well with A3's line. | D5 already has two boons. The Act V stat budget stays small. | A3: the line. A8. | Cheap |

**DD-21 Necropolis Sewer**

| # | DECISION | WHY | WHO ACTS | REVERSIBLE |
| --- | --- | --- | --- | --- |
| Q40 | **(a)** 15 + Sandro: Cinder Roach 40 × 10, Greater Lich 50 × 3, Ghost Mummy 62 × 2, and Sandro 65 once. That is 10.70k per member; the group comes to 41.84k (+5.7 %). | It is inside D-61's 4.5k–12.4k. It meets S's floor of 15, which (c) would miss at 13. It keeps the source's roaches and the mummy's treasure. | A2: recount. | Cheap |
| Q41 | **(a), with changes.**<br>- **The fight.** The hostile Sandro (11283) is fought once. A timer with a `kills` condition on his group does four things: sets 117727, calls `q-d23.sandro`, shows the risen Sandro's group and hides the fallen body's group.<br>- **The risen Sandro.** He is row **11926 "Sandro"**: peaceful, placed only, immobile, NoArena, not counted, with 11283's look. He starts hidden.<br>- **The load event** shows him while 117727 is set and `released` is clear, and hides him once `released` is set. It also makes him unkillable, as DD-15's Pharaoh is.<br>- **The release** plays a shipped dust effect, then hides him.<br>- **Talking.** He talks through the dais plate and the bier's click. | Only existing words. (b) costs Sandro's kill XP and two A1 confirmations, and (c) needs a new word. Keying on 117727 covers a party that brings the heart before the fight. | A2: row 11926. A3: trims the `beaten` text to a single fight ("…you have beaten me once, and it changed nothing. Bring the heart."). The heart state reads right at a first fall: drop "slower this time", or keep it only when `beaten` is set. The hook `where`s become "shown/hidden by the map". A8: the events, with playtests for the heart before and after the fight and a reload. | Cheap |
| Q42 | **(a), corrected.** **11363 Cinder Roach**: giant crawlers tier D, level 40, Fire, look C, placed only (it never rolls in rests). Its body is `xeen_mantis.glb` with a new ash recolour of `mantis_lava`. | The source's roach is level 40. The Lava Roach 26 is 14 under the band. Vampires (c) belong to Nightshadow and Blackfang and would lose the barrel. The roach body is already installed. | A2: the row, and DD-21 added to `where`. S: the skin and binding, with no mesh and no Meshy. | Cheap |
| Q43 | **(a)** The barrel needs Might ≥ 30 (D-4's rule), else aaze0036:7.<br>- Two hidden roaches (counted in the 10) are shown once at the pry (117723), with no re-show on load.<br>- Then it is eaten once per character: +2 Endurance to every member present (a player bit). | Quest XP is closed, so the source's +1 level becomes a stat. A barrel that bites back matches the source. | A3: the bit and text, aaze0036:7–9 rescaled. A2: the ledger. A8: a reload playtest. | Cheap |
| Q44 | **(a)** The sluice wheel opens the culvert gate (one way, D-43). Each answers the other's click. | It is a lever-and-gate pair with its answer in both places. | A3: two lines. A8. AU: the shipped grind. | Cheap |
| Q45 | **(a)** The grille opens with the release: a T5 chest. The statuette is dressing, and aaze0035:29 is said at the grille before the release. | The source's statuette was Luna's Griffin, which is DD-07's here. A takeable statuette would duplicate Q-D20's. | A3: the line, and ORIGINAL_LINES' Luna row drops aaze0035:29 (now DD-21's). | Cheap |
| Q46 | **(a)** Two Ghost Mummies 62 (11273, placed only). | They are inside the band and guard the source's "Mummy's Secret Treasure". | A2: DD-21 added to `where`. | Cheap |
| Q47 | **Changed:** 10 % from the pyramid mummies at **Dif 0** (Tomb Mummy 42 only). | The crawler slot rolls tiers A–C (16/20/26). Liches at Dif 0 roll Lich 35, under the band, and Dif 1 and above can roll the Lich Lord 65, over it (D-4). The mummies are in the map (the vault), and Dif 0 matches a placed mix with no tier C. Tomb Mummies fit every room (D-57). | A2: row 9174, and the mummies' `where`. | Cheap |

**DD-10C Gemstone Mines, north pocket**

| # | DECISION | WHY | WHO ACTS | REVERSIBLE |
| --- | --- | --- | --- | --- |
| Q48 | **(a)** gen.py gains slot `'c'` for the two `'b'` spots in the lava gallery and the collapse.<br>- `PHASE5_ROWS = {'a': 11570, 'b': 11571, 'c': 11610}`.<br>- That is 14 / 4 / 2, 11.50k (0.0 %). | MAPS §0 names all three families, and D-27 asks for D6's own. The Patrols hold the drifts nearest the adit. | A8: gen.py. A2: recount. | Cheap |
| Q49 | **(a)** The cold nest, with its line and hover. The ash glow turns cold. | The built egg cases get a story without the roaches D-27 removed. | A3: one map-local line, and Hector's D-27 line if missing. A8. | Cheap |
| Q50 | **(a) at Dif 0:** 10 %, Floating Eye only. The map card has one slot (eyes Dif 0 w100) and encounter 10. | Dif 1 and above can roll the Gamma Gazer 65, over 40–50 (D-47 Q21). A robot slot at any Dif can roll the Autobot 75. | A8: the map card. A2: row 9161. | Cheap |

**DD-22 Sheltem's Pod**

| # | DECISION | WHY | WHO ACTS | REVERSIBLE |
| --- | --- | --- | --- | --- |
| Q51 | **(a)** 20 robots: Patrol × 14 and Annihilator × 6, 17.20k. DD-26 takes 20 at 13.0k–19.6k. | S's floor is 15. (c) would push DD-26 to 33, past S's 30. MAPS gives DD-22 no "few". | A2: Act VI recount. A8: DD-26's graph to that range. | Cheap until DD-26's graph |
| Q52 | **(a)** It opens once `m33.done`; before that, the sealed line. | An Act V party cannot walk into Act VI's robots, and the log reads as an epitaph. | A3: `d6.sheltem_hatch` requires `m33.done`; the opening text moves the party to `entrance:d6_hatch`; the present text becomes its fail text. A6: D6's door at DD-22's install. | Cheap |
| Q53 | **(a)** The devices are dressing with aaze0088:0. **Plus the drive room's find** (APPROVAL, 117762). | DD-16's device is the pods' one (D-47 Q18). The dead-end rule needs the find. | A8. A3: the line for the find. | Cheap |
| Q54 | **(a)** About six pages ("Entry N of 6", wrapping). The last page sets the autonote "Sheltem's log". | It follows D-47 Q19's pattern. Lore, not experience. | A3: the pages as ORIGINAL_LINES rows (aaze0088:4, :7–17), and the autonote id. A8: the paging variable. | Cheap |
| Q55 | **(a) at Dif 0:** 10 %, Patrol only. | Dif 1 and above can roll the Autobot 75, over 48–65. None is placed. | A2: row 9175 | Cheap |

---

**ROWS AND NUMBERS**

| Map | Monsters (counted) | Uncounted | Kill XP per member | Target | Rest | Chests | Textures |
| --- | --- | --- | --- | --- | --- | --- | --- |
| DD-25 (9122) | 0 | Bosco's Guard 11054 × 4, Peasant Dwarf × 4 | 0 | — | none (encounter 0) | 0 | about 24 of 30, 1 new (`xdbosban`) |
| DD-21 (9174) | 15: Cinder Roach 40 × 10 (2 hidden), Greater Lich 50 × 3, Ghost Mummy 62 × 2; Sandro 65 once | risen Sandro 11926 | **10.70k** (9.48k + Sandro 1.22k) | group DD-08 + 21 39.6k: **41.84k, +5.7 %** | Tomb Mummy Dif 0, 10 % | 3 T5, 3 drain finds, Dead Food | about 24 of 30, 1 new (`xdsandro`) |
| DD-10C (9161) | 20: Floating Eye 40 × 14, Terrible Eye 50 × 4, Patrol 50 × 2 | — | **11.50k** | 11.5k, 0.0 % | Floating Eye Dif 0, 10 % | 1 T5 | 16, 0 new |
| DD-22 (9175) | 20: Patrol 50 × 14, Annihilator 62 × 6 | — | **17.20k** | group DD-22 + 26 33.5k: DD-26 13.0k–19.6k | Patrol Dif 0, 10 % | 3 T6 + 1 find | about 18, 0 new |

- **Kill XP arithmetic** (L(L+10) per kill, per member over four):
  - DD-21: 10 × 2,000 + 3 × 3,000 + 2 × 4,464 + 4,875 = 42,803, so 10.70k.
  - DD-10C: 14 × 2,000 + 6 × 3,000 = 46,000, so 11.50k.
  - DD-22: 14 × 3,000 + 6 × 4,464 = 68,784, so 17.20k.
- **New rows:**
  - 11054 Bosco's Guard;
  - 11363 Cinder Roach;
  - 11926 risen Sandro.
- **Quest XP:** unchanged. Counted route 231.5k (1.11), most experience 239.5k (1.146).
- **Permanent stats:** DD-21's Dead Food +2 Endurance. Act V comes to about +27 per character.
- **Map qbits:**
  - DD-25: 117680.
  - DD-21: 117720–117727, with 117727 `sandro_fell` new and 117728 unused.
  - DD-22: 117760–117762.
  - DD-10C: 117240 unchanged.

**MAPS changes (orchestrator)**
- **§0 rows:**
  - DD-08, DD-21: "60 + Sandro (DD-08 45; DD-21 15 + Sandro, D-62)" and "39.6k (41.84k, +5.7 %: DD-08 31.14k, DD-21 10.70k, D-62)".
  - DD-10C: "11.5k (11.50k, 0.0 %, D-62)".
  - DD-22, DD-26: "40 (DD-22 20; DD-26 20 planned, D-62)" and "33.5k (DD-22 17.20k; DD-26 13.0–19.6k, D-62)".
- **Dungeon list:**
  - DD-21: "Sandro's heart in a green jar in the lowest culvert; Sandro falls once and waits, risen, by his bier".
  - DD-22: "The other ship's log (six pages); opens after M33".
  - DD-25: "A walk-in throne hall; forge, alehall, Earth guild and three residences".

---

**RELAYS**

- **A1:** none. Q41 (a) uses existing words (`show_actors`/`hide_actors`, a `kills` timer, the unkillable figure as DD-15's Pharaoh).
- **A2:**
  - rows 11054 (faction `xeen_bosco_hall`), 11363 and 11926;
  - `where`: DD-21 for the liches, the pyramid mummies and the crawlers;
  - map rows: 9174 mummies Dif 0, 10 %; 9161 eyes Dif 0, 10 %, party 48–51, treasure 5; 9175 robots Dif 0, 10 %; 9122 encounter 0;
  - `maps.yml` monster texts for DD-21 and DD-22;
  - ledger +2 Endurance;
  - recount: DD-21 10.70k, DD-10C 11.50k, DD-22 17.20k, DD-25 0, checking that the peasants and 11054 stay out of the count.
- **A3:**
  - **DD-25:**
    - register block 117680–117719;
    - the arrival, well and throne lines;
    - `SetNPCGreeting` in Q-D17's done step;
    - ORIGINAL_LINES rows for aaze0013:13–17.
  - **DD-21:**
    - Q-D23's `beaten` and heart texts and hook `where`s (Q41);
    - the first-entry, sluice, grille (aaze0035:29), exit-meaning and Dead Food lines;
    - the Dead Food player bit;
    - drop aaze0035:29 from Luna's row;
    - register 117720–117727.
  - **DD-10C:** the cold nest's line, and Hector's D-27 line if missing.
  - **DD-22:**
    - `d6.sheltem_hatch` gated on `m33.done`;
    - six log pages and the autonote;
    - the console, blast-door and drive-room find lines;
    - register 117760–117762.
- **A4:** Bosco's `greet_after` from `q-d17.done` (aaze0013:17), with a free id from 5407–5500. `towns.py` counts 3 residences for DD-25.
- **A5:** none.
- **A6:**
  - D5's `door:dd25` gets `into: {map: xeen_dd25.blv, arrival: entrance:d5_bosco}`, and the sealed message goes.
  - D6's crypt door optionally asks "Descend to the sewer?" (aaze0035:17).
  - Confirm `entrance:dd10c_adit`'s height (the sidecar's 2688 stands unless A6 says otherwise), and name `entrance:d6_adit` on `door:dd10c` at install.
  - Name `entrance:d6_hatch` on `door:dd22` and drop `listed_only` at DD-22's install.
  - Register `xdbosban` and `xdsandro`, add DD-25's 7d24 quarter to `dungeon_families.yml`, confirm the sewer.blv, 6d14 and red-accent pod assignments, and recount the world (about 198).
- **A7:** none.
- **A8:**
  - L1 for DD-25 and DD-21 from their graphs plus this answer.
  - DD-10C's phase-5 steps: the `'c'` slot, `PHASE5_ROWS`, the map card's single eye slot at Dif 0 with encounter 10, `D6_LIVE`, `D6_ARRIVAL`, playtests, install, bake.
  - DD-26's graph at 20 monsters and 13.0k–19.6k, then DD-22's L1 with the drive-room find.
  - Playtests:
    - DD-21: the heart before and after the fight, with a reload; the Dead Food reveal and a reload; the sluice; the release, then the grille.
    - DD-25: the goblet after `done`.
- **S:**
  - the Cinder Roach recolour of `mantis_lava` on `xeen_mantis`, and its binding;
  - 11926 on 11283's look;
  - 11054's recolour on `xeen_dwa1`;
  - four Peasant Dwarf bindings for Xeen (shipped MM7 bodies);
  - the heart jar: a shipped jar or urn with a green light;
  - no Meshy.
- **AU:** optional distant hammering for DD-25; optional heartbeat loop at the jar in DD-21; nothing new for DD-22.
- **Orchestrator:** the MAPS changes above, the DECISIONS row, and in STATUS: DD-25, DD-21 and DD-10C are unblocked, DD-22 waits for DD-26's graph.

---

**SUMMARY ROW**

| D-62 | 2026-11-21 | A8's graphs DD-25, DD-21, DD-10C, DD-22 | All four approved with changes; A8's default except DD-21 Q47 and DD-10C Q50. DD-25: walk-in throne hall, eight peaceful dwarves (guards row 11054, MM7 peasant dwarves), Bosco's `greet_after` from aaze0013:17, goblet on show. DD-21: 15 + Sandro, 10.70k (group 41.84k, +5.7 %); Cinder Roach 11363 (placed-only tier D on `xeen_mantis`); Sandro falls once, risen row 11926 keyed on 117727; Dead Food +2 Endurance; rests Tomb Mummy Dif 0. DD-10C: a third gen.py slot, 11.50k, eyes Dif 0. DD-22: 20 robots, 17.20k (DD-26 13.0–19.6k), opens after M33, a drive-room find, Patrol Dif 0. No quest XP; 2 new textures. Detail: `mockups/act5_a8_decisions_b.md` | A2, A3, A4, A6, A8, S, AU, orchestrator |
