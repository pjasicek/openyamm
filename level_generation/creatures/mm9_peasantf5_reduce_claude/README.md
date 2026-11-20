# MM9 PeasantF5 (`mm9_peasantf5`, the townswoman in a coif) reduction: candidate d r55 ready for review (2026-11-05)

Batch: [REDUCTION_BRIEF_20261104.md](../../../devdocs/mm9_rework/overnight/REDUCTION_BRIEF_20261104.md) and
[REDUCTION_AGENT_TOWNSFOLK.md](../../../devdocs/mm9_rework/overnight/REDUCTION_AGENT_TOWNSFOLK.md) (prio-2 townsfolk, face exact),
ledger row 30 of [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md). Lease `mm9reduce:peasantf5` (owner peasantf5-reduce-20261104); the
creature's own `mm9:peasantf5` lease was free. Source: the installed `assets_source/worlds/mm9/models/mm9_peasantf5.glb` (sha256
cc15d105b676, identical to `../mm9_peasantf5_claude/export/`), copied to `before/` (the rollback source). No Meshy, no credits, no
repaint. **Not installed.** `../mm9_peasantf5_claude/` was only read.

**Relation to PeasantF6** (orchestrator, 2026-11-04): PeasantF6 is this body (`../mm9_peasantf6_claude/README.md`, "variant route on
PeasantF5": F5's final geometry, rig, weights and clips; coif and brooches removed, new hair, braid and elf ears). The two GLBs are
separate files with different vertex sets (F6 dropped slivers and added collar linings), so the cut cannot be shared byte for byte;
instead this reduction uses F6's keep rules (`../mm9_peasantf6_reduce_claude/`, set f): hand stub and the forearm within 2 cm of it,
skirt hem (10 cm) and waist (3 cm) bands, cloth the arms touch in any clip (`scripts/arm_contact.py`, 1.5 cm), group ratios hands 0.6 /
arms 0.45 / hair-coif 0.7 / shoes 0.7 / calves 0.85 / bracelets 0.6, LOD corpse contact LIE 3 cm, and F6's `build_lods.py`. One
difference: F5's skirt is kept exact (below).

| | LOD0 | head (face, neck, hair under the coif, eyes) | coif | dress | skirt + apron | lining | legs | arms | hands | bracelets | brooches + buckle | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| installed | 12,992 | 4,372 | 568 | 1,998 | 942 | 980 | 640 | 898 | 1,464 | 768 | 362 | 6,386 | 2,297 | 763 |
| **d r55 (`export/mm9_peasantf5.glb`, sha256 a7801be91338)** | **10,778 (-17.0 %)** | 4,372 | 416 | 1,208 | 942 | 980 | 526 | 586 | 926 | 460 | 362 | 5,280 | 1,899 | 820 |

Every vertex of the candidate is an installed vertex (position, UV, normal, weights matched exactly); only index buffers changed.
Clips (11), skin, nodes, materials, region ramps/mask, `KHR_materials_variants`, all 8 images: byte-identical (`same_clips.py`). Head
primitive: every installed triangle present (4,372/4,372), so the face renders pixel-identical in both tiers
(`review/sheet_face_diff_d55.png`: face black in all five views of pf5_a and pf5_b; only the coif rim shading, the shoulders and the
pinafore straps below the collar differ).

## Measured first: protected share
Part labels from the creature's last pre-GLB mesh (`../mm9_peasantf5_claude/work/uv_tex2.npz`, 12,992 faces = LOD0, matched by rest
centroid to 1e-8 m; `scripts/glb_parts.py`). Head + brooches + buckle = 4,734 (36 %); with the coif edge, collar, hand stub and
wrist junction, soles, skirt bands, arm contact and the lining the final set d keeps 6,989 (54 %).

Keep set (`scripts/make_sets_pf5.py`, set d = `BRACE=cut LPROBE=b55:0.03 STUB=0.02 HEM=0.1 WAIST=0.03 ARMC=1`, MP_GROUPS skirt 1.0): the
head primitive; coif faces within 8 mm of the head; dress within 1 cm of the head (collar); **the MPFB hand-graft junction** (hand faces
dominated by a forearm joint = the 3.5 cm stub, hand and arm faces within 1.2 cm of a bracelet vertex, arm faces within 2 cm of a stub
vertex); arm faces within 1 cm of the dress (arm leaving the puffed sleeve); soles; brooches and buckle; the skirt lining; the skirt
(see ladders). Groups: hands + fingers 0.6 (seam slides; every finger kept), arm skin 0.45, coif 0.7, shoes 0.7, hidden calves 0.85,
bracelets 0.6, dress at the ladder ratio.

## Route: pose-aware half-edge collapse (`scripts/mpqem.py`, PeasantF3's copy)
Texture guard over each tier's baked body colour (tone x region ramps), each tier's head image and the region mask
(`scripts/tex_extract.py`; refuse > 100 any sample / > 45 mean), the Mummy's chart guard (`MP_CHART=1`, 12 samples), texture weight 4
(`MP_W5`), seam slides on the hands. Scored over 291 poses (every clip at 10 Hz) plus a position+UV rest quadric. Each group is cut on
its own, so a group kept whole leaves the other groups' cuts unchanged.

## Ladders (limits for 1.811 m: p99 <= 5.43 mm, max <= 27.2 mm, IoU >= .98, SSIM >= .93; `review/ladder_sheet_<label>.png`)
| ladder | set / change | step | LOD0 | p99 / max mm (worst) | result |
|---|---|---|---:|---|---|
| a | a: first set (bracelets, lining kept; skirt 0.7, arms 0.5) | r50 / r45 | 10,624 / 10,548 | 4.44/20.5 (Hit), 7.2/61.8 | pass / fail (dress saturates at 882, a 35 mm collapse); a50 built: lining through the cut skirt Hit 4.5 -> 10.0 mm, Death 5.5 -> 8.1; Cower R forearm 0 -> 1.4 cm into the chest |
| b | a + F6's rules (stub 2 cm, hem/waist bands, arm contact), arms 0.45 | r55 / r50 | 10,870 / 10,784 | 4.05/19.5 (Conv1), 6.66/61.8 | pass / fail; b55 built: Cower fixed, lining Running 2.3 -> 7.4 mm, Death 6.1 (`scripts/lining_probe.py`: 25 lining vertices pushed out) |
| c | b + skirt within 3 cm of those lining vertices | r55 | 10,908 | 4.04/19.5 | pass; c55 built: lining Walking 2.3 -> 7.6, Running 5.7 mm (the cut moved elsewhere on the skirt) |
| **d** | **c with the skirt kept exact (gates kept failing on that part) + bracelets 0.6 as F6** | **r55** | **10,778** | **4.03 / 19.5 (Conv1:45)** | **PASS, picked** (IoU .9975, SSIM .9953) |

## Gates, installed -> d r55 (PeasantF5's own scripts, `scripts/gates.sh`; `review/gates_before/`, `review/gates_d55/`)
- **UV chart audit** (`../claude_shared/reduction_uv_audit.py`, `review/uv_audit_d55.json`): **LOD0 0 escaping faces in both nodes**.
  LODs (Blender decimate): body 171 / 132 / 22 at LOD1-3 (installed 118 / 164 / 70), head 52 / 82 / 22 (installed 53 / 85 / 23).
  `scripts/uv_escape.py`: 1 body face flagged (coif back midline, 4.4 % outside), the same face is in the installed file; 0 new.
- Collapse face-frames lower in every clip (total 30,349 -> 24,027; Conv3 6,294 -> 4,668, Cower 2,890 -> 1,972).
- Robe (legs through skirt): 0 in every clip, both. Skin poke (`skin_poke_gate.py --mirrored`, hand stub inside forearm + bracelet, arm
  top inside the puffed sleeve): 0.0 mm every clip, both (28 stub candidates per side both; L sleeve 17 -> 16, one removed vertex).
- Arm/hand (`--outer-only --exact`, 48 fps): hand 0 frames > 1 cm in every clip, both; forearm maxima equal (Cower L 1.4 cm, the
  installed coif-flap contact; Conv3 0.2); finger stretch maxima equal (2.36 Fidget R). On b55/c55 the gate flagged forearm 5.3-6.0 cm
  in several clips: measurement artifacts (`scripts/arm_hand_probe.py` + `scripts/point_probe.py`: the vertex lies 3.4-5.7 cm on the
  outer side of the skirt in both files, no hit along +x/-x; the gate's 6 cm cap picked a face with the opposite normal), as F6 found;
  d55 shows none.
- Skirt lining (`scripts/lining_gate.py`, 10 fps): largest outward distance equal to the installed in every clip (Talk 2.52 -> 2.40 mm).
- Jitter vs `../mm9_peasantf5_claude/work/ref_half.glb`: 2 fails both (Death shoulder skin 35.9 mm/f2, the installed model's own).
- Detached parts: 21 components, the same 7 detached parts (feet inside the skirt by design, bracelets and buckle); bracelet worst lift
  1.81 / 1.69 -> 1.86 / 1.83 cm (Conv3, a few poses), buckle equal. Flat shading 0.00 / 0.01 both. Winding 0. Bone lengths 14, 0
  stretching. Texture quality unchanged (body stretch p90 1.05 -> 1.06, head 1.17).
- LODs (`scripts/lod_check.py`, every frame of every clip; `work/lod_check_{installed,c55,d55}.log`), built by `scripts/build_lods.py`
  (F6's: tool defaults 0.5/0.18/0.06, 4 influences; soles, crown and corpse contact within LIE 3 cm protected, snapped to the imported
  vertex, coincident points with other weights dropped): height 1.807 m at every LOD (installed LOD3 1.795); every clip's lowest point
  at LOD1-3 equal to LOD0 (installed LOD3 stood 0.8-1.2 cm above the floor in every standing clip, Running +2.3 cm).
- See-through (`scripts/see_through.sh`, every clip, 16 views; `python3 scripts/see_summary.py review/gates_before/see_through.json
  review/gates_d55/see_through.json`; hole max px installed / d55): head 315/315, sleeve R 27/26, boots 0/0, collar 1607/1577,
  sleeve L 2512/2413, torso 1286/1432. The large values are all Death frames 30-39 seen from the feet at ground level (az 0, el 0), up
  the open skirt into the hollow dress, the installed construction: the torso worst case (Death 30) is the same frame and view, and the
  annotated images (`review/gates_{before,d55}/see_through_torso_Death_30_az000_el00.png`) are the same opening; the hole pixels move
  between the torso, sleeve L and collar zones because the zone comes from the nearest (cut) bodice face. Other clips within a few px.

## Review
Viewer (installed and reduced, both tiers, all 11 clips; `run_creature_review.py check`: 44 switches, 0 failed, no console errors):
http://127.0.0.1:8912/level_generation/creatures/mm9_peasantf5_reduce_claude/review/viewer/
Sheets read (d55): `review/sheet_face_d55.png` (front close-up, 3/4, true profile, low 3/4, party; both tiers),
`review/sheet_face_diff_d55.png`, `review/sheet_body_d55_{a,b}.png` (Standing front/3-4/back, Walking, Talk, Death),
`review/close_d55_{a,b}_hands.png` (both wrists and bracelets from outside, R hand front, L forearm, R wrist close),
`review/close_d55_{a,b}_1.png` (arms, skirt front/back, Running skirt, Talk hand and fingers, Talk wrist),
`review/close_d55_{a,b}_2.png` (feet and hem, Talk, shoulders from behind, Hit, coif from behind above); earlier steps:
`review/crop_chest_c55.png` (bodice, brooches and straps at 2x), `review/*_a50*`, `*_b55*`, `*_c55*`, `review/ladder_sheet_{a,b,c,d}.png`.
Look at: the pinafore straps on the shoulders (same paint, slightly different shading of the cut bodice faces), the bracelets (0.6:
the same ring outline at viewer zoom), the coif's outer rim.

## Build (project folder)
```sh
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"; G=../claude_shared/gltf_venv/bin/python
REA_GLB=level_generation/creatures/mm9_peasantf5_reduce_claude/before/mm9_peasantf5.glb REA_NODE=PeasantF5 $BL -P scripts/import_source.py  # from the repo root
$BL -P scripts/dump_mesh.py; $G scripts/glb_parts.py; $G scripts/tex_extract.py; $G scripts/arm_contact.py 0.015 10
# lining probe of b55 (work/lining_probe_b55.npy, kept): scripts/lining_probe.py work/mm9_peasantf5_b55.glb b55
BRACE=cut LPROBE=b55:0.03 STUB=0.02 HEM=0.1 WAIST=0.03 ARMC=1 $G scripts/make_sets_pf5.py d
work/run_d.sh       # mpqem r55 (MP_GROUPS 1:0.6,2:0.7,3:1.0,4:0.7,5:0.45,7:0.85,8:0.6) -> build_mp.sh (LIE=0.03) -> work/mm9_peasantf5_d55.glb
cp work/mm9_peasantf5_d55.glb export/mm9_peasantf5.glb
$G ../claude_shared/reduction_uv_audit.py export/mm9_peasantf5.glb before/mm9_peasantf5.glb --json review/uv_audit_d55.json
scripts/gates.sh export/mm9_peasantf5.glb d55; work/queue_d.sh   # ladder metrics, lod_check, see_through
$G scripts/viewer_tiers.py export/mm9_peasantf5.glb red; $G scripts/make_viewer_manifest.py r4-d55-20261105 inst_b=..=work/viewer_inst_th_b.glb red_b=.. inst_a=.. red_a=..
HEADUP=0,0.07,0.09 scripts/shots.sh; scripts/close_shots.sh; $G scripts/shot_sheets.py d55; $G scripts/face_diff_sheet.py d55
$G scripts/pair_sheet.py review/shots_close inst_a red_a review/close_d55_a_hands.png h0,h1,h2,h3,h4   # and _1 / _2, tier b
```
Install (orchestrator, on the OK): `check_winding.py export/mm9_peasantf5.glb` (0), `tools/install_model.py export/mm9_peasantf5.glb
--world mm9`, the `mm9_actor_models_build_every_binding` regression, and add to `../mm9_peasantf5_claude/README.md`: "LOD0 reduced
post-install on <date> by `mm9_peasantf5_reduce_claude`; a rebuild from this project must re-run that reduction". Rollback:
`before/mm9_peasantf5.glb`. Superseded candidates: `work/mm9_peasantf5_{a50,b55,c55}.glb`.

## Not checked
In game (not installed; binding regression and floor audit run after install); motion at normal speed by eye (gates, frames and viewer
stills only); LOD1-3 and shadow meshes by eye (numbers only); eye/mouth close-ups at the user's zoom (the face triangles are the
installed ones and the five-view face diff is black); see-through was run only on the installed file and d55 (a50/b55/c55 were not).
