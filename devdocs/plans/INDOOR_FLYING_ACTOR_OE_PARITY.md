# Indoor Flying Actor OE Parity

This note records the behavior target for indoor flying monsters, using the local OpenEnroth checkout as a behavioral
reference. It is intentionally about engine behavior, not copied implementation.

## OpenEnroth Behavior

`reference/OpenEnroth-git/src/Engine/Graphics/Indoor.cpp` runs indoor actor movement in `BLV_UpdateActors`.

- The indoor floor is sampled from the actor position plus `actor.radius` on Z.
- `isFlying` comes from monster data, but is forced off when the actor cannot act. In OE `CanAct()` excludes stoned,
  paralyzed, dying, dead, removed, summoned, and disabled actors.
- Walking actors get horizontal velocity from yaw and move speed. Flying actors also get Z velocity from pitch.
- Non-flying actors receive gravity. Flying actors do not.
- Collision is split into a horizontal pass and, only if the actor did not move upward, a vertical pass.
- The actor yaw is adjusted from actual travel when movement succeeds.

`reference/OpenEnroth-git/src/Engine/Graphics/Collisions.cpp` runs `ProcessActorCollisionsBLV`.

- Actor collision uses a low probe at `pos.z + radius` and a high probe at `pos.z + height`.
- Indoor geometry, decorations, party, sprite objects, and nearby actors are checked.
- Indoor sky and ledge-drop avoidance block ground actors, not flying actors.
- Geometry collisions slide along the hit plane and can trigger `FACE_TriggerByMonster`.
- Floor faces can step the actor up when the collision is close enough.
- Actor/party/decor collision responses are not disabled for flying actors. Contacts can stop, face, or flee depending
  on relation and crowd state.

`reference/OpenEnroth-git/src/Engine/Objects/Actor.cpp` uses these direction points:

- Actor-to-target direction starts from actor `pos.z + height * 0.75`.
- Party targets use a preferred party Z when one is supplied.
- For flying melee pursuit against a non-flying party, `AI_Pursue1` prefers `pParty->height`.
- For flying missile pursuit, `AI_Pursue1` prefers `actor.radius + 512`. `AI_Pursue2` and `AI_Pursue3` only use that
  missile hover outdoors; indoors they fall back to party height.

## MMerge/Rodril Check

Rodril/MMMerge does add an optional monster pathfinding module outside the original engine:

- `reference/mmmerge/Scripts/Global/MonsterPathfinding.lua` processes monsters only when `Game.ImprovedPathfinding` is
  enabled and the game is not in turn-based mode.
- Indoors, flying monsters are eligible inside a shorter 6000-unit range; ground monsters use a 12000-unit range.
- Outdoors, the script limits processing to non-flying monsters.
- It avoids path ownership when the target is reachable: `TraceReach` first checks line of sight, then direct movement
  reachability for non-missile attackers.
- If the target is not reachable, `AStarWay` calls the DLL wrapper.
- `reference/mmmerge/Scripts/Modules/PathfinderDll.lua` passes `Monster.Fly`, `Monster.BodyRadius`, and a step length
  derived from body radius into `MMPathfinder.AStarWay`.
- The queue gives flying monsters an extra distance cost, so they are processed later than nearby ground monsters.

OpenYAMM therefore keeps OE direct flying pursuit as the baseline, but allows the existing indoor path runtime to plan
for flying actors when direct reach is blocked. The path object uses `canFly`, body radius, and a 6000-unit planning
range to match the Rodril/MMMerge shape.

## OpenYAMM Mapping

OpenYAMM should keep MM8 dragons and similar monsters as flying actors when their monster table says `Fly=Y`.

- Ground conversion (`Fly=N`) would hide the bug, but it would also remove pitch/Z pursuit, flying collision semantics,
  and OE behavior for indoor dragons.
- Normal indoor flying pursuit should remain direct movement when the target is directly reachable. When indoor
  pathfinding is enabled and direct reach is blocked, flying actors may use the flying path mode from the path runtime,
  matching Rodril/MMMerge's `Monster.Fly` A* path.
- Direction source points should use 75% of actor height, matching OE direction math.
- Combat/LOS can keep using the party attack target, but flying movement toward the party should use the party body
  height target. This avoids large actors driving their feet below the dungeon floor while trying to put their 75%
  height point on the lower attack point.
- Flying movement must still collide with indoor world geometry and must not finish below the supported floor when the
  actor body intersects that floor.
- Flying actors should still react to actor/party contacts after movement; being airborne does not suppress the OE
  contact response.

## Invariants To Preserve

- Flying actors are not affected by gravity while they can act.
- Paralyzed and terminal flying actors use non-flying passive physics, so they can fall instead of hovering.
- Flying actors can move vertically from pursuit pitch/desired Z.
- Flying actors collide with walls, floors, ceilings, decorations, actors, sprite objects, and party.
- Flying actors cannot pass through solid walls or ceilings during horizontal or vertical movement.
- Flying actors are not constrained by ground-only ledge avoidance.
- Flying actor feet are clamped out of floor penetration only when their body actually overlaps the support floor, not
  when a small actor is simply below an overhead floor.
- Indoor A* for flying monsters is allowed only through the flying path mode, with direct reach checked first.
