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
- **Damage**: a party's or an event's missile striking one of its faces deals the missile's damage (monsters' missiles
  do not); a melee blow on one of its faces or its decoration deals the blow's damage (the world surface or entity under the cursor, within melee reach:
  `IGameplayWorldRuntime::isPartyAttackMeleeBModelTarget` / `isPartyAttackMeleeEntityTarget`). Nothing happens while
  damage is disabled, for `trigger_destroy_only`, or once destroyed. Monsters do not damage destructibles.
- **Hit boxes**: a destructible's faces are hit even while invisible (`IndoorMapData::destructibleFaceMask`; MM9's
  RayHit boxes: Sturmford's drawbridge chains are invisible slabs round the visible chain), until it is destroyed.
- **Destruction**: hp 0 or `evt.DestroyDestructible`. Its faces become invisible and untouchable (`setFacetBit`, saved
  in the map delta), its decorations hidden (a SpriteOverride on its decoration cog), its sound plays at its centre,
  its effect spawns there (`worldEffectRequests`), and its `destroyed_event` runs.
- **Events** (`destroyed_event`, `damaged_event`) run at the next world update, never inside the event or blow that
  caused them.
- **Cost**: the renderer updates the destroyed faces in place (`IndoorRenderer::updateFaceAttributeChanges`: a face
  bit set by the world, not by an event, collapses the face's vertices in its draw group; no batch rebuild), and a
  broken prop re-lights the map only when it carries a light. The monsters' path map is rebuilt (the gap may open a
  route).

## Lua

| Function | |
| --- | --- |
| `evt.DamageDestructible(id, amount)` | damage it as a blow would; true if it took damage |
| `evt.DestroyDestructible(id)` | break it now (even if damage is disabled); true if it was standing |
| `evt.SetDestructibleDamage(id, on)` | MM9's DamageOn / DamageOff; true if it changed |
| `evt.IsDestructibleDestroyed(id)` | whether it is broken |

`id` is the scene entry's id (an outdoor map's: its source object index).

## Effects

`assets_dev/engine/effects/authored/library.yml`: `openyamm:fx/destructible/stone` (a settling dust cloud and falling
rubble), `wood` (splinters and a little dust), `glass` (glinting shards) and `metal` (sparks and grey fragments), all
CC0 sprites of the effect library, sized for a piece about 200 units across.

## MM9 maps (the converter)

`level_generation/projects/mm9r_common/dungeon/destructibles.py`, run by every rebuilt MM9 map:

- A DestructableBrush whose faces stay static or invisible (its RayHit box) gets the cog `20000 + its DAT index` (a
  map hook's own cog is kept). A breakable window (glass role) gets glass nodes of its own (`STATIC_glass<k>_c<cog>_`)
  whose faces take its cog through the scene's face overrides (Sturmford City: 26 panes). A brush a map turns into a
  mover (its door rules) keeps that route and gets no entry.
- A DestructableProp's decoration gets the SetSprite key `20000 + its DAT index` unless a hook gave it one.
- MM9's HitPoints (at least 1: MM9's 0 is a pane that breaks at the first hit), CanDamage, TriggerDestroyOnly and
  CustomSound; the debris material from the sound's name, else the Stone/Wood/Glass/Metal debris flags, else wood
  for a prop and stone for a brush (with that material's sound when MM9 gives none).
- MM9's Death/DamageTrigger messages are each map's to translate: a map hook `destructible_events(build)` returns
  `{DAT name: (destroyed event, damaged event)}`. The regions' `regionlua.py` may also list `BARRED_DOORS`
  (`{door group: destructible or [destructibles]}`: a gate's boards, Sturmford's two drawbridge chains; a click says it
  is barred until they all break, and breaking the last opens it and calls `handlers.barredOpened(group)`).

## Not yet

- Missiles do not damage decorations (props), only faces; props break by melee or Lua.
- Area damage (fireballs) does not reach destructibles.
- MM9's debris models, DestroyFilename swaps (a prop's broken model) and SpawnObject (an item from a broken crate).
