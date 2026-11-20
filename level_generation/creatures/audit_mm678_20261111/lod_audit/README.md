# LOD audit of the 104 models changed on 2026-11-11/12

Read-only audit of the far LODs of every MM6–MM8 model in the [compare viewer](../compare_viewer/README.md)
manifest (71 texture passes, 7 rebuilds or reverts, 28 clip/attack-only), against the
[LOD playbook](../../LOD_PLAYBOOK.md). Nothing was installed or changed. Inputs: the installed sources
`assets_source/worlds/<w>/models/<stem>.glb` ("after") and the HEAD copies in `../compare_viewer/before/` ("before").

## Verdict

**Yes, new far LODs are needed, but not everywhere.**

| Group | Models | Finding | Fix |
|---|---:|---|---|
| Rebuilds `mm6_gua`, `mm6_thf`, `mm6_mer1`, `mm6_pfem` | 4 | far chain from `build_actor_lods.py` defaults (LOD3 6 %), LOD2/LOD3 sample the LOD0 atlas; pfem LOD3 colour 24.2 (gate 19.5) with smeared skirt hem, gua/thf LOD3 lose the mail and leg detail (detail correlation 0.05 against 0.31-0.39 before the rebuild); pfem's LOD3 shadow 23 % outside | `repair.py` ladder, required |
| Texture passes missing a switch gate (all **pre-existing**: identical scores before the pass) | 10 | LOD2 outline 6.1-29.7 % (`mm7_m158` Bat loses its wing bones, `mm8_m572` Phoenix also LOD3 14.6 %), `mm6_lch`, `mm6_lzd`, `mm6_ske`, `mm7_m242`, `mm7_m386`, `mm7_m390`, `mm7_m479`, `mm8_m552` | ladder (the rerun is due anyway) |
| Texture passes with far LODs on the LOD0 atlas, colours off LOD0 | 2 | `mm8_m516` (LOD3 vertex colour p90 71), `mm8_m608` (p90 52): projected far UVs land on wrong charts in places | ladder |
| Other texture passes (own far maps) | 52 | pass every switch gate; far maps were refilled by the texpass `apply.py` = nearest-point `transfer()` (4x supersampled), not UV correspondence; detail correlation unchanged by the pass (median -0.01 at LOD2) | ladder in one batch, recommended, not urgent |
| Atlas far LODs that pass (`mm6_sor1`, `mm7_m186`, `mm7_m258`, `mm8_m548`, `mm8_wolf`, `mm8_m600`, `mm8_m540`, `mm8_m440`, `mm8_m416`, `mm8_m584`, `mm8_m464`) and `mm8_m536` (effect body, LOD2 6.2 %, pre-existing) | 12 | kept installed in October; pass | keep |
| Clip/attack-only, `mm6_ttn` (hands grafted on LOD0, far chain unchanged, passes), `mm6_wwf` and `mm8_lizardman_peasant` (reverted originals + texture pass: pass, counted with the 52) | 24 | geometry and maps unchanged or passing | keep |

Masks and variants are clean: no four-ramp model has an RGB far mask (RGB masks remain only on 17 one- or two-ramp
models, harmless), no variant far copy points at the default's map where the tier has its own paint, and every
`_LOD<N>` copy's ramps equal its LOD0 material's. No region-mask rerun is needed.

**Shadows ("leaking shadows")**: measured, not confirmed in game. 53 models have more than 2 % and 26 more than 5 %
of a shadow level's surface over 1 world unit outside a colour level drawn with it (worst pair mostly LOD3 shadow against
colour LOD0/LOD1); all of it predates today except the two rebuilds (pfem 0.2 -> 23 %, thf 3.0 -> 7.3 %). Repaired MM9
bodies measure 1-8 %. The in-game check (below) showed no blotches at New Sorpigal's start light. Cause and proposed fix:
[playbook §5](../../LOD_PLAYBOOK.md#5-shadow-lods-and-leaking-shadows) (a surface-sampled tuck; the ladder does not change
it). Over 10 %: `mm6_drg1`, `mm6_ckt`, `mm6_pfem`, `mm7_m479`, `mm8_m548`, `mm8_m608`, `mm8_m588`, `mm8_m572`,
`mm8_m552`, `mm8_m560` (and its MM7 copy `mm7_m434`, 8.5 %).

## Gate counts (after)

| Gate | Pass | Fail |
|---|---:|---:|
| LOD2 switch (outline <= 6 %, colour <= 16 or LOD1 + 3) | 93 | 11 (the 10 above + `mm8_m536`) |
| LOD3 switch (outline <= 13 %, colour <= 19.5) | 101 | 3 (`mm6_pfem`, `mm7_m158`, `mm8_m572`) |
| Far maps (own far maps at LOD2/3, RGBA mask on four ramps, variants, ramps, LOD3 >= 8 %) | 86 | 18 atlas far LODs: the 4 rebuilds, `mm8_m516` and `mm8_m608` (ladder) and 12 kept |
| Shadow, share > 1 unit outside <= 2 % / <= 5 % | 51 / 78 | 53 / 26 |
| Regressions against before (> 1 point) | | only `mm6_thf`, `mm6_gua`, `mm6_pfem` (the rebuilds) |

Medians over the 104 (outline % / colour): LOD1 1.3 / 9.2, LOD2 3.6 / 10.1, LOD3 5.8 / 9.0.

## Sheets to look at

- `sheets/worst_a.png` (`mm7_m158`, `mm6_pfem`, `mm8_m572`, `mm8_m548`, `mm6_thf`) and `sheets/worst_b.png`
  (`mm8_m536`, `mm8_wolf`, `mm8_m608`, `mm7_m390`, `mm8_m588`): three-quarter view, LOD0, then LOD1/2/3 as seen at
  450/180/72 px, then LOD2 and LOD3 at full render size.
- `sheets/rebuilt.png` (`mm6_gua`, `mm6_mer1`, `mm6_ttn`, `mm6_wwf`, `mm8_lizardman_peasant`) and
  `sheets/rebuilt_before.png` (gua, mer1, thf, pfem, ttn before the rebuilds).
- In game (`ingame/`, New Sorpigal, isolated minimized runs, `model spawn` of `mm6_gua`, `mm6_pfem`, `mm6_ckt`,
  `mm8_m588`, bind pose seen from behind with the sun ahead; tours `lods_high.yml`, `lods_low.yml`): `high/` and
  `low/` hold forced `render lod 0..3`, natural LOD and no-shadow shots at shadow quality 3 and 1; `crop_gua_pfem.png`,
  `crop_ckt.png`, `crop_m588.png` put LOD0/1/2/3/no-shadow side by side (top row high, bottom low). What they show:
  pfem's LOD3 skirt streaked and speckled and its LOD2 skirt shading broken up, gua's LOD3 mail flattened (both rebuilds);
  ckt's LOD2 body pattern noisier than LOD0 and LOD3 flat (expected at 72 px); boulder LOD3 faceted; no visible
  self-shadow blotches at either shadow quality in this light.

What I saw on the sheets: the Bat's LOD2/LOD3 lose most wing bones (pre-existing); the Phoenix LOD3 loses feather tips;
the rebuilt guard's LOD3 turns the mail into a flat tan and the merchant's LOD3 face blurs; the boulder's far levels open
dark gaps between stones at full size (invisible at 72 px); the werewolf's LOD3 left arm reads as a blade-like slab
(passes the score, pre-existing).

## Recommended work, time and cost

No Meshy credits. All CPU (pymeshlab, xatlas, Blender Workbench), at most four lanes.

1. **Prerequisites (about 1-2 h, once):** a durable venv (`lod_repair_claude/venv`: pymeshlab, xatlas, numpy, scipy,
   pillow; the October/November venv was in /tmp and is gone, and the `claude_shared` meshlab/xatlas venvs each lack a
   module); a `repair.py` source option (or moving `originals/<stem>.glb` aside), because `originals/` holds the
   pre-rebuild/pre-texpass GLBs of all seven rebuilt models and of all 71 texture-pass models; a strip step for old
   `<material>_LOD<N>` materials and images (`apply_bake.py` refuses inputs that have them).
2. **Rebuilds (4 models, about 1 h):** ladder from the installed GLB, audit, forced-LOD captures, install, ledger rows.
3. **Pre-existing gate misses and the two atlas models (12, about 1.5 h):** same route; the Bat may need the last ladder
   step or a protected wing-bone budget; keep any model whose rerun is not visibly better.
4. **Batch of the other 52 texture-pass models (about 2-3 h):** about 1-2 min per model per lane (most pass at the first
   step: 30 s build/unwrap/transfer/apply plus the audit render), so about 30 min of compute in four lanes, the rest
   review, in-game spot checks, installs and the desktop cook. Shared layout: rebuild `mm7_m434` from `mm8_m560`.
5. **Shadow tuck (separate decision):** write the surface-sampled tuck and confirm a leak in game first (low shadow
   quality, a model over 10 %); 2-3 h.

## Caveats

- **Clips after `originals/`:** head-bob reshaping (23 MM6–MM8 models), the 2026-10-31 gaits (Walk2/Jog/Run/Sprint),
  today's Hit/attack/loop fixes and the texture passes are only in the installed GLBs. A rerun must start from the
  installed source; `build_lods.py` keeps clips byte for byte, so nothing then needs reapplying.
- **MeshLab is not deterministic:** a rerun builds slightly different far meshes than the scores above and may land on
  another ladder step; keep each run's `<step>.built.glb` so later map-only fixes can reuse it.
- The colour score cannot see grain. `fine_score.py` (detail correlation at 512 px) separates nearest-point from
  UV-correspondence maps only weakly (calibration on six MM9 bodies, `calib_nearest/` vs `calib_param/`: +0.03 to
  +0.09 at LOD2, colour within 0.6), so the batch's benefit has to be judged in game.
- Shadow numbers are bind pose, measured against the merged colour level; double-sided sheets (wings, capes) can read
  as outside on their back side. The threshold for visible leaks is not calibrated.
- `vertices_on_lod0` < 1 on LOD1 and on atlas far levels is normal (Blender's collapse moves vertices); their vertex
  colour check covers only the vertices that match.

## Files

`models.tsv` (stem, world, streams, after/before GLB); `run_lane.sh` + `lanes/` (render queue: `lod_split.py`,
`lod_render.py` with `LOD_RENDER_CULL=1`); `after/`, `before/`, `calib_*/` renders; `scores_*.tsv` (`lod_score.py`);
`fine_*.tsv` (`fine_score.py`); `static_*.jsonl` (`lod_static.py`: ratios, far map sizes, UV share, mask channels, ramps,
variants, vertex colours, atlas smear); `shadow_*.jsonl` (`shadow_check.py`, world units, scale from the bindings in
`scales.txt`); `aggregate.py` -> `table.json`, `table.tsv`; `table_md.py` -> the table below; `sheet.py` -> `sheets/`.

## Per-model table

Columns: switch scores outline % / colour (worst of three views); hf = detail correlation of LOD2/LOD3 with LOD0 at
512 px (before in brackets); far maps = own far maps (largest size per level, UV share range, mask channels, LOD0 ramp
count) or LOD0 atlas; shadow = worst shadow/colour pair and its share more than 1 world unit outside; gates =
switch scores / far maps / shadow (2 %).

| Model | Streams | LOD0 tris | LOD2/3 % | LOD1 out/col | LOD2 out/col | LOD3 out/col | hf2/hf3 (before) | Far maps | Shadow worst (> 1 u) | Gates S/F/Sh | Fix |
|---|---|---:|---|---|---|---|---|---|---|---|---|
| `mm6_bh` | texture | 7,341 | 25/12 | 1.4/9.3 | 4.2/14.6 | 7.6/14.1 | 0.20/0.03 (0.23/0.04) | own 512/256, UV 0.34-0.40, RGBA, 3 ramps | s3c1 9.5 % | PP**F** | ladder, batch (UV correspondence) |
| `mm6_drg1` | texture | 7,968 | 35/20 | 2.6/6.8 | 5.7/7.4 | 7.9/4.2 | 0.76/0.57 (0.76/0.56) | own 512/256, UV 0.18-0.51, RGBA, 2 ramps | s3c0 15.7 % | PP**F** | ladder, batch (UV correspondence) |
| `mm6_gar` | texture | 7,249 | 40/25 | 3.5/9.7 | 5.6/10.1 | 6.3/9.3 | 0.69/0.56 (0.69/0.54) | own 512/256, UV 0.26-0.56, RGBA, 2 ramps | s3c1 5.5 % | PP**F** | ladder, batch (UV correspondence) |
| `mm6_djn` | texture | 8,443 | 25/12 | 0.9/8.4 | 4.5/11.9 | 8.0/8.8 | 0.63/0.33 (0.67/0.36) | own 512/256, UV 0.31-0.39, RGBA, 2 ramps | s3c0 2.1 % | PP**F** | ladder, batch (UV correspondence) |
| `mm6_gst` | texture | 9,625 | 25/12 | 0.9/5.8 | 3.4/8.4 | 7.7/10.1 | 0.63/0.42 (0.64/0.42) | own 512/256, UV 0.35-0.43, RGBA, 3 ramps | s3c0 1.3 % | PPP | ladder, batch (UV correspondence) |
| `mm6_gob2` | clips+texture | 6,154 | 25/12 | 2.0/12.5 | 5.6/13.5 | 7.2/8.9 | 0.37/0.16 (0.38/0.15) | own 512/256, UV 0.36-0.43, RGBA, 1 ramps | s3c0 2.2 % | PP**F** | ladder, batch (UV correspondence) |
| `mm6_hyd` | texture | 7,926 | 25/12 | 2.0/10.7 | 4.8/13.0 | 7.9/13.0 | 0.46/0.20 (0.48/0.20) | own 512/256, UV 0.16-0.47, RGBA, 4 ramps | s3c0 8.0 % | PP**F** | ladder, batch (UV correspondence) |
| `mm6_lch` | texture | 6,290 | 40/25 | 3.4/7.7 | 7.4/8.8 | 5.4/5.6 | 0.70/0.55 (0.75/0.58) | own 512/256, UV 0.31-0.40, RGBA, 1 ramps | s3c0 0.8 % | **F**PP | ladder (pre-existing gate miss) |
| `mm6_med` | texture | 9,684 | 25/12 | 1.0/4.6 | 3.2/5.9 | 5.4/5.4 | 0.80/0.46 (0.83/0.48) | own 512/256, UV 0.34-0.45, RGBA, 3 ramps | s3c0 0.8 % | PPP | ladder, batch (UV correspondence) |
| `mm6_thf` | rebuild | 9,638 | 18/6 | 0.8/8.2 | 2.2/11.6 | 4.9/13.4 | 0.41/0.05 (0.59/0.39) | LOD0 atlas, RGBA, 1 ramps | s3c0 7.3 % | P**F****F** | ladder (required) |
| `mm6_ttn` | rebuild | 10,736 | 25/12 | 0.3/8.5 | 1.9/10.0 | 6.4/9.5 | 0.66/0.31 (0.63/0.35) | own 512/256, UV 0.35-0.42, RGBA, 3 ramps | s3c0 6.1 % | PP**F** | keep (passes; hands not in far chain) |
| `mm6_cob` | texture | 6,000 | 25/12 | 0.8/8.3 | 1.4/8.6 | 2.8/5.6 | 0.75/0.50 (0.81/0.51) | own 512/256, UV 0.35-0.37, RGBA, 3 ramps | s3c1 0.1 % | PPP | ladder, batch (UV correspondence) |
| `mm6_ckt` | texture | 6,070 | 35/20 | 2.6/11.0 | 4.7/9.8 | 7.0/6.9 | 0.77/0.59 (0.78/0.58) | own 512/256, UV 0.08-0.42, RGBA, 2 ramps | s3c0 27.3 % | PP**F** | ladder, batch (UV correspondence) |
| `mm6_demon` | texture | 9,060 | 30/16 | 7.0/14.5 | 5.7/13.7 | 9.7/11.9 | 0.69/0.33 (0.71/0.32) | own 512/256, UV 0.16-0.42, RGBA, 2 ramps | s3c0 1.1 % | PPP | ladder, batch (UV correspondence) |
| `mm6_wdm` | clips+texture | 8,846 | 30/16 | 2.4/13.8 | 5.3/14.2 | 7.6/9.6 | 0.56/0.30 (0.57/0.30) | own 512/256, UV 0.18-0.40, RGBA, 1 ramps | s3c2 0.9 % | PPP | ladder, batch (UV correspondence) |
| `mm6_cdr1` | texture | 8,581 | 40/25 | 0.9/4.7 | 5.1/7.5 | 4.1/6.2 | 0.82/0.64 (0.82/0.62) | own 512/256, UV 0.18-0.47, RGB/RGBA, 2 ramps | s3c0 1.2 % | PPP | ladder, batch (UV correspondence) |
| `mm6_wyrm` | attack+texture | 9,214 | 30/16 | 2.1/8.3 | 5.2/8.7 | 5.7/7.0 | 0.87/0.68 (0.87/0.64) | own 512/256, UV 0.06-0.37, RGBA, 2 ramps | s3c3 5.8 % | PP**F** | ladder, batch (UV correspondence) |
| `mm6_dru1` | texture | 6,455 | 25/12 | 1.2/9.6 | 1.6/12.9 | 4.0/10.6 | 0.52/0.29 (0.54/0.27) | own 512/256, UV 0.36-0.41, RGBA, 1 ramps | s3c0 1.7 % | PPP | ladder, batch (UV correspondence) |
| `mm6_gua` | rebuild | 9,781 | 18/6 | 1.0/9.5 | 2.5/9.0 | 8.5/13.0 | 0.25/0.05 (0.57/0.31) | LOD0 atlas, RGBA, 3 ramps | s3c0 1.7 % | P**F**P | ladder (required) |
| `mm6_kni` | clips | 8,335 | 25/12 | 1.5/8.2 | 4.6/10.7 | 6.9/8.7 | 0.60/0.38 (0.60/0.38) | own 512/256, UV 0.36-0.45, RGB, 2 ramps | s3c0 1.6 % | PPP | keep |
| `mm6_lzd` | clips+texture | 6,888 | 25/12 | 3.9/13.2 | 6.1/14.4 | 6.8/9.5 | 0.45/0.22 (0.52/0.24) | own 512/256, UV 0.19-0.40, RGBA, 1 ramps | s3c1 2.8 % | **F**P**F** | ladder (pre-existing gate miss) |
| `mm6_mer1` | rebuild | 10,584 | 18/6 | 0.6/5.3 | 2.0/7.8 | 4.4/10.0 | 0.51/0.20 (0.49/0.34) | LOD0 atlas, RGBA, 1 ramps | s3c0 0.7 % | P**F**P | ladder (required) |
| `mm6_nobl` | texture | 6,603 | 25/12 | 1.6/12.2 | 3.1/14.2 | 6.2/10.6 | 0.46/0.21 (0.48/0.21) | own 512/256, UV 0.37-0.44, RGBA, 2 ramps | s3c0 2.2 % | PP**F** | ladder, batch (UV correspondence) |
| `mm6_pfem` | rebuild | 9,456 | 18/6 | 0.5/11.0 | 2.5/15.1 | 4.8/24.2 | 0.54/0.18 (0.82/0.65) | LOD0 atlas, RGBA, 1 ramps | s3c1 23.0 % | **F****F****F** | ladder (required) |
| `mm6_mfp` | attack+clips+texture | 7,939 | 25/12 | 1.0/4.8 | 3.6/7.3 | 4.5/6.7 | 0.80/0.53 (0.79/0.51) | own 512/256, UV 0.38-0.47, RGBA, 1 ramps | s3c0 1.1 % | PPP | ladder, batch (UV correspondence) |
| `mm6_natf` | texture | 8,613 | 25/12 | 0.9/7.0 | 3.4/9.6 | 5.8/8.2 | 0.61/0.38 (0.60/0.40) | own 512/256, UV 0.38-0.47, RGBA, 2 ramps | s3c0 2.1 % | PP**F** | ladder, batch (UV correspondence) |
| `mm6_pman_v2` | clips | 6,116 | 25/12 | 1.2/10.4 | 2.5/10.9 | 4.7/8.6 | 0.67/0.36 (0.67/0.36) | own 512/256, UV 0.39-0.46, RGB, 1 ramps | s2c1 0.5 % | PPP | keep |
| `mm6_natm` | texture | 6,003 | 25/12 | 5.4/9.9 | 5.8/9.6 | 9.1/10.6 | 0.50/0.25 (0.52/0.25) | own 512/256, UV 0.33-0.42, RGBA, 1 ramps | s3c1 2.0 % | PP**F** | ladder, batch (UV correspondence) |
| `mm6_seas` | texture | 6,286 | 25/12 | 1.6/11.6 | 4.1/12.8 | 7.2/9.1 | 0.47/0.27 (0.52/0.31) | own 512/256, UV 0.40-0.41, RGBA, 3 ramps | s3c2 4.8 % | PP**F** | ladder, batch (UV correspondence) |
| `mm6_ske` | texture | 6,292 | 40/25 | 5.3/18.8 | 7.6/17.1 | 12.2/6.4 | 0.85/0.69 (0.87/0.68) | own 512/256, UV 0.26-0.33, RGBA, 1 ramps | s3c0 0.4 % | **F**PP | ladder (pre-existing gate miss) |
| `mm6_sor1` | clips | 7,753 | 24/12 | 1.0/4.8 | 2.1/6.8 | 2.5/5.7 | 0.50/0.42 (0.50/0.42) | LOD0 atlas, RGBA, 1 ramps | s3c2 0.3 % | P**F**P | keep (atlas far LOD passes) |
| `mm6_wwf` | rebuild+texture | 6,489 | 25/12 | 2.2/6.3 | 4.0/9.1 | 8.6/13.6 | 0.52/0.17 (0.55/0.18) | own 512/256, UV 0.36-0.46, RGBA, 2 ramps | s3c0 2.8 % | PP**F** | ladder, batch (UV correspondence) |
| `mm7_m182` | clips+texture | 7,056 | 40/25 | 1.2/8.0 | 4.9/9.2 | 5.3/7.0 | 0.80/0.60 (0.80/0.60) | own 512/256, UV 0.22-0.46, RGBA, 4 ramps | s3c0 2.9 % | PP**F** | ladder, batch (UV correspondence) |
| `mm7_m461` | clips | 7,598 | 25/12 | 0.6/6.8 | 3.4/9.3 | 6.6/9.0 | 0.48/0.23 (0.48/0.23) | own 512/256, UV 0.34-0.42, RGBA, 4 ramps | s3c0 6.9 % | PP**F** | keep |
| `mm7_m434` | texture | 9,071 | 25/12 | 1.7/6.7 | 5.5/6.8 | 6.0/3.8 | 0.77/0.62 (0.79/0.59) | own 512/256, UV 0.28-0.34, RGBA, 2 ramps | s3c1 8.5 % | PP**F** | ladder, batch (UV correspondence) |
| `mm7_m158` | texture | 6,084 | 25/12 | 8.6/17.6 | 29.7/21.7 | 30.0/15.5 | 0.50/0.28 (0.57/0.29) | own 512/256, UV 0.30-0.40, RGBA, 1 ramps | s3c0 4.3 % | **F**P**F** | ladder (pre-existing gate miss) |
| `mm7_m162` | clips+texture | 11,063 | 25/12 | 1.2/6.3 | 3.6/8.4 | 4.3/8.4 | 0.33/0.15 (0.38/0.14) | own 512/256, UV 0.30-0.36, RGBA, 1 ramps | s3c0 6.4 % | PP**F** | ladder, batch (UV correspondence) |
| `mm7_m166` | texture | 6,814 | 30/16 | 2.0/12.6 | 5.2/13.9 | 7.4/9.0 | 0.71/0.48 (0.72/0.46) | own 512/256, UV 0.34-0.41, RGBA, 3 ramps | s3c0 2.6 % | PP**F** | ladder, batch (UV correspondence) |
| `mm7_m170` | clips+texture | 7,179 | 25/12 | 1.4/9.3 | 2.8/10.5 | 4.5/9.0 | 0.56/0.38 (0.57/0.35) | own 512/256, UV 0.43-0.53, RGBA, 2 ramps | s3c1 0.7 % | PPP | ladder, batch (UV correspondence) |
| `mm7_m174` | attack | 6,305 | 25/12 | 1.6/9.8 | 4.9/13.1 | 7.3/13.9 | 0.77/0.44 (0.77/0.44) | own 512/256, UV 0.44-0.52, RGB, 1 ramps | s3c0 3.3 % | PP**F** | keep |
| `mm7_m186` | texture | 7,227 | 25/12 | 1.8/8.0 | 3.5/6.8 | 4.6/5.0 | 0.66/0.62 (0.67/0.62) | LOD0 atlas, RGBA, 1 ramps | s0c0 0.0 % | P**F**P | keep (atlas far LOD passes) |
| `mm7_m190` | clips | 8,995 | 25/12 | 1.1/9.4 | 3.4/10.9 | 5.8/10.7 | 0.54/0.18 (0.52/0.17) | own 512/256, UV 0.37-0.45, RGB, 1 ramps | s3c0 2.2 % | PP**F** | keep |
| `mm7_m210` | attack | 5,790 | 25/12 | 1.2/12.2 | 4.2/13.6 | 6.1/10.3 | 0.73/0.39 (0.73/0.39) | own 512/256, UV 0.41-0.47, RGBA, 3 ramps | s3c2 1.1 % | PPP | keep |
| `mm7_m214` | clips | 6,931 | 25/12 | 1.2/9.0 | 3.6/10.5 | 8.4/8.6 | 0.78/0.47 (0.78/0.47) | own 512/256, UV 0.37-0.44, RGB, 2 ramps | s3c1 0.7 % | PPP | keep |
| `mm7_m218` | texture | 8,616 | 25/12 | 0.9/5.4 | 2.0/6.5 | 5.6/7.4 | 0.85/0.60 (0.85/0.59) | own 512/256, UV 0.36-0.45, RGBA, 1 ramps | s3c1 0.3 % | PPP | ladder, batch (UV correspondence) |
| `mm7_m238` | texture | 7,786 | 25/12 | 0.6/7.0 | 3.3/9.5 | 7.4/9.2 | 0.83/0.57 (0.83/0.54) | own 512/256, UV 0.32-0.41, RGBA, 1 ramps | s3c0 1.9 % | PPP | ladder, batch (UV correspondence) |
| `mm7_m242` | clips+texture | 6,696 | 25/12 | 5.1/7.1 | 7.7/6.8 | 9.6/8.2 | 0.39/0.25 (0.40/0.22) | own 512/256, UV 0.33-0.40, RGBA, 1 ramps | s3c0 0.9 % | **F**PP | ladder (pre-existing gate miss) |
| `mm7_m246` | texture | 8,603 | 25/12 | 1.4/10.8 | 5.0/14.1 | 5.4/10.5 | 0.59/0.27 (0.60/0.24) | own 512/256, UV 0.32-0.39, RGBA, 2 ramps | s3c0 1.1 % | PPP | ladder, batch (UV correspondence) |
| `mm7_m254` | clips | 8,043 | 25/12 | 0.8/7.4 | 2.2/8.7 | 4.3/7.7 | 0.62/0.31 (0.62/0.31) | own 512/256, UV 0.37-0.44, RGB, 2 ramps | s3c0 2.1 % | PP**F** | keep |
| `mm7_m258` | texture | 9,188 | 25/10 | 2.6/7.8 | 4.8/8.6 | 9.3/9.6 | 0.54/0.35 (0.56/0.35) | LOD0 atlas, RGBA, 3 ramps | s3c0 0.9 % | P**F**P | keep (atlas far LOD passes) |
| `mm7_m262` | clips | 7,312 | 40/25 | 3.0/9.1 | 4.4/9.0 | 6.9/6.9 | 0.71/0.51 (0.71/0.51) | own 512/256, UV 0.30-0.37, RGB, 2 ramps | s3c0 1.2 % | PPP | keep |
| `mm7_m266` | texture | 13,946 | 30/16 | 2.0/11.3 | 5.0/11.9 | 5.9/8.4 | 0.52/0.26 (0.52/0.26) | own 512/256, UV 0.28-0.41, RGBA, 1 ramps | s3c1 8.5 % | PP**F** | ladder, batch (UV correspondence) |
| `mm7_m270` | texture | 7,054 | 25/12 | 1.1/11.1 | 3.5/12.1 | 4.3/8.4 | 0.50/0.13 (0.57/0.14) | own 512/256, UV 0.35-0.44, RGBA, 1 ramps | s3c1 3.1 % | PP**F** | ladder, batch (UV correspondence) |
| `mm7_m274` | attack | 8,124 | 25/13 | 1.1/8.9 | 2.8/13.2 | 3.4/12.3 | 0.59/0.24 (0.59/0.24) | own 512/256, UV 0.41-0.47, RGBA, 3 ramps | s3c0 1.5 % | PPP | keep |
| `mm7_m278` | texture | 10,588 | 25/12 | 3.8/13.4 | 3.7/12.0 | 8.1/11.1 | 0.39/0.21 (0.43/0.21) | own 512/256, UV 0.31-0.38, RGBA, 2 ramps | s3c0 1.4 % | PPP | ladder, batch (UV correspondence) |
| `mm7_m282` | attack | 9,756 | 25/12 | 1.0/7.9 | 4.0/8.8 | 5.0/6.7 | 0.68/0.37 (0.68/0.37) | own 512/256, UV 0.33-0.41, RGB, 1 ramps | s3c0 0.9 % | PPP | keep |
| `mm7_m290` | clips | 7,081 | 25/12 | 1.2/11.5 | 2.5/12.7 | 4.8/9.8 | 0.59/0.20 (0.59/0.20) | own 512/256, UV 0.35-0.41, RGB, 1 ramps | s3c1 1.0 % | PPP | keep |
| `mm7_m294` | clips | 9,125 | 25/12 | 0.8/4.7 | 2.6/8.9 | 5.7/8.2 | 0.53/0.24 (0.53/0.24) | own 512/256, UV 0.34-0.40, RGB, 1 ramps | s3c1 4.2 % | PP**F** | keep |
| `mm7_m302` | clips+texture | 8,755 | 25/12 | 0.6/7.4 | 2.4/9.6 | 3.0/9.6 | 0.67/0.40 (0.68/0.39) | own 512/256, UV 0.38-0.42, RGBA, 2 ramps | s3c1 0.6 % | PPP | ladder, batch (UV correspondence) |
| `mm7_m342` | clips | 8,683 | 35/20 | 1.0/10.0 | 2.2/12.8 | 4.3/13.3 | 0.68/0.38 (0.68/0.38) | own 512/256, UV 0.34-0.41, RGBA, 2 ramps | s3c2 0.7 % | PPP | keep |
| `mm7_m382` | texture | 8,613 | 25/12 | 0.7/5.0 | 3.4/7.9 | 5.4/7.0 | 0.63/0.34 (0.63/0.31) | own 512/256, UV 0.36-0.45, RGBA, 2 ramps | s3c0 0.1 % | PPP | ladder, batch (UV correspondence) |
| `mm7_m386` | attack+texture | 5,223 | 40/25 | 10.4/16.5 | 6.9/13.5 | 7.4/6.6 | 0.64/0.46 (0.67/0.41) | own 512/256, UV 0.28-0.34, 0 ramps | s3c0 3.5 % | **F**P**F** | ladder (pre-existing gate miss) |
| `mm7_m390` | texture | 6,237 | 40/25 | 6.5/14.7 | 7.4/14.2 | 8.4/8.0 | 0.68/0.37 (0.74/0.42) | own 512/256, UV 0.25-0.35, RGBA, 2 ramps | s3c3 9.4 % | **F**P**F** | ladder (pre-existing gate miss) |
| `mm7_m398` | texture | 8,187 | 25/12 | 2.0/11.2 | 3.9/11.8 | 5.5/7.2 | 0.65/0.37 (0.65/0.36) | own 512/256, UV 0.30-0.37, RGBA, 1 ramps | s3c0 2.9 % | PP**F** | ladder, batch (UV correspondence) |
| `mm7_m479` | texture | 10,325 | 40/25 | 3.4/13.6 | 6.5/14.1 | 7.0/7.6 | 0.51/0.34 (0.51/0.33) | own 512/256, UV 0.25-0.30, 0 ramps | s3c0 15.8 % | **F**P**F** | ladder (pre-existing gate miss) |
| `mm7_m426` | attack | 8,713 | 25/13 | 0.9/9.1 | 2.8/11.0 | 4.4/12.7 | 0.65/0.32 (0.64/0.32) | own 512/256, UV 0.37-0.45, RGB, 1 ramps | s3c0 1.6 % | PPP | keep |
| `mm7_m430` | clips | 6,969 | 25/12 | 0.4/10.4 | 0.9/11.0 | 1.8/6.1 | 0.71/0.29 (0.71/0.29) | own 512/256, UV 0.47-0.53, RGB, 1 ramps | s3c1 0.5 % | PPP | keep |
| `mm7_m475` | attack+clips | 6,426 | 25/12 | 1.5/12.3 | 2.5/12.8 | 7.0/11.7 | 0.72/0.41 (0.72/0.41) | own 512/256, UV 0.37-0.48, 0 ramps | s3c1 1.5 % | PPP | keep |
| `mm7_7m500` | texture | 2,198 | 25/12 | 0.2/10.6 | 1.0/11.2 | 4.8/7.3 | 0.59/0.18 (0.61/0.21) | own 512/256, UV 0.40-0.50, 0 ramps | s3c0 1.1 % | PPP | ladder, batch (UV correspondence) |
| `mm8_centaur` | texture | 9,149 | 25/12 | 1.4/6.3 | 4.4/9.6 | 5.2/8.7 | 0.53/0.14 (0.54/0.14) | own 512/256, UV 0.33-0.40, RGBA, 1 ramps | s3c0 4.7 % | PP**F** | ladder, batch (UV correspondence) |
| `mm8_m460` | clips | 7,645 | 25/12 | 1.4/10.0 | 2.2/11.1 | 3.5/10.8 | 0.67/0.43 (0.67/0.43) | own 512/256, UV 0.37-0.45, RGB, 1 ramps | s3c0 0.7 % | PPP | keep |
| `mm8_m408` | texture | 7,122 | 30/16 | 1.4/9.6 | 4.5/11.6 | 11.3/10.3 | 0.72/0.48 (0.73/0.49) | own 512/256, UV 0.33-0.43, RGBA, 4 ramps | s3c0 0.8 % | PPP | ladder, batch (UV correspondence) |
| `mm8_m548` | texture | 6,132 | 25/15 | 1.7/5.5 | 3.7/10.0 | 7.4/10.8 | 0.17/0.02 (0.18/0.03) | LOD0 atlas, 0 ramps | s3c2 14.2 % | P**F****F** | keep (atlas far LOD passes) |
| `mm8_wolf` | texture | 7,809 | 25/12 | 1.1/9.5 | 2.6/10.8 | 5.1/11.1 | 0.32/0.11 (0.27/0.08) | LOD0 atlas, RGBA, 2 ramps | s3c2 7.4 % | P**F****F** | keep (atlas far LOD passes) |
| `mm8_m536` | attack | 8,000 | 25/12 | 3.5/22.2 | 6.2/22.7 | 0.8/2.9 | 0.22/0.18 (0.22/0.18) | LOD0 atlas, RGBA, 1 ramps | s3c1 0.9 % | **F****F**P | keep (pre-existing, effect body) |
| `mm8_m604` | texture | 8,332 | 25/12 | 1.5/9.4 | 3.5/11.3 | 6.4/9.7 | 0.54/0.31 (0.58/0.32) | own 512/256, UV 0.34-0.43, RGBA, 2 ramps | s3c0 6.9 % | PP**F** | ladder, batch (UV correspondence) |
| `mm8_m564` | texture | 7,042 | 25/12 | 1.1/13.9 | 3.0/14.3 | 4.7/9.4 | 0.56/0.32 (0.59/0.33) | own 512/256, UV 0.38-0.43, RGBA, 4 ramps | s3c2 0.8 % | PPP | ladder, batch (UV correspondence) |
| `mm8_m608` | attack+texture | 5,123 | 25/12 | 1.5/10.8 | 2.7/8.8 | 5.3/9.8 | 0.23/0.11 (0.17/0.06) | LOD0 atlas, RGBA, 1 ramps | s3c2 14.0 % | P**F****F** | ladder (atlas far LOD off LOD0 colours) |
| `mm8_lizardman_peasant` | rebuild+texture | 8,245 | 30/16 | 3.7/17.2 | 5.1/17.0 | 9.9/14.1 | 0.41/0.16 (0.40/0.16) | own 512/256, UV 0.31-0.39, RGBA, 2 ramps | s3c2 2.1 % | PP**F** | ladder, batch (UV correspondence) |
| `mm8_m588` | texture | 4,928 | 40/25 | 1.9/15.8 | 4.9/18.1 | 3.8/11.7 | 0.18/0.06 (0.16/0.04) | own 512/256, UV 0.25-0.34, RGBA, 1 ramps | s3c0 20.8 % | PP**F** | ladder, batch (UV correspondence) |
| `mm8_m484` | clips+texture | 6,751 | 25/12 | 0.9/6.4 | 3.1/9.7 | 5.6/10.0 | 0.50/0.21 (0.49/0.20) | own 512/256, UV 0.37-0.43, RGBA, 1 ramps | s3c2 5.9 % | PP**F** | ladder, batch (UV correspondence) |
| `mm8_m472` | clips+texture | 11,013 | 25/12 | 0.8/9.7 | 1.9/11.1 | 3.1/7.8 | 0.72/0.39 (0.74/0.42) | own 512/256, UV 0.42-0.48, RGBA, 1 ramps | s3c0 0.4 % | PPP | ladder, batch (UV correspondence) |
| `mm8_m600` | attack | 8,792 | 50/40 | 0.9/7.0 | 1.9/7.3 | 3.9/8.8 | 0.39/0.24 (0.39/0.24) | LOD0 atlas, RGBA, 2 ramps | s3c0 3.1 % | P**F****F** | keep (atlas far LOD passes) |
| `mm8_m540` | attack+clips+texture | 10,060 | 48/29 | 1.3/6.6 | 2.9/10.0 | 6.3/10.4 | 0.57/0.32 (0.52/0.27) | LOD0 atlas, RGBA, 1 ramps | s3c1 5.3 % | P**F****F** | keep (atlas far LOD passes) |
| `mm8_m436` | texture | 10,527 | 25/12 | 1.4/5.8 | 3.3/7.1 | 7.5/9.0 | 0.41/0.21 (0.42/0.20) | own 512/256, UV 0.35-0.42, RGBA, 1 ramps | s3c0 3.4 % | PP**F** | ladder, batch (UV correspondence) |
| `mm8_m440` | texture | 12,678 | 40/28 | 0.4/5.1 | 1.5/6.5 | 2.5/7.0 | 0.60/0.35 (0.53/0.29) | LOD0 atlas, RGBA, 1 ramps | s3c0 6.6 % | P**F****F** | keep (atlas far LOD passes) |
| `mm8_m572` | texture | 8,919 | 40/25 | 6.5/17.2 | 9.6/17.8 | 14.6/14.1 | 0.64/0.40 (0.64/0.39) | own 512/256, UV 0.22-0.31, RGBA, 3 ramps | s3c3 21.2 % | **F**P**F** | ladder (pre-existing gate miss) |
| `mm8_m416` | attack | 8,160 | 25/12 | 0.8/5.9 | 2.8/8.2 | 4.6/8.5 | 0.45/0.35 (0.45/0.35) | LOD0 atlas, RGBA, 1 ramps | s3c2 1.7 % | P**F**P | keep (atlas far LOD passes) |
| `mm8_m584` | texture | 11,430 | 55/44 | 0.3/1.8 | 0.7/2.6 | 1.5/3.7 | 0.82/0.63 (0.78/0.59) | LOD0 atlas, RGBA, 1 ramps | s3c0 0.1 % | P**F**P | keep (atlas far LOD passes) |
| `mm8_m568` | attack | 9,490 | 25/12 | 0.6/7.5 | 1.5/7.8 | 3.0/4.9 | 0.88/0.72 (0.88/0.72) | own 512/256, UV 0.39-0.46, RGB, 1 ramps | s3c0 0.2 % | PPP | keep |
| `mm8_m524` | attack+texture | 6,156 | 25/12 | 0.8/6.9 | 1.7/7.0 | 3.0/3.9 | 0.87/0.62 (0.87/0.59) | own 512/256, UV 0.42-0.49, RGBA, 2 ramps | s3c0 0.4 % | PPP | ladder, batch (UV correspondence) |
| `mm8_m628` | texture | 10,243 | 35/20 | 2.8/11.5 | 5.0/11.4 | 7.9/8.0 | 0.69/0.44 (0.70/0.45) | own 512/256, UV 0.21-0.34, RGBA, 1 ramps | s3c0 2.3 % | PP**F** | ladder, batch (UV correspondence) |
| `mm8_m516` | texture | 7,584 | 25/12 | 1.4/10.9 | 3.2/9.5 | 3.7/8.3 | 0.53/0.42 (0.54/0.37) | LOD0 atlas, RGBA, 4 ramps | s3c0 0.2 % | P**F**P | ladder (atlas far LOD off LOD0 colours) |
| `mm8_m552` | texture | 6,867 | 40/25 | 4.7/13.8 | 6.5/14.0 | 6.5/5.9 | 0.67/0.46 (0.69/0.48) | own 512/256, UV 0.26-0.34, RGBA, 2 ramps | s3c3 12.2 % | **F**P**F** | ladder (pre-existing gate miss) |
| `mm8_m576` | texture | 6,818 | 25/12 | 2.3/9.4 | 4.1/9.7 | 4.7/6.9 | 0.56/0.32 (0.58/0.33) | own 512/256, UV 0.37-0.43, RGBA, 2 ramps | s3c0 1.5 % | PPP | ladder, batch (UV correspondence) |
| `mm8_m476` | clips+texture | 8,802 | 25/12 | 0.8/5.9 | 2.1/7.9 | 4.1/6.9 | 0.55/0.34 (0.57/0.34) | own 512/256, UV 0.36-0.43, RGBA, 1 ramps | s3c2 1.2 % | PPP | ladder, batch (UV correspondence) |
| `mm8_m480` | clips | 7,598 | 25/12 | 0.6/6.8 | 3.4/9.3 | 6.6/9.0 | 0.48/0.23 (0.48/0.23) | own 512/256, UV 0.34-0.42, RGBA, 4 ramps | s3c0 3.5 % | PP**F** | keep |
| `mm8_m544` | clips | 6,906 | 35/20 | 1.5/6.8 | 4.8/8.3 | 7.0/9.5 | 0.69/0.31 (0.69/0.31) | own 512/256, UV 0.32-0.41, RGB, 2 ramps | s3c1 2.8 % | PP**F** | keep |
| `mm8_m464` | clips | 8,433 | 25/12 | 0.7/8.0 | 1.8/9.0 | 4.8/9.9 | 0.43/0.20 (0.43/0.20) | LOD0 atlas, RGBA, 2 ramps | s3c0 0.4 % | P**F**P | keep (atlas far LOD passes) |
| `mm8_m556` | texture | 8,187 | 25/12 | 0.6/12.5 | 2.5/11.8 | 4.2/5.2 | 0.88/0.72 (0.90/0.69) | own 512/256, UV 0.36-0.45, RGBA, 1 ramps | s3c0 0.2 % | PPP | ladder, batch (UV correspondence) |
| `mm8_m500` | attack | 5,790 | 25/12 | 1.2/12.2 | 4.2/13.6 | 6.1/10.3 | 0.73/0.39 (0.73/0.39) | own 512/256, UV 0.41-0.47, RGBA, 3 ramps | s3c0 2.5 % | PP**F** | keep |
| `mm8_m444` | clips | 7,050 | 25/12 | 0.7/5.8 | 2.5/7.3 | 4.5/7.7 | 0.64/0.38 (0.64/0.38) | own 512/256, UV 0.37-0.45, RGB, 1 ramps | s3c0 0.3 % | PPP | keep |
| `mm8_ratman` | texture | 7,831 | 25/12 | 1.2/5.5 | 5.1/9.6 | 11.3/12.3 | 0.45/0.26 (0.46/0.23) | own 512/256, UV 0.34-0.43, RGBA, 1 ramps | s3c0 2.7 % | PP**F** | ladder, batch (UV correspondence) |
| `mm8_m560` | texture | 9,071 | 25/12 | 1.7/6.7 | 5.5/6.8 | 6.0/3.8 | 0.77/0.62 (0.79/0.59) | own 512/256, UV 0.28-0.34, RGBA, 2 ramps | s3c1 12.2 % | PP**F** | ladder, batch (UV correspondence) |
