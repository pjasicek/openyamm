# Monster pursuit around ledges and melee reach

Status (2026-10-26): implemented. Two changes that let a melee monster find the way up to a party on a ledge
instead of standing under it.

## Melee vertical reach (`world.yml` `actorCombat`)

```yaml
actorCombat:
  meleeVerticalReach: 0.5
```

- A monster's melee reaches the party only across a height difference (feet to feet) of at most this share of the
  lower body's height, and never less than 48 (`GameplayActorService::MinimumMeleeVerticalReach`), so a step never
  stops a blow. With 0.5, a 179-high Drudge cannot strike a party standing 96 above it and pursues it instead.
- Without the block (every MM6–MM9 world) the share is 0 and height never matters, as before.
- Read by `loadWorldManifest` (`WorldActorCombatDefinition`), set on the session's `GameplayActorService`
  (`setMeleeVerticalReach`) when a map's runtime starts, copied into each AI frame (`ActorAiFrameFacts::
  meleeVerticalReach`, since the AI builds its own default services).
- Applied where a monster decides it is in melee range of the party (`resolveActorEngagement` in the AI, the indoor
  facts' `inMeleeRange`, the outdoor engagement) and where its blow lands
  (`IndoorWorldRuntime`/`OutdoorWorldRuntime` `...CanApplyPartyMeleeImpact`). Monster-against-monster melee is
  unchanged.
- Hesper sets 0.5 (`level_generation/projects/hesper_stage/stage.py`).

## Path plans in headless runs

Monster routes are planned on worker threads (`ActorPathRuntime`, two per world). A headless run simulates many seconds
in a few wall-clock milliseconds, so a plan that took 30 ms landed only after the run had moved on, often after its
end: headless pursuits never detoured (`path_deferred=1` for a whole scenario). Every headless command now sets
`OPENYAMM_SYNCHRONOUS_PATH_PLANS` (`game/app/main.cpp`), and `ActorPathRuntime::setWorkerCount` then keeps no workers,
so plans run on the calling thread and land in simulated time. The game itself keeps its workers.

## Checks

- Unit tests: `--test-case='*melee vertical reach*,*actor combat*'` (the rule; parsing and errors).
- Headless (Hesper stage): `level_generation/projects/hesper_walk_test/walk_test.yml` in the walkability test room (a
  96-high platform with a ramp at one end): a Drudge on the floor plans a route, takes the ramp and reaches the party
  on the platform; a Drudge just below the edge, within the flat melee distance, does not strike up and goes round by
  the ramp (`actor_visible` `near` with `min_z`).

## Squat bodies on stairs

Status (2026-10-31): implemented for walkers indoors. A body wider than it is tall (height < 2 × radius: rats, spiders,
behemoths, MM9's Nagates and Imps) has its upper probe sphere at its radius. That sphere reaches down to its feet and
up to 2R, so it took the next steps of a stair as obstacles and needed 2R of headroom.

- **Planner** (`PathMap::traceWalkBody`, indoors only, `riserHeight > 0`): the obstacle loop skips, for a squat body, a
  face wholly over its head and a face it climbs (`PathMap::isClimbedStepFace`): within `riserHeight` of the feet, a
  step's underside (a ceiling face with a floor at most 24 above it) or a riser (a wall facing the move within 60°
  whose top meets a floor). Railings, a stair's sides, low ceilings and lintels still block.
- **Movement** (`IndoorMovementController::resolveMoveSingleStep`): for a squat body the leading floor probe looks 64
  ahead instead of its radius (at radius 190 it passed over the next tread onto the floor under a spiral stair and the
  body stood crushed under the tread's underside), it steps up early from any face at its own height, and its sweep
  ignores faces wholly over its head.
- Taller bodies and outdoor pathing are unchanged.
- Tests: `--test-case='*squat body*'` (`tests/PathMapTests.cpp`). Evidence, MM6-MM8 route comparison and the Thousand
  Terrors probes: [spiral stair pathing](mm9_rework/SPIRAL_STAIR_PATHING.md#done-2026-10-31-option-a3-squat-bodies-on-stairs).

## Wide monsters in narrow passages (`world.yml` `actorMovement`)

Status (2026-11-04): implemented for MM6-MM8. Queen Cobras (radius 72) could not leave their rooms in Temple of Tsantsa
(`6t3.blv`): its necks and corridors are 128 wide, and OpenYAMM sweeps a body's spheres against faces and their edges,
so a body needs its full diameter of clearance. The original tested a sphere against a face only where the sphere's
contact point lay inside the face, with a ray fallback and no edge or vertex test (re_mm8/CREATURE_MOVEMENT.md, "Wall
collision"): a monster passed any doorway its centre fitted through. Every monster of radius 64 or more was held at
128-wide passages (Wights, Archers, Wyverns, most MM7/MM8 large monsters).

```yaml
actorMovement:
  levelRadiusLimit: 60
```

- A monster wider than the limit meets the level indoors (movement and its physics step) and plans its routes at the
  limit (`GameplayActorService::levelCollisionRadius`, set from `WorldActorMovementDefinition` when a map's runtime
  starts). Its own radius still sets its melee reach, its projectile hit radius and how close other bodies come to it.
- MM6, MM7 and MM8 declare 60 (a 128-wide passage with slack). Without the block (MM9, custom worlds) the full radius is
  kept. Outdoors walkers already use the original's fixed radius 40.

## Route plans for a whole pack

Status (2026-11-04): implemented indoors and outdoors. A pack led round a loop (Temple of Tsantsa's central room) turned
back. Route plans were limited map-wide to one every 0.1 s, and taking up a finished worker plan reset that clock too:
about five plans a second for every pursuer on the map, and the first actors in update order took them. A monster whose
route had ended (or that a bump turned away) waited seconds for a new one and in the meantime walked straight at the
party, through the wall between them: back the way it came.

- Each actor still replans at most once a second (`minReplanIntervalSeconds`, also after a failed plan
  `failedRetrySeconds`); the map-wide clock is gone. The per-step budget (two new plans per 1/128 s AI step) counts
  only plans started (`ActorPathResolveResult::requested`), not finished plans taken up.
