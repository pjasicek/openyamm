# S: 3D models

The user started this lane on 2026-11-20 ("start now": Meshy spending for Xeen's new creatures is approved, Acts
I–II first).

## Owns

- New creature projects `level_generation/creatures/xeen_<name>_claude/`.
- Colour tiers of reused models for Xeen's families.
- New decoration props for Xeen (rim crystals, cloud-stone, Ancient machinery, sundials, gongs, pedestals) when map
  lanes ask.
- Ground models of new item bases (later).
- `assets_dev/worlds/xeen/models/decoration_data.txt` (the world's decoration rows, hand-written with each model; orchestrator 2026-11-21). A2 edits a row only when asked.
- Installs with `tools/install_model.py --world xeen`.
- Bindings in `assets_dev/worlds/xeen/models/`.

## Read first

- CLAUDE.md's creature rules (all of them): HD master references first (five masters from Xeen's own sprites as the
  references; Xeen sprites are references only, never shipped), colour tiers, the texture quality pass.
- `.agents/skills/creature-to-3d/SKILL.md` (scope, spending and resume rules).
- `level_generation/creatures/CLAUDE_HUMANOID_NPC_PLAYBOOK.md` (the witch, the sprite, the female caster) and
  `CLAUDE_QUADRUPED_PLAYBOOK.md` (the toad, the mole, the arthropods).
- `level_generation/creatures/CLAUDE_CREATURE_TEXTURES.md`.
- `level_generation/GAME_ASSET_MODELLING_GUIDELINES.md`.
- `anim_library/README.md` (check the library before buying any animation).
- `devdocs/xeen/MONSTERS_AND_ITEMS.md` §2 (the families, "Reuse" and "New").
- `level_generation/creatures/mm5_troll_grunt/` (an earlier Xeen creature study).

## Phase 0 work, in order

1. **The toad** (Giant Toad, Bog Toad, Swamp Toad: X1 Toad Meadow, X3).
2. **The witch** (Wicked Witch, Witch, Head Witch: Witch Tower; later the coven).
3. **The sprite** (Medusa Sprite, Killer Sprite, Sprite Queen: X2, D2).
4. **The swarm** (Doom Bug, Insect Swarm, Stingers): a particle cloud may serve better than a mesh; decide and say why.
5. **Colour tiers** for the reused families of Acts I–II (MONSTERS_AND_ITEMS §2): goblins, orcs, mad dwarves, ogres,
   outlaws, evil rangers, Burlock knights, cultists, skeletons, rotting dead, bats, spiders, oozes, rats, serpents,
   werewolves, golems, wizards.

For each new creature, send A2 its model name and tier textures for its `monsters.yml` rows. Every clip passes the
playbooks' gates before you report it.

## Waits on

Nothing.

## State

- **Toad: done** (`level_generation/creatures/xeen_toad_claude/`, README there). Installed `worlds/xeen/models/
  xeen_toad.glb`, skins `toad_a/b/c` (Giant brown, Bog olive, Swamp slate-green), bound to `Xeen Toad A/B/C`. 15 cr.
  Not seen in game yet (no Xeen map holds toads).
- **Swarm: done** (`xeen_swarm_claude/`, README there). Xeen's Insect Swarm/Stingers sprite (image 23) is a cloud of
  flying wasps; the engine has no particle-bodied actors, so the swarm is a mesh: seven copies of one Meshy Stinger
  (shared UVs) on their own bones with procedural orbits, blended wings, a sting dart and a one-by-one fall.
  `xeen_swarm.glb`, skins `swarm_b` (Insect Swarm, native orange-brown) and `swarm_c` (Stingers, dark crimson), bound
  to `Xeen Swarm B/C`. The A tier, the **Doom Bug**, is one giant cricket in Xeen (image 2): `xeen_doombug.glb`
  (exoskeleton rig, tripod gait, skin `bug_a`), bound to `Xeen Swarm A`. 30 cr for the project.
- In-game check 2026-11-20 (`build-xeen`, XD-21, `xeen_tiers_claude/check_tour_xd21.yml`): the three toad tiers and the
  swarm draw as 3D models with their skins.
- **Witch: done** (`xeen_witch_claude/`, README there; built by a lane sub-agent). Xeen image 76 (gold horned mask, red robe, fork-staff; the source has no pointed hat). `xeen_witch.glb` +
  `xeen_witch_staff.glb` (attachment on node `Staff`), skins `witch_a` (Wicked Witch, native red), `witch_b` (Witch,
  violet), `witch_c` (Elder Witch and the Head Witch boss, black robe), bound to `Xeen Witch A/B/C` and
  `Xeen Head Witch`; seen in game in XD-21. The Coven (Act IV, Darkside's green witch) keeps its stand-in until it
  gets its own tiers. 20 cr. Session 2: the contact faults are fixed in the chain (`scripts/elbow_clear.py` after
  `arm_push.py`, a staff pass after `clip_timing.py`): every clip now <= 0.5 cm (was elbow 1.4-4.1 cm in Running, Cast,
  Fidget, right forearm 1.8 cm in Fidget, corpse forearm 6.4 cm, staff fork 4 cm in the boot); wrist and jerk gates
  unchanged; far LODs re-repaired (r25_12 accepted), death floor fix, reinstalled, floor audit ok, seen in XD-21. Still
  open (README): the staff thumb lies along the shaft.
- **Sprite: done** (`xeen_sprite_claude/`, README there; built by a lane sub-agent). The Killer Sprite design (Xeen
  image 22: blue fey, four translucent wings) for the family; `xeen_sprite.glb`, skins `sprite_a` (Medusa Sprite, green),
  `sprite_b` (Killer Sprite, native blue/magenta), `sprite_c` (Sprite Queen, violet/gold), bound to `Xeen Sprite A/B/C`
  and `Xeen Sharla` (sprite_c). Scale 66 (a 1.1 m hovering sprite). 25 cr. The bat-winged Medusa Sprite / Sharla of
  Darkside image 53 is a different design: a later project if wanted.
- **Bindings**: `assets_dev/worlds/xeen/models/actors.yml` holds all 238 Xeen descriptors (A2's stand-ins from
  `tools/xeen/standin_bindings.py`, Orc Shaman on the MM6 goblin shaman for its cast clip, the MM9 mummy entries
  with sprite timing) and the new models above. `level_generation/creatures/xeen_tiers_claude/bind.py` merges a
  project's `integration/actors.yml`. Checked with `openyamm --world mm7 --headless-validate-actor-models
  --all-worlds` (0 refused).
- **Colour tiers** of the reused families: route built and proven on the goblins. `level_generation/creatures/
  xeen_tiers_claude/xeen_tiers.py <installed source glb> <out glb> <spec.json>` copies an installed model and adds
  Xeen skins as recoloured copies of an existing tier's ramps (mesh, clips, LODs and images untouched); install the
  copy with `--world xeen`, then `rebind.py <model> "<descriptor>=<skin>" ...` points the Xeen bindings at it.
  Done: Goblins and Gremlins on `xeen_gob2.glb` (from `mm6_gob2`; `xgob_a` teal goblin as Xeen image 5, `xgob_b`
  purple gremlin as Darkside image 26, `xgob_c` deep violet, `xgob_d` magenta), checked in game. The remaining
  families are done too (lane sub-agent, `xeen_tiers_claude/README.md`): orcs and warband (`xeen_m246`), mad dwarves,
  ogres, outlaws, evil rangers, Burlock knights, cultists and heretics, skeletons, rotting dead (`xeen_m438`), bats,
  spiders, oozes, rats, sewer stalkers (`xeen_ratman`), serpents and cobras, werewolves, golems (`xeen_m254`, ten
  skins), wizards; Orc Shaman on `xeen_gob2` skin `xgob_e`. All seen in game in XD-21; 238 descriptors on 59 models,
  0 refused. Diamond and Onyx golems have their own skins.
- **Body regions (D-10): done** 2026-11-20 (session 2). `xeen_tiers_claude/add_region.py` adds a mask channel to a
  Xeen copy and a ramp for it on every material (other skins keep their look through a fitted ramp). Golems
  (`xeen_m254`): the whole body to each material (wood, stone, iron with rust highlights, pale high-contrast diamond,
  onyx, sand, water, cloud, sky; the Lava Golem dark with glowing crevices, `lava_cracks.py` + `emission.py`); ogres
  (`xeen_ogr`): armour plates silver / dark iron / blue and cloth rust / red-brown / gold, skin kept; werewolves
  (`xeen_wwf`): fur brown / grey-brown / silver; orcs (`xeen_m246`): tan skin, one shade darker per tier. Installed,
  0 refused, seen in game in XD-21 (`s2-d10`). Skin names unchanged, so A2's rows need nothing.
- **Orc "two swords"**: not a fault. The XD-21 capture had Orc Archer B walking directly behind Orc A (two health bars
  over one body), so B's sword stuck out beside A. Single spawns (session 2) carry one sword each; bindings unchanged.
- Cancelled by the user (2026-11-20): paper-doll art for robes and scale mail (no new equipment items); artifacts reuse
  MM6–MM8 item skins (no item art or ground models). Quest items' ground models stay with A2.
- Queued (A6 via xeen-o, phase 3, low priority): decorations for D2's glowing mushrooms and crystal accents, and
  D1's Dark Grove tree with the rope into the sky.
- **A2's binding requests (session 2): done.** Xeen Sorceress D (Apprentice) and Head Sorceress bind the Sorceress A/C
  stand-ins (druid) until the female caster exists; Xeen Mountain Gargoyle A/B/C copy the Gargoyle A/B/C stand-in
  bindings (mm6 gargoyle; no Xeen gargoyle tiers yet); Xeen Crodo from A2's fragment. Stale header lines (Orc Warband B,
  Swarm A, ogres, werewolves, golems, orcs) corrected. 244 descriptors on 60 models, 0 refused.
- **Gargoyle tiers (session 2): done.** `xeen_gar.glb` (MM6 gargoyle, whole body region): xgar_a-c Gargoyle / Lord /
  Obsidian, xgar_d-f Mountain Gargoyle / Sentinel / Overlord; bound, 0 refused, seen in XD-21 (`s2-gar`). Table in
  `xeen_tiers_claude/README.md`.
- **Flying Feet: done** (session 3, sub-agent; `level_generation/creatures/xeen_feet_claude/`, README there).
  `xeen_feet.glb` (one Meshy winged right foot, mirrored; 4,510 tris), skin `feet_a`, scale 267, bound to
  `Xeen Construct A`; clips Standing/Walking/Running/Attack (stamp, impact 0.45)/Hit/Death/Dead/Fidget; floor audit ok
  as a flier (rows now Fly Y); seen in XD-21 (session 3). 15 cr.
- **Guardian: done** (session 3, sub-agent; `xeen_guardian_claude/`). `xeen_guardian.glb` (chrome skull, 6,879 tris,
  separate jaw and teeth, hand-built ruby and eyes with emission), skin `guardian_a`, scale 125, bound to
  `Xeen Construct B` only; bite impact 0.45, AttackRanged glow at eyes and gem, release from the gem at 0.50; seen in
  XD-21. Known limit: the chrome reads mid grey in dim rooms (`SKULL_GAIN` in its `scripts/compose.py`). 15 cr.
- **Xeen's Guard (11603):** D-19: its own model `xeen_guard` later (Next 5); keeps `mm8_m592`/`m592_b`.
- **Mole: done** (session 3, sub-agent; `level_generation/creatures/xeen_mole_claude/`, README there).
  `xeen_mole.glb` (7,812 tris, own quadruped rig, procedural clips; attack impact 0.47), skins `mole_a` (native
  teal-blue), `mole_b` (stone grey-brown), `mole_c` (earth brown, dark claws), bound to `Xeen Mole A/B/C` at scale 145
  (one size, no scale_reference); floor audit ok; seen in XD-21 (session 3). 15 cr. The rows still carry the rat
  stand-in's heights 77/107/59 and radius 40 (the model is ~92 tall, ~203 long): A2's to adjust.
- **Carnage Hand: done** (session 3, sub-agent; `xeen_hand_claude/`, README there). `xeen_hand.glb` (5,806 tris;
  Meshy hand with a hand-built mouth: sliding lip lids, gums, gullet, tongue, 14 fangs; rig Palm > 3 bones per finger +
  LipUpper/LipLower), skin `hand_a` (mask R skin, G maw, B fangs), scale 143, bound to `Xeen Construct C`; bite impact
  0.45; flier floor audit ok; seen in XD-21 (session 3). 15 cr.
- **A2's binding requests (session 3): done.** Xeen Renegade A-C on `xeen_kni` new skins `xkni_e/f/g` (tarnished
  plate; brick, rust, tarnished-gold trims; reinstalled), Xeen Spirit D (Ghost Rider) from A2's fragment (mm6_gst
  gst_b), Xeen Dark Sprite A-C on `xeen_sprite` new skins `sprite_d` (Darkside image 53: bronze, green, violet wings)
  / `sprite_e` (copper, wine, ember wings) / `sprite_c` (D-23; `xeen_tiers.py` gained `by_material`), Xeen Ogre D
  (Graalg's Brute) as Ogre B (`xogr_b`). 252 descriptors on 62 models, 0 refused; renegades, Ghost Rider, Elder Gorgon
  Sprite and Ogre D seen in XD-21.
- **A2's D-25 bindings (session 3): done.** Troll D, Troll Matron, Warren Troll A-C, Ninja D, Clan Master, Wolf D
  (A2's fragments, existing models and skins), Ogre E-G (copies of Ogre A-C on `xeen_ogr`), Outlaw D and The Master
  Thief (copies of Outlaw C, `xthf_c`). 265 descriptors on 62 models, 0 refused. The bosses (Clan Master, Troll Matron,
  Master Thief) share their tier skins; own skins later if wanted (mm8_m476 and mm6_mnk1 would need Xeen tier copies).
- **A2's DD-04/DD-09/D2 bindings (session 3): done.** Gremlin D-F and G-I as copies of Gremlin A-C (`xgob_b/c/d`),
  Orc Warband D (Snog) as Warband A (`xorc_d`), Sprite D/E (D2's village sprites) as Sprite A/B. All on installed
  models and skins already seen in game; 0 refused.
- **D-26 Dire Rat: done.** Skin `xrat_d` on `xeen_rat` (rust-brown fur, pale skin, orange eyes), bound to `Xeen Rat D`
  at scale 292.5 against Rat A: 1.25x the Giant Rat while it shares Rat C's standing sprite `rCtsta` (rescale if A2
  gives it its own sprite). 266 descriptors, 0 refused; seen in XD-21 beside Rat C. Rat descriptors keep their names
  (A2's renames are monster names), so the Rat and Sewer Stalker bindings still resolve.
- **Quest-item ground models (A2's 7): done** (session 4, sub-agent). Stood up and cleaned (`scripts/stand_meshy.py`; the Speed Doll's shard hair replaced by a closed cap the paint carries), Codex paint and mask bake, installed (`assets_source/worlds/xeen/world_items/models/item_xeen_123{49,51,67-71}.glb`, 3.1-3.4k tris, 0 inverted), bound in `worlds/xeen/world_items/items.yml` (41 bindings); seen in X1 (`items_xeen_claude/review/ingame_meshy7/`): no placeholder left. Meshy 35 of the approved 45 (session 3); 0 more.
- **D-23 great-tree crown: done** (session 4, sub-agent; `level_generation/decorations/xeen_greattree_claude/`, README there). The MM8 broadleaf tree pipeline copied, own limb skeleton (16-sided stub, six limbs), the trunk's own `xdbark` at its tile size, deep blue-green leaves. `xeen_deco_greatcrown.glb`, LOD 14,832 / 7,480 / 2,528 / impostor, overdraw ~3 layers (1.7 at the trunk foot), 0 credits. World decoration `xeen_greatcrown` (row 4001 in `worlds/xeen/models/decoration_data.txt`, sprite 27001 in `worlds/xeen/rendering/sprite_frame_data_world_decorations.yml`, binding `worlds/xeen/models/decorations.yml`: height 3655, yaw facing, lod_pixels [260, 130, 60]). Placement: z = trunk top - 200 (D2: raise 2,848), stub radius 539 at its base, about 4,650 across. Seen in game on D2 from a scratch root (`xeen_greattree_claude/work/ingame/`, its world.yml with the decorations contribution and the stand-in crowns replaced): `work/ingame/shots/sheet.png`. world.yml's `decorations` contribution added by O; A6 places it on D1 and D2 (session 8).
- **The Master Thief** (session 4): its own skin `xthf_d` (dark oxblood cloak) on `xeen_thf`, reinstalled, rebound; seen in XD-21 beside Thief and Master Thief (`xeen_tiers_claude/ingame_s4/s4-thief.png`); 275 descriptors, 0 refused.
- **Sorceress (female caster): done** (session 4, sub-agent; `level_generation/creatures/xeen_sorc_claude/`, README there). Clouds image 31. `xeen_sorc.glb` (LOD 9,949 / 4,973 / 2,480 / 1,234; 1K head set cut from the same 4K paint), scale 99 (173 units), clips Standing/Walking/Running (Standard Run)/Attack (slap, impact 1.055)/Cast (two-palm thrust, release 1.23 from Socket_RightPalm, glow both palms)/Hit/Death/Dead/Fidget; panels on swing bones. Skins `sorc_a` white (Sorceress A, Apprentice D, Head Sorceress), `sorc_b` pale violet (Enchantress), `sorc_c` emerald (Grand Sorceress), `sorc_m` crimson with near-black folds (Morgana, D-32). Bound, 275 descriptors, 0 refused; seen in XD-21 (`review/ingame_sheet_v1.png`, `v2`). 20 credits. The floor audit tool fails on Sorceress D's scale_reference (no Xeen sprite scale); D shares A's model and skin. Open: rigid mane, painted (not glowing) eyes.
- **Engine decorations: done** (session 4, sub-agent; `level_generation/decorations/xeen_engine_props_claude/`, README there): `mm7_deco_haybale2.glb` (straw dome + tuft cards, 1,756 tris, height 188), `mm7_deco_7dec12.glb` (driftwood pile, 1,946, height 118), `mm7_deco_7dec41.glb` (Crodo's bottle, 508, height 92 = the sprite's 1.5x table scale), installed `--engine`, bound in `engine/models/decorations.yml` (outdoor only: no Xeen dungeon places them), seen on X1 (`review/ingame/`). X1-X5, D1-D3 bakes may be stale (`tools/lighting/stale_bakes.py`).
- **Sand-fall (D-31): done** (session 4, sub-agent; `level_generation/decorations/xeen_sandfall_claude/`, README there). `xeen_deco_sandfall.glb` (2,034 tris: tongue + core veil breaking into strands + two additive haze sheets, `openyamm_uv_scroll` downward), world decoration `xeen_sandfall` (row 4002, sprite 27002), bound height 2393.2 (1:1), yaw facing, no z_offset. Origin = the rim edge's top, mid-width: A5 places it on the last land column (x -20480) at the edge's terrain z, `facing: 90` pours west, 3-5 falls at least 1,500 apart, 400 inland kept clear (the tongue), terrain level with the edge for 450 inland. 800 wide at the lip (haze 1,350), veil ~1,080 out, strands end 920-1,300 below the lip, haze fades by ~2,300. Seen on X5's west rim from the scratch root (`review/sheet_ingame3.png`). `scripts/presets.py` takes a lava preset for X7.
- **Sand worm: done** (session 6, sub-agent; `level_generation/creatures/xeen_sandworm_claude/`, README there). Clouds
  image 56; `xeen_sandworm.glb` (ringed worm rising out of its own sand-and-rubble mound, which travels with it; LOD0
  8,396 / 4,197 / 2,096 / 1,030 tris), skins `sandworm_a` (Sand Worm, native orange-ochre, grey spikes, scale 110,
  127 units standing) and `sandworm_c` (Great Worm, rust-red/umber, near-black spikes, scale 126.5, 146 standing);
  the mound one sand colour on both. Procedural clips; Attack impact 0.567; walking = lower rings sunk in a rippling
  mound. Bound `Xeen Sand Worm A/C` (Sand Worm B is the Armadillo); 294 descriptors on 73 models, 0 refused; both
  tiers seen in XD-21 (`xeen_tiers_claude/ingame_s6/s6-sheet.jpg`, with the Xeen mummies). 15 cr. Rows carry heights
  160/190 (model 127/146): A2's to adjust.
- **XD-16's idols (D-40): done** (session 6, sub-agent, no Meshy; `level_generation/decorations/xeen_idols_claude/`,
  README there). `xeen_idol_demon` (row 4008, sprite 27008, `xeen_deco_idol_demon.glb` from `mm6_demon` posed, horns,
  empty eye sockets; height 780; 4,467 / 2,218 / 1,004 / 372 tris) and `xeen_idol_devil` (row 4009, sprite 27009,
  `xeen_deco_idol_devil.glb` from `mm9_greaterdemon`, wings raised; height 820; 5,140 / 2,511 / 1,055 / 320), radius
  165, plinth 320 x 320 x 96, dark volcanic stone (`vlcwl3a` grain), no emission; `yaw: facing`, facing 90 faces west;
  origin at the plinth's bottom centre; entity `decoration_list_id` 4007 / 4008; the devil's wings reach +-282 N-S.
  Seen spawned at X7's cave mouth (`review/ingame/pair.jpg`). A5 replaces L3's blockout buildings with them.
- **D-44 (binding rule):** Xeen depends on `engine, mm6, mm7, mm8` only. Every Xeen binding's model path lies in
  `engine/` or `worlds/{xeen,mm6,mm7,mm8}/`, never `worlds/mm9/`. An MM9 model a Xeen row needs is copied into Xeen
  (`tools/install_model.py --world xeen --name xeen_<x>.glb`, its `.cook.yml` sidecar copied beside the source first),
  as `xeen_bf.glb`; MM6-MM8 stand-ins stay referenced (copied only when a family needs Xeen tiers or edits). Done
  (session 6): the Mummy A-C rows on `xeen_mummy.glb` (copy of `mm9_mummy`, skins `mummy_a/b/c` unchanged); no Xeen
  binding names `worlds/mm9/` now; 294 descriptors on 72 models, 0 refused. Check: `grep worlds/mm9/
  assets_dev/worlds/xeen/models/*.yml`.
- **Octopod: done** (session 7, sub-agent; `level_generation/creatures/xeen_octopod_claude/`, README there; D-36,
  D-52). Darkside image 41; `xeen_octopod.glb` (root at the waterline; 8 tentacles x 8 bones; MASK foam ring on its own
  node; LOD 9,587 / 4,792 / 1,689 / 462), skins `octopod_a` (native red, yellow suckers, blue eyes), `octopod_b`
  (violet, gold suckers), `octopod_c` (sea-green slate); scales A/D 135, B 155.25, C 175.5; Attack impact 0.533 with a
  purple ink glow at `Socket_Siphon`; Death sinks, Dead held under. Outdoor swimmers ride the water tile's terrain height
  (= the surface), so no z offset; DD-14's cistern pool floor is itself the water face, so `Xeen Octopod D` (11473)
  uses the same model, scale and skin as A (no grounded copy). Bound A-D; 310 descriptors, 0 refused; seen on D4's lake
  and in DD-14 (`review/ingame/sheet_d4.png`, `sheet_dd14.png`). 15 cr. For A2: collision A/D 80/60, B 92/70, C
  104/80. For A8: DD-14's five actors still place 11470, swap to 11473.
- **Xeen's Guard: done** (session 7, sub-agent; `level_generation/creatures/xeen_guard_claude/`, README there; D-19).
  Clouds image 62; `xeen_guard.glb` (rigid chrome plates each on one bone, dark joint spheres; LOD 11,642 / 5,820 /
  2,907 / 1,455), clips retargeted from the stand-in `mm8_m592` (Standing, Walking, Running, Attack impact 1.033 with a
  green glow at `Socket_Gem`, Hit, Death, Dead, Fidget), skin `guard_a` (chrome, red seam and gem with emission, cyan
  tubes, black boots), scale 84.5 = 155 units. Bound `Xeen Construct D`; 310 descriptors, 0 refused; seen in XD-21
  (`xeen_tiers_claude/ingame_s7/s7-guard.png`, the slam with the gem glow). 15 cr. For A2: row 11603 height 155,
  radius 55. Limits: joint gaps show the spheres at bends; corpse on its back with boots raised; far LODs no glow.
- **Sphinxes: done** (session 7, sub-agent; `level_generation/decorations/xeen_sphinx_claude/`, README and
  `integration/sphinx_collision.yml` there). Procedural (SDF body, MM6 peasant head as the face, `egycol64` nemes
  stripes), 0 cr. `xeen_sphinx_north` (row 4010, sprite 27010, height 2453.46, LOD 14,170 / 7,085 / 3,400 / 1,132) and
  `xeen_sphinx_south` (4011, 27011, 1414.39, 8,714 / ... / 697), radius 0, `yaw: facing`, `lod_pixels [900, 400, 160]`.
  Origin = the door threshold's middle on the breast face: north (9216, 10240, z 1408) facing 180, south (-12544,
  -10240, z 1536) facing 270; door openings x +-192 z 0..512 / x +-160 z 0..448 (open behind: A5's leaves and a carrier
  block close them); body barrier rings in the yml. Seen on X6 from an overlay (`review/ingame3/`). A5 swaps its masses
  for them (needs decoration facing in the studio, A1) and rebakes X6.
- **Armadillo: done** (session 7, sub-agent; `level_generation/creatures/xeen_armadillo_claude/`, README there).
  Darkside image 5; `xeen_armadillo.glb` (own quadruped rig, tail mace whose spikes pop out on the blow, tongue; LOD
  9,387 / 4,692 / 2,342 / 1,149 tris; UVs xatlas + seam pass + sparrow after PartUV failed: atlas 70.6 %, fragments
  2.8 %, stretch p90 1.20), skin `armadillo_a` (native red, pale bands, claws, eyes+tongue), scale 220 (110 units tall,
  166 wide, 484 snout to tail ball), Attack impact 0.733. Bound `Xeen Sand Worm B`; 301 descriptors, 0 refused; seen
  in XD-21 between the worms and on X6 (`xeen_tiers_claude/ingame_s7/s7-dillo*.png`). 20 cr (10 + 10 retexture).
  Limits: hind claws red, tail straight behind (the sprite curls it), corpse on its side stands taller than the beast.
  For A2: row 11441 height 110, radius about 120 (body without the tail ~264 long).
- **D-47 (session 7): done** (no Meshy). Lord Xeen 11634 on `xeen_demon.glb` (copy of `mm6_demon`) skin `xdem_lx`
  (Xeen image 89: gunmetal hide, royal blue harness; `spec_lord_xeen.json`); Xeen's Pet 11644 on `xeen_cdr1.glb` (copy
  of `mm6_cdr1`) skin `xcdr_pet` (image 88: green, brown belly and spines; `spec_xeens_pet.json`); Corak 11912 on
  `xeen_sor1` new skin `xsor_f` (midnight-blue robe, silver trim, white hair and beard through a new hair channel 2,
  `body_wizards_hair.json`, head UV area only; other wizard skins unchanged); elementals `Xeen Elemental E/F/G`
  (11624-26) on MM6 `mm6_aie1` `aie1_a`, MM7's water `mm7_m210` `m210_a`, earth `mm8_m504` `m504_a` (the MM bindings'
  scales); the People `Xeen Giant D/E/F` (11083-85) as copies of Giant A/B/C. 301 descriptors on 78 models, 0 refused.
  Seen: Lord Xeen beside the Screamer in XD-21, the Pet's wing on X6 (`xeen_tiers_claude/ingame_s7/`); Corak and the
  elementals by GLB renders (`work_s7/corak.png`) until rows can be spawned.
- **DD-05's Golden Pegasus (session 7, A8): done.** World decoration `xeen_pegasus` (row 4012, sprite 27012), bound in
  the new `worlds/xeen/models/indoor_decorations.yml` to `worlds/xeen/world_items/models/item_xeen_12349.glb`, height
  43.4, radius 20. DD-05 loads with it.
- **D-49 (session 7), no Meshy:** the People `Xeen Giant D/E/F` on their own copy `xeen_m520.glb` (from `mm8_m520`, the
  wild giants' MM8 cyclops body; `spec_people.json` + fur channel 1 `body_people_fur.json`): `xgia_d` grey fur, moss
  bands; `xgia_e` grey fur, ochre; `xgia_f` white fur, teal; wild giants A-C stay on `mm8_m520` (no MM9). Barbarian
  Archer 11104 / Archer Chief 11105 bound ahead of A2's rows as `Xeen Barbarian D/E` on `xeen_arc1` skins `xarc_d`
  (blue sleeves and shorts, dark fur vest, grey-brown boots) / `xarc_e` (crimson, black vest, black boots); new vest
  and boots channels (`body_archers_vest.json`, `body_archers_boots.json`; other ranger skins unchanged). Genie lamp
  (Q-D27): world decoration `xeen_genielamp` (row 4013, sprite 27013) on MM7's Genie Lamp item model
  `engine/world_items/models/item_7item260.glb` at 1.5x (height 23, radius 25), bound in decorations.yml and
  indoor_decorations.yml. Row 4014 / sprite 27014 reserved for the Enchanted Boulder (hand-built, queued). Tethered
  griffin 11913 `Xeen Tethered Griffin` bound to MM7 `mm7_m258` `m258_a` (Griffin A, scale 62.7). 304 descriptors on 80 models, 0 refused; seen in
  XD-21 (`xeen_tiers_claude/ingame_s7/s7-d47-sheet.jpg`: elementals E/F/G, Corak, giants vs People).
- **D-50 (session 7), no Meshy:** `Xeen Slick the Gamemaster` (11914) on `xeen_mer1.glb` (copy of `mm6_mer1`) skin
  `xmer_s` (royal purple tunic, gold hems; no club attachment); `Xeen Lacey` (11915) on MM8 Unicorn A (`mm8_m544`,
  skin `unicorn`, white); `Xeen Stumpy` (11916) on MM7 Treant A (`mm7_m479`) at scale 125 (~500 tall; MM7's 288.5 gives
  1,154). 307 descriptors on 82 models, 0 refused; seen in XD-21 (`ingame_s7/s7-d50.png`). Lesson: a binding for a
  descriptor the table lacks makes the whole manifest fail to load: bind only after A2's row exists, and run
  `build-xeen/game/openyamm --world xeen --headless-validate-actor-models` after every binding change and before stopping
  (A2's renames break it too: 2026-11-21 Power/Skeletal Lich). Queued:
  `xeen_waterfall` (water preset of the sand-fall build, ~1,700, XD-17's east cliff) and the Enchanted Boulder
  (row 4014), one decoration sub-agent after the Sphinx; DD-12's aviary bird `xeen_cagebird` (row 4015, sprite 27015 reserved; a Xeen copy of MM9's crow, idle `Perch`/`PerchFidget`, static perched rest copy) in the same sub-agent; optional high-striker pole and doll shelf not started (the
  dolls 12367-12371 already have ground models).
- **D-52 skins (session 7), no Meshy:** Ambrose 11917: `xeen_kni` new skin `xkni_h` (forest-green trims, bright plate;
  `spec_knights.json`); Queen Kalindra 11918: `xeen_sorc` new skin `sorc_k` (near-black violet gown, deathly grey-blue
  skin through a new skin channel 1, `spec_kalindra.json` + `body_kalindra_skin.json`, built from the session-6 source
  kept as `work_s7/xeen_sorc_src_s6.glb`; other sorceress skins unchanged). Both reinstalled, 0 refused. Bound `Xeen Ambrose`
  (Knight A's binding) and `Xeen Queen Kalindra` (Sorceress A's), plus `Xeen Octopod D` (11473, A2's stand-in until the
  octopod); 310 descriptors on 82 models, 0 refused; seen in XD-21 (`ingame_s7/s7-d52.png`). D-52 (1):
  the octopod gets a ground-origin descriptor for DD-14's stationary row 11473 if its swimmer binding centres the body
  (octopod brief).
- **D-56 skins (session 7), no Meshy:** Prince Roland `xeen_kni` skin `xkni_r` (royal-blue trims, bright plate; A4's
  npc14405), Queen Kalindra's wedding look `xeen_sorc` skin `sorc_w` (royal purple gown, fair skin through channel 1;
  npc15001). Both reinstalled (all other knight and sorceress skins unchanged), 0 refused. Bound `Xeen Prince Roland`
  (11920) and `Xeen Queen Kalindra Wedding` (11921); `Xeen Dragon Pharaoh` (11919) on its own figure `xeen_pharaoh.glb`
  (skin `pharaoh_a`, nemes and book attachments; MM8 Lizardman Warrior copy, no Meshy; `xeen_pharaoh_claude/`). 313 descriptors on 83 models, 0 refused. The rest of D-56 (Dragon Pharaoh figure, stone hands,
  Cube and Scepter decorations, cake on a table, Rest Stop bench; rows from 4017) is in sub-agent `xeen-s7-p5`.
- **P5 props (D-56, session 7, sub-agent `xeen-s7-p5`): done**, 0 cr (`xeen_p5hands_claude/`, `xeen_p5props_claude/`,
  READMEs there). Rows/sprites 4017-4022 / 27017-27022 in `indoor_decorations.yml`: `xeen_stonehand` (right hand,
  WEST) and `xeen_stonehand_l` (mirror, EAST): ivory marble with gold veins on a stepped plinth, 448 tall, radius 124,
  palm centre 390 over the origin; `xeen_cube` (height 84, z_offset 394) and `xeen_scepter` (height 21.7, 175 long,
  z_offset 398) placed at the hand's own x/y and floor z, facing 0; `xeen_cake` (MM9 round table copy + built
  three-tier cake, 162 tall, radius 82); `xeen_bench` (MM9 bench01 copy, 56 high, radius 40). Hands, cake and bench
  carry yaw_offset -90 so A5's facing means the direction looked (270 = south). Seen in a scratch overlay on X6; not yet
  in P5. Pharaoh: 231 units tall at scale 125 (A2's descriptor height 160 could be ~230).
- **P5 (session 8): complete on S's side.** Pharaoh, Roland, wedding Kalindra bound; 4017-4022 bound in
  `indoor_decorations.yml` with their models installed; 0 refused. A5 builds with `P5_DECO=1` (A1 merge point 26:
  BLV projects take the world's decorations). Decorations 4014-4016 have rows and sprites but no models or bindings
  yet (Next 1).
- **Planes' pieces (D-58 C5/C7, session 8): done**, 0 cr, rows 4023-4042 bound in `indoor_decorations.yml`
  (merged by `xeen_tiers_claude/merge_deco.py`), all models installed, 0 inverted, P3/P4 load clean, 333 descriptors
  0 refused. Sleepers 4023-4026 `xeen_sleeper_fire|air|earth|water` (sub-agent, `level_generation/decorations/
  xeen_sleeper_claude/`): MM6 Titan `ttn_b` asleep on an Ancient-steel couch 644 x 324 with element glow windows,
  206.4 high, radius 290, `yaw_offset` -90 (facing = the open long side; head on the viewer's left). Statues 4027-4030,
  pedestals 4031-4034, daises 4035-4038 (12-sided, radius 226, 10 high, over A6's discs), Drowned Bell 4042
  (sub-agent, `xeen_planes_claude/`, README has A6's placement table): fire statue with its own black plinth
  (673.4, radius 224), air on MM8 `mm8_m508` (MM6's air elemental is only a funnel) 540, earth `mm8_m504` 479.9, water
  `mm7_m210` with a jar 542; all `yaw_offset` -90. Ways up 4039-4041 `xeen_wayup_fire|air|earth` (`xeen_wayup_claude/`:
  additive scrolling shells, 1,400/2,000/2,400 high, radius 0). Seen: sleepers and props spawned at their L1 spots in
  P1-P4; columns as placed decorations in an X6 overlay (debug `model spawn` ignores blend state). A6 places and wires.
- **P4 octopods (session 8):** at A6's height (`above_floor` 512) they hover mid-sea and read as swimmers, but the
  surface foam ring draws with them under water. `xeen_octopod_deep.glb` (the foam node emptied,
  `xeen_octopod_claude/scripts/deep_variant.py`) installed and seen clean through an overlay; row 11471 also swims on
  D4 (foam wanted), so P4 needs its own row: asked A2 for `Xeen Octopod E` (copy of 11471); binding ready in
  `xeen_octopod_claude/integration/actors_deep.yml`.
- **D-58 bindings (session 7):** `Xeen Air/Water/Earth Elemental A-C` (11700-11722) on A2's stand-ins (`mm6_aie1`
  aie1_b/c/c, `mm7_m210` m210_b/c/c, `mm8_m504` m504_a) until their own tier skins (D-58 queue); `Xeen Outlaw E` (Sky
  Bandit 11116) on `xeen_thf` new skin `xthf_e` (pale sky-blue cloak; `spec_outlaws.json`), reinstalled. 323
  descriptors on 83 models, 0 refused.
- **D-57 first part (session 7, A7's blockers): done**, no Meshy. `Xeen Golem D` (Onyx Sentry 11585) and `Xeen Golem E`
  (Onyx Warden 11586) on `xeen_m254` new skins `xgol_k` (blue-black, steel-blue stripes) / `xgol_l` (red-black,
  blood-red stripes), copied from `xgol_e` (`spec_d57_golems.json`, built on the installed source; every other golem
  skin unchanged); `Xeen Mummy D` (Ghost 11273) and `Xeen Mummy E` (Phase 11274) on `xeen_mummy` new skins `mummy_d`
  (pale grey-blue) / `mummy_e` (dusky violet): the mummy's skins are separate textures (no region mask), so the new
  `xeen_tiers_claude/texture_skin.py` copies mummy_a's materials with recoloured base-colour images
  (`spec_d57_mummies.json`); `Xeen Picard the Aged` (11922) on `xeen_sor1` new skin `xsor_g` (faded grey-brown robe,
  gold trims, white hair and beard). Reinstalled, 328 descriptors on 83 models, 0 refused; all seen in XD-21
  (`ingame_s7/s7-d57-sheet.jpg`).
- **D-61 bindings (session 7):** `Xeen Sheltem` (11924) on `xeen_sor1` new skin `xsor_h` (near-black robe, crimson
  trims, dark hair; reinstalled, other wizard skins unchanged); `Xeen Voweless Knight` (11925) as Xeen Dark Knight A
  (`mm6_kni` `kni_a`). 330 descriptors on 83 models, 0 refused. Not yet seen in game.
- **D-62 bindings (session 7):** `Xeen Mad Dwarf D` (Bosco's Guard 11054) on `xeen_dwa1` new skin `xdwa_d` (steel-grey
  tunic, deep red trousers; `spec_mad_dwarves.json`); `Xeen Crawler D` (Cinder Roach 11363) on `xeen_mantis` new skin
  `mantis_ash` (ash-grey chitin, rust, ember-orange joints and eyes, from `mantis_lava` with its emission;
  `spec_d62_cinder.json`, built on the installed source); `Xeen Sandro Risen` (11926) as Xeen Sandro (`mm6_lch`
  `lch_c`). Both models reinstalled; 333 descriptors on 83 models, 0 refused; previews only, not yet seen in game. The
  four Peasant Dwarf bindings wait for A2's descriptors (none in the table yet); the heart jar is queued.
- Lane tools: `xeen_tiers_claude/bin/blender` (wrapper: one Blender at a time across the lane's sub-agents, `flock`); `rebind.py` and `bind.py` now write by temp file + rename (hard-link scratch roots).
- Installed sources stay in `assets_source/worlds/xeen/models/` (xeen-o excluded `/worlds/xeen/` in the submodule's
  local exclude).

- **Session 9 (2026-11-21, `xeen-s9`), no Meshy (total 330):**
  - **D-66 seats and statue: done.** No MM6-MM8 throne decoration exists; MM9's throne is copied into Xeen (D-44).
    Rows 4043-4046 are in `indoor_decorations.yml` with yaw_offset -90:
    - `xeen_throne` (red; DD-08's Emotion Thrones and Dunce, FD-02's Throne of Legends);
    - `xeen_throne_steel` (DD-17's apse);
    - `xeen_throne_gold` (the Euphoria Throne);
    - all three 250 tall, radius 70;
    - `xeen_statue_teal` (MM8's elf statue in teal metal on a steel plinth, 300 tall, radius 60; DD-17's four statues).

    Seen as spawns in DD-08 and DD-17. Details in `level_generation/decorations/xeen_throne_claude/README.md`.
  - **XD-17 waterfall: installed and bound** (row 4016, `indoor_decorations.yml`, height 2135.22, yaw_offset -90).
    - A5's L4 east cliff is a 49-56 degree slope, not the sheer face the session-7 free fall assumed.
    - So it was rebuilt as a cascade down the measured rock (preset `waterfall_xd17`), with `scripts/fit_xd17.py`
      lifting the sheet off A5's triangulated rock.
    - The origin is the foot point (6272, 2304, z 0), facing 200.
    - Seen as a spawn in XD-17. A placed check (additive layers) waits on A5's rebuild.
    - The hard-link `work/root` was removed.
  - **`Xeen Octopod E`** (11474) is bound to `xeen_octopod_deep.glb`.
  - **Dark knights in black and red (D-61):** `xeen_kni` skins `xkni_i` (Slayer, Voweless Knight), `xkni_j` (Death),
    `xkni_k` (Doom). Seen in XD-21 with Sheltem `xsor_h` beside Corak.
  - The Peasant Dwarves are dropped: MM7's bindings serve them (A2).
  - **Sandro's heart jar:** `xeen_heartjar` (4047; MM7 vase dec97 in glowing green glass).
  - **FD-04's eggs:** `xeen_dragonegg` (4048; the Dragon Egg ground model at 2.34x).
  - **Ways up (A6's look):** P3's dust shaft is dimmer and translucent; P1's heat column is a paler, wider shimmer with
    bigger embers. Both are reinstalled and seen at A6's poses.
  - Validate: 334 descriptors on 83 models, 0 refused.

- **Session 10 (2026-11-21, `xeen-s10`), no Meshy so far (total 330):**
  - **FD-04's lizard: done.** `xeen_lizard` (row 4049 / sprite 27049). It is MM8's Thunder Lizard, still at
    `Standing` frame 0, skin A baked, its own four LODs (7,584 / 3,791 / 1,895 / 943), 50 tall and 87 long, radius
    24, `yaw_offset` -90. It was seen as a spawn in FD-04's alcove.
    - Project: `level_generation/decorations/xeen_lizard_claude/` (README).
    - A7 sets `S_LIZARD = 'xeen_lizard'` (and `S_EGG = 'xeen_dragonegg'`) in `fd04/tools/gen.py`, facing 0.
  - **FD-02's lectern: done** (D-63 polish). `xeen_lectern` (4050 / 27050) is a hand-built carved stand in the Throne
    of Legends' wood atlas, with MM9's open book copied in: 120.5 tall, radius 28. It was seen as a spawn in the Home of
    the Aged. Project: `xeen_lectern_claude/`. The chair is `xeen_throne` (session 9), already placed by A7.
  - **XD-17 waterfall, placed look: fixed.**
    - Cause: COLOR_0 never reaches the game's static shader, so every vertex fade was lost.
    - The mist, foam and veil fades are now baked into the textures.
    - A stream wells up in the gully 760 behind the notch.
    - The strands run over the grass strip into the pool.
    - Height 2,279.28: the binding and row 4016 were updated, and the model reinstalled.
    - Seen placed at A5's poses (`xeen_waterfall_claude/review/s10/sheet.jpg`). A5's placement is unchanged.
  - **P1's heat column, grey edge: fixed.** The side fade is now in the heat texture, the shimmer is amber and twice as
    strong. Reinstalled under the same name and seen at A6's poses (`xeen_wayup_claude/review/s10b/`).
  - **Sheltem in DD-17 (A8): not a model fault.** A8's screenshot tour loads DD-17 without the Soul Box, so the arrival
    check refuses the party and the reveal never shows.
    - Entered from D6 with the Soul Box, the two `SetMonGroupBit` lines show Sheltem and Corak by the throne
      (`level_generation/creatures/xeen_tiers_claude/work_s10/sheltem/sheet.jpg`).
  - **D-69 (A8, FD-01's nook):** MM6–MM8 have no pyramid or obelisk decoration, so A8 shapes one.
    `xeen_statue_teal` serves FD-01's undercroft.
  - **DD-12's cage bird: done** (sub-agent; `level_generation/decorations/xeen_cagebird_claude/`, README there).
    `xeen_cagebird` (4015) is an animated decoration.
    - The bird is MM9's crow copied into Xeen, its eagle skin baked and recoloured canary yellow. It stands 38 over a
      perch bar in a dark-iron tray cut from `xwcage` (120 wide, 46 deep, 50 tall).
    - `model` is the rigid static copy for picking; `animated` is `xeen_deco_cagebird_anim.glb` with idle `perch`
      (5.1 s: Perch three times, then PerchFidget).
    - Origin: the tray's back edge middle on its underside. Facing: out of the wall. Radius 0.
    - Bound by merging `integration/indoor_decorations.yml`; DD-12 loads with no decoration errors.
    - All eight cages were seen animating, out of step, as spawns (`review/ingame/sheet.jpg`).
    - A8 places it: north wall (y 3008) x -3168/-2784/-2400/-2016 facing 270; west (x -3424) y 2624/2240 facing 0;
      south (y 1600) x -3168/-2784 facing 90; z = panel bottom (-2496).
    - Open: the `xwcage` gaps show sky behind the birds; A8 could recess the cages 48–64. One canary look for every
      cage.
  - **The Enchanted Boulder: done** (sub-agent, 0 cr; `level_generation/decorations/xeen_boulder_claude/`, README
    there). `xeen_boulder` (4014, outdoor `decorations.yml`).
    - The shape is MM8's `rock26`, with MM6's bearded mage face (`mm6_pmn2`) carved in as a weathered relief. One
      sandstone texture (MM6 `egywalh`) covers the whole piece.
    - LOD 6,199 / 3,099 / 1,548 / 773; height 279.7; `yaw_offset` -90; `lod_pixels [300, 150, 60]`. 300 across, 330
      deep.
    - The face reads at 300 and 1,000; at 3,000 it is a great rock. Seen on D5 from a scene overlay
      (`review/ingame_v2_sheet.jpg`).
    - For A2: row 4014 radius 165, height 280.
    - For A6: face each boulder outward from its ring's centre; z at the terrain, no offset. `gen.py` picks the model
      by name. The rings could widen to 230 (west) and 340 (east) so the rocks don't touch. Then rebake D5.
  - **D7's sky-barges and celestial boat: done** (sub-agent, 0 cr; `level_generation/decorations/
    xeen_skybarge_claude/`, README there).
    - `xeen_skybarge_fire|air|earth|water` (4051–4054, height 721): 1024 x 384 hulls with a gilt rail, a tinted
      sail with a glowing sigil, a canopy and a gangplank. LOD 2,772 / 1,520 / 648 / 320.
    - `xeen_skyboat` (4055, height 569): 736 x 266, pale-blue sail. LOD 2,440 / 1,232 / 572 / 276.
    - All radius 0, `yaw_offset` -90. Origin: the deck's centre at deck height. Facing: the way the prow points; the
      gangway side is facing + 90.
    - The tints pair smoke with fire, dust with air, steam with water and mud with earth.
    - Seen as spawns on D7 (`review/ingame/`).
    - A6's placement table (positions, floor heights, facings; the barges are not boardable; the dust merchant moves
      off the causeway; the boat goes alongside the jetty at (1429, 2423), facing 327) is in the README and the
      session-10 report.
  - Lesson: **glTF COLOR_0 is not drawn by the game's static models** (the instanced shader takes placement
    lighting there). Fades on additive or blended decorations must live in the texture: `u_fade` / `v_fade`, with v
    mapped once and no scroll on that axis.

- **Session 13 (2026-11-21, `xeen-s13`), no Meshy (total 330): the review's tunings (G3 review, "Follow-ups → S").**
  - **Hell Hornet (11350): done.** Crimson lifted about 20 % (contrast 1.7 -> 1.35) and the wings glow ember red
    (emission on `xwsp_a` only). It reads red in daylight and glows in XD-21's dim room
    (`level_generation/creatures/xeen_tiers_claude/ingame_s13/hornet_v2.jpg`).
  - **Guardian of Air (11702): done.** Pale gold sheets and rich gold streaks (`xaie_guard`); at 2,000 it is a gold
    column beside the white Lesser Air Elemental (`ingame_s13/air_v3.jpg`). An emission try glowed like a fire column
    and was dropped (`air_v2.jpg`).
  - **Power Lich 11284 and Skeletal Lich 11285: done** (D-57 Q30). New Xeen copy `xeen_lch.glb` of `mm6_lch` with three
    body channels; `Xeen Lich D` = `xlch_d` (gunmetal bones, bronze, glowing violet bracers; Darkside 34), `Xeen Lich E`
    = `xlch_e` (teal bones, violet mail, orange rags, red bracers; Darkside 49). Lich A-C stay on `mm6_lch`. Seen
    beside the Lich Lord in daylight and XD-21 (`ingame_s13/liches_v2.jpg`).
  - Validate: 335 descriptors on 84 models, 0 refused. Tables and rebuild steps: `xeen_tiers_claude/README.md`
    "Session 13".
  - **Heart jar and balloon basket (optional polish): built, NOT installed** (a lane sub-agent, stopped at the
    usage-limit checkpoint). The installed jar and basket are unchanged.
    - New jar: translucent green glass with a dark pulsing heart inside. It is at
      `level_generation/decorations/xeen_heartjar_claude/work/s13/xeen_deco_heartjar.glb`, winding 0, not seen in game.
    - New basket: a torn envelope and ropes behind and to the left of the basket, with wrecked wicker; 2,848 triangles,
      height unchanged, footprint 312 x 414. It is at `xeen_planedevices_claude/work/basket/xeen_deco_balloonbasket.glb`
      (this overwrote that work export; the installed copy is the old one). Winding not checked; not seen in game.
    - Resume steps are in each project's README, under "Session 13".
  - P1's ember disc: A6 has not asked (A6.md); not built.

- **Session 14 (2026-11-21, `xeen-s14`), no Meshy (total 330): the heart jar and the P2 basket installed.**
  - **Heart jar (4047, DD-21): installed.** Seen on DD-21's ledge: reads as green glass with the heart inside; the
    belly glow had washed the heart to tan, so the glow peak was lowered and the heart made redder (`build.py`), then
    rebuilt, winding 0, reinstalled. Sheets: `level_generation/decorations/xeen_heartjar_claude/review/s13/
    before_after.jpg`, `heart_v1_v2_crops.jpg` (middle column installed), shots `review/s13/after2/`.
  - **Balloon basket (P2): installed** as built in session 13 (winding 0; 2,848 tris; height 162.1 = binding). The
    torn envelope lies on the isle's open top, well inside the edge and clear of the chest; not shortened. Sheet
    `level_generation/decorations/xeen_planedevices_claude/review/s13/before_after.jpg`.
  - Rows, bindings and placements unchanged: no map lane needs to re-place; `stale_bakes.py --check` 0 (DD-21 needs no
    rebake). Validate: 335 descriptors on 84 models, 0 refused. Rollback sources kept beside each export
    (`installed_s9_heartjar.glb`, `installed_s11_balloonbasket.glb`).
  - P1's ember disc: not asked; not built.
  - Scratch: the great tree's 13 GB hard-link `assets_dev` copy (`xeen_greattree_claude/work/ingame/root/`, mostly
    shared inodes, about 60 MB real) deleted; the other projects hold working data only (no other roots).

## Log

- 2026-11-20 lane created by the orchestrator.
- 2026-11-20 started: toad and witch masters (Codex), Smart Topology for both.
- 2026-11-20 toad installed and bound; stand-in bindings merged (238); swarm B/C installed and bound; witch and sprite
  delegated to sub-agents; Doom Bug cricket in progress.
- 2026-11-20 Doom Bug installed and bound; `--world xeen --headless-validate-actor-models`: 238 descriptors, 0 refused.
- 2026-11-20 sprite installed and bound (sub-agent); goblin/gremlin tiers installed and bound; the remaining tier
  families started in a sub-agent; toads, swarm and goblins seen in game in XD-21.
- 2026-11-20 witch done; colour tiers of all 17 remaining Acts I-II reused families installed and bound (sub-agent).
- 2026-11-20 session 2: orc two-swords checked (overlapping spawns, no fault); D-10 body regions for golems, ogres,
  werewolves, orcs installed and checked in game; witch clearance pass (`elbow_clear.py`) in the chain, witch
  reinstalled and seen in game; A2's new bindings (Sorceress D, Head Sorceress, Mountain Gargoyles, Crodo) added.
  Meshy spend this session 0 (total 90).
- 2026-11-20 session 2 (cont.): gargoyle tiers (xeen_gar, 6 skins) installed, bound, seen in game; Flying Feet and
  Guardian started by two lane sub-agents and stopped at stage 1 (native study) for the orchestrator's handover;
  0 credits spent on them.
- 2026-11-20 session 3 (`xeen-s3`): Flying Feet and Guardian built by two sub-agents, installed, bound (A, B), seen in
  XD-21 (30 cr: 15 + 15); Renegades, Ghost Rider, Dark Sprites (two new sprite tiers), Ogre D bound (252 descriptors,
  0 refused); Carnage Hand and mole HD masters; the seven quest-item masters and Meshy requests (not run). D-19 queued.
  Quest-item Smart Topology 35 cr; mole 15 cr; Carnage Hand 15 cr. Meshy
  total 185.
- 2026-11-20 session 3 (cont.): quest-item Smart Topology run (35 cr); Carnage Hand and mole built by two sub-agents,
  installed, bound, seen in XD-21 (15 + 15 cr); bindings for A2's D-25, DD-04, DD-09 and D2 rows; Dire Rat tier
  `xrat_d` (D-26); the great-tree crown planned (no Meshy). 275 descriptors on 63 models, 0 refused.

- 2026-11-20 session 4 (`xeen-s4`): great-tree crown built, installed, bound as world decoration `xeen_greatcrown`, seen on D2 (scratch root); the seven quest-item ground models installed, bound, seen in X1; Master Thief skin `xthf_d`; Sorceress HD masters; sand-fall (D-31) installed and bound, seen on X5 (scratch root); hay bale, woodpile and Crodo's bottle modelled, installed and bound (engine), seen on X1. Sorceress built, installed, bound (20 cr). Meshy spent this session 20 (total 205).

- **A2's DD-02/DD-09 characters (session 5): done.** Xeen Ellinger (mm7_m274 m274_b), Nathan and Sky (mm8_m620
  bedraggled_a/b), Alicia the Just (mm7_m342 m342_aa), Princess Sheewana (mm7_m372 m372_aa) from A2's fragment
  `output/xeen_a2_check/bindings_characters_dd02_dd09.yml`; 280 descriptors on 67 models, 0 refused.
- **Snow Beast (session 5): done.** `xeen_bf.glb` (MM9 bigfoot copy, skin `xbf_a`), `Xeen Wolf C`, scale 95; XD-21.

- **Bat storm (D-36): done** (session 5, no Meshy; `level_generation/decorations/xeen_batstorm_claude/`, README there).
  World decoration `xeen_batstorm` (row 4003, sprite 27003; entity `decoration_list_id` 4002): `animated:
  xeen_deco_batstorm.glb` (24 bats of 249 triangles = 5,976, 480 joints, three rings of 7/10/13 m at 0/2.6/5 m, clip
  `storm` 12 s seamless, `idle: storm`), static `model` its rigid rest copy; one blended material (no runtime or baked
  shadow); `height` 666.4, about 2,650 across. Origin = the storm's centre at the lowest ring: place 300-500 above the
  keep's top (bats -70..+600 around it). Seen placed on D2 from a scratch root (`review/ingame/placed/sheet.jpg`).
- D-36 (2): the octopod's origin goes at the water surface (D4's octopods swim): in its sub-agent brief.

- **Mantis: done** (session 5, sub-agent; `level_generation/creatures/xeen_mantis_claude/`, README there). Darkside
  image 10; `xeen_mantis.glb` (56 rigid chitin pieces on 25 bones, 8,386 / 4,192 / 2,919 / 1,677 tris), skins
  `mantis_a` (Mantis Ant, native violet, teal eyes), `mantis_b` (Warrior, bronze-green), `mantis_c` (Queen, black-violet
  and gold, scale 160.8 = 1.2x), `mantis_lava` (Lava Roach = Xeen Crawler C, Darkside image 33: dark grey, glowing
  joints, eyes and chest cracks, emission on that skin only); scale 134 (147 units tall); Attack impact 0.50; floor
  audit ok. Bound (Xeen Mantis A/B/C, Xeen Crawler C), 280 descriptors on 68 models, 0 refused; all four seen in XD-21
  (`xeen_tiers_claude/ingame_s5/s5-mantis.png`). 15 cr. Limits: the roach's long antennae and fire-ring attack not
  modelled (its cracks glow all the time); the red abdomen tip stays red on every skin.

- **D-39 tiers: done** (no Meshy). `xeen_sor1`: `xsor_d` Cult Acolyte (11197, grey-brown) and `xsor_e` Basenji Cult
  Leader (11198, near-black robe with wolf-grey trim via a new trim region); floating mages on a Xeen copy
  `xeen_m426.glb`: `xfm_a/b/c` (Mystic/Magic/Mega, rebound), `xfm_d` Floating Adept (11203), `xfm_e` Floating Magus
  (11204). Installed, 0 refused. The new rows bind when A2's descriptors exist (A2 told the skin names).

- **D-40 lava fall: done** (no Meshy). `presets.py` `LAVAFALL` on the sand-fall build (emissive core, dark crust
  streaks, additive heat haze; `build_fall.py` gained per-layer emission, the sand-fall rebuilds byte-identical);
  `xeen_deco_lavafall.glb` 1,609 tris, world decoration `xeen_lavafall` (row 4004, sprite 27004), height 2,385.06,
  `yaw: facing`, origin at the lip as the sand-fall. Seen glowing and scrolling in game (debug spawn).
- **D-40:** XD-16's demon and devil idols (no MM6-MM8 engine statue fits: the engine has statuettes, an elf, a
  dwarf, two plinth statues; plan: stone statues posed from the installed `mm6_demon` and `mm9_lesserdemon`/
  `mm9_greaterdemon` creature models on plinths, dark volcanic stone, no Meshy) still to make. Black basalt rock:
  **done** (`level_generation/decorations/xeen_basalt_claude/`): `xeen_basalt1/2/3` (rows 4005-4007, MM6 rocks
  retextured near-black, heights 300/340/380, radius 150/170/190); a basalt terrain material, if wanted, is A6's.

- **Sabertooth: done** (session 5, sub-agent; `level_generation/creatures/xeen_saber_claude/`, README there).
  Darkside image 44; `xeen_saber.glb` (own quadruped rig, procedural: four-beat walk, gallop, Sprint for MAW; 10,133 /
  5,065 / 2,532 / 1,266 tris; cut-open mouth with a red cavity), skin `saber_a` (tawny; mask fur, pale fur, fangs and
  claws, irises), scale 150 (191 units to the ears, 337 to the tail tip: clearly over the Dark Wolf's 158), Attack
  impact 0.50. Bound `Xeen Wolf B` and `D`; 280 descriptors on 69 models, 0 refused; seen in XD-21 beside the Dark Wolf
  and the Snow Beast (`xeen_tiers_claude/ingame_s5/s5-wolves.png`). 15 cr. The rows' collision height 160 (model 191).

- **D-42 tiers: done** (no Meshy). `xeen_cle` `xcle_g` (DD-05 Cult Leader 11223: white vestments, crimson trim,
  gold cloak), `xeen_witch` `witch_d` (Darkside Head Witch 11173: bone-white robe); installed, A2 told; they bind when
  A2's rows exist. Royal Vampire (11295): `xvam_d` (royal purple, silver hair) on a Xeen copy `xeen_m422` (vampires
  A-C rebound to it with their old skins). A2's D-42 draft bound (Coven Head Witch `witch_d`, Cult Leader `xcle_g`,
  Vampire D `xvam_d`, captives, clerics): 294 descriptors on 71 models, 0 refused; seen in XD-21.
- **A2's D-39 draft bound** (`output/xeen_a2_check/bindings_d39.yml`): Wizard D (Cult Acolyte) `xsor_d`, Basenji Cult
  Leader `xsor_e` (not Valio's `xsor_b`), Floating Mage D/E `xfm_d`/`xfm_e`, Madman D; 285 descriptors on 69 models,
  0 refused.

- **Scorpion: done** (session 5, sub-agent; `level_generation/creatures/xeen_scorpion_claude/`, README there). Clouds
  image 19; `xeen_scorpion.glb` (17 Meshy pieces, 40-bone rig: legs, pincer arms with snapping fingers, 5-segment tail
  and stinger; 7,921 / 3,960 / 1,980 / 984 tris), skin `scorpion_a` (dark brown; mask carapace, legs and pincers,
  stinger, eyes), scale 143 (229 wide and long, tail 119 high), Attack impact 0.467 (the sting over the head). Bound
  `Xeen Crawler A`; 294 descriptors on 72 models, 0 refused; seen in XD-21 beside the Mantis Queen and the Lava Roach
  (`xeen_tiers_claude/ingame_s5/s5-scorpion.png`). 15 cr.

- **Electrapede: done** (session 5, sub-agent; `level_generation/creatures/xeen_electrapede_claude/`, README there).
  Darkside image 7; `xeen_electrapede.glb` (segmented rig, travelling body wave, metachronal legs; LOD0 9,232 tris),
  skin `electrapede_a` (green body, magenta eyes and legs), scale 140, Attack impact 0.533 with glow at
  `Socket_Mouth` and both antenna sockets (the lightning). Bound `Xeen Crawler B`; 294 descriptors on 72 models,
  0 refused; seen in XD-21 biting the party with the mouth and antenna glow
  (`xeen_tiers_claude/ingame_s5/s5-electrapede.jpg`). 15 cr.

- 2026-11-21 session 14 (`xeen-s14`): heart jar (redder heart, lower glow) and P2 basket (torn envelope) installed and seen in DD-21 / P2; 0 refused, 0 stale
  bakes; great tree hard-link root deleted. 0 cr (total 330). Details in State, "Session 14".

- 2026-11-22 lane P (packaging) for S: cook sidecars on 22 Xeen decorations (`assets_source/worlds/xeen/models/
  xeen_deco_*.cook.yml`, the user's approval of 1K decoration textures where it does not matter). `max_size: 1024` on
  the six small ones that keep over 128 texels per metre at 1K (cagebird_anim, lizard, stonehand_l/r, drownedbell,
  statue_teal); `normal_scale: 0.5` (relief at half, colour kept 2K, as the engine's decorations cook) on the 16
  statue-sized ones (statue_air/earth/fire/water, boulder, idol_devil/demon, sleeper_air/earth/fire/water,
  skybarge_air/earth/fire/water, skyboat); the great crown and both sphinxes untouched. Winding 0 on all 25, cooked
  with `cook_models.py --only` (GLBs rewritten identically, 20 textures), cooked model textures 601.7 -> 565.7 MiB, no
  stale bake from it. A new Xeen decoration with 2K maps: give it the same sidecar by its size. Seen in P1
  (`output/xeen_p/shots/p1_decos/`).

## Session 5 plan: the Act III–IV creatures (2026-11-20)

Markers counted in the installed scenes (spawn points per map_stats slot; tiers from map_stats' level range) and the
native images (Clouds `xeen.mon`, Darkside `dark.mon`, image byte at offset 47):

| Order | Model | Rows it serves | Seen where (markers) | Native | Estimate |
|---|---|---|---|---|---|
| 1 | `xeen_mantis` | Mantis Ant/Warrior/Queen 11370-72; **Lava Roach 11362 as a mantis skin** (Darkside image 33 is the same upright four-legged, two-armed insect in grey with glowing red) | D3 slot 1, tiers B-C (24), DD-18; D1 slot 3 tier C | Dark 10, 33 | 15-20 cr |
| 2 | `xeen_saber` | Sabertooth 11411, Kennel Sabertooth 11413 | D2 slot 1, tiers B-C (27), X5 (11), DD-13 kennel | Dark 44 | 15-20 cr |
| 2b | Snow Beast 11412 onto `mm9_bigfoot` as a Xeen tier copy: **done** (`xeen_bf.glb`, skin `xbf_a`, scale 95; seen in XD-21) | | D2, X5 tier C | Clouds 36 | 0 cr |
| 3 | `xeen_electrapede` | Electrapede 11361 (own segmented rig; a centipede does not fit the mantis rig) | D1 slot 3 tier B (15), DD-10A | Dark 7 | 15-20 cr |
| 4 | `xeen_scorpion` | Scorpion 11360 | DD-10A slot 3 tier A | Clouds 19 | 15-20 cr |
| 5 | `xeen_sandworm`, `xeen_armadillo` | Sand Worm 11440, Great Worm 11442 (worm skins); Armadillo 11441 | D3 slot 3, tiers B-C (11); X6 (phase 4) | Clouds 56, Dark 5 | 15-20 cr each |
| 6 | `xeen_octopod` | Octopod, Great Octopod, Kraken 11470-72 | D4 lake (phase 4) | Dark 41 | 15-20 cr |
| 7 | `xeen_guard` (D-19) | Xeen Construct D 11603 | XD-19 (phase 5) | Clouds 62 | 15-30 cr |

Each: Smart Topology 5 + 4K retexture 10, one retry kept in reserve; hard ceiling 30 per model. Done this session: mantis, sabertooth, electrapede, scorpion (lane sub-agents, brief `level_generation/creatures/xeen_tiers_claude/ACT34_SUBAGENT_BRIEF.md`).
Crown checked in the real D1 and D2 (A6's installs of 19:10/19:18): it sits on both trunks, limbs out of the trunk
tops, the D2 arrival silhouette and D1's Dark Grove (fog) read (`level_generation/decorations/xeen_greattree_claude/
work/ingame_real/sheet_d1.jpg`, `sheet_d2.jpg`). Dark Wolf (A) stays on
the MM8 wolf (grey, as image 66).

- 2026-11-20 session 5 (`xeen-s5`): crown checked in the real D1 and D2; Snow Beast on a Xeen bigfoot copy; mantis (with
  the Lava Roach skin), sabertooth, electrapede and scorpion built by lane sub-agents, installed, bound, seen in XD-21
  (4 x 15 cr); bat storm (D-36); lava fall preset and basalt boulders (D-40); D-39 and D-42 tiers (Acolyte, Basenji
  Cult Leader, floating mages, Cult Leader, Head Witch, Royal Vampire) and A2's DD-02/DD-09, D-39, D-42 drafts bound
  (294 descriptors on 72 models, 0 refused). Meshy spent this session 60 (total 265).

- **Session 11 (2026-11-21, `xeen-s11`, 09:10), no Meshy (total 330):**
  - **Alister (A7, FD-04): done.** `Xeen Alister` (11923) had no binding, so he drew nothing. Now on `xeen_cle` with a
    new druid skin `xcle_h` (moss-green robe, brown leggings, bark-brown cloak; `spec_cultists.json`), as Cultist A's
    binding (staff, scale 110). Reinstalled `xeen_cle.glb`. Validate 335 descriptors on 83 models, 0 refused. Seen in
    FD-04's west alcove at (-1040, -768) (`level_generation/creatures/xeen_tiers_claude/work_s11/shots/sheet.jpg`).
  - **Body scan: nothing else missing.** All 335 Xeen descriptors are bound; every map_stats spawn family resolves
    A/B/C; the engine rows placed on Xeen maps (MM7 peasants on X1-X7/D1-D4/DD-03/DD-25/XD-04/XD-05/XD-25, Ghost C
    on X2, Swordsman B on X1/X2, Treants on X5/D4, MM6 Druidess on D1/X5, Novice Monk on X5, Journeyman Mage on D4)
    resolve through the MM6/MM7 bindings Xeen depends on.
  - **XD-17 waterfall, the lip: fixed** (A5's `s22_falls` 05/06). The white core no longer runs the gully: a clear
    blue-green `Stream` layer with soft sides follows the gully's measured centre (10 wide at the spring, 100-120 in
    the gully, 180 at the brink), the water goes over the brink glassy, and the white starts below it lane by lane
    (drops 20-190, middle first), so there is no straight edge and no ears on the gully walls. The spring breaks out of
    the gully floor along its shape. 5,376 triangles, height 2,229.46 (binding and row 4016 updated). Reinstalled under
    the same name; seen placed at A5's poses (`xeen_waterfall_claude/review/s11c/sheet.jpg`, README "Session 11").
  - **P1's Ember Font and camp, P2's basket: done** (sub-agent, 0 cr; `level_generation/decorations/
    xeen_planedevices_claude/`, README there). Procedural, no LODs (each under 1,500 triangles), indoor bindings
    (`yaw: facing`, `yaw_offset` -90), sprites 27056-27058:
    - 4056 `xeen_emberfont`: a 12-sided basalt font with glowing, scrolling, pulsing liquid fire 95 above its origin
      (radius 72); height 107, radius 90; 466 triangles.
    - 4057 `xeen_firecamp`: a burnt bedroll, a dented kettle, two charred logs and a stone ring; height 35.53, radius
      0; 1,354 triangles; no light or flame.
    - 4058 `xeen_balloonbasket`: a wicker gondola tilted 17 degrees onto pale rocks, hanging ropes, two sandbags;
      height 162.07, radius 64; 1,364 triangles.
    - Seen as spawns at their spots (`review/ingame/c_p1_sheet.jpg`, `d_p2_sheet.jpg`). For A6: font (-1152, -448)
      z 96, any facing; camp (-3968, -4736) z 0, facing 90; basket (-3712, 4224) z 320, facing 0. The basket's find
      wants 110+ from its centre (today's potions are 100-150 away). The plan's cache "wedged in the basket" stands
      1,400 away at (-5056, 3840).

- **Session 12 (2026-11-21, `xeen-s12`, 15:35), no Meshy (total 330): names and looks.** The user saw in the guide's
  bestiary that the Water Dragon is red: every tier whose name implies a colour or element should look like it.
  Audit below; 27 tiers recoloured or rebound on new Xeen tier copies (`xeen_cdr1` reinstalled; new `xeen_m492`,
  `xeen_m616`, `xeen_aie1`, `xeen_m210`, `xeen_m504`, `xeen_fie1`, `xeen_m476`, `xeen_mnk1`, `xeen_m479`, `xeen_m556`
  with its sword and shield), all installed with `--world xeen` (winding 0 inverted), bound, validate 335 descriptors
  on 83 models, 0 refused. Seen in XD-11's hall (`level_generation/creatures/xeen_tiers_claude/ingame_s12/`). Tables
  in `xeen_tiers_claude/README.md` (Session 12 sections). Two lane sub-agents (elementals; trolls, ninjas, swamp
  things, hornets); new tools `flame_ramps.py` (flame planes without a mask), `new_mask.py` (a mask for the
  mask-less treant); `xeen_tiers.py` gained optional `shadow`/`highlight` hues in `mid` rules (old specs build alike).

## Session 12: names and looks (audit, 2026-11-21)

Every Xeen family's tiers and bosses (308 rows of `source/monsters.yml`, `xeen_tiers_claude/work_s12/all_tiers.tsv`)
checked against the guide's portraits (`output/xeen_site_monsters/`) and the native sprites. Before: the guide
portraits (`xeen_tiers_claude/work_s12/sheet_dragons.jpg`, `sheet_elem.jpg`, `sheet_misc.jpg`, `sheet_misc2.jpg`);
after: `ingame_s12/sheet2.jpg` (dragons, bone dragons, Devil, hydras), `sheet4.jpg` and `guardians_crop.jpg`
(elementals), `sheet6.jpg` (Guardian of Fire, Hell Hornet, ninjas, swamp things), `trolls_crop.jpg` (Ice Troll).

**Fixed (27):**

| Family | Tier | Name | Was | Now | Action |
| --- | --- | --- | --- | --- | --- |
| Cloud dragons | A 11640 | Water Dragon | red `cdr1_a` | turquoise-blue | `xeen_cdr1` `xcdr_water` |
| Cloud dragons | B 11641 | Acid Dragon | navy blue `cdr1_b` | poison yellow-green | `xcdr_acid` |
| Cloud dragons | C 11642 | Fire Dragon | olive-yellow `cdr1_c` | red, orange belly | `xcdr_fire` |
| Cloud dragons | D 11643 | Frost Dragon | red (= A) | ice blue-white | `xcdr_frost` |
| Cloud dragons | boss 11645 | Dragon King | olive (= Fire C) | black, gold edges (D-57 Q3) | `xcdr_king` |
| Dark dragons | A 11650 | Cloud Dragon | native brown-black `m492` | storm grey-white | `xeen_m492` `xdrg_cloud` |
| Dark dragons | B 11651 | Green Dragon | brown-black (= A) | green | `xdrg_green` |
| Dark dragons | C 11652 | Phase Dragon | brown-black (= A) | indigo, cyan wings | `xdrg_phase` |
| Dark dragons | boss 11653 | Energy Dragon | brown-black (= A) | violet-white (D-57 Q30) | `xdrg_energy` |
| Undead dragons | B 11671 | Undead Dragon | white (= A) | rotting grey-green | `xeen_m616` `xbdr_b` |
| Undead dragons | C 11672, Scraps | Dragon Mummy | white (= A) | tan wrappings (Darkside 15) | `xbdr_c` |
| Demons | B 11631 | Devil | green | red (Xeen 70) | rebind `demon_c`; Screamer takes `demon_b` |
| Hydras | B 11661 | Venomous Hydra | many-coloured | green | rebind `hyd_c`; Great Hydra takes `hyd_b` |
| Air elementals | B 11701 | Whirlwind | red `aie1_c` | storm grey-blue | `xeen_aie1` `xaie_whirl` |
| Air elementals | C 11702 | Guardian of Air | red (= B) | silver-white, gold streaks | `xaie_guard` |
| Water elementals | B 11711 | Tidal Terror | orange-brown `m210_c` | deep navy, foam fins | `xeen_m210` `xm210_tidal` |
| Water elementals | C 11712 | Guardian of Water | orange-brown (= B) | sea-green, gold fins | `xm210_guard` |
| Elementals | G 11626 | Lesser Earth Elemental | brown (= Earth A-C) | sandy ochre | `xeen_m504` `xm504_sand` |
| Earth elementals | B 11721 | Earth Blaster | brown (= A) | iron-oxide red-brown | `xm504_blaster` |
| Earth elementals | C 11722 | Guardian of Earth | brown (= A) | dark slate, jade | `xm504_guard` |
| Elementals | D 11623 | Guardian of Fire | = Fire Blower | gold core, crimson flames | `xeen_fie1` `xfie_d` (`flame_ramps.py`) |
| Trolls | C 11072, Warren C 11692 | Ice Troll | green skin, pink trims | frost blue skin, white-blue trims | `xeen_m476` `xtrl_a` (skin region) |
| Ninjas | B 11121 | Shadow Ninja | navy robe | charcoal, violet-slate cast | `xeen_mnk1` `xmnk_a` |
| Swamp things | A 11460 | Swamp Thing | treant default (all three same) | moss green | `xeen_m479` `xswt_a` |
| Swamp things | B 11461 | Bog Thing | (same) | peat brown, olive | `xswt_b` |
| Swamp things | C 11462 | Marsh Horror | (same) | murky black-green, yellow-green | `xswt_c` |
| Hornets | A 11350 | Hell Hornet | yellow wasp | crimson on black, ember wings (session 13: lighter, wings glow) | `xeen_m556` `xwsp_a` (+ sword, shield copies) |

**Already right (about 40):** Lesser Fire / Fire Elemental / Fire Blower, Lesser Air, Air Elemental, Lesser Water,
Water Elemental, Earth Elemental, Megadragon (native m492, now apart from its siblings), Bone Dragon, Xeen's Pet; the
golems (Wood, Stone, Iron, Diamond, Onyx, Onyx Sentry and Warden, Sand, Water, Cloud, Lava, Sky); Obsidian Gargoyle;
Slayer, Death and Doom Knights; Sky Bandit; Ghost and Phase Mummies; Ghost Rider; Spirit Bones; Lava and Cinder
Roaches; Snow Beast; Bog and Swamp Toads; Gamma Gazer (green); Sewer Slug (blue, native); Plague Rat; Dark Wolf (grey,
native); Elder Witch (black); Grave Ghoul; Gorgon Sprites; Mountain Gargoyles.

**Left (3) and accepted:**
- Power Lich and Skeletal Lich (11284/85): done in session 13 (`xeen_lch` `xlch_d`/`xlch_e`).
- Hobstadt keeps `troll_c` (his Darkside sprite is a teal troll chief, not an ice troll).
- Siblings that share a look on purpose: A2's same-name copies (Gremlin D-I, Ogre E-G, Sprite D/E, Octopod D/E),
  extra tiers on a named tier's look (Troll D, Ninja D, Spirit D, Outlaw D, Sorceress D, Orc Warband D, Ogre D) and
  bosses on their `look` tier, as before.
- Guide: the swamp things' portraits are taken from inside the treant (scale 288.5, about 1,150 tall: the capture
  camera stands inside it), and Undead Dragon 11671 and Green Dragon 11651 have no portrait yet (lane G).

## Next

**Session 14 (after `xeen-s14`):** item 1 below is done (both installed). Open: items 2-4.

**Session 13's open list (after `xeen-s13`):**
1. Finish the optional polish the sub-agent left uninstalled (resume steps in each README's "Session 13"):
   - The heart jar: run the in-game tour (`scripts/ingame_tour.py after`), install with `--name
     xeen_deco_heartjar.glb`, validate.
   - The basket: check winding, run the placed tour on `xeen_p2.blv`, shorten the envelope if it leaves the isle,
     install with `--name xeen_deco_balloonbasket.glb`, validate.
2. P1's ember disc for the heat column, if A6 asks (G3 review row 34 is A6's).
3. Look at G's recaptured portraits once they exist: the 31 ids from session 12 and session 13's four (11350, 11702,
   11284, 11285).
4. Session 12's and 11's lists below (placed checks).

**Session 12's open list (after `xeen-s12`):**
1. Lich D/E own recolours (Power Lich, Skeletal Lich: D-57; a Xeen copy of `mm6_lch`).
2. Look again at G's recaptured portraits (REQUESTS: the 31 ids in the session-12 report) and tune any tier that
   reads poorly in the guide's light (the Hell Hornet's dark crimson, the Marsh Horror's specks, the Guardian of Air
   against the Lesser Air Elemental).
3. Session 11's list below.

**Session 11's open list (after `xeen-s11`):**
1. Placed checks once the lanes place them: D7's barges and boat (A6), the Ember Font, camp and basket (A6, P1/P2),
   the lizard and Alister (A7, FD-04), the lecterns (A7, FD-02), the cage birds (A8, DD-12), the boulders (A6, D5,
   after A2's radius 165 / height 280), and A5's re-shoot of the waterfall's lip (`s22_falls` poses) and A6's of the
   heat column.
2. Polish if asked: a bigger bird or per-cage tints (stat birds, parrot, Songbird); a more expressive boulder face;
   the Ember Font's fire a shade less yellow up close.

**Session 10's open list (after `xeen-s10`):** superseded by session 11's list above (the plane devices are done).

Session 8 (`xeen-s8`, 2026-11-21 06:15) found P5 complete on S's side and stopped at priority boundary 1 to report.
Resumed: priority 2 done (State: planes' pieces, P4 octopods); stopped at boundary 2. Open from 2: bind `Xeen Octopod E`
when A2 adds it. Optional plane devices not built: P1's Ember Font and camp, P2's basket (A6's spots; rows from 4043).
Priority 4 additions (D-66): name a shipped MM6-MM8 throne decoration for DD-08's six and DD-17's throne (or say none:
A8 shapes one from Ancient steel); make or name DD-17's teal propaganda statue (now MM6 `sta1a`); DD-08 founder `7dec55`
and DD-15 reliefs accepted; Sheltem `xsor_h` accepted pending A8's in-game look. D7 needs no hut or boards (A6).
Resume order (the orchestrator's session-8 brief): 2. the planes' pieces (D-58 C7: sleeper and couch, four statues,
pedestal and dais, P3's dust column, P4's bell; P4 octopod swimmer check at A6's height), 3. Sheltem / Voweless Knight
looks, Sandro's heart jar, the four Peasant Dwarves (rows 322, 313, 325, 316 on `mm7_m302`/`mm7_m312`), 4. the
decorations (below, DD-08 thrones, knight statue, DD-17 statue, DD-15 Egyptian statue, FD-04 lizard and egg, chair,
lectern, D7 barges, boat, lamps).
1. **Decorations** (sub-agent `xeen-s7-decos` died with session 7; 0 cr): rows 4014-4016 and sprites 27014-27016
   exist, **no models and no bindings**. `xeen_waterfall` (4016, XD-17's east cliff, A5): built and seen in game from a
   scratch mount (`level_generation/decorations/xeen_waterfall_claude/work/waterfall/xeen_deco_waterfall.glb`, 4,010
   tris, 1,200 across, 1,878 high, `review/ingame1`, `ingame2`), not installed, no README: check winding, install,
   bind (decorations.yml, as `xeen_sandfall`), write the README and the placement numbers. `xeen_boulder` (4014, D5's
   Enchanted Boulders, A6) and `xeen_cagebird` (4015, DD-12's aviary, A8; Xeen copy of MM9's crow, idle perch): not
   started (empty `scripts/` folders).
2. **P5 (D-56): done** (checked session 8). Pharaoh bound (`xeen_pharaoh_claude/`), decorations 4017-4022 bound in
   `indoor_decorations.yml`, models installed, 333 descriptors, 0 refused. A1's merge point 26 lets BLV projects take
   the world's decorations, so A5 can build P5 with `P5_DECO=1`. History: (sub-agent `xeen-s7-p5`): Dragon Pharaoh figure (`level_generation/creatures/xeen_pharaoh_claude/`,
   Meshy <= 30 only if a shipped body does not read), stone hands, Cube/Scepter, cake on a table, bench (rows 4017+, named as A5's generator expects: `xeen_stonehand`
   (`xeen_stonehand_l` if the mirror needs a row), `xeen_cube`, `xeen_scepter`, `xeen_cake`, `xeen_bench`);
   the Pharaoh is merged; check its final report and the decoration rows 4017-4022:
   4017 `xeen_stonehand` (right, west), 4018 `xeen_stonehand_l` (mirror, east), 4019 `xeen_cube`, 4020 `xeen_scepter`,
   4021 `xeen_cake`, 4022 `xeen_bench`.
3. **D-57** (`devdocs/xeen/mockups/act6_a7_decisions.md`, no Meshy, no MM9; bind when A2 names the descriptors):
   `xcdr_king` Dragon King 11645 on `xeen_cdr1` (black scales, gold edges); Energy Dragon (violet-white, a Xeen copy of
   m492); Power Lich and Skeletal Lich (Xeen copy of the lich body; descriptors now `Xeen Lich D` / `Xeen Lich E`, rows
   11284/11285, renamed by A2 and hot-fixed in actors.yml by xeen-o; keep these names); Ghost Mummy 11273 and Phase Mummy 11274 on
   `xeen_mummy`; Onyx Sentry 11585 and Onyx Warden 11586 on `xeen_m254` (from `xgol_e`); Picard (npc 5704, old scholar)
   and Alister (druid) as recoloured installed MM6-MM8 bodies; FD-04's lizard, FD-02's very good chair and the eggs from
   shipped decorations. DONE: Golem D/E, Mummy D/E, Picard (State). Still to do: Dragon King, Energy Dragon, Lich D/E
   skins, Alister, FD-04's lizard, FD-02's chair, the eggs. Started at the stop: mask previews of `xeen_mummy`, `mm6_lch`, `mm8_m492`, `xeen_cle` in
   `xeen_tiers_claude/work_s7/` (mummy.png, lch.png, m492.png, cle.png); descriptors exist: `Xeen Mummy D/E`,
   `Xeen Golem D/E`, `Xeen Lich D/E` (11284/85, on `mm6_lch` `lch_c` by A2's hotfix), `Xeen Dragon King`,
   `Xeen Energy Dragon` (11653), `Xeen Picard the Aged` (11922), `Xeen Alister` (11923). Plan: `xcdr_king` in
   `spec_xeens_pet.json`; mummy_d/e on `xeen_mummy`; xgol_k/l from `xgol_e` on `xeen_m254` (body channel); Xeen copies
   `xeen_lch` (xlch_d/e) and `xeen_m492` (violet-white); Picard `xsor_g` (scholar's grey-brown robe, white hair channel);
   Alister `xcle_h` (druid green) on `xeen_cle`.
4. **D-58** (`devdocs/xeen/briefs/d7/L1/D58_DECISION.md`, RELAYS -> S): D7: four element-tinted barges, the celestial
   boat, Megadragon 11654 bound on the MM8 dragon (scaled, no Meshy), the Sky Bandit skin on the thief body; the
   planes: the sleeper on a built Ancient-steel couch with four element skins (a shipped giant/titan lying down; Meshy
   <= 30 only if no shipped body reads), four stone statues from the elemental models, the pedestal and dais (P5's disc
   in each element's stone), the way-up effects, the per-plane devices (font, singing stones, geode, tide pool, bell,
   wreck), element tier skins for A2's nine new rows, the octopods' swimmer binding check on P4; shared with P5: the
   Rest Stop hut and the blank boards. Give the lanes names early (rows and descriptors) before building.
5. **D-61** (`devdocs/xeen/mockups/act5_a8_decisions.md`, RELAYS -> S; A2 names descriptors): DD-15: the Pharaoh is the
   P5 figure (`Xeen Dragon Pharaoh` 11919 already bound; idle, no attacks), mummy tier D (`mummy_d` exists); DD-17:
   Sheltem 11924's look on an existing caster body (no MM9; Meshy <= 30 only if no shipped body reads), one
   propaganda statue from a shipped statue decoration tinted teal metal, the robot/elemental/eye bindings, D6's ruined
   gatehouse; DD-08: `mm6_kni` black and red tiers, 11925 Voweless Knight on the Slayer look, thrones from shipped
   decorations.
6. **D-62** (no Meshy; A2 names descriptors): Cinder Roach 11363 as an ash recolour of `mantis_lava` on `xeen_mantis`
   and its binding; risen Sandro 11926 on 11283's look; Bosco's Guard 11054 recolour on `xeen_dwa1`; four Peasant Dwarf
   bindings on the shipped MM7 bodies (two male `mm7_m302`, two female `mm7_m312`); Sandro's heart jar as a shipped jar
   or urn decoration with a green light.
7. Optional (D-50): a high-striker pole and a doll shelf for X9 (A5); Q-F1's items when it has a brief.
8. Optional phase-7 polish (D-32): a Darkside image-50 sorceress model.
Meshy lane total: 330 (session 7: armadillo 10 more (20 in all), guard 15, octopod 15).

- 2026-11-20 session 6 (`xeen-s6`): sand worm built by a sub-agent, installed, bound (A/C), seen in XD-21 (15 cr);
  XD-16's demon and devil idols (D-40) built as world decorations 4008/4009 (sub-agent, no Meshy), seen at X7's cave
  mouth; D-44: the Xeen mummies moved off `worlds/mm9/` onto the copy `xeen_mummy.glb` (rule recorded in State);
  armadillo started (masters, Smart Topology v2, clean, rig, UVs laid; nothing installed) and stopped at a safe
  milestone for the handover. Meshy spent this session 25 (worm 15, armadillo 10; total 290).

- 2026-11-21 session 7 (`xeen-s7`): armadillo finished, bound (Sand Worm B), seen in XD-21 and X6 (10 cr more, 20 in all);
  Xeen's Guard built, bound (Construct D), seen in XD-21 (15 cr); Sphinxes (north, buried south) built as world
  decorations 4010/4011, seen on X6 from an overlay (0 cr); D-47 Lord Xeen `xdem_lx`, Xeen's Pet `xcdr_pet`, Corak
  `xsor_f`, Elementals E/F/G, People Giant D/E/F; D-49 People skins `xgia_d/e/f`, Barbarian D/E `xarc_d/e`, tethered
  griffin, genie lamp decoration 4013; D-50 Slick `xmer_s`, Lacey, Stumpy; D-52 Ambrose `xkni_h`, Kalindra `sorc_k`,
  Octopod D stand-in; A8's Pegasus decoration 4012. 310 descriptors on 82 models, 0 refused. Octopod built, bound (A-D), seen on D4 and in DD-14 (15 cr); D-56 Roland `xkni_r` and wedding Kalindra `sorc_w`
  bound (313 descriptors, 0 refused). Boulder / cage bird / waterfall and the P5 set (Pharaoh, hands, Cube/Scepter,
  cake, bench) still running in two sub-agents at the stop. Meshy this session 40 (total 330).


- 2026-11-21 session 8 (`xeen-s8`, 06:15): read the lane rules, S.md, STATUS, D-56/D-58. P5 checked complete on S's
  side (Pharaoh bound, decorations 4017-4022 bound and installed; `build-xeen` validate: 333 descriptors on 83 models,
  0 refused); stopped at priority boundary 1 to unblock A5. Found the session-7 decorations sub-agent dead: waterfall
  built but not installed, boulder and cage bird not started (Next 1). No Meshy (total 330).
- 2026-11-21 session 8 resumed: priority 2. Sleepers (4) and statues, pedestals, daises, bell (13) by two sub-agents,
  ways up (3) by the lane; all installed and bound (rows 4023-4042); P4 octopods checked: deep variant without foam
  installed, needs A2's row. 0 Meshy (total 330).

- 2026-11-21 session 9 (`xeen-s9`, 07:25):
  - D-66 thrones (4043-4045) and the teal statue (4046) built from shipped models, installed, bound and seen in
    DD-08/DD-17; interim report sent.
  - Octopod E bound.
  - The waterfall rebuilt as a cascade fitted to XD-17's real slope, installed and bound (4016).
  - Dark-knight black and red tiers; heart jar (4047); dragon egg (4048); P1/P3 way-up columns toned.
  - Validate 334 / 83, 0 refused. 0 Meshy (total 330).

- 2026-11-21 session 10 (`xeen-s10`, 08:20):
  - FD-04's lizard (4049) and FD-02's lectern (4050) built, installed and bound; both seen as spawns.
  - Built by sub-agents, installed and bound: the cage bird (4015, animated) and the Enchanted Boulder (4014).
  - XD-17's waterfall placed look fixed: COLOR_0 fades moved into the textures, the stream above the notch, the
    strands into the pool. Seen placed.
  - P1's heat column grey edge fixed and seen at A6's poses.
  - D-69 answered: no shipped pyramid.
  - Sheltem in DD-17 traced to A8's tour (no Soul Box), not a model fault.
  - D7's sky-barges (4051–4054) and celestial boat (4055) built by a sub-agent, installed and bound, seen as spawns.
  - Validate 334 / 83, 0 refused. 0 Meshy (total 330).

- 2026-11-21 session 11 (`xeen-s11`, 09:10):
  - Alister bound (`xeen_cle` skin `xcle_h`, druid) and seen in FD-04; scan: no other Xeen row or placed actor lacks
    a body.
  - XD-17's waterfall lip softened (clear stream layer, glassy brink, white breaking out below it, no ears);
    reinstalled under the same name, height 2,229.46; seen placed.
  - P1's Ember Font and camp, P2's basket built by a sub-agent (rows 4056-4058), installed, bound, seen as spawns.
  - Validate 335 / 83, 0 refused. 0 Meshy (total 330).

- 2026-11-21 session 12 (`xeen-s12`, 15:35):
  - Audit of every Xeen tier's name against its look (S.md "Session 12: names and looks"): 27 fixed, about 40 right,
    liches D/E left.
  - Dragons (Cloudside on `xeen_cdr1`, Darkside on the new `xeen_m492`, undead on `xeen_m616`), elementals, Ice
    Troll, Shadow Ninja, swamp things, Hell Hornet recoloured on Xeen tier copies; Devil and Venomous Hydra rebound.
    Two lane sub-agents.
  - Seen in XD-11's hall; validate 335 / 83, 0 refused. 0 Meshy (total 330).

- 2026-11-21 session 13 (`xeen-s13`, 16:45): the G3 review's S follow-ups.
  - The Hell Hornet is lighter, with glowing ember wings.
  - The Guardian of Air has stronger gold (the emission try was dropped).
  - Power and Skeletal Lich got their own skins on the new `xeen_lch` (D/E rebound).
  - All seen in daylight (XD-11) and dim (XD-21); validate 335 / 84, 0 refused.
  - Hornet emission masks: the wing channel (B) of each LOD's region mask x the base luminance (normalised to the
    90th percentile, ^0.7), max'd with 0.35 x channel R. Lich D's glow mask: channel R.
  - The heart jar and the balloon basket were rebuilt by a sub-agent and left uninstalled at the usage-limit stop.
  - 0 Meshy (total 330).

- 2026-11-21 F9 feedback agent (for S): `Xeen Sablewing` (11927) bound on `xeen_cdr1` skin `cdr1_c` (MM6's gold
  dragon: his portrait npc14720 is a gold-bronze dragon), scale 160.5 (about 245 tall, his descriptor; the cloud
  dragons stand 352), Xeen's Pet's clips and sockets (anchors), no death effect (he cannot die). 0 Meshy. A bronze
  skin of his own is optional polish. F4: `tools/xeen/check_actor_heights.py` lists every ranged model row with its
  drawn top (GLB bind pose x scale x scale_reference) against its launch point; a new socketless ranged binding must
  pass it (or get a `release` socket).

- 2026-11-22 session 15 (`openyamm-65`'s S agent, D91 §1): the seasons' old men.
  - New `characters:` row 11928 `Elder Druid` (acting for A2) for the Winter Druid (npc 4529, X5) and the Spring
    Druid (npc 4048, X1), whose portraits are old bearded men. Bound `Xeen Elder Druid` on `xeen_sor1` new skin
    `xsor_i` (moss-green robe `#46583a`, bark-brown trims `#6a4e30`, white hair and beard; spec_wizards.json,
    body_wizards.json, body_wizards_hair.json), as Picard's binding (staff, scale 106.121). Other wizard skins
    unchanged (`xeen_tiers_claude/work_s15/sor_i.png`). Reinstalled `xeen_sor1.glb` (winding 0).
  - `key_npcs.py` `BODY_EXPECTATIONS`: 4529 and 4048 on `Xeen Elder Druid`. They are errors until A6 (X5) and A5 (X1)
    put the figures on 11928 (logged in A5.md and A6.md). D91's 4321 and 4601 (Druidess A) were not added here.
  - Validate 337 / 84, 0 refused; `check_actor_heights.py` 11928 ok (socket). Seen in XD-21 beside Picard
    (`output/xeen_fb/s15/shots/druid.png`). 0 Meshy (total 330).

- 2026-11-22 session 16 (`openyamm-65`'s S agent, D91 §1, orchestrator's decision): the seasons' women.
  - New `characters:` row 11929 `Druidess` (acting for A2; friendly, `move: stand`, NoArena) for the Autumn Druid
    (npc 4321, X4) and the Summer Druid (npc 4601, X6), so row 517 stays hostile and X4/X6 need no map-wide relation.
    Bound `Xeen Druidess` on row 517's body (`mm6_dru1` skin `dru1_a`, Druidess A's binding). `build_world.py --check`
    after `--only gen_monsters`: only `trainer_places.txt` differs (not S's).
  - `key_npcs.py` `BODY_EXPECTATIONS`: 4321 and 4601 on `Xeen Druidess`; errors until A5 swaps them at X4/X6's next
    rebuild (logged in A5.md).
  - Validate 338 / 85, 0 refused; `check_actor_heights.py` 11929 ok (socket). 0 Meshy (total 330).
