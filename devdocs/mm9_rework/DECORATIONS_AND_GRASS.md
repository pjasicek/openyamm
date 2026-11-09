# MM9 decorations and outdoor-BLV grass (task file)

Task from the user, 2026-11-04 (after the outdoor BLVs, OUTDOOR_BLV_ALL.md): replace the low-quality MM9 decorations
(new models and textures, or new textures only); trees from our own or MM6-MM8's 3D trees; most small props (shelf
items, wall shields) likely need only new textures (Codex imagegen); and grass decorations (the outdoor grass shader's
tufts) as an option on the outdoor BLV maps, like MM6-MM8's grassy fields. This file is the durable state.

## Rules

- AGENTS.md/CLAUDE.md. One heavy job at a time: never a game build beside a map conversion (out of memory,
  2026-11-04). Models are installed with `tools/install_model.py` from their source GLB, never edited in assets_dev.
- Codex image work: `codex exec` workers (tex.py's worker pattern), at most 16 parallel, a pilot reviewed before the
  bulk, at most two review rounds per texture (memory: codex batch cost controls).

## What exists (2026-11-04)

- **487 installed MM9 decoration models** (`assets_source/worlds/mm9/models/mm9_deco_*.glb`), built per map by 32 props
  projects (`level_generation/props/mm9_<map>_claude/`, route: the isle's and Anskram Keep's READMEs): MM9's own ABC
  meshes with their skins enlarged x4 (Real-ESRGAN or Lanczos). Their READMEs call this a stopgap ("the Codex x4 pass
  replaces them"); MM9_DUNGEONS_HANDOFF.md: "the props' skins are a separate batch". Not done yet.
- **About 500 distinct skins**, nearly all **128 x 128 natively** (416; 49 at 64, 29 at 256): the low quality is the
  textures, not the meshes (low-poly furniture, mostly fine).
- **The new outdoor regions have no props placed** (only the isle has its ODM pilot's props.json). Their DATs hold
  about 2 200 prop placements of 187 models: trees (tree04 251, tree02 217, tree06 89, tree05 72, snow trees 28, dead
  trees, bushes, flowers), stones and debris (~190), furniture and clutter, and posed figures (`Prop` objects with
  character models and Propanim.scr: peasants, clan soldiers, thralls, dragonflies, imps; a few hundred).
- Grass: MM6-MM8 outdoor maps scatter tufts at load (`TerrainDecorationData::scatterTerrainDecorations` from the ODM's
  tiles and terrain weights; rank quadtree LOD, level_generation/terrain/GRASS_LOD.md, MEADOW.md). Nothing for BLVs.

## Plan

1. **Grass on outdoor BLVs (engine).** Scatter tufts over the terrain faces where the BLV terrain's weights
   (terrain_blend.py's weights png) carry a grass layer; feed the existing placement/LOD/renderer; scene opt-in on
   the terrain block, the existing grass/terrain-decoration settings apply. MM6-MM8 unchanged.
2. **Skins x4 with Codex (all ~500).** A small orchestrator (`level_generation/props/mm9_skins_x4/`): per skin a
   Codex worker redraws the native at 4x keeping its UV layout exactly (prompt from the prop's name and material),
   then checks: low-pass match to the native (layout kept), alpha from the native, size. Swap into the source GLBs
   and reinstall. Pilot of about 12 representative skins first, sheet to the user, then the rest.
3. **Props for the new regions.** A shared outdoor-BLV props route: place the DAT props (props.json per region),
   reusing installed `mm9_deco_*` models (many props recur across maps), trees/bushes/flowers swapped to MM6-MM8 3D
   decorations (`decoration_swaps`, as the isle does), new conversions only for missing props (then they join step 2).
4. **Remodel only where the mesh is the problem** (judged from the sheets after step 2: e.g. hero props); trees are
   never MM9's (step 3).

## Progress log

- 2026-11-04: inventory above; plan written. Starting the skin pilot (step 2) and the grass engine work (step 1).
- 2026-11-04 10:30: skins: `level_generation/props/mm9_skins_x4/skins.py` (inventory: **323 distinct skins** by content;
  gen, finish, sheet). Pilot of 14 (chair, crate, barrel, fruit basket, jug, bookcase, cabinet, cutlery, Kira's
  shield, wall lantern, cookpot, shelf items, weapons cabinet, ship planks): all usable, 4 after one retry with a
  note (purple glass and lilac cloth read as cut-outs, a sooty pot lightened, chair boards moved). Prompt now says
  purple/pink regions are real colours and dark regions stay dark; `finish` replaces any magenta speck inside an
  opaque region with the native's colour. Sheets: mm9_skins_x4/work/pilot_sheet_{a,b,v2}.png. Bulk (309) running,
  12 workers. Next: review the bulk sheets, then swap the skins into the source GLBs and reinstall.
- Grass engine work in progress: scene `terrain: {grass: <decoration file path>}` parsed (IndoorTerrain::grass),
  `loadTerrainDecorationConfigFile`; next the surface scatter, IndoorRenderer drawing, terrain_blend.py opt-in.
- 2026-11-04 11:30: **grass done**: scene `terrain: {grass}` (default New Sorpigal's plants), surface scatter (unit
  test), IndoorRenderer drawing (devdocs/INDOOR_OPEN_SKY.md "Terrain"); all 12 regions opted in via terrain_blend.py.
  User saw the Sturmford view and kept the density (grass_patches counted at 0.8: 603 000 tufts there; measured MM6-MM8
  maps 97 000-150 000; ~5 % fps).
- Skins: all 323 map onto 490 embedded `<name>_basecolor` images of the 487 models (`work/models_by_skin.json`);
  unmatched: the CC0 flame flipbooks and orbs (kept) and five second skins `*_1` (erccsitting, suitofarmor02aged,
  svensitting, thjoradbin, tree04) to add later. `skins.py install [names] [--dry-run]` swaps them into copies of the
  source GLBs (work/glb/, verified byte-exact) and runs tools/install_model.py --engine; finish now bleeds colour under
  cut-out texels. Installing cooks every model: never beside a build or conversion; afterwards the review root needs
  the new files linked (review_root.py).
- Region props (step 3): of ~1 450 Prop placements in the 11 new regions, 947 (78 models) have an installed model;
  missing 501 (57 models): stone 90, stonedebris01 84, arrow 54, clansoldier 52 (posed), snow trees 28, lantern1 18,
  longsword 17, flowers, bushes, coat rack, open scroll, dead trees, goose, wine bottles, banners, hay bales ...
- 2026-11-04 12:30: skins reviewed: all 309 bulk skins generated (none failed); the 47 the checks flagged looked at on
  sheets (work/flag_*.png, soft_alpha.png): the layout check misreads magenta-heavy and low-contrast skins. Fixes:
  `finish` keeps the native's partial alpha (22 skins have glass, lamp glow, a ghost) instead of 0/255; the ice crate
  redone (v2, note: ice not wood). **Kept at their current upscale** (`KEEP_CURRENT`): sorcererstatue, icebanshee,
  goblet, jar, beaker01 (mostly translucent; the redraw lost the material). 318 accepted; installing.
- Region props plan (step 3): one shared project `level_generation/props/mm9_outdoor_regions_claude/` on the Drangheim
  City route (its scripts: props_table.py owners/reuse, convert_all.py, build.py, finish.py, tables.py rows,
  placements.py), writing each region's `props.json` (outdoor_blv.py `outdoor: {props}`); trees, bushes, flowers and
  snow trees swapped to MM6-MM8 3D decorations (`decoration_swaps`); new models' skins through skins.py.
- 2026-11-04 12:50: **skins installed**: 468 models (`skins.py install`, work/install.log, 0 failures); both review
  roots refreshed (review_root.refresh with ASSETS/OWNED pointed at assets_dev and isleofashes_blv_root). Not yet seen
  in game: since 09:45 every map (MM6 too) crashes at load with `free(): invalid pointer`, the binary built by another
  session; that session's tests/CMakeLists.txt also lists a not-yet-existing AiArenaTests.cpp, so configure fails.
  Waiting for it; then rebuild (touch changed headers: build race) and check props in game (Anskram Keep start).
- 2026-11-04 13:05: the other session's build settled (AiArenaTests.cpp appeared); rebuilt, the crash is gone.
  In game (Anskram Keep, tour in the session scratch): bookcase, crates, barrels, weapons cabinet crisp; a pale curved
  band across the weapons cabinet doors is not in the skin (check against the old skin: model shading or room light).
- 2026-11-04 13:20: the cabinet band is not in the skin (model shading); skins step done. Region props started:
  `level_generation/props/mm9_outdoor_regions_claude/scripts/inventory.py` matches every region Prop/CandleProp by
  (model, skin) against the 29 readable props_table.py MODELS tables (391 entries; Arslegard's and Dark Passageway's
  use expressions and are not read): **1 505 placements, 746 with their exact installed model**, 759 without:
  vegetation ~460 (tree02 217, tree06 89, tree05 72, snowtree1/2 28, deadtree3/4 11, bush01/02 13, flowers01/03 20) ->
  MM6-MM8 3D trees by look (MM9 tree05/06 are spruces: the isle maps them to MM8 tree16/tree28; MM7 winter trees
  `level_generation/decorations/mm7_3d/trees_seasonal/` for snow trees; MM6 broadleaf sheet
  `mm6_new_sorpigal_3d/review_ingame/all_trees_species.png`), stones 90 (Bootcamp's coloured stones game included),
  arrows 54, posed clan soldiers 52, lanterns 18, weapons ~30, a tail of single props.
  Next: tree mapping sheet (MM9 species vs candidates), placements.py writing props.json per region for the 746 +
  swapped trees, then the remaining new models on the Drangheim route.
- 2026-11-04 13:45: **big props at 8x** (user: "if that makes sense"): skins with a native of 128 or less whose largest
  prop is about 150 units or more (work/x8_names.json: 171 skins: statues, big trees, beds, tapestries, bookcases,
  cabinets, carts, weapon racks, tables) re-finished at 8x from the same 1254-pixel generations (`finish --scale 8`;
  real detail, no enlargement), 256 models reinstalled, both roots relinked; checked in game (Anskram bookcase,
  crate). Note: work/x4/ now holds both 4x and 8x results (metrics.json records each skin's scale).

- 2026-11-04 12:45: **stat barrels MM6 style** (user: only MM9's real stat barrels drinkable, with the liquid; the
  small shelf barrels in Thjorgard City could be drunk from). Cause: the props tables gave MM9 rows the hints
  "barrel", "keg", "bucket", "cauldron", "campfire", which the engine reads as MMerge's interactive decorations,
  so every barrel, keg and bucket was a stat barrel without a visible liquid (and hearth logs gave food).
  `level_generation/projects/mm9r_common/stat_barrels.py`: neutral hints on those 18 rows (also in the 15 props
  projects' HINTS), rows `mm9_statbarrel` (122.9) and `mm9_statbarrel_x100` (81.9) on MM6's barrel with bigbarel's
  liquid overlays (worlds/mm9/models/decoration_overlays.yml); dungeon/content.py places class `Barrel` props on them.
  The 12 remade maps with stat barrels (46) reconverted; the outdoor regions' 7 (Bootcamp, Mountain Pass, Sturmford)
  follow with step 3's props (same content.props path); Wizard's Lab's 2 have no remade map.
  Checked in game (Anskram Keep: orange and purple liquid, the MM9 barrels beside them plain). The reconversion
  also needed dungeon/build.py actor_barriers to work on maps whose alias table lacks MM9's invisible helper texture
  (Connecting Tunnels): it falls back to INVIZVJN7N.

- 2026-11-04 13:15: **opaque skins with a shine mask** (user: Thjorgard City's gold suit of armour drew magenta and
  flat yellow). MM9 keeps a shine mask in the alpha of some skins drawn by OPAQUE materials; skins.py's reference
  showed those plates as magenta cut-outs and the redraw kept them. `opaque_skin()` now treats a skin whose
  materials are all OPAQUE as fully opaque (reference and finish). Redrawn (v2) and reinstalled (10 models):
  suitofarmor02 (also suitofarmor01gold), capstone, machinepartwhole, machinepartbroken, bonepile, terrorlight1,
  coffinfancy, chandelier; goblet and sorcererstatue stay KEEP_CURRENT. Checked in game at the user's pose.

- 2026-11-04 14:30: **night lamps** (user: Thjorgard City's lamps give no light, a wall lit by nothing). The lit
  wall: a house's room lights (Light158/162) baked through its outer wall (static lights are angle-free) -> scene
  `static_lights: {sides: front}` (devdocs/INDOOR_OPEN_SKY.md "Static lights"), written for every MM9 map; all 42
  reconverted. The lamps: Thjorgard, Thronheim and Arslegard City's lamps have no MM9 Light (MM9 lit them with the
  CandleProp's dynamic light only, the warm spot around the lantern in the user's MM9 screenshot) -> a light at
  each flame (content.py lamp_light). Lamp glass: skins.py's reference painted every texel under half alpha
  magenta, so the glass lost its colour (lamppost1's frosted panes, lantern2's blue and yellow stained glass):
  now only alpha < 16 is magenta; lamppost1, lamppost4, lantern2, lanternwall1, oillamp, shelfitem05 redrawn (v3).

- 2026-11-04 15:20: all 42 MM9 maps reconverted (static_lights, lamp lights; 0 failures). Glass skins (v3) and
  **lamp halos** installed (user: "if it doesnt hinder performance ... sure"): `level_generation/props/
  mm9_lamp_halos_claude/` adds the MM8 lantern's additive flickering Halo card (turned about its own centre) on
  lamppost1-4, lantern2 and lanternwall1; one quad per lamp. Checked in game at the user's Thjorgard pose, 01:15 and
  10:00.

- 2026-11-04 15:45: **second skins (step 2 done)**: skins.py keyed each skin's images by its props' names, so a
  prop's second skin (`<prop>_1`) kept its old upscale and some main images took another skin (the aged suit of
  armour's body its halberd, Krohn's and the skeleton statue their second skins, tree02's trunk its leaves). Images
  are now keyed by the native files' stems (`skin_stems`, `skin_models`; models_by_skin.json retired); 8 models
  reinstalled, 0 of 468 models differ from the mapping. The five `*_1` skins are copies of accepted skins (cup1,
  chair, minecart_1, suitofarmor02_1, tree02_1): nothing new to draw.
- User: posed figures wait until the other session's NPC work is accepted (no posed Props in the region props).

- 2026-11-04 16:30: **region props (step 3)**: `level_generation/props/mm9_outdoor_regions_claude/` (README):
  placements.py writes each region's props.json (overrides `outdoor: {props}`): 1 143 placements in the first pass
  (matched props fitted to the old bakes, median 0.5-0.65 units; vegetation as MM6-MM8 models at MM9's heights,
  vegetation.py, review/tree_candidates.png); 59 new rows (rows.py). 30 missing props built on Thjorgard City's route
  plus 10 tilted variants (arrows and swords stuck in the ground, the windmill, Afterworld's axes; pitch sign checked
  against the old bakes), 23 new skins redrawn (skins.py); posed figures left out (user). Engine/converter fixes on
  the way: outdoor_blv.bind_indoor_decorations rebuilds the isle root's owned manifest from assets_dev (it had
  forked: no stat barrels there), content.flame_offset reads assets_dev's manifest too, skins.py inventory keeps
  existing names, CacheOnly objects never placed.
  Seen in game (Thjorgard, Sturmford): MM8's pines and MM7's hemlock read lime and flat under the open-air BLV's
  model light (one uniform level, no sun direction), as the isle found; MM6's 6tree18 reads better (teal). To raise
  with the user: an engine pass for sunlit foliage on open-air BLVs, or other species.

- 2026-11-04 18:15: **region props done** (second pass): 40 new models installed with their redrawn skins; 1 361
  placements in the eleven regions (Afterworld's arrows, swords and axes at their tilts, fit 0.55); all regions
  reconverted. Left out: posed figures (the NPC work), two invisible candles, Barrel02 (not shipped).
  **Open-air model light** (user chose the engine fix): decorations and creatures in sectors open to the sky take
  the daylight's sun by direction (N.L, leaf translucency) on the ambient share of the room light, at exposure 1 like
  the faces (the decorations' 1.8 exposure made sunlit greens lime): the pines read olive and shaded
  (devdocs/INDOOR_OPEN_SKY.md "Daylight"). Unit tests pass (daylight, static lights).
- 2026-11-07: **New Sorpigal's meadow on the regions** (user: "the settings New Sorpigal uses, not what is there now
  (only the small bushes)"). Before, the BLV grass was the first rule's tufts only (no meadow field, verges,
  undergrowth, bushes or far colour), and its mats measured 0.57-0.87 of the ground's brightness under them
  (New Sorpigal's: 1.06), so the short clumps read as rows of dark little bushes. Now
  `scatterTerrainDecorationsOnSurface` grows the whole library (devdocs/INDOOR_OPEN_SKY.md "Terrain"), the terrain
  takes the meadow field and the foliage map, and each region's file (`worlds/mm9/terrain_decorations/<stem>_blv.yml`,
  terrain_blend.py region_grass) is New Sorpigal's `oute3.yml` with the tint `mm9r_common/grass_tint.py` fits from
  grass on/off captures to New Sorpigal's ratio (`mm9r_common/grass_tints.yml`). Frosgard and Mountain Pass have no
  grassy pose (rock and snow: no grass), their files keep New Sorpigal's tint. Sturmford 343 000 tufts (603 000
  before: the seabed under the sea and the walls' clearance no longer grow grass) and 324 bushes.

## Open questions

- Posed figures (`Prop` with character models, Propanim.scr): default keep MM9's model with x4 skins, as the cities'
  posed RUDE people; the user may prefer otherwise.
- 2026-11-07: the light/dark diagonals across MM9 prop panels (Klusos House's star cabinet; the "pale curved band"
  on the weapons cabinet above) were scrambled normals in every `mm9_deco_*` build: `blib.import_raw` kept the glTF
  import's custom normals through its bmesh round trip. Fixed in blib, and all 569 installed models plus
  `mm9_bottlefloat` re-normalled in place and reinstalled (`mm9_isleofashes_claude/scripts/renormal.py`, its README
  "Scrambled normals repaired"); skins and everything else unchanged. Checked in game in Klusos House and Anskram Keep.
