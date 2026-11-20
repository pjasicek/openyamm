# MM9 monster AI: types and the implementation approach

Status: design proposal, 2026-11-04. Nothing is implemented yet; the decisions at the end are the user's.

The user's request: make MM9 monsters behave as in MM9. Gather the AI types they have (flying melee, flying with
ranged, grounded melee, grounded melee + ranged, ranged only, or everyone special) and choose the implementation
approach: a base AI, extendable per monster or character by Lua, and cheap.

This document is the synthesis. The evidence is in three research records:

- [MM9 data and scripts](monster_ai/MM9_AI_DATA_AND_SCRIPTS.md): every `MONSTERS.txt` row classified, the base
  scripts as state machines, the special monsters, the placement overrides (file:line citations).
- [MM9 native engine](monster_ai/MM9_AI_NATIVE_RE.md): what `object.lto` does natively (Rizin, addresses).
- [OpenYAMM today](monster_ai/OPENYAMM_AI_CURRENT.md): our shared AI, the behaviour layer, which MM9 columns we use.

## 1. What MM9 actually has

### How MM9 is built

- **Native code** (`object.lto`) owns perception, targeting, movement, attacks and the RPG rules. Five C++ AI
  classes cover all 289 actor classes: `AIBase` (all walkers), `AISwimFly` (fliers and swimmers), `NPC`
  (townsfolk), `Lobber`, `NOEFly`. About 25 classes override a native method (gibbers, Dagrell's leap, the Dragon
  King, giants, Terrors, Fish, Ghost, Evil Sorcerer). A monster flies because of its class, not the `Fly` column.
- **Base scripts** make the combat decisions: when to chase, attack, strafe, evade, swoop, flee, call for help or
  resurrect. Every actor thinks at **10 Hz**; scripts tick inside that, so their timers have 0.1 s resolution.
  Actors away from the player are deactivated by the engine (2 100 of 2 217 placed actors are flagged for it).
- **Placements** carry as much behaviour as the table: sight and hearing distance, runaway chance, ranged type,
  wander mode, path and leash, can-be-resurrected, and a `ScriptName` override on 22 % of placed monsters.

### The type matrix (135 monster rows; the other 148 rows are townsfolk, named people, guards and animals)

| Movement \ attacks | Melee only | Melee + ranged | Melee + spells | Melee + ranged + spells | Special | Total |
| --- | --- | --- | --- | --- | --- | --- |
| Walker | 37 | 51 | 10 | 3 | 1 (Yanmir) | 102 |
| Flier, own flying loop | 6 | 0 | 6 | 3 | 0 | 15 |
| Flier on the walker loop (beholders, ghosts) | 2 | 0 | 1 | 3 | 0 | 6 |
| Stationary | 0 | 0 | 3 (Evil Sorcerers) | 0 | 4 (Lobbers, Magic Mine, Dragon King) | 7 |
| Swimmer | 5 | 0 | 0 | 0 | 0 | 5 |

So, to the user's list:

- **There is no ranged-only or caster-only mobile monster.** Every mobile monster melees. Shooting and casting are
  an add-on over a melee fighter that chases; a "caster" is a monster whose ranged attack is a spell.
- **"Ranged only" exists only as a behaviour choice**, not a monster type: the *ranged holder* (Range Type 2) never
  chases and shoots or casts from where it stands. The Evil Sorcerers default to it; 33 placed actors are switched
  to it by their placement.
- **Not everyone is special.** 77 % of monster rows run a pure base with only their own numbers, 19 % add one small
  flag or hook, 4 % are unique (Dragon King, Yanmir, the two Lobbers, the unplaced Magic Mine, arguably the
  Banshee's melee window).

### The archetypes (behaviour loops)

| Archetype | MM9 source | What it does | Who |
| --- | --- | --- | --- |
| **Crawler** | `BaseCrawl.inc` | Chases timing its run to arrive as the attack is ready; attacks; switches to an attacker by chance (70 %, 45 % when in range); gives up after 30 s without combat; taunts on a kill. | wolves, mummies, Nagates, Magreebs; the core of every walker |
| **Skirmisher** | `BaseMelee.inc` | Crawler plus strafe attacks, evades after a swing, back-off taunts, speed matching. | most humanoids and monsters (the default) |
| **Ranged holder** | `Range.inc` Type 2 | Stays put; shot or cast check every 0.2-0.4 s; melees what reaches it, follows it at most 3 × melee range. | Evil Sorcerers, summoners, 33 placed actors |
| **Air flier** | `BaseFly.inc` | Strafing passes; backs off upward for 1 s; swoops in at 30-50°; never flees. | Birds, Ickies, Dragonflies, Winged Mutants, Banshees |
| **Swimmer** | `BaseSwim.inc` | Crawler that never chases a target out of the water and disengages from one on land. | Jellyspores, Sea Monsters |
| **Turret** | `lobber.scr` | Rooted; scans by turning; shoots; launches pods on a cooldown. | Lobbers; the Dragon King is a turret boss |
| **Civilian** | `NPCBase.inc`, animals, `PoliceMan.inc` | Wander and chat; flee and call for help; guards answer help and turn on the party after 3 hits. | 86 townsfolk rows, animals, Town Guards |

Two **add-ons** apply across archetypes, decided by data:

- **Walker ranged (Type 1)**: chase, and outside melee range take a shot or cast every 1-2.5 s, weighted by a
  clear-shot test; within range, 5 s after the last shot, shoot instead of chasing.
- **Flier ranged**: a shot every 0.3-1.3 s (40 % skipped, 2 s apart), never mid-swoop; a shot replaces a swoop after a
  back-off.

And shared **layers** every archetype uses: wander and marker patrols with a leash; flee, cower and hide; alerts
and help calls; the resurrection chain (resurrecters raise fallen allies); doors; hate and enrage triggers.

### What distinguishes monsters inside an archetype

- **Table numbers:** walk, run and fly speed, lunge speed, attack reach, recovery, strafe and evade chances, the
  wince columns, alert radius, resurrecter, the attacks and spells (which decide whether the ranged add-on fires and
  what). Note the swapped names: the `AttackReach` column is the distance at which the AI decides to attack, and
  `AttackRange` × scale is the actual melee sweep length.
- **Placement settings:** sight distance (default 1 320) and hearing distance (360), both doubled after first
  contact; runaway chance; ranged type; wander mode, path and leash; can-be-resurrected; death and damage triggers.
- **Columns MM9's monster AI never reads:** `Fly`, `Move`, `Target Pref`, `ConcatAttk`, `Hostility Group`,
  `Special`, `SpellUse%2`, the first `Projectile2`. We should not invent behaviour from them.

### What is genuinely per-monster

- **Bosses:** the Dragon King (distance bands for wing buffet, breath and fire bolt; target switching; timed Winged
  Mutant reinforcements; fly-in trigger), Yanmir (an invulnerable set piece hunting Ice Lobbercicles, kicking doors),
  Njam (invulnerable cameo, vanishes at a random HP), Ebora (invulnerable taunting in the bath, escapes when her
  concubines die), the summoners' rituals. 13 placements plus a few spawned bosses.
- **Small family hooks**, all expressible as data: the Lobber's pod launch (a summon on cooldown), the Banshee's
  melee window, the Icky's hanging start (dormant until disturbed), the Greater Demon's spawn-in, the Lesser Demon's
  death spawn, the Dagrell's missing speed throttle, the Lobber Pod's always-evade, the Magreeb's quest-key hook.
- **Encounter patterns on placements** (22 %): dormant until a trigger (135), marker patrols and flocks (82),
  friendly until provoked (75), set pieces (42), summoners (10), cliff jumpers (6). Reusable, not per monster.

## 2. Recommendation: native archetypes, data flags, Lua for bosses

Three tiers, cheapest first. Each monster gets exactly what it needs and no more.

### Tier 1: native archetypes in the shared AI

`GameplayActorAiSystem` gets the MM9 archetypes as native loops beside the MM8 one: crawler, skirmisher, ranged
holder, air flier, swimmer, turret, civilian/guard, with the two ranged add-ons and the shared layers. An actor's
archetype and parameters come from data (an `mm9_ai` profile generated per `MONSTERS.txt` row, overridable per
placement). MM6-MM8 monsters keep today's MM8 AI: they never carry a profile, so their path does not change.

Why native:

- **Cost.** Profile branches are a few compares and a seeded roll: well under 0.1 µs per active actor per step,
  where an active MM8 monster costs 7-18 µs today, almost all of it world-side (line of sight, path planning,
  collision). The MM9 outdoor maps place 1 600+ monsters; nothing per-frame may run in Lua.
- **Determinism and saves.** The AI stays a pure function of facts (seeded rolls, no script state per frame), which
  keeps replays, turn-based mode, save/load and a later multiplayer authority simple.
- **MM9's own lesson.** MM9 put the combat loop in untyped scripts; they shipped bugs (the End Demon's HP line,
  monk hostility misspelt, a Guard init that never runs). Seven loops in typed, tested C++ are less code than its
  87 include files.
- **It is the route already proven.** The `skirmisher` modifier is exactly this: a generator reads `MONSTERS.txt`,
  a catalogue checks ranges, tactics facts carry it, AI helpers behind one flag run it.

Decision timing follows MM9: the decisions run on MM9's own timers (shot checks every 1-2.5 s, aggressive tick
0.2 s, 30 s give-up), while movement and collision keep our 128 Hz step. That gives MM9's rhythm without changing the
step.

### Tier 2: data flags for hooks and encounter patterns

Every small hook and placement pattern becomes a declared field, not code:

| Flag | Covers |
| --- | --- |
| `dormant: {until: trigger \| disturbed \| sighted, pose: hang \| lie \| underground \| hidden}` | Icky hanging, mummy awaken, coffins, rise from the ground, Yetis on a cliff, cages |
| `spawn_in: {effect, clip}` / `death_spawn: {monster, chance}` | Greater Demon spawn-in, Lesser Demon death spawn |
| `summon: {monster, count, cooldown, markers}` | Lobber pods, summoners |
| `hostility: friendly_until_provoked \| hostile_after: <event>` | monk and Dook guards, Town Guards' 3 hits |
| `patrol: {markers, order, wait, leash}` | marker patrols, flocks |
| `throttle: false`, `always_evade: true`, `invulnerable: <switch>` | Dagrell, Lobber Pod, Yanmir/Njam/Ebora |
| `ranged_type: 1 \| 2`, `sight`, `hearing`, `runaway_chance`, `can_be_resurrected` | the per-placement settings |

The MM9 converters write these from the DAT placements and `ScriptName`/`ScriptParams` into the scene's actors, the
way they already write `mm9_rude_id`. Map events trigger dormant actors (`evt.*`).

### Tier 3: Lua behaviours for bosses and set pieces

The existing behaviour runtime (`devdocs/ACTOR_SCRIPTING_INVESTIGATION.md`) stays the extension point, unchanged in
spirit: per-actor scripts that react to events (start, damage, health thresholds, timers, death) and an optional
`onThink` at 0.5 s, steering the native AI through its input facts. Lua decides *when*, native code does the work.

Used only for: Dragon King, Yanmir, Njam, Ebora, the summoner rituals, and similar set pieces (about 13 placements
plus spawned bosses). The API additions they need are small: distance-band attack choice (`self:perform` exists),
switch target, invulnerability toggle, summon at markers (exists), vanish/leave, open doors (map events).

**Why not Lua for everyone:** 1 600+ actors at even 2 calls per second each, plus state serialisation per handler,
is real cost on the big maps for behaviour that is identical across 77 % of monsters; and it would rebuild MM9's
fragility. **Why not one shared AI for everyone:** MM9's loops genuinely differ (a flier swoops, a holder never
chases, a turret never moves), and MM8's AI reproduces none of them.

## 3. Fixes needed regardless of the approach

- **Civilians and guards on BLV maps.** MM9's civilian flee, guard help and "found player" dialogue events exist
  only in the outdoor runtime, and the BLV converters do not write the civilian/guard flags. As MM9 maps move to
  BLVs these rules vanish. Move them to shared code and emit the flags.
- **Monster factions.** MM9 makes all monsters friends by default and enemies only by script (`HateAll`,
  `HateAllOthers`, the Dragon King hates all). Our relation table may leave MM9 monsters (ids 9000+) outside it; check
  in game, then give MM9 its default plus the scripted hate triggers as data.
- **Melee reach.** Every monster uses one MM8 melee distance today. MM9 has per-row attack reach and sweep length.
- **Alert radius.** One world-wide 4 096 today; MM9 is per row (alerts) and per placement (sight 1 320, hearing 360,
  doubled after contact, 180° view).
- **Wince.** Our unused `stagger` modifier fits MM9's wince (only at 20 % HP or less, 20-50 %).
- **A sleep tier for far actors.** MM9 deactivates actors away from the player. Our 48-active cap is a partial
  version; the big outdoor BLVs (1 600+ monsters) would gain from MM9's rule. Not needed for correctness.

## 4. Plan, in phases

Each phase ends with unit tests for the pure AI logic and a headless scenario on an MM9 map.

1. **Data.** Generator: an `mm9_ai` profile per row (archetype from the class and script, reach and sweep, alert
   radius, wince, resurrecter, lunge). Converters: placement fields (sight, hearing, runaway chance, ranged type,
   wander/patrol, can-be-resurrected, dormant/hostility patterns). No behaviour change yet.
2. **Walkers.** Crawler and skirmisher fidelity (arrival timing, retarget chances, 30 s give-up, taunts, per-actor
   reach), walker ranged Type 1, ranged holder Type 2. Most monsters are done here.
3. **Fliers, swimmers, turrets.** Flier passes, back-off and swoop, flier ranged; the swimmer's land rule; the
   turret's scan and pod launch.
4. **Layers.** Patrol markers and leash, flee/cower/hide, alerts and help, the resurrection chain, doors, civilians
   and guards in shared code, MM9 factions.
5. **Bosses** in Lua: Dragon King first (the finale), then Yanmir, Njam, Ebora, the summoners.

## 5. Still unknown (more RE before or during phase 2)

- `Att%`: resolved in phase 2 (the chance a monster in reach strikes rather than shoots or casts; the plan's
  "Phase 2").
- How `RangeAttack` picks projectile or spell, and what range limits a shot (phase 2 assumes `SpellUse%1`, then the
  projectile, within the sight distance less 5 LT).
- MM9's flee decision in full: only the 25 % of monsters that roll as runners at spawn flee, if they have a hiding
  place and are badly hurt (HP ≤ 2 × the largest hit taken) or cannot reach a ground attacker. The alert and help
  filters, the wake rule for deactivated actors, and the Dragon King's and Lobber's native parts are not traced.
- Which `ScriptName` wins when both a placement and its row name one.

## 6. Decisions for the user

1. **The approach**: native archetypes + data flags + Lua only for bosses (recommended), as above.
2. **MM9's quirks or its intent**: MM9's `Always Wince? = 1` actually means *never* wince; only 25 % of monsters can
   ever flee; Type 1 hiding after shots was switched off. Recommended: reproduce MM9 as it plays, and record each
   quirk.
3. **Monster infighting**: MM9 monsters are allies unless a script sets hate. Recommended: MM9's default.
4. **MM6-MM8 opt-in**: the archetypes are generic (a flier that swoops would suit MM8's gargoyles). Recommended:
   MM9 only for now; an opt-in per monster for other worlds later, by data, never by default.
5. **Sleep tier for far actors** on the big MM9 BLVs: recommended later, as a performance item.
