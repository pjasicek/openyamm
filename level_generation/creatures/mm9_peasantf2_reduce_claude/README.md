# MM9 PeasantF2 (`mm9_peasantf2`, woman with braid; rows 31, 32, 38, 39) reduction: candidate f r45 ready for review (2026-11-05)

Batch: [REDUCTION_BRIEF_20261104.md](../../../devdocs/mm9_rework/overnight/REDUCTION_BRIEF_20261104.md) (prio-2 townsfolk, relaxed
keep set), ledger row 9 of [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md). Lease `mm9reduce:peasantf2` (owner
peasantf2-reduce-20261104); the creature's own `mm9:peasantf2` lease was free. Source: the installed
`assets_source/worlds/mm9/models/mm9_peasantf2.glb` (r24, sha256 1834cf185349), copied to `before/` (the rollback source). No Meshy,
no credits, no repaint. **Not installed.** `../mm9_peasantf2_claude/` was only read (its scripts, `work/uv_lined.npz`, textures,
ref clips); `mm9_fre_claude` was not touched.

| | LOD0 | body (PeasantF2_A) | head set (PeasantF2Head) | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|---:|---:|
| installed | 14,936 | 8,278 | 6,658 | 7,424 | 2,669 | 887 |
| **f r45 (`export/mm9_peasantf2.glb`, sha256 3f82f999be64)** | **11,125 (-25.5 %)** | 5,451 | 5,674 | 5,560 | 1,998 | 662 |

Every vertex of the candidate is an installed vertex (positions, normals, UVs, joints, weights are the installed bytes; only index
buffers changed). Clips, skin, nodes, materials (doubleSided head set), region ramps, `KHR_materials_variants`, all 8 images:
byte-identical (`same_clips.py`). Head, face, neck, eyes: the installed triangles; the face renders pixel-identical in both tiers
(`review/shots/diff_{a,b}_f*.png`: face and neck black in all five views).

## Measured first
Parts per GLB face from the creature's `work/uv_lined.npz` (`scripts/pf2_parts.py`: body by rest centroid, head by centroid + UV
and a vote per connected piece): head shell with face/neck/skull 3,258 + eyes 418, hair cap 966 (+ rim lining), braid 1,822, nape
tie 194, dress 2,464 (bodice, sleeves, bell cuffs), skirt 1,400 with a 4 mm inner lining (1,400 + 70 hem rim faces), beads 598,
buckle 86, shins 616 + sole pieces 144, MPFB hands 1,500. The bodice and skirt were already cut at assembly (large triangles), so
the cut comes mostly from hands, hair, braid and the skirt/lining pair. The hidden scalp under the cap is only ~470 faces (the
skull top is an open, capped shell) and was kept.

Kept exactly (`scripts/make_sets_pf2.py`, 44 %): the whole head part (face, neck seam, skull, eyes) and every inner face (skull/
hand-stub/waist caps, the cap's rim lining), beads, buckle, soles and sole pieces, the hairline (cap faces within 6 mm of skin) and
the cap's rim band (1 cm), the hand-graft junction (Forearm-weighted hand faces, 2 cm round the stub caps), the bell cuffs (dress
within 10 cm of the stub caps), the neckline (1.5 cm), the waist cap band, the skirt lining's hem rim strip, the nape tie.
Groups: hands 0.6 (every finger kept), hair cap 0.6, skirt outer shell 0.55 (lining re-emitted from the cut shell's twins, 4 mm in),
shins 0.5 (inside the skirt), braid 0.55; bodice and sleeves take the ladder ratio.

## Route: pose-aware half-edge collapse (`scripts/mpqem.py`, the Highwayman's copy)
Scored over every clip at 10 Hz plus a position+UV rest quadric; only removes vertices; texture guard on the body tone + region mask
and both head paints (refuse > 100 any sample / > 45 mean). PeasantF2 changes (orchestrator's UV-escape rule, 2026-11-04):
- a chart guard: a collapse is refused when a new face's UV triangle leaves the source charts (2048 raster, dilated 2 texels);
- skirt-lining twins: per re-emitted face the combination of coincident lining vertices on one chart (smallest UV perimeter), and the
  outer vertices whose twins sit on a lining UV seam are locked (194); without these 195 lining faces crossed two charts;
- `scripts/fix_lining_uv.py`: the last 10 lining faces (back centre seam, side seams) take lining vertices within 4 mm of their
  twins (moved <= 1.64 mm, hidden inside the skirt) so that they stay on one chart; one index-degenerate face dropped.
UV escape (`scripts/uv_escape.py` and `claude_shared/reduction_uv_audit.py`): **LOD0 0** (body 0, head 0). LOD1-3 (Blender's
decimate in `tools/build_actor_lods.py`): 208 / 252 / 120 faces against the installed LODs' 140 / 231 / 166 (`review/uv_audit_f45.json`).

## Ladders (height 1.765 m: p99 <= 5.29 mm, max <= 26.47 mm, IoU >= .98, SSIM >= .93; `review/ladder_sheet_<label>.png`)
| ladder | groups (hands / cap / skirt / shins / braid) | step | LOD0 | p99 / max mm (worst) | IoU / SSIM | |
|---|---|---|---:|---|---|---|
| b | .65 / .65 / .6 / .5 / .75 | r50 / r40 / r30 | 11,765 / 11,599 / 11,481 | 2.99/14.9, 4.11/20.7, 7.37/47.3 (Conv1) | .997/.996 ... | pass / pass / fail |
| c | .6 / .6 / .55 / .4 / .55 | r45 / r40 | 11,093 / 11,009 | 4.05/28.9 (Cower:0, shins) | .996/.996 | fail / fail |
| d | .6 / .6 / .55 / .5 / .55 | r45 / r40 | 11,125 / 11,041 | 3.66/14.9, 4.14/20.7 | .996/.996 | pass / pass |
| e | d + chart guard + one-chart lining | r45 / r40 | same counts | same | | pass / pass (20 lining faces still escape) |
| **f** | e + seam-twin locks (+ fix_lining_uv) | **r45** / r40 | **11,125** / 11,041 | **3.70/14.94 (Death:24)**, 4.15/20.7 | **.996/.996** | **PASS, picked** / pass |
r40 saves 84 more triangles for a higher error; r45 picked.

## Gates, installed -> f r45 (`scripts/gates.sh`, the creature's own scripts; `review/gates_before/`, `review/gates_f45/`)
- Arm/hand (`--outer-only --exact`): 0 frames > 1 cm in every clip both; maxima equal or lower except Conv1 R forearm 0.1 -> 0.4 cm
  (Conv3 L forearm 1.0 cm in one frame, as installed); finger stretch within +0.07 (Running/Cower L p50).
- Robe (legs through skirt): 0 frames in all 11 clips, identical. Skin poke (hand stub through sleeve/cuff): 0.0 mm, identical.
- Collapse face-frames lower or equal in every clip (Death 1,888 -> 1,475, Dead 868 -> 589, Standing 152 = 152).
- Jitter vs the creature's MM9 reference (`work/ref_half.glb`): 2 fails both (Death shoulder skin 33.70 -> 33.75 mm/f2, the
  installed clips' own grounding; the creature's 0 was measured on `work/half.glb`); other clips' shoulder-skin excess <= 0.88 mm/f2.
- Flat 0.00/0.00, winding 0, bones 0 stretching, texture quality equal (body 64.2 %, head 61.1 %; stretch p90 1.05 -> 1.06),
  detached: the same 5 free legs/hands parts (by design), worst distances equal, shin pose counts higher (518 -> 702).
- See-through (double=1, `review/gates_{before,f45}/seethrough/`): maxima equal (sleeves 0 = 0, torso 9 = 9 px, collar 2 = 2 px, head 1 = 1
  px); frames with any hole: torso 86 -> 82, collar 28 -> 43 (1-2 px each), head 1 = 1.
- LODs (`scripts/lod_check.py`, every frame of every clip; `work/lod_check_{installed,f45}.json`), built by `scripts/build_lods.py`
  (floor, crown, braid tip and corpse contact protected, snapped to imported vertices): height 1.762 m at every LOD (installed
  1.762-1.763); Dead 0 at every LOD (installed LOD2/3 +0.23/+0.33 cm, floating); lowest point per clip equal to LOD0 at every LOD
  except LOD2/3 Hit -1.09 cm (installed -0.52, LOD0 -1.09); faces stretched > 20x: 0 everywhere (both).

## Review
Viewer (installed and reduced, both tiers, all 11 clips; `run_creature_review.py check`: 44 switches, 0 failed, no console errors):
http://127.0.0.1:8912/level_generation/creatures/mm9_peasantf2_reduce_claude/review/viewer/
Sheets read: `review/sheet_face_f45.png` (front close-up, 3/4, true profile, low 3/4, party; both tiers), `review/shots/diff_a_f0.png`,
`review/sheet_body_f45_{a,b}.png` (Standing front/3-4/back, Walking, Conv3, Death), `review/close_f45_a.png` (arms/hands, skirt
front/back, Running, feet, Conv1 arms, shoulders and braid from behind, Cower), `review/crop_braid_f45.png` (braid in profile
and from behind), `review/crop_bodice_f45.png`, `review/ladder_sheet_{b,d,f}.png`, `review/sets_a.png`.
Look at: the braid in profile (plait lumps a little softer on the back edge), the bodice brocade (same pattern, shading on larger
triangles a little different), fists (60 %).

## Build (project folder)
```sh
G=../claude_shared/gltf_venv/bin/python; BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"
REA_GLB=level_generation/creatures/mm9_peasantf2_reduce_claude/before/mm9_peasantf2.glb REA_NODE=PeasantF2 $BL -P scripts/import_source.py
$BL -P scripts/dump_mesh.py; $G scripts/pf2_parts.py; $G scripts/tex_extract_pf2.py
BRAID_KEEP=0 $G scripts/make_sets_pf2.py b; cp work/glb_sets_b.npz work/glb_sets_f.npz
SETS=f MP_GROUPS=1:0.6,2:0.6,3:0.55,4:0.5,5:0.55,6:1 scripts/run_mp.sh f 0.45,0.4
$G scripts/fix_lining_uv.py work/mp_f_r45.npz work/mp_f_r45u.npz
scripts/build_mp.sh mp_f_r45u export/mm9_peasantf2.glb     # swap -> single head -> protected LODs -> shadow -> variants -> double head -> winding
scripts/gates.sh export/mm9_peasantf2.glb f45; $G scripts/uv_escape.py before/mm9_peasantf2.glb export/mm9_peasantf2.glb
```
Install (on the orchestrator's/user's OK only): `check_winding.py export/mm9_peasantf2.glb` (0), `tools/install_model.py
export/mm9_peasantf2.glb --world mm9`, the `mm9_actor_models_build_every_binding` regression, and add to
`../mm9_peasantf2_claude/README.md`: "LOD0 reduced post-install on <date> by `mm9_peasantf2_reduce_claude`; a rebuild from this
project must re-run that reduction". Rollback: `before/mm9_peasantf2.glb`.

## Not checked
In game; motion at normal speed by eye (gates and viewer stills only); LOD1-3 and shadow meshes by eye (numbers only); close-ups of
the hands in motion clips (body sheets only).
