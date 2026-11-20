# MM9 PeasantM4, the old prisoner (mm9_peasantm4) — 3D actor variant, 2026-11-02

MM9 `PEASANTM4.abc` + `PEASANTM4A.dtx`, the only `MONSTERS.txt` row naming it: **49 Prisoner** "Peasant Human1 MaleD A"
(NPCbase.scr, PeasantMale library). DAT class `PrisonerHumanMaleA`, 7 placements (Drangheim, Drangheim Prison, Sturmford City:
NPC90.scr = Ivsar, DrangheimPrisoner.scr). Skin `PEASANTM4B.dtx` exists but no row uses it: not built. Batch:
`devdocs/mm9_rework/overnight/VARIANTS_BRIEF.md` (shared-mesh variants). Owner m45-agent. Receipts: `creature_3d_progress.json`.

**Route: variant on PeasantM8 (= Forad's approved body), torso reshaped.** `mm9_meshcmp.py peasantm4:peasantm8,foraddarre,...`
(re-run): M4 has PeasantM8's and Forad's exact skeleton binds (bind diff 0.00 cm; PeasantM1/M2/M3/Markel differ by 18-19 cm).
vs PM8 head p90 1.0, arms 1.6, legs 2.4, torso 4.1 cm. Side by side (`references_hd/mm9_m4_vs_forad_pm8_body.png`, `_head.png`,
`review/sil_mm9_pm8_red_mm9_m4_green.png`): the same man's mesh with a **fuller belly, waist, hips and upper thighs** (3-5 cm),
the same bald head, arms and boots. A reshape matches it, so no new body: PeasantM8's master (`../mm9_peasantm8_claude/v2/work/
master_v2.blend`, only read; copied here as `v2/work/master_v2.blend`), its rig, weights and clip choice, new body and head paint.

| Item | Value |
|---|---|
| Runtime GLB | `assets_source/worlds/mm9/models/mm9_peasantm4.glb` (`tools/install_model.py --world mm9 --name mm9_peasantm4.glb`), = `v2/export/mm9_pm4.glb` = `work/r2_final.glb` (sha256 647521a7d859...) |
| Binding | `actors.yml` `MM9 49 Prisoner` (`scripts/binding_pm4.yml`, `scripts/bind_under_lock_pm4.sh` under the flock): PeasantM8's values (scale 100, yaw -1.5708, stride 1.05 / 3.8, look Neck/Head, impact 0.5 s); script clips `talk`/`conv1` Talk, `cower` Cower, `fidget3` Fidget3, `stand` Standing |
| Descriptor | row 49 in `tools/mm9_import_discovery/mm9_npc_actor_rows.tsv` (fallback 366 = its `mm9_npc_legacy_replacements.tsv` stand-in), tables regenerated (230 rows) |
| Triangles LOD0/1/2/3 | 7,168 / 3,582 / 1,288 / 427 (= PeasantM8) |
| Clips (30 fps, `source/mm9_lib/pmale.glb`, soft offset line) | Standing stand1, Walking walk3, Running run, Fidget fidget1, Talk conv1 (Forad's hand rest), AttackMelee hattack1, Hit wince1, Death die1, Dead, Cower cower (BaseRun.inc), **Fidget3 fidget3** (DrangheimPrisoner.scr `PlayAnim Fidget3`). PM8's Conv2/Conv3 (Narrator.scr) are not on these objects: left out |
| Textures | body 2K colour + 1K normal/ORM on Forad's texture-pass UVs (repainted); head + hands set 2K colour + 1K normal/ORM on PM8's head UVs (repainted; Forad's hand texels, toned) |
| Meshy credits | **20 / 25**: head 4K retexture 10 (backup 2730 before), body 4K retexture 10 (backup 2685 before); no retries |
| Viewer | http://127.0.0.1:8912/level_generation/creatures/mm9_peasantm4_claude/review/viewer/ revision `r3-20261102` |

## Route (project folder; nothing written into mm9_peasantm8_claude or mm9_forad_claude)
0. Sources `scripts/convert_sources.sh` (both skins); MM9 renders `scripts/render_mm9_set.sh` + `scripts/side_sheet.py`;
   silhouettes `scripts/sil_overlay.py` (ABC) and `scripts/sil_npz.py` (dumps from `scripts/dumpco.py` / `dumpglb.py`).
1. **Geometry** (positions only; topology, UVs, weights unchanged), on PM8's `master_v2.blend`:
   `scripts/reshape_m4.py ... work/mm9_dumps/pm8mm9.npz work/mm9_dumps/m4.npz work/reshape_v3.json 1.5` = a SPATIAL offset field:
   the MM9 PM8->M4 surface offset (along PM8's normal, smoothed 5 cm) as vectors, Gaussian-averaged (3 cm) at every vertex
   position so stacked layers (vest hem over waistband) move together, height window knee..lower chest, head/arms/calves pinned,
   10 smoothing passes, gain 1.5 -> `work/reshape_v3.blend` (max 4.7 cm); then `scripts/belt_smooth.py ... 0.18 0.38 15`
   (PM8's belt/waistband lip smoothed away: M4 wears no belt; max 5.9 cm) -> `work/reshape_v4.blend`. A per-normal push
   (v1/v2) opened a bucket rim at the waistband (`review/clay_torso_pm8_vs_reshape_v2.png`). Self-intersections 133 = PM8's 133
   (`scripts/self_overlap.py`). Result vs MM9 M4: `review/sil_reshape_v4_red_mm9_m4_green.png`, clay `review/clay_torso_r3_vs_r4.png`.
   A sculpted moustache volume (`scripts/moustache_sculpt.py`) read as a pouting upper lip in clay
   (`review/clay/face_moustache_v1.png`): dropped, paint only.
2. **Uploads**: body = PM8's upload with the same moves (`scripts/move_upload.py`, UVs untouched) -> `v2/texturing/pm4_body_upload.glb`;
   head = PM8's head upload (head unchanged) -> `pm4_head_upload.glb`.
3. **HD masters** (Codex via `codex_slot.sh`): `SHAPE=mm9_peasantm8_claude scripts/codex_masters.sh <P> 1|2` (brief
   `references_hd/CODEX_BRIEF.md`: design from MM9, pose from PM8's masters, the fuller belly), head turnaround `scripts/codex_head.sh`
   (`references_head/CODEX_BRIEF.md`: calm kindly old man, white walrus moustache, bald top, silver brows). `scripts/clean_alpha.py`.
   Read: `references_hd/selected_views_review.png`, `review/body_clean_check.png`, `references_head/selected_views_review.png`.
4. **Paint**: `v2/requests/retexture_head_pm4.json`, `retexture_body_pm4.json` (4K, meshy-7, our UVs). AO `v2/scripts/bake_ao_texpass.py
   work/reshape_v4.blend`; `compose_texpass.py pm4 ...`; gentle grade; `compose_head_texpass.py forad_tp pm4 meshy/head_retexture_pm4`;
   `scripts/hand_tone.py pm4 1.0 work/texpos_head.npz -0.017` (hands to the ruddy face); **`scripts/trim_calm.py work/dump_m4.npz
   0.30 0.3 0.6`** (new: Meshy painted MM9's woven chevron braid on the neckline/shoulder pieces as a stark leopard print; texels on
   the upper torso holding near-black next to near-white are calmed to a woven brown band; `review/trim_calm_atlas.png`,
   `review/r2/upper.png`); `scripts/collar_match.py pm4 work/dump_m4.npz work/texpos_head.npz` (head-set collar to the body tone).
5. `scripts/lining_texel.py work/reshape_v4.blend work/master_m4.blend textures/pm4_basecolor_graded.png` (lining faces -> the cream
   cuff texel). **`work/master_m4.blend` is the master.**
6. **Runtime**: `PYGLTF_PYTHON=../claude_shared/gltf_venv/bin/python TOKEN=<lease> HEADTEX=pm4 BODYTEX=pm4 BLEND=work/master_m4.blend
   v2/scripts/build_runtime_pm4.sh pm4 PeasantM4 v2/scripts/roles_pm4.json [--install]` (PM8's chain; `v2/scripts/head_pm4.json` =
   PM8's export fix: the 5-edge hole in the back of the vest is filled at export, it was the only torso see-through;
   `v2/scripts/hand_rest_pm4.txt` = Forad's Talk line; new **`v2/scripts/spread_pm4.txt`**: Fidget3's hanging hands sank 6 cm into the
   fuller hips (142/205 frames), one eased 14 deg abduction about the forward axis (`clap_spread.py`, Markel/Sven); a hand_rest push
   cleared them but jittered 1.5-2 deg/f over MM9). Floor ops `scripts/floor_ops_pm4.txt`. Viewer `v2/scripts/make_viewer_v2.py`.

## Checks (installed GLB = `work/r2_final.glb`)

| Gate | Result |
|---|---|
| Arm and hand (`arm_hand_gate.py --outer-only --exact`, `v2/review/gates_r2/arm.txt`) | = PM8's accepted: hands 0 except **Talk L 3.4 cm, 38 f** (MM9's hand on the heart; PM8 3.3/40); forearms Fidget R 2.3 cm (PM8 1.2: the wider hip), finger stretch max 3.2; Fidget3 0 (was 6.0 cm); 19 chains per hand |
| Jitter (`jitter_gate.py` vs MM9's untouched clips) | 5 fails = PM8's/Forad's accepted 5 (Walking/Death shoulder-skin p95, Talk L upper arm); Fidget3 passes |
| Sleeve poke (`sleeve_poke_gate.py`) | = PM8's: rest 0; hard wrist bends meet Forad's bracer (Hit R 24.3, Talk L 16.3, Death L 10.8 mm ...) |
| See-through (`scripts/see_through_gate.py`, every clip, step 3, 8 az x 0/20 deg; `v2/review/see_through_r2/`) | head 0, torso 0, collar 0, boots 0, trousers 0; sleeves R 12 px Running (4 frames), L 4 px Talk (3 frames): one-pixel cuff-rim slivers (read `report_sleeveR_Running_6_az315_el20.png`), PM8 had R 22 / L 4 |
| Rigid head | PM8's (chin/jaw Head 1.0, head unmoved) |
| Floor (`floor_audit.py --world mm9 --match 'MM9 49 *'`) | ok: stand 0, walk 0, living 0, dead 0 |
| Detached / winding / flat / bones | 0 detached; 0 inverted; flat 0.1 % body, 0.0 % head; 0 stretching |
| `texture_quality.py` | body atlas 53.3 % (= PM8, Forad's layout; under 55 % as accepted for Forad), density 1404/1541/1605 spread 1.14, fragments 0.0 %, stretch p90 1.42 (reshape; PM8 1.09); head set 44.0 %, fragments 2.7 %, stretch 1.24 |
| Viewer `run_creature_review.py check` | 11 switches, 0 failed |
| Regression `mm9_actor_models_build_every_binding` (`--world mm9`) | **PASS**, 230 descriptors on 101 models (`review/regression_binding.log`) |

Sheets read: `review/sheet_mm9_vs_ours_r1.png` (MM9 vs ours, five views), `review/r2/upper.png` (upper body, flat), `review/sheet_face_viewer_r3.png`
(**viewer lighting**: front close-up, 3/4, both true profiles, low 3/4 from below, party view and a 128 px party-distance head, Standing
and Talk, MM9's head), `review/head/r1.png`/`r3.png` (EEVEE: eyes, mouth, both neck sides), `review/sheet_ears_r2.png` (both ears,
tight, 3/4 backs, from below, jaw-neck lines).

## Source models untouched
`mm9_peasantm8_claude/` and `mm9_forad_claude/` were only read (copies made here). sha256 of all 1,461 files of both projects plus
`assets_source` and `assets_dev` `mm9_peasantm8.glb` and `mm9_forad.glb`: `review/source_sha256_before.txt` = `review/source_sha256_after.txt`
(identical). Their `actors.yml` blocks (`MM9 55 Shopkeeper`, `MM9 252 Forad Darre`) were not edited (the M4 block was appended).

## Open points / not checked
- The neckline/shoulder braid is a calmed brown woven band, not MM9's crisp cream chevrons (Meshy's paint was a leopard print).
- Brows are silver-white like MM9's (old man); at the front close-up stand1's bowed head makes the eyes read narrowed.
- Sleeve poke and cuff-rim slivers are PeasantM8's (Forad's bracer reaches past the wrist joint).
- Skin PEASANTM4B (no MONSTERS.txt row) not built. No in-game run (row 49 is still placed as legacy 366 by the transcoder: the
  orchestrator's switch); LOD1-3 and shadow meshes not looked at; clips watched only as stills/gates, not at speed.

User artistic acceptance: not recorded.


**LOD0 reduced post-install on 2026-11-05 by `level_generation/creatures/mm9_peasantm4_reduce_claude/`** (ledger: `level_generation/creatures/REDUCTION_LEDGER.md`, "MM9 reduction"). A rebuild from this project must re-run that reduction, or it silently restores the heavier mesh. Rollback source: `level_generation/creatures/mm9_peasantm4_reduce_claude/before/`.
