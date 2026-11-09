# MM9 Sven Svenssen, Jarl of Arslegard (mm9_sven) — 3D actor, 2026-11-02

Townsfolk batch wave 3 (`devdocs/mm9_rework/overnight/TOWNSFOLK_BRIEF.md`), unique humanoid. MM9 `MONSTERS.txt` row **249 "Sven
Svenssen"** (`Sven.abc`, skin `sven.dtx`, NPCbase.scr, BaseName PeasantMale, **Scale 1.25**) is the only row naming SVEN.abc or
SVEN_ARG.abc. Route: the PeasantM7 / PeasantDM1 chain (Meshy body fitted to the original MM9 skeleton, MM9's own clips, MPFB
five-finger hands, a separate head set, sharp textures from the start) plus a Codex face repaint by landmarks (PeasantM1 route).
Progress, hashes and Meshy receipts: `creature_3d_progress.json`.

| Item | Value |
|---|---|
| Runtime GLB | `assets_source/worlds/mm9/models/mm9_sven.glb` (`tools/install_model.py --world mm9 --name mm9_sven.glb` from `export/mm9_sven.glb`; cooked copy in `assets_dev`) |
| Binding | `assets_dev/worlds/mm9/models/actors.yml` block `mm9_sven_claude`: `MM9 249 Sven Svenssen`, **scale 125** (MONSTERS Scale 1.25), `yaw_offset -1.570796327`, stride walk 1.2 / run 3.1 (`stride.py`: walk 1.15/1.27, run 2.7/3.7 per foot), look `Bip01 Neck, Bip01 Head`, impact 0.5 s (hattack1 `Rattack`); one skin, no `skin:` variant |
| Descriptor | row `249 -> 520` (the stand-in of `mm9_npc_legacy_replacements.tsv`, legacy Dwarf A) appended to `tools/mm9_import_discovery/mm9_npc_actor_rows.tsv`; tables regenerated (`generate_mm9_monster_tables.py`): **9249 `MM9 249 Sven Svenssen`** |
| Triangles LOD0/1/2/3 | 8,405 / 4,202 / 1,508 / 501 (Smart Topology 14,951; body 3,244, head + hair + hands 5,161) |
| Skeleton | SVEN.abc = the 45-joint PeasantMale skeleton (rest rotations unchanged, joints translated onto the HD body) + 15 MPFB finger bones per side driven from MM9's mitten curl (`finger_alias`); whole model mirrored to MM9's true handedness (`mirror_glb.py`) |
| Clips (30 fps) | PeasantMale library (`source/mm9_lib/pmale.glb`, copied from mm9_peasantm1_claude): Standing stand1, Walking walk3, Running run, Fidget fidget4, Talk conv2, AttackMelee hattack1, Hit wince1, Death die1, Dead, **Cower** cower, **Bless** bless; from **SVEN_ARG.abc**: **Sit** sitting (loop), **Agree** agree, **Applause** applause |
| Textures | body 2K colour + 1K normal + 1K ORM; head + hands set 2K colour + 1K normal/ORM; `openyamm_specular 0`, metallic 0; no region mask (one skin) |
| Meshy credits | **25** (Smart Topology 5, body 4K retexture 10, head 4K retexture 10; backup account 3375 -> 3340 before the last job; no retries) |

## SVEN_ARG.abc (covered: the same body)

`SVEN_ARG.abc` is the same `Sven` piece (704 faces) with the same SVEN skin **plus a `Chair` piece (ChairPlain skin) on its own
`Bone01`**, in a seated bind pose (toes 0.38 m up). Its three clips are the Thronheim Argument scene: `sitting` (1.7 s),
`applause` (3.6 s, six `Clap` model keys) and `agree` (2.7 s). SVEN.abc's own `sit`/`Agree`/`Applause` are the same poses but
`Agree` 5.0 s and `Applause` 3.63 s; the scene plays the ARG versions, so those are carried. Because the ARG bind is seated,
`clips_mm9.py` gained an opt-in `rest_from` (the ARG clips take SVEN.abc's standing bind for rest translations and the leg
ratio; rotations were always copied absolutely). **The chair is not modelled**: in our engine the seated Sven needs a chair
decoration under him (the clips are grounded with the feet on the floor at MM9's seat height). SVEN.abc's other clips,
`Sven` (a 21-key placeholder) and `Sven_scene06` (a 43.7 s cutscene with camera events), are not played by any DAT object.

## Clips the MM9 scripts play (DAT objects)

| Map | Object | Model | Script | Animations |
|---|---|---|---|---|
| Afterworld | `SvenSvenssen0` (class BjarniThorvaldssen, hidden) | Sven.abc | none -> row default NPCbase.scr | BaseRun.inc `LoopAnim Cower` |
| Arslegard City | `SvenSvenssen0` (Trigger) | Sven.abc | NPC3.scr `Arslegard` | none (quests, Vanish; `loopanim Sit` commented out) |
| The Arena | `SvenArena` (Marker) | Sven.abc | SvenArena.scr `Sven0` | walkto (Walking), `Playanim Bless`, BaseMelee |
| Thronheim City | `Sven` (Prop) | Sven_ARG.ABC + chair | ARG_Sven.scr | `loopanim Sitting`, `PlayAnim Agree` / `Applause` (Clap keys -> clap sounds) |
| Thronheim City | `SvenProp` (RUDEProp) | Sven_ARG.ABC + chair | PropAnim.scr `Sit` | Sit |

The Afterworld/Yorwick `Sven0..Sven26` objects are ClanSoldier corpses (PropAnim static_die), Thjorgard's `Sven` is a
PeasantMale: not this body. `script_clips`: talk/conv2 -> Talk, cower, bless, sit/sitting -> Sit, agree, applause, stand -> Standing.

## Route (scripts/, repo root unless noted)

0. **MM9 sources** (`convert_abc_model.py`, scale 0.0256): `source/mm9/sven.glb`, `sven_arg.glb` (texture 1 = CHAIRPLAIN);
   renders `ref_renders.py` -> `references_hd/mm9_views.png`, `mm9_head_views.png`, `mm9_skin_x4.png`.
1. **HD masters** (Codex via `codex_slot.sh`, `codex_masters.sh 1|2`, brief `references_hd/CODEX_BRIEF.md`): five views in MM9's
   bind pose (arms 37 deg below horizontal, wrists at belt height), 1536x1024; halo removed by `clean_alpha.py` (raw in
   `raw_codex/`). Head turnaround `codex_head.sh` -> `references_head/` (eyes open, relaxed brows, closed smile).
2. **Meshy** Smart Topology 15k from `00_three_quarter.png` (`requests/smart_topology_v1.json`).
3. **Fit** `fit_rig.py` + `fit_config.json`. Two SVEN.abc-specific fixes: the imported rig kept its first clip (`sit`) posed on
   the bones (now reset to rest), and SVEN.abc has only 349 vertices, so the 3 cm centre band held a single back vertex at the
   neck (Neck/clavicles moved 27 cm): new opt-in `centre_band` 0.07, Spine3 interpolated (`centre_interp`; the long hair
   pushed it 20 cm back). X-ray `review/xray_v1.png`.
4. **Reduce** `reduce_uv.py` (14,951 -> 8,256), **hands** `graft_hands.py graft_sven.json` (MPFB muscle 0.7 / weight 0.6, grafted
   at the bracers), **head split** `head_split.py head_sven.json` (cut 0.62, part 0 spans the neck; the necklace plaques stay in
   the body set) -> `work/head_v1.blend`.
5. **UVs** `uv_pass.sh` (body atlas 60.8 %, head 54.6 %). **Never re-run**: the paid paints belong to `work/texpass_uv.blend`
   / `work/texpass_head.blend`.
6. **Paint** (project folder): `bake_ao_texpass.py`, `compose_texpass.py sven_tp ...`, gentle grade (`grade_basecolor.py
   --fine 1.0 --local 0.3 --ao-strength 0.5 --contrast 1.06 --saturation 1.15`), `bracer_paint_fix.py` (below);
   `bake_hands.py work/texpass_head.blend middleage_caucasian_male/...`, `compose_headhand.py sven_tp ... --ref-head
   --hand-gain 1.12` (composed head kept as `work/sven_tp_head_basecolor_composed.png`), `hand_clean.py 1.0`, then the face
   repaint (below).
7. **Wrists and accessories** (geometry/weights only, paints unchanged), in this order: `bracer_rigid.py work/texpass_head.blend
   work/wr_rigid.blend` -> `TUCK_DEEP=-0.025 TUCK_BLEND=0.03 sleeve_tuck.py ... work/wr_tuck.blend 0.75 0.003` -> `cuff_trim.py ...
   work/texpass_head_wrist.blend -0.019` -> `accessory_weights.py ... work/texpass_head_acc.blend 120 15` -> `drop_micro_parts.py
   ... work/texpass_head_final.blend 4` (all through `scripts/bl.sh`).
8. **Runtime** (project folder) `TOKEN=<lease> PYGLTF_PYTHON=<gltf venv python> HEADTEX=sven_tp BODYTEX=sven_tp
   scripts/build_runtime_sven.sh sven Sven scripts/roles_sven.json` (BLEND default `work/texpass_head_final.blend`): export ->
   `clips_mm9.py` (soft offsets, `rest_from`) -> `hand_rest.py` per `hand_rest_sven.txt` -> `clap_spread.py` (Applause 6 deg,
   Talk R 9 deg about the forward axis) -> prepare -> LODs -> shadow fix -> extras -> `floor_fix.py` (`floor_ops.txt`) ->
   `mirror_glb.py` -> winding. Gates `scripts/gates.sh`. Viewer `scripts/make_viewer_sven.py <rev>`.
9. **Binding** (repo root): `flock -x level_generation/creatures/claude_shared/locks/mm9_actors_yml.lock bash -c 'python3
   level_generation/creatures/mm9_sven_claude/scripts/bind_actors.py && python3 tools/mm9_import_discovery/generate_mm9_monster_tables.py'`.

## Face (the batch's failure point)

Meshy's head paint read stern: knitted brows with deep vertical frown furrows, heavy forehead creases, pale full pink lips and a
grey-white streak down the chin braid (`review/head_v1.png`). Fix, 0 Meshy credits, one Codex run:
- `render_face.py` unlit front render (centre z 1.635 m, ortho 0.30) -> Codex (`codex_face.sh`, brief
  `references_face/CODEX_BRIEF.md`): brows relaxed, no furrows, forehead smoothed, eyes kept; lips muted dusky rose, closed in a
  gentle smile (MM9's expression; the lips are paint only, so nothing is pushed out), beard one even brown.
- Codex moved features 6-12 px up: `warp_face.py` measures each landmark (eyes, nose, mouth corners, brows, chin, cheeks) by
  normalised cross-correlation and resamples the repaint through a smooth displacement field (residual 0-1 px).
- `project_face.py` (PeasantM1's, new opt-in `FACE_WINDOWS`) projects it through two windows only: brows/eyes/forehead (1.615-1.712
  m, |x| < 8.5 cm) and mouth/chin (1.505-1.592 m, |x| < 7 cm); the normal map is flattened there (the carved furrows go too).
- Hands: `hand_clean.py` (one clean skin colour 195/120/89, the face skin; the MakeHuman bake had come out 99/60/33 with veins).
Compared with MM9 at front, 3/4, side and the party view 22 deg above (`review/sheet_face4.png`): eyes open with light-blue
irises from party height, one relaxed brow per side, no light band, no red rims, no nostril holes, hairline with fine hairs and
no pale band (`review/sheet_neck_fringe.png`), neck closed with no seam. MM9's grin shows parted lips; ours stays closed.

## Wrists (bare arms with steel bracers)

The grafted stub showed 2-23 mm through the bracers in every clip and the bracer's distal rim was toothed (Meshy's cut, with
skin-painted shards). Causes and fixes:
- the bracer's own rim vertices carried hand weight, so the steel bent inward with the wrist: `bracer_rigid.py` puts every body
  vertex of the bracer (from 14 cm above the hand joint to the rim) 100 % on the forearm (playbook: a rigid bracer);
- the stub under the bracer: `sleeve_tuck.py` (frac 0.75, gap 3 mm; new env `TUCK_DEEP`/`TUCK_BLEND`: the stub takes the rigid
  bracer's weights from 2.5 cm past the joint over 3 cm, so hand skin by the rim lags like skin instead of crossing the rim);
- the toothed rim: `cuff_trim.py` (PeasantDM1's; the selection now also takes long reduced faces that reach past the cut) cuts a
  clean ring 1.9 cm before the hand joint, before the deepest notch;
- skin wedges painted on the bracer's upper rim: `bracer_paint_fix.py` (PeasantM7's `sleeve_paint_fix.py` with bracer triangles
  found by their own grey texels, so the bare forearm keeps its skin; 434 texels).
Gate `sleeve_poke_gate.py`: **0 mm, 0 frames in all 14 clips, both sides** (was up to 23.2 mm). `review/wrists_L.png`,
`review/wrists_R.png` (bind, Talk, Applause, Death: side, other side, back, below).

## Arms: MM9 gestures on a bigger body

- Fidget L, Talk L: `hand_rest.py` (2.3 / 5.0 cm needs, cleared).
- **Talk R**: the hanging hand sank 6 cm into the bulkier thigh/vest; a 9.4 cm hand-rest push failed the jitter gate with every
  filter tried (1.8-2.3 deg/f over MM9). `clap_spread.py` instead adds one constant, eased 9 deg abduction about the forward axis
  (world space through the parent frame): 0 cm, 0 jitter.
- **Applause**: MM9's seated clap brought our thicker hands and bracers 2.2 cm into each other; `arm_clear.py` cleared it but
  jittered 5.8 deg/f; `clap_spread.py` 6 deg horizontal abduction: hands 0.9 / 0.6 cm (palms meet), forearms 0, no jitter.
- Accessories: belt, brooches, medallion and necklace pieces copy the weights of the surface under them (`accessory_weights.py`,
  belt studs from the belt); Meshy's six 1-4 triangle belt studs are dropped (`drop_micro_parts.py`; the belt paint has studs).

## Checks (final build, `review/gates/`)

| Gate | Result |
|---|---|
| Arm and hand gate (`arm_hand_gate.py --outer-only`, every clip, 48 fps) | hands 0 frames over 1 cm in every clip (Applause max 0.9 / 0.6 cm, palms meeting); forearms 0 in every clip; finger stretch p99 <= 1.55, max 3.48 (Fidget L); wrist max 119 deg (Death/Dead, MM9's limp hand); 19 joints per hand |
| Jitter (`jitter_gate.py` vs MM9's untouched clips) | **0 fails** |
| Sleeve/bracer poke (`sleeve_poke_gate.py`) | **0 mm in all 14 clips**, both sides |
| Floor (`floor_audit.py --world mm9 --match 'MM9 249 *'`) | ok: stand 0, walk -0.1..+1.8, living -0.1, dead 0 world units |
| Winding | 0 inverted closed parts |
| Bones (`bone_length_audit.py`) | 12 checked, 0 stretching |
| Detached (`detached_parts_audit.py`) | **0** detached in any pose (26 components; was 8: studs, medallion, necklace) |
| Flat shading | 0.00 on both materials |
| Texture quality | body atlas **60.7 %**, density 1351/1395/1442 (spread 1.07), fragments 0.3 %, stretch p90 1.12; head set 38.8 % of the 2K image (head square + hand squares), spread 1.36, fragments 1.3 %, stretch 1.17 |
| Viewer (`run_creature_review.py check`) | 14 clip switches, 0 failed, 0 console errors (revision r2-20261102) |
| Regression `--world mm9 --headless-run-regression-suite actors` | **passed 192, failed 1** (the known `out05_event_clearance_completes_from_monster_killed_hook` "could not load gameplay data"); `mm9_actor_models_build_every_binding` **PASS** (647 descriptors on 185 models and 185 on 78, 0 failed), `review/gates/regression_actors.log`. After the final texture-only reinstall (bracer rim paint, sha256 3e303710a1f4...) the binding case again **PASS** (186 descriptors on 79 models), `review/gates/regression_binding_final.log` |

Viewer: `http://127.0.0.1:8912/level_generation/creatures/mm9_sven_claude/review/viewer/index.html` (one model `sven`).
Sheets read: `review/sheet_mm9_vs_ours.png`, `review/sheet_face4.png` (MM9 vs ours: front, 3/4, side, party view, 3/4 above),
`review/head_v1.png` (before) and `review/head_v2.png` (after the repaint), `review/sheet_neck_fringe.png`, `review/wrists_L.png`,
`review/wrists_R.png`, `review/strips_1.png` + `review/strips_2.png` (every clip at 15/50/85 %, 3/4 and front),
`review/applause_v1.png`, `review/sheet_viewer.png` (viewer shots), `review/xray_v1.png`, `review/head_split.png`,
`review/graft_all.png`, `references_face/in_face.png` vs `out_face_warped.png`.

## Binding plan (map placement)

The rebuilt maps place Sven's DAT objects with the legacy stand-in (520, Dwarf A) through `transcode_mm9_dat_to_odm.py`, so
descriptor 9249 does not show in game yet. Per the brief this switch is the orchestrator's, once for every row after the batch:
`SvenSvenssen0` (Afterworld, Arslegard) and `SvenArena` (The Arena) should place 9249. The Thronheim `Sven`/`SvenProp` objects are
props on SVEN_ARG.abc (with its chair); placing them as 9249 playing Sit/Agree/Applause needs a chair decoration (ChairPlain)
under him. No transcoder or map change here.

## Deviations and open points

- **No chair** in the model (SVEN_ARG's chair is a separate prop concern, above).
- **Applause and Talk R** carry small constant abductions over MM9's motion (6 and 9 deg).
- **Bracers** are 1.9 cm shorter at the wrist than Meshy modelled them (clean rim before the deepest tooth); the white rim band
  at the wrist end went with the cut, so that end shows engraved steel without the white edge.
- The jaw-side beard paint has a faint cell pattern in close-ups; a faint horizontal line crosses the forehead at the top of the
  repaint window; hands read slightly darker than the forearm under strong light (same albedo, flat normal, rougher).
- MM9's broad grin (parted lips) is a closed smile here, by design.
- Not looked at in game (no map spawns 9249 yet); LOD1-3 and shadow meshes not looked at; motion judged on strips and gates, not
  watched at speed; sounds (Clap model keys) not wired; Android cook not checked.

User artistic acceptance: not recorded.


**See-through linings added post-install on 2026-11-05 by `level_generation/creatures/mm9_sven_lining_claude/`** (brief `devdocs/mm9_rework/overnight/LINING_BRIEF_20261105.md`; LOD0 8,405 -> 9,860, faces appended to the installed mesh). A rebuild from this project must re-run the lining pass (`level_generation/creatures/mm9_sven_lining_claude/scripts/build.sh`). Rollback source: `level_generation/creatures/mm9_sven_lining_claude/before/`.
