# New Sorpigal geometry pilot

> **Shelved 2026-11-12 (experimental).** Start with [HANDOFF.md](HANDOFF.md): what was tried, the open issues and how to resume.

Tier A of the [geometry study](../../geometry_study_20261111/README.md) built for real on seven BModels of
`oute3.odm`: the Armory (51, `ArmoryW`), the tavern (80 `TavFrntW`, 79 `TavBckW`), the stone bridge (20,
`BridgeE_1`) and Goblinwatch (70 `EvilKC`, 71 `EvilKL`, 72 `EvilKR`). Not installed: the map lives in
an isolated stage (`playtest/assets_dev`, hard links to `assets_dev` except the changed map files).

**Whole town (2026-11-11):** every BModel except crates, signs, the ship and the obelisk has a detail model: 61
models, +94,600 triangles (47,673 faces) over the map's 8,322. Seven are hand-tuned (`source/maps/oute3.yml`), the rest come
from the automatic pass (`auto: true`; rules in [PLAYBOOK.md](PLAYBOOK.md)), with `extend: true` entries for the
tower, the gate and the dock. Lighting: 79.5 MB against 17.2 MB for the unchanged map (detail at 4 units per texel on
the hand-tuned models, 12 on the rest; the size follows the face count more than the density). Review:
`review/town_original/`, `review/town3/`, `review/town_town3/` (concept sheets from `concepts/`, Codex level-A edits
of the town poses).

The hand-tuned buildings:

| Building | Original triangles | Added triangles | Added faces | Hidden original faces |
| --- | ---: | ---: | ---: | ---: |
| Armory | 134 | 1,636 | 834 | 26 |
| Tavern front | 195 | 2,352 | 1,213 | 26 |
| Tavern hall | 176 | 2,551 | 1,296 | 7 |
| Bridge | 112 | 1,896 | 948 | 0 |
| Goblinwatch keep (with the castle-wide plinth, quoins, cornice, gate frame) | 183 | 6,239 | 3,118 | 21 |
| Goblinwatch left wing | 157 | 1,170 | 593 | 17 |
| Goblinwatch right wing | 177 | 1,220 | 618 | 22 |

Two generated textures (Codex, `textures/codex/`, source set by `source/make_textures.py`): `gwashlar` (dark basalt
ashlar: Goblinwatch trim) and `lgashlar` (light granite ashlar: bridge coping and arch, Armory plinth).

## What it does

- **Relief from the texture.** Each wall face whose texture is listed in `source/textures.yml` gets a depth level
  per texel from the texture's surface material class map (`assets_source/worlds/mm6/surface_materials/<t>_m.png`):
  wood stands proud, glass and doors are set into the wall, carved bands stand a little proud. Doors whose class map is
  all wood use rectangles instead (`pxstrdr`). The levels become integer polygons in the face's texture space
  (OpenCV contours, Shapely on a one-unit grid, earcut, convex merge), faces at their depth and side walls where the
  depth steps. Every new face keeps the original texture and texel mapping, so the 4x masters and the surface material
  maps (normals, parallax) apply unchanged.
- **Sills, posts, roofs, coping, arches.** Window sills under every glass region; the Armory's gable roof rebuilt
  with a 10-unit slab, 24 units more eave and 16 more gable overhang, rafter ends and a ridge beam; the tavern's four
  square porch posts replaced by chamfered posts on bases with capitals and diagonal brackets. `roof_trim` adds caps
  on every hip and ridge, a fascia under the eaves and rafter ends (tavern hall, Goblinwatch roof and spires);
  `coping` lays jointed stones (or one rail) on thin top faces (bridge parapets, wall walks, balcony); `arch_ring`
  rings an arch opening with voussoirs on both faces (bridge). Goblinwatch's painted corner pilasters are rectangles. Trim on the Armory uses the painted rail
  of `PXSTRST` (rows 166-181), so no new texture was needed.
- **Gameplay unchanged.** The detail is one new BModel per building, appended after all 90 original ones, with every
  face Untouchable. The replaced original faces get Invisible (in the ODM and in the scene's `legacy_attributes`):
  they are not drawn, clicked or baked, but they still collide. Faces made from a clickable face keep its event and
  Clickable bit, so the doors work through the new recessed door faces. All original ODM records are byte-identical
  apart from those attribute words; `build.py` asserts it.
- **Lighting.** Baked with the map's own profile plus `model_units_per_texel` (4 instead of 32 for the detail models,
  an opt-in key added to `tools/lighting/bake_outdoor.py`). Baked with today's tool at 64 samples, the sidecar goes
  from 17.2 MB (unchanged map, `build/rebake_original`, stage `playtest/rebake`) to 36.4 MB for these seven BModels;
  a whole town needs a coarser detail density.
- Steps along a relief face's bottom edge are skipped: lying on the terrain, they baked black patches into it.

Process and lessons: [PLAYBOOK.md](PLAYBOOK.md).

## Run

```sh
cd level_generation/projects/mm6_sorpigal_geometry_pilot
python3 -m venv venv && ./venv/bin/pip install shapely opencv-python-headless mapbox-earcut numpy pillow pyyaml
python3 source/build.py            # generate, append, scene, stage (drops the stage's stale bake)
python3 source/build.py --bake 64  # bake the stage (16 samples by default: ~25 s draft) and install it there
python3 source/run_checks.py       # the three doors still open their events
./source/capture.sh final          # original vs pilot screenshots, review/cmp_final/
```

Play it: `./tools/run_game.sh --isolated geo_pilot --assets $PWD/level_generation/projects/mm6_sorpigal_geometry_pilot/playtest/assets_dev --world mm6 --map oute3.odm --visible --seconds 0`
(from the repository root).

## Checks done (2026-11-11)

- `run_checks.py`: Armory door (event 5), tavern door (11) and the upper tavern door (60) activate through the new
  model (BModel 90/91).
- Walking into the Armory wall, the tavern porch and a porch post stops at identical distances on the original and the
  pilot map (headless `movement_segment`, scenarios in `build/collision/`).
- Desktop captures of 18 poses in `review/rebake_original/` (unchanged map, same bake) and `review/final4/`;
  side by side in `review/cmp_final4/`; concept A | original | result in `review/concept_final4/`.

## Known limits

- The baked lighting is soft at this sun angle; small reliefs read mostly at grazing light and with ambient occlusion.
- T-junctions between the base faces and the side walls can show a faint seam on some plaster.
- Plinths along wall bases are not done (they need the terrain height along each wall).
- A map rebuilt like this resets its saved state when entered (party kept), as any changed map does.
