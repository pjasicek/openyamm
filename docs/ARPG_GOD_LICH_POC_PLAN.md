# ARPG God Lich Proof Of Concept Plan

## Goal

Build the smallest playable ARPG-style proof of concept from `POE_LIKE_ARPG_MODE_DESIGN_PLAN.md`.

The PoC starts a new game as the existing debug God Lich, shows the character as a visible Lich monster billboard, uses
an angled isometric camera, and supports only the first ARPG control loop:

- `LMB` click ground/terrain/bmodels to move;
- `LMB` click usable event/item/NPC targets to interact;
- `RMB` plain attack hostile target;
- `Q` cast the active character's quick spell;
- player billboard uses idle, movement, attack, cast/attack, hit, and death-style monster animation frames where
  available.

Outdoor maps were the first target. Indoor support is now part of the PoC, but it must not reuse the first-person
indoor portal camera rules blindly. Indoor ARPG uses the same gameplay controls and camera settings, with a
sector-reveal visibility mode that starts from the party sector instead of treating the isometric camera as a normal
first-person eye inside a room.

## Existing Bootstrap

OpenYAMM already has a debug God Lich path:

- setting: `[debug] new_game_god_lich=true`;
- storage: `GameSettings::newGameGodLich`;
- creation hook: `NewGameScreen::buildCharacterFromState`;
- party shape: `NewGameScreen::buildPartyCharacters` already forces one member when `m_debugGodLichRoster` is active;
- character setup: `applyDebugGodLichCharacter(...)` sets name `God`, class `Lich`, level `100`, all skills Grandmaster,
  all spells known, and debug equipment.

Use this path as the PoC character bootstrap. Do not create a separate ARPG character creator.

Expected manual startup:

```ini
[debug]
new_game_god_lich=true
start_world=mm6
```

`start_world` can be any mounted world. MM6 is fine for testing, but the PoC should not hardcode MM6-specific behavior.

## Lich Billboard Source

Use monster billboard animation data, not a new player art pipeline.

Two relevant engine table rows currently exist:

```text
monster_data.txt:
291  Lich King  Lich C
570  Power Lich BLich C

monster_descriptors.txt:
291  Lich C   ... m273s m273w m273a m273a m273n m273d m273x m273f
570  BLich C  ... lc3sta lc3walk lc3atk lc3atk lc3wnc lc3dea lc3ded lc3fgt
```

Preferred PoC choice:

- default to `Lich C` if "tier C lich" means the merged/MM7-style Lich King;
- make the descriptor configurable so `BLich C` can be tested without code changes.

Suggested setting:

```ini
[arpg_poc]
enabled=true
player_monster_descriptor=Lich C
```

The renderer should resolve this through `MonsterTable` and `SpriteFrameTable` exactly like actor billboards do. Avoid
copying sprite names into code.

## Camera Target

Use Path of Exile-like ARPG framing as the reference: fixed angled camera from above and behind the character, not a
direct top-down tactical view. Public gameplay references describe/show Path of Exile as an isometric action RPG with
the player controlled from an isometric perspective.

Sources checked:

- MobyGames Path of Exile gameplay screenshots: <https://www.mobygames.com/game/65225/path-of-exile/screenshots/windows/688063/>
- VGTimes screenshot gallery summary describing Path of Exile as using an isometric camera view:
  <https://vgtimes.com/games/path-of-exile/screenshots/>

The exact OpenYAMM numbers should be tunable from settings because world scale and billboard size may need iteration.

Suggested initial settings:

```ini
[arpg_poc]
enabled=true
camera_yaw_degrees=-45
camera_pitch_degrees=-55
camera_distance=2600
camera_target_height=120
camera_fov_degrees=45
camera_follow_lerp=18
camera_zoom=1.0
camera_min_zoom=0.65
camera_max_zoom=1.45
```

Interpretation:

- yaw controls compass direction;
- pitch is downward angle in the existing OpenYAMM convention;
- distance offsets the camera eye away from the player;
- target height aims at the upper body rather than feet;
- FOV remains perspective for the PoC because current outdoor matrices already use perspective projection;
- orthographic can be evaluated later if perspective causes ARPG readability issues.

## Camera Integration

Current outdoor rendering builds the camera from:

- `OutdoorGameView::m_cameraTargetX/Y/Z`;
- `OutdoorGameView::effectiveCameraYawRadians()`;
- `OutdoorGameView::effectiveCameraPitchRadians()`;
- `bx::mtxLookAt`;
- `bx::mtxProj`.

For the PoC, add an ARPG camera mode inside outdoor view/rendering:

```text
target = party/player position + camera_target_height
forward = direction from camera eye to target
eye = target - forward * camera_distance
```

Important: existing first-person mode treats `m_cameraTargetX/Y/Z` as the camera eye. ARPG mode should not blindly
reuse that assumption. Introduce a small camera-frame helper returning:

```text
eye
at
up
viewMatrix
projectionMatrix
forward/right/up vectors
```

Then use it from both:

- render matrix setup;
- `OutdoorInteractionController::buildWorldPickRequest`;
- any actor/hover fallback projection that assumes the old camera target is the eye.

This avoids mismatches where the scene renders from one camera but picking uses another.

## Settings Model

Add a temporary PoC settings block instead of promoting this to the final ARPG mode model immediately.

Suggested `GameSettings` fields:

```cpp
bool arpgPocEnabled = false;
std::string arpgPocPlayerMonsterDescriptor = "Lich C";
float arpgPocCameraYawDegrees = -45.0f;
float arpgPocCameraPitchDegrees = -55.0f;
float arpgPocCameraDistance = 2600.0f;
float arpgPocCameraTargetHeight = 120.0f;
float arpgPocCameraFovDegrees = 45.0f;
float arpgPocCameraFollowLerp = 18.0f;
float arpgPocClickStopRadius = 48.0f;
float arpgPocMoveSpeedMultiplier = 1.0f;
```

Use `[arpg_poc]` in `settings.ini`.

Do not overload `[debug] new_game_god_lich`; that setting only creates the character. ARPG PoC camera/input should be
separately toggleable.

## Player Runtime State

Add a small PoC runtime state owned by `OutdoorGameView` or a new `game/arpg/ArpgPocPlayerController`:

```text
active
movementDestination
hasMovementDestination
lastGroundClick
currentAnimation
animationSeconds
attackTargetActorIndex
attackInProgress
castInProgress
```

Do not make the player a full `MapActorState` for the PoC. The authoritative player remains the one-member `Party` in
`OutdoorPartyRuntime`.

The visual layer can still use monster sprite frames by resolving the configured monster descriptor into action sprite
frame indices.

## Player Billboard Rendering

Add a dedicated player-avatar draw path near existing outdoor actor billboard rendering.

Minimum requirements:

- draw one billboard at `OutdoorPartyRuntime::movementState()`;
- use configured Lich monster descriptor;
- choose frame from movement/action state:
  - standing: `ActorAnimation::Standing`;
  - moving: `ActorAnimation::Walking`;
  - RMB attack: `ActorAnimation::AttackMelee` or the existing attack action frame;
  - Q quick spell: same attack/cast frame for PoC;
  - hit/death can be deferred unless easily available;
- scale from monster descriptor height/radius;
- sort/depth like actors so terrain/bmodels occlude reasonably.

Recommended first rendering target:

- reuse the same sprite texture resolution and directional-frame logic used by actors;
- if actor rendering is too coupled, extract a tiny shared helper for resolving a sprite frame and submitting a
  billboard quad.

Do not duplicate the sprite decoder or asset loading path.

## Movement

### Input Behavior

When ARPG PoC mode is active:

- show cursor during gameplay;
- disable mouse-look camera control;
- `LMB` pressed/released over UI goes to UI first;
- `LMB` on interactable target runs interaction;
- `LMB` on ground sets movement destination;
- holding `LMB` may continuously refresh destination, but a single-click implementation is acceptable first.

### Ground Picking

Movement click target should include:

- outdoor terrain;
- outdoor bmodels that are walkable/collidable ground surfaces.

The current world pick request already produces rays from screen coordinates. Add a ground pick query that returns:

```text
hit
world x/y/z
surface kind: terrain or bmodel
face/index if bmodel
walkable-ish flag
```

For the PoC, terrain picking alone can land the first patch, but bmodel picking is required before calling the movement
piece complete.

### Movement Execution

Start simple:

- compute 2D vector from current party position to destination;
- stop inside `arpgPocClickStopRadius`;
- feed desired velocity into `OutdoorPartyRuntime::update(...)`;
- movement controller remains authoritative for collision, slopes, water, and vertical position.

If direct movement gets blocked often, integrate `PathMap`/`ActorPathRuntime` style waypointing in a second pass.

Indoor movement should use the same click-to-destination logic, but feed desired velocity into `IndoorPartyRuntime`.
Pathfinding-backed indoor movement can be deferred; the first pass should steer directly toward the clicked point and
let `IndoorMovementController` handle walls, portals, slopes, support faces, and sector transitions.

## Indoor ARPG Mode

Indoor ARPG controls should mirror outdoor controls where possible:

- `LMB` held continuously refreshes a movement destination from the current mouse ground/surface pick;
- `RMB` continuously attacks using shared party attack logic;
- `Q` quick-casts using the same ARPG delayed spell timing;
- mouse wheel adjusts the same `arpg_poc.camera_distance`;
- the camera uses the shared `ArpgPocCameraFrame` helper and `[arpg_poc]` yaw/pitch/distance/FOV/target-height
  settings.

The main implementation difference is visibility. Classic indoor rendering uses portal visibility from the current
camera position and direction. This is correct for first-person, but the ARPG camera may be behind ceilings, outside
the current room, or behind a portal from the renderer's point of view. Therefore ARPG indoor mode should use a
separate visibility mask:

```text
start = party eye sector, falling back to party foot sector
visible = BFS through non-hidden portal faces
limits = max depth and optional distance/cell bounds from party
frustum = broad camera frustum only after the sector has been revealed
```

For the PoC, a simple BFS through sector adjacency is preferred over adapting the first-person portal clipping code.
This keeps current-room and nearby-room geometry stable from an isometric camera. Ceiling faces remain render-hidden in
ARPG mode, while collision and picking can still use them if needed for gameplay.

Minimum indoor implementation slices:

1. Add ARPG camera frame support in `IndoorRenderer::render` and `IndoorRenderer::buildGameplayWorldPickRequest`.
2. Add `IndoorRenderer::buildArpgPocVisibleSectorMask` that flood-fills sectors from the party sector through visible
   portal links.
3. In ARPG mode, use that sector mask for geometry, actors, decorations, sprite objects, and hover/pick consistency.
4. Add indoor LMB destination movement in `IndoorRenderer::updateCameraFromInput`, using `gameplayGroundTargetPoint`
   or the same pick request path.
5. Keep RMB/Q routed through shared `GameplayInteractionController` and `GameplayInputController`; do not duplicate
   damage or spell formulas.
6. Render the God Lich puppet indoors after the control/camera loop is proven, using the same monster descriptor and
   directional sprite logic as outdoor.

Initial indoor acceptance:

- entering a BLV while `[arpg_poc] enabled=true` shows the map from the same fixed isometric camera style;
- ceilings are hidden;
- current and adjacent rooms do not disappear just because the camera is outside the party's sector;
- holding `LMB` moves the party toward the cursor surface point;
- mouse wheel zoom changes camera distance;
- RMB and Q continue to use shared ARPG attack/spell behavior.

## Interactions

`LMB` interaction should reuse existing world interaction behavior wherever possible.

Priority:

1. active overlay/UI;
2. item/loot target;
3. NPC/friendly actor dialogue;
4. chest/decoration/door/event face;
5. ground move destination.

Existing hover/pick types already include `GameplayWorldHitKind::Actor`, `WorldItem`, and `EventTarget`. ARPG mode
should route a left click on those through existing interaction controllers instead of creating duplicate event logic.

If a target is too far away:

- set movement destination near the target;
- remember pending interaction;
- fire interaction once within range.

This can be deferred for the first pass; an immediate interaction at current range is enough for the first smoke test.

## Plain Attack On RMB

PoC behavior:

- `RMB` over hostile actor starts a plain attack;
- if no hovered hostile actor exists, either do nothing or attack nearest visible hostile in a short screen/world range;
- player stops or slows during the attack;
- player billboard plays attack animation;
- existing character attack rules apply for hit chance, damage, recovery, and presentation where possible.

Preferred implementation path:

- add an ARPG-specific input path that identifies `actorIndex`;
- call into existing party attack execution logic rather than duplicating damage formulas;
- add a targeted overload/helper if current attack code only supports crosshair/fallback targeting.

Important behavior:

- do not consume RMB for inspect in ARPG mode;
- leave RMB inspect unchanged in first-person modes;
- respect recovery/cooldown from existing character attack state.

## Q Quick Spell

PoC behavior:

- `Q` triggers the active character's `quickSpellName`;
- target is hovered hostile actor if the spell needs an actor target;
- otherwise use cursor ground point or existing quick-spell fallback behavior;
- player billboard plays attack/cast animation;
- existing mana, known-spell, mastery, and recovery rules apply.

Since God Lich knows all spells, quick spell selection is the main practical setup problem. Acceptable first options:

- set a default quick spell during God Lich creation when ARPG PoC is enabled, for example a simple projectile spell;
- or use whatever `quickSpellName` existing debug/new-game setup already provides and show a status message if empty.

Do not build a full action bar for the PoC. `Q` is enough.

## Animation State

The PoC needs player animation state but not a full animation graph.

Suggested priority:

```text
Dead
Hit
Attack/Cast
Moving
Standing
```

State inputs:

- movement speed above small epsilon -> moving;
- RMB attack begins -> attack animation timer;
- Q cast begins -> attack/cast animation timer;
- hit/death optional until player damage/death presentation is wired.

Use monster action frame indices:

```text
Standing -> spriteNames[Standing]
Walking -> spriteNames[Walking]
Attack  -> spriteNames[AttackMelee] or AttackRanged
GotHit  -> spriteNames[GotHit]
Dying   -> spriteNames[Dying]
Dead    -> spriteNames[Dead]
Fidget  -> spriteNames[Fidget]
```

If the descriptor lacks a frame, fall back to standing.

## Recommended File Ownership

New files:

```text
game/arpg/ArpgPocSettings.h
game/arpg/ArpgPocPlayerController.h/.cpp
game/arpg/ArpgPocCamera.h/.cpp
game/arpg/ArpgPocTargeting.h/.cpp
```

Likely touched files:

```text
game/CMakeLists.txt
game/app/GameSettings.h
game/app/GameSettings.cpp
game/ui/screens/NewGameScreen.cpp
game/outdoor/OutdoorGameView.h
game/outdoor/OutdoorGameView.cpp
game/outdoor/OutdoorInteractionController.cpp
game/outdoor/OutdoorBillboardRenderer.cpp
game/gameplay/GameplayInputController.cpp
tests/TableRegressionTests.cpp
```

Indoor files are now expected to be touched for the indoor PoC. Keep indoor-specific work in `IndoorRenderer`,
`IndoorGameView`, and `IndoorWorldRuntime`; shared combat/spell behavior should remain in gameplay systems.

## Implementation Slices

### Slice 1: Settings And Camera

- parse/write `[arpg_poc]`;
- when enabled outdoors, camera follows party from configured angled offset;
- picking uses the same ARPG camera matrices as rendering;
- mouse cursor remains visible and mouse-look is disabled.

Acceptance:

- God Lich new game still works;
- outdoor map renders from ARPG angle;
- changing camera settings changes view after restart;
- first-person modes unchanged.

### Slice 2: Lich Billboard

- resolve configured monster descriptor;
- render player billboard at party position;
- standing/walking animation selected from current movement speed;
- debug fallback if descriptor missing.

Acceptance:

- player visible as `Lich C`/`BLich C`;
- walking changes animation;
- actor monsters still render normally.

### Slice 3: LMB Movement

- ground raycast to terrain and bmodels;
- LMB ground click sets destination;
- controller feeds desired velocity into outdoor party movement;
- stop radius setting works.

Acceptance:

- player can click around outdoor terrain;
- collision/floor remains handled by existing outdoor movement;
- LMB on UI does not move.

### Slice 4: LMB Interaction

- reuse existing hover/world-hit target priority;
- LMB on item/event/NPC activates existing interaction;
- ground move remains fallback.

Acceptance:

- can click an item or event target without duplicating event code;
- can still move by clicking empty ground.

### Slice 5: RMB Attack

- RMB hostile actor pick;
- invoke existing party attack behavior against that actor;
- attack animation timer on player billboard;
- recovery respected.

Acceptance:

- can attack and kill a nearby monster from ARPG camera;
- RMB inspect still works outside ARPG PoC mode.

### Slice 6: Q Quick Spell

- `Q` reads active character quick spell;
- target hovered hostile actor or cursor position as appropriate;
- invoke existing quick spell flow or a small targeted helper;
- play cast/attack animation.

Acceptance:

- God Lich can cast one configured quick spell from ARPG camera;
- mana/recovery/known spell validation remains shared;
- no action bar required.

### Slice 7: Indoor Camera And Controls

- render BLV with the shared ARPG camera frame;
- use ARPG sector BFS visibility instead of first-person portal clipping;
- hide indoor ceiling batches in ARPG mode;
- use LMB held movement destination and mouse-wheel zoom;
- keep shared RMB/Q attack and spell routing.

Acceptance:

- BLV maps use the isometric ARPG view when `[arpg_poc] enabled=true`;
- visible sectors are stable while the camera sits outside or above the current room;
- LMB movement works against floor/wall/object picks with indoor collision still authoritative;
- classic indoor first-person mode remains unchanged when ARPG mode is disabled.

## Testing

Unit/regression:

- settings round trip for `[arpg_poc]`;
- camera helper produces stable eye/at values for known yaw/pitch/distance;
- movement controller stops at destination and clears destination;
- missing monster descriptor falls back safely.

Runtime/headless if feasible:

- new game with `new_game_god_lich=true` produces one party member;
- ARPG PoC outdoor camera active;
- terrain click moves party toward target;
- RMB attack damages target actor;
- Q quick spell starts or reports missing quick spell without crashing.

Manual smoke:

- start new game with God Lich;
- enter outdoor map;
- verify Lich billboard visible;
- click terrain and bmodels;
- click an event/item target;
- RMB attack a hostile;
- set quick spell and press `Q`;
- tweak camera yaw/pitch/distance in settings and restart.

## Deferred Work

- refined indoor cutaway rules and indoor pathfinding-backed click movement;
- full action bar;
- flask/potion slots;
- aura reservation;
- loot labels;
- crafting currency;
- monster density profile;
- pathfinding-backed player movement;
- rotatable camera;
- orthographic camera;
- proper player-specific 3D model.

## Main Risk

The highest-risk PoC detail is not rendering the Lich. It is making render camera, mouse picking, interaction picking,
and attack/spell targeting all agree on the same ARPG camera frame. Build the shared camera-frame helper first and route
all PoC camera consumers through it.
