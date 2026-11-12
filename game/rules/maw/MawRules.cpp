#include "game/rules/maw/MawRules.h"

#include "game/rules/maw/MawAuras.h"
#include "game/rules/maw/MawSpellFormulas.h"

#include "game/events/EvtEnums.h"
#include "game/party/Party.h"
#include "game/rules/RandomStreams.h"
#include "game/tables/MapStats.h"

#include <algorithm>
#include <cctype>
#include <cmath>
#include <tuple>
#include <utility>
#include <vector>

namespace OpenYAMM::Game
{
namespace
{
std::string lowercase(std::string text)
{
    for (char &character : text)
    {
        character = char(std::tolower(static_cast<unsigned char>(character)));
    }

    return text;
}
}

MawRules::MawRules(
    const RulesetOptions &options,
    const MawMapLevels &mapLevels,
    MawItemData itemData,
    MawPromotionData promotionData,
    MawCraftingData craftingData,
    MawTextData textData,
    MawDimensionData dimensionData)
    : m_options(options)
    , m_mapLevels(mapLevels)
    , m_itemData(std::move(itemData))
    , m_promotionData(std::move(promotionData))
    , m_craftingData(std::move(craftingData))
    , m_textData(std::move(textData))
    , m_dimensionData(std::move(dimensionData))
    , m_experience(*this)
    , m_combat(*this)
    , m_monsters(*this)
    , m_items(*this)
    , m_skills(*this)
    , m_spells(*this)
    , m_classes(*this)
    , m_potions(*this)
    , m_crafting(*this)
    , m_gameRules{m_experience, m_combat, m_monsters, m_items, m_skills, m_spells, m_classes, m_potions, m_crafting}
{
}

double MawRules::diminishedCrowdControlSeconds(
    uint64_t targetKey,
    int group,
    double nowSeconds,
    double seconds,
    bool boss) const
{
    constexpr double WindowSeconds = 20.0;

    if (group < 2 || group > 3)
    {
        return seconds;
    }

    std::vector<std::pair<double, double>> &history = m_crowdControlHistory[targetKey][size_t(group - 2)];
    const double windowStart = nowSeconds - WindowSeconds;
    std::erase_if(
        history,
        [windowStart](const std::pair<double, double> &entry)
        {
            return entry.second <= windowStart;
        });
    double recent = 0;

    for (const auto &[start, end] : history)
    {
        recent += std::max(0.0, std::min(end, nowSeconds) - std::max(start, windowStart));
    }

    const double multiplier = mawDiminishingReturnsMultiplier(recent / WindowSeconds);

    if (multiplier <= 0)
    {
        return 0;
    }

    seconds *= multiplier * (boss ? 0.5 : 1);
    history.emplace_back(nowSeconds, nowSeconds + seconds);
    return seconds;
}

MawClassRuntime &MawRules::classRuntime(const Character &member) const
{
    return member.rulesetState.runtime;
}

int MawRules::promotionWorlds(uint32_t classKind) const
{
    const auto found = m_promotionWorlds.find(classKind);
    return found != m_promotionWorlds.end() ? found->second : 0;
}

const std::map<uint32_t, int> &MawRules::promotionWorldsByKind() const
{
    return m_promotionWorlds;
}

void MawRules::setPromotionWorlds(std::map<uint32_t, int> worlds)
{
    m_promotionWorlds = std::move(worlds);
}

const MawPromotionData &MawRules::promotionData() const
{
    return m_promotionData;
}

const GameRules &MawRules::gameRules() const
{
    return m_gameRules;
}

const MawItemRules &MawRules::itemRules() const
{
    return m_items;
}

const MawSpellRules &MawRules::spellRules() const
{
    return m_spells;
}

const MawClassRules &MawRules::classRules() const
{
    return m_classes;
}

const RulesetOptions &MawRules::options() const
{
    return m_options;
}

void MawRules::setOptions(const RulesetOptions &options)
{
    m_options = options;
    m_models.clear();
    m_monsterLevels = {};
}

MawGameState &MawRules::state()
{
    return m_state;
}

const MawGameState &MawRules::state() const
{
    return m_state;
}

void MawRules::setState(const MawGameState &state)
{
    m_state = state;
    m_monsterLevels = {};
}

void MawRules::updateStoryBands(const Party &party)
{
    std::unordered_set<uint32_t> reached;

    for (uint32_t qbit : m_mapLevels.storyBandQBits())
    {
        if (party.hasQuestBit(qbit))
        {
            reached.insert(qbit);
        }
    }

    if (m_mapLevels.setReachedStoryQBits(std::move(reached)))
    {
        m_monsterLevels = {};
    }
}

const MawMapLevels &MawRules::mapLevels() const
{
    return m_mapLevels;
}

const MawCraftingData &MawRules::craftingData() const
{
    return m_craftingData;
}

const MawTextData &MawRules::textData() const
{
    return m_textData;
}

const MawDimensionData &MawRules::dimensionData() const
{
    return m_dimensionData;
}

const MapStats *MawRules::mapTable() const
{
    return m_pMapTable;
}

void MawRules::setMapTable(const MapStats *pMapTable)
{
    m_pMapTable = pMapTable;
}

const SpellTable *MawRules::spellTable() const
{
    return m_pSpellTable;
}

void MawRules::setSpellTable(const SpellTable *pSpellTable)
{
    m_pSpellTable = pSpellTable;
}

const ItemTable *MawRules::itemTable() const
{
    return m_pItemTable;
}

void MawRules::setItemTable(const ItemTable *pItemTable)
{
    m_pItemTable = pItemTable;
}

const ClassMultiplierTable *MawRules::classMultiplierTable() const
{
    return m_pClassMultiplierTable;
}

void MawRules::setClassMultiplierTable(const ClassMultiplierTable *pClassMultiplierTable)
{
    m_pClassMultiplierTable = pClassMultiplierTable;
}

const StandardItemEnchantTable *MawRules::standardItemEnchantTable() const
{
    return m_pStandardItemEnchantTable;
}

const SpecialItemEnchantTable *MawRules::specialItemEnchantTable() const
{
    return m_pSpecialItemEnchantTable;
}

void MawRules::setItemEnchantTables(const StandardItemEnchantTable *pStandard, const SpecialItemEnchantTable *pSpecial)
{
    m_pStandardItemEnchantTable = pStandard;
    m_pSpecialItemEnchantTable = pSpecial;
}

const std::string &MawRules::currentMap() const
{
    return m_currentMap;
}

void MawRules::setCurrentMap(const std::string &mapFileName)
{
    m_currentMap = lowercase(mapFileName);

    if (outdoorMap(m_currentMap))
    {
        m_lastOutdoorMap = m_currentMap;
    }
}

const std::string &MawRules::lastOutdoorMap() const
{
    return m_lastOutdoorMap;
}

bool MawRules::outdoorMap(const std::string &mapFileName) const
{
    const std::string file = lowercase(mapFileName);

    if (file.ends_with(".odm"))
    {
        return true;
    }

    const MapStatsEntry *pMap = m_pMapTable != nullptr ? m_pMapTable->findByFileName(file) : nullptr;
    return pMap != nullptr && pMap->openAir;
}

const MawTrainerHints &MawRules::trainerHints() const
{
    return m_trainerHints;
}

void MawRules::setTrainerHints(MawTrainerHints hints)
{
    m_trainerHints = std::move(hints);
}

const MawDimensionRun *MawRules::dimensionRun(const std::string &mapFileName) const
{
    const auto it = m_state.dimensionRuns.find(lowercase(mapFileName));
    return it != m_state.dimensionRuns.end() ? &it->second : nullptr;
}

std::optional<double> MawRules::mapAffix(MawMapAffix affix) const
{
    return mapAffix(m_currentMap, affix);
}

double MawRules::buffScale() const
{
    const std::optional<double> cut = mapAffix(MawMapAffix::BuffEffects);
    return cut ? 1 - std::clamp(*cut, 0.0, 100.0) / 100 : 1;
}

std::optional<double> MawRules::mapAffix(const std::string &mapFileName, MawMapAffix affix) const
{
    const MawDimensionRun *pRun = dimensionRun(mapFileName);

    if (pRun == nullptr || std::find(pRun->affixes.begin(), pRun->affixes.end(), uint8_t(affix)) == pRun->affixes.end())
    {
        return std::nullopt;
    }

    return m_dimensionData.affixValue(int(affix), pRun->power);
}

std::vector<uint16_t> MawRules::dimensionMapPool() const
{
    std::vector<uint16_t> pool;

    for (uint16_t mapId : m_dimensionData.dungeons())
    {
        const MapStatsEntry *pMap = m_pMapTable != nullptr ? m_pMapTable->findById(mapId) : nullptr;

        if (pMap != nullptr && m_state.completedMaps.contains(lowercase(pMap->fileName)))
        {
            pool.push_back(mapId);
        }
    }

    return pool;
}

MawDimensionMap MawRules::rollDimensionMap(
    RandomStream &stream,
    const std::vector<uint16_t> &pool,
    const std::array<bool, 4> &slots,
    uint8_t activeSlots,
    int power) const
{
    MawDimensionMap map;
    map.mapId = pool.empty() ? 0 : pool[stream.uniform(0, uint32_t(pool.size() - 1))];
    map.affixes = m_dimensionData.rollAffixes(stream, slots);
    map.activeSlots = activeSlots;
    map.power = uint8_t(std::clamp(power, 0, 255));
    return map;
}

const MawItemData &MawRules::itemData() const
{
    return m_itemData;
}

MawLootConfig MawRules::lootConfig() const
{
    const MawModelConfig config = mawModelConfig(m_options, 5);
    MawLootConfig loot;
    loot.difficulty = config.difficulty;
    loot.austerity = config.austerity;
    loot.enchantPower = config.insanityMode ? 1.2 : config.doomMode ? 1.1 : config.trueNightmare ? 1.05 : 1;
    return loot;
}

std::optional<double> MawRules::mapMonsterLevel() const
{
    // The cached levels count only when they are the current map's (audit ROB-2-2).
    const std::vector<int> &levels = m_monsterLevels.nativeLevels;

    if (m_monsterLevels.mapFileName == lowercase(m_currentMap) && !levels.empty()
        && levels[(levels.size() + 1) / 2 - 1] > 0)
    {
        return levels[(levels.size() + 1) / 2 - 1];
    }

    return std::nullopt;
}

double MawRules::mapDropLevel() const
{
    // The lower middle of the map's own B rows (MawMapDropLevel).
    if (const std::optional<double> level = mapMonsterLevel())
    {
        return *level;
    }

    const std::string file = lowercase(m_currentMap);

    // Otherwise 7/8 of a party level plus 1/8 of the band's sum (staticMapDropLevel, MON:1897-1924): the band's sum
    // where the map has a band; in horizontal progression 3/4 of all the continents' banks; else the banks of the
    // other continents plus half this one's, at most 54 (resets add 20 each); Beyond Madness the map's own level; a
    // dimension map its power x 10 + 20.
    const std::array<double, 3> band = m_mapLevels.band(file);
    const double bandSum = band[0] + band[1] + band[2];
    const MapStatsEntry *pMap = m_pMapTable != nullptr ? m_pMapTable->findByFileName(file) : nullptr;
    const uint32_t continentId = pMap != nullptr ? pMap->mergedContinentId : 0;
    const double reset = m_state.resetCount(file) * 20.0;
    double partyLevel = m_state.levelOutside(continentId) + reset;
    double mapLevel = bandSum;

    if (band[0] != 0)
    {
        partyLevel = bandSum;
        mapLevel = 0;
    }
    else if (m_options.progression == RulesetProgression::Horizontal)
    {
        partyLevel = 0.75 * m_state.totalLevel();
    }
    else
    {
        partyLevel += std::min((m_state.levelOn(continentId) + reset) / 2, 54.0);
        mapLevel = 0;
    }

    if (m_options.challengeMode == RulesetChallengeMode::BeyondMadness)
    {
        const int madness = m_mapLevels.madnessLevel(file);
        partyLevel = madness > 0 ? madness : std::pow(bandSum / 3, 1.5);
        mapLevel = 0;
    }

    if (const MawDimensionRun *pRun = dimensionRun(file))
    {
        partyLevel = pRun->power * 10.0 + 20;
    }

    return partyLevel * 7 / 8 + mapLevel / 8;
}

uint64_t MawRules::randomRootSeed() const
{
    return m_randomRootSeed;
}

void MawRules::setRandomRootSeed(uint64_t rootSeed)
{
    m_randomRootSeed = rootSeed;

    if (m_options.challengeMode == RulesetChallengeMode::BeyondMadness)
    {
        m_madnessLedger.loadRun(rootSeed, m_state.madnessDeaths);
        m_state.madnessDeaths = m_madnessLedger.deaths();
        m_madnessSeenDeaths.reset();
    }
}

const MawMadnessLedger &MawRules::madnessLedger() const
{
    return m_madnessLedger;
}

void MawRules::setMadnessLedgerFile(const std::filesystem::path &file)
{
    m_madnessLedger = MawMadnessLedger(file);
}

void MawRules::markMadnessHit(double gameMinutes)
{
    if (m_options.challengeMode == RulesetChallengeMode::BeyondMadness)
    {
        m_madnessLedger.markHit(gameMinutes);
    }
}

void MawRules::updateMadnessLedger(const Party &party, double gameMinutes, bool enemiesNear)
{
    if (m_options.challengeMode != RulesetChallengeMode::BeyondMadness)
    {
        return;
    }

    // A defeat adds to the party's NumDeaths (GameApplication::applyPartyDefeatConsequences).
    const int numDeaths = party.eventVariableValue(uint16_t(EvtVariable::NumDeaths));

    if (m_madnessSeenDeaths && numDeaths > *m_madnessSeenDeaths)
    {
        m_madnessLedger.partyDied();
    }

    m_madnessSeenDeaths = numDeaths;
    m_madnessLedger.update(gameMinutes, enemiesNear);
    m_state.madnessDeaths = m_madnessLedger.deaths();
}

void MawRules::leaveMadnessMap()
{
    if (m_options.challengeMode == RulesetChallengeMode::BeyondMadness)
    {
        m_madnessLedger.leaveMap();
    }
}

std::optional<MawAuraSource> MawRules::activeAura(uint32_t spellId) const
{
    const auto it = m_activeAuras.find(spellId);
    return it != m_activeAuras.end() ? std::optional<MawAuraSource>(it->second) : std::nullopt;
}

void MawRules::setActiveAuras(std::unordered_map<uint32_t, MawAuraSource> auras)
{
    m_activeAuras = std::move(auras);
}

int MawRules::nearbyMonsters() const
{
    return m_nearbyMonsters;
}

void MawRules::setNearbyMonsters(int count)
{
    m_nearbyMonsters = count;
}

bool MawRules::shadowBossNearby() const
{
    return m_shadowBossNearby;
}

void MawRules::setShadowBossNearby(bool nearby)
{
    m_shadowBossNearby = nearby;
}

std::optional<int> MawRules::bountyLevel() const
{
    return m_bountyLevel;
}

void MawRules::setBountyLevel(std::optional<int> levels)
{
    m_bountyLevel = levels;
}

bool MawRules::madnessRewardlessMap(const std::string &mapFileName) const
{
    if (m_options.challengeMode != RulesetChallengeMode::BeyondMadness)
    {
        return false;
    }

    const std::string file = lowercase(mapFileName);
    return mawArenaMap(file) || (m_bountyLevel.has_value() && file == lowercase(m_currentMap));
}

int MawRules::partyStaffResistance() const
{
    return m_partyStaffResistance;
}

void MawRules::setPartyStaffResistance(int resistance)
{
    m_partyStaffResistance = resistance;
}

bool MawRules::takeUnstuck(double gameMinutes)
{
    constexpr double UnstuckWaitGameMinutes = 5;

    // A clock that went back (an earlier save loaded) makes it ready again.
    if (gameMinutes + UnstuckWaitGameMinutes < m_unstuckReadyGameMinutes)
    {
        m_unstuckReadyGameMinutes = 0;
    }

    if (gameMinutes < m_unstuckReadyGameMinutes)
    {
        return false;
    }

    m_unstuckReadyGameMinutes = gameMinutes + UnstuckWaitGameMinutes;
    return true;
}

bool MawRules::austerityIdentifyRespecced() const
{
    return m_austerityIdentifyRespecced;
}

void MawRules::setAusterityIdentifyRespecced(bool respecced)
{
    m_austerityIdentifyRespecced = respecced;
}

std::optional<MawAuraSource> MawRules::memberAura(uint32_t spellId, const Character &member) const
{
    const std::optional<MawAuraSource> aura = activeAura(spellId);
    const std::optional<MawAuraSource> potion = potionAura(spellId, member);

    if (potion
        && (!aura
            || mawAuraStrength(spellId, potion->skill, potion->level)
                > mawAuraStrength(spellId, aura->skill, aura->level)))
    {
        return potion;
    }

    return aura;
}

std::optional<MawAuraSource> MawRules::potionAura(uint32_t spellId, const Character &member)
{
    const int power = member.rulesetState.potionEffect(TimedPotionEffect::Kind::Aura, spellId);

    if (power <= 0)
    {
        return std::nullopt;
    }

    MawAuraSource source;
    source.skill = mawPotionAuraSkill(spellId, power);
    source.mastery = int(SkillMastery::Master);
    source.level = mawPotionAuraLevel(power);
    return source;
}

std::optional<double> MawRules::blessHitSkill(const Character &member) const
{
    const std::optional<double> skill = auraSkill(46, &member);
    return skill || mawWornItemCount(member, {2023}) == 0 ? skill : std::optional<double>(0);
}

std::optional<double> MawRules::auraSkill(uint32_t spellId, const Character *pMember) const
{
    constexpr uint32_t HourOfPower = 86;
    const std::optional<MawAuraSource> own = pMember != nullptr ? memberAura(spellId, *pMember) : activeAura(spellId);
    const bool hourOfPowerCounts = spellId == 5 || spellId == 17 || spellId == 38 || spellId == 47;
    const std::optional<MawAuraSource> hour = hourOfPowerCounts ? activeAura(HourOfPower) : std::nullopt;

    if (!own || !hour)
    {
        // A weak potion casts at a negative skill, which counts as it is.
        return own ? std::optional<double>(own->skill) : hour ? std::optional<double>(hour->skill / 1.5) : std::nullopt;
    }

    return std::max(own->skill, hour->skill / 1.5);
}

MawBalanceModel &MawRules::model(int partyCount) const
{
    auto it = m_models.find(partyCount);

    if (it == m_models.end())
    {
        it = m_models.emplace(partyCount, MawBalanceModel(mawModelConfig(m_options, partyCount))).first;
    }

    return it->second;
}

double MawRules::mapBolster(const MonsterTable &monsterTable, const MapStatsEntry &map) const
{
    monsterLevels(monsterTable, map);
    return m_monsterLevels.bolster;
}

MawMonsterLevelInputs MawRules::monsterLevelInputs(const MapStatsEntry &map) const
{
    MawMonsterLevelInputs inputs;
    inputs.mapFileName = lowercase(map.fileName);
    inputs.encounterPictures = {map.encounter1.pictureName, map.encounter2.pictureName, map.encounter3.pictureName};

    // A world's balance file may name the map's natives itself (MM9's encounter pictures do not always match the
    // monsters its scenes place).
    if (const std::array<std::string, 3> *pNatives = m_mapLevels.natives(map.fileName))
    {
        inputs.encounterPictures = *pNatives;
    }
    inputs.horizontalProgression = m_options.progression == RulesetProgression::Horizontal;
    inputs.madness = m_options.challengeMode == RulesetChallengeMode::BeyondMadness;
    inputs.austerity = m_options.challengeMode == RulesetChallengeMode::Austerity;
    inputs.partyLevel = m_state.levelOutside(map.mergedContinentId);
    inputs.resetCount = m_state.resetCount(inputs.mapFileName);

    if (const MawDimensionRun *pRun = dimensionRun(inputs.mapFileName))
    {
        inputs.dimensionPower = pRun->power;
    }

    if (m_bountyLevel && inputs.mapFileName == m_currentMap)
    {
        inputs.bountyLevel = *m_bountyLevel;
    }

    return inputs;
}

namespace
{
// The mean level of a map's native families' B rows (the Progress tab's map level); 0 without natives.
int nativeMeanLevel(
    const MonsterTable &monsterTable, const MawMapLevels &mapLevels, const MawMonsterLevelInputs &inputs)
{
    const std::unordered_map<int, int> levels = resolveMawMonsterLevels(monsterTable, mapLevels, inputs);
    double sum = 0;
    int count = 0;

    for (const std::string &picture : inputs.encounterPictures)
    {
        const MonsterTable::MonsterStatsEntry *pFamilyB = nullptr;

        for (int id = 1; id <= MawMonsterRows && !picture.empty() && pFamilyB == nullptr; ++id)
        {
            const MonsterTable::MonsterStatsEntry *pStats = monsterTable.findStatsById(int16_t(id));
            pFamilyB = pStats != nullptr && pStats->pictureName == picture + " B" ? pStats : nullptr;
        }

        // A world's family (MM9's "MM9 Thrall" encounters).
        if (pFamilyB == nullptr && !picture.empty())
        {
            const MonsterTable::MonsterStatsEntry *pStats = monsterTable.findStatsByPictureName(picture + " B");
            pFamilyB = pStats != nullptr && pStats->id >= MawWorldMonsterRows ? pStats : nullptr;
        }

        if (pFamilyB != nullptr)
        {
            const auto level = levels.find(pFamilyB->id);
            sum += level != levels.end() ? level->second : pFamilyB->level;
            ++count;
        }
    }

    return count > 0 ? int(std::lround(sum / count)) : 0;
}
}

std::pair<int, int> MawRules::mapLevelSummary(const MonsterTable &monsterTable, const MapStatsEntry &map) const
{
    MawMonsterLevelInputs inputs = monsterLevelInputs(map);
    const int level = nativeMeanLevel(monsterTable, m_mapLevels, inputs);

    if (inputs.resetCount == 0 || level == 0)
    {
        return {level, 0};
    }

    inputs.resetCount = 0;
    return {level, level - nativeMeanLevel(monsterTable, m_mapLevels, inputs)};
}

std::vector<MawRules::MapLevelRow> MawRules::mapLevelTable(const MonsterTable &monsterTable, double bankedLevels) const
{
    std::vector<MapLevelRow> rows;

    if (m_pMapTable == nullptr)
    {
        return rows;
    }

    for (const MapStatsEntry &map : m_pMapTable->getEntries())
    {
        const std::string file = lowercase(map.fileName);

        if (!m_mapLevels.lists(file) || map.name == "pending")
        {
            continue;
        }

        MawMonsterLevelInputs inputs = monsterLevelInputs(map);
        inputs.horizontalProgression = false;
        inputs.madness = false;
        inputs.austerity = false;
        inputs.resetCount = 0;
        inputs.dimensionPower.reset();
        inputs.bountyLevel.reset();
        inputs.partyLevel = 0;

        MapLevelRow row;
        row.fileName = file;
        row.name = map.name;
        row.continentId = map.mergedContinentId;
        row.band = m_mapLevels.band(file);
        row.horizontalStarter = m_mapLevels.isHorizontalStarterMap(file);
        row.madnessLevel = m_mapLevels.madnessLevel(file);
        row.freeLevel = nativeMeanLevel(monsterTable, m_mapLevels, inputs);
        inputs.partyLevel = bankedLevels;
        row.freeBankedLevel = nativeMeanLevel(monsterTable, m_mapLevels, inputs);
        inputs.partyLevel = 0;
        inputs.horizontalProgression = true;
        row.horizontalLevel = nativeMeanLevel(monsterTable, m_mapLevels, inputs);
        inputs.horizontalProgression = false;
        inputs.madness = true;
        row.madnessMapLevel = nativeMeanLevel(monsterTable, m_mapLevels, inputs);
        rows.push_back(std::move(row));
    }

    return rows;
}

std::vector<MawRules::MapMonsterRow> MawRules::mapMonsterTable(
    const MonsterTable &monsterTable, const Party *pParty) const
{
    std::vector<MapMonsterRow> rows;

    if (m_pMapTable == nullptr)
    {
        return rows;
    }

    for (const MapStatsEntry &map : m_pMapTable->getEntries())
    {
        const std::string file = lowercase(map.fileName);

        if (!m_mapLevels.lists(file) || map.name == "pending")
        {
            continue;
        }

        for (const std::string &picture : monsterLevelInputs(map).encounterPictures)
        {
            const MonsterTable::MonsterStatsEntry *pFamilyB =
                picture.empty() ? nullptr : monsterTable.findStatsByPictureName(picture + " B");

            if (pFamilyB == nullptr)
            {
                continue;
            }

            const MawMonsterFamily family = mawMonsterFamily(&monsterTable, pFamilyB->id);

            for (int tier = 1; tier <= 3; ++tier)
            {
                const int monsterId = family.rows[size_t(tier - 1)];
                const MonsterTable::MonsterStatsEntry *pStats =
                    monsterId != 0 ? monsterTable.findStatsById(int16_t(monsterId)) : nullptr;

                if (pStats == nullptr)
                {
                    continue;
                }

                GameplayBolsterRuntimeContext context;
                context.pMap = &map;
                context.pMonsterTable = &monsterTable;
                context.pParty = pParty;
                const GameplayMonsterBolsterResult result = m_gameRules.monsters.resolveMonster(
                    context, *pStats, monsterTable.findById(int16_t(monsterId)));
                rows.push_back({file, map.mergedContinentId, picture, monsterId, pStats->name, uint8_t(tier),
                    result.rulesetFacts.level, result.maxHp, result.armorClass, result.rulesetFacts.attack1Damage});
            }
        }
    }

    return rows;
}

double MawRules::mapBolster(const MapStatsEntry &map) const
{
    return mawMapBolster(m_mapLevels, monsterLevelInputs(map));
}

const std::unordered_map<int, int> &MawRules::monsterLevels(
    const MonsterTable &monsterTable,
    const MapStatsEntry &map) const
{
    const std::string mapFileName = lowercase(map.fileName);
    const double partyLevel = m_state.levelOutside(map.mergedContinentId);
    const int resetCount = m_state.resetCount(mapFileName);
    const MawDimensionRun *pRun = dimensionRun(mapFileName);
    const int dimensionPower = pRun != nullptr ? int(pRun->power) : -1;

    if (m_monsterLevels.mapFileName != mapFileName
        || m_monsterLevels.partyLevel != partyLevel
        || m_monsterLevels.resetCount != resetCount
        || m_monsterLevels.dimensionPower != dimensionPower
        || m_monsterLevels.bountyLevel != (mapFileName == m_currentMap ? m_bountyLevel : std::nullopt))
    {
        const MawMonsterLevelInputs inputs = monsterLevelInputs(map);
        m_monsterLevels.mapFileName = mapFileName;
        m_monsterLevels.partyLevel = partyLevel;
        m_monsterLevels.resetCount = resetCount;
        m_monsterLevels.dimensionPower = dimensionPower;
        m_monsterLevels.bountyLevel = inputs.bountyLevel ? std::optional<int>(int(*inputs.bountyLevel)) : std::nullopt;
        m_monsterLevels.levels = resolveMawMonsterLevels(monsterTable, m_mapLevels, inputs);
        m_monsterLevels.bolster = mawMapBolster(m_mapLevels, inputs);
        m_monsterLevels.nativeLevels.clear();
        // The B rows of the map's encounter pictures, once per slot that names them, by table level then id
        // (currentMapMonsters, MON:448-470).
        std::vector<std::tuple<int, int, int>> natives;

        for (const auto &[monsterId, level] : m_monsterLevels.levels)
        {
            const MonsterTable::MonsterStatsEntry *pStats = monsterTable.findStatsById(int16_t(monsterId));

            for (const std::string &picture : inputs.encounterPictures)
            {
                if (pStats != nullptr && !picture.empty() && pStats->pictureName == picture + " B")
                {
                    natives.emplace_back(pStats->level, monsterId, level);
                }
            }
        }

        std::sort(natives.begin(), natives.end());

        for (const auto &[tableLevel, monsterId, level] : natives)
        {
            m_monsterLevels.nativeLevels.push_back(level);
        }
    }

    return m_monsterLevels.levels;
}
}
