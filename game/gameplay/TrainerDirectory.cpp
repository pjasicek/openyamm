#include "game/gameplay/TrainerDirectory.h"

#include "engine/Utf8Text.h"
#include "engine/Localization.h"

#include "game/gameplay/MasteryTeacherDialog.h"
#include "game/party/Party.h"
#include "game/tables/HouseTable.h"
#include "game/tables/MapStats.h"
#include "game/tables/MergedBaseTables.h"
#include "game/tables/NpcDialogTable.h"

#include <yaml-cpp/yaml.h>

#include <algorithm>
#include <cctype>
#include <exception>
#include <set>
#include <tuple>
#include <unordered_set>

namespace OpenYAMM::Game
{
namespace
{
std::string trimmed(const std::string &text)
{
    size_t first = 0;
    size_t last = text.size();

    while (first < last && std::isspace(static_cast<unsigned char>(text[first])) != 0)
    {
        ++first;
    }

    while (last > first && std::isspace(static_cast<unsigned char>(text[last - 1])) != 0)
    {
        --last;
    }

    return text.substr(first, last - first);
}

std::string lowerCopy(std::string text)
{
    std::transform(text.begin(), text.end(), text.begin(), [](unsigned char c) { return char(std::tolower(c)); });
    return text;
}

bool outdoorFile(const std::string &fileName)
{
    return fileName.size() >= 4 && lowerCopy(fileName.substr(fileName.size() - 4)) == ".odm";
}

size_t teacherSlot(SkillMastery mastery)
{
    return size_t(int(mastery) - int(SkillMastery::Expert));
}

bool teachableMastery(SkillMastery mastery)
{
    return mastery >= SkillMastery::Expert && mastery <= SkillMastery::Grandmaster;
}

uint64_t autonoteKey(uint32_t topicId, uint32_t npcId)
{
    return uint64_t(topicId) << 32 | npcId;
}

bool parseNumber(const std::string &text, float &value)
{
    try
    {
        size_t used = 0;
        value = std::stof(text, &used);
        return used == text.size();
    }
    catch (const std::exception &)
    {
        return false;
    }
}

void replaceAll(std::string &text, const std::string &from, const std::string &to)
{
    for (size_t at = text.find(from); at != std::string::npos; at = text.find(from, at + to.size()))
    {
        text.replace(at, from.size(), to);
    }
}
}

bool TrainerPlaceTable::loadFromRows(const std::vector<std::vector<std::string>> &rows, std::string &errorMessage)
{
    for (const std::vector<std::string> &row : rows)
    {
        if (row.empty() || row[0].empty() || std::isdigit(static_cast<unsigned char>(row[0][0])) == 0)
        {
            continue;
        }

        if (row.size() < 3)
        {
            errorMessage = "trainer place row of house " + row[0] + " has no map and kind";
            return false;
        }

        TrainerPlace place;
        place.houseId = uint32_t(std::stoul(row[0]));
        place.mapFileName = lowerCopy(trimmed(row[1]));
        const std::string kind = lowerCopy(trimmed(row[2]));

        if (kind == "door" || kind == "entrance")
        {
            place.kind = kind == "door" ? TrainerPlaceKind::Door : TrainerPlaceKind::Entrance;

            if (row.size() < 6 || trimmed(row[3]).empty() || !parseNumber(trimmed(row[4]), place.x)
                || !parseNumber(trimmed(row[5]), place.y))
            {
                errorMessage = "trainer place row of house " + row[0] + " has no marker map and position";
                return false;
            }

            place.markerMapFileName = lowerCopy(trimmed(row[3]));
        }
        else if (kind != "indoor")
        {
            errorMessage = "trainer place row of house " + row[0] + " has the unknown kind '" + kind + "'";
            return false;
        }

        add(std::move(place));
    }

    return true;
}

void TrainerPlaceTable::add(TrainerPlace place)
{
    m_places[place.houseId] = std::move(place);
}

const TrainerPlace *TrainerPlaceTable::find(uint32_t houseId) const
{
    const auto found = m_places.find(houseId);
    return found != m_places.end() ? &found->second : nullptr;
}

size_t TrainerPlaceTable::size() const
{
    return m_places.size();
}

bool TeacherLedgerSettings::loadFromYaml(const std::string &text, std::string &errorMessage)
{
    try
    {
        const YAML::Node root = YAML::Load(text);
        price = root["price"].as<int>(price);
        topic = root["topic"].as<std::string>(topic);
        description = root["description"].as<std::string>(description);
        buy = root["buy"].as<std::string>(buy);
        bought = root["bought"].as<std::string>(bought);
        tooPoor = root["too_poor"].as<std::string>(tooPoor);
    }
    catch (const std::exception &exception)
    {
        errorMessage = exception.what();
        return false;
    }

    if (price < 0)
    {
        errorMessage = "the ledger's price is negative";
        return false;
    }

    return true;
}

std::string TeacherLedgerSettings::fill(const std::string &text, const std::string &continentName) const
{
    // teacher_ledger.yml is English; a language pack translates its texts and the continents as terms.
    std::string result = Engine::localize(text);
    replaceAll(result, "{continent}", Engine::localize(continentName));
    replaceAll(result, "{price}", std::to_string(price));
    return result;
}

TrainerNpcState TrainerNpcState::of(const Party &party)
{
    TrainerNpcState state;
    state.topicOverrides = party.npcTopicOverrides();
    state.houseOverrides = party.npcHouseOverrides();
    state.unavailableNpcIds.assign(party.unavailableNpcIds().begin(), party.unavailableNpcIds().end());
    std::sort(state.unavailableNpcIds.begin(), state.unavailableNpcIds.end());
    return state;
}

bool TrainerNpcState::empty() const
{
    return topicOverrides.empty() && houseOverrides.empty() && unavailableNpcIds.empty();
}

uint64_t TrainerNpcState::fingerprint() const
{
    // Order-independent over the unordered maps: a sum of mixed values.
    const auto mix = [](uint64_t value)
    {
        value ^= value >> 33;
        value *= 0xff51afd7ed558ccdull;
        value ^= value >> 33;
        value *= 0xc4ceb9fe1a85ec53ull;
        return value ^ (value >> 33);
    };
    uint64_t sum = 0;

    for (const auto &[npcId, slots] : topicOverrides)
    {
        for (const auto &[slot, topicId] : slots)
        {
            sum += mix(uint64_t(npcId) << 40 ^ uint64_t(slot) << 32 ^ topicId);
        }
    }

    for (const auto &[npcId, houseId] : houseOverrides)
    {
        sum += mix(0x1ull << 62 ^ uint64_t(npcId) << 32 ^ houseId);
    }

    for (uint32_t npcId : unavailableNpcIds)
    {
        sum += mix(0x2ull << 62 ^ npcId);
    }

    return mix(sum) | 1;
}

void TrainerLinks::addWalk(uint32_t fromMap, uint32_t toMap)
{
    if (fromMap != toMap)
    {
        m_links[fromMap].push_back({toMap, TrainerLink::Walk, 0});
    }
}

void TrainerLinks::addRoute(uint32_t fromMap, uint32_t toMap, uint32_t requiredQBit)
{
    if (fromMap != toMap)
    {
        m_links[fromMap].push_back({toMap, TrainerLink::Route, requiredQBit});
    }
}

TrainerNeighbours TrainerLinks::neighbours(
    std::optional<uint32_t> currentMap,
    std::optional<uint32_t> referenceMap,
    const std::function<bool(uint32_t)> &hasQBit) const
{
    TrainerNeighbours result;

    for (const std::optional<uint32_t> &from : {currentMap, referenceMap})
    {
        const auto links = from ? m_links.find(*from) : m_links.end();

        if (links == m_links.end())
        {
            continue;
        }

        for (const Link &link : links->second)
        {
            if (link.requiredQBit != 0 && !(hasQBit && hasQBit(link.requiredQBit)))
            {
                continue;
            }

            const auto [found, inserted] = result.emplace(link.toMap, link.kind);

            if (!inserted && link.kind == TrainerLink::Walk)
            {
                found->second = TrainerLink::Walk;
            }
        }
    }

    return result;
}

TrainerDirectory TrainerDirectory::build(const TrainerDirectorySource &source, TrainerNpcState state)
{
    return buildFrom(std::make_shared<const TrainerDirectorySource>(source), state, {}, {});
}

TrainerDirectory TrainerDirectory::buildFrom(
    std::shared_ptr<const TrainerDirectorySource> pSource,
    const TrainerNpcState &state,
    const TrainerLinks &links,
    const TeacherLedgerSettings &ledger)
{
    const TrainerDirectorySource &source = *pSource;
    TrainerDirectory directory;
    directory.m_links = links;
    directory.m_ledger = ledger;

    for (const auto &[topicId, topic] : source.topics)
    {
        if (teachableMastery(topic.mastery))
        {
            directory.m_skills[topic.skill];
        }
    }

    std::unordered_map<std::string, uint32_t> mapIdsByFile;

    for (const auto &[mapId, map] : source.maps)
    {
        mapIdsByFile.emplace(lowerCopy(map.fileName), mapId);
    }

    // Each house shown once: where its door is, else the map house_data names, or nothing when unknown.
    std::unordered_map<uint32_t, std::optional<TrainerEntry>> places;
    const auto placeOf = [&](uint32_t houseId) -> const std::optional<TrainerEntry> &
    {
        const auto found = places.find(houseId);

        if (found != places.end())
        {
            return found->second;
        }

        std::optional<TrainerEntry> place;
        const auto house = source.houses.find(houseId);
        const TrainerPlace *pPlace = source.places.find(houseId);
        uint32_t mapId = house != source.houses.end() ? house->second.mapId : 0;

        if (pPlace != nullptr)
        {
            if (const auto door = mapIdsByFile.find(pPlace->mapFileName); door != mapIdsByFile.end())
            {
                mapId = door->second;
            }
        }

        const auto map = mapId != 0 ? source.maps.find(mapId) : source.maps.end();

        if (house != source.houses.end() && map != source.maps.end())
        {
            place = TrainerEntry{};
            place->houseId = houseId;
            place->houseName = trimmed(house->second.name);

            if (place->houseName == "House")
            {
                place->houseName.clear();
            }

            place->mapId = mapId;
            place->mapName = trimmed(map->second.name);

            if (place->mapName.empty())
            {
                place->mapName = map->second.fileName;
            }

            place->mapFileName = lowerCopy(map->second.fileName);
            place->continent = map->second.continent;
            place->outdoor = outdoorFile(map->second.fileName);

            if (pPlace != nullptr)
            {
                place->place = *pPlace;
                const auto marker = mapIdsByFile.find(pPlace->markerMapFileName);

                if (marker != mapIdsByFile.end())
                {
                    place->markerMapName = trimmed(source.maps.at(marker->second).name);
                }
            }
        }

        return places.emplace(houseId, std::move(place)).first->second;
    };

    const std::unordered_set<uint32_t> unavailable(state.unavailableNpcIds.begin(), state.unavailableNpcIds.end());
    std::set<std::tuple<std::string, size_t, uint32_t, uint32_t>> listed;

    for (const TrainerDirectorySource::Npc &npc : source.npcs)
    {
        if (unavailable.contains(npc.id))
        {
            continue;
        }

        std::vector<uint32_t> topicIds = npc.topicIds;

        if (const auto slots = state.topicOverrides.find(npc.id); slots != state.topicOverrides.end())
        {
            for (const auto &[slot, topicId] : slots->second)
            {
                if (slot >= topicIds.size())
                {
                    topicIds.resize(slot + 1, 0);
                }

                topicIds[slot] = topicId;
            }
        }

        std::vector<std::pair<uint32_t, const TrainerDirectorySource::Topic *>> taught;

        for (uint32_t topicId : topicIds)
        {
            const auto topic = source.topics.find(topicId);

            if (topic != source.topics.end() && teachableMastery(topic->second.mastery))
            {
                taught.emplace_back(topicId, &topic->second);
            }
        }

        if (taught.empty())
        {
            continue;
        }

        uint32_t homeId = npc.houseId;

        if (const auto moved = state.houseOverrides.find(npc.id); moved != state.houseOverrides.end())
        {
            homeId = moved->second;
        }

        std::vector<std::pair<uint32_t, bool>> houses;
        const auto add = [&houses](uint32_t houseId, bool extra)
        {
            const bool known = std::any_of(houses.begin(), houses.end(),
                [houseId](const auto &house) { return house.first == houseId; });

            if (houseId != 0 && !known)
            {
                houses.emplace_back(houseId, extra);
            }
        };
        add(homeId, false);

        if (const auto extra = source.extraHouses.find(npc.id); extra != source.extraHouses.end())
        {
            for (uint32_t houseId : extra->second)
            {
                add(houseId, true);
            }
        }

        for (const auto &[houseId, extraHouse] : houses)
        {
            const std::optional<TrainerEntry> &place = placeOf(houseId);

            if (!place)
            {
                continue;
            }

            for (const auto &[topicId, pTopic] : taught)
            {
                const size_t slot = teacherSlot(pTopic->mastery);

                if (!listed.emplace(pTopic->skill, slot, npc.id, houseId).second)
                {
                    continue;
                }

                TrainerEntry entry = *place;
                entry.npcId = npc.id;
                entry.name = trimmed(npc.name);
                entry.topicId = topicId;
                entry.skill = pTopic->skill;
                entry.skillId = pTopic->skillId;
                entry.mastery = pTopic->mastery;
                entry.requiredGold = pTopic->requiredGold;
                entry.requiredSkill = pTopic->requiredSkill;
                entry.extraHouse = extraHouse;

                if (const auto note = source.autonotes.find(autonoteKey(topicId, npc.id));
                    note != source.autonotes.end())
                {
                    entry.autonoteId = note->second;
                }

                directory.m_skills[pTopic->skill][slot].push_back(std::move(entry));
            }
        }
    }

    for (const TrainerEntry &entry : source.actorTeachers)
        directory.m_skills[entry.skill][teacherSlot(entry.mastery)].push_back(entry);

    directory.m_pSource = std::move(pSource);
    return directory;
}

TrainerDirectory TrainerDirectory::build(
    const NpcDialogTable &npcs,
    const MergedTeacherTopicTable &teacherTopics,
    const MergedTeacherAutonoteTable &teacherAutonotes,
    const HouseTable &houses,
    const MapStats &maps,
    TrainerPlaceTable places,
    TeacherLedgerSettings ledger,
    std::vector<TrainerEntry> actorTeachers)
{
    TrainerDirectorySource source;
    const auto addTopic = [&](uint32_t topicId)
    {
        if (source.topics.contains(topicId))
        {
            return;
        }

        const std::optional<MasteryTeacherTopicDefinition> topic = resolveMasteryTeacherTopic(topicId, &teacherTopics);

        if (topic)
        {
            source.topics[topicId] = {canonicalSkillName(topic->skillName), topic->targetMastery, topic->skillId,
                topic->requiredGold, topic->requiredSkill};
        }
    };

    for (const MergedTeacherTopicEntry &topic : teacherTopics.entries())
    {
        addTopic(topic.topicId);
    }

    // MM8's original lesson topics, which a script may give an NPC (resolveMasteryTeacherTopic's fallback range).
    for (uint32_t topicId = 300; topicId <= 416; ++topicId)
    {
        addTopic(topicId);
    }

    for (const NpcEntry &npc : npcs.entries())
    {
        source.npcs.push_back({npc.id, npc.name, npc.houseId, npc.topicIds});

        for (uint32_t topicId : npc.topicIds)
        {
            if (topicId != 0)
            {
                addTopic(topicId);
            }
        }
    }

    // The autonote of every NPC and teacher topic pair (the topic may reach the NPC through a script).
    for (const TrainerDirectorySource::Npc &npc : source.npcs)
    {
        for (const auto &[topicId, topic] : source.topics)
        {
            if (const std::optional<uint32_t> autonote = teacherAutonotes.autonoteIdForTopicAndNpc(topicId, npc.id))
            {
                source.autonotes[autonoteKey(topicId, npc.id)] = *autonote;
            }
        }
    }

    source.extraHouses = npcs.extraHouses();

    for (const auto &[houseId, house] : houses.entries())
    {
        source.houses[houseId] = {house.name, house.mapId};
    }

    TrainerLinks links;

    for (const MapStatsEntry &map : maps.getEntries())
    {
        source.maps[uint32_t(map.id)] = {map.name, map.fileName, map.mergedContinentId};

        for (const MapBoundaryEdge edge :
            {MapBoundaryEdge::North, MapBoundaryEdge::South, MapBoundaryEdge::East, MapBoundaryEdge::West})
        {
            const std::optional<MapEdgeTransition> *pTransition = map.edgeTransition(edge);
            const MapStatsEntry *pTarget = pTransition != nullptr && pTransition->has_value()
                ? maps.findByFileName((*pTransition)->destinationMapFileName)
                : nullptr;

            if (pTarget != nullptr)
            {
                links.addWalk(uint32_t(map.id), uint32_t(pTarget->id));
            }
        }
    }

    for (const auto &[houseId, house] : houses.entries())
    {
        for (const HouseEntry::TransportRoute &route : house.transportRoutes)
        {
            const MapStatsEntry *pTarget = maps.findByFileName(route.mapFileName);

            if (house.mapId != 0 && pTarget != nullptr)
            {
                links.addRoute(house.mapId, uint32_t(pTarget->id), route.requiredQBit);
            }
        }
    }

    source.places = std::move(places);
    source.actorTeachers = std::move(actorTeachers);
    return buildFrom(std::make_shared<const TrainerDirectorySource>(std::move(source)), {}, links, ledger);
}

const std::array<std::vector<TrainerEntry>, 3> *TrainerDirectory::find(const std::string &canonicalSkill) const
{
    const auto found = m_skills.find(canonicalSkill);
    return found != m_skills.end() ? &found->second : nullptr;
}

const std::unordered_map<std::string, std::array<std::vector<TrainerEntry>, 3>> &TrainerDirectory::skills() const
{
    return m_skills;
}

const TrainerDirectory &TrainerDirectory::forParty(const Party &party) const
{
    const TrainerNpcState state = TrainerNpcState::of(party);

    if (state.empty() || m_pSource == nullptr)
    {
        return *this;
    }

    const uint64_t fingerprint = state.fingerprint();

    if (m_pPartyDirectory == nullptr || m_partyFingerprint != fingerprint)
    {
        m_pPartyDirectory = std::make_shared<const TrainerDirectory>(buildFrom(m_pSource, state, m_links, m_ledger));
        m_partyFingerprint = fingerprint;
    }

    return *m_pPartyDirectory;
}

std::vector<uint32_t> TrainerDirectory::continentAutonotes(uint32_t continent) const
{
    std::set<uint32_t> autonotes;

    for (const auto &[skill, masteries] : m_skills)
    {
        for (const std::vector<TrainerEntry> &entries : masteries)
        {
            for (const TrainerEntry &entry : entries)
            {
                if (entry.continent == continent && !entry.extraHouse && entry.autonoteId)
                {
                    autonotes.insert(*entry.autonoteId);
                }
            }
        }
    }

    return {autonotes.begin(), autonotes.end()};
}

std::optional<uint32_t> TrainerDirectory::mapContinent(uint32_t mapId) const
{
    if (m_pSource == nullptr)
    {
        return std::nullopt;
    }

    const auto map = m_pSource->maps.find(mapId);
    return map != m_pSource->maps.end() ? map->second.continent : std::nullopt;
}

std::string TrainerDirectory::mapName(const std::string &mapFileName) const
{
    const std::string wanted = lowerCopy(mapFileName);

    if (m_pSource != nullptr)
    {
        for (const auto &[mapId, map] : m_pSource->maps)
        {
            if (lowerCopy(map.fileName) == wanted)
            {
                return trimmed(map.name);
            }
        }
    }

    return mapFileName;
}

const TrainerLinks &TrainerDirectory::links() const
{
    return m_links;
}

const TeacherLedgerSettings &TrainerDirectory::ledger() const
{
    return m_ledger;
}

const TrainerPlaceTable &TrainerDirectory::places() const
{
    static const TrainerPlaceTable empty;
    return m_pSource != nullptr ? m_pSource->places : empty;
}

std::vector<PickedTrainer> pickTrainers(
    const std::vector<TrainerEntry> &entries,
    std::optional<uint32_t> currentMap,
    std::optional<uint32_t> currentContinent,
    size_t limit,
    const TrainerNeighbours &neighbours,
    std::optional<uint32_t> referenceMap)
{
    std::vector<PickedTrainer> ranked;
    ranked.reserve(entries.size());

    for (const TrainerEntry &entry : entries)
    {
        PickedTrainer picked;
        picked.entry = entry;
        const auto neighbour = neighbours.find(entry.mapId);

        if (entry.mapId == currentMap || entry.mapId == referenceMap)
        {
            picked.rank = 0;
            picked.outside = entry.mapId != currentMap;
        }
        else if (neighbour != neighbours.end())
        {
            picked.rank = 1;
            picked.link = neighbour->second;
        }
        else if (currentContinent && entry.continent == currentContinent)
        {
            picked.rank = 2;
        }

        ranked.push_back(std::move(picked));
    }

    std::sort(ranked.begin(), ranked.end(), [](const PickedTrainer &left, const PickedTrainer &right)
    {
        const TrainerEntry &a = left.entry;
        const TrainerEntry &b = right.entry;
        const uint64_t continentA = a.continent ? *a.continent : UINT64_MAX;
        const uint64_t continentB = b.continent ? *b.continent : UINT64_MAX;
        return std::tie(left.rank, b.outdoor, continentA, a.mapName, a.name, a.npcId, a.houseId)
            < std::tie(right.rank, a.outdoor, continentB, b.mapName, b.name, b.npcId, b.houseId);
    });

    std::vector<PickedTrainer> picked;
    std::unordered_set<uint32_t> taken;

    for (PickedTrainer &trainer : ranked)
    {
        if (picked.size() >= limit)
        {
            break;
        }

        if (taken.insert(trainer.entry.npcId).second)
        {
            picked.push_back(std::move(trainer));
        }
    }

    return picked;
}

std::string trainerContinentName(uint32_t continent)
{
    switch (continent)
    {
        case 1:
            return "Jadame";
        case 2:
            return "Antagarich";
        case 3:
            return "Enroth";
        case 5:
            return "Chedian";
        default:
            return {};
    }
}

uint32_t teacherMapNoteId(uint32_t continent, SkillMastery mastery, uint32_t skillId)
{
    return continent * 1000 + uint32_t(teacherSlot(mastery) + 1) * 100 + skillId;
}

bool trainerKnown(const TrainerEntry &entry, const Party &party)
{
    if (entry.continent && party.hasTeacherLedger(*entry.continent))
    {
        return true;
    }

    if (entry.rudeId != 0)
    {
        if (party.findJournalMapNote(entry.mapFileName, 90000 + entry.rudeId) != nullptr)
            return true;
        // Older saves already remember dialogue choices, including teacher offers.
        for (size_t row = 0; row < entry.dialogueRowCount; ++row)
            if (party.hasChosenMm9RudeRow(entry.rudeId, row))
                return true;
        return false;
    }
    if (entry.autonoteId)
    {
        return party.hasAutonote(*entry.autonoteId);
    }

    return entry.continent
        && party.findJournalMapNote(entry.mapFileName, teacherMapNoteId(*entry.continent, entry.mastery, entry.skillId))
            != nullptr;
}

void discoverActorTeacher(Party &party, uint32_t rudeId)
{
    if (party.trainerDirectory() == nullptr)
        return;
    for (const auto &[skill, masteries] : party.trainerDirectory()->skills())
        for (const auto &entries : masteries)
            for (const TrainerEntry &entry : entries)
            {
                if (entry.rudeId != rudeId || !entry.place
                    || party.findJournalMapNote(entry.mapFileName, 90000 + rudeId) != nullptr)
                    continue;
                JournalMapNote note;
                note.id = 90000 + rudeId;
                note.mapFileName = entry.mapFileName;
                note.x = entry.place->x;
                note.y = entry.place->y;
                note.text = entry.name;
                party.setJournalMapNote(note);
            }
}

bool trainerSearchMatches(const std::string &search, const std::vector<std::string> &fields)
{
    std::string hay;

    for (const std::string &field : fields)
    {
        hay += Engine::Utf8::lower(field) + '\n';
    }

    const std::string lowered = Engine::Utf8::lower(search);
    size_t start = 0;

    while (start < lowered.size())
    {
        const size_t end = std::min(lowered.find(' ', start), lowered.size());

        if (end > start && hay.find(lowered.substr(start, end - start)) == std::string::npos)
        {
            return false;
        }

        start = end + 1;
    }

    return true;
}

bool buyTeacherLedger(Party &party, const TrainerDirectory &directory, uint32_t continent)
{
    const int price = directory.ledger().price;

    if (party.hasTeacherLedger(continent) || party.gold() < price)
    {
        return false;
    }

    party.addGold(-price, GoldReason::Guild);
    party.addTeacherLedger(continent);

    for (uint32_t autonoteId : directory.forParty(party).continentAutonotes(continent))
    {
        party.setAutonote(autonoteId, true);
    }

    return true;
}
}
