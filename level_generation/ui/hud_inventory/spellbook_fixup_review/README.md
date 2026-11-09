# Spellbook reconstruction review

[Open the interactive review](http://127.0.0.1:8900/level_generation/ui/hud_inventory/spellbook_fixup_review/).
**Accepted and installed:** the user approved final revision **`e1c5265ae12b808b`**, including the stronger Air icons
and shared school bookmarks. [The publication](../spellbook_acceptance_20260927/README.md) replaces 258 accepted
records, updates the canonical ledger/index, and installs their exact PNG bytes into `assets_dev/engine/icons_x2`.
The five default-state canvas changes are explicit export migrations. The browser now shows **Accepted** and
keeps **Before fixups** and **Previous strength** for comparison. `acceptance.json` binds this status to the receipt;
the final pre-publication browser and evidence are frozen under `revisions/e1c5265ae12b808b/`.

The user had previously approved all 12 reconstructed pages and 111 spell pairs on 2026-09-27:
“OK spell icons and spellbooks are good”. Their artifact hashes are pinned in
[`approved_pages_and_spells.json`](approved_pages_and_spells.json), and the approved
[colour revision](revisions/b7532430dadb3451/index.html) is archived with its browser-local review notes.
The earlier accepted files and receipts are retained. Runtime code and YAML remain unchanged.

**Air opacity revision 4:** the earlier Air workflow multiplied the entire foreground alpha by 0.75 for eight
spell pairs, and by 0.85 for Air Resistance. This attenuation was inherited by the runtime PNGs and both states
of the stable-shape preview. The trial reverses those recorded multipliers in 18 new images under `air_opacity/`.
Sparks and Starburst already use full strength. All RGB pixels, canvases, occupied pixels, glyph masks, palettes,
book pages and bookmarks retain their previous values. Fractional edge/effect alpha remains fractional; this is
not an opaque cutout or a new drawing. [Compare the nine pairs](evidence/air_strength_comparison.png).
The [previous revision](revisions/5d48e77d7231f60b/index.html?school=Air) is archived. Its nine affected approvals
were reopened during the trial, then accepted by the final instruction recorded in the publication above.

**Bookmark revision 3:** following `test_img/2049.png`, all school tabs use one retained parchment bookmark,
matched to the book's paper. Only the school emblem inside the shared circular frame changes. The default ink
drawings and selected colour illustrations come from the existing tabs. The approved pages and spell pairs are
unchanged byte for byte. [Compare all twelve bookmarks](evidence/bookmark_comparison.png).

**Colour revision 2:** following `test_img/2048.png`, the default appearance now learns the palette and contrast of
each installed default icon. This restores reddish-brown midtones, dark ink and pale highlights that the first
generic sepia ramp flattened. The [first preview](revisions/ad96b0d7605b8e44/index.html), its assets, manifest and
browser-local notes are retained separately. Existing backgrounds, highlighted drawings and glyph masks are unchanged.

The page includes all 12 schools, all 111 spell pairs, the 12 school tabs and the three bottom-left controls.
Positions, logical sizes, anchors and state bindings are read from `assets_dev/engine/ui/gameplay/spellbook.yml`.
The logical book is 640 × 480; the review renders it at 1280 × 960 and scales the complete view to fit the browser.
The game’s Lucida font is used for the caster and selected-spell labels.

## Interaction

- Hover a spell to colour it; click to keep it selected. Click the paper or **Clear selection** to deselect.
- School tabs switch pages. The selected school uses the YAML pressed image, as in the game.
  In proposed mode, these bindings use the shared-bookmark composites. Hovering an inactive tab retains its ink state.
- The bottom-left buttons simulate setting a quick spell, setting an attack spell, and closing the book.
  Assigning the same spell again clears it. Double-clicking a spell simulates casting and closes the book.
- Switch **Accepted / Before fixups**, or press **B**, to compare in the same layout.
- Air opens by default. In accepted mode, **Restored strength / Previous strength** compares only the Air opacity
  correction while retaining the same book, bookmarks, palette, drawing and current spell selection. This switch
  applies to the main page and the detail preview. `?school=Air&air=previous` opens the earlier strength directly.
- **Background only** exposes the entire page while retaining the side controls. Arrow keys change schools.
- Right-click a spell or control to review it. The review selector also includes the current page.
- Hover the detail preview or use **Alternate** to examine normal/highlighted or normal/pressed states.
- **Looks good**, **Needs work** and notes persist in browser local storage, separated by artwork revision.
  **Export review** saves JSON with artwork hashes. Import accepts the matching revision and preserves newer notes.
  All 135 page/spell/bookmark targets carry their final explicit approval. Earlier local flags are superseded by
  that decision while keeping their notes and previous decision; feedback created after acceptance remains local.
  Clearing a new note on approved artwork restores its approval. Both Air-state hashes are included in the export.

All spells and schools are available in this visual fixture. Casting and assignments are simulations; the page does
not modify a party or save. The three bottom-left controls retain their installed artwork and state bindings.
Hit testing uses the game’s rectangular regions and target priority; overlapping spell rectangles retain the runtime
draw behavior. Browser font rasterization and filtering can differ slightly from bgfx.

## Candidate construction

`prepare.py` originally snapshotted installed inputs in `installed/`, with source hashes in `manifest.json`.
It now refuses to regenerate this accepted revision. Preserve these files and create a separate revision for
future changes. `installed/` is the retained original review baseline; its name does not imply current runtime art.

- **Book:** the accepted Fire page supplies the common paper, borders, spine and outer medallion ring.
  Its circle interior and nameplate are cleared using clean paper from that same page. Each retained school
  illustration is sampled into one fixed antialiased circular mask. A shared rounded nameplate and consistently
  curved labels complete the frame. The label lettering is rasterized from DejaVu Serif Bold; its font hash is recorded.
  The proposed pages are identical outside `layers/variable_mask.png`. No imagegen call was made.
- **Spells:** each installed highlighted image supplies the only drawing and transparency for that spell.
  A per-spell colour lookup table learned from its installed default creates the normal appearance. Alpha-weighted
  luminance distributions match the ink contrast; the reference’s RGB-minus-luminance offsets recover its actual
  colour at each brightness. Only colour statistics are transferred, so none of the reference’s different outlines
  or internal geometry is copied. The 256-entry RGB tables are retained under `palettes/`. Native normal-state green
  locates the glyph region, and a chroma mask preserves its green fill without preserving rectangular paper patches
  or neighbouring coloured effects. The selected artwork and alpha are never repositioned, rescaled or repainted
  between the two proposed states.
- **School bookmarks:** `bookmarks.py` clears the Dragon tab's interior to make one master. Its retained parchment,
  edge and rim are gently matched to a clean paper sample from the approved shared book. The interior uses that
  same paper sample. Fractional alpha left by the old matte removal is closed inside the opaque medallion once,
  in the master. Measured source ellipses locate each existing emblem inside its own old rim; those interiors are
  mapped into one fixed antialiased mask. Inactive outlines are extracted as sepia ink so their former parchment
  does not come along. Selected emblems keep their colour illustrations and inner colour fields. This preserves
  the existing ink/colour distinction while removing variation in the bookmark and frame. All 24 state images have
  identical alpha and identical pixels outside the emblem mask. `bookmarks/master.png`, `bookmarks/emblem_mask.png`
  and `bookmarks/emblems/` retain the reusable layers. No new image generation is involved.
- **Air strength:** `air_opacity.py` verifies each faded highlighted source against its retained Air ink PNG and
  reads the exact multiplier from that assembly's `processing.json`. The new alpha is
  `round(min(255, previous_alpha / ink_opacity))`; this reverses the global attenuation to the precision of the
  previously quantized alpha. Both current colour/normal states receive the same correction, without relearning
  palettes or changing RGB. The original `canonical` and `proposedNormal` records remain the approved baseline;
  each affected spell's `opacityTrial` explicitly records the two new derivatives and processing provenance.
- **Canvas exceptions:** Inferno, Jump, Earth Resistance, Rock Blast and Enslave have differently sized original
  state canvases. The preview uses each highlighted canvas for both proposed states, drawn into the unmodified
  YAML rectangle. The derived normal files are explicitly review artifacts, not replacements for the old normal
  files under their frozen native contracts. A future shared-renderer implementation can apply the colour treatment
  to one canonical texture and the retained mask, preserving the same sampling in both states.

The browser uses the precomputed colour derivative for reproducible visual comparison. `recipe` in the manifest
records the exact colour transform and compositing parameters. `pages/`, `icons/`, `masks/`, `palettes/`, `bookmarks/`,
`air_opacity/` and `layers/` retain the
candidate assets; `data.js` embeds the manifest so the page requires only a static server.

## Reproduce and verify

From the repository root, with Pillow, NumPy, SciPy and PyYAML available, verify the retained review and installation:

```sh
node level_generation/ui/hud_inventory/spellbook_fixup_review/test_browser.mjs
python3 -B level_generation/ui/hud_inventory/spellbook_fixup_review/validate.py
python3 -B level_generation/ui/hud_inventory/deploy_icons.py --check
python3 -B level_generation/ui/hud_inventory/spellbook_acceptance_20260927/validate.py
```

The browser check launches its own headless Chrome with a fresh temporary profile. It exercises all school tabs,
hover, selection, all three bottom buttons, comparison, saved notes, export/import and a narrow viewport. It records
screenshots and `evidence/browser_checks.json`. Validation checks all recorded input hashes, candidate hashes,
unchanged background pixels and exact alpha/canvas equality for every spell. It also compares the captured normal
and hovered Fire Aura frames to confirm that only its drawing rectangle changes. All 24 bookmark states are checked
against actual browser canvas pixels, and validation reconstructs every tab from its master and emblem layer. The
123 previously approved targets are verified against both their archived revision and the approval receipt.
The Air trial checks exact RGB and footprint preservation, identical alpha in both states, and the correction
against the historical multiplier. Its browser comparison must reproduce the archived Air page exactly at
previous strength; restored strength may change only the nine affected spell rectangles. Hover and selection
are exercised in the stronger variant, including keeping a selected spell while toggling the comparison.

The repository server on port 8900 serves this page. If that server is stopped, start a repository-root
static server with `python3 -u -m http.server 8900 --bind 127.0.0.1 --directory /home/pjasicek/github/OpenYAMM`.

Retain the accepted manifest, decisions and artwork before producing another revision. Deploy from the current
`accepted_icons.json` using `deploy_icons.py`; older dated snapshots must not overwrite this acceptance. The normal
and highlighted exports already implement the reviewed colour treatment in the shared UI without a renderer change.
