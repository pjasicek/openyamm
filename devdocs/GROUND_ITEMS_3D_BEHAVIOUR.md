# Items on the ground in 3D: physical behaviour and interaction

Status (2026-10-18): **implemented except the steps that wait for the item generators** (section 7); unit-tested,
not yet checked in game. It covers how 3D world items ([plan and models](GROUND_ITEMS_3D_PLAN.md)) fall, bounce,
collide, settle, take the cursor and are inspected. MM9 is out of scope. Section 1 records the state before the change.

**Decision (user, 2026-10-18): no item on the ground draws a billboard.** Every MM6-MM8 ground item draws its 3D
model. The ground-item sprite path and the `item_models` switch are removed, not kept as a fallback. An item without a
working model draws a deliberately loud placeholder (section 2): a missing model is a bug to report and fix, never a
quiet return to the sprite.

## 1. Starting point (verified before the change)

Switching an item to 3D changed only its presentation. The simulation underneath was the billboard one.

- **Coverage is complete for MM6-MM8.** All 911 distinct icons of the 1894 real items in
  `assets_dev/engine/data_tables/items.txt` are bound in `assets_dev/engine/world_items/items.yml`. MM9's own items
  (`worlds/mm9/data_tables/items.txt`) have no bindings; while MM9 is out of scope, an MM9 item on the ground shows
  the placeholder.
- **The bindings belong to the renderer.** Only `WorldFxSystem::loadItemModels` reads `items.yml`, and only with
  `[rendering] item_models=true` (default false). A missing `items.yml` binds nothing without an error
  (`ItemModelBindings.h`). The world runtimes, which run the physics and also run headless, cannot see the bindings.
- **Packaging excludes the models.** `tools/package_runtime_assets.py` and `tools/cook_models.py` skip
  `engine/world_items` (development WIP). The runtime copies are 136 MB, against the plan's 30-50 MB estimate.
- **Dimensions are generic.** The items use their ground object's `Radius`/`Height` from `object_list.txt`: 1294
  items are 64 x 64, 598 are 64 x 16, and three others. The bound models span 14 to 393 units of `length` (median 67):
  longsword 135, `item010` sword 176, `item166` 27, smallest gem 14. Every item object except one has the `Bounce`
  flag.
- **Indoors, collision is a moving point.** `IndoorWorldRuntime::updateWorldItemsStep`
  (`game/indoor/IndoorWorldRuntime.cpp:8022`) tests the origin's segment against faces with
  `findProjectileIndoorFaceHit` (`:2417`); radius and height only widen the candidate face search. On a wall hit the
  origin is placed on the wall plane, so half of a long model sits inside the wall. Positions are integers rounded
  after every 1/128 s step, so horizontal motion below about 64 units/s is lost.
- **Outdoors there is no wall sweep.** `OutdoorWorldRuntime::updateWorldItems`
  (`game/outdoor/OutdoorWorldRuntime.cpp:6187`) integrates position once per frame, without sub-steps, expires items
  over water and clamps to the rendered terrain or the highest walkable BModel face under the origin. Items thrown at
  a building pass through it.
- **The resting pose is also the airborne pose.** `WorldFxSystem::syncItemModels`
  (`game/fx/WorldFxSystem.cpp:2787`) draws the baked resting pose with a fixed yaw hashed from the item key, so a
  falling sword is lying flat in mid-air and never turns.
- **The renderer snaps to the ground while bouncing.** The outdoor ground sampler
  (`game/outdoor/OutdoorGameView.cpp:2702`) applies whenever the simulated z is within 16 units of the native terrain,
  regardless of velocity, so the last part of each bounce is drawn glued to the ground. Indoors there is no sampler:
  models sit at the simulated z and do not tilt on ramps.
- **Ground fitting ignores size.** The slope comes from height samples 24 units around the origin. A 176-unit sword
  on a slope or a step edge is tilted to the slope under its centre; its ends can sink in or float.
- **Picking uses the sprite volume, the outline uses the model.** Outdoors the pick box is
  `max(20, radius)` x `max(40, height)` around the origin (`OutdoorInteractionController.cpp:4184`): 128 x 128 x 64
  for nearly every item. A 14-unit gem owns a box nine times its size and can shadow neighbours; the ends of a long
  staff beyond 64 units cannot be clicked. Indoors the pick is the sprite billboard's screen rectangle
  (`IndoorRenderer.cpp` `inspectAtCursor`). The hover outline is already drawn on the model in both worlds.
- **Pick-up and inspect are presentation-independent.** Click, context action ("Pick ..."), drop into the hand and
  RMB inspect all go through `GameplayWorldItemInteraction` and the shared controller by world item index; they need
  no change for 3D beyond the pick shape.

## 2. Missing model placeholder

An item whose icon has no binding, or whose bound model fails to load, draws one engine-owned placeholder instead of
nothing or its sprite. It must be impossible to mistake for real art:

- **Look**: an upright 40-unit cube with a magenta and black checker on every face, unlit (`KHR_materials_unlit`) so it
  is full-bright in a dark dungeon, turning once every four seconds (presentation only; the simulation treats it as a
  box). The model is `engine/world_items/models/missing_item.glb`, built by
  `level_generation/props/items_claude/scripts/build_missing_item.py` and installed with
  `tools/install_model.py --world-items`; it is never bound to an icon (`missingItemModelBinding()`).
- **Hover text**: the hovered name followed by `[missing 3D model for item <id> - please report]`, so a player who
  sees it knows what to do and the report names the item. Pick-up, inspect and the item itself work normally.
- **Log**: one error per icon per session, for example
  `Ground item 512 "Longsword" (icon item010) has no 3D model; drawing the placeholder`.
- **No silent states**: a missing or invalid `items.yml`, or a placeholder that fails to load, is a load error, not an
  empty binding table.
- **Prevention**: doctests (`WorldItemShapeTests.cpp`, `EffectDefinitionLoaderTests.cpp`) load the engine item table
  and `items.yml` from `assets_dev` and fail when a real MM6-MM8 item has no binding or a binding names a missing
  model. The placeholder is for what slips past, such as new content or a broken package.

The placeholder ships in release builds too: a bug players can see and report beats an invisible item.

## 3. Collision shape per model

Give every bound model a simple shape at its game scale, computed offline and stored in the binding, not read from
the GLB at runtime: physics runs in the world runtime, also headless, where models are never loaded.

- **Ownership**: `GameDataLoader::loadItemTable` reads `items.yml` into the `ItemTable` (`groundModel(itemId)`,
  `hasGroundModel(itemId)`), so both world runtimes, headless included, and the presentation read the same bindings.
  `WorldFxSystem` keeps only the loaded models. A missing or invalid `items.yml` fails the data load.
- **Binding data**: each `items.yml` entry carries `bounds: [minX, minY, minZ, maxX, maxY, maxZ]`, the model's box
  in world units at its game scale in the item's own frame (`game/tables/ItemModelBindings.h`), written by
  `tools/item_model_shapes.py` from the runtime GLBs (`--check` reports stale entries). Re-run it after any model is
  installed or replaced; the installers do not write it yet (section 7). Per-icon overrides for odd shapes (a bow's
  arc, a helmet's opening) wait for the final models.
- **Sweep shape**: an item does not turn in flight (until the optional tumbling), so its airborne orientation is
  known: the yaw hashed from its key (`worldItemYawRadians`). It sweeps a chain of spheres along the box's long side
  (`worldItemSphereChain`): one for compact items, up to five for long ones, each resting on the underside, with the
  existing sphere sweeps (`sweepIndoorSphereAgainstFace` indoors, `collideSphereWithFace` outdoors). The box itself
  is used for settling and picking. An enclosing sphere is wrong for long items: a staff would hit a wall 200 units
  early and stand off the floor by its half-length.
- Keep `object_list.txt` radius/height for projectiles; do not rewrite the legacy table.

## 4. Shared simulation: airborne, contact, settled

One shared world-item motion step for both worlds, with the world supplying its geometry queries (indoor faces and
sectors; outdoor terrain, BModel faces, water). This follows the architecture rule that BLV/ODM code owns only
collision and floor queries.

1. **Airborne.** Gravity (900, unchanged); the sphere chain, not the origin, is swept against walls and ceilings
   each sub-step (`findWorldItemIndoorWallHit`, `OutdoorWorldRuntime::sweepWorldItemAgainstWalls`); floors stay with
   the worlds' floor queries. Indoors keeps its 128 Hz sub-steps; outdoors now splits each frame into steps of at most
   1/128 s. A wall hit reflects the velocity (`reflectWorldItemVelocity`, the native object formula, also used for the
   indoor point hits) with the ground damping; indoors it also fires the wall's object trigger. Items that are not
   items (no carried item) and loot satchels still move as points. Expiry over water is unchanged.
2. **Contact.** Floor hits keep the existing bounce rules (`Bounce` flag, factor 0.5, stop velocity 10, ground
   damping) at the origin plus one unit of clearance; every model's underside is at its origin. Indoor positions are
   still integers rounded every step, so slides slower than about 64 units/s stop.
3. **Settled.** When the item stops, the presentation fits its resting pose once (`fitWorldItemRestingPose`): the
   ground under the box's four corners and centre (outdoors the drawn terrain or the BModel floor, indoors the floor
   query; a point more than 24 units from the item's height does not support it), the slope along and across the
   item, at most about 20 degrees, then raised so no supporting point is above its underside. Nothing new is saved:
   yaw is hashed from the key and the fit is recomputed after a load.

The renderer only draws the state: flat at the simulated z while moving, the settled pose at rest. The 16-unit snap
band is gone. Indoor items get the same footprint fit on ramps and stairs. Outdoors, a sliding item is drawn at the
native terrain height and lands on the drawn terrain only when it stops.

**Tumbling** is a later, optional step: a spin about the long axis while airborne, starting from the throw direction
and damped on each bounce, blending into the settled pose on the last contact. Only after wall collision and settling
look right; it would replace the fixed sphere chain with one that turns with the item. Full rigid-body stacking and
item-to-item collision are out of scope; overlapping drops (monster satchels, a party dropping several items) can be
spread by a small horizontal offset at spawn instead.

## 5. Hover, pick-up and inspect

Pick targeting stays deliberately more forgiving than physics and separate from it.

- **Pick shape** (`intersectWorldItemPickBox`) from the same binding: the box grown to at least 40 x 40 x 24, so
  small items (gems, rings, coins, 14-30 units) stay easy to click, and long items are clickable along their visible
  length. The box turns with the item's yaw, so a sword lying diagonally is picked along its blade. It ignores the
  settled tilt and the drawn height's few units of difference.
- **Indoors** the same box replaces the sprite screen rectangle for every item; as before, an item hit wins over a
  face hit.
- **Priority**: when boxes overlap, prefer the nearest ray hit; keep today's preference of items over passive
  entities and objects.
- **Hover outline**: already on the model; no change. The placeholder takes the outline like any model.
- **Inspect (RMB)**: the existing item popup with the inventory icon is correct; the model is only the world
  presentation. A rotating 3D preview in the popup is not needed.
- **Floating items** (`NoGravity` objects) keep their simulated height; they are never ground-fitted or snapped.
- **Sparkle** (`worldItemSparkle`): items worth looking at glitter in a colour by their value in gold with their
  enchantments (as a shop buys them): green from 1000, purple from 2500, gold with rising motes for artifacts, relics
  and named uniques, red for quest items (base value 0), sparse warm white for coin heaps. `WorldFxSystem` loops
  `openyamm:fx/item_sparkle/*` (glint sprites, `engine/effects/authored/library.yml`) for each such item within 3072
  units of the party, its emitter jumping between random points over the item's top so the glints cover it. Every
  other item (`WorldItemSparkle::Plain`, OY-618) glints faintly white (`item_sparkle/plain`), its glints drifting up
  to be brightest half a grass height over it, so small loot shows in tall grass; Settings > Interface > Sparkle on
  all loot (`[gameplay] loot_sparkle`, on by default) turns only that one off. A sparkling item keeps 3-6 particles
  alive. Unidentified items sparkle too; placed items not yet takeable do not.

## 6. Retiring the ground-item sprites

Removed outright, with no switch or fallback (done except the packaging and cook lines):

- `[rendering] item_models` (`GameSettings`, `settings.ini`) and the `enabled` parameter of `loadItemModels`.
- The item sprite branches in `OutdoorBillboardRenderer.cpp` (world item loop, `hasItemModel` test at `:3967`) and in
  `IndoorRenderer.cpp` (runtime sprite-object billboards carrying an item, `:9115`). Sprite objects that are not items
  are unaffected.
- The sprite-sized picks: the outdoor `InteractionWorldItemMin*` box and the indoor billboard rectangle for items.
- The WIP exclusions of `engine/world_items` in `tools/package_runtime_assets.py` and `tools/cook_models.py`: the
  models become required runtime content in desktop and Android packages. Bring the 136 MB down towards the plan's
  estimate with the normal cook before the first release package.

The ground sprites in `object_list.txt` stay for now as data (projectiles and other sprite objects share the table);
nothing draws them for items. Their restored images are deleted (2026-10-19: first 359 item-only PNGs, 6.7 MB, then
the whole `engine/decorations_x2/` pack and the billboard loaders' lookup of it, once nothing drew it), along with
the map load's preload of every pickable object's sprite. MM9 treasure bags (loot containers on the ground) draw the
smallest corpse loot satchel (`lootBagModelBinding`, `engine/models/loot_satchel_t1.glb`) and are picked by its box. Outdoor keyboard targeting takes an item's screen rect from
its pick box (`worldItemPickBoxCorners`) instead of its sprite.

## 7. Order of work

Done (2026-10-18): bindings in the item table with a load error for a missing `items.yml`; coverage doctests; the
placeholder with hover text and log; the `item_models` switch and the item sprite paths removed; `bounds` for all 911
bindings; sphere-chain wall sweeps and outdoor sub-steps; the airborne/settled presentation with the footprint fit,
indoors included; model pick boxes in both worlds. Unit tests cover the shape helpers.

Waiting for the item generators to finish (they run `tools/install_model.py` and `tools/cook_models.py`):

1. `tools/install_model.py --world-items` (and `install_family.py`) write `bounds`; until then re-run
   `tools/item_model_shapes.py` after installs. Per-icon overrides for odd shapes.
2. Include `engine/world_items` in default cooks and in desktop and Android packages, with a size pass on the 136 MB.
   Until then a release package has no `items.yml` and fails its data load.
3. In-game and headless checks on the final models: a sword thrown at a wall indoors and outdoors (no penetration), a
   drop on a slope and a stair edge (ends neither buried nor floating), monster death drops near a wall, small items
   side by side and long items picked at their ends. Re-run the existing scenarios that check where dropped items and
   loot land; their positions change near walls.
4. Optional tumbling.

Projectiles and save data are unchanged throughout. The five weapon-modelling sessions can continue: the model
contract they follow is what the shape generation relies on.
