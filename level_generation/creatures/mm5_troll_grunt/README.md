# MM5 Troll Grunt → MM7/MM8 sprite adaptation

## Current visual direction

The user rejected the first 160-frame set's apparent resolution and rendering style, then selected
**[front-idle option A](style_front_v2/A_faithful_render.png)** from three new 1024×1536 masters.
Use [the selected style study](style_front_v2/README.md) as the visual authority for future generation.
The user subsequently authorized [end-to-end production from master A](master_a/README.md); that document records
the permanent original-MM5-to-selected-master mapping and the current production outputs.
The atlas and reviews below describe the earlier iteration; their technical checks do not imply user style approval.

Open [viewer.html](viewer.html) for animation playback and frame scrubbing. The package is staged here;
it does not overwrite original sprites, register live creature IDs, or install a monster into gameplay.

See the [five-view comparison](review/overview.png), [160-frame contact sheet](review/all_sprites.jpg),
and [final acceptance record](review/acceptance.json). The contact sheet is a reduced review image;
the full-resolution spritesheets are the six `atlas/base_*.png` pages described by `manifest.json`.

## Choice and scope

The Troll Grunt preserves a particularly readable MM5 identity: teal skin, shaggy red hair, a ragged blue vest,
purple trousers, a yellow rope belt, dark cuffed boots, and a simple wooden club. Its uncomplicated humanoid
silhouette provides a useful comparison with the native MM8 troll and MM7 goblin. The
[comparison references](references/mm7_mm8_style.png) use the actual native palettes, rather than embedded BMP colors.

The original Darkside resource is `DARK.CC/056.mon` (eight frontal frames) plus `056.att` (four attack frames).
The unpacked PNGs use `mm4.pal`; their original per-frame drawing origins are retained in `sources.json`.
The `dark.mon` table contains the name **Troll Grunt** in record 56. Records 81, 82 and 83 reference the same sprite
resource and are named Troll Guard, Troll Chief and Hobstadt. Only one decoded appearance is established here;
no additional native palette appearances have been invented.

This is **new creature and motion authoring based on MM5**, not a claim that MM5 contained missing MM7/MM8 views.
MM8 Troll A (descriptor 58, groups `m477*`, textures `m476*`) supplies the motion layout and 125 ms frame timing.
Its motion reference was reflected as a whole for the right-handed MM5 design. The original MM8 clothing, skin,
weapon and head were not used as the final creature design. Art generation used the built-in image tool.

| Stored art | Per view | Five views |
| --- | ---: | ---: |
| Standing | 1 | 5 |
| Walking | 8 | 40 |
| Attack | 8 | 40 |
| Hit reaction | 5 | 25 |
| Fidget | 5 | 25 |
| Falling plus corpse | 4 + 1 | 25 |
| **Total** | **32** | **160** |

Five stored views cover front, front-left, left, rear-left and back. Three reflected aliases complete eight viewing
directions. Attack 2 reuses Attack. Death plays two existing hit frames followed by four falling frames, then holds
the separate corpse. Native timing/topology is explicitly adapted from MM8; it is not asserted to be MM5 timing.
Frame keys retain the motion-reference names for traceability within the namespaced `mm5:troll_grunt` package.

## Processing and deliverables

- `raw/`: original returned PNG sheets, including rejected/superseded versions where applicable.
- `prompts/`: exact generation and correction prompts; every action uses the selected identity reference.
- `references/`, `sources.json`: source pixels, original origins, source hashes, native palettes and motion provenance.
- `aligned/`, `cleaned/`, `masks/`: aligned RGBA masters, cleaned source cells and matching soft blue-vest coverage.
- `atlas/`, `manifest.json`: tightly cropped base/R8-mask pages with identical placement, animation timing and mirrors.
- `review/`: all-frame contacts, mask overlays, edge checks, registration measurements and animation GIFs.
- `viewer.html`: offline player; no web service or engine build is required.

The identity was established once across five views; the initial front-oblique direction was corrected in V2.
Targeted later repairs address a third arm, club-hand continuity and the abrupt roll into two final corpse poses.
The corrected rear-left strike uses a supporting second hand during its downward phase. The two supine corpse
frames and one recovery pose have explicit raw-sheet overrides and matching-head registration records.
Actual alpha is preserved. Faint exterior background dust is removed only beyond eight pixels from the silhouette;
thin semitransparent hair/cloth edges remain. A targeted green-contour audit repairs confirmed residual RGB spill
without changing silhouette alpha, followed by premultiplied-alpha resizing and the same audit on atlas extraction.

AI grid boundaries are approximate. Connected complete figures own their nearby soft pixels, and extraction uses
padded cells with an exact alpha-partition check. This prevents a nominal row boundary from cutting a club or boot.
One anatomical scale applies to a complete sequence. Head/boot comparisons provide explicit death and back-attack
scale overrides because hair coverage changes under foreshortening. Contact-based whole-frame translations preserve
the body scale. Authored falling poses use the ochre waist rope
as their lateral pelvis root and retain the native bottom-contact delta; they are never resized to standing height.

The shared working canvas has additional room for swings and prone silhouettes. Runtime-facing crop origins and
the logical pivot are explicit; no independent silhouette fitting is used. Crops reconstruct aligned masters exactly,
and every atlas rectangle is checked against both the RGBA frame and its mask. The base variant is an exact bypass.
The vest mask is authored on enhanced colors, not an enlarged native palette mask. Other native monster ranks share
the established base appearance; mask availability is not a claim that a particular alternate color was native.

Decoded allocation in `review/checks.json` includes **RGBA base + R8 masks + atlas padding**. It is the allocation for
one resident shared creature package, not an amount multiplied by the number of monsters. Mipmaps and engine
installation are separate work. Actual generated sampling is recorded separately from the physical 2× export tier.

The reviewed export contains all **160 frames**, with minimum generated sampling **2.103 pixels per logical pixel**
and **92.72 MiB** decoded allocation including masks and padding. Atlas reconstruction and mask coordinates pass
exact comparisons. One contour-color detector candidate is intentional teal nose shading in `m476db2`, visually
checked on light and dark backgrounds; no confirmed residual matte fringe was found. The vest mask overlays were
reviewed across all frames. Final review records include file hashes so later changes can be distinguished.

## Reproduce / resume

Requires Python 3, Pillow, NumPy and SciPy already available in the workspace.

```sh
python3 level_generation/creatures/mm5_troll_grunt/prepare.py
# Generation uses the saved prompts and built-in image tool; retain raw checkpoints.
python3 level_generation/creatures/mm5_troll_grunt/export.py
python3 level_generation/creatures/mm5_troll_grunt/build_review.py
```

On resume, inspect `raw/`, `jobs.json`, `registration.json` and review records before preparing anything again.
`prepare.py` rebuilds source sheets and base prompts; preserve saved correction prompts and selected raw versions.
`export.py --partial` is available for review during generation and explicitly reports missing batches.
Re-exporting deliberately resets the visual-review status; compare against `review/acceptance.json` and repeat
affected visual checks before accepting modified artwork.

## Limits

Hidden anatomy, back clothing, directional views and locomotion are inferred designs. The MM7/MM8-style shading is
new artwork rather than recovered high-resolution original art. A 2D generated set is not a rigged model; exact
cross-view geometry and in-between motion remain visual approximations. Mirrored aliases also reflect the club hand,
as in the native five-view/eight-direction sprite convention. Consult the final acceptance record for any specific
remaining visual fault; a numerical export check alone is not visual approval.
