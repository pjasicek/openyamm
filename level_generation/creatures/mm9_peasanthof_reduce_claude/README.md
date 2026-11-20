# MM9 half-orc townswomen PeasantHOF1 / PeasantHOF2 reduction: kept, no useful gain (2026-11-05)

Batch: [REDUCTION_BRIEF_20261104.md](../../../devdocs/mm9_rework/overnight/REDUCTION_BRIEF_20261104.md) and
[REDUCTION_AGENT_TOWNSFOLK.md](../../../devdocs/mm9_rework/overnight/REDUCTION_AGENT_TOWNSFOLK.md), ledger rows 111 and 112 of
[REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md). Lease `mm9reduce:peasanthof` (owner peasanthof-reduce-20261105, released); the
creature's `mm9:peasanthof` lease was free. Sources: the installed `assets_source/worlds/mm9/models/mm9_peasanthof{1,2}.glb`
(sha256 bb2ae72942e4, 9529ff1936da; identical to `../mm9_peasanthof_claude/export/`), copied to `before/`. No Meshy, no credits,
no repaint, **nothing installed**. `../mm9_peasanthof_claude/` was only read.

## Result
Neither file reaches a ~15 % cut that passes the ladder's stop rule, so both are **kept (no useful gain)**.

| | LOD0 | protected (set b) | ladder b (forced ratios) | ladder c (error bound 4.5 mm) |
|---|---:|---:|---|---|
| HOF1 (`mm9_peasanthof1.glb`) | 14,488 | 5,645 (39.0 %) + 2,849 lining twins that follow the cloth | 11,978 (-17.3 %) **fail**: p99 7.88 / max 37.7 mm (Death:24) | 12,790 (-11.7 %) pass: p99 2.93 / max 8.3 mm, IoU .998, SSIM .995 |
| HOF2 (`mm9_peasanthof2.glb`) | 14,438 | 8,024 (55.6 %) + 2,646 lining twins | 12,760 (-11.6 %) **fail**: p99 8.73 / max 88.4 mm (AttackMelee, skirt) | 13,454 (-6.8 %) pass: p99 2.30 / max 5.5 mm, IoU .999, SSIM .995 |

Limits (ladder stop rule, height 1.954 / 1.956 m): p99 <= 5.86 mm, max <= 29.3 mm, IoU >= .98, SSIM >= .93.
Ladder a (HOF1 only: set a, no seam slides) reached 12,078 and was superseded by b before it was scored.

## Why
- **No shared body.** HOF2 is a variant of HOF1's fitted mesh but refitted to MM9's HOF2 with its own UV pass and paint: 0 of
  HOF2's 5,675 body vertices and 0 of its 4,628 head-primitive vertices coincide with HOF1's. So there was nothing to cut once
  and re-derive; the two files were cut separately with the same keep rules.
- **The cloth is already coarse.** The creature reduced Smart Topology to ~10k before its linings; the body's edges are 2-20 cm
  (a HOF2 skirt vertex has ring edges of 12-20 cm). Every body collapse that the error bound allows is refused: in ladder c the
  dress keeps 643 of 675 free faces (HOF1) and 323 of 361 (HOF2). Ladder b forces the ratios and the removed vertices land
  4-10 cm off the coarser surface in motion (HOF2 skirt 97 mm in AttackMelee, `scripts/probe_err.py`).
- **Linings.** `rim_lining.py` twinned most of the cloth (HOF1 2,849, HOF2 2,646 one-texel faces). They are found exactly
  (`scripts/lin_twins.py`: reversed corners, within 12 mm, behind the outer face, equal weights) and re-emitted from the
  surviving outer faces, so they did not block the cut; the rim strips, unmatched one-texel faces and one row of outer faces
  beside every rim stay exact.
- What ladder c removes is almost only hands 0.6 (1,270 -> 762 / 1,261 -> 757, every finger kept), HOF1's braids (1,742 -> 1,098)
  and hair shell (457 -> 273 / 545 -> 327). HOF2's kerchief (2,082) is exact: its inner layer is a decimated copy, not a twin.

## Untried lever (not run: the three-ladder limit)
An error bound of 6-8 mm on HOF1's body would sit between c (-11.7 %) and b (-17.3 %); expect about -14 %, still near the 15 %
line, with the bodice/skirt cut where the gates are hardest (armholes, hem). HOF2 has no such lever below its protected 55.6 %.

## Scripts (project folder; `M=1|2` picks the model, outputs in `work/hof$M/`, `review/hof$M/`)
```sh
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"; G=../claude_shared/gltf_venv/bin/python
M=1 REA_GLB=level_generation/creatures/mm9_peasanthof_reduce_claude/before/mm9_peasanthof1.glb REA_NODE=PeasantHOF $BL -P scripts/import_source.py
M=1 $BL -P scripts/dump_mesh.py; M=1 $G scripts/tex_extract.py
M=1 MASKB=1 RIMBAND=0.012 ORPHAN=0.006 $G scripts/make_sets_phof.py b          # HOF2: + GRAFT=0.03 NECK=0.015
M=1 MP_CHART=1 MP_W5=4 MP_SEAM_GROUPS=0,1,2,3,4,5,6,7 SETS=b MP_GROUPS=1:0.6,2:0.5,3:0.6,4:0.5,5:0.5,6:0.6,7:0.4 MP_MAXDEV=0.0045 \
  MP_TEX_MAX=70 MP_TEX_MEAN=30 REA_HEIGHT_M=1.954 scripts/run_mp.sh c 0.3,0.45    # ladder b: no MP_MAXDEV, groups 2:0.7,3:0.7,4:0.6,5:0.7,6:0.75,7:0.55, ratios 0.5,0.4
```
`mpqem.py` (PeasantF8's copy) gained: lined and unlined faces of one group cut as separate subsets; one-texel lining twins exempt
from the twin UV flip/chart checks; `MP_MAXDEV` (a collapse is refused when the removed vertex, or any vertex it absorbed, lies
further than this from the new faces in any sampled pose). Built for a candidate but not used: `build_mp.sh`, `build_lods.py`,
`gates.sh`, `see_through.sh`, `viewer_tiers.py`, `shots.sh`, `close_shots.sh`, `face_exact.py`. Ladder sheets:
`review/hof1/ladder_sheet_c.png`, `review/hof2/ladder_sheet_c.png`. Partial installed-model gates (HOF1 jitter 0 fails, robe 0,
sleeve poke 0): `review/hof1/gates_inst/`; the run was stopped once the result was clear.
