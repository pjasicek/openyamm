# MM9 Giant (`mm9_giant`, Plain Giant gi_a / Forest Giant gi_b) LOD0 reduction (2026-11-04)

Batch: [REDUCTION_BRIEF_20261104.md](../../../devdocs/mm9_rework/overnight/REDUCTION_BRIEF_20261104.md), ledger row 2 of
"MM9 reduction" in [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md). Lease `mm9reduce:giant` (giant-reduce-20261104).
Route: [RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md) default route, no-retexture branch. No Meshy, no credits.
**Status (fix pass, 2026-11-04): candidate `export/mm9_giant.glb` = f60 (10,016), chart-guarded, UV audit 0 escaping
LOD0 faces; ready for review, not installed (the orchestrator installs). Pass 2 (p79, 9,480) was installed and rolled back:
`claude_shared/reduction_uv_audit.py` found 66 LOD0 faces off the painted charts (belt, pauldron rim, chest fur wedges).**

## Fix pass: chart guard (2026-11-04)

The MeshLab texture-aware collapse lets a seam vertex slide so that a new face's UV triangle reaches into the gutter; an
iterative lock of the source faces round each escape (`scripts/chart_lock.py`, same test as the audit) only moved the
escapes elsewhere (73 -> 71 -> 86 -> 63 -> 33 -> 20 over five rounds while the count crept up), so the body, hair and hand
cut now runs on the Mummy's pose-aware half-edge collapse (`scripts/mpqem.py`, copied from `mm9_mummy_reduce_claude`):
every output corner is an installed GLB vertex (positions, normals, UVs, joints, weights exact), UV seams locked, cost
scored over 301 poses of every clip, chart guard on (MP_CHART=1: every sample of a new face's UV triangle on the installed
charts), texture guard on the body base colour + region mask and both tier head images. Sets: the pass-2 keep mask and
groups (`giant_sets.py` maps them to GLB faces): face skin, ears, eyes, neck seam, finger pads, wrist graft, soles, hems
exact; hair, palms/backs of hands, calves, feet at 0.7; the rest of the body at the ladder ratio. The mallet primitive is
replaced by the pass-2 rebuild (`mallet_inject.py`, unchanged maps).

| step (body rest ratio) | LOD0 with the rebuilt mallet | p99 / max mm | IoU / SSIM | |
|---|---:|---|---|---|
| **f r60** | **10,016** (body 5,950, head 3,534, mallet 532) | **4.25 / 18.95** | 0.9955 / 0.997 | picked |
| f r45 | 9,468 | 6.89 / 31.1 | 0.993 / 0.995 | pass; clay shows creases across the chest and facets on the shoulder in Hit2 (`review/fix_clay_f60_vs_f45.png`) |
| f r35 | 9,156 | 15.95 / 51.2 | | fail |

LODs 5,008 / 1,801 / 597 (heights 2.554 / 2.554 / 2.553 / 2.560 m, 0 stretched faces; Dead lowest point +0.07 cm).
**UV audit** (`review/uv_audit_fix/audit_mp_f_r60.txt`): LOD0 Giant_A 0, GiantHead_A 0, GiantMallet_A 0 (own charts).
LOD1-3 come from tools/build_actor_lods.py as before: body LOD1 escapes above the installed LOD1's own baseline, LOD2-3
at or below it (the builder's decimate; not part of this fix).
Close-ups (both tiers, read zoomed): `review/fix_f60_closeups_1.png` (belt front, side, back, left pauldron),
`review/fix_f60_closeups_2.png` (right pauldron, chest fur front and 3/4, party): no wedges, the same as installed. Face
pixel-identical in front, 3/4, profile and party (`review/glbclose/diff_f60_*.png`: only hair and body pixels differ).
Gates installed -> f60 (`review/gates_f60/`): grip shaft contact 0.28 -> 0.15 cm, pads identical; mallet in body Fidget
1.81 -> 0, Death 4.20 -> 1.27, Dead 4.20 -> 0, AttackMelee 3.63 -> 3.60; arm/hand left-hand contacts Fidget2 2.7 -> 2.8
cm (7 f), Taunt 2.3 -> 2.4 (4 f), **AttackMelee 2.7 -> 3.0 cm (3 f)**; jitter 20 -> 20 fails; collapse face-frames lower in
every clip; bones, winding 0. Viewer: installed, f60 and r84g for both tiers, 96 switches, no console errors.

Pass 1 (r84g, 13,162) is kept as the fallback in `work/fallback_r84g.glb`.

## Pass 2 (orchestrator, 2026-11-04): rebuilt mallet, relaxed prio-1 keep set

| | LOD0 | body set | head set | mallet | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|---:|---:|---:|
| installed | 15,670 | 8,192 | 3,972 | 3,506 | 7,833 | 2,818 | 937 |
| pass 1 r84g (fallback) | 13,162 | 5,684 | 3,972 | 3,506 | 6,579 | 2,367 | 788 |
| **pass 2 p79** | **9,480 (-39.5 %)** | 5,416 | 3,532 | **532** | 4,738 | 1,701 | 563 |

Where it went: mallet -2,974 (rebuild), body -2,776 (pass-1 cut, plus palms, backs of hands and proximal phalanges at
0.7), hair -440 (0.7). Images, materials, variants and clips are unchanged except the four mallet maps.

**Mallet rebuild** (`mallet_analyse.py` -> sampling -> `mallet_build.py` -> `mallet_texels.py` -> `mallet_rays.py`
(Blender BVH) -> `mallet_bake.py` -> `mallet_inject.py`, all in bind space):
- measured from the installed mallet itself: shaft axis fitted on the shaft pieces, the old surface's maximum radius per
  2 mm along it (dense surface samples), Douglas-Peucker at 2 mm -> an 8-sided lathe (29 stations: collar, wrap rings
  where they stand out, grip taper, pommel flare and point; corners at 1.03 x the old radius so the fists' pads keep their
  contact) from 6 mm inside the head to the pommel tip, and a 5-station top knob; the head is the hexagonal prism of the
  Meshy shell (six corners and radii from its mid section, ends at its extent). Bands, plates, studs, rivets and the
  band-corner spikes are left to the maps. 532 triangles, 452 vertices, rigid on Xhammer (weight 1, as before);
- smooth normals below 0.8 rad (the 45 deg lathe stays round), hard on the hex corners and caps;
- UVs: one strip per lathe part (shaft split at t 0.29), the head's six sides as one strip, two caps, knob; skyline
  packed at 844 px/m with 8 px margins (atlas 58.7 %, density spread 1.01, stretch p90 1.08);
- projection bake (1024, as installed): a ray per texel from 3 cm outside along -normal, first old surface facing the
  same way (97.9 % of texels; the rest, inside the head, nearest surface); base colour, ORM and the 4-channel region
  mask sampled bilinearly (both tiers keep working through the same mask and ramps); the normal map re-expressed from the
  old shading normal + old map into the new frame (fs_model.sc convention: T along +u, B along +v, mapped T*x - B*y + N*z),
  so the old studs, bands and ring relief are in it; gutters filled from the nearest texel.
- Result: `review/sheet_mallet_tex_p79.png` (both tiers: whole, neck, head front and back, grip) and
  `review/viewer_shots_p79.png` (viewer 3/4 and walk, both tiers) look the same as installed; clay
  `review/sheet_mallet_clay_p79.png` shows the lost silhouette bits: the band-corner spikes and side studs (painted now).

**Relaxed keep set** (brief "Prio-1 monsters"): `head_classes.py` marks the hair shell (above the hairline behind the
brow, behind the ears, the side locks; never the face front, ears, eyes or the neck-seam rings; `review/head_classes/
sheet.png`): 1,460 faces at 0.7. Hands: palm, back of hand and proximal phalanges at 0.7 (1,201 faces); the 2nd/3rd
phalanges (the pads on the shaft) and every face with a Forearm weight (wrist graft) stay exact. The kept head faces
take the source normals back after export (`copy_kept_normals.py`): the face renders pixel-identical in front, 3/4,
profile, low 3/4 and party views of both tiers (only hair and body pixels differ: `review/glbclose/diff_*.png`); tier
A's headband and braids read the same (`review/sheet_faces_p79.png`).
Ladder p (REA_HEIGHT_M 2.56): r80 12,612 p99 4.69 / max 25.3; **r79 12,454 p99 5.14 / max 33.0, IoU 0.995, SSIM 0.994**
(the same body budget as pass 1's r84); r78 12,298 p99 5.60. All pass; r79 picked for the body level already reviewed.

Gates pass 2 (`review/gates_p79/`, installed -> p79): grip identical; arm/hand as r84g (Taunt L 2.3 -> 2.4 cm, Fidget2/
Taunt R 0.7 -> 0.8 cm under 1 cm, everything else equal or better); jitter 20 -> 19 fails; collapse face-frames lower in
every clip; bone lengths and winding 0; LOD heights 2.554/2.554/2.552/2.556 m, 0 stretched faces; Dead lowest point
+0.4 cm (as r84g). **Mallet in body**: the vertex gate reads AttackMelee 3.63 -> 7.10 cm (3 frames): the pommel passing
the open left hand at 0.458 s. On dense surface samples (`scripts/mallet_body_probe.py`) the installed mallet is already
7.63 cm there (3 frames) and p79 7.61: the vertex gate missed it on the old mesh; renders `review/pommel_attack_p79.png`
show no difference. Fidget 1.81 -> 0, Death 4.20 -> 1.53, Dead 4.20 -> 0. Viewer check 96 switches, no console errors.


Source: the installed `assets_source/worlds/mm9/models/mm9_giant.glb` (= `../mm9_giant_claude/export/mm9_giant.glb`
r23, sha256 70612b5aee8e...), copied to `before/mm9_giant.glb` (the rollback source). Candidate: `export/mm9_giant.glb`.

## Result

| | LOD0 | body set | head set | mallet | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|---:|---:|---:|
| installed | 15,670 | 8,192 | 3,972 | 3,506 | 7,833 | 2,818 | 937 |
| **reduced (g r84)** | **13,162 (-16.0 %)** | 5,684 | 3,972 (byte-identical) | 3,506 (byte-identical) | 6,579 | 2,367 | 788 |

Images, materials, `KHR_materials_variants`, tier head images (GiantHead_B), clips and skin are byte-identical to the
installed file (checked); only the body primitive changed. LOD1-3 and shadows rebuilt the way the model was built
(`tools/build_actor_lods.py --max-influences 4` -> `shrink_shadow_lods.py` -> `carry_variants.py` -> `fix_winding.py`).

Why only 16 %: 65 % of LOD0 is kept by rule or by result: the head set (face untouchable; the hair carries tier A's
painted braids and studded headband, so no hair cut), both MPFB hands with the solved pad-on-shaft grip (2,776), and the
Meshy mallet (3,506), which does not survive any cut (below). The body had already been cut once at assembly
(`reduce_giant.py`). This is close to the brief's 15 % floor; the orchestrator may also call it "kept".

## What is kept, what is cut (`scripts/make_groups.py`, config g)
- Kept exactly: head set; hands with the wrist graft + one face ring; soles; loincloth hems and flap tips (faces whose
  opposite wall lies within 2 cm, `thin_faces.py`, + one ring); the whole mallet; 10 faces on the back around a posed
  miss (`err_lock.py` on config d, Hit2).
- Own ratios: calves (Calf-dominated: fur and leather shin wraps with raised rims) 0.7, feet and boots 0.7.
- Rest of the body (torso, thighs, arms, shoulder pads): the ladder budget (about 43 % at r84).

## Ladder (REA_HEIGHT_M 2.56: p99 <= 7.68 mm, max <= 38.4 mm; textured, component weights, exact source weights)

| config | change | step | LOD0 | p99 / max mm | IoU / SSIM | verdict |
|---|---|---|---:|---|---|---|
| a | head, hands, soles, mallet grip kept; mallet 0.4 pooled | r75 | 11,750 | 4.87 / 32.5 | 0.993 / 0.995 | pass; rejected (below) |
| b | mallet 0.3 | r70 | 10,968 | 6.01 / 31.2 | 0.980 / 0.989 | pass; mallet head bands twisted |
| c | + feet kept | r74 | 11,594 | 5.41 / 31.2 | 0.992 / 0.994 | pass; back hem dark teeth, mallet rings |
| d | + hems kept, calves 0.8 | r79 | 12,376 | 4.42 / 32.5 | 0.994 / 0.996 | pass |
| e | d + error lock | r76 | 11,906 | 5.59 / 33.0 | 0.992 / 0.993 | pass; mallet rings twisted, rivets pyramids |
| f | mallet per piece 0.5 | r78 | 12,218 | 5.30 / 33.0 | 0.993 / 0.994 | pass; head bands broken into wedges |
| g | mallet kept, feet/calves 0.7 | r85 / **r84** / r83 / r82 | 13,318 / **13,162** / 13,006 / 12,848 | 4.94/25.3, **5.38/33.0**, 6.09/33.0, 7.02/36.2 | **0.994 / 0.994** at r84 | all pass |
| h | g + second error lock | r84 / r83 | 13,240 / 13,084 | 7.47 / 26.6, 8.76 / 33.9 | | worse (the lock moved the error), dropped |

Picked **g r84**, not the lowest passing g r82: r82's GLB clay close-ups show faceted shoulders/back and lumpy buttocks
and 26 posed misses over 20 mm (`review/glb_clay_g.png`). Measured rule and gates are met at r84.

Lessons for the batch:
- **The Meshy mallet cannot be cut**: pooled at 0.4 the quadric collapsed the small closed pieces first (tiny absolute
  error): the wrap rings under the head twisted, the round rivets became pyramids; decimated per piece at 0.5 the thin
  iron bands round the head broke into wedges (`review/glb_mallet_zoom_e76.png`, `glb_mallet_zoom_f78.png`). It is
  copied byte for byte (`swap_lod0.py` KEEP_PRIMS).
- **The body skin is closed**: thin loincloth flaps are two walls 1-2 cm apart; their tips crossed under the cut and
  showed the inside as dark teeth (config c, `review/glb_clay_body.png`). Keep faces with a near opposite wall.
- **source.blend lies about shading** (as the MM8 lessons say): its feet looked faceted and the reduced ones "bulbous";
  the GLB renders show the same boots. Judge from `glb_close.py` only.
- **export_cand.py's floor lift must go**: the Giant's mesh sits 1.28 m under its node, so lifting z < 0 would have
  flattened the lower half; the soles are kept instead.
- Mallet and head normals are copied with their primitives; recomputed mallet normals differed (hard-surface split).

## Gates (installed -> reduced, both run here with the giant project's own scripts on the runtime GLBs: `scripts/gates.sh`)
Numbers in `review/gates_before/` and `review/gates_r84g/` (model cm; x3.33 for world size).

| gate | installed | reduced r84g |
|---|---|---|
| grip (`grip_gate.py`, joints, inside, wrap, pad gap, every clip) | | identical |
| mallet in body | Fidget 1.81 (2 f), AttackMelee 3.63, Death 4.20 (2 f), **Dead 4.20 (25 f)** | Fidget 1.08 (1 f), AttackMelee 3.50, Death 1.50, **Dead 0** |
| fingers in shaft R / L | R <= 0.30, L <= 2.79 (AttackMelee) | identical |
| arm/hand in body (`--outer-only --exact`) | Fidget2 L 2.7 (7 f), Taunt L 2.3 (4 f), AttackMelee L 2.7 (3 f), Fidget2/Taunt R 0.7 | Fidget2 L 2.7 (7 f), **Taunt L 2.4 (4 f, +0.1)**, AttackMelee L 0, Fidget2/Taunt R 0.8 (0 f > 1 cm) |
| jitter (vs MM9 reference clips) | 20 fails | 19 fails (clips unchanged; the shoulder-skin term follows the mesh) |
| collapse face-frames Hit2 / Death / Death2 / Dead | 2,350 / 5,945 / 8,920 / 1,922 | 2,121 / 4,548 / 5,831 / 2,015 |
| detached parts, bone lengths, winding | mallet shallow by design, 0, 0 | same |
| flat shading body / mallet | 0.01 / 0.05 | 0.00 / 0.05 |
| texture quality body: atlas, stretch p90 | 55.1 %, 1.13 | 53.7 %, 1.34 (UV-keeping collapse; textured sheets show no change) |
| LOD heights (LOD0-3) | 2.554 / 2.554 / 2.556 / 2.554 m | same; 0 stretched faces at every LOD |
| floor (lod_check, lowest point) | Dead 0.0, Standing 0.0 cm | **Dead +0.4 cm** (corpse 4 mm up: its lowest point was on the cut thigh/buttock; clips are untouched), Standing +0.01 |

## Review
- Viewer (installed and reduced, both tiers, all 16 clips): http://127.0.0.1:8912/level_generation/creatures/mm9_giant_reduce_claude/review/viewer/
  (`run_creature_review.py check`: 64 switches, no console errors).
- Sheets: `review/sheet_faces_r84g.png` (face front, 3/4, profile, low 3/4, party; both tiers; head rows 0 pixels
  changed), `review/sheet_body_tex_r84g.png`, `review/sheet_body_clay_r84g.png`, `review/sheet_mallet_hands_r84g.png`,
  `review/sheet_lods_r84g.png`. Ladder numbers per config: `work/selection_<config>.json` (the ladder renders and `review/ladder_sheet.png` hold the last run, h).

## Install (not run; on the user's OK)
`check_winding.py export/mm9_giant.glb` (0), `tools/install_model.py export/mm9_giant.glb --world mm9`, the
`mm9_actor_models_build_every_binding` regression, then add to `../mm9_giant_claude/README.md`: "LOD0 reduced
post-install on <date> by `mm9_giant_reduce_claude`; a rebuild from this project must re-run that reduction".
Rollback: `before/mm9_giant.glb`.

## Reproduce
`REA_GLB=level_generation/creatures/mm9_giant_reduce_claude/before/mm9_giant.glb REA_NODE=Giant`: `find_doubles.py` (0),
`import_source.py`, `dump_mesh.py`, `dump_faces.py`, `dump_weights.py`, `grip_band.py`, `thin_faces.py` (THIN=0.02),
`KEEP_MALLET=1 FEET_RATIO=0.7 CALF_RATIO=0.7 make_groups.py`, keep_g = keep + `keep_err.npy`,
`REA_WEIGHTS=component REA_KEEP_FACES=work/keep_g.npy REA_GROUPS=work/groups.npy REA_GROUP_RATIOS=3:0.7,4:0.7
run_ladder.sh g 0.85,0.84,0.83,0.82`, `REA_BLEND=ladder_g.blend build_export.sh Cand_84`, `viewer_tiers.py`,
`glb_close.py`, `lod_check.py`, `lod_views.py`, `gates.sh`, `make_viewer_manifest.py`.
