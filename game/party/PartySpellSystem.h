#pragma once

#include "game/gameplay/GameplayRuntimeInterfaces.h"
#include "game/party/Party.h"
#include "game/party/SkillData.h"

#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
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

enum class PartySpellUtilityActionKind : uint8_t
{
    None = 0,
    TownPortalDestination,
    LloydsBeaconSet,
    LloydsBeaconRecall,
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
    std::optional<size_t> targetItemMemberIndex;
    std::optional<uint8_t> targetInventoryGridX;
    std::optional<uint8_t> targetInventoryGridY;
    std::optional<EquipmentSlot> targetEquipmentSlot;
    bool hasTargetPoint = false;
    float targetX = 0.0f;
    float targetY = 0.0f;
    float targetZ = 0.0f;
    uint32_t skillLevelOverride = 0;
    SkillMastery skillMasteryOverride = SkillMastery::None;
    // Wands provide their own fixed spell power and do not require the caster to know the spell mastery.
    bool bypassRequiredMastery = false;
    bool spendMana = true;
    bool applyRecovery = true;
    bool hasViewTransform = false;
    float viewX = 0.0f;
    float viewY = 0.0f;
    float viewZ = 0.0f;
    float viewYawRadians = 0.0f;
    float viewPitchRadians = 0.0f;
    float viewAspectRatio = 1.0f;
    PartySpellUtilityActionKind utilityAction = PartySpellUtilityActionKind::None;
    std::string utilityActionId;
    uint8_t utilitySlotIndex = 0;
    bool hasUtilityMapMove = false;
    int32_t utilityMapMoveX = 0;
    int32_t utilityMapMoveY = 0;
    int32_t utilityMapMoveZ = 0;
    std::string utilityMapMoveMapName;
    std::optional<int32_t> utilityMapMoveDirectionDegrees;
    bool utilityMapMoveUseMapStartPosition = false;
    std::string utilityStatusText;
    int utilityPreviewWidth = 0;
    int utilityPreviewHeight = 0;
    std::vector<uint8_t> utilityPreviewPixelsBgra;
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
    struct ScreenOverlayRequest
    {
        uint32_t colorAbgr = 0x00000000u;
        float durationSeconds = 0.0f;
        float peakAlpha = 0.0f;
    };
    std::optional<ScreenOverlayRequest> screenOverlayRequest;

    bool succeeded() const
    {
        return status == PartySpellCastStatus::Succeeded;
    }
};

struct PartySpellDescriptor
{
    uint32_t spellId = 0;
    PartySpellCastTargetKind targetKind = PartySpellCastTargetKind::None;
    PartySpellCastEffectKind effectKind = PartySpellCastEffectKind::Unsupported;
};

class PartySpellSystem
{
public:
    static std::optional<PartySpellDescriptor> describeSpell(uint32_t spellId);

    static PartySpellCastResult castSpell(
        Party &party,
        IGameplayWorldRuntime &worldRuntime,
        const SpellTable &spellTable,
        const PartySpellCastRequest &request);
};
}
