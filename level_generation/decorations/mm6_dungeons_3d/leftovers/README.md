# MM6 dungeon leftovers in 3D (2026-10-09)

Static models for the MM6 dungeon decorations that had no model yet (brief: `../BRIEF.md`): twelve corpses, the
p336 rocks and `6rock02`, four trees and two flowers. All live in this folder; outdoor pipelines are copied, never
edited (`../../mm6_new_sorpigal_3d/` read only), and every model is installed through `scripts/finish.py`, which
refuses to overwrite a GLB it did not install itself (`work/installed.json`, `--replace-own`).

## Shared scripts

- `scripts/leftovers_lib.py`: the outdoor props library (through `../scripts/dungeon_lib.py`) with its writable roots
  redirected here; `material()` looks in `textures/` here, then the dungeon project's, then the outdoor props'.
- `scripts/finish.py`: material modes, LOD link (`tools/link_static_model_lods.py`), validation (one mesh node, 3-4
  LODs, budgets, COLOR_0 everywhere, base on the ground), install (0664, new names only). Its table merges
  `scripts/finish_<group>.py` (`corpses`, `corpses_b`, `rocks`, `plants`).
- `scripts/review.py` + `scripts/sheet.py`: `review/<name>/compare.png` (native sprite | LOD0 front, three-quarter,
  side over every LOD) and the lit means.
- `scripts/albedo.py`: flat albedo of LOD0 from the front (base colour x COLOR_0, no light), overall and per
  material; `scripts/suggest_tints.py` turns it into COLOR_0 multipliers (linear(native) / linear(albedo)). Every
  model's front albedo was brought to the native sprite's mean, as the brief asks (the dark painted sprites are
  not brightened; review renders under the sky light look lighter than the sprites for that reason).
- `scripts/corpse_common.py`, `corpse_pose.py`, `corpse_texture.py`: copies of the outdoor impaled-corpse pipeline
  (posed MM6 peasants, baked and welded, recoloured and bloodied atlas copies); `hang_props.py`: ropes,
  hangman's-knot coils, chains of alternating links (a tube from LOD1 or LOD2) and J hooks; `make_textures.py`:
  the procedural laid-rope texture.

## Hanged and hooked corpses (`build_hanged.sh`, `scripts/build_hanged.py`)

| Model (`assets_dev/worlds/mm6/models/`) | Sprite | LOD triangles | Binding height | File |
|---|---|---|---|---|
| `mm6_deco_corpse.glb` | `corpse` hanged man, khaki shorts | 5159 / 2210 / 906 / 270 | 205 | 5.5 MB |
| `mm6_deco_corpse07.glb` | `corpse07` hanged woman, ragged dress | 5159 / 2210 / 907 / 272 | 204 | 5.7 MB |
| `mm6_deco_corpse08.glb` | `corpse08` hanged upper body, cut at the waist | 5400 / 2339 / 979 / 272 | 178 | 5.6 MB |
| `mm6_deco_corpse11.glb` | `corpse11` woman hung by the wrists from a hook | 5512 / 2394 / 775 / 274 | 222 | 5.5 MB |
| `mm6_deco_corpse14.glb` | `corpse14` butcher's rack: six chains and hooks | 5808 / 1990 / 1035 / 231 | 203 | 5.6 MB |
| `mm6_deco_corpse15.glb` | `corpse15` hanged man, grey coat, red cap | 5159 / 2210 / 907 / 270 | 177 | 5.6 MB |
| `mm6_deco_corpse18.glb` | `corpse18` headless, armless torso on a hook | 3037 / 2273 / 776 / 273 | 203 | 5.6 MB |

- A corpse is one or more pieces, each a separately posed import of `mm6_pman.glb` / `mm6_pfem.glb` (read only)
  with world-space bone operations (plus `converge`, which draws the pfem skirt in round the legs). Pieces are cut
  with planes through posed bones (`cuts`: only the listed bones' faces are cut; a flesh fan cap closes each cut),
  then joined; the corpse is lifted so its lowest point is on the ground and the rope or chain top is placed at
  `top_fraction` of the sprite (the body's share of the sprite height, measured from the sprite rows), so the
  proportions match the sprite at the binding height. Pieces of one corpse use different bones, so their texels
  never overlap in the shared atlas copy.
- Texture: `corpse_texture.recolour` plus classes added here: smooth skin over the tunic (`tier_skin`), the tunic
  hem below the belt, torn shirt rags, trousers by leg bone and rest height (shorts below a knee height), the
  whole scalp (`hair_all`: black hair, blonde, or corpse15's red cap), green cloth (the pfem bodice), the pfem
  skirt as legs with a loincloth band (corpse11), and exposed ribs (corpse14's torso). Blood from listed bone
  wounds. Normal and metal/roughness atlases are the peasants' copies.
- Props: noose loop, back rope, hangman's knot coil (6 turns and thick on corpse08), rope to the top (`rope`
  texture); chains (`steel`, tinted the sprites' blue steel) and hooks whose bend catches a captured body point
  (wrists, neck stump, knee, waist, arm, torso) or a fixed point (corpse14's empty hooks). corpse14's chains are
  links at LOD0 only and its LOD3 drops the hooks.
- COLOR_0 = vertex occlusion x per-material tint (`tints` in each spec, from `suggest_tints.py`): front albedo
  within about 5 % of the native mean (corpse 85/75/72 vs 85/76/73, corpse07 114/100/101 vs 114/93/88, corpse14
  108/104/113 vs 107/96/98, corpse18 122/100/107 vs 125/102/106).
- Rebuild: `./build_hanged.sh [--install [--replace-own]] [corpse...]`; pose check: `blender --background --python
  scripts/build_hanged.py -- <corpse> --preview` (`review/<corpse>/pose_*.png`). Overview:
  `review/hanged_compare.png`.
- Compromises: the peasants' short hair stands in for the sprites' long hair (corpse, corpse07, corpse11); the
  pman tunic and trousers keep their shapes under the recolours (corpse's bare chest still has the tunic's
  outline, corpse15's coat is the tunic length); corpse11's legs are the drawn-in skirt tube recoloured as skin
  (the pfem has no thighs under the skirt); corpse08's head is a blond mass laid on the shoulder; corpse14's
  pieces are traced loosely (the ribs are painted stripes, the shred on the last hook is left out); blood is
  painted blotches and runs, not the sprites' drips standing off the body.

## Severed heads, rack and pole corpses (`scripts/build_corpses_b.py`)

| Model (`assets_dev/worlds/mm6/models/`) | Sprite | LOD triangles | Binding height | File |
|---|---|---|---|---|
| `mm6_deco_corpse01.glb` | `corpse01` head in a basket | 3293 / 1887 / 738 / 272 | 47 | 4.2 MB |
| `mm6_deco_corpse02.glb` | `corpse02` hung by the ankles under a rack | 5742 / 2742 / 1171 / 279 | 128 | 5.8 MB |
| `mm6_deco_corpse03.glb` | `corpse03` three bodies on a pole | 5729 / 2421 / 879 / 292 | 165 | 5.9 MB |
| `mm6_deco_corpse09.glb` | `corpse09` bearded head on a stake | 2746 / 1352 / 550 / 221 | 102 | 4.0 MB |
| `mm6_deco_corpse10.glb` | `corpse10` woman's head on a spike | 4352 / 2340 / 909 / 275 | 127 | 4.0 MB |

- Posed MM6 peasants (`mm6_pman.glb`, `mm6_pfem.glb`, `mm6_pmn2.glb`; read only) with the corpse_pose.py
  operations plus a two-bone reach toward a world point (wrists and ankles onto corpse02's crossbar), baked and
  welded. Heads keep the neck and head bones, cut square across the neck with a flesh cap and a ragged fringe;
  their texture is the 1K head half of the peasant atlas, recoloured by texel class (eyes and teeth kept).
  corpse09: pmn2 bearded head on a pointed stake. corpse10: pfem face (braid dropped) on a spike through the crown,
  a long alpha-tested hair sheet (MASK, double-sided) and a hanging eyeball. corpse01: pmn2 head with greyed hair
  on its side in a lathe-built plaited basket (`corpse01_wicker`). corpse02: bare bloodied torso, wooden rack
  with rope lashings. corpse03: neutral trousers tinted per body in COLOR_0 (blue, red, green).
- Colour: one whole-model albedo multiplier per corpse; the darkening part goes into COLOR_0, the brightening part
  (COLOR_0 clamps at 1) into the model's own recoloured atlas. Front albedo vs native: corpse01 93/62/45 vs
  94/62/44, corpse02 79/40/28 vs 78/40/28, corpse03 77/48/42 vs 77/48/42, corpse09 75/48/37 vs 76/48/38, corpse10
  72/44/37 vs 73/45/38.
- Build: `blender --background --python scripts/build_corpses_b.py -- <corpse>` (`--preview`: pose only); review
  `scripts/review_b.sh <corpse> <yaw> [elevation]`; install `python3 scripts/finish.py <corpse> --install`
  (table `scripts/finish_corpses_b.py`). Textures: `corpse0*_*`, `corpse10_hair`, `corpse10_eye`, `corpse01_wicker`.
- Compromises: the peasant bodies are slimmer than the painted ones, and corpse03's stack is narrower and more
  spaced; corpse03's shared atlas shows every body's wounds on all three and one hair colour; corpse10's hair is a
  single sheet that reads flat from the side, and the pfem circlet peeks out at the hairline in LOD1-LOD3;
  corpse09's beard hides most of the torn neck; corpse01's hair is the long pmn2 hair cut level and greyed.

## Rocks (`build_rocks.sh`, `scripts/build_rock.py`, `scripts/rocks.json`)

The p336 sprites `rock01`-`rock11` are MM8-origin bitmaps in the merged set (different from the `6rockNN` /
`rokN` rocks already modelled as `mm6_deco_rock01`...`rock14`); `6rock02` is `rok2`.

| Sprite | GLB | Scans | LOD triangles | Binding height |
|---|---|---|---|---|
| `rock01` (mossy cracked block, three pebbles) | `mm6_deco_boulder01.glb` | `namaqualand_boulder_06` + 3 x `namaqualand_boulders_01` | 2398 / 956 / 288 / 96 | 71 |
| `rock04` | reuses `mm6_deco_boulder01.glb`: the same sprite as rock01 (mean within 4/255) | - | - | 69 |
| `rock02` (long low rock, three pebbles) | `mm6_deco_boulder02.glb` | `namaqualand_boulder_05` + 3 x `namaqualand_boulders_01` | 2400 / 956 / 288 / 96 | 39 |
| `rock03` (mossy wedge) | `mm6_deco_boulder03.glb` | `namaqualand_boulder_05`, wedge ramp | 2400 / 960 / 290 / 96 | 104 |
| `rock10` (grey-tan wedge) | `mm6_deco_boulder10.glb` | rock03's geometry, own grade | 2400 / 960 / 290 / 96 | 102 |
| `rock11` (low wedge) | `mm6_deco_boulder11.glb` | `namaqualand_boulder_05`, wedge ramp | 2400 / 960 / 290 / 96 | 53 |
| `rock06` (five small stones) | `mm6_deco_boulder06.glb` | `namaqualand_boulder_06` x2, `_03` x2, `_04` | 1494 / 594 / 238 / 94 | 16 |
| `6rock02` (big sandy boulder) | `mm6_deco_rock02.glb` | `namaqualand_boulder_06` | 2400 / 960 / 290 / 96 | 115 |

- Heights are the sprites' measured opaque heights: the p336 sprites sit at the bottom of a 128-unit canvas, so
  logical height x scale would be the empty canvas; `6rock02` is 114.5 units opaque on its 116 canvas.
- Builder: parts (scan, yaw, scale, size relative to the main rock, position, sink, optional wedge ramp and
  mirroring) assembled, scaled and centred; each part decimated with its own dome unwrap (smart-project
  fallback), one shared 1024 atlas, small pebbles drop at LOD2/LOD3, buried vertices flattened onto the ground.
  Maps baked from the full scans in Cycles; AO folds into the base colour, then a grade (saturation, gain,
  optional contrast) and procedural moss (rock01/02/03) bring it to the sprite's flat albedo (`scripts/albedo.py`,
  within 1/255 per channel for every rock). COLOR_0 is contact occlusion against the parts and the ground.
- Sources (Poly Haven, CC0): namaqualand_boulder_03/04 (Jenelle van Heerden; _03 photography Dario Barresi),
  namaqualand_boulder_05 (modelling Jenelle van Heerden, photography Dario Barresi), namaqualand_boulder_06 and
  namaqualand_boulders_01 (modelling Jenelle van Heerden, photography Greg Zaal), read from
  `../../mm6_new_sorpigal_3d/rocks/source` and `../rock/source`. `scripts/rock_survey.py` renders every scan from
  eight yaws (`work/rocks/survey/`).
- Rebuild: `./build_rocks.sh [--install [--replace-own]] [rock...]`.
- Compromises: the pebbles are separate small scans resting at the base, not cracked-off parts; rock03/rock10 are
  one scan squeezed into a wedge (no pits on the stretched top) and read narrow from the side; the scans lack the
  sprites' painted light and shadow; rock06's stones are blockier than the sprite's; 6rock02 keeps some ruddy
  granite under the tan grade.

## Trees and flowers (`scripts/build_plants.sh`)

Bark UV fix (2026-10-16): `scripts/trees/build_tree.py` had the outdoor pipeline's swapped bark UV axes (furrows
running around the trunk). It is fixed for rebuilds. The four installed trees were fixed in place by
`../../mm6_new_sorpigal_3d/trees/scripts/fix_bark_uv.py`; see that folder's README, "Bark UV fix".


| Model | Sprite | LOD triangles | Binding height | File |
|---|---|---|---|---|
| `mm6_deco_tree09.glb` | `6tree09` weeping willow | 5958 / 2380 / 884 / 4 | 512 | 9.9 MB |
| `mm6_deco_tree22.glb` | `6tree22` broadleaf | 5960 / 2380 / 800 / 4 | 211 | 10.0 MB |
| `mm6_deco_tree26.glb` | `6tree26` flat-topped tree | 5961 / 2380 / 716 / 4 | 128 | 10.1 MB |
| `mm6_deco_tree30.glb` | `6tree30` conifer bush | 3962 / 1574 / 584 / 2 | 60 | 9.4 MB |
| `mm6_deco_flower01.glb` | `6flower01` sword-leaf plant, orange bract spike | 374 / 168 / 52 | 33 | 0.24 MB |
| `mm6_deco_flower11.glb` | `6flower11` small pale rose bush | 498 / 276 / 174 | 35 | 0.65 MB |

- `scripts/build_plants.sh <id> [--install]` runs a copy of the outdoor tree pipeline (`scripts/trees/`, species in
  `scripts/species/<id>.json`) or flower pipeline (`scripts/flowers/`), writes `work/plants/<id>/`, renders the
  review sheet and calls `finish.py` (table `scripts/finish_plants.py`).
- Trees: Sapling skeleton, leaf-spray clumps on alpha-cut cards (MASK 0.5, double-sided, `openyamm_wind` 0.12,
  `openyamm_translucency` 0.35, `openyamm_specular` 0.1), sky-ray occlusion in COLOR_0, LOD2 clump cards and a
  camera-facing impostor (`openyamm_billboard`) as LOD3; bark opaque, wind 0.03. Copied-script changes: willow
  wands on hanging strand cards (`crown.moss.kind: willow`, `bottom`, `down`, `keep` per LOD), clump offsets scaled
  for trees under 2.5 m, root tips clamped 2.5 cm below ground, Sapling `scaleV` 0, no install from post-process.
  6tree09: 80 clumps plus 1000 strand cards (45 % at LOD1, 15 % at LOD2). 6tree22: trunk forking at 45 %, crown
  from 35 %. 6tree26: twisted trunk splitting once, flattened clumps from 46 %. 6tree30: needle sprays in a cone.
- Flowers: procedural 512 atlas, one MASK material `Plant` (wind 0.02, translucency 0.3, specular 0.1). 6flower11
  reuses the rose bush scaled to 0.27 with denser cards and 16 pale roses; 6flower01: 13 folded-ribbon sword
  leaves and a bract spike of crossed cards.
- Colour: flat albedo equals the native mean within 1/255. Trees: `scripts/plant_tint.py` multiplies COLOR_0 on
  every LOD (impostor included) by a linear `albedo_tint` (6tree09 [0.543, 0.517, 0.757], 6tree22 [0.608, 0.561,
  0.859], 6tree26 [0.413, 0.544, 0.741], 6tree30 [0.401, 0.619, 0.43]) -> `work/plants/<id>/tree_tinted.glb`.
  Flowers: a per-channel gain on the painted atlas (6flower01 (0.57, 0.86, 1.53), 6flower11 (1.37, 1.16, 1.43)),
  since their COLOR_0 sits near 1.
- Sources: ambientCG LeafSet022 (CC0) and Poly Haven bark_brown_01 (CC0) from the outdoor trees' `source/`; Sapling
  Tree Gen (GPL) is a tool, its output is ours; flower atlases, willow wands and needles are procedural.
- Compromises: the willow crown top is flatter than the sprite's dome and its curtain ends a little low; 6tree22's
  dense crown hides the limbs; 6tree26 has a few more limbs and its impostor covers 15 % less than LOD0; 6tree30
  lacks the sprite's yellow highlights and dark gaps; 6flower11's roses are flat discs, less defined than the
  sprite's; 6flower01's spike is taller and the leaves more upright. Neighbouring LODs differ by up to about 8/255.
