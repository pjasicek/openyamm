#pragma once

#include "game/maps/Mm9EventsYml.h"
#include "game/maps/OutdoorSceneYml.h"
#include "game/mm9/Mm9ScriptedBillboardVisuals.h"

#include <cstddef>
#include <string>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Game
{
struct Mm9ScriptedObjectRawPropertyRef
{
    size_t propertyIndex = 0;
    std::string name;
    bool decoded = false;
    int code = 0;
    int flags = 0;
    std::string rawRef;
};

struct Mm9ScriptedObjectMovementState
{
    bool stationary = true;
    bool walking = false;
    bool running = false;
    bool flying = false;
    bool rooted = true;
    bool scriptedPath = false;
    bool fleeing = false;
    bool returning = false;
    bool moveToFloor = true;
    bool wanderEnabled = false;
    float animationSpeed = 0.0f;
    float speed = 0.0f;
    float closingSpeed = 0.0f;
    float runawayChance = 0.0f;
    float wanderLeash = 0.0f;
    std::string wanderPathName;
};

struct Mm9ScriptedObject
{
    std::string mapId;
    std::string visualId;
    std::string instanceId;
    std::string objectId;
    std::string sourceRef;
    std::string sourceKind;
    size_t sourceObjectIndex = 0;
    std::string sourceObjectId;
    std::string sourceClass;
    std::string sourceName;
    std::string sourceModel;
    std::string sourceSkin;
    std::string modelAsset;
    std::string modelSkinBinding;
    std::string scriptName;
    std::string scriptParams;
    std::string rawObjectRef;
    size_t rawPropertyCount = 0;
    std::vector<Mm9ScriptedObjectRawPropertyRef> rawProperties;
    std::unordered_map<std::string, std::string> normalizedProperties;
    std::string currentClip;
    std::string movementState;
    Mm9ScriptedObjectMovementState movement;
    bool visible = true;
    bool solid = true;
    bool rayHit = true;
    bool needsTick = false;
    bool pickable = true;
    bool missingVisual = false;
    bool missingVisualDiagnosticLogged = false;
    std::string missingVisualReason;
    float x = 0.0f;
    float y = 0.0f;
    float z = 0.0f;
    float facingRadians = 0.0f;
    float scale = 1.0f;
    float radius = 32.0f;
    float height = 128.0f;
    float verticalOffset = 0.0f;
};

class Mm9ScriptedObjectRuntime
{
public:
    bool initialize(
        const std::string &mapId,
        const OutdoorSceneData &sceneData,
        const Mm9ScriptedBillboardVisualSet &visualSet,
        const Mm9EventsData *pEventsData);

    const std::vector<Mm9ScriptedObject> &objects() const;
    std::vector<Mm9ScriptedObject> &objects();

private:
    std::vector<Mm9ScriptedObject> m_objects;
};
}
