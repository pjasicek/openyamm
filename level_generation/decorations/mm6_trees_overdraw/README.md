# MM6 tree leaf overdraw pass (2026-10-16)

## Shared pipeline (read first; two builders share this folder since 2026-10-16)

- **Ownership:**
  - builder 1: tree01, tree10, tree17, tree02, tree18, tree05, tree06, tree06a;
  - builder 2: tree04, tree15, tree25, tree13, swptree1, swptree2, tree03, tree19, tree14, tree07, swptree3.
  - Each builder writes only `species/<id>.json`, `work/<id>/`, `review/<id>/` and the log files of its own trees.
- **Shared files:**
  - everything in `scripts/` (`common.py` DEFAULTS, `prep.py`, `shell.py`, `select_cards.py`, `tune.py`,
    `compose.py`, `gate.py`, `render.py`, `overdraw.py`, `glb.py`, `install.py`, `summary.py`) and `build.sh`;
  - do not change them in incompatible ways; when a change is needed, note it under "Script changes" below;
  - per-tree differences go in `species/<id>.json` (merged over `DEFAULTS`); `sid` = the MM6 pipeline species.
- **One tree end to end:**
  1. `echo '{"sid": "6tree04"}' > species/tree04.json`;
  2. `./build.sh tree04 > work/tree04.log 2>&1`. This runs prep, shell, select, tune, compose, gate and winding;
     about 3-6 min, at most one Blender process at a time;
  3. Read `review/tree04/before_after.png`;
  4. `python3 scripts/install.py tree04 [--accept-gate]`;
  5. `python3 scripts/summary.py tree04` gives the README row.
- **Pre-pass originals:**
  - `work/<id>/installed.glb` is copied by `prep.py` from `assets_source/engine/models/` before the first install.
    Once this pass has installed a tree, it is copied from `backup_pre_overdraw/`, never from a shelled model.
  - `install.py` copies the original to `backup_pre_overdraw/<glb>` on the first install. It refuses when the
    installed source is neither the original nor this pass's last install (`work/<id>/installed_export.sha256`),
    so changes by other sessions are not overwritten.
- **Gates** (`gate.py`; all against the pre-pass original, same Eevee renderer and framing):
  - coverage within 3 % and mean colour within 3/255 per LOD;
  - neighbouring LOD steps (eye view) within colour max(4, original + 1) and coverage max(5 %, original + 0.5 %);
  - layers from `overdraw.py`, targets about 2.5-3 at LOD0/LOD1 and about 2 at LOD2;
  - triangles not above the original;
  - **black patches:** in the `up` view (2 m above the ground, 1.8 m from the trunk axis, pitched 60° up) and the
    `low3q` view (low three-quarter), the share of opaque pixels below luminance 12 at most the original's + 0.5 %.
    Bark close-ups can trip this on thick or low-crowned trees (tree10); check the sheet.
  - `check_winding.py` must report 0 inverted closed parts. The shell is open (carved sky gaps, open underside),
    so it is not counted as a closed part.
- **Not allowed:** editing the manifests or the engine, `cook_models.py`, git, Android cooks, or copying into
  `assets_dev` / `assets_source` (install only with `install.py` → `tools/install_model.py`).

### Script changes

(add a dated line here for any change to a shared script)
- 2026-10-16 (builder 1): `common.py` DEFAULTS `cards.dark_bias` [0.5, 0.5, 0.0]. LOD2 keeps no dark bias: removing
  its darker clump cards first brightened LOD2 at eye level, so the LOD2 → impostor step grew (tree05).


User-approved quality and performance pass for the MM6 living trees. Alpha-tested leaf cards stacked 4–12 layers deep
(mean card fragments per covered pixel), so dense forests (New Sorpigal: 1035 × tree01) spent about half the GPU
frame on leaves. Targets: about 2.5–3 layers at LOD0/LOD1 and about 2 at LOD2, counted without a depth test, the
look unchanged. The engine already draws every opaque, non-billboard primitive of a model with alpha-tested leaves
into the depth prepass first, nearest batch first (`engine/render/MODEL_RENDERING.md`, "Foliage depth order"), so an
opaque crown shell rejects the cards behind it before their alpha test.

Method from the MM8 pass (`../mm8_3d/trees_other/README.md` "Leaf overdraw pass", `../mm8_3d/trees_broadleaf/`):
an opaque low-poly shell just inside the leaf cards, fewer cards. The MM6 trees are **not rebuilt**: the installed
sources (`assets_source/engine/models/mm6_deco_*.glb`) carry later changes that a rebuild from the species
configs would lose (the `mm6_reduce_pilot` LOD0 bark reduction on 18 models, the 2026-10-16 bark UV fix written in
place, the tree06a fruit winding fix). So this pass edits the installed GLB's foliage only: the leaf primitives of
LOD0–LOD2 keep a subset of their own cards (vertex data copied, only the darkest COLOR_0 floored), each LOD gains
a Shell primitive, and bark, moss, fruit, the impostor and every texture stay byte-identical. The bark UV fix needed
no work here: the bark primitives are untouched, and the trunk close-ups on every sheet show the furrows running
along the limbs. The MM6 pipeline
(`../mm6_new_sorpigal_3d/trees/`) is read only: its `work/<id>/clumps.json` and `groups.json` give the clump layout.

## Pipeline

```bash
./build.sh <id>               # e.g. ./build.sh tree01: work/<id>/mm6_deco_<id>.glb + review/<id>/before_after.png
python3 scripts/install.py <id> [--accept-gate]   # after looking at the sheet (runs tools/install_model.py --engine)
python3 scripts/summary.py <id> ...               # README result rows from work/<id>/gate.json
```

`species/<id>.json` holds what differs from `DEFAULTS` in `scripts/common.py` (`sid` = the MM6 pipeline species;
`base` = reuse another tree's shells and card choice, for the food tree). Two builds may run at once (each runs at
most one Blender process at a time). Do not edit `build.sh` while a build runs.

1. `scripts/prep.py`: copies the pre-pass source to `work/<id>/installed.glb` (from `backup_pre_overdraw/` once this
   pass has installed the tree; never a shelled model). That file is the baseline of every gate. Writes the card
   table `work/<id>/cards.npz`: every card's corners, its clump (LOD0/LOD1 matched to `clumps.json` by centre,
   within 2.5 cm; LOD2 = `groups.json` × 4 cards), its seen colour (mean COLOR_0 × its texels' linear albedo) and its
   mean COLOR_0.
2. `scripts/shell.py` (Blender, for its BVH): per LOD a **star-shaped crown shell**, the MM8 broadleaf construction.
   - Geometry: a sphere grid around the crown centre (`shell.grid`: 16×10 / 14×8 / 10×6 = 288 / 196 / 100
     triangles). Each vertex sits at the far crossing of the union of the clump ellipsoids, shrunk to `shell.scale`
     (0.8) × the clump radius, with axes from the spread of the clump's cards. It is capped at (1 − `shell.inset`
     0.35 − `shell.inset_down` 0.25 × the downward part of the direction) × the card envelope in that direction
     (85th percentile of the card corners within 25°), then smoothed once.
   - Colour (COLOR_0): the seen colour of the nearby cards that it replaces, × a sky term through the remaining
     cards (`shell.ao` 0.4), × a per-vertex value jitter (`shell.jitter` 0.35).
   - Shading normals lean up (`shell.normal_out` 0.6 of the outward normal), and the underside's normals have no
     downward component, so it never reads as a black heart.
3. `scripts/select_cards.py` chooses which shell triangles and which cards stay. It rasterises the LOD's cards
   (texture alpha ≥ 0.5), its bark and its shell from 48 views (8 azimuths × elevations −70, −40, 0, 20, 45, 75°).
   - **Sky gaps:** shell triangles in front of or behind an eye-level gap of the original crown (no card, no bark,
     at least `cards.carve_px` = 12 connected pixels) are removed, so real sky gaps stay open.
   - **Open underside** (LOD0, LOD1): triangles facing down (normal y < −0.35) are removed, and so are lower ones
     facing the trunk. From under the tree one then sees the kept cards and the sky, not a flat ceiling.
   - **Reverse greedy:** the card whose removal uncovers the least goes first, until the mean layers over those
     views reach `cards.layers` (2.7 / 2.7 / 2.4). A pixel is worth 1 once a card covers it in front of the opaque
     depth (2 outside the opaque silhouette, the crown's leafy edge) plus 0.15 for a second card. The views are
     weighted eye level 1, 45° 0.7, from below 0.6, top 0.3. A card's cost is scaled by (COLOR_0 brightness /
     median)^0.5, so deep, dark cards go first: once the cards around them are gone they would show as black.
     Cards inside or behind the shell from every view cost nothing. The kept cards are the ones that cover the
     shell's gaps and the silhouette. `cards.grow` (LOD2 1.08) scales kept cards about their centres.
4. `scripts/tune.py`: one grey factor per LOD (`shell.value`, 0.3–3, secant method), fitted so that each LOD's mean
   colour matches the original. The target is half the mean over the three gate views and half the eye view
   (LOD2: three quarters the eye view, since the impostor step is judged there). Per-channel factors were tried
   and dropped: where little shell shows they drifted the hue toward blue-grey.
5. `scripts/compose.py`: writes the GLB.
   - Leaf primitives keep only the selected cards, with their vertex data copied as they are, except that leaf
     COLOR_0 is floored at 0.15 on the max channel, hue kept (`cards.vc_floor`). The engine's leaf shader adds no
     sky reflection on alpha-tested leaves, so deep cards read darker in game than in Blender.
   - Material `Shell`: opaque, single-sided, roughness 0.95, metallic 0, `openyamm_wind` = the leaves' value (0.12,
     so it sways with the cards), `openyamm_specular` 0.05.
   - Shell base colour is **the model's own impostor texture**, already in the GLB, so no new image. Through a gap
     it reads as foliage deeper in the crown, not as a smooth wash.
     - UVs use the impostor quad's affine map, with x replaced by the arc around the crown folded every quarter
       turn. The lower half is folded onto the lit upper crown, shrunk 0.85 toward the centre.
     - Vertices that land on transparent impostor texels move to the nearest opaque texel.
     - COLOR_0 = the shell colour ÷ the texture's mean, floored at 0.8 × the median, × `shell.value`.
   - Normal map: the flat MM8 shell normal map (same bytes as `mm8_deco_tree14.glb`, stored once by the cook).
   - Cards on the LOD0 bounds are always kept and never grown, so the LOD0 bounds (which the engine scales by) stay
     exact.
6. `scripts/gate.py` renders with `scripts/render.py`. Like the MM6 pipeline's `render_review.py`, it uses Eevee
   without shadow maps and culls back faces on single-sided materials, as the engine does. It then runs
   `scripts/overdraw.py`. `build.sh` ends with `../mm8_3d/animated/scripts/check_winding.py`.

Gates compare the original (pre-pass) model with the new one, same renderer and framing (LOD0 bounds frame every
LOD):
- coverage within 3 % and mean colour within 3/255 per LOD (mean over eye, three-quarter and side views);
- neighbouring LOD steps (eye view) no worse than colour max(4, original + 1)/255 and coverage max(5 %, original);
- card layers from `scripts/overdraw.py` (copied from `../mm8_3d/trees_other/scripts/`; front, three-quarter and
  side, LOD0–LOD2, "all" without a depth test and "front" in front of the opaque depth);
- triangles no higher than the original;
- **black patches** (coordinator, after black crown hearts on the MM8 palms): from 2 m above the ground, 1.8 m from
  the trunk axis, pitched 60° up (`up`), and from a low three-quarter view (`low3q`), the share of opaque pixels
  darker than luminance 12 may grow by at most 0.5 % over the original.

"Opaque seen" is the share of the crown silhouette where bark or shell is the front surface (no card in front).

Review sheet per tree, `review/<id>/before_after.png`, BEFORE (original) above AFTER:
- row 1: LOD0 eye, three-quarter and side; LOD1; LOD2; the impostor;
- row 2: crown close-up, under the crown, trunk close-up, up 60° by the trunk, low three-quarter;
- heat maps of all card layers per LOD (blue 1 → red 8+, grey = bark or shell with no card).

## Results (builder 1, installed 2026-10-16)

Layers are the mean card fragments per covered pixel over the front, three-quarter and side views, without a depth
test; in brackets, those in front of the opaque depth. The columns run original → new. Coverage and colour (max
channel, /255) are the deltas against the original, mean over three views. Triangles are LOD0 / LOD1 / LOD2 /
impostor, with the shell triangles in brackets. Sheets: `review/<id>/before_after.png`.

| Id | Layers LOD0 | LOD1 | LOD2 | Triangles before | after (shell) | Coverage LOD0/1/2 | Colour LOD0/1/2 |
|---|---|---|---|---|---|---|---|
| tree01 | 5.44 (5.23) -> 2.89 (2.67) | 3.71 (3.63) -> 3.06 (2.86) | 5.42 (5.38) -> 2.33 (2.20) | 7209 / 2980 / 860 / 4 | 4064 (143) / 2616 (86) / 508 (100) / 4 | -1.8 % / -0.4 % / -0.8 % | 0.5 / 0.3 / 1.0 |
| tree10 | 5.23 (4.99) -> 2.58 (2.37) | 3.53 (3.44) -> 2.62 (2.42) | 4.52 (4.49) -> 2.12 (2.00) | 7167 / 2980 / 900 / 4 | 3718 (177) / 2369 (117) / 518 (100) / 4 | -2.0 % / -0.6 % / +1.0 % | 1.4 / 1.2 / 1.9 |
| tree17 | 6.83 (6.76) -> 2.93 (2.74) | 4.99 (4.96) -> 3.01 (2.79) | 5.13 (5.09) -> 2.11 (1.96) | 7302 / 2978 / 584 / 2 | 3554 (152) / 1971 (111) / 384 (100) / 2 | -1.9 % / -0.9 % / +0.1 % | 0.5 / 0.6 / 1.2 |
| tree02 | 4.25 (4.17) -> 2.64 (2.48) | 2.92 (2.90) -> 2.70 (2.53) | 4.08 (4.07) -> 2.49 (2.31) | 7147 / 2956 / 988 / 4 | 4527 (146) / 2834 (82) / 576 (100) / 4 | -1.8 % / +0.1 % / -0.0 % | 0.6 / 0.5 / 2.2 |
| tree18 | 3.65 (3.56) -> 2.55 (2.41) | 3.20 (3.18) -> 2.78 (2.65) | 4.29 (4.26) -> 2.58 (2.41) | 5542 / 2380 / 888 / 4 | 3951 (161) / 2063 (61) / 502 (94) / 4 | -1.6 % / -0.3 % / -1.2 % | 0.6 / 0.4 / 1.5 |
| tree05 | 5.13 (5.05) -> 2.73 (2.55) | 3.81 (3.79) -> 2.78 (2.62) | 4.63 (4.60) -> 2.40 (2.22) | 7461 / 2980 / 852 / 4 | 4379 (162) / 2312 (92) / 546 (94) / 4 | -2.0 % / -0.6 % / +1.1 % | 0.7 / 0.6 / 1.1 |
| tree06 | 4.52 (4.47) -> 2.84 (2.62) | 3.45 (3.43) -> 3.01 (2.76) | 4.24 (4.23) -> 2.21 (2.11) | 6871 / 2730 / 816 / 4 | 4678 (123) / 2489 (79) / 552 (100) / 4 | -1.5 % / -0.3 % / +1.1 % | 0.9 / 0.9 / 1.1 |
| tree06a | 4.52 (4.46) -> 2.84 (2.61) | 3.45 (3.43) -> 3.01 (2.76) | 4.24 (4.23) -> 2.21 (2.11) | 7415 / 2922 / 880 / 4 | 5222 (123) / 2681 (79) / 616 (100) / 4 | -1.5 % / -0.3 % / +1.1 % | 0.9 / 0.9 / 1.1 |

- All eight report 0 inverted closed parts and keep their LOD0 bounds byte for byte.
- tree06 and tree06a share the shells and card choice and keep identical LOD0 bounds:
  [-2.97247, -0.02751, -2.93381] .. [2.89729, 7.07151, 2.79686] before and after.
- No binding height or `lod_pixels` change is needed.
- Installed sources are under `assets_source/engine/models/mm6_deco_<id>.glb`; the originals are in
  `backup_pre_overdraw/`.
- These models changed, so outdoor lighting bakes that use them are stale (`tools/lighting/stale_bakes.py`).

Black-patch views, dark share original → new (luminance < 12): tree01 up 0.08 → 0.11 %; tree10 up 0.16 → 1.60 %
(bark, see below); all the others are 0 → 0 %, up and low three-quarter.

## Results (builder 2, installed 2026-10-16)

Same columns as above, plus the black-patch dark share (`up` / `low3q`, original → new) and the settings that differ
from `DEFAULTS` (`species/<id>.json`; the shell factor comes from `tune.py` unless noted). All report 0 inverted
closed parts and keep their LOD0 bounds. Sheets: `review/<id>/before_after.png`.

**Under-crown carve (coordinator, after tree03's flat shell slab across a sky gap in the `up` view).**
`scripts/b2_undercarve.py <id>` runs after `select_cards.py`: from a ring of cameras under the crown (heights 1.2 /
2.0 / 2.8 m, radii 0.9 / 1.8 / 2.7 m from the trunk axis, 16 azimuths), rays go to every front-facing LOD0/LOD1 shell
face (centroid and three points halfway to its corners). A face goes when a ray reaches it past the kept cards, bark
and moss (alpha-tested) and the same ray through the original model meets nothing: the shell would fill a sky gap
of the original crown there. Faces that stand in for original cards stay. `B2_READD=<m>` re-keeps the removed cards
within that distance of a removed face, which gives back eye-level coverage (tree03, tree07, tree25: 0.2 m). Every
builder-2 tree carries this carve. The earlier installs of tree04, tree25, tree15, tree13, tree19 and tree03 were
redone with it and reinstalled.

Builder 2 scripts (shared scripts unchanged): `scripts/b2_finish.sh <id>` = compose + gate + winding with the
species' shell factor (no tune); `scripts/b2_rebuild.sh <id>` = shell + select + under-crown carve + finish;
`scripts/b2_undercarve.py <id>` (keeps `work/<id>/shell_preunder.npz` and starts from it on reruns); `scripts/b2_compose.py <id>` = compose.py, but a LOD whose shell was carved away completely gets no Shell primitive (b2_finish.sh uses it). To redo a
builder-2 tree: `./build.sh <id>` once (prep, tune), then `rm work/<id>/shell_preunder.npz`, `[B2_READD=0.2]
python3 scripts/b2_undercarve.py <id>`, `scripts/b2_finish.sh <id>`, look at the sheet, `python3 scripts/install.py <id>`.

| Id | Layers LOD0 | LOD1 | LOD2 | Triangles before | after (shell) | Coverage LOD0/1/2 | Colour LOD0/1/2 | Dark up / low3q | Settings |
|---|---|---|---|---|---|---|---|---|---|
| tree04 | 6.48 (6.27) -> 2.99 (2.74) | 4.96 (4.94) -> 3.10 (2.92) | 5.64 (5.61) -> 2.62 (2.29) | 6955 / 2980 / 972 / 4 | 3590 (123) / 2001 (75) / 622 (100) / 4 | -2.5 % / -1.6 % / +0.1 % | 0.9 / 1.1 / 1.0 | 0 → 0 / 0 → 0 % | LOD2 layers 2.6, grow 1.1 (at 2.4 the LOD1→2 coverage step was -5.2 %); carve removed 39 / 33 shell faces |
| tree25 | 4.49 (4.26) -> 2.97 (2.80) | 3.63 (3.51) -> 2.82 (2.73) | 3.61 (3.50) -> 2.35 (2.16) | 5968 / 2380 / 884 / 4 | 4331 (17) / 1901 (3) / 522 (100) / 4 | -1.9 % / -1.6 % / +0.4 % | 0.7 / 0.6 / 1.7 | 0 → 0 / 0 → 0 % | layers 2.8 / 2.7 / 2.6, fringe 3 / 3 / 2; the carve removes 80 of 97 / 32 of 35 faces (the crown sits high and is open from below) and re-keeps the cards within 0.2 m (without: LOD0 coverage -3.9 %); the `up` view sees only sky under the tall trunk, in both models |
| tree15 | 4.90 (4.89) -> 2.71 (2.60) | 3.51 (3.50) -> 2.78 (2.68) | 4.33 (4.33) -> 2.39 (2.22) | 7957 / 2976 / 796 / 4 | 4920 (93) / 2436 (50) / 514 (84) / 4 | -2.5 % / -1.0 % / +0.4 % | 1.5 / 0.9 / 0.8 | 0 → 0 / 0 → 0 % | LOD2 layers 2.6; LOD2 shell factor 0.22 by hand (at tune.py's 0.3 floor the LOD2 → impostor step was 8.6 against the 8.3 limit); carve 57 / 44. The eye-level see-through hole in the crown centre is smaller at LOD0/LOD1 and closed at LOD2, as on the impostor |
| tree13 | 3.94 (3.71) -> 2.64 (2.44) | 2.88 (2.85) -> 2.73 (2.64) | 4.05 (4.06) -> 2.28 (2.17) | 7961 / 2976 / 986 / 4 | 5711 (82) / 2848 (20) / 598 (86) / 4 | -1.8 % / -0.1 % / -0.2 % | 0.6 / 0.6 / 1.2 | 0.00 → 0.01 / 0 → 0 % | LOD2 layers 2.6 (at 2.4 the LOD1→2 coverage step was -5.2 %); carve 52 / 17. LOD1 was already at 2.9 layers, so it only loses 6 % of its cards |
| tree03 | 7.47 (7.47) -> 3.04 (2.92) | 5.59 (5.59) -> 3.09 (3.01) | 5.10 (5.10) -> 2.41 (2.23) | 5955 / 2378 / 572 / 4 | 2950 (79) / 1420 (30) / 420 (100) / 4 | -2.9 % / -2.1 % / -1.3 % | 2.2 / 1.4 / 1.4 | 0 → 0 / 0 → 0 % | LOD2 layers 2.6, grow 1.05, fringe 3 / 2 / 2; shell `inset_down` 0.5, `open_bottom` -0.15 (LOD0/LOD1); LOD2 shell factor 0.3 by hand (tune gave 0.439: LOD2 → impostor step 28.0 against 27.4; the original step is already 26.4). Carve 60 / 69 faces, re-keep 0.2 m: the `up` view's flat shell slab is gone |
| tree19 | 12.08 (11.94) -> 3.23 (2.97) | 8.30 (8.27) -> 3.34 (3.04) | 5.65 (5.63) -> 2.56 (2.23) | 5957 / 2380 / 476 / 4 | 2143 (132) / 1208 (74) / 408 (100) / 4 | -2.7 % / -2.0 % / -1.2 % | 0.7 / 0.7 / 0.8 | 0 → 0 / 0 → 0 % | LOD2 layers 2.6, grow 1.04 (1.08: LOD2 → impostor coverage step -6.9 %; 1.0: LOD2 coverage -3.1 %); carve 35 / 43 |
| tree07 | 6.67 (6.30) -> 3.30 (3.02) | 4.83 (4.60) -> 3.40 (3.13) | 5.29 (5.24) -> 2.61 (2.36) | 5954 / 2380 / 876 / 4 | 3674 (78) / 1861 (41) / 586 (100) / 4 | -2.7 % / -1.5 % / +0.1 % | 1.9 / 1.8 / 0.4 | 0 → 0 / 0 → 0 % | LOD2 layers 2.6, fringe 2.5 / 2 / 2; carve 74 / 56 faces, re-keep 0.2 m (without: LOD0 coverage -3.3 %) |
| tree14 | 4.26 (4.18) -> 2.95 (2.85) | 3.30 (3.29) -> 3.19 (3.13) | 3.84 (3.84) -> 2.51 (2.41) | 7961 / 2980 / 988 / 4 | 5881 (62) / 2897 (9) / 620 (56) / 4 | -2.0 % / +0.1 % / +0.6 % | 1.3 / 0.4 / 1.3 | 0 → 0 / 0 → 0 % | LOD2 layers 2.6; carve 83 / 33. LOD1 was already at 3.3 layers and keeps 97 % of its cards; LOD2 loses the original's eye-level hole, as on the impostor |
| swptree1 | 10.13 (9.84) -> 3.80 (3.59) | 5.44 (5.34) -> 3.60 (3.50) | 4.66 (4.61) -> 3.22 (3.10) | 6955 / 2680 / 862 / 4 | 3415 (16) / 1947 (3) / 695 (15) / 4 | -2.9 % / -1.9 % / +2.5 % | 0.4 / 0.8 / 0.5 | 0 → 0 / 0 → 0 % | swamp, tiered pads: layers 3.0 / 3.0 / 3.3, fringe 3, `dark_bias` 0, LOD2 grow 1.08. The star shell is carved to almost nothing over the gaps between the pads, so this is mostly a card cut; layers include the untouched moss (600 / 360 / 210 triangles). **Installed with `--accept-gate`:** LOD2 → impostor colour step 12.7 against 12.4 (original 11.4): LOD2 reads ~1.3/255 brighter at eye level whatever cards go (LOD2 layers 2.4–3.0 gave 13.0–15.2). A surface-nets shell (`shell.mode` nets) was tried and showed flat shell shards across the pads, not used |
| swptree2 | 4.71 (4.55) -> 3.25 (3.11) | 2.75 (2.69) -> 2.75 (2.69) | 2.90 (2.87) -> 2.38 (2.27) | 7962 / 2970 / 984 / 4 | 5969 (9) / 2970 / 934 (20) / 4 | -1.3 % / +0.0 % / -2.0 % | 0.1 / 0.0 / 1.4 | 0 → 0 / 0 → 0 % | swamp: layers 3.0 / 3.0 / 2.8, fringe 3, LOD2 `dark_bias` 1.0, LOD2 grow 1.0; LOD2 shell factor 0.15 by hand. LOD1 was already at 2.75 layers and its shell was carved away completely, so LOD1 is unchanged (`scripts/b2_compose.py` writes no empty Shell primitive) |
| swptree3 | 8.79 (8.24) -> 3.50 (3.16) | 6.77 (6.45) -> 3.77 (3.42) | 4.91 (4.75) -> 2.91 (2.65) | 8956 / 3374 / 930 / 4 | 5659 (83) / 2361 (53) / 837 (95) / 4 | -1.6 % / -1.1 % / +0.9 % | 0.3 / 0.4 / 2.2 | 0 → 0 / 0 → 0 % | swamp (banyan-like, one crown): layers 3.0 / 3.0 / 2.8, fringe 3, LOD2 `dark_bias` 1.0, LOD2 grow 1.04; LOD2 shell factor 0.15 by hand (0.3: LOD2 → impostor step 16.5 against 15.8); carve 55 / 49 |

## Compromises

- **LOD2 layers** end at 2.1–2.6, not about 2. Below that, LOD2's large clump cards left bare shell patches and
  lost coverage at the silhouette. tree02, tree05 and tree18 use a LOD2 target of 2.6 for that reason.
- **LOD2 → impostor colour step:** tree10 (11.8 against the 11.6 limit) and tree05 (10.5 against 10.1) are slightly
  over, installed with `--accept-gate`. Their LOD2 is a little brighter at eye level. The shell factor is already
  at its 0.3 floor, and the removed cards were the darker ones. This renderer already gives 8–11/255 between the
  original LOD2 and its impostor; the engine's 0.3 s crossfade hides the step.
- **tree10 `up` view:** 1.6 % dark against 0.16 %. Its crown reaches low and its trunk is thick, so the camera looks
  at shaded bark through the thinned cards. There is no dark shell patch (checked on the sheet). Accepted.
- **Through gaps the shell shows the impostor texture,** magnified, so close up and from under the crown it reads
  as soft, blurred foliage rather than sharp leaves. The underside is open (LOD0, LOD1), so from below one mostly
  sees kept cards and sky. A few small dark shell shards remain at the open rim in the `under` views.
- **Real sky gaps** stay open only where the original showed them at eye level over at least 12 view pixels. Smaller
  gaps are filled by the shell, so the crowns read slightly denser in a few places (tree01 close-up).
- **Leaf COLOR_0 floor 0.15** (coordinator, for the engine's leaf shader) brightens the deepest kept cards slightly.
  The shell factor compensates in the mean.

## Resume

- State: builder 1's trees are all done and installed, with sheets reviewed: tree01, tree10, tree17, tree02,
  tree18, tree05, tree06, tree06a. Builder 2 owns the other eleven (see "Shared pipeline").
- To redo one tree: `./build.sh <id> > work/<id>.log 2>&1`, look at `review/<id>/before_after.png`, then run
  `python3 scripts/install.py <id>`. `prep.py` takes the baseline from `backup_pre_overdraw/` once a tree is
  installed. `install.py` accepts the current source only if it is the original or this pass's last install.
- No Blender or install process is left running by builder 1.
- **Builder 2 resume:** all eleven builder-2 trees are installed (with the under-crown carve) and their sheets
  reviewed: tree04, tree15, tree25, tree13, swptree1, swptree2, tree03, tree19, tree14, tree07, swptree3. swptree1 was
  installed with `--accept-gate` (LOD2 → impostor colour step 12.7 against 12.4). No builder-2 Blender or install
  process is left running. Earlier variants are kept under `work/<id>/` (`v*`, `b`, `d`, `u03`, `installed_v`) and
  `review/<id>/before_after_*.png`.
