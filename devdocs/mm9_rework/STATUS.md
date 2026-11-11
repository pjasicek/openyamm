# MM9 rework: status and queue

Working list for the rework, kept here so it survives restarts. Decisions are in [PLAN.md](PLAN.md). Last updated
2026-10-30, after the 12:31 restart.

## Creatures
Review page: `level_generation/creatures/claude_shared/mm9_overview/index.html` (http://127.0.0.1:8912/..., restart
with `python3 level_generation/creatures/claude_shared/serve_review.py 8912` from the repo root: it sends no-cache headers, so a reinstalled model never shows an older revision).

- Approved (19, all built monsters and villagers): Dragonfly, Lobber + Pod, Bird, Yrsa, Annud, Forad, Flying Icky, Winged Mutant, Greater Demon, Eye, Magreeb,
  Basilisk, Terror, Jellyspore, Nagate, Dagrell, Wolf, Dragon King, Sea Monster.
- Texture pass finished on all approved creatures; Eye's pebbled hide being restored; Yrsa's Hit clip floor fix running.
- 12 animals approved ([brief](../../level_generation/creatures/claude_shared/MM9_ANIMAL_BRIEF.md)).
- In progress: first humanoids, Imp, Lich, Skeleton Master, Honk male and female
  ([brief](../../level_generation/creatures/claude_shared/MM9_HUMANOID_BRIEF.md)).
- Overnight monsters run, 2026-10-30/31: 23 of 30 bodies installed, all 23 accepted. Stopped at the weekly limit; [handoff](overnight/MONSTERS_HANDOFF.md).
- Not started: 7 monster bodies (Giant, Yanmir, Lich King, Colloidal Warrior, Lesser Demon, Njam,
  Ebora), 38 town NPC bodies, 16 unique characters, Magic Mine.
- Rules: MM9 skeleton and clips (never Mixamo), sharp textures, acceptance from review-viewer shots.
- **Townsfolk and unique NPCs (2026-11-04, [finishing brief](overnight/FINISH_BRIEF_20261104.md))**: every MM9 actor model
  that had no 3D model is now built, installed and bound (`MM9 <row>` descriptors). Fre, Green Man, Krohn and Skraelos were the
  last four. Approval state per model is on the overview page (`status:'ok'` = user-approved). Lining the see-through gaps: decided 2026-11-05 (below). Open with the user afterwards: the converter switch so the
  maps place the new descriptors instead of the MM6-MM8 stand-ins (regenerates every MM9 map). Meshy backup balance 2210, floor 1740.
- **Triangle reduction of approved models (started 2026-11-04, user request)**: about five at a time, no retexture, faces kept
  exactly; record = "MM9 reduction" table in `level_generation/creatures/REDUCTION_LEDGER.md` (110 files queued, heaviest
  first), brief [REDUCTION_BRIEF_20261104.md](overnight/REDUCTION_BRIEF_20261104.md); standing townsfolk agent brief
  [REDUCTION_AGENT_TOWNSFOLK.md](overnight/REDUCTION_AGENT_TOWNSFOLK.md). Up to eight agents. User rule: "if they look the same
  then it is fine with me" -> the orchestrator installs after its own close-up pre-screen (`install_reduced.sh` enforces UV audit 0
  and winding), then runs the binding regression. The 12 UV-escape rollbacks are done (11 reinstalled, Winged Mutant kept).
- **Reduction handoff (2026-11-05)**: open rows and how to finish: [HANDOFF_REDUCTION_20261105.md](overnight/HANDOFF_REDUCTION_20261105.md).
- **Fre**: approved by the user 2026-11-05 ("fre is very good, accepted", r78): new head (Codex HD references + Meshy head,
  grafted with F2's neck method) after the old F1 face-shell head failed (`mm9_fre_claude/README.md` Pass 6/7). Every MM9 NPC
  on the overview page is now approved. Meshy backup balance 2175.
- **Reduction state (2026-11-05, finished)**: every ledger row is closed: 85 installed, 28 kept (no useful gain), 0 open. Installed rows 969k -> 782k LOD0 triangles (-19.3 %); over all 113 rows 1,196k -> 1,009k (-15.6 %). Last rows: Annud b60, Markel b2, Hanndl d7, Bjarni b60, Forad c60 (b60 rejected at pre-screen for pointed fingertips; c60 keeps them exact, -13.6 %). Binding regression PASS (MM9 252/114, MM6-MM8 647/185).
- **See-through linings (2026-11-05, user: "do what you recommend", then PeasantM1 added)**: post-install lining pass on the installed (reduced) GLBs, brief [LINING_BRIEF_20261105.md](overnight/LINING_BRIEF_20261105.md), projects `level_generation/creatures/mm9_<name>_lining_claude/`. Installed: PeasantM1d (worst 772 -> 19 px, LOD0 6,623 -> 7,974), Sven (2,529 -> 12 px, 8,405 -> 9,860), Tryggva (sleeves 590/502 -> 15 px, torso 406 -> 35 px in Death only; 8,405 -> 10,160; fur capes lined on their own fur UVs after the dark-texel version showed black slabs). Bjarni (torso 2,522 -> 2 px, every zone <= 6 px; 6,841 -> 8,359; yoke lined on its own UVs after the dark-texel version showed a slab). PeasantM1 (torso 263 -> 9 px; 6,236 -> 7,641). **Lining pass finished** (5 bodies); before/after sheets in `output/lining_review_20261105/`. HOM1/HOM2 left as they are (minor holes).

## Maps
- **Painted maps everywhere (2026-11-09)**: all 44 maps draw MM9's painted map on the minimap and journal map (the
  dungeons too, one image per floor by the party's height), at 2× from `realesr-animevideov3`; Settings → Interface →
  Map style chooses between it and the line map where a map has outlines (the dungeons); the line map is the default
  there (2026-11-10). 44 of 44 fit the rebuilt maps
  (`tools/mm9_import_discovery/check_mm9_map_images.py`), ten with measured bounds: DUNGEON_PLAYBOOK.md "Painted maps".
- Dungeons: 25 total. All 92 scenarios of the 24 built dungeons pass (2026-10-31 evening, ledger "2026-10-31
  evening"). Built in the review root: Anskram Keep, Temple of Honk, Lich Lab, Chasm of the Dead
  ([record](../../level_generation/projects/mm9r_chasmofthedead/README.md); its "cut off" audit finding is a false
  positive from narrow floor slots, monsters cross in the game), Beethoven ([record](../../level_generation/projects/mm9r_beethoven/README.md); its two `liquids.yml` entries
  are in the review root only, and the Grand Entrance's wading floor is reverted when diving lands), Drangheim Prison
  ([record](../../level_generation/projects/mm9r_drangheimprison/README.md); of its four audit regions two are false, the
  hatchlings' lane was the stand-in's body and is fixed, the lower levels are joined by ladders only, as in MM9), Klusos House
  ([record](../../level_generation/projects/mm9r_klusoshouse/README.md)) and Ruined Temple
  ([record](../../level_generation/projects/mm9r_ruinedtemple/README.md)) , Verhoffin Ruins
  ([record](../../level_generation/projects/mm9r_verhoffinruins/README.md)), Bathhouse
  ([record](../../level_generation/projects/mm9r_bathhouse/README.md)), Inventa Storca
  ([record](../../level_generation/projects/mm9r_inventastorca/README.md)), Dook's Castle
  ([record](../../level_generation/projects/mm9r_dookscastle/README.md)), Ta'Sar Academy
  ([record](../../level_generation/projects/mm9r_tasaracademy/README.md)), Training Hall
  ([record](../../level_generation/projects/mm9r_traininghall/README.md)), Lindisfarne Monastery
  ([record](../../level_generation/projects/mm9r_lindisfarnemonastery/README.md)), Thjorad Mine
  ([record](../../level_generation/projects/mm9r_thjoradmine/README.md)), Yanmir's Fort
  ([record](../../level_generation/projects/mm9r_yanmirsfort/README.md)), Dark Passageway
  ([record](../../level_generation/projects/mm9r_darkpassageway/README.md)), Connecting Tunnels
  ([record](../../level_generation/projects/mm9r_connectingtunnels/README.md)), The Arena
  ([record](../../level_generation/projects/mm9r_thearena/README.md)), Hall of the Gods
  ([record](../../level_generation/projects/mm9r_hallofthegods/README.md)), Dungeon of Secrets
  ([record](../../level_generation/projects/mm9r_dungeonofsecrets/README.md)), Dragon Stadium
  ([record](../../level_generation/projects/mm9r_dragonstadium/README.md)) and The Thousand Terrors
  ([record](../../level_generation/projects/mm9r_1000terrors/README.md)), overnight run 2026-10-30. Great Gate skipped (an unused cutscene copy; the scene
  lives in Arslegard City). All built dungeons follow MM9's DAT lightmaps since the same night, the older six re-lit;
  the morning report is at the top of the [ledger](overnight/dungeons_ledger.md). 24 of 25 dungeons are built.
- Outdoors: Isle of Ashes pilot built; others not started. User review 2026-11-01 fixed in the review root (castle
  cut-out, trails graded); the tunnel waits for a decision. Recipe: [OUTDOOR_PLAYBOOK.md](../../level_generation/projects/mm9r_common/OUTDOOR_PLAYBOOK.md).
- **Outdoor maps as BLVs, pilot (2026-11-01)**: Isle of Ashes built the cities' way into its own root
  (`output/mm9_rework/isleofashes_blv_root`): 1 sector, 9 994 vertices, 12 389 faces; the tunnel and trails are MM9's;
  cheaper than the ODM pilot on every count (draws 117 vs 131, triangles 30 k vs 73 k, GPU 0.34 vs 0.60 ms, textures
  310 vs 492 MB, load 1.2 vs 1.55 s). Decision with the user. [Record](../../level_generation/projects/mm9r_isleofashes_blv/README.md).
  2026-11-02: shared converter `mm9r_common/outdoor_blv.py`; engine fixes for terrain as BLV floors (head bob, seams,
  cliffs: devdocs/INDOOR_OPEN_SKY.md "Party movement"; footsteps); Sturmford built (27 k faces, one sector) with 200
  monsters: floor queries and collision sweeps now use the sector face grid (BLV_GEOMETRY_COSTS.md), frame CPU 0.46 ms
  against Ravenshore's 0.73. [Record](../../level_generation/projects/mm9r_sturmford_blv/README.md).
- **Monster barriers and the rail check (2026-11-02)**: MM9's AIBarrier brushes are monster-only walls in every
  converted map (scene `actor_barriers`, also walls of the monsters' path map; devdocs/INDOOR_OPEN_SKY.md "Monster
  barriers"); rebuilt with them: the Isle of Ashes, 1000 Terrors, Beethoven, Klusos House, Ruined Temple, Training
  Hall, Verhoffin Ruins, Yanmir's Fort and the seven cities. Drangheim Prison, Lich Lab and the Chasm of the Dead do
  not rebuild at all since the t-junction repair (2026-11-01: over the 7 000-outline limit, with or without
  barriers): their installed builds are older and have no barriers. `mm9r_common/rail_check.py` checks a map's
  monster path map against MM9's AI rails (DUNGEON_PLAYBOOK "Monster barriers and the rail check").
- **Cities as BLV + sky: Sturmford City pilot built (2026-10-31 night, openyamm-06)**: a city works as a BLV (63 sectors, 21 148 vertices, painted minimap, our Enhanced sky with time of day behind the sky faces, shops by RUDE dialogue, all scenarios pass; draw calls 218 against the old ODM's 1 347). [Record](../../level_generation/projects/mm9r_sturmfordcity/README.md), recipe for the other six: [CITY_PLAYBOOK.md](../../level_generation/projects/mm9r_common/CITY_PLAYBOOK.md), ledger "Sturmford City pilot".
- **Thjorgard City built as BLV + sky (2026-10-31, wave 1)**: 89 sectors, 37 979 vertices (58 % of 16-bit), 60 townsfolk, 730 decorations, all scenarios pass; draw calls 218 against the old ODM's 1 458, map load 1.69 s against 3.46 s. [Record](../../level_generation/projects/mm9r_thjorgardcity/README.md), ledger "Thjorgard City".
- **Thronheim City built as BLV + sky (2026-10-31, wave 1)**: 63 sectors, 31 192 vertices (48 % of 16-bit), 43 people (40 RUDE dialogues), 307 decorations, the war council, Kira, the Honks and the Desert Terror's breakout as native Lua, all four scenarios pass; draw calls 206 against the old ODM's 1 069. [Record](../../level_generation/projects/mm9r_thronheimcity/README.md), ledger "Thronheim City".
- **Arslegard City built as BLV + sky (2026-10-31, wave 2)**: 63 sectors, 16 017 vertices (24 % of 16-bit, frame shifted 20 000 along y to fit int16), 36 people + Njam, 419 decorations, the Great Gate scene (FateMan/WritMan), Njam's chase and Sven as native Lua, all three scenarios pass; draw calls 212 against the old ODM's 737, map load 1.56 s against 5.03 s. [Record](../../level_generation/projects/mm9r_arslegardcity/README.md), ledger "Arslegard City".
- **Drangheim City built as BLV + sky (2026-10-31/11-01, wave 1)**: 37 sectors, 16 202 vertices (25 % of 16-bit), 39 townsfolk with RUDE dialogues, 201 decorations, all scenarios pass; draw calls 264 against the old ODM's 644, map load 2.37 s against 3.05 s; open: the leaning ladder to the north wall's walkway. [Record](../../level_generation/projects/mm9r_drangheimcity/README.md), ledger "Drangheim City".
- **Frosgard City built as BLV + sky (2026-10-31, wave 2)**: 12 sectors (an open snow-field town: one open-air sector, 11 interiors), 15 352 vertices (23 % of 16-bit), 50 people, 177 decorations, the ice quest and the battle as native Lua, all scenarios pass; draw calls 157 against the old ODM's 591. Boat routes into its docks rewritten to the BLV. [Record](../../level_generation/projects/mm9r_frosgardcity/README.md), ledger "Frosgard City".
- **Guberland City built as BLV + sky (2026-10-31, wave 2)**: 49 sectors (four walled quarters and the central cross, 23 walk-in interiors), 19 823 vertices (30 % of 16-bit), 46 people with RUDE dialogues, 258 decorations, the eight quarter gates opening as the party walks up, Markel, the bank orb and the apothecary's potion as native Lua, all three scenarios pass; draw calls 162 against the old ODM's 816, map load 1.27 s against 1.87 s. [Record](../../level_generation/projects/mm9r_guberlandcity/README.md), ledger "Guberland City".
- **Monster AI (2026-11-05)**: implemented (all plan phases, recovery, spell mapping, animation, perception,
  repositioning casters); current state, open questions and next work in the
  [handoff](HANDOFF_MONSTER_AI.md); design [MM9_MONSTER_AI.md](MM9_MONSTER_AI.md), plan
  [MM9_MONSTER_AI_PLAN.md](MM9_MONSTER_AI_PLAN.md), research in `monster_ai/`.
- **Talk conversation bar (2026-11-04, user chose A)**: MM9 talk is the Carved Obsidian bar, the speaker's live 3D head in its ring (talk camera removed 2026-11-06); since 2026-11-06 the party basebar is hidden in a talk (the bar stands at the bottom edge), trainers list a lesson row per member, and the bar's text is rasterized at its drawn size; Obsidian breath meter and the water surface from below done the same day. [Talk record](../../level_generation/ui/mm9_talk_dialogue_study_20261102/README.md#native-implementation-2026-11-04), water in `MM9_WATER_SWIMMING_DESIGN.md` Status.
- **Swimming and diving (user, 2026-10-31):** Rizin RE of MM9's water (volumes, swim controller and speeds, breath, underwater view, swimmer monsters) and an integration design for our engine, Verhoffin Ruins as the first test case: `MM9_WATER_SWIMMING_RE.md`, `MM9_WATER_SWIMMING_DESIGN.md` (in progress). Implementation waits for the user's review of the design (shared engine feature).
- **All seven MM9 cities are BLV + sky (done 2026-11-01, openyamm-06)**: daylight by time of day, MM9 fog, leaning ladders; every city and dungeon scenario passes. Report and the four open decisions: [ledger, top](overnight/dungeons_ledger.md); brief [CITIES_ROLLOUT.md](CITIES_ROLLOUT.md).
- **City street performance (2026-11-01, stopped mid-way on quota)**: merged roof-line portals (6 of 7 cities rebuilt, unverified) and indoor batch merging (unfinished, built into the current binary, unverified): [HANDOFF_20261101_CITY_PERF.md](HANDOFF_20261101_CITY_PERF.md).

## Open with the user (2026-10-30 evening)
Recommended yes on all four, no answer yet: fix the gold-subtraction portrait effect and the two undefined MM9 event calls
(`routine_followplayer`, `evt.UseMm9Barrel`); friendly spawn-point actors follow the same rule as placed ones; a small save
migration for the old `hostility_type` byte; retire the 11 old dialogue scenarios. Everything else is in [ROADMAP.md](ROADMAP.md);
overnight state is in `overnight/`.

## Engine
- Done: door lighting in the bake, sky/window emitters, translucent BLV faces, rotating movers and ladders
  ([doc](../INDOOR_ROTATING_MOVERS_AND_LADDERS.md); Anskram Keep's doors, levers, traps, pits, ladders and hatches).
  Temple of Honk and the Lich Lab now swing their doors too. Indoor fog ([doc](../INDOOR_FOG.md)), `DirLight`s in the
  bake and the `max_lighting` ceiling are in. The Lich Lab's "white mist" was our own view fade in the reference shots,
  never MM9: capture references with `--set video.view_distance=unlimited`.
- Waiting for the user: timing comparisons in a single session (`output/mm9_rework/movers_baseline/`,
  `output/mm9_rework/fog_baseline/`).
- **User decision 2026-10-31: replacing the dungeons' bakes with MM9's own lightmaps (transfer) is deferred to the end of the MM9 integration**; findings and the plan are in [MM9 lighting decision](MM9_LIGHTING_DECISION.md). Until then there are no re-bakes: a map whose bake goes stale has it removed and uses the classic MM6–MM8 lighting.
- **User decision 2026-10-30 22:30: dungeon lighting follows MM9's original DAT lightmaps** (brightness and hue, dark rooms
  stay dark so Torch Light matters). The old-import capture is not a brightness reference: a real MM9 screenshot of
  Verhoffin Ruins' spawn measures luma 62 against the capture's 94 and a lightmap-matched bake's 56
  (`overnight/mm9_real_vs_ours_verhoffinruins_spawn.jpg`). Maps calibrated to the capture are being recomposed.
- Light hue (`mm9r_common/hue_vs_lightmaps.py`, 2026-10-30): Chasm's and Beethoven's bakes are less coloured than MM9's
  own lightmaps in the tombs and catacombs, and match in the canyon and upper sewers. Do not desaturate them. Ours has a
  floor about 5x MM9's, which flattens the ratios; open: whether shaders treat MM9's bytes and our linear values alike.
- Lighting still unmatched: Lich Lab kitchen (-16), pods (-9), teal on the hall grates and crown frame; Anskram Keep
  stone greyer than MM9 at the entrance (red/blue 1.41 against 1.63), store rooms 0.6, rooms 26, 27, 29, 30 about 1.5.

## Queue, in order
1. Done: indoor fog, `DirLight`s, the engine crown, Anskram Keep on the shared converter.
2. The converter-only list in [MM9 visual properties](MM9_VISUAL_PROPERTIES.md) across the dungeon and outdoor
   converters.
3. Then engine gaps 2-5 from that document: animated creature skins, skin swaps at run time, pulsing indoor lights.
   Outdoor translucent BModels with them.
4. After the running creature agents finish: move shared three.js to `claude_shared/vendor/` and repoint every viewer
   (user approved).
5. Later: monsters opening doors; the Dragon King's grounded boss script (MM9 has no ground walk, so it stands in place);
   the swimming and diving engine feature (design proposal first; the Sea Monster and fish rebind then).
6. Last: x4 surface textures are done (2026-11-02: all 1 002 in-scope textures of the dungeons, cities and outdoor
   regions accepted and installed; 44 out of scope); left is a Codex x4 pass over the MM9 prop skins (a separate batch:
   the x4 playbook excludes decorations today). The outdoor BLVs' ground faces draw blended terrain materials instead
   of their textures (devdocs/INDOOR_OPEN_SKY.md "Terrain"). Prop skins are plain Lanczos x4 until then, no Real-ESRGAN (user, 2026-10-30).

## Decided, in progress or queued (2026-10-30)
- Regression diagnosis of the 13 failures: running, report in `devdocs/REGRESSION_DIAGNOSIS_20261030.md`, no fixes yet.
- Yrsa's clip jitter (smooth correction) and the Winged Mutant's membrane tint: running.
- Humanoid monster batch: started with Imp, Lich, Skeleton Master and Honk (about 850 credits for all 33 bodies). Next
  after review: Banshee, Ghost and the rest.
- User-approved fixes running: the 13 regression failures, headless runs saving settings, `start_world` back to mm8.
