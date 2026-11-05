#pragma once

#include "game/party/SkillData.h"
#include "game/tables/MonsterModifiers.h"
#include "game/tables/MonsterRelationAddOns.h"
#include "game/tables/MonsterShields.h"
#include "game/tables/MonsterSpecialAttackKind.h"

#include <array>
#include <cstdint>
#include <memory>
#include <optional>
#include <string>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Game
{
class ActorModelManifest;

// Flags of MonsterStatsEntry::attackPreferences: whom a monster prefers to attack. The table gives them as a number or
// as MM6/MM7 letters (K, P, A, D, C, S, R, T, M for classes, X/O/F for male/female, H, E, W, G for races).
inline constexpr uint32_t MonsterAttackPreferenceKnight = 0x0001;
inline constexpr uint32_t MonsterAttackPreferencePaladin = 0x0002;
inline constexpr uint32_t MonsterAttackPreferenceArcher = 0x0004;
inline constexpr uint32_t MonsterAttackPreferenceDruid = 0x0008;
inline constexpr uint32_t MonsterAttackPreferenceCleric = 0x0010;
inline constexpr uint32_t MonsterAttackPreferenceSorcerer = 0x0020;
inline constexpr uint32_t MonsterAttackPreferenceRanger = 0x0040;
inline constexpr uint32_t MonsterAttackPreferenceThief = 0x0080;
inline constexpr uint32_t MonsterAttackPreferenceMonk = 0x0100;
inline constexpr uint32_t MonsterAttackPreferenceMale = 0x0200;
inline constexpr uint32_t MonsterAttackPreferenceFemale = 0x0400;
inline constexpr uint32_t MonsterAttackPreferenceHuman = 0x0800;
inline constexpr uint32_t MonsterAttackPreferenceElf = 0x1000;
inline constexpr uint32_t MonsterAttackPreferenceDwarf = 0x2000;
inline constexpr uint32_t MonsterAttackPreferenceGoblin = 0x4000;

class MergedBolsterMonsterTable;

enum class MonsterKind : uint32_t
{
    Undead = 1u << 0,
    Dragon = 1u << 1,
    Swimmer = 1u << 2,
    Immobile = 1u << 3,
    Peasant = 1u << 4,
    NoArena = 1u << 5,
    Ogre = 1u << 6,
    Elemental = 1u << 7,
    Titan = 1u << 8,
    NoCorpse = 1u << 9,
    Demon = 1u << 10,
    Elf = 1u << 11,
};

uint32_t monsterKindFlag(MonsterKind kind);

struct MonsterEntry
{
    uint16_t height = 0;
    uint16_t radius = 0;
    uint16_t movementSpeed = 0;
    int16_t toHitRadius = 0;
    uint32_t tintColor = 0;
    std::array<uint16_t, 4> soundSampleIds = {};
    std::string internalName;
    std::array<std::string, 8> spriteNames = {};
    int inspectYOffset = 0;
    int inspectAttackChance = 100;
    bool inspectFidgetWhenMoving = false;
    // What melee blows strike (monster_descriptors.txt HitMaterial, a melee_hit_materials.txt name); empty is Flesh.
    std::string hitMaterial;
};

class MonsterTable
{
public:
    enum class MonsterMovementType
    {
        Short,
        Medium,
        Long,
        Global,
        Free,
        Stationary,
    };

    enum class MonsterAiType
    {
        Suicide,
        Wimp,
        Normal,
        Aggressive,
    };

    enum class MonsterAttackStyle
    {
        MeleeOnly,
        MixedMeleeRanged,
        Ranged,
    };

    enum class LootItemKind
    {
        None,
        Any,
        Weapon,
        Armor,
        Misc,
        Gem,
        Ring,
        Amulet,
        Boots,
        Gauntlets,
        Cloak,
        Wand,
        Ore,
        Scroll,
        Sword,
        Dagger,
        Axe,
        Spear,
        Chain,
        Leather,
        Plate,
        Mace,
        Club,
        Staff,
        Bow,
        Shield,
        Helm,
        Belt,
    };

    struct LootPrototype
    {
        int goldDiceRolls = 0;
        int goldDiceSides = 0;
        int itemChance = 0;
        int itemLevel = 0;
        LootItemKind itemKind = LootItemKind::None;
    };

    struct MonsterStatsEntry
    {
        struct DamageProfile
        {
            int diceRolls = 0;
            int diceSides = 0;
            int bonus = 0;
        };

        int id = 0;
        std::string name;
        std::string pictureName;
        int level = 0;
        int hitPoints = 0;
        int armorClass = 0;
        int experience = 0;
        std::string attack1Type;
        bool bloodSplatOnDeath = false;
        int hostility = 0;
        int speed = 0;
        int recovery = 0;
        uint32_t attackPreferences = 0;
        std::string specialAttackDescriptor;
        MonsterSpecialAttackKind specialAttackKind = MonsterSpecialAttackKind::None;
        int specialAttackLevel = 0;
        bool canFly = false;
        // Fly column "S" (with Y: "YS"): MM9's AISwimFly swimmers (Sea Monsters, the Spores, Fish). On a map with
        // scene water volumes one that starts in the water swims in it, bound to it; elsewhere it flies (Y) or walks.
        bool swims = false;
        MonsterMovementType movementType = MonsterMovementType::Short;
        MonsterAiType aiType = MonsterAiType::Suicide;
        std::string attack1MissileType;
        bool attack1HasMissile = false;
        DamageProfile attack1Damage = {};
        std::string attack2Type;
        std::string attack2MissileType;
        bool attack2HasMissile = false;
        int attack2Chance = 0;
        DamageProfile attack2Damage = {};
        std::string spell1Descriptor;
        std::string spell1Name;
        bool hasSpell1 = false;
        int spell1UseChance = 0;
        uint32_t spell1SkillLevel = 0;
        SkillMastery spell1SkillMastery = SkillMastery::None;
        std::string spell2Descriptor;
        std::string spell2Name;
        bool hasSpell2 = false;
        int spell2UseChance = 0;
        uint32_t spell2SkillLevel = 0;
        SkillMastery spell2SkillMastery = SkillMastery::None;
        MonsterAttackStyle attackStyle = MonsterAttackStyle::MeleeOnly;
        int fireResistance = 0;
        int airResistance = 0;
        int waterResistance = 0;
        int earthResistance = 0;
        int mindResistance = 0;
        int spiritResistance = 0;
        int bodyResistance = 0;
        int lightResistance = 0;
        int darkResistance = 0;
        int physicalResistance = 0;
        // The Special column's "explode,AdB+C,element" (MM8 Special 3: Gogs, Boulders, Light Elementals, Golems): it
        // bursts when it dies (MonsterDeathExplosion.h).
        bool explodesOnDeath = false;
        DamageProfile deathExplosionDamage = {};
        std::string deathExplosionType;
        std::string treasureDefinition;
        LootPrototype loot = {};
        uint16_t attackSoundId = 0;
        uint16_t deathSoundId = 0;
        uint16_t winceSoundId = 0;
        uint16_t boredSoundId = 0;
        uint32_t kindFlags = 0;

        bool hasKind(MonsterKind kind) const;
    };

    struct MonsterDisplayNameEntry
    {
        int id = 0;
        std::string pictureName;
        std::string displayName;
    };

    // What a melee weapon strikes on a monster (engine melee_hit_materials.txt, after Might and Magic IX's
    // MATERIALS.txt): its impact sound for a glancing, normal and crushing blow (an empty path plays nothing), and the
    // effect spawned at the contact point, which is blood or gore when the blood flag is set.
    struct MeleeHitMaterial
    {
        std::string name;
        std::array<std::string, 3> impactSoundPaths;
        std::string contactEffectId;
        bool blood = false;
    };

    struct MonsterDeathDropEntry
    {
        int monsterId = 0;
        std::string monsterName;
        uint32_t itemId = 0;
        std::string itemName;
        int chancePercent = 0;
        std::string description;
    };

    bool loadEntriesFromRows(const std::vector<std::vector<std::string>> &rows);
    bool loadFromBytes(const std::vector<uint8_t> &bytes);
    bool loadDisplayNamesFromRows(const std::vector<std::vector<std::string>> &rows);
    bool loadStatsFromRows(const std::vector<std::vector<std::string>> &rows);
    bool applyKindFlagsFromBolsterMonsterTable(const MergedBolsterMonsterTable &bolsterMonsterTable);
    bool loadDeathDropsFromRows(const std::vector<std::vector<std::string>> &rows);
    bool loadRelationsFromRows(const std::vector<std::vector<std::string>> &rows);
    bool loadUniqueNamesFromRows(const std::vector<std::vector<std::string>> &rows);
    // After loadEntriesFromRows: fails when a monster names a material the table lacks.
    bool loadMeleeHitMaterialsFromRows(const std::vector<std::vector<std::string>> &materialRows);
    const MeleeHitMaterial *findMeleeHitMaterial(int16_t monsterId) const;
    const MonsterEntry *findByInternalName(const std::string &internalName) const;
    const MonsterEntry *findById(int16_t monsterId) const;
    const MonsterStatsEntry *findStatsById(int16_t monsterId) const;
    const std::vector<MonsterDeathDropEntry> &deathDropsForMonsterId(int16_t monsterId) const;
    const MonsterStatsEntry *findStatsByPictureName(const std::string &pictureName) const;
    const MonsterDisplayNameEntry *findDisplayEntryById(int id) const;
    // The monster entry named by a display entry's picture (an actor's monster info id); resolved at load.
    const MonsterEntry *findByDisplayEntryId(int id) const;
    std::optional<std::string> findDisplayNameByInternalName(const std::string &internalName) const;
    std::optional<std::string> getUniqueName(int32_t uniqueNameIndex) const;
    // Relations: a world's relations.yml add-on (relationAddOns) decides where it has a rule, else hostile.txt.
    int getRelationToParty(int16_t monsterId) const;
    int getRelationBetweenMonsters(int16_t leftMonsterId, int16_t rightMonsterId) const;
    bool isHostileToParty(int16_t monsterId) const;
    bool isLikelySameFaction(int16_t leftMonsterId, int16_t rightMonsterId) const;
    // Whether a party hit on one monster alerts the other (MM8 0x4391ca): the same hostile.txt class, or both Dark Elf
    // peasant classes. Pass relation monster ids, which already follow an actor's Ally class.
    bool sharesAlertFaction(int16_t leftRelationMonsterId, int16_t rightRelationMonsterId) const;
    MonsterRelationAddOns &relationAddOns()
    {
        return m_relationAddOns;
    }
    const MonsterRelationAddOns &relationAddOns() const
    {
        return m_relationAddOns;
    }
    // Energy shields from the worlds' shields.yml; monsters without a profile never meet a shield rule.
    MonsterShieldTable &shields()
    {
        return m_shields;
    }
    const MonsterShieldTable &shields() const
    {
        return m_shields;
    }
    const MonsterShieldProfile *findShieldProfile(int16_t monsterId) const
    {
        return m_shields.empty() ? nullptr : m_shields.find(monsterId);
    }
    // Modifiers (true aim, never staggers, kites party, blink) from the worlds' modifiers.yml.
    MonsterModifierTable &modifiers()
    {
        return m_modifiers;
    }
    const MonsterModifierTable &modifiers() const
    {
        return m_modifiers;
    }
    const MonsterModifierSet *findModifiers(int16_t monsterId) const
    {
        return m_modifiers.empty() ? nullptr : m_modifiers.find(monsterId);
    }
    // The 3D models the monsters are drawn as (worlds' actors.yml), when actor models are on: their attack clips time
    // the monsters' attacks where no sprite contact frame does (resolveActorAttackTiming). Null with models off.
    void setActorModels(std::shared_ptr<const ActorModelManifest> pActorModels)
    {
        m_pActorModels = std::move(pActorModels);
    }
    const ActorModelManifest *actorModels() const
    {
        return m_pActorModels.get();
    }
    const std::vector<MonsterEntry> &getEntries() const;
    const std::unordered_map<int, MonsterStatsEntry> &statsEntries() const;
    // A world's own missile tokens (worlds/<world>/monster_projectiles.yml): an attack naming one is ranged, as one
    // naming an engine token is. MM's tokens and the monsters that name them are untouched.
    void acceptWorldMissileTokens(const std::vector<std::string> &tokens);

private:
    static size_t relationIndexForMonsterId(int16_t monsterId);
    void rebuildEntryIndexByDisplayId();

    std::vector<MonsterEntry> m_entries;
    std::unordered_map<std::string, int16_t> m_entryIndexByInternalName;
    std::vector<MonsterDisplayNameEntry> m_displayNames;
    std::vector<size_t> m_displayNameIndexById;
    std::vector<int16_t> m_entryIndexByDisplayId;
    std::unordered_map<std::string, size_t> m_displayNameIndexByPictureName;
    std::vector<std::string> m_uniqueNames;
    std::unordered_map<int, MonsterStatsEntry> m_statsById;
    std::unordered_map<int, std::vector<MonsterDeathDropEntry>> m_deathDropsByMonsterId;
    std::unordered_map<std::string, int> m_statsIdByPictureName;
    std::vector<std::string> m_relationLabels;
    std::vector<std::vector<int>> m_relations;
    MonsterRelationAddOns m_relationAddOns;
    MonsterShieldTable m_shields;
    MonsterModifierTable m_modifiers;
    std::shared_ptr<const ActorModelManifest> m_pActorModels;
    std::vector<MeleeHitMaterial> m_meleeHitMaterials;
    // Indexed like m_entries.
    std::vector<size_t> m_meleeHitMaterialIndexByEntry;
};
}
