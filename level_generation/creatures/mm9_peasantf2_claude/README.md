# MM9 PeasantF2, the human townswoman with gold bell cuffs and a braid (mm9_peasantf2) — 3D actor, 2026-11-02

MM9 `PEASANTF2.abc` (73 joints, the human female skeleton of `PEASANTFEMALE`; rest pose identical to F5's, only its inverse binds differ)
with skins `PEASANTF2A` (golden-blonde woman, rust-orange dress) and `PEASANTF2B` (copper-red woman, teal dress, green/blue stone necklace).
`MONSTERS.txt` rows on this model, all Town and all NPCbase.scr (PeasantFemale library): **31** "Peasant Human1 FemaleB A" (F2a, DAT
`TownHumanFemaleA`, 1 placed), **32** "Human1 FemaleB B" (F2b, `TownHumanFemaleB`, none placed), **38** "Human2 FemaleB A" (F2a,
`TownHuman2FemaleA`, 2), **39** "Human2 FemaleB B" (F2b, `TownHuman2FemaleB`, 3). The objects' own scripts (NPC187/191/192/197) play no
animation (template comments only, empty ScriptParams). Built on the approved MM9 humanoid route (MM9 skeleton, MM9 `peasantfemale` clips).

**Why a new body:** `mm9_meshcmp.py peasantf2:peasantf1,peasantf5,peasantf8,yrsa`: bind differs by 16.7 cm (arms); posed by the same
library frame the arms agree within 1.3-1.5 cm, but torso p90 4.9-6.4 cm and head 2.2-2.8 cm from every built woman, and the design is
different (long sleeves with flared brocade bell cuffs, a close hair cap with one braid): a new body. F7 is not close either (torso 7.2 cm).

| Item | Value |
|---|---|
| Runtime GLB | `assets_source/worlds/mm9/models/mm9_peasantf2.glb` (r8, sha256 b1de5bbbca41...) = `export/mm9_peasantf2.glb`; variants `pf2_a` (rows 31, 38), `pf2_b` (rows 32, 39) |
| Binding | `assets_dev/worlds/mm9/models/actors.yml` block `mm9_peasantf2_claude`: `MM9 31 Town`, `MM9 38 Town` (pf2_a), `MM9 32 Town`, `MM9 39 Town` (pf2_b); F5's block values |
| Descriptors | rows 31, 32, 38, 39 in `tools/mm9_import_discovery/mm9_npc_actor_rows.tsv` (fallback visuals 352 / 353 / 379 / 380, the legacy replacements); ids 9031, 9032, 9038, 9039 (`scripts/bind_pf.py scripts/binding.json` under the flock) |
| Triangles LOD0/1/2/3 | 14,984 / 7,424 / 2,669 / 887 |
| Skeleton / clips | 108 joints (MM9's 73 + 30 MPFB finger bones + 5 helpers); Standing `stand1`, Walking `Walk`, Running `run`, Fidget `Fidget4`, Talk `Conv2`, Conv1, Conv3, Hit `Wince1`, Death `Die1`, Dead, Cower `cower` |
| Textures | body colour 2K, normal/ORM 1K, region mask 1K (R dress cloth: A rust / B teal; G necklace beads: A copper / B green-blue); head set (head + hair cap + braid) 1K colour per tier, normal/ORM 1K shared |
| Meshy credits | **35 / 50**: Smart Topology 5, body retexture 4K 10, head retextures 4K A 10 and B 10 (backup account; 2675 before the body job, 2610 before the last) |
| Codex | masters run 1 (one stuck session killed and rerun) + run 2, head turnarounds A/B (one stuck session rerun), face repaint A/B; all through `codex_slot.sh` |
| Viewer | http://127.0.0.1:8912/level_generation/creatures/mm9_peasantf2_claude/review/viewer/ revision `r8-20261102` |

## Route (`scripts/`; the F7 chain (`mm9_peasantf7_claude`, itself F1's) with F5's hand graft)

1. `convert_abc_model.py --scale 0.0256` -> `source/mm9/pf2a|pf2b`; MM9 refs `references_hd/mm9_*`; Codex masters (skin A).
2. Smart Topology 15k -> `step1_clean.py ... 1.7618`. One fused shell (face, dress with the sleeves and bell cuffs, skirt; apron and belt are
   paint), Meshy hands, hair cap, braid, a nape tie, 30 bead pieces, eyes, mouth inserts.
3. `seg_pf2.py` + `assemble_pf2.py` (X0 0.007): mirrored; head above the slanted neck plane; a clean waist plane cut (skirt label only within
   the torso: the bell cuffs hang below the waist line); sleeves pulled to MM9's arm length (x1.068) and turned 10.8 deg onto MM9's arm
   direction; the bell's closing disc (Meshy capped the cuff round its hand) pressed into a 7 cm funnel so the cuff reads open; F5's MPFB
   hands with a 3.5 cm stub held inside the cuff; Meshy's ears smoothed into the skull (MM9's hair covers them); bead necklace mirrored;
   mouth inserts dropped; skirt lining (Meshy's hem was open). `hair_fit_pf7.py` (cap only): within 0.7 cm of MM9's cap.
   A modelled side-hair panel was tried and dropped (it read as cheek guards).
4. `uv_pf.py` (never re-run: `work/uv_orig.npz`), `drop_needles_pf7.py` (26 faces) -> uploads. Body atlas 64.2 %, head 61.0 %.
5. Paint, AO, grade, `tiers_pf2.py` (masks from our paint + MM9's skins projected, `project_mm9_skin.py`).
6. Faces: `head_fix_pf2.py` (hair-hue fix; eye/nostril repaints OFF), `tweak_pf2.py` (F5's face tweak with F2 landmarks: lips back 2.2 mm,
   closed slit, nostrils, nose tip, eyeballs 3 mm deeper, lids; plus **the hair cap's lower side rows stretched down over the ears to the jaw**
   (cheek 0.632 -> side 0.603 -> nape 0.598, rounded under, the band Laplacian-smoothed) and the hidden shins slimmed 15 %), Codex face repaint
   by landmarks -> `align_face_pf2.py` (lips thickened x1.3 about the lip line: the modelled lips are fuller) -> `project_face_pf2.py`.
   Head normal map neutral only on the ~200 nose-underside/columella faces (corrupt Meshy normals there).
7. `line_rims_pf2.py`: a 1.2 cm lining inside the hair cap's open rim, caps (head neck bottom and skull opening, the dress waist, the hand stubs), `rig.sh` (weights: hair rigid on Head, braid
   on Ponytail11/12 with up to 60 % Spine3 at its end, beads rigid per bead, F5's rigid hand stub), `build_runtime.sh` (`double_head.py`: the
   head-set materials doubleSided, so the hair shell's inside shows hair under the rim; the engine flips their back-face normals). `rebuild.sh <rev>`.

## Checks (final r8, `review/gates/`)

| Gate | Result |
|---|---|
| `arm_hand_gate.py --outer-only --exact` | **0 frames > 1 cm, every clip, both hands** (hand depth <= 0.2 cm; Conv3 L forearm touches 1.0 cm in one frame) |
| `skin_poke_gate.py` (hand stub through the sleeve/cuff) | **0.0 mm every clip** |
| `robe_gate.py` (legs through skirt) | **0 frames in all 11 clips** (r6: Death 0.4 / Cower 0.7 / Dead 0.9 cm before the shins were slimmed) |
| `jitter_gate.py` | 0 fails |
| `flat_shading_check.py` | 0.00 body, 0.00 head |
| `bone_length_audit.py` | 14 checked, 0 stretching |
| `detached_parts_audit.py` | 5 flagged: the free legs/shoes inside the skirt (by design, as F5/F8) |
| `check_winding.py` | 0 inverted closed parts |
| `floor_audit.py --world mm9` | MM9 31/32/38/39 ok: stand -0.2, walk -0.1..+1.4, living -1.1, dead 0.0 |
| `texture_quality.py` | body atlas 64.2 %, spread 3.41 (hands/legs/lining factors by design), fragments 0.5 %, stretch 1.05; head atlas 61.0 % (density p10 0 = the hidden cap fans) |
| `see_through_gate.py` | r7 (all faces culled): sleeves **0** (bell funnels), collar 2 px, head 212 / torso 256 px = the hair cap's inside seen under its rim. r8 with `double=1` (doubleSided head set drawn from both sides, as the engine): head 0, torso 9 px (Death), sleeves 0, collar 2. r12 (face pass 2): head 0, torso 9, collar 2, sleeves 0-1. Open: the cap inside now shows as a light flap behind the ear at the braid top |
| `mm9_actor_models_build_every_binding` | PASS (240 descriptors on 105 models, 0 failed) |
| Viewer check | 22 switches, 0 failed |
| Sheets (read) | `review/sheet_mm9_vs_ours.png`, `review/sheet_128px.png`, faces `review/sheet_r8a_face.png`, `review/sheet_r8b_face.png`, `review/flat_f2a.png`, `review/sheet_asmhead.png`, `review/mm9skin_proj.png` |

## Deviations and open points
- MM9's F2 hair is a low-poly cap over the ears; ours is Meshy's cap stretched down to the jaw: its strand paint is lengthened there.
- Tier A's embroidered chemise front and B's lacing come from the one body paint (A's design); B differs only by the ramps (teal dress,
  green/blue beads).
- The bell cuffs' insides are the pressed funnel, painted with the cuff's own texels.

## What was not checked
In game (no map places these descriptors yet). LOD1-3 and shadow meshes by eye. Motion at normal speed by eye.

User artistic acceptance: not recorded

## Face pass 2 (coordinator review 2026-11-02, r12, 20 credits)
Review of r8: a light flap of cap inside behind the ear at the braid top; jagged hair side edges standing off the cheeks; the face flat and
pale with the nose barely there (my F5-derived face tweak had smoothed the nose tip and nostrils away), lips puffy/parted from below.
- Geometry first (`tweak_pf2.py` with `scripts/tweak.env`): Meshy's nose and lips kept intact (no midline pull, snap, fin collapse, nose or
  nostril smoothing, no lip pull-back); the lip slit closed by the unfold with a 0.5 mm dome; eyeballs 3 mm back, upper lid rim 2 mm down;
  the hair cap's lower rim loop smoothed along itself and tucked 1.5 mm off the skin (rings 0.6 / 0.3) - no inside shows, no side flaps;
  midline cracks welded (open-boundary vertices within 4 mm of x = 0 snapped). Frozen as `work/geom_final_v2.npz` (hash dc19914f54b5e9d8,
  identical after every later rebuild).
- Fresh Meshy 4K head paints A and B on that geometry (`texturing/pf2_head_upload_v2.glb`, jobs pf2_head_a_v2 / pf2_head_b_v2, 10 + 10;
  backup 2420 / 2410 before). The Codex projection is retired (`work/pre_v2/`); head normal map unmodified.
- Paint finish only (`head_fix_pf2.py` PASS2): lip red toned to rose (lip-red texels only), light specks in mouth/philtrum to the local
  median, nostril paint lifted to 75 % of the nose skin, a soft lid shade over the top of each eyeball, forehead midline band gain.
  Forehead midline vertex normals relaxed in `build_glb_pf.py` (the mirrored halves meet at a slight ridge that read as a pale band).
- Sheet (read): `review/sheet_faces_pass2_before_after.png` (both tiers, r8 vs r12: front close-up, 3/4, profile, low, party).
  Remaining marks: from the low view the lips still read slightly apart (Meshy's lip form, slit closed); a small notch in the cap's lower
  back edge in profile; eyes a little round; the under-chin reads dark from below (paint/AO).
- Credits now **55** (35 + 20).

## Nostril pass (coordinator, 2026-11-03, r15, 0 credits)
Nostrils as small soft cool shadows on the real openings (x +-7.4 mm, z 0.6485), the nose underside paint at 1.2x the nose skin, the nose
base paint floored at 90 % of the skin (`head_fix_pf2.py` PASS2 7). The brown blobs are gone; the remaining darkness is the geometry's own
shading in the alar creases. Sheet `review/sheet_pass3_nostrils.png` (r12 vs r15, both tiers). Installed sha256 6a0ea69d6b91...; binding
PASS (248/110); floor ok x4; viewer 22/0. Geometry unchanged (dc19914f54b5e9d8). Rollback `work/pre_pass3/`.

## Neck graft pass (user review 2026-11-04, r19, 0 credits)
User: "the head graft transition not good, I can see it like it was soldered on her body" (`review/user_20261104/neck_graft.png`), plus a
midline line down the forehead/bridge/neck and dark nostrils. Causes found, and fixes (all scripted, `scripts/rebuild.sh` replays them):
- **Dark jagged band along the graft = shading, not paint.** `line_rims_pf2.py` closes the head's neck bottom with a fan cap (`inner`);
  its large down-facing faces were summed into the seam vertices' normals (median normal z -0.93 instead of +0.65), so the whole seam
  ring was lit from below. `build_glb_pf.py`: positions that have outer faces take the outer faces' normal only (292 positions changed:
  the neck seam, the hair rim lining, the hand-stub and skirt-lining rims).
- **Thin dotted line on the seam** (left after the band): the cap's rim z-fought with the seam. The cap is not needed (the head ring is
  welded to the dress's neck loop): dropped in `build_glb_pf.py` (`NECK_CAP=1` keeps it). LOD0 15,000 -> 14,936.
- **Midline crack at the throat:** the dress loop had 4 extra mirror-seam vertices and its own midline vertex 0.2 mm off the head's;
  projected onto the head ring (5 vertices, max 0.33 mm; head unmoved).
- **"Orange chest" = wrong region.** MM9's upper chest inside the neckline is skin (both skins), but its paint passed the rust-hue test
  and took the dress ramp (A orange, B green). `tiers_pf2.py`: that skin is its own region (mask B channel) with a per-tier ramp mapped
  onto that tier's neck skin (head paint 0.5-5.5 cm above the seam); near the seam its low frequencies are flattened to the chest median;
  the throat strip between the seam and the beads (a painted gold tick) is skin; skin-island padding takes the nearest covered texel
  (the rust padding drew a dark line through the GPU filter).
- **Tier B choker:** Meshy painted a choker (green dots, violet stone, copper lace) on the bottom 1.7 cm of head B: those texels take the
  skin 2.2 cm higher at the same place round the neck (`head_fix_pf2.py` (8), `NECK_CLONE=b`); both tiers' neck paint is then feathered
  to the neck's median skin within 3.2 cm of the seam; gold/brown outliers on the bottom 1.5 cm (midline slivers) replaced.
- **Midline line:** neck and bridge/forehead vertex normals within 7 mm of the midline blended from both sides (F7's pass-3 "SEAM
  normals", now z 0.515-0.575 on the neck and 0.668-0.785 above the nose tip; the nose tip, nostrils, mouth and chin are left alone:
  a first try up to the under-chin drew a dark goatee). Paint: the 1.6 mm mirror line takes a gain to the skin 2-3.5 mm aside (head
  9b, neck and face; body chest likewise). Tier A's forehead band (Meshy painted the middle UV island lighter, then the old flat gain
  (6) made it darker, sharp edges ~1 cm either side): replaced by a profile equalisation (6b, `FH2=1`) above the brows.
- **Nostrils:** cool nostril colour 0.68 -> 0.82 of the nose skin, underside 1.2 -> 1.3x. No visible change: the remaining dark is the
  geometry's own shading of the nostril openings and the columella shards (paint already at the 255 ceiling in R). Not fixed: it needs
  a normal relax on the nose underside, which the face rules forbid. Left for the orchestrator/user.
- Rollback: `work/pre_neck/` (r15 GLB, textures, scripts).
- Checks r19 (`review/gates/`, installed sha256 956a91f002e3...): winding 0; flat 0.00 / 0.00; arm/hand 0 frames > 1 cm every clip; robe
  0 every clip; jitter 0; bones 0 stretching; detached-parts audit unchanged from r15 (same parts); texture quality unchanged (body 64.2 %,
  head 61.1 %); see-through (`seethrough_neck/`, double=1): torso 9 px (Death, as r12/r15), collar 2, sleeves 0 (r15: L 1), head 1 px
  (Conv3 frame 66 side view, at the left bell cuff, not the neck); `--headless-validate-actor-models` 250 descriptors / 112 models, 0
  refused; floor ok x4; viewer check 22 switches, 0 failed. `mm9_actor_models_build_every_binding` first failed on `MM9 256 Fre` (another
  job's row in progress); rerun after F7's install: PASS (252 descriptors on 114 models, 0 failed; `review/gates/regression_neck_final.log`). Not rerun: the hand-stub skin-poke gate (arms, hands and
  weights unchanged).
- Sheets (read): `review/sheet_neck_r15_r19.png` (r15 vs r19, both tiers: close-up, neck front, neck 3/4, 3/4, true profile, low 3/4,
  party), `review/sheet_mm9_vs_ours_r19.png` (full body vs MM9), zooms `review/shots/n19a_close.png`, `n18a_zfront.png`.
- Open: nostrils (above); the under-chin reads dark from below (geometry shading, unchanged); the mouth's slit has 22 backward-facing
  front faces (94 mm2) like F7's had - the user did not flag F2's mouth, so F7's unfold/groove fix was not applied here.

## Pre-screen pass (orchestrator, 2026-11-04, r20, 0 credits)
- **Nostrils** (dark brown T under the nose in every front close-up): Igrid's accepted fix (`mm9_wyrdold_claude`, "Pre-screen pass").
  `build_glb_pf.py` NOSETILT: only the nose underside's downward normals (|x| < 2 cm, z 0.632-0.656, eased by how far down they point) are
  turned toward the front, to at most 20 deg below horizontal; the real nostril pits (x +-7.4 mm, z 0.6485) keep 70 % of their own normal;
  bridge, tip front and wings untouched (34 positions). Paint: underside toned to the nose skin (UNDER_SHADE 1.2 -> 1.0), the nostril
  shadows small and soft (NOST_COOL 0.62). Glb normals are in glTF axes (up +y, front +z).
- **Under-chin** (dark wedge from below): CHINTILT, the under-chin's downward normals (|x| < 5 cm, z 0.56-0.60) to at most 35 deg below
  horizontal (47 positions).
- **Mouth:** F2's closed slit had the fold F7 had (24 front faces facing backward = drawn as their back side). No head repaint credits for
  F2 in this job, so the fold is fixed the cheap way, inside the lip-red texels: MOUTH unfold (24 -> 0 backward faces, 39 positions,
  <= 1.44 mm, post-paint) + the groove's down-facing upper side turned 60 % forward (|x| < 18 mm) + `head_fix_pf2.py` (12): the lip
  underside to the lip-front colour, the crease to 0.8x of it (tier B had white teeth painted in the slit). **Deviation** from "never move
  face geometry after the paint / never edit mouth normals": the proper fix (F7's MOUTH2 geometry + a fresh 4K head paint) costs 20 credits.
  Remaining: faint jagged lines inside the lips at close range and a ~1 mm dark speck at the upper lip in the low 3/4.
- Checks r20 (installed sha256 97177d5e7ed9...): winding 0; flat 0.00/0.00; arm/hand 0 frames > 1 cm; robe 0; jitter 0; bones 0; texture
  64.2 / 61.1 %; detached audit unchanged. See-through not rerun (mouth positions moved <= 1.44 mm inside closed lips; r19 numbers stand).
- Sheets (read): `review/sheet_mouth_nose_prescreen.png` (F2 A/B and F7 A/B: mouth+nose front and low 3/4, before/after),
  `review/sheet_face_r15_r20.png` (close-up, neck front, neck 3/4, 3/4, profile, low, party; both tiers).

## Second pre-screen pass (orchestrator, 2026-11-04, r24, 20 credits): mouth and columella rebuilt, fresh head paint
r20's post-paint mouth patch read jagged and the nose underside kept a pointed columella wedge, so F2 went the F7 way:
- **Geometry first, frozen before the paint** (`tweak_pf2.py`, `work/geom_final_v3.npz`, co hash 6ab4ed0a76f401ac): MOUTH2 as F7
  (3D relax of the slit region - folds, groove and lower-lip pad gone - then the lip_sculpt profiles: upper +2.5 mm, lower +2.8 mm, closed
  groove -0.5 mm; the zone stops 8.5 mm above the line and the philtrum groove is off: they drew a V under the nose); NOSE2 (new): the
  columella between the nostrils (|x| < 6.5 mm, z 0.6345-0.652, behind the tip front, facing down) relaxed into a rounded septum (50
  positions, <= 2.9 mm); bridge, tip front and wings untouched. Clay renders (front, 3/4, profile, below) read before the paint.
- **Fresh Meshy 4K heads** pf2_head_a_v3 / pf2_head_b_v3 on `texturing/pf2_head_upload_v3.glb` (recipe verified byte-identical for v2),
  10 + 10 credits (backup 2230 -> 2210; lease budget 75 = 55 + 20); composed (normal/roughness from A), head AO rebaked on v3. v2 maps in
  `work/pre_v3/`.
- **Face fixes:** the steps that damaged F7's v3 paint are off (`LIPROSE=0`, `LIGHTSPK=0`, `PAD_ERODE=0`, `NBOX_Z0` above the lip, the
  r20 mouth patch `MOUTH_UNFOLD=0`/`MOUTH_LIFT=0`); the nose underside keeps its own v3 colour (`UND_RECOLOR=0`) with only the small soft
  nostril shadows. Neck graft steps (r19) kept.
- **Normals only, on the final geometry:** NOSETILT 12 deg below horizontal with the septum's side facets half-turned too (`NOSE_DEG=12`,
  `NOSE_NXK=0.3`: the smoothed septum still shaded as a soft brown triangle at 20 deg), CHINTILT 35 deg, the lip groove's down-facing
  side 40 % forward (`MOUTH_NRM=0.4`, as F7 r37).
- Checks (r23 geometry = r24; installed r24 sha256 1834cf18534990cd): winding 0; flat 0.00/0.00; arm/hand 0 frames > 1 cm; robe 0;
  jitter 0; bones 0; texture 64.2 / 61.1 %; see-through (`review/gates/seethrough_v3/`, double=1) torso 9, collar 2, sleeves 0, head 1
  (the bell-cuff pixel, as r19); floor ok x4; viewer 22/0; `mm9_actor_models_build_every_binding` PASS (252 on 114,
  `review/gates/regression_v3.log`).
- Sheets (read): `review/sheet_mouth_nose_v3.png` (mouth+nose front and low 3/4, both tiers, r19 vs r24), `review/sheet_face_r19_r24.png`.
- Remaining: a darker zone between the eyes at the inner corners (bridge geometry shading, also in r15-r19; lid shade on/off made no
  difference), the lower lip's underside shadow from below, faint lattice texture on tier B's lower lip (Meshy paint).


**LOD0 reduced post-install on 2026-11-05 by `level_generation/creatures/mm9_peasantf2_reduce_claude/`** (ledger: `level_generation/creatures/REDUCTION_LEDGER.md`, "MM9 reduction"). A rebuild from this project must re-run that reduction, or it silently restores the heavier mesh. Rollback source: `level_generation/creatures/mm9_peasantf2_reduce_claude/before/`.
