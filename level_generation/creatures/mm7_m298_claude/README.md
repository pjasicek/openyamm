# MM7 Ooze (m298) — Claude 3D model, batch I

Emerald / Sapphire / Bloodstone Ooze (monsters 310–312, descriptors Ooze A/B/C, sprite groups m299/m300/m301,
palettes 299 green / 300 blue / 301 red, hit material Slime). Batch I ([../mm7_batches/BATCH_I.md](../mm7_batches/BATCH_I.md)):
the model stops at project exports; nothing is installed or bound.

![tiers in the review viewer above the native palettes](review/tiers_vs_native.png)
![clips in the review viewer](review/clips_viewer.png)

| Item | Value |
|---|---|
| Export | `export/mm7_m298.glb` (LOD0–3 + shadow LODs, three tier variants `m298_a/b/c` sharing every image, 8.2 MB) |
| Editable sources | `work/anim_v1.blend` (rig + clips + UVs, the master), `work/export_master.blend` (as exported: material, pod/glob UVs), `export/mm7_m298_lod0.glb` |
| Triangles LOD0/1/2/3 | 4,662 / 2,330 / 838 / 273 (blob 3,294 + pod 600 + 12 globules 768) |
| Skeleton | 30 bones + `Socket_Spit`: Root, Body, Lump_C, Lump_0–7, PodRoot, Pod1–5, Knob, Glob_00–11 |
| Clips (24 fps) | Standing 1.0 s, Walking 0.75 s, Running 0.5 s, Attack 1.25 s (impact 0.68 s), Cast 1.25 s (release 0.68 s), Hit 0.875 s, Death 0.625 s, Dead, Fidget 0.625 s |
| Textures | one atlas: 2K base colour, 1K normal / ORM (R specular mask, G roughness 0.42) / region mask; one region (slime) |
| Meshy credits | **15 of 100**: Smart Topology 5, retexture 10 (our UVs) |
| Viewer | `http://127.0.0.1:8912/level_generation/creatures/mm7_m298_claude/review/viewer/index.html` — `check`: 3 tiers × 9 clips (27 switches), no console errors, failed [] |

## Route (non-humanoid playbook, replay from the repository root)

1. Native frames through the three palettes: `python3 <P>/scripts/native_palettes.py m298 299 300 301`
   (`references/native_variants/`), reference sheets in `references_hd/native_*.png`.
2. HD masters (`references_hd/`, Codex, `CODEX_BRIEF.md`, landscape 1536×1024): `00_three_quarter` first (one
   corrective regeneration by Codex), gated, then 01–04 with 00 as input 1. Gate: very dark glossy green wormy slime,
   flat proportions, same blob in all five; lobe-level agreement between the views is approximate (accepted for an
   amorphous blob). Faint alpha < 32 zeroed; untouched returns in `references_hd/raw/`. Hashes in the progress file.
3. Smart Topology (`requests/smart_topology_v1.json`, 8k target): 8,800 triangles, one watertight piece.
   `scripts/load_ooze.py` puts the wider axis on X, width 1.0 m, floor at z 0 (height 0.234 m; native 41/178 = 0.23).
4. `scripts/rig_ooze.py`: depth scaled to 0.92 (native side 164 px / front 178 px; Meshy's plan was square), underside
   reduced to 15 % and the rest to 3,294 triangles, pod and globules built, bones and weights (below).
5. `scripts/uv_export.py` (Smart UV 66°, blob only) → `texturing/ooze_neutral_upload.glb` → retexture
   (`requests/retexture_v1.json`, meshy-7, our UVs, 2K PBR, the four HD views).
6. `scripts/anim_ooze.py` (clips + `work/clip_report.json` gates), `scripts/tex_prep.py` (curvature dump, blob AO),
   `scripts/compose_ooze.py` (maps, mask, ramps), `scripts/build_runtime.sh <token>` (export → prepare → LODs →
   shadow fix → variants), `scripts/viewer_tiers.py`, `scripts/update_viewer_manifest.py`.
   Clay sheets: `scripts/render_clip.py` + `scripts/sheet.py` → `review/c_<Clip>_sheet.png`, `review/rest_sheet.png`.

## Anatomy decisions

- **A blob: no skeleton beyond squash and stretch** (batch note). Lump bones (`Lump_C` in the middle, `Lump_0–7` on an
  ellipse at 55 % of the outline) have their heads on the floor, so scaling or sliding them raises or spreads the slime
  without ever lifting or sinking the underside (mm6_ooz_claude route). Heat weights over the lumps only.
  Lumps use non-uniform scale; the engine's joints assume uniform scale, so normals are approximate while a lump
  stretches (as for mm6_ooz). `Body` is never scaled (a non-uniformly scaled parent would shear the rotated pod chain,
  which glTF TRS cannot carry).
- **Pseudopod with a knob** (native attack m298ab–af): a lumpy lathe stalk (radius 6.2 → 5 cm, 0.54 m) ending in an
  onion/diamond knob 27 cm wide; full height 0.85 m = 151 native px, as frame ae. Chain `PodRoot → Pod1–5 → Knob`,
  linear blend weights along the stalk, knob rigid. It stands in the bind pose and is hidden in every clip except
  Attack and Cast by `PodRoot` scale 0.02 inside the blob; the base lump swells where it emerges.
- **Globules** (native death dc–de and corpse xa, which scatter round globs across ~1.4× the body width): 12 low-poly
  flattened spheres, each 100 % on its own `Glob_NN` bone, placed in the bind pose at their corpse spots on the floor
  around the blob. Hidden (scale 0.001 in the blob's middle) except in Death/Dead, and two of them serve as the
  Fidget's bubbles. They are part of the one mesh (one draw), so the hidden parts still skin ~1.4k triangles (cheap; a
  separate node would cost a draw).
- **Pod and globules have no texels of their own.** Their UVs map onto a disc of the blob's flat, never-seen underside
  (one large UV island Meshy painted with the same slime; disc radius 0.32 m), angle around the part → angle on the
  disc. The knob shows faint radial streaks from that mapping at close range.
- **Facing.** The blob has no face; it faces −Y like every creature (yaw_offset −π/2). The attack lashes toward −Y.

## Clips (native timing, 125 ms per frame)

| Clip | Native | What it does |
|---|---|---|
| Standing | sa (one still frame) | slow pulse, lumps out of phase |
| Walking | wa–wf, 0.75 s | the middle heaves into a hump (×1.4) and settles while the outline draws in; peristaltic wave front → back, lumps push forward |
| Running | (none) | the crawl ×1.35, 0.5 s |
| Attack | a b c d e f e d c b, 1.25 s | pod rises (b, c), curls back into a hook (d), stands tallest (e), lashes forward and down at the party (f, impact 0.68 s, knob still ~0.55 m high), retracts through e d c b |
| Cast | shoot = the same group | Toxic Cloud (B/C, Use% 10/15): pod rises straight, the knob swells ×1.45 and spits at 0.68 s (sharp contraction + forward nod; `Socket_Spit` on the knob tip), sinks back. Distinct from Attack (engine rule) |
| Hit | na–ng, 0.875 s | outline draws in (178 → 135 px), the middle heaves into a cone, relaxes with a jiggle |
| Death | da–de, 0.625 s | contracts, gathers into a column and hops 7 cm, bursts into the 12 globules (each leaves from inside the column on its own ballistic arc, round in the air, squashes on landing) around a small remnant puddle |
| Dead | xa | corpse: scattered globules + remnant held |
| Fidget | fa–fe, 0.625 s | two bubbles (≈10 cm) swell out of the top and pop one after the other |

## Material decision

- **Opaque, glossy, no blended layer.** The native frames carry no Transparent/Glowing flag; the sprite is an opaque
  very dark green slime with sharp white wet highlights (`config.json`: "translucent-looking", not transparent). An
  alpha-blended outer shell would lose instancing, the depth prepass and back-face culling, and sort against other
  blended effects for no visible gain. So: one opaque material, engine specular kept like mm6_ooz (`openyamm_specular`
  0.7, `openyamm_specular_mask`: ORM red = specular scale, ~0 in creases and occlusion so creases stay near-black),
  roughness 0.42 ± 0.05, metallic 0.
- Base colour: Meshy's slime graded with the blob AO, then curvature shading (creases toward black, convex up-facing
  lump tops toward white) as the sprites' baked wet shading. Base colour goes below the guidelines' sRGB 30 floor in
  the creases on purpose (the native slime median is sRGB (12, 42, 6)).
- **Tiers: one region (the whole slime), mask = 1 everywhere** (gutters included, so no tier-A seams). Ramps
  (`compose_ooze.rank_ramps`): native pixels of every frame of every action, the same pixels read in 299/300/301
  (the manifest's recolour touches palette indices 3–251, i.e. all of the slime); a stop's hue and saturation come from
  the native pixel at the same luminance rank, its luminance from the texel scaled so the slime mean = native mean ×
  `GAIN` 0.8 (linear; the engine gloss adds light, mm6_ooz in-game A/B settled at 0.9). Matching by absolute
  luminance (`native_shading.transfer_ramps`, the mm6_ooz route) read pastel here: Meshy's slime is brighter than the
  sprite, so its mid stops picked the sprites' near-white glints. Darkest stops desaturated.
- Material classes: `textures/ooze_material_classes.png` = 11 (other: slime) everywhere.
- The review viewer (three.js) ignores `openyamm_specular_mask`; `viewer_tiers.py` folds the mask into roughness for
  the viewer GLBs only, so the creases do not mirror the viewer's environment as grey lines.

## Gates (`work/clip_report.json`, every frame of every clip)

- Floor: lowest vertex (blob, visible pod, globules) ≥ 0.0 m in every clip; underside never lifted except the
  intentional death hop (max 7 cm, native db is drawn off the ground).
- Edge stretch (max edge length / rest): blob ≤ 1.67 (Running lumps; Walking 1.49, Hit 1.54, Death column 1.58 —
  intentional squash and stretch on a smooth blob); pod ≤ 1.2 in Attack, 1.67 in Cast (the knob's uniform swell).
- Export: 0 inverted closed parts (`check_winding.py`); no LOD/shadow triangle spans blob, pod and globules or two
  globules; GLB clip lengths equal the manifest durations; viewer `check` 27/27, no console errors.

## Scale and timing for the binding

- Scale = native standing width 178 px × frame scale 1.0 ÷ blob width 1.0 m = **178** (height check: 41 px / 0.234 m
  = 175; side length 164 px / 0.92 m = 178). B/C have the same frame scale (`native_frame_scales` [1]).
- Stride: Spd 120 (A) × 0.75 s / 178 = **0.5 m** per Walking cycle; Running 0.67 m per 0.5 s cycle.
- Attack impact 0.68 s (frame af). **The MM7 sprite groups m299a/m300a/m301a have no `contact_frame` in
  `engine/rendering/sprite_attack_timing.yml`**, so the game applies the attack when the whole 1.25 s sprite action
  has played and would stretch this clip's wind-up ~1.8×. Recommended (runtime table, not changed here):
  `m299a/m300a/m301a: {contact_frame: 5}` (af at 0.625 s).

## For the user to review

- Brightness: the viewer shows the slime lighter than the very dark sprites; ramps target 0.8 × the native mean
  (linear) for the engine's gloss. Judge in game; rebuild lighter/darker with
  `OOZE_GAIN=<x> python3 <P>/scripts/compose_ooze.py && <P>/scripts/build_runtime.sh <token>`.
- Shape: Meshy's blob has larger, rounder lobes and deeper creases than the sprite's fine wormy ridges.
- Motion is procedural and an interpretation of the native frames; the death's globules ring the remnant more evenly
  than the sprite's left-right spray.
- No in-game check was run (optional for batch I).

## Install later (not run)

**Reduced version:** [`../mm7_m298_reduce_claude/`](../mm7_m298_reduce_claude/README.md) (2026-10-20) — install its
`export/mm7_m298.glb` instead of this one
(`python3 tools/install_model.py level_generation/creatures/mm7_m298_reduce_claude/export/mm7_m298.glb --world mm7`);
the binding below is unchanged.

```sh
python3 tools/install_model.py level_generation/creatures/mm7_m298_claude/export/mm7_m298.glb --world mm7
```

Binding for `assets_dev/worlds/mm7/models/actors.yml` (plus the `contact_frame` entries above):

```yaml
# MM7 Ooze (m298): Meshy blob + own lump rig (squash and stretch), knobbed pseudopod for Attack/Cast, globules for
# the death burst and corpse. Skins m298_a/b/c share one texture set (palettes 299/300/301). Wet slime keeps specular.
- descriptor: Ooze A
  model: worlds/mm7/models/mm7_m298.glb
  scale: 178
  yaw_offset: -1.570796327
  skin: m298_a
  animation:
    cast: Cast
    run: Running
    stride_length: 0.5
    run_stride_length: 0.67
    upper_body_root: Body
    sockets:
      spit: Socket_Spit
    events:
      attack_melee: {impact: 0.68}
      cast: {impact: 0.68, glow: [spit], release: spit, glow_scale: 0.8}
  clips:
    standing: Standing
    walking: Walking
    attack_melee: Attack
    attack_ranged: Attack
    hit: Hit
    dying: Death
    dead: Dead
    fidget: Fidget
# Ooze B / Ooze C: the same with skin m298_b / m298_c and scale_reference: Ooze A
```

## Open issues (shared tools, not changed)

- `engine/rendering/sprite_attack_timing.yml` lacks MM7 `m299a/m300a/m301a` contact frames (see above).
- `level_generation/creatures/mm7_m278_claude/scripts/update_viewer_manifest.py` (copied here) hard-codes its project
  name in several places; a copy must replace every one (done here).
