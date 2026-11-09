# Native Obsidian HUD correction — 2130

Historical revision: the [2131–2132 follow-up](../refinement_2132/README.md) supersedes its flat minimap rim,
resistance sizes, followers control and movement-buff badges. Current gameplay also uses the
[dynamic party basebar](../refinement_party_basebar/README.md).

Implemented from `test_img/2130.png` and the user's accompanying feedback on 2026-09-28.
This supersedes the 2129 bar inset, outer shadows, buff artwork and skull assignments.
The mounted runtime files remain authoritative; archived handoff payloads preserve earlier revisions.

[Native screenshot gallery](index.html) · [exact imagegen prompts](prompts.json) · [art receipts](artwork.json)

## Installed changes

- The shared resource/menu bar anchors at screen **(0,0)**. Its 268×26 logical-pixel plate has no padded bitmap margin
  or drop shadow. Gold starts six logical pixels inside the bar; its label also moves inward.
- The 112-logical-pixel minimap retains its live circular clip and zoom buttons. Its replacement rim is a thin ring
  without the previous outside shading, shadow or extra outline.
- Six resistance gems, sword, shield, Haste wings, Immolation flames, six skull effects and the stone skull are new
  transparent illustrations. No old `asil`/`asir` bitmap is drawn by the new party-buff panels.
- The skull follows the old **desktop** spell mapping. The Android YAML had assigned those images to different spells;
  carrying those assignments forward in 2129 incorrectly made Fly activate the Torch Light glow.

| Spell | Correct skull effect | Archived desktop source |
| --- | --- | --- |
| Torch Light | Warm light beside/behind the skull | `asir06` |
| Wizard Eye | Near eye | `asir02` |
| Feather Fall | Clouds beneath/behind the skull | `asir07` |
| Stoneskin | Stone material replacing the base skull | `asir01` |
| Day of the Gods | Golden halo | `asir05` |
| Protection from Magic | Flower/leaf garland | `asir04` |

The reference is [the archived desktop YAML](../reference_runtime/ui/gameplay/gameplay.yml), not the Android mapping.
Detect Life uses the far eye as an explicit extension. Fly, Water Walk, Invisibility and Levitate use distinct
glyph-free skull corner badges; Glamour uses a hero corner badge. All 22 ordinary party buffs remain represented.
The original resistance colour/shape assignments and warrior spell meanings are preserved.

Light, clouds and flames draw behind the bases; Stoneskin replaces only the skull base; other layers and badges draw
above it. Held RMB still lists the panel's active effects and durations and closes on release. The reserved special
timer strip remains empty for ordinary spells.

## Artwork and registration

Generated using the **built-in imagegen tool**. The four RGBA results are copied unchanged into
`assets_dev/engine/icons_x2/` and preserved in `art/`:

- `obsidian_buff_resistances.png`: six gems, 1536×1024.
- `obsidian_buff_combat.png`: sword, shield, wings and flames, 1254×1254.
- `obsidian_buff_skull_effects.png`: eyes, garland, halo, light and clouds, 1536×1024.
- `obsidian_buff_skull_stone.png`: registered stone material variant, 1254×1254.

The model supplied the alpha, including soft effect edges. No colour key, matte removal or alpha extraction is applied.
Runtime UV rectangles select the sprites directly from the unmodified atlases; no destructive sprite slicing is needed.
[Atlas registration](atlas_registration.json) records source rectangles and placement in the existing 128-square panel
coordinate system. `GameplayBuffHud.h` owns the corresponding runtime constants and spell mapping.

The bar and minimap ring are code-native SVGs in `art/`, rasterized with ImageMagick into
`obsidian_hud_topbar_flat.png` and `obsidian_hud_minimap_rim_flat.png`. These replace code-generated chrome, not painted
imagegen artwork. [Artwork receipts](artwork.json) retain paths, dimensions, alpha information and hashes.

## Validation

The normal desktop executable and unit-test targets built successfully. The focused suite passed **11 cases and
378 assertions**, including old desktop skull meanings, separation of Fly and Torch Light, layer bounds, ordinary
buff classification, shared bar ownership, minimap clipping and HP thresholds.

```sh
cmake --build build --target openyamm -j25
cmake --build build --target openyamm_unit_tests -j25
./build/tests/openyamm_unit_tests --test-case='*Obsidian*,*circular minimap*,*HUD classification*'
```

Native isolated MM6 captures use the regular OpenGL executable at 1600×900 and 1280×960. They cover all 22 active
effects, Torch Light alone, Fly alone, Stoneskin alone, a typical six-effect 4:3 state, held inspectors/release,
all four top-bar actions and the retained inventory overlay. The spell-only saves demonstrate that the right effect
activates independently. These are engine-generated PNGs, not browser mockups.

`tours/`, `fixtures/`, `runs/` and `validation.json` retain exact inputs, native logs, file hashes and capture receipts.
The broader MM6/MM7/MM8 and overlay checks remain recorded in the parent integration reference. No Vulkan or Android
build was run for this shared HUD correction; Android-specific touch controls remain the separate requested task.
