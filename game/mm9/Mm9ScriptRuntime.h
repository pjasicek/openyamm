#pragma once

#include "game/mm9/Mm9DialoguePackage.h"

#include <cstddef>
#include <cstdint>
#include <map>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
struct Mm9DialogueOwnerContext;
struct GameplayWorldHit;
class Mm9DialogueRuntime;

struct Mm9ScriptRuntimeCommand
{
    std::string scriptSource;
    size_t line = 0;
    std::string command;
    std::string argumentsText;
    std::string rawLine;
};

struct Mm9ScriptRuntimeCallback
{
    std::string scriptSource;
    std::string mapId;
    int32_t objectIndex = -1;
    std::string kind;
    std::string selector;
    std::string label;
    size_t line = 0;
};

struct Mm9ScriptRuntimeKeyAccess
{
    std::string scriptSource;
    std::string operation;
    int32_t rawKeyId = 0;
    uint32_t qbitId = 0;
    bool result = false;
    size_t line = 0;
};

struct Mm9ScriptRuntimePartyAccess
{
    std::string scriptSource;
    std::string operation;
    uint32_t id = 0;
    int32_t amount = 0;
    bool result = false;
    size_t line = 0;
};

struct Mm9ScriptRuntimeAudioRequest
{
    std::string mapId;
    int32_t objectIndex = -1;
    std::string objectName;
    std::string scriptSource;
    std::string operation;
    std::string soundName;
    std::string soundHandle;
    std::string handleVar;
    std::string callbackLabel;
    int32_t radius = 0;
    int32_t volume = 0;
    bool loop = false;
    size_t line = 0;
};

struct Mm9ScriptRuntimeAnimationRequest
{
    std::string scriptSource;
    std::string objectHandle;
    std::string operation;
    std::string animationName;
    std::string callbackLabel;
    int32_t loopCount = 0;
    size_t line = 0;
};

struct Mm9ScriptRuntimeClientFxRequest
{
    std::string scriptSource;
    std::string objectHandle;
    std::string operation;
    std::string effectName;
    bool attach = false;
    bool loop = false;
    size_t line = 0;
};

struct Mm9ScriptRuntimePresentationRequest
{
    std::string scriptSource;
    std::string operation;
    std::vector<std::string> arguments;
    size_t line = 0;
};

struct Mm9ScriptRuntimeVec3
{
    double x = 0.0;
    double y = 0.0;
    double z = 0.0;
};

struct Mm9ScriptRuntimeMovementRequest
{
    std::string scriptSource;
    std::string objectHandle;
    std::string operation;
    std::string targetHandle;
    Mm9ScriptRuntimeVec3 targetPosition;
    Mm9ScriptRuntimeVec3 direction;
    double speed = 0.0;
    double distance = 0.0;
    std::string callbackLabel;
    size_t line = 0;
};

struct Mm9ScriptRuntimeSpawnRequest
{
    std::string scriptSource;
    std::string spawnedHandle;
    std::string handleVar;
    Mm9ScriptRuntimeVec3 position;
    std::string parameter;
    size_t line = 0;
};

struct Mm9ScriptRuntimeAiRequest
{
    std::string scriptSource;
    std::string objectHandle;
    std::string operation;
    std::string targetHandle;
    std::string callbackLabel;
    size_t line = 0;
};

struct Mm9ScriptRuntimeAttachmentRequest
{
    std::string scriptSource;
    std::string objectHandle;
    std::string modelName;
    std::string textureName;
    std::string socketName;
    std::string attachedHandle;
    std::string operation;
    size_t line = 0;
};

struct Mm9ScriptRuntimePromotionRequest
{
    std::string scriptSource;
    std::string promotionName;
    std::string characterToken;
    size_t line = 0;
};

struct Mm9ScriptRuntimePartyCommandRequest
{
    std::string scriptSource;
    std::string operation;
    std::vector<std::string> arguments;
    size_t line = 0;
};

struct Mm9ScriptRuntimeControlRequest
{
    std::string scriptSource;
    std::string operation;
    std::string label;
    std::string conditionText;
    bool conditionResult = false;
    double minDelay = 0.0;
    double maxDelay = 0.0;
    std::string exitValue;
    size_t line = 0;
};

struct Mm9ScriptRuntimeScheduledInvocation
{
    std::string scriptSource;
    std::string operation;
    std::string mapId;
    int32_t objectIndex = -1;
    std::string label;
    double dueTimeSeconds = 0.0;
    double minDelay = 0.0;
    double maxDelay = 0.0;
    size_t line = 0;
};

struct Mm9ScriptRuntimeAttributeEffect
{
    uint32_t memberIndex = 0;
    int32_t attributeId = 0;
    int32_t amount = 0;
    double expiresAtSeconds = 0.0;
};

struct Mm9ScriptRuntimeDamageRequest
{
    std::string scriptSource;
    std::string targetHandle;
    int32_t amount = 0;
    int32_t damageType = 0;
    bool noReaction = false;
    size_t line = 0;
};

struct Mm9ObjectActivationResult
{
    bool activated = false;
    bool ranScript = false;
    bool openedDialogue = false;
    bool directDialogue = false;
    bool queuedGreetingSound = false;
    std::string error;
    std::optional<Mm9ScriptRuntimeAudioRequest> audioRequest;
};

struct Mm9ScriptRuntimeTriggerRegistration
{
    std::string scriptSource;
    std::string mapId;
    int32_t objectIndex = -1;
    std::string triggerName;
    std::string label;
    size_t line = 0;
};

struct Mm9ScriptRuntimeTriggerDispatch
{
    std::string scriptSource;
    std::string mapId;
    int32_t objectIndex = -1;
    std::string targetHandle;
    std::string message;
    size_t line = 0;
};

struct Mm9ScriptRuntimeState
{
    std::map<std::string, int32_t> consoleNumVars;
    std::map<std::string, std::string> consoleStrVars;
    std::map<std::string, std::map<std::string, int32_t>> mapNumVars;
    std::map<std::string, std::map<std::string, std::string>> mapStrVars;
    std::map<std::string, int32_t> scriptNumVars;
    std::map<std::string, std::string> scriptStrVars;
    std::map<std::string, std::map<int32_t, int32_t>> scriptNumArrays;
    std::map<std::string, std::map<int32_t, std::string>> scriptStrArrays;
    std::map<std::string, std::string> objectHandleVars;
    std::map<std::string, std::string> soundHandleVars;
    std::map<std::string, std::string> objectTargetHandles;
    std::map<std::string, std::map<std::string, int32_t>> objectStats;
    std::map<std::string, std::map<std::string, std::string>> objectStringProperties;
    std::map<std::string, std::map<std::string, int32_t>> objectFlags;
    std::map<std::string, bool> removedObjects;
    std::map<std::string, std::string> activeSoundHandles;
    std::vector<Mm9ScriptRuntimeAudioRequest> audioRequests;
    int32_t nextSoundHandleId = 1;
    std::map<std::string, Mm9ScriptRuntimeVec3> objectPositions;
    std::map<std::string, Mm9ScriptRuntimeVec3> objectFaceDirs;
    std::map<std::string, std::vector<std::string>> objectLinks;
    std::map<std::string, std::string> objectScriptOverrides;
    std::vector<Mm9ScriptRuntimeMovementRequest> movementRequests;
    std::vector<Mm9ScriptRuntimeSpawnRequest> spawnRequests;
    int32_t nextSpawnHandleId = 1;
    std::map<std::string, std::vector<std::string>> objectFriends;
    std::map<std::string, std::vector<std::string>> objectEnemies;
    std::map<std::string, std::string> objectAiStates;
    std::map<std::string, bool> objectAttackStates;
    std::vector<Mm9ScriptRuntimeAiRequest> aiRequests;
    std::vector<Mm9ScriptRuntimeAnimationRequest> animationRequests;
    std::vector<Mm9ScriptRuntimeClientFxRequest> clientFxRequests;
    std::vector<Mm9ScriptRuntimePresentationRequest> presentationRequests;
    std::map<std::string, std::vector<std::string>> objectModelFilenames;
    std::vector<Mm9ScriptRuntimeAttachmentRequest> attachmentRequests;
    std::vector<Mm9ScriptRuntimePromotionRequest> promotionRequests;
    std::vector<Mm9ScriptRuntimePartyCommandRequest> partyCommandRequests;
    std::vector<Mm9ScriptRuntimeControlRequest> controlRequests;
    double scriptTimeSeconds = 0.0;
    std::vector<Mm9ScriptRuntimeScheduledInvocation> scheduledInvocations;
    std::vector<Mm9ScriptRuntimeAttributeEffect> attributeEffects;
    std::vector<Mm9ScriptRuntimeDamageRequest> damageRequests;
    std::map<std::string, int32_t> objectNumberProperties;
    std::vector<Mm9ScriptRuntimeTriggerRegistration> triggers;
    std::vector<Mm9ScriptRuntimeTriggerDispatch> triggerDispatches;
    std::vector<Mm9ScriptRuntimeCallback> registeredCallbacks;
};

Mm9ScriptRuntimeState createInitialMm9ScriptRuntimeState(const Mm9DialoguePackage &package);

class Mm9ScriptRuntime
{
public:
    Mm9ScriptRuntime(const Mm9DialoguePackage &package, Mm9DialogueRuntime &dialogueRuntime);

    bool runLabel(
        const std::string &scriptSource,
        const std::string &label,
        std::optional<std::string> &errorMessage);
    Mm9ObjectActivationResult activateObject(const std::string &mapId, int32_t objectIndex);
    Mm9ObjectActivationResult activateObject(const GameplayWorldHit &hit);

    const std::vector<Mm9ScriptRuntimeCommand> &unimplementedCommands() const;
    const std::vector<Mm9ScriptRuntimeCallback> &registeredCallbacks() const;
    const std::vector<Mm9ScriptRuntimeKeyAccess> &keyAccesses() const;
    const std::vector<Mm9ScriptRuntimePartyAccess> &partyAccesses() const;
    const std::vector<Mm9ScriptRuntimeAudioRequest> &audioRequests() const;
    const std::vector<Mm9ScriptRuntimeAnimationRequest> &animationRequests() const;
    const std::vector<Mm9ScriptRuntimeClientFxRequest> &clientFxRequests() const;
    const std::vector<Mm9ScriptRuntimePresentationRequest> &presentationRequests() const;
    const std::vector<Mm9ScriptRuntimeMovementRequest> &movementRequests() const;
    const std::vector<Mm9ScriptRuntimeSpawnRequest> &spawnRequests() const;
    const std::vector<Mm9ScriptRuntimeAiRequest> &aiRequests() const;
    const std::vector<Mm9ScriptRuntimeAttachmentRequest> &attachmentRequests() const;
    const std::vector<Mm9ScriptRuntimePromotionRequest> &promotionRequests() const;
    const std::vector<Mm9ScriptRuntimePartyCommandRequest> &partyCommandRequests() const;
    const std::vector<Mm9ScriptRuntimeControlRequest> &controlRequests() const;
    const std::vector<Mm9ScriptRuntimeScheduledInvocation> &scheduledInvocations() const;
    const std::vector<Mm9ScriptRuntimeDamageRequest> &damageRequests() const;
    double scriptTimeSeconds() const;
    bool advanceScriptTime(double elapsedSeconds, std::optional<std::string> &errorMessage);
    bool dispatchRegisteredCallbacks(
        const std::string &kind,
        const std::string &selector,
        const std::string &mapId,
        int32_t objectIndex,
        std::optional<std::string> &errorMessage,
        size_t &dispatchedCount);
    bool dispatchMovementResult(
        size_t movementRequestIndex,
        const std::string &resultKind,
        std::optional<std::string> &errorMessage,
        size_t &dispatchedCount);
    bool dispatchAnimationResult(
        size_t animationRequestIndex,
        const std::string &resultKind,
        const std::string &selector,
        std::optional<std::string> &errorMessage,
        size_t &dispatchedCount);
    bool dispatchAudioResult(
        size_t audioRequestIndex,
        const std::string &resultKind,
        std::optional<std::string> &errorMessage,
        size_t &dispatchedCount);

    std::optional<int32_t> resolveRawKeyId(const std::string &token) const;
    int32_t resolveScriptNumber(const std::string &token, int32_t defaultValue = 0) const;
    void setConsoleNumVar(const std::string &name, int32_t value);
    int32_t getConsoleNumVar(const std::string &name, int32_t defaultValue = 0) const;
    void setConsoleStrVar(const std::string &name, const std::string &value);
    std::string getConsoleStrVar(const std::string &name, const std::string &defaultValue = {}) const;
    void setMapNumVar(const std::string &mapId, const std::string &name, int32_t value);
    int32_t getMapNumVar(const std::string &mapId, const std::string &name, int32_t defaultValue = 0) const;
    void setMapStrVar(const std::string &mapId, const std::string &name, const std::string &value);
    std::string getMapStrVar(
        const std::string &mapId,
        const std::string &name,
        const std::string &defaultValue = {}) const;
    void setScriptNumVar(const std::string &name, int32_t value);
    int32_t getScriptNumVar(const std::string &name, int32_t defaultValue = 0) const;
    void setScriptStrVar(const std::string &name, const std::string &value);
    std::string getScriptStrVar(const std::string &name, const std::string &defaultValue = {}) const;
    void setObjectHandleVar(const std::string &name, const std::string &handle);
    std::string getObjectHandleVar(const std::string &name, const std::string &defaultValue = {}) const;
    std::string getSoundHandleVar(const std::string &name, const std::string &defaultValue = {}) const;
    std::string objectHandleForName(const std::string &name) const;
    void setObjectNumberProperty(const std::string &propertyName, int32_t value, size_t line);
    int32_t getObjectNumberProperty(const std::string &propertyKey, int32_t defaultValue = 0) const;
    std::string resolveScriptString(const std::string &token) const;
    bool executeCommand(
        const std::string &command,
        const std::string &argumentsText,
        size_t line,
        const std::string &rawLine);
    const Mm9ScriptRuntimeState &state() const;
    void restoreState(const Mm9ScriptRuntimeState &state);
    void recordUnimplementedCommand(
        const std::string &command,
        const std::string &argumentsText,
        size_t line,
        const std::string &rawLine);
    void registerCallback(
        const std::string &label,
        size_t line,
        const std::string &kind = {},
        const std::string &selector = {});
    void removeCallbackRegistrations(const std::string &kind, const std::string &selector);
    void recordKeyAccess(const std::string &operation, int32_t rawKeyId, bool result, size_t line);
    void recordPartyAccess(
        const std::string &operation,
        uint32_t id,
        int32_t amount,
        bool result,
        size_t line);
    std::string objectHandleForRudeId(int32_t rudeId) const;
    void registerTrigger(const std::string &triggerName, const std::string &label, size_t line);
    void removeTrigger(const std::string &triggerName);
    void dispatchTrigger(const std::string &targetHandle, const std::string &message, size_t line);
    Mm9DialogueRuntime &dialogueRuntime();
    const std::string &activeScriptSource() const;

private:
    std::string activeObjectPropertyKey(const std::string &propertyName) const;
    std::string activeObjectHandle() const;
    const Mm9GeneratedObjectDialogueBinding *objectBindingForHandle(const std::string &handle) const;
    const Mm9GeneratedObjectDialogueBinding *objectBindingForObject(
        const std::string &mapId,
        int32_t objectIndex) const;
    bool runLabelForObject(
        const std::string &scriptSource,
        const std::string &label,
        const std::string &mapId,
        int32_t objectIndex,
        std::optional<std::string> &errorMessage);
    void removeRuntimeObject(const std::string &handle);
    std::string resolveSoundHandle(const std::string &token) const;
    void recordAudioRequest(Mm9ScriptRuntimeAudioRequest request);
    void recordAnimationRequest(Mm9ScriptRuntimeAnimationRequest request);
    void recordClientFxRequest(Mm9ScriptRuntimeClientFxRequest request);
    void recordPresentationRequest(
        const std::string &operation,
        const std::vector<std::string> &arguments,
        size_t line);
    void recordMovementRequest(Mm9ScriptRuntimeMovementRequest request);
    void recordSpawnRequest(Mm9ScriptRuntimeSpawnRequest request);
    void recordAiRequest(Mm9ScriptRuntimeAiRequest request);
    void recordAttachmentRequest(Mm9ScriptRuntimeAttachmentRequest request);
    void recordPromotionRequest(Mm9ScriptRuntimePromotionRequest request);
    void recordPartyCommandRequest(Mm9ScriptRuntimePartyCommandRequest request);
    void recordControlRequest(Mm9ScriptRuntimeControlRequest request);
    void scheduleInvocation(
        const std::string &operation,
        const std::string &label,
        double minDelay,
        double maxDelay,
        size_t line);
    void expireAttributeEffects();
    void recordDamageRequest(Mm9ScriptRuntimeDamageRequest request);
    void queueGreetingSoundRequest(const Mm9DialogueOwnerContext &owner);

    const Mm9DialoguePackage &m_package;
    Mm9DialogueRuntime &m_dialogueRuntime;
    std::string m_activeScriptSource;
    Mm9ScriptRuntimeState m_state;
    std::vector<Mm9ScriptRuntimeCommand> m_unimplementedCommands;
    std::vector<Mm9ScriptRuntimeCallback> m_registeredCallbacks;
    std::vector<Mm9ScriptRuntimeKeyAccess> m_keyAccesses;
    std::vector<Mm9ScriptRuntimePartyAccess> m_partyAccesses;
    std::vector<Mm9ScriptRuntimeAudioRequest> m_audioRequests;
    std::vector<Mm9ScriptRuntimeAnimationRequest> m_animationRequests;
    std::vector<Mm9ScriptRuntimeClientFxRequest> m_clientFxRequests;
    std::vector<Mm9ScriptRuntimePresentationRequest> m_presentationRequests;
    std::vector<Mm9ScriptRuntimeMovementRequest> m_movementRequests;
    std::vector<Mm9ScriptRuntimeSpawnRequest> m_spawnRequests;
    std::vector<Mm9ScriptRuntimeAiRequest> m_aiRequests;
    std::vector<Mm9ScriptRuntimeAttachmentRequest> m_attachmentRequests;
    std::vector<Mm9ScriptRuntimePromotionRequest> m_promotionRequests;
    std::vector<Mm9ScriptRuntimePartyCommandRequest> m_partyCommandRequests;
    std::vector<Mm9ScriptRuntimeControlRequest> m_controlRequests;
    std::vector<Mm9ScriptRuntimeDamageRequest> m_damageRequests;
    size_t m_triggerDispatchDepth = 0;
    size_t m_schedulerDispatchDepth = 0;
};
}
