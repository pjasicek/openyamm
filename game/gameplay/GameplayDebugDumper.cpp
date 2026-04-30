#include "game/gameplay/GameplayDebugDumper.h"

#include "game/app/GameSession.h"
#include "game/data/GameDataRepository.h"
#include "game/events/EvtEnums.h"
#include "game/events/EventRuntime.h"
#include "game/gameplay/GameplayRuntimeInterfaces.h"
#include "game/outdoor/OutdoorWorldRuntime.h"
#include "game/party/Party.h"
#include "game/scene/SceneKind.h"
#include "game/tables/HouseTable.h"
#include "game/tables/JournalQuestTable.h"
#include "game/tables/NpcDialogTable.h"

#include <algorithm>
#include <cstdint>
#include <iostream>
#include <optional>
#include <sstream>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <utility>
#include <vector>

namespace OpenYAMM::Game
{
namespace
{
std::vector<uint32_t> sortedIdsFromSet(const std::unordered_set<uint32_t> &ids)
{
    std::vector<uint32_t> sortedIds(ids.begin(), ids.end());
    std::sort(sortedIds.begin(), sortedIds.end());
    return sortedIds;
}

std::string joinIds(const std::vector<uint32_t> &ids)
{
    std::ostringstream stream;

    for (size_t index = 0; index < ids.size(); ++index)
    {
        if (index > 0)
        {
            stream << ',';
        }

        stream << ids[index];
    }

    return stream.str();
}

std::string sceneKindName(SceneKind sceneKind)
{
    switch (sceneKind)
    {
        case SceneKind::Outdoor:
            return "outdoor";
        case SceneKind::Indoor:
            return "indoor";
    }

    return "unknown";
}

std::string quoteIfPresent(const std::string &text)
{
    return text.empty() ? std::string() : " \"" + text + '"';
}

std::optional<std::string> questLabel(const GameDataRepository *pData, uint32_t qbitId)
{
    if (pData == nullptr)
    {
        return std::nullopt;
    }

    for (const JournalQuestEntry &entry : pData->journalQuestTable().entries())
    {
        if (entry.qbitId != qbitId)
        {
            continue;
        }

        if (!entry.text.empty() && !entry.notes.empty())
        {
            return entry.text + " - " + entry.notes;
        }

        if (!entry.text.empty())
        {
            return entry.text;
        }

        if (!entry.notes.empty())
        {
            return entry.notes;
        }

        return std::nullopt;
    }

    return std::nullopt;
}

std::string npcLabel(const GameDataRepository *pData, uint32_t npcId)
{
    if (pData == nullptr)
    {
        return {};
    }

    const NpcEntry *pNpc = pData->npcDialogTable().getNpc(npcId);
    return pNpc != nullptr ? quoteIfPresent(pNpc->name) : std::string();
}

std::string houseLabel(const GameDataRepository *pData, uint32_t houseId)
{
    if (houseId == 0)
    {
        return " <none>";
    }

    if (pData == nullptr)
    {
        return {};
    }

    const std::optional<std::string> name = pData->houseTable().getName(houseId);
    return name.has_value() ? quoteIfPresent(*name) : std::string();
}

std::vector<std::pair<uint32_t, uint32_t>> sortedPairs(const std::unordered_map<uint32_t, uint32_t> &values)
{
    std::vector<std::pair<uint32_t, uint32_t>> pairs(values.begin(), values.end());
    std::sort(
        pairs.begin(),
        pairs.end(),
        [](const std::pair<uint32_t, uint32_t> &left, const std::pair<uint32_t, uint32_t> &right)
        {
            return left.first < right.first;
        });
    return pairs;
}

void collectRuntimeSelectorIds(
    const EventRuntimeState &runtimeState,
    EvtVariable variableKind,
    std::vector<uint32_t> &ids)
{
    ids.clear();

    for (const std::pair<const uint32_t, int32_t> &entry : runtimeState.variables)
    {
        if (entry.second == 0)
        {
            continue;
        }

        const uint16_t tag = static_cast<uint16_t>(entry.first & 0xFFFFu);
        if (tag == static_cast<uint16_t>(variableKind))
        {
            ids.push_back(entry.first >> 16);
        }
    }

    std::sort(ids.begin(), ids.end());
}

void dumpQBits(const Party *pParty, const EventRuntimeState *pRuntimeState, const GameDataRepository *pData)
{
    std::vector<uint32_t> qbits;

    if (pParty != nullptr)
    {
        const Party::Snapshot snapshot = pParty->snapshot();
        qbits = sortedIdsFromSet(snapshot.questBits);
        std::cout << "F5 QBits set count=" << qbits.size() << " ids=" << joinIds(qbits) << '\n';
    }
    else if (pRuntimeState != nullptr)
    {
        collectRuntimeSelectorIds(*pRuntimeState, EvtVariable::QBits, qbits);
        std::cout << "F5 QBits set count=" << qbits.size() << " ids=" << joinIds(qbits)
                  << " source=runtimeVars\n";
    }
    else
    {
        std::cout << "F5 QBits set party=missing runtime=missing\n";
        return;
    }

    for (uint32_t qbitId : qbits)
    {
        const std::optional<std::string> label = questLabel(pData, qbitId);
        if (label.has_value())
        {
            std::cout << "  QBit " << qbitId << ": " << *label << '\n';
        }
    }
}

void dumpAwards(const Party *pParty, const EventRuntimeState *pRuntimeState)
{
    if (pParty != nullptr)
    {
        std::unordered_set<uint32_t> awardUnion;

        for (const Character &member : pParty->members())
        {
            for (uint32_t awardId : member.awards)
            {
                awardUnion.insert(awardId);
            }
        }

        const std::vector<uint32_t> awardIds = sortedIdsFromSet(awardUnion);
        std::cout << "F5 Awards set unique.count=" << awardIds.size() << " ids=" << joinIds(awardIds) << '\n';

        for (size_t memberIndex = 0; memberIndex < pParty->members().size(); ++memberIndex)
        {
            const Character &member = pParty->members()[memberIndex];
            const std::vector<uint32_t> memberAwards = sortedIdsFromSet(member.awards);
            std::cout << "  member=" << memberIndex
                      << " name=\"" << member.name << '"'
                      << " awards.count=" << memberAwards.size()
                      << " ids=" << joinIds(memberAwards)
                      << '\n';
        }

        return;
    }

    if (pRuntimeState != nullptr)
    {
        std::vector<uint32_t> runtimeAwards;
        collectRuntimeSelectorIds(*pRuntimeState, EvtVariable::Awards, runtimeAwards);
        std::cout << "F5 Awards set count=" << runtimeAwards.size() << " ids=" << joinIds(runtimeAwards)
                  << " source=runtimeVars\n";
        return;
    }

    std::cout << "F5 Awards set party=missing runtime=missing\n";
}

void dumpNpcOverrides(const EventRuntimeState *pRuntimeState, const GameDataRepository *pData)
{
    if (pRuntimeState == nullptr)
    {
        std::cout << "F5 Runtime NPC overrides runtime=missing\n";
        return;
    }

    const std::vector<std::pair<uint32_t, uint32_t>> houseOverrides = sortedPairs(pRuntimeState->npcHouseOverrides);
    std::cout << "F5 Runtime MoveNPC npcHouseOverrides count=" << houseOverrides.size() << '\n';

    for (const std::pair<uint32_t, uint32_t> &entry : houseOverrides)
    {
        std::cout << "  MoveNPC npc=" << entry.first << npcLabel(pData, entry.first)
                  << " house=" << entry.second << houseLabel(pData, entry.second)
                  << '\n';
    }

    const std::vector<std::pair<uint32_t, uint32_t>> greetingOverrides =
        sortedPairs(pRuntimeState->npcGreetingOverrides);
    std::cout << "F5 Runtime SetNPCGreeting overrides count=" << greetingOverrides.size() << '\n';

    for (const std::pair<uint32_t, uint32_t> &entry : greetingOverrides)
    {
        std::cout << "  SetNPCGreeting npc=" << entry.first << npcLabel(pData, entry.first)
                  << " greeting=" << entry.second << '\n';
    }

    std::vector<uint32_t> topicNpcIds;
    topicNpcIds.reserve(pRuntimeState->npcTopicOverrides.size());

    for (const std::pair<const uint32_t, std::unordered_map<uint32_t, uint32_t>> &entry :
         pRuntimeState->npcTopicOverrides)
    {
        topicNpcIds.push_back(entry.first);
    }

    std::sort(topicNpcIds.begin(), topicNpcIds.end());
    std::cout << "F5 Runtime SetNPCTopic overrides npc.count=" << topicNpcIds.size() << '\n';

    for (uint32_t npcId : topicNpcIds)
    {
        const std::unordered_map<uint32_t, uint32_t> &slotOverrides = pRuntimeState->npcTopicOverrides.at(npcId);
        const std::vector<std::pair<uint32_t, uint32_t>> sortedSlotOverrides = sortedPairs(slotOverrides);

        for (const std::pair<uint32_t, uint32_t> &entry : sortedSlotOverrides)
        {
            std::cout << "  SetNPCTopic npc=" << npcId << npcLabel(pData, npcId)
                      << " slot=" << entry.first
                      << " topic=" << entry.second;

            if (pData != nullptr)
            {
                const std::optional<NpcDialogTable::ResolvedTopic> topic =
                    pData->npcDialogTable().getTopicById(entry.second);
                if (topic.has_value())
                {
                    std::cout << quoteIfPresent(topic->topic);
                }
            }

            std::cout << '\n';
        }
    }

    const std::vector<std::pair<uint32_t, uint32_t>> newsOverrides = sortedPairs(pRuntimeState->npcGroupNews);
    std::cout << "F5 Runtime SetNPCGroupNews overrides count=" << newsOverrides.size() << '\n';

    for (const std::pair<uint32_t, uint32_t> &entry : newsOverrides)
    {
        std::cout << "  SetNPCGroupNews group=" << entry.first << " news=" << entry.second << '\n';
    }
}
} // namespace

void GameplayDebugDumper::dumpStateToConsole(const GameSession &session)
{
    const IGameplayWorldRuntime *pWorldRuntime = session.activeWorldRuntime();
    const Party *pParty = pWorldRuntime != nullptr ? pWorldRuntime->party() : nullptr;
    const EventRuntimeState *pRuntimeState = pWorldRuntime != nullptr ? pWorldRuntime->eventRuntimeState() : nullptr;
    EventRuntimeState effectiveRuntimeState = pRuntimeState != nullptr ? *pRuntimeState : EventRuntimeState();
    const EventRuntimeState *pEffectiveRuntimeState = pRuntimeState;

    if (pParty != nullptr)
    {
        pParty->applyGlobalNpcStateTo(effectiveRuntimeState);
        pEffectiveRuntimeState = &effectiveRuntimeState;
    }

    const GameDataRepository *pData = session.hasDataRepository() ? &session.data() : nullptr;

    std::cout << "F5 gameplay state dump"
              << " scene=" << sceneKindName(session.currentSceneKind());

    if (session.hasCurrentMapFileName())
    {
        std::cout << " map=\"" << session.currentMapFileName() << '"';
    }

    std::cout << '\n';

    dumpQBits(pParty, pRuntimeState, pData);
    dumpAwards(pParty, pRuntimeState);
    dumpNpcOverrides(pEffectiveRuntimeState, pData);

    if (const OutdoorWorldRuntime *pOutdoorWorldRuntime = dynamic_cast<const OutdoorWorldRuntime *>(pWorldRuntime))
    {
        pOutdoorWorldRuntime->dumpDebugFacetCogStateToConsole(25);
        pOutdoorWorldRuntime->dumpDebugFacetCogStateToConsole(26);
    }

    std::cout << "F5 gameplay state dump end\n";
}
} // namespace OpenYAMM::Game
