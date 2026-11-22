## FD-02 Southern Sphinx

X6 · S · party 58 → 61 · 62–72 (MAPS 55–75; DECIDE 2) · 26 · treasure 6 · M40 (Picard, the Chime of Opening)

![FD-02](act6_graphs/fd02.svg)

The source's three levels (dark mazes 125–127) as one BLV of three storeys in and under the half-buried sphinx on X6's
west rim: the body (z 0, the breast steps down to the halls at −256), the head (z 768, the Home of the Aged) and the
crypt under the sand (z −1,280, the dragon mummies). 13 review rooms, 15 sectors (the hall of embalming and the crypt
two each), about 12 M units², 5 doors. **S: at most 15 sectors and 20 M units².** The interior is larger than X6's
shell (3,072 × 2,048), as XD-14's and DD-07's (D-39 Q6/Q7).

- **What it is.** Picard the Aged's home. Runes in the Preservation Rooms spell his name; a voice at the stair asks it;
  behind the door of the name the old man in his very good chair trades the Chime of Opening for Halon's widget (Q-C14).
- **Critical path.** Breast steps (`entrance:x6_door`, quiet); the hall of embalming; one death run (Swinging or
  Chopping); the first Preservation Room (runes P, I, C); the canopic chamber; the second Preservation Room (A, R, D;
  the sixth stone calls `m40.runes`); the other death run back to the hall; the stair of the name ("Study the lessons to
  learn my name." on a plaque at its foot); "What is my name?" on the top landing and at the door (PICARD:
  `m40.name_right`, `name_said` 111800, the door opens in the same visit); the Home of the Aged (Picard 5704, A3's
  topic, `m40.done` 111801, 20,000).
- **Off the path.** The two sarcophagus galleries in the head's lappets (two Phase Mummies and a fixed find each); the
  crypt of the dragons and the stalls down the canopic chamber's steps (four and two Dragon Mummies, the embalmer's T6
  chest, the illusion heap).
- **Loop (1).** Round the body: out by one death run, through both Preservation Rooms and the canopic chamber, back by
  the other.
- **Set pieces (2).** The Home of the Aged: shelves to the vault (`xsshelf`), two bars of light through the eyes, four
  books on two lecterns by the walls, Picard at the far end by his chair (the source's Throne of Legends, hover only).
  The crypt of the dragons: a ribbed vault 2,304 × 1,536, 1,024 high.
- **Traps with tells.** The Swinging Death: four pendulum blades (rotating movers swung by a map timer) over a run
  1,280 × 384; the Chopping Death: three blades dropping from ceiling slots (linear movers on a timer). The blades are
  the tell, in plain sight from 3 m. A step plate under each blade's arc deals about 12 % of a level-59 member's HP
  once per crossing. Each run's carved mask (`egywlspb`) sells protection (DECIDE 3).
- **Dragons.** Dragon Mummy bodies about 512 high, radius about 300 (D-32, `levelRadiusLimit: 60`): the crypt is 1,024
  high; its only way out is the steps' arch, 384 high and 384 wide, so they stay in. The stalls open off the crypt
  through a wide, high opening (dragons in both); the two alcoves at their end are 256 high.
- **Monsters and treasure.** Ghost Mummy 62 × 16 (A2's new tier, e.g. 11273; the body), Phase Mummy 72 × 4 (new tier,
  e.g. 11274; the galleries), Dragon Mummy 65 × 6 (11672; the crypt and stalls). 26 monsters, **31.07k per member**
  (124,290 / 4). MAPS §0 gives FD-01 and FD-02 together 60 at 55–80 and 68.0k: by count FD-02's share of 26 is 29.47k
  (+5.4 %), leaving A8's FD-01 34 monsters and 36.93k (an average level of about 61; DECIDE 1). Picard is peaceful,
  placed-only, uncounted and unkillable (the load event's `SetMm9ActorCanReceiveDamage(false)`, as D-51 and D-56).
  Chests T6 × 3 (the two great sarcophagi behind a Might check, DECIDE 4; the embalmer's chest). Two fixed T6 finds in
  the galleries (A2). Rest encounters 10 % Ghost Mummies (DECIDE 7).
- **Original lines.** aazex125:0–2 signs ("Preservation Room", "Home of the Aged"); :3 the exit's meaning; :4–5 the
  sarcophagi; :9–15 the masks (sums rescaled); :16, :18–19 the name; aazex126:10 the chair's hover, :13–17 the books;
  aazex127:2–9 the runes, the stair's plaque and "Don't feed the dragons." at the crypt steps; :14 the illusion. To the
  ledger only: the embalming fluids, "+2,000,000 exper.", the Super Dragon Embalmer and "+5 levels perm"
  (aazex125:6–8, aazex127:12–13). Picard's topic lines (aazex126:0–9) are A3's.
- **Door to X6.** `door:fd02` (A5, built, listed only until FD-02 exists): two leaves (`egydrlgl`, 160 × 256 each) in
  the breast's east face of `thing:southern_sphinx` (cells 34–40, 82–86, ground 1,536), `m40.sphinx_door` (Roland's
  amulet 12372). **Inside arrival proposed:** `entrance:x6_door`, on the first step about 256 inside the leaves, facing
  west (1024) down into the body. The way out is the exit preset ("Exit the Southern Sphinx?") to X6's
  `entrance:fd02_door` (−12800, −10240, 1536) facing east (0).
- **Hooks.** `m40.runes` (both Preservation Rooms, the sixth stone); `m40.name_right` / `m40.name_wrong` (the stair of
  the name: the top landing's plate on every climb until named, and the door's click); `m40.stair` (the door of the
  name, open on every load with `name_said`); Picard's topic (npc 5704, the Home of the Aged); `m40.sphinx_door` is
  X6's (A5).
- **Map qbits 118110–118119.** 118110–118115 the six runes read; 118116 Swinging Death protection paid; 118117 Chopping
  Death protection paid; 118118 the illusion heap gone; 118119 spare.
- **Textures.** MM6 Tomb of VARN (`pyramid.blv`) upper, as A6 assigns, read apart from XD-15 by the set's other half:
  `egywlh` with `egywlhle`/`egywlhre`, `egywlj`, `egywalg1`, `egywalgm` and `egywld` over `egywla` footings, `egyflorf`
  and `egyflord` floors with drifted sand at the doors, `egyceila`/`egyceild`, `egytrma`/`egytrmas`, `egydrsmd` and the
  `egydrlgl`/`egydrlgr` pair, `egymedb` over the door of the name, `egywlspb` for the masks; no striped `egycol64`
  columns, no `egywle`/`egywlc` (XD-15's marks). 2 new (`xsshelf`, `xsrunes`; one picture for all six stones, the letter
  in the text). About 24 of 30.

**DECIDE items (FD-02)**
1. **FD-02's share of FD-01 + FD-02.** (a, proposed) 26: Ghost 62 × 16, Phase 72 × 4, Dragon Mummy 65 × 6 = 31.07k;
   FD-01 keeps 34 and 36.93k; (b) 30: Ghost 18, Phase 4, Dragon Mummy 8 = 35.74k, FD-01 30 and 32.26k; (c) 20: 23.95k,
   FD-01 40 and 44.05k. Depends on A8 (FD-01's graph) and A2 (recount).
2. **Mummy tiers at the band.** (a, proposed) two new pyramid_mummies tiers, Ghost Mummy 62 (Age) and Phase Mummy 72
   (DrainSP), MM9 mummy recolours; (b) existing rows: Royal Mummy 65 × 16, Dragon Mummy 65 × 6, Undead Dragon 55 × 4 =
   30.39k; (c) Pyramid Guard 52 under the band. Evidence: XEEN_SYSTEMS (Ghost Mummy ×17, Phase Mummy ×4 in the source;
   Tomb 42 and Guard 52 under 55–75). Depends on A2, S.
3. **The toll masks.** (a, proposed) each mask sells its run's protection for 2,000 gold (the blades stop for good; No:
   "Begone, then!", no throw into the blades as in the source); then a "clue" for 500 more: "There's one born every
   minute."; (b) protection only; (c) no masks, traps and tells only. Depends on A3 (lines, sums), A2 (gold ledger).
4. **The great sarcophagi.** (a, proposed) Might ≥ 60 on the clicking member, potions and spells counting (XD-15's 40
   at 31–34, D-39 Q4, scaled); (b) no check.
5. **Reading apart from XD-15.** (a, proposed) the pyramid set's other half, no stripes, drifted sand, 2 new (`xsshelf`,
   `xsrunes`); (b) MM7's bookcase `7t1books` in the library (a second family in one room); (c) as XD-15.
6. **Picard's chair.** (a, proposed) his very good chair hovers "Throne of Legends", no reward (XD-15 already has a
   throne of legends with lecterns); (b) a separate throne, +2 once per character; (c) the line to the ledger only.
7. **Rest encounters.** (a, proposed) 10 % Ghost Mummies (D-47's rule); (b) 0.

**Requests to other lanes**
- A2: Ghost Mummy 62 and Phase Mummy 72 tiers in 11270 (e.g. 11273–11274, DECIDE 2); a peaceful placed-only row for
  Picard (npc 5704, `move: stand`, NoArena, not counted); row 9180 (encounter 10 % Ghost Mummy, treasure 6); two fixed
  T6 finds (the galleries: two potions, a gem); the Might 60 check and the toll sums in the Act VI ledger; the FD-01 +
  FD-02 recount (DECIDE 1).
- A3: the rune stones' text as the source's lessons (aazex127:2–7) instead of "A rune: P"; map-local lines and
  ORIGINAL_LINES rows for aazex125:0–5, 9–19, aazex126:10, 13–17, aazex127:8–9, 14 (the masks' sums rescaled); the
  ledger rows for the dropped fluids, XP and levels; `m40.name_right`'s `where` to name the top landing and the door.
- A4: nothing (5704 is placed as `towns/fd02.yml` says).
- A5: X6's `door:fd02` arrival `entrance:x6_door`; confirm `entrance:fd02_door` (−12800, −10240) stands clear outside
  the leaves (the playtest stands the party at x −11981 before the breast); unseal the door when FD-02 installs.
- A6: a dungeon_families accent line for FD-02 (the pyramid set's other half); register `xsshelf` and `xsrunes`.
- S: Picard's look as a recolour of an installed MM6–MM8 old scholar (no Meshy), after portrait npc 5704; two mummy
  tier skins on the MM9 mummy; the chair decoration.
- A8 / orchestrator: FD-01's remainder (34 monsters, 36.93k) if DECIDE 1 (a).
- AU, A1: nothing required (shipped sounds; doors, rotating movers on timers, step plates, text prompts, talking
  monsters and the load-time damage word all exist).

**State and next steps.** Graph, picture and notes written 2026-11-21 (phase 6, graphs only; nothing built or
installed). Next: the decider answers the DECIDE items, then L1.
