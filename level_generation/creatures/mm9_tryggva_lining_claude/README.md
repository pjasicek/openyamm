# Tryggva Ravenlocks (`mm9_tryggva.glb`) see-through linings, 2026-11-05

Lease released at the end. Brief: [LINING_BRIEF_20261105.md](../../../devdocs/mm9_rework/overnight/LINING_BRIEF_20261105.md) (user approved linings on this
approved body on 2026-11-05). Lease `mm9lining:tryggva` (owner tryggva-lining-20261105); `mm9:tryggva` and `mm9reduce:tryggva`
were free. Source: the installed `assets_source/worlds/mm9/models/mm9_tryggva.glb` (sha256 b05c4f506cf4, = the creature's
`export/mm9_try.glb`), copied to `before/` (rollback). `../mm9_tryggva_claude/` and `../mm9_tryggva_reduce_claude/` were only read.
No Meshy, no repaint, no Blender rebuild from the master. **Nothing installed.**

**Candidate: `export/mm9_tryggva_lined.glb`** (sha256 6c9d55650feb, = `work/v7.glb`; spec `export/mm9_tryggva_lined_spec.json`,
report `export/mm9_tryggva_lined_report.json`; rebuild: `python3 scripts/glb_lining.py before/mm9_tryggva.glb <out> export/mm9_tryggva_lined_spec.json`
from the project folder, it reads the gate JSONs under `review/`).

| | installed | lined | added |
|---|---:|---:|---:|
| LOD0 (body + head set) | 8,405 (2,270 + 6,135) | 10,160 (2,987 + 7,173) | +1,755 |
| LOD1 | 4,200 | 5,551 | +1,351 |
| LOD2 | 1,505 | 2,075 | +570 |
| LOD3 | 495 | 690 | +195 |
| shadow LOD0-3 | 8,405 / 4,200 / 1,505 / 495 | unchanged | 0 |

LOD0 additions by opening: fur capes 225 lining (own-UV twins 1.5 mm under the cape: the underside reads as fur) + 162 rim
strips; cuffs 138 + 52; collar 140 (no strips); hair 805 (0.5 mm,
no strips); fur lapels in the head set 89 + 144. More than the brief's "about a thousand": the hair alone is 805 (its locks are
open sheets everywhere; the lined faces are the ones the gate found holes on). Texels (body / head image): cape rim strips
(0.118, 0.071, 0.031), tunic cuffs (0.043, 0.016, 0.008), collar (0.173, 0.145, 0.122), hair and lapels (0.094, 0.051, 0.043).

See-through (`scripts/see_through_gate.py`, sweep settings, every clip; max px per zone):

| zone | installed | lined | worst lined view |
|---|---:|---:|---|
| sleeve R | 590 | 15 | Death 32 az000 |
| sleeve L | 502 | 15 | Death 24 az000 |
| torso | 406 | **35** | Death 28 az315 (all other clips <= 25: Fidget 25, Hit 21) |
| head | 42 | 14 | Walking 8 az225 |
| collar | 22 | 18 | Death 24 az000 |
| boots, trousers, none | 0 / 0 / 2 | 0 / 0 / 1 | |

Torso stays above 20 in Death only: scattered one-to-three-pixel slivers between hair locks seen from the ground under the lying
corpse (`review/v2_torso_crop.png` is the same pattern); one more hair round (+218 triangles, v5) only took it to 32.
LOD1 / LOD2 (step 8, `review/gates_{before,v3}_lod{1,2}/`): sleeve R 560 -> 45 / 677 -> 102, sleeve L 515 -> 21 / 606 -> 67,
torso 416 -> 54 / 456 -> 128, head 39 -> 18 / 58 -> 54, collar 13 -> 13 / 11 -> 5; no zone worse. LOD3 not gated.

## What the openings were (installed, `review/gates_before/`, `scripts/hole_pieces.py`)
The 2026-11-02 sweep's numbers reproduce exactly (`scripts/see_through_gate.py` = PeasantDM2's gate plus a per-face hole dump,
`faces=1`; sweep settings step 4, 4 mm pixels, 16 views, every clip). Hole pixels by piece (summed over every view and frame):
- **sleeve L/R 502/590: the two fur shoulder capes** (body pieces 1 and 6, 107/118 faces, weighted UpperArm/Clavicle): open
  single-sided sheets; with the arm raised (Fidget, AttackMelee) or seen from behind/below, the view goes up into the cape and
  finds only its back faces (`review/probe3_sheet.png`, `review/probe4_sheet.png`). 386k of 498k hole pixels.
- the tunic's cuffs (Meshy's jagged fringe, tunic piece, Forearm weights): 106k.
- **torso 406 and head 42: the hair shell** (head piece, 2,267 faces of thin locks, every face within 4 cm of its 722-edge rim;
  the back hair is weighted to `Bip01 Ponytail1`, which the gate counts as torso): the undersides of the locks, mostly in the
  lying corpse; 92k. The fur lapels Meshy fused into the head set (small head pieces, Clavicle/Neck): about 5k.
- collar 22: the collar piece (open at both edges) 2.7k plus the tunic's neck faces.
- Not needed (no holes): tunic hem, belt, trousers waist, boots. The tunic's and the face shell's neck rims coincide (the
  head/body seam on the collar cloth) and stay open as installed.

## Route (`scripts/`)
GLB-level, no Blender scene: `glb_lining.py <in> <out> <spec> [report]` adds lining faces to the installed file (DM2's
`rim_lining.py` technique re-implemented on the GLB's own arrays, numpy only):
1. Per visual LOD mesh and spec: open boundary loops of the spec's primitive (welded by position) mostly weighted to the
   spec's bones; loops on another primitive (the neck seam) and pieces holding a large share of the primitive are skipped.
2. Band = faces of the loop's piece within `depth` of the loop; optionally limited to (`holes.mode limit`) or extended by
   (`add`) the faces the see-through gate found holes on (`face_holes` of one or more gate runs, `min_sum` pixels).
3. Band vertices duplicated `offset` behind themselves along the negated area-weighted normal (at most 40 % of the distance to
   any other face that direction meets within 2 cm), band triangles copied with reversed winding; loop edges joined to their
   twins by outward rim strips (fur capes and cuffs only). Lining and strip vertices copy joints and weights of the vertex they
   line; strip corners on the rim sit exactly on the original vertex. Normals negated (strip: face normal).
4. Texel: one dark texel of the garment's own paint: an 8x8 window on painted chart (UV coverage raster, the MM9 gutters are
   black) whose mean luminance is closest to the band's 15th-percentile tone, flattest first. Shared per garment (both capes,
   both cuffs) and per LOD (LOD0's texel). A lining's three UVs are one point, so the GPU samples mip 0 there.
5. Coarser LODs: the same loops/bands on each LOD's own geometry; hole-driven bands take an LOD face when half its area lies
   within `near_m` (per LOD 3 / 4.5 / 10 mm) of the LOD0 band with the same facing.
6. Write: changed primitives get new accessors = the original rows byte for byte + appended rows of the same component types;
   unreferenced accessors dropped. Shadow meshes untouched (DM2 dropped the one-texel linings there).

Iterations (LOD0 added triangles; see-through zone maxima sleeve L / sleeve R / torso / head / collar):

| run | change | LOD0 + | sleeve L | sleeve R | torso | head | collar |
|---|---|---:|---:|---:|---:|---:|---:|
| installed | | 0 | 502 | 590 | 406 | 42 | 22 |
| h40 | capes + strips, cuffs 22 cm + strips, collar + strips, hair faces with >= 40 hole px, 3 mm | 1,239 | 43 | 56 | 90 | 28 | 20 |
| v2 | hair 0.5 mm, faces >= 20 px of both runs; cuffs + hole faces within 50 cm; lapels | 1,603 | 18 | 20 | 66 | 20 | 20 |
| v3 | hair/lapels faces >= 10 px of three runs; collar without strips | 1,755 | 15 | 15 | 35 | 14 | 18 |
| v5 | v3 + faces >= 5 px of four runs, no strips on capes/cuffs | 1,759 | 58 | 56 | 32 | 11 | 18 |
| v3 (pre-screen: not accepted) | | 1,755 | 15 | 15 | 35 | 14 | 18 |
| v6 (rejected) | v3 without the lapel strips (1 mm offset) | 1,611 | 17 | 18 | 35 | 14 | 18 |
| **v7 = candidate** | v3 with the cape linings as own-UV twins (fur UVs kept, 1.5 mm; `own_uv` in the spec) | **1,755** | 15 | 15 | 35 | 14 | 18 |

Orchestrator pre-screen of v3 (2026-11-05): the cape undersides showed as large flat near-black slabs past the arm silhouette
(Fidget 12, AttackMelee 28, Talk 88). Fix as Sven's hair: for the two capes only, the lining faces are reversed copies keeping
the cape's own fur UVs (one twin per split vertex), 1.5 mm under the cape; strips keep the dark fur texel. Everything else is v3.
Accepted by the orchestrator without change: the AttackMelee jitter rise, torso 35 px in Death, +1,755 triangles.

v5 shows the rim strips are needed on the capes and cuffs (the 3 mm slot between cloth and lining opens at the hem); one
more hair round (+218 triangles) only moved torso 35 -> 32. v6 left a 2-triangle lapel lining island unjoined: the
detached-parts audit flagged it (7.4 mm from the body cluster in 6 of 675 poses), so the lapel strips stay (v3).

## Gates (installed -> v7; `review/gates_before/`, `review/gates_v7/`; v3's in `review/gates_v3/`)
| Gate | installed | lined |
|---|---|---|
| Additions only (`scripts/verify_identity.py`) | | **OK**: every original vertex row (all attributes), triangle, image, material, skin, node, clip byte-identical; new triangles use new vertices only |
| Lining poke (`scripts/lining_poke.py`, every clip, step 4, 16 views; lining nearer than outside cloth) | | max 25 px (v3: 35; 1-px lines where a fill meets the cloth edge or along the cape hem), **blob 0** (3x3-eroded: no lining patch on the cloth in any clip); rim strips over cloth (the cut edge) max 45 px |
| Arm/hand (`arm_hand_gate.py --outer-only --exact`) | | equal except Fidget R forearm 2.9 -> 0.8 cm and Applause L forearm 1.9 -> 2.0 cm (the inside test now sees the cuff lining; hands identical) |
| Sleeve poke | 0 mm all clips | 0 mm all clips (identical output) |
| Jitter (`jitter_gate.py` vs MM9 clips) | 0 fails | **2 fails, AttackMelee shoulder skin L 0.74 -> 4.06, R 0.24 -> 3.30 mm/f2**: the clips are byte-identical; the cape linings and strips (UpperArm/Clavicle weights) join the shoulder-skin vertex sample and move its p95 to the cape hem. `scripts/lining_motion.py`: every lining vertex moves as the vertex it lines (offset grows <= 0.36 mm, second difference within 1.7 mm/f2 of its source in AttackMelee). Hanndl's lined GLB showed the same |
| Detached parts | 0 (24 components) | 0 (60 components) |
| Winding | 0 | 0 |
| UV audit (`reduction_uv_audit.py` vs installed) | LOD0 0 | **LOD0 0 escaping**; head LOD1-3 = installed (146/200/173); body LOD1-3 80/99/59 vs installed 77/93/54: the extra are own-UV cape twins of installed LOD faces that already escape (as Sven) |
| Floor / height per LOD (`scripts/lod_floor.py`, every clip, 30 fps) | | identical by number at LOD0-3 |
| Flat shading, bones | 0.00, 0 stretching | 0.00, 0 stretching |

## Sheets read
All read at full size (`review/`): `face_diff_check.png` and `sheet_v7_diff_face_{front,34}.png` (face skin black; the only
differences are former see-through gaps in the side locks, now dark hair lining), `sheet_v7_body.png` (front, back, side,
party view, faces: the same from outside), `sheet_v7_fur.png`, `sheet_v7_cuffs.png`, `sheet_v7_collar_hair_hem.png`,
`sheet_v3_sweep.png` (the sweep's worst view of each zone, textured and with red interiors, installed vs lined),
`final_before_sheet.png`, `probe1..5_sheet.png`, `h40_worst.png`, `poke2_h40_sheet.png`, `poke_v2_sheet.png`, gate shots in
`gates_v3/`. Boot tops and hem have no openings in the gate and were not lined (`hem_below` pair unchanged).

What to look at: the capes' undersides. Where the cape flares off a raised or bent arm (Fidget 12 from the front, AttackMelee
28, Talk 88) the inside that used to be invisible now shows the cape's own fur paint (`sheet_v7_fur.png`, `furR_fidget12`,
`furL_attack28`, `furL_talk88`): the cape's real extent past the arm silhouette, drawn as fur from inside (v3's flat dark slabs:
`sheet_v3_fur.png`). The hair undersides in the corpse are dark hair instead of holes. Sheets for v7 re-rendered: body, face
diff, fur; cuffs, collar/hair/hem and sweep sheets are v3's (those meshes and texels are identical in v7) and were read at full
size there.

## Not checked
- Not installed; binding regression skipped (orchestrator's). Not looked at in game or in the creature viewer; motion not watched
  at speed (Blender stills and numeric gates only).
- LOD3 see-through not gated; LOD1/LOD2 gated at step 8 only. Lining poke run on LOD0 only.
- Shadow meshes left as installed (no linings), not re-checked in game.
- Texture quality (`texture_quality.py`) not rerun: the one-texel lining triangles skew its density/stretch numbers (DM2,
  Hanndl); the images are byte-identical.

## Files
`scripts/glb_lining.py` (the tool), `verify_identity.py`, `see_through_gate.py` (+ `see_through.sh`), `lining_poke.py`,
`hole_pieces.py`, `rims.py`, `lod_swap.py`, `lod_floor.py`, `lining_motion.py`, `views.py`, `pair_sheets.py`, `sheet.py`,
`st_compare.py`, `gates.sh`, `bl.sh`, `cap.sh`, `glbpack.py`/`bglbio.py` (from the reduction). Candidates in `work/` (h40, v2,
v3, v5, v6); only `export/mm9_tryggva_lined.glb` is for install.
