# Turn-Based Mode OpenEnroth Parity

This document captures OpenEnroth's turn-based combat behavior for an OpenYAMM parity implementation. It is based on
local reference inspection only, primarily `reference/OpenEnroth-git/src/Engine/TurnEngine/TurnEngine.cpp`, plus the
input, spell, actor, projectile, timer, save/load, collision, and rendering hooks listed below.

Do not copy OpenEnroth code. Use this as behavioral documentation for a new OpenYAMM implementation.

## Source Map

- Core state machine: `reference/OpenEnroth-git/src/Engine/TurnEngine/TurnEngine.h`,
  `reference/OpenEnroth-git/src/Engine/TurnEngine/TurnEngineEnums.h`,
  `reference/OpenEnroth-git/src/Engine/TurnEngine/TurnEngine.cpp`.
- Party state and active character selection: `reference/OpenEnroth-git/src/Engine/Party.h`,
  `reference/OpenEnroth-git/src/Engine/Party.cpp`.
- Main loop and message gates: `reference/OpenEnroth-git/src/Application/Game.cpp`.
- Keyboard/mouse input gates: `reference/OpenEnroth-git/src/Io/KeyboardInputHandler.cpp`,
  `reference/OpenEnroth-git/src/Io/Mouse.cpp`,
  `reference/OpenEnroth-git/src/Engine/Graphics/Viewport.cpp`.
- Actor AI/recovery hooks: `reference/OpenEnroth-git/src/Engine/Objects/Actor.cpp`.
- Character attacks/items/recovery: `reference/OpenEnroth-git/src/Engine/Objects/Character.cpp`.
- Spell casting/projectile barriers: `reference/OpenEnroth-git/src/Engine/Spells/CastSpellInfo.cpp`,
  `reference/OpenEnroth-git/src/GUI/UI/Books/TownPortalBook.cpp`,
  `reference/OpenEnroth-git/src/GUI/UI/Books/LloydsBook.cpp`.
- Projectiles/object cleanup: `reference/OpenEnroth-git/src/Engine/Objects/SpriteObject.cpp`.
- Game timer behavior: `reference/OpenEnroth-git/src/Engine/Time/Timer.cpp`.
- Save/load/map transition quirks: `reference/OpenEnroth-git/src/Engine/SaveLoad.cpp`,
  `reference/OpenEnroth-git/src/Engine/Engine.cpp`,
  `reference/OpenEnroth-git/src/Engine/Snapshots/EntitySnapshots.cpp`.
- UI overlay and portrait indicators: `reference/OpenEnroth-git/src/Engine/Graphics/TurnBasedOverlay.cpp`,
  `reference/OpenEnroth-git/src/GUI/UI/UIGame.cpp`.
- Movement/collision dt hooks: `reference/OpenEnroth-git/src/Engine/Graphics/Collisions.cpp`.

## State Model

OpenEnroth keeps two separate but coupled turn-based state flags:

- `Party::bTurnBasedModeOn`: the gameplay-visible mode flag.
- `Timer::_turnBased` on `pEventTimer`: freezes event/game time while still allowing frame dt to be measured.

The turn engine state contains:

- `turn_stage`: `TE_NONE`, `TE_WAIT`, `TE_ATTACK`, or `TE_MOVEMENT`.
- `pQueue`: mixed actor/character initiative queue.
- `turn_initiative`: round budget, initialized to `100`.
- `ai_turn_timer`: monster movement timer, initialized to `64` ticks at start and between movement/attack phases.
- `uActionPointsLeft`: party movement budget, set to `130` during movement. Keyboard move/strafe consumes `26`, so
  the movement phase has five movement chunks.
- `pending_actions`: count of in-flight turn-blocking projectiles/effects.
- Flags:
  - `TE_HAVE_PENDING_ACTIONS`: visible pending-action flag set while `pending_actions != 0`.
  - `TE_PLAYER_TURN`: maintained by queue sorting when the first queue element is a character; OE does not otherwise
    use it outside `SortTurnQueue`.
  - `TE_FLAG_1`: action-animation wait latch used while an actor attack/stun/death animation is still playing.
  - `TE_FLAG_8_finished`: player-requested end of movement phase.

Parity implication: keep turn-based mode as explicit game state, not as a UI-only overlay. The event/game-time clock
must stop advancing while turn-based mode is active, but frame time must still drive animation, sounds, and UI.

## Entry And Exit

Toggling on is allowed only from the game screen. OE calls `Start()` and then sets `bTurnBasedModeOn = true`.

Toggling off is allowed only when already in turn-based mode and either:

- the current stage is `TE_MOVEMENT`, or
- the first queue entry is a character.

OE refuses to toggle off during monster/wait phases and while a monster is at the front of the queue.

`Start()`:

- Clears `TE_HAVE_PENDING_ACTIONS`.
- Sets the event timer to turn-based/frozen.
- Plays the start-turn-based UI sound.
- Sets `turn_initiative = 100`, `turns_count = 0`, `ai_turn_timer = 64`, `turn_stage = TE_WAIT`.
- Rebuilds the queue from characters that can act and nearby actors that can act.
- Seeds initial initiative and sorts the queue.

`End(playSound)`:

- Sets stage to `TE_NONE`.
- Resets queued actor state.
- Clears `SPRITE_HALT_TURN_BASED` on all sprite objects.
- Writes queue initiatives back into character `timeToRecovery` and actor recovery fields.
- Optionally plays the end-turn-based sound.
- Clears `TE_HAVE_PENDING_ACTIONS`, unfreezes the event timer, and clears the queue.

Save/load and map-transition quirks:

- Loading a save explicitly exits turn-based mode first and then forces the loaded game to start in realtime. The MM7
  snapshot has turn-based fields, and OE reconstructs them, but `loadGame` resets both the event timer and party flag
  afterward.
- The game loop also calls `End(false)` before each world preparation and clears the party flag to keep the two state
  flags in sync.
- `DoPrepareWorld` clears the attack list and erases only actor entries from the turn queue, because actor ids become
  invalid when actor lists are reloaded.
- Party death/week reset exits turn-based mode with sound.

Parity implication: do not persist an active turn-based combat session across load. Save the underlying recovery fields
if the save format requires them, but load into realtime like OE.

## Queue Construction And Sorting

Queue elements contain packed id, initiative, action length, and selected AI action type.

Initial player queue:

- Adds each character that `CanAct()`.
- Ready characters are sorted by normal attack recovery, then assigned initiatives `2`, `3`, `4`, ... in that order.
- Characters already in recovery get `timeToRecovery * 0.46875 + 16`.
- OE has a minor quirk: while adding initial characters it zeros `pTurnBasedCharacterRecoveryTimes` by queue position,
  not by character id. If earlier characters cannot act, this can zero a different slot than the character id slot.

Initial actor queue:

- Uses the current near-actor AI list.
- Skips actor id `10` as a hardcoded sentinel.
- Adds actors that can act and report `ActorNearby()`.
- Sets actor initiative randomly to `1`, `3`, or `5`, then adds `16`, resulting in `17`, `19`, or `21`.
- Sets actors to stand/bored and marks them as standing in the queue.

Sorting behavior:

- Non-acting actors/characters are assigned initiative `1001`; actors also have their queue state reset.
- Queue is sorted ascending by initiative.
- Initiative ties prefer characters over actors.
- Same-type ties prefer lower id.
- After sorting, the queue is resized to remove inactive trailing elements.
- If the first queue item is a character, that character becomes the active character and `TE_PLAYER_TURN` is set.
  Otherwise active character becomes `0`/none and `TE_PLAYER_TURN` is cleared.
- Character UI recovery times are refreshed from initiative using the reciprocal conversion factor.

Parity implication: the queue is not "party turn, then enemy turn"; it is an initiative queue embedded inside the
attack phase, with a separate monster movement phase and party movement phase around it.

## Stage Lifecycle

### `TE_WAIT`: Monster Movement / Initial Delay

This stage starts when entering turn-based mode and after each party movement phase.

- If `ai_turn_timer == 64`, OE assigns movement decisions to queued actors.
- While `ai_turn_timer > 0`, actors continue/additional-move using frame dt.
- When the timer expires, OE stops actor movement, sets all queued actors to stand, switches to `TE_ATTACK`, and sets
  `ai_turn_timer = 100`.
- The opening overlay uses a separate accelerated animation in OE. Vanilla shared the same 64-tick timer and cut the
  hand animation short; OE intentionally fixes that.

### `TE_ATTACK`: Initiative And Actions

This is the only stage where attacks, most spell casts, item use, and steal actions may consume a character turn.

At the start of a new attack phase, `turn_initiative == 100`, so OE:

- Re-adds missing party characters that can act, with initiative `100`.
- Re-adds newly arrived actors from the near-actor list, with initiative `1`.
- Increments `turns_count`.
- Converts any zero initiatives back to `100`.
- Steps initiatives down until something is ready or the round budget reaches zero.
- Immediately schedules AI actions for front-of-queue actors whose initiative is ready.

During the phase:

- If a player action occurs, `ApplyPlayerAction()` only does anything in `TE_ATTACK`.
- The acting character gets initiative set to stored turn-based recovery if present, else normal attack recovery.
- Player recovery is clamped to at least `30` ticks.
- The queue is re-sorted and initiatives tick downward until another entry is ready or round initiative reaches zero.
- Actor actions are selected when actor initiative reaches zero and `uActionLength` is zero.
- Actor attack/stun/death animations block phase advancement through `TE_FLAG_1`.
- In-flight projectiles/effects block advancement through `pending_actions` and `TE_HAVE_PENDING_ACTIONS`.

When no pending action and no actor animation is blocking, `NextTurn()` transitions to `TE_MOVEMENT`.

### `TE_MOVEMENT`: Party Movement Budget

`NextTurn()` transitions here after attack resolution:

- All non-dead/valid queued actors are set to stand.
- Timed effects, water-walking damage, etc. are advanced by a fixed `213` ticks.
- `uActionPointsLeft = 130`.

Player movement:

- Forward/backward and strafe consume `26` action points through a turn-aware wrapper.
- With five chunks of `26`, the party gets five movement actions per movement phase.
- Movement is refused if action points are already exhausted.
- Party collision processing uses a fixed `26` tick movement dt while in `TE_MOVEMENT`, both indoor and outdoor.
- Passing, attacking, quick-casting, clicking an actor, or stealing during movement does not perform that action; it
  sets `TE_FLAG_8_finished` to end movement.
- When action points are exhausted or `TE_FLAG_8_finished` is set, OE clears the flag, returns to `TE_WAIT`, and resets
  `ai_turn_timer = 64`.

Quirks:

- Turning left/right without turn-strafing does not consume action points in the keyboard input wrapper.
- Look up/down and fly controls are queued separately and are not part of the `26`-point movement budget in the input
  layer; verify downstream movement semantics before deciding whether to emulate or tighten this.
- Jump is blocked outright while turn-based mode is on.

## Player Action Gates

Actions allowed in realtime are often blocked or converted in turn-based mode:

- Attack:
  - Ignored in `TE_WAIT`.
  - Ends movement in `TE_MOVEMENT`.
  - Executes in `TE_ATTACK` only if `TE_HAVE_PENDING_ACTIONS` is clear.
- Quick cast:
  - Ends movement in `TE_MOVEMENT`.
  - Otherwise falls back to attack if no quick spell, underwater, or insufficient mana.
- Spellbook:
  - Opening pages, selecting spells, casting from book, and scroll casts are ignored in `TE_MOVEMENT`.
  - Spell casts are refused in `TE_WAIT` and `TE_MOVEMENT` by the spell/ranged attack push helper.
- Pass:
  - Ends movement in `TE_MOVEMENT`.
  - In attack stage, if active character has no recovery, cancels active spell targeting and applies the player action.
  - In realtime, pass assigns normal attack recovery; in turn-based it relies on `ApplyPlayerAction`.
- Item use:
  - Ignored in `TE_WAIT` and `TE_MOVEMENT`.
  - Potions/reagents set a fixed `100` tick turn-based recovery and apply the player action.
- Steal:
  - Mouse click during movement ends movement.
  - Message handling refuses steal in `TE_WAIT` and `TE_MOVEMENT`.
  - In `TE_ATTACK`, steal is blocked while pending projectile actions exist, then applies normal turn recovery.
- Rest:
  - Always blocked while turn-based mode is on, with the "can't rest in turn-based mode" status string.
- Active character cycling:
  - If the current active character can act and has no recovery, OE refuses to switch away.
  - In turn-based mode, active character is forced to the front queue character during `TE_ATTACK`; otherwise there is
    no active character.

## Player Recovery And Spells

Realtime recovery is scaled by debug combat/non-combat multipliers and `flt_debugrecmod3`. Turn-based recovery is not
scaled the same way; it is stored for the queue and consumed by `ApplyPlayerAction`.

Important paths:

- Generic spell recovery stores `pTurnBasedCharacterRecoveryTimes[caster]`, sets the character recovery UI value, and
  applies the player action unless a targeted enchant flow is still active.
- Town Portal and Lloyd's Beacon book UIs do the same special turn-based recovery handling manually.
- Bows, blasters, wands, and many spells create projectile sprite objects. In turn-based mode those objects receive
  `SPRITE_HALT_TURN_BASED`, and a successful create increments `pending_actions`.
- Melee attacks do not assign direct realtime-style recovery while in turn-based mode; they call `ApplyPlayerAction()`.
- Bows/wands/lasers rely on the spell/projectile path for recovery and pending action handling.
- Failure/no-recovery flags still matter. `ON_CAST_NoRecoverySpell` skips recovery even in turn-based mode.

Parity implication: recovery must be stored in a per-member turn action slot before the action is applied. Do not merely
set the same recovery timer used for realtime movement/action lockout.

## Pending Projectiles And Effect Barriers

OE uses `pending_actions` as a hard barrier before turn progression:

- Turn-blocking projectile/effect sprites get `SPRITE_HALT_TURN_BASED`.
- Each successfully created halted sprite increments `pending_actions`.
- When a halted sprite interacts/hits or is removed via collision handling, OE decrements `pending_actions` and clears
  the flag.
- Temporary objects in turn-based mode that get farther than `5120` units from the party are forcibly interacted/ended,
  which clears the pending barrier.
- `NextTurn()` sets `TE_HAVE_PENDING_ACTIONS` and returns while `pending_actions` is nonzero.
- Player attack/steal messages check `TE_HAVE_PENDING_ACTIONS` and refuse new attack-stage actions while projectiles
  are still resolving.

Parity implication: every projectile and delayed spell effect that can affect initiative progression needs an explicit
turn-blocking lifecycle. Missing even one decrement will soft-lock turn progression; missing an increment will let the
queue advance before the hit resolves.

## Actor AI Parity Notes

When turn-based mode is active, `Actor::UpdateActorAI()` still builds the near-actor AI list and processes Armageddon,
then delegates all actor behavior to the turn engine.

Actor movement phase:

- `ActorAISetMovementDecision()` assigns movement/stand/flee/pursue decisions to queued actors.
- `ActorAIDoAdditionalMove()` advances action timers during the 64-tick wait phase.
- `ActorAIStopMovement()` stops queued actors, sets them to stand, clears action lengths, and switches to attack phase.
- During outdoor rendering/movement, actor speed is multiplied by `debug_turn_based_monster_movespeed_mul` only in
  `TE_WAIT`.

Actor attack phase:

- AI chooses a fresh target, derives hostility/range, and selects ranged, melee, pursue, flee, random move, bored, or
  stand behavior.
- Wimp AI flees when hostile if not stationary.
- Normal AI flees below 20% hp within 10240 units.
- Aggressive AI flees below 10% hp within 10240 units.
- Afraid actors flee within 10240 units, otherwise random-move.
- Melee is selected inside `meleeRange`.
- Ranged/spell attacks are only selected inside 5120 units and if the relevant ability/projectile/spell exists.
- OE has a fallthrough quirk in the actor ability switch: `ABILITY_ATTACK1` can fall through into `ABILITY_ATTACK2`
  handling. Preserve only if strict bug parity is required; otherwise document a deliberate fix.
- Actor recovery in turn-based mode uses the monster's base recovery, doubled when slowed. Realtime adds current action
  animation length and debug-scaled recovery in several, but not all, ranged/spell paths. OE is not fully uniform here:
  strict parity should audit each actor attack helper rather than centralizing the formula too early.
- Stun/force effects add a flat `20` tick monster recovery in turn-based mode; realtime scales that same extra recovery
  through the combat recovery multipliers.

Collision/behavior quirks:

- Actor-vs-actor collision reactions are suppressed during `TE_ATTACK` and `TE_MOVEMENT`.
- Actor walking animation uses `pMiscTimer` while turn-based mode is active so walking animation can continue while
  event/game time is frozen.
- Stoned/paralyzed actors render with zero action time.

## Timers, Time, And Buffs

OE's event timer keeps measuring frame dt but stops accumulating total game time when turn-based mode is active. The
main loop skips normal timed-effect advancement while the event timer is turn-based, except for:

- party death/wake-solo-survivor handling, which still runs in turn-based mode;
- the fixed `213` tick timed-effect advancement when entering `TE_MOVEMENT`;
- actor buffs and shrink expiry checks in the turn-based AI path.

Parity implication: turn-based mode should not simply pause the whole simulation. It freezes game time while allowing a
selected subset of animation, AI action timers, projectile movement, death processing, and effect ticks.

## UI And Presentation

Overlay:

- Icons are loaded from `turnstart`, `turnstop`, `turnhour`, and `turn0` through movement icons.
- Initial state starts when the engine enters `TE_WAIT`.
- Initial animation is accelerated by factor `3` in OE to make the full hand animation visible without vanilla's cut
  off.
- Attack stage draws the stop/attack icon.
- Wait stage draws the hourglass animation.
- Movement stage draws an icon based on `5 - actionPointsLeft / 26`.
- The overlay is drawn at fixed screen position `{394, 288}` in OE.

Portrait indicators:

- While turn-based mode is active and the stage is not `TE_WAIT`, OE draws alert-colored rings on consecutive character
  queue entries at the front of the queue.
- The ring color follows party alert state: red if red alert, yellow if yellow alert, otherwise green.

Status strings:

- Rest in turn-based mode uses `LSTR_YOU_CANT_REST_IN_TURN_BASED_MODE`.
- Dismissing a character has a localized "cannot dismiss in turn based mode" string in the data, but no complete
  implementation path was found in this pass.

## Implementation Shape For OpenYAMM

Recommended owned systems:

- Add a shared gameplay `TurnBasedCombatRuntime` or similar under `game/gameplay/`, not indoor/outdoor-specific views.
- Store active mode, stage, queue, pending actions, movement points, initiative, and per-member turn recovery in party
  or gameplay runtime save state as appropriate.
- Expose narrow hooks:
  - `beginTurnBased()`, `endTurnBased(playSound)`.
  - `updateTurnBasedActors(deltaSeconds)`.
  - `tryApplyPlayerTurnAction(memberIndex, recovery)`.
  - `registerTurnBlockingProjectile(handle)`, `resolveTurnBlockingProjectile(handle)`.
  - `consumeTurnMovementAction(kind)` and `finishMovementPhase()`.
- Keep world-specific hooks limited to actor enumeration, movement/collision integration, projectile collision, and
  rendering data, matching the repository architecture rules.

OpenYAMM integration points to audit during implementation:

- Input: `game/gameplay/GameplayInputController.cpp`,
  `game/gameplay/GameplayHudInputController.cpp`,
  `game/gameplay/GameplayPartyOverlayInputController.cpp`.
- Combat/actions: `game/gameplay/GameplayCombatController.cpp`,
  `game/gameplay/GameplaySpellActionController.cpp`,
  `game/gameplay/GameplaySpellService.cpp`,
  `game/gameplay/GameplayItemService.cpp`.
- Party state/recovery: `game/party/Party.cpp`, `game/party/CharacterState.h`.
- Actor AI and runtime state: `game/gameplay/GameplayActorAiSystem.cpp`,
  `game/gameplay/GameplayActorService.cpp`.
- Projectile lifecycle: `game/gameplay/GameplayProjectileService.cpp`.
- World movement/collision hooks: indoor/outdoor movement controllers and world runtimes.
- UI/HUD: `game/ui/GameplayUiRenderer.cpp`, `game/ui/GameplayHudOverlayRenderer.cpp`,
  `game/ui/GameplayPartyOverlayRenderer.cpp`.
- Save/load: `game/maps/SaveGame.cpp` and runtime bootstrap/reset paths.

## Parity Checklist

- Toggle on/off follows OE restrictions and sounds.
- Load/new map/death reset turn-based mode to realtime like OE.
- Event/game timer freezes but frame animation and selected turn systems continue.
- Queue construction uses OE initiative values and sorting/tie rules.
- Start begins with `TE_WAIT` and a 64-tick monster movement delay.
- Attack phase gates player actions by stage and pending projectile barrier.
- Player action recovery is stored per member, clamps to at least 30 ticks when consumed, and advances initiatives.
- Movement phase grants 130 points and consumes 26 for walk/run/strafe.
- Movement phase can be ended by pass, attack, quick-cast, actor click, or steal attempt.
- Party movement collision uses fixed 26-tick dt during movement phase.
- Pending projectile/effect count increments/decrements reliably and blocks turn advancement.
- Actor AI movement/action/recovery behavior follows OE, including flee thresholds and slowed recovery doubling.
- Rest, jump, spellbook, item use, steal, and attack gates match OE stage restrictions.
- UI overlay states and portrait rings reflect stage, movement points, and alert color.
- Tests cover projectile barrier under hit, miss, expiry, and out-of-range cleanup to avoid turn soft-locks.
