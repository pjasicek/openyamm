#pragma once

#include <cstddef>
#include <optional>
#include <string>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Game
{
struct Mm9EventScript
{
    struct Include
    {
        int line = 0;
        std::string path;
    };

    struct Label
    {
        int line = 0;
        std::string name;
    };

    struct RegisteredTrigger
    {
        int line = 0;
        std::string message;
        std::string callback;
        std::string argumentsRaw;
    };

    struct TriggerEdge
    {
        int line = 0;
        std::string targetExpression;
        std::string messageExpression;
        std::string argumentsRaw;
    };

    struct ScriptCommand
    {
        int line = 0;
        std::string command;
        std::string argumentsRaw;
    };

    std::string scriptId;
    std::string sourcePath;
    size_t registeredTriggerCount = 0;
    size_t movementCommandCount = 0;
    size_t unknownCommandCount = 0;
    size_t commandCount = 0;
    std::vector<Include> includes;
    std::vector<Label> labels;
    std::vector<RegisteredTrigger> registeredTriggers;
    std::vector<TriggerEdge> triggerEdges;
    std::vector<ScriptCommand> movementCommands;
    std::vector<ScriptCommand> unknownCommands;
};

struct Mm9EventObject
{
    struct RawPropertyRef
    {
        size_t propertyIndex = 0;
        std::string name;
        bool decoded = false;
        int code = 0;
        int flags = 0;
        std::string rawRef;
    };

    std::string objectId;
    int sourceObjectIndex = -1;
    std::string sourceClass;
    std::string sourceName;
    std::string rawObjectRef;
    size_t rawPropertyCount = 0;
    std::vector<std::string> classifications;
    std::vector<RawPropertyRef> rawProperties;
    std::unordered_map<std::string, std::string> normalizedProperties;
};

struct Mm9EventBindingTarget
{
    struct SourcePolygonGroup
    {
        size_t sourceModelIndex = 0;
        std::string sourceModelName;
        size_t sourcePolyCount = 0;
        size_t sourceSurfaceCount = 0;
        std::vector<float> boundsMinLt;
        std::vector<float> boundsMaxLt;
        bool movable = false;
        bool hasMovable = false;
    };

    struct MovableWorldModelCandidate
    {
        struct ExactBindingClaim
        {
            int sourceObjectIndex = -1;
            std::string sourceName;
            std::string confidence;
        };

        size_t sourceModelIndex = 0;
        std::string sourceName;
        bool movable = false;
        std::vector<float> worldTranslationLt;
        float distanceLt = 0.0f;
        std::vector<ExactBindingClaim> claimedByExactBindings;
    };

    std::string targetKind;
    std::string targetId;
    std::string confidence;
    std::optional<size_t> bmodelIndex;
    std::string bmodelName;
    std::string sourceModelName;
    std::optional<SourcePolygonGroup> sourcePolygonGroup;
    std::vector<MovableWorldModelCandidate> nearestMovableWorldModelsByRotationPoint;
    std::vector<MovableWorldModelCandidate> nearestMovableWorldModelsByPosition;
};

struct Mm9EventBinding
{
    std::string objectId;
    int sourceObjectIndex = -1;
    std::vector<Mm9EventBindingTarget> targets;
};

struct Mm9EventActivation
{
    bool startOpen = false;
    bool hasStartOpen = false;
    bool locked = false;
    bool hasLocked = false;
    bool pushOpen = false;
    bool hasPushOpen = false;
    bool touchToOpen = false;
    bool hasTouchToOpen = false;
    bool lockOnClose = false;
    bool hasLockOnClose = false;
    bool reopenOnContact = false;
    bool hasReopenOnContact = false;
};

struct Mm9EventLinearMotion
{
    std::vector<float> moveDirLt;
    float moveDistLt = 0.0f;
    float openSpeedLtPerSecond = 0.0f;
    float closeSpeedLtPerSecond = 0.0f;
    bool hasMoveDir = false;
    bool hasMoveDist = false;
    bool hasOpenSpeed = false;
    bool hasCloseSpeed = false;
};

struct Mm9EventRotationMotion
{
    std::vector<float> rotationPointLt;
    std::vector<float> rotationAnglesDeg;
    bool openAway = false;
    bool hasRotationPoint = false;
    bool hasRotationAngles = false;
    bool hasOpenAway = false;
};

struct Mm9EventMechanismTiming
{
    float moveDelaySecondsSource = 0.0f;
    float openWaitSecondsSource = 0.0f;
    bool hasMoveDelaySecondsSource = false;
    bool hasOpenWaitSecondsSource = false;
};

struct Mm9EventTriggerOutput
{
    std::string phase;
    int slot = -1;
    std::string targetName;
    std::string messageName;
    std::string resolution;
};

struct Mm9EventMechanismSound
{
    std::string phase;
    std::string sourceProperty;
    std::string soundName;
    bool authored = false;
};

struct Mm9EventMechanism
{
    std::string mechanismId;
    std::string objectId;
    int sourceObjectIndex = -1;
    std::string sourceClass;
    std::string sourceName;
    std::string kind;
    Mm9EventActivation activation;
    Mm9EventLinearMotion linear;
    Mm9EventRotationMotion rotation;
    Mm9EventMechanismTiming timing;
    std::vector<Mm9EventMechanismSound> sounds;
    std::vector<Mm9EventTriggerOutput> triggerOutputs;
};

struct Mm9EventUnresolved
{
    std::string kind;
    int sourceObjectIndex = -1;
    std::string sourceName;
    std::string sourceClass;
    std::string severity;
    std::vector<Mm9EventBindingTarget::MovableWorldModelCandidate> nearestMovableWorldModelsByRotationPoint;
    std::vector<Mm9EventBindingTarget::MovableWorldModelCandidate> nearestMovableWorldModelsByPosition;
};

struct Mm9EventsData
{
    int formatVersion = 0;
    std::string kind;
    std::string sourceDat;
    std::string sourceRawObjects;
    std::string generatedLua;
    std::string generatedScriptIr;
    std::vector<Mm9EventObject> objects;
    std::vector<Mm9EventMechanism> mechanisms;
    std::vector<Mm9EventBinding> bindings;
    std::vector<Mm9EventScript> scripts;
    std::vector<Mm9EventUnresolved> unresolved;
    size_t mechanismCount = 0;
    size_t triggerCount = 0;
    size_t interactionCount = 0;
    size_t unresolvedCount = 0;
};

class Mm9EventsYmlLoader
{
public:
    std::optional<Mm9EventsData> loadFromText(const std::string &yamlText, std::string &errorMessage) const;
};
}
