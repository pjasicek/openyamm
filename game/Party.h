#pragma once

#include "game/CharacterState.h"
#include "game/ClassSkillTable.h"
#include "game/OutdoorMovementDriver.h"
#include "game/PortraitEnums.h"
#include "game/SoundIds.h"
#include "game/SpeechIds.h"

#include <array>
#include <bitset>
#include <cstdint>
#include <optional>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>

namespace OpenYAMM::Game
{
class ItemTable;
struct RosterEntry;
struct EventRuntimeState;
class StandardItemEnchantTable;
class SpecialItemEnchantTable;

struct InventoryItem
{
    uint32_t objectDescriptionId = 0;
    uint32_t quantity = 1;
    uint8_t width = 1;
    uint8_t height = 1;
    uint8_t gridX = 0;
    uint8_t gridY = 0;
    bool identified = true;
    bool broken = false;
    bool stolen = false;
    uint16_t standardEnchantId = 0;
    uint16_t standardEnchantPower = 0;
    uint16_t specialEnchantId = 0;
    uint16_t artifactId = 0;
    ItemRarity rarity = ItemRarity::Common;
};

struct Character
{
    static constexpr int InventoryWidth = 14;
    static constexpr int InventoryHeight = 9;

    std::string name;
    std::string role;
    std::string className;
    std::string portraitTextureName;
    uint32_t portraitPictureId = 0;
    PortraitId portraitState = PortraitId::Normal;
    uint32_t portraitElapsedTicks = 0;
    uint32_t portraitDurationTicks = 0;
    uint32_t portraitSequenceCounter = 0;
    uint16_t portraitImageIndex = 0;
    uint32_t rosterId = 0;
    uint32_t characterDataId = 0;
    uint32_t birthYear = 0;
    uint32_t experience = 0;
    uint32_t level = 1;
    uint32_t skillPoints = 0;
    uint32_t might = 0;
    uint32_t intellect = 0;
    uint32_t personality = 0;
    uint32_t endurance = 0;
    uint32_t speed = 0;
    uint32_t accuracy = 0;
    uint32_t luck = 0;
    int maxHealth = 100;
    int health = 100;
    int maxSpellPoints = 0;
    int spellPoints = 0;
    std::string quickSpellName;
    std::unordered_set<uint32_t> knownSpellIds;
    CharacterResistanceSet baseResistances = {};
    CharacterStatBonuses permanentBonuses = {};
    CharacterStatBonuses magicalBonuses = {};
    CharacterResistanceImmunitySet permanentImmunities = {};
    CharacterResistanceImmunitySet magicalImmunities = {};
    std::bitset<CharacterConditionCount> permanentConditionImmunities = {};
    std::bitset<CharacterConditionCount> magicalConditionImmunities = {};
    CharacterEquipment equipment = {};
    CharacterEquipmentRuntimeState equipmentRuntime = {};
    std::bitset<CharacterConditionCount> conditions = {};
    std::unordered_map<std::string, CharacterSkill> skills;
    std::unordered_set<uint32_t> awards;
    float recoverySecondsRemaining = 0.0f;
    int merchantBonus = 0;
    int weaponEnchantmentDamageBonus = 0;
    float vampiricHealFraction = 0.0f;
    bool physicalAttackDisabled = false;
    bool physicalDamageImmune = false;
    bool halfMissileDamage = false;
    bool waterWalking = false;
    bool featherFalling = false;
    float healthRegenPerSecond = 0.0f;
    float spellRegenPerSecond = 0.0f;
    float healthRegenAccumulator = 0.0f;
    float spellRegenAccumulator = 0.0f;
    int attackRecoveryReductionTicks = 0;
    float recoveryProgressMultiplier = 1.0f;
    std::unordered_map<std::string, int> itemSkillBonuses;

    bool addInventoryItem(const InventoryItem &item);
    bool addInventoryItemAt(const InventoryItem &item, uint8_t gridX, uint8_t gridY);
    bool removeInventoryItem(uint32_t objectDescriptionId, uint32_t quantity = 1);
    const InventoryItem *inventoryItemAt(uint8_t gridX, uint8_t gridY) const;
    bool takeInventoryItemAt(uint8_t gridX, uint8_t gridY, InventoryItem &item);
    bool tryPlaceInventoryItemAt(
        const InventoryItem &item,
        uint8_t gridX,
        uint8_t gridY,
        std::optional<InventoryItem> &replacedItem);
    size_t inventoryItemCount() const;
    size_t usedInventoryCells() const;
    size_t inventoryCapacity() const;
    bool hasSkill(const std::string &skillName) const;
    const CharacterSkill *findSkill(const std::string &skillName) const;
    CharacterSkill *findSkill(const std::string &skillName);
    bool setSkillMastery(const std::string &skillName, SkillMastery mastery);
    bool knowsSpell(uint32_t spellId) const;
    bool learnSpell(uint32_t spellId);
    bool forgetSpell(uint32_t spellId);

    std::vector<InventoryItem> inventory;
};

struct PartySeed
{
    std::vector<Character> members;
    std::vector<InventoryItem> inventory;
    int gold = 0;
    int food = 0;
};

enum class PartyBuffId : uint8_t
{
    TorchLight = 0,
    WizardEye,
    FeatherFall,
    DetectLife,
    WaterWalk,
    Fly,
    Invisibility,
    Stoneskin,
    DayOfGods,
    ProtectionFromMagic,
    FireResistance,
    WaterResistance,
    AirResistance,
    EarthResistance,
    MindResistance,
    BodyResistance,
    Shield,
    Heroism,
    Haste,
    Immolation,
    Glamour,
    Levitate,
    Count,
};

static constexpr size_t PartyBuffCount = static_cast<size_t>(PartyBuffId::Count);

enum class CharacterBuffId : uint8_t
{
    Bless = 0,
    Fate,
    Preservation,
    Regeneration,
    Hammerhands,
    PainReflection,
    FireAura,
    VampiricWeapon,
    Mistform,
    Glamour,
    Count,
};

static constexpr size_t CharacterBuffCount = static_cast<size_t>(CharacterBuffId::Count);

struct PartyBuffState
{
    float remainingSeconds = 0.0f;
    uint32_t spellId = 0;
    uint32_t skillLevel = 0;
    SkillMastery skillMastery = SkillMastery::None;
    int power = 0;
    uint32_t casterMemberIndex = 0;

    bool active() const
    {
        return remainingSeconds > 0.0f;
    }
};

struct CharacterBuffState
{
    float remainingSeconds = 0.0f;
    float periodicAccumulatorSeconds = 0.0f;
    uint32_t spellId = 0;
    uint32_t skillLevel = 0;
    SkillMastery skillMastery = SkillMastery::None;
    int power = 0;
    uint32_t casterMemberIndex = 0;

    bool active() const
    {
        return remainingSeconds > 0.0f;
    }
};

class Party
{
public:
    struct HouseStockState
    {
        uint32_t houseId = 0;
        float nextRefreshGameMinutes = 0.0f;
        uint32_t refreshSequence = 0;
        std::vector<InventoryItem> standardStock;
        std::vector<InventoryItem> specialStock;
        std::vector<InventoryItem> spellbookStock;
    };

    struct Snapshot
    {
        std::vector<Character> members;
        size_t activeMemberIndex = 0;
        std::array<PartyBuffState, PartyBuffCount> partyBuffs = {};
        std::array<std::array<CharacterBuffState, CharacterBuffCount>, 5> characterBuffs = {};
        int gold = 0;
        int bankGold = 0;
        int food = 0;
        uint32_t waterDamageTicks = 0;
        uint32_t burningDamageTicks = 0;
        uint32_t splashCount = 0;
        uint32_t landingSoundCount = 0;
        uint32_t hardLandingSoundCount = 0;
        uint32_t monsterTargetSelectionCounter = 0;
        uint32_t houseStockSeed = 0;
        float lastFallDamageDistance = 0.0f;
        std::unordered_set<uint32_t> foundArtifactItems;
        std::vector<HouseStockState> houseStockStates;
    };

    struct PendingAudioRequest
    {
        enum class Kind : uint8_t
        {
            Sound,
            Speech,
        };

        Kind kind = Kind::Sound;
        SoundId soundId = SoundId::None;
        SpeechId speechId = SpeechId::None;
        size_t memberIndex = 0;
    };

    static PartySeed createDefaultSeed();

    void setItemTable(const ItemTable *pItemTable);
    void setItemEnchantTables(
        const StandardItemEnchantTable *pStandardItemEnchantTable,
        const SpecialItemEnchantTable *pSpecialItemEnchantTable);
    void setClassSkillTable(const ClassSkillTable *pClassSkillTable);
    Snapshot snapshot() const;
    void restoreSnapshot(const Snapshot &snapshot);
    void reset();
    void seed(const PartySeed &seed);
    void applyMovementEffects(const OutdoorMovementEffects &effects);
    void applyEventRuntimeState(const EventRuntimeState &runtimeState);
    bool applyDamageToMember(size_t memberIndex, int damage, const std::string &status);
    bool applyDamageToActiveMember(int damage, const std::string &status);
    bool applyDamageToAllLivingMembers(int damage, const std::string &status);
    uint32_t addExperienceToMember(size_t memberIndex, int64_t amount);
    uint32_t setMemberExperience(size_t memberIndex, uint32_t experience);
    uint32_t grantSharedExperience(uint32_t totalExperience);
    std::optional<size_t> chooseMonsterAttackTarget(uint32_t attackPreferences, uint32_t seedHint);
    void addGold(int amount);
    void addFood(int amount);
    void requestSound(SoundId soundId);
    bool tryGrantItem(uint32_t objectDescriptionId, uint32_t quantity = 1);
    bool tryGrantInventoryItem(const InventoryItem &item, size_t *pRecipientMemberIndex = nullptr);
    void grantItem(uint32_t objectDescriptionId, uint32_t quantity = 1);
    bool removeItem(uint32_t objectDescriptionId, uint32_t quantity = 1);
    bool needsHealing() const;
    bool activeMemberNeedsHealing() const;
    void restoreAll();
    void restAndHealAll();
    void restoreActiveMember();
    bool trainLeader(uint32_t maxLevel, uint32_t &newLevel, uint32_t &skillPointsEarned);
    bool trainActiveMember(uint32_t maxLevel, uint32_t &newLevel, uint32_t &skillPointsEarned);
    bool canActiveMemberLearnSkill(const std::string &skillName) const;
    bool learnActiveMemberSkill(const std::string &skillName);
    bool canIncreaseActiveMemberSkillLevel(const std::string &skillName) const;
    bool increaseActiveMemberSkillLevel(const std::string &skillName);
    int depositGoldToBank(int amount);
    int withdrawBankGold(int amount);
    int depositAllGoldToBank();
    int withdrawAllBankGold();
    bool isFull() const;
    bool recruitRosterMember(const RosterEntry &rosterEntry);
    bool hasRosterMember(uint32_t rosterId) const;
    bool hasAward(uint32_t awardId) const;
    bool hasAward(size_t memberIndex, uint32_t awardId) const;
    void addAward(uint32_t awardId);
    void addAward(size_t memberIndex, uint32_t awardId);
    void removeAward(uint32_t awardId);
    void removeAward(size_t memberIndex, uint32_t awardId);
    int inventoryItemCount(uint32_t objectDescriptionId, std::optional<size_t> memberIndex = std::nullopt) const;
    bool grantItemToMember(size_t memberIndex, uint32_t objectDescriptionId, uint32_t quantity = 1);
    bool removeItemFromMember(size_t memberIndex, uint32_t objectDescriptionId, uint32_t quantity = 1);
    bool takeItemFromMemberInventoryCell(size_t memberIndex, uint8_t gridX, uint8_t gridY, InventoryItem &item);
    bool tryAutoPlaceItemInMemberInventory(size_t memberIndex, const InventoryItem &item);
    bool tryPlaceItemInMemberInventoryCell(
        size_t memberIndex,
        const InventoryItem &item,
        uint8_t gridX,
        uint8_t gridY,
        std::optional<InventoryItem> &replacedItem);
    bool takeEquippedItemFromMember(size_t memberIndex, EquipmentSlot slot, InventoryItem &item);
    bool tryEquipItemOnMember(
        size_t memberIndex,
        EquipmentSlot targetSlot,
        const InventoryItem &item,
        std::optional<EquipmentSlot> displacedSlot,
        bool autoStoreDisplacedItem,
        std::optional<InventoryItem> &heldReplacement);
    std::optional<InventoryItem> equippedItem(size_t memberIndex, EquipmentSlot slot) const;
    bool tryIdentifyMemberInventoryItem(
        size_t memberIndex,
        uint8_t gridX,
        uint8_t gridY,
        size_t inspectorMemberIndex,
        std::string &statusText);
    bool tryRepairMemberInventoryItem(
        size_t memberIndex,
        uint8_t gridX,
        uint8_t gridY,
        size_t inspectorMemberIndex,
        std::string &statusText);
    bool identifyMemberInventoryItem(
        size_t memberIndex,
        uint8_t gridX,
        uint8_t gridY,
        std::string &statusText);
    bool repairMemberInventoryItem(
        size_t memberIndex,
        uint8_t gridX,
        uint8_t gridY,
        std::string &statusText);
    bool tryIdentifyEquippedItem(
        size_t memberIndex,
        EquipmentSlot slot,
        size_t inspectorMemberIndex,
        std::string &statusText);
    bool tryRepairEquippedItem(
        size_t memberIndex,
        EquipmentSlot slot,
        size_t inspectorMemberIndex,
        std::string &statusText);
    bool identifyEquippedItem(
        size_t memberIndex,
        EquipmentSlot slot,
        std::string &statusText);
    bool repairEquippedItem(
        size_t memberIndex,
        EquipmentSlot slot,
        std::string &statusText);
    bool setMemberClassName(size_t memberIndex, const std::string &className);
    const Character *member(size_t memberIndex) const;
    Character *member(size_t memberIndex);
    bool canSelectMemberInGameplay(size_t memberIndex) const;
    bool hasSelectableMemberInGameplay() const;
    bool setActiveMemberIndex(size_t memberIndex);
    bool canSpendSpellPoints(size_t memberIndex, int amount) const;
    bool spendSpellPoints(size_t memberIndex, int amount);
    bool spendSpellPointsOnActiveMember(int amount);
    void updateRecovery(float deltaSeconds);
    bool applyRecoveryToMember(size_t memberIndex, float recoverySeconds);
    bool applyRecoveryToActiveMember(float recoverySeconds);
    bool switchToNextReadyMember();
    void applyPartyBuff(
        PartyBuffId buffId,
        float durationSeconds,
        int power,
        uint32_t spellId,
        uint32_t skillLevel,
        SkillMastery skillMastery,
        uint32_t casterMemberIndex);
    void applyCharacterBuff(
        size_t memberIndex,
        CharacterBuffId buffId,
        float durationSeconds,
        int power,
        uint32_t spellId,
        uint32_t skillLevel,
        SkillMastery skillMastery,
        uint32_t casterMemberIndex);
    void clearPartyBuff(PartyBuffId buffId);
    void clearCharacterBuff(size_t memberIndex, CharacterBuffId buffId);
    bool hasPartyBuff(PartyBuffId buffId) const;
    bool hasCharacterBuff(size_t memberIndex, CharacterBuffId buffId) const;
    const PartyBuffState *partyBuff(PartyBuffId buffId) const;
    const CharacterBuffState *characterBuff(size_t memberIndex, CharacterBuffId buffId) const;
    bool applyMemberCondition(size_t memberIndex, CharacterCondition condition);
    bool clearMemberCondition(size_t memberIndex, CharacterCondition condition);
    bool hasMemberConditionImmunity(size_t memberIndex, CharacterCondition condition) const;
    bool healMember(size_t memberIndex, int amount);
    bool reviveMember(size_t memberIndex, int health, bool applyWeak);

    const std::vector<Character> &members() const;
    const Character *activeMember() const;
    Character *activeMember();
    size_t activeMemberIndex() const;
    int totalHealth() const;
    int totalMaxHealth() const;
    int gold() const;
    int bankGold() const;
    int food() const;
    uint32_t houseStockSeed() const;
    bool hasFoundArtifactItem(uint32_t itemId) const;
    void markArtifactItemFound(uint32_t itemId);
    void clearFoundArtifactItems();
    HouseStockState *houseStockState(uint32_t houseId);
    const HouseStockState *houseStockState(uint32_t houseId) const;
    HouseStockState &ensureHouseStockState(uint32_t houseId);
    void clearHouseStockStates();
    size_t inventoryItemCount() const;
    size_t usedInventoryCells() const;
    size_t inventoryCapacity() const;
    uint32_t waterDamageTicks() const;
    uint32_t burningDamageTicks() const;
    uint32_t splashCount() const;
    uint32_t landingSoundCount() const;
    uint32_t hardLandingSoundCount() const;
    float lastFallDamageDistance() const;
    const std::string &lastStatus() const;
    const std::vector<PendingAudioRequest> &pendingAudioRequests() const;
    void clearPendingAudioRequests();

private:
    static constexpr size_t MaxMembers = 5;

    uint8_t resolveInventoryWidth(uint32_t objectDescriptionId) const;
    uint8_t resolveInventoryHeight(uint32_t objectDescriptionId) const;
    void applyDefaultStartingSkills(Character &member) const;
    void rebuildMagicalBonusesFromBuffs();
    void markArtifactItemFoundIfRelevant(const InventoryItem &item);
    void queueSound(SoundId soundId);
    void queueSpeech(size_t memberIndex, SpeechId speechId);

    const ItemTable *m_pItemTable = nullptr;
    const StandardItemEnchantTable *m_pStandardItemEnchantTable = nullptr;
    const SpecialItemEnchantTable *m_pSpecialItemEnchantTable = nullptr;
    const ClassSkillTable *m_pClassSkillTable = nullptr;
    std::vector<Character> m_members;
    size_t m_activeMemberIndex = 0;
    std::array<PartyBuffState, PartyBuffCount> m_partyBuffs = {};
    std::array<std::array<CharacterBuffState, CharacterBuffCount>, MaxMembers> m_characterBuffs = {};
    int m_gold = 0;
    int m_bankGold = 0;
    int m_food = 0;
    uint32_t m_waterDamageTicks = 0;
    uint32_t m_burningDamageTicks = 0;
    uint32_t m_splashCount = 0;
    uint32_t m_landingSoundCount = 0;
    uint32_t m_hardLandingSoundCount = 0;
    uint32_t m_monsterTargetSelectionCounter = 0;
    uint32_t m_houseStockSeed = 0;
    float m_lastFallDamageDistance = 0.0f;
    std::string m_lastStatus;
    std::unordered_set<uint32_t> m_foundArtifactItems;
    std::unordered_map<uint32_t, HouseStockState> m_houseStockStates;
    std::vector<PendingAudioRequest> m_pendingAudioRequests;
};
}
