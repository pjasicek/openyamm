# Old Hag (`mm9_hag.glb`) reduction: kept (no useful gain), 2026-11-05

Batch: [REDUCTION_AGENT_TOWNSFOLK.md](../../../devdocs/mm9_rework/overnight/REDUCTION_AGENT_TOWNSFOLK.md) and
[REDUCTION_BRIEF_20261104.md](../../../devdocs/mm9_rework/overnight/REDUCTION_BRIEF_20261104.md) (relaxed keep set, face exact;
uniques reduced on the user's "do all", 2026-11-05), ledger row 72 of [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md). Lease
`mm9reduce:hag` (owner hag-reduce-20261105, released at the end); the creature's own `mm9:hag` lease was free. Source: the
installed `assets_source/worlds/mm9/models/mm9_hag.glb` (sha256 6409f9375efa, = `../mm9_hag_claude/v2/export/mm9_hag.glb`),
copied to `before/`. `../mm9_hag_claude/` and `../mm9_yrsa_reduce_claude/` were only read. No Meshy, no credits.
**Nothing exported or installed; the installed model stays as it is.**

## Labels: carried from the Yrsa reduction
The Hag is Yrsa's approved body with the forehead bead parts deleted and the sleeves flared (no new topology), re-UV'd by the
texture pass (different charts). `scripts/carry_parts.py` measured: body primitive face i = Yrsa's face i (2,993 at identical
centroids, the 382 flared-sleeve faces at the same index with identical joint sets), head primitive faces in order by centroid
(5,102 exact; the 199 bead faces of part 23 gone); per-corner weights and joints identical. Yrsa's part labels
(`../mm9_yrsa_reduce_claude/work/glb_parts.npz`) carried to `work/glb_parts.npz`; lining twins rebuilt through each lined face's
paired lining face. The Hag's lining has UV seams the outer sleeve lacks (23 outer vertices with two lining twins): `mpqem.py`
picks per re-emitted lining face the twin combination with the smallest UV triangle (`twins`). Keep set `scripts/make_sets_hag.py`
(Yrsa's builder, recomputed on the Hag's geometry and clips: `CONTACT=0.03 HW=0.015`).

## Protected share (measured first)
Kept exactly 4,199 of 8,477 (49.5 %): face/neck skin with upper braids 1,724, other head pieces 815, forearm extensions + stubs 370,
hairline 536 of hood/hair, rims/inner sleeve 98, small pieces 223, fingertips 117, collar 84, contact 71, headwear clearance 53,
wrist 39, soles 28, unpaired lining and its outer faces 28. Free 3,976 + 302 sleeve lining (re-emitted). 15 % of LOD0 (1,272) is
32 % of the free part, so ladders were run.

## Ladders (pose-aware `scripts/mpqem.py`, `MP_AUDIT=1 MP_CHART=1 MP_W5=4 MP_SEAM_GROUPS=1`)
Limits for 1.692 m (as Yrsa, same body): p99 <= 5.08 mm, max <= 25.38 mm, IoU >= .98, SSIM >= .93. Groups 1 hands, 2 hood/hair,
4 boots, 5 belt + chest panel; 0 = ladder ratio.

| ladder | groups | step | LOD0 | p99 / max mm (worst) | IoU / SSIM | result |
|---|---|---|---:|---|---|---|
| a | hands .65, hood .75, boots .7, belt .7; bodice+sleeves+skirt ladder | r65 | 7,117 (-16.0 %) | 7.10 / 28.2 (Hit:15, L upper-arm sleeve) | .9938 / .9865 | fail |
| a | | r50 / r35 | 6,921 (stall) | 10.74 / 47.1 | .9869 / .9772 | fail |
| b | hands .6, hood .6, boots .6, belt .7, bodice+sleeves .75 (own group, `BODICEG=1`); skirt ladder; cap 6 mm | r70 / r60 / r50 | 7,129 / 6,993 / 6,987 | 7.40 / 41.8, 8.35 / 41.8, 8.53 / 41.8 (Hit:12, back skirt and hood) | .992 / .988 | fail |
| c | hands .6, hood .7, boots .6, belt .6, bodice .6; skirt ladder; `MP_CAP_MM=3` | r75 / r60 / r45 | 7,257 (-14.4 %) / 7,221 (-14.8 %, cap stall) | 5.74 / 28.4, 5.96 / 28.4 (Hit:15, L upper-arm sleeve) | .996 / .991 | fail |

Unlike Yrsa (her bodice + skirt stalled at -13 % on the texture/chart guards) the Hag's texture-pass charts let the dress be cut,
but the dress was already cut to 0.42 at the build: even at rest (`scripts/region_error.py`, Standing:0) every further collapse
leaves 5-10 mm on the bodice (Spine2), the upper-arm sleeves and the back skirt. With a 3 mm collapse cap the cut stops at -14.8 %
and still fails p99 (5.96 vs 5.08) and max (28.4 vs 25.4, left sleeve in Hit). Three ladders, none passes at or above -15 %: the
stop rule applies, so this project stops at "kept". A passing step would need a gentler cut than -14 %, below the brief's bar.

## Gates (installed only, for the record: `review/gates_before/`)
Arm/hand `--outer-only --exact` 0 frames > 1 cm (Death L hand 1.0 cm); jitter 0 fails; detached 0 (4 shallow); flat 0.00 / 0.00;
winding 0; bone lengths 2 calves (Death/Hit, installed); texture quality body atlas 62.4 % / head 44.5 %; sleeve lining
(`scripts/lining_gate.py`) max 11.75 mm outside. The Hag project's own sleeve and see-through results stay in
`../mm9_hag_claude/v2/review/gates/`. No candidate, so no UV audit, Blender gates, LODs, sheets or viewer.

## Files
`scripts/carry_parts.py`, `make_sets_hag.py`, `mpqem.py` (twins), `run_mp.sh`, `region_error.py`, `probe_err.py`; logs
`work/run_{a,b,c}.out`, `work/compare_{a,b,c}.log`, `work/selection_{a,b,c}.json`, ladder sheets `review/ladder_sheet_{a,b,c}.png`.
