# MM6 master acceptance viewer

From the repository root:

```sh
python3 -B level_generation/creatures/mm6_remaining/acceptance_viewer/serve.py
```

Open <http://127.0.0.1:8765/>. Restart the server after new masters or changed images are staged.

For the complete latest-method MM6 selection, use the isolated
[packed-outline collection](../../mm6_packed_outline_collection_20261001/README.md):

```sh
python3 -B level_generation/creatures/mm6_remaining/acceptance_viewer/serve.py \
  --collection level_generation/creatures/mm6_packed_outline_collection_20261001/collection.json \
  --port 8767
```

This selects only the collection's 60 hash-pinned manifests, including the eight video-ESRGAN finishes.
It never consults the default historical queue or `selected_packages.json`. Changed manifests or review pixels
fail visibly instead of selecting another attempt. Collection mode saves decisions and frame fixups under the
collection's `review_state/` by default; `--state-dir` can override that for a temporary test.
Use `--check` to validate the exact collection without opening a server. Existing `--package` and default
queue behavior remain available for other reviews.

`selected_packages.json` selects replacement staging manifests by the existing queue family label. Selection
changes the default all-family queue, survives progress-ledger refreshes, and leaves previous packages and gameplay
assets intact. Each replacement must retain the creature ID and pass the normal package checks. Unknown family
labels or missing/broken selected packages fail visibly. `--package` still creates an isolated review queue.
Decisions and fixups remain artifact-bound: never carry old-art edits onto a replacement. When promoting an
isolated trial, merge only that exact artifact's saved checkpoint into the main state, preserving other versions.
DragonCover currently selects the guided restoration's single red master; blue/gold variants are outside that trial.

The queue includes all 60 complete MM6 creature/NPC master sets, including earlier packages. Measured generated
detail remains visible: Genie is below 2×; Goblin and Monk are exactly 2×. Completeness is not visual acceptance.
It draws the native
palette image and exported restored atlas at the same default 2× display size and plays frames at their recorded
native durations. Native references receive the exact half-pixel anchor correction used by the atlas export.
The default Game frame scale option preserves per-frame scale relative to standing at a fixed viewing distance;
the viewer does not recreate world projection, AI action changes, or lighting. The tour cycles through distinct
actions and views; selecting an action or view holds that clip. One-shot clips repeat for review.

## Frame placement and guides

For agents preparing equivalent JSON proposals, use the shared
[anatomical placement workflow](../../ANATOMICAL_PLACEMENT_WORKFLOW.md) and
[proposal compiler](propose_anatomical_placement.py). It accepts explicitly measured head/body/contact points,
retains the existing checkpoint schema and writes to an isolated state directory. Custom contact names live
in its evidence rather than changing the landmark UI. Numerical fits remain subject to sequence review.

The viewer opens paused with **Edit placement** enabled. Use **Play** / Space to preview the corrected animation.

- **← Frame / Frame →**, `[ / ]`, or the slider select frames in the current native clip.
- **Master** lists every exported frame, including frames outside animation bindings. Selection opens a canonical,
  unmirrored single frame; frame buttons then move through that list. **Return to clip** restores animation browsing.
- Drag the restored canvas or use arrow keys / arrow buttons. One default step is **one physical atlas pixel**
  (½ original logical pixel at tier 2). Choose **1 original pixel** for a two-atlas-pixel step; Shift+Up/Down gives ten
  steps. Dragging always snaps to individual atlas pixels. Screen directions are converted back through view
  mirroring and native frame scale. The original and camera remain stationary during editing.
- The cyan top guide starts at the opening original's highest nontransparent pixel and then **stays fixed** across
  frames, playback, actions and views. Drag it on the original; both panels follow. With that canvas focused,
  Up/Down nudge it. **Auto top** explicitly snaps to the current original's top; changing frames never does.
  The cyan bottom remains at the original silhouette bottom. Pink lines use restored alpha ≥128 to ignore soft halos.
  Top-vs-guide and silhouette heights are displayed in original logical pixels before native frame scaling.
  Weapons, hair and wings count as silhouette; the guide is not a head detector.
- **Center guide** starts at the opening original's opaque center and then stays fixed, including through mirrored
  views. Drag it on the original or focus that canvas and use Left/Right. **Auto center** explicitly snaps to the
  current original's center. **Guide X / Guide Y** edit positions from the canvas top-left at 100% zoom. Guide nudges
  follow screen directions regardless of mirroring. Both guide positions autosave for the family; **Undo guide**
  reverses the last guide edit, including an entire drag. Moving sprites leaves the references stationary.
- The vertical guide checks actual displayed sprite alpha at each row: solid **red** for original-only hits,
  **pink** for restored-only hits, and **green** where neither intersects. Where both hit, its two-pixel width splits
  red/pink. Both panels show the same comparison strip. Backdrops and other guides do not count as sprite geometry;
  fractional placement, mirroring, frame scale, zoom and your restored offsets are included in the intersection.
- **Zoom** scales both views together, from **50% to 800%**, including **400%**. **100%** is native original size;
  the initial setting is **200%**. Guides zoom with the artwork. The shared zoom is saved with the family guides.
- **Undo frame edit** reverses the last edit to that frame. A drag is one undo step. **Reset offset** only resets
  placement, retaining the guide, regeneration flag and note. **Preview fixups** toggles placement proposals;
  reference guides remain visible.
- **Flag frame for regeneration** and the adjacent note describe art/scale faults that translation cannot repair.
  A frame's fixups apply across its palettes, actions and views; distinct frame names remain independent.

## Interactive size trials

### Eye, head and groin landmarks

The **Landmarks** bar stays at the left of the comparison, including while the canvases scroll. Both sprites show automatically populated
suggestions where the selected package has anatomical records, visually located seeds or a distinct same-view
appearance match. The optional head line records X only. Eyes are separate points: profile/back art is never
assigned a second eye by symmetry. An unknown point stays empty. The visible A-shaped leg junction detector
requires continuous foreground legs on both sides of the gap and independently agreeing original/restored points;
an arm/shield gap, robe hem or centre of silhouette does not establish a groin landmark.

The visible quick actions operate on the current frame:

**Shift+Left / Shift+Right** goes to the previous/next animation and native view, skipping mirrored copies
(for example, Harpy walk 4 → attack → hit). Navigation wraps at the ends and stops the clip tour.
**Shift+Space** applies **Align restored X** followed by **Fit top + bottom** to the current frame, or just
the action whose references are available. One **Undo sprite adjustment** restores the entire shortcut.
Shortcuts leave text fields and dropdowns alone; Shift+Up/Down still nudges by ten steps.

- **Guide → head X** moves the shared vertical guide to the displayed original head axis, including mirroring
  and native frame scale. The guide then stays fixed until moved again; the sprite does not move.
- **Align restored X** moves only the restored frame's horizontal offset to match that head axis, retaining its
  size, vertical offset and scale anchor. It works with current saved size/offset proposals.
- **Guide → head top** moves the shared horizontal guide to the original head-top point.
- **Align restored Y** changes only vertical offset to match head top at the current size.
- **Fit top + bottom** sets one uniform size from the original/restored head-to-bottom spans, aligns the restored
  bottom to the original opaque bottom line, and preserves the restored head's current horizontal position.
  This uses the unmodified master coordinates, so repeated clicks do not compound the size. It sets the bottom
  scale anchor and preserves other notes/flags. The bottom line is the existing opaque-bounds reference, usually
  the feet; a tail or hanging weapon can extend farther down. This is a placement proposal, not pixel resampling.
- **Add / edit head top** opens the point editor and selects head top for clicking on either sprite. Actions
  requiring absent points are disabled; they never substitute a wing/weapon tip or zero coordinate.

Sidebar readings show original and currently corrected restored coordinates in native logical pixels. **Undo
sprite adjustment** and **Undo guide** use the existing edit histories. Head-top suggestions use explicit crown
records where available, otherwise a compact continuous head contour near an independently located head axis.
Narrow projections, a clipped search and ambiguous contours are left unmarked. Head top is a 2D point; the
separate head-axis landmark remains X-only. Check suggested headwear/hair boundaries before applying size.

Circles/dashed head lines are suggestions, not approved anatomy. Open **Edit landmarks** in the sidebar,
enable **Edit points**, choose the kind, then
click or drag on either sprite. Each side has independent coordinates. **Keep suggestion** records the selected
point; **Hidden / not applicable** records an explicit null and suppresses its suggestion. **Clear edit** restores
the automatic candidate, and **Undo point edit** reverses a whole click/drag. Point edits autosave alongside fixups.

**Align selected point** translates the restored frame to the original point; head aligns X only.
**Fit size & offset to points** estimates one uniform scale and translation from at least two separated 2D points,
including the head's X constraint when available. It reports the residual and rejects unstable/out-of-range fits.
These buttons propose a correction for the current frame. Merely displaying/detecting points changes no placement.

Coordinates use **original logical pixels in the shared actor canvas**, before native frame scaling, mirroring,
size and offset proposals. Thus points survive those adjustments and all palettes/aliases share the frame record.
Head axis is `[x, null]`; head top/eyes/groin are `[x, y]`. Missing means unknown; the entire point `null` means explicitly absent.
**Export landmarks** includes recorded and suggested points, their provenance, BMP-local or atlas-local coordinates,
and generated-sheet coordinates where the package records an affine raw-to-master mapping. It never invents an
inverse for a recorded warp. The original and restored positions are measured independently, not copied from
one source to the other. Recorded points also appear in checkpoint exports and acceptance snapshots.

Build suggestions for every selected MM6 frame with:

```sh
python3 -B level_generation/creatures/mm6_remaining/acceptance_viewer/landmarks.py \
  --collection level_generation/creatures/mm6_packed_outline_collection_20261001/collection.json
```

Add `--family mm6:goblin` for one family. The collection's `landmarks/seeds.json` contains visually located
original/restored seeds; per-family suggestion files are bound to the pinned artifact/manifest, registration,
seed content and detector code. Stale suggestions are refused. This is a conservative initial pass, not a universal
fantasy-creature anatomy detector: uncovered/ambiguous poses still need manual points. The shared reviewer supports
manual points and existing anatomical records for other packages as well. Precomputation does not create a fixup
revision, invalidate acceptance, resample images or edit a sprite package.

**Size change** resizes the current restored frame immediately, uniformly in X/Y. `0%` is the current package;
`+2.565%` enlarges it by that amount. The slider covers −10% to +10%; the numeric field supports −50% to +50%.
Use **Keep fixed** to scale around the unmodified silhouette's bottom center, top center, or native actor pivot.
Placement offsets remain additive after scaling, so existing nudges are not multiplied. Size edits keep the original
and guides stationary. Large adjustments that extend beyond the canvas enable **Fit preview (cropped)**; click it
to reframe both panels while retaining the guides' position relative to the artwork. Clip/zoom changes also refit.

**Measurement** lists retained landmark spans, longest vertical span first. **Try measured size** sets the exact
original-relative factor for that span; repeated clicks do not compound it. For Cleric front-walk frame 4, the
head/sole span gives +2.564771%. The displayed range uses the classifier's explicit ±2 logical pixel span uncertainty;
it is not an approved adjustment range. These are saved annotations, not newly verified anatomical measurements.
There is no silhouette-width/height averaging and no automatic change to other frames. Packages without retained
registration landmarks have manual size controls but no measurement suggestions.

**Preview size** compares the size trial with the current package while retaining placement edits. **Preview fixups**
toggles both placement and size. **Reset size** changes only the size factor; **Undo frame edit** also reverses size
and anchor changes. Slider dragging is one undo step. Changes autosave with the frame, survive reload, and apply
to its other palettes and mirrored/reused animation bindings. Preview-size visibility is recorded with acceptance.

This is browser resampling of existing exported PNG pixels for rapid visual comparison. It does not rewrite the
PNG, atlas, or high-resolution source. Saved scale choices are proposals for a later source rebuild, where actual
generated sampling, masks, crop padding and independent body proportions still need checking.

## Match family height and bottom

**Match family height & bottom** adjusts every master frame in the current family, including frames outside clip
bindings. Each frame gets its own uniform X/Y size coefficient: original silhouette height divided by restored
silhouette height in logical pixels. Scaling uses the bottom-center anchor, then a vertical offset aligns its bottom
to its corresponding original, within half an atlas pixel. Original pose-height differences and center-anchor
corrections are retained. The calculation uses the exported bounds, so repeated clicks do not compound changes.

Horizontal offsets, guides, colors, notes and regeneration flags are retained. Empty silhouettes and corrections
outside ±50% size or ±16,384 atlas-pixel offset limits are skipped and counted beside the button. The fixed top guide and
saved anatomical measurements are not used as targets; this fits silhouette height, including weapons and wings.
Adjustments autosave as the existing per-frame checkpoint proposals and apply across palettes and mirrored views.
**Undo family match** restores the last match's size/anchor and vertical offsets, retaining other subsequent edits;
it is available until family navigation or reload. **Undo frame edit** can also undo a match for one frame.

## Live color preview

**Saturation** and **Brightness** range from 0% to 200%; 100% preserves the exported appearance.
**Area** selects the whole sprite or an existing material mask. DemonFly defaults to purple skin;
its neutral chest/belly is outside that skin region. Other choices use the package's own region labels:
a combined hide/wing mask cannot independently select those two materials.

Each palette keeps its own settings, shared across every frame, action and view. **Preview color** toggles
the adjustment without losing its values; **Reset color** restores both sliders to 100%. Changes autosave
with the existing checkpoint and are included in acceptance snapshots and checkpoint exports. These are
preview proposals; saving does not bake new PNGs or change game runtime assets. Original sprites, alpha,
size and placement remain unchanged.

Color grading uses RGB luminance `.2126R + .7152G + .0722B`, saturation about that luminance, then brightness,
clamped and blended by material coverage. The server exposes mask channels as opaque grayscale images because
the original mask's alpha is a fourth coverage channel. Treating it as PNG transparency would discard skin
coverage wherever that fourth channel is zero. Rendered frame crops are cached up to 64 MiB per active settings.

## Checkpoints

Edits autosave after a short debounce and on navigation; **Save now** flushes immediately. The save indicator confirms
the checkpoint revision. `frame_fixups.json` is created next to `serve.py` on the first edit. **Export checkpoints**
downloads the complete file. Offsets, guide adjustments, flags and notes survive reloads.

Checkpoints are keyed by family and artifact digest. Each frame record contains:

```json
{
  "offset_px": [1, -2],
  "scale_factor": 1.0256477123,
  "scale_anchor": "bottom",
  "original_crop_origin_px": [40, 80],
  "regenerate": false,
  "note": "Align shoulders"
}
```

`offset_px` is additive to `manifest.frames[name].crop_origin_px`, in physical atlas pixels, **before** mirroring and
native scaling: +X right, +Y down. Preserve the shared pivot and atlas crop rectangle. Fixed guide positions are
stored separately on the family checkpoint as `"guides": {"x": 155, "y": 28, "zoom": 2}`. X/Y are canvas coordinates
at 1× display zoom; `zoom` retains the shared magnification. Guides never apply to sprite metadata. Existing
per-frame `guide_offset_px` / `center_guide_offset_px` fields remain as historical records. When no fixed family
guides exist, the opening frame's old guide offsets seed the new fixed references once; subsequent frames do not
reposition them. The next edit saves the family guide state. Family records include the
original manifest/artifact hashes, manifest path, tier and revision, so later application can verify the exact source.
These are proposals: saving does not modify atlases, aligned masters, manifests, generation ledgers or installed art.

Scale fields are optional additions to checkpoint schema 1: absent `scale_factor` means 1, absent `scale_anchor`
means `bottom`. For a physical canvas point `p`, the preview uses
`anchor + scale_factor * (p - anchor) + offset_px`, then applies native frame scaling and mirroring. Top/bottom
anchors use the unmodified atlas crop origin plus its alpha>=128 bounds; empty bounds use crop edges. Pivot uses
`logical_pivot * pixels_per_logical_pixel`. Existing translation-only records retain their original behavior.

Writes use atomic file replacement and revision checks. If another tab saves first, or source images change, saving
fails visibly and family navigation is stopped. **Export unsaved edits** preserves that tab's draft before reload.
The browser warns before closing with unsaved changes. Restart the server after source packages change; old
artifact versions remain in the checkpoint file and are never silently applied to a new package.

## Family acceptance

Expand **Family acceptance & review note** for the existing family decisions.
Accept and Flag save to `decisions.json`, keyed by a digest of the manifest, aligned masters, displayed native images,
atlas pages, masks, and palette previews. The viewer does not alter existing pipeline acceptance or installed assets.
Use **Export decisions** to download the current queue with its decisions and hashes.
Decisions made before the anchor/scale preview correction remain saved and are marked ↻ for review in the queue.
New decisions retain the checkpoint revision and a snapshot of its frame fixups. A later checkpoint marks that
decision for review again. Existing decisions are preserved.

## Verification

For size/height discrepancies, see [Sprite scale diagnosis and correction](../../SPRITE_SCALE_DIAGNOSIS.md).
It records the MM6 row findings, original-relative measurements, and the isolated Cleric scale trial.
Interactive size previews now save per-frame scale proposals; production correction still requires a source rebuild.

For isolated before/after experiments, pass `--package path/to/current/manifest.json --package path/to/trial/manifest.json`
with a separate `--state-dir` and `--port`. The same viewer then reviews only those packages. Give trial manifests a
distinct `creature` ID and an optional `review_label`; keep experiment review state separate from production decisions.

`serve.py --check` validates and prints the queue. `--state-dir /tmp/mm6-review-test` isolates review writes.
`check_editor.py` runs Chrome with temporary storage and checks real keyboard/mouse edits, mirrored placement,
guide propagation, persistence, playback, and conflicting writes. Run using Python with Pillow and websocket-client:

```sh
/tmp/openyamm-creature-restore-venv/bin/python -B \
  level_generation/creatures/mm6_remaining/acceptance_viewer/check_editor.py
```
