#pragma once

#include "game/gameplay/ActorTurretScan.h"
#include "game/gameplay/GameplayRuntimeInterfaces.h"
#include "game/party/SkillData.h"
#include "game/tables/Mm9MonsterAi.h"
#include "game/tables/MonsterModifiers.h"

#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
enum class ActorAiTargetKind : uint8_t
{
    None = 0,
    Party = 1,
    Actor = 2,
};

enum class ActorAiMotionState : uint8_t
{
    Standing = 0,
    Wandering = 1,
    Pursuing = 2,
    Fleeing = 3,
    Stunned = 4,
    Attacking = 5,
    Dying = 6,
    Dead = 7,
};

// A skirmisher's footwork (ActorTacticsFacts::skirmish, MM9's BaseMelee AI): a strafe attack runs past the target while
// it swings; afterwards it backs off from a strafe attack, or evades (backpedals, then circles the target; it only
// circles a target that moves away); a taunt holds still playing the model's taunt clip.
enum class ActorSkirmishPhase : uint8_t
{
    None = 0,
    StrafeAttack = 1,
    BackOff = 2,
    Evade = 3,
    Circle = 4,
    Taunt = 5,
};

// Whether a skirmisher's footwork backs it away from its target: a back-off, or the first half of an evade (the rule
// AI_SkirmishEvade moves by). MM9's scripts play these as the Backpedal state and the rest of the footwork as Strafe,
// so presentation reads the phase rather than the angle of the move.
inline bool skirmishBackpedals(ActorSkirmishPhase phase, float secondsLeft, float evadeSeconds)
{
    return secondsLeft > 0.0f
        && (phase == ActorSkirmishPhase::BackOff
            || (phase == ActorSkirmishPhase::Evade && secondsLeft > 0.5f * evadeSeconds));
}

// What the AI decided this step, for the decision trace (ActorAiTrace, devdocs/mm9_rework/MM9_MONSTER_AI_PLAN.md
// "The decision trace"). Set only where a decision is taken; the world ignores it unless tracing is on. New behaviours
// add their kinds at the end and a name in actorAiDecisionName (ActorAiTrace.cpp).
enum class ActorAiDecisionKind : uint8_t
{
    None = 0,
    // Idle: stands, fidgets, wanders inside its home radius, or walks back home (a post, a patrol waypoint).
    Stand,
    Fidget,
    Wander,
    ReturnHome,
    // Combat: chases (note: the pursue mode), circles a ranged target between shots, waits in reach for its attack
    // to recover, waits without a shot (no line of sight), holds in a crowd.
    Pursue,
    Orbit,
    WaitCooldown,
    WaitNoShot,
    CrowdHold,
    AttackMelee,
    AttackRanged,
    AttackSpell,
    // Flees its target (note: fear, forced or engagement), or wanders blind.
    Flee,
    BlindWander,
    // A skirmisher's footwork (ActorTacticsFacts::skirmish).
    StrafeAttack,
    Evade,
    Circle,
    BackOff,
    Taunt,
    Throttle,
    // An MM9 walker (ActorTacticsFacts::mm9Profile, MM9_MONSTER_AI_PLAN.md phase 2). Detect: it takes the target the
    // world found (chance/roll: the 40 % taunt); TauntDetect: it taunts at it; TauntKill: it taunts after killing its
    // target; Retarget: a hit makes it consider its attacker (note switch, keep or no_target); GiveUp: it drops its
    // target (note chase_time after 30 s without an attack, lost after 8 s out of sight, dead); ShotCheck: Range.inc's
    // check rolled (chance from the line to the target); PursuitVeto: Range.inc keeps it from chasing (5 s since its
    // last shot, a clear shot); FleeDecision: ShouldRunAway sent it running (note fear, hurt, unreachable); Wince: the
    // native wince roll at a hit (note yes or no); Hold: a ranged holder keeps its place; Unreachable: it cannot reach
    // its target and waits.
    Detect,
    TauntDetect,
    TauntKill,
    Retarget,
    GiveUp,
    ShotCheck,
    PursuitVeto,
    FleeDecision,
    Wince,
    Hold,
    Unreachable,
    // MM9 fliers and turrets (MM9_MONSTER_AI_PLAN.md phase 3; a flier's back-off is BackOff, note up or level, and its
    // FlyRange check ShotCheck). FlyPass: an attack pass 45 degrees past its target (note left or right); Swoop: the
    // swoop in after a back-off (note left or right); MeleeWindow: a Banshee is undead during its pass; Scan: an idle
    // turret turns; PodLaunch: a Lobber launches a pod.
    FlyPass,
    Swoop,
    MeleeWindow,
    Scan,
    PodLaunch,
    // The layers every MM9 archetype shares (MM9_MONSTER_AI_PLAN.md phase 4a). Wander (BaseWander.inc): WanderWait: it
    // waits before its next walk (seconds); the walk itself is Wander (note aimless) or Patrol (to a marker);
    // MarkerReached: it touched its marker; Leash: beyond its leash it stops (note stop) or turns home (note home).
    // Calls (AICommon.inc): SendAlert and CallHelp are sent (note: the target named); Alert and Help are received
    // (note take, switch, keep, ignored; the chance and roll of a switch). Flight (BaseRun.inc): Hide: it runs to its
    // hiding place (note run, arrived); Cower: it cowers (note start, end). Resurrection (AICommon.inc): a corpse's
    // ResurrectAsk (note asked, none, self), a resurrecter's ResurrectAccept (seconds until it starts) and Resurrect
    // (note cast, delay, gone), the corpse's Raised (note rise, wait, self). OpenDoor: it opens a door it ran into
    // (BaseDoor.inc).
    WanderWait,
    Patrol,
    MarkerReached,
    Leash,
    SendAlert,
    CallHelp,
    Alert,
    Help,
    Hide,
    Cower,
    ResurrectAsk,
    ResurrectAccept,
    Resurrect,
    Raised,
    OpenDoor,
    // Phase 4b (MM9_MONSTER_AI_PLAN.md). Wake: a dormant start wakes (note: what woke it: trigger, hit, alert, help,
    // sighted, woken by the world); SpawnIn: a spawned monster appears (note hidden, spawn, aware, begin); DeathSpawn:
    // a spawned one's corpse spawns another (the monster id as its marker); TurnHostile: a guard makes the party its
    // enemy (note hit N, help, alert) or counts a hit by its friend the party (note hit 1, hit 2).
    Wake,
    SpawnIn,
    DeathSpawn,
    TurnHostile,
    // Phase 5: an MM9 boss behaviour (ActorBehaviorRuntime, Lua). The AI carries out its directives (note target:
    // it holds the target the script named; attack: it starts the attack the script chose; not_ready: the attack was
    // dropped, its attack not ready or no target offered); the script's own decisions are traced under this name too
    // (ActorMm9ScriptFacts::traceLines).
    Script,
    // The reposition modifier (an OpenYAMM addition, ActorRepositionRules.h). Reposition: with its target unseen it
    // walks to the spot the world found (note spot, the point), back to its post (note post) or holds (note none);
    // RepositionArrived: the walk ended (note spot, post, sight: it saw its target on the way, leash, timeout);
    // BackOffRush: a target rushing it makes it backpedal to the spot (note spot) or finds no room (note blocked).
    Reposition,
    RepositionArrived,
    BackOffRush,
};

// One decision: its kind, the target it was taken against, the ability of an attack, and the chance it rolled
// against with the roll (negative: no roll). note is a static string (a mode or reason), never owned.
struct ActorAiDecision
{
    ActorAiDecisionKind kind = ActorAiDecisionKind::None;
    ActorAiTargetKind targetKind = ActorAiTargetKind::None;
    size_t targetActorIndex = static_cast<size_t>(-1);
    bool hasAbility = false;
    GameplayActorAttackAbility ability = GameplayActorAttackAbility::Attack1;
    float chance = -1.0f;
    float roll = -1.0f;
    const char *pNote = nullptr;
    // A marker of its path (negative: none) and a duration it chose (negative: none).
    int marker = -1;
    float seconds = -1.0f;
    // A spot it chose (a reposition) and the sight lines the world tested for it (negative: none).
    bool hasPoint = false;
    GameplayWorldPoint point = {};
    int checks = -1;
    // The clip variant it picked (a fidget, ActorRuntimeFacts::fidgetClips; negative: none).
    int variant = -1;
};

enum class ActorAiMovementAction : uint8_t
{
    None = 0,
    Stand = 1,
    Move = 2,
    Pursue = 3,
    Flee = 4,
    Wander = 5,
};

enum class ActorAiAttackRequestKind : uint8_t
{
    None = 0,
    PartyMelee = 1,
    ActorMelee = 2,
    RangedProjectile = 3,
    SpellProjectile = 4,
};

enum class ActorAiAudioRequestKind : uint8_t
{
    None = 0,
    Bored = 1,
    Attack = 2,
    Hit = 3,
    Death = 4,
};

enum class ActorAiFxRequestKind : uint8_t
{
    None = 0,
    Hit = 1,
    Death = 2,
    Spell = 3,
    Buff = 4,
};

struct ActorPartyFacts
{
    GameplayWorldPoint position = {};
    // Horizontal velocity (ActorPartyVelocityTracker); a skirmisher reads it (ActorTacticsFacts::skirmish).
    float velocityX = 0.0f;
    float velocityY = 0.0f;
    float collisionRadius = 0.0f;
    float collisionHeight = 0.0f;
    bool invisible = false;
    bool hasDispellableBuffs = false;
};

struct ActorIdentityFacts
{
    uint32_t actorId = 0;
    int16_t monsterId = 0;
    std::string displayName;
    uint32_t group = 0;
    uint32_t ally = 0;
    uint8_t hostilityType = 0;
    GameplayActorTargetPolicyState targetPolicy = {};
};

struct ActorStatsFacts
{
    struct AttackDamageFacts
    {
        int diceRolls = 0;
        int diceSides = 0;
        int bonus = 0;
    };

    GameplayActorAiType aiType = GameplayActorAiType::Normal;
    int monsterLevel = 0;
    int currentHp = 0;
    int maxHp = 0;
    int armorClass = 0;
    uint16_t radius = 0;
    uint16_t height = 0;
    uint16_t moveSpeed = 0;
    bool canFly = false;
    bool hasSpell1 = false;
    uint32_t spell1Id = 0;
    std::string spell1Name;
    uint32_t spell1SkillLevel = 0;
    SkillMastery spell1SkillMastery = SkillMastery::None;
    CombatDamageType spell1DamageType = CombatDamageType::Physical;
    bool spell1CastSupported = true;
    bool hasSpell2 = false;
    uint32_t spell2Id = 0;
    std::string spell2Name;
    uint32_t spell2SkillLevel = 0;
    SkillMastery spell2SkillMastery = SkillMastery::None;
    CombatDamageType spell2DamageType = CombatDamageType::Physical;
    bool spell2CastSupported = true;
    int spell1UseChance = 0;
    int spell2UseChance = 0;
    int attack2Chance = 0;
    std::string attack2MissileTypeOverride;
    AttackDamageFacts attack1Damage = {};
    AttackDamageFacts attack2Damage = {};
    CombatDamageType attack1DamageType = CombatDamageType::Physical;
    CombatDamageType attack2DamageType = CombatDamageType::Physical;
    GameplayActorAttackConstraintState attackConstraints = {};
};

// A flier's state in its loop: chasing or holding (None), passing its target in an attack, backing off, swooping in,
// or shooting (FlyRange.inc).
enum class Mm9FlightPhase : uint8_t
{
    None,
    Pass,
    BackOff,
    Swoop,
    Shot,
};

// BaseWander.inc's state: waiting for its startup (a second after it appeared), waiting before a walk, walking
// aimlessly, walking to a marker; Off when it does not wander or while it has a target.
enum class Mm9WanderPhase : uint8_t
{
    Startup,
    Waiting,
    Walking,
    ToMarker,
    Off,
};

inline constexpr float Mm9WanderStartupDelaySeconds = 1.0f;

// The reposition modifier's state (ActorRepositionRules.h): a query out to the world (a spot that sees the target, or
// room to back off), walking to a spot, walking back to its post, backpedalling from a rush.
enum class Mm9RepositionPhase : uint8_t
{
    None,
    SightQuery,
    BackOffQuery,
    Moving,
    Returning,
    BackingOff,
};

// A reposition query: the spots to test in order (the AI's, ActorRepositionRules.h), at most maxSightChecks sight
// lines; a sight query needs a spot that sees `target` (where the actor last saw its target: it does not know where
// the target went) at least minTargetDistance from it, a back-off only room.
inline constexpr size_t ActorRepositionMaxCandidates = 16;

struct ActorRepositionQuery
{
    bool needsSight = true;
    GameplayWorldPoint target = {};
    uint8_t count = 0;
    std::array<GameplayWorldPoint, ActorRepositionMaxCandidates> candidates = {};
    float minTargetDistance = 0.0f;
    uint8_t maxSightChecks = 0;
};

// BaseRun.inc: running away at an angle (a fear, or no hiding place), running to a hiding place, cowering.
enum class Mm9FleeMode : uint8_t
{
    None,
    Run,
    Hide,
    Cower,
};

// GreaterDemon.scr's spawn-in (MM9_MONSTER_AI_PLAN.md phase 4b): not decided yet (its first step), hidden (the client
// effect), playing its Spawn clip, then its Aware clip; Done once it fights (or for a monster that does not spawn in).
enum class Mm9SpawnPhase : uint8_t
{
    Unknown,
    Hidden,
    Spawn,
    Aware,
    Done,
};

// An MM9 monster's own loop state (MM9_MONSTER_AI_PLAN.md phase 2: BaseCrawl.inc's loop with Range.inc and
// BaseRun.inc's decision; phase 3: BaseFly.inc, FlyRange.inc and lobber.scr), kept by the world between AI steps
// (runtime only, not saved) and replaced whole by ActorStateUpdate::mm9 when the AI changes it. Times are seconds.
struct ActorMm9State
{
    // The target it holds: MM9 keeps a target until it gives up, loses it, sees it die or switches to an attacker.
    // The world offers this one while it can (ActorMm9WorldFacts::heldTargetGone when it cannot any more).
    ActorAiTargetKind targetKind = ActorAiTargetKind::None;
    size_t targetActorIndex = static_cast<size_t>(-1);
    // Since it set up its target or last began an attack (MM9's g_nLastAttackTime): it gives up after 30 s.
    float chaseSeconds = 0.0f;
    // Its held target unseen (MM9 loses it after 8 s, TargetLostTime).
    float unseenSeconds = 0.0f;
    // After it drops a target it takes a new one only after this (MM9 searches once a second).
    float searchDelaySeconds = 0.0f;
    // Until its next Range.inc shot check.
    float shotCheckSeconds = 0.0f;
    // Since its last shot or cast; negative until Range.inc's ShouldRunAfter first runs (g_lastRangeAttack 0).
    float sinceShotSeconds = -1.0f;
    // A flight (BaseRun.inc): the time left, and since the last one began (MM9 flees again only 30 s later).
    float fleeSeconds = 0.0f;
    float sinceFleeSeconds = 1000.0f;
    // A kill taunt waits this long (0: none pending).
    float killTauntSeconds = 0.0f;
    // Unable to reach its target, it waits and tries again when this runs out (MM9 re-checks CanReachTarget).
    float reachRetrySeconds = 0.0f;
    // The world's hit, kill and wince serials (ActorMm9WorldFacts) it has seen.
    uint32_t seenDamageSerial = 0;
    uint32_t seenKillSerial = 0;
    uint32_t seenWinceSerial = 0;
    // Counts its MM9 rolls: the seed of the next one.
    uint32_t rollCount = 0;
    // It has targeted the party once: its sight and hearing are doubled from then on.
    bool partyContact = false;
    // A ranged holder struck its target in melee: it may follow it out to 3 x its attack range.
    bool meleedTarget = false;

    // A flier's loop (BaseFly.inc, FlyRange.inc; MM9_MONSTER_AI_PLAN.md phase 3): what it is doing, the time left in a
    // back-off or swoop, the swoop's direction, the side of its pass.
    Mm9FlightPhase flightPhase = Mm9FlightPhase::None;
    float flightSeconds = 0.0f;
    float flightDirectionX = 0.0f;
    float flightDirectionY = 0.0f;
    int8_t flightSide = 1;
    // FlyRange.inc's swoop flag (g_bSwooping): set as a swoop begins, cleared only when one ends; no shot checks while
    // it is set.
    bool swooping = false;
    // FlyRange.inc's check timer runs (RangeCheckSetup): from noticing its target, a swoop's end or a shot, until it
    // has no target.
    bool shotChecksArmed = false;
    // A shot after a back-off swoops in when it is done (FlyRange.inc g_bSwoopAfterRange).
    bool swoopAfterShot = false;
    // A hit while it could not attack: it backs off at its next step (OnDamageDone).
    bool backOffRequested = false;
    // A Banshee's pass made it undead (Banshee.scr GoUndead): traced at the pass's next step.
    bool meleeWindowPending = false;

    // A turret's loop (lobber.scr): its Aware clip's time left, its idle scan (the wait before the next turn, the yaw
    // it turns to), and a pod launch whose attack is under way (the pod comes at the attack's contact time).
    float awareSeconds = 0.0f;
    float scanSeconds = 0.0f;
    bool scanArmed = false;
    bool scanTurning = false;
    float scanYawRadians = 0.0f;
    bool podLaunchPending = false;

    // The layers (MM9_MONSTER_AI_PLAN.md phase 4a). MM9's g_nRandom: the last random number its script drew, which
    // AlertTick waits (alertSeconds until the next alert; negative: none armed).
    float scriptRandom = 0.0f;
    float alertSeconds = -1.0f;
    // The world's call serial (ActorMm9WorldFacts::callSerial) it has seen.
    uint32_t seenCallSerial = 0;

    // BaseWander.inc: started (a second after it appeared), the phase and its time left (the wait, or an aimless walk),
    // the marker it walks to, whether the last walk met an obstacle (a smaller turn next).
    Mm9WanderPhase wanderPhase = Mm9WanderPhase::Startup;
    float wanderSeconds = Mm9WanderStartupDelaySeconds;
    int16_t pathMarker = 0;
    bool pathFirst = true;
    bool wanderObstacle = false;
    bool wanderHalted = false;

    // BaseRun.inc: how it flees, its tick (a run's re-aim or a hiding run's re-run), the hiding place it runs to and
    // whether the last flight began by cowering.
    Mm9FleeMode fleeMode = Mm9FleeMode::None;
    float fleeTickSeconds = 0.0f;
    float hideSearchSeconds = 0.0f;
    int8_t hidingPlace = -1;

    // The resurrection chain (AICommon.inc). A resurrecter: the corpse it will raise, the wait before it starts, the
    // ResurrectSpell clip under way (its time left; the corpse rises at its DoResurrection key).
    size_t resurrectCorpse = static_cast<size_t>(-1);
    float resurrectSeconds = 0.0f;
    float castSeconds = 0.0f;
    bool castRaised = false;
    uint32_t seenResurrectRequestSerial = 0;
    // A corpse: its death seen this session (only such a corpse asks), the target it died holding, its next ask,
    // whether it asked once (a second ask finding no one removes it, or a resurrecter raises itself), a self raise or a
    // raise under way (its Resurrect clip's time left).
    bool dyingSeen = false;
    bool corpseStarted = false;
    ActorAiTargetKind deathTargetKind = ActorAiTargetKind::None;
    size_t deathTargetActorIndex = static_cast<size_t>(-1);
    float askSeconds = -1.0f;
    bool asked = false;
    bool askAwaiting = false;
    float selfRaiseSeconds = -1.0f;
    bool raisePending = false;
    float raiseRetrySeconds = 0.0f;
    float raiseSeconds = 0.0f;
    uint32_t seenRaiseSerial = 0;

    // BaseDoor.inc: the door it opens, all its timers paused meanwhile (the door's open time).
    float doorSeconds = 0.0f;

    // Phase 4b. A townsperson's refuge (NPCBase.inc): the guard it runs to (an actor index), -1 for none.
    size_t refugeActorIndex = static_cast<size_t>(-1);
    // A guard's hits by its friend the party (PoliceMan.inc playerHitCount).
    uint8_t partyHits = 0;
    // A dormant start: it was held dormant at its last step (the world waking it shows as the hold gone), its pose's
    // time, the wait to its next hanging fidget (negative: none armed) and whether it fidgets now; the clip it plays as
    // it wakes (an Icky's Launch, dropping meanwhile).
    bool dormantHeld = false;
    float dormantSeconds = 0.0f;
    float dormantFidgetWaitSeconds = -1.0f;
    bool dormantFidgeting = false;
    float wakeSeconds = 0.0f;
    // A spawn-in (GreaterDemon.scr) and its phase's time left; a spawned one's corpse spawned its successor
    // (LesserDemon.scr OnDeathDone).
    Mm9SpawnPhase spawnPhase = Mm9SpawnPhase::Unknown;
    float spawnSeconds = 0.0f;
    bool deathSpawned = false;
    // Its attack's recovery (MM9_AI_NATIVE_RE.md section 7.2.1): the hit or cast armed it (a blow that connected, a
    // released shot, a cast), with the clip that was left at that moment; a wince that cuts the attack keeps the hit's
    // recovery, or none before it (mm9CutAttackCooldown).
    bool hitRecoveryArmed = false;
    float hitActionLeftSeconds = 0.0f;
    // Phase 5: the target it holds was named by its behaviour script (ActorMm9ScriptFacts): the world offers it
    // whatever their relation (Yanmir hunts his friends the Ice Lobbercicles).
    bool scriptTarget = false;
    // The reposition modifier (ActorTacticsFacts::reposition): its phase, the spot it walks or backs off to, the time
    // left in the phase (a query's wait, a walk's limit), the wait before its next search and back-off, the world's
    // answer serial it has seen, and the rolls of its searches.
    Mm9RepositionPhase repositionPhase = Mm9RepositionPhase::None;
    GameplayWorldPoint repositionSpot = {};
    float repositionSeconds = 0.0f;
    float repositionSearchWaitSeconds = 0.0f;
    float backOffWaitSeconds = 0.0f;
    uint32_t seenRepositionSerial = 0;
    uint32_t repositionCount = 0;
    // Where it last saw the target it holds (its target point then), and whether a walk already took it to a spot
    // that sees there (it does not search for the same place again; seeing the target again clears it).
    bool hasLastSeen = false;
    GameplayWorldPoint lastSeenTarget = {};
    bool lastSeenSearched = false;
    // Its idle (AIBase::SetAnimState and the idle think, MM9_AMBIENT_ANIMATION.md section 2.1): whether it stood idle
    // at its last step and at this one (entering idle arms the fidget), the wait to its fidget, and the fidget under
    // way: its variant (ActorRuntimeFacts::fidgetClips; negative: none) and its time left.
    bool idleLastStep = false;
    bool idleThisStep = false;
    float idleFidgetWaitSeconds = 0.0f;
    int8_t fidgetVariant = -1;
    float fidgetSeconds = 0.0f;
    // Counts its idle rolls (their own counter: the rolls above keep their sequence).
    uint32_t idleRollCount = 0;
    // The party talked to it (the native NPC use, MM9_AMBIENT_ANIMATION.md section 2.4): it turns back to the facing it
    // had (NPCBase.inc OnRUDEExit) once its AI idles again, unless it walks or fights first.
    bool talkTurnBack = false;
    float talkYawRadians = 0.0f;

    // The native NPC use: it stands idle anew (a fidget cut, its timer armed again when its AI next idles) and keeps
    // the facing it had, to turn back to after the talk (a second talk before it has turned back keeps the first).
    void beginTalk(float yawRadians)
    {
        if (!talkTurnBack)
        {
            talkTurnBack = true;
            talkYawRadians = yawRadians;
        }

        idleThisStep = false;
        fidgetVariant = -1;
        fidgetSeconds = 0.0f;
    }
};

// What the world knows about an MM9 monster on its loop that its AI cannot see by itself (runtime only; set by the
// world).
struct ActorMm9WorldFacts
{
    // Counts the hits it took; its latest attacker, how far that is from it and where it stood.
    uint32_t damageSerial = 0;
    ActorAiTargetKind attackerKind = ActorAiTargetKind::None;
    size_t attackerActorIndex = static_cast<size_t>(-1);
    float attackerDistance = 0.0f;
    GameplayWorldPoint attackerPosition = {};
    // The largest single hit it took (MM9's ShouldRunAway).
    int largestHit = 0;
    // Counts the targets it killed.
    uint32_t killSerial = 0;
    // Counts its wince rolls at a hit (only those with a chance), with the last one's chance and roll.
    uint32_t winceSerial = 0;
    float winceChance = 0.0f;
    float winceRoll = 0.0f;
    // The target it holds (ActorMm9State) is dead or gone: the world cannot offer it any more.
    bool heldTargetGone = false;
    // Its last path plan to its target did not get there (MM9's CanReachTarget false).
    bool targetUnreachable = false;
    // Water (a map with scene water volumes; phase 3's swimmers): whether it and the target it is offered are in water.
    // Without water facts a swimmer runs the crawler loop alone.
    bool waterKnown = false;
    bool inWater = false;
    bool targetInWater = false;
    // A turret's pods alive (MM9's CanLob allows five), and for a pod the actor that launched it.
    int livePods = 0;
    size_t podOwnerActorIndex = static_cast<size_t>(-1);

    // The layers (MM9_MONSTER_AI_PLAN.md phase 4a), set by the world. Bit i: its hiding place i is out of its target's
    // sight (MM9's FindHidingPlace takes only those). Computed for a runner holding a target or fleeing.
    uint8_t hidingPlacesUnseen = 0;
    // The last alert or help call a friend sent it (counted by callSerial): the target named, its distance to it as
    // the AI measures its own target's, and whether that one is a valid target for it (not a friend, alive).
    uint32_t callSerial = 0;
    bool callIsHelp = false;
    ActorAiTargetKind callTargetKind = ActorAiTargetKind::None;
    size_t callTargetActorIndex = static_cast<size_t>(-1);
    float callTargetDistance = 0.0f;
    bool callTargetValid = false;
    // Who sent it (PoliceMan.inc): a monster (IsMonster: neither a townsperson nor a guard), a fellow guard.
    bool callFromMonster = false;
    bool callFromGuard = false;
    // A resurrecter: a corpse asked it (counted by resurrectRequestSerial), and whether that one still lies dead.
    uint32_t resurrectRequestSerial = 0;
    size_t resurrectRequestCorpse = static_cast<size_t>(-1);
    bool resurrectCorpseDead = false;
    GameplayWorldPoint resurrectCorpsePosition = {};
    // A corpse: a resurrecter's DoResurrection key raised it (counted by raiseSerial); the nearest other actor's edge
    // distance (MM9's CanResurrectNow); its last ask found a resurrecter.
    uint32_t raiseSerial = 0;
    float nearestActorDistance = 1.0e9f;
    bool resurrecterFound = false;
    // A closed door it ran into that it may open (BaseDoor.inc; an AI-triggerable MM9 door), its outward normal and
    // the time it takes to open.
    bool doorAhead = false;
    uint32_t doorId = 0;
    float doorNormalX = 0.0f;
    float doorNormalY = 0.0f;
    float doorOpenSeconds = 0.0f;
    // Phase 4b. A townsperson's refuges (NPCBase.inc BaseRunFindHidingPlace), for a hit it has not seen: the town
    // guards within 1 600 LT (five at most, in the actor list's order: Mm9GuardSearchCount) farther than 500 LT from
    // its attacker, with where they stand and their radii. While it runs to one (ActorMm9State::refugeActorIndex):
    // where that one stands (refugeActorIndex: which one it is) and its radius.
    std::array<size_t, 5> refugeActorIndices = {};
    std::array<GameplayWorldPoint, 5> refugePositions = {};
    std::array<float, 5> refugeRadii = {};
    uint8_t refugeCount = 0;
    size_t refugeActorIndex = static_cast<size_t>(-1);
    GameplayWorldPoint refugePosition = {};
    float refugeRadius = 0.0f;
    // The reposition modifier: the world's answer to its last query (ActorMm9Request::reposition, counted by
    // repositionSerial): whether a spot passed, which (its floor height), and how many sight lines it tested.
    uint32_t repositionSerial = 0;
    bool repositionFound = false;
    GameplayWorldPoint repositionSpot = {};
    int repositionSightChecks = 0;
};

// What an MM9 monster asks of the world this step (MM9_MONSTER_AI_PLAN.md phase 4a).
struct ActorMm9Request
{
    // SendAlert (its friends within its alert radius) or Help (within ten times its half height) about this target.
    bool alert = false;
    bool help = false;
    ActorAiTargetKind callTargetKind = ActorAiTargetKind::None;
    size_t callTargetActorIndex = static_cast<size_t>(-1);
    // A corpse asks a resurrecter within 1 000 LT holding no target or its death target (AskForResurrection).
    bool askResurrection = false;
    // A resurrecter's DoResurrection key: the corpse rises.
    size_t raiseCorpse = static_cast<size_t>(-1);
    // A corpse rises now (its Resurrect clip starts): full health, standing.
    bool revive = false;
    // Opens this door (and the doors it opens with).
    uint32_t openDoorId = 0;
    // Phase 4b: a guard makes the party its enemy (PoliceMan.inc AddEnemy Player: hostile to it from now on); a
    // dormant start wakes.
    bool turnOnParty = false;
    bool wake = false;
    // The reposition modifier: spots for the world to test (ActorMm9WorldFacts::repositionSerial answers).
    std::optional<ActorRepositionQuery> reposition;
};

// The fidget clips an actor's model picks from (actors.yml `fidget_variants`, ActorModelManifest::BoundClips): their
// lengths, the binding's own fidget (the Bored clip) first. None: its one fidget, as long as boredAnimationSeconds.
struct ActorFidgetClips
{
    static constexpr size_t MaxVariants = 8;
    std::array<float, MaxVariants> seconds = {};
    uint8_t count = 0;
};

struct ActorRuntimeFacts
{
    ActorAiMotionState motionState = ActorAiMotionState::Standing;
    ActorAiAnimationState animationState = ActorAiAnimationState::Standing;
    GameplayActorAttackAbility queuedAttackAbility = GameplayActorAttackAbility::Attack1;
    float animationTimeTicks = 0.0f;
    // A party hit's hitstop (GameplayActorHitFeedback) holds the animation clock still; action timing still runs.
    bool hitstopActive = false;
    float recoverySeconds = 0.0f;
    float attackAnimationSeconds = 0.0f;
    float meleeAttackAnimationSeconds = 0.0f;
    float rangedAttackAnimationSeconds = 0.0f;
    // Time from the start of the attack to the moment it applies (resolveActorAttackTiming: its sprite's contact frame
    // or its model clip's key); 0 applies the attack when the action ends, as MM8 does.
    float meleeAttackImpactSeconds = 0.0f;
    float rangedAttackImpactSeconds = 0.0f;
    // A spell's action and cast (the ranged attack's sprite, the model's cast clip); 0 action: the ranged attack's.
    float spellAttackAnimationSeconds = 0.0f;
    float spellAttackImpactSeconds = 0.0f;
    // Delay of the attack sound after the attack starts (sprite_attack_timing.yml); 0 plays it as the attack starts.
    float meleeAttackSoundDelaySeconds = 0.0f;
    float rangedAttackSoundDelaySeconds = 0.0f;
    float boredAnimationSeconds = 2.0f;
    ActorFidgetClips fidgetClips;
    float attackCooldownSeconds = 0.0f;
    float idleDecisionSeconds = 0.0f;
    float actionSeconds = 0.0f;
    float crowdSideLockRemainingSeconds = 0.0f;
    float crowdNoProgressSeconds = 0.0f;
    float crowdLastEdgeDistance = 0.0f;
    float crowdRetreatRemainingSeconds = 0.0f;
    float crowdStandRemainingSeconds = 0.0f;
    float crowdProbeEdgeDistance = 0.0f;
    float crowdProbeElapsedSeconds = 0.0f;
    float yawRadians = 0.0f;
    uint32_t idleDecisionCount = 0;
    uint32_t pursueDecisionCount = 0;
    uint32_t attackDecisionCount = 0;
    uint8_t crowdEscapeAttempts = 0;
    int8_t crowdSideSign = 0;
    bool attackImpactTriggered = false;
    // A skirmisher's footwork (ActorTacticsFacts::skirmish): the phase, the time left in it and the side it circles to.
    ActorSkirmishPhase skirmishPhase = ActorSkirmishPhase::None;
    float skirmishSeconds = 0.0f;
    int8_t skirmishSide = 1;
    // An MM9 monster's loop (ActorTacticsFacts::mm9Profile); unused by every other actor.
    ActorMm9State mm9;
};

// Action time left when an attack applies at its contact time (seconds from the attack's start); 0 applies it when
// the action ends. The action lasts the attack sprite's animation (startAttack: at least 0.1 s).
// A telegraphed attack (MonsterModifierSet::telegraphedAttack): the hit comes telegraphSeconds into the attack and the
// action runs on afterwards as long as it did after the sprite's contact frame (at least a fifth of a second).
inline void applyAttackTelegraph(float telegraphSeconds, float &attackAnimationSeconds, float &impactSeconds)
{
    if (telegraphSeconds <= 0.0f)
    {
        return;
    }

    const float originalImpact = impactSeconds > 0.0f ? impactSeconds : attackAnimationSeconds;
    const float followThrough = std::max(0.2f, attackAnimationSeconds - originalImpact);
    impactSeconds = telegraphSeconds;
    attackAnimationSeconds = telegraphSeconds + followThrough;
}

// The waypoint a patrol (MapDeltaActor::patrolPoints) heads for from (x, y): the current one, or the next once the
// actor is within arrival of it; index keeps its place in the round.
inline GameplayWorldPoint nextPatrolWaypoint(
    const std::vector<std::array<int32_t, 3>> &points, size_t &index, float x, float y)
{
    constexpr float PatrolArrivalRadius = 96.0f;
    index %= points.size();

    if (std::hypot(float(points[index][0]) - x, float(points[index][1]) - y) <= PatrolArrivalRadius)
    {
        index = (index + 1) % points.size();
    }

    return {float(points[index][0]), float(points[index][1]), float(points[index][2])};
}

inline float actorAttackImpactLeadSeconds(float attackAnimationSeconds, float impactSeconds)
{
    const float actionSeconds = std::max(0.1f, attackAnimationSeconds);
    return impactSeconds > 0.0f && impactSeconds < actionSeconds ? actionSeconds - impactSeconds : 0.0f;
}

// An attack's timing: how long its action lasts and when in it the attack applies (the blow lands, the missile leaves,
// the spell is cast; 0: as the action ends).
struct ActorAttackTiming
{
    float actionSeconds = 0.0f;
    float impactSeconds = 0.0f;
};

// The timing of an attack from its sprite (the native action's length and its authored contact frame, 0 without one:
// rendering/sprite_attack_timing.yml) and from the actor's 3D model clip (the clip's length, 0 unknown, and its impact
// key, negative without one: actors.yml animation.events), in any world (devdocs/mm9_rework/MM9_ANIMATION_AUDIT.md P1):
// an authored contact frame wins; without one the clip's key applies the attack, within the sprite's action. A model
// whose clips are its monster's native timing (clipsTimeAttacks: MM9's models, whose rows carry stand-in sprites)
// lasts its clip and applies at its key, as MM9 plays an attack (MM9_AI_NATIVE_RE.md section 7.3).
inline ActorAttackTiming resolveActorAttackTiming(float spriteSeconds, float spriteImpactSeconds, float clipSeconds,
    float clipImpactSeconds, bool clipsTimeAttacks)
{
    if (clipsTimeAttacks && clipSeconds > 0.0f)
    {
        return {clipSeconds, clipImpactSeconds > 0.0f && clipImpactSeconds < clipSeconds ? clipImpactSeconds : 0.0f};
    }

    if (spriteImpactSeconds > 0.0f)
    {
        return {spriteSeconds, spriteImpactSeconds};
    }

    return {spriteSeconds, std::max(clipImpactSeconds, 0.0f)};
}

// The party's horizontal velocity for the AI, estimated each frame from its position (its movement state keeps none),
// smoothed over about a tenth of a second; a jump of more than MaximumSpeed (a teleport) reads as standing.
struct ActorPartyVelocityTracker
{
    static constexpr float MaximumSpeed = 4000.0f;
    static constexpr float SmoothingSeconds = 0.1f;

    float velocityX = 0.0f;
    float velocityY = 0.0f;
    float lastX = 0.0f;
    float lastY = 0.0f;
    bool hasLast = false;

    void update(float x, float y, float deltaSeconds)
    {
        if (hasLast && deltaSeconds > 0.0f)
        {
            float rawX = (x - lastX) / deltaSeconds;
            float rawY = (y - lastY) / deltaSeconds;

            if (rawX * rawX + rawY * rawY > MaximumSpeed * MaximumSpeed)
            {
                rawX = 0.0f;
                rawY = 0.0f;
                velocityX = 0.0f;
                velocityY = 0.0f;
            }

            const float blend = 1.0f - std::exp(-deltaSeconds / SmoothingSeconds);
            velocityX += (rawX - velocityX) * blend;
            velocityY += (rawY - velocityY) * blend;
        }

        lastX = x;
        lastY = y;
        hasLast = true;
    }
};

struct ActorStatusFacts
{
    GameplayActorSpellEffectState spellEffects = {};
    bool invisible = false;
    bool dead = false;
    bool hostileToParty = false;
    bool bloodSplatSpawned = false;
    bool hasDetectedParty = false;
    bool defaultHostileToParty = false;
    bool suppressLowHealthFlee = false;
    bool forceFleeFromParty = false;
    // A flyer keeps this far above its target's height while it moves (a shield-break climb); 0: none.
    float climbAboveTarget = 0.0f;
    // Seconds since the actor's energy shield broke while it stays down (GameplayActorShields); -1 otherwise.
    float shieldDownSinceBreakSeconds = -1.0f;
};

struct ActorTargetCandidateFacts
{
    ActorAiTargetKind kind = ActorAiTargetKind::None;
    size_t actorIndex = static_cast<size_t>(-1);
    uint32_t actorId = 0;
    int16_t monsterId = 0;
    int currentHp = 0;
    GameplayActorTargetPolicyState policy = {};
    GameplayWorldPoint position = {};
    GameplayWorldPoint audioPosition = {};
    uint16_t radius = 0;
    uint16_t height = 0;
    bool unavailable = false;
    bool hasLineOfSight = false;
};

struct ActorTargetFacts
{
    ActorAiTargetKind currentKind = ActorAiTargetKind::None;
    size_t currentActorIndex = static_cast<size_t>(-1);
    int currentRelationToTarget = 0;
    int currentHp = 0;
    GameplayWorldPoint currentPosition = {};
    GameplayWorldPoint currentMovementPosition = {};
    GameplayWorldPoint currentAudioPosition = {};
    float currentDistance = 0.0f;
    float currentEdgeDistance = 0.0f;
    bool currentCanSense = false;
    bool currentHasAttackLineOfSight = true;
    bool hasCurrentMovementPosition = false;
    // An actor target's horizontal velocity (the party's is ActorPartyFacts::velocityX/Y).
    float currentVelocityX = 0.0f;
    float currentVelocityY = 0.0f;
    bool partyCanSenseActor = false;
    // How far it may shoot or cast at the party: beyond the native reach when the party hit it from farther away
    // (outdoors), 0 for the native reach.
    float partyAttackReach = 0.0f;
    std::vector<ActorTargetCandidateFacts> candidates;
};

struct ActorMovementFacts
{
    GameplayWorldPoint position = {};
    GameplayWorldPoint homePosition = {};
    float moveDirectionX = 0.0f;
    float moveDirectionY = 0.0f;
    float velocityX = 0.0f;
    float velocityY = 0.0f;
    float velocityZ = 0.0f;
    float wanderRadius = 0.0f;
    float effectiveMoveSpeed = 0.0f;
    float distanceToParty = 0.0f;
    float edgeDistanceToParty = 0.0f;
    size_t contactedActorCount = 0;
    GameplayWorldPoint contactedActorPosition = {};
    uint8_t contactedActorHostilityType = 0;
    bool hasContactedActor = false;
    bool meleePursuitActive = false;
    bool inMeleeRange = false;
    bool allowCrowdSteering = false;
    bool allowIdleWander = false;
    bool movementAllowed = false;
    bool movementBlocked = false;
    bool movementSuppressedByNavigation = false;
    // The map placed the actor `immobile` (a post) and faces it homeYawRadians. Only tactics read these
    // (ActorTacticsFacts::holdPost); spawned actors have no home facing.
    bool placedImmobile = false;
    // The placement's own leash (MapDeltaActor::leashRadius), 0 without one.
    float placedLeashRadius = 0.0f;
    // Resting (MapDeltaActor::dormant): it stands still and does not fight until hurt or woken.
    bool dormant = false;
    // The waypoint of its patrol (MapDeltaActor::patrolPoints) it walks to while it has nothing to fight.
    std::optional<GameplayWorldPoint> patrolTarget;
    bool hasHomeYaw = false;
    float homeYawRadians = 0.0f;
    // An MM9 placement's AI settings (MapDeltaActor::mm9Ai, scene mm9_ai); ActorBehaviorRuntime gives an actor with an
    // MM9 profile but no placement record MM9's defaults. The MM9 walkers read it (MM9_MONSTER_AI_PLAN.md phase 2).
    std::optional<Mm9AiPlacement> mm9Placement;
    // Its placement's marker path and hiding places (Mm9AiPlacementRecord), valid for the AI step that reads them.
    std::span<const std::array<int32_t, 3>> mm9PathPoints;
    std::span<const std::array<int32_t, 3>> mm9HidingPlaces;
    // Phase 4b: a townsperson on a stand-in row without an MM9 profile (scene mm9_civilian: the MM9 cities' people on
    // engine peasant rows) runs NPCBase.inc (mm9StandInCivilianProfile); MM9 spawned it with ScriptParams 1
    // (mm9SpawnedWithParam: its row's spawn_in and death_spawn run).
    bool mm9StandInCivilian = false;
    bool mm9Spawned = false;
};

// What an actor does when its energy shield breaks (tactics `shield_break`).
enum class ActorShieldBreakReaction : uint8_t
{
    None,
    // Flees its target (the native flee) while the shield stays down, up to ActorTacticsFacts::shieldBreakSeconds.
    FallBack,
    // Staggers: holds its hit pose, neither moving nor attacking, for shieldBreakSeconds after the break.
    Stagger,
    // Falls back as FallBack, and a flyer climbs ActorStatusFacts::climbAboveTarget above its target meanwhile (out of
    // melee reach).
    Climb,
};

// Optional combat tactics from world data (worlds/<id>/behaviors.yml `tactics`, keyed by monster id and applied by
// ActorBehaviorRuntime::applyAiFacts). The defaults leave the native AI unchanged.
struct ActorTacticsFacts
{
    // Turns toward its target at this rate (radians per second) instead of snapping to it, keeps tracking it between
    // attacks and starts an attack only within fireToleranceRadians of it. 0 keeps the native instant facing.
    float traverseRadiansPerSecond = 0.0f;
    float fireToleranceRadians = 0.0f;
    // A ranged band (edge distance to the target): commits to its ranged attack instead of the native distance roll,
    // so melee is only chosen against an adjacent target, and between shots backs off inside rangedMinDistance, closes
    // in beyond rangedMaxDistance and circles the target in between. A maximum of 0 keeps the native choice.
    float rangedMinDistance = 0.0f;
    float rangedMaxDistance = 0.0f;
    // A post: an actor placed `immobile` that may still leave its spot to fight, at most postLeashRadius from home
    // (0: unlimited), and with no target walks back and faces its placement direction instead of wandering.
    bool holdPost = false;
    float postLeashRadius = 0.0f;
    // A stationary turret's idle scan (ActorTurretScan.h) and the hold of its last aim after losing a target; needs a
    // traverse rate. Disabled by default.
    TurretScanSettings scan;
    // Aims ahead of a moving target by its velocity times this (the facing, the barrel and the shot); needs a traverse
    // rate. 0: aims at the target itself.
    float leadSeconds = 0.0f;
    // A hostile actor's reaction to its shield breaking, for at most shieldBreakSeconds while the shield stays down.
    ActorShieldBreakReaction shieldBreakReaction = ActorShieldBreakReaction::None;
    float shieldBreakSeconds = 8.0f;
    // A skirmisher (monster modifier `skirmisher`, MM9's BaseMelee AI): it keeps chasing a target that steps away
    // while it attacks (its model swings over its gait), may run a strafe attack at 45 degrees past the target
    // (strafeAttackChance, when it was moving as the attack began), and after a melee attack evades (evadeChance:
    // backpedals for half of evadeSeconds, then circles the target) or backs off backOffSeconds from a strafe attack.
    // While evading it may shoot or cast but not strike. By tauntChance it taunts for tauntSeconds (0: never) when it
    // first notices the party and after a back-off. Real-time only.
    // MM9's SpeedThrottle: it holds off until its attack will be ready as it arrives, and while it strikes it keeps
    // pace with a target that moves away and lunges ahead in the wind-up.
    bool skirmish = false;
    float strafeAttackChance = 0.0f;
    float evadeChance = 0.0f;
    float evadeSeconds = 2.0f;
    // Above evadeSeconds: each evade lasts a seeded roll between the two (an MM9 Lobber Pod's 1.8-2.2 s).
    float evadeSecondsMax = 0.0f;
    float backOffSeconds = 0.3f;
    float tauntChance = 0.0f;
    float tauntSeconds = 0.0f;
    // The MM9 AI profile of its monster row (modifier mm9_ai) with its placement's overrides (placedMm9AiProfile),
    // set by ActorBehaviorRuntime every AI step for MM9 monsters only. Walkers, swimmers, fliers and turrets run MM9's
    // loops on it (MM9_MONSTER_AI_PLAN.md phases 2-5; the Dragon King's attacks come from its behaviour script).
    std::optional<Mm9AiProfile> mm9Profile;
    // The reposition modifier (ActorRepositionRules.h): a monster that holds its place moves to see its target again
    // and backs off from a rush. Read by the MM9 ranged holder's loop; any other monster ignores it.
    std::optional<RepositionModifier> reposition;

    // Filled by ActorBehaviorRuntime every AI step, not data. idleAimActive: the actor has no target and its scan (or
    // the hold of its last aim) gives the facing it turns to, idleAimYawRadians. aimLead: the lead (leadSeconds) the
    // AI adds to its target's position.
    bool idleAimActive = false;
    float idleAimYawRadians = 0.0f;
    GameplayWorldPoint aimLead = {};

    bool keepsRangedBand() const
    {
        return rangedMaxDistance > 0.0f;
    }
};

struct ActorWorldFacts
{
    GameplayWorldPoint listenerPosition = {};
    float targetZ = 0.0f;
    float floorZ = 0.0f;
    int sectorId = 0;
    bool active = false;
    bool activeByDistance = false;
    bool sameSectorAsParty = false;
    bool portalPathToParty = false;
};

// An MM9 boss behaviour's directives for its MM9 loop (MM9_MONSTER_AI_PLAN.md phase 5; ActorBehaviorRuntime sets
// them every AI step from the script's self:setMm9 and its one-shot commands). Lua decides when, the loop does the
// work. Without a script they are all off and the loop runs as before.
struct ActorMm9ScriptFacts
{
    // A script drives this monster's loop.
    bool active = false;
    // It picks every attack itself (Dragon.scr): the loop holds its target, faces it (at turnRadiansPerSecond, 0:
    // at once) and attacks only when told (attack below).
    bool drivesAttacks = false;
    float turnRadiansPerSecond = 0.0f;
    // It never takes a target by itself (a cut-scene actor, Ebora in her tub), nor answers calls and hits.
    bool passive = false;
    // Alerts and help calls are lost on it (YanmirBase.scr OnAlert).
    bool ignoresCalls = false;
    // Its give-up clock (MAX_CHASE_TIME): negative keeps the loop's 30 s, 0 never gives up by the clock.
    float chaseLimitSeconds = -1.0f;
    // One-shots for this step: hold this target (kind None: drop it), start this attack.
    bool setTarget = false;
    ActorAiTargetKind targetKind = ActorAiTargetKind::None;
    size_t targetActorIndex = static_cast<size_t>(-1);
    std::optional<GameplayActorAttackAbility> attack;
    // The script's own decisions since the last AI step (self:trace), for the decision trace.
    std::vector<std::string> traceLines;
};

// Directives from an actor behaviour script (ActorBehaviorRuntime). Absent scripts leave these at defaults.
struct ActorBehaviorFacts
{
    // A scripted action is playing: the actor stands, faces its target and shows holdAnimation.
    bool holdActive = false;
    bool holdRestartAnimation = false;
    ActorAiAnimationState holdAnimation = ActorAiAnimationState::Standing;
    // The hold keeps its facing (a dormant monster) instead of turning to its target.
    bool holdKeepsFacing = false;
    // Its attack recovery runs down this many times faster (a frenzy, GameplayActorModifiers).
    float attackRateMultiplier = 1.0f;
    // An MM9 boss behaviour's directives (phase 5).
    ActorMm9ScriptFacts mm9Script;
};

struct ActorAiFacts
{
    size_t actorIndex = static_cast<size_t>(-1);
    uint32_t actorId = 0;

    ActorIdentityFacts identity = {};
    ActorStatsFacts stats = {};
    ActorRuntimeFacts runtime = {};
    ActorStatusFacts status = {};
    ActorTargetFacts target = {};
    ActorMovementFacts movement = {};
    ActorWorldFacts world = {};
    ActorBehaviorFacts behavior = {};
    ActorTacticsFacts tactics = {};
    // An MM9 monster's world facts (hits, kills, winces, reachability, water, pods); unused by every other actor.
    ActorMm9WorldFacts mm9World = {};
};

struct ActorStateUpdate
{
    std::optional<ActorAiMotionState> motionState;
    std::optional<uint8_t> hostilityType;
    std::optional<bool> hostileToParty;
    std::optional<bool> hasDetectedParty;
    std::optional<bool> dead;
    std::optional<int> currentHp;
    std::optional<bool> bloodSplatSpawned;
    std::optional<float> recoverySeconds;
    std::optional<float> attackCooldownSeconds;
    std::optional<float> idleDecisionSeconds;
    std::optional<float> actionSeconds;
    std::optional<float> crowdSideLockRemainingSeconds;
    std::optional<float> crowdNoProgressSeconds;
    std::optional<float> crowdLastEdgeDistance;
    std::optional<float> crowdRetreatRemainingSeconds;
    std::optional<float> crowdStandRemainingSeconds;
    std::optional<float> crowdProbeEdgeDistance;
    std::optional<float> crowdProbeElapsedSeconds;
    std::optional<uint32_t> idleDecisionCount;
    std::optional<uint32_t> pursueDecisionCount;
    std::optional<uint32_t> attackDecisionCount;
    std::optional<uint8_t> crowdEscapeAttempts;
    std::optional<int8_t> crowdSideSign;
    std::optional<bool> attackImpactTriggered;
    std::optional<ActorSkirmishPhase> skirmishPhase;
    std::optional<float> skirmishSeconds;
    std::optional<int8_t> skirmishSide;
    std::optional<GameplayActorAttackAbility> queuedAttackAbility;
    std::optional<GameplayActorSpellEffectState> spellEffects;
    // An MM9 monster's loop state after this step, when it changed (ActorRuntimeFacts::mm9).
    std::optional<ActorMm9State> mm9;
    // The decision taken this step, if any (the decision trace), and one taken before it in the same step (an MM9
    // detection, retarget, shot check or wince), traced first.
    std::optional<ActorAiDecision> decision;
    std::optional<ActorAiDecision> earlierDecision;
    // A decision of the MM9 layers in the same step (a call sent or received, a flight's mode, a resurrection),
    // traced between the two.
    std::optional<ActorAiDecision> layerDecision;
};

struct ActorAnimationUpdate
{
    std::optional<ActorAiAnimationState> animationState;
    std::optional<float> animationTimeTicks;
    bool resetAnimationTime = false;
    bool resetOnAnimationChange = false;
};

struct ActorMovementIntent
{
    ActorAiMovementAction action = ActorAiMovementAction::None;
    GameplayWorldPoint targetPosition = {};
    float moveDirectionX = 0.0f;
    float moveDirectionY = 0.0f;
    float desiredMoveX = 0.0f;
    float desiredMoveY = 0.0f;
    float desiredMoveZ = 0.0f;
    float yawRadians = 0.0f;
    float actionSeconds = 0.0f;
    float moveSpeed = 0.0f;
    float targetEdgeDistance = 0.0f;
    bool targetHasAttackLineOfSight = false;
    bool updateYaw = false;
    // The actor keeps yawRadians while it moves instead of turning to its movement (tactics' back-off: it steps back
    // still facing its target). Indoors the yaw already follows the AI except along a path.
    bool keepYawWhileMoving = false;
    bool clearVelocity = false;
    bool applyMovement = false;
    bool meleePursuitActive = false;
    bool inMeleeRange = false;
    bool resetCrowdSteering = false;
    bool crowdSteeringActive = false;
    bool updateCrowdProbePosition = false;
};

struct ActorAttackRequest
{
    ActorAiAttackRequestKind kind = ActorAiAttackRequestKind::None;
    GameplayActorAttackAbility ability = GameplayActorAttackAbility::Attack1;
    ActorAiTargetKind targetKind = ActorAiTargetKind::None;
    size_t targetActorIndex = static_cast<size_t>(-1);
    uint32_t spellId = 0;
    uint32_t skillLevel = 0;
    SkillMastery skillMastery = SkillMastery::None;
    std::string projectileTokenOverride;
    int damage = 0;
    int attackBonus = 0;
    CombatDamageType damageType = CombatDamageType::Physical;
    GameplayWorldPoint source = {};
    GameplayWorldPoint target = {};
};

struct ActorProjectileRequest
{
    size_t sourceActorIndex = static_cast<size_t>(-1);
    GameplayActorAttackAbility ability = GameplayActorAttackAbility::Attack1;
    ActorAiTargetKind targetKind = ActorAiTargetKind::None;
    // The target actor (targetKind Actor), for a true_aim monster's homing shots.
    size_t targetActorIndex = static_cast<size_t>(-1);
    uint32_t objectId = 0;
    uint32_t spellId = 0;
    uint32_t skillLevel = 0;
    SkillMastery skillMastery = SkillMastery::None;
    std::string projectileTokenOverride;
    int damage = 0;
    int attackBonus = 0;
    CombatDamageType damageType = CombatDamageType::Physical;
    GameplayWorldPoint source = {};
    GameplayWorldPoint target = {};
};

struct ActorAudioRequest
{
    ActorAiAudioRequestKind kind = ActorAiAudioRequestKind::None;
    size_t actorIndex = static_cast<size_t>(-1);
    GameplayWorldPoint position = {};
};

struct ActorFxRequest
{
    ActorAiFxRequestKind kind = ActorAiFxRequestKind::None;
    size_t actorIndex = static_cast<size_t>(-1);
    uint32_t spellId = 0;
    GameplayWorldPoint position = {};
};

// A monster the AI brings into the world: a Lobber's pod (MM9_MONSTER_AI_PLAN.md phase 3). The world places it at
// position facing yawRadians, of the source's hostility and group, and records the source as its launcher.
struct ActorSpawnRequest
{
    size_t sourceActorIndex = static_cast<size_t>(-1);
    int16_t monsterId = 0;
    GameplayWorldPoint position = {};
    float yawRadians = 0.0f;
    bool hostile = true;
    uint32_t group = 0;
    // MM9's Spawn with ScriptParams 1 (a death spawn: LesserDemon.scr's "GreaterDemon ScriptParams 1"), not a pod.
    bool mm9Spawned = false;
};

struct ActorAiUpdate
{
    size_t actorIndex = static_cast<size_t>(-1);

    ActorStateUpdate state = {};
    ActorAnimationUpdate animation = {};
    ActorMovementIntent movementIntent = {};

    std::optional<ActorAttackRequest> attackRequest;
    std::optional<ActorSpawnRequest> spawnRequest;
    std::optional<ActorMm9Request> mm9Request;
    std::vector<ActorAudioRequest> audioRequests;
    std::vector<ActorFxRequest> fxRequests;
};

struct ActorTurnBasedFrameFacts
{
    ActorTurnBasedMode mode = ActorTurnBasedMode::RealTime;
    // Actors the turn engine lets take their queued action in this step, by actor index.
    std::vector<size_t> actionGrantActorIndices;
};

struct ActorAiFrameFacts
{
    float deltaSeconds = 0.0f;
    float fixedStepSeconds = 0.0f;
    ActorPartyFacts party = {};
    ActorTurnBasedFrameFacts turnBased = {};
    // The world's melee vertical reach (GameplayActorService::meleeVerticalReach; 0: melee ignores height).
    float meleeVerticalReach = 0.0f;
    std::vector<ActorAiFacts> backgroundActors;
    std::vector<ActorAiFacts> activeActors;
};

struct ActorAiFrameResult
{
    std::vector<ActorAiUpdate> actorUpdates;
    std::vector<size_t> activeActorIndices;
    std::vector<ActorProjectileRequest> projectileRequests;
    std::vector<ActorAudioRequest> audioRequests;
    std::vector<ActorFxRequest> fxRequests;
    std::vector<ActorSpawnRequest> spawnRequests;
};
}
