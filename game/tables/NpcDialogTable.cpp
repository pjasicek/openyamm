#include "game/tables/NpcDialogTable.h"

#include "game/tables/RosterTable.h"

#include <algorithm>
#include <array>
#include <cctype>
#include <cstdlib>

namespace OpenYAMM::Game
{
namespace
{
bool parseUnsigned(const std::string &text, uint32_t &value)
{
    if (text.empty() || text[0] == '#')
    {
        return false;
    }

    char *pEnd = nullptr;
    const unsigned long parsed = std::strtoul(text.c_str(), &pEnd, 10);

    if (pEnd == text.c_str() || *pEnd != '\0')
    {
        return false;
    }

    value = static_cast<uint32_t>(parsed);
    return true;
}

bool parseLeadingUnsigned(const std::string &text, uint32_t &value)
{
    if (text.empty() || text[0] == '#')
    {
        return false;
    }

    char *pEnd = nullptr;
    const unsigned long parsed = std::strtoul(text.c_str(), &pEnd, 10);

    if (pEnd == text.c_str())
    {
        return false;
    }

    value = static_cast<uint32_t>(parsed);
    return true;
}

bool parseJoinFlag(const std::string &text)
{
    if (text.empty())
    {
        return false;
    }

    if (text == "x" || text == "X" || text == "y" || text == "Y")
    {
        return true;
    }

    uint32_t value = 0;
    return parseUnsigned(text, value) && value != 0;
}

std::string normalizeName(const std::string &text)
{
    std::string normalized;
    normalized.reserve(text.size());

    bool previousWasSpace = true;

    for (char character : text)
    {
        const unsigned char unsignedCharacter = static_cast<unsigned char>(character);

        if (std::isspace(unsignedCharacter) != 0)
        {
            if (!previousWasSpace)
            {
                normalized.push_back(' ');
                previousWasSpace = true;
            }

            continue;
        }

        normalized.push_back(static_cast<char>(std::tolower(unsignedCharacter)));
        previousWasSpace = false;
    }

    if (!normalized.empty() && normalized.back() == ' ')
    {
        normalized.pop_back();
    }

    return normalized;
}

bool isTeacherHintTopicRow(const std::vector<std::string> &row)
{
    if (row.size() <= 6)
    {
        return false;
    }

    std::string loweredCell;
    loweredCell.reserve(row[6].size());

    for (char character : row[6])
    {
        loweredCell.push_back(static_cast<char>(std::tolower(static_cast<unsigned char>(character))));
    }

    return loweredCell == "teacher hint";
}

bool isRosterJoinTopicLabel(const NpcTopicEntry &entry)
{
    return entry.topic == "Roster Join Event" || entry.topic == "Join";
}

std::optional<NpcDialogTable::RosterJoinOffer> buildRosterJoinOffer(
    const NpcTopicEntry &entry,
    const RosterTable &rosterTable,
    const std::unordered_map<uint32_t, std::string> &textsById
)
{
    if (!isRosterJoinTopicLabel(entry))
    {
        return std::nullopt;
    }

    const RosterEntry *pRosterEntry = rosterTable.findByName(entry.notes);

    if (pRosterEntry == nullptr)
    {
        return std::nullopt;
    }

    const uint32_t inviteTextId = 198 + pRosterEntry->id * 2;
    const uint32_t partyFullTextId = inviteTextId + 1;

    if (!textsById.contains(inviteTextId) || !textsById.contains(partyFullTextId))
    {
        return std::nullopt;
    }

    NpcDialogTable::RosterJoinOffer offer = {};
    offer.topicId = entry.id;
    offer.rosterId = pRosterEntry->id;
    offer.inviteTextId = inviteTextId;
    offer.partyFullTextId = partyFullTextId;
    return offer;
}

std::optional<NpcDialogTable::GuildMembershipOffer> buildGuildMembershipOffer(uint32_t topicId)
{
    struct MembershipMapping
    {
        uint32_t topicId = 0;
        uint32_t guildType = 0;
        uint32_t cost = 0;
        uint32_t descriptionTextId = 0;
        uint32_t joinTextId = 0;
        uint32_t autonoteId = 0;
    };

    constexpr std::array<MembershipMapping, 28> mappings = {{
        {1150, 14, 100, 1830, 1049, 564},
        {1151, 15, 100, 1039, 1050, 565},
        {1152, 6, 50, 1040, 1051, 566},
        {1153, 8, 50, 1041, 1052, 567},
        {1154, 5, 50, 1042, 1053, 568},
        {1155, 7, 50, 1043, 1054, 569},
        {1156, 11, 50, 1044, 1055, 570},
        {1157, 10, 50, 1045, 1056, 571},
        {1158, 9, 50, 1046, 1057, 572},
        {1159, 12, 1000, 1047, 1058, 573},
        {1160, 13, 1000, 1048, 1059, 574},
        {1694, 14, 100, 1830, 1049, 564},
        {1695, 15, 100, 1039, 1050, 565},
        {1696, 16, 25, 1832, 1849, 629},
        {1697, 17, 50, 1833, 1850, 630},
        {1698, 18, 50, 1834, 1851, 631},
        {1699, 19, 25, 1835, 1852, 632},
        {1700, 20, 50, 1836, 1853, 633},
        {1701, 21, 50, 1837, 1854, 634},
        {1702, 6, 50, 1040, 1051, 566},
        {1703, 8, 50, 1041, 1052, 567},
        {1704, 5, 50, 1042, 1053, 568},
        {1705, 7, 50, 1043, 1054, 569},
        {1706, 11, 50, 1044, 1055, 570},
        {1707, 10, 50, 1045, 1056, 571},
        {1708, 9, 50, 1046, 1057, 572},
        {1709, 12, 1000, 1047, 1058, 573},
        {1710, 13, 1000, 1048, 1059, 574},
    }};

    const auto mappingIt = std::find_if(
        mappings.begin(),
        mappings.end(),
        [topicId](const MembershipMapping &mapping)
        {
            return mapping.topicId == topicId;
        });

    if (mappingIt == mappings.end())
    {
        return std::nullopt;
    }

    NpcDialogTable::GuildMembershipOffer offer = {};
    offer.topicId = mappingIt->topicId;
    offer.guildType = mappingIt->guildType;
    offer.cost = mappingIt->cost;
    offer.descriptionTextId = mappingIt->descriptionTextId;
    offer.joinTextId = mappingIt->joinTextId;
    offer.autonoteId = mappingIt->autonoteId;
    return offer;
}
}

bool NpcDialogTable::loadGreetingsFromRows(const std::vector<std::vector<std::string>> &rows)
{
    m_greetings.clear();
    std::vector<std::string> pendingRow;

    auto appendPendingRow = [this](const std::vector<std::string> &row)
    {
        if (row.size() <= 4)
        {
            return;
        }

        uint32_t id = 0;

        if (!parseUnsigned(row[0], id))
        {
            return;
        }

        NpcGreetingEntry entry = {};
        entry.id = id;
        entry.greetingPrimary = row[1];
        entry.greetingSecondary = row[2];
        entry.owner = row[4];
        m_greetings[id] = std::move(entry);
    };

    auto appendContinuationRow = [](std::vector<std::string> &target, const std::vector<std::string> &continuation)
    {
        if (target.empty() || continuation.empty())
        {
            return;
        }

        if (!target.back().empty())
        {
            target.back() += '\n';
        }

        target.back() += continuation.front();

        for (size_t index = 1; index < continuation.size(); ++index)
        {
            target.push_back(continuation[index]);
        }
    };

    for (const std::vector<std::string> &row : rows)
    {
        uint32_t id = 0;
        const bool startsNewGreeting = !row.empty() && parseUnsigned(row[0], id);

        if (startsNewGreeting)
        {
            appendPendingRow(pendingRow);
            pendingRow = row;
            continue;
        }

        appendContinuationRow(pendingRow, row);
    }

    appendPendingRow(pendingRow);
    return !m_greetings.empty();
}

bool NpcDialogTable::loadNewsFromRows(const std::vector<std::vector<std::string>> &rows)
{
    m_newsTopics.clear();
    m_newsTexts.clear();

    for (const std::vector<std::string> &row : rows)
    {
        if (row.size() <= 1)
        {
            continue;
        }

        uint32_t id = 0;

        if (!parseUnsigned(row[0], id))
        {
            continue;
        }

        m_newsTexts[id] = row[1];
        if (row.size() > 2)
        {
            m_newsTopics[id] = row[2];
        }
    }

    return !m_newsTexts.empty();
}

bool NpcDialogTable::loadGroupNewsFromRows(const std::vector<std::vector<std::string>> &rows)
{
    m_groupNewsIds.clear();

    for (const std::vector<std::string> &row : rows)
    {
        if (row.size() <= 1)
        {
            continue;
        }

        uint32_t groupId = 0;
        uint32_t newsId = 0;

        if (!parseUnsigned(row[0], groupId) || !parseUnsigned(row[1], newsId))
        {
            continue;
        }

        m_groupNewsIds[groupId] = newsId;
    }

    return !m_groupNewsIds.empty();
}

bool NpcDialogTable::loadTextsFromRows(const std::vector<std::vector<std::string>> &rows)
{
    m_texts.clear();

    for (const std::vector<std::string> &row : rows)
    {
        if (row.size() <= 1)
        {
            continue;
        }

        uint32_t id = 0;

        if (!parseUnsigned(row[0], id))
        {
            continue;
        }

        m_texts[id] = row[1];
    }

    return !m_texts.empty();
}

bool NpcDialogTable::loadTopicsFromRows(const std::vector<std::vector<std::string>> &rows)
{
    m_topicsById.clear();
    m_rosterJoinOffersByTopicId.clear();
    m_guildMembershipOffersByTopicId.clear();

    for (const std::vector<std::string> &row : rows)
    {
        if (row.size() <= 5)
        {
            continue;
        }

        uint32_t id = 0;

        if (!parseUnsigned(row[0], id))
        {
            continue;
        }

        NpcTopicEntry entry = {};
        entry.id = id;
        entry.topic = row[1];
        entry.notes = row.size() > 3 ? row[3] : "";
        entry.owner = row.size() > 5 ? row[5] : "";

        uint32_t textId = 0;

        if (parseLeadingUnsigned(row[4], textId))
        {
            entry.textId = textId;
        }

        entry.specialKind = isTeacherHintTopicRow(row)
            ? NpcTopicEntry::SpecialKind::TextOnly
            : NpcTopicEntry::SpecialKind::None;

        m_topicsById[entry.id] = std::move(entry);
    }

    return !m_topicsById.empty();
}

void NpcDialogTable::resolveSpecialTopics(const RosterTable &rosterTable)
{
    m_rosterJoinOffersByTopicId.clear();
    m_guildMembershipOffersByTopicId.clear();

    for (auto &[topicId, entry] : m_topicsById)
    {
        if (entry.specialKind != NpcTopicEntry::SpecialKind::TextOnly)
        {
            entry.specialKind = NpcTopicEntry::SpecialKind::None;
        }

        const std::optional<RosterJoinOffer> rosterJoinOffer = buildRosterJoinOffer(entry, rosterTable, m_texts);

        if (rosterJoinOffer)
        {
            entry.specialKind = NpcTopicEntry::SpecialKind::RosterJoinOffer;
            entry.topic = "Join";
            m_rosterJoinOffersByTopicId[topicId] = *rosterJoinOffer;
            continue;
        }

        const std::optional<GuildMembershipOffer> guildMembershipOffer = buildGuildMembershipOffer(topicId);

        if (guildMembershipOffer)
        {
            entry.specialKind = NpcTopicEntry::SpecialKind::GuildMembershipOffer;
            m_guildMembershipOffersByTopicId[topicId] = *guildMembershipOffer;
        }
    }
}

bool NpcDialogTable::loadNpcRows(const std::vector<std::vector<std::string>> &rows)
{
    m_npcs.clear();

    for (const std::vector<std::string> &row : rows)
    {
        if (row.size() <= 15)
        {
            continue;
        }

        uint32_t id = 0;

        if (!parseUnsigned(row[0], id))
        {
            continue;
        }

        NpcEntry entry = {};
        entry.id = id;
        entry.name = row[1];

        if (entry.name == "Boob")
        {
            continue;
        }

        uint32_t pictureId = 0;

        if (parseUnsigned(row[2], pictureId))
        {
            entry.pictureId = pictureId;
        }

        uint32_t houseId = 0;

        if (parseUnsigned(row[6], houseId))
        {
            entry.houseId = houseId;
        }

        uint32_t professionId = 0;

        if (parseUnsigned(row[7], professionId))
        {
            entry.professionId = professionId;
        }

        uint32_t greetId = 0;

        if (parseUnsigned(row[8], greetId))
        {
            entry.greetId = greetId;
        }

        entry.joins = parseJoinFlag(row[9]);

        for (size_t topicColumn = 10; topicColumn <= 15 && topicColumn < row.size(); ++topicColumn)
        {
            uint32_t topicId = 0;

            if (parseUnsigned(row[topicColumn], topicId))
            {
                entry.topicIds.push_back(topicId);
            }
        }

        while (!entry.topicIds.empty() && entry.topicIds.back() == 0)
        {
            entry.topicIds.pop_back();
        }

        m_npcs[entry.id] = std::move(entry);
    }

    return !m_npcs.empty();
}

const NpcEntry *NpcDialogTable::getNpc(uint32_t npcId) const
{
    const std::unordered_map<uint32_t, NpcEntry>::const_iterator npcIt = m_npcs.find(npcId);

    if (npcIt == m_npcs.end())
    {
        return nullptr;
    }

    return &npcIt->second;
}

std::vector<NpcEntry> NpcDialogTable::entries() const
{
    std::vector<NpcEntry> entries;
    entries.reserve(m_npcs.size());

    for (const auto &[npcId, npc] : m_npcs)
    {
        static_cast<void>(npcId);
        entries.push_back(npc);
    }

    std::sort(
        entries.begin(),
        entries.end(),
        [](const NpcEntry &left, const NpcEntry &right)
        {
            return left.id < right.id;
        });

    return entries;
}

const NpcEntry *NpcDialogTable::findNpcByName(const std::string &name) const
{
    const std::string normalizedName = normalizeName(name);

    if (normalizedName.empty())
    {
        return nullptr;
    }

    for (const auto &[npcId, entry] : m_npcs)
    {
        static_cast<void>(npcId);

        if (normalizeName(entry.name) == normalizedName)
        {
            return &entry;
        }
    }

    return nullptr;
}

const NpcGreetingEntry *NpcDialogTable::getGreeting(uint32_t greetingId) const
{
    const std::unordered_map<uint32_t, NpcGreetingEntry>::const_iterator greetingIt = m_greetings.find(greetingId);

    if (greetingIt == m_greetings.end())
    {
        return nullptr;
    }

    return &greetingIt->second;
}

const NpcGreetingEntry *NpcDialogTable::getGreetingForNpc(uint32_t npcId) const
{
    const NpcEntry *pNpc = getNpc(npcId);

    if (pNpc == nullptr || pNpc->greetId == 0)
    {
        return nullptr;
    }

    return getGreeting(pNpc->greetId);
}

std::vector<NpcDialogTable::ResolvedTopic> NpcDialogTable::getTopicsForNpc(
    uint32_t npcId,
    const std::unordered_map<uint32_t, uint32_t> *pTopicOverrides
) const
{
    std::vector<ResolvedTopic> resolvedTopics;
    const NpcEntry *pNpc = getNpc(npcId);

    if (pNpc == nullptr)
    {
        return resolvedTopics;
    }

    size_t topicSlotCount = pNpc->topicIds.size();

    if (pTopicOverrides != nullptr)
    {
        for (const auto &[topicSlotIndex, overriddenTopicId] : *pTopicOverrides)
        {
            (void)overriddenTopicId;
            topicSlotCount = std::max(topicSlotCount, static_cast<size_t>(topicSlotIndex) + 1);
        }
    }

    for (size_t topicSlotIndex = 0; topicSlotIndex < topicSlotCount; ++topicSlotIndex)
    {
        uint32_t topicId = topicSlotIndex < pNpc->topicIds.size() ? pNpc->topicIds[topicSlotIndex] : 0;

        if (pTopicOverrides != nullptr)
        {
            const std::unordered_map<uint32_t, uint32_t>::const_iterator overrideIt =
                pTopicOverrides->find(static_cast<uint32_t>(topicSlotIndex));

            if (overrideIt != pTopicOverrides->end())
            {
                topicId = overrideIt->second;
            }
        }

        if (topicId == 0)
        {
            continue;
        }

        const std::unordered_map<uint32_t, NpcTopicEntry>::const_iterator topicIt = m_topicsById.find(topicId);

        if (topicIt == m_topicsById.end())
        {
            continue;
        }

        ResolvedTopic resolvedTopic = {};
        resolvedTopic.id = topicIt->second.id;
        resolvedTopic.textId = topicIt->second.textId;
        resolvedTopic.topic = topicIt->second.topic;
        resolvedTopic.specialKind = topicIt->second.specialKind;
        const uint32_t effectiveTextId = topicIt->second.textId != 0 ? topicIt->second.textId : topicIt->second.id;
        const std::unordered_map<uint32_t, std::string>::const_iterator textIt = m_texts.find(effectiveTextId);

        if (textIt != m_texts.end())
        {
            resolvedTopic.text = textIt->second;
        }

        resolvedTopics.push_back(std::move(resolvedTopic));
    }

    return resolvedTopics;
}

std::optional<std::string> NpcDialogTable::getText(uint32_t textId) const
{
    const std::unordered_map<uint32_t, std::string>::const_iterator textIt = m_texts.find(textId);

    if (textIt == m_texts.end())
    {
        return std::nullopt;
    }

    return textIt->second;
}

std::vector<uint32_t> NpcDialogTable::getNpcIdsForHouse(
    uint32_t houseId,
    const std::unordered_map<uint32_t, uint32_t> *pHouseOverrides
) const
{
    std::vector<uint32_t> npcIds;

    for (const auto &[npcId, npc] : m_npcs)
    {
        uint32_t effectiveHouseId = npc.houseId;

        if (pHouseOverrides != nullptr)
        {
            const auto overrideIt = pHouseOverrides->find(npcId);

            if (overrideIt != pHouseOverrides->end())
            {
                effectiveHouseId = overrideIt->second;
            }
        }

        if (effectiveHouseId == houseId)
        {
            npcIds.push_back(npcId);
        }
    }

    std::sort(npcIds.begin(), npcIds.end());
    return npcIds;
}

std::optional<std::string> NpcDialogTable::getNewsText(uint32_t newsId) const
{
    const std::unordered_map<uint32_t, std::string>::const_iterator newsIt = m_newsTexts.find(newsId);

    if (newsIt == m_newsTexts.end())
    {
        return std::nullopt;
    }

    return newsIt->second;
}

std::optional<std::string> NpcDialogTable::getNewsTopic(uint32_t newsId) const
{
    const std::unordered_map<uint32_t, std::string>::const_iterator topicIt = m_newsTopics.find(newsId);

    if (topicIt == m_newsTopics.end())
    {
        return std::nullopt;
    }

    return topicIt->second;
}

std::optional<std::string> NpcDialogTable::getNewsDialogText(uint32_t textId) const
{
    const std::optional<std::string> newsText = getNewsText(textId);

    if (newsText)
    {
        return newsText;
    }

    return getText(textId);
}

std::optional<uint32_t> NpcDialogTable::getNewsIdForGroup(uint32_t groupId) const
{
    const std::unordered_map<uint32_t, uint32_t>::const_iterator groupIt = m_groupNewsIds.find(groupId);

    if (groupIt == m_groupNewsIds.end())
    {
        return std::nullopt;
    }

    return groupIt->second;
}

std::optional<NpcDialogTable::RosterJoinOffer> NpcDialogTable::getRosterJoinOfferForTopic(uint32_t topicId) const
{
    const std::unordered_map<uint32_t, RosterJoinOffer>::const_iterator offerIt =
        m_rosterJoinOffersByTopicId.find(topicId);

    if (offerIt != m_rosterJoinOffersByTopicId.end())
    {
        return offerIt->second;
    }

    return std::nullopt;
}

std::optional<NpcDialogTable::GuildMembershipOffer> NpcDialogTable::getGuildMembershipOfferForTopic(
    uint32_t topicId) const
{
    const std::unordered_map<uint32_t, GuildMembershipOffer>::const_iterator offerIt =
        m_guildMembershipOffersByTopicId.find(topicId);

    if (offerIt != m_guildMembershipOffersByTopicId.end())
    {
        return offerIt->second;
    }

    return std::nullopt;
}

std::optional<NpcDialogTable::ResolvedTopic> NpcDialogTable::getTopicById(uint32_t topicId) const
{
    const std::unordered_map<uint32_t, NpcTopicEntry>::const_iterator topicIt = m_topicsById.find(topicId);

    if (topicIt == m_topicsById.end())
    {
        return std::nullopt;
    }

    ResolvedTopic topic = {};
    topic.id = topicIt->second.id;
    topic.textId = topicIt->second.textId;
    topic.topic = topicIt->second.topic;
    topic.specialKind = topicIt->second.specialKind;
    const uint32_t effectiveTextId = topicIt->second.textId != 0 ? topicIt->second.textId : topicIt->second.id;
    const std::unordered_map<uint32_t, std::string>::const_iterator textIt = m_texts.find(effectiveTextId);

    if (textIt != m_texts.end())
    {
        topic.text = textIt->second;
    }

    return topic;
}
}
