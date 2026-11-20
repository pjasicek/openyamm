# MM8 spell, UI and MM6–MM8 NPC portrait review

The [rebuilt transparent spell foreground stage](spell_foreground_stage_v2/index.html) covers all 111 spell pairs
(222 states). It compares each native original and prior 2× candidate with a genuine-alpha 2× foreground and records
independent approve/flag decisions for each state. The user approved all 222 states, recorded in
`spell_review_acceptance.json`, and their exact 2× PNGs are copied to `staged_spell_icons/engine/icons_x2/`.
The [stage notes](spell_foreground_stage_v2/README.md) explain the full-master recrops and paper-removal batches.
The earlier spell stage is superseded because some previews lost glyphs or neighboring content during extraction.
The approved foregrounds are staged for later integration; runtime art and the older HUD queue are unchanged.

Open [index.html](index.html) in a browser. The catalog works from a local file; no server is needed. If the
browser restricts local image loading, start `python3 -m http.server 8765 --bind 127.0.0.1` at the repository root
and open `http://127.0.0.1:8765/level_generation/ui/mm8_art_review/`.

The page compares each native original with an individual exact-2× restoration PNG. The default view fits large
images into the card; choose 2×, 3× or 4× display scale to inspect pixels, or click an image for a larger comparison.
Filter by category, world, candidate status, decision or name. Approve or flag candidates, add reasons and notes,
then download or copy the review JSON. You can import that JSON later to continue. Loading screens and NPC portraits
have source- and candidate-bound visual approvals in `review_acceptance.json`; spell icons use
`spell_review_acceptance.json`. New browser flags and notes stay local. These visual approvals do not change the
restoration checkpoint or install artwork in the game. A changed source or candidate hash invalidates its approval.

Scope is derived from `expected_targets.json` and the second-pass runtime usage overlay. The catalog has 2,376
entries: 222 MM8 spell icon states, 12 pages named by the active spellbook layout, 17 loading assets (six full-screen
names, `bardata`, and ten hourglass animation frames), 382 active shared UI button states, and all 1,743 NPC dialogue
portraits across the engine and MM6/MM7/MM8 icon roots. The unreferenced `loading01` and alternate spellbook pages
are outside this active-runtime selection. PC portraits are excluded because a separate second pass owns them.

All 2,376 catalog assets now have an exact-2× candidate. The Body Magic page `sbb000` uses the local
Real-ESRGAN x4plus model on its complete native page; the 4× master was downsampled with Lanczos to its exact 2×
canvas. The image generation tool had rejected a prior faithful edit of its historical medallion. The Real-ESRGAN
master, model hashes, final PNG and method record are in `sbb000_esrgan/`.

The originals are full-resolution PNG decodes of the untouched bitmap sources, using the target's renderer
transparency profile. Their source paths and hashes are in the catalog. Existing candidate artifacts are linked
from the restoration checkpoint and returned bundles without copying or changing them. For gaps in those bundles,
this directory keeps new imagegen master sheets and provisional exact-2× extractions. The sheet references,
layouts, prompts, raw images and per-candidate manifests are next to the generated previews. These provisional
previews still need individual identity, placement, alpha, lettering, animation and state-pair review.

### NPC review repairs

The first NPC gallery used nominal input-sheet rectangles to cut new generated sheets. The returned opaque sheets
compressed their row spacing, so later-row previews such as `npc1531`, `npc1534` and `npc1541` contained a strip of
the next row. `extract_generated_npcs.py` now measures each returned portrait against the dark gutters and records
its actual crop and edge confidence in `generated_npc_candidates/manifest.json`. It recropped all 139 opaque
portraits from those sheets. The 12 irregular cutouts remain separate and still need silhouette review.

Many older returned portraits had an isolated purple sheet-matte border, including `npc0499`. The browser now
defaults to a review-only cleaned variant for 1,372 portraits. The second edge pass also removes a one-pixel frame
when legitimate purple clothing or background continues farther inward. Choose the candidate selector to see the
untouched return. `cleaned_npc_edges/manifest.json` records both hashes and the measured border depth; its former
12 ambiguous portraits were checked against the native art and the frame was removed. The cleanup copies neighboring
interior edge pixels; it does not change the original return or runtime assets.

### Category visual approvals

The user approved all 17 loading assets and 1,743 NPC portraits after a final magenta-edge check. All 17 loading
assets have zero saturated-purple pixels in their outer three pixels. Seven nearly transparent magenta key pixels in
six small loading animation frames were cleared in review-only variants, leaving zero magenta key pixels. The selected
NPC candidates have no remaining
strong one-pixel rectangular magenta frame relative to their native originals. Purple clothing, hair, sky and the
native magenta backdrop in `npc0320` remain legitimate artwork. `accept_review_categories.py` verifies source and
candidate hashes, exact 2× sizes and these edge conditions, then writes `review_acceptance.json`. The catalog shows
these as **Art review approved** while leaving pipeline acceptance and game assets unchanged.

### Approved spell foregrounds

All 222 transparent spell icon states passed the user's visual review. `accept_spell_foregrounds.py` verifies each
native source hash, candidate hash, exact 2× RGBA size and genuine alpha, then copies the approved PNG into
`staged_spell_icons/engine/icons_x2/`. The staging manifest and `spell_review_acceptance.json` bind every copy to
the exact v2 candidate. The catalog selects these candidates first and shows **Art review approved**. This staging
does not replace prior accepted Air artifacts in the HUD queue or install files under `assets_dev/`.

### Spellbook page approvals

The user approved all 12 active spellbook pages. Eleven use their existing exact 2×, opaque, hash-verified
restorations; `sbb000` uses the new Real-ESRGAN candidate. `accept_spellbook_pages.py` verifies the source,
candidate and Real-ESRGAN provenance hashes, then copies all 12 to `staged_spellbook_pages/engine/icons_x2/` and
records their visual approval in `spellbook_review_acceptance.json`. The older HUD checkpoint and runtime assets
remain unchanged.


### MM6 Free Haven Oracle council identity repairs

The eleven flagged body portraits `npc0002`, `npc0004`–`npc0005`, `npc0007`–`npc0008`, `npc0010`–`npc0011`,
`npc0013`–`npc0014`, and `npc0016`–`npc0017` now have new review-only 2× candidates. Their companion avatars
`npc0003`, `npc0006`, `npc0009`, `npc0012`, `npc0015`, and `npc0018` are unchanged. The body edits match the
companion faces, remove the invented glasses from `npc0010`–`npc0011`, and give `npc0013`–`npc0014` a boy's face
and flat shirt/vest. The extraction retains each prior body's exact alpha silhouette and its outer two pixels, so
the generated sheet's dark glow stays outside the cutout. Previous candidates remain selectable for comparison.

[Open the eleven repairs](index.html?artwork=council) to compare native art, the new 2× body, and its matching avatar
in one card. These candidates carry the category visual approval; they are not installed in game assets. The references, prompts,
raw generated sheets, exact crop layouts, candidate hashes, and per-group comparison boards are in
`council_body_repair/`. Run `extract_council_repair.py`, then `build_catalog.py` to reproduce the previews.

The new NPC and paired-spell imagegen prompt sets are in `missing_npc_sheets/*/prompt.txt` and
`missing_spell_sheets/*/prompt.txt`. The full-screen loading masters follow the same faithful-restoration request:
retain the source composition, figures, palette, framing and loading-bar placement without new elements or text.
All new masters were made with the built-in image generation tool; exact-2× previews were cropped or resized from
those masters. To refresh the catalog after source records or extractions change, run:

```sh
python3 level_generation/ui/mm8_art_review/build_catalog.py
```
