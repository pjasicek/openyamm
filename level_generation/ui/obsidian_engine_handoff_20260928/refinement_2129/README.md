# Native Obsidian HUD refinement — 2129

Implemented from the user's `test_img/2129.png` feedback on 2026-09-28. The later
[2130 correction](../refinement_2130/README.md) supersedes this revision's bar inset, outer shadows and buff art/mapping.
In particular, the Android skull mapping described below was incorrect and is preserved here only as historical evidence.

[Open the native screenshot gallery](index.html). These are engine-generated screenshots, not mockups.

## Installed changes

- **Shared top bar:** gold, food, Books, Party, Rest and Options occupy one 268×26 logical-pixel bar at the top left.
  The four menu actions retain their existing illustrations and actions, with hover/pressed feedback and no captions.
  The turn-based control remains in the freed bottom-left space. Fullscreen overlay bars retain their separate layout.
- **Minimap:** no location heading or north letter. The map, rim, zoom controls and followers move up 24 logical
  pixels; the map remains 112 logical pixels across. The full map still displays the location name.
- **Layered buffs:** Obsidian hero and skull illustrations sit below the top bar. Each panel is 60×60 at the previous
  Android reference width of 965, about 7% larger than the old 56×56 panels. The rendering and pointer hit testing use
  the same resolved rectangles. Existing registered `asil01`–`asil10` and `asir01`–`asir07` layers show active effects.
  Stoneskin, Day of the Gods, Protection from Magic, Glamour and Levitate use small glyph-free corner badges because
  the old Android layer set did not cover them. Badges draw last so overlapping effects cannot obscure them.
- **Inspection:** hold RMB on either panel for that panel's active effects and remaining durations, ordered by expiry.
  Release RMB to close. The frame grows with the content, including a compact “No active buffs” state when empty.
  Left clicks on the panels are consumed by the HUD.
- **Future special effects:** the four-icon timed strip, shortest-expiry ordering, counted overflow, glyph-free art and
  inspection remain implemented. `GameplayBuffPresentation::Special` reserves this presentation. All 22 current party
  effects use Hero or Skull, including those close to expiry, so the strip has no current entries.
- **HP:** green at 66% and above, yellow above 33% and below 66%, red at 33% and below. Cached native gradients retain
  the shaded appearance and existing damage trail. The same colours apply to gameplay and fullscreen portrait meters.
  SP remains blue and is omitted when maximum SP is zero.

The previous 10% portrait enlargement, lower placement, portrait/meter gap, selection behaviour and removal of redundant
names/condition labels remain intact. Android loads this shared layout; extra touch controls are still a separate task.

## Artwork

Generated with the **built-in imagegen tool**, using the original hero/skull as registration references and existing
Obsidian artwork as the style reference. Both selected results were copied unchanged into the mounted asset package;
their genuine RGBA transparency is preserved. No colour-key conversion or post-generation image editing was applied.

- [Hero PNG](../../../../assets_dev/engine/icons_x2/obsidian_buff_hero.png)
- [Skull PNG](../../../../assets_dev/engine/icons_x2/obsidian_buff_skull.png)
- [Exact final prompts and tool arguments](prompts.json)
- [Source paths, dimensions, alpha bounds and hashes](artwork.json)

These are the panel bases. Live effects still use the existing registered layers and the previously prepared
glyph-free spell illustrations; the new art does not bake in any buff state.

## Runtime ownership

The mounted `assets_dev/engine/ui/gameplay/gameplay.yml` owns the shared bar, minimap and panel dimensions.
`GameplayScreenRuntime` anchors the panels below the bar. `GameplayBuffHud` owns effect classification, layered drawing
and pointer targets, while `GameplayHudOverlaySupport` supplies held-RMB content. `GameplayUiSkin` owns HP thresholds
and the three cached shaded fills. These are shared gameplay paths for indoor and outdoor scenes.

The archived `engine/`, `design/` and browser payloads in the parent package remain historical handoff material. Do not
reinstall those files over the mounted layout or use their old location/timer-strip rules as current requirements.

## Validation

Normal desktop executable and unit-test targets built successfully:

```sh
cmake --build build --target openyamm -j25
cmake --build build --target openyamm_unit_tests -j25
./build/tests/openyamm_unit_tests --test-case='*Obsidian*,*circular minimap*,*HUD classification*'
```

**9 test cases / 140 assertions passed.** Coverage includes the shared command/resource ownership, all ordinary buff
types staying off the special strip even near expiry, exact HP-band boundaries, circular minimap clipping and retained
layout geometry. All 294 Obsidian YAML asset references resolve; scoped whitespace checks passed.

Native MM6 runs used OpenGL 3.3 on NVIDIA through SDL Wayland at **1600×900, 1280×960 and 1600×1200**. The gallery
preserves 19 captures, including one and five PCs, empty/typical/all-22 buff states, held inspection and release,
all four moved command actions, zoom in/out, full-map location, fullscreen HP colours and the turn-based control.
The five-PC widescreen fixture has stable 100%, 80%, 50%, 34% and 20% HP examples with regeneration disabled for capture.
The typical-buff 4:3 run retained its regeneration skill, so its HP examples rise during that tour.

`validation.json` records the current file hashes, screenshot dimensions/hashes and run receipts. `runs/` contains
the native logs and launcher records; `tours/` and `fixtures/` preserve their exact inputs. The fixtures are isolated
review saves, not gameplay data changes. The parent native-integration record retains the earlier broad MM6/MM7/MM8
and overlay validation; this pass targets the 2129 changes.
