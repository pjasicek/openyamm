# MM9 goose (mm9_goose) — 3D model, 2026-10-30

The MM9 goose (`mm9/extracted/MODELS/MODELS/GOOSE.abc`, 21 joints, 184 tris, 8 clips) for two rows on one body: 293 Goose
(goose.dtx, duck.scr, Hostility 2) and 262 The Great Honk (goosebrown.dtx, Scale 1.5, basemelee.scr, Hostility 1). Both
are `IsMonster 0`. Built on the MM9 rig-reuse route of `../mm9_dfly_claude/`, `../mm9_wolf_claude/` and
`../mm9_crow_claude/`: a new HD Meshy mesh weighted to the original MM9 skeleton, the MM9 clips played with only the
listed fixes. Progress, hashes and receipts: `creature_3d_progress.json`.

| Item | Value |
|---|---|
| Runtime GLB | `assets_source/worlds/mm9/models/mm9_goose.glb` (cooked copy in `assets_dev`), skins `goose_a` (white), `goose_b` (Canada goose) |
| Binding | `assets_dev/worlds/mm9/models/actors.yml` block `mm9_goose_claude`: `MM9 293 Goose` scale 100, `MM9 262 The Great Honk` scale 150 |
| Data | `tools/mm9_import_discovery/mm9_npc_actor_rows.tsv` rows 293 (fallback 466 Chicken A), 262 (467 Chicken B); monsters 9293, 9262 |
| Triangles LOD0/1/2/3 | 5,788 / 2,894 / 1,040 / 346 (eyes 180) |
| Skeleton | the MM9 one, names unchanged: `XCENTER`, `Xbase`, `Xtail`, legs `Xleg-Xfoot-Xtoea/b/c` (+01), `Xback`, neck `XneckA/C/D/E`, `Xhead`, `Xbeak` |
| Clips (30 fps) | Standing 1.2 (stand), Walking 0.5 (walk), Running 0.3 (run), Fidget 2.2 (fidget2, grazing), AttackMelee 0.5 (Hattack1), Hit 0.8 (wince1), Death 1.7 (die1), Dead 1.0 |
| Events | peck impact 0.357 s (MM9 `Rattack` of Hattack1) |
| Gait | stride 0.37 (walk), 0.45 (run) model units per cycle (`scripts/gait_measure.py`), `gait_rate [0.8, 1.6]` |
| Floor | ground rule, root offsets low-passed; `floor_audit.py --world mm9` ok |
| Meshy credits | **25 / 30** (backup account): Smart Topology 5, 4K retexture 10, second 4K retexture on the repaired mesh 10 |

## Decisions

- **The beak does not open.** MM9's goose has no jaw bone and `Xbeak` never moves against `Xhead` in any clip, so the
  peck is a closed bill and there is no mouth cavity. The whole head is rigid on `Xhead`.
- **Great Honk colours are regions, not a second paint.** GOOSEBROWN.dtx is a different design on the same UV layout
  (black neck and head, white chin patch, brown back, cream breast, black bill, dark feet). Four regions carry it: R
  back, G pale, B neck and head, A bill and feet; the eyes are in no region. The split is transferred from the skin:
  each texel takes the class of the nearest MM9 surface samples in the bind pose. Above the shoulders only black and
  the chin patch exist, the patch narrows to a point at its MM9 lower end, and black feathers ring the bill.
- **Each mask runs under the later regions.** The shader mixes the channels in order, so two feathered masks meeting at
  0.5 let a quarter of the white base through: a pale ring round the dark bill. Masks overlap by 4 texels instead.
- **Neck weights by axial position.** Hat functions along the joint polyline, so a joint splits its two bones 50/50;
  nearest-vertex labels kinked the neck. Skull and bill are rigid within 4.5 cm of the mid-eye point.
- **The web curls as one plate.** MM9 curls a foot's three toes together, so every web vertex in front of the ankle takes
  the three toes equally. Splitting the web by toe tore it.
- **Feet rebound to MM9's tilted bind** (`scripts/repose_v5.py`). MM9's bind holds the feet tilted 17-21 deg and its
  clips flatten them. Our flat bind feet therefore tilted 22/19 deg in Standing. Each foot is placed in the `stand`
  pose on MM9's plane and yaw, then pulled back through its own skinning matrix: tilt in Standing 3-6 deg as MM9.
- **Bill reshaped** (same script). Meshy thinned the master's bill to a wader's. Length x0.76 and blunter (thicker
  towards the tip), so it is shorter than the head and deep at the base, as a real goose. It is shorter than MM9's.
- **Belly and claws** (`scripts/repair_v6.py`). Moving the legs 5 cm back onto MM9's joints pushed belly skin into the
  Meshy ledge behind them (hollows, a loose lip): relaxed. Three needle claw shards are drawn in to 10 % of their length.
- **Second retexture.** The bill and belly edits stretched the first paint (stretch p90 2.26), so the final mesh got new
  UVs and a new 4K paint (10 credits).
- **No voxel rebuild.** The return has no fused layers (interior area 0.3 %, the wolf's a third), and a fine voxel surface
  left terraces visible in the shading.
- **Neck re-centred** on MM9's joints in the fit (per slice, depth x0.85, ramped over the shoulders): it lay 4.5 cm in
  front of the bones, so bends pivoted at the back of the neck.
- **Head and legs by landmarks** (`scripts/fit_goose.py`): MM9's eye found through the skin's eye texels, mid-eye and bill
  tip matched; the LBS chain fit twisted the webs, so each leg moves by the tarsus offset and turns to MM9's toe yaw.

## Rebuild

```sh
T=<lease token>; B="tools/run_creature_blender.sh --token $T"; P=level_generation/creatures/mm9_goose_claude
V=level_generation/props/mm9_isleofashes_claude/work/venv/bin/python
M=mm9/extracted/MODELS/MODELS; S=mm9/extracted/SKINS/SKINS; C=tools/mm9_import_discovery/convert_abc_model.py
$V $C $M/GOOSE.abc $P/source/goose --id goose --texture 0=$S/GOOSE.dtx --scale 0.0256
$V $C $M/GOOSE.abc $P/source/goosebrown --id goosebrown --texture 0=$S/GOOSEBROWN.dtx --scale 0.0256
$B $P/scripts/mm9_rig_source.py $P/source/goose/goose.glb $PWD/$P/work/mm9_goose_rig.blend 0 0.3958
$B $P/scripts/clean_sym.py $P/meshy/goose_smart_v1/model_urls_glb.glb $PWD/$P/work/goose_clean_v2.glb 0 1 $PWD/$P/work/clean_v2.json
$B $P/scripts/fit_goose.py $PWD/$P/work/mm9_goose_rig.blend $PWD/$P/work/goose_clean_v2.glb $PWD/$P/work/fit_v3.blend $PWD/$P/work/fit_v3.json
RIG_DIFFUSE=20 RIG_HINGE=4 $B $P/scripts/rig_body.py $PWD/$P/work/fit_v3.blend $PWD/$P/work/rig_v3.blend $PWD/$P/work/rig_v3.json
MM9_BLEND=$PWD/$P/work/mm9_goose_rig.blend $B $P/scripts/refine_goose.py $PWD/$P/work/rig_v3.blend $PWD/$P/work/rig_v4.blend $PWD/$P/work/refine_v4.json
$B $P/scripts/reduce_body.py $PWD/$P/work/rig_v4.blend $PWD/$P/work/reduced_v4.blend $PWD/$P/work/reduced_v4.json 0.3 0.6 0.5
$B $P/scripts/uv_atlas.py $PWD/$P/work/reduced_v4.blend $PWD/$P/work/uv_v4.blend $PWD/$P/texturing/goose_body_upload.glb $PWD/$P/work/uv_v4.json
$B $P/scripts/repose_v5.py $PWD/$P/work/uv_v4.blend $PWD/$P/work/mm9_goose_rig.blend $PWD/$P/work/uv_v5.blend $PWD/$P/work/repose_v5.json
$B $P/scripts/repair_v6.py $PWD/$P/work/uv_v5.blend $PWD/$P/work/uv_v6.blend $PWD/$P/work/repair_v6.json
$B $P/scripts/uv_atlas.py $PWD/$P/work/uv_v6.blend $PWD/$P/work/uv_v7.blend $PWD/$P/texturing/goose_body_upload_v2.glb $PWD/$P/work/uv_v7.json
# xatlas packs differently per run: never re-run once the upload went to Meshy (goose_retexture_v2)
HEAD_GROUPS=Xhead,Xbeak JAW_GROUPS=Xbeak $B $P/scripts/dump_uv3d.py $PWD/$P/work/uv_v7.blend $PWD/$P/work/uv3d_goose.npz Body
$B $P/scripts/bake_ao.py $PWD/$P/work/uv_v7.blend Body $PWD/$P/textures/goose_ao_2k.png 0.03 2048
python3 $P/scripts/compose_goose.py && python3 $P/../claude_shared/grade_basecolor.py --ao $P/textures/goose_ao_2k.png \
  --fine 1.0 --local 0.3 --ao-strength 0.5 --contrast 1.06 --saturation 1.15 $P/textures/goose_basecolor.png \
  && python3 $P/scripts/compose_goose.py
$B $P/scripts/build_export.py $PWD/$P/work/uv_v7.blend $PWD/$P/work/anim_v7.blend $PWD/$P/export/mm9_goose_lod0.glb $PWD/$P/work/clips_v7.json
python3 tools/creature_workspace.py run --project $P --token $T -- $P/scripts/build_runtime.sh --install
flock -x level_generation/creatures/claude_shared/locks/mm9_actors_yml.lock \
  python3 $P/scripts/bind_actors.py mm9_goose_claude $P/work/actors_block.yml
(cd $P && python3 scripts/viewer_tiers.py && python3 scripts/mm9_viewer_model.py source/goose/goose.glb review/viewer/mm9_goose.glb \
  0.3958 Standing=stand Walking=walk Running=run Fidget=fidget2 AttackMelee=Hattack1 Hit=wince1 Death=die1 \
  && python3 scripts/make_viewer_manifest.py r4_goose_20261030 "goose_a=Goose (293, goose.dtx)=review/viewer/goose_a.glb" \
  "goose_b=The Great Honk (262, goosebrown.dtx)=review/viewer/goose_b.glb" \
  "mm9_goose=MM9 Goose (reference)=review/viewer/mm9_goose.glb" "mm9_honk=MM9 Great Honk (reference)=review/viewer/mm9_honk.glb")
```

## Checks (2026-10-30)

- Viewer `review/viewer/`: `run_creature_review.py check` 4 models x 8 clips, 0 console errors. The MM9 originals are
  models in the viewer, for the same clip and time side by side. Playback `review/playback/`.
- Sheets from viewer shots: `review/compare_viewer_sheet.png` (MM9 goose above ours: rest and every clip's extremes),
  `review/compare_tiers_sheet.png` (MM9 Great Honk above ours), `review/texture_sheet.png` (head, throat from below,
  neck base, body, tail, feet, soles).
- Texture quality: atlas 53.0 %, spread 1.05, fragments 0.0 %, stretch p90 1.11, 78 islands, 4K source.
- Symmetry: above the legs mirror distance mean 0.18 mm (MM9 1.0 mm).
- Orientation (`scripts/orient_gate.py`, `review/orient_gate.json`, 48 fps): bill direction vs MM9 7 deg at rest, max 15
  deg in Death; MM9's eye triangle bends with the neck while our head is rigid, and MM9 turns the head up to 127 deg.
  Roll follows: both heads are mirror-symmetric and rigid on the same bones. Sole normal vs MM9: 4-7 deg in Standing,
  Fidget and Hit; up to 25 (walk) and 41 (run) while the toes curl, where MM9's three toes curl unevenly and ours as a plate.
- Gates (`scripts/gates.py`, `review/gates.json`): loop seams 0; edge ratio p1/p99 0.64-0.86 / 1.19-1.55; largest edge
  3.1. Folded faces worst frame 83 (of 5,788), mostly feather ledges at rest (49 in Standing).
- Jitter (`scripts/jitter_gate.py`, `review/jitter_gate.txt`): per-key floor offsets shook the walk, so they are
  low-passed (`floor_fix.py --smooth`); the offset's second difference is now below the clip's own in every clip.
- Attachment `detached_parts_audit.py`: 0 detached. Shading `flat_shading_check.py`: 0.01. Winding: 0 inverted.
- Floor audit `--world mm9`: Goose and Great Honk ok. Regression `mm9_actor_models_build_every_binding`: 61 descriptors on
  28 models, 0 failed.

## Deviations and open points

- Atlas 53.0 % misses the 55 % target (the first layout had 59.5 %); xatlas packs differently per run and the paint is
  bound to this layout. Spread, fragments and stretch are well inside their targets.
- Tier-A ramp error on the bill and feet region is about 10 levels (orange and dark claws in one region); the four
  channels are all in use for the Great Honk. No visible loss in the viewer.
- The bill is shorter than MM9's on purpose (real goose proportions); the Great Honk's bill is brown-black, not MM9's
  blue-black.
- The brown back is even, without MM9's dark blotches: the ramps follow the white paint's luminance.
- A hairline at a UV seam on the black neck shows up close (the 1K mask across the 2 px gutter).
- The feet are low-poly in extreme close-up.
- fidget1 is not exported (the engine has one fidget). MM9 `Velocity` events are not reproduced. MM9 `HeadTurn` of the
  Great Honk is not bound.
- No in-game run. The review root (`output/mm9_rework/assets_dev`) was refreshed.
- User artistic acceptance: not recorded.


**LOD0 reduced post-install on 2026-11-04 by `level_generation/creatures/mm9_goose_reduce_claude/`** (ledger: `level_generation/creatures/REDUCTION_LEDGER.md`, "MM9 reduction"). A rebuild from this project must re-run that reduction, or it silently restores the heavier mesh. Rollback source: `level_generation/creatures/mm9_goose_reduce_claude/before/`.
