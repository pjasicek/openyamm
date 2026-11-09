# Approved Carved Obsidian journal — staged integration package

**Journal revision 01, approved 28 September 2026.** This is the accepted map, quest, story and six-category
autonote design, plus the separate 2090 readiness-strip treatment. It follows the
[approved overlay package](../../obsidian_overlays_20260928/staging/README.md).
The subsequent user-requested text refinement uses justified body paragraphs, with natural left-aligned final lines.
The original left-aligned approval/captures remain in `history/r01-left-aligned/` for comparison.
The 2105 spacing refinement gives the text a 28.07-logical gap to the submenu column, using a 360-logical-wide body.
Its preceding layout is preserved under `history/r01-before-wider-gutter/`.

[Staged asset sheet](http://127.0.0.1:8899/level_generation/ui/obsidian_journal_20260928/staging/index.html) ·
[Interactive approved screens](http://127.0.0.1:8899/level_generation/ui/obsidian_journal_20260928/index.html) ·
[Integration notes](INTEGRATION.md) · [Validation](validation.json)

| Location | Prepared contents |
| --- | --- |
| `engine/icons_x2/` | 40 PNGs: blank journal skin, 20 button plates, 10 transparent icons, four navigation glyphs, map-note strip, transparent map frame, dark backdrop tile, entry divider and blank status strip. |
| `engine/ui/gameplay/journal.yml` | Draft preserving every original ID and input target, the exact map viewport, measured button children and live text. |
| `engine/fonts/` | Book2, Autonote, Create, Smallnum and Lucida TTF/FNT pairs; Fondamento outline font, descriptor and OFL license. |
| `design/` | Palette, font sizes, map geometry, backdrop tiling, button states and required live bindings. |
| `approved_previews/`, `approval.json` | Accepted screen captures and approval receipt. |
| `masters/` | Frozen browser recipes, measured geometry, original icon prompts and generation/source receipts. Original icon masters also remain in `../assets/generated/`. |
| `reference_layouts/`, `reference_fonts/` | Original journal layout and faithful descriptors for rebasing before installation. |
| `manifest.json`, `asset_receipts.json` | File hashes, dimensions, alpha and intended `assets_dev/engine/` destinations. |

This package is prepared for later runtime integration and is **not mounted**. No runtime code, assets, settings or
saves were changed. Preparation does not add files to Git's index. The source script rejects unrecorded graphic changes
and changed pinned references; rebase the layout against current gameplay before installation.

All artwork is the accepted browser artwork. The additional finishing PNGs isolate existing decoration with live text,
map pixels and labels removed; they introduce no new visual design. Icons retain their original transparent masters.
The package keeps dynamic map output and unlocked journal content in the engine; review fixtures are not runtime assets.

Autonote's staged descriptor changes only `presentation: black-ink` to the engine's existing `tintable` mode, so it can
draw soft ivory. Native outlines, FNT spacing, cell height and baseline remain unchanged. The original descriptor is
archived. Other reading faces keep their original descriptors, and Fondamento reuses the prior overlay package.
The exact reviewed Create outlines differ from the current runtime/overlay package; the difference is recorded in
[runtime_font_differences.json](runtime_font_differences.json). Reconcile that font change during integration before
copying global font files. The approved preview is preserved rather than silently refreshed from a changed source.

Validation checks the actual layout parser, asset references, all five button states, native geometry/fonts,
transparent map interior, original IDs, file hashes and preserved runtime sources. The interactive review has 42 passing
browser checks. These checks validate a design handoff; they do not claim native-game rendering has been implemented.
Native justification is an explicit renderer requirement: the YAML draft stays compatible with the current parser,
which presently supports only left, centre and right alignment.

To rebuild from the already-exported approved art:

```sh
python3 level_generation/ui/obsidian_journal_20260928/prepare_drafts.py
python3 level_generation/ui/obsidian_journal_20260928/staging/prepare_stage.py
python3 level_generation/ui/obsidian_journal_20260928/staging/validate_stage.py
```

To deliberately re-export the browser recipes first, use
`node level_generation/ui/obsidian_journal_20260928/check_browser.mjs`, then those three commands.
Check approved source hashes before replacing a historical capture.
