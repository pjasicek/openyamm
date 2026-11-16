// Scratch harness: a solo MAW playthrough over the real MM6-MM8 maps. Monsters, levels, experience, corpse loot, chests,
// map completion and quests go through OpenYAMM's own MAW code. Input ROUTE_SPEC (JSON), output ROUTE_OUT (JSON lines).
#include <doctest/doctest.h>

#include "engine/AssetFileSystem.h"
#include "game/content/RulesetDefinition.h"
#include "game/content/RulesetOptions.h"
#include "game/data/GameDataLoader.h"
#include "game/data/GameDataRepository.h"
#include "game/gameplay/ChestRuntime.h"
#include "game/gameplay/CorpseLootRuntime.h"
#include "game/items/ItemGenerator.h"
#include "game/party/Party.h"
#include "game/rules/GameRules.h"
#include "game/maps/MapDeltaData.h"
#include "game/rules/MonsterRules.h"
#include "game/rules/maw/MawBalanceModel.h"
#include "game/rules/maw/MawCraftingData.h"
#include "game/rules/maw/MawExperienceCurve.h"
#include "game/rules/maw/MawItemRules.h"
#include "game/rules/maw/MawMonsterLevels.h"
#include "game/rules/maw/MawRules.h"
#include "game/rules/maw/MawRulesFactory.h"

#include <yaml-cpp/yaml.h>

#include <algorithm>
#include <cmath>
#include <cstdlib>
#include <fstream>
#include <functional>
#include <map>
#include <set>
#include <sstream>

using namespace OpenYAMM;
using namespace OpenYAMM::Game;

namespace
{
bool gearStat(const std::string &stat)
{
    static const std::set<std::string> Stats = {"Weapon", "Weapon1or2", "Weapon2", "Missile", "Armor", "Shield", "Helm",
        "Belt", "Cloak", "Gauntlets", "Boots", "Ring", "Amulet"};
    return Stats.contains(stat);
}

std::vector<uint8_t> fromHex(const std::string &hex)
{
    std::vector<uint8_t> bytes;
    for (size_t i = 0; i + 1 < hex.size(); i += 2)
    {
        bytes.push_back(uint8_t(std::stoi(hex.substr(i, 2), nullptr, 16)));
    }
    return bytes;
}

std::string itemJson(const InventoryItem &item)
{
    const ItemRulesetFields &f = item.rulesetFields;
    std::ostringstream out;
    out << "[" << item.objectDescriptionId << "," << item.standardEnchantId << "," << item.standardEnchantPower << ","
        << f.secondStandardEnchantId << "," << f.secondStandardEnchantPower << "," << item.specialEnchantId << ","
        << f.itemPower << "," << int(f.lootRarity) << "," << f.dropLevel << "," << f.legendaryAffixId << ","
        << int(f.ancientTier) << "]";
    return out.str();
}
}

TEST_CASE("solo route")
{
    const char *pSpec = std::getenv("ROUTE_SPEC");
    const char *pOut = std::getenv("ROUTE_OUT");
    REQUIRE(pSpec != nullptr);
    REQUIRE(pOut != nullptr);
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
    GameDataRepository data;
    data.bind(dataLoader);
    const MonsterTable &monsterTable = dataLoader.getMonsterTable();
    const ItemTable &items = dataLoader.getItemTable();

    std::map<std::string, const MapStatsEntry *> mapEntries;
    for (const MapStatsEntry &entry : dataLoader.getMapStats().getEntries())
    {
        std::string name = entry.fileName;
        std::transform(name.begin(), name.end(), name.begin(), ::tolower);
        mapEntries[name] = &entry;
    }

    std::ofstream out(pOut);
    const std::vector<int> stages = spec["stages"].as<std::vector<int>>();
    const double globalQuestCount = spec["global_quests"][0].as<double>();
    const double globalQuestTotal = spec["global_quests"][1].as<double>();
    const size_t poolPerKind = spec["pool_per_kind"].as<size_t>(40);
    // A party run (the reference for the solo): `party_count` members share every award as MAW shares it, and the
    // snapshots are taken at given numbers of cleared maps (`stage_maps`: [label, maps cleared]) so that they stand
    // at the same places of the route as the solo's level stages.
    const int partyCount = std::max(1, spec["party_count"].as<int>(1));
    std::vector<std::pair<int, int>> stageMaps;
    for (const YAML::Node &entry : (spec["stage_maps"] ? spec["stage_maps"] : YAML::Node(YAML::NodeType::Sequence)))
    {
        stageMaps.emplace_back(entry[0].as<int>(), entry[1].as<int>());
    }

    for (const YAML::Node &seedNode : spec["seeds"])
    {
        const uint32_t seed = seedNode.as<uint32_t>();
        RulesetOptions options = maw->defaultOptions();
        REQUIRE(applyRulesetOptionIds(spec["options"].as<std::string>(), options));
        options.preferences.lootFilter = rulesetLootFilterWithPreset(RulesetLootFilterPreset::Off);
        std::unique_ptr<MawRules> pRules = createMawRules(data, options);
        MawRules &rules = *pRules;
        rules.setSpellTable(&dataLoader.getSpellTable());
        rules.setItemTable(&items);
        rules.setClassMultiplierTable(&dataLoader.getClassMultiplierTable());
        rules.setItemEnchantTables(&dataLoader.getStandardItemEnchantTable(), &dataLoader.getSpecialItemEnchantTable());
        rules.setMapTable(&dataLoader.getMapStats());

        Party party;
        party.setItemTable(&items);
        party.setCharacterDollTable(&dataLoader.getCharacterDollTable());
        party.setClassSkillTable(&dataLoader.getClassSkillTable());
        party.setClassMultiplierTable(&dataLoader.getClassMultiplierTable());
        party.setItemEnchantTables(&dataLoader.getStandardItemEnchantTable(), &dataLoader.getSpecialItemEnchantTable());
        party.setRules(&rules.gameRules());
        bindGameRules(&rules.gameRules());
        Character hero = {};
        hero.name = "Solo";
        hero.className = "Champion";
        hero.level = 1;
        Party::Snapshot snapshot = party.snapshot();
        snapshot.members.assign(size_t(partyCount), hero);
        party.restoreSnapshot(snapshot);
        MawGameState state = rules.state();
        state.continentLevels = {};
        rules.setState(state);

        MawBalanceModel &model = rules.model(partyCount);
        const auto baseDamages = [&](int monsterId, const std::map<int, const MawRules::MapMonsterRow *> &byId, bool boss)
        {
            const MawMonsterFamily family = mawMonsterFamily(&monsterTable, monsterId);
            const auto b = byId.find(family.row(2));
            const auto own = byId.find(monsterId);
            const double familyLevel = std::max(1, b != byId.end() ? b->second->level : own->second->level);
            static const double tierMul[4] = {1, 0.66, 1, 1.5};
            const double mul = tierMul[std::min<int>(family.tier, 3)] * (boss ? 1.3 : 1.0);
            std::ostringstream o;
            o << "," << model.monsterDamage(familyLevel, MawDamageClass::Physical) * mul << ","
              << model.monsterDamage(familyLevel, MawDamageClass::Magic) * mul;
            return o.str();
        };
        const MawModelConfig config = mawModelConfig(rules.options(), partyCount);
        const bool insanity = config.insanityMode;
        const bool madness = config.madnessMode;
        const bool doom = config.doomMode;
        const bool nightmare = rules.options().difficulty == RulesetDifficulty::Nightmare;

        // A new MAW game: 10000 experience shared by the party (PHASE9 P9.D1). `charExp` is one member's experience.
        double charExp = 10000.0 / partyCount;
        std::map<std::string, std::vector<std::string>> pool;     // kind -> item json, filtered at the end of stages
        std::map<uint32_t, int> materials;
        std::set<std::string> cleared;
        std::vector<YAML::Node> route;
        for (const YAML::Node &m : spec["maps"])
        {
            route.push_back(m);
        }
        size_t stageIndex = 0;
        double questCarry = 0;
        // The global (NPC) quest rewards, smallest first along the route.
        const std::vector<double> questValues = spec["global_quest_values"].as<std::vector<double>>();
        size_t nextQuest = 0;
        double xpKills = 0, xpCompletion = 0, xpQuests = 10000.0 / partyCount;
        int kills = 0, chestsOpened = 0, itemsSeen = 0, mapsCleared = 0, bossKills = 0;
        std::ostringstream trajectory;
        std::vector<std::string> clearedRecords;
        std::mt19937 rng(seed);

        // Candidate items kept per kind (equip stat + skill). A player keeps an item for what is on it, so the kept
        // set is the union of several short lists: the highest rarity (legendary affixes), the highest drop level, and
        // for every enchantment type the strongest first and second enchantment of that type. Rings count three times
        // (six slots). Before 2026-11-15 this was one list by rarity, then drop level, which threw away well-rolled
        // items of a lower rarity and kept low-level legendaries.
        std::map<std::string, std::vector<InventoryItem>> best;
        const auto selectKept = [&](const std::string &kind, std::vector<InventoryItem> &list)
        {
            const size_t scale = kind.rfind("Ring", 0) == 0 ? 3 : 1;
            const size_t perList = std::max<size_t>(1, poolPerKind * scale * 3 / 10);
            const size_t perType = 3 * scale;
            std::set<size_t> keepIndices;
            const auto take = [&](const std::function<double(const InventoryItem &)> &score,
                                  const std::function<bool(const InventoryItem &)> &filter, size_t count)
            {
                std::vector<size_t> order;
                for (size_t i = 0; i < list.size(); ++i)
                {
                    if (filter(list[i]))
                    {
                        order.push_back(i);
                    }
                }
                std::stable_sort(order.begin(), order.end(),
                    [&](size_t a, size_t b) { return score(list[a]) > score(list[b]); });
                for (size_t i = 0; i < std::min(count, order.size()); ++i)
                {
                    keepIndices.insert(order[i]);
                }
            };
            const auto all = [](const InventoryItem &) { return true; };
            const auto enchantSum = [](const InventoryItem &item)
            { return double(item.standardEnchantPower) + item.rulesetFields.secondStandardEnchantPower; };
            take([&](const InventoryItem &item)
                { return item.rulesetFields.lootRarity * 1.0e6 + item.rulesetFields.dropLevel * 1.0e3 + enchantSum(item); },
                all, perList);
            take([&](const InventoryItem &item)
                { return item.rulesetFields.dropLevel * 1.0e6 + item.rulesetFields.lootRarity * 1.0e4 + enchantSum(item); },
                all, perList);
            take([&](const InventoryItem &item)
                { return item.rulesetFields.itemPower * 1.0e6 + enchantSum(item); }, all, perList);
            std::set<int> firstTypes, secondTypes;
            for (const InventoryItem &item : list)
            {
                firstTypes.insert(item.standardEnchantId);
                secondTypes.insert(item.rulesetFields.secondStandardEnchantId);
            }
            for (int type : firstTypes)
            {
                if (type == 0) continue;
                take([&](const InventoryItem &item)
                    { return item.standardEnchantPower * 1.0e3 + item.rulesetFields.secondStandardEnchantPower; },
                    [type](const InventoryItem &item) { return item.standardEnchantId == type; }, perType);
            }
            for (int type : secondTypes)
            {
                if (type == 0) continue;
                take([&](const InventoryItem &item)
                    { return item.rulesetFields.secondStandardEnchantPower * 1.0e3 + item.standardEnchantPower; },
                    [type](const InventoryItem &item) { return item.rulesetFields.secondStandardEnchantId == type; },
                    perType - scale);
            }
            std::vector<InventoryItem> kept;
            for (size_t index : keepIndices)
            {
                kept.push_back(list[index]);
            }
            list = std::move(kept);
        };
        const auto keep = [&](const InventoryItem &item)
        {
            const ItemDefinition *pDef = items.get(item.objectDescriptionId);
            if (pDef == nullptr)
            {
                return;
            }
            if (rules.gameRules().crafting.isMaterial(item))
            {
                ++materials[item.objectDescriptionId];
                return;
            }
            if (!gearStat(pDef->equipStat))
            {
                return;
            }
            ++itemsSeen;
            const std::string kind = pDef->equipStat + "|" + pDef->skillGroup;
            std::vector<InventoryItem> &list = best[kind];
            list.push_back(item);
            if (list.size() > 600)
            {
                selectKept(kind, list);
            }
        };

        const auto snapshotOut = [&](int stage, const std::string &mapFile, double mapLevel)
        {
            std::ostringstream line;
            line << "{\"kind\":\"snapshot\",\"options\":\"" << spec["options"].as<std::string>() << "\",\"seed\":" << seed
                 << ",\"stage\":" << stage << ",\"party_count\":" << partyCount
                 << ",\"char_level\":" << mawLevelForExperience(charExp)
                 << ",\"bank_total\":" << rules.state().totalLevel() << ",\"map\":\"" << mapFile
                 << "\",\"map_level\":" << mapLevel << ",\"maps_cleared\":" << mapsCleared << ",\"kills\":" << kills
                 << ",\"boss_kills\":" << bossKills << ",\"chests\":" << chestsOpened << ",\"items_seen\":" << itemsSeen
                 << ",\"xp_kills\":" << xpKills << ",\"xp_completion\":" << xpCompletion << ",\"xp_quests\":" << xpQuests
                 << ",\"materials\":{";
            bool first = true;
            for (const auto &[id, count] : materials)
            {
                line << (first ? "" : ",") << "\"" << id << "\":" << count;
                first = false;
            }
            line << "},\"fights\":[";
            const size_t firstRecord = clearedRecords.size() > 5 ? clearedRecords.size() - 5 : 0;
            for (size_t i = firstRecord; i < clearedRecords.size(); ++i)
            {
                line << (i > firstRecord ? "," : "") << clearedRecords[i];
            }
            // The next five maps the route would clear, at the banks now.
            {
                const std::vector<MawRules::MapMonsterRow> nowRows = rules.mapMonsterTable(monsterTable, &party);
                std::map<std::string, std::map<int, const MawRules::MapMonsterRow *>> nowById;
                std::map<std::string, std::vector<int>> nowB;
                for (const MawRules::MapMonsterRow &row : nowRows)
                {
                    nowById[row.fileName][row.monsterId] = &row;
                    if (row.tier == 2) nowB[row.fileName].push_back(row.level);
                }
                std::vector<std::pair<double, const YAML::Node *>> upcoming;
                for (const YAML::Node &m : route)
                {
                    const std::string f = m["file"].as<std::string>();
                    if (cleared.contains(f) || nowB[f].empty()) continue;
                    std::vector<int> lv = nowB[f];
                    std::sort(lv.begin(), lv.end());
                    upcoming.emplace_back(lv[lv.size() / 2], &m);
                }
                std::sort(upcoming.begin(), upcoming.end(), [](const auto &a, const auto &b) { return a.first < b.first; });
                for (size_t u = 0; u < std::min<size_t>(5, upcoming.size()); ++u)
                {
                    const YAML::Node &m = *upcoming[u].second;
                    const std::string f = m["file"].as<std::string>();
                    line << (clearedRecords.empty() && u == 0 ? "" : ",") << "{\"file\":\"" << f << "\",\"next\":1,\"level\":"
                         << upcoming[u].first << ",\"actors\":[";
                    bool firstActor = true;
                    for (const YAML::Node &actor : m["actors"])
                    {
                        const auto it = nowById[f].find(actor[0].as<int>());
                        if (it == nowById[f].end()) continue;
                        const bool boss = actor[1].as<double>() > 2.0;
                        line << (firstActor ? "" : ",") << "[" << actor[0].as<int>() << "," << it->second->level << ","
                             << int(it->second->maxHp * (boss ? actor[1].as<double>() : 1.0)) << "," << it->second->attackDamage
                             << "," << (actor.size() > 2 ? actor[2].as<int>() : 0) << "," << (boss ? 1 : 0)
                             << baseDamages(actor[0].as<int>(), nowById[f], boss) << "]";
                        firstActor = false;
                    }
                    line << "]}";
                }
            }
            line << "],\"pool\":{";
            first = true;
            for (auto &[kind, list] : best)
            {
                selectKept(kind, list);
                line << (first ? "" : ",") << "\"" << kind << "\":[";
                for (size_t i = 0; i < list.size(); ++i)
                {
                    line << (i ? "," : "") << itemJson(list[i]);
                }
                line << "]";
                first = false;
            }
            line << "}}";
            out << line.str() << "\n";
            out.flush();
        };

        // The start, before the first map: stage 1 of a level-staged run, or a party run's stage at 0 maps cleared.
        while (stageIndex < stages.size() && stageMaps.empty() && stages[stageIndex] <= 1)
        {
            snapshotOut(stages[stageIndex], "start", 0);
            ++stageIndex;
        }
        size_t stageMapIndex = 0;
        while (stageMapIndex < stageMaps.size() && stageMaps[stageMapIndex].second <= 0)
        {
            snapshotOut(stageMaps[stageMapIndex].first, "start", 0);
            ++stageMapIndex;
        }

        while (cleared.size() < route.size())
        {
            // The easiest uncleared map now: the lowest middle level of its B-tier natives at the current banks.
            const std::vector<MawRules::MapMonsterRow> rows = rules.mapMonsterTable(monsterTable, &party);
            std::map<std::string, std::vector<int>> bLevels;
            std::map<std::string, std::map<int, const MawRules::MapMonsterRow *>> byId;
            for (const MawRules::MapMonsterRow &row : rows)
            {
                byId[row.fileName][row.monsterId] = &row;
                if (row.tier == 2)
                {
                    bLevels[row.fileName].push_back(row.level);
                }
            }
            const YAML::Node *pNext = nullptr;
            double nextLevel = 1e9;
            for (const YAML::Node &m : route)
            {
                const std::string file = m["file"].as<std::string>();
                if (cleared.contains(file))
                {
                    continue;
                }
                std::vector<int> levels = bLevels[file];
                double level = 1e8;
                if (!levels.empty())
                {
                    std::sort(levels.begin(), levels.end());
                    level = levels[levels.size() / 2];
                }
                if (level < nextLevel)
                {
                    nextLevel = level;
                    pNext = &m;
                }
            }
            REQUIRE(pNext != nullptr);
            const YAML::Node &m = *pNext;
            const std::string file = m["file"].as<std::string>();
            const std::string world = m["world"].as<std::string>();
            cleared.insert(file);
            const MapStatsEntry *pMap = mapEntries.count(file) ? mapEntries[file] : nullptr;
            if (pMap == nullptr)
            {
                continue;
            }
            const uint32_t continent = pMap->mergedContinentId;
            rules.setCurrentMap(file);
            rules.mapBolster(monsterTable, *pMap);
            const auto &mapRows = byId[file];
            int slain = 0;
            double levelSum = 0;
            std::ostringstream record;
            record << "{\"file\":\"" << file << "\",\"level\":" << nextLevel << ",\"actors\":[";
            bool firstActor = true;

            // Every spawned monster: experience to the solo (the whole award) and a fifth to the bank, then its loot.
            int actorIndex = 0;
            for (const YAML::Node &actor : m["actors"])
            {
                const int monsterId = actor[0].as<int>();
                const double bossRatio = actor[1].as<double>();
                const auto rowIt = mapRows.find(monsterId);
                const MonsterTable::MonsterStatsEntry *pStats = monsterTable.findStatsById(int16_t(monsterId));
                ++actorIndex;
                if (rowIt == mapRows.end() || pStats == nullptr)
                {
                    continue;
                }
                const MawRules::MapMonsterRow &row = *rowIt->second;
                const bool boss = bossRatio > 2.0;
                const double level = row.level;
                const double hp = row.maxHp * (boss ? bossRatio : 1.0);
                record << (firstActor ? "" : ",") << "[" << monsterId << "," << row.level << "," << int(hp) << ","
                       << row.attackDamage << "," << (actor.size() > 2 ? actor[2].as<int>() : 0) << "," << (boss ? 1 : 0)
                       << baseDamages(monsterId, mapRows, boss) << "]";
                firstActor = false;
                const double expLevel = std::min(std::max(double(pStats->level), level / 3), 100.0);
                double experience = expLevel > 0 ? std::floor((expLevel * 20 + std::pow(expLevel, 1.8)) * level / expLevel + 0.5) : 0;
                if (continent == 2)
                {
                    experience = std::min(experience * 2, experience + 1000);
                }
                experience = std::floor(experience * model.monsterExperienceMultiplier() + 0.5);
                // MawExperienceRules::grantKillExperience: the monster's experience is split among the members, each
                // member's share is scaled and capped for that member, and the bank gets a fifth of the sum.
                const double charLevel = mawLevelForExperience(charExp);
                const double memberLevel = std::max(1.0, std::min(charLevel, rules.state().totalLevel()));
                const double award = std::min(std::floor(experience / partyCount + 0.5) * hp / model.monsterHealth(memberLevel),
                    (std::floor(charLevel) + 1) * 1000.0);
                charExp += award;
                xpKills += award;
                rules.state().addBankedExperience(award * partyCount / 5, continent);
                ++kills;
                bossKills += boss ? 1 : 0;
                ++slain;
                levelSum += level;

                ActorRulesetFacts facts;
                facts.level = int(level);
                facts.tier = row.tier;
                facts.bossAffix = boss ? 1 : 0;
                facts.maxHp = int(std::min(hp, 2.0e9));
                facts.experience = uint32_t(experience);
                for (const auto &[otherId, pOther] : mapRows)
                {
                    if (pOther->family == row.family && pOther->tier == 2)
                    {
                        facts.familyLevel = pOther->level;
                    }
                }
                CorpseLootContext context;
                context.pStats = pStats;
                context.pMonsterTable = &monsterTable;
                context.pFacts = &facts;
                context.pMap = pMap;
                context.visitSeed = seed * 7919u + uint32_t(mapsCleared);
                context.actorIndex = uint32_t(actorIndex);
                context.pParty = &party;
                const CorpseLoot loot = rules.gameRules().monsters.corpseLoot(context);
                const GameplayCorpseViewState view = rollMonsterCarriedLoot("", loot, &items, &party, world);
                for (const GameplayChestItemState &entry : view.items)
                {
                    if (!entry.isGold && entry.itemId != 0)
                    {
                        keep(entry.item);
                    }
                }
                for (const CorpseLoot::ExtraItem &extra : loot.extraItems)
                {
                    keep(corpseExtraInventoryItem(extra, items));
                }
            }

            record << "]}";
            if (!firstActor)
            {
                clearedRecords.push_back(record.str());
            }

            // Every chest on the map, as the game materialises it.
            uint32_t chestIndex = 0;
            for (const YAML::Node &chestNode : m["chests"])
            {
                MapDeltaChest chest;
                chest.chestTypeId = uint16_t(chestNode["type"].as<int>());
                chest.flags = uint16_t(chestNode["flags"].as<int>());
                chest.rawItems = fromHex(chestNode["hex"].as<std::string>());
                chest.inventoryMatrix.assign(size_t(chestNode["matrix"].as<int>()), 0);
                const GameplayChestViewState view = buildMaterializedChestView(chestIndex++, chest, pMap->treasureLevel,
                    pMap->id, seed * 104729u + uint32_t(mapsCleared), &dataLoader.getChestTable(), &items, &party, world);
                ++chestsOpened;
                for (const GameplayChestItemState &entry : view.items)
                {
                    if (!entry.isGold && entry.itemId != 0)
                    {
                        keep(entry.item);
                    }
                }
            }

            // Map completion (MawExperienceRules::rewardMapProgress): the bank gets it all, the solo five times.
            if (slain > 0)
            {
                double slainCounted = slain * (doom ? 0.5 : nightmare ? 0.67 : 1) * (insanity ? 0.8 : 1);
                const std::optional<double> clearLevel = rules.mapMonsterLevel();
                const double clear = clearLevel ? *clearLevel : levelSum / slain;
                double experience =
                    std::ceil(std::pow(slainCounted, 0.7) * (clear * 20 + std::pow(clear, 1.8)) / 3 / 1000) * 1000;
                double gemLevel = clear;
                if (madness)
                {
                    const double bolster = rules.mapLevels().madnessLevel(file);
                    if (bolster > 0)
                    {
                        experience = std::ceil(std::pow(slainCounted, 0.7) * (bolster * 20 + std::pow(bolster, 1.8)) / 3
                                         / 1000) * 1000 * 2;
                        gemLevel = clear;
                    }
                }
                rules.state().addBankedExperience(experience, continent);
                charExp += std::floor(experience * 5 / partyCount / 1000 + 0.5) * 1000;
                xpCompletion += std::floor(experience * 5 / partyCount / 1000 + 0.5) * 1000;
                const MawCraftingData &crafting = rules.craftingData();
                std::vector<uint32_t> rewards = crafting.mapCompletionItems();
                const int gemTier = std::min(int(std::ceil(gemLevel / 25 + 0.5)), crafting.gemDropMaxTier());
                for (int gem = 0; gem < crafting.mapCompletionGems(); ++gem)
                {
                    rewards.push_back(crafting.gemItemId(std::max(1, gemTier)));
                }
                for (uint32_t itemId : rewards)
                {
                    ++materials[itemId];
                }
            }

            // Quests: the map's own script rewards, and the global (NPC) quests spread evenly over the route.
            questCarry += globalQuestCount / double(route.size());
            std::vector<double> quests;
            for (int q = 0; q < m["quests"][0].as<int>(); ++q)
            {
                quests.push_back(m["quests"][1].as<double>() / std::max(1, m["quests"][0].as<int>()));
            }
            while (questCarry >= 1 && nextQuest < questValues.size())
            {
                quests.push_back(questValues[nextQuest++]);
                questCarry -= 1;
            }
            for (double value : quests)
            {
                const double partyLevel = madness ? rules.state().totalLevel() : rules.state().levelOutside(continent);
                const double total = value * (1 + partyLevel / 100) + 500 * partyLevel;
                rules.state().addBankedExperience(total, continent);
                charExp += total * 5 / partyCount;
                xpQuests += total * 5 / partyCount;
            }

            ++mapsCleared;
            const double charLevel = mawLevelForExperience(charExp);
            trajectory << (mapsCleared > 1 ? "," : "") << "[\"" << file << "\"," << nextLevel << "," << charLevel << ","
                       << rules.state().totalLevel() << "," << kills << "]";

            while (stageMaps.empty() && stageIndex < stages.size() && charLevel >= stages[stageIndex])
            {
                snapshotOut(stages[stageIndex], file, nextLevel);
                ++stageIndex;
            }
            while (stageMapIndex < stageMaps.size() && mapsCleared >= stageMaps[stageMapIndex].second)
            {
                snapshotOut(stageMaps[stageMapIndex].first, file, nextLevel);
                ++stageMapIndex;
            }
        }
        snapshotOut(0, "end", 0);
        out << "{\"kind\":\"trajectory\",\"options\":\"" << spec["options"].as<std::string>() << "\",\"seed\":" << seed
            << ",\"final_level\":" << mawLevelForExperience(charExp) << ",\"maps\":[" << trajectory.str() << "]}\n";
        out.flush();
        bindGameRules(nullptr);
    }
}

TEST_CASE("solo monsters")
{
    const char *pOut = std::getenv("MON_OUT");
    REQUIRE(pOut != nullptr);
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
    std::ofstream out(pOut);
    const auto avg = [](const MonsterTable::MonsterStatsEntry::DamageProfile &d)
    { return d.diceRolls * (d.diceSides + 1) / 2.0 + d.bonus; };
    const auto spellId = [&](const std::string &name) -> int
    {
        if (name.empty()) return 0;
        const SpellEntry *pSpell = dataLoader.getSpellTable().findByName(name);
        return pSpell != nullptr ? pSpell->id : -1;
    };
    out << "{";
    bool first = true;
    for (int id = 1; id < 1000; ++id)
    {
        const MonsterTable::MonsterStatsEntry *p = dataLoader.getMonsterTable().findStatsById(int16_t(id));
        if (p == nullptr) continue;
        out << (first ? "" : ",") << "\"" << id << "\":{\"name\":\"" << p->name << "\",\"level\":" << p->level
            << ",\"rec\":" << p->recovery << ",\"speed\":" << p->speed << ",\"fly\":" << (p->canFly ? 1 : 0)
            << ",\"a1\":\"" << p->attack1Type << "\",\"a1m\":" << (p->attack1HasMissile ? 1 : 0) << ",\"a1avg\":" << avg(p->attack1Damage)
            << ",\"a2\":\"" << p->attack2Type << "\",\"a2m\":" << (p->attack2HasMissile ? 1 : 0) << ",\"a2avg\":" << avg(p->attack2Damage)
            << ",\"a2c\":" << p->attack2Chance
            << ",\"s1\":" << (p->hasSpell1 ? spellId(p->spell1Name) : 0) << ",\"s1n\":\"" << p->spell1Name << "\",\"s1c\":" << p->spell1UseChance
            << ",\"s2\":" << (p->hasSpell2 ? spellId(p->spell2Name) : 0) << ",\"s2n\":\"" << p->spell2Name << "\",\"s2c\":" << p->spell2UseChance
            << ",\"res\":[" << p->fireResistance << "," << p->airResistance << "," << p->waterResistance << "," << p->earthResistance
            << "," << p->spiritResistance << "," << p->mindResistance << "," << p->bodyResistance << "," << p->lightResistance
            << "," << p->darkResistance << "," << p->physicalResistance << "]"
            << ",\"special\":" << int(p->specialAttackKind) << ",\"speclvl\":" << p->specialAttackLevel << "}";
        first = false;
    }
    out << "}\n";
}
