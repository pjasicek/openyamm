# MM9 Hen (mm9_hen) — 3D model, 2026-10-30

The MM9 hen (`mm9/extracted/MODELS/MODELS/HEN.abc`, 34 nodes, 189 tris, 13 clips, skin HEN.dtx) for MM9 NPC row 269
(`hen.scr`, Hostility 2). Built on the MM9 rig-reuse route (`../mm9_dfly_claude/`, `../mm9_wolf_claude/`,
`../mm9_crow_claude/`): a new HD Meshy hen weighted to the original MM9 skeleton, the MM9 clips played with only the
listed fixes. The rooster (`../mm9_rooster_claude/`) shares the scripts. Progress and receipts:
`creature_3d_progress.json`.

| Item | Value |
|---|---|
| Runtime GLB | `assets_source/worlds/mm9/models/mm9_hen.glb` (cooked copy in `assets_dev`) |
| Binding | `assets_dev/worlds/mm9/models/actors.yml` block `mm9_hen_claude`: descriptor MM9 269 Hen, scale 100 (100 x MONSTERS.txt `Scale` 1), one skin |
| Data | `tools/mm9_import_discovery/mm9_npc_actor_rows.tsv` row 269 -> legacy Chicken A (466), runtime id 9269 |
| Triangles LOD0/1/2/3 | 6,053 / 3,025 / 1,087 / 357 |
| Skeleton | the MM9 one, names unchanged (`XCENTER`, `Xbody`, `Xneck/B/C`, `Xhead`, `Xbeak`, `Xtail/A/B`, legs `Xlegpiv-Xuprleg-Xleg-Xlowrleg-Xfoot`, toes `Xtoepiv*`, `Xtoe*`) + `Socket_Mouth` at the beak tip |
| Clips (30 fps) | Standing 1.2 (Stand), Walking 0.9 (Walk), Running 0.3 (Run), Fidget 1.8 (Fidget1), AttackMelee 1.1 (HAttack1), Hit 1.4 (Wince1), Death 2.2 (Die1), Dead 1.0 |
| Events | peck 0.367 s (MM9 `Rattack` of HAttack1) |
| Gait | stride 0.24 (walk), 0.56 (run) model units per cycle (`scripts/gait_measure.py`) |
| Floor | ground rule; Running one uniform lift (+3 cm, no bob); `floor_audit.py --world mm9` ok |
| Meshy credits | **20** (backup account): body Smart Topology 5, head Smart Topology 5, 4K retexture 10 |

## Decisions

- **Head graft from the start.** The body Smart Topology's head had a thin bill and a flap under it. A head-only HD
  turnaround (`references_head/`, Codex) and a head-only Smart Topology gave a closed short deep beak and separate
  wattles; `scripts/graft_chicken.py` cuts the old head, places the new one and lofts the neck. Beak elevation: MM9
  -7 deg, ours -12 deg (eye -> tip set to MM9's Xhead -> tip, -12.4 deg).
- **Symmetry.** MM9 is symmetric; `scripts/sym_meshy.py` finds the Meshy mirror plane by ICP, cuts it and mirrors the
  right half (legs stood one forward; body and head). Mirror error before: mean 1.6 % of size.
- **Legs on MM9's chains.** Height is matched by a no-rotation ICP (free rotation pitched the bird). `scripts/
  leg_fit.py` moves the body 2 cm back so the legs meet MM9's, puts each shank cross-section on the MM9 leg polyline and
  yaws the feet 19 deg onto MM9's toe directions.
- **Beak closed; weights.** MM9 never opens the beak (0 deg in every clip), so there is no cavity. Skull, beak, comb and
  wattles are rigid on Xhead; the throat and the loft follow the neck chain (`scripts/rig_chicken.py`, crow lesson: no
  hanging chin). Toes take MM9's three `Xtoepiv*` by direction; the hind toe stays on Xfoot.
- **One texture set**, no separate head set: 2x head density in one 2K atlas; one skin, so no mask or ramps.
- **Compose** (`scripts/compose_chicken.py`): the paint left the hidden throat pocket dark (read as an open mouth from
  the front and below) and maroon blotches on the wattles; those texels take the feather and wattle colours.

## Rebuild

```sh
T=<lease token>; B="tools/run_creature_blender.sh --token $T"; P=level_generation/creatures/mm9_hen_claude
V=level_generation/props/mm9_isleofashes_claude/work/venv/bin/python   # any python with pygltflib
M=mm9/extracted/MODELS/MODELS; S=mm9/extracted/SKINS/SKINS; C=tools/mm9_import_discovery/convert_abc_model.py
$V $C $M/HEN.abc $P/source/hen --id hen --texture 0=$S/HEN.dtx --scale 0.0256
$B $P/scripts/mm9_rig_source.py $P/source/hen/hen.glb $P/work/mm9_hen_rig.blend 0 0.2902
$B $P/scripts/sym_meshy.py $P/meshy/hen_smart_v1/model_urls_glb.glb $P/work/hen_sym_v1.glb neg $P/work/sym_v1.json
$B $P/scripts/sym_meshy.py $P/meshy/hen_head_smart_v1/model_urls_glb.glb $P/work/hen_head_sym_v1.glb neg $P/work/head_sym_v1.json
NOCHAIN=1 NOHEAD=1 $B $P/scripts/fit_chicken.py $P/work/mm9_hen_rig.blend $P/work/hen_sym_v1.glb $P/work/fit_v1.blend $P/work/fit_v1.json
$B $P/scripts/leg_fit.py $P/work/fit_v1.blend $P/work/fit_v2.blend $P/work/fit_v2.json
$B $P/scripts/graft_chicken.py $P/work/fit_v2.blend $P/work/hen_head_sym_v1.glb $P/work/graft_v1.cfg.json $P/work/graft_v1.blend $P/work/graft_v1.json
$B $P/scripts/rig_chicken.py $P/work/graft_v1.blend $P/work/rig_v1.blend $P/work/rig_v1.cfg.json $P/work/rig_v1.json
$B $P/scripts/reduce_body.py $P/work/rig_v1.blend $P/work/reduced_v1.blend $P/work/reduced_v1.json 0.3 0.3 0.5
$B $P/scripts/uv_atlas_v4.py $P/work/reduced_v1.blend $P/work/uv_v1.blend $P/texturing/hen_body_upload_v1.glb $P/work/uv_v1.json
# xatlas packs differently per run: never re-run once the upload went to Meshy
python3 tools/creature_meshy.py --project $P --token $T submit --job hen_retexture_v1 --kind retexture \
  --request requests/hen_retexture_v1.json --credits 10     # then poll / download
$B $P/scripts/reanchor_pieces.py $P/work/uv_v1.blend $P/work/uv_v1b.blend
HEAD_GROUPS=Xhead,Xbeak JAW_GROUPS=Xbeak $B $P/scripts/dump_uv3d.py $P/work/uv_v1b.blend $P/work/uv3d_hen.npz Body
$B $P/scripts/bake_ao.py $P/work/uv_v1b.blend Body $PWD/$P/textures/hen_ao_2k.png 0.03 2048
python3 $P/scripts/compose_chicken.py && python3 $P/../claude_shared/grade_basecolor.py --ao $P/textures/hen_ao_2k.png \
  --fine 1.0 --local 0.3 --ao-strength 0.5 --contrast 1.06 --saturation 1.15 $P/textures/hen_basecolor.png \
  && python3 $P/scripts/compose_chicken.py
$B $P/scripts/build_export.py $P/work/uv_v1b.blend $P/work/anim_v1.blend $P/export/mm9_hen_lod0.glb $P/work/clips_v1.json
python3 tools/creature_workspace.py run --project $P --token $T -- $P/scripts/build_runtime.sh --install
flock -x level_generation/creatures/claude_shared/locks/mm9_actors_yml.lock \
  python3 $P/scripts/bind_actors.py mm9_hen_claude $P/work/actors_block.yml
(cd $P && python3 scripts/make_viewer_manifest.py r2_hen_20261030 "hen=Hen (HEN.dtx)=export/mm9_hen.glb")
```

`scripts/mm9_compare_glb.py` builds the MM9 reference tier (roles renamed, feet on the floor) for the MM9-vs-ours viewer
shots; `scripts/compare_sheet.py` makes the sheets. That tier is left out of the delivered manifest.

## Checks (2026-10-30)

- Viewer `review/viewer/` (own title, framings for a ground bird; `rear` looks up at the throat):
  `tools/run_creature_review.py check` 1 skin x 8 clips, 0 console errors; playback `review/playback/`.
- Sheets from viewer shots: `review/sheet_rest_mm9_vs_ours.png`, `review/sheet_clips_mm9_vs_ours.png` (same camera,
  time and light; the MM9 reference tier), `review/sheet_texture_closeup.png`. All shots read by the author.
- `texture_quality.py`: atlas 60.6 %, equivalent 1595 px, density p50 1034, spread 1.06, 108 islands, fragments 0.0 %,
  stretch p90 1.11, 4K source. Flat shading 0.00.
- Head (`scripts/head_angles.py`, 48 fps, against MM9's mesh; `review/head_angles.json`): bind direction 3.8 deg off
  MM9 (MM9's skull set is coarse); orientation max per clip: Standing 4.3, Walking 5.4, Running 4.4, Fidget 6.3,
  AttackMelee 8.7, Hit 11.7, Death 11.8; roll max 7.1; fold 0.2 (rigid). Middle toes within 2.7 deg in Standing, 16.8 max.
- Neck/feet gate (`scripts/region_gate.py`): neck edge ratio p1 0.74-0.93, folded neck triangles 0-3 (Death, Dead);
  feet p1 0.43-0.98, 0-3 folded at the toe roots in Running and Death.
- Gates `review/gates.json`: loop seams 0; edge ratio p1/p99 per clip 0.62-0.92 / 1.08-1.64.
- Jitter (`scripts/jitter.py`, XCENTER height acceleration per frame, MM9 / ours, mm): Walking 3.8 / 3.1, Running 16.4
  / 18.2, AttackMelee 51.3 / 36.2, Hit 1.3 / 1.2, Death 23.7 / 19.0. The floor offsets are low-passed (`floor_fix.py --smooth`).
- `detached_parts_audit.py` (strict rules, 30 fps): 0 detached in every clip (9 parts); the wing and tail tufts lift
  1.4-1.8 cm at one root in Fidget and Death.
- Winding 0 inverted. Floor audit `floor_audit.py --world mm9`: ok. Regression `mm9_actor_models_build_every_binding`
  (`--world mm9`): 0 failed for this model (a run while the Fish project was mid-install flagged only that model).

## Deviations and open points

- MM9's second fidgets, `Sit`, Wince2 and Die2 are not exported; MM9 `Velocity`/`lunge` events are not reproduced
  (clips stay in place). The peck is a lunge in MM9 too: the body pitches and the feet leave the floor.
- MM9's fat boxy body is rounder and fuller here (HD master), with real folded wings where MM9 has a painted wing;
  wings are separate sheets rigid on the body under them.
- The head is the master's size, a little smaller than MM9's blocky head; the wattles are flat lobes.
- A small red paint speck remains behind the eye. Downward-facing feathers read grey in the viewer's hemisphere light.
- Comb and head are one shell; 28 triangles of collapsed slivers are dropped from LOD1-3 (`scripts/drop_lod_slivers.py`).
- User artistic acceptance: not recorded.


**LOD0 reduced post-install on 2026-11-04 by `level_generation/creatures/mm9_hen_reduce_claude/`** (ledger: `level_generation/creatures/REDUCTION_LEDGER.md`, "MM9 reduction"). A rebuild from this project must re-run that reduction, or it silently restores the heavier mesh. Rollback source: `level_generation/creatures/mm9_hen_reduce_claude/before/`.
