# XD-23 Troll Warren: L4 notes

Lane A7 phase 3 (agent `xeen-a7-xd23`), 2026-11-20. Map 9146, `xeen_xd23.blv`, class S, `world: xeen`. Built from the
MU-6 graph `devdocs/xeen/mockups/act3_graphs/xd23.graph.yml` with D-25 (`mockups/act3_a7_decisions.md`), which wins:
the burn shows one message (A3's hook), the smoke is a capped mist, the chimney exit stays. Generator:
`output/studio_cal/xd23/tools/gen.py` (writes L1-L4; never hand-edit the written files); cycle
`output/studio_cal/xd23/cycle.sh`; playtests `output/studio_cal/xd23/play.sh <name>`; tour `output/studio_cal/xd23/shots.sh`.

## What was built

Tunnels under X5's barrow mound in the Troll Forest, three floors down to the Troll Matron's hearth. x east, y north;
the mouth's exit wall is y 0 (X5's mouth faces north, so the warren runs south into the mound).

| Room | Floor | Size | Monsters (placed, group) | What |
| --- | --: | --- | --- | --- |
| Warren mouth | 0 | 640 × 768 | 2 Troll (10) | Start; the dragged-aside barricade; snow exit north; hide flap west |
| Gnawing hall | 0 | 1,280 square, domed | 4 Troll (11) | Gnawed bark piles (one clicked: aaze0007:6), bones |
| Larder | 0 | 1,216 × 768 | 3 Troll (12) | Hung hides, carcasses (step line); the crawlway down |
| Tunnel down, Crawlway | 0 → −512 | 256 / 224 wide, 1,024 long | — | The two ways down (the upper loop) |
| Cold spring | −512 | 1,024 × 1,280 | 2 Troll, 1 Troll Guard (13) | Meltwater pool (wtrtyl, water); the slope west |
| Sleeping hollows | −512 | 2,304 × 1,664, domed | 5 Troll (14) | Five straw beds, a bark pile, two hung hides |
| Rock store | −512 | 640 square | 1 Troll Guard (15) | Dead end; aaze0008:2's second sentence; the hunter's pack (T3) |
| Slope down | −512 → −1,024 | 256 wide | — | West then south to the guard tunnel |
| Guard tunnel | −1,024 | 384 wide, 4,096 long | 3 Troll Guard (17) | South, then east to the hearth's hide curtain |
| Whelping den | −1,024 | 1,024 × 960 | 4 Troll (16) | Behind a hide curtain; the young trolls' nest; shiny things (T3) |
| The Matron's hearth | −1,024 | 1,792 × 1,408, domed | 2 Troll Guard (18), the Troll Matron (19) | Her straw bedding, bark, hides; her hoard (T4) |
| Smoke chimney | −1,024 → 384 | 768 × 640 | — | Fire pit; the hide plug 480 up; the root ladder (1,024) on its east wall |
| Smoke hole | 0 | 640 × 512 | — | The ladder's top; the one-way exit east (snow) |

**Counts and sizes.** 14 rooms (the build's 15 sectors count the BLV's sector 0), about 15.3 M units² of floor, 806
faces, 28 monsters (20 Troll 11070 at 18, 7 Troll Guard 11071 at 28, the Troll Matron 11074 at 32; Ice Troll left
out), 3 chests (T3, T3, hoard T4), 3 doors (the hide flap and two hide curtains, all destructible). Kill XP per member
L(L+10)/4: 20 × 504 + 7 × 1,064 + 1,344 = 18,872 / 4 = **4.7k** (the graph's 4.7k). Monsters all placed (one group per
room, so the burnt stage hides them; a hit wakes only that room's trolls).

**Textures.** 16 distinct (15 on faces at load + xochar by event), 0 new: 7dirttyl (X5's mouth shell, MM7 dirt cave:
walls, roofs, floors), straw (beds, the hollows' and the den's floors), xohide (curtains, hung hides, the plug), xdbark
(bark piles, D2's), xoburn / xochar (XD-05's fire and char), wtrtyl (the pool), snow (both exits, as XD-10's mouths),
t66abc10a (the root ladder), the plain chest set ch1* (7). Cap 30.

**Monsters' rows.** A2's Trolls rows and the Matron's boss row (D-25 Q4: 32, look B, frenzy below half health) exist;
the trolls' model is the family's stand-in (they read as green goblin-like trolls in the pictures: A2/S's).

**Map card.** Music 8; environment cave; treasure 3; lock 6, trap 3, perception 6; refill 672; bolster LowerToEqual;
**encounter 0** (no rest encounters: the burnt warren must stay empty, which a rest encounter would break); slot 1
`Xeen Troll`, tier 1, [2, 3], weight 100 (for the card only). Test row 9146 in the scratch root's map_stats.txt and
bolster_maps.txt (copied from 9149's) until A2 writes it.

## The burn (D-25 Q5, "Other items")

- **Kill timer** `evt:matron_dead` (every 2 s, `kills: monster:matron`, once; XD-05's method): map variable
  `matron_dead`, map qbit `matron_dead` 110930, the line "The Troll Matron falls. Her fire still burns in its pit under
  the chimney."
- **The question** `evt:fire_pit` (the pit under the chimney, "Fire pit"): before her death "The trolls' fire burns in its
  pit. The Matron is near."; after it the source's whole line (aaze0008:2) in the question's window, "Destroy
  (Yes/No)?"; No: "You leave the lair as it is, for now." (asked again next click). Yes:
  1. `XeenQuests.hook("q-c15.lair")`: sets `q-c15.lair_burnt` 112301 and shows A3's one message ("You burn everything
     you can, and what you cannot burn you throw outside. The warren fills with smoke, and the trolls that are left
     will not come back to it."). The map adds no message of its own.
  2. `evt.DamageDestructible(n, 1000)` on all 16 burnables (7 straw beds, 6 bark piles with the mouth's barricade, the
     3 hide doors): wood breaks with its sound and splinters.
  3. `evt.DestroyDestructible` on the chimney's hide plug (trigger-only: blows cannot break it before).
  4. The hearth's two hide panels and the pit blaze (xoburn, two pulsing fire lights, the "raging fire loop" sound);
     the other hung hides charred (xochar); the trolls' fire light and its campfire sound off.
  5. `evt.SetMist(1, 60)`: the smoke drawn in over a minute (map variable `smoke` 1 mirrors it for the playtest).
  6. `evt:burn_out` 4 s later: the hearth's hides and the pit charred, the blaze off, embers on.
- **Smoke mist** (atmosphere.yml): one grey layer over all three floors (colour 118/116/114, base 320, falloff 300,
  visibility 1,500, at most 60 % cover, no daylight follow). At the player's 100 % a lit wall 1,500 away is about 38 %
  covered (52 % at 200 %): visible (pictures 24-26). `evt:smoke_clear` draws it at 0 on **every** load.
- **Burnt stage** `evt:stage_burnt` (load, `q-c15.lair_burnt`): every troll group hidden (10-19), every destructible
  broken again in case (they stay broken in the map's saved state anyway), all hung hides and the pit charred, the
  trolls' fire out, no smoke.
- **The chimney**: the root ladder is there from the start (rungs on the east wall); before the burn the hide plug (a
  solid platform 480 over the pit) stops the climb. After it the ladder climbs 1,024 to the smoke hole.

## Exits (D-24: `exit` preset, the game's leave window, no question)

- **Mouth, both ways** → `exit:x5_mouth` arrival **(768, −14595, 1210)**, facing north (90): 400 north of X5's
  `thing:warren` mouth face (768, −14995, 1336; `oymap things` on X5, event 109), facing away from it. Cells [65.5,
  94.5] give the mound's middle (768, −15616) by X3's convention; the mouth face lies 621 north of it (turn 180).
- **Smoke hole, out only** → `exit:x5_crown` arrival **(768, −15616, 1645)**, facing south (270). **PROVISIONAL** until
  A6 gives the point: over the mound's middle, 256 south of its crest, facing away from the mouth and the smoke hole;
  clear of X5's troll encounter circles (the nearest, (64, 100) and (71, 93), are 1,800+ away).
- **X5's `into` (A6)**: the map's start, **(0, −256, 0) in room:mouth, facing south (270)**, just inside the mouth
  (the snow exit behind).

### Measured heights (2026-11-20, dropping the party on X5 from 1,500 / 3,000)

| Point on X5 | Ground |
| --- | --: |
| (768, −14595), 400 in front of the mouth | 1,200.8 (arrival 1,210) |
| (768, −15616), the mound's middle (crown arrival) | 1,635.1 (arrival 1,645) |
| (768, −15360), the crest | 1,696.9 |
| (512, −15616) / (1024, −15616) / (768, −16128) | 1,610.6 / 1,594.6 / 1,372.8 |

`playtest_exit.yml` lands at 1,190-1,215 and 1,625-1,650 and stays there 2-3 s later.

## Original lines

- "The stench of this cave tells you that Trolls have been living in it." (aaze0008:2, first sentence): the mouth's
  line on arrival (a one-shot timer, since the party arrives standing in the mouth; the brief's "step message").
- The whole aaze0008:2 as the burn question's message ("... Destroy the lair?").
- "They gnaw on our bark to sharpen their teeth in a most uncivilized fashion. Friends don't gnaw on friend's bark."
  (Thickbark, aaze0007:6) on the gnawed bark in the gnawing hall (a clicked line in a window).
- "This hollow is filled with things that Trolls find valuable: bones, fist-sized rocks and hides." (aaze0008:2, second
  sentence, adapted) as the rock store's step line.
- aaze0008:3 "You burn everything you can ..." is shown by A3's hook.

## Checks (scratch root `output/studio_cal/xd23/root`, binaries of merge point 11)

- `oymap fmt --check`, `validate` (L1-L4), `build` (0 warnings), `audit --reach --solve` (no error or warning; infos:
  the ladder poles' squashed texels, the AmbientSound and smoke variables written but never read by a handler).
- `playtest.yml` 118 steps, `playtest_hostility.yml` 24, `playtest_exit.yml` 20: 4 of 4 each
  (`output/studio_cal/xd23/four.out`, logs in `output/studio_cal/xd23/a7_xrun/`).
- Pictures `output/studio_cal/xd23/shots/` (sheets `sheet1-3.jpg`): unbaked (flat light; the lead bakes).

## Words needed

- No word for a ladder that is closed until an event (the plug is a solid platform that stops the climb).
- No scenario read-out of the scripted mist share: the playtest checks the map variable `smoke` set beside
  `evt.SetMist`.
- A wall panel cannot be a destructible that leaves wall behind (its faces vanish into the void), so the hung hides
  char (set_texture xochar) instead of burning away; the beds, bark and curtains are platforms and doors.
- `rough` walls cover an `exits` face on the same wall (the mouth's snow exit vanished behind them): the mouth has no
  rough walls.

## Dressing exceptions

None (audit clean). Beds, bark piles and the fire pit are low platforms by the walls or in the chimney; containers
none (trolls keep none).

## DECIDE

1. *Rest encounters.* Encounter chance 0, so the burnt warren stays empty. Option: 10 % like other dungeons (rests
   then spawn trolls in the burnt warren). Default 0.
2. *Charred hides.* The hung hides become black xochar panels after the burn (read a little like holes in the
   pictures). Options: keep; a new soot-on-dirt texture (1 of the 4 allowed); hides as thin destructible slabs in front
   of a soot panel. Default keep.

## For the user

- The burn: kill the Matron, click the fire pit, answer Yes; the hides blaze, the smoke thickens for a minute, and the
  chimney's hides are gone: climb the roots to the smoke hole. Come back in by the mouth: charred, empty, no smoke.
- The upper loop: the larder's crawlway and the gnawing hall's tunnel both reach the sleeping level.

## Sixth session (2026-11-20, lane A7)

- **D-33 (6):** the hung hides (`panel:hides_sleep_s`, `panel:hides_sleep_w`, `panel:larder_hides`) turn to the new
  `xosoot` in the burn and the burnt stage (smoke-blackened hides, Codex, `level_generation/textures_xeen/a7_xd23_soot/`,
  refs `xeen/xohide` and `mm7/7dirttyl`; installed in `assets_dev`, master in `assets_source/worlds/xeen/textures_x4/`;
  A6 to register); `xochar` stays on the fire pit and the hearth's hides. Textures 17 (1 new).
- **Texture fit:** the hide picture (pole along its top) tiled twice down the 320 and 416 high panels; those panels now
  take it at scale 1.25 and 1.625, once top to bottom, repeated only along the pole.
- **Lamp rule:** `light:chimney_top` stood 420 above the chimney's ceiling (its height is over the highest floor under
  it, the plug's top at -496): height 836, z 340, under the chimney's top. Clean under A1's audit.
- Pictures `output/studio_cal/xd23/s6soot2/` (before and after the burn; the tour's console stage does not hide the
  trolls, the playtest does).

## Texture fit (2026-11-20, merge point 16)

A1's `textures.*` check flagged 17 errors, all `feature_repeated` on `xohide` (one patchwork hide on its pole, a
picture meant once): the five hung-hide panels showed it 2.4-3.7 times along the wall (the sixth session fitted them
top to bottom only), the chimney's plug 5.8 x 2.4 on its underside and top and 4.8-5.8 times along its 48-high sides,
and the three curtains' folding leaves (192 wide) 1.5 times across. Changed in `gen.py` (no new texture: 17 of 30):

- **Hung hides:** every hide is its own panel, the picture laid once over it (`fit: true`, `uneven: true`), about half
  as wide as it is high, with the dirt wall between neighbours (`hides()`): larder 3 x 136 x 256 (gaps 40), sleeping
  hollows south 3 x 160 x 320 (gaps 32) and west 2 x 160 x 320 (gap 64), the hearth north 3 x 224 x 416 (gaps 48) and
  south 2 x 224 x 416 (gap 64). The first panel of each wall keeps the old id; the others are `<id>_2`, `_3` (ids.lock
  24-31). The burn's and the burnt stage's `set_texture` lists are read from the panels (`panel_ids()`), so every hide
  smokes (`xosoot`, 128 x 256 like `xohide`: the fitted panels show it once too) or blazes and chars (`xoburn`,
  `xochar`: tiles).
- **Curtains** (larder flap, whelping den, hearth): two leaves that part sideways (`slide_left, leaves: 2`, no fold),
  each one whole hide stretched over its 96-wide half, the right one turned over (`pictures` with `mirror`); the leaf
  ends in bark (`edge_surface: xdbark`). A folding leaf lays its picture at its own size (128 on 192: 1.5 copies) and
  the doorways stay 192 wide (the trolls are 160 across). The hearth curtain's leaves are 96 x 288 (the hide stretched
  1.1 down, no longer its pole again at the foot). Doors 3, leaves 6 (`.leaf2` 4-6); the destructibles break both
  leaves (they share the door's cog).
- **The chimney's plug:** bark (`xdbark`) on its sides, top and underside, as the mouth's barricade ("frozen hides and
  gnawed poles"; its click line says so now). A platform's top and underside are laid from the map's origin like a
  floor and take no `fit`, so the hide picture cannot lie once over the 736 x 608 underside.
- Faces 806 -> 849. Audit (`oymap audit`, and `--reach --solve`): no error, no warning; build 0 warnings.
- Playtests from `output/studio_cal/xd23/root`: `playtest` 118/118, `playtest_hostility` 24/24, `playtest_exit` 20/20,
  4 of 4 each (`output/studio_cal/xd23/s8fit/four.out`).
- Pictures before and after (same poses, the trolls stand where the tour freezes them):
  `output/studio_cal/xd23/s8fit/compare1.jpg` (hung hides, curtains), `compare2.jpg` (a curtain's back, the plug, the
  burnt stage's smoked and charred hides); single shots in `s8fit/before/` and `s8fit/after/`.

### Texture fit exceptions

None.

## chest.front (2026-11-22, lane A7 twenty-seventh session)

The build's `chest.front` warning (merge point 41: an indoor chest's `facing` is its long axis, its front 90 degrees
anticlockwise of it): the chest(s) it named turned 180 degrees in place, back to the wall, front to the room.
Installed with the bake; build warnings and audit as before.

## D-89 cave shape, identity and name test (2026-11-22, lane A7 28th-29th sessions)

Shared pass `tools/xeen/cave_shape.py` (corners cut where no other room, object or numbered wall is near, `rough` walls,
floor points that rise and fall with everything standing pinned level, vaulted roofs), called from this map's generator
after L4 is written; `identity:` in project.yml. Metrics are `oymap metrics`' cave_shape (floor uneven share, ceiling
spread, rough wall share; the audit's numbers 0.30 / 80 / 0.18). `tools/xeen/check_identity.py <key>` checks the family
share and the shape of the installed map.

- Metrics before -> after (floor / ceiling spread / rough): 0.17 / 149 / 0.28 -> 0.45 / 154 / 0.30; family d13 86 % (was
  0 %: 7dirttyl).
- Identity: the assigned family MM8 d13 (the troll home) as d13 uses it: `gtrlwal1` walls 128 x 256, `gtrlrf3` roofs,
  `gtrlflr` floors (the d13 BLV: rf3 on 2,822 ceiling faces, wal1 on 798 walls, flr on 403 floors); hides, straw, bark,
  bones and the fire's char unchanged. Shape: every cave room but the tunnels with slopes, the chimney (plug, root
  ladder) and the smoke hole; the spring keeps its south-east corner (its opening into the hollows takes 384 of 512);
  the guard tunnel rough (`path_rough`). 12/12.
- Name test (arrival, first fight room, signature room), engine captures from `assets_dev` in
  `output/studio_cal/a7/s29/names/xd23/shots/`  (01-1_arrival.png, 02-2_gnawing_hall.png, 03-3_sleeping.png,
  04-4_hearth.png); all eight maps on one sheet `output/studio_cal/a7/s29/names/names_sheet.jpg`. Reads as a troll home:
  trolls at the mouth, straw beds and hides in the hollows, bones and bark, the Matron's hearth. d13's masonry walls and
  plank roofs read built rather than dug (that is the family's own look); see DECIDE in the lane file.
