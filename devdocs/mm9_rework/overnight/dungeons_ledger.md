# Overnight MM9 dungeons: ledger

Orchestrator: Claude session `openyamm-05`, started 2026-10-30 17:09. Brief: [OVERNIGHT_DUNGEONS.md](../OVERNIGHT_DUNGEONS.md).
Agent brief (given to every map agent): [AGENT_BRIEF.md](AGENT_BRIEF.md). Each agent keeps
`status/<map>.md`; this ledger aggregates them.

## Report for your return: the seven MM9 cities as BLVs (2026-11-01, openyamm-06)

**All seven cities are native BLV maps open to the sky**, installed in the review root `output/mm9_rework/assets_dev`
(Sturmford, Thjorgard, Thronheim, Drangheim, Arslegard, Frosgard, Guberland City). Each has its own sectors and portals
(walk-in houses and shops behind door and window portals, streets split by street cuts under a roof line), our Enhanced
sky with time of day behind MM9's sky faces, MM9's painted city map as the minimap, RUDE townsfolk and walk-in shops,
its scripts as native Lua, transitions both ways, and review sheets against the old ODM import that I looked at (no
holes). Recipe: `level_generation/projects/mm9r_common/CITY_PLAYBOOK.md`; brief: `devdocs/mm9_rework/CITIES_ROLLOUT.md`;
each city's record: `level_generation/projects/mm9r_<city>/README.md` and its section below.

| City | Vertices (of 65 535) | Sectors | Portal faces | Draw calls, median: BLV / old ODM | Map load: BLV / old ODM |
| --- | --: | --: | --: | --: | --: |
| Sturmford | 20 965 (32 %) | 63 | 215 (343) | 218 / 1 347 | 1.46 / 2.73 s |
| Thjorgard | 34 479 (53 %) | 89 | 237 (1 470) | 218 / 1 458 | 1.69 / 3.46 s |
| Thronheim | 29 553 (45 %) | 63 | 299 (974) | 206 / 1 069 | 2.43 / 2.93 s |
| Drangheim | 14 840 (23 %) | 37 | 206 (744) | 264 / 644 | 2.37 / 3.05 s |
| Arslegard | 16 261 (25 %) | 63 | 213 (224) | 212 / 737 | 1.56 / 5.03 s |
| Frosgard | 15 352 (23 %) | 12 | 12 | 157 / 591 | 3.97 / 5.59 s (noisy) |
| Guberland | 19 019 (29 %) | 49 | 271 (631) | 162 / 816 | 1.27 / 1.87 s |

Vertices and portal faces are after the merged roof-line portals and the merged face draws (2026-11-01 evening,
below; in brackets the portal faces before); the draw-call and load columns are from before them. No city needed
wider vertex indices. Frosgard is one open snow field with free-standing houses (one open-air sector;
the gain is the interiors) and was clipped to a sealed box round town and harbour (MM9's sky shell runs past the BLV's
16-bit coordinates; MM9 itself draws only 2 500 LT far). Frame rate still needs a single-session run on your side.

**Checks at the end:** every city scenario passes (doors and exits, shops by real clicks, chests where MM9 has them,
scripted objects, ladders), all 92 dungeon scenarios pass after the night's engine changes, `openyamm_unit_tests`
2444/2444, `openyamm_runtime_tests` 54/55 (the old New Sorpigal braziers case), `indoor` suite 174/174. MM6 6d02, MM7
7d06, MM8 d06, MM8 out01 and two MM9 dungeons render as before (old vs new binary, only moving things differ).

**Engine changes tonight (all opt-in per map; MM6-MM8 unchanged):**
1. Open sky behind sky faces (`sky` scene block): `devdocs/INDOOR_OPEN_SKY.md`.
2. Daylight for open-air sectors by time of day (`daylight` block): MM9's ambient plus its fixed StaticSunLight; houses
   unchanged; dark at night. MM9's own LightScale/NightLightScale have no visible effect in MM9 (Rizin).
3. MM9 fog model (`fog: {model: lithtech, night: ..., sky: ..., follow_daylight: true}`): MM9's two-pass fog, its
   black night fog, the fogged sky where MM9 greys it (Frosgard), fog colour following the night: `devdocs/INDOOR_FOG.md`.
4. Leaning ladders (a ladder whose top is offset is climbed along its line) and `grab_at_top` (enter a ladder from
   its top): Drangheim's walkway ladder. Only one of MM9's 68 ladders leans.
5. Screenshot tours hold the indoor game clock (tours on city BLVs had killed the party through the "days without
   rest" rule, as a tour's clock jumps added whole days; a player can't hit it).
6. Build fixes: `mm9_compile_indoor_source` and `openyamm-editor` lacked `IndoorSectorFaceGrid.cpp` since the
   line-of-sight change (both link again).

**Converter (all opt-in, Lich Lab output identical):** the `city/` module (street cuts, roof line, top portals,
`street_box_lt`, half steps), painted minimap without outlines, `bright_scale_lights` (MM9's BrightScale, which only
MM9's lightmap baker applies; it fixed Sturmford's glaring facades), `fog: lithtech`, `sky_fog`, `daylight`.

**Decisions for you:**
1. **Arslegard as a living party.** In MM9 you first arrive by dying; a party walking in without key 98 is sent to the
   Dark Passageway about 27 s later by the first-arrival scene, as in MM9. Keep, or let a living party visit freely?
2. **BrightScale in 12 dungeons** (Anskram, Inventa Storca, Verhoffin, Drangheim Prison, Lindisfarne, Chasm, Klusos,
   Lich Lab, Arena, Dook's, Temple of Honk, Hall of the Gods): their lights are written at full strength; MM9's
   BrightScale would dim 1 342 of 1 377 to 0.3-0.75. Not applied, because lighting is deferred to the end and Klusos
   House's real screenshots matched full-strength lights. Table: CITY_PLAYBOOK "Street lights and BrightScale".
3. **Grey sky by day in Thjorgard and Drangheim**: by MM9's data their sky is fogged grey in daylight too (as
   Frosgard's now is). Left clear, as accepted on the sheets; one override each if you want MM9's look.
4. **Swimming** still waits for your six decisions (`devdocs/mm9_rework/MM9_WATER_SWIMMING_DESIGN.md`); until then
   Frosgard's bay and Sturmford's well are wadeable surfaces.

**Not built (specified in CITY_PLAYBOOK):** weather only in open-sky sectors, outdoor-only spells asking "open to the
sky", sun shadows (a wall facing the sun is lit even where a house would shade it).

**Open items, smaller:** townsfolk draw as stand-in peasants until the MM9 town NPC models exist; MM9's breakable
windows, Perception hints, NPC schedules and cutscenes are not carried; Guberland's 89 painted facade windows draw black
and its south-square tower tops show sky (MM9's sky faces stand in front of them); in Arslegard two outdoor portals reach
41-82 units into the south tower (a start placed on its upper floor drops to the porch); one Drangheim wall at the west
gate stays bright at night; MM9's world fog is by eye distance, ours by view depth (tiny difference at screen edges).

## Morning report (2026-10-31)

Overnight run of `OVERNIGHT_DUNGEONS.md`: paused 18:30-21:52 on request, then ran to the end. **18 of the 19 queued
dungeons are built** as native BLVs in the review root `output/mm9_rework/assets_dev`, with scene, Lua, line minimap and
a current bake; **greatgate was skipped** (not a dungeon). Every map's scenarios pass with real clicks, and the
orchestrator read each map's compare sheet; five maps were sent back once after that review (bathhouse, inventastorca,
verhoffinruins, darkpassageway, dragonstadium: water, black corridors, wall darkness, brightness). The six maps from
before tonight were re-lit to the same standard (Temple of Honk, Anskram Keep, Drangheim Prison, Chasm of the Dead, Lich Lab and Beethoven; Klusos House to your real shots). Run ended 05:21.
`tools/lighting/stale_bakes.py --check` lists no MM9 map (its 20 entries are MM6-MM8 outdoor bakes, not from tonight).

### Play a map
```
SDL_AUDIODRIVER=dummy ./tools/run_game.sh --isolated <name> --visible --world mm9 --map <map>.blv \
    --assets "$PWD/output/mm9_rework/assets_dev" --seconds 3600
```
with `<map>` one of: verhoffinruins, bathhouse, ruinedtemple, klusoshouse, inventastorca, dookscastle, traininghall,
tasaracademy, lindisfarnemonastery, thjoradmine, yanmirsfort, darkpassageway, 1000terrors, connectingtunnels,
dungeonofsecrets, hallofthegods, thearena, dragonstadium (and the earlier anskramkeep, templeofhonk, lichlab,
beethoven, chasmofthedead, drangheimprison). Each map's README (`level_generation/projects/mm9r_<map>/README.md`) lists
its quests, deviations and what was not checked; its entry under "Finished maps" below has the numbers.

### Lighting: what was decided (please confirm)
- **Walls follow MM9's own DAT lightmaps (texture x lightmap x1)**, your decision at 22:30; proven from MM9's renderer
  (`devdocs/mm9_rework/MM9_RENDER_LIGHTING_RE.md`: no 2x, no gamma). The old-import "MM9 original" captures are far
  too bright and grey. Your real screenshots: Verhoffin spawn matched (62 vs 57); Klusos House real shots were
  1.2-1.37x the lightmaps, most likely MM9's dynamic fire/candle lights, so Klusos is calibrated to your four shots.
  Real screenshots of more maps would settle each one (`overnight/real_mm9/`).
- **No pitch-black rooms**: MM9 has a party light (`PlayerLightOn`) we lack; dark rooms get a per-room floor so no view
  is under luma ~10-12, reversible per map (`ROOM_LEVELS` etc.). Torch Light still matters.
- **Props**: MM9's model lighting is an opt-in engine mode (`model_lighting`), chosen per map by measuring both paths;
  the old path plus "sector minimum light 31" elsewhere. Props are still the weakest point (Ruined Temple banners darker
  and bluer than MM9's).
- **Re-lit older maps got much darker**: Chasm of the Dead was 2.9-5.4x MM9's lightmaps and is now 0.92-1.13; its entry
  tomb and corridors now read near black (darkest view luma 15, above the floor rule). Beethoven 3.9-5.4x -> 0.82-1.24.
  If they should read lighter, the per-room floor (Dark Passageway's `ROOM_LEVELS`) is a one-line change per map.
- Maps worth a look for colour, all following MM9's lightmaps where the old capture was grey: Yanmir's Fort (deep
  cyan ice light), Dungeon of Secrets (red plate room), Dragon Stadium (near-black open bowl walls).

#- 05:21 pre-overnight re-light done; all agents finished; morning report written. Run ends.

## Engine changes (all built by the orchestrator; unit tests and the `indoor` regression suite run after each)
1. `IndoorLadder::grabInAir`, scene key `grab_in_air` (opt-in): Training Hall's climbing poles.
2. MM9 model lighting, scene block `model_lighting` (opt-in, `devdocs/INDOOR_MODEL_LIGHTING.md`), including
   `lightsIgnoreReach` (MM9 model lights have no occlusion). Off = old path; MM8 d06 pixel-identical apart from its
   animated lantern.
3. `IndoorWorldRuntime::setMapActorPosition`: `evt.SetMapActorPosition` did nothing indoors (no MM6-MM8 script uses it).
Final state: `openyamm_unit_tests` 2396/2396, `indoor` suite 174/174 (the five failures listed on 2026-10-30 no longer
fail), `openyamm_runtime_tests` 54/55. The one failure, `New Sorpigal temple braziers toggle and retain their light
state` (IndoorDecorationInteractionTests.cpp:44), is not from tonight as far as the code shows, but was not compared
with HEAD. `IndoorRenderer.cpp` also carries another session's uncommitted keyboard-picking rework, built along.
4. **2026-10-31, user-approved (A3), changes MM6-MM8 behaviour:** squat walkers (height < 2 x radius) on stairs.
   Planner (`PathMap::traceWalkBody`, new `isClimbedStepFace`): skips faces wholly over the head and the steps being
   climbed; railings, stair sides, low ceilings and lintels still block. Movement (`IndoorMovementController`): for squat
   bodies, the leading floor probe looks 64 ahead (not the radius), a step up from another face of the same tread, and
   faces wholly over the head ignored. Tests: two new cases in `tests/PathMapTests.cpp`. After: unit 2416/2416 (other
   sessions added tests), indoor suite 174/174, runtime 54/55 (same braziers case). MM6-MM8: 8 220 planner routes on
   115 maps, tall control identical; squat bodies 145 routes better, 39 partial routes end farther, none success ->
   fail; 16 headless chases: 12 same, 2 closer, 2 farther (7d26 spider 407 vs 253, mdt10 giant rat +147). Details:
   `devdocs/mm9_rework/SPIRAL_STAIR_PATHING.md` ("A3 done"), `devdocs/ACTOR_PURSUIT_AND_REACH.md`.
5. **2026-10-31 evening: a timer that restarts itself keeps its period** (`game/events/ScriptedEventTimer.*`,
   both scenes' `updateTimers`). `evt.StartTimer` from a timer's own handler used to apply on the next frame and count
   from it, so a 0.25 s self-restarting poll ticked about every 0.3 s headless (0.27-0.28 s at 60 fps). Now
   `updateScriptedEventTimers` takes the scene's queued controls, applies a handler's at once, and counts its restart
   of its own timer from the alarm that ran it (from the clock if that alarm is more than the delay behind: rest).
   Other requests unchanged (applied at the next update, from its clock). MM6-MM8: no MM6-MM8 script calls
   `evt.StartTimer` (an OpenYAMM extension). Tests: two new cases in `tests/ScriptedEventTimerTests.cpp`, the
   StopTimer/StartTimer case in `EventScriptingTests.cpp` on the new path. After: unit 2426/2426, indoor suite 173/174
   (`mm6_ogr_actor_models_bind_all_tiers`, another session's ogre model), runtime 54/55 (the braziers case).

### Shared tool changes (opt-in or default-preserving)
`mm9r_common/dungeon/`: glass portals with more than four corners (thearena), `tables.transitions_text` merges the
review root's current row (1000terrors; fixes two maps overwriting a shared transition row, which broke every game load
for ~5 min twice; side effect: a map's own exit settings are not reapplied once its row is converted),
`map: {model_lighting}` opt-in. `tools/lighting/bake_indoor.py`: `ambient_colour`, `shadowless_faces` (both default off).
Lich Lab `--plan` identical after every converter change. Nothing committed; no git was run.

### MM9 water to the liquid shader (2026-10-31)
The remaining MM9 water surfaces draw with the engine's liquid shader (the user agreed). Shared helper
`level_generation/projects/mm9r_common/liquids.py` (not the converter), called last in each map's `scene` hook:
visible horizontal faces drawn with Water115 (`WATEQOBX0Z`, `WATEZWECUN`), water125's first frame (`WATENZD35K`) or
water123 (`WATE1XKSQP`) take a liquid name of their own (`lqw115mm9`, `lqw125mm9`, `lqw123mm9`) through the scene's
`face_attribute_overrides` (`texture_name`). The review root's liquid table gains `water115_mm9` [22,60,140],
`water125_frame_mm9` [44,92,102] and `water123_mm9` [48,64,104] (all `worlds: [mm9]`, `depth: shallow`, distinct ids,
so Beethoven's, Inventa Storca's and Dook's installers keep them). `worlds/mm9/textures/LQW*.bmp` are byte copies of the
native first frames, for the bake only (the game loads no art for a liquid). Every liquid face leaves
`translucent_faces`, because a translucent entry drew the liquid's flat colour over the shader. Own names, not the
aliases: outdoor MM9 maps use the same textures on non-water faces (Wizard's Lab's puzzle blocks, Boot Camp's orbs,
Arslegard's water-box sides, gate sheets), all Fluid-flagged, so neither a name nor a `fluid` match could tell them
apart.
- Liquid now: Bathhouse 14 (pools, tub, wading floors, drained-room movers), Chasm 2 (+ acid slime no longer
  translucent), Verhoffin 3 (trap water, pit), Temple of Honk 1, Drangheim 1 (sink), Hall of the Gods 2 (pool), Dark
  Passageway 149 lake tiles (+ 91 tube and ocean faces no longer translucent), Yanmir 36 (pool), Dungeon of Secrets 16,
  Training Hall 12 (pole room; + lobby Ocean4 no longer translucent).
- Stay bitmaps: Beethoven's 71 `slime_0000` beds; vertical gate sheets (Yanmir `WavySurface4/5`, Hall of the Gods
  `WorldObject6`); invisible faces (Beethoven's 63 water125_0000 volume faces, Thousand Terrors' 4, Bathhouse's 10).
- Depth: `shallow` everywhere. Indoors `depth` changes no collision (only `wade_speed`); routes and puzzles are the
  geometry's. MM9 swims in Bathhouse (shafts, tunnels, the drained room), Verhoffin (crevasse with a chest on its bed,
  pit), Dark Passageway (lake, tube, ocean), Training Hall (pole room, 104 LT), Dungeon of Secrets (the submerged
  tunnel) and the deeper parts of Yanmir's pool (62 LT). Wading floors, dives and teleports stand in, as before.
  Temple of Honk's pool is 8 LT, and MM9 lets the party wade it; the user chose wadeable and `depth: shallow`.
- No rebuild needed: installed scenes were fixed in place (`liquids.py --scenes ...`), and the hooks redo it on every
  rebuild from the new BLV's face ids (Yanmir's 14:31 rebuild did). Scene edits leave the bakes hash-stale
  (`scene.yml` dependency): bathhouse, chasmofthedead, darkpassageway, drangheimprison, dungeonofsecrets, hallofthegods,
  templeofhonk, traininghall and verhoffinruins until each is re-baked (Yanmir was re-baked at 14:34).
- Sheets (before | after, looked at): `level_generation/projects/mm9r_<map>/review/liquid/before_after_p*.jpg`.

### MM9 see-through water (2026-10-31, user: "if MM9 water was see-through partially, we need to keep this, and lighter blue to fit")
- **Engine (opt-in, indoor):** `liquids.yml` `opacity` (default 1; water/tar faces only, never terrain or lava;
  `game/tables/LiquidTable.*`, `liquidFaceColorAbgr` in the face tint's alpha via `MapAssetLoader`). See-through surfaces
  are kept apart (`WaterGeometry.h`) and drawn by `WaterRenderer::renderIndoor(..., WaterSurfaceSet::SeeThrough)` after
  the creatures and models, before the translucent faces (`IndoorRenderer.cpp`); `fs_indoor_water.sc` blends them
  (body at the opacity, rippled like MM9's caustic sprites and lit at least as much as it is clear; reflection and
  highlights over it whole). The bake export (`IndoorBakeSceneExport.cpp`) gives their faces a translucency of that
  opacity. Outdoor BModel faces stay opaque (an `fs_water.sc` change shifted 3 sea pixels by 1-2 levels, so dropped).
  Docs: `devdocs/INDOOR_TRANSLUCENT_FACES.md` "See-through liquids", `INDOOR_BAKED_LIGHTING.md`, both liquids.yml headers.
- **MM6-MM8 unchanged:** frozen-clock captures (temporary `time_scale 0`, reverted) of sewer.blv, d01.blv (MM7),
  d07.blv (MM8), oute3, 7out01, out01 before/after: byte-identical outside animated creatures and a flickering lamp,
  which also differ between two runs of the unchanged build.
- **Data (`mm9r_common/liquids.py`):** each water face's MM9 surface is found in the DAT (the volume it tops or the brush
  polygon it came from); opacity = SurfaceAlpha (or a Translucent brush's Alpha) x the sprite's mean alpha (Water115
  0.42, water125 0.25; Water115flowing, water123, slime, oceans none); see-through when below 1 and at least half of the
  object's faces have a floor of their room (or a portal neighbour) under them. Names `lq<family>o<percent>`, 13 entries
  (`water115_o12..o70_mm9`, `water125_o17/o20`, `water123_o90`, `slime_o70/o80`, `ocean4_o50`), lighter colours, bake
  bitmaps with opaque alpha. Beethoven's hook now calls the helper too. See-through: Bathhouse 8 (0.21 pools, 0.7
  drained room), Chasm 3 (0.42, 0.29, acid 0.7), Verhoffin 2 (trap 0.37), Temple of Honk 1 (0.37), Drangheim 1
  (0.29), Dark Passageway 149 (lake 0.17), Yanmir 36 (0.29), Dungeon of Secrets 16 (0.12), Training Hall 17 (0.5,
  0.9), Beethoven 78 (slime 0.8, baths 0.17/0.2). Opaque: wading floors over sealed or unbuilt water (Bathhouse,
  Inventa Storca, Dook's Castle, Dark Passageway's tube room and ocean, Verhoffin's pit), Hall of the Gods (no
  Translucent bit in MM9). Installed scenes fixed in place (`liquids.py --scenes ...`); bakes of those scenes are
  hash-stale until re-baked. Sheets: `level_generation/projects/mm9r_<map>/review/liquid/see_through*.jpg`.
- Tests: unit 2426/2426 (new: liquid opacity parsing/default, see-through surface split); runtime 54/55 (the same New
  Sorpigal braziers case); indoor suite 173/174: `mm6_ogr_actor_models_bind_all_tiers` ("Ogre Hit did not blend out
  over 120 ms into Running"), an actor-model case on `mm6_ogr.glb`/`actors.yml`, which another session has uncommitted
  edits to; nothing in it touches liquids.

### MM9 monster bodies (2026-10-31, user: "do what you recommend")
All 158 MM9 rows of `worlds/mm9/data_tables/monster_descriptors.txt` carry MM9's own collision body (model's initial
animation half extents x Scale x 2.56; `devdocs/mm9_rework/MM9_MONSTER_COLLISION_RE.md`, "Applied"): Terrors 64 (was
160-190), Gezzampt Elder 51 (180), Spores 41, Eyes 51, Imps 26; Dragon King 512 x 1700, Sea Monsters 192-230,
Colloidals 134-179. Kept on regeneration by `tools/mm9_import_discovery/mm9_monster_bodies.py` ->
`mm9_monster_body_overrides.tsv` -> the generator's `--body-overrides` hook (tests added). Shared helper
`mm9r_common/dungeon/bodies.py` `placed_body`: a DAT Scale other than 1 **replaces** the row's Scale (converters
multiplied, or ignored it); 13 converters use it (playbook "Package change: MM9's monster bodies"; Lich Lab `--plan`
identical). **Rebuild for the new sizes:** 1000terrors, chasmofthedead, lichlab, beethoven, anskramkeep,
drangheimprison, templeofhonk, inventastorca, thjoradmine, ruinedtemple (rebuilt after 14:37 = the table install; the
converter edits landed 14:35-14:36). The other 14 built dungeons give identical bodies. No new placement problem;
Terrors, Imps, Honks, Nagate Hatchlings and Lich Kings newly fit gaps to the party (Terrors now climb the Thousand
Terrors' spiral stair, headless). Old-importer outdoor maps still carry the stand-in bodies until re-imported.

### Broken or open
- Big monsters do not path down spiral stairs (1000terrors crypts; MM9 uses AI rails). **2026-10-31:** under
  investigation, our navigation against MM9's rails, report in `devdocs/mm9_rework/SPIRAL_STAIR_PATHING.md`: real, but
  map data (8 dropped tread-top triangles, a 3-unit crack) blocks every body; Terrors are wider than the stair's
  doorway and squat bodies plan as a sphere. Recommended: converter data fix (A1). Waiting for the user's decision.
  **Terrors' width fixed 2026-10-31:** MM9's own radius 64 (see "MM9 monster bodies" above); they fit the doorway.
- Thousands of translucent BLV faces make the desktop renderer refuse a map (headless does not show it). **2026-10-31:**
  the converter build warns over 1 500 (worst built map: Training Hall 647); the renderer fix (batching) is deferred.
- ~~`util/map_export.py` reads BLV vertex indices as signed~~ **fixed 2026-10-31** (unsigned; all 161 MM6-MM8 BLV
  exports byte-identical before and after; the Thousand Terrors' masks removed).
- ~~`tables.py` `OLD_SIDECARS` misses old `_authored` scene/Lua files~~ **fixed 2026-10-31** (`OLD_SIDECARS`,
  `OLD_EVENT_SIDECARS`; the outdoor maps' files stay for their converter).
- ~~Transition writer side effect~~ **fixed 2026-10-31**: the other map's end of a shared row comes from the review
  root, this map's own end is rebuilt from the original on every install. Checked on all 24 dungeons: old and new writer
  both reproduce today's table; with each map's own rows damaged, only the new writer repairs them. Hall of the Gods'
  gate wrapper stays (it also deepens the box, which `exits` cannot).
- Six other projects' prop models carry a stray 2 cm ball mesh; claw torches without a flame; ice statues opaque.
  **Fixed 2026-10-31:** the ball was in 26 installed models (each −80 triangles, LODs rebuilt; opt-in
  `SKIP_BONE_SHAPES` in the isle's `blib.py`); Dark Passageway's claw torches are a new lit model `mm9_clawtorchlit`
  (row 2453; four blue flames between the talons; Dungeon of Secrets keeps the unlit `mm9_clawtorch`), map rebuilt and
  re-baked; the ice statues are blended (reads as cut ice, no flicker). Sheets in
  `level_generation/props/mm9_darkpassageway_claude/review/propfix_game/`, looked at by the orchestrator.
  The stale-bake check lists no MM9 map; its 42 MM6-MM8 entries are outdoor maps stale from texture and scene changes
  made elsewhere, none from this work.
- **2026-10-31:** a project hook (`.claude/settings.json`, `.claude/hooks/guard_rm.py`) refuses `rm` with `$`, `*`,
  `?` or backticks, `xargs rm` and pattern `find` deletes.
- Not done anywhere: desktop playthroughs with real input, save/load mid-puzzle, sounds, Android; actors still mostly
  stand-in models.
- Rule slips by agents (own files only, nothing lost): rm with shell variables or wildcards (verhoffinruins,
  traininghall, yanmirsfort); scratch images overwritten (inventastorca).

## PAUSED 2026-10-30 ~18:30 (user request); RESUMED 21:52 by session openyamm-06
Every agent stopped at a safe point, wrote a handoff in `status/<map>.md`, and holds no lock. No bake, build or game
run of this run is in progress. `converter_edit.d` is not held. The `locks/*.lock` files are plain flock files.

**To resume:** the orchestrator re-reads this ledger and resumes each paused agent by its agent ID (SendMessage; IDs in
the queue table). If an agent can no longer be resumed, start a new one with the same prompt (it reads its status file
and carries on). Then re-arm the /loop. Keep at most 5 running.

| Map | State at pause | Next steps (details in `status/<map>.md`) |
| --- | --- | --- |
| klusoshouse | done | none |
| ruinedtemple | done | optional: MM9 sunlight through the skylight in the bake, then rebake, tour, sheets |
| bathhouse | built, 64-sample bake installed and current, 3 scenarios pass | final baked/unbaked tours, `calib.py`, `pages.py`, lighting sheet, `hue_vs_lightmaps.py`, README sections (bake, brightness, hue, checks), DONE |
| verhoffinruins | built, 3 scenarios pass, DD14 "cut off" proven false in game | **installed bake is a stale 16-sample draft**: full bake via `bake_slot.sh`, stale check, final tours + sheets, final audit, README |
| inventastorca | built + rebaked, doors/chests pass, compare sheet read by agent | **scripted scenario fails at step 88** (dying adventurer not dead 15 s after the Lich King turns on him), v05 final tours (re-check the cave shaft that rendered black, fixed), stale check, both READMEs |
| dookscastle | **done** 23:00 | props pipeline (4 copied scripts need small edits, listed), full build, map scripts, scenarios, audit, tours, bake, README |
| 7-19 | not started | |

Rule slips reported by agents: verhoffinruins deleted its own `review/cal` screenshot folder with `rm -rf` through a
shell variable (own files only, nothing else lost). inventastorca overwrote `v01_part0-3.jpg` in the orchestrator's
scratchpad (scratch files only).

## Decisions made by the orchestrator
- **Builds:** map agents never run `cmake`. An agent needing an engine fix edits the source + test and ends with
  `BUILD REQUEST:`; the orchestrator builds under `locks/cmake_build.lock`, runs `openyamm_unit_tests` and the `indoor`
  regression suite (`--user-data` private), and resumes the agent.
- **Converter lock:** `level_generation/projects/mm9r_common/locks/converter_edit.d` (atomic `mkdir`, `owner` file
  names the map). A flock cannot be held across an agent's separate shell calls, so a directory claim is used. The
  holder proves Lich Lab `convert.py --plan --scratch` is unchanged before releasing.
- **User decision (~22:30): keep dungeon lighting in sync with MM9's original lightmaps** (dark where MM9 is dark, so the Torch Light spell matters).
- **Brightness standard (revised ~22:25 after a real MM9 screenshot from the user):** calibrate against the DAT lightmaps (absolute), not the old-import capture. Real MM9 at Verhoffin's spawn: luma 62, RGB (68,63,45); capture 94; lightmap-matched v07 bake 56 (62,56,41); capture-matched v08 89 (97,88,72). The ~22:04 rule (capture mean) was wrong and is withdrawn. Evidence: `mm9_real_verhoffinruins_spawn.png`, `mm9_real_vs_ours_verhoffinruins_spawn.jpg`. **Follow-up:** maps calibrated to the capture (klusoshouse, ruinedtemple, bathhouse, inventastorca, and the six pre-overnight maps) are probably too bright and grey; recompose each against its lightmaps (profile + `--recompose`, cheap).
- **No sound (user, 22:15):** all desktop game runs are prefixed `SDL_AUDIODRIVER=dummy`; added to AGENT_BRIEF.md and sent to every running agent.
- **Status files** instead of agents writing this ledger, to avoid five writers on one file.

## Build log
- 17:09 `openyamm`, `mm9_compile_indoor_source`, `openyamm_indoor_source_tests` built at HEAD `c7b188c89` + working tree.

- 22:54-22:59 `openyamm`, `openyamm_unit_tests`, `mm9_compile_indoor_source` (traininghall grab_in_air); unit 2391/2391, indoor 174/174.

- 23:33-23:37 `openyamm` (+shaders), `openyamm_unit_tests` (engine model lighting); unit 2396/2396, indoor 174/174.

- 00:15-00:20 second engine-model-lighting build (`IndoorLightingFrameInput::lightsIgnoreReach`, set only with scene model_lighting: MM9 model lights have no visibility test; first verification showed Klusos props darker, x0.77 on shot 3, because our lights stop at portals). Unit all pass, model-lighting 5/5; indoor suite running (indoor_0020.txt).

- 00:31 build request from lindisfarnemonastery: `IndoorWorldRuntime::setMapActorPosition` (indoor evt.SetMapActorPosition was a no-op; places via placeMapActorAt, sets home). No MM6-MM8/engine script calls it (grep). Test in IndoorActorFlyingRuntimeTests.cpp. Second engine-model-lighting build's indoor suite (indoor_0020) passed 174/174. Built 00:45: unit 2396/2396; openyamm_runtime_tests 54/55, the new SetMapActorPosition test passes, the one failure is `New Sorpigal temple braziers toggle and retain their light state` (IndoorDecorationInteractionTests.cpp:44, billboard texture/palette lookup), unrelated to this change, not compared against HEAD. Indoor suite rerun (indoor_0050.txt): see build log.

- 00:45 `openyamm`, `openyamm_unit_tests`, `openyamm_runtime_tests` (indoor evt.SetMapActorPosition); unit 2396/2396; runtime 54/55 (New Sorpigal braziers, unrelated); indoor: Regression suite summary: passed=174 failed=0.

## Recalibration queue (lightmap-matched recompose, runs before new maps as slots free)
| Map | State |
| --- | --- |
| klusoshouse | **done** 22:44: calibrated to the user's 4 real MM9 screenshots (direct 0.75, ambient 1.188, max 1.4, sector min light 31): shots x1.02, x1.01, x0.96, x0.89 (Count missing in ours); vs DAT lightmaps x1.19-1.37; lighting views mean 49.2; `review/real_vs_real09.jpg` read by orchestrator, a close match; cabinet04ns turned 90 deg (Drangheim Prison may need the same) |
| ruinedtemple | **done** 04:30 (revisit): model_lighting light_scale 4 (banners 1.08/0.82 of their wall, were 0.35/0.25; crypt lid kept 0.86, which sector-31 dropped to 0.59); teal fixed (torch green 0.5 -> 0.3; G/B matches MM9 in every zone; e04 e05 e07 t02 pure blue); zones 0.86-1.08, elevator 1.22; darkest view 16.6; scenarios pass; `review/v08_compare.jpg` read by orchestrator: blue matches MM9, banners visible but still darker and bluer than MM9's pale white ones |
| beethoven | **done** 23:00: rebaked to DAT lightmaps (direct 0.7, ambient 0.88, max 1, dirlights as spots via map-local bake.py, sector min light 31); zones 0.82-1.24 (before 3.9-5.4); 23-view mean 21.5 (old bake 79, capture 94); south arrival 27 vs real YouTube frame 6.8 (frame location unconfirmed, crushed blacks); `review/lighting_v05_compare.jpg` read by orchestrator; old bake kept in `output/mm9_rework/bakes/beethoven_capture_matched/`; lower sewers' green lights weaker than MM9 |
| templeofhonk, anskramkeep, drangheimprison, chasmofthedead, lichlab | **done** 05:21: recomposed to the DAT lightmaps (TOH 1.69-2.06 -> 0.90-1.07, Anskram 1.11-1.47 -> 0.84-1.11, Drangheim 1.08-1.33 -> 0.96-1.06, Chasm 2.93-5.37 -> 0.92-1.13, Lich Lab 0.96-1.28 -> 0.78-1.09); model_lighting on Drangheim, Chasm, Lich Lab; scenarios pass; overview `status/relight_premaps.md`; orchestrator read Chasm p01 |

## Queue
| # | Map | State | Agent | Notes |
| --- | --- | --- | --- | --- |
| 1 | verhoffinruins | **done** ~22:15 (lightmap bake reinstalled) | ab3253d2bd1632aaf | |
| 2 | bathhouse | **done** ~22:20 | ab5fc1d908009a7a0 | |
| 3 | ruinedtemple | **done** 18:20 | aef351d292f1c8b93 | sheets read by orchestrator |
| 4 | klusoshouse | **done** 18:04 | ac1dc49d889f3440e | sheets read by orchestrator |
| 5 | inventastorca | **done** ~22:29 | a619601c35c2118e4 | |
| 6 | dookscastle | running (resumed 21:52) | a97fd799ddc0dd2d3 | |
| 7 | traininghall | **done** 23:48 | aafe99dae8313d128 | |
| 8 | tasaracademy | **done** 23:23 | afd7c88a7c450a140 | |
| 9 | lindisfarnemonastery | **done** 00:52 | a190571eb8111296c | |
| 10 | thjoradmine | **done** 01:38 | af720acd3d1ed473b | |
| 11 | yanmirsfort | **done** 02:25 | a1231ee50ae461b64 | |
| 12 | darkpassageway | **done** 02:28 | ab350eda7352ad3f9 | |
| 13 | 1000terrors | **done** 04:40 | addb5d723483931ad | |
| 14 | connectingtunnels | **done** 02:54 | a8cb1b64649e2d5f4 | |
| 15 | dungeonofsecrets | **done** 04:09 | a6e7ee4bb81654b8a | |
| 16 | hallofthegods | **done** 04:09 | ab0c9e77cd66b589b | |
| 17 | thearena | **done** 03:45 | a01eca6b8fd8024ce | |
| 18 | dragonstadium | **done** 04:11 | aafde3a1f44d41100 | |
| 19 | greatgate | **skipped** 03:51: not a dungeon | a89457f589f1a1296 | |

## Finished maps
(faces, rooms, movers, monsters, scenarios, brightness, unmatched items, sheet paths, not checked)

### Klusos House (`klusoshouse`), done 18:04
- 1 716 faces, 10 rooms (11 sectors), 13 portal faces, 26 movers (13 rotating double doors), 36 BLV lights + 5 bake-only,
  112 decorations (props project `level_generation/props/mm9_klusoshouse_claude/`, 21 new models, rows 2239-2262,
  19 reused), 1 chest, 20 actors (19 Guard Captains + Count Kluso, MM9 body sizes).
- Scenarios (real clicks): doors_exits PASS (13 door pairs, shut door stops, both exits), chests PASS, scripted PASS
  (letter text 456, Blackheart item 10029 + key 223 / QBit 90223 + alarm, 7 hidden guards appear, sleeper wakes).
- Audit: no unreachable region; 3 step warnings are the stair side drop; 8 actor notes are guards against walls.
- Brightness: 28-view mean MM9 93.0 / ours 96.5 (+4 %); lighting set 93.4 / 93.5. Hue ×0.82-0.90 of MM9's lightmaps
  (upper corridors ×0.74). Over 10 %: brighter l05 l06 l07 l10 l13 l14 u01 u04 u06 u07 u08; darker u03 u11 u12 u13.
  Not in stale bakes.
- Unmatched: KlusosPatrol.scr patrols (no patrol paths; guards stand at posts), GuardTrigger alarm relay (native AI
  chases on sight; aware2.wav not in our audio), PropAnim.scr "ns" (static furniture only).
- Sheets: `level_generation/projects/mm9r_klusoshouse/review/v04_compare.jpg`, `lighting07_compare.jpg`, `flames01/`.
  Orchestrator read both sheets: geometry, props, doors, window and fireplaces match MM9 view for view; baked column
  close to MM9; unbaked darker as expected.
- Not checked: **actors invisible in the review root** (borrowed MM6 guard/nobleman sprites fail "requires cooked
  schema 2"; no MM9 3D models yet); no desktop playthrough; save/reload after the theft; arrival in Drangheim City
  through the exits; Android.
- Converter unchanged (tried an opt-in, reverted, Lich Lab plan byte-identical). Playbook gained "Lessons from Klusos House".

### Ruined Temple (`ruinedtemple`), done 18:20
- 3 724 faces, 9 rooms, 10 portal faces, 54 MM9 mover models in 44 groups (66 mechanisms), 65 BLV lights + 2 bake-only,
  68 decorations (8 new props, rows 2225-2233, 9 reused), 3 chests, 15 actors (14 monsters at MM9 sizes + hidden genie).
- Scenarios (real clicks) all PASS: doors_exits (47 steps), chests, scripted (205 steps: dirt plugs, Tree of Life, lamp,
  genie), party climb shaft -> tunnel, 3 monsters reaching the party in their rooms. Audit findings (1 region, 2 pits,
  1 actor) checked: false or harmless; no monster cut off.
- Brightness: MM9 36.0 / baked 34.3 (-4.7 %), unbaked 55.1; only 12 of 34 views within 10 %. Dark: skylight hall
  e01-e07 (MM9 adds sunlight through the skylight, not carried), s03 s04 s05 t05 n01 n02 n05 c01. Bright: t01 t03,
  crypt c03-d03. Map-local light colours scaled by MM9 per-light strength (converter writes colour only).
- Unmatched: TriggerHostile0, DBEffectsTrigger0-2 dust/earthquake effects; pews' "onside" anim (absent in MM9's model).
  Deviations: debris drops out of sight; dirt plugs break on click not damage; genie talks on click; lift toggles ends;
  Trigger1 enlarged 100 units.
- Sheets: `level_generation/projects/mm9r_ruinedtemple/review/v06_compare.jpg`, `lighting_compare.jpg`, `flames/`.
  Orchestrator read them: geometry, skylight, temple, crypt, cells, doors match view for view. Seen differences:
  the red/white banners draw much darker than MM9's (e03, t01, c03), the chest-room chests nearly black (s05),
  baked column bluer than MM9 in the entrance halls. Follow-up candidates, not blockers.
- Not checked: Perception hints on desktop, genie item/attribute wishes, riding the lift on desktop, walking into the
  crypt hole, walking into TriggerCaveIn1. Three monsters draw as placeholders.

### Verhoffin Ruins (`verhoffinruins`), done 22:11
- 5 954 faces, 29 rooms, 32 portal faces, 76 movers, 85 BLV lights + 11 bake-only + 3 DirLights (bake), 94 decorations
  (20 new props: rows 2216-2224, 2234-2238, 2269-2274; 18 reused), 6 chests, 30 actors (5 hidden busts).
- Scenarios (real clicks) PASS: doors_exits, chests (one chest on the flooded crevasse bed opened by event), scripted
  (key, bolt, nozzle, drain, book, block, writ). Audit: DD14 room "cut off" false (Terror walks out, in and out of sight;
  plain-floor controls idle, so evidence is the placed Terror only); electrified pit a real trap.
- Brightness (final, ~22:15, lightmap-matched: direct 0.7, ambient 0.6, sky 0.4): validated against a real MM9 screenshot
  of the spawn corridor (real luma 62 / ours 57, same warm hue; `review/spawn_real_vs_v09.jpg`, read by the orchestrator).
  Per zone x1.00-1.22 of MM9's lightmaps (x1.67 open central ruin), hue within 0.03; cells screen luma 14-20 (lightmap
  data only, no real shot). Capture ratio x0.42 (information only). Capture-matched alternative (v08) documented.
- Unmatched: perception red lights at nozzles and pentagram fires' coloured lights (no switchable lights), dust puffs,
  swimming/diving, ambient sounds. Deviations: busts appear under their slabs; bolt breaks on click; stained glass 0.5
  alpha shows the room behind (old import drew it opaque); sky04; crevasse and pit wading floors (`WADING` switch),
  invisible ledge out of the pit; trap water stops under the ceiling. Map-local room-split patches in convert.py.
- Sheets: `level_generation/projects/mm9r_verhoffinruins/review/v08_compare.jpg`, `lighting_v08_compare.jpg`,
  `brightness_v08.txt`, final `v09_compare.jpg`, `lighting_v09_compare.jpg`. Orchestrator read v07, v08 and the v09 spawn comparison; v08 was installed by an orchestrator mistake and reverted after the real screenshot: geometry, doors, cells, torture and
  paddle rooms match MM9; cells now dim stone, not black.
- Not checked: rising water and paddle push in a running game, bake on the moving water face, arrival from Isle of
  Ashes, perception hints in a capture, combat beyond reach probes.
- Rule slip: deleted its own `review/cal` with `rm -rf` through a shell variable (recorded).

### Bathhouse (`bathhouse`), done ~22:20
- 2 462 faces, 25 rooms, 22 portal faces, 20 movers (10 sliding doors, gas valve, drain switch, propeller, vent flap,
  4 pistons, 2 water surfaces), 1 ladder, 73 BLV lights (5 capped + 20 DirLights bake-only), 63 decorations (2 new props,
  rows 2263-2268), 4 chests, 20 actors (16 placed + 4 hidden spores).
- Scenarios (real clicks) PASS: doors_exits (Door0, exit to Arslegard, ladder, Door6/7 locked until drain), chests,
  scripted (furnace valve, drain, 6 dives, steam vents, spores, concubines -> Ebora leaves, key 349).
- Water (no diving, reversible in convert.py): hall pool and tub wading with visible blue surface (opacity 1 x texture
  alpha 0.42, about MM9's SurfaceAlpha 0.5); other pools solid wading floors; MM9's swim route = 6 dive pads; drained
  room walked on its floor, surface sinks 30 s on the switch. MM9's water volume sides are Visible 0 (the old capture's
  blue wall at switch_shelf was an old-importer artefact).
- Brightness (lightmap-matched, second round): zones 0.90-1.31 of MM9's lightmaps (great hall +31 %), hue 7 of 8;
  23 dim lights carry MM9 BrightScale; Light108 x0.45 for the east corridor's teal. Capture x0.42 (information).
- Audit: 103 steps are pool/terrace/ramp edges; sealed furnace interior only unreachable region; colloidal walks off the
  wading floor; concubines Stationary by their monster row (control on plain floor also stays).
- Unmatched: Ebora camera cut/letterbox, rollover strings (own text), Fatc MoveIt/EboraArrive, DP2waterdamage, DP2steam
  FireOn/Off, ImpHenchman Help, camera quake (sound kept), BATHHOUSE.scr (unattached), concubines' random skins.
- Sheets: `level_generation/projects/mm9r_bathhouse/review/pages_v02_01-04.jpg`, `lighting_v02_p1-p6.jpg`,
  `work/fix_round2.jpg`. Orchestrator read round 1 (sent back: invisible water, blown wall, cast) and round 2 (accepted).
- Not checked: dives and drain animation on desktop, furnace fires with the valve open, Ebora/concubines (no model).

### Inventa Storca (`inventastorca`), done ~22:29
- 9 057 faces, 27 rooms (28 sectors), 29 portal faces (12 UserPortals, 10 archway cuts, 6 door leaves, 1 ladder hole),
  88 movers (59 rotating, 23 linear, 5 sink, 1 slide), 1 ladder, 71 BLV lights + 13 bake-only + 6 map-local cave lights,
  108 decorations (3 new props rows 2275-2277, 11 reused), 5 loot containers, 39 actors (9 dead adventurers), 13 pads,
  11 perception hints.
- Scenarios (real clicks) PASS: doors_exits, chests (floor-compartment bags/chests by event), scripted (step 88 fixed:
  the Lich King kills the dying adventurer within 20-30 s). Audit: no monster region cut off.
- Brightness (lightmap-matched, direct 0.46, ambient 0.671): zones 0.92-1.26, green party hall 1.72 (torches); hue
  8 of 8, slightly greener. Cave shaft x1.11, b/r 0.84 like MM9. Capture x1.03 (information).
- Black long tables traced: engine lights a decoration as room ambient + BLV lights - frame ambient (0.345 at minimum
  light 20); in rooms lit by bake-only DirLights, far from BLV lights, that is ~0. Map workaround: sector minimum light
  31 (frame ambient 0), ambient_scale raised to keep the bake; table top RGB (8,6,4) -> (31,28,21), still darker than
  the floor. Engine proposal (not made): baked decorations should not subtract the frame ambient, or room ambient should
  include baked direct light.
- Deviations: breakable walls break on click; falling-bookcase relay angles summed; basilisks/flyers vanish; no diving
  (cavern and well wading, fall -> well edge, 3 bone piles out of reach); AxeTrap absent from the DAT; 4 creature sounds
  missing from the audio import.
- Sheets: `level_generation/projects/mm9r_inventastorca/review/v07_compare.jpg`, `lighting_v07_compare.jpg`,
  `cave06_compare.jpg`. Orchestrator read v05 (sent back: black cave, black table) and cave06 (accepted). The capture's
  purple shaft rock reads brown-grey in ours: texture/tint difference, not traced.
- Not checked: each dresser/drawer, all 7 orbs (one clicked), ladder down from the top, real-hardware performance.

### Dook's Castle (`dookscastle`), done 23:00
- 4 588 faces, 11 rooms (12 sectors), 12 portal faces, 16 movers (7 double doors, secret slide + its invisible box),
  156 BLV lights + 18 bake-only + 7 DirLights, 96 decorations (9 new props, rows 2278-2294; 20 reused), 7 chests
  (one on the lake bed via a dive pad), 47 actors (21 militia, Baron Dook RUDE 415, 11 Trellborgs, 6 winged mutants,
  8 basilisks).
- Scenarios (real clicks) PASS: doors_exits, chests, scripted (friendly guards, letters, dialogue, sleepers wake,
  basilisks vanish, shield opens secret door -> guards hostile), alarm (hitting a guard turns all hostile).
- Lake: solid wading surface with MM9's animated ocean texture (reads as blue water), Ladder0 to the bridges; three
  invisible ramps at the rim (MM9's 40-48 LT rock steps are above our step). Shields hang point-down. Caves get their
  own darker ambient.
- Brightness (DAT lightmaps): castle 0.92-1.06, tunnels 1.62, north caves 1.29; capture x0.89 (information).
- Audit: 0 unreachable, 0 pits after the ramps; 4 low-ceiling actor notes false.
- Unmatched: militia wandering, sergeant waking walk and cower/fidget anims, basilisks running off (vanish), the
  hostility script's dialogue block. Engine notes (not changed): a hostile guard with engagement type 0 never attacks;
  a hostile monster stops ~400 units short of a party in view with its targeting flag off.
- Sheets: `level_generation/projects/mm9r_dookscastle/review/v03_compare.jpg`, `lighting01_compare.jpg`,
  `flames01/flames_sheet.jpg`. Orchestrator read v03: castle halls, corridors, throne room, armoury, caves and lake
  bridges match MM9 view for view.
- Not checked: actors (sprite load), desktop fight/bridges/ladder, save/load after the secret door, arrival in
  Guberland, the Baron's quest rows with Markel's keys, Android.

### Ta'Sar Academy (`tasaracademy`), done 23:23
- 6 918 faces, 29 rooms, 34 portal faces (15 UserPortals, 7 door leaves, 6 archway cuts, 6 rects: pit mouth, 5 pen
  gates), 45 movers (38 linear, 6 rotating, 1 sink), 2 ladders, 116 BLV lights + 5 bake-only + 4 DirLights, 304
  decorations (13 new props, rows 2302-2322), 4 chests, 26 actors (hidden Dagrell in the crate).
- Scenarios (real clicks) PASS: doors_exits, chests, scripted (library book puzzle, Book of Rules, bookcase, secret doors
  and switches, cracked wall, trap doors, chalices, skill books, letters, crate Dagrell, sparring, perception hints).
  Compiler tests 21 pass. Reach: Dagrell0 follows to the secret door and the shut door holds it (control run).
- Brightness (DAT lightmaps x1): zones 0.89-1.21, hue within 0.08 (neutral white); sector min light 31 workaround;
  capture x0.85 (information; library column, west corridor/dormitory, east octagon under 0.7x of the capture).
- Unmatched: TaSarGuardDuty.scr walks (no marker paths), teacher's attack anim before sparring, letter 434 on three
  invisible AI helpers, 9 ambient sounds.
- Sheets: `level_generation/projects/mm9r_tasaracademy/review/v03_compare.jpg`, `v03_pages_p01-p13.jpg`,
  `lighting_v03_compare.jpg`, `features02/`. Orchestrator read v03: halls, chalice room, arena with skylights,
  dormitories, library match MM9 view for view; actors now draw.
- Not checked: trap doors and bookcase in motion on desktop, arrival from Lindisfarne, perception hints at exactly 10 in a
  capture, the sparring fight, combat beyond reach probes.
- Props sub-agent found a stray 2 cm ball mesh in six other projects' models (incl. `bookflat`, `book`); left to owners.

### Training Hall (`traininghall`), done 23:48
- 6 697 faces, 13 rooms (14 sectors), 17 portal faces, 69 movers, 46 ladder strips (chain, 2 steel ladders, 11 poles
  x 4 sides with `grab_in_air`), 52 BLV lights + 18 bake-only + 16 DirLights as bake spots, 53 decorations (45 props +
  8 MM9 fires as flame cards; 6 new props rows 2295-2301, 7 reused), 5 chests, 22 monsters at MM9 sizes.
- Scenarios PASS: doors_exits (43: both exits, chandelier fall, lobby door, ladder, pole from the water, falling party
  grabs a pole, end door after its bar breaks), chests (28), scripted (107: lobby ghouls, horse levers, Mean Trellborg,
  wooden wall, archery targets and ring prize, crate boards, moving beams), monster reach (15).
- Audit: 3 regions, none real (roof start room by chain only, orc commander's podium false, crate top).
- Brightness (DAT lightmaps): zones 0.91-1.11, hue matches except the archery range (b/r 0.92 vs 0.82); capture x0.88.
- Engine: opt-in ladder `grab_in_air` (built 22:54, tests 2391/2391 and indoor 174/174). Map-local: invisible floor
  riding the chandelier, front exit box +24 LT, end exit panel leaves with the bar, archery rings as fully transparent
  faces, per-zone light boosts.
- Unmatched: monster idle loops (drills, gossip, joust walks), wheel spin, breakable skylight glass, 2 unused scripts.
- Sheets: `level_generation/projects/mm9r_traininghall/review/v02_compare.jpg` (37 views), `lighting_v02_compare.jpg`,
  `flames01_sheet.jpg`. Orchestrator read v02: roof, lobby pool, chandelier, pole room, corridors, joust lanes match;
  the training room's swinging arms appear at a different phase.
- Not checked: monsters drawn, the pole room as a real jumping course (no jump input in scenarios), real missiles on
  rings/boards/bar, a wall torch from the side here, save/load after training, arrivals from Thjorgard, Android.
- Rule slip: deleted its own `review/flames01` with a wildcard rm; regenerated.

### Lindisfarne Monastery (`lindisfarnemonastery`), done 00:52
- 13 766 faces, 7 rooms (8 sectors), 13 portal faces, 7 ladders, 40 movers (10 rotating leaves, 25 organ keys,
  5 bell ropes), 106 BLV lights + 20 bake-only + 264 DirLights, 125 decorations (11 new props rows 2323-2337, 8 reused),
  0 chests (none in MM9), 27 monks and NPCs. Hillside outside built; its up-facing faces TRIGGER_detail (outline limit).
- Scenarios (real clicks) PASS: doors_exits (8 door groups, 7 ladders), scripted (letters, organ key, bell order ->
  key 9507, monks walk to prayer via the new indoor evt.SetMapActorPosition, Thjorad click -> item 197 + key 162,
  hurting a monk turns the rest hostile), quests (dialogues and endings, Robert at 5:00), immobile (18 actors 30 s).
- Audit: 190 steps + 2 flights explained; fountain basin 0.03 M units^2 inside MM9's solid box; no monster cut off.
- Brightness (DAT lightmaps): zones 0.84-1.31 (east tower 1.29, bell tower 1.31: one big fill light each); slightly
  warmer than MM9; props 0.96-2.80 of their walls. Capture 92.0 / baked 51.6 (information).
- Engine: `IndoorWorldRuntime::setMapActorPosition` (see build log).
- Unmatched: monk work/prayer anims, wander paths and tools, bell swing and re-ring delay, book page anim, voice lines,
  ambient sounds, WeatherMan fog switching.
- Sheets: `level_generation/projects/mm9r_lindisfarnemonastery/review/v03_compare.jpg`, `lighting_v03_compare.jpg`.
  Orchestrator read v03: narthex, nave, choir, altar windows, courtyard, cloister, library, organ loft, bell tower match.
- Not checked: sounds, combat once monks turn hostile, arrival from Lindisfarne, save/load, desktop playthrough; a thin
  dark line along one cloister window and blotchy tower floors in the bake, not traced.

### Thjorad Mine (`thjoradmine`), done 01:38
- 11 076 faces, 59 rooms (60 sectors), 62 portal faces (53 auto archway cuts from `work/cuts/auto_cuts.py` + 6 by
  hand), 71 movers, 257 BLV lights (none over the cap, no bake-only), 371 decorations (13 new props rows 2338-2358,
  16 reused), 15 chests, 93 actors (73 placed + 20 hidden spawns), `model_lighting: true`.
- Scenarios PASS: doors_exits, chests, scripted (letters, RUDE 11/9/8/428, barricade, hard rock -> key 36 + Ebora freed,
  cave-in key 35, gnoll bust-out, spawns, slag extractor keys 9512/37 by events), machinery (torch/barrel chain, cart,
  steam valve, falling board, spiked boards, stalactite).
- Reach: flooded cavern "cut off" false (troglodytes chase up the flights; control same); abandoned mine west room real
  (72 LT fence vs 35 LT jump) -> invisible ramps, probe in and out.
- Brightness (DAT lightmaps): zones 0.93-1.25, hue within 0.09; BLV light colours x BrightScale/0.75 (rebuild +
  rebake); capture 27.0 / ours 26.0 over 70 views (information).
- Unmatched: Mine.scr (disabled by MM9 1.3), ThjoradQuake + 8 EarthQuakes (no camera shake), EboraCam1, miner walks,
  falling torches' fall and steam jet motion, perception lights, spawn manager respawn.
- Sheets: `level_generation/projects/mm9r_thjoradmine/review/v04_compare.jpg` (70 views; a07 moved out of the rock),
  `lighting01_compare.jpg`, `model_lighting_compare.jpg`. Orchestrator read v03 and the model-lighting compare.
- Not checked: desktop playthrough (cave-in fall, climb out, barrel chain), save/load mid-machinery, arrival in
  Thjorgard, Hjarrand/Gudrek quest rows, oil-lamp flames in game, Android.

### Yanmir's Fort (`yanmirsfort`), done 02:25
- 10 667 faces, 27 rooms (28 sectors), 31 portal faces, 79 movers (69 rotating: 30 double doors, 7 cages, secret wall;
  6 sinking supports; 4 sliding trap floors), 86 BLV lights + 1 capped fill + 610 per-polygon ice LIGHTDEFS lights +
  5 added basement fills (bake-only), 158 decorations (7 new props rows 2359-2382, 28 reused), 11 chests, 73 actors.
- Scenarios (real clicks) PASS: doors_exits (53), chests, scripted (126: Yanmir sleeps until his trigger and shrugs off
  attacks, supports break, trap floor gives way -> key 173, Forest Giants on reload, spawners + respawn after 920 s,
  child freed, fall -> Frosgard City). Compiler tests 21 pass. Audit: no actor cut off.
- Brightness (DAT lightmaps): zones 0.56-1.40, mean 1.02; MM9's strong cyan from the ice texture light per polygon.
  Darkest view luma 20.7. Capture x0.73 (information). Prop lighting compared (one capped light): old path 0.86,
  model lighting 0.66 -> old path + sector min light 31.
- Deviations: trap floor drops 399 LT (keeps its baked light), supports break on click, Yanmir chases on sight instead of
  his patrol (door kicks scripted), freed children vanish; own wording for their calls.
- Sheets: `level_generation/projects/mm9r_yanmirsfort/review/v03_compare.jpg`, `v03_pages_p01-p12.jpg`,
  `lighting_v03_compare.jpg`, `flames01_sheet.jpg`. Orchestrator read v03: geometry, doors, supports, cages, halls
  match MM9; ours is a deep saturated cyan/blue where the old capture is pale lavender, which follows MM9's lightmaps
  (accepted under the lightmap rule; worth a real screenshot). Wooden supports read green under the cyan light.
- Not checked: Yanmir's fall on desktop, arrivals from Frosgard/Frosgard City, monsters through doors, spawners and
  wading on desktop.
- Rule slip: one wildcard rm on its own review JPGs.

### Dark Passageway (`darkpassageway`), done 02:28
- 4 419 faces, 28 rooms (+1 path room from the `path_tube` cut), 21+ portal faces, 44 movers, 76 BLV lights + 44
  bake-only + 11 DirLights, 113 decorations (16 new props rows 2383-2403, 5 reused), 7 chests, 44 actors, 3 ladders,
  `model_lighting: true` (compared on six props: old path drew bushes x0.11 and chests near black).
- Scenarios (real clicks) PASS: doors_exits (106), chests (117), scripted (243: bridge puzzle on MM9's state tables,
  solve ADCBDCBA; 5 teleporter pairs; canyon statue and banshee eyes; forest ambush; painting's hidden room; mirror/
  gemstone puzzle frees 6 Terrors; spike trap; exit riser; Njam cameo; the Wyrde RUDE 338 opens the flame cage and the
  Guberland exit). Reach probes pass. Audit: 8 "unreachable" regions are areas joined only by teleporters.
- Water: solid wading surfaces at MM9's alpha, dive box tube room -> ocean, sea monsters stand on the surface. Carpet
  rises straight up (movers don't carry sideways), invisible plank to the statue ledge.
- Brightness: lit zones 0.89-1.19 of MM9's lightmaps before the floor; player-light stand-in floor per room
  (`ROOM_LEVELS` in convert.py, ambient_scale 0.22; revert = `ROOM_LEVELS = []`, 0.2): darkest view 9.6 (desert
  teleporter alcove), all others >= 11.4. Capture x0.27 (information).
- Unmatched: swimming, turning mirrors, carpet steering, spike damage, laser visuals, anims, ambient sounds, fireflies,
  MM9's player light.
- Sheets: `level_generation/projects/mm9r_darkpassageway/review/v02_pages_p01-p08.jpg`, `v02_compare.jpg`,
  `model_lighting_compare_p01.jpg`, `props01_pages_p01.jpg`. Orchestrator read p01 and p04 twice: first round pitch-black
  corridors (sent back), second round dim but visible.
- Open prop items: claw torches have an orb and no flame; ice statues opaque.
- Not checked: desktop playthrough (puzzles by hand, carpet, fights on water, deaths), save/load mid-puzzle, arrivals
  from Arslegard/Guberland, Android.

### Connecting Tunnels (`connectingtunnels`), done 02:54
- 4 254 faces, 31 rooms (32 sectors, 32 automatic tunnel cuts from `work/cuts/tunnel_cuts.py`), 32 portal faces,
  first map with a frame offset (x + 17 000; exits/arrivals shifted in convert.py, the shared table writer has no
  offset support), 4 movers (coffin lids, rock fall), 76 BLV lights + 7 capped fills + 8 ice-cap texture lights
  (bake-only), 119 decorations (17 new props rows 2417-2434, 6 reused), 2 chests, 38 monsters (12 untextured).
- No `.scr` scripts in the DAT; wiring as Lua: coffin lids lock/unlock the chest, a click breaks the rock fall.
- Scenarios PASS: doors_exits (exits, rock fall blocks then breaks on a click), chests, coffin. Audit: 0 unreachable,
  0 pits; 3 ceiling notes false (actors chase like the control); 17 steep flights walked.
- Brightness (DAT lightmaps): zones 0.84-1.38 (tunnels 0.98-1.14; centre/NE high from the player-light floor); blue
  halls about half as blue as MM9. New opt-in `ambient_colour` key in `tools/lighting/bake_indoor.py` (default white;
  MM9's blue world ambient 15/25/35). Player-light floor on 13 rooms (darkest view 13.0; revert `ROOM_LEVELS = []`).
  `model_lighting: true` after comparing (old path drew crates and skeletons black).
- Sheets: `level_generation/projects/mm9r_connectingtunnels/review/v02_compare.jpg`, `lighting_v02.jpg`,
  `model_lighting_compare.jpg`. Orchestrator read v02: tunnels, rock fall, blue coffin hall match MM9.
- Not checked: desktop playthrough, save/load, arrivals from Thronheim/Yorwick, candle flames in game.

### The Arena (`thearena`), done 03:45
- 1 421 faces, 4 rooms (hall + booth, open bowl with stands and Sven's box, two pens), 4 portal faces, 6 movers (arena
  double door rotates, 4 pen doors slide), 16 BLV lights (none capped) + bake-only sun and fills, `model_lighting:
  true`, 22 decorations (2 new props rows 2438-2440), 0 chests, 5 NPCs (Arena Master RUDE 430, Byri 245, Sven's double
  428, 2 clan soldiers; stand-in models).
- Arena fights ported into the map's Lua (Page/Squire/Knight/Lord, bouts with bets, Jarl Sven's plot); not the shared
  `ArenaRuntime` (MM6-MM8 arena: topic 704, MM8 awards, teleport; README explains). MM9 bug fixed: its script paid for
  1-n opponents but spawned one.
- Scenarios (real clicks) PASS: doors_exits, fight (Page to the purse), lord (key 214 -> 217), bout (50-gold bet pays
  75), sven (keys 230/231).
- Brightness (DAT lightmaps): hall 0.85, floor 1.16, pens 1.04/1.07, south stand 1.11, east stand 0.77, box 0.86; pens
  darkest at luma 18.6; capture 89.6 / baked 74.7 (information).
- Not built: 11 animated spectators (no peasant models; painted crowd cards built), crowd cheer/boo relays (a cheer
  sound instead). Deviations: bout fighters appear at pen mouths, NPCs move in one step, betting slips instead of
  figurines, counter bars click-through, diagonal stands' upper tiers too high to climb, a mid-bout load resets.
- Shared converter: `dungeon/build.py` fix for glass portals with more than four corners (crashed the build); Lich Lab
  --plan identical; lock released.
- Sheets: `level_generation/projects/mm9r_thearena/review/v04_compare.jpg`, `lighting_v04_compare.jpg`,
  `lighting_v04_detail.jpg`. Orchestrator read v04: hall, counter bars, corridors, stairs, bowl with crowd cards, pens
  match MM9 (our projected sky is daylight where the capture's is dark blue).
- Not checked: Knight/Lord fights with several opponents, sounds, jumping onto the counter, save/load mid-bout, actor
  models, x4 textures.

### Hall of the Gods (`hallofthegods`), done 04:09
- Enclosed geometry: an open colonnaded temple inside MM9's 6 sky faces (porch with the gate, west hall with pool,
  great stair, throne hall); a story map, not a cutscene stage. 2 164 faces, 1 room (colonnades open on every side,
  no cut possible), 0 portals, 0 movers, 34 BLV lights + 12 capped + 31 DirLights (bake-only), 41 decorations (props
  rows 2441-2451; god statues in MM9's `statue` pose, the old import T-posed them; MM9 ships no dragon models),
  0 chests, 10 actors (Krohn, Skraelos, Fre, the Great Honk with RUDE dialogue; 6 hidden cinema cast). Sky faces carry
  MM9's Arslegaard sky box at full brightness.
- Lua: Krohn gives Njam's Key; Skraelos' six-fires reward and the Afterworld move (asks first, as MM9); Fre takes the
  Golden Honk; bill of sale; end game with key 109 -> cast appears ~90 s -> Writ of Fate, Krohn back on his throne.
  Gods borrow the peasant family's relations (`ally` 118) because their stand-in families are hostile to the party.
- Scenarios PASS: doors_exits, scripted, quests, immobile; compiler tests 21/21.
- Brightness (DAT lightmaps): porch 0.80, west hall 1.00, stair 1.01, throne hall 1.23, dais 1.07 (one room = one
  ambient); `model_lighting` tried and off (lions black, statues dark).
- Not carried: cinema cameras and 13 voice lines, MM9's end-game score screen (the engine's win screen shows MM8's
  text), Skraelos' six fires scenes (Afterworld), voices and ambient sound.
- Sheets: `level_generation/projects/mm9r_hallofthegods/review/v02_compare.jpg` (25 views), `lighting01_compare.jpg`,
  `model_lighting_compare.jpg`. Orchestrator read v02: temple, gate, pool, lions, stair and throne hall match MM9;
  ours shows a cloud sky where the old import was a navy void.
- Not checked: the cinema on desktop, arrivals from neighbours, Arslegard exit on desktop, save/load, Android, statue
  LOD/collision. Headless walking stops at the stair's last step (desktop walks up).

### Dungeon of Secrets (`dungeonofsecrets`), done 04:09
- 5 096 faces, 10 rooms, 10 portal faces, 155 movers, 139 BLV lights + 25 capped + 1 DirLight (bake), 55 decorations
  (34 claw torches, claw lamp, 20 sconces; new `sconce2`, rows 2436-2437), 0 chests, 1 actor (Chadwick Boorsley, RUDE
  417, through the booth's bars).
- The trial runs from MM9's own object links (123 triggers, 150 doors, 80 shooters, 23 knockbacks) through one
  dispatcher in the map Lua; a timer lever's lock holds its axe trap until the lever creeps shut (each section's clock).
- Scenarios PASS: trial (201: all nine sections by real lever/door clicks against each clock; the walk between is waited,
  not walked; exit gate -> key 245), traps (233: late door axe, fire plate, rat volley, 6 of 10 gauntlet plates, double
  axe, blade, fake lever, water grate, perception hints), doors_exits (35: Chadwick's dialogue + key 247, Frosgard exit).
- Brightness (DAT lightmaps, `work/hue.txt`): 10 of 15 zones 0.9-1.14; exit corridor red 0.69, gauntlet 0.71-0.79,
  shaft foot green 0.67, section 4 corridor 1.27. The plate room and gauntlet are deep red in MM9's own lightmaps
  (B/R 0.38; ours 0.37), where the old capture is grey. No view under luma 12; model lighting off (sconces black).
- Deviations: invisible steps onto the elevator box and out of the pool room, submerged tunnel without swimming (party
  moved back up), double axes built where their carrier slides them, blade spins once, non-solid trap faces untouchable,
  every load resets the trial.
- Unmatched: rat cameo targets and knockback25-29 (absent in the DAT), saw/blade spin, Chadwick's voice, 31 ambient
  sounds.
- Sheets: `level_generation/projects/mm9r_dungeonofsecrets/review/v02_compare.jpg` (43 views), `lighting_v02_compare.jpg`,
  `props_compare.jpg`. Orchestrator read v02 part 2 and the hue table: geometry matches; the red rooms follow MM9's
  lightmaps.
- Not checked: desktop playthrough (jumping the double axe's plate, knockbacks, fire bolts), sconce flames in game,
  4 gauntlet plates and the lower axe plate, the tunnel route, arrival in Frosgard, Android.

### Dragon Stadium (`dragonstadium`), done 04:11
- 1 480 faces, 3 rooms (4 sectors), 2 portal faces, 0 movers, 3 lights + bake-only sun, 5 decorations (1 new row 2452),
  2 chests, 1 actor (the Dragon King, a static boss). Pillars: 7 stacked levels each; breaking one hides it and all above
  (movers impossible: 2 950 tall, over the 1 024 baked-mover limit). New opt-in bake key `shadowless_faces`
  (`tools/lighting/bake_indoor.py`, default empty) so pillars cast no baked shadow.
- Scenarios PASS: doors_exits (exit, pillar p1 blocks then breaks on a click, p3 breaks from level 2), chests, scripted
  (Dragon King hidden until the arena-mouth trigger; 2 Winged Mutants after 45 s; death -> key 472 + item 10577,
  spawns stop).
- Brightness, walls only by face normal (`work/walls_vs_lightmaps.py`): bowl walls 0.85 -> 0.99 (arena sector light 18,
  `ARENA_LEVEL`), tunnel walls 0.99-1.04, floors 0.96-1.06, slopes 1.15; hue matches. MM9's own screen value for these
  walls is about texture 72.4 x lightmap 0.196 = 14; ours 15-16; the old capture's even grey rock (79-92) is the old
  import. Darkest view 13.
- Unmatched: the Dragon King's fly-in, Land/Taunt clips, movement, target switching, wing push-back, smoke, growl and
  landing sounds; pillars break on a click (no weapon/fire damage, no explosion damage or debris).
- Sheets: `level_generation/projects/mm9r_dragonstadium/review/v03_compare.jpg`, `lighting_compare_v03.jpg`,
  `dragon_sheet.jpg`, `pillars_sheet_a/b.jpg`. Orchestrator read v02 (sent back: walls near black) and accepted the
  wall-only measurement: the darkness is MM9's own; a real MM9 screenshot of the bowl would confirm it.
- Not checked: breaking a pillar by desktop click, the fight on desktop, walkability ledges in game, sound. Finding: the
  party gets ~240 units into the foot of a wall that leans back (shared collision; not changed).

### The Thousand Terrors (`1000terrors`), done 04:40
- 17 769 faces, 19 rooms, 20 portal faces, one air component (24 outside seeds excluded), 121 movers (38 rotating,
  83 linear: three 4x4 button walls, 912 LT gear lift, plates, gates, doors, levers), 379 BLV lights + 154 fills + 81
  DirLights (bake-only), 402 decorations, 14 chests, 114 actors. `model_lighting: true`, light_scale 1.2 (old path drew
  the skull head black).
- Outline limit (~12 000 vs 7 000): new estimator `outlines.py` (matches the compiler on Lindisfarne and the Chasm);
  1 867 smallest up-facing faces compiled as invisible detail -> 6 299, redrawn at load.
- Candle orbs: 117 translucent orbs as decorations (`mm9_waterorb`, opacity 0.4). As 9 828 translucent BLV faces they
  made the desktop renderer refuse the map (one batch per translucent face); headless did not show it.
- MM9 object links (triggers, door triggers, shooters, spawners, spawn markers, death triggers) as data through one Lua
  dispatcher, plus button puzzles, chess board, Njam's appearances and taunt, win switch (rewards -> Hall of the Gods),
  genie lamp, chess note.
- Scenarios PASS: doors_exits (every clickable door group by real click, poses from `make_scenarios.py --probe`),
  chests (14 by real clicks), scripted (Pull2, HiddenButton1, Rotating Lever 17 by event: no headless pick target).
- Brightness: zones x1.05-1.41 of MM9's lightmaps, deliberately (player-light stand-in floor; without it eight views
  were luma 7-10; darkest now 10.7; ambient 0.7 gives x0.74-1.13). Capture 19.5 / ours 21.0 (information).
- Audit: the upper halls are reachable only by the lift (as MM9); big monsters do not take the spiral stair down, so the
  crypts are cut off in our engine (MM9 uses AI rails, not built); south halls not probed.
- Shared converter: `tables.transitions_text` now starts from the review root's current row (fixes the shared-row
  overwrite with hallofthegods); Lich Lab --plan identical. Row 444 reads 1000terrors.blv -> hallofthegods.blv.
- Not carried: shooters travelling their markers, chess pieces moving/queening, weighted lifts, gears and skull turning,
  flyer paths, cutscenes and cameras, earthquake and lightning objects, ambient sound, orb touch damage.
- Sheets: `level_generation/projects/mm9r_1000terrors/review/v02_compare.jpg`, `lighting01_compare.jpg`,
  `ml_new_compare.jpg`. Orchestrator read v02: blue halls, sorcerer rooms, water hall, foyer, chess board, Njam's hall,
  win switch, lift top match MM9 view for view.
- Not checked: riding the lift, combat and shooter bolts, south-hall reach, arrival from Arslegard, desktop level change
  after the win switch, save/load, sounds, Android, orbs and flames up close.

## Progress log
- 17:42 all five running: klusoshouse built + scenarios pass (holds converter lock since 17:39); verhoffinruins built (5 703 faces); inventastorca first compile; ruinedtemple props; bathhouse rooms plan (water route decided: wading + same-map moves).

- 18:30 paused by the user; 21:52 resumed (4 agents resumed by ID, traininghall started). Another session was running `cmake --build build --target openyamm` at resume time (not ours).

- ~22:00 bathhouse reported DONE; orchestrator read pages_v02 01-04 + lighting p1: sent back for one fix round (hall pool and tub water surface invisible vs MM9's blue surface, missing vertical water face at switch_shelf, blown-out wall at flood_stairs_foot, teal/yellow cast in east corridor).

- ~22:02 inventastorca reported DONE (9 057 faces, 27 rooms, 88 movers, 39 actors, 3 scenarios pass, baked mean 1.02x MM9). Orchestrator read v05 + lighting sheets: geometry matches; sent back for cave darkness/hue (views 32-33 near black vs MM9 purple) and a long table drawn solid black (u11).

- ~22:04 verhoffinruins reported DONE (5 954 faces, 29 rooms, 76 movers, 30 actors, 3 scenarios pass) but calibrated to DAT lightmaps: baked x0.42 of the capture, cells x0.22 (near black). Orchestrator decision: maps calibrate the mean against the capture (as all other finished maps) with lightmap hue/ratios kept; the lightmap-matched settings stay documented as an alternative. Sent back.

- ~22:25 user supplied a real MM9 screenshot (Verhoffin spawn). It matches the lightmap-matched bake, not the capture. Brightness standard reversed; verhoffinruins told to reinstall its v07 settings; all agents told.

- 22:31 user supplied 4 real Klusos House screenshots (`real_mm9/klusoshouse_real_*.png`): central luma 64.5, 47.5, 37.2, 91.9 vs our lightmap-matched lighting views 28-52 (mean 39) and capture 93: the lightmap bake looks 1.3-1.7x too dark in lit rooms, right in the dark room; real is warmer (b/r 0.49-0.67). Shot 3 shows MM9 props bright beside dark walls (ours: props darker than walls). Klusos agent resumed to calibrate to the real shots (6 agents briefly: over the 5 cap for a short recompose task). Rule added: real screenshots outrank the lightmap math.

- 22:33 research agent afa57275cf6cb13a0 started (user suggestion): Rizin on mm9/game/d3d.ren, lithtech.exe and mm9.exe for lightmap blending (modulate x1/x2, gamma), model/prop lighting, world adds; output devdocs/mm9_rework/MM9_RENDER_LIGHTING_RE.md. Read-only, no game runs. Result decides the calibration rule and the decoration-lighting engine change.

- 22:44 klusoshouse matched to the real shots: MM9 on screen = about 1.2-1.37x its stored lightmap texels (Verhoffin 1.1x). Interim rule for new maps until the RE result: lightmap texels x ~1.2 unless real shots exist. lindisfarnemonastery started.

- 23:00 RE result (`devdocs/mm9_rework/MM9_RENDER_LIGHTING_RE.md`, proven from d3d.ren): walls = texture x lightmap x1 (no 2x, no gamma, no brightness term); dynamic Fire/candle lights add on top (the likely source of Klusos' 1.2-1.37x); models lit by world AmbientLight + full-colour lights (no BrightScale, no shadows) + ModelAdd 30, clamped. Interim x1.2 rule withdrawn; brief updated; running agents told. Engine agent a4221ca3bfad355ef started: opt-in MM9 model lighting for decorations (scene block + converter opt-in), MM6-MM8 unchanged. dookscastle and beethoven accepted; thjoradmine started.

- 02:06 darkpassageway reported DONE; orchestrator read v02 pages p01/p04: corridors pitch black (luma ~2) where MM9's player light (PlayerLightOn) lit them. Decision: no view below ~luma 10-12 baked; a per-room floor stands in for MM9's player light (rule added to AGENT_BRIEF.md). Sent back for one round.

- 03:52 dragonstadium reported DONE (1 480 faces, 3 rooms, 2 chests, Dragon King static boss, pillars break by levels, 3 scenarios pass, new opt-in `shadowless_faces` bake key). Orchestrator read v02: rock walls near black in tunnels and bowl where MM9 is evenly lit grey rock; sent back to compare wall-only lightmap texels and add the missing sky/bounce.

- 04:10 queue finished (19 maps: 17 built or running, greatgate skipped). Free slots used for the recalibration queue: ruinedtemple revisit, five pre-overnight maps re-lit by one agent.

## Engine changes

- 23:00 build for traininghall's request: `IndoorLadder::grabInAir` (opt-in scene key `grab_in_air`, default off; `indoorLadderGrabAllowed`; test "ladder: only a standing body grabs, unless the ladder takes a body in the air"). Orchestrator reviewed the diff: ladders without the flag behave as before. Targets openyamm, openyamm_unit_tests, mm9_compile_indoor_source built 22:54-22:59. Tests 23:00-23:03: openyamm_unit_tests 2391/2391 pass; indoor regression suite (--world mm8, private user data) passed=174 failed=0 (the five failures listed on 2026-10-30 are no longer failing); log output/mm9_rework/overnight_tests/indoor_2259.txt.

- 23:33-23:37 build for the engine-model-lighting request (opt-in scene `model_lighting: {mode: mm9, ambient, add, light_scale}`; fs_model.sc fixed-function branch, sprites via `sampleModelLightRgb`, actors included; converter opt-in `map: {model_lighting: true}`, Lich Lab --plan and full --scratch identical). Orchestrator reviewed: every changed path gated on the flag, off path uniforms unchanged. Note: IndoorRenderer.cpp also carries another session's uncommitted keyboard-picking rework, built along. Unit 2396/2396 (5 new); indoor suite 174/174 (log indoor_2338.txt, finished 00:05). Engine agent resumed for the Klusos real-shot and MM8 before/after verification.

### Engine change 2: MM9 model lighting (opt-in; used per map where it measured better)
- Scene `model_lighting: {mode: mm9, ambient, add: [30,30,30], light_scale}` lights decorations and actors MM9's way
  (ambient + 30 + full-colour lights x (1 - d^2/r^2) x N.L, no occlusion: `IndoorLightingFrameInput::lightsIgnoreReach`);
  converter opt-in `map: {model_lighting: true}`, default off. Doc `devdocs/INDOOR_MODEL_LIGHTING.md`. Off = old path
  (Lich Lab converter output identical; MM8 d06 pixel-identical except the animated lantern; unit and indoor suites pass).
- Result on Klusos House's real shots: old path x1.02/1.01/0.96/0.89, model lighting x0.92/1.01/0.77/0.88; props
  darker and browner (`level_generation/projects/mm9r_klusoshouse/review/model_lighting_props01.jpg`, read by the
  orchestrator). Cause: MM9 models also got the large fill lights our converter keeps out of the BLV (bake-only once a
  floor point has four lights), e.g. Light19 gives Klusos cabinets 0.5-0.57 of its colour in MM9.
- Revised (01:38) after Thjorad Mine's comparison (`level_generation/projects/mm9r_thjoradmine/review/model_lighting_compare.jpg`, read by the orchestrator: old path draws its ore bin black, model lighting keeps props x0.72-1.17 of the capture): **use `model_lighting: true` where no light is over the four-per-point cap** (no bake-only fill lights); where capped lights exist, compare both paths on the map's props and keep the better. Earlier decision (00:35): Klusos stays on the old path (`model_lighting: false`); map agents keep the
  sector-minimum-light-31 workaround. **Proposed next step for the user:** let `model_lighting` carry the bake-only
  (capped) lights for models only, then re-test on Klusos. The engine code stays in the tree, unused, for the user to
  keep or drop.

## Cross-map issues
- Borrowed MM6-MM8 monster sprites fail to load in the review root ("requires cooked schema 2"): actors invisible in shots (Klusos House). Not fixed overnight; other session owns monster art.

- **Decorations darker than the walls under lightmap-matched bakes** — cause found by inventastorca (see its entry): frame-ambient subtraction in decoration lighting; per-map workaround sector minimum light 31; engine proposal written down, not made (would change MM6-MM8 baked maps' decorations). (Klusos lighting08: chairs and tables near black beside lit walls; Inventa Storca's black long table; Ruined Temple's dark banners may be the same). Being checked by the ruinedtemple and inventastorca agents; engine fix only if a small shared one.

- Desktop game closed at startup in the shared review root ~22:50-23:10: "Actor model load failed: worlds/mm9/models/actors.yml ... attack_ranged", another session's edit; cleared by itself. Headless unaffected.
- Stray 2 cm ball mesh in six `mm9_deco_*` models from other props projects (found by tasaracademy's props agent; owners to fix).

- `openyamm_runtime_tests`: `New Sorpigal temple braziers toggle and retain their light state across save and reentry` fails (billboard texture with the frame's palette not loaded; IndoorDecorationInteractionTests.cpp:44). Not from tonight's changes as far as the code shows (decoration sprite loading); not compared with HEAD.

- Shared converter `tables.py` `OLD_SIDECARS` misses `<stem>_authored.scene.yml` and `events/maps/<stem>_authored.lua` (they break the map load / replace our Lua); thjoradmine removes them in its own convert.py; Drangheim, Thjorgard and Boot Camp also have them (outdoor). Converter fix left for the user/next converter owner.

- Shared review-root `map_transitions.txt` rows between two converted maps (1000terrors <-> hallofthegods) were overwritten by each other's convert.py (the writer rebuilds a row from the original file): every game load failed for ~5 min with "row 3 ... unresolved". Both agents told to merge their half under the review tables lock. Shared writer fix left for later (merge per side).
- `tools/lighting/bake_indoor.py` gained an opt-in `ambient_colour` profile key (connectingtunnels; default white, other maps unchanged).

- Shared `dungeon/tables.py` changed by the 1000terrors agent (02:45): converted rows are now merged per side instead of rebuilt from the original (fixes the shared-row overwrite). Side effect reported by hallofthegods: a map's own exit settings are no longer reapplied once its row is converted (it wraps its gate exit box in its own convert.py). Review when the user audits the converter.

- `util/map_export.py` reads BLV vertex indices as signed: negative above 32 767 vertices (1000terrors masks them).
- Many translucent BLV faces (thousands) make the desktop renderer refuse a map (one render batch each); headless runs do not show it. Use decorations for small translucent objects.
- Big monsters do not path down spiral stairs (1000terrors crypts); MM9 uses AI rails.

## Failures and skips
- **greatgate, skipped 03:51:** `GREATGATE.dat` is an unused test copy of the Great Gate cutscene (open-air set in a sky
  box, no lights, no exits; Hanndl and the Loseman/Fateman cutscene managers). Nothing in MM9 loads it; the final
  scene lives in Arslegard City (with WRITMAN.scr and ExitTrigger2). Belongs to the Arslegard City (outdoor) conversion
  as events. Record: `level_generation/projects/mm9r_greatgate/README.md`.

## 2026-10-31 afternoon: invisible ramp bottoms, Firethrough, rebuild of all 24 dungeons, lighting

### Converter change
- Under the converter lock, 14:15-14:2x. Invisible collision brushes' down-facing faces at most the party's height over
  a floor are dropped (`floors.invisible_bottoms`; opt-out `map: {drop_invisible_bottoms: false}`).
- `Misc\Firethrough.dtx` is a helper texture, invisible whatever its flags; only Lindisfarne had such polygons drawn.
- Proof: Lich Lab `--plan` differs only by 46 dropped faces.
- Playbook: "Package change: invisible brush bottoms and the Firethrough helper".

### Rebuilds
All rebuilds started after the monster-size change (14:37), from `convert.py` and the current converter. Times are
start-end of `convert.py`:

| Map | Rebuild | Bottoms dropped |
| --- | --- | --- |
| tasaracademy | 14:52-14:53 | 15 |
| templeofhonk | 14:52-14:53 | 38 |
| yanmirsfort | 14:52-14:56 | 35 (also 14:27, before the size change) |
| thjoradmine | 14:54-14:58 | 1 |
| anskramkeep | 14:55-14:56 | 3 |
| lichlab | 14:57-15:02 | 46 |
| klusoshouse | 14:57-14:58 | 4 |
| verhoffinruins | 14:58-14:59 | 0, BLV identical |
| inventastorca | 14:59-15:00 | 1 |
| dungeonofsecrets | 15:00-15:00 | 0, BLV identical |
| hallofthegods | 15:00-15:01 | 30 |
| dookscastle | 15:01-15:02 | 0, BLV identical |
| dragonstadium | 15:01-15:02 | 3 |
| thearena | 15:02-15:02 | 54 |
| traininghall | 15:02-15:03 | 1 |
| bathhouse | 15:03-15:03 | 2 |
| ruinedtemple | 15:03-15:04 | 9 |
| chasmofthedead | 15:04-15:10 | 20 |
| connectingtunnels | 15:05-15:08 | 0, BLV identical |
| darkpassageway | 15:08-15:10 | 2 |
| beethoven | 15:11-15:14 | 39 |
| drangheimprison | 15:14-15:18 | 1 |
| lindisfarnemonastery | 15:18-15:20 | 23, plus 11 Firethrough faces made invisible |
| 1000terrors | 15:22-15:28 | 15 |

Exact start times are in `level_generation/projects/mm9r_common/rebuild_1031/<map>.log`.

### Checks
- Scenarios pass, with three exceptions (all fixed in the evening, see "2026-10-31 evening" below):
  - Training Hall `scripted` step 8 and Dark Passageway `scripted` step 192: pre-existing, identical on the old BLVs.
    Both scenarios passed: these were the runner's tolerated "transient state" warnings, which `rebuild_map.sh`
    counted with every `ASSERT fail` line (its scenario "exit 0" is also no verdict: read `Scenario passed`).
  - Anskram Keep `rotating` step 36 (TrapExitDoor1 still opening): caused by the monster sizes. It passes on the
    rebuilt BLV with the old actor sizes. Left for the monster-size session.
- Honk's repro climbs (user pose 0 -> 817 / +304; `scenario_stairs.yml` passes).
- Stair probes: Ruined Temple's stair freed (0 -> 114 / +37). All others are identical before and after, and the
  boxes still block.
- Lindisfarne: 0 visible Firethrough faces, no magenta.

### Lighting
- The lightmap transfer is deferred (user). The tool is hardened and documented in
  `devdocs/mm9_rework/MM9_LIGHTMAP_TRANSFER.md`, "Hardening and recipe". No map was transferred.
- Cycles re-bakes are deferred too.
- Removed via `review_root.remove`, with copies in each project's `work/lighting_stale_20261031/`: every rebuilt map's
  stale sidecar, plus the nine maps that the water scene change made stale. Only `connectingtunnels` and `dookscastle`
  keep their dungeon sidecars.
- `stale_bakes.py --assets output/mm9_rework/assets_dev --check` lists no MM9 map.

### Incident
At about 14:30 this session removed the converter lock (`locks/converter_edit.d`) by mistake while the monster-size
session held it: a failed `mkdir` claim followed by an unconditional release line. It recreated the lock within
seconds, with a note in `owner`, and the holder released it normally at 14:52. The holder's own `owner` text was lost.

## 2026-10-31 evening: the three scenario failures, and every dungeon scenario green

### Causes and fixes
- **Anskram Keep `rotating` step 36** (scenario). Not the table (the old table fails too) and not the BLV: the scene's
  actor sizes. NagateHatchling3 (MM9 radius 46; the stand-in's 109 kept it at x 1681) followed the party from the
  double doors to the trap corridor during the scenario's waits and stood with its body in TrapExitDoor1's swing, which
  waited for it. The mover test relied on the oversized body keeping monsters away; `make_scenarios.py` now slays the
  placed monsters awake at load (not the Invisible Giant Imp and guards) before the mover checks.
- **Training Hall `scripted` step 8** (engine, change 5 above). The pole room beams waited about 4 s out instead of
  MM9's 3 s: their handler restarts itself every 0.25 s and counts ticks as its clock, and each tick took about 0.3 s.
  Now 3 s out, 11.5 s cycle. No map change.
- **Dark Passageway `scripted` step 192** (scenario). ForestDoor0 rises 96 LT at 70 LT/s (1.4 s); `opening` was
  checked 3 s after the trigger. `make_scenarios.py` checks `opening` at 1 s and `open` 2 s later.
- Neither Training Hall nor Dark Passageway ever failed: both were tolerated transient-state warnings, already in the
  build night's logs, counted as failures by `rebuild_map.sh` (it counts every `ASSERT fail` line).
- **Dungeon of Secrets** after the engine change (its 0.1 s poll now really ticks every 0.1 s): `doors_exits` never
  crossed MM9's `knockback off` trigger (its walks start west of it), so knockback02 (MM9 `StartOn`) threw the party down
  section 2's stair; the scenario now crosses it first, as the arriving party does. `traps` checks the gauntlet plates
  0.5 s after the pose (1.2 s was calibrated to the slow poll). The Lua's clock calibration is gone (`clock = tick *
  0.1`; it ran about 13 % fast) and `convert.py --lua` applies the blade's single turn (it wrote 3.6 s); Lua only.
- READMEs: anskramkeep, traininghall, darkpassageway, dungeonofsecrets.

### Every scenario of the 24 dungeons
One run, 2026-10-31 ~16:30, binary 15:53 (this change), review root: **92 of 92 pass, no transient-state warning**
(per scenario: `level_generation/projects/mm9r_common/rebuild_1031/scenarios_final_1031.txt`).

| Map | Scenarios | Result |
| --- | --- | --- |
| 1000terrors | chests, doors_exits, scripted, stair_probes | all pass (4) |
| anskramkeep | chests, doors_exits, rotating, scripted | all pass (4) |
| bathhouse | chests, doors_exits, scripted | all pass (3) |
| beethoven | chests, doors_exits, scripted | all pass (3) |
| chasmofthedead | chests, doors_exits, pivot, scripted, stair_probes | all pass (5) |
| connectingtunnels | chests, doors_exits, scripted | all pass (3) |
| darkpassageway | chests, doors_exits, scripted | all pass (3) |
| dookscastle | alarm, chests, doors_exits, scripted | all pass (4) |
| dragonstadium | chests, doors_exits, scripted | all pass (3) |
| drangheimprison | chests, doors_exits, immobile, quests, scripted | all pass (5) |
| dungeonofsecrets | doors_exits, traps, trial | all pass (3) |
| hallofthegods | doors_exits, immobile, quests, scripted | all pass (4) |
| inventastorca | chests, doors_exits, scripted | all pass (3) |
| klusoshouse | chests, doors_exits, scripted | all pass (3) |
| lichlab | chests, doors_exits, scripted, stair_probes | all pass (4) |
| lindisfarnemonastery | doors_exits, immobile, quests, scripted, stair_probes | all pass (5) |
| ruinedtemple | chests, doors_exits, scripted, stair_probes | all pass (4) |
| tasaracademy | chests, doors_exits, scripted, stair_probes | all pass (4) |
| templeofhonk | chests, doors_exits, hostility, scripted, stair_probes | all pass (5) |
| thearena | bout, doors_exits, fight, lord, stair_probes, sven | all pass (6) |
| thjoradmine | chests, doors_exits, machinery, scripted | all pass (4) |
| traininghall | chests, doors_exits, scripted | all pass (3) |
| verhoffinruins | chests, doors_exits, scripted | all pass (3) |
| yanmirsfort | chests, doors_exits, scripted, stair_probes | all pass (4) |

## 2026-10-31 night: Sturmford City pilot (cities as BLV + sky)

Session `openyamm-06` (unattended), on the user's decision of 2026-10-31 (PLAN.md, Cities row). Record:
[`level_generation/projects/mm9r_sturmfordcity/README.md`](../../../level_generation/projects/mm9r_sturmfordcity/README.md);
recipe for the other six cities: [`CITY_PLAYBOOK.md`](../../../level_generation/projects/mm9r_common/CITY_PLAYBOOK.md).

- **Verdict: a city works as a BLV.** Sturmford City is built in the review root: 12 926 faces, 21 148 vertices (32 %
  of the 16-bit index range), coordinates inside ±32 767, 0 outlines (painted minimap), 63 sectors, 343 portal faces,
  105 doors, 48 actors (44 RUDE dialogues), 9 posed talking props, 439 decorations, 2 chests, 6 exits, 6 starts.
- **Structure**: 37 walk-in interiors behind door portals and 37 glass (window) portals; the districts' open air is
  divided by a roof line (street air under the eaves, one roof room per district: 244 top-portal rectangles) and 23
  street cuts found automatically at narrow corridor places (`mm9r_common/city/structure.py`). MM9's VisBSP has a PVS
  (2 057 leaves) but no portal graph for streets, so it is not used. Median 5 sectors drawn per view (max 12).
- **Performance counts** (32 views; frame rate needs a single session): draw calls median 218 / max 385 against the old
  ODM import's 1 347 / 1 879 and MM8 Ravenshore's 262 / 313; triangles 30.6 k / 70.8 k against 57.5 k / 156.5 k and
  195 k / 347 k; map load 1.46 s against 2.73 s; 16 goblins: 1.5-1.7 ms CPU per goblin per game second.
- **Engine (opt-in, MM6-MM8 untouched)**: an indoor map open to the sky (`sky: {mode: open}`: the sky faces are not
  drawn, the Enhanced outdoor sky with the time of day is drawn behind the scene; `devdocs/INDOOR_OPEN_SKY.md`). Unit
  tests 2 429 / 2 429; `openyamm_runtime_tests` 54 / 55 (braziers, predates); `indoor` regression suite 173 / 174 (the
  ogre case, another session's); `openyamm_indoor_source_tests` 21 / 21. The painted indoor minimap was already in
  the engine.
- **Build fix**: `tools/CMakeLists.txt` was missing `game/indoor/IndoorSectorFaceGrid.cpp` (the per-sector grid of
  2026-10-31) in `openyamm_indoor_source`: `mm9_compile_indoor_source` failed to link (and a failed relink deletes the
  binary: it was gone for about 10 minutes at 17:30 while this session rebuilt it). Fixed and rebuilt.
- **Converter (both opt-in; Lich Lab `--plan --scratch` identical)**: `Hooks.extra_portals`; `map: {painted_minimap:
  true}` (catalog entry kept, `generate_outlines: false`).
- **Scenarios**: doors_exits, shops (walk-in shops by real clicks), chests (and the well's rope), scripted: all pass.
- **Review**: `review/v03_compare.jpg` (32 views, MM9 old import | ours: same city, no holes), `review/sky01_sheet.jpg`
  (dawn, noon, dusk, night).
- **Specified, not built** (CITY_PLAYBOOK "Engine features"): weather in open-sky sectors, a time-of-day scale on
  static light, outdoor-only rules by "open to the sky", 32-bit vertex indices (not needed here).
- **Open**: floor check 150 535 LT² (no wrong sector seen in any view); MM9's breakable windows, hire keys and
  Perception hints not carried; townsfolk are stand-in peasants until the town NPC bodies exist.
- **Street lights (2026-10-31, late)**: `map: {bright_scale_lights: true}`: 123 of 151 BLV lights at colour x
  BrightScale (0.2-0.85); the palace front and north lane no longer glare, the ring north keeps a warmer wash
  (`review/bs_compare_<time>.jpg`). doors_exits, shops, chests, scripted pass.

## Thjorgard City

Record: [`level_generation/projects/mm9r_thjorgardcity/README.md`](../../../level_generation/projects/mm9r_thjorgardcity/README.md)
(wave 1 of [CITIES_ROLLOUT.md](../CITIES_ROLLOUT.md); props:
[`mm9_thjorgardcity_claude`](../../../level_generation/props/mm9_thjorgardcity_claude/README.md)).

- **The largest city DAT, built as a BLV open to the sky:** 27 911 faces, 37 979 vertices (58 % of the 16-bit index
  range; no widening), coordinates inside ±32 767, 89 sectors, 1 470 portal faces, 145 doors, 160 lights, 60 actors,
  730 decorations, 0 chests (none in MM9), 3 exits, 4 starts, painted minimap, Enhanced sky with time of day.
- **Faces per sector:** max 3 579 (the air over the town's roofs), median 95. The `--plan` estimate before the props
  and scripts work was about 34 000 vertices.
- **Structure:** a roof line at 224 LT and 18 street cuts (one by hand in the north gate) over the walled town only.
  The hillside and palace terrace are their own open-air room, split from the roof air by one archway cut over the
  north wall.
- **Performance counts** (36 views): draw calls median 218 / max 669 against the old ODM import's 1 458 / 2 294;
  triangles 36.9 k / 119.9 k against 89.5 k / 249.9 k; median 4 sectors drawn; map load 1.69 s against 3.46 s.
- **Scenarios:** doors_exits (24 steps), shops (26: two walk-in shops by real clicks) and scripted (45): all pass.
  Five half steps: four probed and climbed; the fifth lies inside a stair block.
- **Converter:** `city/structure.py` `street_box_lt` (opt-in; Lich Lab and Sturmford `--plan --scratch`
  byte-identical, `work/proof/`).
- **Map-local:** glass only on translucent panes; wall, floor and ceiling splits at the walls standing on them (two
  sky holes from review v01 fixed); a cached `crossing_portals` (the shared one took over 30 min here; proposed for
  `rooms.py`).
- **Engine:** none.
- **Open:** the grey night fog (MM9's WeatherMan switches to black fog at night); static light without time of day;
  the well's bonus; Perception hints and breakable windows; 1 371 roof-line portals from the diagonal streets (no
  measured cost).
- **Street lights (2026-10-31, late)**: `bright_scale_lights` (59 of 160 lights x 0.6-0.8), barely visible;
  doors_exits, shops, scripted pass. By its DAT the sky would be grey by day (`sky_fog`, not set).
- **Fog by the daylight (2026-11-01)**: rebuilt with scene fog `follow_daylight` (BLV byte-identical); noon
  unchanged, 23:30 still MM9's black night fog; doors_exits, shops, scripted pass.

## Thronheim City

Wave 1 of the cities rollout ([CITIES_ROLLOUT.md](../CITIES_ROLLOUT.md)), one agent. Record:
[`level_generation/projects/mm9r_thronheimcity/README.md`](../../../level_generation/projects/mm9r_thronheimcity/README.md);
props: [`level_generation/props/mm9_thronheimcity_claude/`](../../../level_generation/props/mm9_thronheimcity_claude/README.md).

- **Verdict: works as a BLV.** 19 561 faces, 31 192 vertices (48 % of the 16-bit range), 63 sectors, 974 portal faces
  (890 roof-line rectangles, 51 street cuts, 15 door portals, 8 leaf portals, 10 glass), faces per sector max 1 460,
  median 142; 0 outlines (painted minimap), sky open with time of day, 48 lights, 40 doors, 43 people (+1 hidden guard),
  307 decorations (props project: 25 new models, 63 reused, rows 2516-2551), 1 chest, 2 exits, 3 starts.
- **Counts** (32 views): draw calls median 206 / max 381 against the old ODM's 1 069 / 1 576; triangles 26.0 k / 51.3 k
  against 86.2 k / 157.7 k; 4 sectors drawn (max 8); map load 2.43 s against 2.93 s (median of 3).
- **Scenarios**: doors_exits 22 steps, shops 31, chests 7, scripted 38: all pass.
- **City settings**: roof line 1 472 LT; wide streets, so cuts up to 1 152 LT every 1 024 LT plus 3 by hand;
  `half_steps: true` (4 steps, probed). The Argument cinema's stage under the city is not built (`seed_exclude`).
- **Map-local fix**: `split_floors_at_walls` (convert.py): a sidewalk polygon running on under a house went to the
  house's sector and the street drew sky along the inn front; floors of 20 000 LT² or more are cut at the walls standing
  on them (4 880 cuts; floor under another room's air 193 141 -> 99 887 LT²). Other cities with long sidewalks may need
  the same (a candidate for the shared city hooks, opt-in).
- **Engine / converter**: none. `openyamm_indoor_source_tests` 21 / 21.
- **Open**: streets darker than the old bake (classic light); the camera cinema, voices, schedules, guard respawns,
  breakable windows and Perception hints not carried; the props' model names overlap Thjorgard City's plan (this city
  installed them first).
- **Daylight and street lights (2026-10-31, late)**: `daylight`, `fog: lithtech` (no fog at the start in MM9),
  `bright_scale_lights` (29 of 48 lights); `review/dl2_compare_<time>.jpg`; doors_exits, shops, chests, scripted
  pass.

## Arslegard City

Wave 2 of the city rollout ([CITIES_ROLLOUT.md](../CITIES_ROLLOUT.md)), one agent. Record:
[`level_generation/projects/mm9r_arslegardcity/README.md`](../../../level_generation/projects/mm9r_arslegardcity/README.md);
props: [`level_generation/props/mm9_arslegardcity_claude/`](../../../level_generation/props/mm9_arslegardcity_claude/README.md).

- **Verdict: works as a BLV.** 11 830 faces, 16 017 vertices (24 % of the 16-bit range), 63 sectors (15 walk-in
  interiors, 48 street rooms, 1 roof room), 224 portal faces (169 roof-line rectangles, 41 street cuts, 11 UserPortals,
  3 leaf portals), faces per sector max 1 998, median 26; 0 outlines (painted minimap), sky open with time of day,
  55 lights, 30 doors, 36 people + Njam, 419 decorations (props: 5 new models, 85 reused, rows 2610-2622), 0 chests
  (none in the DAT), 6 exits, 4 starts.
- **Counts** (32 views): draw calls median 212 / max 467 against the old ODM's 737 / 1 002; triangles 30.5 k / 89.5 k
  against 80.2 k / 156 k; 4 sectors drawn (max 15); indoor visibility build at most 0.9 ms; map load 1.56 s against
  5.03 s (median of 3, loaded machine).
- **Scenarios**: doors_exits 37 steps, shops 27, scripted 62: all pass.
- **Frame offset**: the DAT spans native y -34 488..-5 734 (over int16): `offset: [0, -20000, 0]`; convert.py moves
  props.json, the transition rows and the painted map's catalog bounds by it (Connecting Tunnels' route).
- **Map-local fixes (convert.py)**: (1) the air flood leaked to the border through a 32 LT Invisible.dtx strip under a
  hollow house's roof: invisible vertical strips above LT 150 are solid for the flood only; (2) **top portals over
  solid**: the shared cover broke the 45-degree streets' footprints into 1 024 thin rectangles and the visibility build
  took up to 15.6 ms per sector change; grown over cells with no air (walls, roofs, hollow houses) they are 169 and the
  build takes under 1 ms (a candidate for the shared city module, opt-in: Thronheim has 890); (3) horizontal faces of
  8 000 LT² or more cut at every wall on them, any direction (the weapon shop's ceiling showed the sky); (4) the bank's
  bars as untouchable cut-outs; (5) peaceful relations for the friendly actors (Hanndl's row 555); (6) a new row
  `mm9:transition/arslegardcity/638` for MM9's ExitTrigger3 (the chasm through the city has a sky floor; falling in
  lands in Thjorgard; the old import made no row).
- **Great Gate**: no transition row names greatgate (the skipped DAT is an unused cinema copy). Its scene lives here:
  FateMan.scr (first arrival without key 98: 46 000 xp, Hanndl's lines as status lines, then the move to the Dark
  Passageway) and WritMan.scr (key 100: 9515, 170 000 xp, Hanndl gone, the gate opens) as native Lua; tours set key 98.
- **Engine / converter**: none.
- **Hall court ramp (follow-up)**: not blocked. The one ramp rises south (LT 0 at z -12 288 to 128 at z -12 800);
  forward walks up it at its west edge, middle and east edge climb +328 (`work/probes/hall_ramp.yml`). The "two
  blocked ramps" were a probe walking east into the ramp's side wall (MM9's own). Scenarios rerun: 37 / 27 / 62 pass.
- **Open**: how a living party first reaches Arslegard (MM9: by dying; FateMan then sends it to the Dark Passageway);
  the temple's two ladders (feet 144 LT over the porch) not built (the leaning-ladder agent's); streets darker than the old bake (classic light; the lighting agent's).
- **Street lights (2026-11-01)**: `bright_scale_lights`, rebuilt: 29 of 55 kept lights x 0.6-0.8;
  `review/bs_1101_sheet.jpg`; doors_exits, shops, scripted, ladders pass.

## Drangheim City

Wave 1 of the city rollout ([CITIES_ROLLOUT.md](../CITIES_ROLLOUT.md)). Record:
[`level_generation/projects/mm9r_drangheimcity/README.md`](../../../level_generation/projects/mm9r_drangheimcity/README.md);
props: [`level_generation/props/mm9_drangheimcity_claude/README.md`](../../../level_generation/props/mm9_drangheimcity_claude/README.md).

- **Built in the review root as BLV + sky**: 11 258 faces, 16 202 vertices (25 % of 16-bit), 37 sectors (19 walk-in
  interiors), 744 portal faces, faces per sector max 5 455 (the air over the roofs, which holds the whole hill district)
  and median 55; 0 outlines (painted minimap), 33 doors, 54 BLV lights, 39 townsfolk (RUDE dialogues), 201 decorations
  (20 new models, rows 2552-2578), 3 exits, 4 starts; `half_steps: true` (7 steps; probes in the README).
- **Performance** (32 views): draw calls median 264 / max 432 against the old ODM's 644 / 779; triangles 51.7 k /
  102.9 k against 51.4 k / 97.2 k; sectors drawn 4 / 12; map load 2.37 s against 3.05 s.
- **Scenarios** (all pass): doors_exits 23 steps, shops 33, scripted 48, ladders 6, half_steps 9 (probes). No chests in
  the DAT.
- **Transitions**: wilderness <-> city and Klusos House <-> city (door and window) consistent on both sides; Drangheim
  Prison has no exit into the city (its wilderness rows untouched); Town Portal: row 9005 names the BLV (no MM9 Town
  Portal destination table yet).
- **No converter or engine change.** Map-local (`convert.py`, `terrain.py`): the air under the terrain taken out of the
  flood (the void outside the walls ran under the whole hill), the town hall's door as a rect portal (MM9's portal sat in
  the arched recess and leaked), interior faces of thin walls given back from the open air (49 moved, 45 split at an
  interior's ceiling line: the blacksmith's chimney, the tower's wall over the town hall), the burning logs lifted onto
  their hearths, Klusos House's window exit grown onto the walkway, Sigmund and Guaire on peasant relations.
- **Open**: the leaning TowerLadder1 to the north wall's walkway does not climb natively (the climber goes straight up and
  stops under the walkway): a party arriving through Klusos House's window gets off the walkway only back through the
  window. Hrolf and Alfrigg's quarrel, Perception hints, drinkable barrels not carried. `street_box_lt` does not fit
  this city (the low town runs up the hill with no wall between them).
- **Street lights, fog by the daylight (2026-11-01)**: `bright_scale_lights`, rebuilt: 47 of 54 kept lights
  x 0.3-0.8 (median 0.6); scene fog `follow_daylight`; `review/bs_1101_sheet.jpg`; all five scenarios pass.

## Frosgard City

Wave 2 of the cities rollout ([CITIES_ROLLOUT.md](../CITIES_ROLLOUT.md)), one agent. Record:
[`level_generation/projects/mm9r_frosgardcity/README.md`](../../../level_generation/projects/mm9r_frosgardcity/README.md);
props: [`level_generation/props/mm9_frosgardcity_claude/`](../../../level_generation/props/mm9_frosgardcity_claude/README.md).

- **Verdict: works as a BLV.** 13 986 faces, 15 352 vertices (23 % of the 16-bit range), 12 sectors (11 walk-in
  interiors and one open-air sector), 12 portal faces, faces per sector max 11 787 (the open air), median 232; painted
  minimap, sky open with time of day, 38 lights, 72 movers (doors, the bank's hatch, 37 ice floes), 50 people, 177
  decorations (props: 8 new models, 63 reused, rows 2623-2636), no chests (none in MM9), 1 exit, 4 starts.
- **A different city:** free-standing houses on one snow field, no wall and no corridor streets: the street-cut pass
  found nothing to divide, so the open air stays one room (`extra_portals` off, map-local). MM9's sky shell runs past
  the int16 frame over the bay (31 232 LT): the voxel pass covers a box round the town and harbour only, sealed at its
  faces; the mountains and far bay are scenery of the open-air room, clipped to 12 700 LT; the sea bed under the
  ocean is dropped. The ocean is a solid wading surface (liquid shader).
- **Counts** (28 views): draw calls median 157 / max 289 against the old ODM's 591 / 861; triangles 41.9 k / 111.2 k
  against 48.1 k / 112.3 k (one open-air sector); 2 sectors drawn (max 6); map load median 3.97 s against 5.59 s (best
  2.33 against 2.67; a loaded machine).
- **Scenarios:** doors_exits 22 steps, shops 26, scripted 55 (the ice quest's barrel and floes, the maypole, the
  dockmaster, Tryggva's reward, the battle's start): all pass. Yanmir's Fort's four scenarios pass after its change.
- **Shared tables, found on the first tour:** three `transport_routes.txt` boat rows into Frosgard City named
  `frosgardcity.odm`, which the install removes: every game start on the review root failed ("destination map
  reference is unresolved") for a few minutes until `transport.py` rewrote them to the BLV (map-local, under the
  review tables lock, rerun after each install). Any later city that is a boat destination needs the same.
- **Other project:** Yanmir's Fort's fall now goes to `frosgardcity.blv` at FallingStart as built (its `convert.py`
  `city_arrival`, rebuilt).
- **Converter / engine:** none.
- **Open:** MM9's 1-2 000 LT grey fog (the fog session); the bay is waded, not swum; cinemas, pledges, Tamur joining
  the party, Perception hints and snowfall not carried.
- **Daylight, fog, sky, street lights (2026-10-31, late)**: `daylight`, `fog: lithtech`, `sky_fog` (the sky in the
  fog colour, as MM9: new engine opt-in, scene fog `sky`), `bright_scale_lights` (26 of 38); `review/dl2_compare_<time>.jpg`;
  doors_exits, shops, scripted pass. Open: the grey sky stays light at night (MM9 does not change with the hour).
- **Night fog and tour deaths (2026-11-01)**: scene fog `follow_daylight` (fog and fogged sky (27, 29, 39) at 23:30,
  noon unchanged; BLV byte-identical); `review/fog_night_1101_compare.jpg`; doors_exits, shops, scripted pass. The
  death video of long tours was the tour's clock, fixed in the engine (section "2026-11-01" below).

## Guberland City

Wave 2 of the cities rollout ([CITIES_ROLLOUT.md](../CITIES_ROLLOUT.md)), one agent. Record:
[`level_generation/projects/mm9r_guberlandcity/README.md`](../../../level_generation/projects/mm9r_guberlandcity/README.md);
props: [`level_generation/props/mm9_guberlandcity_claude/`](../../../level_generation/props/mm9_guberlandcity_claude/README.md).

- **Verdict: works as a BLV.** 15 326 faces, 19 823 vertices (30 % of the 16-bit range), 49 sectors (23 walk-in
  interiors, 21 street rooms, 5 roof rooms), 631 portal faces (540 roof-line rectangles, 29 street cuts, 30 glass, 32
  doorways), faces per sector max 1 632, median 138; painted minimap, sky open with time of day, 51 lights, 76 movers,
  46 people, 258 decorations (props: 5 new models, 87 reused, rows 2637-2643), no chests (none in MM9), 1 exit, 2
  starts.
- **The city:** four walled quarters round a central cross, joined by eight sliding gates (MM9's UserPortals already
  separate the five districts); roof line 192 LT; no hand cuts. A 0.25 s poll opens a gate when the party walks into
  MM9's trigger box.
- **Map-local fixes:** Thjorgard's and Thronheim's (glass on 0x8 panes, `split_at_walls` with the 16 LT foot rule,
  the cached crossing test, string DOORS keys, peaceful relations); **new:** sloped ceilings cut at the partitions with
  two corners on their plane (the tavern's side rooms share one lean-to ceiling: a sky triangle in review v02, fixed);
  the bank's bars as a cut-out (The Arena); the fish tank as see-through Water115 at 0.7; an invisible step onto the
  tavern's 82-unit stage (probed: +82).
- **Counts** (38 views): draw calls median 162 / max 278 against the old ODM's 816 / 1 050; triangles 22.2 k / 80.6 k
  against 65.8 k / 148.5 k; 6 sectors drawn (max 14); map load median 1.27 s against 1.87 s.
- **Scenarios:** doors_exits 23 steps (the bank door, a facade door, Gate6 by walking up to it, the exit), shops 26,
  scripted 73 (location, shop hours, altar, letter, Markel's clans and reward, the bank orb, the keg, the apothecary's
  potion and Nurtigan's door): all pass.
- **Converter / engine:** none.
- **Open:** static light by time of day (the daylight agent); facade windows draw black where MM9 shows faint shards;
  the Guberland Players' show, its voices and the actors' walks not carried; the corner towers' tops behind MM9's sky
  partitions show the sky, as MM9's sky faces do.
- **Daylight and street lights (2026-10-31, late)**: `daylight`, `fog: lithtech` (no fog in MM9),
  `bright_scale_lights` (37 of 51); noon streets as bright as the old import; `review/dl2_compare_<time>.jpg`;
  doors_exits, shops, scripted pass.

## 2026-10-31 late: city daylight rollout, street lights (BrightScale), the sky in fog

One agent. Record: CITY_PLAYBOOK.md "Daylight and fog" and "Street lights and BrightScale",
devdocs/INDOOR_FOG.md "The sky in fog", `level_generation/projects/mm9r_common/daylight_fog_20261031/`.

- **Rollout**: Frosgard, Thronheim, Guberland City rebuilt with `daylight` and `fog: lithtech`; Sturmford and
  Thjorgard rebuilt for the street lights. Drangheim and Arslegard (the ladder agent's) not touched: they should add
  `bright_scale_lights: true`.
- **BrightScale** is MM9's lightmap-bake strength of a Light (Processor.exe reads it, LithTech LightMapMaker
  colour x BrightScale; the runtime never does); MM9's own lightmaps rise in proportion to it
  (`brightscale_lightmaps.txt`). Converter opt-in `map: {bright_scale_lights: true}` (Lich Lab scratch build
  byte-identical with it off). **Dungeons not rebuilt**: 12 on the shared writer would change 1 342 of 1 377 kept
  lights (median factor 0.30-0.75 per map; table in CITY_PLAYBOOK); the other 12 already apply BrightScale themselves
  and must not opt in. Klusos House's real shots matched full colour, so compare before adopting.
- **Sky in fog**: MM9 fogs the sky box from the fog state's SkyFogNearZ whenever fog is on (the `SkyFog` flag is
  read by nothing; the client copies SkyFogNearZ into SkyFogFarZ); the box is deeper than every such value, so the sky
  is wholly the fog colour (Frosgard always; Thjorgard and Drangheim by day; Thronheim only in scripted weather).
  Engine opt-in: scene fog `sky` (0..1, day and night), the open sky lerped to the fog colour
  (`SkyInputs::fogCover`); converter opt-in `map: {sky_fog: true}`; set for Frosgard only.
- **Found on the way**: MM9's world fog is range fog (distance from the eye) unless `TableFog` is on; the view-depth
  function the lithtech model copies is the sky's (INDOOR_FOG.md "Correction"; not changed). Long screenshot tours on
  the city BLVs end in a death video (8+ views); `compare_tour.py` runs one view per game run.
- **Scenarios after the rebuilds, all pass**: Frosgard doors_exits / shops / scripted; Thronheim doors_exits / shops /
  chests / scripted; Guberland doors_exits / shops / scripted; Sturmford doors_exits / shops / chests / scripted;
  Thjorgard doors_exits / shops / scripted.
- **Engine build**: unit tests 2 442 / 2 442; `openyamm_runtime_tests` 54 / 55 (braziers, predates); `indoor`
  regression suite 174 / 174; MM6 6d02, MM7 7d06, MM8 d06, MM8 out01 (outdoor sky), Lich Lab, Anskram Keep and
  Thjorgard City old binary vs new: only moving creatures, flames, status text and grass differ
  (`daylight_fog_20261031/nochange_skyfog_mm6_mm8_out01_diff.jpg`).

## 2026-11-01: tour deaths, last BrightScale rebuilds, night fog by the daylight

One agent. Records: CITY_PLAYBOOK.md "Daylight and fog" and "Street lights and BrightScale", devdocs/INDOOR_FOG.md
"Fog by the daylight", tools/RUN_GAME.md (tours), the Frosgard City README's open items.

- **Death video of long city tours: cause.** A repro tour on Frosgard City (`hp show`, `time` per shot) and gdb on the
  cutscene screen: `processPendingPartyDefeat`, the party's one member Dead at full HP, set by
  `Party::updateDaysWithoutRest` (MM6-MM8's days-without-rest rule) under `setDebugClockMinute`. The indoor renderer
  runs its own simulation step (clock, timers, face triggers, MM9 positioned transitions) and kept running it while the
  tour held gameplay, so the clock crept past each shot's `time:` and every repeated time jumped a day; four days
  without rest killed the party. The ODM renderer has no such step. Not a city fault, not reachable by a player.
- **Fix (engine, debug path; MM6-MM8 play unchanged)**: `IndoorRenderer::setWorldTimeHeld`, set by the app while a
  screenshot tour is active: the renderer takes the turn-based branch (mechanisms only), so doors and lifts still move;
  a tour shot's `time:` clears the days without rest before the clock jump. Proof: Frosgard `dl2` (16 shots) and a
  32-shot tour (8 views x 06:30/12:00/19:30/23:30) and Thronheim `dl2` (16) end alive, no cutscene; the old binary
  plays the death video on all three (Thronheim's clock at day 10 instead of day 1).
- **Drangheim and Arslegard City**: `bright_scale_lights`, rebuilt (47 of 54 and 29 of 55 lights); scenarios 5 / 5
  and 4 / 4 pass; noon and 23:30 views look right (`review/bs_1101_sheet.jpg`).
- **Fog by the daylight**: engine opt-in scene fog `follow_daylight` (`indoorDaylightFogScale`: per channel the open
  air's light over its noon light); converter (`city/hooks.py`, under the lock) writes it where `city: {daylight:
  true}` and fog are both on: Thjorgard, Drangheim, Frosgard rebuilt (Thjorgard's and Frosgard's BLVs byte-identical).
  Frosgard at 23:30: fog and sky (27, 29, 39) instead of 127; noon identical. Lich Lab `--plan --scratch` before and
  after: identical (only the scratch path in build.log).
- **No change elsewhere**: MM6 6d02, MM7 7d06, MM8 d06, MM8 out01, Lich Lab, Anskram Keep, old binary vs new: only
  moving creatures, flames, status text and grass differ (7d06 and Lich Lab pixel-identical;
  `mm9r_frosgardcity/review/nochange_1101_mm6_mm8_dungeons.jpg`).
- **Engine build**: unit tests 2 444 / 2 444; `openyamm_runtime_tests` 54 / 55 (braziers, predates); `indoor`
  regression suite 174 / 174. The editor target fails to link on `IndoorSectorFaceGrid` (its source list lacks that
  file; not from this change, EditorDocument.cpp compiles).

## 2026-11-01 evening: street performance (merged roof-line portals, merged face draws)

One session, continuing [HANDOFF_20261101_CITY_PERF.md](../HANDOFF_20261101_CITY_PERF.md) (both agents of the
afternoon were stopped mid-task). Records: [CITY_STREET_COST.md](../CITY_STREET_COST.md) "Proposal 2: result" and
"Result of proposal 3", [INDOOR_FACE_DRAW_GROUPS.md](../../INDOOR_FACE_DRAW_GROUPS.md), CITY_PLAYBOOK "The open air",
each city's README.

- **Merged roof-line portals, all six roof-line cities rebuilt** with the final converter (the afternoon builds
  predated its sky-face rule; Arslegard's then had 405 top portals and 460 portal faces). Portal faces: Thjorgard
  1 470 -> 237, Thronheim 974 -> 299, Drangheim 744 -> 206, Guberland 631 -> 271, Sturmford 343 -> 215, Arslegard
  224 -> 213. Max portal link tests per visibility build: Thjorgard 148 544 -> 3 066, Drangheim 96 913 -> 9 195,
  Thronheim 55 721 -> 3 378; the 256-node cap is hit nowhere (4 poses before). Every city's scenarios pass (23 / 23).
  Before/after tours at 12:00 compared in 16 x 16 blocks: no hole. Arslegard's library and Njam lane no longer reach
  the roof air: the library was lit as open to the sky before and is darker now (its ceiling is solid). Frosgard has
  no roof line and was not rebuilt. Lich Lab `--plan --scratch`: byte-identical.
- **Merged world-face draws** (engine, every BLV): one draw per texture and draw state over the visible sectors,
  sectors and daylight per vertex, batch order kept only between nearly parallel overlapping faces. Thjorgard street
  world draws 159-431 -> 108-157, frame draws 290-670 -> 240-390; MM6-MM8 rooms draw once per texture. Pictures: A/B/A
  shots in one run (8 maps, 62 poses: 6d02, 7d06, d06, d12, Anskram Keep, Lich Lab, Thjorgard noon and night): 30
  identical, the rest single pixels along lines where two faces meet. Unit tests 2 453 / 2 453, runtime 54 / 55
  (braziers, predates), `indoor` suite 174 / 174.
- **Not done:** FPS on the user's machine (single-session run); the editor link failure above is unchanged.
