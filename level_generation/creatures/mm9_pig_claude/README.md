# MM9 pig (mm9_pig) — 3D model, 2026-10-30

The MM9 pig (`mm9/extracted/MODELS/MODELS/PIG.abc`, 30 joints, 299 tris, 14 clips) for row 271 Pig (pig.dtx, pig.scr,
Hostility 2, Damage 0, `IsMonster 0`). Built on the MM9 rig-reuse route of `../mm9_dfly_claude/` and `../mm9_wolf_claude/`:
a new HD Meshy mesh weighted to the original MM9 skeleton, the MM9 clips played with only the listed fixes. Progress,
hashes and receipts: `creature_3d_progress.json`.

| Item | Value |
|---|---|
| Runtime GLB | `assets_source/worlds/mm9/models/mm9_pig.glb` (cooked copy in `assets_dev`) |
| Binding | `assets_dev/worlds/mm9/models/actors.yml` block `mm9_pig_claude`: `MM9 271 Pig`, scale 100 |
| Data | `tools/mm9_import_discovery/mm9_npc_actor_rows.tsv` row 271 (fallback visual 471, zdog C); monster 9271 |
| Triangles LOD0/1/2/3 | 6,018 / 3,008 / 1,082 / 360 (eyes 544) |
| Skeleton | the MM9 one, names unchanged, plus two ear hinge helpers `EarRoot`, `EarRoot01` (children of `Xhead`) |
| Clips (30 fps) | Standing 1.7 (Stand), Walking 0.9 (Walk), Running 0.3 (Run), Fidget 1.8 (Fidget2), Hit 0.9 (Wince1), Death 1.2 (Die1), Dead 1.0 |
| Gait | stride 0.35 (walk), 0.48 (run) model units per cycle (`scripts/gait_measure.py`), `gait_rate [0.8, 1.6]` |
| Floor | ground rule, root offsets low-passed; `floor_audit.py --world mm9` ok |
| Meshy credits | **15 / 30** (backup account): Smart Topology 5, 4K retexture 10 |

## Route

0. **HD masters** (`references_hd/`, Codex, two runs): renders of the MM9 model and skin (`mm9_views_pig.png`), skin x4.
1. **Meshy** Smart Topology 15k from `00_three_quarter.png`: 15.7k body, two eye pieces, 0.1 % interior area.
2. **Clean** (`scripts/clean_sym.py`, voxel size 0): mirror plane found, body symmetrised, eye mirrored, pinholes
   closed. No voxel rebuild: the return has no fused layers (interior area 0.1 %, the wolf's a third), and a 3 mm voxel
   surface left terraces that showed as moire in the shading.
3. **Fit** (`scripts/fit_pig.py`, from the wolf's `fit_quad.py`): pitch-only ICP (the mirror plane stays), grounded,
   head ICP, the four legs and the tail on MM9's chains by the transient skinning pose.
4. **Weights**: `scripts/rig_body.py` (nearest MM9 label, diffusion), then `scripts/refine_pig.py`: ear flaps found by
   thickness, each on a helper hinge at its own root; left copies right with bones renamed.
5. **Reduce** symmetric (`scripts/reduce_body.py 0.3 0.6 0.45`), **UV** `scripts/uv_atlas.py` (`claude_shared/uv_atlas.py`, head
   x2), **4K retexture** with the four HD masters (`requests/pig_retexture_v1.json`).
6. **Weights on the UV mesh** (`scripts/weights_v5.py`): leg roots fade into the spine towards the mid-plane; ear
   vertices past the head's width go fully on the hinge. Topology and UVs unchanged.
7. **Textures** (`scripts/compose_pig.py`): colour 4K -> 2K once, gentle grade, normal and ORM 1K, material classes; no mask.
8. **Clips** (`scripts/clips_mm9.py`, `build_export.py`): PCHIP through the MM9 keys, loop seams closed by distributing
   the residual (Walk 6.7, Run 12.9 deg); helper bones copy Xearpiv's rotation keys.
9. **Runtime** (`scripts/build_runtime.sh`): prepare, LODs, shadow shrink, extras (specular 0, metallic 0), floor pass, winding.

## Rebuild

```sh
T=<lease token>; B="tools/run_creature_blender.sh --token $T"; P=level_generation/creatures/mm9_pig_claude
V=level_generation/props/mm9_isleofashes_claude/work/venv/bin/python
$V tools/mm9_import_discovery/convert_abc_model.py mm9/extracted/MODELS/MODELS/PIG.abc $P/source/pig --id pig \
  --texture 0=mm9/extracted/SKINS/SKINS/PIG.dtx --scale 0.0256
$B $P/scripts/mm9_rig_source.py $P/source/pig/pig.glb $PWD/$P/work/mm9_pig_rig.blend 0 0.2385
$B $P/scripts/clean_sym.py $P/meshy/pig_smart_v1/model_urls_glb.glb $PWD/$P/work/pig_clean_v2.glb 0 1 $PWD/$P/work/clean_v2.json
$B $P/scripts/fit_pig.py $PWD/$P/work/mm9_pig_rig.blend $PWD/$P/work/pig_clean_v2.glb $PWD/$P/work/fit_v3.blend $PWD/$P/work/fit_v3.json
RIG_DIFFUSE=20 RIG_HINGE=4 $B $P/scripts/rig_body.py $PWD/$P/work/fit_v3.blend $PWD/$P/work/rig_v3.blend $PWD/$P/work/rig_v3.json
$B $P/scripts/refine_pig.py $PWD/$P/work/rig_v3.blend $PWD/$P/work/rig_v4.blend $PWD/$P/work/refine_v4.json
$B $P/scripts/reduce_body.py $PWD/$P/work/rig_v4.blend $PWD/$P/work/reduced_v4.blend $PWD/$P/work/reduced_v4.json 0.3 0.6 0.45
$B $P/scripts/uv_atlas.py $PWD/$P/work/reduced_v4.blend $PWD/$P/work/uv_v4.blend $PWD/$P/texturing/pig_body_upload.glb $PWD/$P/work/uv_v4.json
# xatlas packs differently per run: never re-run once the upload went to Meshy (pig_retexture_v1)
$B $P/scripts/weights_v5.py $PWD/$P/work/uv_v4.blend $PWD/$P/work/uv_v5.blend $PWD/$P/work/weights_v5.json
HEAD_GROUPS=Xhead,Xnose,EarRoot,EarRoot01 JAW_GROUPS=Xnose $B $P/scripts/dump_uv3d.py $PWD/$P/work/uv_v4.blend $PWD/$P/work/uv3d_pig.npz Body
$B $P/scripts/bake_ao.py $PWD/$P/work/uv_v4.blend Body $PWD/$P/textures/pig_ao_2k.png 0.03 2048
python3 $P/scripts/compose_pig.py && python3 $P/../claude_shared/grade_basecolor.py --ao $P/textures/pig_ao_2k.png \
  --fine 1.0 --local 0.3 --ao-strength 0.5 --contrast 1.06 --saturation 1.15 $P/textures/pig_basecolor.png
$B $P/scripts/build_export.py $PWD/$P/work/uv_v5.blend $PWD/$P/work/anim_v5.blend $PWD/$P/export/mm9_pig_lod0.glb $PWD/$P/work/clips_v5.json
python3 tools/creature_workspace.py run --project $P --token $T -- $P/scripts/build_runtime.sh --install
flock -x level_generation/creatures/claude_shared/locks/mm9_actors_yml.lock \
  python3 $P/scripts/bind_actors.py mm9_pig_claude $P/work/actors_block.yml
(cd $P && python3 scripts/mm9_viewer_model.py source/pig/pig.glb review/viewer/mm9_pig.glb 0.2385 Standing=Stand \
  Walking=Walk Running=Run Fidget=Fidget2 Hit=Wince1 Death=Die1 && python3 scripts/make_viewer_manifest.py r3_pig_20261030 \
  "pig=Pig (271, pig.dtx)=export/mm9_pig.glb" "mm9_pig=MM9 original (reference)=review/viewer/mm9_pig.glb")
```

## Checks (2026-10-30)

- Viewer `review/viewer/`: `run_creature_review.py check` 2 models x 7 clips, 0 console errors. The MM9 original is a
  model in the viewer, for the same clip and time side by side. Playback `review/playback/`.
- Sheets from viewer shots: `review/compare_viewer_sheet.png` (MM9 above ours: rest, every clip's extremes),
  `review/texture_sheet.png` (head, ears, tail, legs, underside, Hit).
- Texture quality: atlas 55.0 %, spread 2.05 (density p50 1,439, head 2,811: the head charts are x2 on purpose, and the
  MM9 head bones own a third of the pig), fragments 0.1 %, stretch p90 1.13, 74 islands, 4K source.
- Symmetry: mirror distance of the surface mean 1.3 mm, p99 5 mm (MM9's leg joints differ by 3 mm).
- Orientation (`scripts/orient_gate.py`, `review/orient_gate.json`, 48 fps): snout direction vs MM9 6.8 deg at rest, max
  14 deg in Fidget/Death (MM9's eye triangle bends with the neck; our head is rigid). Sole normal vs MM9: front 7-17,
  hind 17-37 deg: the hind figure compares our flat hoof with MM9's slanted diamond and its lowest vertices change
  in the stride; the feet are flat on the floor in the viewer shots.
- Gates (`scripts/gates.py`, `review/gates.json`): loop seams 0; edge ratio p1/p99 0.43-0.91 / 1.11-2.09; largest
  single edge 7.5 (a 2 mm edge at the nape in Death; 4.2 in Walking and Hit). Folded faces worst frame 43 (of 6,018).
- Jitter (`scripts/jitter_gate.py`, `review/jitter_gate.txt`): per-key floor offsets shook the walk, so they are
  low-passed (`floor_fix.py --smooth`); the offset's second difference is now below the clip's own in every clip.
- Attachment `detached_parts_audit.py`: 0 detached. Shading `flat_shading_check.py`: 0.00. Winding: 0 inverted.
- Floor audit `--world mm9`: Pig ok. Regression `mm9_actor_models_build_every_binding`: 61 descriptors on 28 models, 0 failed.

## Deviations and open points

- `EarRoot` helpers: two joints beyond MM9's skeleton. Our ears sit about 5 cm in front of MM9's; turning them about
  MM9's pivot swung them off the head and shredded them. MM9's `Xear` is not used: it is held 44 deg off its bind in
  every clip, which crumpled our flap, so the ear flick is lost and the swing (Xearpiv) stays. In Hit the swing lays the
  ear against the head, as in MM9.
- Ears are smaller than MM9's large flaps, as in the HD master.
- Pig does not fight: `attack_melee` and `attack_ranged` play Fidget (the Yrsa precedent). Unused MM9 clips (Fidget1,
  Wince2, Die2, Standdown, Rest, Roll, Standup) are not exported. MM9 `Velocity` events are not reproduced.
- No in-game run. The review root (`output/mm9_rework/assets_dev`) was refreshed.
- User artistic acceptance: not recorded.
