# Brackenford terrain lab

An isolated copy of the Brackenford/Greywatch playtest for comparing terrain artwork.
The original authoring project, asset directories and staging pointer remain intact.
The native 128×128 height/tile grid, 512-unit spacing, hills, water, roads, BModels,
decorations, events and population are identical in all variants.

From the repository root:

```sh
level_generation/projects/brackenford_terrain_lab/play.sh native
level_generation/projects/brackenford_terrain_lab/play.sh smooth2x
level_generation/projects/brackenford_terrain_lab/play.sh ai2x
```

Choose **Load Game**, then the supplied **Scenario** entry. All three modes start
from the same level-25 test-party save, with separate settings and save directories.
The default launcher mode is `ai2x`. Close one mode before launching another.
Greywatch remains available through its normal entrance; its textures are unchanged.

| Mode | Terrain | Purpose |
| --- | --- | --- |
| `native` | Original 128×128 tiles | Reference, using the same anisotropic filtering |
| `smooth2x` | 256×256, Mitchell resampling | Conservative smoothing control; no generated detail |
| `ai2x` | Smooth control plus an AI grass sample | Test whether restrained new detail preserves the atmosphere |

Open [review.html](review.html) for a local, interactive tile comparison. It works
directly from disk. These enlarged samples are an inspection aid; judge the result
in the game at normal walking height too.

The AI sample uses the built-in imagegen tool, referenced to the original grass.
The exact prompt is in [reference/grass_ai_prompt.txt](reference/grass_ai_prompt.txt),
with the original and generated master beside it. The deployed main grass tile
mixes 40% of the resized AI image into the smooth control in its interior; the
weight fades to zero toward its edges. This deliberately retains the existing
grass/dirt boundary pixels. Other grass variants, transitions, rock, roads and
animated water currently use only the smooth control. This is a **grass style
pilot**, not a completed AI restoration of the tileset. No generated detail is
claimed for the other materials, and native seams/repetition are not repaired.

All resolved atlas tile names and animation frames are exported, including the
shore overlays. Legacy magenta is converted to alpha before resampling to avoid
pink shore fringes. Terrain alone uses the engine's existing `terrain_x2` tier.
The shared water animation masters already contain 256×256 pixels: the native
runtime reduces them to 128, whereas the 2× modes retain that existing detail.
Buildings, sprites, UI and the terrain mesh remain at their original settings.
The 256-pixel atlas costs approximately four times the native atlas storage;
the mesh size does not increase. Performance still needs evaluation on target hardware.

## Reproduce and iterate

```sh
python3 level_generation/projects/brackenford_terrain_lab/prepare.py
python3 level_generation/projects/brackenford_terrain_lab/verify.py
```

Requires the local development assets, built game, Python with PyYAML/Pillow and
ImageMagick. The checked content archive in `source/` freezes the original maps
and scoped registrations. Its installer rejects incompatible base tables.
The playable snapshot uses copied executable/maps/scripts/tables and shared
original art mounts; each experiment adds only its own terrain directory.
`playtest/`, `variants/` and `work/` are local generated directories, not a portable
game distribution. The authored image files and provenance manifest are retained.

Re-running preparation regenerates the tile exports and comparison settings, but
keeps existing player saves and the frozen playtest executable. Close the lab
before regeneration. To try artwork, modify the files in `tiles/ai2x/` and restart
the AI mode; a subsequent preparation replaces those edits, so keep masters in
`reference/`. Do not write through the original art mounts under `playtest/`.

Compare the grass at the same camera position, then walk over a grass/dirt seam,
a diagonal road and a shore edge. Look for loss of the muted palette, repeated
bright clumps, flat smooth patches, visible tile squares and water fringes.
The next step after choosing a look is a coordinated material/transition-family
pass, rather than independent creative edits of every transition tile.

## Initial review

All three modes passed faithful save loading. Verification checked all 15 frozen
package entries, 82 texture exports per mode, image dimensions, opaque magenta
removal and preservation of the AI grass boundary pixels. See
[review/validation.json](review/validation.json). The original project's staging
pointer still targets its previous playtest, and no engine code was changed.

The in-game grass comparison is embedded in the HTML review. The result stays
close in palette and is softer, with a modest change in grass structure. The
current AI blend is a starting sample for judging atmosphere, not a claim that
every tile has gained useful detail.

**Known issue:** thin dark/blue grid seams appear at some distances with 2× terrain
in the frozen executable. Switching from anisotropic to linear filtering did
not remove them; see [the linear check](review/gameplay/terrain_lab_grass_linear.png).
The map geometry is byte-identical and the grass boundary pixels match the smooth
control. Atlas padding/mipmap handling is a likely investigation target (the atlas
uses two physical padding pixels at both scales), but the exact cause is not yet
confirmed. Resolve this rendering issue before promoting a terrain set to normal
play. The supplied lab retains identical anisotropic 8× settings for the three modes.
The short Xvfb captures are visual checks, not performance benchmarks.
