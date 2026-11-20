# HUD feedback 2131–2132

Installed native refinement, 2026-09-28–29. [Native gallery](index.html). The subsequent
[party basebar](../refinement_party_basebar/README.md) is included in the final captures from this pass.

The six resistance gems now share a 24×24 source-placement budget (teardrops preserve their narrower shape),
replacing their inconsistent larger sizes. The warrior and skull group is inset three logical units from the
left edge below the shared strip. Existing true-alpha buff atlases are sampled unchanged.

The 112-logical-pixel circular minimap moves down 14 units to leave room for a small live clock above it.
The clock shares Rest's 12-hour formatter, including rounding at midnight. A soft transparent outer shade
restores separation from the world without the previous broad drop shadow. The resource strip remains flush
at screen (0,0), with its gold inset and no outer shadow.

The old right-facing followers head was redrawn in antique brass with built-in imagegen. Its 26×26 logical
button is flush with the right edge. It replaces the wide Followers caption/button. The original three-slot
panel and scroll/dialogue behavior use the shared Obsidian frame, inset portrait wells and matching chevrons.
The panel follows existing behavior: it opens on map load when hired followers exist. Scrolling clamps after
dismissal; empty panels have disabled arrows. All portraits and dialogue topics remain live game data.

The user's follow-up excludes Fly, Levitate and Water Walk from the skull. They have **no skull layer or badge**.
The existing `spell21` animation is a separate flight indicator for Fly or Levitate (Fly takes precedence if
both are active); `spell27` is the separate Water Walk animation. Both sit beside the panels and support
held-RMB inspection. Flight keeps the existing movement-dependent animation timing. The remaining skull
assignments from 2130 stay intact: Torch Light glow, Feather Fall clouds, Stoneskin material, Wizard Eye eye,
Day of the Gods halo and Protection from Magic garland. The timed overflow strip remains reserved for future
special modifiers.

## Sources and validation

- `art/obsidian_followers_head.png`: unchanged generated RGBA; [prompt](prompts.json), [receipt](artwork.json).
- `art/*.svg`: code-native tab, clock, scroll, portrait-well and minimap chrome. `export_chrome.py` exports these
  with librsvg/cairo; it never processes the generated image.
- [Atlas placement](atlas_registration.json): current source regions, reduced gem sizes and movement classification.
- `tours/`, `fixtures/`: isolated native checks; copied saves are review fixtures, not normal saves.
- [Validation](validation.json): native capture/run hashes and checks. Shared build/test results are recorded in
  [the basebar validation](../refinement_party_basebar/validation.json).

Authoritative runtime content is under `assets_dev/engine`, with behavior in shared `game/ui` and `game/gameplay`
code. Do not reinstall older staged payloads over the native layouts.
