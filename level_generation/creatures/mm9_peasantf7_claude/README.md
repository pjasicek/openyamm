# MM9 PeasantF7, the elf townswoman with long hair and two front braids (mm9_peasantf7) — 3D actor, 2026-11-02

MM9 `PEASANTF7.abc` (73 joints, the human female skeleton of `PEASANTFEMALE`; its rest arms sit 25.7 deg below horizontal, F5's 34.2) with skins
`PEASANTF7A` and `PEASANTF7B`. `MONSTERS.txt` rows on this model: **18** Town "Peasant Elf FemaleB B" (F7a, DAT `TownElfFemaleB`, 7 placed) and
**20** Shopkeeper "Peasant Elf FemaleC B" (F7b, DAT `ShopkeeperElfFemaleB`, 3 placed). Both run NPCbase.scr (PeasantFemale library); the
objects' own scripts (shopkeeper.scr, retainer.scr, NPC96.scr) play no animation. Built on the approved MM9 humanoid route (MM9 skeleton, MM9
`peasantfemale` clips, never Mixamo).

**Why a new body:** `mm9_meshcmp.py peasantf7:peasantf5,peasantf6,peasantf2`: bind differs from F5/F6 by 7.2 cm; after a rigid shift head
p90 4.1-4.7, torso 3.0-3.6, arms 5.3 cm. Posed by the same library frame (stand1 0, `posedcmp.py` in the scratch notes): arms agree within
0.7 cm (the raw arm gap is the bind angle) but torso p90 3.4 / max 4.9 cm and head 3.3 / 6.6 cm vs F5; vs F2 torso 7.2 cm. Not within
1.5-2 cm of any built body, and the design differs (long hair sheet, two front braids, elbow-length chemise sleeves): a new body.

| Item | Value |
|---|---|
| Runtime GLB | `assets_source/worlds/mm9/models/mm9_peasantf7.glb` (r16, sha256 643d7ed9723c...) = `export/mm9_peasantf7.glb`; variants `pf7_a` (row 18), `pf7_b` (row 20) |
| Binding | `assets_dev/worlds/mm9/models/actors.yml` block `mm9_peasantf7_claude`: `MM9 18 Town` (pf7_a), `MM9 20 Shopkeeper` (pf7_b); scale 100, yaw_offset -1.570796327, stride 1.0 / run 1.6, look Neck + Head (F5's block) |
| Descriptors | rows 18, 20 in `tools/mm9_import_discovery/mm9_npc_actor_rows.tsv` (fallback visuals 335 / 338, the legacy replacements), tables regenerated: ids 9018, 9020 (`scripts/bind_pf.py scripts/binding.json` under the flock) |
| Triangles LOD0/1/2/3 | 14,952 / 7,399 / 2,663 / 887 (r16, with the hair-rim lining; before it 14,518: head + eyes 3.1k, MPFB arms + hands 3.6k, dress 2.2k, skirt 1.7k, braids 1.6k, hair 1.2k, legs 0.8k, bracelets 0.4k, caps 0.3k) |
| Skeleton / clips | 108 joints (MM9's 73 + 30 MPFB finger bones + 5 helpers); Standing `stand1`, Walking `Walk`, Running `run`, Fidget `Fidget4`, Talk `Conv2`, Conv1, Conv3, Hit `Wince1`, Death `Die1`, Dead, Cower `cower` |
| Textures | body colour 2K, normal/ORM 1K, region mask 1K (R dress cloth, G tier-B corset panel, B tier-B lacing, A belt); head set (head, hair, braids) 1K colour per tier, normal/ORM 1K shared |
| Meshy credits | **35 / 50**: Smart Topology 5, body retexture 4K 10, head retextures 4K A 10 and B 10 (backup account; 2755 before the first job, 2715 before the last) |
| Codex | masters run 1 (three-quarter) + run 2 (four views), head turnarounds A and B (8 views), face repaint A and B (`references_face/`); all through `codex_slot.sh` (one stuck session killed and rerun) |
| Viewer | http://127.0.0.1:8912/level_generation/creatures/mm9_peasantf7_claude/review/viewer/ revision `r16-20261102` |

## Route (`scripts/`, F1's chain (`mm9_peasantf1_claude`) with F3's braids and F5's bracelets)

0. `convert_abc_model.py --scale 0.0256` (gltf_venv python + system yaml on PYTHONPATH) -> `source/mm9/pf7a|pf7b`; `refsheets.py` + `ref_renders.py` -> `references_hd/mm9_*`.
1. Codex masters (`references_hd/CODEX_BRIEF.md`, skin A), `clean_alpha.py`; head turnarounds (`references_head/`).
2. Smart Topology 15k -> `step1_clean.py ... 1.7557` (MM9's height). Meshy fused face, chemise, pinafore and skirt (with the apron) into one shell
   and closed the skirt itself (an inner hem wall and a floor at the shins: no lining needed).
3. `seg_pf7.py` (Dijkstra head/dress split, skirt below 1.10 m) -> `assemble_pf7.py` (X0 0.008): mirrored at the midline; the head = exactly
   what lies above the slanted neck plane (clean seam); MPFB arm + hand (F1's `work/hand.npz`) on MM9's arm direction; procedural bracelets
   (F5); **braids** as F3's tubes along MM9 F7's xpony path (plait swell, tie, tuft; top tucked under the hair); Meshy's mouth inserts and
   eyelash cards dropped later (`drop_mouth_pf7.py`, both loose pieces: the cards read as heavy dark wings over the eyes).
   `hair_fit_pf7.py` (x2): the hair's outer surface fitted to MM9's own hair radius per height/azimuth (back +1-2 cm); head-window IoU 0.94 front.
4. `uv_pf.py` (never re-run: `work/uv_orig.npz` is the paid layout), `drop_needles_pf7.py` (32 sub-millimetre needle/degenerate faces dropped
   before the upload). Body atlas 63.5 %, head 56.3 %.
5. Paint: body 4K, heads 4K A and B; `compose_pf.py`, AO (`texpass_bake_ao.py`, `pad_ao.py`), `finish_pf.py` (gentle grade), `sym_paint.py`.
6. `tiers_pf7.py`: masks from our paint and MM9's skins projected onto our UVs (`project_mm9_skin.py`): R dress cloth (A yellow-green, B red),
   G corset panel and B lacing (tier B's dark laced corset under the open red vest; tier A takes the dress ramp there), A belt (A cream, B dark).
7. Faces: `head_fix_pf7.py` (hair/braid texels off the hair hue recoloured; the procedural eye/nostril repaints exist but are OFF: they made
   it worse); `tweak_pf7.py` (F5's face tweak with F7 landmarks: midline pull, lips back 2.6 mm, closed slit (dome 0.7 mm), nostril and nose-tip
   smoothing, eyeballs 3 mm deeper, upper lid rim 1.6 mm down, degenerate faces dropped; the eye-crease smoothing is OFF: it made the brows wavy);
   Codex face repaint by landmarks (`references_face/`, flat front renders in, warm closed-lip smiles, lids over the top of the iris, clean nose)
   -> `align_face_pf7.py` -> `project_face_pf7.py` (window chin..brows, edge-ring colour gains, mouth box always projected, nose underside and
   columella faces on one feathered nose-skin colour, unreached/tiny faces from their nearest projected neighbours). The head normal map is
   neutral ONLY on those ~300 underside/columella faces (Meshy's normals there were corrupt: jagged shading and a blue-white speck that no paint
   changed); the rest of the nose and mouth relief is Meshy's.
8. `line_rims_pf7.py`: a 1.5 cm lining inside the hair shell's open rims (`HAIR_BAND`, 2 mm inside, rim strip, dark hair texel); caps over the head shell's open loops (neck bottom x2, the skull opening under the hair that Wince/Fidget expose, a 9 mm
   forehead pinhole), the dress's waist loop (facing down) and the MPFB arm stubs inside the sleeves.
9. `rig.sh` (`fit_rig_pf.py` with pf7a.glb; `weights_pf.py`: hair rigid on Head, its hanging sheet on Ponytail11/12 with up to 60 % on Spine3 at
   the bottom; braids on the xpony chains blending to Head over their top 4 cm; bracelets one weight set per side; `ARMDEG` 5 deg constant
   abduction (our hips are fuller than MM9's) + `arm_clear`/`arm_soft` on Conv3 (`arm_jobs.txt`)) -> `build_runtime.sh` (skirt-lift
   tolerance 0.14 as F5; `double_head.py` marks the head-set materials doubleSided: the engine draws their back faces with a flipped normal
   (fs_model.sc), so the one-sided hair shell's inside shows hair, not background) -> `viewer_update.sh`. `tweak_pf7.py` also slims the MPFB
   upper arm hidden inside each short sleeve to 85 % (it poked 1-2.6 mm through the sleeve in Death/Dead). **`rebuild.sh <rev> [--install]`** replays all of it from the paid paints.

## Checks (final r16, `review/gates/`)

| Gate | Result |
|---|---|
| `arm_hand_gate.py --outer-only --exact` | **0 frames > 1 cm, every clip, both hands** (before ARMDEG/arm_clear: Standing 1.9/2.3 cm all frames, Conv3 3.9/5.1 cm) |
| `robe_gate.py` (legs through skirt) | **0 frames in all 11 clips** (Death/Dead 4.0/3.4 cm at the F1 tolerance 0.12; 0 at 0.14) |
| `jitter_gate.py` | 0 fails |
| `sleeve_poke_pf1.py` (MPFB upper arm through the short sleeve) | **0.0 mm every clip** (r15: Death 2.6 / Dead 1.9 mm, fixed by the slimming) |
| `flat_shading_check.py` | 0.00 body, 0.00 head |
| `bone_length_audit.py` | 14 checked, 0 stretching |
| `detached_parts_audit.py` | 1: the left leg free inside the closed skirt (by design, as F5/F8) |
| `check_winding.py` | 0 inverted closed parts |
| `floor_audit.py --world mm9` | MM9 18 / MM9 20 ok: stand -0.2, walk -0.1..+1.5, living -1.1, dead 0.0 |
| Sheets (read) | `review/sheet_mm9_vs_ours.png`, `review/sheet_128px.png`, `review/clay_hair2.png`, `review/mm9_hair_clips.png`, `review/sheet_asm2.png`, `review/sil_fit2.png` |
| `texture_quality.py` | body atlas 63.5 %, spread 3.42 (hands 1.4x, legs 0.5x, skirt inside 0.3x by design), fragments 0.0 %, stretch 1.11; head atlas 56.3 %, fragments 0.1 %, stretch 1.08 (its density p10 0 / spread: the hidden cap fans use one texel) |
| `see_through_gate.py` (8 az x 0/20 deg, step 3) | r6 (no caps): torso 347 px, head 105, sleeve L 77, collar 31. r15 (caps + hair lining, all faces culled): head 102, torso 339 (the hair shell's inside under its rim; the torso zone is the hair sheet's Spine3 share), sleeves 1-3, collar 2. r16 with `double=1` (the gate draws doubleSided materials from both sides, as the engine): head 0, torso 49 px (Death, from behind), sleeves 1-3, collar 2 |
| `mm9_actor_models_build_every_binding` | PASS (240 descriptors on 105 models, 0 failed) |
| Viewer `run_creature_review.py check` | 22 switches, 0 failed |
| Faces (viewer lighting: front close-up, 3/4, true profile, low 3/4, party view) | `review/sheet_r16a_face.png`, `review/sheet_r16b_face.png` (r14 identical faces) |

## Deviations and open points
- **Hair fling:** MM9's Wince1/Fidget4 key the Ponytail chain so the hair sheet swings up behind the head (MM9's own thin wedge does the same,
  `review/mm9_hair_clips.png`); ours is thicker, so it reads as a slab for a few frames.
- **Ears:** MM9's F7 hides the ears under the hair; so do we (no elf ears visible).
- **Face residuals:** a ~2 mm pale speck at the base of the columella in the front close-up (present since the first build: Meshy geometry
  there); the eyes still read a little wide (Meshy's large lid opening; MM9's F7 also has big open eyes).
- **Tier B necklace:** MM9 B wears a heavy gold-amber necklace; ours keeps A's thin chain (no mask channel left).
- Lacing on tier B's corset is a ramp on a low-resolution mask projected from MM9's 256 px skin: soft.

## What was not checked
In game (no map places these descriptors yet; the map switch is the orchestrator's). LOD1-3 and shadow meshes by eye. Motion at normal
speed by eye (stills and gates only). Ear close-ups (no ears: hidden by the hair, checked in profile and 3/4 only).

User artistic acceptance: not recorded

## Face pass 2 (coordinator review 2026-11-02, r21, 20 credits)
Review of r16: a pale speck and a dark notch at the nose base; eyes a little wide; a dark notch at the top of the hair parting.
- Causes found in clay (welded): my F5-derived face tweak had blunted the nose; the mirror seam had unwelded midline vertices and the
  sub-mm needle slivers dropped before the upload left open cracks under the nose, on the chin, forehead and hair parting (44 boundary
  edges); Meshy's columella/nostril rims were jagged shards.
- Geometry (`tweak_pf7.py` + `scripts/tweak.env`): Meshy's nose and lips kept (no midline pull/snap/fin collapse/nose smoothing/lip pull);
  slit closed (dome 0.5 mm); eyeballs 3 mm back; upper lid rim 2.6 mm down; midline cracks welded; the small holes left at the philtrum top
  collapsed to their centroid (HOLES); pinhole caps in `line_rims_pf7.py`. Frozen geometry `work/geom_final_v2.npz` (c4c8d917b0c90616)
  was painted; AFTER the paint the down-facing nose-underside shards were Laplacian-smoothed (COL_PASSES 10, at most 2.5 mm, 56 positions)
  and the 2 philtrum holes collapsed (final hash 80e2158b907ab484) - the one deviation from "no moves after painting", confined to faces
  whose texels are then repainted from their new positions (PASS2 nose underside: nose-skin shade + two soft nostrils; philtrum fill).
- Fresh Meshy 4K head paints A and B on the frozen geometry (pf7_head_a_v2 / pf7_head_b_v2, 10 + 10; backup 2400 / 2390 before); Codex
  projection retired; head normal map unmodified. Paint finish PASS2 as F2's (lips rose, specks, nostril lift, parting, lid shade, forehead).
- Sheet (read): `review/sheet_faces_pass2_before_after.png` (both tiers, r16 vs r21) and `review/zoom_r21.png`.
  Remaining marks: a pale line along the hair parting in tier A (3/4, low); a faint pale tick at the top of tier B's forehead midline; a
  slightly lighter facet on the bridge between the eyes (mirror midline, nose normals left alone); the nose underside reads as a soft
  dark shadow from the front; eyes still a little round.
- Credits now **55** (35 + 20).

## Face pass 3 (coordinator, 2026-11-03, r25, 0 credits)
- Pale strip down the midline: it was a 1 mm line in the paint (sym_paint keeps the midline faces' own Meshy paint) on the forehead and
  bridge. Fixed by a gain on those texels to the skin 2-3.5 mm aside (`head_fix_pf7.py` PASS2 9b, detail kept). Plus vertex normals within
  7 mm of the midline (hairline to nose tip) blended from the mirrored normals at 7 mm, feathered (`build_glb_pf.py`, "SEAM normals"; 66
  welded positions; positions unchanged). A broad soft bridge highlight that follows the nose form remains.
- Nostrils: the procedural nostrils moved onto the real openings (x +-6.8 mm, z 0.643; they were 1 cm low) and made small and soft; the
  underside paint lifted to 1.2x the nose skin and the nose-base paint floored at 90 % of the skin. The remaining darkness is the
  geometry's own shading in the alar creases (unchanged by further paint lifts).
- Hair parting: pale scalp-line texels within 5 mm of the midline toned to the hair beside them (PASS2 10); the red forehead tick gone.
- Sheets (read): `review/sheet_pass3_before_after.png` (r21 vs r25, both tiers: close-up, 3/4, low), `review/zoom_parting.png`,
  `review/flatbr_cmp.png` (flat albedo of the bridge before/after). Installed sha256 10f163a3572f...; binding PASS (248/110); floor ok;
  viewer 22/0. Geometry hash unchanged (80e2158b907ab484); gates unaffected (paint and normals only). Rollback `work/pre_pass3/`.

## Neck graft and upper lip pass (user review 2026-11-04, r33, 0 credits)
User: "peasantf7 the same [as F2: the head graft looks soldered on] + the black stuff on her upper lip"
(`review/user_20261104/neck_graft.png`, `upper_lip.png`). F2's method (`mm9_peasantf2_claude/README.md`, "Neck graft pass"), plus:
- **Dark band and V notches on the graft** = shading: the head's two neck-bottom caps (`inner` fans, 68 + 80 vertices) were summed into
  the seam normals (median normal z -0.80 instead of +0.45). `build_glb_pf.py`: outer-only normals at shared rim positions (348
  positions); both caps dropped (148 faces; the head rings are welded to the dress); 9 dress neck-loop vertices projected onto the
  head ring (<= 0.93 mm). LOD0 14,942 -> 14,794.
- **Paint on the graft:** Meshy painted chemise/collar colours (and bead shapes at the sides) on the bottom ~1.2 cm of both heads: cloned
  over with the neck skin 2.2 cm higher (`head_fix_pf7.py` (11), `NECK_CLONE=ab`, `NECK_CLONE_H=0.020`), outliers replaced, the neck paint
  feathered within 3.2 cm of the seam. The body has no free region channel (R dress, G corset, B lacing, A belt), so both necks and the
  chest skin are pulled to one shared skin, `NECK_TARGET=240,162,110` (the mean of the two tiers' neck medians): chest skin 202,126,87 ->
  240,162,110 (`tiers_pf7.py`, skin = front dress texels within 17 cm of the seam, skin-coloured, sat > 0.30 to keep the chemise trim out;
  padding fixed).
- **Pale V marks on both shoulders and an M under the necklace** = Meshy paint (outlines of the old graft's geometry), not shading: cloned
  over from the skin 2.4 cm lower (`MARKS`, r 11 mm). The stray dark tag on the left shoulder and the dark wedge on the neck midline were
  seam/midline shading: gone with the cap normals and the neck SEAM normals (z 0.515-0.575, as F2).
- **Black triangle on the upper lip and black slit:** geometry. At the closed slit's tubercle (and two spots 14 mm aside) the front surface
  folds over itself - 20 front faces face backward, so the engine draws their back side (doubleSided head set): black. `build_glb_pf.py`
  MOUTH unfold relaxes those vertices toward their neighbours (30 positions, <= 1.5 mm, 5 passes, 20 -> 0 backward faces); then the groove's
  down-facing upper side is turned 60 % toward forward (`MOUTH_NRM=0.6`, |x| < 16 mm, 97 positions; glTF axes). Paint: the upper lip's
  underside (painted 0.7x the lip front) takes the lip-red colour, the slit crease 0.8x of it, eased out before the corners
  (`head_fix_pf7.py` (12)). **Deviation:** post-paint moves (<= 1.5 mm, inside the lip red) and normal edits on the mouth, against "never
  move face geometry after painting / never relax normals over the mouth"; made because the defect was a fold and its shading, which no
  paint changes (tried: r26). Check the lips at the corners: the unfolded slit's corner wings read as a faint flat band there.
- **Forehead band (tier A):** the old flat gain (6) left a band: replaced by F2's profile equalisation above the brows (`FH2=1`).
- **Nostrils:** not fixed. Paint lifts (UNDER_SHADE 1.3, softer cool spots) made the underside khaki without removing the dark: the
  remaining dark T under the tip is the down-facing underside's own shading. A normal edit there is what the face rules forbid; left
  for the orchestrator/user (UNDER_SHADE back to 1.2, NOST_COOL 0.82).
- Sheets (read): `review/sheet_neck_r25_r33.png` (r25 vs r33: close-up, neck front, neck 3/4, 3/4, profile, low, party, both tiers),
  `review/zoom_mouth_r32.png`, `review/shots/n33a_zfront.png` (forehead). Rollback `work/pre_neck/`.
- Checks r33 (`review/gates/`, installed sha256 86b89267d675...): winding 0; flat 0.00 / 0.00; arm/hand 0 frames > 1 cm every clip; robe
  0 every clip; jitter 0; bones 0 stretching; sleeve poke 0.0 mm every clip; texture quality body 63.5 %, head 56.4 %; see-through
  (`seethrough_neck/`, double=1): torso 48 px (Death from behind, as r21/r25), collar 2, sleeves 1-3, head 0 (the caps' removal opened
  nothing); floor ok x2; viewer check 22 switches, 0 failed; `mm9_actor_models_build_every_binding` PASS (252 descriptors on 114 models, `review/gates/regression_neck.log`). Full body vs MM9: `review/sheet_mm9_vs_ours_r33.png`.

## Pre-screen pass (orchestrator, 2026-11-04, r37, 20 credits): mouth rebuilt, fresh head paint
- **Mouth geometry first** (`tweak_pf7.py` MOUTH2, before the paint; r26-r33's post-paint unfold/lift retired): the head-shell positions
  in an ellipse round the closed slit (|x| < 3.2 cm, 1.1 cm above / 2.0 cm below LZ 0.6235, front, nose base excluded) Laplacian-relaxed
  in 3D (40 passes, eased at the rim): the folds, the tubercle peak, the jagged slit groove and the separate lower-lip pad gone; then subtle
  lips sculpted along -y as `mm9_peasantboy_claude/scripts/lip_sculpt.py` (upper +2.5 mm, lower +2.8 mm, closed groove -0.5 mm,
  mentolabial dip, philtrum groove, corners tucked and turned up 0.8 mm). 313 positions, the slit area's dense cavity moved up to 9.7 mm.
  Frozen `work/geom_final_v3.npz` (co hash b22511ad73b4fdc8) after clay renders (front, 3/4, profile, below) were read. Never moved after the paint.
- **Fresh Meshy 4K head paints** on that geometry: `texturing/pf7_head_upload_v3.glb` (same recipe as v2, verified byte-identical for v2),
  jobs pf7_head_a_v3 / pf7_head_b_v3 with the A/B head turnarounds (calm closed smiles), 10 + 10 credits (backup 2250 -> 2230; lease budget
  raised to 75 = 55 + 20). `compose_pf.py` -> pf_head_a/b_raw (normal + roughness from A), head AO rebaked on v3 (`head_upload.py`,
  `texpass_bake_ao.py` 0.04 m, 1024, `pad_ao.py`). v2 inputs kept in `work/pre_v3/`.
- Face fixes re-tuned to the v3 paint (it is clean: closed lips, soft line): the v2-specific steps are off - lip rose (`LIPROSE=0`), the
  9-texel light-speck median (`LIGHTSPK=0`, it drew blocks across UV islands), the philtrum box (`PHIL=0`), the padding erosion
  (`PAD_ERODE=0`, it refilled tiny lip faces from the cavity islands: orange specks); the nostril lift and the nose-underside repaint start
  above the upper lip (`NBOX_Z0` 0.6345, `UND_Z0` 0.6365). Neck graft steps kept (shared skin `NECK_TARGET` 243,168,120 from the v3 necks).
- **Nostrils / under-chin:** as F2 (NOSETILT: |x| < 2 cm, z 0.627-0.651, pits x +-6.8 mm z 0.643; CHINTILT 35 deg); underside paint toned
  to the skin (UNDER_SHADE 1.0), soft nostril shadows (NOST_COOL 0.62).
- **Groove shading:** the sculpted lips' closed groove still read as a dark centre; its down-facing upper side turned 40 % forward
  (MOUTH_NRM 0.4, |x| < 16 mm; normals only, on the final geometry and paint).
- Remaining: a soft dark line at the centre of the lips and the lower lip's underside shadow from below; tier A's red lid rims and strong
  freckles are Meshy's v3 paint.
- Checks r37 (installed sha256 43d0cff97cce...): winding 0; flat 0.00/0.00; arm/hand 0 frames > 1 cm; robe 0; jitter 0; bones 0; texture
  63.5 / 56.3 %; see-through (`review/gates/seethrough_mouth/`, double=1) torso 48, collar 2, sleeves 1-3, head 0 (unchanged); floor ok x2;
  viewer 22/0. `mm9_actor_models_build_every_binding`: 251 of 252 build; the failure is `MM9 266 Green Man` (another job's model texture
  not cooked yet), not rows 18/20 (`review/gates/regression_prescreen.log`). Sleeve poke not rerun (arms unchanged).
- Sheets (read): `review/sheet_mouth_nose_prescreen.png` (all four tiers, mouth+nose front and low 3/4, before/after),
  `review/sheet_face_r25_r37.png` (close-up, neck front, neck 3/4, 3/4, profile, low, party; both tiers), `review/shots/n37a_close.png`,
  `n37b_close.png`.


**LOD0 reduced post-install on 2026-11-04 by `level_generation/creatures/mm9_peasantf7_reduce_claude/`** (ledger: `level_generation/creatures/REDUCTION_LEDGER.md`, "MM9 reduction"). A rebuild from this project must re-run that reduction, or it silently restores the heavier mesh. Rollback source: `level_generation/creatures/mm9_peasantf7_reduce_claude/before/`.
