# BModel geometry detail playbook

> **Shelved 2026-11-12 (experimental).** Start with [HANDOFF.md](HANDOFF.md): what was tried, the open issues and how to resume.

How to give MM6–MM8 outdoor BModels (buildings, bridges, castles) real geometric detail without changing gameplay:
recessed windows and doors, raised timbers and pilasters, sills, roof trim, coping, battlements, plinths and
cornices. Worked example and tools: this project ([README](README.md)); background and concept edits:
[geometry study](../../geometry_study_20261111/README.md).

## Rules

- **Detail is a separate, untouchable BModel.** Append one `<name>_geo` model per building after all original
  models. Every new face is Untouchable. The original faces it replaces get Invisible in the ODM *and* in the scene's
  `legacy_attributes`: not drawn, clicked or baked, still colliding. Faces made from a clickable face keep its event
  and Clickable bit (the click ray skips Invisible faces, so the door must move to the new face). Nothing else in the
  ODM changes; `build.py` asserts it.
- **Same textures, same texel mapping.** New faces reuse the original texture and its UV mapping (one texel per world
  unit on walls), so the 4x masters and surface material maps apply unchanged. Trim (sills, fascia, beams) uses a
  painted beam inside a wall texture or a world-aligned projection of an existing texture.
- **Trim belongs to the material it sits on.** Coping, caps, sills, plinths, quoins and roof caps are a dressed or
  board version of the host texture: same colour family and grain, a step lighter and smoother. One borrowed light
  granite everywhere looked pasted on (dark rubble, red barn wood, orange roof planks; user, 2026-11-11). Textures are
  cheap: `source/trim_textures.py` writes one Codex job per host (`TRIMS`: host, use, content, colour), and
  `generate.py` picks the trim from the host's texture prefix (`STONE_TRIMS`, `ROOF_TRIMS`). `source/make_textures.py`
  writes the source set (x4 master, x2, native BMP, surface maps; `GAIN` brightens a trim to the concept's step)
  under `textures/root`, `build.py` cooks it into the stage only (`--only`), and the bake reads it through a second
  `--sources`. Installing it is part of the install.
- **Everything added is supported.** A post base is clipped to the floor it stands on (a base hanging past the
  porch edge was the first thing the user saw); nothing sticks out past an edge or floats.
- **Size and outline as in the concept, not just presence.** A thin strip does not match a thick overhanging
  capstone; a cap course does not match a plain pyramid. Leave out what the concept does not have (Goblinwatch's
  battlements, the gate's cap course).
- **Never put a face on the terrain.** A horizontal face lying on the ground bakes a black patch into the terrain
  (steps along a wall's bottom edge did this at Goblinwatch). Skip faces that are never seen from below.
- **Stage, never install by hand.** Build into `playtest/assets_dev` (hard links; replace files through a temporary
  file and rename). Installing into `assets_dev` is a separate, approved step.

## Whole maps: the automatic pass

Every map has its own file, `source/maps/<stem>.yml` (map, hand-tuned buildings, `extend` entries, `poses`,
`pose_scale` for foggy maps); wall texture depth specs are shared in `source/textures.yml`. `source/maps.py` has the
per-map paths (New Sorpigal keeps its pilot folders). A new map:

1. `source/maps/<stem>.yml` (copy a small one), then `python3 source/generate.py --map <stem>` and read the plan.
2. **Class and height maps first.** Relief reads each texture's surface material maps; in November 2026 only New
   Sorpigal's textures had them (44–93 % of the wall area of the next four maps had none). Run
   `level_generation/surface_materials/mat.py auto --world mm6 --map <stem>.odm --parallel 12` (two Codex calls
   per texture; about an hour for four maps). It installs into `assets_source`; the stage does not cook them, so
   before and after compare geometry only.
3. Inventory its wall and roof textures; every new host family gets a trim in `source/trim_textures.py` (`TRIMS`),
   mapped by prefix in `generate.py` (`STONE_TRIMS`, `ROOF_TRIMS`, `STONE_TOPS`, `TIMBER`), then
   `source/make_textures.py`.
4. `source/original.sh <stem>`: re-bake the unchanged map with today's tool and capture every pose (the fair
   before). Captures run with weather off (`video.weather_quality=off`); a map's own fog stays.
5. Pick 10–15 concept views from the captures (`source/contact.py`; drop poses inside walls) and run
   `concepts/run.sh <stem> <shot>...`.
6. `source/review.sh <stem> <run> [samples]`, `source/astra_review.py --map <stem> review/<stem>/<run>`, fix, repeat.

`auto: true` in the map file gives every BModel without a hand-written entry a spec from its own faces
(`generate.py`, `auto_texture_spec` and `auto_building`); `extend: true` entries add features to it, and plain entries
replace it. The rules:

- wall textures from their class maps: glass and lead set in (−12), wood proud (+5/+6) where it is 10–60 % of a
  plaster, stone or brick texture, clickable door textures (`dr`, `dor`, `door` in the name) recessed as a whole;
- sills under every window (the painted beam of `PXSTRST` on half-timber, the host's trim elsewhere: dressed stone,
  red boards on the barns);
- caps on every hip and ridge and a fascia under the eaves of sloped roof faces in the upper part of a model, in
  the roof's own family (`ROOF_TRIMS`);
- weathered coping (18 thick, 8 over each face, chamfered top) on thin top faces and a cap stone with a low pyramid on
  pier and pillar tops (`shaft_top`: not the tip of a pyramid roof), **stone textures only** (on wooden roofs and
  balconies it laid light blocks on the ridges);
- chamfered posts with bases and caps for square box posts;
- a plinth course for stone and brick buildings with storey-high stone walls (not well rings or planters), with
  doors kept clear; **never under half-timbering**: it hides the painted sole beam (user, 2026-11-11);
- **budget**: a face whose relief has more than 300 polygon corners per texture tile stays flat (rubble, snow,
  noisy class maps); plain beams, boards and logs (`PLAIN_TIMBER`) get no raised wood, only their glass set in;
  wood-on-wood walls (planks with painted beams, one class) take their frames from the height map's raised parts
  when those are a few large shapes;
- coping only on real wall tops (`wall_top`: walls go down from both long edges; stair treads got coping);
- rafter ends only where an eave overhangs a wall face by 10 units or more, spanning wall to fascia (`eave_overhang`);
- jambs and a lintel round every clickable door at the foot of a building; heads over rectangular windows;
- a stone footing under log and plank houses (`PLANK`), never under painted half-timbering;
- no bottom face on a plinth standing on the ground (a black patch spread round Free Haven's dungeon entrance);
- skipped: crates, signs, the ship (`auto_skip`; it has a hand entry with wales), and plank, sign and crate
  textures.

Review a whole map with `source/town_tour.py` (a raised three-quarter pose in front of every building's door plus
hand-placed poses; ground-level poses landed inside trees and neighbouring buildings) and
`source/town_compare.py` (concept / original / result for every concept pose, before/after pairs for all).

## Steps

1. **Pick the poses** for the building: the user's view plus close, oblique and silhouette views. Add them to
   `source/tour.py`.
2. **Concept first.** If the building has no concept edit yet, make one with Codex from the engine capture at the main
   pose (study `briefs/COMMON.md`, `run_concepts.sh`): version A only adds modular detail (recesses, frames, sills,
   timbers, roof slab and trim, coping, plinth, cornice) to the same buildings, textures and light.
3. **Dump and read the faces** (`source/dump.py <bmodel>`): textures, sizes, events, roof faces, thin top faces,
   arches, which walls reach the ground. Look at each wall texture with its class map
   (`assets_source/worlds/<w>/surface_materials/<t>_m.png`).
4. **Configure** the map file `source/maps/<stem>.yml` (wall texture depths: `source/textures.yml`):
   - per texture: depth by class (`wood: 6, glass: -12`), `rects` where the class map cannot separate parts (doors
     that are all wood, painted pilasters on plain stone), cleanup (`close`, `simplify`, `min_area`) for carved or
     leaded textures;
   - per building: `trim`, `sills`, `gable_roof`, `posts`, `roof_trim` (hip and ridge caps, fascia, rafters),
     `coping` (with `merlons` for battlements), `arch_ring`, `bands` (plinth courses, string courses, cornices with
     corbels, sliced from the walls at `slice_z`; `exclude` keeps gates clear).
5. **Build, bake, check.** `python3 source/build.py`, `python3 source/build.py --bake` (16 samples, about 30 s; 64
   for the final), `python3 source/run_checks.py` (every clickable door), and the collision walk if posts or walls
   changed. Compare against a re-bake of the unchanged map with the same tool (`build/rebake_original`, stage
   `playtest/rebake`), never against the old installed bake: profile changes would look like geometry changes.
6. **Compare the result with the concept, not only with the original.** Run
   `python3 source/concept_compare.py review/rebake_original review/<run>` and read every sheet
   (concept A | original | result) at full size. Write down each feature the concept shows by name (plinth, cornice,
   corbels, pilasters, sills, window depth, roof edge, battlements, arch stones…) and mark it present, weaker or
   missing in the result. Fix the generator or the config for every weaker or missing one, or note why it is dropped.
   Repeat until the result reads like the concept at the main pose. "Looks about the same as the original" is a
   failed iteration, however many triangles were added.
7. **Independent review.** `python3 source/astra_review.py --map <stem> review/<stem>/<run>` gives Codex (its default model,
   gpt-6-astra) concept, original and result for every concept pose and original and result for every close-up
   (`close_*` in `town_tour.py`), with the rules above and none of our notes; it writes
   `review/<run>/astra/<shot>.md` ending in `VERDICT: PASS` or `FAIL`. Fix every finding that holds up when you
   look at the crop yourself (`source/crops.py`), and repeat until the poses pass. The user should not have to list
   occurrences: the loop finds them. `source/review.sh <map> <run>` runs build, bake, tour and checks in one go.
8. **Show** the user concept, original and result at the same poses (the review page), with triangle counts and the
   lighting file size.

## Lessons

- **Silhouette kit over texture relief (user, 2026-11-12).** On whole towns the texture relief (painted timber
  raised 5–6 units, windows set in 12) took most of the triangles and could not be seen from play distance, and the
  12-unit recesses baked black. The concepts' gain is a short kit of large pieces: eave lips with fascia and rafter
  ends, corner posts or stones, door frames with a step, full window frames, a footing. `generate.py --kit <models>`
  (`kit_building`, `kit_texture`, `build_eave_lips`; `source/kit_run.sh` for a prototype) builds it: −41 % triangles
  on six buildings, and the eave line reads at every distance. Judge at street level as well as at the raised
  concept view (`source/kit_tour.py`).

- **Dark textures hide small depth.** On Goblinwatch's black rubble, 12-unit window recesses and 8-unit pilasters
  were invisible; the first pass looked the same as the original (the user saw it at once). Dark materials need
  forms that change the outline or cast large shadows (battlements, plinths, quoins, cornices on corbels, gate
  frames) in a contrasting dressed stone. The same rubble as trim reads as nothing; busy light cobble (`Rblst`) as
  trim overshoots. A generated dark basalt ashlar (`gwashlar`) matched the concept.
- **Silhouette beats surface.** Roof slabs and eaves, porch posts with brackets, coping and battlements read from
  every distance; raised timbers read only at grazing light.
- **Per-face lightmap charts cannot be the answer.** Every detail face got its own chart (4×4 minimum plus 4 texels
  of padding): the whole town went from 17.2 MB to about 80 MB whatever the density, and the user's limit is the
  original size. The detail must borrow its host face's chart and get its small shadows at run time
  ([lighting proposal](LIGHTING_PROPOSAL.md), option A); until then a whole-town bake is for review only.
- **Outlines of several models rarely close.** Bands are built per wall slice (strips in front of each wall, extended
  past the ends and merged), not by closing a footprint polygon.
- **Integer grid.** Vertices and texture coordinates are integers; polygon operations run on a one-unit grid
  (Shapely `grid_size=1`) so new faces line up with the texels.
