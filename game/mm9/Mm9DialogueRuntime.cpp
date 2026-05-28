#include "game/mm9/Mm9DialogueRuntime.h"

#include "game/mm9/Mm9ScriptRuntime.h"
#include "game/party/Party.h"

#include <algorithm>
#include <cctype>
#include <optional>
#include <string>
#include <utility>

namespace OpenYAMM::Game
{
namespace
{
constexpr uint32_t Mm9KeyQbitBase = 9000;

std::string serviceNameForOpcode(const Mm9DialoguePackage &package, int32_t opcode)
{
    const auto serviceIterator = package.services.find(opcode);
    if (serviceIterator != package.services.end())
    {
        return serviceIterator->second.name;
    }

    return {};
}

std::string lowerCopy(const std::string &text)
{
    std::string result = text;
    for (char &ch : result)
    {
        ch = static_cast<char>(std::tolower(static_cast<unsigned char>(ch)));
    }
    return result;
}
}

uint32_t mm9KeyQbitIdForRawKey(int32_t rawKeyId)
{
    if (rawKeyId <= 0)
    {
        return 0;
    }

    return Mm9KeyQbitBase + static_cast<uint32_t>(rawKeyId);
}

bool mm9QbitIdIsKeyMapping(uint32_t qbitId)
{
    return qbitId > Mm9KeyQbitBase;
}

int32_t mm9RawKeyIdForQbit(uint32_t qbitId)
{
    if (!mm9QbitIdIsKeyMapping(qbitId))
    {
        return 0;
    }

    return static_cast<int32_t>(qbitId - Mm9KeyQbitBase);
}

Mm9ServiceKind mm9ServiceKindForOpcode(int32_t opcode)
{
    switch (opcode)
    {
    case -2:
        return Mm9ServiceKind::Shop;
    case -3:
        return Mm9ServiceKind::Training;
    case -4:
        return Mm9ServiceKind::SkillTraining;
    case -5:
        return Mm9ServiceKind::Travel;
    case -6:
        return Mm9ServiceKind::Bank;
    case -7:
        return Mm9ServiceKind::Inn;
    case -8:
        return Mm9ServiceKind::Healer;
    case -10:
        return Mm9ServiceKind::Hire;
    case -11:
        return Mm9ServiceKind::Dismiss;
    case -13:
        return Mm9ServiceKind::ItemCombine;
    case -14:
        return Mm9ServiceKind::QuestHandoff;
    case -15:
        return Mm9ServiceKind::TownPortal;
    case -16:
        return Mm9ServiceKind::Donation;
    default:
        return Mm9ServiceKind::Unknown;
    }
}

std::string mm9ServiceKindName(Mm9ServiceKind kind)
{
    switch (kind)
    {
    case Mm9ServiceKind::Shop:
        return "shop";
    case Mm9ServiceKind::Training:
        return "training";
    case Mm9ServiceKind::SkillTraining:
        return "skill_training";
    case Mm9ServiceKind::Travel:
        return "travel";
    case Mm9ServiceKind::Bank:
        return "bank";
    case Mm9ServiceKind::Inn:
        return "inn";
    case Mm9ServiceKind::Healer:
        return "healer";
    case Mm9ServiceKind::Hire:
        return "hire";
    case Mm9ServiceKind::Dismiss:
        return "dismiss";
    case Mm9ServiceKind::ItemCombine:
        return "item_combine";
    case Mm9ServiceKind::QuestHandoff:
        return "quest_handoff";
    case Mm9ServiceKind::TownPortal:
        return "town_portal";
    case Mm9ServiceKind::Donation:
        return "donation";
    case Mm9ServiceKind::Unknown:
        return "unknown";
    }

    return "unknown";
}

Mm9DialogueRuntime::Mm9DialogueRuntime(const Mm9DialoguePackage &package, Party &party)
    : m_package(package)
    , m_party(party)
{
}

bool Mm9DialogueRuntime::hasKey(int32_t rawKeyId) const
{
    const uint32_t qbitId = qbitIdForRawKey(rawKeyId);
    return qbitId != 0 && m_party.hasQuestBit(qbitId);
}

void Mm9DialogueRuntime::giveKey(int32_t rawKeyId)
{
    const uint32_t qbitId = qbitIdForRawKey(rawKeyId);
    if (qbitId != 0)
    {
        m_party.setQuestBit(qbitId, true);
    }
}

void Mm9DialogueRuntime::takeKey(int32_t rawKeyId)
{
    const uint32_t qbitId = qbitIdForRawKey(rawKeyId);
    if (qbitId != 0)
    {
        m_party.setQuestBit(qbitId, false);
    }
}

bool Mm9DialogueRuntime::enterRudeId(int32_t rudeId, const Mm9DialogueOwnerContext &owner)
{
    const auto dialogueIterator = m_package.npcDialogues.find(rudeId);
    if (dialogueIterator == m_package.npcDialogues.end())
    {
        return false;
    }

    for (const Mm9GeneratedRudeRow &row : dialogueIterator->second.rows)
    {
        if (row.npcId == rudeId && row.nodeId == rudeId)
        {
            m_pDialogue = &dialogueIterator->second;
            m_owner = owner;
            m_currentRudeId = rudeId;
            m_currentNodeId = rudeId;
            m_closed = false;
            return true;
        }
    }

    return false;
}

bool Mm9DialogueRuntime::enterObject(const std::string &mapId, int32_t objectIndex, std::string *pError)
{
    const Mm9GeneratedObjectDialogueBinding *pBinding = objectBindingForObject(mapId, objectIndex);
    if (pBinding == nullptr)
    {
        if (pError != nullptr)
        {
            *pError = "MM9 dialogue binding was not found for selected object";
        }
        return false;
    }

    if (!pBinding->rudeId)
    {
        if (pError != nullptr)
        {
            *pError = "MM9 dialogue binding has no resolved RUDE id";
        }
        return false;
    }

    Mm9DialogueOwnerContext owner = {};
    ownerContextForObject(mapId, objectIndex, owner);

    if (!enterRudeId(*pBinding->rudeId, owner))
    {
        if (pError != nullptr)
        {
            *pError = "MM9 dialogue binding points to a missing generated RUDE dialogue";
        }
        return false;
    }

    return true;
}

bool Mm9DialogueRuntime::ownerContextForObject(
    const std::string &mapId,
    int32_t objectIndex,
    Mm9DialogueOwnerContext &owner,
    std::string *pError) const
{
    const Mm9GeneratedObjectDialogueBinding *pBinding = objectBindingForObject(mapId, objectIndex);
    if (pBinding == nullptr)
    {
        if (pError != nullptr)
        {
            *pError = "MM9 dialogue binding was not found for selected object";
        }
        return false;
    }

    owner = {};
    owner.mapId = pBinding->mapId;
    owner.objectIndex = pBinding->objectIndex;
    owner.objectName = pBinding->objectName;
    owner.scriptName = pBinding->scriptName;
    owner.scriptParams = pBinding->scriptParams;
    owner.greetingSound = pBinding->greetingSound;
    if (!owner.scriptName.empty())
    {
        owner.onRudeExitLabel = onRudeExitLabelForScript(owner.scriptName).value_or("");
    }
    return true;
}

void Mm9DialogueRuntime::setOwnerContext(Mm9DialogueOwnerContext owner)
{
    m_owner = std::move(owner);
}

void Mm9DialogueRuntime::setOnRudeExitLabel(std::string label)
{
    m_owner.onRudeExitLabel = std::move(label);
}

void Mm9DialogueRuntime::bindScriptRuntimeState(const Mm9ScriptRuntimeState *pState)
{
    m_pScriptRuntimeState = pState;
}

int32_t Mm9DialogueRuntime::currentRudeId() const
{
    return m_currentRudeId;
}

int32_t Mm9DialogueRuntime::currentNodeId() const
{
    return m_currentNodeId;
}

bool Mm9DialogueRuntime::closed() const
{
    return m_closed;
}

const Mm9DialogueOwnerContext &Mm9DialogueRuntime::owner() const
{
    return m_owner;
}

Party &Mm9DialogueRuntime::party()
{
    return m_party;
}

const Party &Mm9DialogueRuntime::party() const
{
    return m_party;
}

std::vector<Mm9DialogueTopic> Mm9DialogueRuntime::visibleTopics() const
{
    std::vector<Mm9DialogueTopic> topics;
    if (m_closed || m_pDialogue == nullptr)
    {
        return topics;
    }

    for (size_t rowIndex = 0; rowIndex < m_pDialogue->rows.size(); ++rowIndex)
    {
        const Mm9GeneratedRudeRow &row = m_pDialogue->rows[rowIndex];
        if (row.npcId != m_currentRudeId || row.nodeId != m_currentNodeId || !rowPassesVisibilityConditions(row))
        {
            continue;
        }

        Mm9DialogueTopic topic = {};
        topic.rowIndex = rowIndex;
        topic.sourceRow = row.source.row;
        topic.choiceSlot = row.choiceSlot;
        topic.next = row.next;
        topic.prompt = row.prompt;
        topic.response = row.response;
        topic.rawColumns = row.rawColumns;
        topic.requiredKeys = row.requiredKeys;
        topics.push_back(std::move(topic));
    }

    std::sort(
        topics.begin(),
        topics.end(),
        [](const Mm9DialogueTopic &left, const Mm9DialogueTopic &right)
        {
            if (left.choiceSlot != right.choiceSlot)
            {
                return left.choiceSlot < right.choiceSlot;
            }
            return left.sourceRow < right.sourceRow;
        });

    return topics;
}

Mm9DialogueSelectionResult Mm9DialogueRuntime::selectTopic(size_t visibleTopicIndex)
{
    Mm9DialogueSelectionResult result = {};
    result.owner = m_owner;

    const std::vector<Mm9DialogueTopic> topics = visibleTopics();
    if (visibleTopicIndex >= topics.size())
    {
        return result;
    }

    const Mm9DialogueTopic &topic = topics[visibleTopicIndex];
    result.next = topic.next;
    result.response = topic.response;

    if (topic.next > 0)
    {
        result.kind = Mm9DialogueSelectionKind::GotoNode;
        m_currentNodeId = topic.next;
    }
    else if (topic.next == -1)
    {
        result.kind = Mm9DialogueSelectionKind::Close;
        result.onRudeExitLabel = m_owner.onRudeExitLabel;
        m_closed = true;
    }
    else if (topic.next < -1)
    {
        result.kind = Mm9DialogueSelectionKind::Service;
        result.serviceOpcode = topic.next;
        result.serviceName = serviceNameForOpcode(m_package, topic.next);
        result.serviceRequest = serviceRequestForTopic(topic);
    }
    else
    {
        result.kind = Mm9DialogueSelectionKind::UnresolvedZero;
    }

    return result;
}

bool Mm9DialogueRuntime::dispatchServiceSelection(
    const Mm9DialogueSelectionResult &selection,
    Mm9DialogueServiceHandler &handler) const
{
    if (selection.kind != Mm9DialogueSelectionKind::Service || !selection.serviceRequest)
    {
        return false;
    }

    handler.openService(*selection.serviceRequest);
    return true;
}

const Mm9GeneratedObjectDialogueBinding *Mm9DialogueRuntime::objectBindingForObject(
    const std::string &mapId,
    int32_t objectIndex) const
{
    const auto bindingIterator = std::find_if(
        m_package.objectBindings.begin(),
        m_package.objectBindings.end(),
        [&](const Mm9GeneratedObjectDialogueBinding &binding)
        {
            return binding.mapId == mapId && binding.objectIndex == objectIndex;
        });

    return bindingIterator != m_package.objectBindings.end() ? &*bindingIterator : nullptr;
}

std::optional<Mm9DialogueServiceRequest> Mm9DialogueRuntime::serviceRequestForTopic(
    const Mm9DialogueTopic &topic) const
{
    if (topic.next >= -1)
    {
        return std::nullopt;
    }

    Mm9DialogueServiceRequest request = {};
    request.kind = mm9ServiceKindForOpcode(topic.next);
    request.opcode = topic.next;
    request.name = serviceNameForOpcode(m_package, topic.next);
    if (request.name.empty())
    {
        request.name = mm9ServiceKindName(request.kind);
    }
    request.rudeId = m_currentRudeId;
    request.nodeId = m_currentNodeId;
    request.rowIndex = topic.rowIndex;
    request.sourceRow = topic.sourceRow;
    request.owner = m_owner;
    request.rawColumns = topic.rawColumns;
    return request;
}

uint32_t Mm9DialogueRuntime::qbitIdForRawKey(int32_t rawKeyId) const
{
    if (rawKeyId <= 0)
    {
        return 0;
    }

    const auto keyIterator = m_package.keys.find(rawKeyId);
    if (keyIterator != m_package.keys.end() && keyIterator->second.qbitId > 0)
    {
        return static_cast<uint32_t>(keyIterator->second.qbitId);
    }

    return mm9KeyQbitIdForRawKey(rawKeyId);
}

bool Mm9DialogueRuntime::rowPassesVisibilityConditions(const Mm9GeneratedRudeRow &row) const
{
    for (const Mm9GeneratedRequiredKeyCondition &condition : row.requiredKeys)
    {
        const uint32_t qbitId = condition.qbitId != 0 ? condition.qbitId : qbitIdForRawKey(condition.rawId);
        if (qbitId == 0 || !m_party.hasQuestBit(qbitId))
        {
            return false;
        }
    }

    if (!rowPassesInventoryConditions(row) || !rowPassesConsoleConditions(row))
    {
        return false;
    }

    return true;
}

bool Mm9DialogueRuntime::rowPassesInventoryConditions(const Mm9GeneratedRudeRow &row) const
{
    for (const Mm9GeneratedRequiredItemCondition &condition : row.requiredItems)
    {
        if (condition.itemId == 0 || !m_party.hasItemAnywhere(condition.itemId))
        {
            return false;
        }
    }

    return true;
}

bool Mm9DialogueRuntime::rowPassesConsoleConditions(const Mm9GeneratedRudeRow &row) const
{
    if (!row.requiredConsoleNumEquals.empty() || !row.requiredConsoleStrEquals.empty())
    {
        if (m_pScriptRuntimeState == nullptr)
        {
            return false;
        }
    }

    for (const Mm9GeneratedConsoleNumEqualsCondition &condition : row.requiredConsoleNumEquals)
    {
        const auto valueIterator = m_pScriptRuntimeState->consoleNumVars.find(condition.variable);
        if (valueIterator == m_pScriptRuntimeState->consoleNumVars.end()
            || valueIterator->second != condition.value)
        {
            return false;
        }
    }

    for (const Mm9GeneratedConsoleStrEqualsCondition &condition : row.requiredConsoleStrEquals)
    {
        const auto valueIterator = m_pScriptRuntimeState->consoleStrVars.find(condition.variable);
        if (valueIterator == m_pScriptRuntimeState->consoleStrVars.end()
            || valueIterator->second != condition.value)
        {
            return false;
        }
    }

    return true;
}

std::optional<std::string> Mm9DialogueRuntime::onRudeExitLabelForScript(const std::string &scriptName) const
{
    auto scriptIterator = m_package.scripts.find(scriptName);
    if (scriptIterator == m_package.scripts.end())
    {
        const std::string loweredScriptName = lowerCopy(scriptName);
        scriptIterator = std::find_if(
            m_package.scripts.begin(),
            m_package.scripts.end(),
            [&](const std::pair<const std::string, Mm9GeneratedScriptFile> &scriptPair)
            {
                return lowerCopy(scriptPair.first) == loweredScriptName;
            });
        if (scriptIterator == m_package.scripts.end())
        {
            return std::nullopt;
        }
    }

    for (const Mm9GeneratedScriptCommand &command : scriptIterator->second.commands)
    {
        if (command.name == "onrudeexit" && !command.argumentsText.empty())
        {
            return command.argumentsText;
        }
    }

    return std::nullopt;
}
}
