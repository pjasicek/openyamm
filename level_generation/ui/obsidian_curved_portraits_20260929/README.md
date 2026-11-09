# Curved portrait meters — 2133 study

[Interactive browser](index.html) · [Split arcs](images/split.png) · [Nested arcs](images/nested.png)

Design study requested on 2026-09-29, using `test_img/2133.png`. **The user selected A, split arcs, and it is now
integrated into the native game.** See the [native screenshots](native/index.html) and [implementation record](native/README.md)
for the fitted, bottom-anchored frame with narrower borders and compact ornaments. The browser below preserves the
original comparison geometry before those fitting adjustments. The preview uses existing mounted portraits,
the current frame/end ornament, selection diamond, aggro gems and personal-buff medallion. Gauge geometry is SVG,
with simulated resource values. No portraits or UI bitmap artwork were regenerated for this study.

## Selected: A, split arcs

HP rises around the left side and mana around the right. Both use the same stroke width and leave small gaps above
and below the portrait. Preserve the current HP bands (green ≥66%, amber >33%, red ≤33%) and blue mana. The face
stays at its accepted size. Avoid the reference's large glow, extra runes and tiny numerical labels around the arc;
resource values belong in existing held-RMB character inspection.

Selection is the inner ivory-gold rim plus the top diamond, independent of meter colour or amount. Aggro remains the
plain lower-left diamond; its existing recovery arc stays around that diamond. Individual buffs use the lower-right
medallion. It opens the character's buff list and is absent with no effects. If everyone is recovering, there is no
selected rim/diamond. For a character with no mana, omit the mana gauge and its dark track entirely; HP keeps its
usual left-hand position.

The alternative B uses a broad inner health arc and a slimmer outer mana arc over 310 degrees. It fits the same slot,
but has three concentric outlines once selection is included. A reads more clearly at normal size and is closer to
the reference's division of the two resources.

The browser includes 1–5 members, widescreen/4:3 logical scale, click-to-select, HP/mana sliders, no-mana state,
three aggro colours, everyone recovering, buff toggles/popover and a short damage-trail example. The previous vertical
arrangement is also included as a comparison. Portrait names and explanation labels are review controls, not new
in-game labels.

## Original implementation assessment (before integration)

This is a modest extension to the shared HUD renderer. It does not need a replacement portrait pipeline, dynamic
bitmap regeneration, new shaders, stencil masks, or an image for every percentage.

Relevant existing code:

- `game/ui/GameplayUiRuntime.cpp`: `submitHudTexturedEllipse` already emits an elliptical triangle fan with the HUD
  vertex format/shader. `submitHudQuadBatch` handles shaded textured segments, including the recovery arc's lines.
- `game/ui/GameplayUiRenderer.cpp`: owns live HP/SP fractions, zero-mana suppression, selection visibility, HP colour
  selection and the current damage-trail timer.
- `game/ui/GameplayBuffHud.cpp`: owns personal-buff hit regions; their positions continue to come from the layout.
- `assets_dev/engine/ui/gameplay/gameplay.yml`: current slot geometry and independent selection/readiness/buff roles.

Implementation route:

1. Add an explicit arc-meter shape and start/sweep values to the layout data/parser. Keep the existing Health/Mana
   element IDs; their rectangles become the bounding ellipse. [design.yml](design.yml) records the proposed geometry,
   not a directly loadable runtime replacement.
2. Add one textured elliptical-band primitive alongside the existing ellipse. Emit inner/outer vertex pairs along
   the requested angle range and two triangles per segment. Map the existing colour ramp across the band, with a
   narrow alpha fade at both edges for smooth borders. The standard HUD texture shader suffices.
3. Render the dark track, then the resource band up to the current fraction. Render the existing damage trail over
   the corresponding angular interval; keep the current short fade. Cache the fixed arc sample positions and adjust
   only the last segment at the live fill boundary.
4. Reposition the existing selection/aggro/buff elements from the draft. Keep their current input and visibility
   rules. No-mana and nobody-ready behavior already exist in the renderer.

At 48 segments per half-arc, ten full resource fills for five PCs are about 960 triangles; tracks add a similar
amount. That is a small geometry budget. It is an estimate, not a measured performance result. Batch arcs sharing a
texture and retain transient-buffer bounds checks; don't submit a separate draw for every small segment.

The existing short-line batch path could make an initial implementation with little code, but a connected band is
preferable for production: it avoids dark seams from overlapping alpha at joins and gives controlled end caps.
Final native work should check empty/full/tiny fills, the 66%/33% thresholds, damage trails, the no-mana class,
selection when all PCs recover, enlarged/small HUD scales and 4:3 party sizes.

## Review status

**A is user-approved and integrated.** The retained browser comparison and its `checks.json` describe the original
proposal. The [native record](native/README.md) is authoritative for current geometry and verification; the earlier
[vertical basebar captures](../obsidian_engine_handoff_20260928/refinement_party_basebar/index.html) are historical.
