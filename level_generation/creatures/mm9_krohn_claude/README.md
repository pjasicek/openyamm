# MM9 Krohn (mm9_krohn) — 3D actor, 2026-11-04

Finishing brief job 3 (`devdocs/mm9_rework/overnight/FINISH_BRIEF_20261104.md`), rules from `RUN2_COMMON.md`, `TOWNSFOLK_BRIEF.md`,
`VARIANTS_BRIEF.md`. MM9 `MONSTERS.txt` row **255 "Krohn"** (`Krohn.abc`, skins `Krohn.dtx` + `KrohnSword.dtx` + `KrohnSpear.dtx`,
NPCbase.scr, BaseName PeasantMale, Scale 1, IsMonster 0, Hostility 1); the only row naming the model, one skin, no tiers. Built on the
approved MM9 humanoid route (MM9 skeleton and MM9 clips, Meshy Smart Topology + 4K retextures on our UVs, MPFB five-finger hands, a
separate head set), with the glaive and the scabbarded sword built from MM9's own weapon pieces. Receipts, hashes:
`creature_3d_progress.json`. Status: `devdocs/mm9_rework/overnight/status/townsfolk_krohn.md`.

| Item | Value |
|---|---|
| Runtime GLB | `assets_source/worlds/mm9/models/mm9_krohn.glb` (`tools/install_model.py --world mm9 --name mm9_krohn.glb` from `export/mm9_kr.glb`) |
| Binding | `assets_dev/worlds/mm9/models/actors.yml` block `mm9_krohn_claude` (`scripts/bind_actors.py` under the flock): `MM9 255 Krohn`, scale 100, `yaw_offset -1.570796327`, stride walk 1.55 (`stride.py`: 1.50-1.61 m) / run 3.6 (the retargeted run is planted only 10-13 % of its cycle; PeasantMale's 2.8 x Krohn's leg ratio 1.29), look `Bip01 Neck, Bip01 Head`, impact 0.5 s (hattack1 Rattack), script clips below |
| Descriptor | row 255 appended to `tools/mm9_import_discovery/mm9_npc_actor_rows.tsv` (fallback legacy 565 "Armored Death Knight", the stand-in of `mm9_npc_legacy_replacements.tsv`); `mm9_monster_bodies.py --write-overrides` added 9255 (MM9's rule: krsetup dims (20, 54, 20), Scale 1 -> height 276, radius 51); tables regenerated: 9255 `MM9 255 Krohn` |
| Size | 2.78 m (108.6 MM9 units, MM9's own model height; Krohn is a giant). The DAT objects in the Hall of the Gods place him at Scale 1.25 (3.47 m): placement scale is the orchestrator's (map switch) |
| Triangles LOD0/1/2/3 | 12,320 / 6,158 / 2,216 / 726 (body 6,645 incl. rim linings, head + hands 4,399 (hands 2 x 700), glaive 796 + sword 480) |
| Skeleton | KROHN.abc's 64 nodes: Bip01 biped (Pelvis root, Spine/Spine2/Spine3, clavicles under the Neck), three hair chains `Xhair*`, beard `Xbeard*`, cape `Zcape*`, skirt flaps `Yback*/Yfront*`, `Xspear` (right hand) and `Xsword` (Spine3); joints translated onto our mesh (`fit_rig.py`, rest rotations unchanged), + 15 MPFB finger bones per side; mirrored to MM9's true handedness at the end (`mirror_glb.py`) |
| Textures | body 2K colour + 1K normal/ORM (atlas 58.3 %, spread 1.06, fragments 0.4 %, stretch 1.12); head + hands set 2K + 1K + 1K (atlas 43.8 %: hand squares at half density by design, fragments 1.2 %, stretch 1.26); props atlas 2048 x 1024 procedural; no region mask (one skin); specular 0, metallic 0 |
| Meshy credits | **25 / 60**: Smart Topology 5, body 4K retexture 10, head 4K retexture 10 (backup 2355 before the first job; 2325 -> 2315 around the retextures, other agents spend from the same account), no retries |

## Why a new body
`claude_shared/mm9_meshcmp.py krohn:<every built humanoid>`: raw p90 25-125 cm (Krohn is 1.55x a peasant); `scripts/meshcmp_scaled.py`
(Krohn scaled to each body's height, centred): p90 8-23 cm in every region against Bjarni, PeasantHOM1, Hanndl, Markel, Sven, Guard, Kira,
Sigmund, Tryggva, ClanSoldier, DookMilitia, Highwayman, Monk, Trellborg. Different skeleton (64 nodes) and costume: a new body.

## What MM9 does with him (DAT objects and scripts)
`mm9_markel_claude/scripts/dat_objects.py krohn`: Hall of the Gods only.
- `Krohn0` (NPC335.scr: the Stop Njam quest reward on Rude; `Loopanim stand` on Start);
- `Krohn` (WG_NPC335.scr, the win-game cutscene: `Loopanim stand`, `PlayAnim Krohn01..Krohn05`, `SC7_22_Krohn`; `HidePiece spear`
  only when hidden);
- `Krohnstat` (Prop, PropAnim.scr `statue`, skins Krohnsculpt/KrohnSpearsculpt/KROHNSwordsculpt, Scale 7): a stone statue of him.
KROHN.abc's clips: krsetup, stand, fidget1-4, walk, stand1, statue, Krohn01-06, Krohn16(novoice), Krohnshot25, SC7_22_Krohn. No run,
attack, hit or death: as Sigmund, **Running, AttackMelee, Hit and Death are PeasantMale library clips (run, hattack1, wince1, die1)
retargeted** by world-rotation copy (`scripts/retarget_mm9.py`, `retarget_pmale.json`: Pelvis <- Spine, Spine <- Spine1, the left thumb
on Finger01/02; root translation x 1.29 = Krohn's thigh+shin over PeasantMale's). No Talk (no conv clip), no Cower.
The glaive is rigid in the right hand in every clip (Xspear keys only roll it about the shaft in walk, or slide it 0.34 m along the
shaft in stand1/fidget3/fidget4/statue): one fist fits every clip.

## Clips (30 fps; `scripts/roles_krohn.json`)
Own: Standing `stand`, Walking `walk`, Fidget `fidget1`, Statue `statue` (held 1 s), Krohn01-05, SC7_22_Krohn (each eased from/to
Standing; LithTech animation origin (0, -54, 0) units of the cutscene clips subtracted from the pelvis: per-role `source_offset`, new in
`clips_mm9.py`). Retargeted: Running, AttackMelee, Hit, Death; Dead = Death's last pose. Hair and cape chains damped toward Standing in
the retargeted clips. `script_clips`: stand, walk, fidget1, statue, krohn01..05, sc7_22_krohn.

## Route (`scripts/`, repo root unless noted)
0. `convert_sources.sh` (KROHN with its three skins, and the sculpt skins); `ref_renders.py` (HIDE_OBJS=sword,spear), `input_sheets.py`.
1. Codex via `codex_slot.sh`: `codex_masters.sh 1|2` (brief `references_hd/CODEX_BRIEF.md`: calm, warm old god-king, no weapon),
   `clean_alpha.py`; head turnaround `codex_head.sh` -> `references_head/`. Sheets `review/masters_check.png`, `review/head_check.png`.
2. Meshy Smart Topology 15k (`requests/smart_topology_v1.json`). Nearly symmetric (mirror p90 <= 2.8 cm), kept unsymmetrised (the
   baldric and shoulder medallion are geometry).
3. `fit_rig.py work/... fit_config.json` (MM9 body + head pieces joined, weapons dropped; Neck interpolated: the beard sits in front of
   it; X-ray `review/xray_v1.png`) -> `reduce_uv.py` (15.2k -> 9.4k) -> `graft_hands.py graft_krohn.json` (search ranges x1.5 for a
   giant: `along_max`, `arm_radius`; `poke`/`rim_clean`) -> `loose_parts.py ... 30 0.35` (old finger-tip remnants) -> `head_split.py
   head_krohn.json` (head, hair, beard, crown; cape/medallion/baldric parts excluded; `max_abs_x`, `hair_box` new) -> `cuff_trim.py`
   (CUFF_RAD 0.13) -> `triangulate.py` = `work/tri_v1.blend`.
4. UVs (never re-run): `texpass_uv.py` (body 59.5 %), `relayout_head_k.py` (face one chart; head upload).
5. Paint: retextures 4K; `bake_ao_texpass.py` (6 cm), `SKIN_RULE=1 compose_texpass.py kr_tp ...` (skin class for the bare arms and legs,
   new), gentle grade, `bake_hands.py` (old caucasian male), `compose_headhand.py kr_tp meshy/retexture_head_tp ...`.
6. Weapons: `make_props.py` (glaive and sword from MM9's piece geometry in its PCA frame, procedural paint; faces wound by the frame's
   determinant: check_winding 0) -> `grip_solve_kr.py` (right fist: a natural fist fitted round the shaft, the shaft axis through it, a
   22 deg wrist turn (knuckle line onto the shaft) undone on Xspear so the glaive stays where MM9's keys put it; Xspear/Xspearmid
   translated) -> `add_props.py` (`SWORD_FIT=0.075 SWORD_BONE=Zcapepiv`: the scabbard laid 7.5 cm off the back surface and carried by
   the cape's centre pivot, so it rides on the cape it lies on). Rim linings first: `linings_kr.sh` (bracer ends, skirt and tabard hems:
   `rim_lining.py`, all texels region R in `textures/kr_lining_mask.png`): `grip_v1` -> `linings_v1`, then add_props -> **`work/grip_props_cape.blend`**.
7. Runtime `TOKEN=<lease> scripts/build_runtime_kr.sh [--install]`: export (props joined as material `KrohnProps`), `clips_mm9.py`,
   `arm_const.py` (`arm_const_kr.txt`: shoulder abduction L 14 / R 9 deg on the standing clips, Fidget L 18, Walking L 15; the punch,
   hit and death only at their ends, faded over 0.5 s (new `:win[:in]` syntax)), `grip_keys.py` (fist, wrist turn, Xspear inverse),
   `spear_clear.py` passes (`spear_clear_kr.txt`, pivot at the fist), `hair_follow.py` (the hanging hair follows Spine3 in the
   retargeted clips), prepare, LODs, shadow fix, extras, `floor_fix.py` (`floor_ops.txt`), `drop_lod_slivers.py` (the LOD2-shadow blade
   collapses flat), mirror, winding.
8. Binding: `flock -x level_generation/creatures/claude_shared/locks/mm9_actors_yml.lock bash -c 'python3
   level_generation/creatures/mm9_krohn_claude/scripts/bind_actors.py && python3 tools/mm9_import_discovery/mm9_monster_bodies.py
   --write-overrides && python3 tools/mm9_import_discovery/generate_mm9_monster_tables.py'`.
   Viewer: `python3 scripts/make_viewer_manifest.py <rev> "kr=Krohn=export/mm9_kr.glb"`. Gates: `scripts/gates_kr.sh` (project
   folder), `arm_hand_gate.py ... --exclude-bones Xspear,Xspearmid,Xsword,Xswordbase` (new option), `see_through_gate.py`.

## Checks (installed build, `review/gates_r4/`; earlier rounds `gates_r1..r3`)
| Gate | Result |
|---|---|
| Arm and hand (`arm_hand_gate.py --outer-only --exclude-bones Xspear,Xspearmid,Xsword,Xswordbase`, 48 fps, 15 clips) | **0 frames over 1 cm, hands and forearms, both sides, every clip** (r1 before the abduction: Standing L 6+ cm / R 4.1 cm every frame, Fidget L 6, cutscenes L 6) |
| Grip | right fist closed round the shaft in every clip (one pose: MM9 never moves the glaive across the hand); solve clearances index/pinky -11/-14 mm at the finger roots (skin into the 2.7 cm shaft), middle +1, ring -0.7 (`work/hand_poses.json`); looked at in the viewer (`review/shots/sheet_hands_r5.png`) |
| Glaive vs body (`prop_gate.py`, 24 fps) | 0 in Standing, Walking, Running, Fidget, Hit, Death, Statue, Krohn02, SC7_22_Krohn, Dead; **AttackMelee 6 cm (6 f, side hair), Krohn01 6 cm (12 f), Krohn04 6 cm (3 f), Krohn05 6 cm (55 of 484 f), Krohn03 1.0 cm (2 f)** (the butt behind the right thigh in the cutscene clips). r1: Standing 1.7 cm every frame, Fidget/Attack/cutscenes 6 cm |
| Sword vs body | 0 except **Death 3.1 cm (5 f, the hair as he falls back)** (r1: Running 4.9, Hit 5.9, Death 6.0, AttackMelee 3.8, Walking 1.8) |
| Jitter (`jitter_gate.py` vs the untouched MM9 clips) | **AttackMelee fails (L upper arm +2.4 deg/f, forearm +2.7, shoulder skin 15.8 mm/f2; R skin 7.2), Death fails (L forearm +1.4 deg/f, skin 4.0; R skin 2.5)**: the abduction faded in/out at the clip ends; every other clip passes (Walking passes with the 0.06 s floor smoothing) |
| Sleeve poke (`sleeve_poke_gate.py`) | 0 mm in every clip but Dead L 1.0 mm (3 vertices); it finds no cuff rim (rim vertices 0): the wrists were judged in the viewer (`review/shots/sheet_wrists_r7.png`) |
| See-through (`see_through_gate.py`, 9 role clips, step 5, 4.5 mm px) | torso 129 px (a thin sliver along the cape's side seen from behind-left, every clip), sleeve L 75 / R 62 px (Death), collar 73 px (Death, 2 f), head 5, trousers R 1 (r2 before the rim linings: sleeve 182/152, torso 988, trousers 297/220) |
| Floor (`floor_audit.py --world mm9 --match 'MM9 255*'`) | stand 0, living -0.4, dead 0.0; **walk -0.2..+3.8 (all feet off by 3.8 units at one key; tolerance 2.76)**: per-key grounding with 0.04 s smoothing gave +2.5 but failed jitter (shoulder skin 4.8 mm/f2) |
| Detached (`detached_parts_audit.py`) | 9 flagged: the fur skirt part hangs up to 11 cm off the thigh in Krohn05 (cloth, looked at: `review/shots/sheet_det.png`), the sword carried by the cape 1 cm off it, the glaive pieces 2 cm off the fist in 2 AttackMelee poses, small parts under 1 cm |
| Winding / bones / flat | 0 inverted (after `drop_lod_slivers.py`); 12 checked, 0 stretching; flat 0.00 body and head, props 0.07 (hard blade edges) |
| Texture quality | body atlas 58.3 %, fragments 0.9 %, stretch 1.11 (spread reported infinite: one-texel lining faces); head set 43.8 % (hands at half density by design), stretch 1.26; props 79.5 % |
| Viewer (`run_creature_review.py check`) | 15 switches, 0 failed (r7-20261104) |
| Regression `mm9_actor_models_build_every_binding` | **PASS** (251 descriptors on 113 models, 0 failed; `review/gates_r4/regression_binding.log`) |

## Sheets read
`review/sheet_mm9_vs_ours.png` (MM9 front/3-4/back mirrored to true handedness vs ours), `review/sheet_faces_r2.png` and
`review/faces/r2_zoom.png` (front close-up, 3/4, true profile, low 3/4, party view, ear; MM9 head views on top), `review/faces/r1_zoom_a.png`,
`r1_zoom_b.png`, `review/shots/sheet_clips_r5.png`, `sheet_final_r6.png`, `sheet_hands_r5.png`, `sheet_wrists_r7.png`, `sheet_det.png`,
`review/grip_v1.png`, `review/gates_r1/spear_worst.png`, `review/gates_r4/st_sheet.png`, `review/masters_check.png`, `review/head_check.png`,
`review/xray_v1.png`, `review/hands_v1.png`, `review/cuff_v1.png`, `review/headsplit.png`, `review/mm9_strips_own.png`, `mm9_strips_lib.png`.
Viewer: `http://127.0.0.1:8912/level_generation/creatures/mm9_krohn_claude/review/viewer/`.

## Deviations and open points
- **Weapons** are procedural (outline and proportions from MM9's pieces), plainer than the Codex/Meshy-painted body; no Codex prop
  master (the Guard's weapon prompt was refused). One GLB, no separate attachment (one skin).
- **Arms** hang 9-18 deg further out than MM9's (constant abduction): our scale skirt and mail are fuller than MM9's flat panels.
- **AttackMelee** is the PeasantMale punch with a glaive in the fist; the shaft still crosses the side hair in 6 frames at 24 fps.
- **Cutscene clips** (Krohn01/04/05): the glaive's butt passes behind the right thigh (Krohn05 56 of 484 frames at 24 fps); whether
  OpenYAMM plays the win-game cutscene is script work.
- **Ears** show through the long hair (MM9's hair covers them; Meshy modelled ears on the head shell).
- **Statue prop** (`Krohnstat`, sculpt skins, Scale 7) not built: the `Statue` clip is carried; a stone tier/material is open.
- Handedness: `references_hd/mm9_*` renders are of the raw conversion (the mirror image); the installed model is true-handed.

## Motion pass (orchestrator pre-screen of r7, 2026-11-04; installed sha256 7cbdb15c12b6..., viewer r9)
- **Jitter (AttackMelee, Hit, Death):** no shoulder offset rotates the fast clips any more (a constant or faded offset changed the
  arm's world speed in the punch: +2.4 deg/f). They ease over 0.3 s from and to the in-game Standing, the one with the constant
  abduction (`roles_krohn.json` `ease_s`, `ease_standing_override`, new in `clips_mm9.py`); hands and forearms stay 0 frames > 1 cm.
  The jitter gate (vs `work/mm9_kr_clips.glb`, clips_mm9.py's output, which now carries that ease) passes 0 fails in every clip.
  Against the r7 reference (the old 0.15/0.2 s ease to the unabducted Standing, `work/mm9_kr_clips_ref_r7.glb`) the new ends read as
  differences (AttackMelee up to 8.5 deg/f, `review/gates_r5/jitter_vs_r7ref.txt`): that is the changed ease, not jitter.
- **Death shoulder skin:** the floor pass's death smoothing 0.1 -> 0.15 s (`floor_ops.txt`): skin excess 2.3/2.5 -> 1.4/1.5 mm/f2
  (passes), dying lowest -1.8 cm.
- **Walk hop:** `scripts/walk_floor.py`: one cyclic Gaussian low-pass (0.1 s) of the root height, centred on the floor, instead of
  floor_fix's grounding + smoothing (whose running maximum lifted every foot): walk -2.1..+2.1 units (was -0.2..+3.8; tolerance
  2.76), floor_audit ok, Walking jitter 0.
- **Glaive through the shoulder/side hair in AttackMelee:** `scripts/spear_window.py`: one smooth turn of the glaive about the fist
  over the contact window (eased 0.2 s), axis and angle searched (18 deg about the hand's x): 13.8 cm -> 0.4 cm at 48 fps.
  Cutscene clips the same way: Krohn01 14.8 -> 0.2 cm (38 deg), Krohn04 -> 0.0 (14 deg), Krohn03 1.4 cm 1 frame, Krohn05 2.2 cm
  3 frames (searched at 8 fps over its 20 s; left).
- **Sword through the hair in Death:** the whole-hair follow in Death removed (it added shoulder-skin jitter); `scripts/hair_window.py`
  turns only the side strand Xhairpiv01 20 deg over its contact window: 3.1 cm -> 0.2 cm, jitter 0.
- Sheets: `review/shots/sheet_motion_fix_r8.png` (AttackMelee 0.3/0.375/0.42 s, Death 0.5 s back and side, Walking feet, Krohn01 2.0 s,
  Krohn04 1.0 s). Gates `review/gates_r5/`, `review/gates_r6/` (jitter 0 fails, floor ok, regression PASS 252 descriptors).


**LOD0 reduced post-install on 2026-11-05 by `level_generation/creatures/mm9_krohn_reduce_claude/`** (ledger: `level_generation/creatures/REDUCTION_LEDGER.md`, "MM9 reduction"). A rebuild from this project must re-run that reduction, or it silently restores the heavier mesh. Rollback source: `level_generation/creatures/mm9_krohn_reduce_claude/before/`.
