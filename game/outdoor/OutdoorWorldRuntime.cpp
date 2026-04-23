#include "game/outdoor/OutdoorWorldRuntime.h"

#include "game/tables/ChestTable.h"
#include "game/fx/ParticleRecipes.h"
#include "game/outdoor/OutdoorFxRuntime.h"
#include "game/gameplay/ChestRuntime.h"
#include "game/gameplay/CorpseLootRuntime.h"
#include "game/gameplay/GameplayActorAiSystem.h"
#include "game/gameplay/GameplayActorService.h"
#include "game/gameplay/GameplayFxService.h"
#include "game/items/ItemGenerator.h"
#include "game/items/ItemRuntime.h"
#include "game/outdoor/OutdoorGameView.h"
#include "game/tables/ItemTable.h"
#include "game/outdoor/OutdoorGeometryUtils.h"
#include "game/outdoor/OutdoorGameplayInputController.h"
#include "game/outdoor/OutdoorInteractionController.h"
#include "game/outdoor/OutdoorPartyRuntime.h"
#include "game/party/SpellIds.h"
#include "game/audio/SoundIds.h"
#include "game/SpriteObjectDefs.h"
#include "game/party/SkillData.h"
#include "game/StringUtils.h"
#include "game/ui/GameplayOverlayTypes.h"

#include <bx/math.h>

#include <algorithm>
#include <cassert>
#include <cmath>
#include <cstring>
#include <iostream>
#include <limits>
#include <numeric>
#include <random>
#include <sstream>
#include <utility>

namespace OpenYAMM::Game
{
namespace
{
constexpr int RandomChestItemMinLevel = 1;
constexpr int RandomChestItemMaxLevel = 7;
constexpr int SpawnableItemTreasureLevels = 6;
constexpr float GameMinutesPerRealSecond = 0.5f;
constexpr uint32_t ActorInvisibleBit = static_cast<uint32_t>(EvtActorAttribute::Invisible);
constexpr uint32_t ActorAggressorBit = static_cast<uint32_t>(EvtActorAttribute::Aggressor);
constexpr float TicksPerSecond = 128.0f;
constexpr float OeRealtimeRecoveryScale = 2.133333333333333f;
constexpr float HostilityCloseRange = 1024.0f;
constexpr float HostilityShortRange = 2560.0f;
constexpr float HostilityMediumRange = 5120.0f;
constexpr float HostilityLongRange = 10240.0f;
constexpr float ActorMeleeRange = 307.2f;
constexpr float ActiveActorUpdateRange = 6144.0f;
constexpr size_t MaxActiveActorUpdates = 48;
constexpr float InactiveActorDecisionIntervalSeconds = 1.5f;
constexpr float InactiveActorBoredSeconds = 2.0f;
constexpr uint32_t InactiveActorFidgetChancePercent = 5u;
constexpr float PeasantAggroRadius = 4096.0f;
constexpr float PartyCollisionRadius = 37.0f;
constexpr float PartyCollisionHeight = 192.0f;
constexpr float OutdoorFaceSpatialCellSize = 2048.0f;
constexpr bool DebugProjectileSpawnLogging = false;
constexpr bool DebugProjectileCollisionLogging = false;
constexpr bool DebugProjectileLifetimeLogging = false;
constexpr bool DebugProjectileImpactLogging = false;
constexpr bool DebugProjectileAoeLogging = false;
constexpr bool DebugChestPopulateLogging = false;
constexpr std::array<std::array<int, 3>, 4> EncounterDifficultyTierWeights = {{
    {{100, 0, 0}},
    {{90, 8, 2}},
    {{70, 20, 10}},
    {{50, 30, 20}},
}};
constexpr float GroundSnapHeight = 1.0f;
constexpr float OeNonFlyingActorRadius = 40.0f;
constexpr float ActorUpdateStepSeconds = 1.0f / 128.0f;
constexpr float MaxAccumulatedActorUpdateSeconds = 0.1f;
constexpr int JournalRevealWidth = 88;
constexpr int JournalRevealHeight = 88;
constexpr int JournalRevealBytesPerRow = 11;
constexpr float JournalMapWorldHalfExtent = 32768.0f;

void ensureJournalRevealMaskSize(std::vector<uint8_t> &bytes)
{
    const size_t expectedSize = JournalRevealHeight * JournalRevealBytesPerRow;

    if (bytes.size() != expectedSize)
    {
        bytes.assign(expectedSize, 0);
    }
}

void setPackedRevealBit(std::vector<uint8_t> &bytes, int cellX, int cellY)
{
    if (cellX < 0 || cellX >= JournalRevealWidth || cellY < 0 || cellY >= JournalRevealHeight)
    {
        return;
    }

    const size_t index = static_cast<size_t>(cellY * JournalRevealWidth + cellX);
    const size_t byteIndex = index / 8;

    if (byteIndex >= bytes.size())
    {
        return;
    }

    const uint8_t mask = static_cast<uint8_t>(1u << (7u - static_cast<unsigned>(index % 8)));
    bytes[byteIndex] |= mask;
}

void updateOutdoorJournalRevealMask(const OutdoorPartyRuntime &partyRuntime, MapDeltaData &outdoorMapDeltaData)
{
    ensureJournalRevealMaskSize(outdoorMapDeltaData.fullyRevealedCells);
    ensureJournalRevealMaskSize(outdoorMapDeltaData.partiallyRevealedCells);

    const OutdoorMoveState &moveState = partyRuntime.movementState();
    const float centerU = std::clamp(
        (moveState.x + JournalMapWorldHalfExtent) / (JournalMapWorldHalfExtent * 2.0f),
        0.0f,
        0.999999f);
    const float centerV = std::clamp(
        (JournalMapWorldHalfExtent - moveState.y) / (JournalMapWorldHalfExtent * 2.0f),
        0.0f,
        0.999999f);
    const int centerCellX = static_cast<int>(std::floor(centerU * static_cast<float>(JournalRevealWidth)));
    const int centerCellY = static_cast<int>(std::floor(centerV * static_cast<float>(JournalRevealHeight)));

    for (int offsetY = -10; offsetY < 10; ++offsetY)
    {
        const int cellY = centerCellY + offsetY;

        for (int offsetX = -10; offsetX < 10; ++offsetX)
        {
            const int cellX = centerCellX + offsetX;
            const int distanceSquared = offsetX * offsetX + offsetY * offsetY;

            if (distanceSquared > 100)
            {
                continue;
            }

            setPackedRevealBit(outdoorMapDeltaData.partiallyRevealedCells, cellX, cellY);

            if (distanceSquared <= 49)
            {
                setPackedRevealBit(outdoorMapDeltaData.fullyRevealedCells, cellX, cellY);
            }
        }
    }
}
constexpr float Pi = 3.14159265358979323846f;
constexpr float PartyTargetHeightOffset = 96.0f;
constexpr float OeTurnAwayFromWaterAngleRadians = Pi / 32.0f;
constexpr int DwiMapId = 1;
constexpr uint32_t DwiTestActor61 = 61;
constexpr float DwiTestActor61X = -7665.0f;
constexpr float DwiTestActor61Y = -4660.0f;
constexpr float DwiTestActor61Z = 200.0f;
constexpr uint32_t EventSpellSourceId = std::numeric_limits<uint32_t>::max();
constexpr uint32_t GoldHeapSmallItemId = 187;
constexpr uint32_t GoldHeapLargeItemId = 189;
constexpr float WorldItemThrowPitchRadians = Pi * 2.0f * (184.0f / 2048.0f);
constexpr float WorldItemThrowSpeed = 200.0f;
constexpr float WorldItemGravity = 900.0f;
constexpr float WorldItemBounceFactor = 0.5f;
constexpr float WorldItemGroundDamping = 0.89263916f;
constexpr float WorldItemRestingHorizontalSpeedSquared = 400.0f;
constexpr float WorldItemBounceStopVelocity = 10.0f;
constexpr float WorldItemGroundClearance = 1.0f;
constexpr float WorldItemSupportFloorProbeHeight = 96.0f;
constexpr int32_t MapWeatherFoggy = 1;
constexpr int32_t MapWeatherSnowing = 2;
constexpr int32_t MapWeatherRaining = 4;
constexpr float DefaultOutdoorVisibilityDistance = 200000.0f;
constexpr float ArmageddonDurationSeconds = 256.0f / TicksPerSecond;
constexpr uint32_t ArmageddonShakeStepCount = 60;
constexpr float ArmageddonShakeYawRadians = 0.035f;
constexpr float ArmageddonShakePitchRadians = 0.024f;
constexpr size_t MaxOutdoorBloodSplats = 64;
constexpr size_t BloodSplatGridResolution = 10;
constexpr float BloodSplatHeightOffset = 2.0f;
constexpr float BloodSplatMinSurfaceHeightTolerance = 32.0f;

enum class InactiveActorDeathAction : uint8_t
{
    Continue = 0,
    HoldDead = 1,
    MarkDead = 2,
    AdvanceDying = 3,
};

struct InactiveActorDeathFrame
{
    InactiveActorDeathAction action = InactiveActorDeathAction::Continue;
    float actionSeconds = 0.0f;
    bool finishedDying = false;
};

struct OutdoorActiveActorCandidate
{
    size_t actorIndex = static_cast<size_t>(-1);
    float distanceToParty = 0.0f;
    bool eligible = false;
};

InactiveActorDeathFrame resolveInactiveActorDeathFrame(
    bool dead,
    bool hpDepleted,
    bool dying,
    float actionSeconds,
    float deltaSeconds)
{
    InactiveActorDeathFrame result = {};

    if (dead)
    {
        result.action = InactiveActorDeathAction::HoldDead;
        return result;
    }

    if (!hpDepleted && !dying)
    {
        return result;
    }

    if (!dying)
    {
        result.action = InactiveActorDeathAction::MarkDead;
        return result;
    }

    result.action = InactiveActorDeathAction::AdvanceDying;
    result.actionSeconds = std::max(0.0f, actionSeconds - std::max(0.0f, deltaSeconds));
    result.finishedDying = result.actionSeconds <= 0.0f;
    return result;
}

float rainIntensityValue(OutdoorWorldRuntime::RainIntensityPreset preset)
{
    switch (preset)
    {
        case OutdoorWorldRuntime::RainIntensityPreset::Light:
            return 0.85f;
        case OutdoorWorldRuntime::RainIntensityPreset::Medium:
            return 1.65f;
        case OutdoorWorldRuntime::RainIntensityPreset::Heavy:
            return 3.65f;
        case OutdoorWorldRuntime::RainIntensityPreset::VeryHeavy:
            return 5.35f;
        case OutdoorWorldRuntime::RainIntensityPreset::Off:
        default:
            return 0.0f;
    }
}

const char *rainIntensityPresetName(OutdoorWorldRuntime::RainIntensityPreset preset)
{
    switch (preset)
    {
        case OutdoorWorldRuntime::RainIntensityPreset::Light:
            return "Light";
        case OutdoorWorldRuntime::RainIntensityPreset::Medium:
            return "Medium";
        case OutdoorWorldRuntime::RainIntensityPreset::Heavy:
            return "Heavy";
        case OutdoorWorldRuntime::RainIntensityPreset::VeryHeavy:
            return "Very Heavy";
        case OutdoorWorldRuntime::RainIntensityPreset::Off:
        default:
            return "Off";
    }
}

uint32_t makeTintedFogColor(
    uint8_t brightness,
    bool hasFogTint,
    uint8_t tintRed,
    uint8_t tintGreen,
    uint8_t tintBlue)
{
    if (!hasFogTint)
    {
        return 0xff000000u
            | (static_cast<uint32_t>(brightness) << 16)
            | (static_cast<uint32_t>(brightness) << 8)
            | static_cast<uint32_t>(brightness);
    }

    const uint8_t red =
        static_cast<uint8_t>(std::clamp(std::lround(static_cast<float>(brightness) * tintRed / 255.0f), 0l, 255l));
    const uint8_t green =
        static_cast<uint8_t>(std::clamp(std::lround(static_cast<float>(brightness) * tintGreen / 255.0f), 0l, 255l));
    const uint8_t blue =
        static_cast<uint8_t>(std::clamp(std::lround(static_cast<float>(brightness) * tintBlue / 255.0f), 0l, 255l));
    return 0xff000000u
        | (static_cast<uint32_t>(blue) << 16)
        | (static_cast<uint32_t>(green) << 8)
        | static_cast<uint32_t>(red);
}

bx::Vec3 approximateOutdoorTerrainNormal(const OutdoorMapData &outdoorMapData, float x, float y)
{
    constexpr float SampleOffset = 32.0f;
    const float heightLeft = sampleOutdoorTerrainHeight(outdoorMapData, x - SampleOffset, y);
    const float heightRight = sampleOutdoorTerrainHeight(outdoorMapData, x + SampleOffset, y);
    const float heightDown = sampleOutdoorTerrainHeight(outdoorMapData, x, y - SampleOffset);
    const float heightUp = sampleOutdoorTerrainHeight(outdoorMapData, x, y + SampleOffset);
    const bx::Vec3 normal = {
        heightLeft - heightRight,
        heightDown - heightUp,
        SampleOffset * 2.0f
    };
    const float lengthSquared = normal.x * normal.x + normal.y * normal.y + normal.z * normal.z;

    if (lengthSquared <= 0.0001f)
    {
        return {0.0f, 0.0f, 1.0f};
    }

    const float inverseLength = 1.0f / std::sqrt(lengthSquared);
    return {normal.x * inverseLength, normal.y * inverseLength, normal.z * inverseLength};
}

float worldItemFloorHeight(const OutdoorMapData &outdoorMapData, float x, float y, float z)
{
    const float supportHeight = sampleOutdoorPlacementFloorHeight(outdoorMapData, x, y, z);
    const float renderedTerrainHeight = sampleOutdoorRenderedTerrainHeight(outdoorMapData, x, y);
    return std::max(supportHeight, renderedTerrainHeight) + WorldItemGroundClearance;
}

uint32_t makeAbgr(uint8_t red, uint8_t green, uint8_t blue)
{
    return 0xff000000u
        | (static_cast<uint32_t>(blue) << 16)
        | (static_cast<uint32_t>(green) << 8)
        | static_cast<uint32_t>(red);
}

float secondsFromHours(float hours)
{
    return hours * 3600.0f;
}

float secondsFromMinutes(float minutes)
{
    return minutes * 60.0f;
}

SkillMastery normalizeEventSkillMastery(uint32_t rawSkillMastery)
{
    if (rawSkillMastery >= static_cast<uint32_t>(SkillMastery::Grandmaster))
    {
        return SkillMastery::Grandmaster;
    }

    return static_cast<SkillMastery>(rawSkillMastery);
}

float resolveEventPartyBuffDurationSeconds(uint32_t spellId, uint32_t skillLevel, SkillMastery mastery)
{
    switch (spellIdFromValue(spellId))
    {
        case SpellId::TorchLight:
        case SpellId::WizardEye:
        case SpellId::Invisibility:
        case SpellId::Fly:
        case SpellId::WaterWalk:
        case SpellId::DetectLife:
        case SpellId::ProtectionFromMagic:
        case SpellId::Glamour:
        case SpellId::FireResistance:
        case SpellId::AirResistance:
        case SpellId::WaterResistance:
        case SpellId::EarthResistance:
        case SpellId::MindResistance:
        case SpellId::BodyResistance:
            return secondsFromHours(static_cast<float>(skillLevel));

        case SpellId::FeatherFall:
            if (mastery == SkillMastery::Normal)
            {
                return secondsFromMinutes(static_cast<float>(5 * skillLevel));
            }

            if (mastery == SkillMastery::Expert)
            {
                return secondsFromMinutes(static_cast<float>(10 * skillLevel));
            }

            return secondsFromHours(static_cast<float>(skillLevel));

        case SpellId::Haste:
            if (mastery == SkillMastery::Expert)
            {
                return secondsFromHours(1.0f) + secondsFromMinutes(static_cast<float>(skillLevel));
            }

            if (mastery == SkillMastery::Master)
            {
                return secondsFromHours(1.0f) + secondsFromMinutes(static_cast<float>(3 * skillLevel));
            }

            return secondsFromHours(1.0f) + secondsFromMinutes(static_cast<float>(4 * skillLevel));

        case SpellId::Shield:
        case SpellId::StoneSkin:
        case SpellId::Heroism:
            if (mastery == SkillMastery::Expert)
            {
                return secondsFromHours(1.0f) + secondsFromMinutes(static_cast<float>(5 * skillLevel));
            }

            if (mastery == SkillMastery::Master)
            {
                return secondsFromHours(1.0f) + secondsFromMinutes(static_cast<float>(15 * skillLevel));
            }

            return secondsFromHours(static_cast<float>(skillLevel + 1));

        case SpellId::Immolation:
            return mastery == SkillMastery::Grandmaster
                ? secondsFromMinutes(static_cast<float>(10 * skillLevel))
                : secondsFromMinutes(static_cast<float>(skillLevel));

        case SpellId::Levitate:
            return mastery == SkillMastery::Expert
                ? secondsFromMinutes(static_cast<float>(10 * skillLevel))
                : mastery == SkillMastery::Master
                ? secondsFromHours(static_cast<float>(skillLevel))
                : secondsFromHours(static_cast<float>(3 * skillLevel));

        case SpellId::DayOfGods:
            return mastery == SkillMastery::Expert
                ? secondsFromHours(static_cast<float>(3 * skillLevel))
                : mastery == SkillMastery::Master
                ? secondsFromHours(static_cast<float>(4 * skillLevel))
                : secondsFromHours(static_cast<float>(5 * skillLevel));

        case SpellId::DayOfProtection:
            return mastery == SkillMastery::Master
                ? secondsFromHours(static_cast<float>(4 * skillLevel))
                : secondsFromHours(static_cast<float>(5 * skillLevel));

        case SpellId::HourOfPower:
            return mastery == SkillMastery::Master
                ? secondsFromHours(1.0f) + secondsFromMinutes(static_cast<float>(15 * 4 * skillLevel))
                : secondsFromHours(1.0f) + secondsFromMinutes(static_cast<float>(15 * 5 * skillLevel));

        case SpellId::TravelersBoon:
            return mastery == SkillMastery::Expert
                ? secondsFromMinutes(static_cast<float>(30 * skillLevel))
                : mastery == SkillMastery::Master
                ? secondsFromHours(static_cast<float>(skillLevel))
                : secondsFromHours(static_cast<float>(2 * skillLevel));

        case SpellId::Flight:
            return mastery == SkillMastery::Grandmaster
                ? secondsFromHours(24.0f)
                : secondsFromHours(static_cast<float>(skillLevel));

        default:
            return 0.0f;
    }
}

int resolveEventPartyBuffPower(uint32_t spellId, uint32_t skillLevel, SkillMastery mastery)
{
    switch (spellIdFromValue(spellId))
    {
        case SpellId::TorchLight:
            return mastery == SkillMastery::Normal ? 2 : mastery == SkillMastery::Expert ? 3 : 4;

        case SpellId::FireResistance:
        case SpellId::AirResistance:
        case SpellId::WaterResistance:
        case SpellId::EarthResistance:
        case SpellId::MindResistance:
        case SpellId::BodyResistance:
            return mastery == SkillMastery::Normal
                ? static_cast<int>(skillLevel)
                : mastery == SkillMastery::Expert
                ? static_cast<int>(2 * skillLevel)
                : mastery == SkillMastery::Master
                ? static_cast<int>(3 * skillLevel)
                : static_cast<int>(4 * skillLevel);

        case SpellId::StoneSkin:
        case SpellId::Heroism:
            return static_cast<int>(skillLevel) + 5;

        case SpellId::ProtectionFromMagic:
        case SpellId::Immolation:
            return static_cast<int>(skillLevel);

        case SpellId::DayOfGods:
            return mastery == SkillMastery::Expert
                ? static_cast<int>(3 * skillLevel + 10)
                : mastery == SkillMastery::Master
                ? static_cast<int>(4 * skillLevel + 10)
                : static_cast<int>(5 * skillLevel + 10);

        case SpellId::DayOfProtection:
            return mastery == SkillMastery::Master
                ? static_cast<int>(4 * skillLevel)
                : static_cast<int>(5 * skillLevel);

        case SpellId::HourOfPower:
            return static_cast<int>(skillLevel) + 5;

        case SpellId::Glamour:
            return mastery == SkillMastery::Grandmaster
                ? static_cast<int>(3 * skillLevel)
                : static_cast<int>(2 * skillLevel);

        default:
            return 0;
    }
}

bool applyCompositeEventPartyBuff(Party &party, uint32_t spellId, uint32_t skillLevel, SkillMastery mastery)
{
    const float durationSeconds = resolveEventPartyBuffDurationSeconds(spellId, skillLevel, mastery);
    const int power = resolveEventPartyBuffPower(spellId, skillLevel, mastery);

    switch (spellIdFromValue(spellId))
    {
        case SpellId::DayOfProtection:
            party.applyPartyBuff(PartyBuffId::BodyResistance, durationSeconds, power, spellId, skillLevel, mastery, 0);
            party.applyPartyBuff(PartyBuffId::MindResistance, durationSeconds, power, spellId, skillLevel, mastery, 0);
            party.applyPartyBuff(PartyBuffId::FireResistance, durationSeconds, power, spellId, skillLevel, mastery, 0);
            party.applyPartyBuff(PartyBuffId::WaterResistance, durationSeconds, power, spellId, skillLevel, mastery, 0);
            party.applyPartyBuff(PartyBuffId::AirResistance, durationSeconds, power, spellId, skillLevel, mastery, 0);
            party.applyPartyBuff(PartyBuffId::EarthResistance, durationSeconds, power, spellId, skillLevel, mastery, 0);
            party.applyPartyBuff(PartyBuffId::FeatherFall, durationSeconds, 0, spellId, skillLevel, mastery, 0);
            party.applyPartyBuff(PartyBuffId::WizardEye, durationSeconds, 0, spellId, skillLevel, mastery, 0);
            return true;

        case SpellId::HourOfPower:
        {
            const float hasteDurationSeconds = mastery == SkillMastery::Master
                ? secondsFromHours(1.0f) + secondsFromMinutes(static_cast<float>(3 * 4 * skillLevel))
                : secondsFromHours(1.0f) + secondsFromMinutes(static_cast<float>(4 * 5 * skillLevel));

            party.applyPartyBuff(PartyBuffId::Heroism, durationSeconds, power, spellId, skillLevel, mastery, 0);
            party.applyPartyBuff(PartyBuffId::Shield, durationSeconds, 0, spellId, skillLevel, mastery, 0);
            party.applyPartyBuff(PartyBuffId::Stoneskin, durationSeconds, power, spellId, skillLevel, mastery, 0);

            bool anyWeak = false;

            for (const Character &member : party.members())
            {
                if (member.conditions.test(static_cast<size_t>(CharacterCondition::Weak)))
                {
                    anyWeak = true;
                    break;
                }
            }

            if (!anyWeak)
            {
                party.applyPartyBuff(PartyBuffId::Haste, hasteDurationSeconds, 0, spellId, skillLevel, mastery, 0);
            }

            for (size_t memberIndex = 0; memberIndex < party.members().size(); ++memberIndex)
            {
                party.applyCharacterBuff(
                    memberIndex,
                    CharacterBuffId::Bless,
                    durationSeconds,
                    power,
                    spellIdValue(SpellId::Bless),
                    static_cast<uint32_t>(power),
                    mastery,
                    0);
            }

            return true;
        }

        case SpellId::TravelersBoon:
            party.applyPartyBuff(PartyBuffId::TorchLight, durationSeconds, 3, spellId, skillLevel, mastery, 0);
            party.applyPartyBuff(PartyBuffId::WizardEye, durationSeconds, 0, spellId, skillLevel, mastery, 0);
            party.applyPartyBuff(PartyBuffId::FeatherFall, durationSeconds, 0, spellId, skillLevel, mastery, 0);
            return true;

        case SpellId::Levitate:
            party.applyPartyBuff(PartyBuffId::Levitate, durationSeconds, 0, spellId, skillLevel, mastery, 0);
            party.applyPartyBuff(PartyBuffId::WaterWalk, durationSeconds, 0, spellId, skillLevel, mastery, 0);
            party.applyPartyBuff(PartyBuffId::FeatherFall, durationSeconds, 0, spellId, skillLevel, mastery, 0);
            return true;

        default:
            return false;
    }
}

float resolveEventCharacterBuffDurationSeconds(uint32_t spellId, uint32_t skillLevel, SkillMastery mastery)
{
    switch (spellIdFromValue(spellId))
    {
        case SpellId::Bless:
            return mastery == SkillMastery::Normal
                ? secondsFromHours(1.0f) + secondsFromMinutes(static_cast<float>(5 * skillLevel))
                : mastery == SkillMastery::Expert
                ? secondsFromHours(1.0f) + secondsFromMinutes(static_cast<float>(5 * skillLevel))
                : mastery == SkillMastery::Master
                ? secondsFromHours(1.0f) + secondsFromMinutes(static_cast<float>(15 * skillLevel))
                : secondsFromHours(1.0f + static_cast<float>(skillLevel));

        case SpellId::Preservation:
            return mastery == SkillMastery::Expert
                ? secondsFromHours(1.0f) + secondsFromMinutes(static_cast<float>(5 * skillLevel))
                : mastery == SkillMastery::Master
                ? secondsFromHours(1.0f) + secondsFromMinutes(static_cast<float>(5 * skillLevel))
                : mastery == SkillMastery::Grandmaster
                ? secondsFromHours(1.0f) + secondsFromMinutes(static_cast<float>(15 * skillLevel))
                : secondsFromHours(1.0f) + secondsFromMinutes(static_cast<float>(15 * skillLevel));

        default:
            return 0.0f;
    }
}

bool tryApplyEventCharacterBuff(Party &party, uint32_t spellId, uint32_t skillLevel, uint32_t rawSkillMastery)
{
    const SkillMastery mastery = normalizeEventSkillMastery(rawSkillMastery);
    const float durationSeconds = resolveEventCharacterBuffDurationSeconds(spellId, skillLevel, mastery);

    if (durationSeconds <= 0.0f)
    {
        return false;
    }

    switch (spellIdFromValue(spellId))
    {
        case SpellId::Bless:
            if (mastery == SkillMastery::Normal)
            {
                return false;
            }

            for (size_t memberIndex = 0; memberIndex < party.members().size(); ++memberIndex)
            {
                party.applyCharacterBuff(
                    memberIndex,
                    CharacterBuffId::Bless,
                    durationSeconds,
                    5 + static_cast<int>(skillLevel),
                    spellId,
                    skillLevel,
                    mastery,
                    0);
            }

            return true;

        case SpellId::Preservation:
            if (mastery == SkillMastery::Master || mastery == SkillMastery::Grandmaster)
            {
                for (size_t memberIndex = 0; memberIndex < party.members().size(); ++memberIndex)
                {
                    party.applyCharacterBuff(
                        memberIndex,
                        CharacterBuffId::Preservation,
                        durationSeconds,
                        0,
                        spellId,
                        skillLevel,
                        mastery,
                        0);
                }

                return true;
            }

            return false;

        default:
            return false;
    }
}

bool tryApplyEventPartyBuff(Party &party, uint32_t spellId, uint32_t skillLevel, uint32_t rawSkillMastery)
{
    const SkillMastery mastery = normalizeEventSkillMastery(rawSkillMastery);
    const float durationSeconds = resolveEventPartyBuffDurationSeconds(spellId, skillLevel, mastery);

    if (durationSeconds <= 0.0f)
    {
        return false;
    }

    switch (spellIdFromValue(spellId))
    {
        case SpellId::DayOfProtection:
        case SpellId::HourOfPower:
        case SpellId::TravelersBoon:
        case SpellId::Levitate:
            return applyCompositeEventPartyBuff(party, spellId, skillLevel, mastery);

        case SpellId::TorchLight:
            party.applyPartyBuff(PartyBuffId::TorchLight, durationSeconds, 3, spellId, skillLevel, mastery, 0);
            return true;

        case SpellId::WizardEye:
            party.applyPartyBuff(PartyBuffId::WizardEye, durationSeconds, 0, spellId, skillLevel, mastery, 0);
            return true;

        case SpellId::FeatherFall:
            party.applyPartyBuff(PartyBuffId::FeatherFall, durationSeconds, 0, spellId, skillLevel, mastery, 0);
            return true;

        case SpellId::Haste:
            party.applyPartyBuff(PartyBuffId::Haste, durationSeconds, 0, spellId, skillLevel, mastery, 0);
            return true;

        case SpellId::Immolation:
            party.applyPartyBuff(
                PartyBuffId::Immolation,
                durationSeconds,
                resolveEventPartyBuffPower(spellId, skillLevel, mastery),
                spellId,
                skillLevel,
                mastery,
                0);
            return true;

        case SpellId::Shield:
            party.applyPartyBuff(PartyBuffId::Shield, durationSeconds, 0, spellId, skillLevel, mastery, 0);
            return true;

        case SpellId::FireResistance:
            party.applyPartyBuff(
                PartyBuffId::FireResistance,
                durationSeconds,
                resolveEventPartyBuffPower(spellId, skillLevel, mastery),
                spellId,
                skillLevel,
                mastery,
                0);
            return true;

        case SpellId::AirResistance:
            party.applyPartyBuff(
                PartyBuffId::AirResistance,
                durationSeconds,
                resolveEventPartyBuffPower(spellId, skillLevel, mastery),
                spellId,
                skillLevel,
                mastery,
                0);
            return true;

        case SpellId::WaterResistance:
            party.applyPartyBuff(
                PartyBuffId::WaterResistance,
                durationSeconds,
                resolveEventPartyBuffPower(spellId, skillLevel, mastery),
                spellId,
                skillLevel,
                mastery,
                0);
            return true;

        case SpellId::EarthResistance:
            party.applyPartyBuff(
                PartyBuffId::EarthResistance,
                durationSeconds,
                resolveEventPartyBuffPower(spellId, skillLevel, mastery),
                spellId,
                skillLevel,
                mastery,
                0);
            return true;

        case SpellId::DayOfGods:
            party.applyPartyBuff(
                PartyBuffId::DayOfGods,
                durationSeconds,
                resolveEventPartyBuffPower(spellId, skillLevel, mastery),
                spellId,
                skillLevel,
                mastery,
                0);
            return true;

        case SpellId::Heroism:
            party.applyPartyBuff(
                PartyBuffId::Heroism,
                durationSeconds,
                resolveEventPartyBuffPower(spellId, skillLevel, mastery),
                spellId,
                skillLevel,
                mastery,
                0);
            return true;

        case SpellId::MindResistance:
            party.applyPartyBuff(
                PartyBuffId::MindResistance,
                durationSeconds,
                resolveEventPartyBuffPower(spellId, skillLevel, mastery),
                spellId,
                skillLevel,
                mastery,
                0);
            return true;

        case SpellId::BodyResistance:
            party.applyPartyBuff(
                PartyBuffId::BodyResistance,
                durationSeconds,
                resolveEventPartyBuffPower(spellId, skillLevel, mastery),
                spellId,
                skillLevel,
                mastery,
                0);
            return true;

        case SpellId::StoneSkin:
            party.applyPartyBuff(
                PartyBuffId::Stoneskin,
                durationSeconds,
                resolveEventPartyBuffPower(spellId, skillLevel, mastery),
                spellId,
                skillLevel,
                mastery,
                0);
            return true;

        case SpellId::ProtectionFromMagic:
            party.applyPartyBuff(
                PartyBuffId::ProtectionFromMagic,
                durationSeconds,
                resolveEventPartyBuffPower(spellId, skillLevel, mastery),
                spellId,
                skillLevel,
                mastery,
                0);
            return true;

        case SpellId::Invisibility:
            party.applyPartyBuff(PartyBuffId::Invisibility, durationSeconds, 0, spellId, skillLevel, mastery, 0);
            return true;

        case SpellId::Fly:
            party.applyPartyBuff(PartyBuffId::Fly, durationSeconds, 0, spellId, skillLevel, mastery, 0);
            return true;

        case SpellId::WaterWalk:
            party.applyPartyBuff(PartyBuffId::WaterWalk, durationSeconds, 0, spellId, skillLevel, mastery, 0);
            return true;

        case SpellId::DetectLife:
            party.applyPartyBuff(PartyBuffId::DetectLife, durationSeconds, 0, spellId, skillLevel, mastery, 0);
            return true;

        case SpellId::Glamour:
            party.applyPartyBuff(
                PartyBuffId::Glamour,
                durationSeconds,
                resolveEventPartyBuffPower(spellId, skillLevel, mastery),
                spellId,
                skillLevel,
                mastery,
                0);
            return true;

        default:
            return false;
    }
}

std::vector<size_t> buildAllPartyMemberIndices(const Party &party)
{
    std::vector<size_t> memberIndices;
    memberIndices.reserve(party.members().size());

    for (size_t memberIndex = 0; memberIndex < party.members().size(); ++memberIndex)
    {
        memberIndices.push_back(memberIndex);
    }

    return memberIndices;
}

std::string resolveFallbackSkyTextureName(const MapStatsEntry &map, const std::optional<OutdoorMapData> &outdoorMapData)
{
    if (outdoorMapData && !outdoorMapData->skyTexture.empty())
    {
        return toLowerCopy(outdoorMapData->skyTexture);
    }

    const std::string environmentName = toLowerCopy(map.environmentName);

    if (environmentName == "plains" || environmentName == "forest" || environmentName == "city")
    {
        return "plansky3";
    }

    if (environmentName == "underwater")
    {
        return "sky01";
    }

    return "plansky1";
}

bool isGenericSkySourceTextureName(const std::string &textureName)
{
    if (textureName.empty())
    {
        return true;
    }

    if (textureName.starts_with("plansky"))
    {
        return true;
    }

    return textureName == "sky01"
        || textureName == "sky03"
        || textureName == "sky04"
        || textureName == "sky05"
        || textureName == "sky06"
        || textureName == "cloudsabove";
}

std::string resolveRenderedSkyTextureName(const std::string &sourceSkyTextureName, float minutesOfDay)
{
    const std::string normalizedSourceSkyTextureName = toLowerCopy(sourceSkyTextureName);

    if (!isGenericSkySourceTextureName(normalizedSourceSkyTextureName))
    {
        return normalizedSourceSkyTextureName;
    }

    if (minutesOfDay >= 1200.0f && minutesOfDay < 1260.0f)
    {
        return "sunsetclouds";
    }

    if (minutesOfDay >= 1260.0f || minutesOfDay < 300.0f)
    {
        return "sky6pm";
    }

    if (minutesOfDay >= 300.0f && minutesOfDay < 360.0f)
    {
        return "sunsetclouds";
    }

    if (normalizedSourceSkyTextureName.starts_with("plansky") || normalizedSourceSkyTextureName.empty())
    {
        return "sky05";
    }

    return normalizedSourceSkyTextureName;
}

OutdoorWorldRuntime::AtmosphereState buildAtmosphereSourceState(
    const MapStatsEntry &map,
    const std::optional<OutdoorMapData> &outdoorMapData,
    const std::optional<MapDeltaData> &outdoorMapDeltaData)
{
    OutdoorWorldRuntime::AtmosphereState result = {};

    if (outdoorMapDeltaData)
    {
        result.sourceSkyTextureName = toLowerCopy(outdoorMapDeltaData->locationTime.skyTextureName);
        result.weatherFlags = outdoorMapDeltaData->locationTime.weatherFlags;
        result.fogWeakDistance = outdoorMapDeltaData->locationTime.fogWeakDistance;
        result.fogStrongDistance = outdoorMapDeltaData->locationTime.fogStrongDistance;
    }

    if (result.sourceSkyTextureName.empty())
    {
        result.sourceSkyTextureName = resolveFallbackSkyTextureName(map, outdoorMapData);
    }

    result.skyTextureName = result.sourceSkyTextureName;

    return result;
}

bool hasConfiguredFogState(const OutdoorWorldRuntime::AtmosphereState &atmosphereState)
{
    return (atmosphereState.weatherFlags & MapWeatherFoggy) != 0
        || atmosphereState.fogWeakDistance != 0
        || atmosphereState.fogStrongDistance != 0;
}

OutdoorFogDistances fallbackFogDistancesForProfile(const OutdoorWeatherProfile &profile)
{
    if (profile.defaultFog.strongDistance > 0)
    {
        return profile.defaultFog;
    }

    if (profile.redFog)
    {
        return profile.denseFog.strongDistance > 0 ? profile.denseFog : OutdoorFogDistances{0, 2048};
    }

    if (profile.underwater)
    {
        return profile.averageFog.strongDistance > 0 ? profile.averageFog : OutdoorFogDistances{0, 4096};
    }

    return profile.averageFog.strongDistance > 0 ? profile.averageFog : OutdoorFogDistances{0, 4096};
}

float normalizedAmbientBrightness(float minutesOfDay)
{
    const float ambient =
        0.15f + (std::sin(((minutesOfDay - 360.0f) * 2.0f * Pi) / 1440.0f) + 1.0f) * 0.27f;
    return std::clamp(ambient, 0.15f, 0.69f);
}

bool readInt32FromBytes(const std::vector<uint8_t> &bytes, size_t offset, int32_t &value)
{
    if (offset + sizeof(value) > bytes.size())
    {
        return false;
    }

    std::memcpy(&value, bytes.data() + offset, sizeof(value));
    return true;
}

bool isGoldHeapItemId(uint32_t itemId)
{
    return itemId >= GoldHeapSmallItemId && itemId <= GoldHeapLargeItemId;
}

std::string debugStringOrNone(const std::string &value)
{
    if (value.empty())
    {
        return "<none>";
    }

    return value;
}

const char *monsterAttackAbilityName(OutdoorWorldRuntime::MonsterAttackAbility ability)
{
    switch (ability)
    {
        case OutdoorWorldRuntime::MonsterAttackAbility::Attack1:
            return "attack1";
        case OutdoorWorldRuntime::MonsterAttackAbility::Attack2:
            return "attack2";
        case OutdoorWorldRuntime::MonsterAttackAbility::Spell1:
            return "spell1";
        case OutdoorWorldRuntime::MonsterAttackAbility::Spell2:
            return "spell2";

        default:
            return "unknown";
    }
}

const char *spellSourceKindName(OutdoorWorldRuntime::RuntimeSpellSourceKind sourceKind)
{
    switch (sourceKind)
    {
        case OutdoorWorldRuntime::RuntimeSpellSourceKind::Actor:
            return "monster";
        case OutdoorWorldRuntime::RuntimeSpellSourceKind::Event:
            return "event";
        case OutdoorWorldRuntime::RuntimeSpellSourceKind::Party:
            return "party";
        default:
            return "unknown";
    }
}

const char *projectileSourceKindName(OutdoorWorldRuntime::ProjectileState::SourceKind sourceKind)
{
    switch (sourceKind)
    {
        case OutdoorWorldRuntime::ProjectileState::SourceKind::Actor:
            return "monster";
        case OutdoorWorldRuntime::ProjectileState::SourceKind::Event:
            return "event";
        case OutdoorWorldRuntime::ProjectileState::SourceKind::Party:
            return "party";
        default:
            return "unknown";
    }
}

GameplayProjectileService::ProjectileDefinition buildGameplayProjectileDefinition(
    const OutdoorWorldRuntime::ResolvedProjectileDefinition &definition,
    uint16_t objectSpriteFrameIndex)
{
    GameplayProjectileService::ProjectileDefinition result = {};
    result.objectDescriptionId = definition.objectDescriptionId;
    result.objectSpriteId = definition.objectSpriteId;
    result.objectSpriteFrameIndex = objectSpriteFrameIndex;
    result.impactObjectDescriptionId = definition.impactObjectDescriptionId;
    result.objectFlags = definition.objectFlags;
    result.radius = definition.radius;
    result.height = definition.height;
    result.spellId = definition.spellId;
    result.effectSoundId = definition.effectSoundId;
    result.lifetimeTicks = definition.lifetimeTicks;
    result.speed = definition.speed;
    result.objectName = definition.objectName;
    result.objectSpriteName = definition.objectSpriteName;
    return result;
}

OutdoorWorldRuntime::ProjectileState::SourceKind projectileSourceKindFromSpellSource(
    OutdoorWorldRuntime::RuntimeSpellSourceKind sourceKind)
{
    if (sourceKind == OutdoorWorldRuntime::RuntimeSpellSourceKind::Party)
    {
        return OutdoorWorldRuntime::ProjectileState::SourceKind::Party;
    }

    if (sourceKind == OutdoorWorldRuntime::RuntimeSpellSourceKind::Event)
    {
        return OutdoorWorldRuntime::ProjectileState::SourceKind::Event;
    }

    return OutdoorWorldRuntime::ProjectileState::SourceKind::Actor;
}

void logProjectileSpawn(
    const char *sourceKind,
    const OutdoorWorldRuntime::ProjectileState &projectile,
    float directionX,
    float directionY,
    float directionZ,
    float speed)
{
    if (!DebugProjectileSpawnLogging)
    {
        return;
    }

    std::cout
        << "Projectile spawn kind=" << sourceKind
        << " projectile=" << projectile.projectileId
        << " source=" << projectile.sourceId
        << " ability=" << monsterAttackAbilityName(projectile.ability)
        << " object=\"" << debugStringOrNone(projectile.objectName) << "\""
        << " sprite=\"" << debugStringOrNone(projectile.objectSpriteName) << "\""
        << " spriteId=" << projectile.objectSpriteId
        << " pos=(" << projectile.x << ", " << projectile.y << ", " << projectile.z << ")"
        << " dir=(" << directionX << ", " << directionY << ", " << directionZ << ")"
        << " speed=" << speed
        << " velocity=(" << projectile.velocityX << ", " << projectile.velocityY << ", " << projectile.velocityZ << ")"
        << " radius=" << projectile.radius
        << " height=" << projectile.height
        << " lifetimeTicks=" << projectile.lifetimeTicks
        << " spellId=" << projectile.spellId
        << '\n';
}

void logProjectileCollision(
    const OutdoorWorldRuntime::ProjectileState &projectile,
    const char *colliderKind,
    const std::string &colliderName,
    const bx::Vec3 &point)
{
    if (!DebugProjectileCollisionLogging)
    {
        return;
    }

    std::cout
        << "Projectile collision projectile=" << projectile.projectileId
        << " source=" << projectile.sourceId
        << " ability=" << monsterAttackAbilityName(projectile.ability)
        << " object=\"" << debugStringOrNone(projectile.objectName) << "\""
        << " sprite=\"" << debugStringOrNone(projectile.objectSpriteName) << "\""
        << " collider=" << colliderKind
        << " target=\"" << debugStringOrNone(colliderName) << "\""
        << " pos=(" << point.x << ", " << point.y << ", " << point.z << ")"
        << '\n';
}

void logProjectileLifetimeExpiry(const OutdoorWorldRuntime::ProjectileState &projectile)
{
    if (!DebugProjectileLifetimeLogging)
    {
        return;
    }

    std::cout
        << "Projectile expired projectile=" << projectile.projectileId
        << " source=" << projectile.sourceId
        << " ability=" << monsterAttackAbilityName(projectile.ability)
        << " object=\"" << debugStringOrNone(projectile.objectName) << "\""
        << " sprite=\"" << debugStringOrNone(projectile.objectSpriteName) << "\""
        << " pos=(" << projectile.x << ", " << projectile.y << ", " << projectile.z << ")"
        << " lifetimeTicks=" << projectile.lifetimeTicks
        << " ageTicks=" << projectile.timeSinceCreatedTicks
        << '\n';
}

void logProjectileImpactEffect(
    const OutdoorWorldRuntime::ProjectileState &projectile,
    const OutdoorWorldRuntime::ProjectileImpactState &effect)
{
    if (!DebugProjectileImpactLogging)
    {
        return;
    }

    std::cout
        << "Projectile impact effect projectile=" << projectile.projectileId
        << " effect=" << effect.effectId
        << " object=\"" << debugStringOrNone(effect.objectName) << "\""
        << " sprite=\"" << debugStringOrNone(effect.objectSpriteName) << "\""
        << " spriteId=" << effect.objectSpriteId
        << " pos=(" << effect.x << ", " << effect.y << ", " << effect.z << ")"
        << '\n';
}

void logProjectileAoeHit(
    const OutdoorWorldRuntime::ProjectileState &projectile,
    const char *pTargetKind,
    const bx::Vec3 &impactPoint,
    float radius)
{
    if (!DebugProjectileAoeLogging)
    {
        return;
    }

    std::cout
        << "Projectile aoe hit projectile=" << projectile.projectileId
        << " source=" << projectile.sourceId
        << " ability=" << monsterAttackAbilityName(projectile.ability)
        << " object=\"" << debugStringOrNone(projectile.objectName) << "\""
        << " sprite=\"" << debugStringOrNone(projectile.objectSpriteName) << "\""
        << " spellId=" << projectile.spellId
        << " target=" << pTargetKind
        << " radius=" << radius
        << " pos=(" << impactPoint.x << ", " << impactPoint.y << ", " << impactPoint.z << ")"
        << '\n';
}

float clampLength(float value, float maxValue)
{
    if (value > maxValue)
    {
        return maxValue;
    }

    if (value < -maxValue)
    {
        return -maxValue;
    }

    return value;
}

float length2d(float x, float y)
{
    return std::sqrt(x * x + y * y);
}

float length3d(float x, float y, float z)
{
    return std::sqrt(x * x + y * y + z * z);
}

float pointSegmentDistanceSquared2d(
    float pointX,
    float pointY,
    float segmentStartX,
    float segmentStartY,
    float segmentEndX,
    float segmentEndY,
    float &projectionFactor)
{
    const float segmentDeltaX = segmentEndX - segmentStartX;
    const float segmentDeltaY = segmentEndY - segmentStartY;
    const float segmentLengthSquared = segmentDeltaX * segmentDeltaX + segmentDeltaY * segmentDeltaY;

    if (segmentLengthSquared <= 0.0001f)
    {
        projectionFactor = 0.0f;
        const float deltaX = pointX - segmentStartX;
        const float deltaY = pointY - segmentStartY;
        return deltaX * deltaX + deltaY * deltaY;
    }

    projectionFactor =
        ((pointX - segmentStartX) * segmentDeltaX + (pointY - segmentStartY) * segmentDeltaY) / segmentLengthSquared;
    projectionFactor = std::clamp(projectionFactor, 0.0f, 1.0f);
    const float closestX = segmentStartX + segmentDeltaX * projectionFactor;
    const float closestY = segmentStartY + segmentDeltaY * projectionFactor;
    const float deltaX = pointX - closestX;
    const float deltaY = pointY - closestY;
    return deltaX * deltaX + deltaY * deltaY;
}

float normalizeAngleRadians(float angle)
{
    while (angle <= -Pi)
    {
        angle += 2.0f * Pi;
    }

    while (angle > Pi)
    {
        angle -= 2.0f * Pi;
    }

    return angle;
}

uint32_t inactiveActorDecisionSeed(uint32_t actorId, uint32_t counter, uint32_t salt)
{
    return static_cast<uint32_t>(actorId + 1) * 1103515245u
        + counter * 2654435761u
        + salt;
}

float shortestAngleDistanceRadians(float left, float right)
{
    return std::abs(normalizeAngleRadians(left - right));
}

float lengthSquared3d(float x, float y, float z)
{
    return x * x + y * y + z * z;
}

void faceDirection(OutdoorWorldRuntime::MapActorState &actor, float deltaX, float deltaY);

bool isWithinRange3d(float x, float y, float z, float range)
{
    return range > 0.0f && lengthSquared3d(x, y, z) <= range * range;
}

bool isOutdoorLandMaskWater(const std::optional<std::vector<uint8_t>> &outdoorLandMask, float x, float y)
{
    if (!outdoorLandMask || outdoorLandMask->empty())
    {
        return false;
    }

    const float gridX = outdoorWorldToGridXFloat(x);
    const float gridY = outdoorWorldToGridYFloat(y);
    const int tileX = std::clamp(static_cast<int>(std::floor(gridX)), 0, OutdoorMapData::TerrainWidth - 2);
    const int tileY = std::clamp(static_cast<int>(std::floor(gridY)), 0, OutdoorMapData::TerrainHeight - 2);
    const int landMaskWidth = OutdoorMapData::TerrainWidth - 1;
    const size_t tileIndex = static_cast<size_t>(tileY * landMaskWidth + tileX);

    if (tileIndex >= outdoorLandMask->size())
    {
        return false;
    }

    return (*outdoorLandMask)[tileIndex] == 0;
}

bool isOutdoorMonsterWaterTile(
    const OutdoorMapData &outdoorMapData,
    const std::optional<std::vector<uint8_t>> &outdoorLandMask,
    float x,
    float y)
{
    return isOutdoorTerrainWater(outdoorMapData, x, y) || isOutdoorLandMaskWater(outdoorLandMask, x, y);
}

bool canMonsterWalkOnWater(const MonsterTable::MonsterStatsEntry *pStats)
{
    if (pStats == nullptr)
    {
        return false;
    }

    return toLowerCopy(pStats->pictureName).find("water elemental") != std::string::npos;
}

bx::Vec3 outdoorTerrainTileCenter(int tileX, int tileY)
{
    return {
        outdoorGridCornerWorldX(tileX) + static_cast<float>(OutdoorMapData::TerrainTileSize) * 0.5f,
        outdoorGridCornerWorldY(tileY) - static_cast<float>(OutdoorMapData::TerrainTileSize) * 0.5f,
        0.0f
    };
}

bool findNearbyLandDirection(
    const OutdoorMapData &outdoorMapData,
    const std::optional<std::vector<uint8_t>> &outdoorLandMask,
    float actorX,
    float actorY,
    float &directionX,
    float &directionY)
{
    const float gridX = 64.0f - (actorX / static_cast<float>(OutdoorMapData::TerrainTileSize));
    const float gridY = 64.0f - (actorY / static_cast<float>(OutdoorMapData::TerrainTileSize));
    const int tileX = std::clamp(static_cast<int>(std::floor(gridX)), 0, OutdoorMapData::TerrainWidth - 2);
    const int tileY = std::clamp(static_cast<int>(std::floor(gridY)), 0, OutdoorMapData::TerrainHeight - 2);
    float bestDistanceSquared = std::numeric_limits<float>::max();
    bool found = false;

    for (int candidateY = tileY - 1; candidateY <= tileY + 1; ++candidateY)
    {
        if (candidateY < 0 || candidateY >= OutdoorMapData::TerrainHeight - 1)
        {
            continue;
        }

        for (int candidateX = tileX - 1; candidateX <= tileX + 1; ++candidateX)
        {
            if (candidateX < 0 || candidateX >= OutdoorMapData::TerrainWidth - 1)
            {
                continue;
            }

            const bx::Vec3 center = outdoorTerrainTileCenter(candidateX, candidateY);

            if (isOutdoorMonsterWaterTile(outdoorMapData, outdoorLandMask, center.x, center.y))
            {
                continue;
            }

            const float deltaX = center.x - actorX;
            const float deltaY = center.y - actorY;
            const float distanceSquared = deltaX * deltaX + deltaY * deltaY;

            if (distanceSquared >= bestDistanceSquared || distanceSquared <= 0.01f)
            {
                continue;
            }

            bestDistanceSquared = distanceSquared;
            directionX = deltaX;
            directionY = deltaY;
            found = true;
        }
    }

    if (!found)
    {
        return false;
    }

    const float distance = length2d(directionX, directionY);

    if (distance <= 0.01f)
    {
        return false;
    }

    directionX /= distance;
    directionY /= distance;
    return true;
}

enum class OutdoorWaterRestrictionResult
{
    None,
    RedirectedToLand,
    BlockedByWater,
};

void rotateDirectionClockwise(float &directionX, float &directionY, float radians)
{
    const float cosine = std::cos(radians);
    const float sine = std::sin(radians);
    const float rotatedX = directionX * cosine + directionY * sine;
    const float rotatedY = -directionX * sine + directionY * cosine;
    directionX = rotatedX;
    directionY = rotatedY;
}

OutdoorWaterRestrictionResult applyOutdoorWaterRestriction(
    const OutdoorMapData &outdoorMapData,
    const std::optional<std::vector<uint8_t>> &outdoorLandMask,
    const MonsterTable::MonsterStatsEntry *pStats,
    OutdoorWorldRuntime::MapActorState &actor,
    float moveSpeed,
    float &desiredMoveX,
    float &desiredMoveY,
    OutdoorWorldRuntime::ActorAiState &nextAiState,
    OutdoorWorldRuntime::ActorAnimation &nextAnimation)
{
    if (pStats == nullptr
        || pStats->canFly
        || canMonsterWalkOnWater(pStats)
        || (std::abs(desiredMoveX) <= 0.001f && std::abs(desiredMoveY) <= 0.001f))
    {
        return OutdoorWaterRestrictionResult::None;
    }

    const bool onWater = isOutdoorMonsterWaterTile(outdoorMapData, outdoorLandMask, actor.preciseX, actor.preciseY);

    if (onWater)
    {
        float shoreDirectionX = 0.0f;
        float shoreDirectionY = 0.0f;

        if (!findNearbyLandDirection(
                outdoorMapData,
                outdoorLandMask,
                actor.preciseX,
                actor.preciseY,
                shoreDirectionX,
                shoreDirectionY))
        {
            desiredMoveX = 0.0f;
            desiredMoveY = 0.0f;
            return OutdoorWaterRestrictionResult::BlockedByWater;
        }

        desiredMoveX = shoreDirectionX;
        desiredMoveY = shoreDirectionY;
        faceDirection(actor, desiredMoveX, desiredMoveY);
        nextAiState = OutdoorWorldRuntime::ActorAiState::Fleeing;
        nextAnimation = OutdoorWorldRuntime::ActorAnimation::Walking;
        return OutdoorWaterRestrictionResult::RedirectedToLand;
    }

    const float moveDeltaX = desiredMoveX * moveSpeed * ActorUpdateStepSeconds;
    const float moveDeltaY = desiredMoveY * moveSpeed * ActorUpdateStepSeconds;
    const float candidateX = actor.preciseX + moveDeltaX;
    const float candidateY = actor.preciseY + moveDeltaY;

    if (!isOutdoorMonsterWaterTile(outdoorMapData, outdoorLandMask, candidateX, candidateY))
    {
        return OutdoorWaterRestrictionResult::None;
    }

    rotateDirectionClockwise(desiredMoveX, desiredMoveY, OeTurnAwayFromWaterAngleRadians);
    const float rotatedLength = length2d(desiredMoveX, desiredMoveY);

    if (rotatedLength > 0.01f)
    {
        desiredMoveX /= rotatedLength;
        desiredMoveY /= rotatedLength;
    }
    else
    {
        desiredMoveX = 0.0f;
        desiredMoveY = 0.0f;
    }

    const float rotatedCandidateX = actor.preciseX + desiredMoveX * moveSpeed * ActorUpdateStepSeconds;
    const float rotatedCandidateY = actor.preciseY + desiredMoveY * moveSpeed * ActorUpdateStepSeconds;

    if (length2d(desiredMoveX, desiredMoveY) <= 0.001f
        || isOutdoorMonsterWaterTile(outdoorMapData, outdoorLandMask, rotatedCandidateX, rotatedCandidateY))
    {
        desiredMoveX = 0.0f;
        desiredMoveY = 0.0f;
        return OutdoorWaterRestrictionResult::BlockedByWater;
    }

    faceDirection(actor, desiredMoveX, desiredMoveY);
    nextAiState = OutdoorWorldRuntime::ActorAiState::Fleeing;
    nextAnimation = OutdoorWorldRuntime::ActorAnimation::Walking;
    return OutdoorWaterRestrictionResult::RedirectedToLand;
}

void faceDirection(OutdoorWorldRuntime::MapActorState &actor, float deltaX, float deltaY)
{
    if (std::abs(deltaX) <= 0.01f && std::abs(deltaY) <= 0.01f)
    {
        return;
    }

    actor.yawRadians = std::atan2(deltaY, deltaX);
}

float monsterRecoverySeconds(int recoveryTicks)
{
    return std::max(0.3f, static_cast<float>(recoveryTicks) / TicksPerSecond * OeRealtimeRecoveryScale);
}

bool isProjectileSpellName(const std::string &spellName)
{
    static const std::vector<std::string> projectileSpellNames = {
        "fire bolt",
        "fireball",
        "incinerate",
        "lightning bolt",
        "ice bolt",
        "acid burst",
        "deadly swarm",
        "blades",
        "rock blast",
        "mind blast",
        "psychic shock",
        "harm",
        "light bolt",
        "toxic cloud",
        "dragon breath",
    };

    return std::find(projectileSpellNames.begin(), projectileSpellNames.end(), toLowerCopy(spellName))
        != projectileSpellNames.end();
}

bool resolveProjectileDefinition(
    const MonsterTable::MonsterStatsEntry &stats,
    OutdoorWorldRuntime::MonsterAttackAbility ability,
    const MonsterProjectileTable &projectileTable,
    const ObjectTable &objectTable,
    const SpellTable &spellTable,
    OutdoorWorldRuntime::ResolvedProjectileDefinition &definition)
{
    definition = {};

    if (ability == OutdoorWorldRuntime::MonsterAttackAbility::Attack1
        || ability == OutdoorWorldRuntime::MonsterAttackAbility::Attack2)
    {
        const std::string &projectileToken =
            ability == OutdoorWorldRuntime::MonsterAttackAbility::Attack1
                ? stats.attack1MissileType
                : stats.attack2MissileType;
        const MonsterProjectileEntry *pProjectileEntry = projectileTable.findByToken(projectileToken);

        if (pProjectileEntry == nullptr)
        {
            return false;
        }

        const ObjectEntry *pObjectEntry = objectTable.findByObjectId(static_cast<int16_t>(pProjectileEntry->objectId));

        if (pObjectEntry == nullptr)
        {
            return false;
        }

        const std::optional<uint16_t> objectDescriptionId =
            objectTable.findDescriptionIdByObjectId(static_cast<int16_t>(pProjectileEntry->objectId));

        if (!objectDescriptionId)
        {
            return false;
        }

        definition.objectDescriptionId = *objectDescriptionId;
        definition.objectSpriteId = pObjectEntry->spriteId;
        definition.objectFlags = pObjectEntry->flags;
        definition.radius = static_cast<uint16_t>(std::max<int>(pObjectEntry->radius, 16));
        definition.height = static_cast<uint16_t>(std::max<int>(pObjectEntry->height, 16));
        definition.lifetimeTicks = static_cast<uint32_t>(std::max<int>(pObjectEntry->lifetimeTicks, 64));
        definition.speed = static_cast<float>(std::max<int>(pObjectEntry->speed, 2000));
        definition.objectName = pObjectEntry->internalName;
        definition.objectSpriteName = pObjectEntry->spriteName;

        if (pProjectileEntry->impactObjectId > 0)
        {
            const ObjectEntry *pImpactEntry =
                objectTable.findByObjectId(static_cast<int16_t>(pProjectileEntry->impactObjectId));
            const std::optional<uint16_t> impactDescriptionId =
                objectTable.findDescriptionIdByObjectId(static_cast<int16_t>(pProjectileEntry->impactObjectId));

            if (pImpactEntry != nullptr && impactDescriptionId)
            {
                definition.impactObjectDescriptionId = *impactDescriptionId;
                definition.impactObjectSpriteId = pImpactEntry->spriteId;
                definition.impactObjectName = pImpactEntry->internalName;
                definition.impactObjectSpriteName = pImpactEntry->spriteName;
            }
        }

        return true;
    }

    const std::string &spellName =
        ability == OutdoorWorldRuntime::MonsterAttackAbility::Spell1 ? stats.spell1Name : stats.spell2Name;

    if (!isProjectileSpellName(spellName))
    {
        return false;
    }

    const SpellEntry *pSpellEntry = spellTable.findByName(spellName);

    if (pSpellEntry == nullptr || pSpellEntry->displayObjectId <= 0)
    {
        return false;
    }

    const ObjectEntry *pObjectEntry = objectTable.findByObjectId(static_cast<int16_t>(pSpellEntry->displayObjectId));
    const std::optional<uint16_t> objectDescriptionId =
        objectTable.findDescriptionIdByObjectId(static_cast<int16_t>(pSpellEntry->displayObjectId));

    if (pObjectEntry == nullptr || !objectDescriptionId)
    {
        return false;
    }

    definition.objectDescriptionId = *objectDescriptionId;
    definition.objectSpriteId = pObjectEntry->spriteId;
    definition.objectFlags = pObjectEntry->flags;
    definition.radius = static_cast<uint16_t>(std::max<int>(pObjectEntry->radius, 16));
    definition.height = static_cast<uint16_t>(std::max<int>(pObjectEntry->height, 16));
    definition.lifetimeTicks = static_cast<uint32_t>(std::max<int>(pObjectEntry->lifetimeTicks, 64));
    definition.speed = static_cast<float>(std::max<int>(pObjectEntry->speed, 2000));
    definition.spellId = pSpellEntry->id;
    definition.effectSoundId = pSpellEntry->effectSoundId;
    definition.objectName = pObjectEntry->internalName;
    definition.objectSpriteName = pObjectEntry->spriteName;

    if (pSpellEntry->impactDisplayObjectId > 0)
    {
        const ObjectEntry *pImpactEntry =
            objectTable.findByObjectId(static_cast<int16_t>(pSpellEntry->impactDisplayObjectId));
        const std::optional<uint16_t> impactDescriptionId =
            objectTable.findDescriptionIdByObjectId(static_cast<int16_t>(pSpellEntry->impactDisplayObjectId));

        if (pImpactEntry != nullptr && impactDescriptionId)
        {
            definition.impactObjectDescriptionId = *impactDescriptionId;
            definition.impactObjectSpriteId = pImpactEntry->spriteId;
            definition.impactObjectName = pImpactEntry->internalName;
            definition.impactObjectSpriteName = pImpactEntry->spriteName;
        }
    }

    return true;
}

bool resolveSpellDefinition(
    const SpellEntry &spell,
    const ObjectTable &objectTable,
    OutdoorWorldRuntime::ResolvedProjectileDefinition &definition)
{
    definition = {};

    if (spell.displayObjectId <= 0)
    {
        return false;
    }

    const ObjectEntry *pObjectEntry = objectTable.findByObjectId(static_cast<int16_t>(spell.displayObjectId));
    const std::optional<uint16_t> objectDescriptionId =
        objectTable.findDescriptionIdByObjectId(static_cast<int16_t>(spell.displayObjectId));

    if (pObjectEntry == nullptr || !objectDescriptionId)
    {
        return false;
    }

    definition.objectDescriptionId = *objectDescriptionId;
    definition.objectSpriteId = pObjectEntry->spriteId;
    definition.objectFlags = pObjectEntry->flags;
    definition.radius = static_cast<uint16_t>(std::max<int>(pObjectEntry->radius, 16));
    definition.height = static_cast<uint16_t>(std::max<int>(pObjectEntry->height, 16));
    definition.lifetimeTicks = static_cast<uint32_t>(std::max<int>(pObjectEntry->lifetimeTicks, 64));
    definition.speed = static_cast<float>(std::max<int>(pObjectEntry->speed, 2000));
    definition.spellId = spell.id;
    definition.effectSoundId = spell.effectSoundId;
    definition.objectName = pObjectEntry->internalName;
    definition.objectSpriteName = pObjectEntry->spriteName;
    const SpellId resolvedSpellId = spellIdFromValue(std::max(spell.id, 0));

    if (resolvedSpellId == SpellId::Sparks)
    {
        definition.objectFlags |= ObjectDescBounce;
    }
    else if (resolvedSpellId == SpellId::RockBlast)
    {
        definition.objectFlags |= ObjectDescBounce;
        definition.objectFlags &= ~ObjectDescNoGravity;
    }

    if (spell.impactDisplayObjectId > 0)
    {
        const ObjectEntry *pImpactEntry =
            objectTable.findByObjectId(static_cast<int16_t>(spell.impactDisplayObjectId));
        const std::optional<uint16_t> impactDescriptionId =
            objectTable.findDescriptionIdByObjectId(static_cast<int16_t>(spell.impactDisplayObjectId));

        if (pImpactEntry != nullptr && impactDescriptionId)
        {
            definition.impactObjectDescriptionId = *impactDescriptionId;
            definition.impactObjectSpriteId = pImpactEntry->spriteId;
            definition.impactObjectName = pImpactEntry->internalName;
            definition.impactObjectSpriteName = pImpactEntry->spriteName;
        }
    }

    return true;
}

bool resolveObjectProjectileDefinition(
    int objectId,
    int impactObjectId,
    const ObjectTable &objectTable,
    OutdoorWorldRuntime::ResolvedProjectileDefinition &definition)
{
    definition = {};

    if (objectId <= 0)
    {
        return false;
    }

    const ObjectEntry *pObjectEntry = objectTable.findByObjectId(static_cast<int16_t>(objectId));
    const std::optional<uint16_t> objectDescriptionId =
        objectTable.findDescriptionIdByObjectId(static_cast<int16_t>(objectId));

    if (pObjectEntry == nullptr || !objectDescriptionId)
    {
        return false;
    }

    definition.objectDescriptionId = *objectDescriptionId;
    definition.objectSpriteId = pObjectEntry->spriteId;
    definition.objectFlags = pObjectEntry->flags;
    definition.radius = static_cast<uint16_t>(std::max<int>(pObjectEntry->radius, 16));
    definition.height = static_cast<uint16_t>(std::max<int>(pObjectEntry->height, 16));
    definition.lifetimeTicks = static_cast<uint32_t>(std::max<int>(pObjectEntry->lifetimeTicks, 64));
    definition.speed = static_cast<float>(std::max<int>(pObjectEntry->speed, 2000));
    definition.objectName = pObjectEntry->internalName;
    definition.objectSpriteName = pObjectEntry->spriteName;

    if (impactObjectId > 0)
    {
        const ObjectEntry *pImpactEntry = objectTable.findByObjectId(static_cast<int16_t>(impactObjectId));
        const std::optional<uint16_t> impactDescriptionId =
            objectTable.findDescriptionIdByObjectId(static_cast<int16_t>(impactObjectId));

        if (pImpactEntry != nullptr && impactDescriptionId)
        {
            definition.impactObjectDescriptionId = *impactDescriptionId;
            definition.impactObjectSpriteId = pImpactEntry->spriteId;
            definition.impactObjectName = pImpactEntry->internalName;
            definition.impactObjectSpriteName = pImpactEntry->spriteName;
        }
    }

    return true;
}

bool actorLooksUndead(const MonsterTable::MonsterStatsEntry &stats)
{
    const std::string name = toLowerCopy(stats.name + " " + stats.pictureName);
    static const std::array<const char *, 11> UndeadTokens = {{
        "skeleton",
        "zombie",
        "ghost",
        "ghoul",
        "vampire",
        "lich",
        "mummy",
        "wight",
        "spectre",
        "spirit",
        "undead"
    }};

    for (const char *pToken : UndeadTokens)
    {
        if (name.find(pToken) != std::string::npos)
        {
            return true;
        }
    }

    return false;
}

float minutesToSeconds(float minutes)
{
    return minutes * 60.0f;
}

float hoursToSeconds(float hours)
{
    return hours * 3600.0f;
}

GameplayProjectileService::ProjectilePartyImpactDamageInput buildProjectilePartyImpactDamageInput(
    const OutdoorWorldRuntime::ProjectileState &projectile,
    const MonsterTable *pMonsterTable,
    const std::vector<OutdoorWorldRuntime::MapActorState> &mapActors)
{
    GameplayProjectileService::ProjectilePartyImpactDamageInput input = {};
    input.sourceKind = projectile.sourceKind;
    input.eventSource = projectile.sourceId == EventSpellSourceId;
    input.projectileDamage = projectile.damage;
    input.spellId = projectile.spellId;
    input.skillLevel = projectile.skillLevel;
    input.monsterAbility = projectile.ability;

    if (projectile.sourceKind == OutdoorWorldRuntime::ProjectileState::SourceKind::Party)
    {
        return input;
    }

    if (pMonsterTable == nullptr)
    {
        return input;
    }

    const MonsterTable::MonsterStatsEntry *pStats = nullptr;

    if (projectile.sourceMonsterId != 0)
    {
        pStats = pMonsterTable->findStatsById(projectile.sourceMonsterId);
    }
    else
    {
        for (const OutdoorWorldRuntime::MapActorState &actor : mapActors)
        {
            if (actor.actorId != projectile.sourceId)
            {
                continue;
            }

            pStats = pMonsterTable->findStatsById(actor.monsterId);
            break;
        }
    }

    if (pStats == nullptr)
    {
        return input;
    }

    input.hasMonsterFacts = true;
    input.monsterLevel = pStats->level;
    input.attack1Damage.diceRolls = pStats->attack1Damage.diceRolls;
    input.attack1Damage.diceSides = pStats->attack1Damage.diceSides;
    input.attack1Damage.bonus = pStats->attack1Damage.bonus;
    input.attack2Damage.diceRolls = pStats->attack2Damage.diceRolls;
    input.attack2Damage.diceSides = pStats->attack2Damage.diceSides;
    input.attack2Damage.bonus = pStats->attack2Damage.bonus;
    return input;
}

float resolveActorGroundZ(
    const OutdoorMapData *pOutdoorMapData,
    const MonsterTable::MonsterStatsEntry *pStats,
    uint16_t radius,
    float x,
    float y,
    float currentZ
)
{
    if (pOutdoorMapData == nullptr)
    {
        return currentZ;
    }

    const float supportFloorZ = sampleOutdoorSupportFloor(
        *pOutdoorMapData,
        x,
        y,
        currentZ,
        5.0f,
        std::max(5.0f, static_cast<float>(radius))).height;
    const float terrainFloorZ = sampleOutdoorRenderedTerrainHeight(*pOutdoorMapData, x, y);
    const float floorZ = std::max(supportFloorZ, terrainFloorZ);

    if (pStats != nullptr && pStats->canFly)
    {
        return std::max(currentZ, floorZ);
    }

    return floorZ;
}

void applyTestActorOverrides(
    int mapId,
    const OutdoorMapData *pOutdoorMapData,
    const MonsterTable::MonsterStatsEntry *pStats,
    uint32_t actorId,
    OutdoorWorldRuntime::MapActorState &state
)
{
    if (mapId == DwiMapId && actorId == DwiTestActor61)
    {
        state.preciseX = DwiTestActor61X;
        state.preciseY = DwiTestActor61Y;
        state.preciseZ = resolveActorGroundZ(
            pOutdoorMapData,
            pStats,
            state.radius,
            DwiTestActor61X,
            DwiTestActor61Y,
            DwiTestActor61Z);
        state.x = static_cast<int>(std::lround(state.preciseX));
        state.y = static_cast<int>(std::lround(state.preciseY));
        state.z = static_cast<int>(std::lround(state.preciseZ));
        state.homePreciseX = state.preciseX;
        state.homePreciseY = state.preciseY;
        state.homePreciseZ = state.preciseZ;
        state.homeX = state.x;
        state.homeY = state.y;
        state.homeZ = state.z;
    }
}

float resolveInitialActorGroundZ(
    const OutdoorMapData *pOutdoorMapData,
    const MonsterTable::MonsterStatsEntry *pStats,
    uint16_t radius,
    float x,
    float y,
    float currentZ
)
{
    if (pOutdoorMapData == nullptr)
    {
        return currentZ;
    }

    const float supportFloorZ = sampleOutdoorSupportFloor(
        *pOutdoorMapData,
        x,
        y,
        currentZ,
        std::numeric_limits<float>::max(),
        std::max(5.0f, static_cast<float>(radius))).height;
    const float terrainFloorZ = sampleOutdoorRenderedTerrainHeight(*pOutdoorMapData, x, y);
    const float floorZ = std::max(supportFloorZ, terrainFloorZ);

    if (pStats != nullptr && pStats->canFly)
    {
        return std::max(currentZ, floorZ);
    }

    return floorZ;
}

float actorCollisionRadius(
    const OutdoorWorldRuntime::MapActorState &actor,
    const MonsterTable::MonsterStatsEntry *pStats)
{
    if (pStats != nullptr && !pStats->canFly)
    {
        return OeNonFlyingActorRadius;
    }

    if (actor.radius > 0)
    {
        return static_cast<float>(actor.radius);
    }

    return OeNonFlyingActorRadius;
}

float actorCollisionHeight(
    const OutdoorWorldRuntime::MapActorState &actor,
    float collisionRadius)
{
    if (actor.height > 0)
    {
        return std::max(static_cast<float>(actor.height), collisionRadius * 2.0f + 2.0f);
    }

    return collisionRadius * 2.0f + 2.0f;
}

bool isActorUnavailableForCombat(const OutdoorWorldRuntime::MapActorState &actor);

std::vector<OutdoorActorCollision> buildNearbyActorMovementColliders(
    const std::vector<OutdoorWorldRuntime::MapActorState> &mapActors,
    const std::vector<bool> &activeActorMask,
    const MonsterTable &monsterTable)
{
    std::vector<OutdoorActorCollision> colliders;

    if (mapActors.empty())
    {
        return colliders;
    }

    colliders.reserve(mapActors.size());

    for (size_t actorIndex = 0; actorIndex < mapActors.size(); ++actorIndex)
    {
        if (actorIndex >= activeActorMask.size() || !activeActorMask[actorIndex])
        {
            continue;
        }

        const OutdoorWorldRuntime::MapActorState &actor = mapActors[actorIndex];

        if (isActorUnavailableForCombat(actor))
        {
            continue;
        }

        const MonsterTable::MonsterStatsEntry *pStats = monsterTable.findStatsById(actor.monsterId);
        const float collisionRadius = actorCollisionRadius(actor, pStats);
        const float collisionHeight = actorCollisionHeight(actor, collisionRadius);

        if (collisionRadius <= 0.0f || collisionHeight <= 0.0f)
        {
            continue;
        }

        OutdoorActorCollision collider = {};
        collider.source = OutdoorActorCollisionSource::MapDelta;
        collider.sourceIndex = actorIndex;
        collider.radius = static_cast<uint16_t>(std::lround(collisionRadius));
        collider.height = static_cast<uint16_t>(std::lround(collisionHeight));
        collider.worldX = static_cast<int>(std::lround(actor.preciseX));
        collider.worldY = static_cast<int>(std::lround(actor.preciseY));
        collider.worldZ = static_cast<int>(std::lround(actor.preciseZ + GroundSnapHeight));
        collider.group = actor.group;
        collider.name = actor.displayName;
        colliders.push_back(std::move(collider));
    }

    return colliders;
}

void syncActorFromMovementState(OutdoorWorldRuntime::MapActorState &actor)
{
    actor.preciseX = actor.movementState.x;
    actor.preciseY = actor.movementState.y;
    actor.preciseZ = actor.movementState.footZ - GroundSnapHeight;
    actor.x = static_cast<int>(std::lround(actor.preciseX));
    actor.y = static_cast<int>(std::lround(actor.preciseY));
    actor.z = static_cast<int>(std::lround(actor.preciseZ));
}

bool tryMoveActorInWorld(
    OutdoorWorldRuntime::MapActorState &actor,
    const OutdoorMapData &outdoorMapData,
    const std::vector<OutdoorFaceGeometryData> &faces,
    const MonsterTable::MonsterStatsEntry *pStats,
    float deltaX,
    float deltaY
)
{
    const float candidateX = actor.preciseX + deltaX;
    const float candidateY = actor.preciseY + deltaY;
    const bool canFly = pStats != nullptr && pStats->canFly;

    if (!canFly && outdoorTerrainSlopeTooHigh(outdoorMapData, candidateX, candidateY))
    {
        const float terrainHeight = sampleOutdoorRenderedTerrainHeight(outdoorMapData, candidateX, candidateY);

        if (terrainHeight > actor.preciseZ + 8.0f)
        {
            return false;
        }
    }

    const float candidateZ = resolveActorGroundZ(
        &outdoorMapData,
        pStats,
        actor.radius,
        candidateX,
        candidateY,
        actor.preciseZ);
    const float radius = static_cast<float>(actor.radius > 0 ? actor.radius : 40);
    const float height = static_cast<float>(actor.height > 0 ? actor.height : 120);

    for (const OutdoorFaceGeometryData &face : faces)
    {
        if (face.isWalkable)
        {
            continue;
        }

        if (isOutdoorCylinderBlockedByFace(face, candidateX, candidateY, candidateZ, radius, height))
        {
            return false;
        }
    }

    actor.preciseX = candidateX;
    actor.preciseY = candidateY;
    actor.preciseZ = candidateZ;
    return true;
}

void applyOeOutdoorSteepSlopeResponse(
    OutdoorWorldRuntime::MapActorState &actor,
    const OutdoorMapData &outdoorMapData,
    const MonsterTable::MonsterStatsEntry *pStats)
{
    if (pStats == nullptr || pStats->canFly)
    {
        return;
    }

    const float terrainFloorZ = sampleOutdoorRenderedTerrainHeight(
        outdoorMapData,
        actor.preciseX,
        actor.preciseY);

    if (actor.preciseZ > terrainFloorZ + GroundSnapHeight + 2.0f)
    {
        return;
    }

    if (!outdoorTerrainSlopeTooHigh(outdoorMapData, actor.preciseX, actor.preciseY))
    {
        return;
    }

    actor.preciseZ = terrainFloorZ;

    const bx::Vec3 terrainNormal = approximateOutdoorTerrainNormal(
        outdoorMapData,
        actor.preciseX,
        actor.preciseY);
    const bx::Vec3 actorVelocity = {actor.velocityX, actor.velocityY, actor.velocityZ};
    const float slopeResponse = std::abs(
        actorVelocity.x * terrainNormal.x
        + actorVelocity.y * terrainNormal.y
        + actorVelocity.z * terrainNormal.z) * 2.0f;

    actor.velocityX += slopeResponse * terrainNormal.x;
    actor.velocityY += slopeResponse * terrainNormal.y;
    actor.yawRadians -= OeTurnAwayFromWaterAngleRadians;
}

bool segmentMayTouchFaceBounds(
    const bx::Vec3 &segmentStart,
    const bx::Vec3 &segmentEnd,
    const OutdoorFaceGeometryData &face,
    float padding)
{
    const float segmentMinX = std::min(segmentStart.x, segmentEnd.x) - padding;
    const float segmentMaxX = std::max(segmentStart.x, segmentEnd.x) + padding;
    const float segmentMinY = std::min(segmentStart.y, segmentEnd.y) - padding;
    const float segmentMaxY = std::max(segmentStart.y, segmentEnd.y) + padding;
    const float segmentMinZ = std::min(segmentStart.z, segmentEnd.z) - padding;
    const float segmentMaxZ = std::max(segmentStart.z, segmentEnd.z) + padding;

    if (segmentMaxX < face.minX || segmentMinX > face.maxX)
    {
        return false;
    }

    if (segmentMaxY < face.minY || segmentMinY > face.maxY)
    {
        return false;
    }

    if (segmentMaxZ < face.minZ || segmentMinZ > face.maxZ)
    {
        return false;
    }

    return true;
}

std::vector<int> parseCsvIntegers(const std::optional<std::string> &note)
{
    std::vector<int> values;

    if (!note || note->empty())
    {
        return values;
    }

    std::istringstream stream(*note);
    std::string token;

    while (std::getline(stream, token, ','))
    {
        if (token.empty())
        {
            values.push_back(0);
            continue;
        }

        try
        {
            values.push_back(std::stoi(token));
        }
        catch (...)
        {
            values.push_back(0);
        }
    }

    return values;
}

void appendTimersFromProgram(
    const std::optional<ScriptedEventProgram> &program,
    std::vector<OutdoorWorldRuntime::TimerState> &timers
)
{
    if (!program)
    {
        return;
    }

    for (const ScriptedEventProgram::TimerTrigger &trigger : program->timerTriggers())
    {
        OutdoorWorldRuntime::TimerState timer = {};
        timer.eventId = trigger.eventId;
        timer.repeating = trigger.repeating;
        timer.targetHour = trigger.targetHour;
        timer.intervalGameMinutes = trigger.intervalGameMinutes;
        timer.remainingGameMinutes = trigger.remainingGameMinutes;
        timers.push_back(std::move(timer));
    }
}

const MapEncounterInfo *getEncounterInfo(const MapStatsEntry &map, int encounterSlot)
{
    if (encounterSlot == 1)
    {
        return &map.encounter1;
    }

    if (encounterSlot == 2)
    {
        return &map.encounter2;
    }

    if (encounterSlot == 3)
    {
        return &map.encounter3;
    }

    return nullptr;
}

int16_t resolveMapActorMonsterId(const MapDeltaActor &actor)
{
    if (actor.monsterInfoId > 0)
    {
        return actor.monsterInfoId;
    }

    if (actor.monsterId > 0)
    {
        return actor.monsterId;
    }

    return 0;
}

const MonsterEntry *resolveMonsterEntry(
    const MonsterTable &monsterTable,
    int16_t monsterId,
    const MonsterTable::MonsterStatsEntry *pStats
)
{
    if (pStats != nullptr && !pStats->pictureName.empty())
    {
        if (const MonsterEntry *pEntry = monsterTable.findByInternalName(pStats->pictureName))
        {
            return pEntry;
        }
    }

    return monsterTable.findById(monsterId);
}

OutdoorWorldRuntime::MapActorState buildMapActorState(
    const MonsterTable &monsterTable,
    const MapDeltaActor &actor,
    uint32_t actorId,
    const OutdoorMapData *pOutdoorMapData,
    float attackAnimationSeconds
)
{
    OutdoorWorldRuntime::MapActorState state = {};
    state.actorId = actorId;
    state.monsterId = resolveMapActorMonsterId(actor);
    state.group = actor.group;
    state.ally = actor.ally;

    const MonsterTable::MonsterStatsEntry *pStats = monsterTable.findStatsById(state.monsterId);
    const MonsterEntry *pMonsterEntry = resolveMonsterEntry(monsterTable, state.monsterId, pStats);
    state.displayName = pStats != nullptr ? pStats->name : actor.name;
    state.maxHp = pStats != nullptr ? pStats->hitPoints : std::max(0, static_cast<int>(actor.hp));
    state.currentHp = actor.hp > 0 ? actor.hp : state.maxHp;
    state.x = actor.x;
    state.y = actor.y;
    state.z = actor.z;
    state.preciseX = static_cast<float>(actor.x);
    state.preciseY = static_cast<float>(actor.y);
    state.preciseZ = static_cast<float>(actor.z);
    state.homeX = actor.x;
    state.homeY = actor.y;
    state.homeZ = actor.z;
    state.homePreciseX = static_cast<float>(actor.x);
    state.homePreciseY = static_cast<float>(actor.y);
    state.homePreciseZ = static_cast<float>(actor.z);
    state.radius = actor.radius;
    state.height = actor.height;
    state.moveSpeed = pMonsterEntry != nullptr ? pMonsterEntry->movementSpeed : 0;
    state.hostileToParty =
        (actor.attributes & ActorAggressorBit) != 0 || monsterTable.isHostileToParty(state.monsterId);
    state.hostilityType = actor.hostilityType;

    if (state.hostilityType == 0 && state.hostileToParty && pStats != nullptr)
    {
        state.hostilityType = static_cast<uint8_t>(pStats->hostility);
    }

    state.isInvisible = (actor.attributes & ActorInvisibleBit) != 0;
    state.animation = actor.hp <= 0 ? OutdoorWorldRuntime::ActorAnimation::Dead
        : static_cast<OutdoorWorldRuntime::ActorAnimation>(std::clamp<int>(actor.currentActionAnimation, 0, 7));
    state.aiState = actor.hp <= 0 ? OutdoorWorldRuntime::ActorAiState::Dead : OutdoorWorldRuntime::ActorAiState::Standing;
    state.recoverySeconds = monsterRecoverySeconds(pStats != nullptr ? pStats->recovery : 100);
    state.attackAnimationSeconds = std::max(0.1f, attackAnimationSeconds);
    GameplayActorService actorService = {};
    state.attackCooldownSeconds = actorService.initialAttackCooldownSeconds(actorId, state.recoverySeconds);
    state.idleDecisionSeconds = actorService.initialIdleDecisionSeconds(actorId);

    state.preciseZ = resolveInitialActorGroundZ(
        pOutdoorMapData,
        pStats,
        state.radius,
        state.preciseX,
        state.preciseY,
        state.preciseZ);
    state.z = static_cast<int>(std::lround(state.preciseZ));
    state.homePreciseZ = state.preciseZ;
    state.homeZ = state.z;

    return state;
}

float attackAnimationSecondsForBillboard(
    const ActorPreviewBillboardSet &billboardSet,
    const ActorPreviewBillboard &billboard)
{
    uint16_t attackFrameIndex =
        billboard.actionSpriteFrameIndices[static_cast<size_t>(OutdoorWorldRuntime::ActorAnimation::AttackMelee)];

    if (attackFrameIndex == 0)
    {
        attackFrameIndex =
            billboard.actionSpriteFrameIndices[static_cast<size_t>(OutdoorWorldRuntime::ActorAnimation::AttackRanged)];
    }

    if (attackFrameIndex == 0)
    {
        return 0.3f;
    }

    const SpriteFrameEntry *pAttackFrame = billboardSet.spriteFrameTable.getFrame(attackFrameIndex, 0);

    if (pAttackFrame == nullptr || pAttackFrame->animationLengthTicks <= 0)
    {
        return 0.3f;
    }

    return static_cast<float>(pAttackFrame->animationLengthTicks) / TicksPerSecond;
}

float animationSecondsForSpriteFrame(
    const SpriteFrameTable *pSpriteFrameTable,
    uint16_t spriteFrameIndex,
    float fallbackSeconds)
{
    if (pSpriteFrameTable == nullptr || spriteFrameIndex == 0)
    {
        return fallbackSeconds;
    }

    const SpriteFrameEntry *pFrame = pSpriteFrameTable->getFrame(spriteFrameIndex, 0);

    if (pFrame == nullptr || pFrame->animationLengthTicks <= 0)
    {
        return fallbackSeconds;
    }

    return std::max(0.05f, static_cast<float>(pFrame->animationLengthTicks) / TicksPerSecond);
}

float actorAnimationSeconds(
    const SpriteFrameTable *pSpriteFrameTable,
    const OutdoorWorldRuntime::MapActorState &actor,
    OutdoorWorldRuntime::ActorAnimation animation,
    float fallbackSeconds)
{
    const size_t animationIndex = static_cast<size_t>(animation);

    if (animationIndex >= actor.actionSpriteFrameIndices.size())
    {
        return fallbackSeconds;
    }

    return animationSecondsForSpriteFrame(
        pSpriteFrameTable,
        actor.actionSpriteFrameIndices[animationIndex],
        fallbackSeconds);
}

bool isActorUnavailableForCombat(const OutdoorWorldRuntime::MapActorState &actor)
{
    GameplayActorService actorService = {};
    return actorService.isActorUnavailableForCombat(
        actor.isInvisible,
        actor.isDead,
        actor.currentHp <= 0,
        actor.aiState == OutdoorWorldRuntime::ActorAiState::Dying,
        actor.aiState == OutdoorWorldRuntime::ActorAiState::Dead);
}

std::vector<bool> selectOutdoorActiveActorMask(
    const std::vector<OutdoorActiveActorCandidate> &candidates,
    size_t actorCount,
    size_t maxActiveActors,
    float activeRange)
{
    std::vector<bool> activeActorMask(actorCount, false);

    if (actorCount == 0 || maxActiveActors == 0)
    {
        return activeActorMask;
    }

    std::vector<std::pair<size_t, float>> activeActorDistances;
    activeActorDistances.reserve(candidates.size());

    for (const OutdoorActiveActorCandidate &candidate : candidates)
    {
        if (!candidate.eligible || candidate.actorIndex >= actorCount)
        {
            continue;
        }

        if (candidate.distanceToParty <= activeRange)
        {
            activeActorDistances.push_back({candidate.actorIndex, candidate.distanceToParty});
        }
    }

    std::stable_sort(
        activeActorDistances.begin(),
        activeActorDistances.end(),
        [](const std::pair<size_t, float> &left, const std::pair<size_t, float> &right)
        {
            return left.second < right.second;
        });

    for (size_t index = 0; index < activeActorDistances.size() && index < maxActiveActors; ++index)
    {
        activeActorMask[activeActorDistances[index].first] = true;
    }

    return activeActorMask;
}

bool canEnterHitReaction(const OutdoorWorldRuntime::MapActorState &actor)
{
    GameplayActorService actorService = {};
    return actorService.canActorEnterHitReaction(
        actor.isInvisible,
        actor.isDead,
        actor.currentHp <= 0,
        actor.aiState == OutdoorWorldRuntime::ActorAiState::Dying,
        actor.aiState == OutdoorWorldRuntime::ActorAiState::Dead,
        actor.aiState == OutdoorWorldRuntime::ActorAiState::Stunned,
        actor.aiState == OutdoorWorldRuntime::ActorAiState::Attacking);
}

void beginHitReaction(
    OutdoorWorldRuntime::MapActorState &actor,
    const SpriteFrameTable *pSpriteFrameTable)
{
    actor.aiState = OutdoorWorldRuntime::ActorAiState::Stunned;
    actor.animation = OutdoorWorldRuntime::ActorAnimation::GotHit;
    actor.animationTimeTicks = 0.0f;
    actor.moveDirectionX = 0.0f;
    actor.moveDirectionY = 0.0f;
    actor.velocityX = 0.0f;
    actor.velocityY = 0.0f;
    actor.velocityZ = 0.0f;
    actor.actionSeconds = actorAnimationSeconds(
        pSpriteFrameTable,
        actor,
        OutdoorWorldRuntime::ActorAnimation::GotHit,
        0.25f);
    actor.idleDecisionSeconds = std::max(actor.idleDecisionSeconds, actor.actionSeconds);
    actor.attackImpactTriggered = false;
}

void beginDyingState(
    OutdoorWorldRuntime::MapActorState &actor,
    const SpriteFrameTable *pSpriteFrameTable)
{
    actor.currentHp = 0;
    actor.aiState = OutdoorWorldRuntime::ActorAiState::Dying;
    actor.animation = OutdoorWorldRuntime::ActorAnimation::Dying;
    actor.animationTimeTicks = 0.0f;
    actor.moveDirectionX = 0.0f;
    actor.moveDirectionY = 0.0f;
    actor.velocityX = 0.0f;
    actor.velocityY = 0.0f;
    actor.velocityZ = 0.0f;
    actor.actionSeconds = actorAnimationSeconds(
        pSpriteFrameTable,
        actor,
        OutdoorWorldRuntime::ActorAnimation::Dying,
        0.35f);
    actor.idleDecisionSeconds = 0.0f;
    actor.attackImpactTriggered = false;
}

std::array<uint16_t, 8> buildMonsterActionSpriteFrameIndices(
    const SpriteFrameTable &spriteFrameTable,
    const MonsterEntry *pMonsterEntry)
{
    std::array<uint16_t, 8> spriteFrameIndices = {};

    if (pMonsterEntry == nullptr)
    {
        return spriteFrameIndices;
    }

    for (size_t actionIndex = 0; actionIndex < spriteFrameIndices.size(); ++actionIndex)
    {
        const std::string &spriteName = pMonsterEntry->spriteNames[actionIndex];

        if (spriteName.empty())
        {
            continue;
        }

        const std::optional<uint16_t> frameIndex = spriteFrameTable.findFrameIndexBySpriteName(spriteName);

        if (frameIndex)
        {
            spriteFrameIndices[actionIndex] = *frameIndex;
        }
    }

    return spriteFrameIndices;
}

OutdoorWorldRuntime::MonsterVisualState buildMonsterVisualState(
    const SpriteFrameTable &spriteFrameTable,
    const MonsterEntry *pMonsterEntry)
{
    OutdoorWorldRuntime::MonsterVisualState state = {};

    if (pMonsterEntry == nullptr)
    {
        return state;
    }

    for (const std::string &spriteName : pMonsterEntry->spriteNames)
    {
        if (spriteName.empty())
        {
            continue;
        }

        const std::optional<uint16_t> frameIndex = spriteFrameTable.findFrameIndexBySpriteName(spriteName);

        if (frameIndex)
        {
            state.spriteFrameIndex = *frameIndex;
            break;
        }
    }

    state.actionSpriteFrameIndices = buildMonsterActionSpriteFrameIndices(spriteFrameTable, pMonsterEntry);
    return state;
}

void applyMonsterVisualState(
    OutdoorWorldRuntime::MapActorState &actor,
    const OutdoorWorldRuntime::MonsterVisualState &visualState)
{
    actor.spriteFrameIndex = visualState.spriteFrameIndex;
    actor.actionSpriteFrameIndices = visualState.actionSpriteFrameIndices;
    actor.useStaticSpriteFrame = visualState.useStaticFrame;
}

uint16_t resolveRuntimeSpriteFrameIndex(
    const SpriteFrameTable *pSpriteFrameTable,
    uint16_t spriteId,
    const std::string &spriteName)
{
    if (pSpriteFrameTable != nullptr && !spriteName.empty())
    {
        const std::optional<uint16_t> frameIndex = pSpriteFrameTable->findFrameIndexBySpriteName(spriteName);

        if (frameIndex)
        {
            return *frameIndex;
        }
    }

    return spriteId;
}

void applyImmediateSpellVisualFallback(
    SpellId spellId,
    uint16_t &spriteId,
    std::string &spriteName)
{
    switch (spellId)
    {
        case SpellId::Slow:
            spriteId = 714;
            spriteName = "spell41";
            break;

        case SpellId::Paralyze:
            spriteId = 786;
            spriteName = "spell84";
            break;

        case SpellId::MassFear:
        case SpellId::Fear:
            spriteId = 722;
            spriteName = "spell57";
            break;

        default:
            break;
    }
}

GameplayActorControlMode gameplayActorControlModeFromOutdoor(OutdoorWorldRuntime::ActorControlMode mode)
{
    switch (mode)
    {
        case OutdoorWorldRuntime::ActorControlMode::Charm:
            return GameplayActorControlMode::Charm;

        case OutdoorWorldRuntime::ActorControlMode::Berserk:
            return GameplayActorControlMode::Berserk;

        case OutdoorWorldRuntime::ActorControlMode::Enslaved:
            return GameplayActorControlMode::Enslaved;

        case OutdoorWorldRuntime::ActorControlMode::ControlUndead:
            return GameplayActorControlMode::ControlUndead;

        case OutdoorWorldRuntime::ActorControlMode::Reanimated:
            return GameplayActorControlMode::Reanimated;

        case OutdoorWorldRuntime::ActorControlMode::None:
        default:
            return GameplayActorControlMode::None;
    }
}

GameplayActorAiType gameplayActorAiTypeFromMonster(MonsterTable::MonsterAiType aiType)
{
    switch (aiType)
    {
        case MonsterTable::MonsterAiType::Wimp:
            return GameplayActorAiType::Wimp;

        case MonsterTable::MonsterAiType::Normal:
            return GameplayActorAiType::Normal;

        case MonsterTable::MonsterAiType::Aggressive:
            return GameplayActorAiType::Aggressive;

        case MonsterTable::MonsterAiType::Suicide:
        default:
            return GameplayActorAiType::Suicide;
    }
}

enum class OutdoorTargetKind : uint8_t
{
    None = 0,
    Party = 1,
    Actor = 2,
};

ActorAiTargetKind actorAiTargetKindFromOutdoorTarget(OutdoorTargetKind kind)
{
    switch (kind)
    {
        case OutdoorTargetKind::Party:
            return ActorAiTargetKind::Party;

        case OutdoorTargetKind::Actor:
            return ActorAiTargetKind::Actor;

        case OutdoorTargetKind::None:
        default:
            return ActorAiTargetKind::None;
    }
}

ActorAiMotionState actorAiMotionStateFromOutdoor(OutdoorWorldRuntime::ActorAiState state)
{
    switch (state)
    {
        case OutdoorWorldRuntime::ActorAiState::Wandering:
            return ActorAiMotionState::Wandering;

        case OutdoorWorldRuntime::ActorAiState::Pursuing:
            return ActorAiMotionState::Pursuing;

        case OutdoorWorldRuntime::ActorAiState::Fleeing:
            return ActorAiMotionState::Fleeing;

        case OutdoorWorldRuntime::ActorAiState::Stunned:
            return ActorAiMotionState::Stunned;

        case OutdoorWorldRuntime::ActorAiState::Attacking:
            return ActorAiMotionState::Attacking;

        case OutdoorWorldRuntime::ActorAiState::Dying:
            return ActorAiMotionState::Dying;

        case OutdoorWorldRuntime::ActorAiState::Dead:
            return ActorAiMotionState::Dead;

        case OutdoorWorldRuntime::ActorAiState::Standing:
        default:
            return ActorAiMotionState::Standing;
    }
}

ActorAiAnimationState actorAiAnimationStateFromOutdoor(OutdoorWorldRuntime::ActorAnimation animation)
{
    switch (animation)
    {
        case OutdoorWorldRuntime::ActorAnimation::Walking:
            return ActorAiAnimationState::Walking;

        case OutdoorWorldRuntime::ActorAnimation::AttackMelee:
            return ActorAiAnimationState::AttackMelee;

        case OutdoorWorldRuntime::ActorAnimation::AttackRanged:
            return ActorAiAnimationState::AttackRanged;

        case OutdoorWorldRuntime::ActorAnimation::GotHit:
            return ActorAiAnimationState::GotHit;

        case OutdoorWorldRuntime::ActorAnimation::Dying:
            return ActorAiAnimationState::Dying;

        case OutdoorWorldRuntime::ActorAnimation::Dead:
            return ActorAiAnimationState::Dead;

        case OutdoorWorldRuntime::ActorAnimation::Bored:
            return ActorAiAnimationState::Bored;

        case OutdoorWorldRuntime::ActorAnimation::Standing:
        default:
            return ActorAiAnimationState::Standing;
    }
}

OutdoorWorldRuntime::ActorAiState outdoorActorAiStateFromGameplay(ActorAiMotionState state)
{
    switch (state)
    {
        case ActorAiMotionState::Wandering:
            return OutdoorWorldRuntime::ActorAiState::Wandering;

        case ActorAiMotionState::Pursuing:
            return OutdoorWorldRuntime::ActorAiState::Pursuing;

        case ActorAiMotionState::Fleeing:
            return OutdoorWorldRuntime::ActorAiState::Fleeing;

        case ActorAiMotionState::Stunned:
            return OutdoorWorldRuntime::ActorAiState::Stunned;

        case ActorAiMotionState::Attacking:
            return OutdoorWorldRuntime::ActorAiState::Attacking;

        case ActorAiMotionState::Dying:
            return OutdoorWorldRuntime::ActorAiState::Dying;

        case ActorAiMotionState::Dead:
            return OutdoorWorldRuntime::ActorAiState::Dead;

        case ActorAiMotionState::Standing:
        default:
            return OutdoorWorldRuntime::ActorAiState::Standing;
    }
}

OutdoorWorldRuntime::ActorAnimation outdoorActorAnimationFromGameplay(ActorAiAnimationState animation)
{
    switch (animation)
    {
        case ActorAiAnimationState::Walking:
            return OutdoorWorldRuntime::ActorAnimation::Walking;

        case ActorAiAnimationState::AttackMelee:
            return OutdoorWorldRuntime::ActorAnimation::AttackMelee;

        case ActorAiAnimationState::AttackRanged:
            return OutdoorWorldRuntime::ActorAnimation::AttackRanged;

        case ActorAiAnimationState::GotHit:
            return OutdoorWorldRuntime::ActorAnimation::GotHit;

        case ActorAiAnimationState::Dying:
            return OutdoorWorldRuntime::ActorAnimation::Dying;

        case ActorAiAnimationState::Dead:
            return OutdoorWorldRuntime::ActorAnimation::Dead;

        case ActorAiAnimationState::Bored:
            return OutdoorWorldRuntime::ActorAnimation::Bored;

        case ActorAiAnimationState::Standing:
        default:
            return OutdoorWorldRuntime::ActorAnimation::Standing;
    }
}

GameplayActorTargetPolicyState buildGameplayActorTargetPolicyState(const OutdoorWorldRuntime::MapActorState &actor)
{
    GameplayActorTargetPolicyState state = {};
    state.monsterId = actor.monsterId;
    state.preciseZ = actor.preciseZ;
    state.height = actor.height;
    state.hostileToParty = actor.hostileToParty;
    state.controlMode = gameplayActorControlModeFromOutdoor(actor.controlMode);
    return state;
}

OutdoorWorldRuntime::MonsterAttackAbility outdoorAttackAbilityFromGameplay(GameplayActorAttackAbility ability)
{
    switch (ability)
    {
        case GameplayActorAttackAbility::Attack2:
            return OutdoorWorldRuntime::MonsterAttackAbility::Attack2;

        case GameplayActorAttackAbility::Spell1:
            return OutdoorWorldRuntime::MonsterAttackAbility::Spell1;

        case GameplayActorAttackAbility::Spell2:
            return OutdoorWorldRuntime::MonsterAttackAbility::Spell2;

        case GameplayActorAttackAbility::Attack1:
        default:
            return OutdoorWorldRuntime::MonsterAttackAbility::Attack1;
    }
}

GameplayActorAttackAbility gameplayAttackAbilityFromOutdoor(OutdoorWorldRuntime::MonsterAttackAbility ability)
{
    switch (ability)
    {
        case OutdoorWorldRuntime::MonsterAttackAbility::Attack2:
            return GameplayActorAttackAbility::Attack2;

        case OutdoorWorldRuntime::MonsterAttackAbility::Spell1:
            return GameplayActorAttackAbility::Spell1;

        case OutdoorWorldRuntime::MonsterAttackAbility::Spell2:
            return GameplayActorAttackAbility::Spell2;

        case OutdoorWorldRuntime::MonsterAttackAbility::Attack1:
        default:
            return GameplayActorAttackAbility::Attack1;
    }
}

OutdoorWorldRuntime::ActorControlMode outdoorActorControlModeFromGameplay(GameplayActorControlMode mode)
{
    switch (mode)
    {
        case GameplayActorControlMode::Charm:
            return OutdoorWorldRuntime::ActorControlMode::Charm;

        case GameplayActorControlMode::Berserk:
            return OutdoorWorldRuntime::ActorControlMode::Berserk;

        case GameplayActorControlMode::Enslaved:
            return OutdoorWorldRuntime::ActorControlMode::Enslaved;

        case GameplayActorControlMode::ControlUndead:
            return OutdoorWorldRuntime::ActorControlMode::ControlUndead;

        case GameplayActorControlMode::Reanimated:
            return OutdoorWorldRuntime::ActorControlMode::Reanimated;

        case GameplayActorControlMode::None:
        default:
            return OutdoorWorldRuntime::ActorControlMode::None;
    }
}

GameplayActorSpellEffectState buildGameplayActorSpellEffectState(const OutdoorWorldRuntime::MapActorState &actor)
{
    GameplayActorSpellEffectState state = {};
    state.slowRemainingSeconds = actor.slowRemainingSeconds;
    state.slowMoveMultiplier = actor.slowMoveMultiplier;
    state.slowRecoveryMultiplier = actor.slowRecoveryMultiplier;
    state.stunRemainingSeconds = actor.stunRemainingSeconds;
    state.paralyzeRemainingSeconds = actor.paralyzeRemainingSeconds;
    state.fearRemainingSeconds = actor.fearRemainingSeconds;
    state.blindRemainingSeconds = actor.blindRemainingSeconds;
    state.controlRemainingSeconds = actor.controlRemainingSeconds;
    state.controlMode = gameplayActorControlModeFromOutdoor(actor.controlMode);
    state.shrinkRemainingSeconds = actor.shrinkRemainingSeconds;
    state.shrinkDamageMultiplier = actor.shrinkDamageMultiplier;
    state.shrinkArmorClassMultiplier = actor.shrinkArmorClassMultiplier;
    state.darkGraspRemainingSeconds = actor.darkGraspRemainingSeconds;
    state.hostileToParty = actor.hostileToParty;
    state.hasDetectedParty = actor.hasDetectedParty;
    return state;
}

void applyGameplayActorSpellEffectState(
    const GameplayActorSpellEffectState &state,
    OutdoorWorldRuntime::MapActorState &actor)
{
    actor.slowRemainingSeconds = state.slowRemainingSeconds;
    actor.slowMoveMultiplier = state.slowMoveMultiplier;
    actor.slowRecoveryMultiplier = state.slowRecoveryMultiplier;
    actor.stunRemainingSeconds = state.stunRemainingSeconds;
    actor.paralyzeRemainingSeconds = state.paralyzeRemainingSeconds;
    actor.fearRemainingSeconds = state.fearRemainingSeconds;
    actor.blindRemainingSeconds = state.blindRemainingSeconds;
    actor.controlRemainingSeconds = state.controlRemainingSeconds;
    actor.controlMode = outdoorActorControlModeFromGameplay(state.controlMode);
    actor.shrinkRemainingSeconds = state.shrinkRemainingSeconds;
    actor.shrinkDamageMultiplier = state.shrinkDamageMultiplier;
    actor.shrinkArmorClassMultiplier = state.shrinkArmorClassMultiplier;
    actor.darkGraspRemainingSeconds = state.darkGraspRemainingSeconds;
    actor.hostileToParty = state.hostileToParty;
    actor.hasDetectedParty = state.hasDetectedParty;
}

struct EncounterSpawnDescriptor
{
    int encounterSlot = 0;
    char fixedTier = '\0';
};

std::string encounterPictureBase(const MapEncounterInfo &encounter);

EncounterSpawnDescriptor resolveEncounterSpawnDescriptor(uint16_t index)
{
    EncounterSpawnDescriptor descriptor = {};

    if (index >= 1 && index <= 3)
    {
        descriptor.encounterSlot = index;
        return descriptor;
    }

    if (index >= 4 && index <= 12)
    {
        descriptor.encounterSlot = static_cast<int>((index - 4) % 3) + 1;
        descriptor.fixedTier = static_cast<char>('A' + (index - 4) / 3);
    }

    return descriptor;
}

const MonsterTable::MonsterStatsEntry *resolveEncounterMonsterStats(
    const MapStatsEntry &map,
    const MonsterTable &monsterTable,
    int encounterSlot,
    char tierLetter
)
{
    const MapEncounterInfo *pEncounter = getEncounterInfo(map, encounterSlot);

    if (pEncounter == nullptr)
    {
        return nullptr;
    }

    std::string pictureName = encounterPictureBase(*pEncounter);

    if (pictureName.empty())
    {
        return nullptr;
    }

    pictureName += " ";
    pictureName.push_back(tierLetter);
    return monsterTable.findStatsByPictureName(pictureName);
}

char resolveEncounterTierLetter(
    const MapStatsEntry &map,
    int encounterSlot,
    char fixedTier,
    uint32_t seed)
{
    if (fixedTier != '\0')
    {
        return fixedTier;
    }

    const MapEncounterInfo *pEncounter = getEncounterInfo(map, encounterSlot);

    if (pEncounter == nullptr)
    {
        return 'A';
    }

    const int difficulty = std::clamp(pEncounter->difficulty, 0, 3);
    const std::array<int, 3> &weights = EncounterDifficultyTierWeights[difficulty];
    const int aWeight = weights[0];
    const int bWeight = weights[1];
    const int totalWeight = std::max(1, aWeight + bWeight + weights[2]);
    std::mt19937 rng(seed);
    const int roll = std::uniform_int_distribution<int>(0, totalWeight - 1)(rng);

    if (roll < aWeight)
    {
        return 'A';
    }

    if (roll < aWeight + bWeight)
    {
        return 'B';
    }

    return 'C';
}

uint32_t resolveEncounterSpawnCount(
    const MapStatsEntry &map,
    int encounterSlot,
    uint32_t countOverride,
    uint32_t sessionSeed,
    uint32_t salt
)
{
    if (countOverride > 0)
    {
        return countOverride;
    }

    const MapEncounterInfo *pEncounter = getEncounterInfo(map, encounterSlot);

    if (pEncounter == nullptr)
    {
        return 0;
    }

    const int minCount = std::max(0, std::min(pEncounter->minCount, pEncounter->maxCount));
    const int maxCount = std::max(0, std::max(pEncounter->minCount, pEncounter->maxCount));

    if (maxCount <= 0)
    {
        return 0;
    }

    if (minCount == maxCount)
    {
        return static_cast<uint32_t>(maxCount);
    }

    std::mt19937 rng(sessionSeed ^ salt ^ static_cast<uint32_t>(encounterSlot * 2654435761u));
    return static_cast<uint32_t>(std::uniform_int_distribution<int>(minCount, maxCount)(rng));
}

bx::Vec3 calculateEncounterSpawnPosition(
    float centerX,
    float centerY,
    float centerZ,
    uint16_t spawnRadius,
    uint16_t actorRadius,
    uint32_t spawnOrdinal
)
{
    if (spawnOrdinal == 0)
    {
        return {centerX, centerY, centerZ};
    }

    const uint32_t ringOrdinal = spawnOrdinal - 1;
    const uint32_t ringIndex = ringOrdinal / 8;
    const uint32_t slotIndex = ringOrdinal % 8;
    const float baseRadius = std::max(
        static_cast<float>(std::max<uint16_t>(spawnRadius, static_cast<uint16_t>(96))),
        static_cast<float>(actorRadius) * 2.0f + 16.0f);
    const float radius = baseRadius + static_cast<float>(ringIndex) * (baseRadius * 0.75f);
    const float angle = (2.0f * Pi * static_cast<float>(slotIndex)) / 8.0f;
    return {
        centerX + std::cos(angle) * radius,
        centerY + std::sin(angle) * radius,
        centerZ
    };
}

OutdoorWorldRuntime::MapActorState buildSpawnedMapActorState(
    const MonsterTable &monsterTable,
    const OutdoorMapData *pOutdoorMapData,
    const MonsterTable::MonsterStatsEntry &stats,
    uint32_t actorId,
    uint32_t uniqueNameId,
    bool fromSpawnPoint,
    size_t spawnPointIndex,
    uint32_t group,
    uint16_t attributes,
    float x,
    float y,
    float z
)
{
    OutdoorWorldRuntime::MapActorState state = {};
    state.actorId = actorId;
    state.monsterId = static_cast<int16_t>(stats.id);
    state.displayName = stats.name;
    state.uniqueNameId = uniqueNameId;
    state.spawnedAtRuntime = true;
    state.fromSpawnPoint = fromSpawnPoint;
    state.spawnPointIndex = spawnPointIndex;
    state.group = group;
    state.ally = group;
    state.hostilityType = static_cast<uint8_t>(stats.hostility);
    state.maxHp = stats.hitPoints;
    state.currentHp = stats.hitPoints;
    state.x = static_cast<int>(std::lround(x));
    state.y = static_cast<int>(std::lround(y));
    state.z = static_cast<int>(std::lround(z));
    state.preciseX = x;
    state.preciseY = y;
    state.preciseZ = z;
    state.homeX = state.x;
    state.homeY = state.y;
    state.homeZ = state.z;
    state.homePreciseX = state.preciseX;
    state.homePreciseY = state.preciseY;
    state.homePreciseZ = state.preciseZ;

    const MonsterEntry *pMonsterEntry = resolveMonsterEntry(monsterTable, state.monsterId, &stats);
    state.radius = pMonsterEntry != nullptr ? pMonsterEntry->radius : 32;
    state.height = pMonsterEntry != nullptr ? pMonsterEntry->height : 128;
    state.moveSpeed = pMonsterEntry != nullptr ? pMonsterEntry->movementSpeed : 0;
    state.hostileToParty =
        (attributes & ActorAggressorBit) != 0 || monsterTable.isHostileToParty(state.monsterId);
    state.isInvisible = (attributes & ActorInvisibleBit) != 0;
    state.animation = OutdoorWorldRuntime::ActorAnimation::Standing;
    state.aiState = OutdoorWorldRuntime::ActorAiState::Standing;
    state.recoverySeconds = monsterRecoverySeconds(stats.recovery);
    state.attackAnimationSeconds = 0.3f;
    GameplayActorService actorService = {};
    state.attackCooldownSeconds = actorService.initialAttackCooldownSeconds(actorId, state.recoverySeconds);
    state.idleDecisionSeconds = actorService.initialIdleDecisionSeconds(actorId);

    state.preciseZ = resolveInitialActorGroundZ(
        pOutdoorMapData,
        &stats,
        state.radius,
        state.preciseX,
        state.preciseY,
        state.preciseZ);
    state.z = static_cast<int>(std::lround(state.preciseZ));
    state.homePreciseZ = state.preciseZ;
    state.homeZ = state.z;
    return state;
}

struct OutdoorCombatTargetCandidate
{
    size_t actorIndex = static_cast<size_t>(-1);
    GameplayActorTargetPolicyState policyState = {};
    float preciseX = 0.0f;
    float preciseY = 0.0f;
    float targetZ = 0.0f;
    uint16_t radius = 0;
    bool unavailable = false;
    bool lineOfSightChecked = false;
    bool hasLineOfSight = false;
};

struct OutdoorTargetFacts
{
    OutdoorTargetKind kind = OutdoorTargetKind::None;
    size_t actorIndex = static_cast<size_t>(-1);
    int relationToTarget = 0;
    float targetX = 0.0f;
    float targetY = 0.0f;
    float targetZ = 0.0f;
    float deltaX = 0.0f;
    float deltaY = 0.0f;
    float deltaZ = 0.0f;
    float horizontalDistanceToTarget = 0.0f;
    float distanceToTarget = 0.0f;
    float edgeDistance = 0.0f;
    bool canSense = false;
    bool partyCanSense = false;
};

struct OutdoorEngagementState
{
    bool shouldEngageTarget = false;
    bool shouldPromoteHostility = false;
    float promotionRange = 0.0f;
    bool shouldFlee = false;
    bool inMeleeRange = false;
    bool friendlyNearParty = false;
};

float meleeRangeForCombatTarget(bool targetIsActor)
{
    return targetIsActor ? ActorMeleeRange * 0.5f : ActorMeleeRange;
}

std::vector<OutdoorCombatTargetCandidate> buildCombatTargetCandidates(
    const GameplayActorService *pGameplayActorService,
    const OutdoorWorldRuntime::MapActorState &actor,
    size_t actorIndex,
    const std::vector<OutdoorWorldRuntime::MapActorState> &mapActors)
{
    std::vector<OutdoorCombatTargetCandidate> candidates;

    if (pGameplayActorService == nullptr)
    {
        return candidates;
    }

    candidates.reserve(mapActors.size() > 0 ? mapActors.size() - 1 : 0);

    for (size_t otherActorIndex = 0; otherActorIndex < mapActors.size(); ++otherActorIndex)
    {
        if (otherActorIndex == actorIndex)
        {
            continue;
        }

        const OutdoorWorldRuntime::MapActorState &otherActor = mapActors[otherActorIndex];

        if (isActorUnavailableForCombat(otherActor))
        {
            continue;
        }

        const float deltaX = otherActor.preciseX - actor.preciseX;
        const float deltaY = otherActor.preciseY - actor.preciseY;

        if (std::abs(deltaX) > HostilityLongRange || std::abs(deltaY) > HostilityLongRange)
        {
            continue;
        }

        const float otherActorTargetZ =
            otherActor.preciseZ + std::max(24.0f, static_cast<float>(otherActor.height) * 0.7f);
        OutdoorCombatTargetCandidate candidate = {};
        candidate.actorIndex = otherActorIndex;
        candidate.policyState = buildGameplayActorTargetPolicyState(otherActor);
        candidate.preciseX = otherActor.preciseX;
        candidate.preciseY = otherActor.preciseY;
        candidate.targetZ = otherActorTargetZ;
        candidate.radius = otherActor.radius;
        candidates.push_back(candidate);
    }

    return candidates;
}

template <typename VisibilityFn>
OutdoorTargetFacts resolveOutdoorTargetFacts(
    const GameplayActorService *pGameplayActorService,
    const OutdoorWorldRuntime::MapActorState &actor,
    size_t actorIndex,
    std::vector<OutdoorCombatTargetCandidate> &candidates,
    float partyX,
    float partyY,
    float partyZ,
    VisibilityFn &&hasClearOutdoorLineOfSight)
{
    OutdoorTargetFacts target = {};

    if (pGameplayActorService == nullptr)
    {
        return target;
    }

    float bestPriorityDistanceSquared = std::numeric_limits<float>::max();
    const GameplayActorTargetPolicyState actorPolicyState = buildGameplayActorTargetPolicyState(actor);
    const float actorTargetZ = actor.preciseZ + std::max(24.0f, static_cast<float>(actor.height) * 0.7f);
    const float partyTargetZ = partyZ + PartyTargetHeightOffset;
    const float partySenseRange = pGameplayActorService->partyEngagementRange(actorPolicyState);

    if (partySenseRange > 0.0f)
    {
        const float deltaPartyX = partyX - actor.preciseX;
        const float deltaPartyY = partyY - actor.preciseY;
        const float deltaPartyZ = partyTargetZ - actorTargetZ;
        const bool canSenseParty =
            std::abs(deltaPartyX) <= partySenseRange
            && std::abs(deltaPartyY) <= partySenseRange
            && std::abs(deltaPartyZ) <= partySenseRange
            && isWithinRange3d(deltaPartyX, deltaPartyY, deltaPartyZ, partySenseRange);

        target.partyCanSense = canSenseParty;

        if (canSenseParty)
        {
            const float horizontalDistanceToParty = length2d(deltaPartyX, deltaPartyY);
            const float distanceToParty = length3d(deltaPartyX, deltaPartyY, deltaPartyZ);
            const float edgeDistanceToParty =
                std::max(0.0f, distanceToParty - static_cast<float>(actor.radius) - PartyCollisionRadius);
            target.kind = OutdoorTargetKind::Party;
            target.targetX = partyX;
            target.targetY = partyY;
            target.targetZ = partyTargetZ;
            target.deltaX = deltaPartyX;
            target.deltaY = deltaPartyY;
            target.deltaZ = deltaPartyZ;
            target.horizontalDistanceToTarget = horizontalDistanceToParty;
            target.distanceToTarget = distanceToParty;
            target.edgeDistance = edgeDistanceToParty;
            target.canSense = true;
            bestPriorityDistanceSquared = distanceToParty * distanceToParty;
        }
    }

    for (OutdoorCombatTargetCandidate &candidate : candidates)
    {
        if (candidate.actorIndex == actorIndex || candidate.unavailable)
        {
            continue;
        }

        const float deltaX = candidate.preciseX - actor.preciseX;
        const float deltaY = candidate.preciseY - actor.preciseY;

        if (std::abs(deltaX) > HostilityLongRange || std::abs(deltaY) > HostilityLongRange)
        {
            continue;
        }

        const GameplayActorTargetPolicyResult targetPolicy =
            pGameplayActorService->resolveActorTargetPolicy(actorPolicyState, candidate.policyState);

        if (!targetPolicy.canTarget)
        {
            continue;
        }

        const float deltaZ = candidate.targetZ - actorTargetZ;
        const float distanceSquaredToCandidate = lengthSquared3d(deltaX, deltaY, deltaZ);

        if (distanceSquaredToCandidate >= bestPriorityDistanceSquared)
        {
            continue;
        }

        if (!isWithinRange3d(deltaX, deltaY, deltaZ, targetPolicy.engagementRange))
        {
            continue;
        }

        if (!candidate.lineOfSightChecked)
        {
            candidate.hasLineOfSight =
                hasClearOutdoorLineOfSight(
                    actorIndex,
                    candidate.actorIndex,
                    bx::Vec3{actor.preciseX, actor.preciseY, actorTargetZ},
                    bx::Vec3{candidate.preciseX, candidate.preciseY, candidate.targetZ});
            candidate.lineOfSightChecked = true;
        }

        if (!candidate.hasLineOfSight)
        {
            continue;
        }

        const float horizontalDistanceToCandidate = length2d(deltaX, deltaY);
        const float distanceToCandidate = length3d(deltaX, deltaY, deltaZ);
        const float edgeDistance =
            std::max(
                0.0f,
                distanceToCandidate - static_cast<float>(actor.radius) - static_cast<float>(candidate.radius));
        target.kind = OutdoorTargetKind::Actor;
        target.actorIndex = candidate.actorIndex;
        target.relationToTarget = targetPolicy.relationToTarget;
        target.targetX = candidate.preciseX;
        target.targetY = candidate.preciseY;
        target.targetZ = candidate.targetZ;
        target.deltaX = deltaX;
        target.deltaY = deltaY;
        target.deltaZ = deltaZ;
        target.horizontalDistanceToTarget = horizontalDistanceToCandidate;
        target.distanceToTarget = distanceToCandidate;
        target.edgeDistance = edgeDistance;
        target.canSense = true;
        bestPriorityDistanceSquared = distanceSquaredToCandidate;
    }

    return target;
}

OutdoorEngagementState resolveOutdoorEngagementState(
    const GameplayActorService &actorService,
    const GameplayActorTargetPolicyState &actorPolicyState,
    const OutdoorTargetFacts &combatTarget,
    GameplayActorAiType aiType,
    uint8_t hostilityType,
    int currentHp,
    int maxHp,
    bool hostileToParty,
    bool partyIsVeryNearActor)
{
    OutdoorEngagementState engagement = {};
    const bool targetIsActor = combatTarget.kind == OutdoorTargetKind::Actor;
    const bool hasCombatTarget = combatTarget.kind != OutdoorTargetKind::None;
    engagement.shouldEngageTarget = hasCombatTarget && combatTarget.canSense;
    engagement.inMeleeRange = combatTarget.edgeDistance <= meleeRangeForCombatTarget(targetIsActor);

    if (targetIsActor && hostilityType == 0 && !actorService.isPartyControlledActor(actorPolicyState.controlMode))
    {
        engagement.promotionRange =
            actorService.hostilityPromotionRangeForFriendlyActor(combatTarget.relationToTarget);
        engagement.shouldPromoteHostility =
            combatTarget.relationToTarget == 1
            || (engagement.promotionRange >= 0.0f
                && lengthSquared3d(combatTarget.deltaX, combatTarget.deltaY, combatTarget.deltaZ)
                    <= engagement.promotionRange * engagement.promotionRange);

        if (!engagement.shouldPromoteHostility)
        {
            engagement.shouldEngageTarget = false;
        }
    }

    engagement.shouldFlee =
        engagement.shouldEngageTarget
        && combatTarget.distanceToTarget <= HostilityLongRange
        && actorService.shouldFleeForAiType(aiType, currentHp, maxHp);
    engagement.friendlyNearParty = !engagement.shouldEngageTarget && !hostileToParty && partyIsVeryNearActor;
    return engagement;
}

void resetCrowdSteeringState(OutdoorWorldRuntime::MapActorState &actor)
{
    actor.crowdSideLockRemainingSeconds = 0.0f;
    actor.crowdNoProgressSeconds = 0.0f;
    actor.crowdLastEdgeDistance = 0.0f;
    actor.crowdRetreatRemainingSeconds = 0.0f;
    actor.crowdStandRemainingSeconds = 0.0f;
    actor.crowdProbeX = actor.preciseX;
    actor.crowdProbeY = actor.preciseY;
    actor.crowdProbeEdgeDistance = 0.0f;
    actor.crowdProbeElapsedSeconds = 0.0f;
    actor.crowdEscapeAttempts = 0;
    actor.crowdSideSign = 0;
}

void updateInactiveActorPresentation(
    OutdoorWorldRuntime::MapActorState &actor,
    float partyX,
    float partyY,
    const GameplayActorService *pGameplayActorService)
{
    if (actor.isDead || actor.aiState == OutdoorWorldRuntime::ActorAiState::Dead)
    {
        actor.aiState = OutdoorWorldRuntime::ActorAiState::Dead;
        actor.animation = OutdoorWorldRuntime::ActorAnimation::Dead;
        actor.moveDirectionX = 0.0f;
        actor.moveDirectionY = 0.0f;
        actor.velocityX = 0.0f;
        actor.velocityY = 0.0f;
        actor.velocityZ = 0.0f;
        actor.actionSeconds = 0.0f;
        actor.attackImpactTriggered = false;
        return;
    }

    actor.aiState = OutdoorWorldRuntime::ActorAiState::Standing;
    actor.moveDirectionX = 0.0f;
    actor.moveDirectionY = 0.0f;
    actor.velocityX = 0.0f;
    actor.velocityY = 0.0f;
    actor.velocityZ = 0.0f;
    actor.hasDetectedParty = false;
    actor.attackImpactTriggered = false;

    const float deltaX = partyX - actor.preciseX;
    const float deltaY = partyY - actor.preciseY;

    if (std::abs(deltaX) > 0.01f || std::abs(deltaY) > 0.01f)
    {
        actor.yawRadians = std::atan2(deltaY, deltaX);
    }

    actor.animationTimeTicks += ActorUpdateStepSeconds * TicksPerSecond;
    actor.actionSeconds = std::max(0.0f, actor.actionSeconds - ActorUpdateStepSeconds);
    actor.idleDecisionSeconds = std::max(0.0f, actor.idleDecisionSeconds - ActorUpdateStepSeconds);

    if (actor.animation == OutdoorWorldRuntime::ActorAnimation::Bored && actor.actionSeconds > 0.0f)
    {
        return;
    }

    actor.animation = OutdoorWorldRuntime::ActorAnimation::Standing;

    if (actor.idleDecisionSeconds > 0.0f)
    {
        return;
    }

    actor.idleDecisionSeconds = InactiveActorDecisionIntervalSeconds;

    if (pGameplayActorService == nullptr)
    {
        return;
    }

    const uint32_t decisionSeed = inactiveActorDecisionSeed(actor.actorId, actor.idleDecisionCount, 0x7f4a7c15u);
    actor.idleDecisionCount += 1;

    if ((decisionSeed % 100u) < InactiveActorFidgetChancePercent)
    {
        actor.attackImpactTriggered = false;
        actor.actionSeconds = InactiveActorBoredSeconds;
        actor.idleDecisionSeconds = InactiveActorBoredSeconds;
        actor.animation = OutdoorWorldRuntime::ActorAnimation::Bored;
        actor.animationTimeTicks = 0.0f;
    }
}

char tierLetterForSummonLevel(uint32_t level)
{
    const uint32_t clampedLevel = std::clamp(level, 1u, 3u);
    return static_cast<char>('A' + (clampedLevel - 1u));
}

std::string encounterPictureBase(const MapEncounterInfo &encounter)
{
    return encounter.pictureName.empty() ? encounter.monsterName : encounter.pictureName;
}

OutdoorWorldRuntime::SpawnPointState buildSpawnPointState(
    const MapStatsEntry &map,
    const MonsterTable &monsterTable,
    const OutdoorSpawn &spawn
)
{
    OutdoorWorldRuntime::SpawnPointState state = {};
    state.x = spawn.x;
    state.y = spawn.y;
    state.z = spawn.z;
    state.radius = spawn.radius;
    state.typeId = spawn.typeId;
    state.index = spawn.index;
    state.attributes = spawn.attributes;
    state.group = spawn.group;

    if (spawn.typeId != 3)
    {
        return state;
    }

    const EncounterSpawnDescriptor descriptor = resolveEncounterSpawnDescriptor(spawn.index);
    state.encounterSlot = descriptor.encounterSlot;
    state.isFixedTier = descriptor.fixedTier != '\0';
    state.fixedTier = descriptor.fixedTier;

    const MapEncounterInfo *pEncounter = getEncounterInfo(map, descriptor.encounterSlot);

    if (pEncounter == nullptr)
    {
        return state;
    }

    state.minCount = pEncounter->minCount;
    state.maxCount = pEncounter->maxCount;
    state.monsterFamilyName = pEncounter->monsterName;

    const MonsterTable::MonsterStatsEntry *pStats =
        resolveEncounterMonsterStats(
            map,
            monsterTable,
            descriptor.encounterSlot,
            descriptor.fixedTier != '\0' ? descriptor.fixedTier : 'A');

    if (pStats == nullptr)
    {
        return state;
    }

    state.representativePictureName = pStats->pictureName;
    state.representativeMonsterId = static_cast<int16_t>(pStats->id);
    state.hostilityType = static_cast<uint8_t>(pStats->hostility);
    state.hostileToParty = monsterTable.isHostileToParty(state.representativeMonsterId);
    return state;
}

float wanderRadiusForMovementType(MonsterTable::MonsterMovementType movementType)
{
    switch (movementType)
    {
        case MonsterTable::MonsterMovementType::Short:
            return 1024.0f;

        case MonsterTable::MonsterMovementType::Medium:
            return 2560.0f;

        case MonsterTable::MonsterMovementType::Long:
            return 5120.0f;

        case MonsterTable::MonsterMovementType::Global:
        case MonsterTable::MonsterMovementType::Free:
            return 10240.0f;

        case MonsterTable::MonsterMovementType::Stationary:
            return 0.0f;
    }

    return 0.0f;
}

bool isRangedAttackAbility(
    const MonsterTable::MonsterStatsEntry &stats,
    OutdoorWorldRuntime::MonsterAttackAbility ability)
{
    switch (ability)
    {
        case OutdoorWorldRuntime::MonsterAttackAbility::Attack1:
            return stats.attack1HasMissile;

        case OutdoorWorldRuntime::MonsterAttackAbility::Attack2:
            return stats.attack2HasMissile;

        case OutdoorWorldRuntime::MonsterAttackAbility::Spell1:
        case OutdoorWorldRuntime::MonsterAttackAbility::Spell2:
            return true;
    }

    return false;
}

OutdoorWorldRuntime::ActorAnimation attackAnimationForAbility(
    const MonsterTable::MonsterStatsEntry &stats,
    OutdoorWorldRuntime::MonsterAttackAbility ability)
{
    return isRangedAttackAbility(stats, ability)
        ? OutdoorWorldRuntime::ActorAnimation::AttackRanged
        : OutdoorWorldRuntime::ActorAnimation::AttackMelee;
}

bool isMeleeAttackAbility(
    const MonsterTable::MonsterStatsEntry &stats,
    OutdoorWorldRuntime::MonsterAttackAbility ability)
{
    return !isRangedAttackAbility(stats, ability);
}

bool shouldMaterializeEncounterSpawnsOnInitialize(const std::optional<MapDeltaData> &outdoorMapDeltaData)
{
    return outdoorMapDeltaData.has_value() && outdoorMapDeltaData->locationInfo.lastRespawnDay == 0;
}
}

uint32_t OutdoorWorldRuntime::makeChestSeed(uint32_t sessionSeed, int mapId, uint32_t chestId, uint32_t salt)
{
    return sessionSeed
        ^ static_cast<uint32_t>(mapId) * 1315423911u
        ^ (chestId + 1u) * 2654435761u
        ^ (salt + 1u) * 2246822519u;
}

int OutdoorWorldRuntime::generateGoldAmount(int treasureLevel, std::mt19937 &rng)
{
    switch (treasureLevel)
    {
        case 1: return std::uniform_int_distribution<int>(50, 100)(rng);
        case 2: return std::uniform_int_distribution<int>(100, 200)(rng);
        case 3: return std::uniform_int_distribution<int>(200, 500)(rng);
        case 4: return std::uniform_int_distribution<int>(500, 1000)(rng);
        case 5: return std::uniform_int_distribution<int>(1000, 2000)(rng);
        case 6: return std::uniform_int_distribution<int>(2000, 5000)(rng);
        default: return 0;
    }
}

std::pair<int, int> OutdoorWorldRuntime::remapTreasureLevelRange(int itemTreasureLevel, int mapTreasureLevel)
{
    static constexpr int mapping[7][7][2] = {
        {{1, 1}, {1, 1}, {1, 1}, {1, 1}, {1, 1}, {1, 1}, {1, 1}},
        {{1, 1}, {1, 2}, {2, 2}, {2, 2}, {2, 2}, {2, 2}, {2, 2}},
        {{1, 2}, {2, 2}, {2, 3}, {3, 3}, {3, 3}, {3, 3}, {3, 3}},
        {{2, 2}, {2, 2}, {3, 3}, {3, 4}, {4, 4}, {4, 4}, {4, 4}},
        {{2, 2}, {2, 2}, {3, 4}, {4, 4}, {4, 5}, {5, 5}, {5, 5}},
        {{2, 2}, {2, 2}, {4, 4}, {4, 5}, {5, 5}, {5, 6}, {6, 6}},
        {{2, 2}, {2, 2}, {7, 7}, {7, 7}, {7, 7}, {7, 7}, {7, 7}}
    };

    const int clampedItemLevel = std::clamp(itemTreasureLevel, RandomChestItemMinLevel, RandomChestItemMaxLevel);
    const int clampedMapLevel = std::clamp(mapTreasureLevel, RandomChestItemMinLevel, RandomChestItemMaxLevel);
    const int minLevel = mapping[clampedItemLevel - 1][clampedMapLevel - 1][0];
    const int maxLevel = mapping[clampedItemLevel - 1][clampedMapLevel - 1][1];
    return {minLevel, maxLevel};
}

int OutdoorWorldRuntime::sampleRemappedTreasureLevel(int itemTreasureLevel, int mapTreasureLevel, std::mt19937 &rng)
{
    const auto [minimumLevel, maximumLevel] = remapTreasureLevelRange(itemTreasureLevel, mapTreasureLevel);
    return std::uniform_int_distribution<int>(minimumLevel, maximumLevel)(rng);
}

int OutdoorWorldRuntime::normalizedMapTreasureLevel() const
{
    return std::clamp(m_mapTreasureLevel + 1, RandomChestItemMinLevel, RandomChestItemMaxLevel);
}

void OutdoorWorldRuntime::pushAudioEvent(
    uint32_t soundId,
    uint32_t sourceId,
    const std::string &reason,
    float x,
    float y,
    float z,
    bool positional)
{
    if (soundId == 0)
    {
        return;
    }

    AudioEvent event = {};
    event.soundId = soundId;
    event.sourceId = sourceId;
    event.reason = reason;
    event.x = x;
    event.y = y;
    event.z = z;
    event.positional = positional;
    m_pendingAudioEvents.push_back(std::move(event));
}

void OutdoorWorldRuntime::pushProjectileAudioEvent(
    const GameplayProjectileService::ProjectileAudioRequest &request)
{
    pushAudioEvent(
        request.soundId,
        request.sourceId,
        request.reason,
        request.x,
        request.y,
        request.z,
        request.positional);
}

OutdoorWorldRuntime::ChestViewState OutdoorWorldRuntime::buildChestView(uint32_t chestId) const
{
    if (chestId >= m_chests.size())
    {
        return {};
    }

    return buildMaterializedChestView(
        chestId,
        m_chests[chestId],
        m_mapTreasureLevel,
        m_mapId,
        m_sessionChestSeed,
        m_pChestTable,
        m_pItemTable,
        m_pParty);
}

void OutdoorWorldRuntime::activateChestView(uint32_t chestId)
{
    if (chestId >= m_chests.size())
    {
        return;
    }

    if (chestId >= m_materializedChestViews.size())
    {
        return;
    }

    if (!m_materializedChestViews[chestId].has_value())
    {
        m_materializedChestViews[chestId] = buildChestView(chestId);
    }

    m_activeChestView = *m_materializedChestViews[chestId];
    pushAudioEvent(
        static_cast<uint32_t>(SoundId::OpenChest),
        chestId,
        "chest_open",
        0.0f,
        0.0f,
        0.0f,
        false);
}

void OutdoorWorldRuntime::initialize(
    const MapStatsEntry &map,
    const MonsterTable &monsterTable,
    const MonsterProjectileTable &monsterProjectileTable,
    const ObjectTable &objectTable,
    const SpellTable &spellTable,
    const ItemTable &itemTable,
    Party *pParty,
    OutdoorPartyRuntime *pPartyRuntime,
    const StandardItemEnchantTable &standardItemEnchantTable,
    const SpecialItemEnchantTable &specialItemEnchantTable,
    const ChestTable *pChestTable,
    const std::optional<OutdoorMapData> &outdoorMapData,
    const std::optional<MapDeltaData> &outdoorMapDeltaData,
    const std::optional<OutdoorWeatherProfile> &outdoorWeatherProfile,
    const std::optional<EventRuntimeState> &eventRuntimeState,
    const std::optional<ActorPreviewBillboardSet> &outdoorActorPreviewBillboardSet,
    const std::optional<std::vector<uint8_t>> &outdoorLandMask,
    const std::optional<OutdoorDecorationCollisionSet> &outdoorDecorationCollisionSet,
    const std::optional<OutdoorActorCollisionSet> &outdoorActorCollisionSet,
    const std::optional<OutdoorSpriteObjectCollisionSet> &outdoorSpriteObjectCollisionSet,
    const std::optional<SpriteObjectBillboardSet> &outdoorSpriteObjectBillboardSet,
    GameplayActorService *pGameplayActorService,
    GameplayProjectileService *pGameplayProjectileService,
    GameplayCombatController *pGameplayCombatController,
    GameplayFxService *pGameplayFxService
)
{
    m_mapId = map.id;
    m_map = map;
    m_mapName = map.name;
    m_mapTreasureLevel = map.treasureLevel;
    m_gameMinutes = 9.0f * 60.0f;
    m_atmosphereState = buildAtmosphereSourceState(map, outdoorMapData, outdoorMapDeltaData);
    m_outdoorWeatherProfile = outdoorWeatherProfile;
    m_timers.clear();
    m_mapActors.clear();
    m_spawnPoints.clear();
    m_mapActorCorpseViews.clear();
    m_activeCorpseView.reset();
    m_pendingAudioEvents.clear();
    m_worldItems.clear();
    m_chests = outdoorMapDeltaData ? outdoorMapDeltaData->chests : std::vector<MapDeltaChest>();
    m_openedChests.assign(outdoorMapDeltaData ? outdoorMapDeltaData->chests.size() : 0, false);
    m_materializedChestViews.assign(m_chests.size(), std::nullopt);
    m_activeChestView.reset();
    m_eventRuntimeState = eventRuntimeState;
    m_pItemTable = &itemTable;
    m_pParty = pParty;
    m_pPartyRuntime = pPartyRuntime;
    m_pStandardItemEnchantTable = &standardItemEnchantTable;
    m_pSpecialItemEnchantTable = &specialItemEnchantTable;
    m_pChestTable = pChestTable;
    m_pMonsterTable = &monsterTable;
    m_pMonsterProjectileTable = &monsterProjectileTable;
    m_pObjectTable = &objectTable;
    m_pOutdoorMapData = outdoorMapData ? &*outdoorMapData : nullptr;
    m_pOutdoorMapDeltaData = outdoorMapDeltaData ? &*outdoorMapDeltaData : nullptr;
    m_outdoorLandMask = outdoorLandMask;
    m_pSpellTable = &spellTable;
    m_pGameplayActorService = pGameplayActorService;
    m_pGameplayProjectileService = pGameplayProjectileService;
    m_pGameplayCombatController = pGameplayCombatController;
    m_pGameplayFxService = pGameplayFxService;
    projectileService().clear();
    if (m_pGameplayCombatController != nullptr)
    {
        m_pGameplayCombatController->clearPendingCombatEvents();
    }
    m_pActorSpriteFrameTable = outdoorActorPreviewBillboardSet ? &outdoorActorPreviewBillboardSet->spriteFrameTable : nullptr;
    m_pProjectileSpriteFrameTable = outdoorSpriteObjectBillboardSet
        ? &outdoorSpriteObjectBillboardSet->spriteFrameTable
        : m_pActorSpriteFrameTable;
    m_pParticleSystem = nullptr;
    m_monsterVisualsById.clear();
    m_outdoorFaces.clear();
    m_outdoorFaceGridCells.clear();
    m_outdoorFaceGridMinX = 0.0f;
    m_outdoorFaceGridMinY = 0.0f;
    m_outdoorFaceGridWidth = 0;
    m_outdoorFaceGridHeight = 0;
    m_outdoorMovementController.reset();
    m_actorUpdateAccumulatorSeconds = 0.0f;
    m_nextWorldItemId = 1;
    m_armageddonState = {};

    materializeMapDeltaWorldItems();
    applyInitialWeatherProfile();
    refreshAtmosphereState();

    if (outdoorActorPreviewBillboardSet)
    {
        for (const ActorPreviewBillboard &billboard : outdoorActorPreviewBillboardSet->billboards)
        {
            if (billboard.monsterId <= 0)
            {
                continue;
            }

            MonsterVisualState &visualState = m_monsterVisualsById[billboard.monsterId];

            if (visualState.spriteFrameIndex == 0 && billboard.spriteFrameIndex != 0)
            {
                visualState.spriteFrameIndex = billboard.spriteFrameIndex;
            }

            for (size_t actionIndex = 0; actionIndex < visualState.actionSpriteFrameIndices.size(); ++actionIndex)
            {
                if (visualState.actionSpriteFrameIndices[actionIndex] == 0
                    && billboard.actionSpriteFrameIndices[actionIndex] != 0)
                {
                    visualState.actionSpriteFrameIndices[actionIndex] = billboard.actionSpriteFrameIndices[actionIndex];
                }
            }
        }
    }

    if (m_pOutdoorMapData != nullptr)
    {
        for (size_t bModelIndex = 0; bModelIndex < m_pOutdoorMapData->bmodels.size(); ++bModelIndex)
        {
            const OutdoorBModel &bModel = m_pOutdoorMapData->bmodels[bModelIndex];

            for (size_t faceIndex = 0; faceIndex < bModel.faces.size(); ++faceIndex)
            {
                OutdoorFaceGeometryData geometry = {};

                if (buildOutdoorFaceGeometry(bModel, bModelIndex, bModel.faces[faceIndex], faceIndex, geometry))
                {
                    m_outdoorFaces.push_back(std::move(geometry));
                }
            }
        }

        buildOutdoorFaceSpatialIndex();
    }

    if (outdoorMapData)
    {
        m_outdoorMovementController.emplace(
            *outdoorMapData,
            outdoorLandMask,
            outdoorDecorationCollisionSet,
            outdoorActorCollisionSet,
            outdoorSpriteObjectCollisionSet);
    }
    m_nextActorId = 0;
    projectileService().clear();

    if (outdoorMapDeltaData)
    {
        std::vector<float> mapActorAttackAnimationSeconds(outdoorMapDeltaData->actors.size(), 0.3f);

        if (outdoorActorPreviewBillboardSet)
        {
            for (const ActorPreviewBillboard &billboard : outdoorActorPreviewBillboardSet->billboards)
            {
                if (billboard.source != ActorPreviewSource::Companion
                    || billboard.runtimeActorIndex >= mapActorAttackAnimationSeconds.size())
                {
                    continue;
                }

                uint16_t attackFrameIndex =
                    billboard.actionSpriteFrameIndices[static_cast<size_t>(ActorAnimation::AttackMelee)];

                if (attackFrameIndex == 0)
                {
                    attackFrameIndex =
                        billboard.actionSpriteFrameIndices[static_cast<size_t>(ActorAnimation::AttackRanged)];
                }

                if (attackFrameIndex == 0)
                {
                    continue;
                }

                const SpriteFrameEntry *pAttackFrame =
                    outdoorActorPreviewBillboardSet->spriteFrameTable.getFrame(attackFrameIndex, 0);

                if (pAttackFrame == nullptr || pAttackFrame->animationLengthTicks <= 0)
                {
                    continue;
                }

                mapActorAttackAnimationSeconds[billboard.runtimeActorIndex] =
                    static_cast<float>(pAttackFrame->animationLengthTicks) / TicksPerSecond;
            }
        }

        m_mapActors.reserve(outdoorMapDeltaData->actors.size());
        m_mapActorCorpseViews.assign(outdoorMapDeltaData->actors.size(), std::nullopt);

        for (size_t actorIndex = 0; actorIndex < outdoorMapDeltaData->actors.size(); ++actorIndex)
        {
            MapActorState actorState = buildMapActorState(
                monsterTable,
                outdoorMapDeltaData->actors[actorIndex],
                static_cast<uint32_t>(actorIndex),
                m_pOutdoorMapData,
                mapActorAttackAnimationSeconds[actorIndex]);
            const MonsterTable::MonsterStatsEntry *pStats = monsterTable.findStatsById(actorState.monsterId);
            applyTestActorOverrides(map.id, m_pOutdoorMapData, pStats, actorState.actorId, actorState);

            if (outdoorActorPreviewBillboardSet)
            {
                for (const ActorPreviewBillboard &billboard : outdoorActorPreviewBillboardSet->billboards)
                {
                    if (billboard.source != ActorPreviewSource::Companion
                        || billboard.runtimeActorIndex != actorIndex)
                    {
                        continue;
                    }

                    actorState.spriteFrameIndex = billboard.spriteFrameIndex;
                    actorState.actionSpriteFrameIndices = billboard.actionSpriteFrameIndices;
                    actorState.useStaticSpriteFrame = billboard.useStaticFrame;
                    break;
                }
            }

            m_mapActors.push_back(std::move(actorState));
        }

        if (m_outdoorMovementController)
        {
            for (MapActorState &actor : m_mapActors)
            {
                const MonsterTable::MonsterStatsEntry *pStats = monsterTable.findStatsById(actor.monsterId);
                const float collisionRadius = actorCollisionRadius(actor, pStats);
                actor.movementState = m_outdoorMovementController->initializeStateForBody(
                    actor.preciseX,
                    actor.preciseY,
                    actor.preciseZ + GroundSnapHeight,
                    collisionRadius);
                actor.movementStateInitialized = true;
                syncActorFromMovementState(actor);
                actor.homePreciseZ = actor.preciseZ;
                actor.homeZ = actor.z;
            }
        }

        m_nextActorId = static_cast<uint32_t>(m_mapActors.size());
    }

    std::random_device randomDevice;
    const uint64_t timeSeed = static_cast<uint64_t>(
        std::chrono::steady_clock::now().time_since_epoch().count());
    m_sessionChestSeed = randomDevice() ^ static_cast<uint32_t>(timeSeed) ^ static_cast<uint32_t>(timeSeed >> 32);

    if (outdoorMapData)
    {
        m_spawnPoints.reserve(outdoorMapData->spawns.size());

        for (const OutdoorSpawn &spawn : outdoorMapData->spawns)
        {
            m_spawnPoints.push_back(buildSpawnPointState(map, monsterTable, spawn));
        }

        if (shouldMaterializeEncounterSpawnsOnInitialize(outdoorMapDeltaData))
        {
            for (size_t spawnIndex = 0; spawnIndex < m_spawnPoints.size(); ++spawnIndex)
            {
                const SpawnPointState &spawn = m_spawnPoints[spawnIndex];

                if (spawn.typeId == 2)
                {
                    materializeTreasureSpawnFromSpawnPoint(spawnIndex);
                    continue;
                }

                if (spawn.typeId != 3 || spawn.encounterSlot <= 0)
                {
                    continue;
                }

                const uint32_t resolvedCount = resolveEncounterSpawnCount(
                    m_map,
                    spawn.encounterSlot,
                    0,
                    m_sessionChestSeed,
                    static_cast<uint32_t>(spawnIndex));

                spawnEncounterFromResolvedData(
                    spawn.encounterSlot,
                    spawn.fixedTier,
                    resolvedCount,
                    static_cast<float>(spawn.x),
                    static_cast<float>(spawn.y),
                    static_cast<float>(spawn.z),
                    spawn.radius,
                    spawn.attributes,
                    spawn.group,
                    0,
                    true,
                    spawnIndex,
                    false);
            }
        }
    }

    applyEventRuntimeState();
}

void OutdoorWorldRuntime::setParticleSystem(ParticleSystem *pParticleSystem)
{
    m_pParticleSystem = pParticleSystem;
}

bool OutdoorWorldRuntime::resolveWorldItemVisual(
    uint32_t itemId,
    uint16_t &objectDescriptionId,
    uint16_t &objectSpriteId,
    uint16_t &objectSpriteFrameIndex,
    uint16_t &objectFlags,
    uint16_t &radius,
    uint16_t &height,
    std::string &objectName,
    std::string &objectSpriteName) const
{
    if (m_pItemTable == nullptr || m_pObjectTable == nullptr || itemId == 0)
    {
        return false;
    }

    const ItemDefinition *pItemDefinition = m_pItemTable->get(itemId);

    if (pItemDefinition == nullptr || pItemDefinition->spriteIndex == 0)
    {
        return false;
    }

    const std::optional<uint16_t> descriptionId =
        m_pObjectTable->findDescriptionIdByObjectId(static_cast<int16_t>(pItemDefinition->spriteIndex));

    if (!descriptionId)
    {
        return false;
    }

    const ObjectEntry *pObjectEntry = m_pObjectTable->get(*descriptionId);

    if (pObjectEntry == nullptr || (pObjectEntry->flags & ObjectDescNoSprite) != 0 || pObjectEntry->spriteId == 0)
    {
        return false;
    }

    objectDescriptionId = *descriptionId;
    objectSpriteId = pObjectEntry->spriteId;
    objectSpriteFrameIndex = resolveRuntimeSpriteFrameIndex(
        m_pProjectileSpriteFrameTable,
        pObjectEntry->spriteId,
        pObjectEntry->spriteName);
    objectFlags = pObjectEntry->flags;
    radius = static_cast<uint16_t>(std::max<int16_t>(0, pObjectEntry->radius));
    height = static_cast<uint16_t>(std::max<int16_t>(0, pObjectEntry->height));
    objectName = pObjectEntry->internalName;
    objectSpriteName = pObjectEntry->spriteName;
    return true;
}

bool OutdoorWorldRuntime::materializeTreasureSpawnFromSpawnPoint(size_t spawnPointIndex)
{
    if (spawnPointIndex >= m_spawnPoints.size()
        || m_pItemTable == nullptr
        || m_pObjectTable == nullptr
        || m_pStandardItemEnchantTable == nullptr
        || m_pSpecialItemEnchantTable == nullptr)
    {
        return false;
    }

    const SpawnPointState &spawn = m_spawnPoints[spawnPointIndex];

    if (spawn.typeId != 2)
    {
        return false;
    }

    const int treasureLevel = std::clamp(static_cast<int>(spawn.index), RandomChestItemMinLevel, RandomChestItemMaxLevel);
    const int mapTreasureLevel = normalizedMapTreasureLevel();
    const uint32_t seed = makeChestSeed(m_sessionChestSeed, m_mapId, static_cast<uint32_t>(spawnPointIndex), 0x54524541u);
    std::mt19937 rng(seed);
    const int resolvedTreasureLevel = sampleRemappedTreasureLevel(treasureLevel, mapTreasureLevel, rng);
    InventoryItem item = {};
    uint32_t goldAmount = 0;
    const auto canMaterializeAsWorldItem =
        [this](const ItemDefinition &entry)
        {
            uint16_t objectDescriptionId = 0;
            uint16_t objectSpriteId = 0;
            uint16_t objectSpriteFrameIndex = 0;
            uint16_t objectFlags = 0;
            uint16_t radius = 0;
            uint16_t height = 0;
            std::string objectName;
            std::string objectSpriteName;
            return resolveWorldItemVisual(
                entry.itemId,
                objectDescriptionId,
                objectSpriteId,
                objectSpriteFrameIndex,
                objectFlags,
                radius,
                height,
                objectName,
                objectSpriteName);
        };

    if (resolvedTreasureLevel != RandomChestItemMaxLevel)
    {
        const int roll = std::uniform_int_distribution<int>(0, 99)(rng);

        if (roll < 20)
        {
            return false;
        }

        if (roll < 60)
        {
            goldAmount = static_cast<uint32_t>(std::max(0, generateGoldAmount(treasureLevel, rng)));
            const uint32_t goldHeapItemId = goldAmount <= 200 ? GoldHeapSmallItemId : GoldHeapLargeItemId;
            item = ItemGenerator::makeInventoryItem(goldHeapItemId, *m_pItemTable, ItemGenerationMode::ChestLoot);
        }
        else
        {
            ItemGenerationRequest request = {};
            request.treasureLevel = std::min(resolvedTreasureLevel, SpawnableItemTreasureLevels);
            request.mode = ItemGenerationMode::ChestLoot;
            const std::optional<InventoryItem> generatedItem =
                ItemGenerator::generateRandomInventoryItem(
                    *m_pItemTable,
                    *m_pStandardItemEnchantTable,
                    *m_pSpecialItemEnchantTable,
                    request,
                    m_pParty,
                    rng,
                    canMaterializeAsWorldItem);

            if (!generatedItem)
            {
                return false;
            }

            item = *generatedItem;
        }
    }
    else
    {
        ItemGenerationRequest request = {};
        request.treasureLevel = SpawnableItemTreasureLevels;
        request.mode = ItemGenerationMode::ChestLoot;
        request.allowRareItems = true;
        request.rareItemsOnly = true;
        const std::optional<InventoryItem> generatedItem =
            ItemGenerator::generateRandomInventoryItem(
                *m_pItemTable,
                *m_pStandardItemEnchantTable,
                *m_pSpecialItemEnchantTable,
                request,
                m_pParty,
                rng,
                canMaterializeAsWorldItem);

        if (!generatedItem)
        {
            return false;
        }

        item = *generatedItem;
    }

    if (item.objectDescriptionId == 0)
    {
        return false;
    }

    uint16_t objectDescriptionId = 0;
    uint16_t objectSpriteId = 0;
    uint16_t objectSpriteFrameIndex = 0;
    uint16_t objectFlags = 0;
    uint16_t radius = 0;
    uint16_t height = 0;
    std::string objectName;
    std::string objectSpriteName;

    if (!resolveWorldItemVisual(
            item.objectDescriptionId,
            objectDescriptionId,
            objectSpriteId,
            objectSpriteFrameIndex,
            objectFlags,
            radius,
            height,
            objectName,
            objectSpriteName))
    {
        return false;
    }

    float worldZ = static_cast<float>(spawn.z);

    if (m_pOutdoorMapData != nullptr)
    {
        worldZ = worldItemFloorHeight(
            *m_pOutdoorMapData,
            static_cast<float>(spawn.x),
            static_cast<float>(spawn.y),
            worldZ);
    }

    WorldItemState worldItem = {};
    worldItem.worldItemId = m_nextWorldItemId++;
    worldItem.item = item;
    worldItem.goldAmount = goldAmount;
    worldItem.isGold = goldAmount > 0 && isGoldHeapItemId(item.objectDescriptionId);
    worldItem.objectDescriptionId = objectDescriptionId;
    worldItem.objectSpriteId = objectSpriteId;
    worldItem.objectSpriteFrameIndex = objectSpriteFrameIndex;
    worldItem.objectFlags = objectFlags;
    worldItem.radius = radius;
    worldItem.height = height;
    worldItem.attributes = spawn.attributes;
    worldItem.objectName = objectName;
    worldItem.objectSpriteName = objectSpriteName;
    worldItem.x = static_cast<float>(spawn.x);
    worldItem.y = static_cast<float>(spawn.y);
    worldItem.z = worldZ;
    worldItem.initialX = worldItem.x;
    worldItem.initialY = worldItem.y;
    worldItem.initialZ = worldItem.z;
    m_worldItems.push_back(std::move(worldItem));
    return true;
}

void OutdoorWorldRuntime::materializeMapDeltaWorldItems()
{
    if (m_pOutdoorMapDeltaData == nullptr || m_pItemTable == nullptr || m_pObjectTable == nullptr)
    {
        return;
    }

    for (const MapDeltaSpriteObject &spriteObject : m_pOutdoorMapDeltaData->spriteObjects)
    {
        if (!hasContainingItemPayload(spriteObject.rawContainingItem))
        {
            continue;
        }

        const ObjectEntry *pObjectEntry = m_pObjectTable->get(spriteObject.objectDescriptionId);

        if (pObjectEntry == nullptr || (pObjectEntry->flags & ObjectDescUnpickable) != 0)
        {
            continue;
        }

        int32_t rawItemId = 0;
        int32_t rawGoldAmount = 0;

        if (!readInt32FromBytes(spriteObject.rawContainingItem, 0x00, rawItemId)
            || !readInt32FromBytes(spriteObject.rawContainingItem, 0x0c, rawGoldAmount)
            || rawItemId <= 0)
        {
            continue;
        }

        uint16_t objectDescriptionId = 0;
        uint16_t objectSpriteId = 0;
        uint16_t objectSpriteFrameIndex = 0;
        uint16_t objectFlags = 0;
        uint16_t radius = 0;
        uint16_t height = 0;
        std::string objectName;
        std::string objectSpriteName;

        if (!resolveWorldItemVisual(
                static_cast<uint32_t>(rawItemId),
                objectDescriptionId,
                objectSpriteId,
                objectSpriteFrameIndex,
                objectFlags,
                radius,
                height,
                objectName,
                objectSpriteName))
        {
            continue;
        }

        const ItemDefinition *pItemDefinition = m_pItemTable->get(static_cast<uint32_t>(rawItemId));

        if (pItemDefinition == nullptr)
        {
            continue;
        }

        WorldItemState worldItem = {};
        worldItem.worldItemId = m_nextWorldItemId++;
        worldItem.item.objectDescriptionId = static_cast<uint32_t>(rawItemId);
        worldItem.item.quantity = 1;
        worldItem.item.width = pItemDefinition->inventoryWidth;
        worldItem.item.height = pItemDefinition->inventoryHeight;
        worldItem.goldAmount = isGoldHeapItemId(worldItem.item.objectDescriptionId)
            ? static_cast<uint32_t>(std::max(0, rawGoldAmount))
            : 0;
        worldItem.isGold = worldItem.goldAmount > 0 && isGoldHeapItemId(worldItem.item.objectDescriptionId);
        worldItem.objectDescriptionId = objectDescriptionId;
        worldItem.objectSpriteId = objectSpriteId;
        worldItem.objectSpriteFrameIndex = objectSpriteFrameIndex;
        worldItem.objectFlags = objectFlags;
        worldItem.radius = radius;
        worldItem.height = height;
        worldItem.soundId = spriteObject.soundId;
        worldItem.attributes = spriteObject.attributes;
        worldItem.sectorId = spriteObject.sectorId;
        worldItem.objectName = objectName;
        worldItem.objectSpriteName = objectSpriteName;
        worldItem.x = static_cast<float>(spriteObject.x);
        worldItem.y = static_cast<float>(spriteObject.y);
        worldItem.z = static_cast<float>(spriteObject.z);
        worldItem.velocityX = static_cast<float>(spriteObject.velocityX);
        worldItem.velocityY = static_cast<float>(spriteObject.velocityY);
        worldItem.velocityZ = static_cast<float>(spriteObject.velocityZ);
        worldItem.initialX = static_cast<float>(spriteObject.initialX);
        worldItem.initialY = static_cast<float>(spriteObject.initialY);
        worldItem.initialZ = static_cast<float>(spriteObject.initialZ);
        worldItem.timeSinceCreatedTicks = uint32_t(spriteObject.timeSinceCreated) * 8;
        worldItem.lifetimeTicks = spriteObject.temporaryLifetime > 0
            ? uint32_t(spriteObject.temporaryLifetime) * 8
            : 0;
        m_worldItems.push_back(std::move(worldItem));
    }
}

bool OutdoorWorldRuntime::spawnWorldItem(
    const InventoryItem &item,
    float sourceX,
    float sourceY,
    float sourceZ,
    float yawRadians)
{
    if (item.objectDescriptionId == 0)
    {
        return false;
    }

    uint16_t objectDescriptionId = 0;
    uint16_t objectSpriteId = 0;
    uint16_t objectSpriteFrameIndex = 0;
    uint16_t objectFlags = 0;
    uint16_t radius = 0;
    uint16_t height = 0;
    uint32_t lifetimeTicks = 0;
    std::string objectName;
    std::string objectSpriteName;

    if (!resolveWorldItemVisual(
            item.objectDescriptionId,
            objectDescriptionId,
            objectSpriteId,
            objectSpriteFrameIndex,
            objectFlags,
            radius,
            height,
            objectName,
            objectSpriteName))
    {
        return false;
    }

    const float directionX = std::cos(yawRadians);
    const float directionY = std::sin(yawRadians);
    const float horizontalSpeed = WorldItemThrowSpeed * std::cos(WorldItemThrowPitchRadians);
    const float verticalSpeed = WorldItemThrowSpeed * std::sin(WorldItemThrowPitchRadians);

    WorldItemState worldItem = {};
    worldItem.worldItemId = m_nextWorldItemId++;
    worldItem.item = item;
    worldItem.objectDescriptionId = objectDescriptionId;
    worldItem.objectSpriteId = objectSpriteId;
    worldItem.objectSpriteFrameIndex = objectSpriteFrameIndex;
    worldItem.objectFlags = objectFlags;
    worldItem.radius = radius;
    worldItem.height = height;
    worldItem.objectName = objectName;
    worldItem.objectSpriteName = objectSpriteName;
    worldItem.attributes = SpriteAttrDroppedByPlayer;
    worldItem.x = sourceX;
    worldItem.y = sourceY;
    worldItem.z = sourceZ;
    worldItem.velocityX = directionX * horizontalSpeed;
    worldItem.velocityY = directionY * horizontalSpeed;
    worldItem.velocityZ = verticalSpeed;
    worldItem.initialX = sourceX;
    worldItem.initialY = sourceY;
    worldItem.initialZ = sourceZ;
    worldItem.spawnedByPlayer = true;
    m_worldItems.push_back(std::move(worldItem));
    return true;
}

bool OutdoorWorldRuntime::spawnPartyFireSpikeTrap(
    uint32_t casterMemberIndex,
    uint32_t spellId,
    uint32_t skillLevel,
    uint32_t skillMastery,
    float x,
    float y,
    float z)
{
    if (m_pSpellTable == nullptr || m_pObjectTable == nullptr || m_pParty == nullptr)
    {
        return false;
    }

    const SpellEntry *pSpellEntry = m_pSpellTable->findById(static_cast<int>(spellId));

    if (pSpellEntry == nullptr || spellIdFromValue(spellId) != SpellId::FireSpike)
    {
        return false;
    }

    ResolvedProjectileDefinition definition = {};

    if (!resolveSpellDefinition(*pSpellEntry, *m_pObjectTable, definition))
    {
        return false;
    }

    GameplayProjectileService::FireSpikeTrapSpawnLimitInput spawnLimitInput = {};
    spawnLimitInput.sourceKind = ProjectileState::SourceKind::Party;
    spawnLimitInput.sourcePartyMemberIndex = casterMemberIndex;
    spawnLimitInput.skillMastery = skillMastery;
    spawnLimitInput.traps.reserve(m_fireSpikeTraps.size());

    for (const FireSpikeTrapState &trap : m_fireSpikeTraps)
    {
        GameplayProjectileService::FireSpikeActiveTrapFacts trapFacts = {};
        trapFacts.sourceKind = trap.sourceKind;
        trapFacts.sourcePartyMemberIndex = trap.sourcePartyMemberIndex;
        trapFacts.expired = trap.isExpired;
        spawnLimitInput.traps.push_back(trapFacts);
    }

    const GameplayProjectileService::FireSpikeTrapSpawnResult spawnResult =
        projectileService().buildFireSpikeTrapSpawn(spawnLimitInput);

    if (!spawnResult.accepted)
    {
        return false;
    }

    const float supportZ = sampleSupportFloorHeight(x, y, z + 256.0f, 512.0f, 32.0f);
    FireSpikeTrapState trap = {};
    trap.trapId = spawnResult.trapId;
    trap.sourceKind = ProjectileState::SourceKind::Party;
    trap.sourceId = casterMemberIndex + 1;
    trap.sourcePartyMemberIndex = casterMemberIndex;
    trap.objectDescriptionId = definition.objectDescriptionId;
    trap.objectSpriteId = definition.objectSpriteId;
    trap.objectSpriteFrameIndex = resolveRuntimeSpriteFrameIndex(
        m_pProjectileSpriteFrameTable,
        definition.objectSpriteId,
        definition.objectSpriteName);
    trap.impactObjectDescriptionId = definition.impactObjectDescriptionId;
    trap.objectFlags = definition.objectFlags | ObjectDescBounce;
    trap.radius = definition.radius;
    trap.height = definition.height;
    trap.spellId = definition.spellId;
    trap.effectSoundId = definition.effectSoundId;
    trap.skillLevel = skillLevel;
    trap.skillMastery = skillMastery;
    trap.objectName = definition.objectName;
    trap.objectSpriteName = definition.objectSpriteName;
    trap.x = x;
    trap.y = y;
    trap.z = supportZ + 1.0f;

    ProjectileState audioSource = {};
    audioSource.sourceKind = trap.sourceKind;
    audioSource.sourceId = trap.sourceId;
    audioSource.effectSoundId = trap.effectSoundId;
    m_fireSpikeTraps.push_back(std::move(trap));

    if (const std::optional<GameplayProjectileService::ProjectileAudioRequest> audioRequest =
            projectileService().buildProjectileReleaseAudioRequest(audioSource, x, y, supportZ))
    {
        pushProjectileAudioEvent(*audioRequest);
    }

    return true;
}

void OutdoorWorldRuntime::updateWorldItems(float deltaSeconds)
{
    if (deltaSeconds <= 0.0f || m_pOutdoorMapData == nullptr)
    {
        return;
    }

    for (WorldItemState &worldItem : m_worldItems)
    {
        if (worldItem.isExpired)
        {
            continue;
        }

        worldItem.timeSinceCreatedTicks += static_cast<uint32_t>(std::lround(deltaSeconds * TicksPerSecond));

        if (worldItem.lifetimeTicks > 0 && worldItem.timeSinceCreatedTicks >= worldItem.lifetimeTicks)
        {
            worldItem.isExpired = true;
            continue;
        }

        if (worldItem.velocityX == 0.0f && worldItem.velocityY == 0.0f && worldItem.velocityZ == 0.0f)
        {
            continue;
        }

        if ((worldItem.objectFlags & ObjectDescNoGravity) == 0)
        {
            worldItem.velocityZ -= WorldItemGravity * deltaSeconds;
        }

        worldItem.x += worldItem.velocityX * deltaSeconds;
        worldItem.y += worldItem.velocityY * deltaSeconds;
        worldItem.z += worldItem.velocityZ * deltaSeconds;

        if (isOutdoorTerrainWater(*m_pOutdoorMapData, worldItem.x, worldItem.y))
        {
            worldItem.isExpired = true;
            continue;
        }

        const float terrainFloorZ =
            sampleOutdoorRenderedTerrainHeight(*m_pOutdoorMapData, worldItem.x, worldItem.y) + WorldItemGroundClearance;
        float floorZ = terrainFloorZ;

        if (worldItem.z <= terrainFloorZ + WorldItemSupportFloorProbeHeight)
        {
            const float supportFloorZ =
                sampleOutdoorSupportFloorHeight(*m_pOutdoorMapData, worldItem.x, worldItem.y, worldItem.z)
                + WorldItemGroundClearance;
            floorZ = std::max(floorZ, supportFloorZ);
        }

        if (worldItem.z <= floorZ)
        {
            worldItem.z = floorZ;

            if ((worldItem.objectFlags & ObjectDescBounce) != 0
                && std::abs(worldItem.velocityZ) >= WorldItemBounceStopVelocity)
            {
                worldItem.velocityZ = -worldItem.velocityZ * WorldItemBounceFactor;
            }
            else
            {
                worldItem.velocityZ = 0.0f;
            }

            worldItem.velocityX *= WorldItemGroundDamping;
            worldItem.velocityY *= WorldItemGroundDamping;

            const float horizontalSpeedSquared =
                worldItem.velocityX * worldItem.velocityX + worldItem.velocityY * worldItem.velocityY;

            if (horizontalSpeedSquared < WorldItemRestingHorizontalSpeedSquared)
            {
                worldItem.velocityX = 0.0f;
                worldItem.velocityY = 0.0f;
            }
        }
    }

    m_worldItems.erase(
        std::remove_if(
            m_worldItems.begin(),
            m_worldItems.end(),
            [](const WorldItemState &worldItem)
            {
                return worldItem.isExpired;
            }),
        m_worldItems.end());
}

void OutdoorWorldRuntime::updateFireSpikeTraps(float deltaSeconds, float partyX, float partyY, float partyZ)
{
    if (deltaSeconds <= 0.0f)
    {
        return;
    }

    for (FireSpikeTrapState &trap : m_fireSpikeTraps)
    {
        if (trap.isExpired)
        {
            continue;
        }

        trap.timeSinceCreatedTicks =
            projectileService().advanceFireSpikeTrapLifetime(trap.timeSinceCreatedTicks, deltaSeconds);

        if (m_pOutdoorMapData != nullptr)
        {
            trap.z = sampleSupportFloorHeight(trap.x, trap.y, trap.z + 64.0f, 128.0f, 24.0f) + 1.0f;
        }

        GameplayProjectileService::FireSpikeTrapTriggerInput triggerInput = {};
        triggerInput.sourceKind = trap.sourceKind;
        triggerInput.trapId = trap.trapId;
        triggerInput.trapRadius = trap.radius;
        triggerInput.skillLevel = trap.skillLevel;
        triggerInput.skillMastery = trap.skillMastery;
        triggerInput.x = trap.x;
        triggerInput.y = trap.y;
        triggerInput.z = trap.z;
        triggerInput.actors.reserve(m_mapActors.size());

        for (size_t actorIndex = 0; actorIndex < m_mapActors.size(); ++actorIndex)
        {
            const MapActorState &actor = m_mapActors[actorIndex];

            GameplayProjectileService::FireSpikeTrapActorFacts actorFacts = {};
            actorFacts.actorIndex = actorIndex;
            actorFacts.actorId = actor.actorId;
            actorFacts.x = actor.preciseX;
            actorFacts.y = actor.preciseY;
            actorFacts.z = actor.preciseZ;
            actorFacts.radius = actor.radius;
            actorFacts.height = actor.height;
            actorFacts.unavailableForCombat = actor.isDead || isActorUnavailableForCombat(actor);
            actorFacts.hostileToParty = actor.hostileToParty;
            actorFacts.friendlyToTrapSource = projectileSourceIsFriendlyToActor(
                ProjectileState{
                    .sourceKind = trap.sourceKind,
                    .sourceId = trap.sourceId,
                    .sourcePartyMemberIndex = trap.sourcePartyMemberIndex,
                    .sourceMonsterId = trap.sourceMonsterId,
                    .fromSummonedMonster = trap.fromSummonedMonster,
                    .ability = trap.ability},
                actor);
            triggerInput.actors.push_back(actorFacts);
        }

        const GameplayProjectileService::FireSpikeTrapTriggerResult triggerResult =
            projectileService().buildFireSpikeTrapTrigger(triggerInput);

        if (triggerResult.triggered)
        {
            applyFireSpikeTrapTriggerResult(trap, triggerResult);
        }
    }

    std::erase_if(
        m_fireSpikeTraps,
        [](const FireSpikeTrapState &trap)
        {
            return trap.isExpired;
        });
}

void OutdoorWorldRuntime::applyFireSpikeTrapTriggerResult(
    FireSpikeTrapState &trap,
    const GameplayProjectileService::FireSpikeTrapTriggerResult &result)
{
    if (!result.triggered || result.actorIndex >= m_mapActors.size())
    {
        return;
    }

    if (result.applyActorImpact)
    {
        const size_t triggeredActorIndex = result.actorIndex;
        const int damage = result.damage;
        const int beforeHp = m_mapActors[triggeredActorIndex].currentHp;

        if (trap.sourceKind == ProjectileState::SourceKind::Party)
        {
            applyPartyAttackToMapActor(
                triggeredActorIndex,
                damage,
                trap.x,
                trap.y,
                trap.z);

            if (m_pGameplayCombatController != nullptr)
            {
                m_pGameplayCombatController->recordPartyProjectileActorImpact(
                    trap.sourceId,
                    trap.sourcePartyMemberIndex,
                    m_mapActors[triggeredActorIndex].actorId,
                    damage,
                    trap.spellId,
                    true,
                    beforeHp > 0 && m_mapActors[triggeredActorIndex].currentHp <= 0);
            }
        }
        else
        {
            applyMonsterAttackToMapActor(triggeredActorIndex, damage, trap.sourceId);
        }
    }

    if (result.spawnImpactVisual)
    {
        GameplayProjectileService::FireSpikeTrapImpactProjectileInput impactInput = {};
        impactInput.sourceKind = trap.sourceKind;
        impactInput.sourceId = trap.sourceId;
        impactInput.sourcePartyMemberIndex = trap.sourcePartyMemberIndex;
        impactInput.sourceMonsterId = trap.sourceMonsterId;
        impactInput.fromSummonedMonster = trap.fromSummonedMonster;
        impactInput.ability = trap.ability;
        impactInput.objectDescriptionId = trap.objectDescriptionId;
        impactInput.objectSpriteId = trap.objectSpriteId;
        impactInput.objectSpriteFrameIndex = trap.objectSpriteFrameIndex;
        impactInput.impactObjectDescriptionId = trap.impactObjectDescriptionId;
        impactInput.objectFlags = trap.objectFlags;
        impactInput.radius = trap.radius;
        impactInput.height = trap.height;
        impactInput.spellId = trap.spellId;
        impactInput.effectSoundId = trap.effectSoundId;
        impactInput.skillLevel = trap.skillLevel;
        impactInput.skillMastery = trap.skillMastery;
        impactInput.objectName = trap.objectName;
        impactInput.objectSpriteName = trap.objectSpriteName;
        impactInput.x = trap.x;
        impactInput.y = trap.y;
        impactInput.z = trap.z;
        impactInput.damage = result.damage;

        const ProjectileState impactSource = projectileService().buildFireSpikeTrapImpactProjectile(impactInput);
        spawnProjectileImpact(impactSource, trap.x, trap.y, trap.z);
    }

    if (result.expireTrap)
    {
        trap.isExpired = true;
    }
}

bool OutdoorWorldRuntime::isInitialized() const
{
    return m_mapId != 0 || !m_mapName.empty() || m_eventRuntimeState.has_value();
}

void OutdoorWorldRuntime::bindInteractionView(OutdoorGameView *pView)
{
    m_pInteractionView = pView;
}

void OutdoorWorldRuntime::updateWorldMovement(
    const GameplayInputFrame &input,
    float deltaSeconds,
    bool allowWorldInput)
{
    (void)allowWorldInput;

    if (m_pInteractionView == nullptr)
    {
        return;
    }

    OutdoorGameplayInputController::updateCameraFromInput(*m_pInteractionView, input, deltaSeconds);
}

void OutdoorWorldRuntime::updateActorAi(float deltaSeconds)
{
    (void)deltaSeconds;

    if (!m_actorAiUpdateQueued)
    {
        return;
    }

    const float queuedDeltaSeconds = m_queuedActorAiDeltaSeconds;
    const float partyX = m_queuedActorAiPartyX;
    const float partyY = m_queuedActorAiPartyY;
    const float partyZ = m_queuedActorAiPartyZ;

    m_actorAiUpdateQueued = false;
    m_queuedActorAiDeltaSeconds = 0.0f;
    m_queuedActorAiPartyX = 0.0f;
    m_queuedActorAiPartyY = 0.0f;
    m_queuedActorAiPartyZ = 0.0f;

    updateMapActors(queuedDeltaSeconds, partyX, partyY, partyZ);
}

void OutdoorWorldRuntime::updateWorld(float deltaSeconds)
{
    (void)deltaSeconds;

    if (m_pOutdoorMapDeltaData != nullptr && m_pPartyRuntime != nullptr)
    {
        updateOutdoorJournalRevealMask(*m_pPartyRuntime, *const_cast<MapDeltaData *>(m_pOutdoorMapDeltaData));
    }
}

void OutdoorWorldRuntime::renderWorld(
    int width,
    int height,
    const GameplayInputFrame &input,
    float deltaSeconds)
{
    if (m_pInteractionView != nullptr)
    {
        m_pInteractionView->render(width, height, input, deltaSeconds);
    }
}

GameplayWorldUiRenderState OutdoorWorldRuntime::gameplayUiRenderState(int width, int height) const
{
    if (m_pInteractionView == nullptr)
    {
        return GameplayWorldUiRenderState{.renderGameplayHud = false};
    }

    return m_pInteractionView->gameplayUiRenderState(width, height);
}

bool OutdoorWorldRuntime::requestTravelAutosave()
{
    return m_pInteractionView != nullptr
        && OutdoorInteractionController::requestTravelAutosave(*m_pInteractionView);
}

void OutdoorWorldRuntime::presentPendingEventDialog(size_t previousMessageCount, bool allowNpcFallbackContent)
{
    if (m_pInteractionView != nullptr)
    {
        OutdoorInteractionController::presentPendingEventDialog(
            *m_pInteractionView,
            previousMessageCount,
            allowNpcFallbackContent);
    }
}

void OutdoorWorldRuntime::handleDialogueCloseRequest()
{
    if (m_pInteractionView != nullptr)
    {
        OutdoorInteractionController::handleDialogueCloseRequest(*m_pInteractionView);
    }
}

void OutdoorWorldRuntime::executeActiveDialogAction()
{
    if (m_pInteractionView != nullptr)
    {
        OutdoorInteractionController::executeActiveDialogAction(*m_pInteractionView);
    }
}

void OutdoorWorldRuntime::openDebugNpcDialogue(uint32_t npcId)
{
    if (m_pInteractionView != nullptr)
    {
        OutdoorInteractionController::openDebugNpcDialogue(*m_pInteractionView, npcId);
    }
}

void OutdoorWorldRuntime::applyGrantedEventItemsToHeldInventory()
{
    if (m_pInteractionView != nullptr)
    {
        OutdoorInteractionController::applyGrantedEventItemsToHeldInventory(*m_pInteractionView);
    }
}

bool OutdoorWorldRuntime::tryTriggerLocalEventById(uint16_t eventId)
{
    if (m_pInteractionView == nullptr)
    {
        return false;
    }

    return OutdoorInteractionController::tryTriggerLocalEventById(*m_pInteractionView, eventId);
}

int OutdoorWorldRuntime::mapId() const
{
    return m_mapId;
}

const std::string &OutdoorWorldRuntime::mapName() const
{
    return m_mapName;
}

const std::vector<uint8_t> *OutdoorWorldRuntime::journalMapFullyRevealedCells() const
{
    return m_pOutdoorMapDeltaData != nullptr ? &m_pOutdoorMapDeltaData->fullyRevealedCells : nullptr;
}

const std::vector<uint8_t> *OutdoorWorldRuntime::journalMapPartiallyRevealedCells() const
{
    return m_pOutdoorMapDeltaData != nullptr ? &m_pOutdoorMapDeltaData->partiallyRevealedCells : nullptr;
}

int OutdoorWorldRuntime::restFoodRequired() const
{
    int foodRequired = 2;

    if (m_pPartyRuntime != nullptr)
    {
        const OutdoorMoveState &moveState = m_pPartyRuntime->movementState();

        if (moveState.supportKind == OutdoorSupportKind::Terrain
            && !moveState.airborne
            && !moveState.supportOnWater
            && m_pOutdoorMapData != nullptr)
        {
            const std::string tilesetName = toLowerCopy(m_pOutdoorMapData->groundTilesetName);

            if (tilesetName.find("grass") != std::string::npos || tilesetName.find("gras") != std::string::npos)
            {
                foodRequired = 1;
            }
            else if (tilesetName.find("desert") != std::string::npos
                     || tilesetName.find("dsrt") != std::string::npos
                     || tilesetName.find("sand") != std::string::npos)
            {
                foodRequired = 5;
            }
            else if (tilesetName.find("snow") != std::string::npos
                     || tilesetName.find("snw") != std::string::npos
                     || tilesetName.find("ice") != std::string::npos
                     || tilesetName.find("swamp") != std::string::npos
                     || tilesetName.find("swmp") != std::string::npos)
            {
                foodRequired = 3;
            }
            else if (tilesetName.find("badland") != std::string::npos || tilesetName.find("bad") != std::string::npos)
            {
                foodRequired = 4;
            }
        }

        const Party &partyState = m_pPartyRuntime->party();

        for (const Character &member : partyState.members())
        {
            constexpr uint32_t DragonRaceId = 5;

            if (member.raceId == DragonRaceId)
            {
                ++foodRequired;
                break;
            }
        }
    }

    return std::max(1, foodRequired);
}

OutdoorWorldRuntime::Snapshot OutdoorWorldRuntime::snapshot() const
{
    Snapshot snapshot = {};
    const GameplayProjectileService::Snapshot projectileSnapshot = projectileService().snapshot();
    snapshot.gameMinutes = m_gameMinutes;
    snapshot.atmosphere = m_atmosphereState;
    snapshot.timers = m_timers;
    snapshot.mapActors = m_mapActors;
    snapshot.chests = m_chests;
    snapshot.materializedChestViews = m_materializedChestViews;
    snapshot.activeChestView = m_activeChestView;
    snapshot.eventRuntimeState = m_eventRuntimeState;
    snapshot.actorUpdateAccumulatorSeconds = m_actorUpdateAccumulatorSeconds;
    snapshot.sessionChestSeed = m_sessionChestSeed;
    snapshot.nextActorId = m_nextActorId;
    snapshot.mapActorCorpseViews = m_mapActorCorpseViews;
    snapshot.activeCorpseView = m_activeCorpseView;
    snapshot.worldItems = m_worldItems;
    snapshot.nextWorldItemId = m_nextWorldItemId;
    snapshot.nextProjectileId = projectileSnapshot.nextProjectileId;
    snapshot.nextProjectileImpactId = projectileSnapshot.nextProjectileImpactId;
    snapshot.nextFireSpikeTrapId = projectileSnapshot.nextFireSpikeTrapId;
    snapshot.gameplayOverlayRemainingSeconds = m_gameplayOverlayRemainingSeconds;
    snapshot.gameplayOverlayDurationSeconds = m_gameplayOverlayDurationSeconds;
    snapshot.gameplayOverlayPeakAlpha = m_gameplayOverlayPeakAlpha;
    snapshot.gameplayOverlayColorAbgr = m_gameplayOverlayColorAbgr;
    snapshot.projectiles = projectileSnapshot.projectiles;
    snapshot.projectileImpacts = projectileSnapshot.projectileImpacts;
    snapshot.fireSpikeTraps = m_fireSpikeTraps;
    snapshot.armageddon = m_armageddonState;
    snapshot.hasRainIntensityOverride = m_hasRainIntensityOverride;
    snapshot.rainIntensityPreset = m_rainIntensityPreset;
    snapshot.openedChestFlags.reserve(m_openedChests.size());

    for (bool opened : m_openedChests)
    {
        snapshot.openedChestFlags.push_back(opened ? 1u : 0u);
    }

    return snapshot;
}

void OutdoorWorldRuntime::restoreSnapshot(const Snapshot &snapshot)
{
    GameplayProjectileService::Snapshot projectileSnapshot = {};
    projectileSnapshot.nextProjectileId = snapshot.nextProjectileId;
    projectileSnapshot.nextProjectileImpactId = snapshot.nextProjectileImpactId;
    projectileSnapshot.nextFireSpikeTrapId = snapshot.nextFireSpikeTrapId;
    projectileSnapshot.projectiles = snapshot.projectiles;
    projectileSnapshot.projectileImpacts = snapshot.projectileImpacts;

    m_gameMinutes = snapshot.gameMinutes;
    m_atmosphereState = snapshot.atmosphere;
    m_timers = snapshot.timers;
    m_mapActors = snapshot.mapActors;
    m_chests = snapshot.chests;
    m_materializedChestViews = snapshot.materializedChestViews;
    m_activeChestView = snapshot.activeChestView;
    m_eventRuntimeState = snapshot.eventRuntimeState;
    m_actorUpdateAccumulatorSeconds = snapshot.actorUpdateAccumulatorSeconds;
    m_sessionChestSeed = snapshot.sessionChestSeed;
    m_nextActorId = snapshot.nextActorId;
    m_mapActorCorpseViews = snapshot.mapActorCorpseViews;
    m_activeCorpseView = snapshot.activeCorpseView;
    m_worldItems = snapshot.worldItems;
    m_nextWorldItemId = snapshot.nextWorldItemId;
    projectileService().restoreSnapshot(projectileSnapshot);
    m_gameplayOverlayRemainingSeconds = snapshot.gameplayOverlayRemainingSeconds;
    m_gameplayOverlayDurationSeconds = snapshot.gameplayOverlayDurationSeconds;
    m_gameplayOverlayPeakAlpha = snapshot.gameplayOverlayPeakAlpha;
    m_gameplayOverlayColorAbgr = snapshot.gameplayOverlayColorAbgr;
    m_fireSpikeTraps = snapshot.fireSpikeTraps;
    m_armageddonState = snapshot.armageddon;
    m_hasRainIntensityOverride = snapshot.hasRainIntensityOverride;
    m_rainIntensityPreset = snapshot.rainIntensityPreset;
    m_openedChests.clear();
    m_openedChests.reserve(snapshot.openedChestFlags.size());

    for (uint8_t opened : snapshot.openedChestFlags)
    {
        m_openedChests.push_back(opened != 0);
    }

    m_pendingAudioEvents.clear();
    clearPendingCombatEvents();
    refreshAtmosphereState();
    applyEventRuntimeState();
}

float OutdoorWorldRuntime::gameMinutes() const
{
    return m_gameMinutes;
}

float OutdoorWorldRuntime::currentGameMinutes() const
{
    return gameMinutes();
}

const OutdoorMapData *OutdoorWorldRuntime::mapData() const
{
    return m_pOutdoorMapData;
}

int OutdoorWorldRuntime::currentHour() const
{
    int currentHour = static_cast<int>(m_gameMinutes / 60.0f) % 24;

    if (currentHour < 0)
    {
        currentHour += 24;
    }

    return currentHour;
}

int OutdoorWorldRuntime::currentLocationReputation() const
{
    if (m_pOutdoorMapDeltaData == nullptr)
    {
        return 0;
    }

    return m_pOutdoorMapDeltaData->locationInfo.reputation;
}

void OutdoorWorldRuntime::setCurrentLocationReputation(int reputation)
{
    if (m_pOutdoorMapDeltaData == nullptr)
    {
        return;
    }

    MapDeltaData *pMutableMapDeltaData = const_cast<MapDeltaData *>(m_pOutdoorMapDeltaData);
    pMutableMapDeltaData->locationInfo.reputation = reputation;
}

const OutdoorWorldRuntime::AtmosphereState &OutdoorWorldRuntime::atmosphereState() const
{
    return m_atmosphereState;
}

OutdoorWorldRuntime::RainIntensityPreset OutdoorWorldRuntime::cycleRainIntensityPreset()
{
    m_hasRainIntensityOverride = true;

    switch (m_rainIntensityPreset)
    {
        case RainIntensityPreset::Off:
            m_rainIntensityPreset = RainIntensityPreset::Light;
            break;
        case RainIntensityPreset::Light:
            m_rainIntensityPreset = RainIntensityPreset::Medium;
            break;
        case RainIntensityPreset::Medium:
            m_rainIntensityPreset = RainIntensityPreset::Heavy;
            break;
        case RainIntensityPreset::Heavy:
            m_rainIntensityPreset = RainIntensityPreset::VeryHeavy;
            break;
        case RainIntensityPreset::VeryHeavy:
        default:
            m_rainIntensityPreset = RainIntensityPreset::Off;
            break;
    }

    refreshAtmosphereState();
    return m_rainIntensityPreset;
}

OutdoorWorldRuntime::RainIntensityPreset OutdoorWorldRuntime::rainIntensityPreset() const
{
    return m_rainIntensityPreset;
}

const char *OutdoorWorldRuntime::rainIntensityPresetName() const
{
    return ::OpenYAMM::Game::rainIntensityPresetName(m_rainIntensityPreset);
}

void OutdoorWorldRuntime::advanceGameMinutes(float minutes)
{
    if (minutes <= 0.0f)
    {
        return;
    }

    advanceGameMinutesInternal(minutes);
    refreshAtmosphereState();
}

void OutdoorWorldRuntime::advanceGameMinutesInternal(float minutes)
{
    if (minutes <= 0.0f)
    {
        return;
    }

    const int previousWeatherDay = weatherDayIndexForMinutes(m_gameMinutes);
    m_gameMinutes += minutes;
    const int currentWeatherDay = weatherDayIndexForMinutes(m_gameMinutes);

    if (currentWeatherDay > previousWeatherDay)
    {
        resetDailySpellCounters();
        applyDailyWeatherRollover(currentWeatherDay);
    }
}

void OutdoorWorldRuntime::applyInitialWeatherProfile()
{
    if (!m_outdoorWeatherProfile.has_value())
    {
        return;
    }

    const OutdoorWeatherProfile &profile = *m_outdoorWeatherProfile;

    if (profile.defaultPrecipitation == OutdoorPrecipitationKind::Snow)
    {
        m_atmosphereState.weatherFlags &= ~MapWeatherRaining;
        m_atmosphereState.weatherFlags |= MapWeatherSnowing;
    }
    else if (profile.defaultPrecipitation == OutdoorPrecipitationKind::Rain)
    {
        m_atmosphereState.weatherFlags &= ~MapWeatherSnowing;
        m_atmosphereState.weatherFlags |= MapWeatherRaining;
    }
    else
    {
        m_atmosphereState.weatherFlags &= ~(MapWeatherSnowing | MapWeatherRaining);
    }

    m_atmosphereState.redFog = profile.redFog;
    m_atmosphereState.hasFogTint = profile.hasFogTint;
    m_atmosphereState.fogTintRed = profile.fogTintRgb[0];
    m_atmosphereState.fogTintGreen = profile.fogTintRgb[1];
    m_atmosphereState.fogTintBlue = profile.fogTintRgb[2];

    if (profile.fogMode == OutdoorFogMode::DailyRandom)
    {
        if (!hasConfiguredFogState(m_atmosphereState))
        {
            applyDailyWeatherRollover(weatherDayIndexForMinutes(m_gameMinutes));
            return;
        }
    }
    else if (profile.alwaysFoggy)
    {
        const OutdoorFogDistances distances = fallbackFogDistancesForProfile(profile);
        applyFogDistances(distances, true);
        return;
    }

    syncAtmosphereStateToMapDelta();
}

void OutdoorWorldRuntime::applyDailyWeatherRollover(int weatherDayIndex)
{
    if (!m_outdoorWeatherProfile.has_value())
    {
        return;
    }

    const OutdoorWeatherProfile &profile = *m_outdoorWeatherProfile;

    if (profile.fogMode != OutdoorFogMode::DailyRandom)
    {
        return;
    }

    const int clampedWeatherDayIndex = std::max(weatherDayIndex, 0);
    uint32_t seed = 0x9e3779b9u;
    seed ^= static_cast<uint32_t>(m_mapId) * 2246822519u;
    seed ^= static_cast<uint32_t>(clampedWeatherDayIndex) * 3266489917u;
    std::mt19937 rng(seed);
    const int roll = std::uniform_int_distribution<int>(0, 99)(rng);
    const int smallThreshold = std::max(profile.smallFogChance, 0);
    const int averageThreshold = smallThreshold + std::max(profile.averageFogChance, 0);
    const int denseThreshold = averageThreshold + std::max(profile.denseFogChance, 0);

    if (roll < smallThreshold)
    {
        applyFogDistances(profile.smallFog, true);
        return;
    }

    if (roll < averageThreshold)
    {
        applyFogDistances(profile.averageFog, true);
        return;
    }

    if (roll < denseThreshold)
    {
        applyFogDistances(profile.denseFog, true);
        return;
    }

    if (profile.alwaysFoggy)
    {
        applyFogDistances(fallbackFogDistancesForProfile(profile), true);
        return;
    }

    applyFogDistances({}, false);
}

void OutdoorWorldRuntime::applyFogDistances(const OutdoorFogDistances &distances, bool foggy)
{
    if (foggy)
    {
        m_atmosphereState.weatherFlags |= MapWeatherFoggy;
        m_atmosphereState.fogWeakDistance = std::max(distances.weakDistance, 0);
        m_atmosphereState.fogStrongDistance = std::max(distances.strongDistance, 0);
    }
    else
    {
        m_atmosphereState.weatherFlags &= ~MapWeatherFoggy;
        m_atmosphereState.fogWeakDistance = 0;
        m_atmosphereState.fogStrongDistance = 0;
    }

    syncAtmosphereStateToMapDelta();
}

void OutdoorWorldRuntime::syncAtmosphereStateToMapDelta()
{
    if (m_pOutdoorMapDeltaData == nullptr)
    {
        return;
    }

    MapDeltaData *pMutableMapDeltaData = const_cast<MapDeltaData *>(m_pOutdoorMapDeltaData);
    pMutableMapDeltaData->locationTime.weatherFlags = m_atmosphereState.weatherFlags;
    pMutableMapDeltaData->locationTime.fogWeakDistance = m_atmosphereState.fogWeakDistance;
    pMutableMapDeltaData->locationTime.fogStrongDistance = m_atmosphereState.fogStrongDistance;
}

int OutdoorWorldRuntime::weatherDayIndexForMinutes(float gameMinutes) const
{
    const float safeGameMinutes = std::max(gameMinutes, 0.0f);
    const float shiftedMinutes = safeGameMinutes - 180.0f;
    return static_cast<int>(std::floor(shiftedMinutes / 1440.0f));
}

void OutdoorWorldRuntime::resetDailySpellCounters()
{
    if (m_pParty == nullptr)
    {
        return;
    }

    for (size_t memberIndex = 0; memberIndex < m_pParty->members().size(); ++memberIndex)
    {
        Character *pMember = m_pParty->member(memberIndex);

        if (pMember != nullptr)
        {
            pMember->armageddonCastsToday = 0;
        }
    }
}

void OutdoorWorldRuntime::refreshAtmosphereState()
{
    if (m_outdoorWeatherProfile.has_value())
    {
        m_atmosphereState.redFog = m_outdoorWeatherProfile->redFog;
        m_atmosphereState.hasFogTint = m_outdoorWeatherProfile->hasFogTint;
        m_atmosphereState.fogTintRed = m_outdoorWeatherProfile->fogTintRgb[0];
        m_atmosphereState.fogTintGreen = m_outdoorWeatherProfile->fogTintRgb[1];
        m_atmosphereState.fogTintBlue = m_outdoorWeatherProfile->fogTintRgb[2];
    }

    if (m_eventRuntimeState && m_eventRuntimeState->snowEnabled.has_value())
    {
        if (*m_eventRuntimeState->snowEnabled)
        {
            m_atmosphereState.weatherFlags &= ~MapWeatherRaining;
            m_atmosphereState.weatherFlags |= MapWeatherSnowing;
        }
        else
        {
            m_atmosphereState.weatherFlags &= ~MapWeatherSnowing;
        }
    }

    if (m_eventRuntimeState && m_eventRuntimeState->rainEnabled.has_value())
    {
        if (*m_eventRuntimeState->rainEnabled)
        {
            m_atmosphereState.weatherFlags &= ~MapWeatherSnowing;
            m_atmosphereState.weatherFlags |= MapWeatherRaining;
        }
        else
        {
            m_atmosphereState.weatherFlags &= ~MapWeatherRaining;
        }
    }

    m_atmosphereState.rainIntensity = (m_atmosphereState.weatherFlags & MapWeatherRaining) != 0 ? 1.0f : 0.0f;

    if (m_hasRainIntensityOverride)
    {
        if (m_rainIntensityPreset != RainIntensityPreset::Off)
        {
            m_atmosphereState.weatherFlags &= ~MapWeatherSnowing;
            m_atmosphereState.weatherFlags |= MapWeatherRaining;
            m_atmosphereState.rainIntensity = rainIntensityValue(m_rainIntensityPreset);
        }
        else
        {
            m_atmosphereState.weatherFlags &= ~MapWeatherRaining;
            m_atmosphereState.rainIntensity = 0.0f;
        }
    }

    const float minutesOfDay = std::fmod(std::max(m_gameMinutes, 0.0f), 1440.0f);

    if (minutesOfDay < 300.0f || minutesOfDay >= 1260.0f)
    {
        m_atmosphereState.isNight = true;
        m_atmosphereState.fogDensity = 1.0f;
    }
    else if (minutesOfDay < 360.0f)
    {
        m_atmosphereState.isNight = false;
        m_atmosphereState.fogDensity = (360.0f - minutesOfDay) / 60.0f;
    }
    else if (minutesOfDay < 1200.0f)
    {
        m_atmosphereState.isNight = false;
        m_atmosphereState.fogDensity = 0.0f;
    }
    else if (minutesOfDay < 1260.0f)
    {
        m_atmosphereState.isNight = false;
        m_atmosphereState.fogDensity = (minutesOfDay - 1200.0f) / 60.0f;
    }
    else
    {
        m_atmosphereState.isNight = true;
        m_atmosphereState.fogDensity = 1.0f;
    }

    m_atmosphereState.skyTextureName =
        resolveRenderedSkyTextureName(m_atmosphereState.sourceSkyTextureName, minutesOfDay);

    if (m_mapId == DwiMapId)
    {
        m_atmosphereState.skyTextureName = "sunsetclouds";
    }

    m_atmosphereState.ambientBrightness = normalizedAmbientBrightness(minutesOfDay);
    const float normalizedBrightness = std::clamp(
        (m_atmosphereState.ambientBrightness - 0.15f) / (0.69f - 0.15f),
        0.0f,
        1.0f);
    m_atmosphereState.darknessOverlayAlpha = (1.0f - normalizedBrightness) * 0.55f;

    if (m_atmosphereState.isNight)
    {
        m_atmosphereState.darknessOverlayColorAbgr = makeAbgr(16, 24, 52);
    }
    else
    {
        const float twilightFactor = std::clamp(m_atmosphereState.fogDensity, 0.0f, 1.0f);
        const uint8_t red = static_cast<uint8_t>(std::clamp(std::lround(92.0f * twilightFactor), 0l, 255l));
        const uint8_t green = static_cast<uint8_t>(std::clamp(std::lround(36.0f * twilightFactor), 0l, 255l));
        const uint8_t blue = static_cast<uint8_t>(std::clamp(std::lround(30.0f * twilightFactor), 0l, 255l));
        m_atmosphereState.darknessOverlayColorAbgr = makeAbgr(red, green, blue);
    }

    m_atmosphereState.gameplayOverlayAlpha = 0.0f;
    m_atmosphereState.gameplayOverlayColorAbgr = m_gameplayOverlayColorAbgr;

    if (minutesOfDay >= 300.0f && minutesOfDay < 1260.0f)
    {
        const float daylightMinutes = minutesOfDay - 300.0f;
        const float sunlightRadians = (daylightMinutes * Pi) / 960.0f;
        m_atmosphereState.sunDirectionX = std::cos(sunlightRadians);
        m_atmosphereState.sunDirectionY = 0.0f;
        m_atmosphereState.sunDirectionZ = std::sin(sunlightRadians);
    }
    else
    {
        m_atmosphereState.sunDirectionX = 0.0f;
        m_atmosphereState.sunDirectionY = 0.0f;
        m_atmosphereState.sunDirectionZ = 1.0f;
    }

    m_atmosphereState.visibilityDistance = DefaultOutdoorVisibilityDistance;

    if (m_atmosphereState.fogStrongDistance > 0 && (m_atmosphereState.weatherFlags & MapWeatherFoggy) != 0)
    {
        m_atmosphereState.visibilityDistance =
            std::min(m_atmosphereState.visibilityDistance, static_cast<float>(m_atmosphereState.fogStrongDistance) * 2.0f);
    }

    if (m_atmosphereState.fogDensity > 0.0f)
    {
        const float dayNightVisibility =
            DefaultOutdoorVisibilityDistance
            - (DefaultOutdoorVisibilityDistance - 24576.0f) * std::min(m_atmosphereState.fogDensity, 1.0f);
        m_atmosphereState.visibilityDistance = std::min(m_atmosphereState.visibilityDistance, dayNightVisibility);
    }

    m_atmosphereState.visibilityDistance = std::max(m_atmosphereState.visibilityDistance, 4096.0f);

    if ((m_atmosphereState.weatherFlags & MapWeatherFoggy) != 0)
    {
        if (m_atmosphereState.isNight)
        {
            if (m_atmosphereState.hasFogTint)
            {
                m_atmosphereState.clearColorAbgr = makeTintedFogColor(
                    48,
                    true,
                    m_atmosphereState.fogTintRed,
                    m_atmosphereState.fogTintGreen,
                    m_atmosphereState.fogTintBlue);
            }
            else if (m_atmosphereState.redFog)
            {
                m_atmosphereState.clearColorAbgr = makeAbgr(64, 24, 24);
            }
            else
            {
                m_atmosphereState.clearColorAbgr = makeAbgr(48, 48, 56);
            }
        }
        else
        {
            const uint8_t fogLevel = static_cast<uint8_t>(std::clamp(
                std::lround((1.0f - m_atmosphereState.fogDensity) * 200.0f + m_atmosphereState.fogDensity * 31.0f),
                0l,
                255l));

            if (m_atmosphereState.hasFogTint)
            {
                m_atmosphereState.clearColorAbgr = makeTintedFogColor(
                    fogLevel,
                    true,
                    m_atmosphereState.fogTintRed,
                    m_atmosphereState.fogTintGreen,
                    m_atmosphereState.fogTintBlue);
            }
            else if (m_atmosphereState.redFog)
            {
                const uint8_t green = static_cast<uint8_t>(std::lround(static_cast<float>(fogLevel) * 0.35f));
                const uint8_t blue = static_cast<uint8_t>(std::lround(static_cast<float>(fogLevel) * 0.35f));
                m_atmosphereState.clearColorAbgr = makeAbgr(fogLevel, green, blue);
            }
            else
            {
                m_atmosphereState.clearColorAbgr = makeAbgr(fogLevel, fogLevel, fogLevel);
            }
        }
    }
    else if (m_atmosphereState.isNight)
    {
        m_atmosphereState.clearColorAbgr = makeAbgr(8, 16, 32);
    }
    else
    {
        const float skyBias = std::clamp(normalizedBrightness, 0.0f, 1.0f);
        const float twilightFactor = std::clamp(m_atmosphereState.fogDensity, 0.0f, 1.0f);
        const float dayRed = 24.0f + skyBias * 76.0f;
        const float dayGreen = 48.0f + skyBias * 96.0f;
        const float dayBlue = 84.0f + skyBias * 132.0f;
        const uint8_t red = static_cast<uint8_t>(std::clamp(
            std::lround(dayRed * (1.0f - twilightFactor) + 112.0f * twilightFactor),
            0l,
            255l));
        const uint8_t green = static_cast<uint8_t>(std::clamp(
            std::lround(dayGreen * (1.0f - twilightFactor) + 60.0f * twilightFactor),
            0l,
            255l));
        const uint8_t blue = static_cast<uint8_t>(std::clamp(
            std::lround(dayBlue * (1.0f - twilightFactor) + 72.0f * twilightFactor),
            0l,
            255l));
        m_atmosphereState.clearColorAbgr = makeAbgr(red, green, blue);
    }
}

void OutdoorWorldRuntime::updateGameplayScreenOverlay(float deltaSeconds)
{
    float overlayAlpha = 0.0f;
    uint32_t overlayColor = m_gameplayOverlayColorAbgr;

    if (m_gameplayOverlayRemainingSeconds > 0.0f && m_gameplayOverlayDurationSeconds > 0.0f)
    {
        m_gameplayOverlayRemainingSeconds = std::max(0.0f, m_gameplayOverlayRemainingSeconds - deltaSeconds);
        const float elapsedSeconds = m_gameplayOverlayDurationSeconds - m_gameplayOverlayRemainingSeconds;
        const float normalizedTime =
            std::clamp(elapsedSeconds / m_gameplayOverlayDurationSeconds, 0.0f, 1.0f);
        overlayAlpha = std::sin(normalizedTime * Pi) * m_gameplayOverlayPeakAlpha;
    }

    if (m_armageddonState.active())
    {
        const float armageddonPulse = 0.55f + 0.45f * std::sin(m_armageddonState.remainingSeconds * 12.0f);
        const float armageddonAlpha = 0.24f + 0.14f * armageddonPulse;

        if (armageddonAlpha >= overlayAlpha)
        {
            overlayAlpha = armageddonAlpha;
            overlayColor = makeAbgr(196, 18, 12);
        }
    }

    m_atmosphereState.gameplayOverlayAlpha = overlayAlpha;
    m_atmosphereState.gameplayOverlayColorAbgr = overlayColor;
}

void OutdoorWorldRuntime::updateActorFrameGlobalEffects(
    float deltaSeconds,
    float partyX,
    float partyY,
    float partyZ)
{
    updateGameplayScreenOverlay(deltaSeconds);
    updateArmageddon(deltaSeconds, partyX, partyY, partyZ);
    m_actorUpdateAccumulatorSeconds =
        std::min(m_actorUpdateAccumulatorSeconds + deltaSeconds, MaxAccumulatedActorUpdateSeconds);
}

std::vector<bool> OutdoorWorldRuntime::selectOutdoorActiveActors(float partyX, float partyY, float partyZ) const
{
    std::vector<OutdoorActiveActorCandidate> activeActorCandidates;
    activeActorCandidates.reserve(m_mapActors.size());

    for (size_t actorIndex = 0; actorIndex < m_mapActors.size(); ++actorIndex)
    {
        const MapActorState &actor = m_mapActors[actorIndex];
        OutdoorActiveActorCandidate candidate = {};
        candidate.actorIndex = actorIndex;
        candidate.eligible = !actor.isDead && !actor.isInvisible;

        if (candidate.eligible)
        {
            const float deltaX = partyX - actor.preciseX;
            const float deltaY = partyY - actor.preciseY;
            const float deltaZ = partyZ - actor.preciseZ;
            candidate.distanceToParty = std::sqrt(deltaX * deltaX + deltaY * deltaY + deltaZ * deltaZ)
                - static_cast<float>(actor.radius);

            if (candidate.distanceToParty < 0.0f)
            {
                candidate.distanceToParty = 0.0f;
            }
        }

        activeActorCandidates.push_back(candidate);
    }

    return selectOutdoorActiveActorMask(
        activeActorCandidates,
        m_mapActors.size(),
        MaxActiveActorUpdates,
        ActiveActorUpdateRange);
}

ActorAiFrameFacts OutdoorWorldRuntime::collectOutdoorActorAiFrameFacts(
    float deltaSeconds,
    float partyX,
    float partyY,
    float partyZ,
    const std::vector<bool> &activeActorMask) const
{
    ActorAiFrameFacts facts = {};
    facts.deltaSeconds = deltaSeconds;
    facts.fixedStepSeconds = ActorUpdateStepSeconds;
    facts.party.position = GameplayWorldPoint{partyX, partyY, partyZ};
    facts.party.collisionRadius = PartyCollisionRadius;
    facts.party.collisionHeight = PartyCollisionHeight;
    facts.party.invisible = false;

    std::vector<int8_t> actorLineOfSightCache(m_mapActors.size() * m_mapActors.size(), -1);

    for (size_t actorIndex = 0; actorIndex < m_mapActors.size(); ++actorIndex)
    {
        const bool active = actorIndex < activeActorMask.size() && activeActorMask[actorIndex];
        const std::optional<ActorAiFacts> actorFacts =
            collectOutdoorActorAiFacts(actorIndex, active, partyX, partyY, partyZ, actorLineOfSightCache);

        if (!actorFacts)
        {
            continue;
        }

        if (active)
        {
            facts.activeActors.push_back(*actorFacts);
        }
        else
        {
            facts.backgroundActors.push_back(*actorFacts);
        }
    }

    return facts;
}

std::optional<ActorAiFacts> OutdoorWorldRuntime::collectOutdoorActorAiFacts(
    size_t actorIndex,
    bool active,
    float partyX,
    float partyY,
    float partyZ,
    std::vector<int8_t> &actorLineOfSightCache) const
{
    if (actorIndex >= m_mapActors.size() || m_pMonsterTable == nullptr)
    {
        return std::nullopt;
    }

    const MapActorState &actor = m_mapActors[actorIndex];
    const MonsterTable::MonsterStatsEntry *pStats = m_pMonsterTable->findStatsById(actor.monsterId);

    if (pStats == nullptr)
    {
        return std::nullopt;
    }

    const size_t mapActorCount = m_mapActors.size();
    const auto hasClearOutdoorLineOfSight =
        [this, mapActorCount, &actorLineOfSightCache](
        size_t startActorIndex,
        size_t endActorIndex,
        const bx::Vec3 &start,
        const bx::Vec3 &end) -> bool
    {
        if (startActorIndex >= mapActorCount || endActorIndex >= mapActorCount)
        {
            return this->hasClearOutdoorLineOfSight(start, end);
        }

        const size_t firstActorIndex = std::min(startActorIndex, endActorIndex);
        const size_t secondActorIndex = std::max(startActorIndex, endActorIndex);
        const size_t cacheIndex = firstActorIndex * mapActorCount + secondActorIndex;

        if (cacheIndex >= actorLineOfSightCache.size())
        {
            return this->hasClearOutdoorLineOfSight(start, end);
        }

        int8_t &cachedResult = actorLineOfSightCache[cacheIndex];

        if (cachedResult >= 0)
        {
            return cachedResult != 0;
        }

        const bool hasLineOfSight = this->hasClearOutdoorLineOfSight(start, end);
        cachedResult = hasLineOfSight ? 1 : 0;
        return hasLineOfSight;
    };

    std::vector<OutdoorCombatTargetCandidate> combatCandidates;
    OutdoorTargetFacts combatTarget = {};

    if (active)
    {
        combatCandidates =
            buildCombatTargetCandidates(
                m_pGameplayActorService,
                actor,
                actorIndex,
                m_mapActors);
        combatTarget =
            resolveOutdoorTargetFacts(
                m_pGameplayActorService,
                actor,
                actorIndex,
                combatCandidates,
                partyX,
                partyY,
                partyZ,
                hasClearOutdoorLineOfSight);
    }

    ActorAiFacts facts = {};
    facts.actorIndex = actorIndex;
    facts.actorId = actor.actorId;

    facts.identity.actorId = actor.actorId;
    facts.identity.monsterId = actor.monsterId;
    facts.identity.displayName = actor.displayName;
    facts.identity.group = actor.group;
    facts.identity.ally = actor.ally;
    facts.identity.hostilityType = actor.hostilityType;
    facts.identity.targetPolicy = buildGameplayActorTargetPolicyState(actor);

    facts.stats.aiType = gameplayActorAiTypeFromMonster(pStats->aiType);
    facts.stats.monsterLevel = pStats->level;
    facts.stats.currentHp = actor.currentHp;
    facts.stats.maxHp = actor.maxHp;
    facts.stats.armorClass = effectiveMapActorArmorClass(actorIndex);
    facts.stats.radius = actor.radius;
    facts.stats.height = actor.height;
    facts.stats.moveSpeed = actor.moveSpeed > 0 ? actor.moveSpeed : static_cast<uint16_t>(pStats->speed);
    facts.stats.canFly = pStats->canFly;
    facts.stats.hasSpell1 = pStats->hasSpell1;
    facts.stats.hasSpell2 = pStats->hasSpell2;
    facts.stats.spell1UseChance = pStats->spell1UseChance;
    facts.stats.spell2UseChance = pStats->spell2UseChance;
    facts.stats.attack2Chance = pStats->attack2Chance;
    facts.stats.attack1Damage.diceRolls = pStats->attack1Damage.diceRolls;
    facts.stats.attack1Damage.diceSides = pStats->attack1Damage.diceSides;
    facts.stats.attack1Damage.bonus = pStats->attack1Damage.bonus;
    facts.stats.attack2Damage.diceRolls = pStats->attack2Damage.diceRolls;
    facts.stats.attack2Damage.diceSides = pStats->attack2Damage.diceSides;
    facts.stats.attack2Damage.bonus = pStats->attack2Damage.bonus;
    facts.stats.attackConstraints.attack1IsRanged = pStats->attack1HasMissile;
    facts.stats.attackConstraints.attack2IsRanged = pStats->attack2HasMissile;
    facts.stats.attackConstraints.blindActive = actor.blindRemainingSeconds > 0.0f;
    facts.stats.attackConstraints.darkGraspActive = actor.darkGraspRemainingSeconds > 0.0f;
    facts.stats.attackConstraints.rangedCommitAllowed = true;

    facts.runtime.motionState = actorAiMotionStateFromOutdoor(actor.aiState);
    facts.runtime.animationState = actorAiAnimationStateFromOutdoor(actor.animation);
    facts.runtime.queuedAttackAbility = gameplayAttackAbilityFromOutdoor(actor.queuedAttackAbility);
    facts.runtime.animationTimeTicks = actor.animationTimeTicks;
    facts.runtime.recoverySeconds = actor.recoverySeconds;
    facts.runtime.attackAnimationSeconds = actor.attackAnimationSeconds;
    facts.runtime.meleeAttackAnimationSeconds = actorAnimationSeconds(
        m_pActorSpriteFrameTable,
        actor,
        ActorAnimation::AttackMelee,
        actor.attackAnimationSeconds);
    facts.runtime.rangedAttackAnimationSeconds = actorAnimationSeconds(
        m_pActorSpriteFrameTable,
        actor,
        ActorAnimation::AttackRanged,
        actor.attackAnimationSeconds);
    facts.runtime.attackCooldownSeconds = actor.attackCooldownSeconds;
    facts.runtime.idleDecisionSeconds = actor.idleDecisionSeconds;
    facts.runtime.actionSeconds = actor.actionSeconds;
    facts.runtime.crowdSideLockRemainingSeconds = actor.crowdSideLockRemainingSeconds;
    facts.runtime.crowdNoProgressSeconds = actor.crowdNoProgressSeconds;
    facts.runtime.crowdLastEdgeDistance = actor.crowdLastEdgeDistance;
    facts.runtime.crowdRetreatRemainingSeconds = actor.crowdRetreatRemainingSeconds;
    facts.runtime.crowdStandRemainingSeconds = actor.crowdStandRemainingSeconds;
    facts.runtime.crowdProbeEdgeDistance = actor.crowdProbeEdgeDistance;
    facts.runtime.crowdProbeElapsedSeconds = actor.crowdProbeElapsedSeconds;
    facts.runtime.yawRadians = actor.yawRadians;
    facts.runtime.idleDecisionCount = actor.idleDecisionCount;
    facts.runtime.pursueDecisionCount = actor.pursueDecisionCount;
    facts.runtime.attackDecisionCount = actor.attackDecisionCount;
    facts.runtime.crowdEscapeAttempts = actor.crowdEscapeAttempts;
    facts.runtime.crowdSideSign = actor.crowdSideSign;
    facts.runtime.attackImpactTriggered = actor.attackImpactTriggered;

    facts.status.spellEffects = buildGameplayActorSpellEffectState(actor);
    facts.status.invisible = actor.isInvisible;
    facts.status.dead = actor.isDead;
    facts.status.hostileToParty = actor.hostileToParty;
    facts.status.bloodSplatSpawned = actor.bloodSplatSpawned;
    facts.status.hasDetectedParty = actor.hasDetectedParty;
    facts.status.defaultHostileToParty = m_pMonsterTable->isHostileToParty(actor.monsterId);

    facts.target.currentKind = actorAiTargetKindFromOutdoorTarget(combatTarget.kind);
    facts.target.currentActorIndex = combatTarget.actorIndex;
    facts.target.currentRelationToTarget = combatTarget.relationToTarget;
    facts.target.currentPosition = GameplayWorldPoint{combatTarget.targetX, combatTarget.targetY, combatTarget.targetZ};
    facts.target.currentAudioPosition = facts.target.currentPosition;

    if (combatTarget.kind == OutdoorTargetKind::Actor
        && combatTarget.actorIndex < m_mapActors.size())
    {
        const MapActorState &targetActor = m_mapActors[combatTarget.actorIndex];
        facts.target.currentHp = targetActor.currentHp;
        facts.target.currentAudioPosition =
        GameplayWorldPoint{
            targetActor.preciseX,
            targetActor.preciseY,
            targetActor.preciseZ + static_cast<float>(targetActor.height) * 0.5f};
    }

    facts.target.currentDistance = combatTarget.distanceToTarget;
    facts.target.currentEdgeDistance = combatTarget.edgeDistance;
    facts.target.currentCanSense = combatTarget.canSense;
    facts.target.partyCanSenseActor = combatTarget.partyCanSense;
    facts.target.candidates.reserve(combatCandidates.size());

    for (const OutdoorCombatTargetCandidate &combatCandidate : combatCandidates)
    {
        ActorTargetCandidateFacts candidate = {};
        candidate.kind = ActorAiTargetKind::Actor;
        candidate.actorIndex = combatCandidate.actorIndex;
        candidate.policy = combatCandidate.policyState;
        candidate.position =
        GameplayWorldPoint{combatCandidate.preciseX, combatCandidate.preciseY, combatCandidate.targetZ};
        candidate.radius = combatCandidate.radius;
        candidate.unavailable = combatCandidate.unavailable;
        candidate.hasLineOfSight = combatCandidate.hasLineOfSight;

        if (combatCandidate.actorIndex < m_mapActors.size())
        {
        const MapActorState &targetActor = m_mapActors[combatCandidate.actorIndex];
        candidate.actorId = targetActor.actorId;
        candidate.monsterId = targetActor.monsterId;
        candidate.currentHp = targetActor.currentHp;
        candidate.height = targetActor.height;
        candidate.audioPosition =
            GameplayWorldPoint{
                targetActor.preciseX,
                targetActor.preciseY,
                targetActor.preciseZ + static_cast<float>(targetActor.height) * 0.5f};
        }

        facts.target.candidates.push_back(candidate);
    }

    facts.movement.position = GameplayWorldPoint{actor.preciseX, actor.preciseY, actor.preciseZ};
    facts.movement.homePosition = GameplayWorldPoint{actor.homePreciseX, actor.homePreciseY, actor.homePreciseZ};
    facts.movement.moveDirectionX = actor.moveDirectionX;
    facts.movement.moveDirectionY = actor.moveDirectionY;
    facts.movement.velocityX = actor.velocityX;
    facts.movement.velocityY = actor.velocityY;
    facts.movement.velocityZ = actor.velocityZ;
    facts.movement.wanderRadius = wanderRadiusForMovementType(pStats->movementType);
    {
        const GameplayActorService *pActorService = m_pGameplayActorService;
        GameplayActorService fallbackActorService = {};

        if (pActorService == nullptr)
        {
            pActorService = &fallbackActorService;
        }

        facts.movement.effectiveMoveSpeed =
            pActorService->effectiveActorMoveSpeed(
                actor.moveSpeed,
                pStats->speed,
                actor.slowMoveMultiplier,
                actor.darkGraspRemainingSeconds > 0.0f);
    }
    facts.movement.distanceToParty = length2d(partyX - actor.preciseX, partyY - actor.preciseY);
    facts.movement.edgeDistanceToParty =
        std::max(0.0f, facts.movement.distanceToParty - static_cast<float>(actor.radius) - PartyCollisionRadius);
    facts.movement.allowIdleWander = m_pGameplayActorService != nullptr;
    facts.movement.movementAllowed = pStats->movementType != MonsterTable::MonsterMovementType::Stationary;
    facts.movement.movementBlocked = false;
    {
        const GameplayActorService *pActorService = m_pGameplayActorService;
        GameplayActorService fallbackActorService = {};

        if (pActorService == nullptr)
        {
            pActorService = &fallbackActorService;
        }

        const bool partyIsVeryNearActor =
            pActorService->partyIsVeryNearActor(
                facts.movement.distanceToParty,
                partyZ - actor.preciseZ,
                actor.radius,
                actor.height,
                PartyCollisionRadius);
        const OutdoorEngagementState engagement =
            resolveOutdoorEngagementState(
                *pActorService,
                facts.identity.targetPolicy,
                combatTarget,
                facts.stats.aiType,
                actor.hostilityType,
                actor.currentHp,
                actor.maxHp,
                actor.hostileToParty,
                partyIsVeryNearActor);

        facts.movement.inMeleeRange = engagement.inMeleeRange;
    }

    facts.world.targetZ = actor.preciseZ + std::max(24.0f, static_cast<float>(actor.height) * 0.7f);
    facts.world.floorZ = actor.preciseZ;
    facts.world.active = active;
    facts.world.activeByDistance = active;

    return facts;
}

void OutdoorWorldRuntime::applyOutdoorActorAiFrameResult(
    const ActorAiFrameResult &result,
    const std::vector<bool> &activeActorMask,
    const GameplayActorAiSystem &actorAiSystem)
{
    for (const ActorAiUpdate &update : result.actorUpdates)
    {
        if (update.actorIndex >= m_mapActors.size())
        {
            continue;
        }

        MapActorState &actor = m_mapActors[update.actorIndex];
        const bool activeActor =
        update.actorIndex < activeActorMask.size()
        && activeActorMask[update.actorIndex];
        const MonsterTable::MonsterStatsEntry *pStats =
            activeActor && m_pMonsterTable != nullptr ? m_pMonsterTable->findStatsById(actor.monsterId) : nullptr;
        const bool activeBehavior = hasOutdoorActorActiveBehaviorUpdate(update, activeActor);

        if (activeActor && pStats != nullptr)
        {
            ensureOutdoorActorMovementState(actor, *pStats);
        }

        applyOutdoorActorStateUpdate(actor, update.state, activeActor, activeBehavior);
        applyOutdoorActorAnimationUpdate(actor, update.animation, activeActor, activeBehavior);

        if (activeBehavior)
        {
            applyOutdoorActorMovementIntent(
                update.actorIndex,
                actor,
                pStats,
                update.movementIntent,
                activeActorMask,
                actorAiSystem);
        }

        if (activeActor)
        {
            syncOutdoorActorIntegerPosition(actor);
            applyOutdoorActorAttackRequest(actor, update.attackRequest);
        }

        applyOutdoorActorTerminalUpdate(update.actorIndex, actor, update);
    }

    applyOutdoorActorRequests(result, activeActorMask);
}

void OutdoorWorldRuntime::applyOutdoorActorRequests(
    const ActorAiFrameResult &result,
    const std::vector<bool> &activeActorMask)
{
    applyOutdoorActorProjectileRequests(result.projectileRequests, activeActorMask);
    applyOutdoorActorAudioRequests(result.audioRequests);
    applyOutdoorActorFxRequests(result.fxRequests);
}

void OutdoorWorldRuntime::applyOutdoorActorProjectileRequests(
    const std::vector<ActorProjectileRequest> &projectileRequests,
    const std::vector<bool> &activeActorMask)
{
    for (const ActorProjectileRequest &projectileRequest : projectileRequests)
    {
        if (projectileRequest.sourceActorIndex >= m_mapActors.size()
            || projectileRequest.sourceActorIndex >= activeActorMask.size()
            || !activeActorMask[projectileRequest.sourceActorIndex])
        {
            continue;
        }

        const MapActorState &actor = m_mapActors[projectileRequest.sourceActorIndex];
        const MonsterTable::MonsterStatsEntry *pStats =
            m_pMonsterTable != nullptr ? m_pMonsterTable->findStatsById(actor.monsterId) : nullptr;

        if (pStats == nullptr)
        {
            continue;
        }

        if (m_pGameplayCombatController != nullptr)
        {
            m_pGameplayCombatController->recordMonsterRangedRelease(actor.actorId, projectileRequest.damage);
        }

        if (projectileRequest.targetKind != ActorAiTargetKind::None)
        {
            spawnProjectileFromMapActor(
                actor,
                *pStats,
                outdoorAttackAbilityFromGameplay(projectileRequest.ability),
                projectileRequest.target.x,
                projectileRequest.target.y,
                projectileRequest.target.z);
        }
    }
}

void OutdoorWorldRuntime::applyOutdoorActorAudioRequests(const std::vector<ActorAudioRequest> &audioRequests)
{
    for (const ActorAudioRequest &audioRequest : audioRequests)
    {
        if (audioRequest.actorIndex >= m_mapActors.size())
        {
            continue;
        }

        const MapActorState &actor = m_mapActors[audioRequest.actorIndex];
        const MonsterTable::MonsterStatsEntry *pStats =
            m_pMonsterTable != nullptr ? m_pMonsterTable->findStatsById(actor.monsterId) : nullptr;

        if (pStats == nullptr)
        {
            continue;
        }

        if (audioRequest.kind == ActorAiAudioRequestKind::Alert)
        {
            pushAudioEvent(
                pStats->awareSoundId,
                actor.actorId,
                "monster_alert",
                audioRequest.position.x,
                audioRequest.position.y,
                audioRequest.position.z);
        }
        else if (audioRequest.kind == ActorAiAudioRequestKind::Attack)
        {
            pushAudioEvent(
                pStats->attackSoundId,
                actor.actorId,
                "monster_attack",
                audioRequest.position.x,
                audioRequest.position.y,
                audioRequest.position.z);
        }
        else if (audioRequest.kind == ActorAiAudioRequestKind::Hit)
        {
            pushAudioEvent(
                pStats->winceSoundId,
                actor.actorId,
                "monster_hit",
                audioRequest.position.x,
                audioRequest.position.y,
                audioRequest.position.z);
        }
        else if (audioRequest.kind == ActorAiAudioRequestKind::Death)
        {
            pushAudioEvent(
                pStats->deathSoundId,
                actor.actorId,
                "monster_death",
                audioRequest.position.x,
                audioRequest.position.y,
                audioRequest.position.z);
        }
    }
}

void OutdoorWorldRuntime::applyOutdoorActorFxRequests(const std::vector<ActorFxRequest> &fxRequests)
{
    for (const ActorFxRequest &fxRequest : fxRequests)
    {
        if (fxRequest.kind == ActorAiFxRequestKind::Death)
        {
            spawnBloodSplatForActorIfNeeded(fxRequest.actorIndex);
        }
    }
}

bool OutdoorWorldRuntime::hasOutdoorActorActiveBehaviorUpdate(const ActorAiUpdate &update, bool activeActor) const
{
    return activeActor
        && (update.state.motionState
            || update.animation.animationState
            || update.state.queuedAttackAbility
            || update.movementIntent.action != ActorAiMovementAction::None
            || update.movementIntent.updateYaw
            || update.movementIntent.applyMovement);
}

void OutdoorWorldRuntime::ensureOutdoorActorMovementState(
    MapActorState &actor,
    const MonsterTable::MonsterStatsEntry &stats)
{
    if (!m_outdoorMovementController || actor.movementStateInitialized)
    {
        return;
    }

    const float collisionRadius = actorCollisionRadius(actor, &stats);
    actor.movementState = m_outdoorMovementController->initializeStateForBody(
        actor.preciseX,
        actor.preciseY,
        actor.preciseZ + GroundSnapHeight,
        collisionRadius);
    actor.movementStateInitialized = true;
    syncActorFromMovementState(actor);
}

void OutdoorWorldRuntime::applyOutdoorActorStateUpdate(
    MapActorState &actor,
    const ActorStateUpdate &state,
    bool activeActor,
    bool activeBehavior)
{
    if (state.spellEffects)
    {
        applyGameplayActorSpellEffectState(*state.spellEffects, actor);
    }

    if (state.hostilityType)
    {
        actor.hostilityType = *state.hostilityType;
    }

    if (state.hostileToParty)
    {
        actor.hostileToParty = *state.hostileToParty;
    }

    if (state.hasDetectedParty)
    {
        actor.hasDetectedParty = *state.hasDetectedParty;
    }

    if (state.bloodSplatSpawned)
    {
        actor.bloodSplatSpawned = *state.bloodSplatSpawned;
    }

    if (!activeActor)
    {
        return;
    }

    if (state.recoverySeconds)
    {
        actor.recoverySeconds = *state.recoverySeconds;
    }

    if (state.idleDecisionSeconds)
    {
        actor.idleDecisionSeconds = *state.idleDecisionSeconds;
    }

    if (state.attackCooldownSeconds)
    {
        actor.attackCooldownSeconds = *state.attackCooldownSeconds;
    }

    if (state.actionSeconds)
    {
        actor.actionSeconds = *state.actionSeconds;
    }

    if (state.attackDecisionCount)
    {
        actor.attackDecisionCount = *state.attackDecisionCount;
    }

    if (state.idleDecisionCount)
    {
        actor.idleDecisionCount = *state.idleDecisionCount;
    }

    if (state.pursueDecisionCount)
    {
        actor.pursueDecisionCount = *state.pursueDecisionCount;
    }

    if (state.crowdSideLockRemainingSeconds)
    {
        actor.crowdSideLockRemainingSeconds = *state.crowdSideLockRemainingSeconds;
    }

    if (state.crowdRetreatRemainingSeconds)
    {
        actor.crowdRetreatRemainingSeconds = *state.crowdRetreatRemainingSeconds;
    }

    if (state.crowdStandRemainingSeconds)
    {
        actor.crowdStandRemainingSeconds = *state.crowdStandRemainingSeconds;
    }

    if (state.attackImpactTriggered)
    {
        actor.attackImpactTriggered = *state.attackImpactTriggered;
    }

    if (!activeBehavior)
    {
        return;
    }

    if (state.motionState)
    {
        actor.aiState = outdoorActorAiStateFromGameplay(*state.motionState);
    }

    if (state.queuedAttackAbility)
    {
        actor.queuedAttackAbility = outdoorAttackAbilityFromGameplay(*state.queuedAttackAbility);
    }
}

void OutdoorWorldRuntime::applyOutdoorActorAnimationUpdate(
    MapActorState &actor,
    const ActorAnimationUpdate &animation,
    bool activeActor,
    bool activeBehavior)
{
    if (!activeActor)
    {
        return;
    }

    const ActorAnimation previousAnimation = actor.animation;

    if (activeBehavior && animation.animationState)
    {
        actor.animation = outdoorActorAnimationFromGameplay(*animation.animationState);
    }

    if (animation.resetOnAnimationChange
        && previousAnimation != actor.animation
        && actor.aiState != ActorAiState::Attacking)
    {
        actor.animationTimeTicks = 0.0f;
    }

    if (animation.animationTimeTicks)
    {
        actor.animationTimeTicks = *animation.animationTimeTicks;
    }

    if (animation.resetAnimationTime)
    {
        actor.animationTimeTicks = 0.0f;
    }
}

void OutdoorWorldRuntime::applyOutdoorActorMovementIntent(
    size_t actorIndex,
    MapActorState &actor,
    const MonsterTable::MonsterStatsEntry *pStats,
    const ActorMovementIntent &movementIntent,
    const std::vector<bool> &activeActorMask,
    const GameplayActorAiSystem &actorAiSystem)
{
    if (movementIntent.action != ActorAiMovementAction::None)
    {
        actor.moveDirectionX = movementIntent.moveDirectionX;
        actor.moveDirectionY = movementIntent.moveDirectionY;
    }

    if (movementIntent.updateYaw)
    {
        actor.yawRadians = movementIntent.yawRadians;
    }

    if (movementIntent.resetCrowdSteering)
    {
        resetCrowdSteeringState(actor);
    }

    if (movementIntent.clearVelocity)
    {
        actor.velocityX = 0.0f;
        actor.velocityY = 0.0f;
        actor.velocityZ = 0.0f;
    }

    if (!movementIntent.applyMovement || pStats == nullptr)
    {
        return;
    }

    ActorAiState nextAiState = actor.aiState;
    ActorAnimation nextAnimation = actor.animation;
    float desiredMoveX = movementIntent.desiredMoveX;
    float desiredMoveY = movementIntent.desiredMoveY;

    applyOutdoorActorMovementIntegration(
        actorIndex,
        pStats,
        activeActorMask,
        movementIntent.moveSpeed,
        movementIntent.meleePursuitActive,
        movementIntent.inMeleeRange,
        movementIntent.targetPosition,
        movementIntent.targetEdgeDistance,
        actorAiSystem,
        nextAiState,
        nextAnimation,
        desiredMoveX,
        desiredMoveY);
}

void OutdoorWorldRuntime::applyOutdoorActorAttackRequest(
    MapActorState &actor,
    const std::optional<ActorAttackRequest> &attackRequest)
{
    if (!attackRequest)
    {
        return;
    }

    if (attackRequest->kind == ActorAiAttackRequestKind::PartyMelee)
    {
        if (m_pGameplayCombatController != nullptr)
        {
            m_pGameplayCombatController->recordMonsterMeleeImpact(actor.actorId, attackRequest->damage);
        }
    }
    else if (attackRequest->kind == ActorAiAttackRequestKind::ActorMelee)
    {
        applyMonsterAttackToMapActor(
            attackRequest->targetActorIndex,
            attackRequest->damage,
            actor.actorId,
            false);
    }
}

void OutdoorWorldRuntime::applyOutdoorActorTerminalUpdate(
    size_t actorIndex,
    MapActorState &actor,
    const ActorAiUpdate &update)
{
    const bool terminalActor =
        actor.isDead
        || actor.currentHp <= 0
        || actor.aiState == ActorAiState::Dying
        || actor.aiState == ActorAiState::Dead;

    if (!terminalActor)
    {
        return;
    }

    resetCrowdSteeringState(actor);

    if (update.movementIntent.clearVelocity)
    {
        actor.moveDirectionX = 0.0f;
        actor.moveDirectionY = 0.0f;
        actor.velocityX = 0.0f;
        actor.velocityY = 0.0f;
        actor.velocityZ = 0.0f;
    }

    if (update.state.attackImpactTriggered)
    {
        actor.attackImpactTriggered = *update.state.attackImpactTriggered;
    }
    else
    {
        actor.attackImpactTriggered = false;
    }

    if (update.state.dead && *update.state.dead)
    {
        setMapActorDead(actorIndex, true, false);
        return;
    }

    if (update.state.motionState)
    {
        actor.aiState = outdoorActorAiStateFromGameplay(*update.state.motionState);
    }

    if (update.animation.animationState)
    {
        actor.animation = outdoorActorAnimationFromGameplay(*update.animation.animationState);
    }

    if (update.animation.animationTimeTicks)
    {
        actor.animationTimeTicks = *update.animation.animationTimeTicks;
    }

    if (update.state.actionSeconds)
    {
        actor.actionSeconds = *update.state.actionSeconds;
    }

    syncOutdoorActorIntegerPosition(actor);
}

void OutdoorWorldRuntime::syncOutdoorActorIntegerPosition(MapActorState &actor) const
{
    actor.x = static_cast<int>(std::lround(actor.preciseX));
    actor.y = static_cast<int>(std::lround(actor.preciseY));
    actor.z = static_cast<int>(std::lround(actor.preciseZ));
}

void OutdoorWorldRuntime::applyOutdoorActorPostMovementAiUpdate(
    MapActorState &actor,
    const ActorAiUpdate &movementUpdate,
    float &desiredMoveX,
    float &desiredMoveY)
{
    if (movementUpdate.state.pursueDecisionCount)
    {
        actor.pursueDecisionCount = *movementUpdate.state.pursueDecisionCount;
    }

    if (movementUpdate.state.crowdSideLockRemainingSeconds)
    {
        actor.crowdSideLockRemainingSeconds = *movementUpdate.state.crowdSideLockRemainingSeconds;
    }

    if (movementUpdate.state.crowdNoProgressSeconds)
    {
        actor.crowdNoProgressSeconds = *movementUpdate.state.crowdNoProgressSeconds;
    }

    if (movementUpdate.state.crowdLastEdgeDistance)
    {
        actor.crowdLastEdgeDistance = *movementUpdate.state.crowdLastEdgeDistance;
    }

    if (movementUpdate.state.crowdRetreatRemainingSeconds)
    {
        actor.crowdRetreatRemainingSeconds = *movementUpdate.state.crowdRetreatRemainingSeconds;
    }

    if (movementUpdate.state.crowdStandRemainingSeconds)
    {
        actor.crowdStandRemainingSeconds = *movementUpdate.state.crowdStandRemainingSeconds;
    }

    if (movementUpdate.state.crowdProbeEdgeDistance)
    {
        actor.crowdProbeEdgeDistance = *movementUpdate.state.crowdProbeEdgeDistance;
    }

    if (movementUpdate.state.crowdProbeElapsedSeconds)
    {
        actor.crowdProbeElapsedSeconds = *movementUpdate.state.crowdProbeElapsedSeconds;
    }

    if (movementUpdate.state.crowdEscapeAttempts)
    {
        actor.crowdEscapeAttempts = *movementUpdate.state.crowdEscapeAttempts;
    }

    if (movementUpdate.state.crowdSideSign)
    {
        actor.crowdSideSign = *movementUpdate.state.crowdSideSign;
    }

    if (movementUpdate.movementIntent.updateCrowdProbePosition)
    {
        actor.crowdProbeX = actor.preciseX;
        actor.crowdProbeY = actor.preciseY;
        desiredMoveX = movementUpdate.movementIntent.desiredMoveX;
        desiredMoveY = movementUpdate.movementIntent.desiredMoveY;
    }

    if (movementUpdate.movementIntent.clearVelocity)
    {
        actor.velocityX = 0.0f;
        actor.velocityY = 0.0f;
    }

    if (movementUpdate.movementIntent.action == ActorAiMovementAction::Stand
        || movementUpdate.movementIntent.action == ActorAiMovementAction::Pursue
        || movementUpdate.movementIntent.action == ActorAiMovementAction::Flee)
    {
        actor.moveDirectionX = movementUpdate.movementIntent.moveDirectionX;
        actor.moveDirectionY = movementUpdate.movementIntent.moveDirectionY;
    }

    if (movementUpdate.movementIntent.updateYaw)
    {
        actor.yawRadians = movementUpdate.movementIntent.yawRadians;
    }

    if (movementUpdate.state.actionSeconds)
    {
        actor.actionSeconds = *movementUpdate.state.actionSeconds;
    }

    if (movementUpdate.state.motionState)
    {
        actor.aiState = outdoorActorAiStateFromGameplay(*movementUpdate.state.motionState);
    }

    if (movementUpdate.animation.animationState)
    {
        actor.animation = outdoorActorAnimationFromGameplay(*movementUpdate.animation.animationState);
    }

    if (movementUpdate.animation.animationTimeTicks)
    {
        actor.animationTimeTicks = *movementUpdate.animation.animationTimeTicks;
    }

    if (movementUpdate.state.idleDecisionSeconds)
    {
        actor.idleDecisionSeconds = *movementUpdate.state.idleDecisionSeconds;
    }

    if (movementUpdate.state.attackImpactTriggered)
    {
        actor.attackImpactTriggered = *movementUpdate.state.attackImpactTriggered;
    }
}

void OutdoorWorldRuntime::applyOutdoorActorMovementIntegration(
    size_t actorIndex,
    const MonsterTable::MonsterStatsEntry *pStats,
    const std::vector<bool> &activeActorMask,
    float moveSpeed,
    bool meleePursuitActive,
    bool inMeleeRange,
    const GameplayWorldPoint &targetPosition,
    float targetEdgeDistance,
    const GameplayActorAiSystem &actorAiSystem,
    ActorAiState &nextAiState,
    ActorAnimation &nextAnimation,
    float &desiredMoveX,
    float &desiredMoveY)
{
    if (actorIndex >= m_mapActors.size() || pStats == nullptr)
    {
        return;
    }

    MapActorState &actor = m_mapActors[actorIndex];

    if (m_pOutdoorMapData != nullptr)
    {
        applyOutdoorWaterRestriction(
        *m_pOutdoorMapData,
        m_outdoorLandMask,
        pStats,
        actor,
        moveSpeed,
        desiredMoveX,
        desiredMoveY,
        nextAiState,
        nextAnimation);
    }

    actor.velocityX = desiredMoveX * moveSpeed;
    actor.velocityY = desiredMoveY * moveSpeed;
    actor.velocityZ = 0.0f;

    if (m_pOutdoorMapData != nullptr)
    {
        applyOeOutdoorSteepSlopeResponse(actor, *m_pOutdoorMapData, pStats);
    }

    const float moveDeltaX = actor.velocityX * ActorUpdateStepSeconds;
    const float moveDeltaY = actor.velocityY * ActorUpdateStepSeconds;
    bool moved = false;
    size_t contactedActorCount = 0;
    std::vector<size_t> contactedActorIndices;

    if (m_outdoorMovementController && actor.movementStateInitialized && m_pMonsterTable != nullptr)
    {
        m_outdoorMovementController->setActorColliders(
        buildNearbyActorMovementColliders(m_mapActors, activeActorMask, *m_pMonsterTable));
        const float collisionRadius = actorCollisionRadius(actor, pStats);
        const float collisionHeight = actorCollisionHeight(actor, collisionRadius);
        actor.movementState = m_outdoorMovementController->resolveOutdoorActorMove(
        actor.movementState,
        OutdoorBodyDimensions{collisionRadius, collisionHeight},
        actor.velocityX,
        actor.velocityY,
        actor.velocityZ,
        pStats->canFly,
        ActorUpdateStepSeconds,
        &contactedActorIndices,
        OutdoorIgnoredActorCollider{OutdoorActorCollisionSource::MapDelta, actorIndex});
        syncActorFromMovementState(actor);
        actor.velocityZ = actor.movementState.verticalVelocity;
        moved = true;

        std::sort(contactedActorIndices.begin(), contactedActorIndices.end());
        contactedActorCount = static_cast<size_t>(
        std::distance(
            contactedActorIndices.begin(),
            std::unique(contactedActorIndices.begin(), contactedActorIndices.end())));
    }
    else
    {
        if (m_pOutdoorMapData != nullptr)
        {
        moved = tryMoveActorInWorld(
            actor,
            *m_pOutdoorMapData,
            m_outdoorFaces,
            pStats,
            moveDeltaX,
            moveDeltaY);

        if (!moved && std::abs(moveDeltaX) > 0.001f)
        {
            moved = tryMoveActorInWorld(
                actor,
                *m_pOutdoorMapData,
                m_outdoorFaces,
                pStats,
                moveDeltaX,
                0.0f);
        }

        if (!moved && std::abs(moveDeltaY) > 0.001f)
        {
            moved = tryMoveActorInWorld(
                actor,
                *m_pOutdoorMapData,
                m_outdoorFaces,
                pStats,
                0.0f,
                moveDeltaY);
        }
        }
        else
        {
        actor.preciseX += moveDeltaX;
        actor.preciseY += moveDeltaY;
        moved = true;
        }
    }

    ActorAiFacts movementFacts = {};
    movementFacts.actorIndex = actorIndex;
    movementFacts.actorId = actor.actorId;
    movementFacts.identity.hostilityType = actor.hostilityType;
    movementFacts.stats.canFly = pStats->canFly;
    movementFacts.runtime.motionState = actorAiMotionStateFromOutdoor(actor.aiState);
    movementFacts.runtime.actionSeconds = actor.actionSeconds;
    movementFacts.runtime.crowdNoProgressSeconds = actor.crowdNoProgressSeconds;
    movementFacts.runtime.crowdLastEdgeDistance = actor.crowdLastEdgeDistance;
    movementFacts.runtime.crowdRetreatRemainingSeconds = actor.crowdRetreatRemainingSeconds;
    movementFacts.runtime.crowdStandRemainingSeconds = actor.crowdStandRemainingSeconds;
    movementFacts.runtime.crowdProbeEdgeDistance = actor.crowdProbeEdgeDistance;
    movementFacts.runtime.crowdProbeElapsedSeconds = actor.crowdProbeElapsedSeconds;
    movementFacts.runtime.pursueDecisionCount = actor.pursueDecisionCount;
    movementFacts.runtime.crowdEscapeAttempts = actor.crowdEscapeAttempts;
    movementFacts.runtime.crowdSideSign = actor.crowdSideSign;
    movementFacts.movement.position = GameplayWorldPoint{actor.preciseX, actor.preciseY, actor.preciseZ};
    movementFacts.movement.contactedActorCount = contactedActorCount;

    if (!contactedActorIndices.empty())
    {
        const size_t contactedActorIndex = contactedActorIndices.front();

        if (contactedActorIndex < m_mapActors.size())
        {
            const MapActorState &contactedActor = m_mapActors[contactedActorIndex];
            movementFacts.movement.hasContactedActor = true;
            movementFacts.movement.contactedActorHostilityType = contactedActor.hostilityType;
            movementFacts.movement.contactedActorPosition =
                GameplayWorldPoint{contactedActor.preciseX, contactedActor.preciseY, contactedActor.preciseZ};
        }
    }

    movementFacts.movement.meleePursuitActive = meleePursuitActive;
    movementFacts.movement.inMeleeRange = inMeleeRange;
    movementFacts.movement.allowCrowdSteering = m_pGameplayActorService != nullptr;
    movementFacts.movement.crowdSteeringTriggersOnMovementBlocked = false;
    movementFacts.movement.crowdSidestepAngleRadians = Pi * 0.30555556f;
    movementFacts.movement.crowdRetreatAngleRadians = Pi * 0.53f;
    movementFacts.movement.movementBlocked = !moved;
    movementFacts.target.currentPosition = targetPosition;
    movementFacts.target.currentEdgeDistance = targetEdgeDistance;
    const ActorAiUpdate movementUpdate = actorAiSystem.updateActorAfterWorldMovement(movementFacts);
    applyOutdoorActorPostMovementAiUpdate(actor, movementUpdate, desiredMoveX, desiredMoveY);
}

void OutdoorWorldRuntime::updateOutdoorInactiveAndInvalidActors(
    float partyX,
    float partyY,
    float partyZ,
    const std::vector<bool> &activeActorMask)
{
    for (size_t actorIndex = 0; actorIndex < m_mapActors.size(); ++actorIndex)
    {
        MapActorState &actor = m_mapActors[actorIndex];
        const MonsterTable::MonsterStatsEntry *pStats = m_pMonsterTable->findStatsById(actor.monsterId);

        if (pStats == nullptr)
        {
            const InactiveActorDeathFrame earlyDeathFrame = resolveInactiveActorDeathFrame(
                actor.isDead,
                actor.currentHp <= 0,
                actor.currentHp <= 0 && actor.aiState == ActorAiState::Dying,
                actor.actionSeconds,
                ActorUpdateStepSeconds);

            if (earlyDeathFrame.action == InactiveActorDeathAction::HoldDead)
            {
                resetCrowdSteeringState(actor);
                actor.aiState = ActorAiState::Dead;
                actor.animation = ActorAnimation::Dead;
                continue;
            }

            if (earlyDeathFrame.action == InactiveActorDeathAction::MarkDead
                || earlyDeathFrame.action == InactiveActorDeathAction::AdvanceDying)
            {
                spawnBloodSplatForActorIfNeeded(actorIndex);
                resetCrowdSteeringState(actor);
                actor.moveDirectionX = 0.0f;
                actor.moveDirectionY = 0.0f;
                actor.velocityX = 0.0f;
                actor.velocityY = 0.0f;
                actor.velocityZ = 0.0f;
                actor.attackImpactTriggered = false;

                if (earlyDeathFrame.action == InactiveActorDeathAction::AdvanceDying)
                {
                    actor.animation = ActorAnimation::Dying;
                    actor.animationTimeTicks += ActorUpdateStepSeconds * TicksPerSecond;
                    actor.actionSeconds = earlyDeathFrame.actionSeconds;

                    if (earlyDeathFrame.finishedDying)
                    {
                        setMapActorDead(actorIndex, true, false);
                    }
                }
                else
                {
                    setMapActorDead(actorIndex, true, false);
                }

                continue;
            }

            resetCrowdSteeringState(actor);
            actor.animation = ActorAnimation::Standing;
            continue;
        }

        const bool selectedForActiveUpdate = actorIndex < activeActorMask.size() && activeActorMask[actorIndex];

        if (!selectedForActiveUpdate)
        {
            resetCrowdSteeringState(actor);

            const InactiveActorDeathFrame inactiveDeathFrame = resolveInactiveActorDeathFrame(
                actor.isDead,
                actor.currentHp <= 0,
                actor.currentHp <= 0 && actor.aiState == ActorAiState::Dying,
                actor.actionSeconds,
                ActorUpdateStepSeconds);

            if (inactiveDeathFrame.action == InactiveActorDeathAction::HoldDead)
            {
                actor.aiState = ActorAiState::Dead;
                actor.animation = ActorAnimation::Dead;
                actor.moveDirectionX = 0.0f;
                actor.moveDirectionY = 0.0f;
                actor.velocityX = 0.0f;
                actor.velocityY = 0.0f;
                actor.velocityZ = 0.0f;
                actor.actionSeconds = 0.0f;
                actor.attackImpactTriggered = false;
                continue;
            }

            if (inactiveDeathFrame.action == InactiveActorDeathAction::MarkDead
                || inactiveDeathFrame.action == InactiveActorDeathAction::AdvanceDying)
            {
                spawnBloodSplatForActorIfNeeded(actorIndex);
                actor.moveDirectionX = 0.0f;
                actor.moveDirectionY = 0.0f;
                actor.velocityX = 0.0f;
                actor.velocityY = 0.0f;
                actor.velocityZ = 0.0f;
                actor.attackImpactTriggered = false;

                if (inactiveDeathFrame.action == InactiveActorDeathAction::AdvanceDying)
                {
                    actor.aiState = ActorAiState::Dying;
                    actor.animation = ActorAnimation::Dying;
                    actor.animationTimeTicks += ActorUpdateStepSeconds * TicksPerSecond;
                    actor.actionSeconds = inactiveDeathFrame.actionSeconds;

                    if (inactiveDeathFrame.finishedDying)
                    {
                        setMapActorDead(actorIndex, true, false);
                    }
                }
                else
                {
                    setMapActorDead(actorIndex, true, false);
                }

                continue;
            }

            updateInactiveActorPresentation(actor, partyX, partyY, m_pGameplayActorService);
            continue;
        }
    }
}

void OutdoorWorldRuntime::applyActorFrameSideEffects(float deltaSeconds, float partyX, float partyY, float partyZ)
{
    updateWorldItems(deltaSeconds);
    updateProjectiles(deltaSeconds, partyX, partyY, partyZ);
    updateFireSpikeTraps(deltaSeconds, partyX, partyY, partyZ);
}

void OutdoorWorldRuntime::updateMapActors(float deltaSeconds, float partyX, float partyY, float partyZ)
{
    if (deltaSeconds <= 0.0f || m_pMonsterTable == nullptr)
    {
        return;
    }

    updateActorFrameGlobalEffects(deltaSeconds, partyX, partyY, partyZ);

    while (m_actorUpdateAccumulatorSeconds >= ActorUpdateStepSeconds)
    {
        const std::vector<bool> activeActorMask = selectOutdoorActiveActors(partyX, partyY, partyZ);
        const ActorAiFrameFacts actorAiFacts =
            collectOutdoorActorAiFrameFacts(ActorUpdateStepSeconds, partyX, partyY, partyZ, activeActorMask);
        const GameplayActorAiSystem actorAiSystem = {};
        const ActorAiFrameResult actorAiResult = actorAiSystem.updateActors(actorAiFacts);
        applyOutdoorActorAiFrameResult(actorAiResult, activeActorMask, actorAiSystem);

        updateOutdoorInactiveAndInvalidActors(partyX, partyY, partyZ, activeActorMask);
        applyActorFrameSideEffects(ActorUpdateStepSeconds, partyX, partyY, partyZ);
        m_actorUpdateAccumulatorSeconds -= ActorUpdateStepSeconds;
    }
}

void OutdoorWorldRuntime::queueActorAiUpdate(float deltaSeconds, float partyX, float partyY, float partyZ)
{
    if (deltaSeconds <= 0.0f)
    {
        return;
    }

    m_actorAiUpdateQueued = true;
    m_queuedActorAiDeltaSeconds += deltaSeconds;
    m_queuedActorAiPartyX = partyX;
    m_queuedActorAiPartyY = partyY;
    m_queuedActorAiPartyZ = partyZ;
}

bool OutdoorWorldRuntime::spawnProjectileFromMapActor(
    const MapActorState &actor,
    const MonsterTable::MonsterStatsEntry &stats,
    MonsterAttackAbility ability,
    float targetX,
    float targetY,
    float targetZ
)
{
    if (ability == MonsterAttackAbility::Spell1 || ability == MonsterAttackAbility::Spell2)
    {
        return castSpellFromMapActor(actor, stats, ability, targetX, targetY, targetZ);
    }

    if (m_pMonsterProjectileTable == nullptr || m_pObjectTable == nullptr || m_pSpellTable == nullptr)
    {
        std::cout
            << "Projectile spawn skipped actor=" << actor.actorId
            << " ability=" << monsterAttackAbilityName(ability)
            << " reason=missing_runtime_tables"
            << '\n';
        return false;
    }

    ResolvedProjectileDefinition definition = {};

    if (!resolveProjectileDefinition(
            stats,
            ability,
            *m_pMonsterProjectileTable,
            *m_pObjectTable,
            *m_pSpellTable,
            definition))
    {
        const std::string projectileToken =
            ability == MonsterAttackAbility::Attack1
                ? stats.attack1MissileType
                : ability == MonsterAttackAbility::Attack2 ? stats.attack2MissileType : std::string();
        const std::string spellName =
            ability == MonsterAttackAbility::Spell1
                ? stats.spell1Name
                : ability == MonsterAttackAbility::Spell2 ? stats.spell2Name : std::string();

        std::cout
            << "Projectile spawn skipped actor=" << actor.actorId
            << " ability=" << monsterAttackAbilityName(ability)
            << " missile=\"" << debugStringOrNone(projectileToken) << "\""
            << " spell=\"" << debugStringOrNone(spellName) << "\""
            << " reason=unresolved_definition"
            << '\n';
        return false;
    }

    const float sourceX = actor.preciseX;
    const float sourceY = actor.preciseY;
    const float sourceZ = actor.preciseZ + std::max(24.0f, static_cast<float>(actor.height) * 0.7f);
    const float aimX = targetX;
    const float aimY = targetY;
    const float aimZ = targetZ;
    const uint16_t objectSpriteFrameIndex = resolveRuntimeSpriteFrameIndex(
        m_pProjectileSpriteFrameTable,
        definition.objectSpriteId,
        definition.objectSpriteName);
    GameplayProjectileService::ProjectileSpawnRequest spawnRequest = {};
    spawnRequest.sourceKind = ProjectileState::SourceKind::Actor;
    spawnRequest.sourceId = actor.actorId;
    spawnRequest.sourceMonsterId = actor.monsterId;
    spawnRequest.fromSummonedMonster =
        m_pGameplayActorService != nullptr
        && m_pGameplayActorService->isPartyControlledActor(gameplayActorControlModeFromOutdoor(actor.controlMode));
    spawnRequest.ability = ability;
    spawnRequest.definition = buildGameplayProjectileDefinition(definition, objectSpriteFrameIndex);
    spawnRequest.sourceX = sourceX;
    spawnRequest.sourceY = sourceY;
    spawnRequest.sourceZ = sourceZ;
    spawnRequest.targetX = aimX;
    spawnRequest.targetY = aimY;
    spawnRequest.targetZ = aimZ;
    spawnRequest.spawnForwardOffset = static_cast<float>(actor.radius) + 8.0f;
    const GameplayProjectileService::ProjectileSpawnResult spawnResult =
        projectileService().spawnProjectile(spawnRequest);
    const GameplayProjectileService::ProjectileSpawnEffects spawnEffects =
        projectileService().buildProjectileSpawnEffects(spawnResult);

    if (!applyProjectileSpawnEffects(
            spawnResult,
            spawnEffects,
            "monster",
            "monster_projectile_zero_distance"))
    {
        std::cout
            << "Projectile spawn skipped actor=" << actor.actorId
            << " ability=" << monsterAttackAbilityName(ability)
            << " reason=zero_distance_target"
            << '\n';
        return false;
    }

    return true;
}

bool OutdoorWorldRuntime::castSpellFromMapActor(
    const MapActorState &actor,
    const MonsterTable::MonsterStatsEntry &stats,
    MonsterAttackAbility ability,
    float targetX,
    float targetY,
    float targetZ
)
{
    if (m_pSpellTable == nullptr)
    {
        std::cout
            << "Spell cast skipped actor=" << actor.actorId
            << " ability=" << monsterAttackAbilityName(ability)
            << " reason=missing_spell_table"
            << '\n';
        return false;
    }

    const std::string &spellName =
        ability == MonsterAttackAbility::Spell1 ? stats.spell1Name : stats.spell2Name;

    if (spellName.empty())
    {
        std::cout
            << "Spell cast skipped actor=" << actor.actorId
            << " ability=" << monsterAttackAbilityName(ability)
            << " reason=empty_spell_name"
            << '\n';
        return false;
    }

    if (!isProjectileSpellName(spellName) && spellName != "meteor shower" && spellName != "starburst")
    {
        std::cout
            << "Spell cast skipped actor=" << actor.actorId
            << " ability=" << monsterAttackAbilityName(ability)
            << " spell=\"" << spellName << "\""
            << " reason=unsupported_nonprojectile_spell"
            << '\n';
        return false;
    }

    const SpellEntry *pSpellEntry = m_pSpellTable->findByName(spellName);

    if (pSpellEntry == nullptr)
    {
        std::cout
            << "Spell cast skipped actor=" << actor.actorId
            << " ability=" << monsterAttackAbilityName(ability)
            << " spell=\"" << spellName << "\""
            << " reason=spell_not_found"
            << '\n';
        return false;
    }

    SpellCastRequest request = {};
    request.sourceKind = RuntimeSpellSourceKind::Actor;
    request.sourceId = actor.actorId;
    request.sourceMonsterId = actor.monsterId;
    request.fromSummonedMonster =
        m_pGameplayActorService != nullptr
        && m_pGameplayActorService->isPartyControlledActor(gameplayActorControlModeFromOutdoor(actor.controlMode));
    request.ability = ability;
    request.spellId = static_cast<uint32_t>(pSpellEntry->id);
    request.skillLevel = static_cast<uint32_t>(std::max(stats.level, 1));
    const SpellId resolvedSpellId = spellIdFromValue(std::max(pSpellEntry->id, 0));
    request.skillMastery = resolvedSpellId == SpellId::MeteorShower
        ? static_cast<uint32_t>(SkillMastery::Master)
        : resolvedSpellId == SpellId::Starburst
        ? static_cast<uint32_t>(SkillMastery::Grandmaster)
        : static_cast<uint32_t>(SkillMastery::None);
    request.sourceX = actor.preciseX;
    request.sourceY = actor.preciseY;
    request.sourceZ = actor.preciseZ + std::max(24.0f, static_cast<float>(actor.height) * 0.7f);
    request.targetX = targetX;
    request.targetY = targetY;
    request.targetZ = targetZ;
    return castSpell(request);
}

bool OutdoorWorldRuntime::castSpell(const SpellCastRequest &request)
{
    if (m_pObjectTable == nullptr || m_pSpellTable == nullptr)
    {
        return false;
    }

    const SpellEntry *pSpellEntry = m_pSpellTable->findById(static_cast<int>(request.spellId));

    if (pSpellEntry == nullptr)
    {
        return false;
    }

    ResolvedProjectileDefinition definition = {};

    if (!resolveSpellDefinition(*pSpellEntry, *m_pObjectTable, definition))
    {
        return false;
    }

    if (isSpellId(request.spellId, SpellId::MeteorShower))
    {
        return castMeteorShower(request, definition);
    }

    if (isSpellId(request.spellId, SpellId::Starburst))
    {
        return castStarburst(request, definition);
    }

    return castDirectSpellProjectile(request, definition);
}

bool OutdoorWorldRuntime::resolveObjectProjectileDefinition(
    int objectId,
    int impactObjectId,
    ResolvedProjectileDefinition &definition) const
{
    if (m_pObjectTable == nullptr)
    {
        return false;
    }

    return ::OpenYAMM::Game::resolveObjectProjectileDefinition(objectId, impactObjectId, *m_pObjectTable, definition);
}

bool OutdoorWorldRuntime::castDirectSpellProjectile(
    const SpellCastRequest &request,
    const ResolvedProjectileDefinition &definition
)
{
    return spawnSpellProjectile(
        request,
        definition,
        request.sourceX,
        request.sourceY,
        request.sourceZ,
        request.targetX,
        request.targetY,
        request.targetZ,
        0.0f);
}

bool OutdoorWorldRuntime::spawnDeathBlossomFalloutProjectiles(
    const ProjectileState &projectile,
    float x,
    float y,
    float z)
{
    ResolvedProjectileDefinition definition = {};

    if (!resolveObjectProjectileDefinition(4092, 4091, definition))
    {
        return false;
    }

    const uint16_t objectSpriteFrameIndex = resolveRuntimeSpriteFrameIndex(
        m_pProjectileSpriteFrameTable,
        definition.objectSpriteId,
        definition.objectSpriteName);
    const GameplayProjectileService::ProjectileDefinition projectileDefinition =
        buildGameplayProjectileDefinition(definition, objectSpriteFrameIndex);
    const std::vector<GameplayProjectileService::ProjectileSpawnResult> falloutResults =
        projectileService().spawnDeathBlossomFalloutProjectiles(projectile, projectileDefinition, x, y, z);
    bool spawnedAny = false;

    for (const GameplayProjectileService::ProjectileSpawnResult &spawnResult : falloutResults)
    {
        const GameplayProjectileService::ProjectileSpawnEffects spawnEffects =
            projectileService().buildProjectileSpawnEffects(spawnResult);

        if (applyProjectileSpawnEffects(
                spawnResult,
                spawnEffects,
                projectileSourceKindName(spawnResult.projectile.sourceKind),
                "death_blossom_fallout_zero_distance"))
        {
            spawnedAny = true;
        }
    }

    return spawnedAny;
}

bool OutdoorWorldRuntime::castMeteorShower(
    const SpellCastRequest &request,
    const ResolvedProjectileDefinition &definition
)
{
    const std::vector<GameplayProjectileService::AreaSpellProjectileShot> shots =
        projectileService().buildMeteorShowerProjectileShots(
            request.skillMastery,
            projectileService().nextProjectileId(),
            request.targetX,
            request.targetY,
            request.targetZ);
    bool spawnedAny = false;

    for (const GameplayProjectileService::AreaSpellProjectileShot &shot : shots)
    {
        float meteorTargetZ = shot.targetZ;

        if (m_pOutdoorMapData != nullptr)
        {
            meteorTargetZ = std::max(
                meteorTargetZ,
                sampleOutdoorTerrainHeight(*m_pOutdoorMapData, shot.targetX, shot.targetY));
        }

        const float meteorSourceZ = meteorTargetZ + shot.sourceHeightOffset;
        spawnedAny = spawnSpellProjectile(
            request,
            definition,
            shot.sourceX,
            shot.sourceY,
            meteorSourceZ,
            shot.targetX,
            shot.targetY,
            meteorTargetZ,
            0.0f)
            || spawnedAny;
    }

    return spawnedAny;
}

bool OutdoorWorldRuntime::castStarburst(
    const SpellCastRequest &request,
    const ResolvedProjectileDefinition &definition
)
{
    const std::vector<GameplayProjectileService::AreaSpellProjectileShot> shots =
        projectileService().buildStarburstProjectileShots(
            projectileService().nextProjectileId(),
            request.targetX,
            request.targetY,
            request.targetZ);
    bool spawnedAny = false;

    for (const GameplayProjectileService::AreaSpellProjectileShot &shot : shots)
    {
        float starTargetZ = shot.targetZ;
        float starSourceBaseZ = shot.targetZ;

        if (m_pOutdoorMapData != nullptr)
        {
            starTargetZ = std::max(
                starTargetZ,
                sampleOutdoorTerrainHeight(*m_pOutdoorMapData, shot.targetX, shot.targetY));
            starSourceBaseZ = std::max(
                starSourceBaseZ,
                sampleOutdoorTerrainHeight(*m_pOutdoorMapData, shot.sourceX, shot.sourceY));
        }

        const float starSourceZ = starSourceBaseZ + shot.sourceHeightOffset;
        spawnedAny = spawnSpellProjectile(
            request,
            definition,
            shot.sourceX,
            shot.sourceY,
            starSourceZ,
            shot.targetX,
            shot.targetY,
            starTargetZ,
            0.0f)
            || spawnedAny;
    }

    return spawnedAny;
}

bool OutdoorWorldRuntime::spawnSpellProjectile(
    const SpellCastRequest &request,
    const ResolvedProjectileDefinition &definition,
    float sourceX,
    float sourceY,
    float sourceZ,
    float targetX,
    float targetY,
    float targetZ,
    float spawnForwardOffset
)
{
    const uint16_t objectSpriteFrameIndex = resolveRuntimeSpriteFrameIndex(
        m_pProjectileSpriteFrameTable,
        definition.objectSpriteId,
        definition.objectSpriteName);
    GameplayProjectileService::ProjectileSpawnRequest spawnRequest = {};
    spawnRequest.sourceKind = projectileSourceKindFromSpellSource(request.sourceKind);
    spawnRequest.sourceId = request.sourceId;
    spawnRequest.sourcePartyMemberIndex = request.sourcePartyMemberIndex;
    spawnRequest.sourceMonsterId = request.sourceMonsterId;
    spawnRequest.fromSummonedMonster = request.fromSummonedMonster;
    spawnRequest.ability = request.ability;
    spawnRequest.definition = buildGameplayProjectileDefinition(definition, objectSpriteFrameIndex);
    spawnRequest.skillLevel = request.skillLevel;
    spawnRequest.skillMastery = request.skillMastery;
    spawnRequest.damage = request.damage;
    spawnRequest.attackBonus = request.attackBonus;
    spawnRequest.useActorHitChance = request.useActorHitChance;
    spawnRequest.sourceX = sourceX;
    spawnRequest.sourceY = sourceY;
    spawnRequest.sourceZ = sourceZ;
    spawnRequest.targetX = targetX;
    spawnRequest.targetY = targetY;
    spawnRequest.targetZ = targetZ;
    spawnRequest.spawnForwardOffset = spawnForwardOffset;
    spawnRequest.allowInstantImpact = true;
    const GameplayProjectileService::ProjectileSpawnResult spawnResult =
        projectileService().spawnProjectile(spawnRequest);
    const GameplayProjectileService::ProjectileSpawnEffects spawnEffects =
        projectileService().buildProjectileSpawnEffects(spawnResult);

    return applyProjectileSpawnEffects(
        spawnResult,
        spawnEffects,
        spellSourceKindName(request.sourceKind),
        "spell_zero_distance");
}

void OutdoorWorldRuntime::spawnProjectileImpact(
    const ProjectileState &projectile,
    float x,
    float y,
    float z,
    bool centerVertically)
{
    if (const std::optional<GameplayProjectileService::ProjectileAudioRequest> audioRequest =
            projectileService().buildProjectileImpactAudioRequest(projectile, x, y, z))
    {
        pushProjectileAudioEvent(*audioRequest);
    }

    if (projectile.impactObjectDescriptionId == 0 || m_pObjectTable == nullptr)
    {
        return;
    }

    const std::optional<GameplayProjectileService::ProjectileImpactVisualDefinition> impactDefinition =
        projectileService().buildProjectileImpactVisualDefinition(
            projectile.impactObjectDescriptionId,
            m_pObjectTable,
            m_pProjectileSpriteFrameTable);

    if (!impactDefinition)
    {
        return;
    }

    const GameplayProjectileService::ProjectileImpactSpawnResult result =
        spawnProjectileImpactVisual(projectile, *impactDefinition, x, y, z, centerVertically);

    if (result.spawned && result.pImpact != nullptr)
    {
        logProjectileImpactEffect(projectile, *result.pImpact);
    }
}

bool OutdoorWorldRuntime::spawnWaterSplashImpact(float x, float y, float z)
{
    if (m_pObjectTable == nullptr || m_pProjectileSpriteFrameTable == nullptr)
    {
        return false;
    }

    const std::optional<GameplayProjectileService::ProjectileImpactVisualDefinition> splashDefinition =
        projectileService().buildWaterSplashImpactVisualDefinition(m_pObjectTable, m_pProjectileSpriteFrameTable);

    if (!splashDefinition)
    {
        return false;
    }

    spawnWaterSplashImpactVisual(*splashDefinition, x, y, z);

    if (const std::optional<GameplayProjectileService::ProjectileAudioRequest> audioRequest =
            projectileService().buildWaterSplashAudioRequest(x, y, z))
    {
        pushProjectileAudioEvent(*audioRequest);
    }
    return true;
}

bool OutdoorWorldRuntime::projectileSourceIsFriendlyToActor(
    const ProjectileState &projectile,
    const MapActorState &actor) const
{
    GameplayProjectileService::ProjectileActorRelationFacts facts = {};
    facts.eventSource = projectile.sourceId == EventSpellSourceId;
    facts.targetHostileToParty = actor.hostileToParty;

    if (m_pGameplayActorService != nullptr)
    {
        facts.targetPartyControlled = m_pGameplayActorService->isPartyControlledActor(
            gameplayActorControlModeFromOutdoor(actor.controlMode));
        facts.sourceMonsterKnown = projectile.sourceMonsterId != 0;
        facts.sourceMonsterFriendlyToTarget = facts.sourceMonsterKnown
            && m_pGameplayActorService->monsterIdsAreFriendly(projectile.sourceMonsterId, actor.monsterId);
    }

    return projectileService().isProjectileSourceFriendlyToActor(projectile, facts);
}

int OutdoorWorldRuntime::resolveProjectilePartyImpactDamage(const ProjectileState &projectile) const
{
    const GameplayProjectileService::ProjectilePartyImpactDamageInput input =
        buildProjectilePartyImpactDamageInput(projectile, m_pMonsterTable, m_mapActors);
    return projectileService().resolveProjectilePartyImpactDamage(input);
}

GameplayProjectileService::ProjectileAreaImpactInput OutdoorWorldRuntime::buildProjectileAreaImpactInput(
    const ProjectileState &projectile,
    const bx::Vec3 &impactPoint,
    float impactRadius,
    float partyX,
    float partyY,
    float partyZ,
    bool canHitParty,
    size_t directActorIndex) const
{
    GameplayProjectileService::ProjectileAreaImpactInput input = {};
    input.impactX = impactPoint.x;
    input.impactY = impactPoint.y;
    input.impactZ = impactPoint.z;
    input.impactRadius = impactRadius;
    input.partyX = partyX;
    input.partyY = partyY;
    input.partyZ = partyZ;
    input.partyCollisionRadius = PartyCollisionRadius;
    input.partyCollisionHeight = PartyCollisionHeight;
    input.canHitParty = canHitParty;
    input.nonPartyProjectileDamage = resolveProjectilePartyImpactDamage(projectile);
    input.actors.reserve(m_mapActors.size());

    for (size_t actorIndex = 0; actorIndex < m_mapActors.size(); ++actorIndex)
    {
        const MapActorState &actor = m_mapActors[actorIndex];

        GameplayProjectileService::ProjectileAreaImpactActorFacts actorFacts = {};
        actorFacts.actorIndex = actorIndex;
        actorFacts.actorId = actor.actorId;
        actorFacts.x = actor.preciseX;
        actorFacts.y = actor.preciseY;
        actorFacts.z = actor.preciseZ;
        actorFacts.radius = actor.radius;
        actorFacts.height = actor.height;
        actorFacts.unavailableForCombat = isActorUnavailableForCombat(actor);
        actorFacts.friendlyToProjectileSource =
            projectile.sourceKind != ProjectileState::SourceKind::Party
            && projectileSourceIsFriendlyToActor(projectile, actor);
        actorFacts.directImpactActor = actorIndex == directActorIndex;
        input.actors.push_back(actorFacts);
    }

    return input;
}

int OutdoorWorldRuntime::resolvePartyProjectileDamageMultiplier(
    const ProjectileState &projectile,
    size_t actorIndex) const
{
    if (actorIndex >= m_mapActors.size()
        || m_pParty == nullptr
        || m_pMonsterTable == nullptr)
    {
        return 1;
    }

    const Character *pSourceMember = m_pParty->member(projectile.sourcePartyMemberIndex);
    const MonsterTable::MonsterStatsEntry *pStats =
        m_pMonsterTable->findStatsById(m_mapActors[actorIndex].monsterId);

    if (pSourceMember == nullptr || pStats == nullptr)
    {
        return 1;
    }

    return projectileService().resolvePartyProjectileDamageMultiplier(
        projectile,
        pSourceMember,
        m_pItemTable,
        m_pSpecialItemEnchantTable,
        pStats->name,
        pStats->pictureName);
}

GameplayProjectileService::ProjectileDirectActorImpactInput
OutdoorWorldRuntime::buildProjectileDirectActorImpactInput(
    const ProjectileState &projectile,
    size_t actorIndex) const
{
    GameplayProjectileService::ProjectileDirectActorImpactInput input = {};

    if (actorIndex >= m_mapActors.size())
    {
        return input;
    }

    const MapActorState &actor = m_mapActors[actorIndex];
    const float distanceToTarget = std::max(
        0.0f,
        length3d(
            actor.preciseX - projectile.sourceX,
            actor.preciseY - projectile.sourceY,
            actor.preciseZ - projectile.sourceZ)
            - static_cast<float>(actor.radius));

    input.actorIndex = actorIndex;
    input.actorId = actor.actorId;
    input.targetArmorClass = effectiveMapActorArmorClass(actorIndex);
    input.damageMultiplier = resolvePartyProjectileDamageMultiplier(projectile, actorIndex);
    input.targetDistance = distanceToTarget;
    input.nonPartyProjectileDamage = resolveProjectilePartyImpactDamage(projectile);
    return input;
}

void OutdoorWorldRuntime::buildOutdoorFaceSpatialIndex()
{
    m_outdoorFaceGridCells.clear();
    m_outdoorFaceVisitGenerations.clear();
    m_outdoorFaceVisitGenerationCounter = 1;
    m_outdoorFaceGridMinX = 0.0f;
    m_outdoorFaceGridMinY = 0.0f;
    m_outdoorFaceGridWidth = 0;
    m_outdoorFaceGridHeight = 0;

    if (m_outdoorFaces.empty())
    {
        return;
    }

    float minX = m_outdoorFaces.front().minX;
    float maxX = m_outdoorFaces.front().maxX;
    float minY = m_outdoorFaces.front().minY;
    float maxY = m_outdoorFaces.front().maxY;

    for (const OutdoorFaceGeometryData &face : m_outdoorFaces)
    {
        minX = std::min(minX, face.minX);
        maxX = std::max(maxX, face.maxX);
        minY = std::min(minY, face.minY);
        maxY = std::max(maxY, face.maxY);
    }

    m_outdoorFaceGridMinX = minX;
    m_outdoorFaceGridMinY = minY;
    m_outdoorFaceGridWidth = std::max<size_t>(
        1,
        static_cast<size_t>(std::floor((maxX - minX) / OutdoorFaceSpatialCellSize)) + 1);
    m_outdoorFaceGridHeight = std::max<size_t>(
        1,
        static_cast<size_t>(std::floor((maxY - minY) / OutdoorFaceSpatialCellSize)) + 1);
    m_outdoorFaceGridCells.assign(m_outdoorFaceGridWidth * m_outdoorFaceGridHeight, {});
    m_outdoorFaceVisitGenerations.assign(m_outdoorFaces.size(), 0);

    for (size_t faceIndex = 0; faceIndex < m_outdoorFaces.size(); ++faceIndex)
    {
        const OutdoorFaceGeometryData &face = m_outdoorFaces[faceIndex];
        const size_t minCellX = std::min(
            m_outdoorFaceGridWidth - 1,
            static_cast<size_t>(std::floor((face.minX - minX) / OutdoorFaceSpatialCellSize)));
        const size_t maxCellX = std::min(
            m_outdoorFaceGridWidth - 1,
            static_cast<size_t>(std::floor((face.maxX - minX) / OutdoorFaceSpatialCellSize)));
        const size_t minCellY = std::min(
            m_outdoorFaceGridHeight - 1,
            static_cast<size_t>(std::floor((face.minY - minY) / OutdoorFaceSpatialCellSize)));
        const size_t maxCellY = std::min(
            m_outdoorFaceGridHeight - 1,
            static_cast<size_t>(std::floor((face.maxY - minY) / OutdoorFaceSpatialCellSize)));

        for (size_t cellY = minCellY; cellY <= maxCellY; ++cellY)
        {
            for (size_t cellX = minCellX; cellX <= maxCellX; ++cellX)
            {
                m_outdoorFaceGridCells[cellY * m_outdoorFaceGridWidth + cellX].push_back(faceIndex);
            }
        }
    }
}

void OutdoorWorldRuntime::collectOutdoorFaceCandidates(
    float minX,
    float minY,
    float maxX,
    float maxY,
    std::vector<size_t> &indices) const
{
    indices.clear();

    if (m_outdoorFaceGridCells.empty() || m_outdoorFaceGridWidth == 0 || m_outdoorFaceGridHeight == 0)
    {
        indices.reserve(m_outdoorFaces.size());

        for (size_t faceIndex = 0; faceIndex < m_outdoorFaces.size(); ++faceIndex)
        {
            indices.push_back(faceIndex);
        }

        return;
    }

    const float clampedMinX = std::max(minX, m_outdoorFaceGridMinX);
    const float clampedMinY = std::max(minY, m_outdoorFaceGridMinY);
    const float clampedMaxX = std::max(maxX, m_outdoorFaceGridMinX);
    const float clampedMaxY = std::max(maxY, m_outdoorFaceGridMinY);
    const size_t minCellX = std::min(
        m_outdoorFaceGridWidth - 1,
        static_cast<size_t>(std::floor((clampedMinX - m_outdoorFaceGridMinX) / OutdoorFaceSpatialCellSize)));
    const size_t maxCellX = std::min(
        m_outdoorFaceGridWidth - 1,
        static_cast<size_t>(std::floor((clampedMaxX - m_outdoorFaceGridMinX) / OutdoorFaceSpatialCellSize)));
    const size_t minCellY = std::min(
        m_outdoorFaceGridHeight - 1,
        static_cast<size_t>(std::floor((clampedMinY - m_outdoorFaceGridMinY) / OutdoorFaceSpatialCellSize)));
    const size_t maxCellY = std::min(
        m_outdoorFaceGridHeight - 1,
        static_cast<size_t>(std::floor((clampedMaxY - m_outdoorFaceGridMinY) / OutdoorFaceSpatialCellSize)));

    if (m_outdoorFaceVisitGenerations.size() != m_outdoorFaces.size())
    {
        m_outdoorFaceVisitGenerations.assign(m_outdoorFaces.size(), 0);
        m_outdoorFaceVisitGenerationCounter = 1;
    }

    if (m_outdoorFaceVisitGenerationCounter == std::numeric_limits<uint32_t>::max())
    {
        std::fill(m_outdoorFaceVisitGenerations.begin(), m_outdoorFaceVisitGenerations.end(), 0);
        m_outdoorFaceVisitGenerationCounter = 1;
    }

    const uint32_t visitGeneration = m_outdoorFaceVisitGenerationCounter++;

    for (size_t cellY = minCellY; cellY <= maxCellY; ++cellY)
    {
        for (size_t cellX = minCellX; cellX <= maxCellX; ++cellX)
        {
            const std::vector<size_t> &cellFaces = m_outdoorFaceGridCells[cellY * m_outdoorFaceGridWidth + cellX];

            for (size_t faceIndex : cellFaces)
            {
                if (faceIndex >= m_outdoorFaceVisitGenerations.size()
                    || m_outdoorFaceVisitGenerations[faceIndex] == visitGeneration)
                {
                    continue;
                }

                m_outdoorFaceVisitGenerations[faceIndex] = visitGeneration;
                indices.push_back(faceIndex);
            }
        }
    }

}

const OutdoorFaceGeometryData *OutdoorWorldRuntime::outdoorFace(size_t faceIndex) const
{
    if (faceIndex >= m_outdoorFaces.size())
    {
        return nullptr;
    }

    return &m_outdoorFaces[faceIndex];
}

bool OutdoorWorldRuntime::hasClearOutdoorLineOfSight(const bx::Vec3 &start, const bx::Vec3 &end) const
{
    if (m_pOutdoorMapData != nullptr)
    {
        constexpr float TerrainLosSampleSpacing = static_cast<float>(OutdoorMapData::TerrainTileSize) * 0.5f;
        constexpr float TerrainLosHeightSlack = 12.0f;
        const float deltaX = end.x - start.x;
        const float deltaY = end.y - start.y;
        const float deltaZ = end.z - start.z;
        const float horizontalDistance = std::sqrt(deltaX * deltaX + deltaY * deltaY);

        if (horizontalDistance > TerrainLosSampleSpacing)
        {
            const int sampleCount = std::max(2, static_cast<int>(std::ceil(horizontalDistance / TerrainLosSampleSpacing)));

            for (int sampleIndex = 1; sampleIndex < sampleCount; ++sampleIndex)
            {
                const float factor = static_cast<float>(sampleIndex) / static_cast<float>(sampleCount);
                const float sampleX = start.x + deltaX * factor;
                const float sampleY = start.y + deltaY * factor;
                const float sampleZ = start.z + deltaZ * factor;
                const float terrainHeight = sampleOutdoorTerrainHeight(*m_pOutdoorMapData, sampleX, sampleY);

                if (terrainHeight >= sampleZ - TerrainLosHeightSlack)
                {
                    return false;
                }
            }
        }
    }

    if (m_outdoorFaces.empty())
    {
        return true;
    }

    constexpr float FaceCollisionPadding = 16.0f;
    constexpr float EdgeFactorEpsilon = 0.01f;
    std::vector<size_t> candidateFaceIndices;
    collectOutdoorFaceCandidates(
        std::min(start.x, end.x) - FaceCollisionPadding,
        std::min(start.y, end.y) - FaceCollisionPadding,
        std::max(start.x, end.x) + FaceCollisionPadding,
        std::max(start.y, end.y) + FaceCollisionPadding,
        candidateFaceIndices);

    for (size_t faceIndex : candidateFaceIndices)
    {
        if (faceIndex >= m_outdoorFaces.size())
        {
            continue;
        }

        const OutdoorFaceGeometryData &face = m_outdoorFaces[faceIndex];

        if (!face.hasPlane || face.isWalkable)
        {
            continue;
        }

        if (!segmentMayTouchFaceBounds(start, end, face, FaceCollisionPadding))
        {
            continue;
        }

        float factor = 0.0f;
        bx::Vec3 point = {0.0f, 0.0f, 0.0f};

        if (intersectOutdoorSegmentWithFace(face, start, end, factor, point)
            && factor > EdgeFactorEpsilon
            && factor < 1.0f - EdgeFactorEpsilon)
        {
            return false;
        }
    }

    return true;
}

float OutdoorWorldRuntime::sampleSupportFloorHeight(float x, float y, float z, float maxRise, float xySlack) const
{
    if (m_pOutdoorMapData == nullptr)
    {
        return z;
    }

    const float terrainHeight = sampleOutdoorTerrainHeight(*m_pOutdoorMapData, x, y);
    float bestHeight = terrainHeight;
    std::vector<size_t> candidateFaceIndices;
    collectOutdoorFaceCandidates(x - xySlack, y - xySlack, x + xySlack, y + xySlack, candidateFaceIndices);

    for (size_t faceIndex : candidateFaceIndices)
    {
        if (faceIndex >= m_outdoorFaces.size())
        {
            continue;
        }

        const OutdoorFaceGeometryData &geometry = m_outdoorFaces[faceIndex];

        if (!geometry.isWalkable
            || x < geometry.minX - xySlack
            || x > geometry.maxX + xySlack
            || y < geometry.minY - xySlack
            || y > geometry.maxY + xySlack
            || !isPointInsideOrNearOutdoorPolygon(x, y, geometry.vertices, xySlack))
        {
            continue;
        }

        const float faceHeight = calculateOutdoorFaceHeight(geometry, x, y);

        if (faceHeight < terrainHeight || faceHeight > z + maxRise)
        {
            continue;
        }

        if (faceHeight >= bestHeight)
        {
            bestHeight = faceHeight;
        }
    }

    return bestHeight;
}

OutdoorWorldRuntime::ProjectileCollisionFacts OutdoorWorldRuntime::buildProjectileCollisionFacts(
    const ProjectileState &projectile,
    const bx::Vec3 &segmentStart,
    const bx::Vec3 &segmentEnd,
    float partyX,
    float partyY,
    float partyZ) const
{
    ProjectileCollisionFacts best = {};
    best.point = segmentEnd;

    auto considerImpact = [&best](
        float factor,
        const bx::Vec3 &point,
        ProjectileCollisionKind kind,
        std::string colliderName,
        size_t actorIndex,
        size_t faceIndex)
    {
        if (factor < 0.0f || factor > 1.0f || factor >= best.factor)
        {
            return;
        }

        best.hit = true;
        best.factor = factor;
        best.point = point;
        best.kind = kind;
        best.colliderName = std::move(colliderName);
        best.actorIndex = actorIndex;
        best.faceIndex = faceIndex;
    };

    if (projectileService().canProjectileCollideWithParty(projectile))
    {
        float projectionFactor = 0.0f;
        const float distanceSquared = pointSegmentDistanceSquared2d(
            partyX,
            partyY,
            segmentStart.x,
            segmentStart.y,
            segmentEnd.x,
            segmentEnd.y,
            projectionFactor);
        const float collisionRadius =
            PartyCollisionRadius + static_cast<float>(std::max<uint16_t>(projectile.radius, 8));

        if (distanceSquared <= collisionRadius * collisionRadius)
        {
            const float collisionZ = segmentStart.z + (segmentEnd.z - segmentStart.z) * projectionFactor;
            const float partyMinZ = partyZ;
            const float partyMaxZ = partyZ + PartyCollisionHeight;

            if (collisionZ >= partyMinZ - static_cast<float>(projectile.height)
                && collisionZ <= partyMaxZ + static_cast<float>(projectile.height))
            {
                considerImpact(
                    projectionFactor,
                    {
                        segmentStart.x + (segmentEnd.x - segmentStart.x) * projectionFactor,
                        segmentStart.y + (segmentEnd.y - segmentStart.y) * projectionFactor,
                        collisionZ
                    },
                    ProjectileCollisionKind::Party,
                    "party",
                    static_cast<size_t>(-1),
                    static_cast<size_t>(-1));
            }
        }
    }

    for (size_t actorIndex = 0; actorIndex < m_mapActors.size(); ++actorIndex)
    {
        const MapActorState &actor = m_mapActors[actorIndex];

        GameplayProjectileService::ProjectileCollisionActorFacts actorFacts = {};
        actorFacts.actorId = actor.actorId;
        actorFacts.dead = actor.isDead;
        actorFacts.unavailableForCombat = isActorUnavailableForCombat(actor);
        actorFacts.friendlyToProjectileSource =
            projectile.sourceKind != ProjectileState::SourceKind::Party
            && projectileSourceIsFriendlyToActor(projectile, actor);

        if (!projectileService().canProjectileCollideWithActor(projectile, actorFacts))
        {
            continue;
        }

        float projectionFactor = 0.0f;
        const float distanceSquared = pointSegmentDistanceSquared2d(
            actor.preciseX,
            actor.preciseY,
            segmentStart.x,
            segmentStart.y,
            segmentEnd.x,
            segmentEnd.y,
            projectionFactor);
        const float collisionRadius =
            static_cast<float>(std::max<uint16_t>(actor.radius, 8))
            + static_cast<float>(std::max<uint16_t>(projectile.radius, 8));

        if (distanceSquared > collisionRadius * collisionRadius)
        {
            continue;
        }

        const float collisionZ = segmentStart.z + (segmentEnd.z - segmentStart.z) * projectionFactor;

        if (collisionZ < actor.preciseZ - static_cast<float>(projectile.height)
            || collisionZ > actor.preciseZ + static_cast<float>(actor.height) + static_cast<float>(projectile.height))
        {
            continue;
        }

        std::ostringstream colliderNameStream;
        colliderNameStream << actor.displayName << " #" << actor.actorId;
        considerImpact(
            projectionFactor,
            {
                segmentStart.x + (segmentEnd.x - segmentStart.x) * projectionFactor,
                segmentStart.y + (segmentEnd.y - segmentStart.y) * projectionFactor,
                collisionZ
            },
            ProjectileCollisionKind::Actor,
            colliderNameStream.str(),
            actorIndex,
            static_cast<size_t>(-1));
    }

    const float faceCollisionPadding =
        static_cast<float>(std::max<uint16_t>(projectile.radius, projectile.height)) + 16.0f;
    std::vector<size_t> candidateFaceIndices;
    collectOutdoorFaceCandidates(
        std::min(segmentStart.x, segmentEnd.x) - faceCollisionPadding,
        std::min(segmentStart.y, segmentEnd.y) - faceCollisionPadding,
        std::max(segmentStart.x, segmentEnd.x) + faceCollisionPadding,
        std::max(segmentStart.y, segmentEnd.y) + faceCollisionPadding,
        candidateFaceIndices);

    for (size_t faceIndex : candidateFaceIndices)
    {
        if (faceIndex >= m_outdoorFaces.size())
        {
            continue;
        }

        const OutdoorFaceGeometryData &face = m_outdoorFaces[faceIndex];

        if (!segmentMayTouchFaceBounds(segmentStart, segmentEnd, face, faceCollisionPadding))
        {
            continue;
        }

        float factor = 0.0f;
        bx::Vec3 point = {0.0f, 0.0f, 0.0f};

        if (intersectOutdoorSegmentWithFace(face, segmentStart, segmentEnd, factor, point))
        {
            std::ostringstream colliderNameStream;
            colliderNameStream << face.modelName << " face=" << face.faceIndex;
            considerImpact(
                factor,
                point,
                ProjectileCollisionKind::BModel,
                colliderNameStream.str(),
                static_cast<size_t>(-1),
                faceIndex);
        }
    }

    if (m_pOutdoorMapData != nullptr)
    {
        const float terrainZ = sampleOutdoorTerrainHeight(*m_pOutdoorMapData, segmentEnd.x, segmentEnd.y);

        if (segmentEnd.z <= terrainZ)
        {
            float factor = 1.0f;

            if (std::abs(segmentEnd.z - segmentStart.z) > 0.01f)
            {
                factor = std::clamp(
                    (terrainZ - segmentStart.z) / (segmentEnd.z - segmentStart.z),
                    0.0f,
                    1.0f);
            }

            considerImpact(
                factor,
                {
                    segmentStart.x + (segmentEnd.x - segmentStart.x) * factor,
                    segmentStart.y + (segmentEnd.y - segmentStart.y) * factor,
                    terrainZ
                },
                ProjectileCollisionKind::Terrain,
                "terrain",
                static_cast<size_t>(-1),
                static_cast<size_t>(-1));
        }
    }

    if (best.hit
        && best.kind == ProjectileCollisionKind::Terrain
        && m_pOutdoorMapData != nullptr)
    {
        best.waterTerrainImpact =
            isOutdoorTerrainWater(*m_pOutdoorMapData, best.point.x, best.point.y)
            || isOutdoorLandMaskWater(m_outdoorLandMask, best.point.x, best.point.y);
    }

    return best;
}

OutdoorWorldRuntime::ProjectileFrameWorldFacts OutdoorWorldRuntime::collectProjectileFrameFacts(
    const ProjectileState &projectile,
    float deltaSeconds,
    float partyX,
    float partyY,
    float partyZ) const
{
    ProjectileState predictedProjectile = projectile;
    const uint32_t deltaTicks = GameplayProjectileService::ticksFromDeltaSeconds(deltaSeconds);
    const bool lifetimeExpired = projectileService().advanceProjectileLifetime(predictedProjectile, deltaTicks);

    ProjectileFrameWorldFacts worldFacts = {};
    worldFacts.frame.deltaSeconds = deltaSeconds;
    worldFacts.frame.gravity = WorldItemGravity;
    worldFacts.frame.bounceFactor = WorldItemBounceFactor;
    worldFacts.frame.bounceStopVelocity = WorldItemBounceStopVelocity;
    worldFacts.frame.groundDamping = WorldItemGroundDamping;
    worldFacts.frame.partyPosition = {partyX, partyY, partyZ};
    worldFacts.frame.partyCollisionRadius = PartyCollisionRadius;
    worldFacts.frame.partyCollisionHeight = PartyCollisionHeight;
    worldFacts.frame.canHitParty = true;
    worldFacts.frame.nonPartyProjectileDamage = resolveProjectilePartyImpactDamage(projectile);

    size_t directActorIndex = static_cast<size_t>(-1);
    bx::Vec3 areaImpactPoint = {projectile.x, projectile.y, projectile.z};

    if (!lifetimeExpired)
    {
        worldFacts.frame.motion =
            projectileService().advanceProjectileMotion(predictedProjectile, deltaSeconds, WorldItemGravity);
        const bx::Vec3 segmentStart = {
            worldFacts.frame.motion.startX,
            worldFacts.frame.motion.startY,
            worldFacts.frame.motion.startZ
        };
        const bx::Vec3 segmentEnd = {
            worldFacts.frame.motion.endX,
            worldFacts.frame.motion.endY,
            worldFacts.frame.motion.endZ
        };

        areaImpactPoint = segmentEnd;
        worldFacts.collision =
            buildProjectileCollisionFacts(projectile, segmentStart, segmentEnd, partyX, partyY, partyZ);

        if (worldFacts.collision.hit)
        {
            areaImpactPoint = worldFacts.collision.point;
            directActorIndex = worldFacts.collision.kind == ProjectileCollisionKind::Actor
                ? worldFacts.collision.actorIndex
                : static_cast<size_t>(-1);

            worldFacts.frame.hasCollision = true;
            worldFacts.frame.collision.point = {
                worldFacts.collision.point.x,
                worldFacts.collision.point.y,
                worldFacts.collision.point.z
            };
            worldFacts.frame.collision.colliderName = worldFacts.collision.colliderName;
            worldFacts.frame.collision.actorIndex = worldFacts.collision.actorIndex;
            worldFacts.frame.collision.bounceSurface = buildProjectileBounceSurfaceFacts(worldFacts.collision);
            worldFacts.frame.collision.waterTerrainImpact = worldFacts.collision.waterTerrainImpact;

            switch (worldFacts.collision.kind)
            {
                case ProjectileCollisionKind::Party:
                    worldFacts.frame.collision.kind =
                        GameplayProjectileService::ProjectileFrameCollisionKind::Party;
                    break;

                case ProjectileCollisionKind::Actor:
                {
                    worldFacts.frame.collision.kind =
                        GameplayProjectileService::ProjectileFrameCollisionKind::Actor;

                    const GameplayProjectileService::ProjectileDirectActorImpactInput directInput =
                        buildProjectileDirectActorImpactInput(projectile, worldFacts.collision.actorIndex);
                    worldFacts.frame.collision.actorId = directInput.actorId;
                    worldFacts.frame.collision.targetArmorClass = directInput.targetArmorClass;
                    worldFacts.frame.collision.damageMultiplier = directInput.damageMultiplier;
                    worldFacts.frame.collision.targetDistance = directInput.targetDistance;
                    break;
                }

                case ProjectileCollisionKind::BModel:
                case ProjectileCollisionKind::Terrain:
                    worldFacts.frame.collision.kind =
                        GameplayProjectileService::ProjectileFrameCollisionKind::World;
                    break;

                case ProjectileCollisionKind::None:
                default:
                    worldFacts.frame.collision.kind =
                        GameplayProjectileService::ProjectileFrameCollisionKind::None;
                    break;
            }
        }
    }

    const GameplayProjectileService::ProjectileAreaImpactInput areaInput =
        buildProjectileAreaImpactInput(
            projectile,
            areaImpactPoint,
            0.0f,
            partyX,
            partyY,
            partyZ,
            true,
            directActorIndex);
    worldFacts.frame.areaActors = areaInput.actors;

    return worldFacts;
}

GameplayProjectileService::ProjectileBounceSurfaceFacts OutdoorWorldRuntime::buildProjectileBounceSurfaceFacts(
    const ProjectileCollisionFacts &collision) const
{
    GameplayProjectileService::ProjectileBounceSurfaceFacts facts = {};

    if (!collision.hit)
    {
        return facts;
    }

    if (collision.kind == ProjectileCollisionKind::Terrain && !collision.waterTerrainImpact)
    {
        bx::Vec3 surfaceNormal = {0.0f, 0.0f, 1.0f};
        if (m_pOutdoorMapData != nullptr)
        {
            surfaceNormal = approximateOutdoorTerrainNormal(*m_pOutdoorMapData, collision.point.x, collision.point.y);
        }

        facts.canBounce = true;
        facts.requiresDownwardVelocity = true;
        facts.normalX = surfaceNormal.x;
        facts.normalY = surfaceNormal.y;
        facts.normalZ = surfaceNormal.z;
        return facts;
    }

    if (collision.kind != ProjectileCollisionKind::BModel || collision.faceIndex >= m_outdoorFaces.size())
    {
        return facts;
    }

    const OutdoorFaceGeometryData &face = m_outdoorFaces[collision.faceIndex];

    if (!face.hasPlane
        || face.normal.z <= 0.35f
        || (!face.isWalkable && face.normal.z <= 0.6f))
    {
        return facts;
    }

    facts.canBounce = true;
    facts.normalX = face.normal.x;
    facts.normalY = face.normal.y;
    facts.normalZ = face.normal.z;
    return facts;
}

void OutdoorWorldRuntime::applyProjectileFrameResult(
    ProjectileState &projectile,
    const ProjectileCollisionFacts &collision,
    const GameplayProjectileService::ProjectileFrameResult &frameResult)
{
    if (frameResult.deathBlossomFalloutPoint)
    {
        spawnDeathBlossomFalloutProjectiles(
            projectile,
            frameResult.deathBlossomFalloutPoint->x,
            frameResult.deathBlossomFalloutPoint->y,
            frameResult.deathBlossomFalloutPoint->z);
    }

    if (frameResult.directPartyDamage)
    {
        if (m_pGameplayCombatController != nullptr)
        {
            m_pGameplayCombatController->recordPartyProjectileImpact(
                projectile.sourceId,
                *frameResult.directPartyDamage,
                projectile.spellId,
                false);
        }
    }

    if (frameResult.directActorImpact && frameResult.directActorImpact->actorIndex < m_mapActors.size())
    {
        const GameplayProjectileService::ProjectileDirectActorImpact &impact =
            *frameResult.directActorImpact;

        bool killed = false;
        if (impact.applyPartyProjectileDamage)
        {
            const int beforeHp = m_mapActors[impact.actorIndex].currentHp;
            applyPartyAttackToMapActor(
                impact.actorIndex,
                impact.damage,
                projectile.sourceX,
                projectile.sourceY,
                projectile.sourceZ);
            const OutdoorWorldRuntime::MapActorState &afterActor = m_mapActors[impact.actorIndex];
            killed = beforeHp > 0 && afterActor.currentHp <= 0;
        }

        if (impact.queuePartyProjectileActorEvent)
        {
            if (m_pGameplayCombatController != nullptr)
            {
                m_pGameplayCombatController->recordPartyProjectileActorImpact(
                    projectile.sourceId,
                    projectile.sourcePartyMemberIndex,
                    impact.actorId,
                    impact.damage,
                    projectile.spellId,
                    impact.hit,
                    killed);
            }
        }
        else if (impact.applyNonPartyProjectileDamage)
        {
            applyMonsterAttackToMapActor(
                impact.actorIndex,
                impact.damage,
                projectile.sourceId);
        }
    }

    if (frameResult.areaImpact)
    {
        const GameplayProjectileService::ProjectileFrameAreaImpactResult &areaImpact = *frameResult.areaImpact;

        if (areaImpact.impact.hitParty)
        {
            if (m_pGameplayCombatController != nullptr)
            {
                m_pGameplayCombatController->recordPartyProjectileImpact(
                    projectile.sourceId,
                    areaImpact.impact.partyDamage,
                    projectile.spellId,
                    true);
            }

            if (areaImpact.logHits)
            {
                const bx::Vec3 impactPoint = {areaImpact.point.x, areaImpact.point.y, areaImpact.point.z};
                logProjectileAoeHit(projectile, "party", impactPoint, areaImpact.radius);
            }
        }

        for (const GameplayProjectileService::ProjectileAreaImpactActorHit &actorHit :
             areaImpact.impact.actorHits)
        {
            if (actorHit.actorIndex >= m_mapActors.size())
            {
                continue;
            }

            bool killed = false;
            if (projectile.sourceKind == ProjectileState::SourceKind::Party)
            {
                const int beforeHp = m_mapActors[actorHit.actorIndex].currentHp;
                applyPartyAttackToMapActor(
                    actorHit.actorIndex,
                    actorHit.damage,
                    projectile.sourceX,
                    projectile.sourceY,
                    projectile.sourceZ);
                killed = beforeHp > 0 && m_mapActors[actorHit.actorIndex].currentHp <= 0;

                if (m_pGameplayCombatController != nullptr)
                {
                    m_pGameplayCombatController->recordPartyProjectileActorImpact(
                        projectile.sourceId,
                        projectile.sourcePartyMemberIndex,
                        m_mapActors[actorHit.actorIndex].actorId,
                        actorHit.damage,
                        projectile.spellId,
                        true,
                        killed);
                }
            }
            else
            {
                applyMonsterAttackToMapActor(actorHit.actorIndex, actorHit.damage, projectile.sourceId);
            }

            if (areaImpact.logHits)
            {
                const bx::Vec3 impactPoint = {areaImpact.point.x, areaImpact.point.y, areaImpact.point.z};
                logProjectileAoeHit(projectile, "actor", impactPoint, areaImpact.radius);
            }
        }
    }

    if (frameResult.logCollision)
    {
        logProjectileCollision(
            projectile,
            projectileCollisionKindName(collision.kind),
            collision.colliderName,
            collision.point);
    }

    if (frameResult.fxRequest)
    {
        switch (frameResult.fxRequest->kind)
        {
            case GameplayProjectileService::ProjectileFrameFxKind::WaterSplash:
                spawnWaterSplashImpact(
                    frameResult.fxRequest->point.x,
                    frameResult.fxRequest->point.y,
                    frameResult.fxRequest->point.z);
                break;

            case GameplayProjectileService::ProjectileFrameFxKind::ProjectileImpact:
                spawnProjectileImpact(
                    projectile,
                    frameResult.fxRequest->point.x,
                    frameResult.fxRequest->point.y,
                    frameResult.fxRequest->point.z,
                    frameResult.fxRequest->centerVertically);
                break;
        }
    }

    if (frameResult.audioRequest)
    {
        pushProjectileAudioEvent(*frameResult.audioRequest);
    }

    for (const GameplayProjectileService::ProjectileSpawnRequest &spawnRequest : frameResult.spawnedProjectiles)
    {
        projectileService().spawnProjectile(spawnRequest);
    }

    if (frameResult.logLifetimeExpiry)
    {
        logProjectileLifetimeExpiry(projectile);
    }

    if (frameResult.bounce)
    {
        projectileService().applyProjectileBounce(
            projectile,
            frameResult.bounce->point.x,
            frameResult.bounce->point.y,
            frameResult.bounce->point.z,
            frameResult.bounce->normalX,
            frameResult.bounce->normalY,
            frameResult.bounce->normalZ,
            frameResult.bounce->bounceFactor,
            frameResult.bounce->stopVelocity,
            frameResult.bounce->groundDamping);
    }

    if (frameResult.applyMotionEnd)
    {
        projectileService().applyProjectileMotionEnd(projectile, frameResult.motion);
    }

    if (frameResult.expireProjectile)
    {
        projectileService().expireProjectile(projectile);
    }
}

bool OutdoorWorldRuntime::applyProjectileSpawnEffects(
    const GameplayProjectileService::ProjectileSpawnResult &spawnResult,
    const GameplayProjectileService::ProjectileSpawnEffects &effects,
    const std::string &spawnKindName,
    const std::string &instantColliderName)
{
    if (!effects.accepted)
    {
        return false;
    }

    if (effects.spawnInstantImpact)
    {
        logProjectileCollision(
            spawnResult.projectile,
            "instant",
            instantColliderName,
            {effects.impactX, effects.impactY, effects.impactZ});
        spawnProjectileImpact(
            spawnResult.projectile,
            effects.impactX,
            effects.impactY,
            effects.impactZ);
    }

    if (effects.playReleaseAudio && effects.releaseAudioRequest)
    {
        pushProjectileAudioEvent(*effects.releaseAudioRequest);
    }

    if (effects.logSpawn)
    {
        logProjectileSpawn(
            spawnKindName.c_str(),
            spawnResult.projectile,
            spawnResult.directionX,
            spawnResult.directionY,
            spawnResult.directionZ,
            spawnResult.speed);
    }

    return true;
}

const char *OutdoorWorldRuntime::projectileCollisionKindName(ProjectileCollisionKind kind)
{
    switch (kind)
    {
        case ProjectileCollisionKind::Party:
            return "party";
        case ProjectileCollisionKind::Actor:
            return "actor";
        case ProjectileCollisionKind::BModel:
            return "bmodel";
        case ProjectileCollisionKind::Terrain:
            return "terrain";
        case ProjectileCollisionKind::None:
        default:
            return "unknown";
    }
}

void OutdoorWorldRuntime::updateProjectiles(float deltaSeconds, float partyX, float partyY, float partyZ)
{
    if (deltaSeconds <= 0.0f)
    {
        return;
    }

    for (ProjectileState &projectile : projectileService().projectiles())
    {
        if (projectile.isExpired)
        {
            continue;
        }

        const ProjectileFrameWorldFacts worldFacts =
            collectProjectileFrameFacts(projectile, deltaSeconds, partyX, partyY, partyZ);
        const GameplayProjectileService::ProjectileFrameResult frameResult =
            projectileService().updateProjectileFrame(projectile, worldFacts.frame);
        applyProjectileFrameResult(projectile, worldFacts.collision, frameResult);
    }

    projectileService().eraseExpiredProjectiles();
}

void OutdoorWorldRuntime::applyEventRuntimeState()
{
    if (!m_eventRuntimeState)
    {
        return;
    }

    for (auto &[actorId, setMask] : m_eventRuntimeState->actorSetMasks)
    {
        if (actorId < m_mapActors.size() && (setMask & ActorInvisibleBit) != 0)
        {
            m_mapActors[actorId].isInvisible = true;
        }

        if (actorId < m_mapActors.size()
            && (setMask & static_cast<uint32_t>(EvtActorAttribute::HasItem)) != 0)
        {
            m_mapActors[actorId].specialItemId =
                m_eventRuntimeState->actorItemOverrides.contains(actorId)
                    ? m_eventRuntimeState->actorItemOverrides.at(actorId)
                    : 0;
        }
    }

    for (auto &[actorId, clearMask] : m_eventRuntimeState->actorClearMasks)
    {
        if (actorId < m_mapActors.size() && (clearMask & ActorInvisibleBit) != 0)
        {
            m_mapActors[actorId].isInvisible = false;
        }

        if (actorId < m_mapActors.size()
            && (clearMask & static_cast<uint32_t>(EvtActorAttribute::HasItem)) != 0)
        {
            m_mapActors[actorId].specialItemId = 0;
        }
    }

    for (auto &[actorId, groupId] : m_eventRuntimeState->actorIdGroupOverrides)
    {
        if (actorId < m_mapActors.size())
        {
            m_mapActors[actorId].group = groupId;
        }
    }

    for (auto &[groupId, setMask] : m_eventRuntimeState->actorGroupSetMasks)
    {
        if ((setMask & ActorInvisibleBit) == 0)
        {
            continue;
        }

        for (MapActorState &actor : m_mapActors)
        {
            if (actor.group == groupId)
            {
                actor.isInvisible = true;
            }
        }

    }

    for (auto &[groupId, clearMask] : m_eventRuntimeState->actorGroupClearMasks)
    {
        if ((clearMask & ActorInvisibleBit) == 0)
        {
            continue;
        }

        for (MapActorState &actor : m_mapActors)
        {
            if (actor.group == groupId)
            {
                actor.isInvisible = false;
            }
        }

    }

    for (auto &[fromGroupId, toGroupId] : m_eventRuntimeState->actorGroupOverrides)
    {
        for (MapActorState &actor : m_mapActors)
        {
            if (actor.group == fromGroupId)
            {
                actor.group = toGroupId;
            }
        }
    }

    for (auto &[groupId, allyId] : m_eventRuntimeState->actorGroupAllyOverrides)
    {
        for (MapActorState &actor : m_mapActors)
        {
            if (actor.group == groupId)
            {
                actor.ally = allyId;
            }
        }
    }

    for (auto &[chestId, setMask] : m_eventRuntimeState->chestSetMasks)
    {
        if (chestId >= m_chests.size())
        {
            continue;
        }

        m_chests[chestId].flags |= static_cast<uint16_t>(setMask);

        if (chestId < m_materializedChestViews.size() && m_materializedChestViews[chestId].has_value())
        {
            m_materializedChestViews[chestId]->flags = m_chests[chestId].flags;
        }

        if (m_activeChestView && m_activeChestView->chestId == chestId)
        {
            m_activeChestView->flags = m_chests[chestId].flags;
        }
    }

    for (auto &[chestId, clearMask] : m_eventRuntimeState->chestClearMasks)
    {
        if (chestId >= m_chests.size())
        {
            continue;
        }

        m_chests[chestId].flags &= ~static_cast<uint16_t>(clearMask);

        if (chestId < m_materializedChestViews.size() && m_materializedChestViews[chestId].has_value())
        {
            m_materializedChestViews[chestId]->flags = m_chests[chestId].flags;
        }

        if (m_activeChestView && m_activeChestView->chestId == chestId)
        {
            m_activeChestView->flags = m_chests[chestId].flags;
        }
    }

    for (uint32_t chestId : m_eventRuntimeState->openedChestIds)
    {
        if (chestId < m_openedChests.size())
        {
            m_openedChests[chestId] = true;
            activateChestView(chestId);
        }
    }
}

bool OutdoorWorldRuntime::updateTimers(
    float deltaSeconds,
    const EventRuntime &eventRuntime,
    const std::optional<ScriptedEventProgram> &localEventProgram,
    const std::optional<ScriptedEventProgram> &globalEventProgram
)
{
    if (!m_eventRuntimeState || deltaSeconds <= 0.0f)
    {
        return false;
    }

    const float deltaGameMinutes = deltaSeconds * GameMinutesPerRealSecond;
    advanceGameMinutesInternal(deltaGameMinutes);
    refreshAtmosphereState();

    if (m_timers.empty())
    {
        appendTimersFromProgram(localEventProgram, m_timers);
        appendTimersFromProgram(globalEventProgram, m_timers);
    }

    if (m_timers.empty())
    {
        return false;
    }

    bool executedAny = false;

    for (TimerState &timer : m_timers)
    {
        if (timer.hasFired && !timer.repeating)
        {
            continue;
        }

        timer.remainingGameMinutes -= deltaGameMinutes;

        if (timer.remainingGameMinutes > 0.0f)
        {
            continue;
        }

        if (eventRuntime.executeEventById(
                localEventProgram,
                globalEventProgram,
                timer.eventId,
                *m_eventRuntimeState,
                nullptr,
                this))
        {
            executedAny = true;
            applyEventRuntimeState();
        }

        if (timer.repeating)
        {
            timer.remainingGameMinutes += std::max(0.5f, timer.intervalGameMinutes);
        }
        else
        {
            timer.hasFired = true;
        }
    }

    return executedAny;
}

bool OutdoorWorldRuntime::isChestOpened(uint32_t chestId) const
{
    return chestId < m_openedChests.size() ? m_openedChests[chestId] : false;
}

size_t OutdoorWorldRuntime::mapActorCount() const
{
    return m_mapActors.size();
}

bool OutdoorWorldRuntime::actorRuntimeState(size_t actorIndex, GameplayRuntimeActorState &state) const
{
    const MapActorState *pActor = mapActorState(actorIndex);

    if (pActor == nullptr)
    {
        return false;
    }

    state.preciseX = pActor->preciseX;
    state.preciseY = pActor->preciseY;
    state.preciseZ = pActor->preciseZ;
    state.radius = pActor->radius;
    state.height = pActor->height;
    state.isDead = pActor->isDead;
    state.isInvisible = pActor->isInvisible;
    state.hostileToParty = pActor->hostileToParty;
    state.hasDetectedParty = pActor->hasDetectedParty;
    return true;
}

bool OutdoorWorldRuntime::actorInspectState(
    size_t actorIndex,
    uint32_t animationTicks,
    GameplayActorInspectState &state) const
{
    const MapActorState *pActor = mapActorState(actorIndex);

    if (pActor == nullptr)
    {
        return false;
    }

    state = {};
    state.displayName = pActor->displayName;
    state.monsterId = pActor->monsterId;
    state.currentHp = pActor->currentHp;
    state.maxHp = pActor->maxHp;
    state.armorClass = effectiveMapActorArmorClass(actorIndex);
    state.isDead = pActor->isDead;
    state.slowRemainingSeconds = pActor->slowRemainingSeconds;
    state.stunRemainingSeconds = pActor->stunRemainingSeconds;
    state.paralyzeRemainingSeconds = pActor->paralyzeRemainingSeconds;
    state.fearRemainingSeconds = pActor->fearRemainingSeconds;
    state.shrinkRemainingSeconds = pActor->shrinkRemainingSeconds;
    state.darkGraspRemainingSeconds = pActor->darkGraspRemainingSeconds;

    switch (pActor->controlMode)
    {
        case ActorControlMode::Charm:
            state.controlMode = GameplayActorControlMode::Charm;
            break;
        case ActorControlMode::Berserk:
            state.controlMode = GameplayActorControlMode::Berserk;
            break;
        case ActorControlMode::Enslaved:
            state.controlMode = GameplayActorControlMode::Enslaved;
            break;
        case ActorControlMode::ControlUndead:
            state.controlMode = GameplayActorControlMode::ControlUndead;
            break;
        case ActorControlMode::Reanimated:
            state.controlMode = GameplayActorControlMode::Reanimated;
            break;
        case ActorControlMode::None:
            state.controlMode = GameplayActorControlMode::None;
            break;
    }

    if (m_pActorSpriteFrameTable == nullptr)
    {
        return true;
    }

    uint16_t spriteFrameIndex = pActor->spriteFrameIndex;
    const size_t walkingAnimationIndex = static_cast<size_t>(ActorAnimation::Walking);

    if (walkingAnimationIndex < pActor->actionSpriteFrameIndices.size()
        && pActor->actionSpriteFrameIndices[walkingAnimationIndex] != 0)
    {
        spriteFrameIndex = pActor->actionSpriteFrameIndices[walkingAnimationIndex];
    }

    const SpriteFrameEntry *pFrame = m_pActorSpriteFrameTable->getFrame(spriteFrameIndex, animationTicks);

    if (pFrame == nullptr)
    {
        pFrame = m_pActorSpriteFrameTable->getFrame(spriteFrameIndex, 0);
    }

    if (pFrame == nullptr)
    {
        return true;
    }

    static constexpr int PreviewFacingOctant = 0;
    const ResolvedSpriteTexture resolvedTexture = SpriteFrameTable::resolveTexture(*pFrame, PreviewFacingOctant);
    state.previewTextureName = resolvedTexture.textureName;
    state.previewPaletteId = pFrame->paletteId;
    return true;
}

std::optional<GameplayCombatActorInfo> OutdoorWorldRuntime::combatActorInfoById(uint32_t actorId) const
{
    if (m_pMonsterTable == nullptr)
    {
        return std::nullopt;
    }

    for (const MapActorState &actor : m_mapActors)
    {
        if (actor.actorId != actorId)
        {
            continue;
        }

        GameplayCombatActorInfo info = {};
        info.actorId = actor.actorId;
        info.monsterId = actor.monsterId;
        info.maxHp = actor.maxHp;
        info.displayName = actor.displayName;

        if (const MonsterTable::MonsterStatsEntry *pStats = m_pMonsterTable->findStatsById(actor.monsterId))
        {
            info.attackPreferences = pStats->attackPreferences;
        }

        return info;
    }

    return std::nullopt;
}

const OutdoorWorldRuntime::MapActorState *OutdoorWorldRuntime::mapActorState(size_t actorIndex) const
{
    if (actorIndex >= m_mapActors.size())
    {
        return nullptr;
    }

    return &m_mapActors[actorIndex];
}

std::optional<GameplayWorldPoint> OutdoorWorldRuntime::partyAttackFallbackProjectionPoint(
    size_t actorIndex) const
{
    const MapActorState *pActor = mapActorState(actorIndex);

    if (pActor == nullptr)
    {
        return std::nullopt;
    }

    return GameplayWorldPoint{
        .x = pActor->preciseX,
        .y = pActor->preciseY,
        .z = pActor->preciseZ + std::max(48.0f, static_cast<float>(pActor->height) * 0.6f),
    };
}

std::optional<GameplayPartyAttackActorFacts> OutdoorWorldRuntime::partyAttackActorFacts(
    size_t actorIndex,
    bool visibleForFallback) const
{
    const MapActorState *pActor = mapActorState(actorIndex);

    if (pActor == nullptr)
    {
        return std::nullopt;
    }

    return GameplayPartyAttackActorFacts{
        .actorIndex = actorIndex,
        .monsterId = pActor->monsterId,
        .displayName = pActor->displayName,
        .position =
            GameplayWorldPoint{
                .x = pActor->preciseX,
                .y = pActor->preciseY,
                .z = pActor->preciseZ,
            },
        .radius = pActor->radius,
        .height = pActor->height,
        .currentHp = pActor->currentHp,
        .maxHp = pActor->maxHp,
        .effectiveArmorClass = effectiveMapActorArmorClass(actorIndex),
        .isDead = pActor->isDead,
        .isInvisible = pActor->isInvisible,
        .hostileToParty = pActor->hostileToParty,
        .visibleForFallback = visibleForFallback,
    };
}

std::vector<GameplayPartyAttackActorFacts> OutdoorWorldRuntime::collectPartyAttackFallbackActors(
    const GameplayPartyAttackFallbackQuery &query) const
{
    std::vector<GameplayPartyAttackActorFacts> actors;
    float viewProjectionMatrix[16] = {};
    bx::mtxMul(viewProjectionMatrix, query.viewMatrix.data(), query.projectionMatrix.data());

    for (size_t actorIndex = 0; actorIndex < mapActorCount(); ++actorIndex)
    {
        const std::optional<GameplayWorldPoint> projectionPoint = partyAttackFallbackProjectionPoint(actorIndex);

        if (!projectionPoint)
        {
            continue;
        }

        const bx::Vec3 projected = bx::mulH(
            {
                projectionPoint->x,
                projectionPoint->y,
                projectionPoint->z,
            },
            viewProjectionMatrix);
        const bool visibleForFallback =
            projected.z >= 0.0f
            && projected.z <= 1.0f
            && projected.x >= -1.0f
            && projected.x <= 1.0f
            && projected.y >= -1.0f
            && projected.y <= 1.0f;
        std::optional<GameplayPartyAttackActorFacts> facts = partyAttackActorFacts(actorIndex, visibleForFallback);

        if (facts)
        {
            actors.push_back(*facts);
        }
    }

    return actors;
}

std::optional<OutdoorWorldRuntime::ActorDecisionDebugInfo> OutdoorWorldRuntime::debugActorDecisionInfo(
    size_t actorIndex,
    float partyX,
    float partyY,
    float partyZ
) const
{
    if (actorIndex >= m_mapActors.size() || m_pMonsterTable == nullptr)
    {
        return std::nullopt;
    }

    const MapActorState &actor = m_mapActors[actorIndex];
    const MonsterTable::MonsterStatsEntry *pStats = m_pMonsterTable->findStatsById(actor.monsterId);

    if (pStats == nullptr)
    {
        return std::nullopt;
    }

    ActorDecisionDebugInfo info = {};
    info.actorIndex = actorIndex;
    info.monsterId = actor.monsterId;
    info.hostilityType = actor.hostilityType;
    info.hostileToParty = actor.hostileToParty;
    info.hasDetectedParty = actor.hasDetectedParty;
    info.aiState = actor.aiState;
    info.animation = actor.animation;
    info.idleDecisionSeconds = actor.idleDecisionSeconds;
    info.actionSeconds = actor.actionSeconds;
    info.attackCooldownSeconds = actor.attackCooldownSeconds;
    info.idleDecisionCount = actor.idleDecisionCount;
    info.pursueDecisionCount = actor.pursueDecisionCount;
    info.attackDecisionCount = actor.attackDecisionCount;
    info.monsterAiType = static_cast<int>(pStats->aiType);
    info.movementAllowed = pStats->movementType != MonsterTable::MonsterMovementType::Stationary;

    const GameplayActorTargetPolicyState actorTargetPolicyState = buildGameplayActorTargetPolicyState(actor);
    const float partySenseRange =
        m_pGameplayActorService != nullptr
        ? m_pGameplayActorService->partyEngagementRange(actorTargetPolicyState)
        : 0.0f;
    const float deltaPartyX = partyX - actor.preciseX;
    const float deltaPartyY = partyY - actor.preciseY;
    const float distanceToParty = length2d(deltaPartyX, deltaPartyY);
    const auto hasClearOutdoorLineOfSight =
        [this](size_t, size_t, const bx::Vec3 &start, const bx::Vec3 &end) -> bool
    {
        return this->hasClearOutdoorLineOfSight(start, end);
    };
    std::vector<OutdoorCombatTargetCandidate> combatCandidates =
        buildCombatTargetCandidates(
            m_pGameplayActorService,
            actor,
            actorIndex,
            m_mapActors);
    const OutdoorTargetFacts combatTarget =
        resolveOutdoorTargetFacts(
            m_pGameplayActorService,
            actor,
            actorIndex,
            combatCandidates,
            partyX,
            partyY,
            partyZ,
            hasClearOutdoorLineOfSight);
    const bool targetIsParty = combatTarget.kind == OutdoorTargetKind::Party;
    const bool targetIsActor = combatTarget.kind == OutdoorTargetKind::Actor;
    GameplayActorService fallbackActorService = {};
    const GameplayActorService *pActorService = m_pGameplayActorService;

    if (pActorService == nullptr)
    {
        pActorService = &fallbackActorService;
    }

    const bool partyIsVeryNearActor =
        pActorService->partyIsVeryNearActor(
            distanceToParty,
            partyZ - actor.preciseZ,
            actor.radius,
            actor.height,
            PartyCollisionRadius);
    const OutdoorEngagementState engagement =
        resolveOutdoorEngagementState(
            *pActorService,
            actorTargetPolicyState,
            combatTarget,
            gameplayActorAiTypeFromMonster(pStats->aiType),
            actor.hostilityType,
            actor.currentHp,
            actor.maxHp,
            actor.hostileToParty,
            partyIsVeryNearActor);

    info.partySenseRange = partySenseRange;
    info.distanceToParty = distanceToParty;
    info.canSenseParty = combatTarget.partyCanSense;
    info.targetKind = targetIsParty
        ? DebugTargetKind::Party
        : targetIsActor ? DebugTargetKind::Actor : DebugTargetKind::None;
    info.targetActorIndex = combatTarget.actorIndex;
    info.relationToTarget = combatTarget.relationToTarget;
    info.targetDistance = combatTarget.distanceToTarget;
    info.targetEdgeDistance = combatTarget.edgeDistance;
    info.targetCanSense = combatTarget.canSense;

    if (targetIsActor && combatTarget.actorIndex < m_mapActors.size())
    {
        info.targetMonsterId = m_mapActors[combatTarget.actorIndex].monsterId;
    }

    const bool attacking = actor.aiState == ActorAiState::Attacking;
    const bool attackInProgress = attacking && actor.actionSeconds > 0.0f;
    const bool attackJustCompleted = attacking && !attackInProgress && !actor.attackImpactTriggered;

    info.promotionRange = engagement.promotionRange;
    info.shouldPromoteHostility = engagement.shouldPromoteHostility;
    info.shouldEngageTarget = engagement.shouldEngageTarget;
    info.shouldFlee = engagement.shouldFlee;
    info.inMeleeRange = engagement.inMeleeRange;
    info.attackJustCompleted = attackJustCompleted;
    info.attackInProgress = attackInProgress;
    info.friendlyNearParty = engagement.friendlyNearParty;
    return info;
}

bool OutdoorWorldRuntime::debugSpawnMapActorProjectile(
    size_t actorIndex,
    MonsterAttackAbility ability,
    float targetX,
    float targetY,
    float targetZ)
{
    if (actorIndex >= m_mapActors.size())
    {
        return false;
    }

    const MapActorState &actor = m_mapActors[actorIndex];

    if (m_pMonsterTable == nullptr)
    {
        return false;
    }

    const MonsterTable::MonsterStatsEntry *pStats = m_pMonsterTable->findStatsById(actor.monsterId);

    if (pStats == nullptr)
    {
        return false;
    }

    return spawnProjectileFromMapActor(actor, *pStats, ability, targetX, targetY, targetZ);
}

bool OutdoorWorldRuntime::debugSpawnEncounterFromSpawnPoint(size_t spawnIndex, uint32_t countOverride)
{
    if (spawnIndex >= m_spawnPoints.size())
    {
        return false;
    }

    const SpawnPointState &spawn = m_spawnPoints[spawnIndex];
    const uint32_t resolvedCount = resolveEncounterSpawnCount(
        m_map,
        spawn.encounterSlot,
        countOverride,
        m_sessionChestSeed,
        static_cast<uint32_t>(spawnIndex));

    return spawnEncounterFromResolvedData(
        spawn.encounterSlot,
        spawn.fixedTier,
        resolvedCount,
        static_cast<float>(spawn.x),
        static_cast<float>(spawn.y),
        static_cast<float>(spawn.z),
        spawn.radius,
        spawn.attributes,
        spawn.group,
        0,
        true,
        spawnIndex,
        false);
}

bool OutdoorWorldRuntime::setMapActorDead(size_t actorIndex, bool isDead, bool emitAudio)
{
    if (actorIndex >= m_mapActors.size())
    {
        return false;
    }

    MapActorState &actor = m_mapActors[actorIndex];
    const bool wasDead = actor.isDead;
    actor.isDead = isDead;
    actor.currentHp = isDead ? 0 : actor.maxHp;
    actor.aiState = isDead ? ActorAiState::Dead : ActorAiState::Standing;
    actor.animation = isDead ? ActorAnimation::Dead : ActorAnimation::Standing;
    actor.animationTimeTicks = 0.0f;
    actor.actionSeconds = 0.0f;

    if (!wasDead && isDead && m_pMonsterTable != nullptr)
    {
        const MonsterTable::MonsterStatsEntry *pStats = m_pMonsterTable->findStatsById(actor.monsterId);

        if (pStats != nullptr)
        {
            if (actorIndex >= m_mapActorCorpseViews.size())
            {
                m_mapActorCorpseViews.resize(actorIndex + 1);
            }

            if (emitAudio)
            {
                pushAudioEvent(
                    pStats->deathSoundId,
                    actor.actorId,
                    "monster_death",
                    actor.preciseX,
                    actor.preciseY,
                    actor.preciseZ + static_cast<float>(actor.height) * 0.5f);
            }
        }
    }

    if (wasDead && !isDead && actorIndex < m_mapActorCorpseViews.size())
    {
        m_mapActorCorpseViews[actorIndex].reset();
    }

    if (wasDead && !isDead)
    {
        actor.bloodSplatSpawned = false;
        removeBloodSplat(actor.actorId);
    }

    return true;
}

bool OutdoorWorldRuntime::applyMonsterAttackToMapActor(
    size_t actorIndex,
    int damage,
    uint32_t sourceActorId,
    bool emitAudio)
{
    if (actorIndex >= m_mapActors.size() || damage <= 0)
    {
        return false;
    }

    MapActorState &actor = m_mapActors[actorIndex];

    if (isActorUnavailableForCombat(actor))
    {
        return false;
    }

    const MapActorState *pSourceActor = nullptr;

    for (const MapActorState &candidate : m_mapActors)
    {
        if (candidate.actorId == sourceActorId)
        {
            pSourceActor = &candidate;
            break;
        }
    }

    actor.currentHp = std::max(0, actor.currentHp - damage);

    if (pSourceActor != nullptr)
    {
        faceDirection(actor, pSourceActor->preciseX - actor.preciseX, pSourceActor->preciseY - actor.preciseY);
    }

    if (actor.currentHp <= 0)
    {
        beginDyingState(actor, m_pActorSpriteFrameTable);

        if (emitAudio && m_pMonsterTable != nullptr)
        {
            if (const MonsterTable::MonsterStatsEntry *pStats = m_pMonsterTable->findStatsById(actor.monsterId))
            {
                pushAudioEvent(
                    pStats->deathSoundId,
                    actor.actorId,
                    "monster_death",
                    actor.preciseX,
                    actor.preciseY,
                    actor.preciseZ + static_cast<float>(actor.height) * 0.5f);
            }
        }

        return true;
    }

    if (canEnterHitReaction(actor))
    {
        beginHitReaction(actor, m_pActorSpriteFrameTable);
    }

    if (emitAudio && m_pMonsterTable != nullptr)
    {
        if (const MonsterTable::MonsterStatsEntry *pStats = m_pMonsterTable->findStatsById(actor.monsterId))
        {
            pushAudioEvent(
                pStats->winceSoundId,
                actor.actorId,
                "monster_hit",
                actor.preciseX,
                actor.preciseY,
                actor.preciseZ + static_cast<float>(actor.height) * 0.5f);
        }
    }

    return true;
}

bool OutdoorWorldRuntime::spawnEncounterFromResolvedData(
    int encounterSlot,
    char fixedTier,
    uint32_t count,
    float x,
    float y,
    float z,
    uint16_t radius,
    uint16_t attributes,
    uint32_t group,
    uint32_t uniqueNameId,
    bool fromSpawnPoint,
    size_t spawnPointIndex,
    bool aggro)
{
    if (m_pMonsterTable == nullptr || count == 0)
    {
        return false;
    }

    bool spawnedAny = false;

    for (uint32_t spawnOrdinal = 0; spawnOrdinal < count; ++spawnOrdinal)
    {
        const uint32_t tierSeed = m_sessionChestSeed
            ^ static_cast<uint32_t>(encounterSlot * 2654435761u)
            ^ static_cast<uint32_t>((spawnOrdinal + 1u) * 2246822519u)
            ^ static_cast<uint32_t>(group * 3266489917u)
            ^ static_cast<uint32_t>(uniqueNameId * 668265263u)
            ^ static_cast<uint32_t>(spawnPointIndex == static_cast<size_t>(-1) ? 0u : spawnPointIndex + 1u)
            ^ static_cast<uint32_t>(std::lround(x))
            ^ static_cast<uint32_t>(std::lround(y))
            ^ static_cast<uint32_t>(std::lround(z));
        const char resolvedTier = resolveEncounterTierLetter(m_map, encounterSlot, fixedTier, tierSeed);
        const MonsterTable::MonsterStatsEntry *pStats =
            resolveEncounterMonsterStats(m_map, *m_pMonsterTable, encounterSlot, resolvedTier);

        if (pStats == nullptr)
        {
            continue;
        }

        const MonsterEntry *pMonsterEntry =
            resolveMonsterEntry(*m_pMonsterTable, static_cast<int16_t>(pStats->id), pStats);
        const uint16_t actorRadius = pMonsterEntry != nullptr ? std::max<uint16_t>(pMonsterEntry->radius, 32) : 32;
        const bx::Vec3 spawnPosition = calculateEncounterSpawnPosition(
            x,
            y,
            z,
            radius,
            actorRadius,
            spawnOrdinal);
        MapActorState actor = buildSpawnedMapActorState(
            *m_pMonsterTable,
            m_pOutdoorMapData,
            *pStats,
            m_nextActorId++,
            uniqueNameId,
            fromSpawnPoint,
            spawnPointIndex,
            group,
            attributes,
            spawnPosition.x,
            spawnPosition.y,
            spawnPosition.z);

        const auto visualIt = m_monsterVisualsById.find(actor.monsterId);

        if (visualIt != m_monsterVisualsById.end())
        {
            applyMonsterVisualState(actor, visualIt->second);
        }
        else if (m_pActorSpriteFrameTable != nullptr)
        {
            const MonsterVisualState visualState = buildMonsterVisualState(*m_pActorSpriteFrameTable, pMonsterEntry);

            if (visualState.spriteFrameIndex != 0)
            {
                m_monsterVisualsById[actor.monsterId] = visualState;
                applyMonsterVisualState(actor, visualState);
            }
        }

        actor.hostileToParty = actor.hostileToParty || aggro;
        applyTestActorOverrides(m_mapId, m_pOutdoorMapData, pStats, actor.actorId, actor);

        if (m_outdoorMovementController)
        {
            const float collisionRadius = actorCollisionRadius(actor, pStats);
            actor.movementState = m_outdoorMovementController->initializeStateForBody(
                actor.preciseX,
                actor.preciseY,
                actor.preciseZ + GroundSnapHeight,
                collisionRadius);
            actor.movementStateInitialized = true;
            syncActorFromMovementState(actor);
            actor.homePreciseX = actor.preciseX;
            actor.homePreciseY = actor.preciseY;
            actor.homePreciseZ = actor.preciseZ;
            actor.homeX = actor.x;
            actor.homeY = actor.y;
            actor.homeZ = actor.z;
        }

        m_mapActors.push_back(std::move(actor));
        spawnedAny = true;
    }

    if (spawnedAny)
    {
        applyEventRuntimeState();
    }

    return spawnedAny;
}

bool OutdoorWorldRuntime::setMapActorHostileToParty(
    size_t actorIndex,
    float partyX,
    float partyY,
    float partyZ,
    bool resetActionState)
{
    if (actorIndex >= m_mapActors.size())
    {
        return false;
    }

    MapActorState &actor = m_mapActors[actorIndex];

    if (isActorUnavailableForCombat(actor))
    {
        return false;
    }

    actor.hostileToParty = true;
    actor.hasDetectedParty = false;
    faceDirection(actor, partyX - actor.preciseX, partyY - actor.preciseY);

    if (!resetActionState)
    {
        return true;
    }

    actor.aiState = ActorAiState::Standing;
    actor.animation = ActorAnimation::Standing;
    actor.animationTimeTicks = 0.0f;
    actor.moveDirectionX = 0.0f;
    actor.moveDirectionY = 0.0f;
    actor.velocityX = 0.0f;
    actor.velocityY = 0.0f;
    actor.velocityZ = 0.0f;
    actor.actionSeconds = 0.0f;
    actor.idleDecisionSeconds = 0.0f;
    actor.attackImpactTriggered = false;
    return true;
}

void OutdoorWorldRuntime::aggroNearbyMapActorFaction(size_t actorIndex, float partyX, float partyY, float partyZ)
{
    if (actorIndex >= m_mapActors.size() || m_pMonsterTable == nullptr)
    {
        return;
    }

    const MapActorState &victim = m_mapActors[actorIndex];

    for (size_t otherActorIndex = 0; otherActorIndex < m_mapActors.size(); ++otherActorIndex)
    {
        if (otherActorIndex == actorIndex)
        {
            continue;
        }

        MapActorState &otherActor = m_mapActors[otherActorIndex];

        if (isActorUnavailableForCombat(otherActor))
        {
            continue;
        }

        if (!m_pMonsterTable->isLikelySameFaction(victim.monsterId, otherActor.monsterId))
        {
            continue;
        }

        const float distance = length3d(
            otherActor.preciseX - victim.preciseX,
            otherActor.preciseY - victim.preciseY,
            otherActor.preciseZ - victim.preciseZ);

        if (distance > PeasantAggroRadius)
        {
            continue;
        }

        setMapActorHostileToParty(otherActorIndex, partyX, partyY, partyZ, true);
    }
}

bool OutdoorWorldRuntime::applyPartyAttackToMapActor(
    size_t actorIndex,
    int damage,
    float partyX,
    float partyY,
    float partyZ)
{
    if (actorIndex >= m_mapActors.size() || damage <= 0)
    {
        return false;
    }

    MapActorState &actor = m_mapActors[actorIndex];

    if (isActorUnavailableForCombat(actor))
    {
        return false;
    }

    actor.currentHp = std::max(0, actor.currentHp - damage);
    faceDirection(actor, partyX - actor.preciseX, partyY - actor.preciseY);
    setMapActorHostileToParty(actorIndex, partyX, partyY, partyZ, false);

    const bool died = actor.currentHp <= 0;

    if (died)
    {
        beginDyingState(actor, m_pActorSpriteFrameTable);

        if (m_pMonsterTable != nullptr)
        {
            if (const MonsterTable::MonsterStatsEntry *pStats = m_pMonsterTable->findStatsById(actor.monsterId))
            {
                if (m_pParty != nullptr && pStats->experience > 0)
                {
                    m_pParty->grantSharedExperience(static_cast<uint32_t>(pStats->experience));
                }

                pushAudioEvent(
                    pStats->deathSoundId,
                    actor.actorId,
                    "monster_death",
                    actor.preciseX,
                    actor.preciseY,
                    actor.preciseZ + static_cast<float>(actor.height) * 0.5f);
            }
        }
    }
    else
    {
        if (canEnterHitReaction(actor))
        {
            faceDirection(actor, partyX - actor.preciseX, partyY - actor.preciseY);
            beginHitReaction(actor, m_pActorSpriteFrameTable);
        }

        if (m_pMonsterTable != nullptr)
        {
            if (const MonsterTable::MonsterStatsEntry *pStats = m_pMonsterTable->findStatsById(actor.monsterId))
            {
                pushAudioEvent(
                    pStats->winceSoundId,
                    actor.actorId,
                    "monster_hit",
                    actor.preciseX,
                    actor.preciseY,
                    actor.preciseZ + static_cast<float>(actor.height) * 0.5f);
            }
        }
    }

    aggroNearbyMapActorFaction(actorIndex, partyX, partyY, partyZ);
    return true;
}

bool OutdoorWorldRuntime::applyPartyAttackMeleeDamage(
    size_t actorIndex,
    int damage,
    const GameplayWorldPoint &source)
{
    return applyPartyAttackToMapActor(actorIndex, damage, source.x, source.y, source.z);
}

bool OutdoorWorldRuntime::spawnPartyAttackProjectile(const GameplayPartyAttackProjectileRequest &request)
{
    PartyProjectileRequest worldRequest = {};
    worldRequest.sourcePartyMemberIndex = static_cast<uint32_t>(request.sourcePartyMemberIndex);
    worldRequest.objectId = request.objectId;
    worldRequest.damage = request.damage;
    worldRequest.attackBonus = request.attackBonus;
    worldRequest.useActorHitChance = request.useActorHitChance;
    worldRequest.sourceX = request.source.x;
    worldRequest.sourceY = request.source.y;
    worldRequest.sourceZ = request.source.z;
    worldRequest.targetX = request.target.x;
    worldRequest.targetY = request.target.y;
    worldRequest.targetZ = request.target.z;
    return spawnPartyProjectile(worldRequest);
}

bool OutdoorWorldRuntime::castPartyAttackSpell(const GameplayPartyAttackSpellRequest &request)
{
    SpellCastRequest worldRequest = {};
    worldRequest.sourceKind = RuntimeSpellSourceKind::Party;
    worldRequest.sourceId = static_cast<uint32_t>(request.sourcePartyMemberIndex + 1);
    worldRequest.sourcePartyMemberIndex = static_cast<uint32_t>(request.sourcePartyMemberIndex);
    worldRequest.ability = MonsterAttackAbility::Spell1;
    worldRequest.spellId = request.spellId;
    worldRequest.skillLevel = request.skillLevel;
    worldRequest.skillMastery = request.skillMastery;
    worldRequest.damage = request.damage;
    worldRequest.attackBonus = request.attackBonus;
    worldRequest.useActorHitChance = request.useActorHitChance;
    worldRequest.sourceX = request.source.x;
    worldRequest.sourceY = request.source.y;
    worldRequest.sourceZ = request.source.z;
    worldRequest.targetX = request.target.x;
    worldRequest.targetY = request.target.y;
    worldRequest.targetZ = request.target.z;
    return castPartySpell(worldRequest);
}

void OutdoorWorldRuntime::recordPartyAttackWorldResult(
    std::optional<size_t> actorIndex,
    bool attacked,
    bool actionPerformed)
{
    if (!m_eventRuntimeState)
    {
        return;
    }

    if (actorIndex)
    {
        m_eventRuntimeState->lastActivationResult =
            attacked
                ? "actor " + std::to_string(*actorIndex) + " hit by party"
                : "actor " + std::to_string(*actorIndex) + " attacked by party";
        return;
    }

    m_eventRuntimeState->lastActivationResult =
        actionPerformed
            ? "party attack released"
            : "party attack failed";
}

bool OutdoorWorldRuntime::worldInteractionReady() const
{
    return m_pOutdoorMapData != nullptr;
}

bool OutdoorWorldRuntime::worldInspectModeActive() const
{
    return m_pInteractionView != nullptr && OutdoorInteractionController::worldInspectModeActive(*m_pInteractionView);
}

GameplayWorldPickRequest OutdoorWorldRuntime::buildWorldPickRequest(const GameplayWorldPickRequestInput &input) const
{
    if (m_pInteractionView == nullptr)
    {
        return {};
    }

    return OutdoorInteractionController::buildWorldPickRequest(*m_pInteractionView, input);
}

std::optional<GameplayHeldItemDropRequest> OutdoorWorldRuntime::buildHeldItemDropRequest() const
{
    if (m_pInteractionView == nullptr)
    {
        return std::nullopt;
    }

    return OutdoorInteractionController::buildHeldItemDropRequest(*m_pInteractionView);
}

GameplayPartyAttackFrameInput OutdoorWorldRuntime::buildPartyAttackFrameInput(
    const GameplayWorldPickRequest &pickRequest) const
{
    if (m_pInteractionView == nullptr)
    {
        return {};
    }

    return OutdoorInteractionController::buildPartyAttackFrameInput(*m_pInteractionView, pickRequest);
}

std::optional<size_t> OutdoorWorldRuntime::spellActionHoveredActorIndex() const
{
    if (m_pInteractionView == nullptr)
    {
        return std::nullopt;
    }

    return OutdoorInteractionController::resolveSpellActionHoveredActorIndex(*m_pInteractionView);
}

std::optional<size_t> OutdoorWorldRuntime::spellActionClosestVisibleHostileActorIndex() const
{
    if (m_pInteractionView == nullptr || m_pPartyRuntime == nullptr)
    {
        return std::nullopt;
    }

    const OutdoorMoveState &moveState = m_pPartyRuntime->movementState();
    return OutdoorInteractionController::resolveClosestVisibleHostileActorIndex(
        *m_pInteractionView,
        moveState.x,
        moveState.y,
        moveState.footZ + 96.0f);
}

std::optional<bx::Vec3> OutdoorWorldRuntime::spellActionActorTargetPoint(size_t actorIndex) const
{
    if (m_pInteractionView == nullptr)
    {
        return std::nullopt;
    }

    return OutdoorInteractionController::resolveSpellActionActorTargetPoint(*m_pInteractionView, actorIndex);
}

std::optional<bx::Vec3> OutdoorWorldRuntime::spellActionGroundTargetPoint(float screenX, float screenY) const
{
    if (m_pInteractionView == nullptr || m_pOutdoorMapData == nullptr)
    {
        return std::nullopt;
    }

    return OutdoorInteractionController::resolveQuickCastCursorTargetPoint(*m_pInteractionView, screenX, screenY);
}

bool OutdoorWorldRuntime::applyDirectSpellImpactToMapActor(
    size_t actorIndex,
    uint32_t spellId,
    float partyX,
    float partyY,
    float partyZ,
    uint32_t sourcePartyMemberIndex,
    const GameplayActorService::DirectSpellImpactResult &impact)
{
    if (actorIndex >= m_mapActors.size()
        || impact.disposition != GameplayActorService::DirectSpellImpactDisposition::ApplyDamage)
    {
        return false;
    }

    MapActorState &actor = m_mapActors[actorIndex];

    if (impact.visualKind == GameplayActorService::DirectSpellImpactVisualKind::ActorCenter)
    {
        spawnImmediateSpellVisual(
            spellId,
            actor.preciseX,
            actor.preciseY,
            actor.preciseZ + static_cast<float>(actor.height) * 0.5f,
            impact.centerVisual,
            impact.preferImpactObject);
    }
    else if (impact.visualKind == GameplayActorService::DirectSpellImpactVisualKind::ActorUpperBody)
    {
        spawnImmediateSpellVisual(
            spellId,
            actor.preciseX,
            actor.preciseY,
            actor.preciseZ + static_cast<float>(actor.height) * 0.8f,
            impact.centerVisual,
            impact.preferImpactObject);
    }

    const int beforeHp = actor.currentHp;
    const bool applied = applyPartyAttackToMapActor(actorIndex, impact.damage, partyX, partyY, partyZ);

    if (applied && m_pGameplayCombatController != nullptr)
    {
        m_pGameplayCombatController->recordPartyProjectileActorImpact(
            0,
            sourcePartyMemberIndex,
            actor.actorId,
            impact.damage,
            static_cast<int>(spellId),
            true,
            beforeHp > 0 && actor.currentHp <= 0);
    }

    return applied;
}

bool OutdoorWorldRuntime::applyPartySpellToMapActor(
    size_t actorIndex,
    uint32_t spellId,
    uint32_t skillLevel,
    SkillMastery skillMastery,
    int damage,
    float partyX,
    float partyY,
    float partyZ,
    uint32_t sourcePartyMemberIndex)
{
    if (actorIndex >= m_mapActors.size() || m_pSpellTable == nullptr)
    {
        return false;
    }

    MapActorState &actor = m_mapActors[actorIndex];

    if (isActorUnavailableForCombat(actor))
    {
        return false;
    }

    const SpellEntry *pSpellEntry = m_pSpellTable->findById(static_cast<int>(spellId));

    if (pSpellEntry == nullptr)
    {
        return false;
    }

    const std::string &spellName = pSpellEntry->normalizedName;
    const auto spawnTargetDebuffParticles = [this, spellId, &actor, partyX, partyY]()
    {
        if (m_pParticleSystem == nullptr)
        {
            return;
        }

        const float frontDirectionX = actor.preciseX - partyX;
        const float frontDirectionY = actor.preciseY - partyY;
        const uint32_t seed =
            actor.actorId * 2246822519u
            ^ spellId * 3266489917u
            ^ projectileService().allocateProjectileImpactId();
        FxRecipes::spawnActorDebuffParticles(
            *m_pParticleSystem,
            spellId,
            seed,
            actor.preciseX,
            actor.preciseY,
            actor.preciseZ,
            static_cast<float>(actor.height),
            frontDirectionX,
            frontDirectionY);
    };

    GameplayActorService fallbackActorService = {};
    const GameplayActorService *pActorService = m_pGameplayActorService;

    if (pActorService == nullptr)
    {
        fallbackActorService.bindTables(m_pMonsterTable, m_pSpellTable);
        pActorService = &fallbackActorService;
    }

    if (pActorService != nullptr)
    {
        const GameplayActorService::DirectSpellImpactResult directImpact =
            pActorService->resolveDirectSpellImpact(
                spellId,
                skillLevel,
                damage,
                actor.currentHp,
                pActorService->actorLooksUndead(actor.monsterId));

        if (directImpact.disposition == GameplayActorService::DirectSpellImpactDisposition::Rejected)
        {
            return false;
        }

        if (directImpact.disposition == GameplayActorService::DirectSpellImpactDisposition::ApplyDamage)
        {
            return applyDirectSpellImpactToMapActor(
                actorIndex,
                spellId,
                partyX,
                partyY,
                partyZ,
                sourcePartyMemberIndex,
                directImpact);
        }

        const bool defaultHostileToParty =
            m_pMonsterTable != nullptr
            && m_pMonsterTable->isHostileToParty(actor.monsterId);
        GameplayActorSpellEffectState effectState = buildGameplayActorSpellEffectState(actor);
        const GameplayActorService::SharedSpellEffectResult effectResult =
            pActorService->tryApplySharedSpellEffect(
                spellId,
                skillLevel,
                skillMastery,
                pActorService->actorLooksUndead(actor.monsterId),
                defaultHostileToParty,
                effectState);

        if (effectResult.disposition == GameplayActorService::SharedSpellDisposition::Rejected)
        {
            return false;
        }

        if (effectResult.disposition == GameplayActorService::SharedSpellDisposition::Applied)
        {
            applyGameplayActorSpellEffectState(effectState, actor);

            const auto resetActorMotion =
                [&actor]()
            {
                actor.aiState = ActorAiState::Standing;
                actor.animation = ActorAnimation::Standing;
                actor.animationTimeTicks = 0.0f;
                actor.actionSeconds = 0.0f;
                actor.moveDirectionX = 0.0f;
                actor.moveDirectionY = 0.0f;
                actor.velocityX = 0.0f;
                actor.velocityY = 0.0f;
                actor.velocityZ = 0.0f;
                actor.attackImpactTriggered = false;
            };

            switch (effectResult.effectKind)
            {
                case GameplayActorService::SharedSpellEffectKind::Stun:
                {
                    actor.aiState = ActorAiState::Stunned;
                    actor.animation = ActorAnimation::GotHit;
                    actor.actionSeconds = std::max(actor.actionSeconds, actor.stunRemainingSeconds);
                    faceDirection(actor, partyX - actor.preciseX, partyY - actor.preciseY);
                    break;
                }

                case GameplayActorService::SharedSpellEffectKind::Paralyze:
                case GameplayActorService::SharedSpellEffectKind::Control:
                {
                    resetActorMotion();
                    break;
                }

                case GameplayActorService::SharedSpellEffectKind::Fear:
                {
                    if (spellName == "fear")
                    {
                        const float deltaX = actor.preciseX - partyX;
                        const float deltaY = actor.preciseY - partyY;
                        const float horizontalLength = std::sqrt(deltaX * deltaX + deltaY * deltaY);

                        if (horizontalLength > 0.01f)
                        {
                            const float pushStrength = 160.0f + 8.0f * static_cast<float>(skillLevel);
                            actor.velocityX = (deltaX / horizontalLength) * pushStrength;
                            actor.velocityY = (deltaY / horizontalLength) * pushStrength;
                        }

                        actor.animation = ActorAnimation::GotHit;
                        actor.actionSeconds = std::max(actor.actionSeconds, 0.3f);
                    }
                    else
                    {
                        resetActorMotion();
                    }

                    break;
                }

                case GameplayActorService::SharedSpellEffectKind::Blind:
                {
                    actor.animation = ActorAnimation::GotHit;
                    break;
                }

                case GameplayActorService::SharedSpellEffectKind::Slow:
                case GameplayActorService::SharedSpellEffectKind::Shrink:
                case GameplayActorService::SharedSpellEffectKind::DarkGrasp:
                case GameplayActorService::SharedSpellEffectKind::DispelMagic:
                case GameplayActorService::SharedSpellEffectKind::None:
                default:
                {
                    break;
                }
            }

            if (effectResult.effectKind != GameplayActorService::SharedSpellEffectKind::DispelMagic)
            {
                spawnTargetDebuffParticles();
            }

            return true;
        }
    }

    if (spellName == "fear" || spellName == "wing buffet")
    {
        if (spellName == "fear")
        {
            actor.fearRemainingSeconds = std::max(
                actor.fearRemainingSeconds,
                skillMastery == SkillMastery::Expert
                    ? minutesToSeconds(5.0f + static_cast<float>(skillLevel))
                    : minutesToSeconds(3.0f + static_cast<float>(skillLevel)));
            actor.hasDetectedParty = false;
            spawnTargetDebuffParticles();
        }

        const float deltaX = actor.preciseX - partyX;
        const float deltaY = actor.preciseY - partyY;
        const float horizontalLength = std::sqrt(deltaX * deltaX + deltaY * deltaY);

        if (horizontalLength > 0.01f)
        {
            const float pushStrength =
                spellName == "wing buffet"
                    ? 320.0f + 24.0f * static_cast<float>(skillLevel)
                    : 160.0f + 8.0f * static_cast<float>(skillLevel);
            actor.velocityX = (deltaX / horizontalLength) * pushStrength;
            actor.velocityY = (deltaY / horizontalLength) * pushStrength;
        }

        actor.animation = ActorAnimation::GotHit;
        actor.actionSeconds = std::max(actor.actionSeconds, 0.3f);
        return true;
    }

    if (spellName == "reanimate")
    {
        if (!actor.isDead)
        {
            return false;
        }

        const int healthMultiplier =
            skillMastery == SkillMastery::Grandmaster
                ? 50
                : skillMastery == SkillMastery::Master
                ? 40
                : skillMastery == SkillMastery::Expert
                ? 30
                : 20;
        return resurrectMapActor(actorIndex, static_cast<int>(skillLevel) * healthMultiplier, true);
    }

    return false;
}

bool OutdoorWorldRuntime::spawnImmediateSpellVisual(
    uint32_t spellId,
    float x,
    float y,
    float z,
    bool centerVertically,
    bool preferImpactObject)
{
    if (m_pSpellTable == nullptr || m_pObjectTable == nullptr)
    {
        return false;
    }

    const SpellEntry *pSpellEntry = m_pSpellTable->findById(static_cast<int>(spellId));

    if (pSpellEntry == nullptr)
    {
        return false;
    }

    ResolvedProjectileDefinition definition = {};

    if (!resolveSpellDefinition(*pSpellEntry, *m_pObjectTable, definition))
    {
        return false;
    }

    uint16_t effectDescriptionId = preferImpactObject ? definition.impactObjectDescriptionId : definition.objectDescriptionId;
    uint16_t effectSpriteId = preferImpactObject ? definition.impactObjectSpriteId : definition.objectSpriteId;
    std::string effectObjectName = preferImpactObject ? definition.impactObjectName : definition.objectName;
    std::string effectSpriteName = preferImpactObject ? definition.impactObjectSpriteName : definition.objectSpriteName;

    if (effectDescriptionId == 0)
    {
        effectDescriptionId = preferImpactObject ? definition.objectDescriptionId : definition.impactObjectDescriptionId;
        effectSpriteId = preferImpactObject ? definition.objectSpriteId : definition.impactObjectSpriteId;
        effectObjectName = preferImpactObject ? definition.objectName : definition.impactObjectName;
        effectSpriteName = preferImpactObject ? definition.objectSpriteName : definition.impactObjectSpriteName;
    }

    if (effectDescriptionId == 0)
    {
        return false;
    }

    const SpellId resolvedSpellId = spellIdFromValue(spellId);
    uint16_t resolvedFrameIndex = resolveRuntimeSpriteFrameIndex(
        m_pProjectileSpriteFrameTable,
        effectSpriteId,
        effectSpriteName);

    if ((m_pProjectileSpriteFrameTable == nullptr
            || m_pProjectileSpriteFrameTable->getFrame(resolvedFrameIndex, 0) == nullptr)
        && !preferImpactObject)
    {
        applyImmediateSpellVisualFallback(resolvedSpellId, effectSpriteId, effectSpriteName);
        resolvedFrameIndex = resolveRuntimeSpriteFrameIndex(
            m_pProjectileSpriteFrameTable,
            effectSpriteId,
            effectSpriteName);
    }

    const ObjectEntry *pEffectEntry = m_pObjectTable->get(effectDescriptionId);

    if (pEffectEntry == nullptr)
    {
        return false;
    }

    GameplayProjectileService::ProjectileImpactVisualDefinition effectDefinition = {};
    effectDefinition.objectDescriptionId = effectDescriptionId;
    effectDefinition.objectSpriteId = effectSpriteId;
    effectDefinition.objectSpriteFrameIndex = resolvedFrameIndex;
    effectDefinition.objectHeight = pEffectEntry->height;
    effectDefinition.lifetimeTicks = static_cast<uint32_t>(std::max<int>(pEffectEntry->lifetimeTicks, 32));
    effectDefinition.hasVisual = effectSpriteId != 0 || !effectSpriteName.empty();
    effectDefinition.objectName = effectObjectName;
    effectDefinition.objectSpriteName = effectSpriteName;

    const GameplayProjectileService::ProjectileImpactSpawnResult result =
        spawnImmediateSpellImpactVisual(
            effectDefinition,
            static_cast<int>(spellId),
            definition.objectName,
            definition.objectSpriteName,
            x,
            y,
            z,
            centerVertically,
            !preferImpactObject);
    return result.spawned;
}

bool OutdoorWorldRuntime::applyPartySpellToActor(
    size_t actorIndex,
    uint32_t spellId,
    uint32_t skillLevel,
    SkillMastery skillMastery,
    int damage,
    float partyX,
    float partyY,
    float partyZ,
    uint32_t sourcePartyMemberIndex)
{
    return applyPartySpellToMapActor(
        actorIndex,
        spellId,
        skillLevel,
        skillMastery,
        damage,
        partyX,
        partyY,
        partyZ,
        sourcePartyMemberIndex);
}

bool OutdoorWorldRuntime::healMapActor(size_t actorIndex, int amount)
{
    if (actorIndex >= m_mapActors.size() || amount <= 0)
    {
        return false;
    }

    MapActorState &actor = m_mapActors[actorIndex];

    if (actor.isDead)
    {
        return false;
    }

    const int previousHp = actor.currentHp;
    actor.currentHp = std::clamp(actor.currentHp + amount, 0, std::max(1, actor.maxHp));
    return actor.currentHp > previousHp;
}

bool OutdoorWorldRuntime::resurrectMapActor(size_t actorIndex, int health, bool friendlyToParty)
{
    if (actorIndex >= m_mapActors.size())
    {
        return false;
    }

    MapActorState &actor = m_mapActors[actorIndex];

    if (!actor.isDead)
    {
        return false;
    }

    setMapActorDead(actorIndex, false, false);
    actor.currentHp = std::clamp(health, 1, std::max(1, actor.maxHp));
    actor.aiState = ActorAiState::Standing;
    actor.animation = ActorAnimation::Standing;
    actor.actionSeconds = 0.0f;
    actor.attackCooldownSeconds = actor.recoverySeconds;
    actor.controlMode = friendlyToParty ? ActorControlMode::Reanimated : ActorControlMode::None;
    actor.controlRemainingSeconds = friendlyToParty ? hoursToSeconds(24.0f) : 0.0f;
    actor.hostileToParty = !friendlyToParty
        && m_pMonsterTable != nullptr
        && m_pMonsterTable->isHostileToParty(actor.monsterId);
    actor.hasDetectedParty = false;
    return true;
}

bool OutdoorWorldRuntime::clearMapActorSpellEffects(size_t actorIndex)
{
    if (actorIndex >= m_mapActors.size())
    {
        return false;
    }

    if (m_pGameplayActorService == nullptr)
    {
        return false;
    }

    MapActorState &actor = m_mapActors[actorIndex];
    GameplayActorSpellEffectState effectState = buildGameplayActorSpellEffectState(actor);
    const bool defaultHostileToParty =
        m_pMonsterTable != nullptr
        && m_pMonsterTable->isHostileToParty(actor.monsterId);
    m_pGameplayActorService->clearSpellEffects(effectState, defaultHostileToParty);
    applyGameplayActorSpellEffectState(effectState, actor);
    return true;
}

int OutdoorWorldRuntime::effectiveMapActorArmorClass(size_t actorIndex) const
{
    if (actorIndex >= m_mapActors.size())
    {
        return 0;
    }

    const MapActorState &actor = m_mapActors[actorIndex];
    const MonsterTable::MonsterStatsEntry *pStats =
        m_pMonsterTable != nullptr ? m_pMonsterTable->findStatsById(actor.monsterId) : nullptr;
    const int baseArmorClass = pStats != nullptr ? pStats->armorClass : 0;

    if (m_pGameplayActorService == nullptr)
    {
        return std::max(0, baseArmorClass);
    }

    return m_pGameplayActorService->effectiveArmorClass(baseArmorClass, buildGameplayActorSpellEffectState(actor));
}

std::vector<size_t> OutdoorWorldRuntime::collectMapActorIndicesWithinRadius(
    float centerX,
    float centerY,
    float centerZ,
    float radius,
    bool requireLineOfSight,
    float sourceX,
    float sourceY,
    float sourceZ) const
{
    std::vector<size_t> result;

    if (radius <= 0.0f)
    {
        return result;
    }

    const bx::Vec3 source = {sourceX, sourceY, sourceZ};

    for (size_t actorIndex = 0; actorIndex < m_mapActors.size(); ++actorIndex)
    {
        const MapActorState &actor = m_mapActors[actorIndex];

        if (isActorUnavailableForCombat(actor))
        {
            continue;
        }

        const float targetZ = actor.preciseZ + std::max(24.0f, static_cast<float>(actor.height) * 0.7f);
        const float deltaX = actor.preciseX - centerX;
        const float deltaY = actor.preciseY - centerY;
        const float deltaZ = targetZ - centerZ;
        const float edgeDistance =
            std::max(0.0f, length3d(deltaX, deltaY, deltaZ) - static_cast<float>(actor.radius));

        if (edgeDistance > radius)
        {
            continue;
        }

        if (requireLineOfSight)
        {
            const bx::Vec3 target = {actor.preciseX, actor.preciseY, targetZ};

            if (!hasClearOutdoorLineOfSight(source, target))
            {
                continue;
            }
        }

        result.push_back(actorIndex);
    }

    return result;
}

bool OutdoorWorldRuntime::notifyPartyContactWithMapActor(size_t actorIndex, float partyX, float partyY, float partyZ)
{
    if (actorIndex >= m_mapActors.size())
    {
        return false;
    }

    MapActorState &actor = m_mapActors[actorIndex];

    if (isActorUnavailableForCombat(actor) || actor.hostileToParty)
    {
        return false;
    }

    if (std::abs(partyZ - actor.preciseZ) > static_cast<float>(std::max<uint16_t>(actor.height, 192)))
    {
        return false;
    }

    faceDirection(actor, partyX - actor.preciseX, partyY - actor.preciseY);
    actor.aiState = ActorAiState::Standing;
    actor.animation = ActorAnimation::Standing;
    actor.animationTimeTicks = 0.0f;
    actor.moveDirectionX = 0.0f;
    actor.moveDirectionY = 0.0f;
    actor.velocityX = 0.0f;
    actor.velocityY = 0.0f;
    actor.velocityZ = 0.0f;
    actor.actionSeconds = std::max(actor.actionSeconds, 2.0f);
    actor.idleDecisionSeconds = std::max(actor.idleDecisionSeconds, 2.0f);
    return true;
}

size_t OutdoorWorldRuntime::spawnPointCount() const
{
    return m_spawnPoints.size();
}

const OutdoorWorldRuntime::SpawnPointState *OutdoorWorldRuntime::spawnPointState(size_t spawnIndex) const
{
    if (spawnIndex >= m_spawnPoints.size())
    {
        return nullptr;
    }

    return &m_spawnPoints[spawnIndex];
}

size_t OutdoorWorldRuntime::chestCount() const
{
    return m_openedChests.size();
}

size_t OutdoorWorldRuntime::openedChestCount() const
{
    size_t count = 0;

    for (bool isOpened : m_openedChests)
    {
        if (isOpened)
        {
            ++count;
        }
    }

    return count;
}

OutdoorWorldRuntime::ChestViewState *OutdoorWorldRuntime::activeChestView()
{
    return m_activeChestView ? &*m_activeChestView : nullptr;
}

const OutdoorWorldRuntime::ChestViewState *OutdoorWorldRuntime::activeChestView() const
{
    if (!m_activeChestView)
    {
        return nullptr;
    }

    return &*m_activeChestView;
}

void OutdoorWorldRuntime::commitActiveChestView()
{
    if (!m_activeChestView)
    {
        return;
    }

    const uint32_t chestId = m_activeChestView->chestId;

    if (chestId < m_materializedChestViews.size() && m_materializedChestViews[chestId].has_value())
    {
        m_materializedChestViews[chestId] = *m_activeChestView;
    }
}

bool OutdoorWorldRuntime::takeActiveChestItem(size_t itemIndex, ChestItemState &item)
{
    if (!m_activeChestView || !takeChestItem(*m_activeChestView, itemIndex, item))
    {
        return false;
    }

    const uint32_t chestId = m_activeChestView->chestId;

    if (chestId < m_materializedChestViews.size() && m_materializedChestViews[chestId].has_value())
    {
        m_materializedChestViews[chestId] = *m_activeChestView;
    }

    return true;
}


bool OutdoorWorldRuntime::takeActiveChestItemAt(uint8_t gridX, uint8_t gridY, ChestItemState &item)
{
    if (!m_activeChestView || !takeChestItemAt(*m_activeChestView, gridX, gridY, item))
    {
        return false;
    }
    const uint32_t chestId = m_activeChestView->chestId;

    if (chestId < m_materializedChestViews.size() && m_materializedChestViews[chestId].has_value())
    {
        m_materializedChestViews[chestId] = *m_activeChestView;
    }

    return true;
}

bool OutdoorWorldRuntime::tryPlaceActiveChestItemAt(const ChestItemState &item, uint8_t gridX, uint8_t gridY)
{
    if (!m_activeChestView || !tryPlaceChestItemAt(*m_activeChestView, item, gridX, gridY))
    {
        return false;
    }
    const uint32_t chestId = m_activeChestView->chestId;

    if (chestId < m_materializedChestViews.size() && m_materializedChestViews[chestId].has_value())
    {
        m_materializedChestViews[chestId] = *m_activeChestView;
    }

    return true;
}

void OutdoorWorldRuntime::closeActiveChestView()
{
    m_activeChestView.reset();
}

OutdoorWorldRuntime::CorpseViewState *OutdoorWorldRuntime::activeCorpseView()
{
    return m_activeCorpseView ? &*m_activeCorpseView : nullptr;
}

const OutdoorWorldRuntime::CorpseViewState *OutdoorWorldRuntime::activeCorpseView() const
{
    return m_activeCorpseView ? &*m_activeCorpseView : nullptr;
}

void OutdoorWorldRuntime::commitActiveCorpseView()
{
    if (!m_activeCorpseView)
    {
        return;
    }

    if (m_activeCorpseView->sourceIndex < m_mapActorCorpseViews.size())
    {
        m_mapActorCorpseViews[m_activeCorpseView->sourceIndex] = *m_activeCorpseView;
    }
}

bool OutdoorWorldRuntime::openMapActorCorpseView(size_t actorIndex)
{
    if (actorIndex >= m_mapActors.size())
    {
        return false;
    }

    const MapActorState &actor = m_mapActors[actorIndex];

    if (!actor.isDead || actor.isInvisible)
    {
        return false;
    }

    if (actorIndex >= m_mapActorCorpseViews.size())
    {
        m_mapActorCorpseViews.resize(actorIndex + 1);
    }

    if (!m_mapActorCorpseViews[actorIndex].has_value())
    {
        if (m_pMonsterTable == nullptr)
        {
            return false;
        }

        const MonsterTable::MonsterStatsEntry *pStats = m_pMonsterTable->findStatsById(actor.monsterId);

        if (pStats == nullptr)
        {
            return false;
        }

        CorpseViewState corpse = buildMonsterCorpseView(actor.displayName, pStats->loot, m_pItemTable, m_pParty);

        if (corpse.items.empty())
        {
            return false;
        }

        corpse.fromSummonedMonster = false;
        corpse.sourceIndex = static_cast<uint32_t>(actorIndex);
        m_mapActorCorpseViews[actorIndex] = std::move(corpse);
    }

    m_activeCorpseView = *m_mapActorCorpseViews[actorIndex];
    return true;
}

bool OutdoorWorldRuntime::takeActiveCorpseItem(size_t itemIndex, ChestItemState &item)
{
    if (!m_activeCorpseView || itemIndex >= m_activeCorpseView->items.size())
    {
        return false;
    }

    item = m_activeCorpseView->items[itemIndex];
    m_activeCorpseView->items.erase(m_activeCorpseView->items.begin() + static_cast<ptrdiff_t>(itemIndex));

    if (m_activeCorpseView->items.empty())
    {
        if (m_activeCorpseView->sourceIndex < m_mapActorCorpseViews.size())
        {
            m_mapActorCorpseViews[m_activeCorpseView->sourceIndex].reset();
        }

        if (m_activeCorpseView->sourceIndex < m_mapActors.size())
        {
            m_mapActors[m_activeCorpseView->sourceIndex].isInvisible = true;
        }

        m_activeCorpseView.reset();
        return true;
    }

    if (m_activeCorpseView->sourceIndex < m_mapActorCorpseViews.size())
    {
        m_mapActorCorpseViews[m_activeCorpseView->sourceIndex] = *m_activeCorpseView;
    }

    return true;
}


void OutdoorWorldRuntime::closeActiveCorpseView()
{
    m_activeCorpseView.reset();
}

const std::vector<OutdoorWorldRuntime::AudioEvent> &OutdoorWorldRuntime::pendingAudioEvents() const
{
    return m_pendingAudioEvents;
}

void OutdoorWorldRuntime::clearPendingAudioEvents()
{
    m_pendingAudioEvents.clear();
}

const std::vector<OutdoorWorldRuntime::CombatEvent> &OutdoorWorldRuntime::pendingCombatEvents() const
{
    if (m_pGameplayCombatController == nullptr)
    {
        static const std::vector<CombatEvent> EmptyEvents;
        return EmptyEvents;
    }

    return m_pGameplayCombatController->pendingCombatEvents();
}

void OutdoorWorldRuntime::clearPendingCombatEvents()
{
    if (m_pGameplayCombatController != nullptr)
    {
        m_pGameplayCombatController->clearPendingCombatEvents();
    }
}

size_t OutdoorWorldRuntime::worldItemCount() const
{
    return m_worldItems.size();
}

const OutdoorWorldRuntime::WorldItemState *OutdoorWorldRuntime::worldItemState(size_t worldItemIndex) const
{
    if (worldItemIndex >= m_worldItems.size())
    {
        return nullptr;
    }

    return &m_worldItems[worldItemIndex];
}

OutdoorWorldRuntime::WorldItemState *OutdoorWorldRuntime::worldItemStateMutable(size_t worldItemIndex)
{
    if (worldItemIndex >= m_worldItems.size())
    {
        return nullptr;
    }

    return &m_worldItems[worldItemIndex];
}

bool OutdoorWorldRuntime::takeWorldItem(size_t worldItemIndex, WorldItemState &item)
{
    if (worldItemIndex >= m_worldItems.size())
    {
        return false;
    }

    item = m_worldItems[worldItemIndex];
    m_worldItems.erase(m_worldItems.begin() + static_cast<std::ptrdiff_t>(worldItemIndex));
    return true;
}

bool OutdoorWorldRuntime::identifyWorldItem(size_t worldItemIndex, std::string &statusText)
{
    statusText.clear();
    WorldItemState *pWorldItem = worldItemStateMutable(worldItemIndex);

    if (pWorldItem == nullptr || m_pItemTable == nullptr || pWorldItem->isGold)
    {
        return false;
    }

    const ItemDefinition *pItemDefinition = m_pItemTable->get(pWorldItem->item.objectDescriptionId);

    if (pItemDefinition == nullptr)
    {
        statusText = "Unavailable.";
        return false;
    }

    if (pWorldItem->item.identified || !ItemRuntime::requiresIdentification(*pItemDefinition))
    {
        statusText = "Already identified.";
        return false;
    }

    pWorldItem->item.identified = true;
    statusText = "Identified " + ItemRuntime::displayName(pWorldItem->item, *pItemDefinition) + ".";
    return true;
}

bool OutdoorWorldRuntime::tryIdentifyWorldItem(size_t worldItemIndex, const Character &inspector, std::string &statusText)
{
    statusText.clear();
    WorldItemState *pWorldItem = worldItemStateMutable(worldItemIndex);

    if (pWorldItem == nullptr || m_pItemTable == nullptr || pWorldItem->isGold)
    {
        return false;
    }

    const ItemDefinition *pItemDefinition = m_pItemTable->get(pWorldItem->item.objectDescriptionId);

    if (pItemDefinition == nullptr)
    {
        statusText = "Unavailable.";
        return false;
    }

    if (pWorldItem->item.identified || !ItemRuntime::requiresIdentification(*pItemDefinition))
    {
        statusText = "Already identified.";
        return false;
    }

    if (!ItemRuntime::canCharacterIdentifyItem(inspector, *pItemDefinition))
    {
        statusText = "Not skilled enough.";
        std::cout << "Item identify: inspector=\"" << inspector.name
                  << "\" owner=\"ground\" item=\"" << pItemDefinition->name
                  << "\" location=ground(" << worldItemIndex << ") result=failed status=\""
                  << statusText << "\"\n";
        return false;
    }

    pWorldItem->item.identified = true;
    statusText = "Identified " + ItemRuntime::displayName(pWorldItem->item, *pItemDefinition) + ".";
    std::cout << "Item identify: inspector=\"" << inspector.name
              << "\" owner=\"ground\" item=\"" << pItemDefinition->name
              << "\" location=ground(" << worldItemIndex << ") result=success status=\""
              << statusText << "\"\n";
    return true;
}

bool OutdoorWorldRuntime::tryRepairWorldItem(size_t worldItemIndex, const Character &inspector, std::string &statusText)
{
    statusText.clear();
    WorldItemState *pWorldItem = worldItemStateMutable(worldItemIndex);

    if (pWorldItem == nullptr || m_pItemTable == nullptr || pWorldItem->isGold)
    {
        return false;
    }

    const ItemDefinition *pItemDefinition = m_pItemTable->get(pWorldItem->item.objectDescriptionId);

    if (pItemDefinition == nullptr)
    {
        statusText = "Unavailable.";
        return false;
    }

    if (!pWorldItem->item.broken)
    {
        statusText = "Nothing to repair.";
        return false;
    }

    if (!ItemRuntime::canCharacterRepairItem(inspector, *pItemDefinition))
    {
        statusText = "Not skilled enough.";
        std::cout << "Item repair: inspector=\"" << inspector.name
                  << "\" owner=\"ground\" item=\"" << pItemDefinition->name
                  << "\" location=ground(" << worldItemIndex << ") result=failed status=\""
                  << statusText << "\"\n";
        return false;
    }

    pWorldItem->item.broken = false;
    pWorldItem->item.identified = true;
    statusText = "Repaired " + ItemRuntime::displayName(pWorldItem->item, *pItemDefinition) + ".";
    std::cout << "Item repair: inspector=\"" << inspector.name
              << "\" owner=\"ground\" item=\"" << pItemDefinition->name
              << "\" location=ground(" << worldItemIndex << ") result=success status=\""
              << statusText << "\"\n";
    return true;
}

size_t OutdoorWorldRuntime::projectileCount() const
{
    return projectileService().projectileCount();
}

const OutdoorWorldRuntime::ProjectileState *OutdoorWorldRuntime::projectileState(size_t projectileIndex) const
{
    return projectileService().projectileState(projectileIndex);
}

size_t OutdoorWorldRuntime::projectileImpactCount() const
{
    return projectileService().projectileImpactCount();
}

const OutdoorWorldRuntime::ProjectileImpactState *OutdoorWorldRuntime::projectileImpactState(size_t effectIndex) const
{
    return projectileService().projectileImpactState(effectIndex);
}

size_t OutdoorWorldRuntime::fireSpikeTrapCount() const
{
    return m_fireSpikeTraps.size();
}

const OutdoorWorldRuntime::FireSpikeTrapState *OutdoorWorldRuntime::fireSpikeTrapState(size_t trapIndex) const
{
    if (trapIndex >= m_fireSpikeTraps.size())
    {
        return nullptr;
    }

    return &m_fireSpikeTraps[trapIndex];
}

size_t OutdoorWorldRuntime::bloodSplatCount() const
{
    return m_bloodSplats.size();
}

const OutdoorWorldRuntime::BloodSplatState *OutdoorWorldRuntime::bloodSplatState(size_t splatIndex) const
{
    if (splatIndex >= m_bloodSplats.size())
    {
        return nullptr;
    }

    return &m_bloodSplats[splatIndex];
}

uint64_t OutdoorWorldRuntime::bloodSplatRevision() const
{
    return m_bloodSplatRevision;
}

void OutdoorWorldRuntime::addBloodSplat(uint32_t sourceActorId, float x, float y, float z, float radius)
{
    if (radius <= 0.0f)
    {
        return;
    }

    removeBloodSplat(sourceActorId);

    BloodSplatState splat = {};
    splat.sourceActorId = sourceActorId;
    splat.x = x;
    splat.y = y;
    splat.z = z;
    splat.radius = radius;
    bakeBloodSplatGeometry(splat);

    if (splat.vertices.empty())
    {
        return;
    }

    if (m_bloodSplats.size() >= MaxOutdoorBloodSplats)
    {
        m_bloodSplats.erase(m_bloodSplats.begin());
    }

    m_bloodSplats.push_back(splat);
    ++m_bloodSplatRevision;
}

void OutdoorWorldRuntime::spawnBloodSplatForActorIfNeeded(size_t actorIndex)
{
    if (actorIndex >= m_mapActors.size() || m_pMonsterTable == nullptr)
    {
        return;
    }

    MapActorState &actor = m_mapActors[actorIndex];

    if (actor.bloodSplatSpawned)
    {
        return;
    }

    const MonsterTable::MonsterStatsEntry *pStats = m_pMonsterTable->findStatsById(actor.monsterId);

    if (pStats == nullptr || !pStats->bloodSplatOnDeath)
    {
        return;
    }

    const float terrainZ =
        m_pOutdoorMapData != nullptr
            ? sampleOutdoorRenderedTerrainHeight(*m_pOutdoorMapData, actor.preciseX, actor.preciseY)
            : actor.preciseZ;
    const float supportZ = sampleSupportFloorHeight(
        actor.preciseX,
        actor.preciseY,
        actor.preciseZ + 256.0f,
        512.0f,
        24.0f);
    const float splatZ = std::max(terrainZ, supportZ);
    const float splatRadius = std::max(32.0f, static_cast<float>(actor.radius) * 1.5f);
    addBloodSplat(actor.actorId, actor.preciseX, actor.preciseY, splatZ, splatRadius);
    actor.bloodSplatSpawned = true;
}

void OutdoorWorldRuntime::bakeBloodSplatGeometry(BloodSplatState &splat) const
{
    splat.vertices.clear();

    if (splat.radius <= 0.0f)
    {
        return;
    }

    const float diameter = splat.radius * 2.0f;
    const float cellSize = diameter / static_cast<float>(BloodSplatGridResolution);
    const float cellHalfSize = cellSize * 0.5f;
    const float surfaceHeightTolerance =
        std::max(BloodSplatMinSurfaceHeightTolerance, splat.radius * 0.5f);

    splat.vertices.reserve(BloodSplatGridResolution * BloodSplatGridResolution * 12);

    const auto appendVertex =
        [&splat](const bx::Vec3 &position, float u, float v)
        {
            BloodSplatState::Vertex vertex = {};
            vertex.x = position.x;
            vertex.y = position.y;
            vertex.z = position.z;
            vertex.u = u;
            vertex.v = v;
            splat.vertices.push_back(vertex);
        };

    const auto sampleWorldPoint =
        [this, &splat, surfaceHeightTolerance](float x, float y, bx::Vec3 &point) -> bool
        {
            const float terrainZ =
                m_pOutdoorMapData != nullptr
                    ? sampleOutdoorRenderedTerrainHeight(*m_pOutdoorMapData, x, y)
                    : splat.z;
            const float supportZ = sampleSupportFloorHeight(
                x,
                y,
                splat.z + 256.0f,
                512.0f,
                24.0f);
            const float z = std::max(terrainZ, supportZ);

            if (std::abs(z - splat.z) > surfaceHeightTolerance)
            {
                return false;
            }

            point = {x, y, z + BloodSplatHeightOffset + 1.0f};
            return true;
        };

    for (size_t yIndex = 0; yIndex < BloodSplatGridResolution; ++yIndex)
    {
        const float v0 = static_cast<float>(yIndex) / static_cast<float>(BloodSplatGridResolution);
        const float v1 = static_cast<float>(yIndex + 1) / static_cast<float>(BloodSplatGridResolution);
        const float localY0 = (v0 - 0.5f) * diameter;
        const float localY1 = (v1 - 0.5f) * diameter;

        for (size_t xIndex = 0; xIndex < BloodSplatGridResolution; ++xIndex)
        {
            const float u0 = static_cast<float>(xIndex) / static_cast<float>(BloodSplatGridResolution);
            const float u1 = static_cast<float>(xIndex + 1) / static_cast<float>(BloodSplatGridResolution);
            const float localX0 = (u0 - 0.5f) * diameter;
            const float localX1 = (u1 - 0.5f) * diameter;
            const float localCenterX = (localX0 + localX1) * 0.5f;
            const float localCenterY = (localY0 + localY1) * 0.5f;
            const float nearestX = std::max(std::abs(localCenterX) - cellHalfSize, 0.0f);
            const float nearestY = std::max(std::abs(localCenterY) - cellHalfSize, 0.0f);

            if (nearestX * nearestX + nearestY * nearestY > splat.radius * splat.radius)
            {
                continue;
            }

            bx::Vec3 topLeft = {0.0f, 0.0f, 0.0f};
            bx::Vec3 topRight = {0.0f, 0.0f, 0.0f};
            bx::Vec3 bottomLeft = {0.0f, 0.0f, 0.0f};
            bx::Vec3 bottomRight = {0.0f, 0.0f, 0.0f};
            const float centerU = (u0 + u1) * 0.5f;
            const float centerV = (v0 + v1) * 0.5f;
            bx::Vec3 center = {0.0f, 0.0f, 0.0f};

            if (!sampleWorldPoint(splat.x + localX0, splat.y + localY0, topLeft)
                || !sampleWorldPoint(splat.x + localX1, splat.y + localY0, topRight)
                || !sampleWorldPoint(splat.x + localX0, splat.y + localY1, bottomLeft)
                || !sampleWorldPoint(splat.x + localX1, splat.y + localY1, bottomRight)
                || !sampleWorldPoint(splat.x + localCenterX, splat.y + localCenterY, center))
            {
                continue;
            }

            appendVertex(topLeft, u0, v0);
            appendVertex(topRight, u1, v0);
            appendVertex(center, centerU, centerV);

            appendVertex(topRight, u1, v0);
            appendVertex(bottomRight, u1, v1);
            appendVertex(center, centerU, centerV);

            appendVertex(bottomRight, u1, v1);
            appendVertex(bottomLeft, u0, v1);
            appendVertex(center, centerU, centerV);

            appendVertex(bottomLeft, u0, v1);
            appendVertex(topLeft, u0, v0);
            appendVertex(center, centerU, centerV);
        }
    }
}

void OutdoorWorldRuntime::removeBloodSplat(uint32_t sourceActorId)
{
    const size_t previousCount = m_bloodSplats.size();
    m_bloodSplats.erase(
        std::remove_if(
            m_bloodSplats.begin(),
            m_bloodSplats.end(),
            [sourceActorId](const BloodSplatState &splat)
            {
                return splat.sourceActorId == sourceActorId;
            }),
        m_bloodSplats.end());

    if (m_bloodSplats.size() != previousCount)
    {
        ++m_bloodSplatRevision;
    }
}

GameplayProjectileService &OutdoorWorldRuntime::projectileService()
{
    if (m_pGameplayProjectileService == nullptr)
    {
        return m_fallbackGameplayProjectileService;
    }

    return *m_pGameplayProjectileService;
}

const GameplayProjectileService &OutdoorWorldRuntime::projectileService() const
{
    if (m_pGameplayProjectileService == nullptr)
    {
        return m_fallbackGameplayProjectileService;
    }

    return *m_pGameplayProjectileService;
}

GameplayProjectileService::ProjectileImpactSpawnResult
OutdoorWorldRuntime::spawnProjectileImpactVisual(
    const ProjectileState &projectile,
    const GameplayProjectileService::ProjectileImpactVisualDefinition &definition,
    float x,
    float y,
    float z,
    bool centerVertically)
{
    if (m_pGameplayFxService != nullptr)
    {
        return m_pGameplayFxService->spawnProjectileImpactVisual(
            projectile,
            definition,
            x,
            y,
            z,
            centerVertically);
    }

    return projectileService().spawnProjectileImpactVisual(projectile, definition, x, y, z, centerVertically);
}

GameplayProjectileService::ProjectileImpactSpawnResult
OutdoorWorldRuntime::spawnWaterSplashImpactVisual(
    const GameplayProjectileService::ProjectileImpactVisualDefinition &definition,
    float x,
    float y,
    float z)
{
    if (m_pGameplayFxService != nullptr)
    {
        return m_pGameplayFxService->spawnWaterSplashImpactVisual(definition, x, y, z);
    }

    return projectileService().spawnWaterSplashImpactVisual(definition, x, y, z);
}

GameplayProjectileService::ProjectileImpactSpawnResult
OutdoorWorldRuntime::spawnImmediateSpellImpactVisual(
    const GameplayProjectileService::ProjectileImpactVisualDefinition &definition,
    int sourceSpellId,
    const std::string &sourceObjectName,
    const std::string &sourceObjectSpriteName,
    float x,
    float y,
    float z,
    bool centerVertically,
    bool freezeAnimation)
{
    if (m_pGameplayFxService != nullptr)
    {
        return m_pGameplayFxService->spawnImmediateSpellImpactVisual(
            definition,
            sourceSpellId,
            sourceObjectName,
            sourceObjectSpriteName,
            x,
            y,
            z,
            centerVertically,
            freezeAnimation);
    }

    return projectileService().spawnImmediateSpellImpactVisual(
        definition,
        sourceSpellId,
        sourceObjectName,
        sourceObjectSpriteName,
        x,
        y,
        z,
        centerVertically,
        freezeAnimation);
}

bool OutdoorWorldRuntime::summonMonsters(
    uint32_t typeIndexInMapStats,
    uint32_t level,
    uint32_t count,
    int32_t x,
    int32_t y,
    int32_t z,
    uint32_t group,
    uint32_t uniqueNameId
)
{
    if (m_pMonsterTable == nullptr || typeIndexInMapStats < 1 || typeIndexInMapStats > 3 || count == 0)
    {
        return false;
    }

    return spawnEncounterFromResolvedData(
        static_cast<int>(typeIndexInMapStats),
        tierLetterForSummonLevel(level),
        count,
        static_cast<float>(x),
        static_cast<float>(y),
        static_cast<float>(z),
        128,
        0,
        group,
        uniqueNameId,
        false,
        static_cast<size_t>(-1),
        false);
}

bool OutdoorWorldRuntime::summonEventItem(
    uint32_t itemId,
    int32_t x,
    int32_t y,
    int32_t z,
    int32_t speed,
    uint32_t count,
    bool randomRotate
)
{
    if (m_pObjectTable == nullptr || itemId == 0 || count == 0)
    {
        return false;
    }

    uint16_t objectDescriptionId = 0;
    uint16_t objectSpriteId = 0;
    uint16_t objectSpriteFrameIndex = 0;
    uint16_t objectFlags = 0;
    uint16_t radius = 0;
    uint16_t height = 0;
    uint32_t lifetimeTicks = 0;
    std::string objectName;
    std::string objectSpriteName;
    const ItemDefinition *pItemDefinition = nullptr;
    bool payloadResolved = false;

    const std::optional<uint16_t> descriptionId =
        m_pObjectTable->findDescriptionIdByObjectId(static_cast<int16_t>(itemId));

    if (descriptionId)
    {
        const ObjectEntry *pObjectEntry = m_pObjectTable->get(*descriptionId);

        if (pObjectEntry != nullptr && (pObjectEntry->flags & ObjectDescNoSprite) == 0 && pObjectEntry->spriteId != 0)
        {
            objectDescriptionId = *descriptionId;
            objectSpriteId = pObjectEntry->spriteId;
            objectSpriteFrameIndex = resolveRuntimeSpriteFrameIndex(
                m_pProjectileSpriteFrameTable,
                pObjectEntry->spriteId,
                pObjectEntry->spriteName);
            objectFlags = pObjectEntry->flags;
            radius = static_cast<uint16_t>(std::max<int16_t>(0, pObjectEntry->radius));
            height = static_cast<uint16_t>(std::max<int16_t>(0, pObjectEntry->height));
            lifetimeTicks = pObjectEntry->lifetimeTicks > 0 ? pObjectEntry->lifetimeTicks : 0;
            objectName = pObjectEntry->internalName;
            objectSpriteName = pObjectEntry->spriteName;
            payloadResolved = true;

            if (m_pItemTable != nullptr)
            {
                pItemDefinition = m_pItemTable->findBySpriteIndex(static_cast<uint16_t>(itemId));
            }
        }
    }

    if (!payloadResolved && m_pItemTable != nullptr)
    {
        pItemDefinition = m_pItemTable->get(itemId);

        if (pItemDefinition != nullptr)
        {
            if (resolveWorldItemVisual(
                    itemId,
                    objectDescriptionId,
                    objectSpriteId,
                    objectSpriteFrameIndex,
                    objectFlags,
                    radius,
                    height,
                    objectName,
                    objectSpriteName))
            {
                payloadResolved = true;
            }
            else
            {
                pItemDefinition = nullptr;
            }
        }
    }

    if (!payloadResolved)
    {
        std::cout << "Event summon unresolved payload=" << itemId << '\n';
        return false;
    }

    if (lifetimeTicks == 0)
    {
        const ObjectEntry *pObjectEntry = m_pObjectTable->get(objectDescriptionId);

        if (pObjectEntry != nullptr)
        {
            lifetimeTicks = pObjectEntry->lifetimeTicks > 0 ? pObjectEntry->lifetimeTicks : 0;
        }
    }

    bool spawnedAny = false;
    const float baseX = static_cast<float>(x);
    const float baseY = static_cast<float>(y);
    const float baseZ = static_cast<float>(z);

    for (uint32_t itemIndex = 0; itemIndex < count; ++itemIndex)
    {
        WorldItemState worldItem = {};
        worldItem.worldItemId = m_nextWorldItemId++;
        worldItem.objectDescriptionId = objectDescriptionId;
        worldItem.objectSpriteId = objectSpriteId;
        worldItem.objectSpriteFrameIndex = objectSpriteFrameIndex;
        worldItem.objectFlags = objectFlags;
        worldItem.radius = radius;
        worldItem.height = height;
        worldItem.objectName = objectName;
        worldItem.objectSpriteName = objectSpriteName;
        worldItem.attributes = SpriteAttrTemporary;
        worldItem.x = baseX;
        worldItem.y = baseY;
        worldItem.z = baseZ;
        worldItem.initialX = baseX;
        worldItem.initialY = baseY;
        worldItem.initialZ = baseZ;
        worldItem.lifetimeTicks = lifetimeTicks;

        if (pItemDefinition != nullptr)
        {
            worldItem.item.objectDescriptionId = pItemDefinition->itemId;
            worldItem.item.quantity = 1;
            worldItem.item.width = pItemDefinition->inventoryWidth;
            worldItem.item.height = pItemDefinition->inventoryHeight;
            worldItem.goldAmount = isGoldHeapItemId(worldItem.item.objectDescriptionId) ? 1u : 0u;
            worldItem.isGold = worldItem.goldAmount > 0 && isGoldHeapItemId(worldItem.item.objectDescriptionId);
        }

        if (speed > 0)
        {
            const float angleRadians = randomRotate
                ? (Pi * 2.0f * static_cast<float>((itemId + itemIndex * 37u) % 2048u) / 2048.0f)
                : 0.0f;
            worldItem.velocityX = std::cos(angleRadians) * speed;
            worldItem.velocityY = std::sin(angleRadians) * speed;
            worldItem.velocityZ = 0.0f;
        }

        m_worldItems.push_back(std::move(worldItem));
        spawnedAny = true;
    }

    return spawnedAny;
}

bool OutdoorWorldRuntime::summonFriendlyMonsterById(
    int16_t monsterId,
    uint32_t count,
    float durationSeconds,
    float x,
    float y,
    float z)
{
    if (m_pMonsterTable == nullptr || count == 0)
    {
        return false;
    }

    const MonsterTable::MonsterStatsEntry *pStats = m_pMonsterTable->findStatsById(monsterId);

    if (pStats == nullptr)
    {
        return false;
    }

    bool spawnedAny = false;

    for (uint32_t summonIndex = 0; summonIndex < count; ++summonIndex)
    {
        const MonsterEntry *pMonsterEntry = resolveMonsterEntry(*m_pMonsterTable, monsterId, pStats);
        const uint16_t actorRadius = pMonsterEntry != nullptr ? std::max<uint16_t>(pMonsterEntry->radius, 32) : 32;
        const bx::Vec3 spawnPosition = calculateEncounterSpawnPosition(
            x,
            y,
            z,
            128,
            actorRadius,
            summonIndex);
        MapActorState actor = buildSpawnedMapActorState(
            *m_pMonsterTable,
            m_pOutdoorMapData,
            *pStats,
            m_nextActorId++,
            0,
            false,
            static_cast<size_t>(-1),
            0,
            0,
            spawnPosition.x,
            spawnPosition.y,
            spawnPosition.z);

        const auto visualIt = m_monsterVisualsById.find(actor.monsterId);

        if (visualIt != m_monsterVisualsById.end())
        {
            applyMonsterVisualState(actor, visualIt->second);
        }
        else if (m_pActorSpriteFrameTable != nullptr)
        {
            const MonsterVisualState visualState = buildMonsterVisualState(*m_pActorSpriteFrameTable, pMonsterEntry);

            if (visualState.spriteFrameIndex != 0)
            {
                m_monsterVisualsById[actor.monsterId] = visualState;
                applyMonsterVisualState(actor, visualState);
            }
        }

        actor.controlMode = ActorControlMode::Enslaved;
        actor.controlRemainingSeconds = std::max(durationSeconds, 1.0f);
        actor.hostileToParty = false;
        actor.hasDetectedParty = false;
        m_mapActors.push_back(std::move(actor));
        spawnedAny = true;
    }

    return spawnedAny;
}

bool OutdoorWorldRuntime::checkMonstersKilled(
    uint32_t checkType,
    uint32_t id,
    uint32_t count,
    bool invisibleAsDead
) const
{
    int totalActors = 0;
    int defeatedActors = 0;

    auto countMonster =
        [&](bool matches, bool isDead, bool isInvisible)
        {
            if (!matches)
            {
                return;
            }

            ++totalActors;

            if (isDead || (invisibleAsDead && isInvisible))
            {
                ++defeatedActors;
            }
        };

    for (const MapActorState &actor : m_mapActors)
    {
        bool matches = false;

        switch (checkType)
        {
            case static_cast<uint32_t>(EvtActorKillCheck::Any):
                matches = true;
                break;

            case static_cast<uint32_t>(EvtActorKillCheck::Group):
                matches = actor.group == id;
                break;

            case static_cast<uint32_t>(EvtActorKillCheck::MonsterId):
                matches = actor.monsterId == static_cast<int16_t>(id);
                break;

            case static_cast<uint32_t>(EvtActorKillCheck::ActorIdOe):
            case static_cast<uint32_t>(EvtActorKillCheck::ActorIdMm8):
                matches = actor.actorId == id;
                break;

            default:
                break;
        }

        countMonster(matches, actor.isDead || actor.currentHp <= 0, actor.isInvisible);
    }

    if (count > 0)
    {
        return defeatedActors >= static_cast<int>(count);
    }

    return totalActors == defeatedActors;
}

const EventRuntimeState::PendingMapMove *OutdoorWorldRuntime::pendingMapMove() const
{
    if (!m_eventRuntimeState || !m_eventRuntimeState->pendingMapMove)
    {
        return nullptr;
    }

    return &*m_eventRuntimeState->pendingMapMove;
}

std::optional<EventRuntimeState::PendingMapMove> OutdoorWorldRuntime::consumePendingMapMove()
{
    if (!m_eventRuntimeState || !m_eventRuntimeState->pendingMapMove)
    {
        return std::nullopt;
    }

    std::optional<EventRuntimeState::PendingMapMove> result = std::move(m_eventRuntimeState->pendingMapMove);
    m_eventRuntimeState->pendingMapMove.reset();
    return result;
}

Party *OutdoorWorldRuntime::party()
{
    return m_pParty;
}

const Party *OutdoorWorldRuntime::party() const
{
    return m_pParty;
}

float OutdoorWorldRuntime::partyX() const
{
    return m_pPartyRuntime != nullptr ? m_pPartyRuntime->partyX() : 0.0f;
}

float OutdoorWorldRuntime::partyY() const
{
    return m_pPartyRuntime != nullptr ? m_pPartyRuntime->partyY() : 0.0f;
}

float OutdoorWorldRuntime::partyFootZ() const
{
    return m_pPartyRuntime != nullptr ? m_pPartyRuntime->partyFootZ() : 0.0f;
}

void OutdoorWorldRuntime::syncSpellMovementStatesFromPartyBuffs()
{
    if (m_pPartyRuntime != nullptr)
    {
        m_pPartyRuntime->syncSpellMovementStatesFromPartyBuffs();
    }
}

void OutdoorWorldRuntime::requestPartyJump()
{
    if (m_pPartyRuntime != nullptr)
    {
        m_pPartyRuntime->requestJump();
    }
}

void OutdoorWorldRuntime::setAlwaysRunEnabled(bool enabled)
{
    if (m_pPartyRuntime != nullptr)
    {
        m_pPartyRuntime->setRunning(enabled);
    }
}

void OutdoorWorldRuntime::cancelPendingMapTransition()
{
    if (m_pInteractionView != nullptr)
    {
        OutdoorInteractionController::cancelPendingMapTransition(*m_pInteractionView);
        return;
    }

    if (m_pOutdoorMapData == nullptr || m_pPartyRuntime == nullptr)
    {
        return;
    }

    const MapBounds &bounds = m_map.outdoorBounds;

    if (!bounds.enabled)
    {
        return;
    }

    constexpr float CancelClampInset = 1.0f;
    const OutdoorMoveState &moveState = m_pPartyRuntime->movementState();
    const float clampedX = std::clamp(
        moveState.x,
        static_cast<float>(bounds.minX) + CancelClampInset,
        static_cast<float>(bounds.maxX) - CancelClampInset);
    const float clampedY = std::clamp(
        moveState.y,
        static_cast<float>(bounds.minY) + CancelClampInset,
        static_cast<float>(bounds.maxY) - CancelClampInset);

    if (clampedX == moveState.x && clampedY == moveState.y)
    {
        return;
    }

    m_pPartyRuntime->teleportTo(clampedX, clampedY, moveState.footZ);
}

bool OutdoorWorldRuntime::executeNpcTopicEvent(uint16_t eventId, size_t &previousMessageCount)
{
    return m_pInteractionView != nullptr
        && OutdoorInteractionController::executeNpcTopicEvent(*m_pInteractionView, eventId, previousMessageCount);
}

const MapDeltaData *OutdoorWorldRuntime::mapDeltaData() const
{
    return m_pOutdoorMapDeltaData;
}

EventRuntimeState *OutdoorWorldRuntime::eventRuntimeState()
{
    if (!m_eventRuntimeState)
    {
        return nullptr;
    }

    return &*m_eventRuntimeState;
}

bool OutdoorWorldRuntime::castEventSpell(
    uint32_t spellId,
    uint32_t skillLevel,
    uint32_t skillMastery,
    int32_t fromX,
    int32_t fromY,
    int32_t fromZ,
    int32_t toX,
    int32_t toY,
    int32_t toZ
)
{
    if (m_pParty != nullptr
        && (tryApplyEventPartyBuff(*m_pParty, spellId, skillLevel, skillMastery)
            || tryApplyEventCharacterBuff(*m_pParty, spellId, skillLevel, skillMastery)))
    {
        if (m_eventRuntimeState)
        {
            EventRuntimeState::SpellFxRequest request = {};
            request.spellId = spellId;
            request.memberIndices = buildAllPartyMemberIndices(*m_pParty);
            m_eventRuntimeState->spellFxRequests.push_back(std::move(request));
        }

        return true;
    }

    SpellCastRequest request = {};
    request.sourceKind = RuntimeSpellSourceKind::Event;
    request.sourceId = EventSpellSourceId;
    request.ability = MonsterAttackAbility::Spell1;
    request.spellId = spellId;
    request.skillLevel = skillLevel;
    request.skillMastery = static_cast<uint32_t>(normalizeEventSkillMastery(skillMastery));
    request.sourceX = static_cast<float>(fromX);
    request.sourceY = static_cast<float>(fromY);
    request.sourceZ = static_cast<float>(fromZ);
    request.targetX = static_cast<float>(toX);
    request.targetY = static_cast<float>(toY);
    request.targetZ = static_cast<float>(toZ);
    return castSpell(request);
}

bool OutdoorWorldRuntime::castPartySpell(const SpellCastRequest &request)
{
    if (request.sourceKind != RuntimeSpellSourceKind::Party)
    {
        return false;
    }

    return castSpell(request);
}

bool OutdoorWorldRuntime::castPartySpellProjectile(const GameplayPartySpellProjectileRequest &request)
{
    SpellCastRequest worldRequest = {};
    worldRequest.sourceKind = RuntimeSpellSourceKind::Party;
    worldRequest.sourceId = request.casterMemberIndex + 1;
    worldRequest.sourcePartyMemberIndex = request.casterMemberIndex;
    worldRequest.ability = MonsterAttackAbility::Spell1;
    worldRequest.spellId = request.spellId;
    worldRequest.skillLevel = request.skillLevel;
    worldRequest.skillMastery = static_cast<uint32_t>(request.skillMastery);
    worldRequest.damage = request.damage;
    worldRequest.attackBonus = 0;
    worldRequest.useActorHitChance = false;
    worldRequest.sourceX = request.sourceX;
    worldRequest.sourceY = request.sourceY;
    worldRequest.sourceZ = request.sourceZ;
    worldRequest.targetX = request.targetX;
    worldRequest.targetY = request.targetY;
    worldRequest.targetZ = request.targetZ;
    return castPartySpell(worldRequest);
}

bool OutdoorWorldRuntime::spawnPartyProjectile(const PartyProjectileRequest &request)
{
    ResolvedProjectileDefinition definition = {};

    if (!resolveObjectProjectileDefinition(
            static_cast<int>(request.objectId),
            static_cast<int>(request.impactObjectId),
            definition))
    {
        return false;
    }

    const uint16_t objectSpriteFrameIndex = resolveRuntimeSpriteFrameIndex(
        m_pProjectileSpriteFrameTable,
        definition.objectSpriteId,
        definition.objectSpriteName);
    GameplayProjectileService::ProjectileSpawnRequest spawnRequest = {};
    spawnRequest.sourceKind = ProjectileState::SourceKind::Party;
    spawnRequest.sourceId = request.sourcePartyMemberIndex + 1;
    spawnRequest.sourcePartyMemberIndex = request.sourcePartyMemberIndex;
    spawnRequest.definition = buildGameplayProjectileDefinition(definition, objectSpriteFrameIndex);
    spawnRequest.damage = request.damage;
    spawnRequest.attackBonus = request.attackBonus;
    spawnRequest.useActorHitChance = request.useActorHitChance;
    spawnRequest.sourceX = request.sourceX;
    spawnRequest.sourceY = request.sourceY;
    spawnRequest.sourceZ = request.sourceZ;
    spawnRequest.targetX = request.targetX;
    spawnRequest.targetY = request.targetY;
    spawnRequest.targetZ = request.targetZ;
    spawnRequest.spawnForwardOffset = PartyCollisionRadius;
    const GameplayProjectileService::ProjectileSpawnResult spawnResult =
        projectileService().spawnProjectile(spawnRequest);
    const GameplayProjectileService::ProjectileSpawnEffects spawnEffects =
        projectileService().buildProjectileSpawnEffects(spawnResult, false);
    return applyProjectileSpawnEffects(
        spawnResult,
        spawnEffects,
        "party",
        "party_projectile_zero_distance");
}

void OutdoorWorldRuntime::startGameplayScreenOverlay(uint32_t colorAbgr, float durationSeconds, float peakAlpha)
{
    m_gameplayOverlayColorAbgr = colorAbgr;
    m_gameplayOverlayDurationSeconds = std::max(durationSeconds, 0.0f);
    m_gameplayOverlayRemainingSeconds = m_gameplayOverlayDurationSeconds;
    m_gameplayOverlayPeakAlpha = std::clamp(peakAlpha, 0.0f, 1.0f);
    m_atmosphereState.gameplayOverlayColorAbgr = m_gameplayOverlayColorAbgr;
    m_atmosphereState.gameplayOverlayAlpha = 0.0f;
}

bool OutdoorWorldRuntime::tryStartArmageddon(
    size_t casterMemberIndex,
    uint32_t skillLevel,
    SkillMastery skillMastery,
    std::string &failureText)
{
    failureText.clear();

    if (m_pParty == nullptr)
    {
        failureText = "Spell failed";
        return false;
    }

    if (isArmageddonActive())
    {
        failureText = "Armageddon already active";
        return false;
    }

    Character *pCaster = m_pParty->member(casterMemberIndex);

    if (pCaster == nullptr)
    {
        failureText = "Spell failed";
        return false;
    }

    const uint8_t castLimit = skillMastery == SkillMastery::Grandmaster ? 4 : 3;

    if (pCaster->armageddonCastsToday >= castLimit)
    {
        failureText = "No Armageddon casts left today";
        return false;
    }

    m_armageddonState.remainingSeconds = ArmageddonDurationSeconds;
    m_armageddonState.skillLevel = skillLevel;
    m_armageddonState.skillMastery = skillMastery;
    m_armageddonState.casterMemberIndex = static_cast<uint32_t>(casterMemberIndex);
    m_armageddonState.shakeStepsRemaining = ArmageddonShakeStepCount;
    ++m_armageddonState.shakeSequence;
    m_armageddonState.cameraShakeYawRadians = 0.0f;
    m_armageddonState.cameraShakePitchRadians = 0.0f;
    ++pCaster->armageddonCastsToday;
    return true;
}

bool OutdoorWorldRuntime::canActivateWorldHit(
    const GameplayWorldHit &hit,
    GameplayInteractionMethod interactionMethod) const
{
    if (m_pInteractionView == nullptr)
    {
        return false;
    }

    const OutdoorInteractionController::InteractionInputMethod outdoorMethod =
        interactionMethod == GameplayInteractionMethod::Keyboard
            ? OutdoorInteractionController::InteractionInputMethod::Keyboard
            : OutdoorInteractionController::InteractionInputMethod::Mouse;

    return OutdoorInteractionController::canDispatchWorldActivation(*m_pInteractionView, hit, outdoorMethod);
}

bool OutdoorWorldRuntime::activateWorldHit(const GameplayWorldHit &hit)
{
    if (m_pInteractionView == nullptr)
    {
        return false;
    }

    return OutdoorInteractionController::dispatchWorldActivation(*m_pInteractionView, hit);
}

GameplayPendingSpellWorldTargetFacts OutdoorWorldRuntime::pickPendingSpellWorldTarget(
    const GameplayWorldPickRequest &request)
{
    if (m_pInteractionView == nullptr || m_pOutdoorMapData == nullptr)
    {
        return {};
    }

    return OutdoorInteractionController::pickPendingSpellWorldTarget(
        *m_pInteractionView,
        *m_pOutdoorMapData,
        request);
}

GameplayWorldHit OutdoorWorldRuntime::pickKeyboardInteractionTarget(const GameplayWorldPickRequest &request)
{
    if (m_pInteractionView == nullptr || m_pOutdoorMapData == nullptr)
    {
        return {};
    }

    return OutdoorInteractionController::pickKeyboardInteractionTarget(
        *m_pInteractionView,
        *m_pOutdoorMapData,
        request);
}

GameplayWorldHit OutdoorWorldRuntime::pickHeldItemWorldTarget(const GameplayWorldPickRequest &request)
{
    if (m_pInteractionView == nullptr || m_pOutdoorMapData == nullptr)
    {
        return {};
    }

    return OutdoorInteractionController::pickHeldItemWorldTarget(
        *m_pInteractionView,
        *m_pOutdoorMapData,
        request);
}

GameplayWorldHit OutdoorWorldRuntime::pickMouseInteractionTarget(const GameplayWorldPickRequest &request)
{
    if (m_pInteractionView == nullptr || m_pOutdoorMapData == nullptr)
    {
        return {};
    }

    return OutdoorInteractionController::pickCurrentInteractionTarget(
        *m_pInteractionView,
        *m_pOutdoorMapData,
        request);
}

GameplayWorldHoverCacheState OutdoorWorldRuntime::worldHoverCacheState() const
{
    if (m_pInteractionView == nullptr)
    {
        return {};
    }

    return OutdoorInteractionController::worldHoverCacheState(*m_pInteractionView);
}

GameplayHoverStatusPayload OutdoorWorldRuntime::refreshWorldHover(const GameplayWorldHoverRequest &request)
{
    if (m_pInteractionView == nullptr || m_pOutdoorMapData == nullptr)
    {
        return {};
    }

    return OutdoorInteractionController::refreshWorldHover(*m_pInteractionView, *m_pOutdoorMapData, request);
}

GameplayHoverStatusPayload OutdoorWorldRuntime::readCachedWorldHover()
{
    if (m_pInteractionView == nullptr)
    {
        return {};
    }

    return OutdoorInteractionController::readCachedWorldHover(*m_pInteractionView);
}

void OutdoorWorldRuntime::clearWorldHover()
{
    if (m_pInteractionView != nullptr)
    {
        OutdoorInteractionController::clearWorldHover(*m_pInteractionView);
    }
}

bool OutdoorWorldRuntime::canUseHeldItemOnWorld(const GameplayWorldHit &hit) const
{
    return canActivateWorldHit(hit, GameplayInteractionMethod::Mouse);
}

bool OutdoorWorldRuntime::useHeldItemOnWorld(const GameplayWorldHit &hit)
{
    return activateWorldHit(hit);
}

void OutdoorWorldRuntime::applyPendingSpellCastWorldEffects(const PartySpellCastResult &castResult)
{
    if (m_pParticleSystem == nullptr)
    {
        return;
    }

    OutdoorFxRuntime::triggerPartySpellFx(*m_pParticleSystem, castResult);
}

bool OutdoorWorldRuntime::dropHeldItemToWorld(const GameplayHeldItemDropRequest &request)
{
    return spawnWorldItem(
        request.item,
        request.sourceX,
        request.sourceY,
        request.sourceZ,
        request.yawRadians);
}

bool OutdoorWorldRuntime::tryGetGameplayMinimapState(GameplayMinimapState &state) const
{
    state = {};

    if (m_map.fileName.empty() || m_pPartyRuntime == nullptr)
    {
        return false;
    }

    const Party &runtimeParty = m_pPartyRuntime->party();
    const PartyBuffState *pWizardEyeBuff = runtimeParty.partyBuff(PartyBuffId::WizardEye);
    const SkillMastery wizardEyeMastery =
        pWizardEyeBuff != nullptr ? pWizardEyeBuff->skillMastery : SkillMastery::None;
    const OutdoorMoveState &moveState = m_pPartyRuntime->movementState();

    state.textureName = toLowerCopy(std::filesystem::path(m_map.fileName).stem().string());
    state.zoom = 512.0f;
    state.partyU = std::clamp((moveState.x + 32768.0f) / 65536.0f, 0.0f, 1.0f);
    state.partyV = std::clamp((32768.0f - moveState.y) / 65536.0f, 0.0f, 1.0f);
    state.wizardEyeActive = pWizardEyeBuff != nullptr;
    state.wizardEyeShowsExpertObjects = wizardEyeMastery >= SkillMastery::Expert;
    state.wizardEyeShowsMasterDecorations = wizardEyeMastery >= SkillMastery::Master;
    return true;
}

void OutdoorWorldRuntime::collectGameplayMinimapLines(std::vector<GameplayMinimapLineState> &lines)
{
    lines.clear();
}

void OutdoorWorldRuntime::collectGameplayMinimapMarkers(std::vector<GameplayMinimapMarkerState> &markers) const
{
    markers.clear();

    GameplayMinimapState minimapState = {};

    if (!tryGetGameplayMinimapState(minimapState) || !minimapState.wizardEyeActive)
    {
        return;
    }

    for (size_t actorIndex = 0; actorIndex < mapActorCount(); ++actorIndex)
    {
        const MapActorState *pActor = mapActorState(actorIndex);

        if (pActor == nullptr || pActor->isInvisible)
        {
            continue;
        }

        if (!pActor->isDead && !pActor->hasDetectedParty)
        {
            continue;
        }

        GameplayMinimapMarkerState marker = {};
        marker.type = pActor->isDead
            ? GameplayMinimapMarkerType::CorpseActor
            : pActor->hostileToParty ? GameplayMinimapMarkerType::HostileActor : GameplayMinimapMarkerType::FriendlyActor;
        marker.u = std::clamp((static_cast<float>(pActor->x) + 32768.0f) / 65536.0f, 0.0f, 1.0f);
        marker.v = std::clamp((32768.0f - static_cast<float>(pActor->y)) / 65536.0f, 0.0f, 1.0f);
        markers.push_back(marker);
    }

    if (minimapState.wizardEyeShowsExpertObjects)
    {
        for (size_t worldItemIndex = 0; worldItemIndex < worldItemCount(); ++worldItemIndex)
        {
            const WorldItemState *pWorldItem = worldItemState(worldItemIndex);

            if (pWorldItem == nullptr)
            {
                continue;
            }

            GameplayMinimapMarkerState marker = {};
            marker.type = GameplayMinimapMarkerType::WorldItem;
            marker.u = std::clamp((pWorldItem->x + 32768.0f) / 65536.0f, 0.0f, 1.0f);
            marker.v = std::clamp((32768.0f - pWorldItem->y) / 65536.0f, 0.0f, 1.0f);
            markers.push_back(marker);
        }

        for (size_t projectileIndex = 0; projectileIndex < projectileCount(); ++projectileIndex)
        {
            const ProjectileState *pProjectile = projectileState(projectileIndex);

            if (pProjectile == nullptr)
            {
                continue;
            }

            GameplayMinimapMarkerState marker = {};
            marker.type = GameplayMinimapMarkerType::Projectile;
            marker.u = std::clamp((pProjectile->x + 32768.0f) / 65536.0f, 0.0f, 1.0f);
            marker.v = std::clamp((32768.0f - pProjectile->y) / 65536.0f, 0.0f, 1.0f);
            markers.push_back(marker);
        }
    }

    if (minimapState.wizardEyeShowsMasterDecorations
        && m_pOutdoorMapDeltaData != nullptr
        && m_pOutdoorMapData != nullptr)
    {
        for (size_t entityIndex = 0; entityIndex < m_pOutdoorMapData->entities.size(); ++entityIndex)
        {
            if (entityIndex >= m_pOutdoorMapDeltaData->decorationFlags.size())
            {
                continue;
            }

            if ((m_pOutdoorMapDeltaData->decorationFlags[entityIndex] & 0x0008) == 0)
            {
                continue;
            }

            if (m_eventRuntimeState)
            {
                const auto overrideIterator =
                    m_eventRuntimeState->spriteOverrides.find(static_cast<uint32_t>(entityIndex));

                if (overrideIterator != m_eventRuntimeState->spriteOverrides.end() && overrideIterator->second.hidden)
                {
                    continue;
                }
            }

            const OutdoorEntity &entity = m_pOutdoorMapData->entities[entityIndex];
            GameplayMinimapMarkerState marker = {};
            marker.type = GameplayMinimapMarkerType::Decoration;
            marker.u = std::clamp((static_cast<float>(entity.x) + 32768.0f) / 65536.0f, 0.0f, 1.0f);
            marker.v = std::clamp((32768.0f - static_cast<float>(entity.y)) / 65536.0f, 0.0f, 1.0f);
            markers.push_back(marker);
        }
    }
}

bool OutdoorWorldRuntime::isArmageddonActive() const
{
    return m_armageddonState.active();
}

float OutdoorWorldRuntime::armageddonCameraShakeYawRadians() const
{
    return m_armageddonState.cameraShakeYawRadians;
}

float OutdoorWorldRuntime::armageddonCameraShakePitchRadians() const
{
    return m_armageddonState.cameraShakePitchRadians;
}

void OutdoorWorldRuntime::updateArmageddon(float deltaSeconds, float partyX, float partyY, float partyZ)
{
    if (!m_armageddonState.active())
    {
        m_armageddonState.cameraShakeYawRadians = 0.0f;
        m_armageddonState.cameraShakePitchRadians = 0.0f;
        return;
    }

    m_armageddonState.remainingSeconds = std::max(0.0f, m_armageddonState.remainingSeconds - deltaSeconds);

    if (m_armageddonState.shakeStepsRemaining > 0)
    {
        std::mt19937 rng(
            static_cast<uint32_t>(m_mapId) * 2654435761u
            ^ (m_armageddonState.shakeSequence + 1u) * 2246822519u
            ^ m_armageddonState.shakeStepsRemaining * 3266489917u);
        std::uniform_real_distribution<float> yawDistribution(-ArmageddonShakeYawRadians, ArmageddonShakeYawRadians);
        std::uniform_real_distribution<float> pitchDistribution(-ArmageddonShakePitchRadians, ArmageddonShakePitchRadians);
        m_armageddonState.cameraShakeYawRadians = yawDistribution(rng);
        m_armageddonState.cameraShakePitchRadians = pitchDistribution(rng);
        --m_armageddonState.shakeStepsRemaining;
    }
    else
    {
        m_armageddonState.cameraShakeYawRadians = 0.0f;
        m_armageddonState.cameraShakePitchRadians = 0.0f;
    }

    if (m_armageddonState.remainingSeconds > 0.0f)
    {
        return;
    }

    resolveArmageddonDetonation(partyX, partyY, partyZ);
    m_armageddonState = {};
}

void OutdoorWorldRuntime::resolveArmageddonDetonation(float partyX, float partyY, float partyZ)
{
    if (m_pParty == nullptr)
    {
        return;
    }

    const int armageddonDamage = 50 + m_armageddonState.skillLevel;
    const uint32_t sourceMemberIndex = m_armageddonState.casterMemberIndex;

    for (size_t actorIndex = 0; actorIndex < m_mapActors.size(); ++actorIndex)
    {
        MapActorState &actor = m_mapActors[actorIndex];

        if (isActorUnavailableForCombat(actor))
        {
            continue;
        }

        const int beforeHp = actor.currentHp;
        const bool applied = applyPartyAttackToMapActor(actorIndex, armageddonDamage, partyX, partyY, partyZ);

        if (!applied)
        {
            continue;
        }

        if (m_pGameplayCombatController != nullptr)
        {
            m_pGameplayCombatController->recordPartyProjectileActorImpact(
                0,
                sourceMemberIndex,
                actor.actorId,
                armageddonDamage,
                spellIdValue(SpellId::Armageddon),
                true,
                beforeHp > 0 && actor.currentHp <= 0);
        }

        if (actor.currentHp > 0)
        {
            actor.stunRemainingSeconds = std::max(actor.stunRemainingSeconds, 1.0f);
            actor.aiState = ActorAiState::Stunned;
            actor.animation = ActorAnimation::GotHit;
            actor.actionSeconds = std::max(actor.actionSeconds, actor.stunRemainingSeconds);
        }
    }

    for (size_t memberIndex = 0; memberIndex < m_pParty->members().size(); ++memberIndex)
    {
        Character *pMember = m_pParty->member(memberIndex);

        if (pMember == nullptr
            || pMember->conditions.test(static_cast<size_t>(CharacterCondition::Dead))
            || pMember->conditions.test(static_cast<size_t>(CharacterCondition::Petrified))
            || pMember->conditions.test(static_cast<size_t>(CharacterCondition::Eradicated)))
        {
            continue;
        }

        m_pParty->applyDamageToMember(memberIndex, armageddonDamage, "");
    }

    startGameplayScreenOverlay(makeAbgr(255, 56, 24), 0.6f, 0.72f);
}

const EventRuntimeState *OutdoorWorldRuntime::eventRuntimeState() const
{
    if (!m_eventRuntimeState)
    {
        return nullptr;
    }

    return &*m_eventRuntimeState;
}
}
