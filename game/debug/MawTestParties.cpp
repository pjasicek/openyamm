#include "game/debug/MawTestParties.h"

#include "game/data/GameDataLoader.h"
#include "game/gameplay/GameMechanics.h"
#include "game/items/InventoryBags.h"
#include "game/items/ItemGenerator.h"
#include "game/party/Party.h"
#include "game/party/SkillData.h"
#include "game/party/SpellSchool.h"
#include "game/rules/GameRules.h"
#include "game/rules/RandomStreams.h"
#include "game/rules/maw/MawDimensionMaps.h"
#include "game/rules/maw/MawItemData.h"
#include "game/rules/maw/MawRules.h"

#include <yaml-cpp/yaml.h>

#include <algorithm>
#include <array>
#include <cctype>
#include <random>
#include <set>
#include <sstream>

namespace OpenYAMM::Game
{
namespace
{
// MAW's dimension map (its item 290).
constexpr uint32_t DimensionMapItemId = 290;

std::string lowerCopy(std::string text)
{
    std::transform(text.begin(), text.end(), text.begin(),
        [](unsigned char character) { return char(std::tolower(character)); });
    return text;
}

std::optional<MawRarity> parseRarity(const std::string &name)
{
    for (int rarity = int(MawRarity::Common); rarity <= int(MawRarity::Celestial); ++rarity)
    {
        if (lowerCopy(mawRarityName(MawRarity(rarity))) == lowerCopy(name))
        {
            return MawRarity(rarity);
        }
    }

    return std::nullopt;
}

// A YAML id or `[first, last]` range.
void readIdRange(const YAML::Node &node, uint32_t &first, uint32_t &last)
{
    if (node.IsSequence() && node.size() == 2)
    {
        first = node[0].as<uint32_t>();
        last = node[1].as<uint32_t>();
    }
    else
    {
        first = node.as<uint32_t>();
        last = first;
    }
}

std::vector<std::string> readStrings(const YAML::Node &node)
{
    std::vector<std::string> values;

    for (const YAML::Node &value : node)
    {
        values.push_back(value.as<std::string>());
    }

    return values;
}

// The portrait of a member: one of the race's when the member names one, else one of the class's own, else any; the
// member's place in the party picks among them so that members of one class differ.
const CharacterDollEntry *chooseDoll(
    const GameDataLoader &data,
    const MawTestPartyMember &member,
    const std::string &className,
    size_t memberIndex)
{
    const std::optional<uint32_t> classId = data.getClassSkillTable().classIdForName(className);
    const MergedCharacterSelectionTable &selection = data.getMergedCharacterSelectionTable();
    std::vector<const CharacterDollEntry *> matches;
    std::vector<const CharacterDollEntry *> any;

    for (const auto &[characterId, entry] : data.getCharacterDollTable().characters())
    {
        (void)characterId;

        if (entry.raceId < 0)
        {
            continue;
        }

        any.push_back(&entry);
        const std::optional<std::string> raceName = selection.raceNameForId(uint32_t(entry.raceId));

        if (!member.race.empty() ? raceName && lowerCopy(*raceName) == lowerCopy(member.race)
                                 : classId && entry.defaultClassId == *classId)
        {
            matches.push_back(&entry);
        }
    }

    std::vector<const CharacterDollEntry *> &choices = !matches.empty() ? matches : any;

    if (choices.empty())
    {
        return nullptr;
    }

    std::sort(choices.begin(), choices.end(),
        [](const CharacterDollEntry *pLeft, const CharacterDollEntry *pRight) { return pLeft->id < pRight->id; });
    return choices[memberIndex % choices.size()];
}

Character makeShell(
    const GameDataLoader &data,
    const MawTestPartyMember &member,
    const std::string &className,
    size_t memberIndex)
{
    Character character = {};
    character.name = member.name.empty() ? displayClassName(className) : member.name;
    character.className = className;
    character.role = displayClassName(className);

    if (const CharacterDollEntry *pDoll = chooseDoll(data, member, className, memberIndex))
    {
        character.characterDataId = pDoll->id;
        character.portraitPictureId = pDoll->id - 1;
        character.raceId = uint32_t(pDoll->raceId);

        if (!pDoll->facePicturesPrefix.empty())
        {
            character.portraitTextureName = pDoll->facePicturesPrefix + "01";
        }
    }

    return character;
}

std::string memberClassName(const MawTestPartyMember &member, const MawTestPartyStage &stage)
{
    return stage.promoted && !member.promotedClassName.empty() ? member.promotedClassName : member.className;
}

// Every skill the class can learn, at the stage's level within the ruleset's caps and the highest mastery the class
// and that level allow.
void grantSkills(Character &character, const GameRules &rules, const ClassSkillTable &classSkills, int skillLevel)
{
    character.skills.clear();
    constexpr std::array<SkillMastery, 4> Masteries = {
        SkillMastery::Normal, SkillMastery::Expert, SkillMastery::Master, SkillMastery::Grandmaster};

    for (const std::string &skill : allCanonicalSkillNames())
    {
        const SkillMastery cap = classSkills.getEffectiveCap(character.className, character.raceId, skill);

        if (cap == SkillMastery::None || isTechnologySkill(skill))
        {
            continue;
        }

        const uint32_t level = std::min(uint32_t(std::max(skillLevel, 1)),
            rules.skills.skillLevelCap(skill).value_or(uint32_t(std::max(skillLevel, 1))));
        SkillMastery mastery = SkillMastery::Normal;

        for (SkillMastery candidate : Masteries)
        {
            if (candidate <= cap && level >= rules.skills.masteryRequiredLevel(skill, candidate))
            {
                mastery = candidate;
            }
        }

        character.skills[skill] = {skill, level, mastery};
    }
}

// Every spell of the schools the member has at the mastery it needs, for classes that learn from books.
void learnSpells(Character &character, const GameRules &rules, const SpellTable &spells)
{
    character.knownSpellIds.clear();

    if (!rules.classes.learnsSpellsFromBooks(character))
    {
        return;
    }

    for (const SpellEntry &spell : spells.entries())
    {
        const std::optional<std::string> school = spell.id > 0 ? resolveMagicSkillName(uint32_t(spell.id)) : std::nullopt;
        const CharacterSkill *pSkill = school ? character.findSkill(*school) : nullptr;

        if (pSkill != nullptr && pSkill->mastery != SkillMastery::None && pSkill->mastery >= spell.requiredMastery)
        {
            character.learnSpell(uint32_t(spell.id));
        }
    }
}

const CharacterSkill *bestSkill(const Character &character, std::initializer_list<const char *> skills)
{
    const CharacterSkill *pBest = nullptr;

    for (const char *pSkill : skills)
    {
        const CharacterSkill *pCandidate = character.findSkill(pSkill);

        if (pCandidate != nullptr && pCandidate->mastery != SkillMastery::None
            && (pBest == nullptr || pCandidate->mastery > pBest->mastery
                || (pCandidate->mastery == pBest->mastery && pCandidate->level > pBest->level)))
        {
            pBest = pCandidate;
        }
    }

    return pBest;
}

// The base items MAW rolls for the slot kind (equip stats, and a skill group when one is named), the top rung first.
std::vector<const ItemDefinition *> baseItems(
    const ItemTable &items,
    const MawItemData &itemData,
    std::initializer_list<const char *> equipStats,
    const std::string &skill)
{
    std::vector<std::pair<const ItemDefinition *, double>> found;

    for (const ItemDefinition &definition : items.entries())
    {
        const MawBaseItem *pBase = itemData.baseItem(definition.itemId);

        if (pBase != nullptr && definition.rarity == ItemRarity::Common
            && std::find(equipStats.begin(), equipStats.end(), definition.equipStat) != equipStats.end()
            && (skill.empty() || canonicalSkillName(definition.skillGroup) == skill))
        {
            found.emplace_back(&definition, pBase->rung);
        }
    }

    std::stable_sort(found.begin(), found.end(),
        [](const auto &left, const auto &right)
        {
            return left.second != right.second ? left.second > right.second : left.first->value > right.first->value;
        });
    std::vector<const ItemDefinition *> sorted;

    for (const auto &[pDefinition, rung] : found)
    {
        (void)rung;
        sorted.push_back(pDefinition);
    }

    return sorted;
}

const ItemDefinition *topBaseItem(
    const ItemTable &items,
    const MawItemData &itemData,
    std::initializer_list<const char *> equipStats,
    const std::string &skill)
{
    const std::vector<const ItemDefinition *> sorted = baseItems(items, itemData, equipStats, skill);
    return sorted.empty() ? nullptr : sorted.front();
}

// A slot and its base items, the best first: a lower rung serves when the member's level is too low for the top.
struct GearPick
{
    EquipmentSlot slot = EquipmentSlot::MainHand;
    std::vector<const ItemDefinition *> candidates;
};

std::vector<GearPick> chooseGear(const Character &character, const ItemTable &items, const MawItemData &itemData)
{
    std::vector<GearPick> picks;
    const auto add = [&picks](EquipmentSlot slot, std::vector<const ItemDefinition *> candidates)
    {
        if (!candidates.empty())
        {
            picks.push_back({slot, std::move(candidates)});
        }
    };
    const bool shield = character.findSkill("Shield") != nullptr;
    const CharacterSkill *pWeapon = bestSkill(character, {"Sword", "Axe", "Mace", "Spear", "Dagger", "Staff"});
    bool twoHanded = false;

    if (pWeapon != nullptr)
    {
        std::vector<const ItemDefinition *> weapons =
            shield ? baseItems(items, itemData, {"Weapon", "Weapon1or2"}, pWeapon->name)
                   : std::vector<const ItemDefinition *>();

        if (weapons.empty())
        {
            weapons = baseItems(items, itemData, {"Weapon", "Weapon1or2", "Weapon2"}, pWeapon->name);
        }

        twoHanded = !weapons.empty() && weapons.front()->equipStat == "Weapon2";
        add(EquipmentSlot::MainHand, weapons);
    }

    if (shield && !twoHanded)
    {
        add(EquipmentSlot::OffHand, baseItems(items, itemData, {"Shield"}, ""));
    }

    if (character.findSkill("Bow") != nullptr)
    {
        add(EquipmentSlot::Bow, baseItems(items, itemData, {"Missile"}, "Bow"));
    }

    if (const CharacterSkill *pArmor = bestSkill(character, {"PlateArmor", "ChainArmor", "LeatherArmor"}))
    {
        add(EquipmentSlot::Armor, baseItems(items, itemData, {"Armor"}, pArmor->name));
    }

    add(EquipmentSlot::Helm, baseItems(items, itemData, {"Helm"}, ""));
    add(EquipmentSlot::Belt, baseItems(items, itemData, {"Belt"}, ""));
    add(EquipmentSlot::Cloak, baseItems(items, itemData, {"Cloak"}, ""));
    add(EquipmentSlot::Gauntlets, baseItems(items, itemData, {"Gauntlets"}, ""));
    add(EquipmentSlot::Boots, baseItems(items, itemData, {"Boots"}, ""));
    add(EquipmentSlot::Amulet, baseItems(items, itemData, {"Amulet"}, ""));

    for (EquipmentSlot ring : {EquipmentSlot::Ring1, EquipmentSlot::Ring2, EquipmentSlot::Ring3, EquipmentSlot::Ring4,
             EquipmentSlot::Ring5, EquipmentSlot::Ring6})
    {
        add(ring, baseItems(items, itemData, {"Ring"}, ""));
    }

    return picks;
}

InventoryItem rolledItem(
    const MawRules &rules,
    const GameDataLoader &data,
    const ItemDefinition &definition,
    int level,
    MawRarity rarity,
    int legendaryAffix,
    std::mt19937 &rng)
{
    InventoryItem item = ItemGenerator::makeInventoryItem(definition.itemId, data.getItemTable(), ItemGenerationMode::Generic);
    rules.itemRules().rollEnchantmentsAtRarity(item, definition,
        {data.getItemTable(), data.getStandardItemEnchantTable(), data.getSpecialItemEnchantTable()}, level, rarity,
        legendaryAffix, rng);
    item.identified = true;
    return item;
}

// Into the first member, from `firstMember` on, with room in any bag; every member keeps the bag they had open.
bool grantToBags(Party &party, const InventoryItem &item, size_t firstMember)
{
    const int bagCount = std::max(1, party.rules().items.bagCount(party));
    const size_t memberCount = party.memberCount();

    for (size_t offset = 0; offset < memberCount; ++offset)
    {
        const size_t memberIndex = (firstMember + offset) % memberCount;
        Character *pMember = party.member(memberIndex);
        const uint8_t openBag = pMember->rulesetState.currentBag;
        bool granted = false;

        for (int bag = 0; bag < bagCount && !granted; ++bag)
        {
            InventoryBags::openBag(*pMember, uint8_t(bag), bagCount);
            granted = party.tryGrantInventoryItemToMember(memberIndex, item);
        }

        InventoryBags::openBag(*pMember, openBag, bagCount);

        if (granted)
        {
            return true;
        }
    }

    return false;
}

// Spreads a kit over the members, a kind at a time, so that no one member's bags fill first.
size_t grantKit(
    Party &party,
    MawRules &rules,
    const GameDataLoader &data,
    const MawTestPartyKit &kit,
    int stageLevel,
    std::mt19937 &rng,
    size_t &nextMember,
    size_t &lost)
{
    const ItemTable &items = data.getItemTable();
    size_t granted = 0;
    const auto give = [&](const InventoryItem &item)
    {
        if (party.memberCount() == 0)
        {
            return;
        }

        if (grantToBags(party, item, nextMember))
        {
            ++granted;
        }
        else
        {
            ++lost;
        }

        nextMember = (nextMember + 1) % party.memberCount();
    };

    for (const MawTestPartyKitItem &entry : kit.items)
    {
        const int level = entry.level > 0 ? entry.level : stageLevel;

        if (entry.dimensionMap)
        {
            const std::vector<uint16_t> pool = rules.dimensionMapPool();
            RandomStream stream(rng(), 0);

            for (uint32_t copy = 0; copy < entry.count && !pool.empty(); ++copy)
            {
                InventoryItem item = ItemGenerator::makeInventoryItem(DimensionMapItemId, items, ItemGenerationMode::Generic);
                rules.rollDimensionMap(stream, pool, {true, true, true, true}, 0, entry.power)
                    .writeFields(item.rulesetFields);
                item.identified = true;
                give(item);
            }

            continue;
        }

        if (entry.artifacts)
        {
            for (const MawArtifact &artifact : rules.itemData().artifacts())
            {
                if (items.get(artifact.itemId) != nullptr)
                {
                    InventoryItem item =
                        ItemGenerator::makeInventoryItem(artifact.itemId, items, ItemGenerationMode::Generic);
                    item.identified = true;
                    give(item);
                }
            }

            continue;
        }

        if (entry.firstAffix != 0)
        {
            // One Legendary jewel, belt or cloak per affix: anyone can wear them.
            const std::array<const char *, 4> Kinds = {"Amulet", "Ring", "Belt", "Cloak"};

            for (int affix = entry.firstAffix; affix <= entry.lastAffix; ++affix)
            {
                const ItemDefinition *pBase = topBaseItem(
                    items, rules.itemData(), {Kinds[size_t(affix) % Kinds.size()]}, "");

                if (pBase != nullptr)
                {
                    give(rolledItem(rules, data, *pBase, level, MawRarity::Legendary, affix, rng));
                }
            }

            continue;
        }

        for (uint32_t itemId = entry.firstId; itemId <= entry.lastId && itemId != 0; ++itemId)
        {
            const ItemDefinition *pDefinition = items.get(itemId);

            if (pDefinition == nullptr)
            {
                continue;
            }

            for (uint32_t copy = 0; copy < entry.count; ++copy)
            {
                InventoryItem item = ItemGenerator::makeInventoryItem(itemId, items, ItemGenerationMode::Generic);
                item.identified = true;

                if (entry.power > 0 && pDefinition->hasPotionPower)
                {
                    item.standardEnchantPower = uint16_t(entry.power);
                }

                // Reagents take their power from their level, as a drop of the stage's level does.
                if (pDefinition->equipStat == "Reagent")
                {
                    ItemGenerationRequest request;
                    request.dropLevel = level;
                    rules.itemRules().rollPlainItem(item, *pDefinition, request);
                }

                give(item);
            }
        }
    }

    return granted;
}

void setGoldAndFood(Party &party, int gold, int food)
{
    party.addGold(gold - party.gold());
    party.addFood(food - party.food());
}
}

bool MawTestPartyCatalog::loadFromYaml(const std::string &text, std::string &errorMessage)
{
    try
    {
        const YAML::Node root = YAML::Load(text);
        stages.clear();
        parties.clear();
        kits.clear();

        for (const YAML::Node &node : root["kits"])
        {
            MawTestPartyKit kit;
            kit.id = node["id"].as<std::string>();
            kit.title = node["title"].as<std::string>("");

            for (const YAML::Node &itemNode : node["items"])
            {
                MawTestPartyKitItem item;
                item.count = itemNode["count"].as<uint32_t>(1);
                item.power = itemNode["power"].as<int>(0);
                item.level = itemNode["level"].as<int>(0);

                if (itemNode["items"])
                {
                    readIdRange(itemNode["items"], item.firstId, item.lastId);
                }
                else if (itemNode["legendary_affixes"])
                {
                    uint32_t first = 0;
                    uint32_t last = 0;
                    readIdRange(itemNode["legendary_affixes"], first, last);
                    item.firstAffix = int(first);
                    item.lastAffix = int(last);
                }
                else if (itemNode["artifacts"])
                {
                    item.artifacts = itemNode["artifacts"].as<bool>();
                }
                else if (itemNode["dimension_maps"])
                {
                    item.dimensionMap = true;
                    item.count = itemNode["dimension_maps"].as<uint32_t>();
                }
                else
                {
                    errorMessage = "kit " + kit.id + ": an entry needs items, legendary_affixes, dimension_maps or artifacts";
                    return false;
                }

                kit.items.push_back(item);
            }

            kits.push_back(kit);
        }

        for (const YAML::Node &node : root["parties"])
        {
            MawTestPartyParty partyEntry;
            partyEntry.id = node["id"].as<std::string>();
            partyEntry.title = node["title"].as<std::string>("");

            for (const YAML::Node &memberNode : node["members"])
            {
                MawTestPartyMember member;
                member.name = memberNode["name"].as<std::string>("");
                member.className = memberNode["class"].as<std::string>();
                member.promotedClassName = memberNode["promoted"].as<std::string>("");
                member.race = memberNode["race"].as<std::string>("");
                partyEntry.members.push_back(member);
            }

            if (partyEntry.members.empty() || partyEntry.members.size() > 5)
            {
                errorMessage = "party " + partyEntry.id + " needs one to five members";
                return false;
            }

            parties.push_back(partyEntry);
        }

        for (const YAML::Node &node : root["stages"])
        {
            MawTestPartyStage stageEntry;
            stageEntry.id = node["id"].as<std::string>();
            stageEntry.title = node["title"].as<std::string>("");
            stageEntry.level = node["level"].as<int>(1);
            stageEntry.skillLevel = node["skill_level"].as<int>(1);
            stageEntry.stats = node["stats"].as<int>(15);
            stageEntry.promoted = node["promoted"].as<bool>(false);
            stageEntry.gear.level = node["gear"]["level"].as<int>(stageEntry.level);
            stageEntry.gear.rarity = node["gear"]["rarity"].as<std::string>("common");
            stageEntry.gold = node["gold"].as<int>(0);
            stageEntry.food = node["food"].as<int>(20);
            stageEntry.kits = readStrings(node["kits"]);
            stageEntry.completedMaps = readStrings(node["completed_maps"]);
            stageEntry.completeAllMaps = node["complete_all_maps"].as<bool>(false);
            stageEntry.dimensionQuestDone = node["dimension_quest_done"].as<bool>(false);
            stageEntry.map = node["map"].as<std::string>("");
            stageEntry.party = node["party"].as<std::string>("");

            for (const YAML::Node &bank : node["banks"])
            {
                stageEntry.banks.push_back(bank.as<double>());
            }

            for (const YAML::Node &bit : node["quest_bits"])
            {
                stageEntry.questBits.push_back(bit.as<uint32_t>());
            }

            if (!parseRarity(stageEntry.gear.rarity))
            {
                errorMessage = "stage " + stageEntry.id + ": unknown gear rarity " + stageEntry.gear.rarity;
                return false;
            }

            if (!stageEntry.banks.empty() && stageEntry.banks.size() != MawGameState::ContinentCount)
            {
                errorMessage = "stage " + stageEntry.id + ": banks are MM8, MM7, MM6 and MM9";
                return false;
            }

            for (const std::string &kitId : stageEntry.kits)
            {
                if (kit(kitId) == nullptr)
                {
                    errorMessage = "stage " + stageEntry.id + ": unknown kit " + kitId;
                    return false;
                }
            }

            stages.push_back(stageEntry);
        }
    }
    catch (const YAML::Exception &exception)
    {
        errorMessage = exception.what();
        return false;
    }

    if (stages.empty() || parties.empty())
    {
        errorMessage = "the catalog needs stages and parties";
        return false;
    }

    return true;
}

const MawTestPartyStage *MawTestPartyCatalog::stage(const std::string &id) const
{
    for (const MawTestPartyStage &entry : stages)
    {
        if (entry.id == lowerCopy(id))
        {
            return &entry;
        }
    }

    return nullptr;
}

const MawTestPartyParty *MawTestPartyCatalog::party(const std::string &id) const
{
    for (const MawTestPartyParty &entry : parties)
    {
        if (entry.id == lowerCopy(id))
        {
            return &entry;
        }
    }

    return nullptr;
}

const MawTestPartyKit *MawTestPartyCatalog::kit(const std::string &id) const
{
    for (const MawTestPartyKit &entry : kits)
    {
        if (entry.id == lowerCopy(id))
        {
            return &entry;
        }
    }

    return nullptr;
}

std::string MawTestPartyCatalog::listing() const
{
    std::ostringstream text;
    text << "Stages:";

    for (const MawTestPartyStage &entry : stages)
    {
        text << "\n  " << entry.id << " - " << entry.title;
    }

    text << "\nParties:";

    for (const MawTestPartyParty &entry : parties)
    {
        text << "\n  " << entry.id << " - " << entry.title;
    }

    text << "\nKits (+name):";

    for (const MawTestPartyKit &entry : kits)
    {
        text << "\n  " << entry.id << " - " << entry.title;
    }

    return text.str();
}

bool parseMawTestPartyRequest(
    const std::vector<std::string> &args,
    const MawTestPartyCatalog &catalog,
    MawTestPartyRequest &request,
    std::string &errorMessage)
{
    request = {};

    for (const std::string &arg : args)
    {
        if (request.pStage == nullptr)
        {
            request.pStage = catalog.stage(arg);

            if (request.pStage == nullptr)
            {
                errorMessage = "Unknown stage: " + arg + " (testparty list)";
                return false;
            }
        }
        else if (!arg.empty() && arg.front() == '+')
        {
            const MawTestPartyKit *pKit = catalog.kit(arg.substr(1));

            if (pKit == nullptr)
            {
                errorMessage = "Unknown kit: " + arg.substr(1);
                return false;
            }

            request.kits.push_back(pKit);
        }
        else if (request.pParty == nullptr && catalog.party(arg) != nullptr)
        {
            request.pParty = catalog.party(arg);
        }
        else
        {
            request.rulesetOptions += (request.rulesetOptions.empty() ? "" : ":") + lowerCopy(arg);
        }
    }

    if (request.pStage == nullptr)
    {
        errorMessage = "Name a stage (testparty list).";
        return false;
    }

    if (request.pParty == nullptr)
    {
        request.pParty = catalog.party(request.pStage->party);
        request.pParty = request.pParty != nullptr ? request.pParty : &catalog.parties.front();
    }

    return true;
}

std::vector<Character> mawTestPartyShells(const MawTestPartyRequest &request, const GameDataLoader &data)
{
    std::vector<Character> shells;

    for (size_t index = 0; index < request.pParty->members.size(); ++index)
    {
        const MawTestPartyMember &member = request.pParty->members[index];
        shells.push_back(makeShell(data, member, memberClassName(member, *request.pStage), index));
    }

    return shells;
}

std::string applyMawTestParty(
    Party &party,
    MawRules &rules,
    const GameDataLoader &data,
    const MawTestPartyCatalog &catalog,
    const MawTestPartyRequest &request,
    uint32_t seed)
{
    const MawTestPartyStage &stage = *request.pStage;
    const GameRules &gameRules = party.rules();
    std::mt19937 rng(seed);
    std::vector<Character> members = mawTestPartyShells(request, data);

    for (Character &member : members)
    {
        member.level = uint32_t(std::max(stage.level, 1));
        member.experience = member.level > 1 ? gameRules.experience.experienceForNextLevel(member.level - 1) : 0;
        const uint32_t stat = uint32_t(std::max(stage.stats, 1));
        member.might = stat;
        member.intellect = stat;
        member.personality = stat;
        member.endurance = stat;
        member.accuracy = stat;
        member.speed = stat;
        member.luck = stat;
        grantSkills(member, gameRules, data.getClassSkillTable(), stage.skillLevel);
        learnSpells(member, gameRules, data.getSpellTable());
        GameMechanics::refreshCharacterBaseResources(member, true, &data.getClassMultiplierTable());
    }

    Party::Snapshot snapshot = party.snapshot();
    snapshot.members = members;
    snapshot.activeMemberIndex = 0;
    snapshot.characterBuffs = {};
    party.restoreSnapshot(snapshot);

    // MAW's banks and completed maps first: monsters, item levels and dimension maps read them.
    MawGameState state = rules.state();

    if (!stage.banks.empty())
    {
        std::copy(stage.banks.begin(), stage.banks.end(), state.continentLevels.begin());
    }

    for (const std::string &map : stage.completedMaps)
    {
        state.completedMaps.insert(lowerCopy(map));
    }

    if (stage.completeAllMaps)
    {
        for (const MapStatsEntry &map : data.getMapStats().getEntries())
        {
            if (!map.fileName.empty())
            {
                state.completedMaps.insert(lowerCopy(map.fileName));
            }
        }
    }

    state.dimensionQuest.done = state.dimensionQuest.done || stage.dimensionQuestDone;
    rules.setState(state);

    for (uint32_t questBit : stage.questBits)
    {
        party.setQuestBit(questBit, true);
    }

    const MawRarity rarity = parseRarity(stage.gear.rarity).value_or(MawRarity::Common);
    size_t worn = 0;
    size_t refused = 0;
    std::set<std::string> refusals;

    for (size_t memberIndex = 0; memberIndex < party.memberCount(); ++memberIndex)
    {
        const std::vector<GearPick> picks = chooseGear(*party.member(memberIndex), data.getItemTable(), rules.itemData());

        const Character &member = *party.member(memberIndex);

        for (const GearPick &pick : picks)
        {
            // MAW asks a level a little above an item's drop level: roll lower until the member can wear it, and
            // take a lower rung when even a level-0 roll of the best is too much (a level-1 party).
            InventoryItem item;
            const auto wearable = [&]()
            {
                const ItemDefinition &definition = *data.getItemTable().get(item.objectDescriptionId);
                return rules.itemRules().levelRequirement(definition, item.rulesetFields) <= int(member.level);
            };

            for (const ItemDefinition *pCandidate : pick.candidates)
            {
                item = rolledItem(rules, data, *pCandidate, stage.gear.level, rarity, 0, rng);

                for (int level = stage.gear.level - 1; level >= 0 && !wearable(); --level)
                {
                    item = rolledItem(rules, data, *pCandidate, level, rarity, 0, rng);
                }

                if (wearable())
                {
                    break;
                }
            }

            std::optional<InventoryItem> held;

            if (party.tryEquipItemOnMember(memberIndex, pick.slot, item, std::nullopt, true, held))
            {
                ++worn;
            }
            else
            {
                ++refused;
                refusals.insert(party.lastStatus());
                grantToBags(party, item, memberIndex);
            }
        }
    }

    size_t nextMember = 0;
    size_t granted = 0;
    size_t lost = 0;
    std::vector<const MawTestPartyKit *> kits;

    for (const std::string &kitId : stage.kits)
    {
        kits.push_back(catalog.kit(kitId));
    }

    kits.insert(kits.end(), request.kits.begin(), request.kits.end());

    for (const MawTestPartyKit *pKit : kits)
    {
        granted += grantKit(party, rules, data, *pKit, stage.level, rng, nextMember, lost);
    }

    setGoldAndFood(party, stage.gold, stage.food);
    party.refreshDerivedState();

    for (size_t memberIndex = 0; memberIndex < party.memberCount(); ++memberIndex)
    {
        Character &member = *party.member(memberIndex);
        member.health = Party::effectiveMaximumHealth(member);
        member.spellPoints = Party::effectiveMaximumSpellPoints(member);
    }

    std::ostringstream text;
    text << request.pParty->title << " at " << stage.title << ": " << party.memberCount() << " members, level "
         << stage.level << ", " << worn << " items worn (" << mawRarityName(rarity) << ")";

    if (refused > 0)
    {
        text << ", " << refused << " refused (in the bags:";

        for (const std::string &refusal : refusals)
        {
            text << ' ' << refusal << ';';
        }

        text << ')';
    }

    if (granted > 0 || lost > 0)
    {
        text << ", " << granted << " kit items";
    }

    if (lost > 0)
    {
        text << " (" << lost << " did not fit)";
    }

    return text.str();
}

std::string addMawTestPartyKit(
    Party &party,
    MawRules &rules,
    const GameDataLoader &data,
    const MawTestPartyKit &kit,
    uint32_t seed)
{
    std::mt19937 rng(seed);
    size_t nextMember = party.activeMemberIndex();
    size_t lost = 0;
    int level = 1;

    for (size_t memberIndex = 0; memberIndex < party.memberCount(); ++memberIndex)
    {
        level = std::max(level, int(party.member(memberIndex)->level));
    }

    const size_t granted = grantKit(party, rules, data, kit, level, rng, nextMember, lost);
    std::string text = kit.title + ": " + std::to_string(granted) + " items";
    return lost > 0 ? text + " (" + std::to_string(lost) + " did not fit)" : text;
}
}
