# MM9 prop placement audit (2026-11-07)

The user's play-test of 2026-11-06 found many props placed wrong: wall items, things on desks and wardrobes. This
audit compares every decoration of the built review-root BLVs with MM9's own placement, maps the error classes to
their causes and records the fixes. Tools:

- `level_generation/projects/mm9r_common/prop_audit.py [stem ...]` (numeric pass). It places each decoration's GLB
  as the engine does (binding height and z_offset, facing). It compares that with the ABC as MM9 draws it: the
  animation PropAnim.scr loops, else the first animation's first key, at the DAT Scale, full Euler Rotation and Pos.
  It writes `output/mm9_rework/prop_audit_20261107/<stem>.json`. `--props <stem>` audits what `props.json` would
  place before a convert, and `--report` rewrites the per-map tables below (keeping this hand-written part).
- `level_generation/projects/mm9r_common/prop_audit_tour.py <stem> <tour> <entity ...>` (visual pass). It writes a
  screenshot tour that frames each named decoration from a clear eye point. The captures go under
  `output/mm9_rework/prop_audit_20261107/<stem>/<tour>/`.

Columns: `fit` is the median distance (native units) of our vertices from MM9's mesh, with the bottoms aligned.
`dz` is our bottom minus MM9's raw bottom. `gap` is our bottom over the highest surface under it (BLV floors and the
other decorations' tops; negative means sunk); the bracketed value is MM9's own. `wall` is our hung mesh's distance
from its wall (negative means inside it). Flags: `turnN` (a quarter or half turn fits MM9 better), `tilt_lost` /
`misfit` (shape does not match MM9's), `floating` / `sunk` / `no_support` (a standing prop off its surface, unless
MM9 draws it the same), `off_wall` / `in_wall` (a hung prop), `height` (a hanging prop at another height than MM9's).

## Error classes, causes and fixes

1. **PropAnim quarter turns** (Anskram Keep's 28 BedMedium beds, Kluso's weapon cabinets 52 units into the wall and
   its trestle table, Drangheim City's Cabinet6/Bedmed1, Beethoven's coffin chests, Temple of Honk's
   Stonebench17). Cause: MM9 draws a prop running `PropAnim.scr` in the animation its ScriptParams name ("ns",
   "ew"), and that animation turns these models a quarter from their first animation. Only Lindisfarne and
   1000 Terrors handled it, through per-project `POSE_TURN` tables. Fix: `dungeon/prop_pose.py` poses by
   `scripted_animation()` for every map. A pose counts as a turn when at least 60 % of the mesh is the bind mesh
   turned, because the weapon cabinet's "NS" pose has its doors ajar. Both `POSE_TURN` tables are retired: the
   benches come out identical, the coffins within 8 units (the pose offset now applies).
2. **Wall shields lying flat** (30 shields in Arslegard, Drangheim, Frosgard, Guberland, Sturmford and Thronheim
   City): they stuck 40 units out of and into the wall like shelves, 40 units too high. Cause: Shield.ABC's first
   animation lays the shield down and MM9's pitch of pi/2 stands it up again. The `shieldNflat` variants were read
   against the old bake, which applied the pitch to the bind mesh and lay flat. Fix: these cities take Dook's
   Castle's hung shield1/shield2/shield4/shield3r (`TILT_OF`/`TILTS`), as Thjorgard City has since 2026-11-02.
   Arslegard's placements do not centre a hung shield on its flat bake box: that pushed the two on the diagonal wall
   14 units into it. Every audited shield is now flush (wall within 0.3, fit 2.1-2.8).
3. **Standing furniture sunk into the floor** (about 100 entries: chair03 and the desk chairs 28-36 units deep, the
   pews 36, weapon cabinets 131, Tasar's beds 43, Wizard's Lab's round table 46, Yanmir's cabinet 122). Cause: MM9
   authored these models with their base at the DAT position. Every MoveToFloor-0 instance of them in the 41 maps
   has its Pos on the floor under it, and the real MM9 shows them standing
   (`overnight/real_mm9/klusoshouse_real_3_dark_room_props.png`). Their ABC origin is at mid-height, and the old bake
   drew them at Pos plus the binding origin; its "authored floor contact" list covered only some of them. First fix:
   a per-model list `prop_pose.BASE_AT_POS` (40 ABCs at the end), which missed Thjorgard's and Thronheim's
   bookcases. **Current fix, the standing rule** (2026-11-07 evening, `prop_pose.stands_by_base` / `base_height`,
   applied by `content.props()` through `move_to_floor`, and by `prop_audit.py` as MM9's reference): every upright
   (pitch and roll under 0.05 rad) MoveToFloor-0 prop whose DAT Pos lies on a surface (at most 4 units under it,
   `BASE_FLOOR_REACH`) or at most 24 units over one (`BASE_SETTLE`; a floor, or the top of another prop under its
   footprint) stands on that surface by its base. With no surface that close under it, it hangs at its props.json
   height (wall lamps, shields, banners). MoveToFloor-1 props drop as in item 6. Refined from the data, not by name:
   a decoration that is not MM9's own model (the regions' MM6-MM8 trees standing in for MM9's, sunk as their worlds
   sink them) and a model whose ABC origin lies outside its mesh's height (Frosgard's Green Man's tree, its canopy
   661 units over its origin) keep their placement; bindings with a seat z_offset keep theirs. The data behind it:
   furniture has its Pos on the floor with the origin at mid-height (chairs 61-72 units over their base, cabinets
   120-150, the vertical sarcophagi 95); small things on shelves and tables (shelf items, mugs, stones, toy boats)
   have their Pos 5-20 over their surface (the origin at the scale-1 half height; the DAT Scale 1.5-2 sank them
   10-15 units into it). Proof against the list (2026-11-07): every map project converted twice into scratch
   (`convert.py --scratch`, the list code and the rule): all 450 MoveToFloor-0 upright instances of the listed models
   on the 28 maps with changes come out identical (a lighter placement-only pass over all 44 maps: 506 of 506), and
   417 props on 27 maps change (405 the rule stands, 12 MoveToFloor props dropping onto them; none stands under one
   rule and hangs under the other). Audit flags on the changed props, both builds against the same reference: 317
   removed (253 sunk, 44 no_support, 20 floating), one added (Dark Passageway's Prop18 bush, 6 units up on a slope
   that already rose 46 units into it); raw `gap` better for 378, the same for 31, 1-10 units worse for 7 already
   sunk 19-55 units (bushes on uneven ground, a mummy, two debris piles). Classes changed: shelf items (~140, onto
   their shelves), Chasm of the Dead's 39 vertical sarcophagi (90 units up out of the floor), stone debris (Thjorad
   Mine, the regions), Connecting Tunnels' and Tasar's candles, Dark Passageway's bushes, burning logs, cauldrons,
   oil lamps, stone benches, mugs, Frosgard City's Viking ship (on the surface under its DAT Pos; the other ships
   keep their draft: no floor within reach under them, the water is none), The Arena's two banners (onto the
   floor, their Pos 20 over it), the spike pits, Verhoffin's torture rack (84 units up out of the floor), a mine
   cart. Drangheim City's Chair28-30, whose DAT Pos is 10 units over the floor, settle onto it. Found on the way, not changed: Frosgard City's Spikes2 is a PropDamager MM9 keeps invisible
   (Visible 0, no script shows it) that we draw as a spike pit in the throne hall's fire, now standing on the floor
   (before, half of it under it); captures `prop_audit_20261107/<stem>/standrule/`.
4. **Not fixed, MM9 draws them the same** (`gap` equal to MM9's): the wall torches and tapestries 5-7 units off
   their walls. (The shelf items, sarcophagi and Thjorad Mine's debris listed here before stand since the rule.)
5. **False flags**: the mine lanterns and weapon racks 10-15 units off in plan (their binding origin; under 15 units),
   the split straw-dummy rack (l/c/r), the stat barrels and the regions' trees (stand-ins), and the seated spectators
   (their legs below the bench top).
6. **MoveToFloor surface items** (147 entries off their surface by more than 4 units: 81 floating, 66 sunk;
   Arslegard City 37, Sturmford City 15, Drangheim City 13, The Arena 11, Tasar 10). Examples: Dook's Castle's
   Cards0/1 3 units inside the round table's top (hidden), Arslegard's wine bottles 114-152 units up, and
   Sturmford's tavern cups in the air over a table that was never placed. Cause: the old transcoder dropped these
   props by their DAT dims box onto its own supports, and the props projects fit that bake. Fix:
   `prop_pose.move_to_floor()`, applied by `content.props()`; `chest_on_floor` is retired into it. It is LithTech's
   MoveToFloor: from its DAT height, each MoveToFloor decoration drops its GLB base onto the first surface under the
   lowest part of its mesh. That surface is a map floor, a mover's floor where MM9 authored it (Dark Passageway's ice
   statues on the bridges), or the top faces of a decoration placed before it. Non-MoveToFloor props stay as placed
   and are supports from the start; the dropped ones go lowest DAT height first, then by entry. The seated
   townsfolk keep the seat placement of the props projects' `seats.py`: MM9 rests their dims box, which ends at the
   thighs, on the seat, not their feet. `prop_pose.dat_name()` matches entries renamed `<name>_<index>` for a
   repeated DAT name; without it, Sturmford's tavern table (the second "Table0") was no support and its cups fell to
   the floor. Result in the built maps: of 2 886 MoveToFloor props (Tasar not rebuilt), 26 stay flagged, all false
   flags:
   - 15 seated figures whose legs hang below the bench top, and Sturmford's tavern Table (a floor edge under its
     footprint);
   - 7 overlapping rubble, bone-pile and lumber pieces (Arslegard's Prop191, Connecting Tunnels' BonePile4/5/7,
     Training Hall's Prop1/Prop5, Thjorgard's Clover2), a bucket in a pile (Drangheim Prison's Bucket6), and
     Yanmir's Bench0 (a repeated DAT name in the audit's lookup).
7. **Kept as MM9 has it**: Kluso's Prop27 shield3 hangs point up (MM9's roll 0; flush to its wall, fit 9.7).

## Reconversion and checks (2026-11-07)

The review root was reconverted (convert, lightmap transfer; heavy.sh map lanes) in four rounds: pose, shields and
base height (22 maps); MoveToFloor twice (28 maps: 1000terrors, anskramkeep, arslegardcity, bathhouse, beethoven,
chasmofthedead, connectingtunnels, darkpassageway, dookscastle, drangheimcity, drangheimprison, frosgardcity,
guberlandcity, hallofthegods, inventastorca, klusoshouse, lichlab, lindisfarnemonastery, ruinedtemple,
sturmfordcity, thearena, thjoradmine, thjorgardcity, thronheimcity, traininghall, verhoffinruins, wizardslab,
yanmirsfort); and seats plus repeated names (arslegardcity, guberlandcity, sturmfordcity, thearena, thronheimcity,
yanmirsfort). Tasar Academy waits for the full reconversion; `--props` confirms its *NS props and drops.

Scenarios of the 28 maps: all pass except 9 that failed the same way before these changes (the rotation agent's
rebuild logs or the first round): Beethoven doors_exits, Chasm scripted, Lich Lab lifecycle and scripted, The Arena
sven, Training Hall doors_exits, 1000 Terrors scripted and Arslegard njam_dead ("damage_actor could not damage
actor"), and Thronheim breakout_dead (an unknown `load_map` key `id`). Dark Passageway's scripted scenario failed
while the ice statues had dropped through the bridges; it passes since mover floors count.

Captures: `output/mm9_rework/prop_audit_20261107/<stem>/{after,v1,drop,drop2}/sheet.jpg`.

The standing rule (item 3) was reconverted into the review roots on the 28 maps with changes (convert, layout,
lightmap transfer; heavy.sh map lanes): their 118 scenarios pass except Verhoffin Ruins' scripted one, which fails
at step 59 (TortureChamberDoor0 found open) the same way with the rule's decorations left out, and passes 3 of 3 on
`assets_dev`: the review root's Verhoffin Ruins has another monster since R7 (a Terror for a Zombie, scene.yml; not
the rule's), and its regenerated scenario (make_scenarios.py: actor indices one lower) passes 1 of 3. Captures of the
sarcophagi, a shelf, The Arena's banners, Frosgard City's ship and Spikes2 and a Dark Passageway bush:
`output/mm9_rework/prop_audit_20261107/<stem>/standrule/`. drop/drop2 show Dook's
card table, Arslegard's shelves, Sturmford's tavern and desk, Drangheim City's bar and shelves, The Arena's stands
and Dark Passageway's ice statues.

## Per map (built review-root BLVs)

### 1000terrors

284 props compared, 31 flagged.

| decoration | flags | n | fit | dz | gap (MM9) | wall (MM9) | examples |
|---|---|---|---|---|---|---|---|
| mm9_treasureopening | off_wall | 9 | 0 | 0 | 154 (154) | 6 (5) | Opening0, Opening7, Opening8, Opening12 |
| mm9_sorcererstatue | misfit | 8 | 7 | -65 | 0 (66) |  () | SorceressStatue0, SorceressStatue1, SorceressStatue2, SorceressStatue3 |
| mm9_dragonpharoah | misfit | 4 | 51 | -179 | 0 (179) |  () | Dragonpharoh0, Dragonpharoh1, Dragonpharoh2, Dragonpharoh3 |
| mm9_treasureopening | no_support | 2 | 0 | 0 |  (-77) |  () | Opening5, Opening6 |
| mm9_coffinraised_x150 | misfit | 1 | 6 | -108 | 0 (108) |  () | Coffin42 |
| mm9_sconce1torch | off_wall | 1 | 2 | 3 | 485 (482) | 6 (4) | Torch19 |
| mm9_scrollp90 | tilt_lost | 1 | 12 | -144 | 0 (144) |  () | ChessNote0 |
| mm9_skulls1000a | misfit no_support | 1 | 26 | 122 |  (-252) |  () | SkeletonHead |
| mm9_skulls1000b | misfit height | 1 | 26 | 122 |  () |  (-42) | LargeSkeletonProp0 |
| mm9_skulls1000b | misfit sunk | 1 | 26 | 122 | -39 (-165) |  () | LargeSkeletonProp1 |
| mm9_switch03 | misfit | 1 | 10 | 1 | 57 (56) |  (-31) | WinMan |
| mm9_terrorlight1 | off_wall | 1 | 0 | 0 | 367 (367) | 7 (6) | CandleProp150 |

### anskramkeep

247 props compared, 8 flagged.

| decoration | flags | n | fit | dz | gap (MM9) | wall (MM9) | examples |
|---|---|---|---|---|---|---|---|
| mm9_walltorch | off_wall | 4 | 0 | -0 | 211 (211) | 5 (5) | WallTorch11, WallTorch29, WallTorch72, WallTorch76 |
| mm9_weaponrack | misfit | 3 | 13 | -55 | 1 (56) |  () | Weaponrack1, Weaponrack2, Weaponrack3 |
| mm9_scrollflat | misfit | 1 | 18 | -66 | 1 (66) |  () | Prop7 |

### arslegardcity

391 props compared, 29 flagged.

| decoration | flags | n | fit | dz | gap (MM9) | wall (MM9) | examples |
|---|---|---|---|---|---|---|---|
| mm9_plate1p80 | turn180 | 5 | 6 | 0 | 3 (2) |  () | Plate4, Plate3, Plate2, Plate1 |
| mm9_scrollflat | misfit | 2 | 18 | -106 | -0 (106) |  () | Prop84, Prop85 |
| mm9_strawdummy2c | misfit | 2 | 9 | -87 | 1 (88) |  () | Strawdummyrack1, Strawdummyrack4 |
| mm9_strawdummy2l | misfit | 2 | 116 | -87 | 1 (88) |  () | Strawdummyrack0, Strawdummyrack3 |
| mm9_strawdummy2r | misfit | 2 | 132 | -87 | 1 (88) |  () | Strawdummyrack2, Strawdummyrack5 |
| mm9_weaponrack_new | misfit no_support | 2 | 13 | -27 |  (-56) |  () | Weaponrack10, Weaponrack11 |
| mm9_weaponracknsnewg1 | misfit | 2 | 13 | -55 | 1 (56) |  () | Weaponrack2, Weaponrack3 |
| mm9_burner | misfit | 1 | 14 | -34 | 0 (34) |  () | Jacobsladder0 |
| mm9_kegbeer | misfit | 1 | 6 | -56 | 1 (57) |  () | Prop2 |
| mm9_kegbeer_x200 | misfit | 1 | 8 | -56 | 1 (57) |  () | Prop1 |
| mm9_orblinking | height | 1 | 0 | -15 | 24 (39) |  (13) | Prop3 |
| mm9_stonedebris01ls | sunk | 1 | 0 | -32 | -23 (9) |  () | Prop191 |
| mm9_tabletrestle2 | misfit | 1 | 844 | 0 | 1 (-22) |  () | Table |
| mm9_weaponrackg1_x150 | misfit no_support | 1 | 13 | -27 |  (-56) |  () | Weaponrack9 |
| mm9_weaponracknewg3 | misfit no_support | 1 | 14 | -27 |  (-56) |  () | Weaponrack8 |
| mm9_weaponracknsnewg1 | misfit no_support | 1 | 14 | -27 |  (-56) |  () | Weaponrack4 |
| mm9_weaponracknsnewg2 | misfit | 1 | 38 | -55 | 1 (56) |  () | Weaponrack0 |
| mm9_weaponracknsnewg2 | misfit no_support | 1 | 38 | -27 |  (-56) |  () | Weaponrack5 |
| mm9_weaponracknsnewg3 | misfit | 1 | 13 | -55 | 1 (56) |  () | Weaponrack1 |

### bathhouse

58 props compared, 20 flagged.

| decoration | flags | n | fit | dz | gap (MM9) | wall (MM9) | examples |
|---|---|---|---|---|---|---|---|
| mm9_towelrack | misfit | 16 | 8 | 0 | 100 (100) |  (13) | Towelrack0, Towelrack1, Towelrack2, Towelrack3 |
| mm9_scrollflat | misfit | 2 | 18 | -164 | 0 (164) |  () | Prop8, Prop7 |
| mm9_towelrack | misfit in_wall | 2 | 8 | 0 | 139 (139) | -8 (3) | Towelrack4, Towelrack5 |

### beethoven

98 props compared, 10 flagged.

| decoration | flags | n | fit | dz | gap (MM9) | wall (MM9) | examples |
|---|---|---|---|---|---|---|---|
| mm9_sconcetorch | misfit height | 7 | 7 | 8 | 169 (161) | 0 (-8) | Torch18, Torch16, Torch14, Torch8 |
| mm9_hangingbowl1 | in_wall height | 1 | 0 | -39 | 535 (574) | -7 (1) | BrazierBowl15 |
| mm9_jar04side | turn180 floating | 1 | 7 | 3 | 39 (-21) |  () | Jar7 |
| mm9_well_x100 | misfit | 1 | 13 | -16 | 0 (16) |  () | WellMMIX0 |

### chasmofthedead

312 props compared, 122 flagged.

| decoration | flags | n | fit | dz | gap (MM9) | wall (MM9) | examples |
|---|---|---|---|---|---|---|---|
| mm9_sarcophagusvert | no_support | 39 | 6 | 0 |  (-90) |  () | Sarcopen4, Sarcopen6, Sarcopen14, Sarcopen15 |
| mm9_bluesconce | height | 30 | 5 | -20 | 163 (183) | 0 (6) | Brazier10, Brazier9, Brazier56, Brazier57 |
| mm9_bluetorch | misfit height | 20 | 6 | 8 | 189 (184) | 1 (-8) | Torch1, Torch3, Torch5, Torch7 |
| mm9_bluebowl | height | 19 | 0 | -26 | 236 (262) |  (388) | Brazier0, Brazier21, Brazier1, Brazier2 |
| mm9_statueguardian | misfit | 4 | 14 | -36 | 0 (36) |  () | Statue4, Statue5, Statue8, Statue9 |
| mm9_statueguardianew_x100 | misfit | 2 | 14 | -168 | 1 (170) |  () | Statue10, Statue11 |
| mm9_statueguardianew_x50 | misfit | 2 | 7 | -84 | 0 (84) |  () | Statue0, Statue1 |
| mm9_statueguardianew_x60 | misfit | 2 | 8 | -69 | 0 (69) |  () | Statue6, Statue7 |
| mm9_pillarfallen | turn180 | 1 | 7 | -102 | 1 (103) |  () | Stand3 |
| mm9_spikepit | misfit | 1 | 13 | 112 | 0 (-112) |  () | Spikes2 |
| mm9_urn2tip1 | turn180 | 1 | 14 | 0 |  () |  () | Urn5 |
| mm9_urn2tip2 | turn180 | 1 | 17 | 1 |  () |  () | Urn8 |

### connectingtunnels

116 props compared, 59 flagged.

| decoration | flags | n | fit | dz | gap (MM9) | wall (MM9) | examples |
|---|---|---|---|---|---|---|---|
| mm9_minelantern02plain | misfit | 45 | 8 | 0 | 292 (292) |  (14) | mine lantern10, mine lantern11, mine lantern12, mine lantern13 |
| mm9_cratep356 | turn180 | 3 | 13 | 13 | 2 (-9) |  () | Prop9, Prop10, Prop12 |
| mm9_skeletonlayingprop | sunk | 3 | 1 | -134 | -9 (125) |  () | BonePile4, BonePile5, BonePile7 |
| mm9_crater355 | turn180 | 1 | 14 | -6 | 2 (11) |  () | Prop14 |
| mm9_lumberstone03p10 | tilt_lost sunk | 1 | 21 | 1 | -8 (-1) |  () | Prop4 |
| mm9_sack01p350r356 | tilt_lost | 1 | 9 | -10 | 1 (14) |  () | Prop17 |
| mm9_stonedebris01lsp350 | tilt_lost sunk | 1 | 12 | -18 | -22 (6) |  () | Prop5 |
| mm9_stonedebris02p350 | tilt_lost sunk | 1 | 15 | -24 | -34 (1) |  () | Prop8 |
| mm9_stonedebris04lsp350 | tilt_lost sunk | 1 | 18 | -23 | -34 (-1) |  () | Prop6 |
| mm9_stonedebris04lsp7 | tilt_lost sunk | 1 | 16 | -23 | -19 (9) |  () | Prop3 |
| mm9_stonedebris05lsp350 | tilt_lost sunk | 1 | 17 | -13 | -40 (-10) |  () | Prop7 |

### darkpassageway

84 props compared, 21 flagged.

| decoration | flags | n | fit | dz | gap (MM9) | wall (MM9) | examples |
|---|---|---|---|---|---|---|---|
| mm9_bush03_x300 | sunk | 8 | 0 | 82 | -54 (-108) |  () | Prop17, Prop18, Prop19, Prop23 |
| mm9_bush05 | sunk | 5 | 1 | 96 | -52 (-119) |  () | Prop20, Prop21, Prop22, Prop26 |
| mm9_stonebanshee | misfit | 4 | 12 | -33 | 0 (34) |  () | BansheeProp3, BansheeProp2, BansheeProp1, BansheeProp0 |
| mm9_crystal | sunk | 1 | 0 | -32 | -31 (1) |  () | Gemstone |
| mm9_icezombie | misfit | 1 | 7 | -51 | 0 (51) |  () | SwitchCreature1 |
| mm9_runestone | misfit | 1 | 12 | -38 | 0 (38) |  () | StoneOfFate |
| mm9_spikepit_x100 | no_support | 1 | 0 | -0 |  (-86) |  () | Spikes1 |

### dookscastle

94 props compared, 15 flagged.

| decoration | flags | n | fit | dz | gap (MM9) | wall (MM9) | examples |
|---|---|---|---|---|---|---|---|
| mm9_suitofarmor02 | misfit | 8 | 11 | -18 | 0 (18) |  () | Armor6, Armor7, Armor4, Armor5 |
| mm9_hangingbowl_x200 | in_wall height | 3 | 0 | -50 | 696 (746) | -16 (-3) | BrazierBowl19, BrazierBowl21, BrazierBowl22 |
| mm9_weaponracknew | misfit | 2 | 9 | -50 | 0 (50) |  () | Weaponrack0, Weaponrack1 |
| mm9_hangingbowl | in_wall height | 1 | 0 | -18 | 503 (521) | -6 (-4) | BrazierBowl18 |
| mm9_scrollflat | misfit | 1 | 18 | -30 | 0 (30) |  () | Prop6 |

### dragonstadium

5 props compared, 0 flagged.

### drangheimcity

198 props compared, 17 flagged.

| decoration | flags | n | fit | dz | gap (MM9) | wall (MM9) | examples |
|---|---|---|---|---|---|---|---|
| mm9_chair03 | floating | 3 | 0 | 62 | 10 (-52) |  () | Chair30, Chair29, Chair28 |
| mm9_scrollflat | misfit | 3 | 18 | -255 | 0 (255) |  () | Prop17, Prop16, Prop15 |
| mm9_tapestry_banner2 | off_wall | 3 | 0 | 0 | 283 (283) | 5 (5) | Banner4, Banner3, Banner2 |
| mm9_suitofarmor02 | misfit | 2 | 11 | -140 | 1 (142) |  () | Armor5, Armor3 |
| mm9_strawdummy2c | misfit | 1 | 9 | -88 | 1 (89) |  () | Strawdummyrack1 |
| mm9_strawdummy2l | misfit | 1 | 116 | -88 | 1 (89) |  () | Strawdummyrack0 |
| mm9_strawdummy2r | misfit | 1 | 132 | -88 | 1 (89) |  () | Strawdummyrack2 |
| mm9_weaponrackg1 | misfit | 1 | 10 | -36 | 0 (36) |  () | Weaponrack2 |
| mm9_weaponrackg2 | misfit | 1 | 10 | -36 | 0 (36) |  () | Weaponrack3 |
| mm9_well_x100 | misfit | 1 | 13 | -57 | 1 (58) |  () | WellMMIX0 |

### drangheimprison

258 props compared, 13 flagged.

| decoration | flags | n | fit | dz | gap (MM9) | wall (MM9) | examples |
|---|---|---|---|---|---|---|---|
| mm9_weaponrack_x100 | misfit | 4 | 9 | -30 | 1 (30) |  () | Weaponrack1, Weaponrack2, Weaponrack5, WeaponRack |
| mm9_weaponrackns | misfit | 3 | 9 | -50 | 1 (51) |  () | Weaponrack0, Weaponrack3, Weaponrack4 |
| mm9_axerusty_x100 | misfit | 1 | 101 | -53 | -0 (-8) |  () | Prop18 |
| mm9_bedmedium2r270 | tilt_lost | 1 | 10 | -3524 | 0 (3111) |  () | Cot5 |
| mm9_bedmedium2r90 | tilt_lost | 1 | 10 | -42 | 0 (42) |  () | Cot4 |
| mm9_bucket01 | sunk | 1 | 0 | -65 | -16 (49) |  () | Bucket6 |
| mm9_lumberstone03 | misfit | 1 | 12 | -44 | 0 (44) |  () | Debris2 |
| mm9_tapestryold01 | no_support | 1 | 0 | 0 |  (-80) |  () | Wallhanging0 |

### dungeonofsecrets

55 props compared, 20 flagged.

| decoration | flags | n | fit | dz | gap (MM9) | wall (MM9) | examples |
|---|---|---|---|---|---|---|---|
| mm9_sconce2 | in_wall height | 20 | 4 | -16 | 156 (172) | -6 (-3) | Prop2, Prop0, Prop1, Prop10 |

### frosgardcity

176 props compared, 28 flagged.

| decoration | flags | n | fit | dz | gap (MM9) | wall (MM9) | examples |
|---|---|---|---|---|---|---|---|
| mm9_herbrack1_x200 | height | 10 | 0 | 31 | 111 (80) |  (15) | Herbwallrack5, Herbwallrack6, Herbwallrack7, Herbwallrack8 |
| mm9_scrollflat | misfit | 3 | 18 | -41 | 0 (83) |  () | Prop7, Prop8, Prop9 |
| mm9_hangingbowl_x100 | height | 2 | 1 | -26 | 377 (402) | -2 (-2) | BrazierBowl23, BrazierBowl22 |
| mm9_burner | misfit | 1 | 13 | -34 | 0 (34) |  () | Burner1 |
| mm9_forge_x100 | misfit | 1 | 22 | -26 | 0 (26) |  () | Forge1 |
| mm9_runestone | misfit | 1 | 11 | -151 | 0 (151) |  () | Prop1 |
| mm9_scroll | off_wall | 1 | 0 | 0 | 100 (100) | 6 (6) | Prop6 |
| mm9_strawdummy2c | misfit | 1 | 9 | -42 | 0 (42) |  () | Strawdummyrack1 |
| mm9_strawdummy2l | misfit | 1 | 116 | -42 | 0 (42) |  () | Strawdummyrack0 |
| mm9_strawdummy2r | misfit | 1 | 132 | -42 | 0 (42) |  () | Strawdummyrack2 |
| mm9_tapestry_banner1 | off_wall | 1 | 0 | 0 | 98 (98) | 5 (5) | Banner0 |
| mm9_vikingship | no_support | 1 | 1 | 377 |  (-475) |  () | Boat0 |
| mm9_weaponrack | misfit | 1 | 13 | -14 | 0 (14) |  () | Weaponrack1 |
| mm9_weaponracknsusedg2 | misfit | 1 | 37 | -14 | 0 (14) |  () | Weaponrack0 |
| mm9_weaponracknsusedg3 | misfit | 1 | 13 | -14 | 0 (14) |  () | Weaponrack2 |
| mm9_well_x100 | misfit | 1 | 14 | -37 | 0 (37) |  () | WellMMIX0 |

### guberlandcity

248 props compared, 27 flagged.

| decoration | flags | n | fit | dz | gap (MM9) | wall (MM9) | examples |
|---|---|---|---|---|---|---|---|
| mm9_herbrack1_x200 | floating | 6 | 0 | 32 | 20 (-12) |  () | Herbwallrack5, Herbwallrack6, Herbwallrack7, Herbwallrack8 |
| mm9_suitofarmor02aged | misfit | 4 | 11 | 2 | 0 (-2) |  () | Armor2, Armor4, Armor3, Armor5 |
| mm9_chair03 | sunk | 2 | 1 | 62 | -12 (-62) |  () | Chair92, Chair93 |
| mm9_scrollflat | misfit | 2 | 19 | -158 | 0 (159) |  () | Prop5, Prop6 |
| mm9_strawdummy2c | misfit | 2 | 9 | -36 | 0 (36) |  () | Strawdummyrack1, Strawdummyrack4 |
| mm9_strawdummy2l | misfit | 2 | 116 | -36 | 0 (36) |  () | Strawdummyrack0, Strawdummyrack3 |
| mm9_strawdummy2r | misfit | 2 | 132 | -36 | 0 (36) |  () | Strawdummyrack2, Strawdummyrack5 |
| mm9_burner | misfit | 1 | 14 | -44 | 1 (45) |  () | Burner1 |
| mm9_forge_x100 | misfit | 1 | 22 | -26 | 0 (26) |  () | Forge1 |
| mm9_seamonster | height | 1 | 3 | -5 | 39 (44) | 2 (2) | SeaMonster0 |
| mm9_tapestry_banner7 | off_wall | 1 | 0 | 1 | 105 (104) | 5 (5) | Banner0 |
| mm9_weaponracknewg2 | misfit | 1 | 13 | -15 | 0 (15) |  () | Weaponrack0 |
| mm9_weaponracknewg3 | misfit | 1 | 13 | -15 | 0 (15) |  () | Weaponrack1 |
| mm9_well_x100 | misfit | 1 | 13 | -37 | 0 (37) |  () | Well0 |

### hallofthegods

41 props compared, 5 flagged.

| decoration | flags | n | fit | dz | gap (MM9) | wall (MM9) | examples |
|---|---|---|---|---|---|---|---|
| mm9_torchmetalorange | misfit height | 4 | 20 | 23 | 819 (796) |  (-24) | WallTorch7, WallTorch6, WallTorch8, WallTorch9 |
| mm9_scrollflat | misfit | 1 | 18 | -155 | 0 (155) |  () | Prop3 |

### inventastorca

101 props compared, 13 flagged.

| decoration | flags | n | fit | dz | gap (MM9) | wall (MM9) | examples |
|---|---|---|---|---|---|---|---|
| mm9_orblinking | tilt_lost | 7 | 12 | -168 | 0 (168) |  () | Prop2, Prop0, Prop1, Prop3 |
| mm9_scrollflat | misfit | 2 | 19 | -115 | 0 (116) |  () | Prop7, Prop8 |
| mm9_walltorch | off_wall | 2 | 1 | -0 | 118 (118) | 4 (4) | WallTorch167, WallTorch131 |
| mm9_bench03 | misfit | 1 | 5964 | -785 | 0 (7) |  () | Bench |
| mm9_tableround | misfit | 1 | 4306 | -53 | 1 (56) |  () | Table |

### klusoshouse

112 props compared, 4 flagged.

| decoration | flags | n | fit | dz | gap (MM9) | wall (MM9) | examples |
|---|---|---|---|---|---|---|---|
| mm9_chair03 | sunk | 2 | 0 | 62 | -12 (-62) |  () | Chair37, Chair38 |
| mm9_pew2ns | misfit | 1 | 6 | -128 | 0 (128) |  () | TemplePew17 |
| mm9_shield3 | tilt_lost | 1 | 10 | 0 | 53 (52) | -0 (0) | Prop27 |

### lichlab

178 props compared, 19 flagged.

| decoration | flags | n | fit | dz | gap (MM9) | wall (MM9) | examples |
|---|---|---|---|---|---|---|---|
| mm9_torturecage01 | height | 4 | 0 | -90 | 291 (380) |  () | Cage3, Cage1, Cage2, Cage0 |
| mm9_booktilt | turn180 floating | 3 | 13 | 1 | 10 (17) |  () | firebook3, firebook4, firebook2 |
| mm9_torturerack01 | misfit | 3 | 7 | -44 | 0 (44) |  () | Rack2, Rack1, Rack0 |
| mm9_flayingbench | misfit | 2 | 11 | -70 | 0 (70) |  () | Flayinbench1, Flayinbench0 |
| mm9_scrollflat | misfit | 2 | 18 | -277 | 0 (277) |  () | Prop16, Prop19 |
| mm9_burner | misfit | 1 | 13 | -39 | 1 (40) |  () | Prop17 |
| mm9_burner | misfit floating | 1 | 14 | -29 | 56 (1) |  () | Burner0 |
| mm9_headsmansblock | misfit | 1 | 6 | -123 | 0 (123) |  () | Block0 |
| mm9_skeletonsitting | misfit | 1 | 20 | -100 | 0 (100) |  () | BonePile1 |
| mm9_switch02 | height | 1 | 2 | -8 | 82 (90) | -1 (2) | lichswitch |

### lindisfarnemonastery

121 props compared, 13 flagged.

| decoration | flags | n | fit | dz | gap (MM9) | wall (MM9) | examples |
|---|---|---|---|---|---|---|---|
| mm9_scrollflat | misfit | 3 | 19 | -170 | 0 (170) |  () | Prop5, Prop6, Prop7 |
| mm9_walltorch | off_wall | 3 | 0 | 0 | 125 (125) | 7 (7) | WallTorch38, WallTorch41, WallTorch43 |
| mm9_walltorch | in_wall | 2 | 0 | -0 | 149 (149) | -5 (-5) | WallTorch22, WallTorch23 |
| mm9_bell | height | 1 | 1 | -54 | 4645 (4698) |  (-46) | Bell1 |
| mm9_bell_x70 | height | 1 | 1 | -37 | 4701 (4738) |  () | Bell5 |
| mm9_bell_x75 | height | 1 | 0 | -40 | 4691 (4732) | 4 (4) | Bell4 |
| mm9_bell_x85 | height | 1 | 1 | -46 | 4672 (4718) | -4 (-4) | Bell3 |
| mm9_bell_x90 | height | 1 | 0 | -48 | 1308 (1356) |  (-18) | Bell2 |

### ruinedtemple

64 props compared, 30 flagged.

| decoration | flags | n | fit | dz | gap (MM9) | wall (MM9) | examples |
|---|---|---|---|---|---|---|---|
| mm9_torchmetal | misfit height | 16 | 6 | 8 | 195 (187) | 2 (-6) | CandleProp6, CandleProp31, CandleProp10, CandleProp11 |
| mm9_torchmetal | height | 5 | 6 | 8 | 133 (125) | 2 (-4) | CandleProp33, CandleProp41, CandleProp43, CandleProp44 |
| mm9_scrollflat | misfit | 2 | 19 | -122 | 0 (123) |  () | Prop7, Prop8 |
| mm9_stonedebris05 | misfit sunk | 2 | 13 | -14 | -15 (-1) |  () | Debris2, Debris3 |
| mm9_tapestry_bannergeo3_x250 | off_wall | 2 | 0 | 0 | 52 (52) | 6 (5) | Banner5, Banner4 |
| mm9_stonedebris04 | misfit | 1 | 16 | 1 | 0 (-1) |  () | Debris0 |
| mm9_stonedebris04 | misfit sunk | 1 | 16 | 1 | -5 (-2) |  () | Debris1 |
| mm9_torchmetal | misfit off_wall height | 1 | 7 | 8 | 195 (187) | 5 (-3) | CandleProp34 |

### sturmfordcity

410 props compared, 104 flagged.

| decoration | flags | n | fit | dz | gap (MM9) | wall (MM9) | examples |
|---|---|---|---|---|---|---|---|
| mm9_lamppost4 | misfit | 25 | 35 | -1 | 0 (1) |  () | Lightpost0, Lightpost1, Lightpost3, Lightpost6 |
| mm9_hangingbowl1_x100 | height | 11 | 0 | -26 | 311 (336) | 1 (-5) | BrazierBowl12, BrazierBowl11, BrazierBowl10, BrazierBowl9 |
| mm9_beetrack | floating | 7 | 0 | 16 | 15 (-1) |  () | Beets6, Beets7, Beets8, Beets9 |
| mm9_beetrack | height | 6 | 0 | 16 | 59 (42) | -3 (-11) | Beets0, Beets1, Beets3, Beets2 |
| mm9_chandelier | height | 4 | 0 | 328 | 555 (227) |  () | Chandelier0, Prop29, Prop63, Prop66 |
| mm9_kegbeer | misfit | 3 | 6 | -17 | 1 (18) |  () | Barrel2, Barrel1, Barrel0 |
| mm9_peasantms2csitting | floating | 2 | 6 | -56 | 10 (12) |  () | CommonerHumanMaleA5, CommonerElfFemaleA1 |
| mm9_scrollflat | misfit | 2 | 18 | -60 | 0 (61) |  () | Prop3, Prop7 |
| mm9_shieldrustyp90 | tilt_lost | 2 | 20 | 0 | 136 (136) | -1 (-1) | Shield, Shield0 |
| mm9_strawdummy2c | misfit | 2 | 9 | -5 | 1 (6) |  () | Strawdummyrack4, Strawdummyrack1 |
| mm9_strawdummy2l | misfit | 2 | 116 | -5 | 1 (6) |  () | Strawdummyrack3, Strawdummyrack0 |
| mm9_strawdummy2r | misfit | 2 | 132 | -5 | 1 (6) |  () | Strawdummyrack5, Strawdummyrack2 |
| mm9_barrel_x100 | misfit | 1 | 10470 | -604 | 0 (25) |  () | Barrel |
| mm9_barstool1 | misfit | 1 | 357 | 0 | 0 (-45) |  () | Stool |
| mm9_basketveggies | misfit | 1 | 11474 | -573 | 0 (-22) |  () | Basket |
| mm9_bedmedium_x100 | misfit | 1 | 4052 | 510 | 0 (-12) |  () | Bed |
| mm9_bedornate_x100 | misfit | 1 | 12054 | 54 | 1 (-43) |  () | Bed101 |
| mm9_beetrack | sunk | 1 | 0 | 16 | -46 (-62) |  () | Beets12 |
| mm9_bjarnisitting | misfit | 1 | 14 | -20 | 0 (-36) |  () | Bjarni |
| mm9_burner | misfit | 1 | 13 | -34 | 0 (34) |  () | Jacobsladder0 |
| mm9_bush03_x100 | misfit | 1 | 1576 | -5 | 0 (5) |  () | Bush |
| mm9_cabinet04ns | misfit | 1 | 4900 | 309 | 1 (-1) |  () | Cabinet |
| mm9_candelabra | floating | 1 | 0 | -4 | 47 (-25) |  () | Candelabra |
| mm9_catstanddown | sunk | 1 | 0 | 5 | -9 (-14) |  () | Cat2 |
| mm9_chairskin1 | misfit | 1 | 2394 | -18 | 0 (-54) |  () | Chair |
| mm9_chandelier | floating | 1 | 0 | 328 | 309 (-19) |  () | Prop67 |
| mm9_crate | misfit | 1 | 11301 | -584 | 0 (5) |  () | Crate |
| mm9_desk01 | misfit | 1 | 7570 | 103 | 1 (-0) |  () | Desk |
| mm9_dresserns | misfit | 1 | 5479 | 496 | 0 (52) |  () | Dresser |
| mm9_erccsitting | sunk | 1 | 0 | -144 | -40 (63) |  () | RUDEProp1 |
| mm9_forge_x100 | misfit | 1 | 22 | -26 | 1 (27) |  () | Forge1 |
| mm9_hangingbowl1_x200 | in_wall height | 1 | 0 | -50 | 353 (403) | -8 (-2) | BrazierBowl15 |
| mm9_mug1 | misfit | 1 | 476 | -8 | 0 (25) |  () | Cup |
| mm9_peasantms2bconv | sunk | 1 | 6 | -137 | -41 (55) |  () | RUDEProp0 |
| mm9_peasantms2bwriting | misfit | 1 | 8 | 17 | 0 (-17) |  () | Ludwig |
| mm9_peasantms2dlisten | sunk | 1 | 6 | -141 | -45 (55) |  () | Halfdan |
| mm9_peasantms2dsitting2 | misfit floating | 1 | 10 | 8 | 10 (2) |  () | CommonerHumanMaleA6 |
| mm9_pew2ns_x100 | misfit | 1 | 3619 | 39 | 0 (2) |  () | Bench |
| mm9_pewns | sunk | 1 | 0 | 66 | -50 (-65) |  () | Pew5 |
| mm9_sack02 | misfit | 1 | 11520 | 406 | 0 (-20) |  () | Sack |
| mm9_scrollflat | misfit floating | 1 | 18 | 0 | 67 (-20) |  () | Prop0 |
| mm9_strawdummy | misfit | 1 | 10 | -5 | 1 (6) |  () | Strawdummy0 |
| mm9_tablebench2 | misfit sunk | 1 | 5425 | -104 | -48 (-16) |  () | Table |
| mm9_tableround | misfit | 1 | 7018 | 54 | 1 (-46) |  () | Table0 |
| mm9_throne | sunk | 1 | 0 | 134 | -15 (-134) |  () | Throne |
| mm9_weaponracknewg2 | misfit | 1 | 13 | 11 | 0 (-11) |  () | Weaponrack0 |
| mm9_weaponracknewg3 | misfit | 1 | 13 | 11 | 0 (-11) |  () | Weaponrack1 |
| mm9_woodbin | misfit | 1 | 5962 | 567 | 0 (-36) |  () | Woodbin |

### tasaracademy

296 props compared, 24 flagged.

| decoration | flags | n | fit | dz | gap (MM9) | wall (MM9) | examples |
|---|---|---|---|---|---|---|---|
| mm9_suitofarmor02_x150 | misfit | 6 | 14 | -48 | 1 (49) |  () | Prop143, Prop142, Prop141, Prop144 |
| mm9_dwarfaxeonside | floating | 3 | 0 | -84 | 174 (258) |  () | Pickaxe5, Pickaxe4, Pickaxe3 |
| mm9_table01ns | sunk | 3 | 0 | -46 | -8 (39) |  () | Prop154, Prop165, Prop166 |
| mm9_weaponrack_new | misfit | 3 | 13 | -12 | 2 (14) |  () | Weaponrack2, Weaponrack0, Weaponrack1 |
| mm9_brazier | sunk | 2 | 0 | -2 | -10 (-8) |  () | Brazier73, Brazier71 |
| mm9_chandelier | floating | 2 | 0 | 328 | 231 (-78) |  () | Chandelier0, Chandelier1 |
| mm9_forge | misfit | 2 | 20 | -2 | 1 (3) |  () | Forge1, Forge2 |
| mm9_bucket01 | floating | 1 | 0 | -66 | 31 (14) |  () | Bucket5 |
| mm9_scroll1 | sunk | 1 | 1 | -279 | -6 (194) |  () | Prop177 |
| mm9_tablebench2 | sunk | 1 | 1 | 45 | -49 (-45) |  () | Prop24 |

### templeofhonk

154 props compared, 5 flagged.

| decoration | flags | n | fit | dz | gap (MM9) | wall (MM9) | examples |
|---|---|---|---|---|---|---|---|
| mm9_hangingbowl | in_wall height | 2 | 0 | -19 | 584 (603) | -6 (-6) | BrazierBowl18, BrazierBowl19 |
| mm9_walltorch | in_wall | 2 | 0 | 0 | 70 (70) | -6 (-6) | WallTorch155, WallTorch154 |
| mm9_chest3 | floating | 1 | 1 | -3 | 9 (12) |  () | CollectionChest |

### thearena

31 props compared, 29 flagged.

| decoration | flags | n | fit | dz | gap (MM9) | wall (MM9) | examples |
|---|---|---|---|---|---|---|---|
| mm9_torchrust | misfit height | 14 | 7 | 8 | 143 (135) | 0 (-1) | WallTorch0, WallTorch1, WallTorch2, WallTorch3 |
| mm9_peasantms2blisten | sunk | 3 | 6 | -31 | -49 (-18) |  () | Spectator0, Spectator2, Spectator10 |
| mm9_tapestry_banner6 | no_support | 2 | 0 | 0 |  (-74) |  () | Banner2, Banner3 |
| mm9_tapestry_banner6_x150 | no_support | 2 | 0 | 0 |  (-80) |  () | Banner0, Banner1 |
| mm9_peasantfs2bconv1 | floating | 1 | 3 | -39 | 12 (-12) |  () | Spectator9 |
| mm9_peasantfs2bconv1 | sunk | 1 | 3 | -39 | -50 (-12) |  () | Spectator5 |
| mm9_peasantms1alisten | misfit sunk | 1 | 7 | -31 | -50 (-18) |  () | Spectator3 |
| mm9_peasantms1blisten | misfit sunk | 1 | 7 | -31 | -50 (-18) |  () | Spectator6 |
| mm9_peasantms2alisten | floating | 1 | 6 | -31 | 13 (-18) |  () | Spectator4 |
| mm9_peasantms2clisten | floating | 1 | 6 | -31 | 13 (-18) |  () | Spectator1 |
| mm9_peasantms2clisten | sunk | 1 | 6 | -31 | -49 (-18) |  () | Spectator7 |
| mm9_peasantms2dlisten | floating | 1 | 6 | -27 | 17 (-18) |  () | Spectator8 |

### thjoradmine

357 props compared, 134 flagged.

| decoration | flags | n | fit | dz | gap (MM9) | wall (MM9) | examples |
|---|---|---|---|---|---|---|---|
| mm9_minelantern02 | misfit | 89 | 8 | 1 | 342 (342) | -0 (13) | MLantrn1, MLantrn2, MLantrn3, MLantrn4 |
| mm9_stonedebris05thjorad | misfit sunk | 34 | 12 | -15 | -15 (-0) |  () | Debris0, Debris1, Debris10, Debris11 |
| mm9_minelantern02 | misfit off_wall | 9 | 8 | 0 | 363 (363) | 4 (5) | MLantrn30, MLantrn32, MLantrn45, MLantrn44 |
| mm9_minecart | no_support | 1 | 0 | 1 |  () |  () | MineCar14 |
| mm9_minelantern02 | misfit in_wall | 1 | 8 | 0 | 363 (363) | -5 (8) | MLantrn33 |

### thjorgardcity

730 props compared, 93 flagged.

| decoration | flags | n | fit | dz | gap (MM9) | wall (MM9) | examples |
|---|---|---|---|---|---|---|---|
| mm9_lamppost2 | misfit | 27 | 36 | 52 | 0 (-52) |  () | Streetlamp0, Streetlamp1, Streetlamp2, Streetlamp3 |
| mm9_lantern2 | height | 12 | 1 | -9 | 415 (424) |  (-41) | Lantern0, Lantern1, Lantern2, Lantern3 |
| mm9_chair03 | sunk | 6 | 1 | 62 | -12 (-62) |  () | Chair37, Chair38, Chair92, Chair93 |
| mm9_bookcase02ew_x120 | no_support | 4 | 0 | 19 |  (-127) |  () | Bookcase62, Bookcase61, Bookcase63, Bookcase64 |
| mm9_herbrack1 | height | 4 | 0 | 24 | 84 (60) |  () | Herbwallrack5, Herbwallrack6, Herbwallrack7, Herbwallrack8 |
| mm9_scrollp90 | misfit | 4 | 18 | -94 | 0 (94) |  () | Prop3, Prop4, Prop5, Prop6 |
| mm9_suitofarmor02 | misfit | 4 | 11 | -202 | 1 (203) |  () | Armor3, Armor4, Armor5, Armor6 |
| mm9_tapestry_banner6_x200 | off_wall | 4 | 0 | 0 | 140 (140) | 5 (5) | Banner0, Banner1, Banner2, Banner3 |
| mm9_chair | sunk | 3 | 5 | 72 | -11 (-72) |  () | Chair74, Chair66, Chair69 |
| mm9_kegbeer | misfit | 3 | 6 | -51 | 1 (52) |  () | Barrel7, Barrel1, Barrel2 |
| mm9_torchrust | height | 3 | 6 | 7 | 215 (208) | -1 (-8) | WallTorch12, WallTorch11, WallTorch8 |
| mm9_torchrust | misfit height | 3 | 6 | 8 | 134 (126) | -1 (-8) | WallTorch10, WallTorch9, WallTorch7 |
| mm9_burner | misfit | 2 | 14 | -57 | 0 (58) |  () | Burner0, Burner1 |
| mm9_forge_x100 | misfit | 2 | 22 | -26 | 0 (26) |  () | Forge2, Forge1 |
| mm9_candelabra | sunk | 1 | 1 | -4 | -17 (-34) |  () | Candelabra0 |
| mm9_clover | sunk | 1 | 0 | -40 | -6 (34) |  () | Clover2 |
| mm9_desk02ns | misfit | 1 | 13 | -36 | 0 (36) |  () | Desk0 |
| mm9_herbrack2 | in_wall | 1 | 0 | 1 | 115 (114) | -6 (-6) | Herbwallrack2 |
| mm9_strawdummy2c | misfit | 1 | 9 | -26 | 0 (26) |  () | Strawdummyrack1 |
| mm9_strawdummy2l | misfit | 1 | 116 | -26 | 0 (26) |  () | Strawdummyrack0 |
| mm9_strawdummy2r | misfit | 1 | 132 | -26 | 0 (26) |  () | Strawdummyrack2 |
| mm9_wallcandle | off_wall | 1 | 2 | 0 | 175 (175) | 10 (7) | WallTorch96 |
| mm9_weaponracknsnewg1 | misfit | 1 | 14 | -56 | 0 (56) |  () | Weaponrack2 |
| mm9_weaponracknsnewg2 | misfit | 1 | 14 | -56 | 0 (56) |  () | Weaponrack0 |
| mm9_weaponracknsnewg3 | misfit | 1 | 13 | -56 | 0 (56) |  () | Weaponrack1 |
| mm9_well_x100 | misfit | 1 | 14 | 4 | 0 (-4) |  () | WellMMIX0 |

### thronheimcity

305 props compared, 31 flagged.

| decoration | flags | n | fit | dz | gap (MM9) | wall (MM9) | examples |
|---|---|---|---|---|---|---|---|
| mm9_herbrack1 | height | 8 | 0 | 24 | 84 (60) |  () | Herbwallrack5, Herbwallrack6, Herbwallrack7, Herbwallrack8 |
| mm9_scrollflat | misfit | 4 | 18 | -200 | 1 (201) |  () | Prop18, Prop19, Prop20, Prop21 |
| mm9_forge_x100 | misfit | 2 | 22 | -28 | 1 (29) |  () | Forge1, Forge2 |
| mm9_pew2_x120 | misfit | 2 | 6 | -5 | 1 (6) |  () | TemplePew17, TemplePew18 |
| mm9_strawdummy2c | misfit | 2 | 9 | -110 | 1 (111) |  () | Strawdummyrack1, Strawdummyrack4 |
| mm9_strawdummy2l | misfit | 2 | 116 | -110 | 1 (111) |  () | Strawdummyrack0, Strawdummyrack3 |
| mm9_strawdummy2r | misfit | 2 | 132 | -110 | 1 (111) |  () | Strawdummyrack2, Strawdummyrack5 |
| mm9_suitofarmor02 | misfit | 2 | 11 | -39 | 0 (39) |  () | Armor4, Armor3 |
| mm9_tapestry_banner8 | off_wall | 2 | 0 | 0 | 76 (76) | 6 (6) | Banner0, Banner1 |
| mm9_bookcase02ew_x120 | floating | 1 | 1 | 19 | 222 (-125) |  () | Bookcase47 |
| mm9_pew2_x110 | misfit | 1 | 6 | 68 | 0 (-68) |  () | TemplePew3 |
| mm9_weaponracknsnewg1 | misfit | 1 | 13 | -58 | 1 (59) |  () | Weaponrack2 |
| mm9_weaponracknsnewg3 | misfit | 1 | 13 | -58 | 1 (59) |  () | Weaponrack1 |
| mm9_well_x100 | misfit | 1 | 14 | -111 | 0 (111) |  () | WellMMIX0 |

### traininghall

43 props compared, 25 flagged.

| decoration | flags | n | fit | dz | gap (MM9) | wall (MM9) | examples |
|---|---|---|---|---|---|---|---|
| mm9_walltorch | off_wall | 10 | 0 | -0 | 210 (210) | 7 (7) | WallTorch0, WallTorch3, WallTorch4, WallTorch5 |
| mm9_hangingbowl1_x100 | height | 6 | 0 | -26 | 1 (27) |  () | hangingtorch2, hangingtorch7, hangingtorch3, hangingtorch4 |
| mm9_strawdummy | misfit | 4 | 10 | -30 | 0 (30) |  () | Dummy6, Dummy7, Dummy0, Dummy1 |
| mm9_lumberdebris02 | misfit | 2 | 31 | -10 | -1 (-12) |  () | Prop0, Prop4 |
| mm9_lumberdebris03 | sunk | 1 | 1 | -4 | -9 (-4) |  () | Prop1 |
| mm9_lumberdebris05 | misfit | 1 | 14 | -12 | 0 (21) |  () | Prop2 |
| mm9_lumberstone02 | sunk | 1 | 1 | 23 | -20 (-30) |  () | Prop5 |

### verhoffinruins

89 props compared, 56 flagged.

| decoration | flags | n | fit | dz | gap (MM9) | wall (MM9) | examples |
|---|---|---|---|---|---|---|---|
| mm9_minelantern | misfit | 37 | 8 | 1 | 169 (168) |  (15) | Lantern0, Lantern1, Lantern3, Lantern4 |
| mm9_chest1 | misfit | 5 | 7 | -59 | 1 (60) |  () | TreasureChest0, TreasureChest1, TreasureChest2, TreasureChest3 |
| mm9_spikepit | misfit | 4 | 27 | 83 | 0 (-83) |  () | Spikes5, Spikes6, Spikes7, Spikes8 |
| mm9_chairdesk03p270 | tilt_lost | 2 | 10 | -50 | 1 (51) |  () | Chair1, Chair2 |
| mm9_tableround2p60 | tilt_lost | 2 | 30 | -56 | 0 (57) |  () | Table2, Table4 |
| mm9_chairdesk03p90 | tilt_lost | 1 | 8 | -118 | 0 (98) |  () | Chair0 |
| mm9_flayingbench | misfit | 1 | 12 | 2 | 1 (-1) |  () | FlayingBench |
| mm9_manacles | misfit | 1 | 18 | 0 | 180 (180) |  () | Manacles0 |
| mm9_skeletondebris03 | misfit sunk | 1 | 8 | -8 | -19 (-2) |  () | Debris0 |
| mm9_torturerack01 | misfit no_support | 1 | 7 | 1 |  (-84) |  () | TortureRack1 |
| mm9_weaponscabinet02tip | tilt_lost no_support | 1 | 102 | -76 |  (-17) |  () | Cabinet2 |

### wizardslab

241 props compared, 93 flagged.

| decoration | flags | n | fit | dz | gap (MM9) | wall (MM9) | examples |
|---|---|---|---|---|---|---|---|
| mm9_torchmetal | misfit height | 46 | 7 | 8 | 164 (156) | 0 (-8) | CandleProp20, CandleProp21, CandleProp22, CandleProp23 |
| mm9_torchmetalorange_x100 | misfit height | 18 | 7 | 8 | 154 (146) | 0 (-8) | CandleProp48, CandleProp49, CandleProp50, CandleProp51 |
| mm9_herbrack1_x175 | height | 12 | 0 | 28 | 303 (275) |  () | Prop55, Prop56, Prop57, Prop58 |
| mm9_torchmetal | misfit off_wall height | 5 | 6 | 8 | 154 (146) | 4 (-3) | CandleProp81, CandleProp14, CandleProp15, CandleProp18 |
| mm9_torchmetalunlit | misfit height | 4 | 7 | 8 | 164 (156) |  (-13) | CandleProp67, CandleProp68, CandleProp69, CandleProp70 |
| mm9_torchmetalorange_x100 | misfit off_wall height | 2 | 7 | 8 | 164 (156) | 5 (-3) | CandleProp73, CandleProp74 |
| mm9_burner | misfit | 1 | 14 | -56 | 1 (57) |  () | Prop42 |
| mm9_scrollflat | misfit | 1 | 19 | -77 | 1 (78) |  () | Prop8 |
| mm9_shelfitem01_x120 | no_support | 1 | 3 | -0 |  () |  () | Prop126 |
| mm9_torchmetal | height | 1 | 6 | 8 | 368 (360) | -0 (-6) | CandleProp47 |
| mm9_torchmetal | off_wall height | 1 | 6 | 8 | 164 (156) | 13 (6) | CandleProp41 |
| mm9_torchmetalorange_x100 | misfit floating | 1 | 7 | 8 | 21 (13) |  () | CandleProp75 |

### yanmirsfort

158 props compared, 11 flagged.

| decoration | flags | n | fit | dz | gap (MM9) | wall (MM9) | examples |
|---|---|---|---|---|---|---|---|
| mm9_chairdesk03p270 | tilt_lost | 2 | 8 | 29 | 0 (-29) |  () | Chair0, Chair4 |
| mm9_chairdesk03p270_x125 | tilt_lost sunk | 2 | 11 | 8 | -31 (-39) |  () | PlainChair3, PlainChair5 |
| mm9_chairp270 | tilt_lost sunk | 2 | 21 | -8 | -42 (-34) |  () | PlainChair0, PlainChair2 |
| mm9_bedornate_x300 | no_support | 1 | 0 | 1 |  (-342) |  () | Bed0 |
| mm9_pew3_x100 | misfit sunk | 1 | 24238 | 528 | -26 (-20) |  () | Bench0 |
| mm9_pew3_x100 | sunk | 1 | 1 | 31 | -26 (-57) |  () | Bench1 |
| mm9_stool01p90 | tilt_lost | 1 | 11 | -300 | 1 (301) |  () | Stool5 |
| mm9_tableroundplain | misfit | 1 | 30499 | 573 | 0 (54) |  () | RdTable |

