# Yrsa the Troll (`mm9_yrsa.glb`) reduction: kept (no useful gain), 2026-11-05

Batch: [REDUCTION_AGENT_TOWNSFOLK.md](../../../devdocs/mm9_rework/overnight/REDUCTION_AGENT_TOWNSFOLK.md) and
[REDUCTION_BRIEF_20261104.md](../../../devdocs/mm9_rework/overnight/REDUCTION_BRIEF_20261104.md) (relaxed keep set, face exact;
uniques reduced on the user's "do all", 2026-11-05), ledger row 68 of [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md). Lease
`mm9reduce:yrsa` (owner yrsa-reduce-20261105, released at the end); the creature's own `mm9:yrsa` lease was free. Source: the
installed `assets_source/worlds/mm9/models/mm9_yrsa.glb` (sha256 5f601016b26f, = `../mm9_yrsa_claude/v2/export/mm9_yrsa.glb`),
copied to `before/`. `../mm9_yrsa_claude/` was only read. No Meshy, no credits. **Nothing exported or installed; the installed model
stays as it is.**

## Protected share (measured first)
Labels (`scripts/glb_parts.py`): every GLB triangle matched 1:1 to the final master `../mm9_yrsa_claude/v2/work/sleeves_v2.blend`
(`hand` / `head` face flags; frame (x, -z, y), floor lift 0.9307 m; max 1.2e-7 m), connected pieces per primitive, the head shell's
faces split by painted colour (`scripts/head_classes.py`) and by visibility in 60 frontal face-ID renders (`scripts/vis_render.py`,
`scripts/vis_decode.py`), the sleeve lining found by its single dark texel and paired with the outer sleeve by twin vertices (same
weights, 1.5-4.5 mm; 302 of 315 lining faces paired). Class render: `review/head_parts_sheet.png`.

| | faces | kept exact | free |
|---|---:|---:|---:|
| face/neck skin with the upper braids (visible skin-coloured head shell) | 1,724 | 1,724 | 0 |
| other head pieces: eyes, mouth, neck ring, white fringe, bead band, earrings, braid ends | 1,014 | 1,014 | 0 |
| hood, white hair, hidden shell under the hood | 872 | 536 (hairline 8 mm) | 336 |
| MPFB hands / forearm extensions + stubs | 1,308 / 370 | 117 (fingertips) / 370 | 1,191 |
| bodice + sleeves (outer) / sleeve lining / rims + inner layer | 697 / 315 / 98 | 206 / 13 / 98 | 491 / 302 re-emitted |
| skirt / boots / belt + chest panel / small pieces | 1,418 / 337 / 287 / 223 | 53 / 28 / 33 / 223 | 1,365 / 309 / 254 / 0 |
| **total** | **8,676** | **4,428 (51.0 %)** | **3,946 + 302 lining** |

Keep set (`scripts/make_sets_yrsa.py a`, `CONTACT=0.03 HW=0.015`): as the brief's relaxed set plus collar 1.2 cm, headwear
clearance 1.5 cm (hood tail and braids on the dress), cuff 3 cm round the hands, fingertips 6 mm, hand contact 3 cm in every clip,
soles. 15 % of LOD0 (1,300) is 33 % of the free part, so a ladder was run.

## Ladder a (pose-aware `scripts/mpqem.py`, Kira's copy; `MP_AUDIT=1 MP_CHART=1 MP_W5=4 MP_SEAM_GROUPS=1`)
Limits for 1.692 m: p99 <= 5.08 mm, max <= 25.4 mm, IoU >= .98, SSIM >= .93. Groups: hands 0.65, hood/hair 0.75, boots 0.7,
belt + chest 0.7, bodice + sleeves + skirt at the ladder ratio; the lining re-emitted from the twins of the cut sleeve.

| step | LOD0 | p99 / max mm (worst) | IoU / SSIM | result |
|---|---:|---|---|---|
| r65 / r55 / r45 | 7,552 (-13.0 %) each | 7.08 / 42.0 (Hit:21, back skirt at the waist) | .9927 / .9876 | fail |

The bodice + skirt group stalls at 1,378 of 1,856 free faces at every ratio: the texture, chart and audit guards refuse every
further collapse (the body was already cut to 0.42 at the build). The belt and chest panel stall at 250 of 254. Hands and hood reach
their targets (1,191 -> 773, 336 -> 252). The worst error is in the stalled group's last collapses (33.7 mm rms on the skirt, 54.6 mm
on the boots), which a cost cap would refuse, so a passing step would be smaller than 7,552.
Guard floor (mpqem only, `work/mp_floor_r30.json`): hands and hood at 0.6, boots and belt at 0.5, body r30, no cost cap: **7,444
(-14.2 %)**, still short of 15 % and already failing the error limits. That meets the stop rule, so this project stops at "kept".
`scripts/mpqem.py` gained `MP_CAP_MM` (stop a group's collapse above that rms) and the set builder `THIGH` (keep the boots' thigh
band) for a later attempt; neither was run in a ladder.

## Gates (installed only, for the record: `review/gates_before/`)
Arm/hand `--outer-only --exact` 0 frames > 1 cm (Death L hand 1.0 cm); jitter 0 fails; detached 0 (4 shallow); flat 0.00; winding 0;
bone lengths 2 calves (Death/Hit, the installed model's own); texture quality body atlas 29.3 % / head 33.7 %; sleeve lining
(`scripts/lining_gate.py`) Fidget max 24.1 mm outside (gate geometry near the cuff rim, installed). Blender gates (sleeve, poke)
not run: no candidate.

## Not checked
No candidate was built, so no viewer, sheets, LODs or Blender gates. A ladder with `MP_CAP_MM` might pass a step near -10 %, below
the brief's ~15 % bar.
