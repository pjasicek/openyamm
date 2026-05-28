#pragma once

#include "game/mm9/Mm9DialoguePackage.h"

#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
class Party;
struct Mm9ScriptRuntimeState;

struct Mm9DialogueOwnerContext
{
    std::string mapId;
    int32_t objectIndex = -1;
    std::string objectName;
    std::string scriptName;
    std::vector<std::string> scriptParams;
    std::string greetingSound;
    std::string onRudeExitLabel;
};

struct Mm9DialogueTopic
{
    size_t rowIndex = 0;
    size_t sourceRow = 0;
    int32_t choiceSlot = 0;
    int32_t next = 0;
    std::string prompt;
    std::string response;
    std::vector<std::string> rawColumns;
    std::vector<Mm9GeneratedRequiredKeyCondition> requiredKeys;
};

enum class Mm9DialogueSelectionKind
{
    None,
    GotoNode,
    Close,
    Service,
    UnresolvedZero,
};

enum class Mm9ServiceKind
{
    Unknown,
    Shop,
    Training,
    SkillTraining,
    Travel,
    Bank,
    Inn,
    Healer,
    Hire,
    Dismiss,
    ItemCombine,
    QuestHandoff,
    TownPortal,
    Donation,
};

struct Mm9DialogueServiceRequest
{
    Mm9ServiceKind kind = Mm9ServiceKind::Unknown;
    int32_t opcode = 0;
    std::string name;
    int32_t rudeId = 0;
    int32_t nodeId = 0;
    size_t rowIndex = 0;
    size_t sourceRow = 0;
    Mm9DialogueOwnerContext owner;
    std::vector<std::string> rawColumns;
};

struct Mm9DialogueSelectionResult
{
    Mm9DialogueSelectionKind kind = Mm9DialogueSelectionKind::None;
    int32_t next = 0;
    int32_t serviceOpcode = 0;
    std::string serviceName;
    std::string response;
    std::string onRudeExitLabel;
    Mm9DialogueOwnerContext owner;
    std::optional<Mm9DialogueServiceRequest> serviceRequest;
};

class Mm9DialogueServiceHandler
{
public:
    virtual ~Mm9DialogueServiceHandler() = default;
    virtual void openService(const Mm9DialogueServiceRequest &request) = 0;
};

uint32_t mm9KeyQbitIdForRawKey(int32_t rawKeyId);
bool mm9QbitIdIsKeyMapping(uint32_t qbitId);
int32_t mm9RawKeyIdForQbit(uint32_t qbitId);
Mm9ServiceKind mm9ServiceKindForOpcode(int32_t opcode);
std::string mm9ServiceKindName(Mm9ServiceKind kind);

class Mm9DialogueRuntime
{
public:
    Mm9DialogueRuntime(const Mm9DialoguePackage &package, Party &party);

    bool hasKey(int32_t rawKeyId) const;
    void giveKey(int32_t rawKeyId);
    void takeKey(int32_t rawKeyId);

    bool enterRudeId(int32_t rudeId, const Mm9DialogueOwnerContext &owner = {});
    bool enterObject(const std::string &mapId, int32_t objectIndex, std::string *pError = nullptr);
    bool ownerContextForObject(
        const std::string &mapId,
        int32_t objectIndex,
        Mm9DialogueOwnerContext &owner,
        std::string *pError = nullptr) const;
    void setOwnerContext(Mm9DialogueOwnerContext owner);
    void setOnRudeExitLabel(std::string label);
    void bindScriptRuntimeState(const Mm9ScriptRuntimeState *pState);

    int32_t currentRudeId() const;
    int32_t currentNodeId() const;
    bool closed() const;
    const Mm9DialogueOwnerContext &owner() const;
    Party &party();
    const Party &party() const;

    std::vector<Mm9DialogueTopic> visibleTopics() const;
    Mm9DialogueSelectionResult selectTopic(size_t visibleTopicIndex);
    bool dispatchServiceSelection(
        const Mm9DialogueSelectionResult &selection,
        Mm9DialogueServiceHandler &handler) const;

private:
    const Mm9GeneratedObjectDialogueBinding *objectBindingForObject(
        const std::string &mapId,
        int32_t objectIndex) const;
    std::optional<Mm9DialogueServiceRequest> serviceRequestForTopic(const Mm9DialogueTopic &topic) const;
    uint32_t qbitIdForRawKey(int32_t rawKeyId) const;
    bool rowPassesVisibilityConditions(const Mm9GeneratedRudeRow &row) const;
    bool rowPassesInventoryConditions(const Mm9GeneratedRudeRow &row) const;
    bool rowPassesConsoleConditions(const Mm9GeneratedRudeRow &row) const;
    std::optional<std::string> onRudeExitLabelForScript(const std::string &scriptName) const;

    const Mm9DialoguePackage &m_package;
    Party &m_party;
    const Mm9ScriptRuntimeState *m_pScriptRuntimeState = nullptr;
    const Mm9GeneratedRudeDialogue *m_pDialogue = nullptr;
    Mm9DialogueOwnerContext m_owner;
    int32_t m_currentRudeId = 0;
    int32_t m_currentNodeId = 0;
    bool m_closed = true;
};
}
