# MM9 Verhoffin Ruins props as 3D decorations (2026-10-30)

The props, torches, chests, quest objects and pentagram flames of MM9's Verhoffin Ruins, converted from their LithTech
ABC models into OpenYAMM 3D decorations for the native BLV ([map project](../../projects/mm9r_verhoffinruins/README.md)).
The route is the Chasm of the Dead props project's ([`../mm9_chasmofthedead_claude/`](../mm9_chasmofthedead_claude/README.md)):
`scripts/anskram.py` runs the Anskram Keep scripts on this project's table, `build.py` runs the Anskram build (with this
project's additions), `finish.py` the isle's. No paid services, no Meshy, no Codex: every model is MM9's own mesh with
its skin x4 (Lanczos, the shared `textures.py`).

## Outputs

- **20 models built here**, installed with `tools/install_model.py --world mm9` (`assets_source/worlds/mm9/models/mm9_deco_*.glb`),
  all through `check_winding.py` (finish.py):
  `minelantern` (37 placements), `sconce1` (2, flame cards on the head), `manacles`, `key1`, `skeletondebris03`,
  `capstone`, `greatbookfake`, `writ`; the tipped variants `chairdesk03p90`, `chairdesk03p270`, `tableround2p60`,
  `weaponscabinet02tip`, `scrollp268` (pitch/roll baked in: decorations turn about z only); `bedmedium2onside`
  (the beds' PropAnim.scr "onside": the ABC's `onside` animation pose baked in, a full export posed in Blender); the
  five `pentafire_<colour>` flames (below).
- **Reused** (same ABC, skin and scale; their rows, bindings and GLBs stay with their owner): `bench01`, `skeletondebris02`,
  `tableround2`, `tableround3`, `weaponscabinet02` (Drangheim Prison), `chairdesk03`, `flayingbench`, `pew3ns`,
  `pillory`, `skeletoncage`, `torturerack01`, `blackchest` (Lich Lab), `scroll`, `weaponscabinet01`, `chest1` (Anskram
  Keep), `table02` (Temple of Honk), `pillarstand` (Chasm of the Dead); `weaponscabinet01` at MM9's Scale 0.75 is a variant
  row `mm9_weaponscabinet01_x75`.
- Rows in the MM9 world's decoration contribution (`assets_dev/worlds/mm9/data_tables/decoration_data.txt`, sprites,
  `worlds/mm9/models/indoor_decorations.yml`), appended under `mm9r_common/locks/mm9_decorations.lock` in three runs:
  2216-2224, 2234-2238, 2269-2274 (other agents' rows in between).
- `../../projects/mm9r_verhoffinruins/props.json`: **85 placements** (77 props, 6 chests, 2 torches), each checked against
  the old map's baked BModel: median of medians 0.57 units, worst 1.3 (the writ), except the seven posed beds (32-50:
  the bake is the bind pose; they stand on the floor under their DAT position instead).
- `review/props_sheet.png`: contact sheet of the first 8 models; `review/<prop>/`: the review renders.

## The pentagram's flames

PentagramPuzzle.scr's five `Fire` objects (PentaFire1-5, FireScale 2) burn in five colours, and letter 485 ("RED skeletons
... YELLOW bellied ... feeling BLUE ... GREEN envy ... ORANGE metal") gives the puzzle's order by them. `scripts/
pentafire_textures.py` recolours the shared CC0 flame flipbook by luminance into each fire's `FireColor1` (red 255/0/0,
yellow 255/255/0, blue 43/88/244, green 31/224/65, orange 255/137/81) with a pale core; `build.py` makes each a
flame-only decoration (two cards, 0.55 m, the Anskram `gatefire` route with a per-prop texture). The map hides them until
the puzzle starts. Their MM9 lights (LightColor2, radius 40 LT) are not carried (no switchable runtime lights).

## Route (`scripts/`)

```sh
cd level_generation/props/mm9_verhoffinruins_claude
python3 scripts/props_table.py && python3 scripts/convert_all.py && python3 scripts/textures.py
python3 scripts/pentafire_textures.py
blender --background --factory-startup --python scripts/build.py
python3 scripts/finish.py --install          # (finish.py pentafire_red ... for the flame-only props: not in MODELS)
blender --background --factory-startup --python scripts/review.py -- && bash scripts/contact_sheet.sh
flock -x ../../projects/mm9r_common/locks/mm9_decorations.lock python3 scripts/tables.py --apply
python3 scripts/placements.py && python3 ../../projects/mm9r_common/review_root.py
```

`bedmedium2onside` is converted by hand in `full` mode (the rigid export drops the animation):
`convert_abc_model.py BEDMEDIUM2.abc work/raw/bedmedium2onside --id bedmedium2onside --export-mode full --texture 0=...`
and `work/raw/bedmedium2onside/mode.txt` says `full`; `build.py` poses it (props_table `POSES`).

## Notes

- `skeletondebris03` and `manacles` have no LODs: their decimated chains inverted a closed part / lost the plate.
- `flayingbench` (Lich Lab's GLB) faces half a turn from its ABC's bake: `placements.py` turns it (`YAW_FIX`; 21.9 units
  as placed, 0.74 turned). The Lich Lab places it unchecked.
- Reused rows keep their owner's collision and height even where this table's own guess differs (`tables.py` prints
  NOTE lines: `chest1` 35.8 high by Anskram's binding, `torturerack01` 63/144, `chairdesk03` and `skeletondebris02`
  without collision).
- The pews (`pew3ns`, PropAnim.scr "onside") stay upright: their ABC has no `onside` animation, so MM9 shows them upright too.
- The PropDamager spikes in the electrified pit are Anskram's `spikepit`, placed by the map project on the pit floor.
- `Transparent` (Pillory2, SkeletonCage1/2) and `Chromakey` (SkeletonCage1/2): the reused models carry their owner's alpha
  modes.


## Bone-display ball removed (2026-10-31)

Blender 5's glTF importer adds an `Icosphere` bone-display mesh (42 vertices, 80 triangles, 2.4 cm) to every skinned
(`full`) import, and the isle's `blib.import_raw` took every imported mesh, so the ball stayed in the decoration (Tasar
Academy found it). Removed from `bedmedium2onside` 156        -> 76 triangles (LOD0 / LOD1 / LOD2). Fixed in the Anskram
build this project runs (it sets the isle's `blib.SKIP_BONE_SHAPES`); rebuilt and reinstalled, geometry otherwise
identical (the ball was 0.72 m up inside the posed bed). Rebuilt, checked (`finish.py`, check_winding.py: 0 inverted
closed parts) and reinstalled with `install_model.py --world mm9`; the replaced GLBs and scripts are in
`work/backup_propfix_20261031/`. No MM9 bake depends on decoration models (stale_bakes.py lists none).
