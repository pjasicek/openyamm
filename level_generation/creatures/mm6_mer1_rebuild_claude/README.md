# MM6 Merchant (mer1) rebuild on MM9 skeletons — 2026-11-11 (stream `rebuild`, audit mm678 2026-11-11)

Merchant A / B / C, monsters 577/578/579 (palettes 252/253/770). Replaces the Codex round-3 install on QA hold
(`../mm6_mer1_codex/` + `../mm6_mer1_reduce_claude/` + gait package h05): Meshy auto-rig with odd hands, club grip gaps up
to 75 mm, club/body penetration 64 mm, coat-hem findings, hands atlas 13.9 %, bland attack (motion ratio 0.42).
Route: the approved MM9 humanoid "Yrsa route" (MM9 skeleton, names and rest rotations kept, joints translated, MM9 clips,
MPFB five-finger hands, separate head set), with the Thief worker's chain (`../mm6_thf_rebuild_claude/`) as the script base.

| Item | Value |
|---|---|
| Installed | `assets_source/worlds/mm6/models/mm6_mer1.glb` (sha256 e51ec4fb1e4d…) and `mm6_mer1_club.glb` (4234a7af5d41…, re-seated on the new `Club` joint), `tools/install_model.py --world mm6`, 2026-11-11 |
| Revert | `mkdir -p /tmp/mer1_revert && cp work/before_rebuild/mm6_mer1.glb work/before_rebuild/mm6_mer1_club.glb /tmp/mer1_revert/ && python3 tools/install_model.py /tmp/mer1_revert/mm6_mer1.glb --world mm6 && python3 tools/install_model.py /tmp/mer1_revert/mm6_mer1_club.glb --world mm6`, then put the Merchant section of `work/before_rebuild/actors_mer1_entries.yml` back into `assets_dev/worlds/mm6/models/actors.yml` (whole file at claim: `work/before_rebuild/actors_full_at_claim.yml`) |
| Binding | `actors.yml` Merchant A/B/C (`scripts/bind_actors.py 101.55 0.321`, `WALK_STRIDE=1.7251 RUN_STRIDE=2.0628`): scale 101.55 (native stand 177.1 units / 1.744 m Standing height; old 103.94 with z_offset, dropped), walking `Walk2`, run `Jog`, look `Bip01 Neck, Bip01 Head`, upper body `Bip01 Spine1`, impact 0.321 s (melee, ranged slot and cast all play Attack), club attachment on node `Club` |
| Geometry | the Codex round-2 Smart Topology parts (`../mm6_mer1_codex/work/round2/raw_parts.blend`, made from the gated round-2 HD masters, 15,916 tris) decimated per part (`clean_mer.py`), scaled x1.035 to MM9's shoulder height; no new geometry credits. Masters copied to `references_hd/` (round 2) and `references_head/` |
| Skeleton | MM9 HIGHWAYMAN / FIGHTERBASE (32 nodes; rest frames turned onto our limbs, `fit_mer.py` from `fit_thf.py`; the centre bones Pelvis..Head take NOBLEMAN's `stand` frame 0, see "Donors") + 30 MPFB finger bones + 10 half-joint helpers + 64 robe chain bones (16 columns x 4) + `Club` = 137 joints |
| Body clips (MM9 NOBLEMAN, `source/nb_hw.glb`) | Standing `stand`, Walking `walk`, Running `run`, Fidget `fidget1`, Hit `wince1`, Death `die1`, Dead; Walk2 = `walk` legs x1.3, rate 1.2 (game walk); Jog = `run` legs x0.9, rate 1.0 (game run) |
| Attack (MM9 FIGHTERBASE / HIGHWAYMAN) | `Hattack1` x1.2 = 0.667 s with the swing amplified (`clips_mm9.py` role option `gain`: Spine, Pelvis, R Clavicle/UpperArm/Forearm x1.3); club head fastest at 0.321 s (`blow_time.py`) = impact |
| Hands | MPFB male hands (weight 0.7) grafted at the cuffs (`graft_hands.py`, frame `rig`, palm toward the thigh as MM9's mitten), 15 finger bones per side, relaxed MPFB curl in every clip; in the Attack the right fist closes round the club handle (`finish_mer.py` per-finger solve, thumb over; `finger_keys_mer.py` eases in 0.12 s, out 0.16 s) |
| Club | the approved club GLB (unchanged images and LODs, 1,122 / 290 / 252 / 200 tris) re-seated on the body's `Club` joint (`place_club.py`). As the native merchant (mer1sta*, mer1wa*) it hangs head down at his right hip, behind the hand's reach, and is drawn in the attack (mer1atb..f): `Club` rides the robe column `Robe_06_0`, turned with that column's chord (`robe_keys.py`), and `club_keys.py` moves it into the fist and back with the fist's weight, swinging out round the hip on the way |
| Robe | the knee-length tunic skirt on a closed ring of 16 x 4 chain bones (`rig_mer.py`), keyed per frame by `robe_keys.py` (the Thief's `cloak_keys.py` on a closed ring rooted on Bip01 Spine: leg and heel capsules, lateral spacing limits, no tears; the other columns pushed off the club) |
| Textures | body 2K colour + 1K normal/ORM (uv_atlas, atlas 57.5 %, fragments 0.0 %, stretch p90 1.08, density p50 1,147 px/m), head set 1K (face, neck, eyes, cap; atlas 69.5 %, fragments 0.1 %, stretch 1.06); 4K Meshy paints downsampled once, gentle grade; hands toned to the face's skin; paint fixes by texel position (`compose_mer.py`): the hair fringe Meshy painted under the cap rim, the cap rim's own fringe paint, blue specks on the face, brown streaks on the skirt; tiers = the installed `tunic` region + ramps (palettes 252/253/770), range refitted |
| Meshy credits | 20 of 85 (body retexture 4K 10, head retexture 4K 10; backup account) |
| Triangles LOD0/1/2/3 | 10,584 / 5,291 / 1,902 / 634 (installed 7,924 / 3,959 / 1,423 / 472); LOD0: hands 2 x 800, head + eyes + cap 3,073, robe 1,460 |

## Donors

- **Body clips from NOBLEMAN, attack from FIGHTERBASE, skeleton HIGHWAYMAN/FIGHTERBASE.** NOBLEMAN and FIGHTERBASE share the Bip01 core names
  (Pelvis, Spine..Spine3, Neck, Head, Clavicle, UpperArm, Forearm, Hand, Thigh, Calf, Foot, Toe0), every bone with the biped axis convention
  (-X along the bone), so local rotations carry over. Two differences, handled in `convert_nb.py`: NOBLEMAN hangs the thighs from Bip01 Spine
  (FIGHTERBASE from the Pelvis: thigh keys become Spine_local x Thigh_local on the union of the key times, world poses match the source within
  0.4 mm), and the finger chains differ (dropped; our MPFB fingers are keyed separately). FIGHTERBASE carries the weapon joint and the club
  blows, so it is the skeleton; NOBLEMAN's civilian stand/walk/run/fidget/wince/die are the body. PEASANTMALE was not used: it has no Pelvis.
- NOBLEMAN's standing spine, neck and head differ from the HIGHWAYMAN bind by up to 18 deg (the merchant leaned back and looked up), so the
  centre bones' rest frames are NOBLEMAN's `stand` frame 0 (`fit_mer.py`).
- **Attack choice** (motion ratio vs MM9 biped median, `work/atk/`): Hattack2 (overhead chop) 0.72-0.75, x1.45 gain 0.87; Hattack3 0.88, with
  gain the arm deformation exceeds 12 %; Hattack1 x1.2 0.83, with gain 1.3 **0.90** (arm 10.9 % beyond Standing). The club is a separate
  attachment, so the audit's peak speed sees only the fist (the club head peaks at 23 m/s).

## Chain (`scripts/`)
1. `rebuild_mesh.sh`: `clean_mer.py` -> `fit_mer.py` (`fit_mer.json`, `source/nb_hw.glb`) -> `rig_mer.py` (weights, robe chains,
   `work/rig_v1.blend.robe.json`) -> `graft_hands.py graft_mer.json` (`BLENDER_USER_EXTENSIONS=$HOME/.config/blender/5.2/extensions`)
   -> `hands_fix.py` -> `helpers_thf.py` -> `prune_hidden.py`. `convert_nb.py` writes `source/nb_hw.glb` (gltf venv).
2. `uv_mer.py` (frozen: the paints belong to `work/uv_v1.blend`) -> Meshy `requests/retexture_{body,head}.json` -> `bake_ao_thf.py`
   -> `finish_mer.py` (fist, grip, belt placement, `Club` joint; `work/club_place.json`) -> `slim_legs.py work/final_v1.blend work/final_v1.blend`
   (the hidden thigh filler under the tunic pulled to 8.5 cm radius) -> `head_fix.py work/final_v1.blend work/final_v1.blend` (skin edge under the cap lifted into it, eyeballs 7 % smaller) -> `dump_uv.py work/final_v1.blend work/final_v1_uv.npz`
   -> `compose_mer.py --stage raw`, `--stage final`.
3. `scripts/build_runtime.sh [--install]`: `smooth_band.py` (neck) -> `export_mer.py` -> `clips.sh` (`clips_mm9.py roles_mer.json`,
   `finger_keys_mer.py`, `half_keys.py`, `foot_clear.py`, `robe_keys.py`, `club_keys.py`) -> prepare, LODs, shadow fix, `region_variants.py`,
   `floor_fix.py`, winding, `place_club.py` [-> install both GLBs]. `FROM_CLIPS=1` reuses the textured export.
4. `gates.sh`, `club_gate.py`, `blow_time.py`, viewer (`viewer_mer.py export/mm6_mer1.glb export/mm6_mer1_club.glb rebuild`,
   `viewer_manifest.py rebuild <rev>`), `sheet_shots.sh`, `ingame.sh`, binding `scripts/bind_actors.py` (repo root, env `WALK_STRIDE RUN_STRIDE`).

## Checks (final build, installed)
| Check | Result |
|---|---|
| Attack motion ratio vs MM9 biped median | 0.42 -> **0.93** (amp p90 0.339, body share 0.933, peak speed 4.82, torso turn 67 deg, 0.667 s) |
| Worst region beyond Standing (audit roles) | Fidget arm 10.8 % (installed: Jog leg 14.1 %); cloth worst Death 8.8 %, Running 4.9 %, Jog 3.9 %, Walk2 1.0 % |
| Hand inside the body (motion_audit) | 0 % in every bound role (installed: Jog 6.0 %) |
| `arm_hand_gate.py --outer-only --exact` (`review/gates/arm_hand.txt`) | <= 1.3 cm in every clip but Attack R hand 3.9 cm at frame 29 (2 frames > 1 cm, the fist coming back past the belly in the ease-out); 17 finger chains per hand; finger stretch <= 1.56 |
| `club_gate.py` (`review/gates/club.txt`) | grip gaps thumb 3 / index 3 / middle 4 / ring 4 / pinky 8 mm, finger skin inside the handle <= 3 mm (Codex install: up to 75 mm); club against the body 0-0.5 cm in every clip but Attack 4.4 cm at the blow (0.31 s): the handle behind the fist against the heel of the hand / wrist skin while the club lines up with the forearm (Codex install: 64 mm in Death) |
| `jitter_gate.py` vs the raw MM9 clips | 1 marginal fail: Attack L shoulder skin 2.35 mm/f2 against 2.0 (the amplified torso swing) |
| gait_gate / gait_audit / floor_audit | **PASSED** (wander Walk2 x0.91, chase Jog x1.34, MAW the same) / 0 flagged / 0 problems (stand 0, walk -1.8..+1.1, living -1.8, dead 0) |
| texture_quality (`audit_after/texq.txt`) | body Merchant_A 2048: atlas **57.5 %** (installed clothing 26.8 %, hands 13.9 %), fragments 0.0 % (5.4 / 11.8), stretch p90 1.19 (2.43), density p50 1,149 px/m (849); head MerchantHead_A 1024: atlas **69.5 %** (57.0 %), fragments 0.1 % (4.9), stretch 1.15; materials 3 -> 2 |
| winding, regression, viewer | 0 inverted (body and club); `mm6_mm7_mm8_actor_models_build_every_binding` PASS (647 descriptors, 0 failed), `mm6_merchant_actor_model_tiers_share_the_native_height` PASS; `run_creature_review.py check` 30 switches, 0 console errors |
| Before/after | `review/sheet_before_after.png` (stand front/quarter/back, walk, jog, attack x2, hit, dead; every tier), `review/sheet_before_after_close.png` (face front and 3/4, both hands in Standing); `review/attack_seq.png` (the blow), `review/grip_tilt_0.png` (fist on the handle), `review/skirt_check.png` |
| In game | `review/ingame/frozen_sheet.png` (three tiers frozen: New Sorpigal test spot, Agar's Laboratory), `review/ingame/out_sheet.png`, `in_sheet.png` (hostile merchants draw and swing the club at an immortal party, one killed: death, loot) |

## Deviations / open
- Skeleton is HIGHWAYMAN/FIGHTERBASE with NOBLEMAN's body clips (see Donors), not a NOBLEMAN skeleton: FIGHTERBASE carries the club blows and the
  weapon joint; the thigh parent difference is converted exactly.
- The club hangs from the belt and is drawn only in the attack (the native merchant's sprites), unlike the installed model, which held it in
  every clip. It slides from the hip into the fist over 0.12 s (out round the hip, not through it) and back over 0.16 s.
- Attack amplified (`gain` 1.3 on the spine, pelvis and right arm) to reach ratio 0.93; MM9's own Hattack1 scores 0.83 on this body.
- The handle behind the fist meets the wrist skin at the blow (4.4 cm by the gate's surface test); a diagonal grip (+-20 deg) was tried:
  +20 left the pinky off the handle, -20 opened the fist; kept straight.
- The hidden thighs under the tunic were slimmed (`slim_legs.py`, positions only): they were a skirt-wide filler that showed through the robe.
- Paint fixes by texel position (fringe, specks, skirt streaks, smooth weave filled with a tiled weave patch); a tiny dark sliver remains at
  the corner of the right eye in face close-ups; eyebrows are heavy in the Meshy paint.
- One marginal jitter fail (above); Attack ease-out brings the right fist past the belly for two frames.
- Not checked: LOD1-3 by eye beyond the in-game shots; Android.

## Far LODs repaired (2026-11-12, lod-step1)

LOD2/LOD3 and their shadows rebuilt by `lod_repair_claude/scripts/repair.py` from the installed GLB: ladder step
25/12 %, own 512/256 px far maps by UV correspondence; LOD0, LOD1, clips, materials and tiers unchanged
(`verify_far_only.py` OK), winding 0, every_binding PASS. Numbers and captures: `../lod_repair_claude/README.md`
("MM6 rebuilds' far LODs"). Revert: `tools/install_model.py level_generation/creatures/mm6_mer1_rebuild_claude/work/before_lodrepair/mm6_mer1.glb --world mm6`.
