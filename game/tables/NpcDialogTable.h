#pragma once

#include <cstdint>
#include <optional>
#include <string>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Game
{
class MergedNpcProfessionTable;
class RosterTable;

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
        TextOnly,
        RosterJoinOffer,
        MasteryTeacherOffer,
        GuildMembershipOffer,
    };

    uint32_t id = 0;
    uint32_t textId = 0;
    std::string topic;
    std::string notes;
    std::string owner;
    SpecialKind specialKind = SpecialKind::None;
};

struct NpcEntry
{
    uint32_t id = 0;
    std::string name;
    uint32_t pictureId = 0;
    uint32_t houseId = 0;
    uint32_t professionId = 0;
    uint32_t greetId = 0;
    bool joins = false;
    std::vector<uint32_t> topicIds;
    // npc.txt's optional "Title" column after Notes (a world's rows): a talk reads "{name}, {title}". Empty: the
    // profession's "{name} the {profession}", or the name.
    std::string title;
};

// An NPC as its talk's title names it, localized: "{name}, {title}" with a title, else the profession's
// "{name} the {profession}" (the original NameAndTitle), else the name. Empty for an NPC without a name.
std::string npcNameAndTitle(const NpcEntry &npc, const MergedNpcProfessionTable *pProfessionTable);

class NpcDialogTable
{
public:
    struct ResolvedTopic
    {
        uint32_t id = 0;
        uint32_t textId = 0;
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

    struct GuildMembershipOffer
    {
        uint32_t topicId = 0;
        uint32_t guildType = 0;
        uint32_t cost = 0;
        uint32_t descriptionTextId = 0;
        uint32_t joinTextId = 0;
        uint32_t autonoteId = 0;
    };

    bool loadGreetingsFromRows(const std::vector<std::vector<std::string>> &rows);
    bool loadNewsFromRows(const std::vector<std::vector<std::string>> &rows);
    bool loadGroupNewsFromRows(const std::vector<std::vector<std::string>> &rows);
    bool loadTextsFromRows(const std::vector<std::vector<std::string>> &rows);
    bool loadTopicsFromRows(const std::vector<std::vector<std::string>> &rows);
    bool loadNpcRows(const std::vector<std::vector<std::string>> &rows);
    void resolveSpecialTopics(const RosterTable &rosterTable);

    const NpcEntry *getNpc(uint32_t npcId) const;
    const NpcEntry *findNpcByName(const std::string &name) const;
    const NpcGreetingEntry *getGreeting(uint32_t greetingId) const;
    const NpcGreetingEntry *getGreetingForNpc(uint32_t npcId) const;
    std::vector<ResolvedTopic> getTopicsForNpc(
        uint32_t npcId,
        const std::unordered_map<uint32_t, uint32_t> *pTopicOverrides = nullptr
    ) const;
    std::vector<uint32_t> getNpcIdsForHouse(
        uint32_t houseId,
        const std::unordered_map<uint32_t, uint32_t> *pHouseOverrides = nullptr
    ) const;
    // Houses where an NPC is present besides its own (a ruleset's, MAW's moved teachers), by NPC id.
    void setExtraHouses(std::unordered_map<uint32_t, std::vector<uint32_t>> extraHouses);
    const std::unordered_map<uint32_t, std::vector<uint32_t>> &extraHouses() const;
    std::optional<std::string> getText(uint32_t textId) const;
    std::optional<std::string> getNewsTopic(uint32_t newsId) const;
    std::optional<std::string> getNewsText(uint32_t newsId) const;
    std::optional<std::string> getNewsDialogText(uint32_t textId) const;
    // A street group's news by npc_group.txt; none in a world that turns the engine's group news off.
    std::optional<uint32_t> getNewsIdForGroup(uint32_t groupId) const;
    // Whether npc_group.txt's group news applies (world.yml streetNpcGroupNews, set on each world switch).
    void setGroupNewsDefaults(bool enabled);
    // An MMerge filler row of npc_news.txt rather than a line to say: "Group <n>" or the empty "Default change me
    // text" row (51) that many imported MM6/MM7 groups point at.
    bool isPlaceholderNews(uint32_t newsId) const;
    std::optional<RosterJoinOffer> getRosterJoinOfferForTopic(uint32_t topicId) const;
    std::optional<GuildMembershipOffer> getGuildMembershipOfferForTopic(uint32_t topicId) const;
    std::optional<ResolvedTopic> getTopicById(uint32_t topicId) const;
    std::vector<NpcEntry> entries() const;

private:
    std::unordered_map<uint32_t, RosterJoinOffer> m_rosterJoinOffersByTopicId;
    std::unordered_map<uint32_t, GuildMembershipOffer> m_guildMembershipOffersByTopicId;
    std::unordered_map<uint32_t, NpcEntry> m_npcs;
    std::unordered_map<uint32_t, std::vector<uint32_t>> m_extraHouses;
    std::unordered_map<uint32_t, NpcGreetingEntry> m_greetings;
    std::unordered_map<uint32_t, NpcTopicEntry> m_topicsById;
    std::unordered_map<uint32_t, std::string> m_texts;
    std::unordered_map<uint32_t, std::string> m_newsTopics;
    std::unordered_map<uint32_t, std::string> m_newsTexts;
    std::unordered_map<uint32_t, uint32_t> m_groupNewsIds;
    bool m_groupNewsDefaults = true;
};
}
