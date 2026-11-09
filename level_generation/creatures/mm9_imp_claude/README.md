# MM9 Imp family (mm9_imp) — 3D actor, 2026-10-30

## Dropped MM9 clips (2026-10-31, run2-clips-groupD) - current

The user lifted the hold on this approved project for clip grafting only. 7 of IMP.abc's 16 clips were missing; all are
carried now. `scripts/extra_clips.sh` (roles `scripts/roles_imp_extra.json`, floor `scripts/floor_ops_extra*.txt`) builds them
through the accepted steps (clips_mm9 with grip.json, trident_clear, floor on the split body, mirror) and grafts only them onto
the installed export (`work/pre_clips_export.glb` kept); `graft_byte_check.py`: OK, 15.48 -> 16.30 MB. Bound as `script_clips`
on Imp A/B/C: fidget2 Fidget2, aware Aware, attack_melee2 AttackRanged (MM9's Hattack1 carries Rattack1's keys), hit2 Hit2,
death2 Death2, dead2 Dead2 (die2's last pose), backpedal Backpedal, backpedal_run BackpedalRun. Fidget2 goes through
`scripts/trident_clear_wide.py` (new copy, hold 0.12 s, clearance 2.5 cm): the accepted constants left the trident head 3.0 cm in
the head on one 48 fps frame. Gates (`review/clips_restore_D/`): hands 0 frames over 1 cm; trident worst 0.5 cm (Fidget2), 0.4
elsewhere; bones 0 stretching; floor living -0.8..+2.7 cm, Death2 -1.5 on one frame (the leap's take-off), corpse 0; jitter: arm
joints 0 excess, Death2 shoulder skin 2.4/2.9 mm/f2 over MM9 (limit 2.0; the floor settle). MM9's aware is fidget2 at double
speed. Strips `review/clips_restore_D/strip_new_*.png` (untextured, read). Not looked at in the viewer or in game.
Edits to approved files (opt-in, defaults unchanged; the patched `clips_mm9.py` rebuilds the accepted clips byte for byte): `clips_mm9.py` gained roles-json `soft_offsets` (the soft joint-offset line) and a per-role `hold`; `scripts/bind_actor.py` carries the new script clips.

MM9's trident imp for the MM9 world: Imply (MONSTERS.txt 78, `MM9 Imp A`, IMP1), Imp (79, `B`, IMP2), Imp Elder (80, `C`,
IMP3), body `IMP.abc`, 65 joints, 15 clips, weapon skin IMPTRIDENT. Placed in Anskram Keep, needed by Chasm of the Dead. Built
on the approved Yrsa route: Meshy HD body on the ORIGINAL MM9 skeleton, MM9's own clips. Progress, hashes and Meshy receipts:
`creature_3d_progress.json`.

| Item | Value |
|---|---|
| Runtime GLBs | `assets_source/worlds/mm9/models/mm9_imp.glb` + attachments `mm9_imp_trident.glb`, `mm9_imp_wrapl.glb`, `mm9_imp_wrapr.glb` (B), `mm9_imp_tongue.glb` (C), installed with `tools/install_model.py --world mm9` |
| Binding | `assets_dev/worlds/mm9/models/actors.yml`, `MM9 Imp A/B/C` (rows existed), `scale: 100`, `yaw_offset: -1.570796327`, look `Bip01 Neck, Bip01 Head`, stride 0.76 / 1.0, sockets `trident: Yweapon`, attack_melee impact 0.389, attack_ranged impact 0.45 released at `trident` |
| Triangles LOD0/1/2/3 | 8,864 / 4,419 / 1,587 / 514 with all parts; body 8,080 (head 3,263, body 4,817; from Smart Topology 15,695); trident 408, wrap 168 each, tongue 40 |
| Skeleton | IMP.abc, 65 joints, names and rest rotations unchanged, joints translated, + helper bones `Xwrap L/R`, `Xtongue` |
| Clips (30 fps, MM9 events) | Standing `stand`, Walking `walk`, Running `run`, Fidget `fidget1`, Taunt `taunt` (script clip), AttackMelee `Hattack2` (Rattack 0.389 s), AttackRanged `Rattack1` (RangeAttack 0.45 s), Hit `wince1`, Death `die1`, Dead |
| Textures | body 2K colour + 1K normal/ORM, head set 2K colour + 1K normal/ORM (Yrsa's split; see Deviations), props 2048 x 1024 |
| Tiers | one shared set; region mask R skin, G claw tips (body) / eyes (head); ramps from IMP1-3; eye emission per tier, strength 0.42 |
| Meshy credits | **25** (Smart Topology 5, body retexture 10, head retexture 10; backup account), no retries |

## Route (scripts/)

0. **Masters** (Codex, `references_hd/`, briefs `CODEX_BRIEF.md`, `CODEX_BRIEF_PARTS.md`; `references_head/`): inputs are renders of
   the MM9 model and skin (`ref_renders.py`). Five body views, trident `05_trident.png`, shin wrap swatch `06_wrap.png`, head
   turnaround. The tongue image was refused twice by the image tool's filter, so the tongue texture is painted in
   `compose_props.py`.
1. **Meshy** Smart Topology 15k from `00_three_quarter.png`.
2. **Fit** (`fit_imp.py`, `fit_imp.json`, `digits.py`, `scipy_free_tail.py`): height scale, torso aligned, centre chain = MM9's
   joints. Limbs: joint estimates from slices, FK with MM9's bone directions and our lengths, the mesh posed there by a
   transient skin, so MM9's clips give MM9's poses (the Meshy legs are symmetric, MM9's bind has a 19 cm stagger; without this
   the gait would carry that offset). The Meshy tail, twice MM9's, is curve-deformed onto MM9's chain x 1.25. A Kabsch fit
   (`fit_mm9.py`, Winged Mutant route) collapsed the arms on this body and is not used.
3. **Weights** (`rig_imp.py`, `rig_imp.json`): MM9 surface labels diffused, then arm bands, tail along its chain, head above a
   plane under the chin (the chin stretched into a spike until the plane went 3 cm below it), flap on `Xpiv`, belt on the pelvis,
   loose pieces rigid, 3 smoothing passes. Studs deleted as geometry (578 vertices), kept as paint.
4. **Reduce, split, UVs** (`reduce_body.py`, `head_split.py`, `texpass_uv.py`, `texpass_head_uv.py` with `uv_atlas.py`), **4K retextures**.
5. **Fingers** (`finger_fix.py`, `finger_fix.json`): the design has thumb + three clawed fingers and MM9 has real three-joint
   chains for them, so no MPFB graft: digits by connectivity, knuckles levelled, MM9's chains placed in them.
   **Toes** stay on MM9's joints; the toes are fused lobes with claws, weights from MM9's labels.
6. **Fist** (`grip_imp.py`): right hand solved round the shaft per digit, constant in every clip (`fixed_local_file` in
   `clips_mm9.py`); MM9's right-hand curl is constant too. `Yweaponbase` moves to the solved handle centre.
7. **Parts** (`make_trident.py`: geometry from the master's silhouette, planar projection; `make_parts.py`).
8. **Textures** (`bake_ao_texpass.py`, `compose_texpass.py`, gentle grade, `tone_studs.py`, `compose_tiers.py`, `compose_props.py`).
   `tone_studs.py`: the head paint came back more orange than the body (RGB 167/105/15 vs 117/82/3), matched by one gain on the
   skin class; Meshy painted the studs chalk white, 83 pale blobs on the leather became steel domes with a normal-map bump.
9. **Runtime** (`scripts/rv.sh [--install]`, `build_runtime.sh`): export -> clips -> `trident_clear.py` -> prepare -> LODs -> shadow
   fix -> ramps -> attachments split -> floor -> eye emission -> `mirror_glb.py` -> winding -> install -> viewer tiers.

Rebuild from the master: `TOKEN=<lease> scripts/rv.sh --install` in the project folder (`work/master.blend`). Never re-run the UV
scripts: the paint belongs to their exact layouts. `PYGLTF_PYTHON` is `claude_shared/gltf_venv/bin/python`; `work/pylib` links
the system `yaml` for `convert_abc_model.py`.

## Checks (2026-10-30, final build)

| Gate | Result |
|---|---|
| `detached_parts_audit.py --fps 48` | 18 components, **0 detached** |
| `flat_shading_check.py` | **0.00** on both materials |
| `check_winding.py` | **0** inverted (3 tiny shadow-LOD fragments flipped by `fix_winding.py`) |
| `arm_hand_gate.py --outer-only --exact`, 48 fps | hand and forearm **0.0 cm** inside the body in every clip, 0 frames > 1 cm (hand-to-skin distances cross-checked directly: 3.4 cm or more on the sampled frames); finger stretch p99 2.3, max 5.5; wrist max 107 deg (MM9's Taunt) |
| `jitter_gate.py` against MM9's clips | **0 fails** |
| `blade_gate.py` (trident vs skin, shaft sampled, 48 fps) | worst AttackMelee **1.3 cm on 1 frame** (head), others 0.4 cm or less, Hit was 5.7 cm before `trident_clear.py` (tilt 4-7 deg, smoothed) |
| Floor (`floor_audit.py --world mm9 --match 'MM9 Imp*'`) | 3/3 ok: stand 0, walk -0.8..+2.5, living -1.9, dead 0 |
| `texture_quality.py` body / head | atlas **52.6 % / 61.9 %**, spread 1.13 / 1.11, islands 89 / 86, fragments 0.3 / 0.9 %, stretch p90 1.11 / 1.08, 4K source |
| Head topology | 0 flipped, 0 non-manifold |
| Viewer `run_creature_review.py check` | 0 console errors, 30 switches, revision `r3_imp_20261030` |
| Regression `mm9_actor_models_build_every_binding` (`--world mm9`) | 69 descriptors on 33 models, 0 failed |
| In game (`bootcamp.odm`, spawned tiers) | `review/ingame_sheet.png`: trident and wraps attached, attacks play (before the last tongue edit) |

Mirror symmetry of the upper body (bind, residual to the mirrored mesh): mean 8.8 mm, p90 14.2 mm, max 7 cm. Not made exact: the
Meshy body is close, and MM9's own legs and stance are not symmetric.

Sheets (viewer shots unless noted): `review/compare_mm9.png` (MM9 vs ours, eight clip extremes; MM9 is a Blender render, its
image mirrored), `review/sheet_tiers.png` (A/B/C), `review/sheet_close.png` (mouths, hands, tail), `review/sheet_c3.png` (tongue),
`review/sheet_strip.png` (walk and run), `review/fit_v2.png` and `review/fit_v2_digits.png` (bind overlay on MM9, Blender).

## Deviations and open points

- **Mirror (inferred from the coordinate handling and bone names, not compared with MM9 footage).** `convert_abc_model.py` keeps
  LithTech's left-handed numbers, so every MM9-route GLB is the mirror image of the game's actor: MM9's `R Hand` lands on the anatomical left. It never showed on bare hands. `mirror_glb.py` conjugates the final
  GLBs by x -> -x, so the trident is in the true right hand; bone names keep MM9's meaning. Other MM9 models are still mirrored.
- **Head set colour 2K**, as Yrsa's approved route, not the 1K the brief names.
- **Tier parts are attachments**, one extra draw each: B's shin wraps (painted in IMP2) and C's tongue (painted in IMP3) cannot be
  ramps. Wraps are rigid on helper bones below the knee; three.js viewer GLBs drop the parts of the other tiers.
- **Eyes**: C's MM9 eye has a small pupil; ours is a pupil-less orange glow from the ramp.
- **No MPFB hands, no five fingers**: the design has four digits, compared with the MM9 model above.
- **Fist in the swivel**: the fingers are constant in all clips; `Rattack1`'s 98 deg `Yweaponbase` turn is a spin about the shaft,
  so the fist holds.
- **Eye cups** (two parts, 14-edge open loops inside the head) are kept: they read clean, unlike Annud's.
- **Trident floor**: the floor pass ignores the trident, whose butt swings under the feet in Walking, as in MM9.
- Open: AttackMelee frame 26 of the shaft touching the head by 1.3 cm; the tongue reads as a thin hook from the side.
- Normal-speed playback was not watched: judged from the jitter gate and frame strips.
- User artistic acceptance: not recorded.


**LOD0 reduced post-install on 2026-11-04 by `level_generation/creatures/mm9_imp_reduce_claude/`** (ledger: `level_generation/creatures/REDUCTION_LEDGER.md`, "MM9 reduction"). A rebuild from this project must re-run that reduction, or it silently restores the heavier mesh. Rollback source: `level_generation/creatures/mm9_imp_reduce_claude/before/`.
