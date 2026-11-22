## DD-24 Giants' Hall

D5 · S · party 45 → 47 · 36–62 (MAPS 38–58, DECIDE 2) · 30 · treasure 5 · Q-D16 (the bloody throne)

![DD-24](act5_graphs/dd24.svg)

No source maze: Darkside D1 has Gurodel's giants and the bloody throne outdoors (dark/aaze0013:7–8, 19, 33–34). Ours
is Gurodel's hall in the hillside behind his hold on D5: two floors 1,024 apart built for giants. 11 review rooms,
about 14 sectors, about 16 M units², 6 doors (the great doors and the throne hall's doors as hinged pairs).

- **Giant scale.** The stand-in is MM8's cyclops: drawn about 310 high (model 2.4 × 127.5), descriptor body 185 high,
  radius 100 (60 by D-32). Openings 384 wide × 512 high, halls 768–1,024 high, the Great Stair 640 wide with 1,024 of
  headroom and 96-high steps (the party steps 128). The little ones' crack is 128 × 256: it keeps giants out only if
  A2 raises their body height to about 300 (DECIDE 5).
- **What it is.** The People's hall. At peace it is open and its giants friendly; at war (Gurodel's "Your hall", or
  Q-D12's hostile/camp_burned) "the People will be waiting on the stair", and the bloody throne at the top holds two
  Energy Disks.
- **Critical path.** Threshold (`entrance:d5_hold`, quiet); longhall; the Great Stair; the upper landing; the throne
  hall's double doors; the bloody throne (`q-d16.throne`).
- **Off the path.** The larder (T5); the sleeping hall; the boulder store and the crack; the trophy gallery; Gurodel's
  hoard behind the throne (T5, refuses at peace: "Gurodel would notice.", DD-13's pattern).
- **Loops (2).** Up the Great Stair or up the crack to the trophy gallery; into the throne hall by its double doors or
  the gallery's side door.
- **Set piece.** The bloody throne: black wood big enough for four, stained dark, under a smoke hole (`sky: true` at
  least 1,280 above the floor, D5's Darkside day preset, never `xeendark1`).
- **Monsters and treasure.** The People as their own rows (D-25): Cyclops 36 × 9, Giant 50 × 17, Elder Giant 62 × 4
  (A2's new tiers, e.g. 11083–11085, faction `xeen_giants_people`). 30 monsters, **20.94k per member** (83,760 / 4).
  With DD-16's 4.79k the group is 37 monsters and 25.73k against 45 and 26.7k (−3.6 %). Chests T5 × 2. Rest
  encounters 0 (the only rows are peaceful at peace).
- **Original lines.** dark/aaze0013:34 the throne (A3's hook); :33 "We recognize you as enemies!  Prepare to defend
  yourselves!" at the threshold once per war; :26 (close) on the longhall's law stone; :19 "Greetings, little ones." is
  Gurodel's on D5.
- **Door to D5.** The great doors in the hillside behind Gurodel's fire (A6, D5 not built), two leaves 384 × 512.
  **Inside arrival proposed:** `entrance:d5_hold`, about 384 inside the leaves, facing into the hall. The way out
  returns to D5 about 512 before the doors, facing away, clear of Gurodel.
- **Hooks.** `q-d16.throne` (the throne hall); proposed `q-d16.hall_attacked` (a People giant struck at peace: map
  qbit 118091 by D-37's timer pattern, then war). Map qbits: 118090 the war line shown, 118091 struck.
- **Textures.** No family yet: proposed MM8 Cyclops Larder d14 (DECIDE 3): gcav1wal, gcst1bs1, gcst2flr, gston1fl,
  gcst2cel, gkp1ceil planks, trim9_32, furnishing; 2 new (`xdgiantd`, one giant door wing mirrored on the pair;
  `xdthrone`, black wood stained with old blood). About 16 of 30.

**DECIDE items (DD-24)**
1. **The hall at peace.** (a, proposed) open: the People as their own rows and faction, friendly at load, hostile on
   `q-d16.war`, `q-d12.hostile`, `q-d12.camp_burned` or a blow; Gurodel stays on D5; throne and hoard refuse at peace;
   (b) shut until war, ordinary giant rows; (c) Gurodel inside on his throne, a Giant King boss at war.
2. **Levels and count.** (a, proposed) Cyclops 36 × 9, Giant 50 × 17, Elder 62 × 4 (20.94k; group −3.6 %), MAPS's
   DD-24 row 38–58 → 36–62; (b) Giant 50 × 30 (group +2.2 %, inside 38–58); (c) 38 in the hall (over S, +12 %).
3. **Texture family.** (a, proposed) MM8 Cyclops Larder d14, 2 new; (b) MM8 Barbarian Fortress d25 (shares XD-23's
   troll rock); (c) MM7 Stone City 7d24 (XD-09's hub).
4. **Rest encounters.** (a, proposed) 0; (b) 10 % at war only (needs a qbit-switched encounter, A1).
5. **Giant body height.** (a, proposed) A2 sets about 300 on the giant rows (crack keeps them out); (b) leave 185.

**Requests to other lanes**
- A2: three People tiers (36/50/62) in faction `xeen_giants_people` with relations on 113321, 113242, 113244 and the
  hall-attacked bit; body height about 300 on the giant family (DECIDE 5); Act V recount (37 monsters, 25.73k).
- A3: hook `q-d16.hall_attacked` (sets war); the hoard's "Gurodel would notice." and the law stone as map-local lines.
- A4: nothing (Gurodel 5452 stays on D5).
- A6: `entrance:d5_hold` and its return point; the great doors on D5; a dungeon_families line for DD-24 and the two
  new textures `xdgiantd`, `xdthrone`.
- Orchestrator: MAPS DD-24 row 38–58 → 36–62 (if DECIDE 2a).
- AU, S, A1: nothing.

**State and next steps.** Graph, picture and notes written 2026-11-20 (phase 5, graphs only; nothing built or installed). Next: the decider answers the DECIDE items, then L1. The scratch PNG (ImageMagick) drops the link strokes; the SVG is the reference.
