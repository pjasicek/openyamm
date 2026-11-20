> Historical snapshot, superseded by HANDOFF.md. Painted doll restoration is deferred by user decision.

# Paperdoll and fitted equipment restoration handoff

Snapshot: **2026-09-24**. This document is for the next Codex session working on the
`assets_dev/engine/icons/*` paperdoll slice. The user's goal is to **visually approve every usable 2× doll
part and fitted equipment variant in the assembled game context**, after repairing the artwork that fails
that review. Preparation, a context browser, and exact-size candidates exist; classification and approval
of the remaining targets have not happened.

**PC01 update, 2026-09-24:** the user relaxed exact mask equality: the restored doll may be thinner,
so armor can cover it. The [contained-outline revision](identity_workflow/prepared/doll_01/contained_20260924/README.md)
now supplies one shared body plus four hand/arm layers through **Use PC01 fitted restoration**.
It reprocesses the retained generated master with inward antialiasing and no copied original RGB.
Every part stays inside its original 2× mask, with unchanged canvases and table coordinates.
The blue-black boot backing is removed; the shield hand remains original. This is a contour improvement,
not additional generated detail or proof that every equipment candidate fits. Visual approval is pending.
The browser displays one pose at a time and has an independent **Use original doll (body + hands)** option.
Older exact-mask and full-doll trials below are historical; the browser no longer loads them.

Start with the [paperdoll browser](index.html), the [PC01 limb diagnosis](identity_workflow/in_situ_preview.html),
the [identity workflow](identity_workflow/README.md), and the
[exact pending target snapshot](APPROVAL_SCOPE_20260924.csv). The [review browser README](README.md)
explains its resolver, source tables, candidate selection, and refresh commands in more detail.

## Precise ownership and approval state

The scope is **engine icons** whose frozen target treatment is `paperdoll_parts` or
`fitted_equipment_variants`. The generated `catalog.js` is the live browser inventory. The CSV is a dated,
one-row-per-target snapshot with source and candidate hashes, native and 2× dimensions, candidate provenance,
and whether the current game resolver selects it. Its 1,396 rows are exactly this predicate:

```text
target in catalog.js.reviewTargets
target.active == true
catalog.js.assets[target.name].candidateStatus not in {"accepted", "hud_approved"}
```

The snapshot was checked against `catalog.js` SHA-256
`68655adbac1927c8842cb8a70a2d779a2c114c5205dbe46c9450c0fe0c890701`; the CSV SHA-256 is
`d36b35baacc29ed4d1e86148eb5fad21138ed8d7d6beb521de0f3054eed5030f`. Use the live catalog and
checkpoint if either changes.

| Pending engine icons to review | Count | What is included |
| --- | ---: | --- |
| `paperdoll_parts` | **490** | 75 bodies, 391 separate limbs/hand overlays, 7 table-selected backgrounds, 17 head/beard metadata fields |
| `fitted_equipment_variants` | **906** | 505 `Armor`, 18 lowercase `armor`, 102 `Cloak`, 171 `Helm`, 66 `Belt`, 41 `Boots`, 3 `Shield` table variants |
| **Total pending** | **1,396** | 1,281 currently resolver-selected; 115 manual or metadata-only (98 fitted, 17 head fields) |

The broader browser queue has **1,757** engine targets in these two treatments. Of them, 127 active fitted
variants are already accepted in the canonical checkpoint, and 234 targets are outside the current active
restoration scope. The checkpoint contains 132 accepted fitted variants in total, including five inactive ones.
Do not reclassify existing acceptances merely because they appear in the browser's “all” scope.

Every one of the 1,396 pending targets has a nonempty **RGBA candidate at exactly twice its own original
width and height**. The current selection is 399 preexisting audited candidates (including eight prepared
one-pixel border repairs), 940 extracted raw returns, 35 target-specific previews from donor artwork, and 22
new transparent sheet returns. The 35 donor destinations require their own consumer review. Technical
registration flags, cell-boundary flags, and a successful dimension check are **not** artwork approval.
Some candidates are clearly rough, clipped, or contaminated and exist so the user can classify them.

### Nearby assets that are context, not this approval queue

- Weapons, bows, shields, base inventory item icons, and many jewelry icons are `inventory_items` targets.
  The paperdoll browser draws them as context. It uses an exact 2× file if selected, otherwise a nearest-neighbor
  enlarged native 1× image; it never draws a higher-resolution raw master directly. The loadout in
  `test_img/2030.png` mixed such layers. Do not approve those item icons as part of these 1,396 targets.
- Player avatar portrait frames and NPC portraits have separate restoration/approval families. The original
  avatar selected by `character_data.txt` is the identity reference for the doll. A 2× portrait candidate
  beside it is comparison context until its own family accepts it.
- HUD skin, panels, buff icons, bars, and controls were handled in the separate HUD acceptance slice.
  The spellbook, other UI, and MM9 icon work have their own scopes. Do not merge their decisions into this queue.
- The seven missing `pc30` body/limb names and four absent dwarf beard names are evidenced missing/non-target
  references. Do not invent a substituted sprite. Character #31 has a portrait but no body for the identity
  packs. The browser lists these missing names explicitly.

## What the browser already does

The [main browser](index.html) covers all 77 `character_data.txt` rows. It derives positions, variant
selection, and layer order from `character_data.txt`, `doll_types.txt`, `items.txt`,
`complex_item_pictures.txt`, `assets_dev/engine/ui/gameplay/character.yml`, and the gameplay renderer. It
shows the assigned original avatar, one table-selected background with a visibility toggle, and three
simultaneous poses: empty hands, one-hand main item with optional off-hand item, and two-hand main item.
There is also a jewelry overlay view and a Spear mastery control. Select an item for each shared slot, inspect
layers and the original/candidate pair, and switch between candidate and original art.

The default right-hand queue is **active and not canonically approved**. Search or step through assets; `[`/`]`
step through filtered targets, and Left/Right arrows step dolls outside inputs. A URL such as
`index.html?doll=1` or `index.html?target=engine--icons--6chain1v3.bmp` opens a review context. For variants
the live resolver would not choose, the browser says **forced preview**. That view is useful for art review but
is not evidence that the game would draw that file. Seventeen head fields are metadata only in the current
renderer and are shown in the inspector without a fabricated placement. The browser simulates engine positions
and draw order, but Canvas blending can differ slightly from the engine's BGRA integer blend; use a game
capture for a final borderline alpha/placement issue.

Browser Approve/Flag decisions are stored locally and only leave the browser through **Export review JSON**.
That JSON records target id, selected attempt, source/candidate hashes, doll id, note, and forced-preview state.
An imported decision becomes stale when its source or selected candidate hash changes. Browser approval is
review evidence, **not** canonical `queue.py accept`, export staging, or installation. No paperdoll decision
export has been retained in this repository from this slice; do not infer user approval from a preview.

## The intended doll restoration method

The user prefers the detailed restored dolls to the Real-ESRGAN enlargement, but requires the limbs to look
as if they belong to that same doll. The [ESRGAN comparison](identity_workflow/esrgan_baseline/index.html)
contains 466 exact 2× RGBA body/limb enlargements, all registration-passing, assembled for 75 dolls. It is
a geometry and color reference, not the desired final art: sampled hands and bracers are visibly weaker than
the painted body candidates. The 75 prepared identity packs cover available doll/portrait pairs; two of the
77 rows lack necessary original art as described above.

Use the **assigned original avatar and one selected body** as the face, skin, clothing, bracer, and lighting
reference. Assemble the native limb with that body at its actual table offset before imagegen. Show the full
doll and an enlarged native pose/edit region, so the return knows how elbow, wrist, cuff, and fingers attach.
Keep the body pixels fixed in the final assembly; extract a regenerated limb onto its own original logical
canvas at **exactly 2×** size. Give each distinct forearm orientation its own in-place pose. When two hand
states share a proximal bracer at the same placement, reuse that approved proximal material and change only
the distal wrist/hand region. Transfer pixels only where the two placed silhouettes actually correspond.
Do not cut arbitrary limbs from a newly generated whole doll and assume offsets will align.

Keep the exact raw imagegen output, exact submitted prompt, references, processing parameters, source/output
hashes, and technical report. Ask imagegen for genuine alpha on separate cutouts. Inspect dark/light alpha
edges and magenta spill. Measure silhouette, occupied area, margins, grip opening, fingertip gaps, and joins
against the original and assembled states. A source-mask paste must not hide displaced generated anatomy to
make a failed sprite pass registration. A deterministic repair is acceptable for a specifically identified
one-pixel fringe or for an aligned shared material region, with the before/after evidence retained. Follow
[matte and fitting](../MATTE_AND_FITTING.md) and [Dense64 batching](../BATCHING_DENSE64.md) when grouping new
returns; use fewer than 64 cells when doll/equipment art needs more resolution and linked references.

Review a doll with its background both on and off, in all supported hand poses and representative equipment
loadouts. Inspect each fitted `vN`/`vNa` state beside sibling variants and the body/limbs it touches; armor
uses `vNa` preferentially when the main hand is empty, cloaks use `vNa`, and doll types 2/3 use cloak `v1a`.
Check item identity, layer order, table offsets, material continuity, transparency, clipping, and silhouette at
normal display size and close-up. A green technical measurement does not override a visible failure.

## PC01 pilot: current evidence and blockers

The [PC01 comparison page](identity_workflow/in_situ_preview.html) is a **method trial only**. Its sprites are
not selected by the main browser, canonically accepted, staged, or installed. The high-detail `pc01bod`
candidate is the visual style anchor, but its own registration and portrait identity still need review.
Relevant target ids are `engine--icons--pc01bod.bmp`, `pc01lhu.bmp`, `pc01lho.bmp`, `pc01rhd.bmp`,
`pc01rhu.bmp`, and `pc01rhb.bmp`.

The first whole-sheet generation produced six exact-size parts with genuine alpha, but all six failed
registration. A separate grip-hand retest also changed its width/height relationship. An in-place `pc01lhu`
open-arm attempt passed alpha registration but its hand looks soft and its brown bracer differs from the
body's red bracer. A shield-hand attempt became too narrow. A later shared-bracer shield hand passed
registration, and a full-context imagegen pass reproduced red bracer material but curled the open fingers
and expanded the alpha-16 area to 1.124× the native area (over the 1.10× guard).

The current unapproved material trials combine that red bracer paint with the registered open-arm alpha,
then transfer corresponding bracer colors to the registered shield-arm geometry. They pass registration and
are illustrated with sword #1 and shield #99, but **the open-hand fingertips still end flat at the sprite
bottom**. The exact 2× open-arm canvas is 52×108; the native 26×54 file already has 11 alpha-128 pixels on
its last row, and the current open-arm trial has 32. The cut is not browser scaling. First determine whether
the intended complete fingers can fit within the fixed logical canvas while retaining the elbow/cuff offset.
If not, an explicit canvas/placement contract change would be needed; do not quietly enlarge this one icon
and call it plug-and-play.

`test_img/2036.png` shows another separate problem: the screen-left open arm is the unchanged
`pc01rhd` **raw prepared candidate**, whose hand is jagged and has colored edges. The prior generated
`pc01rhd` from the six-part sheet failed registration, so no usable restored right-open arm exists yet.
The soft screen-right hand in that image is the generated in-place `pc01lhu` itself. In `test_img/2037.png`,
the left open hand is cut by its canvas, the middle shield hand is an older artifacted batch candidate, and
the right shield hand is a newer unapproved trial. That three-panel diagnostic omitted the opposite arm;
it was never a complete-doll proof. The PC01 page now labels these states and puts old comparisons in a
collapsed section. The right-hold/finger overlays `pc01rhu` and `pc01rhb` also need coherent finishing.

**Do not scale the PC01 trial across all dolls yet.** First obtain a visually coherent, properly bounded PC01
empty-hand pose and matching main-hand, two-hand, and shield states, then review it with the assigned avatar,
backgrounds, and equipped items. Only after that method passes visual and geometry checks should the session
process other dolls one at a time or in compatible groups.

## Next session sequence

1. Read this handoff, the [browser README](README.md), and the
   [identity method/results](identity_workflow/README.md). Open the main and PC01 review pages. Run the
   focused verifier before changing candidates:

   ```sh
   python3 -B level_generation/ui/hud_inventory/paperdoll_review/verify.py
   ```

2. Reproduce PC01's original and candidate assemblies at table offsets. Resolve the `pc01lhu` bottom crop and
   the unfinished `pc01rhd` open arm; then finish `pc01rhu`/`pc01rhb` and the shared shield/open bracer states.
   Preserve source/trial provenance. Do not mark the current red-bracer trial approved just because its alpha
   registration passes.
3. Present a **complete** PC01 doll with all relevant limb states, assigned original avatar, correct background
   toggle, and one-hand/shield/two-hand loadouts. Keep component/source labels visible so no raw or native
   fallback is mistaken for a finished 2× piece. Obtain visual decisions for the actual selected files.
4. Apply the validated method across available dolls and inspect the 906 fitted variants in their resolver
   contexts. Keep related armor/cape variants together, review `vN` and `vNa` poses as a family, and prioritize
   clipped hands, alpha/color spill, missing fingers, mismatched bracers, and items that shift at game offsets.
5. Export browser review JSON, reconcile each decision against the current source and candidate hashes, and
   prepare targeted repairs for flags. Only then use the canonical queue's measured compare/accept/reconstruct/
   stage flow with actual review images. `queue.py` and [QUEUE.md](../QUEUE.md) define those gates. Staging is
   separate from installing assets under `assets_dev/*/icons_x2`.

The shared workspace has substantial unrelated work in progress. Keep changes in this paperdoll slice and
inspect the live checkpoint before any queue mutation; do not reset, overwrite, or reaccept another session's
assets. The original files under `assets_dev/engine/icons/` are the immutable comparison baseline for this
review. Regenerating `build.py` output is only necessary when authoritative tables, frozen targets, candidate
selection, or source manifests change; it does not preserve browser-only decisions unless they were exported.
