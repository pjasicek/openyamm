# MM6–MM8 surface textures at 4×

Regenerate every BLV face texture and outdoor BModel face texture (walls, floors, ceilings, doors, building
facades, trim) as fresh 4× master artwork. The masters ship as the `x4` tier; the `x2` tier is reduced from the same
masters. Terrain, decorations/sprites, sky (including sky art on BModel faces whose name lacks "sky", listed in `SKY_TEXTURES`, e.g. MM8 `stormclds`) and the renderer-animated water/lava/oil materials are out of scope.

One orchestrator (Claude) runs the loop below. Codex does nothing but image generation, through `codex exec`
workers that `tex.py gen` launches. Everything routine is scripted in [`tex.py`](tex.py); the orchestrator only
writes material descriptions and judges the results.

## Why 4×, briefly

One texel covers one world unit. With the 60° vertical field of view, indoor walls are typically 430–480 units away,
so 2× is visibly magnified on about a quarter to a third of wall pixels at 1440p; 4× cuts that to about a tenth.
Fresh art differs most from Real-ESRGAN in the 2×–4× detail band. Imagegen returns about 1.57 MP per image, enough for
one native texture plus its wrap margin at 4×; more than 4× would need sectioned generation and is not worth it.

## What a finished master looks like

At 1:1 the master reads like a sharp photograph of the real surface at about 4 pixels per centimetre (one world
unit is roughly a centimetre): crisp chipped stone edges, pits and hairline cracks, real wood grain and knots,
mortar with depth and grit, rust and tarnish as continuous material. The native fixes only the large scale: block
and plank positions, joints, ornaments, figures, colours and brightness. All fine detail is newly invented, so it
must **not** follow the native's pixels: a mosaic of small cells, square blocks or dither under the surface means
the model traced the low-resolution original and the master is not really 4×. Contrast inside one block stays
moderate so walls read like the original from a distance; no baked lighting, glare or vignette.

## Texture families: one painted canvas, exact shared pixels

The original artists cut most wall sets from one painted canvas: the plain repeating wall, its corner and post
pieces, niches, drains and slits share large regions pixel for pixel, often at an offset (`d2wlbc` matches
`d2wlbctr` shifted 81 pixels, the niches match the plain wall shifted 128). Generated independently, every piece
gets its own stones and its own brightness, and the join is a visible step (2026-10-09 review, `6d11` corner).

- `tex.py inventory` finds these relations exactly: every 8×8 block of every native is hashed at every position
  and looked up among all other textures of the world; candidate offsets are verified pixel by pixel. A relation
  needs at least 15% identical pixels. Each entry gets `relatives` (id, dx, dy, shared fraction) and `shared_px`.
  MM6 has 705 textures with relatives (MM7 514, MM8 452); this is not a 10-pixel edge test, because shared regions
  are usually whole halves or interiors, not only borders.
- **Order:** the piece sharing most pixels (normally the plain wall) is generated first. A piece waits while a
  higher-priority relative is still in progress; `gen` skips it until that relative is accepted.
- **Reference:** the native areas identical to accepted relatives are filled with those relatives' exact 4× master
  pixels (sharp); only the rest is the blurred guide, and the prompt says to keep the sharp areas and continue them.
- **Candidate:** after calibration on the newly painted region only, the shared areas (eroded by one native pixel,
  so the generated edge meets them, but never across the tile edge: a copied edge column stays copied up to the
  boundary, where the generator would otherwise paint its boundary groove) are overwritten with the relatives' exact pixels. The copied region's outline
  is smoothed from native-pixel stair steps into a contour and faded over ~2 pixels into the generated art;
  blocky outlines showed as faint square patches on marble walls. A piece covered ≥ 99.5% by
  accepted relatives is derived directly (`<name>_d`), with no generation, unless an uncovered patch is
  larger than `MAX_DERIVED_GAP` (4) native pixels: the uncovered pixels are filled from the nearest copied ones,
  which smeared a missing 2-row plank shadow of MM6 `whend` into 8 repeated master rows that `whft` and `whcntr`
  then copied (no retry of the copiers could remove it). Such pieces are generated with the prefill instead.
- `tex.py calibrate` processes sources before the pieces that copy them and re-copies the shared pixels after
  re-gaining a piece's own region; `tex.py verify-families` confirms every family master still carries its sources'
  exact pixels. Never re-gain a family master independently: that is what reintroduces the step.
- `tex.py redo --families` reopens accepted pieces that should have been built on an accepted relative.
- A source that repeats on an axis may draw a joint straddling its own seam (half on each edge), which is harmless
  there; a piece that does not repeat on that axis would inherit the half joint as an edge line no retry can remove
  (MM7 `hep1b` -> `hep1bs`, `hwm1bs1` -> `hwm1bsw`). Prefill therefore never copies the outer `SEAM_TRIM` (2) native
  rows/columns of a source on an axis where the source repeats and the piece does not; they are generated.
- To rebuild after a bad family source, reopen the source and exactly the accepted pieces whose prefill
  `accepted_sources` contain it (transitively); `redo --families` selects every piece with an accepted relative and
  is far too broad for that.
- **Standalone pieces.** Chest, crate and cabinet panels share most pixels with framed siblings, but their faces never
  lie flat beside each other in a map, so they need no exact shared pixels. Copying from a framed face brings its
  frame and lock shadows into plain panels as outlines (MM7 `ch001*`, `ch003*`). Mark such pieces with a trailing
  ` [standalone]` in `materials` or `retry --standalone`: they are generated from their own native only (no waiting
  for, copying from or deriving from relatives), and the setting sticks to the texture. Wall pieces that abut their
  relatives keep prefill.
- **Tone step at a continuous joint.** The normal gain matches each master to its own native mean, which can leave a
  piece more saturated or brighter than the accepted neighbour it continues into (MM7 `banwiz-a` against `banwiz-b`).
  `retry --match-neighbor` (sticks to the texture) adds one per-channel linear gain in `check` so the two-native-pixel
  strip along each continuous joint matches the neighbour's strip, keeping the natives' own difference there. Copied
  relative pixels are pasted back unchanged; rolled versions skip it. It cannot fix a local hue error of one material
  (a banner's cloth): one linear gain measured on a saturated cloth colour needs extreme channel ratios and skews
  everything else, so such joints go to the user with crops.
- **Edges a roll cannot reach.** `retry --roll <axis> --drop-context` rolls an axis that has neighbours anyway; their
  margins are dropped for that version and `joint` still measures them (right-end facade pieces whose free post edge
  keeps a rim). (A margin that repeats the edge column was tried for free sides and
  broke the layout on MM7 and MM8: the model rescales the picture into the streaked margin. Don't add it back.) If the neighbour itself is off its native, redo the neighbour.
- Engraved glyph plates (`NO_FAMILY_PREFIXES`, the MM8 `alphanum*` letters and numerals) are generated
  independently: their shared blank plate meets each glyph along a curved native-pixel staircase, and copying it
  left stair-stepped glyph edges and ghost strokes of the source plate's glyph (2026-10-09).

## State

| File | Owner | Content |
| --- | --- | --- |
| `inventory.json` | `tex.py inventory` (rebuildable) | Every in-scope texture: native source/hash/size, maps, face count and world area, wrap axes from the map UVs, cutout flag, ESRGAN x4 path, exact-duplicate `canonical`, exclusions. Material text is preserved across rebuilds. |
| `ledger.jsonl` | append-only, all commands | `claim`, `candidate`, `reject`, `accept`, `release`, `reopen` events. Status is the fold of these. |
| `jobs/<id>/` | one job each | `job.json` (textures, references, materials, versions, notes), `refs/`, `prompts/`, `raw/` (unchanged returns + worker logs), `candidates/`, `results.json`, `review/` |
| `masters/<world>/<name>.png` | `tex.py accept` | Accepted 4× masters, exactly 4× the native size. |
| `config.json` | `tex.py calibrate --target` | Shared brightness target of every master: `native` (default) or `esrgan`. |
| `output/textures_x4_runs/<run>/` | `tex.py stage` | Playable hard-linked asset roots (outside git). |

Status per texture: `pending → claimed → candidate → accepted`. `reject` sends it back to `claimed` for a retry,
`release` back to `pending`, `redo` reopens accepted textures for regeneration with the current recipe (the old
master stays staged until a new one is accepted; corrections from the accepted version carry forward). Exact duplicates (identical native pixels) follow their `canonical` entry and are never
generated separately. Each `next` holds a lock while it claims, so several sessions can work at once without overlap.

## One session per world

MM6, MM7 and MM8 can each have their own orchestrator session. Each one passes its world to everything it runs:
`next --world mm7`, `gen --world mm7 --follow`, `redo --world mm7 ...`, and stage names such as `review-mm7-...`
(`stage` replaces a run of the same name). Wall families and assemblies never cross worlds. A texture that is
pixel-identical in several worlds belongs to the first world (MM6 before MM7 before MM8): only that world claims and
generates it, and the others show it with the same status.

- `gen --world W` takes that world's scheduler lock; one per world can run at once. A `gen` without `--world` serves
  every world and excludes all per-world schedulers (and the reverse).
- The schedulers' workers add up: with three sessions use about `--parallel 4` each instead of 10.
- `inventory` and `calibrate` rewrite every world's state; only one session runs them, while the others are not
  accepting. `verify-families` and `status` only read.

## The loop: "generate N more"

```sh
cd level_generation/textures_x4
python3 tex.py status
python3 tex.py next --count 200 [--world mm6] [--map 6d05.blv] [--dry-run]
```

`next` picks coherently: maps closest to completion first, then by remaining wall area, taking **all** pending
textures of a map before moving on, packed into jobs of up to 24. Each piece also brings its pending
higher-priority relatives (see Texture families), so a family's base wall is always claimed with its pieces. Finishing whole maps keeps runs reviewable and
lets one family's members share wording. Use `--map` to direct the work.

For each job:

1. **Describe materials.** Look at `jobs/<id>/review/natives.png` (labelled natives with their wrap axes). Write one
   short physical line per texture and pipe it in. Use identical wording for members of one family (`d2wlble`,
   `d2wlbctr`, `d2wlbre`) so their redraws match.

   ```sh
   python3 tex.py materials JOB <<'EOF'
   d2wlbctr: rough grey granite blocks with dark recessed mortar and faint green damp stains
   d2flor2: worn sandstone flagstones, dusty, brown-grey
   EOF
   ```

   Describe the physical surface, not the image: material, colour, wear. Do not mention the native's pixels.

2. **Generate.** `python3 tex.py gen` (one scheduler, default 10 parallel `codex exec` workers across every open
   job, or of one world's jobs with `--world`; it rescans after each completion, so materials and retries queued
   meanwhile join automatically, and a second scheduler for the same world refuses to start). Each texture is one call (45–70 s) with one
   reference built from the **original bitmap**: softened by a 1.2-pixel Gaussian blur and smoothly enlarged (Lanczos), with wrap-around margins (1/8 of the
   size, at most 16 native pixels) on each axis the map UVs repeat. Narrow trims get extra wrap context, or stacked
   copies when they do not repeat across, so every reference stays within 1:2–2:1. ESRGAN is never an input.
   For family pieces the reference also carries the accepted relatives' exact master pixels (Texture families).
   References are built when the worker starts, from the masters accepted at that moment.
   The prompt template lives in `tex.py`; exact prompts and references are saved per version.
   The blur is the key to real 4× detail: unblurred references (even smoothly enlarged) let the model trace the
   native pixels into cell mosaics. 1.2 keeps layout (layout correlation 0.93–0.98) and drops traced correlation to
   about 0.03; 2.0 already lets the model redesign locks and double lines.

3. **Check.** `python3 tex.py check JOB` builds a candidate from each raw return and flags it:
   - **budget**: the return must hold at least 4 source pixels per native pixel (never enlarged).
   - **registration**: phase correlation against the native; small drift is fixed by moving the crop inside the
     generated margin, residual drift over 1.5 native pixels is flagged.
   - **traced**: correlation of the master's finest detail with the native's pixel staircase (blocky minus smooth
     enlargement); above 0.15 the model copied the low-resolution raster instead of inventing material. Traced
     masters measure 0.23–0.48, fresh art −0.09 to 0.01, sharp geometric art on the native grid (checkerboards)
     about 0.08. The staircase form replaced a plain correlation with the blocky enlargement, which wrongly flagged
     clean checkerboards.
   - **brightness**: a per-channel linear-light gain matches the shared target's mean colour (`config.json`:
     the native by default, or the ESRGAN baseline). Every master uses the same target, so neighbouring pieces
     from different batches match. `tex.py calibrate [--target native|esrgan]` re-gains all accepted masters
     (write-and-rename, so staged runs keep their snapshot). This is the only tonal
     operation. Imagegen returns art 1.3–2× too bright almost every time, so gains of 0.45–0.8 are normal; an
     overall gain outside 0.3–2.0 (dark dungeon walls often need 0.33–0.4), or channels disagreeing (colour drift), is flagged.
   - **seams**: on wrap axes the generated trailing margin is joined onto the tile start along a minimum-error cut
     (image quilting): no blur, no repaint. Boundary contrast is compared with the native's own boundary contrast;
     dark joints that sit on the tile edge can still trip it, so confirm in the repeat column.
   - **layout**: correlation of the blurred native with the reduced candidate (moved/missing features).
   - **alpha**: cutout textures must keep the native silhouette (IoU).
   - **edge**, **rim**: outermost row/column brightness and single-line hairlines against the native (see Edge
     rims); never accept a dark edge flag or a rim flag.

4. **Review.** Look at `review/sheet_*.png` (per row: native, ESRGAN x4, candidate, 1:1 centre crop, 2×2 repeat)
   and accept by sight, not only by flags:
   - same layout, joints, ornaments and figures as the native at matched scale;
   - newly resolved material, no enlarged pixel blocks, stipple, crunchy grain or halos;
   - no baked lighting gradient, vignette or highlights;
   - invisible repeats on wrap axes; finite artwork (doors, signs, paintings) intact.

   **Raster copying is the main failure**: the 1:1 crop looks like enlarged square pixels, cells or dither instead
   of grain. The `traced` flag catches it; still look at the crop, and never accept a traced flag.

   Then:

   ```sh
   python3 tex.py accept JOB                    # all latest candidates without flags
   python3 tex.py accept JOB name name2@v1      # explicit picks (overrides flags you judged harmless, never `traced`)
   python3 tex.py reject JOB name --reason "mortar lost"
   python3 tex.py retry JOB name --note "keep the thin dark border on all four edges"
   python3 tex.py check JOB        # after the scheduler has produced the retry
   ```

   For random speckle (granite, lava, gravel) whose layout carries no meaning, retry with `--ref-blur 2.5` so the
   reference keeps only colour and borders. **Never ship ESRGAN next to generated masters** (user, 2026-10-09): every in-scope texture ends as a generated master. After two failed retries, change the strategy instead of releasing: `--roll` for edge rims (see Edge rims), a corrected material when the model draws the wrong thing, `--standalone` when a relative's flaw is copied in, `--ref-blur` for speckle. A texture released earlier is reclaimed with `next` and continues this way.

5. **Play.** After a batch of maps, stage and look in game:

   ```sh
   python3 tex.py stage review-20261009            # x4 tier: accepted masters over the ESRGAN x4 baseline
   python3 tex.py stage review-20261009-x2 --tier x2
   python3 tex.py stage baseline --baseline       # ESRGAN only, for before/after
   python3 tex.py play review-20261009 --world mm6 --map 6d01.blv
   ```

   Staging hard-links `assets_dev` (seconds, no extra disk), writes only the new tier directory, and never writes
   through a linked file. A stage is a snapshot: restage after other `assets_dev` changes (new models, maps),
   otherwise the game can fail to load assets added since. `play` passes extra `--set` options to `tools/run_game.sh`, for example a screenshot
   tour. In-game review is per map or batch, not per texture.

## Pilot (2026-10-09, job `20261009-1232-mm6-6d02-00`)

24 MM6 textures (Temple leftovers, `zddb*`, `zdtl01`): 4 workers generated 24 images in 5 min 40 s. With the
first nearest-neighbour references, 4–5 wood/floor textures copied pixel blocks; all 5 retries with the smooth
reference came back clean (d1flr slightly noisy, accepted). 24/24 accepted after one retry round. Brightness
gains were 0.45–1.0 throughout. Agent time per job is mostly the review: one natives sheet, four result sheets.

## First 200 (2026-10-09, nine MM6 jobs)

200 textures (Temple, Goblinwatch, Sewers, Castle Darkmoor halls, Silver Helm outpost) took 50 minutes of
wall time: 236 generations, of which 36 were retries, with 4 then 10 workers. All 200 accepted, mostly first try.
Failures were copied palette dither (marble, granite, lava, small stone squares; fixed by the reference blur and
`--ref-blur 2.5` for speckle), invented ornament on plain trims (fixed by "single uninterrupted strip" wording),
and a few redrawn medallions/letters (fixed by "copy exactly" notes). New art sits at native brightness, so it
reads clearly brighter than the darker ESRGAN baseline in game.

## Review feedback (2026-10-09, after the first 200)

- Corner pieces were about 2.4× brighter than the walls beside them: the imported Codex masters had been matched
  to ESRGAN brightness, the new ones to the native. Fixed with the shared `config.json` target and `calibrate`.
- Doors, posts and the skull switch did not look 4×: most of the first 200 had been generated from unblurred
  references and traced the native pixels (traced correlation median 0.13–0.19, up to 0.55; the Codex masters
  0.02). 168 were reopened with `redo` and regenerated with the 1.2 blur and the traced gate.

- Wall families (same review): corner pieces had been generated apart from the plain wall. Exact shared-region
  detection, priority order and pixel prefill were added; 50 accepted MM6 pieces were rebuilt on their relatives
  (2 derived without generation) and `verify-families` reports 0 mismatches.

## Rules

- Never accept a `traced` flag; the master would only be an enlarged original (`accept` refuses it).
- After any brightness change run `tex.py verify-families`; it must report 0 mismatched.
- Never accept an `edge … < 0.6`, a `rim` or a `line` flag: a dark rim becomes a seam line in game.
- A family base is only as good as its edges and its material wording: its pixels are copied into every relative.
  Give all members of a family the same base wording, checked against the natives (MM7: `ch001d` described as
  vertical planks spoiled three relatives). Fix a bad base with `redo --world W` on the base and every accepted
  piece that copies it, then reclaim the released relatives.
- Never generate an assembly piece on its own; review assemblies on their `*_assembly.png`.
- Never enlarge, sharpen, add noise or blend a seam. Anything a deterministic step cannot fix is regenerated.
- Masters are exactly 4× native, RGB unless the native has transparency.
- Do not hand-edit generated files or the ledger; every decision goes through `tex.py` so status stays true.
- Masters from the earlier Codex-orchestrated study (`../terrain/mm6_textures_x4`) were discarded on 2026-10-09 at
  the user's request and regenerated here; do not import them again (`import-codex-mm6` is historical).

## Assemblies: one picture split into strips

Chests (and some doors and trims) were painted as one picture per face and split into strips that abut in the
map: chest front = `ch1frle | ch1frntb | ch1frre`, lid = `ch1tplev / ch1tpbv / ch1tprev`. They share no pixels, so
family detection cannot see them; generated alone, each strip became its own framed panel (2026-10-09 review).

- `tex.py inventory` reads the map geometry: two coplanar faces with different textures sharing an edge that lies
  on both textures' borders, with rows aligned along the edge. The native pixel profile along the joint must
  continue (correlation ≥ 0.6 on structured edges; real splits measure 0.74–0.99, unrelated neighbours
  −0.4..0.2) and simple chains of 2–5 pieces become `assembly` entries (MM6 15, MM7 1, MM8 6).
- The largest piece is the head. `gen` generates the head as the whole picture (`@head` canvas = members edge to
  edge); `check` cuts the candidate into every member at exact 4× boundaries (`*_assembly.png` keeps the whole).
- A narrow assembly (or strip) that would be stacked as copies but then not fit one return gets a wider mirrored
  margin on its short axis instead, so it stays one picture at 1:2. Generating it in sections, or as separate pieces
  joined through neighbour context, misaligned plank rows at every join (MM8 crate `t68a13l*`, 2026-10-09).
- `next` and `redo` always claim all pieces of an assembly together.
- `assembly_overrides.json` (`[{"members": [ids in order], "axis": "u"|"v"}]`) declares assemblies that detection
  skips because the members have family relatives, e.g. MM7 two-part banners (`wizh-a/b`, `chb1p6/7`,
  `banwiz-a/b`). Generated separately, each half got its own native-mean gain and the cloth stepped at the joint,
  which no per-piece gain can fix; one canvas gives both halves one calibration. `inventory` applies the file after
  detection; to apply it without a rebuild, run `apply_assembly_overrides` on inventory.json under `.claim.lock`. Describe the head's material as the whole
  face (e.g. "one complete front face of a plank chest: ...").

## Small motifs: generate the motif once, copy it everywhere

A narrow repeating motif inside large pieces (the MM8 `t01a*` greek-key frieze, 16 native pixels tall) is too small
for the generator to read in a 128×256 reference: it redrew it as bow-tie, star or flower panels, and family prefill
spread the misreading to every piece. When the motif also exists as its own texture (`t01a11c` is the frieze tile),
generate that tile `--standalone` with a finer reference (`--ref-blur 0.6`) and an exact description, review it at 1:1,
then list it in `family_sources.json` ({member: [{id, dx, dy}]}) for every piece containing it. Those sources are
copied first and the pieces wait for them; the motif is below the automatic 15% relation threshold. Reopen the
pieces and everything whose `accepted_sources` reach them. Judge friezes and other fine ornament at 1:1, never from
the thumbnail.

## Rotated copies

Some natives are exact rotations of another texture (MM8 `t05a11` is `t05a10` turned 270°). `retry JOB NAME
--rotate-from SOURCE:K` checks that `np.rot90(SOURCE, K)` equals the native, and `check` then cuts the master from
SOURCE's accepted master by the same rotation (candidate `NAME_r`, accepted as `NAME@vr`); nothing is generated.

Others are re-dithered copies of a window of another texture: exact block hashing misses them because the palette
noise differs, so family prefill covers only part of the picture and the model fills the rest, leaving stepped
patches along the prefill boundary (MM6 `mswallr` and `mswalll` are the halves of `mswalld`, mean difference 5 per
channel). `retry JOB NAME --copy-from SOURCE:DX[:DY]` checks that the native matches SOURCE shifted by DX,DY within
`COPY_TOLERANCE` (8), and `check` cuts the master from SOURCE's accepted master (candidate `NAME_c`, accepted as
`NAME@vc`). Add `--mirror` when the native is SOURCE mirrored left to right (MM6 `mswinr1` is `mswinr` mirrored, `mswinm3` is `mswinm2` mirrored): generate one of a mirrored pair, cut the other. `rebuild` and `redo` follow both kinds of cut like any other copier. When a family piece keeps getting
patches after two retries, search the accepted natives for such a window before generating again.

When one relative draws its own joint or bevel a native pixel inside the region it shares with a piece (MM6
`t1wl9rea`'s border highlight inside the `t1wl9cts` shared columns, copied on into `t1wl9spa/spb/spc` as a pale
hairline), restrict the piece to the clean relatives: `retry JOB NAME --prefill-from NAME[,NAME]` (sticks to the
texture; used for prefill and derivation).

### Composed facades: one base wall under every door and window

Many facade sets repaint the wall inside every door, window and end piece (MM6 `th*` brick, `str*` fieldstone,
`pxstr*` timber plaster): exact and near matching find 10–25% shared pixels, each piece's wall is generated on its
own, and in game the brick courses, stones and plaster tone step at every joint (user review 2026-10-11, New
Sorpigal, Free Haven, Ironfist). The native joints themselves usually line up (course profiles correlate ~0.9 across
the joint, 0.1–0.5 in the independent masters). For such sets, `compose.json` names a base wall per piece:

    "mm6/thsmdr": {"base": "mm6/thctr", "features": [[6, 0, 122, 256]]}

`prefill` then copies the base master (tiled, at `dx`/`dy`, default 0) into everything outside the feature boxes
(native pixels, `[x0, y0, x1, y1)`), before the exact relatives; only the boxes are generated, on that wall. Every
piece sits on the base's own tiling grid, so piece-to-base and piece-to-piece joints continue by construction.
The base is copied with its own seam columns (no `SEAM_TRIM`): continuity with the base is the point. Pieces wait
for their base; `accepted_sources`, `rebuild` and `verify-families` follow it like any relative.

- Draw boxes on the native with a 16-pixel grid; cover the door, window, trim, pilaster and its cast shadow, and also
  any unique ornament of the base (the `thctr` urn and pendant) where a piece's own native has something else, or
  every piece gets a copy of it.
- Keep boxes off continuous bands (cornices, friezes, beams) except where the feature really crosses them: the model
  redraws a band inside a box a few pixels off height (MM6 `thre` cornice beside the pilaster).
- On uniform walls (plaster), add `"refine": "diff"` and `"tol"`: inside the boxes only pixels whose blurred native
  differs from the base by more than `tol` are generated. Boxes around a diagonal brace otherwise become shaded
  rectangles with straight edges against the copied plaster; `tol` 60 keeps just the timber (MM6 `pxstr*`).
- Automatic masks failed: base-colour matching misses arches, frames and pilasters drawn in wall colours; patch
  nearest-neighbour and blurred difference flag whole pieces on brick and stone, whose walls differ everywhere.
- Changing a piece's spec needs a scheduler restart (specs are cached per process); reopen the piece and every
  accepted texture whose sources reach it.

## Neighbours: continuing across abutting textures

Buildings and walls are tiled from one background: a facade's door, window, corner and end pieces abut the plain
wall piece in the map, edge to edge, and the original pixels continue across each joint. Shared-pixel families only
catch pieces that overlap; abutting pieces generated alone invent their own courses, friezes and door wings, and the
facade jumps at every joint (2026-10-10 user review of MM8 out01/out02: inn double door, hut door frame, Ravenshore
thatch line; 136 of 141 bad joints traced had been generated with no neighbour context).

- **Detection.** `collect_abutments` buckets faces by plane and links collinear, overlapping edges (UVs interpolated
  along the edge), so T-junctions count; it used to need two shared vertices and missed most facade joints. Every
  border-to-border abutment becomes a `neighbors` link, not only pixel-continuous ones: facade pieces line up only
  approximately in the natives (stone courses and thatch line at the same height, pixels not equal).
  `tex.py neighbors --world W` refreshes one world's links under the claim lock without a full inventory rebuild
  (MM8: 750 → 1964 links).
- **Split pictures are one canvas.** Pixel-continuous pairs whose partners are exclusive on that side (door wings,
  relief halves, crate rows/columns, panel pairs) are declared in `assembly_overrides.json` and generated as one
  picture, cut back into the pieces. The canvas gets its members' family prefill and the chain's outer neighbours as
  context, so the wall on both sides is real 4× art (`|A|B C|A|`). Assemblies that would not fit one return at 4x
  keep the neighbour-context route.
- **Order.** A piece (or canvas) waits for every higher-priority neighbour still in progress (`waiting_for`,
  `wait_priority`: members share their canvas's order, so waits never deadlock). Base walls go first; nothing is
  generated beside an unfinished neighbour.
- **Context.** Each side with an accepted neighbour shows a `CONTEXT_PAD` = 32 native-pixel strip of that
  neighbour's real master (16 was too little to follow), when one return still holds the canvas at 4x; the margin is
  recorded per version in `request['pad']` so `check` and `rebuild` crop exactly as generated. On a repeating axis
  with context the wrap splice (`quilt_wrap`) is skipped: those margins are the neighbour, not the texture's own
  repeat (it pasted the neighbour onto the opposite edge, MM8 `gtempdor1`).
- **Soft joint in the reference.** The first `JOINT_OVERLAP` = 4 native pixels of each context strip next to the joint
  show the neighbour's *blurred native*, not its sharp master: sharp neighbour art directly against the blurred core
  put a hard edge exactly on the crop line, and the model painted it as a 2–3 master-pixel dark groove inside the crop
  (user screenshot, MM8 Ravenshore `t14a07|t14a01`, 2026-10-10: edge columns 66/53/49 where the native stays at 80;
  after the change 75/74/75). The sharp-to-soft step now lies in the discarded margin.
- **Check.** `joint_<side>` = step across the joint / interior step (master vs native, at native scale); `joint <side>`
  is flagged above max(2.0, 1.5× native) and also covers assemblies. It does **not** replace the edge/rim/line tests:
  it averages 4 master pixels into one native pixel and hides exactly the 2-pixel grooves above (an earlier rule that
  let a passing joint drop those flags shipped the Ravenshore groove). Judge rim/line flags on zoomed joint crops
  against the real map neighbour (native | master, 3x), never on whole review sheets: most remaining ones are the
  native's own joints (bamboo seams, pilaster gaps, ledge shadows, door-wing gaps), the rest are grooves to retry. Joint-only flags go to eye review on a strip with the neighbours (left | piece | right): many
  flagged pairs are different materials that merely touch (tapestry beside a floor, marble beside plaster).
- **Repair round** (MM8, 2026-10-10): pilot the user's examples first; then `redo` the later side of every joint with
  a master step > 2× native, every member of a declared assembly, and every accepted texture whose
  `accepted_sources` reach a reopened one. A joint audit at native scale after the round: 47 of 899 joints still
  > 2× native, nearly all ledges and different materials on review; the 4×-scale audit overstates steps because crisp
  4× edges always differ more than the blurred natives.
- **Tone steps at joints** (user review 2026-10-10: MM8 Fellburn door `t19b03b`, Clan Leader's Hall plaster
  `t02a06`/`t02a08a`). A narrow wall strip beside a door or pilaster is shaded as one flat block, so a brick or plaster
  patch crossing the joint changes tone half way; regeneration keeps reproducing it. `tex.py joint-tone NAME...
  --world W` applies a smooth per-channel gain field near each edge so the master's low-pass edge tone continues the
  accepted neighbour the way the natives continue (the native's own step is kept), fading out over 20 native pixels;
  detail is untouched, the flag is stored on the request and `check`/`rebuild` re-apply it. Correct the *family
  source* first: copied pixels are pasted back exactly, so a dark edge inherited from a source (`t02a08b` here)
  survives any correction of the copy. Then `rebuild --world W --only <copiers>` and correct the copiers. Measure
  the edge tones of the whole family (left/right 3 native columns, master vs native) before choosing what to correct.
  `audit/rowview.py` renders a mapped facade row (native above, masters below) for review.
- Not fixable by textures: faces that show only part of a texture's width (a well whose 72-unit faces cut a 128-wide
  texture mid-stone, a facade face cut at the texture's middle column) break mid-pattern in the original too.

## Edge rims and margins on every side

The renderer's sampler repeats every texture, so the outermost rows/columns of a texture blend with its opposite
edge in game. The generator tends to paint a dark (or light) rim at the canvas border; on `wywl`/`wywl2` the
bottom row came out at luma 15–29 instead of the native's 88, and showed in game as a dark dashed line flickering
along the top of the next row (2026-10-09 review).

- Every reference has a margin on all four sides (1/8 of the size, 4–16 native pixels); the rim lands in the margin
  and is cropped away. Repeating axes show the neighbouring repeat there and get `quilt_wrap`. Axes that do not
  repeat mirror the piece's own edge (the blur reflects there too): a wrapped margin put the opposite edge, often a
  dark post or frame, right at the tile boundary, and the model carried it into the crop (MM7 2026-10-09: about a
  third of the `hn*`/`cnb*` facades and most tapestry and door releases).
- `check` measures each side's outermost native-pixel row/column against the native (`edge_*` metrics) and flags
  ratios below 0.6 (dark rim → seam) or above 2.2. Mild brightening from a thinner joint line is harmless.
- `rim_*` checks the outer 8 master-pixel lines one by one against the darkest and brightest of the native's three
  outer rows, and flags a line darker than 0.6× or brighter than 1.8×. It catches the one or two master-pixel
  hairlines on the crop boundary that `edge` averages away. These are seams in game, and family prefill copies them
  exactly into every relative, where no retry can remove them; never accept a `rim` flag.
- `line_*` catches the partial-length version: per native pixel along each side, a position counts when the outer two
  master pixels differ from the native edge pixel by more than 70 while master pixels 4–7 inside still match it
  (within 50). On repeating axes the native pixel across the seam (the opposite edge) also counts as a match, since
  a joint the native draws on one side of the seam may land on the other (MM8 `gcst1-rt`, `gcstwal1`). A run of 8 or
  more native pixels flags `line <side> <run>px`; shorter runs were mostly crisper native joints. Typical cause: the
  generator moved the native's edge joint two master pixels inward and left a pale or dark hairline on the boundary
  (MM7 framed crate faces, `t4s1er`, `tfb1r3a`; MM8 `alphanumc`). Never accept a `line` flag; retry with `--roll`
  on that axis where allowed.
- On a repeating axis the rim reference also includes the opposite edge's three rows: in game that edge is across the
  seam, so a joint the native splits between the two edges is real content, not a rim.
- **Rolled generation** (`retry JOB NAME --roll u|v|uv`). The remaining rims come from the model painting a groove
  wherever the reference shows the tile boundary: a mirror fold, a joint the artists put on the edge, or the opposite
  edge wrapped against it. Rewording the prompt does not help (MM8 A/B, 22 rim failures: 17 rims with the border
  wording, 14 without it); edge-replicated margins break the layout. Rolled, each chosen axis moves its quietest
  interior line (`quiet_offset`) to the canvas boundary, so the real edges are painted as ordinary interior content;
  the rolled axes wrap and are quilted, and `check` rolls the master back by whole master pixels and recomputes the
  seam, edge and rim checks in the texture's own frame. On the same set, 9 of 16 rolled returns still flagged, and
  most of those were native joints drawn sharper (now passed by the seam-aware rim on repeating axes). Use the axes
  of the flagged sides, but never an axis along which the texture abuts other textures in the map (`neighbors`): there the accepted neighbour's real pixels are the context, and `--roll` refuses it. Rolled versions keep family prefill (rolled with the texture, so shared pixels stay exact) and the neighbour margins of the other axis; sectioned textures and assemblies cannot be rolled. Never use `--standalone` to get rid of a flaw copied from a relative: fix the relative instead, or every piece of the background drifts apart.

## Large textures: sections

Textures whose 4× reference would exceed one return (~1.57 MP: 512×256 carpets, 256×512 windows and tapestries,
512×512 panels) are generated in overlapping sections instead of being skipped. None of the MM6–MM8 cases repeats
internally (checked by exact self-matching), so they cannot be assembled by tiling a smaller period.
`section_plan` splits the padded canvas into 2 or 4 parts with 12 native pixels of overlap (each section joins the finished pixels along a minimum-error cut through that overlap, not a straight line); each section's
reference carries every finished pixel (family prefill and earlier sections) sharp, the rest blurred, and the
worker is told which part it draws. Sections are gain-matched to the finished overlap and assembled into the
version's raw image; `check` then treats it like any other return. Review the section joins at 1:1.

A narrow strip that would be stacked as copies (see `layout_for`) but is then too large for one return is not
stacked: one copy is generated in sections along its long axis. Stacked copies split into sections showed the model
parts of two copies, and it painted one wide picture across them (MM8 crate assembly `t68a13l*`, 2026-10-09).
Sectioned assembly heads hand the scheduler the real member id, not the `@head` canvas id (fixed the same day; a
scheduler started before that crashes with `KeyError: 'mm8/@…'` on its first sectioned assembly and needs a restart).

## MM9 rework maps (pilot: Anskram Keep, 2026-10-30)

The remade MM9 maps (`level_generation/projects/mm9r_*`) live in the isolated review root
`output/mm9_rework/assets_dev`, so the `mm9` world is scoped per map and installs there only:

```sh
python3 tex.py inventory --world mm9 --map anskramkeep.blv   # rebuilds only mm9; map_scope is kept for reruns
python3 tex.py next --world mm9 --count 40
python3 tex.py gen --world mm9 --parallel 24 --follow
python3 tex.py install --world mm9                           # review root + assets_source PNG sources
```

- **Sources.** Maps and map Lua come from the review root (`WORLD_CONTENT`); natives are the importer's decoded DTX
  bitmaps in `assets_dev/worlds/mm9/textures` (10-character aliases; `source_texture` in the inventory names the DTX
  from the `*.material_aliases.yml` files). Helper materials (`invisible`, `black`, `greenscreen`, ...) are excluded.
  The ESRGAN column is `tools/upscaling/out_prod_bmodel_mm9` (`upscale_model.sh` with `PROD_DIR`).
- **Prompt.** The era line and the artefact line are per world (`ERA`): MM9 is early-2000s 3D art compressed as DXT1,
  so the prompt names 4×4 block artefacts instead of palette dither. MM6–MM8 prompts are unchanged.
- **Independent tiling materials.** MM9 has no cut-sheet families: the natives share no exact pixels (DXT re-encoding)
  and the faces are mapped in world space on a 128-unit grid, so different materials meet at texture borders by
  coincidence. `TILED_MATERIAL_WORLDS` keeps only pixel-continuous joints as neighbours there; the coincidental ones
  replaced a texture's own wrap margin with an unrelated material and skipped its seam splice. Nearly every MM9
  texture repeats on both axes, so the wrap splice and the seam/edge/rim checks carry the weight.
- **Tiled base + something on top.** Where MM9 painted a small repeating pattern under a foreground (the Anskram
  ceiling: a 32-pixel quatrefoil lattice under crossed beams), `periodic_bases.json` declares the pattern as its own
  base (`from`, `period`, `exclude` mask of the foreground). Its native is the per-phase median of the cells outside
  the mask; it is generated once as a seamless tile, and the source is composed on it (`compose.json` with a `mask`
  PNG, white = feature): the lattice is copied exactly and only the beams are painted over it. Bases have no faces and
  are never installed. A re-painted variant of a wall (`anskramwall2` = the wall's courses plus a crack, mean
  difference 12, above `COPY_TOLERANCE`) is composed on the wall with a feature box, as for MM6 facades.
- **Install.** `install --world mm9` cooks the masters with the desktop cook's exact job (BC7, linear, full chain) and
  places them as `worlds/mm9/textures_x4/<name>.oytex`, plus a Lanczos half as `textures_x2/<name>.png`, through
  `review_root.install()` (owned paths, never through a hard link). It also syncs the tier sources into
  `assets_source/worlds/mm9/textures_x4` (the master, hard-linked) and `textures_x2` (the same half), from which the
  build's surface cook makes the game's x4 files in `assets_dev`, as for MM6–MM8; the `*opq` variants there and in
  the roots belong to `mm9r_common/opaque_textures.py` and are kept. Textures without a master get no file and draw
  their 1× native (in `assets_dev` a cooked x1 file from `assets_source/worlds/mm9/textures`, which the surface cook
  removes once the master is installed). No lighting re-bake is needed: the bake depends on the 1× bitmaps, and the logical size (and so
  the UVs) stays 128.
- **Animated frame sequences.** Faces name only a sequence's first frame (`texture_frame_data.txt`), so the inventory
  never sees the other frames. Left at 1×, they made the animation alternate between the x4 head and the 1× frames:
  the Thjorad Mine ore walls (`thjo3rw631`, `thjoj5hw88`; one glint moving over an unchanged wall) flickered once per
  cycle (2026-11-08). `tier_plan` now derives the later frames' masters (`frame_masters`) from the head master plus
  each frame's own change against the first native frame, upscaled, into `masters/<world>/frames/`. Every stage and
  install carries them, and they follow a re-accepted head automatically. Frames that redraw more than 10 % of the
  head are different art, not variants: they are reported and left as they are (MM6 `john01`–`john06`).
- **Density.** MM9 maps 1 texel per LithTech unit = 0.39 texels per native unit (MM6–MM8: 1). The keep's UVs are
  MM9's own (checked per face); x4 brings it to 1.56/unit. A texture without an x4 file draws its 1× native at the same density (the engine's 1× fallback
  takes the loaded file's tier since commit `f6bed391c`, confirmed in game 2026-10-31), so native and x4 can be
  compared on the same map directly.
- **Alpha.** The decoded natives are 32-bit BMPs whose fourth byte is alpha (SDL reads it; PIL opens them as RGB).
  `tex.py` reads that byte since 2026-11-01 (`bmp32_alpha`): 266 MM9 natives carry alpha, 54 of them in the dungeon
  scope (arena crowds, grilles, chains, ladders, glass, ice, web, blood, a door's open top). Before that, 42 of them
  were accepted as opaque masters: the Arena crowd drew as heads on black. `tex.py alpha-from-native ID...` gives such
  a master the native's alpha at 4× (binary cut-outs: a one-texel feather, and painted-background strips along the
  silhouette cut away; translucent natives keep their smooth levels) and logs an `alpha` ledger event. Where the
  generated shape itself does not follow the native silhouette (Grill1's bent bars, the round light fixture, the
  spiked fence's knob), regenerate it as a cut-out instead (`redo`).

## Known limits

- Two different wall families that meet in a map (for example `d2wlcctr` and `d2wlactr`) share no pixels in the
  originals either, so they stay visibly different stone sets, as in MM6.
- Event-switched textures are included through `SetTexture` calls in the map scripts; their faces have no area, so
  they rank low.
- 12 textures have no ESRGAN x4 file; staging carries their x2 enlarged as placeholders until accepted.
- `mm6/stain512` (512×512 checker floor with a stained-glass light pool) still fails in sections: tile rows misalign
  at the vertical wrap. It stays on ESRGAN until a checker-specific approach (generate one tile family, assemble the
  grid, add the light pool as a separate layer) is built.
