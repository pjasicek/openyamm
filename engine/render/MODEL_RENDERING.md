# 3D model rendering: what we stand on

State of 2026-10-08. This document covers glTF creatures (skinned actors), their carried items, and static
decoration models: the asset contract, the build post-processes, how `ModelRenderer` draws them, and how to make a
variant such as a boss. Keep it in step with the code. If a statement here disagrees with the code, the code wins;
fix this file in the same change.

Code: `engine/models/` (loading, `ModelInstanceSystem`, poses) and `engine/render/ModelRenderer.{h,cpp}` (drawing).
Shaders: `game/shaders/vs_model*.sc`, `fs_model.sc`, `model_skin.sh`, `model_static.sh`. World bindings:
`assets_dev/worlds/<world>/models/actors.yml` (creatures, read by `game/fx/WorldFxSystem.cpp`) and `decorations.yml`
(read by `game/maps/DecorationModelSet.cpp`).

## 1. Asset contract (GLB)

| What | How it is expressed |
|---|---|
| Colour LODs | Base mesh `extras.openyamm_lods`: up to 3 coarser mesh indices, coarsest last, decreasing triangles. Shadow-only chains go in `openyamm_shadow_lods` (up to 4). Static models get these from `tools/link_static_model_lods.py`; creatures from `tools/build_actor_lods.py`. |
| Colour variants (tiers) | `KHR_materials_variants`. Tiers share one skin: a region mask (`extras.openyamm_region_mask`, up to four RGBA channels) and per-tier `openyamm_region_ramps` (16 linear stops over a luminance range per region), written by `level_generation/creatures/claude_shared/region_variants.py`. `actors.yml` picks a tier with `skin:`. |
| Specular | `extras.openyamm_specular` (0..1; 0 skips sky reflection and specular lobes). `extras.openyamm_specular_mask: true` multiplies it per texel by the metallic-roughness texture's red channel, which glTF leaves unused. It lets a matte head and glossy armour share one material. |
| Static decoration extras | `openyamm_wind`, `openyamm_billboard`, `openyamm_translucency`, `openyamm_uv_scroll`, `openyamm_flipbook`, `openyamm_flutter`; COLOR_0 multiplies the base colour (`engine/models/ModelAsset.h` documents each). |
| Sockets | Empty nodes named `Socket_*` (palms, eyes, staff head) that FX attach to; `actors.yml` names them. |
| Held items | Not part of the creature: a separate unskinned GLB in the space of the bone that carries it (section 3). |

The loader rejects what the renderer cannot honour (unsupported extensions, bad extras, inconsistent LOD chains)
instead of guessing.

## 2. Creature build post-processes (order matters)

Each creature project's `scripts/build_runtime.sh` ends with:

1. `region_variants.py`: tiers as one shared skin plus ramps.
2. `tools/split_attachment.py creature.glb --joint <Bone> --body creature.glb --attachment item.glb`: only for
   creatures that hold something. It moves every triangle weighted fully to `<Bone>` out of all colour and shadow
   LODs into a static GLB in that bone's space (inverse bind applied), with the item's part of each texture
   (region mask included) cropped out and the creature's colour variants kept under the same names, so tiers
   recolour the item as before. A triangle that mixes item and body vertices is refused. Held items split so far:
   mage staff (`Staff`), goblin sword (`Sword`), guard halberd (`Halberd`, by the guard session).
3. `tools/merge_head_material.py creature.glb creature.glb`: the separate head texture set joins the body. Each LOD
   becomes one primitive and each tier one material, using a `body | 32 px gutter | head` atlas per map
   (2080×1024 for 1K maps; texels unchanged). Metallic, roughness and specular differences between head and body
   are baked into the metallic-roughness atlas (specular through `openyamm_specular_mask`). Any other difference,
   or head ramps that differ from the body's, is refused. It does nothing for creatures without a `*Head*`
   material (rob1, ooz).

Applied as of this date: pman, pfem, gob, gua (by its session) and pmn2 (also split). One material means one draw
per creature, which is what instancing (section 4) batches.

## 3. Runtime objects

- `ModelInstanceSystem` holds instances: asset, root transform, clip state, pose and bounds, material variant,
  outline colour, and **attachments** (`ModelAttachment {asset, nodeIndex, materialVariant}`). An attachment is drawn
  with its node's world matrix every frame. It has no skin and no pose of its own.
- `WorldFxSystem` binds actors to models from `actors.yml`. One binding per monster descriptor. An attachment
  without its own `skin:` uses the carrier's skin when the item has a variant of that name (split items do), so a
  tier's item matches its body; a different weapon per tier or boss is just a different `attachments` model.
- **Static stand-ins (corpses).** `ModelInstanceSystem::setStaticStandIn(handle, asset)` replaces an instance's own
  skinned draws with a static asset placed at its root transform; the instance keeps its pose, bounds, picking and
  attachments. `WorldFxSystem` sets it when an actor is dead, its death clip has finished and its Dead clip is held
  (past its end, or the corpse's clock stopped: dead actors are not updated). The stand-in is
  `bakeStaticModelPose` (`engine/models/ModelAnimation.h`) of that held pose, baked once per model, Dead clip and
  held time on the first corpse: every mesh node with its colour and shadow LOD chains skinned and morphed into
  asset space on identity nodes, with the source's materials and images (so GPU textures are shared). A baked node
  must carry an identity `matrix`, because poses read `node.matrix`, not the TRS.
- **Loot satchels (default `gameplay.corpses=satchel`).** Once a slain creature's body is at rest (model: its baked
  stand-in is shown; sprite: its dead frame), `WorldFxSystem::syncCorpseSatchels` waits 0.1 s, then the body dissolves
  (`ModelInstanceSystem::setCoverage`, screen-door dither on the stand-in and attachment placements) while it sinks by
  its height over 0.9 s (a sprite is only lowered, through `actorCorpseSinkDepth`). The satchel
  (`engine/models/loot_satchel_t1..6.glb`, a static stand-in instance) fades in with a small overshoot over the first
  0.35 s of that, so body and satchel cross over. Satchels share one drawstring-sack shape and tell their tier by
  material and size (burlap, green wool, rust leather, blue leather, purple velvet with a glowing violet gem, crimson velvet
  with a glowing gold gem; `level_generation/props/loot_satchel_claude/v2/`). They are authored at their in-game
  widths, 0.5-1.25 m (the size of the game's dropped items, so grass does not hide them), and have no LOD chain: at
  about 900 triangles, full detail costs little, and collapsed LODs visibly changed their shape (v1). The tier follows the
  corpse's gold plus item value (`IGameplayWorldRuntime::corpseLootValue`; 1-99, 100-749, 750-2,999, 3,000-7,999,
  8,000-14,999 for a rich hoard or an artifact, 15,000+ for an artifact or relic), and changes as items are taken; an
  empty corpse dissolves and leaves nothing. The loot is rolled at death (`ensureMapActorCorpseView`), and for older
  saves on the first actor update after loading. Once the body is gone, hover outlines and picking go through the
  satchel; a sunk empty corpse reports empty bounds and is not picked. Corpses seen already at rest (a loaded map)
  show their satchels at once. `corpses=keep` leaves the bodies as before.

```yaml
- descriptor: Necromancer A                # monster table name
  model: worlds/mm6/models/mm6_pmn2.glb
  scale: 140                               # model units; scale_reference: <descriptor> scales by sprite ratio
  skin: pmn2_d                             # tier (KHR_materials_variants name)
  attachments:                             # rigid items on nodes of the model
    - model: worlds/mm6/models/mm6_pmn2_artifact_staff.glb
      node: Staff
  animation:
    cast_color: [176, 70, 255]             # cast charge colour instead of the spell element's
    cast_focus_socket: Socket_Staff_Head   # second charge glow at the item
    ranged_hand_effects: {Dark: openyamm:fx/creature_dark_staff}
    ranged_hand_sockets: [Socket_Staff_Head]
    # also: cast, run, stride_length, upper_body_root, sockets, eye_color, glow scales
  clips: {standing: …, walking: …, attack_melee: …, attack_ranged: …, hit: …, dying: …, dead: …, fidget: …}
```

## 4. How `ModelRenderer` draws

Order in a frame: `renderSunShadows` (when shadows are on), then `renderStatic` (decorations), then `render`
(creatures, then their attachments, then transparent creature materials).

**Joint palette.** All skinned nodes share one RGBA32F texture, 512 texels wide, holding 128 joints per row as
4 texels per matrix. A skin keeps its rows while its instance lives and re-uploads them only when its pose
revision changes. The texture doubles in height when full. `model_skin.sh`: `modelSkinMatrix(row)` blends up to
eight influences into one world-space matrix shared by position and normal. Joints carry uniform scale only;
non-uniform bone scale would skew normals.

**Instanced skinned creatures** (`submitInstancedSkinned`, `vs_model_skinned_instanced.sc`). An opaque creature
draw is instanced when it is skinned, has no hover outline and no point lights, and shares the frame's sun, sky
scale and key light. Batches are per primitive, material and winding. Each instance is 32 bytes: ambient light
(rgb), sun visibility, and its palette row. One draw covers every creature on the same LOD of the same model and
tier. Point-lit creatures (most indoors), outlined ones, morphing ones (the demon's face) and blended materials keep
their own draws through `submit()`. That path is the reference: `render instancing off` must look identical.

**Attachments** become static placements (`collectAttachments`): one `ModelStaticGroup` per item model and
variant, with each placement at its carrier's node matrix. A placement takes the carrier's colour LOD level, its
ambient light and sun visibility, its point lights folded into undirected light at the item, and its hover
outline. A carrier keeps its LOD hysteresis across frames. Items are instanced like decorations: every mage's
staff is one draw per LOD. They cast sun shadows with the static casters.
Static stand-ins go through the same path (`collectAttachments`, one group per stand-in asset and variant), but each
placement picks its colour LOD by projected size with the coarser `ModelStandInLodPixels` (750/300/120 px) instead
of a carrier's level. `collectDraws` skips their skinned draws and releases their joint palette rows. Measured
(New Sorpigal, 50 Cockatrice corpses, `output/performance/corpses_20261008/README.md`): −110 µs GPU when they fill the
screen, −50 µs at mid distance; screen coverage and LOD0 triangles, not skinning, are most of a corpse's cost.

**Static decorations** (`renderStatic`). Placements are culled each one, LOD chosen with hysteresis
(`lod_pixels`), and the switch crossfaded with dither for 0.3 s. Each LOD primitive is one instanced draw. LOD0
alpha-tested foliage gets a depth prepass, followed by a discard-free shading pass with an equal depth test.

**Lighting model.** `ModelRenderLighting` holds the shared terms (sun direction and colour, fog, indoor key light,
`environmentScale`: sky reflection as a multiple of the ambient light) and the per-model terms (`ambientColor`
× `ambient`, `direct` = sun visibility, up to 12 directional point lights). Instanced paths keep the shared terms
in uniforms and move the per-model terms into instance data (`v_color0`), so a batch needs only one uniform set.

**Per-draw overhead** is the main cost on the CPU-bound reference pose. bgfx keeps uniform values between draws.
Shadow matrices and samplers are bound per draw only when shadow maps exist; otherwise the zero enable flag is set
once per view. Consecutive draws of one instance skip its lighting uniforms.

## 5. Making a variant (the boss mage recipe)

A variant needs no new mesh: give it a tier ramp, a scale and attachments, plus FX colours.

1. Tier: add a ramp to the creature's tier script (`mm6_pmn2_claude/scripts/tier_ramps.py`: `BOSS_TIER pmn2_d`)
   and rebuild. Every tier shares textures, so a tier costs one material and a small ramp texture.
2. Item: model it in the carrying bone's space (`mm6_pmn2_claude/scripts/make_artifact_staff.py`: the shaft along
   the bone axis, the crystal centred on `Socket_Staff_Head`), link its LODs, install it.
3. Bind it in `actors.yml` (example above). Items of the same model batch across all carriers; a different item
   adds one draw per LOD in view.
4. Test: `actor spawn 307 1 <x> <y> <z>` (Necromancer A, not placed on any MM6 map) with
   `debug.actor_models=true debug.immortal=true`. Regression: `mm6_pmn2_actor_models_bind_free_haven_mages` checks
   the four tiers of one skin and that every mage carries its staff on the Staff bone.

## 6. Profiling switches and measured state

Console `render <switch> on|off|toggle`. Layers: `terrain`, `bmodels`, `sky`, `water`, `grass`, `deco_models`,
`deco_sprites`, `actors`, `creature_models`, `effects`. Settings: `foliage`, `instancing`, `shadows`, `ao`,
`grading`, `model_lods`, `lightmaps`, `freeze`. `render lod <-1..3>` forces a LOD. Every change logs
`[RenderLayers]`. Scripts and results:
[decoration and reference-pose profiling](../../output/performance/decorations_20261008/README.md).

Reference pose (New Sorpigal start, 1600×900, RTX 3060 Ti, OpenGL), quiet machine:

| | fps |
|---|---|
| all sprites (before the 3D work) | 1,760–1,800 |
| 3D decorations and creatures, morning of 2026-10-08 | 1,395–1,420 |
| + head merge, shadow-binding skip, instanced creatures | **~1,720** (instancing off: ~1,560) |

## 7. Known limits and next levers

- bmodels (world buildings, `game/outdoor/OutdoorRenderer.cpp`) are not glTF models but share the draw-count
  problem; see section 8.
- The shadow pass still draws creatures one by one; shadows are off by default (baked lighting).
- Indoors most creatures are point-lit and keep their own draws. Instancing them would need a few point lights per
  instance.
- Joint matrices assume uniform scale (ooz grows a pseudopod by bone scale: its normals are approximate while it
  grows).
- pmn2's body atlas still holds the staff's texels (about 4 % of the 1K map), which `split_attachment.py` leaves in
  place. Repacking needs the Blender UV pass (`atlas_pack.json`, then `dump_uv3d_body.py` for the native shading).

## 8. Outdoor bmodel texture arrays (2026-10-08)

The resolved bmodel path (lightmapped outdoor maps that are not BModel-world maps) used to draw one group per
material and lightmap page across the whole map: 147 draws of about 36 vertices each at the reference pose, cheap
on pixels and expensive in per-draw cost. Now `createBModelTextureBatches` puts every single-frame bmodel texture
into a texture array per exact physical size (`BModelTextureArray`, same edge bleed and mip chain as the 2D
texture; no 2D copy is kept, so GPU memory is unchanged). A size with only one texture keeps its 2D texture,
because bgfx creates a one-layer array as a plain 2D texture. Animated textures keep their 2D frames.

- Lightmapped faces group by (array, lightmap page, water colour); `LightmappedBModelVertex::textureLayer` carries
  the layer, and `fs_outdoor_bmodel_{lightmap,baked}_array` sample `s_texColor` as an array.
- Faces drawn one by one (moving mechanisms, faces without lightmap) bind the array and set
  `u_bmodelTextureLayer` for `fs_outdoor_textured_fog_array`.
- `OutdoorRenderer::resolvedBModelGroupFrame` decides drawability and frame for the main and reflection passes.

Reference pose, same run, buildings on against off: 147 → 22 bmodel draws, CPU cost about 126 → 61 µs, GPU cost
about 110 → 58 µs (fps on/off 1,577/1,937 before, 1,761/1,933 after). Same-pose captures of MM6 (oute3, oute1),
MM7 (7out01) and MM8 (out01) match the 2D path except for animated content. Lightmaps off and BModel-world maps
use the old path unchanged.

## 9. Water reflections and the lighting bake (2026-10-09)

**Reflections.** `OutdoorRenderer::renderWaterReflections` draws the 3D decorations and creatures into each water
reflection view through `ModelRenderer::renderReflection` when `video.water_sprite_reflections` is on (the
reflected sprites they replace follow the same setting; actors with models are skipped in the sprite pass).
- `fs_model` clips against `u_worldClipPlane` (zero, so no clipping, outside reflections); the reflection passes
  set it to the water plane.
- The pass reads the main view's LOD hysteresis and crossfade state without writing it (`ModelLodView::keepState`),
  does not cull (the mirrored view flips winding), and skips hover outlines and the foliage depth prepass.
- Lighting is shared with the main pass: `OutdoorRenderer::modelSceneLighting` (shared terms) and
  `creatureModelLighting` (per creature: baked probes, nearby lights, sky).
- Water that has no object reflections (the small shore inlets) shows none for models either, as for sprites.
  Check in a scene with both: save `saves/save31.oysav` ("NS_10"), trees and goblins at the dock.

**Bake casters.** With `decoration_shadows`, `tools/lighting/bake_outdoor.py` runs
`openyamm --world <world> --headless-export-decoration-models <map> <out.json>` (`--game-binary`, default
`build/game/openyamm`) and casts every 3D decoration with its own LOD0 meshes: one import per model, a linked copy
per placement at the game's placement matrix, invisible to the camera and to bounces, in the sun terms only (like
the sprite cards). Decorations without a model keep their sprite cards. The models and `decorations.yml` are
recorded as bake dependencies. Changing a decoration model or its binding makes the bakes of the maps that use it
stale. The game still loads them and notes them in `assets_dev/STALE_LIGHTING_BAKES.txt`. Re-bake what
`tools/lighting/stale_bakes.py` lists before a release (`tools/lighting/baked_outdoors/README.md`).
- The casters skip blended and camera-facing (`openyamm_billboard`) faces, as the runtime shadows do: a flame card
  has no fixed shadow, and in Blender a flipbook card would cast its whole atlas (`casts_shadow` in the bake).

## 10. Indoor decoration models and animated decorations (2026-10-09)

**Bindings.** Indoor (BLV) maps read `worlds/<world>/models/indoor_decorations.yml`, outdoor maps
`decorations.yml`. They are separate because `decorations.yml` is a dependency of every baked outdoor map, and
indoor maps have no bake. A binding without `maps` applies to every map of its kind. Fields beyond the outdoor ones:
- `mount: wall` hangs the model on the nearest steep face within 64 units, measured at half its height
  (`findIndoorDecorationWall`). The model's front (asset +z) points along the face normal, and its back (asset bounds'
  minimum z) lies on the face. Native torch facings are always 0, so this is the only orientation they have.
- `free_model` is drawn where no wall is in reach: its own binding and group after the binding it serves. Without it,
  such a placement keeps its map facing and is listed in `DecorationModelSet::unmountedBillboards` (the BLV export
  lists them with positions).
- `swing: [degrees, seconds]` swings the model about the asset x axis through the top of its bounds,
  `DecorationModelSet::animate` on the CPU, each placement out of step.
- `still: true` records that a natively animated sprite is drawn by a still model. The regression
  `mm6_decoration_models_keep_native_animation` fails for an animated sprite whose model has no flipbook, uv scroll,
  flutter, wind, pulse or swing.

**Drawing.** `IndoorRenderer` loads the set beside the decoration billboards and draws it with `renderStatic`
before the creatures. Each frame, `updateDecorationModels`:
- hides placements outside the portal-visible sectors;
- follows event sprite switches, including the lit and unlit torch and brazier pairs that light toggles flip;
- sets the hover outline;
- gives each placement the light its sprite would get (`billboardLightingUniform`; a self-lit flame sprite gets one)
  as its ambient.

That light is drawn with a softer key light than the creatures get (`IndoorDecorationKeyFraction` 0.35) and an
exposure of `IndoorDecorationExposure` 1.8. A model's visible surface averages well below its light level: faces
turn from the camera and the key light, and Fresnel and the baked vertex occlusion darken it further. A painted
sprite shows all of its light. The exposure was measured against the sprites the models replace, in model/sprite
capture pairs from four dungeons (`output/dungeon_content_20261009/`), where it brings the median ratio to about one.
What remains per model (0.6 to 1.3) is that model's albedo. Their sky/environment reflection, the only
specular indoors, is `IndoorDecorationReflection` 0.1 of the creatures'. At full strength it laid white glints over
glossy props such as the iron torches, so it stays faint until indoor models get proper local shading.

The billboard pass skips sprites a model draws. Water reflections draw the models too.

**Picking.** Indoors and outdoors, `DecorationModelSet::raycast` tests a model's LOD1 triangles. Camera-facing
cards are turned toward the ray origin first (`facingCardCorner`, the same turn as `modelStaticPosition`), so a
flame picks where it is drawn. Indoors, the coarse entity box is skipped for entities drawn by a model.

**Animated materials.** `openyamm_flipbook` (fire), `openyamm_uv_scroll` (water, foam), `openyamm_flutter` (flags),
`openyamm_wind` (foliage) and `openyamm_pulse: [amplitude, period]` (glow; the emission scaled by
`1 + amplitude * sin(2 pi t / period + phase)`, carried to `fs_model` in `v_flowInfo.a`). All of them use the
per-placement phase from the placement position, so neighbours do not move in step.

**Measured.** Pyramid (`pyramid.blv`), 445 model placements, a torch hall at 1600 x 900, vsync off. Only one game
instance ran during each measurement.
- Render CPU time is unchanged: the decoration sprite pass drops from about 55 to 8 us, and the models add about
  25-35 us.
- Median FPS was 863 with sprites and 840 with models in the clean pair. An earlier pair measured 921 and 781;
  frame-rate noise between runs is about that size.
