# Obsidian engine handoff

**Native activation completed after this handoff was prepared.** See [NATIVE_INTEGRATION.md](NATIVE_INTEGRATION.md)
for the mounted implementation, migration decisions and verification. The sections below preserve the original
handoff requirements. Its mobile gating was superseded by the user's explicit request to use desktop UI on Android
and defer additional touch buttons.

The newest fullscreen status revision addresses **2116.png**. Its empty rail is 22.4 logical pixels tall, with a
454.933333 × 17.066667 text region. `obsidian_hud_fullscreen_basebar` supersedes `obsidian_basebar` for this package.
Only the upper rail samples the imagegen edit. The carved body/right panel and the top bar retain the approved sources.
This is a requested refinement, prepared for review; it is not retroactively labelled as an earlier approval.

## Install in coherent steps

1. Compare `reference_runtime/ui/gameplay` with the current mounted layouts. This package was rebased on those
   snapshots; `layout_rebase.json` records preserved current changes. Resolve later edits by ID before installation.
2. Add the `engine/icons_x2` payload to base-owned `assets_dev/engine/icons_x2` with existing icon package precedence,
   lowercase names and 0644 permissions. Add the candidate `engine/ui/gameplay` files only with matching renderer/input
   work. The historical `obsidian_basebar` entry has `install: false`; the replacement is
   `obsidian_hud_fullscreen_basebar`. Do not install `sources`, `previews`, fixture names, captured map art or browser
   sample values as content.
3. Register Fondamento through the existing independent TrueType loader, as the current menu renderer already does.
   `GameplayHudCommon::loadHudFont` needs the same supported path. Keep recreated MM faces and native FNT advances for
   reading roles. `design/fonts.yml` gives the consolidated file paths and takes precedence over the historical
   hyphenated filenames. `font_resolution.json` preserves the newer Create font instead of the older journal preview copy.
   Autonote changes from black-ink to tintable for ivory reading; inspect any additional consumers before mounting it.
4. Make a single shared desktop HUD path resolve the new layout for both former Standard/Widescreen choices.
   `gameplay.yml` intentionally removes legacy strip/tableau/ornament roots; use `legacy_id_migration.json` to retire
   named renderer lookups and input branches together. Do not retain an invisible clickable skull, doll or old button.
5. Render the new live PC templates, horizontal meters, padded rim art, selection, readiness and personal-buff hit
   targets. Use dynamic party count 1–5. Draw PC names in gameplay, hide them in the fullscreen basebar. Do not reuse
   ManaFRM/selring or resurrect FACEMASK. Apply viewport anchors and collision rules from `design/gameplay.yml`.
6. Replace the body/skull effects renderer with the 22-entry enum mapping and stable sorted strip. Add counted overflow,
   popup scrolling and owner-specific personal effects. Retain all existing effect mechanics and inspection data.
7. Clip the native minimap and markers to the circle, preserving reveal/Wizard Eye rules and zoom limits. Keep its live
   location/name/heading. Bind the existing follower toggle, slot and scrolling actions to the new button and popup.
8. Finish overlays using the frozen per-package contracts under `design/` and `sources/*/INTEGRATION.md`. The current
   consolidated contract takes precedence over historical instructions. Draw live content on the correct surface;
   implement fixed-corner/repeated-edge inspector frames, measured dialogue height and bounded font fallback.
9. Add native paragraph justification for journal body text after wrapping with native advances. Keep final paragraph
   and single-entry lines left aligned; justify a line continuing to the next page. The YAML uses supported `left`
   plus an explicit note, because `justify` is not yet a supported parser field. Keep the 28.066667 submenu gutter.
10. Bind fullscreen status and input to the clear rail. The current bank controller builds entry into dialog lines;
    move only its presentation to this shared host when intended, keeping bank transaction validation. Event/password
    entry retains the same event callback and text buffer. Active editing outranks hover/events, and the caret stays
    visible while long input scrolls horizontally. Remove the hardcoded `Ui-FrSp` draw in the overlay status path.
11. Migrate `gameplay_mobile.yml` explicitly before enabling the new HUD on Android. Its current snapshot refers to
    removed legacy roots. Preserve touch movement, inspect mode and all action/flight controls. This package does not
    claim a newly approved mobile arrangement. Menus/creation/settings use their separate accepted menu work.

## Live content and interactions

- Inventory remains 14×9 at **32×32 logical pixels**, grid origin **(7,32)** in the centered workspace. No hover
  overlay or hover label above Stats. Inspect opens on held RMB, closes on release anywhere, focus loss or view change.
- Skills retain whole-row clicks, blue for affordable upgrades, no plus buttons. Preserve the original font role,
  point costs, mastery restrictions and native action validation. Stats keep original slash/bonus formatting and
  conditional jade/coral colours, with stronger section rules. Awards retain their priority colours without nested frames.
- Item inspectors retain centered name, Type/details/descriptions in their native font roles. Value is `Value: N`,
  anchored below its divider at the bottom; overflow scrolls above it. Monster, spell, buff, skill and stat inspectors
  keep their different content and gameplay information on the shared visual frame.
- Rest retains its three blocks and native buttons. No standalone Food 7 label. Quick reference retains five columns,
  larger descriptor column, stronger dividers, Reputation/Fame and coloured HP/SP numbers without bars.
- Dialogue remains body-only, with no invented heading/Continue button. Preserve the original media rectangle,
  camera/video aspect and input routing. Body text starts Arrus 19, tries 18, then Create 18/17 before bounded scrolling.
- Journal retains four views, six note categories, native table content, unlocks, pagination, map pins, zoom and Close.
  Its map rectangle is exactly **(131,101,300,300)**; body is **(101,96,360,293)**. Do not bake sample records into assets.
- All labels/counters remain localized/live. Icon/label children inherit the parent button state and never steal input.
  Disabled, selected-hover, focus and pressed text colours are runtime behaviour, not unsupported YAML asset keys.

## Retained content and companion work

`coverage.json` accounts for every current gameplay layout. Chest reuses the new fullscreen chrome and inventory skin
while preserving chest-specific art and dimensions. Native paperdolls, portraits, inventory items, house media, rest
animations and world maps stay native dependencies, enumerated in `runtime_dependencies.json`.

The separately accepted spellbook restoration stays installed and authoritative; see
`../hud_inventory/spellbook_fixup_review/README.md`. Town Portal, Lloyd's Beacon and adventurer recruitment have no
new approved standalone redesign in this conversation; their current layouts are pinned for continuity. Main/pause/
settings/save/load/creation screens belong to the separate menu work. This handoff must not overwrite it incidentally.
`runtime_reference_changes.json` records any separately retained layout that changed after its initial snapshot.
Those snapshots are comparison material, never install candidates; current companion work stays authoritative.

## Verification at integration

The package validator parses all candidates with the actual `UiLayoutManager`; that establishes schema compatibility,
not implemented rendering. It also checks local asset references, alpha, font descriptors, key geometry, buff coverage,
state plates, file hashes, layout ID migration and preserved runtime snapshots. Browser captures check the approved
composition and status/input specimens. Run `python3 validate.py` to refresh its report and manifest.

After native implementation, build only the normal target and test: indoor/outdoor shared HUD; parties 1–5; 4:3/16:9/
21:9 and UI scale; clear/yellow/red/recovery/incapacity; 0/4/5/8/9/22 buffs including ties/expiry/permanent effects;
personal effects; minimap reveal/zoom; followers; real time and all turn phases; short/long/empty status; Alamos input,
bank deposit/withdraw/cancel/validation; held RMB release/focus loss; all overlays; journal empty/multipage/localized
paragraphs; mobile touch controls. Scene fixtures in browser previews are not evidence that these native checks passed.
