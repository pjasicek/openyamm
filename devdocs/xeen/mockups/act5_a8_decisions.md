# Phase 5, lane A8's graphs DD-15, DD-17, DD-08: decisions (D-61)

Decider D-61, 2026-11-21. Where this answer and the graphs in `act5_graphs/` (`dd15`, `dd17`, `dd08`) or `act5_dungeon_graphs_a8.md` disagree, this answer wins. DD-15 can go to L1 now, so segment 69 can follow its build.

**APPROVAL**

- **DD-15 Great Pyramid: approved with changes.** A8's default on every question except Q6, which takes (b).
  - **Scarab cell.** It is a dead end that holds only a guard post, which breaks the dead-end rule.
    - The weapon rack gets a find: one random T5 weapon, map qbit 117578, then "Nothing here.".
  - **Pad count.** The pad hall has four pads: sun, eye, scarab and bird. The bird cell's second pad makes five, and every cell has a pad back. Correct "five glyph pads in the floor" at L1.
  - **The Pharaoh's lift** wakes on the party's first entry into the throne hall (map qbit 117577), not on `m28.done` (Q4).
    - Before that: "A gilded cage. It answers only to the Pharaoh's guests."
  - **Rest encounters** are at Dif 2 (Q10). Drop "none in the Pharaoh's rooms": the engine has no exclusion per room, and the Pharaoh cannot be killed.
  - **The Pharaoh** is S's installed P5 figure (D-56), not the Lizardman stand-in.
  - **Ids.** 11919 with `monsters[].npc: 5453`. It is made unkillable on load, as P5 does.
- **DD-17 Castle Alamar: approved with changes.** A8's default except:
  - Q14: (a) while the castle stands, then (b) after `m33.done`;
  - Q19: (b);
  - Q21: Dif 2.

  The changes:
  - **A dial at nine says so in the alcove.** The slabs cannot be seen from there.
    - The slab's grind plays, and the status line reads "The dial clicks home at nine. Somewhere below, stone grinds level.".
    - Leaving nine: "Somewhere below, stone drops away.".
  - **Map reset.**
    - `Xeen.alamarSundialsSync()` rewrites 117611–117614 and 111663 from the dial variables.
    - DD-17's load event calls it before the stages for the slabs and the fields.
  - **The hatch arrival calls its own `m33.roof_arrival`.**
    - It has the same requires and sets as `m33.arrival`, and its own fail text.
    - A refusal moves the party back to D7's `entrance:dd17_roof`.
    - The refusal voice plays once (`refused_once`).
  - **Doors.** The four bridge slabs are mechanisms and do not count against the doors (24).
  - **Free ids.** The characters block (11900–11999) is not full: the last row is Alister 11923. Sheltem takes **11924**.
- **DD-08 Northern Tower: approved with changes.** A8's default except:
  - Q25: (c);
  - Q27: (b);
  - Q28: (a), with a narrower faction;
  - Q31: Dif 0.

  The changes:
  - **Faction split** by A2 (see Q28): only the Slayer and Death Knights turn friendly. FD-04's Doom Knights stay hostile.
  - **The four oath figures** are row **11925**, "Voweless Knight", on the Slayer Knight's look. No new skin.
  - **Oath text (A3).** "You set the Chalice back on its stand" becomes "You set the Chalice before the plaque". The plaque is in the chapter hall, not the chalice room.
  - **Ormond's compilation** is an A4 topic, not an item (see "+" under DD-08).

**General rules for all three**
- **No experience is added.**
  - Act V quest XP stays at 231.5k on the counted route (1.11) and 239.5k on the most-experience line (1.146).
  - That line has 0.85k left under 1.15, so the books and the juice pay in permanent stats.
- **Permanent stats.**
  - These maps add +16 per character: the books +7 (one per stat), Euphoria +7 and the juice +2 Might.
  - Act V comes to about +25 per character, against Act IV's +45.
- **Rest encounters.**
  - 10 % from one hostile, in-band slot per map.
  - The Dif is the one whose share of tier C is closest to the placed mix (`balance.py` DIF_MIX: Dif 0 is 100/0/0, Dif 2 is 70/20/10).
  - All three slots fit their rooms (D-57).
- **Textures.**
  - 8 new in all: DD-15 1, DD-17 5, DD-08 2. Each map is inside its per-map limit (L ≤ 14, M ≤ 8).
  - The world comes to about 196 of 450. A6 recounts.
- **A1.** No new engine words. DD-17 only needs the four confirmations in RELAYS.

---

**DD-15 Great Pyramid**

| # | DECISION | WHY | WHO ACTS | REVERSIBLE |
| --- | --- | --- | --- | --- |
| Q1 | **(a)** 70 Pyramid mummies: Tomb 34, Guard 24, Ghost 6, Royal 6. 51.92k (+3.0 %). | It is inside the band and within ±10 %. The Cloud Dragons are over the band, Act VI's family, and not part of the pyramid's story. (c) adds 7 % for nothing. | A2: recount | Cheap |
| Q2 | **(a)** Four torches, each with two hidden Tomb Mummies in its chapel, shown by the lever.<br>- They stay shown and hostile after a reload (D-18). They are counted in the 70.<br>- The levers are one-way ("The lever is stuck.", D-43). | It matches A3's "fourth torch". The source's levers bring monsters too. Each torch has a visible effect: its brazier and the wake. | A8: events, and a playtest (light one, reload, the pair is still there; the fourth opens the stair door). AU: the ignition. | Cheap |
| Q3 | **(a)** Optional: it opens the Overseer's vault. | M28's "number lock" is the registry (A3's reading). The answer-givers are in the same room and the office. On the path it would stack two riddles before the stair. | A3: map-local lines (the niches, the rule statues, the note). A8. | Cheap |
| Q4 | **(a), changed:** the lift runs both ways after the first entry into the throne hall (117577). | M30, M33's Lord Xeen topic and M36 bring the party back three times. The bottom stop is behind the torch door, so the lift skips nothing the party has not done. Gating on the audience instead of `m28.done` also covers a party that climbed without the orb ("Bring it."). | A8: the lift and the qbit. A3: the cage's line. | Cheap |
| Q5 | **(a)** The wardens stay hostile. | They are the source's mindless wardens, and the lift carries return visits past any refill. A peaceful turn would add a faction rule for nothing. | — | Cheap |
| Q6 | **(b)** The first click gives the Pharaoh's warning (aaze0086:0).<br>- A second click in the same visit (a map variable) drinks: 50 Fire damage to the clicking member, "He did warn you.".<br>- No reward. | The joke gets a visible, harmless payoff and touches no ledger. | A3: two lines. A8: the event. AU: the bubbling, and a hiss on a drink. | Cheap |
| Q7 | **(a)** The safe's three prompts, 20-30-1. The tapestry shows the numbers. T5 chest. | It finishes the source's unfinished safe, with its answer in the same room. | A3: the tapestry and safe lines (aaze0086:19–29). A8. | Cheap |
| Q8 | **(a)** The source's three directives (aaze0086:30) without the +1,000,000. A second read gives aaze0086:31. | MAPS names this book as DD-15's original line. The directives also frame Sheltem as a guardian who stopped obeying. | A3: `m28.prime_directive` text, ORIGINAL_LINES. | Cheap |
| Q9 | **(a)** Behind the throne on L4. | The source's L4 button leads to the Skyroads, and D-58 wants the door both ways after M30. A pad on L3 would land D7 arrivals in the maze. The inside height is independent of the outside (D-49 Q6). | A6: D7's `entrance:dd15_sky`. A8: the sealed line until D7 installs. | Cheap |
| Q10 | **(a) at Dif 2:** 10 %, Tomb 70 / Guard 20 / Royal 10. | All three tiers are inside 42–65, and the Ghost Mummy (tier D) is never rolled. Dif 2's 10 % Royal matches the 9 % placed. | A2: row 9168 | Cheap |
| + | The scarab cell's find (117578). Four pads in the hall. The Pharaoh is S's P5 figure. | The dead-end rule, the graph's own count, and D-56. | A8, S | Cheap |

**DD-17 Castle Alamar**

| # | DECISION | WHY | WHO ACTS | REVERSIBLE |
| --- | --- | --- | --- | --- |
| Q11 | **(a)** Plate rides, with "The floor lurches and carries you along." and the rumble. The bolted Head-side doors close the loops. | Existing words only. It keeps the source's one-way carry into each Head's room. (b) means dozens of camera snaps; (c) is new engine work for four rooms. | A1: confirm an in-map move from a step plate keeps the facing given. A8. AU. | Cheap (plates can give way to (c) later) |
| Q12 | **(a)** Four `xafield` leaves over the sundials, each dropped by its Head (one-way, D-43). | It ties L1 to L2, the Heads' own lines name their fields, and nothing needs undoing. (c) needs A1. | A3: "Shut the field down?" and "The Head goes dark. Somewhere above, a field dies." A8. | Cheap |
| Q13 | **(a)** One two-state slab per ring, level only while its dial reads nine. Plus the line and grind at nine (APPROVAL). | The puzzle can be seen in the hall. Two states are right, because turning a dial off nine does something (D-43). | A3: the helper's bits 117611–117614, the sync, the lines. A1: confirm a horizontal slab can be a two-state door. A8. | Cheap |
| Q14 | **Before `m33.done`, (a):** DD-17 can be entered, and the hatch works both ways once unlocked. Its arrival calls `m33.roof_arrival`.<br>**After `m33.done`, (b):** D7's hatch leads both ways into **FD-01 Alamar Depths** (its own `entrance:d7_roof`, a shaft through the rubble), built at FD-01's L1 in phase 6.<br>Until FD-01 installs, D7's hatch after `m33.done` reads "Below the hatch: smoke, and a long fall onto rubble. Castle Alamar is gone."<br>**D-58 D-5 is amended accordingly.** | Q-D26 (level 60) comes after M33 (level 53) for nearly every party. Under (a) alone, the Megadragon's key would open a door into nothing. FD-01 is the castle's depths at 58–61, so the hatch becomes the shortcut Q-D26 promises. (c) would put a second state on an L map for one corridor. | A3: `q-d26.hatch` takes its target and text from `m33.done`; the new `m33.roof_arrival`. A6: D7's hatch exit by `m33.done`. A8: DD-17's hatch now, and FD-01's L1 in phase 6. Orchestrator: the D-58 note and the MAPS FD-01 row. | Cheap now; FD-01's spot is settled at its L1 |
| Q15 | **(a)** Row **11924 "Sheltem"**: peaceful, placed only, unkillable, immobile, not counted, hidden until the cinematic shows him. Corak 11912 is placed hidden. | D-38's voiced lines need a figure to look at. This is D-47's pattern. (c) contradicts M33, where Corak does the fighting. | A2: the row. S: the look. A1: the cinematic shows hidden actors (D-47's item). | Cheap |
| Q16 | **(a)** The dais plate asks "Before the throne. Open the Soul Box?" first. | As D-47's scepter: the castle is gone afterwards, so the strongroom and the chests must stay reachable. | A3: `m33.sheltem` `where` and the question. A8. | Cheap |
| Q17 | **(a)** D6's `entrance:dd17_gate`. | No D6 change. It is the same point as the refusal and FD-01's stair. | A1: a leave after `evt.PlayCinematic` (shared with XD-19, D-47). A8. | Cheap |
| Q18 | **(a)** Six hatched trapdoor plates (`trap`) drop 1,280 to the sump. The first has a hover. | The seams are the answer. A fall costs hit points and a climb, not progress. | A1: confirm a `trap` lift can drop through two floors of open air. A8. AU: the clang. | Cheap |
| Q19 | **(b)** **+2 Might once per character** (a player bit). The label "XEEN Power Juice" stays; the "+5 levels" line is dropped. | 2,500 experience per character would put the most-experience line at 1.158, over 1.15 (D-53). Act V has given few permanent stats so far. | A3: the bit and text. A2: ledger. | Cheap |
| Q20 | **(a)** Robots 56, eight Head elementals, six Gamma Gazers: 68.85k (+1.4 %). | The elementals tie each Head to its element. The Gazers make `m33.castle_door`'s "looking at you" true. | A2: Castle Alamar in the `where` of 11620/11624–11626 and the eyes. | Cheap |
| Q21 | **(a) at Dif 2:** 10 %, Patrol 70 / Annihilator 20 / Autobot 10. | All tiers are inside 50–75. Dif 2's 10 % Autobots (Eradicate) matches the 11 % placed; Dif 5 would give 40 %. | A2: row 9170 | Cheap |

**DD-08 Northern Tower**

| # | DECISION | WHY | WHO ACTS | REVERSIBLE |
| --- | --- | --- | --- | --- |
| Q22 | **(a)** 45: Slayer 33, Death 12, 31.14k.<br>DD-21's graph must land between **4.5k and 12.4k** (about 15 monsters plus Sandro), so that the DD-08 + DD-21 group stays within ±10 % of 39.6k. | It is the floor of class M, and the group closes when DD-21 is drawn. | A8: DD-21's graph. A2: recount. | Cheap |
| Q23 | **(a)** No Doom Knight. A Death Knight stands in the Hall of Thrones in his place. | D-4: nothing over the band. The Doom Knights are FD-04's. | — | Cheap |
| Q24 | **(a)** Knights only. | The source has only knights. The floors read apart by their rooms and by the Death Knights' rising share. Onyx Sentries are FD-03's (D-57). | — | Cheap |
| Q25 | **(c)** Each book gives **+1 to a different statistic** (all seven once), once per character, to every member present (seven player bits).<br>- The answer is the proverb or its vowels.<br>- A wrong answer gets the slam, and the book can be tried again.<br>- Map qbits 117641–117647 are freed. | Experience is closed: 7k would put the counted route at 1.14. The books are the tower's identity and need a reward, and +7 spread over the seven stats is within D-4's sizes. | A3: bits, texts, ORIGINAL_LINES. A2: ledger. A8: the prompts. | Cheap |
| Q26 | **(a)** The four thrones of the lows give Weak, Drunk, Afraid and Insane. The Euphoria Throne gives +1 to all seven stats, once per character. The Dunce deals 50 damage. | The source's order, with its answer-giver on L1. It is the size of the other +1-to-all devices (DD-09, DD-07, DD-16). | A3: the bit, aaze0072:8–12 and :21–25 rescaled. A2: ledger. | Cheap |
| Q27 | **(b)** "Chlc" or "aie" calls `voice`; "Chalice" calls `voice_wrong`; anything else gets aaze0072:7.<br>`q-d17.voice`'s text becomes "Very Good! Lv Lng nd prspr!" (aaze0072:5), then "The iron door beside you swings open." | "aie" is the source's own answer and follows the books' vowel rule, at no cost. Bosco's "Chlc" stays the answer he gives. | A8: the prompt. A3: the text, ORIGINAL_LINES. | Cheap |
| Q28 | **(a), narrowed.**<br>- A2 splits the family: `xeen_voweless_knights` [11150–11151], friendly from `after_qbit: 113344`; `xeen_dark_knights` [11152] stays hostile.<br>- Four row-11925 figures stand hidden in the chapter hall's niches, are shown by the oath, and stay shown on every later load. | The oath text says "the knights come out of the walls". The family's `where` includes FD-04 (D-57), so the whole family must not turn. Splitting a family's faction already exists (Burlock's knights). | A2: the faction split and row 11925. A8: niches and a reload playtest. | Cheap |
| Q29 | **(a)** A split core with the two wall stairs between. | Each floor is crossed both ways, as the source's alternating stairs do. | A8 | Medium after build |
| Q30 | **(a)** The loose disks are not placed. | The tower's two disks are the quest's (M18). | A3: disk ledger | Cheap |
| Q31 | **(a) at Dif 0:** 10 %, Slayer Knights only. They are friendly after the oath through the Q28 faction. | At Dif 1 and above the slot can roll the Doom Knight 75, over 40–62. | A2: row 9157 | Cheap |
| + | **Ormond (4928)**, Castleview's librarian, sells "The Voweless Knights' answers" as a topic for 500 gold. The topic adds an autonote with the seven proverbs and the voice's answer. The oath text is corrected (APPROVAL). | MAPS and QUESTS promise the compilation "sold in Castleview's library". A topic plus an autonote needs no new item or icon. | A4: the topic. A3: the autonote id and text. | Cheap |

---

**ROWS AND NUMBERS**

| Map | Monsters (counted) | Uncounted | Kill XP per member | Target | Rest | Chests | Textures |
| --- | --- | --- | --- | --- | --- | --- | --- |
| DD-15 (9168) | 70: Tomb Mummy 42 ×34, Pyramid Guard 52 ×24, Ghost Mummy 62 ×6, Royal Mummy 65 ×6 | Dragon Pharaoh 11919 (npc 5453) | **51.92k** | 50.4k, +3.0 % | mummies Dif 2, 10 % | 5 T5 + 1 find (scarab cell) | about 40 of 70, 1 new (`xdregplq`) |
| DD-17 (9170) | 70: Patrol 50 ×30, Annihilator 62 ×20, Autobot 75 ×6, Lesser Fire/Air/Water/Earth Elemental 55 ×2 each, Gamma Gazer 65 ×6 | Sheltem 11924, Corak 11912 | **68.85k** | 67.9k, +1.4 % | robots Dif 2, 10 % | 6 T5 + hoard T6, 2 finds | about 36 of 70, 5 new |
| DD-08 (9157) | 45: Slayer Knight 45 ×33, Death Knight 55 ×12 | Voweless Knight 11925 ×4 | **31.14k** | group DD-08+21 39.6k: DD-21 lands 4.5k–12.4k (about 10k gives 41.1k, +3.9 %) | Slayer Dif 0, 10 % | 4 T5 + 3 wall finds | about 25 of 45, 2 new |

- **Quest XP:** unchanged. Counted route 231.5k (1.11), most experience 239.5k (1.146).
- **Permanent-stat ledger, Act V adds:**
  - DD-08 books: +1 to each of the seven stats (+7);
  - DD-08 Euphoria Throne: +1 to all seven (+7);
  - DD-17 Power Juice: +2 Might.
- **Map qbits:**
  - DD-15: 117577 (throne hall reached), 117578 (scarab find).
  - DD-17: 117611–117614 (each dial at nine, from the helper).
  - DD-08: 117641–117647 are freed.

**MAPS changes (orchestrator)**
- **§0 rows:**
  - DD-15: "50.4k (51.92k, +3.0 %, D-61)".
  - DD-17: "67.9k (68.85k, +1.4 %, D-61)".
  - DD-08, DD-21: "60 (DD-08 45; DD-21 about 15 + Sandro, D-61)" and "39.6k (DD-08 31.14k; DD-21 4.5–12.4k)".
- **Dungeon list:**
  - DD-15: "Torch levers that wake the chapels' mummies, the registry lock (1701), a pad maze, the Pharaoh; optional number niches; the Pharaoh's lift after the first audience; the sky door to D7 after M30".
  - DD-17: "Conveyor rides to four Lava Heads that drop four energy fields; element sundials raising four bridges; the true-name gate; the trapdoor deck; Sheltem and Corak by cinematic; the roof hatch to D7".
  - DD-08: add "the knights friendly after the oath; Ormond sells the answers".
  - FD-01: add "a second way in from D7's roof hatch after M33 (Q-D26's key, D-61)".
- **D7 section:** "the Megadragon on Alamar's roof hatch (into DD-17 before M33, into FD-01 after, D-61)".

---

**RELAYS**

- **A1:** For DD-17, confirm four things:
  - an in-map move from a step plate keeps the facing given (Q11);
  - a horizontal slab can be a two-state door (Q13);
  - a `trap` lift can drop through 1,280 of open air (Q18);
  - hidden actors are shown by a cinematic, and a leave works after `evt.PlayCinematic` (Q15, Q17; this is D-47's XD-19 item).

  Nothing new for DD-15 or DD-08.
- **A2:**
  - **Map rows:**
    - 9168: mummies Dif 2 [2,3], 10 %, D5's lock and trap 12/6, music 46.
    - 9170: robots Dif 2, 10 %.
    - 9157: dark knights Dif 0, 10 %.
  - **Character rows:** 11924 Sheltem and 11925 Voweless Knight: peaceful, placed only, NoArena, not counted.
  - **Factions:** split `xeen_voweless_knights` [11150–11151], friendly after 113344, from `xeen_dark_knights` [11152].
  - **`where`:** add Castle Alamar to the elementals and the eyes.
  - **Ledgers and recount:**
    - permanent stats +7, +7 and +2 Might;
    - quest XP unchanged;
    - recount DD-15 51.92k, DD-17 68.85k and DD-08 31.14k.
- **A3:**
  - **M28:**
    - the Prime Directive text (Q8);
    - map-local lines: the niches, the rule statues, the Overseer's note, the tapestry, the safe, the eye cell's map, "Access Denied!", the cage, the Brew's two lines;
    - confirm that `m28.torches` fires from the last torch;
    - register 117560–117578.
  - **M33:**
    - the helper's bits 117611–117614 and the sync on load;
    - the dial's line at nine and when it leaves nine;
    - the Heads' question and the "offline" line;
    - `m33.roof_arrival`;
    - `m33.sheltem` called from the dais plate, with its question.
  - **Q-D26:** `q-d26.hatch` takes its target and text from `m33.done`.
  - **Player bits and texts:**
    - the Power Juice;
    - DD-08: seven book bits, the Euphoria bit, the books' texts, `q-d17.voice`'s text (aaze0072:5), the oath text, Ormond's autonote.
  - **ORIGINAL_LINES:** rows for every cited line.
  - **Segment 69:** written once DD-15 is built.
- **A4:** Ormond's 500-gold topic with the answers (DD-08). Nothing for DD-15 or DD-17.
- **A5:** none.
- **A6:**
  - **D5:**
    - `door:dd15` names `arrival: entrance:d5_door`;
    - `door:dd08` names `entrance:d5_tower` and drops its placeholder effect.
  - **D6:** `door:dd17` names `entrance:d6_gate`.
  - **D7:**
    - `entrance:dd15_sky` near the apex;
    - the hatch's exit chosen by `m33.done` (DD-17 before, FD-01 after, the "gone" line until FD-01 exists).
  - **Textures:**
    - register `xdregplq`, `xalavahd`, `xalavahdx`, `xasundial`, `xaglyph`, `xatrapplt`, `xvkban`, `xvkmask`;
    - add DD-08 to the map lists of `xdvowel` and `xkmirror`;
    - confirm the 7d33 accent;
    - recount the world total.
- **A7:** none. The cinematic leave is shared with XD-19; whichever map lands first tests it.
- **A8:**
  - **DD-15 first:** L1 from the graph plus this answer.
  - **DD-17 and DD-08:** L1 from their graphs plus this answer.
  - **DD-21:** draw it to 4.5k–12.4k.
  - **FD-01's L1 (phase 6):** `entrance:d7_roof`, both ways.
  - **Playtests:**
    - DD-15: the torches with a reload; the registry; the bird pads; the lift before and after the audience; the sealed sky door.
    - DD-17: belts and Heads; dial reset and sync; bridges; gate; lift; trapdoor fall; the hatch in both states; the dais refusal and the cinematic leave.
    - DD-08: both answer forms for the books; four answers at the voice; the oath with a reload; the thrones; the roof before M30.
- **S:**
  - **DD-15:** the Pharaoh is the installed P5 figure (idle, no attacks); bind the mummy tier D.
  - **DD-17:**
    - Sheltem's look on an existing caster body, with no MM9 model. Meshy, at most 30 credits, only if no shipped body reads.
    - One propaganda statue from a shipped statue decoration, tinted teal metal.
    - The robot, elemental and eye bindings.
    - D6's ruined gatehouse.
  - **DD-08:** the mm6_kni black and red tiers; 11925 on the Slayer look; the thrones from shipped decorations.
- **AU:**
  - **DD-15:** torch ignition, the pads' whoosh, the vat's bubbling and hiss; VARN beds with `pan: false`.
  - **DD-17:** the belt rumble, the four Head hums, the field crackle, the dial clank and slab grind, the gate's two chimes, the trapdoor clang, the klaxon and the groan; D-38's `xeen_vo_sheltem_refusal` and `xeen_vo_sheltem_corak`.
  - **DD-08:** optional rumble under the voice.
- **Orchestrator:**
  - the MAPS changes above;
  - the DECISIONS row;
  - a note on D-58 D-5 (the hatch leads into FD-01 after M33);
  - STATUS: DD-15 is unblocked for segment 69.

---

**SUMMARY ROW**

| D-61 | 2026-11-21 | A8's Act V graphs DD-15, DD-17, DD-08 | All three approved with changes; A8's default except DD-15 Q6, DD-17 Q14/Q19/Q21, DD-08 Q25/Q27/Q28/Q31. DD-15: 70 mummies 51.92k, the Pharaoh's lift after the first audience, Brew burns on a second click, scarab find. DD-17: 68.85k, dial-at-nine line and sync, Sheltem 11924, `m33.roof_arrival`, juice +2 Might, hatch into FD-01 after M33 (D-58 D-5 amended). DD-08: 45 (31.14k; DD-21 4.5–12.4k), books +1 stat each, Euphoria +1 all, "aie" accepted, Voweless faction 11150–11151 friendly after the oath, figures 11925, Ormond's paid answers. No quest XP added. Detail: `mockups/act5_a8_decisions.md` | A1, A2, A3, A4, A6, A8, S, AU, orchestrator |
