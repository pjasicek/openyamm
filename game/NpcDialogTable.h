#pragma once

#include <cstdint>
#include <optional>
#include <string>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Game
{
struct NpcGreetingEntry
{
    uint32_t id = 0;
    std::string greetingPrimary;
    std::string greetingSecondary;
    std::string owner;
};

struct NpcTopicEntry
{
    enum class SpecialKind
    {
        None,
        RosterJoinOffer,
        MasteryTeacherOffer,
    };

    uint32_t id = 0;
    std::string topic;
    uint32_t textId = 0;
    std::string owner;
    SpecialKind specialKind = SpecialKind::None;
};

struct NpcEntry
{
    uint32_t id = 0;
    std::string name;
    uint32_t pictureId = 0;
    uint32_t houseId = 0;
    uint32_t greetId = 0;
    std::vector<uint32_t> topicIds;
};

class NpcDialogTable
{
public:
    struct ResolvedTopic
    {
        uint32_t id = 0;
        std::string topic;
        std::string text;
        NpcTopicEntry::SpecialKind specialKind = NpcTopicEntry::SpecialKind::None;
    };

    struct RosterJoinOffer
    {
        uint32_t topicId = 0;
        uint32_t rosterId = 0;
        uint32_t inviteTextId = 0;
        uint32_t partyFullTextId = 0;
    };

    bool loadGreetingsFromRows(const std::vector<std::vector<std::string>> &rows);
    bool loadNewsFromRows(const std::vector<std::vector<std::string>> &rows);
    bool loadGroupNewsFromRows(const std::vector<std::vector<std::string>> &rows);
    bool loadTextsFromRows(const std::vector<std::vector<std::string>> &rows);
    bool loadTopicsFromRows(const std::vector<std::vector<std::string>> &rows);
    bool loadNpcRows(const std::vector<std::vector<std::string>> &rows);

    const NpcEntry *getNpc(uint32_t npcId) const;
    const NpcGreetingEntry *getGreetingForNpc(uint32_t npcId) const;
    std::vector<ResolvedTopic> getTopicsForNpc(
        uint32_t npcId,
        const std::unordered_map<uint32_t, uint32_t> *pTopicOverrides = nullptr
    ) const;
    std::vector<uint32_t> getNpcIdsForHouse(
        uint32_t houseId,
        const std::unordered_map<uint32_t, uint32_t> *pHouseOverrides = nullptr
    ) const;
    std::optional<std::string> getText(uint32_t textId) const;
    std::optional<std::string> getNewsText(uint32_t newsId) const;
    std::optional<uint32_t> getNewsIdForGroup(uint32_t groupId) const;
    std::optional<RosterJoinOffer> getRosterJoinOfferForTopic(uint32_t topicId) const;
    std::optional<ResolvedTopic> getTopicById(uint32_t topicId) const;

private:
    std::unordered_map<uint32_t, NpcEntry> m_npcs;
    std::unordered_map<uint32_t, NpcGreetingEntry> m_greetings;
    std::unordered_map<uint32_t, NpcTopicEntry> m_topicsById;
    std::unordered_map<uint32_t, std::string> m_texts;
    std::unordered_map<uint32_t, std::string> m_newsTexts;
    std::unordered_map<uint32_t, uint32_t> m_groupNewsIds;
};
}
