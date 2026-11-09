# MM9 Bjarni Thorvaldssen, Jarl of Sturmford (mm9_bjarni) — 3D actor, 2026-11-02

Townsfolk batch wave 3 (`devdocs/mm9_rework/overnight/TOWNSFOLK_BRIEF.md`), unique humanoid. MM9 `MONSTERS.txt` row **246
"Bjarni Thorvaldssen"**: `Bjarni.abc` + `bjarni.dtx`, NPCbase.scr, Scale 1, BaseName **PeasantMale**. Only this row names the
model. Built on the Annud/PeasantM7 route: Meshy body fitted to BJARNI.abc's own skeleton (the 45-joint PeasantMale biped,
names and rest rotations unchanged), MM9 clips only (PeasantMale library + BJARNI.abc's own clips), MPFB five-finger hands, a
separate head set. Progress, hashes and Meshy receipts: `creature_3d_progress.json`.

| Item | Value |
|---|---|
| Runtime GLB | `assets_source/worlds/mm9/models/mm9_bjarni.glb` (sha256 e51870d1339e4c39..., installed with `tools/install_model.py --world mm9 --name mm9_bjarni.glb` from `export/mm9_bj.glb`; cooked copy in `assets_dev`) |
| Binding | `assets_dev/worlds/mm9/models/actors.yml` block `mm9_bjarni_claude`: `MM9 246 Bjarni Thorvaldssen`, scale 100, `yaw_offset -1.570796327`, stride walk 1.1 / run 2.8, look `Bip01 Neck, Bip01 Head`, impact 0.5 s (hattack1 `Rattack`), script clips below |
| Descriptor | row 246 (legacy stand-in 586, Nobleman A) appended to `tools/mm9_import_discovery/mm9_npc_actor_rows.tsv`; tables regenerated (`generate_mm9_monster_tables.py`: 9246 `MM9 246 Bjarni Thorvaldssen`, 183 rows) |
| Triangles LOD0/1/2/3 | 8,089 / 4,036 / 1,444 / 475 (Smart Topology 14,596; head and hair 2,122, two MPFB hands 1,398) |
| Skeleton | BJARNI.abc = PeasantMale (45 joints), joints translated onto the HD body (Spine2/Spine3 interpolated between Spine1 and Neck: the yoke's back panel hangs clear of the back and pulled them 12.6 cm back); + 15 finger bones per side driven from MM9's mitten curl (`finger_alias`); mirrored to MM9's true handedness (`mirror_glb.py`) |
| Textures | body 2K colour + 1K normal + 1K ORM; head + hands set 2K colour + 1K normal/ORM; one skin, no tiers; `openyamm_specular 0`, metallic 0 |
| Meshy credits | **25** (Smart Topology 5, body retexture 4K 10, head retexture 4K 10; backup account, 3430 -> 3405) |
| Codex | 3 runs through `codex_slot.sh` (masters 00, masters 01-04, head turnaround) |

## Placements and the clips his scripts play

DAT objects naming the model (`scripts/dat_objects.py`):
- `BjarniThorvaldssen` (row 246) in **Afterworld** (no script: row default NPCbase.scr -> npcBase.inc -> BaseRun.inc `LoopAnim
  Cower`, Converse -> talk) and **Thronheim City** (`ARG_Bjarni.scr`, the Argument scene: `loopanim Sit`; `Agree`, `Applause`,
  `Sc2_Bjarni1a` on Shot1A (keys Sign, Cam3), `Sc2_Bjarni1c` on Shake, `Sc2_Bjarni2` / `Sc2_bjarni9` / `Sc2_bjarni15` on
  Speak2/9/16, each back to Sit). Its DAT `Filename` says `Kira.abc` (a DEdit leftover; the row decides the model).
- Props, not monster rows (not bound here): the Sturmford `RUDEProp` "Bjarni" (`Bjarni.scr`: `loopanim Sit`, `listen`) and the
  Thronheim `RUDEProp` "BjarniProp" (`PropAnim Sit`) are the existing decoration `mm9_bjarnisitting` (the native MM9 model posed,
  level_generation/props/mm9_sturmfordcity_claude); the corpse props "Kira0" in Afterworld and Yorwick are `bjarni.abc` +
  `bjarni.dtx` in `Static_die1` (named Kira in the DAT, but they are Bjarni's model and skin; Kira's status file lists them as
  hers). Swapping those props to this model posed in Sit / Dead would be a props-project change.
- `SigmundtheStressed` objects carry `Filename models\Bjarni.abc` too, but row 247 is `sigmund.abc` (another body).

Roles (`scripts/roles_bj.json`, 30 fps, sources `source/mm9_lib/pmale.glb` and `source/mm9/bjarni.glb`): Standing stand1,
Walking walk3, Running run, Fidget fidget4, Talk conv2, AttackMelee hattack1 (impact 0.5 s), Hit wince1, Death die1, Dead,
Cower cower; own clips Sit, Agree, Applause, ArgumentShot1A (Sc2_Bjarni1a), ArgumentShake (Sc2_Bjarni1c), ArgumentSpeak2,
ArgumentSpeak9, ArgumentSpeak16 (Sc2_bjarni15). Script clip names in actors.yml follow Forad's Argument binding (`sit`, `agree`,
`applause`, `argument_shot1a`, `argument_shake`, `argument_speak2/9/16`, plus `talk`, `conv2`, `cower`, `stand`). Left out: the
own `Bjarni` (reference pose), `static_die1` (the props'), `Sc2_bjarni3` (not played), and every other library clip.
The seated clips keep MM9's seat: Sit is grounded, the other scene clips take Sit's offset (`floor_fix.py --seat-like`, new
opt-in option) so the sitter does not drop when a foot lifts (per-key grounding failed the shoulder-skin jitter); Speak9/16
stretch the toes 4 cm lower than Sit's feet, lifted by a smoothed `--raise`. In Speak16's first and Speak9's last keys the feet
stick out toward the viewer with the soles up, as in MM9 (`review/mm9_pose_sheet.png`).

## Route (scripts/, project folder unless noted)

0. **HD masters** (`references_hd/`, brief `CODEX_BRIEF.md`, `codex_masters.sh 1|2`, inputs `mm9_views.png`,
   `mm9_head_views.png`, `mm9_skin_x4.png` from `ref_renders.py` on `source/mm9/bjarni.glb`); halo removed by `clean_alpha.py`
   (raw in `raw_codex/`). Head turnaround `references_head/` (`codex_head.sh`; the brief asks for open eyes with irises, one brow
   per side, no pale band under the brows or at the hairline).
1. **Meshy** Smart Topology 15k from `00_three_quarter.png` (`requests/smart_topology_v1.json`).
2. **Fit** `fit_rig.py` + `fit_config.json` (new option `centre_span`), X-ray `review/xray_v1_*.png`; **reduce** `reduce_uv.py`
   (`reduce_config.json`) -> `work/rig_v1.blend`; **hands** `graft_hands.py graft_bj.json` (MPFB macro age 0.7);
   **head split** `head_split.py head_bj.json` (neck cut 0.64, radius 0.19 so the back hair is in the head set, necklace beads
   excluded) -> `work/head_v1.blend`, `review/head_split.png`; **sleeve tuck** `sleeve_tuck.py work/head_v1.blend
   work/head_tuck.blend 0.75 0.003` (before the UVs: L 17 / R 20 stub vertices moved in).
3. **UVs** `texpass_uv.py work/head_tuck.blend work/texpass_uv.blend texturing/bj_body_upload_tp.glb` (body atlas 59.9 %),
   `texpass_head_uv.py` -> `work/texpass_head.blend`, `texturing/bj_head_upload_tp.glb`. Never re-run: the paid textures belong
   to these layouts.
4. **Retextures** 4K: `requests/retexture_body_tp.json`, `requests/retexture_head_tp.json`.
5. **Mesh fixes on the master** (geometry only, UVs unchanged): `fix_flips.py work/texpass_head.blend work/texpass_head_fx.blend`
   (6 triangles wound against their vertex normals: nostril, forehead, temple, crown, belt; the nostril one rendered as a dark
   square), `remove_specks.py work/texpass_head_fx.blend work/texpass_head_fx2.blend 8 "0.177,0.011,0.126;0.051,-0.157,0.222"`
   (the two loose chips the detached audit flagged; the belt and trouser studs stay).
6. **Maps** `bake_ao_texpass.py work/texpass_head.blend textures/bj_tp_ao_2k.png`; `compose_texpass.py bj_tp
   meshy/body_retexture_tp texturing/bj_body_upload_tp.glb textures/bj_tp_ao_2k.png`; `grade_basecolor.py --fine 1.0 --local 0.3
   --ao-strength 0.5 --contrast 1.06 --saturation 1.15`; `bake_hands.py work/texpass_head.blend
   middleage_caucasian_male/middleage_lightskinned_male_diffuse.png`; `compose_headhand.py bj_tp meshy/head_retexture_tp
   textures/bj_tp_basecolor_graded.png textures/bj_tp_material_classes.png textures/bj_tp_metal_rough_1k.png --ref-head
   --hand-gain 1.12` (kept as `work/bj_tp_head_basecolor_composed.png`); `hand_clean.py`; `moustache_fix.py` (a grey smudge
   Meshy painted in the moustache under the left nostril, which the hole-fill triangles there also sample, takes beard strands
   from 38 texels below); `eye_rim_fix.py export/mm9_bj.glb` (lid texels within 2 cm of each eye centre that read red move 60 %
   toward the skin ring around the eye, own luminance kept).
7. **Runtime** `PYGLTF_PYTHON=../claude_shared/gltf_venv/bin/python TOKEN=<lease> HEADTEX=bj_tp BODYTEX=bj_tp
   BLEND=work/texpass_head_fx2.blend PYTHONPATH=/usr/lib/python3/dist-packages scripts/build_runtime_v2.sh bj Bjarni
   scripts/roles_bj.json` (export with `export_fix` in `head_bj.json`: Meshy's eyeball cups dropped by position (`drop_at`, new
   opt-in option in `build_export_v2.py`; they poked through the lower lids as a light outlined band), one 5-edge hole filled ->
   `clips_mm9.py` (soft offsets) -> `hand_rest.py` per `hand_rest_bj.txt` (Fidget, Talk) -> prepare -> LODs -> shadow fix ->
   extras -> `floor_fix.py` per `floor_ops.txt` -> `mirror_glb.py` -> winding). No region variants (one skin). Install as above.
8. **Binding** (repo root, under the flock): `flock level_generation/creatures/claude_shared/locks/mm9_actors_yml.lock bash -c
   'python3 level_generation/creatures/mm9_bjarni_claude/scripts/bind_actors.py && python3
   tools/mm9_import_discovery/generate_mm9_monster_tables.py'`, then `level_generation/projects/mm9r_common/review_root.py`.
9. **Gates** `scripts/gates.sh <dir>`; viewer `scripts/make_viewer_bj.py <rev>` + `tools/run_creature_review.py check`.

## Faults the siblings shipped, checked here

- **Hands through the sleeves**: `sleeve_tuck.py` before the UVs; `sleeve_poke_gate.py` 0 mm in 17 of 18 clips, both sides.
  ArgumentShot1A R 28.5 mm on 2 vertices for 23 frames: two back-of-hand vertices 2 cm past the hand joint that MM9's 70 deg wrist
  bend folds back beside the cuff's outer wall (outside the cloth, not through it); close renders of frame 270 with the hand
  material in red (`review/poke_parts.png`, `review/poke_close.png`) show no skin through the sleeve.
  `sleeve_paint_fix.py` was tried and **rejected**: its skin test took the rust-red wrist trim of the cuffs (19,667 texels;
  `review/sleeve_paint_fix_mask_rejected.png`) and the retexture painted no skin wedges on the sleeves (`review/sheet_wrists.png`).
- **Hands**: one clean face-skin colour with the MakeHuman bake's luminance detail (`hand_clean.py`), natural nails.
- **Eyes and brows**: Meshy's separate eyeball cups were dropped (the lid band and a dark square under the left eye came from
  them); eyes open with blue irises from the party view, one brow per side, no pale band between brows and eyes
  (`review/sheet_face_closeup.png`, `review/face_closeup_r4.png`).
- **Fringe**: his fringe and hair are painted on the same shell as the face; the hairline reads clean in the brow close-ups, no
  pale jagged band (`fringe_fix.py` assumes a separate hair shell and was not applicable).
- **Neck and collar**: the neck cut sits under the beard inside the necklace ring; no collar paint on the neck, no seam visible.

## Checks (final build, `review/gates_final/`)

| Gate | Result |
|---|---|
| Arm and hand (`arm_hand_gate.py`, 48 fps) | hands 0 cm in body in every clip except **Fidget R 2.9 cm, 9 frames** (MM9's hand over the mouth, fingers into the beard; forearm 5.9 cm against the necklace beads at frame 50) and **Applause L 1.9 / R 2.0 cm** (the clapping hands meet, as Forad's). Finger stretch p99 <= 1.5, max 3.3 (Fidget L). Wrist max 119 deg (Death/Dead, MM9's limp hand). 19 joints per hand (five chains) |
| Sleeve poke (`sleeve_poke_gate.py`) | 0 mm in every clip except ArgumentShot1A R 28.5 mm (2 vertices, above) |
| Jitter (`jitter_gate.py` vs MM9's untouched clips) | **0 fails** (Speak9/16 failed the shoulder skin at 6-11 mm/f2 with per-key grounding; fixed by `--seat-like`) |
| Floor (`floor_audit.py --world mm9 --match 'MM9 246 *'`) | ok: stand 0, walk -0.5..+2.2, living -0.5, dead -0.0 world units (walk smoothing 0.12 -> 0.08 after the first audit flagged a 2.6-unit all-feet lift) |
| Winding | 0 inverted closed parts |
| Bones (`bone_length_audit.py`) | thigh translation 0.105-0.127 (MM9's own hip slide, as the PeasantMale siblings) |
| Detached (`detached_parts_audit.py`) | 0 detached in any pose (46 components) |
| Flat shading | 0.0 % body, 0.1 % head |
| Texture quality | body atlas **59.9 %**, density p10/p50/p90 1323/1395/1444 (spread 1.09), fragments 0.1 %, stretch p90 1.09; head set 44.7 %, spread 1.66 (hands half density by design), fragments 1.5 % |
| Viewer | revision r4-20261102, `run_creature_review.py check`: 18 clip switches, 0 failed, 0 console errors |
| Regression | `--world mm9 --headless-run-regression-suite actors`: passed 192, failed 1 (the known `out05 ... could not load gameplay data`; `review/regression_actors.log`, run on the first install); after the final reinstall (walk smoothing, eye rims) `mm9_actor_models_build_every_binding` **PASS** (184 descriptors on 77 models, 0 failed; `review/regression_binding.log`) |

Viewer: `http://127.0.0.1:8912/level_generation/creatures/mm9_bjarni_claude/review/viewer/index.html`.
Sheets read: `review/sheet_mm9_vs_ours.png`, `review/strips_final_a.png` + `review/strips_final_b.png` (every clip, six times),
`review/sheet_face_closeup.png` (party view, front, 3/4, eyes, brow, mouth, neck; bind and Talk), `review/face_closeup_r4.png`
(brow/fringe both 3/4s, Fidget), `review/sheet_wrists.png` (both hands, six clips, four views), `review/shots/*.png` (viewer),
`review/speak16.png`, `review/mm9_pose_sheet.png`, `review/head_split.png`, `review/xray_v1_*.png`.

## Binding plan (map placement)

The rebuilt maps place `BjarniThorvaldssen` with the legacy stand-in 586 through `transcode_mm9_dat_to_odm.py`, so the new
descriptor does not show in game yet. Per the brief this switch is the orchestrator's, once for every row after the batch:
placements of DAT class `BjarniThorvaldssen` should use 9246. No transcoder or map change here. The Argument scene's triggers
(Shot1A, Shake, Speak2/9/16, Agree, Clap) need a behaviour script to play the bound `argument_*` clips, as Forad's.

## Deviations and open points

- Shared tools gained opt-in options, defaults unchanged: `claude_shared/floor/floor_fix.py --seat-like REF CLIP`; the project's
  `build_export_v2.py` `drop_at`, `fit_rig.py` `centre_span`, `head_closeups.py` `UVMODE`/`IDMODE`/`PROBE`/`NOSHADOW`/`NONORMAL`
  and views `brow`, `browQ`, `browQL`, `party` (debug renders that locate a texel or a triangle from a pixel).
- Smart Topology modelled the tusk necklace as round beads (the paint carries the tusks); the yoke's back panel stands a few cm
  off the back in profile (the master's stiff yoke).
- Not looked at in game; motion judged on strips and the viewer, not watched at speed; LOD1-3 and shadow meshes not looked at.
- User artistic acceptance: not recorded.


**LOD0 reduced post-install on 2026-11-05 by `level_generation/creatures/mm9_bjarni_reduce_claude/`** (ledger: `level_generation/creatures/REDUCTION_LEDGER.md`, "MM9 reduction"). A rebuild from this project must re-run that reduction, or it silently restores the heavier mesh. Rollback source: `level_generation/creatures/mm9_bjarni_reduce_claude/before/`.


**See-through linings added post-install on 2026-11-05 by `level_generation/creatures/mm9_bjarni_lining_claude/`** (brief `devdocs/mm9_rework/overnight/LINING_BRIEF_20261105.md`; LOD0 6,841 -> 8,359, faces appended to the reduced mesh; yoke lined with reversed copies on its own UVs). A rebuild from this project must re-run the reduction and then the lining pass. Rollback source: `level_generation/creatures/mm9_bjarni_lining_claude/before/`.
