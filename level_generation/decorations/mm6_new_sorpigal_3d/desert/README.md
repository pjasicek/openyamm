# MM6 desert palms — static 3D decorations (2026-10-09)

Procedural Blender (bmesh) models for seven MM6 desert/tropical decoration sprites, with procedurally painted
alpha-tested foliage atlases and bark maps. No external images, no paid generation. Not bound yet
(`decorations.yml` untouched, no bake).

```bash
./build.sh all --install          # textures + all seven (about 6 min); or ./build.sh <id> [--install]
python3 scripts/overview.py       # review/overview.png and review/overview_lods.png
```

| Sprite | Plant | Installed GLB (`assets_dev/worlds/mm6/models/`) | LOD triangles | File |
|---|---|---|---|---:|
| `6tree21` | fan palm (Washingtonia) | `mm6_deco_tree21.glb` | 4320 / 1188 / 226 / 4 | 3.5 MB |
| `cac19` | banana plant | `mm6_deco_cac19.glb` | 1194 / 445 / 135 / 4 | 2.1 MB |
| `cac18` | banana clump | `mm6_deco_cac18.glb` | 4974 / 1934 / 606 / 4 | 2.8 MB |
| `cac24` | dragon / Joshua tree | `mm6_deco_cac24.glb` | 1710 / 517 / 204 / 4 | 2.6 MB |
| `cac17` | yucca clump | `mm6_deco_cac17.glb` | 4840 / 1590 / 772 / 4 | 3.1 MB |
| `cac23` | tall yucca / cordyline clump | `mm6_deco_cac23.glb` | 2760 / 942 / 252 / 4 | 2.5 MB |
| `cac3` | agave / yucca rosette | `mm6_deco_cac3.glb` | 1380 / 450 / 210 / 4 | 2.0 MB |

LOD3 is a camera-facing impostor (one quad, cut to a 6-vertex outline = 4 triangles). Budgets and validation in
`scripts/desert_common.py` / `scripts/post_process.py`.

## Suggested bindings

Heights are the native sprite heights × DSFT scale (`info.json`); `yaw: random` (the default) for all.

| name | height | height_jitter | lod_pixels |
|---|---:|---:|---|
| 6tree21 | 360 | 0.12 | [650, 320, 180] |
| cac18 | 255 | 0.12 | [600, 300, 160] |
| cac23 | 282 | 0.12 | [600, 300, 160] |
| cac17 | 218 | 0.12 | [600, 300, 160] |
| cac24 | 196 | 0.12 | [500, 250, 140] |
| cac19 | 168 | 0.12 | [500, 250, 140] |
| cac3 | 154 | 0.15 | [500, 250, 140] |

No `z_offset` needed: every model stands on y = 0 (the agave's lowest leaves touch the ground, 2 cm under the
rosette's lowest point at LOD3).

## Contract

glTF Y-up metres, origin at the base centre on the ground, one node `Plant` with `openyamm_lods`
(`tools/link_static_model_lods.py`), alpha-tested cards cut to their texels (`tools/cut_foliage_cards.py`), COLOR_0
on every primitive. Materials:
- `Bark` (opaque, single-sided; absent on cac3), `Leaves` (MASK 0.5, double-sided, `openyamm_specular` 0.1,
  `openyamm_translucency` 0.3), `Impostor` (MASK, `openyamm_billboard`, `openyamm_specular` 0.1).
- `openyamm_wind` is the same on every material of a model, so leaves stay on their stems as the sway grows with
  height²: 0.05 (palm, cac19), 0.06 (cac18, cac23), 0.04 (cac17), 0.03 (cac24), 0.02 (cac3).
- COLOR_0 = per-part tint × sky visibility: rays over the hemisphere about (normal + up), attenuated through proxy
  spheres (crown, rosettes, dense cores) and blocked by the ground (`desert_lib.proxy_occlusion`). The tint grades
  the shared atlases per model (so cac18/cac19 share one banana atlas and cac17/23/24/3 one yucca atlas, and the
  engine shares the identical images).

## Construction (`scripts/build_plant.py`)

Each plant's layout is drawn once from a seed; every LOD is built from it with fewer/coarser parts (a seeded subset
of the leaves, enlarged to hold the coverage; enlarged cards above LOD0's top are squashed into it, since LOD0's
bounds scale the placement).
- **6tree21**: curved tube trunk (14 sides) with a boot-lattice bark (`palmboot`) and a darker fibrous foot; 25
  pleated fan leaves (21 rays × 4 rings, ridges/valleys alternate, outer part drooping) on tube petioles, spread on a
  Fibonacci spiral (young ones upright, old ones lower and yellower, cell `fanC`); a skirt of 12 hanging dead-leaf
  cards under the crown. LOD1 11 rays, LOD2 7-ray fans on flat petiole cards.
- **cac19 / cac18**: pseudostems (tubes, `bananastem`) topped by spiral leaves; each leaf is a 5-across strip
  (midrib raised, edges curled) along a gravity-bent spine, the texture spanning the leaf width with transparent
  tear slits along the lateral veins and strip-wise light changes; petioles are 3-sided tubes; dead leaves hang down
  the stems. cac18: eight stems leaning out of a 0.4 m clump, leaves biased away from the clump centre, three green
  banana bunches on drooping stalks. LOD2: flat 2-across strips.
- **cac24**: Catmull-Rom trunk and branches traced from the sprite (fork, two/three tips) with the `dragonbark`
  map; four rosettes of 64 spiky spray cards (two-segment, drooping toward the bottom) plus a few dry cards.
- **cac17**: 36 rosettes (seven on the ground round the base, the rest rejection-sampled inside the sprite's
  silhouette) on thin curved stems from five root points; upper rosettes carry long hanging orange-brown dead
  leaves.
- **cac23**: six slim straight stems (`yuccastem`, leaf-scar rings) with large rosettes of long thin drooping
  strand cards (three segments) and a few dead leaves.
- **cac3**: 230 real-geometry sword leaves (channelled, 3 across, pointed tip), radiating from 0.62 m over a
  flattened sphere band and cut short at the ground. LOD1 150 flat leaves, LOD2 70 leaves of 3 triangles.

## Impostors

`bake_impostor.py` renders LOD0 from the front (Cycles, orthographic, frame = 2 × the largest horizontal reach ×
the height, emission of texel × COLOR_0, camera-space shading normal with z turned toward the camera, 128
transparent bounces — the default 8 left black texels inside the dense rosettes), `finish_impostor.py`
box-filters to 512 px, cuts at alpha 0.75 and dilates colour/normal. `calibrate_impostor.py` folds the linear mean
ratio LOD0/LOD3 (front, Eevee, no shadows) into `scripts/impostor_tone.json`; `build.sh` re-finishes once when it
moved by more than 3 %. Rebuilds are byte-identical once the tone has settled.

## Review

`review/<id>/compare.png` (sprite | LOD0 front | three-quarter | back, Eevee, specular scaled by
`openyamm_specular` as in the engine) and `review/<id>/lods.png` (all levels from the front with triangles, mean
colour and coverage vs the previous level); `review/overview.png`, `review/overview_lods.png`.
Neighbouring levels (Eevee, front, no shadows): mean colour within 3.2/255 in every channel; coverage within 10 %
(largest: cac18 LOD2 −9 % and its impostor +10 %, cac3 LOD1 −9 %); every impostor within 9 % of LOD0's coverage.

## Sources and licences

All textures are generated by `scripts/make_textures.py` (numpy strokes at 2× resolution, box-filtered; normal maps
from painted heights; seeded): fan leaves, dead skirt, banana leaves with tears, banana bunch, yucca spike sprays,
dry hanging leaves, strand sprays, sword-leaf strips, and the four tileable barks. Original work for this project; no
third-party images, no attribution needed. Blender is the tool; its output is ours.

## Compromises

- The palm crown is denser and a little darker than the sprite, whose painted fans have strong light/dark contrast;
  fan segments are painted, so a fan seen edge-on reads as a thin spiky blade.
- Banana leaves are smoother and less shredded than the sprite's; cac18's bunches are mostly hidden in the clump.
- cac17's dead leaves hang as distinct brown skirts under each upper rosette where the sprite shows streaks between
  rosettes; its stems fan from a few root points (the sprite shows two thick curved trunks).
- cac24's trunk is smoother than the sprite's gnarled bark; the crown sits left of the trunk base as in the sprite,
  so the model's origin (trunk base) is not under the crown's centre.
- Colours were matched in Eevee review lighting: LOD0 front mean vs sprite mean within 8/255 per channel, except
  cac18 (12/255 darker in red) and cac3 (7/255 brighter); check under engine lighting once bound.
- Each GLB embeds its copy of the shared atlas and bark (~2–3.5 MB per file).
