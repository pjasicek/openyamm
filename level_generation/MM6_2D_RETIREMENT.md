# 3D models replace 2D sprites

Since 2026-10-15 every MM6 monster and MM6 map decoration is drawn as a 3D model, and no 2D art is loaded or shipped
for them. Since 2026-10-16 no projectile or impact draws its native sprite either: solid projectiles are 3D models
(`engine/models/projectiles.yml`), the rest are effects (`engine/effects/projectiles.yml`). Items on the ground stay
sprites. These rules apply to any world.

## Which content is 3D

- **Actors.** Every mounted world's `worlds/<world>/models/actors.yml` contributes bindings by global monster
  descriptor (`game/maps/ActorModelManifest`), so a world can bind monsters for all worlds. An MM9 map that spawns
  the MM6 Bloodsucker or Guard shows the MM6 model. A world binds a descriptor once. The active world's binding
  replaces another world's. Two other worlds binding the same descriptor is an error. `[debug] actor_models` (now on
  by default, release included) turns this on; `actor_models_manifest` limits it to one file for diagnostics.
- **Decorations.** Since 2026-10-16 the bindings of every world are engine content: `engine/models/decorations.yml`
  (outdoor), `indoor_decorations.yml` (dungeons) and `decoration_overlays.yml`. A world can extend or override them
  with `worlds/<world>/models/` manifests of the same names (`game/maps/DecorationModelManifest`). A map loads only the
  models of the decorations it places, their lit/unlit counterparts and its events' `SetSprite` targets.

## What is not loaded

- **Map loader.** `MapAssetLoader` requests no sprite for a bound monster (placed actors, spawns, encounter tiers A–C,
  summons). It requests none for a model-bound decoration either, including the lit/unlit counterpart and an event's
  `SetSprite` target. The sprite frame table (YAML metadata) stays: `scale_reference` and attack contact frames read
  it. `ActorPreviewBillboardSet::modelDescriptors` lists the bound monsters a map shows when it loads.
- **Models.** `WorldFxSystem` builds those bindings with the map. Any other bound monster (a summon, an arena
  opponent) is built the first time it appears. Before this change every MM6 map load parsed all 88 actor GLBs
  (177 MB), whatever the map used.
- **Renderers.** The outdoor and indoor renderers never resolve a sprite for a bound monster, even on the frame
  before its model exists. Atlas preloads, keyboard targeting, health bars, quest markers and melee contact points
  use the model: its standing-pose top (`WorldFxSystem::actorModelStandingTop`) and its bounds.
- **Runtime cost.** No per-frame cost was added beyond one bit lookup per actor. Load time adds a single parse of the
  actor manifests, cached until the world or asset content changes.

## Removed assets

- **Monster atlases.** All MM6 monster atlas families: `assets_dev/engine/sprites_new/` and
  `assets_cooked/android/sprites_new/` (about 540 MB and 370 MB). Packaging treats absent profiles as having no
  families. `mm6_aie1` is kept, in both profiles, as the cooked fixture of the atlas pipeline tests
  (`tests/fixtures/sprite_atlas/`). The local authoring bank (restored x2 frames, ignored by git) moved from
  `assets_source/engine/sprites_new/` to the archive `assets_legacy/sprites_new_mm6_20261015/`. Without that folder,
  CMake defines no `openyamm_cook_sprite_atlases` target and `tools/cook_sprite_atlases.py` has no default source, so
  the atlases cannot be cooked back by accident. Move the folder back to cook an atlas again.
- **Decoration sprites.** The 136 restored decoration sprites in `assets_dev/engine/decorations_x2/` (21 MB) that only
  model-bound MM6 placements showed. Lighting bakes depend on `_legacy/sprites_original/`, which is kept.
- **MM7 and MM8 decoration sprites (2026-10-16).** Every drawn decoration of MM6–MM9 (map placements and event
  `SetSprite` targets) is model-bound. The restored sprites that only bound decorations showed are archived, not
  deleted, outside the runtime mounts:
  - `assets_legacy/decorations_x2_mm8_20261016/` (369 files, MM8 session);
  - `assets_legacy/decorations_x2_20261016/` (422 files, 34.9 MB, all worlds).
  `level_generation/decorations/scripts/retire_decoration_sprites.py` reports coverage and the candidates, and
  `--archive` moves them. Kept: sprites another engine table names (bag01, bucket, corpse, empty). Without its x2
  sprite, a decoration falls back to the native bitmap. `decorations_x2/manifest.json` keeps its entries as the
  approval record. `assets_source` holds no decoration sprite bank. Older copies remain only in local review and
  playtest stages under `output/` and `level_generation/projects/`.
- **Projectile and impact sprites (2026-10-16).** The restored sprites that only projectiles and their impacts used
  (spell display and impact objects, monster missiles, the water splash; 458 files, 20.8 MB) are archived in
  `assets_legacy/projectiles_x2_20261016/` (`level_generation/props/projectiles_claude/scripts/retire_sprites.py`).
  The map loader preloads only item sprites. Thrown items keep their item sprites; `spell70c` stays (another sprite
  shares it).
- **Corpse frame fix.** `sprite_frames/monsters/m498.yml`: the MM7/MM8 Fire Elemental B corpse frame (`m498x`) again
  uses its own `m496xa` bitmap. The MM6 demon atlas had claimed it because MM6's demon death group shares the name.

## Retiring another world's sprites

1. Bind every monster or decoration in its world's manifests.
2. Find the atlas families and decoration textures that only bound content uses. Map each monster descriptor's
   sprites to their `atlas:` packages, and each decoration placement or event `SetSprite` in every world's
   `scene.yml` and map Lua to its texture.
3. Keep any texture an unbound placement, object or spell still needs.
4. Delete the remaining files, then load the affected maps and check the log for `[SpriteAtlas]` errors.
