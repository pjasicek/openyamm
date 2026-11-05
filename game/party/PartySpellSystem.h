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
class SpellRules;
class SpellTable;

enum class PartySpellCastTargetKind : uint8_t
{
    None = 0,
    Actor,
    Character,
    CharacterOrWorldTarget,
    ActorOrCharacter,
    GroundPoint,
    InventoryItem,
    TelekinesisTarget,
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
    Telekinesis,
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
    NeedCharacterOrWorldTarget,
    NeedActorOrCharacterTarget,
    NeedGroundPoint,
    NeedInventoryItemTarget,
    NeedTelekinesisTarget,
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
    std::optional<GameplayWorldHit> telekinesisTarget;
    std::optional<GameplayWorldHit> targetWorldHit;
    uint32_t skillLevelOverride = 0;
    SkillMastery skillMasteryOverride = SkillMastery::None;
    // Scrolls and wands provide fixed spell power without requiring the caster to know the spell mastery.
    bool bypassRequiredMastery = false;
    // Read from a scroll: the party's rules may hold its buff as a fixed aura (SpellRules::castSourceBuff).
    bool fromScroll = false;
    // NPC and scripted casts can use a party member as the UI speaker without requiring that member to be ready.
    bool bypassGameplayCasterValidation = false;
    bool turnBasedPendingAction = false;
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
    bool utilityMapMoveUseFullscreenLoading = false;
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
    // Mana an ordinary cast would spend, or nullopt when the caster lacks the skill for the spell.
    // What the spell costs this caster, under the party's rules.
    static std::optional<uint32_t> manaCost(
        const Party &party,
        const Character &caster,
        const SpellTable &spellTable,
        uint32_t spellId);
    // Whether a quick or attack cast of this spell on a member picks its own target (quickCastCharacterTarget): the
    // heals, cures and revivals. A buff on one member asks for its target.
    static bool hasQuickCastCharacterTarget(uint32_t spellId);
    // The member a quick or attack spell on a member targets: the dead for Raise Dead and Resurrection, the
    // petrified for Stone to Flesh; for a heal the lowest HP share among members at or below a third of their
    // maximum, else the one who gains the most from this cast (ties to the lowest share), else, nobody wounded, a
    // member with the condition it cures (MAW's Greater Heal and Remove Curse); a cure's condition; for the rest the
    // wounded member with the fewest HP. Nothing when nobody fits.
    static std::optional<size_t> quickCastCharacterTarget(
        const Party &party,
        size_t casterIndex,
        uint32_t spellId,
        const SpellTable *pSpellTable);
    // The monster a quick cast takes when none is under the cursor: the closest visible hostile within
    // SpellActorTargetRange, whether or not it has noticed the party, or, for a spell the
    // rules spread (SpellRules::quickCastSpreadsDebuff, MAW), the visible hostile within 4800 whose debuff of the spell
    // ends soonest (an undead one for Control Undead), the closer on a tie (SPL-18).
    static std::optional<size_t> quickCastActorTarget(
        const IGameplayWorldRuntime &worldRuntime,
        const SpellRules &spellRules,
        uint32_t spellId);
    // The original pick depth of spell and missile targets (MM7/MM8; OpenEnroth's RangedAttackDepth). The player's
    // actor-targeted casts reach no further; scripted casts are not limited.
    static constexpr float SpellActorTargetRange = 5120.0f;
    // The furthest from the party a party's Meteor Shower or Starburst falls (a design limit, shorter than the
    // original's pick depth).
    static constexpr float FallingSpellTargetRange = 3500.0f;
    // Where a party's Meteor Shower or Starburst aimed at the point falls: a point beyond FallingSpellTargetRange
    // comes back along the same line to that range. Other spells keep the point. The cast and its aiming marker both
    // use it.
    static bx::Vec3 resolveFallingSpellTargetPoint(
        const IGameplayWorldRuntime &worldRuntime,
        uint32_t spellId,
        const bx::Vec3 &targetPoint);
    // Whether the actor, alive or dead, is within SpellActorTargetRange of the party's feet.
    static bool isActorWithinSpellTargetRange(const IGameplayWorldRuntime &worldRuntime, size_t actorIndex);
    // A living, visible actor within spell reach of the party; with `requireHostile` (the targets the game picks for
    // a quick or attack spell) only a hostile one.
    static bool isUsableSpellActorTarget(
        const IGameplayWorldRuntime &worldRuntime,
        size_t actorIndex,
        bool requireHostile);
    // The HP the caster's heal spell would give one member, as a cast applies it (the ruleset's heal, else Standard's
    // Heal), before any crit; nothing for a spell that does not heal or a caster without the skill.
    static std::optional<int> healAmount(
        const Party &party,
        const Character &caster,
        const SpellTable &spellTable,
        uint32_t spellId);

    static PartySpellCastResult castSpell(
        Party &party,
        IGameplayWorldRuntime &worldRuntime,
        const SpellTable &spellTable,
        const PartySpellCastRequest &request);
};
}
