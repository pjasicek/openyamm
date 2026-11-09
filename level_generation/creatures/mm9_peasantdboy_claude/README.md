# MM9 dwarf boy (PeasantDboy1) — 3D actor, 2026-11-02

Overnight batch (`devdocs/mm9_rework/overnight/TOWNSFOLK_BRIEF.md`, `VARIANTS_BRIEF.md`): MM9 `MONSTERS.txt` rows naming
`PeasantDboy1.ABC`: **67 Commoner Child** "Peasant Dwarf Child A" (skin DWARFBOY1) and **68 Townsfolk Child** "Peasant Dwarf
Child B" (skin DWARFBOY2), both NPCbase.scr, BaseName PeasantBoy, Scale 1. Two skins = two tiers of one new body. Route: the
approved MM9 humanoid route (MM9 skeleton and MM9 clips, Meshy Smart Topology + 4K retextures on our UVs, MPFB five-finger
hands, separate head set per boy). Progress, hashes and Meshy receipts: `creature_3d_progress.json`.

## Why a new body (mesh comparison)
`mm9_meshcmp.py peasantdboy1:peasantboy1,peasantdm1,peasantchildboy`: PEASANTDBOY1 has its own **38-joint** skeleton (the
human boy / PEASANTCHILDBOY have 30, the dwarf men 41); after the rigid shift the meshes differ 2-4 cm in the head and 4-8 cm
in torso, arms and legs from both families. PEASANTDBOY1.abc lists **no child models** and carries its own clips (stand,
aware, fidget1/2, sitdown, sit-wait, sitfidget1/2, walk, run, Hattack1, wince1, die1), so it uses neither the
PEASANTCHILDBOY nor the dwarf library: its own skeleton and clips. The figure is 1.01 m (MM9's own height; the human boy
is 1.36 m).

| Item | Value |
|---|---|
| Runtime GLB | `assets_source/worlds/mm9/models/mm9_peasantdboy.glb` (`tools/install_model.py --world mm9 --name mm9_peasantdboy.glb` from `export/mm9_pdboy.glb`, sha256 ab3ec78feaac...), variants `pdboy_a` (67), `pdboy_b` (68) |
| Binding | `assets_dev/worlds/mm9/models/actors.yml` block `mm9_peasantdboy_claude` (`scripts/bind_actors.py` under the flock): `MM9 67 Commoner Child`, `MM9 68 Townsfolk Child`; scale 100, `yaw_offset -1.570796327`, stride walk 0.37 / run 0.78 (`stride.py`), look Neck/Head, impact 0.242 s (Hattack1 `Rattack`) |
| Rows | `tools/mm9_import_discovery/mm9_npc_actor_rows.tsv`: 67 -> 313, 68 -> 322 (the stand-ins of `mm9_npc_legacy_replacements.tsv`); tables regenerated, descriptors 9067 / 9068; `mm9_monster_bodies.py --write-overrides`: **Height 97, Radius 26** (MM9's rule on PEASANTDBOY1's upright static_model box (10, 19, 10) LT; our figure is 1.01 m: sane, no exception needed) |
| Triangles LOD0/1/2/3 | 12,983 / 6,490 / 2,336 / 776 (Smart Topology 15,794 -> 9,349 reduced + MPFB hands 2 x 700; linings, hair and sleeve twins ~3,500, one texel each, left out of the shadow meshes) |
| Skeleton | PEASANTDBOY1.abc's 38 joints (Bip01 biped, pelvis root, Spine..Spine3, two 3-bone finger chains per hand), names and rest rotations unchanged, joints translated onto our body (`fit_rig.py`, `fit_config.json`), + 15 MPFB finger bones per side driven from MM9's finger curl (`finger_alias`, 3-bone chains: Finger1/11/12 -> each finger's 1/2/3); mirrored to MM9's true handedness (`mirror_glb.py`) |
| Clips (30 fps, `source/mm9/pdboy_a.glb`) | Standing stand 1.6, Walking walk 0.9, Running run 0.4, Fidget fidget1 3.5, Fidget2 fidget2 2.0, AttackMelee Hattack1 1.1, Hit wince1 1.0, Death die1 1.0, Dead |
| Textures | body 2K colour + 1K normal/ORM, region mask (R tunic, G embroidered bands, B trousers, A belt) + ramps per tier; head + hands set 2K colour + 1K normal/ORM, tier b has its own head colour (`tier_head.py`: a different boy); specular 0, metallic 0 |
| Meshy credits | **35 / 50**: Smart Topology 5, body 4K retexture 10, head a 4K 10, head b 4K 10 (backup 2640 before the first job -> 2580 after the fourth; other agents spend from it too) |

## Clips MM9 plays on him
DAT objects (`dat_objects.py Child`): two `CommonerChildDwarfChildA` in the rebuilt maps, both `scripts\YanmirChild.scr` (FollowPlayer:
walk and run, RunToPos); rows 67/68 are NPCbase.scr: Converse finds no conv clip on this model and BaseRun's `GetAnimNbr Cower` is -1,
so neither plays. Carried: the roles plus fidget2 (`script_clips` stand, walk, run, fidget1, fidget2). Not carried: aware, sitdown,
sit-wait, sitfidget1/2 (no script plays them). The pelvis keys sit at the bind height (no `source_offset`).

## Route (scripts/, repo root unless noted)
0. Sources `convert_abc_model.py --scale 0.0256` (both skins) -> `source/mm9/pdboy_{a,b}.glb`; `ref_renders.py` -> `review/mm9/`;
   `input_sheets.py` -> `references_hd/mm9_views_{a,b}.png`, `mm9_head_views_{a,b}.png`, `mm9_skin_x4_{a,b}.png`.
1. Codex (via `codex_slot.sh`): `codex_masters.sh 1|2` (brief `references_hd/CODEX_BRIEF.md`, halo removed by `clean_alpha.py 200`,
   raw returns `references_hd/raw/selected_*`), `codex_head.sh a|b` (`references_head/`, `references_head_b/`: b is a different
   boy, strawberry blond, on a's silhouette). Sheets `review/masters_check.png`, `review/heads_ab_check.png`.
2. Meshy Smart Topology 15k from `00_three_quarter.png`; `sym_meshy.py ... pos` (exact symmetry); `fit_rig.py` (X-ray
   `review/xray_v1.png`); `reduce_uv.py`; `sym_rigged.py`; `graft_hands.py graft_dboy.json` (MPFB age 0.2, weight 0.65, hand 0.14 m);
   `head_split.py head_dboy.json` (first pass lists parts) -> `eye_fill.py 9,10` -> `drop_parts.py 3,5,9,10,13,14,19,20` (eyeball
   cups, iris discs, fragments) -> `cuff_trim.py -0.03` -> `head_split.py` -> `triangulate.py` = `work/eyes_v1t.blend`.
3. UVs (never re-run: the paid paints are on these layouts): `texpass_uv.py` (body 57.2 %) and **`relayout_head_dboy.py`** (the boy's
   face-as-one-chart head layout run BEFORE the head retexture, so no paint transfer; also writes the head upload) =
   `work/texpass_head.blend`.
4. Paint (project folder): `bake_ao_texpass.py`, `compose_texpass.py pdboy_tp`, gentle grade (`grade_basecolor.py --fine 1.0
   --local 0.3 --ao-strength 0.5 --contrast 1.06 --saturation 1.15`), `bake_hands.py` (young caucasian male skin),
   `compose_headhand.py pdboy_tp|pdboyb_tp meshy/head_{a,b}_tp ... --ref-head --ref-lum-min 150 --hand-gain 1.12` (backups
   `work/<p>_head_basecolor_composed.png`), then **`scripts/head_paint_dboy.sh`**: `face_fix_dboy.py` (closed mouth: the mouth
   pocket and b's pale gap between the lip bands become lip/lip shadow, lips moved 20 % (a) / 40 % (b) toward the cheek hue: no
   lipstick) -> `hand_clean.py` -> `wrist_band_dboy.py` (MM9's dark leather wrist band over the graft seam, body + hand texels).
   Tiers `mm9_skin_labels_dboy.py`, `tiers_dboy.py` (args in `scripts/tiers_dboy.args`).
5. Geometry after the paint (positions/faces/weights only): `midline_weld.py` (the mirror midline's unwelded pairs shaded as dark
   X pinches on the forehead, crown and chin) -> `mouth_relax.py` (CZ 0.327 RX 0.024 RZ 0.014, 10 iters: the pursed lips) =
   `work/geo_v2.blend` -> **`scripts/linings_dboy.sh`** (neck cap; `hair_lining.py` inner twins of the bob's three hair shells;
   rim linings of the collar, trouser tops and the forearm end at the wrist (leather texel); `sleeve_twin.py` shoulder/sleeve
   twins; `mouth_fill.py` closes the mouth pocket) = **`work/linings_v3.blend`, the build default**.
6. Runtime `TOKEN=<lease> scripts/build_runtime_pdboy.sh [--install]` (memory-capped): export, `clips_mm9.py roles_dboy.json`,
   `arm_clear.py` (upper arm, then a forearm pass) + `arm_bump.py` per `arm_bumps_pdboy.txt` (one faded rotation per arm: Fidget's
   hands on the hips and against the flared tunic skirt, Running's right hand), `hand_rest.py` per `hand_rest_pdboy.txt` (Fidget2's
   hand at the face), prepare, LODs, shadow fix, region variants, tier head b, extras, floor fix (`floor_ops.txt`), mirror,
   winding. Viewer `scripts/viewer.sh <rev>`; binding `flock -x level_generation/creatures/claude_shared/locks/mm9_actors_yml.lock
   bash -c 'python3 level_generation/creatures/mm9_peasantdboy_claude/scripts/bind_actors.py && python3
   tools/mm9_import_discovery/generate_mm9_monster_tables.py'`, then `mm9_monster_bodies.py --write-overrides` and the generator again.

## Checks (final build, `review/gates/`)
| Gate | Result |
|---|---|
| Arm and hand (`arm_hand_gate.py --outer-only`, 9 clips) | **0 frames over 1 cm, both hands, every clip** (before: Fidget 6.0 cm both hands, 134/141 frames; Fidget2 L 2.8 cm; Running R 6.0 cm 2 frames) |
| Jitter (`jitter_gate.py` vs MM9's untouched clips) | **0 fails** (per-key arm_clear corrections failed at 8-12 mm/f2 shoulder skin; arm_bump's single faded rotations, split over shoulder and elbow, pass) |
| See-through (`see_through_gate.py`, all clips every 2nd frame + Running 15; worst px at 3 mm px) | r1 (no linings) -> final: sleeve L 162 -> 23, sleeve R 161 -> 15, head 38 -> 5, collar 44 -> 0, torso 68 -> 50 (one Death fall frame from 135 deg / 20 deg down at the belt crease; Dead and standing clips <= 5), boots 0. **Not 0**: residual specks at the elbow folds and the falling corpse's belt |
| Sleeve poke (`sleeve_poke_gate.py`) | reads 18 mm with **0 rim vertices**: the gate finds no sleeve rim (bare forearms, MM9's design); not applicable, the hand close-ups were judged instead |
| Floor (`floor_audit.py --world mm9`) | 67 / 68: stand 0.0, walk -0.1..+1.7, living -1.4, dead -0.0: ok |
| Detached / winding / bones / flat | 0 detached; 0 inverted; 12 checked, 0 stretching; flat 0.00 on both materials |
| Texture quality | body atlas **57.2 %**, spread 1.06 before the one-texel linings (reported spread is infinite with them, as PeasantDM2/boy), fragments 1.6 %, stretch p90 1.09; head set **40.9 %** (hands half density by design; below the 55 % body target, as the boy's 43.8 %), fragments 2.2 %, stretch 1.20 |
| LOD0 | 12,983 triangles (< 15k) |
| Viewer (`run_creature_review.py check`) | 18 switches, 0 failed, 0 console errors |
| Regression `mm9_actor_models_build_every_binding` | **PASS** (240 descriptors on 105 models, 0 failed; `review/gates/regression_binding.log`) |

## Sheets read
`review/sheet_mm9_vs_ours.png` (MM9 front/3-4/back vs ours, both tiers), `review/sheet_faces_r8a.png`, `review/sheet_faces_r8b.png`
(per tier: MM9 head views; front close-up, 3/4, true profile, low 3/4 from below, party view, both ears, 128 px simulation; body
front/3-4/back; EEVEE with a viewer-like key + fill), `review/faces/r8_mouth.png` (mouths front + low, both tiers),
`review/faces/hands_r10.png` (wrists and hands, tier b), `review/faces/hands_r9.png` (tier a), `review/sheet_clips_final.png`,
`review/tiers_v1.png`, `review/xray_v1.png`, `review/masters_check.png`, `review/heads_ab_check.png`,
`review/gates/see_through_r1..r4,final/` worst-case images.

## Deviations and open points
- **Pattern differences** (ramps recolour one paint): b's tunic is MM9's plain dark brown but keeps our weave and the bands' scroll as
  faint relief; b keeps a's cream shirt band at the waist (MM9 b shows the tunic and a braided belt there) and the checked trousers
  (dark brown). Faces: two head paints (two different boys).
- **Mouths**: closed in front and 3/4; from a low camera a thin lip-shadow line and a few pale specks remain at the lip line (a).
- **Wrists**: MM9's thin wrist band is a 4 cm painted leather band over the graft seam; small skin wedges of Meshy's forearm show
  between the elbow sleeve and the band from some angles.
- **Fidget**: the hands rest on the hips and hang beside the skirt as MM9's, but the arms swing out up to ~26 deg (our tunic flares
  wider than MM9's) - check it at speed in the viewer.
- Hair over the ears as MM9 (no ear close-up applies: the bob covers them; `*_ear_l/r` in the face sheets show the hair sides).
- Not looked at in game (placement still uses the legacy stand-ins 313 / 322: the orchestrator's switch); LOD1-3 and shadow meshes
  not looked at; motion judged on strips and gates, not watched at speed; sounds; Android cook.


**LOD0 reduced post-install on 2026-11-04 by `level_generation/creatures/mm9_peasantdboy_reduce_claude/`** (ledger: `level_generation/creatures/REDUCTION_LEDGER.md`, "MM9 reduction"). A rebuild from this project must re-run that reduction, or it silently restores the heavier mesh. Rollback source: `level_generation/creatures/mm9_peasantdboy_reduce_claude/before/`.
