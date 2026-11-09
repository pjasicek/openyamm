# Smoother portrait outlines and clearer HUD text

Implemented on 2026-09-29 after the user reported a blurry Attack label, jagged HP/mana outlines and selection rim,
and a soft minimap clock. [Before/after review](index.html) uses unmodified native screenshots; enlarged details are
CSS crops with nearest-pixel sampling so their actual edge coverage stays visible.

## Changes

The arc material's former edge fade occupied a fixed fraction of the stroke. On thin rings it became a fraction of
a screen pixel, producing hard stair steps despite sufficient curve segments. `submitHudTexturedArc` now maps the
same material through four vertices per cross section: transparent outside, solid core, solid core, transparent
inside. Each edge transition stays one screen pixel wide, centred on the designed boundary. Strokes thinner than a
pixel reduce their peak opacity so their integrated coverage still equals their specified width.

The same code smooths HP/mana fills, metal outlines, damage trails and normal/selected inner rims in gameplay and
full-screen overlays. Portrait dimensions, logical stroke widths, colours, arc angles and live resource behaviour
are unchanged. Each band still uses one submission and the existing texture shader/material cache. No new shader,
MSAA setting or global texture-filter change is required. Transient geometry has four vertices per cross section
and three quads per segment, with the existing allocation checks.

In `gameplay.yml`, the phase label's Lucida scale increases from 0.40784314 to 0.7, and the minimap clock from 0.52 to
0.7. Their 11.9-logical-pixel font height fits inside the existing 12.8 and 14-high rows. The recreated font, soft
ivory colour, positions, plates and secondary Turn based/AP line remain unchanged. This prevents shrinking the
font's fine strokes to the tiny sizes seen in the feedback. The font's existing smoothing and rounded text origin
continue to apply.

## Verification

- Normal `openyamm` and `openyamm_unit_tests` builds passed. No Vulkan build was run.
- Focused Obsidian coverage passed **15 cases / 1,332 assertions**, including new checks for a constant edge fade,
  correct coverage from subpixel through large strokes, and equal fade widths around the ellipse.
- Final native captures cover 1600 × 900 gameplay, selection and inventory, plus 800 × 600 Attack/Movement phases
  and inventory. Both isolated runs exited successfully on OpenGL 3.3, NVIDIA, SDL Wayland.
- The smaller window exercises a one-member, zero-mana Knight; the wide run uses five members and all HP colours.
  The full-screen capture confirms the shared smoothing and clear status rail.
- The browser comparison was captured and inspected. Native screenshots retain original pixels; no image cleanup
  or asset repainting was applied.

See [validation.json](validation.json), [tests.log](tests.log), and `tours/`, `runs/`, `images/`, `reference/`.
Initial label-only captures are preserved in [turn_label](../turn_label/README.md).
Android shares these runtime changes, but no device/APK check or release ZIP repack was performed.
