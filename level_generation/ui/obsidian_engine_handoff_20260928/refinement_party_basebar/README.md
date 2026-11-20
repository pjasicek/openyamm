# Dynamic Obsidian party basebar

Native implementation of the user's 2026-09-29 follow-up. [Open the native review](index.html), with selectable
one-, three- and five-member captures and a 4:3 example. This implements the requested direction; visual feedback
on the new basebar is still pending.

The user subsequently selected A from the [2133 curved-meter study](../../obsidian_curved_portraits_20260929/README.md).
Its [native integration](../../obsidian_curved_portraits_20260929/native/README.md) now replaces this vertical version,
with a fitted bottom-anchored frame and compact ornaments. The captures and geometry below are the earlier stage.

The gameplay portraits now sit inside one shared Carved Obsidian frame. Its width follows the active party count
and remains centered: `22 + 80 × members` logical pixels for one to five members. The middle uses the existing
fixed-scale reading surface and tiled Obsidian border. The existing portrait artwork stays at the accepted 10%
increase. A new worn-brass/obsidian flourish extends outside each end of the bar; the right end mirrors the same
true-alpha sprite, preserving symmetry at every party size.

HP and mana are vertical, filling from the bottom, in narrow recessed tracks to the right of each portrait.
HP retains the green/yellow/red 66%/33% thresholds and short damage trail; mana retains its blue shading.
The health gradient runs across the narrow track so it still has a beveled appearance. Characters with zero
maximum mana draw neither a mana fill nor an empty mana track. Selection, recovery arcs, alert diamonds,
personal buff medallions and portrait input remain attached to their live slots.

The fixed 4:3 inventory/dialogue basebar keeps its earlier geometry and horizontal meters; the new dynamic frame
is for gameplay. The shared desktop/Android gameplay YAML uses this layout; Android touch additions remain the
separate follow-up requested by the user.

This pass also completes the [2131–2132 refinement](../refinement_2132/README.md): smaller uniform resistance gems,
the three-unit buff-panel inset, minimap shading/time, the right-edge followers head/panel, and standalone animated
movement buffs with no Fly/Levitate/Water Walk badges on the skull.

## Installed assets

- `assets_dev/engine/icons_x2/obsidian_party_endcap.png`: generated with the built-in imagegen tool; copied unchanged.
  [Exact prompt](prompts.json), [source, alpha and hash receipt](artwork.json).
- `obsidian_party_meter_track.png`, `obsidian_party_meter_sp.png`: native SVG gradient/track exports. Sources in `art/`;
  `export_chrome.py` rasterizes only those SVGs.
- `assets_dev/engine/ui/gameplay/gameplay.yml`: five slot templates, width/stride, vertical meter rectangles and
  compact standalone animated flight/water-walk indicators.
- Shared resolver/renderer/skin code sizes the frame, centers the used slots, mirrors the ornament and draws the
  resource fills. Texture sizes and unchanged generated PNGs are independent of party count.

## Checks

Normal development build and focused doctest coverage pass: **14 cases, 428 assertions**. These cover movement
buff classification/precedence, vertical fill and damage-segment geometry, HP thresholds, clock rollover,
layout ownership and circular-map clipping. Commands/logs and native run/image hashes are in
[validation.json](validation.json). Native checks include party sizes 1/3/5, 4:3, no-mana Knight, follower
open/close/scroll bounds/NPC dialogue, and Water Walk animation plus held-RMB movement-buff inspection. The flight fixture checks its grounded
indicator; active-flight timing continues to use the existing movement-dependent animation code.

Captures use the authorized isolated desktop launcher and the normal OpenGL build. They are visual/interaction
checks, not performance measurements. No Vulkan or Android build was run.
