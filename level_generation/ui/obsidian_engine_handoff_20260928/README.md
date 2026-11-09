# Obsidian integration package

The user authorized wholesale native integration on 2026-09-28. The shared gameplay HUD and overlay collection are
now installed under `assets_dev/engine`, with matching native drawing and input. Start with
[NATIVE_INTEGRATION.md](NATIVE_INTEGRATION.md) and [the native capture gallery](native_review/index.html).

The [2129 refinement](refinement_2129/README.md) has its own [native gallery](refinement_2129/index.html):
one slim shared resource/command bar, a raised minimap without a location label, restored Obsidian hero/skull party-buff
panels, and green/yellow/red HP meters. Ordinary buffs no longer use the timed strip; it remains available for future
special modifiers. This supersedes those parts of the earlier native gallery and browser mockups.

The earlier [2130 correction](refinement_2130/README.md), with its [native gallery](refinement_2130/index.html), anchors
the bar at (0,0), fixes the gold inset and removes the outer bar/minimap shadows. New true-alpha buff atlases replace
the old contaminated overlays. Skull effects follow the archived desktop mapping; Torch Light owns the glow, while
Stoneskin replaces the skull material without hiding other active effects.

The latest [dynamic party basebar](refinement_party_basebar/README.md) and its
[native review](refinement_party_basebar/index.html) add a shared frame sized to the party, carved exterior
ornaments and vertical HP/mana tracks. The accompanying [2131–2132 changes](refinement_2132/README.md) add smaller
uniform gems, a buff-panel inset, minimap time/subtle shading and the right-edge followers head/panel. Fly,
Levitate and Water Walk use separate animated indicators and no longer appear on the skull.

The original [browser review](index.html), [handoff contract](INTEGRATION.md), `engine/` payload and
`reference_runtime/` snapshots remain preserved design/rebase material. Their original staging checks describe
pre-integration state; they are not native acceptance tests.

This consolidates the approved gameplay **Obsidian r04**, fullscreen **Carved Obsidian r06**, **overlay r03**, and
**journal r01** with justified text and the wider submenu gutter from 2105. Gameplay now has component PNGs and its own
replacement layout, including all party counts, compact buff overflow, readiness states and circular minimap geometry.
Fondamento is used for buttons; recreated MM fonts and soft ivory remain the reading choice.

The installed **2116 status/input revision** removes the upper basebar ornament and enlarges the reading rail.
The browser includes short/long status, editable bank deposit/withdraw and Alamos password examples. That refinement is
also implemented in the native HUD. The rest of the carved frame retains its previous artwork. See
[the exact imagegen prompt and source](basebar_generation.json); the built-in imagegen tool produced the edited rail.

Native refinements from 2121–2127 include smoother small icons and Fondamento labels, larger scrollable skills,
framed awards, the compact rest screen without an hourglass, and the original dialogue topic font. The final size
adjustment uses **10% larger gameplay portraits** and a **112 logical-pixel minimap** (slightly reduced from the first
native refinement). Portraits also sit lower with a larger gap above their bars and no condition labels. The mounted YAMLs are authoritative for these later changes.

Contents:

- `engine/icons_x2/`: merged art, all button states, true-alpha inspector slices, fixed-scale reading surfaces,
  22 glyph-free buff illustrations and the new gameplay pieces. Names, values, portraits and maps stay live.
- `engine/ui/gameplay/`: replacement candidates for gameplay, character pages, dialogue, rest, quick reference,
  journal, chest chrome and six inspector/detail layouts. See `coverage.json` for retained companion screens.
- `engine/fonts/`: Fondamento plus current recreated MM faces, their metrics and license; font-version decisions
  are explicit in `font_resolution.json`.
- `design/`, `hud_exports.json`, `hud_geometry.json`: geometry, state, slicing, input and rendering contracts.
- `manifest.json`, `runtime_dependencies.json`, `legacy_id_migration.json`: targets, hashes, native content
  dependencies and the exact legacy/new layout-ID boundary.
- `previews/`, `sources/`: visual review and provenance. These are not runtime payload.

Historical staging commands (reproduce the original handoff, not the current native implementation):

```sh
node level_generation/ui/obsidian_engine_handoff_20260928/export_hud.mjs
python3 level_generation/ui/obsidian_engine_handoff_20260928/prepare.py
python3 level_generation/ui/obsidian_engine_handoff_20260928/validate.py
```

`prepare.py` refuses conflicting layout changes. The old `validate.py` checks staging assumptions that intentionally
predate installation. Do not copy the archived candidates over the mounted layouts. `obsidian-runtime-preparation.zip`
preserves the original payload, contracts, receipts, snapshots and previews; it is a design archive, not a replacement
for the installed assets and shared render/input code. Current build, test and native capture evidence is recorded in
[NATIVE_INTEGRATION.md](NATIVE_INTEGRATION.md).
