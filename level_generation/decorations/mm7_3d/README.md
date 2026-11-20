# MM7 decorations in 3D

Every visible MM7 map decoration drawn as a 3D model, as MM6's are. Started 2026-10-15.
- **Inventory:** 121 visible decorations with 7,899 placements, 4,590 of them in the 13 outdoor maps and 3,309 in
  the dungeons. `inventory.json`, from `scripts/inventory.py`.
- **Builder brief:** `BRIEF.md`.
- **Engine:** no new engine work. The MM6 work (indoor models, wall mounts, swing, pulse, flipbooks) is
  world-agnostic.

## Where models live

Decoration models of every world are engine content, so any world can bind them. Since 2026-10-15, the MM6
decoration GLBs are in `assets_source/engine/models/` as well, so MM7 can bind them.
- **Install:** `tools/install_model.py <glb> --engine`.
- **Names:**
  - `mm7_deco_*` for MM7 art, including art that MM8 shares (beacon fires, pedestals, cauldron, trash heap, glass,
    fruit bowl).
  - `mm8_deco_*` for MM8-only art. The MM8 decorations are a separate session's work.
- **Bindings:** engine content since 2026-10-16, shared by every world: `assets_dev/engine/models/decorations.yml`
  (outdoor), `indoor_decorations.yml` (dungeons) and `decoration_overlays.yml` (the stat barrel liquids).

## Reused models

| MM7 decoration | Placements | Model |
|---|---|---|
| `torch01` | 1,888 | `mm6_deco_torch01` (the same sprite) |
| `torch07`, `torch05`, `torch06` | 656, 246, 158 | `torch01` with red, purple and green flames (`mm7_deco_torch01_<colour>`, flames from `../shared_flames/`) |
| `7dec02` campfire | 17 | `mm6_deco_campfire` (the art of MM6 `dec25`) |
| `bush14`, `bush15` | 85, 25 | `mm6_deco_cac24`, `mm6_deco_cac7` (the same art) |

## Event sprite switches

All of these targets must be bound, and each family or pair keeps the same height and jitter:
- **Seasonal families** (Harmondale, Erathia, Tularean Forest, Barrow Downs, Avlee) switch sprites through the
  seasons: `7tree13`/`14`/`15`, `7tree16`/`17`/`18`, `7tree19`/`20`/`21`, `7tree07`/`08`/`09`,
  `7tree25`/`tree26`/`tree27`, `7tree22`/`24` and `7tree28`/`7tree30`.
- **Fruit trees:** `tree38` becomes `tree37` when picked and `7tree30` in winter.
- **Hidden:** some decorations are hidden (`"0"`) by events in dungeons.

## Batches

| Batch folder | Decorations | Builder |
|---|---|---|
| `torches/` | torch07/05/06 flame variants (and their `_free` models) | orchestrator |
| `rocks/` | 7rock01, 02, 03, 04, 05, 07, 08, 09 | builder |
| `trees_a/` | tree36, tree33, tree60 (conifers), 7tree04, tree65, 7tree63, 7tree01, 7tree10 | builder |
| `trees_seasonal/` | the seasonal families above, and tree38/tree37 | builder |
| `trees_b/` | tree41, tree42 (bare), tree23, tree66, tree69, 7tree29, 7tree05, 7tree06 | builder |
| `flowers/` | flower01–13, flower16 | builder |
| `plants/` | bush03 fern, bush02, plant01a/01b/02a/03b/04b/07b/11a, cacti bush10, 11, 12, 13, 16 | builder |
| `fire/` | beacon fires dec60–63, pedestals dec64–75, 7dec33 buoy, torch02 lantern, dec24x burned-out fire | builder |
| `dressing/` | 7dec32 cobweb barrel, dec19, 7dec18, 7dec10, 7dec11, 7dec16, cages 7dec05/06/07, 7dec46, statues 7dec54/55 and dec94/95/96, dec97, 7dec20, 7dec21 | builder |
| (MM8 session) | 7dec03 cauldron, 7dec01 trash heap, 7dec48 glass, 7dec08 fruit bowl | MM8 session |

The `fire01` large fire has no sprite (its fire comes from particles), so it is not modelled.

## Status

**2026-10-16: every visible MM7 decoration is bound** (102 outdoor and 31 dungeon bindings), including `v77dec24`, the
lit signal fire that events 237–239 of 7out02 switch dec24x to (dec24x's logs plus a flame, bound so the logs keep
their size). Nothing is committed.
- **Seen in game:**
  - all 13 outdoor maps (`output/mm7_deco_outdoor_20261016/`);
  - the dungeons 7d27 (cages), 7d29 (heaps, rocks, bones), d03 and 7d17 (lanterns, net barrels), 7d22 (trees) and t02
    (goblets) (`output/mm7_deco_dungeons_20261016/`);
  - the torches (`output/mm7_deco_torches_20261015/`).
- **Revisions applied after review:** 7dec18 bone pile, skull stains, 7dec32 net; statue helm, horns and plinth;
  tree38's apples; inside-out parts of the cages, dec19 and tree38 (`check_winding.py` now runs before every install).
- **Shared art:** the cauldron, trash heap, glass and fruit bowl come from the MM8 session (`../mm8_3d/props/`); MM8
  binds the beacon fires and pedestals.
- **Regression:** `openyamm --headless-run-regression-suite decorations` includes `mm7_decoration_models_outdoor_maps`.
  It checks:
  - every drawn decoration of the 13 outdoor maps is a model with LODs within 7000 triangles;
  - every model stands on its ground point;
  - the seasonal, fruit-tree and signal fire switches keep the placement.
- **Lighting bakes:** none is stale (`tools/lighting/stale_bakes.py`). The installed outdoor bakes were made without
  `--decoration-shadows`, so they do not depend on decoration models.
- **Bindings are engine content** (2026-10-16): `engine/models/decorations.yml`, `indoor_decorations.yml` and
  `decoration_overlays.yml` (MM6–MM8 merged; worlds may extend them). 7dec32 is open-topped with seven stat liquids.
- **Sprite retirement** (`../../MM6_2D_RETIREMENT.md`): every drawn MM6–MM9 decoration is bound; the restored sprites
  that only bound decorations showed are archived in `assets_legacy/decorations_x2_20261016/`
  (`../scripts/retire_decoration_sprites.py`).
- **Known MM6 defects** (found by `check_winding.py`, not changed): inside-out parts in `mm6_deco_bonecage`, `brazier`,
  `brazier_unlit`, `cauldron`, `hngncge2`, `hngncge2_long` and `tree06a` (far apples).
- **Android:** the overlay is stale for the moved and new models; cook it only when the user asks
  (`tools/cook_android.sh`).
- **Quality and reduction pass** (2026-10-16, done; Meshy and Codex allowed): statues 7dec54, 7dec55 and dec95 rebuilt
  from Codex HD references with Meshy (45 credits; dec94's reference was refused by the image tool, so it kept the
  procedural model with fixes), 7rock08 rebuilt with Meshy (30 credits), all rocks 1200 → 900 triangles, winter trees
  narrower and gnarlier, 15–26 % fewer LOD0 triangles on the most-placed trees (leaf cards most hidden in the crown,
  pilot bark reduction), snow white in shade, tree41/42 -45 %/-29 %, a bark UV fix in the copied MM6 tree scripts
  (the MM6 New Sorpigal trees still have the bug), plants -14 % weighted, lily pads, foxglove, fuller fires with
  additive glow and flicker, metal goblet, vase and eagle, an open 7dec32 with stat liquids. In-game captures:
  `output/mm7_deco_quality_20261016/`. The shared cauldron, trash heap, glass and fruit bowl belong to the MM8
  session's props batch.