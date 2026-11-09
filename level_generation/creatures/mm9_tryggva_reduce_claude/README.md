# Tryggva Ravenlocks (`mm9_tryggva.glb`) reduction: kept (no useful gain), 2026-11-05

Batch: [REDUCTION_AGENT_TOWNSFOLK.md](../../../devdocs/mm9_rework/overnight/REDUCTION_AGENT_TOWNSFOLK.md) and
[REDUCTION_BRIEF_20261104.md](../../../devdocs/mm9_rework/overnight/REDUCTION_BRIEF_20261104.md) (relaxed keep set, face exact;
uniques reduced on the user's "do all", 2026-11-05), ledger row 74 of [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md). Lease
`mm9reduce:tryggva` (owner tryggva-reduce-20261105, released at the end); the creature's own `mm9:tryggva` lease was free. Source:
the installed `assets_source/worlds/mm9/models/mm9_tryggva.glb` (sha256 b05c4f506cf4, = `../mm9_tryggva_claude/export/mm9_try.glb`),
copied to `before/`. `../mm9_tryggva_claude/` was only read. No Meshy, no credits, no linings added (the user's open decision on
see-through gaps). **Nothing installed; the installed model stays as it is.**

## Family check
Tryggva and Sven Svenssen (`mm9_sven.glb`, row 75) both have 8,405 LOD0 triangles by coincidence: they are separate Meshy Smart
Topology bodies (Tryggva body 2,270 + head set 6,135; Sven 3,244 + 5,161; different pieces, vertex counts and fits). Sven is
reduced on his own in `../mm9_sven_reduce_claude/`. Bjarni (`mm9_bjarni.glb`, row 78: 4,569 + 3,520) is a third separate body;
not part of this job (row 78 untouched).

## Parts and protected share (measured first)
`scripts/probe_pieces.py`, `scripts/glb_parts.py` + `scripts/cfg.py` (pieces welded by position): body 1 tunic + sleeves 931,
5 trousers + boots (one piece) 821, 7 shoulder fur 225, 4 collar 140, 3 belt 127, 9 buckle 26; head set 20 face shell 1,533,
21 hair shell 2,267 (with the ears and the fur lapels Meshy fused into it), 23 front braids 772, 22 small pieces (mouth, braid
ends) 164, 0 MPFB hands 1,399. Set builder `scripts/make_sets_try.py`. Set b (face shell + small whole, ears = skin-coloured
hair-shell faces in `fix_ear_try.py`'s box + 1 cm (160), hairline 715, collar 157, cuffs 63, soles 117, buckle, openings 3 cm):
**36.9 % kept**, -15 % needs 24 % of the free part, so ladders ran.

## Ladders (pose-aware `scripts/mpqem.py`, PeasantM1 copy: chart guard + the audit's chart test, W5 4, seam slides on the hands)
Limits for 1.798 m: p99 <= 5.39 mm, max <= 26.97 mm, IoU >= .98, SSIM >= .93.

| ladder | set | groups | step | LOD0 | p99 / max mm | result |
|---|---|---|---|---:|---|---|
| a | b | hands .6, forearm .5, hair/braids/legs/belt/fur/collar .75 | r75 / r65 / r55 | 6,917 / 6,839 / 6,763 | 3.94 / 21.3, 4.51 / 21.3, 5.35 / 22.7 | pass |
| b | d = b + belt + 2 cm, collar piece, hand-vs-hand contact 1.5 cm (283), forearm whole | hands .6, hair/braids .7, legs/fur .75 | r85 / r75 / r65 | 7,039 / 6,975 / 6,909 | 4.01 / 21.3, 4.32 / 21.3, 4.98 / 22.1 | pass |
| c | e = d + fingertips (distal phalanges 390), arm contact 3 cm, trousers under the tunic 4 cm, see-through probe keeps (499); 54.1 % kept | hands .6, hair/braids .65, legs/fur .75 | r65 / r55 / r45 | 7,263 (-13.6 %) every step | 6.30 / 58.4 (Death:24) | **fail** |

Built and gated: a55 (6,763), a65, b65 (6,909), b75 (6,975) in `export/` (**rejected, not for install**). UV audit LOD0: 0
escaping faces in every one (`review/uv_audit_*.json`); every kept face present exactly (`scripts/exact_parts.py`); clips, skin,
materials, images byte-identical.

Gates, installed -> a55 -> b65 (`review/gates_*`, `scripts/gate_summary.py`):
- arm/hand (`--outer-only --exact`): Applause R hand 2.1 -> 4.0 -> **4.0 cm** (the R ring finger behind a coarse L-thumb face, hand vs
  hand: `scripts/probe_depth.py`); Fidget R forearm 2.9 -> 3.6 -> **3.6 cm** (into the fur lapels of the hair shell). Worse.
- detached: 0 -> **1** (a 16-triangle Neck piece split off, 2 cm in Agree) in a55 and b65. Worse.
- see-through (`scripts/see_through.sh`, step 9, 16 views, every clip): zone maxima 22,442 -> 23,040 -> **22,720** (+1.2 %); torso,
  sleeve R and head (hair) up in most clips (`review/see_through_compare_b.txt`, `review/see_through_compare_a55.txt`). Worse.
- jitter 0 fails, sleeve poke 0, winding 0, bones 0 stretching, flat 0.00, texture quality equal; collapse face-frames lower.
- Sheets read (`review/sheet_face_{a55,b65}.png`, `sheet_face_diff_{a55,b65}.png`: face skin black; `sheet_body_a55_a.png`,
  `close_a55_{1,2,3,hands}.png`, `close_b65_{1,3,hands}.png`, `close_b_tunic_3way.png`): a55 smeared the belt (dark wedges on its
  top edge and the buckle); b65/b75 fixed the belt but show a dark wedge between the legs under the tunic's front point.

Ladder c added a keep for every one of those regressions; the hands, braids and tunic then stall on the guards (tunic 585 -> 381
free at every ratio), the hair collapses grow to 20 mm rms, and the result is -13.6 % with the error limits failed. No step
saves ~15 % with every gate no worse: **kept (no useful gain)** (stop rule; three ladders, the cap).

## Review
Reference viewer (installed vs the rejected b65 / b75): http://127.0.0.1:8912/level_generation/creatures/mm9_tryggva_reduce_claude/review/viewer/
(`run_creature_review.py check`: 28 switches, 0 failed, no console errors, with a55). Viewer shots must be taken with the same
manifest for installed and candidate: the viewer frames differently after a manifest change (first b65 face diff 41 %, retaken 6 %).

## Not checked
LOD check, Blender sleeve/poke shots and a full-density see-through (no candidate kept); b75's see-through was dropped once c was
needed; motion at speed.
