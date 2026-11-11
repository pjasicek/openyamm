# Indoor destructibles (BLV)

Walls, boards, windows and props that break, on BLV maps (2026-11-04, for MM9's DestructableBrush and DestructableProp
objects on the rebuilt maps; devdocs/mm9_rework/REGIONS_FINISH.md step 5). Outdoor (ODM) maps keep their own
BModel destructibles (`OutdoorDestructible`, scene `destructibles` with `binding`), which share the save state and
the Lua functions below.

## Scene data

```yaml
destructibles:
  - id: 412                 # MM9: the DAT object index. The save key and the Lua id; unique per map
    name: gateboard
    cog: 20412              # the faces it is made of (their cog number); 0: none
    decoration_cog: 0       # the decorations it is (their SetSprite key, the entity's event_id_primary); 0: none
    hp: 15
    damage_enabled: true    # MM9's CanDamage
    trigger_destroy_only: false   # only evt.DestroyDestructible breaks it
    sound: Events/shatterwood02.wav
    effect: openyamm:fx/destructible/wood
    effect_scale: 0.6
    center: [1200, -340, 96]
    destroyed_event: 360    # a map event run when it breaks; 0: none
    damaged_event: 0        # a map event run on every hit that damages it; 0: none
```

`game/indoor/IndoorMapData.h` `IndoorDestructible`; parsed by `game/maps/IndoorSceneYml.cpp` (an overlay's list
replaces the base scene's). An entry needs a cog or a decoration cog and a positive hp.

## Runtime

`IndoorWorldRuntime` (game/indoor):

- **State** is `EventRuntimeState::destructibles` (hp, damage enabled, destroyed), created from the scene on first use
  and saved with the map. On map load a destroyed destructible is hidden again (no sound or effect).
- **Damage**: a party's or an event's missile striking one of its faces or props deals the missile's damage
  (monsters' missiles do not); a melee blow on one of its faces or its decoration deals the blow's damage (the world
  surface or entity under the cursor, within melee reach: `IGameplayWorldRuntime::isPartyAttackMeleeBModelTarget` /
  `isPartyAttackMeleeEntityTarget`, true for a standing destructible that takes damage). Nothing happens while
  damage is disabled, for `trigger_destroy_only`, or once destroyed. Monsters do not damage destructibles.
- **Props take missiles** (2026-11-06): each decoration of a destructible's decoration cog is a hit cylinder for party
  and event missiles while the destructible stands and takes damage (`initializeIndoorDestructibles`: the
  decoration's radius and height, at least 24 and 48; a collision of kind World with `worldEntityIndex`, no bounce).
  Monsters' missiles pass props, as before.
- **Area impacts** (2026-11-06): a party's or an event's blast (Fireball, Meteor Shower, Starburst, Rock Blast, Death
  Blossom, dragon breath, Flame Blast, a Carnage arrow) deals its damage to every standing destructible whose box (its
  faces and props) lies within the blast radius of the burst (`GameplayProjectileService::
  buildProjectileAreaDestructibleHits`; the struck destructible takes only its direct hit). No line-of-sight test,
  as MM9's ExplodeDamage. Outdoors the same rule covers the BModel destructibles (their BModels' boxes). Spells
  without a missile (Inferno, Armageddon, Prismatic Light) break nothing.
- **Hit boxes**: a destructible's faces are hit even while invisible (`IndoorMapData::destructibleFaceMask`; MM9's
  RayHit boxes: Sturmford's drawbridge chains are invisible slabs round the visible chain), until it is destroyed.
- **Destruction**: hp 0 or `evt.DestroyDestructible`. Its faces become invisible and untouchable (`setFacetBit`, saved
  in the map delta), its decorations hidden (a SpriteOverride on its decoration cog), its sound plays at its centre,
  its effect spawns there (`worldEffectRequests`), and its `destroyed_event` runs. An actor standing on one of its faces
  loses that floor (`grounded` off) and falls, also an idle one (2026-11-10: Verhoffin Ruins' ceiling slabs, which the
  busts wait on until KingKong.scr's ForceFall breaks them; a flat brush between two rooms takes `motion: break,
  doorway: true` like a wall, and the converter gives it a horizontal portal).
- **Events** (`destroyed_event`, `damaged_event`) run at the next world update, never inside the event or blow that
  caused them.
- **Cost** (2026-11-11: a break on Sturmford cost 200-450 ms of frames, now about one frame): the renderer updates the
  destroyed faces in place (`IndoorRenderer::updateFaceAttributeChanges`: a changed face bit collapses the face's
  vertices in its draw group; no batch rebuild), also when an event set the bit (`evt.SetFacetBit` in a destroyed
  event) or a door starts moving in the same frame; only a change of what the batches read from the events
  (`evt.SetTexture`) rebuilds them. The collision caches redo the changed faces alone
  (`IndoorFaceGeometryCache::geometryForFace` rebuilds a face whose bits changed,
  `IndoorMovementController::refreshChangedFaceAttributes` its masks), the same for every face bit an MM6-MM8 script
  sets. A broken prop re-lights the map only when it carries a light. The monsters' path map is rebuilt off the main
  thread (the gap may open a route), and the map it replaces is freed there too.

## Aiming

A party attack with no actor under the crosshair (or the cursor) used to go to the nearest visible hostile
(`chooseFallbackRangedTarget`). A standing destructible face, BModel or prop under the crosshair now wins
(`GameplayActionController::crosshairDestructibleOverridesFallback`): the bow, crossbow, thrown, blaster or wand shot
flies at the crosshair's hit point and breaks it on impact, unless the fallback hostile is within blow reach (407
units; then the member strikes it as before). A destructible under the crosshair within blow reach takes a blow
from a member who also carries a bow (2026-11-09; before, the bow fired because only an actor in reach counted). An
attack spell or quick cast missile (Fire Bolt, Lightning Bolt ...)
with no actor under the crosshair flies there too (`GameplaySpellService::resolveCursorDestructiblePoint`, which
picks with `pickPartyAttackTarget`, through `standingDestructibleHitPoint`). Indoors and outdoors alike; a broken or
damage-disabled destructible does not count. `tests/scenarios/mm9/destructibles/sturmford_chain_crosshair.yml`.

## Lua

| Function | |
| --- | --- |
| `evt.DamageDestructible(id, amount)` | damage it as a blow would; true if it took damage |
| `evt.DestroyDestructible(id)` | break it now (even if damage is disabled); true if it was standing |
| `evt.SetDestructibleDamage(id, on)` | MM9's DamageOn / DamageOff; true if it changed |
| `evt.IsDestructibleDestroyed(id)` | whether it is broken |

`id` is the scene entry's id (an outdoor map's: its source object index).

Console: `destructible <id> damage <amount>`, `destructible <id> destroy`, `destructible <id> state` (its hp and
standing or broken; `untouched` before anything hit it), as scenarios check them
(`tests/scenarios/mm9/destructibles/`).

## Effects

`assets_dev/engine/effects/authored/library.yml`: `openyamm:fx/destructible/stone` (a settling dust cloud and falling
rubble), `wood` (splinters and a little dust), `glass` (glinting shards) and `metal` (sparks and grey fragments), all
CC0 sprites of the effect library, sized for a piece about 200 units across.

## MM9 maps (the converter)

`level_generation/projects/mm9r_common/dungeon/destructibles.py`, run by every rebuilt MM9 map:

- A DestructableBrush whose faces stay static or invisible (its RayHit box) gets the cog `20000 + its DAT index` (a
  map hook's own cog is kept). A breakable window (glass role) gets glass nodes of its own (`STATIC_glass<k>_c<cog>_`)
  whose faces take its cog through the scene's face overrides (Sturmford City: 26 panes). A brush a map turns into a
  mover (its door rules) keeps that route and gets no entry. A rule `motion: break` (2026-11-06, the brushes once
  built as click movers: Connecting Tunnels' rock fall, Thjorad Mine, Yanmir's supports...) keeps the mover's place in
  the plan (no voxel solid, its doorway portal) but builds static cog faces and an entry; its `click` (default true)
  deals a killing blow through `evt.DamageDestructible` (event 38000 + the index; none for TriggerDestroyOnly), or
  names another event (`click: 38127`: a second brush clicks the first).
- A DestructableProp's decoration gets the SetSprite key `20000 + its DAT index` unless a hook gave it one.
- **A brush between two rooms needs a portal** (2026-11-08). The engine's sight (line of sight, monsters noticing the
  party and each other) and its portal rendering cross from sector to sector only through portals, and breaking a
  destructible only hides its faces: a brush built `static` (solid in the voxel pass) between two rooms leaves a hole
  that is still a wall to them. Thronheim City's prison wall broke into a hole that showed the empty clear colour
  instead of the cell's floor, and the guards and the Desert Terror could not see each other through it. Such a brush
  takes the `break` route with a doorway: `{group: <name>, motion: break, doorway: true}` (`click: false` where MM9 has
  no click), as Ta'Sar Academy's cracked wall. `sealed_passages` checks every `static` destructible brush after the
  rooms are labelled: one with a different room on either side (probed along its thin axis) and no portal over it is
  printed as `destructible <name> seals rooms ...` and counted in the build report's `destructible_sealed_passages`.
- MM9's HitPoints (at least 1: MM9's 0 is a pane that breaks at the first hit), CanDamage, TriggerDestroyOnly and
  CustomSound; the debris material from the sound's name, else the Stone/Wood/Glass/Metal debris flags, else wood
  for a prop and stone for a brush (with that material's sound when MM9 gives none).
- MM9's Death/DamageTrigger messages are each map's to translate: a map hook `destructible_events(build)` returns
  `{DAT name: (destroyed event, damaged event)}`. The regions' `regionlua.py` may also list `BARRED_DOORS`
  (`{door group: destructible or [destructibles]}`: a gate's boards, Sturmford's two drawbridge chains; a click says it
  is barred until they all break, and breaking the last opens it and calls `handlers.barredOpened(group)`).
- Where the map hook gives no destroyed event, MM9's own consequences (dungeon/destructibles.py `on_break`, Lua from
  dungeon/objects.py, event 30000 + the DAT index): a DestructableProp whose SpawnObject is a TreasureBag drops it
  (the scene's `spawned_loot_containers`, `evt.SpawnLootContainer`: Bathhouse's 21 urns, Beethoven's one); an
  `Exploding` one deals ExplodeDamage (fire) to the party within DamageRadius of its centre and damages the other
  exploding destructibles there (a chain); a Death/DamageTrigger `off` to a PerceptionBrush the shared hints placed
  turns that hint off (`HintOff<cog>`; the damaged event is 34000 + the index).

## Not yet

- MM9's debris models and DestroyFilename swaps (a prop's broken model); SpawnObject other than a TreasureBag
  (Ta'Sar Academy's DestructableProp0 spawns a Dagrell). Explosions hurt the party and the other exploding
  destructibles only, not monsters (no Lua call damages actors in an area).
