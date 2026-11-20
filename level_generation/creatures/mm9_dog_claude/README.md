# MM9 dog (mm9_dog) — 3D model, 2026-10-30

The MM9 town dog (`mm9/extracted/MODELS/MODELS/DOG.abc`, 40 joints, 320 tris, 10 clips; MONSTERS.txt row 295, `dog.dtx`,
`dog.scr`, Hostility 2) on the MM9 rig-reuse route of `../mm9_dfly_claude/` and `../mm9_wolf_claude/`: a new HD Meshy mesh
weighted to the original skeleton, the MM9 clips played with only the listed changes. Progress, hashes and receipts:
`creature_3d_progress.json`.

| Item | Value |
|---|---|
| Runtime GLB | `assets_source/worlds/mm9/models/mm9_dog.glb` (cooked copy in `assets_dev`); one skin, no tiers |
| Binding | `assets_dev/worlds/mm9/models/actors.yml` block `mm9_dog_claude`: `MM9 295 dog`, scale 100 (100 x MONSTERS.txt `Scale` 1) |
| Descriptor | `tools/mm9_import_discovery/mm9_npc_actor_rows.tsv`: row 295, fallback visual legacy zdog A (469); monster id 9295 |
| Triangles LOD0/1/2/3 | 7,177 / 3,582 / 1,256 / 395 (46 teeth 460, tongue ~100, eyes 40) |
| Skeleton | the MM9 one, names unchanged (`XCENTER`, `XbackA/B/C`, `Xback`, `Xfrontleg`, legs `Xflegpiv-Xfleg-Xfankle-Xffoot` and `Xblegpiv-Xbleg-Xblegmid-Xbankle-Xbfoot` (+01), neck `XneckC/B/A`, `Xheadpiv`, `Xhead`, `Xmouth`, `Xjawpiv`, ears `Xearbase-Xearpiv` (+1), tail `Xtailpiv`, `XtailA/B/C`) |
| Clips (30 fps) | Standing 1.4 (stand), Walking 0.5 (walk), Running 0.27 (run), Fidget 3.0 (fidget1), AttackMelee 2.0 (Bark, also ranged and cast), Hit 0.5 and Death 1.2 (authored: MM9 has neither for the dog), Dead 1.0 |
| Events | attack impact 0.5 s (the second bark's jaw peak; MM9's Bark has only a sound event at 0) |
| Gait | stride 1.05 (walk), 1.28 (run) model units per cycle (`scripts/gait_measure.py`) |
| Floor | ground rule; `floor_audit.py --world mm9` ok |
| Meshy credits | **25 / 25** (backup account): Smart Topology 5, 4K body retexture 10, 4K head retexture 10 |

## Route

0. **HD masters** (`references_hd/`, Codex): five views from renders of the MM9 model and skin (the skin is 128 px, shown
   x8), bind pose, mouth narrowly open. **Head turnaround** (`references_head/`): four 1254² views, mouth closed.
1. **Meshy** Smart Topology 15k from `00_three_quarter.png`. The return has a real mouth pocket (palate, floor, back wall)
   and separate teeth, eyes and claws, plus sliver threads between the forelegs.
2. **Clean** (`clean_meshy.py`): raw holes fan-filled (an open shell voxelises as a double wall), voxel 3.5 mm in Meshy
   units, threads removed after the voxel pass by local thickness (`STRAND_BOX`), the body re-voxelised.
3. **Fit** (`fit_quad.py`): global ICP, head turned by the yaw and roll that make it mirror-symmetric (`HEAD_ROT=sym`, 4.5 /
   4 deg), limbs by the wolf's transient skinning, segment stretch up to 1.45 (MM9's forelegs are 1.3x the Meshy ones).
4. **Symmetry** (`symmetrize.py`): the dog's right half mirrored (the left ear stuck out sideways), tail centred first
   (5.6 cm at the tip), seam relaxed; MM9's mesh is exactly symmetric, ours too (0 mirror misses after `sym_rigged.py`).
5. **Mouth** (`mouth_carve.py`): the voxel pass fused the slit along the sides, so a thin wedge along the lip plane
   (Boolean, tapering to the corners at y -0.40, by the MM9 hinge) is cut, re-voxelised and cut again. Upper and lower jaw
   are then separate skin up to y -0.41 (`jaw_comps.py`).
6. **Weights** (`rig_body.py`, `refine_weights.py`, `mouth_weights.py`): nearest MM9 label + diffusion, torso smoothing from
   the wolf; jaw by connectivity in front of the corners (MM9's own Xjawpiv owns only a few chin vertices), cheek and throat
   on a soft band, pocket floor fading out towards the hinge; eyes on socket weights.
7. **Reduce** (`reduce_body.py`, two passes, head kept denser) and mirror again (`sym_rigged.py`).
8. **UVs** (`uv_atlas_run.py`): xatlas, head charts x2.5, two uploads on one layout: whole body, and the head islands alone.
9. **Teeth** (`teeth_rebuild.py`): Meshy's jagged tooth rows replaced by 46 closed cones along the arcades, each rigid on its
   jaw, rooted in the gum, none reaching the opposite lip; all map into one ivory patch of free atlas space, so the paid
   layout stays valid.
10. **Paint** (`compose_dog.py`): 4K retextures downsampled once to 2K; head paint merged over the head by head weight, body
    paint elsewhere, so the face has the head masters' detail in one 2K map and no extra material. The mouth interior no
    master shows is painted per texel (palate ridges, floor, dark throat, tongue with a groove), eyes are procedural (the
    views disagreed between the eyes). Gentle grade. Class map `textures/dog_material_classes.png`.
11. **Clips** (`clips_mm9.py`, `clips_keys.py`): MM9 key poses as PCHIP curves, loop seams closed (the 0.25 s run takes 8
    frames, so its cycle is sampled over those 8). Hit and Death are key poses from `stand` in armature space.
    `neck_spread.py` then moves 60% of Xheadpiv's turn onto XneckA and XneckB on every frame: MM9 bends up to 83 deg in that
    one joint, which folded our nape into a spike. The head keeps MM9's world orientation; its position moves a little.
12. **Runtime** (`build_runtime.sh`): prepare, LODs, shadow shrink (tongue exempt), specular 0, floor pass, winding.

## Rebuild

```sh
T=<lease token>; B="tools/run_creature_blender.sh --token $T"; P=level_generation/creatures/mm9_dog_claude
V=level_generation/props/mm9_isleofashes_claude/work/venv/bin/python
$V tools/mm9_import_discovery/convert_abc_model.py mm9/extracted/MODELS/MODELS/DOG.abc $P/source/dog --id dog \
  --texture 0=mm9/extracted/SKINS/SKINS/DOG.dtx --scale 0.0256
$B $P/scripts/mm9_rig_source.py $P/source/dog/dog.glb $P/work/mm9_dog_rig.blend 0 0.4967
STRAND_BOX=-0.09,0.09,-0.38,-0.05,-0.31,0.06 STRAND_THICK=0.008 CLEAN_MODE=none $B $P/scripts/clean_meshy.py \
  $P/meshy/dog_smart_v1/model_urls_glb.glb $P/work/dog_clean_v1.glb 0.0035 0
STRETCH_MAX=1.45 HEAD_ROT=sym HEAD_DIFFUSE=200 $B $P/scripts/fit_quad.py $P/work/mm9_dog_rig.blend $P/work/dog_clean_v1.glb \
  $P/work/fit_v1.blend $P/work/fit_v1.json
KEEP=neg MID_BAND=0.03 MID_ITERS=15 $B $P/scripts/symmetrize.py $P/work/fit_v1.blend $P/work/sym_v1.blend $P/work/sym_v1.json
$B $P/scripts/mouth_carve.py $P/work/sym_v1.blend $P/work/carve_v1.blend $P/work/carve_v1.json -0.40 0.0055 0.7475 0.03 0.0047
KEEP=neg MID_BAND=0.012 MID_ITERS=4 $B $P/scripts/symmetrize.py $P/work/carve_v1.blend $P/work/carve_sym.blend $P/work/carve_sym.json
RIG_DIFFUSE=120 RIG_HINGE=20 $B $P/scripts/rig_body.py $P/work/carve_sym.blend $P/work/rig_v2.blend $P/work/rig_v2.json
$B $P/scripts/reduce_body.py $P/work/rig_v2.blend $P/work/reduced_v2.blend $P/work/reduced_v2.json 0.0042 0.3 0.022
$B $P/scripts/reduce_body.py $P/work/reduced_v2.blend $P/work/reduced_v3.blend $P/work/reduced_v3.json 0.6 1.0 0.62
$B $P/scripts/sym_rigged.py $P/work/reduced_v3.blend $P/work/reduced_v3s.blend $P/work/reduced_v3s.json Xearbase=Xearbase1,Xearpiv=Xearpiv1
$B $P/scripts/refine_weights.py $P/work/reduced_v3s.blend $P/work/refined_v1.blend $P/work/refined_v1.json
$B $P/scripts/mouth_weights.py $P/work/refined_v1.blend $P/work/mouth_v1.blend $P/work/mouth_v1.json
$B $P/scripts/uv_atlas_run.py $P/work/mouth_v1.blend $P/work/uv_v1.blend $P/texturing/dog_body_upload.glb \
  $P/texturing/dog_head_upload.glb $P/work/uv_v1.json Xheadpiv,Xhead,Xmouth,Xjawpiv,Xearbase,Xearpiv,Xearbase1,Xearpiv1 2.5
# xatlas packs differently per run: never re-run the UV step once the uploads went to Meshy (dog_retexture_v1, dog_head_retexture_v1)
$B $P/scripts/teeth_rebuild.py $P/work/uv_v1.blend $P/work/uv_v2.blend $P/work/teeth_v2.json
HEAD_GROUPS=Xheadpiv,Xhead,Xmouth,Xjawpiv,Xearbase,Xearpiv,Xearbase1,Xearpiv1 JAW_GROUPS=Xjawpiv \
  $B $P/scripts/dump_uv3d.py $P/work/uv_v2.blend $P/work/uv3d_dog.npz Body
$B $P/scripts/bake_ao.py $P/work/uv_v1.blend Body $PWD/$P/textures/dog_ao_2k.png 0.035 2048
(cd $P && python3 scripts/compose_dog.py && python3 ../claude_shared/grade_basecolor.py --ao textures/dog_ao_2k.png \
  --fine 1.0 --local 0.3 --ao-strength 0.5 --contrast 1.06 --saturation 1.15 textures/dog_basecolor.png)
$B $P/scripts/build_export.py $P/work/uv_v2.blend $P/work/anim_v2.blend $P/export/mm9_dog_lod0.glb $P/work/clips_v2.json
python3 tools/creature_workspace.py run --project $P --token $T -- $P/scripts/build_runtime.sh --install
flock -x level_generation/creatures/claude_shared/locks/mm9_actors_yml.lock \
  python3 $P/scripts/bind_actors.py mm9_dog_claude $P/work/actors_block.yml
(cd $P && python3 scripts/mm9_viewer_model.py source/dog/dog.glb review/viewer/mm9_dog.glb 0.4967 Standing=stand:1.4 \
  Walking=walk:0.5 Running=run:0.26667 Fidget=fidget1:3.0 AttackMelee=Bark:2.0 Hit=stand:0.5 Death=stand:1.2 && \
  python3 scripts/make_viewer_manifest.py r7_dog_20261030 "dog=Dog (295, dog.dtx)=export/mm9_dog.glb" \
  "mm9_dog=MM9 original (reference)=review/viewer/mm9_dog.glb")
```

## Checks (2026-10-30)

- Viewer `review/viewer/` (r7, MM9 original as second model): `tools/run_creature_review.py check` 8 clips, 16 switches, 0
  console errors. Acceptance from viewer shots, each looked at: `review/sheet_mm9_vs_ours.png` (MM9 left, ours right: rest
  and clip extremes), `review/sheet_a.png` (other angles, Hit, Death, Dead), `review/sheet_texture_closeup.png` (face, open
  mouth with teeth and tongue, nape). Single-skin model, so there are no tier sheets.
- Winding `check_winding.py`: 0 inverted. Smooth shading `flat_shading_check.py`: flat 0.00. Detached
  `detached_parts_audit.py`: 0 detached of 64 components (the separate pieces are the teeth, tongue and eyes).
- Texture `texture_quality.py`: atlas 58.4%, density spread 1.13, fragments 0.9%, stretch p90 1.08.
- Gates `scripts/gates.py` (`review/gates.json`): loop seams 0; edge ratio p1 0.58-0.88, p99 1.23-1.99; largest single edge 25
  (in the bark).
- Fold measure `scripts/fold_measure.py`, worst faces in one frame: Standing 0, Hit 0, Walking 19, Running 34, Fidget 59,
  AttackMelee 22 (38 before the neck spread), Death 11, Dead 10. This measure missed the nape spike, which was found in a viewer
  shot: creases at the nape over 45 deg fell from 55 to 28 (bark) and 40 to 22 (Fidget).
- Orientation `scripts/orientation_gate.py` at 48 fps: head 3.8 deg or less, paws 7.2 deg or less (the neck spread leaves the
  head's orientation alone).
- Floor audit `floor_audit.py --world mm9`: dog ok (stand 0, walk -1.3 to +0.7, living -1.3, dead 0).
- Regression `mm9_actor_models_build_every_binding` (`--world mm9`): 66 descriptors on 32 models, 0 failed; `mm9_` filter
  passed=4 failed=0.
- Not run: an in-game check (optional in the brief).

## Deviations and open points

- MM9 has no Hit, Death or attack clip for the dog (an NPC animal): Hit and Death are authored key poses, not MM9 motion;
  Bark serves as the attack because the generator makes the row `Aggress` and the engine requires attack clips.
- Bark runs 2 s with five barks, one attack; the impact is the second bark.
- Unused MM9 clips: run(away), sitting, walkbark, walksniff.
- The row is `Stationary` in the generated table (its MM9 Move column is 0).
- Xheadpiv, XneckA and XneckB differ from MM9's keys (`neck_spread.py`): same head orientation, a slightly different neck curve.
- MM9's dog is a redder brown; ours follows the HD masters (more orange tan). The mouth is narrowly open at rest, as MM9's.
- The closed lips are a slit of about 1 cm, wider than a real dog's, because the voxel pass closes anything narrower.
- User artistic acceptance: not recorded.
