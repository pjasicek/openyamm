#pragma once

#include "game/tables/Mm9MonsterAi.h"

#include <cstdint>

namespace OpenYAMM::Game
{
// MM9's walker rules (devdocs/mm9_rework/MM9_MONSTER_AI_PLAN.md phase 2) as pure functions: the crawler loop of
// BaseCrawl.inc, Range.inc's shots, BaseRun.inc's flight and the native perception, wince and ShouldRunAway of
// object.lto (monster_ai/MM9_AI_DATA_AND_SCRIPTS.md section 3, monster_ai/MM9_AI_NATIVE_RE.md). Times are seconds,
// distances ours (MM9's LithTech units x 2.56). The AI (GameplayActorAiSystem) and both world runtimes use them.

// BaseCrawl.inc: a taunt on noticing a target (AWARE_CHANCE), the chase limit without an attack (MAX_CHASE_TIME), the
// native TargetLostTime and once-a-second target search, the RunTo arrival (0.95 of the attack range), the band a
// moving target must leave during an attack (0.70) and the stop of a waiting actor near a still target (0.75).
inline constexpr float Mm9AwareChance = 0.40f;
inline constexpr float Mm9MaxChaseSeconds = 30.0f;
inline constexpr float Mm9TargetLostSeconds = 8.0f;
inline constexpr float Mm9TargetSearchSeconds = 1.0f;
inline constexpr float Mm9RunToRangeShare = 0.95f;
inline constexpr float Mm9RunAfterRangeShare = 0.70f;
inline constexpr float Mm9StopRangeShare = 0.75f;
// The kill taunt (OnTargetDead: KilledTargetTaunt 0.5 s after it killed its target).
inline constexpr float Mm9KillTauntDelaySeconds = 0.5f;
// Range.inc: no pursuit within the range attack range once this long passed since its last shot with a clear shot;
// before a shot a walker (type 1) stops only when its target is less than this much running away; a holder (type 2)
// follows a target it struck in melee out to this many times its attack range.
inline constexpr float Mm9MaxRangeAttackIntervalSeconds = 5.0f;
inline constexpr float Mm9ShotStopSeconds = 1.0f;
inline constexpr float Mm9HolderFollowRangeMultiple = 3.0f;
// BaseRun.inc: a flight lasts at most 15 s and ends beyond 1 000 LT of its attacker; no new flight within 30 s of the
// last unless feared (BaseCrawl.inc MIN_RUN_AWAY_AGAIN_TIME).
inline constexpr float Mm9RunAwayMaxSeconds = 15.0f;
inline constexpr float Mm9RunAwayDistance = 2560.0f;
inline constexpr float Mm9RunAwayAgainSeconds = 30.0f;

// BaseFly.inc and FlyRange.inc (MM9_MONSTER_AI_PLAN.md phase 3): a flier backs off for 1 s rising 0.6 for each unit it
// moves away (level from a flying target), swoops 1 s at 30-50 degrees off the line to its target, passes its target
// 45 degrees off the line, at 0.8 of its speed (at most 200 LT a second) past a still one. FlyRange checks a shot
// every 0.3-1.3 s, at least 2 s after its last, and a flier shooting closer than 1.1 s of flight stops for it.
inline constexpr float Mm9FlyBackOffSeconds = 1.0f;
inline constexpr float Mm9FlyBackOffRise = 0.6f;
inline constexpr float Mm9FlySwoopSeconds = 1.0f;
inline constexpr float Mm9FlyPassAngleDegrees = 45.0f;
inline constexpr float Mm9FlyStillPassSpeedShare = 0.8f;
inline constexpr float Mm9FlyMaxPassSpeed = 200.0f * 2.56f;
inline constexpr float Mm9FlyMinShotIntervalSeconds = 2.0f;
inline constexpr float Mm9FlyShotStopSeconds = 1.1f;
// Banshee.scr: a shorter, lower back-off (0.6 s, rising 0.2) and no swoop.
inline constexpr float Mm9BansheeBackOffSeconds = 0.6f;
inline constexpr float Mm9BansheeBackOffRise = 0.2f;
// lobber.scr: an idle scan turns 20-120 degrees every 5-15 s (at 180 degrees a second); a target found starts the
// Aware clip (the Lobbers' lasts 1.5 s) and the attack check 1 s after it, then every second; at most five pods live
// at once (the native CanLob, Lobber 0x1002a160).
inline constexpr float Mm9TurretScanTurnRadiansPerSecond = 3.14159265358979f;
inline constexpr float Mm9TurretAwareSeconds = 1.5f;
inline constexpr float Mm9TurretAttackCheckSeconds = 1.0f;
inline constexpr int Mm9TurretMaxPods = 5;

// MM9's recovery (MM9_AI_NATIVE_RE.md section 7.2.1): `Recovery` game seconds of 33 ms of real time (the importer
// converts it), counted from the end of the attack clip for blows and shots alike, without a random factor; a cast
// recovers by its spell's own recovery from the cast. The cooldown an attack starts with, from its start: the clip and
// the recovery, or for a cast the time to its cast key (impactSeconds into the clip) and the spell's recovery.
float mm9AttackStartCooldown(bool cast, float clipSeconds, float impactSeconds, float recoverySeconds);

// The cooldown left when a wince cuts an attack (death and a wince are the only interruptions). Cut before its hit or
// cast, or after a missed blow (armedAtHit false), none: it can act once the wince ends. After a blow that connected or
// a released shot, hit time + recovery: the start's cooldown less the clip that was left at the hit
// (actionLeftAtHit). After a cast, the cast's recovery, already the start's cooldown.
float mm9CutAttackCooldown(bool armedAtHit, bool cast, float cooldownLeft, float actionLeftAtHit);

// RecoveryTimeLeft as MM9's scripts read it (GetStat: the game seconds left x 0.1, not x 0.033): 3.03 times the real
// time left. ShouldRunAfter compares that with the travel time, so the monster arrives late (quirk reproduced).
inline constexpr float Mm9ScriptRecoveryScale = 0.1f / 0.033f;
float mm9ScriptRecoveryTimeLeft(float realSecondsLeft);

// The archetypes on the walker loop (BaseCrawl.inc): crawler, skirmisher, ranged holder, swimmer (BaseSwim.inc is
// BaseCrawl.inc with its land rule) and guard (PoliceMan.inc is BaseMelee.inc with its police rules).
bool mm9WalkerArchetype(Mm9AiArchetype archetype);

// The archetypes that run an MM9 loop (MM9_MONSTER_AI_PLAN.md phases 2-5): the walkers (guards among them:
// PoliceMan.inc is BaseMelee.inc), the fliers, the turrets (the Dragon King among them: a turret boss whose Lua
// behaviour picks its targets and attacks, phase 5), and the townsfolk (phase 4b).
bool mm9LoopArchetype(const Mm9AiProfile &profile);

// GetRandomInt a, b is inclusive: a script's "GetRandomInt 0, 100 < n" passes n times in 101.
float mm9ScriptChance(int below);

// A value in [0, 1) from an actor, a counter and a salt (an integer hash): MM9's GetRandom, seeded.
float mm9Unit(uint32_t actorId, uint32_t counter, uint32_t salt);

// NewTargetCheck (BaseCrawl.inc:890-995): the chance (0-1) that a damaged monster switches from its target to its
// attacker. 70 %, or 45 % while its target is in its attack range; halved when the attacker is farther than the
// target, else times 1.15. MM9 doubles the target's distance before the second test, so every attacker that is not
// farther gets the 1.15 (quirk reproduced).
float mm9RetargetChance(bool targetInAttackRange, float targetDistance, float attackerDistance);

// ShouldRunAfter (BaseCrawl.inc:324-351): it runs after its target only when its attack is ready, or its recovery
// ends before it would arrive (the edge distance at its run speed).
bool mm9ShouldRunAfter(bool attackReady, float recoveryLeftSeconds, float edgeDistance, float runSpeed);

// Range.inc's shot check interval: 1.0-2.5 s for a walker (type 1), 0.2-0.4 s for a holder (type 2); unit in [0, 1).
float mm9ShotCheckSeconds(bool holder, float unit);

// What EstimateRangeAttackHit finds first on the line to the target.
enum class Mm9ShotLine : uint8_t
{
    Target,   // the target: always shoots
    Clear,    // nothing: 20 %
    Object,   // another object: 15 %
    Blocked,  // another AI or the world: never
};

// Range.inc's chance (0-1) to shoot at a check (RANGE.inc:151-224).
float mm9ShotChance(Mm9ShotLine line);

// The range a walker shoots or casts within: min(the projectile's range, SightDistance - 5 LT) at its placement;
// OpenYAMM has no per-projectile range, so the projectile side is the engine's ranged reach.
float mm9RangeAttackRange(float sight, float projectileRange);

// The spell a RangeAttack casts (MM9_AI_NATIVE_RE.md section 7.2.2): 1 or 2, or 0 for a shot. The chances are the
// monster row's sequential ones in percent (0 for a spell it cannot cast now): spell 1 by its chance, else spell 2 by
// its own. One roll in [0, 1) makes both, the part above spell 1's chance rescaled for spell 2. The MM9 generator
// writes the chances from MM9's two rolls (a spell by 100 - Att%, then spell 1 by SpellUse%1), so this is MM9's choice.
int mm9RangedSpellSlot(int spell1Chance, int spell2Chance, float roll);

// Whether a placed monster is a runner: MM9 rolls RunawayChance once when it reads the placement (0x1000d462); seeded
// by the actor.
bool mm9IsRunner(uint32_t actorId, float runawayChance);

struct Mm9RunAwayInput
{
    bool feared = false;
    bool runner = false;
    bool hasHidingPlace = false;
    int currentHp = 0;
    int largestHit = 0;
    bool hasRangedAttack = false;
    bool targetReachable = true;
    bool targetFlies = false;
    // Since its last flight began (a large value when it never fled).
    float sinceLastFleeSeconds = 1000.0f;
};

// ShouldRunAway (native 0x1001a1a0 with BaseCrawl.inc's 30 s hold): Fear always; else not again within 30 s of the
// last flight; else only a runner with a hiding place that is badly hurt (HP at most twice its largest hit) or, with
// no ranged attack, cannot reach a target that does not fly.
bool mm9ShouldRunAway(const Mm9RunAwayInput &input);

// The native wince roll at a hit (0x10019e00): never for `Always Wince? = 1` (wince Never, the column reads as its
// opposite); else 0 while its health is above 20 % and 20-50 % (unit picks it) at or below.
float mm9WinceChance(Mm9AiWince wince, int currentHp, int maxHp, float unit);

struct Mm9PerceptionInput
{
    // Centre to centre, and whether the line to it is clear (neither sight nor hearing goes through walls).
    float distance = 0.0f;
    bool lineOfSight = false;
    // It is in the front half-space (a 180 degree view; hearing needs none).
    bool inFront = false;
    float sight = 0.0f;
    float hearing = 0.0f;
    // It has targeted the party before: both ranges doubled (BaseCrawl.inc SetupTarget).
    bool doubled = false;
};

// Perceive (0x1000d890): heard within its hearing distance, or seen within its sight distance in front of it, always
// with a clear line.
bool mm9Perceives(const Mm9PerceptionInput &input);

// How far its senses reach: the farther of its sight and hearing, doubled once it has targeted the party.
float mm9PerceptionRange(float sight, float hearing, bool doubled);

// The distance within which the world considers the party for an MM9 monster (outdoors the world's engagement range,
// indoors the activation range): the shared range, raised to its perception range, at most maximumRange.
float mm9SenseRange(float sharedRange, float perceptionRange, float maximumRange);

// world.yml actorAwareness mm9Sight and mm9Provoke (MM9_MONSTER_AI_PLAN.md "Awareness of the party"): OpenYAMM's
// departures from MM9's perception of the party, chosen by the user. The defaults are MM9's own rules.
struct Mm9PartyAwareness
{
    // It sees the party all round, not only in front (hearing is unchanged).
    bool sightAllRound = false;
    // Its placement's sight times this.
    float sightScale = 1.0f;
    // Its sight before contact goes no farther than this (0: no limit). MM9: 4275, its 3800 engagement range and
    // 12.5 % more, as MM6-MM8's outdoor full-AI range (5632) passes their yellow alert (5120).
    float sightMax = 0.0f;
    // A party hit from at most this far provokes it: it holds the party as far as this, wherever the party is, until
    // it loses it. A party hit from farther makes it take no target. 0: MM9's rule (every hit is a reason to take
    // the attacker, which it keeps only within its doubled sight).
    // A provoking hit provokes too its awake friends within provokeRadius that it sees, so a friend beside it comes
    // even without perceiving the party (IndoorWorldRuntime::provokeMm9Actors).
    float provokeRange = 0.0f;
    // The provoked friends' distance from it, centre to centre (0: its own alert radius, Mm9AiProfile::alertRadius).
    // A map's scene actor_detection provoke_radius wins over both.
    float provokeRadius = 0.0f;
};

// The placement as its senses find the party: sight scaled, at most sightMax. A dormant start keeps MM9's senses.
Mm9AiPlacement mm9PartySenses(const Mm9AiPlacement &placement, const Mm9PartyAwareness &awareness, bool dormant);

// Whether the party counts as in front of it: always with all-round sight, unless it is dormant.
bool mm9PartyInView(bool inFront, const Mm9PartyAwareness &awareness, bool dormant);

// Whether a party hit from this distance provokes it, and whether one is too far to make it take any target.
bool mm9PartyHitProvokes(const Mm9PartyAwareness &awareness, float hitDistance);
bool mm9PartyHitTooFar(const Mm9PartyAwareness &awareness, float hitDistance);

// How far it keeps the party it holds: its sight, doubled after contact, or the provoke range while provoked.
float mm9HeldPartyRange(float sight, bool doubled, bool provoked, const Mm9PartyAwareness &awareness);

// Its eye's height (AIBase GetEyePos 0x10003280: the centre plus half the height less 2 LT): the top of its body less
// eyeBelowTop. Sight lines run from there to the target's centre (MM9_AI_NATIVE_RE.md section 5.1).
float mm9EyeZ(float footZ, float height, float eyeBelowTop);

// The edge distance from which an MM9 monster's melee reaches its target, as OpenYAMM measures edges (only the
// monster's radius is taken off its distance to the party): MM9's attack range is edge to edge (both radii), so the
// party's radius is added back.
float mm9MeleeReach(float attackReach, bool targetIsActor, float partyRadius);

// The melee hit sweep (0x1000f3d0): the blow lands on a target within its own radius, the sweep and the target's radius
// of its centre as the blow lands. MM9's lunge key carries a monster whose sweep is shorter than its attack range into
// reach during the swing; OpenYAMM has no lunge impulse, so the sweep is at least the attack range (a target that
// stepped out of the attack range during the wind-up is missed).
bool mm9MeleeSweepReaches(float meleeSweep, float attackReach, float attackerRadius, float targetRadius,
    float centerDistance);

// A flier's style: BaseFly.inc's, or Banshee.scr's (the profile's melee window marks a Banshee: banshee.scr is the only
// script with one) with its lower, shorter back-off and no swoop.
struct Mm9FlierStyle
{
    float backOffSeconds = Mm9FlyBackOffSeconds;
    float backOffRise = Mm9FlyBackOffRise;
    bool swoops = true;
};

Mm9FlierStyle mm9FlierStyle(const Mm9AiProfile &profile);

// A flier hit by someone switches to it by OnDamageDone's roll (GetRandomInt 0, 100 < 50: 50 in 101), whoever it is.
float mm9FlierRetargetChance();

// FlyRange.inc's check: 0.3-1.3 s apart (unit in [0, 1)); it shoots unless GetRandomInt 0, 100 < 40 (61 in 101), and
// only with its attack ready, at least 2 s after its last shot and a clear shot.
float mm9FlyShotCheckSeconds(float unit);
float mm9FlyShotChance();

// A back-off: per unit of its speed, the horizontal share and the rise (Strafe normalises (away, rise)); level from a
// flying target.
void mm9FlyBackOffShares(float rise, bool targetFlies, float &horizontalShare, float &verticalShare);

// The swoop's turn off the line to the target: GetRandomInt 30, 50 degrees, to the side GetRandomInt 0, 1 picks
// (units in [0, 1)); radians, signed.
float mm9SwoopAngleRadians(float angleUnit, float sideUnit);

// A pass's speed share of its flight speed: full past a moving target, 0.8 (at most 200 LT a second) past a still one.
float mm9FlyPassSpeedShare(bool targetMoving, float flySpeed);

// lobber.scr's idle scan: the wait before the next turn (5-15 s) and the turn (20-120 degrees to a side), radians.
float mm9TurretScanSeconds(float unit);
float mm9TurretScanTurnRadians(float angleUnit, float sideUnit);

// lobber.scr's AttackCheck: a pod when it can lob (CanLob: its attack ready and fewer than five pods alive; the
// script's own 5-10 s wait never runs, MM9 quirk reproduced), else a shot within its range attack range, taken without
// a clear shot only when GetRandomInt 0, 100 is not below 75 (26 in 101).
bool mm9TurretCanLob(bool attackReady, int livePods);
float mm9TurretShotChance(bool clearShot);

// BaseSwim.inc: a swimmer runs from any target that is not in water (whether it is in water itself); AISwimFly targets
// only what is in water while it is in water itself.
bool mm9SwimmerRunsFrom(bool targetInWater);
bool mm9SwimmerCanTarget(bool selfInWater, bool targetInWater);

// The layers every MM9 archetype shares (MM9_MONSTER_AI_PLAN.md phase 4a): BaseWander.inc, BaseRun.inc, AICommon.inc's
// alerts, help calls and resurrection chain, and BaseDoor.inc.

// BaseWander.inc: wandering starts a second after the monster appears (BaseWanderInit, Mm9WanderStartupDelaySeconds),
// a marker is reached within 1 LT of its edge (WalkTo range 1).
inline constexpr float Mm9WanderMarkerRange = 2.56f;
// BaseRun.inc: a runner's tick every 0.3-0.8 s (the first after 0.5 s), a hiding place re-run (and a help call) every
// 1.5 s, a cower checked every 5 s; MIN_RUNAWAY_DIST (1 000 LT) ends a run without a hiding place.
inline constexpr float Mm9RunAwayFirstTickSeconds = 0.5f;
inline constexpr float Mm9HideTickSeconds = 1.5f;
inline constexpr float Mm9CowerTickSeconds = 5.0f;
// AICommon.inc: a corpse asks a resurrecter within 1 000 LT every 5 s; the resurrecter starts 3-6 s later; a lone
// resurrecter raises itself 2-10 s after its second ask finds no one; a raise waits (every 0.5 s) until no actor
// stands within twice its radius; a resurrecter busy attacking or wincing tries again 0.1 s later.
inline constexpr float Mm9ResurrectAskSeconds = 5.0f;
inline constexpr float Mm9ResurrectDistance = 2560.0f;
inline constexpr float Mm9RaiseRetrySeconds = 0.5f;
inline constexpr float Mm9ResurrectDelayRetrySeconds = 0.1f;
// BaseDoor.inc: a walker opens a closed AI-triggerable door it runs into within 45 degrees of facing it.
inline constexpr float Mm9DoorFacingDegrees = 45.0f;

// The wait before a wander walk: GetRandomFloat over the placement's WanderWaitMin-Max (a zero bound is 0.01); below
// 0.2 s it starts at once (BaseWanderStart). Also the walk's length over WanderTimeMin-Max.
float mm9WanderSeconds(float minimum, float maximum, float unit);

// BaseWanderPickRandomDir: the turn of an aimless walk, 15-180 degrees (15-90 after an obstacle) to the side
// GetRandomInt FALSE, TRUE picks; radians, signed.
float mm9WanderTurnRadians(bool afterObstacle, float angleUnit, float sideUnit);

// BaseWanderLeashCheck: beyond its leash (0: none) from where wandering started, measured level (MM9 levels the
// height).
bool mm9BeyondLeash(float deltaX, float deltaY, float leash);

// The marker a path walks to next (BaseWanderGetNextMarker): in turn; random: the other of two, else any other
// (GetRandomInt 0, count - 1 until it differs), unit in [0, 1). The first marker is marker 0 in turn, and in random
// order the next from 0 (BaseWanderGetFirstMarker).
int mm9NextPathMarker(int current, int count, bool random, float unit);
int mm9FirstPathMarker(int count, bool random, float unit);

// NewTargetCheck (BaseCrawl.inc:890-995) for a walker offered a new target by a hit, an alert or a help call.
enum class Mm9NewTargetOutcome : uint8_t
{
    Invalid,  // itself, its own target, a friend, a dead one, or it is fleeing, cowering or resurrecting
    Take,     // it has no target: it takes this one
    Roll,     // it rolls mm9RetargetChance to switch
};

struct Mm9NewTargetInput
{
    bool hasTarget = false;
    bool candidateIsTarget = false;
    bool candidateValid = true;
    bool fleeing = false;
    bool resurrecting = false;
};

Mm9NewTargetOutcome mm9NewTargetCheck(const Mm9NewTargetInput &input);

// AlertTick waits g_nRandom, the last random number the script drew, whatever it was (MM9 quirk reproduced): the
// interval of the next alert, 0 when none follows (a wait of 0 cancels).
float mm9AlertRepeatSeconds(float scriptRandom);

// Help's radius: ten times the sender's half height.
float mm9HelpRadius(float height);

// BaseRunAway: a monster with a Cower clip cowers in place instead of running 10 times in 101.
float mm9CowerChance();

// BaseRunAwayFace: the turn off the line away from its attacker, 15-45 degrees. Its side is GetRandomFloat 0, 1 == 1,
// which a float never meets (MM9 quirk reproduced): always the same side, radians.
float mm9RunAwayTurnRadians(float unit);

// BaseRunAwayTick's interval: 0.3-0.8 s.
float mm9RunAwayTickSeconds(float unit);

// ResurrectMe: the resurrecter starts 3-6 s later; a lone resurrecter raises itself 2-10 s after its last ask.
float mm9ResurrectDelaySeconds(float unit);
float mm9SelfRaiseDelaySeconds(float unit);

// CanResurrectNow: no actor within twice its radius.
bool mm9CanRaiseNow(float nearestActorDistance, float radius);

// BD_OnDoor: it opens a door it runs into only heading within 45 degrees into it (its facing against the door's
// normal turned around).
bool mm9DoorAhead(float facingX, float facingY, float doorNormalX, float doorNormalY);

// Townsfolk and guards, dormant starts and spawn-ins (MM9_MONSTER_AI_PLAN.md phase 4b): NPCBase.inc, PoliceMan.inc,
// FlyingIcky.scr, MummyAwaken.scr, GreaterDemon.scr and LesserDemon.scr.

// NPCBase.inc BaseRunFindHidingPlace: without a hiding place of its own a fleeing townsperson looks for town guards
// (GetObjects GuardBase) within 1 600 LT, five at most, and runs to one of those farther than 500 LT from its attacker.
// NPCBaseInit sets MIN_RUNAWAY_DIST to 1 200 LT ("100 feet").
inline constexpr float Mm9GuardSearchRadius = 1600.0f * 2.56f;
inline constexpr size_t Mm9GuardSearchCount = 5;
inline constexpr float Mm9GuardAttackerMinDistance = 500.0f * 2.56f;
inline constexpr float Mm9CivilianRunAwayDistance = 1200.0f * 2.56f;
// PoliceMan.inc MAX_PLAYER_HIT_TOLERATION: the party's third hit makes a guard its enemy.
inline constexpr int Mm9GuardPartyHitTolerance = 3;
// FlyingIcky.scr IckyLaunch: it drops (MoveDir down at 100 LT/s) while its Launch clip plays.
inline constexpr float Mm9LaunchDropSpeed = 100.0f * 2.56f;
// GreaterDemon.scr: a spawn-in starts invisible, plays its client effect 0.1 s later and its Spawn clip, visible, 1 s
// after that.
inline constexpr float Mm9SpawnInHiddenSeconds = 1.1f;

// The guard a townsperson runs to among count candidates: GetRandomInt 0, count - 1 (unit in [0, 1)).
int mm9PickRefuge(int count, float unit);

// NPCBase.inc OnDamage and OnProjectile: a townsperson whose target is the party (it runs from it, or talks to it)
// ignores the hit (MM9 quirk reproduced: so does a hit by a monster then); else it runs from its new attacker.
bool mm9CivilianRunsFromHit(bool heldTargetIsParty);

// PoliceMan.inc for a call a guard receives: PoliceAlert ignores an alert a monster (IsMonster) sends, and makes the
// target a fellow guard alerts it to its enemy when it was a friend; OnHelp makes the target a friend calls for help
// about its enemy when it was a friend (the party: AddEnemy Player). Then the base's OnAlert / OnHelp run.
struct Mm9PoliceCallInput
{
    bool help = false;
    bool senderIsMonster = false;
    bool senderIsGuard = false;
    bool targetIsFriend = false;
};

struct Mm9PoliceCallResult
{
    bool ignored = false;
    bool targetBecomesEnemy = false;
};

Mm9PoliceCallResult mm9PoliceCall(const Mm9PoliceCallInput &input);

// PoliceMan.inc OnDamage: the party's hits on a guard counted; at the third the party becomes its enemy (before it, a
// hit by a friend is no reason to fight: NewTargetCheck's IsAttackerValidTarget).
bool mm9GuardTurnsOnParty(int partyHits);

// What may wake a dormant start.
enum class Mm9DormantEvent : uint8_t
{
    Hit,
    Alert,
    Help,
    Sighted,
    Trigger,
};

// Whether the event wakes a dormant start: a trigger always; a hit too (MummyAwaken.scr OnDamage WakeUp, and the
// engine's rule for a resting actor); disturbed (FlyingIcky.scr Sleep) also an alert, a help call or a target it
// notices, a hanging one only while it plays its fidget (MM9 quirk reproduced: FlyingIcky.scr registers OnFoundTarget
// only in Fidget); sighted (Jumper.inc) a target it notices. KlusosSleeper.scr wakes only on damage or its link.
bool mm9DormantWakes(Mm9AiDormantUntil until, Mm9AiDormantPose pose, Mm9DormantEvent event, bool fidgeting);

// FlyingIcky.scr FidgetSetup: the next hanging fidget 2-10 s later (unit in [0, 1)).
float mm9HangFidgetWaitSeconds(float unit);

// AIBase::SetAnimState: entering idle arms the fidget 5-12 s later (unit in [0, 1); MM9_AMBIENT_ANIMATION.md 2.1).
float mm9IdleFidgetWaitSeconds(float unit);

// SetState(fidget, -1): one of count fidget clips, uniformly (unit in [0, 1); 0 for a count of 0 or 1).
int mm9FidgetVariant(float unit, size_t count);

// NPCBase.inc's chats (MM9_AMBIENT_ANIMATION.md section 2.3), units in [0, 1). SetupNextChat: the next search
// GetRandomInt 5, 15 s later; LookForPersonOn: a search window of GetRandomInt 5, 10 s; GoChat: the walk to the one
// who accepted gives up after GetRandomFloat 4, 10 s; OnChatArrival: the chat lasts GetRandomInt 10, 30 s; LeaveChat:
// a turn of 180 degrees plus GetRandomFloat -45, 45 (radians).
float mm9SocializeWaitSeconds(float unit);
float mm9ChatSearchSeconds(float unit);
float mm9ChatApproachSeconds(float unit);
float mm9ChatLengthSeconds(float unit);
float mm9ChatLeaveTurnRadians(float unit);

// OnHello's wait for the one it accepted to arrive (OnChatGiveUp), and how often the native search runs.
inline constexpr float Mm9ChatListenGiveUpSeconds = 20.0f;
inline constexpr float Mm9ChatSearchIntervalSeconds = 1.0f;
// FaceObject and FaceDir at 180 degrees a second (OnChatBegin, LeaveChat), in radians.
inline constexpr float Mm9ChatTurnRadiansPerSecond = 3.14159265f;

// BaseWanderStartup: only a townsperson wandering aimlessly without a leash looks for someone to talk to (one on a
// path, with a leash or not wandering only answers).
bool mm9Socializes(const Mm9AiPlacement &placement, size_t pathPointCount);

// Turns in a chat (OnConverseDone, YourTurn): the one who asked speaks first, then they alternate; each plays one Conv
// clip and hands over when it ends. It may start a clip when neither plays one and it is its turn.
bool mm9ChatTurnIsMine(bool initiator, uint16_t turns, uint16_t partnerTurns);

// How long a dormant start's wake holds it before its base runs: a hanging one drops for its Launch clip
// (FlyingIcky.scr IckyLaunch); a lying one (a coffin's mummy, a sleeper) gets up with its Wakeup clip, which
// MummyAwaken.scr never plays (MM9 snaps to the stand; MM9_ANIMATION_AUDIT.md P3); 0 without such a clip.
float mm9WakeHoldSeconds(Mm9AiDormantPose pose, float launchSeconds, float wakeupSeconds);

// Whether a dormant start in this pose wakes with its Wakeup clip (mm9WakeHoldSeconds).
bool mm9WakesWithWakeup(Mm9AiDormantPose pose);
}
