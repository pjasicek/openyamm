# Native Obsidian integration

Installed in the real game on 2026-09-28, following the user's authorization to replace the entire prepared gameplay
UI slice. Desktop and Android load the same shared gameplay layout. Android's extra touch buttons remain a separate
follow-up, as requested. Concurrent menu work is preserved.

The [native screenshot gallery](native_review/index.html) contains engine-generated GPU captures. The mounted files in
`assets_dev/engine/ui/gameplay/` and `assets_dev/engine/icons_x2/` are authoritative. The browser studies, `engine/`
payload and portable preparation archive preserve earlier design decisions; do not reinstall them over these files.

The subsequent [2129 refinement and checks](refinement_2129/README.md), with its
[native gallery](refinement_2129/index.html), supersedes the old command-bar placement, minimap location label,
ordinary party-buff strip and HP colours shown in the first gallery.

The earlier [2130 correction and checks](refinement_2130/README.md), with its
[current native gallery](refinement_2130/index.html), anchors the bar at (0,0), removes the outer bar/minimap shadows,
replaces the old contaminated buff overlays with true-alpha artwork and corrects the skull spell assignments.

The earlier [native party basebar review](refinement_party_basebar/index.html) and
[implementation notes](refinement_party_basebar/README.md) supersede floating gameplay portraits: a shared frame
grows with the party, exterior carved ornaments finish its ends and vertical HP/mana tracks sit beside each PC.
The [2131–2132 refinement](refinement_2132/README.md) also completes the smaller gems, buff-panel inset, minimap
time/shading and reskinned legacy followers panel. Fly/Levitate and Water Walk retain separate animated icons,
with no skull badges.

The latest [approved A split-arc integration](../obsidian_curved_portraits_20260929/native/README.md), with
[native captures](../obsidian_curved_portraits_20260929/native/index.html), replaces the vertical gameplay meters.
HP curves around the portrait's left and mana around its right; the bottom-anchored basebar has a 25% narrower
border, compact ornaments and clear space around every portrait indicator.
The [full-screen follow-up](../obsidian_curved_portraits_20260929/native/overlay_arcs/README.md) applies the same
curved meters, selected rim/diamond and lower indicators to inventory, house dialogue and all shared overlay HUDs.
Their portrait sizes, fixed 4:3 canvas, carved frame and status/input rail remain unchanged.

## Installed coverage

- **Gameplay:** live animated portraits for one to five PCs on a dynamic Obsidian basebar; selection rim/diamond,
  curved shaded HP/SP meters, compact carved exterior end ornaments, stronger
  recovery arcs, plain green/yellow/red readiness diamonds, gold/food, Books/Party/Rest/Options, followers, circular
  minimap and turn phases. No portrait names or mana meter for characters with zero maximum SP. No gameplay selection
  ring when nobody can act. Existing condition and portrait animation logic remains active.
- **Buffs:** 19 ordinary party effects on compact Obsidian hero/skull panels below the shared top bar, using new
  alpha atlases registered in the old 128-square coordinates, the correct desktop skull spell assignments and small
  glyph-free badges for Invisibility and Glamour. Fly/Levitate share a separate flight indicator; Water Walk has its
  own animated indicator. Detect Life uses the far eye as an extension. Held RMB lists each
  panel's effects and durations. The four-icon strip with counted overflow and expiry ordering is reserved for future
  special modifiers. Character medallions expose the ten individual effect types and their durations.
- **Fullscreen chrome:** carved top/left/base edges, smaller shields, empty-slot banners and the clear status/input
  rail from 2116. Existing centred 4:3 media, paperdoll and inventory geometry remains intact.
- **Character:** the 14×9 inventory grid remains 32 logical pixels per cell. Inventory has no hover overlay/label;
  inspectors use held RMB and close on release. Stats retain the original font roles and value formatting with stronger
  section divisions. Skills use blue eligible whole-row clicks, larger text, more row spacing and a shared scrollbar.
  Awards have the inline class title, header divider, framed list, native priority colours and the same scrollbar.
- **Rest and quick reference:** grouped native rest actions/date information, compact placement without an hourglass;
  a larger reference table with wider labels, strong column dividers, numeric HP/SP, conditional colours, reputation
  and fame.
- **Dialogue:** original video/sidebar geometry, simple dynamically sized dark reading surface and original recreated
  MM reading fonts. Topics use Lucida again; the permanent keyboard-navigation hint is removed. No extra body headings
  or Continue button. Bank/event entry remains in the unobstructed status rail.
- **Inspectors:** shared fixed-scale dark surface and tiled alpha border for item, monster, character stat/skill,
  spell, buff and detail windows. Native content fields/font roles remain; item name is centred and `Value: ...` is
  anchored below a divider at the bottom. Monster art uses the shared sprite atlas cache, including palette variants.
- **Journal:** live map/quests/story and six autonote categories, justified text bodies, pagination, selected/disabled
  controls, enlarged submenu spacing and native map behaviour. Autonote retains its recreated glyph metrics and is now
  tintable so it reads in soft ivory on obsidian.
- **Companion screens:** chest chrome uses the new surface; existing chest slots, spellbook and other independently
  prepared art remain wired to their native actions. Main/pause/settings/save/load/new-game menus retain the concurrent
  menu implementation.

## Final feedback from 2121–2127

The first native size experiment enlarged gameplay portraits by 25%. The user's final correction reduced that to
**10% over the approved browser baseline**. The later minimap correction reduced its diameter from 117⅓ to **112 logical
pixels** (about 4.5%). Zoom buttons remain on the outline, slightly overlapping the map; the shaded location label
initially replaced the north label. The later 2129 request removes the location label and raises the minimap and
followers by 24 logical pixels. Fullscreen portrait sizes were not enlarged.

The final 2127 adjustment lowers the gameplay party strip by 12.27 logical pixels and adds six logical pixels between
portraits and their meters. Portrait names and condition labels are absent; native facial/condition effects remain.

Small command/journal/follower illustrations now have alpha-aware mipmaps. Fondamento is sampled as a smooth TTF even
when its atlas scale is one; advances and kerning are respected. Original bitmap fonts retain their own sampling path.
This addresses the pixelation reports without replacing the selected artwork or reading faces.

Skills use an 18 logical-pixel row pitch and the recreated Lucida face. The two columns scroll together; headings and
rows clip to the viewport, and wheel, track clicks, thumb dragging and held-RMB inspection share the same geometry.
Awards use the corresponding scrollbar appearance from the new save/load menu. Rest retains its time-of-day sky
animation but removes the hourglass entirely.

## Runtime ownership

- `GameplayUiSkin` owns shared button states, surface/frame composition and scrollbars.
- `GameplayBuffHud` owns buff presentation, compact ordering and input targets.
- `GameplayScreenRuntime`, the shared HUD renderers and gameplay input controllers use the same resolved geometry.
  Character scroll offsets affect both drawing and picking. Outdoor/indoor views do not have separate skins.
- `GameplayHudCommon` loads Fondamento independently of the recreated MM faces. `TextureFiltering::UiIllustration`
  prepares the detailed Obsidian images for reduction; existing native icon/texture profiles retain their behaviour.
- The inspector reuses the application-owned `SpriteAtlasCache`; canvas dimensions preserve frame placement. It does
  not own another monster atlas or duplicate the world sprite cache.
- `gameplay_mobile.yml` is no longer loaded. The retired HUD-layout option is no longer emitted when settings are saved;
  old settings cannot re-enable the legacy HUD. Native keyboard/controller actions remain shared.
- `MenuInputTour` gained action-name steps and held right-button steps for repeatable native interaction captures.
  These are diagnostic launch features, not gameplay dependencies.

`native_install_receipt.json` records the initial 157 PNGs, 13 gameplay layouts and Autonote descriptor installation,
including the pre-install hashes and backup location. `native_review/validation.json` records the final mounted hashes,
test result, capture dimensions and run receipts after refinements. Initial receipt hashes intentionally remain intact.

## Validation

Normal development build and focused test build succeeded:

```sh
cmake --build build --target openyamm -j25
cmake --build build --target openyamm_unit_tests -j25
./build/tests/openyamm_unit_tests \
  --test-case='*Obsidian*,*circular minimap*,*HUD classification*,*character inspect layout*,*character doll*,*spellbook*,*bank deposit*,*settings*,*sprite atlas*,*font*,*Font*,*Upload preparation*,*Billboard upload*'
```

**64 test cases / 12,498 assertions passed.** Coverage includes circular clipping, complete buff classification and
ordering, layout loading/ownership and inventory geometry, font metrics/presentation, sprite atlas/filtering, settings,
retained spellbook and bank transaction behaviour. Final YAML asset validation found **285 Obsidian references and no
missing files**. Scoped whitespace checks passed.

Native desktop runs used OpenGL 3.3 on the NVIDIA GPU through SDL Wayland. Screenshots came from bgfx readback, with
isolated settings/saves:

- MM6: 1600×900 and 1280×960, five portraits, expanded party and individual buffs, turn-based controls, all character
  pages, inspectors and release behaviour, quick reference, rest and populated journal pages.
- Clicking the blue Mace row increased skill 3 → 4 and spent four skill points (45 → 41). Wheel and scrollbar dragging
  reached the lower skill rows and awards. The no-action fixture displayed no gameplay selection rim/diamond; both
  zero-mana Knights omitted their SP meters.
- An actual house video/NPC topic confirmed the restored topic font and clear bottom rail. Bank entry accepted a
  deposit of 125 and withdrawal of 25, producing carried gold 9900 and bank gold 100.
- Monster inspection displayed the Goblin King's restored atlas/palette and closed when RMB was released.
- MM7 Castle Harmondale checked an indoor map/inventory/vector minimap; MM8 Ravenshore checked outdoor gameplay and
  fullscreen rest at 2100×900. The concurrent pause menu was opened over the new HUD.

Some review saves deliberately populate every buff and high skills to exercise crowded layouts. Mistform can tint
portraits, and boosted maximum health makes the fixture's partially filled meters unusually short. These are live
game states, not baked UI illustrations. Internal action tours and run records accompany the captures.

No Vulkan build, Android APK/device validation or release ZIP packaging was performed. Android uses the installed shared
layout; touch-specific refinement remains deferred. The current development executable and mounted assets are ready
for normal native play and further visual review.
