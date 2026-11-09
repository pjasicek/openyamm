# MM9 Igrid, Wyrde of the Known (mm9_wyrdold) — 3D actor, 2026-11-02

MM9 `MONSTERS.txt` row 263 "Wyrde of the Known (Igrid)", `wyrd_old.abc`, skin `wyrdold.dtx`, basemelee.scr, BaseName PeasantFemale.
One tier. Own GLB `mm9_wyrdold.glb`.

## Route decision: a new body (not a Wyrde or Yrsa variant)
`mm9_meshcmp.py wyrd_old:wyrd_young,hag,yrsa` (`review/mm9_compare_old_young_hag_yrsa.png`):
- vs the built Wyrde (`wyrd_young`, frozen): the same 73 joint names but the bind differs by up to 26 cm (wyrd_old is stooped, the head and
  neck thrust forward), torso p90 10.8 cm after a rigid shift: not the Wyrde skeleton, so no Wyrde variant.
- vs Hag / Yrsa: the same skeleton (bind within 8 cm: the braid chains) and the same five clips (`stand`, `fidget1`, `walk`, `Wince3`,
  `Die3`), but the body is a different design: a full-length open brown robe with full sleeves and a deep hood over a navy gown (torso p90
  6.9 cm, the robe's volume). Yrsa's dress would be completely covered and the robe would have to be built from scratch.
So one new Meshy body on the approved MM9 humanoid route (the Wyrde's scripts: hood + mantle-like robe + gown), rigged on wyrd_old's OWN
stooped skeleton with its OWN clips (the Yrsa clip set, Yrsa's role table and floor operations).

## Clips (what the scripts play)
DAT objects: Hall of the Gods `WyrdeoftheKnown0` and Dark Passageway `WyrdeoftheUnknown0` (class WyrdeoftheKnown = row 263, `NPC338.scr`:
voice and quest only). `WG_NPC334.scr` (win cutscene) only toggles the Wyrdes' visibility, solidity and gravity; its `PlayAnim` calls are on
Hanndl. No script plays a clip on Igrid, so MM9's roles only, from wyrd_old.abc's own clips: Standing `stand`, Walking `walk`, Running
`walk` x1.45 (as Yrsa), Fidget `fidget1`, Hit `Wince3` (skirt chains damped 0.6, as Yrsa), Death `Die3`, Dead. No attack clip: attacks play
Fidget (as the Wyrdes and the Hag).

## Route (`scripts/`)
0. `convert_abc_model.py --scale 0.0256` -> `source/mm9/wyrd_old/`; `mm9_dump.py` -> `work/mm9.npz`; reference renders (`ref_renders.py`).
1. HD masters (Codex via `codex_slot.sh`, `references_hd/CODEX_BRIEF.md`, `codex_masters.sh` 1 and 2): stooped, kind 85-year-old, open brown
   robe, navy gown; `clean_alpha.py`; sheet `review/masters_vs_mm9.png`. Head turnaround `references_head/` (`codex_heads.sh`): calm warm face.
2. Smart Topology 15k from `00_three_quarter_clean.png` -> `step1_clean.py` (height 1.69) -> `work/raw.npz`.
3. `assemble_wo.py`: robe shell (+ cuff ring) mirrored from +x (the two small back holes were on -x), face shell mirrored, flat hair plates on
   the forehead deleted, circlet gem kept, eye spheres, braids paired, gown skirt mirrored, the +x shoe on MM9's foot with a shin tube, sleeves
   turned (9.5 deg) and scaled (x0.76) onto MM9's arm, MPFB female hands (172 mm) with forearm stubs into the cuffs; robe reduced to 5k.
4. **Face geometry before any paint** (`face_geo_wo.py`): Meshy's mouth was parted and pursed (a loose lip shell over it, a hole in the lower
   lip, a slit into a cavity). The loose shell (assemble) and the cavity island are removed, the mouth patch (ellipse 2.6 x 1.55 cm) is
   rebuilt from a symmetric lattice (Delaunay, min angle 21 deg), its depth a membrane from the rim plus subtle closed lips (upper +0.7 mm,
   lower +1.2 mm, corners lifted 0.8 mm), the rim band depth-smoothed. Lids opened (upper 12 deg, lower 7 deg): Meshy's eyes were a 3 mm slit.
5. `uv_wo.py` (never re-run: the paid paints belong to `work/uv.npz`): body 2K 60.1 %, head set (face 1.7x, eyes, gem, braids) 62.2 %.
6. Paint: body + head retextures 4K (`make_upload.py`, `make_upload.py ... head`), AO bakes (`texpass_bake_ao.py`, `pad_ao.py`), `compose_wo.py`,
   `finish_wo.py` (gentle grade). `head_fix_wo.py` and `body_fix_wo.py` (below).
7. After the paint (positions only, UVs unchanged, no face-shell vertex moved): `tweak_wo.py` (gem halved, shin tubes shortened to 30 cm),
   `linings_wo.sh` (below).
8. `rig_wo.sh` (fit_rig_wo, weights_wo, build_glb_wo, clips_pf with `roles_wo.json`, finger_rest, arm_out 3 deg, `arm_jobs_wo.txt`,
   `hand_rest_wo.txt`, half_keys) -> `build_runtime_wo.sh [--install]` -> `viewer_update.sh <rev>`. `quick_face.sh <rev>` runs 7-8 plus face shots
   (`work/hv2/build_r13.sh <rev>` is the same chain with a 2026-11-04 revision tag).

### Head paint fixes (`head_fix_wo.py`, face pre-screen in the viewer, `review/face_r1..r7_sheet.png`)
Meshy painted the thin braid cords the hood's brown (-> warm grey with a three-strand plait pattern), the head shell above the face (scalp and
temples inside the hood) the hood's maroon so the face read as a mask (-> grey hair in the hood's shade), a maroon swag on the forehead
(-> local skin), the wrinkles as a net of dark thin lines (softened 65 %, wrinkles kept), dark nostrils and lip dimple (lifted), a pinkish
lip (saturation x0.8). Review round 2 (coordinator): the grey hair above the circlet read as a bald grey skull cap -> a soft ivory linen
coif (linen colours, a fine weave and fold shading) continuous under the hood rim; the wrinkle net (an orange line net) dropped further
(`NET DROP` 0.022, `NETK` 0.9, closing 7) into soft creases; the eye zone kept (`face_r10`, `face_r11_sheet.png`). The circlet: a thin gold band and a small ruby gem on the gem piece's own faces. `body_fix_wo.py`: the neckline inside the
hood opening (pale cream, the pearl choker smeared) -> the hood's dark cloth.

### Weights (`weights_wo.py`)
Robe and gown below the waist analytic over MM9's eight skirt chains, spine heights and clavicles above, sleeves along the arm; the hood
(robe shell within 26 cm of the head and above the jaw plane) rigid on Head with a cowl band to Neck / Spine3; face rigid on Head above the
jaw plane; braids on MM9's braid chains (`xpony`, `xpony_a`); MPFB hands; shoes and shins on Calf / Foot / Toe0; half-joint helpers.

### Linings (`linings_wo.sh`)
Faces seen from behind at rest (`visible_backfaces.py`, 483) and in posed frames (`posed_backfaces.py`, 1593 polygons, Standing ... Dead),
plus the open lower hem and front-edge bands of the robe (below -0.30 m) and of the gown, doubled 2 mm behind themselves with rim strips:
1527 twin faces, 223 rim edges. Round 2: posed back faces re-collected on r3 plus Death 0.35-0.5 s (`work/posed_backfaces.npy`: the
mid-fall view into the crumpled robe and the right sleeve), a robe hood box and robe/skirt loops (`linings_wo.sh`); LOD0 14,821 triangles.

### Head paint v2 (finishing round, 2026-11-04)
The first head paint had needed more than two patch passes (r1-r11) and still read wrong in the coordinator's round-2 review: the coif a
flat white cap, the skin blotchy from the net closing, orange/white bands under the eyes, almost no wrinkles left. So a fresh paint on the
final head mesh (face geometry unchanged since `face_geo_wo.py`):
- Codex head turnaround v2 (`references_head_v2/`, `scripts/codex_heads_v2.sh`, brief in that folder): the approved turnaround corrected
  only by an ivory linen coif with folds under the hood (circlet on its lower edge), soft natural creases instead of a wrinkle net, a
  gentle closed smile and warmer skin. Read and accepted (`references_head_v2/selected_views_review.png`).
- Meshy head retexture 4K `wo_head_v2` on `texturing/wo_head_upload_v2.glb` (`make_upload.py work/uv_tw.npz ... head`: the final head
  geometry on the same UVs), 10 credits; `compose_wo.py wo_head_v2 head`. The v1 maps are kept in `work/head_v1_backup/`.
- `head_fix_wo2.py` (replaces `head_fix_wo.py` for v2): Meshy painted the scalp as a dark hair fringe down to the brows (the hood is not in
  the head upload) and no brows. Braids, gem and band as v1; the coif from the Codex v2 front view projected from the front (x by the eye
  spacing, z anchored on the eyes and the circlet gem, `CU CV CA ZB VE`) where it shows white linen, over v1's procedural linen elsewhere;
  the forehead and brows below the band from the same projection, toned to Meshy's cheek skin (saturation x0.8); net and lifts off;
  the upper lip x1.12 (`UL`).
- A dark moustache-like band above the upper lip was SHADING, not paint (`work/hv2/raster.py`: unlit texture vs Lambert shading of the
  head primitive): the rebuilt mouth patch's upper rim. `build_glb_wo.py` relaxes the normals of that band only (`ULRELAX` 4 passes,
  |x| < 3 cm, z 0.4885-0.4995, positions and UVs unchanged; the lips and nose are outside it).
- Face sheets `review/face_r13..r15_sheet.png`; r15 installed, then the orchestrator's pre-screen pass below.

### Clean cuff rims (orchestrator pre-screen of r22, 2026-11-04: "a jagged, spiky collar round each wrist") -> r42
Diagnosed with `work/hv2/joint_raster.py` (posed faces coloured by dominant joint; `ONLYNEAR=L VERTS=hand` draws only the geometry within
3 cm of the forearm axis) and `work/hv2/posed_flip.py`: the teeth were the MPFB hand's forearm STUB (a sparse cone of long thin triangles
with a zig-zag cut end, painted dark, showing through the gathered cuff opening) plus Meshy's crumpled rim and an inner sleeve layer folded
in toward the wrist. What r42 keeps (`tweak_wo.py`, positions only, UVs unchanged):
- step 4 CUFFS: taper over 14 cm (was 10) to 45 % radius;
- 4b RIM: the sleeve end stretched along the forearm so its end sits 1 cm behind the wrist joint (`RIMEND`), its vertices at least 3.4 cm
  off the forearm axis (`RIMCL`), the inner folded layer pushed out to 2.4 cm (`INNCL`, inside the outer layer). The relaxation passes
  (`RIMIT`) are OFF: relaxing the rolled rim folded it into back faces (see-through sleeves 79-85 px in r34-r41) and pulled the rim 7.3 cm
  up the arm (r30: hands hanging free);
- 3b STUB CYLINDER: the stub behind the wrist becomes a clean tube (every stub vertex on one end circle 5.4 cm behind the joint, at the
  wrist ring's radius), with a repair pass that pulls back vertices of any triangle the move would flip;
- `linings_wo.sh` `LINE_CUFF=0.065`: the last 6.5 cm of each sleeve lined whole.
Tried and dropped: a 1.4x stub (stretched spikes, r24), a distance-only wrist-ring weight ramp (`WRISTRING`, off: no gain), pulling the
rim 1.5 cm back without restoring it.
Gates r22 -> r42: sleeve poke 0 -> 0; see-through sleeves worst 28 -> 28 px (Hit L); arm/hand Death R 3.7 -> 3.6 cm (1 f), Death L 1.6
cm 4 f, Dead L 1.8 cm 6 f (unchanged); robe 0; jitter 0; LOD0 14,973 -> **15,067 triangles (67 over the 15k ceiling: the cuff linings)**.
Sheets: `review/cuff_rim_zoom_r22_vs_r42.png` (Standing, close front of both wrists; r22 top, r42 bottom), `review/cuffs_before_after_a.png`
/ `_b.png` (front + 3/4 low, two frames each of Standing, Walking, Fidget, Hit, Death, Dead; r22 vs r42). **Left: one small dark V notch on
top of each wrist in the closest views** (where the wrist top meets the cuff's inside), not fixed.

### Fitted undersleeve and recentred bell (user review r43: "hands still out of the sleeves") -> r45
From the user's angle (front, slightly above, Standing 0) the navy band and hand hung below and in front of the bell, which showed its
empty brown inside. Two causes: there was no arm inside the bell (only the hand's 5 cm stub), and Meshy's bell hangs 3-5 cm in FRONT of
MM9's forearm axis (`asm_tw` sleeve-end centre offset 0.044 m), so the forearm left through its back/lower wall.
- `tweak_wo.py` 3c RECENTRE: the sleeve's last 20 cm shift sideways by minus their mean offset from the forearm axis (eased in from 20 cm
  to 6.7 cm behind the wrist); centre offset near the opening 0.044 -> 0.003-0.009 m.
- step 5 UNDERSLEEVE: the band is now the cuff of a fitted 8-segment navy tube from the wrist up the forearm to the elbow and 4 cm up the
  upper arm (radius 2.4 cm at the wrist to 3.8 cm past the elbow), inside the bell; `weights_wo.py`: Forearm below the elbow, UpperArm
  above, blended across the elbow (smoothstep -3..+4 cm), no Hand share. The bell's turned-in inner layer goes out to 2.9 cm (`INNCL`), clear
  of it. The hand's stub faces wholly inside it are deleted (`STUBDEL`, 8 faces).
- LOD0 15,101 (101 over 15k: the undersleeve; the cuff-end linings stay off).
Gates r43 -> r45: sleeve poke 0 -> 0; see-through sleeves worst 16 -> 13 px (torso Standing 30 -> 43, Fidget 38 -> 46, Running 52 -> 60
px, Death/Dead unchanged); robe 0; jitter 0; flat 0.00; arm/hand unchanged (Death R ~3.6 cm 1 f, L 1.6 cm 4 f, Dead L 1.8 cm 6 f);
floor ok; viewer 0 errors; regression PASS 252 on 114.
Sheet `review/undersleeve_r43_vs_r45.png` (Standing 0, Walking 0.3, Fidget 1.0, Hit 0.15, Death 0.3; each from the user's angle, 3/4,
low 3/4 and side; r43 vs r45); zoom of the user's angle `work/hv2/us_front_zoom45.png`.

### Undersleeve bands (orchestrator pre-screen of r42: "a dark V sliver on top of each wrist") -> r43
Diagnosis (`work/hv2/part_raster.py`: Standing wrists, faces in flat part colours by nearest rest face of `work/uv_tex.npz`, hand
orange, stub green, sleeve outer blue, lining yellow, back faces magenta; `work/hv2/parts_AB.png`): the V was neither an open cut end nor
a gap nor the inner sleeve layer: it was the hand/stub junction's long thin triangles (hand-labelled, lying almost edge-on, so they render
dark) running from the wrist ring to the stub's end circle, with the stub tube itself standing out of the gathered cuff on top. The hand
and stub are one closed skin tube (no open end, no gap).
Fix (`tweak_wo.py` step 5, `weights_wo.py`): a navy undersleeve band round each wrist, coming out of the cuff: a 10-segment tube 2.5 cm off
the forearm axis from 4.5 cm behind the wrist joint to 0.4 cm behind it, its hem folded 3 mm inward (a clean ring 6 mm off the wrist
skin), robe part on the body material with UVs on a small patch of the gown's navy, 100 % on the Forearm (as the Green Man's bracelets).
It hides the junction in every clip. Budget: the cuff-end linings (`LINE_CUFF`) are off again and the band has no inner wall
(`BANDWALL`, 40 faces): LOD0 14,982.
Gates r42 -> r43: sleeve poke 0 -> 0; see-through sleeves worst 28 -> 16 px; robe 0; jitter 0; flat 0.00; arm/hand Death L 1.6 cm 4 f,
Dead L 1.8 cm 6 f, Death R ~3.6 cm 1 f (unchanged); floor ok; viewer 0 errors; regression PASS 252 on 114.
Sheet `review/wrists_r42_vs_r43.png` (Standing close front and 3/4 low of both wrists, Walking 0.3 s, Fidget 1.0 s and 2.2 s, Hit 0.15 s;
r42 left, r43 right).

### Pre-screen pass (orchestrator, 2026-11-04; paint and normals only, no position moved, no credits)
- **Nose blot** (front, low, under): the paint there is clean skin (`work/hv2/raster.py` with `ROT=-50`: `work/hv2/raster_low.png`, unlit
  left vs shaded middle); the blot was the hemisphere's dark ground term on the large downward-facing nose underside of a head tilted
  forward. `build_glb_wo.py` NOSETILT turns only that underside's normals (|x| < 2.2 cm, z 0.497-0.52, normals > ~27 deg below horizontal)
  toward the front, to at most 20 deg below horizontal; the nostril pits keep 70 % of their own normal. `head_fix_wo2.py` step 8 tones the
  underside paint to the nose-side skin (x1.06) and paints small soft shadows in the real nostril openings (NOSTRILK 0.38).
  This deviates from the face lesson "never relax a Meshy nose's normals": the bridge, tip front and wings are untouched and the nose's
  shape reads the same in front and 3/4 (`review/nose_r15_vs_r19.png`).
- **Age** (step 7): the Codex v2 front view's creases (crow's feet, under-eye folds, nasolabial folds, forehead and cheek lines, jaw sag)
  multiplied onto the face skin (Codex luminance / its 7 px blur, `AGEK` 0.75), projected from the front with a landmark height map
  (eyes 0.550 -> v 471, nose base 0.503 -> 617, mouth 0.4855 -> 647), weighted by how much the texel faces the front; the eyeballs and the
  lips keep their own paint (no second lip line); skin warmed (`WARM` 1.05, 0.97, 0.91) and the cheeks flushed from the Codex view's own
  redness. No painted smile beyond the Codex creases at the mouth corners (the lips' geometry is neutral).
- **Coif edge** (step 9): by 3D distance to the face edge, the coif darkens over 1.8 cm toward the face (up to 55 %: the cloth turning in)
  and the skin within 6 mm of the coif takes its cast shade (35 %) (`review/coif_edge_r15_vs_r20.png`).
- Face sheets `review/face_r16..r20_sheet.png`; r20 installed.

### Hands into the sleeves (user review r20, 2026-11-04: "her hands are not in her sleeves")
Cause: Meshy's bell sleeves open to a cuff of ~8.5 cm radius round a ~2.5 cm wrist, and MM9's wrist is bent 34-59 deg down in Standing,
Hit, Fidget and Walking (`work/hv2/cuff_probe.py`). The wrist joint sits at the cuff rim and the stub is weighted to the forearm
(`work/hv2/stubw.py`), so the hand turned down out of the lower edge of the wide opening and the cuff above it showed its dark, empty inside.
Fix (r22), no change to the hand mesh or the face:
- `tweak_wo.py` step 4 CUFFS: the last 10 cm of each sleeve taper toward the forearm axis to 45 % of their radius at the rim (smoothstep).
- `weights_wo.py` cuff rim: the last 6 cm of each sleeve take up to 35 % Hand weight (from Forearm), so the opening turns toward the hand.
- `wrist_clamp.py` (the Scholar's, FHP names) via `scripts/wrist_clamp_wo.txt` in `rig_wo.sh`: the hand's bend from its bind limited to
  30 deg (knee 20) in Standing, Walking, Running, Fidget and Hit, 34 deg (knee 24) in Death and Dead (was up to 59 deg).
Before/after (viewer, front, 3/4 low, back and side at two frames of each clip): `review/hands_stand_walk_before_after.png`,
`review/hands_fidget_hit_before_after.png`, `review/hands_death_before_after.png`; close-ups `work/hv2/ba_0..3.png`.
Gates r20 -> r22: sleeve poke Fidget R 24 mm -> **0 in every clip**; see-through sleeves worst 32 -> 28 px (after a 1-px erosion 10 -> 7;
per clip Standing 9/14 -> 19/23, Fidget L 11 -> 23, Dead R 6 -> 15, Hit 32/31 -> 27/27, Running 27 -> 24/26); torso Death 370 -> 345,
Dead 219 -> 235 (one-pixel hem slivers); robe 0; jitter 0; arm/hand Death R 4.0 -> 3.7 cm (1 f), **Death L 1.4 cm 4 f -> 1.6 cm 4 f,
Dead L 1.4 cm 4 f -> 1.8 cm 6 f** (the left hand resting on the right cuff, which now turns toward its own hand); wrist bends now
<= 29.7 deg in the standing clips, 32.7 in Death/Dead; flat 0.00; viewer check 0 errors; floor ok; regression PASS 250 on 112 (a first run
failed on three PeasantF4 rows whose model another agent was installing at that moment; the rerun passed).

### Death (round 2)
- Legs: `legs_hide.py` scales both Calf joints to 5 % (Death from 0.05 to 0.3 s, Dead held) **and pulls their translation 80 % toward the
  Pelvis** (wyrd_old has no thighs: shrinking alone left the knee points, and so the shrunken legs, 4.5-6 cm outside the lifted robe at
  0.3-0.46 s). `floor_ops.txt`: `--smooth Death 0.035` (0.07 let the fall dip 2.8 cm under the floor once the legs no longer reach down).
- Arms: `arm_clip_wo.txt` Death / Dead left arm abd 15 deg (hand under the robe fold: Death 23 -> 3 frames). Tried and dropped: left 22 deg
  (Dead 1.4 -> 2.6 cm), right -12 deg in the fall (4.1 -> 2.7 cm but jitter: shoulder skin 5 mm/f2), flexion -10 (worse).
- Finishing round (`work/armtry/`, 14 variants gated on Death/Dead with the jitter gate): right arm abd 10 deg eased in 0.15-0.42 s and out
  0.6-1.4 s (`Death:R:10:0:0.15:0.42:0.6:1.4`). Measured on the unmirrored build (`work/half.glb` ... `export/mm9_wyrdold_floor.glb`) the
  right hand's brush through the hood at 0.48 s drops 4.1 -> 2.1 cm; the same gate on the mirrored runtime GLB still reads 4.0 cm (the
  gate's outer-surface classification differs after the mirror; geometry and distances are the same). Larger offsets (12 deg) put the hand
  into the body for 27 frames; flexion either way made it worse.

## Result (r45, installed 2026-11-04)

| Item | Value |
|---|---|
| Runtime GLB | `assets_source/worlds/mm9/models/mm9_wyrdold.glb` (`tools/install_model.py --world mm9`), = `export/mm9_wyrdold.glb` (sha256 4f382ac9030c...; r43 was c787513947e1, kept as `work/hv2/mm9_wyrdold_r43.glb`; r42 was 597705e92727, kept as `work/hv2/mm9_wyrdold_r42.glb`; r22 was 77cde78e5c89, kept as `work/hv2/mm9_wyrdold_r22_installed.glb`; r20 was 16fe15cf6d31, kept as `work/hv2/mm9_wyrdold_r20_installed.glb`; r15 was f893bcb2b8ea; r12 was 50096212c87c, kept as `work/head_v1_backup/mm9_wyrdold_r12_installed.glb`) |
| Binding | `assets_dev/worlds/mm9/models/actors.yml` block `mm9_wyrdold_claude` (`scripts/bind_actors_wo.py` via `scripts/bind_under_lock.sh` under the flock): `MM9 263 Wyrde of the Known (Igrid)`, scale 100, yaw_offset -1.570796327, stride walk 1.55 / run 1.58 (`stride.py`), look Neck + Head, attacks play Fidget, script clip talk -> Fidget |
| Descriptor | row 263 in `tools/mm9_import_discovery/mm9_npc_actor_rows.tsv` (fallback 376 = the stand-in of `mm9_npc_legacy_replacements.tsv`); `mm9_monster_bodies.py --write-overrides` + tables: id 9263, **height 174, radius 31** (MM9's rule on wyrds_old's upright (12, 34, 12) box: sane, no exception) |
| Triangles LOD0/1/2/3 | r45: 15,101 (101 over the 15k ceiling: the undersleeve); r43: 14,982 / 7,486 / 2,690 / 889; r42: 15,067 / 7,529 / 2,706 / 895; r12: 14,821 / 7,406 / 2,662 / 880 (robe 5,000 + linings, head set 3,922, gown, hands 1,474, braids 560, jewel 699, legs 520) |
| Skeleton | 108 joints: wyrd_old's 73 + 30 finger bones + 5 half-joint helpers |
| Textures | body colour 2K, normal + ORM 1K; head set colour 1K (paint v2), normal 1K (paint v2) + ORM 1K; one tier, no region ramps |
| Meshy credits | **25 / 50**: Smart Topology 5 (backup 2480 before), body retexture 4K 10 (2470 before), head retexture 4K 10 (2460 before); no retries; round 2 spent nothing (backup 2370 at the end); **finishing round 2026-11-04: head retexture v2 10 (backup 2365 before) -> 35 / 45** (lease budget = 25 spent + the finishing cap 20) |
| Viewer | http://127.0.0.1:8912/level_generation/creatures/mm9_wyrdold_claude/review/viewer/ revision `r45-20261104` |

## Gates (`review/gates/`)

| Gate | Result |
|---|---|
| `arm_hand_gate.py --outer-only --exact` | hands 0 frames > 1 cm in Standing, Walking, Running, Fidget, Hit; **r15: Death L 4 frames 1.4 cm (the hand against the hood/head at 0.5-0.56 s), R 1 frame 4.0 cm (the hand brushing the hood at 0.48 s mid-fall; 2.1 cm on the unmirrored build, see Death); Dead L 4 frames 1.4 cm (the left hand resting on the right sleeve)** (r12: Death L 2 f 1.4, R 1 f 4.1; r9: Death L 23 frames) |
| `jitter_gate.py` | 0 fails (Fidget arm offset eased over 0.75 s; hand_rest's 13 cm push failed it and was dropped) |
| `see_through_gate.py` (pdm2's) | r1 (no linings) torso 14,728 px Death / 11,773 Dead / 10,162 Hit / 633 Running / 114 Standing, collar 2,000 Death, 105 Running; r3: torso Death 1,079, sleeve R Death 698; r5: torso 350 Death (az135 mid-fall), 219 Dead; **r6 (r15, `see_through_r6.json`): torso 32 Standing, 53 Walking, 52 Running, 38 Fidget, 177 Hit, 370 Death, 219 Dead; collar <= 28; sleeves <= 32 (Death 17 / 13). Every torso hole pixel of Death/Dead is a one-pixel silhouette sliver along the hem outline: 0 pixels survive a 1-px erosion, longest sliver 24-30 px (3 mm pixels); collar and sleeve spots <= 11 px after erosion** |
| `robe_gate.py` (legs through the robe) | **0 in every clip** (r9: Death 18/25 frames 7.8 cm, Dead 7.8 cm; legs_hide above) |
| `sleeve_poke_gate.py` (m7's, patched for body-material hands) | 0 mm in every clip except **Fidget R 24 mm, 2 vertices, 9 frames** (the same in the uncorrected clip: MM9's own wrist bend at 1.6 s; the stub shortening did not change it) |
| `detached_parts_audit.py` | the shoes (with their shin tubes) part from the robe in Hit by up to 24 cm: legs hang free inside the robe by design (MM9 has no thighs; as the Wyrde) |
| `bone_length_audit.py` | Calves 0.08 -> 0.45 m: Death's pulled-in calves (legs_hide, by design) and MM9's keyed Hit calf translation |
| `flat_shading_check.py` / `check_winding.py` | 0.00 body, 0.00 head / 0 inverted |
| `texture_quality.py` | body atlas 60.1 %, spread 1.11, fragments 1.7 % (the lining twins count), stretch p90 1.05; head 62.2 %, spread 1.77 (face 1.7x), fragments 0.1 % |
| `floor_audit.py --world mm9 --match 'MM9 263*'` | r15 and r20: stand 0.0, walk -0.5..+0.4, living -1.9, dead 0.0: ok (r12 first build: the fall sank 2.8 cm, fixed) |
| `mm9_actor_models_build_every_binding` | PASS, 248 descriptors on 110 models, 0 failed (`review/gates/regression_actors.log`; an earlier r12 build failed it: duplicated Calf translation key times, fixed in legs_hide.py) |
| Viewer `run_creature_review.py check` | r15 and r20: 7 clips, 0 failed, 0 console errors |

## Sheets (read)
**Pre-screen pass (r20): `review/face_r20_sheet.png`**, `review/nose_r15_vs_r19.png`, `review/coif_edge_r15_vs_r20.png`. **Finishing round (r15): `review/face_r15_sheet.png`** (MM9 front + profile, front close-up, both 3/4, true profile, low 3/4, under the jaw,
party, party at 128 px; r13/r14 before), **`review/mm9_vs_ours_r15.png`** (MM9 vs ours, five views), `references_head_v2/selected_views_review.png`,
`work/hv2/raster.png` / `raster_ul.png` (unlit vs shaded mouth band). Earlier: `review/mm9_compare_old_young_hag_yrsa.png` (route), `review/masters_vs_mm9.png`, `review/head_masters.png`, `review/mm9_vs_ours_r9.png` (MM9 vs ours,
five views, viewer; `review/mm9_vs_ours_r11.png` current), **`review/face_r11_sheet.png`** (round 2: coif and creases; r9 before) (viewer lighting: MM9 front + profile, front close-up, both 3/4, true profile, low 3/4, under
the jaw, party view, party at 128 px; earlier rounds `face_r1..r7_sheet.png`), `review/ears_sheet.png` (both sides, ear close-ups, from below,
jaw-neck line, party: the hood hides the ears as in MM9), `review/sleeve_r9_sheet.png` (right hand in Fidget), `work/st/fid3_sheet.png`
(Fidget with the arm offset), `work/st/clay1_sheet.png` (clips in clay), `review/death_r12_sheet.png` (Death / Dead: no shoes out of the hem).

## Open points / what to look at
- **Face (paint v2 + pre-screen pass)**: kind and calm, now visibly old (crow's feet, under-eye folds, nasolabial folds, forehead and
  cheek creases) with warmer, ruddier skin; still less extreme than MM9's very old face and not MM9's broad grin (neutral lip geometry).
  The nose reads skin-toned from below with small nostril shadows. Chin soft and slightly receding in true profile.
- **Coif**: ivory linen with folds under the hood, the circlet on its lower edge (Codex projection); white strips run down beside the cheeks.
- **Braids**: a painted three-strand plait on thin cords (Meshy modelled cords, not flat braids).
- **Fidget**: arms held 20 deg out and forward through the gesture (MM9's hands rest on the belly, inside our fuller robe).
- **Death**: the legs vanish into the robe in the fall (scaled and pulled to the pelvis); the right hand brushes the hood in one mid-fall
  frame (gate 4.0 cm mirrored / 2.1 cm unmirrored); the see-through gate's 370 px are hem-outline slivers, no area hole.
- Map placement not switched (the orchestrator's): descriptor 9263 is ready; the maps still place the stand-in 376.

## Not checked
In game (no map places 9263); motion at normal speed in the viewer by eye (clay strips and gates only); LOD1-3 by eye; the v2 head paint
from the back and the coif inside the hood from above (hidden in the sheets' views).
