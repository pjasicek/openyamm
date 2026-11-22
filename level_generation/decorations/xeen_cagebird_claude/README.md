# Xeen cage bird (DD-12's aviary), 2026-11-21

Lane S, session 10. `xeen_cagebird` (row 4015, sprite 27015, radius 0, height 50): a bright cage bird perched on a
bar in a small dark-iron tray that stands out of the wall under each of DD-12's eight cages (A8's aviary, the `xwcage`
panels 160 wide from 64 to 384 over the floor). The cage picture is a flat wall panel, so the decoration brings its own
cage floor. An animated decoration (`devdocs/ANIMATED_DECORATIONS.md`, the `animated:` kind) with one seamless idle
loop. No Meshy, no Codex: 0 credits.

## Deliverables

| File | What |
|---|---|
| `assets_source/worlds/xeen/models/xeen_deco_cagebird_anim.glb` | the skinned copy (binding `animated`), clip `perch`; = `export/xeen_deco_cagebird_anim.glb` |
| `assets_source/worlds/xeen/models/xeen_deco_cagebird.glb` | the rigid static copy (binding `model`, picking only); = `export/xeen_deco_cagebird.glb` |
| `integration/indoor_decorations.yml` | the binding fragment for `assets_dev/worlds/xeen/models/indoor_decorations.yml` (the lane lead merges it) |
| `scripts/cagebird.json` | palette, bird and tray dimensions |
| `scripts/bake_colour.py` | stage 1: skin `Crow_B`'s ramps baked into each texture set, plumage recoloured |
| `scripts/tray_texture.py` | stage 2: the tray atlas cut from `xwcage` |
| `scripts/build_glbs.py` | stage 3: both GLBs (clip, feet lock, tray, static LODs) |
| `scripts/render_review.py` | Blender review renders against a stand-in wall and cage |
| `scripts/tours.py` | the in-game menu-input tour on DD-12 |
| `review/renders/` | `sheet_views.jpg` (front, three-quarter, side, close, static), `sheet_clip.jpg` (eight moments of `perch`) |
| `review/ingame/` | `sheet.jpg`; `before/` (the aviary without birds) |

## Source

The bird is a Xeen copy of MM9's crow (D-44: Xeen does not reference `worlds/mm9/`), read from
`assets_source/worlds/mm9/models/mm9_crow.glb` (project `level_generation/creatures/mm9_crow_claude/`): its 28-joint
skeleton, its four LODs (7,467 / 3,732 / 2,985 / 1,863 triangles) and four shadow LODs, normal and metal/roughness
maps unchanged; the clips `Perch` (1.2 s) and `PerchFidget` (1.5 s).

## Skin

A decoration has no tier skins. The eagle skin `Crow_B` (MM9's BIRD.dtx through the region ramps) is baked into the
base colour of each texture set (body and head at LOD0/1, LOD2, LOD3) with `claude_shared/tier_textures.py`
`apply()`; the region mask, ramps, variants and the second skin are dropped. The eagle's brown plumage is then
recoloured by a gradient map (the baked plumage's lightness, ranked between its 2nd and 98th percentiles, picks from
olive-brown through gold to pale lemon), so the feather detail stays: palette `canary`, a canary-yellow songbird
with pale horn beak and pink-grey legs. The dark crow (`Crow_A`) read as a carrion bird; `budgie` (green body,
yellow head), `russet` and the plain `eagle` are kept in `cagebird.json` for comparison.

## Size, origin, facing

- Asset space in metres (x 100 = world units at the binding height 50), glTF +Y up, **+Z out of the wall**.
- **Origin: the tray's back edge middle on its underside** (the wall line at the panel bottom).
- Tray 120 wide (x ±60), 46 deep (z 0-46): a slatted floor 4 thick, a riveted rim 8 tall on the front and sides (open
  at the back, against the wall), an octagonal perch bar (radius 2, top 12 over the underside, 31.7 out from the wall)
  on two posts. 100 triangles in every LOD, one 256 atlas cut from `xwcage.png` (its bars as slats, its riveted cross
  bars on the rim), so the tray is the cage's own iron. Opaque, in the shadow LODs too.
- Bird: **38 over the bar** (the crow scaled 0.794; a perched crow at MM9 scale 100 is 58 tall with its drooping
  tail), turned 20 degrees off straight out; its tail rests on the tray floor at the back, the beak at the front rim.
- **Whole piece 50 tall** (0-50, = row 4015's height 50), 120 x 46 footprint.
- Binding `yaw: facing`, `yaw_offset: -pi/2`: the map's facing is the direction out of the wall.

## Clip and LODs

- One loop `perch`: 5.1 s, 30 fps, 154 keys: `Perch` three times, then `PerchFidget` once (it ducks forward and
  lifts its wings), each join blended over 6 frames; the last key equals the first (seam 5e-8). Placements play it out
  of step (the engine's idle offsets), so eight cages never move together.
- Feet lock: MM9's perched clips move the feet (Perch breathes them 3 mm, PerchFidget drops them 0.10 m), so each
  frame lifts the `Scene Root` by the feet's drop below the first frame: the feet stay on the bar.
- Rest pose = the clip's first frame; the static copy is every LOD skinned at that frame plus the tray, linked by
  `tools/link_static_model_lods.py`, its images at most 512 (never drawn).
- LODs: the crow's own chain, each with the tray: 7,567 / 3,832 / 3,085 / 1,963 triangles.
- The tray is skinned to a new still joint `Tray` (joint 28) beside the crow's `BirdPlace` node (the scale, turn and
  lift), so every LOD and shadow LOD is one skinned mesh.

## Placement rule (A8)

At **each cage's centre on the wall line, facing out of the wall, floor height = the panel bottom** (room floor
+ 64): north wall (y 3008) x -3168, -2784, -2400, -2016 at facing 270; west wall (x -3424) y 2624, 2240 at facing 0;
south wall (y 1600) x -3168, -2784 at facing 90; z -2496. Decoration `xeen_cagebird` (row 4015; a scene entity's
`decoration_list_id` 4014). No collision, no light.

## Checks

- `check_winding.py`: 0 inverted closed parts (both GLBs). Installed with `tools/install_model.py --world xeen`.
- In game (`build-xeen`, `xeen_dd12.blv`, 2026-11-21, `review/ingame/sheet.jpg`): the skinned copy spawned at the
  eight cages exactly as the binding places it (`model spawn`, scale 100, yaw = facing - 90 degrees) and looped out
  of step: each bird sits on its tray at the cage's foot, the tray meets the wall, two shots a second apart differ
  (`cage2_a`, `cage2_b`). Then placed as a real decoration from a hard-link scratch root (DD-12's two store_d small
  barrels rebound to the cage bird's fields; root deleted after): the idle loop plays, out of step (`placed_a`,
  `placed_b`).
- `--headless-validate-actor-models --world xeen` on the scratch root: 334 descriptors on 83 models, 0 refused (it
  reads actors.yml only, not decoration bindings).

## Open

- The `xwcage` panels' transparent gaps show the sky (`review/ingame/before/`), A8's to fix (an opaque backing, or a
  niche). **Better arrangement:** recess each cage 48-64 into the wall with the panel at the wall face and place the
  bird at the niche's back wall (the same rule on the niche's back line): the bird then sits behind the bars and the
  gaps show the niche, not the sky.
- The bird reads small against a 320-tall cage (38 over the bar, as briefed). A larger binding height scales tray and
  bird together (the tray would outgrow the 160-wide panel); a bigger bird on the same tray is `height_above_feet` in
  `cagebird.json` and a rebuild.
- One bird for every cage (stat birds, parrot, Songbird); no per-cage colours (one binding, no tiers).
- During `PerchFidget` the tail tip reaches the wall line (about 1 unit) for a few frames.

## Rebuild

```sh
cd level_generation/decorations/xeen_cagebird_claude
python3 scripts/bake_colour.py            # palette from cagebird.json (or: bake_colour.py budgie)
python3 scripts/tray_texture.py
python3 scripts/build_glbs.py
../../creatures/xeen_tiers_claude/bin/blender -b --factory-startup --python scripts/render_review.py -- \
  review/renders export/xeen_deco_cagebird_anim.glb export/xeen_deco_cagebird.glb
cd ../../..
for g in level_generation/decorations/xeen_cagebird_claude/export/*.glb; do
  python3 level_generation/decorations/mm8_3d/animated/scripts/check_winding.py $g; done
python3 tools/install_model.py level_generation/decorations/xeen_cagebird_claude/export/xeen_deco_cagebird.glb \
  --world xeen --name xeen_deco_cagebird.glb
python3 tools/install_model.py level_generation/decorations/xeen_cagebird_claude/export/xeen_deco_cagebird_anim.glb \
  --world xeen --name xeen_deco_cagebird_anim.glb
```
