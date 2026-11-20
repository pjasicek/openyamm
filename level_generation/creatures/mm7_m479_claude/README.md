# MM7 Treant (m479) — Claude 3D model, batch I

Treant A / B / C (monster ids 451 / 452 / 453, monster name "Tree"; sprite groups m480s/a/n/d/x, palette 530 for all
three). Batch I ([../mm7_batches/BATCH_I.md](../mm7_batches/BATCH_I.md)): the model stops at project exports; nothing
is installed or bound.

![attack impact in the review viewer](review/attack_impact.png)

| Item | Value |
|---|---|
| Export | `export/mm7_m479.glb` (LOD0–3 + shadow LODs, one material `M479`, no tier variants) |
| Editable sources | `work/rig_v4.blend` (rig, UVs, eyes, teeth bones), `work/anim_v1.blend` (rig + clips + UVs, exported), `export/mm7_m479_lod0.glb` |
| Triangles LOD0/1/2/3 | 13,591 / 6,794 / 2,420 / 728 |
| Skeleton | 30 bones: Root, Trunk1–3, Spire, Limb0–5 × 3, Jaw, UpperLip, TeethU, TeethL, Eye_L, Eye_R, Socket_Mouth |
| Clips (30 fps) | Standing 4.0 s loop, Attack 1.133 s (impact 0.6875 s), Hit 0.433 s, Death 0.9 s, Dead 1.0 s |
| Textures | one atlas: 2K base colour, 1K normal / ORM (R specular mask, G roughness); class map `textures/m479_material_classes.png`; no region mask (see Tiers) |
| Meshy credits | **25 of 100**: Smart Topology 5, retexture_v1 10 (superseded, see below), retexture_v2 10 |
| Viewer | `http://127.0.0.1:8912/level_generation/creatures/mm7_m479_claude/review/viewer/index.html` — check: 1 model × 5 clips, no console errors, failed [] |

## Native actions (what exists, and what was built)

The native set has 33 frames, one view (the same picture in every direction, no mirrors), 62.5 ms per frame
(`mm7_m479/manifest.json`, `descriptor_animations`):

| Native group | Frames | Built as |
|---|---|---|
| standing / walk / fidget = m480s | `m479sa0` only: the resting disguise, a plain tree with no face | `Standing` (one clip serves all three) |
| attack / shoot = m480a | 18 frames ab0–as0, 1.125 s | `Attack` (melee and the ranged Earth missile) |
| hit = m480n | 7 frames na0–ng0, 0.4375 s | `Hit` |
| death = m480d | da0–dd0 (0.25 s; de0/df0 exist but are not played) | `Death` 0.9 s (the engine finishes a longer death before Dead) |
| corpse = m480x | `m479xa0`, a toothed stump | `Dead` = last Death pose held |

No Walking, Running or Fidget clip was invented: the monster is immobile (`stand`), and the natives reuse the standing
frame for walk and fidget.

## Anatomy decisions

- **Non-humanoid playbook, own rig.** A leafless tree: a flared trunk on a root skirt, a pointed spire, about seven
  antler-like limbs, and a face (two small green eyes, a wide toothed mouth) on the front only.
- **The Smart Topology return is a soup of ~140 loose strands** (bark ropes, root tendrils, limb pieces, twig tips) that
  overlap and touch everywhere. Heat weights or per-piece rigid binding would tear touching strands apart, so **every
  weight is a continuous field of position** (`rig_treant.py`): overlapping pieces at the same place get identical
  weights and move together.
- **Trunk chain** Root (0–0.3 m, the root skirt stays planted) → Trunk1 (mouth) → Trunk2 (eyes) → Trunk3 (where the limbs
  leave) → Spire; smooth height blends between them.
- **Six limb chains instead of one per limb.** The limbs are not separable pieces, so the crown is split into six
  sectors (azimuth 0, 60, …, 300°), each a three-bone chain from the trunk at 2.2 m out through the sector's limb mass
  (joints at the centroids 0.5 m and 1.0 m from the base). Crown weight = distance outside the trunk radius × height
  above 1.85 m; between sectors the weights blend linearly in azimuth, along a chain by distance from its base.
- **Roots do not move** (native roots are static): the skirt is on Root.
- **Mouth:** Meshy's 30 needle teeth (3 cm wide) were replaced by 19 peg teeth fitted to the same gum lines
  (`step2_teeth.py`; the native teeth are few broad pale pegs). Jaw (lower lip, piece 15, by height, less toward the
  corners) and UpperLip (lip arc above the opening) are translated to close/open the mouth. Teeth rows are on TeethU /
  TeethL (`teeth_bones.py`), scaled to 0.35 when the mouth closes so the corner teeth draw in behind the lips.
- **Eyes are our own geometry** (`eyes_add.py`): Meshy modelled none and painted none. Two almonds (0.19 × 0.11 m) on
  Eye_L / Eye_R at the position measured on the front HD master (z 1.80, x ±0.20), sunk 2.6 cm into the bark; the bones
  scale to 0.05 to sink them. Painted procedurally in their own UV square (green iris, slit pupil, dark rim, highlight).
- **The disguise:** Standing has the mouth closed (lip slit, teeth hidden) and the eyes sunk, as the native resting
  frame shows no face. Attack and Hit open both; the blend back to Standing closes them.
- **Root skirt reduced** (`reduce_roots.py`): the tendrils on the ground (faces below 0.35 m) held 6.6k of 17.3k
  triangles; collapse decimation of that region only at 0.5 → 13.6k total, no visible change (q3/4 and rear compared).

## Clips

- **Standing** 4 s loop: slow wind sway of the trunk (lean, side and twist, shared up the chain) and phase-shifted limb
  sways growing toward the tips.
- **Attack** (native ab–as): wakes (eyes open, mouth opens, 0–0.25 s), winds up leaning back to its right with the
  right-hand limbs drawn back (0.5 s), then a whip-lash lean forward to its left with every limb sweeping and pitching
  forward, the chains lagging base → tip (impact 0.6875 s = native frame ak0), recovering upright with the mouth open.
  The native frames bend the trunk sideways; the 3D lash is diagonal so it reads as a blow toward the party.
  `Socket_Mouth` is the ranged release point (Earth missile, attack 2).
- **Hit** (native na–ng): eyes open, mouth gapes, recoil back and a decaying limb shudder within the native 0.4375 s.
- **Death** (native da–dd: the tree bursts into splinters, corpse a toothed stump): a shudder, the six limb sectors snap
  outward, tumble and shrink to splinters while ending inside the collapsing top, the spire and Trunk3 collapse, and the
  trunk between 1.2 m and 1.9 m flattens (Trunk2 axial scale 0.18) onto a stump of about 1.4 m with the mouth bared.

## Route (replay, from the repository root, `T` = lease token)

1. HD masters (`references_hd/`, Codex: primary 00, gated, then 01–04 with 00 as first input; brief `CODEX_BRIEF.md`,
   records `generation_runs.json`); native frames through palette 530 (`scripts/native_palettes.py m479 530`).
2. Smart Topology 15k (`requests/smart_topology_v1.json`): 16,220 triangles, 140 pieces; `step1_clean.py` normalises
   the height to 4.0 m; `step2_teeth.py` (peg teeth) → `work/step2.blend`.
3. `rig_treant.py` → `work/rig_v1.blend`; `uv_export.py rig_v1 rig_v1u` (+ `texturing/m479_upload.glb`).
4. Retexture `requests/retexture_v2.json` (four HD views, our UVs); `eyes_add.py 0.2 1.8 -0.2 1.8` → rig_v2;
   `reduce_roots.py` → rig_v3; `teeth_bones.py` → rig_v4; `anim_treant.py rig_v4 anim_v1`.
5. `uv_raster.py rig_v4 2048 v2`, `uv_raster.py rig_v4 1024 v2`, `bake_ao.py rig_v4 2048`, `python3 compose_m479.py`.
6. `scripts/build_runtime.sh <T>`; viewer `viewer_tiers.py`, `update_viewer_manifest.py`; gates `gates.py anim_v1`.
Blender scripts run through `tools/run_creature_blender.sh --token <T> level_generation/creatures/mm7_m479_claude/scripts/<script>.py <args>`.

## Tiers

Descriptors 451–453 all draw sprite group m480 with palette 530 (native manifest: one variant, recolour `identity`,
masks zero). Every tier looks the same, so there is **one material and no region mask or ramps**, and the binding has
no `skin`. `scripts/set_extras.py` sets the extras the region-variants step would set (`openyamm_specular=1`,
`openyamm_specular_mask=true`, `pbr.metallicFactor=0`). A future recolour would need a mask (bark = everything but
teeth, eyes and mouth interior: classes 10 in the class map) and ramps.

## Textures

- Bark: Meshy retexture_v2 graded by the rest-pose AO, median scaled to the native median × 1.35 (77/59/40 vs native
  56/44/32) with half its chroma pulled to the native hue.
- Teeth repainted ivory, darker toward the gum (Meshy painted them tan); eyes painted procedurally; mouth interior ×0.8.
- Material classes: 10 wood, 5 tooth, 6 eye, 7 mouth interior (`compose_m479.py`).
- **retexture_v1 superseded:** the first unwrap (Smart UV + default bounding-box packing) put ~1,800 strand islands on
  13 % of the atlas. `uv_export.py` now uses angle 1.55 rad (1,439 islands), concave packing and margin 0.002 → 35 %
  coverage, and retexture_v2 was bought on that layout (correction ledger in `creature_3d_progress.json`).
- **Deviation (texel padding):** island margin is 0.002 (4 texels at 2K, 2 at 1K) instead of the guideline's 8 at 2K;
  with 1,439 strand islands the 8-texel margin left only 23 % coverage. All maps are dilated into the gutters; bark next
  to bark bleeds harmlessly; teeth and eyes have their own islands.

## Gates (`work/gates.json`, every frame of every clip)

| Clip | Floor min z | Max edge stretch | Limb clearance (bone segments) |
|---|---|---|---|
| Standing | −0.004 m (rest roots) | 1.83 (Trunk1: lower lip stretched closed) | 0.244 m (rest 0.246), margin +0.12 |
| Attack | −0.004 m | 1.83 (frame 0, closed lip) | 0.225 m (rest 0.250), margin +0.11 |
| Hit | −0.004 m | 1.83 (frame 0, closed lip) | 0.245 m, margin +0.13 |
| Death | −0.004 m | 2.36 (intended burst, Limb1_1) | not gated (burst) |
| Dead | −0.004 m | 1.84 (stump flattening) | not gated |

- Closed mouth (Standing): the lower lip's top is 4 cm above the lowest upper-tooth tip, teeth 24 cm behind the lip
  front. Winding: `check_winding.py export/mm7_m479.glb` → 0 inverted closed parts. GLB re-imported in a clean Blender
  (`reimport_check.py`): mesh M479 13,591 triangles, 1 UV set, material M479, clips Standing/Attack/Hit/Death/Dead.
- Viewer check: 5 clip switches, no console errors, failed []. Shots in `review/shots/`.

## For the user to review

- Motion is procedural and an interpretation of the native frames; the attack lash is diagonal (native: sideways).
- The disguise: closed mouth = the lower lip raised over the teeth (bark stretch up to 1.83× on the lip); a thin slit
  remains. Eyes sink fully.
- The death has no particle effect (`death_effect` unset): splinters are the limbs shrinking in flight. The stump is a
  smooth dome, not the native's jagged broken top.
- The bark reads paler in the three.js viewer than in Blender or the sprite (viewer lighting); check in game.
- The tree is huge in game: native height 231 px × frame scale 5 = 1155 units, while the descriptor's collision
  height is 199 and radius 112.

## Install later (not run)

**Reduced version:** [`../mm7_m479_reduce_claude/`](../mm7_m479_reduce_claude/README.md) (2026-10-20, 13,591 -> 10,325
triangles) — install its `export/mm7_m479.glb` instead of this one
(`python3 tools/install_model.py level_generation/creatures/mm7_m479_reduce_claude/export/mm7_m479.glb --world mm7`);
the binding below is unchanged.

```sh
python3 tools/install_model.py level_generation/creatures/mm7_m479_claude/export/mm7_m479.glb --world mm7
```

Binding for `assets_dev/worlds/mm7/models/actors.yml` (scale = native standing height 231 px (alpha bbox of
`m479sa0`) × frame scale 5.0 ÷ 4.004 m model height = 288.5; all tiers frame scale 5.0, one material, no `skin`):

```yaml
- descriptor: Treant A
  model: worlds/mm7/models/mm7_m479.glb
  scale: 288.5
  yaw_offset: -1.570796327
  animation:
    sockets:
      mouth: Socket_Mouth
    cast: Attack
    run: Standing
    stride_length: 1.0
    upper_body_root: Trunk2
    events:
      attack_melee: {impact: 0.6875}
      attack_ranged: {impact: 0.6875, release: mouth}
  clips:
    standing: Standing
    walking: Standing
    attack_melee: Attack
    attack_ranged: Attack
    hit: Hit
    dying: Death
    dead: Dead
    fidget: Standing
# Treant B / C: the same with scale_reference: Treant A
```

No in-game check was run (optional for batch I).
