# Obsidian NPC portrait frame — 2026-09-29

The user identified the copper/parchment portrait border in House Memoria as a remaining mismatch with the
Carved Obsidian HUD. NPC cards now use the existing approved stone-and-gold frame pieces at 0.35 border scale,
giving them fine metal edges and small matching corner details.

This is a native composition of the existing artwork, with no new generated raster or duplicate frame asset.
The shared dialogue renderer applies it to single NPCs, multi-occupant houses and shopkeeper cards. Map and
dungeon transition pictures keep their own presentation.

- Layout remains 71 × 81 logical pixels.
- The portrait remains 63 × 73 with its existing four-unit inset and UV crop.
- Names, house titles, dialogue topics, selection/hit areas and portrait images retain their geometry.
- `DialogueNpcPortrait` in `assets_dev/engine/ui/gameplay/dialogue.yml` declares the shared Obsidian frame.
- `GameplayDialogueRenderer.cpp` uses `GameplayUiSkin::renderPanel` instead of the legacy `evtnpc` texture.

[Native House Memoria capture](native/house-memoria.png) · [User reference](user-reference.png)

## Native verification

The isolated desktop check enters MM8 `out03.odm` event 451 (House Memoria), using the original Karanya Memoria
portrait and live dialogue. The capture is 1200 × 900, matching the user's 4:3 view. See [native/run.json](native/run.json)
for renderer and launch settings. A temporary event-entry probe is preserved in [capture-probe.patch](capture-probe.patch)
and removed from production code after capture; [tour.yml](tour.yml) contains its capture steps.

The development build and visual review are the checks for this small rendering change. The shared rendering path
also serves MM6/MM7 and Android; this review does not constitute a mobile-device or multi-world runtime test.
