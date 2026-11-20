# Approved A — native split portrait arcs

Integrated on 2026-09-29 after the user selected A and requested a fitted bottom-anchored basebar, less outward curl
on its ornaments and a narrower border. [Real game captures](index.html) are the current visual reference.
The [earlier browser comparison](../index.html) preserves the proposal before these fitting adjustments.

**Final native appearance approved by the user on 2026-09-29:** “OK this looks good, implement this”.
At that approval, the installed source, layout, ornament and development executable were verified against the retained
native review and matched it exactly. This fitted split-arc version is the approved gameplay portrait/basebar baseline.

The subsequent [2134 refinement](refinement_2134/README.md) enlarges only the gameplay selection diamond to 20 × 20
logical pixels. Portrait size and HP/mana widths remain as approved. Its screenshots and receipt supersede the
initial diamond size recorded below; the initial verification record remains preserved.

The [2135 status refinement](refinement_2135/README.md) increases gameplay event/hover text from Lucida scale 0.65
to 0.75 and attaches the panel six logical pixels above the basebar. The enlarged 2134 diamond remains installed.

The [full-screen follow-up](overlay_arcs/README.md) also installs the split arcs and matching indicators in inventory,
house dialogue and the other shared overlay screens. It retains their portrait dimensions and the clear status/input
rail, and supersedes the horizontal overlay meters described in the original integration record below.

The [outline/text clarity follow-up](arc_smoothing/README.md) uses a constant one-screen-pixel antialiasing fringe for
the portrait arcs and rims in both HUD layouts. It also raises the phase label and minimap clock to Lucida scale 0.7
inside their existing plates. [Before/after native comparison](arc_smoothing/index.html).

The [journal map correction](journal_map_pixels/README.md) fixes CPU sampling of x2 map assets by returning physical
pixel dimensions with the source buffer. It retains the existing map scale, exploration state and marker placement.

## Installed result

- HP fills upward around the portrait's left, mana upward around its right. Each gauge covers 160 degrees, leaving
  gaps above and below. The existing HP thresholds remain green ≥66%, amber >33%, red ≤33%; mana is blue.
- Selection is an ivory-gold inner rim and top diamond. Both disappear when nobody can act. The existing plain
  lower-left aggro diamond retains its colours/dim state and recovery ring; individual buffs use the lower-right
  medallion and its existing live effect list.
- No mana gauge or track is drawn for zero maximum SP. The existing short HP damage trail follows the curved interval.
- Portraits retain their accepted 47.52 × 63.946666 logical size, animated expressions and condition treatment.
  No extra names, numbers or condition labels were added.
- The shared frame has width `46 + 80 × party size` (1–5), height 104, and screen-space bottom-centre anchoring with
  zero bottom offset. Slots start at x=24, advance by 80, and sit at y=12. The top selection diamond, full aggro sprite
  and buff button fit inside the border, including the decorative corners. The HUD rises only six logical pixels
  above the previous frame because its old ten-pixel bottom gap is gone.
- Party-frame border art is drawn at 75% of its prior thickness. The new compact end ornament uses generated true
  alpha and unchanged source pixels, registered through UVs and mirrored for the right side. It stays within the
  frame's height. At this initial integration, the separate fullscreen 4:3 overlay retained its horizontal bars;
  the full-screen follow-up above replaces those with matching arcs inside the existing carved frame.

## Runtime ownership and geometry

`assets_dev/engine/ui/gameplay/gameplay.yml` remains authoritative. Its optional `meter_arc` mapping gives
`start_degrees`, signed `sweep_degrees` and logical `stroke_width`; the element rectangle bounds the ellipse centreline.
Invalid arc widths and sweeps are rejected by `UiLayoutManager`. All existing element IDs and hit-region ownership
are retained.

`GameplayUiRuntime::submitHudTexturedArc` draws a connected elliptical strip using the normal HUD texture shader.
Cross sections follow the true ellipse normal, so stroke thickness remains uniform. Each complete half-meter has
48 segments; a full inner rim has 108. Partial fills and damage-only ranges end at the live fraction rather than a
rounded segment boundary. A strip uses one submission, not one draw per small segment. Standard transient-buffer
capacity checks remain in place.

`GameplayUiSkin` caches the shaded material textures, including narrow alpha fades along open ends and inner/outer
edges. Closed rims have no end fade/seam. `GameplayUiRenderer` connects these bands to the existing resource,
selection, recovery and personal-buff state. No new shader, stencil pass, dynamic portrait image or platform-specific
gameplay implementation is required.

## Asset provenance

Generated using the **built-in imagegen tool**, editing the previous Obsidian endcap:

- Runtime asset: [obsidian_party_endcap_compact.png](../../../../assets_dev/engine/icons_x2/obsidian_party_endcap_compact.png)
- Preserved output: [art/obsidian_party_endcap_compact.png](art/obsidian_party_endcap_compact.png)
- Exact prompt and generation mode: [art/prompt.json](art/prompt.json)
- Dimensions, registered UV region and SHA-256: [art/receipt.json](art/receipt.json)

No alpha extraction, recolouring, resampling or bitmap cleanup was applied. The old ornament is preserved for the
historical studies. Dynamic arc textures are native geometry/materials, not generated replacement portraits.

## Verification

Normal `openyamm` and `openyamm_unit_tests` builds passed. The focused suite passed **23 cases / 8,460 assertions**:

```sh
cmake --build build --target openyamm -j25
cmake --build build --target openyamm_unit_tests -j25
./build/tests/openyamm_unit_tests --test-case='*Obsidian*,*circular minimap*,*HUD classification*,*layout*'
```

Coverage includes mirrored upward fill, constant band thickness, empty/tiny/full and damage intervals, malformed arc
configuration, all 1–5 party widths, border/corner clearance, bottom screen anchoring and the existing shared layouts.
An initial full-rim sample-count test exposed float rounding at 360 degrees; the subdivision arithmetic was corrected.

Six retained native desktop runs produced ten reviewed captures through bgfx on **OpenGL 3.3, NVIDIA, SDL Wayland**:
five PCs at 1600×900, 1280×960 and 800×600; three PCs; one zero-mana Knight; everyone recovering and the first member
becoming ready. Interaction captures verify fourth-portrait selection, the first member's buff button and the retained
fullscreen inventory. All runs exited successfully. The development screenshot tour uses isolated fixtures and does
not alter normal saves. One initial wide interaction tour was corrected to toggle the buff popup closed before opening
inventory; the retained wide run and screenshots are from that correction.

The tiny/empty SP states and all three HP colours were reviewed natively. Damage interval math is unit-covered; this
pass did not force an actual damage event in the running game. These captures establish appearance and interaction,
not a GPU performance measurement. No Vulkan build, Android device/APK check or release ZIP repack was performed.
Android loads the same shared layout as already requested; touch-specific refinement remains separate.

`validation.json`, `runs/`, `tours/`, `fixtures/`, build logs and `tests.log` retain the verification record.
