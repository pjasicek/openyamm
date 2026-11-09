# MM9 Fleet Foot art (2026-11-09)

In the MM9 world the Air spell in Fly's slot (spell 21) is MM9's Fleet Foot, a run-speed buff whose art is a pair of
winged boots. This project makes its two pictures in the engine's HD style. The engine resolves icons from the active
world's `worlds/mm9/icons_x2/` before `engine/icons_x2/` (`engine/icon_packages.txt`), so a file there with the
engine's name shadows the engine's picture only while MM9 is mounted.

Installed (lowercase, 0644):

| File in `assets_dev/worlds/mm9/icons_x2/` | What |
|---|---|
| `sba10a.png`, `sba10b.png` | Spellbook picture, highlighted (colour) and normal (sepia), 300 x 298 RGBA: shadows Fly's pair. |
| `fleetfoot01.png` .. `fleetfoot08.png` | HUD movement indicator, eight 128 x 128 RGBA frames (new names; the engine binds them). |

Previews: `previews/spellbook_fly_vs_fleet_foot.png` (engine Fly pair, then the Fleet Foot pair, on a dark background),
`previews/hud_sheet.png` (MM9's native frames at 4x nearest above the new frames), `previews/hud_loop.gif` and
`hud_loop_2x.gif` (the loop at 0.16 s a frame), `previews/hud_moving.png` (pixels that change in the loop: only the
wings), `previews/sepia_check_fly.png` (the sepia derivation applied to Fly's own colour picture, beside the original
sepia picture).

## Spellbook picture

- Codex's built-in image generation (`codex exec`) paints the highlighted state from
  [CODEX_BRIEF.md](CODEX_BRIEF.md) and [art.json](art.json), with `refs/refs_air_vignettes.png` (original Air pictures
  as colour/sepia pairs: Fly, the sword and shield, Feather Fall, Jump) and `refs/refs_mm9_fleetfoot.png` (MM9's own
  picture, subject only). The subject is a running pair of boots seen from the side with white ankle wings and wind
  streaks, so it does not repeat Jump's standing pair of winged boots. The caption is new invented runes in Fly's
  layout (large teal-green glyph, two rows of small red-orange glyphs, bottom left).
- Four attempts: 1 (runes rejected by Codex), 2 (master `masters/fleet_foot.png`: an opaque dark backdrop and thorny
  runes, rejected), 3 (`scripts/retry_vignette.sh`, an edit of 2: sparse hatching, but hairline runes and a haze much
  paler than Fly's; `masters/fleet_foot_v3.png`), 4 (`scripts/retry_vignette4.sh`, an edit of 3 with
  `refs/refs_fly_caption.png`: Fly's caption weight and haze darkness; `masters/fleet_foot_v4.png`). **Attempt 4 is
  used**, although Codex's record marks it unselected (its doubts were the haze density and one glyph). At the
  installed size its haze and caption match Fly better than attempt 3. The one glyph that read as a "9" is mirrored by
  `build_spellbook.py` (`GLYPH_MIRROR_BOXES`).
- `scripts/build_spellbook.py` crops the master to its content and fits it into Fly's content box (12..290 x
  9..292 of 300 x 298). It derives the normal state as the MAW class spellbook study does: luminance mapped onto
  the median-colour sepia ramp of nine original normal pictures. The large rune keeps its teal-green, as in the
  originals; the rune is the largest green component in the bottom-left half, so pale green tints elsewhere are toned
  too. `--check` runs the same derivation on Fly (`previews/sepia_check_fly.png`).

## HUD indicator

MM9's `FLEETFOOTANIM.pcx` is eight 36 x 36 frames: a brown boot, toe right, with two dark wings at the top of the
shaft that flap (level, down in 2-4, level, up in 6-7, and frame 8 equals frame 1).

- Codex paints one boot without wings (`masters/hud_boot.png`) and one dark wing, root lower left and tip upper right
  (`masters/hud_wing.png`, second try; the first was too narrow), from `refs/refs_hud.png` (native frames enlarged
  above the HD Fly frames).
- `scripts/build_hud.py` finds each native frame's two wings: dark unsaturated pixels; the boot's one-pixel dark rim is
  removed by a horizontal opening. Masking out the shaft separates them into a left and a right component. The HD
  wing (mirrored for the left one) is warped onto each silhouette by an affine, fitted as for the Fly indicator
  (`movement_icons_20261108/scripts/fly.py`: moment matching over a rotation sweep, then Powell on the soft IoU), with a
  penalty that keeps its root at the ankle. A wing is drawn in front of the boot when the native frame shows it over
  the boot. Fits are logged in `out/hud_fit.txt` (IoU 0.47-0.73: the native wings are 36-pixel renders and the edge-on
  frames are one pixel wide).
- One boot for every frame, fitted to the native boot's box and toned to 85 % saturation (the painted leather was
  copper next to the native tan). It is identical in all frames. The native boot sinks by a third of a native pixel
  while the wings are up; that is left out, because a one-pixel HD bob reads as a twitch.
- Frame 8 is halfway between frames 7 and 1 instead of a copy of 1, so 7 -> 8 -> 1 is one even stroke and the loop
  has no hold (`--native-8` keeps the native copy).
- Composited at 512 px and downsampled once (Lanczos) to 128.

## Regenerate

```
cd level_generation/ui/mm9_fleet_foot_20261109
python3 -I scripts/make_refs.py
scripts/run_batch.sh            # attempts 1-2 and the HUD boot and wing (skips existing masters)
scripts/retry_vignette.sh       # attempt 3
scripts/retry_vignette4.sh      # attempt 4
python3 -I scripts/build_spellbook.py --check
python3 -I scripts/build_hud.py
python3 -I scripts/preview_hud.py
for f in sba10a sba10b fleetfoot01 fleetfoot02 fleetfoot03 fleetfoot04 fleetfoot05 fleetfoot06 fleetfoot07 fleetfoot08; do
    install -m 0644 out/$f.png ../../../assets_dev/worlds/mm9/icons_x2/$f.png
done
```

Spend: no paid API calls; 7 image generations on the Codex subscription (vignette 4, boot 1, wing 2).
