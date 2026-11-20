# Spellbook reconstruction review

[Open the interactive review](http://127.0.0.1:8899/level_generation/ui/hud_inventory/spellbook_fixup_review/).
This is the user-requested follow-up to the accepted x2 spellbook artwork. It contains candidates, not new approvals.
The installed artwork, acceptance records, runtime code and YAML remain unchanged.

The page includes all 12 schools, all 111 spell pairs, the 12 school tabs and the three bottom-left controls.
Positions, logical sizes, anchors and state bindings are read from `assets_dev/engine/ui/gameplay/spellbook.yml`.
The logical book is 640 × 480; the review renders it at 1280 × 960 and scales the complete view to fit the browser.
The game’s Lucida font is used for the caster and selected-spell labels.

## Interaction

- Hover a spell to colour it; click to keep it selected. Click the paper or **Clear selection** to deselect.
- School tabs switch pages. The selected school uses the YAML pressed image, as in the game.
- The bottom-left buttons simulate setting a quick spell, setting an attack spell, and closing the book.
  Assigning the same spell again clears it. Double-clicking a spell simulates casting and closes the book.
- Switch **Proposed / Installed**, or press **B**, to compare in the same layout.
- **Background only** exposes the entire page while retaining the side controls. Arrow keys change schools.
- Right-click a spell or control to review it. The review selector also includes the current page.
- Hover the detail preview or use **Alternate** to examine normal/highlighted or normal/pressed states.
- **Looks good**, **Needs work** and notes persist in browser local storage, separated by artwork revision.
  **Export review** saves JSON with artwork hashes. Import accepts the matching revision and preserves newer notes.

All spells and schools are available in this visual fixture. Casting and assignments are simulations; the page does
not modify a party or save. Button artwork is included unchanged, so existing button-state differences remain visible.
Hit testing uses the game’s rectangular regions and target priority; overlapping spell rectangles retain the runtime
draw behavior. Browser font rasterization and filtering can differ slightly from bgfx.

## Candidate construction

`prepare.py` snapshots the current installed inputs in `installed/`, with source hashes in `manifest.json`.
It does not overwrite the accepted sources or modify the live restoration ledger.

- **Book:** the accepted Fire page supplies the common paper, borders, spine and outer medallion ring.
  Its circle interior and nameplate are cleared using clean paper from that same page. Each retained school
  illustration is sampled into one fixed antialiased circular mask. A shared rounded nameplate and consistently
  curved labels complete the frame. The label lettering is rasterized from DejaVu Serif Bold; its font hash is recorded.
  The proposed pages are identical outside `layers/variable_mask.png`. No imagegen call was made.
- **Spells:** each installed highlighted image supplies the only drawing and transparency for that spell.
  A deterministic luminance-to-sepia colour transform creates the normal appearance. Native normal-state green
  locates the glyph region, and a chroma mask preserves its green fill without preserving rectangular paper patches
  or neighbouring coloured effects. The selected artwork and alpha are never repositioned, rescaled or repainted
  between the two proposed states.
- **Canvas exceptions:** Inferno, Jump, Earth Resistance, Rock Blast and Enslave have differently sized original
  state canvases. The preview uses each highlighted canvas for both proposed states, drawn into the unmodified
  YAML rectangle. The derived normal files are explicitly review artifacts, not replacements for the old normal
  files under their frozen native contracts. A future shared-renderer implementation can apply the colour treatment
  to one canonical texture and the retained mask, preserving the same sampling in both states.

The browser uses the precomputed colour derivative for reproducible visual comparison. `recipe` in the manifest
records the exact colour transform and compositing parameters. `pages/`, `icons/`, `masks/` and `layers/` retain the
candidate assets; `data.js` embeds the manifest so the page requires only a static server.

## Reproduce and verify

From the repository root, with Pillow, NumPy, SciPy and PyYAML available:

```sh
python3 -B level_generation/ui/hud_inventory/spellbook_fixup_review/prepare.py
node level_generation/ui/hud_inventory/spellbook_fixup_review/test_browser.mjs
python3 -B level_generation/ui/hud_inventory/spellbook_fixup_review/validate.py
```

The browser check launches its own headless Chrome with a fresh temporary profile. It exercises all school tabs,
hover, selection, all three bottom buttons, comparison, saved notes, export/import and a narrow viewport. It records
screenshots and `evidence/browser_checks.json`. Validation checks all recorded input hashes, candidate hashes,
unchanged background pixels and exact alpha/canvas equality for every spell. It also compares the captured normal
and hovered Fire Aura frames to confirm that only its drawing rectangle changes.

The existing repository server on port 8899 serves this page. If that server is stopped, start a repository-root
static server with `python3 -m http.server 8899 --bind 127.0.0.1`.

After this candidate is reviewed, retain its manifest, exported decisions and artwork before producing another revision.
Do not rerun an older accepted installer over a future approved repair. Integration into game assets and the shared
UI colour treatment are subsequent steps following this review.
