# MM6 Reactor (rea) — hand-built 3D model

Descriptors 647/648/652 (`zReactor`, palette 835, one tier), placed once in The Hive (`hive.blv`, actor 0 at
4416, 22464, -2128, on the central dais under the ceiling fixture). Stationary ranged attacker (energy missile).
Installed 2026-10-13: `assets_source/worlds/mm6/models/mm6_rea.glb` (runtime copy in `assets_dev`), bound in
`assets_dev/worlds/mm6/models/actors.yml` (`descriptor: zReactor`). Progress: `creature_3d_progress.json`.

## Route and why

A precise machine of turned parts, not a creature: hand-built in Blender from the native silhouette, no Meshy job
(0 credits). Codex HD masters (`references_hd/`, five views, gated against `reasta00`) are the design reference for
the back and sides, which the original never shows (front-only sprites).

Built to the [game asset modelling guidelines](../../GAME_ASSET_MODELLING_GUIDELINES.md) (Khronos, Arm, Android,
Unity, Unreal, Blender), applied as follows:
- **Silhouette-first segments:** 48 on large shells, 32 on the bowl/cup/liquid, 16 on small turned parts, 8 on
  rods, 12 around balls. The budget is set by quality, not crowd cost: the Reactor is alone in its room with at most
  a few Kreegans (user, 2026-10-13). Straight walls carry only their end rings. Thin lips that would be long slivers (band lip, lid rim, spire collar)
  are normal-map detail; faces hidden under other parts are not modelled.
- **No fans:** disc centres are strip-triangulated rings (max valence 8). Quads are split on the shorter diagonal;
  winding is checked per triangle against the profile normal.
- **Hard edges = UV seams:** profile sections are vertex splits with an 8-texel gap in v.
- **One texel density** (625 px/m on the 2K metal atlas, found by packing all parts at their real sizes until the
  atlas is full); lid top and inner liner deliberately lower, control plate higher. Mirrored halves (u = |theta|/pi)
  and shared rod/hub/strut rectangles are deliberate overlaps. Gutters are dilated.
- **Materials:** base colour 30-243 sRGB; material-class map `textures/rea_material_classes_1k.png` (9 metal,
  11 other: paint, screens, plastic hubs, char). The painter still writes a glTF-convention normal map and an ORM
  map (cavity AO / roughness / metallic) as records for a lit variant; the shipped GLB uses base colour only (below).
- **Transparent parts** (glass, flash shell, shards) on their own mesh node `ReactorGlass`, single-sided; shards
  are duplicated and flipped instead of double-sided blending.
- `scripts/check_geometry.py` reports valence, slivers, sub-10-px triangles at 1000 units and degenerates.
  Accepted sliver class: the thin arm/electrode rods and the struts' narrow sides (inherent to thin cylinders, at the
  minimum side count).

Engine-driven choices (deviations from the lit-PBR guidance, recorded here as the guidelines ask):
- **Every material is unlit (KHR_materials_unlit) with baked light.** The native Reactor frames are fullbright
  ("Lit" sprite flags) and the Hive's room light is dim: lit PBR steel read dull grey and partial-metal diffuse read
  almost black next to the sprite (captured during review; see `review/ingame_final/first_engine_v1.png`). The metal texture carries the light instead: an analytic
  polished-chrome response from each texel's true lathe normal seen from the party's low eye (bright centre, darker
  reflected-horizon band, rim light, brighter upward faces), scaled per part to the sprite's median metal luminance
  at the same heights (`native_shade` in `paint_textures.py`, the elevation form of native shading transfer), times
  the painted detail; seams and rivets get top-lit relief from the height map; rods, tips and bulbs get
  chrome-cylinder shading. The actor always faces the party, so the baked light stays in front, as on the sprite.
  Glass is unlit too: its painted highlights are the reflection.
- Glowing parts use the unlit material because the engine has no emissive texture, and every animated surface (arc,
  lamps, glows, liquid level, wreck) is bone-switched geometry with STEP scale keys, because skinned materials have no
  material clock. Screen waveforms switch by depth instead (STEP translation: the active one 8 mm proud of the dark
  window, the others 38 mm behind it inside the shell), so a clip cross-fade slides them rather than shrinking them.
  Window areas of the band and lid textures are painted dark, and offsets clear depth precision at room distance.
- Arcs get a soft blue halo: a blended unlit tube (`Reactor_Halo`) on the glass node, on the same arc bones.

## Measurements

1 native logical pixel = 1 cm (`scripts/reactor_layout.py`), read from the side silhouette of
`mm6_rea/aligned_2x/reasta00.png` (radius = half width per row). Binding `scale: 200` = native frame scale 2.0 x 100,
so the model stands where the 908-unit sprite did (4.30 m model; the sprite's extra 0.24 m is the lid's top face
seen from its raised render camera). Arm joints from `reaat05` (converged) and `reaat09` (spread), `scripts/
reactor_geometry.py` `POSES`.

## Model (v1)

| | triangles |
|---|---|
| `Reactor` (opaque metal + unlit glow), all parts | 8,368 |
| `ReactorGlass` (glass, broken glass, flash, shards, arc halos) | ~1,900 (768 intact glass) |
| authored LOD chain (`scripts/author_lods.py`) | 8,368 / 5,567 / 3,830 / 3,055 |

LODs are authored, not decimated: `reactor_geometry.build(lod=k)` rebuilds every part with 70/50/33 % of its
segments around (rings, UVs, bones and textures unchanged). Collapse decimation (`tools/build_actor_lods.py`) smeared
the screens and shredded the small parts (`review/ingame_final/decimated_lod*_rejected.png`). LOD3 is held up by
per-part minimum segment counts; with one Reactor in the game that costs nothing measurable.

64 rigid bones, one weight per vertex. Parts switched by scale: four idle arcs, three charge stars, three waveforms
per screen, three lamps, cap and bowl glows, three liquid levels, glass/broken glass/flash, the dome top and spire
versus the torn crown, the lower bowl versus torn petals, the nozzle, eight shards, eight debris chunks, goo stream
and puddle, four three-segment arms. Each bone's vertices carry a distinct micro-offset (<= 0.64 mm) so the LOD
weld never merges parts of different bones (checked: no multi-bone vertex in LODs 1-3).

## Clips (24 fps, `scripts/anim_reactor.py`)

| Clip | Length | Content (native source) |
|---|---|---|
| Standing (also walking, fidget) | 1.125 s loop | arc flicker every 0.125 s, waveforms every 0.375 s, lamps per `reasta00-05` |
| Attack (melee and ranged) | 2.4 s | arms emerge and spread (`reaat02-04`, `reaat09`), swing in (`reaat05`), charge star, discharge flash 1.80-1.98 s, impact marker 1.90 s (missile from `Socket_Arc`), arms retract |
| Hit | 1.125 s | power cut (glows, screens, arc), chamber swings on its mount, base jolts, lamps per `reawi01-06`, power back at 0.86-0.98 s |
| Death | 1.75 s | overload flash and arc star, burst at 0.22 s: glass breaks, shards fly, bowl tears, nozzle drops, dome top bursts with debris; liquid drains in a stream onto the dome; the puddle shrinks (`reade01-06`) |
| Dead | 1.0 s hold | the wreck (`reade07`) |

Deliberate deviation: the native attack (2.0 s) discharges at 0.5-1.1 s and releases the missile at the end; here
the discharge is moved to the release (wind-up 1.90 s, -5 %), so the bolt leaves the arc at the flash.

## Rebuild

```sh
CREATURE_3D_TOKEN=<lease token> level_generation/creatures/mm6_rea_claude/scripts/build_runtime.sh [--install]
```

`paint_textures.py` -> `build_blend.py` (work/model_v1.blend) -> `anim_reactor.py` (work/anim_v1.blend) ->
`export_glb.py` -> `fix_gltf.py` (unlit/blend materials, STEP toggles) -> `tools/prepare_actor_glb.py` ->
`author_lods.py` (authored LODs, merged shadow meshes) -> `tools/install_model.py`.
Review: `review_render.py` (static views vs the sprite), `clip_sheet.py`, the three.js viewer in `review/viewer/`
(checked with `claude_shared/check_viewer.mjs`), in-game captures and their tours in `review/ingame_final/`.

## Checks and status

- Actor regressions: `mm6_reactor_actor_model_binds_the_hive_reactor` (placed Reactor has the model; `Socket_Arc`
  406 units above it) passes. Three unrelated pre-existing failures (pmn2, gua, ooz material checks) fail with and
  without this binding.
- Viewer: all five clips load without console errors.
- In-game review in The Hive (`review/ingame_final/`): `compare_sheet.png` (3D vs the native sprite, close and at
  a level camera: same size and placement under the ceiling fixture), `states_sheet.png` (frozen debug copies:
  discharge, hit, live idle, dying, wreck), forced LOD0/LOD2. The live Reactor attacks the party with arms,
  charge star, flash and bolt from the arc.
- Known limits: screens can flash a split waveform for one cross-fade (~0.2 s) when a clip starts; frozen copies
  about 3,000 units away showed specks in the lid window (depth precision), not seen on the live actor at fighting
  distance or up close.
- **User accepted the model on 2026-10-13.**
