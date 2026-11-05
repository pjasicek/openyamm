#include "game/gameplay/Mm9ActorRules.h"

#include <algorithm>
#include <cmath>

namespace OpenYAMM::Game
{
namespace
{
constexpr float RetargetChance = 0.70f;
constexpr float RetargetChanceInRange = 0.45f;
constexpr float RetargetFartherMultiplier = 0.5f;
constexpr float RetargetNearerMultiplier = 1.15f;
constexpr float ShotCheckWalkerMinSeconds = 1.0f;
constexpr float ShotCheckWalkerMaxSeconds = 2.5f;
constexpr float ShotCheckHolderMinSeconds = 0.2f;
constexpr float ShotCheckHolderMaxSeconds = 0.4f;
// SightDistance - 5 LT.
constexpr float RangeAttackSightMargin = 5.0f * 2.56f;
constexpr float WinceHealthShare = 0.2f;
constexpr float WinceMinChance = 0.20f;
constexpr float WinceMaxChance = 0.50f;
constexpr uint32_t RunnerSalt = 0x5bd1e995u;
constexpr float DegreesToRadians = 3.14159265358979f / 180.0f;
// BaseFly.inc OnDamageDone, FlyRange.inc ShouldRangeAttack, lobber.scr NO_CLEAR_SHOT_IGNORE_CHANCE: the bounds their
// GetRandomInt 0, 100 rolls are tested below.
constexpr int FlierRetargetBelow = 50;
constexpr int FlyShotSkipBelow = 40;
constexpr int TurretBlindShotSkipBelow = 75;
constexpr float FlyShotCheckMinSeconds = 0.3f;
constexpr float FlyShotCheckMaxSeconds = 1.3f;
constexpr float SwoopMinDegrees = 30.0f;
constexpr float SwoopMaxDegrees = 50.0f;
constexpr float TurretScanMinSeconds = 5.0f;
constexpr float TurretScanMaxSeconds = 15.0f;
constexpr float TurretScanMinDegrees = 20.0f;
constexpr float TurretScanMaxDegrees = 120.0f;
constexpr float WanderZeroBound = 0.01f;
constexpr float WanderTurnMinDegrees = 15.0f;
constexpr float WanderTurnMaxDegrees = 180.0f;
constexpr float WanderTurnObstacleMaxDegrees = 90.0f;
constexpr int CowerBelow = 10;
constexpr float RunAwayTurnMinDegrees = 15.0f;
constexpr float RunAwayTurnMaxDegrees = 45.0f;
constexpr float RunAwayTickMinSeconds = 0.3f;
constexpr float RunAwayTickMaxSeconds = 0.8f;
constexpr float ResurrectMinSeconds = 3.0f;
constexpr float ResurrectMaxSeconds = 6.0f;
constexpr float SelfRaiseMinSeconds = 2.0f;
constexpr float SelfRaiseMaxSeconds = 10.0f;
constexpr float HangFidgetMinSeconds = 2.0f;
constexpr float HangFidgetMaxSeconds = 10.0f;
// AIBase::SetAnimState's idle fidget timer: 5 s plus up to 7 s (object.lto 0x100ee5c8, 0x100eef30).
constexpr float IdleFidgetMinSeconds = 5.0f;
constexpr float IdleFidgetRandomSeconds = 7.0f;
}

float mm9AttackStartCooldown(bool cast, float clipSeconds, float impactSeconds, float recoverySeconds)
{
    const float clip = std::max(0.0f, clipSeconds);
    const float recovery = std::max(0.0f, recoverySeconds);
    return cast ? std::clamp(impactSeconds, 0.0f, clip) + recovery : clip + recovery;
}

float mm9CutAttackCooldown(bool armedAtHit, bool cast, float cooldownLeft, float actionLeftAtHit)
{
    if (!armedAtHit)
    {
        return 0.0f;
    }

    return std::max(0.0f, cast ? cooldownLeft : cooldownLeft - std::max(0.0f, actionLeftAtHit));
}

float mm9ScriptRecoveryTimeLeft(float realSecondsLeft)
{
    return std::max(0.0f, realSecondsLeft) * Mm9ScriptRecoveryScale;
}

bool mm9WalkerArchetype(Mm9AiArchetype archetype)
{
    return archetype == Mm9AiArchetype::Crawler || archetype == Mm9AiArchetype::Skirmisher
        || archetype == Mm9AiArchetype::RangedHolder || archetype == Mm9AiArchetype::Swimmer
        || archetype == Mm9AiArchetype::Guard;
}

bool mm9LoopArchetype(const Mm9AiProfile &profile)
{
    return mm9WalkerArchetype(profile.archetype) || profile.archetype == Mm9AiArchetype::Flier
        || profile.archetype == Mm9AiArchetype::Civilian || profile.archetype == Mm9AiArchetype::Turret;
}

float mm9ScriptChance(int below)
{
    return float(std::clamp(below, 0, 101)) / 101.0f;
}

float mm9Unit(uint32_t actorId, uint32_t counter, uint32_t salt)
{
    uint32_t value = (actorId + 1u) * 0x9e3779b1u + counter * 0x85ebca6bu + salt;
    value ^= value >> 16;
    value *= 0x7feb352du;
    value ^= value >> 15;
    value *= 0x846ca68bu;
    value ^= value >> 16;
    return float(value & 0xffffffu) / float(0x1000000u);
}

float mm9RetargetChance(bool targetInAttackRange, float targetDistance, float attackerDistance)
{
    const float chance = targetInAttackRange ? RetargetChanceInRange : RetargetChance;
    return std::min(1.0f, chance * (attackerDistance > targetDistance ? RetargetFartherMultiplier
        : RetargetNearerMultiplier));
}

bool mm9ShouldRunAfter(bool attackReady, float recoveryLeftSeconds, float edgeDistance, float runSpeed)
{
    if (attackReady)
    {
        return true;
    }

    if (runSpeed <= 0.0f)
    {
        return false;
    }

    return recoveryLeftSeconds < std::max(0.0f, edgeDistance) / runSpeed;
}

float mm9ShotCheckSeconds(bool holder, float unit)
{
    const float minimum = holder ? ShotCheckHolderMinSeconds : ShotCheckWalkerMinSeconds;
    const float maximum = holder ? ShotCheckHolderMaxSeconds : ShotCheckWalkerMaxSeconds;
    return minimum + (maximum - minimum) * std::clamp(unit, 0.0f, 1.0f);
}

float mm9ShotChance(Mm9ShotLine line)
{
    switch (line)
    {
        case Mm9ShotLine::Target:
            return 1.0f;
        case Mm9ShotLine::Clear:
            return 0.20f;
        case Mm9ShotLine::Object:
            return 0.15f;
        case Mm9ShotLine::Blocked:
            return 0.0f;
    }

    return 0.0f;
}

float mm9RangeAttackRange(float sight, float projectileRange)
{
    return std::max(0.0f, std::min(projectileRange, sight - RangeAttackSightMargin));
}

int mm9RangedSpellSlot(int spell1Chance, int spell2Chance, float roll)
{
    const float spell1 = float(std::clamp(spell1Chance, 0, 100)) / 100.0f;
    const float spell2 = float(std::clamp(spell2Chance, 0, 100)) / 100.0f;

    if (roll < spell1)
    {
        return 1;
    }

    if (spell1 < 1.0f && (roll - spell1) / (1.0f - spell1) < spell2)
    {
        return 2;
    }

    return 0;
}

bool mm9IsRunner(uint32_t actorId, float runawayChance)
{
    return runawayChance > mm9Unit(actorId, 0u, RunnerSalt);
}

bool mm9ShouldRunAway(const Mm9RunAwayInput &input)
{
    if (input.feared)
    {
        return true;
    }

    if (input.sinceLastFleeSeconds < Mm9RunAwayAgainSeconds || !input.runner || !input.hasHidingPlace)
    {
        return false;
    }

    if (input.largestHit > 0 && input.currentHp <= 2 * input.largestHit)
    {
        return true;
    }

    return !input.hasRangedAttack && !input.targetReachable && !input.targetFlies;
}

float mm9WinceChance(Mm9AiWince wince, int currentHp, int maxHp, float unit)
{
    if (wince == Mm9AiWince::Never || maxHp <= 0 || float(currentHp) > WinceHealthShare * float(maxHp))
    {
        return 0.0f;
    }

    // 20 + rand % 31 percent: 20-50 %.
    const float steps = std::round((WinceMaxChance - WinceMinChance) * 100.0f) + 1.0f;
    return WinceMinChance + std::floor(std::clamp(unit, 0.0f, 0.999f) * steps) / 100.0f;
}

bool mm9Perceives(const Mm9PerceptionInput &input)
{
    if (!input.lineOfSight)
    {
        return false;
    }

    const float scale = input.doubled ? 2.0f : 1.0f;

    if (input.distance <= input.hearing * scale)
    {
        return true;
    }

    return input.inFront && input.distance <= input.sight * scale;
}

float mm9PerceptionRange(float sight, float hearing, bool doubled)
{
    return std::max(0.0f, std::max(sight, hearing)) * (doubled ? 2.0f : 1.0f);
}

float mm9SenseRange(float sharedRange, float perceptionRange, float maximumRange)
{
    return std::min(std::max(sharedRange, perceptionRange), std::max(sharedRange, maximumRange));
}

float mm9EyeZ(float footZ, float height, float eyeBelowTop)
{
    return footZ + std::max(height - eyeBelowTop, height * 0.5f);
}

float mm9MeleeReach(float attackReach, bool targetIsActor, float partyRadius)
{
    return targetIsActor ? attackReach : attackReach + std::max(0.0f, partyRadius);
}

bool mm9MeleeSweepReaches(float meleeSweep, float attackReach, float attackerRadius, float targetRadius,
    float centerDistance)
{
    return centerDistance <= attackerRadius + std::max(meleeSweep, attackReach) + targetRadius;
}

Mm9FlierStyle mm9FlierStyle(const Mm9AiProfile &profile)
{
    Mm9FlierStyle style = {};

    if (profile.meleeWindowSeconds > 0.0f)
    {
        style.backOffSeconds = Mm9BansheeBackOffSeconds;
        style.backOffRise = Mm9BansheeBackOffRise;
        style.swoops = false;
    }

    return style;
}

float mm9FlierRetargetChance()
{
    return mm9ScriptChance(FlierRetargetBelow);
}

float mm9FlyShotCheckSeconds(float unit)
{
    return FlyShotCheckMinSeconds + (FlyShotCheckMaxSeconds - FlyShotCheckMinSeconds) * std::clamp(unit, 0.0f, 1.0f);
}

float mm9FlyShotChance()
{
    return 1.0f - mm9ScriptChance(FlyShotSkipBelow);
}

void mm9FlyBackOffShares(float rise, bool targetFlies, float &horizontalShare, float &verticalShare)
{
    const float up = targetFlies ? 0.0f : std::max(0.0f, rise);
    const float length = std::sqrt(1.0f + up * up);
    horizontalShare = 1.0f / length;
    verticalShare = up / length;
}

float mm9SwoopAngleRadians(float angleUnit, float sideUnit)
{
    // GetRandomInt 30, 50: 21 whole degrees.
    const float degrees = SwoopMinDegrees
        + std::floor(std::clamp(angleUnit, 0.0f, 0.999f) * (SwoopMaxDegrees - SwoopMinDegrees + 1.0f));
    const float sign = sideUnit < 0.5f ? -1.0f : 1.0f;
    return sign * degrees * DegreesToRadians;
}

float mm9FlyPassSpeedShare(bool targetMoving, float flySpeed)
{
    if (targetMoving || flySpeed <= 0.0f)
    {
        return 1.0f;
    }

    return std::min(Mm9FlyStillPassSpeedShare, Mm9FlyMaxPassSpeed / flySpeed);
}

float mm9TurretScanSeconds(float unit)
{
    return TurretScanMinSeconds + (TurretScanMaxSeconds - TurretScanMinSeconds) * std::clamp(unit, 0.0f, 1.0f);
}

float mm9TurretScanTurnRadians(float angleUnit, float sideUnit)
{
    const float degrees =
        TurretScanMinDegrees + (TurretScanMaxDegrees - TurretScanMinDegrees) * std::clamp(angleUnit, 0.0f, 1.0f);
    const float sign = sideUnit < 0.5f ? -1.0f : 1.0f;
    return sign * degrees * DegreesToRadians;
}

bool mm9TurretCanLob(bool attackReady, int livePods)
{
    return attackReady && livePods < Mm9TurretMaxPods;
}

float mm9TurretShotChance(bool clearShot)
{
    return clearShot ? 1.0f : 1.0f - mm9ScriptChance(TurretBlindShotSkipBelow);
}

bool mm9SwimmerRunsFrom(bool targetInWater)
{
    return !targetInWater;
}

bool mm9SwimmerCanTarget(bool selfInWater, bool targetInWater)
{
    return !selfInWater || targetInWater;
}

float mm9WanderSeconds(float minimum, float maximum, float unit)
{
    // BaseWanderStartup: a zero bound reads as 0.01.
    const float low = minimum == 0.0f ? WanderZeroBound : minimum;
    const float high = maximum == 0.0f ? WanderZeroBound : maximum;
    return low + (high - low) * std::clamp(unit, 0.0f, 1.0f);
}

float mm9WanderTurnRadians(bool afterObstacle, float angleUnit, float sideUnit)
{
    const float maximum = afterObstacle ? WanderTurnObstacleMaxDegrees : WanderTurnMaxDegrees;
    const float degrees = WanderTurnMinDegrees + (maximum - WanderTurnMinDegrees) * std::clamp(angleUnit, 0.0f, 1.0f);
    const float sign = sideUnit < 0.5f ? 1.0f : -1.0f;
    return sign * degrees * DegreesToRadians;
}

bool mm9BeyondLeash(float deltaX, float deltaY, float leash)
{
    return leash > 0.0f && deltaX * deltaX + deltaY * deltaY >= leash * leash;
}

int mm9NextPathMarker(int current, int count, bool random, float unit)
{
    if (count <= 0)
    {
        return 0;
    }

    if (!random)
    {
        return (current + 1) % count;
    }

    if (count == 2)
    {
        return current == 0 ? 1 : 0;
    }

    if (count == 1)
    {
        return 0;
    }

    // Rejection sampling over 0 .. count - 1 until it differs: uniform over the others.
    const int pick = std::min(count - 2, int(std::clamp(unit, 0.0f, 0.999999f) * float(count - 1)));
    return pick >= current ? pick + 1 : pick;
}

int mm9FirstPathMarker(int count, bool random, float unit)
{
    return random ? mm9NextPathMarker(0, count, true, unit) : 0;
}

Mm9NewTargetOutcome mm9NewTargetCheck(const Mm9NewTargetInput &input)
{
    if (input.resurrecting || !input.candidateValid || input.candidateIsTarget || input.fleeing)
    {
        return Mm9NewTargetOutcome::Invalid;
    }

    return input.hasTarget ? Mm9NewTargetOutcome::Roll : Mm9NewTargetOutcome::Take;
}

float mm9AlertRepeatSeconds(float scriptRandom)
{
    return std::max(0.0f, scriptRandom);
}

float mm9HelpRadius(float height)
{
    return 10.0f * 0.5f * std::max(0.0f, height);
}

float mm9CowerChance()
{
    return mm9ScriptChance(CowerBelow);
}

float mm9RunAwayTurnRadians(float unit)
{
    return (RunAwayTurnMinDegrees + (RunAwayTurnMaxDegrees - RunAwayTurnMinDegrees) * std::clamp(unit, 0.0f, 1.0f))
        * DegreesToRadians;
}

float mm9RunAwayTickSeconds(float unit)
{
    return RunAwayTickMinSeconds + (RunAwayTickMaxSeconds - RunAwayTickMinSeconds) * std::clamp(unit, 0.0f, 1.0f);
}

float mm9ResurrectDelaySeconds(float unit)
{
    return ResurrectMinSeconds + (ResurrectMaxSeconds - ResurrectMinSeconds) * std::clamp(unit, 0.0f, 1.0f);
}

float mm9SelfRaiseDelaySeconds(float unit)
{
    return SelfRaiseMinSeconds + (SelfRaiseMaxSeconds - SelfRaiseMinSeconds) * std::clamp(unit, 0.0f, 1.0f);
}

bool mm9CanRaiseNow(float nearestActorDistance, float radius)
{
    return nearestActorDistance > 2.0f * std::max(0.0f, radius);
}

bool mm9DoorAhead(float facingX, float facingY, float doorNormalX, float doorNormalY)
{
    const float facingLength = std::sqrt(facingX * facingX + facingY * facingY);
    const float normalLength = std::sqrt(doorNormalX * doorNormalX + doorNormalY * doorNormalY);

    if (facingLength <= 0.0f || normalLength <= 0.0f)
    {
        return false;
    }

    const float cosine = -(facingX * doorNormalX + facingY * doorNormalY) / (facingLength * normalLength);
    return cosine >= std::cos(Mm9DoorFacingDegrees * DegreesToRadians);
}

int mm9PickRefuge(int count, float unit)
{
    return count <= 0 ? -1 : std::min(count - 1, int(std::clamp(unit, 0.0f, 0.999999f) * float(count)));
}

bool mm9CivilianRunsFromHit(bool heldTargetIsParty)
{
    return !heldTargetIsParty;
}

Mm9PoliceCallResult mm9PoliceCall(const Mm9PoliceCallInput &input)
{
    Mm9PoliceCallResult result = {};

    if (!input.help && input.senderIsMonster)
    {
        result.ignored = true;
        return result;
    }

    result.targetBecomesEnemy = input.targetIsFriend && (input.help || input.senderIsGuard);
    return result;
}

bool mm9GuardTurnsOnParty(int partyHits)
{
    return partyHits >= Mm9GuardPartyHitTolerance;
}

bool mm9DormantWakes(Mm9AiDormantUntil until, Mm9AiDormantPose pose, Mm9DormantEvent event, bool fidgeting)
{
    if (event == Mm9DormantEvent::Trigger || event == Mm9DormantEvent::Hit)
    {
        return true;
    }

    switch (until)
    {
    case Mm9AiDormantUntil::Disturbed:
        return event != Mm9DormantEvent::Sighted || pose != Mm9AiDormantPose::Hang || fidgeting;
    case Mm9AiDormantUntil::Sighted:
        return event == Mm9DormantEvent::Sighted;
    default:
        return false;
    }
}

float mm9HangFidgetWaitSeconds(float unit)
{
    return HangFidgetMinSeconds + (HangFidgetMaxSeconds - HangFidgetMinSeconds) * std::clamp(unit, 0.0f, 1.0f);
}

float mm9IdleFidgetWaitSeconds(float unit)
{
    return IdleFidgetMinSeconds + IdleFidgetRandomSeconds * std::clamp(unit, 0.0f, 1.0f);
}

int mm9FidgetVariant(float unit, size_t count)
{
    return count <= 1 ? 0 : std::min(int(count) - 1, int(std::clamp(unit, 0.0f, 1.0f) * float(count)));
}

bool mm9WakesWithWakeup(Mm9AiDormantPose pose)
{
    return pose == Mm9AiDormantPose::Coffin || pose == Mm9AiDormantPose::Sleep || pose == Mm9AiDormantPose::Lie;
}

float mm9WakeHoldSeconds(Mm9AiDormantPose pose, float launchSeconds, float wakeupSeconds)
{
    if (pose == Mm9AiDormantPose::Hang)
    {
        return std::max(0.0f, launchSeconds);
    }

    return mm9WakesWithWakeup(pose) ? std::max(0.0f, wakeupSeconds) : 0.0f;
}
}
