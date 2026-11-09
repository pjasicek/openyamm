# Sven Svenssen (`mm9_sven.glb`) reduction: kept (no useful gain), 2026-11-05

Batch: [REDUCTION_AGENT_TOWNSFOLK.md](../../../devdocs/mm9_rework/overnight/REDUCTION_AGENT_TOWNSFOLK.md) and
[REDUCTION_BRIEF_20261104.md](../../../devdocs/mm9_rework/overnight/REDUCTION_BRIEF_20261104.md) (relaxed keep set, face exact;
uniques reduced on the user's "do all", 2026-11-05), ledger row 75 of [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md). Lease
`mm9reduce:sven` (owner sven-reduce-20261105, released at the end); the creature's own `mm9:sven` lease was free. Source: the
installed `assets_source/worlds/mm9/models/mm9_sven.glb` (sha256 3e303710a1f4, = `../mm9_sven_claude/export/mm9_sven.glb`), copied
to `before/`. `../mm9_sven_claude/` was only read. No Meshy, no credits, no linings added (the user's open decision on see-through
gaps). **Nothing installed; the installed model stays as it is.** Scripts are copies of `../mm9_tryggva_reduce_claude/` (run in
the same session; Tryggva has the same LOD0 count by coincidence but another body, see its README).

## Parts and protected share (measured first)
`scripts/glb_parts.py` + `scripts/cfg.py`: body 1 tunic/vest 813, 2 bare arms + bracers 563, 3 belt 133, 5 trousers 546, 6 boots
836, 9 small (necklace plaques, brooches, boot pieces) 353; head set 20 face shell (face, painted beard, neck) 1,807, 21 hair shell
1,443, 23 side braids 150, 22 small (eyes, lips) 361, 0 MPFB hands 1,400. Set builder `scripts/make_sets_sven.py`. Set b (face
shell, eyes, lips, small pieces whole; ears = skin-coloured hair-shell faces in the ear box + 1 cm (322), hairline 180, collar 72,
bracer ends 92, soles 84, openings 3 cm): **42.5 % kept**, -15 % needs 26 % of the free part, so ladders ran.

## Ladders (pose-aware `scripts/mpqem.py`: chart guard + the audit's chart test, W5 4, seam slides on the hands)
Limits for 1.777 m: p99 <= 5.33 mm, max <= 26.66 mm, IoU >= .98, SSIM >= .93.

| ladder | set | groups | step | LOD0 | p99 / max mm | result |
|---|---|---|---|---:|---|---|
| a | b | hands .6, forearm .5, the rest .75 | r75 | 7,059 (-16.0 %) | 4.17 / 19.9 | pass |
| a | b | | r65 / r55 | 7,005 / 6,951 | 4.61 / 29.4, 5.21 / 36.2 (Death:24) | fail |
| b | c = b + shoulder skin (481), fingertips (389), hand-vs-hand contact 1.5 cm, arm contact 3 cm; 52.8 % | hands .6, hair/boots/trousers .65 | r70 / r60 | 7,129 (-15.2 %) / 7,089 | 5.51 / 26.5, 5.87 / 36.2 | fail |
| c | d = c + see-through probe keeps (271); 55.1 % | hands .6, the rest .75 | r75 | 7,417 (-11.8 %) | 4.55 / 21.2 | pass, below the bar |

a75 (`export/mm9_sven_a75.glb`, **rejected, not for install**): UV audit LOD0 0 escaping (`review/uv_audit_a75.json`), every kept
face exact, clips/materials/images byte-identical. Gates installed -> a75 (`review/gates_{before,a75}/`):
- **jitter: 0 -> 1 fail** (AttackMelee R shoulder skin 0.2 -> 2.19 mm/f2 over MM9; the shoulder-skin sample loses vertices).
- arm/hand: Applause L hand 0.9 -> 2.8 cm (1 frame over 1 cm; L pinky behind a coarse R-pinky face, `scripts/probe_depth.py`).
- see-through (step 9, 16 views, every clip): zone maxima 20,988 -> **21,298** (+1.5 %; torso Death +70, Dead +30, Fidget +25,
  sleeves +5..+21; `review/see_through_compare_a75.txt`).
- sleeve/bracer poke 0, detached 0, winding 0, bones 0 stretching, flat 0.00, collapse face-frames lower.
- Sheets read: `review/sheet_face_a75.png`, `sheet_face_diff_a75.png` (face skin black; only hair-shell shading differs),
  `review/close_a75_1.png` (belt front/back, necklace, both bracers: no visible change).

Keeping what those three gates need (ladders b and c) leaves -15 % at 33 % of the free part; the ratios that pass the error limits
give -11.8 %, the deeper ones fail p99. No step saves ~15 % with every gate no worse: **kept (no useful gain)** (stop rule; three
ladders, the cap).

## Review
Reference viewer (installed vs the rejected a75): http://127.0.0.1:8912/level_generation/creatures/mm9_sven_reduce_claude/review/viewer/

## Not checked
c75 was not built or gated (below the bar); no LOD check or Blender shots (no candidate kept); motion at speed.
