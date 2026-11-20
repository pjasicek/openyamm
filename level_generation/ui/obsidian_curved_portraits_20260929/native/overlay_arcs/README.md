# Matching curved portraits in full-screen overlays

Integrated on 2026-09-29 at the user's request to carry the gameplay portrait style into inventory and the house/talk
HUD. [Native review gallery](../index.html#overlay-inventory).

`assets_dev/engine/ui/gameplay/gameplay.yml` now gives all five `ObsidianOverlayPc` slots the same split HP/mana arcs,
inner selection rim, top diamond, lower-left aggro/recovery indicator and lower-right personal buff medallion as the
gameplay row. The existing shared renderer handles both; no separate overlay rendering code or new artwork is needed.

The fixed 640 × 480 canvas, carved 640 × 114 basebar and clear 22.4-high status/input rail stay intact. Overlay portraits
retain their 45⅓ × 60.266667 logical size. Their centres are x=58, 152, 246, 340, 434, with slots starting at y=28 inside
the basebar. Empty-slot banners align with those centres. The 4.6-wide HP/mana arcs and 20 × 20 selection diamond match
gameplay; the ellipse radius fits the existing, slightly smaller overlay portraits. All rendered elements, including
the larger aggro artwork, stay below the input rail and above the bottom border.

HP colours, live mana, short damage trail, recovery and buff interaction use the existing shared behaviour. A character
with zero maximum mana has no mana arc or empty track. Full-screen selection continues to identify the inspected party
member while recovering; the existing gameplay rule still hides selection when nobody can act. The shared overlay row
is also used by stats, skills, awards, spellbook, rest, journal, quick reference and other full-screen HUD states.

## Verification

- Built `openyamm_unit_tests`; the existing Obsidian suite passed **14 cases / 1,162 assertions**. Its obsolete
  horizontal-overlay assertion now expects the curved configuration. See [tests.log](tests.log).
- Checked all 35 portrait elements against the reserved rail and frame, matching arc parameters to gameplay and
  confirming that portrait dimensions and unrelated layout entries are unchanged. See [geometry.json](geometry.json).
- Four isolated native runs exited successfully on **OpenGL 3.3, NVIDIA, SDL Wayland**, producing 15 screenshots.
  Reviewed inventory, fourth-member selection, buff interaction, stats, house topic dialogue, bank input and a
  1280 × 960 one-Knight inventory with no mana gauge and four empty slots. Widescreen runs use 1600 × 900.
- Bank tours exercise deposit/withdrawal entry and submission. The amount and caret remain unobstructed in the rail.

Runtime changes are layout-only and are loaded on game startup. The development executable already contains the
shared arc renderer from the approved gameplay implementation. Native runs use isolated copies of existing fixtures;
normal saves are untouched. Android uses this shared layout, but no device/APK check or release ZIP repack was performed.

[validation.json](validation.json), `tours/`, `runs/` and `images/` retain the verification record.
