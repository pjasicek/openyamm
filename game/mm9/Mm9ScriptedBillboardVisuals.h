#pragma once

#include "game/maps/OutdoorSceneYml.h"

#include <cstdint>
#include <optional>
#include <string>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Engine
{
class AssetFileSystem;
}

namespace OpenYAMM::Game
{
constexpr const char *Mm9ScriptedBillboardVisualSchema = "openyamm.mm9.scripted_billboard_visual.v1";
constexpr const char *Mm9ScriptedBillboardVisualRoot = "worlds/mm9/rendering/scripted_billboards";

struct Mm9ScriptedBillboardFrame
{
    std::string textureName;
    std::string path;
    std::string angle;
    uint32_t durationMs = 0;
    float anchorX = -1.0f;
    float anchorY = -1.0f;
};

struct Mm9ScriptedBillboardClip
{
    std::string name;
    std::string semantic;
    std::string fallback;
    std::string sourceClip;
    uint32_t angleCount = 0;
    uint32_t durationMs = 0;
    std::vector<Mm9ScriptedBillboardFrame> frames;
};

struct Mm9ScriptedBillboardCollision
{
    int radius = 32;
    int height = 128;
    int verticalOffset = 0;
    std::string anchor = "feet";
    std::string source;
};

struct Mm9ScriptedBillboardUse
{
    std::string mapId;
    std::string objectId;
    size_t sourceObjectIndex = 0;
    std::string sourceClass;
    std::string sourceName;
    std::string scriptName;
    std::string scriptParams;
};

struct Mm9ScriptedBillboardVisual
{
    std::string visualId;
    std::string sourceModel;
    std::string sourceGlb;
    std::vector<std::string> sourceSkins;
    std::string variantId;
    std::string modelId;
    uint32_t angleCount = 0;
    std::vector<std::string> angleNames;
    std::vector<Mm9ScriptedBillboardClip> clips;
    Mm9ScriptedBillboardCollision collision = {};
    std::vector<Mm9ScriptedBillboardUse> usedBy;
};

class Mm9ScriptedBillboardVisualSet
{
public:
    bool loadFromAssetFileSystem(
        const Engine::AssetFileSystem &assetFileSystem,
        std::string &errorMessage,
        const std::string &rootPath = Mm9ScriptedBillboardVisualRoot,
        bool verifyFrameAssets = true);

    const Mm9ScriptedBillboardVisual *findVisual(const std::string &visualId) const;
    const Mm9ScriptedBillboardClip *findClip(
        const Mm9ScriptedBillboardVisual &visual,
        const std::string &clipName) const;
    const Mm9ScriptedBillboardClip *findIdleClip(const Mm9ScriptedBillboardVisual &visual) const;
    const Mm9ScriptedBillboardFrame *findFirstIdleFrame(const Mm9ScriptedBillboardVisual &visual) const;
    const Mm9ScriptedBillboardClip *resolveClip(
        const Mm9ScriptedBillboardVisual &visual,
        const std::string &clipName,
        const std::string &semanticFallback) const;
    const Mm9ScriptedBillboardFrame *resolveFrame(
        const Mm9ScriptedBillboardVisual &visual,
        const std::string &clipName,
        const std::string &semanticFallback,
        const std::string &angleName,
        uint32_t elapsedMs) const;
    std::optional<std::string> resolveVisualIdForModelInstance(
        const std::string &mapId,
        const OutdoorSceneModelInstance &modelInstance) const;

    const std::vector<Mm9ScriptedBillboardVisual> &visuals() const;

private:
    void rebuildIndexes();

    std::vector<Mm9ScriptedBillboardVisual> m_visuals;
    std::unordered_map<std::string, size_t> m_visualIndexById;
    std::unordered_map<std::string, size_t> m_visualIndexByMapObject;
    std::unordered_map<std::string, size_t> m_visualIndexByMapClassName;
    std::unordered_map<std::string, size_t> m_visualIndexBySourceModel;
    std::unordered_map<std::string, size_t> m_visualIndexBySourceModelAndSkin;
};
}
