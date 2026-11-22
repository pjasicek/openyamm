# FD-01 Alamar Depths graph: decisions (D-69)

Decider D-69, 2026-11-21. If this answer disagrees with `mockups/act6_graphs/fd01.graph.yml`, `notes_fd01.md` or `act6_fd01_graph_a8.md`, this answer wins.

**What I read:**
- the page, the graph, the notes and the PNG `output/studio_cal/fd01/png/fd01.png`;
- MAPS (§0 FD-01 + FD-02, the dungeon list), QUESTS (M39, Q-D26, Q-F1), WORLD_DESIGN and MONSTERS_AND_ITEMS (the robots);
- D-57, D-61, D-65, D-66 and D-67, D-37 and D-24 (DECISIONS rows), and `lanes/README.md`;
- A2's recount (`lanes/A2.md`, `balance_installed_20261121k.md`);
- the quest files `m39.yml`, `q-d26.yml` and `q-f1.yml`;
- D7's `output/studio_cal/d7/tools/gen_objects.py` (the hatch's LIVE logic);
- DD-17's and DD-22's `geo.py` texture use;
- the sw textures (`swll5dk`, `swall2`, `swall4`, `swdoora`, `swdoorb`, `swdoorc`, `swtrpnl`), looked at side by side.

---

## APPROVAL

**FD-01 Alamar Depths: approved with changes.** A8's default stands on eight of ten questions. The two exceptions are Q67 (b), a named point on D7, and Q72 (b), the main walls moved off `swll5dk`. A8 builds L1–L4 from the graph plus the changes below. No redraw is needed.

**What stands as drawn:**
- 20 review rooms, about 27 sectors, about 43 M units² and 11 doors. This is inside class M.
- The C of galleries round the west maze, the two levers and the east wing with both keys.
- One skull door, and Roland's stasis vault a lift (768) below.
- One loop, closed by the bolted grate.
- Four T6 chests, and the Dragon Tower key on the critical path (D-57 Q23).
- Both arrivals are quiet (D-11.3), and every dead end holds something.
- Inside names: `entrance:d6_stair` and `entrance:d7_roof` (D-37).
- The exit to D6 is the `exit` preset (D-24). The way up to D7 asks the map's own Yes/No (D-66).

**Changes:**

1. **The levers show what they did.** Neither slab can be seen from the lever hall, so a pull would otherwise be a mechanism with no visible effect (D-43).
   - Each first pull grinds (FX 35) and shows a status line that names the direction. A3 writes the lines, for example "Far to the west, a wall grinds down into the floor." and the same for the east.
   - Each closed slab reads as a shut bulkhead: a shipped sw door or panel picture (`swdoora` or `swpnl`), once per face and whole, so it does not look like plain wall.
   - **WHO ACTS:** A3 (two map-local lines), A8.
2. **The stasis coffin reads as a coffin and opens as the text says.** The hover is "Coffin" and `m39.roland`'s text begins "The coffin's lid slides back".
   - A8 builds a long steel coffin on the dais from the sw kit, about 256 × 96 × 80, with its lid as a small sliding leaf.
   - The click drops the field and slides the lid back. Both stay so on every load with `m39.done`.
   - The field's face and the coffin both carry the click and the "Coffin" hover until `m39.done`, so a click on the field is not lost.
   - **WHO ACTS:** A8.
3. **The stasis vault's pair** is one `swdoorb` picture split over two leaves that part in the middle (D-67 item 3).
   - It is not two mirrored `swdoorb` wings. `swdoorb` is a whole door, not one wing, so a mirrored pair would show two doors side by side.
   - **WHO ACTS:** A8.
4. **The bolted grate is a solid leaf with the lattice picture `swdoorc`**, once per face and whole. It opens one way, by side:
   - the bolt is on the workshop face ("You draw the bolt.");
   - the gallery face says "Bolted from the other side.".

   A solid leaf blocks the robots' sight and shots, while the picture still reads as a grate.
   - **WHO ACTS:** A3 (lines), A8.
5. **The shaft's way up has its own hook.** A quest hook names one map (QUESTS_FORMAT §4), so FD-01 cannot simply be added to DD-17's `q-d26.alamar_hatch`.
   - A3 adds `q-d26.depths_hatch` (map FD-01) with the same `requires: {qbit: roof_unlocked}` and the fail_text "Bolted from above.". FD-01 goes into Q-D26's `maps`.
   - The ladder up the shaft wall is dressing. Its foot is the click: the map's own Yes/No "Climb up through the hatch?", with no message before it (D-65 B1, D-66). Yes calls the hook; when it returns true, the party moves at once to D7's `entrance:fd01_roof` (Q67).
   - The first arrival from D7 shows one status line, once per game (map qbit 117846). A3 writes it, for example "You climb down through smoke and rubble to the floor of what was Castle Alamar." A D6 arrival gets the statue; a D7 arrival would otherwise land in a dark shaft with no word of where it is.
   - **WHO ACTS:** A3, A8.
6. **D7's side at FD-01's install.** A8's page says "D7: nothing", but D7's `gen_objects.py` reads `LIVE['fd01']` when it runs, so D7 must be regenerated after FD-01 is installed.
   - At the same install, A3 drops `q-d26.hatch`'s `m33.done` state ("Castle Alamar is gone."). Otherwise that line would show and the party would then be moved into FD-01 anyway.
   - **WHO ACTS:** A6, A3.
7. **Textures as Q72 (b).** **WHO ACTS:** A6 (the `per_site` line), A8.
8. **Alamar's statue reuses DD-17's propaganda statue**: the teal statue S owes DD-17 (D-61, D-66 item 8), not MM6's `sta1a`.
   - It carries a title ("Statue") and a speech, so it must read right (D-66).
   - It blocks FD-01's done, not its L1.
   - **WHO ACTS:** S, A8.
9. **The long gallery's two juice niches** are either left out of the geometry or dressed (a dead robot frame, no title). They must not be empty alcoves that look as if something was taken. **WHO ACTS:** A8.
10. **NOTES and checks.**
    - The L4 NOTES carry D-57 Q7's exception line: 34 monsters under M's 45.
    - The playtests cover:
      - both ways in;
      - the levers in both orders;
      - the grate from both sides;
      - the key box once, then "Nothing here.";
      - the warden's chest once;
      - the skull door;
      - the coffin, then a reload (field down, lid open, the empty line);
      - the shaft's way up, bolted without `roof_unlocked` and then, with it set, up to `entrance:fd01_roof`;
      - the D6 exit landing at `entrance:fd01_stair`.
    - `oymap audit` passes (dressing, lights, doors, texture fit).
    - **WHO ACTS:** A8.

**General rules:**
- No new monster rows, bodies, items, icons or textures.
- No Meshy or MM9.
- No quest experience is added: M39's 40,000 is already in Act VI.

---

## Decisions

| # | DECISION | WHY | WHO ACTS | REVERSIBLE |
| --- | --- | --- | --- | --- |
| Q63 | **(a)** Annihilator 62 (11611) × 28 and Autobot 75 (11612) × 6, 34 in all, placed by room as drawn: 40.81k per member. The FD-01 + FD-02 row is 71.88k against 68.0k (+5.7 %). | D-57 Q7 lets FD-01 move anywhere in 30.1k–43.7k, and 40.81k is inside that. It keeps the source's two families and its six Autobots, a C share of 18 %. With Patrol 50 under the band, 34 robots cannot come under 37.94k. Option (c) buys 3k by thinning a map that is already under M's 45. Option (b) halves the source's C tier for 1.4k. Act VI moves to about 1.037, well under 1.15. | A2: recount; FD-01 in the robots' `where`. A8: placement and the NOTES exception. | Yes, cheap until placement |
| Q64 | **(a)** One skull door (`m39.skull_door`, the Cube) before the stasis lift. The Silver skull's place becomes the plain warden's door. | The world has no I.D. cards (D-57 Q18), and A3's `m39.yml` already has one door. A second door reading the same Cube would add a click and no choice. :5 and :6 go unused. | A3: `skull_door`'s `where`. A8. | Yes, cheap |
| Q65 | **(a)** No figure. Roland lives only in the text, with no row and no body. The coffin is built and opens as change 2 says. | His speech ends with him leaving at once ("I must return to my brother"). A body would cost S a figure and A2 a peaceful row for a single talk. The sliding lid and the dropping field make the moment visible. | A8 (change 2). | Yes, cheap: (b) can be added later with a load event |
| Q66 | **(a)** The bolted grate between the workshop and the south gallery, drawn from the workshop's side (once, 117843), built as change 4. | It closes the one loop and cuts the walk back to about a third without a bypass on the way in. The gallery side's "Bolted from the other side." hints at the shortcut, and the game answers it later. | A3: two lines. A8. | Yes, cheap |
| Q67 | **(b)** A6 adds D7's `entrance:fd01_roof` at the hatch's point (−18688, 8448, 1536), facing 1024. FD-01's way up names it. | It follows D6's precedent: `entrance:fd01_stair` was added at DD-17's gate point, with one name per dungeon that lands there. DD-17 is gone after M33, so `dd17_roof` would name a dead map. D7 is rebuilt at DD-26's install (D-65) and again at FD-01's install (change 6), so this adds no extra rebuild. A6 adds the point at the DD-26 rebuild, before FD-01's L4. | A6, A8. | Yes, cheap |
| Q68 | **(a)** The map's own Yes/No, then `roof_unlocked`; "Bolted from above." until then. It uses the new hook `q-d26.depths_hatch` (change 5). | Without the gate, a party that came down D6's stair before the Megadragon fight would climb out under a level-125 dragon. It matches DD-17's side (D-58 D-5): the bolt is on top, so holding the key below does not help. | A3: the hook, Q-D26's `maps`. A8. | Yes, cheap |
| Q69 | **(a)** Dropped. The niches are handled as change 9. | DD-17 already pays the juice (+2 Might, D-61 Q19). Spent boxes (b) waste clicks. Potion finds (c) pad a map that already has 4 T6 chests and two keys. | A8. | Yes, cheap |
| Q70 | **(a)** A small dark Ancient pyramid in the nook: hover "Pyramid", click "Its light is out. Its twin stands outside the gate." (true: D-50's D6 pyramid stands outside Alamar's gate). The nook's T6 chest stands beside it.<br>The pyramid is a shipped pyramid or obelisk decoration that S names. If there is none, A8 shapes four sloped faces on a plinth in the D6 pyramid's cladding. If neither reads as a pyramid, use (b): no title, chest only. | It keeps the source's object at no cost and points at the working pyramid. A working pad (c) would add a third exit beside a stair that is already close. | A3: the line. S: name a decoration. A8. | Yes, cheap |
| Q71 | **(a)** 0. | The robots' slot rolls Patrol 50 at Dif 0, under the band. This is D-57's rule for Act VI. | A2: row 9179, encounter 0, treasure 6. | Yes, cheap |
| Q72 | **(b)** Main walls `swall4` (crossed braces with rust) in the galleries and the passages, and `swall2` (diamond braces) in the halls. Floors stay `swankdk`. The rest is as (a): `swceilf`, `swgirder`/`swaled`, `xahullbn` where the castle came down, `swtrpnl`/`swtrdk` on the skull door, `swor2`/`trekscrn` and `xafield`, plus changes 1, 3 and 4. No `swll5dk` main walls and no red accent panels. About 22 of 45, 0 new. | Since D-67, DD-22 (also under D6) wears `swll5dk` everywhere, and D-67 moved it there to read apart from "the teal of DD-17 and FD-01". `swll5dk` walls would make the depths a twin of Sheltem's pod. FD-01 is Alamar's own bottom: DD-17 already uses `swall4` for its sump and `swall2` for its bays, so the undercroft reads as the castle's substructure, burnt and buckled. | A6: the `per_site` line. A8. | Medium after the bake; free before L1 |

---

## ROWS AND NUMBERS

| Map (row) | Monsters | Kill XP per member | Group row | Rest | Chests | Textures |
| --- | --- | --- | --- | --- | --- | --- |
| FD-01 (9179) | 34: Annihilator 62 × 28, Autobot 75 × 6 (NOTES exception: under M's 45) | **40.81k** (163,242 / 4) | FD-01 + FD-02 68.0k: **71.88k, +5.7 %** | 0 | 4 T6 + the Dragon Tower key's box | about 22 of 45, 0 new |

- **Kill XP:**
  - 28 × 4,464 + 6 × 6,375 = 163,242, which is 40.81k per member.
  - The rejected mixes: (b) 39.38k, (c) 37.46k.
- **Act VI:** A2's projection was 341.5k of 333.0k (1.025) with FD-01 at 36.93k. With 40.81k it is **about 345.4k of 333.0k (1.037)**. No trigger.
- **Quest XP:** unchanged. M39's 40,000 and its award are already counted.
- **Treasure:** 4 T6 chests:
  - the pyramid nook;
  - the assembly hall;
  - the warden's chest, which also calls `m39.darkstone_key`;
  - the stasis vault.

  Finds: the Key to the Dragon Tower 12376, once (map qbit 117844).
- **Map qbits 117840–117879** (A3 registers the block):
  - 117840: the statue has spoken;
  - 117841, 117842: the west and east slabs down;
  - 117843: the grate's bolt drawn;
  - 117844: the key box taken;
  - 117845: the skull door open;
  - **117846: the first arrival from D7 (change 5)**;
  - 117847–117879 free.

  Quest qbits used: 111780 (`darkstone_key`), 111781 (`m39.done`) and 113521 (`roof_unlocked`).
- **New ids:**
  - D7's `entrance:fd01_roof`;
  - A3's hook `q-d26.depths_hatch`.

  No new rows, items, NPCs, houses or textures.

---

## RELAYS

- **A1:** none. Everything used already exists:
  - slabs by event and qbit, and one-way doors by side;
  - a lift, field and lid leaves, and `open_sky` with a preset;
  - the map's Yes/No, finds, chests that call a hook, and status lines.
- **A2:**
  - The Act VI recount with FD-01 at 40.81k (row 71.88k, +5.7 %; Act VI about 1.037).
  - FD-01 added to the robots' `where` for 11611 and 11612.
  - Map row 9179: encounter 0, treasure 6.
  - The `maps.yml` monster text: "group FD-01+02: 60 (FD-01 34: Annihilator 28, Autobot 6)".
- **A3:**
  - Register 117840–117879.
  - `m39.plaque_nine` `where`: "the plaque in the Hall of Nine, by the lever hall".
  - `m39.skull_door` `where`: "the skull door between the warden's room and the stasis lift".
  - `q-f1.tower_key` `where`: "the box in the key vault".
  - New hook `q-d26.depths_hatch` (map FD-01; question "Climb up through the hatch?"; requires `roof_unlocked`; fail_text "Bolted from above."), and FD-01 added to Q-D26's `maps`.
  - At FD-01's install, drop `q-d26.hatch`'s `m33.done` "gone" state.
  - Map-local lines:
    - the two lever tells (change 1);
    - "Bolted from the other side." and "You draw the bolt.";
    - "Its light is out. Its twin stands outside the gate.";
    - the shaft's first-arrival line (117846).
  - ORIGINAL_LINES rows for aaze0052:2, :3 and :4 (rewritten), :7, :8, :9 (shortened), and :12–:17.
- **A4:** none. Roland's move to house 4201 is already in `m39.yml`.
- **A5:** none.
- **A6:**
  - **D7, at the DD-26 install rebuild:** add `entrance:fd01_roof` at (−18688, 8448, 1536), facing 1024.
  - **D7, at FD-01's install:** regenerate it so that `LIVE['fd01']` takes effect (the hatch into FD-01 after `m33.done`), together with A3's hook change.
  - **D6, at FD-01's install:** drop `DUNGEON['fd01'] = False` and rebuild, so that `thing:fd01_stair` leads to `entrance:d6_stair`.
  - **The ancient kit's `per_site` line for FD-01:** "the sw set's braced panels (`swall4`, `swall2`) on `swankdk` plate floors, with `xahullbn` where the castle came down; no `swll5dk` main walls, no red accents (D-69)". Confirm the count at install.
- **A7:** none.
- **A8:**
  - FD-01's L1–L4 from the graph plus changes 1–10 and Q72 (b).
  - The sub-agent rules apply.
  - FD-01's done waits on S's statue (change 8). Its L1 does not.
- **S:**
  - The teal Alamar statue that DD-17 already waits on (D-61, D-66) also serves FD-01's undercroft hall.
  - Name a shipped small pyramid or obelisk decoration for the nook, or say there is none (Q70).
- **AU:** optional: wind and trickling grit down the shaft, and the coffin's cold hum, which stops with the field. The machine bed and the lever grind are already shipped (DD-17's).
- **Orchestrator:**
  - **MAPS §0, row FD-01 + FD-02:**
    - Monsters: "60 (FD-02 26; FD-01 34, D-57, D-69)".
    - Kill XP: "68.0k (71.88k, +5.7 %: FD-02 31.07k, FD-01 40.81k, D-69)".
  - **MAPS dungeon list, FD-01:**
    - Monster levels: "55–80 (robots 62/75 placed, D-69)".
    - Role or notes: "The castle's undercroft round the west maze: two levers, the Dragon Tower key, one skull door (the Cube), Roland's stasis vault a lift below, the bolted grate's way back; a second way in from D7's roof hatch after M33 (Q-D26's key, D-61)".
  - **QUESTS:**
    - Q-D26: "Guards a shortcut onto Castle Alamar's roof (into FD-01's rubble shaft after M33, D-61, D-69)".
    - Q-F1: add "the Key to the Dragon Tower lies in FD-01's key vault on M39's path (D-57 Q23, D-69)".
  - **MONSTERS_AND_ITEMS, robots:** "Castle Alamar, D6" becomes "Castle Alamar, Alamar Depths (FD-01), Dungeon of Death (FD-04)".
  - **STATUS:** FD-01 to L1. Add the DECISIONS row below.

---

## SUMMARY ROW

| D-69 | 2026-11-21 | A8's FD-01 Alamar Depths graph | Approved with changes; A8's default except Q67 (b) `entrance:fd01_roof` on D7 and Q72 (b) walls `swall4`/`swall2`, not DD-22's `swll5dk`. 34 robots (62 × 28, 75 × 6) 40.81k, row 71.88k (+5.7 %), NOTES exception; one skull door; no Roland figure, the lid slides open; bolted grate loop; new hook `q-d26.depths_hatch`; juice dropped; dead pyramid; rests 0; lever tells. Detail: `mockups/act6_fd01_decisions.md` | A2, A3, A6, A8, S, orchestrator |
