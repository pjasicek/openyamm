#include "game/NpcDialogTable.h"

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
}

bool NpcDialogTable::loadGreetingsFromRows(const std::vector<std::vector<std::string>> &rows)
{
    m_greetings.clear();

    for (const std::vector<std::string> &row : rows)
    {
        if (row.size() <= 4)
        {
            continue;
        }

        uint32_t id = 0;

        if (!parseUnsigned(row[0], id))
        {
            continue;
        }

        NpcGreetingEntry entry = {};
        entry.id = id;
        entry.greetingPrimary = row[1];
        entry.greetingSecondary = row[2];
        entry.owner = row[4];
        m_greetings[id] = std::move(entry);
    }

    return !m_greetings.empty();
}

bool NpcDialogTable::loadNewsFromRows(const std::vector<std::vector<std::string>> &rows)
{
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
        entry.owner = row[5];

        if (entry.topic == "Roster Join Event")
        {
            entry.topic = "Join";
            entry.specialKind = NpcTopicEntry::SpecialKind::RosterJoinOffer;
        }

        uint32_t textId = 0;

        if (parseUnsigned(row[4], textId))
        {
            entry.textId = textId;
        }

        m_topicsById[entry.id] = std::move(entry);
    }

    return !m_topicsById.empty();
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

        uint32_t greetId = 0;

        if (parseUnsigned(row[8], greetId))
        {
            entry.greetId = greetId;
        }

        for (size_t topicColumn = 10; topicColumn <= 15 && topicColumn < row.size(); ++topicColumn)
        {
            uint32_t topicId = 0;

            if (parseUnsigned(row[topicColumn], topicId) && topicId != 0)
            {
                entry.topicIds.push_back(topicId);
            }
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

const NpcGreetingEntry *NpcDialogTable::getGreetingForNpc(uint32_t npcId) const
{
    const NpcEntry *pNpc = getNpc(npcId);

    if (pNpc == nullptr || pNpc->greetId == 0)
    {
        return nullptr;
    }

    const std::unordered_map<uint32_t, NpcGreetingEntry>::const_iterator greetingIt = m_greetings.find(pNpc->greetId);

    if (greetingIt == m_greetings.end())
    {
        return nullptr;
    }

    return &greetingIt->second;
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
        resolvedTopic.topic = topicIt->second.topic;
        resolvedTopic.specialKind = topicIt->second.specialKind;

        if (topicIt->second.textId != 0)
        {
            const std::unordered_map<uint32_t, std::string>::const_iterator textIt = m_texts.find(topicIt->second.textId);

            if (textIt != m_texts.end())
            {
                resolvedTopic.text = textIt->second;
            }
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

std::optional<std::string> NpcDialogTable::getNewsText(uint32_t newsId) const
{
    const std::unordered_map<uint32_t, std::string>::const_iterator newsIt = m_newsTexts.find(newsId);

    if (newsIt == m_newsTexts.end())
    {
        return std::nullopt;
    }

    return newsIt->second;
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
    if (topicId == 602)
    {
        RosterJoinOffer offer = {};
        offer.topicId = topicId;
        offer.rosterId = 2;
        offer.inviteTextId = 202;
        offer.partyFullTextId = 203;
        return offer;
    }

    return std::nullopt;
}
}
