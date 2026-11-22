## DD-21 Necropolis Sewer

D6 · S · party 49 → 52 · 40–62, Sandro 65 · 15 + Sandro · treasure 5 · Q-D23 (Sandro's Heart), Promo Lich / Priest of Dark

![DD-21](act5_graphs/dd21.svg)

The source's Necropolis Sewer (dark maze0036, 16 × 16, aaze0036) lies under the Necropolis (maze0035). It has a cross
of sewage channels and three ladders up to the city ("Descend to the sewer?", aaze0035:17). Twelve barrels are signed
"Food for the dead, keep warm."; seven hold Dead Food (a Might test, two monsters, +1 level). There are twelve sewer
drains, an alcove, a trapped box and the "Mummy's Secret Treasure", and 11 Lava Roaches (level 40). Sandro stood in
the Necropolis itself (aaze0035:25–29); only his heart was in the sewer. Ours puts both in one BLV of three floors:
Sandro's crypt at the stair foot (0), the sewer below it (−512) and the lowest culvert (−896). It has 14 review rooms,
about 14 sectors, about 11 M units² and 8 doors (S: at most 15 sectors and 20 M units²).

- **What it is.** A lich's crypt over a sewer. Master Morbius (5506) sends the party down the crypt stair in the
  Necropolis's south-east corner. Sandro fights, falls and rises again; his heart beats in a jar in the lowest
  culvert. Bring it back and he is released, with the Key to the Dungeon of Death; casters may ask for his ritual
  first (the Lich and Priest of Dark promotion).
- **Critical path.**
  1. The crypt stair foot (`entrance:d6_stair`, quiet), the Hall of Biers, Sandro's crypt. On the first entry his
     name and "And now my hunger for the living compels me to attack you." (aaze0035:25, :26). He falls once:
     `q-d23.sandro` (beaten, autonote 4630), and the risen Sandro stands by his bier (DECIDE 2).
  2. Down the railed stair to the sewer; the main channel's west arm, the west culvert. In the sluice room the wheel
     lifts the culvert gate (one way, D-43).
  3. The outfall, the steps down, the heart culvert: the jar (`q-d23.heart`, Sandro's Heart 12353).
  4. Back by the east culvert and the main channel's east arm (the ring), up to the crypt. On the dais's step plate,
     with the heart: "Give Sandro his heart?", then "Ask Sandro for his ritual first?" (`q-d23.ritual`), then
     `q-d23.release` (the key 12354). Sandro is gone and the reliquary grille opens.
- **Off the path.** These rooms lie off the critical path:
  - The mummy's vault (behind a stone door at the west arm's end): two Ghost Mummies and the source's "Mummy's Secret
    Treasure" (T5).
  - The dead-food cellar: the barrels and the one that can be pried (DECIDE 4).
  - The east culvert's niche with the source's trapped "Box" (T5), and three sewer drains with small finds.
  - Sandro's reliquary (T5 and his statuette, DECIDE 6), on the way out.
- **Loop (1).** The sewer ring: stair landing, west arm, west culvert, outfall, east culvert, east arm.
- **Set piece.** Sandro's heart: the lowest culvert falling into a black cistern, the jar of green glass on a ledge,
  a green light in it and a slow heartbeat heard from the steps. Sandro's crypt (the boss) is the second goal.
- **Riddles and their answer-givers.**
  - Where the heart is: Master Morbius (5506, "He lives in the sewer under us"), Digby the gravedigger (5510, "Something
    under the city keeps its heart in a box"), Sandro himself at his first fall, and autonote 4630.
  - The sluice gate: its click says the wheel is upstream; the wheel's click says what it opened.
- **How Sandro rises (DECIDE 2).** Proposed with existing engine words only:
  - Two bodies. The hostile Sandro (11283) falls for real, once; a timer with a kills condition (XD-19's
    `evt:lord_dead` pattern) calls `q-d23.sandro` and shows a hidden risen Sandro by the bier.
  - The risen Sandro is a peaceful placed-only figure (A2 row). A load event keeps him unkillable
    (`SetMm9ActorCanReceiveDamage(false)`) and shows him while `beaten` is set and `released` clear.
  - He talks through the dais's step plate and the bier's click (he has no NPC id). Without the heart he says the
    beaten text; with it, the heart text and the two prompts. After the release he crumbles to dust (a shipped
    effect) and stays hidden.
  - There is no second fight. A3 trims two lines of the hook text, as DECIDE 2 says.
- **Monsters (15 + Sandro) and kill XP.** These are placed:
  - Cinder Roach 40 × 10 (a new giant-crawler tier D, A2 request; the source's Lava Roach D33 at 40). Two of them are
    hidden in the Dead Food barrel and shown when it is pried.
  - Greater Lich 50 (11281) × 3, Sandro's household: two in the Hall of Biers, one at the heart.
  - Ghost Mummy 62 (11273, placed only, D-57) × 2 in the vault.
  - Sandro 65 (11283) once.

  Groups are 2–3. The stair foot, the landing, the sluice room, the outfall and the reliquary are quiet. XP:
  - **10.70k per member** (42,803 / 4): the 15 at 9.48k, Sandro 1.22k.
  - **Sandro counts once.** Under DECIDE 2 (a) he dies once and rises as a figure that is never fought; under (b) he
    never dies (no kill XP; the release's 12,000 stands in).
  - With DD-08's 45 (31.14k) the group is 60 + Sandro and **41.84k against 39.6k, +5.7 %**. Session 10 assumed DD-21
    at about 10k (+3.9 %); the exact share would be 8.47k (DECIDE 1 c).
  - Rest encounters 10 % from the Greater Liches and the Cinder Roaches (DECIDE 8).
- **Treasure.** Three chests T5 (S: 0–3): the reliquary (Sandro's "treasures in this room"), the mummy's vault and the
  trapped Box. Three drain finds at treasure 5, the Dead Food (DECIDE 4), the heart and the key.
- **Original lines.**
  - Sandro: aaze0035:25 (his name) and the last sentence of :26 on the first entry; :27 and :28 are A3's
    `q-d23.sandro` and `q-d23.release` texts (the "+2,000,000 experience" dropped); :29 "Don't even THINK about taking
    my statuette!" on the reliquary grille.
  - The sewer: aaze0036:4/:5 the signed barrels; :7, :8 and :9 the Dead Food (rescaled); :3/:1 the drains; :10 the
    vault's door; :2 the Box; :0 the alcove.
  - aazex122:24 (Sandro's note "Gone to Necropolis ...") belongs to the Dungeon of Death, FD-04's lower half, which his
    key opens: not placed here.
- **Door to D6.** D6's `door:dd21`: `thing:dd21_crypt`, the crypt in the Necropolis's south-east corner, grille pair
  `gkp103a` in its north face, sealed with a line until DD-21 is built.
  - **Inside arrival proposed:** `entrance:d6_stair` (as D6 assumes, D-37), at the stair foot. In the map's frame it is
    about (0, 0, 0); the stair climbs north from y 256 to the grille pair at y 1,024, z 448. Facing south (1536), into
    the Hall of Biers. The grille's inner face is the same `gkp103a` pair, with the exit preset at the stair's top.
  - **Return:** the exit preset to D6's installed `entrance:dd21_stair` (17408, −11776, 1664), facing 512. It lies about
    280 north of the crypt's door (the crypt spans sketch x 97.25–98.75, its north face at about y −12,060), facing away.
    **It matches**; the door goes live by itself once DD-21's sidecar lists `entrance:d6_stair` (D6 NOTES).
  - The source's sewer had no way-up line. The exit preset's meaning is proposed map-local: "Climb up to the
    Necropolis?" (A3). "Descend to the sewer?" (aaze0035:17) suits D6's side of the door.
- **Hooks.** All four of Q-D23's DD-21 hooks are placed:
  - `q-d23.sandro`: Sandro's first fall, then the dais's step plate and the bier.
  - `q-d23.release` and `q-d23.ritual`: the two prompts at the dais.
  - `q-d23.heart`: the jar in the heart culvert.

  Map qbits:
  - 117720: `dd21_arrived_once`.
  - 117721: the sluice.
  - 117722: Sandro's first-entry line.
  - 117723: the Dead Food barrel pried.
  - 117724–117726: the three drains.
  - 117728: the statuette, only under DECIDE 6 (b).
  - The rest of 117720–117759 are free.
- **Textures.** The sewer is MM6 Free Haven Sewer `sewer.blv` (A6's assign for DD-21, another face than XD-01's): grey
  d1 stone walls (`d1wcntr`, `d1wldle2`, `d1wldle3`, `d1smbw`), `d7flor4` walkways, `swprrf3` sewage with the `swp`
  pipe mouths, `d1lggrt` grates, `d1mbea` beams. Sandro's crypt is MM6 Tomb of Ethric the Mad 6d14's niches (A6's
  crypts assign): `d2wlbctr`/`d2wlbpos` walls, `d2niche1/3/4`, `d2flor4`, `d2ceil3`, `d2lgdor` doors, `crsmdr1` on the
  vault, `cedsqrdk` posts. The stair's top uses D6's `gkp103a` inner face. About 24 of 30 textures; 1 is new: `xdsandro`
  (Sandro's seal, a heart pierced by a bone, once over the crypt doors).

**DECIDE items** (options in the graph file; the proposed default first)

1. **Count.** (a, proposed) 15 + Sandro: 10 Cinder Roaches, 3 Greater Liches, 2 Ghost Mummies, Sandro once. That is
   10.70k, and the group 41.84k (+5.7 %). (b) No mummies, 11 roaches and 4 Greater Liches: 9.72k, the group +3.2 %.
   (c) The exact share, 10 roaches, 3 Greater Liches and Sandro (13 + Sandro, under S's 15): the group 39.61k
   (+0.0 %). Depends: A2's recount, DD-08's Q22.
2. **How Sandro rises.** (a, proposed) Two bodies, one fight: the hostile Sandro dies once; a peaceful, unkillable
   risen Sandro (shown by the fall's event and by load events while `released` is clear) waits by the bier. A3 trims
   "Once again you must defeat me, or die." to a threat and fits "rises from the floor, slower this time" (the heart
   text). (b) He fights every time without the heart: the damage hook counts the blows against his row's HP, zeroes
   the killing blow, restores his HP with `evt.SetMapActorHp` and swaps in the figure. That means no kill XP for
   Sandro, and A1 must confirm that `hook.damage` is the HP taken. (c) A revive word from A1 (the source's behaviour).
3. **The sewer's vermin.** (a, proposed) A new ordinary giant-crawler tier D "Cinder Roach" 40 (11363, look C, Fire,
   where DD-21; ordinary so that rests can draw it). (b) The existing Lava Roach 26, under the band: the group 39.18k
   (−1.1 %). (c) Vampires 40 (11291) in their place, no new row.
4. **The Dead Food barrel.** (a, proposed) One barrel: Might at least 30 to pry (else aaze0036:7), two hidden roaches
   shown, then eaten once per character for +2 Endurance (a player bit; the +1 level line rescaled). (b) +1 Endurance
   and +1 Might. (c) Dressing only, no roaches (13 monsters).
5. **The sluice gate.** (a, proposed) The culvert gate is opened by the sluice wheel in its room off the west culvert
   (one way, D-43); each answers the other's click. (b) No gate and no sluice room.
6. **Sandro's treasure and statuette.** (a, proposed) The reliquary behind the grille, opened by the release: a chest
   T5. The statuette is dressing, with aaze0035:29 kept on the grille (the source's statuette was Luna's Griffin,
   which is DD-07's here). (b) As (a), and the statuette a T5 find. (c) No grille.
7. **The vault's mummies.** (a, proposed) Two Ghost Mummies 62 (11273). (b) Two Pyramid Guards 52 (11271), −0.62k
   (the group +4.1 %). (c) None.
8. **Rest encounters.** (a, proposed) 10 % from the Greater Liches and the Cinder Roaches, never the placed-only Ghost
   Mummies or Sandro (D-39). (b) 0.

**Requests to other lanes**
- **A1:** nothing under 2 (a). Under 2 (b), confirm that `hook.damage` in the monster damage hook is the HP the blow
  takes, and that `evt.SetMapActorHp` works from studio wiring Lua. Under 2 (c), a word that revives a dead placed
  actor.
- **A2:**
  - The Act V recount (DD-21 15 + Sandro, 10.70k; the group 41.84k).
  - The Cinder Roach tier (3 a). The risen Sandro, a peaceful placed-only row with Sandro's look, uncounted (the
    characters block is full at 11923: an id from A2).
  - Add DD-21 to the Ghost Mummy's and the liches' `where`.
- **A3:**
  - Under 2 (a), trim the two `q-d23.sandro` lines.
  - Map-local lines: the first-entry line (aaze0035:25 and :26's last sentence), the sluice wheel and gate, the grille
    (aaze0035:29, "The grille is locked."), the exit's "Climb up to the Necropolis?".
  - The Dead Food player bit and text (4). ORIGINAL_LINES rows for the lines above. Register map qbits
    117720–117728.
- **A4:** nothing (Morbius 5506 and Digby 5510 already point to the sewer).
- **A6:** nothing on D6 (the outside point matches). Register `xdsandro` (a proposed name). Confirm the sewer.blv and
  6d14 assigns as planned. Optionally, the crypt door's question "Descend to the sewer?" (aaze0035:17).
- **AU:** optional: a slow heartbeat loop at the jar. The sewer bed and the sluice grind are shipped.
- **S:** the giant-crawler mesh (already planned as new) with an ash skin for the Cinder Roach, and a jar of green
  glass (a decoration, or a shipped jar or urn with a green light). The risen Sandro uses 11283's look.

**State and next steps.** The graph, the SVG and these notes were written on 2026-11-21 (session 11, phase 5,
graphs only; nothing is built or installed). The render printed no warnings; the PNG
(`output/studio_cal/a8_s11/png/dd21.png`, headless Chrome) has been checked. Next: the decider answers the DECIDE
items, then L1.
