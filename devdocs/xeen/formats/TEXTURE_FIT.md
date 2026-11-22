# Texture fit: pictures meant once, bands, seams and the wall round them

The user (2026-11-20): "tiling of stuff which doesn't fit, e.g. on the walls: continuous textures with like a window
which has a different background, or just some tiles which aren't really fitting in the tiling". `oymap audit` runs
the check on every Xeen map, indoor and outdoor (others with `--textures`; `--textures-measure` prints each surface's
numbers and each pair of neighbouring surfaces; RPC `check.audit` `textures`). Code:
`openyamm-studio/core/TextureAudit.cpp` (`auditTextureFit`); data: `assets_dev/engine/models/texture_classes.yml` and
`assets_dev/worlds/xeen/models/texture_classes.yml`, written by `tools/xeen/texture_classes.py` from the pictures,
their names, Xeen's registry (`source/textures.yml` `kind`), the shipped maps and the hand-written
`tools/xeen/texture_classes_overrides.yml` (A6 reviews it). Door pictures are the door check's ([DOORS.md](DOORS.md)).

## Surfaces

The check judges surfaces, not faces: the touching faces of one texture in one plane whose pictures continue each other
(the same texels per unit, offset by whole pictures). A window drawn over two faces is one surface showing it once; a
window laid again on the face beside it at its own size is one surface showing it twice. Copies across (down) = the
texels the surface spans over the picture's width (height). "Whole" = the longest unbroken share of the picture the
surface shows that way (a picture's own edge inside the surface breaks it). A surface under 16 either way (a jamb's
edge, a frame's side) is not judged.

## Classes

Each texture of the shipped and Xeen maps has a row in `texture_classes.yml`:

| Field | What |
| --- | --- |
| `class` | `feature` (meant once: a window, a sign, a picture, a panel, a door picture), `tile`, `trim_u` (a band: repeats along its width only), `trim_v` (a strip: up its height only), `flat` (one colour: the dark faces of ways in; never judged) |
| `tiles` | [across, down]: it repeats cleanly that way: its edges meet (`seam` 3 or under) or the shipped maps show it 1.6 times or more that way on one surface (`used`) |
| `seam` | [across, down]: the step across the wrap seam over the median step between neighbouring texel columns (rows): about 1 where the edges meet |
| `used` | the most copies across and down any shipped surface shows |
| `border` | the mean colour of the picture's outer ring; `material` its surface-material class where it has one |
| `motif`, `mirror` | measured only (the middle against the border; the mirror likeness): see the calibration |

A texture is a `feature` by Xeen's registry (`kind: picture` or `sign`), its name (`win`, `wndw`, `sign`, `sgn`, `pic`,
`panel`, `banner`, `crest`, `notice`, `portrait`, `tapest`; not bookshelves or wine racks, which the originals run
along whole walls), its door role (a single leaf's picture or a wing), or as a panel: its edges clearly apart both ways
(`seam` 5 or more each way) and the shipped maps laying it whole once wherever they use it (a wall's end post, a shop
sign, a carved panel). Cut-outs and derived cuts of the registry are measured (a portcullis or a cage's bars repeat
across). Otherwise a band (`trim_u`) when it repeats across and its top and bottom are clearly apart (`seam` down 5 or
more), a strip (`trim_v`) the other way, else a `tile`. The overrides win over everything measured.

## Checks (numbers measured on the shipped MM6–MM8 maps)

Measured over the 203 shipped maps: 366,289 surfaces, 174,670 pairs of neighbouring surfaces of different textures in
one plane (`output/xeen_a1/fit/fit_mm678.txt` lists every finding there; the shipped maps stay as they are, D-7.2).

| Code | Severity | Rule | Shipped |
| --- | --- | --- | --- |
| `textures.feature_repeated` | error | a feature shown more than 1.3 times across or down its surface | 97 |
| `textures.feature_cut` | error | a feature whose surface (48 or more that way) shows no unbroken 70 % of it across or down: cut off, or split by its own edge | 16 |
| `textures.trim_tiled` | error | a band shown more than 1.3 times up its surface (a strip across) | 54 |
| `textures.storey_stacked` | by texture (D-41): error for `storey_stack: edge`, none for `module`, else warning | a picture one storey high (256) stacked whole up the wall, its first copy at its edge, two or more times: a storey panel per storey, or a frieze or window row repeated up the wall. `edge`: a footing or eaves panel meant once per wall (`hkm3b`, `hkm3el(w)`, `hkm3er(w)`, `t07b0*`); `module`: made to repeat once per storey (half-timber frames, one window or slit per storey, cage bars); the lists are in `tools/xeen/texture_classes_overrides.yml` (A6) | 0 (all 23 `module`) |
| `textures.tile_seams` | warning | a texture whose edges do not meet that way shown twice or more that way | 0 |
| `textures.feature_border` | warning | a feature set into a tile (an edge of 32 or more shared in one plane) whose border colour is more than 60 from the wall's (mean of the R, G, B differences) | 24 |
| `textures.family_switch` | warning | two tiles side by side along one wall (an edge of 64 or more) more than 80 apart in colour, with no trim, pillar or corner between | 315 |

The shipped findings: MM6's window rows (`gbwin`, `whwin`, `strwin1`, `mswinm`, `deswin1`) laid along whole walls (the
user's example); MM7's storey bands shown 1.5 times up a face (`t5s1b`, `hwm1bs1`, `hwm1b`); MM7's wall-end posts cut on
narrow faces (`hkm3el`, `hkm3er`). Every warning is fixed or kept with one line under "Texture fit exceptions" in the
map's NOTES.md (as the dressing's).

## Calibration

- **The pixel measures alone do not tell a picture meant once from a wall.** Over the textures the shipped maps repeat
  (2.5 or more copies on a surface) against the shipped windows, signs and door pictures, the seam ratio across keeps
  90 % of the repeated textures at 3 or under, but half of the windows measure seamless too (a window painted on the
  wall's stone meets itself at its edges); the motif score (middle against border) came out lower for the windows than
  for the walls. So a feature comes from the registry, the name, the door role or the panel rule, and the pixels decide
  only which way a texture repeats cleanly (`SEAMLESS` 3: 90 % of the shipped repeated textures across, 86 % down;
  `TRIM_SEAM` 5: 4–6 % of them measure past it).
- **Cut** at 70 %: the shipped signs on boards narrower than the picture show 74 % (MM7's `sign01-*`, `wharsign`) and
  stay out; shipped surfaces 48 or more wide flagged at 50 % 5, at 60 % 13, at 70 % 16, at 75 % 31 (the wall-end posts
  on narrow faces).
- **Border** at 60 (feature beside tile, 1,147 shipped pairs: median 4, 95th percentile 43, 99th 73).
- **Family** at 80 (tile beside tile along a wall, 24,407 shipped pairs: median 6, 95th percentile 44, 99th 91); the
  surface-material classes are known for too few textures to judge by.
- **Storey panels**: the studio lays walls in rows of 256 and its kits' panels are one storey high (`hhm2b2`, `t07b01`,
  `t1wl9ctl`), so a house of two storeys stacks them; whole stacked copies are a warning, a band shown 1.5 times (a
  storey panel on a wall 384 high, or a wall whose texels do not start at the panel's edge) an error. Decision D-41
  sets it per texture: an `edge` panel stacked is an error (fix: a plain wall of the same kit with the panel once at the
  foot or eaves, `upper_walls`), a `module` stacked is right, any other stacked panel stays a warning, kept with one
  line per texture under "Texture fit exceptions" in the map's NOTES.md.

## Studio words

- `textures.<role>: {texture, fit: true, size: [w, h]}` on a building part: the picture (its size in texels) laid once
  over each bay of the role, stretched to the bay (a 192 window bay shows its 128-wide window once); the rows above the
  lowest lay such a bay as plain wall unless `upper_walls` names the role (no window or frieze repeated up a wall
  taller than one row).
- An open part's posts and a porch's posts in the `trim` (no `post` role) lay the band on its end, along the post.
- `raise` on `kind: wall`: the whole wall (foot, top, batter and gates) stands that much higher than the land.
- Indoors a surface's `fit: true` (with `size`) stretches the picture once over each face, as before.
