#include "game/rules/maw/MawTrainerHints.h"
#include "engine/Localization.h"

#include "game/party/Party.h"
#include "game/rules/maw/MawRules.h"
#include "game/tables/ClassSkillTable.h"
#include "game/tables/MapStats.h"

#include <algorithm>
#include <cctype>
#include <cstdint>

namespace OpenYAMM::Game
{
namespace
{
// The tooltip box is short: the nearest teacher only.
constexpr size_t MaxTrainers = 1;
// The next mastery's teachers are all ones the party has not found (TrainerDirectory.h trainerKnown).
constexpr std::string_view UnknownTrainers =
    Engine::trNoop("No trainer known yet: a tavern sells the Ledger of Teachers.");

bool outdoorFile(const std::string &fileName)
{
    if (fileName.size() < 4)
    {
        return false;
    }

    std::string extension = fileName.substr(fileName.size() - 4);
    std::transform(extension.begin(), extension.end(), extension.begin(),
        [](unsigned char c) { return char(std::tolower(c)); });
    return extension == ".odm";
}

size_t teacherSlot(SkillMastery mastery)
{
    return size_t(int(mastery) - int(SkillMastery::Expert));
}
}

std::string mawComposeTrainerHint(const MawTrainerHintInfo &info)
{
    MawTrainerHintKind kind = info.kind;

    // Teachers the party has not found yet still say what the lesson needs.
    if (kind == MawTrainerHintKind::Trainers && (!info.trainers || info.trainers->empty()) && !info.unknownTrainers)
    {
        kind = MawTrainerHintKind::None;
    }

    if (kind == MawTrainerHintKind::ClassMaximum)
    {
        return Engine::tr("<value>Highest mastery for this class reached.</>");
    }

    if (kind == MawTrainerHintKind::Grandmaster)
    {
        return Engine::tr("<value>Grandmaster reached.</>");
    }

    const std::string mastery = Engine::tr(masteryDisplayName(info.nextMastery));
    const std::string noTrainer = Engine::tr(info.unknownTrainers ? UnknownTrainers : "No trainer found.");

    if (kind == MawTrainerHintKind::None)
    {
        return Engine::tr("<value>Next mastery: {mastery}</>", {{"mastery", mastery}}) + "\n " + noTrainer;
    }

    if (kind == MawTrainerHintKind::Automatic)
    {
        return Engine::tr("<value>Next mastery: {mastery}</>", {{"mastery", mastery}}) + "\n "
            + Engine::tr("Learned automatically at skill {level}.", {{"level", info.requiredLevel}});
    }

    std::string text = Engine::tr(info.level >= info.requiredLevel
            ? "<value>Next mastery: {mastery} (skill </><good>{level}</><value> required)</>"
            : "<value>Next mastery: {mastery} (skill </><bad>{level}</><value> required)</>",
        {{"mastery", mastery}, {"level", info.requiredLevel}});

    if (kind == MawTrainerHintKind::Promotion)
    {
        text += "\n " + Engine::tr("Requires a class promotion first.");
    }

    if (info.trainers && info.trainers->empty())
    {
        text += "\n " + noTrainer;
    }

    for (const PickedTrainer &trainer : info.trainers.value_or(std::vector<PickedTrainer>{}))
    {
        const TrainerEntry &entry = trainer.entry;
        text += "\n "
            + (entry.houseName.empty()
                    ? Engine::tr("{trainer} - {map}",
                        {{"trainer", Engine::localize(entry.name)}, {"map", Engine::localize(entry.mapName)}})
                    : Engine::tr("{trainer} - {house}, {map}",
                        {{"trainer", Engine::localize(entry.name)}, {"house", Engine::localize(entry.houseName)},
                            {"map", Engine::localize(entry.mapName)}}));

        if (trainer.rank == 0)
        {
            text += " " + Engine::tr(trainer.outside ? "<good>(outside)</>" : "<good>(this map)</>");
            continue;
        }

        std::vector<std::string> tags;

        if (trainer.rank == 1 && trainer.link)
        {
            tags.push_back(Engine::tr(*trainer.link == TrainerLink::Walk ? "next map" : "coach/boat"));
        }

        if (entry.continent && entry.continent != info.currentContinent)
        {
            const std::string continent = Engine::localize(trainerContinentName(*entry.continent));

            if (!continent.empty())
            {
                tags.push_back(continent);
            }
        }

        for (size_t tag = 0; tag < tags.size(); ++tag)
        {
            text += (tag == 0 ? " (" : ", ") + tags[tag];
        }

        if (!tags.empty())
        {
            text += ")";
        }
    }

    return text;
}

std::optional<MawTrainerHintInfo> mawExplainTrainerHint(
    const TrainerDirectory &directory,
    const MawTrainerHintQuery &query)
{
    if (query.level == 0 || query.mastery == SkillMastery::None)
    {
        return std::nullopt;
    }

    const std::array<std::vector<TrainerEntry>, 3> *pTeachers = directory.find(query.skill);
    MawTrainerHintInfo info;

    if (query.mastery >= SkillMastery::Grandmaster)
    {
        // Nothing left to learn: said only for skills that have masteries to learn at all.
        if (pTeachers == nullptr && !query.ladder)
        {
            return std::nullopt;
        }

        info.kind = MawTrainerHintKind::Grandmaster;
        return info;
    }

    info.nextMastery = SkillMastery(int(query.mastery) + 1);
    info.level = query.level;
    info.requiredLevel = query.requiredLevel;

    // A party of one gets these masteries by skill level alone, whatever the class.
    if (query.soloMastery)
    {
        info.kind = MawTrainerHintKind::Automatic;
        return info;
    }

    if (pTeachers == nullptr && !query.ladder)
    {
        return std::nullopt;
    }

    const bool reachable = query.classCap >= info.nextMastery;

    if (!reachable && query.promotionCap < info.nextMastery)
    {
        info.kind = MawTrainerHintKind::ClassMaximum;
        return info;
    }

    // The same ladder and rule as the masteries MAW grants on a raise.
    if (query.ladder)
    {
        info.requiredLevel = (*query.ladder)[teacherSlot(info.nextMastery)];
        info.kind = reachable ? MawTrainerHintKind::Automatic : MawTrainerHintKind::Promotion;
        return info;
    }

    info.currentContinent = query.currentContinent;
    const std::vector<TrainerEntry> &teachers = (*pTeachers)[teacherSlot(info.nextMastery)];
    std::vector<TrainerEntry> known;

    for (const TrainerEntry &entry : teachers)
    {
        if (!query.known || query.known(entry))
        {
            known.push_back(entry);
        }
    }

    info.unknownTrainers = known.empty() && !teachers.empty();
    info.trainers = pickTrainers(known, query.currentMap, query.currentContinent, MaxTrainers, query.neighbours,
        query.referenceMap);
    info.kind = reachable ? MawTrainerHintKind::Trainers : MawTrainerHintKind::Promotion;
    return info;
}

std::string mawTrainerHintText(
    const MawRules &rules,
    const Party &party,
    const Character &character,
    const std::string &canonicalSkill,
    MawSkillMode mode)
{
    const MawTrainerHints &hints = rules.trainerHints();
    const CharacterSkill *pSkill = character.findSkill(canonicalSkill);

    if (!rules.options().preferences.trainerHints || hints.pMapStats == nullptr || hints.pClassSkillTable == nullptr
        || party.trainerDirectory() == nullptr || rules.currentMap().empty() || pSkill == nullptr)
    {
        return {};
    }

    const TrainerDirectory &directory = party.trainerDirectory()->forParty(party);

    const MapStatsEntry *pCurrentMap = hints.pMapStats->findByFileName(rules.currentMap());
    const MapStatsEntry *pReferenceMap = !outdoorFile(rules.currentMap()) && !rules.lastOutdoorMap().empty()
        ? hints.pMapStats->findByFileName(rules.lastOutdoorMap())
        : nullptr;
    MawTrainerHintQuery query;
    query.skill = canonicalSkill;
    query.level = pSkill->level;
    query.mastery = pSkill->mastery;
    query.classCap = hints.pClassSkillTable->getEffectiveCap(character.className, character.raceId, canonicalSkill);
    query.promotionCap =
        hints.pClassSkillTable->getHighestPromotionEffectiveCap(character.className, character.raceId, canonicalSkill);

    if (pSkill->mastery < SkillMastery::Grandmaster)
    {
        query.requiredLevel = rules.gameRules().skills.masteryRequiredLevel(canonicalSkill,
            SkillMastery(int(std::max(pSkill->mastery, SkillMastery::Normal)) + 1));
    }

    query.ladder = mawSkillMasteryLadder(canonicalSkill, mode);
    query.soloMastery = party.members().size() == 1 && mawIsSoloMasterySkill(canonicalSkill);

    if (pCurrentMap != nullptr)
    {
        query.currentMap = uint32_t(pCurrentMap->id);
        query.currentContinent = pCurrentMap->mergedContinentId;
    }

    if (pReferenceMap != nullptr)
    {
        query.referenceMap = uint32_t(pReferenceMap->id);
    }

    query.neighbours = directory.links().neighbours(query.currentMap, query.referenceMap,
        [&party](uint32_t qbit) { return party.hasQuestBit(qbit); });
    query.known = [&party](const TrainerEntry &entry) { return trainerKnown(entry, party); };
    const std::optional<MawTrainerHintInfo> info = mawExplainTrainerHint(directory, query);
    return info ? mawFillText(mawComposeTrainerHint(*info), {}) : std::string();
}
}
