# MM9 Magreeb family (mm9_magreeb) — 3D model, 2026-10-30

The MM9 Magreeb, a four-legged mantis beast with two pincer arms, a toothed snout and a horn
(`mm9/extracted/MODELS/MODELS/MAGREEB.abc`, 49 joints, 16 clips), for the MM9 world: Magreeb Spawn (9276, MAGREEB1),
Magreeb (9277, MAGREEB1, Scale 1.5), Armored Magreeb (9278, MAGREEB2, Scale 1.75) and the single scripted row
MagreebBaby (9244, MAGREEB1, Scale 0.7), which shares the body. Descriptors `MM9 Magreeb A|B|C`, `MM9 244 MagreebBaby`.
Not a humanoid: it stands on four insect legs; the arms are claw limbs. Built on the MM9 rig-reuse route of
`../mm9_dfly_claude/` and `../mm9_lobber_claude/`. Progress, hashes and receipts: `creature_3d_progress.json`.

| Item | Value |
|---|---|
| Runtime GLB | `assets_source/worlds/mm9/models/mm9_magreeb.glb` (installed; cooked copy in `assets_dev`), skins `mag_a` (MAGREEB1), `mag_c` (MAGREEB2) |
| Binding | `assets_dev/worlds/mm9/models/actors.yml`, block `# >>> mm9_magreeb_claude` (`bindings/actors_block.yml`); scales 100 / 150 / 175, Baby 70 (MONSTERS.txt Scale x 100) |
| Triangles LOD0/1/2/3 | 6,002 / 3,001 / 1,079 / 357 |
| Texture (2026-10-30 pass) | 2K base colour from a 4K Meshy paint on xatlas UVs: 54.0 % of the atlas, 261 islands, 2,020 texels per creature size (median) |
| Skeleton | the MM9 one, names unchanged (`Bone37` root, legs `Bone56/61/108/114`, arms `Bone38/39`, head `Bone36/09`, jaw `Bone01/02`, horn `Bone04-07`) |
| Clips (30 fps) | Standing 3.0 (stand), Walking 0.67 (walk), Running 0.4 (run), Fidget 3.0 (fidget1), AttackMelee 1.13 (Hattack1), AttackRanged 1.0 (Hattack2, the second melee attack), Hit 1.3 (wince1), Death 1.7 (die1), Dead 1.0 |
| Events | AttackMelee impact 0.533 s (MM9 `Lattack`), AttackRanged impact 0.413 s (MM9 `Lattack; Rattack`); no ranged attack or spells, so no release socket |
| Gait | stride 0.78 m (mean foot fore-aft travel per walk cycle, `scripts/gait_measure.py`), run stride 1.2, gait rate 0.8-1.6 |
| Floor | ground rule: Standing/Walking/Running/Fidget on the floor, attacks and Hit raised, corpse grounded; `floor_audit.py --world mm9` ok |
| Meshy credits | **25 / 35** (Smart Topology 5, retexture v1 10, 4K retexture v2 10 for the texture pass; backup account) |

## Route

0. **HD masters** (`references_hd/`, Codex via `claude_shared/codex_slot.sh`, two runs, 1536x1024): renders of the
   MM9 model with MAGREEB1, the skin x4 and a top view. Gate: four legs, two pincers, horn, dorsal spines. `02_back`
   shows six legs; accepted because the back view only colours the retexture (uniform olive legs).
1. **Meshy** Smart Topology 15k from `00_three_quarter.png`: body, head with horn, four separate legs (front pair with
   forked feet), each arm as three pieces split differently per side (`work/comps_v1_*.png`).
2. **Fit** (`scripts/fit_magreeb.py`, chains in `scripts/mag_cfg.py`): core scale + translation ICP onto the MM9 non-limb
   vertices, head rigid ICP onto the MM9 head; legs by `fit_chain` with the centreline taken from the attachment (the
   forked feet average into one foot instead of folding the line), the MM9 foot hook replaced by a straight extension
   of the shin; arms: one joint polyline through the arm's pieces (shoulder, junctions, wrist, claw centre, tip)
   mapped onto the MM9 arm chain with the wrist anchored on `Bone14`, and the claw rolled so its blades open in MM9's
   plane (`work/fit_v6_sheet.png`).
3. **Weights** (`scripts/rig_body.py`): nearest MM9 vertex per chain, diffusion; then `scripts/reweight_head.py`:
   MM9's lower jaw (`Bone01/02`) hangs where our throat is, so head vertices are split by the plane through the jaw
   hinge and the mouth: above -> skull/horn, below -> jaw, behind the hinge -> skull/horn/neck (attack stretch edges
   199-289 -> 57-149 per clip).
4. **Reduce** (`reduce_body.py 0.35 0.5 0.55`), **UV** (`uv_export.py magreeb`, head x1.8), **retexture** (01/03/02/04)
   on fit v5 (superseded by the texture pass below: UVs v8, retexture v2). Fit v6 (straight feet: v5 had black
   fin-like toes) was carried onto the textured mesh by
   `scripts/carry_fix.py` (per-vertex displacement of the two fits, UVs and weights unchanged).
5. **Clips** (`scripts/clips_mm9.py`): PCHIP resampling at 30 fps; loop seams closed (walk 20.3, run 13.8 degrees
   before MM9's own seam; 0 after); Dead = last Death pose.
6. **Textures** (`scripts/compose.py`): regions R red/orange (claws, belly bands, horn), G olive chitin, B bright green
   (claw and leg tips), A dark (spines, joints); eyes and teeth are outside the mask (base colour on every tier). Tier A identity; C takes MAGREEB2's chroma by luminance
   percentile (blue-violet body, teal claws) (`review/magreeb_texture_classes_tiers.png`).
7. **Runtime** (`scripts/build_runtime.sh [--install]`): prepare -> LODs -> shadow shrink -> `region_variants.py` ->
   ground floor pass -> winding check (0 inverted).

## Rebuild

```sh
T=<lease token>; B="tools/run_creature_blender.sh --token $T"; P=level_generation/creatures/mm9_magreeb_claude
V=level_generation/props/mm9_isleofashes_claude/work/venv/bin/python
for t in 1 2; do $V tools/mm9_import_discovery/convert_abc_model.py mm9/extracted/MODELS/MODELS/MAGREEB.abc \
  $P/source/tier$t --id magreeb$t --texture 0=mm9/extracted/SKINS/SKINS/MAGREEB$t.dtx --scale 0.0256; done
$B $P/scripts/mm9_rig_source.py $P/source/tier1/magreeb1.glb $P/work/mm9_magreeb_ground.blend 0 1.3482
$B $P/scripts/fit_magreeb.py $P/work/mm9_magreeb_ground.blend $P/meshy/magreeb_smart_v1/model_urls_glb.glb $P/work/fit_v6.blend $P/work/fit_v6.json
# the textured mesh was built from fit v5 (fit_magreeb.py without the straight-foot targets) and then corrected:
$B $P/scripts/rig_body.py $P/work/fit_v5.blend $P/work/rig_v5.blend $P/work/rig_v5.json
$B $P/scripts/reduce_body.py $P/work/rig_v5.blend $P/work/reduced_v5.blend $P/work/reduced_v5.json 0.35 0.5 0.55
$B $P/scripts/uv_export.py $P/work/reduced_v5.blend magreeb $P/work/uv_v5.blend $P/texturing/magreeb_body_upload.glb
$B $P/scripts/carry_fix.py $P/work/uv_v5.blend $P/work/fit_v5.blend $P/work/fit_v6.blend $P/work/uv_v6.blend $P/work/carry_v6.json
$B $P/scripts/reweight_head.py $P/work/uv_v6.blend $P/work/mm9_magreeb_ground.blend $P/work/uv_v7.blend $P/work/reweight_v7.json
# texture pass (2026-10-30): rooted limbs, xatlas UVs, 4K retexture v2 on them, gentle grade
$B $P/scripts/root_limbs.py $P/work/uv_v7.blend $P/work/roots_v7.blend $P/work/roots_v7.json
$B $P/scripts/uv_atlas_v8.py $P/work/roots_v7.blend $P/work/uv_v8.blend $P/texturing/magreeb_body_upload_v2.glb $P/work/uv_v8.json
#   xatlas packs a little differently per run: never re-run this once the upload went to Meshy (retexture_v2 is on it)
python3 tools/creature_meshy.py --project $P --token $T submit --job magreeb_retexture_v2 --kind retexture \
  --request requests/retexture_v2.json --credits 10      # then poll / download
$B $P/scripts/dump_uv3d.py $P/work/uv_v8.blend $P/work/uv3d_magreeb_v8.npz Body
$B $P/scripts/dump_uv3d.py $P/source/tier1/magreeb1.glb $P/work/uv3d_mm9_magreeb.npz Magreeb.mesh:1
$B $P/scripts/bake_ao.py $P/work/uv_v8.blend Body $PWD/$P/textures/magreeb_ao_2k.png 0.03 2048
python3 $P/scripts/compose.py && python3 $P/../claude_shared/grade_basecolor.py --ao $P/textures/magreeb_ao_2k.png \
  --fine 1.0 --local 0.3 --ao-strength 0.5 --contrast 1.06 --saturation 1.15 $P/textures/magreeb_basecolor.png \
  && python3 $P/scripts/compose.py
$B $P/scripts/build_export.py $P/work/uv_v8.blend $P/work/anim_v8.blend $P/export/mm9_magreeb_lod0.glb $P/work/clips_v8.json
python3 tools/creature_workspace.py run --project $P --token $T -- $P/scripts/build_runtime.sh --install
flock -x level_generation/creatures/claude_shared/locks/mm9_actors_yml.lock python3 $P/scripts/install_binding.py $P/bindings/actors_block.yml mm9_magreeb_claude
python3 $P/scripts/viewer_tiers.py && python3 $P/scripts/make_viewer_manifest.py r2_magreeb_texpass_20261030 \
  "mag_a=Magreeb Spawn / Magreeb / Baby (A, B)=$P/review/viewer/mag_a.glb" "mag_c=Armored Magreeb (C)=$P/review/viewer/mag_c.glb"
```

The v1 texture route (before 2026-10-30) used `uv_v5.blend` / `uv_v7.blend` directly (`uv_export.py`,
`magreeb_retexture_v1`, default grade). Fit v5 is the same script before the "MM9 feet end in a short sideways hook" target change (`work/fit_v5.json`).

## Checks (2026-10-30)

- Viewer `review/viewer/` (2 tiers x 9 clips): `tools/run_creature_review.py --project ... check` 0 errors (18
  switches); shots `review/viewer_shots_sheet.png`.
- Gates (`scripts/gates.py`, `review/gates.json`): loop seams 0; edge ratio p1/p99 per clip 0.64-0.97 / 1.04-2.68;
  the extremes (max 15.8) are the pincer web between the blades when MM9 opens the claw wide and the mouth corners
  (`scripts/stretch_where.py`).
- Floor audit `floor_audit.py --world mm9`: the four Magreeb bindings ok. Regression
  `mm9_actor_models_build_every_binding`: 28 descriptors on 12 models, 0 failed. Winding: 0 inverted closed parts.
- In game (tours in `../mm9_eye_claude/review/`): `review/ingame_lindisfarne_sheet.png` (Lindisfarne: the map's
  own Magreebs on the field, spawned Armored Magreeb (C, blue) and MagreebBaby/Spawn (A) at the party),
  `review/ingame_ravensford_sheet.png` (Ravensford valley: spawned Magreeb A/B/C walking up and attacking).

## Deviations and open points

- Magreeb (B) and MagreebBaby use the Spawn's skin (MM9 gives them MAGREEB1 too); they differ by scale only.
- The Meshy arms are shorter than MM9's; they are stretched along the MM9 arm chain (upper arm and claw thicker
  than MM9's). Pincer blades are one piece per claw, so the web between the blades stretches when the claw opens.
- Hattack2 plays as AttackRanged (the descriptor's second attack is melee); Taunt, fidget2, wince2, die2, Backpedal,
  Backpedalrun and Jumping are not exported. MM9 `lunge` events are not reproduced (clips in place).
- Back master has six legs (see step 0).
- User artistic acceptance: accepted "magreeb - ok" (2026-10-30, after the texture pass).

## Texture quality pass (2026-10-30)

User feedback: "model/anims ok but texturing needs to do much better job" (close-up of head, arm and claw: blotchy,
soft, pincer texture stretched). Pilot of `../claude_shared/TEXTURE_QUALITY_PASS.md`; mesh shape, rig and clips kept.

**Causes, largest first** (measured with `claude_shared/texture_quality.py` and texture crops):
1. **UV layout.** Smart UV Project on the reduced body: 740 islands, 33.7 % of the 2K atlas (an equivalent 1,188 px
   square), 10.3 % of the surface on islands under 8 triangles. Meshy paints every fragment as its own flat blotch
   (the coloured specks over the old texture), and gutters took two thirds of the atlas.
2. **Meshy's paint at 2K** on that layout: little texel-scale detail (fine-band RMS 6.1 levels; the v2 paint has
   14.9 at the same 2K after downsampling its 4K return). It was baked once on our UVs (`enable_original_uv`), not
   twice: no re-bake loss.
3. **Grading** (`grade_basecolor.py` defaults): AO multiply 0.7 plus local contrast at 16 px raised the 4-16 px band
   1.6x - the dark blotches on the claws - and fine damping halved the finest octave.
4. **Ramps**: one luminance ramp for olive and bright green turned the green claw tips olive on tier A (mean error
   13 levels on the v2 paint); hue variation inside a region is flattened by design.
5. **Not causes:** texel-density spread was already even (p90/p10 1.23; claws at the median, rest-pose stretch p90
   1.3-1.5). The engine samples trilinear + anisotropic, the creature cook keeps 2048. The "stretched pincer" is the
   blades' web stretching when MM9 opens the claw (edge ratio up to 15.8, unchanged, see Checks) plus the old blotch
   pattern; the sawtooth inner edges are the serrated teeth of the HD master, left as modelled.

**Changes.**
- `scripts/root_limbs.py` (coordinator request after `claude_shared/detached_parts_mm9.md`): legs Bone61 and Bone114
  stretched along their root bone until the cap is 3 cm inside the body (x1.22, x1.16; they stopped 1.6 / 4.7 cm short),
  taking the body's weights where they enter; the +X upper-arm piece (Bone21, parted 2.1 cm in Death) takes its
  neighbours' weights within 6 cm. `detached_parts_audit.py export/mm9_magreeb.glb`: **0 detached in any pose**
  (was 3). Done before the new UVs, so nothing is re-textured afterwards.
- `scripts/uv_atlas_v8.py` (`claude_shared/uv_atlas.py`): xatlas charts, charts under 12 triangles merged into a
  neighbour and re-flattened (SLIM, reverted where they overlap or collapse), head x1.8, xatlas brute-force packing
  with a 2 px margin -> `work/uv_v8.blend`.
- Retexture v2 (`requests/retexture_v2.json`): same four HD masters, `meshy-7`, **4K**, our UVs; **10 credits**
  (backup). Its 4K maps are downsampled once to 2K (colour) and 1K (normal); never re-baked.
- Grade: `--fine 1.0 --local 0.3 --ao-strength 0.5 --contrast 1.06 --saturation 1.15` (4-16 px band 1.30x instead
  of 1.6x, finest octave kept).
- Regions: red, olive, bright green, dark; eyes and teeth left the mask. Tier A ramp errors: red 13.0, olive 5.0,
  green 10.0, dark 2.7 levels; tier C 0.05-0.24.
- AO re-baked on the new UVs; binding unchanged (same model path and skins).

| Measure (`texture_quality.py`, LOD0) | Before | After |
|---|---|---|
| Atlas use (2K) | 33.7 % | **54.0 %** |
| Equivalent fully used square | 1,188 px | 1,506 px |
| Texels per creature size p10 / p50 / p90 | 1,429 / 1,612 / 1,754 | **1,931 / 2,020 / 2,166** (+25 % linear) |
| Density spread p90/p10 | 1.23 | 1.12 |
| Islands / surface on fragments | 740 / 10.3 % | 261 / 2.1 % |
| UV stretch p90 (rest pose) | 1.52 | 1.17 |
| Meshy source | 2K on 34 % | 4K on 54 % (3,011 px equivalent) |

The 70 % atlas target was not reached: the reduced Meshy body has spikes, teeth and serrated pincer edges on every
part, so automatic charts stay jagged and brute-force packing tops out at 54-58 % (58.2 % unmerged with 399 islands
and 5 % fragments; the merged 54 % layout was chosen because fragments are what Meshy paints as blotches). Known
flaw: 12 triangles on the +X front leg's shin (0.09 % of the surface) were squeezed to zero UV area by SLIM and sample
a line of texels; `uv_atlas.py` now reverts such charts, a fix here needs a new retexture.

**Checks.** Winding 0 inverted; flat-shading check 0.00; viewer `check` 0 errors (18 switches); gates unchanged
(p1/p99 0.62-0.97 / 1.05-2.69, max 15.8 in AttackRanged as before); floor audit the four bindings ok; regression
`mm9_actor_models_build_every_binding` (`--world mm9`) 49 descriptors on 20 models, 0 failed. No in-game run.
Sheets (identical cameras, `scripts/texpass_views.py`): `review/texpass_before_after_sheet.png` (close-up of head, arm
and claw, front, 3/4; tiers A and C), `review/texpass_density_heatmap_sheet.png` (density on one scale, green = the old
median), `review/texpass_viewer_sheet.png` (review viewer presets). Before state kept in `work/before_texpass/`.
