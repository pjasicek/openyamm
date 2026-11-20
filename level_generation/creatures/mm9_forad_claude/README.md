# MM9 Forad Darre (mm9_forad) — 3D actor, 2026-10-29

## Clips MM9's scripts play (2026-10-31, run2-clips-groupD) - current

User decision: Forad carries only the clips his MM9 scripts and dialogue play. forad.scr (`playanim bow`, installed) and
basemelee.scr (row 252's default, Afterworld) both include BaseRun.inc `LoopAnim Cower`; ARG_Forad.scr (Thronheim's Argument
scene) loops Sit and plays Agree, Applause, Sc2_Forad6 (trigger Speak6) and Sc2_forad26 (Speak20), his own FORADDARRE.abc clips.
RUDE rows name no animation. Added and bound: cower Cower, sit Sit, agree Agree, applause Applause, argument_speak6
ArgumentSpeak6, argument_speak20 ArgumentSpeak20. Left out, not played by this NPC: ForadDarre (own), run2, lean, leanfidget,
bardrink, barfig, barstand, bless, pray, conv, conv2-5, fidget2-5, fidget8, hattack2, wince2, backpedal, backpedalrun,
cowerstart, cowerend, Sc07_shot1, play_death, play_getup, Njam_*.
`v2/scripts/extra_clips.sh` (roles `v2/scripts/roles_forad_extra.json` with the own source `source/mm9/forad.glb`,
`v2/scripts/hand_rest_forad_extra.txt`, `scripts/floor_ops_extra.txt`) grafts them onto the installed export; byte check OK,
15.93 -> 17.57 MB. The seated clips stand on their feet (MM9's raw keys float them 27 cm); the seat is the map's. Joint angles
match MM9's sit within 6 deg, but our longer shins make it read as perched, and the right foot sits 7 cm above the left.
Gates (`v2/review/clips_restore_D/`): hands clear except Applause (the clapping hands meet, 2.2 cm), Sc2_Forad6 R 7.6 cm cleared
by hand_rest; forearms up to 2.4 cm; jitter 0 fails; floor 0; bones 0 stretching. Strips `strip_new_*.png`, `clay_new.png` read.
Not looked at in the viewer or in game.
Edits: `v2/scripts/clips_mm9.py` gained opt-in `soft_offsets` and `hold` (accepted clips rebuild byte for byte).

## Bracers lined (2026-10-30) - current

After Yrsa's sleeve defect. Forad has bare arms, so no forearm was needed, but his bracers are single-sided rings wider
than the wrist, and the background showed through their back faces beside the hand. `v2/scripts/sleeve_lining.py
forearm=0 near=0.09 dark_pct=10` (`v2/work/texpass_head.blend` -> `sleeves_v2.blend`) lines only the faces within 9 cm
of the wrist. No clip change: every clip 0.000 mm against the texture-pass GLB (`glb_diff.py`). Sheets
`v2/review/sleeves_compare.png`, `v2/review/viewer_sleeves_sheet.png`. `PYGLTF_PYTHON` is
`claude_shared/gltf_venv/bin/python`, by that path (setup in `../mm9_yrsa_claude/README.md`). Rebuild:
`HEADTEX=forad_tp BODYTEX=forad_tp BLEND=v2/work/sleeves_v2.blend v2/scripts/build_runtime_v2.sh forad Forad
v2/scripts/roles_forad_v3.json --install`. Meshy: 0 credits. `sleeve_gate.py` see-through worst px right sleeve front / above / below / 3/4: 115 / 123 / 153 / 84 -> 3 / 42 / 0 / 22 (left 45 / 25 / 85 / 52 -> 2 / 0 / 5 / 5); viewer `v3.4-cuffs-20261030`, 0 errors.

## Texture quality pass (2026-10-30) - current base

Coordinator request after `../claude_shared/TEXTURE_QUALITY_PASS.md` ranked Forad's body atlas sixth (26 %): sharper
textures only; mesh, rig, weights, clips, hands' skin and binding unchanged (v3.2 was approved as it looks and moves).
Same route as Annud's pass (`../mm9_annud_claude/README.md`, shared scripts):

- **Body**: `texpass_uv.py` on `v2/work/head_v3.blend` -> `v2/work/texpass_uv.blend` (head/hand faces in the upload at
  0.35x density); 4K retexture `v2/requests/retexture_texpass.json` -> `meshy/body_retexture_texpass/`; AO, compose ->
  `textures/forad_tp_*`; gentle grade. The new paint follows the HD master (abs and light chest hair, patterned
  bracers, crisp vest piping) but painted the arms darker than the approved paint (rendered upper arm 124/79/53
  against 145/88/55), which would leave a seam at the wrists against the head set's hands. `v2/scripts/match_skin.py`
  (shared; `uv_pairs.py` dumps the old and new UVs of every body face) resamples the approved graded colour onto the
  new layout and adds, inside the new skin class, a mask-normalised 40-texel blur of the difference: the tone follows
  the approved paint region by region (upper arm 143/86/52), the detail stays the new paint's.
- **Head**: `texpass_head_uv.py` -> `v2/work/texpass_head.blend`, 4K head retexture
  `v2/requests/head_retexture_texpass.json` -> `meshy/head_retexture_texpass/`, `compose_head_texpass.py` (hand texels
  kept byte for byte) -> `v2/textures/forad_tp_head_*`. Same face (scar, eyes, goatee, cheek 157/104/78 against
  158/111/88), sharper eyes and brows: `v2/review/texpass_head_closeups.png`.
- Rebuild: `HEADTEX=forad_tp BODYTEX=forad_tp BLEND=v2/work/texpass_head.blend v2/scripts/build_runtime_v2.sh forad
  Forad v2/scripts/roles_forad_v3.json --install` (hand_rest as before). Never re-run the UV scripts.

| `texture_quality.py`, LOD0 | Body before | Body after | Head set before | Head set after |
|---|---|---|---|---|
| Atlas use (2K) | 26.4 % | **53.5 %** | 30.6 % (head square 42 %) | 43.9 % (head square 63 %) |
| Equivalent square | 1,052 px | 1,498 px | 1,132 px | 1,356 px |
| Density p10 / p50 / p90 | 960 / 1,066 / 1,119 | **1,509 / 1,553 / 1,599** (+46 %) | 1,934 / 3,352 / 3,761 | 1,934 / 4,201 / 4,417 (+25 %) |
| Spread p90/p10 | 1.17 | 1.06 | 1.95 (hands half as dense, by design) | 2.28 |
| Islands / fragments | 404 / 4.6 % | 229 / 0.4 % | 405 / 7.8 % | 190 / 2.8 % |
| Stretch p90 | 1.38 | 1.09 | 1.44 | 1.24 |
| Meshy source | 2K | 4K on 55 % | 2K | 4K on 63 % |

Body atlas 53.5 %: just under the 55 % automatic charts usually reach (228 islands, many of them the 39 necklace
beads); accepted like the Magreeb's 54 %.

**Checks**: motion identical to the installed GLB (`glb_diff.py`: every clip 0.000 mm at 48 fps); LOD0 8,397 triangles
as before; winding 0 inverted; installed; viewer revision `v3.3-texpass-20261030`, `run_creature_review.py check` 10
clips, 0 errors; `arm_hand_gate.py --outer-only` hand and forearm depths identical, finger stretch within 0.04 (new
vertex split; `v2/review/arm_hand_gate_texpass_{before,after}.txt`); `jitter_gate.py` hand and arm values identical,
shoulder-skin p95 moves with the vertex split (10 -> 9 pre-existing fails); `detached_parts_audit.py` 0 detached before
and after; `mm9_actor_models_build_every_binding` (`--world mm9`): 49 descriptors on 20 models, 0 failed. Binding
unchanged. Sheets: `v2/review/texpass_compare.png`, `v2/review/texpass_head_closeups.png`. Before state:
`v2/work/before_texpass/`. **Meshy: 20 credits** (body and head retexture, 10 each, backup account).

New shared v2 scripts from this pass (identical in the three projects' `v2/scripts/`): `texpass_uv.py`, `texpass_head_uv.py`,
`bake_ao_texpass.py`, `compose_texpass.py`, `compose_head_texpass.py`, `uv_pairs.py` + `match_skin.py`, `texpass_shots.py`
(identical-camera stills), `part_views.py` (close-ups around joints, also see-through), `glb_diff.py` (what changed
between two runtime GLBs: images, meshes, clips, posed vertices).

## v3 (2026-10-30, after the user's review of v2) - current base (textures changed above)

User review of v2: "I can see the rectangles composing the model"; the face looked like "the new texture overlays the
older texture"; "We want the MM9 animations on the model, no? Why are we using Mixamo?". v3 returns to Annud's and
Yrsa's (approved) route: the MM9 skeleton and clips, grafted five-finger hands, the v2 head set. v2 below is superseded.

- **Faceted shading (cause)**: the v1 MM9-route body came from Meshy with flat faces (only the grafted hands, 16 % of
  the faces, were smooth: `use_smooth` in `work/head_v1.blend`, `step1.blend`, `rig_v5.blend`), and v2's own
  `export_runtime.py` exported them as they were, so glTF split every vertex (body: 12,289 vertices for 4,097
  triangles, 100 % flat; head 69 %). v3 exports through the shared `build_export_v2.py`, which shades smooth:
  0 % flat triangles in both primitives (`v2/scripts/shading_check.py`), hard edges only where UV seams split vertices.
- **Face**: one surface carrying only the head set (material map: the whole face, ears and scalp are `ForadHead`, the
  body material starts at the collar). The fighting layers were Meshy's separate eyeball cups (parts 6 and 11):
  they cross the lids and carry lid skin from the retexture, so jagged lid patches sat on the painted eyes. Dropped
  by `export_fix` in `v2/scripts/head_forad.json` (shared `build_export_v2.py`, as Annud); the head shell carries the
  painted eyes. The scar is in the Codex head reference (`v2/references_head/01_front.png`), not a body-texture
  leak. Head normal/ORM come from the same Meshy job on the same `HeadUV`, resampled identically (compose_headhand).
  A 5-edge hole in the back of the vest is filled too (`fill_body_holes`). Topology (`v2/review/head_topology_v2/v3
  .json`): small holes 1 -> 0, eyeball cups 2 -> 0, 0 flipped, 0 non-manifold.
- **Rig** (`v2/scripts/v3_rig.py`, `v3_rig_forad.json`; `work/head_v1.blend` -> `work/head_v3.blend`, report
  `work/v3_rig.json`): Forad's graft had run without `add_bones` (v2 rigged the fingers on its own rig), so the 15
  finger bones per side are added as for Annud and Yrsa (MPFB joints from `work/hands_v1.json`, MM9 mitten rest
  frames, frame error 0); knees moved to the leg-slice centre at Meshy's knee height (+10.5 / +10.1 cm up, 1.6 / 4.6
  cm forward; rest rotations and ankles unchanged) with Thigh/Calf weights re-split around the new knee (+/- 4 cm);
  chin: Head + Neck weight re-split by a plane through the bottom of the chin and the nape, so the chin and jaw are
  all Head (the MM9 skin blended Neck into the chin: v1's cut-looking chin); the neck blend below is MM9's.
- **Clips**: MM9 PeasantMale, as v1 (`v2/scripts/roles_forad_v3.json`): stand1, walk3, run, fidget1, conv1 (Talk), bow,
  hattack1 (impact 0.5 s), wince1, die1, with `finger_alias` driving the finger chains from the mitten curl.
- **v3.1 hand rest (2026-10-30, after review of v3: Talk's hand covered the face and "the hand is jiggling
  constantly")**. Cause: `arm_clear.py` solved every key on its own (an upper-arm turn of up to 40 deg per key), which
  lifted MM9's hand-on-heart to the face and changed from key to key. Replaced for Forad by `hand_rest.py`
  (`v2/scripts/hand_rest_forad.txt`, run by `build_runtime_v2.sh` instead of arm_clear): MM9's hand is cast
  horizontally against the outer trunk surface and pushed out of it by a smooth curve (running maximum +/- 0.16 s,
  Gaussian 0.08 s, so it rises and falls over ~0.5 s), reached by a two-bone solve with the palm keeping MM9's world
  rotation; Talk's right hand (MM9 `L`) also lowers 40 deg onto the chest (hand on heart), the left hand comes out
  of the hip, and Bow's hand on heart (MM9 `R`, buried in the chest before) comes out of the chest. Bow's motion is
  otherwise MM9's.
- **v3.2 shoulders (2026-10-30, user: "frames 97-107 weird slight movement in the right shoulder, 179-190 strange in
  left shoulder")**. Cause (`jitter_gate.py` shoulder chain, per frame against MM9's untouched Talk): the push was
  smoothed over time, so it kept fading while MM9's arm was still (frames 95-110: MM9's upper arm turns 0.1-0.4
  deg/frame, v3.1 up to 6.4; frames 186-192 the left arm kept moving after MM9's stopped), and the old two-bone solve
  rebuilt the elbow pole from a nearly straight arm. Fix in `hand_rest.py`: the push curve is filtered over MM9's
  own wrist path (it changes only while MM9's wrist travels; plus a 0.07 s time Gaussian), and the solve bends the
  elbow only as far as the reach changes, then swings the whole arm about the shoulder. Upper-arm angular velocity
  in the reported windows: right 95-110 max 1.43 deg/f (MM9 1.26; v3.1 6.44), left 177-192 max 4.4 (MM9 4.18; v3.1
  5.36, and 1.74 deg/f after MM9 had stopped, now 0.36). Strips `v2/review/v3_shoulder_strips.png` (MM9, v3.1, v3.2
  at 48 fps, front and 3/4). The remaining per-frame excess is the reach onto the chest at frames 8-13 (upper arm
  up to 9 deg/f above MM9, one monotonic swing as the hand arrives, no reversal; the hand path is within 9 % of MM9's).
- **Jitter gate** (`jitter_gate.py`, `v2/review/jitter_gate.json`; before `jitter_gate_before.json`): at 48 fps the
  wrist's second difference and the hand's angular velocity against MM9's untouched clips; fail above 1.5 x and
  +2 mm / +2 deg of MM9's own maximum. Talk right hand before (v3 arm_clear): 72.4 mm/f2 and 23.8 deg/f against MM9
  43.9 / 17.6, FAIL; after: 47.5 / 17.7, pass. Bow 39.9 / 55.1 mm/f2 (MM9 38.4 / 53.9). Every clip passes.
- **Gate** (`v2/review/arm_hand_gate.txt`, 48 fps, every clip, `--outer-only`: the outer body surface, see
  `outer_surface.py`; the vest's standing two-layer lapel no longer reads as the inside of the body): hands clear
  except Talk 4.1 cm on 2 frames (13-14, the hand arriving at the chest), Bow 1.2-1.8 cm on 1-3 frames; finger
  stretch max 2.91. Normal-speed viewer playback (`review/playback/Talk-1.webm`) checked: the hand settles on the
  chest and stays there without shaking.
- **Beads**: 39 small necklace parts take the weights of the skin under them (`v3_rig.py` step 4); detached-parts
  audit on the installed GLB: 0 detached (one bead floated 5.6 mm in Fidget before).
- **Binding** (`actors.yml`, under the lock): Bip01 look/upper-body nodes, stride walk 1.05 / run 3.8 (measured,
  `scripts/stride.py`), impact 0.5. Regression `mm9_actor_models_build_every_binding` (`--world mm9`): 49
  descriptors on 20 models, 0 failed (v3.1 rerun: Forad and Annud build; 3 Dagrell failures from other work in
  progress). Viewer check 0 errors (`review/viewer/`, revision v3.2-20261030).
- Before/after (v2 vs v3.1): `v2/review/v3_face_compare.png` (bind, Talk 20/43, Walking 21: front, both profiles,
  3/4, eyes, mouth, neck) and `v2/review/v3_body_compare.png` (Standing, Talk 20/43, Bow 50/70, Walking 21: front,
  both sides, 3/4, both hands); Talk v3 (arm_clear) vs v3.1: `v2/review/v3_talk_compare.png` (Talk 12-175, with sides).
- Runtime: `v3_rig.py v2/scripts/v3_rig_forad.json` (Blender wrapper), then `BLEND=v2/work/head_v3.blend
  v2/scripts/build_runtime_v2.sh forad Forad v2/scripts/roles_forad_v3.json --install`; LOD0 8,397 triangles.
  No Meshy credits.

## v2 rework (2026-10-30, after the user's review) - superseded by v3

User review of v1: poor head texture, a cut-looking chin, four warped fingers and a spike thumb, and the right
arm buried in the torso in Talk and Bow (MM9's mitten rig and thin-body arm clips). v1 below is superseded.

- **Rig and clips: humanoid playbook route** (`v2/scripts/rebuild_forad.sh`, hvm/natm scripts): the v1 textured
  body (UVs and body texture kept) with grafted five-finger MPFB hands, Meshy auto-rig (5 credits) for the axial
  joints, shoulders, elbows, hips and knees (the MM9 knees sat 10-12 cm low), MPFB wrists, ring ankles; source-frame
  rig (52 bones + twist), frame error 0; finger chains on the MPFB joints, finger weights from MPFB's own.
  Clips (Mixamo, world-rotation retarget): Standing Standard Idle, Walking Standard Walk (stride 1.654 m), Running
  Standard Run (`run_fit.py`, stride 2.052 m), Fidget Standing Idle 03 Examine, Talk Talking, Bow Quick Formal Bow
  (yaw-only plant; spine flexion x1.8 for a courtly bow), AttackMelee Punching (impact 0.633 s), Hit Standing React
  Large From Front, Death Dying Backwards. Loose unarmed hands (60 % of the source curl).
- **Head**: Codex head turnaround (`v2/references_head/`, 4 views), Meshy head-only retexture (10 credits) on
  `HeadUV`; head = the skin weighted to Bip01 Head/Neck above z 0.615 (MM9 space) plus ponytail, tie and eyes; the
  seam sits at the vest collar and the necklace. The chin geometry was fine; v1's chin tearing came from the MM9
  weights and is gone on the new rig (Walking 21 front checked).
- **Gate** (`v2/review/arm_hand_gate.txt`): no hand or forearm vertex inside the body on any 48 fps frame of any
  clip; finger stretch max 1.80; floor audit ok. Renders `v2/review/clips_v2.png`, `v2/review/bow_v3.png`.
- In game (remade isle review root, minimized): `v2/review/ingame_sheet.png` (all three NPCs: idles, walk/run, a hostile Forad punching, Yrsa killed).
- Runtime: `v2/scripts/build_runtime_forad.sh --install`; LOD0 8,552 triangles, two materials (Forad, ForadHead; not
  merged: the 2K/1K maps cannot share one atlas layout). Binding updated (B_* bones, strides, impact 0.633).
- Meshy: 15 credits (auto-rig 5, head retexture 10).

Shared v2 scripts (identical in the three projects' `v2/scripts/`): `graft_hands.py` (posed MPFB/MakeHuman CC0
hands grafted at the bracer or sleeve: old skin past the cuff deleted by the class map, stub conformed inside the
cuff, MPFB weights kept), `head_split.py` (head faces + `HeadUV`, head upload), `bake_hands.py` +
`compose_headhand.py` (head + hands set: Meshy head retexture resampled into the lower-left 0.8 square, MakeHuman
hand skin graded to the character's own skin in the freed squares; base colour 2K like the body, normal/ORM 1K),
`arm_hand_gate.py` (every clip at 48 fps: hand/forearm depth inside the rest of the body, finger edge stretch,
wrist), `arm_clear.py` (least upper-arm turn that takes a hand out of the body), `glb_frames.py` (textured renders); since the 2026-10-30 face fix also `build_export_v2.py`'s `export_fix` (head cleanup), `head_closeups.py`
(head/neck close-ups), `head_topology.py` (holes, flipped faces), `compare_rows.py` (before/after sheets) and
`shading_check.py` (flat-shading check).

## v1 (MM9 rig-reuse route, superseded where v2 says so)


Isle of Ashes NPC for the MM9 world: MONSTERS.txt 252, `ForadDarre.abc` + `FORADDARRE.dtx`; isle object `ForadDarreNPC` (61), RUDE 2. Built by the **MM9 rig-reuse route for humanoid NPCs**: a Meshy HD
body fitted to the ORIGINAL MM9 skeleton, playing the original MM9 clips (see "Deviations"). Progress, hashes and
Meshy receipts: `creature_3d_progress.json`. Shared scripts are identical in `mm9_forad_claude/`,
`mm9_yrsa_claude/` and `mm9_annud_claude/` (only the configs differ).

| Item | Value |
|---|---|
| Runtime GLB | `assets_source/worlds/mm9/models/mm9_forad.glb` (installed with `tools/install_model.py --world mm9`; cooked copy in `assets_dev`) |
| Binding | `assets_dev/worlds/mm9/models/actors.yml`, descriptor `MM9 252 Forad Darre` (new MM9 NPC row, see below), `scale: 100` (GLB = LithTech units x 0.0256, MM9 world x 2.56), `yaw_offset: -1.570796327`, look `Bip01 Neck, Bip01 Head`, stride walk/run 1.1 / 3.0 |
| Triangles LOD0/1/2/3 | 8,267 / 4,128 / 1,449 / 455; LOD0 8267 (head+neck 3821, hands 1173, rest 3273; from Smart Topology 15161) |
| Skeleton | ForadDarre / PeasantMale, 45 joints (`Bip01 *` biped, mitten fingers `Finger0/01` thumb + `Finger1/11`, hip ring `root_bone`/`Bone02..23`); names and rest rotations unchanged, joints translated onto the HD body |
| Clips (30 fps, from PeasantMale library (`PEASANTMALE.abc`, 43 clips; `source/mm9_lib/pmale.glb`)) | Standing `stand1` 3.0 s, Walking `walk3` 0.9 s, Running `run` 1.03 s, Fidget `fidget1` 3.37 s, Talk `conv1` 4.37 s (script clip `talk`), Bow `bow` 3.03 s (script clip `bow`), AttackMelee `hattack1` 1.03 s (impact 0.5 s = MM9 `Rattack`), Hit `wince1` 1.03 s, Death `die1` 1.47 s, Dead |
| Textures | one set, no tiers: base colour 2K (head and neck UV islands 3x denser), normal 1K, ORM 1K (R baked AO, G roughness, B 0), `openyamm_specular 0`, metallic 0; class map `textures/forad_material_classes.png` (1 skin, 8 cloth/leather, 9 metal) |
| Meshy credits | **15** (Smart Topology 5, retexture 10; backup account), no retries |

## Route (scripts/)

0. **HD masters** (`references_hd/`, Codex, two runs, brief `CODEX_BRIEF.md`, records `generation_runs.json`,
   `selected_views_review.png`): inputs are renders of the MM9 model with its skin (`mm9_views.png` five views,
   `mm9_head_views.png`, `mm9_skin_x4.png` surface only). Pose = the MM9 bind pose (arms out ~17 deg below horizontal),
   so the Meshy mesh needs no posing to sit on the MM9 skeleton. Canvas 1536x1024 (spread arms).
1. **Meshy** Smart Topology 15k from `00_three_quarter.png` (`requests/smart_topology_v1.json`).
2. **Fit + weights** (`fit_rig.py`, `fit_config.json`; X-ray `review/xray_v1.png`): body scaled to the MM9 height,
   centre chain by torso depth (neck/head by the face line), arms by slices along the MM9 arm axis (each joint keeps
   its fraction of the arm and its offset from the centreline; wide sleeves: along the axis only), hips by hip width,
   knees/ankles by leg slices (a dress: legs follow the shoes), every other joint (fingers, hip ring, skirt, braids,
   hood) with its nearest fitted ancestor. Weights: the rigid MM9 skin carried onto the fitted joints, nearest-surface
   bone label, 8 diffusion passes, then **arm bands** (clavicle -> upper arm -> forearm -> hand by the position on the
   arm axis, so vest caps and sleeves follow the arm), 4 influences.
3. **Reduce after weighting + UVs** (`reduce_uv.py`, `reduce_config.json`): head/neck 0.75, hands 0.6, rest 0.42;
   Smart UV, head islands x3; upload `texturing/forad_body_upload.glb`; **retexture** with our UVs from 01/03/02/04
   (`requests/retexture_v1.json`).
4. **Textures** (`bake_ao.py`, `compose.py`, `../claude_shared/grade_basecolor.py --ao`).
5. **Clips** (`clips_mm9.py`, `roles_forad.json`): MM9 local rotations copied unchanged (the rest rotations are the MM9
   ones), translations = our rest + the source's pelvis offset x leg-length ratio; LithTech keys resampled as monotone
   cubic curves at 30 fps; loop seams spread; one-shots eased from/to Standing (0.15 / 0.2 s; Death in only).
6. **Runtime** (`build_runtime.sh forad Forad [--install]`): textured export (armature lifted so model y = 0 is
   the floor) -> clips -> `prepare_actor_glb.py` -> `build_actor_lods.py` -> `shrink_shadow_lods.py` -> material
   extras -> `floor_fix.py` (`floor_ops.txt`: ground loops/idles, raise run, corpse grounded) -> winding check (0).

Rebuild: `PYGLTF_PYTHON=<python with pygltflib> scripts/rebuild_rig.sh source/mm9/forad.glb scripts/roles_forad.json`
(fit + quick clip test), then `reduce_uv.py` (only with a new retexture: the UVs feed the paid job), `bake_ao.py`,
`compose.py`, `grade_basecolor.py`, `build_runtime.sh forad Forad --install`. MM9 sources:
`tools/mm9_import_discovery/convert_abc_model.py <abc> source/mm9 --id <id> --texture 0=<dtx> --scale 0.0256`.

## Checks (2026-10-29)

`scripts/gates.py` (`review/gates.json`), every clip at 30 fps (lowest point cm, edge stretch, wrist rotation
relative to the forearm vs rest, largest per-frame world rotation step of head/hands/feet):

| Clip | lowest cm | stretch p99 / max | hand p99 / max | wrist deg | jerk deg/frame |
|---|---|---|---|---|---|
| Standing | -0.0..-0.0 | 1.47 / 2.76 | 1.64 / 2.76 | 19.4 | 0.0 |
| Walking | -0.0..0.1 | 1.41 / 2.57 | 1.49 / 2.18 | 47.9 | 18.2 |
| Running | 1.1..13.2 | 1.52 / 2.63 | 1.51 / 2.12 | 40.9 | 34.5 |
| Fidget | -0.0..0.0 | 1.97 / 4.52 | 2.75 / 4.52 | 88.6 | 17.5 |
| Talk | -0.0..0.0 | 1.39 / 2.76 | 1.31 / 2.76 | 35.3 | 29.0 |
| Bow | -0.0..0.0 | 1.66 / 5.03 | 1.76 / 3.06 | 71.1 | 19.3 |
| AttackMelee | -0.0..0.0 | 1.68 / 3.41 | 2.13 / 3.2 | 35.5 | 55.6 |
| Hit | -0.0..0.0 | 1.5 / 3.77 | 1.64 / 3.77 | 53.2 | 40.0 |
| Death | -0.0..9.5 | 1.49 / 2.99 | 1.37 / 2.91 | 127.2 | 24.7 |
| Dead | 0.0..0.0 | 1.71 / 2.99 | 1.4 / 2.91 | 127.2 | 0.0 |

- Loop seams 0; floor: `floor_audit.py --world mm9` ok (stand 0, walk never below, corpse on the floor).
- Wrist angles above 60 deg and the fast steps (attack, hit) are the MM9 authored motion (fidget scratch, bow, limp
  death hand), checked in textured close-ups (`review/tex_clips.png`, `review/tex_close.png`): no wrist collapse.
- Viewer: `review/viewer/index.html` (port 8912 serves the repo root:
  `http://127.0.0.1:8912/level_generation/creatures/mm9_forad_claude/review/viewer/index.html`), `check_viewer.mjs` exit 0.
- Regression `mm9_actor_models_build_every_binding` (`--world mm9`): 6 descriptors on 4 models, 0 failed.
- In game: `review/ingame_sheet.png` (all three NPCs spawned on the remade isle: idles, walk/run, a hostile Forad fighting, Yrsa killed and lying on the floor) (remade isle review root, minimized, private `--user-data`, tour
  `mm9_forad_claude/review/ingame_tour.yml`).

## Deviations and open points

- **Clips are MM9's own, on the MM9 skeleton** (the dragonfly rig-reuse route), not the humanoid set/Mixamo with a
  Mixamo-frame rig: the MM9 libraries are the authored clips of these exact bodies and cover every role (including
  Forad's bow and the shopkeeper's talk), with MM9's contact events. The playbook gates were run on them. MM9's
  `stand1` is sparse (5 keys / 3 s), so Standing is quiet; MM9 hands are mittens (thumb + one four-finger chain),
  so fingers do not curl individually.
- No separate 1K head set (budget 15 credits: one retexture); the face gets 3x texel density in the 2K atlas instead.
- No tiers: unique NPCs with one MM9 skin each (no region mask/ramps).
- Descriptor: MM9 NPC rows (IsMonster 0) had no MM9 world descriptor, so `tools/mm9_import_discovery/
  generate_mm9_monster_tables.py` gained `--npc-actors` (`mm9_npc_actor_rows.tsv`: 54, 252, 254 with the legacy
  visual actor the isle already used) and the MM9 tables were regenerated (137 rows; the 134 monster rows unchanged).
  The isle's actors still use the old stand-in monster ids until the story session switches them.
- User artistic acceptance: v3.2 accepted 2026-10-30 ("forad darre - OK").


**LOD0 reduced post-install on 2026-11-05 by `level_generation/creatures/mm9_forad_reduce_claude/`** (ledger: `level_generation/creatures/REDUCTION_LEDGER.md`, "MM9 reduction"). A rebuild from this project must re-run that reduction, or it silently restores the heavier mesh. Rollback source: `level_generation/creatures/mm9_forad_reduce_claude/before/`.
