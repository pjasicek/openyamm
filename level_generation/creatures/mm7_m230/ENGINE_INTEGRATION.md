# Crusader engine integration

The corrected m230 artwork is available as three additional monsters. Original BMPs, palettes, monster entries,
and native animation groups retain their existing behavior.

| Monster ID | Identity | Native stats | Sprite group | Palette preset |
| --- | --- | --- | --- | --- |
| 901 | custom:crusader_green | 259, Initiate | m900 | 54, exact green base |
| 902 | custom:crusader_blue | 260, Champion | m901 | 55, blue |
| 903 | custom:crusader_red | 261, Master of the Sword | m902 | 233, red |

## Play the Brackenford demonstration

From the repository root:

```sh
./level_generation/creatures/mm7_m230/play.sh
```

Choose **Load Game → Scenario** (Brackenford). The prepared save contains the God Lich, three enhanced crusaders
near the western arrival, and three original crusaders nearby for comparison. They use ordinary actor AI and can
wander; walk around them to see the directional views. Combat uses their native attack/hit/death sequences.
Three additional enhanced crusaders occupy Greywatch's upper entrance hall in this test setup.

The launcher uses `/tmp/openyamm-crusader-playtest`, its separate settings/assets/saves, and the current built game.
`OPENYAMM_CRUSADER_DEMO` can select another prepared directory. After a reboot clears `/tmp`, recreate it:

```sh
python3 level_generation/creatures/mm7_m230/install_runtime.py
python3 level_generation/creatures/mm7_m230/prepare_playtest.py
```

The project-owned `playtest/crusader_demo.oysav` is the God-character seed, created through the ordinary New Game
God Lich option. Preparation loads that seed and positions the camera at the demonstration. F9 saves and F10 loads
the quicksave. The original authored Brackenford scene/package and other playtest saves are not replaced.

## Runtime contract

`assets_dev/engine/sprites_new/crusader/manifest.json` is the compact runtime manifest, separate from the restoration
provenance manifest. Four base PNG pages and four grayscale mask PNG pages supply 114 poses. Review sheets and baked
palette previews are not installed. Native sprite-frame YAML uses explicit `atlas:crusader/m230...` texture names;
existing direction selection appends the view suffix and mirrors the original octants. Timings, action order,
`Image1`, frame scale and descriptor slots remain authoritative in the native frame tables. Frame IDs 30000–30101
are reserved by this installer, which checks ID/family collisions before writing.

`engine/SpriteAtlas` validates the manifest. Shared `game/render/SpriteAtlasCache` owns GPU pages per renderer,
package and page, shared across frames, actors and all three variants. Base pages upload once as BGRA8 and mask
pages once as R8. Decoded source pixels are released after constructing compact opacity masks. All four resident
page pairs occupy **60.28 MiB**, excluding driver and opacity-cache overhead; three presets do not triple this.
Only explicitly selected atlas names probe this directory. Invalid selected packages report an error.

Cropped physical dimensions are divided by the manifest tier (2), then the ordinary frame/actor scale is applied.
Crop offsets restore the native logical 256×256 canvas. The current actor renderer bottom-anchors that canvas,
including native m230's `Center`-flag frames: horizontal placement uses logical pivot X, vertical placement uses
logical canvas height. Mirroring reflects the crop about the same horizontal pivot. Rendering, actor picking,
visibility geometry and health bars use this placement. Collision and combat dimensions remain native statistics.
This first integration is for actor sprites; it is not a promise of arbitrary per-frame pivot overrides for items.

`fs_sprite_atlas.sc` shares lighting/fog/outline code with the native billboard shader. It clamps UV samples to the
frame rectangle, preserving padding and avoiding neighboring-frame bleed. The mask selects cloth/plume/heraldic
color, leaving zero-mask steel, gold and leather unchanged. In encoded RGB it uses the same `green_chroma_srgb_v1`
operation as `process.py:recolor`; preset 54 bypasses it exactly. Alpha is unchanged. The grayscale PNG decoder
places coverage in BGRA's red component; do not incorrectly require replicated RGB or read its blue component.
Filtering follows the billboard setting; atlas mipmaps and generalized multi-region recoloring are future work.

## Validation and remaining scope

- Development executable and both billboard shaders compiled successfully.
- Focused tests: 16 cases, 170 assertions passed, including native billboards/frame behavior, manifest bounds,
  crop/mirror/camera placement, and the grayscale-mask decode regression.
- All 102 custom frame-table records match their native timing, flags, scale and animation data after accounting
  for the new IDs and texture prefix; they resolve the same 114 unique directional poses.
- Brackenford scenario validates all six custom/native actors and save/load. The saved party is God, with 3350 HP.
- Actual [outdoor](review/runtime/crusader_fixed.png) and [indoor](review/runtime/crusader_indoor.png) captures show
  enhanced sprites with selective colors and scene lighting. Walking frames load through the ordinary animator.
  Logs show one allocation per used page, shared by the three presets. The initial failed mask-loader capture
  `crusader_outdoor.png` is historical diagnostic evidence, not the accepted result.

An isolated [60-crusader map capture](review/runtime/crusader_crowd.png) also loaded each used page only once
across the three presets. Terrain/buildings occlude some actors, so this is a page-sharing check rather than a
60-visible-sprite fill-rate benchmark. The three loaded page pairs total 51.67 MiB; death/corpse art can bring
the four-page total to 60.28 MiB. See [validation data](review/runtime/integration_validation.json).

These software-display captures establish functional rendering, not target-GPU FPS or a full combat balance audit.
The green-chroma shader is deliberately the fitted crusader operation; other creatures need their own accepted
masks/presets or an explicitly extended recolor contract. This opt-in path does not replace native palette decoding.
