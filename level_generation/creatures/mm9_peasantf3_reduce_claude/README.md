# MM9 PeasantF3 (`mm9_peasantf3`, the young townswoman with a veil and braids) reduction: candidate g r50 ready for review (2026-11-04)

Batch: [REDUCTION_BRIEF_20261104.md](../../../devdocs/mm9_rework/overnight/REDUCTION_BRIEF_20261104.md) (prio-2 townsfolk: the
relaxed prio-1 keep set, face exact), ledger row 7 of [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md). Lease `mm9reduce:peasantf3`
(owner peasantf3-reduce-20261104); the creature's own `mm9:peasantf3` lease was free. Source: the installed
`assets_source/worlds/mm9/models/mm9_peasantf3.glb` (sha256 4c8f6d61cc07, identical to `../mm9_peasantf3_claude/export/`), copied
to `before/` (the rollback source). No Meshy, no credits, no repaint. **Not installed.** `../mm9_peasantf3_claude/` was only read.

| | LOD0 | head (face, neck, eyes, teeth) | veil | braids | hood | dress | skirt | lining | legs | arms + hands | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| installed | 14,982 | 3,616 | 600 | 476 | 1,150 | 2,598 | 1,362 | 850 | 760 | 3,570 | 7,350 | 2,645 | 1,050 |
| **g r50 (`export/mm9_peasantf3.glb`, sha256 6b471244d7a0)** | **12,162 (-18.8 %)** | 3,616 | 600 | 476 | 1,034 | 2,006 | 952 | 850 | 638 | 1,990 | 5,944 | 2,138 | 1,015 |

Every vertex of the candidate is an installed vertex (positions, normals, UVs, joints, weights are the installed bytes; only index
buffers changed). Clips (11), skin, nodes, materials, region ramps, `KHR_materials_variants`, all 8 images: byte-identical
(`same_clips.py`). Head, veil and braids: every installed triangle present exactly (checked by vertex position + UV + normal), so the
face renders pixel-identical in both tiers (`review/sheet_face_diff_g50.png`: face black in all five views of pf3_a and pf3_b;
only the necklace/bodice shading below the neckline, the hood rim and the shoulders differ).

## Measured first: protected share
Part labels from the creature's last pre-GLB mesh (`../mm9_peasantf3_claude/work/uv_tex2_chin.npz`, `scripts/glb_parts.py`; the
head primitive by connected component because the veil and braid vertices moved after that file). Head + veil + braids are 31 %
of LOD0; with the hood edge, collar, soles, small pieces (lacing) and the skirt lining the final set g keeps 53 %. The cut comes
from the MPFB arms and hands (3,570, the largest part), the dress, the skirt, the hidden legs and the hood.

Keep set (`scripts/make_sets_pf3.py`, set g): the whole head part, the veil (thin sheet + lining: a cut shredded it at the build)
and the braids (already merged 4 rings into 1); hood faces within 8 mm of the head shell and within 15 mm of the veil; dress
faces within 1 cm of the neck (collar seam); dress and hood faces within 2.5 cm of a veil or braid vertex (the headwear's
clearance); both short sleeves (dress beyond |x| 15 cm: set f cut them and the arm stub came 1.8 mm through the R sleeve in Conv1);
soles (leg faces within 1.2 cm of the floor); pieces up to 80 faces (lacing); the skirt lining (F1's, decimated to 60 % at the F3
build, so it is not a twin of the skirt and cannot be re-emitted like the Highwayman's).
Groups: hand + fingers 0.6 (seam slides; every finger kept), arm skin 0.45, hood 0.7, skirt 0.7, shoes 0.7, hidden calves 0.85
(0.4 cost 21 mm in Death), dress at the ladder ratio.

## Route: pose-aware half-edge collapse (`scripts/mpqem.py`)
The Thrall's copy (Lesser Demon seam slides, `MP_SEAM_GROUPS=1` on the hands) with: a texture guard over each tier's baked body
colour (tone x region ramps), each tier's head image and the region mask (`scripts/tex_extract.py`; refuse > 100 any sample /
> 45 mean); the Mummy's chart guard (`MP_CHART=1`: every sample of a new UV triangle on the installed charts; sampled at 12
subdivisions like `uv_escape.py` - at 8 two fingertip faces still reached 3 % outside); texture weight 4 (`MP_W5`, brief 3-8).
Scored over 291 poses (every clip at 10 Hz) plus a position+UV rest quadric.

## Ladders (limits for 1.792 m: p99 <= 5.38 mm, max <= 26.9 mm, IoU >= .98, SSIM >= .93; `review/ladder_sheet_<label>.png`)
| ladder | set / change | step | LOD0 | p99 / max mm (worst) | result |
|---|---|---|---:|---|---|
| a | a: hands .55, arms .5, calves .4 | r70 / r60 / r50 | 11,964 / 11,740 / 11,516 | 1.98, 2.37, 3.08 / 21.5 (Death: hidden calves) | pass |
| b | a, hands .5, arms .45, hood/skirt .7 | r45 / r40 / r35 | 11,120 / 11,008 / 10,960 | 4.2/21.5, 5.92, 7.34 | pass / fail / fail |
| c | b, calves .85 | r50 / r45 | 11,282 / 11,170 | 2.88/17.8, 3.78/16.3 | pass; 28 faces leave the UV charts |
| d | c + chart guard + W5 4 | r45 | 11,170 | 3.78 / 18.9 | pass; built: hands at 0.5 a little angular at the fingertips, headwear gate veil 1.3 -> 1.9 cm (Standing), braids 0 -> 0.4 cm at rest |
| e/f | e: d + headwear contact kept, hands .6 | r50 / r45 | 11,806 / 11,710 | 2.97/16.8, 4.18/25.6 (Conv3) | pass; f r50 built: headwear equal or better, sleeve poke Conv1 R 0 -> 1.8 mm (17 f) |
| **g** | **g: f + sleeves kept** | **r50** / r45 | **12,162** / 12,122 | **2.64 / 18.9 (Death:30)**, 3.30/25.6 | **PASS, picked** (IoU .9975, SSIM .9949) / pass |

## Gates, installed -> g r50 (PeasantF3's own scripts, `scripts/gates.sh`; `review/gates_before/`, `review/gates_g50/`)
- Collapse face-frames lower in every clip (Hit 5,180 -> 4,511, Cower 3,564 -> 2,565, Death 2,601 -> 2,329).
- Robe (legs through the skirt): 0 in every clip, both. Sleeve poke (`sleeve_poke_pf1.py`): 0 mm in every clip, both.
- Arm/hand (`--outer-only --exact`): 0 frames > 1 cm in every clip, both; hand depth Standing R 0.2 -> 0.3, Hit R 0.2 -> 0.3,
  Hit L 0.8 -> 0.7 cm; finger stretch maxima equal.
- Headwear (`headwear_gate_pf3.py`): rest veil 2.76 / braids 0.0 cm both; per-clip maxima equal or lower except Death veil
  1.4 -> 1.6 cm (52 vs 50 frames > 1 cm); Running veil 1.4 -> 1.2 cm.
- Skirt lining through the skirt (`scripts/lining_gate.py`, new: the lining is kept while the skirt is cut): largest outward
  distance equal in every clip (installed max Walking 18.7 mm at the hem rim); lining vertices > 0.5 mm out, worst frame,
  4 -> 6 in most clips (8 -> 12 Running), frames equal except Death 17 -> 20.
- Jitter vs the creature's `ref_half.glb`: 2 fails both (Death shoulder skin 45.2 -> 45.1 mm/f2, the installed model's own).
- Detached parts: 16 components and the same 2 (the legs, by design), same worst distances. Flat shading 0.00. Winding 0.
  Bone lengths 14 checked, 0 stretching. Texture quality: unchanged (body stretch p90 1.09, head 1.35).
- **UV escape** (`scripts/uv_escape.py`, the Mummy's check): 0 faces leave the source charts (d45 without the chart guard: 28).
- See-through (`scripts/see_through.sh`, PeasantF3's `see_through_gate.py`, every clip, 16 views; hole max px, level / 20 deg):
  head 48/29 -> 42/29, torso 749/123 -> 728/119, collar 565/6 -> 537/5, sleeve L 1592/25 -> 1608/25, sleeve R 28/22 -> 29/22,
  boots 0 both; the large ones are the installed construction (Death 30-39 seen from the feet at ground level, up the open skirt
  into F1's hollow dress), same frames and views.
- LODs (`scripts/lod_check.py`, every frame of every clip; `work/lod_check_{installed,g50}.json`), built by `scripts/build_lods.py`
  (tool defaults 0.5/0.18/0.06, 4 influences; soles, crown and corpse contact protected, each point snapped to the imported vertex):
  height 1.788 m at every LOD (installed LOD3 1.777); every clip's lowest point at LOD1-2 equal to LOD0 (installed LOD3 floated
  +0.24 cm standing, +0.77 walking); LOD3 Death -2.1 cm (installed -1.8), Dead -0.24 (installed 0); stretched faces 16/16/17
  (installed 16/16/16; LOD0 30 both: the uv-sliver rows of the head).

## Review
Viewer (installed and reduced, both tiers, all 11 clips; `run_creature_review.py check`: 44 switches, 0 failed, no console errors):
http://127.0.0.1:8912/level_generation/creatures/mm9_peasantf3_reduce_claude/review/viewer/
Sheets read: `review/sheet_face_g50.png` (front close-up, 3/4, true profile, low 3/4, party; both tiers), `review/sheet_face_diff_g50.png`,
`review/sheet_body_g50_{a,b}.png` (Standing front/3-4/back, Walking, Talk, Death), `review/close_g50_{a,b}_hands.png` (L/R hand
outside, R hand front), `review/close_g50_{a,b}_1.png` (arms, skirt front/back, Running skirt), `review/close_g50_{a,b}_2.png` (feet,
Talk arms, veil from behind, Hit, hood top), `review/crop_neck_f50_{a,b}.png` (necklace at full size), `review/ladder_sheet_g.png`.
Look at: the fingertips in close-up (hands at 0.6: very slightly more angular tips), the necklace on the bodice (same paint, the
shading of the cut chest faces differs a little), the skirt hem in Running.

## Build (project folder)
```sh
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"; G=../claude_shared/gltf_venv/bin/python
REA_GLB=level_generation/creatures/mm9_peasantf3_reduce_claude/before/mm9_peasantf3.glb REA_NODE=PeasantF3 $BL -P scripts/import_source.py
$BL -P scripts/dump_mesh.py; $G scripts/glb_parts.py; $G scripts/tex_extract.py
SMALL=80 HW=0.025 SLEEVE=0.15 $G scripts/make_sets_pf3.py g
MP_CHART=1 MP_W5=4 MP_SEAM_GROUPS=1 SETS=g MP_GROUPS=1:0.6,2:0.7,3:0.7,4:0.7,5:0.45,7:0.85 scripts/run_mp.sh g 0.5,0.45
scripts/build_mp.sh mp_g_r50 export/mm9_peasantf3.glb    # swap_mp -> build_lods (protected, snapped) -> shrink_shadow_lods -> carry_variants -> fix_winding
$G scripts/uv_escape.py before/mm9_peasantf3.glb export/mm9_peasantf3.glb
scripts/gates.sh export/mm9_peasantf3.glb g50; $G scripts/lining_gate.py export/mm9_peasantf3.glb review/gates_g50/lining.json
REA_NODE=PeasantF3 $BL -P scripts/lod_check.py -- $PWD/export/mm9_peasantf3.glb g50; scripts/see_through.sh export/mm9_peasantf3.glb g50
$G scripts/viewer_tiers.py export/mm9_peasantf3.glb red   # ramps baked for three.js; installed: viewer_tiers.py before/... inst
$G scripts/make_viewer_manifest.py <rev> inst_a=..=work/viewer_inst_th_a.glb red_a=..=work/viewer_red_th_a.glb inst_b=.. red_b=..
scripts/shots.sh; scripts/close_shots.sh; $G scripts/shot_sheets.py g50; $G scripts/face_diff_sheet.py g50
```
Install (orchestrator, on the OK): `check_winding.py export/mm9_peasantf3.glb` (0), `tools/install_model.py export/mm9_peasantf3.glb
--world mm9`, the `mm9_actor_models_build_every_binding` regression, and add to `../mm9_peasantf3_claude/README.md`: "LOD0 reduced
post-install on <date> by `mm9_peasantf3_reduce_claude`; a rebuild from this project must re-run that reduction". Rollback:
`before/mm9_peasantf3.glb`.

## Not checked
In game (not installed; binding regression and floor audit run after install); motion at normal speed by eye (frames, gates and
viewer stills only); LOD1-3 and shadow meshes by eye (numbers only); the eye/mouth close-ups at the user's zoom (the face triangles
are the installed ones, and the five-view face diff is black).
