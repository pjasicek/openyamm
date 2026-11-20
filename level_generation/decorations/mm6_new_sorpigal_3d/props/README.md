# MM6 props — New Sorpigal (2026-10-08) and the later campfire, burning rock, blue flag and skull pile

Static 3D replacements for the remaining New Sorpigal decorations (flowers and the ship are separate). No paid
generation: procedural Blender modelling traced from the native sprites, Poly Haven CC0 scans and procedural
textures. Rebuild everything (about 70 s) with `./build.sh --install`.

| Model (`assets_dev/worlds/mm6/models/`) | Sprite | LOD triangles | Height | File | Animation extras |
|---|---|---|---|---|---|
| `mm6_deco_cauldron.glb` | `ckfyr00` | 1458 / 807 / 313 | 1.81 m | 4.9 MB | Fire: shared flame (`openyamm_billboard`, `openyamm_flipbook [16, 4, 30]`), unlit, BLEND; Glow unlit; Char emissive + `openyamm_pulse [0.35, 1.3]` |
| `mm6_deco_fountain.glb` | `sta1a` | 6336 / 2584 / 746 | 2.42 m statue (bounds 2.45 m: streams end 0.027 m under the base) | 2.0 MB | Water (streams): BLEND, `openyamm_uv_scroll [0, -1.3]` (flows down; glTF v runs down the streams) |
| `mm6_deco_swordstone.glb` | `swrdstn` | 4416 / 1328 / 380 / 152 | 3.37 m | 4.0 MB | — |
| `mm6_deco_swordstone_empty.glb` | `swrdstx` | 2600 / 1000 / 240 / 80 | 1.60 m | 3.6 MB | — |
| `mm6_deco_surfrock_a.glb` | `searka01` | 2364 / 940 / 284 / 106 | 1.15 m | 3.6 MB | Foam: `openyamm_uv_scroll [0.025, 0]`, BLEND |
| `mm6_deco_surfrock_b.glb` | `searkb01` | 2364 / 940 / 284 / 106 | 1.64 m | 3.7 MB | Foam: as above |
| `mm6_deco_buoy.glb` | `bouy0` | 2044 / 902 / 292 | 2.20 m | 0.8 MB | all materials `openyamm_wind 0.05` |
| `mm6_deco_flag.glb` | `fla3__01` | 116 / 54 / 15 | 4.07 m | 0.4 MB | Cloth: `openyamm_flutter 0.1`, double-sided |
| `mm6_deco_flag1.glb` | `fla1__01` | 508 / 278 / 15 | 4.07 m | 0.6 MB | Cloth: as `flag` |
| `mm6_deco_campfire.glb` | `cmpfyr00` | 746 / 206 / 144 | 1.48 m | 3.5 MB | Fire: shared flame, as the cauldron; Glow unlit; Char emissive + pulse, as the cauldron |
| `mm6_deco_burningrock.glb` | `brnrock0` | 1696 / 428 / 106 | 2.07 m | 5.5 MB | Fire: as the campfire; Lava: unlit, MASK 0.5 |
| `mm6_deco_logfire.glb` | `dec04` (dungeons) | 550 / 231 / 97 | 1.42 m | 4.0 MB | Fire: shared flame (one card, orange COLOR_0); Smoke (before Fire): `openyamm_flipbook [8, 4, 10]`, billboard, unlit, BLEND; Glow, Embers unlit; Char emissive + pulse |
| `mm6_deco_skullpile.glb` | `sklplrev` | 22480 / 6460 / 2930 / 198 | 1.90 m | 1.8 MB | — |
| `mm6_deco_pedestal.glb` | `ped06` | 1764 / 676 / 276 | 1.84 m | 1.2 MB | — |
| `mm6_deco_foodbowl.glb` | `foodbowl` | 1568 / 540 / 184 | 0.15 m (0.41 m wide) | 1.7 MB | — |
| `mm6_deco_keg.glb` | `smlbarel` | 1916 / 860 / 396 | 1.00 m | 1.2 MB | — |
| `mm6_deco_corpse04.glb` | `corpse04` | 4634 / 1925 / 712 / 228 | 1.59 m | 5.6 MB | — |
| `mm6_deco_corpse05.glb` | `corpse05` | 4739 / 1998 / 746 / 254 | 1.25 m | 5.9 MB | — |
| `mm6_deco_corpse06.glb` | `corpse06` | 4844 / 2073 / 782 / 281 | 1.21 m | 5.8 MB | — |
| `mm6_deco_corpse16.glb` | `corpse16` | 1203 / 675 / 332 / 149 | 1.25 m | 5.5 MB | — |

Contract: glTF Y-up metres, origin at the base centre on the ground, one mesh node per model with `openyamm_lods`
(`tools/link_static_model_lods.py`), COLOR_0 on every primitive (vertex occlusion on built geometry; white on scans,
whose occlusion is baked into their base colour).

- **Sword stones**: both models share the same boulder geometry and textures; the sword top is
  174 / 83 × the boulder height (3.37 / 1.61 m), so bound at their sprite heights the boulder is identical in both
  (nothing may rise above the sword top, or the model's scale changes). The sword (2026-10-09 rework, hero budget in
  `finish.py`): blade with bevelled edges and a central fuller on its own non-tiled `blade` texture (u across, v
  along; polished bevels, brushed flats, grime where it enters the stone; partly metallic so it reads bright like
  the sprite instead of mirroring the blue sky), curved quillons with knobs, a spiral leather wrap between bronze
  collars and a wheel pommel. Changing the model makes the New Sorpigal bake stale: re-bake `oute3` afterwards.
- **Fire** (2026-10-09): every fire uses the shared flame, `props_lib.flame_material()`. It is the CC0 Unity Labs
  Flame02 flipbook recoloured to the MM torch flame (`../../mm6_dungeons_3d/textures/flame02_basecolor.png`, 16 × 4
  frames of 128 × 256, a seamless 64-frame loop at 30 fps; recipe in `../../mm6_dungeons_3d/textures/FLAMES.md`).
  The cards show a frame's lower 80 % (`FLAME_FRAME_TOP`), and the flame spans about 60 % of a card's width. It
  replaces the procedural `fire` and `bonfire` atlases; those stay in `make_textures.py` so later textures keep their
  noise. The fire props' surfaces were reworked on 2026-10-09 (below, "Fire props texture rework").
- **Flag**: pennant grid 8 × 4 at LOD0; texture u runs 0 at the pole to 1 at the tip and COLOR_0.a (flutter
  weight) rises 0 → 1 along it. `build_flag.py -- flag1` builds the blue `fla1` variant from the same script (wider
  pennant laced to the pole through seven steel rings at LOD0/LOD1); the default variant rebuilds `fla3` unchanged.

### Fountain water (sta1a; 2026-10-09, revisions 2 and 3)

Revision 2 (gallery review) replaced the opaque wavy ribbons with translucent streams falling into a marble basin
with its own water surface and foam. The user's in-game review (`review/fountain_rev3/ingame_rev2_review.png`, New
Sorpigal `oute3`: the fountain stands in the map's own octagonal stone pool, BModel geometry with the engine's
water) found the basin, its water and the foam duplicating the map's pool, the streams pale lavender ribbons unlike
the pool's water, and the whole fountain small and squat. Revision 3 (current):
- **No basin, pool or foam.** The statue (geometry unchanged since revision 1) rises out of the map's water, as on
  the sprite; the streams end at `END_Z` = −0.022 m (their lowest vertex −0.027 m), just under the model's base, so
  they meet the water without a gap. The bounds grow by that much (2.447 m instead of 2.42), so at the unchanged
  binding height (266) the statue is 1.1 % smaller.
- **Streams**: eight outer streams run as a sheet down each canopy panel from under the dome, spill over the tip and
  fall in a parabola that fans out to r ≈ 0.86 m at the water (the sprite's strands reach almost its full 200-unit
  width: 0.91 m half width at this height), 0.25–0.30 m wide and 0.04–0.08 m thick; eight inner streams (0.13 m) pour
  from the stem collar between the panels and arc over the urn to r ≈ 0.62 m (LOD0/LOD1). Closed flattened tubes,
  single-sided, capped: one translucent layer per stream.
- **Water material** (`textures_water/stream_*`, `scripts/make_water_textures.py`), revision 4 after the user found
  revision 3's streams "transparent or semi-transparent": falling water is aerated, so the streams are nearly
  opaque (alpha 0.86–1.0, about 10 % thinner at the flattened tube's edges) in the native strands' blue (fount1–3
  stream pixels: median sRGB 79/101/154; texture mean 90/111/159) with narrow near-white aerated streaks and
  stretched bubbles; roughness 0.3 and full specular (a moderate wet sheen); the normal map mixes OpenMW's
  `water_nm.png` (shimmer, tiled 2 around and stretched along the fall) with the streaks' relief. Scroll
  `[0, -1.3]`: Blender v runs up a stream and the glTF export flips v, so the negative scroll moves the texture down
  (about 1.5 m/s). Revision 3 used the map pool's dark teal at alpha 0.4 and read as glass.

Sorting (checked in `engine/render/ModelRenderer.cpp` `renderStatic`): the main view is sequential, static batches
are drawn in binding/LOD order, and inside a batch every primitive in glTF order; BLEND draws test depth but do not
write it, and nothing is sorted back to front. The primitive order is Marble, Gold, Water (checked in the GLB), so
the statue is in the depth buffer before the streams. Remaining limits: streams are not sorted against each other
(same colour, so it hardly shows), and an opaque decoration or creature drawn after the fountain behind a stream
covers it. The map's pool water is drawn by the world renderer, not by this model.

Licence decision for the normal map: `water_nm.png` is GPL-3.0 (OpenMW, `assets_dev/engine/rendering/water/
source.yml`); this repository is GPL-3.0 too (`LICENSE`) and the engine already ships the file, so embedding it
(resampled and mixed into `stream_normal.png`) adds no new licence terms. Everything else is generated here.

Review: `review/fountain/compare.png`, `review/fountain/lods.png`; gallery captures of revision 3 in
`review/fountain_rev3/` (`gallery_side.png`, `gallery_model.png`, `gallery_front_above_low.png`), of revision 4 (current
water) in `review/fountain_rev4/`; revision 2 in
`review/fountain_rev2/` (with the revision-1 `before_*` captures). Re-bake `oute3` (New Sorpigal) for the outdoor
placements; the dungeon binding needs no bake.

### Fire props texture rework (cauldron, campfire, burning rock; 2026-10-09, gallery review revision 2)

The user's review: "solid colours on slabs", no roughness. The three fire props now use real CC0 Poly Haven scans
(`scripts/fetch_pbr.py` downloads the 2k sets into `textures_pbr/source/`; `scripts/make_pbr_textures.py` grades them
into `textures_pbr/<name>_{basecolor,normal,mr}.png`, mr = G roughness, B metal, from the scans' own roughness maps).
Lit textures keep the scan's luminance detail recoloured so the texture's linear mean is the native sprite's measured
colour (`textures_pbr/means.json`): poles 64, 30, 19; kettle 85, 63, 62; stones 114-129, 81-92, 89-102; logs
115, 26, 7; rock top 64, 46, 46 / lower 37, 24, 23 and its glow 82, 21, 10. The engine has only a constant
per-material emission, so every glowing surface is its own unlit material whose brightness lives in its texture and
COLOR_0. Shared flame cards and their materials are unchanged.

- **Logs** (`scripts/fire_parts.py`, both fires): split logs with a D cross-section. The flat split face, turned
  out toward the viewer, and the foot's end grain are `Glow` (unlit `fire_glow`: the `pine_bark` scan's plates as
  alligatored char, glowing red-orange with black cracks); the bark arc and top end are `Char` (lit `fire_char`:
  `bark_willow` burnt near black, normal and roughness) with a faint ember emission that flickers
  (`openyamm_pulse [0.35, 1.3]`). COLOR_0 on the glow is hottest low in the fire and cools up the logs and at their
  outer feet; the ember bed and coals are `Glow` too (the cauldron gained a small one under its logs).
- **Stones** (`fire_stone`, both fires): `rock_boulder_dry` graded to the sprites' purple-grey, box-projected per
  face (no stretching), reddened by COLOR_0 where they face the fire and low down.
- **Cauldron**: tripod poles and cap in `fire_wood` (`japanese_cedar_bark`, fibres along the poles, dark red-brown);
  kettle, bail and chain in `fire_iron` (`rust_coarse_01` greyed to dark mauve iron, metal 0.45, roughness
  0.32-0.67 from the scan, so it takes a sheen).
- **Burning rock**: `Basalt` is `lava_rock` (`dark_rock` scan, 1K, charcoal with the sprite's purple-brown cast,
  rough and porous), mapped at 1.6 tiles per metre (cylindrical round the sides, sheared so the scan's straight
  cracks wind round instead of ringing the rock; planar on the crown). The `Lava` shell (4 mm out, every LOD now,
  the same texture coordinates) is unlit and alpha-tested `lava_glow`: deep red lava pooled in that same scan's
  hollows (fine pores plus broad basins, 43 % of the texture), so the glow sits in the rock's own relief. It covers
  the upper 70 % of the rock, in noise patches toward its lower edge; COLOR_0 fades it from full on the crown to dark
  red below, and reddens the lit rock toward the crown. The old bright orange `lavaveins` crack network is retired.
- Re-bake (the installed GLBs changed): `outa2`, `outb1`, `outb2`, `outc1`, `outc2`, `outc3`, `outd1`, `outd2`,
  `outd3`, `oute1`, `oute2`, `oute3` (`tools/lighting/stale_bakes.py --check`).
- Review: gallery screenshots before and after in `review/fire_rev2/before/` and `review/fire_rev2/after/`
  (`outdoor:ckfyr00`, `outdoor:cmpfyr00`, `outdoor:brnrock0`, `dungeon:brnrock0`, `dungeon:dec04`,
  `outdoor:dec25`; `side` and `model` modes), iterations in `review/fire_rev2/iter*/`, the graded textures in
  `review/fire_rev2/textures_pbr.png` and the LODs in `review/fire_rev2/lods_all.png`.
- `dec25` (outc2) is the `cmpfyr00` art and keeps the campfire model (height 108). `dec04` (the dungeons' log-pile
  fire) now has its own model, below.
- `props_lib.pbr_material()` (new; reads `textures_pbr/`) is the only shared-code change; a rebuilt keg was
  bit-identical to its installed GLB, and the reworked campfire rebuilds bit-identical.

### Log-pile fire `dec04` (dungeons, 2026-10-09)

`scripts/build_logfire.py` -> `mm6_deco_logfire.glb`, bound in `indoor_decorations.yml` (height 116, the sprite's art
extent: 104 units wide, 116 tall). Indoor only (30 placements), so no outdoor bake depends on it.

- Shape, traced from the sprite: a low, sprawling heap 44 units tall across the full 104-unit width (built 1.52 m
  wide and scaled 0.84 across to 1.27 m): 14 chunky charred boards and beams lying flat and crossed at random tilts,
  four charred split logs lying split face up, and three bigger, lighter-brown round logs in front, the largest with
  its end toward the viewer. No stone ring. A glowing bed with coals under the fire.
- Surfaces (Revision 2, CC0 Poly Haven via `textures_pbr/`): boards and split-log bark `Char` (fire_char, lit PBR,
  faint flickering ember emission, `openyamm_pulse [0.35, 1.3]`); the boards' upward faces near the fire, the split
  faces and the front logs' end grain `Embers` (unlit logfire_embers: near-black char from the `pine_bark` scan, orange
  like the sprite's glints, 192, 96, 25, only deep in its cracks, about 5 % of the surface); front logs `Wood`
  (logfire_wood: Poly Haven `rough_wood`, CC0, graded to the sprite's mid brown 89, 66, 41); bed `Glow`. COLOR_0 is
  occlusion times a per-material tint (char darker and less red, to the sprite's near-black 18, 13, 9 to 44, 30, 17;
  the front logs shaded) and a light fire-facing reddening.
- Fire (user-approved, one flame): a single camera-facing card on the shared Flame02 (`props_lib.flame_material()`),
  centred on the heap, 1.6 m wide (the flame spans 60 % of it: about 0.95 m, 75 % of the heap's width) and rising
  from inside the heap to 93 units, the sprite's one broad fire. Only this model's card is recoloured, through their COLOR_0 (`fire_colour`: a linear
  multiplier of about 0.92, 0.29, 0.18 at the base, redder toward the tops), turning the torch-yellow core
  (254, 228, 88) into the sprite's deep orange (about 240, 110, 30) with darker red-orange edges.
- Smoke: one camera-facing card from 45 to 116 units, 1.1 m wide (the plume widens to about 60 % of the heap's width
  at the top, and its base merges into the flame), on `logfire_smoke`, a procedural flipbook made by
  `make_pbr_textures.py` (no CC0 smoke flipbook was at hand: the Unity Labs sheets in
  `../../mm6_dungeons_3d/source/unity_labs_vfx/` are flames): 8 x 4 frames of 160 x 128, a seamless 32-frame loop at
  10 fps (3.2 s) of twelve noise-textured grey puffs (130, 128, 127; plume core alpha 0.75, at most 0.8) rising,
  widening, drifting and fading. Material `Smoke`: BLEND, double-sided, unlit, `openyamm_billboard`,
  `openyamm_flipbook [8, 4, 10]`, specular 0. Blended static primitives go to the sequential transparent view in
  primitive order, and the camera-facing cards share one plane (a depth offset would not survive the billboard), so
  the Smoke primitive is placed before Fire (its material slot is moved up after the join): the smoke stays behind
  the flame where they overlap.
- Review: `review/logfire/compare.png` (native dec04a | LOD0 front | three-quarter | back), `review/logfire/lods.png`,
  gallery shots in `review/fire_rev2/logfire_single/` (final, one flame; earlier `logfire_tuned/` with three cards,
  `logfire_after/`, `logfire1`-`logfire3`), the new textures in
  `review/fire_rev2/logfire_textures.png`.
- `review.py` now feeds the flipbook emission from the base colour input (texture times COLOR_0), so review renders
  show recoloured flame cards; the other props' cards have white COLOR_0, so their renders are unchanged.
- Compromises: the flame is Flame02's tongue stretched wide (about 2.6 x) rather than a true fireball; the smoke is a
  procedural flipbook; the model's base sits up to 1.3 cm below the ground (tilted boards).

### Silver Cove, Misty Islands, Castle Ironfist and Eel Infested Waters props (2026-10-09)

- **Campfire** (`build_campfire.py`): a ring of five purple-grey stones, a teepee of seven split logs, an unlit
  ember mound with coals (textures: "Fire props texture rework" above), and three flame cards on the shared flame: a central one about as wide as the teepee and two
  lower, mirrored side ones. The billboard keeps each vertex's offset across the model, so the cards stay side by side
  facing the camera; the flame dominates at about 1.6 x the teepee's height. COLOR_0 reddens the stones and logs where they face the fire
  and the stones' lower parts.
- **Burning rock** (`build_burningrock.py`): a noise-displaced charcoal rock mound (flat underside on
  the ground) with an alpha-tested, unlit copy of its upper faces 4 mm out carrying pooled lava (rework above),
  and a narrow column of the shared flame (plus a lower mirrored card) rising about 0.8 x the rock's height above it.
  The engine has only constant per-material emission, so the glowing lava is its own unlit material.
- **Skull pile** (`build_skullpile.py`): one procedural skull per level (280 / 80 / 36 triangles): a deformed sphere
  whose grid nodes sit on the features of the non-tiling `skull` texture (front at u = 0.5), with the eye sockets
  and nasal cavity pushed in as real pits, brow ridge and cheekbones out, hollow temples and a narrower lower face.
  80 skulls of varied size (0.75–1.35) in seeded rings on a cone narrowing to a small crown, over a dark `bone`
  filler cone; most face out with a tilt, the rest lie sideways, upside down, face up/down or show the cranium's
  back. COLOR_0 is occlusion^2.2 (gaps and sockets near black) times a per-skull shade. LOD1/LOD2 use the coarser
  skulls at the same placements; LOD3 is a lumpy bone mound.
- These were added after the New Sorpigal bake; installing them does not touch the earlier props' GLBs.

### outd2 props: pedestal, food bowl, keg and impaled corpses (2026-10-09)

- **Pedestal** (`build_pedestal.py`): square stepped plinth and capital (4-segment lathes, flat shaded), an octagonal
  drum with two gold tori, an octagonal shaft with a V groove down each edge (LOD0) and a gold ring under the
  capital; speckled `granite`. Traced from the sprite (capital 0.45 x the height wide, like the sprite).
- **Food bowl** (`build_foodbowl.py`): one pewter lathe (foot ring, outside, rolled lip, inside) and a noise-lumped
  `porridge` heap that leaves the inner wall showing. Built 0.41 m wide and 0.15 m high: the sprite is a high view
  of a shallow bowl, so bind it by width (height 20 units gives the sprite's 54-unit width; at 32 it is 86 wide).
- **Keg** (`build_keg.py`): a bulging lathe of 24 `kegwood` staves (gaps and grain in the texture), recessed plank
  lid, and four riveted `hoop` bands at the sprite's heights (a pair at the bottom). Procedural, not the scan.
- **Corpses** (`build_corpse.py` with `corpse_pose.py` and `corpse_texture.py`): the rigged MM6 peasants
  (`assets_dev/worlds/mm6/models/mm6_pfem.glb` for `corpse04`, `mm6_pman.glb` for the others; read only, nothing
  in the creature folders is touched) are imported, their clips dropped, placed with a world rotation (supine or
  prone) and posed with world-space bone operations (`aim`, `rot`, `twist`, `move`, and `aim_group`, which turns the
  pfem skirt cone rigidly so it stays round the legs and then sags its panels). The pose is baked to a static mesh,
  seam-split vertices are welded (no cracks under decimation), and each LOD is that body collapse-decimated plus
  its stakes. Stakes are lines or `impale` entries (through a point of a posed bone, so they always pierce the body)
  with the new `stake` texture (bloody above two-thirds, runs below). The body texture is a copy of the peasant's
  atlas recoloured per texel class (strongest bone + colour, shoes by rest height): cold grey-white skin with
  bruising, pale trousers turned to the same skin (pman), tunic/bodice from the region mask recoloured (blue-grey
  "armour" on 05, brown mail on 06, blue cloth on 04), red hair on 04, red boots on 06; blood is painted where it
  belongs on the posed body (the mesh is rasterised in texture space to a world position per texel): ragged soaked
  patches where stakes enter and leave the body and at listed bone points, spatter, and runs flowing straight down.
  The peasant's normal and metal/roughness atlases are copied unchanged. `corpse16` keeps only the legs, cut
  square across mid-thigh, tunic scraps dropped, with flesh caps.
  - `corpse04`: pfem folded backward over one stake through the pelvis, head and arms hanging left, the skirt
    hanging as rags to the right with the feet below its hem. `corpse05`: pman supine across four stakes, arched,
    head hanging, near arm to the ground, near thigh raised. `corpse06`: pman prone, rolled to face the camera, on
    seven slanting stakes, knees bent, red boots. `corpse16`: two severed pman legs on one stake.
  - Body scale: the model heights make the bodies human-sized at the sprite heights (139 / 139 / 177 / 128 units
    -> ~110 units per metre, like the actor binding of the peasants).
- These were added after the earlier props; `make_textures.py` appends `granite`, `pewter`, `porridge`,
  `kegwood`, `hoop` and `stake` at its end (all earlier textures regenerate byte-identical, checked by hash), and a
  rebuild of `campfire` reproduced its installed GLB bit for bit. Every new model rebuilds bit-identical.

## Sources and licences

- Boulders: Poly Haven `namaqualand_boulder_04` (CC0; downloaded for `../rock/`), graded per `rocks.json` to each
  sprite's mean colour; the surf rocks are reshaped toward the sprites' peaks (`peak` in `rocks.json`).
- Log bark: Poly Haven `bark_brown_01` (CC0, `../trees/source/`).
- Fire props (cauldron, campfire, burning rock): Poly Haven `japanese_cedar_bark`, `rust_coarse_01`,
  `rock_boulder_dry`, `bark_willow`, `pine_bark`, `dark_rock` and, for the log-pile fire, `rough_wood` (all CC0, https://polyhaven.com/license; 2k PNG
  diffuse, OpenGL normal, roughness, AO, displacement in `textures_pbr/source/`), graded by
  `scripts/make_pbr_textures.py`.
- Corpse bodies: the project's own MM6 peasant models (`mm6_pfem.glb`, `mm6_pman.glb`, built by the
  `level_generation/creatures/mm6_p*_claude` pipelines); their atlases are copied, recoloured and bloodied per corpse
  into `textures/corpse*_{basecolor,normal,mr}.png`.
- Fountain water (revisions 2–3): `textures_water/stream_*` generated by `scripts/make_water_textures.py`; its
  normal map mixes in OpenMW's `water_nm.png` (GPL-3.0, like this repository; see above).
- All other textures (wood, iron, stone, marble, gold, red paint, cloth, steel, bronze, leather, water, foam, fire,
  blade; later bone, basalt, lava, embers, blue cloth, lava veins, skull, bonfire, camp stone; for outd2 granite,
  pewter, porridge, keg wood, hoop, stake) are generated procedurally by
  `scripts/make_textures.py` (tileable FFT noise; the blade and skull are non-tiling). New textures are appended at
  the end of the script so the seeded noise of the earlier ones, and their installed models, stay byte-identical.
  `lava` is currently unused (kept so the later textures keep their noise).

## Scripts

`scripts/props_lib.py` (lathe/tube/box builders, materials, vertex occlusion, export, renders), `build_cauldron.py`,
`build_fountain.py`, `build_swordstone.py`, `build_surfrock.py`, `build_buoy.py`, `build_flag.py` (variants `flag`,
`flag1`), `build_campfire.py`, `build_burningrock.py`, `build_skullpile.py`, `build_pedestal.py`, `build_foodbowl.py`,
`build_keg.py`, `build_corpse.py` (+ `corpse_pose.py`, `corpse_texture.py`; `-- <corpse> --preview` renders a
quick pose check to `review/<corpse>/pose_*.png`), `review.py` +
`sheet.py` (review sheets), `finish.py` (material modes, LOD link, validation, install), `fetch_pbr.py` +
`make_pbr_textures.py` (fire props' Poly Haven textures), `fire_parts.py` (split logs, ember bed, glow colours),
`make_water_textures.py` (fountain water, `textures_water/`).
The scan rocks go through the shared `../scripts/build_prop.py` (now accepting `PROPS_JSON` / `PROP_ROOT`).

## Review

`review/<prop>/compare.png` (native sprite | LOD0 front | three-quarter | back; flipbook fire shown emissive, as
unlit in the engine) and `review/<prop>/lods.png`;
`review/all_lods.png` (every prop's LODs), `review/outd2_props_compare.png`, `review/corpses_compare.png` and
`review/outd2_props_lods.png` (the outd2 props), `review/swordstone/compare_both.png`, `review/surfrock_foam.png` (foam
over water), `review/textures.png`, `review/fire_water.png`.

## Known compromises

- Fire and fountain water are judged as stills in Blender (first flipbook frame / static streams); the gallery
  scrolls the base colour only, the engine scrolls base and normal maps together.
- The fountain's water is translucent (revisions 2–3) and relies on its primitive order (above); a decoration or
  creature behind a stream that is drawn after the fountain shows through it unblended. Without the map's pool
  (the gallery, the dungeon placement) the streams end on the bare ground.
- Surf rock foam is a flat ring at y ≈ 0.025–0.035 m; it only reads right if the map's water level is at the
  decoration's ground point.
- The buoy has no bob animation beyond `openyamm_wind` sway.
- The skull pile is by far the heaviest prop (22480 triangles at LOD0, 4 levels); LOD1 drops to 6460. Its LOD3
  mound is plain bone with no skull detail.
- The flame cards share one flipbook frame at a time (the phase is per placement), so the mirrored side cards are
  mirror images of the centre flame rather than independent flames.
- The burning rock's glow is alpha-tested lava pools (hard edges up close), not a soft emissive gradient; the
  fire glows are unlit, so they ignore the map's light (as the self-lit sprites do).
- Corpses: the sprites show nude women with long hair and armour/boot pieces; the models are the clothed MM6
  peasants (pman is male, short-haired), recoloured. `corpse04` has pfem's short bun (the sprite's long red hair
  hanging to the ground is not modelled) and its skirt hangs as a bell rather than torn rags; `corpse05`'s armour
  is the tunic coloured blue-grey (no gold trim, no chain skirt); `corpse06` reads more "diving" than the sprite's
  kneeling sprawl. Blood is texture only (no drip geometry). The base colour atlases are 2080 x 1024 per corpse
  (~3 MB each; corpse16 uses ~6 % of its atlas). `corpse16` is lighter than the others (1.2k triangles: pman's legs
  are low poly).
- Pedestal speckle is blotchier than the sprite's fine granite; the food bowl is plainer silver than the sprite.
