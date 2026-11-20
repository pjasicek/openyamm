// Scratch harness (not part of the repository): builds concrete MAW characters with the real MAW-patched game data
// and asks the engine's own functions for their numbers. Input: SOLO_SPEC (YAML), output: one JSON line per case.
#include <doctest/doctest.h>

#include "engine/AssetFileSystem.h"
#include "game/content/RulesetDefinition.h"
#include "game/content/RulesetOptions.h"
#include "game/data/GameDataLoader.h"
#include "game/data/GameDataRepository.h"
#include "game/gameplay/GameMechanics.h"
#include "game/items/ItemGenerator.h"
#include "game/party/Party.h"
#include "game/tables/ClassMultiplierTable.h"
#include "game/tables/CharacterDollTable.h"
#include "game/party/SpellSchool.h"
#include "game/rules/maw/MawBalanceModel.h"
#include "game/rules/maw/MawClassRules.h"
#include "game/rules/maw/MawCombatRules.h"
#include "game/rules/maw/MawItemData.h"
#include "game/rules/maw/MawItemRules.h"
#include "game/rules/maw/MawRules.h"
#include "game/rules/maw/MawRulesFactory.h"
#include "game/rules/maw/MawSkillFormulas.h"
#include "game/rules/maw/MawAuras.h"
#include "game/rules/GameRules.h"
#include "game/rules/CraftingRules.h"
#include "game/rules/maw/MawCharacterSheet.h"

#include <yaml-cpp/yaml.h>

#include <algorithm>
#include <functional>
#include <cmath>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <random>
#include <sstream>

using namespace OpenYAMM;
using namespace OpenYAMM::Game;

namespace
{
std::vector<const ItemDefinition *> baseItems(const ItemTable &items, const MawItemData &itemData,
    std::initializer_list<const char *> equipStats, const std::string &skill)
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
    std::stable_sort(found.begin(), found.end(), [](const auto &a, const auto &b)
        { return a.second != b.second ? a.second > b.second : a.first->value > b.first->value; });
    std::vector<const ItemDefinition *> out;
    for (const auto &entry : found)
    {
        out.push_back(entry.first);
    }
    return out;
}

MawRarity rarityFromName(const std::string &name)
{
    static const std::vector<std::pair<std::string, MawRarity>> Names = {{"common", MawRarity::Common},
        {"uncommon", MawRarity::Uncommon}, {"rare", MawRarity::Rare}, {"epic", MawRarity::Epic},
        {"ancient", MawRarity::Ancient}, {"primordial", MawRarity::Primordial}, {"legendary", MawRarity::Legendary},
        {"celestial", MawRarity::Celestial}};
    for (const auto &[text, rarity] : Names)
    {
        if (text == name)
        {
            return rarity;
        }
    }
    return MawRarity::Common;
}

const char *typeName(CombatDamageType type)
{
    static const char *Names[] = {"phys", "fire", "air", "water", "earth", "spirit", "mind", "body", "light", "dark",
        "energy", "irresistible"};
    return Names[size_t(type)];
}
}

TEST_CASE("solo harness")
{
    const char *pSpec = std::getenv("SOLO_SPEC");
    const char *pOut = std::getenv("SOLO_OUT");
    REQUIRE(pSpec != nullptr);
    REQUIRE(pOut != nullptr);
    const YAML::Node spec = YAML::LoadFile(pSpec);

    Engine::AssetFileSystem assetFileSystem;
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    REQUIRE(assetFileSystem.initialize(sourceRoot, sourceRoot / "assets_dev", Engine::AssetScaleTier::X1,
        spec["world"].as<std::string>("mm8")));
    std::vector<RulesetDefinition> rulesets;
    std::string error;
    REQUIRE_MESSAGE(loadAvailableRulesets(assetFileSystem, rulesets, error), error);
    const auto maw = std::find_if(rulesets.begin(), rulesets.end(), [](const RulesetDefinition &r) { return r.id == "maw"; });
    REQUIRE(maw != rulesets.end());
    GameDataLoader dataLoader = {};
    dataLoader.setActiveRuleset(*maw);
    REQUIRE(dataLoader.loadCommonForGameplay(assetFileSystem));
    GameDataRepository data;
    data.bind(dataLoader);
    std::ofstream out(pOut);

    for (const YAML::Node &c : spec["cases"])
    {
        RulesetOptions options = maw->defaultOptions();
        REQUIRE(applyRulesetOptionIds(c["options"].as<std::string>("maw:free"), options));
        std::unique_ptr<MawRules> pRules = createMawRules(data, options);
        REQUIRE(pRules != nullptr);
        MawRules &rules = *pRules;
        if (c["promotion_worlds"])
        {
            if (const ClassMultiplierEntry *pEntry =
                    dataLoader.getClassMultiplierTable().get(canonicalClassName(c["class"].as<std::string>())))
            {
                rules.setPromotionWorlds({{pEntry->classKind, c["promotion_worlds"].as<int>()}});
            }
        }
        const int monsterLevel = c["monster_level"].as<int>();
        // A member of the party-of-five reference run: the model, the power report and the class defence take the
        // party's size. The Party object still holds this one member.
        const int partyCount = std::max(1, c["party_count"].as<int>(1));
        MawGameState state = rules.state();
        state.continentLevels = {};
        state.continentLevels[0] = float(c["bank_level"].as<int>(monsterLevel));
        rules.setState(state);

        Party party;
        party.setItemTable(&dataLoader.getItemTable());
        party.setCharacterDollTable(&dataLoader.getCharacterDollTable());
        party.setClassSkillTable(&dataLoader.getClassSkillTable());
        party.setClassMultiplierTable(&dataLoader.getClassMultiplierTable());
        party.setItemEnchantTables(&dataLoader.getStandardItemEnchantTable(), &dataLoader.getSpecialItemEnchantTable());
        party.setRules(&rules.gameRules());
        bindGameRules(&rules.gameRules());
        rules.setSpellTable(&dataLoader.getSpellTable());
        rules.setItemTable(&dataLoader.getItemTable());
        rules.setClassMultiplierTable(&dataLoader.getClassMultiplierTable());
        rules.setItemEnchantTables(&dataLoader.getStandardItemEnchantTable(), &dataLoader.getSpecialItemEnchantTable());

        Character member = {};
        member.name = c["id"].as<std::string>();
        member.className = c["class"].as<std::string>();
        member.raceId = c["race"].as<uint32_t>(0);
        member.level = c["level"].as<uint32_t>();
        if (c["portrait"])
        {
            member.characterDataId = c["portrait"].as<uint32_t>();
            member.portraitPictureId = member.characterDataId - 1;
        }
        member.experience = member.level > 1 ? party.rules().experience.experienceForNextLevel(member.level - 1) : 0;
        const YAML::Node stats = c["stats"];
        member.might = stats["might"].as<uint32_t>(15);
        member.intellect = stats["intellect"].as<uint32_t>(15);
        member.personality = stats["personality"].as<uint32_t>(15);
        member.endurance = stats["endurance"].as<uint32_t>(15);
        member.accuracy = stats["accuracy"].as<uint32_t>(15);
        member.speed = stats["speed"].as<uint32_t>(15);
        member.luck = stats["luck"].as<uint32_t>(15);
        std::ostringstream warnings;

        for (const auto &entry : c["skills"])
        {
            const std::string name = canonicalSkillName(entry.first.as<std::string>());
            const uint32_t level = entry.second[0].as<uint32_t>();
            uint32_t mastery = entry.second[1].as<uint32_t>();
            uint32_t cap =
                uint32_t(dataLoader.getClassSkillTable().getEffectiveCap(member.className, member.raceId, name));
            // Solo talent tree v2: Lone Discipline lifts a solo's Bodybuilding cap (TALENT_TREE_V2.md).
            if (c["cap_raise"] && c["cap_raise"][entry.first.as<std::string>()])
            {
                cap = std::max(cap, c["cap_raise"][entry.first.as<std::string>()].as<uint32_t>());
            }
            if (mastery > cap)
            {
                warnings << name << " mastery " << mastery << ">cap " << cap << "; ";
                mastery = cap;
            }
            if (cap == 0)
            {
                warnings << name << " not learnable; ";
                continue;
            }
            member.skills[name] = {name, level, SkillMastery(mastery)};
        }

        // A solo run's learned talents (passives apply through MAW's rules when the options carry "solo").
        for (const auto &talent : (c["talents"] ? c["talents"] : YAML::Node(YAML::NodeType::Map)))
        {
            member.talentRanks[talent.first.as<std::string>()] = uint16_t(talent.second.as<int>());
        }

        for (const YAML::Node &spell : (c["spells"] ? c["spells"] : YAML::Node(YAML::NodeType::Sequence)))
        {
            member.learnSpell(spell.as<uint32_t>());
        }

        if (c["learn_school_spells"].as<bool>(false))
        {
            for (const SpellEntry &spell : dataLoader.getSpellTable().entries())
            {
                const std::optional<std::string> school =
                    spell.id > 0 ? resolveMagicSkillName(uint32_t(spell.id)) : std::nullopt;
                const CharacterSkill *pSkill = school ? member.findSkill(*school) : nullptr;
                if (pSkill != nullptr && pSkill->mastery >= spell.requiredMastery)
                {
                    member.learnSpell(uint32_t(spell.id));
                }
            }
        }

        // Potions: buff auras by power, Regeneration potion by power.
        const YAML::Node potions = c["potions"] ? c["potions"] : YAML::Node();
        if (potions.IsMap())
        {
            for (const auto &aura : potions["auras"])
            {
                member.rulesetState.potionEffects.push_back({TimedPotionEffect::Kind::Aura,
                    aura.first.as<uint32_t>(), aura.second.as<int>(), 1.0e7f});
            }
            if (potions["regen"])
            {
                member.rulesetState.potionEffects.push_back({TimedPotionEffect::Kind::Regeneration, 0,
                    potions["regen"].as<int>() / 2, 1.0e7f});
            }
        }

        GameMechanics::refreshCharacterBaseResources(member, true, &dataLoader.getClassMultiplierTable());
        Party::Snapshot snapshot = party.snapshot();
        snapshot.members = {member};
        snapshot.activeMemberIndex = 0;
        snapshot.characterBuffs = {};
        party.restoreSnapshot(snapshot);

        // Gear.
        const bool hasGear = bool(c["gear"]);
        const YAML::Node gear = hasGear ? c["gear"] : YAML::Node(YAML::NodeType::Map);
        int gearLevel = gear["level"].as<int>(0);
        MawRarity rarity = rarityFromName(gear["rarity"].as<std::string>("epic"));
        // Set while a pool case buys the plain weapon or armour its loot did not hold (below).
        bool shopFallback = false;
        const int craftedPower = gear["crafted_power"].as<int>(0);
        std::mt19937 rng(gear["seed"].as<uint32_t>(7));
        const ItemTable &items = dataLoader.getItemTable();
        const ItemRollTables tables = {items, dataLoader.getStandardItemEnchantTable(), dataLoader.getSpecialItemEnchantTable()};
        int worn = 0;
        const CharacterDollEntry *pDoll = dataLoader.getCharacterDollTable().getCharacter(party.member(0)->characterDataId);
        const CharacterDollTypeEntry *pDollType =
            pDoll != nullptr ? dataLoader.getCharacterDollTable().getDollType(pDoll->dollTypeId) : nullptr;
        const auto dollAllows = [&](const ItemDefinition &definition)
        {
            if (pDollType == nullptr) return true;
            const std::string &stat = definition.equipStat;
            if (stat == "Missile") return pDollType->canEquipBow;
            if (stat == "Armor") return pDollType->canEquipArmor;
            if (stat == "Helm") return pDollType->canEquipHelm;
            if (stat == "Belt") return pDollType->canEquipBelt;
            if (stat == "Boots") return pDollType->canEquipBoots;
            if (stat == "Cloak") return pDollType->canEquipCloak;
            if (stat == "Weapon" || stat == "Weapon1or2" || stat == "Weapon2" || stat == "Shield") return pDollType->canEquipWeapon;
            return true;
        };
        int dollRefused = 0;
        const auto equip = [&](EquipmentSlot slot, const std::vector<const ItemDefinition *> &candidates, bool crafted)
        {
            const Character &held = *party.member(0);
            if (c["pool"] && !shopFallback)
            {
                return false;
            }
            if (!candidates.empty() && !dollAllows(*candidates.front()))
            {
                ++dollRefused;
                return false;
            }
            for (const ItemDefinition *pCandidate : candidates)
            {
                // A bought or starting item is of the rung its level sells: MAW's ladders climb a rung per 15 levels.
                if ((shopFallback || gear["basic_only"].as<bool>(false))
                    && rules.itemData().baseItem(pCandidate->itemId) != nullptr
                    && rules.itemData().baseItem(pCandidate->itemId)->rung > 1 + gearLevel / 15.0)
                {
                    continue;
                }
                for (int level = gearLevel; level >= 0; --level)
                {
                    InventoryItem item =
                        ItemGenerator::makeInventoryItem(pCandidate->itemId, items, ItemGenerationMode::Generic);
                    rules.itemRules().rollEnchantmentsAtRarity(item, *pCandidate, tables, level, rarity, 0, rng);
                    item.identified = true;
                    if (crafted && craftedPower > item.rulesetFields.itemPower)
                    {
                        item.rulesetFields.itemPower = uint16_t(craftedPower);
                    }
                    if (rules.itemRules().levelRequirement(*pCandidate, item.rulesetFields) > int(held.level))
                    {
                        continue;
                    }
                    std::optional<InventoryItem> displaced;
                    if (party.tryEquipItemOnMember(0, slot, item, std::nullopt, true, displaced))
                    {
                        ++worn;
                        return true;
                    }
                    warnings << "equip refused slot " << int(slot) << " item " << pCandidate->itemId << " ("
                             << party.lastStatus() << "); ";
                    return false;
                }
            }
            return false;
        };
        const MawItemData &itemData = rules.itemData();
        const std::string mainSkill = gear["main"].as<std::string>("");
        if (!mainSkill.empty())
        {
            const bool two = gear["two_handed"].as<bool>(false);
            std::vector<const ItemDefinition *> weapons = two
                ? baseItems(items, itemData, {"Weapon2"}, canonicalSkillName(mainSkill))
                : baseItems(items, itemData, {"Weapon", "Weapon1or2"}, canonicalSkillName(mainSkill));
            if (weapons.empty())
            {
                weapons = baseItems(items, itemData, {"Weapon", "Weapon1or2", "Weapon2"}, canonicalSkillName(mainSkill));
            }
            equip(EquipmentSlot::MainHand, weapons, true);
        }
        if (gear["off"])
        {
            const std::string off = gear["off"].as<std::string>();
            if (off == "Shield")
            {
                equip(EquipmentSlot::OffHand, baseItems(items, itemData, {"Shield"}, ""), true);
            }
            else
            {
                const bool two = gear["off_two_handed"].as<bool>(false);
                equip(EquipmentSlot::OffHand,
                    two ? baseItems(items, itemData, {"Weapon2"}, canonicalSkillName(off))
                        : baseItems(items, itemData, {"Weapon", "Weapon1or2"}, canonicalSkillName(off)),
                    true);
            }
        }
        if (gear["bow"].as<bool>(false))
        {
            equip(EquipmentSlot::Bow, baseItems(items, itemData, {"Missile"}, "Bow"), true);
        }
        if (gear["armor"])
        {
            equip(EquipmentSlot::Armor, baseItems(items, itemData, {"Armor"}, canonicalSkillName(gear["armor"].as<std::string>())),
                true);
        }
        for (const auto &[slot, stat] : !hasGear ? std::vector<std::pair<EquipmentSlot, const char *>>{} : std::vector<std::pair<EquipmentSlot, const char *>>{{EquipmentSlot::Helm, "Helm"},
                 {EquipmentSlot::Belt, "Belt"}, {EquipmentSlot::Cloak, "Cloak"}, {EquipmentSlot::Gauntlets, "Gauntlets"},
                 {EquipmentSlot::Boots, "Boots"}, {EquipmentSlot::Amulet, "Amulet"}, {EquipmentSlot::Ring1, "Ring"},
                 {EquipmentSlot::Ring2, "Ring"}, {EquipmentSlot::Ring3, "Ring"}, {EquipmentSlot::Ring4, "Ring"},
                 {EquipmentSlot::Ring5, "Ring"}, {EquipmentSlot::Ring6, "Ring"}})
        {
            if (gear["basic_only"].as<bool>(false))
            {
                continue;
            }
            if (gear["no_armor_slots"].as<bool>(false) && stat != std::string("Amulet") && stat != std::string("Ring")
                && stat != std::string("Belt") && stat != std::string("Cloak"))
            {
                continue;
            }
            // A dragon's doll type allows rings, the amulet and gauntlets only (isRestrictedByDollType).
            if (gear["dragon_slots"].as<bool>(false) && stat != std::string("Amulet") && stat != std::string("Ring")
                && stat != std::string("Gauntlets"))
            {
                continue;
            }
            equip(slot, baseItems(items, itemData, {stat}, ""), false);
        }

        // Items rolled exactly as the scenario step grant_item {item_id, roll_level, seed, equip} rolls them.
        for (const YAML::Node &entry : (c["rolled_items"] ? c["rolled_items"] : YAML::Node(YAML::NodeType::Sequence)))
        {
            const std::string slotName = entry[0].as<std::string>();
            const uint32_t itemId = entry[1].as<uint32_t>();
            const ItemDefinition &definition = *items.get(itemId);
            InventoryItem item = ItemGenerator::makeInventoryItem(itemId, items, ItemGenerationMode::Generic);
            item.identified = true;
            if (entry[2].as<int>(0) > 0)
            {
                ItemGenerationRequest request;
                request.treasureLevel = 6;
                request.allowRareItems = false;
                request.dropLevel = entry[2].as<int>();
                request.boss = false;
                std::mt19937 itemRng(entry[3].as<uint32_t>(itemId));
                party.rules().items.rollEnchantments(item, definition, tables, request, nullptr, itemRng);
                item.identified = true;
            }
            static const std::vector<std::pair<std::string, EquipmentSlot>> Slots = {{"main_hand", EquipmentSlot::MainHand},
                {"off_hand", EquipmentSlot::OffHand}, {"bow", EquipmentSlot::Bow}, {"armor", EquipmentSlot::Armor},
                {"helm", EquipmentSlot::Helm}, {"belt", EquipmentSlot::Belt}, {"cloak", EquipmentSlot::Cloak},
                {"gauntlets", EquipmentSlot::Gauntlets}, {"boots", EquipmentSlot::Boots},
                {"amulet", EquipmentSlot::Amulet}, {"ring1", EquipmentSlot::Ring1}, {"ring2", EquipmentSlot::Ring2}};
            for (const auto &[name, slot] : Slots)
            {
                if (name == slotName)
                {
                    std::optional<InventoryItem> displaced;
                    if (party.tryEquipItemOnMember(0, slot, item, std::nullopt, true, displaced))
                    {
                        ++worn;
                    }
                    else
                    {
                        warnings << "rolled equip refused " << itemId << "; ";
                    }
                }
            }
        }

        // Gear chosen from a simulated playthrough's loot (c["pool"]), then the crafting materials it found.
        std::ostringstream craftLog;
        if (c["pool"])
        {
            const StandardItemEnchantTable *pStdTable = &dataLoader.getStandardItemEnchantTable();
            const SpecialItemEnchantTable *pSpecialTable = &dataLoader.getSpecialItemEnchantTable();
            if (c["quick_spell"])
            {
                const SpellEntry *pQuick = dataLoader.getSpellTable().findByName(c["quick_spell"].as<std::string>());
                if (pQuick != nullptr && party.member(0)->knowsSpell(uint32_t(pQuick->id)))
                {
                    party.member(0)->quickSpellName = c["quick_spell"].as<std::string>();
                }
            }
            const std::string merit = c["merit"].as<std::string>("melee");
            const auto meritOf = [&]() -> double
            {
                party.refreshDerivedState();
                Character &h = *party.member(0);
                const MawPowerReport rep = mawPowerReport(rules, h, items, pStdTable, pSpecialTable, partyCount);
                const MawLeech lch = mawLeech(rules, h, &items);
                double dps = rep.melee * (1 + 4 * lch.melee);
                if (merit == "bow")
                {
                    dps = rep.ranged * (1 + 4 * lch.ranged);
                }
                else if (merit == "spell")
                {
                    dps = rep.spell * std::sqrt(std::max(1, Party::effectiveMaximumSpellPoints(h)));
                }
                else if (merit == "breath")
                {
                    const CharacterAttackProfile prof =
                        GameMechanics::buildCharacterAttackProfile(h, &items, &dataLoader.getSpellTable());
                    dps = (prof.rangedMinDamage + prof.rangedMaxDamage) / 2.0 + rep.melee;
                }
                return std::max(dps, 1e-6) * std::max(rep.vitality, 1e-6);
            };
            std::vector<InventoryItem> poolItems;
            for (const YAML::Node &entry : c["pool"])
            {
                InventoryItem item = ItemGenerator::makeInventoryItem(entry[0].as<uint32_t>(), items, ItemGenerationMode::Generic);
                item.standardEnchantId = entry[1].as<uint16_t>();
                item.standardEnchantPower = entry[2].as<uint16_t>();
                item.rulesetFields.secondStandardEnchantId = entry[3].as<uint16_t>();
                item.rulesetFields.secondStandardEnchantPower = entry[4].as<uint16_t>();
                item.specialEnchantId = entry[5].as<uint16_t>();
                item.rulesetFields.itemPower = entry[6].as<uint16_t>();
                item.rulesetFields.lootRarity = entry[7].as<uint8_t>();
                item.rulesetFields.dropLevel = entry[8].as<uint16_t>();
                item.rulesetFields.legendaryAffixId = entry[9].as<uint16_t>();
                item.rulesetFields.ancientTier = entry[10].as<uint8_t>();
                item.identified = true;
                const ItemDefinition *pDef = items.get(item.objectDescriptionId);
                if (pDef != nullptr && rules.itemRules().levelRequirement(*pDef, item.rulesetFields) <= int(party.member(0)->level)
                    && dollAllows(*pDef))
                {
                    poolItems.push_back(item);
                }
            }
            const std::string mainSkill = canonicalSkillName(gear["main"].as<std::string>(""));
            const bool mainTwo = gear["two_handed"].as<bool>(false);
            const std::string off = gear["off"].as<std::string>("");
            const bool offTwo = gear["off_two_handed"].as<bool>(false);
            const std::string armorSkill = canonicalSkillName(gear["armor"].as<std::string>(""));
            const bool bow = gear["bow"].as<bool>(false);
            struct SlotPlan { EquipmentSlot slot; std::function<bool(const ItemDefinition &)> fits; };
            std::vector<SlotPlan> plan;
            const auto weaponFits = [](const std::string &skill, bool two)
            {
                return [skill, two](const ItemDefinition &d)
                {
                    const bool isTwo = d.equipStat == "Weapon2";
                    return (d.equipStat == "Weapon" || d.equipStat == "Weapon1or2" || d.equipStat == "Weapon2")
                        && canonicalSkillName(d.skillGroup) == skill && (two ? isTwo : !isTwo);
                };
            };
            if (!mainSkill.empty())
            {
                plan.push_back({EquipmentSlot::MainHand, weaponFits(mainSkill, mainTwo)});
            }
            if (off == "Shield")
            {
                plan.push_back({EquipmentSlot::OffHand, [](const ItemDefinition &d) { return d.equipStat == "Shield"; }});
            }
            else if (!off.empty())
            {
                plan.push_back({EquipmentSlot::OffHand, weaponFits(canonicalSkillName(off), offTwo)});
            }
            if (bow)
            {
                plan.push_back({EquipmentSlot::Bow, [](const ItemDefinition &d) { return d.equipStat == "Missile"; }});
            }
            if (!armorSkill.empty())
            {
                plan.push_back({EquipmentSlot::Armor, [armorSkill](const ItemDefinition &d)
                    { return d.equipStat == "Armor" && canonicalSkillName(d.skillGroup) == armorSkill; }});
            }
            for (const auto &[slot, stat] : std::vector<std::pair<EquipmentSlot, std::string>>{{EquipmentSlot::Helm, "Helm"},
                     {EquipmentSlot::Belt, "Belt"}, {EquipmentSlot::Cloak, "Cloak"}, {EquipmentSlot::Gauntlets, "Gauntlets"},
                     {EquipmentSlot::Boots, "Boots"}, {EquipmentSlot::Amulet, "Amulet"}, {EquipmentSlot::Ring1, "Ring"},
                     {EquipmentSlot::Ring2, "Ring"}, {EquipmentSlot::Ring3, "Ring"}, {EquipmentSlot::Ring4, "Ring"},
                     {EquipmentSlot::Ring5, "Ring"}, {EquipmentSlot::Ring6, "Ring"}})
            {
                const std::string want = stat;
                plan.push_back({slot, [want](const ItemDefinition &d) { return d.equipStat == want; }});
            }
            std::vector<int> used(poolItems.size(), -1);
            const auto clearSlot = [&](EquipmentSlot slot)
            {
                std::optional<InventoryItem> held;
                InventoryItem empty = {};
                (void)empty;
                party.member(0)->equipment = party.member(0)->equipment;
                return held;
            };
            (void)clearSlot;
            std::map<int, int> chosen;   // plan index -> pool index
            for (int pass = 0; pass < 2; ++pass)
            {
                for (size_t pi = 0; pi < plan.size(); ++pi)
                {
                    double bestMerit = -1;
                    int bestIndex = -1;
                    std::optional<InventoryItem> current = party.equippedItem(0, plan[pi].slot);
                    for (size_t ii = 0; ii < poolItems.size(); ++ii)
                    {
                        if ((used[ii] >= 0 && used[ii] != int(pi)))
                        {
                            continue;
                        }
                        const ItemDefinition *pDef = items.get(poolItems[ii].objectDescriptionId);
                        if (pDef == nullptr || !plan[pi].fits(*pDef))
                        {
                            continue;
                        }
                        std::optional<InventoryItem> displaced;
                        if (!party.tryEquipItemOnMember(0, plan[pi].slot, poolItems[ii], std::nullopt, false, displaced))
                        {
                            continue;
                        }
                        const double value = meritOf();
                        if (value > bestMerit)
                        {
                            bestMerit = value;
                            bestIndex = int(ii);
                        }
                    }
                    if (bestIndex >= 0)
                    {
                        if (chosen.count(int(pi)))
                        {
                            used[chosen[int(pi)]] = -1;
                        }
                        chosen[int(pi)] = bestIndex;
                        used[bestIndex] = int(pi);
                        std::optional<InventoryItem> displaced;
                        party.tryEquipItemOnMember(0, plan[pi].slot, poolItems[bestIndex], std::nullopt, false, displaced);
                    }
                    else if (current)
                    {
                        std::optional<InventoryItem> displaced;
                        party.tryEquipItemOnMember(0, plan[pi].slot, *current, std::nullopt, false, displaced);
                    }
                }
            }
            worn = int(chosen.size());

            // A weapon, shield, bow or body armour the loot did not hold is bought: a common item of the content level
            // (`shop_level`, the monster level by default), as every town's shops sell and every new character starts
            // with. Until 2026-11-15 such a slot stayed empty, so the level-10 stage fought bare-handed and unarmoured.
            {
                shopFallback = true;
                gearLevel = c["shop_level"].as<int>(monsterLevel);
                rarity = rarityFromName("common");
                const int before = worn;
                const auto buy = [&](EquipmentSlot slot, const std::vector<const ItemDefinition *> &candidates)
                {
                    if (!party.equippedItem(0, slot))
                    {
                        equip(slot, candidates, false);
                    }
                };
                if (!mainSkill.empty())
                {
                    std::vector<const ItemDefinition *> weapons = mainTwo
                        ? baseItems(items, itemData, {"Weapon2"}, mainSkill)
                        : baseItems(items, itemData, {"Weapon", "Weapon1or2"}, mainSkill);
                    if (weapons.empty())
                    {
                        weapons = baseItems(items, itemData, {"Weapon", "Weapon1or2", "Weapon2"}, mainSkill);
                    }
                    buy(EquipmentSlot::MainHand, weapons);
                }
                if (off == "Shield")
                {
                    buy(EquipmentSlot::OffHand, baseItems(items, itemData, {"Shield"}, ""));
                }
                else if (!off.empty())
                {
                    buy(EquipmentSlot::OffHand, offTwo ? baseItems(items, itemData, {"Weapon2"}, canonicalSkillName(off))
                                                       : baseItems(items, itemData, {"Weapon", "Weapon1or2"}, canonicalSkillName(off)));
                }
                if (bow)
                {
                    buy(EquipmentSlot::Bow, baseItems(items, itemData, {"Missile"}, "Bow"));
                }
                if (!armorSkill.empty())
                {
                    buy(EquipmentSlot::Armor, baseItems(items, itemData, {"Armor"}, armorSkill));
                }
                shopFallback = false;
                craftLog << "bought " << worn - before << " ";
            }

            // Crafting with what the playthrough found, as the Workbench crafts.
            std::map<uint32_t, int> materials;
            for (const auto &entry : c["materials"])
            {
                materials[entry.first.as<uint32_t>()] = entry.second.as<int>();
            }
            CraftingContext craftContext;
            craftContext.pItemTable = &items;
            craftContext.pStandardEnchantTable = pStdTable;
            craftContext.pSpecialEnchantTable = pSpecialTable;
            craftContext.ownerLevel = int(party.member(0)->level);
            std::vector<EquipmentSlot> order;
            for (const SlotPlan &sp : plan)
            {
                order.push_back(sp.slot);
            }
            const auto applyMaterial = [&](uint32_t materialId, const std::vector<EquipmentSlot> &targets, bool repeat)
            {
                int applied = 0;
                for (EquipmentSlot slot : targets)
                {
                    while (materials[materialId] > 0)
                    {
                        std::optional<InventoryItem> target = party.equippedItem(0, slot);
                        if (!target)
                        {
                            break;
                        }
                        const InventoryItem material =
                            ItemGenerator::makeInventoryItem(materialId, items, ItemGenerationMode::Generic);
                        const CraftResult result = rules.gameRules().crafting.craft(*target, material, craftContext);
                        if (!result.possible)
                        {
                            break;
                        }
                        std::optional<InventoryItem> displaced;
                        party.tryEquipItemOnMember(0, slot, result.target, std::nullopt, false, displaced);
                        --materials[materialId];
                        ++applied;
                        if (!repeat)
                        {
                            break;
                        }
                    }
                }
                return applied;
            };
            std::vector<EquipmentSlot> armsAndArmor;
            for (EquipmentSlot slot : order)
            {
                if (slot == EquipmentSlot::MainHand || slot == EquipmentSlot::OffHand || slot == EquipmentSlot::Bow
                    || slot == EquipmentSlot::Armor)
                {
                    armsAndArmor.push_back(slot);
                }
            }
            craftLog << "emerald " << applyMaterial(1065, armsAndArmor, true);
            if (c["craft"].as<std::string>("smart") == "found")
            {
                // The 2026-11-14 crafting: every material once in a fixed order, no previews.
                craftLog << " hourglass " << applyMaterial(1062, order, false);
                craftLog << " eye " << applyMaterial(1061, order, false);
            }
            else
            {
                // What a player does at the Workbench: the Hourglass's and the Eye's results are previewed (they come
                // from the item's own craft stream), a Pearl removes the enchantment the player picks, and any other
                // craft step moves the stream on. So per worn item: take the previewed result when it makes the build
                // stronger, otherwise spend a gem or a Crafting Cube on the item (useful anyway) and look again.
                const auto craftOn = [&](const InventoryItem &target, uint32_t materialId, size_t choice)
                {
                    CraftingContext context = craftContext;
                    context.choice = choice;
                    return rules.gameRules().crafting.craft(
                        target, ItemGenerator::makeInventoryItem(materialId, items, ItemGenerationMode::Generic), context);
                };
                const auto meritWith = [&](EquipmentSlot slot, const InventoryItem &candidate, const InventoryItem &current)
                {
                    std::optional<InventoryItem> displaced;
                    party.tryEquipItemOnMember(0, slot, candidate, std::nullopt, false, displaced);
                    const double value = meritOf();
                    party.tryEquipItemOnMember(0, slot, current, std::nullopt, false, displaced);
                    return value;
                };
                int hourglasses = 0, eyes = 0, pearls = 0, nudges = 0;
                struct Step { InventoryItem item; std::map<uint32_t, int> cost; double merit = 0; };
                for (int round = 0; round < 2; ++round)
                {
                    for (EquipmentSlot slot : order)
                    {
                        for (int attempt = 0; attempt < 8; ++attempt)
                        {
                            const std::optional<InventoryItem> current = party.equippedItem(0, slot);
                            if (!current)
                            {
                                break;
                            }
                            const double now = meritOf();
                            std::optional<Step> bestStep;
                            const auto consider = [&](const InventoryItem &item, const std::map<uint32_t, int> &cost)
                            {
                                for (const auto &[id, count] : cost)
                                {
                                    if (materials[id] < count)
                                    {
                                        return;
                                    }
                                }
                                const double value = meritWith(slot, item, *current);
                                if (value > now * 1.002 && (!bestStep || value > bestStep->merit))
                                {
                                    bestStep = Step{item, cost, value};
                                }
                            };
                            for (uint32_t finisher : {1062u, 1061u})
                            {
                                const CraftResult direct = craftOn(*current, finisher, 0);
                                if (direct.possible)
                                {
                                    consider(direct.target, {{finisher, 1}});
                                }
                                for (size_t choice = 0; choice < 3; ++choice)
                                {
                                    const CraftResult pearl = craftOn(*current, 1066, choice);
                                    if (!pearl.possible || choice >= std::max<size_t>(1, pearl.choices.size()))
                                    {
                                        break;
                                    }
                                    const CraftResult after = craftOn(pearl.target, finisher, 0);
                                    if (after.possible)
                                    {
                                        consider(after.target, {{1066, 1}, {finisher, 1}});
                                    }
                                }
                            }
                            if (bestStep)
                            {
                                std::optional<InventoryItem> displaced;
                                party.tryEquipItemOnMember(0, slot, bestStep->item, std::nullopt, false, displaced);
                                for (const auto &[id, count] : bestStep->cost)
                                {
                                    materials[id] -= count;
                                    hourglasses += id == 1062 ? count : 0;
                                    eyes += id == 1061 ? count : 0;
                                    pearls += id == 1066 ? count : 0;
                                }
                                continue;
                            }
                            if (materials[1062] + materials[1061] == 0)
                            {
                                break;
                            }
                            // Nothing worth taking: move the item's craft stream on with a gem or a cube.
                            bool moved = false;
                            for (uint32_t gem = 1060; gem >= 1041 && !moved; --gem)
                            {
                                moved = applyMaterial(gem, {slot}, false) > 0;
                            }
                            moved = moved || applyMaterial(1070, {slot}, false) > 0;
                            if (!moved)
                            {
                                break;
                            }
                            ++nudges;
                        }
                    }
                }
                craftLog << " hourglass " << hourglasses << " eye " << eyes << " pearl " << pearls << " nudges " << nudges;
            }
            int gems = 0;
            for (uint32_t gem = 1060; gem >= 1041; --gem)
            {
                gems += applyMaterial(gem, order, true);
            }
            craftLog << " gems " << gems;
            craftLog << " pandora " << applyMaterial(1063, armsAndArmor, true);
            craftLog << " cube " << applyMaterial(1070, armsAndArmor, true) + applyMaterial(1070, order, true);
            craftLog << " merit " << meritOf();
        }

        party.refreshDerivedState();
        Character &hero = *party.member(0);
        hero.health = Party::effectiveMaximumHealth(hero);
        hero.spellPoints = Party::effectiveMaximumSpellPoints(hero);
        if (c["quick_spell"])
        {
            const SpellEntry *pQuick = dataLoader.getSpellTable().findByName(c["quick_spell"].as<std::string>());
            if (pQuick != nullptr && hero.knowsSpell(uint32_t(pQuick->id)))
            {
                hero.quickSpellName = c["quick_spell"].as<std::string>();
            }
            else
            {
                warnings << "quick spell not known; ";
            }
        }

        if (c["elemental_stacks"])
        {
            rules.classRuntime(hero).elementalStacks = c["elemental_stacks"].as<int>();
            rules.classRuntime(hero).elementalIdleSeconds = 0;
        }
        const StandardItemEnchantTable *pStd = &dataLoader.getStandardItemEnchantTable();
        const SpecialItemEnchantTable *pSpecial = &dataLoader.getSpecialItemEnchantTable();
        const CharacterSheetSummary sheet = GameMechanics::buildCharacterSheetSummary(hero, &items, pStd, pSpecial);
        const MawPowerReport report = mawPowerReport(rules, hero, items, pStd, pSpecial, partyCount);
        MawBalanceModel &model = rules.model(partyCount);
        const int fullHealth = Party::effectiveMaximumHealth(hero);

        // Damage taken (% of a hit after armour/resistance/class cuts) against a monster of the level.
        const std::vector<CombatDamageType> types = {CombatDamageType::Physical, CombatDamageType::Fire,
            CombatDamageType::Air, CombatDamageType::Water, CombatDamageType::Earth, CombatDamageType::Mind,
            CombatDamageType::Body, CombatDamageType::Energy};
        const std::vector<double> taken =
            mawDamageTakenPercents(rules, hero, &items, pStd, pSpecial, types, monsterLevel);
        // Chance a monster of the level lands a hit (Speed dodge), and GM Dodging's extra dodge (not for dragons).
        const double hitChance = 1.0 / (1.0 + sheet.speed.actual / (100.0 + model.stat(monsterLevel)) * 0.5);
        const CharacterSkill *pDodging = hero.findSkill("Dodging");
        const double dodge = pDodging != nullptr && pDodging->mastery >= SkillMastery::Grandmaster && !mawIsDragon(hero)
            ? 1 - 1 / (1 + (pDodging->level + hero.skillBonus("Dodging") + 10) / 200.0)
            : 0;

        // Regeneration (in combat, multiplier 1): the private MawSkillRules::regenerationPerSecond, from its parts.
        const CharacterSkill *pRegen = hero.findSkill("Regeneration");
        const double regenSkill = (pRegen != nullptr ? pRegen->level : 0) + hero.skillBonus("Regeneration");
        const SkillMastery regenMastery = pRegen != nullptr ? pRegen->mastery : SkillMastery::None;
        const double regenFull = mawRegenerationHealthPerSecond(
            regenMastery, model.health(std::pow(regenSkill, 1.4)), fullHealth, fullHealth);
        const double regenHalf = mawRegenerationHealthPerSecond(
            regenMastery, model.health(std::pow(regenSkill, 1.4)), fullHealth, fullHealth / 2.0);
        const int potionRegenSkill = hero.rulesetState.potionEffect(TimedPotionEffect::Kind::Regeneration, 0);
        const double regenPotion = mawRegenerationPotionHealthPerSecond(fullHealth, potionRegenSkill);

        const MawLeech leech = mawLeech(rules, hero, &items);
        const MawAttackDelay meleeDelay = mawCharacterAttackDelay(rules, hero, items, CharacterAttackMode::Melee,
            sheet.speed.actual, rules.auraSkill(5, &hero));
        const MawAttackDelay bowDelay = mawCharacterAttackDelay(rules, hero, items, CharacterAttackMode::Bow,
            sheet.speed.actual, rules.auraSkill(5, &hero));

        // Empirical melee / bow / breath through MAW's attack resolver, against a B-tier target of the level.
        ActorRulesetFacts target;
        target.level = monsterLevel;
        target.familyLevel = monsterLevel;
        target.tier = 2;
        target.maxHp = std::max(1, int(model.monsterHealth(monsterLevel)));
        const CharacterAttackProfile profile =
            GameMechanics::buildCharacterAttackProfile(hero, &items, &dataLoader.getSpellTable());
        const auto empirical = [&](CharacterAttackMode mode, int minimum, int maximum, double &recovery)
        {
            std::mt19937 attackRng(12345);
            double total = 0;
            recovery = 0;
            const int count = 4000;
            for (int i = 0; i < count; ++i)
            {
                CharacterAttackResult attack;
                attack.mode = mode;
                attack.canAttack = true;
                attack.hit = true;
                attack.attackBonus = mode == CharacterAttackMode::Melee ? profile.meleeAttackBonus
                                                                         : profile.rangedAttackBonus.value_or(0);
                CharacterAttackOnMonster context;
                context.pCharacter = &hero;
                context.pItemTable = &items;
                context.pStandardItemEnchantTable = pStd;
                context.pSpecialItemEnchantTable = pSpecial;
                context.minimumDamage = minimum;
                context.maximumDamage = maximum;
                context.pTargetFacts = &target;
                context.targetCurrentHp = target.maxHp;
                context.monstersNearTarget = 1;
                context.partyCount = partyCount;
                context.pRng = &attackRng;
                rules.gameRules().combat.resolveCharacterAttack(attack, context);
                if (attack.hit)
                {
                    total += attack.damage + attack.rulesElementalDamage.total();
                }
                recovery += attack.recoverySeconds;
            }
            recovery /= count;
            return total / count;
        };
        double meleeRecovery = 0;
        const double meleePerAttack =
            empirical(CharacterAttackMode::Melee, profile.meleeMinDamage, profile.meleeMaxDamage, meleeRecovery);
        double breathRecovery = 0;
        double breathPerAttack = 0;
        if (mawIsDragon(hero) && profile.hasDragonBreath)
        {
            breathPerAttack = empirical(
                CharacterAttackMode::DragonBreath, profile.rangedMinDamage, profile.rangedMaxDamage, breathRecovery);
        }

        // The quick spell's cost and recovery as the rules charge them; Meditation's SP a second (no auras held).
        int spellCost = 0;
        double spellRecovery = 0;
        if (!hero.quickSpellName.empty())
        {
            if (const SpellEntry *pSpell = dataLoader.getSpellTable().findByName(hero.quickSpellName))
            {
                const std::optional<std::string> school = resolveMagicSkillName(uint32_t(pSpell->id));
                const CharacterSkill *pSchool = school ? hero.findSkill(*school) : nullptr;
                CharacterSpellCast cast;
                cast.pCaster = &hero;
                cast.pItemTable = &items;
                cast.pStandardItemEnchantTable = pStd;
                cast.pSpecialItemEnchantTable = pSpecial;
                cast.pSpell = pSpell;
                cast.mastery = pSchool != nullptr ? pSchool->mastery : SkillMastery::Normal;
                cast.skillLevel = pSchool != nullptr ? pSchool->level : 0;
                cast.partyCount = partyCount;
                const SpellMasteryNumbers numbers = spellNumbersAtMastery(*pSpell, cast.mastery);
                spellCost = rules.gameRules().spells.manaCost(cast, numbers.manaCost);
                spellRecovery = rules.gameRules().spells.recoveryTicks(cast, numbers.recoveryTicks) / 60.0;
            }
        }
        // The healing spells the character knows (the party reference's healer): [amount, SP, recovery in seconds].
        std::ostringstream heals;
        for (const char *pHealName : {"Heal", "Power Cure"})
        {
            const SpellEntry *pSpell = dataLoader.getSpellTable().findByName(pHealName);
            double amount = 0, cost = 0, recovery = 0;
            if (pSpell != nullptr && hero.knowsSpell(uint32_t(pSpell->id)))
            {
                const std::optional<std::string> school = resolveMagicSkillName(uint32_t(pSpell->id));
                const CharacterSkill *pSchool = school ? hero.findSkill(*school) : nullptr;
                CharacterSpellCast cast;
                cast.pCaster = &hero;
                cast.pItemTable = &items;
                cast.pStandardItemEnchantTable = pStd;
                cast.pSpecialItemEnchantTable = pSpecial;
                cast.pSpell = pSpell;
                cast.mastery = pSchool != nullptr ? pSchool->mastery : SkillMastery::Normal;
                cast.skillLevel = pSchool != nullptr ? pSchool->level + hero.skillBonus(*school) : 0;
                cast.partyCount = partyCount;
                const SpellMasteryNumbers numbers = spellNumbersAtMastery(*pSpell, cast.mastery);
                amount = rules.gameRules().spells.healAmount(cast).value_or(0);
                cost = rules.gameRules().spells.manaCost(cast, numbers.manaCost);
                recovery = rules.gameRules().spells.recoveryTicks(cast, numbers.recoveryTicks) / 60.0;
            }
            heals << (heals.tellp() > 0 ? "," : "") << "[" << amount << "," << cost << "," << recovery << "]";
        }
        // What the character wears: [slot, item id, enchant 1 id, power, enchant 2 id, power, special, item power,
        // rarity, drop level, legendary affix, quality percent, ancient tier].
        std::ostringstream wornGear;
        for (int slotIndex = 0; slotIndex <= int(EquipmentSlot::Ring6); ++slotIndex)
        {
            const std::optional<InventoryItem> item = party.equippedItem(0, EquipmentSlot(slotIndex));
            if (!item)
            {
                continue;
            }
            const ItemRulesetFields &f = item->rulesetFields;
            wornGear << (wornGear.tellp() > 0 ? "," : "") << "[" << slotIndex << "," << item->objectDescriptionId << ","
                     << item->standardEnchantId << "," << item->standardEnchantPower << "," << f.secondStandardEnchantId
                     << "," << f.secondStandardEnchantPower << "," << item->specialEnchantId << "," << f.itemPower << ","
                     << int(f.lootRarity) << "," << f.dropLevel << "," << f.legendaryAffixId << ","
                     << int(f.qualityPercent) << "," << int(f.ancientTier) << "]";
        }
        const CharacterSkill *pMeditation = hero.findSkill("Meditation");
        const double meditationSkill = (pMeditation != nullptr ? pMeditation->level : 0) + hero.skillBonus("Meditation");
        const double spPerSecond = mawMeditationSpellPerSecond(pMeditation != nullptr ? pMeditation->mastery
                                                                                       : SkillMastery::None,
            model.mana(std::pow(meditationSkill, 1.4) / 2), Party::effectiveMaximumSpellPoints(hero));

        std::ostringstream line;
        line.precision(6);
        line << "{\"id\":\"" << c["id"].as<std::string>() << "\",\"class\":\"" << hero.className << "\",\"race\":"
             << hero.raceId << ",\"level\":" << hero.level << ",\"monster_level\":" << monsterLevel
             << ",\"options\":\"" << c["options"].as<std::string>("maw:free") << "\",\"worn\":" << worn
             << ",\"hp\":" << fullHealth << ",\"sp\":" << Party::effectiveMaximumSpellPoints(hero)
             << ",\"might\":" << sheet.might.actual << ",\"speed\":" << sheet.speed.actual
             << ",\"luck\":" << sheet.luck.actual << ",\"accuracy\":" << sheet.accuracy.actual
             << ",\"endurance\":" << sheet.endurance.actual << ",\"intellect\":" << sheet.intellect.actual
             << ",\"personality\":" << sheet.personality.actual
             << ",\"melee_dps\":" << report.melee << ",\"ranged_dps\":" << report.ranged
             << ",\"spell_dps\":" << report.spell << ",\"vitality\":" << report.vitality
             << ",\"melee_delay_s\":" << meleeDelay.delay / 60.0 << ",\"melee_mult\":" << meleeDelay.damageMultiplier
             << ",\"bow_delay_s\":" << bowDelay.delay / 60.0
             << ",\"emp_melee_per_attack\":" << meleePerAttack << ",\"emp_melee_recovery\":" << meleeRecovery
             << ",\"breath_per_attack\":" << breathPerAttack << ",\"breath_recovery\":" << breathRecovery
             << ",\"prof_min\":" << profile.meleeMinDamage << ",\"prof_max\":" << profile.meleeMaxDamage
             << ",\"rows_min\":" << mawCombatRows(rules, hero, items, {sheet.might.actual, sheet.accuracy.actual, sheet.luck.actual}).meleeMinimumDamage
             << ",\"rows_max\":" << mawCombatRows(rules, hero, items, {sheet.might.actual, sheet.accuracy.actual, sheet.luck.actual}).meleeMaximumDamage
             << ",\"sheet_melee\":\"" << sheet.combat.meleeDamageText << "\""
             << ",\"prof_attack\":" << profile.meleeAttackBonus
             << ",\"breath_min\":" << profile.rangedMinDamage << ",\"breath_max\":" << profile.rangedMaxDamage
             << ",\"my_hit_melee\":" << mawPartyHitChance(profile.meleeAttackBonus, monsterLevel, rules.blessHitSkill(hero), model)
             << ",\"my_hit_ranged\":" << mawPartyHitChance(profile.rangedAttackBonus.value_or(0), monsterLevel, rules.blessHitSkill(hero), model)
             << ",\"hit_on_me\":" << hitChance << ",\"dodge\":" << dodge
             << ",\"regen_full\":" << regenFull << ",\"regen_half\":" << regenHalf << ",\"regen_potion\":" << regenPotion
             << ",\"regen_skill\":" << regenSkill
             << ",\"leech_melee\":" << leech.melee << ",\"leech_ranged\":" << leech.ranged
             << ",\"leech_spell\":" << leech.spell
             << ",\"spell_cost\":" << spellCost << ",\"spell_recovery_s\":" << spellRecovery
             << ",\"sp_per_s\":" << spPerSecond
             << ",\"assassination_bonus\":" << mawAssassinationBonus(rules, hero, items)
             << ",\"pot_heal_large\":" << 50 + 0.35 * rules.model(5).health(std::max(1, c["potion_power"].as<int>(1)))
             << ",\"pot_heal_small\":" << 20 + 0.25 * rules.model(5).health(std::max(1, c["potion_power"].as<int>(1)))
             << ",\"flat_cut\":" << mawClassDefense(rules, hero, partyCount).flatReduction
             << ",\"flat_maw_factor\":" << model.chanceToBeHit(std::max(1.0, rules.state().totalLevel()) + 1)
                    * model.legendaryDamageTaken(std::max(1.0, rules.state().totalLevel()) + 1)
             << ",\"craft\":\"" << craftLog.str() << "\""
             << ",\"seraph_heal\":" << mawSeraphBodyHeal(rules, hero, party)
             << ",\"shaman_heal\":" << mawShamanBodyHeal(hero)
             << ",\"mon_hp_b\":" << model.monsterHealth(monsterLevel)
             << ",\"mon_dmg_b\":" << model.monsterDamage(monsterLevel)
             << ",\"mon_dmg_b_phys\":" << model.monsterDamage(monsterLevel, MawDamageClass::Physical)
             << ",\"mon_dmg_b_magic\":" << model.monsterDamage(monsterLevel, MawDamageClass::Magic)
             << ",\"model_stat\":" << model.stat(monsterLevel)
             << ",\"exp_health\":" << model.health(monsterLevel)
             << ",\"exp_power\":" << model.power(monsterLevel)
             // MAW's expected character of this character's own level, and the monster it is sized against.
             << ",\"own_exp_health\":" << model.health(hero.level) << ",\"own_exp_power\":" << model.power(hero.level)
             << ",\"own_exp_vitality\":" << model.vitality(hero.level, MawDamageClass::Blended)
             << ",\"own_mon_hp_b\":" << model.monsterHealth(hero.level)
             << ",\"own_mon_dmg_b\":" << model.monsterDamage(hero.level)
             << ",\"party_count\":" << partyCount
             << ",\"heals\":[" << heals.str() << "]"
             << ",\"gear\":[" << wornGear.str() << "]";
        for (size_t i = 0; i < types.size(); ++i)
        {
            line << ",\"taken_" << typeName(types[i]) << "\":" << taken[i];
        }
        // Damage taken (% of a hit) per type and the Speed dodge, against attackers of each level in the grid.
        if (c["level_grid"])
        {
            const std::vector<CombatDamageType> gridTypes = {CombatDamageType::Physical, CombatDamageType::Fire,
                CombatDamageType::Air, CombatDamageType::Water, CombatDamageType::Earth, CombatDamageType::Spirit,
                CombatDamageType::Mind, CombatDamageType::Body, CombatDamageType::Light, CombatDamageType::Dark,
                CombatDamageType::Energy};
            line << ",\"grid\":{";
            bool firstLevel = true;
            for (const YAML::Node &levelNode : c["level_grid"])
            {
                const int attackerLevel = std::max(1, levelNode.as<int>());
                const std::vector<double> percents =
                    mawDamageTakenPercents(rules, hero, &items, pStd, pSpecial, gridTypes, attackerLevel);
                const double hit = 1.0 / (1.0 + sheet.speed.actual / (100.0 + model.stat(attackerLevel)) * 0.5);
                line << (firstLevel ? "" : ",") << "\"" << attackerLevel << "\":[" << hit;
                for (double percent : percents)
                {
                    line << "," << percent;
                }
                line << "]";
                firstLevel = false;
            }
            line << "}";
        }
        std::string warningText = warnings.str();
        std::replace(warningText.begin(), warningText.end(), '"', '\'');
        line << ",\"warnings\":\"" << warningText << "\"}";
        out << line.str() << "\n";
        bindGameRules(nullptr);
    }
}

TEST_CASE("solo caps")
{
    const char *pSpec = std::getenv("SOLO_SPEC");
    REQUIRE(pSpec != nullptr);
    const YAML::Node spec = YAML::LoadFile(pSpec);
    Engine::AssetFileSystem assetFileSystem;
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    REQUIRE(assetFileSystem.initialize(sourceRoot, sourceRoot / "assets_dev", Engine::AssetScaleTier::X1, "mm8"));
    std::vector<RulesetDefinition> rulesets;
    std::string error;
    REQUIRE(loadAvailableRulesets(assetFileSystem, rulesets, error));
    const auto maw = std::find_if(rulesets.begin(), rulesets.end(), [](const RulesetDefinition &r) { return r.id == "maw"; });
    GameDataLoader dataLoader = {};
    dataLoader.setActiveRuleset(*maw);
    REQUIRE(dataLoader.loadCommonForGameplay(assetFileSystem));
    const char *Letters = "-NEMG";
    for (const YAML::Node &c : spec["caps"])
    {
        const std::string cls = c[0].as<std::string>();
        const uint32_t race = c[1].as<uint32_t>();
        std::cout << "CAPS " << cls << " race " << race << ":";
        for (const std::string &skill : allCanonicalSkillNames())
        {
            const int cap = int(dataLoader.getClassSkillTable().getEffectiveCap(cls, race, skill));
            if (cap > 0)
            {
                std::cout << " " << skill << "=" << Letters[std::min(cap, 4)];
            }
        }
        std::cout << "\n";
        const ClassMultiplierEntry *pEntry = dataLoader.getClassMultiplierTable().get(cls);
        if (pEntry != nullptr)
        {
            std::cout << "HPSP " << cls << " hpBase " << pEntry->baseHealth << " hpPerLevel " << int(pEntry->healthPerLevel)
                      << " spBase " << pEntry->baseMana << " spPerLevel " << int(pEntry->manaPerLevel) << "\n";
        }
    }
}
