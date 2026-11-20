# UI YAML legacy-art audit — 2026-09-29

The remaining visible Obsidian conversion candidates are **Lloyd’s Beacon**, the **Close button shared by
the teleport screens**, and the **character jewelry panel/magnifier**. The spellbook also retains a classic
book design, but it was separately approved and restored. It is not an overlooked low-resolution installation.

[View the current artwork](index.html). These are existing runtime assets, not proposed replacements.
[The inventory](inventory.json) records every engine UI YAML asset binding and source-file hash at audit time.

The user subsequently requested these conversions. See the
[implemented native follow-up](../obsidian_remaining_20260929/README.md) and its gallery for Lloyd's Beacon,
teleport Close buttons, jewelry/magnifier, context actions and the Android touch supplement. The old shop frame
fallback is removed; spellbook artwork remains intentional. The audit below records the pre-change state.

## Scope and method

Inspected all 35 YAML files in `assets_dev/engine/ui/` and the additional MM9 map catalog in
`assets_dev/worlds/mm9/ui/maps/catalog.yml`. Parsed asset states, inspected the relevant mounted PNGs,
and traced renderer substitutions and menu routing. This is a source/artwork audit, not a new native playthrough.
No game code, layouts or artwork were changed.

Classic names such as `IRBgrnd` and `c_close_up` resolve through the
[x2 package declarations](../../../assets_dev/engine/icon_packages.txt). “Legacy” here means the older visual
design, not a claim that the original low-resolution BMP is still mounted. Font roles selected for the Obsidian
overlays remain intentional; a recreated MM reading font is not itself a legacy-art defect.

## Active conversion candidates

| View | Remaining artwork | Source and runtime behavior | Suggested scope |
| --- | --- | --- | --- |
| Lloyd’s Beacon | `IRBgrnd`; `IRT01r/b`, `IRT02r/b`; `c_close_up/DN/ht` | [lloyds_beacon.yml](../../../assets_dev/engine/ui/gameplay/lloyds_beacon.yml), asset lines 22, 126, 139, 152. The utility-spell renderer uses the scroll/table background and red-and-gold mode buttons directly. | A coordinated Obsidian screen treatment. Preserve five beacon slots, preview images and set/recall behavior. Slot borders and text colors are also specified in C++, so replacing only the background would leave paper-oriented colors. |
| Town Portal / Dimension Door | `c_close_up/DN/ht` | [town_portal.yml](../../../assets_dev/engine/ui/gameplay/town_portal.yml), line 47. Both modes share the layout, and the renderer draws the selected button texture directly. The word “Close” is baked into the art. | Replace the button states with the shared blank Obsidian button and live Fondamento label. Rendering needs to draw that label as well as the texture. |
| Character jewelry view | `backhand` | [character.yml](../../../assets_dev/engine/ui/gameplay/character.yml), line 1302. Visible when the jewelry overlay is open. Its silver beveled slot borders and green mottled panel are the older design. | Obsidian panel/slot treatment while preserving the gauntlet, amulet and six ring positions and hit areas. |
| Character magnifier | `MAGNIF-B` | [character.yml](../../../assets_dev/engine/ui/gameplay/character.yml), line 1466. A restored red/gold magnifier, with the same asset for all three interaction states. | Smaller consistency candidate: match the Obsidian icon treatment and button states. |

Renderer evidence: [GameplayPartyOverlayRenderer.cpp](../../../game/ui/GameplayPartyOverlayRenderer.cpp),
Town Portal/Dimension Door around lines 4750–4915, Lloyd’s Beacon around 4920–5070, and the jewelry visibility
branch around 9226. The Lloyd’s Beacon implementation includes black text, a brown slot border and a white
highlight border; these need attention if its reading surface becomes dark.

## Retained classic artwork — distinguish it from unfinished UI chrome

| YAML | Existing art | Assessment |
| --- | --- | --- |
| [spellbook.yml](../../../assets_dev/engine/ui/gameplay/spellbook.yml) | Twelve `sb*000` book pages, twelve `ST*` bookmark pairs, 111 spell-icon pairs; `STXT*`, `STSS*`, `GF-ASpell*` bottom controls. | Live classic book styling. The pages, spell pairs and bookmarks were explicitly approved and installed in the [spellbook acceptance](../hud_inventory/spellbook_acceptance_20260927/README.md). The three bottom controls retain their previously accepted restored art. A future Obsidian redesign would be a separate design decision; the controls are potential small consistency changes if requested. |
| [town_portal.yml](../../../assets_dev/engine/ui/gameplay/town_portal.yml) | `townport` declared; world/destination backgrounds and hover patches selected at runtime. | Illustrated map content, not a generic window panel. MM6/MM7 replacements are separately approved and installed. Later MM6 palette work and the MM8 colored candidate remain review work according to the [map revision record](../hud_inventory/town_portal_fixup_review/README.md). Preserve the installed maps when updating the Close button. |
| [chest.yml](../../../assets_dev/engine/ui/gameplay/chest.yml) | `chest01` default, overridden from the active chest table; `ticonCH` chest illustration. | Restored wooden container/interior art remains inside the Obsidian outer frame. The top bar, sides, nested inventory and Close button already use Obsidian assets. Reskinning the wood is optional, not a missing shell conversion. |
| [character.yml](../../../assets_dev/engine/ui/gameplay/character.yml) | `backdolm` declaration and runtime paperdoll/background composition. | Preserved character/paperdoll content. Do not equate it with the jewelry panel’s older slot chrome. |
| [rest.yml](../../../assets_dev/engine/ui/gameplay/rest.yml) | `terra0000` panorama animation; `scorebg_food` cost icon. | Intentionally retained content. The rest frame, grouped controls and replacement animated hourglass are Obsidian. |
| [gameplay.yml](../../../assets_dev/engine/ui/gameplay/gameplay.yml) | `scorebg_gold`, `scorebg_food`, `sp21a10`, `sp27a10`. | Retained resource icons and the explicitly requested separate animated Fly/Levitate and Water Walk indicators. Resource icons also occur in character/chest/dialogue layouts. |
| [MM9 map catalog](../../../assets_dev/worlds/mm9/ui/maps/catalog.yml) | `ui/maps/*.pcx` | World map illustrations only; no button/frame skin definitions. MM9 keeps its native package tier. |

## Conditional and bypassed definitions

- **Dialogue `evt`**: [dialogue.yml](../../../assets_dev/engine/ui/gameplay/dialogue.yml), lines 124 and 135,
  still declares the old gray marble texture. `DialogueVideoArea` is drawn by the video renderer and does not
  use that declared texture; a missing movie gets a solid fill/border. `DialogueShopOverlayFrame` uses `evt`
  only if `buildHouseShopVisualLayout` supplies no shop-specific background. Normal shops select `WEPNTABL`,
  `ARMORY`, `GENSHELF` or `MAGSHELF`. Those are retained merchandise-display illustrations, selected in code.
  See [GameplayDialogueRenderer.cpp](../../../game/ui/GameplayDialogueRenderer.cpp), lines 516–666,
  1395–1404, 1626 and 2390 onward. The fallback material is a small remaining cleanup candidate, not the
  ordinary dialogue reading surface.
- **Old settings layouts**: [controls.yml](../../../assets_dev/engine/ui/gameplay/controls.yml),
  [keyboard.yml](../../../assets_dev/engine/ui/gameplay/keyboard.yml) and
  [video_options.yml](../../../assets_dev/engine/ui/gameplay/video_options.yml) retain `controlbg`, `optkb`,
  `optvid`, `bt_*`, `bl_*`, `ar_*` and `bv_rtrn*` textures. They are still loaded and have old handlers, but the
  normal current menus open the new `settings_*.yml` screens. `GameApplication::openPauseMenuScreen` transfers
  control to `MainMenuScreen`; its Settings action loads the new layouts. The old input path expects
  `MenuButtonControls`, which is absent from the current menu YAML. These files are cleanup debt, not the
  settings artwork normally shown to the player.
- **Old Android layout**: [gameplay_mobile.yml](../../../assets_dev/engine/ui/gameplay/gameplay_mobile.yml)
  contains the old `Basebar_cut`, `npcpnl`, `butn*`, `asiL*`/`asiR*`, minimap frame, zoom and touch controls.
  It is absent from [GameplayLayoutFiles](../../../game/ui/GameplayUiController.cpp) and has no runtime source
  reference. Android currently shares the desktop layout as requested. Keep this distinction when revisiting
  the deferred touch UI.

## Already converted

The other mounted YAML frame/button definitions use `obsidian_*` or `hud_x2/menus/omenu_*`: gameplay HUD,
adventurer’s guild, stats/skills/awards, quick reference, inspect windows, dialogue frame, rest, journal,
chest outer frame, main/pause menus, save/load, character creation, continent selection, current Settings,
keyboard, credits and confirmation. Content exceptions are listed above.

The useful next conversion scope is Lloyd’s Beacon, the shared teleport Close button and the jewelry panel.
The dormant layouts can be cleaned up separately; the approved book/map illustrations should retain their
own acceptance history.
