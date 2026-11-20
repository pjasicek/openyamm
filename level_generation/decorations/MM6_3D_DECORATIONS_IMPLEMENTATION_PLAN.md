# MM6 3D decorations: animated-decoration fixups and indoor integration — implementation plan

Status: implemented 2026-10-09 (see "Implementation status" at the end). It replaced the earlier
`MM6_INDOOR_3D_DECORATIONS_PLAN.md`.

Since 2026-10-15 every accepted decoration GLB, of any world, is engine content: a source in
`assets_source/engine/models/` (it was `assets_source/worlds/mm6/models/` from 2026-10-12), bound by the worlds'
manifests as `engine/models/...`. Install new or revised ones with `tools/install_model.py <export.glb> --engine`,
which also writes the cooked runtime copy into `assets_dev` (see AGENTS.md). The install paths in the project scripts
below predate this.

Scope:
- **Part A:** fix the animated MM6 outdoor decorations that are already 3D.
- **Part B:** shared engine work that indoors needs, written once for both indoor and outdoor.
- **Part C:** indoor content for all 51 MM6 dungeons.

MM7/MM8 content is out of scope. The engine work is world-agnostic, so it applies to those worlds later.

Decisions so far:
- **Hanging cages sway**, as MM7's cages do.
- **Fire is a hybrid:**
  - Flipbook flame cards on every flame. This is the standard technique: cheap, little overdraw, and no sorting
    when blended additively.
  - A few particles only near the camera.
  - The flame art is chosen at the pilot (A3, C1).

## 1. What exists today

**Engine.** Static 3D decorations (`DecorationModelSet`, outdoor only), bound by name in
`worlds/mm6/models/decorations.yml`. They have:
- Instancing and LODs with crossfade.
- Water reflections.
- Bake casters and precise picking (LOD1 ray cast).
- Material extras, in `engine/models/ModelAsset.h` and `game/shaders/model_static.sh`:
  - `openyamm_billboard`: a quad turned about the vertical axis toward the camera.
  - `openyamm_flipbook [columns, rows, fps]`: with a per-placement phase from the placement position.
  - `openyamm_uv_scroll`.
  - `openyamm_flutter`.
  - `openyamm_wind`.
  - `openyamm_specular(_mask)` and `openyamm_translucency`.
- Runtime shadows skip blended and billboard primitives (`ModelRenderer.cpp`, shadow batch filter).
- Decoration lights and their pulse, plus the native `EmitFire`/`EmitSmoke` particles, come from
  `OutdoorSpatialFxRuntime::syncDecorationEmitters`. They do not depend on how the decoration is drawn.

**Outdoor animated decorations.** All of them are 3D already. The native frame count and loop come from
`sprite_frame_data_common.yml`; one raw unit is 1/16 s.

| Decoration | Native animation | Model | Model animation | Maps (placements) |
|---|---|---|---|---|
| ckfyr00 cauldron | 6 frames, 1.13 s loop (≈5 fps) | cauldron | flame card, procedural flipbook 4×4 at 12 fps | 10 maps (19) |
| cmpfyr00, dec25 campfire | 6 frames in 0.38 s (16 fps); 8 frames in 1 s (8 fps), light 128 | campfire | three flame cards, same flipbook | outc2, oute2 (4) |
| brnrock0 burning rock | 6 frames in 0.38 s, Glowing | burningrock | flame column, same flipbook; unlit lava cracks | 5 maps (8) |
| sta1a fountain | 3 frames, 0.56 s | fountain | `uv_scroll` water | oute3 (3) |
| searka01/searkb01 surf rocks | 6 frames, 1.13 s | surfrock_a/b | `uv_scroll` foam, BLEND | 9 maps (308) |
| fla1__01, fla3__01 flags | 8 frames, 1.5–2 s | flag1, flag | `flutter` | 8 maps (9) |
| bouy0 buoy | 10 frames, 3.1 s | buoy | `wind` sway | 4 maps (30) |

**Indoor (MM6, 51 BLV maps).** 5764 placements of 100 types. About 100 of them are invisible markers.
- **Wall torches:** 6torch01 ×3441, trchb00 ×755, torch01 ×75, torch03 ×6, torch2 ×4. That is 75% of all
  placements.
- **Other flames:** brnrock0 ×106, cauld00 ×39, flamb00 ×33, dec04 campfire ×30, scon200 ×20, ckfyr00 ×7,
  cndlab0 ×6, torskul0, scon100.
- **Glowing crystals:** crystl0 ×32, mcryst01 ×4.
- **Moving:** chndlir0 chandelier ×3, and the hanging cages hngncge2 ×8 and `empty`. The MM6 cage sprites are
  static; MM7's 7dec05/06 swing in a 12-frame ping-pong loop of 1.5 s.
- **Containers:** smlbarel 152, bigbarel 135, bag_a 123, bag01 74, floursac/floursack 70, bucket 28.
- **Dressing:**
  - brazir2f 111, sklplrev 86, corinth 32, torchnf (unlit torch) 29, trasheap 28, bonecage 19.
  - Crystals, stalagmites, mushrooms and about 30 corpse variants.
  - A few outdoor rocks and trees, and sta1a (fountain) ×1.

Indoor renders decorations as billboards. Visibility is per sector (`isRenderSectorVisible`), and lighting is per
billboard. Light toggles come from events (`indoorDecorationLightToggleTarget`). Picking uses a 48 × 48 × 64 entity box
in `IndoorRenderer::inspectAtCursor`. Torch facing is 0 in the map data (931 of 931 checked).

## Part A — outdoor fixups

### A1. Flame, water and foam cards must not cast baked shadows

`bake_outdoor.py` (`decoration_model_casters`) imports every mesh of a model as a caster. This causes two problems:
- **Flame cards** cast a fixed-orientation shadow. In Blender their texture coordinates span the whole 4 × 4 atlas,
  so the shadow is 16 small flame shapes.
- **Fountain water and surf foam** (BLEND) also cast.

The runtime already skips blended and billboard primitives for its shadows.
- Change: after the glTF import, drop caster objects whose material uses alpha blending or carries the
  `openyamm_billboard` extra. Blender's glTF importer keeps material extras as custom properties. Then apply the same
  rule as the runtime, and state it in `MODEL_RENDERING.md`.
- Re-bake: the 14 maps with cauldron, campfire, burning rock, fountain or surf rocks. That is every map except
  outa1. Then run the MM6 regressions and capture the fire props.

### A2. Picking billboard cards where they are drawn

`DecorationModelSet::pickTriangles` takes billboard quads in their rest pose, but they are drawn facing the camera.
A cursor on a visible flame can miss, and one beside it can hit.
- Change: keep the pick triangles of billboard primitives apart, with their placement origin and across axis. In
  `raycast`, turn them toward the ray origin about the vertical axis, as `modelStaticPosition` does, before
  intersecting.
- Test: a unit test for a billboard quad hit from two directions, and the existing New Sorpigal regression.

### A3. Flame fidelity

- **Shared flame library.** Move the flame atlases (`fire`, `bonfire`) to one documented place shared by every fire
  model, and add a small-flame `torch` atlas for Part C. Each model keeps its own fps.
- **Speed.** Match each model's fps to the native flicker rate where it reads better: the campfire and burning rock
  are faster natively (16 fps), the cauldron slower (≈5 fps). Rebuilding a GLB invalidates its maps' bakes, so do
  this together with the A1 re-bake.
- **Art review.** Compare procedural flames with the restored native frames. Build a still sheet from the
  `decorations_x2` frames and a capture of each model. If the native frames win, they become the atlases. Decide
  this together with the indoor torch in C1, so outdoor and indoor fire match.

### A4. Parity checks (no change expected)

- The decoration light, its pulse and dec25's 128 radius still come from the decoration table. Check that the light
  origin sits in the model's flame (capture at night).
- Decoration sounds (cauldron, campfire, fountain) play as before.
- The water reflection shows the animated parts: flipbook, foam scroll and flag flutter.
- The hover outline is not drawn around flame cards.

### A5. Guard against missing animation

Extend the MM6 decoration regression with a rule: every binding whose native sprite has more than one frame must
have an animated model, meaning one of flipbook, uv_scroll, flutter, wind, swing or pulse. Otherwise the binding
must say `still: true`, so the choice is recorded in `decorations.yml`. This also covers Part C.

## Part B — shared engine work

### B1. Indoor model decorations

- Load a `DecorationModelSet` alongside `m_indoorDecorationBillboardSet` in `IndoorRenderer`. Indoor bindings list
  `.blv` maps under `maps:`.
- Each frame, set `ModelStaticPlacement::visible` from the event state and from
  `isRenderSectorVisible(billboard.sectorId, visibleSectorMask)`. `renderStatic` then does the frustum test and LOD
  selection.
- `renderDecorationBillboards` skips billboards whose sprite is modelled.
- The indoor reflection pass (around `IndoorRenderer.cpp:9970`) calls `renderReflection`.
- Extend `--headless-export-decoration-models` to BLV maps, for tests and the wall-mount report in B3.

### B2. Indoor lighting

- Fill the per-placement `pointLight` from the same per-billboard lighting the sprite uses today, with no sun term.
  A model is then exactly as bright as the sprite it replaces.
- Recompute when lights change (event toggles, spells, the party torch), not every frame for every placement.
- Second step: a key-light direction from the strongest light, using the creature path
  (`selectDrawLightSetForBounds`) as the reference.
- No shadows indoors in this plan.

### B3. Wall mounting

- Binding field `mount: wall`. At load, find the nearest vertical face within about 64 units in the decoration's
  sector and its portal neighbours. Take the yaw from that face's normal, and set the model back so its back plane
  touches the face.
- List placements with no wall in range in the BLV export, then fix the threshold or the content.

### B4. Indoor picking and hover

- In `inspectAtCursor`, use `DecorationModelSet::raycast` (including the A2 billboard rule) when a model draws the
  billboard.
- Skip the entity box for entities with a decoration billboard, as the outdoor fix does.
- Keep the hover-hint fallback (`resolveEntityDecorationHoverStatusText`).

### B5. Lit and unlit state

A torch put out by an event should show the unlit bracket: `torchnf` is the native unlit torch.
- Binding field `unlit: <decoration name>`. While the decoration light is toggled off, the placement uses that
  binding.
- This reuses `DecorationModelSet::update`'s sprite-switch path, so no per-part visibility is needed.

### B6. Swinging models

Binding field `swing: {angle_degrees, period_seconds}` for chandeliers and hanging cages.
- Each frame, the CPU rotates the few placements about their top pivot by `angle · sin(2πt / period + phase)` and
  updates their bounds.
- Cages take their period and amplitude from MM7's 7dec05/06 (1.5 s ping-pong).
- There are only a few such placements, so no shader path is needed.

### B7. Glow pulse

Material extra `openyamm_pulse [amplitude, period]`. It scales the material's emission by
`1 + amplitude · sin(2πt / period + phase)` in `fs_model`, using the existing placement phase. Used by crystl0
and mcryst01.

### B8. Near-camera embers and smoke (optional, last)

- Binding field `effect: <effect id>`, emitted from a `Socket_Flame` node in the model.
- A shared runtime (game FX, not indoor/outdoor-specific) keeps the effect only on the nearest N placements (start
  with 8) that are visible and within range. They fade with distance, the way Niagara's significance culling does.
- It reuses the authored effects library (`assets_dev/engine/effects/authored/library.yml`) and `WorldFxSystem`.
- Applies to outdoor fires too.

### B9. Only if the pilot needs them

- `openyamm_blend: additive`: lets overlapping flames ignore draw order.
- Flipbook frame crossfade: two texture reads, which smooths 6–10-frame native flames.
- Decide these after C1.

## Part C — indoor content

The route is the same as outdoors: procedural Blender modelling traced from the native sprites, Poly Haven CC0 scans
and procedural textures (`mm6_new_sorpigal_3d/props/`).
- **Height:** world height = native sprite pixels × DSFT frame scale.
- **Budgets:** triangle budgets follow complexity and placement count.
- **Lighting:** after each model change, nothing needs re-baking indoors.

| Batch | Contents | Notes |
|---|---|---|
| C1 pilot | 6torch01 bracket and flame card, torchnf | Pilot dungeon **6d01 Goblinwatch** (its goblins are already 3D). Bracket LOD0 300–600 triangles. All of B1–B5 is proven here, plus the flame-art decision for A3. |
| C2 torches | trchb00, torch01, torch03, torch2, flamb00, scon100/200, torskul0 | Variants of the pilot bracket. |
| C3 fire props | brazir2f, brnrock0 / dec04 / ckfyr00 (reuse the outdoor models), cauld00, cndlab0 | Flame cards. The cauldron gets a bubbling-surface flipbook. |
| C4 containers | smlbarel / bigbarel (reuse keg, barrel), bag_a, bag01, floursac/floursack, bucket | Static, low triangle counts. |
| C5 dressing | sklplrev / corpses / rocks / trees / fountain (reuse), bonecage, trasheap, corinth, crystals, stalagmites, mushrooms | Crystals use B7. |
| C6 moving | chndlir0, hngncge2, empty cage | B6. |

## 2. Order of work and checks

1. **A1 + A2 + A5.** Re-bake 14 maps, run the MM6 regressions, capture the fire props.
2. **B1–B4 with C1 on 6d01.** Check sprite-to-model brightness side by side, wall-mount report, picking, captures.
3. **B5, then A3 and the C1 flame art together.** Decide the flame art with the user from captures. Rebuild the
   outdoor fire models if needed and re-bake their maps.
4. **C2–C5**, one batch at a time, with captures of the densest maps for each batch.
5. **B6, B7 and C6.**
6. **B8 and B9**, if wanted after step 5 is on screen.
7. **Performance and documentation.**
   - Profile the densest torch corridors before and after. Check that no other `openyamm` instance runs before and
     after each measurement.
   - Run the indoor regression suite.
   - Add an indoor section to `engine/render/MODEL_RENDERING.md`.

Unit tests cover the pure logic: the billboard pick, wall-mount yaw, swing transform and binding parsing. Headless
regressions cover the map-level bindings, the animation guard from A5 and placement counts.

## 3. Risks

- **Draw count in torch corridors.** One instanced draw per model group and LOD, plus one per flame group. Measure
  this on 6d01 first.
- **Brightness mismatch** with the surrounding faces and sprites. Step 2 matches the sprite lighting before
  anything else changes.
- **Wall-mount misses** on pillars and corners. They are reported, and a binding can override them.
- **Events:** SetSprite, hiding and light toggles must keep working. The outdoor `update()` path handles sprite
  switches and hiding; B5 extends it.

## Implementation status (2026-10-09)

| Item | State |
|---|---|
| A1 bake casters | Done: blended and camera-facing faces cast no baked shadow (`casts_shadow` in `bake_outdoor.py`). The 14 affected maps were re-baked. |
| A2 billboard picking | Done: `facingCardCorner` and `DecorationModelSet::raycast`, with a unit test. |
| A3 flame fidelity | Done, with a change of source: the upscaled native flames were too poor. Every fire, indoor and outdoor, uses the CC0 Unity Labs Flame02/Flame03 flipbooks recoloured to the MM torch flame (`mm6_dungeons_3d/textures/FLAMES.md`). The outdoor campfire, cauldron and burning rock were rebuilt and their 12 maps re-baked. |
| A4 parity | Checked: outlines skip blended materials; lights and sounds do not depend on how a decoration is drawn. |
| A5 animation guard | Done: `decoration_models_keep_native_animation` covers the outdoor and indoor manifests (of every world since 2026-10-15). |
| B1 indoor models | Done: `indoor_decorations.yml`, sector visibility, sprite skipping, reflections; the BLV export lists placements and unmounted wall fixtures. |
| B2 indoor lighting | Done: the sprite's light (a self-lit flame sprite at one) as the placement ambient, with the creature key light. |
| B3 wall mounting | Done: `mount: wall`, the nearest steep face within 64 units, and `free_model` where none is in reach. The regression `mm6_decoration_models_indoor_wall_torches` covers it, and every MM6 dungeon mounts or stands every fixture. |
| B4 indoor picking | Done: model ray casts, and no entity box for model-drawn entities. |
| B5 lit/unlit | Done without engine work: light toggles switch sprites, and both sprites of each pair are bound. |
| B6 swing | Done: `swing`, used by the cages and the chandelier. |
| B7 pulse | Done: `openyamm_pulse`, used by the crystals. |
| B8 embers near the camera | Not done (optional). |
| B9 additive blend, frame crossfade | Not needed: the 64-frame flipbooks loop smoothly. |
| C1-C6 content | 98 indoor bindings covering 5661 of 5665 visible dungeon placements (only `torch2`, 4 placements, has no decoration entry). Batches are in `mm6_dungeons_3d/<batch>/`. |
| Event sprite switches | Checked (2026-10-09) against every `SetSprite` in the MM6 map scripts: each source and target is bound in its manifest, so a switched decoration stays 3D. Pairs: memory crystal `mcryst01` ↔ `crysdisc` (cd1-3, 6t6, oracle), `ped06` → `ped01`-`ped05` statuettes (`mm6_new_sorpigal_3d/statuettes/`), `swrdstn` → `swrdstx`, `tree06a` → `6tree06`, torches; target `0` hides. The Book of Liches in Castle Darkmoor is a face texture switch (`SetTexture`), not a decoration. |

Development flow: a changed bake source no longer blocks loading a map. Stale bakes are noted in
`assets_dev/STALE_LIGHTING_BAKES.txt`; run `tools/lighting/stale_bakes.py` before a release or commit.

Performance: in the pyramid's densest torch hall (445 placements), render CPU time is unchanged, and FPS stays
within run-to-run noise (`engine/render/MODEL_RENDERING.md` section 10).

