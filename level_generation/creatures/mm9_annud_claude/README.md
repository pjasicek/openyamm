# MM9 Annud Redeye (Shopkeeper Human2 MaleC A) (mm9_annud) — 3D actor, 2026-10-29

## Tier pm6_a for row 47 (2026-11-02, binding worker) - current

User decision ("Nearest + recolour"): MM9 row 47 Shopkeeper "Peasant Human1 MaleC A" (PeasantM6.abc, skin PEASANTM6A) is
a colour tier of this approved, frozen body, made with a region mask + ramp, 0 Meshy credits. PEASANTM6A is PEASANTM6B
(Annud's skin) with a mustard tunic where M6b is red; its face is a different man (not carried: Annud's face stays).
Work folder `tier_m6a/` (scripts, textures, review, rollback).

| Item | Value |
|---|---|
| Runtime GLB | `assets_source/worlds/mm9/models/mm9_annud.glb` = `tier_m6a/export/mm9_annud.glb`, sha256 `2091b0bd0fcdae18...`; before `164064ee7b99784e...`, rollback `tier_m6a/work/rollback/mm9_annud_installed_before_pm6a.glb` (source) and `mm9_annud_assets_dev_before_pm6a.glb` (cooked, `169f2b90bed24324...`) |
| Variants | default = the approved look (no `skin:`, `MM9 54 Shopkeeper` unchanged); **`pm6_a`** new (`MM9 47 Shopkeeper`) |
| Mask | one region, the tunic cloth: `tier_m6a/scripts/uv_positions.py` (rest-pose position per texel, body and head materials) + `tier_mask_ramp.py` (hue 4-28 deg, saturation >= ~0.7, value < ~0.8, above the hem at 0.65 m; head set: the collar below 1.55 m; gold-trim bands, rope belt, trousers, boots, skin and hair out; padded into the gutters, 1-texel feather) -> `textures/annud_m6a_region_mask.png` (body, 52 % of the atlas), `annud_m6a_head_region_mask.png` (3.4 %) |
| Ramp | `textures/annud_m6a_ramps.json`: PEASANTM6A's tunic texels (where M6b is red and M6a mustard, 22,129) sorted by luminance into 16 linear stops at M6a's own luminance (`--brightness 1.0`); range = our tunic's 2-98 % luminance. Annud's albedo ratio to M6b (0.82) made the mustard olive-brown (`review/sheet_pm6a_torso_k082.png`), so it is not applied |
| Append | `tier_m6a/scripts/add_tier.py` (as mm9_peasanthom2_claude's): two materials `Annud_PM6_A`, `AnnudHead_PM6_A` (copies sharing every image + mask/ramp extras), two mask images at the end of the buffer, KHR_materials_variants with `pm6_a`, 12 primitives mapped (LOD0-3, shadow meshes) |

Approved Annud unchanged (proof): `tier_m6a/review/verify_append.txt` **OK** (all 2,385 old bufferViews byte-identical at
the same offsets; every old accessor, image, texture, sampler, material, node, skin, animation, scene and mesh entry
identical; primitives only gain the variants extension); `review/glb_diff_vs_approved.txt` (v2 `glb_diff.py`): all six
images "same", same vertex counts on every mesh, same keys and durations on all 15 clips, **0.000 mm posed in every
clip**; cooked copy `review/cooked_runtime_check.txt` **OK** (old JSON entries and bufferViews identical, the six old
`.oytex` unchanged, two new). Winding 0. `mm9_hanndl.glb` (source `99c719f1...`, cooked `a6f5112c...`) unchanged.

Review: `tier_m6a/review/sheet_pm6a_vs_mm9.png` (MM9 PeasantM6 with M6b / ours approved / MM9 with M6a / ours pm6_a, front
and side, Blender, ramp applied by `preview_ramp.py` with the shader's formula), `review/sheet_pm6a_torso.png` (torso:
approved, pm6_a, MM9 M6a). Reads as an ochre-mustard tunic, a little browner than MM9's golden render; gold trim, laces,
rope belt, trousers and boots keep Annud's colours. Not checked: an in-game capture of the tier (map placement is the
orchestrator's), the ramp in the three.js viewer.

## Clips MM9's scripts play (2026-10-31, run2-clips-groupD) - current

User decision: the shopkeeper body carries only the PeasantMale clips its MM9 scripts and dialogue play. It is the DAT class
ShopkeeperHuman2MaleA (row 54, every shopkeeper of that class in every world). Its scripts: NPCbase.scr (row 54's default) and
retainer.scr via NPCBase.inc -> BaseRun.inc `LoopAnim Cower`; Trislan.scr (Guberland City play) conv1, conv2, conv3, stand,
Play_Death -> Play_getup, Bow; shopkeeper.scr, npcshopkeeper.scr (empty anim parameter), HideModel.scr, NPC5/61/128/129/142.scr,
BankOrb.scr: none. RUDE rows name no animation; no wander marker on these NPCs names one. Added and bound on `MM9 54 Shopkeeper`:
cower Cower, conv1 Conv1, conv2 Talk (installed), conv3 Conv3, bow Bow, play_death PlayDeath, play_getup PlayGetUp. MM9's `stand`
does not exist in the library (Standing plays stand1). Left out, not played by this NPC: MP_6a, run2, lean, leanfidget, bardrink,
barfig, barstand, bless, pray, conv, conv4, conv5, fidget1-3, fidget5, fidget8, hattack1, wince2, backpedal, backpedalrun,
cowerstart, cowerend, Sc07_shot1, Njam_*, hammer*, count*, sweep*, shovel*, innkeeper*.
`v2/scripts/extra_clips.sh` (roles `v2/scripts/roles_annud_extra.json`, `v2/scripts/hand_rest_annud_extra.txt`,
`scripts/floor_ops_extra.txt`) grafts them onto the installed export; byte check OK, 17.30 -> 18.99 MB. Conv1 and Bow take
hand_rest (Forad's route for the same library clips: arm_clear on conv1 jittered 14.6 deg/f over MM9); PlayGetUp keeps MM9's arm
(arm_clear's turn jittered 7.9 deg/f for a hand that holds the head). PlayDeath/PlayGetUp floors smoothed 0.08 s.
Gates (`v2/review/clips_restore_D/`): hands over 1 cm Conv1 L 3.0 cm 33 frames (hand at the chin), R 2.1 72 frames, Bow R 3.6
13 frames, PlayGetUp L 4.5 8 frames (hand on the head); forearms in the sleeves up to 6 cm (cloth on cloth, as the accepted
clips); jitter fails Conv1 (upper arm 1.25 / 1.06 deg/f over MM9, limit 1.0) and Bow (shoulder skin 2.3, limit 2.0); floor
living 0, PlayDeath/PlayGetUp -2.7 on single frames, corpse 0; limb bones within 7.5 %. Clay strip `clay_new.png` read.
Not looked at in the viewer or in game; Cower floated 82 cm before the floor pass (MM9's crouch drops a non-root joint).
Edits: `v2/scripts/clips_mm9.py` gained opt-in `soft_offsets` and `hold` (accepted clips rebuild byte for byte).

## Forearms in the sleeves (2026-10-30) - current

After Yrsa's "hands - cut off, floating?". Annud's sleeves already have a Meshy inner layer, so nothing shows
through them; only the hand ended in a visible cut stub inside the wide cuff. `v2/scripts/sleeve_lining.py lining=0`
(`v2/work/texpass_head.blend` -> `sleeves_v2.blend`) continues each stub up the sleeve to 6 cm from the elbow (171 faces
per arm, skin from the stub's rim texels). No lining, no clip change: every clip 0.000 mm against the texture-pass GLB
(`glb_diff.py`). Sheets `v2/review/sleeves_compare.png`, `v2/review/viewer_sleeves_sheet.png`.
`PYGLTF_PYTHON` is `claude_shared/gltf_venv/bin/python`, by that path (setup in `../mm9_yrsa_claude/README.md`). Rebuild:
`HEADTEX=annud_tp BODYTEX=annud_tp BLEND=v2/work/sleeves_v2.blend v2/scripts/build_runtime_v2.sh annud Annud
v2/scripts/roles_annud_v2.json --install`. Meshy: 0 credits. Forearm poke 0 frames in any clip at 48 fps (`sleeve_gate.py`, 211 + 215 vertices); `arm_hand_gate.py` hand values and `jitter_gate.py` unchanged in substance (clips identical); viewer `v2.2-sleeves-20261030`, 0 errors.

## Texture quality pass (2026-10-30) - current base

Coordinator request after `../claude_shared/TEXTURE_QUALITY_PASS.md` ranked Annud's body atlas fifth (25 %): sharper
textures only; mesh, rig, weights, clips, hands' skin and binding unchanged (the user had approved the look and motion).

- **Body set**: `v2/scripts/texpass_uv.py` (shared) re-laid the body faces' UVs with `uv_atlas.py` on
  `v2/work/head_v1.blend` -> `v2/work/texpass_uv.blend`; the head and hand faces stay in the upload, cut loose from the
  body and packed 0.35x as dense (1.2 % of the atlas), so Meshy sees the whole figure and the body never shares a
  chart with them. Retexture `v2/requests/retexture_texpass.json` (same four HD masters, `meshy-7`, 4K, our
  UVs) -> `meshy/body_retexture_texpass/`; `v2/scripts/bake_ao_texpass.py` (AO on the new UVs),
  `v2/scripts/compose_texpass.py` (4K -> 2K colour once, normal/roughness/metallic to 1K, classes) ->
  `textures/annud_tp_*`; gentle grade (`grade_basecolor.py --fine 1.0 --local 0.3 --ao-strength 0.5 --contrast 1.06
  --saturation 1.15`). Grade chosen on crops of raw / v1 default / gentle / gentle with v1 contrast
  (`v2/review/texpass/` renders; rendered tunic mean RGB approved 67/43/32, gentle 70/45/33, closest of the graded
  ones). The new paint follows the HD master's woven tunic; the approved paint's dark mottling (the Smart UV
  fragments) is gone.
- **Head set**: `v2/scripts/texpass_head_uv.py` re-laid the head faces (HeadUV x 0.8, lower-left square as before)
  -> `v2/work/texpass_head.blend`; 4K head retexture `v2/requests/head_retexture_texpass.json` (same head references)
  -> `meshy/head_retexture_texpass/`; `v2/scripts/compose_head_texpass.py` pastes it into the approved head set's
  head square and keeps every hand texel byte for byte -> `v2/textures/annud_tp_head_*`. Same face (eyes, beard,
  smile), sharper: `v2/review/texpass_head_closeups.png`. The repainted rim of the neck hole under the right jaw put a
  brown triangle on the fill patch, so `build_export_v2.py` gained `fill_texel: median` (`v2/scripts/head_annud.json`):
  the patch samples the rim face whose texel is nearest the rim's median colour.
- Shared script options added: `build_runtime_v2.sh` `BODYTEX` / `HEADTEX`, `build_export_v2.py` sixth argument (head
  set file prefix). Rebuild: `HEADTEX=annud_tp BODYTEX=annud_tp BLEND=v2/work/texpass_head.blend
  v2/scripts/build_runtime_v2.sh annud Annud v2/scripts/roles_annud_v2.json --install`. Never re-run the two UV
  scripts: the paid textures belong to their exact layouts.

| `texture_quality.py`, LOD0 | Body before | Body after | Head set before | Head set after |
|---|---|---|---|---|
| Atlas use (2K) | 25.2 % | **59.4 %** | 39.1 % (head square 54 %) | 40.9 % (head square 58 %) |
| Equivalent square | 1,029 px | 1,579 px | 1,280 px | 1,310 px |
| Density p10 / p50 / p90 | 802 / 891 / 955 | **1,353 / 1,400 / 1,437** (+57 %) | 1,820 / 3,068 / 3,402 | 1,820 / 3,221 / 3,352 |
| Spread p90/p10 | 1.19 | 1.06 | 1.87 (hands half as dense, by design) | 1.84 |
| Islands / fragments | 293 / 4.9 % | 94 / 0.1 % | 310 / 6.1 % | 142 / 1.4 % |
| Stretch p90 | 1.46 | 1.09 | 1.44 | 1.23 |
| Meshy source | 2K | 4K on 61 % | 2K | 4K on 58 % |

**Checks**: motion identical to the installed GLB (`v2/scripts/glb_diff.py`: every clip 0.000 mm at 48 fps, clip
channels equal); LOD0 8,218 triangles as before; winding 0 inverted; installed (`tools/install_model.py --world mm9`);
viewer revision `v2.1-texpass-20261030`, `run_creature_review.py check` 9 clips, 0 errors; `arm_hand_gate.py`
identical (`v2/review/arm_hand_gate_texpass_{before,after}.txt`); `jitter_gate.py` hand and arm values identical, only
the shoulder-skin p95 moves with the new vertex split (8 -> 7 pre-existing fails, `jitter_gate_texpass_*.txt`);
`detached_parts_audit.py`: the same single known case (left hand 5.3 mm inside the sleeve), nothing new;
`mm9_actor_models_build_every_binding` (`--world mm9`): 49 descriptors on 20 models, 0 failed. Binding unchanged.
Sheets: `v2/review/texpass_compare.png` (face front/3/4, both hands, torso, full front/3/4 at identical cameras),
`v2/review/texpass_head_closeups.png` (bind and Talk 60: front, profile, 3/4, eyes, mouth, neck). Before state:
`v2/work/before_texpass/`. **Meshy: 20 credits** (body and head retexture, 10 each, backup account).

New shared v2 scripts from this pass (identical in the three projects' `v2/scripts/`): `texpass_uv.py`, `texpass_head_uv.py`,
`bake_ao_texpass.py`, `compose_texpass.py`, `compose_head_texpass.py`, `uv_pairs.py` + `match_skin.py`, `texpass_shots.py`
(identical-camera stills), `part_views.py` (close-ups around joints, also see-through), `glb_diff.py` (what changed
between two runtime GLBs: images, meshes, clips, posed vertices).

## v2 rework (2026-10-30, after the user's review) - current base (textures changed above)

User review of v1: overall good, keep the body and animations; fix the head texture and the four warped fingers.

- **Hands**: five-finger MPFB hands grafted inside the wide sleeves, 15 new finger bones per side
  (`Bip01 <S> Thumb1..Pinky3`) with the MM9 mitten bones' rest frames, driven from MM9's Finger0/01/1/11 curl
  (`finger_alias` in `v2/scripts/roles_annud_v2.json`; index 0.75 .. pinky 1.0 of the mitten curl). MPFB weights.
- **Head**: Codex head turnaround + Meshy head-only retexture (10 credits) on the separate head/neck shell and the hair.
- **Arm and hand gate**: `arm_clear.py` cleared the hands in Fidget and Talk (up to 6 cm into the tunic before);
  remaining: one interpolated Talk frame (5.5 cm fingertip at the tunic skirt), the wide sleeves brushing the tunic
  (cloth on cloth, 4-6 cm). The MM9 clips are otherwise unchanged.
- In game (remade isle review root, minimized): `v2/review/ingame_sheet.png` in mm9_forad_claude (all three).
- Runtime `v2/scripts/build_runtime_v2.sh annud Annud v2/scripts/roles_annud_v2.json --install`; LOD0 8,218 triangles
  (8,404 before the face fix).
- **Face fix (2026-10-30, user review: "missing triangles" in the neck, "weird artifacts" at the eyes and lips).**
  Causes, all in the Meshy head mesh and present since v1 (`fit_v1.blend`), not in the head split or the composed set:
  (1) a 5-edge hole in the head shell under the right jaw (two grey triangles); (2) Meshy's separate eyeball cups
  (parts 6, 7) cross the lower lids, and their lower halves carry lid skin from the retexture, so jagged skin and
  white strips showed under both eyes (the shell itself already carries the painted eyes: removing the cups leaves
  a clean eye); (3) the mouth is a thin slit open to the back of the head (29-edge loop), lined with the reference
  smile's teeth painted onto jagged inner-lip faces, with the background showing through the gap.
  Fix in the shared `build_export_v2.py` (`export_fix` in `v2/scripts/head_annud.json`): eyeballs dropped, small holes
  filled (one island's texel, rim relaxed), the mouth slit capped and its inner faces given one dark lip texel, and
  the pale teeth texels around the slit repainted with the lips' median colour into the embedded copy
  `v2/work/annud_head_basecolor_export.png` (the composed set is unchanged). Head shell: boundary loops 33/29/5 ->
  33 (the neck opening inside the collar), 0 flipped, 0 non-manifold (`v2/review/head_topology_*.json`,
  `head_topology.py`). Before/after `v2/review/face_fix_compare.png` (bind, Talk 60/130: front, both profiles, 3/4,
  eyes, mouth, neck; `head_closeups.py`, `compare_rows.py`) and viewer crops `v2/review/viewer_face_fix_compare.png`.
  Gate rerun (`v2/review/arm_hand_gate.txt`): unchanged except Fidget R hand 2.5 cm at frame 57, the MM9 beard
  scratch whose fingertips now meet the closed mouth instead of entering the open slit (one frame). Winding 0,
  viewer check 0 errors.
- Jitter gate (2026-10-30, `jitter_gate.py`, `v2/review/jitter_gate.json`): every clip within MM9's own hand
  acceleration and angular velocity (the arm_clear corrections add no shake). Detached-parts audit: the left hand
  sits 5 mm from the inside of the wide sleeve, inside the sleeve opening; left as is (closing it would change the
  sleeve or the wrist).

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


Isle of Ashes NPC for the MM9 world: DAT class `ShopkeeperHuman2MaleA` = MONSTERS.txt 54 "Shopkeeper", Type "Peasant Human2 MaleC A": `PeasantM6.abc` + `PEASANTM6B.dtx`; isle object 747 (`ShopkeeperHuman2MaleA0`, `Filename models\PeasantMale.abc`, NPCNbr float 138.0 = RUDE NPC 138 "Annud Redeye", greeting `NPC_138.wav`). Built by the **MM9 rig-reuse route for humanoid NPCs**: a Meshy HD
body fitted to the ORIGINAL MM9 skeleton, playing the original MM9 clips (see "Deviations"). Progress, hashes and
Meshy receipts: `creature_3d_progress.json`. Shared scripts are identical in `mm9_forad_claude/`,
`mm9_yrsa_claude/` and `mm9_annud_claude/` (only the configs differ).

| Item | Value |
|---|---|
| Runtime GLB | `assets_source/worlds/mm9/models/mm9_annud.glb` (installed with `tools/install_model.py --world mm9`; cooked copy in `assets_dev`) |
| Binding | `assets_dev/worlds/mm9/models/actors.yml`, descriptor `MM9 54 Shopkeeper` (new MM9 NPC row, see below), `scale: 100` (GLB = LithTech units x 0.0256, MM9 world x 2.56), `yaw_offset: -1.570796327`, look `Bip01 Neck, Bip01 Head`, stride walk/run 1.1 / 2.8 |
| Triangles LOD0/1/2/3 | 8,338 / 4,169 / 1,500 / 496; LOD0 8338 (head+neck 3992, hands 1208, rest 3138; from Smart Topology 15034) |
| Skeleton | PeasantM6 / PeasantMale, 45 joints (as Forad); names and rest rotations unchanged, joints translated onto the HD body |
| Clips (30 fps, from PeasantMale library (`source/mm9_lib/pmale.glb`)) | Standing `stand1` 3.0 s, Walking `walk3` 0.9 s, Running `run` 1.03 s, Fidget `fidget4` 3.37 s, Talk `conv2` 4.37 s (script clip `talk`), AttackMelee `hattack2` 1.37 s (impact 0.533 s = MM9 `Rattack`), Hit `wince1`, Death `die1`, Dead |
| Textures | one set, no tiers: base colour 2K (head and neck UV islands 3x denser), normal 1K, ORM 1K (R baked AO, G roughness, B 0), `openyamm_specular 0`, metallic 0; class map `textures/annud_material_classes.png` (1 skin, 8 cloth/leather, 9 metal) |
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
   Smart UV, head islands x3; upload `texturing/annud_body_upload.glb`; **retexture** with our UVs from 01/03/02/04
   (`requests/retexture_v1.json`).
4. **Textures** (`bake_ao.py`, `compose.py`, `../claude_shared/grade_basecolor.py --ao`).
5. **Clips** (`clips_mm9.py`, `roles_annud.json`): MM9 local rotations copied unchanged (the rest rotations are the MM9
   ones), translations = our rest + the source's pelvis offset x leg-length ratio; LithTech keys resampled as monotone
   cubic curves at 30 fps; loop seams spread; one-shots eased from/to Standing (0.15 / 0.2 s; Death in only).
6. **Runtime** (`build_runtime.sh annud Annud [--install]`): textured export (armature lifted so model y = 0 is
   the floor) -> clips -> `prepare_actor_glb.py` -> `build_actor_lods.py` -> `shrink_shadow_lods.py` -> material
   extras -> `floor_fix.py` (`floor_ops.txt`: ground loops/idles, raise run, corpse grounded) -> winding check (0).

Rebuild: `PYGLTF_PYTHON=<python with pygltflib> scripts/rebuild_rig.sh source/mm9/pm6.glb scripts/roles_annud.json`
(fit + quick clip test), then `reduce_uv.py` (only with a new retexture: the UVs feed the paid job), `bake_ao.py`,
`compose.py`, `grade_basecolor.py`, `build_runtime.sh annud Annud --install`. MM9 sources:
`tools/mm9_import_discovery/convert_abc_model.py <abc> source/mm9 --id <id> --texture 0=<dtx> --scale 0.0256`.

## Checks (2026-10-29)

`scripts/gates.py` (`review/gates.json`), every clip at 30 fps (lowest point cm, edge stretch, wrist rotation
relative to the forearm vs rest, largest per-frame world rotation step of head/hands/feet):

| Clip | lowest cm | stretch p99 / max | hand p99 / max | wrist deg | jerk deg/frame |
|---|---|---|---|---|---|
| Standing | -0.0..-0.0 | 1.29 / 2.14 | 1.38 / 1.98 | 12.9 | 0.0 |
| Walking | -0.0..0.0 | 1.36 / 3.07 | 1.95 / 3.07 | 41.3 | 18.2 |
| Running | 0.9..13.1 | 1.44 / 2.79 | 1.76 / 2.79 | 36.4 | 34.5 |
| Fidget | -0.0..0.0 | 1.76 / 4.84 | 2.99 / 4.84 | 67.9 | 36.5 |
| Talk | -0.0..0.0 | 1.33 / 3.05 | 1.38 / 2.23 | 58.4 | 19.6 |
| AttackMelee | -0.0..0.0 | 1.63 / 5.09 | 2.25 / 4.17 | 31.3 | 52.8 |
| Hit | -0.0..0.0 | 1.35 / 3.24 | 1.64 / 3.05 | 53.2 | 40.0 |
| Death | -0.0..10.7 | 1.44 / 4.03 | 1.19 / 2.86 | 119.2 | 24.7 |
| Dead | 0.0..0.0 | 1.59 / 3.9 | 1.35 / 2.86 | 119.2 | 0.0 |

- Loop seams 0; floor: `floor_audit.py --world mm9` ok (stand 0, walk never below, corpse on the floor).
- Wrist angles above 60 deg and the fast steps (attack, hit) are the MM9 authored motion (fidget scratch, bow, limp
  death hand), checked in textured close-ups (`review/tex_clips.png`, `review/tex_close.png`): no wrist collapse.
- Viewer: `review/viewer/index.html` (port 8912 serves the repo root:
  `http://127.0.0.1:8912/level_generation/creatures/mm9_annud_claude/review/viewer/index.html`), `check_viewer.mjs` exit 0.
- Regression `mm9_actor_models_build_every_binding` (`--world mm9`): 6 descriptors on 4 models, 0 failed.
- In game: `../mm9_forad_claude/review/ingame_sheet.png` (all three NPCs spawned on the remade isle: idles, walk/run, a hostile Forad fighting, Yrsa killed and lying on the floor) (remade isle review root, minimized, private `--user-data`, tour
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
- User artistic acceptance: v2 with the face fix accepted 2026-10-30 ("anud - ok").


**LOD0 reduced post-install on 2026-11-05 by `level_generation/creatures/mm9_annud_reduce_claude/`** (ledger: `level_generation/creatures/REDUCTION_LEDGER.md`, "MM9 reduction"). A rebuild from this project must re-run that reduction, or it silently restores the heavier mesh. Rollback source: `level_generation/creatures/mm9_annud_reduce_claude/before/`.
