# MM9 PeasantM2 townsman (mm9_peasantm2) — 3D actor, 2026-11-01

MM9's most common townsfolk body (`PEASANTM2.abc`, 45-joint PeasantMale skeleton, about 98 placements in the rebuilt cities).
`MONSTERS.txt` rows on this model: **44** Commoner, Peasant Human1 MaleA B (skin PEASANTM2B) and **50** Commoner, Peasant Human2 MaleA A
(PEASANTM2A). Both skins are tiers of one body. PEASANTM2C/D are skins of a different model, `PEASANTM2D.abc` (714 tris, a young
blond elf with pointed ears, rows 24 Town Elf MaleB A and 26 Shopkeeper Elf MaleC A): not tiers of this body, so not built here.
Built on the approved MM9 humanoid route (MM9 skeleton, MM9 clips, grafted five-finger hands, a separate head set), with
`mm9_njam_claude`'s scripts as the template (same PeasantMale skeleton) and `mm9_nobleman_claude`'s tier approach. Batch brief:
`devdocs/mm9_rework/overnight/TOWNSFOLK_BRIEF.md`. Status log: `devdocs/mm9_rework/overnight/status/townsfolk_peasantm2.md`.

| Item | Value |
|---|---|
| Runtime GLB | `assets_source/worlds/mm9/models/mm9_peasantm2.glb` (`tools/install_model.py --world mm9`), = `export/mm9_peasantm2.glb`, variants `pm2_a`, `pm2_b` |
| Binding | `assets_dev/worlds/mm9/models/actors.yml`, block `mm9_peasantm2_claude` (`scripts/bind_actors.py 1.1 2.8` under the flock): `MM9 50 Commoner` skin `pm2_a`, `MM9 44 Commoner` skin `pm2_b`; scale 100 (MONSTERS Scale 1), `yaw_offset` -1.570796327, stride walk 1.1 / run 2.8, look `Bip01 Neck, Bip01 Head`, melee impact 0.533 s (hattack2 `Rattack`, as `MM9 54 Shopkeeper` on the same library) |
| Rows / tables | rows 44 and 50 appended to `tools/mm9_import_discovery/mm9_npc_actor_rows.tsv` (legacy visuals 359 / 367, the stand-ins of `mm9_npc_legacy_replacements.tsv`), `generate_mm9_monster_tables.py` run (170 rows), both under the flock (`scripts/add_rows.py`) |
| Triangles LOD0/1/2/3 | 12,039 / 6,018 / 2,164 / 720. LOD0: limbs set 3,519 (hands 760 each), torso set 2,650 (skirt, cuff and hem linings 520, skirt cap 32), head set 5,870 (face shell 3,580, hair 1,144 + its lining 1,144) |
| Skeleton | PEASANTM2.abc's 45 nodes (rest frames turned by the least rotation onto our limbs, `fit_pm2.py`) + 15 finger bones per side (MPFB hands, `finger_alias` from MM9's mitten curl) + 12 half-joint helpers `*_h`; MM9's six skirt hinges re-parented to the Spine (`reparent_skirt.py`) |
| Clips (30 fps, MM9 PeasantMale library) | Standing `stand1`, Walking `walk3`, Running `run`, Fidget `fidget4`, Talk `conv2`, AttackMelee `hattack2`, Hit `wince1`, Death `die1`, Dead; script clips Cower `cower`, Conv1 `conv1`, Conv3 `conv3`, Bow `bow` |
| Textures | limbs 1792 colour + 1K normal + 1K ORM (shared); torso 2048 colour + 1K normal + 1K ORM + 1K region mask (shared, ramps per tier); head 1792 colour + 1K normal per tier, 1K ORM shared. 12 images |
| Meshy credits | **35 / 60**: Smart Topology 5, body 4K paint 10, head-only 4K paints tier A 10 and tier B 10 (backup account 3,740 at the start of the batch, 3,605 after my last job; floor 2,740 never reached) |
| Viewer | http://127.0.0.1:8912/level_generation/creatures/mm9_peasantm2_claude/review/viewer/ tiers `pm2_a`, `pm2_b` |

## Clips: what MM9's scripts play

Placed as DAT classes `CommonerHuman2MaleA` (and `CommonerHuman1MaleB`) with `models\PeasantMale.abc`. Scripts on the placements:
none (NPCbase.scr from the row), `ThjorgardSpectator.scr` (no animation), `StonesPlayer.scr`, `NPC*.scr` (talk/quest, no animation),
`Randverrun.scr` and NPCbase.inc via BaseRun.inc (`LoopAnim Cower`), `Wilam.scr` (conv2, Conv1, conv3, `stand` (not in the library:
Standing plays stand1), Bow). No wander marker names an animation. NPCbase's `Converse` plays the conversation clip (Talk). Carried
exactly those, as Annud on the same library (user decision: only the clips the scripts play).

## Route (scripts/)

0. **Sources:** `convert_abc_model.py --scale 0.0256` with each skin (`source/pm2_a..d`, `pm2d_c` for the M2d check), `merge_child.py`
   with the PeasantMale library (`../mm9_annud_claude/source/mm9_lib/pmale.glb`), `mirror_glb.py` (true handedness),
   `reparent_skirt.py` -> `source/true/pm2_src.glb` (clip source). `ref_renders.py` for the MM9 views (`references_hd/mm9_*`).
1. **Masters** (`references_hd/`, Codex via `codex_slot.sh`, `scripts/codex_masters.sh`): tier A, A-pose. Codex returned a second
   right profile for `03_left`, so `03_left_clean.png` is the mirrored `04_right_clean.png` (the figure is symmetric); all `*_clean.png`
   have the Codex halo removed (`clean_alpha.py`). **Head turnarounds** (`references_head/`, `scripts/codex_heads.sh`): tier A bearded
   with white hair, tier B a different, clean-shaven man with ash-grey hair on the same head outline (`grey_sheet.png`).
2. **Meshy:** Smart Topology 15k on `00_three_quarter_clean.png`; one 4K body paint on the frozen layout (head faces collapsed);
   one 4K head-only paint per tier on the head upload (`texturing/pm2_head_upload.glb`, HeadUV).
3. **Clean** (`clean_pm2.py`): MM9 height, the figure's left half mirrored, parts labelled; the head stays (no head graft); Meshy's
   eyeball cups, lip strips and the neck lacing piece go (paint). `face_fix.py`: the mouth pocket closed, lids and mouth Taubin-smoothed,
   midline sheets made manifold.
4. **Rest and weights** (`fit_pm2.py` + `fit_pm2.json`, `scripts/step_b.sh`: `rig_pm2.py`, `graft_hands.py` + `graft_pm2.json`,
   `helpers_pm2.py`), then `carry_uv.py` onto the frozen UVs and `sleeve_inner.py`. Weight rules that came from defects: the bell
   sleeve's inner wall and the whole cuff past the torso's width wholly on the arm (the stretched hanging triangles in Fidget and
   AttackMelee), Meshy's hand piece split Forearm/Hand at the wrist (its forearm stub inside the sleeve turned with the hand and showed
   as black shards through the sleeve), hair Head above the ears then Neck/Spine3 so the long hair follows the back.
5. **UVs** `uv_pm2.py`: **never re-run** (the three paints belong to `work/uv_v1.blend`).
6. **Paint** (`compose_pm2.py`, gentle grade, `tone_pm2.py`, `head_seam.py`, `fix_net_pm2.py` (r4, see "Ear net"; delete
   `textures/pm2_head_*_tone_prenet.png` after head_seam.py rewrites the tone images), `finish_tex.py`): never-seen texels Meshy painted
   black take their cloth or skin (sleeve inner wall, hidden tunic flank, the hands' stub); the mirror-midline UV seam on the forehead
   (a pale vertical line on both heads) takes its 3D neighbours' colour (`texel_pos.py` positions).
7. **Tiers** (`tiers_fit_pm2.py`, `tiers_pm2.py`): torso mask R tunic, G sleeves (armhole plane through the shoulder joint, so the edge
   is smooth on top of the shoulder), B collar braid, A cuff braid (by paint); tier B's target per region = PEASANTM2B's colour at the
   same luminance quantile of the same MM9 skin region, with our shading (tunic 197/169/131 against MM9 193/165/128, sleeves
   103/60/28 against 93/54/24); braids flattened (B's collar is plain cream, its cuffs plain brown). Head: per-tier images.
8. **Runtime** `scripts/rebuild.sh [--install]` (IN = `uv_v3.blend`): `finish_pm2.py` (skirt lining and cap, bell-cuff lining, a
   two-sided cuff hem, hair lining, trousers narrowed under the hem), `export_pm2.py`, `clips_mm9.py` (soft joint-offset line),
   `arm_const.py` (4 deg per shoulder, every clip but AttackMelee), `hand_rest.py` (`hand_rest_pm2.txt`), `half_keys.py`,
   `skirt_keys.py`, prepare, LODs, shadow fix, tiers, material extras, `floor_fix.py` (`floor_ops.txt`), winding fix and check.
   `viewer_tiers.py` + `make_viewer_manifest.py` for the viewer, `gates.sh` for the numbers. The r4 build ran
   `IN=uv_v3.blend scripts/rebuild.sh` (the script's default `uv_v2.blend` is stale; `work/token` holds the current lease).

## Ear net (r4, 2026-11-02)
Ear sweep (`claude_shared/mm9_overview/ear_sweep_20261102.png`, rows 9-10): a white net of thin crossing strands on the skin
beside and below both ears, strong on pm2_b, weaker on pm2_a. **Cause**: the paid head-only paints themselves
(`meshy/pm2_retex_head_{a,b}/`, unchanged by compose / head_seam / finish_tex): tier B (clean-shaven) got a net patch in front of
each ear, a strip down behind the jaw and strands on the ear rim; tier A's white beard thins into the same net in the sideburn.
**Fix** (`scripts/fix_net_pm2.py`, between head_seam.py and finish_tex.py, reads `*_tone_prenet.png` backups): on the face shell
only (the hair shell is another part, untouched) inside the ear zone: tier B: thin bright strands whose underlying colour is skin
take the strand-free skin around them, then small leftover white/grey islands at the hair edge and the ear rim (< 120 texels)
take the skin around them; tier A: every bright thin strand in the sideburn (above z 0.725, beside |x| 0.06, faded over 12 mm)
outside the dense beard (white density, opened) takes the non-white skin around it. Tier A's beard now ends at the jaw: no
sideburn (the head master had a full sideburn; densifying the net into a solid sideburn left a pink fog with the net still
visible, and removing the net below the jaw too cut the beard into a hook). The jaw beard keeps Meshy's crossing-strand texture at
its back edge in close-ups. Only `pm2_head_a_final` and `pm2_head_b_final` changed (`glb_diff.py` vs r3: 0.000 mm in every clip,
all other images same). Rollback `work/installed_preear.glb` (= the r3 install); viewer GLBs before: `work/viewer_pm2_{a,b}_preear.glb`.
Sheet `review/sheet_ear_before_after.png` (both tiers, before r3 / after r4: ear close-ups both sides, both profiles, both 3/4
backs, both under-jaw views, party view from 22 deg).
Regression after the last ear-sweep install (2026-11-02, `review/regression_actors_earsweep.log`): `--world mm9 actors` passed 192,
failed 1 (the known `out05_event_clearance_completes_from_monster_killed_hook` "could not load gameplay data");
`mm9_actor_models_build_every_binding` **PASS**.

## Checks
Final build installed 2026-11-01 (sha256 prefix in `creature_3d_progress.json`); r4 (ear net, head colour images only) installed
2026-11-02, sha256 prefix fc3e623f4d1d. Gates on r3 (`review/gates3/`); the installed build differs
from r3 only in the floor pass of Cower and Bow (root translation: `--ground-loop`, as Annud; Cower floated before).

| Gate | Result |
|---|---|
| `arm_hand_gate.py --outer-only --exact`, 48 fps | hands 0 frames over 1 cm in Standing, Walking, Running, AttackMelee, Hit, Death, Dead, Cower, Conv3, Bow (R 0.7 cm); Talk L 1.1 cm on 1 frame; **fails: Fidget R 5.3 cm, 15 frames** (MM9's fidget4 rubs the forehead: fingers into the hair and brow), **Conv1 L 6.0 cm (gate cap), 63 frames** (MM9's hand on the belly, see below). "Forearm" 2-5.8 cm in most clips is the bell sleeve (all forearm-weighted) against the tunic: cloth on cloth, as Annud's wide sleeves |
| Finger stretch | p99 at most 1.38, max 2.8 (Fidget L) |
| `jitter_gate.py` | **0 fails** against MM9's untouched clips with the same half-joint helper keys (`work/pm2_ref_h.glb`). Against the clips without helper keys (`gates2`) AttackMelee read 2.7 mm/f2 shoulder skin with 0.0 deg/f arm excess: the helpers, not motion |
| `collapse_gate.py` | Standing 694 face-frames (torso 9, groin 2), Walking 99, Running 493; elbows/knees/hips/ankles at most 1-2 (Cower ankle 4); neck/head counts in Bow 70/68 and Cower 20/46 are the long hair folding on the back when the head bows, mostly unseen (`review/gates3/collapse.txt`) |
| `skirt_gate.py` | 0 frames in Standing, Walking, Fidget, Talk, Conv1, Conv3; Running 4/50 (7.1 cm), Hit 2/50, AttackMelee 1/66, Death 10/71, Bow 11/146 (10.8 cm), Dead 49/49 (8.3 cm): the corpse's skirt back is pressed between body and floor (top view clean, `review/dead_sheet.png`) |
| `orient_gate.py` | head mean 0.0-2.2 deg (Hit 2.2, max 13 at MM9's snap), feet up vector mean under 2.4 deg; foot forward constant 1.3-1.4 deg (rest turn) |
| `bone_length_audit.py` | 0 stretching of 12 (raw MM9: 2 of 12, its own sliding thighs) |
| `detached_parts_audit.py` (24 fps) | **0 detached**, 23 components |
| `flat_shading_check.py` | limbs 0.00, torso 0.01, head 0.01 |
| `check_winding.py` | 0 inverted closed parts |
| `texture_quality.py` | limbs atlas 59.0 %, spread 1.54 (hands 1.5x dense by design), fragments 0.0 %, stretch 1.26; **torso 54.9 %** (0.1 under 55; spread reads 1e12 because the linings sit on one dark texel on purpose), fragments 2.2 %, stretch 1.11; head 60.3 %, spread 1.13, fragments 0.0 %, stretch 1.12 |
| `floor_audit.py --world mm9` | `MM9 44 Commoner`, `MM9 50 Commoner`: ok, stand 0, walk -1.3..+0.7, living -1.3, dead 0 |
| Regression `mm9_actor_models_build_every_binding` | **PASS**, 170 descriptors on 70 models, 0 failed (first install: full actors suite, every case PASS until I stopped it to reinstall; final install: `OPENYAMM_REGRESSION_FILTER=mm9_`, 4 of 4 PASS, `review/regression_actors.txt`) |
| Ear net (r4) | `review/sheet_ear_before_after.png`: tier B no net from any view; tier A sideburn net gone, beard kept on the jaw; see "Ear net" |
| `run_creature_review.py check` | 26 switches (2 tiers x 13 clips), 0 failed, 0 console errors (viewer r4-20261102; r3-20261101 before) |

## Not zero, with why

- **Conv1 L hand on the belly (6.0 cm, 63 frames):** MM9's conv1 lays the hand on the heart, then on the belly; our tunic is far
  deeper than MM9's thin body there (hand_rest's cast asks 13.8 cm). Uncapped push: 1.7 cm but upper arm 4.0 deg/f over MM9 (jitter
  fail); 8 cm cap: 4.4 cm and 1.9 deg/f (fail); 3 cm cap: 6.0 cm, jitter pass (kept). A forward shoulder bump (`arm_out.py` 10-16
  deg) changed nothing (the contacts sit at the window edges). Conv1 is played only by Wilam.scr (one placement).
- **Fidget R (5.3 cm, 15 frames):** fidget4's hand rubs the forehead; the fingers enter the long hair and brow. MM9's own gesture.
- **Arm constant:** 4 deg abduction per shoulder on every clip but AttackMelee (MM9's stand lowers the arms below our A-pose and the
  bell sleeves met the tunic flank); on AttackMelee it scaled the fast swing over the jitter limit, so that clip keeps MM9's arm.
- **Cuff rim:** a hairline of the sleeve rim's back can show from inside the bell at grazing angles (the lining sits 3 mm in).

## Deviations and open points

- **Head per tier:** the body is one shared set with ramps; the head set has its own colour and normal image per tier, because the two
  skins are two different men (A: white beard, grin, white hair; B: clean-shaven, more lined, ash-grey hair). Same as the accepted
  Nobleman/Ebora deviation, limited to the head.
- **Tier B pendant:** PEASANTM2B's silver pendant is not modelled (the tunic is a ramp of A's paint); B's collar is A's braid turned
  plain cream, its cuffs A's braid turned dark brown, so a faint braid relief stays in both.
- **Mouth closed:** MM9 grins with teeth; the masters asked for closed lips (no jaw bone, no clip opens the mouth; Meshy's mouth
  pocket was closed by `face_fix.py`). The smile is paint.
- **Belt strap end** hangs on both tiers (A's design; MM9's B skin has the buckle only).
- **PeasantM2d (rows 24, 26, skins C/D)** is another body, not built.
- **Map placement:** the rebuilt maps place these townsfolk with the legacy stand-ins (359 / 367) through the transcoder; the switch to
  `MM9 44/50 Commoner` for every townsfolk row is the orchestrator's after the batch (brief, "Lessons from wave 1"). Not done here.
- Rest pose is our A-pose, not MM9's T-pose; MM9's local rotations give MM9's world rotations (`orient_gate.py`).

## Sheets (viewer shots unless noted)

`review/sheet_ear_before_after.png` (r4), `review/sheet_mm9_vs_ours.png` (MM9 = Blender renders with their own light), `review/sheet_tiers.png`, `review/sheet_heads.png` (face
close-ups, both tiers, front / quarter / profile), `review/sheet_details.png` (arms, skirt in Walking, feet), `review/sheet_hands.png`,
`review/strips_1.png`, `review/strips_2.png` (every clip, four times, tier A). Diagnosis (Blender): `review/check*.png`,
`review/bf*.png` (backfaces red), `review/dead_sheet.png`, `review/sheet_faces_v1.png` (before the forehead seam fix).

## Not checked

In game (no map places the new descriptors yet; the switch is the orchestrator's); motion at normal speed by eye (strips and gates
only, no playback recordings watched); LOD1-3 and shadow meshes by eye; tier B clip strips (tier A only; same mesh and motion); indoor
light, fog, night; sounds and footsteps; Android cook; whether both tiers' head images upload when one tier is on a map.

User artistic acceptance: not recorded.


**LOD0 reduced post-install on 2026-11-04 by `level_generation/creatures/mm9_peasantm2_reduce_claude/`** (ledger: `level_generation/creatures/REDUCTION_LEDGER.md`, "MM9 reduction"). A rebuild from this project must re-run that reduction, or it silently restores the heavier mesh. Rollback source: `level_generation/creatures/mm9_peasantm2_reduce_claude/before/`.

## Seated and work clips for RUDEProps (2026-11-07)
MM9's posed townsfolk (RUDEProps: the Sturmford innkeeper, Ludwig, Tryggva, Halfdan, Ercc, the drinkers; The Arena's
spectators) loop clips from MM9's PeasantSeated.abc and PeasantWork.abc libraries. Those clips are grafted onto the
**installed** `mm9_peasantm2.glb` (meshes, LODs, reduction, variants and the old clips byte-identical, `graft_byte_check.py` OK),
not rebuilt, so the 2026-11-04 LOD0 reduction stays.
- Sources: `convert_abc_model.py --scale 0.0256` of both libraries (system python + gltf venv: `../mm9_peasantm2_claude/scripts/py_yaml_gltf.sh`),
  `mirror_glb.py`, `reparent_skirt.py` -> `../mm9_peasantm2_claude/source/true/peasant{seated,work}_src.glb`. The seated library
  lacks Bone15/Bone23 (second segments of two skirt hinges): they follow their first segment.
- Chain: `clips_mm9.py` with `scripts/roles_seated.json` on the project body, `arm_const.py` (4 deg, as every clip),
  `half_keys.py`, `skirt_keys.py` (front flaps swing 44-53 deg over the thighs), `claude_shared/graft_clips.py` onto the
  installed source, `check_winding.py` 0, `tools/install_model.py`; `claude_shared/bind_script_clips.py` (role = clip name).
  Floor (`claude_shared/floor/floor_fix.py`, after the graft): MM9's seated library carries the feet 25.4 cm above the
  model origin (MM9 drops these props with MoveToFloor), so every chained seated clip moves by ONE amount, the offset
  that grounds `sitting`'s first key (`--seat-like sitting <clip>`, -25.43 cm; list `sitting` last or it measures 0):
  feet on the floor, Ercc's set 0.7 cm up, no pop between sitting, listen, conv_seated, ercc*, ludwig_*. Seated hip
  joint 0.59 m (seat about 0.48 m). `innkeeper2` `--raise-uniform` +1.07 cm. **`sitting2` keeps MM9's origin** (the
  bar-stool pose: feet 26.9 cm above the origin, pelvis 0.93 m), so its placement goes at the DAT position without a
  floor drop, as MM9 places that prop (no MoveToFloor).
- Clips (s): sitting 1.37, sitting2 1.70, listen 6.70, ludwig_writing 9.00, innkeeper2 2.20, ercc_out 0.10 (loops);
  conv_seated 18.13, ercc01a 21.70, ercc01b 21.67, ercc01c 22.67, ercc02 8.70, ludwig_lookup 4.03 (one-shots, no ease:
  ercc01a-c start and end in the sitting pose; ercc02 ends slumped and ercc_out holds that last pose).
- Gates (`review/seated/`): arm/hand 0 frames over 1 cm except ercc01b (L 5.1 cm, 22 frames; R 3.3 cm, 3) and ercc01c
  (L up to 6 cm on the M2 body): MM9's drinking gesture brings the hand to the mouth/chest. Skirt gate: the thighs pass
  through the side panels in every seated clip (about 19.6 cm, the hinge ring cannot drape a horizontal thigh); front and
  back read correctly (`review/seated/clay_skirt.png`). Strips: `clay_a.png`, `clay_b.png`, `clay_ercc.png` (M2 body).
- Rollback: `work/seated/before/mm9_peasantm2.glb` (the source before the graft).

## MM9 sockets (2026-11-10)

The installed model carries MM9's attach points as `Socket_<name>` nodes for held items (scene `held_items`, MM9's AttachProp), added after this project's install by [`mm9_held_items_claude/scripts/add_sockets.py`](../../props/mm9_held_items_claude/scripts/add_sockets.py) (`Socket_Cup`, for Ercc's cup). A rebuild installed from here drops them: run that script again and install its export (`tools/install_model.py --world mm9`). Since 2026-11-11 the held items project's `grip_clips.py` also closes the right hand round
Ercc's cup in ercc01a-c, ercc02 and ercc_out, moves `Socket_Cup` into that fist and adds the still clip `ercc_sitting`
(Ercc.ABC's own sitting pose, cup at the chest); a rebuild must run `add_sockets.py`, then `grip_clips.py`.
