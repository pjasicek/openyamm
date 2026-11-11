# MM9 Honk female (`mm9_honkf`, Honk / Elder Honk) reduction: fix pass n r70 ready for review (2026-11-04)

## Fix pass (2026-11-04): chart guard, UV audit 0
The first candidate (h r70 below, 7,901) was installed and **rolled back** by the orchestrator: `claude_shared/reduction_uv_audit.py`
found 83 LOD0 faces of `HonkFHead` whose UVs left the painted charts (the goose's eye gone, scales smeared beside the beak;
`review/uv_audit/closeups.png`), almost all from seam slides on the goose hat. Changes (lease claimed again as
honkf-reduce-fix-20261104, released at the end; no credits):
- `scripts/mpqem.py` has the Imp/Mummy **chart guard** (`MP_CHART=1`): a collapse is refused when any of 91 samples of a new face's
  UV triangle falls off the installed charts (rasterised at 2048, dilated 2 texels).
- The same keep set with the chart guard (k r70) gave 8,003 (-15.1 %) and LOD0 audit 0, but the goose's beak came out straighter,
  pointier and darker in every close-up (`review/hat_k70_a.png`). **Set m** also keeps the gold goose piece (head, neck, beak, eye;
  225 faces, `scripts/goose_keep.py`). Hands 0.7 / braids 0.65 to win the count back (m r70, 8,045) were tried and dropped: arm/hand
  regressed (Fidget L forearm 0.9 -> 2.0 cm, CowerStart L 3.2 -> 3.9, PropFidget2 R frames 15 -> 26).
- **Picked: n r70 = set m, hands 0.75, braids 0.7 (h's ratios), chart guard: LOD0 8,141 (-13.7 %)**, LOD1-3 4,069 / 1,464 / 485,
  `export/mm9_honkf.glb` sha256 ef804653a269. That is a little under the brief's ~15 %; the alternative at -15.1 % is k r70 with
  the changed beak (rebuild: `SETS=h MP_CHART=1 ...`, `work/mp_k_r70.npz`).
- Ladder n r70: p99 2.93 / max 17.6 mm (limits 5.73 / 28.6), IoU .997, SSIM .995, open edges 935 as installed.
- **UV audit** (`review/uv_audit_n70/audit.txt`): LOD0 escaping **0** in both primitives (was 83). LOD1-3 escapes come from
  `tools/build_actor_lods.py` (Blender decimate) and are near the installed file's own (body 72/66/36 vs installed 60/61/46,
  head set 187/210/121 vs installed 165/220/155).
- Gates installed -> n r70 (`review/gates_compare_n70.txt`): collapse face-frames 30,385 -> 29,601 (worst regions lower except
  leg_L 0 -> 1 in Death2/Dead2); robe identical; hair equal or fewer; arm/hand as h r70 (Death R 0.0 -> 0.2 cm, Fidget2 R forearm
  0.0 -> 0.4 cm, 0 frames over 1 cm; the rest equal or better); jitter 0 -> 0; forearm poke, winding, bone lengths, same_clips
  identical; flat shading 0.01 / 0.00. Sleeve gate: identical except Running L see-through 6 -> 5 px (worst 29 px both).
  LODs (`work/lod_check_n70.json`): height 1.9164 m and LOD0's lowest point at every LOD in every clip; stretched faces
  1 / 0 / 1 / 0 (LOD2 1, installed 0).
- Headdress close-ups, installed | reduced, both tiers (`review/hat_n70_a.png`, `review/hat_n70_b.png`: goose head and eye from
  both sides, scales below the beak, 3/4 above, band from the side, back) and zoomed crops (`work/zoom_n70_a_h2.png`,
  `work/zoom_n70_a_h4.png`, `work/zoom_n70_b_h3.png`, `work/zoom_n70_b_h0.png`), all read: eye and beak as installed, scales
  intact (scale lines slightly redrawn along the dome's seams), band knotwork as installed with a slightly darker lower gold lip.
- Viewer revision `r7-n70-chartguard` (same URL as below). Rebuild: `scripts/reproduce.sh` (updated).
The sections below describe the first (rolled-back) candidate h r70 and stay as its record.

Batch: [REDUCTION_BRIEF_20261104.md](../../../devdocs/mm9_rework/overnight/REDUCTION_BRIEF_20261104.md) (prio-1 monster, relaxed
keep set), ledger row 65 of [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md). Lease `mm9reduce:honkf` (owner honkf-reduce-20261104);
the creature's own `mm9:honkfemale` lease was free. Source: the installed `assets_source/worlds/mm9/models/mm9_honkf.glb` (sha256
9fd961fe94ef, identical to `../mm9_honkfemale_claude/v2/export/mm9_honkf.glb`), copied to `before/` (the rollback source). No Meshy,
no credits, no repaint. **Not installed.** `../mm9_honkfemale_claude/` was only read. The male Honk's hats are separate GLBs and
not in scope; the female's goose hat is part of her head set and was reduced here.

| | LOD0 | body set `HonkF_A` (robe, linings, boots, medallion, buckle) | head + hands set `HonkFHead` | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|---:|---:|
| installed | 9,431 | 2,621 | 6,810 | 4,714 | 1,695 | 564 |
| **h r70 (`export/mm9_honkf.glb`, sha256 4e6181fa39b2)** | **7,901 (-16.2 %)** | 2,279 | 5,622 | 3,949 | 1,421 | 471 |

Every vertex of the candidate is an installed vertex (positions, normals, UVs, joints, weights are the installed bytes; only index
buffers changed). Clips (22), skin, nodes, materials, region ramps, `KHR_materials_variants` (carried to every LOD and shadow
primitive) and all 8 images are byte-identical (`same_clips.py`). The face is the installed triangles: the whole head shell (face,
ears, neck, the hidden neck skirt and the hair painted on it) and the eyes are kept, and the face diff sheets are black on the face
in both tiers and every view.

## Measured first: protected share
The mesh is light already (the robe is 1,961 faces with its linings); most triangles are in the head + hands set: head shell 1,486,
hands with forearm skin 1,686, goose hat 1,860 (dome and goose 1,107, flat brim band layers 753), braids and side locks 1,026, veil
563, eyes 189. Exact in the base set (33.5 %): head shell and eyes, robe/sleeve linings with hem rim and top cap (517 zero-UV faces)
and the outer faces they line (242), soles, the hand-graft junction (hand-piece faces within 3.5 cm of each wrist joint), the
hairline (braid/veil faces within 8 mm of the head shell), the seam ring round the head shell, pieces of up to 80 faces (buckle,
goose eyes, eyes). The final set h keeps 42.9 % (4,048 faces): the base set plus
- **contact**: faces under a hand within 3 cm in any frame of any clip (15 Hz; `honk_contact.py`, 750, mostly face/eyes already kept);
- **paint edges**: robe faces whose base colour or region mask spans a boundary inside the face (383; `paint_edges.py`): the
  neckline's skin ellipse grew and a pale patch spread on the Elder's blue collar in build a60 without them;
- **neck zone**: robe faces within 18 cm of the neck joint (274; `neck_zone.py`): a pale fleck at the Elder's collar edge grew in f65;
- **shoulder skin** (447, the jitter gate's set: a60's Death L shoulder skin rose 1.98 -> 2.15 mm/f2, over the 2.0 limit) and the
  Death R hand contacts at 48 fps (`contact_lock.py` on the a60 and f65 gates).
Groups: hands 0.75 (every finger kept), braids + side locks 0.7, veil 0.7, hat dome + goose 0.5, brim band 0.85, boots 0.6,
medallion disc 0.5, forearm skin 0.6 (nothing collapsible: every vertex is on a seam or a kept face); robe takes the ladder ratio.
Seam slides (`MP_SEAM_GROUPS`) on hands, braids, hat and band.

## Route: pose-aware half-edge collapse (`scripts/mpqem.py`, the Lesser Demon's copy with seam slides)
Scored over every clip at 10 Hz plus a position+UV rest quadric; only removes vertices; texture guard on the body base colour +
region mask (both tiers are ramps on one image) and on the head set's tier A and B base colours, refusing at > 70 any sample /
> 30 mean (a60 used 100 / 45 and smeared the band's lower edge).

## Ladders (height 1.909 m: p99 <= 5.73 mm, max <= 28.6 mm, IoU >= .98, SSIM >= .93; `review/ladder_sheet_<label>.png`)
| set | change | step | LOD0 | p99 / max mm (worst) | IoU / SSIM | |
|---|---|---|---:|---|---|---|
| a | base keep set + contact, guard 100/45 | r60 / r50 | 7,413 / 7,295 | 4.77/17.9 (Death2), 7.07/39.4 | .996/.993 | pass (built: neckline and collar paint moved, band edge smear, jitter Death L fail, arm Death R 0 -> 2.0 cm) / fail |
| c, e | robe wall lining dropped and re-emitted from the cut outer wall (12 mm twins) | r60 / r65 | 7,205 / 7,747 | 4.22 | | e: 4 new open edges where re-emitted lining met the top cap strip; fixing it kept 140 of 194 lined faces, so the rebuild saved ~40 faces and was dropped |
| d | a + paint edges + band group, guard 70/30 | r60 | 7,459 | | | mpqem only |
| f | d + shoulder skin + Death R contacts, hands 0.75 | r70 / **r65** | 7,849 / 7,817 | 3.58/15.1, 4.22/18.7 | .995/.994 | pass (built: Elder collar fleck larger) |
| g | f + neck zone | r75 / r70 | 7,925 / 7,901 | 3.18/16.7, 3.69/17.6 | .996/.994 | pass |
| **h** | g + f65's Death R / Fidget2 R hand contacts | **r70** | **7,901** | **3.69 / 17.6 (Cower)** | **.996 / .994** | **PASS, picked** |
Robe steps below r70 add one 14 mm collapse (the robe group runs out of cheap collapses at about 0.66).

## Gates, installed -> h r70 (the Honk female's own scripts, `scripts/gates.sh`; `review/gates_before/`, `review/gates_h70/`, `review/gates_compare_h70.txt`)
- Collapse face-frames 30,385 -> 29,477, lower or equal in every clip; worst-frame region counts lower almost everywhere (Death
  leg_L 13 -> 5, leg_R 15 -> 7, AttackRanged/Cast waist 28 -> 24); up by one face: leg_L 0 -> 1 in Death2 and Dead2.
- Robe gate (boots through the robe, 48 fps): identical in every clip. Hair gate: equal or fewer crossing edges in every clip
  (Death2 64 -> 61, Dead2 47 -> 42; frames equal or lower).
- Arm/hand (`--outer-only --exact`): Hit L forearm 1.3 -> 1.2, CowerStart R 0.7 -> 0.6, Cower R frames over 1 cm 39 -> 37,
  PropFidget2 R 15 -> 13; **Death R hand 0.0 -> 0.2 cm** (0 frames over 1 cm) and **Fidget2 R forearm 0.0 -> 0.4 cm** (not
  chased further); finger-stretch maxima unchanged, p99 higher (fewer finger vertices: Fidget R 1.68 -> 2.01, Dead2 R 1.57 -> 1.91).
- Jitter (against `v2/work/mm9_honkf_armout.glb`): 0 fails before and after. Forearm poke: identical. Bone lengths, winding (0),
  same_clips: identical. Flat shading 0.02 -> 0.01 (body), 0.00 (head). Detached: the same two boots (by design) and shallow pieces
  with the same distances. Texture quality: body stretch p90 1.17 -> 1.18, head unchanged (fragments 0.9 -> 2.1 % of surface).
- Sleeve gate (24 fps, front / above34 / below / q34): forearm poke 0 everywhere both; see-through identical in every clip except
  Running L 6 -> 5 px; worst 29 px (Death R) both.
- LODs (`lod_check.py`, every frame of every clip; `work/lod_check_{installed,h70b}.json`): height 1.9164 m at every LOD (installed
  LOD3 1.9046: the goose's top lost 1.2 cm); every LOD's lowest point equals LOD0's in every clip (Standing 0, Walking -0.28, Death
  -2.43, Death2 -1.96, Dead/Dead2 0 cm; installed LOD3 stood 0.47 cm up in Standing). The first build's LOD3 sank to -3.65 cm in
  Death: `build_lods.py` now also protects the floor contact every 0.1 s of the falls. Faces stretched over 20x: LOD0 1 (Cower, as
  installed), LOD1 0, **LOD2 1** (installed 0), LOD3 0.

## Review
Viewer (installed and reduced, both tiers, all 22 clips; `run_creature_review.py check`: 88 switches, 0 failed, no console errors):
http://127.0.0.1:8912/level_generation/creatures/mm9_honkf_reduce_claude/review/viewer/ (models `inst_a/b`, `red_a/b`; ramps baked
into the viewer copies by `scripts/viewer_tiers.py`, as the creature's own viewer does).
Sheets read: `review/sheet_face_diff_h70.png` (front close-up, 3/4, profile, low 3/4, party; installed | reduced | diff x4; both
tiers), `review/sheet_body_h70_a.png` (Standing front/3-4/back, Walking, AttackMelee, Death), `review/close_h70_{a,b}_{1,2}.png`
(both hands, AttackMelee hand, goose hat 3/4 above and from behind, veil from behind, braids and medallion, left cuff from below,
hem in Walking, Death), full-size crops `work/crop_h70_b_f0.png`, `work/crop_h70_b_f2.png` (and the a60/f65 crops that found the
neckline and collar faults), `review/sets_b.png`, `review/paint_head.png`, `review/ladder_sheet_{a,f,g,h}.png`. Written, not read:
`review/sheet_face_h70.png`, `review/sheet_body_h70_b.png`.
Look at: the goose hat (dome at 0.5: the scale pattern and the wing relief shade slightly differently up close), the brim band's
lower edge from the side, the hands at 75 %, the braid tips on the chest.

## Build
`scripts/reproduce.sh` (import_source -> dump_mesh -> tex_extract -> make_sets a -> honk_contact / paint_edges / neck_zone ->
make_sets h (with work/lock_death.npy and work/lock_f65.npy from `contact_lock.py`) -> mpqem h 0.7 -> ladder -> build_mp.sh:
swap_mp -> build_lods.py (tools/build_actor_lods.py defaults, protected soles / hat top / beak tip / corpse contact, snapped to the
import) -> the creature's shrink_shadow_lods -> carry_variants -> check_winding). Gates: `scripts/gates_all.sh <glb> <tag>`
(numeric gates, sleeve gate, LOD checks; one Blender at a time; the LOD0 gates ran on the build before the LOD fix, whose
LOD0 is the same: identical triangles), `gate_compare.py <tag>`; viewer: `viewer_tiers.py`,
`make_viewer_manifest.py`, `shots.sh`, `close_shots.sh`, `shot_sheets.py`, `face_diff_sheet.py`, `pair_sheet.py`.

Install (on the user's OK only): `check_winding.py export/mm9_honkf.glb` (0), `python3 tools/install_model.py
level_generation/creatures/mm9_honkf_reduce_claude/export/mm9_honkf.glb --world mm9`, the `mm9_actor_models_build_every_binding`
regression, `floor_audit.py --world mm9 --match 'MM9 Honk Female*'`, the ledger row, and the line in
`../mm9_honkfemale_claude/README.md`: "LOD0 reduced post-install on <date> by `mm9_honkf_reduce_claude`; a rebuild from this
project must re-run that reduction". Rollback: `before/mm9_honkf.glb`.

## Not checked
In game (not installed; the binding regression and floor audit read the installed file); motion at normal speed (frames, gates
and viewer stills only); LOD1-3 and shadow meshes by eye (numbers only); the collapse gate's exposed faces by eye; the two small
arm/hand increases above (Death R 0.2 cm, Fidget2 R forearm 0.4 cm) by eye.

## MM9 sockets (2026-11-10)

The installed model carries MM9's attach points as `Socket_<name>` nodes for held items (scene `held_items`, MM9's AttachProp), added after this project's install by [`mm9_held_items_claude/scripts/add_sockets.py`](../../props/mm9_held_items_claude/scripts/add_sockets.py) (`Socket_pamphlet`). A rebuild installed from here drops them: run that script again and install its export (`tools/install_model.py --world mm9`).
