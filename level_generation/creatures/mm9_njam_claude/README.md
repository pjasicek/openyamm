# MM9 Njam the Meddler (mm9_njam) — 3D actor, 2026-10-31

MM9's trickster god in human form, queue item 27: Njam the Meddler L200 (`MONSTERS.txt` 261, descriptor `MM9 261 Njam the Meddler`,
skin NJAM.dtx, MONSTERS Scale 1.5, `baserange.scr`); body `NJAM.abc`, 45 nodes. Humanoid by the ABC (`Bip01` biped without a Pelvis,
two finger chains per hand, a `Ponytail1`, six two-segment coat-skirt hinges): built on the approved Yrsa route (MM9 skeleton, MM9
clips, grafted five-finger hands, a separate head set), with `mm9_nobleman_claude`'s scripts as the template. One skin, no tiers.
Bare hands. Progress, hashes and Meshy receipts: `creature_3d_progress.json`. Status log: `devdocs/mm9_rework/overnight/status/monster_njam.md`.

| Item | Value |
|---|---|
| Runtime GLB | `assets_source/worlds/mm9/models/mm9_njam.glb` (`tools/install_model.py --world mm9`; 34.1 MB source, 16.6 MB cooked runtime copy) |
| Binding | `assets_dev/worlds/mm9/models/actors.yml`, block `mm9_njam_claude` (`scripts/bind_actors.py` under the flock): `scale: 150` (MONSTERS Scale 1.5), `yaw_offset: -1.570796327`, stride walk 1.37 / run 3.2 (`stride.py`), look `Bip01 Neck, Bip01 Head`, sockets `palm_left: LHand1`, `palm_right: RHand1` (`add_sockets_nj.py`, PeasantMale's socket names), melee impact 1.2 s (Njam_Hattack1 first `Rattack`), ranged impact 0.866 s released from the right palm (Njam_Spell1 `RangeAttack`, the right hand leads), cast `Cast` impact 1.466 s from the left palm (Njam_Spell2 `RangeAttack`) |
| Triangles LOD0/1/2/3 | 11,053 / 5,525 / 1,987 / 662. LOD0: limbs set 3,385 (hands 760 each), torso set 3,150 (skirt lining 446, dark cap 32), head set 4,518 (face skin ~2,600, hair helmet 1,776, neck tube 184) |
| Skeleton | NJAM.abc's 45 nodes, joints moved onto our mesh, rest frames = source frame turned by the least rotation onto our limb (`fit_nj.py`/`fit_nj.json`), + 15 finger bones per side + 12 half-joint helpers `*_h`. The six skirt hinges Bone06/22/14/10/02/18 re-parented to the Spine (`reparent_skirt.py`) |
| Clips (30 fps) | Standing `stand1`, Walking `walk3`, Running `run`, Fidget `fidget1`, AttackMelee `Njam_Hattack1`, AttackRanged `Njam_Spell1`, Cast `Njam_Spell2`, Hit `wince1`, Death `die1`, Dead. **39 script clips**, every other MM9 clip of NJAM.abc and its child PeasantMale.abc: NjamPose `Njam`, SpellAttack, WinGame `njam_wingame`, Twitch, Frozen, Statue, Kick `Njam_kick`, AttackMelee2 `Njam_Hattack2`, Run2, Lean, LeanFidget, BarDrink, BarFidget, BarStand, Bless, Pray, Bow, Conv..Conv5, Fidget2/3/4/5/8, PeasantAttack/2 (`hattack1/2`), Hit2 `wince2`, Backpedal, BackpedalRun, CowerStart/Loop/End, Sc07Shot1, PlayDeath, PlayGetup. None left out (only the `----------` separator) |
| Textures | limbs 1792 + 1K normal + 1K ORM, torso 2048 + 1K normal + 1K ORM, head 1792 + 1K normal + flat ORM. One set, no ramps (one skin) |
| Meshy credits | **20 / 30** (the head pass used none): Smart Topology body 5, head 5, one 4K body paint 10 (backup account, balance 3940 at the start, no retries) |

## Findings in the source

- **Two files of clips.** `NJAM.abc` holds 6 clips (`Njam`, a held T-pose; `spell_attack`; `njam_wingame` with the boss-cutscene
  events; `njam_twitch`, `njam_frozen`, `statue`). Its ChildModels section names `PeasantMale.abc`, which holds the other 41: the
  peasant set and Njam's own `Njam_kick`, `Njam_Hattack1/2`, `Njam_Spell1/2`. Same 45 joints; the rests differ by 4.5 mm at the Spine
  and thighs and up to 9 degrees on five skirt hinges (re-rested onto our mesh anyway). `scripts/merge_child.py` joins them.
- **Skirt hinges on a second root.** The six hinges hang from `root_bone`, a sibling of `Bip01 Spine` that follows it loosely (yaw up
  to 8 degrees apart in walk3, the hinge pivots sliding 2-22 cm against the Spine). `reparent_skirt.py` puts them under the Spine keeping
  MM9's world rotation exactly (renders of the source before and after differ by at most 1 grey level) and pins the pivots at their rest
  offset, so the coat's top ring cannot leave the belt. The second segments (Bone07/23/15/11/03/19) never move in any clip and carry nothing.
- **MM9's own thighs slide:** `bone_length_audit.py` on the true-handed source reads 2 of 12 stretching (thighs 9.7-12.9 cm). Ours reads
  0 of 12 (`ORBIT` in `clips_mm9.py`).
- **`Bip01 Ponytail1`** swings up to 75 degrees (wince2) on a short bob; our hair helmet is rigid on the Head, the bone carries nothing.
- **Freeze skins and statue skin:** `NJAM1-7.dtx` are the freeze sequence `NJAMFREEZE.scr` swaps in; `NJAMSCULPT.dtx` is the statue's.

## Route (scripts/)

0. **Sources:** `convert_abc_model.py --scale 0.0256` (NJAM, PEASANTMALE, gltf_venv site-packages on `PYTHONPATH`), `merge_child.py`,
   `mm9_imp_claude/scripts/mirror_glb.py` -> `source/true/njam_true.glb`, `reparent_skirt.py` -> `source/true/njam_src.glb` (the clip
   source). `ref_renders.py`, `src_strips.py` for the references.
1. **Masters** (Codex through `codex_slot.sh`, `codex_masters.sh`): `references_hd/` five views; `references_head/` clay sculpt
   `00_geometry` (`codex_head.sh`) and seven painted views on clay renders of our own head (`codex_heads.sh`, `head_clay.py`).
2. **Meshy:** Smart Topology 15k on the body (`requests/smart_topology_v1.json`) and on the sculpt (`head_smart_v1.json`); one 4K paint
   on the frozen layout (`retexture_v1.json`).
3. **Clean** (`clean_nj.py`): height scale, each central piece on its own mid-plane, the figure's LEFT half kept (two pin-hole tears on
   the right chest) and mirrored, head/brooches/pendant dropped (head graft; jewellery is paint), reduced per garment with joints protected;
   skirt and belt band split from the coat by height.
4. **Head** (`head_prep_nj.py`, `head_fix_nj.py`, `graft_nj.py`; after the UV freeze `head_post_nj.py`, see the head pass below): Meshy's head came as a face shell with inner pockets behind eyes and
   mouth joined to the skin by slits, plus loose brow, lid and lip strips and a torn hair helmet. Tried and dropped: visibility culling,
   island votes, fold relaxing, a raw polar resample (noisy), a voxel remesh (leaked). Kept: a smooth closed balloon shrunk onto Meshy's
   skin and eyeball caps (`mm9_bigfoot_claude/scripts/head_close.py`'s route), so the **eyes are painted skin** as in MM9; the hair helmet
   rebuilt as a polar grid (thickness held to 0.6-2 cm over the skin, a lip under the rim). Scale 0.30, crown at MM9's 0.952 m.
5. **Rest and weights:** `fit_nj.py`, `rig_nj.py`, `graft_hands.py` (MPFB, `graft_nj.json`), `helpers_nj.py` (`step_b.sh` runs them).
   Pivots: knee 5 cm back, elbow 1.5 cm back, hip 2.5 cm forward. Head/neck band 7 cm wide with extra relax at the nape (r5).
6. **UVs** `uv_nj.py`: **never re-run**, the paint belongs to `work/uv_v1.blend`. Re-rigs go through `carry_uv.py` (checked: max vertex
   move 0.0, 0 loops differ) -> `work/uv_v2.blend`.
7. **Paint:** `scripts/textures.sh` (`compose_nj.py`, gentle grade saturation 0.92 contrast 1.03 with the baked AO, `tone_nj.py`: fur local
   contrast x 0.5 with the detail blurred, normals scaled 0.65 / fur 0.4, `finish_tex.py`). Head: `dump_head.py` + `project_head.py`
   (one source per feature: the face from the front view alone, placed by 12 measured landmarks; z-buffer over both head layers; hair
   texels refuse skin-coloured paint; the hair lip (part 23) takes the outer hair).
8. **Runtime:** `scripts/rebuild.sh [--install]`: `neck_fix_nj.py` (after the UV freeze: the jagged grafted neck rim cut at 0.705 m and a
   tube narrowing down to 0.62 m under the collar, one plain skin texel; marks the hair lip), `finish_nj.py` (skirt and cuff lining 3 mm
   in on the dark texel, a dark cap across the skirt under the belt, hose narrowed toward the leg axes under the hem), `export_nj.py`,
   `clips_mm9.py` (soft joint-offset line), `arm_out.py` (`armout_jobs.txt`), `half_keys.py`, `skirt_keys.py`, `arm_bump.py`
   (`arm_jobs.txt`, script clips), prepare, LODs, shadow fix, `set_material_extras.py` (specular 0, metallic 0), floor, winding,
   `add_sockets_nj.py`, viewer. Binding: `flock level_generation/creatures/claude_shared/locks/mm9_actors_yml.lock python3 <project>/scripts/bind_actors.py`.

## Checks

Installed build r14 (head pass). Its clips equal r9's; r10-r11 changed the limbs image, r12 the head mesh (`head_post_nj.py`) and paint, r13-r14
the head paint only (r14: the hair rim's underside lifted 1.6x, it read as a dark band in the viewer's light). Full gates on r12: `review/gates_r12/` (the collapse table below is r9's; r12 reads the same within a few faces outside the
head, e.g. Standing 2040 -> 1952, AttackRanged 1707 -> 1779, neck 44 -> 48). `gates_r8/`, `gates_r9/` hold the earlier full runs. Validator,
regression and winding ran on r14, detached and flat on r13 (r14 changed one image only). Earlier rounds: `gates/` (r2, first rig), `gates_r3/`, `gates_r5/`.

| Gate | Result |
|---|---|
| `bone_length_audit.py` | **0 stretching of 12** (raw MM9: 2 of 12, its own sliding thighs) |
| Handedness (`handedness.py`) | raw `R Hand` x +0.622 anatomical LEFT; source -0.622, runtime -0.445 anatomical **RIGHT** |
| `detached_parts_audit.py` (24 fps, all 49 clips, r10) | **0 detached**, 11 components (largest root lift: the left leg 38 cm off the right forearm in Kick, a pose, not a gap) |
| `flat_shading_check.py` | 0.00 limbs, 0.01 torso, 0.01 head |
| `check_winding.py` | 0 inverted closed parts |
| `texture_quality.py` (painted faces only, `work/nj_painted_only.glb`) | limbs atlas 55.4 %, spread 1.19, fragments 0.0 %, stretch 1.10; **torso atlas 53.7 %** (target 55: 1.3 points short), spread 1.19, fragments 0.6 %, stretch 1.12; head atlas 55.1 %, spread 1.65 (dense face), stretch 1.07. On the runtime GLB the torso and head spread reads ~1e12 because the linings, the cap and the neck tube sit on single dark/skin texels on purpose |
| `skirt_gate.py` (48 fps, hose through the outer skirt) | Standing 0/145, Walking 0/44, Running 9/50 at 0.5 cm, every other bound clip <= 0.4 cm except **Cast 29/146 at 1.3 cm**. First rig: 1.0-1.7 cm in every clip, Standing included (the Meshy hose stood out through the skirt at the hips; fixed by narrowing the hidden hose under the hem). Script clips: BarFidget 2.0 cm, PlayGetup 10.2 cm (sitting up from the floor), the rest <= 1.0 cm |
| `jitter_gate.py` against the untouched MM9 clips (all 49 clips) | **0 fails** (r9). Every per-clip constant offset or short hold I tried on the hand-on-hip contact of AttackRanged failed this gate (1.08-1.85 deg/f over MM9), so AttackRanged keeps MM9's motion there |
| `orient_gate.py`, head and feet against MM9 | head mean <= 2.2 deg in every bound clip; foot forward a constant 10.9 deg (the rest turn itself); the 45.9 deg foot maxima in the attacks sit at the eased first frames |
| `arm_hand_gate.py --outer-only --exact` (48 fps) | Standing, Walking, Running, Hit, Death, Dead: 0 frames over 1 cm. **Fails:** AttackMelee L 6.0 cm (gate cap), 43 frames (the hand rests on the belly at 2.1-2.9 s), Cast R 5.9 cm, 12 frames (the fingers into the hair behind the head at 1.0 s), AttackRanged R 4.7 cm, 7 frames (hand on the hip at the clip's start), Fidget R forearm 2.0 cm; AttackMelee R 1.0 cm, 1 frame. Script clips: SpellAttack L/R 6.0/5.9, Bow R 5.3, Conv1 L 3.2, Conv5 L 2.2, the rest <= 1.3 cm |
| Finger stretch | p99 at most 1.7 (bound clips), 3.0 in Fidget8 |
| `floor_fix.py` | Dead corpse moved +4.1 cm, Death 26 keys raised to the floor (lowest -4.9 cm before) |
| `--headless-validate-actor-models --world mm9` | 158 descriptors on 65 models, 0 refused |
| Regression `mm9_actor_models_build_every_binding` | **PASS** on r14 (158 descriptors on 65 models, 0 failed) |
| `run_creature_review.py check` | 49 clip switches, 0 failed (r10) |
| In game (`arslegardcity.blv`, review root, r14 install, Njam's own placement at his door; r8 shots in `review/ingame/`) | `review/ingame_tour.png` (`review/ingame_r14/`): textured, at MM9 scale 1.5, full body in frame (shot 2); the face is too small at this distance to judge in game |

Collapse gate (faces under 20 % of rest area or flipped, worst single frame per region, all LOD0 primitives; `scripts/collapse_gate.py`
from `mm9_evilsorcerer_claude`, r9). Strip = faces on the skirt hinges. Seen = faces any camera can see at the clip's worst frame.

| Clip | face-frames | knee_L | knee_R | hip_L | hip_R | groin | ankle_L | ankle_R | elbow_L | elbow_R | shoulder_L | shoulder_R | wrist_L | wrist_R | torso | neck | head | strip | finger | seen |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Standing | 2040 | 0 | 0 | 0 | 0 | 2 | 0 | 0 | 0 | 0 | 7 | 9 | 0 | 0 | 4 | 3 | 0 | 1 | 0 | 18 |
| Walking | 423 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 7 | 7 | 0 | 0 | 2 | 1 | 0 | 3 | 1 | 16 |
| Running | 540 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 7 | 9 | 0 | 0 | 1 | 4 | 0 | 7 | 1 | 13 |
| Fidget | 2171 | 0 | 0 | 0 | 0 | 2 | 0 | 0 | 0 | 3 | 7 | 15 | 0 | 0 | 4 | 4 | 0 | 1 | 2 | 21 |
| AttackMelee | 3360 | 0 | 0 | 2 | 0 | 2 | 1 | 0 | 8 | 10 | 6 | 8 | 2 | 4 | 2 | 23 | 3 | 3 | 13 | 33 |
| AttackRanged | 1707 | 0 | 0 | 0 | 0 | 2 | 0 | 0 | 3 | 3 | 14 | 9 | 0 | 0 | 3 | 44 | 5 | 8 | 0 | 50 |
| Cast | 1785 | 0 | 0 | 0 | 0 | 2 | 0 | 0 | 5 | 6 | 16 | 19 | 0 | 0 | 5 | 7 | 2 | 6 | 0 | 51 |
| Hit | 533 | 0 | 0 | 0 | 0 | 3 | 0 | 0 | 0 | 0 | 6 | 11 | 0 | 0 | 3 | 15 | 0 | 1 | 0 | 16 |
| Death | 482 | 0 | 0 | 0 | 0 | 2 | 0 | 0 | 3 | 0 | 5 | 8 | 0 | 2 | 8 | 16 | 2 | 5 | 0 | 8 |
| NjamPose | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| SpellAttack | 1287 | 0 | 0 | 0 | 0 | 2 | 0 | 0 | 3 | 9 | 10 | 8 | 0 | 1 | 3 | 13 | 1 | 1 | 0 | 22 |
| WinGame | 2707 | 0 | 0 | 0 | 0 | 6 | 0 | 0 | 0 | 0 | 9 | 10 | 0 | 0 | 3 | 10 | 0 | 4 | 0 | 13 |
| Twitch | 174 | 0 | 0 | 0 | 0 | 2 | 0 | 0 | 0 | 0 | 2 | 3 | 0 | 0 | 0 | 10 | 0 | 2 | 0 | 9 |
| Frozen | 34 | 0 | 0 | 0 | 0 | 2 | 0 | 0 | 0 | 0 | 0 | 3 | 0 | 0 | 0 | 10 | 0 | 2 | 0 | 9 |
| Statue | 58 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 9 | 9 | 0 | 0 | 2 | 1 | 0 | 8 | 0 | 22 |
| Kick | 3912 | 0 | 0 | 0 | 0 | 4 | 0 | 1 | 0 | 0 | 5 | 8 | 0 | 0 | 2 | 72 | 5 | 18 | 0 | 29 |
| AttackMelee2 | 4292 | 0 | 0 | 0 | 0 | 4 | 0 | 0 | 5 | 4 | 5 | 10 | 0 | 2 | 3 | 42 | 2 | 34 | 0 | 30 |
| Run2 | 620 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 3 | 3 | 8 | 8 | 0 | 0 | 2 | 4 | 0 | 4 | 0 | 13 |
| Lean | 744 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 2 | 4 | 0 | 1 | 3 | 0 | 0 | 1 | 0 | 12 |
| LeanFidget | 1412 | 0 | 0 | 0 | 0 | 2 | 0 | 1 | 4 | 0 | 5 | 8 | 4 | 1 | 4 | 2 | 0 | 1 | 2 | 16 |
| BarDrink | 2864 | 0 | 0 | 0 | 0 | 2 | 0 | 0 | 4 | 3 | 7 | 8 | 2 | 1 | 3 | 18 | 0 | 1 | 4 | 28 |
| BarFidget | 1734 | 0 | 0 | 0 | 0 | 6 | 0 | 0 | 3 | 3 | 12 | 12 | 6 | 1 | 4 | 4 | 0 | 2 | 4 | 24 |
| BarStand | 1024 | 0 | 0 | 0 | 0 | 2 | 0 | 0 | 4 | 0 | 7 | 6 | 2 | 1 | 3 | 2 | 0 | 1 | 4 | 25 |
| Bless | 3005 | 0 | 0 | 0 | 0 | 2 | 0 | 0 | 0 | 3 | 8 | 12 | 0 | 1 | 3 | 11 | 0 | 2 | 1 | 18 |
| Pray | 3503 | 0 | 0 | 0 | 0 | 2 | 0 | 0 | 0 | 0 | 21 | 15 | 0 | 0 | 4 | 7 | 0 | 4 | 0 | 35 |
| Bow | 1687 | 0 | 0 | 0 | 0 | 4 | 0 | 0 | 0 | 3 | 5 | 9 | 0 | 1 | 3 | 16 | 6 | 6 | 0 | 32 |
| Conv | 2072 | 0 | 0 | 0 | 0 | 2 | 0 | 0 | 0 | 0 | 6 | 9 | 0 | 0 | 4 | 12 | 1 | 1 | 0 | 15 |
| Conv1 | 2668 | 0 | 0 | 0 | 0 | 2 | 0 | 0 | 8 | 0 | 9 | 9 | 0 | 0 | 4 | 5 | 0 | 1 | 0 | 13 |
| Conv2 | 2125 | 0 | 0 | 0 | 0 | 2 | 0 | 0 | 0 | 0 | 8 | 10 | 0 | 0 | 2 | 7 | 0 | 1 | 1 | 15 |
| Conv3 | 2148 | 0 | 0 | 0 | 0 | 2 | 0 | 0 | 0 | 0 | 8 | 12 | 0 | 0 | 4 | 2 | 0 | 1 | 1 | 21 |
| Conv4 | 1372 | 0 | 0 | 0 | 0 | 2 | 0 | 0 | 0 | 0 | 7 | 10 | 0 | 1 | 3 | 5 | 0 | 1 | 1 | 13 |
| Conv5 | 11923 | 0 | 0 | 0 | 0 | 2 | 0 | 0 | 8 | 0 | 9 | 8 | 0 | 0 | 3 | 7 | 0 | 1 | 0 | 15 |
| Fidget2 | 618 | 0 | 0 | 0 | 0 | 2 | 0 | 0 | 3 | 0 | 5 | 8 | 0 | 0 | 2 | 7 | 0 | 1 | 0 | 15 |
| Fidget3 | 2404 | 0 | 0 | 0 | 0 | 2 | 0 | 0 | 0 | 0 | 7 | 7 | 0 | 0 | 2 | 3 | 0 | 1 | 2 | 17 |
| Fidget4 | 1460 | 0 | 0 | 0 | 0 | 2 | 0 | 0 | 0 | 5 | 5 | 9 | 0 | 1 | 4 | 2 | 0 | 1 | 2 | 15 |
| Fidget5 | 2080 | 0 | 0 | 1 | 5 | 10 | 0 | 0 | 0 | 0 | 6 | 8 | 0 | 5 | 3 | 6 | 2 | 18 | 19 | 33 |
| Fidget8 | 1400 | 0 | 0 | 0 | 0 | 2 | 0 | 0 | 0 | 0 | 19 | 8 | 0 | 2 | 4 | 4 | 0 | 1 | 5 | 24 |
| PeasantAttack | 601 | 0 | 0 | 0 | 0 | 4 | 0 | 0 | 3 | 3 | 8 | 8 | 0 | 1 | 3 | 7 | 0 | 4 | 2 | 18 |
| PeasantAttack2 | 904 | 0 | 0 | 0 | 0 | 10 | 0 | 0 | 3 | 3 | 8 | 8 | 1 | 1 | 6 | 11 | 1 | 8 | 5 | 33 |
| Hit2 | 1133 | 0 | 0 | 0 | 0 | 3 | 0 | 0 | 2 | 0 | 5 | 8 | 0 | 1 | 4 | 36 | 3 | 4 | 3 | 32 |
| Backpedal | 633 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 7 | 7 | 0 | 0 | 2 | 1 | 0 | 3 | 1 | 16 |
| BackpedalRun | 379 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 7 | 7 | 0 | 0 | 2 | 1 | 0 | 3 | 1 | 15 |
| CowerStart | 585 | 0 | 0 | 0 | 0 | 16 | 0 | 0 | 3 | 3 | 7 | 8 | 0 | 0 | 5 | 18 | 0 | 7 | 0 | 29 |
| CowerLoop | 2032 | 0 | 0 | 0 | 0 | 16 | 0 | 0 | 3 | 3 | 5 | 3 | 0 | 0 | 5 | 14 | 0 | 7 | 0 | 29 |
| CowerEnd | 1147 | 0 | 0 | 0 | 0 | 16 | 0 | 0 | 3 | 3 | 5 | 8 | 0 | 0 | 5 | 14 | 0 | 7 | 0 | 29 |
| Sc07Shot1 | 443 | 0 | 0 | 0 | 0 | 2 | 0 | 0 | 0 | 0 | 5 | 9 | 0 | 0 | 4 | 5 | 0 | 1 | 0 | 16 |
| PlayDeath | 1474 | 0 | 0 | 0 | 0 | 4 | 0 | 0 | 3 | 0 | 5 | 8 | 0 | 2 | 8 | 20 | 3 | 5 | 0 | 13 |
| PlayGetup | 3589 | 0 | 0 | 12 | 1 | 5 | 1 | 0 | 3 | 1 | 13 | 9 | 0 | 2 | 5 | 41 | 4 | 22 | 1 | 34 |
| Dead | 682 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 0 | 16 | 2 | 2 | 0 | 8 |

First rig (r2) against final (r9), face-frames: Standing 2051 -> 2040, Walking 435 -> 423, Running 571 -> 540, Fidget 2444 -> 2171,
AttackMelee 4559 -> 3360, AttackRanged 3045 -> 1707, Cast 2150 -> 1785, Hit 593 -> 533, Death 704 -> 482, Dead 1395 -> 682,
Kick 6456 -> 3912, AttackMelee2 6070 -> 4292, CowerLoop 2761 -> 2032.

These are real counts, not excused. Knees, hips and ankles stay at 0-2. **Shoulders are the open joint** (7-9 already in Standing,
up to 19 in Cast, mostly visible): MM9's stand brings our A-pose arms down 30 degrees and the coat folds under the arm, as on the
Nobleman. **Neck** came down from 89 to 44 in AttackRanged (wider head/neck band, more relax) but still folds at the nape under the
hair rim when the head turns far; most of those faces sit under the hair lip, and the tiny slivers there (0.01-0.6 cm2) come from the
balloon head's decimation.

## Not zero, with why (second attempts done)

- **AttackMelee L hand on the belly (6 cm, 43 frames):** MM9's hand rests on the stomach; our coat is fuller. Tried: `arm_bump.py`
  (15 deg over the whole clip, 12 -> 10.9 cm by its own measure, jitter failed), `arm_out.py` abduction 16 deg (forearm 5.4 -> 2.2 cm, the
  fingertips still in), forward flexion 16 deg both signs (one made the forearm worse, 6.0 cm). Kept: abduction 16 deg at 1.75-3.03 s.
- **Cast R fingers in the hair (5.9 cm, 12 frames):** MM9's hands go to the temples; our hair helmet stands 0.6-2 cm off the skull. Tried:
  bump 12 deg (6.5 -> 5.3, jitter), abduction 14/24 deg, an extra fore-aft turn (jitter failed). Kept: abduction 24 deg at 0.3-1.8 s (46 -> 12 frames).
- **AttackRanged R hand on the hip (4.7 cm, 7 frames at the start):** every offset that cleared it (bump 18 deg: 0.4 cm; constant 14 deg:
  2.3 cm; holds of 14/10/8 deg faded out by 0.6-1.0 s) failed the jitter gate, because the clip's fast throw follows at once. MM9's motion kept.
- **Torso atlas 53.7 %** against 55: the UVs were frozen for the paid paint; a new layout means a new 10-credit paint for 1.3 points.

## Script events (engine/script work, not done here)

`NJAMFREEZE.scr` drives the boss end: on panic `PlayAnim njam_wingame` (our `WinGame`), with model keys at **CameraSwitch 1.692 s,
StartBall 2.414 s** (`DoClientFX "Njam lightball for cutscene"` + column01.wav), **CameraSwitch2 2.944 s, Lightning 4.647 s**; then
`LoopAnim Njam` (`NjamPose`), on Lightning `Loopanim njam_twitch` (`Twitch`) and the **freeze skins NJAM1..NJAM7.dtx** swapped every 0.4 s
(`SetModelFilenames`), on LightningOff `Loopanim njam_frozen` (`Frozen`). `NJAMTAUNT.scr` (walk to a marker, two rollover texts, vanish
with the GreaterDemon client FX), `SPAWNNJAM.scr`/`SPAWNNJAMCAMEO.scr` (appear/vanish at markers in the Tomb of a Thousand Terrors),
`NJAMCHASE.scr` (opens Njam's door, then he chases). Their clips are all bound as `script_clips`; the camera switches, the light ball, the
lightning, the freeze skins (none built: NJAM1-7 would be seven more images or ramps) and the statue skin (`NJAMSCULPT`, `statue` clip,
decoration `mm9_njamstatue`) are left for the script work.

## Deviations and open points

- **Head (head pass r12-r13, coordinator's review of r11: gaunt, droopy, smeared, dark band under the fringe, pale cheek strips, plain
  helmet):** 0 credits. New Codex paint (`references_head/`, brief v2: about 28, smug, clear wide eyes, crisp features; the first paint is in
  `references_head/v1/`) with a CLOSE front view `08_face` at twice the pixels, which is the face's only paint source out to the cheeks and
  jaw (`project_head.py`, 15 landmarks incl. the fringe edge; the smirk kept); 3/4 views paint only beside the cheeks, side views behind
  them, the front view only the fringe and crown hair; hair texels refuse skin-coloured paint and skin texels refuse hair-coloured paint;
  the neck tone comes from the close view's own neck. Mesh: `head_post_nj.py` (vertex moves only, UVs and weights kept) re-projects the
  face onto Meshy's skin (0.25 mm mean: the remaining softness is Meshy's own face shape) and gives the hair a rolled pageboy rim (12 %
  fuller 1.2 cm above the edge, rolling in to 55 % at the edge); the rim's underside (part 23) carries the outer hair's paint and lies
  1.5 mm off the skin, so the fringe underside reads as hair, not a black band, and the skin starts at the hairline.
  Read at full size, front, both quarters, side, back, below (`review/sheet_head_full.png`, r14): one nose, one mouth, both eyes level,
  green-blue and open, the smirk on the closed mouth, stubble on the jaw only. Seen and not fixed: the face is still smoother and wider
  than the Codex face (mesh); a small dark nick on the right cheek; a thin pale line along the hairline on the forehead and temples; the hair is still a closed shell with painted strands, no loose locks;
  a soft tonal step where the close-view paint meets the 3/4 paint on the cheek side; the neck is short above the high collar.
- **Collar V:** the coat's painted V at the throat has a ragged lower edge (Meshy paint).
- **Hose:** Meshy's flecks and a gold dot on the left thigh cleaned to the hose green (`tone_nj.py`, r10-r11, `review/r11_body.png`); the
  hidden hose top under the skirt carries smeared projected coat paint.
- **Fur** reads combed and a little blotchy up close (`tone_nj.py` halves its local contrast).
- **Hands:** MPFB, with MM9's curl through `finger_alias`.
- **Ponytail1** unused (rigid hair helmet).
- **Rest pose:** our A-pose, not MM9's T-pose; MM9's local rotations give MM9's world rotations (`orient_gate.py`).
- **Corrections on MM9's clips**, all smooth single curves: `arm_out.py` AttackMelee L 16 deg (1.75-3.03 s), Cast R 24 deg (0.3-1.8 s);
  `arm_bump.py` on script clips (SpellAttack L, Lean L, Bow R, Conv1/2/4/5, Fidget3/4/5/8); `half_keys.py`; `skirt_keys.py`.
- **Size:** 34.1 MB source GLB (49 clips), 16.6 MB cooked runtime copy.
- Events `lunge`, `footstep`, `Rkick`, `Lkick`, `Lattack` and the second and third `Rattack` of Njam_Hattack1 are not bound; sounds not wired.
- Rows at MM9's size (Scale 1.5). Health bar position against the sprite row height: not measured.

## Sheets (viewer shots unless noted)

`review/sheet_mm9_vs_ours.png` (MM9 is a Blender render of the true-handed source with its own light, top; ours bottom, same clip times),
`review/sheet_body.png` (four sides, walk, run), `review/sheet_head_full.png` (full size: front, figure's right quarter, side, back, below,
left quarter), `review/sheet_close_{CowerLoop,Death,Dead,Running,Kick}.png` (knees, groin, armpits, elbows and the mouth, cameras fixed to the
body so a lying corpse is framed from the same side), `review/sheet_hands.png`, `review/strips_0..6.png` (every clip, six times, two views; r8:
r12), `review/ingame_tour.png`. Numbers: `review/gates_r8/`, `review/gates_r9/`; first rig `review/gates/`.
Strips `review/strips_0..6.png` and the close-up sheets were reshot on r12-r13 (r12 for the strips: same clips and body, the head paint
refined in r13). Viewer: http://127.0.0.1:8912/level_generation/creatures/mm9_njam_claude/review/viewer/

## Not checked

LOD1-3 and shadow meshes by eye; motion at normal speed by eye (no playback recording made: strips and gates only); the other placement
(`darkpassageway.blv`); indoor light variety, fog, night; melee contact timing and footsteps; sounds; the corpse in game; the scripted events
above; Android cook; the face up close in game (the r14 capture shows him at room distance); the strips and close-ups at r14 (strips are r12, close-up sheets r13, the head sheet r14: only the head paint differs between them).


User artistic acceptance: not recorded


**LOD0 reduced post-install on 2026-11-05 by `level_generation/creatures/mm9_njam_reduce_claude/`** (ledger: `level_generation/creatures/REDUCTION_LEDGER.md`, "MM9 reduction"). A rebuild from this project must re-run that reduction, or it silently restores the heavier mesh. Rollback source: `level_generation/creatures/mm9_njam_reduce_claude/before/`.
