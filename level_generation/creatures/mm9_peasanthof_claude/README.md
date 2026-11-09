# MM9 half-orc townswomen PeasantHOF1 / PeasantHOF2 (mm9_peasanthof1, mm9_peasanthof2) — 3D actors, 2026-11-02

Townsfolk / variants batch (`devdocs/mm9_rework/overnight/TOWNSFOLK_BRIEF.md`, `VARIANTS_BRIEF.md`). MM9 `MONSTERS.txt` rows:
**61 Commoner** "Peasant Half-Orc Female A" (PeasantHOF1, skin HOF1a; DAT `CommonerHalfOrcFemaleA`, 5 placed: Arslegard City 2,
Sturmford City 1, Thronheim City 2), **62 Town** (HOF1, skin HOF1a; not placed), **63 Shopkeeper** (HOF1, skin HOF1b, an older
woman; DAT `ShopKeeperHalfOrcFemaleA`, 4 placed in Guberland City: shopkeeper.scr, NPC141.scr, none), **64 Prisoner**
(PeasantHOF2, skin HOF1c; not placed). Progress, hashes and Meshy receipts: `creature_3d_progress.json`.

## Body / variant split (the decision)
- `mm9_meshcmp.py peasanthof1:peasanthof2,...` re-run: HOF1 and HOF2 are the **same 86-node skeleton** (rest identical apart
  from Ponytail1 < 1 deg; Scene Root -> Pelvis -> Spine (thighs) -> Spine1..Head; XCOM_skirt with x* hem chains on the pelvis;
  Hair_root braid chains Bone07-12 / Bone14-19; Ponytail back braid); HOF1 vs HOF2 head p90 3.2, torso 3.6, arms 1.6, legs 11.7 cm.
  Side by side (`review/mm9_all.png`, `review/mm9_heads_all.png`): HOF1 knee-length skirt + apron, short sleeves, two front
  braids; HOF2 a floor-length dress, a cream kerchief over the head to the shoulders, long sleeves that are only paint on the same
  arm mesh (MM9's arms differ by 1.6 cm).
- So **ONE Meshy body** (HOF1, design A). HOF2 is a **variant of that body**, not a second Smart Topology: the fitted HOF1 mesh
  with the skirt and apron stretched to the ankles / mid-shin, the braids and shawl knot removed and a procedural kerchief built
  over the head (`scripts/variant_hof2.py`), refitted to MM9's HOF2 (weights from HOF2's own surface, same skeleton), with its
  own UV pass and paint. Two GLBs because the geometry differs (`mm9_peasanthof1.glb` tiers phof1_a / phof1_b;
  `mm9_peasanthof2.glb` tier phof2_c). One rig, one clip library, one script set.
- Tier B (row 63) is a different (older) woman: the body is A's paint recoloured by region ramps (bodice, skirt, skin), the head
  is her own 1K-equivalent head paint (`tier_head.py`, a 10-credit head retexture), as PeasantDM1/DM2 tier B.

| Item | Value |
|---|---|
| Runtime GLBs | `assets_source/worlds/mm9/models/mm9_peasanthof1.glb` (phof1_a, phof1_b), `mm9_peasanthof2.glb` (phof2_c); `tools/install_model.py --world mm9` from `export/` |
| Binding | `assets_dev/worlds/mm9/models/actors.yml` block `mm9_peasanthof_claude` (`scripts/bind_actors_phof.py` under the flock): `MM9 61 Commoner` / `MM9 62 Town` phof1_a, `MM9 63 Shopkeeper` phof1_b, `MM9 64 Prisoner` phof2_c; scale 100, `yaw_offset -1.570796327`, stride 1.34 / 2.5 (`scripts/stride.py`: walk 1.28-1.40 m per 1.1 s, run 2.48-2.53 m per 0.6 s), look Neck + Head, melee impact 0.5 s (hattack1 has no event; right hand fastest at 0.48 s, furthest forward at 0.50 s) |
| Rows | `tools/mm9_import_discovery/mm9_npc_actor_rows.tsv` rows 61-64 (fallbacks = the stand-ins 430 / 433 / 436 / 438); tables regenerated, descriptors 9061-9064, height 195 / radius 38 (MM9's rule) |
| Triangles LOD0/1/2/3 | HOF1 14,488 / 7,242 / 2,604 / 864 (r10: her right lower face subdivided once); HOF2 14,438 / 7,217 / 2,597 / 864 (Smart Topology 14,747 -> ~10k reduced + linings, kerchief inner layer, waist cap) |
| Clips (30 fps, `source/mm9_lib/phofemale.glb`) | Standing stand, Walking walk, Running run, Talk conv1 (NPCBASE Converse), Fidget fidget1, Fidget2 fidget2, Fidget3 fidget3, AttackMelee hattack1, Hit wince1, Death die1, Dead, Cower cowerloop (NPCbase -> BaseRun.inc `LoopAnim Cower`; the library's `cower` is a 0.3 s entry). shopkeeper.scr / NPC141.scr play none; conv2 and the cower entry are not carried |
| Textures | body 2K colour + 1K normal/ORM + 1K region mask; head + hands 2K colour + 1K normal/ORM; tier B has its own head colour + normal; specular 0, metallic 0 |
| Meshy credits | **95** (lease limit 95): Smart Topology 5; body 4K A 10; head 4K A 10, B 10; HOF2 body 4K 10, head 4K 10; r2 head A2 10; r6 head B2 10; r10 heads A3 10, B3 10. Backup 2705 at start, 2285 before the B2 job, 2210 before / 2190 after r10 (shared account) |
| Codex | masters A (2 runs), head turnarounds A, B, C, HOF2 body views on the variant's clay silhouettes (`references_hd/c/sil_*`) |
| Viewer | http://127.0.0.1:8912/level_generation/creatures/mm9_peasanthof_claude/review/viewer/ (tiers phof1_a, phof1_b, phof2_c) |


## User review round r10 (2026-11-04: "her right lower face runs as a straight diagonal from the cheek to the chin") - current
`review/user_20261104/jaw_asymmetry_r9.png`. HOF1 is built from `work/master_v9e.blend`; HOF2's head is a different mesh (its own
Smart Topology head, already symmetric: surface mirror asymmetry over the jaw p95 2.9 mm, seam heights within a few mm), unchanged.
Meshy: two fresh 4K head paints on the final head (`head_retexture_a3`, `head_retexture_b3`, 10 + 10 credits; backup 2210 before,
2190 after; **95** in total, lease limit 95).
- **Cause, measured.** The r8/r9 symmetry metric matched mirrored vertices to the nearest *vertex*, so it mostly measured the coarse
  tessellation (p95 12 mm on both sides). `scripts/jaw_symmetry.py` now also prints the point-to-surface distance (JAWSYM-SURF):
  r9 jaw band (1.635-1.72 m, front) max 8.7 / p95 2.7 mm, worst at the jaw corner. The real defects were (1) the head shell's lower
  edge (the neck seam, shared with the body) sat 12-13 mm higher on her right at the jaw corner (55-80 deg from the front), so the
  body neck took over where her left side still has its jaw corner and a few large triangles spanned straight from cheek to chin; and
  (2) skin weights: her right cheek/jaw carried 13-21 % R Clavicle at 1.71-1.73 m (left side 2-5 %) and both sides up to 77 % Neck
  on the jaw, so in the viewer's Standing pose (head pitched 8.6 deg) the two sides bent differently: head-local mirror asymmetry
  p95 17.8 mm in Standing 0, 22.0 mm in Fidget (bind 2.3).
- **Geometry** (`scripts/jaw_mirror3.py`, master_v8b -> v9c; the user's left = master -x is the source): her right lower-face head
  faces subdivided once (UVs/weights interpolated, all new faces triangulated: quads folded into a chin slit); every right-side seam
  vertex takes the left side's seam height at its angle (shift up to 14.5 mm), the shift spread over 3 cm above/below; every
  right-side shell vertex (cheekbone 1.748 m down to the seam, 12-135 deg from the front) projected radially onto the mirror image
  of the left surface (rays from a centre at 1.715 m), missed rays filled from neighbours and the displacement relaxed twice;
  smooth eases at the cheekbone, the midline (welded, untouched) and the back; lips/tusks/nose/eyes excluded (2 cm sphere + 1 cm
  ease). Body neck (`scripts/neck_relax.py ... 0 0 follow` -> v9e): the body-only vertices take only the seam's shift, faded over
  3 cm (the radial projection had folded the neck's large triangles into a dark facet). Tried and dropped: nearest-point mirror
  (`jaw_mirror.py`, moved 4.7 mm at most), radial projection without the seam (`jaw_mirror2.py`), Laplacian neck relax (dimple).
- **Weights** (`scripts/jaw_weights.py`, v9c -> v9d): her right side takes the mirror of the left side's weights (bones mirrored
  by rest position: L/R clavicle, braid chains Bone07-12 <-> Bone14-19), same eases; clavicle on the head shell fades to 0 from
  1.67 to 1.70 m; Neck/Clavicle on the shell fade from 5 mm to 25 mm above the neck seam (to Head), so the jaw keeps its shape.
- **Numbers** (export, point-to-surface, jaw band 1.635-1.72 m front): r9 max 8.7 / p95 2.7 / p50 0.7 mm -> r10 max 3.1 / p95
  1.7 / p50 0.4 mm (sides 1.6 / 2.2). Seam height at 36-38 mm from the midline: right 1.664 -> 1.654 m, left 1.652. Head-local
  posed asymmetry (`posed` check, p95): Standing 0 17.8 -> 4.8 mm, Talk 6.0 -> 1.7, Fidget 22.0 -> 4.6, bind 2.3 -> 1.5.
- **Paint** (geometry moved, so repainted): `scripts/export_head_upload.py work/master_v9c.blend texturing/phof_head_upload_a3.glb`
  -> `requests/retexture_head_a3.json` / `_b3.json` (the A2 / B Codex turnarounds) -> `crop_head_square.py` ->
  `HEADJOB=a3r scripts/paint_chain_a.sh` and `HEADJOB_B=head_retexture_b3r COPY_TUSKS=0 scripts/head_chain_b.sh` (both paints draw
  their own tusks), texel positions now from `work/phof1_v9c_tex.glb` (the chains used the 2026-11-02 export before). New steps:
  `chin_speck.py` (both paints left a tusk-pale 2-4 texel streak on the chin island's edge: a bright dot under her right lip) and,
  for B, `cheek_line_heal.py` (her right cheek side ~12-20 L brighter than the mirror point: toned to the mirror image of her left
  side; the outermost cheek strip beside both ears, 66-95 mm from the midline, flattened between 1.2 and 10 mm). Previous textures
  kept in `work/r9_textures/`.
- Sheets: `review/sheet_faces_r10.png` (EEVEE on the viewer GLBs, bind pose; per tier before/after rows: front with the face
  midline in red, the same front with her left half mirrored onto her right, 3/4 both sides, profile, low 3/4, party; HOF2 rows are
  the unchanged model), `review/sheet_viewer_heads_r9_vs_r10.png` (viewer, Standing 0 s: front x2 with midline and mirrored half,
  3/4, both profiles; r9 vs r10, every tier), clay checks `review/faces/clay_r10c.png`, `clay_r10e.png` (posed).
- Remaining: B keeps a faint soft edge at her right cheek side beside the braid (much weaker); the body neck under her right jaw is
  coarser than the left (large body triangles).
- Checks (`review/gates/fin10_1`, HOF1; HOF2 unchanged): arm/hand 12/12 clips 0 frames > 1 cm; jitter 0 fails; bones 0 stretching;
  sleeve poke 0; robe 0 in every clip; detached as r8 (the known calf/skirt parts); winding 0; flat shading 0.00; texture quality
  head set 38.5 % / spread 1.58 (as r8). Installed HOF1 sha256 bb2ae72942e4ed5b...; regression mm9 PASS (252 on 114), mm6-8 PASS
  (`review/gates/regression_binding_r10.log`); floor 4/4 ok; viewer r10-20261104 36 switches, 0 failed.
  See-through (step 6) identical to r8 in every part (head max 1 px, Hit; the known Death/Dead sleeve, torso, hair holes).

## Pre-screen round r9 (2026-11-04, orchestrator notes on sheet_viewer_heads_r8) - superseded by r10 above where they differ
Paint/normal pass only (geometry, rig and clips as r8; installed HOF1 sha256 02016ad8a2d3a3e5..., HOF2 9529ff1936dadabb...). No credits.
- **Ears**: `scripts/ear_tone.py` rewritten: per ear, the target is the median of the skin-coloured skin-shell texels within 3 cm of
  the ear's root (the cheek/temple beside it, hair painted on the shell excluded); every ear texel = target x 1.12 (the folded leaf's
  lower facet renders darker) x its own luminance detail ** 0.35: one tone with soft shading. Texture level (skin beside -> ear before
  -> ear after, L / hue deg): A 102/11.7 -> 96/13.5 -> 115/11.7 and 136/14.6 -> 106/26.9 -> 152/14.6; B 141/18.0 -> 89-128 -> 158/18.0
  and 146/18.6 -> 93-122 -> 164/18.6; HOF2 131/13.5 -> 104/17 -> 147/13.5 and 133/13.5 -> 105/17 -> 149/13.5 (HOF2's skin shell is
  part 1 in the body-tex frame; the first r9 attempt sampled the kerchief). Viewer front, point samples along the ear leaf vs the
  temple: A ear L 74 hue 11.4 (r8) -> 109 hue 15.0 (temple 150 / 17.2); B 64 / 15.0 -> 116 / 19.9 (temple 153 / 23.2): hue within
  2-3 deg; the leaf stays darker than the temple where its lower facet faces down. HOF2's ear is one tone now (was a pale back and a
  dark brown front).
- **HOF2 chin line (viewer only)**: diagnosed, not fixed. It stays with the head colour flat, the normal map flat, the normal and ORM
  gutters re-padded (`pad_gutters.py` on every head normal/ORM map and HOF2's body maps), and the coincident-vertex normals grouped
  by a KD-tree (0.1 mm; `normal_seams.py` now; the old rounding buckets missed pairs on a cell edge): it is a crease in the head mesh
  itself, lit by the viewer's key light. A normal relax over the chin made it worse (seam-split vertices diverged) and was dropped.
- **HOF2 nostrils**: `normal_seams.py --nose-s 0.012` (HOF2 build): down-facing normals round a point 12 mm below and behind the nose
  tip turned up/forward with a Gaussian falloff (the chin rule); the paint there is not dark (blot texels L ~109 vs 149 around), so a
  paint lift was tried and dropped. The openings now read as small soft shadows; a small dark septum shadow remains.
- Sheets: `review/sheet_viewer_heads_r8_vs_r9.png` (left r8, right r9; every tier front, 3/4, profile), `review/sheet_viewer_heads_r9.png`.
- Checks: viewer r9-20261104 36 switches, 0 errors; winding 0; floor 4/4 ok; regression mm9 PASS (252 on 114), mm6-8 PASS
  (`review/gates/regression_binding_r9.log`). Arm/jitter/sleeve/robe/see-through not re-run (geometry and clips unchanged since r8).

## User review round r8 (2026-11-04: "deformed right part of the face/chin? not symmetrical?") - superseded by r9 above where they differ
`review/user_20261104/jaw_asymmetry.png`. No credits (75 in total). HOF1 is built from `work/master_v8b.blend` = `master_v5` (the
r6 geometry: r7's `nape_strip_in.py` pull, which also pulled the jaw corner in, is undone) + `scripts/strip_delete.py` (the two
head-shell faces of the strip at the nape side that stood out beside the jaw corner as the "pale wedge" are deleted; the body's
neck/collar behind them closes the view; no vertex moves, the jaw is untouched). Tried and dropped on the way: an outward symmetric
fill of the jaw (it moved both sides by its 12 mm cap, not one) and a mirror-match tuck of the strip (`strip_mirror_in.py`: left a
crease along the jaw line).
- **Symmetry** (`scripts/jaw_symmetry.py`: every skin-shell vertex mirrored at the nose-tip plane and matched to the nearest shell
  vertex; band 1.635-1.70 m, all depths, i.e. the jaw incl. its corners): r6 max 23.7 / p95 13.5 mm (one side 23.7, the other 15.0),
  r7 max 20.5 / p95 13.5 (r7's pull made BOTH sides 20.5: the pinch the user saw), r8 max 15.5 / p95 12.1 (sides 15.5 / 13.8; the
  remainder is the Smart Topology head's own asymmetry and tessellation). Face band 1.62-1.76 m, front of z -0.06: 12.0 p95 in all.
- **Cheek and chin lines** (thin light lines down her left cheek near the ear and on the chin, still there with the normal map
  flattened): the paint steps after the compose had changed the islands but not the gutter texels, so bilinear/mip sampling at the
  UV seams mixed in the old lighter padding. `scripts/pad_gutters.py` re-pads every head set (A, B, C) and HOF2's body last in the
  chains. Also `scripts/normal_seams.py` on every build: head vertex normals averaged across UV seams and the head/body seam, and
  the under-chin normals turned up/forward with a Gaussian falloff (sigma 3 cm) weighted by how far down they face (the FINISH
  brief's rule: no hard region) - the dark band under the chin is gone in the viewer.
- **Pale strip along the top of the fringe**: `scripts/fringe_edge.py` (skin-shell texels within 3-7 mm of the hair shell take the
  hair's local colour; the fringe painted on the forehead further down stays), tiers A and B.
- **skin_seam_blend.py** now runs with its jaw darkening off (default `--jawk` was 0.86 and darkened the jaw sides in r7).
- HOF2 (tier C) checked the same way: symmetry band 1.60-1.745 m p95 9.2 mm unchanged (no geometry change); gutters re-padded and
  normals averaged. A diagonal light line across the chin's left side shows in the three.js viewer only (also with the normal map
  flattened; not in Blender's renders; already in r7) - not resolved.
- Sheets: `review/sheet_faces_r8.png` (rows: A before r7, A after, B after, C before r7, C after; columns front, 3/4 left, 3/4 right,
  true profile, low 3/4, party; EEVEE; the r7 rows are the r7 export, tier A's head with its body unramped),
  `review/sheet_viewer_heads_r8.png` (viewer head front / 3/4 / profile, every tier), the user's shot above.

## Pre-screen round r7 (2026-11-04, orchestrator notes on r6) - superseded by r8 above where they differ
No Meshy credits (75 in total). HOF1 is built from `work/master_v6.blend`, HOF2 still from `work/hof2/master_v23.blend`.
- **HOF2 legs through the long dress** (Walking, Running, Cower, from behind / side / low back): the robed bodies' route
  (MM9's long dresses show no legs) instead of making the dress follow the legs (`skirt_leg_blend.py` on HOF2 was tried in r6 and
  rejected: spikes). `scripts/dress_clips.py` (keys only, in `build_runtime_phof.sh` before the floor passes):
  `--tuck`: a scale channel on both Calf joints driven by the knee's flex away from its Standing pose (s = 1 straight, down to 0.35
  Walking / 0.2 Running / 0.4 Cower / 0.5 Hit when bent; a0 8, a1 35 deg): the stance foot stays on the floor, the kicked-back
  shin and shoe pull in toward the knee; `--tuck-thigh`: the same on both Thighs from the larger of thigh swing and knee flex
  (Walking 0.7, Cower 0.7; Running 0.35 always, `Running=0.35@0:1`: the running leg swung back still carried the heel out through
  the back). `--damp`: every skirt joint (XCOM_skirt, x* chains) slerped toward its Standing pose, Running 0.85 (the back flap,
  and a lining fold that came out through the back of the dress in every running frame), Death 0.6, Dead 0.6 (the flare).
  `scripts/legs_hide.py` (copied from `mm9_scholar_claude`): both Calves scaled to 5 % in Death from 0.05 to 0.35 s and in Dead,
  run AFTER the floor passes (before them the corpse's lowest point moved and the ground-death root offsets jerked: Death
  shoulder-skin jitter 6-10 mm/f2). Low-back / low-side views added to `scripts/from_dm2/glb_frames.py` (`lowback`, `lowside`).
- **HOF2 dress streaks**: `scripts/streak_heal.py` (Hough transform over ridge texels on the dark cloth; 49 straight lines,
  9,284 texels refilled from their surroundings), last step of `paint_chain_c.sh`.
- **HOF2 kerchief smear**: `scripts/kerchief_smear_fix.py` (pinkish / speck texels of the kerchief parts beside the ears refilled
  from the cloth), last step of `paint_chain_c.sh`.
- **HOF1 ears**: `scripts/ear_tone.py` (ears to the cheek's hue at 60 % and x 0.88/0.84/0.80: A 164/97/78 -> 145/81/62, B
  150/98/75 -> 137/81/57; HOF2's are 149/93/69) in both head chains.
- **HOF1 cheek sides**: `scripts/skin_seam_blend.py` (skin tone across the paint's projection seams outside the central face box
  made continuous in 3D, sigma 1.2 cm; the cheek sides beside the braids x 0.9) in both head chains. The faint vertical line on
  B's left cheek is weaker, not gone (a fine-scale paint step that a broad-colour blend does not remove).
- **HOF1 pale wedge beside the jaw** (REVERTED in r8: the pull pinched the jaw corner): a ray pick (`scripts/pick_pixel.py`) showed it is the head shell's lowest strip at the nape
  sides (export height 1.645-1.665 m, 7 cm behind the neck centre, |x| 7.5-8 cm) standing out sideways past the jaw and facing
  the key light. `scripts/nape_strip_in.py` moves those 12 shell vertices toward the centre line (|x| x up to 0.78, max 20 mm) ->
  `work/master_v6.blend`. Paint darkening of the strip and a gutter-texel repaint were tried first and dropped (the darkening
  left smudges under the jaw; the wedge is not body material).
- Sheets: `review/sheet_hof2_legs_before_after_r7.png` (Walking 10/22, Running 2/6/10, Cower 4/46, Death 24/48; side, back, low
  back, low side; left r6 installed, right r7), `review/hof2_death_r7.png`, `review/hof2_legs_r7f.png` (the whole run cycle),
  `review/sheet_faces_r7.png` (all tiers: MM9 front/3-4/profile, ours front, 3/4, true profile, low 3/4, party, party at 128 px),
  `review/sheet_viewer_heads_r7.png`.

## Finishing round r6 (2026-11-04, FINISH_BRIEF_20261104 job 1) - superseded by r7 above where they differ
The r2 round above was cut off by a usage limit after its exports (HOF1 00:05, HOF2 23:46 CET, kept as
`work/r2_00h05_mm9_peasanthof1.glb` / `work/r2_23h46_mm9_peasanthof2.glb`) and before any gate or install. This round read
their gates (`review/gates/fin4_1`, `fin4_2`), fixed what remained and rebuilt both (`review/gates/fin5_1`, `fin5_2`).
Meshy: one fresh tier-B head paint (`head_retexture_b2`, 10 credits; **75** in total, lease limit 85 = 65 + this job's 20;
backup 2285 before it).
- **Neck strip, tiers A and B** (`scripts/neck_even.py`, last step of `paint_chain_a.sh` and `head_chain_b.sh`): the head
  shell's lowest strip (neck sides and nape below the jaw) was painted a saturated orange (~185/111/72) next to the tier's
  pale body neck (~210/135/105), so the body showed between jagged orange polygons (a flat-colour render had none: paint).
  Head skin texels below 1.675 m (front) / 1.70 m (sides, back) now take the tier's body neck colour (measured on its ramp
  preview) as their broad colour, detail kept, smoothed across islands in 3D. Broad-colour distance to the body neck: A
  9.1 -> 1.7, B 7.8 -> 1.3 (mean, sRGB). Diagnostics: `review/faces/diag_neck.png`, `diag_uv.png`, `neck_fix_v1.png`.
- **Tier B fresh head paint** (the old B paint had a pale mask panel with straight edges at |x| = 7 cm from temple to jaw,
  present in the raw Meshy paint, `review/faces/diag_b_raw.png`, so no patch could fix it): the existing B Codex turnaround
  (`references_head/b/`) on the current head geometry (`texturing/phof_head_upload_a2.glb`, the same upload as A's a2 paint)
  -> `meshy/head_retexture_b2` -> `scripts/crop_head_square.py` -> `meshy/head_retexture_b2r` ->
  `HEADJOB_B=head_retexture_b2r COPY_TUSKS=0 scripts/head_chain_b.sh` (this paint draws its own tusks) with a new
  `skin_warm.py` step (gain 1.02/0.94/0.86, cheek flush 0.18) before the neck step. Before/after `review/faces/b_before_after.png`.
  A faint vertical boundary remains at the left cheek, much weaker than before.
- **HOF2 thigh stretch** (`bone_length_audit.py`: Bip01 L Thigh offset 0.171-0.202 m, 11 % over rest, also in the installed
  GLB): `scripts/thigh_length_fix.py` keeps both thigh offsets at their rest length (direction kept) right after
  `clips_mm9.py` in `build_runtime_phof.sh` (MODEL=2). Audit 1 -> 0 stretching joints; jitter 0 fails.
- HOF2 is built with the default `scripts/floor_ops.txt` (as the r2 export); `floor_ops_hof2.txt` (Death smooth 0.1) raised
  the Death shoulder-skin jitter to 2.03 mm/f2 (1 fail).
- **Hair silhouette** (`scripts/head_sil.py`, `scripts/hair_overlay.py` -> `review/hair_overlay/overlay.png`, MM9 outline in
  cyan, aligned on the crown): widths 2/4/6/8 cm below the crown, front MM9 23.2/25.5/27.7/29.3 cm vs ours 19.2/22.6/25.2/
  26.8 cm (MM9's low-poly bob has a flat top; ours is a dome, 2.5 cm narrower at the temples); profile 22.6/25.8/27.8/28.9 vs
  19.9/23.8/26.8/28.0. MM9's ear tips sit ~2.5 cm higher under its crown than ours. Not reshaped: alignment by ears instead
  of crown reverses the height difference, and the read in the viewer is now a copper bob with strands, not a helmet.
- Gate tooling: `scripts/robe_diag.py` (HOF2's lined dress makes `robe_gate.py` flag every frame: the legs sit between the
  lining and the outer dress; it counts leg vertices with no dress face further out on a horizontal ray),
  `scripts/finish_gates.sh` (all gates on one export), `head_closeups.py` diagnostics (`HEAD_FWD`, `FLATTEX`, `NONORMAL`,
  `HEADTEX`, `BODYTEX`), `scripts/sheet_body_vs_mm9.py`.

## Coordinator review r2 (2026-11-02 evening) - superseded by the finishing round below
Asked: HOF2's right-hand flap over the cuff and left-wrist see-through; HOF1 hair read as a smooth dark-brown helmet; tier A's
face pale, doughy and blank, pale pink ears; HOF1 Death legs through the skirt. Meshy: one fresh head paint (10 credits,
**65 / 70** in total; backup 2380 before it).
- **Tier A fresh head paint**: Codex turnaround `references_head/a2/` (warm ruddy skin with freckles, gentle closed smile,
  tusks, copper hair with visible strands, ears in the face tone) -> 4K head retexture on the CURRENT head geometry
  (`scripts/export_head_upload.py` -> `texturing/phof_head_upload_a2.glb`). That upload carried the master's HeadUV (the head
  islands scaled 0.8 into the lower-left square), so Meshy's maps were cropped back to the full layout the compose expects
  (`meshy/head_retexture_a2r/`, see its README.txt). Chain `scripts/paint_chain_a.sh` (HEADJOB=a2r): compose -> head_fix
  (ears toned to the cheek x 0.84: thin ears facing the light read pale; pale-panel fill) -> `hair_color.py` (light strand
  contrast, matte hair roughness) -> tiers -> `skin_warm.py --body-auto` (the body skin region takes the new head's neck tone)
  -> seam_tone -> face_paint. Tier B keeps her own head paint (hair brightened toward copper, `--side-x 9`), tusks copied from
  the first A paint (`phofaold_tp`, the a2 paint draws them elsewhere).
- **Hair crown**: `scripts/hair_taper.py` narrows the hair shell above 0.875 m toward MM9's crown (+-9 cm at 0.95 m; ours was
  +-11-12 cm); MM9's head sits 10 cm further forward in its bind, its width/height matched ours otherwise.
- **HOF1 Death skirt**: `scripts/skirt_leg_blend.py ... 0.85 0.22 -0.05 1.0 0.4` (skirt vertices take up to 85 % of the nearest
  leg vertex's weights within 22 cm, front; 40 % at the back): robe gate 0 in every clip (Death was 10/37 frames, 5.7 cm).
- **HOF2 wrists**: `wrist_trim_cap.py` (stub shards trimmed, deep stub removed), `stub_ray_fix.py` (reweight),
  `set_weights_near.py`, `drop_faces_near.py`, `shrink_boot_cuffs.py` (the boot cuffs poked through the long dress at rest).

## Route (scripts/, repo root unless noted; `bld.sh` runs Blender directly under a 12G cap, 4 threads)
0. `convert_sources.sh`, `ref_renders.py` -> `review/mm9/`, `review/mm9_head/`; `ref_sheets.py` -> `references_hd/mm9_*`.
1. Masters: `codex_masters.sh a phof1a 1|2` (brief `references_hd/a/CODEX_BRIEF.md`), `clean_alpha.py` -> `references_hd/a/clean/`.
2. Smart Topology 15k from `references_hd/a/clean/00_three_quarter.png` (padded 64 px top/bottom).
3. `fit_rig.py` + `fit_config.json` (centre chain Pelvis..Head, Spine/Spine2 by neighbour mean, `hip_band` 0.15 m: MM9's
   low-poly hips have no vertex within 8 cm of the hip joints) -> `reduce_uv.py` -> `drop_bracelets.py` (wrist cords, paint in
   MM9) -> `graft_hands.py graft_phof.json` (MPFB female hands, 0.205 m) -> `neck_bisect.py ... 0.65` -> **`add_ears.py`**
   (procedural pointed half-orc ears: the Smart Topology hid none under its hair shell) -> `head_split.py head_phof.json`
   (back braids included) -> `eye_fill.py` -> `loose_parts.py` (eye cups, the loose lip plate that showed between the lips) ->
   `fill_holes.py` (eye socket) -> `cuff_trim.py -0.03` -> `stub_clamp.py` -> `triangulate.py` -> `uv_pass.sh` (**never re-run**:
   body 66.9 %, head 54.2 %).
4. Master fixes after the paint (positions/weights/added faces only): `drop_part_near.py` (a leftover eye cup),
   **`mouth_close.py`** (the lips' 1-2 mm open slit closed to one line), `weights_from_neighbour.py` (boot cuffs took the boot's
   weights: 8 mm float in Fidget), `linings_phof.sh` (`sleeve_tuck.py`, `rim_lining.py` skirt/apron, collar, boots, sleeves;
   **`waist_cap.py`** a disc inside the dress at the hips) -> `work/master_v3.blend`.
5. Paint: `paint_chain_a.sh` (compose_texpass, gentle grade, compose_headhand, **`head_fix_phof.py`** ears to the cheek tone, grey
   scalp/temples, neck evening, pale collar band; `seam_tone.py`; **`face_paint_phof.py`** under-eye/eyeshadow lift, corner
   specks, chin specks), `tiers_phof.py a` (body R bodice, G skirt, B skin; B targets from MM9's HOF1b skin, B skin = A x B's
   face tone), `head_chain_b.sh` (B's head against the tier-B body, A's painted tusks copied in: B's paint had none).
6. HOF2: `variant_hof2.py` on `work/fit_v1.blend` -> `fit_rig.py` (phof2c) -> `geo_hof2.sh` -> eye/mouth/cuff steps as above ->
   `uv_pass_hof2.sh` (body 64.3 %, head 62.1 %) -> Codex views on the clay (`codex_design.sh c phof2c`) and head turnaround
   (`codex_head.sh c`) -> retextures -> `paint_chain_c.sh work/phof2_paintpos.glb` (`--dy -0.015 --dz 0.034`: fit_rig recentred
   the variant) + `hand_tone.py` -> `tiers_phof.py c` -> `mouth_close.py`, `weights_from_neighbour.py`, `linings_phof.sh` (skirt
   depth 1.2) -> **`twin_part.py`** (kerchief inner layer, decimated 0.944) -> `stub_clamp.py`, `stub_ray_fix.py`, `sleeve_tuck.py`
   -> `work/hof2/master_v8.blend`.
7. Runtime: `MODEL=1|2 scripts/build_runtime_phof.sh [--install]`: export -> `clips_mm9.py` (`roles_phof.json`, soft offsets) ->
   `finger_pose.py` -> `arm_clear.py` (Fidget, Fidget3) + `smooth_correction.py` -> prepare -> LODs -> shadow fix ->
   `region_variants.py` -> `tier_head.py` (HOF1) -> extras -> `floor_fix.py` (`floor_ops.txt`) + a second skirt-strip pass ->
   `mirror_glb.py` -> `fix_winding.py` -> winding. Viewer: `viewer_tiers_phof.py a|c`, `make_viewer_manifest.py`.
   Binding: `flock -x level_generation/creatures/claude_shared/locks/mm9_actors_yml.lock bash -c 'python3
   level_generation/creatures/mm9_peasanthof_claude/scripts/bind_actors_phof.py && python3
   tools/mm9_import_discovery/mm9_monster_bodies.py --write-overrides && python3 tools/mm9_import_discovery/generate_mm9_monster_tables.py'`.

## Checks (r8 builds, installed 2026-11-04; HOF1 sha256 6d0acf8ac5a0aa20..., HOF2 3737f0f580b7919b...)
r8 (`review/gates/fin8_1`, `fin8_1b`, `fin8_2`): every number in the r7 table below is unchanged - arm/hand 0 frames over 1 cm,
jitter 0, sleeve poke 0 mm, bones 0, winding 0 on both; HOF1 robe gate 0 in every clip; HOF2 visible-leg counts as r7; see-through
identical to r7 on both (HOF1 on the final build: the two deleted shell faces opened nothing; head <= 1 px, collar <= 13 px as
before); floor 4/4 ok; viewer r8-20261104 36 switches 0 errors; regression mm9 PASS (252 on 114), mm6-8 PASS
(`review/gates/regression_binding_r8.log`). (`fin8_1` ran on the v8b build before the last head-paint pass, `fin8_1b` on the final:
same geometry.)

### r7 checks (installed 2026-11-04; HOF1 sha256 e4ec961dde85c755..., HOF2 e415315c3d7fc068...)
`review/gates/fin7_1`, `fin7_2` (see-through every 6th 30 fps frame, 16 views). Earlier rounds below.
| Gate | HOF1 (rows 61-63) | HOF2 (row 64) |
|---|---|---|
| Arm and hand (`--outer-only`, 12 clips) | **0 frames over 1 cm**; Fidget L forearm 1.7 cm | **0 frames over 1 cm**; Fidget L forearm 5.6 cm |
| Jitter | **0 fails** | **0 fails** (legs_hide before the floor passes gave Death shoulder skin 6-10 mm/f2: moved after them) |
| Sleeve poke | **0 mm every clip** | **0 mm every clip** |
| Legs through the skirt / dress | `robe_gate.py` **0 every clip** | `robe_gate.py` still flags every frame (legs between the lining and the outer dress, hidden); `robe_diag.py` (no dress face further out): Standing, Running, Talk, Fidget2/3, AttackMelee, Cower, Dead **0**; Walking 2 frames / 5 vertices, Fidget 3 vertices, Hit 45 frames / 19 vertices (all: the shoe toes under the front hem, renders clean), Death 12 frames (horizontal rays on a lying body; renders closed, no shoes). r6: Walking 17 frames / 45, Running 8 / 28, Cower 37 / 47 |
| See-through | identical to r6 / installed: living clips <= 24 px apart from Hit (skirt 67, torso 22); Death/Dead torso 84-94, sleeves 84/104, hair 182, trousers L 48 | living clips: left wrist ring <= 4 px; Death sleeve R 33 px (r6 113), sleeve L 2 (r6 58), torso 39 (r6 43); Dead torso 8 |
| Floor (`floor_audit.py`) | ok (stand 0, walk -0.1..+1.8, dead 0) | ok (walk -0.1..+1.4, dead 0) |
| Bones / winding / flat | 0 / 0 / 0.00 | 0 / 0 / 0.01 |
| Detached | 6 "in some pose": calves/boots under the skirt (installed r5: 5, same parts) | 1: apron 1.5 cm off Spine2, AttackMelee frame 5 |
| Texture quality | body 66.9 %, head set 38.5 %, spread 1.58, fragments 0.7 % | body 62.7 %, head set 43.5 %, spread 1.5, fragments 1.6 % |
| Viewer | r7-20261104: 36 switches, 0 failed, 0 console errors | |
| Regression | `mm9_actor_models_build_every_binding` **PASS** (252 descriptors on 114 models), mm6-8 PASS (`review/gates/regression_binding_r7.log`) | |

### r6 checks
#### r6 (installed 2026-11-04 09:40; HOF1 sha256 9b049f40f1258ff6..., HOF2 511267d32822ed0d...)
Before = the installed 2026-11-02 builds (and the cut-off r2 exports, `review/gates/fin4_*`); after = `review/gates/fin5_1`, `fin5_2`.
| Gate | HOF1 (rows 61-63) | HOF2 (row 64) |
|---|---|---|
| Arm and hand (`arm_hand_gate.py --outer-only`, 12 clips) | **0 frames over 1 cm, both hands, every clip**; Fidget L forearm 1.7 cm (forearm over the bust) | **0 frames over 1 cm**; Fidget L forearm 5.6 cm (forearm against the bust, hand clear) |
| Jitter (`jitter_gate.py` vs the retargeted clips) | **0 fails** | **0 fails** |
| Sleeve poke (`sleeve_poke_gate.py`) | **0 mm in every clip** | **0 mm in every clip** (was Running 27.1 / Death 25.2 mm; fixed in r2 by `wrist_weights.py` RIGID, v21-v23) |
| See-through (`see_through_gate.py`, 16 views; HOF1 every 6th 30 fps frame, HOF2 every 3rd) | living clips <= 24 px apart from Hit (skirt 67, torso 22); Death/Dead torso 84-94, sleeves 84/104, hair 182, trousers L 48 (Death) - as installed (24 / Hit 66 / 68-91 / 84-110 / 183) | living clips: left wrist ring **2-4 px** (was 41-87 px in every clip); Death: sleeve R 113 px (1 frame, level camera; 0 at the party's 20 deg), sleeve L 58 (4 at 20 deg), torso 43; Dead torso 7 (installed: Death sleeves 82-87, torso 46) |
| Legs through skirt (`robe_gate.py`) | **0 in every clip** (Death was 9/37 frames, 5.6 cm) | `robe_gate.py` flags every frame (legs between the dress lining and the outer dress, hidden). `robe_diag.py` (leg vertices with no dress face further out): 0 in Standing, Talk, Fidget2/3, Dead; Walking 17/27 frames (up to 45 vertices), Running 8/15 (28), Hit 44/65 (9), Cower 37/37 (45), Death 20/37 (76), Fidget 3, AttackMelee 0. **Seen in renders** (`review/hof2_legs_r6.png`): the heel/calf pokes through the back of the dress in Walking and Running (and a small one in Cower); also in the installed build. Not fixed: `skirt_leg_blend.py` (k 0.6-0.9, reach 15-25 cm, with feet) did not stop it and spiked the dress (`review/hof2_legs_r6b/c/d.png`, rejected `work/hof2/master_v24_skirtblend_rejected.blend`) |
| Floor (`floor_audit.py --world mm9 --match 'MM9 6[1-4] *'`) | ok (stand 0, walk -0.1..+1.8, dead 0) | ok (walk -0.1..+1.3, dead 0) |
| Detached (`detached_parts_audit.py`) | 6 parts "in some pose": the calves/boots under the skirt (bind gap 6-8 cm to the skirt cluster; installed build: 5, same parts) - hidden under the skirt in renders (`review/hof1_legs_r6.png`) | 1 detached: apron 1.5 cm off Spine2 in AttackMelee frame 5; legs under the dress concealed |
| Bones (`bone_length_audit.py`) | 0 stretching | **0 stretching** (was L Thigh 0.171-0.202 m, 1 joint) |
| Winding / flat | 0 / 0.00 | 0 / 0.01 |
| Texture quality (export; linings sample one texel by design, so the body spread is meaningless) | body atlas 66.9 %, fragments 3.8 %, stretch 1.10; head set 38.5 %, spread 1.58, fragments 0.7 % | body 62.7 %, 3.7 %, 1.09; head set 43.5 %, 1.50, 1.6 % |
| LOD0 | 13,862 | 14,438 |
| Viewer (`run_creature_review.py check`) | r6-20261104: 36 switches, 0 failed, 0 console errors (3 tiers) | |
| Regression (`OPENYAMM_REGRESSION_FILTER=actor_models_build_every_binding ./build/game/openyamm --world mm9 --headless-run-regression-suite actors`) | `mm9_actor_models_build_every_binding` **PASS** (251 descriptors on 113 models), mm6-8 PASS (647 on 185) (`review/gates/regression_binding_r6.log`) | |

Sheets read (r6): `review/sheet_faces_r6.png` (MM9 front/3/4/profile vs ours front, 3/4, true profile, low 3/4, party, party
at 128 px; EEVEE on the viewer GLBs), `review/sheet_viewer_heads_r6.png` (viewer shots: head front, 3/4, right profile, every
tier), `review/sheet_mm9_vs_ours_r6.png` (full body vs MM9, every tier), `review/faces/neck_fix_v1.png`,
`review/faces/side_fix_v2.png` (a rejected side-tone patch), `review/faces/diag_b.png`, `review/faces/diag_b_raw.png`,
`review/faces/diag_b2.png`, `review/faces/b_before_after.png`, `review/hair_overlay/overlay.png`, `review/wrist/r6_sheet.png`,
`review/hof2_legs_r6.png`, `review/hof1_legs_r6.png`, `review/gates/fin4_2/see_through_*.png` (HOF2 Death slivers).
Before (installed): `review/sheet_faces_final.png`, `review/sheet_mm9_vs_ours_before_r2.png`; r2 cut-off export:
`review/sheet_faces_final_r2.png`.

### Previous checks (installed 2026-11-02; HOF1 9594fa82c1aa5918..., HOF2 de2c3f11795bfc7e...)
| Gate | HOF1 (rows 61-63) | HOF2 (row 64) |
|---|---|---|
| Arm and hand (`arm_hand_gate.py --outer-only`, 12 clips) | **0 frames over 1 cm, both hands, every clip**; Fidget L forearm 1.7 cm (forearm over the bust; raw MM9 6.0 cm hand) | **0 frames over 1 cm**; Fidget L forearm 5.6 cm (forearm against the bust, hand clear) |
| Jitter (`jitter_gate.py` vs the retargeted clips) | **0 fails** | **0 fails** |
| Sleeve poke (`sleeve_poke_gate.py`) | **0 mm in every clip** | **FAIL**: rest 0 mm, but the right wrist's grafted-hand flap rises over the cuff when the wrist bends: Running 27.1 mm (4 vertices, 24 frames), Death 25.2 mm (34 frames), Talk 1.6, Hit 1.5 mm; tried `stub_clamp`, `stub_ray_fix.py` (reweight), `sleeve_tuck.py` 0.7: not resolved |
| See-through (`see_through_gate.py`, every 6th 30 fps frame, 16 views) | before linings torso 20,676 / sleeves 1,898 / skirt 1,176 px; after: living clips <= 24 px apart from Hit (skirt-zone 66 px: shoulder-cap sliver), Death/Dead torso 68-91, sleeves 84-110, hair 183 (Death, hair shell rim) | living clips: left wrist ring 41-87 px in every clip (the open cuff end seen from behind); Death sleeves 82-87, torso 46; skirt, kerchief, collar <= 5 |
| Legs through skirt (`robe_gate.py`, skirt = XCOM/x* chains) | 0 in every clip but Death: 9/37 frames, 5.6 cm (the falling skirt opens over the thighs) | not run |
| Floor (`floor_audit.py --world mm9 --match 'MM9 6[1-4] *'`) | ok (stand 0, walk -0.1..+1.8, dead 0) | ok (walk -0.1..+1.3, dead 0; the death's dress dip lifted by a second skirt-strip pass) |
| Detached (`detached_parts_audit.py`) | 0 detached (boot cuffs re-weighted) | 3 parts in some poses: legs/boots under the long dress (up to 2.4 cm in Death, hidden), the apron 1.5 cm off Spine2 in AttackMelee frame 5 |
| Winding / flat / bones | 0 / 0.00 / 0 stretching | 0 / 0.01 / not run |
| Texture quality (pre-lining export; linings sample one texel by design) | body atlas 66.9 %, spread 1.06, fragments 0.0 %, stretch 1.11; head set 38.5 %, spread 1.56 (head vs hands), fragments 0.7 % | body 62.7 %, 1.05, 0.0 %, 1.09; head set 43.4 %, 1.54, 2.3 % |
| LOD0 | 13,862 | 14,438 |
| Viewer (`run_creature_review.py check`) | r4: 36 switches, 0 failed, 0 console errors (3 tiers) | |
| Regression (`OPENYAMM_REGRESSION_FILTER=actor_models_build_every_binding ... --world mm9 ... actors`) | `mm9_actor_models_build_every_binding` **PASS** (246 descriptors on 109 models), mm6-8 PASS (`review/gates/regression_binding.log`) | |

Sheets read: `review/sheet_faces_final.png` (MM9 front/3/4/profile vs ours front, 3/4, side, low 3/4, party, party at 128 px;
EEVEE with the viewer GLBs' baked tiers), `review/sheet_faces_all_r2.png`, `review/sheet_viewer_a.png` (viewer shots, tier A),
`review/sheet_mm9_vs_ours.png`, `review/sheet_ears.png`, `review/death_frames.png`, `review/fidget_frames.png`,
`review/clay_clips.png`, `review/gates/see_through_r1|r2|hof2/`, `review/poke_run_sheet.png` (HOF2 wrist flap),
`review/neck_flat.png`, `review/mm9_all.png`, `review/mm9_heads_all.png`, `review/hof2_variant_v1.png`.

## Heights
`mm9_monster_bodies.py --write-overrides` gives rows 61-64 **195 / radius 38** (MM9's rule from the models' own extents: half
height 0.9728 m); our GLBs stand 1.97 m = 197 units at scale 100, so 195 matches the model. The ~215 expected in the brief is the
half-orc MAN (PeasantHOM1 is 2.27 m); MM9's half-orc women are 1.95 m. Reported, not changed.

## Deviations and open points
- **Tusks are paint** (as MM9): tier A's a2 head paint and tier B's b2 paint (r6) draw their own; the old B paint had none
  and got A's tusk texels copied (`copy_tusks.py`, now off: `COPY_TUSKS=0`). Modelled tusks were tried (`add_tusks.py`) and dropped: thin needles in profile.
- Ears are procedural (Meshy modelled none): one cupped leaf per side on the head bone, painted by the head retexture and toned
  to the cheek. The HOF2 ears stand in front of the kerchief.
- HOF2's kerchief is a procedural shell (convex hull of the head and shoulder tops) with a decimated inner layer; its top reads
  higher and more pointed than MM9's rounded kerchief.
- HOF1's back has two short braids where MM9 has one (Smart Topology); the masters' back braid is painted over both.
- Tier B: a faint vertical line on the left cheek remains (Meshy's front/side projection; weaker after r7's seam blend).
- HOF2 runs and walks with her legs pulled up under the dress (dress_clips.py): her feet do not plant in Running (MM9's long
  dresses show no legs; the hem stays on the floor).
- Hair: our bob is a dome, MM9's a flat-topped low-poly bob ~2.5 cm wider at the temples (overlay numbers above).
- Map placement is the orchestrator's (the DAT classes still place the stand-ins 430/436 through the transcoder).

User artistic acceptance: not recorded.
