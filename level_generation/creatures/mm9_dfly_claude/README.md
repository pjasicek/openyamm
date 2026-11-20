# MM9 dragonfly family (mm9_dfly) — 3D model, 2026-10-29

The serpentine MM9 dragonfly (long S-curved snake body, four wings, no legs; `mm9/extracted/MODELS/MODELS/DRAGONFLY.abc`)
for the MM9 world: Dragonfly Mite (9075, skin DRAGONFLY1), Dragonfly (9076, DRAGONFLY2), Fire Dragonfly (9077,
DRAGONFLY3). First pilot of the MM9 rig-reuse route (`devdocs/mm9_rework/PLAN.md`, "Creatures and NPCs";
`CHECKS.md` section 3): a new HD Meshy mesh weighted to the original MM9 skeleton, the MM9 clips played with only the
listed fixes. Progress, hashes and receipts: `creature_3d_progress.json`.

| Item | Value |
|---|---|
| Runtime GLB | `assets_source/worlds/mm9/models/mm9_dfly.glb` (installed; cooked copy in `assets_dev`), skins `dfly_a/b/c` |
| Binding | `assets_dev/worlds/mm9/models/actors.yml` (new file, MM9 descriptors only), `scale: 100` = the MM9 size |
| Triangles LOD0/1/2/3 | 5,867 / 2,930 / 1,019 / 313 (LOD0: body 1,942, head 1,872, teeth/jaw 517, eyes 576, wings 960) |
| Skeleton | the MM9 one, 31 joints, names unchanged (`XCENTER`, `Xback*`, `Xtail*`, `Xwingbase`, `Xneck`, `Xheadpiv`, `Xhead`, `Xjawpiv`, four wing chains) + `Socket_Mouth` |
| Clips (30 fps) | Standing 1.4 (StandAir), Walking 1.3 (Flap), Running 0.9 (Flap ×1.44), Fidget 1.4 (FidgetAir1), AttackMelee 1.4 (HAttackair1), AttackRanged 1.2 (Rattack1, also the cast), Hit 1.4 (WinceAir1), Death 2.7 (DieAir1+fall1+FallDOwn1), Dead 1.0 |
| Events | melee impact 0.649 s (MM9 `Bite`), ranged/cast impact 0.673 s (MM9 `rangeattack`), released from `Socket_Mouth` |
| Floor | flier rule: hover +0.8493 m baked in the living clips, eased out over Death; corpse grounded (+0.6204); `floor_audit.py --world mm9` 3/3 ok |
| Meshy credits | **15 / 30** (Smart Topology 5, retexture 10; backup account; texture quality pass 0) |

## Texture quality pass (2026-10-30)

`../claude_shared/TEXTURE_QUALITY_PASS.md`, rank 2 ("wing atlas 13 %, repack only"). Mesh, rig, clips, weights, body
texture set and every tier ramp are unchanged; only the wing UVs and the wing base colour changed. **0 Meshy credits.**

- **Cause.** The v1 wing UVs were the top-view image points of a 1488 x 864 crop squeezed into the 1K square: 13 % of
  the atlas used, the image squeezed to 0.69 across and stretched 1.19 down (stretch p90 1.92), so the veins were
  already softened before the texture reached the GPU.
- **UVs** (`scripts/wing_uv_v2.py` on `work/uv_v1.blend` -> `work/uv_v2.blend`): each leaf flattened isometrically on
  its own plane (top and bottom sheets share it), cut once across its long axis (2 pieces: 57.0 %; 1 piece 39.2 %,
  3 pieces 55.6 %), one density, xatlas brute-force packing into 1024 with a 4 px margin. `work/wing_uv_v2.json` keeps
  per piece the affine map new UV -> top-view pixel. Do not re-run it: xatlas packs differently per run.
- **Paint** (`scripts/compose_wing_v2.py`): the same HD top view (`references_hd/05_wings_top.png`), dilated as in
  `prep_wings.py`, enlarged x4 by Real-ESRGAN x4plus (`tools/upscaling/realesrgan-ncnn-vulkan`; crisp veins) plus
  0.6 x the Lanczos x4 band above 1.5 source px (ESRGAN smooths the membrane grain); every texel samples it through
  its piece's affine map, gutters included, so the piece cut has no seam. -> `textures/dfly_wing_basecolor_src_v2.png`,
  `work/wing_alpha_v2.png`, read by `compose_dfly.py`. The new layout gives 1.5-2.4 texels per top-view pixel, which
  is why the x4 source is used (no new Codex image).
- **Tiers.** A refit of the wing ramps on the sharper paint raised the B/C saturation (B olive -> lime, C brown-red ->
  orange), so the approved v1 wing ramps are pinned (`textures/dfly_wing_ramps_pin.json`): they reproduce the v1
  mean leaf colour of every tier within 2 levels. Tier A ramp error on leaf texels: v1 12.8, now 14.9 levels (the gold
  veins flatten toward lavender in tier A, as approved in v1). `textures/dfly_ramps.json` equals v1.
- **Body set kept**: 54.7 % atlas, fragments 3.0 %, stretch 1.43; its spread 2.63 is the deliberate x2.5 head density.

| `texture_quality.py`, `DflyWing_A` (1K) | Before | After |
|---|---|---|
| Atlas use | 13.1 % | **57.0 %** |
| Equivalent fully used square | 371 px | **773 px** (x2.08) |
| Density p10 / p50 / p90 | 888 / 891 / 1,267 | 2,237 / 2,245 / 2,249 |
| Spread p90/p10 | 1.43 | 1.01 |
| Islands / fragments | 4 / 0 % | 8 / 0 % |
| Stretch p90 | 1.92 | 1.01 |

LOD0, clips, weights and sockets are byte-identical to the v1 install; LOD1-3 keep their triangle counts (a few more
wing vertices at the new UV seam). **Checks:** winding 0 inverted; `run_creature_review.py check` 0 errors, 27
switches (manifest `r2_dfly_texpass_20261030`); floor audit 3/3 ok; `detached_parts_audit.py` 0 detached (45
components, as before); flat-shading check unchanged (body 0.00, the flat wing leaves 1.00 as in v1); regression
`mm9_actor_models_build_every_binding` (`--world mm9`) 49 descriptors on 20 models, 0 failed. No in-game run.
Sheets (identical cameras, `scripts/texpass_views.py` + `review/texpass_shots.json`, `scripts/texpass_sheet.py`):
`review/texpass_closeups_sheet.png` (tier A: front wing, rear wing, top, head), `review/texpass_tiers_sheet.png`
(tiers A/B/C, 3/4 and front wing). Before state: `work/before_texpass/`.

Rebuild change: after `uv_export.py`, `$B $P/scripts/wing_uv_v2.py $PWD/$P/work/uv_v1.blend $PWD/$P/work/uv_v2.blend
$P/work/wing_uv_v2.json pieces=2` (done once; keep `uv_v2.blend`), `python3 $P/scripts/compose_wing_v2.py` before
`compose_dfly.py`, and `build_export.py $P/work/uv_v2.blend $P/work/anim_v2.blend ... $P/work/clips_v2.json`.

## Route

0. **HD masters** (`references_hd/`, Codex, two runs): there are no MM9 sprites, so the inputs are renders of the MM9
   model with its tier-1 skin (`mm9_views_tier1.png`, five views; `mm9_top_tier1.png`; the skin ×4 for material).
   Brief `CODEX_BRIEF.md`; records `generation_runs.json`, `selected_views_review.png`. Masters are in the MM9 bind
   pose (S-curve, wings raised), so Meshy returns the right pose. Extra `05_wings_top.png` (top view) textures the
   wings. Gate: 00 accepted; 01/02 show an extra short wing pair, accepted because only their body pixels are used.
1. **Meshy** Smart Topology 15k from `00_three_quarter.png` (`requests/smart_topology_v1.json`).
2. **Fit** (`scripts/fit_body.py`): S-plane aligned to YZ, head −Y; centrelines (Meshy: geodesic bins from the tail
   tip; MM9: Catmull-Rom through the joint chain); arc length mapped piecewise (tail tip, wing root `Xwingbase`,
   skull `Xheadpiv`); every vertex keeps its offset in the local frame and is placed on the MM9 centreline; the head and
   separate pieces move rigidly with the skull frame. Meshy's wings and the stray head-to-wing threads are dropped,
   small holes filled, the lumpy eyes replaced by clean spheres.
3. **Weights** (`scripts/rig_body.py`): nearest MM9 vertex label (the MM9 skin is rigid), then diffusion along the mesh
   (14 iterations, jaw/snout held, 3 hinge iterations); teeth rigid with their nearest body vertex; 4 influences.
4. **Wings** (`scripts/prep_wings.py`, `build_wings.py`): outlines from the top master, mapped by a 2D similarity onto
   the MM9 wing planes (top view), built as thin closed leaves (8 mm ridge); UVs are the image points; weights are the
   barycentric blend of the MM9 wing triangle under each vertex (reproduces the MM9 flap, membrane stretch included).
5. **Reduce** (`scripts/reduce_body.py 0.45 0.75 0.3`: body, head skin, teeth), **UV** (`uv_export.py`: Smart UV,
   head islands ×2.5), **retexture** from 01/03/02/04 with our UVs (`requests/retexture_v1.json`).
6. **Clips** (`scripts/clips_mm9.py`, run by `build_export.py`): the MM9 key poses kept, resampled as monotone cubic
   (PCHIP) curves at 30 fps; loop seams closed (StandAir popped 8.4°, Flap 0°); Death stitched with a 0.3 s smoothstep
   blend of the 28.4° DieAir1→fall1 jump; Running = Flap ×1.44; Dead = Death's last pose.
7. **Textures** (`scripts/compose_dfly.py`): body 2K graded base (`grade_basecolor.py`, AO `bake_ao.py`), 1K normal,
   1K ORM (R AO, G roughness, B 0), class map; regions R scales, G belly, B eyes, A mouth; wing material 1K, one region.
   Ramps: tier A keeps the HD look (target = base); B/C take hue from their own MM9 skin (chroma by luminance
   percentile), saturation scaled by how much more vivid our A is than MM9's A, brightness by the MM9 tier/A ratio;
   eyes take the MM9 tier colours directly (black → amber → grey-brown). `textures/dfly_ramps.json` has the fit report.
8. **Runtime** (`scripts/build_runtime.sh`): prepare → LODs → shadow shrink (wings and parts < 3 cm not pushed) →
   `region_variants.py` (specular 0, metallic 0) → floor pass → winding check (0 inverted).

## Rebuild

```sh
T=<lease token>; B="tools/run_creature_blender.sh --token $T"; P=level_generation/creatures/mm9_dfly_claude
V=<venv with pygltflib>/bin/python
for t in 1 2 3; do $V tools/mm9_import_discovery/convert_abc_model.py mm9/extracted/MODELS/MODELS/DRAGONFLY.abc \
  $P/source/tier$t --id dragonfly$t --texture 0=mm9/extracted/SKINS/SKINS/DRAGONFLY$t.dtx --scale 0.0256; done
$B $P/scripts/fit_body.py $P/meshy/body_smart_v1/model_urls_glb.glb $P/source/tier1/dragonfly1.glb $P/work/fit_v1.blend $P/work/fit_v1.json
$B $P/scripts/rig_body.py $P/work/fit_v1.blend $P/work/rig_v1.blend $P/work/rig_v1.json
python3 $P/scripts/prep_wings.py
$B $P/scripts/build_wings.py $P/work/rig_v1.blend $P/source/tier1/dragonfly1.glb $P/work/rig_wings_v1.blend $P/work/wings_v1.json
$B $P/scripts/reduce_body.py $P/work/rig_wings_v1.blend $P/work/reduced_v1.blend $P/work/reduced_v1.json 0.45 0.75 0.3
$B $P/scripts/uv_export.py $P/work/reduced_v1.blend $P/work/uv_v1.blend $P/texturing/dfly_body_upload.glb
# (retexture_v1 was made on this upload; rerunning the steps above reproduces the same UVs)
$B $P/scripts/dump_uv3d.py $P/work/uv_v1.blend $P/work/uv3d_body.npz Dfly
$B $P/scripts/dump_uv3d.py $P/source/tier1/dragonfly1.glb $P/work/uv3d_mm9.npz d_body.mesh:1 d_winga.mesh:2 d_wingb.mesh:2 d_wingc.mesh:2 d_wingd.mesh:2
$B $P/scripts/bake_ao.py $P/work/uv_v1.blend Dfly $PWD/$P/textures/dfly_ao_2k.png 0.03 2048
python3 $P/scripts/compose_dfly.py && python3 $P/../claude_shared/grade_basecolor.py --ao $P/textures/dfly_ao_2k.png $P/textures/dfly_basecolor.png && python3 $P/scripts/compose_dfly.py
$B $P/scripts/build_export.py $P/work/uv_v1.blend $P/work/anim_v1.blend $P/export/mm9_dfly_lod0.glb $P/work/clips_v1.json
TOK=$T $P/scripts/build_runtime.sh            # --install runs tools/install_model.py --world mm9
python3 $P/scripts/viewer_tiers.py && python3 $P/scripts/make_viewer_manifest.py r1_dfly_20261029 \
  "dfly_a=Dragonfly Mite (A)=$P/review/viewer/dfly_a.glb" "dfly_b=Dragonfly (B)=$P/review/viewer/dfly_b.glb" "dfly_c=Fire Dragonfly (C)=$P/review/viewer/dfly_c.glb"
```

## Checks (2026-10-29)

- `node ../claude_shared/check_viewer.mjs .../mm9_dfly_claude/review/viewer/`: 3 tiers × 9 clips, 0 errors;
  `tools/run_creature_review.py` check, shots (`review/shots/`, `review/viewer_shots_sheet.png`) and playback
  (`review/playback/`, every clip at 1× and 0.5×).
- `scripts/gates.py` (`review/gates.json`): loop seams 0 jump; edge ratio p1/p99 per clip 0.42–0.81 / 1.38–2.0;
  extremes on a few tiny tail-tip edges in tight MM9 curls (min 0.08), not visible at review size (`work/tailcheck.png`).
- Floor audit mm9 3/3 ok (`floor_audit.py` now also reads a world's own `monster_data.txt` for canFly; MM6 still 173/173).
- Regression: new case `mm9_actor_models_build_every_binding` (`--world mm9`: 3 descriptors on 1 model, 0 failed;
  other worlds skip it) and `mm6_mm7_mm8_actor_models_build_every_binding` 647/0.
- In game (Isle of Ashes, minimized, private `--user-data`): `review/ingame_models_sheet.png` (static tier-A models
  playing every clip, death and corpse on the slope) and `review/ingame_sheet.png` / `ingame_tiers_sheet.png` (the
  map's own dragonflies and spawned tiers as 3D actors in flight, casting their bolts). Tours: `review/*_tour.yml`.
  `tools/run_game.sh --isolated` cannot be used for MM9 yet: its save_game preparation step fails on every MM9 map.
- Tier look: `review/tiers_bind_views.png` (Blender, baked tier textures), `review/texture_classes_tiers.png`.

## Deviations and open points

- Wings are our own flat closed leaves (Meshy's slab wings dropped), textured from the HD top view, not from the
  retexture. MM9 front wings flap by joint translation, so their inner third stretches as in MM9.
- Canvas 1536×1024 for all masters; 01/02 extra wing pair (see gate above).
- Tier A uses the HD/Meshy colours (identity ramps, fit error 5–8 levels), B/C the MM9 hues; Fire Dragonfly's flame
  marks on the belly are not a separate pattern (its belly ramp runs red → orange).
- Unused MM9 clips (AwareAir, FidgetAir2, Glide, SearchAir, TauntAir, HAttackair2 `RKick`, WinceAir2, DieAir2 set) are
  not exported; the engine has one clip per role. MM9 `Velocity` lunge events are not reproduced (clips are in place).
- Hit is the full 1.4 s WinceAir1; the engine blends out of it when the hit state ends.
- Close in-game views of tiers B/C were not captured (fliers keep their range); they are checked in the viewer.
- User artistic acceptance: not recorded.
