#pragma once

#include "game/party/Party.h"
#include "game/party/SkillData.h"

#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
class OutdoorPartyRuntime;
class OutdoorWorldRuntime;
class SpellTable;

enum class PartySpellCastTargetKind : uint8_t
{
    None = 0,
    Actor,
    Character,
    ActorOrCharacter,
    GroundPoint,
    InventoryItem,
    UtilityUi,
};

enum class PartySpellCastEffectKind : uint8_t
{
    Unsupported = 0,
    Projectile,
    MultiProjectile,
    PartyBuff,
    CharacterBuff,
    CharacterRestore,
    PartyRestore,
    ActorEffect,
    AreaEffect,
    Jump,
    UtilityUi,
};

enum class PartySpellCastStatus : uint8_t
{
    Succeeded = 0,
    InvalidCaster,
    InvalidSpell,
    NotSkilledEnough,
    NotEnoughSpellPoints,
    NeedActorTarget,
    NeedCharacterTarget,
    NeedActorOrCharacterTarget,
    NeedGroundPoint,
    NeedInventoryItemTarget,
    NeedUtilityUi,
    Unsupported,
    Failed,
};

struct PartySpellCastRequest
{
    size_t casterMemberIndex = 0;
    uint32_t spellId = 0;
    bool quickCast = false;
    std::optional<size_t> targetActorIndex;
    std::optional<size_t> targetCharacterIndex;
    bool hasTargetPoint = false;
    float targetX = 0.0f;
    float targetY = 0.0f;
    float targetZ = 0.0f;
    uint32_t skillLevelOverride = 0;
    SkillMastery skillMasteryOverride = SkillMastery::None;
    bool spendMana = true;
    bool applyRecovery = true;
};

struct PartySpellCastResult
{
    PartySpellCastStatus status = PartySpellCastStatus::Failed;
    PartySpellCastTargetKind targetKind = PartySpellCastTargetKind::None;
    PartySpellCastEffectKind effectKind = PartySpellCastEffectKind::Unsupported;
    uint32_t spellId = 0;
    uint32_t manaCost = 0;
    uint32_t skillLevel = 0;
    SkillMastery skillMastery = SkillMastery::None;
    float recoverySeconds = 0.0f;
    bool hasSourcePoint = false;
    float sourceX = 0.0f;
    float sourceY = 0.0f;
    float sourceZ = 0.0f;
    std::string statusText;
    std::vector<size_t> affectedCharacterIndices;

    bool succeeded() const
    {
        return status == PartySpellCastStatus::Succeeded;
    }
};

struct PartySpellDescriptor
{
    PartySpellCastTargetKind targetKind = PartySpellCastTargetKind::None;
    PartySpellCastEffectKind effectKind = PartySpellCastEffectKind::Unsupported;
};

class PartySpellSystem
{
public:
    static std::optional<PartySpellDescriptor> describeSpell(uint32_t spellId);

    static PartySpellCastResult castSpell(
        Party &party,
        OutdoorPartyRuntime &partyRuntime,
        OutdoorWorldRuntime &worldRuntime,
        const SpellTable &spellTable,
        const PartySpellCastRequest &request);
};
}
