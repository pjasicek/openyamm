# MM9 water: swimming and diving in OpenYAMM (design)

How to bring MM9's deep water into the engine as a **shared, opt-in feature**, following the user's decision of
2026-10-30 ([PLAN.md](PLAN.md), Water and diving: diving and swimming as a new shared engine feature; swimmers move in
water, not on the floor). The MM9 behaviour it reproduces, with addresses, is in
[MM9_WATER_SWIMMING_RE.md](MM9_WATER_SWIMMING_RE.md). Implemented for indoor maps on 2026-11-02 (phases 1, 2, the
breath meter of 3 and the MM9 monster rules of 4): see **Status** below; the sections after it are the design as agreed,
with the user's decisions resolved to MM9's behaviour.

## Status (2026-11-02)

The user's decisions ("the same way as MM9"): walkers in deep water sink and walk the bed (1); drowning as MM9, 1/6 of
maximum HP every 2 s after 15 s (2); a thin breath bar above the basebar drawn with the HUD's solid quads, no new art
(3); tint at 0.6 of MM9's light scale (4); breath runtime only, full after a load (5); no outdoor ODM swimming (6):
every MM9 outdoor map is now built as a BLV with one open-air sector, so the indoor feature covers them.

**Implemented** (user summary in [INDOOR_OPEN_SKY.md](../INDOOR_OPEN_SKY.md) "Swimming"):

- Data: scene `water_volumes` (§1; `mover` is `mover_door_id`, the scene door's id, whose first vertex the tops follow;
  no `damage` key yet), `IndoorMapData::waterVolumes`, parsed in `IndoorSceneYml.cpp` (`parseWaterVolumesNode`, an
  overlay's block replaces the base's), emitted by the editor (`EditorDocument.cpp`).
- Pure module `game/indoor/IndoorWater.h/.cpp`: `indoorWaterAt`, `indoorBodyWaterSample`, `indoorWaterVolumeColumn`,
  `indoorWaterTopOffsets` (mover-bound tops from the controller's runtime vertices), the state table
  `indoorSwimState`, `indoorSwimVelocity`, `indoorSurfaceJumpAirControl`, breath (`advanceIndoorBreath`) and the MM9
  constants.
- Party (`IndoorPartyRuntime::stepInWater`, `updateWaterBreath`): the states of §2 plus **Bed** (feet on a floor, eye
  under: MM9's WalkingInWater comes before UnderWater, so the party walks the bed; Jump or Fly Up rises off it, as
  MM9's land jump hands over to UnderWater at once). Swimming steps use `resolveMove`'s walking branch with gravity 0
  and the step's 3D velocity (not the flying branch): floors catch a sinking body (it lands on the bed), ceilings stop
  a rising one. Current added in water; no fall damage landing in water; ladders taken from the water. Input from
  `IndoorRenderer` (`setSwimInput`: forward/back, strafe, Jump or Fly Up, Fly Down, yaw, pitch); the `update` signature
  is unchanged.
- Breath 15 s, ticks every 2 s of 1/6 maximum HP per member through `Party::applyDamageToMember` (unconscious members
  keep taking it, as MM9's tick hits every slot), "You are drowning!", `drown01/02.wav`; HUD bar
  (`GameplayUiRenderer`, `IGameplayWorldRuntime::partyBreathFraction`).
- Screen and sound: the multiplicative tint `mix(1, tint, 0.6)` (`IndoorRenderer::renderWaterTint`, a full-screen
  quad after the world's effects); a volume's fog replaces the frame fog (a map with no fog of its own loads the fog
  programs with a fog too far to show); `watersplash.wav`, `out_water.wav` and the `player/unwater2.wav` loop
  (imported from `SOUNDS/PLAYER/UNWATER2.wav` into `worlds/mm9/audio/player/`).
- Combat: bows, crossbows and thrown weapons swing in melee with the eye under water (`choosePartyAttackMode`).
- Android: the flight arrows show while swimming (`partySwimming`, `mobileFlightControlsAvailable`).
- Monsters: the MM9 generator writes `S` (`YS` for the flying Spores) in the Fly cell of MM9's AISwimFly rows
  (Jellyspore A-C, Sea Monster Male/Female, Fish: `SWIMMER_SOURCES` in `generate_mm9_monster_tables.py`;
  `MonsterStatsEntry::swims`). On a map with volumes such a monster that starts in a volume flies in it, bound to it: a
  move whose centre leaves the footprint is refused, its centre kept between bed and surface; its placement keeps its
  height. Walkers in water: half speed, the liquid's gravity 512, sinking at most 102 u/s (MM9 damps per update; ours
  uses the party's idle sink), walking the bed; no planner change (they path along beds as along any floor).
- Scenarios: `assert: {water: {...}}` and `movement_segment` `jump`/`fly_up`/`fly_down` (`tests/scenarios/README.md`).

**Deviations** beyond §2's: surface jump on a fresh Jump press (MM9 reads the held key, so holding Jump while rising
pops out at once); a grounded body with the eye out always wades (MM9 keeps its surface mover over a shallow floor and
lets its collision lift the body); the swimmer binding refuses the whole step (no slide along the edge).

**Done 2026-11-04** (user: Obsidian breath art, underside): the breath meter is a small Carved Obsidian plate
(`GameplayUiRenderer.cpp` `renderBreathMeter`: the frame pieces round the reading surface, "Breath", a brass-rimmed
track filling water blue, amber at a third, coral when it is out), above the status line's slot so "You are drowning!"
never covers it. The surface from below (`fs_indoor_water.sc`, a floor liquid face with the camera under its plane): no
planar reflection; the world above shows through, clearest within Snell's window (about 49 degrees round the vertical,
brighter straight up and rippling) and about 40 % outside it, where the surface partly mirrors the water body (MM9's
surface sprite is evenly see-through). With the eye under water the indoor renderer draws every liquid after the open
sky (`IndoorRenderer`, `WaterSurfaceSet::All` in the see-through pass), so the opaque deep sea shows the sky and cliffs
too. Strength and colour are unmatched against MM9 (RE doc, measurement 4).

**Swimmers bound, 2026-11-04** (user-approved): the Jellyspore family, Sea Monster Male/Female and Fish models follow a
swimmer rule (`floor_fix.py --swim`, `floor_audit.py` kind `swimmer`): the living clips keep MM9's motion and carry
MM9's origin at the centre of the MM9 body box (half the descriptor height: Spores +0.6656 m, Sea Monster +0.896 m,
Fish +0.4096 m), since the engine draws a model's y = 0 at the actor's feet and keeps the box centre in the water, and
MM9 centres its Dims on the object; Death eases into the corpse on the floor, which then sinks to the bed. Converters
place a swimmer's box centre at MM9's position, under the surface and over the seabed (`mm9r_common/outdoor_blv.py`
`swimmer_foot`). Combat line of sight ignores the non-solid horizontal faces of a map with water volumes (the water
surface; `indoorSegmentBlockedByCombatFace`): a swimmer held at the surface, its aim point over the water, attacked
nothing across it before (the Sea Monster circled a floating party). Project READMEs: `mm9_jelly_claude`,
`mm9_seamon_claude`, `mm9_fish_claude`; Isle of Ashes BLV README "Swimmers".

**Open**: `damage` volumes and the radial current (phase 5); Water Walk on a volume (MM9's
WalkingOnWater); the other indoor maps (§8); MM9's field-of-view wobble and model warble (skipped by design).

## Principles

- **Opt-in per map.** A map swims only if its scene lists `water_volumes`. With the list empty (every MM6–MM8 map, and
  every MM9 map until it is converted again) no new code runs: the party, monsters, rendering and saves behave exactly
  as today. The MM6–MM8 model stays as it is: drowning on outdoor water tiles without Water Walk, `MonsterKind::Swimmer`
  on the surface, the map-wide `underwater` flag.
- **One water model, both world kinds.** A volume set and a swim step shared by indoor and outdoor; only the
  geometry queries (floor, collision, sector) differ, as for flying and ladders.
- **MM9's numbers by default**, converted × 2.56, as named constants next to the code, not a new configuration layer.
  The few places where MM9's literal behaviour would play badly here are listed as deviations.
- **No new abstraction beyond what water needs**: a volume list, a query, a party state, a breath timer.

## 1. Data: water volumes

### Scene block (BLV `*.scene.yml`, later ODM scenes)

```yaml
water_volumes:
  - id: BlueWater0                 # the DAT object's name
    liquid: water                  # water | lava (MM9 codes 1-3 → water, 5 → lava; 4/6 unused in MM9)
    pieces:                        # vertical prisms: a horizontal footprint and its z range (native units)
      - polygon: [[-983, -5079], [2949, -5079], [2949, -3277], [-983, -3277]]
        bottom: -819.2
        top: -453.1                # the water surface at this piece
    fog: {color_rgb: [0, 0, 0], near_distance: 1280, far_distance: 5120}   # optional: only MM9 FogEnable 1 (Dook's lake)
    tint: [0.0, 0.5, 0.7]          # optional; default from `liquid` (MM9's light scale per code)
    current: [0, 0, 0]             # optional, units per second (MM9 Current × 2.56, axes swapped)
    damage: {per_second: 0, type: fire}      # optional; scripts may switch it (DP2waterdamage.scr)
    mover: WaterTrapTop            # optional: the door whose offset moves `top` (DrainWater.scr volumes)
```

- **Pieces** are vertical prisms because every MM9 water brush has a horizontal top: 6-poly boxes are one piece; the
  larger brushes (Bathhouse's 46-poly `BlueWater0`, Isle of Ashes' 720-poly sea) become one piece per up-facing top
  polygon, extruded down to the brush's lowest point under it. A point is in the volume when it is inside a piece's
  polygon and between its `bottom` and `top`. The volume does not collide; walls and beds are the map's own faces.
- **Moving water**: with `mover`, a piece's `top` (and, for a draining volume, nothing else) follows that door's
  current offset. Verhoffin's `WaterTrap` and Bathhouse's `BlueWater2` already move their top face as a `slide` mover;
  the volume binds to it, so the drowning trap becomes real water instead of a scripted damage loop.
- **Damage** reuses the existing face/area damage: a volume with `damage` deals it to bodies inside once per second
  (MM9's cadence), and the map's Lua can switch it (`evt` call to set a volume's damage, used by Bathhouse's boiling
  pools). Verhoffin's electrified pit keeps its separate `ElectricDamager1` damage as today.
- **Runtime**: `IndoorMapData::waterVolumes` (and the outdoor equivalent), parsed in `IndoorSceneYml.cpp` beside
  `ladders`, saved by the editor's scene emitter (`EditorDocument.cpp`) like ladders. Each piece keeps a precomputed
  AABB; maps have 1–13 volumes, so a linear scan with AABB rejection is enough (no spatial index).

### The shared query

```cpp
struct WaterSample { const WaterVolume *pVolume; float surfaceZ; };
std::optional<WaterSample> waterAt(const WaterVolumeSet &set, float x, float y, float z);   // point
bool bodyTouchesWater(const WaterVolumeSet &set, float x, float y, float footZ, float height); // body column
```

Pure functions over map data plus the movers' current offsets: unit-testable without a map.

### The converter (`level_generation/projects/mm9r_common/dungeon/`)

- A small `water.py`: for each DAT object of a liquid class (`BlueWater`, `DirtyWater`, `ClearWater`,
  `CorrosiveFluid`, `Kato`, `LiquidNitrogen`; `Hidden 0`), its world model's polygons → pieces in the native frame
  (`Project.native`), `FogEnable 1` → `fog` (`FogNearZ`/`FogFarZ` × 2.56, `FogNearZ` < 0 → 0), `Current` →
  `current` (LT vector to native, × 2.56; only when its length exceeds 1 LT/s, MM9's threshold), `ScriptName
  DrainWater.scr` → `mover` (the slide mover the map already makes), `DP2waterdamage.scr` → `damage` switched by Lua.
  The radial `CurrentPower`/`CurrentRadius`/`CurrentSource` is carried only where a map needs it (Dark Passageway's
  tube: `current_pull: {toward: [x, y, z], power, radius}`; a phase 5 item).
- **Opt-in** by `overrides.yml` `map: {swim: true}`. Without it the converter does what it does today.
- **Surfaces**: with `swim: true` the volume's top faces are built **non-solid** (no wading floor: the `WADING`
  switches of the map converters go off) and **two-sided** so they are seen from below. They keep their liquid
  texture names from `liquids.py` (`lqw115mm9`, the see-through `lq…o…` names, the maps' own oceans); the
  `depth: shallow` flag stays on those entries (it only means "terrain cells of this liquid never drown", which is
  irrelevant to faces). Where the shared helper today keeps an over-water face opaque because "nothing would show
  through" (sealed or unbuilt beds: Dook's Castle's lake, Training Hall's pole room), the bed must be built and the face
  becomes see-through like the others.
- **What swimming removes** in a map that opts in: the wading floors at the water's height, the dive pads and their
  `evt.MoveToMap` stand-ins for MM9's swims, the invisible "climb out" ledges (Verhoffin's `PIT_STEP`) where MM9 swims
  out, the event pads that open chests lying on beds (the chest becomes an ordinary chest), and the scripted drowning
  in Verhoffin's water trap. The beds and the walls down to them must exist (several maps dropped faces "with no air"
  under sealed water: the voxel pass has to treat volume air as air).
- `audit.py`'s walkability gets one rule: water volume air counts as reachable for the party (it swims), and a step
  out of water onto a rim counts as a step if it is at most the surface jump's reach (below).

## 2. The party in water

### States

The state is derived each movement step from geometry, as MM9 derives it each frame, plus two remembered bits:

| State | When | Movement |
| --- | --- | --- |
| **Dry / wading** | eye out of water, feet on a floor (body may be in water) | today's walking (MM9: wading is walking; `wade_speed` stays available for shallow faces but MM9 maps use 1) |
| **Falling into water** | body in water, airborne, eye never under since entering | today's fall (gravity), until the eye goes under |
| **Submerged** | eye point under the surface | gravity off; velocity set each step from input (no momentum) |
| **Surface** | eye out, body in, and it was submerged | gravity off; no vertical drift; held at the surface |
| **Surface jump** | Jump pressed on the surface | a jump from the surface with gravity and air control, until landing or going under again |

The eye point is the eye minus 25 units (MM9 tests 10 LT below the top of the body; our eye is the top).

### Movement numbers (MM9 → ours)

| | MM9 | Ours | Note |
| --- | --- | --- | --- |
| swim speed (forward, back, strafe, up, down) | 150 LT/s | **384 u/s** | = our walk speed; running does not change it |
| idle sink (no input, submerged) | 40 LT/s | **102 u/s** | MM9's liquid gravity −200 × 0.2 |
| forward under water | along the look direction incl. pitch | same | the eye's pitch already exists indoors and outdoors |
| up / down | Jump / Crouch, world vertical | Jump or Fly Up / Fly Down | |
| surface | forward and strafe with the upward part removed | same | looking down while moving forward dives |
| surface jump | 275 LT/s up, gravity on | **704 u/s** up, our party gravity 1280 | the feet rise about 190 units: from the surface pose they clear rims up to about 55 units above the water |
| surface jump air control | 150 LT/s forward, 75 back and strafe | 384 / 192 u/s | |
| current | summed `Current` of the volumes touched | same, u/s, added to the velocity | |
| speed buffs | MM9 doubles swim and walk alike under its timed effect | the party's movement multipliers (settings, ruleset slow, Fleet Foot/MAW) apply to swimming as to walking | |

**Deviations**: the input directions are summed and the result is clamped to the swim speed (MM9 adds them
unnormalised, up to 1.7 × with forward + strafe + up). The surface pose is held explicitly (eye point 1 unit above
the surface) instead of hovering where MM9's test flips, which avoids a per-frame flicker between Submerged and Surface.

### Where it lives

- A shared, pure **swim step** in `game/movement/` (or beside `IndoorMovers.cpp`'s ladder step): input (wish
  direction from yaw and pitch, Jump / Fly Up / Fly Down held, run), the water samples at feet and eye point, the
  remembered bits → the state, the velocity for this step, and whether gravity applies. No collision inside it.
- **Indoor**: `IndoorPartyRuntime::update` calls it before `resolveMove`, like `stepOnLadder`. It returns a 3D velocity;
  `resolveMove` takes it through its existing flying branch (`flyingActive` true, vertical velocity from the step,
  gravity 0), exactly as ladders do, so collision, sectors, portals and actor contacts are unchanged. `update` gains
  the pitch (or the already-rotated 3D wish velocity) from `IndoorGameView`; today it receives only the horizontal
  velocity. The surface hold sets `footZ` from the surface before the move.
- **Outdoor** (phase 6): `OutdoorMovementDriver` calls the same step, `OutdoorMovementController`'s flying path takes the
  velocity. The terrain-water drowning (`waterDamageTicks`) is skipped where a volume covers the point.
- **Entering and leaving**: walking down a slope into deep water, falling in, or stepping off a rim are all just the
  derived state changing; leaving is walking out at a shallow edge, a ramp, the surface jump onto a low rim, or a
  ladder.
- **Ladders out of water**: a ladder's grab rule (`indoorLadderGrabAllowed`) also accepts a swimming party (Submerged or
  Surface), so ladders that start under the surface (Beethoven's `Ladder0`, Dook's Castle's `Ladder0`) are taken from
  the water. Climbing below the surface keeps the ladder movement; breath still counts while the eye is under.
- **Fall damage**: landing in water does not hurt (MM9 skips its landing path under water); a fall that ends with the
  body in a volume clears the fall distance.

### Controls

- **Desktop**: movement keys and mouse look as today; Jump and Fly Up swim up, Fly Down swims down (MM9's Crouch: we
  have no crouch). Jump on the surface is the surface jump. The Fly Up/Down bindings already exist (ladders use them).
- **Android**: the flight arrows show while the party is in water (Submerged or Surface), the same visibility rule as
  for the Fly buff and ladders (`touch_controls.yml` and the touch input's rule); the stick moves forward along the
  look pitch.
- **Turn-based**: a swim step is a movement step like walking; idle sinking happens in the physics steps.

## 3. Breath and drowning

- **Party state**: `Party::breathSeconds` (runtime), counting down while the eye point is under water, refilled to full
  at once when it comes out (MM9). **15 s.**
- **At zero**: every 2 s, each living member takes **1/6 of its maximum HP** (MM9's tick; not reduced by armour or
  resistances), with MM9's `drown01/02.wav` and the existing status text "You are drowning!" (outdoor already shows
  it). The damage goes through the party's ordinary damage path, so unconsciousness, death and party defeat follow the
  existing rules.
- **Water Walk** (MM6–MM8 spell; MM9 has none, but the merged spell list reaches MM9 maps): on a volume the party
  stands on the surface (MM9's own `WalkingOnWater` mover: vertical velocity never below 0 in water). No Water
  Breathing exists in MM6–MM9; nothing extends breath.
- **HUD**: a breath meter while the eye is under water, draining 100 → 0 over the 15 s. Placement and art are an
  Obsidian HUD decision (proposal: a thin bar centred just above the dynamic party basebar, in the HP meter's style,
  hidden out of water). Until the art exists, phase 1 shows the status line "Holding breath" / "You are drowning!".

## 4. Screen and sound

- **Fog and tint per volume**: while the camera is in a volume, the renderer swaps the scene's `IndoorFog` for the
  volume's `fog` (if set, else keeps the map's fog), and multiplies the frame by the volume's `tint`. MM9's light scale
  for BlueWater, (0, 0.5, 0.7), is very dark on our lighting; the converter writes it, and the tint is applied as
  `mix(1, tint, strength)` with one engine strength (start 0.6) to be matched against the user's MM9 capture
  (RE doc, measurement 4). Outdoors the existing `underwater` sky special and tint path take the same inputs from the
  volume instead of the map flag.
- **Surface from below**: the liquid shader draws a two-sided liquid face's back side as the underside: no planar
  reflection or sky response, the liquid colour at a higher opacity, a light Fresnel brightening toward the vertical.
  This is the only shader change; see-through faces (the current work) already blend over what lies behind them.
- **Skipped**: MM9's field-of-view wobble and `ModelWarble` (motion sickness, little value); an audio low-pass (the
  mixer has none; a later engine item).
- **Sounds**: `watersplash.wav` when the eye goes under, `out_water.wav` when it comes out (both already in
  `worlds/mm9/audio/events/`), MM9's `Sounds\Player\unwater2.wav` looped while under (to import from `SOUNDS.REZ`).
  These are the MM9 world's; an MM6–MM8 map that opts in later names its own.

## 5. Combat, spells, projectiles

- **Ranged weapons** (bows, crossbows, thrown, Blackpowder) are not fired while the eye is under water (MM9): the
  attack falls back to the melee path (or "can't shoot" when out of reach). Spells are allowed.
- **Projectiles** fly unchanged through water, both ways (MM9's water physics only touches actors).
- **Picking and LOS** are unaffected: volumes are not faces.
- **Items**: dropped items fall to the bed as they fall to any floor; chests and items on beds are reached by swimming.

## 6. Monsters

- **Swimmers** are actors with the existing `MonsterKind::Swimmer` on a map with volumes. They move like flyers (the
  shared AI's `canFly` path: no gravity, 3D steering) but are **bound to the volume they spawn in**: a step whose
  centre would leave the volume is refused (slide along, like a wall), and a target outside it is approached to the
  nearest point inside (the surface under a party on the shore). Their speed is MM9's FlyVelocity (Sea Monster and the
  Spores 200 LT/s = 512 u/s, Fish 77 u/s) as the MM9 rows' movement speed, and the MM9 monster table generator tags
  the Sea Monster, Spore and Fish rows `swimmer` (`generate_mm9_monster_tables.py`). They do not surface-walk (the MM8 outdoor "swimmers walk on
  water tiles" rule applies only without volumes). Placed swimmers get `Gravity 0`-like spawn: no floor snap.
- **Walkers** enter water where the water over the bed is lower than their height (they wade), slowed to × 0.5 (MM9's
  `1 − Viscosity`). Deeper water is **closed to walkers** in the planner: the indoor path builder marks floor cells
  whose water depth exceeds the actor's height as blocked for non-swimmers. MM9 lets walkers sink and walk the bed;
  ours keeping them out avoids monsters stranded on beds and endless pursuits along a seabed (a deviation; see
  decisions).
- **Flyers** ignore water (MM9).
- **Attacks**: a swimmer attacks a party in or at the edge of its water within its reach; ranged swimmers use their
  ranged attacks as usual. A walker cannot reach a submerged party it cannot path to; it waits on the shore.
- **Monsters do not drown** (MM9).

## 7. Saving and loading

No save format change. The water state is derived from the saved position and the map's volumes on load (a party saved
under water loads under water; "was submerged" is recomputed: in water with the eye out counts as Surface). Breath is
runtime only and loads full, as the ladder state is runtime only. Volume tops bound to movers come back from the saved
door states. (If the user wants breath persisted, it is one float in the party record and a save version bump.)

## 8. Per map

Indoor maps in the order to convert. "Swim" lists the volumes deep enough that the eye goes under (bed more than about
135 units below the surface); shallower volumes still emit (tint, fog, surface look) and behave as wading.

| Map | Swim | What changes |
| --- | --- | --- |
| **Verhoffin Ruins** (test case) | crevasse `BlueWater0/1` (≈ 366), pit `ElectricWater1` (≈ 328), `WaterTrap` (rises to 492) | `WADING = False`; volumes; TreasureChest0 a plain chest on the bed (its pad goes); the pit's `PIT_STEP` ledge goes (swim out); the water trap's top bound to its slide mover, the scripted drowning replaced by breath; the NW ramp stays the way out of the crevasse (its 123-unit rim is too high for the surface jump, as in MM9) |
| Dark Passageway | bridge lake (1311), tube room and tube (901–1147), ocean (1014) | wading surfaces go; the tube's downward current and pull; 6 world objects on beds; Sea Monster M/F as swimmers |
| Bathhouse | boiling pools `WaterthatBoilsA/B` (≈ 1400–1550), `BlueWater2` (824, drains) | the six dives go; burn damage switched by the valve's Lua; `BlueWater2` bound to its mover |
| Dook's Castle | the lake (1556), fog 500–2000 black | wading face goes; the bed is built; chest 6 plain; Ladder0 from the water |
| Beethoven | `GrandEntrance Water` (942) | the solid surface goes; the shaft walls back to MM9's −830; swim under them to the corridors; Ladder0 from the water |
| Dungeon of Secrets | pool room (696) | the sink-in `evt.MoveToMap` goes; MM9's lower route around the double axe becomes the swim |
| Inventa Storca | cavern and well (819–983) | the fall-to-shore move goes; swim down `BlueWater2` and up the well; the bone piles on the bed |
| Training Hall | pole room (430) | the solid surface goes; the sealed bed is built |
| 1000 Terrors | `BlueWater0–6` (300–410, three with fog) | the sea monster pool; the 13 weighted lifts and 3 doors under water become reachable (puzzle check) |
| Thjorad Mine, Lich Lab | `DirtyWater1` (655, fog), four 246-unit pools | small; volumes only |
| Yanmir's Fort | marginal (bed at most 159 units: the eye dips under only at the deepest spot) | volume for the tint and fog (MM9 has fog on); otherwise wading as now |

Outdoor (phase 6): Isle of Ashes, Sturmford, Thronheim, Thjorgard (rivers with current), Guberland, Yorwick, Drangheim,
Frosgard City; Dook's Castle's and Inventa Storca's outdoor oceans if those maps have them.

## 9. Outdoor

The plan's approach holds: the heightmap keeps the seabed (already saved, `work/seabed_heights.npy` on Isle of
Ashes), each water body is a volume with its surface level, and the map is raised by the water's depth where needed.
The engine work beyond the indoor feature: water tiles under a volume draw their surface at the volume's `top`
instead of the terrain height (the terrain water pass gets a per-body height); the outdoor controller uses the swim
step; the terrain-water drowning and the MM8 swimmers' surface rule are off inside volumes; the `underwater` sky
special takes its trigger from the camera's volume. The outdoor ODM scene needs a `water_volumes` block (or a per-map
sidecar if the ODM has no scene file). This is the largest and riskiest part; do it after the indoor maps prove the
model.

## 10. Phasing, effort, risks, tests

| Phase | Work | Effort (agent days) |
| --- | --- | --- |
| 1 | Engine core indoor: volume data and parsing, `waterAt`, swim step, `IndoorPartyRuntime` integration (pitch input, flying branch, surface hold, surface jump), breath and drowning ticks, status text, fog/tint swap, splash/out/loop sounds, Android arrow rule, ladders from water | 3–4 |
| 2 | Converter `water.py`, `swim: true`, non-solid two-sided surfaces, audit rule; **Verhoffin Ruins** converted, scenarios, desktop visual check | 1–1.5 |
| 3 | Underside liquid shader path; breath meter HUD (after the art decision) | 2–3 (+ art) |
| 4 | Swimmers bound to volumes, walker depth rule in the planner, water speed for walkers; Dark Passageway's sea monsters as the test | 2–3 |
| 5 | The other indoor maps (table above), currents and moving volumes where used | 0.5–1 per map |
| 6 | Outdoor (terrain surface height per body, outdoor controller, raised maps) | 8–12 |

**Risks**

- **MM6–MM8 regressions**: every new path is behind `waterVolumes.empty()`; the MM8 movement and actor scenarios are
  the guard. The `IndoorPartyRuntime::update` signature change (pitch) touches the game view and headless drivers.
- **Collision in the flying branch** has only been used by ladders indoors (short vertical moves). Long 3D swims through
  portals and down shafts may expose sector lookups (the floor-portal flag issue the ladders hit). Test in Verhoffin's
  crevasse and Dark Passageway's tube.
- **Dropped faces under water**: the converters dropped faces "with no air" below sealed water; a swim reveals holes.
  The voxel pass must treat volume air as air and maps need a geometry pass.
- **Baked lighting**: non-solid, see-through surfaces change the bake (light reaches the beds); rebake each converted map.
- **Performance**: a few AABB tests per party step and per swimmer step; nothing for maps without volumes.

**Tests**

- doctest: `waterAt` (inside, outside, at the top, a moved top, two pieces); the swim step's state table (dry → falling
  → submerged → surface → surface jump → landing; the idle sink of 102 u/s; forward with pitch; the surface removes the
  upward part; clamping); breath (15 s, then a tick every 2 s, 1/6 maximum HP, instant refill); swimmer volume binding.
- Headless scenarios (`tests/scenarios/`, MM9 review root): Verhoffin: walk off the rim, sink, swim to TreasureChest0
  and open it, surface, leave by the ramp; stay under 30 s and check the drowning ticks; the water trap floods and the
  party drowns unless it drains; a save under water reloads under water with full breath. Dark Passageway: a sea monster
  stays in its water while the party walks the shore.
- Regression: the existing MM6–MM8 scenarios and unit tests unchanged.

## Decisions for the user

1. **Walkers in deep water**: keep them out (proposed) or let them sink and walk the bed as MM9 does.
2. **Drowning damage**: MM9's 1/6 of maximum HP every 2 s after 15 s (proposed), or something gentler.
3. **Breath meter**: placement and art for the Obsidian HUD (proposal: a thin bar above the basebar).
4. **Tint strength**: start at 0.6 of MM9's light scale and match it to a real-game capture (RE doc, measurement 4).
5. **Breath across save/load**: runtime only (proposed, loads full) or persisted.
6. **Outdoor**: whether phase 6 is wanted now or after all indoor maps.
