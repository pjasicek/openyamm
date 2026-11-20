# 3D model rendering: what we stand on

State of 2026-10-08 (emission and creature bloom: 2026-10-22). This document covers glTF creatures (skinned actors),
their carried items, and static decoration models: the asset contract, the build post-processes, how `ModelRenderer`
draws them, and how to make a variant such as a boss. Keep it in step with the code. If a statement here disagrees with the code, the code wins;
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
| Emission | glTF `emissiveFactor` (times `KHR_materials_emissive_strength`, up to 16) and `emissiveTexture` (sRGB, UV0; cooked as a colour map), per material and so per tier variant; `extras.openyamm_bloom` and `openyamm_pulse` on creatures. See "Emission and bloom" in section 4. |
| Specular | `extras.openyamm_specular` (0..1; 0 skips sky reflection and specular lobes). `extras.openyamm_specular_mask: true` multiplies it per texel by the metallic-roughness texture's red channel, which glTF leaves unused. It lets a matte head and glossy armour share one material. |
| Normal maps | glTF convention: +x along +u, +y up the image (against +v), tangent space from screen derivatives (no TANGENT attribute needed; the frame's sign is divided out, so OpenGL and Vulkan agree). Meshy's retexture returns +y-down maps: `tools/normal_map_convention.py` measures each map (slope integrability) and inverts green, run by `tools/prepare_actor_glb.py` and `tools/link_static_model_lods.py`; `--check` audits installed GLBs. |
| Static decoration extras | `openyamm_wind`, `openyamm_billboard`, `openyamm_translucency`, `openyamm_uv_scroll`, `openyamm_flipbook`, `openyamm_flutter`; COLOR_0 multiplies the base colour (`engine/models/ModelAsset.h` documents each). |
| Creature texture scroll | `openyamm_uv_scroll` also scrolls creature (skinned) materials: `u_modelScroll` in `vs_model` and `vs_model_skinned_instanced`, wrapped to one texture period, on the clock `render()` is given. The air elemental (`mm6_aie1`) spins its wind with it, so the spin stays continuous across clip changes. A blended creature primitive keeps its authored triangle order, which is its draw order. |
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
- **When actor models load.** Preloaded, not on first sight: building a binding costs about 20–100 ms per model
  (GLB parse and cooked texture upload; 2026-10-15, 88 MM6 actor GLBs, median 29 ms), and a first-sight load would
  stall combat for that long. `MapAssetLoader` lists the map's model descriptors (`ActorPreviewBillboardSet::
  modelDescriptors`: placed and saved actors, spawn points, and every tier of all three encounter slots, which event
  scripts may summon). `GameApplication::prepareGameplayRendering` builds them and creates their instances
  (`syncActorModels`) before its render passes, so both the load and the GPU upload happen under the loading screen.
  Monsters outside that list still load on first sight: summoned wisps (rare, by choice), actor-behaviour `summon()`
  ids, and arena fighters.
- **Static stand-ins (corpses).** `ModelInstanceSystem::setStaticStandIn(handle, asset)` replaces an instance's own
  skinned draws with a static asset placed at its root transform; the instance keeps its pose, bounds, picking and
  attachments. `WorldFxSystem` sets it when an actor is dead, its death clip has finished and its Dead clip is held
  (past its end, or the corpse's clock stopped: dead actors are not updated). The stand-in is
  `bakeStaticModelPose` (`engine/models/ModelAnimation.h`) of that held pose, baked once per model, Dead clip and
  held time on the first corpse: every mesh node with its colour and shadow LOD chains skinned and morphed into
  asset space on identity nodes, with the source's materials and images (so GPU textures are shared). A baked node
  must carry an identity `matrix`, because poses read `node.matrix`, not the TRS.
  An optional third argument, `minimumPixels`, hides the stand-in in colour views wherever its projected bounds are
  smaller than that on screen. Ground items use 8: in a dump of every item (save ITEMS_1, about 900 items in view to
  the horizon), it took 1407 draws to 1039 and 300 to about 410 FPS at 1600x900, losing only part of the band of
  items along the horizon under the fog. Their models have no LOD chain, so the items that remain drawn still cost
  full detail. Corpses, satchels and projectiles draw at every size.
- **Loot satchels (always on).** Once a slain creature's body is at rest (model: its baked
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
  show their satchels at once.
- **Projectile models (2026-10-16).** `engine/models/projectiles.yml` binds a model to a projectile object id
  (`object_list.txt` ObjectId) with its length in world units and an optional spin about the model's forward, up or
  side axis; the model points along glTF +Z with its origin at the projectile's centre.
  `WorldFxSystem::syncProjectileModels` keeps one static stand-in instance per flying projectile (so flipbook and
  additive materials work), turned by yaw then pitch along its velocity and then by its spin, at the effect anchor
  (`projectileRecipeAnchorOffset`) so it lines up with the enhanced trail; a settled projectile lies level and still.
  Bound projectiles draw no native sprite in either projectile style, and the map loader no longer preloads the
  sprites of unpickable bound objects; indoors the models follow the portal-revealed sectors. Every solid projectile
  is bound (arrows, cannonball, rocks, ice shards, blades, shrapnel, Fire Spike, Flying Fist, Starburst, meteors,
  thrown items); their flight sprites are archived (`level_generation/props/projectiles_claude/README.md`).
- **Inspect portrait.** The actor inspect popup shows a modelled actor's model instead of its sprite
  (`game/render/ActorModelPreview`). `WorldFxSystem::syncInspectPortrait` keeps a hidden copy of the actor's model
  (same skin and attachments) at the origin, which no world, shadow or reflection pass draws. On the popup's clock it
  plays the sprite preview's demonstration: fidget, then standing, then a fidget or an attack by the monster's inspect
  attack chance. Its camera is framed once from the per-joint boxes of the demonstrated poses (a swung weapon may reach
  past the edge). `ModelRenderer::renderPortrait` draws that one instance at LOD 0 into a small offscreen target
  (`ActorPortraitView`, ordered before the HUD view), without sun shadows, hover outlines or a change of the world's sky
  environment and LOD state. The copy is released on the first frame after the popup closes; actors without a model
  keep their sprite.
- **Ambient particle effects.** An actor binding can set `ambient_effect: {id: mm8:fx/wisp_stars, radius: 48}`.
  The named effect follows the model origin at the tier's relative scale while alive, visible and within 4096 world
  units. It repeats its emission cycle while the previous cycle's particles drain; death, hiding and removal stop
  emission, and teleporting clears the active cycle. The radius is the full particle extent in reference-tier world
  units for portrait framing. Inspect portraits simulate the same effect on their own clock and draw it into their
  target, separately from world particles. Additive stars sharing a texture batch across creatures in `EffectRenderer`;
  each star is a camera-facing quad, with an additional glow pass when bloom is active. Wisp's bounded-count, pause,
  repeat, hidden/death drain and portrait coverage is in `mm8_wisp_actor_models_keep_sizes_effects_and_empty_corpse`.

```yaml
- descriptor: Necromancer A                # monster table name
  model: worlds/mm6/models/mm6_pmn2.glb
  scale: 140                               # model units; scale_reference: <descriptor> scales by sprite ratio
  skin: pmn2_d                             # tier (KHR_materials_variants name)
  attachments:                             # rigid items on nodes of the model
    - model: worlds/mm6/models/mm6_pmn2_artifact_staff.glb
      node: Staff
  animation:
    sockets:                               # named points: a node, or a node plus an offset in its space
      staff_head: Socket_Staff_Head
      palm_left: Socket_Palm_Left
      tip: {node: Staff, offset: [0, 0.82, 0]}
    events:                                # optional action markers and charge sockets, see below
      attack_ranged:
        impact: 0.75
        glow: [staff_head]                 # the element charges here; the missile leaves here
        effects: {Dark: openyamm:fx/creature_dark_staff}   # named effect instead of the glow, per element
      cast: {impact: 0.75, glow: [staff_head], color: [176, 70, 255]}   # colour instead of the projectile's
      attack_melee: {impact: 0.70}
    look: {nodes: [neck, Head], max_yaw_degrees: 60, max_pitch_degrees: 35}   # optional head turn, see below
    # also: cast, run, stride_length, run_stride_length, sprint + sprint_stride_length (optional faster gait),
    # gait_rate, upper_body_root, eye_color (sockets eye_left/eye_right); gaits: CREATURE_POSTPROCESS.md step 3
  clips: {standing: …, walking: …, attack_melee: …, attack_ranged: …, hit: …, dying: …, dead: …, fidget: …}
```

**Aim height.** The party aims at 60 % of a monster's collision height, or 60 % up its bound model when the model is
shorter (MM8's Bone Dragon: 450 tall, its model about 166), so shots meet the body rather than the air above it
(`actorTargetHeight`, `GameplayRuntimeActorState::targetHeight`). The model's height is its bind pose from the file's
JSON (`Engine::readGltfModelSummary`), with the binding's `scale`, `scale_reference` and `z_offset` and the actor's
own scale; hits still test the collision cylinder.

**Action timing (`animation.events`).** Gameplay never follows a posed model, but it reads the bindings' data
(`resolveActorAttackTiming`, `ActorModelManifest::attackClips`): an attack or cast lasts the native sprite action, and
the game applies it (the melee hit lands, the missile or spell is released) when the sprite's authored contact frame
appears (`engine/rendering/sprite_attack_timing.yml`); for a sprite without one, at the binding's `impact` key when it
falls within the action, else when the whole sprite animation has played, as MM8 does (`re_mm8/ACTOR_ATTACK_TIMING.md`).
A manifest whose clips are its monsters' native timing (MM9's: top-level `attack_timing: clip`) instead lasts the
clip and applies at its key, over any stand-in sprite (lengths read from the model file's JSON,
`Engine::readGltfModelSummary`). The monster table's recovery runs from the action's start, exactly as for the
sprite (MM9's loops from the clip's end). A model clip may keep its own, longer timing (a mocap or library clip at
its intended speed): its event `impact` is the clip time of the moment the game acts (the blow lands, the staff or bow
releases). `WorldFxSystem` fits the clip's wind-up `[0, impact]` to the native time until that moment, so that frame
plays exactly when the game acts (`GameplayRuntimeActorState::attackImpactLeadSeconds` is the action time still to
run). The rest of the clip plays at its own speed: through the rest of the action (whole body), then as
follow-through: the whole body while the actor stands, the upper body over the gait while it walks (needs
`upper_body_root`; a binding without one attacks with its whole body, moving or not, as MM9's plain animator). A hit,
death (a 0.1 s blend unless `death_blend_seconds` says otherwise), script or the next attack cuts it with the usual
blend. Author the wind-up close to
that native time (stretching beyond about ±20 % shows) and keep the follow-through within the monster's recovery
(MM6 cleric: 0.75 s action, 1.33-1.5 s recovery). Without a marker, a clip runs on the action clock and is cut when
the action ends. The contact frames and markers are picked in `level_generation/creatures/timing_review/`.

**Charge and release sockets (ranged attack and cast events).** `glow` lists one to four sockets where the
projectile's charge forms while the action winds up: both palms, a staff head, an eye or a mouth. It goes out with a
burst of sparks when the action releases. `release` is where the missile or spell leaves, indoors and outdoors
(`WorldFxSystem::actorLaunchPoint`). Without it, the projectile leaves the single glow socket, or the middle of
several (between the palms). Sprite actors, models without either key, and points found away from the body keep the
body origin. The charge colour comes from the projectile the action releases:
- a spell's recipe;
- a missile token through `monster_projectiles.txt` and its object (an Energy robot's blaster);
- with the enhanced projectile style, the flight light of that monster's projectile binding.

`color` overrides it, and `glow_scale` sizes the glow. A melee attack event may also name `glow` sockets (with
`glow_scale`; no `release`): the blow charges there during its wind-up and goes out with sparks as it lands. It launches
nothing, so its glow is drawn only in its own `color`, which the loader requires (`attack_melee: {impact: 0.7,
glow: [fist], color: [255, 120, 40]}`). A physical missile (arrow, rock) charges only when it has a
`color`. On a ranged attack, `effects` maps a missile element to a named effect drawn at the glow sockets instead of the
glow. The sockets are placed in `level_generation/creatures/timing_review/`. Regressions:
`mm6_cleric_actor_marked_attack_fits_the_action_and_follows_through`,
`mm6_cleric_actor_ranged_attack_launches_from_staff_head`.

**Fidget and death past the native length.** The AI ends a fidget (Bored) after the native sprite length; a longer
fidget clip then plays to its end while the actor stands, through the same follow-through path (presentation only:
the AI's timing is unchanged). Walking, an attack, a hit, death or a script cuts it with the usual blend. A fidget
mapped to the Standing or Walking loop just continues that loop. A death clip longer than the native death likewise
finishes before the Dead clip is held. Hit clips are still cut at the native length. Regression:
`mm6_skeleton_actor_fidget_clip_plays_past_the_native_fidget`.

**Back-face culling of hidden triangles** (a geometry pass of the model cook: `tools/cook_model_geometry.py`, ray tests in
`tools/CookModelGeometry.cpp`). Creature exports (Meshy and similar) mark every material double-sided, so the GPU
rasterizes and shades every back face that draws before the surface covering it. The cook casts 64 rays from just
behind each triangle of an opaque double-sided primitive over its back hemisphere (up to 89° from the reversed normal:
thin tubes along a membrane show their backs at grazing angles). A triangle whose rays all hit an opaque surface of the
same mesh cannot show its back to any outside viewer in the bind pose. The primitive then draws with a single-sided
copy of its material (and of every KHR_materials_variants tier material), and each triangle whose back can be seen
(capes, wings, skirts, open sleeves and necks) gets a reversed copy on duplicated vertices with negated normals, as
two-sided cloth is usually modelled. Each primitive stays one draw in its slot. A primitive where more than a quarter
of the triangles show their back keeps its double-sided material (cheaper than the copies; the demon's sheet-like LOD
meshes). Alpha-tested and blended primitives and the dedicated shadow meshes are unchanged. Over 40 MM6 creatures:
about 90 % of the checked triangles single-sided, +5 % triangles. Corridor of swordsmen (`saves/save40.oysav`): main
view about 505 → 440 µs, creature CPU unchanged (a first layout with a separate double-sided primitive doubled the
draws and cost about 40 µs of main thread); outdoor reference poses unchanged. Blender renders from nine directions
match the originals within edge noise (a forced single-sided material opened up to 3,300 pixels: bat wings, robes and
skirts seen from below). About 8 s per creature in the first (Blender) version of the pass.
Until the switch to cooked models, `tools/install_model.py` applies the same pass to the uncooked runtime copy in
`assets_dev` (`tools/model_backface_split.py`, marked `asset.extras.openyamm_backface_split`; 0.25 s per creature);
the sources in `assets_source` stay unprocessed, and the cook applies the pass itself (ASSET_COOKING_PLAN.md §12).

**Foliage depth order** (`ModelRenderer::submitStatic`). Static batches are drawn nearest first (by their nearest
placement), not only the placements inside each batch, so one species' crowns reject the leaves of the species behind
them. The opaque, non-billboard primitives of every batch that has alpha-tested leaves (inner crown shells, trunks)
are drawn into the depth prepass before the leaves, so the cards they hide fail the depth test before their alpha
test runs; their shaded pass then draws at the same depth with the same program. Blended primitives are shaded back
to front (2026-10-16, the MM8 foliage overdraw pass). Alpha-tested leaves are shaded by `fs_model_prepassed` after
their prepass, and that variant skips the normal map and the sky reflection: on leaf cards neither shows, and leaves
fill much of a forest view. Measured in the dense out07 view (frozen, desktop), the frame went 0.83 -> 0.80 ms; there
the leaves cost about 0.34 ms (depth prepass about 0.12, shading about 0.22), and dropping the prepass would add about
0.25 ms.

**Blended skins** sort by where the primitive's main joint (`anchorJoint`, most vertex weight) carries its centre this frame, so a swinging limb or a flying head keeps the right layer.

**Static blended order** (`ModelRenderer::renderStatic`). Blended primitives (flames, glows) write no depth, so they
are shaded in a second pass after every opaque and alpha-tested primitive of the static decorations. Before that,
alpha-tested foliage shaded later (equal depth after its prepass) painted over a flame in front of it whenever the
blended draws shared the world view, which they do without ambient occlusion (2026-10-16, the MM8 beacons among palms).

**Vertex cache order** (`GltfModelLoader`). Every loaded triangle primitive except blended materials is reordered
for the GPU's post-transform vertex cache (`meshopt_optimizeVertexCacheFifo`, meshoptimizer from bgfx's `3rdparty`).
Over all models the vertex shader ran about 1.46 times per vertex, now about 1.03; in the corridor below the main view
went 606 → ~540 µs. Reordering every model in the game takes about 70 ms on the desktop (a map loads a fraction). Blended materials keep their authored triangle order, which is also their draw order. Cooked models are ordered by the cook
(`asset.extras.openyamm_cooked.geometry.vertex_cache`) and skip it at load.

**Animation rate** (`WorldFxSystem::syncActorModels`). Each actor samples its clips at most 240 times a second,
60 beyond 750 units, 15 beyond 1500 and 8 (the native sprite rate) beyond 3000, each on its own phase (with
`video.model_lods`). Transition blends advance in the same steps (`ModelInstanceSystem::sampleBlended`,
`blendStepSeconds`). Root motion stays per frame and only recomposes the joint hierarchy. Pose evaluation was about
30 % of the main thread with the swordsman crowd at ~1000 FPS, mostly from fights starting about 240 transitions a
second; it is now about 12 %. Local matrices are composed once, after the layer and transition blends.

**Head look (`animation.look`).** The listed nodes, root to tip (neck, head), turn toward the party's eyes
(`IGameplayWorldRuntime::partyEyeZ`: the indoor camera eye or the outdoor world's `partyMovement.eyeHeight`) over every
clip except death, scripts and the corpse. The turn is relative to the body's facing, seen from the last node's rest
height above the feet, clamped to the limits, shared equally between the nodes and eased in and out over about
0.2 s. It fades back to the clip's own head when the party is more than 20° outside the yaw limit (behind the actor)
or beyond 2048 units. It is decided and applied at most 30 times a second per actor (15 beyond the 1500-unit
animation LOD distance), each actor on its own phase, and costs nothing while the head rests. `ModelInstanceSystem::setNodeRotations` applies such post-clip world rotations about each node's pivot to
its subtree, so attachments and sockets follow. Regression: `mm6_cleric_actor_head_turns_toward_the_party`.

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

**Creature depth prepass** (`ModelRenderer::render`, `OpaquePass`). Opaque creature draws (instanced and single) at
colour LOD 0 first write only depth, then shade with an equal-depth test and no depth write, so each pixel is lit
once. Smaller creatures draw in one pass: their second pass over the geometry cost more than it saved (including
LOD 1 cost about 35 µs in the corridor below; all levels cost up to 29 µs outdoors). Creature
materials are double-sided and creatures overlap each other, and their lighting is the costly part: in a corridor of
about 30 swordsmen and their 3D guards (`saves/save40.oysav`, MM6 `6d12.blv`) the main view takes 578 instead of
775 µs of GPU. Forcing single-sided culling saved about as much, but would open thin cloth. With the prepass, point
lights' specular costs nothing measurable. The depth pass sets outline flag 2: `vs_model.sc` keeps the surface in
place (1 is the hover outline shell, which is pushed out) and `fs_model.sc` returns right after the alpha test. Both
passes run the same programs, so their depths match exactly. Every skinned draw's palette rows are allocated before
either pass is submitted: a palette growth between the passes would leave the shaded pass reading rows never written
to the new texture. Water reflections draw in one pass.

**Creature contour** (`drawsContour`, `submitContour`). Every opaque material with edge darkening (creature skins)
draws an inverted hull right after its body, in both the instanced and the single paths: back faces only, pushed out
along the screen-space normal by `CreatureContourPixels` (1.5 per 1080 view rows, at least one pixel) and written with
depth, so only the rim past the silhouette and along limbs crossing the body survive. Its colour is the albedo times
`CreatureContourDarkness` (0.25) of the ambient light, fogged, unlit and without emission (outline flag 3 in
`fs_model.sc`). It repeats the body's vertex work (skinning) and costs little fill. Reflection passes, attachments and
static stand-ins draw none. Off by default: `[video] creature_outlines=true` in `settings.ini` (or
`render creature_outlines on`) turns it on.

**Burning creatures** (`ModelBurn`, `ModelInstanceSystem::setBurn`, `bindBurn`; actors.yml `death_effect: burn`).
Each skinned material carries a linear burn map (`extras.openyamm_burn_map`, made by
`level_generation/creatures/claude_shared/burn_maps.py`): red orders the surface (0 burns first), green drives glowing
cracks. The cook bakes the red channel at each vertex into a `_BURN_ORDER` vertex attribute
(`tools/cook_model_geometry.py`), which `WorldFxSystem::buildActorBurnSurface` reads to place the flames on the CPU;
the burn map itself cooks like any other texture (BC5 desktop, EAC RG android) and only the shaders sample it. A
burning model must therefore be cooked; an uncooked one fails its binding. One front per instance sweeps that order. In `fs_model.sc` texels within the char width ahead of the front
darken towards black with glowing cracks, a narrow edge glows brightest where the hole begins, and texels past the edge
are discarded; `fs_model_shadow.sc` discards the same texels. A second pass of the same skinned draw
(`submitBurnFire`, burn pass 2) shades only the freshly burnt texels, for the fire width behind the edge, as rising
world-space noise strongest at the silhouette, premultiplied over the scene without depth writes and with both faces:
the body briefly remains a shape of fire. A burning draw keeps its own draw (no instancing, no depth prepass, no
contour), casts from its colour meshes (a merged shadow mesh has one material and so one burn map), and stops drawing
and releases its palette rows once the front passes `1 + edge + fire`. `u_modelBurn` is set on every draw because
uniforms persist between draws. The emission colour is linear: fire orange is about `[1.0, 0.18, 0.02]`.
After the burn completes, picking uses only visible attachment bounds (for example, Wyrm charred remains),
or the loot satchel when present; the vanished body is no longer pickable.

**Energy shield shells** (`ModelShieldShell`, `ModelInstanceSystem::setShieldShell`, `submitShieldShell`; game side:
`devdocs/ENERGY_SHIELDS_AND_RELATIONS.md`). An instance with a shell draws each skinned or CPU-deformed draw once more
after the scene's blended parts, with `vs_model_shield`/`fs_model_shield`: pushed out along the normals, additive,
both faces, depth-tested without depth writes, and again into the glow view at 45 % when bloom runs; also in the
inspect portrait. The program loads on the first shielded draw; without shells nothing is submitted and the existing
programs are unchanged (all shader binaries compared identical, 2026-10-23). Creatures stay instanced: the shell is
an extra single draw.

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
× `ambient`, `direct` = sun visibility, up to 12 uniform point lights). Instanced paths keep the shared terms
in uniforms and move the per-model terms into instance data (`v_color0`), so a batch needs only one uniform set.

**Light grid** (`pLightGrid`, phases 3 and 4 of
[the lighting and materials plan](../../docs/LIGHTING_AND_MATERIALS_ARCHITECTURE.md), 2026-10-16). In the main view
a model's point lights come from a clustered grid instead of the uniform list (`engine/render/LightGrid.h`,
`game/shaders/light_grid.sh`). Each frame the CPU bins the frame's lights into view tiles × logarithmic depth slices
(`video.light_grid`: high 16×9×24 cells, 32 lights per cell; low, the Android default, 8×5×16 and 16), out to 4,096
units indoors and 8,192 outdoors, with lights fading over the last 15 %. Dynamic lights (torch, spells, effects) are
binned ahead of static ones, so a full cell drops static lights first. The result is one point-sampled RGBA32F texture,
64 texels wide (light data at 3 texels per light, then the cells, then the index list), read with `texelFetch` at
stage 11, plus `u_lightGrid`; `LightGridBinding` binds both for a draw (`ModelRenderer::bindLightGrid` for models). A
fragment loops over only its own cell's lights. Indoors the grid holds the lighting frame's lights, outdoors the
object runtime lights (authored and dynamic) × `OutdoorFxLightingScale`. A grid without lights is not uploaded or
bound, so lightless outdoor scenes run the old path. Creatures read full lighting from it; instanced batches compare
the grid pointer, so point-lit creatures indoors now instance like outdoor ones. Reflection passes, the editor and
terrain bushes keep the uniform list (`creatureModelLighting(..., selectPointLights)` selects it for the water
reflection). World geometry reads the same grid (BLV faces, terrain, buildings; see the plan's section 12). Console
`render light_grid off` empties it for A/B profiling.

**Room of a model** (`ModelRenderLighting::sector`, `ModelStaticPlacement::sector`, phase 5). Indoors a grid light
lights a model only when its reach (the rooms it lights through portals) holds the model's sector, so light no longer
passes through walls. The sector reaches the fragment shader as `v_sector`: skinned instances in `i_data1.x`, static
placements packed with the LOD crossfade as `i_data4.w = crossfade + 4 × (sector + 1)` (decoded in
`vs_model_instanced`), single draws in `u_modelSector`; -1 (outdoors) takes every light. The indoor renderer gives a
creature its sector (cached per instance, resampled after it moves 16 units) and that room's ambient through the
per-model lighting callback; both are instance data, so creatures still draw instanced. Decorations take their
billboard's sector, and carried items their carrier's.

**Bloom glow** (`setGlowView`, `u_modelGlow`, phase 7 of the lighting plan). When the grading pass runs bloom,
`renderStatic` submits each emitting primitive a second time into the glow view, with the same bindings
(`BGFX_DISCARD_NONE`), the alpha-tested program and an additive state over the world depth: blended flame and glow
cards (additive, unlit or flipbook materials) with their display colour times a weight (0.45 for additive cards,
whose flipbooks already include a halo; 0.8 for blended flames), other emissive materials with their emission and
pulse. `fs_model` returns the glow right after the fog, so cards still fade in fog and so does their bloom. Creature
materials glow only when they opt in (below).

**Emission and bloom** (2026-10-22, opt-in from data; Hesper's energy parts). How it works:
- *Emission.* `ModelMaterial::emissive` is the glTF `emissiveFactor` times `KHR_materials_emissive_strength`; the
  loader reads both for every material, static or skinned. `fs_model` adds it unlit after the lighting, the edge
  darkening and before the SDR shoulder and fog (`u_modelSurface.xyz`, times `v_flowInfo.a`: a static placement's
  `openyamm_pulse`/`openyamm_flicker` from `vs_model_instanced`, 1 for creatures). The contour shell emits nothing.
  This was already so for factor-only emission on creatures (the MM6 robot's eye, `mm6_rob1`: the only emitting
  creature material of MM6-MM8) and static models (196 materials: satchel gems, braziers, crystals).
- *Emissive texture* (`emissiveImageIndex`, new). Desktop and Android share the shader source: `fs_model.sc` compiled
  with `MODEL_EMISSIVE_MAP=1` is `fs_model_emissive.bin` (every shader profile: glsl, essl, spirv), which multiplies the
  emission by `s_modelEmissive` (stage 7). `ModelRenderer` draws a material with that program (single draws,
  instanced creatures, static placements, the glow pass) only when the material has an emissive texture, and binds
  stage 7 only then. The three programs load the first time a model with an emissive texture is prepared
  (`setEmissiveProgramLoader`, set by the indoor and outdoor renderers); a renderer without a loader (terrain
  bushes) gives such a texture no emission rather than lighting the whole material. Every other draw keeps its
  program, bindings and uniforms: `fs_model.bin`, `fs_model_prepassed.bin` and `fs_model_coverage.bin` compile to
  the same bytes as before (checked for glsl and essl: the default variant preprocesses to the same source). An
  emissive alpha-tested static material shades with the emissive program after its depth prepass (alpha test
  repeated at equal depth, normal map and sky reflection kept).
- *Bloom* (`video.bloom`; `CinematicGrading::glowView`). Static emitters glow whenever they emit, as before. A
  creature (skinned) material draws into the glow view only with `ModelMaterial::bloom`: true with an emissive
  texture, otherwise only with the extra `openyamm_bloom: true` (false opts a textured one out), so `mm6_rob1`'s eye
  keeps its unbloomed look. The glow is a second submission of the same colour draw (`BGFX_DISCARD_NONE`,
  `submitCreatureGlow`): single draws and instanced runs alike, before the contour shell; not in reflections or
  inspect portraits (the portrait shows the emission without bloom). Burning emitters glow with their burn too. With
  bloom off, or no emitter in view, nothing is submitted and the bloom chain is skipped (`glowDrawn`).
- *Tiers.* Each `KHR_materials_variants` material carries its own factor (and may name its own texture), so tiers
  share one mask and glow in different colours. Corpses (`bakeStaticModelPose`) and split attachments are static
  models with the same materials: they glow as statics do.
- *Pulse on creatures.* `openyamm_pulse` / `openyamm_flicker` scale a creature material's emission on the CPU
  (`modelCreaturePulse` in `ModelAsset.h`, the static shader's formula at phase 0, on the creature clock), in the
  factor uploaded per draw: every creature of a material pulses in step, instanced or not.
- *Cook.* `tools/cook_models.py` cooks an `emissiveTexture` as an sRGB colour map of the model's quality (desktop
  BC1/BC7, Android ETC2; flat maps shrink like colour maps); before it rejected the slot. Models without one plan
  and cook exactly as before (all 1,657 source models compared, 2026-10-22).
- *In use* (Hesper stage only): the acid crawlers (`hes_crawler_claude`: grey acid mask, one factor per tier, pulse)
  and the Landfall turrets (`hes_turrets_claude`: the `_Energy` material's own base colour map as its emissive
  texture, so the glow costs no extra texture; the cook shares the cooked map).
- *Authoring:* `level_generation/creatures/CLAUDE_CREATURE_TEXTURES.md` ("Emission") and
  `level_generation/creatures/claude_shared/emission.py`. The three.js review viewers show emissive maps as they are
  (MeshStandardMaterial), without bloom.

**Highlights on static models** (`pointSpecularOnly`, 2026-10-16). Indoors, a decoration placement's light is the
light its sprite would receive, which already includes the nearby torches' diffuse share, and the sky reflection is
the wrong environment there. With `pointSpecularOnly` the point lights add only their GGX specular lobe
(`modelSpecular` in `fs_model.sc`: grid mode 2, or a negative uniform point count without a grid). It is added after
the display-space scaling by the light level, since a highlight reflects the light itself. Metal props catch the
torches' coloured highlights; matte and rough surfaces barely change, and materials without specular skip the grid
loop. Both indoor and outdoor decorations take their highlights from the grid in the main view, so braziers and
lanterns light nearby metal at night. Without a grid the indoor renderer still passes one set per `renderStatic`
call: up to 12 lights within `IndoorDecorationHighlightReach` of the camera (`selectDrawLightSetForBounds`).

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
4. Test: spawn the bound descriptor with `actor spawn <id> 1 <x> <y> <z>` and
   `debug.actor_models=true debug.immortal=true`. The boss mage demo above (Necromancer A, 307) was unbound on
   2026-10-21: that descriptor is MM7's own Necromancer, and the tier, artifact staff and `bosses/necro_mage`
   behaviour are kept for a future boss. Regression: `mm6_pmn2_actor_models_bind_free_haven_mages` checks
   the four tiers of one skin and that every mage carries its staff on the Staff bone.

## 6. Profiling switches and measured state

Console `render <switch> on|off|toggle`. Layers: `terrain`, `bmodels`, `sky`, `water`, `grass`, `deco_models`,
`deco_sprites`, `actors`, `creature_models`, `effects`. Settings: `foliage`, `instancing`, `shadows`, `ao`,
`grading`, `model_lods`, `lightmaps`, `creature_outlines`, `light_grid` (off: no point lights from the grid), `freeze`,
`hud` (off: gameplay draws only the world, for clean captures). `render lod <-1..3>` forces a LOD. Every change logs
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
stale; the game loads them without checking. Re-bake what `tools/lighting/stale_bakes.py` lists before a release
(`tools/lighting/baked_outdoors/README.md`).
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
- `turn_in: [degrees, seconds]` makes a switched-to model turn into its pose: when an event's `SetSprite` moves a
  placed decoration to this binding during play, `DecorationModelSet::animate` turns it from `-degrees` back to its
  own pose about the asset z axis (its front axis: a valve wheel's axle) through the centre of its bounds, easing in
  and out. A decoration placed at load, or switched before the first update (a map's load event restoring its state),
  stands in the pose at once. Hesper's valves use it (`hes_valve_wheel_turned`).
- `still: true` records that a natively animated sprite is drawn by a still model. The regression
  `mm6_decoration_models_keep_native_animation` fails for an animated sprite whose model has no flipbook, uv scroll,
  flutter, wind, pulse or swing.

**State overlays.** `worlds/<world>/models/decoration_overlays.yml` (shared by indoor and outdoor maps) gives a bound
decoration one more model per interactive decoration state (the decor var a barrel or cauldron event steps through),
`null` for none. The overlay is authored in the decoration model's asset space and drawn in its own group with the
decoration's placement matrix. It is never picked or outlined, and it hides with the decoration. It lives apart from
`decorations.yml` so that adding one leaves the outdoor bakes current (overlays cast no baked shadow). The MM6 stat
barrels use it for their liquids: `mm6_deco_barrel_liquid_<colour>.glb` for states 1–7, removed once drunk.

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
cards are turned toward the ray origin first (`facingCardCorner`, the same turn as `modelStaticPosition`, about the
same pivot: the model origin, or a `"card"` billboard's own centre), so a flame picks where it is drawn. Indoors, the coarse entity box is skipped for entities drawn by a model.

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
