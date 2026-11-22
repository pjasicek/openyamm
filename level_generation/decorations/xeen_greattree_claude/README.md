# Xeen great-tree crown (D2 Sprite Forest, D-23), lane S

Decision D-23 (devdocs/xeen/DECISIONS.md): one static crown for D2's great tree (`thing:great_tree`, A6's 16-sided
BModel trunk in `output/studio_cal/d2/tools/gen.py`, GREAT_*: root foot 448 high, trunk 2,600 high, radius 760 -> 547
(taper 0.72), flat top cap at 3,048 units). No Meshy, no Codex (0 credits). Built and installed 2026-11-20 as
`assets_source/worlds/xeen/models/xeen_deco_greatcrown.glb` (runtime copy cooked into `assets_dev/worlds/xeen/models/`).
The binding and decoration row are lane S's (`assets_dev/worlds/xeen/models/decorations.yml`), not written here.

## Rebuild

```bash
cd level_generation/decorations/xeen_greattree_claude
python3 scripts/make_shared.py        # leaf atlas + bark maps in shared/ (only when they must change)
./build.sh greatcrown                 # silhouette -> profile -> crown -> LOD2 clump cards -> impostor -> export ->
                                      # validate -> review sheets (about 2.5 minutes)
cd scripts && python3 overdraw.py greatcrown <tag> && python3 undergate.py greatcrown <tag>
python3 ../../mm8_3d/animated/scripts/check_winding.py ../work/greatcrown/xeen_deco_greatcrown.glb   # 0 inverted
# from the repository root:
python3 tools/install_model.py level_generation/decorations/xeen_greattree_claude/work/greatcrown/xeen_deco_greatcrown.glb \
    --world xeen --name xeen_deco_greatcrown.glb      # or ./build.sh greatcrown --install
```

`scripts/quick.sh greatcrown [views]` rebuilds only the crown blend and renders it (colour iteration, ~1 minute).
Every Blender call goes through lane S's serialising wrapper
(`level_generation/creatures/xeen_tiers_claude/bin/blender`, `common.BLENDER`); never `/snap/bin/blender`.

## Route (adapted from `../mm8_3d/trees_broadleaf/`, scripts copied, not edited)

- **Envelope**: no sprite. `make_envelope.py` draws `source/crown_silhouette.png` procedurally from
  `species/greatcrown.json` `envelope` (stub, lifted rim at 7.5 m and 20 m out, widest 26 m at 16 m, a superellipse
  dome, two sine tiers for layered shelves, a little noise); `prepare.py` traces it (101 rows) into the profile.
  `crown.lobes_az` makes the revolved envelope lopsided (3- and 5-fold lobes), `crown.gaps` opens nine windows in the
  outer crown where the limbs show.
- **Skeleton** (`build_tree.py`, replaces Sapling): a 16-sided stub, radius 6.6 m (539 units, as the trunk top's 547
  minus a hair), z = 0 to 5.2 m, open at the bottom (inside the trunk) and capped under the limbs; six heavy limbs
  (one leader, five spreading from 26-38 to 58-72 degrees off vertical, base radius 2.7-3.3 m) starting inside it,
  4-6 sub-limbs each and 3-5 branches per sub-limb, geometric taper, cut at 0.92 x the envelope. Branch and sub-limb
  ends anchor the outer clumps.
- **Bark**: one tube per limb, thickest first within the LOD budget (3,600 / 1,600 / 800), the trunk's own xdbark
  (`shared/bark_basecolor.png` is a byte copy of `assets_source/worlds/xeen/textures_x4/xdbark.png`) at the trunk's
  tile size (128 x 256 units = 1.57 m around x 3.13 m along; the stub wraps exactly 26 tiles), u per ring
  circumference with the one seam on the limb's top side, a normal map derived from xdbark's luminance. COLOR_0 =
  1 (trunk colour) x sky visibility (floor 0.5), faded to 1 below 3-9 m so the joint has no step.
- **Leaves**: own atlas `shared/leaves_basecolor.png` 2048 = 2 x 2 cells of 1024, each a cluster of 17-20 MM8 maple
  sprays (`source/mm8_leaves_*.png`, the MM8 batch's leaf atlas bytes, CC0 ambientCG) scaled so the leaves stay
  ~20-25 cm on a 2.6-3.2 m card, recoloured cool green with low jitter, deeper sprays darker. ~400 clumps of r 1.6-2.9 m
  (outer 375, inner 26: the envelope's shell holds no more at gap 0.8), 10,000 cards generated and the 4,500 most
  visible kept, 280 / 140 / 50 opaque shell cores (0.62 x clump). Colour: `leaves.target_srgb` [58, 190, 108] is
  the COLOR_0 tint parameter; it renders the crown's mean at sRGB [27, 82, 49] (front, sun + sky), the requested
  leaf look [34, 92, 58]; occlusion floor 0.38 (the crown is huge: most cards are deep inside), hue [1.15, 1, 0.95].
- **LODs** as the MM8 batch: LOD1 a per-clump subset 1.3x larger, LOD2 clump cards (two crossed verticals + a top
  card per group, 70 % of the triangle capacity), impostor quad. LOD2 tone is per channel [1.54, 2.16, 1.74] and the
  impostor tone [1.28, 1.91, 1.47] applies to leaf texels only (`finish_impostor.py`: bark keeps its colour).
- **Wind**: leaves and cores 0.3 model units at the top (~25 world units), bark 0.05; (z / H)^2 makes the stub's
  motion at the joint ~0.

## Results (2026-11-20)

| | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| Triangles | 14,832 | 7,480 | 2,528 | 2 (4 after the outline cut) |
| Overdraw mean / p95, front-3/4-side | 2.95 / 8.0 | 2.89 / 7.0 | 2.68 / 6.7 | 1.0 |
| Overdraw at the trunk's foot (mean / p95) | 1.71 / 5.0 | 1.73 / 5.0 | 1.48 / 4.0 | 1.0 |
| Overdraw on the green, 4,000 units | 2.22 | 2.28 | 2.20 | 1.0 |
| Eye mean sRGB / coverage vs LOD0 | 35/92/55, 1.0 | 35/90/55, 1.03 | 34/87/52, 0.94 | 31/86/51, 0.97 |

Under-crown gate (crown alone, engine-like light): near-black share (sRGB lum < 16) 0.2 % at the foot and on the
green, 0.4 % below the rim. `check_winding.py`: 0 inverted closed parts.

Model (metres, 81.7 units/m): bounds z 0 to 44.74 m, x -28.1 to 29.1, y -28.0 to 28.2. For the binding:
- `height: 3655` (44.74 m x 81.7; the engine scales by LOD0's bounds height, so 3655 keeps the bark tile and the stub
  radius exactly at the trunk's scale);
- placement raise / z offset: 3,048 - 200 = **2,848** (the stub's base 200 units inside the trunk);
- crown ~4,600-4,670 units across; stub radius at its base 539 units (16-gon vertex radius, vertices at 0, 22.5, ...
  degrees about the model's +x; it bulges to 6.73 m = 550 units at 3.1 m, above the trunk cap); the joint is cleanest if the
  placement's yaw lines its facets up with the trunk's (otherwise its corners may stand ~7 units proud of the
  trunk's flat faces over the last 200 units below the cap);
- suggested `lod_pixels: [260, 130, 60]` (one placement, seen across the map; LOD0 to ~14,000 units at 1080p),
  no `height_jitter`, no random yaw needed.

Review sheets (`review/greatcrown/`): `sheet.png` (envelope | front | three-quarter | side, LOD consistency),
`context.png` (with a trunk stand-in: green 4,000 / 6,000, the trunk's foot, below the rim, far 14,000 for every
LOD), `overdraw_v3.png`, `under_v3.png`, `occlusion.png`. Numbers: `work/greatcrown/validation.txt`,
`lc_stats.json`, `overdraw_v3.json`, `under_v3.json`.

## Compromises

- The envelope is revolved: lobes and gaps break the symmetry a little, but the crown is a rounded dome from every
  side; layered tiers read mainly in the silhouette.
- The crown's mean matches the requested sRGB [34, 92, 58]; under Eevee's sun it reads as a fairly saturated green.
  If it reads too bright in game, lower `leaves.target_srgb` (linear in the result) and rebuild.
- Leaf cards seen edge-on show as short streaks; the LOD2 top cards edge-on show thin bright lines (as in the MM8
  trees); fine at their switch size.
- The stub's bottom is open (hidden inside the trunk); the cap's apex is a 16-valence fan (hidden under the limbs).
- Source GLB ~12 MB (2048 leaf atlas and its normal map embedded); cooked runtime 1.7 MB plus textures.

## In game (lane S, session 4)

Scratch check on D2 (`work/ingame/`, git-ignored): a hard-link copy of `assets_dev` (`root/`, deleted in S session 14
as superseded scratch; the tour and shots remain) whose `worlds/xeen/
world.yml` adds the `decorations` table contribution (`path: models/decoration_data.txt`) and whose
`xeen_d2.scene.yml` turns A6's centre stand-in crown (entity 3509) into `xeen_greatcrown` (decoration_list_id 4000) at
z 3,840 (ground 992 + trunk top 3,048 - 200) and sinks the 15 other stand-ins. Tour `work/ingame/tour.yml`, shots
`work/ingame/shots/` (`sheet.png`: the green at 4,600, the arrival view from D1's road, the trunk foot, east): the
crown sits on the trunk without a visible step and rises well over the canopy from the arrival. The real placement is
A6's (gen.py `thing:great_crown`); the world.yml line is the orchestrator's.
