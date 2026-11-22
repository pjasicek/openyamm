## FD-03 Darkstone Tower

X5 · M · party 60 → 63 · 62–85, Onyx Golem 85 (MAPS 60–85) · 45 · treasure 6 · M41 (the gongs, the seal)

![FD-03](act6_graphs/fd03.svg)

The source's four levels (dark mazes 113–116) as one BLV of four storeys 768 apart (z 0, 768, 1,536, 2,304) and the
roof stair's head at 3,072. 26 review rooms, about 30 sectors (the four rotundas two each), about 38 M units², 11 doors.
**The interior is larger than X5's shell, said plainly:** outside the tower's base has radius 544 (896 high plus the
frieze) and its top storey 448; inside, each storey is a round plan of radius 2,048 (4,096 across), as XD-14's and
DD-07's interiors (D-39 Q6/Q7). Each storey: a rotunda (radius 896, 640 high) round an open well (radius 384, a parapet
192 high) that runs from L1 to the top, a ring gallery in two arcs, a side room and a stair flight round the outer
wall, alternating south and north.

- **What it is.** The last dungeon of the main story (P5 has no monsters, D-56 Q2). "No Sound No Ground!": on each
  storey a gong must be rung before the next flight has its top. On the top storey the Onyx Golem guards the roof
  stair, whose foot the invisible seal closes until the Chime of Opening breaks it; the stair leads to the Clouds of
  the Ancients (P5).
- **Critical path.** Door hall (`entrance:x5_door`, quiet); an arc; the L1 gong (`m41.gong_voice`); the south stair;
  L2's landing, an arc, the gong, the north stair; L3's landing, an arc, the twin gongs, the south stair; L4's landing,
  an arc, the hall of the skull (the Onyx Golem); the foot of the roof stair (`m41.seal`, the Chime); the roof stair;
  the roof stair's head and the exit to P5.
- **Off the path.** The onyx forge (L1, T6), the mason's library (L2, T6), the rain cistern (L3, T6, sunk 128 with an
  edge to step out of), the skull's vault (L4, T6 behind the force); the second arc of every storey (the plaques).
- **Loops (4).** Round each storey's rotunda by either arc (L4: into the hall of the skull by its two leaves or the
  open north side).
- **Set pieces (2).** The gong well: the rotundas round the open well, a bronze gong (`xngong`, XD-03's) on the wall;
  rung, the voice booms and the missing landing of the next flight grinds up out of the dark; from L1 the raised
  landings are seen stacked up the well. The seal: a tall room under a shaft of cloud light, the roof stair's mouth
  closed by a translucent leaf rippling like heat (DECIDE 8); the Chime's note cracks it like ice (A3's text).
- **The gongs (DECIDE 2).** Each flight (24 steps of 32) ends 640 short of the storey above at a dark slot. The ground
  is a 512 × 512 slab (a door mover) sunk below. A gong's click calls `m41.gong_voice`, shows the gong's two hidden
  guards in the wall niches beside it (DECIDE 3), and raises the slab into place (map qbits 118120 L1, 118121 L2; L3's
  twin gongs lift it 320 each, 118122 and 118123). The top step's plate gives the voice's line (aazex113:2, map text)
  before the gong, so the party knows what is missing. **The ground stays raised once rung** (D-56): the load event
  raises every slab whose bit is set. They are qbits, not map variables, so a rebuild of the map does not drop them, and
  a party that fell from P5 to X5 walks straight back up (the seal is open by `seal_broken`).
- **Monsters and treasure.** The source's onyx golems: Onyx Sentry 62 × 20 and Onyx Warden 72 × 16 (A2's new ordinary
  tiers, e.g. 11585–11586, recolours of `xgol_e` on `xeen_m254`; DECIDE 1), Sky Golem 75 × 8 (11594) on L3–L4 where the
  cloud light comes down, and the Onyx Golem 85 (11584, the boss row) once, the source's L4 "+1". 45 monsters, **60.70k
  per member** (242,819 / 4) against 58.9k (+3.1 %). By storey: L1 10, L2 10, L3 12, L4 13; 8 of them are the gongs'
  hidden guards (always met: every gong must be rung). Golems are about 300 high: the 640 rotundas and 384 openings fit
  them; none flies. Chests T6 × 4. Rest encounters 0: every row is a construct (D-47: never a construct).
- **Original lines.** aazex113:0 the exit's meaning; aazex113–116:1–2 the gongs and the voice (A3's hook); the plaques'
  rows aazex113:3–6, aazex114:3–6, aazex115:3–6 and L4's heads aazex116:3–6; :0 "A force repels you." at the vault;
  :7–8 the seal (A3's texts); :15 "The skull is silent." The skull's riddle (:9–14, answer 120) and the Gold ID Card stay
  in the ledger (A3 dropped the riddle). Read down the columns, the plaques say "NEW WORLD THANKS YOU FOR PLAYING MIGHT
  AND MAGIC" (L1), "SO END THE SAGA OF CORAK AND SHELTEM!" (L2), "1994 BEGINS THE NEXT MIGHT AND MAGIC SAGA!" (L3) and
  "TYPE "COMPUTER" ON LEVEL 4 OF THE DUNGEON OF DEATH. SEE YA SOON!" (L4's heads; FD-04's terminal, DECIDE 4).
- **Door to X5.** `thing:darkstone` (A6, built, sealed today with "Darkstone Tower is not open to you yet."): the door
  on the base's north face, front about (−4608, 2060, 1500) facing north, the tower centred at (−4608, 1536) on the rock
  top (1,500), `m41.tower_door` (`m39.darkstone_key`). X5 has no neighbour line for FD-03 yet. **Inside arrival
  proposed:** `entrance:x5_door`, in the door hall about 256 inside the door, facing south (1536) into the tower. **Return
  point proposed:** X5's `entrance:fd03_door` at (−4608, 2304, 1500) facing north (512): the spot of D-56's
  `entrance:p5_fall`, turned away from the door (768 of flat rock to the rock's north edge).
- **The roof (D-56).** The roof stair's top step is **`entrance:p5_stair`, facing down the stair** (P5's stair house:
  "Descend into Darkstone Tower?", aazex129:14). The hatch over the roof stair's head (`sky: true`, P5's cloud sky,
  DECIDE 7) is the exit preset up to P5's **`entrance:fd03_roof` (4608, −3968, 0) facing 512**. Nothing in FD-03
  changes for P5's stair house, which copies X5's crown.
- **Hooks.** `m41.gong_voice` (the gongs of L1, L2 and the twin gongs of L3); `m41.seal` (the seal's leaf, clicked or
  walked into: with the Chime it takes it, sets `seal_broken` 111820, 27,000 XP, and the leaf opens in the same visit
  and on every load); `m41.tower_door` is X5's (A6).
- **Map qbits 118120–118129.** 118120–118123 the grounds (L1, L2, L3 west and east halves); 118124 the vault's field
  down (the Onyx Golem dead); 118125–118129 spare. The plaques' reading uses map variables (no lasting state).
- **Textures.** MM8 Castle of Fire d29 (A6's towers.yml): `gston1wl` and `gtrlwal1` walls (`gtrlwal1` is the tower's
  outside too), `gkp2ceil` and `gcav1flr` floors, `gston1fl` and `gcst2cel` ceilings, `gcstdoor` leaves, `gkp4-bs`
  trim; d29's lava left out. X5's `hkm3b` skull frieze once round the door hall; XD-03's `xngong` for the gong panels. 3
  new (`xdplaque` one picture for the twelve plaques, `xdhead` one for L4's four heads, `xdseal` the seal's ripple).
  About 18 of 45. Apart from DD-24's d14 (shared ceilings) and XD-23's d13 (shared `gtrlwal1`) by the black ashlar
  walls and no cave rock.

**DECIDE items (FD-03)**
1. **Rows.** (a, proposed) new Onyx Sentry 62 and Onyx Warden 72 tiers with Sky Golem 75 and the Onyx Golem 85 once:
   20 / 16 / 8 / 1 = 60.70k (+3.1 %); (b) existing rows: Lava Golem 55 × 24 (under the band), Sky Golem 75 × 20, Onyx 1
   = 55.34k (−6.0 %); (c) Alamar's robots: Annihilator 62 × 20, Autobot 75 × 16, Sky 8, Onyx 1 = 62.59k (+6.3 %).
   Depends on A2, S.
2. **The gongs.** (a, proposed) the missing landing raised by the gong (a door mover), kept by qbits at load; (b) a
   round lift in the well rung up to the next storey; (c) the gong opens a door at the stair head (DD-06's pattern).
3. **The gong guards.** (a, proposed) two hidden guards beside each gong shown by its ring (the source's summons, 8 of
   the 45); (b) all placed in sight.
4. **The plaques.** (a, proposed) the source's rows on click, and on a storey's fourth plaque one more line reading the
   columns down; no reward; (b) the rows only; (c) dropped. L4's line points at FD-04's "COMPUTER" (A7's FD-04
   sub-agent).
5. **The skull's prize.** (a, proposed) the skull silent; the vault's force drops when the Onyx Golem dies, a T6 chest;
   (b) the vault open; (c) no vault.
6. **Interior size.** (a, proposed) radius 2,048, storeys 768 apart, about 38 M units²; (b) radius 1,536, about 26 M
   units² (under M's 30); (c) radius 2,560, about 55 M units², long walks.
7. **The roof stair's head.** (a, proposed) an open hatch (`sky: true`, P5's cloud sky) and the exit preset up to P5;
   (b) a closed hatch, the same exit; (c) no landing, the top step a plain exit.
8. **The seal's look.** (a, proposed) a translucent leaf, opacity about 0.15, with a ripple texture (D-51's word), opened
   by the hook; (b) a fully clear leaf (no tell).

**Requests to other lanes**
- A2: Onyx Sentry 62 and Onyx Warden 72 tiers in 11580 (e.g. 11585–11586, DECIDE 1); row 9181 (encounter 0, treasure
  6); the Act VI recount (45, 60.70k).
- A3: the four plaque summary lines (DECIDE 4) and the roof exit's window line (the source moves the party without one)
  as map-local text; ORIGINAL_LINES rows for aazex113–116:0–8 and :15 (the riddle :9–14 as ledger only).
- A4: nothing.
- A5: P5's `door:fd03` arrives at FD-03's `entrance:p5_stair` (as P5's project already says); FD-03's roof exit lands at
  P5's `entrance:fd03_roof`; the sky preset name for the roof stair's head.
- A6: X5: a neighbour `door:fd03` → `xeen_fd03.blv`, arrival `entrance:x5_door`; the return point `entrance:fd03_door`
  (−4608, 2304, 1500) facing 512; the sealed message replaced when FD-03 installs; register `xdplaque`, `xdhead`,
  `xdseal`; confirm d29's other textures for the plan.
- S: two onyx recolour skins (Sentry, Warden) distinct from the boss's `xgol_e`.
- AU: the seal's crack (optional; shipped glass first).
- A7 (FD-04's sub-agent): L4's heads name "COMPUTER" on the Dungeon of Death's level 4; keep or note it there.
- A1: nothing required (door movers, qbits at load, hidden actors shown by event, translucent leaves, open sky over a
  BLV room, exits and named arrivals exist).

**State and next steps.** Graph, picture and notes written 2026-11-21 (phase 6, graphs only; nothing built or
installed). Next: the decider answers the DECIDE items, then L1.
