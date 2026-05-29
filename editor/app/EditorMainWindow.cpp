#include "editor/app/EditorMainWindow.h"
#include "engine/ImageAssetLoader.h"
#include "game/indoor/IndoorGeometryUtils.h"
#include "editor/import/ObjModelImport.h"
#include "editor/model/Mm9ModelInstanceActorResolver.h"

#include "game/maps/TerrainTileData.h"
#include "game/maps/MapIdentity.h"
#include "game/mm9/Mm9DatWorld.h"
#include "game/mm9/Mm9DtxTexture.h"
#include "game/SpawnPreview.h"
#include "game/SpriteObjectDefs.h"
#include "game/data/ActorNameResolver.h"
#include "game/events/EvtEnums.h"
#include "game/outdoor/OutdoorGeometryUtils.h"

#include <imgui.h>
#include <imgui_internal.h>
#include <SDL3/SDL.h>

#include <algorithm>
#include <array>
#include <cctype>
#include <cmath>
#include <cfloat>
#include <cstdio>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iterator>
#include <limits>
#include <optional>
#include <sstream>
#include <unordered_map>
#include <unordered_set>
#include <vector>

#if defined(_WIN32)
#include <process.h>
#else
#include <sys/types.h>
#include <unistd.h>
#endif

namespace OpenYAMM::Editor
{
namespace
{
std::string formatIndoorRoomList(const std::vector<uint16_t> &roomIds);
Game::IndoorFace effectiveIndoorFace(
    const Game::IndoorSceneData &sceneData,
    const Game::IndoorMapData &indoorGeometry,
    size_t faceIndex);

ImGuiID editorDockspaceId()
{
    return ImGui::GetID("EditorDockspace");
}

std::filesystem::path editorStatePath()
{
    return std::filesystem::current_path() / ".openyamm-editor.ini";
}

std::filesystem::path editorBasePath()
{
    const char *pBasePath = SDL_GetBasePath();

    if (pBasePath == nullptr || *pBasePath == '\0')
    {
        return std::filesystem::current_path();
    }

    return std::filesystem::path(pBasePath);
}

std::filesystem::path defaultGameExecutablePath()
{
#if defined(_WIN32)
    static constexpr const char *ExecutableName = "openyamm.exe";
#else
    static constexpr const char *ExecutableName = "openyamm";
#endif

    const std::filesystem::path basePath = editorBasePath();
    const std::array<std::filesystem::path, 3> candidates = {{
        std::filesystem::current_path() / "build" / "game" / ExecutableName,
        basePath / ".." / "game" / ExecutableName,
        basePath / ExecutableName
    }};

    for (const std::filesystem::path &candidate : candidates)
    {
        std::error_code error;

        if (std::filesystem::exists(candidate, error))
        {
            return std::filesystem::weakly_canonical(candidate, error);
        }
    }

    return {};
}

bool launchDetachedProcess(
    const std::filesystem::path &executablePath,
    const std::vector<std::string> &arguments,
    std::string &errorMessage)
{
    if (executablePath.empty())
    {
        errorMessage = "game executable path is empty";
        return false;
    }

    const std::string executableText = executablePath.string();

#if defined(_WIN32)
    std::vector<const char *> argv;
    argv.reserve(arguments.size() + 2);
    argv.push_back(executableText.c_str());

    for (const std::string &argument : arguments)
    {
        argv.push_back(argument.c_str());
    }

    argv.push_back(nullptr);
    const intptr_t processHandle = _spawnv(_P_NOWAIT, executableText.c_str(), argv.data());

    if (processHandle == -1)
    {
        errorMessage = "could not launch " + executableText;
        return false;
    }

    return true;
#else
    const pid_t childPid = fork();

    if (childPid < 0)
    {
        errorMessage = "could not fork for playtest launch";
        return false;
    }

    if (childPid == 0)
    {
        std::vector<char *> argv;
        argv.reserve(arguments.size() + 2);
        argv.push_back(const_cast<char *>(executableText.c_str()));

        for (const std::string &argument : arguments)
        {
            argv.push_back(const_cast<char *>(argument.c_str()));
        }

        argv.push_back(nullptr);
        execv(executableText.c_str(), argv.data());
        _exit(127);
    }

    return true;
#endif
}

std::string toLowerCopy(const std::string &value)
{
    std::string result = value;

    for (char &character : result)
    {
        character = static_cast<char>(std::tolower(static_cast<unsigned char>(character)));
    }

    return result;
}

std::string trimCopy(const std::string &value)
{
    const auto begin = std::find_if_not(value.begin(), value.end(), [](unsigned char character)
    {
        return std::isspace(character) != 0;
    });
    const auto end = std::find_if_not(value.rbegin(), value.rend(), [](unsigned char character)
    {
        return std::isspace(character) != 0;
    }).base();

    if (begin >= end)
    {
        return {};
    }

    return std::string(begin, end);
}

bool stringContains(const std::string &value, const std::string &substring)
{
    return value.find(substring) != std::string::npos;
}

bool stringStartsWith(const std::string &value, const std::string &prefix)
{
    return value.size() >= prefix.size() && value.compare(0, prefix.size(), prefix) == 0;
}

bool isIndoorSourceDiagnostic(const std::string &message)
{
    return stringStartsWith(message, "Indoor source ") || stringStartsWith(message, "Indoor geometry source ");
}

bool indoorDoorContainsFace(const Game::MapDeltaDoor &door, uint16_t faceId)
{
    return std::find(door.faceIds.begin(), door.faceIds.end(), faceId) != door.faceIds.end();
}

void synchronizeIndoorDoorFaceArraySizes(Game::MapDeltaDoor &door)
{
    door.numFaces = static_cast<uint16_t>(door.faceIds.size());
    door.deltaUs.resize(door.faceIds.size(), 0);
    door.deltaVs.resize(door.faceIds.size(), 0);
}

bool addIndoorDoorFace(Game::MapDeltaDoor &door, uint16_t faceId)
{
    if (indoorDoorContainsFace(door, faceId))
    {
        return false;
    }

    synchronizeIndoorDoorFaceArraySizes(door);
    door.faceIds.push_back(faceId);
    door.deltaUs.push_back(0);
    door.deltaVs.push_back(0);
    door.numFaces = static_cast<uint16_t>(door.faceIds.size());
    return true;
}

bool removeIndoorDoorFace(Game::MapDeltaDoor &door, uint16_t faceId)
{
    const auto iterator = std::find(door.faceIds.begin(), door.faceIds.end(), faceId);

    if (iterator == door.faceIds.end())
    {
        return false;
    }

    const size_t offset = static_cast<size_t>(std::distance(door.faceIds.begin(), iterator));
    door.faceIds.erase(iterator);

    if (offset < door.deltaUs.size())
    {
        door.deltaUs.erase(door.deltaUs.begin() + static_cast<ptrdiff_t>(offset));
    }

    if (offset < door.deltaVs.size())
    {
        door.deltaVs.erase(door.deltaVs.begin() + static_cast<ptrdiff_t>(offset));
    }

    synchronizeIndoorDoorFaceArraySizes(door);
    return true;
}

bool canSplitImportedModelPathByMesh(const std::string &pathText)
{
    const std::string trimmedPath = trimCopy(pathText);

    if (trimmedPath.empty())
    {
        return false;
    }

    const std::string extension = toLowerCopy(std::filesystem::path(trimmedPath).extension().string());
    return extension == ".gltf" || extension == ".glb";
}

std::string importedModelSummaryText(size_t modelCount)
{
    if (modelCount == 0)
    {
        return "No named meshes found.";
    }

    if (modelCount == 1)
    {
        return "1 named mesh found.";
    }

    return std::to_string(modelCount) + " named meshes found.";
}

size_t countImportedModelMaterials(const ImportedModel &model)
{
    std::unordered_set<std::string> materials;

    for (const ImportedModelFace &face : model.faces)
    {
        const std::string materialName = trimCopy(face.materialName);

        if (!materialName.empty())
        {
            materials.insert(toLowerCopy(materialName));
        }
    }

    return materials.size();
}

EditorMainWindow::ModelImportInspectionState::Entry buildImportedModelInspectionEntry(const ImportedModel &model)
{
    EditorMainWindow::ModelImportInspectionState::Entry entry = {};
    entry.name = model.name;
    entry.vertexCount = model.positions.size();
    entry.faceCount = model.faces.size();
    entry.materialCount = countImportedModelMaterials(model);

    if (model.positions.empty())
    {
        return entry;
    }

    entry.minX = model.positions.front().x;
    entry.minY = model.positions.front().y;
    entry.minZ = model.positions.front().z;
    entry.maxX = model.positions.front().x;
    entry.maxY = model.positions.front().y;
    entry.maxZ = model.positions.front().z;

    for (const ImportedModelPosition &position : model.positions)
    {
        entry.minX = std::min(entry.minX, position.x);
        entry.minY = std::min(entry.minY, position.y);
        entry.minZ = std::min(entry.minZ, position.z);
        entry.maxX = std::max(entry.maxX, position.x);
        entry.maxY = std::max(entry.maxY, position.y);
        entry.maxZ = std::max(entry.maxZ, position.z);
    }

    return entry;
}

std::optional<EditorMainWindow::ModelImportInspectionState::Entry> mergedImportedModelInspectionEntry(
    const EditorMainWindow::ModelImportInspectionState &state)
{
    if (state.entries.empty())
    {
        return std::nullopt;
    }

    EditorMainWindow::ModelImportInspectionState::Entry merged = {};
    merged.name = "<Merged Scene>";
    merged.minX = state.entries.front().minX;
    merged.minY = state.entries.front().minY;
    merged.minZ = state.entries.front().minZ;
    merged.maxX = state.entries.front().maxX;
    merged.maxY = state.entries.front().maxY;
    merged.maxZ = state.entries.front().maxZ;

    for (const EditorMainWindow::ModelImportInspectionState::Entry &entry : state.entries)
    {
        merged.vertexCount += entry.vertexCount;
        merged.faceCount += entry.faceCount;
        merged.materialCount += entry.materialCount;
        merged.minX = std::min(merged.minX, entry.minX);
        merged.minY = std::min(merged.minY, entry.minY);
        merged.minZ = std::min(merged.minZ, entry.minZ);
        merged.maxX = std::max(merged.maxX, entry.maxX);
        merged.maxY = std::max(merged.maxY, entry.maxY);
        merged.maxZ = std::max(merged.maxZ, entry.maxZ);
    }

    return merged;
}

const EditorMainWindow::ModelImportInspectionState::Entry *findImportedModelInspectionEntry(
    const EditorMainWindow::ModelImportInspectionState &state,
    const std::string &selectedModelName)
{
    const std::string normalizedSelection = toLowerCopy(trimCopy(selectedModelName));

    if (normalizedSelection.empty())
    {
        return nullptr;
    }

    for (const EditorMainWindow::ModelImportInspectionState::Entry &entry : state.entries)
    {
        if (toLowerCopy(trimCopy(entry.name)) == normalizedSelection)
        {
            return &entry;
        }
    }

    return nullptr;
}

std::vector<std::string> collectOutdoorMapFileNames(const Engine::AssetFileSystem &assetFileSystem)
{
    const std::vector<std::string> entries = assetFileSystem.enumerate("Data/games");
    std::unordered_set<std::string> seenMapFiles;
    std::vector<std::string> mapFiles;

    for (const std::string &entry : entries)
    {
        std::string mapFileName;

        if (entry.ends_with(".map.yml") || entry.ends_with(".scene.yml"))
        {
            mapFileName = std::filesystem::path(entry).stem().stem().string() + ".odm";
        }
        else if (entry.ends_with(".odm"))
        {
            mapFileName = std::filesystem::path(entry).filename().string();
        }

        if (mapFileName.empty())
        {
            continue;
        }

        const std::string normalized = toLowerCopy(mapFileName);

        if (!seenMapFiles.insert(normalized).second)
        {
            continue;
        }

        mapFiles.push_back(mapFileName);
    }

    std::sort(mapFiles.begin(), mapFiles.end());
    return mapFiles;
}

std::vector<std::string> collectEditableMapFileNames(const Engine::AssetFileSystem &assetFileSystem)
{
    const std::vector<std::string> entries = assetFileSystem.enumerate("Data/games");
    std::unordered_set<std::string> seenMapFiles;
    std::vector<std::string> mapFiles;

    for (const std::string &entry : entries)
    {
        std::string mapFileName;

        if (entry.ends_with(".map.yml") || entry.ends_with(".scene.yml"))
        {
            const std::filesystem::path path(entry);
            const std::string baseName = path.stem().stem().string();
            const std::string blvName = baseName + ".blv";
            mapFileName = assetFileSystem.exists((path.parent_path() / blvName).generic_string())
                ? blvName
                : baseName + ".odm";
        }
        else if (entry.ends_with(".odm") || entry.ends_with(".blv"))
        {
            mapFileName = std::filesystem::path(entry).filename().string();
        }

        if (mapFileName.empty())
        {
            continue;
        }

        const std::string normalized = toLowerCopy(mapFileName);

        if (!seenMapFiles.insert(normalized).second)
        {
            continue;
        }

        mapFiles.push_back(mapFileName);
    }

    std::sort(mapFiles.begin(), mapFiles.end());
    return mapFiles;
}

struct OpenableMapEntry
{
    std::filesystem::path physicalPath;
    std::string kindLabel;
};

std::string openableMapKindLabel(const std::filesystem::path &path)
{
    const std::string fileNameLower = toLowerCopy(path.filename().string());
    const std::string extension = toLowerCopy(path.extension().string());
    const std::string normalizedPath = toLowerCopy(path.generic_string());
    const bool underMm9World =
        normalizedPath.find("/worlds/mm9/") != std::string::npos
        || normalizedPath.find("\\worlds\\mm9\\") != std::string::npos;

    if (fileNameLower.ends_with(".level.yml"))
    {
        return underMm9World ? "MM9 DAT" : "DAT Level";
    }

    if (fileNameLower.ends_with(".scene.yml"))
    {
        return "Scene";
    }

    if (fileNameLower.ends_with(".map.yml"))
    {
        return "Map YAML";
    }

    if (extension == ".odm")
    {
        return underMm9World ? "MM9 Compat ODM" : "ODM";
    }

    if (extension == ".blv")
    {
        return underMm9World ? "MM9 Compat BLV" : "BLV";
    }

    return "Map";
}

std::vector<std::filesystem::path> collectChildDirectories(const std::filesystem::path &directoryPath)
{
    std::vector<std::filesystem::path> directories;

    try
    {
        for (const std::filesystem::directory_entry &entry : std::filesystem::directory_iterator(directoryPath))
        {
            if (entry.is_directory())
            {
                directories.push_back(entry.path());
            }
        }
    }
    catch (const std::filesystem::filesystem_error &)
    {
    }

    std::sort(directories.begin(), directories.end());
    return directories;
}

std::vector<OpenableMapEntry> collectOpenableMapEntries(
    const std::filesystem::path &directoryPath)
{
    std::unordered_set<std::string> seenPaths;
    std::vector<OpenableMapEntry> entries;

    try
    {
        for (const std::filesystem::directory_entry &entry : std::filesystem::directory_iterator(directoryPath))
        {
            if (!entry.is_regular_file())
            {
                continue;
            }

            const std::filesystem::path path = entry.path();
            const std::string extension = toLowerCopy(path.extension().string());
            if (extension != ".odm" && extension != ".blv" && extension != ".yml")
            {
                continue;
            }

            const std::string fileNameLower = toLowerCopy(path.filename().string());

            if (extension == ".yml"
                && !fileNameLower.ends_with(".scene.yml")
                && !fileNameLower.ends_with(".map.yml")
                && !fileNameLower.ends_with(".level.yml"))
            {
                continue;
            }

            const std::string normalizedPath = toLowerCopy(path.generic_string());

            if (!seenPaths.insert(normalizedPath).second)
            {
                continue;
            }

            OpenableMapEntry openableEntry = {};
            openableEntry.physicalPath = path;
            openableEntry.kindLabel = openableMapKindLabel(path);
            entries.push_back(openableEntry);
        }
    }
    catch (const std::filesystem::filesystem_error &)
    {
    }

    std::sort(entries.begin(), entries.end(), [](const OpenableMapEntry &left, const OpenableMapEntry &right)
    {
        return toLowerCopy(left.physicalPath.filename().string()) < toLowerCopy(right.physicalPath.filename().string());
    });
    return entries;
}

std::string suggestAvailableMapId(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &preferredBaseId)
{
    const std::vector<std::string> mapFiles = collectOutdoorMapFileNames(assetFileSystem);
    std::unordered_set<std::string> existingIds;

    for (const std::string &mapFile : mapFiles)
    {
        existingIds.insert(toLowerCopy(std::filesystem::path(mapFile).stem().string()));
    }

    std::string baseId = toLowerCopy(trimCopy(preferredBaseId));

    if (baseId.empty())
    {
        baseId = "out16";
    }

    if (!existingIds.contains(baseId))
    {
        return baseId;
    }

    for (int suffix = 1; suffix < 1000; ++suffix)
    {
        const std::string candidate = baseId + "_" + std::to_string(suffix);

        if (!existingIds.contains(candidate))
        {
            return candidate;
        }
    }

    return baseId + "_copy";
}

bool parseBoolValue(const std::string &value)
{
    const std::string normalized = toLowerCopy(trimCopy(value));
    return normalized == "1" || normalized == "true" || normalized == "yes" || normalized == "on";
}

ImVec4 colorFromRgb(uint32_t rgb)
{
    const float red = static_cast<float>((rgb >> 16) & 0xff) / 255.0f;
    const float green = static_cast<float>((rgb >> 8) & 0xff) / 255.0f;
    const float blue = static_cast<float>(rgb & 0xff) / 255.0f;
    return ImVec4(red, green, blue, 1.0f);
}

enum class UiIcon
{
    None,
    Select,
    Face,
    Terrain,
    Entity,
    Spawn,
    Actor,
    Object,
    Move,
    Rotate,
    World,
    Local,
    Snap,
    Paint,
    Rectangle,
    Fill,
    Raise,
    Lower,
    Flatten,
    Smooth,
    Noise,
    Ramp,
    Clay,
    Grid,
    Wireframe,
    Textured
};

void drawArrowHead(ImDrawList *pDrawList, const ImVec2 &tip, const ImVec2 &direction, float size, ImU32 color)
{
    const float length = std::sqrt(direction.x * direction.x + direction.y * direction.y);

    if (length <= 0.0001f)
    {
        return;
    }

    const ImVec2 normal = {direction.x / length, direction.y / length};
    const ImVec2 perpendicular = {-normal.y, normal.x};
    const ImVec2 base = {tip.x - normal.x * size, tip.y - normal.y * size};
    const ImVec2 left = {base.x + perpendicular.x * size * 0.55f, base.y + perpendicular.y * size * 0.55f};
    const ImVec2 right = {base.x - perpendicular.x * size * 0.55f, base.y - perpendicular.y * size * 0.55f};
    pDrawList->AddTriangleFilled(tip, left, right, color);
}

void drawUiIcon(ImDrawList *pDrawList, UiIcon icon, const ImVec2 &origin, float size, ImU32 color)
{
    const float stroke = std::max(1.4f, size * 0.11f);
    const float x = origin.x;
    const float y = origin.y;
    const float s = size;
    const float cX = x + s * 0.5f;
    const float cY = y + s * 0.5f;

    switch (icon)
    {
    case UiIcon::Select:
        pDrawList->AddTriangle(ImVec2(x + s * 0.18f, y + s * 0.12f), ImVec2(x + s * 0.76f, y + s * 0.52f),
            ImVec2(x + s * 0.44f, y + s * 0.60f), color, stroke);
        pDrawList->AddLine(ImVec2(x + s * 0.44f, y + s * 0.60f), ImVec2(x + s * 0.63f, y + s * 0.90f), color, stroke);
        break;

    case UiIcon::Face:
        pDrawList->AddQuad(
            ImVec2(x + s * 0.22f, y + s * 0.28f),
            ImVec2(x + s * 0.78f, y + s * 0.20f),
            ImVec2(x + s * 0.72f, y + s * 0.78f),
            ImVec2(x + s * 0.16f, y + s * 0.72f),
            color,
            stroke);
        pDrawList->AddLine(ImVec2(x + s * 0.22f, y + s * 0.28f), ImVec2(x + s * 0.72f, y + s * 0.78f), color, stroke);
        break;

    case UiIcon::Terrain:
        pDrawList->AddBezierCubic(
            ImVec2(x + s * 0.08f, y + s * 0.70f),
            ImVec2(x + s * 0.30f, y + s * 0.56f),
            ImVec2(x + s * 0.48f, y + s * 0.30f),
            ImVec2(x + s * 0.64f, y + s * 0.40f),
            color,
            stroke);
        pDrawList->AddBezierCubic(
            ImVec2(x + s * 0.64f, y + s * 0.40f),
            ImVec2(x + s * 0.76f, y + s * 0.46f),
            ImVec2(x + s * 0.84f, y + s * 0.62f),
            ImVec2(x + s * 0.92f, y + s * 0.58f),
            color,
            stroke);
        pDrawList->AddLine(ImVec2(x + s * 0.08f, y + s * 0.70f), ImVec2(x + s * 0.92f, y + s * 0.70f), color, stroke);
        break;

    case UiIcon::Entity:
        pDrawList->AddCircle(ImVec2(cX, y + s * 0.28f), s * 0.14f, color, 0, stroke);
        pDrawList->AddBezierCubic(
            ImVec2(x + s * 0.20f, y + s * 0.86f),
            ImVec2(x + s * 0.28f, y + s * 0.62f),
            ImVec2(x + s * 0.40f, y + s * 0.56f),
            ImVec2(cX, y + s * 0.56f),
            color,
            stroke);
        pDrawList->AddBezierCubic(
            ImVec2(cX, y + s * 0.56f),
            ImVec2(x + s * 0.60f, y + s * 0.56f),
            ImVec2(x + s * 0.72f, y + s * 0.62f),
            ImVec2(x + s * 0.80f, y + s * 0.86f),
            color,
            stroke);
        break;

    case UiIcon::Spawn:
        pDrawList->AddCircle(ImVec2(cX, y + s * 0.40f), s * 0.20f, color, 0, stroke);
        pDrawList->AddLine(ImVec2(cX, y + s * 0.60f), ImVec2(cX, y + s * 0.90f), color, stroke);
        pDrawList->AddLine(ImVec2(cX, y + s * 0.90f), ImVec2(x + s * 0.38f, y + s * 0.72f), color, stroke);
        pDrawList->AddLine(ImVec2(cX, y + s * 0.90f), ImVec2(x + s * 0.62f, y + s * 0.72f), color, stroke);
        break;

    case UiIcon::Actor:
        pDrawList->AddCircle(ImVec2(cX, y + s * 0.26f), s * 0.14f, color, 0, stroke);
        pDrawList->AddLine(ImVec2(cX, y + s * 0.40f), ImVec2(cX, y + s * 0.66f), color, stroke);
        pDrawList->AddLine(ImVec2(x + s * 0.30f, y + s * 0.52f), ImVec2(cX, y + s * 0.62f), color, stroke);
        pDrawList->AddLine(ImVec2(cX, y + s * 0.62f), ImVec2(x + s * 0.70f, y + s * 0.52f), color, stroke);
        pDrawList->AddLine(ImVec2(cX, y + s * 0.66f), ImVec2(x + s * 0.36f, y + s * 0.90f), color, stroke);
        pDrawList->AddLine(ImVec2(cX, y + s * 0.66f), ImVec2(x + s * 0.64f, y + s * 0.90f), color, stroke);
        break;

    case UiIcon::Object:
        pDrawList->AddRect(
            ImVec2(x + s * 0.20f, y + s * 0.28f),
            ImVec2(x + s * 0.80f, y + s * 0.80f),
            color,
            0.0f,
            0,
            stroke);
        pDrawList->AddLine(ImVec2(x + s * 0.20f, y + s * 0.44f), ImVec2(x + s * 0.80f, y + s * 0.44f), color, stroke);
        pDrawList->AddLine(ImVec2(x + s * 0.40f, y + s * 0.28f), ImVec2(x + s * 0.40f, y + s * 0.80f), color, stroke);
        break;

    case UiIcon::Move:
        pDrawList->AddLine(ImVec2(cX, y + s * 0.14f), ImVec2(cX, y + s * 0.86f), color, stroke);
        pDrawList->AddLine(ImVec2(x + s * 0.14f, cY), ImVec2(x + s * 0.86f, cY), color, stroke);
        drawArrowHead(pDrawList, ImVec2(cX, y + s * 0.10f), ImVec2(0.0f, -1.0f), s * 0.10f, color);
        drawArrowHead(pDrawList, ImVec2(cX, y + s * 0.90f), ImVec2(0.0f, 1.0f), s * 0.10f, color);
        drawArrowHead(pDrawList, ImVec2(x + s * 0.10f, cY), ImVec2(-1.0f, 0.0f), s * 0.10f, color);
        drawArrowHead(pDrawList, ImVec2(x + s * 0.90f, cY), ImVec2(1.0f, 0.0f), s * 0.10f, color);
        break;

    case UiIcon::Rotate:
        pDrawList->PathArcTo(ImVec2(cX, cY), s * 0.30f, 3.3f, 7.3f, 24);
        pDrawList->PathStroke(color, 0, stroke);
        drawArrowHead(pDrawList, ImVec2(x + s * 0.24f, y + s * 0.30f), ImVec2(-0.8f, -0.6f), s * 0.10f, color);
        break;

    case UiIcon::World:
        pDrawList->AddCircle(ImVec2(cX, cY), s * 0.34f, color, 0, stroke);
        pDrawList->AddLine(ImVec2(x + s * 0.16f, cY), ImVec2(x + s * 0.84f, cY), color, stroke);
        pDrawList->AddBezierCubic(
            ImVec2(cX, y + s * 0.16f),
            ImVec2(x + s * 0.74f, y + s * 0.30f),
            ImVec2(x + s * 0.74f, y + s * 0.70f),
            ImVec2(cX, y + s * 0.84f),
            color,
            stroke);
        pDrawList->AddBezierCubic(
            ImVec2(cX, y + s * 0.16f),
            ImVec2(x + s * 0.26f, y + s * 0.30f),
            ImVec2(x + s * 0.26f, y + s * 0.70f),
            ImVec2(cX, y + s * 0.84f),
            color,
            stroke);
        break;

    case UiIcon::Local:
        pDrawList->AddTriangle(ImVec2(cX, y + s * 0.16f), ImVec2(x + s * 0.18f, y + s * 0.84f),
            ImVec2(x + s * 0.82f, y + s * 0.84f), color, stroke);
        pDrawList->AddLine(ImVec2(cX, y + s * 0.16f), ImVec2(cX, y + s * 0.84f), color, stroke);
        pDrawList->AddLine(ImVec2(x + s * 0.34f, y + s * 0.60f), ImVec2(x + s * 0.66f, y + s * 0.60f), color, stroke);
        break;

    case UiIcon::Snap:
        pDrawList->AddRect(ImVec2(x + s * 0.28f, y + s * 0.28f), ImVec2(x + s * 0.72f, y + s * 0.72f), color, 0.0f,
            0, stroke);
        pDrawList->AddLine(ImVec2(cX, y + s * 0.10f), ImVec2(cX, y + s * 0.28f), color, stroke);
        pDrawList->AddLine(ImVec2(cX, y + s * 0.72f), ImVec2(cX, y + s * 0.90f), color, stroke);
        pDrawList->AddLine(ImVec2(x + s * 0.10f, cY), ImVec2(x + s * 0.28f, cY), color, stroke);
        pDrawList->AddLine(ImVec2(x + s * 0.72f, cY), ImVec2(x + s * 0.90f, cY), color, stroke);
        break;

    case UiIcon::Paint:
        pDrawList->AddLine(ImVec2(x + s * 0.65f, y + s * 0.18f), ImVec2(x + s * 0.86f, y + s * 0.39f), color, stroke);
        pDrawList->AddRect(ImVec2(x + s * 0.44f, y + s * 0.30f), ImVec2(x + s * 0.67f, y + s * 0.62f), color, 0.0f,
            0, stroke);
        pDrawList->AddTriangle(ImVec2(x + s * 0.22f, y + s * 0.82f), ImVec2(x + s * 0.44f, y + s * 0.30f),
            ImVec2(x + s * 0.56f, y + s * 0.42f), color, stroke);
        break;

    case UiIcon::Rectangle:
        pDrawList->AddRect(
            ImVec2(x + s * 0.18f, y + s * 0.24f),
            ImVec2(x + s * 0.82f, y + s * 0.76f),
            color,
            0.0f,
            0,
            stroke);
        break;

    case UiIcon::Fill:
        pDrawList->AddRectFilled(ImVec2(x + s * 0.20f, y + s * 0.24f), ImVec2(x + s * 0.80f, y + s * 0.78f), color);
        break;

    case UiIcon::Raise:
        pDrawList->AddLine(ImVec2(cX, y + s * 0.18f), ImVec2(cX, y + s * 0.82f), color, stroke);
        drawArrowHead(pDrawList, ImVec2(cX, y + s * 0.14f), ImVec2(0.0f, -1.0f), s * 0.12f, color);
        break;

    case UiIcon::Lower:
        pDrawList->AddLine(ImVec2(cX, y + s * 0.18f), ImVec2(cX, y + s * 0.82f), color, stroke);
        drawArrowHead(pDrawList, ImVec2(cX, y + s * 0.86f), ImVec2(0.0f, 1.0f), s * 0.12f, color);
        break;

    case UiIcon::Flatten:
        pDrawList->AddLine(ImVec2(x + s * 0.16f, y + s * 0.72f), ImVec2(x + s * 0.84f, y + s * 0.72f), color, stroke);
        pDrawList->AddLine(ImVec2(cX, y + s * 0.20f), ImVec2(cX, y + s * 0.54f), color, stroke);
        drawArrowHead(pDrawList, ImVec2(cX, y + s * 0.18f), ImVec2(0.0f, -1.0f), s * 0.10f, color);
        break;

    case UiIcon::Smooth:
        pDrawList->AddBezierCubic(
            ImVec2(x + s * 0.12f, y + s * 0.62f),
            ImVec2(x + s * 0.28f, y + s * 0.32f),
            ImVec2(x + s * 0.46f, y + s * 0.32f),
            ImVec2(cX, y + s * 0.62f),
            color,
            stroke);
        pDrawList->AddBezierCubic(
            ImVec2(cX, y + s * 0.62f),
            ImVec2(x + s * 0.62f, y + s * 0.92f),
            ImVec2(x + s * 0.76f, y + s * 0.92f),
            ImVec2(x + s * 0.88f, y + s * 0.62f),
            color,
            stroke);
        break;

    case UiIcon::Noise:
        pDrawList->AddPolyline(
            std::array<ImVec2, 8> {{
                ImVec2(x + s * 0.10f, y + s * 0.70f),
                ImVec2(x + s * 0.22f, y + s * 0.46f),
                ImVec2(x + s * 0.34f, y + s * 0.76f),
                ImVec2(x + s * 0.46f, y + s * 0.34f),
                ImVec2(x + s * 0.58f, y + s * 0.80f),
                ImVec2(x + s * 0.70f, y + s * 0.50f),
                ImVec2(x + s * 0.82f, y + s * 0.68f),
                ImVec2(x + s * 0.90f, y + s * 0.40f)
            }}.data(),
            8,
            color,
            0,
            stroke);
        break;

    case UiIcon::Ramp:
        pDrawList->AddLine(ImVec2(x + s * 0.14f, y + s * 0.78f), ImVec2(x + s * 0.88f, y + s * 0.78f), color, stroke);
        pDrawList->AddLine(ImVec2(x + s * 0.22f, y + s * 0.78f), ImVec2(x + s * 0.76f, y + s * 0.30f), color, stroke);
        pDrawList->AddLine(ImVec2(x + s * 0.76f, y + s * 0.30f), ImVec2(x + s * 0.76f, y + s * 0.78f), color, stroke);
        break;

    case UiIcon::Clay:
        pDrawList->AddBezierCubic(
            ImVec2(x + s * 0.12f, y + s * 0.70f),
            ImVec2(x + s * 0.26f, y + s * 0.40f),
            ImVec2(x + s * 0.44f, y + s * 0.34f),
            ImVec2(x + s * 0.56f, y + s * 0.58f),
            color,
            stroke);
        pDrawList->AddBezierCubic(
            ImVec2(x + s * 0.56f, y + s * 0.58f),
            ImVec2(x + s * 0.66f, y + s * 0.40f),
            ImVec2(x + s * 0.78f, y + s * 0.36f),
            ImVec2(x + s * 0.88f, y + s * 0.58f),
            color,
            stroke);
        pDrawList->AddLine(ImVec2(x + s * 0.12f, y + s * 0.70f), ImVec2(x + s * 0.88f, y + s * 0.70f), color, stroke);
        break;

    case UiIcon::Grid:
        for (int index = 0; index < 4; ++index)
        {
            const float offset = x + s * (0.18f + 0.18f * static_cast<float>(index));
            pDrawList->AddLine(ImVec2(offset, y + s * 0.12f), ImVec2(offset, y + s * 0.88f), color, stroke);
            pDrawList->AddLine(
                ImVec2(x + s * 0.12f, offset - x + y), ImVec2(x + s * 0.88f, offset - x + y), color, stroke);
        }
        break;

    case UiIcon::Wireframe:
        pDrawList->AddLine(ImVec2(cX, y + s * 0.14f), ImVec2(x + s * 0.82f, y + s * 0.32f), color, stroke);
        pDrawList->AddLine(ImVec2(x + s * 0.82f, y + s * 0.32f), ImVec2(x + s * 0.82f, y + s * 0.72f), color, stroke);
        pDrawList->AddLine(ImVec2(x + s * 0.82f, y + s * 0.72f), ImVec2(cX, y + s * 0.90f), color, stroke);
        pDrawList->AddLine(ImVec2(cX, y + s * 0.90f), ImVec2(x + s * 0.18f, y + s * 0.72f), color, stroke);
        pDrawList->AddLine(ImVec2(x + s * 0.18f, y + s * 0.72f), ImVec2(x + s * 0.18f, y + s * 0.32f), color, stroke);
        pDrawList->AddLine(ImVec2(x + s * 0.18f, y + s * 0.32f), ImVec2(cX, y + s * 0.14f), color, stroke);
        pDrawList->AddLine(ImVec2(cX, y + s * 0.14f), ImVec2(cX, y + s * 0.90f), color, stroke);
        pDrawList->AddLine(ImVec2(x + s * 0.18f, y + s * 0.32f), ImVec2(x + s * 0.82f, y + s * 0.72f), color, stroke);
        pDrawList->AddLine(ImVec2(x + s * 0.82f, y + s * 0.32f), ImVec2(x + s * 0.18f, y + s * 0.72f), color, stroke);
        break;

    case UiIcon::Textured:
        pDrawList->AddRect(ImVec2(x + s * 0.14f, y + s * 0.18f), ImVec2(x + s * 0.86f, y + s * 0.82f), color, 0.0f,
            0, stroke);
        pDrawList->AddBezierCubic(
            ImVec2(x + s * 0.18f, y + s * 0.44f),
            ImVec2(x + s * 0.30f, y + s * 0.34f),
            ImVec2(x + s * 0.42f, y + s * 0.34f),
            ImVec2(x + s * 0.54f, y + s * 0.44f),
            color,
            stroke);
        pDrawList->AddBezierCubic(
            ImVec2(x + s * 0.54f, y + s * 0.44f),
            ImVec2(x + s * 0.66f, y + s * 0.54f),
            ImVec2(x + s * 0.74f, y + s * 0.54f),
            ImVec2(x + s * 0.86f, y + s * 0.44f),
            color,
            stroke);
        pDrawList->AddBezierCubic(
            ImVec2(x + s * 0.18f, y + s * 0.66f),
            ImVec2(x + s * 0.30f, y + s * 0.56f),
            ImVec2(x + s * 0.42f, y + s * 0.56f),
            ImVec2(x + s * 0.54f, y + s * 0.66f),
            color,
            stroke);
        pDrawList->AddBezierCubic(
            ImVec2(x + s * 0.54f, y + s * 0.66f),
            ImVec2(x + s * 0.66f, y + s * 0.76f),
            ImVec2(x + s * 0.74f, y + s * 0.76f),
            ImVec2(x + s * 0.86f, y + s * 0.66f),
            color,
            stroke);
        break;

    case UiIcon::None:
    default:
        break;
    }
}

bool renderTogglePill(const char *pLabel, bool active, const ImVec2 &size = ImVec2(0.0f, 0.0f))
{
    const ImVec4 buttonColor = active ? colorFromRgb(0x56401F) : colorFromRgb(0x1E2328);
    const ImVec4 buttonHovered = active ? colorFromRgb(0x785225) : colorFromRgb(0x252B31);
    const ImVec4 buttonActive = active ? colorFromRgb(0xA86F2E) : colorFromRgb(0x14181C);
    const ImVec4 borderColor = active ? colorFromRgb(0xE0B167) : colorFromRgb(0x323A44);
    const ImVec4 textColor = active ? colorFromRgb(0xFFF0D6) : colorFromRgb(0xBEC6CF);

    ImGui::PushStyleColor(ImGuiCol_Button, buttonColor);
    ImGui::PushStyleColor(ImGuiCol_ButtonHovered, buttonHovered);
    ImGui::PushStyleColor(ImGuiCol_ButtonActive, buttonActive);
    ImGui::PushStyleColor(ImGuiCol_Border, borderColor);
    ImGui::PushStyleColor(ImGuiCol_Text, textColor);
    ImGui::PushStyleVar(ImGuiStyleVar_FrameBorderSize, 1.0f);
    const bool clicked = ImGui::Button(pLabel, size);
    ImGui::PopStyleVar();
    ImGui::PopStyleColor(5);
    return clicked;
}

bool renderIconTogglePill(
    const char *pId,
    const char *pLabel,
    UiIcon icon,
    bool active,
    const ImVec2 &size = ImVec2(0.0f, 0.0f))
{
    ImDrawList *pDrawList = ImGui::GetWindowDrawList();
    const ImGuiStyle &style = ImGui::GetStyle();
    const ImVec2 textSize = ImGui::CalcTextSize(pLabel);
    const float iconSize = 14.0f;
    const float horizontalPadding = style.FramePadding.x + 2.0f;
    const float verticalPadding = style.FramePadding.y;
    const float spacing = 6.0f;
    const ImVec2 buttonSize = size.x > 0.0f || size.y > 0.0f
        ? ImVec2(
            size.x > 0.0f ? size.x : horizontalPadding * 2.0f + iconSize + spacing + textSize.x,
            size.y > 0.0f ? size.y : std::max(iconSize, textSize.y) + verticalPadding * 2.0f)
        : ImVec2(horizontalPadding * 2.0f + iconSize + spacing + textSize.x,
            std::max(iconSize, textSize.y) + verticalPadding * 2.0f);

    ImGui::PushID(pId);
    const bool clicked = ImGui::InvisibleButton("##IconPill", buttonSize);
    const bool hovered = ImGui::IsItemHovered();
    const bool held = ImGui::IsItemActive();
    ImGui::PopID();

    const uint32_t bg = active ? 0x56401F : 0x1E2328;
    const uint32_t bgHover = active ? 0x785225 : 0x252B31;
    const uint32_t bgPressed = active ? 0xA86F2E : 0x14181C;
    const uint32_t border = active ? 0xE0B167 : 0x323A44;
    const uint32_t text = active ? 0xFFF0D6 : 0xBEC6CF;
    const ImU32 bgColor = ImGui::ColorConvertFloat4ToU32(colorFromRgb(held ? bgPressed : hovered ? bgHover : bg));
    const ImU32 borderColor = ImGui::ColorConvertFloat4ToU32(colorFromRgb(border));
    const ImU32 textColor = ImGui::ColorConvertFloat4ToU32(colorFromRgb(text));
    const ImRect rect(ImGui::GetItemRectMin(), ImGui::GetItemRectMax());
    pDrawList->AddRectFilled(rect.Min, rect.Max, bgColor, 4.0f);
    pDrawList->AddRect(rect.Min, rect.Max, borderColor, 4.0f, 0, 1.0f);

    const ImVec2 iconOrigin = {
        rect.Min.x + horizontalPadding,
        rect.Min.y + (buttonSize.y - iconSize) * 0.5f
    };
    drawUiIcon(pDrawList, icon, iconOrigin, iconSize, textColor);
    pDrawList->AddText(
        ImVec2(iconOrigin.x + iconSize + spacing, rect.Min.y + (buttonSize.y - textSize.y) * 0.5f),
        textColor,
        pLabel);
    return clicked;
}

bool renderSecondaryTogglePill(const char *pLabel, bool active, const ImVec2 &size = ImVec2(0.0f, 0.0f))
{
    const ImVec4 buttonColor = active ? colorFromRgb(0x232931) : colorFromRgb(0x13171B);
    const ImVec4 buttonHovered = active ? colorFromRgb(0x2A313B) : colorFromRgb(0x161A1E);
    const ImVec4 buttonActive = active ? colorFromRgb(0x313A45) : colorFromRgb(0x101317);
    const ImVec4 borderColor = active ? colorFromRgb(0x4A5664) : colorFromRgb(0x1F252C);
    const ImVec4 textColor = active ? colorFromRgb(0xC5CED8) : colorFromRgb(0x79828D);

    ImGui::PushStyleColor(ImGuiCol_Button, buttonColor);
    ImGui::PushStyleColor(ImGuiCol_ButtonHovered, buttonHovered);
    ImGui::PushStyleColor(ImGuiCol_ButtonActive, buttonActive);
    ImGui::PushStyleColor(ImGuiCol_Border, borderColor);
    ImGui::PushStyleColor(ImGuiCol_Text, textColor);
    ImGui::PushStyleVar(ImGuiStyleVar_FrameBorderSize, 1.0f);
    const bool clicked = ImGui::Button(pLabel, size);
    ImGui::PopStyleVar();
    ImGui::PopStyleColor(5);
    return clicked;
}

bool renderSecondaryIconTogglePill(
    const char *pId,
    const char *pLabel,
    UiIcon icon,
    bool active,
    const ImVec2 &size = ImVec2(0.0f, 0.0f))
{
    ImDrawList *pDrawList = ImGui::GetWindowDrawList();
    const ImGuiStyle &style = ImGui::GetStyle();
    const ImVec2 textSize = ImGui::CalcTextSize(pLabel);
    const float iconSize = 14.0f;
    const float horizontalPadding = style.FramePadding.x + 2.0f;
    const float verticalPadding = style.FramePadding.y;
    const float spacing = 6.0f;
    const ImVec2 buttonSize = size.x > 0.0f || size.y > 0.0f
        ? ImVec2(
            size.x > 0.0f ? size.x : horizontalPadding * 2.0f + iconSize + spacing + textSize.x,
            size.y > 0.0f ? size.y : std::max(iconSize, textSize.y) + verticalPadding * 2.0f)
        : ImVec2(horizontalPadding * 2.0f + iconSize + spacing + textSize.x,
            std::max(iconSize, textSize.y) + verticalPadding * 2.0f);

    ImGui::PushID(pId);
    const bool clicked = ImGui::InvisibleButton("##SecondaryIconPill", buttonSize);
    const bool hovered = ImGui::IsItemHovered();
    const bool held = ImGui::IsItemActive();
    ImGui::PopID();

    const uint32_t bg = active ? 0x232931 : 0x13171B;
    const uint32_t bgHover = active ? 0x2A313B : 0x161A1E;
    const uint32_t bgPressed = active ? 0x313A45 : 0x101317;
    const uint32_t border = active ? 0x4A5664 : 0x1F252C;
    const uint32_t text = active ? 0xC5CED8 : 0x79828D;
    const ImU32 bgColor = ImGui::ColorConvertFloat4ToU32(colorFromRgb(held ? bgPressed : hovered ? bgHover : bg));
    const ImU32 borderColor = ImGui::ColorConvertFloat4ToU32(colorFromRgb(border));
    const ImU32 textColor = ImGui::ColorConvertFloat4ToU32(colorFromRgb(text));
    const ImRect rect(ImGui::GetItemRectMin(), ImGui::GetItemRectMax());
    pDrawList->AddRectFilled(rect.Min, rect.Max, bgColor, 4.0f);
    pDrawList->AddRect(rect.Min, rect.Max, borderColor, 4.0f, 0, 1.0f);

    const ImVec2 iconOrigin = {
        rect.Min.x + horizontalPadding,
        rect.Min.y + (buttonSize.y - iconSize) * 0.5f
    };
    drawUiIcon(pDrawList, icon, iconOrigin, iconSize, textColor);
    pDrawList->AddText(
        ImVec2(iconOrigin.x + iconSize + spacing, rect.Min.y + (buttonSize.y - textSize.y) * 0.5f),
        textColor,
        pLabel);
    return clicked;
}

UiIcon selectionKindIcon(EditorSelectionKind kind)
{
    switch (kind)
    {
    case EditorSelectionKind::Terrain:
        return UiIcon::Terrain;

    case EditorSelectionKind::InteractiveFace:
        return UiIcon::Face;

    case EditorSelectionKind::Entity:
        return UiIcon::Entity;

    case EditorSelectionKind::Spawn:
        return UiIcon::Spawn;

    case EditorSelectionKind::Actor:
        return UiIcon::Actor;

    case EditorSelectionKind::SpriteObject:
        return UiIcon::Object;

    case EditorSelectionKind::Light:
        return UiIcon::Entity;

    case EditorSelectionKind::Door:
        return UiIcon::Face;

    case EditorSelectionKind::ModelInstance:
    case EditorSelectionKind::Mm9ScriptedObject:
    case EditorSelectionKind::Mm9WorldModel:
    case EditorSelectionKind::Mm9DatPolygon:
    case EditorSelectionKind::Mm9MaterialTexture:
    case EditorSelectionKind::Mm9RawObject:
    case EditorSelectionKind::Mm9EventObject:
    case EditorSelectionKind::Mm9Mechanism:
    case EditorSelectionKind::Mm9EventScript:
        return UiIcon::Object;

    case EditorSelectionKind::None:
    default:
        return UiIcon::Select;
    }
}

UiIcon terrainPaintModeIcon(EditorTerrainPaintMode mode)
{
    switch (mode)
    {
    case EditorTerrainPaintMode::Brush:
        return UiIcon::Paint;

    case EditorTerrainPaintMode::Rectangle:
        return UiIcon::Rectangle;

    case EditorTerrainPaintMode::Fill:
    default:
        return UiIcon::Fill;
    }
}

UiIcon terrainSculptModeIcon(EditorTerrainSculptMode mode)
{
    switch (mode)
    {
    case EditorTerrainSculptMode::Raise:
        return UiIcon::Raise;

    case EditorTerrainSculptMode::Lower:
        return UiIcon::Lower;

    case EditorTerrainSculptMode::Flatten:
        return UiIcon::Flatten;

    case EditorTerrainSculptMode::Smooth:
        return UiIcon::Smooth;

    case EditorTerrainSculptMode::Noise:
        return UiIcon::Noise;

    case EditorTerrainSculptMode::Ramp:
    default:
        return UiIcon::Ramp;
    }
}

bool matchesSceneFilter(const char *pFilterText, const std::string &label)
{
    const std::string filter = toLowerCopy(trimCopy(pFilterText != nullptr ? pFilterText : ""));

    if (filter.empty())
    {
        return true;
    }

    return toLowerCopy(label).find(filter) != std::string::npos;
}

std::string mm9Vec3Text(const EditorMm9Vec3 &value)
{
    char buffer[128] = {};
    std::snprintf(buffer, sizeof(buffer), "%.3f, %.3f, %.3f", value.x, value.y, value.z);
    return buffer;
}

std::string mm9DatVec3Text(const Game::Mm9DatVec3 &value)
{
    char buffer[128] = {};
    std::snprintf(buffer, sizeof(buffer), "%.3f, %.3f, %.3f", value.x, value.y, value.z);
    return buffer;
}

struct Mm9MovableWorldModelCandidate
{
    size_t sourceModelIndex = 0;
    std::string sourceName;
    EditorMm9Vec3 worldTranslationLt;
    float distanceLt = 0.0f;
};

float mm9DistanceLt(const std::vector<float> &pointLt, const EditorMm9Vec3 &positionLt)
{
    if (pointLt.size() < 3)
    {
        return 0.0f;
    }

    const float deltaX = pointLt[0] - positionLt.x;
    const float deltaY = pointLt[1] - positionLt.y;
    const float deltaZ = pointLt[2] - positionLt.z;
    return std::sqrt(deltaX * deltaX + deltaY * deltaY + deltaZ * deltaZ);
}

std::vector<Mm9MovableWorldModelCandidate> nearestMm9MovableWorldModels(
    const EditorMm9DatWorldSidecar &datWorld,
    const std::vector<float> &pointLt,
    size_t maxCandidates)
{
    std::vector<Mm9MovableWorldModelCandidate> candidates;

    if (pointLt.size() < 3 || maxCandidates == 0)
    {
        return candidates;
    }

    for (const EditorMm9DatWorldModelSummary &worldModel : datWorld.worldModels)
    {
        if (!worldModel.roles.movable)
        {
            continue;
        }

        Mm9MovableWorldModelCandidate candidate = {};
        candidate.sourceModelIndex = worldModel.sourceModelIndex;
        candidate.sourceName = worldModel.sourceName;
        candidate.worldTranslationLt = worldModel.worldTranslationLt;
        candidate.distanceLt = mm9DistanceLt(pointLt, worldModel.worldTranslationLt);
        candidates.push_back(std::move(candidate));
    }

    std::sort(
        candidates.begin(),
        candidates.end(),
        [](const Mm9MovableWorldModelCandidate &left, const Mm9MovableWorldModelCandidate &right)
        {
            return left.distanceLt < right.distanceLt;
        });

    if (candidates.size() > maxCandidates)
    {
        candidates.resize(maxCandidates);
    }

    return candidates;
}

std::string hex32Text(uint32_t value)
{
    char buffer[32] = {};
    std::snprintf(buffer, sizeof(buffer), "0x%08X", static_cast<unsigned>(value));
    return buffer;
}

std::string hex16Text(uint16_t value)
{
    char buffer[32] = {};
    std::snprintf(buffer, sizeof(buffer), "0x%04X", static_cast<unsigned>(value));
    return buffer;
}

void appendMm9SurfaceFlagName(std::vector<std::string> &names, uint32_t flags, uint32_t bit, const char *pName)
{
    if ((flags & bit) != 0)
    {
        names.push_back(pName);
    }
}

std::string mm9SurfaceFlagsText(uint32_t flags)
{
    std::vector<std::string> names;
    appendMm9SurfaceFlagName(names, flags, Game::Mm9DatSurfaceFlagSolid, "SURF_SOLID");
    appendMm9SurfaceFlagName(names, flags, Game::Mm9DatSurfaceFlagNonexistent, "SURF_NONEXISTENT");
    appendMm9SurfaceFlagName(names, flags, Game::Mm9DatSurfaceFlagInvisible, "SURF_INVISIBLE");
    appendMm9SurfaceFlagName(names, flags, Game::Mm9DatSurfaceFlagTransparent, "SURF_TRANSPARENT");
    appendMm9SurfaceFlagName(names, flags, Game::Mm9DatSurfaceFlagSky, "SURF_SKY");
    appendMm9SurfaceFlagName(names, flags, Game::Mm9DatSurfaceFlagPortal, "SURF_PORTAL");
    appendMm9SurfaceFlagName(names, flags, Game::Mm9DatSurfaceFlagPhysicsBlocker, "SURF_PHYSICSBLOCKER");
    appendMm9SurfaceFlagName(names, flags, Game::Mm9DatSurfaceFlagVisibilityBlocker, "SURF_VISBLOCKER");
    appendMm9SurfaceFlagName(names, flags, Game::Mm9DatSurfaceFlagNotAStep, "SURF_NOTASTEP");

    std::string text = hex32Text(flags);

    if (!names.empty())
    {
        text += " (";
        text += names.front();

        for (size_t index = 1; index < names.size(); ++index)
        {
            text += ", " + names[index];
        }

        text += ")";
    }

    return text;
}

std::string mm9WorldModelRolesText(const EditorMm9DatWorldModelRoles &roles)
{
    std::vector<std::string> roleNames;

    if (roles.visible)
    {
        roleNames.push_back("visible");
    }
    if (roles.terrain)
    {
        roleNames.push_back("terrain");
    }
    if (roles.physicsBsp)
    {
        roleNames.push_back("physics_bsp");
    }
    if (roles.visBsp)
    {
        roleNames.push_back("vis_bsp");
    }
    if (roles.sky)
    {
        roleNames.push_back("sky");
    }
    if (roles.water)
    {
        roleNames.push_back("water");
    }
    if (roles.triggerOrVolume)
    {
        roleNames.push_back("trigger_or_volume");
    }
    if (roles.movable)
    {
        roleNames.push_back("movable");
    }

    if (roleNames.empty())
    {
        return "<none>";
    }

    std::string text = roleNames.front();

    for (size_t index = 1; index < roleNames.size(); ++index)
    {
        text += ", " + roleNames[index];
    }

    return text;
}

Game::Mm9DatModelRenderRole mm9ModelRenderRoleFromSidecarModel(const EditorMm9DatWorldModelSummary &model)
{
    Game::Mm9DatModelRenderRole role = {};
    role.sourceModelIndex = model.sourceModelIndex;
    role.visible = model.roles.visible;
    role.terrain = model.roles.terrain;
    role.physicsBsp = model.roles.physicsBsp;
    role.visBsp = model.roles.visBsp;
    role.sky = model.roles.sky;
    role.water = model.roles.water;
    role.triggerOrVolume = model.roles.triggerOrVolume;
    role.movable = model.roles.movable;
    return role;
}

std::vector<Game::Mm9DatModelRenderRole> mm9ModelRenderRolesFromSidecar(
    const EditorMm9DatWorldSidecar &datWorld)
{
    std::vector<Game::Mm9DatModelRenderRole> roles;
    roles.reserve(datWorld.worldModels.size());

    for (const EditorMm9DatWorldModelSummary &model : datWorld.worldModels)
    {
        roles.push_back(mm9ModelRenderRoleFromSidecarModel(model));
    }

    return roles;
}

bool mm9DatFilterEntryShouldRenderInDefaultEditorView(const Game::Mm9DatRenderFilterEntry &filterEntry)
{
    const bool renderable =
        (filterEntry.flags
            & (Game::Mm9DatRenderFilterVisual
                | Game::Mm9DatRenderFilterSky
                | Game::Mm9DatRenderFilterWater
                | Game::Mm9DatRenderFilterTerrain
                | Game::Mm9DatRenderFilterPhysics
                | Game::Mm9DatRenderFilterMovable)) != 0;
    const bool hidden =
        (filterEntry.flags
            & (Game::Mm9DatRenderFilterInvisible
                | Game::Mm9DatRenderFilterWaterVolume
                | Game::Mm9DatRenderFilterRail
                | Game::Mm9DatRenderFilterVisibility
                | Game::Mm9DatRenderFilterTrigger)) != 0;
    return renderable && !hidden;
}

std::string boolText(bool value)
{
    return value ? "true" : "false";
}

struct ReadOnlyTextPreview
{
    std::filesystem::path path;
    std::string text;
    uintmax_t fileSizeBytes = 0;
    bool exists = false;
    bool loaded = false;
    bool truncated = false;
};

std::filesystem::path resolveMm9LevelRelativePath(
    const EditorDocument &document,
    const std::string &path)
{
    if (path.empty())
    {
        return {};
    }

    const std::filesystem::path parsedPath(path);

    if (parsedPath.is_absolute())
    {
        return parsedPath;
    }

    return (document.scenePhysicalPath().parent_path() / parsedPath).lexically_normal();
}

ReadOnlyTextPreview loadReadOnlyTextPreview(
    const std::filesystem::path &path,
    size_t maxBytes = 200 * 1024)
{
    ReadOnlyTextPreview preview = {};
    preview.path = path;
    preview.exists = !path.empty() && std::filesystem::exists(path);

    if (!preview.exists)
    {
        return preview;
    }

    std::error_code errorCode;
    preview.fileSizeBytes = std::filesystem::file_size(path, errorCode);

    if (errorCode)
    {
        preview.fileSizeBytes = 0;
    }

    std::ifstream input(path, std::ios::binary);

    if (!input)
    {
        return preview;
    }

    std::string text;
    const size_t readBytes = preview.fileSizeBytes == 0
        ? maxBytes
        : std::min<size_t>(static_cast<size_t>(preview.fileSizeBytes), maxBytes);
    text.resize(readBytes);

    if (readBytes > 0)
    {
        input.read(text.data(), static_cast<std::streamsize>(readBytes));
        text.resize(static_cast<size_t>(input.gcount()));
    }

    preview.loaded = true;
    preview.truncated = preview.fileSizeBytes > text.size();
    preview.text = std::move(text);
    return preview;
}

void appendMm9DtxFlagName(std::vector<std::string> &names, int flags, int bit, const char *pName)
{
    if ((flags & bit) != 0)
    {
        names.push_back(pName);
    }
}

std::string mm9DtxFlagsText(int flags)
{
    std::vector<std::string> names;
    appendMm9DtxFlagName(names, flags, 1 << 0, "FULLBRITE");
    appendMm9DtxFlagName(names, flags, 1 << 1, "PREFER16BIT");
    appendMm9DtxFlagName(names, flags, 1 << 2, "MIPSALLOCED");
    appendMm9DtxFlagName(names, flags, 1 << 3, "SECTIONSFIXED");
    appendMm9DtxFlagName(names, flags, 1 << 6, "NOSYSCACHE");
    appendMm9DtxFlagName(names, flags, 1 << 7, "PREFER4444");
    appendMm9DtxFlagName(names, flags, 1 << 8, "PREFER5551");
    appendMm9DtxFlagName(names, flags, 1 << 9, "32BITSYSCOPY");
    appendMm9DtxFlagName(names, flags, 1 << 10, "CUBEMAP");
    appendMm9DtxFlagName(names, flags, 1 << 11, "BUMPMAP");
    appendMm9DtxFlagName(names, flags, 1 << 12, "LUMBUMPMAP");

    std::string text = std::to_string(flags);

    if (!names.empty())
    {
        text += " (";
        text += names.front();

        for (size_t index = 1; index < names.size(); ++index)
        {
            text += ", " + names[index];
        }

        text += ")";
    }

    return text;
}

std::string mm9DtxExtraBytesText(const EditorMm9DtxHeader &header)
{
    std::ostringstream stream;
    stream << "[";

    for (size_t index = 0; index < header.extraBytes.size(); ++index)
    {
        if (index > 0)
        {
            stream << ", ";
        }

        stream << header.extraBytes[index];
    }

    stream << "]";
    return stream.str();
}

const EditorMm9RawObjectProperty *findMm9RawObjectProperty(
    const EditorMm9RawObject &object,
    const std::string &propertyName)
{
    for (const EditorMm9RawObjectProperty &property : object.properties)
    {
        if (toLowerCopy(property.name) == toLowerCopy(propertyName))
        {
            return &property;
        }
    }

    return nullptr;
}

std::string mm9RawObjectPropertyValue(
    const EditorMm9RawObject &object,
    const std::string &propertyName)
{
    const EditorMm9RawObjectProperty *pProperty = findMm9RawObjectProperty(object, propertyName);

    if (pProperty == nullptr)
    {
        return "<none>";
    }

    return pProperty->valueJson.empty() ? std::string("<empty>") : pProperty->valueJson;
}

std::string joinMm9Classifications(const std::vector<std::string> &classifications)
{
    if (classifications.empty())
    {
        return "<none>";
    }

    std::string text = classifications.front();

    for (size_t index = 1; index < classifications.size(); ++index)
    {
        text += ", " + classifications[index];
    }

    return text;
}

std::string mm9FloatVectorText(const std::vector<float> &values)
{
    if (values.empty())
    {
        return "<none>";
    }

    std::ostringstream stream;
    stream << "[";

    for (size_t index = 0; index < values.size(); ++index)
    {
        if (index > 0)
        {
            stream << ", ";
        }

        stream << values[index];
    }

    stream << "]";
    return stream.str();
}

std::string mm9OptionalBoolText(bool value, bool present)
{
    if (!present)
    {
        return "<unknown>";
    }

    return value ? "true" : "false";
}

bool isMm9ScriptedModelInstanceForEditor(
    const EditorDocument &document,
    const Game::OutdoorSceneModelInstance &modelInstance,
    const Mm9ModelInstanceActorSourceLookup *pActorSourceLookup)
{
    if (document.kind() != EditorDocument::Kind::Outdoor
        || toLowerCopy(document.outdoorGeometry().worldId) != "mm9")
    {
        return false;
    }

    if (canResolveMm9ModelInstanceActorSource(modelInstance, pActorSourceLookup))
    {
        return true;
    }

    return !modelInstance.sourceModel.empty() && toLowerCopy(modelInstance.sourceClass) != "prop";
}

bool indoorRoomMatchesFilter(std::optional<uint16_t> roomId, int filterRoomId)
{
    if (filterRoomId < 0)
    {
        return true;
    }

    return roomId.has_value() && *roomId == static_cast<uint16_t>(filterRoomId);
}

bool indoorRoomListMatchesFilter(const std::vector<uint16_t> &roomIds, int filterRoomId)
{
    if (filterRoomId < 0)
    {
        return true;
    }

    return std::find(roomIds.begin(), roomIds.end(), static_cast<uint16_t>(filterRoomId)) != roomIds.end();
}

std::optional<uint16_t> findIndoorRoomIdForPoint(
    const Game::IndoorMapData &indoorGeometry,
    int x,
    int y,
    int z,
    Game::IndoorFaceGeometryCache &geometryCache)
{
    const std::optional<int16_t> sectorId = Game::findIndoorSectorForPoint(
        indoorGeometry,
        indoorGeometry.vertices,
        {static_cast<float>(x), static_cast<float>(y), static_cast<float>(z)},
        &geometryCache);

    if (!sectorId.has_value() || *sectorId < 0)
    {
        return std::nullopt;
    }

    return static_cast<uint16_t>(*sectorId);
}

int snapIndoorActorZToFloor(const Game::IndoorMapData &indoorGeometry, int x, int y, int z)
{
    Game::IndoorFaceGeometryCache geometryCache(indoorGeometry.faces.size());
    const std::optional<int16_t> sectorId = Game::findIndoorSectorForPoint(
        indoorGeometry,
        indoorGeometry.vertices,
        {static_cast<float>(x), static_cast<float>(y), static_cast<float>(z)},
        &geometryCache);
    const Game::IndoorFloorSample floor = Game::sampleIndoorFloor(
        indoorGeometry,
        indoorGeometry.vertices,
        static_cast<float>(x),
        static_cast<float>(y),
        static_cast<float>(z),
        131072.0f,
        0.0f,
        sectorId,
        nullptr,
        &geometryCache);

    if (!floor.hasFloor || floor.height <= static_cast<float>(z))
    {
        return z;
    }

    return static_cast<int>(std::lround(floor.height));
}

void assignIndoorEntityToSector(Game::IndoorMapData &indoorGeometry, size_t entityIndex)
{
    if (entityIndex >= indoorGeometry.entities.size())
    {
        return;
    }

    const uint16_t clampedEntityIndex = static_cast<uint16_t>(std::min<size_t>(entityIndex, 65535));

    for (Game::IndoorSector &sector : indoorGeometry.sectors)
    {
        sector.decorationIds.erase(
            std::remove(sector.decorationIds.begin(), sector.decorationIds.end(), clampedEntityIndex),
            sector.decorationIds.end());
    }

    const Game::IndoorEntity &entity = indoorGeometry.entities[entityIndex];
    Game::IndoorFaceGeometryCache geometryCache(indoorGeometry.faces.size());
    const std::optional<uint16_t> roomId =
        findIndoorRoomIdForPoint(indoorGeometry, entity.x, entity.y, entity.z, geometryCache);

    if (!roomId.has_value() || *roomId >= indoorGeometry.sectors.size())
    {
        return;
    }

    std::vector<uint16_t> &decorationIds = indoorGeometry.sectors[*roomId].decorationIds;

    if (std::find(decorationIds.begin(), decorationIds.end(), clampedEntityIndex) == decorationIds.end())
    {
        decorationIds.push_back(clampedEntityIndex);
    }
}

std::string indoorFaceOutlinerLabel(const Game::IndoorFace &face, size_t faceIndex)
{
    const bool isPortal = face.isPortal || Game::hasFaceAttribute(face.attributes, Game::FaceAttribute::IsPortal);
    std::string label = "Face " + std::to_string(faceIndex);

    if (isPortal)
    {
        label += " · Portal " + std::to_string(face.roomNumber) + "↔" + std::to_string(face.roomBehindNumber);
    }
    else
    {
        label += " · Room " + std::to_string(face.roomNumber);
    }

    const std::string textureName = trimCopy(face.textureName);

    if (!textureName.empty())
    {
        label += " · " + textureName;
    }

    if (face.cogTriggered != 0)
    {
        label += " · evt " + std::to_string(face.cogTriggered);
    }

    return label;
}

std::string indoorEntityOutlinerLabel(
    const Game::IndoorEntity &entity,
    size_t entityIndex,
    std::optional<uint16_t> roomId)
{
    std::string label = entity.name.empty() ? "Entity " + std::to_string(entityIndex) : entity.name;
    label += " · " + (roomId.has_value() ? "Room " + std::to_string(*roomId) : std::string("Room ?"));

    if (entity.eventIdPrimary != 0)
    {
        label += " · evt " + std::to_string(entity.eventIdPrimary);
    }

    return label;
}

std::string indoorLightOutlinerLabel(size_t lightIndex, std::optional<uint16_t> roomId)
{
    std::string label = "Light " + std::to_string(lightIndex);
    label += " · " + (roomId.has_value() ? "Room " + std::to_string(*roomId) : std::string("Room ?"));
    return label;
}

std::string indoorSpawnOutlinerLabel(const Game::IndoorSpawn &spawn, size_t spawnIndex, std::optional<uint16_t> roomId)
{
    std::string label = "Spawn " + std::to_string(spawnIndex);
    label += " · " + (roomId.has_value() ? "Room " + std::to_string(*roomId) : std::string("Room ?"));
    label += " · type " + std::to_string(spawn.typeId);
    label += " · idx " + std::to_string(spawn.index);
    return label;
}

std::string indoorDoorOutlinerLabel(
    const Game::IndoorSceneDoor &door,
    const std::vector<uint16_t> &affectedRoomIds)
{
    std::string label = "Door " + std::to_string(door.doorIndex);
    label += " · id " + std::to_string(door.door.doorId);
    label += " · rooms " + formatIndoorRoomList(affectedRoomIds);
    label += " · faces " + std::to_string(door.door.faceIds.size());
    return label;
}

void beginToolbarCard(const char *pTitle, float width = 0.0f)
{
    ImGui::PushStyleColor(ImGuiCol_ChildBg, colorFromRgb(0x171B1F));
    ImGui::PushStyleColor(ImGuiCol_Border, colorFromRgb(0x303741));
    ImGui::BeginChild(pTitle, ImVec2(width, 0.0f), ImGuiChildFlags_Borders, ImGuiWindowFlags_NoScrollbar);
    ImGui::PushStyleColor(ImGuiCol_Text, colorFromRgb(0x97A0AC));
    ImGui::TextUnformatted(pTitle);
    ImGui::PopStyleColor();
    ImGui::Dummy(ImVec2(0.0f, 1.0f));
}

void endToolbarCard()
{
    ImGui::EndChild();
    ImGui::PopStyleColor(2);
}

void renderStatusPill(const char *pLabel, uint32_t textColorRgb, uint32_t borderColorRgb, uint32_t fillColorRgb)
{
    ImGui::PushStyleColor(ImGuiCol_Button, colorFromRgb(fillColorRgb));
    ImGui::PushStyleColor(ImGuiCol_ButtonHovered, colorFromRgb(fillColorRgb));
    ImGui::PushStyleColor(ImGuiCol_ButtonActive, colorFromRgb(fillColorRgb));
    ImGui::PushStyleColor(ImGuiCol_Border, colorFromRgb(borderColorRgb));
    ImGui::PushStyleColor(ImGuiCol_Text, colorFromRgb(textColorRgb));
    ImGui::PushStyleVar(ImGuiStyleVar_FrameBorderSize, 1.0f);
    ImGui::Button(pLabel);
    ImGui::PopStyleVar();
    ImGui::PopStyleColor(5);
}

void renderToolbarSubLabel(const char *pLabel)
{
    ImGui::PushStyleColor(ImGuiCol_Text, colorFromRgb(0x8C95A0));
    ImGui::TextUnformatted(pLabel);
    ImGui::PopStyleColor();
}

std::string activeEditorContextSummary(const EditorSession &session, const EditorOutdoorViewport &viewport)
{
    if (session.hasDocument() && session.document().kind() == EditorDocument::Kind::Indoor)
    {
        if (viewport.placementKind() == EditorSelectionKind::InteractiveFace)
        {
            return "Indoor  ·  Face";
        }

        if (viewport.placementKind() == EditorSelectionKind::Actor)
        {
            return "Indoor  ·  Actor Place";
        }

        if (viewport.placementKind() == EditorSelectionKind::SpriteObject)
        {
            return "Indoor  ·  Object Place";
        }

        return "Indoor  ·  Select";
    }

    if (viewport.placementKind() == EditorSelectionKind::Terrain)
    {
        if (session.terrainSculptEnabled())
        {
            const char *pTool = "Raise";

            switch (session.terrainSculptMode())
            {
            case EditorTerrainSculptMode::Lower:
                pTool = "Lower";
                break;
            case EditorTerrainSculptMode::Flatten:
                pTool = "Flatten";
                break;
            case EditorTerrainSculptMode::Smooth:
                pTool = "Smooth";
                break;
            case EditorTerrainSculptMode::Noise:
                pTool = "Noise";
                break;
            case EditorTerrainSculptMode::Ramp:
                pTool = "Ramp";
                break;
            case EditorTerrainSculptMode::Raise:
            default:
                break;
            }

            return std::string("Terrain  ·  Sculpt  ·  ") + pTool;
        }

        return "Terrain  ·  Paint";
    }

    const char *pMode = "Select";

    switch (viewport.placementKind())
    {
    case EditorSelectionKind::InteractiveFace:
        pMode = "Face";
        break;
    case EditorSelectionKind::BModel:
        pMode = "BModel Place";
        break;
    case EditorSelectionKind::Entity:
        pMode = "Entity Place";
        break;
    case EditorSelectionKind::Spawn:
        pMode = "Spawn Place";
        break;
    case EditorSelectionKind::Actor:
        pMode = "Actor Place";
        break;
    case EditorSelectionKind::SpriteObject:
        pMode = "Object Place";
        break;
    case EditorSelectionKind::Mm9WorldModel:
        pMode = "DAT World Model";
        break;
    case EditorSelectionKind::Mm9DatPolygon:
        pMode = "DAT Polygon";
        break;
    case EditorSelectionKind::Mm9MaterialTexture:
        pMode = "DTX Texture";
        break;
    case EditorSelectionKind::Mm9RawObject:
        pMode = "DAT Raw Object";
        break;
    case EditorSelectionKind::Mm9EventObject:
        pMode = "MM9 Event Object";
        break;
    case EditorSelectionKind::Mm9Mechanism:
        pMode = "MM9 Mechanism";
        break;
    case EditorSelectionKind::Mm9EventScript:
        pMode = "MM9 Script";
        break;
    case EditorSelectionKind::None:
    default:
        break;
    }

    const char *pTransform = viewport.transformGizmoMode() == EditorOutdoorViewport::TransformGizmoMode::Rotate
        ? "Rotate"
        : "Move";
    const char *pSpace = viewport.transformSpaceMode() == EditorOutdoorViewport::TransformSpaceMode::Local
        ? "Local"
        : "World";
    return std::string(pMode) + "  ·  " + pTransform + "  ·  " + pSpace;
}

std::string inspectorFieldId(const char *pLabel);
void beginInspectorFieldRow(const char *pLabel);

std::string actorDisplayLabel(
    const Game::MonsterTable *pMonsterTable,
    const Game::MapDeltaActor &actor,
    size_t actorIndex)
{
    if (pMonsterTable != nullptr)
    {
        const std::string resolvedName = Game::resolveMapDeltaActorName(*pMonsterTable, actor);

        if (!resolvedName.empty())
        {
            return resolvedName;
        }
    }

    if (actor.uniqueNameIndex > 0)
    {
        return "Unique Actor " + std::to_string(actor.uniqueNameIndex);
    }

    if (actor.monsterInfoId > 0)
    {
        return "Monster Info " + std::to_string(actor.monsterInfoId);
    }

    if (actor.monsterId > 0)
    {
        return "Monster " + std::to_string(actor.monsterId);
    }

    return "Actor " + std::to_string(actorIndex);
}

std::string actorMonsterTemplateLabel(const Game::MonsterTable *pMonsterTable, const Game::MapDeltaActor &actor)
{
    if (pMonsterTable == nullptr)
    {
        return {};
    }

    const Game::MonsterTable::MonsterDisplayNameEntry *pDisplayEntry =
        pMonsterTable->findDisplayEntryById(actor.monsterInfoId);

    if (pDisplayEntry != nullptr && !pDisplayEntry->displayName.empty())
    {
        return pDisplayEntry->displayName;
    }

    const int16_t effectiveMonsterId = actor.monsterInfoId > 0 ? actor.monsterInfoId : actor.monsterId;
    const Game::MonsterTable::MonsterStatsEntry *pStats = pMonsterTable->findStatsById(effectiveMonsterId);

    if (pStats != nullptr && !pStats->name.empty())
    {
        return pStats->name;
    }

    return {};
}

std::string hostilityTypeLabel(uint8_t hostilityType)
{
    if (hostilityType == 0)
    {
        return "Auto/Default (0)";
    }

    return "Raw " + std::to_string(hostilityType);
}

EditorBModelSourceTransform sourceTransformFromBModel(const Game::OutdoorBModel &bmodel)
{
    EditorBModelSourceTransform transform = {};

    if (bmodel.vertices.empty())
    {
        transform.originX = static_cast<float>(bmodel.boundingCenterX);
        transform.originY = static_cast<float>(bmodel.boundingCenterY);
        transform.originZ = static_cast<float>(bmodel.boundingCenterZ);
        return transform;
    }

    float minX = std::numeric_limits<float>::max();
    float minY = std::numeric_limits<float>::max();
    float minZ = std::numeric_limits<float>::max();
    float maxX = std::numeric_limits<float>::lowest();
    float maxY = std::numeric_limits<float>::lowest();
    float maxZ = std::numeric_limits<float>::lowest();

    for (const Game::OutdoorBModelVertex &vertex : bmodel.vertices)
    {
        minX = std::min(minX, static_cast<float>(vertex.x));
        minY = std::min(minY, static_cast<float>(vertex.y));
        minZ = std::min(minZ, static_cast<float>(vertex.z));
        maxX = std::max(maxX, static_cast<float>(vertex.x));
        maxY = std::max(maxY, static_cast<float>(vertex.y));
        maxZ = std::max(maxZ, static_cast<float>(vertex.z));
    }

    transform.originX = (minX + maxX) * 0.5f;
    transform.originY = (minY + maxY) * 0.5f;
    transform.originZ = (minZ + maxZ) * 0.5f;
    return transform;
}

std::array<float, 3> rotateVectorByEulerDegrees(
    const std::array<float, 3> &vector,
    float rotationXDegrees,
    float rotationYDegrees,
    float rotationZDegrees)
{
    const float rotationXRadians = rotationXDegrees * 3.14159265358979323846f / 180.0f;
    const float rotationYRadians = rotationYDegrees * 3.14159265358979323846f / 180.0f;
    const float rotationZRadians = rotationZDegrees * 3.14159265358979323846f / 180.0f;
    const float cosX = std::cos(rotationXRadians);
    const float sinX = std::sin(rotationXRadians);
    const float cosY = std::cos(rotationYRadians);
    const float sinY = std::sin(rotationYRadians);
    const float cosZ = std::cos(rotationZRadians);
    const float sinZ = std::sin(rotationZRadians);
    const float rotatedXY = vector[1] * cosX - vector[2] * sinX;
    const float rotatedXZ = vector[1] * sinX + vector[2] * cosX;
    const float rotatedYX = vector[0] * cosY + rotatedXZ * sinY;
    const float rotatedYZ = -vector[0] * sinY + rotatedXZ * cosY;
    const float rotatedZX = rotatedYX * cosZ - rotatedXY * sinZ;
    const float rotatedZY = rotatedYX * sinZ + rotatedXY * cosZ;
    return {rotatedZX, rotatedZY, rotatedYZ};
}

void applySpriteObjectVisualDescriptor(EditorSession &session, Game::MapDeltaSpriteObject &spriteObject)
{
    const Game::ObjectEntry *pObjectEntry = session.objectTable().get(spriteObject.objectDescriptionId);

    if (pObjectEntry == nullptr)
    {
        spriteObject.spriteId = 0;
        return;
    }

    spriteObject.spriteId = pObjectEntry->spriteId;

    if (spriteObject.temporaryLifetime == 0 && pObjectEntry->lifetimeTicks > 0)
    {
        spriteObject.temporaryLifetime = pObjectEntry->lifetimeTicks;
    }
}

std::string spriteObjectDisplayLabel(
    const EditorSession &session,
    const Game::MapDeltaSpriteObject &spriteObject,
    size_t objectIndex)
{
    const uint32_t containedItemId = Game::spriteObjectContainedItemId(spriteObject.rawContainingItem);

    if (containedItemId != 0)
    {
        return session.itemDisplayName(containedItemId) + " (#" + std::to_string(containedItemId) + ")";
    }

    if (spriteObject.objectDescriptionId != 0)
    {
        return "Object " + std::to_string(spriteObject.objectDescriptionId);
    }

    if (spriteObject.spriteId != 0)
    {
        return "Sprite " + std::to_string(spriteObject.spriteId);
    }

    return "Sprite Object " + std::to_string(objectIndex);
}

std::pair<std::string, std::string> inspectorSelectionSummary(const EditorSession &session)
{
    if (!session.hasDocument())
    {
        return {"No document", {}};
    }

    const EditorDocument &document = session.document();
    const EditorSelection &selection = session.selection();

    switch (selection.kind)
    {
    case EditorSelectionKind::None:
    case EditorSelectionKind::Summary:
        return {"Level Summary", document.displayName()};

    case EditorSelectionKind::Environment:
        return {"Environment", document.displayName()};

    case EditorSelectionKind::Terrain:
    {
        if (selection.index == std::numeric_limits<size_t>::max())
        {
            return {"Terrain", "Map-wide terrain settings"};
        }

        const int cellX = static_cast<int>(selection.index % Game::OutdoorMapData::TerrainWidth);
        const int cellY = static_cast<int>(selection.index / Game::OutdoorMapData::TerrainWidth);
        return {"Terrain Cell", std::to_string(cellX) + ", " + std::to_string(cellY)};
    }

    case EditorSelectionKind::BModel:
        return {"BModel", "Index " + std::to_string(selection.index)};

    case EditorSelectionKind::InteractiveFace:
        if (document.kind() == EditorDocument::Kind::Indoor)
        {
            const Game::IndoorMapData &indoorGeometry = document.indoorGeometry();
            const Game::IndoorSceneData &sceneData = document.indoorSceneData();

            if (selection.index < indoorGeometry.faces.size())
            {
                return {
                    "Face",
                    indoorFaceOutlinerLabel(effectiveIndoorFace(sceneData, indoorGeometry, selection.index), selection.index)
                };
            }

            return {"Face", "Index " + std::to_string(selection.index)};
        }

        return {"Face Selection", std::to_string(session.selectedInteractiveFaceIndices().size()) + " selected"};

    case EditorSelectionKind::Entity:
    {
        if (document.kind() == EditorDocument::Kind::Indoor)
        {
            const Game::IndoorMapData &indoorGeometry = document.indoorGeometry();

            if (selection.index < indoorGeometry.entities.size())
            {
                const Game::IndoorEntity &entity = indoorGeometry.entities[selection.index];
                const std::string name = entity.name.empty()
                    ? "Entity " + std::to_string(selection.index)
                    : entity.name;
                return {"Entity", name};
            }

            break;
        }

        const Game::OutdoorSceneData &sceneData = document.outdoorSceneData();

        if (selection.index < sceneData.entities.size())
        {
            const Game::OutdoorSceneEntity &entity = sceneData.entities[selection.index];
            const std::string name = entity.entity.name.empty()
                ? "Entity " + std::to_string(entity.entityIndex)
                : entity.entity.name;
            return {"Entity", name};
        }

        break;
    }

    case EditorSelectionKind::Spawn:
        return {"Spawn", "Index " + std::to_string(selection.index)};

    case EditorSelectionKind::Actor:
    {
        if (document.kind() == EditorDocument::Kind::Indoor)
        {
            const Game::IndoorSceneData &sceneData = document.indoorSceneData();

            if (selection.index < sceneData.initialState.actors.size())
            {
                return {
                    "Actor",
                    actorDisplayLabel(&session.monsterTable(), sceneData.initialState.actors[selection.index], selection.index)
                };
            }

            break;
        }

        const Game::OutdoorSceneData &sceneData = document.outdoorSceneData();

        if (selection.index < sceneData.initialState.actors.size())
        {
            return {
                "Actor",
                actorDisplayLabel(&session.monsterTable(), sceneData.initialState.actors[selection.index], selection.index)
            };
        }

        break;
    }

    case EditorSelectionKind::SpriteObject:
    {
        if (document.kind() == EditorDocument::Kind::Indoor)
        {
            const Game::IndoorSceneData &sceneData = document.indoorSceneData();

            if (selection.index < sceneData.initialState.spriteObjects.size())
            {
                return {
                    "Sprite Object",
                    spriteObjectDisplayLabel(session, sceneData.initialState.spriteObjects[selection.index], selection.index)
                };
            }

            break;
        }

        const Game::OutdoorSceneData &sceneData = document.outdoorSceneData();

        if (selection.index < sceneData.initialState.spriteObjects.size())
        {
            return {
                "Sprite Object",
                spriteObjectDisplayLabel(session, sceneData.initialState.spriteObjects[selection.index], selection.index)
            };
        }

        break;
    }

    case EditorSelectionKind::Chest:
        return {"Chest", "Index " + std::to_string(selection.index)};
    case EditorSelectionKind::Light:
        return {"Light", "Index " + std::to_string(selection.index)};

    case EditorSelectionKind::Door:
        if (document.kind() == EditorDocument::Kind::Indoor)
        {
            const Game::IndoorSceneData &sceneData = document.indoorSceneData();

            if (selection.index < sceneData.initialState.doors.size())
            {
                const Game::IndoorSceneDoor &door = sceneData.initialState.doors[selection.index];
                return {
                    "Mechanism",
                    "Door " + std::to_string(door.doorIndex) + " · id " + std::to_string(door.door.doorId)
                };
            }
        }

        return {"Door", "Index " + std::to_string(selection.index)};

    case EditorSelectionKind::ModelInstance:
    case EditorSelectionKind::Mm9ScriptedObject:
        if (document.kind() == EditorDocument::Kind::Outdoor)
        {
            const Game::OutdoorSceneData &sceneData = document.outdoorSceneData();

            if (selection.index < sceneData.modelInstances.size())
            {
                const Game::OutdoorSceneModelInstance &modelInstance = sceneData.modelInstances[selection.index];
                const std::string name = modelInstance.sourceName.empty()
                    ? modelInstance.instanceId
                    : modelInstance.sourceName;
                return {
                    selection.kind == EditorSelectionKind::Mm9ScriptedObject
                        ? "MM9 Scripted Object"
                        : "Model Instance",
                    name};
            }
        }

        return {
            selection.kind == EditorSelectionKind::Mm9ScriptedObject ? "MM9 Scripted Object" : "Model Instance",
            "Index " + std::to_string(selection.index)};

    case EditorSelectionKind::Mm9WorldModel:
        if (document.kind() == EditorDocument::Kind::Mm9Dat && document.hasMm9DatLoadedSidecars())
        {
            const EditorMm9DatWorldSidecar &datWorld = document.mm9DatLoadedSidecars().datWorld;

            if (selection.index < datWorld.worldModels.size())
            {
                const EditorMm9DatWorldModelSummary &model = datWorld.worldModels[selection.index];
                return {
                    "DAT World Model",
                    std::to_string(model.sourceModelIndex) + " - "
                        + (model.sourceName.empty() ? std::string("<unnamed>") : model.sourceName)};
            }
        }

        return {"DAT World Model", "Index " + std::to_string(selection.index)};

    case EditorSelectionKind::Mm9DatPolygon:
        if (document.kind() == EditorDocument::Kind::Mm9Dat && document.hasMm9DatWorld())
        {
            const Game::Mm9DatRenderMesh &mesh = document.mm9DatRenderMesh();

            if (selection.index < mesh.triangles.size())
            {
                const Game::Mm9DatRenderTriangle &triangle = mesh.triangles[selection.index];
                return {
                    "DAT Polygon",
                    "Model " + std::to_string(triangle.sourceModelIndex)
                        + " / Poly " + std::to_string(triangle.sourcePolyIndex)
                        + " / Surface " + std::to_string(triangle.sourceSurfaceIndex)};
            }
        }

        return {"DAT Polygon", "Triangle " + std::to_string(selection.index)};

    case EditorSelectionKind::Mm9MaterialTexture:
        if (document.kind() == EditorDocument::Kind::Mm9Dat && document.hasMm9DatLoadedSidecars())
        {
            const EditorMm9MaterialAliasesSidecar &materials =
                document.mm9DatLoadedSidecars().materialAliases;

            if (selection.index < materials.textures.size())
            {
                const EditorMm9MaterialTexture &texture = materials.textures[selection.index];
                return {
                    "DTX Texture",
                    texture.alias + " - "
                        + (texture.sourceTexture.empty()
                            ? std::string("<missing source>")
                            : texture.sourceTexture)};
            }
        }

        return {"DTX Texture", "Index " + std::to_string(selection.index)};

    case EditorSelectionKind::Mm9RawObject:
        if (document.kind() == EditorDocument::Kind::Mm9Dat && document.hasMm9DatLoadedSidecars())
        {
            const EditorMm9RawObjectsSidecar &rawObjects = document.mm9DatLoadedSidecars().rawObjects;

            if (selection.index < rawObjects.objects.size())
            {
                const EditorMm9RawObject &object = rawObjects.objects[selection.index];
                return {
                    "DAT Raw Object",
                    std::to_string(object.objectIndex) + " - "
                        + (object.name.empty() ? std::string("<unnamed>") : object.name)};
            }
        }

        return {"DAT Raw Object", "Index " + std::to_string(selection.index)};

    case EditorSelectionKind::Mm9EventObject:
        if (document.kind() == EditorDocument::Kind::Mm9Dat && document.hasMm9DatLoadedSidecars())
        {
            const Game::Mm9EventsData &events = document.mm9DatLoadedSidecars().events;

            if (selection.index < events.objects.size())
            {
                const Game::Mm9EventObject &object = events.objects[selection.index];
                return {
                    "MM9 Event Object",
                    std::to_string(object.sourceObjectIndex) + " - "
                        + (object.sourceName.empty() ? object.sourceClass : object.sourceName)};
            }
        }

        return {"MM9 Event Object", "Index " + std::to_string(selection.index)};

    case EditorSelectionKind::Mm9Mechanism:
        if (document.kind() == EditorDocument::Kind::Mm9Dat && document.hasMm9DatLoadedSidecars())
        {
            const Game::Mm9EventsData &events = document.mm9DatLoadedSidecars().events;

            if (selection.index < events.mechanisms.size())
            {
                const Game::Mm9EventMechanism &mechanism = events.mechanisms[selection.index];
                return {
                    "MM9 Mechanism",
                    std::to_string(mechanism.sourceObjectIndex) + " - "
                        + (mechanism.sourceName.empty() ? mechanism.sourceClass : mechanism.sourceName)};
            }
        }

        return {"MM9 Mechanism", "Index " + std::to_string(selection.index)};

    case EditorSelectionKind::Mm9EventScript:
        if (document.kind() == EditorDocument::Kind::Mm9Dat && document.hasMm9DatLoadedSidecars())
        {
            const Game::Mm9EventsData &events = document.mm9DatLoadedSidecars().events;

            if (selection.index < events.scripts.size())
            {
                const Game::Mm9EventScript &script = events.scripts[selection.index];
                return {"MM9 Script", script.scriptId};
            }
        }

        return {"MM9 Script", "Index " + std::to_string(selection.index)};
    }

    return {"Selection", {}};
}

const EditorIdLabelOption *findOptionById(
    const std::vector<EditorIdLabelOption> &options,
    uint32_t id)
{
    for (const EditorIdLabelOption &option : options)
    {
        if (option.id == id)
        {
            return &option;
        }
    }

    return nullptr;
}

std::string selectorPreviewLabel(
    uint32_t value,
    const std::vector<EditorIdLabelOption> &options,
    const char *pZeroLabel,
    const char *pFallbackPrefix)
{
    if (value == 0 && pZeroLabel != nullptr)
    {
        return pZeroLabel;
    }

    const EditorIdLabelOption *pOption = findOptionById(options, value);

    if (pOption != nullptr)
    {
        return pOption->label;
    }

    return std::string(pFallbackPrefix) + " #" + std::to_string(value);
}

std::string canonicalBitmapTextureName(
    const std::vector<std::string> &options,
    const std::string &value)
{
    const std::string loweredValue = toLowerCopy(value);

    for (const std::string &option : options)
    {
        if (toLowerCopy(option) == loweredValue)
        {
            return option;
        }
    }

    return value;
}

bool optionMatchesFilter(const EditorIdLabelOption &option, const std::string &filter)
{
    if (filter.empty())
    {
        return true;
    }

    const std::string lowerLabel = toLowerCopy(option.label);
    const std::string lowerId = std::to_string(option.id);
    return lowerLabel.find(filter) != std::string::npos || lowerId.find(filter) != std::string::npos;
}

bool editOptionField(
    EditorSession &session,
    const char *pLabel,
    uint32_t &value,
    const std::vector<EditorIdLabelOption> &options,
    const char *pZeroLabel,
    const char *pFallbackPrefix)
{
    beginInspectorFieldRow(pLabel);

    const std::string comboId = inspectorFieldId(pLabel);
    const std::string preview = selectorPreviewLabel(value, options, pZeroLabel, pFallbackPrefix);

    if (!ImGui::BeginCombo(comboId.c_str(), preview.c_str()))
    {
        return false;
    }

    const ImGuiID filterStorageId = ImGui::GetID((comboId + "/filter").c_str());
    static std::unordered_map<ImGuiID, std::string> filters;
    std::string &filter = filters[filterStorageId];
    char filterBuffer[128] = {};
    std::snprintf(filterBuffer, sizeof(filterBuffer), "%s", filter.c_str());
    ImGui::SetNextItemWidth(-FLT_MIN);

    if (ImGui::InputText("##Filter", filterBuffer, sizeof(filterBuffer)))
    {
        filter = filterBuffer;
    }

    const std::string normalizedFilter = toLowerCopy(filter);
    bool changed = false;

    if (pZeroLabel != nullptr)
    {
        const bool selected = value == 0;

        if ((normalizedFilter.empty() || toLowerCopy(pZeroLabel).find(normalizedFilter) != std::string::npos)
            && ImGui::Selectable(pZeroLabel, selected))
        {
            if (value != 0)
            {
                session.captureUndoSnapshot();
                value = 0;
                changed = true;
            }
        }

        if (selected)
        {
            ImGui::SetItemDefaultFocus();
        }
    }

    for (const EditorIdLabelOption &option : options)
    {
        if (!optionMatchesFilter(option, normalizedFilter))
        {
            continue;
        }

        const bool selected = option.id == value;

        if (ImGui::Selectable(option.label.c_str(), selected))
        {
            if (option.id != value)
            {
                session.captureUndoSnapshot();
                value = option.id;
                changed = true;
            }
        }

        if (selected)
        {
            ImGui::SetItemDefaultFocus();
        }
    }

    ImGui::EndCombo();
    return changed;
}

bool editTransientOptionField(
    const char *pLabel,
    uint32_t &value,
    const std::vector<EditorIdLabelOption> &options,
    const char *pZeroLabel,
    const char *pFallbackPrefix)
{
    beginInspectorFieldRow(pLabel);

    const std::string comboId = inspectorFieldId(pLabel);
    const std::string preview = selectorPreviewLabel(value, options, pZeroLabel, pFallbackPrefix);

    if (!ImGui::BeginCombo(comboId.c_str(), preview.c_str()))
    {
        return false;
    }

    const ImGuiID filterStorageId = ImGui::GetID((comboId + "/filter").c_str());
    static std::unordered_map<ImGuiID, std::string> filters;
    std::string &filter = filters[filterStorageId];
    char filterBuffer[128] = {};
    std::snprintf(filterBuffer, sizeof(filterBuffer), "%s", filter.c_str());
    ImGui::SetNextItemWidth(-FLT_MIN);

    if (ImGui::InputText("##Filter", filterBuffer, sizeof(filterBuffer)))
    {
        filter = filterBuffer;
    }

    const std::string normalizedFilter = toLowerCopy(filter);
    bool changed = false;

    if (pZeroLabel != nullptr)
    {
        const bool selected = value == 0;

        if ((normalizedFilter.empty() || toLowerCopy(pZeroLabel).find(normalizedFilter) != std::string::npos)
            && ImGui::Selectable(pZeroLabel, selected))
        {
            value = 0;
            changed = true;
        }

        if (selected)
        {
            ImGui::SetItemDefaultFocus();
        }
    }

    for (const EditorIdLabelOption &option : options)
    {
        if (!optionMatchesFilter(option, normalizedFilter))
        {
            continue;
        }

        const bool selected = option.id == value;

        if (ImGui::Selectable(option.label.c_str(), selected))
        {
            value = option.id;
            changed = true;
        }

        if (selected)
        {
            ImGui::SetItemDefaultFocus();
        }
    }

    ImGui::EndCombo();
    return changed;
}

constexpr float InspectorMinLabelColumnWidth = 170.0f;
constexpr float InspectorMaxLabelColumnWidth = 260.0f;
constexpr float InspectorFieldMaxWidth = 240.0f;
constexpr uint32_t MonsterBitShowOnMap = 0x00008000u;
constexpr uint32_t MonsterBitInvisible = 0x00010000u;
constexpr uint32_t MonsterBitNoFlee = 0x00020000u;
constexpr uint32_t MonsterBitHostile = 0x00080000u;
constexpr uint32_t MonsterBitOnAlertMap = 0x00100000u;
constexpr uint32_t MonsterBitTreasureGenerated = 0x00800000u;
constexpr uint32_t MonsterBitShowAsHostile = 0x01000000u;
constexpr uint16_t ObjectBitVisible = 0x0001u;
constexpr uint16_t ObjectBitTemporary = 0x0002u;
constexpr uint16_t ObjectBitHaltTurnBased = 0x0004u;
constexpr uint16_t ObjectBitDroppedByPlayer = 0x0008u;
constexpr uint16_t ObjectBitIgnoreRange = 0x0010u;
constexpr uint16_t ObjectBitNoZBuffer = 0x0020u;
constexpr uint16_t ObjectBitSkipAFrame = 0x0040u;
constexpr uint16_t ObjectBitAttachToHead = 0x0080u;
constexpr uint16_t ObjectBitMissile = 0x0100u;
constexpr uint16_t ObjectBitRemoved = 0x0200u;
constexpr uint16_t ChestBitTrapped = 0x0001u;
constexpr uint16_t ChestBitItemsPlaced = 0x0002u;
constexpr uint16_t ChestBitIdentified = 0x0004u;
constexpr uint32_t FaceAttributeFluid = Game::faceAttributeBit(Game::FaceAttribute::Fluid);
constexpr uint32_t FaceAttributeInvisible = Game::faceAttributeBit(Game::FaceAttribute::Invisible);
constexpr uint32_t FaceAttributeHasHint = Game::faceAttributeBit(Game::FaceAttribute::HasHint);
constexpr uint32_t FaceAttributeClickable = Game::faceAttributeBit(Game::FaceAttribute::Clickable);
constexpr uint32_t FaceAttributePressurePlate = Game::faceAttributeBit(Game::FaceAttribute::PressurePlate);
constexpr uint32_t FaceAttributeUntouchable = Game::faceAttributeBit(Game::FaceAttribute::Untouchable);
constexpr uint32_t EditableFaceAttributeMask =
    FaceAttributeFluid
    | FaceAttributeInvisible
    | FaceAttributeHasHint
    | FaceAttributeClickable
    | FaceAttributePressurePlate
    | FaceAttributeUntouchable;
constexpr size_t ChestItemRecordSize = 36;
constexpr size_t ChestItemRecordCount = 140;

enum class BModelBulkFaceScope
{
    All = 0,
    Walkable = 1,
    Blocking = 2
};

std::string inspectorFieldId(const char *pLabel)
{
    return "##" + std::string(pLabel);
}

bool beginInspectorPropertyTable(const char *pId)
{
    if (!ImGui::BeginTable(
            pId,
            2,
            ImGuiTableFlags_SizingStretchProp
                | ImGuiTableFlags_NoSavedSettings
                | ImGuiTableFlags_BordersInnerV
                | ImGuiTableFlags_BordersInnerH
                | ImGuiTableFlags_RowBg))
    {
        return false;
    }

    const float availableWidth = ImGui::GetContentRegionAvail().x;
    const float labelWidth = std::clamp(
        availableWidth * 0.42f,
        InspectorMinLabelColumnWidth,
        InspectorMaxLabelColumnWidth);
    ImGui::TableSetupColumn("Label", ImGuiTableColumnFlags_WidthFixed, labelWidth);
    ImGui::TableSetupColumn("Value", ImGuiTableColumnFlags_WidthStretch);
    return true;
}

void beginInspectorFieldRow(const char *pLabel)
{
    ImGui::TableNextRow();
    ImGui::TableSetColumnIndex(0);
    ImGui::AlignTextToFramePadding();
    ImGui::PushStyleColor(ImGuiCol_Text, colorFromRgb(0xAAB3BD));
    ImGui::TextUnformatted(pLabel);
    ImGui::PopStyleColor();
    ImGui::TableSetColumnIndex(1);
    ImGui::SetNextItemWidth(std::min(ImGui::GetContentRegionAvail().x, InspectorFieldMaxWidth));
}

void renderInspectorReadOnlyField(const char *pLabel, const std::string &value)
{
    beginInspectorFieldRow(pLabel);
    ImGui::TextUnformatted(value.c_str());
}

void renderInspectorReadOnlyField(const char *pLabel, const char *pValue)
{
    beginInspectorFieldRow(pLabel);
    ImGui::TextUnformatted(pValue);
}

void renderInspectorCopyButton(const char *pId, const std::string &value)
{
    const bool canCopy = !value.empty() && value != "<none>" && value != "<unknown>" && value != "<unavailable>";

    ImGui::PushID(pId);
    ImGui::BeginDisabled(!canCopy);
    if (ImGui::SmallButton("Copy"))
    {
        ImGui::SetClipboardText(value.c_str());
    }
    ImGui::EndDisabled();

    if (ImGui::IsItemHovered(ImGuiHoveredFlags_AllowWhenDisabled))
    {
        ImGui::SetTooltip(canCopy ? "Copy value" : "No value to copy");
    }

    ImGui::PopID();
}

std::string localPathFileUrl(const std::string &pathText)
{
    std::error_code pathError;
    std::filesystem::path path(pathText);

    if (path.is_relative())
    {
        path = std::filesystem::current_path(pathError) / path;
    }

    if (!pathError)
    {
        path = std::filesystem::weakly_canonical(path, pathError);
    }

    if (pathError)
    {
        path = std::filesystem::absolute(std::filesystem::path(pathText), pathError);
    }

    std::string genericPath = path.generic_string();

#if defined(_WIN32)
    return "file:///" + genericPath;
#else
    return "file://" + genericPath;
#endif
}

void renderInspectorOpenPathButton(const char *pId, const std::string &pathText)
{
    const bool hasPath = !pathText.empty() && pathText != "<none>" && pathText != "<unknown>";
    const bool canOpen = hasPath && std::filesystem::exists(std::filesystem::path(pathText));

    ImGui::PushID(pId);
    ImGui::BeginDisabled(!canOpen);
    if (ImGui::SmallButton("Open"))
    {
        const std::string url = localPathFileUrl(pathText);
        SDL_OpenURL(url.c_str());
    }
    ImGui::EndDisabled();

    if (ImGui::IsItemHovered(ImGuiHoveredFlags_AllowWhenDisabled))
    {
        ImGui::SetTooltip(canOpen ? "Open file" : "Path does not exist");
    }

    ImGui::PopID();
}

bool renderInspectorJumpButton(const char *pLabel, bool enabled)
{
    bool clicked = false;

    ImGui::BeginDisabled(!enabled);
    clicked = ImGui::SmallButton(pLabel);
    ImGui::EndDisabled();

    if (ImGui::IsItemHovered(ImGuiHoveredFlags_AllowWhenDisabled))
    {
        ImGui::SetTooltip(enabled ? "Select linked inspector row" : "Linked row is unavailable");
    }

    return clicked && enabled;
}

void renderInspectorCopyableReadOnlyField(const char *pLabel, const std::string &value)
{
    beginInspectorFieldRow(pLabel);
    renderInspectorCopyButton(pLabel, value);
    ImGui::SameLine();
    ImGui::TextUnformatted(value.c_str());
}

void renderInspectorCopyableReadOnlyField(const char *pLabel, const char *pValue)
{
    renderInspectorCopyableReadOnlyField(pLabel, std::string(pValue != nullptr ? pValue : ""));
}

void renderInspectorCopyOpenReadOnlyField(
    const char *pLabel,
    const std::string &value,
    const std::string &openPath)
{
    beginInspectorFieldRow(pLabel);
    renderInspectorCopyButton((std::string(pLabel) + "Copy").c_str(), value);
    ImGui::SameLine();
    renderInspectorOpenPathButton((std::string(pLabel) + "Open").c_str(), openPath);
    ImGui::SameLine();
    ImGui::TextUnformatted(value.c_str());
}

std::optional<size_t> findMm9RawObjectIndexBySourceObjectIndex(
    const EditorMm9RawObjectsSidecar &rawObjects,
    int sourceObjectIndex)
{
    if (sourceObjectIndex < 0)
    {
        return std::nullopt;
    }

    for (size_t objectIndex = 0; objectIndex < rawObjects.objects.size(); ++objectIndex)
    {
        if (rawObjects.objects[objectIndex].objectIndex == static_cast<size_t>(sourceObjectIndex))
        {
            return objectIndex;
        }
    }

    return std::nullopt;
}

std::optional<size_t> findMm9EventObjectIndexByObjectId(
    const Game::Mm9EventsData &events,
    const std::string &objectId)
{
    for (size_t eventObjectIndex = 0; eventObjectIndex < events.objects.size(); ++eventObjectIndex)
    {
        if (events.objects[eventObjectIndex].objectId == objectId)
        {
            return eventObjectIndex;
        }
    }

    return std::nullopt;
}

std::optional<size_t> findMm9MechanismIndexByObjectId(
    const Game::Mm9EventsData &events,
    const std::string &objectId)
{
    for (size_t mechanismIndex = 0; mechanismIndex < events.mechanisms.size(); ++mechanismIndex)
    {
        if (events.mechanisms[mechanismIndex].objectId == objectId)
        {
            return mechanismIndex;
        }
    }

    return std::nullopt;
}

std::optional<size_t> findMm9WorldModelIndexBySourceModelIndex(
    const EditorMm9DatWorldSidecar &datWorld,
    size_t sourceModelIndex)
{
    for (size_t worldModelIndex = 0; worldModelIndex < datWorld.worldModels.size(); ++worldModelIndex)
    {
        if (datWorld.worldModels[worldModelIndex].sourceModelIndex == sourceModelIndex)
        {
            return worldModelIndex;
        }
    }

    return std::nullopt;
}

const Game::Mm9EventBinding *findMm9EventBindingForObject(
    const Game::Mm9EventsData &events,
    const std::string &objectId)
{
    for (const Game::Mm9EventBinding &binding : events.bindings)
    {
        if (binding.objectId == objectId)
        {
            return &binding;
        }
    }

    return nullptr;
}

std::string normalizeMm9ScriptId(const std::string &scriptName)
{
    std::string normalized = toLowerCopy(trimCopy(scriptName));

    if (!normalized.empty() && std::filesystem::path(normalized).extension().empty())
    {
        normalized += ".scr";
    }

    return normalized;
}

const Game::Mm9EventScript *findMm9EventScriptById(
    const Game::Mm9EventsData &events,
    const std::string &scriptName)
{
    const std::string normalizedScriptName = normalizeMm9ScriptId(scriptName);

    if (normalizedScriptName.empty())
    {
        return nullptr;
    }

    for (const Game::Mm9EventScript &script : events.scripts)
    {
        const std::string normalizedSourceFileName =
            normalizeMm9ScriptId(std::filesystem::path(script.sourcePath).filename().string());

        if (normalizeMm9ScriptId(script.scriptId) == normalizedScriptName
            || normalizeMm9ScriptId(script.sourcePath) == normalizedScriptName
            || normalizedSourceFileName == normalizedScriptName)
        {
            return &script;
        }
    }

    return nullptr;
}

size_t countMm9HostilityRegisteredTriggers(const Game::Mm9EventScript &script)
{
    size_t count = 0;

    for (const Game::Mm9EventScript::RegisteredTrigger &trigger : script.registeredTriggers)
    {
        const std::string message = toLowerCopy(trimCopy(trigger.message));
        const std::string callback = toLowerCopy(trimCopy(trigger.callback));

        if (message == "hostile" || callback.find("hostil") != std::string::npos)
        {
            ++count;
        }
    }

    return count;
}

size_t countMm9HostilityTriggerEdges(const Game::Mm9EventScript &script)
{
    size_t count = 0;

    for (const Game::Mm9EventScript::TriggerEdge &edge : script.triggerEdges)
    {
        const std::string message = toLowerCopy(trimCopy(edge.messageExpression));
        const std::string target = toLowerCopy(trimCopy(edge.targetExpression));

        if (message.find("hostil") != std::string::npos || target.find("hostil") != std::string::npos)
        {
            ++count;
        }
    }

    return count;
}

size_t countMm9HostilityIncludes(const Game::Mm9EventScript &script)
{
    size_t count = 0;

    for (const Game::Mm9EventScript::Include &include : script.includes)
    {
        if (toLowerCopy(trimCopy(include.path)).find("hostil") != std::string::npos)
        {
            ++count;
        }
    }

    return count;
}

std::string mm9ScriptIncludePathsText(const Game::Mm9EventScript &script)
{
    if (script.includes.empty())
    {
        return "<none>";
    }

    std::string text;

    for (size_t includeIndex = 0; includeIndex < script.includes.size(); ++includeIndex)
    {
        if (!text.empty())
        {
            text += ", ";
        }

        text += script.includes[includeIndex].path.empty()
            ? std::string("<empty>")
            : script.includes[includeIndex].path;
    }

    return text;
}

bool isMm9RequiredMechanismTarget(const Game::Mm9EventMechanism &mechanism)
{
    return mechanism.sourceClass != "ScriptObject";
}

struct Mm9ReferenceValidationUiSummary
{
    size_t missingDocumentPaths = 0;
    size_t sourceManifestIssues = 0;
    size_t assetGraphBlockingIssues = 0;
    size_t materialBlockingIssues = 0;
    size_t materialWarnings = 0;
    size_t rawObjectAssetBlockingIssues = 0;
    size_t documentValidationIssues = 0;
};

struct Mm9NormalizedDiagnosticUiEntry
{
    std::string severity;
    std::string sourceFile;
    std::string sourceIndexPath;
    std::string sidecarPath;
    std::string resolver;
    std::string suggestedOwner;
    std::string message;
};

size_t mm9ReferenceValidationBlockingIssueCount(const Mm9ReferenceValidationUiSummary &summary)
{
    return summary.missingDocumentPaths
        + summary.sourceManifestIssues
        + summary.assetGraphBlockingIssues
        + summary.materialBlockingIssues
        + summary.rawObjectAssetBlockingIssues
        + summary.documentValidationIssues;
}

bool isMm9MaterialTextureBlockingIssue(const EditorMm9MaterialTextureStatus &status)
{
    if (status.defaultHelperMaterial)
    {
        return false;
    }

    const bool requiredSource = status.datReferenceCount > 0 || !status.sourceTexture.empty();
    bool invalid =
        requiredSource
        && !status.placeholderMissingSource
        && (!status.sourceDtxResolved
            || status.sourceDtxAmbiguous
            || !status.sourcePathExists
            || !status.dtxHeaderLoaded
            || !status.dtxHeaderMatchesSidecar);

    if (status.sourceAssetFamily == "sprites")
    {
        invalid =
            requiredSource
            && (!status.sourceSpriteResolved
                || status.sourceSpriteAmbiguous
                || !status.sourceSpritePathExists
                || !status.sourceSpriteParsed
                || status.spriteFrameTextureCount == 0
                || status.unresolvedSpriteFrameTextureCount != 0
                || status.ambiguousSpriteFrameTextureCount != 0);
    }

    return invalid;
}

bool mm9MaterialTextureHasResolvedPreviewSource(const EditorMm9MaterialTextureStatus &status)
{
    if (status.defaultHelperMaterial)
    {
        return true;
    }

    if (status.sourceAssetFamily == "sprites")
    {
        return status.sourceSpriteResolved
            && status.sourceSpritePathExists
            && status.sourceSpriteParsed
            && status.spriteFrameTextureCount != 0
            && status.unresolvedSpriteFrameTextureCount == 0
            && status.ambiguousSpriteFrameTextureCount == 0;
    }

    return status.sourceDtxResolved && status.sourcePathExists;
}

std::vector<Mm9NormalizedDiagnosticUiEntry> collectMm9NormalizedDiagnostics(
    const EditorSession &session,
    const EditorDocument &document)
{
    std::vector<Mm9NormalizedDiagnosticUiEntry> diagnostics;

    if (document.kind() != EditorDocument::Kind::Mm9Dat)
    {
        return diagnostics;
    }

    const EditorMm9DatLevelMetadata &metadata = document.mm9DatLevelMetadata();

    const auto addDiagnostic =
        [&diagnostics](
            const std::string &severity,
            const std::string &sourceFile,
            const std::string &sourceIndexPath,
            const std::string &sidecarPath,
            const std::string &resolver,
            const std::string &suggestedOwner,
            const std::string &message)
    {
        Mm9NormalizedDiagnosticUiEntry diagnostic = {};
        diagnostic.severity = severity;
        diagnostic.sourceFile = sourceFile;
        diagnostic.sourceIndexPath = sourceIndexPath;
        diagnostic.sidecarPath = sidecarPath;
        diagnostic.resolver = resolver;
        diagnostic.suggestedOwner = suggestedOwner;
        diagnostic.message = message;
        diagnostics.push_back(std::move(diagnostic));
    };

    for (const std::string &message : session.validationMessages())
    {
        addDiagnostic(
            "error",
            document.sceneVirtualPath(),
            "",
            document.sceneVirtualPath(),
            "editor_document_validator",
            "parser",
            message);
    }

    for (const EditorMm9DocumentPathStatus &status : document.mm9DocumentPathStatuses())
    {
        if (status.exists)
        {
            continue;
        }

        const bool requiredPath = isMm9DocumentPathRequired(status);
        const bool cachePath = status.role == "generated_cache";

        addDiagnostic(
            requiredPath ? "error" : (cachePath ? "warning" : "info"),
            document.sceneVirtualPath(),
            "document_paths/" + status.label,
            status.relativePath,
            "mm9_document_path_inventory",
            status.sourceReadOnly ? "source asset mirror" : "sidecar generator",
            "document path is missing: " + status.relativePath);
    }

    for (const std::string &message : document.mm9SourceAssetManifestDiagnostics())
    {
        addDiagnostic(
            "error",
            "source/manifest.yml",
            "",
            "source/manifest.yml",
            "mm9_source_manifest_validator",
            "source asset mirror",
            message);
    }

    for (const EditorMm9SourceAssetFamilyStatus &status : document.mm9SourceAssetFamilyStatuses())
    {
        if (status.declared && status.packageDirectoryExists && status.expectedFileCount == status.actualFileCount)
        {
            continue;
        }

        std::string message;

        if (!status.declared)
        {
            message = "source manifest family is missing: " + status.id;
        }
        else if (!status.packageDirectoryExists)
        {
            message = "source package directory is missing: " + status.package;
        }
        else
        {
            message = "source family file count mismatch: " + status.id
                + " expected=" + std::to_string(status.expectedFileCount)
                + " actual=" + std::to_string(status.actualFileCount);
        }

        addDiagnostic(
            "error",
            "source/manifest.yml",
            "families/" + status.id,
            "source/manifest.yml",
            "mm9_source_manifest_validator",
            "source asset mirror",
            message);
    }

    for (const EditorMm9MaterialTextureStatus &status : document.mm9MaterialTextureStatuses())
    {
        if (isMm9MaterialTextureBlockingIssue(status))
        {
            addDiagnostic(
                "error",
                status.physicalPath,
                "material_textures/" + std::to_string(status.textureIndex),
                metadata.sidecars.materials,
                "mm9_material_texture_resolver",
                status.sourceDtxAmbiguous || status.sourceSpriteAmbiguous ? "authored override" : "source asset mirror",
                "material texture reference is unresolved or ambiguous: " + status.sourceTexture);
        }

        if (status.cacheOlderThanSource)
        {
            addDiagnostic(
                "error",
                status.physicalPath,
                "material_textures/" + std::to_string(status.textureIndex),
                status.emittedBitmap,
                "mm9_material_cache_validator",
                "sidecar generator",
                "generated material cache is older than source DTX: " + status.sourceTexture);
        }

        if (status.placeholderMissingSource
            && status.datReferenceCount > 0
            && !mm9MaterialTextureHasResolvedPreviewSource(status))
        {
            addDiagnostic(
                "warning",
                status.physicalPath.empty() ? status.sourceTexture : status.physicalPath,
                "material_textures/" + std::to_string(status.textureIndex),
                metadata.sidecars.materials,
                "mm9_material_texture_resolver",
                "source asset mirror",
                "DAT material alias still renders from a placeholder cache: " + status.sourceTexture
                    + " dat_refs=" + std::to_string(status.datReferenceCount));
        }
    }

    for (const EditorMm9RawObjectAssetReferenceStatus &status : document.mm9RawObjectAssetReferenceStatuses())
    {
        if (status.resolved && !status.ambiguous)
        {
            continue;
        }

        addDiagnostic(
            status.required ? "error" : "warning",
            metadata.source.dat,
            "raw_objects/" + std::to_string(status.sourceObjectIndex)
                + "/properties/" + std::to_string(status.propertyIndex),
            metadata.sidecars.rawObjects,
            "mm9_raw_object_asset_resolver",
            status.ambiguous ? "authored override" : "source asset mirror",
            (status.required ? "required" : "optional")
                + std::string(" raw object asset reference is unresolved or ambiguous: ")
                + status.sourceFamily + " " + status.sourceValue);
    }

    if (!document.hasMm9DatLoadedSidecars())
    {
        return diagnostics;
    }

    const Engine::AssetFileSystem *pAssetFileSystem = session.assetFileSystem();
    const Mm9ModelInstanceActorSourceLookup *pActorSourceLookup =
        pAssetFileSystem != nullptr
            ? cachedMm9ModelInstanceActorSourceLookup(*pAssetFileSystem)
            : nullptr;
    std::unordered_set<size_t> actorVariantSourceObjectIndexes;

    for (const Game::OutdoorSceneModelInstance &modelInstance : document.outdoorSceneData().modelInstances)
    {
        if (!canResolveMm9ModelInstanceActorSource(modelInstance, pActorSourceLookup))
        {
            continue;
        }

        actorVariantSourceObjectIndexes.insert(modelInstance.sourceObjectIndex);

        const Mm9ResolvedModelInstanceActorSource resolvedSource =
            resolveMm9ModelInstanceActorSource(modelInstance, pActorSourceLookup);

        if (!resolvedSource.inferredFromActorClass)
        {
            addDiagnostic(
                "error",
                metadata.source.dat,
                "raw_objects/" + std::to_string(modelInstance.sourceObjectIndex),
                metadata.sidecars.materials,
                "mm9_actor_variant_resolver",
                "sidecar generator",
                "actor/monster variant is unresolved: " + modelInstance.sourceName
                    + " class=" + modelInstance.sourceClass
                    + " model=" + modelInstance.sourceModel
                    + " skin=" + modelInstance.sourceSkin);
        }
        else if (mm9ActorFootSoundRequiresResolution(resolvedSource.actorRow.footSound)
            && resolvedSource.actorRow.footSoundReferences.empty())
        {
            addDiagnostic(
                "error",
                metadata.source.dat,
                "raw_objects/" + std::to_string(modelInstance.sourceObjectIndex),
                metadata.source.manifest,
                "mm9_actor_variant_sound_resolver",
                "source asset mirror",
                "actor/monster foot sound is unresolved: " + resolvedSource.actorRow.footSound
                    + " source=" + modelInstance.sourceName);
        }
    }

    for (const EditorMm9RawObjectAssetReferenceStatus &status : document.mm9RawObjectAssetReferenceStatuses())
    {
        if ((status.sourceFamily != "sounds" && status.sourceFamily != "voices")
            || actorVariantSourceObjectIndexes.find(status.sourceObjectIndex) == actorVariantSourceObjectIndexes.end()
            || (status.resolved && !status.ambiguous))
        {
            continue;
        }

        addDiagnostic(
            status.required ? "error" : "warning",
            metadata.source.dat,
            "raw_objects/" + std::to_string(status.sourceObjectIndex)
                + "/properties/" + std::to_string(status.propertyIndex),
            metadata.sidecars.rawObjects,
            "mm9_actor_variant_source_asset_resolver",
            status.ambiguous ? "authored override" : "source asset mirror",
            "actor/monster " + status.sourceFamily
                + " reference is unresolved or ambiguous: " + status.sourceValue);
    }

    const Game::Mm9EventsData &events = document.mm9DatLoadedSidecars().events;

    for (const Game::Mm9EventMechanism &mechanism : events.mechanisms)
    {
        const Game::Mm9EventBinding *pBinding = findMm9EventBindingForObject(events, mechanism.objectId);
        bool hasResolvedTarget = false;
        bool hasUnresolvedTarget = pBinding == nullptr || pBinding->targets.empty();

        if (pBinding != nullptr)
        {
            for (const Game::Mm9EventBindingTarget &target : pBinding->targets)
            {
                if ((target.targetKind == "odm_bmodel" && target.bmodelIndex)
                    || (target.targetKind == "model_instance" && !target.targetId.empty()))
                {
                    hasResolvedTarget = true;
                }

                if (target.targetKind == "unresolved")
                {
                    hasUnresolvedTarget = true;
                }
            }
        }

        if (hasResolvedTarget && !hasUnresolvedTarget)
        {
            continue;
        }

        const bool required = isMm9RequiredMechanismTarget(mechanism);
        addDiagnostic(
            required ? "error" : "warning",
            metadata.source.dat,
            "raw_objects/" + std::to_string(mechanism.sourceObjectIndex),
            metadata.sidecars.events,
            "mm9_mechanism_target_resolver",
            "sidecar generator",
            "mechanism target is unresolved: " + mechanism.sourceName);
    }

    return diagnostics;
}

Mm9ReferenceValidationUiSummary collectMm9ReferenceValidationUiSummary(
    const EditorSession &session,
    const EditorDocument &document)
{
    Mm9ReferenceValidationUiSummary summary = {};
    summary.documentValidationIssues = session.validationMessages().size();

    for (const EditorMm9DocumentPathStatus &status : document.mm9DocumentPathStatuses())
    {
        if (!status.exists && isMm9DocumentPathRequired(status))
        {
            ++summary.missingDocumentPaths;
        }
    }

    summary.sourceManifestIssues = document.mm9SourceAssetManifestDiagnostics().size();

    for (const EditorMm9SourceAssetFamilyStatus &status : document.mm9SourceAssetFamilyStatuses())
    {
        if (!status.declared || !status.packageDirectoryExists)
        {
            ++summary.sourceManifestIssues;
        }
        else if (status.expectedFileCount != status.actualFileCount)
        {
            ++summary.sourceManifestIssues;
        }
    }

    const EditorMm9AssetDependencySummary &assetSummary = document.mm9AssetDependencySummary();
    summary.assetGraphBlockingIssues = assetSummary.requiredUnresolved + assetSummary.requiredAmbiguous;

    for (const EditorMm9MaterialTextureStatus &status : document.mm9MaterialTextureStatuses())
    {
        if (isMm9MaterialTextureBlockingIssue(status))
        {
            ++summary.materialBlockingIssues;
        }

        if (status.cacheOlderThanSource)
        {
            ++summary.materialWarnings;
        }

        if (status.placeholderMissingSource
            && status.datReferenceCount > 0
            && !mm9MaterialTextureHasResolvedPreviewSource(status))
        {
            ++summary.materialWarnings;
        }
    }

    for (const EditorMm9RawObjectAssetReferenceStatus &status : document.mm9RawObjectAssetReferenceStatuses())
    {
        if (status.required && (!status.resolved || status.ambiguous))
        {
            ++summary.rawObjectAssetBlockingIssues;
        }
    }

    return summary;
}

const char *bmodelBulkFaceScopeLabel(BModelBulkFaceScope scope)
{
    switch (scope)
    {
    case BModelBulkFaceScope::Walkable:
        return "Walkable Faces";
    case BModelBulkFaceScope::Blocking:
        return "Blocking Faces";
    case BModelBulkFaceScope::All:
    default:
        return "All Faces";
    }
}

const char *outdoorTilesetPresetLabel(EditorOutdoorMapTilesetPreset preset)
{
    switch (preset)
    {
    case EditorOutdoorMapTilesetPreset::Shadowspire:
        return "Shadowspire";
    case EditorOutdoorMapTilesetPreset::IronsandDesert:
        return "Ironsand Desert";
    case EditorOutdoorMapTilesetPreset::Grassland:
    default:
        return "Grassland";
    }
}

bool bmodelFaceMatchesScope(const Game::OutdoorBModelFace &face, BModelBulkFaceScope scope)
{
    switch (scope)
    {
    case BModelBulkFaceScope::Walkable:
        return Game::isOutdoorWalkablePolygonType(face.polygonType);
    case BModelBulkFaceScope::Blocking:
        return !Game::isOutdoorWalkablePolygonType(face.polygonType);
    case BModelBulkFaceScope::All:
    default:
        return true;
    }
}

void repairOutdoorSceneFaceReferencesAfterDelete(
    Game::OutdoorSceneData &sceneData,
    size_t bmodelIndex,
    size_t deletedFaceIndex)
{
    sceneData.interactiveFaces.erase(
        std::remove_if(
            sceneData.interactiveFaces.begin(),
            sceneData.interactiveFaces.end(),
            [bmodelIndex, deletedFaceIndex](Game::OutdoorSceneInteractiveFace &face)
            {
                if (face.bmodelIndex != bmodelIndex)
                {
                    return false;
                }

                if (face.faceIndex == deletedFaceIndex)
                {
                    return true;
                }

                if (face.faceIndex > deletedFaceIndex)
                {
                    --face.faceIndex;
                }

                return false;
            }),
        sceneData.interactiveFaces.end());

    sceneData.bmodelFaceSources.erase(
        std::remove_if(
            sceneData.bmodelFaceSources.begin(),
            sceneData.bmodelFaceSources.end(),
            [bmodelIndex, deletedFaceIndex](Game::OutdoorSceneBModelFaceSource &faceSource)
            {
                if (faceSource.bmodelIndex != bmodelIndex)
                {
                    return false;
                }

                if (faceSource.faceIndex == deletedFaceIndex)
                {
                    return true;
                }

                if (faceSource.faceIndex > deletedFaceIndex)
                {
                    --faceSource.faceIndex;
                }

                return false;
            }),
        sceneData.bmodelFaceSources.end());

    sceneData.initialState.faceAttributeOverrides.erase(
        std::remove_if(
            sceneData.initialState.faceAttributeOverrides.begin(),
            sceneData.initialState.faceAttributeOverrides.end(),
            [bmodelIndex, deletedFaceIndex](Game::OutdoorSceneFaceAttributeOverride &face)
            {
                if (face.bmodelIndex != bmodelIndex)
                {
                    return false;
                }

                if (face.faceIndex == deletedFaceIndex)
                {
                    return true;
                }

                if (face.faceIndex > deletedFaceIndex)
                {
                    --face.faceIndex;
                }

                return false;
            }),
        sceneData.initialState.faceAttributeOverrides.end());
}

Game::IndoorSceneFaceAttributeOverride *findIndoorFaceAttributeOverride(
    Game::IndoorSceneData &sceneData,
    size_t faceIndex)
{
    return Game::findIndoorSceneFaceOverride(sceneData, faceIndex);
}

const Game::IndoorSceneFaceAttributeOverride *findIndoorFaceAttributeOverride(
    const Game::IndoorSceneData &sceneData,
    size_t faceIndex)
{
    return Game::findIndoorSceneFaceOverride(sceneData, faceIndex);
}

bool indoorFaceOverrideHasAnyField(const Game::IndoorSceneFaceAttributeOverride &overrideEntry)
{
    return overrideEntry.legacyAttributes.has_value()
        || overrideEntry.textureFrameTableCog.has_value()
        || overrideEntry.cogNumber.has_value()
        || overrideEntry.cogTriggered.has_value()
        || overrideEntry.cogTriggerType.has_value();
}

void synchronizeIndoorFaceAttributeOverride(
    Game::IndoorSceneData &sceneData,
    size_t faceIndex,
    uint32_t effectiveAttributes,
    uint32_t baseAttributes)
{
    Game::IndoorSceneFaceAttributeOverride *pOverride = findIndoorFaceAttributeOverride(sceneData, faceIndex);

    if (effectiveAttributes == baseAttributes)
    {
        if (pOverride == nullptr)
        {
            return;
        }

        pOverride->legacyAttributes.reset();

        if (!indoorFaceOverrideHasAnyField(*pOverride))
        {
            sceneData.initialState.faceAttributeOverrides.erase(
                std::remove_if(
                    sceneData.initialState.faceAttributeOverrides.begin(),
                    sceneData.initialState.faceAttributeOverrides.end(),
                    [faceIndex](const Game::IndoorSceneFaceAttributeOverride &overrideEntry)
                    {
                        return overrideEntry.faceIndex == faceIndex;
                    }),
                sceneData.initialState.faceAttributeOverrides.end());
        }

        return;
    }

    if (pOverride == nullptr)
    {
        Game::IndoorSceneFaceAttributeOverride overrideEntry = {};
        overrideEntry.faceIndex = faceIndex;
        overrideEntry.legacyAttributes = effectiveAttributes;
        sceneData.initialState.faceAttributeOverrides.push_back(std::move(overrideEntry));
        return;
    }

    pOverride->legacyAttributes = effectiveAttributes;
}

uint32_t effectiveIndoorFaceAttributes(
    const Game::IndoorSceneData &sceneData,
    const Game::IndoorFace &face,
    size_t faceIndex)
{
    if (const Game::IndoorSceneFaceAttributeOverride *pOverride = findIndoorFaceAttributeOverride(sceneData, faceIndex))
    {
        if (pOverride->legacyAttributes.has_value())
        {
            return *pOverride->legacyAttributes;
        }
    }

    return face.attributes;
}

Game::IndoorFace effectiveIndoorFace(
    const Game::IndoorSceneData &sceneData,
    const Game::IndoorMapData &indoorGeometry,
    size_t faceIndex)
{
    Game::IndoorFace effectiveFace = indoorGeometry.faces[faceIndex];

    if (const Game::IndoorSceneFaceAttributeOverride *pOverride = findIndoorFaceAttributeOverride(sceneData, faceIndex))
    {
        Game::applyIndoorSceneFaceOverride(*pOverride, effectiveFace);
    }

    return effectiveFace;
}

void synchronizeIndoorFaceTriggerOverride(
    Game::IndoorSceneData &sceneData,
    const Game::IndoorFace &baseFace,
    size_t faceIndex,
    uint16_t textureFrameTableCog,
    uint16_t cogNumber,
    uint16_t cogTriggered,
    uint16_t cogTriggerType)
{
    Game::IndoorSceneFaceAttributeOverride *pOverride = findIndoorFaceAttributeOverride(sceneData, faceIndex);

    if (pOverride == nullptr)
    {
        if (textureFrameTableCog == baseFace.textureFrameTableCog
            && cogNumber == baseFace.cogNumber
            && cogTriggered == baseFace.cogTriggered
            && cogTriggerType == baseFace.cogTriggerType)
        {
            return;
        }

        Game::IndoorSceneFaceAttributeOverride overrideEntry = {};
        overrideEntry.faceIndex = faceIndex;
        overrideEntry.textureFrameTableCog =
            textureFrameTableCog != baseFace.textureFrameTableCog ? std::optional<uint16_t>(textureFrameTableCog)
                                                                  : std::nullopt;
        overrideEntry.cogNumber = cogNumber != baseFace.cogNumber ? std::optional<uint16_t>(cogNumber) : std::nullopt;
        overrideEntry.cogTriggered =
            cogTriggered != baseFace.cogTriggered ? std::optional<uint16_t>(cogTriggered) : std::nullopt;
        overrideEntry.cogTriggerType =
            cogTriggerType != baseFace.cogTriggerType ? std::optional<uint16_t>(cogTriggerType) : std::nullopt;
        sceneData.initialState.faceAttributeOverrides.push_back(std::move(overrideEntry));
        return;
    }

    pOverride->textureFrameTableCog =
        textureFrameTableCog != baseFace.textureFrameTableCog ? std::optional<uint16_t>(textureFrameTableCog)
                                                              : std::nullopt;
    pOverride->cogNumber = cogNumber != baseFace.cogNumber ? std::optional<uint16_t>(cogNumber) : std::nullopt;
    pOverride->cogTriggered =
        cogTriggered != baseFace.cogTriggered ? std::optional<uint16_t>(cogTriggered) : std::nullopt;
    pOverride->cogTriggerType =
        cogTriggerType != baseFace.cogTriggerType ? std::optional<uint16_t>(cogTriggerType) : std::nullopt;

    if (!indoorFaceOverrideHasAnyField(*pOverride))
    {
        sceneData.initialState.faceAttributeOverrides.erase(
            std::remove_if(
                sceneData.initialState.faceAttributeOverrides.begin(),
                sceneData.initialState.faceAttributeOverrides.end(),
                [faceIndex](const Game::IndoorSceneFaceAttributeOverride &overrideEntry)
                {
                    return overrideEntry.faceIndex == faceIndex;
                }),
            sceneData.initialState.faceAttributeOverrides.end());
    }
}

bool applyIndoorFaceAttributeMaskToSelection(
    Game::IndoorSceneData &sceneData,
    const Game::IndoorMapData &indoorGeometry,
    const std::vector<size_t> &selectedFaceIndices,
    uint32_t attributeMask,
    bool enabled)
{
    bool mutated = false;

    for (size_t selectedFaceIndex : selectedFaceIndices)
    {
        if (selectedFaceIndex >= indoorGeometry.faces.size())
        {
            continue;
        }

        const Game::IndoorFace &selectedFace = indoorGeometry.faces[selectedFaceIndex];
        const uint32_t effectiveAttributes =
            effectiveIndoorFaceAttributes(sceneData, selectedFace, selectedFaceIndex);
        const uint32_t updatedAttributes =
            enabled ? (effectiveAttributes | attributeMask) : (effectiveAttributes & ~attributeMask);

        if (updatedAttributes == effectiveAttributes)
        {
            continue;
        }

        synchronizeIndoorFaceAttributeOverride(sceneData, selectedFaceIndex, updatedAttributes, selectedFace.attributes);
        mutated = true;
    }

    return mutated;
}

bool resetIndoorFaceAttributeSelectionToBase(
    Game::IndoorSceneData &sceneData,
    const Game::IndoorMapData &indoorGeometry,
    const std::vector<size_t> &selectedFaceIndices)
{
    bool mutated = false;

    for (size_t selectedFaceIndex : selectedFaceIndices)
    {
        if (selectedFaceIndex >= indoorGeometry.faces.size())
        {
            continue;
        }

        const Game::IndoorFace &selectedFace = indoorGeometry.faces[selectedFaceIndex];
        const uint32_t effectiveAttributes =
            effectiveIndoorFaceAttributes(sceneData, selectedFace, selectedFaceIndex);

        if (effectiveAttributes == selectedFace.attributes)
        {
            continue;
        }

        synchronizeIndoorFaceAttributeOverride(
            sceneData,
            selectedFaceIndex,
            selectedFace.attributes,
            selectedFace.attributes);
        mutated = true;
    }

    return mutated;
}

std::vector<size_t> collectLinkedIndoorMechanismIndicesForFaces(
    const Game::IndoorSceneData &sceneData,
    const std::vector<size_t> &selectedFaceIndices)
{
    std::unordered_set<size_t> selectedFaceIndexSet(selectedFaceIndices.begin(), selectedFaceIndices.end());
    std::vector<size_t> linkedDoorIndices;

    for (size_t doorIndex = 0; doorIndex < sceneData.initialState.doors.size(); ++doorIndex)
    {
        const Game::IndoorSceneDoor &door = sceneData.initialState.doors[doorIndex];
        const bool linked = std::any_of(
            door.door.faceIds.begin(),
            door.door.faceIds.end(),
            [&selectedFaceIndexSet](uint16_t faceId)
            {
                return selectedFaceIndexSet.contains(faceId);
            });

        if (linked)
        {
            linkedDoorIndices.push_back(doorIndex);
        }
    }

    return linkedDoorIndices;
}

std::vector<uint16_t> collectIndoorFaceEventIds(
    const Game::IndoorSceneData &sceneData,
    const Game::IndoorMapData &indoorGeometry,
    const std::vector<size_t> &selectedFaceIndices)
{
    std::vector<uint16_t> eventIds;

    for (size_t selectedFaceIndex : selectedFaceIndices)
    {
        if (selectedFaceIndex >= indoorGeometry.faces.size())
        {
            continue;
        }

        const Game::IndoorFace effectiveFace = effectiveIndoorFace(sceneData, indoorGeometry, selectedFaceIndex);
        const uint16_t eventId = effectiveFace.cogTriggered;

        if (eventId == 0 || std::find(eventIds.begin(), eventIds.end(), eventId) != eventIds.end())
        {
            continue;
        }

        eventIds.push_back(eventId);
    }

    return eventIds;
}

void appendUniqueIndoorSectorFaceIds(
    std::vector<uint16_t> &targetFaceIds,
    const std::vector<uint16_t> &sourceFaceIds)
{
    for (uint16_t faceId : sourceFaceIds)
    {
        if (std::find(targetFaceIds.begin(), targetFaceIds.end(), faceId) == targetFaceIds.end())
        {
            targetFaceIds.push_back(faceId);
        }
    }
}

std::vector<uint16_t> indoorSectorFaceIds(const Game::IndoorMapData &indoorGeometry, uint16_t sectorId)
{
    if (sectorId >= indoorGeometry.sectors.size())
    {
        return {};
    }

    const Game::IndoorSector &sector = indoorGeometry.sectors[sectorId];
    std::vector<uint16_t> faceIds;
    faceIds.reserve(sector.faceIds.size() + sector.portalFaceIds.size());
    appendUniqueIndoorSectorFaceIds(faceIds, sector.faceIds);
    appendUniqueIndoorSectorFaceIds(faceIds, sector.portalFaceIds);
    return faceIds;
}

std::vector<uint16_t> connectedIndoorRoomIds(const Game::IndoorMapData &indoorGeometry, uint16_t roomId)
{
    if (roomId >= indoorGeometry.sectors.size())
    {
        return {};
    }

    const Game::IndoorSector &sector = indoorGeometry.sectors[roomId];
    std::vector<uint16_t> roomIds;

    const auto appendRoomId =
        [&](uint16_t connectedRoomId)
    {
        if (connectedRoomId >= indoorGeometry.sectors.size())
        {
            return;
        }

        if (std::find(roomIds.begin(), roomIds.end(), connectedRoomId) == roomIds.end())
        {
            roomIds.push_back(connectedRoomId);
        }
    };

    const auto collectFromFaces =
        [&](const std::vector<uint16_t> &faceIds)
    {
        for (uint16_t faceId : faceIds)
        {
            if (faceId >= indoorGeometry.faces.size())
            {
                continue;
            }

            const Game::IndoorFace &face = indoorGeometry.faces[faceId];
            const bool isPortal = face.isPortal || Game::hasFaceAttribute(face.attributes, Game::FaceAttribute::IsPortal);

            if (!isPortal)
            {
                continue;
            }

            if (face.roomNumber == roomId)
            {
                appendRoomId(face.roomBehindNumber);
            }
            else if (face.roomBehindNumber == roomId)
            {
                appendRoomId(face.roomNumber);
            }
        }
    };

    collectFromFaces(sector.portalFaceIds);
    collectFromFaces(sector.faceIds);
    return roomIds;
}

std::vector<uint16_t> collectIndoorDoorRoomIds(const Game::IndoorMapData &indoorGeometry, const Game::MapDeltaDoor &door)
{
    std::vector<uint16_t> roomIds;

    const auto appendRoomId =
        [&](uint16_t roomId)
    {
        if (roomId >= indoorGeometry.sectors.size())
        {
            return;
        }

        if (std::find(roomIds.begin(), roomIds.end(), roomId) == roomIds.end())
        {
            roomIds.push_back(roomId);
        }
    };

    for (uint16_t sectorId : door.sectorIds)
    {
        appendRoomId(sectorId);
    }

    for (uint16_t faceId : door.faceIds)
    {
        if (faceId >= indoorGeometry.faces.size())
        {
            continue;
        }

        const Game::IndoorFace &face = indoorGeometry.faces[faceId];
        appendRoomId(face.roomNumber);
        appendRoomId(face.roomBehindNumber);
    }

    return roomIds;
}

bool containsIndoorId(const std::vector<uint16_t> &ids, uint16_t id)
{
    return std::find(ids.begin(), ids.end(), id) != ids.end();
}

std::string yamlQuoted(const std::string &value)
{
    std::string result = "\"";

    for (char character : value)
    {
        if (character == '\\' || character == '"')
        {
            result.push_back('\\');
            result.push_back(character);
        }
        else if (character == '\n')
        {
            result += "\\n";
        }
        else if (character == '\r')
        {
            result += "\\r";
        }
        else if (character == '\t')
        {
            result += "\\t";
        }
        else
        {
            result.push_back(character);
        }
    }

    result.push_back('"');
    return result;
}

std::string sanitizeDiagnosticFileStem(const std::string &value)
{
    std::string result;
    result.reserve(value.size());

    for (char character : value)
    {
        const unsigned char byte = static_cast<unsigned char>(character);

        if (std::isalnum(byte) != 0 || character == '-' || character == '_')
        {
            result.push_back(static_cast<char>(std::tolower(byte)));
        }
        else if (character == '.' || character == ' ')
        {
            result.push_back('_');
        }
    }

    while (!result.empty() && result.back() == '_')
    {
        result.pop_back();
    }

    return result.empty() ? "indoor_map" : result;
}

std::string indoorMechanismStateName(uint16_t state)
{
    switch (static_cast<Game::EvtMechanismState>(state))
    {
    case Game::EvtMechanismState::Open:
        return "Open";
    case Game::EvtMechanismState::Closed:
        return "Closed";
    case Game::EvtMechanismState::Opening:
        return "Opening";
    case Game::EvtMechanismState::Closing:
        return "Closing";
    }

    return "Unknown";
}

template <typename Integer>
void writeYamlIntegerList(std::ostream &output, const std::string &key, const std::vector<Integer> &values, int indent)
{
    output << std::string(static_cast<size_t>(indent), ' ') << key << ": [";

    for (size_t index = 0; index < values.size(); ++index)
    {
        if (index != 0)
        {
            output << ", ";
        }

        output << values[index];
    }

    output << "]\n";
}

std::vector<size_t> collectIndoorActorIndicesForRoom(const Game::IndoorSceneData &sceneData, uint16_t roomId)
{
    std::vector<size_t> actorIndices;

    for (size_t actorIndex = 0; actorIndex < sceneData.initialState.actors.size(); ++actorIndex)
    {
        const Game::MapDeltaActor &actor = sceneData.initialState.actors[actorIndex];

        if (actor.sectorId == static_cast<int16_t>(roomId))
        {
            actorIndices.push_back(actorIndex);
        }
    }

    return actorIndices;
}

std::vector<size_t> collectIndoorSpriteObjectIndicesForRoom(const Game::IndoorSceneData &sceneData, uint16_t roomId)
{
    std::vector<size_t> objectIndices;

    for (size_t objectIndex = 0; objectIndex < sceneData.initialState.spriteObjects.size(); ++objectIndex)
    {
        const Game::MapDeltaSpriteObject &spriteObject = sceneData.initialState.spriteObjects[objectIndex];

        if (spriteObject.sectorId == static_cast<int16_t>(roomId))
        {
            objectIndices.push_back(objectIndex);
        }
    }

    return objectIndices;
}

std::vector<size_t> collectIndoorDoorIndicesForRoom(
    const Game::IndoorSceneData &sceneData,
    const Game::IndoorMapData &indoorGeometry,
    uint16_t roomId)
{
    std::vector<size_t> doorIndices;

    for (size_t doorIndex = 0; doorIndex < sceneData.initialState.doors.size(); ++doorIndex)
    {
        const Game::IndoorSceneDoor &door = sceneData.initialState.doors[doorIndex];
        const std::vector<uint16_t> doorRoomIds = collectIndoorDoorRoomIds(indoorGeometry, door.door);

        if (containsIndoorId(doorRoomIds, roomId))
        {
            doorIndices.push_back(doorIndex);
        }
    }

    return doorIndices;
}

std::vector<uint16_t> collectIndoorRoomPortalFaceIds(const Game::IndoorMapData &indoorGeometry, uint16_t roomId)
{
    if (roomId >= indoorGeometry.sectors.size())
    {
        return {};
    }

    const Game::IndoorSector &sector = indoorGeometry.sectors[roomId];
    std::vector<uint16_t> portalFaceIds;
    portalFaceIds.reserve(sector.portalFaceIds.size());

    const auto appendPortalFace =
        [&](uint16_t faceId)
    {
        if (faceId >= indoorGeometry.faces.size() || containsIndoorId(portalFaceIds, faceId))
        {
            return;
        }

        const Game::IndoorFace &face = indoorGeometry.faces[faceId];
        const bool isPortal = face.isPortal || Game::hasFaceAttribute(face.attributes, Game::FaceAttribute::IsPortal);

        if (!isPortal)
        {
            return;
        }

        if (face.roomNumber == roomId || face.roomBehindNumber == roomId)
        {
            portalFaceIds.push_back(faceId);
        }
    };

    for (uint16_t faceId : sector.portalFaceIds)
    {
        appendPortalFace(faceId);
    }

    for (uint16_t faceId : sector.faceIds)
    {
        appendPortalFace(faceId);
    }

    return portalFaceIds;
}

std::filesystem::path indoorGeometryDiagnosticPath(const EditorDocument &document)
{
    std::string mapName = document.displayName();

    if (mapName.empty() && !document.scenePhysicalPath().empty())
    {
        mapName = document.scenePhysicalPath().stem().string();
    }

    const std::string fileStem = sanitizeDiagnosticFileStem(std::filesystem::path(mapName).stem().string());
    return std::filesystem::current_path() / "tests" / "indoor_geometry" / (fileStem + ".yml");
}

bool appendIndoorRoomGeometryDiagnostic(
    const EditorSession &session,
    uint16_t roomId,
    size_t selectedFaceIndex,
    std::filesystem::path &outputPath,
    std::string &errorMessage)
{
    const EditorDocument &document = session.document();

    if (document.kind() != EditorDocument::Kind::Indoor)
    {
        errorMessage = "current document is not an indoor map";
        return false;
    }

    const Game::IndoorMapData &indoorGeometry = document.indoorGeometry();
    const Game::IndoorSceneData &sceneData = document.indoorSceneData();

    if (roomId >= indoorGeometry.sectors.size())
    {
        errorMessage = "room id is out of range";
        return false;
    }

    outputPath = indoorGeometryDiagnosticPath(document);
    std::error_code filesystemError;
    std::filesystem::create_directories(outputPath.parent_path(), filesystemError);

    if (filesystemError)
    {
        errorMessage = "could not create " + outputPath.parent_path().string() + ": " + filesystemError.message();
        return false;
    }

    std::ofstream output(outputPath, std::ios::out | std::ios::app);

    if (!output)
    {
        errorMessage = "could not open " + outputPath.string() + " for append";
        return false;
    }

    const Game::IndoorSector &sector = indoorGeometry.sectors[roomId];
    const std::vector<uint16_t> connectedRoomIds = connectedIndoorRoomIds(indoorGeometry, roomId);
    const std::vector<uint16_t> portalFaceIds = collectIndoorRoomPortalFaceIds(indoorGeometry, roomId);
    const std::vector<size_t> roomDoorIndices = collectIndoorDoorIndicesForRoom(sceneData, indoorGeometry, roomId);
    const std::vector<size_t> roomActorIndices = collectIndoorActorIndicesForRoom(sceneData, roomId);
    const std::vector<size_t> roomSpriteObjectIndices = collectIndoorSpriteObjectIndicesForRoom(sceneData, roomId);
    const std::string mapName =
        document.displayName().empty() ? document.scenePhysicalPath().filename().string() : document.displayName();

    output << "---\n";
    output << "kind: indoor_room_geometry_snapshot\n";
    output << "map: " << yamlQuoted(mapName) << "\n";
    output << "scene: " << yamlQuoted(document.sceneVirtualPath()) << "\n";
    output << "room_id: " << roomId << "\n";
    output << "selected_face: " << selectedFaceIndex << "\n";
    output << "room_bounds:\n";
    output << "  min: [" << sector.minX << ", " << sector.minY << ", " << sector.minZ << "]\n";
    output << "  max: [" << sector.maxX << ", " << sector.maxY << ", " << sector.maxZ << "]\n";
    writeYamlIntegerList(output, "connected_rooms", connectedRoomIds, 0);
    writeYamlIntegerList(output, "raw_portal_face_ids", sector.portalFaceIds, 0);
    writeYamlIntegerList(output, "raw_face_ids", sector.faceIds, 0);

    output << "portals:\n";

    if (portalFaceIds.empty())
    {
        output << "  []\n";
    }
    else
    {
        for (size_t portalIndex = 0; portalIndex < portalFaceIds.size(); ++portalIndex)
        {
            const uint16_t faceId = portalFaceIds[portalIndex];
            const Game::IndoorFace &portalFace = indoorGeometry.faces[faceId];
            const uint16_t connectedRoom =
                portalFace.roomNumber == roomId ? portalFace.roomBehindNumber : portalFace.roomNumber;
            const std::vector<size_t> linkedDoorIndices =
                collectLinkedIndoorMechanismIndicesForFaces(sceneData, {faceId});

            output << "  - portal_id: " << portalIndex << "\n";
            output << "    face_id: " << faceId << "\n";
            output << "    room: " << portalFace.roomNumber << "\n";
            output << "    behind_room: " << portalFace.roomBehindNumber << "\n";
            output << "    connected_room: " << connectedRoom << "\n";
            output << "    listed_in_portal_face_ids: "
                << (containsIndoorId(sector.portalFaceIds, faceId) ? "true" : "false") << "\n";
            output << "    listed_in_face_ids: "
                << (containsIndoorId(sector.faceIds, faceId) ? "true" : "false") << "\n";
            output << "    direct_blocking_door_ids: [";

            for (size_t index = 0; index < linkedDoorIndices.size(); ++index)
            {
                if (index != 0)
                {
                    output << ", ";
                }

                const size_t doorIndex = linkedDoorIndices[index];
                output << sceneData.initialState.doors[doorIndex].door.doorId;
            }

            output << "]\n";
        }
    }

    output << "doors:\n";

    if (roomDoorIndices.empty())
    {
        output << "  []\n";
    }
    else
    {
        for (size_t doorIndex : roomDoorIndices)
        {
            const Game::IndoorSceneDoor &door = sceneData.initialState.doors[doorIndex];
            const std::vector<uint16_t> doorRoomIds = collectIndoorDoorRoomIds(indoorGeometry, door.door);
            std::vector<uint16_t> linkedPortalFaceIds;

            for (uint16_t faceId : door.door.faceIds)
            {
                if (containsIndoorId(portalFaceIds, faceId))
                {
                    linkedPortalFaceIds.push_back(faceId);
                }
            }

            output << "  - door_index: " << doorIndex << "\n";
            output << "    door_id: " << door.door.doorId << "\n";
            output << "    state: " << door.door.state << "\n";
            output << "    state_name: " << yamlQuoted(indoorMechanismStateName(door.door.state)) << "\n";
            writeYamlIntegerList(output, "face_ids", door.door.faceIds, 4);
            writeYamlIntegerList(output, "sector_ids", door.door.sectorIds, 4);
            writeYamlIntegerList(output, "affected_rooms", doorRoomIds, 4);
            writeYamlIntegerList(output, "linked_portal_face_ids", linkedPortalFaceIds, 4);
        }
    }

    output << "objects:\n";
    output << "  decorations:\n";
    output << "    count: " << sector.decorationIds.size() << "\n";
    writeYamlIntegerList(output, "ids", sector.decorationIds, 4);
    output << "  lights:\n";
    output << "    count: " << sector.lightIds.size() << "\n";
    writeYamlIntegerList(output, "ids", sector.lightIds, 4);
    output << "  actors:\n";
    output << "    count: " << roomActorIndices.size() << "\n";
    writeYamlIntegerList(output, "ids", roomActorIndices, 4);
    output << "  sprite_objects:\n";
    output << "    count: " << roomSpriteObjectIndices.size() << "\n";
    writeYamlIntegerList(output, "ids", roomSpriteObjectIndices, 4);

    if (!output)
    {
        errorMessage = "failed while writing " + outputPath.string();
        return false;
    }

    return true;
}

std::string formatIndoorRoomList(const std::vector<uint16_t> &roomIds)
{
    if (roomIds.empty())
    {
        return "None";
    }

    std::ostringstream stream;

    for (size_t index = 0; index < roomIds.size(); ++index)
    {
        if (index != 0)
        {
            stream << ", ";
        }

        stream << roomIds[index];
    }

    return stream.str();
}

const char *indoorFaceAttributeLabel(Game::FaceAttribute attribute)
{
    switch (attribute)
    {
    case Game::FaceAttribute::IsPortal:
        return "Portal";
    case Game::FaceAttribute::IsSecret:
        return "Secret";
    case Game::FaceAttribute::FlowDown:
        return "Flow Down";
    case Game::FaceAttribute::TextureAlignDown:
        return "Align Down";
    case Game::FaceAttribute::Fluid:
        return "Fluid";
    case Game::FaceAttribute::FlowUp:
        return "Flow Up";
    case Game::FaceAttribute::FlowLeft:
        return "Flow Left";
    case Game::FaceAttribute::SeenByParty:
        return "Seen By Party";
    case Game::FaceAttribute::XYPlane:
        return "XY Plane";
    case Game::FaceAttribute::XZPlane:
        return "XZ Plane";
    case Game::FaceAttribute::YZPlane:
        return "YZ Plane";
    case Game::FaceAttribute::FlowRight:
        return "Flow Right";
    case Game::FaceAttribute::TextureAlignLeft:
        return "Align Left";
    case Game::FaceAttribute::Invisible:
        return "Invisible";
    case Game::FaceAttribute::Animated:
        return "Animated";
    case Game::FaceAttribute::TextureAlignRight:
        return "Align Right";
    case Game::FaceAttribute::Outlined:
        return "Outlined";
    case Game::FaceAttribute::TextureAlignBottom:
        return "Align Bottom";
    case Game::FaceAttribute::TextureMoveByDoor:
        return "Move Texture By Door";
    case Game::FaceAttribute::TriggerByTouch:
        return "Trigger By Touch";
    case Game::FaceAttribute::HasHint:
        return "Has Hint";
    case Game::FaceAttribute::IndoorCarpet:
        return "Indoor Carpet";
    case Game::FaceAttribute::IndoorSky:
        return "Indoor Sky";
    case Game::FaceAttribute::FlipNormalU:
        return "Flip U";
    case Game::FaceAttribute::FlipNormalV:
        return "Flip V";
    case Game::FaceAttribute::Clickable:
        return "Clickable";
    case Game::FaceAttribute::PressurePlate:
        return "Pressure Plate";
    case Game::FaceAttribute::TriggerByMonster:
        return "Trigger By Monster";
    case Game::FaceAttribute::TriggerByObject:
        return "Trigger By Object";
    case Game::FaceAttribute::Untouchable:
        return "Untouchable";
    case Game::FaceAttribute::Lava:
        return "Lava";
    case Game::FaceAttribute::Picked:
        return "Picked";
    case Game::FaceAttribute::Indicate:
    default:
        return "Unknown";
    }
}

std::string formatIndoorFaceAttributeList(uint32_t attributes)
{
    static const std::array<Game::FaceAttribute, 32> AttributeOrder = {{
        Game::FaceAttribute::IsPortal,
        Game::FaceAttribute::IsSecret,
        Game::FaceAttribute::Invisible,
        Game::FaceAttribute::Clickable,
        Game::FaceAttribute::PressurePlate,
        Game::FaceAttribute::HasHint,
        Game::FaceAttribute::TriggerByTouch,
        Game::FaceAttribute::TriggerByMonster,
        Game::FaceAttribute::TriggerByObject,
        Game::FaceAttribute::Untouchable,
        Game::FaceAttribute::Animated,
        Game::FaceAttribute::Outlined,
        Game::FaceAttribute::TextureMoveByDoor,
        Game::FaceAttribute::TextureAlignLeft,
        Game::FaceAttribute::TextureAlignRight,
        Game::FaceAttribute::TextureAlignDown,
        Game::FaceAttribute::TextureAlignBottom,
        Game::FaceAttribute::FlipNormalU,
        Game::FaceAttribute::FlipNormalV,
        Game::FaceAttribute::Fluid,
        Game::FaceAttribute::Lava,
        Game::FaceAttribute::FlowUp,
        Game::FaceAttribute::FlowDown,
        Game::FaceAttribute::FlowLeft,
        Game::FaceAttribute::FlowRight,
        Game::FaceAttribute::XYPlane,
        Game::FaceAttribute::XZPlane,
        Game::FaceAttribute::YZPlane,
        Game::FaceAttribute::IndoorCarpet,
        Game::FaceAttribute::IndoorSky,
        Game::FaceAttribute::SeenByParty,
        Game::FaceAttribute::Picked
    }};

    std::string result;

    for (Game::FaceAttribute attribute : AttributeOrder)
    {
        if ((attributes & Game::faceAttributeBit(attribute)) == 0)
        {
            continue;
        }

        if (!result.empty())
        {
            result += ", ";
        }

        result += indoorFaceAttributeLabel(attribute);
    }

    return result.empty() ? "None" : result;
}

bool renderTerrainTilePreviewButton(
    const EditorOutdoorViewport &viewport,
    uint8_t tileId,
    bool selected,
    const ImVec2 &size)
{
    float u0 = 0.0f;
    float v0 = 0.0f;
    float u1 = 0.0f;
    float v1 = 0.0f;
    const bool hasPreview =
        bgfx::isValid(viewport.terrainTextureAtlasHandle())
        && viewport.tryGetTerrainTilePreviewUv(tileId, u0, v0, u1, v1);

    ImGui::PushID(static_cast<int>(tileId));

    if (!hasPreview)
    {
        char label[8] = {};
        std::snprintf(label, sizeof(label), "%02X", tileId);
        const bool clicked = ImGui::Button(label, size);
        ImGui::PopID();
        return clicked;
    }

    const ImVec2 cursorPosition = ImGui::GetCursorScreenPos();
    const bool clicked = ImGui::InvisibleButton("##TerrainTilePreview", size);
    const ImGuiID itemId = ImGui::GetItemID();
    const bool hovered = ImGui::IsItemHovered();
    const ImU32 borderColor = ImGui::GetColorU32(
        selected
            ? ImVec4(0.92f, 0.72f, 0.22f, 1.0f)
            : (hovered ? ImVec4(0.82f, 0.62f, 0.22f, 0.95f) : ImVec4(0.16f, 0.16f, 0.16f, 1.0f)));
    const ImU32 backgroundColor = ImGui::GetColorU32(ImVec4(0.08f, 0.08f, 0.08f, 1.0f));
    ImDrawList *pDrawList = ImGui::GetWindowDrawList();
    const ImVec2 endPosition = ImVec2(cursorPosition.x + size.x, cursorPosition.y + size.y);
    pDrawList->AddRectFilled(cursorPosition, endPosition, backgroundColor, 3.0f);
    pDrawList->AddImage(
        static_cast<ImTextureID>(static_cast<uintptr_t>(viewport.terrainTextureAtlasHandle().idx + 1)),
        ImVec2(cursorPosition.x + 2.0f, cursorPosition.y + 2.0f),
        ImVec2(endPosition.x - 2.0f, endPosition.y - 2.0f),
        ImVec2(u0, v0),
        ImVec2(u1, v1));
    pDrawList->AddRect(cursorPosition, endPosition, borderColor, 3.0f, 0, selected ? 2.0f : 1.0f);

    if (hovered)
    {
        ImGui::SetTooltip("Tile %u (0x%02X)", static_cast<unsigned>(tileId), static_cast<unsigned>(tileId));
    }

    ImGui::PopID();
    return clicked;
}

std::optional<std::vector<uint8_t>> loadBitmapPreviewPixels(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::vector<std::string> &bitmapTextureNames,
    const std::string &textureName,
    int &width,
    int &height)
{
    const std::string canonicalName = canonicalBitmapTextureName(bitmapTextureNames, textureName);

    if (canonicalName.empty())
    {
        return std::nullopt;
    }

    std::string virtualPath = "Data/bitmaps/" + canonicalName + ".png";
    std::optional<std::vector<uint8_t>> bitmapBytes = assetFileSystem.readBinaryFile(virtualPath);

    if (!bitmapBytes || bitmapBytes->empty())
    {
        virtualPath = "Data/bitmaps/" + canonicalName + ".bmp";
        bitmapBytes = assetFileSystem.readBinaryFile(virtualPath);
    }

    if (!bitmapBytes || bitmapBytes->empty())
    {
        return std::nullopt;
    }

    const std::optional<Engine::ImagePixelsBgra> image =
        Engine::decodeImagePixelsBgra(*bitmapBytes, virtualPath);

    if (!image)
    {
        return std::nullopt;
    }

    width = image->width;
    height = image->height;
    return image->pixels;
}

std::optional<std::string> findDirectoryEntryPath(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &directoryPath,
    const std::string &fileName)
{
    const std::vector<std::string> entries = assetFileSystem.enumerate(directoryPath);
    const std::string normalizedFileName = toLowerCopy(fileName);

    for (const std::string &entry : entries)
    {
        if (toLowerCopy(entry) == normalizedFileName)
        {
            return directoryPath + "/" + entry;
        }
    }

    return std::nullopt;
}

std::optional<std::array<uint8_t, 256 * 3>> loadActPalettePreview(
    const Engine::AssetFileSystem &assetFileSystem,
    int16_t paletteId)
{
    if (paletteId <= 0)
    {
        return std::nullopt;
    }

    char paletteFileName[32] = {};
    std::snprintf(paletteFileName, sizeof(paletteFileName), "pal%03d.act", static_cast<int>(paletteId));
    const std::optional<std::string> palettePath =
        findDirectoryEntryPath(assetFileSystem, "Data/bitmaps", paletteFileName);

    if (!palettePath)
    {
        return std::nullopt;
    }

    const std::optional<std::vector<uint8_t>> paletteBytes = assetFileSystem.readBinaryFile(*palettePath);

    if (!paletteBytes || paletteBytes->size() < 256 * 3)
    {
        return std::nullopt;
    }

    std::array<uint8_t, 256 * 3> palette = {};
    std::memcpy(palette.data(), paletteBytes->data(), palette.size());
    return palette;
}

std::optional<std::vector<uint8_t>> loadSpritePreviewPixels(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &textureName,
    int16_t paletteId,
    int &width,
    int &height)
{
    std::optional<std::string> bitmapPath =
        findDirectoryEntryPath(assetFileSystem, "Data/sprites", textureName + ".png");

    if (!bitmapPath)
    {
        bitmapPath = findDirectoryEntryPath(assetFileSystem, "Data/sprites", textureName + ".bmp");
    }

    if (!bitmapPath)
    {
        return std::nullopt;
    }

    const std::optional<std::vector<uint8_t>> bitmapBytes = assetFileSystem.readBinaryFile(*bitmapPath);

    if (!bitmapBytes || bitmapBytes->empty())
    {
        return std::nullopt;
    }

    Engine::ImageDecodeOptions decodeOptions = {};
    decodeOptions.overridePalette = loadActPalettePreview(assetFileSystem, paletteId);
    decodeOptions.applyMagentaTransparencyKey = true;
    decodeOptions.applyTealTransparencyKey = true;

    const std::optional<Engine::ImagePixelsBgra> image =
        Engine::decodeImagePixelsBgra(*bitmapBytes, *bitmapPath, decodeOptions);

    if (!image)
    {
        return std::nullopt;
    }

    width = image->width;
    height = image->height;
    return image->pixels;
}

int16_t clampToInt16(int value)
{
    return static_cast<int16_t>(std::clamp(value, -32768, 32767));
}

std::pair<int, int> faceTextureCoordinateRange(const std::vector<int16_t> &coordinates)
{
    if (coordinates.empty())
    {
        return {0, 0};
    }

    int minimum = coordinates.front();
    int maximum = coordinates.front();

    for (int16_t value : coordinates)
    {
        minimum = std::min(minimum, static_cast<int>(value));
        maximum = std::max(maximum, static_cast<int>(value));
    }

    return {minimum, maximum};
}

void flipFaceTextureAxis(std::vector<int16_t> &coordinates)
{
    const auto [minimum, maximum] = faceTextureCoordinateRange(coordinates);

    for (int16_t &value : coordinates)
    {
        value = clampToInt16(minimum + maximum - static_cast<int>(value));
    }
}

void scaleFaceTextureAxis(std::vector<int16_t> &coordinates, float scale)
{
    if (coordinates.empty())
    {
        return;
    }

    const auto [minimum, maximum] = faceTextureCoordinateRange(coordinates);
    const float center = (static_cast<float>(minimum) + static_cast<float>(maximum)) * 0.5f;

    for (int16_t &value : coordinates)
    {
        const float scaled = center + (static_cast<float>(value) - center) * scale;
        value = clampToInt16(static_cast<int>(std::lround(scaled)));
    }
}

void fitFaceTextureAxis(std::vector<int16_t> &coordinates, int extent)
{
    if (coordinates.empty() || extent <= 0)
    {
        return;
    }

    const auto [minimum, maximum] = faceTextureCoordinateRange(coordinates);

    if (minimum == maximum)
    {
        coordinates.front() = 0;

        for (size_t index = 1; index < coordinates.size(); ++index)
        {
            coordinates[index] = static_cast<int16_t>(extent);
        }

        return;
    }

    const float sourceRange = static_cast<float>(maximum - minimum);

    for (int16_t &value : coordinates)
    {
        const float normalized = (static_cast<float>(value) - static_cast<float>(minimum)) / sourceRange;
        value = clampToInt16(static_cast<int>(std::lround(normalized * static_cast<float>(extent))));
    }
}

void resetFaceTextureMappingFromGeometry(
    const std::vector<Game::OutdoorBModelVertex> &vertices,
    Game::OutdoorBModelFace &face)
{
    if (face.vertexIndices.size() < 3)
    {
        return;
    }

    const auto vertexAt = [&vertices](uint16_t index) -> const Game::OutdoorBModelVertex &
    {
        return vertices[index];
    };

    const Game::OutdoorBModelVertex &a = vertexAt(face.vertexIndices[0]);
    const Game::OutdoorBModelVertex &b = vertexAt(face.vertexIndices[1]);
    const Game::OutdoorBModelVertex &c = vertexAt(face.vertexIndices[2]);
    const float abX = static_cast<float>(b.x - a.x);
    const float abY = static_cast<float>(b.y - a.y);
    const float abZ = static_cast<float>(b.z - a.z);
    const float acX = static_cast<float>(c.x - a.x);
    const float acY = static_cast<float>(c.y - a.y);
    const float acZ = static_cast<float>(c.z - a.z);
    const float normalX = abY * acZ - abZ * acY;
    const float normalY = abZ * acX - abX * acZ;
    const float normalZ = abX * acY - abY * acX;
    const float absNormalX = std::fabs(normalX);
    const float absNormalY = std::fabs(normalY);
    const float absNormalZ = std::fabs(normalZ);

    face.textureUs.clear();
    face.textureVs.clear();
    face.textureUs.reserve(face.vertexIndices.size());
    face.textureVs.reserve(face.vertexIndices.size());

    for (uint16_t vertexIndex : face.vertexIndices)
    {
        if (vertexIndex >= vertices.size())
        {
            face.textureUs.push_back(0);
            face.textureVs.push_back(0);
            continue;
        }

        const Game::OutdoorBModelVertex &vertex = vertices[vertexIndex];
        int16_t textureU = 0;
        int16_t textureV = 0;

        if (absNormalZ >= absNormalX && absNormalZ >= absNormalY)
        {
            textureU = clampToInt16(vertex.x);
            textureV = clampToInt16(-vertex.y);
        }
        else if (absNormalX >= absNormalY)
        {
            textureU = clampToInt16(vertex.y);
            textureV = clampToInt16(-vertex.z);
        }
        else
        {
            textureU = clampToInt16(vertex.x);
            textureV = clampToInt16(-vertex.z);
        }

        face.textureUs.push_back(textureU);
        face.textureVs.push_back(textureV);
    }

    face.textureDeltaU = 0;
    face.textureDeltaV = 0;
}

bx::Vec3 faceNormal(
    const std::vector<Game::OutdoorBModelVertex> &vertices,
    const Game::OutdoorBModelFace &face)
{
    if (face.vertexIndices.size() < 3)
    {
        return {0.0f, 0.0f, 0.0f};
    }

    const auto vertexAt = [&vertices](uint16_t index) -> const Game::OutdoorBModelVertex &
    {
        return vertices[index];
    };

    const Game::OutdoorBModelVertex &a = vertexAt(face.vertexIndices[0]);
    const Game::OutdoorBModelVertex &b = vertexAt(face.vertexIndices[1]);
    const Game::OutdoorBModelVertex &c = vertexAt(face.vertexIndices[2]);
    const bx::Vec3 edge1 = {
        static_cast<float>(b.x - a.x),
        static_cast<float>(b.y - a.y),
        static_cast<float>(b.z - a.z)};
    const bx::Vec3 edge2 = {
        static_cast<float>(c.x - a.x),
        static_cast<float>(c.y - a.y),
        static_cast<float>(c.z - a.z)};
    const bx::Vec3 normal = {
        edge1.y * edge2.z - edge1.z * edge2.y,
        edge1.z * edge2.x - edge1.x * edge2.z,
        edge1.x * edge2.y - edge1.y * edge2.x};
    const float length = std::sqrt(normal.x * normal.x + normal.y * normal.y + normal.z * normal.z);

    if (length <= 0.0001f)
    {
        return {0.0f, 0.0f, 0.0f};
    }

    const float invLength = 1.0f / length;
    return {
        normal.x * invLength,
        normal.y * invLength,
        normal.z * invLength};
}

float faceOutwardDot(
    const std::vector<Game::OutdoorBModelVertex> &vertices,
    const Game::OutdoorBModelFace &face,
    float modelCenterX,
    float modelCenterY,
    float modelCenterZ)
{
    if (face.vertexIndices.empty())
    {
        return 0.0f;
    }

    bx::Vec3 normal = faceNormal(vertices, face);
    bx::Vec3 center = {0.0f, 0.0f, 0.0f};
    int validVertexCount = 0;

    for (uint16_t vertexIndex : face.vertexIndices)
    {
        if (vertexIndex >= vertices.size())
        {
            continue;
        }

        center.x += static_cast<float>(vertices[vertexIndex].x);
        center.y += static_cast<float>(vertices[vertexIndex].y);
        center.z += static_cast<float>(vertices[vertexIndex].z);
        ++validVertexCount;
    }

    if (validVertexCount == 0)
    {
        return 0.0f;
    }

    const float invCount = 1.0f / static_cast<float>(validVertexCount);
    center.x *= invCount;
    center.y *= invCount;
    center.z *= invCount;

    return normal.x * (center.x - modelCenterX)
        + normal.y * (center.y - modelCenterY)
        + normal.z * (center.z - modelCenterZ);
}

void reverseFaceWinding(Game::OutdoorBModelFace &face)
{
    std::reverse(face.vertexIndices.begin(), face.vertexIndices.end());
    std::reverse(face.textureUs.begin(), face.textureUs.end());
    std::reverse(face.textureVs.begin(), face.textureVs.end());
}

void orientFaceWindingOutward(
    const std::vector<Game::OutdoorBModelVertex> &vertices,
    Game::OutdoorBModelFace &face,
    float modelCenterX,
    float modelCenterY,
    float modelCenterZ)
{
    if (face.vertexIndices.size() < 3)
    {
        return;
    }

    bool shouldReverse = false;

    if (face.polygonType == 0x3 || face.polygonType == 0x4)
    {
        const bx::Vec3 normal = faceNormal(vertices, face);
        shouldReverse = normal.z < 0.0f;
    }
    else
    {
        shouldReverse = faceOutwardDot(vertices, face, modelCenterX, modelCenterY, modelCenterZ) < 0.0f;
    }

    if (shouldReverse)
    {
        reverseFaceWinding(face);
    }
}

void renderInspectorSectionHeader(const char *pLabel)
{
    ImGui::Spacing();
    ImGui::PushStyleColor(ImGuiCol_Separator, colorFromRgb(0x37414D));
    ImGui::PushStyleColor(ImGuiCol_Text, colorFromRgb(0xF8E4C7));
    ImGui::SeparatorText(pLabel);
    ImGui::PopStyleColor(2);
}

bool beginInspectorSectionBlock(const char *pLabel, bool defaultOpen = true)
{
    ImGui::PushStyleColor(ImGuiCol_Header, colorFromRgb(0x23292F));
    ImGui::PushStyleColor(ImGuiCol_HeaderHovered, colorFromRgb(0x2A3139));
    ImGui::PushStyleColor(ImGuiCol_HeaderActive, colorFromRgb(0x4B3318));
    ImGui::PushStyleColor(ImGuiCol_Border, colorFromRgb(0x404854));
    ImGui::PushStyleColor(ImGuiCol_Text, colorFromRgb(0xF8E4C7));
    ImGui::PushStyleVar(ImGuiStyleVar_FramePadding, ImVec2(10.0f, 7.0f));
    ImGui::PushStyleVar(ImGuiStyleVar_FrameBorderSize, 1.0f);
    const bool open = ImGui::CollapsingHeader(
        pLabel,
        (defaultOpen ? ImGuiTreeNodeFlags_DefaultOpen : ImGuiTreeNodeFlags_None) | ImGuiTreeNodeFlags_Framed);
    ImGui::PopStyleVar(2);
    ImGui::PopStyleColor(5);

    if (open)
    {
        ImGui::Indent(8.0f);
        ImGui::Spacing();
    }

    return open;
}

void endInspectorSectionBlock()
{
    ImGui::Unindent(8.0f);
    ImGui::Spacing();
}

bool editStringField(EditorSession &session, const char *pLabel, std::string &value, size_t capacity)
{
    const size_t bufferSize = std::max(capacity, value.size() + 1);
    std::vector<char> buffer(bufferSize, '\0');
    std::copy(value.begin(), value.end(), buffer.begin());

    beginInspectorFieldRow(pLabel);

    if (!ImGui::InputText(inspectorFieldId(pLabel).c_str(), buffer.data(), buffer.size()))
    {
        return false;
    }

    session.captureUndoSnapshot();
    value = buffer.data();
    return true;
}

bool editTransientStringField(const char *pLabel, std::string &value, size_t capacity)
{
    const size_t bufferSize = std::max(capacity, value.size() + 1);
    std::vector<char> buffer(bufferSize, '\0');
    std::copy(value.begin(), value.end(), buffer.begin());

    beginInspectorFieldRow(pLabel);

    if (!ImGui::InputText(inspectorFieldId(pLabel).c_str(), buffer.data(), buffer.size()))
    {
        return false;
    }

    value = buffer.data();
    return true;
}

bool editIntField(EditorSession &session, const char *pLabel, int &value, int minimum, int maximum)
{
    int editedValue = value;

    beginInspectorFieldRow(pLabel);

    if (!ImGui::InputInt(inspectorFieldId(pLabel).c_str(), &editedValue))
    {
        return false;
    }

    editedValue = std::clamp(editedValue, minimum, maximum);

    if (editedValue == value)
    {
        return false;
    }

    session.captureUndoSnapshot();
    value = editedValue;
    return true;
}

bool editTransientIntField(const char *pLabel, int &value, int minimum, int maximum)
{
    int editedValue = value;

    beginInspectorFieldRow(pLabel);

    if (!ImGui::InputInt(inspectorFieldId(pLabel).c_str(), &editedValue))
    {
        return false;
    }

    editedValue = std::clamp(editedValue, minimum, maximum);

    if (editedValue == value)
    {
        return false;
    }

    value = editedValue;
    return true;
}

bool editUInt8Field(EditorSession &session, const char *pLabel, uint8_t &value)
{
    int editedValue = value;

    beginInspectorFieldRow(pLabel);

    if (!ImGui::InputInt(inspectorFieldId(pLabel).c_str(), &editedValue))
    {
        return false;
    }

    editedValue = std::clamp(editedValue, 0, 255);

    if (editedValue == value)
    {
        return false;
    }

    session.captureUndoSnapshot();
    value = static_cast<uint8_t>(editedValue);
    return true;
}

bool editUInt16Field(EditorSession &session, const char *pLabel, uint16_t &value)
{
    int editedValue = value;

    beginInspectorFieldRow(pLabel);

    if (!ImGui::InputInt(inspectorFieldId(pLabel).c_str(), &editedValue))
    {
        return false;
    }

    editedValue = std::clamp(editedValue, 0, 65535);

    if (editedValue == value)
    {
        return false;
    }

    session.captureUndoSnapshot();
    value = static_cast<uint16_t>(editedValue);
    return true;
}

bool editTransientUInt16Field(const char *pLabel, uint16_t &value)
{
    int editedValue = value;

    beginInspectorFieldRow(pLabel);

    if (!ImGui::InputInt(inspectorFieldId(pLabel).c_str(), &editedValue))
    {
        return false;
    }

    editedValue = std::clamp(editedValue, 0, 65535);

    if (editedValue == value)
    {
        return false;
    }

    value = static_cast<uint16_t>(editedValue);
    return true;
}

bool editMapEventField(EditorSession &session, const char *pLabel, uint16_t &value)
{
    const std::vector<EditorIdLabelOption> &options = session.mapEventOptions();

    beginInspectorFieldRow(pLabel);

    bool changed = false;
    uint32_t selectedValue = value;
    const std::string comboId = inspectorFieldId(pLabel) + "/combo";
    const std::string preview = selectorPreviewLabel(selectedValue, options, "<none>", "Event");
    const float inputWidth = 90.0f;
    const float spacing = ImGui::GetStyle().ItemInnerSpacing.x;
    const float comboWidth = std::max(80.0f, ImGui::GetContentRegionAvail().x - inputWidth - spacing);

    ImGui::SetNextItemWidth(comboWidth);

    if (ImGui::BeginCombo(comboId.c_str(), preview.c_str()))
    {
        const ImGuiID filterStorageId = ImGui::GetID((comboId + "/filter").c_str());
        static std::unordered_map<ImGuiID, std::string> filters;
        std::string &filter = filters[filterStorageId];
        char filterBuffer[128] = {};
        std::snprintf(filterBuffer, sizeof(filterBuffer), "%s", filter.c_str());
        ImGui::SetNextItemWidth(-FLT_MIN);

        if (ImGui::InputText("##Filter", filterBuffer, sizeof(filterBuffer)))
        {
            filter = filterBuffer;
        }

        const std::string normalizedFilter = toLowerCopy(filter);
        const bool zeroSelected = selectedValue == 0;

        if ((normalizedFilter.empty() || std::string("<none>").find(normalizedFilter) != std::string::npos)
            && ImGui::Selectable("<none>", zeroSelected))
        {
            if (value != 0)
            {
                session.captureUndoSnapshot();
                value = 0;
                changed = true;
            }
        }

        if (zeroSelected)
        {
            ImGui::SetItemDefaultFocus();
        }

        for (const EditorIdLabelOption &option : options)
        {
            if (!optionMatchesFilter(option, normalizedFilter))
            {
                continue;
            }

            const bool selected = option.id == selectedValue;

            if (ImGui::Selectable(option.label.c_str(), selected))
            {
                if (option.id != value)
                {
                    session.captureUndoSnapshot();
                    value = static_cast<uint16_t>(option.id);
                    changed = true;
                }
            }

            if (selected)
            {
                ImGui::SetItemDefaultFocus();
            }
        }

        ImGui::EndCombo();
    }

    ImGui::SameLine();

    int editedValue = value;
    ImGui::SetNextItemWidth(inputWidth);

    if (ImGui::InputInt((inspectorFieldId(pLabel) + "/raw").c_str(), &editedValue))
    {
        editedValue = std::clamp(editedValue, 0, 65535);

        if (editedValue != value)
        {
            session.captureUndoSnapshot();
            value = static_cast<uint16_t>(editedValue);
            changed = true;
        }
    }

    return changed;
}

void renderResolvedMapEventField(EditorSession &session, const char *pLabel, uint16_t eventId)
{
    const std::optional<std::string> description = session.describeMapEvent(eventId);

    if (description)
    {
        renderInspectorReadOnlyField(pLabel, *description);
        return;
    }

    renderInspectorReadOnlyField(pLabel, eventId == 0 ? "<none>" : "<unresolved>");
}

bool editInt16Field(EditorSession &session, const char *pLabel, int16_t &value)
{
    int editedValue = value;

    beginInspectorFieldRow(pLabel);

    if (!ImGui::InputInt(inspectorFieldId(pLabel).c_str(), &editedValue))
    {
        return false;
    }

    editedValue = std::clamp(editedValue, -32768, 32767);

    if (editedValue == value)
    {
        return false;
    }

    session.captureUndoSnapshot();
    value = static_cast<int16_t>(editedValue);
    return true;
}

bool editTransientInt16Field(const char *pLabel, int16_t &value)
{
    int editedValue = value;

    beginInspectorFieldRow(pLabel);

    if (!ImGui::InputInt(inspectorFieldId(pLabel).c_str(), &editedValue))
    {
        return false;
    }

    editedValue = std::clamp(editedValue, -32768, 32767);

    if (editedValue == value)
    {
        return false;
    }

    value = static_cast<int16_t>(editedValue);
    return true;
}

bool editUInt32Field(EditorSession &session, const char *pLabel, uint32_t &value)
{
    uint32_t editedValue = value;

    beginInspectorFieldRow(pLabel);

    if (!ImGui::InputScalar(inspectorFieldId(pLabel).c_str(), ImGuiDataType_U32, &editedValue))
    {
        return false;
    }

    if (editedValue == value)
    {
        return false;
    }

    session.captureUndoSnapshot();
    value = editedValue;
    return true;
}

bool editTransientUInt32Field(const char *pLabel, uint32_t &value)
{
    uint32_t editedValue = value;

    beginInspectorFieldRow(pLabel);

    if (!ImGui::InputScalar(inspectorFieldId(pLabel).c_str(), ImGuiDataType_U32, &editedValue))
    {
        return false;
    }

    if (editedValue == value)
    {
        return false;
    }

    value = editedValue;
    return true;
}

bool editFloatField(EditorSession &session, const char *pLabel, float &value, float step = 1.0f)
{
    float editedValue = value;

    beginInspectorFieldRow(pLabel);

    if (!ImGui::InputFloat(inspectorFieldId(pLabel).c_str(), &editedValue, step, step * 10.0f, "%.2f"))
    {
        return false;
    }

    if (std::fabs(editedValue - value) <= 0.0001f)
    {
        return false;
    }

    session.captureUndoSnapshot();
    value = editedValue;
    return true;
}

bool editBufferedIntField(
    EditorSession &session,
    const char *pLabel,
    int &value,
    int minimum,
    int maximum)
{
    int editedValue = value;

    beginInspectorFieldRow(pLabel);

    if (!ImGui::InputInt(
            inspectorFieldId(pLabel).c_str(),
            &editedValue,
            1,
            100,
            ImGuiInputTextFlags_EnterReturnsTrue))
    {
        return false;
    }

    editedValue = std::clamp(editedValue, minimum, maximum);

    if (editedValue == value)
    {
        return false;
    }

    session.captureUndoSnapshot();
    value = editedValue;
    return true;
}

int32_t readChestRecordId(const Game::MapDeltaChest &chest, size_t recordIndex)
{
    if ((recordIndex + 1) * ChestItemRecordSize > chest.rawItems.size())
    {
        return 0;
    }

    int32_t rawItemId = 0;
    std::memcpy(&rawItemId, chest.rawItems.data() + recordIndex * ChestItemRecordSize, sizeof(rawItemId));
    return rawItemId;
}

void writeChestRecordId(Game::MapDeltaChest &chest, size_t recordIndex, int32_t rawItemId)
{
    if (chest.rawItems.size() < ChestItemRecordCount * ChestItemRecordSize)
    {
        chest.rawItems.resize(ChestItemRecordCount * ChestItemRecordSize, 0);
    }

    std::memcpy(chest.rawItems.data() + recordIndex * ChestItemRecordSize, &rawItemId, sizeof(rawItemId));
}

void clearChestRecord(Game::MapDeltaChest &chest, size_t recordIndex)
{
    if ((recordIndex + 1) * ChestItemRecordSize > chest.rawItems.size())
    {
        return;
    }

    std::fill(
        chest.rawItems.begin() + static_cast<ptrdiff_t>(recordIndex * ChestItemRecordSize),
        chest.rawItems.begin() + static_cast<ptrdiff_t>((recordIndex + 1) * ChestItemRecordSize),
        0);

    for (int16_t &cellValue : chest.inventoryMatrix)
    {
        if (cellValue == static_cast<int16_t>(recordIndex + 1))
        {
            cellValue = 0;
        }
    }
}

std::optional<size_t> findFirstEmptyChestRecord(const Game::MapDeltaChest &chest)
{
    for (size_t recordIndex = 0; recordIndex < ChestItemRecordCount; ++recordIndex)
    {
        if (readChestRecordId(chest, recordIndex) == 0)
        {
            return recordIndex;
        }
    }

    return std::nullopt;
}

bool editPositionField(EditorSession &session, const char *pLabel, int &x, int &y, int &z)
{
    std::array<int, 3> values = {x, y, z};

    beginInspectorFieldRow(pLabel);

    if (!ImGui::InputInt3(inspectorFieldId(pLabel).c_str(), values.data()))
    {
        return false;
    }

    if (values[0] == x && values[1] == y && values[2] == z)
    {
        return false;
    }

    session.captureUndoSnapshot();
    x = values[0];
    y = values[1];
    z = values[2];
    return true;
}

void recomputeBModelMetadata(Game::OutdoorBModel &bmodel)
{
    if (bmodel.vertices.empty())
    {
        bmodel.positionX = 0;
        bmodel.positionY = 0;
        bmodel.positionZ = 0;
        bmodel.minX = 0;
        bmodel.minY = 0;
        bmodel.minZ = 0;
        bmodel.maxX = 0;
        bmodel.maxY = 0;
        bmodel.maxZ = 0;
        bmodel.boundingCenterX = 0;
        bmodel.boundingCenterY = 0;
        bmodel.boundingCenterZ = 0;
        bmodel.boundingRadius = 0;
        return;
    }

    float minX = std::numeric_limits<float>::max();
    float minY = std::numeric_limits<float>::max();
    float minZ = std::numeric_limits<float>::max();
    float maxX = std::numeric_limits<float>::lowest();
    float maxY = std::numeric_limits<float>::lowest();
    float maxZ = std::numeric_limits<float>::lowest();

    for (const Game::OutdoorBModelVertex &vertex : bmodel.vertices)
    {
        minX = std::min(minX, static_cast<float>(vertex.x));
        minY = std::min(minY, static_cast<float>(vertex.y));
        minZ = std::min(minZ, static_cast<float>(vertex.z));
        maxX = std::max(maxX, static_cast<float>(vertex.x));
        maxY = std::max(maxY, static_cast<float>(vertex.y));
        maxZ = std::max(maxZ, static_cast<float>(vertex.z));
    }

    const float centerX = (minX + maxX) * 0.5f;
    const float centerY = (minY + maxY) * 0.5f;
    const float centerZ = (minZ + maxZ) * 0.5f;
    float maxRadiusSquared = 0.0f;

    for (const Game::OutdoorBModelVertex &vertex : bmodel.vertices)
    {
        const float deltaX = static_cast<float>(vertex.x) - centerX;
        const float deltaY = static_cast<float>(vertex.y) - centerY;
        const float deltaZ = static_cast<float>(vertex.z) - centerZ;
        maxRadiusSquared = std::max(maxRadiusSquared, deltaX * deltaX + deltaY * deltaY + deltaZ * deltaZ);
    }

    bmodel.positionX = static_cast<int>(std::lround(centerX));
    bmodel.positionY = static_cast<int>(std::lround(centerY));
    bmodel.positionZ = static_cast<int>(std::lround(centerZ));
    bmodel.minX = static_cast<int>(std::floor(minX));
    bmodel.minY = static_cast<int>(std::floor(minY));
    bmodel.minZ = static_cast<int>(std::floor(minZ));
    bmodel.maxX = static_cast<int>(std::ceil(maxX));
    bmodel.maxY = static_cast<int>(std::ceil(maxY));
    bmodel.maxZ = static_cast<int>(std::ceil(maxZ));
    bmodel.boundingCenterX = static_cast<int>(std::lround(centerX));
    bmodel.boundingCenterY = static_cast<int>(std::lround(centerY));
    bmodel.boundingCenterZ = static_cast<int>(std::lround(centerZ));
    bmodel.boundingRadius = static_cast<int>(std::ceil(std::sqrt(maxRadiusSquared)));
}

bool editInt16PositionField(EditorSession &session, const char *pLabel, int16_t &x, int16_t &y, int16_t &z)
{
    std::array<int, 3> values = {x, y, z};

    beginInspectorFieldRow(pLabel);

    if (!ImGui::InputInt3(inspectorFieldId(pLabel).c_str(), values.data()))
    {
        return false;
    }

    values[0] = std::clamp(values[0], -32768, 32767);
    values[1] = std::clamp(values[1], -32768, 32767);
    values[2] = std::clamp(values[2], -32768, 32767);

    if (values[0] == x && values[1] == y && values[2] == z)
    {
        return false;
    }

    session.captureUndoSnapshot();
    x = static_cast<int16_t>(values[0]);
    y = static_cast<int16_t>(values[1]);
    z = static_cast<int16_t>(values[2]);
    return true;
}

bool editLookupIndicesField(EditorSession &session, const char *pLabel, std::array<uint16_t, 4> &values)
{
    std::array<int, 4> editedValues = {
        static_cast<int>(values[0]),
        static_cast<int>(values[1]),
        static_cast<int>(values[2]),
        static_cast<int>(values[3])
    };

    beginInspectorFieldRow(pLabel);

    if (!ImGui::InputInt4(inspectorFieldId(pLabel).c_str(), editedValues.data()))
    {
        return false;
    }

    bool changed = false;

    for (size_t index = 0; index < editedValues.size(); ++index)
    {
        const int clampedValue = std::clamp(editedValues[index], 0, 65535);

        if (clampedValue != values[index])
        {
            values[index] = static_cast<uint16_t>(clampedValue);
            changed = true;
        }
    }

    if (changed)
    {
        session.captureUndoSnapshot();
    }

    return changed;
}

bool editStringOptionField(
    EditorSession &session,
    const char *pLabel,
    std::string &value,
    const std::vector<std::string> &options)
{
    beginInspectorFieldRow(pLabel);

    const std::string comboId = inspectorFieldId(pLabel);
    const char *pPreview = value.empty() ? "<none>" : value.c_str();

    if (!ImGui::BeginCombo(comboId.c_str(), pPreview))
    {
        return false;
    }

    const ImGuiID filterStorageId = ImGui::GetID((comboId + "/filter").c_str());
    static std::unordered_map<ImGuiID, std::string> filters;
    std::string &filter = filters[filterStorageId];
    char filterBuffer[128] = {};
    std::snprintf(filterBuffer, sizeof(filterBuffer), "%s", filter.c_str());
    ImGui::SetNextItemWidth(-FLT_MIN);

    if (ImGui::InputText("##Filter", filterBuffer, sizeof(filterBuffer)))
    {
        filter = filterBuffer;
    }

    const std::string normalizedFilter = toLowerCopy(filter);
    bool changed = false;

    if ((normalizedFilter.empty() || std::string("<none>").find(normalizedFilter) != std::string::npos)
        && ImGui::Selectable("<none>", value.empty()))
    {
        if (!value.empty())
        {
            session.captureUndoSnapshot();
            value.clear();
            changed = true;
        }
    }

    for (const std::string &option : options)
    {
        if (!normalizedFilter.empty() && toLowerCopy(option).find(normalizedFilter) == std::string::npos)
        {
            continue;
        }

        const bool selected = option == value;

        if (ImGui::Selectable(option.c_str(), selected))
        {
            if (option != value)
            {
                session.captureUndoSnapshot();
                value = option;
                changed = true;
            }
        }

        if (selected)
        {
            ImGui::SetItemDefaultFocus();
        }
    }

    ImGui::EndCombo();
    return changed;
}

bool editBitCheckbox(EditorSession &session, const char *pLabel, int32_t &bitField, int32_t bitMask)
{
    bool enabled = (bitField & bitMask) != 0;

    beginInspectorFieldRow(pLabel);

    if (!ImGui::Checkbox(inspectorFieldId(pLabel).c_str(), &enabled))
    {
        return false;
    }

    session.captureUndoSnapshot();

    if (enabled)
    {
        bitField |= bitMask;
    }
    else
    {
        bitField &= ~bitMask;
    }

    return true;
}

bool editBitCheckbox(EditorSession &session, const char *pLabel, uint32_t &bitField, uint32_t bitMask)
{
    bool enabled = (bitField & bitMask) != 0;

    beginInspectorFieldRow(pLabel);

    if (!ImGui::Checkbox(inspectorFieldId(pLabel).c_str(), &enabled))
    {
        return false;
    }

    session.captureUndoSnapshot();

    if (enabled)
    {
        bitField |= bitMask;
    }
    else
    {
        bitField &= ~bitMask;
    }

    return true;
}

bool editBitCheckbox(EditorSession &session, const char *pLabel, uint8_t &bitField, uint8_t bitMask)
{
    bool enabled = (bitField & bitMask) != 0;
    beginInspectorFieldRow(pLabel);

    if (!ImGui::Checkbox(inspectorFieldId(pLabel).c_str(), &enabled))
    {
        return false;
    }

    session.captureUndoSnapshot();

    if (enabled)
    {
        bitField = static_cast<uint8_t>(bitField | bitMask);
    }
    else
    {
        bitField = static_cast<uint8_t>(bitField & ~bitMask);
    }

    return true;
}

bool editBitCheckbox(EditorSession &session, const char *pLabel, uint16_t &bitField, uint16_t bitMask)
{
    bool enabled = (bitField & bitMask) != 0;

    beginInspectorFieldRow(pLabel);

    if (!ImGui::Checkbox(inspectorFieldId(pLabel).c_str(), &enabled))
    {
        return false;
    }

    session.captureUndoSnapshot();

    if (enabled)
    {
        bitField |= bitMask;
    }
    else
    {
        bitField &= ~bitMask;
    }

    return true;
}

bool editActorHostilityTypeField(EditorSession &session, uint8_t &hostilityType)
{
    int editedValue = hostilityType;

    beginInspectorFieldRow("Hostility Type");

    if (!ImGui::InputInt("##Hostility Type", &editedValue))
    {
        return false;
    }

    editedValue = std::clamp(editedValue, 0, 255);

    if (editedValue == hostilityType)
    {
        return false;
    }

    session.captureUndoSnapshot();
    hostilityType = static_cast<uint8_t>(editedValue);
    return true;
}

void applyMonsterTemplateSelection(EditorSession &session, Game::MapDeltaActor &actor, int16_t previousMonsterInfoId);

bool editMonsterTemplateField(EditorSession &session, Game::MapDeltaActor &actor)
{
    const int16_t previousMonsterInfoId = actor.monsterInfoId;
    uint32_t selectedId = actor.monsterInfoId > 0 ? static_cast<uint32_t>(actor.monsterInfoId) : 0;

    if (!editOptionField(
            session,
            "Monster Template",
            selectedId,
            session.monsterOptions(),
            "<none>",
            "Monster Template"))
    {
        return false;
    }

    actor.monsterInfoId = static_cast<int16_t>(std::min<uint32_t>(selectedId, 32767));
    applyMonsterTemplateSelection(session, actor, previousMonsterInfoId);
    return true;
}

void applyMonsterTemplateSelection(EditorSession &session, Game::MapDeltaActor &actor, int16_t previousMonsterInfoId)
{
    const Game::MonsterTable &monsterTable = session.monsterTable();

    if (actor.monsterId <= 0 || actor.monsterId == previousMonsterInfoId)
    {
        actor.monsterId = actor.monsterInfoId;
    }

    const Game::MonsterTable::MonsterStatsEntry *pStats = monsterTable.findStatsById(actor.monsterInfoId);
    const Game::MonsterEntry *pMonsterEntry = monsterTable.findById(actor.monsterId);

    if (pStats != nullptr)
    {
        actor.hp = static_cast<int16_t>(std::clamp(pStats->hitPoints, 0, 32767));
        actor.hostilityType = static_cast<uint8_t>(std::clamp(pStats->hostility, 0, 255));
    }
    else
    {
        actor.hp = 0;
        actor.hostilityType = 0;
    }

    if (pMonsterEntry != nullptr)
    {
        actor.radius = pMonsterEntry->radius;
        actor.height = pMonsterEntry->height;
        actor.moveSpeed = pMonsterEntry->movementSpeed;
    }
    else
    {
        actor.radius = 0;
        actor.height = 0;
        actor.moveSpeed = 0;
    }

    actor.spriteIds = {};
}

bool editTransientMonsterTemplateField(EditorSession &session, Game::MapDeltaActor &actor)
{
    const int16_t previousMonsterInfoId = actor.monsterInfoId;
    uint32_t selectedId = actor.monsterInfoId > 0 ? static_cast<uint32_t>(actor.monsterInfoId) : 0;

    if (!editTransientOptionField(
            "Monster Template",
            selectedId,
            session.monsterOptions(),
            "<none>",
            "Monster Template"))
    {
        return false;
    }

    actor.monsterInfoId = static_cast<int16_t>(std::min<uint32_t>(selectedId, 32767));
    applyMonsterTemplateSelection(session, actor, previousMonsterInfoId);
    return true;
}

bool editObjectDescriptionField(EditorSession &session, uint16_t &objectDescriptionId)
{
    uint32_t selectedId = objectDescriptionId;

    if (!editOptionField(
            session,
            "Object Description",
            selectedId,
            session.objectOptions(),
            nullptr,
            "Object"))
    {
        return false;
    }

    objectDescriptionId = static_cast<uint16_t>(std::min<uint32_t>(selectedId, 65535));
    return true;
}

bool editSpriteObjectContainedItemField(EditorSession &session, Game::MapDeltaSpriteObject &spriteObject)
{
    uint32_t selectedId = Game::spriteObjectContainedItemId(spriteObject.rawContainingItem);

    if (!editOptionField(
            session,
            "Contained Item",
            selectedId,
            session.itemOptions(),
            "<none>",
            "Item"))
    {
        return false;
    }

    Game::writeSpriteObjectContainedItemPayload(spriteObject.rawContainingItem, selectedId);
    session.setPendingSpriteObjectItemId(selectedId);

    if (const std::optional<uint16_t> objectDescriptionId = session.objectDescriptionIdForItem(selectedId))
    {
        spriteObject.objectDescriptionId = *objectDescriptionId;
        applySpriteObjectVisualDescriptor(session, spriteObject);
        session.setPendingSpriteObjectDescriptionId(*objectDescriptionId);
    }

    return true;
}

bool editTransientSpriteObjectContainedItemField(EditorSession &session, uint32_t &itemId)
{
    uint32_t selectedId = itemId;

    if (!editTransientOptionField(
            "Contained Item",
            selectedId,
            session.itemOptions(),
            "<none>",
            "Item"))
    {
        return false;
    }

    itemId = selectedId;
    session.setPendingSpriteObjectItemId(selectedId);

    if (const std::optional<uint16_t> objectDescriptionId = session.objectDescriptionIdForItem(selectedId))
    {
        session.setPendingSpriteObjectDescriptionId(*objectDescriptionId);
    }

    return true;
}

bool editDecorationField(EditorSession &session, uint16_t &decorationListId)
{
    uint32_t selectedId = decorationListId;

    if (!editOptionField(
            session,
            "Decoration",
            selectedId,
            session.decorationOptions(),
            nullptr,
            "Decoration"))
    {
        return false;
    }

    decorationListId = static_cast<uint16_t>(std::min<uint32_t>(selectedId, 65535));
    return true;
}

bool editChestPictureField(EditorSession &session, uint16_t &chestTypeId)
{
    uint32_t selectedId = chestTypeId;

    if (!editOptionField(
            session,
            "Chest Picture",
            selectedId,
            session.chestOptions(),
            nullptr,
            "Chest"))
    {
        return false;
    }

    chestTypeId = static_cast<uint16_t>(std::min<uint32_t>(selectedId, 65535));
    return true;
}

bool editFixedItemSelectorField(EditorSession &session, const char *pLabel, int &itemId)
{
    uint32_t selectedId = itemId > 0 ? static_cast<uint32_t>(itemId) : 0;

    if (!editOptionField(
            session,
            pLabel,
            selectedId,
            session.itemOptions(),
            "<none>",
            "Item"))
    {
        return false;
    }

    itemId = static_cast<int>(selectedId);
    return true;
}

const Game::MapEncounterInfo *spawnEncounterInfo(const Game::MapStatsEntry &mapEntry, int encounterSlot)
{
    if (encounterSlot == 1)
    {
        return &mapEntry.encounter1;
    }

    if (encounterSlot == 2)
    {
        return &mapEntry.encounter2;
    }

    if (encounterSlot == 3)
    {
        return &mapEntry.encounter3;
    }

    return nullptr;
}

std::vector<EditorIdLabelOption> buildActorSpawnIndexOptions(const Game::MapStatsEntry &mapEntry)
{
    std::vector<EditorIdLabelOption> options;
    options.reserve(12);

    for (int encounterSlot = 1; encounterSlot <= 3; ++encounterSlot)
    {
        const Game::MapEncounterInfo *pEncounter = spawnEncounterInfo(mapEntry, encounterSlot);

        if (pEncounter == nullptr)
        {
            continue;
        }

        EditorIdLabelOption option = {};
        option.id = static_cast<uint32_t>(encounterSlot);
        option.label = "Encounter " + std::to_string(encounterSlot) + " Random";

        if (!pEncounter->monsterName.empty())
        {
            option.label += " - " + pEncounter->monsterName;
        }

        option.label += " (#" + std::to_string(option.id) + ")";
        options.push_back(std::move(option));
    }

    for (int encounterSlot = 1; encounterSlot <= 3; ++encounterSlot)
    {
        const Game::MapEncounterInfo *pEncounter = spawnEncounterInfo(mapEntry, encounterSlot);

        if (pEncounter == nullptr)
        {
            continue;
        }

        for (int tierIndex = 0; tierIndex < 3; ++tierIndex)
        {
            EditorIdLabelOption option = {};
            option.id = static_cast<uint32_t>(4 + (tierIndex * 3) + (encounterSlot - 1));
            const char tierSuffix = static_cast<char>('A' + tierIndex);
            option.label = "Encounter " + std::to_string(encounterSlot) + " Tier " + std::string(1, tierSuffix);

            if (!pEncounter->monsterName.empty())
            {
                option.label += " - " + pEncounter->monsterName;
            }

            option.label += " (#" + std::to_string(option.id) + ")";
            options.push_back(std::move(option));
        }
    }

    return options;
}

std::vector<EditorIdLabelOption> buildTreasureLevelOptions()
{
    std::vector<EditorIdLabelOption> options;
    options.reserve(7);

    for (uint32_t level = 1; level <= 7; ++level)
    {
        EditorIdLabelOption option = {};
        option.id = level;
        option.label = std::to_string(level);

        if (level == 7)
        {
            option.label += " (Artefact)";
        }

        options.push_back(std::move(option));
    }

    return options;
}

bool editSpawnTypeField(EditorSession &session, Game::OutdoorSpawn &spawn)
{
    beginInspectorFieldRow("Spawn Type");

    int selectedKind = 2;

    if (spawn.typeId == 3)
    {
        selectedKind = 0;
    }
    else if (spawn.typeId == 2)
    {
        selectedKind = 1;
    }

    static const char *Kinds[] = {"Actor Encounter", "Sprite / Item", "Legacy Raw"};

    if (!ImGui::Combo("##SpawnType", &selectedKind, Kinds, IM_ARRAYSIZE(Kinds)))
    {
        return false;
    }

    session.captureUndoSnapshot();

    if (selectedKind == 0)
    {
        spawn.typeId = 3;

        if (spawn.index == 0)
        {
            spawn.index = 1;
        }
    }
    else if (selectedKind == 1)
    {
        spawn.typeId = 2;

        if (spawn.index < 1 || spawn.index > 7)
        {
            spawn.index = 1;
        }
    }

    return true;
}

bool editTransientSpawnTypeField(Game::OutdoorSpawn &spawn)
{
    beginInspectorFieldRow("Spawn Type");

    int selectedKind = 2;

    if (spawn.typeId == 3)
    {
        selectedKind = 0;
    }
    else if (spawn.typeId == 2)
    {
        selectedKind = 1;
    }

    static const char *Kinds[] = {"Actor Encounter", "Sprite / Item", "Legacy Raw"};

    if (!ImGui::Combo("##SpawnType", &selectedKind, Kinds, IM_ARRAYSIZE(Kinds)))
    {
        return false;
    }

    if (selectedKind == 0)
    {
        spawn.typeId = 3;

        if (spawn.index == 0)
        {
            spawn.index = 1;
        }
    }
    else if (selectedKind == 1)
    {
        spawn.typeId = 2;

        if (spawn.index < 1 || spawn.index > 7)
        {
            spawn.index = 1;
        }
    }

    return true;
}

bool editActorSpawnEncounterField(
    EditorSession &session,
    const Game::MapStatsEntry &mapEntry,
    Game::OutdoorSpawn &spawn)
{
    std::vector<EditorIdLabelOption> options = buildActorSpawnIndexOptions(mapEntry);
    uint32_t selectedId = spawn.index;

    if (!editOptionField(
            session,
            "Encounter",
            selectedId,
            options,
            nullptr,
            "Encounter"))
    {
        return false;
    }

    spawn.typeId = 3;
    spawn.index = static_cast<uint16_t>(std::min<uint32_t>(selectedId, 65535));
    return true;
}

bool editSpawnTreasureLevelField(EditorSession &session, Game::OutdoorSpawn &spawn)
{
    std::vector<EditorIdLabelOption> options = buildTreasureLevelOptions();
    uint32_t selectedId = spawn.index;

    if (!editOptionField(
            session,
            "Treasure Level",
            selectedId,
            options,
            nullptr,
            "Level"))
    {
        return false;
    }

    spawn.typeId = 2;
    spawn.index = static_cast<uint16_t>(std::min<uint32_t>(selectedId, 65535));
    return true;
}

bool editTransientSpawnTreasureLevelField(Game::OutdoorSpawn &spawn)
{
    std::vector<EditorIdLabelOption> options = buildTreasureLevelOptions();
    uint32_t selectedId = spawn.index;

    if (!editTransientOptionField(
            "Treasure Level",
            selectedId,
            options,
            nullptr,
            "Level"))
    {
        return false;
    }

    spawn.typeId = 2;
    spawn.index = static_cast<uint16_t>(std::min<uint32_t>(selectedId, 65535));
    return true;
}

bool editTransientActorSpawnEncounterField(
    const Game::MapStatsEntry &mapEntry,
    Game::OutdoorSpawn &spawn)
{
    std::vector<EditorIdLabelOption> options = buildActorSpawnIndexOptions(mapEntry);
    uint32_t selectedId = spawn.index;

    if (!editTransientOptionField(
            "Encounter",
            selectedId,
            options,
            nullptr,
            "Encounter"))
    {
        return false;
    }

    spawn.typeId = 3;
    spawn.index = static_cast<uint16_t>(std::min<uint32_t>(selectedId, 65535));
    return true;
}

bool editUInt16Array4Field(EditorSession &session, const char *pLabel, std::array<uint16_t, 4> &values)
{
    std::array<int, 4> editedValues = {
        static_cast<int>(values[0]),
        static_cast<int>(values[1]),
        static_cast<int>(values[2]),
        static_cast<int>(values[3])
    };

    beginInspectorFieldRow(pLabel);

    if (!ImGui::InputInt4(inspectorFieldId(pLabel).c_str(), editedValues.data()))
    {
        return false;
    }

    bool changed = false;

    for (size_t index = 0; index < values.size(); ++index)
    {
        const uint16_t clampedValue = static_cast<uint16_t>(std::clamp(editedValues[index], 0, 65535));

        if (clampedValue != values[index])
        {
            values[index] = clampedValue;
            changed = true;
        }
    }

    if (changed)
    {
        session.captureUndoSnapshot();
    }

    return changed;
}

bool isObjectLifecycleKind(EditorSelectionKind kind)
{
    return kind == EditorSelectionKind::BModel
        || kind == EditorSelectionKind::Entity
        || kind == EditorSelectionKind::Spawn
        || kind == EditorSelectionKind::Actor
        || kind == EditorSelectionKind::SpriteObject;
}

size_t terrainCellFlatIndex(int x, int y)
{
    return static_cast<size_t>(y) * Game::OutdoorMapData::TerrainWidth + static_cast<size_t>(x);
}

bool decodeTerrainCellFlatIndex(size_t flatIndex, int &x, int &y)
{
    if (flatIndex >= static_cast<size_t>(Game::OutdoorMapData::TerrainWidth * Game::OutdoorMapData::TerrainHeight))
    {
        return false;
    }

    x = static_cast<int>(flatIndex % Game::OutdoorMapData::TerrainWidth);
    y = static_cast<int>(flatIndex / Game::OutdoorMapData::TerrainWidth);
    return true;
}

bool tryPickFlattenTargetFromSelectedTerrainCell(EditorSession &session)
{
    if (!session.hasDocument() || session.document().kind() != EditorDocument::Kind::Outdoor)
    {
        return false;
    }

    if (session.selection().kind != EditorSelectionKind::Terrain)
    {
        return false;
    }

    int cellX = 0;
    int cellY = 0;

    if (!decodeTerrainCellFlatIndex(session.selection().index, cellX, cellY))
    {
        return false;
    }

    const size_t sampleIndex = terrainCellFlatIndex(cellX, cellY);
    const Game::OutdoorMapData &outdoorGeometry = session.document().outdoorGeometry();

    if (sampleIndex >= outdoorGeometry.heightMap.size())
    {
        return false;
    }

    session.setTerrainFlattenTargetMode(EditorTerrainFlattenTargetMode::Sampled);
    session.setTerrainFlattenSampledTargetHeight(outdoorGeometry.heightMap[sampleIndex]);
    return true;
}

size_t flattenedOutdoorFaceIndex(const Game::OutdoorMapData &outdoorMapData, size_t bmodelIndex, size_t faceIndex)
{
    size_t flattenedIndex = 0;

    for (size_t index = 0; index < bmodelIndex && index < outdoorMapData.bmodels.size(); ++index)
    {
        flattenedIndex += outdoorMapData.bmodels[index].faces.size();
    }

    return flattenedIndex + faceIndex;
}

bool decodeFlattenedOutdoorFaceIndex(
    const Game::OutdoorMapData &outdoorMapData,
    size_t flattenedIndex,
    size_t &bmodelIndex,
    size_t &faceIndex)
{
    size_t runningIndex = 0;

    for (size_t currentBModelIndex = 0; currentBModelIndex < outdoorMapData.bmodels.size(); ++currentBModelIndex)
    {
        const size_t faceCount = outdoorMapData.bmodels[currentBModelIndex].faces.size();

        if (flattenedIndex < runningIndex + faceCount)
        {
            bmodelIndex = currentBModelIndex;
            faceIndex = flattenedIndex - runningIndex;
            return true;
        }

        runningIndex += faceCount;
    }

    return false;
}

Game::OutdoorSceneTerrainAttributeOverride *findTerrainOverride(
    Game::OutdoorSceneData &sceneData,
    int x,
    int y)
{
    for (Game::OutdoorSceneTerrainAttributeOverride &overrideEntry : sceneData.terrainAttributeOverrides)
    {
        if (overrideEntry.x == x && overrideEntry.y == y)
        {
            return &overrideEntry;
        }
    }

    return nullptr;
}

const Game::OutdoorSceneTerrainAttributeOverride *findTerrainOverride(
    const Game::OutdoorSceneData &sceneData,
    int x,
    int y)
{
    for (const Game::OutdoorSceneTerrainAttributeOverride &overrideEntry : sceneData.terrainAttributeOverrides)
    {
        if (overrideEntry.x == x && overrideEntry.y == y)
        {
            return &overrideEntry;
        }
    }

    return nullptr;
}

Game::OutdoorSceneInteractiveFace *findInteractiveFace(
    Game::OutdoorSceneData &sceneData,
    size_t bmodelIndex,
    size_t faceIndex)
{
    for (Game::OutdoorSceneInteractiveFace &interactiveFace : sceneData.interactiveFaces)
    {
        if (interactiveFace.bmodelIndex == bmodelIndex && interactiveFace.faceIndex == faceIndex)
        {
            return &interactiveFace;
        }
    }

    return nullptr;
}

const Game::OutdoorSceneInteractiveFace *findInteractiveFace(
    const Game::OutdoorSceneData &sceneData,
    size_t bmodelIndex,
    size_t faceIndex)
{
    for (const Game::OutdoorSceneInteractiveFace &interactiveFace : sceneData.interactiveFaces)
    {
        if (interactiveFace.bmodelIndex == bmodelIndex && interactiveFace.faceIndex == faceIndex)
        {
            return &interactiveFace;
        }
    }

    return nullptr;
}

const Game::OutdoorSceneBModelFaceSource *findBModelFaceSource(
    const Game::OutdoorSceneData &sceneData,
    size_t bmodelIndex,
    size_t faceIndex)
{
    for (const Game::OutdoorSceneBModelFaceSource &faceSource : sceneData.bmodelFaceSources)
    {
        if (faceSource.bmodelIndex == bmodelIndex && faceSource.faceIndex == faceIndex)
        {
            return &faceSource;
        }
    }

    return nullptr;
}

Game::OutdoorSceneInteractiveFace makeInteractiveFaceEntry(
    size_t bmodelIndex,
    size_t faceIndex,
    const Game::OutdoorBModelFace &face)
{
    Game::OutdoorSceneInteractiveFace interactiveFace = {};
    interactiveFace.bmodelIndex = bmodelIndex;
    interactiveFace.faceIndex = faceIndex;
    interactiveFace.legacyAttributes = face.attributes;
    interactiveFace.cogNumber = face.cogNumber;
    interactiveFace.cogTriggeredNumber = face.cogTriggeredNumber;
    interactiveFace.cogTrigger = face.cogTrigger;
    return interactiveFace;
}

}

void EditorMainWindow::render(
    EditorSession &session,
    uint32_t frameNumber,
    float deltaSeconds,
    const std::string &rendererName)
{
    ensureEditorStateLoaded(session);
    const ImGuiID dockspaceId = editorDockspaceId();
    ImGui::DockSpaceOverViewport(
        dockspaceId,
        ImGui::GetMainViewport(),
        ImGuiDockNodeFlags_PassthruCentralNode);
    ensureDefaultDockLayout();
    handleGlobalShortcuts(session);
    syncImportedModelPreview(session);

    renderMenuBar(session);
    ImGui::SetNextWindowDockID(dockspaceId, ImGuiCond_FirstUseEver);
    renderViewportPanel(session, deltaSeconds);
    renderToolbar(session);
    renderSceneOutliner(session);
    renderInspector(session);
    renderLogPanel(session, frameNumber, deltaSeconds, rendererName);
    renderNewOutdoorMapModal(session);
    renderOpenOutdoorMapModal(session);
    renderMapPackageActionModal(session);
    renderDeleteCurrentMapModal(session);
    renderModelImportModal(session);
    renderModelFileBrowserPopup(session);
    persistEditorStateIfNeeded(session);
}

bool EditorMainWindow::restoreLastLoadedMap(EditorSession &session, std::string &errorMessage)
{
    ensureEditorStateLoaded(session);

    if (m_lastLoadedMapPath.empty())
    {
        return false;
    }

    std::error_code fileError;

    if (!std::filesystem::exists(m_lastLoadedMapPath, fileError))
    {
        errorMessage = "last loaded map no longer exists: " + m_lastLoadedMapPath.string();
        return false;
    }

    if (!session.openMapPhysicalPath(m_lastLoadedMapPath, errorMessage))
    {
        return false;
    }

    const std::filesystem::path parentPath = m_lastLoadedMapPath.parent_path();

    if (!parentPath.empty())
    {
        m_openMapBrowserDirectory = parentPath;
    }

    return true;
}

void EditorMainWindow::syncImportedModelPreview(EditorSession &session)
{
    const bool importModalVisible =
        m_openImportNewBModelModal || m_showImportNewBModelWindow;

    if (importModalVisible)
    {
        const std::string sourcePath = trimCopy(m_globalBModelImportPath);

        if (!sourcePath.empty())
        {
            EditorOutdoorViewport::ImportedModelPreviewRequest request = {};
            request.sourcePath = sourcePath;
            request.sourceMeshName = canSplitImportedModelPathByMesh(sourcePath) ? m_globalBModelImportSelectedMeshName : "";
            request.importScale = m_globalBModelImportScale;
            request.mergeCoplanarFaces = m_globalBModelImportMergeCoplanarFaces;
            request.targetMode = EditorOutdoorViewport::ImportedModelPreviewRequest::TargetMode::NewImportPlacement;
            m_viewport.setImportedModelPreviewRequest(request);
            return;
        }
    }

    if (session.selection().kind == EditorSelectionKind::BModel)
    {
        const std::string sourcePath = trimCopy(m_bmodelImportPath);

        if (!sourcePath.empty())
        {
            EditorOutdoorViewport::ImportedModelPreviewRequest request = {};
            request.sourcePath = sourcePath;
            request.sourceMeshName = canSplitImportedModelPathByMesh(sourcePath) ? m_bmodelImportSelectedMeshName : "";
            request.importScale = m_bmodelImportScale;
            request.mergeCoplanarFaces = m_bmodelImportMergeCoplanarFaces;
            request.targetMode = EditorOutdoorViewport::ImportedModelPreviewRequest::TargetMode::ReplaceSelectedBModel;
            request.bmodelIndex = session.selection().index;
            m_viewport.setImportedModelPreviewRequest(request);
            return;
        }
    }

    m_viewport.setImportedModelPreviewRequest(std::nullopt);
}

void EditorMainWindow::handleGlobalShortcuts(EditorSession &session)
{
    const ImGuiIO &io = ImGui::GetIO();

    if (io.KeyCtrl && ImGui::IsKeyPressed(ImGuiKey_N, false))
    {
        openNewOutdoorMapModal(session);
    }

    if (io.KeyCtrl && ImGui::IsKeyPressed(ImGuiKey_O, false))
    {
        openOpenOutdoorMapModal();
    }

    if (!session.hasDocument())
    {
        return;
    }

    if (io.KeyCtrl && !io.WantTextInput)
    {
        if (io.KeyShift && ImGui::IsKeyPressed(ImGuiKey_Z, false))
        {
            std::string errorMessage;

            if (session.canRedo() && !session.redo(errorMessage))
            {
                session.logError(errorMessage);
            }
        }
        else if (!io.KeyShift && ImGui::IsKeyPressed(ImGuiKey_Z, false))
        {
            std::string errorMessage;

            if (session.canUndo() && !session.undo(errorMessage))
            {
                session.logError(errorMessage);
            }
        }
        else if (ImGui::IsKeyPressed(ImGuiKey_Y, false))
        {
            std::string errorMessage;

            if (session.canRedo() && !session.redo(errorMessage))
            {
                session.logError(errorMessage);
            }
        }
    }

    if (io.KeyCtrl && ImGui::IsKeyPressed(ImGuiKey_S, false))
    {
        std::string errorMessage;

        if (session.saveActiveDocument(errorMessage))
        {
            setStatusMessage(StatusMessageKind::Success, "Saved source.");
        }
        else
        {
            session.logError(errorMessage);
            setStatusMessage(StatusMessageKind::Error, errorMessage);
        }
    }

    if (io.KeyCtrl && ImGui::IsKeyPressed(ImGuiKey_B, false))
    {
        std::string errorMessage;

        if (session.buildActiveDocument(errorMessage))
        {
            setStatusMessage(StatusMessageKind::Success, "Built runtime ODM.");
        }
        else
        {
            session.logError(errorMessage);
            setStatusMessage(StatusMessageKind::Error, errorMessage);
        }
    }

    if (ImGui::IsKeyPressed(ImGuiKey_F5, false))
    {
        std::string errorMessage;

        if (playtestCurrentMap(session, errorMessage))
        {
            setStatusMessage(StatusMessageKind::Success, "Launched playtest.");
        }
        else
        {
            session.logError(errorMessage);
            setStatusMessage(StatusMessageKind::Error, errorMessage);
        }
    }
}

void EditorMainWindow::shutdown()
{
    if (m_shutdownComplete)
    {
        return;
    }

    m_shutdownComplete = true;
    destroyBitmapPreviewTextures();
    m_viewport.shutdown();
}

void EditorMainWindow::ensureEditorStateLoaded(EditorSession &session)
{
    if (m_editorStateLoaded)
    {
        return;
    }

    m_editorStateLoaded = true;
    std::ifstream input(editorStatePath());

    if (!input)
    {
        return;
    }

    std::unordered_map<std::string, std::string> values;
    std::string line;

    while (std::getline(input, line))
    {
        const size_t separator = line.find('=');

        if (separator == std::string::npos)
        {
            continue;
        }

        values[trimCopy(line.substr(0, separator))] = trimCopy(line.substr(separator + 1));
    }

    if (const auto iterator = values.find("placement_kind"); iterator != values.end())
    {
        const int rawKind = std::clamp(std::atoi(iterator->second.c_str()), 0, static_cast<int>(EditorSelectionKind::Chest));
        m_viewport.setPlacementKind(static_cast<EditorSelectionKind>(rawKind));
    }

    if (const auto iterator = values.find("transform_mode"); iterator != values.end())
    {
        const int rawMode = std::clamp(std::atoi(iterator->second.c_str()), 0, 1);
        m_viewport.setTransformGizmoMode(static_cast<EditorOutdoorViewport::TransformGizmoMode>(rawMode));
    }

    if (const auto iterator = values.find("transform_space"); iterator != values.end())
    {
        const int rawMode = std::clamp(std::atoi(iterator->second.c_str()), 0, 1);
        m_viewport.setTransformSpaceMode(static_cast<EditorOutdoorViewport::TransformSpaceMode>(rawMode));
    }

    if (const auto iterator = values.find("snap_enabled"); iterator != values.end())
    {
        m_viewport.setSnapEnabled(parseBoolValue(iterator->second));
    }

    if (const auto iterator = values.find("snap_step"); iterator != values.end())
    {
        m_viewport.setSnapStep(std::atoi(iterator->second.c_str()));
    }

    if (const auto iterator = values.find("show_terrain"); iterator != values.end())
    {
        m_viewport.setShowTerrainFill(parseBoolValue(iterator->second));
    }

    if (const auto iterator = values.find("show_terrain_grid"); iterator != values.end())
    {
        m_viewport.setShowTerrainGrid(parseBoolValue(iterator->second));
    }

    if (const auto iterator = values.find("preview_material_mode"); iterator != values.end())
    {
        const int rawMode = std::clamp(std::atoi(iterator->second.c_str()), 0, 2);
        m_viewport.setPreviewMaterialMode(static_cast<EditorOutdoorViewport::PreviewMaterialMode>(rawMode));
    }

    if (const auto iterator = values.find("preview_selected_only"); iterator != values.end())
    {
        m_viewport.setForcePreviewOnSelectedOnly(parseBoolValue(iterator->second));
    }

    if (const auto iterator = values.find("show_bmodels"); iterator != values.end())
    {
        m_viewport.setShowBModels(parseBoolValue(iterator->second));
    }

    if (const auto iterator = values.find("show_mm9_dat_portals"); iterator != values.end())
    {
        m_viewport.setShowMm9DatPortals(parseBoolValue(iterator->second));
    }

    if (const auto iterator = values.find("show_mm9_world_model_bounds"); iterator != values.end())
    {
        m_viewport.setShowMm9WorldModelBounds(parseBoolValue(iterator->second));
    }

    if (const auto iterator = values.find("show_mm9_object_bounds"); iterator != values.end())
    {
        m_viewport.setShowMm9ObjectBounds(parseBoolValue(iterator->second));
    }

    if (const auto iterator = values.find("show_mm9_asset_issue_markers"); iterator != values.end())
    {
        m_viewport.setShowMm9AssetIssueMarkers(parseBoolValue(iterator->second));
    }

    if (const auto iterator = values.find("show_indoor_portals"); iterator != values.end())
    {
        m_viewport.setShowIndoorPortals(parseBoolValue(iterator->second));
    }

    if (const auto iterator = values.find("show_indoor_floors"); iterator != values.end())
    {
        m_viewport.setShowIndoorFloors(parseBoolValue(iterator->second));
    }

    if (const auto iterator = values.find("show_indoor_ceilings"); iterator != values.end())
    {
        m_viewport.setShowIndoorCeilings(parseBoolValue(iterator->second));
    }

    if (const auto iterator = values.find("show_indoor_gizmos_everywhere"); iterator != values.end())
    {
        m_viewport.setShowIndoorGizmosEverywhere(parseBoolValue(iterator->second));
    }

    if (const auto iterator = values.find("isolated_indoor_room"); iterator != values.end())
    {
        const int roomId = std::atoi(iterator->second.c_str());
        m_viewport.setIsolatedIndoorRoomId(roomId >= 0 ? std::optional<uint16_t>(static_cast<uint16_t>(roomId)) : std::nullopt);
    }

    if (const auto iterator = values.find("show_bmodel_wire"); iterator != values.end())
    {
        m_viewport.setShowBModelWireframe(parseBoolValue(iterator->second));
    }

    if (const auto iterator = values.find("show_entities"); iterator != values.end())
    {
        m_viewport.setShowEntities(parseBoolValue(iterator->second));
    }

    if (const auto iterator = values.find("show_entity_billboards"); iterator != values.end())
    {
        m_viewport.setShowEntityBillboards(parseBoolValue(iterator->second));
    }

    if (const auto iterator = values.find("show_spawns"); iterator != values.end())
    {
        m_viewport.setShowSpawns(parseBoolValue(iterator->second));
    }

    if (const auto iterator = values.find("show_actors"); iterator != values.end())
    {
        m_viewport.setShowActors(parseBoolValue(iterator->second));
    }

    if (const auto iterator = values.find("show_actor_billboards"); iterator != values.end())
    {
        m_viewport.setShowActorBillboards(parseBoolValue(iterator->second));
    }

    if (const auto iterator = values.find("show_objects"); iterator != values.end())
    {
        m_viewport.setShowSpriteObjects(parseBoolValue(iterator->second));
    }

    if (const auto iterator = values.find("show_spawn_actor_billboards"); iterator != values.end())
    {
        m_viewport.setShowSpawnActorBillboards(parseBoolValue(iterator->second));
    }

    if (const auto iterator = values.find("show_events"); iterator != values.end())
    {
        m_viewport.setShowEventMarkers(parseBoolValue(iterator->second));
    }

    if (const auto iterator = values.find("show_chest_links"); iterator != values.end())
    {
        m_viewport.setShowChestLinks(parseBoolValue(iterator->second));
    }

    if (const auto iterator = values.find("terrain_paint_enabled"); iterator != values.end())
    {
        session.setTerrainPaintEnabled(parseBoolValue(iterator->second));
    }

    if (const auto iterator = values.find("terrain_paint_tile"); iterator != values.end())
    {
        session.setTerrainPaintTileId(static_cast<uint8_t>(std::clamp(std::atoi(iterator->second.c_str()), 0, 255)));
    }

    if (const auto iterator = values.find("terrain_paint_mode"); iterator != values.end())
    {
        const int rawMode = std::clamp(std::atoi(iterator->second.c_str()), 0, 2);
        session.setTerrainPaintMode(static_cast<EditorTerrainPaintMode>(rawMode));
    }

    if (const auto iterator = values.find("terrain_paint_radius"); iterator != values.end())
    {
        session.setTerrainPaintRadius(std::atoi(iterator->second.c_str()));
    }

    if (const auto iterator = values.find("terrain_paint_edge_noise"); iterator != values.end())
    {
        session.setTerrainPaintEdgeNoise(std::atoi(iterator->second.c_str()));
    }

    if (const auto iterator = values.find("terrain_sculpt_enabled"); iterator != values.end())
    {
        session.setTerrainSculptEnabled(parseBoolValue(iterator->second));
    }

    if (const auto iterator = values.find("terrain_sculpt_mode"); iterator != values.end())
    {
        const int rawMode = std::clamp(std::atoi(iterator->second.c_str()), 0, 5);
        session.setTerrainSculptMode(static_cast<EditorTerrainSculptMode>(rawMode));
    }
    else if (const auto iterator = values.find("terrain_sculpt_lower"); iterator != values.end())
    {
        session.setTerrainSculptMode(
            parseBoolValue(iterator->second) ? EditorTerrainSculptMode::Lower : EditorTerrainSculptMode::Raise);
    }

    if (const auto iterator = values.find("terrain_sculpt_radius"); iterator != values.end())
    {
        session.setTerrainSculptRadius(std::atoi(iterator->second.c_str()));
    }

    if (const auto iterator = values.find("terrain_sculpt_strength"); iterator != values.end())
    {
        session.setTerrainSculptStrength(std::atoi(iterator->second.c_str()));
    }

    if (const auto iterator = values.find("terrain_sculpt_falloff"); iterator != values.end())
    {
        const int rawMode = std::clamp(std::atoi(iterator->second.c_str()), 0, 2);
        session.setTerrainSculptFalloffMode(static_cast<EditorTerrainFalloffMode>(rawMode));
    }

    if (const auto iterator = values.find("terrain_flatten_target_mode"); iterator != values.end())
    {
        const int rawMode = std::clamp(std::atoi(iterator->second.c_str()), 0, 1);
        session.setTerrainFlattenTargetMode(static_cast<EditorTerrainFlattenTargetMode>(rawMode));
    }

    if (const auto iterator = values.find("terrain_flatten_target_height"); iterator != values.end())
    {
        session.setTerrainFlattenTargetHeight(std::atoi(iterator->second.c_str()));
    }

    if (const auto iterator = values.find("terrain_flatten_sampled_valid"); iterator != values.end()
        && parseBoolValue(iterator->second))
    {
        session.setTerrainFlattenSampledTargetHeight(session.terrainFlattenTargetHeight());
    }

    if (const auto iterator = values.find("import_directory"); iterator != values.end())
    {
        m_modelBrowserDirectory = iterator->second;
    }

    if (const auto iterator = values.find("open_map_directory"); iterator != values.end())
    {
        m_openMapBrowserDirectory = iterator->second;
    }

    if (const auto iterator = values.find("last_map_path"); iterator != values.end())
    {
        m_lastLoadedMapPath = iterator->second;

        if (m_openMapBrowserDirectory.empty())
        {
            m_openMapBrowserDirectory = m_lastLoadedMapPath.parent_path();
        }
    }
}

void EditorMainWindow::persistEditorStateIfNeeded(const EditorSession &session)
{
    if (session.hasDocument() && !session.document().scenePhysicalPath().empty())
    {
        m_lastLoadedMapPath = session.document().scenePhysicalPath();
    }

    std::ostringstream output;
    output << "placement_kind=" << static_cast<int>(m_viewport.placementKind()) << '\n';
    output << "transform_mode=" << static_cast<int>(m_viewport.transformGizmoMode()) << '\n';
    output << "transform_space=" << static_cast<int>(m_viewport.transformSpaceMode()) << '\n';
    output << "snap_enabled=" << (m_viewport.snapEnabled() ? 1 : 0) << '\n';
    output << "snap_step=" << m_viewport.snapStep() << '\n';
    output << "show_terrain=" << (m_viewport.showTerrainFill() ? 1 : 0) << '\n';
    output << "show_terrain_grid=" << (m_viewport.showTerrainGrid() ? 1 : 0) << '\n';
    output << "preview_material_mode=" << static_cast<int>(m_viewport.previewMaterialMode()) << '\n';
    output << "preview_selected_only=" << (m_viewport.forcePreviewOnSelectedOnly() ? 1 : 0) << '\n';
    output << "show_bmodels=" << (m_viewport.showBModels() ? 1 : 0) << '\n';
    output << "show_mm9_dat_portals=" << (m_viewport.showMm9DatPortals() ? 1 : 0) << '\n';
    output << "show_mm9_world_model_bounds=" << (m_viewport.showMm9WorldModelBounds() ? 1 : 0) << '\n';
    output << "show_mm9_object_bounds=" << (m_viewport.showMm9ObjectBounds() ? 1 : 0) << '\n';
    output << "show_mm9_asset_issue_markers=" << (m_viewport.showMm9AssetIssueMarkers() ? 1 : 0) << '\n';
    output << "show_indoor_portals=" << (m_viewport.showIndoorPortals() ? 1 : 0) << '\n';
    output << "show_indoor_floors=" << (m_viewport.showIndoorFloors() ? 1 : 0) << '\n';
    output << "show_indoor_ceilings=" << (m_viewport.showIndoorCeilings() ? 1 : 0) << '\n';
    output << "show_indoor_gizmos_everywhere=" << (m_viewport.showIndoorGizmosEverywhere() ? 1 : 0) << '\n';
    output << "isolated_indoor_room="
           << (m_viewport.isolatedIndoorRoomId().has_value()
                   ? std::to_string(*m_viewport.isolatedIndoorRoomId())
                   : std::string("-1"))
           << '\n';
    output << "show_bmodel_wire=" << (m_viewport.showBModelWireframe() ? 1 : 0) << '\n';
    output << "show_entities=" << (m_viewport.showEntities() ? 1 : 0) << '\n';
    output << "show_entity_billboards=" << (m_viewport.showEntityBillboards() ? 1 : 0) << '\n';
    output << "show_spawns=" << (m_viewport.showSpawns() ? 1 : 0) << '\n';
    output << "show_actors=" << (m_viewport.showActors() ? 1 : 0) << '\n';
    output << "show_actor_billboards=" << (m_viewport.showActorBillboards() ? 1 : 0) << '\n';
    output << "show_objects=" << (m_viewport.showSpriteObjects() ? 1 : 0) << '\n';
    output << "show_spawn_actor_billboards=" << (m_viewport.showSpawnActorBillboards() ? 1 : 0) << '\n';
    output << "show_events=" << (m_viewport.showEventMarkers() ? 1 : 0) << '\n';
    output << "show_chest_links=" << (m_viewport.showChestLinks() ? 1 : 0) << '\n';
    output << "terrain_paint_enabled=" << (session.terrainPaintEnabled() ? 1 : 0) << '\n';
    output << "terrain_paint_tile=" << static_cast<int>(session.terrainPaintTileId()) << '\n';
    output << "terrain_paint_mode=" << static_cast<int>(session.terrainPaintMode()) << '\n';
    output << "terrain_paint_radius=" << session.terrainPaintRadius() << '\n';
    output << "terrain_paint_edge_noise=" << session.terrainPaintEdgeNoise() << '\n';
    output << "terrain_sculpt_enabled=" << (session.terrainSculptEnabled() ? 1 : 0) << '\n';
    output << "terrain_sculpt_mode=" << static_cast<int>(session.terrainSculptMode()) << '\n';
    output << "terrain_sculpt_radius=" << session.terrainSculptRadius() << '\n';
    output << "terrain_sculpt_strength=" << session.terrainSculptStrength() << '\n';
    output << "terrain_sculpt_falloff=" << static_cast<int>(session.terrainSculptFalloffMode()) << '\n';
    output << "terrain_flatten_target_mode=" << static_cast<int>(session.terrainFlattenTargetMode()) << '\n';
    output << "terrain_flatten_target_height=" << session.terrainFlattenTargetHeight() << '\n';
    output << "terrain_flatten_sampled_valid=" << (session.hasTerrainFlattenSampledTarget() ? 1 : 0) << '\n';
    output << "import_directory=" << m_modelBrowserDirectory.generic_string() << '\n';
    output << "open_map_directory=" << m_openMapBrowserDirectory.generic_string() << '\n';
    output << "last_map_path=" << m_lastLoadedMapPath.generic_string() << '\n';
    const std::string serialized = output.str();

    if (serialized == m_lastSavedEditorState)
    {
        return;
    }

    std::ofstream file(editorStatePath(), std::ios::binary | std::ios::trunc);

    if (!file)
    {
        return;
    }

    file << serialized;
    m_lastSavedEditorState = serialized;
}

int EditorMainWindow::viewportX() const
{
    return m_viewportX;
}

int EditorMainWindow::viewportY() const
{
    return m_viewportY;
}

uint16_t EditorMainWindow::viewportWidth() const
{
    return m_viewportWidth;
}

uint16_t EditorMainWindow::viewportHeight() const
{
    return m_viewportHeight;
}

const EditorOutdoorViewport::RenderSubmissionStats &EditorMainWindow::lastViewportRenderSubmissionStats() const
{
    return m_viewport.lastRenderSubmissionStats();
}

void renderReadOnlyTextPreviewSection(
    const char *pLabel,
    const char *pId,
    const ReadOnlyTextPreview &preview,
    bool defaultOpen = false)
{
    if (!beginInspectorSectionBlock(pLabel, defaultOpen))
    {
        return;
    }

    if (beginInspectorPropertyTable(pId))
    {
        renderInspectorReadOnlyField("Path", preview.path.empty() ? std::string("<none>") : preview.path.generic_string());
        renderInspectorReadOnlyField("Exists", boolText(preview.exists));
        renderInspectorReadOnlyField("Loaded", boolText(preview.loaded));
        renderInspectorReadOnlyField("Read Only", "true");
        renderInspectorReadOnlyField("Bytes", std::to_string(preview.fileSizeBytes));
        renderInspectorReadOnlyField("Preview Truncated", boolText(preview.truncated));
        ImGui::EndTable();
    }

    if (!preview.loaded)
    {
        ImGui::TextDisabled("File is not available for preview.");
        endInspectorSectionBlock();
        return;
    }

    const std::string childId = std::string(pId) + "Text";
    if (ImGui::BeginChild(childId.c_str(), ImVec2(0.0f, 260.0f), ImGuiChildFlags_Borders))
    {
        ImGui::TextUnformatted(preview.text.c_str(), preview.text.c_str() + preview.text.size());
    }
    ImGui::EndChild();

    endInspectorSectionBlock();
}

void EditorMainWindow::ensureDefaultDockLayout()
{
    if (m_dockLayoutInitialized)
    {
        return;
    }

    const ImGuiViewport *pViewport = ImGui::GetMainViewport();
    const ImGuiID dockspaceId = editorDockspaceId();
    ImGui::DockBuilderRemoveNode(dockspaceId);
    ImGui::DockBuilderAddNode(dockspaceId, ImGuiDockNodeFlags_DockSpace);
    ImGui::DockBuilderSetNodeSize(dockspaceId, pViewport->WorkSize);

    ImGuiID leftNode = 0;
    ImGuiID rightNode = 0;
    ImGuiID bottomNode = 0;
    ImGuiID topNode = 0;
    ImGuiID centerNode = dockspaceId;

    ImGui::DockBuilderSplitNode(centerNode, ImGuiDir_Up, 0.10f, &topNode, &centerNode);
    ImGui::DockBuilderSplitNode(centerNode, ImGuiDir_Left, 0.18f, &leftNode, &centerNode);
    ImGui::DockBuilderSplitNode(centerNode, ImGuiDir_Right, 0.24f, &rightNode, &centerNode);
    ImGui::DockBuilderSplitNode(centerNode, ImGuiDir_Down, 0.23f, &bottomNode, &centerNode);

    ImGui::DockBuilderDockWindow("Tools", topNode);
    ImGui::DockBuilderDockWindow("Scene", leftNode);
    ImGui::DockBuilderDockWindow("Inspector", rightNode);
    ImGui::DockBuilderDockWindow("Viewport", centerNode);
    ImGui::DockBuilderDockWindow("Log", bottomNode);
    ImGui::DockBuilderFinish(dockspaceId);
    m_dockLayoutInitialized = true;
}

void EditorMainWindow::renderMenuBar(EditorSession &session)
{
    if (!ImGui::BeginMainMenuBar())
    {
        return;
    }

    if (ImGui::BeginMenu("File"))
    {
        if (ImGui::MenuItem("New Outdoor Map...", "Ctrl+N"))
        {
            openNewOutdoorMapModal(session);
        }
        if (ImGui::MenuItem("Open...", "Ctrl+O"))
        {
            openOpenOutdoorMapModal();
        }
        if (ImGui::MenuItem("Save Current Map As...", nullptr, false, session.hasDocument()))
        {
            openMapPackageActionModal(session, MapPackageAction::SaveAs);
        }
        if (ImGui::MenuItem("Duplicate Current Map...", nullptr, false, session.hasDocument()))
        {
            openMapPackageActionModal(session, MapPackageAction::Duplicate);
        }
        if (ImGui::MenuItem("Save Source", "Ctrl+S", false, session.hasDocument()))
        {
            std::string errorMessage;

            if (session.saveActiveDocument(errorMessage))
            {
                setStatusMessage(StatusMessageKind::Success, "Saved source.");
            }
            else
            {
                session.logError(errorMessage);
                setStatusMessage(StatusMessageKind::Error, errorMessage);
            }
        }
        if (ImGui::MenuItem("Delete Current Map...", nullptr, false, session.hasDocument()))
        {
            openDeleteCurrentMapModal();
        }
        ImGui::MenuItem("Save All", "Ctrl+Shift+S", false, false);
        ImGui::Separator();
        ImGui::MenuItem("Quit", "Ctrl+Q", false, false);
        ImGui::EndMenu();
    }

    if (ImGui::BeginMenu("Build"))
    {
        if (ImGui::MenuItem("Build Current Map", "Ctrl+B", false, session.hasDocument()))
        {
            std::string errorMessage;

            if (session.buildActiveDocument(errorMessage))
            {
                setStatusMessage(StatusMessageKind::Success, "Built runtime ODM.");
            }
            else
            {
                session.logError(errorMessage);
                setStatusMessage(StatusMessageKind::Error, errorMessage);
            }
        }

        ImGui::Separator();
        ImGui::MenuItem("Validate Scene", nullptr, false, false);
        if (ImGui::MenuItem("Playtest Current Map", "F5", false, session.hasDocument()))
        {
            std::string errorMessage;

            if (playtestCurrentMap(session, errorMessage))
            {
                setStatusMessage(StatusMessageKind::Success, "Launched playtest.");
            }
            else
            {
                session.logError(errorMessage);
                setStatusMessage(StatusMessageKind::Error, errorMessage);
            }
        }
        ImGui::EndMenu();
    }

    if (ImGui::BeginMenu("Edit"))
    {
        if (ImGui::MenuItem("Undo", "Ctrl+Z", false, session.canUndo()))
        {
            std::string errorMessage;

            if (!session.undo(errorMessage))
            {
                session.logError(errorMessage);
            }
        }

        if (ImGui::MenuItem("Redo", "Ctrl+Shift+Z", false, session.canRedo()))
        {
            std::string errorMessage;

            if (!session.redo(errorMessage))
            {
                session.logError(errorMessage);
            }
        }

        ImGui::EndMenu();
    }

    if (ImGui::BeginMenu("View"))
    {
        ImGui::MenuItem("Scene", nullptr, true, false);
        ImGui::MenuItem("Inspector", nullptr, true, false);
        ImGui::MenuItem("Log", nullptr, true, false);
        ImGui::EndMenu();
    }

    ImGui::EndMainMenuBar();
}

void EditorMainWindow::renderToolbar(EditorSession &session)
{
    ImGui::SetNextWindowDockID(editorDockspaceId(), ImGuiCond_FirstUseEver);
    const bool isIndoorDocument =
        session.hasDocument() && session.document().kind() == EditorDocument::Kind::Indoor;
    const bool isMm9DatDocument =
        session.hasDocument() && session.document().kind() == EditorDocument::Kind::Mm9Dat;

    const ImGuiWindowFlags windowFlags = ImGuiWindowFlags_NoCollapse | ImGuiWindowFlags_NoScrollbar |
        ImGuiWindowFlags_NoScrollWithMouse;

    if (!ImGui::Begin("Tools", nullptr, windowFlags))
    {
        ImGui::End();
        return;
    }

    ImGui::PushStyleVar(ImGuiStyleVar_FramePadding, ImVec2(6.0f, 1.0f));
    ImGui::PushStyleVar(ImGuiStyleVar_ItemSpacing, ImVec2(4.0f, 2.0f));
    const ImGuiStyle &style = ImGui::GetStyle();
    const float iconSize = 14.0f;
    const float iconTextSpacing = 6.0f;
    const float iconPillPadding = style.FramePadding.x + 2.0f;
    const float cardInnerPadding = 12.0f;
    const float columnSpacing = 10.0f;
    const auto iconPillWidth = [&](const char *pLabel)
    {
        return iconPillPadding * 2.0f + iconSize + iconTextSpacing + ImGui::CalcTextSize(pLabel).x;
    };
    const auto textPillWidth = [&](const char *pLabel)
    {
        return style.FramePadding.x * 2.0f + ImGui::CalcTextSize(pLabel).x;
    };
    const auto rowWidth = [&](std::initializer_list<float> widths)
    {
        float width = 0.0f;
        bool first = true;

        for (float value : widths)
        {
            if (!first)
            {
                width += style.ItemSpacing.x;
            }

            width += value;
            first = false;
        }

        return width;
    };
    const float modeCreateWidth = std::max(
        rowWidth({iconPillWidth("Select"), iconPillWidth("Terrain"), iconPillWidth("Face")}),
        std::max(
            rowWidth({iconPillWidth("Entity"), iconPillWidth("Spawn"), iconPillWidth("Actor")}),
            rowWidth({
                iconPillWidth("Object"),
                iconPillWidth("Import BModel"),
                textPillWidth("Duplicate"),
                textPillWidth("Delete")
            }))) + cardInnerPadding;
    const float transformWidth = std::max(
        rowWidth({iconPillWidth("Move"), iconPillWidth("Rotate")}),
        std::max(
            rowWidth({iconPillWidth("World"), iconPillWidth("Local"), iconPillWidth("Snap")}),
            ImGui::CalcTextSize("Snap Step").x + style.ItemSpacing.x + 64.0f)) + cardInnerPadding;
    const float primaryViewWidth = rowWidth({
        iconPillWidth("Terrain"),
        iconPillWidth("Grid"),
        iconPillWidth("Textured"),
        iconPillWidth("Clay"),
        iconPillWidth("Entities"),
        iconPillWidth("Actors"),
        iconPillWidth(isIndoorDocument ? "Event Faces" : "Events")
    });
    float secondaryViewWidth = rowWidth({
        iconPillWidth("BModels"),
        iconPillWidth("Wire"),
        iconPillWidth("Grid Preview"),
        iconPillWidth("Selected"),
        iconPillWidth("Spawns"),
        iconPillWidth("Objects")
    });

    if (isMm9DatDocument)
    {
        secondaryViewWidth = std::max(
            secondaryViewWidth,
            rowWidth({
                iconPillWidth("BModels"),
                iconPillWidth("Models"),
                iconPillWidth("DAT"),
                iconPillWidth("Sky"),
                iconPillWidth("Physics"),
                iconPillWidth("Water"),
                iconPillWidth("Vis"),
                iconPillWidth("Invisible"),
                iconPillWidth("Helper"),
                iconPillWidth("Trigger"),
                iconPillWidth("Portals"),
                iconPillWidth("Bounds"),
                iconPillWidth("Wire"),
                iconPillWidth("Grid Preview"),
                iconPillWidth("Selected"),
                iconPillWidth("Spawns"),
                iconPillWidth("Objects")
            }));
    }

    const float viewWidth = std::max(primaryViewWidth, secondaryViewWidth) + cardInnerPadding;

    renderToolbarStatus(session);
    ImGui::Separator();
    ImGui::BeginTable("ToolbarContextBands", 4, ImGuiTableFlags_SizingFixedFit);
    ImGui::TableSetupColumn("ModeCreate", ImGuiTableColumnFlags_WidthFixed, modeCreateWidth);
    ImGui::TableSetupColumn("Transform", ImGuiTableColumnFlags_WidthFixed, transformWidth);
    ImGui::TableSetupColumn("View", ImGuiTableColumnFlags_WidthFixed, viewWidth);
    ImGui::TableSetupColumn("Spacer", ImGuiTableColumnFlags_WidthStretch);
    ImGui::TableNextRow();

    ImGui::TableNextColumn();
    beginToolbarCard("Mode", modeCreateWidth);
    renderToolModeButtons(session);
    ImGui::Dummy(ImVec2(0.0f, 1.0f));
    renderToolbarSubLabel("Create");
    renderCreateButtons(session);
    endToolbarCard();

    ImGui::TableNextColumn();
    beginToolbarCard("Transform", transformWidth);
    renderTransformToolbar();
    endToolbarCard();

    ImGui::TableNextColumn();
    beginToolbarCard("View", viewWidth);
    renderViewToolbar(session);
    endToolbarCard();
    ImGui::TableNextColumn();
    ImGui::EndTable();
    ImGui::PopStyleVar(2);

    ImGuiWindow *pWindow = ImGui::GetCurrentWindowRead();

    if (pWindow != nullptr && pWindow->DockNode != nullptr)
    {
        const float desiredHeight = std::clamp(
            ImGui::GetCursorPosY() + ImGui::GetStyle().WindowPadding.y,
            32.0f,
            180.0f);

        if (std::fabs(m_toolsDockTargetHeight - desiredHeight) > 1.0f)
        {
            pWindow->DockNode->SizeRef.y = desiredHeight;
            m_toolsDockTargetHeight = desiredHeight;
        }
    }

    ImGui::End();
}

void EditorMainWindow::renderToolModeButtons(EditorSession &session)
{
    const bool indoorDocument =
        session.hasDocument() && session.document().kind() == EditorDocument::Kind::Indoor;
    const auto renderModeButton = [this](const char *pLabel, EditorSelectionKind kind)
    {
        const bool selected = m_viewport.placementKind() == kind;

        if (renderIconTogglePill(pLabel, pLabel, selectionKindIcon(kind), selected))
        {
            m_viewport.setPlacementKind(selected ? EditorSelectionKind::None : kind);
        }
    };

    if (renderIconTogglePill("Select", "Select", UiIcon::Select, m_viewport.placementKind() == EditorSelectionKind::None))
    {
        m_viewport.setPlacementKind(EditorSelectionKind::None);
    }

    ImGui::SameLine();
    renderModeButton("Face", EditorSelectionKind::InteractiveFace);

    if (!indoorDocument)
    {
        ImGui::SameLine();
        renderModeButton("Terrain", EditorSelectionKind::Terrain);
    }
}

void EditorMainWindow::renderTransformToolbar()
{
    const auto renderTransformModeButton =
        [this](const char *pLabel, EditorOutdoorViewport::TransformGizmoMode mode)
    {
        const bool isSelected = m_viewport.transformGizmoMode() == mode;
        const UiIcon icon = mode == EditorOutdoorViewport::TransformGizmoMode::Translate ? UiIcon::Move : UiIcon::Rotate;

        if (renderIconTogglePill(pLabel, pLabel, icon, isSelected))
        {
            m_viewport.setTransformGizmoMode(mode);
        }
    };

    renderTransformModeButton("Move", EditorOutdoorViewport::TransformGizmoMode::Translate);
    ImGui::SameLine();
    renderTransformModeButton("Rotate", EditorOutdoorViewport::TransformGizmoMode::Rotate);
    ImGui::NewLine();

    const auto renderTransformSpaceButton =
        [this](const char *pLabel, EditorOutdoorViewport::TransformSpaceMode mode)
    {
        const bool isSelected = m_viewport.transformSpaceMode() == mode;
        const UiIcon icon = mode == EditorOutdoorViewport::TransformSpaceMode::World ? UiIcon::World : UiIcon::Local;

        if (renderIconTogglePill(pLabel, pLabel, icon, isSelected))
        {
            m_viewport.setTransformSpaceMode(mode);
        }
    };

    renderTransformSpaceButton("World", EditorOutdoorViewport::TransformSpaceMode::World);
    ImGui::SameLine();
    renderTransformSpaceButton("Local", EditorOutdoorViewport::TransformSpaceMode::Local);
    ImGui::SameLine();

    bool snapEnabled = m_viewport.snapEnabled();

    if (renderIconTogglePill("Snap", "Snap", UiIcon::Snap, snapEnabled))
    {
        m_viewport.setSnapEnabled(!snapEnabled);
    }

    ImGui::NewLine();
    int snapStep = m_viewport.snapStep();
    renderToolbarSubLabel("Snap Step");
    ImGui::SameLine();
    ImGui::SetNextItemWidth(64.0f);

    if (ImGui::InputInt("Step", &snapStep))
    {
        m_viewport.setSnapStep(snapStep);
    }
}

void EditorMainWindow::renderTerrainToolbar(EditorSession &session)
{
    ImGui::BeginDisabled(m_viewport.placementKind() != EditorSelectionKind::Terrain);
    static constexpr const char *FalloffModeLabels[] = {"Flat", "Linear", "Smooth"};
    static constexpr const char *FlattenTargetModeLabels[] = {"Sampled", "Numeric"};
    const bool paintEnabled = session.terrainPaintEnabled();
    const bool sculptEnabled = session.terrainSculptEnabled();

    ImGui::BeginGroup();

    if (renderIconTogglePill("PaintModeEnabled", "Paint", UiIcon::Paint, paintEnabled))
    {
        session.setTerrainPaintEnabled(!paintEnabled);

        if (!paintEnabled)
        {
            session.setTerrainSculptEnabled(false);
        }
    }

    if (ImGui::SameLine(), renderIconTogglePill("SculptModeEnabled", "Sculpt", UiIcon::Flatten, sculptEnabled))
    {
        session.setTerrainSculptEnabled(!sculptEnabled);

        if (!sculptEnabled)
        {
            session.setTerrainPaintEnabled(false);
        }
    }

    if (sculptEnabled)
    {
        ImGui::NewLine();
        renderToolbarSubLabel("Tool");
        ImGui::SameLine();
        const std::array<std::pair<const char *, EditorTerrainSculptMode>, 6> sculptModes = {{
            {"Raise", EditorTerrainSculptMode::Raise},
            {"Lower", EditorTerrainSculptMode::Lower},
            {"Flatten", EditorTerrainSculptMode::Flatten},
            {"Smooth", EditorTerrainSculptMode::Smooth},
            {"Noise", EditorTerrainSculptMode::Noise},
            {"Ramp", EditorTerrainSculptMode::Ramp}
        }};

        for (size_t index = 0; index < sculptModes.size(); ++index)
        {
            const auto &[pLabel, mode] = sculptModes[index];
            const bool selected = session.terrainSculptMode() == mode;

            if (renderIconTogglePill(pLabel, pLabel, terrainSculptModeIcon(mode), selected))
            {
                session.setTerrainSculptMode(mode);
            }

            if ((index % 3) != 2 && index + 1 < sculptModes.size())
            {
                ImGui::SameLine();
            }
        }
    }

    ImGui::EndGroup();
    ImGui::SameLine(0.0f, 10.0f);
    ImGui::BeginGroup();

    if (paintEnabled)
    {
        int tileId = static_cast<int>(session.terrainPaintTileId());
        renderToolbarSubLabel("Tile");
        ImGui::SameLine();
        ImGui::SetNextItemWidth(54.0f);

        if (ImGui::InputInt("##TerrainTile", &tileId))
        {
            tileId = std::clamp(tileId, 0, 255);
            session.setTerrainPaintTileId(static_cast<uint8_t>(tileId));
        }

        ImGui::SameLine();
        renderTerrainTilePreviewButton(
            m_viewport,
            session.terrainPaintTileId(),
            true,
            ImVec2(28.0f, 28.0f));

        ImGui::NewLine();
        renderToolbarSubLabel("Brush");
        ImGui::SameLine();

        const std::array<std::pair<const char *, EditorTerrainPaintMode>, 3> paintModes = {{
            {"Brush", EditorTerrainPaintMode::Brush},
            {"Rect", EditorTerrainPaintMode::Rectangle},
            {"Fill", EditorTerrainPaintMode::Fill}
        }};

        for (size_t index = 0; index < paintModes.size(); ++index)
        {
            const auto &[pLabel, mode] = paintModes[index];
            const bool selected = session.terrainPaintMode() == mode;

            if (renderIconTogglePill(pLabel, pLabel, terrainPaintModeIcon(mode), selected))
            {
                session.setTerrainPaintMode(mode);
            }

            if (index + 1 < paintModes.size())
            {
                ImGui::SameLine();
            }
        }

        if (session.terrainPaintMode() == EditorTerrainPaintMode::Brush)
        {
            ImGui::NewLine();
            int radius = session.terrainPaintRadius();
            renderToolbarSubLabel("Radius");
            ImGui::SameLine();
            ImGui::SetNextItemWidth(56.0f);

            if (ImGui::InputInt("##TerrainPaintRadius", &radius))
            {
                session.setTerrainPaintRadius(radius);
            }

            ImGui::SameLine();
            int edgeNoise = session.terrainPaintEdgeNoise();
            renderToolbarSubLabel("Edge");
            ImGui::SameLine();
            ImGui::SetNextItemWidth(52.0f);

            if (ImGui::InputInt("##TerrainPaintEdgeNoise", &edgeNoise))
            {
                session.setTerrainPaintEdgeNoise(edgeNoise);
            }
        }
    }
    else if (sculptEnabled)
    {
        renderToolbarSubLabel("Brush");
        ImGui::SameLine();
        int radius = session.terrainSculptRadius();
        ImGui::SetNextItemWidth(56.0f);

        if (ImGui::InputInt("##TerrainRadius", &radius))
        {
            session.setTerrainSculptRadius(radius);
        }

        ImGui::SameLine();
        int strength = session.terrainSculptStrength();
        renderToolbarSubLabel("Strength");
        ImGui::SameLine();
        ImGui::SetNextItemWidth(56.0f);

        if (ImGui::InputInt("##TerrainStrength", &strength))
        {
            session.setTerrainSculptStrength(strength);
        }

        ImGui::NewLine();
        renderToolbarSubLabel("Falloff");
        ImGui::SameLine();
        ImGui::AlignTextToFramePadding();
        ImGui::SetNextItemWidth(80.0f);
        int falloffMode = static_cast<int>(session.terrainSculptFalloffMode());

        if (ImGui::Combo("##TerrainFalloffMode", &falloffMode, FalloffModeLabels, IM_ARRAYSIZE(FalloffModeLabels)))
        {
            session.setTerrainSculptFalloffMode(static_cast<EditorTerrainFalloffMode>(falloffMode));
        }

        if (session.terrainSculptMode() == EditorTerrainSculptMode::Flatten)
        {
            ImGui::SameLine();
            int targetMode = static_cast<int>(session.terrainFlattenTargetMode());
            renderToolbarSubLabel("Target");
            ImGui::SameLine();
            ImGui::SetNextItemWidth(80.0f);

            if (ImGui::Combo(
                    "##TerrainFlattenTargetMode",
                    &targetMode,
                    FlattenTargetModeLabels,
                    IM_ARRAYSIZE(FlattenTargetModeLabels)))
            {
                session.setTerrainFlattenTargetMode(static_cast<EditorTerrainFlattenTargetMode>(targetMode));
            }

            if (session.terrainFlattenTargetMode() == EditorTerrainFlattenTargetMode::Numeric)
            {
                ImGui::NewLine();
                int targetHeight = session.terrainFlattenTargetHeight();
                renderToolbarSubLabel("Height");
                ImGui::SameLine();
                ImGui::SetNextItemWidth(56.0f);

                if (ImGui::InputInt("##TerrainFlattenTargetHeight", &targetHeight))
                {
                    session.setTerrainFlattenTargetHeight(targetHeight);
                }
            }
            else
            {
                ImGui::NewLine();
                ImGui::TextDisabled("H %d", session.terrainFlattenTargetHeight());

                const bool canPickSelected =
                    session.selection().kind == EditorSelectionKind::Terrain
                    && session.selection().index
                        < static_cast<size_t>(Game::OutdoorMapData::TerrainWidth * Game::OutdoorMapData::TerrainHeight);
                ImGui::BeginDisabled(!canPickSelected);

                if (ImGui::Button("Pick Selected"))
                {
                    tryPickFlattenTargetFromSelectedTerrainCell(session);
                }

                ImGui::EndDisabled();
                ImGui::SameLine();
                ImGui::TextDisabled("Alt+LMB");
            }
        }
    }

    ImGui::EndGroup();

    ImGui::EndDisabled();
}

void EditorMainWindow::renderViewToolbar(const EditorSession &session)
{
    const bool isIndoorDocument =
        session.hasDocument() && session.document().kind() == EditorDocument::Kind::Indoor;
    const bool isMm9DatDocument =
        session.hasDocument() && session.document().kind() == EditorDocument::Kind::Mm9Dat;
    bool hasPrimaryItem = false;
    const auto samePrimaryLine = [&hasPrimaryItem]()
    {
        if (hasPrimaryItem)
        {
            ImGui::SameLine();
        }

        hasPrimaryItem = true;
    };
    bool hasSecondaryItem = false;
    const auto sameSecondaryLine = [&hasSecondaryItem]()
    {
        if (hasSecondaryItem)
        {
            ImGui::SameLine();
        }

        hasSecondaryItem = true;
    };

    renderToolbarSubLabel("Primary");

    if (!isIndoorDocument)
    {
        samePrimaryLine();
        bool showTerrain = m_viewport.showTerrainFill();
        if (renderIconTogglePill("ViewTerrain", "Terrain", UiIcon::Terrain, showTerrain))
        {
            m_viewport.setShowTerrainFill(!showTerrain);
        }

        samePrimaryLine();
        bool showTerrainGrid = m_viewport.showTerrainGrid();
        if (renderIconTogglePill("ViewGrid", "Grid", UiIcon::Grid, showTerrainGrid))
        {
            m_viewport.setShowTerrainGrid(!showTerrainGrid);
        }

        samePrimaryLine();
        if (renderIconTogglePill(
                "PreviewTextured",
                "Textured",
                UiIcon::Textured,
                m_viewport.previewMaterialMode() == EditorOutdoorViewport::PreviewMaterialMode::Textured))
        {
            m_viewport.setPreviewMaterialMode(EditorOutdoorViewport::PreviewMaterialMode::Textured);
        }

        samePrimaryLine();
        if (renderIconTogglePill(
                "PreviewClay",
                "Clay",
                UiIcon::Clay,
                m_viewport.previewMaterialMode() == EditorOutdoorViewport::PreviewMaterialMode::Clay))
        {
            m_viewport.setPreviewMaterialMode(EditorOutdoorViewport::PreviewMaterialMode::Clay);
        }
    }

    samePrimaryLine();
    bool showEntities = m_viewport.showEntities();
    if (renderIconTogglePill("ViewEntities", "Entities", UiIcon::Entity, showEntities))
    {
        m_viewport.setShowEntities(!showEntities);
    }

    samePrimaryLine();
    bool showSpawns = m_viewport.showSpawns();
    bool showActors = m_viewport.showActors();
    if (renderIconTogglePill("ViewActors", "Actors", UiIcon::Actor, showActors))
    {
        m_viewport.setShowActors(!showActors);
    }

    samePrimaryLine();
    bool showEvents = m_viewport.showEventMarkers();
    if (renderIconTogglePill("ViewEvents", isIndoorDocument ? "Event Faces" : "Events", UiIcon::Select, showEvents))
    {
        m_viewport.setShowEventMarkers(!showEvents);
    }

    ImGui::NewLine();
    renderToolbarSubLabel("Secondary");

    if (!isIndoorDocument)
    {
        sameSecondaryLine();
        bool showBModels = m_viewport.showBModels();
        if (renderSecondaryIconTogglePill("ViewBModels", "BModels", UiIcon::Face, showBModels))
        {
            m_viewport.setShowBModels(!showBModels);
        }
    }

    if (isMm9DatDocument)
    {
        sameSecondaryLine();
        bool showModelInstances = m_viewport.showModelInstances();
        if (renderSecondaryIconTogglePill("ViewMm9Models", "Models", UiIcon::Object, showModelInstances))
        {
            m_viewport.setShowModelInstances(!showModelInstances);
        }

        const auto renderMm9DatSubsetToggle =
            [this, &sameSecondaryLine](
                const char *pId,
                const char *pLabel,
                EditorOutdoorViewport::Mm9DatWorldRenderSubset subset)
        {
            sameSecondaryLine();
            if (renderSecondaryIconTogglePill(
                    pId,
                    pLabel,
                    UiIcon::Face,
                    m_viewport.mm9DatWorldRenderSubset() == subset))
            {
                m_viewport.setMm9DatWorldRenderSubset(subset);
            }
        };

        renderMm9DatSubsetToggle(
            "ViewMm9DatWorld",
            "DAT",
            EditorOutdoorViewport::Mm9DatWorldRenderSubset::Default);
        renderMm9DatSubsetToggle(
            "ViewMm9DatSky",
            "Sky",
            EditorOutdoorViewport::Mm9DatWorldRenderSubset::Sky);
        renderMm9DatSubsetToggle(
            "ViewMm9DatPhysics",
            "Physics",
            EditorOutdoorViewport::Mm9DatWorldRenderSubset::Physics);
        renderMm9DatSubsetToggle(
            "ViewMm9DatWater",
            "Water",
            EditorOutdoorViewport::Mm9DatWorldRenderSubset::Water);
        renderMm9DatSubsetToggle(
            "ViewMm9DatVisibility",
            "Vis",
            EditorOutdoorViewport::Mm9DatWorldRenderSubset::Visibility);
        renderMm9DatSubsetToggle(
            "ViewMm9DatInvisible",
            "Invisible",
            EditorOutdoorViewport::Mm9DatWorldRenderSubset::Invisible);
        renderMm9DatSubsetToggle(
            "ViewMm9DatHelper",
            "Helper",
            EditorOutdoorViewport::Mm9DatWorldRenderSubset::Helper);
        renderMm9DatSubsetToggle(
            "ViewMm9DatTrigger",
            "Trigger",
            EditorOutdoorViewport::Mm9DatWorldRenderSubset::Trigger);

        sameSecondaryLine();
        bool showMm9Portals = m_viewport.showMm9DatPortals();
        if (renderSecondaryIconTogglePill("ViewMm9DatPortals", "Portals", UiIcon::Face, showMm9Portals))
        {
            m_viewport.setShowMm9DatPortals(!showMm9Portals);
        }

        sameSecondaryLine();
        bool showMm9WorldModelBounds = m_viewport.showMm9WorldModelBounds();
        if (renderSecondaryIconTogglePill(
                "ViewMm9WorldModelBounds",
                "World Bounds",
                UiIcon::Object,
                showMm9WorldModelBounds))
        {
            m_viewport.setShowMm9WorldModelBounds(!showMm9WorldModelBounds);
        }

        sameSecondaryLine();
        bool showMm9ObjectBounds = m_viewport.showMm9ObjectBounds();
        if (renderSecondaryIconTogglePill("ViewMm9ObjectBounds", "Bounds", UiIcon::Object, showMm9ObjectBounds))
        {
            m_viewport.setShowMm9ObjectBounds(!showMm9ObjectBounds);
        }

        sameSecondaryLine();
        bool showMm9AssetIssueMarkers = m_viewport.showMm9AssetIssueMarkers();
        if (renderSecondaryIconTogglePill(
                "ViewMm9AssetIssueMarkers",
                "Issues",
                UiIcon::Select,
                showMm9AssetIssueMarkers))
        {
            m_viewport.setShowMm9AssetIssueMarkers(!showMm9AssetIssueMarkers);
        }
    }

    if (isIndoorDocument)
    {
        sameSecondaryLine();
        bool showIndoorPortals = m_viewport.showIndoorPortals();

        if (renderSecondaryIconTogglePill("ViewIndoorPortals", "Portals", UiIcon::Face, showIndoorPortals))
        {
            m_viewport.setShowIndoorPortals(!showIndoorPortals);
        }

        sameSecondaryLine();
        bool showIndoorFloors = m_viewport.showIndoorFloors();

        if (renderSecondaryIconTogglePill("ViewIndoorFloors", "Floors", UiIcon::Face, showIndoorFloors))
        {
            m_viewport.setShowIndoorFloors(!showIndoorFloors);
        }

        sameSecondaryLine();
        bool showIndoorCeilings = m_viewport.showIndoorCeilings();

        if (renderSecondaryIconTogglePill("ViewIndoorCeilings", "Ceilings", UiIcon::Face, showIndoorCeilings))
        {
            m_viewport.setShowIndoorCeilings(!showIndoorCeilings);
        }

        sameSecondaryLine();
        const bool showIndoorGizmosEverywhere = m_viewport.showIndoorGizmosEverywhere();

        if (renderSecondaryIconTogglePill(
                "ViewIndoorGizmosEverywhere",
                showIndoorGizmosEverywhere ? "Gizmos All" : "Gizmos LoS",
                UiIcon::Select,
                showIndoorGizmosEverywhere))
        {
            m_viewport.setShowIndoorGizmosEverywhere(!showIndoorGizmosEverywhere);
        }

        const std::optional<uint16_t> isolatedRoomId = m_viewport.isolatedIndoorRoomId();

        if (isolatedRoomId.has_value())
        {
            sameSecondaryLine();
            const std::string label = "Room " + std::to_string(*isolatedRoomId);

            if (renderSecondaryIconTogglePill("ViewIndoorRoomIsolation", label.c_str(), UiIcon::Face, true))
            {
                m_viewport.setIsolatedIndoorRoomId(std::nullopt);
            }
        }
    }

    sameSecondaryLine();
    bool showBModelWire = m_viewport.showBModelWireframe();
    if (renderSecondaryIconTogglePill("ViewWire", "Wire", UiIcon::Wireframe, showBModelWire))
    {
        m_viewport.setShowBModelWireframe(!showBModelWire);
    }

    if (!isIndoorDocument)
    {
        sameSecondaryLine();
        if (renderSecondaryIconTogglePill(
                "PreviewGrid",
                "Grid",
                UiIcon::Grid,
                m_viewport.previewMaterialMode() == EditorOutdoorViewport::PreviewMaterialMode::Grid))
        {
            m_viewport.setPreviewMaterialMode(EditorOutdoorViewport::PreviewMaterialMode::Grid);
        }

        sameSecondaryLine();
        bool previewSelectedOnly = m_viewport.forcePreviewOnSelectedOnly();
        if (renderSecondaryIconTogglePill("PreviewSelected", "Selected", UiIcon::Select, previewSelectedOnly))
        {
            m_viewport.setForcePreviewOnSelectedOnly(!previewSelectedOnly);
        }
    }

    sameSecondaryLine();
    if (renderSecondaryIconTogglePill("ViewSpawns", "Spawns", UiIcon::Spawn, showSpawns))
    {
        m_viewport.setShowSpawns(!showSpawns);
    }

    sameSecondaryLine();
    bool showObjects = m_viewport.showSpriteObjects();
    if (renderSecondaryIconTogglePill("ViewObjects", "Objects", UiIcon::Object, showObjects))
    {
        m_viewport.setShowSpriteObjects(!showObjects);
    }

    ImGui::NewLine();
    bool showEntityBillboards = m_viewport.showEntityBillboards();
    if (renderSecondaryTogglePill("Entity Preview", showEntityBillboards))
    {
        m_viewport.setShowEntityBillboards(!showEntityBillboards);
    }

    ImGui::SameLine();
    bool showActorBillboards = m_viewport.showActorBillboards();
    if (renderSecondaryTogglePill("Actor Preview", showActorBillboards))
    {
        m_viewport.setShowActorBillboards(!showActorBillboards);
    }

    ImGui::SameLine();
    bool showSpawnActorBillboards = m_viewport.showSpawnActorBillboards();
    if (renderSecondaryTogglePill("Spawn Preview", showSpawnActorBillboards))
    {
        m_viewport.setShowSpawnActorBillboards(!showSpawnActorBillboards);
    }

    ImGui::SameLine();
    bool showChestLinks = m_viewport.showChestLinks();
    if (renderSecondaryTogglePill("Chest Links", showChestLinks))
    {
        m_viewport.setShowChestLinks(!showChestLinks);
    }
}

bool EditorMainWindow::playtestCurrentMap(EditorSession &session, std::string &errorMessage) const
{
    if (!session.hasDocument())
    {
        errorMessage = "no document is loaded";
        return false;
    }

    if (session.document().isDirty() && !session.saveActiveDocument(errorMessage))
    {
        return false;
    }

    if (session.document().isRuntimeBuildDirty() && !session.buildActiveDocument(errorMessage))
    {
        return false;
    }

    const std::filesystem::path gameExecutablePath = defaultGameExecutablePath();

    if (gameExecutablePath.empty())
    {
        errorMessage = "could not locate build/game/openyamm for playtest launch";
        return false;
    }

    const std::string mapFileName = session.document().displayName();

    if (mapFileName.empty())
    {
        errorMessage = "document has no runtime map file";
        return false;
    }

    const std::vector<std::string> arguments = {"--map", mapFileName};

    if (!launchDetachedProcess(gameExecutablePath, arguments, errorMessage))
    {
        return false;
    }

    session.logInfo("Launched playtest for " + mapFileName);
    return true;
}

void EditorMainWindow::renderToolbarStatus(const EditorSession &session)
{
    if (session.hasDocument())
    {
        const EditorDocument &document = session.document();
        const bool sourceDirty = document.isDirty();
        const bool buildDirty = document.isRuntimeBuildDirty();
        const EditorOutdoorMapPackageMetadata &packageMetadata = document.outdoorMapPackageMetadata();

        ImGui::PushStyleColor(ImGuiCol_Text, colorFromRgb(0xE6E8EB));
        ImGui::Text(
            "%s  ·  %s v%u  ·  %s",
            document.displayName().c_str(),
            document.hasMapPackageRoot() ? packageMetadata.packageId.c_str() : "legacy",
            packageMetadata.version,
            document.sceneVirtualPath().c_str());
        ImGui::PopStyleColor();

        if (ImGui::IsItemHovered())
        {
            ImGui::BeginTooltip();
            ImGui::Text("Package Path: %s", document.mapPackagePhysicalPath().string().c_str());
            ImGui::Text("Display Name: %s", packageMetadata.displayName.c_str());
            ImGui::Text("Source Fingerprint: %s", packageMetadata.sourceFingerprint.c_str());
            ImGui::Text("Built Fingerprint: %s", packageMetadata.builtSourceFingerprint.c_str());
            ImGui::EndTooltip();
        }

        ImGui::SameLine();
        renderStatusPill(
            sourceDirty ? "Source · Dirty" : "Source · Saved",
            sourceDirty ? 0xF2DEC2 : 0xD7F0DB,
            sourceDirty ? 0xB9873D : 0x5FA36A,
            sourceDirty ? 0x3A2B18 : 0x1A2B1D);
        ImGui::SameLine();
        renderStatusPill(
            buildDirty ? "Build · Stale" : "Build · Ready",
            buildDirty ? 0xF2DEC2 : 0xD7F0DB,
            buildDirty ? 0xB9873D : 0x5FA36A,
            buildDirty ? 0x3A2B18 : 0x1A2B1D);
        ImGui::SameLine();
        renderStatusPill(
            ("Validation · " + std::to_string(session.validationMessages().size())).c_str(),
            session.validationMessages().empty() ? 0xD7F0DB : 0xF2DEC2,
            session.validationMessages().empty() ? 0x5FA36A : 0xD0A44C,
            session.validationMessages().empty() ? 0x1A2B1D : 0x332814);
        ImGui::SameLine();
        const bx::Vec3 &cameraPosition = m_viewport.cameraPosition();
        ImGui::TextDisabled(
            "X %.0f  Y %.0f  Z %.0f",
            cameraPosition.x,
            cameraPosition.y,
            cameraPosition.z);
        if (session.hasDocument() && session.document().kind() == EditorDocument::Kind::Mm9Dat)
        {
            const EditorOutdoorViewport::RenderSubmissionStats &submissionStats = m_viewport.lastRenderSubmissionStats();
            ImGui::SameLine();
            const std::string mm9StatsText =
                "DAT Vtx " + std::to_string(submissionStats.datWorldSubmittedVertices)
                + " · Model Vtx " + std::to_string(submissionStats.modelInstanceSubmittedVertices)
                + " · Overlay Vtx "
                + std::to_string(
                    submissionStats.mm9DatPortalOverlayVertices
                    + submissionStats.mm9DatWorldModelOverlayVertices
                    + submissionStats.mm9DatObjectOverlayVertices
                    + submissionStats.mm9DatSourceMarkerVertices
                    + submissionStats.mm9DatAssetIssueMarkerVertices
                    + submissionStats.mm9DatMechanismTargetMarkerVertices);
            renderStatusPill(
                mm9StatsText.c_str(),
                submissionStats.modelInstanceSubmittedVertices == 0 ? 0xF2DEC2 : 0xD7F0DB,
                submissionStats.modelInstanceSubmittedVertices == 0 ? 0xB9873D : 0x5FA36A,
                submissionStats.modelInstanceSubmittedVertices == 0 ? 0x3A2B18 : 0x1A2B1D);
        }

        if (!m_statusMessage.empty())
        {
            ImGui::SameLine();

            if (m_statusMessageKind == StatusMessageKind::Success)
            {
                renderStatusPill(m_statusMessage.c_str(), 0xD7F0DB, 0x5FA36A, 0x1A2B1D);
            }
            else if (m_statusMessageKind == StatusMessageKind::Error)
            {
                renderStatusPill(m_statusMessage.c_str(), 0xF5D3D3, 0xCC6666, 0x301A1A);
            }
            else
            {
                renderStatusPill(m_statusMessage.c_str(), 0xE7D8B8, 0xD0A44C, 0x332814);
            }
        }

        if (!session.validationMessages().empty())
        {
            ImGui::SameLine();
            ImGui::TextDisabled("hover validation");

            if (ImGui::IsItemHovered())
            {
                ImGui::BeginTooltip();
                ImGui::TextUnformatted("Validation");

                for (const std::string &message : session.validationMessages())
                {
                    ImGui::BulletText("%s", message.c_str());
                }

                ImGui::EndTooltip();
            }
        }
    }
    else
    {
        ImGui::TextUnformatted("No document loaded.");
    }
}

void EditorMainWindow::setStatusMessage(StatusMessageKind kind, const std::string &message)
{
    m_statusMessageKind = kind;
    m_statusMessage = message;
}

std::optional<bgfx::TextureHandle> EditorMainWindow::ensureBitmapPreviewTexture(
    const EditorSession &session,
    const std::string &textureName,
    int16_t paletteId,
    bool spriteTexture) const
{
    const Engine::AssetFileSystem *pAssetFileSystem = session.assetFileSystem();

    if (pAssetFileSystem == nullptr)
    {
        return std::nullopt;
    }

    const std::string normalizedName =
        (spriteTexture ? "sprite|" : "bitmap|") + toLowerCopy(textureName) + "|" + std::to_string(static_cast<int>(paletteId));
    const auto existingIt = m_bitmapPreviewTextures.find(normalizedName);

    if (existingIt != m_bitmapPreviewTextures.end())
    {
        if (bgfx::isValid(existingIt->second))
        {
            return existingIt->second;
        }

        return std::nullopt;
    }

    int width = 0;
    int height = 0;
    const std::optional<std::vector<uint8_t>> pixels = spriteTexture
        ? loadSpritePreviewPixels(*pAssetFileSystem, textureName, paletteId, width, height)
        : loadBitmapPreviewPixels(*pAssetFileSystem, session.bitmapTextureNames(), textureName, width, height);

    if (!pixels || width <= 0 || height <= 0)
    {
        const bgfx::TextureHandle invalidHandle = BGFX_INVALID_HANDLE;
        m_bitmapPreviewTextures.emplace(normalizedName, invalidHandle);
        m_bitmapPreviewTextureSizes.emplace(normalizedName, std::pair<int, int>{0, 0});
        return std::nullopt;
    }

    const bgfx::TextureHandle textureHandle = bgfx::createTexture2D(
        static_cast<uint16_t>(width),
        static_cast<uint16_t>(height),
        false,
        1,
        bgfx::TextureFormat::BGRA8,
        BGFX_SAMPLER_MIN_POINT | BGFX_SAMPLER_MAG_POINT | BGFX_SAMPLER_MIP_POINT,
        bgfx::copy(pixels->data(), static_cast<uint32_t>(pixels->size())));

    m_bitmapPreviewTextures.emplace(normalizedName, textureHandle);
    m_bitmapPreviewTextureSizes.emplace(normalizedName, std::pair<int, int>{width, height});

    if (!bgfx::isValid(textureHandle))
    {
        return std::nullopt;
    }

    return textureHandle;
}

std::optional<std::pair<int, int>> EditorMainWindow::bitmapPreviewTextureSize(
    const std::string &textureName,
    int16_t paletteId,
    bool spriteTexture) const
{
    const std::string normalizedName =
        (spriteTexture ? "sprite|" : "bitmap|") + toLowerCopy(textureName) + "|" + std::to_string(static_cast<int>(paletteId));
    const auto existingIt = m_bitmapPreviewTextureSizes.find(normalizedName);

    if (existingIt == m_bitmapPreviewTextureSizes.end())
    {
        return std::nullopt;
    }

    if (existingIt->second.first <= 0 || existingIt->second.second <= 0)
    {
        return std::nullopt;
    }

    return existingIt->second;
}

std::optional<bgfx::TextureHandle> EditorMainWindow::ensureMm9DtxMipPreviewTexture(
    const std::filesystem::path &sourcePath,
    size_t mipLevel) const
{
    if (sourcePath.empty())
    {
        return std::nullopt;
    }

    const std::string cacheKey = sourcePath.lexically_normal().generic_string() + "|" + std::to_string(mipLevel);
    const auto existingIt = m_mm9DtxMipPreviewTextures.find(cacheKey);

    if (existingIt != m_mm9DtxMipPreviewTextures.end())
    {
        if (bgfx::isValid(existingIt->second))
        {
            return existingIt->second;
        }

        return std::nullopt;
    }

    std::ifstream input(sourcePath, std::ios::binary);

    if (!input)
    {
        const bgfx::TextureHandle invalidHandle = BGFX_INVALID_HANDLE;
        m_mm9DtxMipPreviewTextures.emplace(cacheKey, invalidHandle);
        m_mm9DtxMipPreviewTextureSizes.emplace(cacheKey, std::pair<int, int>{0, 0});
        return std::nullopt;
    }

    const std::vector<uint8_t> bytes{
        std::istreambuf_iterator<char>(input),
        std::istreambuf_iterator<char>()};
    std::string errorMessage;
    const std::optional<Game::Mm9DtxTexture> texture =
        Game::decodeMm9DtxMipTexture(bytes, mipLevel, errorMessage);

    if (!texture
        || texture->width == 0
        || texture->height == 0
        || texture->pixelsBgra.empty())
    {
        const bgfx::TextureHandle invalidHandle = BGFX_INVALID_HANDLE;
        m_mm9DtxMipPreviewTextures.emplace(cacheKey, invalidHandle);
        m_mm9DtxMipPreviewTextureSizes.emplace(cacheKey, std::pair<int, int>{0, 0});
        return std::nullopt;
    }

    const bgfx::TextureHandle textureHandle = bgfx::createTexture2D(
        static_cast<uint16_t>(texture->width),
        static_cast<uint16_t>(texture->height),
        false,
        1,
        bgfx::TextureFormat::BGRA8,
        BGFX_SAMPLER_MIN_POINT | BGFX_SAMPLER_MAG_POINT | BGFX_SAMPLER_MIP_POINT,
        bgfx::copy(texture->pixelsBgra.data(), static_cast<uint32_t>(texture->pixelsBgra.size())));

    m_mm9DtxMipPreviewTextures.emplace(cacheKey, textureHandle);
    m_mm9DtxMipPreviewTextureSizes.emplace(
        cacheKey,
        std::pair<int, int>{static_cast<int>(texture->width), static_cast<int>(texture->height)});

    if (!bgfx::isValid(textureHandle))
    {
        return std::nullopt;
    }

    return textureHandle;
}

std::optional<std::pair<int, int>> EditorMainWindow::mm9DtxMipPreviewTextureSize(
    const std::filesystem::path &sourcePath,
    size_t mipLevel) const
{
    const std::string cacheKey = sourcePath.lexically_normal().generic_string() + "|" + std::to_string(mipLevel);
    const auto existingIt = m_mm9DtxMipPreviewTextureSizes.find(cacheKey);

    if (existingIt == m_mm9DtxMipPreviewTextureSizes.end())
    {
        return std::nullopt;
    }

    if (existingIt->second.first <= 0 || existingIt->second.second <= 0)
    {
        return std::nullopt;
    }

    return existingIt->second;
}

void EditorMainWindow::renderBitmapPreviewTooltip(
    const EditorSession &session,
    const std::string &label,
    const std::string &textureName,
    int16_t paletteId,
    bool spriteTexture) const
{
    const std::optional<bgfx::TextureHandle> textureHandle =
        ensureBitmapPreviewTexture(session, textureName, paletteId, spriteTexture);

    if (!textureHandle || !bgfx::isValid(*textureHandle))
    {
        return;
    }

    const std::optional<std::pair<int, int>> textureSize =
        bitmapPreviewTextureSize(textureName, paletteId, spriteTexture);
    const ImVec2 imageSize = textureSize
        ? ImVec2(static_cast<float>(textureSize->first), static_cast<float>(textureSize->second))
        : ImVec2(96.0f, 96.0f);

    const ImVec2 mousePosition = ImGui::GetMousePos();
    ImGui::SetNextWindowPos(
        ImVec2(mousePosition.x - 200.0f, mousePosition.y),
        ImGuiCond_Always,
        ImVec2(1.0f, 0.0f));
    ImGui::BeginTooltip();
    ImGui::TextUnformatted(label.c_str());
    ImGui::TextUnformatted(textureName.c_str());
    ImGui::Image(
        static_cast<ImTextureID>(static_cast<uintptr_t>(textureHandle->idx + 1)),
        imageSize,
        ImVec2(0.0f, 0.0f),
        ImVec2(1.0f, 1.0f));
    ImGui::EndTooltip();
}

bool EditorMainWindow::renderIdOptionSelectorWithBitmapPreview(
    EditorSession &session,
    const char *pLabel,
    uint32_t &value,
    const std::vector<EditorIdLabelOption> &options,
    const char *pZeroLabel,
    const char *pFallbackPrefix,
    bool transient,
    const std::function<std::optional<std::pair<std::string, int16_t>>(uint32_t)> &resolveTexture) const
{
    beginInspectorFieldRow(pLabel);

    const std::string comboId = inspectorFieldId(pLabel);
    const std::string preview = selectorPreviewLabel(value, options, pZeroLabel, pFallbackPrefix);

    if (!ImGui::BeginCombo(comboId.c_str(), preview.c_str()))
    {
        return false;
    }

    const ImGuiID filterStorageId = ImGui::GetID((comboId + "/filter").c_str());
    static std::unordered_map<ImGuiID, std::string> filters;
    std::string &filter = filters[filterStorageId];
    char filterBuffer[128] = {};
    std::snprintf(filterBuffer, sizeof(filterBuffer), "%s", filter.c_str());
    ImGui::SetNextItemWidth(-FLT_MIN);

    if (ImGui::InputText("##Filter", filterBuffer, sizeof(filterBuffer)))
    {
        filter = filterBuffer;
    }

    const std::string normalizedFilter = toLowerCopy(filter);
    bool changed = false;

    if (pZeroLabel != nullptr)
    {
        const bool selected = value == 0;

        if ((normalizedFilter.empty() || toLowerCopy(pZeroLabel).find(normalizedFilter) != std::string::npos)
            && ImGui::Selectable(pZeroLabel, selected))
        {
            if (value != 0)
            {
                if (!transient)
                {
                    session.captureUndoSnapshot();
                }

                value = 0;
                changed = true;
            }
        }

        if (selected)
        {
            ImGui::SetItemDefaultFocus();
        }
    }

    for (const EditorIdLabelOption &option : options)
    {
        if (!optionMatchesFilter(option, normalizedFilter))
        {
            continue;
        }

        const bool selected = option.id == value;

        if (ImGui::Selectable(option.label.c_str(), selected))
        {
            if (option.id != value)
            {
                if (!transient)
                {
                    session.captureUndoSnapshot();
                }

                value = option.id;
                changed = true;
            }
        }

        if (ImGui::IsItemHovered())
        {
            const std::optional<std::pair<std::string, int16_t>> preview = resolveTexture(option.id);

            if (preview)
            {
                renderBitmapPreviewTooltip(session, option.label, preview->first, preview->second, true);
            }
        }

        if (selected)
        {
            ImGui::SetItemDefaultFocus();
        }
    }

    ImGui::EndCombo();
    return changed;
}

bool EditorMainWindow::renderDecorationSelector(
    EditorSession &session,
    const char *pLabel,
    uint16_t &decorationListId,
    bool transient) const
{
    uint32_t selectedId = decorationListId;

    if (!renderIdOptionSelectorWithBitmapPreview(
            session,
            pLabel,
            selectedId,
            session.decorationOptions(),
            nullptr,
            "Decoration",
            transient,
            [&session](uint32_t optionId)
            {
                return session.previewDecorationTexture(static_cast<uint16_t>(std::min<uint32_t>(optionId, 65535)));
            }))
    {
        return false;
    }

    decorationListId = static_cast<uint16_t>(std::min<uint32_t>(selectedId, 65535));
    return true;
}

bool EditorMainWindow::renderObjectSelector(
    EditorSession &session,
    const char *pLabel,
    uint16_t &objectDescriptionId,
    bool transient) const
{
    uint32_t selectedId = objectDescriptionId;

    if (!renderIdOptionSelectorWithBitmapPreview(
            session,
            pLabel,
            selectedId,
            session.objectOptions(),
            nullptr,
            "Object",
            transient,
            [&session](uint32_t optionId)
            {
                return session.previewObjectTexture(static_cast<uint16_t>(std::min<uint32_t>(optionId, 65535)));
            }))
    {
        return false;
    }

    objectDescriptionId = static_cast<uint16_t>(std::min<uint32_t>(selectedId, 65535));
    return true;
}

bool EditorMainWindow::renderMonsterTemplateSelector(
    EditorSession &session,
    const char *pLabel,
    Game::MapDeltaActor &actor,
    bool transient) const
{
    const int16_t previousMonsterInfoId = actor.monsterInfoId;
    uint32_t selectedId = actor.monsterInfoId > 0 ? static_cast<uint32_t>(actor.monsterInfoId) : 0;

    if (!renderIdOptionSelectorWithBitmapPreview(
            session,
            pLabel,
            selectedId,
            session.monsterOptions(),
            "<none>",
            "Monster Template",
            transient,
            [&session, &actor](uint32_t optionId)
            {
                const int16_t resolvedId = static_cast<int16_t>(std::min<uint32_t>(optionId, 32767));
                return session.previewMonsterTexture(resolvedId, actor.monsterId);
            }))
    {
        return false;
    }

    actor.monsterInfoId = static_cast<int16_t>(std::min<uint32_t>(selectedId, 32767));
    applyMonsterTemplateSelection(session, actor, previousMonsterInfoId);
    return true;
}

void EditorMainWindow::destroyBitmapPreviewTextures()
{
    for (const auto &[name, textureHandle] : m_bitmapPreviewTextures)
    {
        if (bgfx::isValid(textureHandle))
        {
            bgfx::destroy(textureHandle);
        }
    }

    m_bitmapPreviewTextures.clear();
    m_bitmapPreviewTextureSizes.clear();

    for (const auto &[name, textureHandle] : m_mm9DtxMipPreviewTextures)
    {
        if (bgfx::isValid(textureHandle))
        {
            bgfx::destroy(textureHandle);
        }
    }

    m_mm9DtxMipPreviewTextures.clear();
    m_mm9DtxMipPreviewTextureSizes.clear();
}

bool EditorMainWindow::renderBitmapTextureSelector(
    EditorSession &session,
    const char *pLabel,
    std::string &value,
    std::optional<size_t> bmodelIndex) const
{
    beginInspectorFieldRow(pLabel);

    const std::string popupId = inspectorFieldId(pLabel) + "/popup";
    const ImVec2 previewSize(56.0f, 56.0f);
    bool changed = false;

    if (session.assetFileSystem() != nullptr && !value.empty())
    {
        const std::optional<bgfx::TextureHandle> textureHandle =
            ensureBitmapPreviewTexture(session, value);

        if (textureHandle && bgfx::isValid(*textureHandle))
        {
            ImGui::Image(
                static_cast<ImTextureID>(static_cast<uintptr_t>(textureHandle->idx + 1)),
                previewSize,
                ImVec2(0.0f, 0.0f),
                ImVec2(1.0f, 1.0f));
        }
        else
        {
            ImGui::Button(value.c_str(), previewSize);
        }
    }
    else
    {
        ImGui::Button(value.empty() ? "<none>" : value.c_str(), previewSize);
    }

    ImGui::SameLine();

    if (ImGui::Button("Browse..."))
    {
        ImGui::OpenPopup(popupId.c_str());
    }

    ImGui::SameLine();
    ImGui::TextUnformatted(value.empty() ? "<none>" : value.c_str());

    if (ImGui::BeginPopup(popupId.c_str()))
    {
        const ImGuiID filterStorageId = ImGui::GetID((popupId + "/filter").c_str());
        const ImGuiID sourceStorageId = ImGui::GetID((popupId + "/source").c_str());
        static std::unordered_map<ImGuiID, std::string> filters;
        static std::unordered_map<ImGuiID, int> sourceModeByPopup;
        std::string &filter = filters[filterStorageId];
        int &sourceMode = sourceModeByPopup[sourceStorageId];
        char filterBuffer[128] = {};
        std::snprintf(filterBuffer, sizeof(filterBuffer), "%s", filter.c_str());
        ImGui::SetNextItemWidth(-FLT_MIN);

        if (ImGui::InputText("##Filter", filterBuffer, sizeof(filterBuffer)))
        {
            filter = filterBuffer;
        }

        std::vector<std::string> availableTextures;

        if (!bmodelIndex.has_value() && sourceMode == 0)
        {
            sourceMode = 1;
        }

        if (sourceMode == 2)
        {
            availableTextures = session.bitmapTextureNames();
        }
        else if (sourceMode == 0 && bmodelIndex.has_value())
        {
            availableTextures = session.usedBitmapTextureNamesForBModel(*bmodelIndex);

            if (availableTextures.empty())
            {
                availableTextures = session.usedBitmapTextureNamesInMap();
            }
        }
        else
        {
            availableTextures = session.usedBitmapTextureNamesInMap();
        }

        ImGui::Spacing();
        ImGui::TextUnformatted("Source:");
        ImGui::SameLine();

        if (bmodelIndex.has_value())
        {
            ImGui::RadioButton("On This BModel##TextureSource", &sourceMode, 0);
            ImGui::SameLine();
        }

        ImGui::RadioButton("Used In Map##TextureSource", &sourceMode, 1);
        ImGui::SameLine();
        ImGui::RadioButton("All Textures##TextureSource", &sourceMode, 2);

        const std::string normalizedFilter = toLowerCopy(filter);

        if (ImGui::BeginChild("TextureBrowserList", ImVec2(560.0f, 420.0f), ImGuiChildFlags_Borders))
        {
            int tilesOnRow = 0;

            for (const std::string &option : availableTextures)
            {
                if (!normalizedFilter.empty() && toLowerCopy(option).find(normalizedFilter) == std::string::npos)
                {
                    continue;
                }

                ImGui::PushID(option.c_str());
                const bool selected = toLowerCopy(option) == toLowerCopy(value);
                const std::optional<bgfx::TextureHandle> textureHandle =
                    session.assetFileSystem() != nullptr ? ensureBitmapPreviewTexture(session, option) : std::nullopt;

                if (selected)
                {
                    ImGui::PushStyleColor(ImGuiCol_ChildBg, ImVec4(0.18f, 0.16f, 0.12f, 1.0f));
                }

                if (ImGui::BeginChild("TextureTile", ImVec2(96.0f, 112.0f), ImGuiChildFlags_Borders))
                {
                    if (textureHandle && bgfx::isValid(*textureHandle))
                    {
                        ImGui::ImageButton(
                            "##TextureImage",
                            static_cast<ImTextureID>(static_cast<uintptr_t>(textureHandle->idx + 1)),
                            ImVec2(80.0f, 80.0f),
                            ImVec2(0.0f, 0.0f),
                            ImVec2(1.0f, 1.0f));
                    }
                    else
                    {
                        ImGui::Button(option.c_str(), ImVec2(80.0f, 80.0f));
                    }

                    if (ImGui::IsItemClicked())
                    {
                        session.captureUndoSnapshot();
                        value = option;
                        changed = true;
                        ImGui::CloseCurrentPopup();
                    }

                    ImGui::PushTextWrapPos(ImGui::GetCursorPos().x + 80.0f);
                    ImGui::TextUnformatted(option.c_str());
                    ImGui::PopTextWrapPos();
                }
                ImGui::EndChild();

                if (selected)
                {
                    ImGui::PopStyleColor();
                }

                ++tilesOnRow;
                if ((tilesOnRow % 5) != 0)
                {
                    ImGui::SameLine();
                }

                ImGui::PopID();
            }
        }
        ImGui::EndChild();

        ImGui::EndPopup();
    }

    return changed;
}

bool EditorMainWindow::renderInlineBitmapTextureSelector(
    EditorSession &session,
    const char *pId,
    std::string &value,
    std::optional<size_t> bmodelIndex) const
{
    const std::string popupId = std::string(pId) + "/popup";
    bool changed = false;

    if (ImGui::Button((value.empty() ? "<none>" : value).c_str(), ImVec2(-FLT_MIN, 0.0f)))
    {
        ImGui::OpenPopup(popupId.c_str());
    }

    if (ImGui::BeginPopup(popupId.c_str()))
    {
        const ImGuiID filterStorageId = ImGui::GetID((popupId + "/filter").c_str());
        const ImGuiID sourceStorageId = ImGui::GetID((popupId + "/source").c_str());
        static std::unordered_map<ImGuiID, std::string> filters;
        static std::unordered_map<ImGuiID, int> sourceModeByPopup;
        std::string &filter = filters[filterStorageId];
        int &sourceMode = sourceModeByPopup[sourceStorageId];
        char filterBuffer[128] = {};
        std::snprintf(filterBuffer, sizeof(filterBuffer), "%s", filter.c_str());
        ImGui::SetNextItemWidth(320.0f);

        if (ImGui::InputText("##Filter", filterBuffer, sizeof(filterBuffer)))
        {
            filter = filterBuffer;
        }

        std::vector<std::string> availableTextures;

        if (!bmodelIndex.has_value() && sourceMode == 0)
        {
            sourceMode = 1;
        }

        if (sourceMode == 2)
        {
            availableTextures = session.bitmapTextureNames();
        }
        else if (sourceMode == 0 && bmodelIndex.has_value())
        {
            availableTextures = session.usedBitmapTextureNamesForBModel(*bmodelIndex);

            if (availableTextures.empty())
            {
                availableTextures = session.usedBitmapTextureNamesInMap();
            }
        }
        else
        {
            availableTextures = session.usedBitmapTextureNamesInMap();
        }

        ImGui::Spacing();

        if (bmodelIndex.has_value())
        {
            ImGui::RadioButton("This BModel##InlineTextureSource", &sourceMode, 0);
            ImGui::SameLine();
        }

        ImGui::RadioButton("Map##InlineTextureSource", &sourceMode, 1);
        ImGui::SameLine();
        ImGui::RadioButton("All##InlineTextureSource", &sourceMode, 2);

        const std::string normalizedFilter = toLowerCopy(filter);

        if (ImGui::BeginChild("InlineTextureBrowserList", ImVec2(360.0f, 260.0f), ImGuiChildFlags_Borders))
        {
            for (const std::string &option : availableTextures)
            {
                if (!normalizedFilter.empty() && toLowerCopy(option).find(normalizedFilter) == std::string::npos)
                {
                    continue;
                }

                if (ImGui::Selectable(option.c_str(), toLowerCopy(option) == toLowerCopy(value)))
                {
                    value = option;
                    changed = true;
                    ImGui::CloseCurrentPopup();
                    break;
                }

                if (ImGui::IsItemHovered() && session.assetFileSystem() != nullptr)
                {
                    const std::optional<bgfx::TextureHandle> textureHandle =
                        ensureBitmapPreviewTexture(session, option);

                    if (textureHandle && bgfx::isValid(*textureHandle))
                    {
                        ImGui::BeginTooltip();
                        ImGui::TextUnformatted(option.c_str());
                        ImGui::Image(
                            static_cast<ImTextureID>(static_cast<uintptr_t>(textureHandle->idx + 1)),
                            ImVec2(96.0f, 96.0f),
                            ImVec2(0.0f, 0.0f),
                            ImVec2(1.0f, 1.0f));
                        ImGui::EndTooltip();
                    }
                }
            }
        }

        ImGui::EndChild();
        ImGui::EndPopup();
    }

    return changed;
}

void EditorMainWindow::renderPlacementButtons(EditorSession &session)
{
    if (session.hasDocument() && session.document().kind() == EditorDocument::Kind::Indoor)
    {
        ImGui::TextDisabled("Indoor geometry is read-only in Wave 1.");
        return;
    }

    const auto renderPlacementButton =
        [this](const char *pId, const char *pLabel, EditorSelectionKind kind)
    {
        const bool selected = m_viewport.placementKind() == kind;
        return renderIconTogglePill(pId, pLabel, selectionKindIcon(kind), selected);
    };

    const bool entityPlacementSelected = m_viewport.placementKind() == EditorSelectionKind::Entity;
    if (renderIconTogglePill("PlaceEntity", "Entity", UiIcon::Entity, entityPlacementSelected))
    {
        if (entityPlacementSelected)
        {
            m_viewport.setPlacementKind(EditorSelectionKind::None);
        }
        else
        {
            if (session.selection().kind == EditorSelectionKind::Entity)
            {
                const Game::OutdoorSceneData &sceneData = session.document().outdoorSceneData();

                if (session.selection().index < sceneData.entities.size())
                {
                    session.setPendingEntityDecorationListId(
                        sceneData.entities[session.selection().index].entity.decorationListId);
                }
            }

            m_viewport.setPlacementKind(EditorSelectionKind::Entity);
        }
    }

    ImGui::SameLine();
    if (renderPlacementButton("PlaceSpawn", "Spawn", EditorSelectionKind::Spawn))
    {
        const bool selected = m_viewport.placementKind() == EditorSelectionKind::Spawn;

        if (selected)
        {
            m_viewport.setPlacementKind(EditorSelectionKind::None);
        }
        else
        {
            if (session.selection().kind == EditorSelectionKind::Spawn)
            {
                const Game::OutdoorSceneData &sceneData = session.document().outdoorSceneData();

                if (session.selection().index < sceneData.spawns.size())
                {
                    session.setPendingSpawn(sceneData.spawns[session.selection().index].spawn);
                }
            }

            m_viewport.setPlacementKind(EditorSelectionKind::Spawn);
        }
    }

    ImGui::SameLine();
    if (renderPlacementButton("PlaceActor", "Actor", EditorSelectionKind::Actor))
    {
        const bool selected = m_viewport.placementKind() == EditorSelectionKind::Actor;

        if (selected)
        {
            m_viewport.setPlacementKind(EditorSelectionKind::None);
        }
        else
        {
            if (session.selection().kind == EditorSelectionKind::Actor)
            {
                const Game::OutdoorSceneData &sceneData = session.document().outdoorSceneData();

                if (session.selection().index < sceneData.initialState.actors.size())
                {
                    session.setPendingActor(sceneData.initialState.actors[session.selection().index]);
                }
            }

            m_viewport.setPlacementKind(EditorSelectionKind::Actor);
        }
    }

    ImGui::SameLine();
    const bool selected = m_viewport.placementKind() == EditorSelectionKind::SpriteObject;
    if (renderIconTogglePill("PlaceObject", "Object", UiIcon::Object, selected))
    {
        if (selected)
        {
            m_viewport.setPlacementKind(EditorSelectionKind::None);
        }
        else
        {
            if (session.selection().kind == EditorSelectionKind::SpriteObject)
            {
                const Game::OutdoorSceneData &sceneData = session.document().outdoorSceneData();

                if (session.selection().index < sceneData.initialState.spriteObjects.size())
                {
                    session.setPendingSpriteObjectDescriptionId(
                        sceneData.initialState.spriteObjects[session.selection().index].objectDescriptionId);
                }
            }

            m_viewport.setPlacementKind(EditorSelectionKind::SpriteObject);
        }
    }
}

void EditorMainWindow::renderCreateButtons(EditorSession &session)
{
    if (session.hasDocument() && session.document().kind() == EditorDocument::Kind::Indoor)
    {
        const auto renderIndoorPlacementButton =
            [this](EditorSession &session, const char *pId, const char *pLabel, EditorSelectionKind kind)
        {
            const bool selected = m_viewport.placementKind() == kind;

            if (!renderIconTogglePill(pId, pLabel, selectionKindIcon(kind), selected))
            {
                return;
            }

            if (selected)
            {
                m_viewport.setPlacementKind(EditorSelectionKind::None);
                return;
            }

            const Game::IndoorSceneData &sceneData = session.document().indoorSceneData();

            if (kind == EditorSelectionKind::Actor
                && session.selection().kind == EditorSelectionKind::Actor
                && session.selection().index < sceneData.initialState.actors.size())
            {
                session.setPendingActor(sceneData.initialState.actors[session.selection().index]);
            }
            else if (kind == EditorSelectionKind::Entity
                && session.selection().kind == EditorSelectionKind::Entity
                && session.selection().index < session.document().indoorGeometry().entities.size())
            {
                session.setPendingEntityDecorationListId(
                    session.document().indoorGeometry().entities[session.selection().index].decorationListId);
            }
            else if (kind == EditorSelectionKind::Spawn
                && session.selection().kind == EditorSelectionKind::Spawn
                && session.selection().index < session.document().indoorGeometry().spawns.size())
            {
                const Game::IndoorSpawn &selectedSpawn =
                    session.document().indoorGeometry().spawns[session.selection().index];
                Game::OutdoorSpawn pendingSpawn = {};
                pendingSpawn.x = selectedSpawn.x;
                pendingSpawn.y = selectedSpawn.y;
                pendingSpawn.z = selectedSpawn.z;
                pendingSpawn.radius = selectedSpawn.radius;
                pendingSpawn.typeId = selectedSpawn.typeId;
                pendingSpawn.index = selectedSpawn.index;
                pendingSpawn.attributes = selectedSpawn.attributes;
                pendingSpawn.group = selectedSpawn.group;
                session.setPendingSpawn(pendingSpawn);
            }
            else if (kind == EditorSelectionKind::SpriteObject
                && session.selection().kind == EditorSelectionKind::SpriteObject
                && session.selection().index < sceneData.initialState.spriteObjects.size())
            {
                session.setPendingSpriteObjectDescriptionId(
                    sceneData.initialState.spriteObjects[session.selection().index].objectDescriptionId);
            }

            m_viewport.setPlacementKind(kind);
        };

        renderIndoorPlacementButton(session, "CreateIndoorDecoration", "Decoration", EditorSelectionKind::Entity);
        ImGui::SameLine();
        renderIndoorPlacementButton(session, "CreateIndoorActor", "Actor", EditorSelectionKind::Actor);
        ImGui::SameLine();
        renderIndoorPlacementButton(session, "CreateIndoorSpawn", "Spawn", EditorSelectionKind::Spawn);
        ImGui::SameLine();
        renderIndoorPlacementButton(session, "CreateIndoorObject", "Object", EditorSelectionKind::SpriteObject);
        ImGui::SameLine();

        if (renderTogglePill("Add Chest", false))
        {
            std::string errorMessage;

            if (!session.createOutdoorObject(EditorSelectionKind::Chest, 0, 0, 0, errorMessage))
            {
                session.logError(errorMessage);
            }
        }

        const bool canMutateIndoorSelection =
            session.selection().kind == EditorSelectionKind::Entity
            || session.selection().kind == EditorSelectionKind::Actor
            || session.selection().kind == EditorSelectionKind::Spawn
            || session.selection().kind == EditorSelectionKind::SpriteObject
            || session.selection().kind == EditorSelectionKind::Chest
            || session.selection().kind == EditorSelectionKind::Door;

        ImGui::BeginDisabled(!canMutateIndoorSelection);
        ImGui::SameLine();

        if (renderTogglePill("Duplicate", false))
        {
            duplicateSelected(session);
        }

        ImGui::SameLine();

        if (renderTogglePill("Delete", false))
        {
            deleteSelected(session);
        }

        ImGui::EndDisabled();
        return;
    }

    const auto renderPlacementButton =
        [this](EditorSession &session, const char *pId, const char *pLabel, EditorSelectionKind kind)
    {
        if (kind == EditorSelectionKind::Entity)
        {
            const bool selected = m_viewport.placementKind() == EditorSelectionKind::Entity;

            if (renderIconTogglePill(pId, pLabel, UiIcon::Entity, selected))
            {
                if (selected)
                {
                    m_viewport.setPlacementKind(EditorSelectionKind::None);
                }
                else
                {
                    if (session.selection().kind == EditorSelectionKind::Entity)
                    {
                        const Game::OutdoorSceneData &sceneData = session.document().outdoorSceneData();

                        if (session.selection().index < sceneData.entities.size())
                        {
                            session.setPendingEntityDecorationListId(
                                sceneData.entities[session.selection().index].entity.decorationListId);
                        }
                    }

                    m_viewport.setPlacementKind(EditorSelectionKind::Entity);
                }
            }

            return;
        }

        if (kind == EditorSelectionKind::SpriteObject)
        {
            const bool selected = m_viewport.placementKind() == EditorSelectionKind::SpriteObject;

            if (renderIconTogglePill(pId, pLabel, UiIcon::Object, selected))
            {
                if (selected)
                {
                    m_viewport.setPlacementKind(EditorSelectionKind::None);
                }
                else
                {
                    if (session.selection().kind == EditorSelectionKind::SpriteObject)
                    {
                        const Game::OutdoorSceneData &sceneData = session.document().outdoorSceneData();

                        if (session.selection().index < sceneData.initialState.spriteObjects.size())
                        {
                            session.setPendingSpriteObjectDescriptionId(
                                sceneData.initialState.spriteObjects[session.selection().index].objectDescriptionId);
                        }
                    }

                    m_viewport.setPlacementKind(EditorSelectionKind::SpriteObject);
                }
            }

            return;
        }

        const bool selected = m_viewport.placementKind() == kind;

        if (renderIconTogglePill(pId, pLabel, selectionKindIcon(kind), selected))
        {
            m_viewport.setPlacementKind(selected ? EditorSelectionKind::None : kind);
        }
    };

    renderPlacementButton(session, "CreateEntity", "Entity", EditorSelectionKind::Entity);
    ImGui::SameLine();
    renderPlacementButton(session, "CreateSpawn", "Spawn", EditorSelectionKind::Spawn);
    ImGui::SameLine();
    renderPlacementButton(session, "CreateActor", "Actor", EditorSelectionKind::Actor);
    ImGui::NewLine();
    renderPlacementButton(session, "CreateObject", "Object", EditorSelectionKind::SpriteObject);
    ImGui::SameLine();

    if (renderIconTogglePill("ImportBModel", "Import BModel", UiIcon::Face, false))
    {
        m_openImportNewBModelModal = true;
    }

    const bool canMutateSelection = isObjectLifecycleKind(session.selection().kind);

    ImGui::BeginDisabled(!canMutateSelection);
    ImGui::SameLine();
    if (renderTogglePill("Duplicate", false))
    {
        duplicateSelected(session);
    }

    ImGui::SameLine();

    if (renderTogglePill("Delete", false))
    {
        deleteSelected(session);
    }

    ImGui::EndDisabled();
}

const EditorMainWindow::ModelImportInspectionState &EditorMainWindow::ensureModelImportInspection(
    const char *pPath,
    ModelImportInspectionState &state) const
{
    const std::string pathText = trimCopy(pPath != nullptr ? pPath : "");

    if (state.cachedPath == pathText)
    {
        return state;
    }

    state.cachedPath = pathText;
    state.entries.clear();
    state.errorMessage.clear();

    if (pathText.empty())
    {
        return state;
    }

    std::vector<ImportedModel> models;

    if (!loadImportedModelsFromFile(std::filesystem::path(pathText), models, state.errorMessage))
    {
        return state;
    }

    state.entries.reserve(models.size());

    for (const ImportedModel &model : models)
    {
        state.entries.push_back(buildImportedModelInspectionEntry(model));
    }

    return state;
}

bool EditorMainWindow::renderImportedModelSelector(
    const char *pId,
    const ModelImportInspectionState &state,
    std::string &selectedModelName) const
{
    const std::string previewText =
        trimCopy(selectedModelName).empty() ? "<Merged Scene>" : selectedModelName;
    bool changed = false;

    if (ImGui::BeginCombo(pId, previewText.c_str()))
    {
        const bool mergedSelected = trimCopy(selectedModelName).empty();

        if (ImGui::Selectable("<Merged Scene>", mergedSelected))
        {
            selectedModelName.clear();
            changed = true;
        }

        if (mergedSelected)
        {
            ImGui::SetItemDefaultFocus();
        }

        for (const ModelImportInspectionState::Entry &entry : state.entries)
        {
            const bool selected = toLowerCopy(trimCopy(entry.name)) == toLowerCopy(trimCopy(selectedModelName));

            if (ImGui::Selectable(entry.name.c_str(), selected))
            {
                selectedModelName = entry.name;
                changed = true;
            }

            if (selected)
            {
                ImGui::SetItemDefaultFocus();
            }
        }

        ImGui::EndCombo();
    }

    return changed;
}

void EditorMainWindow::renderImportedModelInspectionTable(
    const char *pId,
    const ModelImportInspectionState &state,
    std::string &selectedModelName,
    float height) const
{
    if (state.entries.empty())
    {
        return;
    }

    if (!ImGui::BeginChild(pId, ImVec2(0.0f, height), ImGuiChildFlags_Borders))
    {
        ImGui::EndChild();
        return;
    }

    ImGui::PushID(pId);

    if (ImGui::BeginTable(
            "ImportedModelInspectionTable",
            4,
            ImGuiTableFlags_SizingStretchProp | ImGuiTableFlags_RowBg | ImGuiTableFlags_ScrollY))
    {
        ImGui::TableSetupColumn("Mesh", ImGuiTableColumnFlags_WidthStretch, 0.48f);
        ImGui::TableSetupColumn("Verts", ImGuiTableColumnFlags_WidthStretch, 0.17f);
        ImGui::TableSetupColumn("Faces", ImGuiTableColumnFlags_WidthStretch, 0.17f);
        ImGui::TableSetupColumn("Mats", ImGuiTableColumnFlags_WidthStretch, 0.18f);
        ImGui::TableHeadersRow();

        for (const ModelImportInspectionState::Entry &entry : state.entries)
        {
            const bool selected = toLowerCopy(trimCopy(entry.name)) == toLowerCopy(trimCopy(selectedModelName));
            ImGui::TableNextRow();
            ImGui::TableSetColumnIndex(0);

            if (ImGui::Selectable(entry.name.c_str(), selected, ImGuiSelectableFlags_SpanAllColumns))
            {
                selectedModelName = entry.name;
            }

            ImGui::TableSetColumnIndex(1);
            ImGui::Text("%zu", entry.vertexCount);
            ImGui::TableSetColumnIndex(2);
            ImGui::Text("%zu", entry.faceCount);
            ImGui::TableSetColumnIndex(3);
            ImGui::Text("%zu", entry.materialCount);
        }

        ImGui::EndTable();
    }

    ImGui::PopID();
    ImGui::EndChild();
}

void EditorMainWindow::renderImportedModelInspectionSummary(
    const ModelImportInspectionState &state,
    const std::string &selectedModelName) const
{
    std::optional<ModelImportInspectionState::Entry> mergedEntry;
    const ModelImportInspectionState::Entry *pEntry = findImportedModelInspectionEntry(state, selectedModelName);

    if (pEntry == nullptr)
    {
        mergedEntry = mergedImportedModelInspectionEntry(state);
        pEntry = mergedEntry ? &*mergedEntry : nullptr;
    }

    if (pEntry == nullptr)
    {
        return;
    }

    ImGui::TextDisabled("Preview Target");
    ImGui::PushID(pEntry->name.c_str());

    if (beginInspectorPropertyTable("ImportedModelInspectionSummary"))
    {
        renderInspectorReadOnlyField("Name", pEntry->name);
        renderInspectorReadOnlyField("Vertices", std::to_string(pEntry->vertexCount));
        renderInspectorReadOnlyField("Faces", std::to_string(pEntry->faceCount));
        renderInspectorReadOnlyField("Materials", std::to_string(pEntry->materialCount));
        renderInspectorReadOnlyField(
            "Bounds Min",
            std::to_string(static_cast<int>(std::floor(pEntry->minX))) + ", "
                + std::to_string(static_cast<int>(std::floor(pEntry->minY))) + ", "
                + std::to_string(static_cast<int>(std::floor(pEntry->minZ))));
        renderInspectorReadOnlyField(
            "Bounds Max",
            std::to_string(static_cast<int>(std::ceil(pEntry->maxX))) + ", "
                + std::to_string(static_cast<int>(std::ceil(pEntry->maxY))) + ", "
                + std::to_string(static_cast<int>(std::ceil(pEntry->maxZ))));
        renderInspectorReadOnlyField(
            "Size",
            std::to_string(static_cast<int>(std::ceil(pEntry->maxX - pEntry->minX))) + " x "
                + std::to_string(static_cast<int>(std::ceil(pEntry->maxY - pEntry->minY))) + " x "
                + std::to_string(static_cast<int>(std::ceil(pEntry->maxZ - pEntry->minZ))));
        ImGui::EndTable();
    }

    ImGui::PopID();
}

void EditorMainWindow::renderModelImportModal(EditorSession &session)
{
    if (m_openImportNewBModelModal)
    {
        m_showImportNewBModelWindow = true;
        m_openImportNewBModelModal = false;
    }

    if (!m_showImportNewBModelWindow)
    {
        return;
    }

    const ImGuiViewport *pViewport = ImGui::GetMainViewport();
    ImGui::SetNextWindowPos(
        ImVec2(
            pViewport->WorkPos.x + pViewport->WorkSize.x * 0.5f,
            pViewport->WorkPos.y + pViewport->WorkSize.y * 0.5f),
        ImGuiCond_Appearing,
        ImVec2(0.5f, 0.5f));
    ImGui::SetNextWindowSize(ImVec2(900.0f, 0.0f), ImGuiCond_FirstUseEver);
    bool keepImportWindowOpen = m_showImportNewBModelWindow;

    if (!ImGui::Begin(
            "Import New BModel",
            &keepImportWindowOpen,
            ImGuiWindowFlags_NoDocking | ImGuiWindowFlags_NoCollapse | ImGuiWindowFlags_AlwaysAutoResize))
    {
        ImGui::End();
        m_showImportNewBModelWindow = keepImportWindowOpen;
        return;
    }

    m_showImportNewBModelWindow = keepImportWindowOpen;

    if (m_closeImportNewBModelModal)
    {
        m_closeImportNewBModelModal = false;
        m_showImportNewBModelWindow = false;
        ImGui::End();
        return;
    }

    ImGui::TextUnformatted("Import a new outdoor bmodel from an OBJ, glTF, or GLB file.");
    ImGui::Separator();
    const bool canSplitByMesh = canSplitImportedModelPathByMesh(m_globalBModelImportPath);
    const ModelImportInspectionState &inspection =
        ensureModelImportInspection(m_globalBModelImportPath, m_globalBModelImportInspection);

    if (!trimCopy(m_globalBModelImportSelectedMeshName).empty())
    {
        bool foundSelectedMesh = false;

        for (const ModelImportInspectionState::Entry &entry : inspection.entries)
        {
            if (toLowerCopy(trimCopy(entry.name)) == toLowerCopy(trimCopy(m_globalBModelImportSelectedMeshName)))
            {
                foundSelectedMesh = true;
                break;
            }
        }

        if (!foundSelectedMesh)
        {
            m_globalBModelImportSelectedMeshName.clear();
        }
    }

    if (beginInspectorPropertyTable("ImportNewBModelFields"))
    {
        beginInspectorFieldRow("Model Path");
        const float browseButtonWidth = 30.0f;
        ImGui::SetNextItemWidth(-browseButtonWidth - ImGui::GetStyle().ItemSpacing.x);
        ImGui::InputText("##GlobalBModelImportPath", m_globalBModelImportPath, sizeof(m_globalBModelImportPath));
        ImGui::SameLine();

        if (ImGui::Button("...", ImVec2(browseButtonWidth, 0.0f)))
        {
            openModelFileBrowser(ModelImportTarget::ImportNewBModel, m_globalBModelImportPath);
        }

        beginInspectorFieldRow("Import Scale");
        ImGui::InputFloat("##GlobalBModelImportScale", &m_globalBModelImportScale, 0.1f, 1.0f, "%.3f");

        std::string defaultTextureName = m_globalBModelImportDefaultTexture;
        const bool texturePickerChanged =
            renderBitmapTextureSelector(session, "Default Texture (Optional)", defaultTextureName);

        beginInspectorFieldRow("Default Texture Raw");
        char defaultTextureBuffer[64] = {};
        std::snprintf(defaultTextureBuffer, sizeof(defaultTextureBuffer), "%s", defaultTextureName.c_str());
        const bool rawTextureChanged = ImGui::InputText(
            "##GlobalBModelImportDefaultTextureRaw",
            defaultTextureBuffer,
            sizeof(defaultTextureBuffer));

        if (rawTextureChanged)
        {
            defaultTextureName = defaultTextureBuffer;
        }

        if (texturePickerChanged || rawTextureChanged)
        {
            std::snprintf(
                m_globalBModelImportDefaultTexture,
                sizeof(m_globalBModelImportDefaultTexture),
                "%s",
                defaultTextureName.c_str());
        }

        beginInspectorFieldRow("Split Meshes");
        ImGui::BeginDisabled(!canSplitByMesh);
        ImGui::Checkbox("##GlobalBModelImportSplitByMesh", &m_globalBModelImportSplitByMesh);
        ImGui::EndDisabled();

        beginInspectorFieldRow("Merge Coplanar");
        ImGui::Checkbox("##GlobalBModelImportMergeCoplanarFaces", &m_globalBModelImportMergeCoplanarFaces);

        if (canSplitByMesh)
        {
            beginInspectorFieldRow("Source Mesh");
            ImGui::BeginDisabled(m_globalBModelImportSplitByMesh || inspection.entries.empty());
            renderImportedModelSelector(
                "##GlobalBModelImportSourceMesh",
                inspection,
                m_globalBModelImportSelectedMeshName);
            ImGui::EndDisabled();
        }

        ImGui::EndTable();
    }

    if (canSplitByMesh)
    {
        if (!inspection.errorMessage.empty())
        {
            ImGui::TextColored(colorFromRgb(0xE7A46C), "%s", inspection.errorMessage.c_str());
        }
        else
        {
            ImGui::TextDisabled("%s", importedModelSummaryText(inspection.entries.size()).c_str());

            if (!inspection.entries.empty())
            {
                renderImportedModelInspectionTable(
                    "GlobalModelImportMeshes",
                    inspection,
                    m_globalBModelImportSelectedMeshName,
                    110.0f);
                renderImportedModelInspectionSummary(inspection, m_globalBModelImportSelectedMeshName);
            }
        }
    }

    if (ImGui::Button("Import", ImVec2(120.0f, 0.0f)))
    {
        std::string errorMessage;
        const std::string sourceMeshName =
            canSplitByMesh ? m_globalBModelImportSelectedMeshName : std::string();

        if (session.importNewBModelFromModel(
                m_globalBModelImportPath,
                m_globalBModelImportScale,
                m_globalBModelImportDefaultTexture,
                sourceMeshName,
                m_globalBModelImportSplitByMesh,
                m_globalBModelImportMergeCoplanarFaces,
                errorMessage))
        {
            rememberModelImportDirectory(m_globalBModelImportPath);
            m_viewport.setPlacementKind(EditorSelectionKind::BModel);
            m_showImportNewBModelWindow = false;
            m_showModelBrowserWindow = false;
        }
        else
        {
            session.logError(errorMessage);
        }
    }

    ImGui::SameLine();

    if (ImGui::Button("Cancel", ImVec2(120.0f, 0.0f)))
    {
        m_showImportNewBModelWindow = false;
        m_showModelBrowserWindow = false;
    }

    ImGui::End();
}

void EditorMainWindow::openModelFileBrowser(ModelImportTarget target, const char *pCurrentPath) const
{
    m_modelBrowserTarget = target;
    m_modelBrowserFilter[0] = '\0';
    const std::string currentPath = trimCopy(pCurrentPath != nullptr ? pCurrentPath : "");

    if (!currentPath.empty())
    {
        const std::filesystem::path path = std::filesystem::path(currentPath);
        const std::filesystem::path directory = std::filesystem::is_directory(path) ? path : path.parent_path();

        if (!directory.empty() && std::filesystem::exists(directory))
        {
            m_modelBrowserDirectory = directory;
        }
    }

    if (m_modelBrowserDirectory.empty() || !std::filesystem::exists(m_modelBrowserDirectory))
    {
        m_modelBrowserDirectory = std::filesystem::current_path();
    }

    m_openModelBrowserPopup = true;
}

void EditorMainWindow::assignModelBrowserSelectionPath(const std::filesystem::path &path) const
{
    const std::string normalizedPath = path.lexically_normal().string();

    if (m_modelBrowserTarget == ModelImportTarget::ReplaceSelectedBModel)
    {
        std::snprintf(m_bmodelImportPath, sizeof(m_bmodelImportPath), "%s", normalizedPath.c_str());
    }
    else if (m_modelBrowserTarget == ModelImportTarget::ImportNewBModel)
    {
        std::snprintf(m_globalBModelImportPath, sizeof(m_globalBModelImportPath), "%s", normalizedPath.c_str());
    }
    else if (m_modelBrowserTarget == ModelImportTarget::ImportIndoorSourceGeometry)
    {
        std::snprintf(
            m_indoorSourceGeometryImportPath,
            sizeof(m_indoorSourceGeometryImportPath),
            "%s",
            normalizedPath.c_str());
    }

    rememberModelImportDirectory(normalizedPath.c_str());
}

void EditorMainWindow::rememberModelImportDirectory(const char *pPath) const
{
    const std::string pathText = trimCopy(pPath != nullptr ? pPath : "");

    if (pathText.empty())
    {
        return;
    }

    const std::filesystem::path path(pathText);
    const std::filesystem::path directory = std::filesystem::is_directory(path) ? path : path.parent_path();

    if (!directory.empty() && std::filesystem::exists(directory))
    {
        m_modelBrowserDirectory = directory;
    }
}

void EditorMainWindow::openNewOutdoorMapModal(EditorSession &session)
{
    std::string suggestedMapId = "out16";

    if (const Engine::AssetFileSystem *pAssetFileSystem = session.assetFileSystem())
    {
        const std::vector<std::string> entries = pAssetFileSystem->enumerate("Data/games");
        std::unordered_set<std::string> existingIds;

        for (const std::string &entry : entries)
        {
            if (entry.ends_with(".map.yml"))
            {
                existingIds.insert(toLowerCopy(std::filesystem::path(entry).stem().stem().string()));
            }
            else if (entry.ends_with(".scene.yml"))
            {
                existingIds.insert(toLowerCopy(std::filesystem::path(entry).stem().stem().string()));
            }
            else if (entry.ends_with(".odm"))
            {
                existingIds.insert(toLowerCopy(std::filesystem::path(entry).stem().string()));
            }
        }

        for (int index = 1; index < 1000; ++index)
        {
            char candidate[32] = {};
            std::snprintf(candidate, sizeof(candidate), "out%02d", index);

            if (!existingIds.contains(candidate))
            {
                suggestedMapId = candidate;
                break;
            }
        }
    }

    std::snprintf(m_newOutdoorMapId, sizeof(m_newOutdoorMapId), "%s", suggestedMapId.c_str());
    std::snprintf(m_newOutdoorDisplayName, sizeof(m_newOutdoorDisplayName), "%s", suggestedMapId.c_str());
    m_newOutdoorMapSizePreset = 0;
    m_newOutdoorTilesetPreset = static_cast<int>(EditorOutdoorMapTilesetPreset::Grassland);
    m_openNewOutdoorMapModal = true;
    m_closeNewOutdoorMapModal = false;
}

void EditorMainWindow::openOpenOutdoorMapModal() const
{
    m_openOutdoorMapFilter[0] = '\0';
    m_openMapSelectedRelativePath.clear();
    m_openOpenOutdoorMapModal = true;
}

void EditorMainWindow::openMapPackageActionModal(EditorSession &session, MapPackageAction action) const
{
    m_mapPackageAction = action;
    std::string suggestedMapId = "out16";
    std::string suggestedDisplayName = "out16";

    if (const Engine::AssetFileSystem *pAssetFileSystem = session.assetFileSystem())
    {
        const std::string currentMapId =
            session.hasDocument() ? std::filesystem::path(session.document().displayName()).stem().string() : "out16";
        suggestedMapId = suggestAvailableMapId(*pAssetFileSystem, currentMapId + "_copy");
        suggestedDisplayName = session.hasDocument()
            ? session.document().outdoorMapPackageMetadata().displayName
            : suggestedMapId;
    }

    std::snprintf(m_mapPackageActionMapId, sizeof(m_mapPackageActionMapId), "%s", suggestedMapId.c_str());
    std::snprintf(
        m_mapPackageActionDisplayName,
        sizeof(m_mapPackageActionDisplayName),
        "%s",
        suggestedDisplayName.c_str());
    m_openMapPackageActionModal = true;
}

void EditorMainWindow::openDeleteCurrentMapModal() const
{
    m_openDeleteCurrentMapModal = true;
}

void EditorMainWindow::renderNewOutdoorMapModal(EditorSession &session)
{
    if (m_openNewOutdoorMapModal)
    {
        ImGui::OpenPopup("New Outdoor Map");
        m_openNewOutdoorMapModal = false;
    }

    if (!ImGui::BeginPopupModal("New Outdoor Map", nullptr, ImGuiWindowFlags_AlwaysAutoResize))
    {
        return;
    }

    if (m_closeNewOutdoorMapModal)
    {
        m_closeNewOutdoorMapModal = false;
        ImGui::CloseCurrentPopup();
        ImGui::EndPopup();
        return;
    }

    ImGui::TextUnformatted("Create a new source-native outdoor map package.");
    ImGui::Separator();

    if (beginInspectorPropertyTable("NewOutdoorMapFields"))
    {
        beginInspectorFieldRow("Map Id");
        ImGui::InputText("##NewOutdoorMapId", m_newOutdoorMapId, sizeof(m_newOutdoorMapId));

        beginInspectorFieldRow("Display Name");
        ImGui::InputText("##NewOutdoorDisplayName", m_newOutdoorDisplayName, sizeof(m_newOutdoorDisplayName));

        beginInspectorFieldRow("Map Size");
        const char *sizeLabel = "Classic 128x128";
        ImGui::SetNextItemWidth(220.0f);
        ImGui::Combo("##NewOutdoorMapSize", &m_newOutdoorMapSizePreset, &sizeLabel, 1);

        beginInspectorFieldRow("Tileset");
        const char *tilesetPreview = outdoorTilesetPresetLabel(
            static_cast<EditorOutdoorMapTilesetPreset>(m_newOutdoorTilesetPreset));

        if (ImGui::BeginCombo("##NewOutdoorTilesetPreset", tilesetPreview))
        {
            for (int presetIndex = 0; presetIndex < 3; ++presetIndex)
            {
                const EditorOutdoorMapTilesetPreset preset = static_cast<EditorOutdoorMapTilesetPreset>(presetIndex);
                const bool selected = presetIndex == m_newOutdoorTilesetPreset;

                if (ImGui::Selectable(outdoorTilesetPresetLabel(preset), selected))
                {
                    m_newOutdoorTilesetPreset = presetIndex;
                }

                if (selected)
                {
                    ImGui::SetItemDefaultFocus();
                }
            }

            ImGui::EndCombo();
        }

        ImGui::EndTable();
    }

    ImGui::TextDisabled("Creates .map.yml, .scene.yml, .geometry.yml, .terrain.yml, and a compiled ODM.");

    if (ImGui::Button("Create", ImVec2(120.0f, 0.0f)))
    {
        std::string errorMessage;

        if (session.createNewOutdoorMap(
                m_newOutdoorMapId,
                m_newOutdoorDisplayName,
                static_cast<EditorOutdoorMapTilesetPreset>(m_newOutdoorTilesetPreset),
                errorMessage))
        {
            setStatusMessage(StatusMessageKind::Success, "Created new outdoor map.");
            m_closeNewOutdoorMapModal = true;
        }
        else
        {
            session.logError(errorMessage);
            setStatusMessage(StatusMessageKind::Error, errorMessage);
        }
    }

    ImGui::SameLine();

    if (ImGui::Button("Cancel", ImVec2(120.0f, 0.0f)))
    {
        ImGui::CloseCurrentPopup();
    }

    ImGui::EndPopup();
}

void EditorMainWindow::renderOpenOutdoorMapModal(EditorSession &session)
{
    if (m_openOpenOutdoorMapModal)
    {
        ImGui::OpenPopup("Open Map");
        m_openOpenOutdoorMapModal = false;
    }

    if (!ImGui::BeginPopupModal("Open Map", nullptr, ImGuiWindowFlags_AlwaysAutoResize))
    {
        return;
    }

    const Engine::AssetFileSystem *pAssetFileSystem = session.assetFileSystem();

    if (pAssetFileSystem == nullptr)
    {
        ImGui::TextUnformatted("Asset file system is not initialized.");

        if (ImGui::Button("Close", ImVec2(120.0f, 0.0f)))
        {
            ImGui::CloseCurrentPopup();
        }

        ImGui::EndPopup();
        return;
    }

    const std::filesystem::path editorWorldsRoot = pAssetFileSystem->getEditorDevelopmentRoot() / "worlds";

    if (m_openMapBrowserDirectory.empty() || !std::filesystem::exists(m_openMapBrowserDirectory))
    {
        m_openMapBrowserDirectory = std::filesystem::exists(editorWorldsRoot)
            ? editorWorldsRoot
            : std::filesystem::current_path();
    }

    std::error_code pathError;
    const std::filesystem::path normalizedDirectory =
        std::filesystem::weakly_canonical(std::filesystem::absolute(m_openMapBrowserDirectory), pathError);

    if (!pathError && !normalizedDirectory.empty())
    {
        m_openMapBrowserDirectory = normalizedDirectory;
    }

    auto openSelectedMap = [&](const std::string &selectedPath) -> bool
    {
        if (selectedPath.empty())
        {
            return false;
        }

        std::string errorMessage;
        const bool opened = session.openMapPhysicalPath(selectedPath, errorMessage);

        if (!opened)
        {
            session.logError(errorMessage);
            setStatusMessage(StatusMessageKind::Error, errorMessage);
            return false;
        }

        const std::filesystem::path openedPath(selectedPath);
        m_lastLoadedMapPath = openedPath;
        m_openMapBrowserDirectory = openedPath.parent_path();
        setStatusMessage(StatusMessageKind::Success, "Opened " + selectedPath + ".");
        ImGui::CloseCurrentPopup();
        return true;
    };

    ImGui::TextUnformatted("Open an authored scene package or MM9 DAT level.");
    ImGui::Separator();
    ImGui::TextWrapped("Directory: %s", m_openMapBrowserDirectory.generic_string().c_str());

    if (ImGui::Button("Up", ImVec2(80.0f, 0.0f)))
    {
        const std::filesystem::path parentPath = m_openMapBrowserDirectory.parent_path();

        if (!parentPath.empty() && parentPath != m_openMapBrowserDirectory)
        {
            m_openMapBrowserDirectory = parentPath;
            m_openMapSelectedRelativePath.clear();
        }
    }

    ImGui::SameLine();

    if (ImGui::Button("Root", ImVec2(80.0f, 0.0f)))
    {
        m_openMapBrowserDirectory = std::filesystem::exists(editorWorldsRoot)
            ? editorWorldsRoot
            : std::filesystem::absolute(m_openMapBrowserDirectory).root_path();
        m_openMapSelectedRelativePath.clear();
    }

    ImGui::SameLine();
    ImGui::SetNextItemWidth(360.0f);
    ImGui::InputTextWithHint("##OpenOutdoorMapFilter", "Filter maps", m_openOutdoorMapFilter, sizeof(m_openOutdoorMapFilter));
    const std::string filter = toLowerCopy(trimCopy(m_openOutdoorMapFilter));
    const std::vector<std::filesystem::path> childDirectories = collectChildDirectories(m_openMapBrowserDirectory);
    const std::vector<OpenableMapEntry> mapFiles = collectOpenableMapEntries(m_openMapBrowserDirectory);

    if (ImGui::BeginChild("OpenOutdoorMapList", ImVec2(640.0f, 360.0f), ImGuiChildFlags_Borders))
    {
        bool anyVisible = false;

        for (const std::filesystem::path &directoryPath : childDirectories)
        {
            const std::string fileName = directoryPath.filename().string();

            if (!filter.empty() && toLowerCopy(fileName).find(filter) == std::string::npos)
            {
                continue;
            }

            anyVisible = true;
            const std::string label = "[DIR] " + fileName;

            if (ImGui::Selectable(label.c_str(), false))
            {
                m_openMapBrowserDirectory = directoryPath;
                m_openMapSelectedRelativePath.clear();
            }
        }

        for (const OpenableMapEntry &mapEntry : mapFiles)
        {
            const std::string fileName = mapEntry.physicalPath.filename().string();
            const std::string visibleLabel = "[" + mapEntry.kindLabel + "] " + fileName;

            if (!filter.empty() && toLowerCopy(visibleLabel).find(filter) == std::string::npos)
            {
                continue;
            }

            anyVisible = true;
            const bool selected =
                toLowerCopy(m_openMapSelectedRelativePath) == toLowerCopy(mapEntry.physicalPath.generic_string());

            if (ImGui::Selectable(visibleLabel.c_str(), selected))
            {
                m_openMapSelectedRelativePath = mapEntry.physicalPath.generic_string();

                if (ImGui::IsMouseDoubleClicked(ImGuiMouseButton_Left))
                {
                    if (openSelectedMap(mapEntry.physicalPath.generic_string()))
                    {
                        ImGui::EndChild();
                        ImGui::EndPopup();
                        return;
                    }
                }
            }
        }

        if (!anyVisible)
        {
            ImGui::TextUnformatted("No folders or maps match the current filter.");
        }
    }
    ImGui::EndChild();

    const bool hasSelection = !m_openMapSelectedRelativePath.empty();

    if (!hasSelection)
    {
        ImGui::BeginDisabled();
    }

    if (ImGui::Button("Open", ImVec2(120.0f, 0.0f)))
    {
        openSelectedMap(m_openMapSelectedRelativePath);
    }

    if (!hasSelection)
    {
        ImGui::EndDisabled();
    }

    if (hasSelection)
    {
        ImGui::SameLine();
        ImGui::TextWrapped("%s", m_openMapSelectedRelativePath.c_str());
    }

    ImGui::SameLine();

    if (ImGui::Button("Close", ImVec2(120.0f, 0.0f)))
    {
        ImGui::CloseCurrentPopup();
    }

    ImGui::EndPopup();
}

void EditorMainWindow::renderMapPackageActionModal(EditorSession &session)
{
    if (m_openMapPackageActionModal)
    {
        ImGui::OpenPopup("Map Package Action");
        m_openMapPackageActionModal = false;
    }

    if (!ImGui::BeginPopupModal("Map Package Action", nullptr, ImGuiWindowFlags_AlwaysAutoResize))
    {
        return;
    }

    const char *pTitle =
        m_mapPackageAction == MapPackageAction::Duplicate ? "Duplicate current outdoor map package." : "Save current outdoor map to a new package.";
    ImGui::TextUnformatted(pTitle);
    ImGui::Separator();

    if (beginInspectorPropertyTable("MapPackageActionFields"))
    {
        beginInspectorFieldRow("Map Id");
        ImGui::InputText("##MapPackageActionMapId", m_mapPackageActionMapId, sizeof(m_mapPackageActionMapId));

        beginInspectorFieldRow("Display Name");
        ImGui::InputText(
            "##MapPackageActionDisplayName",
            m_mapPackageActionDisplayName,
            sizeof(m_mapPackageActionDisplayName));

        ImGui::EndTable();
    }

    const char *pConfirmLabel = m_mapPackageAction == MapPackageAction::Duplicate ? "Duplicate" : "Save As";

    if (ImGui::Button(pConfirmLabel, ImVec2(120.0f, 0.0f)))
    {
        std::string errorMessage;
        bool succeeded = false;

        if (m_mapPackageAction == MapPackageAction::Duplicate)
        {
            succeeded = session.duplicateActiveDocumentAs(
                m_mapPackageActionMapId,
                m_mapPackageActionDisplayName,
                errorMessage);
        }
        else
        {
            succeeded = session.saveActiveDocumentAs(
                m_mapPackageActionMapId,
                m_mapPackageActionDisplayName,
                errorMessage);
        }

        if (succeeded)
        {
            setStatusMessage(
                StatusMessageKind::Success,
                std::string(pConfirmLabel) + " complete: " + session.document().displayName());
            ImGui::CloseCurrentPopup();
        }
        else
        {
            session.logError(errorMessage);
            setStatusMessage(StatusMessageKind::Error, errorMessage);
        }
    }

    ImGui::SameLine();

    if (ImGui::Button("Cancel", ImVec2(120.0f, 0.0f)))
    {
        ImGui::CloseCurrentPopup();
    }

    ImGui::EndPopup();
}

void EditorMainWindow::renderDeleteCurrentMapModal(EditorSession &session)
{
    if (m_openDeleteCurrentMapModal)
    {
        ImGui::OpenPopup("Delete Current Map");
        m_openDeleteCurrentMapModal = false;
    }

    if (!ImGui::BeginPopupModal("Delete Current Map", nullptr, ImGuiWindowFlags_AlwaysAutoResize))
    {
        return;
    }

    if (!session.hasDocument())
    {
        ImGui::TextUnformatted("No map is currently open.");
    }
    else
    {
        const EditorDocument &document = session.document();
        ImGui::Text("Delete current map package '%s'?", document.displayName().c_str());
        ImGui::TextWrapped("This removes the current map files from Data/games and then opens another map.");
        ImGui::Separator();
        ImGui::Text("Runtime: %s", document.geometryPhysicalPath().filename().string().c_str());
        ImGui::Text("Scene: %s", document.scenePhysicalPath().filename().string().c_str());
        ImGui::Text("Package: %s", document.mapPackagePhysicalPath().filename().string().c_str());
        ImGui::Text("Geometry: %s", document.geometryMetadataPhysicalPath().filename().string().c_str());
        ImGui::Text("Terrain: %s", document.terrainMetadataPhysicalPath().filename().string().c_str());
    }

    if (ImGui::Button("Delete", ImVec2(120.0f, 0.0f)))
    {
        std::string errorMessage;

        if (session.deleteActiveDocumentPackage(errorMessage))
        {
            setStatusMessage(StatusMessageKind::Success, "Deleted current map package.");
            ImGui::CloseCurrentPopup();
        }
        else
        {
            session.logError(errorMessage);
            setStatusMessage(StatusMessageKind::Error, errorMessage);
        }
    }

    ImGui::SameLine();

    if (ImGui::Button("Cancel", ImVec2(120.0f, 0.0f)))
    {
        ImGui::CloseCurrentPopup();
    }

    ImGui::EndPopup();
}

void EditorMainWindow::renderModelFileBrowserPopup(EditorSession &session)
{
    if (m_openModelBrowserPopup)
    {
        m_showModelBrowserWindow = true;
        m_openModelBrowserPopup = false;
        ImGui::SetNextWindowFocus();
    }

    if (!m_showModelBrowserWindow)
    {
        return;
    }

    const ImGuiViewport *pViewport = ImGui::GetMainViewport();
    ImGui::SetNextWindowPos(
        ImVec2(
            pViewport->WorkPos.x + pViewport->WorkSize.x * 0.5f,
            pViewport->WorkPos.y + pViewport->WorkSize.y * 0.5f),
        ImGuiCond_Appearing,
        ImVec2(0.5f, 0.5f));
    ImGui::SetNextWindowSize(ImVec2(820.0f, 520.0f), ImGuiCond_FirstUseEver);
    bool keepBrowserWindowOpen = m_showModelBrowserWindow;

    if (!ImGui::Begin(
            "Model Browser",
            &keepBrowserWindowOpen,
            ImGuiWindowFlags_NoDocking | ImGuiWindowFlags_NoCollapse | ImGuiWindowFlags_AlwaysAutoResize))
    {
        ImGui::End();
        m_showModelBrowserWindow = keepBrowserWindowOpen;
        return;
    }

    m_showModelBrowserWindow = keepBrowserWindowOpen;

    if (m_modelBrowserDirectory.empty() || !std::filesystem::exists(m_modelBrowserDirectory))
    {
        m_modelBrowserDirectory = std::filesystem::current_path();
    }

    ImGui::TextWrapped("Directory: %s", m_modelBrowserDirectory.string().c_str());
    ImGui::InputText("Filter", m_modelBrowserFilter, sizeof(m_modelBrowserFilter));

    if (ImGui::Button("Up", ImVec2(90.0f, 0.0f)))
    {
        if (m_modelBrowserDirectory.has_parent_path())
        {
            m_modelBrowserDirectory = m_modelBrowserDirectory.parent_path();
        }
    }

    ImGui::SameLine();

    if (ImGui::Button("Refresh", ImVec2(90.0f, 0.0f)))
    {
    }

    std::vector<std::filesystem::path> directories;
    std::vector<std::filesystem::path> modelFiles;
    const std::string normalizedFilter = toLowerCopy(trimCopy(m_modelBrowserFilter));

    try
    {
        for (const std::filesystem::directory_entry &entry :
             std::filesystem::directory_iterator(m_modelBrowserDirectory))
        {
            const std::filesystem::path path = entry.path();
            const std::string fileName = path.filename().string();

            if (entry.is_directory())
            {
                if (!normalizedFilter.empty() && toLowerCopy(fileName).find(normalizedFilter) == std::string::npos)
                {
                    continue;
                }

                directories.push_back(path);
            }
            else
            {
                const std::string extension = toLowerCopy(path.extension().string());

                if (extension != ".obj" && extension != ".gltf" && extension != ".glb")
                {
                    continue;
                }

                std::error_code existsError;

                if (!std::filesystem::exists(path, existsError) || std::filesystem::is_directory(path, existsError))
                {
                    continue;
                }

                if (!normalizedFilter.empty() && toLowerCopy(fileName).find(normalizedFilter) == std::string::npos)
                {
                    continue;
                }

                modelFiles.push_back(path);
            }
        }
    }
    catch (const std::filesystem::filesystem_error &)
    {
    }

    std::sort(directories.begin(), directories.end());
    std::sort(modelFiles.begin(), modelFiles.end());

    if (ImGui::BeginChild("ModelBrowserEntries", ImVec2(760.0f, 420.0f), ImGuiChildFlags_Borders))
    {
        for (const std::filesystem::path &path : directories)
        {
            const std::string label = "[DIR] " + path.filename().string();

            if (ImGui::Selectable(label.c_str(), false))
            {
                m_modelBrowserDirectory = path;
            }
        }

        for (const std::filesystem::path &path : modelFiles)
        {
            const std::string label = path.filename().string();

            if (ImGui::Selectable(label.c_str(), false))
            {
                assignModelBrowserSelectionPath(path);
                m_showModelBrowserWindow = false;
            }
        }
    }

    ImGui::EndChild();

    if (ImGui::Button("Cancel", ImVec2(120.0f, 0.0f)))
    {
        m_showModelBrowserWindow = false;
    }

    ImGui::End();
}

void EditorMainWindow::duplicateSelected(EditorSession &session)
{
    std::string errorMessage;
    const EditorSelectionKind duplicatedKind = session.selection().kind;

    if (!session.duplicateSelectedObject(errorMessage))
    {
        session.logError(errorMessage);
        return;
    }

    if (duplicatedKind == EditorSelectionKind::BModel)
    {
        m_viewport.setPlacementKind(EditorSelectionKind::BModel);
    }
}

void EditorMainWindow::deleteSelected(EditorSession &session)
{
    std::string errorMessage;

    if (!session.deleteSelectedObject(errorMessage))
    {
        session.logError(errorMessage);
        return;
    }

    if (session.selection().kind != EditorSelectionKind::BModel && m_viewport.placementKind() == EditorSelectionKind::BModel)
    {
        m_viewport.setPlacementKind(EditorSelectionKind::None);
    }
}

void EditorMainWindow::renderSceneOutliner(EditorSession &session)
{
    ImGui::SetNextWindowDockID(editorDockspaceId(), ImGuiCond_FirstUseEver);

    if (!ImGui::Begin("Scene"))
    {
        ImGui::End();
        return;
    }

    if (!session.hasDocument())
    {
        ImGui::TextUnformatted("No document loaded.");
        ImGui::End();
        return;
    }

    if (session.document().kind() == EditorDocument::Kind::Indoor)
    {
        const Game::IndoorMapData &indoorGeometry = session.document().indoorGeometry();
        const Game::IndoorSceneData &sceneData = session.document().indoorSceneData();
        Game::IndoorFaceGeometryCache roomLookupCache(indoorGeometry.faces.size());

        if (m_indoorSceneRoomFilter >= static_cast<int>(indoorGeometry.sectors.size()))
        {
            m_indoorSceneRoomFilter = -1;
        }

        const auto focusOutlinerSelection = [this, &session](EditorSelectionKind kind, size_t index)
        {
            if (ImGui::IsItemHovered() && ImGui::IsMouseDoubleClicked(ImGuiMouseButton_Left))
            {
                session.select(kind, index);
                m_viewport.focusSelection(session.document(), {kind, index});
            }
        };
        const auto selectRoomFaces = [&session, &indoorGeometry](uint16_t roomId)
        {
            const std::vector<uint16_t> roomFaceIds = indoorSectorFaceIds(indoorGeometry, roomId);

            if (roomFaceIds.empty())
            {
                return;
            }

            session.replaceInteractiveFaceSelection(roomFaceIds.front());

            for (size_t roomFaceIndex = 1; roomFaceIndex < roomFaceIds.size(); ++roomFaceIndex)
            {
                session.addInteractiveFaceSelection(roomFaceIds[roomFaceIndex]);
            }
        };

        ImGui::PushStyleColor(ImGuiCol_Header, colorFromRgb(0x2B2318));
        ImGui::PushStyleColor(ImGuiCol_HeaderHovered, colorFromRgb(0x3A2F1F));
        ImGui::PushStyleColor(ImGuiCol_HeaderActive, colorFromRgb(0x5B4323));
        ImGui::PushStyleColor(ImGuiCol_ChildBg, colorFromRgb(0x171B1F));
        ImGui::PushStyleColor(ImGuiCol_Border, colorFromRgb(0x313944));
        if (ImGui::BeginChild("SceneHeaderCard", ImVec2(0.0f, 58.0f), ImGuiChildFlags_Borders))
        {
            ImGui::SetNextItemWidth(-1.0f);
            ImGui::InputTextWithHint("##SceneFilter", "Search scene...", m_sceneFilter, sizeof(m_sceneFilter));

            const std::optional<uint16_t> isolatedRoomId = m_viewport.isolatedIndoorRoomId();
            std::string roomFilterLabel = "All rooms";

            if (m_indoorSceneRoomFilter >= 0)
            {
                roomFilterLabel = "Room " + std::to_string(m_indoorSceneRoomFilter);
            }

            if (ImGui::BeginCombo("##IndoorSceneRoomFilter", roomFilterLabel.c_str()))
            {
                if (ImGui::Selectable("All rooms", m_indoorSceneRoomFilter < 0))
                {
                    m_indoorSceneRoomFilter = -1;
                }

                if (isolatedRoomId.has_value())
                {
                    const std::string isolatedLabel = "Use isolated room (" + std::to_string(*isolatedRoomId) + ")";

                    if (ImGui::Selectable(isolatedLabel.c_str(), m_indoorSceneRoomFilter == *isolatedRoomId))
                    {
                        m_indoorSceneRoomFilter = *isolatedRoomId;
                    }
                }

                for (size_t roomId = 0; roomId < indoorGeometry.sectors.size(); ++roomId)
                {
                    const std::string label = "Room " + std::to_string(roomId);

                    if (ImGui::Selectable(label.c_str(), m_indoorSceneRoomFilter == static_cast<int>(roomId)))
                    {
                        m_indoorSceneRoomFilter = static_cast<int>(roomId);
                    }
                }

                ImGui::EndCombo();
            }

            if (isolatedRoomId.has_value())
            {
                ImGui::SameLine();

                if (ImGui::SmallButton("Isolated"))
                {
                    m_indoorSceneRoomFilter = *isolatedRoomId;
                }
            }

            if (m_indoorSceneRoomFilter >= 0)
            {
                ImGui::SameLine();

                if (ImGui::SmallButton("Clear"))
                {
                    m_indoorSceneRoomFilter = -1;
                }
            }
        }
        ImGui::EndChild();
        ImGui::PopStyleColor(5);
        ImGui::Spacing();

        const bool summarySelected = session.selection().kind == EditorSelectionKind::Summary;

        if (matchesSceneFilter(m_sceneFilter, "Level Summary") && ImGui::Selectable("Level Summary", summarySelected))
        {
            session.select(EditorSelectionKind::Summary);
        }

        if (matchesSceneFilter(m_sceneFilter, "Environment")
            && ImGui::Selectable("Environment", session.selection().kind == EditorSelectionKind::Environment))
        {
            session.select(EditorSelectionKind::Environment);
        }

        const auto renderIndexedList =
            [this, &session, &focusOutlinerSelection](
                const std::string &label,
                size_t count,
                EditorSelectionKind kind,
                const std::function<std::optional<std::string>(size_t)> &buildLabel)
        {
            if (!ImGui::TreeNodeEx(label.c_str(), ImGuiTreeNodeFlags_DefaultOpen))
            {
                return;
            }

            ImGuiListClipper clipper;
            clipper.Begin(static_cast<int>(count));

            while (clipper.Step())
            {
                for (int itemIndex = clipper.DisplayStart; itemIndex < clipper.DisplayEnd; ++itemIndex)
                {
                    const size_t index = static_cast<size_t>(itemIndex);
                    const std::optional<std::string> itemLabel = buildLabel(index);

                    if (!itemLabel.has_value())
                    {
                        continue;
                    }

                    if (ImGui::Selectable(
                            itemLabel->c_str(),
                            session.selection().kind == kind && session.selection().index == index))
                    {
                        session.select(kind, index);
                    }

                    focusOutlinerSelection(kind, index);
                }
            }

            ImGui::TreePop();
        };

        if (ImGui::TreeNodeEx(
                ("Rooms (" + std::to_string(indoorGeometry.sectors.size()) + ")").c_str(),
                ImGuiTreeNodeFlags_DefaultOpen))
        {
            for (size_t roomId = 0; roomId < indoorGeometry.sectors.size(); ++roomId)
            {
                if (!indoorRoomMatchesFilter(static_cast<uint16_t>(roomId), m_indoorSceneRoomFilter))
                {
                    continue;
                }

                const Game::IndoorSector &room = indoorGeometry.sectors[roomId];
                const std::vector<uint16_t> roomFaceIds = indoorSectorFaceIds(indoorGeometry, static_cast<uint16_t>(roomId));
                const std::vector<uint16_t> connectedRooms =
                    connectedIndoorRoomIds(indoorGeometry, static_cast<uint16_t>(roomId));
                const std::string roomLabel =
                    "Room " + std::to_string(roomId)
                    + " · faces " + std::to_string(roomFaceIds.size())
                    + " · portals " + std::to_string(room.portalFaceIds.size())
                    + " · links " + formatIndoorRoomList(connectedRooms);

                if (!matchesSceneFilter(m_sceneFilter, roomLabel))
                {
                    continue;
                }

                const bool roomSelected =
                    session.selection().kind == EditorSelectionKind::InteractiveFace
                    && session.selection().index < indoorGeometry.faces.size()
                    && (indoorGeometry.faces[session.selection().index].roomNumber == roomId
                        || indoorGeometry.faces[session.selection().index].roomBehindNumber == roomId);

                if (ImGui::Selectable(roomLabel.c_str(), roomSelected))
                {
                    selectRoomFaces(static_cast<uint16_t>(roomId));
                }

                if (ImGui::IsItemHovered() && ImGui::IsMouseDoubleClicked(ImGuiMouseButton_Left) && !roomFaceIds.empty())
                {
                    selectRoomFaces(static_cast<uint16_t>(roomId));
                    m_viewport.focusSelection(
                        session.document(),
                        {EditorSelectionKind::InteractiveFace, roomFaceIds.front()});
                }

                ImGui::SameLine();
                const std::string selectLabel = "Select##IndoorRoomSelect" + std::to_string(roomId);

                if (ImGui::SmallButton(selectLabel.c_str()))
                {
                    selectRoomFaces(static_cast<uint16_t>(roomId));
                }

                ImGui::SameLine();
                const bool isolated =
                    m_viewport.isolatedIndoorRoomId().has_value() && *m_viewport.isolatedIndoorRoomId() == roomId;
                const std::string isolateLabel =
                    isolated ? "Show##IndoorRoom" + std::to_string(roomId)
                             : "Isolate##IndoorRoom" + std::to_string(roomId);

                if (ImGui::SmallButton(isolateLabel.c_str()))
                {
                    m_viewport.setIsolatedIndoorRoomId(
                        isolated ? std::nullopt : std::optional<uint16_t>(static_cast<uint16_t>(roomId)));
                }
            }

            ImGui::TreePop();
        }

        renderIndexedList(
            "Faces (" + std::to_string(indoorGeometry.faces.size()) + ")",
            indoorGeometry.faces.size(),
            EditorSelectionKind::InteractiveFace,
            [this, &sceneData, &indoorGeometry](size_t faceIndex)
                -> std::optional<std::string>
            {
                const Game::IndoorFace effectiveFace = effectiveIndoorFace(sceneData, indoorGeometry, faceIndex);

                if (!indoorRoomMatchesFilter(effectiveFace.roomNumber, m_indoorSceneRoomFilter)
                    && !indoorRoomMatchesFilter(effectiveFace.roomBehindNumber, m_indoorSceneRoomFilter))
                {
                    return std::nullopt;
                }

                const std::string label = indoorFaceOutlinerLabel(effectiveFace, faceIndex);
                return matchesSceneFilter(m_sceneFilter, label) ? std::optional<std::string>(label) : std::nullopt;
            });
        renderIndexedList(
            "Entities (" + std::to_string(indoorGeometry.entities.size()) + ")",
            indoorGeometry.entities.size(),
            EditorSelectionKind::Entity,
            [this, &indoorGeometry, &roomLookupCache](size_t entityIndex)
                -> std::optional<std::string>
            {
                const Game::IndoorEntity &entity = indoorGeometry.entities[entityIndex];
                const std::optional<uint16_t> roomId =
                    findIndoorRoomIdForPoint(indoorGeometry, entity.x, entity.y, entity.z, roomLookupCache);

                if (!indoorRoomMatchesFilter(roomId, m_indoorSceneRoomFilter))
                {
                    return std::nullopt;
                }

                const std::string label = indoorEntityOutlinerLabel(entity, entityIndex, roomId);
                return matchesSceneFilter(m_sceneFilter, label) ? std::optional<std::string>(label) : std::nullopt;
            });
        renderIndexedList(
            "Lights (" + std::to_string(indoorGeometry.lights.size()) + ")",
            indoorGeometry.lights.size(),
            EditorSelectionKind::Light,
            [this, &indoorGeometry, &roomLookupCache](size_t lightIndex)
                -> std::optional<std::string>
            {
                const Game::IndoorLight &light = indoorGeometry.lights[lightIndex];
                const std::optional<uint16_t> roomId =
                    findIndoorRoomIdForPoint(indoorGeometry, light.x, light.y, light.z, roomLookupCache);

                if (!indoorRoomMatchesFilter(roomId, m_indoorSceneRoomFilter))
                {
                    return std::nullopt;
                }

                const std::string label = indoorLightOutlinerLabel(lightIndex, roomId);
                return matchesSceneFilter(m_sceneFilter, label) ? std::optional<std::string>(label) : std::nullopt;
            });
        renderIndexedList(
            "Spawns (" + std::to_string(indoorGeometry.spawns.size()) + ")",
            indoorGeometry.spawns.size(),
            EditorSelectionKind::Spawn,
            [this, &indoorGeometry, &roomLookupCache](size_t spawnIndex)
                -> std::optional<std::string>
            {
                const Game::IndoorSpawn &spawn = indoorGeometry.spawns[spawnIndex];
                const std::optional<uint16_t> roomId =
                    findIndoorRoomIdForPoint(indoorGeometry, spawn.x, spawn.y, spawn.z, roomLookupCache);

                if (!indoorRoomMatchesFilter(roomId, m_indoorSceneRoomFilter))
                {
                    return std::nullopt;
                }

                const std::string label = indoorSpawnOutlinerLabel(spawn, spawnIndex, roomId);
                return matchesSceneFilter(m_sceneFilter, label) ? std::optional<std::string>(label) : std::nullopt;
            });
        renderIndexedList(
            "Actors (" + std::to_string(sceneData.initialState.actors.size()) + ")",
            sceneData.initialState.actors.size(),
            EditorSelectionKind::Actor,
            [this, &session, &sceneData](size_t actorIndex)
                -> std::optional<std::string>
            {
                const Game::MapDeltaActor &actor = sceneData.initialState.actors[actorIndex];
                const std::optional<uint16_t> roomId =
                    actor.sectorId >= 0 ? std::optional<uint16_t>(static_cast<uint16_t>(actor.sectorId)) : std::nullopt;

                if (!indoorRoomMatchesFilter(roomId, m_indoorSceneRoomFilter))
                {
                    return std::nullopt;
                }

                std::string label = actorDisplayLabel(&session.monsterTable(), actor, actorIndex);
                label += " · " + (roomId.has_value() ? "Room " + std::to_string(*roomId) : std::string("Room ?"));
                return matchesSceneFilter(m_sceneFilter, label) ? std::optional<std::string>(label) : std::nullopt;
            });
        renderIndexedList(
            "Sprite Objects (" + std::to_string(sceneData.initialState.spriteObjects.size()) + ")",
            sceneData.initialState.spriteObjects.size(),
            EditorSelectionKind::SpriteObject,
            [this, &session, &sceneData](size_t objectIndex)
                -> std::optional<std::string>
            {
                const Game::MapDeltaSpriteObject &spriteObject = sceneData.initialState.spriteObjects[objectIndex];
                const std::optional<uint16_t> roomId = spriteObject.sectorId >= 0
                    ? std::optional<uint16_t>(static_cast<uint16_t>(spriteObject.sectorId))
                    : std::nullopt;

                if (!indoorRoomMatchesFilter(roomId, m_indoorSceneRoomFilter))
                {
                    return std::nullopt;
                }

                std::string label = spriteObjectDisplayLabel(session, spriteObject, objectIndex);
                label += " · " + (roomId.has_value() ? "Room " + std::to_string(*roomId) : std::string("Room ?"));
                return matchesSceneFilter(m_sceneFilter, label) ? std::optional<std::string>(label) : std::nullopt;
            });
        renderIndexedList(
            "Chests (" + std::to_string(sceneData.initialState.chests.size()) + ")",
            sceneData.initialState.chests.size(),
            EditorSelectionKind::Chest,
            [this](size_t chestIndex)
                -> std::optional<std::string>
            {
                const std::string label = "Chest " + std::to_string(chestIndex);
                return matchesSceneFilter(m_sceneFilter, label) ? std::optional<std::string>(label) : std::nullopt;
            });
        renderIndexedList(
            "Mechanisms (" + std::to_string(sceneData.initialState.doors.size()) + ")",
            sceneData.initialState.doors.size(),
            EditorSelectionKind::Door,
            [this, &sceneData, &indoorGeometry](size_t doorIndex)
                -> std::optional<std::string>
            {
                const std::vector<uint16_t> affectedRooms =
                    collectIndoorDoorRoomIds(indoorGeometry, sceneData.initialState.doors[doorIndex].door);

                if (!indoorRoomListMatchesFilter(affectedRooms, m_indoorSceneRoomFilter))
                {
                    return std::nullopt;
                }

                const std::string label = indoorDoorOutlinerLabel(sceneData.initialState.doors[doorIndex], affectedRooms);
                return matchesSceneFilter(m_sceneFilter, label) ? std::optional<std::string>(label) : std::nullopt;
            });

        ImGui::End();
        return;
    }

    if (session.document().kind() == EditorDocument::Kind::Mm9Dat)
    {
        const EditorDocument &document = session.document();
        const EditorMm9DatLevelMetadata &metadata = document.mm9DatLevelMetadata();

        ImGui::PushStyleColor(ImGuiCol_Header, colorFromRgb(0x2B2318));
        ImGui::PushStyleColor(ImGuiCol_HeaderHovered, colorFromRgb(0x3A2F1F));
        ImGui::PushStyleColor(ImGuiCol_HeaderActive, colorFromRgb(0x5B4323));
        ImGui::PushStyleColor(ImGuiCol_ChildBg, colorFromRgb(0x171B1F));
        ImGui::PushStyleColor(ImGuiCol_Border, colorFromRgb(0x313944));
        if (ImGui::BeginChild("SceneHeaderCard", ImVec2(0.0f, 38.0f), ImGuiChildFlags_Borders))
        {
            ImGui::SetNextItemWidth(-1.0f);
            ImGui::InputTextWithHint("##SceneFilter", "Search MM9 level...", m_sceneFilter, sizeof(m_sceneFilter));
        }
        ImGui::EndChild();
        ImGui::PopStyleColor(5);
        ImGui::Spacing();

        ImGui::PushStyleColor(ImGuiCol_Header, colorFromRgb(0x3C2D18));
        ImGui::PushStyleColor(ImGuiCol_HeaderHovered, colorFromRgb(0x4E3B21));
        ImGui::PushStyleColor(ImGuiCol_HeaderActive, colorFromRgb(0x654A27));
        ImGui::PushStyleColor(ImGuiCol_TextSelectedBg, ImVec4(0.34f, 0.24f, 0.12f, 0.72f));

        const bool summarySelected = session.selection().kind == EditorSelectionKind::Summary;

        if (matchesSceneFilter(m_sceneFilter, "Level Summary") && ImGui::Selectable("Level Summary", summarySelected))
        {
            session.select(EditorSelectionKind::Summary);
        }

        if (document.hasMm9DatLoadedSidecars())
        {
            const EditorMm9LoadedSidecars &sidecars = document.mm9DatLoadedSidecars();
            const std::string worldModelsLabel =
                "DAT World Models (" + std::to_string(sidecars.datWorld.worldModels.size()) + ")";

            if (ImGui::TreeNodeEx(worldModelsLabel.c_str(), ImGuiTreeNodeFlags_DefaultOpen))
            {
                ImGuiListClipper clipper;
                clipper.Begin(static_cast<int>(sidecars.datWorld.worldModels.size()));

                while (clipper.Step())
                {
                    for (int itemIndex = clipper.DisplayStart; itemIndex < clipper.DisplayEnd; ++itemIndex)
                    {
                        const EditorMm9DatWorldModelSummary &model =
                            sidecars.datWorld.worldModels[static_cast<size_t>(itemIndex)];
                        const std::string label =
                            std::to_string(model.sourceModelIndex)
                            + " - "
                            + (model.sourceName.empty() ? std::string("<unnamed>") : model.sourceName)
                            + " - "
                            + model.kind;

                        if (!matchesSceneFilter(m_sceneFilter, label))
                        {
                            continue;
                        }

                        const size_t modelIndex = static_cast<size_t>(itemIndex);
                        ImGui::PushID(static_cast<int>(modelIndex));
                        const bool selected =
                            session.selection().kind == EditorSelectionKind::Mm9WorldModel
                            && session.selection().index == modelIndex;

                        if (ImGui::Selectable(label.c_str(), selected))
                        {
                            session.select(EditorSelectionKind::Mm9WorldModel, modelIndex);
                        }

                        ImGui::PopID();
                    }
                }

                ImGui::TreePop();
            }

            const std::string objectsLabel =
                "Raw Objects (" + std::to_string(sidecars.rawObjects.objects.size()) + ")";

            if (ImGui::TreeNodeEx(objectsLabel.c_str(), ImGuiTreeNodeFlags_DefaultOpen))
            {
                ImGuiListClipper clipper;
                clipper.Begin(static_cast<int>(sidecars.rawObjects.objects.size()));

                while (clipper.Step())
                {
                    for (int itemIndex = clipper.DisplayStart; itemIndex < clipper.DisplayEnd; ++itemIndex)
                    {
                        const EditorMm9RawObject &object =
                            sidecars.rawObjects.objects[static_cast<size_t>(itemIndex)];
                        const std::string label =
                            std::to_string(object.objectIndex)
                            + " - "
                            + (object.name.empty() ? std::string("<unnamed>") : object.name)
                            + " - properties "
                            + std::to_string(object.properties.size());

                        if (!matchesSceneFilter(m_sceneFilter, label))
                        {
                            continue;
                        }

                        const size_t objectIndex = static_cast<size_t>(itemIndex);
                        ImGui::PushID(static_cast<int>(objectIndex));
                        const bool selected =
                            session.selection().kind == EditorSelectionKind::Mm9RawObject
                            && session.selection().index == objectIndex;

                        if (ImGui::Selectable(label.c_str(), selected))
                        {
                            session.select(EditorSelectionKind::Mm9RawObject, objectIndex);
                        }

                        ImGui::PopID();
                    }
                }

                ImGui::TreePop();
            }

            const std::string materialsLabel =
                "Materials (" + std::to_string(sidecars.materialAliases.textures.size()) + ")";

            if (ImGui::TreeNodeEx(materialsLabel.c_str()))
            {
                ImGuiListClipper clipper;
                clipper.Begin(static_cast<int>(sidecars.materialAliases.textures.size()));

                while (clipper.Step())
                {
                    for (int itemIndex = clipper.DisplayStart; itemIndex < clipper.DisplayEnd; ++itemIndex)
                    {
                        const EditorMm9MaterialTexture &texture =
                            sidecars.materialAliases.textures[static_cast<size_t>(itemIndex)];
                        const std::string label =
                            texture.alias
                            + " - "
                            + (texture.sourceTexture.empty() ? std::string("<missing source>") : texture.sourceTexture);

                        if (!matchesSceneFilter(m_sceneFilter, label))
                        {
                            continue;
                        }

                        const size_t textureIndex = static_cast<size_t>(itemIndex);
                        ImGui::PushID(static_cast<int>(textureIndex));
                        const bool selected =
                            session.selection().kind == EditorSelectionKind::Mm9MaterialTexture
                            && session.selection().index == textureIndex;

                        if (ImGui::Selectable(label.c_str(), selected))
                        {
                            session.select(EditorSelectionKind::Mm9MaterialTexture, textureIndex);
                        }

                        ImGui::PopID();
                    }
                }

                ImGui::TreePop();
            }

            const std::string eventsLabel =
                "Event Objects (" + std::to_string(sidecars.events.objects.size()) + ")";

            if (ImGui::TreeNodeEx(eventsLabel.c_str()))
            {
                ImGuiListClipper clipper;
                clipper.Begin(static_cast<int>(sidecars.events.objects.size()));

                while (clipper.Step())
                {
                    for (int itemIndex = clipper.DisplayStart; itemIndex < clipper.DisplayEnd; ++itemIndex)
                    {
                        const Game::Mm9EventObject &object =
                            sidecars.events.objects[static_cast<size_t>(itemIndex)];
                        const std::string label =
                            std::to_string(object.sourceObjectIndex)
                            + " - "
                            + (object.sourceName.empty() ? std::string("<unnamed>") : object.sourceName)
                            + " - "
                            + object.sourceClass;

                        if (!matchesSceneFilter(m_sceneFilter, label))
                        {
                            continue;
                        }

                        const size_t eventObjectIndex = static_cast<size_t>(itemIndex);
                        ImGui::PushID(static_cast<int>(eventObjectIndex));
                        const bool selected =
                            session.selection().kind == EditorSelectionKind::Mm9EventObject
                            && session.selection().index == eventObjectIndex;

                        if (ImGui::Selectable(label.c_str(), selected))
                        {
                            session.select(EditorSelectionKind::Mm9EventObject, eventObjectIndex);
                        }

                        ImGui::PopID();
                    }
                }

                ImGui::TreePop();
            }

            const std::string mechanismsLabel =
                "Mechanisms (" + std::to_string(sidecars.events.mechanisms.size()) + ")";

            if (ImGui::TreeNodeEx(mechanismsLabel.c_str()))
            {
                ImGuiListClipper clipper;
                clipper.Begin(static_cast<int>(sidecars.events.mechanisms.size()));

                while (clipper.Step())
                {
                    for (int itemIndex = clipper.DisplayStart; itemIndex < clipper.DisplayEnd; ++itemIndex)
                    {
                        const Game::Mm9EventMechanism &mechanism =
                            sidecars.events.mechanisms[static_cast<size_t>(itemIndex)];
                        const std::string label =
                            std::to_string(mechanism.sourceObjectIndex)
                            + " - "
                            + (mechanism.sourceName.empty() ? std::string("<unnamed>") : mechanism.sourceName)
                            + " - "
                            + (mechanism.kind.empty() ? mechanism.sourceClass : mechanism.kind);

                        if (!matchesSceneFilter(m_sceneFilter, label))
                        {
                            continue;
                        }

                        const size_t mechanismIndex = static_cast<size_t>(itemIndex);
                        ImGui::PushID(static_cast<int>(mechanismIndex));
                        const bool selected =
                            session.selection().kind == EditorSelectionKind::Mm9Mechanism
                            && session.selection().index == mechanismIndex;

                        if (ImGui::Selectable(label.c_str(), selected))
                        {
                            session.select(EditorSelectionKind::Mm9Mechanism, mechanismIndex);
                        }

                        ImGui::PopID();
                    }
                }

                ImGui::TreePop();
            }

            const std::string scriptsLabel =
                "Scripts (" + std::to_string(sidecars.events.scripts.size()) + ")";

            if (ImGui::TreeNodeEx(scriptsLabel.c_str()))
            {
                ImGuiListClipper clipper;
                clipper.Begin(static_cast<int>(sidecars.events.scripts.size()));

                while (clipper.Step())
                {
                    for (int itemIndex = clipper.DisplayStart; itemIndex < clipper.DisplayEnd; ++itemIndex)
                    {
                        const Game::Mm9EventScript &script =
                            sidecars.events.scripts[static_cast<size_t>(itemIndex)];
                        const std::string label =
                            script.scriptId
                            + " - "
                            + std::to_string(script.registeredTriggerCount)
                            + " triggers";

                        if (!matchesSceneFilter(m_sceneFilter, label))
                        {
                            continue;
                        }

                        const size_t scriptIndex = static_cast<size_t>(itemIndex);
                        ImGui::PushID(static_cast<int>(scriptIndex));
                        const bool selected =
                            session.selection().kind == EditorSelectionKind::Mm9EventScript
                            && session.selection().index == scriptIndex;

                        if (ImGui::Selectable(label.c_str(), selected))
                        {
                            session.select(EditorSelectionKind::Mm9EventScript, scriptIndex);
                        }

                        ImGui::PopID();
                    }
                }

                ImGui::TreePop();
            }

            const Game::OutdoorSceneData &mm9SceneData = document.outdoorSceneData();
            const Engine::AssetFileSystem *pAssetFileSystem = session.assetFileSystem();
            const Mm9ModelInstanceActorSourceLookup *pActorSourceLookup =
                pAssetFileSystem != nullptr
                    ? cachedMm9ModelInstanceActorSourceLookup(*pAssetFileSystem)
                    : nullptr;
            const auto rawObjectIndexForSourceObject =
                [&sidecars](size_t sourceObjectIndex) -> std::optional<size_t>
                {
                    for (size_t objectIndex = 0; objectIndex < sidecars.rawObjects.objects.size(); ++objectIndex)
                    {
                        if (sidecars.rawObjects.objects[objectIndex].objectIndex == sourceObjectIndex)
                        {
                            return objectIndex;
                        }
                    }

                    return std::nullopt;
                };

            const Game::Mm9ObjectLayer &objectLayer = document.mm9ObjectLayer();
            const std::string objectSourcesLabel =
                "Object Source Transforms (" + std::to_string(objectLayer.objects.size()) + ")";

            if (ImGui::TreeNodeEx(objectSourcesLabel.c_str()))
            {
                ImGuiListClipper clipper;
                clipper.Begin(static_cast<int>(objectLayer.objects.size()));

                while (clipper.Step())
                {
                    for (int itemIndex = clipper.DisplayStart; itemIndex < clipper.DisplayEnd; ++itemIndex)
                    {
                        const size_t objectSourceIndex = static_cast<size_t>(itemIndex);
                        const Game::Mm9Object &object = objectLayer.objects[objectSourceIndex];
                        std::string label =
                            std::to_string(object.sourceObjectIndex)
                            + " - "
                            + (object.sourceName.empty() ? std::string("<unnamed>") : object.sourceName)
                            + " - "
                            + object.sourceClass;

                        if (object.hasBoundsEvidence)
                        {
                            label += " - bounds";
                        }

                        if (object.triggerVolume)
                        {
                            label += " - trigger";
                        }

                        if (!matchesSceneFilter(m_sceneFilter, label))
                        {
                            continue;
                        }

                        const std::optional<size_t> rawObjectIndex =
                            rawObjectIndexForSourceObject(object.sourceObjectIndex);
                        const bool selected =
                            rawObjectIndex
                            && session.selection().kind == EditorSelectionKind::Mm9RawObject
                            && session.selection().index == *rawObjectIndex;

                        ImGui::PushID(static_cast<int>(objectSourceIndex));
                        if (ImGui::Selectable(label.c_str(), selected) && rawObjectIndex)
                        {
                            session.select(EditorSelectionKind::Mm9RawObject, *rawObjectIndex);
                        }
                        ImGui::PopID();
                    }
                }

                ImGui::TreePop();
            }

            const Game::Mm9LightLayer &lightLayer = document.mm9LightLayer();
            const std::string lightsLabel =
                "Light Objects (" + std::to_string(lightLayer.lights.size()) + ")";

            if (ImGui::TreeNodeEx(lightsLabel.c_str()))
            {
                ImGuiListClipper clipper;
                clipper.Begin(static_cast<int>(lightLayer.lights.size()));

                while (clipper.Step())
                {
                    for (int itemIndex = clipper.DisplayStart; itemIndex < clipper.DisplayEnd; ++itemIndex)
                    {
                        const size_t lightIndex = static_cast<size_t>(itemIndex);
                        const Game::Mm9LightObject &light = lightLayer.lights[lightIndex];
                        std::string label =
                            std::to_string(light.sourceObjectIndex)
                            + " - "
                            + (light.sourceName.empty() ? std::string("<unnamed>") : light.sourceName)
                            + " - "
                            + light.sourceClass
                            + " - radius "
                            + (light.hasLightRadius ? std::to_string(light.lightRadius) : std::string("<missing>"));

                        if (!matchesSceneFilter(m_sceneFilter, label))
                        {
                            continue;
                        }

                        const std::optional<size_t> rawObjectIndex =
                            rawObjectIndexForSourceObject(light.sourceObjectIndex);
                        const bool selected =
                            rawObjectIndex
                            && session.selection().kind == EditorSelectionKind::Mm9RawObject
                            && session.selection().index == *rawObjectIndex;

                        ImGui::PushID(static_cast<int>(lightIndex));
                        if (ImGui::Selectable(label.c_str(), selected) && rawObjectIndex)
                        {
                            session.select(EditorSelectionKind::Mm9RawObject, *rawObjectIndex);
                        }
                        ImGui::PopID();
                    }
                }

                ImGui::TreePop();
            }

            const Game::Mm9SoundLayer &soundLayer = document.mm9SoundLayer();
            const std::string soundsLabel =
                "Sound Objects (" + std::to_string(soundLayer.objects.size()) + ")";

            if (ImGui::TreeNodeEx(soundsLabel.c_str()))
            {
                ImGuiListClipper clipper;
                clipper.Begin(static_cast<int>(soundLayer.objects.size()));

                while (clipper.Step())
                {
                    for (int itemIndex = clipper.DisplayStart; itemIndex < clipper.DisplayEnd; ++itemIndex)
                    {
                        const size_t soundIndex = static_cast<size_t>(itemIndex);
                        const Game::Mm9SoundObject &sound = soundLayer.objects[soundIndex];
                        std::string label =
                            std::to_string(sound.sourceObjectIndex)
                            + " - "
                            + (sound.sourceName.empty() ? std::string("<unnamed>") : sound.sourceName)
                            + " - "
                            + sound.sourceClass
                            + " - refs "
                            + std::to_string(sound.references.size());

                        for (const Game::Mm9SoundSourceReference &reference : sound.references)
                        {
                            label += " - " + reference.propertyName + ":" + reference.sourceValue;
                        }

                        if (!matchesSceneFilter(m_sceneFilter, label))
                        {
                            continue;
                        }

                        const std::optional<size_t> rawObjectIndex =
                            rawObjectIndexForSourceObject(sound.sourceObjectIndex);
                        const bool selected =
                            rawObjectIndex
                            && session.selection().kind == EditorSelectionKind::Mm9RawObject
                            && session.selection().index == *rawObjectIndex;

                        ImGui::PushID(static_cast<int>(soundIndex));
                        if (ImGui::Selectable(label.c_str(), selected) && rawObjectIndex)
                        {
                            session.select(EditorSelectionKind::Mm9RawObject, *rawObjectIndex);
                        }
                        ImGui::PopID();
                    }
                }

                ImGui::TreePop();
            }

            const Game::Mm9SpawnLayer &spawnLayer = document.mm9SpawnLayer();
            const std::string spawnLabel =
                "Spawn Source Objects (" + std::to_string(spawnLayer.objects.size()) + ")";

            if (ImGui::TreeNodeEx(spawnLabel.c_str()))
            {
                ImGuiListClipper clipper;
                clipper.Begin(static_cast<int>(spawnLayer.objects.size()));

                while (clipper.Step())
                {
                    for (int itemIndex = clipper.DisplayStart; itemIndex < clipper.DisplayEnd; ++itemIndex)
                    {
                        const size_t spawnIndex = static_cast<size_t>(itemIndex);
                        const Game::Mm9SpawnObject &spawn = spawnLayer.objects[spawnIndex];
                        std::string label =
                            std::to_string(spawn.sourceObjectIndex)
                            + " - "
                            + (spawn.sourceName.empty() ? std::string("<unnamed>") : spawn.sourceName)
                            + " - "
                            + spawn.sourceClass;

                        if (spawn.spawnLevel)
                        {
                            label += " - level " + std::to_string(*spawn.spawnLevel);
                        }

                        if (spawn.npcNumber)
                        {
                            label += " - npc " + std::to_string(*spawn.npcNumber);
                        }

                        if (spawn.spawnObject && !spawn.spawnObject->empty())
                        {
                            label += " - object " + *spawn.spawnObject;
                        }

                        if (!matchesSceneFilter(m_sceneFilter, label))
                        {
                            continue;
                        }

                        const std::optional<size_t> rawObjectIndex =
                            rawObjectIndexForSourceObject(spawn.sourceObjectIndex);
                        const bool selected =
                            rawObjectIndex
                            && session.selection().kind == EditorSelectionKind::Mm9RawObject
                            && session.selection().index == *rawObjectIndex;

                        ImGui::PushID(static_cast<int>(spawnIndex));
                        if (ImGui::Selectable(label.c_str(), selected) && rawObjectIndex)
                        {
                            session.select(EditorSelectionKind::Mm9RawObject, *rawObjectIndex);
                        }
                        ImGui::PopID();
                    }
                }

                ImGui::TreePop();
            }

            const std::string sourceRefsLabel =
                "Source Asset References ("
                + std::to_string(document.mm9RawObjectAssetReferenceStatuses().size())
                + ")";

            if (ImGui::TreeNodeEx(sourceRefsLabel.c_str()))
            {
                ImGuiListClipper clipper;
                clipper.Begin(static_cast<int>(document.mm9RawObjectAssetReferenceStatuses().size()));

                while (clipper.Step())
                {
                    for (int itemIndex = clipper.DisplayStart; itemIndex < clipper.DisplayEnd; ++itemIndex)
                    {
                        const EditorMm9RawObjectAssetReferenceStatus &status =
                            document.mm9RawObjectAssetReferenceStatuses()[static_cast<size_t>(itemIndex)];
                        std::string label =
                            status.sourceFamily
                            + " - "
                            + status.objectName
                            + " - "
                            + status.propertyName
                            + " - "
                            + status.sourceValue;

                        if (!status.resolvedSourcePath.empty())
                        {
                            label += " -> " + status.resolvedSourcePath;
                        }

                        if (!matchesSceneFilter(m_sceneFilter, label))
                        {
                            continue;
                        }

                        const std::optional<size_t> rawObjectIndex =
                            rawObjectIndexForSourceObject(status.sourceObjectIndex);
                        const bool selected =
                            rawObjectIndex
                            && session.selection().kind == EditorSelectionKind::Mm9RawObject
                            && session.selection().index == *rawObjectIndex;

                        ImGui::PushID(itemIndex);
                        if (ImGui::Selectable(label.c_str(), selected) && rawObjectIndex)
                        {
                            session.select(EditorSelectionKind::Mm9RawObject, *rawObjectIndex);
                        }
                        ImGui::PopID();
                    }
                }

                ImGui::TreePop();
            }

            const std::string mm9ModelInstancesLabel =
                "Model Instances (" + std::to_string(mm9SceneData.modelInstances.size()) + ")";

            if (ImGui::TreeNodeEx(mm9ModelInstancesLabel.c_str()))
            {
                ImGuiListClipper clipper;
                clipper.Begin(static_cast<int>(mm9SceneData.modelInstances.size()));

                while (clipper.Step())
                {
                    for (int itemIndex = clipper.DisplayStart; itemIndex < clipper.DisplayEnd; ++itemIndex)
                    {
                        const size_t modelInstanceIndex = static_cast<size_t>(itemIndex);
                        const Game::OutdoorSceneModelInstance &modelInstance =
                            mm9SceneData.modelInstances[modelInstanceIndex];
                        const bool scripted =
                            isMm9ScriptedModelInstanceForEditor(
                                document,
                                modelInstance,
                                pActorSourceLookup);
                        const EditorSelectionKind selectionKind =
                            scripted ? EditorSelectionKind::Mm9ScriptedObject : EditorSelectionKind::ModelInstance;
                        std::string label =
                            modelInstance.sourceName
                            + " - "
                            + modelInstance.sourceClass
                            + " - "
                            + modelInstance.sourceModel
                            + " - "
                            + modelInstance.sourceSkin
                            + " - "
                            + modelInstance.modelAsset;

                        if (!matchesSceneFilter(m_sceneFilter, label))
                        {
                            continue;
                        }

                        const bool selected =
                            session.selection().kind == selectionKind
                            && session.selection().index == modelInstanceIndex;

                        ImGui::PushID(static_cast<int>(modelInstanceIndex));
                        if (ImGui::Selectable(label.c_str(), selected))
                        {
                            session.select(selectionKind, modelInstanceIndex);
                        }
                        ImGui::PopID();
                    }
                }

                ImGui::TreePop();
            }

            const std::string actorVariantsLabel =
                "Actor Variants (" + std::to_string(mm9SceneData.modelInstances.size()) + ")";

            if (ImGui::TreeNodeEx(actorVariantsLabel.c_str()))
            {
                ImGuiListClipper clipper;
                clipper.Begin(static_cast<int>(mm9SceneData.modelInstances.size()));

                while (clipper.Step())
                {
                    for (int itemIndex = clipper.DisplayStart; itemIndex < clipper.DisplayEnd; ++itemIndex)
                    {
                        const size_t modelInstanceIndex = static_cast<size_t>(itemIndex);
                        const Game::OutdoorSceneModelInstance &modelInstance =
                            mm9SceneData.modelInstances[modelInstanceIndex];
                        const Mm9ResolvedModelInstanceActorSource resolvedSource =
                            resolveMm9ModelInstanceActorSource(
                                modelInstance,
                                pActorSourceLookup);
                        const std::string resolvedAsset =
                            mm9ModelInstanceActorVariantAssetPath(
                                resolvedSource.sourceModel,
                                resolvedSource.sourceSkin);
                        std::string label =
                            (resolvedSource.variantId.empty() ? modelInstance.sourceName : resolvedSource.variantId)
                            + " - "
                            + (resolvedSource.actorRow.monsterName.empty()
                                ? modelInstance.sourceClass
                                : resolvedSource.actorRow.monsterName)
                            + " - "
                            + (resolvedSource.actorRow.typePicture.empty()
                                ? std::string("<no type picture>")
                                : resolvedSource.actorRow.typePicture)
                            + " - "
                            + resolvedSource.sourceModel
                            + " - "
                            + resolvedSource.sourceSkin
                            + " - "
                            + resolvedAsset;

                        if (!matchesSceneFilter(m_sceneFilter, label))
                        {
                            continue;
                        }

                        const bool selected =
                            session.selection().kind == EditorSelectionKind::ModelInstance
                            && session.selection().index == modelInstanceIndex;

                        ImGui::PushID(static_cast<int>(modelInstanceIndex));
                        if (ImGui::Selectable(label.c_str(), selected))
                        {
                            session.select(EditorSelectionKind::ModelInstance, modelInstanceIndex);
                        }
                        ImGui::PopID();
                    }
                }

                ImGui::TreePop();
            }

            size_t diagnosticCount = session.validationMessages().size();
            for (const EditorMm9MaterialTextureStatus &status : document.mm9MaterialTextureStatuses())
            {
                if (!status.defaultHelperMaterial
                    && (status.placeholderMissingSource
                        || !status.sourceDtxResolved
                        || status.sourceDtxAmbiguous
                        || status.cacheOlderThanSource))
                {
                    ++diagnosticCount;
                }
            }

            for (const EditorMm9RawObjectAssetReferenceStatus &status :
                document.mm9RawObjectAssetReferenceStatuses())
            {
                if (status.required && (!status.resolved || status.ambiguous))
                {
                    ++diagnosticCount;
                }
            }

            for (const Game::Mm9EventMechanism &mechanism : sidecars.events.mechanisms)
            {
                bool hasBinding = false;
                bool hasResolvedTarget = false;
                bool hasUnresolvedTarget = false;

                for (const Game::Mm9EventBinding &binding : sidecars.events.bindings)
                {
                    if (binding.objectId != mechanism.objectId)
                    {
                        continue;
                    }

                    hasBinding = true;

                    for (const Game::Mm9EventBindingTarget &target : binding.targets)
                    {
                        if ((target.targetKind == "odm_bmodel" && target.bmodelIndex)
                            || (target.targetKind == "model_instance" && !target.targetId.empty()))
                        {
                            hasResolvedTarget = true;
                        }

                        if (target.targetKind == "unresolved")
                        {
                            hasUnresolvedTarget = true;
                        }
                    }
                }

                if (!hasBinding || !hasResolvedTarget || hasUnresolvedTarget)
                {
                    ++diagnosticCount;
                }
            }

            const std::string diagnosticsLabel =
                "Diagnostics (" + std::to_string(diagnosticCount) + ")";

            if (ImGui::TreeNodeEx(diagnosticsLabel.c_str()))
            {
                for (size_t diagnosticIndex = 0; diagnosticIndex < session.validationMessages().size(); ++diagnosticIndex)
                {
                    const std::string label = "document - " + session.validationMessages()[diagnosticIndex];

                    if (matchesSceneFilter(m_sceneFilter, label))
                    {
                        ImGui::BulletText("%s", label.c_str());
                    }
                }

                for (const EditorMm9MaterialTextureStatus &status : document.mm9MaterialTextureStatuses())
                {
                    if (status.defaultHelperMaterial
                        || (!status.placeholderMissingSource
                            && status.sourceDtxResolved
                            && !status.sourceDtxAmbiguous
                            && !status.cacheOlderThanSource))
                    {
                        continue;
                    }

                    const std::string label =
                        "material - "
                        + status.alias
                        + " - "
                        + status.sourceTexture
                        + " - "
                        + status.resolvedSourcePath;

                    if (!matchesSceneFilter(m_sceneFilter, label))
                    {
                        continue;
                    }

                    const bool selected =
                        session.selection().kind == EditorSelectionKind::Mm9MaterialTexture
                        && session.selection().index == status.textureIndex;

                    ImGui::PushID(static_cast<int>(status.textureIndex));
                    if (ImGui::Selectable(label.c_str(), selected))
                    {
                        session.select(EditorSelectionKind::Mm9MaterialTexture, status.textureIndex);
                    }
                    ImGui::PopID();
                }

                for (const EditorMm9RawObjectAssetReferenceStatus &status :
                    document.mm9RawObjectAssetReferenceStatuses())
                {
                    if (!status.required || (status.resolved && !status.ambiguous))
                    {
                        continue;
                    }

                    const std::string label =
                        "asset - "
                        + status.objectName
                        + " - "
                        + status.sourceFamily
                        + " - "
                        + status.sourceValue;

                    if (!matchesSceneFilter(m_sceneFilter, label))
                    {
                        continue;
                    }

                    const std::optional<size_t> rawObjectIndex =
                        rawObjectIndexForSourceObject(status.sourceObjectIndex);
                    const bool selected =
                        rawObjectIndex
                        && session.selection().kind == EditorSelectionKind::Mm9RawObject
                        && session.selection().index == *rawObjectIndex;

                    ImGui::PushID(static_cast<int>(status.sourceObjectIndex));
                    if (ImGui::Selectable(label.c_str(), selected) && rawObjectIndex)
                    {
                        session.select(EditorSelectionKind::Mm9RawObject, *rawObjectIndex);
                    }
                    ImGui::PopID();
                }

                for (size_t mechanismIndex = 0; mechanismIndex < sidecars.events.mechanisms.size(); ++mechanismIndex)
                {
                    const Game::Mm9EventMechanism &mechanism = sidecars.events.mechanisms[mechanismIndex];
                    bool hasBinding = false;
                    bool hasResolvedTarget = false;
                    bool hasUnresolvedTarget = false;

                    for (const Game::Mm9EventBinding &binding : sidecars.events.bindings)
                    {
                        if (binding.objectId != mechanism.objectId)
                        {
                            continue;
                        }

                        hasBinding = true;

                        for (const Game::Mm9EventBindingTarget &target : binding.targets)
                        {
                            if ((target.targetKind == "odm_bmodel" && target.bmodelIndex)
                                || (target.targetKind == "model_instance" && !target.targetId.empty()))
                            {
                                hasResolvedTarget = true;
                            }

                            if (target.targetKind == "unresolved")
                            {
                                hasUnresolvedTarget = true;
                            }
                        }
                    }

                    if (hasBinding && hasResolvedTarget && !hasUnresolvedTarget)
                    {
                        continue;
                    }

                    const std::string label =
                        "mechanism - "
                        + mechanism.sourceName
                        + " - "
                        + mechanism.sourceClass
                        + " - "
                        + mechanism.mechanismId;

                    if (!matchesSceneFilter(m_sceneFilter, label))
                    {
                        continue;
                    }

                    const bool selected =
                        session.selection().kind == EditorSelectionKind::Mm9Mechanism
                        && session.selection().index == mechanismIndex;

                    ImGui::PushID(static_cast<int>(mechanismIndex));
                    if (ImGui::Selectable(label.c_str(), selected))
                    {
                        session.select(EditorSelectionKind::Mm9Mechanism, mechanismIndex);
                    }
                    ImGui::PopID();
                }

                ImGui::TreePop();
            }
        }
        else
        {
            ImGui::TextDisabled("MM9 sidecars are not loaded.");
        }

        if (ImGui::TreeNodeEx("Declared Sidecars"))
        {
            ImGui::BulletText("DAT world: %s", metadata.sidecars.datWorld.c_str());
            ImGui::BulletText("Raw objects: %s", metadata.sidecars.rawObjects.c_str());
            ImGui::BulletText("Materials: %s", metadata.sidecars.materials.c_str());
            ImGui::BulletText("Events: %s", metadata.sidecars.events.c_str());
            ImGui::BulletText(
                "Source asset aliases: %s",
                metadata.sidecars.sourceAssetAliases
                    ? metadata.sidecars.sourceAssetAliases->c_str()
                    : "<none>");
            ImGui::BulletText("Lua: %s", metadata.scripts.level.c_str());
            ImGui::TreePop();
        }

        ImGui::PopStyleColor(4);
        ImGui::End();
        return;
    }

    const Game::OutdoorSceneData &sceneData = session.document().outdoorSceneData();
    bool pendingDuplicate = false;
    bool pendingDelete = false;
    const auto focusOutlinerSelection = [this, &session](EditorSelectionKind kind, size_t index)
    {
        if (ImGui::IsItemHovered() && ImGui::IsMouseDoubleClicked(ImGuiMouseButton_Left))
        {
            session.select(kind, index);
            m_viewport.focusSelection(session.document(), {kind, index});
        }
    };

    ImGui::PushStyleColor(ImGuiCol_Header, colorFromRgb(0x2B2318));
    ImGui::PushStyleColor(ImGuiCol_HeaderHovered, colorFromRgb(0x3A2F1F));
    ImGui::PushStyleColor(ImGuiCol_HeaderActive, colorFromRgb(0x5B4323));
    ImGui::PushStyleColor(ImGuiCol_ChildBg, colorFromRgb(0x171B1F));
    ImGui::PushStyleColor(ImGuiCol_Border, colorFromRgb(0x313944));
    if (ImGui::BeginChild("SceneHeaderCard", ImVec2(0.0f, 38.0f), ImGuiChildFlags_Borders))
    {
        ImGui::SetNextItemWidth(-1.0f);
        ImGui::InputTextWithHint("##SceneFilter", "Search scene...", m_sceneFilter, sizeof(m_sceneFilter));
    }
    ImGui::EndChild();
    ImGui::PopStyleColor(5);
    ImGui::Spacing();

    ImGui::PushStyleColor(ImGuiCol_Header, colorFromRgb(0x3C2D18));
    ImGui::PushStyleColor(ImGuiCol_HeaderHovered, colorFromRgb(0x4E3B21));
    ImGui::PushStyleColor(ImGuiCol_HeaderActive, colorFromRgb(0x654A27));
    ImGui::PushStyleColor(ImGuiCol_TextSelectedBg, ImVec4(0.34f, 0.24f, 0.12f, 0.72f));

    const bool summarySelected = session.selection().kind == EditorSelectionKind::Summary;

    if (matchesSceneFilter(m_sceneFilter, "Level Summary") && ImGui::Selectable("Level Summary", summarySelected))
    {
        session.select(EditorSelectionKind::Summary);
    }

    if (matchesSceneFilter(m_sceneFilter, "Environment")
        && ImGui::Selectable("Environment", session.selection().kind == EditorSelectionKind::Environment))
    {
        session.select(EditorSelectionKind::Environment);
    }

    if (matchesSceneFilter(m_sceneFilter, "Terrain Overrides")
        && ImGui::Selectable("Terrain Overrides", session.selection().kind == EditorSelectionKind::Terrain))
    {
        session.select(EditorSelectionKind::Terrain, std::numeric_limits<size_t>::max());
    }

    const std::string terrainOverrideLabel =
        "Terrain Override Cells (" + std::to_string(sceneData.terrainAttributeOverrides.size()) + ")";

    if (ImGui::TreeNodeEx(terrainOverrideLabel.c_str(), ImGuiTreeNodeFlags_DefaultOpen))
    {
        ImGuiListClipper clipper;
        clipper.Begin(static_cast<int>(sceneData.terrainAttributeOverrides.size()));

        while (clipper.Step())
        {
            for (int itemIndex = clipper.DisplayStart; itemIndex < clipper.DisplayEnd; ++itemIndex)
            {
                const Game::OutdoorSceneTerrainAttributeOverride &overrideEntry =
                    sceneData.terrainAttributeOverrides[itemIndex];
                const size_t flatIndex = terrainCellFlatIndex(overrideEntry.x, overrideEntry.y);
                const bool isSelected =
                    session.selection().kind == EditorSelectionKind::Terrain
                    && session.selection().index == flatIndex;
                const std::string label =
                    "(" + std::to_string(overrideEntry.x) + ", " + std::to_string(overrideEntry.y) + ")";

                if (!matchesSceneFilter(m_sceneFilter, label))
                {
                    continue;
                }

                if (ImGui::Selectable(label.c_str(), isSelected))
                {
                    session.select(EditorSelectionKind::Terrain, flatIndex);
                }

                focusOutlinerSelection(EditorSelectionKind::Terrain, flatIndex);
            }
        }

        ImGui::TreePop();
    }

    const Game::OutdoorMapData &outdoorGeometry = session.document().outdoorGeometry();
    const std::string bmodelsLabel = "BModels (" + std::to_string(outdoorGeometry.bmodels.size()) + ")";

    if (ImGui::TreeNodeEx(bmodelsLabel.c_str(), ImGuiTreeNodeFlags_DefaultOpen))
    {
        ImGuiListClipper clipper;
        clipper.Begin(static_cast<int>(outdoorGeometry.bmodels.size()));

        while (clipper.Step())
        {
            for (int itemIndex = clipper.DisplayStart; itemIndex < clipper.DisplayEnd; ++itemIndex)
            {
                const size_t bmodelIndex = static_cast<size_t>(itemIndex);
                const Game::OutdoorBModel &bmodel = outdoorGeometry.bmodels[bmodelIndex];
                const std::string label =
                    "BModel " + std::to_string(bmodelIndex)
                    + " (" + std::to_string(bmodel.faces.size()) + " faces)";

                if (!matchesSceneFilter(m_sceneFilter, label))
                {
                    continue;
                }

                const bool isSelected =
                    session.selection().kind == EditorSelectionKind::BModel && session.selection().index == bmodelIndex;

                if (ImGui::Selectable(label.c_str(), isSelected, ImGuiSelectableFlags_SpanAvailWidth))
                {
                    session.select(EditorSelectionKind::BModel, bmodelIndex);
                }

                if (ImGui::IsItemHovered() && ImGui::IsMouseDoubleClicked(ImGuiMouseButton_Left))
                {
                    session.select(EditorSelectionKind::BModel, bmodelIndex);
                    m_viewport.focusBModel(session.document(), bmodelIndex);
                }

                if (ImGui::BeginPopupContextItem())
                {
                    session.select(EditorSelectionKind::BModel, bmodelIndex);
                    pendingDuplicate = ImGui::MenuItem("Duplicate");
                    pendingDelete = ImGui::MenuItem("Delete");
                    ImGui::EndPopup();
                }
            }
        }

        ImGui::TreePop();
    }

    const std::string entitiesLabel = "Entities (" + std::to_string(sceneData.entities.size()) + ")";

    if (ImGui::TreeNodeEx(entitiesLabel.c_str(), ImGuiTreeNodeFlags_DefaultOpen))
    {
        ImGuiListClipper clipper;
        clipper.Begin(static_cast<int>(sceneData.entities.size()));

        while (clipper.Step())
        {
            for (int itemIndex = clipper.DisplayStart; itemIndex < clipper.DisplayEnd; ++itemIndex)
            {
                const size_t entityIndex = static_cast<size_t>(itemIndex);
                const bool isSelected =
                    session.selection().kind == EditorSelectionKind::Entity
                    && session.selection().index == entityIndex;
                const Game::OutdoorSceneEntity &entity = sceneData.entities[entityIndex];
                std::string label = entity.entity.name.empty()
                    ? "Entity " + std::to_string(entity.entityIndex)
                    : entity.entity.name + "##entity" + std::to_string(entity.entityIndex);

                if (entity.entity.eventIdPrimary != 0 || entity.entity.eventIdSecondary != 0)
                {
                    label += " [evt]";
                }

                if (!matchesSceneFilter(m_sceneFilter, label))
                {
                    continue;
                }

                if (ImGui::Selectable(label.c_str(), isSelected))
                {
                    session.select(EditorSelectionKind::Entity, entityIndex);
                }

                focusOutlinerSelection(EditorSelectionKind::Entity, entityIndex);

                if (ImGui::BeginPopupContextItem())
                {
                    session.select(EditorSelectionKind::Entity, entityIndex);
                    pendingDuplicate = ImGui::MenuItem("Duplicate");
                    pendingDelete = ImGui::MenuItem("Delete");
                    ImGui::EndPopup();
                }
            }
        }

        ImGui::TreePop();
    }

    const std::string spawnsLabel = "Spawns (" + std::to_string(sceneData.spawns.size()) + ")";

    if (ImGui::TreeNodeEx(spawnsLabel.c_str(), ImGuiTreeNodeFlags_DefaultOpen))
    {
        ImGuiListClipper clipper;
        clipper.Begin(static_cast<int>(sceneData.spawns.size()));

        while (clipper.Step())
        {
            for (int itemIndex = clipper.DisplayStart; itemIndex < clipper.DisplayEnd; ++itemIndex)
            {
                const size_t spawnIndex = static_cast<size_t>(itemIndex);
                const bool isSelected =
                    session.selection().kind == EditorSelectionKind::Spawn
                    && session.selection().index == spawnIndex;
                const Game::OutdoorSceneSpawn &spawn = sceneData.spawns[spawnIndex];
                const Game::MapStatsEntry *pMapEntry = session.currentMapStatsEntry();
                const Game::SpawnPreview preview = pMapEntry != nullptr
                    ? Game::SpawnPreviewResolver::describe(
                        *pMapEntry,
                        &session.monsterTable(),
                        spawn.spawn.typeId,
                        spawn.spawn.index,
                        spawn.spawn.attributes,
                        spawn.spawn.group)
                    : Game::SpawnPreview {};
                std::string label = "Spawn " + std::to_string(spawn.spawnIndex);

                if (!preview.summary.empty())
                {
                    label += " - " + preview.summary;
                }

                if (!matchesSceneFilter(m_sceneFilter, label))
                {
                    continue;
                }

                if (ImGui::Selectable(label.c_str(), isSelected))
                {
                    session.select(EditorSelectionKind::Spawn, spawnIndex);
                }

                focusOutlinerSelection(EditorSelectionKind::Spawn, spawnIndex);

                if (ImGui::BeginPopupContextItem())
                {
                    session.select(EditorSelectionKind::Spawn, spawnIndex);
                    pendingDuplicate = ImGui::MenuItem("Duplicate");
                    pendingDelete = ImGui::MenuItem("Delete");
                    ImGui::EndPopup();
                }
            }
        }

        ImGui::TreePop();
    }

    const Engine::AssetFileSystem *pAssetFileSystem = session.assetFileSystem();
    const Mm9ModelInstanceActorSourceLookup *pMm9ActorSourceLookup =
        pAssetFileSystem != nullptr
            ? cachedMm9ModelInstanceActorSourceLookup(*pAssetFileSystem)
            : nullptr;
    std::vector<size_t> scriptedModelInstanceIndices;
    std::vector<size_t> regularModelInstanceIndices;
    scriptedModelInstanceIndices.reserve(sceneData.modelInstances.size());
    regularModelInstanceIndices.reserve(sceneData.modelInstances.size());

    for (size_t modelInstanceIndex = 0; modelInstanceIndex < sceneData.modelInstances.size(); ++modelInstanceIndex)
    {
        const Game::OutdoorSceneModelInstance &modelInstance = sceneData.modelInstances[modelInstanceIndex];

        if (isMm9ScriptedModelInstanceForEditor(
                session.document(),
                modelInstance,
                pMm9ActorSourceLookup))
        {
            scriptedModelInstanceIndices.push_back(modelInstanceIndex);
        }
        else
        {
            regularModelInstanceIndices.push_back(modelInstanceIndex);
        }
    }

    if (!scriptedModelInstanceIndices.empty())
    {
        const std::string scriptedObjectsLabel =
            "MM9 Scripted Objects (" + std::to_string(scriptedModelInstanceIndices.size()) + ")";

        if (ImGui::TreeNodeEx(scriptedObjectsLabel.c_str()))
        {
            ImGuiListClipper clipper;
            clipper.Begin(static_cast<int>(scriptedModelInstanceIndices.size()));

            while (clipper.Step())
            {
                for (int itemIndex = clipper.DisplayStart; itemIndex < clipper.DisplayEnd; ++itemIndex)
                {
                    const size_t modelInstanceIndex = scriptedModelInstanceIndices[static_cast<size_t>(itemIndex)];
                    const Game::OutdoorSceneModelInstance &modelInstance =
                        sceneData.modelInstances[modelInstanceIndex];
                    const bool isSelected =
                        session.selection().kind == EditorSelectionKind::Mm9ScriptedObject
                        && session.selection().index == modelInstanceIndex;
                    std::string label = modelInstance.sourceName.empty()
                        ? modelInstance.instanceId
                        : modelInstance.sourceName + "##mm9_scripted_object" + std::to_string(itemIndex);

                    if (!modelInstance.sourceClass.empty())
                    {
                        label += " - " + modelInstance.sourceClass;
                    }

                    if (!matchesSceneFilter(m_sceneFilter, label))
                    {
                        continue;
                    }

                    if (ImGui::Selectable(label.c_str(), isSelected))
                    {
                        session.select(EditorSelectionKind::Mm9ScriptedObject, modelInstanceIndex);
                    }

                    focusOutlinerSelection(EditorSelectionKind::Mm9ScriptedObject, modelInstanceIndex);

                    if (ImGui::IsItemHovered())
                    {
                        ImGui::BeginTooltip();
                        ImGui::Text("Source: %s", modelInstance.sourceRef.c_str());
                        ImGui::Text("Class: %s", modelInstance.sourceClass.c_str());
                        ImGui::Text("Scripted object backed by model instance %zu", modelInstanceIndex);
                        ImGui::Text(
                            "Position: %d, %d, %d",
                            modelInstance.x,
                            modelInstance.y,
                            modelInstance.z);
                        ImGui::EndTooltip();
                    }
                }
            }

            ImGui::TreePop();
        }
    }

    const std::string modelInstancesLabel =
        "Model Instances (" + std::to_string(regularModelInstanceIndices.size()) + ")";

    if (ImGui::TreeNodeEx(modelInstancesLabel.c_str()))
    {
        ImGuiListClipper clipper;
        clipper.Begin(static_cast<int>(regularModelInstanceIndices.size()));

        while (clipper.Step())
        {
            for (int itemIndex = clipper.DisplayStart; itemIndex < clipper.DisplayEnd; ++itemIndex)
            {
                const size_t modelInstanceIndex = regularModelInstanceIndices[static_cast<size_t>(itemIndex)];
                const Game::OutdoorSceneModelInstance &modelInstance =
                    sceneData.modelInstances[modelInstanceIndex];
                const bool isSelected =
                    session.selection().kind == EditorSelectionKind::ModelInstance
                    && session.selection().index == modelInstanceIndex;
                std::string label = modelInstance.sourceName.empty()
                    ? modelInstance.instanceId
                    : modelInstance.sourceName + "##model_instance" + std::to_string(itemIndex);

                if (!modelInstance.modelAsset.empty())
                {
                    label += " - " + modelInstance.modelAsset;
                }

                if (!matchesSceneFilter(m_sceneFilter, label))
                {
                    continue;
                }

                if (ImGui::Selectable(label.c_str(), isSelected))
                {
                    session.select(EditorSelectionKind::ModelInstance, modelInstanceIndex);
                }

                focusOutlinerSelection(EditorSelectionKind::ModelInstance, modelInstanceIndex);

                if (ImGui::IsItemHovered())
                {
                    ImGui::BeginTooltip();
                    ImGui::Text("Source: %s", modelInstance.sourceRef.c_str());
                    ImGui::Text("Class: %s", modelInstance.sourceClass.c_str());
                    ImGui::Text(
                        "Position: %d, %d, %d",
                        modelInstance.x,
                        modelInstance.y,
                        modelInstance.z);
                    ImGui::EndTooltip();
                }
            }
        }

        ImGui::TreePop();
    }

    const std::string actorsLabel = "Actors (" + std::to_string(sceneData.initialState.actors.size()) + ")";

    if (ImGui::TreeNodeEx(actorsLabel.c_str(), ImGuiTreeNodeFlags_DefaultOpen))
    {
        ImGuiListClipper clipper;
        clipper.Begin(static_cast<int>(sceneData.initialState.actors.size()));

        while (clipper.Step())
        {
            for (int itemIndex = clipper.DisplayStart; itemIndex < clipper.DisplayEnd; ++itemIndex)
            {
                const size_t actorIndex = static_cast<size_t>(itemIndex);
                const bool isSelected =
                    session.selection().kind == EditorSelectionKind::Actor
                    && session.selection().index == actorIndex;
                const Game::MapDeltaActor &actor = sceneData.initialState.actors[actorIndex];
                const std::string label = actorDisplayLabel(
                    &session.monsterTable(),
                    actor,
                    actorIndex)
                    + "##actor" + std::to_string(actorIndex);

                if (!matchesSceneFilter(m_sceneFilter, label))
                {
                    continue;
                }

                if (ImGui::Selectable(label.c_str(), isSelected))
                {
                    session.select(EditorSelectionKind::Actor, actorIndex);
                }

                focusOutlinerSelection(EditorSelectionKind::Actor, actorIndex);

                if (ImGui::BeginPopupContextItem())
                {
                    session.select(EditorSelectionKind::Actor, actorIndex);
                    pendingDuplicate = ImGui::MenuItem("Duplicate");
                    pendingDelete = ImGui::MenuItem("Delete");
                    ImGui::EndPopup();
                }
            }
        }

        ImGui::TreePop();
    }

    const std::string objectsLabel =
        "Sprite Objects (" + std::to_string(sceneData.initialState.spriteObjects.size()) + ")";

    if (ImGui::TreeNodeEx(objectsLabel.c_str(), ImGuiTreeNodeFlags_DefaultOpen))
    {
        ImGuiListClipper clipper;
        clipper.Begin(static_cast<int>(sceneData.initialState.spriteObjects.size()));

        while (clipper.Step())
        {
            for (int itemIndex = clipper.DisplayStart; itemIndex < clipper.DisplayEnd; ++itemIndex)
            {
                const size_t spriteObjectIndex = static_cast<size_t>(itemIndex);
                const bool isSelected =
                    session.selection().kind == EditorSelectionKind::SpriteObject
                    && session.selection().index == spriteObjectIndex;
                const Game::MapDeltaSpriteObject &spriteObject = sceneData.initialState.spriteObjects[spriteObjectIndex];
                const std::string label =
                    spriteObjectDisplayLabel(session, spriteObject, spriteObjectIndex)
                    + "##object"
                    + std::to_string(spriteObjectIndex);

                if (!matchesSceneFilter(m_sceneFilter, label))
                {
                    continue;
                }

                if (ImGui::Selectable(label.c_str(), isSelected))
                {
                    session.select(EditorSelectionKind::SpriteObject, spriteObjectIndex);
                }

                focusOutlinerSelection(EditorSelectionKind::SpriteObject, spriteObjectIndex);

                if (ImGui::BeginPopupContextItem())
                {
                    session.select(EditorSelectionKind::SpriteObject, spriteObjectIndex);
                    pendingDuplicate = ImGui::MenuItem("Duplicate");
                    pendingDelete = ImGui::MenuItem("Delete");
                    ImGui::EndPopup();
                }
            }
        }

        ImGui::TreePop();
    }

    const std::string chestsLabel = "Chests (" + std::to_string(sceneData.initialState.chests.size()) + ")";

    if (ImGui::TreeNodeEx(chestsLabel.c_str(), ImGuiTreeNodeFlags_DefaultOpen))
    {
        ImGuiListClipper clipper;
        clipper.Begin(static_cast<int>(sceneData.initialState.chests.size()));

        while (clipper.Step())
        {
            for (int itemIndex = clipper.DisplayStart; itemIndex < clipper.DisplayEnd; ++itemIndex)
            {
                const size_t chestIndex = static_cast<size_t>(itemIndex);
                const bool isSelected =
                    session.selection().kind == EditorSelectionKind::Chest
                    && session.selection().index == chestIndex;
                const Game::MapDeltaChest &chest = sceneData.initialState.chests[chestIndex];
                const Game::ChestEntry *pChestEntry = session.chestTable().get(chest.chestTypeId);
                std::string label = "Chest " + std::to_string(chestIndex);

                if (pChestEntry != nullptr && !pChestEntry->name.empty())
                {
                    label += " - " + pChestEntry->name;
                }

                const std::vector<EditorChestLink> chestLinks = session.findChestLinks(chestIndex);

                if (!chestLinks.empty())
                {
                    label += " [";
                    label += std::to_string(chestLinks.size());
                    label += " opener";
                    if (chestLinks.size() != 1)
                    {
                        label += "s";
                    }
                    label += "]";
                }

                if (!matchesSceneFilter(m_sceneFilter, label))
                {
                    continue;
                }

                if (ImGui::Selectable(label.c_str(), isSelected))
                {
                    session.select(EditorSelectionKind::Chest, chestIndex);
                }

                focusOutlinerSelection(EditorSelectionKind::Chest, chestIndex);
            }
        }

        ImGui::TreePop();
    }

    if (pendingDuplicate)
    {
        duplicateSelected(session);
    }

    if (pendingDelete)
    {
        deleteSelected(session);
    }

    ImGui::PopStyleColor(4);

    ImGui::End();
}

void EditorMainWindow::renderInspector(EditorSession &session)
{
    ImGui::SetNextWindowDockID(editorDockspaceId(), ImGuiCond_FirstUseEver);

    if (!ImGui::Begin("Inspector"))
    {
        ImGui::End();
        return;
    }

    if (!session.hasDocument())
    {
        ImGui::TextUnformatted("No document loaded.");
        ImGui::End();
        return;
    }

    std::pair<std::string, std::string> selectionSummary = inspectorSelectionSummary(session);

    if (m_viewport.placementKind() == EditorSelectionKind::Actor)
    {
        selectionSummary = {"Actor Placement", "Click in the viewport to place an actor"};
    }
    else if (m_viewport.placementKind() == EditorSelectionKind::SpriteObject)
    {
        selectionSummary = {"Item Placement", "Click in the viewport to place an item pickup"};
    }
    else if (m_viewport.placementKind() == EditorSelectionKind::Entity)
    {
        selectionSummary = {"Decoration Placement", "Click in the viewport to place a decoration"};
    }
    else if (m_viewport.placementKind() == EditorSelectionKind::Spawn)
    {
        selectionSummary = {"Spawn Placement", "Click in the viewport to place a spawn marker"};
    }
    else if (session.document().kind() == EditorDocument::Kind::Outdoor)
    {
        switch (m_viewport.placementKind())
        {
        case EditorSelectionKind::Entity:
            selectionSummary = {"Entity Placement", "Click in the viewport to place a decoration"};
            break;
        case EditorSelectionKind::Spawn:
            selectionSummary = {"Spawn Placement", "Click in the viewport to place a spawn marker"};
            break;
        case EditorSelectionKind::Terrain:
            selectionSummary = {"Terrain", "Terrain editing tools"};
            break;
        case EditorSelectionKind::None:
        case EditorSelectionKind::Summary:
        case EditorSelectionKind::Environment:
        case EditorSelectionKind::BModel:
        case EditorSelectionKind::InteractiveFace:
        case EditorSelectionKind::Actor:
        case EditorSelectionKind::SpriteObject:
        case EditorSelectionKind::Chest:
        case EditorSelectionKind::Light:
        case EditorSelectionKind::Door:
        case EditorSelectionKind::ModelInstance:
        case EditorSelectionKind::Mm9ScriptedObject:
        case EditorSelectionKind::Mm9WorldModel:
        case EditorSelectionKind::Mm9DatPolygon:
        case EditorSelectionKind::Mm9MaterialTexture:
        case EditorSelectionKind::Mm9RawObject:
        case EditorSelectionKind::Mm9EventObject:
        case EditorSelectionKind::Mm9Mechanism:
        case EditorSelectionKind::Mm9EventScript:
            break;
        }
    }

    const std::string &selectionTitle = selectionSummary.first;
    const std::string &selectionSubtitle = selectionSummary.second;
    ImGui::PushStyleColor(ImGuiCol_ChildBg, colorFromRgb(0x171B1F));
    ImGui::PushStyleColor(ImGuiCol_Border, colorFromRgb(0x313944));
    if (ImGui::BeginChild("InspectorSelectionHeader", ImVec2(0.0f, 56.0f), ImGuiChildFlags_Borders))
    {
        ImGui::PushStyleColor(ImGuiCol_Text, colorFromRgb(0xF2DEC2));
        ImGui::TextUnformatted(selectionTitle.c_str());
        ImGui::PopStyleColor();

        if (!selectionSubtitle.empty())
        {
            ImGui::PushStyleColor(ImGuiCol_Text, colorFromRgb(0xB5BDC8));
            ImGui::TextUnformatted(selectionSubtitle.c_str());
            ImGui::PopStyleColor();
        }
    }
    ImGui::EndChild();
    ImGui::PopStyleColor(2);
    ImGui::Spacing();

    if (m_viewport.placementKind() == EditorSelectionKind::Entity)
    {
        renderEntityPlacementInspector(session);
        ImGui::End();
        return;
    }

    if (m_viewport.placementKind() == EditorSelectionKind::Spawn)
    {
        renderSpawnPlacementInspector(session);
        ImGui::End();
        return;
    }

    if (m_viewport.placementKind() == EditorSelectionKind::Actor)
    {
        renderActorPlacementInspector(session);
        ImGui::End();
        return;
    }

    if (m_viewport.placementKind() == EditorSelectionKind::SpriteObject)
    {
        renderSpriteObjectPlacementInspector(session);
        ImGui::End();
        return;
    }

    if (session.document().kind() == EditorDocument::Kind::Outdoor
        && m_viewport.placementKind() == EditorSelectionKind::Terrain)
    {
        renderTerrainInspector(session);
        ImGui::End();
        return;
    }

    switch (session.selection().kind)
    {
    case EditorSelectionKind::None:
    case EditorSelectionKind::Summary:
        renderDocumentSummary(session);
        break;

    case EditorSelectionKind::Environment:
        renderEnvironmentInspector(session);
        break;

    case EditorSelectionKind::Terrain:
        renderTerrainInspector(session);
        break;

    case EditorSelectionKind::BModel:
        renderBModelInspector(session, session.selection().index);
        break;

    case EditorSelectionKind::Entity:
        if (session.document().kind() == EditorDocument::Kind::Indoor)
        {
            renderIndoorEntityInspector(session, session.selection().index);
        }
        else
        {
            renderEntityInspector(session, session.selection().index);
        }
        break;

    case EditorSelectionKind::Spawn:
        if (session.document().kind() == EditorDocument::Kind::Indoor)
        {
            renderIndoorSpawnInspector(session, session.selection().index);
        }
        else
        {
            renderSpawnInspector(session, session.selection().index);
        }
        break;

    case EditorSelectionKind::Actor:
        if (session.document().kind() == EditorDocument::Kind::Indoor)
        {
            renderIndoorActorInspector(session, session.selection().index);
        }
        else
        {
            renderActorInspector(session, session.selection().index);
        }
        break;

    case EditorSelectionKind::SpriteObject:
        if (session.document().kind() == EditorDocument::Kind::Indoor)
        {
            renderIndoorSpriteObjectInspector(session, session.selection().index);
        }
        else
        {
            renderSpriteObjectInspector(session, session.selection().index);
        }
        break;

    case EditorSelectionKind::Chest:
        if (session.document().kind() == EditorDocument::Kind::Indoor)
        {
            renderIndoorChestInspector(session, session.selection().index);
        }
        else
        {
            renderChestInspector(session, session.selection().index);
        }
        break;

    case EditorSelectionKind::InteractiveFace:
        renderInteractiveFaceInspector(session);
        break;

    case EditorSelectionKind::Light:
        renderIndoorLightInspector(session, session.selection().index);
        break;

    case EditorSelectionKind::Door:
        renderIndoorDoorInspector(session, session.selection().index);
        break;

    case EditorSelectionKind::ModelInstance:
    case EditorSelectionKind::Mm9ScriptedObject:
        if (session.document().kind() == EditorDocument::Kind::Outdoor
            || session.document().kind() == EditorDocument::Kind::Mm9Dat)
        {
            const Game::OutdoorSceneData &sceneData = session.document().outdoorSceneData();

            if (session.selection().index < sceneData.modelInstances.size())
            {
                const Game::OutdoorSceneModelInstance &modelInstance =
                    sceneData.modelInstances[session.selection().index];
                if (session.selection().kind == EditorSelectionKind::Mm9ScriptedObject)
                {
                    ImGui::TextUnformatted("MM9 Scripted Object");
                    ImGui::Text("Model Instance Index: %zu", session.selection().index);
                    ImGui::Separator();
                }
                ImGui::Text("Source: %s", modelInstance.sourceRef.c_str());
                ImGui::Text("Class: %s", modelInstance.sourceClass.c_str());
                ImGui::Text("Name: %s", modelInstance.sourceName.c_str());
                ImGui::Text("Model: %s", modelInstance.sourceModel.c_str());
                ImGui::Text("Skin: %s", modelInstance.sourceSkin.c_str());
                ImGui::Text("Asset: %s", modelInstance.modelAsset.c_str());

                const Engine::AssetFileSystem *pAssetFileSystem = session.assetFileSystem();
                const Mm9ModelInstanceActorSourceLookup *pActorSourceLookup =
                    pAssetFileSystem != nullptr
                        ? cachedMm9ModelInstanceActorSourceLookup(*pAssetFileSystem)
                        : nullptr;
                const Mm9ResolvedModelInstanceActorSource resolvedSource =
                    resolveMm9ModelInstanceActorSource(
                        modelInstance,
                        pActorSourceLookup);
                if (session.document().kind() == EditorDocument::Kind::Mm9Dat)
                {
                    const EditorDocument &document = session.document();
                    const std::string resolvedAsset =
                        mm9ModelInstanceActorVariantAssetPath(
                            resolvedSource.sourceModel,
                            resolvedSource.sourceSkin);
                    std::string resolvedAssetOpenPath;

                    if (pAssetFileSystem != nullptr)
                    {
                        const std::optional<std::filesystem::path> physicalAssetPath =
                            pAssetFileSystem->resolvePhysicalPath(resolvedAsset);

                        if (physicalAssetPath)
                        {
                            resolvedAssetOpenPath = physicalAssetPath->generic_string();
                        }
                    }

                    std::optional<size_t> linkedRawObjectIndex;
                    std::optional<size_t> linkedEventObjectIndex;
                    std::optional<size_t> linkedMechanismIndex;

                    if (document.hasMm9DatLoadedSidecars()
                        && modelInstance.sourceObjectIndex <= static_cast<size_t>(std::numeric_limits<int>::max()))
                    {
                        const EditorMm9LoadedSidecars &sidecars = document.mm9DatLoadedSidecars();
                        linkedRawObjectIndex =
                            findMm9RawObjectIndexBySourceObjectIndex(
                                sidecars.rawObjects,
                                static_cast<int>(modelInstance.sourceObjectIndex));

                        for (size_t eventObjectIndex = 0; eventObjectIndex < sidecars.events.objects.size();
                            ++eventObjectIndex)
                        {
                            const Game::Mm9EventObject &eventObject = sidecars.events.objects[eventObjectIndex];

                            if (eventObject.sourceObjectIndex == static_cast<int>(modelInstance.sourceObjectIndex))
                            {
                                linkedEventObjectIndex = eventObjectIndex;
                                linkedMechanismIndex =
                                    findMm9MechanismIndexByObjectId(sidecars.events, eventObject.objectId);
                                break;
                            }
                        }
                    }

                    if (beginInspectorSectionBlock("Actor/Monster Variant"))
                    {
                        const auto renderActorRowField =
                            [this](const char *pLabel, const std::string &value)
                        {
                            renderInspectorCopyableReadOnlyField(
                                pLabel,
                                value.empty() ? std::string("<none>") : value);
                        };
                        std::string footSoundSourcePaths;
                        for (const Mm9ResolvedModelInstanceActorSource::ActorSoundReference &reference :
                            resolvedSource.actorRow.footSoundReferences)
                        {
                            if (!footSoundSourcePaths.empty())
                            {
                                footSoundSourcePaths += "; ";
                            }
                            footSoundSourcePaths += reference.sourcePath;
                        }
                        const bool actorVariantCandidate =
                            canResolveMm9ModelInstanceActorSource(modelInstance, pActorSourceLookup);
                        const bool actorRowEvidence =
                            !resolvedSource.actorRow.table.empty()
                            || !resolvedSource.actorRow.row.empty()
                            || !resolvedSource.actorRow.number.empty()
                            || !resolvedSource.actorRow.monsterName.empty()
                            || !resolvedSource.actorRow.typePicture.empty();
                        const bool actorGameplayIdentity =
                            !resolvedSource.actorRow.level.empty()
                            || !resolvedSource.actorRow.hitPoints.empty()
                            || !resolvedSource.actorRow.armorClass.empty()
                            || !resolvedSource.actorRow.experience.empty()
                            || !resolvedSource.actorRow.speed.empty()
                            || !resolvedSource.actorRow.scriptName.empty()
                            || !resolvedSource.actorRow.footSound.empty()
                            || !resolvedSource.actorRow.isMonster.empty()
                            || !resolvedSource.actorRow.hostilityGroup.empty()
                            || !resolvedSource.actorRow.voiceRadius.empty();
                        const bool missingFootSoundSource =
                            resolvedSource.inferredFromActorClass
                            && mm9ActorFootSoundRequiresResolution(resolvedSource.actorRow.footSound)
                            && resolvedSource.actorRow.footSoundReferences.empty();
                        const bool completeVariant =
                            !resolvedSource.sourceModel.empty()
                            && !resolvedSource.sourceSkin.empty()
                            && (!resolvedSource.inferredFromActorClass || !resolvedSource.actorRow.row.empty());
                        const Game::Mm9EventScript *pActorEventScript = nullptr;

                        if (document.hasMm9DatLoadedSidecars())
                        {
                            pActorEventScript =
                                findMm9EventScriptById(
                                    document.mm9DatLoadedSidecars().events,
                                    resolvedSource.actorRow.scriptName);
                        }

                        const size_t hostilityRegisteredTriggerCount =
                            pActorEventScript != nullptr
                                ? countMm9HostilityRegisteredTriggers(*pActorEventScript)
                                : 0;
                        const size_t hostilityTriggerEdgeCount =
                            pActorEventScript != nullptr ? countMm9HostilityTriggerEdges(*pActorEventScript) : 0;
                        const size_t hostilityIncludeCount =
                            pActorEventScript != nullptr ? countMm9HostilityIncludes(*pActorEventScript) : 0;
                        const bool hasActorTableHostility =
                            !trimCopy(resolvedSource.actorRow.hostilityGroup).empty();
                        const bool hasScriptHostility =
                            hostilityRegisteredTriggerCount > 0
                            || hostilityTriggerEdgeCount > 0
                            || hostilityIncludeCount > 0;
                        std::string hostilitySemantics = "<none>";

                        if (hasActorTableHostility && hasScriptHostility)
                        {
                            hostilitySemantics = "actor-table group plus generated-script hostility callbacks";
                        }
                        else if (hasActorTableHostility)
                        {
                            hostilitySemantics = "actor-table hostility group";
                        }
                        else if (hasScriptHostility)
                        {
                            hostilitySemantics = "generated-script hostility callbacks";
                        }

                        std::string variantDiagnosticSeverity = "none";
                        std::string variantDiagnosticResolver = "<none>";
                        std::string variantDiagnosticMessage = "<none>";

                        if (actorVariantCandidate && !resolvedSource.inferredFromActorClass)
                        {
                            variantDiagnosticSeverity = "error";
                            variantDiagnosticResolver = "mm9_actor_variant_resolver";
                            variantDiagnosticMessage =
                                "actor/monster variant is unresolved: class="
                                + modelInstance.sourceClass
                                + " name="
                                + modelInstance.sourceName
                                + " model="
                                + modelInstance.sourceModel
                                + " skin="
                                + modelInstance.sourceSkin;
                        }
                        else if (resolvedSource.inferredFromActorClass && !actorRowEvidence)
                        {
                            variantDiagnosticSeverity = "error";
                            variantDiagnosticResolver = "mm9_actor_variant_resolver";
                            variantDiagnosticMessage =
                                "actor/monster variant has no official actor-table row evidence";
                        }
                        else if (actorVariantCandidate && !actorGameplayIdentity)
                        {
                            variantDiagnosticSeverity = "error";
                            variantDiagnosticResolver = "mm9_actor_variant_resolver";
                            variantDiagnosticMessage =
                                "actor/monster variant has no gameplay identity row fields";
                        }
                        else if (missingFootSoundSource)
                        {
                            variantDiagnosticSeverity = "error";
                            variantDiagnosticResolver = "mm9_actor_variant_sound_resolver";
                            variantDiagnosticMessage =
                                "actor/monster foot sound is unresolved: "
                                + resolvedSource.actorRow.footSound;
                        }

                        if (beginInspectorPropertyTable("Mm9ActorVariantFields"))
                        {
                            renderInspectorReadOnlyField("Complete", completeVariant ? "true" : "false");
                            renderInspectorReadOnlyField(
                                "Actor Variant Candidate",
                                actorVariantCandidate ? "true" : "false");
                            renderInspectorCopyableReadOnlyField(
                                "Variant Diagnostic Severity",
                                variantDiagnosticSeverity);
                            renderInspectorCopyableReadOnlyField(
                                "Variant Diagnostic Resolver",
                                variantDiagnosticResolver);
                            renderInspectorCopyableReadOnlyField(
                                "Variant Diagnostic Message",
                                variantDiagnosticMessage);
                            renderInspectorCopyableReadOnlyField(
                                "Variant Id",
                                resolvedSource.variantId.empty()
                                    ? std::string("<object source>")
                                    : resolvedSource.variantId);
                            renderInspectorReadOnlyField(
                                "Resolution",
                                resolvedSource.inferredFromActorClass ? "actor table" : "object source");
                            renderInspectorCopyableReadOnlyField(
                                "Actor Table",
                                resolvedSource.actorRow.table.empty()
                                    ? std::string("<none>")
                                    : resolvedSource.actorRow.table);
                            renderInspectorCopyableReadOnlyField(
                                "Actor Row",
                                resolvedSource.actorRow.row.empty()
                                    ? std::string("<none>")
                                    : resolvedSource.actorRow.row);
                            renderInspectorCopyableReadOnlyField(
                                "Actor Number",
                                resolvedSource.actorRow.number.empty()
                                    ? std::string("<none>")
                                    : resolvedSource.actorRow.number);
                            renderInspectorCopyableReadOnlyField(
                                "Monster Name",
                                resolvedSource.actorRow.monsterName.empty()
                                    ? std::string("<none>")
                                    : resolvedSource.actorRow.monsterName);
                            renderInspectorCopyableReadOnlyField(
                                "Type Picture",
                                resolvedSource.actorRow.typePicture.empty()
                                    ? std::string("<none>")
                                    : resolvedSource.actorRow.typePicture);
                            renderInspectorCopyableReadOnlyField(
                                "Base Name",
                                resolvedSource.actorRow.baseName.empty()
                                    ? std::string("<none>")
                                    : resolvedSource.actorRow.baseName);
                            renderInspectorCopyableReadOnlyField(
                                "Level",
                                resolvedSource.actorRow.level.empty()
                                    ? std::string("<none>")
                                    : resolvedSource.actorRow.level);
                            renderInspectorCopyableReadOnlyField(
                                "Hit Points",
                                resolvedSource.actorRow.hitPoints.empty()
                                    ? std::string("<none>")
                                    : resolvedSource.actorRow.hitPoints);
                            renderInspectorCopyableReadOnlyField(
                                "Armor Class",
                                resolvedSource.actorRow.armorClass.empty()
                                    ? std::string("<none>")
                                    : resolvedSource.actorRow.armorClass);
                            renderInspectorCopyableReadOnlyField(
                                "Experience",
                                resolvedSource.actorRow.experience.empty()
                                    ? std::string("<none>")
                                    : resolvedSource.actorRow.experience);
                            renderInspectorCopyableReadOnlyField(
                                "Speed",
                                resolvedSource.actorRow.speed.empty()
                                    ? std::string("<none>")
                                    : resolvedSource.actorRow.speed);
                            renderInspectorCopyableReadOnlyField(
                                "Hostility Group",
                                resolvedSource.actorRow.hostilityGroup.empty()
                                    ? std::string("<none>")
                                    : resolvedSource.actorRow.hostilityGroup);
                            renderInspectorCopyableReadOnlyField(
                                "Faction Semantics Source",
                                hasActorTableHostility
                                    ? std::string("ACTOR/MONSTERS Hostility Group")
                                    : std::string("<none>"));
                            renderInspectorCopyableReadOnlyField(
                                "Team/Alignment Columns",
                                "no explicit ACTOR/MONSTERS team/alignment columns");
                            renderInspectorCopyableReadOnlyField(
                                "Hostility Runtime Source",
                                hostilitySemantics);
                            renderInspectorCopyableReadOnlyField(
                                "Is Monster",
                                resolvedSource.actorRow.isMonster.empty()
                                    ? std::string("<none>")
                                    : resolvedSource.actorRow.isMonster);
                            renderInspectorCopyableReadOnlyField(
                                "Script",
                                resolvedSource.actorRow.scriptName.empty()
                                    ? std::string("<none>")
                                    : resolvedSource.actorRow.scriptName);
                            renderInspectorCopyableReadOnlyField(
                                "Generated Script Matched",
                                pActorEventScript != nullptr ? "true" : "false");
                            renderInspectorCopyableReadOnlyField(
                                "Generated Script Source",
                                pActorEventScript != nullptr && !pActorEventScript->sourcePath.empty()
                                    ? pActorEventScript->sourcePath
                                    : std::string("<none>"));
                            renderInspectorCopyableReadOnlyField(
                                "Generated Script Includes",
                                pActorEventScript != nullptr
                                    ? mm9ScriptIncludePathsText(*pActorEventScript)
                                    : std::string("<none>"));
                            renderInspectorCopyableReadOnlyField(
                                "Hostility Includes",
                                std::to_string(hostilityIncludeCount));
                            renderInspectorCopyableReadOnlyField(
                                "Hostility Registered Triggers",
                                std::to_string(hostilityRegisteredTriggerCount));
                            renderInspectorCopyableReadOnlyField(
                                "Hostility Trigger Edges",
                                std::to_string(hostilityTriggerEdgeCount));
                            renderInspectorCopyableReadOnlyField(
                                "Foot Sound",
                                resolvedSource.actorRow.footSound.empty()
                                    ? std::string("<none>")
                                    : resolvedSource.actorRow.footSound);
                            renderInspectorCopyableReadOnlyField(
                                "Foot Sound Source Count",
                                std::to_string(resolvedSource.actorRow.footSoundReferences.size()));
                            renderInspectorCopyableReadOnlyField(
                                "Foot Sound Sources",
                                footSoundSourcePaths.empty()
                                    ? std::string("<none>")
                                    : footSoundSourcePaths);
                            renderInspectorCopyableReadOnlyField(
                                "Voice Radius",
                                resolvedSource.actorRow.voiceRadius.empty()
                                    ? std::string("<none>")
                                    : resolvedSource.actorRow.voiceRadius);
                            renderActorRowField("Treasure Type", resolvedSource.actorRow.treasureType);
                            renderActorRowField("Treasure Level", resolvedSource.actorRow.treasureLevel);
                            renderActorRowField("Quest", resolvedSource.actorRow.quest);
                            renderActorRowField("Fly", resolvedSource.actorRow.fly);
                            renderActorRowField("Move", resolvedSource.actorRow.move);
                            renderActorRowField("Walk Velocity", resolvedSource.actorRow.walkVelocity);
                            renderActorRowField("Run Velocity", resolvedSource.actorRow.runVelocity);
                            renderActorRowField("Fly Velocity", resolvedSource.actorRow.flyVelocity);
                            renderActorRowField("Lunge Velocity", resolvedSource.actorRow.lungeVelocity);
                            renderActorRowField("Attack Reach", resolvedSource.actorRow.attackReach);
                            renderActorRowField("Attack Range", resolvedSource.actorRow.attackRange);
                            renderActorRowField("Recovery", resolvedSource.actorRow.recovery);
                            renderActorRowField("Target Preference", resolvedSource.actorRow.targetPreference);
                            renderActorRowField("Bonus", resolvedSource.actorRow.bonus);
                            renderActorRowField("Alert Radius", resolvedSource.actorRow.alertRadius);
                            renderActorRowField("Accuracy", resolvedSource.actorRow.accuracy);
                            renderActorRowField("Foot Radius", resolvedSource.actorRow.footRadius);
                            renderActorRowField("Transparent", resolvedSource.actorRow.transparent);
                            renderActorRowField("Head Turn", resolvedSource.actorRow.headTurn);
                            renderActorRowField("Special", resolvedSource.actorRow.special);
                            renderActorRowField("Scale", resolvedSource.actorRow.scale);
                            renderActorRowField("Evade Chance", resolvedSource.actorRow.evadeChance);
                            renderActorRowField("Strafe Attack Pct", resolvedSource.actorRow.strafeAttackPct);
                            renderInspectorCopyableReadOnlyField("Resolved Model", resolvedSource.sourceModel);
                            renderInspectorCopyableReadOnlyField("Resolved Skin", resolvedSource.sourceSkin);
                            renderInspectorCopyOpenReadOnlyField(
                                "Generated Variant Asset",
                                resolvedAsset,
                                resolvedAssetOpenPath);
                            renderInspectorCopyableReadOnlyField(
                                "Source Object Index",
                                std::to_string(modelInstance.sourceObjectIndex));
                            ImGui::EndTable();
                        }

                        if (renderInspectorJumpButton("Select Raw Object", linkedRawObjectIndex.has_value()))
                        {
                            session.select(EditorSelectionKind::Mm9RawObject, *linkedRawObjectIndex);
                        }

                        ImGui::SameLine();

                        if (renderInspectorJumpButton("Select Event Object", linkedEventObjectIndex.has_value()))
                        {
                            session.select(EditorSelectionKind::Mm9EventObject, *linkedEventObjectIndex);
                        }

                        ImGui::SameLine();

                        if (renderInspectorJumpButton("Select Mechanism", linkedMechanismIndex.has_value()))
                        {
                            session.select(EditorSelectionKind::Mm9Mechanism, *linkedMechanismIndex);
                        }

                        endInspectorSectionBlock();
                    }

                    if (beginInspectorSectionBlock("Variant Source Assets", false))
                    {
                        size_t variantAssetReferenceCount = 0;

                        for (const EditorMm9RawObjectAssetReferenceStatus &status :
                            document.mm9RawObjectAssetReferenceStatuses())
                        {
                            if (status.sourceObjectIndex != modelInstance.sourceObjectIndex
                                || (status.sourceFamily != "models"
                                    && status.sourceFamily != "skins"
                                    && status.sourceFamily != "sounds"
                                    && status.sourceFamily != "voices"))
                            {
                                continue;
                            }

                            if (variantAssetReferenceCount == 0)
                            {
                                if (!ImGui::BeginTable(
                                        "Mm9ActorVariantSourceAssets",
                                        7,
                                        ImGuiTableFlags_SizingStretchProp))
                                {
                                    break;
                                }

                                ImGui::TableSetupColumn("Family", ImGuiTableColumnFlags_WidthFixed, 84.0f);
                                ImGui::TableSetupColumn("Property", ImGuiTableColumnFlags_WidthStretch);
                                ImGui::TableSetupColumn("Raw Value", ImGuiTableColumnFlags_WidthStretch);
                                ImGui::TableSetupColumn("Required", ImGuiTableColumnFlags_WidthFixed, 72.0f);
                                ImGui::TableSetupColumn("Resolved", ImGuiTableColumnFlags_WidthFixed, 72.0f);
                                ImGui::TableSetupColumn("Ambiguous", ImGuiTableColumnFlags_WidthFixed, 82.0f);
                                ImGui::TableSetupColumn("Source Path", ImGuiTableColumnFlags_WidthStretch);
                                ImGui::TableHeadersRow();
                            }

                            ++variantAssetReferenceCount;
                            ImGui::TableNextRow();
                            ImGui::TableSetColumnIndex(0);
                            ImGui::TextUnformatted(status.sourceFamily.c_str());
                            ImGui::TableSetColumnIndex(1);
                            ImGui::TextUnformatted(status.propertyName.c_str());
                            ImGui::TableSetColumnIndex(2);
                            ImGui::TextUnformatted(status.sourceValue.c_str());
                            ImGui::TableSetColumnIndex(3);
                            ImGui::TextUnformatted(status.required ? "true" : "false");
                            ImGui::TableSetColumnIndex(4);
                            ImGui::TextUnformatted(status.resolved ? "true" : "false");
                            ImGui::TableSetColumnIndex(5);
                            ImGui::TextUnformatted(status.ambiguous ? "true" : "false");
                            ImGui::TableSetColumnIndex(6);
                            ImGui::TextUnformatted(status.resolvedSourcePath.c_str());
                        }

                        if (variantAssetReferenceCount > 0)
                        {
                            ImGui::EndTable();
                        }
                        else
                        {
                            ImGui::TextDisabled(
                                "No model, skin, sound, or voice source-asset references for this instance.");
                        }

                        endInspectorSectionBlock();
                    }
                }
                else if (resolvedSource.inferredFromActorClass)
                {
                    ImGui::Separator();
                    ImGui::Text("Resolved Model: %s", resolvedSource.sourceModel.c_str());
                    ImGui::Text("Resolved Skin: %s", resolvedSource.sourceSkin.c_str());
                    ImGui::Text(
                        "Resolved Asset: %s",
                        mm9ModelInstanceActorVariantAssetPath(
                            resolvedSource.sourceModel,
                            resolvedSource.sourceSkin).c_str());
                }

                ImGui::Text("Position: %d, %d, %d", modelInstance.x, modelInstance.y, modelInstance.z);
            }
        }
        break;

    case EditorSelectionKind::Mm9WorldModel:
        renderMm9DatWorldModelInspector(session, session.selection().index);
        break;

    case EditorSelectionKind::Mm9DatPolygon:
        renderMm9DatPolygonInspector(session, session.selection().index);
        break;

    case EditorSelectionKind::Mm9MaterialTexture:
        renderMm9MaterialTextureInspector(session, session.selection().index);
        break;

    case EditorSelectionKind::Mm9RawObject:
        renderMm9RawObjectInspector(session, session.selection().index);
        break;

    case EditorSelectionKind::Mm9EventObject:
        renderMm9EventObjectInspector(session, session.selection().index);
        break;

    case EditorSelectionKind::Mm9Mechanism:
        renderMm9MechanismInspector(session, session.selection().index);
        break;

    case EditorSelectionKind::Mm9EventScript:
        renderMm9EventScriptInspector(session, session.selection().index);
        break;
    }

    ImGui::End();
}

void EditorMainWindow::renderLogPanel(
    const EditorSession &session,
    uint32_t frameNumber,
    float deltaSeconds,
    const std::string &rendererName)
{
    ImGui::SetNextWindowDockID(editorDockspaceId(), ImGuiCond_FirstUseEver);

    if (!ImGui::Begin("Log"))
    {
        ImGui::End();
        return;
    }

    ImGui::Text("Frame: %u", frameNumber);
    ImGui::Text("Delta: %.3f ms", deltaSeconds * 1000.0f);
    ImGui::Text("Renderer: %s", rendererName.c_str());

    for (const std::string &message : session.logMessages())
    {
        ImGui::TextWrapped("%s", message.c_str());
    }

    if (!session.validationMessages().empty())
    {
        ImGui::Separator();
        ImGui::Text("Validation Issues: %zu", session.validationMessages().size());

        for (const std::string &message : session.validationMessages())
        {
            ImGui::BulletText("%s", message.c_str());
        }
    }

    ImGui::End();
}

void EditorMainWindow::renderViewportPanel(EditorSession &session, float deltaSeconds)
{
    const ImGuiWindowFlags flags = ImGuiWindowFlags_NoScrollbar | ImGuiWindowFlags_NoScrollWithMouse;
    ImGui::SetNextWindowBgAlpha(0.08f);

    if (!ImGui::Begin("Viewport", nullptr, flags))
    {
        ImGui::End();
        return;
    }

    const ImVec2 viewportOrigin = ImGui::GetCursorScreenPos();
    const ImVec2 viewportSize = ImGui::GetContentRegionAvail();
    m_viewportX = static_cast<int>(viewportOrigin.x);
    m_viewportY = static_cast<int>(viewportOrigin.y);
    m_viewportWidth = static_cast<uint16_t>(std::max(viewportSize.x, 1.0f));
    m_viewportHeight = static_cast<uint16_t>(std::max(viewportSize.y, 1.0f));

    ImGui::InvisibleButton(
        "ViewportSurface",
        viewportSize,
        ImGuiButtonFlags_MouseButtonLeft | ImGuiButtonFlags_MouseButtonRight);
    const bool isHovered = ImGui::IsItemHovered();
    const bool isFocused = ImGui::IsWindowFocused(ImGuiFocusedFlags_RootAndChildWindows);
    const bool leftMouseClicked = isHovered && ImGui::IsMouseClicked(ImGuiMouseButton_Left);
    const bool leftMouseDown = isHovered && ImGui::IsMouseDown(ImGuiMouseButton_Left);
    const ImVec2 mousePosition = ImGui::GetIO().MousePos;
    m_viewport.updateAndRender(
        session,
        m_viewportX,
        m_viewportY,
        m_viewportWidth,
        m_viewportHeight,
        isHovered,
        isFocused,
        leftMouseClicked,
        leftMouseDown,
        mousePosition.x,
        mousePosition.y,
        deltaSeconds);
    if (bgfx::isValid(m_viewport.viewportTextureHandle()))
    {
        ImGui::GetWindowDrawList()->AddImage(
            static_cast<ImTextureID>(static_cast<uintptr_t>(m_viewport.viewportTextureHandle().idx + 1)),
            viewportOrigin,
            ImVec2(viewportOrigin.x + viewportSize.x, viewportOrigin.y + viewportSize.y),
            ImVec2(0.0f, 1.0f),
            ImVec2(1.0f, 0.0f));
    }

    ImGui::SetCursorScreenPos(ImVec2(viewportOrigin.x + 12.0f, viewportOrigin.y + 12.0f));
    ImGui::PushStyleColor(ImGuiCol_ChildBg, ImVec4(0.06f, 0.07f, 0.08f, 0.80f));
    ImGui::PushStyleColor(ImGuiCol_Border, colorFromRgb(0x343B45));
    if (ImGui::BeginChild(
            "ViewportOverlay",
            ImVec2(328.0f, 74.0f),
            ImGuiChildFlags_Borders,
            ImGuiWindowFlags_NoScrollbar | ImGuiWindowFlags_NoScrollWithMouse))
    {
        m_viewport.renderOverlayUi(session);
    }
    ImGui::EndChild();
    ImGui::PopStyleColor(2);
    ImGui::End();
}

void EditorMainWindow::renderDocumentSummary(EditorSession &session)
{
    const EditorDocument &document = session.document();

    if (document.kind() == EditorDocument::Kind::Mm9Dat)
    {
        renderMm9DatDocumentSummary(session);
        return;
    }

    if (document.kind() == EditorDocument::Kind::Indoor)
    {
        renderIndoorDocumentSummary(session);
        return;
    }

    const Game::OutdoorMapData &outdoorGeometry = document.outdoorGeometry();
    const Game::OutdoorSceneData &sceneData = document.outdoorSceneData();

    size_t totalFaceCount = 0;

    for (const Game::OutdoorBModel &bmodel : outdoorGeometry.bmodels)
    {
        totalFaceCount += bmodel.faces.size();
    }

    ImGui::Text("Map: %s", document.displayName().c_str());
    ImGui::Text("Scene: %s", document.sceneVirtualPath().c_str());
    ImGui::Spacing();
    ImGui::Text("BModels: %zu", outdoorGeometry.bmodels.size());
    ImGui::Text("Faces: %zu", totalFaceCount);
    ImGui::Text("Entities: %zu", sceneData.entities.size());
    ImGui::Text("Spawns: %zu", sceneData.spawns.size());
    ImGui::Text("Model Instances: %zu", sceneData.modelInstances.size());
    ImGui::Text("Actors: %zu", sceneData.initialState.actors.size());
    ImGui::Text("Sprite Objects: %zu", sceneData.initialState.spriteObjects.size());
    ImGui::Text("Chests: %zu", sceneData.initialState.chests.size());
    ImGui::Text("Terrain Overrides: %zu", sceneData.terrainAttributeOverrides.size());
    ImGui::Text("Dirty: %s", document.isDirty() ? "yes" : "no");

    if (!session.validationMessages().empty())
    {
        ImGui::Spacing();
        ImGui::Text("Validation Issues: %zu", session.validationMessages().size());

        const size_t issueCountToShow = std::min<size_t>(session.validationMessages().size(), 6);

        for (size_t index = 0; index < issueCountToShow; ++index)
        {
            ImGui::BulletText("%s", session.validationMessages()[index].c_str());
        }
    }
}

void EditorMainWindow::renderMm9DatDocumentSummary(EditorSession &session)
{
    const EditorDocument &document = session.document();
    const EditorMm9DatLevelMetadata &metadata = document.mm9DatLevelMetadata();
    const Mm9ReferenceValidationUiSummary referenceValidationSummary =
        collectMm9ReferenceValidationUiSummary(session, document);
    const size_t referenceValidationBlockingIssues =
        mm9ReferenceValidationBlockingIssueCount(referenceValidationSummary);
    const std::vector<Mm9NormalizedDiagnosticUiEntry> diagnostics =
        collectMm9NormalizedDiagnostics(session, document);

    if (beginInspectorSectionBlock("Level"))
    {
        if (beginInspectorPropertyTable("Mm9DatLevelFields"))
        {
            renderInspectorReadOnlyField("Kind", metadata.kind);
            renderInspectorReadOnlyField("Map Id", metadata.mapId);
            renderInspectorReadOnlyField("Display Name", metadata.displayName);
            renderInspectorReadOnlyField("Runtime Backend", metadata.runtime.worldBackend);
            renderInspectorReadOnlyField("Classification", metadata.runtime.classification);
            renderInspectorReadOnlyField("Confidence", metadata.runtime.classificationConfidence);
            renderInspectorReadOnlyField("Visibility", metadata.runtime.visibility);
            renderInspectorReadOnlyField("Collision", metadata.runtime.collision);
            renderInspectorReadOnlyField("Render", metadata.runtime.render);
            renderInspectorReadOnlyField("Sky", metadata.runtime.sky ? "true" : "false");
            ImGui::EndTable();
        }
        endInspectorSectionBlock();
    }

    if (beginInspectorSectionBlock("Reference Validation"))
    {
        if (beginInspectorPropertyTable("Mm9ReferenceValidationFields"))
        {
            renderInspectorReadOnlyField(
                "Blocking Issues",
                std::to_string(referenceValidationBlockingIssues));
            renderInspectorReadOnlyField(
                "Missing Document Paths",
                std::to_string(referenceValidationSummary.missingDocumentPaths));
            renderInspectorReadOnlyField(
                "Source Manifest Issues",
                std::to_string(referenceValidationSummary.sourceManifestIssues));
            renderInspectorReadOnlyField(
                "Asset Graph Blocking",
                std::to_string(referenceValidationSummary.assetGraphBlockingIssues));
            renderInspectorReadOnlyField(
                "Material Blocking",
                std::to_string(referenceValidationSummary.materialBlockingIssues));
            renderInspectorReadOnlyField(
                "Raw Object Asset Blocking",
                std::to_string(referenceValidationSummary.rawObjectAssetBlockingIssues));
            renderInspectorReadOnlyField(
                "Document Validation Issues",
                std::to_string(referenceValidationSummary.documentValidationIssues));
            renderInspectorReadOnlyField(
                "Warnings",
                std::to_string(referenceValidationSummary.materialWarnings));
            ImGui::EndTable();
        }

        if (ImGui::Button("Validate Referenced Sidecars And Assets", ImVec2(280.0f, 0.0f)))
        {
            if (referenceValidationBlockingIssues == 0)
            {
                setStatusMessage(
                    StatusMessageKind::Success,
                    "MM9 referenced sidecars and required assets validate cleanly.");
            }
            else
            {
                setStatusMessage(
                    StatusMessageKind::Error,
                    "MM9 reference validation found "
                        + std::to_string(referenceValidationBlockingIssues)
                        + " blocking issue(s).");
            }
        }

        endInspectorSectionBlock();
    }

    if (beginInspectorSectionBlock("Diagnostics", false))
    {
        size_t errorCount = 0;
        size_t warningCount = 0;
        size_t infoCount = 0;

        for (const Mm9NormalizedDiagnosticUiEntry &diagnostic : diagnostics)
        {
            if (diagnostic.severity == "error")
            {
                ++errorCount;
            }
            else if (diagnostic.severity == "warning")
            {
                ++warningCount;
            }
            else
            {
                ++infoCount;
            }
        }

        if (beginInspectorPropertyTable("Mm9NormalizedDiagnosticSummary"))
        {
            renderInspectorReadOnlyField("Total", std::to_string(diagnostics.size()));
            renderInspectorReadOnlyField("Errors", std::to_string(errorCount));
            renderInspectorReadOnlyField("Warnings", std::to_string(warningCount));
            renderInspectorReadOnlyField("Info", std::to_string(infoCount));
            ImGui::EndTable();
        }

        const std::vector<EditorMm9DiagnosticSeverityRule> &severityRules = mm9DiagnosticSeverityRules();
        if (!severityRules.empty()
            && ImGui::BeginTable("Mm9DiagnosticSeverityPolicy", 4, ImGuiTableFlags_SizingStretchProp))
        {
            ImGui::TableSetupColumn("Severity", ImGuiTableColumnFlags_WidthFixed, 72.0f);
            ImGui::TableSetupColumn("Blocks", ImGuiTableColumnFlags_WidthFixed, 56.0f);
            ImGui::TableSetupColumn("Owner", ImGuiTableColumnFlags_WidthStretch, 0.25f);
            ImGui::TableSetupColumn("Category", ImGuiTableColumnFlags_WidthStretch, 0.75f);
            ImGui::TableHeadersRow();

            for (const EditorMm9DiagnosticSeverityRule &rule : severityRules)
            {
                ImGui::TableNextRow();
                ImGui::TableSetColumnIndex(0);
                ImGui::TextUnformatted(rule.severity.c_str());
                ImGui::TableSetColumnIndex(1);
                ImGui::TextUnformatted(rule.blocksCleanValidation ? "yes" : "no");
                ImGui::TableSetColumnIndex(2);
                ImGui::TextUnformatted(rule.suggestedOwner.c_str());
                ImGui::TableSetColumnIndex(3);
                ImGui::TextWrapped("%s", rule.category.c_str());
            }

            ImGui::EndTable();
        }

        if (diagnostics.empty())
        {
            ImGui::TextDisabled("No normalized diagnostics.");
        }
        else if (ImGui::BeginTable("Mm9NormalizedDiagnostics", 7, ImGuiTableFlags_SizingStretchProp))
        {
            ImGui::TableSetupColumn("Severity", ImGuiTableColumnFlags_WidthFixed, 72.0f);
            ImGui::TableSetupColumn("Source", ImGuiTableColumnFlags_WidthStretch, 0.18f);
            ImGui::TableSetupColumn("Index", ImGuiTableColumnFlags_WidthStretch, 0.16f);
            ImGui::TableSetupColumn("Sidecar", ImGuiTableColumnFlags_WidthStretch, 0.18f);
            ImGui::TableSetupColumn("Resolver", ImGuiTableColumnFlags_WidthStretch, 0.18f);
            ImGui::TableSetupColumn("Owner", ImGuiTableColumnFlags_WidthStretch, 0.14f);
            ImGui::TableSetupColumn("Message", ImGuiTableColumnFlags_WidthStretch, 0.28f);
            ImGui::TableHeadersRow();

            for (const Mm9NormalizedDiagnosticUiEntry &diagnostic : diagnostics)
            {
                const uint32_t severityColor =
                    diagnostic.severity == "error" ? 0xE7A46C
                    : (diagnostic.severity == "warning" ? 0xD8B277 : 0xAAB3BD);

                ImGui::TableNextRow();
                ImGui::TableSetColumnIndex(0);
                ImGui::TextColored(colorFromRgb(severityColor), "%s", diagnostic.severity.c_str());
                ImGui::TableSetColumnIndex(1);
                ImGui::TextUnformatted(diagnostic.sourceFile.c_str());
                ImGui::TableSetColumnIndex(2);
                ImGui::TextUnformatted(diagnostic.sourceIndexPath.c_str());
                ImGui::TableSetColumnIndex(3);
                ImGui::TextUnformatted(diagnostic.sidecarPath.c_str());
                ImGui::TableSetColumnIndex(4);
                ImGui::TextUnformatted(diagnostic.resolver.c_str());
                ImGui::TableSetColumnIndex(5);
                ImGui::TextUnformatted(diagnostic.suggestedOwner.c_str());
                ImGui::TableSetColumnIndex(6);
                ImGui::TextWrapped("%s", diagnostic.message.c_str());
            }

            ImGui::EndTable();
        }

        endInspectorSectionBlock();
    }

    if (beginInspectorSectionBlock("Source"))
    {
        if (beginInspectorPropertyTable("Mm9DatSourceFields"))
        {
            renderInspectorCopyOpenReadOnlyField(
                "Level",
                document.sceneVirtualPath(),
                document.scenePhysicalPath().generic_string());
            renderInspectorCopyOpenReadOnlyField(
                "DAT",
                metadata.source.dat,
                resolveMm9LevelRelativePath(document, metadata.source.dat).generic_string());
            renderInspectorCopyOpenReadOnlyField(
                "Original DAT",
                metadata.source.originalDat,
                resolveMm9LevelRelativePath(document, metadata.source.originalDat).generic_string());
            renderInspectorReadOnlyField("DAT Version", std::to_string(metadata.source.datVersion));
            renderInspectorCopyableReadOnlyField("Content Hash", metadata.source.contentHash);
            renderInspectorReadOnlyField("Source Game", metadata.source.sourceGame);
            renderInspectorReadOnlyField(
                "Sidecars Loaded",
                document.hasMm9DatLoadedSidecars() ? "true" : "false");
            renderInspectorReadOnlyField(
                "Source DAT Parsed",
                document.hasMm9DatWorld() ? "true" : "false");

            if (document.hasMm9DatWorld())
            {
                renderInspectorReadOnlyField(
                    "Native DAT Models",
                    std::to_string(document.mm9DatWorld().worldModels.size()));
                renderInspectorReadOnlyField(
                    "Native Mesh Triangles",
                    std::to_string(document.mm9DatRenderMesh().triangles.size()));
            }

            ImGui::EndTable();
        }
        endInspectorSectionBlock();
    }

    if (beginInspectorSectionBlock("Document Paths"))
    {
        const std::vector<EditorMm9DocumentPathStatus> &pathStatuses = document.mm9DocumentPathStatuses();
        size_t readOnlySourceCount = 0;
        size_t generatedCount = 0;
        size_t authoredCount = 0;
        size_t compatibilityCount = 0;

        for (const EditorMm9DocumentPathStatus &status : pathStatuses)
        {
            if (status.sourceReadOnly)
            {
                ++readOnlySourceCount;
            }

            if (status.generated)
            {
                ++generatedCount;
            }

            if (status.authored)
            {
                ++authoredCount;
            }

            if (status.compatibilityDerived)
            {
                ++compatibilityCount;
            }
        }

        if (beginInspectorPropertyTable("Mm9DocumentPathSummary"))
        {
            renderInspectorReadOnlyField("Paths", std::to_string(pathStatuses.size()));
            renderInspectorReadOnlyField("Read-only Source", std::to_string(readOnlySourceCount));
            renderInspectorReadOnlyField("Generated", std::to_string(generatedCount));
            renderInspectorReadOnlyField("Authored", std::to_string(authoredCount));
            renderInspectorReadOnlyField("Derived Compat", std::to_string(compatibilityCount));
            ImGui::EndTable();
        }

        if (!pathStatuses.empty()
            && ImGui::BeginTable("Mm9DocumentPathStatuses", 6, ImGuiTableFlags_SizingStretchProp))
        {
            ImGui::TableSetupColumn("Label", ImGuiTableColumnFlags_WidthStretch, 0.18f);
            ImGui::TableSetupColumn("Role", ImGuiTableColumnFlags_WidthStretch, 0.22f);
            ImGui::TableSetupColumn("Path", ImGuiTableColumnFlags_WidthStretch, 0.42f);
            ImGui::TableSetupColumn("Exists", ImGuiTableColumnFlags_WidthFixed, 58.0f);
            ImGui::TableSetupColumn("Source", ImGuiTableColumnFlags_WidthFixed, 62.0f);
            ImGui::TableSetupColumn("Actions", ImGuiTableColumnFlags_WidthFixed, 112.0f);
            ImGui::TableHeadersRow();

            for (const EditorMm9DocumentPathStatus &status : pathStatuses)
            {
                ImGui::TableNextRow();
                ImGui::TableSetColumnIndex(0);
                ImGui::TextUnformatted(status.label.c_str());
                ImGui::TableSetColumnIndex(1);
                ImGui::TextUnformatted(status.role.c_str());
                ImGui::TableSetColumnIndex(2);
                ImGui::TextUnformatted(status.relativePath.c_str());
                ImGui::TableSetColumnIndex(3);
                ImGui::TextUnformatted(status.exists ? "yes" : "no");
                ImGui::TableSetColumnIndex(4);
                ImGui::TextUnformatted(status.sourceReadOnly ? "ro" : "w");
                ImGui::TableSetColumnIndex(5);
                renderInspectorCopyButton(
                    ("Mm9DocumentPathStatus" + status.label + status.relativePath).c_str(),
                    status.relativePath);
                ImGui::SameLine();
                renderInspectorOpenPathButton(
                    ("Mm9DocumentPathStatusOpen" + status.label + status.resolvedPath).c_str(),
                    status.resolvedPath);
            }

            ImGui::EndTable();
        }

        endInspectorSectionBlock();
    }

    if (beginInspectorSectionBlock("Source Manifest"))
    {
        const std::vector<EditorMm9SourceAssetFamilyStatus> &familyStatuses =
            document.mm9SourceAssetFamilyStatuses();
        size_t expectedTotal = 0;
        size_t actualTotal = 0;
        size_t mismatchCount = 0;
        size_t missingCount = 0;

        for (const EditorMm9SourceAssetFamilyStatus &status : familyStatuses)
        {
            expectedTotal += status.expectedFileCount;
            actualTotal += status.actualFileCount;

            if (!status.declared || !status.packageDirectoryExists)
            {
                ++missingCount;
            }
            else if (status.expectedFileCount != status.actualFileCount)
            {
                ++mismatchCount;
            }
        }

        if (beginInspectorPropertyTable("Mm9SourceManifestFields"))
        {
            renderInspectorCopyOpenReadOnlyField(
                "Manifest",
                document.mm9SourceAssetManifestPhysicalPath().generic_string(),
                document.mm9SourceAssetManifestPhysicalPath().generic_string());
            renderInspectorReadOnlyField(
                "Loaded",
                document.hasMm9SourceAssetManifest() ? "true" : "false");

            if (document.hasMm9SourceAssetManifest())
            {
                const EditorMm9SourceAssetManifest &manifest = document.mm9SourceAssetManifest();
                renderInspectorReadOnlyField("Kind", manifest.kind);
                renderInspectorReadOnlyField("Format", std::to_string(manifest.formatVersion));
                renderInspectorCopyableReadOnlyField("Source Root", manifest.sourceRoot);
                renderInspectorCopyableReadOnlyField("Package Root", manifest.packageRoot);
                renderInspectorReadOnlyField("Families", std::to_string(manifest.families.size()));
                renderInspectorReadOnlyField("Expected Files", std::to_string(expectedTotal));
                renderInspectorReadOnlyField("Actual Files", std::to_string(actualTotal));
                renderInspectorReadOnlyField("Missing Families", std::to_string(missingCount));
                renderInspectorReadOnlyField("Count Mismatches", std::to_string(mismatchCount));
                renderInspectorReadOnlyField(
                    "Source Truth",
                    manifest.policy.sourceTruth ? "true" : "false");
                renderInspectorReadOnlyField(
                    "Generated Cache",
                    manifest.policy.generatedCache ? "true" : "false");
            }

            ImGui::EndTable();
        }

        if (!familyStatuses.empty()
            && ImGui::BeginTable("Mm9SourceManifestFamilies", 6, ImGuiTableFlags_SizingStretchProp))
        {
            ImGui::TableSetupColumn("Family", ImGuiTableColumnFlags_WidthStretch, 0.18f);
            ImGui::TableSetupColumn("Source", ImGuiTableColumnFlags_WidthStretch, 0.24f);
            ImGui::TableSetupColumn("Package", ImGuiTableColumnFlags_WidthStretch, 0.24f);
            ImGui::TableSetupColumn("Expected", ImGuiTableColumnFlags_WidthFixed, 76.0f);
            ImGui::TableSetupColumn("Actual", ImGuiTableColumnFlags_WidthFixed, 76.0f);
            ImGui::TableSetupColumn("Actions", ImGuiTableColumnFlags_WidthFixed, 112.0f);
            ImGui::TableHeadersRow();

            for (const EditorMm9SourceAssetFamilyStatus &status : familyStatuses)
            {
                ImGui::TableNextRow();
                ImGui::TableSetColumnIndex(0);
                ImGui::TextUnformatted(status.id.c_str());
                ImGui::TableSetColumnIndex(1);
                ImGui::TextUnformatted(status.source.c_str());
                ImGui::TableSetColumnIndex(2);
                ImGui::TextUnformatted(status.package.c_str());
                ImGui::TableSetColumnIndex(3);
                ImGui::Text("%zu", status.expectedFileCount);
                ImGui::TableSetColumnIndex(4);
                ImGui::Text("%zu", status.actualFileCount);
                ImGui::TableSetColumnIndex(5);
                renderInspectorCopyButton(
                    ("Mm9SourceManifestFamily" + status.id).c_str(),
                    status.source.empty() ? status.package : status.source);
                ImGui::SameLine();
                renderInspectorOpenPathButton(
                    ("Mm9SourceManifestFamilyOpen" + status.id).c_str(),
                    (document.mm9SourceAssetManifestPhysicalPath().parent_path() / status.package).generic_string());
            }

            ImGui::EndTable();
        }

        if (!document.mm9SourceAssetManifestDiagnostics().empty())
        {
            ImGui::Text("Source Manifest Issues: %zu", document.mm9SourceAssetManifestDiagnostics().size());

            for (const std::string &message : document.mm9SourceAssetManifestDiagnostics())
            {
                ImGui::BulletText("%s", message.c_str());
            }
        }

        endInspectorSectionBlock();
    }

    if (document.hasMm9DatLoadedSidecars() && beginInspectorSectionBlock("Loaded Sidecars"))
    {
        const EditorMm9LoadedSidecars &sidecars = document.mm9DatLoadedSidecars();

        if (beginInspectorPropertyTable("Mm9DatLoadedSidecarCounts"))
        {
            renderInspectorReadOnlyField("World Models", std::to_string(sidecars.datWorld.worldModels.size()));
            renderInspectorReadOnlyField("DAT Objects", std::to_string(sidecars.datWorld.totals.objectCount));
            renderInspectorReadOnlyField("Source Polys", std::to_string(sidecars.datWorld.totals.sourcePolyCount));
            renderInspectorReadOnlyField("Surfaces", std::to_string(sidecars.datWorld.totals.surfaceCount));
            renderInspectorReadOnlyField("Leaves", std::to_string(sidecars.datWorld.totals.leafCount));
            renderInspectorReadOnlyField("User Portals", std::to_string(sidecars.datWorld.totals.userPortalCount));
            renderInspectorReadOnlyField(
                "Leaf References",
                std::to_string(sidecars.datWorld.totals.leafReferenceCount));
            renderInspectorReadOnlyField(
                "Invalid Leaf Refs",
                std::to_string(sidecars.datWorld.totals.invalidLeafReferenceCount));
            renderInspectorReadOnlyField("Raw Objects", std::to_string(sidecars.rawObjects.objects.size()));
            renderInspectorReadOnlyField(
                "Unknown Properties",
                std::to_string(sidecars.rawObjects.unknownPropertyCount));
            renderInspectorReadOnlyField("Materials", std::to_string(sidecars.materialAliases.textures.size()));
            renderInspectorReadOnlyField("Events Objects", std::to_string(sidecars.events.objects.size()));
            renderInspectorReadOnlyField("Mechanisms", std::to_string(sidecars.events.mechanismCount));
            renderInspectorReadOnlyField("Triggers", std::to_string(sidecars.events.triggerCount));
            renderInspectorReadOnlyField("Interactions", std::to_string(sidecars.events.interactionCount));
            renderInspectorReadOnlyField("Unresolved Events", std::to_string(sidecars.events.unresolvedCount));
            renderInspectorReadOnlyField(
                "Object Transforms",
                std::to_string(document.mm9ObjectLayer().positionedObjectCount));
            renderInspectorReadOnlyField(
                "Object Bounds",
                std::to_string(document.mm9ObjectLayer().boundsEvidenceObjectCount));
            renderInspectorReadOnlyField(
                "Trigger Volumes",
                std::to_string(document.mm9ObjectLayer().triggerVolumeCount));
            renderInspectorReadOnlyField("Light Objects", std::to_string(document.mm9LightLayer().lights.size()));
            renderInspectorReadOnlyField(
                "Static Render Lights",
                std::to_string(Game::buildMm9StaticRenderLights(document.mm9LightLayer()).size()));
            renderInspectorReadOnlyField(
                "Light Diagnostics",
                std::to_string(document.mm9LightLayer().diagnostics.size()));
            renderInspectorReadOnlyField("Sound Objects", std::to_string(document.mm9SoundLayer().objects.size()));
            renderInspectorReadOnlyField("Sound References", std::to_string(document.mm9SoundLayer().referenceCount));
            renderInspectorReadOnlyField(
                "Resolved Sound Refs",
                std::to_string(document.mm9SoundLayer().resolvedReferenceCount));
            renderInspectorReadOnlyField(
                "Unresolved Required Sound Refs",
                std::to_string(document.mm9SoundLayer().unresolvedRequiredReferenceCount));
            renderInspectorReadOnlyField(
                "Spawn Source Objects",
                std::to_string(document.mm9SpawnLayer().objects.size()));
            renderInspectorReadOnlyField(
                "Spawn NPC Numbers",
                std::to_string(document.mm9SpawnLayer().npcNumberCount));
            ImGui::EndTable();
        }
        endInspectorSectionBlock();
    }

    if (document.hasMm9DatLoadedSidecars() && beginInspectorSectionBlock("Unresolved Event Evidence", false))
    {
        const EditorMm9LoadedSidecars &sidecars = document.mm9DatLoadedSidecars();
        const std::vector<Game::Mm9EventUnresolved> &unresolvedEvents = sidecars.events.unresolved;

        if (unresolvedEvents.empty())
        {
            ImGui::TextDisabled("No unresolved generated event entries.");
        }
        else if (ImGui::BeginTable("Mm9UnresolvedEventEvidence", 8, ImGuiTableFlags_SizingStretchProp))
        {
            ImGui::TableSetupColumn("Kind", ImGuiTableColumnFlags_WidthStretch, 0.18f);
            ImGui::TableSetupColumn("Severity", ImGuiTableColumnFlags_WidthStretch, 0.10f);
            ImGui::TableSetupColumn("Source", ImGuiTableColumnFlags_WidthFixed, 72.0f);
            ImGui::TableSetupColumn("Name", ImGuiTableColumnFlags_WidthStretch, 0.18f);
            ImGui::TableSetupColumn("Class", ImGuiTableColumnFlags_WidthStretch, 0.14f);
            ImGui::TableSetupColumn("Rot Candidates", ImGuiTableColumnFlags_WidthFixed, 96.0f);
            ImGui::TableSetupColumn("Pos Candidates", ImGuiTableColumnFlags_WidthFixed, 96.0f);
            ImGui::TableSetupColumn("Actions", ImGuiTableColumnFlags_WidthFixed, 116.0f);
            ImGui::TableHeadersRow();

            for (size_t unresolvedIndex = 0; unresolvedIndex < unresolvedEvents.size(); ++unresolvedIndex)
            {
                const Game::Mm9EventUnresolved &entry = unresolvedEvents[unresolvedIndex];
                const std::optional<size_t> rawObjectIndex =
                    findMm9RawObjectIndexBySourceObjectIndex(sidecars.rawObjects, entry.sourceObjectIndex);

                ImGui::PushID(static_cast<int>(unresolvedIndex));
                ImGui::TableNextRow();
                ImGui::TableSetColumnIndex(0);
                ImGui::TextUnformatted(entry.kind.c_str());
                ImGui::TableSetColumnIndex(1);
                ImGui::TextUnformatted(entry.severity.empty() ? "<unknown>" : entry.severity.c_str());
                ImGui::TableSetColumnIndex(2);
                ImGui::Text("%d", entry.sourceObjectIndex);
                ImGui::TableSetColumnIndex(3);
                ImGui::TextUnformatted(entry.sourceName.c_str());
                ImGui::TableSetColumnIndex(4);
                ImGui::TextUnformatted(entry.sourceClass.c_str());
                ImGui::TableSetColumnIndex(5);
                ImGui::Text("%zu", entry.nearestMovableWorldModelsByRotationPoint.size());
                ImGui::TableSetColumnIndex(6);
                ImGui::Text("%zu", entry.nearestMovableWorldModelsByPosition.size());
                ImGui::TableSetColumnIndex(7);
                if (renderInspectorJumpButton("Select Raw", rawObjectIndex.has_value()))
                {
                    session.select(EditorSelectionKind::Mm9RawObject, *rawObjectIndex);
                }
                ImGui::PopID();
            }

            ImGui::EndTable();
        }

        for (size_t unresolvedIndex = 0; unresolvedIndex < unresolvedEvents.size(); ++unresolvedIndex)
        {
            const Game::Mm9EventUnresolved &entry = unresolvedEvents[unresolvedIndex];

            if (entry.nearestMovableWorldModelsByRotationPoint.empty()
                && entry.nearestMovableWorldModelsByPosition.empty())
            {
                continue;
            }

            const std::string label = "Evidence "
                + std::to_string(entry.sourceObjectIndex)
                + " "
                + (entry.sourceName.empty() ? entry.kind : entry.sourceName);
            ImGui::SetNextItemOpen(false, ImGuiCond_FirstUseEver);
            if (!ImGui::TreeNodeEx(label.c_str()))
            {
                continue;
            }

            const auto renderCandidates =
                [](const char *pLabel,
                   const std::vector<Game::Mm9EventBindingTarget::MovableWorldModelCandidate> &candidates)
            {
                if (candidates.empty())
                {
                    return;
                }

                if (!ImGui::TreeNodeEx(pLabel))
                {
                    return;
                }

                for (size_t candidateIndex = 0; candidateIndex < candidates.size(); ++candidateIndex)
                {
                    const Game::Mm9EventBindingTarget::MovableWorldModelCandidate &candidate =
                        candidates[candidateIndex];
                    ImGui::PushID(static_cast<int>(candidateIndex));
                    if (beginInspectorPropertyTable("Mm9UnresolvedEventCandidate"))
                    {
                        renderInspectorCopyableReadOnlyField(
                            "Source Model Index",
                            std::to_string(candidate.sourceModelIndex));
                        renderInspectorCopyableReadOnlyField("Source Model Name", candidate.sourceName);
                        renderInspectorReadOnlyField("Movable", candidate.movable ? "true" : "false");
                        renderInspectorReadOnlyField(
                            "World Translation LT",
                            mm9FloatVectorText(candidate.worldTranslationLt));
                        renderInspectorReadOnlyField("Distance LT", std::to_string(candidate.distanceLt));
                        renderInspectorReadOnlyField(
                            "Exact Binding Claims",
                            std::to_string(candidate.claimedByExactBindings.size()));
                        ImGui::EndTable();
                    }
                    ImGui::PopID();
                }

                ImGui::TreePop();
            };

            renderCandidates(
                "Nearest Movable World Models By Rotation Point",
                entry.nearestMovableWorldModelsByRotationPoint);
            renderCandidates(
                "Nearest Movable World Models By Position",
                entry.nearestMovableWorldModelsByPosition);
            ImGui::TreePop();
        }

        endInspectorSectionBlock();
    }

    if (document.hasMm9DatLoadedSidecars() && beginInspectorSectionBlock("Asset Dependency Graph"))
    {
        const EditorMm9AssetDependencySummary &summary = document.mm9AssetDependencySummary();

        if (beginInspectorPropertyTable("Mm9AssetDependencyGraphSummary"))
        {
            renderInspectorReadOnlyField("Total", std::to_string(summary.total));
            renderInspectorReadOnlyField("Resolved", std::to_string(summary.resolved));
            renderInspectorReadOnlyField("Unresolved", std::to_string(summary.unresolved));
            renderInspectorReadOnlyField("Ambiguous", std::to_string(summary.ambiguous));
            renderInspectorReadOnlyField("Stale", std::to_string(summary.stale));
            renderInspectorReadOnlyField("Required Unresolved", std::to_string(summary.requiredUnresolved));
            renderInspectorReadOnlyField("Required Ambiguous", std::to_string(summary.requiredAmbiguous));
            renderInspectorReadOnlyField("Optional Unresolved", std::to_string(summary.optionalUnresolved));
            ImGui::EndTable();
        }

        if (!summary.families.empty()
            && ImGui::BeginTable("Mm9AssetDependencyGraphFamilies", 9, ImGuiTableFlags_SizingStretchProp))
        {
            ImGui::TableSetupColumn("Family", ImGuiTableColumnFlags_WidthStretch);
            ImGui::TableSetupColumn("Total", ImGuiTableColumnFlags_WidthFixed, 64.0f);
            ImGui::TableSetupColumn("Resolved", ImGuiTableColumnFlags_WidthFixed, 78.0f);
            ImGui::TableSetupColumn("Unresolved", ImGuiTableColumnFlags_WidthFixed, 88.0f);
            ImGui::TableSetupColumn("Ambiguous", ImGuiTableColumnFlags_WidthFixed, 88.0f);
            ImGui::TableSetupColumn("Stale", ImGuiTableColumnFlags_WidthFixed, 64.0f);
            ImGui::TableSetupColumn("Req Unres", ImGuiTableColumnFlags_WidthFixed, 82.0f);
            ImGui::TableSetupColumn("Req Ambig", ImGuiTableColumnFlags_WidthFixed, 82.0f);
            ImGui::TableSetupColumn("Opt Unres", ImGuiTableColumnFlags_WidthFixed, 82.0f);
            ImGui::TableHeadersRow();

            for (const EditorMm9AssetDependencyFamilySummary &family : summary.families)
            {
                ImGui::TableNextRow();
                ImGui::TableSetColumnIndex(0);
                ImGui::TextUnformatted(family.family.c_str());
                ImGui::TableSetColumnIndex(1);
                ImGui::Text("%zu", family.total);
                ImGui::TableSetColumnIndex(2);
                ImGui::Text("%zu", family.resolved);
                ImGui::TableSetColumnIndex(3);
                ImGui::Text("%zu", family.unresolved);
                ImGui::TableSetColumnIndex(4);
                ImGui::Text("%zu", family.ambiguous);
                ImGui::TableSetColumnIndex(5);
                ImGui::Text("%zu", family.stale);
                ImGui::TableSetColumnIndex(6);
                ImGui::Text("%zu", family.requiredUnresolved);
                ImGui::TableSetColumnIndex(7);
                ImGui::Text("%zu", family.requiredAmbiguous);
                ImGui::TableSetColumnIndex(8);
                ImGui::Text("%zu", family.optionalUnresolved);
            }

            ImGui::EndTable();
        }

        endInspectorSectionBlock();
    }

    if (beginInspectorSectionBlock("Sidecar Paths", false))
    {
        if (beginInspectorPropertyTable("Mm9DatSidecarPathFields"))
        {
            renderInspectorCopyOpenReadOnlyField(
                "DAT World",
                metadata.sidecars.datWorld,
                resolveMm9LevelRelativePath(document, metadata.sidecars.datWorld).generic_string());
            renderInspectorCopyOpenReadOnlyField(
                "Raw Objects",
                metadata.sidecars.rawObjects,
                resolveMm9LevelRelativePath(document, metadata.sidecars.rawObjects).generic_string());
            renderInspectorCopyOpenReadOnlyField(
                "Materials",
                metadata.sidecars.materials,
                resolveMm9LevelRelativePath(document, metadata.sidecars.materials).generic_string());
            renderInspectorCopyOpenReadOnlyField(
                "Events",
                metadata.sidecars.events,
                resolveMm9LevelRelativePath(document, metadata.sidecars.events).generic_string());
            renderInspectorCopyOpenReadOnlyField(
                "Source Asset Aliases",
                metadata.sidecars.sourceAssetAliases
                    ? *metadata.sidecars.sourceAssetAliases
                    : std::string("<none>"),
                metadata.sidecars.sourceAssetAliases
                    ? resolveMm9LevelRelativePath(document, *metadata.sidecars.sourceAssetAliases).generic_string()
                    : std::string());
            renderInspectorCopyOpenReadOnlyField(
                "Level Lua",
                metadata.scripts.level,
                resolveMm9LevelRelativePath(document, metadata.scripts.level).generic_string());
            renderInspectorCopyOpenReadOnlyField(
                "Script IR",
                metadata.scripts.scriptIr,
                resolveMm9LevelRelativePath(document, metadata.scripts.scriptIr).generic_string());
            ImGui::EndTable();
        }
        endInspectorSectionBlock();
    }

    if (beginInspectorSectionBlock("Compatibility", false))
    {
        if (beginInspectorPropertyTable("Mm9DatCompatibilityFields"))
        {
            renderInspectorCopyableReadOnlyField("Legacy Target", metadata.compatibility.legacyTargetFormat);
            renderInspectorReadOnlyField(
                "ODM/BLV Derived",
                metadata.compatibility.generatedOdmBlvAreDerived ? "true" : "false");
            renderInspectorCopyOpenReadOnlyField(
                "ODM Compat",
                metadata.sidecars.odmCompat ? *metadata.sidecars.odmCompat : std::string("<none>"),
                metadata.sidecars.odmCompat
                    ? resolveMm9LevelRelativePath(document, *metadata.sidecars.odmCompat).generic_string()
                    : std::string());
            renderInspectorCopyOpenReadOnlyField(
                "BLV Compat",
                metadata.sidecars.blvCompat ? *metadata.sidecars.blvCompat : std::string("<none>"),
                metadata.sidecars.blvCompat
                    ? resolveMm9LevelRelativePath(document, *metadata.sidecars.blvCompat).generic_string()
                    : std::string());
            renderInspectorCopyOpenReadOnlyField(
                "Scene Compat",
                metadata.sidecars.sceneCompat ? *metadata.sidecars.sceneCompat : std::string("<none>"),
                metadata.sidecars.sceneCompat
                    ? resolveMm9LevelRelativePath(document, *metadata.sidecars.sceneCompat).generic_string()
                    : std::string());
            ImGui::EndTable();
        }
        endInspectorSectionBlock();
    }

    if (!session.validationMessages().empty() && beginInspectorSectionBlock("Diagnostics"))
    {
        ImGui::Text("Validation Issues: %zu", session.validationMessages().size());

        for (const std::string &message : session.validationMessages())
        {
            ImGui::BulletText("%s", message.c_str());
        }

        endInspectorSectionBlock();
    }
}

void EditorMainWindow::renderMm9DatWorldModelInspector(EditorSession &session, size_t worldModelIndex)
{
    const EditorDocument &document = session.document();

    if (document.kind() != EditorDocument::Kind::Mm9Dat || !document.hasMm9DatLoadedSidecars())
    {
        ImGui::TextDisabled("MM9 DAT sidecars are not loaded.");
        return;
    }

    const EditorMm9DatWorldSidecar &datWorld = document.mm9DatLoadedSidecars().datWorld;
    const EditorMm9MaterialAliasesSidecar &materials = document.mm9DatLoadedSidecars().materialAliases;
    const std::vector<EditorMm9MaterialTextureStatus> &materialStatuses =
        document.mm9MaterialTextureStatuses();

    if (worldModelIndex >= datWorld.worldModels.size())
    {
        ImGui::Text("DAT world model index %zu is out of range.", worldModelIndex);
        return;
    }

    const EditorMm9DatWorldModelSummary &model = datWorld.worldModels[worldModelIndex];
    const auto normalizedMm9TextureReference = [](const std::string &value)
    {
        std::string normalized = toLowerCopy(value);

        for (char &character : normalized)
        {
            if (character == '\\')
            {
                character = '/';
            }
        }

        return normalized;
    };
    const auto findMaterialStatusForTexture =
        [&materialStatuses, &normalizedMm9TextureReference](
            const EditorMm9DatWorldModelTexture &texture) -> const EditorMm9MaterialTextureStatus *
    {
        const std::string textureKey = normalizedMm9TextureReference(texture.sourceTexture);

        for (const EditorMm9MaterialTextureStatus &status : materialStatuses)
        {
            if (normalizedMm9TextureReference(status.sourceTexture) == textureKey)
            {
                return &status;
            }
        }

        return nullptr;
    };

    if (beginInspectorSectionBlock("DAT World Model"))
    {
        if (beginInspectorPropertyTable("Mm9DatWorldModelFields"))
        {
            renderInspectorCopyableReadOnlyField("Source Index", std::to_string(model.sourceModelIndex));
            renderInspectorCopyableReadOnlyField(
                "Source Name",
                model.sourceName.empty() ? std::string("<unnamed>") : model.sourceName);
            renderInspectorReadOnlyField("Kind", model.kind);
            renderInspectorReadOnlyField("Roles", mm9WorldModelRolesText(model.roles));
            renderInspectorReadOnlyField("World Info Flags", std::to_string(model.worldInfoFlags));
            renderInspectorReadOnlyField("Bounds Min LT", mm9Vec3Text(model.boundsMinLt));
            renderInspectorReadOnlyField("Bounds Max LT", mm9Vec3Text(model.boundsMaxLt));
            renderInspectorReadOnlyField("World Translation LT", mm9Vec3Text(model.worldTranslationLt));
            renderInspectorReadOnlyField("Points", std::to_string(model.pointCount));
            renderInspectorReadOnlyField("Planes", std::to_string(model.planeCount));
            renderInspectorReadOnlyField("Surfaces", std::to_string(model.surfaceCount));
            renderInspectorReadOnlyField("Polygons", std::to_string(model.polyCount));
            renderInspectorReadOnlyField("Nodes", std::to_string(model.nodeCount));
            renderInspectorReadOnlyField("Leaves", std::to_string(model.leafCount));
            renderInspectorReadOnlyField("User Portals", std::to_string(model.userPortalCount));
            renderInspectorReadOnlyField("Textures", std::to_string(model.textures.size()));
            renderInspectorReadOnlyField("Root Node Index", std::to_string(model.rootNodeIndex));
            renderInspectorReadOnlyField("Section Count", std::to_string(model.sectionCount));
            ImGui::EndTable();
        }
        endInspectorSectionBlock();
    }

    if (beginInspectorSectionBlock("BSP Counts And Unknowns", false))
    {
        if (beginInspectorPropertyTable("Mm9DatWorldModelBspCountFields"))
        {
            renderInspectorReadOnlyField("Vert Count", std::to_string(model.bspCounts.vertCount));
            renderInspectorReadOnlyField(
                "Total Vis List Size",
                std::to_string(model.bspCounts.totalVisListSize));
            renderInspectorReadOnlyField("Leaf List Count", std::to_string(model.bspCounts.leafListCount));
            renderInspectorReadOnlyField(
                "Texture Name Length",
                std::to_string(model.bspCounts.textureNameLength));
            renderInspectorReadOnlyField("BSP Texture Count", std::to_string(model.bspCounts.textureCount));
            renderInspectorReadOnlyField(
                "Unknown Value",
                std::to_string(model.unknownValues.worldBspUnknownValue));
            renderInspectorReadOnlyField(
                "Unknown Value 2",
                std::to_string(model.unknownValues.worldBspUnknownValue2));
            renderInspectorReadOnlyField(
                "Unknown Value 3",
                std::to_string(model.unknownValues.worldBspUnknownValue3));
            ImGui::EndTable();
        }
        endInspectorSectionBlock();
    }

    if (beginInspectorSectionBlock("Reference Validation", false))
    {
        if (beginInspectorPropertyTable("Mm9DatWorldModelReferenceValidationFields"))
        {
            renderInspectorReadOnlyField(
                "Invalid Surface Texture Refs",
                std::to_string(model.referenceValidation.invalidSurfaceTextureRefs));
            renderInspectorReadOnlyField(
                "Invalid Polygon Surface Refs",
                std::to_string(model.referenceValidation.invalidPolySurfaceRefs));
            renderInspectorReadOnlyField(
                "Invalid Polygon Plane Refs",
                std::to_string(model.referenceValidation.invalidPolyPlaneRefs));
            renderInspectorReadOnlyField(
                "Invalid Polygon Vertex Refs",
                std::to_string(model.referenceValidation.invalidPolyVertexRefs));
            renderInspectorReadOnlyField(
                "Invalid Node Polygon Refs",
                std::to_string(model.referenceValidation.invalidNodePolyRefs));
            renderInspectorReadOnlyField(
                "Invalid Root Node Refs",
                std::to_string(model.referenceValidation.invalidRootNodeRefs));
            ImGui::EndTable();
        }
        endInspectorSectionBlock();
    }

    if (beginInspectorSectionBlock("PBlock And Source Preservation", false))
    {
        if (beginInspectorPropertyTable("Mm9DatWorldModelPBlockFields"))
        {
            renderInspectorReadOnlyField(
                "Preserved In Source DAT",
                model.pblockTable.preservedInSourceDat ? "true" : "false");
            renderInspectorReadOnlyField("Decoded Summary", model.pblockTable.decodedSummary ? "true" : "false");
            renderInspectorReadOnlyField(
                "Record Count",
                model.pblockTable.recordCount
                    ? std::to_string(*model.pblockTable.recordCount)
                    : std::string("<not decoded>"));
            renderInspectorReadOnlyField(
                "Dimensions",
                std::to_string(model.pblockTable.dimA) + ", "
                    + std::to_string(model.pblockTable.dimB) + ", "
                    + std::to_string(model.pblockTable.dimC));
            renderInspectorReadOnlyField("Bounds Min LT", mm9Vec3Text(model.pblockTable.boundsMinLt));
            renderInspectorReadOnlyField("Bounds Max LT", mm9Vec3Text(model.pblockTable.boundsMaxLt));
            renderInspectorReadOnlyField("Parser Status", datWorld.validation.parseStatus);
            renderInspectorReadOnlyField("Unknown Field Policy", datWorld.validation.unknownFieldPolicy);
            renderInspectorReadOnlyField("PBlock Status", datWorld.validation.pblockSummaryStatus);
            ImGui::EndTable();
        }
        endInspectorSectionBlock();
    }

    if (beginInspectorSectionBlock("Textures", false))
    {
        if (model.textures.empty())
        {
            ImGui::TextDisabled("No texture references.");
        }
        else if (ImGui::BeginTable("Mm9DatWorldModelTextures", 7, ImGuiTableFlags_SizingStretchProp))
        {
            ImGui::TableSetupColumn("Index", ImGuiTableColumnFlags_WidthFixed, 70.0f);
            ImGui::TableSetupColumn("Source Texture", ImGuiTableColumnFlags_WidthStretch);
            ImGui::TableSetupColumn("Alias", ImGuiTableColumnFlags_WidthFixed, 120.0f);
            ImGui::TableSetupColumn("Resolved DTX", ImGuiTableColumnFlags_WidthFixed, 92.0f);
            ImGui::TableSetupColumn("Ambiguous", ImGuiTableColumnFlags_WidthFixed, 86.0f);
            ImGui::TableSetupColumn("Path", ImGuiTableColumnFlags_WidthStretch);
            ImGui::TableSetupColumn("Actions", ImGuiTableColumnFlags_WidthFixed, 112.0f);
            ImGui::TableHeadersRow();

            for (const EditorMm9DatWorldModelTexture &texture : model.textures)
            {
                const EditorMm9MaterialTextureStatus *pStatus = findMaterialStatusForTexture(texture);
                ImGui::TableNextRow();
                ImGui::TableSetColumnIndex(0);
                ImGui::Text("%zu", texture.textureIndex);
                ImGui::TableSetColumnIndex(1);
                ImGui::TextUnformatted(texture.sourceTexture.c_str());
                ImGui::TableSetColumnIndex(2);

                if (pStatus != nullptr && !pStatus->alias.empty())
                {
                    ImGui::PushID(static_cast<int>(texture.textureIndex));
                    const bool canSelectMaterial = pStatus->textureIndex < materials.textures.size();

                    if (canSelectMaterial && ImGui::Selectable(pStatus->alias.c_str(), false))
                    {
                        session.select(EditorSelectionKind::Mm9MaterialTexture, pStatus->textureIndex);
                    }
                    else if (!canSelectMaterial)
                    {
                        ImGui::TextUnformatted(pStatus->alias.c_str());
                    }

                    ImGui::PopID();
                }
                else
                {
                    ImGui::TextDisabled("<unresolved>");
                }

                ImGui::TableSetColumnIndex(3);
                ImGui::TextUnformatted(pStatus != nullptr && pStatus->sourceDtxResolved ? "true" : "false");
                ImGui::TableSetColumnIndex(4);
                ImGui::TextUnformatted(pStatus != nullptr && pStatus->sourceDtxAmbiguous ? "true" : "false");
                ImGui::TableSetColumnIndex(5);
                ImGui::TextUnformatted(pStatus != nullptr ? pStatus->resolvedSourcePath.c_str() : "");
                ImGui::TableSetColumnIndex(6);
                renderInspectorCopyButton(
                    ("Mm9WorldModelTexture" + std::to_string(texture.textureIndex)).c_str(),
                    pStatus != nullptr && !pStatus->resolvedSourcePath.empty()
                        ? pStatus->resolvedSourcePath
                        : texture.sourceTexture);
                ImGui::SameLine();
                renderInspectorOpenPathButton(
                    ("Mm9WorldModelTextureOpen" + std::to_string(texture.textureIndex)).c_str(),
                    pStatus != nullptr ? pStatus->resolvedSourcePath : std::string());
            }

            ImGui::EndTable();
        }
        endInspectorSectionBlock();
    }

    if (beginInspectorSectionBlock("Surface Flags", false))
    {
        if (ImGui::BeginTable("Mm9DatWorldModelSurfaceFlags", 2, ImGuiTableFlags_SizingStretchProp))
        {
            ImGui::TableSetupColumn("DAT Surface Flags", ImGuiTableColumnFlags_WidthStretch);
            ImGui::TableSetupColumn("Count", ImGuiTableColumnFlags_WidthFixed, 80.0f);
            ImGui::TableHeadersRow();

            for (const EditorMm9DatWorldHistogramEntry &entry : model.surfaceFlagHistogram)
            {
                ImGui::TableNextRow();
                ImGui::TableSetColumnIndex(0);
                ImGui::Text("%d", entry.key);
                ImGui::TableSetColumnIndex(1);
                ImGui::Text("%zu", entry.count);
            }

            ImGui::EndTable();
        }

        ImGui::Spacing();

        if (ImGui::BeginTable("Mm9DatWorldModelTextureUserFlags", 2, ImGuiTableFlags_SizingStretchProp))
        {
            ImGui::TableSetupColumn("DTX Texture User Flag", ImGuiTableColumnFlags_WidthStretch);
            ImGui::TableSetupColumn("Count", ImGuiTableColumnFlags_WidthFixed, 80.0f);
            ImGui::TableHeadersRow();

            for (const EditorMm9DatWorldHistogramEntry &entry : model.textureUserFlagHistogram)
            {
                ImGui::TableNextRow();
                ImGui::TableSetColumnIndex(0);
                ImGui::Text("%d", entry.key);
                ImGui::TableSetColumnIndex(1);
                ImGui::Text("%zu", entry.count);
            }

            ImGui::EndTable();
        }

        endInspectorSectionBlock();
    }

    if (beginInspectorSectionBlock("World Leaf References", false))
    {
        if (beginInspectorPropertyTable("Mm9DatLeafReferenceFields"))
        {
            renderInspectorReadOnlyField("Decode", datWorld.leafReferences.decode);
            renderInspectorReadOnlyField("Total Refs", std::to_string(datWorld.leafReferences.totalRefs));
            renderInspectorReadOnlyField("Invalid Refs", std::to_string(datWorld.leafReferences.invalidRefs));
            ImGui::EndTable();
        }
        endInspectorSectionBlock();
    }

    if (beginInspectorSectionBlock("User Portals", false))
    {
        size_t matchingPortalCount = 0;

        for (const EditorMm9DatUserPortalSummary &portal : datWorld.userPortals)
        {
            if (portal.sourceModelIndex == model.sourceModelIndex)
            {
                ++matchingPortalCount;
            }
        }

        if (matchingPortalCount == 0)
        {
            ImGui::TextDisabled("No user portals on this world model.");
        }
        else if (ImGui::BeginTable("Mm9DatWorldModelUserPortals", 5, ImGuiTableFlags_SizingStretchProp))
        {
            ImGui::TableSetupColumn("Index", ImGuiTableColumnFlags_WidthFixed, 62.0f);
            ImGui::TableSetupColumn("Name", ImGuiTableColumnFlags_WidthStretch);
            ImGui::TableSetupColumn("Center LT", ImGuiTableColumnFlags_WidthStretch);
            ImGui::TableSetupColumn("Dims LT", ImGuiTableColumnFlags_WidthStretch);
            ImGui::TableSetupColumn("Raw Short", ImGuiTableColumnFlags_WidthFixed, 78.0f);
            ImGui::TableHeadersRow();

            for (const EditorMm9DatUserPortalSummary &portal : datWorld.userPortals)
            {
                if (portal.sourceModelIndex != model.sourceModelIndex)
                {
                    continue;
                }

                ImGui::TableNextRow();
                ImGui::TableSetColumnIndex(0);
                ImGui::Text("%zu", portal.portalIndex);
                ImGui::TableSetColumnIndex(1);
                ImGui::TextUnformatted(portal.name.c_str());
                ImGui::TableSetColumnIndex(2);
                ImGui::TextUnformatted(mm9Vec3Text(portal.centerLt).c_str());
                ImGui::TableSetColumnIndex(3);
                ImGui::TextUnformatted(mm9Vec3Text(portal.dimsLt).c_str());
                ImGui::TableSetColumnIndex(4);
                ImGui::Text("%d", portal.rawUnknowns.unknownShort);
            }

            ImGui::EndTable();
        }

        endInspectorSectionBlock();
    }
}

void EditorMainWindow::renderMm9DatPolygonInspector(EditorSession &session, size_t triangleIndex)
{
    const EditorDocument &document = session.document();

    if (document.kind() != EditorDocument::Kind::Mm9Dat || !document.hasMm9DatWorld())
    {
        ImGui::TextDisabled("MM9 DAT world is not loaded.");
        return;
    }

    const Game::Mm9DatRenderMesh &mesh = document.mm9DatRenderMesh();

    if (triangleIndex >= mesh.triangles.size())
    {
        ImGui::Text("DAT render triangle index %zu is out of range.", triangleIndex);
        return;
    }

    const Game::Mm9DatRenderTriangle &triangle = mesh.triangles[triangleIndex];
    const Game::Mm9DatWorld &world = document.mm9DatWorld();
    const Game::Mm9DatWorldModel *pModel = nullptr;
    const Game::Mm9DatPoly *pPoly = nullptr;
    const Game::Mm9DatSurface *pSurface = nullptr;
    const Game::Mm9DatPlane *pPlane = nullptr;

    if (triangle.sourceModelIndex < world.worldModels.size())
    {
        pModel = &world.worldModels[triangle.sourceModelIndex];

        if (triangle.sourcePolyIndex < pModel->polies.size())
        {
            pPoly = &pModel->polies[triangle.sourcePolyIndex];
        }

        if (triangle.sourceSurfaceIndex < pModel->surfaces.size())
        {
            pSurface = &pModel->surfaces[triangle.sourceSurfaceIndex];
        }

        if (pPoly != nullptr && pPoly->planeIndex < pModel->planes.size())
        {
            pPlane = &pModel->planes[pPoly->planeIndex];
        }
    }

    const std::vector<Game::Mm9DatRenderMaterialAssignment> &assignments =
        document.mm9DatRenderMaterialAssignments();
    const Game::Mm9DatRenderMaterialAssignment *pAssignment = nullptr;

    if (triangleIndex < assignments.size() && assignments[triangleIndex].triangleIndex == triangleIndex)
    {
        pAssignment = &assignments[triangleIndex];
    }
    else
    {
        for (const Game::Mm9DatRenderMaterialAssignment &assignment : assignments)
        {
            if (assignment.triangleIndex == triangleIndex)
            {
                pAssignment = &assignment;
                break;
            }
        }
    }

    const std::vector<EditorMm9MaterialTextureStatus> &materialStatuses =
        document.mm9MaterialTextureStatuses();
    const EditorMm9MaterialTextureStatus *pMaterialStatus = nullptr;

    if (pAssignment != nullptr && pAssignment->materialIndex < materialStatuses.size())
    {
        pMaterialStatus = &materialStatuses[pAssignment->materialIndex];
    }

    const float minX = std::min(
        triangle.vertices[0].x,
        std::min(triangle.vertices[1].x, triangle.vertices[2].x));
    const float minY = std::min(
        triangle.vertices[0].y,
        std::min(triangle.vertices[1].y, triangle.vertices[2].y));
    const float minZ = std::min(
        triangle.vertices[0].z,
        std::min(triangle.vertices[1].z, triangle.vertices[2].z));
    const float maxX = std::max(
        triangle.vertices[0].x,
        std::max(triangle.vertices[1].x, triangle.vertices[2].x));
    const float maxY = std::max(
        triangle.vertices[0].y,
        std::max(triangle.vertices[1].y, triangle.vertices[2].y));
    const float maxZ = std::max(
        triangle.vertices[0].z,
        std::max(triangle.vertices[1].z, triangle.vertices[2].z));
    const Game::Mm9DatVec3 renderBoundsMin = {minX, minY, minZ};
    const Game::Mm9DatVec3 renderBoundsMax = {maxX, maxY, maxZ};
    Game::Mm9DatRenderFilterEntry filterEntry = {};
    bool hasFilterEntry = false;

    if (document.hasMm9DatLoadedSidecars())
    {
        const EditorMm9DatWorldSidecar &datWorld = document.mm9DatLoadedSidecars().datWorld;
        const Game::Mm9DatRenderFilterResult filters = Game::classifyMm9DatRenderMeshFilters(
            mesh,
            mm9ModelRenderRolesFromSidecar(datWorld),
            datWorld.userPortals.size());

        if (triangleIndex < filters.entries.size() && filters.entries[triangleIndex].triangleIndex == triangleIndex)
        {
            filterEntry = filters.entries[triangleIndex];
            hasFilterEntry = true;
        }
        else
        {
            for (const Game::Mm9DatRenderFilterEntry &entry : filters.entries)
            {
                if (entry.triangleIndex == triangleIndex)
                {
                    filterEntry = entry;
                    hasFilterEntry = true;
                    break;
                }
            }
        }
    }

    if (beginInspectorSectionBlock("DAT Polygon"))
    {
        if (beginInspectorPropertyTable("Mm9DatPolygonFields"))
        {
            renderInspectorCopyableReadOnlyField("Render Triangle", std::to_string(triangleIndex));
            renderInspectorCopyableReadOnlyField("Source Model Index", std::to_string(triangle.sourceModelIndex));
            renderInspectorCopyableReadOnlyField(
                "Source Model Name",
                triangle.sourceModelName.empty() ? std::string("<unnamed>") : triangle.sourceModelName);
            renderInspectorCopyableReadOnlyField("Source Polygon Index", std::to_string(triangle.sourcePolyIndex));
            renderInspectorCopyableReadOnlyField("Source Surface Index", std::to_string(triangle.sourceSurfaceIndex));
            renderInspectorCopyableReadOnlyField("Source Texture Index", std::to_string(triangle.sourceTextureIndex));
            renderInspectorCopyableReadOnlyField("Source Texture", triangle.sourceTexture);
            renderInspectorReadOnlyField("Plane Orientation Flipped", triangle.sourcePlaneOrientationFlipped
                ? "true"
                : "false");
            renderInspectorReadOnlyField("Render Bounds Min", mm9DatVec3Text(renderBoundsMin));
            renderInspectorReadOnlyField("Render Bounds Max", mm9DatVec3Text(renderBoundsMax));
            ImGui::EndTable();
        }
        endInspectorSectionBlock();
    }

    if (beginInspectorSectionBlock("Surface Participation"))
    {
        if (beginInspectorPropertyTable("Mm9DatPolygonParticipationFields"))
        {
            if (hasFilterEntry)
            {
                renderInspectorReadOnlyField("Filter Flags", hex32Text(filterEntry.flags));
                renderInspectorReadOnlyField(
                    "Default Rendered",
                    boolText(mm9DatFilterEntryShouldRenderInDefaultEditorView(filterEntry)));
                renderInspectorReadOnlyField("In Pick Mesh", "true");
                renderInspectorReadOnlyField(
                    "Visual Art",
                    boolText((filterEntry.flags & Game::Mm9DatRenderFilterVisual) != 0));
                renderInspectorReadOnlyField(
                    "Invisible Surface",
                    boolText((filterEntry.flags & Game::Mm9DatRenderFilterInvisible) != 0));
                renderInspectorReadOnlyField(
                    "Physics",
                    boolText((filterEntry.flags & Game::Mm9DatRenderFilterPhysics) != 0));
                renderInspectorReadOnlyField(
                    "Visibility",
                    boolText((filterEntry.flags & Game::Mm9DatRenderFilterVisibility) != 0));
                renderInspectorReadOnlyField(
                    "Trigger Or Volume",
                    boolText((filterEntry.flags & Game::Mm9DatRenderFilterTrigger) != 0));
                renderInspectorReadOnlyField(
                    "Sky",
                    boolText((filterEntry.flags & Game::Mm9DatRenderFilterSky) != 0));
                renderInspectorReadOnlyField(
                    "Water",
                    boolText((filterEntry.flags & Game::Mm9DatRenderFilterWater) != 0));
                renderInspectorReadOnlyField(
                    "Visible Water",
                    boolText((filterEntry.flags & Game::Mm9DatRenderFilterVisibleWater) != 0));
                renderInspectorReadOnlyField(
                    "Water Volume Or Marker",
                    boolText((filterEntry.flags & Game::Mm9DatRenderFilterWaterVolume) != 0));
                renderInspectorReadOnlyField(
                    "Rail Or AIRail Helper",
                    boolText((filterEntry.flags & Game::Mm9DatRenderFilterRail) != 0));
                renderInspectorReadOnlyField(
                    "Terrain",
                    boolText((filterEntry.flags & Game::Mm9DatRenderFilterTerrain) != 0));
                renderInspectorReadOnlyField(
                    "Movable",
                    boolText((filterEntry.flags & Game::Mm9DatRenderFilterMovable) != 0));
                renderInspectorReadOnlyField(
                    "Helper Geometry",
                    boolText((filterEntry.flags & Game::Mm9DatRenderFilterHelper) != 0));
            }
            else
            {
                renderInspectorReadOnlyField("Classifier", "<sidecar unavailable>");
            }

            ImGui::EndTable();
        }

        endInspectorSectionBlock();
    }

    if (beginInspectorSectionBlock("Collision And Material"))
    {
        if (beginInspectorPropertyTable("Mm9DatPolygonCollisionMaterialFields"))
        {
            const uint32_t datSurfaceFlags = triangle.surfaceFlags;
            const uint32_t dtxUserFlags =
                pMaterialStatus != nullptr && pMaterialStatus->dtxHeader
                    ? static_cast<uint32_t>(pMaterialStatus->dtxHeader->userFlags)
                    : 0u;
            const bool dtxUserFlagsKnown = pMaterialStatus != nullptr && pMaterialStatus->dtxHeader.has_value();
            const bool datSolid = (datSurfaceFlags & Game::Mm9DatSurfaceFlagSolid) != 0;
            const bool datPhysicsBlocker =
                (datSurfaceFlags & Game::Mm9DatSurfaceFlagPhysicsBlocker) != 0
                || (hasFilterEntry && (filterEntry.flags & Game::Mm9DatRenderFilterPhysics) != 0);
            const bool datVisibilityBlocker =
                (datSurfaceFlags & Game::Mm9DatSurfaceFlagVisibilityBlocker) != 0
                || (hasFilterEntry && (filterEntry.flags & Game::Mm9DatRenderFilterVisibility) != 0);

            renderInspectorReadOnlyField("DAT Surface Flags", mm9SurfaceFlagsText(datSurfaceFlags));
            renderInspectorReadOnlyField(
                "DTX User/Material Flags",
                dtxUserFlagsKnown ? mm9SurfaceFlagsText(dtxUserFlags) : std::string("<unavailable>"));
            renderInspectorReadOnlyField("Solid Candidate", boolText(datSolid));
            renderInspectorReadOnlyField("Physics Blocker", boolText(datPhysicsBlocker));
            renderInspectorReadOnlyField("Visibility Blocker", boolText(datVisibilityBlocker));
            renderInspectorReadOnlyField(
                "Not A Step",
                boolText((datSurfaceFlags & Game::Mm9DatSurfaceFlagNotAStep) != 0));
            renderInspectorReadOnlyField(
                "Portal Surface",
                boolText((datSurfaceFlags & Game::Mm9DatSurfaceFlagPortal) != 0));
            renderInspectorReadOnlyField(
                "Invisible Surface",
                boolText((datSurfaceFlags & Game::Mm9DatSurfaceFlagInvisible) != 0));
            renderInspectorReadOnlyField(
                "Sky Surface",
                boolText((datSurfaceFlags & Game::Mm9DatSurfaceFlagSky) != 0));
            renderInspectorReadOnlyField(
                "Contact Metadata Source",
                dtxUserFlagsKnown ? "DTX m_UserFlags" : "DTX header unavailable");
            ImGui::EndTable();
        }

        endInspectorSectionBlock();
    }

    if (beginInspectorSectionBlock("Surface And Material"))
    {
        if (beginInspectorPropertyTable("Mm9DatPolygonSurfaceMaterialFields"))
        {
            renderInspectorReadOnlyField("DAT Surface Flags", mm9SurfaceFlagsText(triangle.surfaceFlags));
            renderInspectorReadOnlyField("DAT Texture Flags", hex16Text(triangle.textureFlags));

            if (pSurface != nullptr)
            {
                renderInspectorReadOnlyField("Surface Unknown", hex32Text(pSurface->unknown));
                renderInspectorReadOnlyField("Surface Unknown 2", hex32Text(pSurface->unknown2));
                renderInspectorReadOnlyField("Surface Texture Index", std::to_string(pSurface->textureIndex));
                renderInspectorReadOnlyField("Effect Name", pSurface->effectName);
                renderInspectorReadOnlyField("Effect Param", pSurface->effectParam);
                renderInspectorReadOnlyField("UV Origin LT", mm9DatVec3Text(pSurface->uvOriginLt));
                renderInspectorReadOnlyField("UV U LT", mm9DatVec3Text(pSurface->uvULt));
                renderInspectorReadOnlyField("UV V LT", mm9DatVec3Text(pSurface->uvVLt));
            }
            else
            {
                renderInspectorReadOnlyField("Surface Record", "<out of range>");
            }

            if (pAssignment != nullptr)
            {
                renderInspectorCopyableReadOnlyField("Material Alias", pAssignment->alias);
                renderInspectorReadOnlyField(
                    "Material Candidates",
                    std::to_string(pAssignment->materialCandidateCount));
                renderInspectorReadOnlyField("Material Assigned", pAssignment->assigned ? "true" : "false");
                renderInspectorReadOnlyField("Material Ambiguous", pAssignment->ambiguous ? "true" : "false");
                renderInspectorCopyableReadOnlyField("Resolved Source DTX", pAssignment->resolvedSourcePath);
            }

            if (pMaterialStatus != nullptr && pMaterialStatus->dtxHeader)
            {
                const EditorMm9DtxHeader &header = *pMaterialStatus->dtxHeader;
                renderInspectorReadOnlyField(
                    "DTX User Flags",
                    mm9SurfaceFlagsText(static_cast<uint32_t>(header.userFlags)));
                renderInspectorReadOnlyField(
                    "DTX Surface Flag",
                    mm9SurfaceFlagsText(static_cast<uint32_t>(header.surfaceFlag)));
                renderInspectorReadOnlyField("DTX Texture Group", std::to_string(header.textureGroup));
            }

            ImGui::EndTable();
        }
        endInspectorSectionBlock();
    }

    if (beginInspectorSectionBlock("Source Polygon"))
    {
        if (beginInspectorPropertyTable("Mm9DatPolygonSourceFields"))
        {
            if (pPoly != nullptr)
            {
                renderInspectorReadOnlyField("Center LT", mm9DatVec3Text(pPoly->centerLt));
                renderInspectorReadOnlyField("Lightmap Width", std::to_string(pPoly->lightmapWidth));
                renderInspectorReadOnlyField("Lightmap Height", std::to_string(pPoly->lightmapHeight));
                renderInspectorReadOnlyField("Unknown Flag", hex16Text(pPoly->unknownFlag));
                renderInspectorReadOnlyField("Unknown List Count", std::to_string(pPoly->unknownList.size()));
                renderInspectorReadOnlyField("Surface Index", std::to_string(pPoly->surfaceIndex));
                renderInspectorReadOnlyField("Plane Index", std::to_string(pPoly->planeIndex));
                renderInspectorReadOnlyField("Vertex Count", std::to_string(pPoly->vertices.size()));
            }
            else
            {
                renderInspectorReadOnlyField("Polygon Record", "<out of range>");
            }

            if (pPlane != nullptr)
            {
                renderInspectorReadOnlyField("Plane Normal LT", mm9DatVec3Text(pPlane->normalLt));
                renderInspectorReadOnlyField("Plane Distance", std::to_string(pPlane->distance));
            }
            else
            {
                renderInspectorReadOnlyField("Plane Record", "<out of range>");
            }

            ImGui::EndTable();
        }

        if (pPoly != nullptr && pModel != nullptr && ImGui::BeginTable(
                "Mm9DatPolygonVertices",
                6,
                ImGuiTableFlags_SizingStretchProp))
        {
            ImGui::TableSetupColumn("Vertex", ImGuiTableColumnFlags_WidthFixed, 64.0f);
            ImGui::TableSetupColumn("Point", ImGuiTableColumnFlags_WidthFixed, 64.0f);
            ImGui::TableSetupColumn("Position LT", ImGuiTableColumnFlags_WidthStretch);
            ImGui::TableSetupColumn("Normal LT", ImGuiTableColumnFlags_WidthStretch);
            ImGui::TableSetupColumn("Dummy", ImGuiTableColumnFlags_WidthFixed, 96.0f);
            ImGui::TableSetupColumn("Valid", ImGuiTableColumnFlags_WidthFixed, 64.0f);
            ImGui::TableHeadersRow();

            for (size_t vertexIndex = 0; vertexIndex < pPoly->vertices.size(); ++vertexIndex)
            {
                const Game::Mm9DatPolyVertex &vertex = pPoly->vertices[vertexIndex];
                const bool pointValid = vertex.pointIndex < pModel->pointsLt.size();
                const bool normalValid = vertex.pointIndex < pModel->pointNormalsLt.size();
                char dummyBuffer[32] = {};
                std::snprintf(
                    dummyBuffer,
                    sizeof(dummyBuffer),
                    "%02X %02X %02X",
                    static_cast<unsigned>(vertex.rawDummy[0]),
                    static_cast<unsigned>(vertex.rawDummy[1]),
                    static_cast<unsigned>(vertex.rawDummy[2]));

                ImGui::TableNextRow();
                ImGui::TableSetColumnIndex(0);
                ImGui::Text("%zu", vertexIndex);
                ImGui::TableSetColumnIndex(1);
                ImGui::Text("%u", static_cast<unsigned>(vertex.pointIndex));
                ImGui::TableSetColumnIndex(2);
                ImGui::TextUnformatted(pointValid
                    ? mm9DatVec3Text(pModel->pointsLt[vertex.pointIndex]).c_str()
                    : "<out of range>");
                ImGui::TableSetColumnIndex(3);
                ImGui::TextUnformatted(normalValid
                    ? mm9DatVec3Text(pModel->pointNormalsLt[vertex.pointIndex]).c_str()
                    : "<out of range>");
                ImGui::TableSetColumnIndex(4);
                ImGui::TextUnformatted(dummyBuffer);
                ImGui::TableSetColumnIndex(5);
                ImGui::TextUnformatted(pointValid ? "true" : "false");
            }

            ImGui::EndTable();
        }

        if (ImGui::BeginTable("Mm9DatRenderTriangleVertices", 5, ImGuiTableFlags_SizingStretchProp))
        {
            ImGui::TableSetupColumn("Triangle Vertex", ImGuiTableColumnFlags_WidthFixed, 110.0f);
            ImGui::TableSetupColumn("X", ImGuiTableColumnFlags_WidthStretch);
            ImGui::TableSetupColumn("Y", ImGuiTableColumnFlags_WidthStretch);
            ImGui::TableSetupColumn("Z", ImGuiTableColumnFlags_WidthStretch);
            ImGui::TableSetupColumn("UV Pixels", ImGuiTableColumnFlags_WidthStretch);
            ImGui::TableHeadersRow();

            for (size_t vertexIndex = 0; vertexIndex < triangle.vertices.size(); ++vertexIndex)
            {
                const Game::Mm9DatRenderVertex &vertex = triangle.vertices[vertexIndex];
                char uvBuffer[64] = {};
                std::snprintf(uvBuffer, sizeof(uvBuffer), "%.3f, %.3f", vertex.uPixels, vertex.vPixels);

                ImGui::TableNextRow();
                ImGui::TableSetColumnIndex(0);
                ImGui::Text("%zu", vertexIndex);
                ImGui::TableSetColumnIndex(1);
                ImGui::Text("%.3f", vertex.x);
                ImGui::TableSetColumnIndex(2);
                ImGui::Text("%.3f", vertex.y);
                ImGui::TableSetColumnIndex(3);
                ImGui::Text("%.3f", vertex.z);
                ImGui::TableSetColumnIndex(4);
                ImGui::TextUnformatted(uvBuffer);
            }

            ImGui::EndTable();
        }

        endInspectorSectionBlock();
    }
}

void EditorMainWindow::renderMm9MaterialTextureInspector(EditorSession &session, size_t textureIndex)
{
    const EditorDocument &document = session.document();

    if (document.kind() != EditorDocument::Kind::Mm9Dat || !document.hasMm9DatLoadedSidecars())
    {
        ImGui::TextDisabled("MM9 DAT sidecars are not loaded.");
        return;
    }

    const EditorMm9MaterialAliasesSidecar &materials = document.mm9DatLoadedSidecars().materialAliases;

    if (textureIndex >= materials.textures.size())
    {
        ImGui::Text("DTX texture index %zu is out of range.", textureIndex);
        return;
    }

    const EditorMm9MaterialTexture &texture = materials.textures[textureIndex];
    const std::vector<EditorMm9MaterialTextureStatus> &statuses = document.mm9MaterialTextureStatuses();
    const EditorMm9MaterialTextureStatus *pStatus =
        textureIndex < statuses.size() ? &statuses[textureIndex] : nullptr;

    if (beginInspectorSectionBlock("Material Alias"))
    {
        if (beginInspectorPropertyTable("Mm9MaterialAliasFields"))
        {
            renderInspectorCopyableReadOnlyField("Alias", texture.alias);
            renderInspectorCopyableReadOnlyField("Source Texture", texture.sourceTexture);
            renderInspectorCopyOpenReadOnlyField(
                "Original Physical Path",
                texture.physicalPath,
                resolveMm9LevelRelativePath(document, texture.physicalPath).generic_string());
            renderInspectorCopyOpenReadOnlyField(
                "Generated Cache",
                texture.emittedBitmap,
                resolveMm9LevelRelativePath(document, texture.emittedBitmap).generic_string());
            renderInspectorReadOnlyField("Cache Mode", texture.emittedBitmapMode);

            if (pStatus != nullptr)
            {
                renderInspectorReadOnlyField("Source Asset Family", pStatus->sourceAssetFamily);
                renderInspectorReadOnlyField("Resolution Source", pStatus->resolutionSource);
                renderInspectorReadOnlyField("Alias Applied", pStatus->aliasApplied ? "true" : "false");
                renderInspectorReadOnlyField("Alias Target Key", pStatus->aliasTargetKey);
                renderInspectorReadOnlyField(
                    "Default Helper Material",
                    pStatus->defaultHelperMaterial ? "true" : "false");
                renderInspectorCopyOpenReadOnlyField(
                    "Resolved Source",
                    pStatus->resolvedSourcePath,
                    pStatus->resolvedSourcePath);
                renderInspectorReadOnlyField("Source Exists", pStatus->sourcePathExists ? "true" : "false");
                renderInspectorCopyableReadOnlyField(
                    "Source DTX SHA-256",
                    pStatus->sourceDtxHashLoaded ? pStatus->sourceDtxSha256 : "");
                renderInspectorReadOnlyField(
                    "Source DTX Bytes",
                    pStatus->sourceDtxHashLoaded ? std::to_string(pStatus->sourceDtxSizeBytes) : "");
                renderInspectorReadOnlyField(
                    "Source DTX Candidates",
                    std::to_string(pStatus->sourceDtxCandidateCount));
                renderInspectorReadOnlyField(
                    "Source DTX Resolved",
                    pStatus->sourceDtxResolved ? "true" : "false");
                renderInspectorReadOnlyField(
                    "Source DTX Ambiguous",
                    pStatus->sourceDtxAmbiguous ? "true" : "false");
                renderInspectorCopyOpenReadOnlyField(
                    "Resolved SPR",
                    pStatus->resolvedSpritePath,
                    pStatus->resolvedSpritePath);
                renderInspectorReadOnlyField("Source SPR Exists", pStatus->sourceSpritePathExists ? "true" : "false");
                renderInspectorReadOnlyField(
                    "Source SPR Candidates",
                    std::to_string(pStatus->sourceSpriteCandidateCount));
                renderInspectorReadOnlyField(
                    "Source SPR Resolved",
                    pStatus->sourceSpriteResolved ? "true" : "false");
                renderInspectorReadOnlyField(
                    "Source SPR Ambiguous",
                    pStatus->sourceSpriteAmbiguous ? "true" : "false");
                renderInspectorReadOnlyField("Source SPR Parsed", pStatus->sourceSpriteParsed ? "true" : "false");
                renderInspectorReadOnlyField(
                    "SPR Frame Textures",
                    std::to_string(pStatus->spriteFrameTextureCount));
                renderInspectorReadOnlyField(
                    "Resolved SPR Frame Textures",
                    std::to_string(pStatus->resolvedSpriteFrameTextureCount));
                renderInspectorReadOnlyField(
                    "Unresolved SPR Frame Textures",
                    std::to_string(pStatus->unresolvedSpriteFrameTextureCount));
                renderInspectorReadOnlyField(
                    "Ambiguous SPR Frame Textures",
                    std::to_string(pStatus->ambiguousSpriteFrameTextureCount));
                renderInspectorCopyOpenReadOnlyField(
                    "Resolved Cache",
                    pStatus->resolvedCachePath,
                    pStatus->resolvedCachePath);
                renderInspectorReadOnlyField("Cache Exists", pStatus->cachePathExists ? "true" : "false");
                renderInspectorReadOnlyField(
                    "Cache SHA-256",
                    pStatus->cacheHashLoaded ? pStatus->cacheSha256 : "");
                renderInspectorReadOnlyField(
                    "Cache Bytes",
                    pStatus->cacheHashLoaded ? std::to_string(pStatus->cacheSizeBytes) : "");
                renderInspectorReadOnlyField(
                    "Cache Timestamp Known",
                    pStatus->cacheFreshnessKnown ? "true" : "false");
                renderInspectorReadOnlyField(
                    "Cache Newer Than Source",
                    pStatus->cacheNewerThanSource ? "true" : "false");
                renderInspectorReadOnlyField(
                    "Cache Older Than Source",
                    pStatus->cacheOlderThanSource ? "true" : "false");
                renderInspectorReadOnlyField("DAT References", std::to_string(pStatus->datReferenceCount));
                renderInspectorReadOnlyField(
                    "Default-Renderable DAT References",
                    std::to_string(pStatus->defaultRenderableDatReferenceCount));
                renderInspectorReadOnlyField(
                    "Helper-Only DAT References",
                    std::to_string(pStatus->helperOnlyDatReferenceCount));
                renderInspectorReadOnlyField(
                    "Aliases For Source",
                    std::to_string(pStatus->materialAliasCountForSource));
                renderInspectorReadOnlyField(
                    "Placeholder Missing Source",
                    pStatus->placeholderMissingSource ? "true" : "false");
            }

            ImGui::EndTable();
        }
        endInspectorSectionBlock();
    }

    if (pStatus != nullptr && pStatus->sourceSpriteAmbiguous && beginInspectorSectionBlock("Source SPR Candidates"))
    {
        for (const std::string &candidate : pStatus->sourceSpriteCandidates)
        {
            renderInspectorCopyButton(("Mm9SourceSpriteCandidate" + candidate).c_str(), candidate);
            ImGui::SameLine();
            renderInspectorOpenPathButton(("Mm9SourceSpriteCandidateOpen" + candidate).c_str(), candidate);
            ImGui::SameLine();
            ImGui::BulletText("%s", candidate.c_str());
        }

        endInspectorSectionBlock();
    }

    if (pStatus != nullptr
        && (!pStatus->spriteFrameTextureRefs.empty()
            || !pStatus->resolvedSpriteFrameTexturePaths.empty()
            || !pStatus->unresolvedSpriteFrameTextureRefs.empty()
            || !pStatus->ambiguousSpriteFrameTextureRefs.empty())
        && beginInspectorSectionBlock("SPR Frame Textures"))
    {
        for (const std::string &frameTextureRef : pStatus->spriteFrameTextureRefs)
        {
            renderInspectorCopyButton(("Mm9SpriteFrameTextureRef" + frameTextureRef).c_str(), frameTextureRef);
            ImGui::SameLine();
            ImGui::BulletText("%s", frameTextureRef.c_str());
        }

        if (!pStatus->resolvedSpriteFrameTexturePaths.empty())
        {
            ImGui::SeparatorText("Resolved Source DTX");

            for (const std::string &frameTexturePath : pStatus->resolvedSpriteFrameTexturePaths)
            {
                renderInspectorCopyButton(("Mm9SpriteFrameTexturePath" + frameTexturePath).c_str(), frameTexturePath);
                ImGui::SameLine();
                renderInspectorOpenPathButton(
                    ("Mm9SpriteFrameTexturePathOpen" + frameTexturePath).c_str(),
                    frameTexturePath);
                ImGui::SameLine();
                ImGui::BulletText("%s", frameTexturePath.c_str());
            }
        }

        if (!pStatus->unresolvedSpriteFrameTextureRefs.empty())
        {
            ImGui::SeparatorText("Unresolved");

            for (const std::string &frameTextureRef : pStatus->unresolvedSpriteFrameTextureRefs)
            {
                renderInspectorCopyButton(("Mm9UnresolvedSpriteFrameTextureRef" + frameTextureRef).c_str(), frameTextureRef);
                ImGui::SameLine();
                ImGui::BulletText("%s", frameTextureRef.c_str());
            }
        }

        if (!pStatus->ambiguousSpriteFrameTextureRefs.empty())
        {
            ImGui::SeparatorText("Ambiguous");

            for (const std::string &frameTextureRef : pStatus->ambiguousSpriteFrameTextureRefs)
            {
                renderInspectorCopyButton(("Mm9AmbiguousSpriteFrameTextureRef" + frameTextureRef).c_str(), frameTextureRef);
                ImGui::SameLine();
                ImGui::BulletText("%s", frameTextureRef.c_str());
            }
        }

        endInspectorSectionBlock();
    }

    if (pStatus != nullptr && pStatus->sourceDtxAmbiguous && beginInspectorSectionBlock("Source DTX Candidates"))
    {
        for (const std::string &candidate : pStatus->sourceDtxCandidates)
        {
            renderInspectorCopyButton(("Mm9SourceDtxCandidate" + candidate).c_str(), candidate);
            ImGui::SameLine();
            renderInspectorOpenPathButton(("Mm9SourceDtxCandidateOpen" + candidate).c_str(), candidate);
            ImGui::SameLine();
            ImGui::BulletText("%s", candidate.c_str());
        }

        endInspectorSectionBlock();
    }

    if (beginInspectorSectionBlock("DTX Header"))
    {
        if (beginInspectorPropertyTable("Mm9MaterialDtxHeaderFields"))
        {
            renderInspectorReadOnlyField("Width", std::to_string(texture.width));
            renderInspectorReadOnlyField("Height", std::to_string(texture.height));
            renderInspectorReadOnlyField("User/Surface Flags", std::to_string(texture.dtxSurfaceFlag));
            renderInspectorReadOnlyField("Texture Group", std::to_string(texture.dtxTextureGroup));
            renderInspectorReadOnlyField("BPP", std::to_string(texture.dtxBpp));
            renderInspectorReadOnlyField("Mipmap Count", std::to_string(texture.dtxMipmapCount));
            renderInspectorReadOnlyField("Mipmaps Used", std::to_string(texture.dtxMipmapsUsed));
            renderInspectorReadOnlyField("Flags", mm9DtxFlagsText(texture.dtxFlags));
            renderInspectorReadOnlyField("Detail Scale", std::to_string(texture.dtxDetailScale));
            renderInspectorReadOnlyField("Detail Angle", std::to_string(texture.dtxDetailAngle));
            renderInspectorReadOnlyField("Command", texture.dtxCommandString);

            if (pStatus != nullptr)
            {
                renderInspectorReadOnlyField("Header Loaded", pStatus->dtxHeaderLoaded ? "true" : "false");
                renderInspectorReadOnlyField(
                    "Header Matches Sidecar",
                    pStatus->dtxHeaderMatchesSidecar ? "true" : "false");

                if (pStatus->dtxHeader)
                {
                    const EditorMm9DtxHeader &header = *pStatus->dtxHeader;
                    renderInspectorReadOnlyField("Source Version", std::to_string(header.version));
                    renderInspectorReadOnlyField("Source File Type", std::to_string(header.fileType));
                    renderInspectorReadOnlyField("Source Width", std::to_string(header.width));
                    renderInspectorReadOnlyField("Source Height", std::to_string(header.height));
                    renderInspectorReadOnlyField("Source Mipmap Count", std::to_string(header.mipmapCount));
                    renderInspectorReadOnlyField("Source Section Count", std::to_string(header.sectionCount));
                    renderInspectorReadOnlyField("Source Mipmaps Used", std::to_string(header.mipmapsUsed));
                    renderInspectorReadOnlyField("Source Flags", mm9DtxFlagsText(header.flags));
                    renderInspectorReadOnlyField("Source User Flags", std::to_string(header.userFlags));
                    renderInspectorReadOnlyField("Source Surface Flag Alias", std::to_string(header.surfaceFlag));
                    renderInspectorReadOnlyField("Source Texture Group", std::to_string(header.textureGroup));
                    renderInspectorReadOnlyField("Source BPP", std::to_string(header.bpp));
                    renderInspectorReadOnlyField("Source Extra Bytes", mm9DtxExtraBytesText(header));
                    renderInspectorReadOnlyField("Source Detail Scale", std::to_string(header.detailScale));
                    renderInspectorReadOnlyField("Source Detail Angle", std::to_string(header.detailAngle));
                    renderInspectorReadOnlyField("Source Section Count Alias", std::to_string(header.lightFlag));
                    renderInspectorReadOnlyField("Source Unknown", std::to_string(header.unknown));
                    renderInspectorReadOnlyField("Source Non S3TC Offset", std::to_string(header.nonS3tcOffset));
                    renderInspectorReadOnlyField("Source UI Mipmap Offset", std::to_string(header.uiMipmapOffset));
                    renderInspectorReadOnlyField("Source Priority", std::to_string(header.texturePriority));
                    renderInspectorReadOnlyField("Source Command", header.commandString);
                }
            }

            ImGui::EndTable();
        }
        endInspectorSectionBlock();
    }

    if (pStatus != nullptr
        && pStatus->dtxHeader
        && beginInspectorSectionBlock("DTX Mip Payloads", false))
    {
        const EditorMm9DtxHeader &header = *pStatus->dtxHeader;

        if (header.mips.empty())
        {
            ImGui::TextDisabled("Mip payload layout is unavailable.");
        }
        else if (ImGui::BeginTable("Mm9MaterialDtxMips", 7, ImGuiTableFlags_SizingStretchProp))
        {
            ImGui::TableSetupColumn("Level", ImGuiTableColumnFlags_WidthFixed, 56.0f);
            ImGui::TableSetupColumn("Width", ImGuiTableColumnFlags_WidthFixed, 72.0f);
            ImGui::TableSetupColumn("Height", ImGuiTableColumnFlags_WidthFixed, 72.0f);
            ImGui::TableSetupColumn("Offset", ImGuiTableColumnFlags_WidthFixed, 92.0f);
            ImGui::TableSetupColumn("Bytes", ImGuiTableColumnFlags_WidthFixed, 92.0f);
            ImGui::TableSetupColumn("Available", ImGuiTableColumnFlags_WidthFixed, 86.0f);
            ImGui::TableSetupColumn("Decoded", ImGuiTableColumnFlags_WidthFixed, 78.0f);
            ImGui::TableHeadersRow();

            for (const EditorMm9DtxMipLevel &mip : header.mips)
            {
                ImGui::TableNextRow();
                ImGui::TableSetColumnIndex(0);
                ImGui::Text("%zu", mip.level);
                ImGui::TableSetColumnIndex(1);
                ImGui::Text("%u", mip.width);
                ImGui::TableSetColumnIndex(2);
                ImGui::Text("%u", mip.height);
                ImGui::TableSetColumnIndex(3);
                ImGui::Text("%zu", mip.payloadOffset);
                ImGui::TableSetColumnIndex(4);
                ImGui::Text("%zu", mip.payloadSize);
                ImGui::TableSetColumnIndex(5);
                ImGui::TextUnformatted(mip.payloadAvailable ? "true" : "false");
                ImGui::TableSetColumnIndex(6);
                ImGui::TextUnformatted(mip.decodedPreviewAvailable ? "true" : "false");
            }

            ImGui::EndTable();
        }

        endInspectorSectionBlock();
    }

    if (pStatus != nullptr
        && pStatus->dtxHeader
        && pStatus->sourcePathExists
        && beginInspectorSectionBlock("DTX Decoded Preview", false))
    {
        const EditorMm9DtxHeader &header = *pStatus->dtxHeader;
        const std::filesystem::path sourcePath(pStatus->resolvedSourcePath);
        bool renderedAnyPreview = false;

        for (const EditorMm9DtxMipLevel &mip : header.mips)
        {
            if (!mip.decodedPreviewAvailable)
            {
                continue;
            }

            const std::optional<bgfx::TextureHandle> textureHandle =
                ensureMm9DtxMipPreviewTexture(sourcePath, mip.level);

            if (!textureHandle || !bgfx::isValid(*textureHandle))
            {
                continue;
            }

            const std::optional<std::pair<int, int>> textureSize =
                mm9DtxMipPreviewTextureSize(sourcePath, mip.level);
            const float sourceWidth =
                textureSize ? static_cast<float>(textureSize->first) : static_cast<float>(mip.width);
            const float sourceHeight =
                textureSize ? static_cast<float>(textureSize->second) : static_cast<float>(mip.height);
            const float maxPreviewSize = mip.level == 0 ? 160.0f : 96.0f;
            const float scale = sourceWidth > 0.0f && sourceHeight > 0.0f
                ? std::min(1.0f, maxPreviewSize / std::max(sourceWidth, sourceHeight))
                : 1.0f;
            const ImVec2 imageSize(
                std::max(1.0f, sourceWidth * scale),
                std::max(1.0f, sourceHeight * scale));

            if (renderedAnyPreview)
            {
                ImGui::SameLine();
            }

            ImGui::BeginGroup();
            ImGui::Text("Mip %zu", mip.level);
            ImGui::TextDisabled("%ux%u", mip.width, mip.height);
            ImGui::Image(
                static_cast<ImTextureID>(static_cast<uintptr_t>(textureHandle->idx + 1)),
                imageSize,
                ImVec2(0.0f, 0.0f),
                ImVec2(1.0f, 1.0f));
            ImGui::EndGroup();
            renderedAnyPreview = true;
        }

        if (!renderedAnyPreview)
        {
            ImGui::TextDisabled("No decoded mip previews available.");
        }

        endInspectorSectionBlock();
    }

    if (pStatus != nullptr
        && pStatus->dtxHeader
        && beginInspectorSectionBlock("DTX Sections", false))
    {
        const EditorMm9DtxHeader &header = *pStatus->dtxHeader;

        if (header.sections.empty())
        {
            ImGui::TextDisabled("No DTX sections.");
        }
        else if (ImGui::BeginTable("Mm9MaterialDtxSections", 6, ImGuiTableFlags_SizingStretchProp))
        {
            ImGui::TableSetupColumn("Index", ImGuiTableColumnFlags_WidthFixed, 56.0f);
            ImGui::TableSetupColumn("Type", ImGuiTableColumnFlags_WidthStretch);
            ImGui::TableSetupColumn("Name", ImGuiTableColumnFlags_WidthStretch);
            ImGui::TableSetupColumn("Offset", ImGuiTableColumnFlags_WidthFixed, 92.0f);
            ImGui::TableSetupColumn("Bytes", ImGuiTableColumnFlags_WidthFixed, 92.0f);
            ImGui::TableSetupColumn("Available", ImGuiTableColumnFlags_WidthFixed, 86.0f);
            ImGui::TableHeadersRow();

            for (const EditorMm9DtxSection &section : header.sections)
            {
                ImGui::TableNextRow();
                ImGui::TableSetColumnIndex(0);
                ImGui::Text("%zu", section.sectionIndex);
                ImGui::TableSetColumnIndex(1);
                ImGui::TextUnformatted(section.type.c_str());
                ImGui::TableSetColumnIndex(2);
                ImGui::TextUnformatted(section.name.c_str());
                ImGui::TableSetColumnIndex(3);
                ImGui::Text("%zu", section.payloadOffset);
                ImGui::TableSetColumnIndex(4);
                ImGui::Text("%zu", section.payloadSize);
                ImGui::TableSetColumnIndex(5);
                ImGui::TextUnformatted(section.payloadAvailable ? "true" : "false");
            }

            ImGui::EndTable();
        }

        if (header.trailingBytes > 0)
        {
            ImGui::Text("Trailing bytes: %zu", header.trailingBytes);
        }

        endInspectorSectionBlock();
    }
}

void EditorMainWindow::renderMm9RawObjectInspector(EditorSession &session, size_t objectIndex)
{
    const EditorDocument &document = session.document();

    if (document.kind() != EditorDocument::Kind::Mm9Dat || !document.hasMm9DatLoadedSidecars())
    {
        ImGui::TextDisabled("MM9 DAT sidecars are not loaded.");
        return;
    }

    const EditorMm9LoadedSidecars &sidecars = document.mm9DatLoadedSidecars();
    const EditorMm9RawObjectsSidecar &rawObjects = sidecars.rawObjects;

    if (objectIndex >= rawObjects.objects.size())
    {
        ImGui::Text("DAT raw object index %zu is out of range.", objectIndex);
        return;
    }

    const EditorMm9RawObject &object = rawObjects.objects[objectIndex];

    if (beginInspectorSectionBlock("DAT Raw Object"))
    {
        if (beginInspectorPropertyTable("Mm9RawObjectFields"))
        {
            renderInspectorCopyableReadOnlyField("Source Object Index", std::to_string(object.objectIndex));
            renderInspectorCopyableReadOnlyField("Source Class", object.name);
            renderInspectorCopyableReadOnlyField("Name Property", mm9RawObjectPropertyValue(object, "Name"));
            renderInspectorReadOnlyField("Position", mm9RawObjectPropertyValue(object, "Pos"));
            renderInspectorReadOnlyField("Rotation", mm9RawObjectPropertyValue(object, "Rotation"));
            renderInspectorReadOnlyField("Scale", mm9RawObjectPropertyValue(object, "Scale"));
            renderInspectorReadOnlyField("Dims", mm9RawObjectPropertyValue(object, "Dims"));
            renderInspectorReadOnlyField("Data Length", std::to_string(object.dataLength));
            renderInspectorReadOnlyField("Property Count", std::to_string(object.propertyCount));
            renderInspectorReadOnlyField(
                "Trailing Bytes",
                object.trailingHex.empty() ? std::string("<none>") : object.trailingHex);
            ImGui::EndTable();
        }
        endInspectorSectionBlock();
    }

    if (beginInspectorSectionBlock("Event Binding", false))
    {
        const Game::Mm9EventObject *pEventObject = nullptr;
        std::optional<size_t> linkedEventObjectIndex;
        std::optional<size_t> linkedMechanismIndex;

        for (size_t eventObjectIndex = 0; eventObjectIndex < sidecars.events.objects.size(); ++eventObjectIndex)
        {
            const Game::Mm9EventObject &eventObject = sidecars.events.objects[eventObjectIndex];

            if (eventObject.sourceObjectIndex == static_cast<int>(object.objectIndex))
            {
                pEventObject = &eventObject;
                linkedEventObjectIndex = eventObjectIndex;
                linkedMechanismIndex = findMm9MechanismIndexByObjectId(sidecars.events, eventObject.objectId);
                break;
            }
        }

        if (pEventObject == nullptr)
        {
            ImGui::TextDisabled("No generated event object for this source object.");
        }
        else if (beginInspectorPropertyTable("Mm9RawObjectEventFields"))
        {
            renderInspectorCopyableReadOnlyField("Object Id", pEventObject->objectId);
            renderInspectorCopyableReadOnlyField("Source Class", pEventObject->sourceClass);
            renderInspectorCopyableReadOnlyField("Source Name", pEventObject->sourceName);
            renderInspectorCopyableReadOnlyField("Raw Object Ref", pEventObject->rawObjectRef);
            renderInspectorReadOnlyField("Raw Properties", std::to_string(pEventObject->rawPropertyCount));
            renderInspectorReadOnlyField(
                "Classifications",
                pEventObject->classifications.empty()
                    ? std::string("<none>")
                    : pEventObject->classifications.front());
            ImGui::EndTable();

            if (renderInspectorJumpButton("Select Event Object", linkedEventObjectIndex.has_value()))
            {
                session.select(EditorSelectionKind::Mm9EventObject, *linkedEventObjectIndex);
            }

            ImGui::SameLine();

            if (renderInspectorJumpButton("Select Mechanism", linkedMechanismIndex.has_value()))
            {
                session.select(EditorSelectionKind::Mm9Mechanism, *linkedMechanismIndex);
            }
        }
        endInspectorSectionBlock();
    }

    if (beginInspectorSectionBlock("Source Asset References", false))
    {
        size_t referenceCount = 0;
        size_t requiredUnresolvedCount = 0;
        size_t optionalUnresolvedCount = 0;
        size_t ambiguousCount = 0;

        for (const EditorMm9RawObjectAssetReferenceStatus &status : document.mm9RawObjectAssetReferenceStatuses())
        {
            if (status.sourceObjectIndex != object.objectIndex)
            {
                continue;
            }

            if (status.ambiguous)
            {
                ++ambiguousCount;
            }

            if (!status.resolved || status.ambiguous)
            {
                if (status.required)
                {
                    ++requiredUnresolvedCount;
                }
                else
                {
                    ++optionalUnresolvedCount;
                }
            }
        }

        if (beginInspectorPropertyTable("Mm9RawObjectAssetReferenceSummary"))
        {
            renderInspectorReadOnlyField("Required Issues", std::to_string(requiredUnresolvedCount));
            renderInspectorReadOnlyField("Optional Issues", std::to_string(optionalUnresolvedCount));
            renderInspectorReadOnlyField("Ambiguous", std::to_string(ambiguousCount));
            ImGui::EndTable();
        }

        const auto rawObjectAssetIssueLabel =
            [](const EditorMm9RawObjectAssetReferenceStatus &status) -> const char *
        {
            if (status.ambiguous)
            {
                return status.required ? "ambiguous required" : "ambiguous optional";
            }

            if (!status.resolved)
            {
                return status.required ? "unresolved required" : "unresolved optional";
            }

            if (status.aliasApplied)
            {
                return "resolved by alias";
            }

            return "resolved";
        };

        for (const EditorMm9RawObjectAssetReferenceStatus &status : document.mm9RawObjectAssetReferenceStatuses())
        {
            if (status.sourceObjectIndex != object.objectIndex)
            {
                continue;
            }

            if (referenceCount == 0)
            {
                if (!ImGui::BeginTable("Mm9RawObjectAssetReferences", 9, ImGuiTableFlags_SizingStretchProp))
                {
                    break;
                }

                ImGui::TableSetupColumn("Property", ImGuiTableColumnFlags_WidthStretch);
                ImGui::TableSetupColumn("Issue", ImGuiTableColumnFlags_WidthFixed, 132.0f);
                ImGui::TableSetupColumn("Family", ImGuiTableColumnFlags_WidthFixed, 96.0f);
                ImGui::TableSetupColumn("Value", ImGuiTableColumnFlags_WidthStretch);
                ImGui::TableSetupColumn("Required", ImGuiTableColumnFlags_WidthFixed, 76.0f);
                ImGui::TableSetupColumn("Resolved", ImGuiTableColumnFlags_WidthFixed, 72.0f);
                ImGui::TableSetupColumn("Ambiguous", ImGuiTableColumnFlags_WidthFixed, 82.0f);
                ImGui::TableSetupColumn("Path", ImGuiTableColumnFlags_WidthStretch);
                ImGui::TableSetupColumn("Actions", ImGuiTableColumnFlags_WidthFixed, 112.0f);
                ImGui::TableHeadersRow();
            }

            ++referenceCount;
            ImGui::TableNextRow();
            ImGui::TableSetColumnIndex(0);
            ImGui::TextUnformatted(status.propertyName.c_str());
            ImGui::TableSetColumnIndex(1);
            if (!status.resolved || status.ambiguous)
            {
                ImGui::TextColored(colorFromRgb(status.required ? 0xE7A46C : 0xD8B277), "%s",
                    rawObjectAssetIssueLabel(status));
            }
            else
            {
                ImGui::TextUnformatted(rawObjectAssetIssueLabel(status));
            }
            ImGui::TableSetColumnIndex(2);
            ImGui::TextUnformatted(status.sourceFamily.c_str());
            ImGui::TableSetColumnIndex(3);
            ImGui::TextUnformatted(status.sourceValue.c_str());
            ImGui::TableSetColumnIndex(4);
            ImGui::TextUnformatted(status.required ? "true" : "false");
            ImGui::TableSetColumnIndex(5);
            ImGui::TextUnformatted(status.resolved ? "true" : "false");
            ImGui::TableSetColumnIndex(6);
            ImGui::TextUnformatted(status.ambiguous ? "true" : "false");
            ImGui::TableSetColumnIndex(7);
            ImGui::TextUnformatted(status.resolvedSourcePath.c_str());
            ImGui::TableSetColumnIndex(8);
            renderInspectorCopyButton(
                ("Mm9RawObjectAssetReference" + std::to_string(status.sourceObjectIndex) + status.propertyName).c_str(),
                status.resolvedSourcePath.empty() ? status.sourceValue : status.resolvedSourcePath);
            ImGui::SameLine();
            renderInspectorOpenPathButton(
                ("Mm9RawObjectAssetReferenceOpen"
                    + std::to_string(status.sourceObjectIndex)
                    + status.propertyName).c_str(),
                status.resolvedSourcePath);
        }

        if (referenceCount > 0)
        {
            ImGui::EndTable();
        }
        else
        {
            ImGui::TextDisabled("No source asset references detected from string properties.");
        }

        bool candidateTableOpen = false;

        for (const EditorMm9RawObjectAssetReferenceStatus &status : document.mm9RawObjectAssetReferenceStatuses())
        {
            if (status.sourceObjectIndex != object.objectIndex || status.sourceCandidates.empty())
            {
                continue;
            }

            if (!candidateTableOpen)
            {
                candidateTableOpen =
                    ImGui::BeginTable("Mm9RawObjectAssetReferenceCandidates", 4, ImGuiTableFlags_SizingStretchProp);

                if (!candidateTableOpen)
                {
                    break;
                }

                ImGui::TableSetupColumn("Property", ImGuiTableColumnFlags_WidthStretch);
                ImGui::TableSetupColumn("Family", ImGuiTableColumnFlags_WidthFixed, 96.0f);
                ImGui::TableSetupColumn("Candidate", ImGuiTableColumnFlags_WidthStretch);
                ImGui::TableSetupColumn("Actions", ImGuiTableColumnFlags_WidthFixed, 112.0f);
                ImGui::TableHeadersRow();
            }

            for (const std::string &candidate : status.sourceCandidates)
            {
                ImGui::TableNextRow();
                ImGui::TableSetColumnIndex(0);
                ImGui::TextUnformatted(status.propertyName.c_str());
                ImGui::TableSetColumnIndex(1);
                ImGui::TextUnformatted(status.sourceFamily.c_str());
                ImGui::TableSetColumnIndex(2);
                ImGui::TextUnformatted(candidate.c_str());
                ImGui::TableSetColumnIndex(3);
                renderInspectorCopyButton(("Mm9RawObjectAssetCandidate" + candidate).c_str(), candidate);
                ImGui::SameLine();
                renderInspectorOpenPathButton(("Mm9RawObjectAssetCandidateOpen" + candidate).c_str(), candidate);
            }
        }

        if (candidateTableOpen)
        {
            ImGui::EndTable();
        }

        endInspectorSectionBlock();
    }

    if (beginInspectorSectionBlock("Raw Properties"))
    {
        if (object.properties.empty())
        {
            ImGui::TextDisabled("No raw properties.");
        }
        else if (ImGui::BeginTable("Mm9RawObjectProperties", 8, ImGuiTableFlags_SizingStretchProp))
        {
            ImGui::TableSetupColumn("Index", ImGuiTableColumnFlags_WidthFixed, 54.0f);
            ImGui::TableSetupColumn("Name", ImGuiTableColumnFlags_WidthStretch);
            ImGui::TableSetupColumn("Code", ImGuiTableColumnFlags_WidthFixed, 54.0f);
            ImGui::TableSetupColumn("Flags", ImGuiTableColumnFlags_WidthFixed, 64.0f);
            ImGui::TableSetupColumn("Declared", ImGuiTableColumnFlags_WidthFixed, 74.0f);
            ImGui::TableSetupColumn("Consumed", ImGuiTableColumnFlags_WidthFixed, 78.0f);
            ImGui::TableSetupColumn("Decoded", ImGuiTableColumnFlags_WidthFixed, 66.0f);
            ImGui::TableSetupColumn("Value", ImGuiTableColumnFlags_WidthStretch);
            ImGui::TableHeadersRow();

            for (size_t propertyIndex = 0; propertyIndex < object.properties.size(); ++propertyIndex)
            {
                const EditorMm9RawObjectProperty &property = object.properties[propertyIndex];
                ImGui::TableNextRow();
                ImGui::TableSetColumnIndex(0);
                ImGui::Text("%zu", propertyIndex);
                ImGui::TableSetColumnIndex(1);
                ImGui::TextUnformatted(property.name.c_str());
                ImGui::TableSetColumnIndex(2);
                ImGui::Text("%d", property.code);
                ImGui::TableSetColumnIndex(3);
                ImGui::Text("%d", property.flags);
                ImGui::TableSetColumnIndex(4);
                ImGui::Text("%zu", property.declaredDataLength);
                ImGui::TableSetColumnIndex(5);
                ImGui::Text("%zu", property.consumedDataLength);
                ImGui::TableSetColumnIndex(6);
                ImGui::TextUnformatted(property.decoded ? "true" : "false");
                ImGui::TableSetColumnIndex(7);
                ImGui::TextUnformatted(property.valueJson.c_str());
            }

            ImGui::EndTable();
        }
        endInspectorSectionBlock();
    }

    if (beginInspectorSectionBlock("Raw Property Bytes", false))
    {
        for (size_t propertyIndex = 0; propertyIndex < object.properties.size(); ++propertyIndex)
        {
            const EditorMm9RawObjectProperty &property = object.properties[propertyIndex];
            const std::string label = std::to_string(propertyIndex) + " - " + property.name;

            if (ImGui::TreeNodeEx(label.c_str()))
            {
                if (beginInspectorPropertyTable("Mm9RawObjectPropertyBytes"))
                {
                    renderInspectorReadOnlyField("Raw Hex", property.rawHex);
                    renderInspectorReadOnlyField("Value JSON", property.valueJson);
                    renderInspectorReadOnlyField("Declared Length", std::to_string(property.declaredDataLength));
                    renderInspectorReadOnlyField("Consumed Length", std::to_string(property.consumedDataLength));
                    renderInspectorReadOnlyField("Decoded", property.decoded ? "true" : "false");
                    ImGui::EndTable();
                }
                ImGui::TreePop();
            }
        }
        endInspectorSectionBlock();
    }
}

void EditorMainWindow::renderMm9EventObjectInspector(EditorSession &session, size_t eventObjectIndex)
{
    const EditorDocument &document = session.document();

    if (document.kind() != EditorDocument::Kind::Mm9Dat || !document.hasMm9DatLoadedSidecars())
    {
        ImGui::TextDisabled("MM9 DAT sidecars are not loaded.");
        return;
    }

    const EditorMm9LoadedSidecars &sidecars = document.mm9DatLoadedSidecars();

    if (eventObjectIndex >= sidecars.events.objects.size())
    {
        ImGui::Text("MM9 event object index %zu is out of range.", eventObjectIndex);
        return;
    }

    const Game::Mm9EventObject &eventObject = sidecars.events.objects[eventObjectIndex];
    const std::optional<size_t> linkedRawObjectIndex =
        findMm9RawObjectIndexBySourceObjectIndex(sidecars.rawObjects, eventObject.sourceObjectIndex);
    const std::optional<size_t> linkedMechanismIndex =
        findMm9MechanismIndexByObjectId(sidecars.events, eventObject.objectId);

    if (beginInspectorSectionBlock("Event Object"))
    {
        if (beginInspectorPropertyTable("Mm9EventObjectFields"))
        {
            renderInspectorCopyableReadOnlyField("Object Id", eventObject.objectId);
            renderInspectorCopyableReadOnlyField("Source Object Index", std::to_string(eventObject.sourceObjectIndex));
            renderInspectorCopyableReadOnlyField("Source Class", eventObject.sourceClass);
            renderInspectorCopyableReadOnlyField("Source Name", eventObject.sourceName);
            renderInspectorReadOnlyField("Classifications", joinMm9Classifications(eventObject.classifications));
            renderInspectorCopyableReadOnlyField("Raw Object Ref", eventObject.rawObjectRef);
            renderInspectorReadOnlyField("Raw Property Count", std::to_string(eventObject.rawPropertyCount));
            ImGui::EndTable();
        }

        if (renderInspectorJumpButton("Select Raw Object", linkedRawObjectIndex.has_value()))
        {
            session.select(EditorSelectionKind::Mm9RawObject, *linkedRawObjectIndex);
        }

        ImGui::SameLine();

        if (renderInspectorJumpButton("Select Mechanism", linkedMechanismIndex.has_value()))
        {
            session.select(EditorSelectionKind::Mm9Mechanism, *linkedMechanismIndex);
        }

        endInspectorSectionBlock();
    }

    if (beginInspectorSectionBlock("Normalized Properties", false))
    {
        if (eventObject.normalizedProperties.empty())
        {
            ImGui::TextDisabled("No normalized properties.");
        }
        else if (beginInspectorPropertyTable("Mm9EventObjectNormalizedProperties"))
        {
            for (const std::pair<const std::string, std::string> &property : eventObject.normalizedProperties)
            {
                renderInspectorReadOnlyField(property.first.c_str(), property.second);
            }
            ImGui::EndTable();
        }
        endInspectorSectionBlock();
    }

    if (beginInspectorSectionBlock("Raw Property Evidence", false))
    {
        if (eventObject.rawProperties.empty())
        {
            ImGui::TextDisabled("No raw property refs.");
        }
        else if (ImGui::BeginTable("Mm9EventObjectRawProperties", 6, ImGuiTableFlags_SizingStretchProp))
        {
            ImGui::TableSetupColumn("Index", ImGuiTableColumnFlags_WidthFixed, 54.0f);
            ImGui::TableSetupColumn("Name", ImGuiTableColumnFlags_WidthStretch);
            ImGui::TableSetupColumn("Decoded", ImGuiTableColumnFlags_WidthFixed, 66.0f);
            ImGui::TableSetupColumn("Code", ImGuiTableColumnFlags_WidthFixed, 54.0f);
            ImGui::TableSetupColumn("Flags", ImGuiTableColumnFlags_WidthFixed, 64.0f);
            ImGui::TableSetupColumn("Raw Ref", ImGuiTableColumnFlags_WidthStretch);
            ImGui::TableHeadersRow();

            for (const Game::Mm9EventObject::RawPropertyRef &property : eventObject.rawProperties)
            {
                ImGui::TableNextRow();
                ImGui::TableSetColumnIndex(0);
                ImGui::Text("%zu", property.propertyIndex);
                ImGui::TableSetColumnIndex(1);
                ImGui::TextUnformatted(property.name.c_str());
                ImGui::TableSetColumnIndex(2);
                ImGui::TextUnformatted(property.decoded ? "true" : "false");
                ImGui::TableSetColumnIndex(3);
                ImGui::Text("%d", property.code);
                ImGui::TableSetColumnIndex(4);
                ImGui::Text("%d", property.flags);
                ImGui::TableSetColumnIndex(5);
                ImGui::TextUnformatted(property.rawRef.c_str());
            }

            ImGui::EndTable();
        }
        endInspectorSectionBlock();
    }

    if (beginInspectorSectionBlock("Bindings"))
    {
        size_t bindingCount = 0;

        for (const Game::Mm9EventBinding &binding : sidecars.events.bindings)
        {
            if (binding.objectId != eventObject.objectId)
            {
                continue;
            }

            ++bindingCount;

            for (const Game::Mm9EventBindingTarget &target : binding.targets)
            {
                if (beginInspectorPropertyTable("Mm9EventObjectBindingTarget"))
                {
                    const std::optional<size_t> linkedWorldModelIndex = target.bmodelIndex
                        ? findMm9WorldModelIndexBySourceModelIndex(
                            sidecars.datWorld,
                            static_cast<size_t>(*target.bmodelIndex))
                        : std::nullopt;
                    const EditorMm9DatWorldModelSummary *pTargetWorldModel =
                        linkedWorldModelIndex && *linkedWorldModelIndex < sidecars.datWorld.worldModels.size()
                            ? &sidecars.datWorld.worldModels[*linkedWorldModelIndex]
                            : nullptr;

                    renderInspectorReadOnlyField("Target Kind", target.targetKind);
                    renderInspectorCopyableReadOnlyField("Target Id", target.targetId);
                    renderInspectorReadOnlyField("Confidence", target.confidence);
                    renderInspectorReadOnlyField(
                        "BModel Index",
                        target.bmodelIndex ? std::to_string(*target.bmodelIndex) : std::string("<none>"));
                    renderInspectorCopyableReadOnlyField("BModel Name", target.bmodelName);
                    renderInspectorCopyableReadOnlyField("Source Model Name", target.sourceModelName);
                    ImGui::EndTable();

                    if (renderInspectorJumpButton("Select Target World Model", linkedWorldModelIndex.has_value()))
                    {
                        session.select(EditorSelectionKind::Mm9WorldModel, *linkedWorldModelIndex);
                    }
                }
                ImGui::Spacing();
            }
        }

        if (bindingCount == 0)
        {
            ImGui::TextDisabled("No generated bindings for this object.");
        }

        endInspectorSectionBlock();
    }
}

void EditorMainWindow::renderMm9MechanismInspector(EditorSession &session, size_t mechanismIndex)
{
    const EditorDocument &document = session.document();

    if (document.kind() != EditorDocument::Kind::Mm9Dat || !document.hasMm9DatLoadedSidecars())
    {
        ImGui::TextDisabled("MM9 DAT sidecars are not loaded.");
        return;
    }

    const EditorMm9LoadedSidecars &sidecars = document.mm9DatLoadedSidecars();
    const Game::Mm9EventsData &events = sidecars.events;

    if (mechanismIndex >= events.mechanisms.size())
    {
        ImGui::Text("MM9 mechanism index %zu is out of range.", mechanismIndex);
        return;
    }

    const Game::Mm9EventMechanism &mechanism = events.mechanisms[mechanismIndex];
    const Game::Mm9EventObject *pEventObject = nullptr;
    const EditorMm9RawObject *pRawObject = nullptr;
    std::optional<size_t> linkedEventObjectIndex;
    std::optional<size_t> linkedRawObjectIndex;

    for (size_t eventObjectIndex = 0; eventObjectIndex < events.objects.size(); ++eventObjectIndex)
    {
        const Game::Mm9EventObject &eventObject = events.objects[eventObjectIndex];

        if (eventObject.objectId == mechanism.objectId)
        {
            pEventObject = &eventObject;
            linkedEventObjectIndex = eventObjectIndex;
            break;
        }
    }

    for (size_t rawObjectIndex = 0; rawObjectIndex < sidecars.rawObjects.objects.size(); ++rawObjectIndex)
    {
        const EditorMm9RawObject &rawObject = sidecars.rawObjects.objects[rawObjectIndex];

        if (rawObject.objectIndex == static_cast<size_t>(mechanism.sourceObjectIndex))
        {
            pRawObject = &rawObject;
            linkedRawObjectIndex = rawObjectIndex;
            break;
        }
    }

    const auto renderSidecarCandidateEvidence =
        [this](
            const char *pLabel,
            const std::vector<Game::Mm9EventBindingTarget::MovableWorldModelCandidate> &candidates)
    {
        if (candidates.empty())
        {
            return;
        }

        ImGui::SetNextItemOpen(false, ImGuiCond_FirstUseEver);
        if (!ImGui::TreeNodeEx(pLabel))
        {
            return;
        }

        for (size_t candidateIndex = 0; candidateIndex < candidates.size(); ++candidateIndex)
        {
            const Game::Mm9EventBindingTarget::MovableWorldModelCandidate &candidate = candidates[candidateIndex];
            ImGui::PushID(static_cast<int>(candidateIndex));
            if (beginInspectorPropertyTable("Mm9MechanismSidecarWorldModelCandidate"))
            {
                renderInspectorCopyableReadOnlyField("Source Model Index", std::to_string(candidate.sourceModelIndex));
                renderInspectorCopyableReadOnlyField("Source Model Name", candidate.sourceName);
                renderInspectorReadOnlyField("Movable", candidate.movable ? "true" : "false");
                renderInspectorReadOnlyField(
                    "World Translation LT",
                    mm9FloatVectorText(candidate.worldTranslationLt));
                renderInspectorReadOnlyField("Distance LT", std::to_string(candidate.distanceLt));
                renderInspectorReadOnlyField(
                    "Exact Binding Claims",
                    std::to_string(candidate.claimedByExactBindings.size()));
                ImGui::EndTable();
            }

            if (!candidate.claimedByExactBindings.empty()
                && beginInspectorPropertyTable("Mm9MechanismSidecarWorldModelCandidateClaims"))
            {
                for (size_t claimIndex = 0; claimIndex < candidate.claimedByExactBindings.size(); ++claimIndex)
                {
                    const Game::Mm9EventBindingTarget::MovableWorldModelCandidate::ExactBindingClaim &claim =
                        candidate.claimedByExactBindings[claimIndex];
                    const std::string label = "Claim " + std::to_string(claimIndex);
                    std::string claimText = "source_object_index=" + std::to_string(claim.sourceObjectIndex);

                    if (!claim.sourceName.empty())
                    {
                        claimText += ", source_name=" + claim.sourceName;
                    }

                    if (!claim.confidence.empty())
                    {
                        claimText += ", confidence=" + claim.confidence;
                    }

                    renderInspectorCopyableReadOnlyField(label.c_str(), claimText);
                }

                ImGui::EndTable();
            }

            ImGui::PopID();
            ImGui::Spacing();
        }

        ImGui::TreePop();
    };

    if (beginInspectorSectionBlock("Mechanism"))
    {
        if (beginInspectorPropertyTable("Mm9MechanismFields"))
        {
            renderInspectorCopyableReadOnlyField("Mechanism Id", mechanism.mechanismId);
            renderInspectorCopyableReadOnlyField("Object Id", mechanism.objectId);
            renderInspectorCopyableReadOnlyField("Source Object Index", std::to_string(mechanism.sourceObjectIndex));
            renderInspectorCopyableReadOnlyField("Source Class", mechanism.sourceClass);
            renderInspectorCopyableReadOnlyField("Source Name", mechanism.sourceName);
            renderInspectorReadOnlyField("Kind", mechanism.kind.empty() ? std::string("<unknown>") : mechanism.kind);
            renderInspectorReadOnlyField("Event Object Found", pEventObject != nullptr ? "true" : "false");
            renderInspectorReadOnlyField("Raw Object Found", pRawObject != nullptr ? "true" : "false");
            ImGui::EndTable();
        }

        if (renderInspectorJumpButton("Select Event Object", linkedEventObjectIndex.has_value()))
        {
            session.select(EditorSelectionKind::Mm9EventObject, *linkedEventObjectIndex);
        }

        ImGui::SameLine();

        if (renderInspectorJumpButton("Select Raw Object", linkedRawObjectIndex.has_value()))
        {
            session.select(EditorSelectionKind::Mm9RawObject, *linkedRawObjectIndex);
        }

        endInspectorSectionBlock();
    }

    if (beginInspectorSectionBlock("Activation And Motion"))
    {
        if (beginInspectorPropertyTable("Mm9MechanismMotionFields"))
        {
            renderInspectorReadOnlyField(
                "Start Open",
                mm9OptionalBoolText(mechanism.activation.startOpen, mechanism.activation.hasStartOpen));
            renderInspectorReadOnlyField(
                "Locked",
                mm9OptionalBoolText(mechanism.activation.locked, mechanism.activation.hasLocked));
            renderInspectorReadOnlyField(
                "Push Open",
                mm9OptionalBoolText(mechanism.activation.pushOpen, mechanism.activation.hasPushOpen));
            renderInspectorReadOnlyField(
                "Touch To Open",
                mm9OptionalBoolText(mechanism.activation.touchToOpen, mechanism.activation.hasTouchToOpen));
            renderInspectorReadOnlyField(
                "Lock On Close",
                mm9OptionalBoolText(mechanism.activation.lockOnClose, mechanism.activation.hasLockOnClose));
            renderInspectorReadOnlyField(
                "Reopen On Contact",
                mm9OptionalBoolText(
                    mechanism.activation.reopenOnContact,
                    mechanism.activation.hasReopenOnContact));
            renderInspectorReadOnlyField(
                "Move Dir LT",
                mechanism.linear.hasMoveDir ? mm9FloatVectorText(mechanism.linear.moveDirLt) : "<unknown>");
            renderInspectorReadOnlyField(
                "Move Distance LT",
                mechanism.linear.hasMoveDist
                    ? std::to_string(mechanism.linear.moveDistLt)
                    : std::string("<unknown>"));
            renderInspectorReadOnlyField(
                "Open Speed LT/s",
                mechanism.linear.hasOpenSpeed
                    ? std::to_string(mechanism.linear.openSpeedLtPerSecond)
                    : std::string("<unknown>"));
            renderInspectorReadOnlyField(
                "Close Speed LT/s",
                mechanism.linear.hasCloseSpeed
                    ? std::to_string(mechanism.linear.closeSpeedLtPerSecond)
                    : std::string("<unknown>"));
            renderInspectorReadOnlyField(
                "Rotation Point LT",
                mechanism.rotation.hasRotationPoint
                    ? mm9FloatVectorText(mechanism.rotation.rotationPointLt)
                    : std::string("<unknown>"));
            renderInspectorReadOnlyField(
                "Rotation Angles Deg",
                mechanism.rotation.hasRotationAngles
                    ? mm9FloatVectorText(mechanism.rotation.rotationAnglesDeg)
                    : std::string("<unknown>"));
            renderInspectorReadOnlyField(
                "Open Away",
                mm9OptionalBoolText(mechanism.rotation.openAway, mechanism.rotation.hasOpenAway));
            renderInspectorReadOnlyField(
                "Move Delay Seconds",
                mechanism.timing.hasMoveDelaySecondsSource
                    ? std::to_string(mechanism.timing.moveDelaySecondsSource)
                    : std::string("<unknown>"));
            renderInspectorReadOnlyField(
                "Open Wait Seconds",
                mechanism.timing.hasOpenWaitSecondsSource
                    ? std::to_string(mechanism.timing.openWaitSecondsSource)
                    : std::string("<unknown>"));
            renderInspectorReadOnlyField("Sound Slots", std::to_string(mechanism.sounds.size()));
            renderInspectorReadOnlyField("Trigger Outputs", std::to_string(mechanism.triggerOutputs.size()));
            ImGui::EndTable();
        }
        endInspectorSectionBlock();
    }

    if (beginInspectorSectionBlock("Sounds", false))
    {
        if (mechanism.sounds.empty())
        {
            ImGui::TextDisabled("No generated sound evidence for this mechanism.");
        }
        else if (beginInspectorPropertyTable("Mm9MechanismSounds"))
        {
            for (size_t soundIndex = 0; soundIndex < mechanism.sounds.size(); ++soundIndex)
            {
                const Game::Mm9EventMechanismSound &sound = mechanism.sounds[soundIndex];
                const std::string propertyText =
                    sound.sourceProperty.empty() ? std::string("<unknown>") : sound.sourceProperty;
                const std::string soundNameText =
                    sound.soundName.empty() ? std::string("<empty>") : sound.soundName;
                std::string soundText = "phase=" + sound.phase
                    + ", property=" + propertyText
                    + ", sound=" + soundNameText
                    + ", authored=" + boolText(sound.authored);
                const std::string label = "Sound " + std::to_string(soundIndex);
                renderInspectorCopyableReadOnlyField(label.c_str(), soundText);
            }

            ImGui::EndTable();
        }

        endInspectorSectionBlock();
    }

    if (beginInspectorSectionBlock("Trigger Outputs", false))
    {
        if (mechanism.triggerOutputs.empty())
        {
            ImGui::TextDisabled("No generated trigger outputs for this mechanism.");
        }
        else if (beginInspectorPropertyTable("Mm9MechanismTriggerOutputs"))
        {
            for (size_t outputIndex = 0; outputIndex < mechanism.triggerOutputs.size(); ++outputIndex)
            {
                const Game::Mm9EventTriggerOutput &output = mechanism.triggerOutputs[outputIndex];
                std::string outputText = "phase=" + output.phase
                    + ", slot=" + std::to_string(output.slot)
                    + ", target=" + (output.targetName.empty() ? std::string("<none>") : output.targetName)
                    + ", message=" + (output.messageName.empty() ? std::string("<none>") : output.messageName)
                    + ", resolution=" + (output.resolution.empty() ? std::string("<unknown>") : output.resolution);
                const std::string label = "Output " + std::to_string(outputIndex);
                renderInspectorCopyableReadOnlyField(label.c_str(), outputText);
            }

            ImGui::EndTable();
        }

        endInspectorSectionBlock();
    }

    if (beginInspectorSectionBlock("Preview"))
    {
        const Game::Mm9EventBinding *pBinding = findMm9EventBindingForObject(events, mechanism.objectId);
        const bool hasMotion =
            (mechanism.linear.hasMoveDir
                && mechanism.linear.hasMoveDist
                && std::fabs(mechanism.linear.moveDistLt) > 0.0001f)
            || (mechanism.rotation.hasRotationPoint && mechanism.rotation.hasRotationAngles);
        bool hasWorldModelTarget = false;

        if (pBinding != nullptr)
        {
            for (const Game::Mm9EventBindingTarget &target : pBinding->targets)
            {
                if (target.targetKind == "odm_bmodel" && target.bmodelIndex.has_value())
                {
                    hasWorldModelTarget = true;
                    break;
                }
            }
        }

        float previewProgress = 0.0f;
        const bool hasPreview =
            m_viewport.tryGetMm9MechanismPreviewProgress(document, mechanismIndex, previewProgress);
        const bool canPreview = hasMotion && hasWorldModelTarget;
        const std::string previewReason =
            canPreview
                ? std::string("previewable")
                : (!hasMotion && !hasWorldModelTarget
                    ? std::string("inert: missing motion and world-model target")
                    : (!hasMotion
                        ? std::string("inert: missing motion")
                        : std::string("inert: missing world-model target")));

        if (beginInspectorPropertyTable("Mm9MechanismPreviewFields"))
        {
            renderInspectorReadOnlyField("Previewable", canPreview ? "true" : "false");
            renderInspectorReadOnlyField("Preview Status", previewReason);
            renderInspectorReadOnlyField("Target World Model", hasWorldModelTarget ? "true" : "false");
            renderInspectorReadOnlyField("Motion", hasMotion ? "true" : "false");
            renderInspectorReadOnlyField("Active", hasPreview ? "true" : "false");
            renderInspectorReadOnlyField("Progress", std::to_string(previewProgress));
            ImGui::EndTable();
        }

        if (canPreview)
        {
            float editedProgress = previewProgress;
            ImGui::SetNextItemWidth(-1.0f);
            if (ImGui::SliderFloat("Preview Progress", &editedProgress, 0.0f, 1.0f, "%.2f"))
            {
                m_viewport.setMm9MechanismPreviewProgress(document, mechanismIndex, editedProgress);
            }

            if (ImGui::Button("Closed"))
            {
                m_viewport.setMm9MechanismPreviewProgress(document, mechanismIndex, 0.0f);
            }

            ImGui::SameLine();

            if (ImGui::Button("Half"))
            {
                m_viewport.setMm9MechanismPreviewProgress(document, mechanismIndex, 0.5f);
            }

            ImGui::SameLine();

            if (ImGui::Button("Open"))
            {
                m_viewport.setMm9MechanismPreviewProgress(document, mechanismIndex, 1.0f);
            }

            ImGui::SameLine();

            if (ImGui::Button("Clear"))
            {
                m_viewport.clearMm9MechanismPreview(document);
            }
        }
        else
        {
            ImGui::TextDisabled("Preview requires a generated world-model target and movement data.");
        }

        endInspectorSectionBlock();
    }

    if (beginInspectorSectionBlock("Source Evidence", false))
    {
        if (pEventObject != nullptr && beginInspectorPropertyTable("Mm9MechanismEventEvidence"))
        {
            renderInspectorCopyableReadOnlyField("Event Object Id", pEventObject->objectId);
            renderInspectorCopyableReadOnlyField("Raw Object Ref", pEventObject->rawObjectRef);
            renderInspectorReadOnlyField("Classifications", joinMm9Classifications(pEventObject->classifications));
            renderInspectorReadOnlyField("Raw Properties", std::to_string(pEventObject->rawPropertyCount));
            ImGui::EndTable();
        }

        if (pRawObject != nullptr && beginInspectorPropertyTable("Mm9MechanismRawObjectEvidence"))
        {
            renderInspectorCopyableReadOnlyField("Raw Object Index", std::to_string(pRawObject->objectIndex));
            renderInspectorCopyableReadOnlyField("Raw Class", pRawObject->name);
            renderInspectorCopyableReadOnlyField("Name Property", mm9RawObjectPropertyValue(*pRawObject, "Name"));
            renderInspectorReadOnlyField("Position", mm9RawObjectPropertyValue(*pRawObject, "Pos"));
            renderInspectorReadOnlyField("Rotation", mm9RawObjectPropertyValue(*pRawObject, "Rotation"));
            renderInspectorReadOnlyField("Dims", mm9RawObjectPropertyValue(*pRawObject, "Dims"));
            renderInspectorReadOnlyField("Property Count", std::to_string(pRawObject->propertyCount));
            ImGui::EndTable();
        }

        if (pEventObject == nullptr && pRawObject == nullptr)
        {
            ImGui::TextDisabled("No event or raw object evidence for this mechanism.");
        }

        endInspectorSectionBlock();
    }

    if (beginInspectorSectionBlock("Generated Binding Targets"))
    {
        size_t bindingCount = 0;

        for (const Game::Mm9EventBinding &binding : events.bindings)
        {
            if (binding.objectId != mechanism.objectId)
            {
                continue;
            }

            ++bindingCount;

            for (const Game::Mm9EventBindingTarget &target : binding.targets)
            {
                if (beginInspectorPropertyTable("Mm9MechanismBindingTarget"))
                {
                    const std::optional<size_t> linkedWorldModelIndex = target.bmodelIndex
                        ? findMm9WorldModelIndexBySourceModelIndex(
                            sidecars.datWorld,
                            static_cast<size_t>(*target.bmodelIndex))
                        : std::nullopt;
                    const EditorMm9DatWorldModelSummary *pTargetWorldModel =
                        linkedWorldModelIndex && *linkedWorldModelIndex < sidecars.datWorld.worldModels.size()
                            ? &sidecars.datWorld.worldModels[*linkedWorldModelIndex]
                            : nullptr;

                    renderInspectorReadOnlyField("Target Kind", target.targetKind);
                    renderInspectorCopyableReadOnlyField("Target Id", target.targetId);
                    renderInspectorReadOnlyField("Confidence", target.confidence);
                    renderInspectorReadOnlyField(
                        "Source World Model Index",
                        target.bmodelIndex ? std::to_string(*target.bmodelIndex) : std::string("<none>"));
                    renderInspectorCopyableReadOnlyField("BModel Name", target.bmodelName);
                    renderInspectorCopyableReadOnlyField("Source World Model Name", target.sourceModelName);
                    renderInspectorReadOnlyField(
                        "Source Polygon Group",
                        target.sourcePolygonGroup.has_value() ? "true" : "false");
                    renderInspectorReadOnlyField(
                        "Group Source Model Index",
                        target.sourcePolygonGroup
                            ? std::to_string(target.sourcePolygonGroup->sourceModelIndex)
                            : std::string("<none>"));
                    renderInspectorCopyableReadOnlyField(
                        "Group Source Model Name",
                        target.sourcePolygonGroup
                            ? target.sourcePolygonGroup->sourceModelName
                            : std::string("<none>"));
                    renderInspectorReadOnlyField(
                        "Group Source Polygons",
                        target.sourcePolygonGroup
                            ? std::to_string(target.sourcePolygonGroup->sourcePolyCount)
                            : std::string("<none>"));
                    renderInspectorReadOnlyField(
                        "Group Source Surfaces",
                        target.sourcePolygonGroup
                            ? std::to_string(target.sourcePolygonGroup->sourceSurfaceCount)
                            : std::string("<none>"));
                    renderInspectorReadOnlyField(
                        "Target DAT Model Found",
                        pTargetWorldModel != nullptr ? "true" : "false");
                    renderInspectorReadOnlyField(
                        "Target DAT Movable Role",
                        pTargetWorldModel != nullptr && pTargetWorldModel->roles.movable ? "true" : "false");
                    renderInspectorReadOnlyField(
                        "Target DAT Roles",
                        pTargetWorldModel != nullptr
                            ? mm9WorldModelRolesText(pTargetWorldModel->roles)
                            : std::string("<none>"));
                    ImGui::EndTable();

                    if (renderInspectorJumpButton("Select Target World Model", linkedWorldModelIndex.has_value()))
                    {
                        session.select(EditorSelectionKind::Mm9WorldModel, *linkedWorldModelIndex);
                    }
                }

                renderSidecarCandidateEvidence(
                    "Sidecar Candidates By Rotation Point",
                    target.nearestMovableWorldModelsByRotationPoint);
                renderSidecarCandidateEvidence(
                    "Sidecar Candidates By Position",
                    target.nearestMovableWorldModelsByPosition);
                ImGui::Spacing();
            }
        }

        if (mechanism.rotation.hasRotationPoint && mechanism.rotation.rotationPointLt.size() >= 3)
        {
            ImGui::SetNextItemOpen(false, ImGuiCond_FirstUseEver);
            if (ImGui::TreeNodeEx("Nearest Movable DAT World Models"))
            {
                const std::vector<Mm9MovableWorldModelCandidate> candidates =
                    nearestMm9MovableWorldModels(sidecars.datWorld, mechanism.rotation.rotationPointLt, 5);

                if (candidates.empty())
                {
                    ImGui::TextDisabled("No movable world-model candidates near the rotation point.");
                }
                else
                {
                    for (const Mm9MovableWorldModelCandidate &candidate : candidates)
                    {
                        if (beginInspectorPropertyTable("Mm9MechanismNearestWorldModelCandidate"))
                        {
                            renderInspectorCopyableReadOnlyField(
                                "Source Model Index",
                                std::to_string(candidate.sourceModelIndex));
                            renderInspectorCopyableReadOnlyField("Source Model Name", candidate.sourceName);
                            renderInspectorReadOnlyField(
                                "World Translation LT",
                                mm9Vec3Text(candidate.worldTranslationLt));
                            renderInspectorReadOnlyField("Distance LT", std::to_string(candidate.distanceLt));
                            ImGui::EndTable();
                        }
                        ImGui::Spacing();
                    }
                }

                ImGui::TreePop();
            }
        }

        if (bindingCount == 0)
        {
            ImGui::TextDisabled("No generated binding targets for this mechanism.");
        }

        endInspectorSectionBlock();
    }
}

void EditorMainWindow::renderMm9EventScriptInspector(EditorSession &session, size_t scriptIndex)
{
    const EditorDocument &document = session.document();

    if (document.kind() != EditorDocument::Kind::Mm9Dat || !document.hasMm9DatLoadedSidecars())
    {
        ImGui::TextDisabled("MM9 DAT sidecars are not loaded.");
        return;
    }

    const Game::Mm9EventsData &events = document.mm9DatLoadedSidecars().events;
    const EditorMm9DatLevelMetadata &metadata = document.mm9DatLevelMetadata();

    if (scriptIndex >= events.scripts.size())
    {
        ImGui::Text("MM9 script index %zu is out of range.", scriptIndex);
        return;
    }

    const Game::Mm9EventScript &script = events.scripts[scriptIndex];

    if (beginInspectorSectionBlock("Script Provenance"))
    {
        if (beginInspectorPropertyTable("Mm9EventScriptFields"))
        {
            renderInspectorCopyableReadOnlyField("Script Id", script.scriptId);
            renderInspectorCopyOpenReadOnlyField(
                "Source Path",
                script.sourcePath,
                resolveMm9LevelRelativePath(document, script.sourcePath).generic_string());
            renderInspectorCopyOpenReadOnlyField(
                "Generated Lua",
                events.generatedLua,
                resolveMm9LevelRelativePath(document, events.generatedLua).generic_string());
            renderInspectorCopyOpenReadOnlyField(
                "Generated Script IR",
                events.generatedScriptIr,
                resolveMm9LevelRelativePath(document, events.generatedScriptIr).generic_string());
            renderInspectorCopyOpenReadOnlyField(
                "Authored Source Asset Aliases",
                metadata.sidecars.sourceAssetAliases
                    ? *metadata.sidecars.sourceAssetAliases
                    : std::string("<none>"),
                metadata.sidecars.sourceAssetAliases
                    ? resolveMm9LevelRelativePath(document, *metadata.sidecars.sourceAssetAliases).generic_string()
                    : std::string());
            renderInspectorReadOnlyField(
                "Source Asset Alias Role",
                metadata.sidecars.sourceAssetAliases ? "authored_override" : "none");
            renderInspectorReadOnlyField("Includes", std::to_string(script.includes.size()));
            renderInspectorReadOnlyField("Labels", std::to_string(script.labels.size()));
            renderInspectorReadOnlyField("Registered Triggers", std::to_string(script.registeredTriggerCount));
            renderInspectorReadOnlyField("Trigger Edges", std::to_string(script.triggerEdges.size()));
            renderInspectorReadOnlyField("Movement Commands", std::to_string(script.movementCommandCount));
            renderInspectorReadOnlyField("Unknown Commands", std::to_string(script.unknownCommandCount));
            renderInspectorReadOnlyField("Command Count", std::to_string(script.commandCount));
            ImGui::EndTable();
        }
        endInspectorSectionBlock();
    }

    if (beginInspectorSectionBlock("Includes", false))
    {
        if (script.includes.empty())
        {
            ImGui::TextDisabled("No source script includes.");
        }
        else if (beginInspectorPropertyTable("Mm9EventScriptIncludes"))
        {
            for (size_t includeIndex = 0; includeIndex < script.includes.size(); ++includeIndex)
            {
                const Game::Mm9EventScript::Include &include = script.includes[includeIndex];
                const std::string includeText = "line=" + std::to_string(include.line)
                    + ", path=" + (include.path.empty() ? std::string("<none>") : include.path);
                const std::string label = "Include " + std::to_string(includeIndex);
                renderInspectorCopyableReadOnlyField(label.c_str(), includeText);
            }

            ImGui::EndTable();
        }

        endInspectorSectionBlock();
    }

    if (beginInspectorSectionBlock("Labels", false))
    {
        if (script.labels.empty())
        {
            ImGui::TextDisabled("No source script labels.");
        }
        else if (beginInspectorPropertyTable("Mm9EventScriptLabels"))
        {
            for (size_t labelIndex = 0; labelIndex < script.labels.size(); ++labelIndex)
            {
                const Game::Mm9EventScript::Label &scriptLabel = script.labels[labelIndex];
                const std::string labelText = "line=" + std::to_string(scriptLabel.line)
                    + ", name=" + (scriptLabel.name.empty() ? std::string("<none>") : scriptLabel.name);
                const std::string label = "Label " + std::to_string(labelIndex);
                renderInspectorCopyableReadOnlyField(label.c_str(), labelText);
            }

            ImGui::EndTable();
        }

        endInspectorSectionBlock();
    }

    if (beginInspectorSectionBlock("Registered Triggers", false))
    {
        if (script.registeredTriggers.empty())
        {
            ImGui::TextDisabled("No registered script triggers.");
        }
        else if (beginInspectorPropertyTable("Mm9EventScriptRegisteredTriggers"))
        {
            for (size_t triggerIndex = 0; triggerIndex < script.registeredTriggers.size(); ++triggerIndex)
            {
                const Game::Mm9EventScript::RegisteredTrigger &trigger =
                    script.registeredTriggers[triggerIndex];
                std::string triggerText = "line=" + std::to_string(trigger.line)
                    + ", message=" + (trigger.message.empty() ? std::string("<none>") : trigger.message)
                    + ", callback=" + (trigger.callback.empty() ? std::string("<none>") : trigger.callback);
                if (!trigger.argumentsRaw.empty())
                {
                    triggerText += ", raw=" + trigger.argumentsRaw;
                }
                const std::string label = "Trigger " + std::to_string(triggerIndex);
                renderInspectorCopyableReadOnlyField(label.c_str(), triggerText);
            }

            ImGui::EndTable();
        }

        endInspectorSectionBlock();
    }

    if (beginInspectorSectionBlock("Trigger Edges", false))
    {
        if (script.triggerEdges.empty())
        {
            ImGui::TextDisabled("No outgoing script trigger edges.");
        }
        else if (beginInspectorPropertyTable("Mm9EventScriptTriggerEdges"))
        {
            for (size_t edgeIndex = 0; edgeIndex < script.triggerEdges.size(); ++edgeIndex)
            {
                const Game::Mm9EventScript::TriggerEdge &edge = script.triggerEdges[edgeIndex];
                std::string edgeText = "line=" + std::to_string(edge.line)
                    + ", target="
                    + (edge.targetExpression.empty() ? std::string("<none>") : edge.targetExpression)
                    + ", message="
                    + (edge.messageExpression.empty() ? std::string("<none>") : edge.messageExpression);
                if (!edge.argumentsRaw.empty())
                {
                    edgeText += ", raw=" + edge.argumentsRaw;
                }
                const std::string label = "Edge " + std::to_string(edgeIndex);
                renderInspectorCopyableReadOnlyField(label.c_str(), edgeText);
            }

            ImGui::EndTable();
        }

        endInspectorSectionBlock();
    }

    const auto renderScriptCommands =
        [](const char *pSectionLabel,
           const char *pTableId,
           const char *pEmptyLabel,
           const std::vector<Game::Mm9EventScript::ScriptCommand> &commands)
    {
        if (beginInspectorSectionBlock(pSectionLabel, false))
        {
            if (commands.empty())
            {
                ImGui::TextDisabled("%s", pEmptyLabel);
            }
            else if (beginInspectorPropertyTable(pTableId))
            {
                for (size_t commandIndex = 0; commandIndex < commands.size(); ++commandIndex)
                {
                    const Game::Mm9EventScript::ScriptCommand &command = commands[commandIndex];
                    std::string commandText = "line=" + std::to_string(command.line)
                        + ", command=" + (command.command.empty() ? std::string("<none>") : command.command);
                    if (!command.argumentsRaw.empty())
                    {
                        commandText += ", raw=" + command.argumentsRaw;
                    }
                    const std::string label = "Command " + std::to_string(commandIndex);
                    renderInspectorCopyableReadOnlyField(label.c_str(), commandText);
                }

                ImGui::EndTable();
            }

            endInspectorSectionBlock();
        }
    };

    renderScriptCommands(
        "Movement Commands",
        "Mm9EventScriptMovementCommands",
        "No movement script commands.",
        script.movementCommands);
    renderScriptCommands(
        "Unknown Commands",
        "Mm9EventScriptUnknownCommands",
        "No unknown script commands.",
        script.unknownCommands);

    const ReadOnlyTextPreview generatedLuaPreview =
        loadReadOnlyTextPreview(resolveMm9LevelRelativePath(document, events.generatedLua));
    renderReadOnlyTextPreviewSection(
        "Generated Lua Preview",
        "Mm9EventGeneratedLuaPreview",
        generatedLuaPreview,
        false);

    const ReadOnlyTextPreview generatedScriptIrPreview =
        loadReadOnlyTextPreview(resolveMm9LevelRelativePath(document, events.generatedScriptIr));
    renderReadOnlyTextPreviewSection(
        "Generated Script IR Preview",
        "Mm9EventGeneratedScriptIrPreview",
        generatedScriptIrPreview,
        false);
}

std::string extractQuotedIndoorSourceId(const std::string &message)
{
    const size_t firstQuote = message.find('\'');

    if (firstQuote == std::string::npos)
    {
        return {};
    }

    const size_t secondQuote = message.find('\'', firstQuote + 1);

    if (secondQuote == std::string::npos || secondQuote <= firstQuote + 1)
    {
        return {};
    }

    return message.substr(firstQuote + 1, secondQuote - firstQuote - 1);
}

enum class IndoorSourceDiagnosticGroup
{
    SourceAsset,
    Portal,
    Trigger,
    Mechanism,
    Marker,
    Other
};

IndoorSourceDiagnosticGroup indoorSourceDiagnosticGroup(const std::string &message)
{
    if (stringContains(message, "source asset") || stringContains(message, "asset path"))
    {
        return IndoorSourceDiagnosticGroup::SourceAsset;
    }

    if (stringContains(message, " portal "))
    {
        return IndoorSourceDiagnosticGroup::Portal;
    }

    if (stringContains(message, " trigger ") || stringContains(message, "surface '"))
    {
        return IndoorSourceDiagnosticGroup::Trigger;
    }

    if (stringContains(message, " mechanism "))
    {
        return IndoorSourceDiagnosticGroup::Mechanism;
    }

    if (stringContains(message, " entity ")
        || stringContains(message, " light ")
        || stringContains(message, " spawn "))
    {
        return IndoorSourceDiagnosticGroup::Marker;
    }

    return IndoorSourceDiagnosticGroup::Other;
}

const char *indoorSourceDiagnosticGroupLabel(IndoorSourceDiagnosticGroup group)
{
    switch (group)
    {
    case IndoorSourceDiagnosticGroup::SourceAsset:
        return "Source File";
    case IndoorSourceDiagnosticGroup::Portal:
        return "Portals";
    case IndoorSourceDiagnosticGroup::Trigger:
        return "Triggers";
    case IndoorSourceDiagnosticGroup::Mechanism:
        return "Mechanisms";
    case IndoorSourceDiagnosticGroup::Marker:
        return "Markers";
    case IndoorSourceDiagnosticGroup::Other:
        return "Other";
    }

    return "Other";
}

bool selectIndoorSourceDiagnosticTarget(
    EditorSession &session,
    const EditorIndoorGeometryMetadata &sourceGeometry,
    const std::string &message)
{
    const std::string sourceId = extractQuotedIndoorSourceId(message);

    if (sourceId.empty())
    {
        return false;
    }

    if (stringContains(message, "portal '"))
    {
        for (const EditorIndoorGeometryPortalMetadata &portal : sourceGeometry.portals)
        {
            if (portal.id == sourceId && portal.runtimeFaceIndex)
            {
                session.replaceInteractiveFaceSelection(*portal.runtimeFaceIndex);
                return true;
            }
        }
    }

    if (stringContains(message, "surface '"))
    {
        for (const EditorIndoorGeometrySurfaceMetadata &surface : sourceGeometry.surfaces)
        {
            if (surface.id == sourceId && surface.runtimeFaceIndex)
            {
                session.replaceInteractiveFaceSelection(*surface.runtimeFaceIndex);
                return true;
            }
        }
    }

    if (stringContains(message, "mechanism '"))
    {
        for (const EditorIndoorGeometryMechanismMetadata &mechanism : sourceGeometry.mechanisms)
        {
            if (mechanism.id == sourceId && mechanism.runtimeDoorIndex)
            {
                session.select(EditorSelectionKind::Door, *mechanism.runtimeDoorIndex);
                return true;
            }
        }
    }

    if (stringContains(message, "entity '"))
    {
        for (const EditorIndoorGeometryEntityMetadata &entity : sourceGeometry.entities)
        {
            if (entity.id == sourceId && entity.runtimeEntityIndex)
            {
                session.select(EditorSelectionKind::Entity, *entity.runtimeEntityIndex);
                return true;
            }
        }
    }

    if (stringContains(message, "light '"))
    {
        for (const EditorIndoorGeometryLightMetadata &light : sourceGeometry.lights)
        {
            if (light.id == sourceId && light.runtimeLightIndex)
            {
                session.select(EditorSelectionKind::Light, *light.runtimeLightIndex);
                return true;
            }
        }
    }

    if (stringContains(message, "spawn '"))
    {
        for (const EditorIndoorGeometrySpawnMetadata &spawn : sourceGeometry.spawns)
        {
            if (spawn.id == sourceId && spawn.runtimeSpawnIndex)
            {
                session.select(EditorSelectionKind::Spawn, *spawn.runtimeSpawnIndex);
                return true;
            }
        }
    }

    return false;
}

bool editIndoorSourceStringVector(
    EditorSession &session,
    const char *pLabel,
    std::vector<std::string> &values,
    size_t capacity)
{
    std::string joinedValues;

    for (size_t index = 0; index < values.size(); ++index)
    {
        if (index != 0)
        {
            joinedValues += ", ";
        }

        joinedValues += values[index];
    }

    if (!editStringField(session, pLabel, joinedValues, capacity))
    {
        return false;
    }

    values.clear();
    std::stringstream stream(joinedValues);
    std::string entry;

    while (std::getline(stream, entry, ','))
    {
        const std::string trimmedEntry = trimCopy(entry);

        if (!trimmedEntry.empty())
        {
            values.push_back(trimmedEntry);
        }
    }

    return true;
}

bool editIndoorSourceOptionalFloat(
    EditorSession &session,
    const char *pLabel,
    std::optional<float> &value,
    float defaultValue)
{
    float editedValue = value.value_or(defaultValue);

    if (!editFloatField(session, pLabel, editedValue, 1.0f))
    {
        return false;
    }

    value = editedValue;
    return true;
}

bool editIndoorSourceOptionalUInt32(
    EditorSession &session,
    const char *pLabel,
    std::optional<uint32_t> &value,
    uint32_t defaultValue)
{
    uint32_t editedValue = value.value_or(defaultValue);

    if (!editUInt32Field(session, pLabel, editedValue))
    {
        return false;
    }

    value = editedValue;
    return true;
}

void renderIndoorSourceMetadataEditor(
    EditorSession &session,
    EditorIndoorGeometryMetadata &sourceGeometry)
{
    bool changed = false;

    if (beginInspectorSectionBlock("Source Metadata", false))
    {
        if (beginInspectorPropertyTable("IndoorSourceMetadataFields"))
        {
            changed = editStringField(session, "Source Asset", sourceGeometry.source.assetPath, 256) || changed;
            changed = editStringField(session, "Authoring File", sourceGeometry.source.authoringFile, 256) || changed;
            changed = editStringField(session, "Root Node", sourceGeometry.source.rootNodeName, 128) || changed;
            changed = editStringField(
                session,
                "Coordinate System",
                sourceGeometry.source.coordinateSystem,
                64) || changed;
            changed = editFloatField(session, "Unit Scale", sourceGeometry.source.unitScale, 1.0f) || changed;
            ImGui::EndTable();
        }

        endInspectorSectionBlock();
    }

    if (beginInspectorSectionBlock("Rooms", false))
    {
        for (size_t roomIndex = 0; roomIndex < sourceGeometry.rooms.size(); ++roomIndex)
        {
            EditorIndoorGeometryRoomMetadata &room = sourceGeometry.rooms[roomIndex];
            const std::string label =
                room.id.empty() ? "Room " + std::to_string(roomIndex) : room.id + "##Room" + std::to_string(roomIndex);

            if (ImGui::TreeNodeEx(label.c_str(), ImGuiTreeNodeFlags_DefaultOpen))
            {
                if (beginInspectorPropertyTable(("IndoorSourceRoom" + std::to_string(roomIndex)).c_str()))
                {
                    changed = editStringField(session, "Id", room.id, 128) || changed;
                    changed = editStringField(session, "Name", room.name, 128) || changed;
                    changed = editIndoorSourceStringVector(
                        session,
                        "Source Nodes",
                        room.sourceNodeNames,
                        512) || changed;
                    ImGui::EndTable();
                }

                ImGui::TreePop();
            }
        }

        endInspectorSectionBlock();
    }

    if (beginInspectorSectionBlock("Portals", false))
    {
        for (size_t portalIndex = 0; portalIndex < sourceGeometry.portals.size(); ++portalIndex)
        {
            EditorIndoorGeometryPortalMetadata &portal = sourceGeometry.portals[portalIndex];
            const std::string label = portal.id.empty()
                ? "Portal " + std::to_string(portalIndex)
                : portal.id + "##Portal" + std::to_string(portalIndex);

            if (ImGui::TreeNodeEx(label.c_str(), ImGuiTreeNodeFlags_DefaultOpen))
            {
                if (beginInspectorPropertyTable(("IndoorSourcePortal" + std::to_string(portalIndex)).c_str()))
                {
                    changed = editStringField(session, "Id", portal.id, 128) || changed;
                    changed = editStringField(session, "Name", portal.name, 128) || changed;
                    changed = editStringField(session, "Front Room", portal.frontRoom, 128) || changed;
                    changed = editStringField(session, "Back Room", portal.backRoom, 128) || changed;
                    changed = editStringField(session, "Source Node", portal.sourceNodeName, 256) || changed;
                    ImGui::EndTable();
                }

                ImGui::TreePop();
            }
        }

        endInspectorSectionBlock();
    }

    if (beginInspectorSectionBlock("Trigger Surfaces", false))
    {
        for (size_t surfaceIndex = 0; surfaceIndex < sourceGeometry.surfaces.size(); ++surfaceIndex)
        {
            EditorIndoorGeometrySurfaceMetadata &surface = sourceGeometry.surfaces[surfaceIndex];
            const std::string label = surface.id.empty()
                ? "Surface " + std::to_string(surfaceIndex)
                : surface.id + "##Surface" + std::to_string(surfaceIndex);

            if (ImGui::TreeNodeEx(label.c_str(), ImGuiTreeNodeFlags_DefaultOpen))
            {
                if (beginInspectorPropertyTable(("IndoorSourceSurface" + std::to_string(surfaceIndex)).c_str()))
                {
                    changed = editStringField(session, "Id", surface.id, 128) || changed;
                    changed = editStringField(session, "Source Node", surface.sourceNodeName, 256) || changed;
                    changed = editStringField(session, "Material", surface.materialId, 128) || changed;

                    if (!surface.trigger)
                    {
                        if (ImGui::Button("Add Trigger"))
                        {
                            session.captureUndoSnapshot();
                            surface.trigger = EditorIndoorGeometrySurfaceTriggerMetadata{};
                            changed = true;
                        }
                    }
                    else
                    {
                        changed = editMapEventField(session, "Event Id", surface.trigger->eventId) || changed;
                        changed = editStringField(session, "Trigger Type", surface.trigger->type, 64) || changed;
                    }

                    ImGui::EndTable();
                }

                ImGui::TreePop();
            }
        }

        endInspectorSectionBlock();
    }

    if (beginInspectorSectionBlock("Mechanisms", false))
    {
        for (size_t mechanismIndex = 0; mechanismIndex < sourceGeometry.mechanisms.size(); ++mechanismIndex)
        {
            EditorIndoorGeometryMechanismMetadata &mechanism = sourceGeometry.mechanisms[mechanismIndex];
            const std::string label = mechanism.id.empty()
                ? "Mechanism " + std::to_string(mechanismIndex)
                : mechanism.id + "##Mechanism" + std::to_string(mechanismIndex);

            if (ImGui::TreeNodeEx(label.c_str(), ImGuiTreeNodeFlags_DefaultOpen))
            {
                if (beginInspectorPropertyTable(("IndoorSourceMechanism" + std::to_string(mechanismIndex)).c_str()))
                {
                    changed = editStringField(session, "Id", mechanism.id, 128) || changed;
                    changed = editStringField(session, "Name", mechanism.name, 128) || changed;
                    changed = editStringField(session, "Kind", mechanism.kind, 64) || changed;
                    changed = editStringField(session, "Initial State", mechanism.initialState, 32) || changed;
                    changed = editIndoorSourceStringVector(session, "Source Nodes", mechanism.sourceNodeNames, 512)
                        || changed;
                    changed = editIndoorSourceStringVector(
                        session,
                        "Trigger Surfaces",
                        mechanism.triggerSurfaceIds,
                        512) || changed;
                    changed = editIndoorSourceOptionalUInt32(
                        session,
                        "Door Id",
                        mechanism.doorId,
                        mechanism.mechanismId)
                        || changed;
                    changed = editIndoorSourceOptionalFloat(session, "Move Distance", mechanism.moveDistance, 512.0f)
                        || changed;
                    changed = editIndoorSourceOptionalUInt32(session, "Move Length", mechanism.moveLength, 512)
                        || changed;
                    changed = editIndoorSourceOptionalFloat(session, "Open Speed", mechanism.openSpeed, 128.0f)
                        || changed;
                    changed = editIndoorSourceOptionalFloat(session, "Close Speed", mechanism.closeSpeed, 128.0f)
                        || changed;
                    ImGui::EndTable();
                }

                ImGui::TreePop();
            }
        }

        endInspectorSectionBlock();
    }

    if (beginInspectorSectionBlock("Markers", false))
    {
        for (size_t entityIndex = 0; entityIndex < sourceGeometry.entities.size(); ++entityIndex)
        {
            EditorIndoorGeometryEntityMetadata &entity = sourceGeometry.entities[entityIndex];
            const std::string label = entity.id.empty()
                ? "Decoration " + std::to_string(entityIndex)
                : entity.id + "##Entity" + std::to_string(entityIndex);

            if (ImGui::TreeNodeEx(label.c_str()))
            {
                if (beginInspectorPropertyTable(("IndoorSourceEntity" + std::to_string(entityIndex)).c_str()))
                {
                    changed = editStringField(session, "Id", entity.id, 128) || changed;
                    changed = editStringField(session, "Kind", entity.kind, 64) || changed;
                    changed = editStringField(session, "Source Node", entity.sourceNodeName, 256) || changed;
                    changed = editUInt16Field(session, "Decoration List Id", entity.decorationListId) || changed;
                    changed = editMapEventField(session, "Event Primary", entity.eventIdPrimary) || changed;
                    changed = editMapEventField(session, "Event Secondary", entity.eventIdSecondary) || changed;
                    ImGui::EndTable();
                }

                ImGui::TreePop();
            }
        }

        for (size_t lightIndex = 0; lightIndex < sourceGeometry.lights.size(); ++lightIndex)
        {
            EditorIndoorGeometryLightMetadata &light = sourceGeometry.lights[lightIndex];
            const std::string label = light.id.empty()
                ? "Light " + std::to_string(lightIndex)
                : light.id + "##Light" + std::to_string(lightIndex);

            if (ImGui::TreeNodeEx(label.c_str()))
            {
                if (beginInspectorPropertyTable(("IndoorSourceLight" + std::to_string(lightIndex)).c_str()))
                {
                    changed = editStringField(session, "Id", light.id, 128) || changed;
                    changed = editStringField(session, "Source Node", light.sourceNodeName, 256) || changed;
                    changed = editStringField(session, "Type", light.type, 64) || changed;
                    changed = editInt16Field(session, "Radius", light.radius) || changed;
                    changed = editInt16Field(session, "Brightness", light.brightness) || changed;
                    ImGui::EndTable();
                }

                ImGui::TreePop();
            }
        }

        for (size_t spawnIndex = 0; spawnIndex < sourceGeometry.spawns.size(); ++spawnIndex)
        {
            EditorIndoorGeometrySpawnMetadata &spawn = sourceGeometry.spawns[spawnIndex];
            const std::string label = spawn.id.empty()
                ? "Spawn " + std::to_string(spawnIndex)
                : spawn.id + "##Spawn" + std::to_string(spawnIndex);

            if (ImGui::TreeNodeEx(label.c_str()))
            {
                if (beginInspectorPropertyTable(("IndoorSourceSpawn" + std::to_string(spawnIndex)).c_str()))
                {
                    changed = editStringField(session, "Id", spawn.id, 128) || changed;
                    changed = editStringField(session, "Source Node", spawn.sourceNodeName, 256) || changed;
                    changed = editUInt16Field(session, "Type Id", spawn.typeId) || changed;
                    changed = editUInt16Field(session, "Index", spawn.index) || changed;
                    changed = editUInt16Field(session, "Radius", spawn.radius) || changed;
                    changed = editUInt32Field(session, "Group", spawn.group) || changed;
                    ImGui::EndTable();
                }

                ImGui::TreePop();
            }
        }

        endInspectorSectionBlock();
    }

    if (changed)
    {
        session.noteDocumentMutated("Edited indoor source metadata");
    }
}

void EditorMainWindow::renderIndoorDocumentSummary(EditorSession &session)
{
    const EditorDocument &document = session.document();
    const Game::IndoorMapData &indoorGeometry = document.indoorGeometry();
    const Game::IndoorSceneData &sceneData = document.indoorSceneData();
    const EditorIndoorGeometryMetadata &sourceGeometry = document.indoorGeometryMetadata();

    ImGui::Text("Map: %s", document.displayName().c_str());
    ImGui::Text("Scene: %s", document.sceneVirtualPath().c_str());
    ImGui::Spacing();
    ImGui::Text("Vertices: %zu", indoorGeometry.vertices.size());
    ImGui::Text("Faces: %zu", indoorGeometry.faces.size());
    ImGui::Text("Sectors: %zu", indoorGeometry.sectors.size());
    ImGui::Text("Entities: %zu", indoorGeometry.entities.size());
    ImGui::Text("Lights: %zu", indoorGeometry.lights.size());
    ImGui::Text("Spawns: %zu", indoorGeometry.spawns.size());
    ImGui::Text("Actors: %zu", sceneData.initialState.actors.size());
    ImGui::Text("Sprite Objects: %zu", sceneData.initialState.spriteObjects.size());
    ImGui::Text("Chests: %zu", sceneData.initialState.chests.size());
    ImGui::Text("Doors: %zu", sceneData.initialState.doors.size());
    ImGui::Text("Dirty: %s", document.isDirty() ? "yes" : "no");
    ImGui::Spacing();
    ImGui::SeparatorText("Source Geometry");
    ImGui::Text("Metadata: %s", document.hasIndoorGeometryMetadata() ? "yes" : "no");
    const char *pSourceAsset =
        sourceGeometry.source.assetPath.empty() ? "<none>" : sourceGeometry.source.assetPath.c_str();
    ImGui::Text("Source Asset: %s", pSourceAsset);
    ImGui::Text(
        "Rooms %zu  Portals %zu  Surfaces %zu  Mechanisms %zu",
        sourceGeometry.rooms.size(),
        sourceGeometry.portals.size(),
        sourceGeometry.surfaces.size(),
        sourceGeometry.mechanisms.size());

    std::vector<std::string> sourceDiagnostics;

    for (const std::string &message : session.validationMessages())
    {
        if (isIndoorSourceDiagnostic(message))
        {
            sourceDiagnostics.push_back(message);
        }
    }

    const bool hasSourceMetadata =
        document.hasIndoorGeometryMetadata() || !isIndoorGeometryMetadataEmpty(sourceGeometry);
    const bool sourceMissing = std::any_of(
        sourceDiagnostics.begin(),
        sourceDiagnostics.end(),
        [](const std::string &message)
        {
            return stringContains(message, "source asset is missing")
                || stringContains(message, "source asset path is empty");
        });
    const char *pSourceStatus = "No Source Metadata";
    uint32_t sourceStatusTextColor = 0xAEB6C2;

    if (hasSourceMetadata && sourceMissing)
    {
        pSourceStatus = "Source Missing";
        sourceStatusTextColor = 0xF5D3D3;
    }
    else if (hasSourceMetadata && !sourceDiagnostics.empty())
    {
        pSourceStatus = "Source Has Warnings";
        sourceStatusTextColor = 0xF2DEC2;
    }
    else if (hasSourceMetadata)
    {
        pSourceStatus = "Source OK";
        sourceStatusTextColor = 0xD7F0DB;
    }

    ImGui::PushStyleColor(ImGuiCol_Text, colorFromRgb(sourceStatusTextColor));
    ImGui::Text("Status: %s", pSourceStatus);
    ImGui::PopStyleColor();

    if (beginInspectorPropertyTable("IndoorSourceGeometryImportFields"))
    {
        beginInspectorFieldRow("Model Path");
        const float browseButtonWidth = 30.0f;
        ImGui::SetNextItemWidth(-browseButtonWidth - ImGui::GetStyle().ItemSpacing.x);
        ImGui::InputText(
            "##IndoorSourceGeometryImportPath",
            m_indoorSourceGeometryImportPath,
            sizeof(m_indoorSourceGeometryImportPath));
        ImGui::SameLine();

        if (ImGui::Button("...", ImVec2(browseButtonWidth, 0.0f)))
        {
            openModelFileBrowser(
                ModelImportTarget::ImportIndoorSourceGeometry,
                m_indoorSourceGeometryImportPath);
        }

        ImGui::EndTable();
    }

    if (ImGui::Button("Import Source Geometry", ImVec2(180.0f, 0.0f)))
    {
        std::string errorMessage;

        if (session.importIndoorSourceGeometryFromModel(m_indoorSourceGeometryImportPath, errorMessage))
        {
            rememberModelImportDirectory(m_indoorSourceGeometryImportPath);
            setStatusMessage(StatusMessageKind::Success, "Imported indoor source geometry metadata.");
        }
        else
        {
            setStatusMessage(StatusMessageKind::Error, errorMessage);
            session.logError(errorMessage);
        }
    }
    ImGui::SameLine();

    if (!hasSourceMetadata)
    {
        ImGui::BeginDisabled();
    }

    if (ImGui::Button("Build Source Geometry", ImVec2(180.0f, 0.0f)))
    {
        std::string errorMessage;

        if (session.buildActiveDocument(errorMessage))
        {
            setStatusMessage(StatusMessageKind::Success, "Built indoor source geometry.");
        }
        else
        {
            setStatusMessage(StatusMessageKind::Error, errorMessage);
            session.logError(errorMessage);
        }
    }

    if (!hasSourceMetadata)
    {
        ImGui::EndDisabled();
    }

    if (!sourceDiagnostics.empty() && beginInspectorSectionBlock("Source Diagnostics"))
    {
        const std::array<IndoorSourceDiagnosticGroup, 6> groups = {{
            IndoorSourceDiagnosticGroup::SourceAsset,
            IndoorSourceDiagnosticGroup::Portal,
            IndoorSourceDiagnosticGroup::Trigger,
            IndoorSourceDiagnosticGroup::Mechanism,
            IndoorSourceDiagnosticGroup::Marker,
            IndoorSourceDiagnosticGroup::Other
        }};

        for (IndoorSourceDiagnosticGroup group : groups)
        {
            size_t groupIssueCount = 0;

            for (const std::string &message : sourceDiagnostics)
            {
                if (indoorSourceDiagnosticGroup(message) == group)
                {
                    ++groupIssueCount;
                }
            }

            if (groupIssueCount == 0)
            {
                continue;
            }

            ImGui::PushStyleColor(ImGuiCol_Text, colorFromRgb(0xF8E4C7));
            ImGui::Text("%s · %zu", indoorSourceDiagnosticGroupLabel(group), groupIssueCount);
            ImGui::PopStyleColor();

            for (size_t index = 0; index < sourceDiagnostics.size(); ++index)
            {
                const std::string &message = sourceDiagnostics[index];

                if (indoorSourceDiagnosticGroup(message) != group)
                {
                    continue;
                }

                ImGui::PushID(static_cast<int>(index));
                const bool canSelect = !extractQuotedIndoorSourceId(message).empty();

                if (!canSelect)
                {
                    ImGui::BeginDisabled();
                }

                if (ImGui::SmallButton("Select"))
                {
                    selectIndoorSourceDiagnosticTarget(session, sourceGeometry, message);
                }

                if (!canSelect)
                {
                    ImGui::EndDisabled();
                }

                ImGui::SameLine();
                ImGui::TextWrapped("%s", message.c_str());
                ImGui::PopID();
            }

            ImGui::Spacing();
        }

        endInspectorSectionBlock();
    }

    if (hasSourceMetadata)
    {
        EditorIndoorGeometryMetadata &mutableSourceGeometry = session.document().mutableIndoorGeometryMetadata();
        renderIndoorSourceMetadataEditor(session, mutableSourceGeometry);
    }

    if (!session.validationMessages().empty())
    {
        ImGui::Spacing();
        ImGui::Text("All Validation Issues: %zu", session.validationMessages().size());

        const size_t issueCountToShow = std::min<size_t>(session.validationMessages().size(), 6);

        for (size_t index = 0; index < issueCountToShow; ++index)
        {
            ImGui::BulletText("%s", session.validationMessages()[index].c_str());
        }
    }
}

void EditorMainWindow::renderEnvironmentInspector(EditorSession &session) const
{
    if (session.document().kind() == EditorDocument::Kind::Indoor)
    {
        renderIndoorEnvironmentInspector(session);
        return;
    }

    EditorDocument &document = session.document();
    Game::OutdoorSceneData &sceneData = document.mutableOutdoorSceneData();
    Game::OutdoorSceneEnvironment &environment = session.document().mutableOutdoorSceneData().environment;
    EditorOutdoorMapPackageMetadata &packageMetadata = document.mutableOutdoorMapPackageMetadata();
    bool changed = false;

    if (beginInspectorPropertyTable("EnvironmentFields"))
    {
        changed = editStringField(session, "Sky Texture", environment.skyTexture, 128) || changed;
        changed = editStringField(session, "Ground Tileset", environment.groundTilesetName, 128) || changed;
        changed = editUInt8Field(session, "Master Tile", environment.masterTile) || changed;
        changed = editLookupIndicesField(session, "Lookup Indices", environment.tileSetLookupIndices) || changed;
        changed = editIntField(
            session,
            "Day Bits Raw",
            environment.dayBitsRaw,
            0,
            std::numeric_limits<int32_t>::max()) || changed;
        changed = editUInt32Field(session, "Map Extra Bits Raw", environment.mapExtraBitsRaw) || changed;
        changed = editIntField(
            session,
            "Fog Weak Distance",
            environment.fogWeakDistance,
            0,
            std::numeric_limits<int>::max())
            || changed;
        changed = editIntField(
            session,
            "Fog Strong Distance",
            environment.fogStrongDistance,
            0,
            std::numeric_limits<int>::max())
            || changed;
        changed = editIntField(
            session,
            "Ceiling",
            environment.ceiling,
            std::numeric_limits<int>::min(),
            std::numeric_limits<int>::max())
            || changed;
        ImGui::EndTable();
    }

    ImGui::Separator();
    ImGui::TextUnformatted("Flags");

    if (beginInspectorPropertyTable("EnvironmentFlags"))
    {
        changed = editBitCheckbox(session, "Foggy", environment.dayBitsRaw, 0x1) || changed;
        changed = editBitCheckbox(session, "Raining", environment.mapExtraBitsRaw, 0x1) || changed;
        changed = editBitCheckbox(session, "Snowing", environment.mapExtraBitsRaw, 0x2) || changed;
        changed = editBitCheckbox(session, "Underwater", environment.mapExtraBitsRaw, 0x4) || changed;
        changed = editBitCheckbox(session, "No Terrain", environment.mapExtraBitsRaw, 0x8) || changed;
        changed = editBitCheckbox(session, "Always Dark", environment.mapExtraBitsRaw, 0x10) || changed;
        changed = editBitCheckbox(session, "Always Light", environment.mapExtraBitsRaw, 0x20) || changed;
        changed = editBitCheckbox(session, "Always Foggy", environment.mapExtraBitsRaw, 0x40) || changed;
        changed = editBitCheckbox(session, "Red Fog", environment.mapExtraBitsRaw, 0x80) || changed;
        ImGui::EndTable();
    }

    ImGui::Separator();
    ImGui::TextUnformatted("Party Start");

    size_t partyStartSceneIndex = sceneData.entities.size();

    for (size_t entityIndex = 0; entityIndex < sceneData.entities.size(); ++entityIndex)
    {
        if (toLowerCopy(sceneData.entities[entityIndex].entity.name) == "party start")
        {
            partyStartSceneIndex = entityIndex;
            break;
        }
    }

    if (partyStartSceneIndex >= sceneData.entities.size())
    {
        ImGui::TextUnformatted("No party start entity is present.");

        if (ImGui::Button("Create Party Start"))
        {
            session.captureUndoSnapshot();
            Game::OutdoorSceneEntity entity = {};
            entity.entityIndex = sceneData.entities.size();
            entity.entity.name = "party start";
            sceneData.entities.push_back(entity);
            changed = true;
            partyStartSceneIndex = sceneData.entities.size() - 1;
        }
    }

    if (partyStartSceneIndex < sceneData.entities.size())
    {
        Game::OutdoorSceneEntity &partyStart = sceneData.entities[partyStartSceneIndex];
        ImGui::Text("Entity Index: %zu", partyStart.entityIndex);

        if (beginInspectorPropertyTable("PartyStartFields"))
        {
            changed = editIntField(
                session,
                "Start X",
                partyStart.entity.x,
                std::numeric_limits<int>::min(),
                std::numeric_limits<int>::max()) || changed;
            changed = editIntField(
                session,
                "Start Y",
                partyStart.entity.y,
                std::numeric_limits<int>::min(),
                std::numeric_limits<int>::max()) || changed;
            changed = editIntField(
                session,
                "Start Z",
                partyStart.entity.z,
                std::numeric_limits<int>::min(),
                std::numeric_limits<int>::max()) || changed;
            changed = editIntField(session, "Facing", partyStart.entity.facing, -3600, 3600) || changed;
            ImGui::EndTable();
        }

        if (ImGui::Button("Select Party Start"))
        {
            session.select(EditorSelectionKind::Entity, partyStartSceneIndex);
        }
    }

    if (document.hasMapPackageRoot())
    {
        ImGui::Separator();
        ImGui::TextUnformatted("Runtime Defaults");

        if (beginInspectorPropertyTable("PackageRuntimeDefaults"))
        {
            changed = editIntField(
                session,
                "Map Stats Id",
                packageMetadata.mapStatsId,
                1,
                std::numeric_limits<int>::max()) || changed;
            changed = editIntField(
                session,
                "Redbook Track",
                packageMetadata.redbookTrack,
                0,
                std::numeric_limits<int>::max()) || changed;
            changed = editStringField(session, "Environment Name", packageMetadata.environmentName, 64) || changed;
            ImGui::EndTable();
        }

        bool isTopLevelArea = packageMetadata.isTopLevelArea;

        if (ImGui::Checkbox("Top Level Area", &isTopLevelArea))
        {
            session.captureUndoSnapshot();
            packageMetadata.isTopLevelArea = isTopLevelArea;
            changed = true;
        }

        ImGui::Separator();
        ImGui::TextUnformatted("Outdoor Bounds");

        if (beginInspectorPropertyTable("PackageOutdoorBounds"))
        {
            changed = editIntField(
                session,
                "Min X",
                packageMetadata.outdoorBounds.minX,
                std::numeric_limits<int>::min(),
                std::numeric_limits<int>::max()) || changed;
            changed = editIntField(
                session,
                "Max X",
                packageMetadata.outdoorBounds.maxX,
                std::numeric_limits<int>::min(),
                std::numeric_limits<int>::max()) || changed;
            changed = editIntField(
                session,
                "Min Y",
                packageMetadata.outdoorBounds.minY,
                std::numeric_limits<int>::min(),
                std::numeric_limits<int>::max()) || changed;
            changed = editIntField(
                session,
                "Max Y",
                packageMetadata.outdoorBounds.maxY,
                std::numeric_limits<int>::min(),
                std::numeric_limits<int>::max()) || changed;
            ImGui::EndTable();
        }

        packageMetadata.outdoorBounds.enabled = true;

        auto renderTransitionEditor =
            [&](const char *pLabel, std::optional<Game::MapEdgeTransition> &transition) -> bool
        {
            bool localChanged = false;
            const std::string headerId = std::string(pLabel) + " Transition";

            if (!ImGui::CollapsingHeader(headerId.c_str(), ImGuiTreeNodeFlags_DefaultOpen))
            {
                return false;
            }

            bool enabled = transition.has_value();

            if (ImGui::Checkbox((std::string("Enable ") + pLabel).c_str(), &enabled))
            {
                session.captureUndoSnapshot();

                if (enabled)
                {
                    Game::MapEdgeTransition newTransition = {};
                    newTransition.travelDays = 1;
                    newTransition.useMapStartPosition = true;
                    transition = newTransition;
                }
                else
                {
                    transition.reset();
                }

                localChanged = true;
            }

            if (!transition.has_value())
            {
                return localChanged;
            }

            const std::string destinationLabel = std::string(pLabel) + " Destination";
            const std::string travelDaysLabel = std::string(pLabel) + " Travel Days";
            const std::string headingLabel = std::string(pLabel) + " Heading";
            const std::string useStartLabel = std::string(pLabel) + " Use Map Start";
            const std::string arrivalXLabel = std::string(pLabel) + " Arrival X";
            const std::string arrivalYLabel = std::string(pLabel) + " Arrival Y";
            const std::string arrivalZLabel = std::string(pLabel) + " Arrival Z";
            Game::MapEdgeTransition &value = *transition;

            if (beginInspectorPropertyTable((std::string("TransitionFields_") + pLabel).c_str()))
            {
                localChanged = editStringField(session, destinationLabel.c_str(), value.destinationMapFileName, 64)
                    || localChanged;
                localChanged = editIntField(
                    session,
                    travelDaysLabel.c_str(),
                    value.travelDays,
                    0,
                    std::numeric_limits<int>::max()) || localChanged;

                int headingDegrees = value.directionDegrees.value_or(0);

                if (editIntField(session, headingLabel.c_str(), headingDegrees, -3600, 3600))
                {
                    value.directionDegrees = headingDegrees == 0 ? std::nullopt : std::optional<int>(headingDegrees);
                    localChanged = true;
                }

                ImGui::EndTable();
            }

            bool useMapStartPosition = value.useMapStartPosition;

            if (ImGui::Checkbox(useStartLabel.c_str(), &useMapStartPosition))
            {
                session.captureUndoSnapshot();
                value.useMapStartPosition = useMapStartPosition;

                if (useMapStartPosition)
                {
                    value.arrivalX.reset();
                    value.arrivalY.reset();
                    value.arrivalZ.reset();
                }
                else
                {
                    value.arrivalX = value.arrivalX.value_or(0);
                    value.arrivalY = value.arrivalY.value_or(0);
                    value.arrivalZ = value.arrivalZ.value_or(0);
                }

                localChanged = true;
            }

            if (!value.useMapStartPosition)
            {
                int arrivalX = value.arrivalX.value_or(0);
                int arrivalY = value.arrivalY.value_or(0);
                int arrivalZ = value.arrivalZ.value_or(0);

                if (beginInspectorPropertyTable((std::string("TransitionArrival_") + pLabel).c_str()))
                {
                    if (editIntField(
                            session,
                            arrivalXLabel.c_str(),
                            arrivalX,
                            std::numeric_limits<int>::min(),
                            std::numeric_limits<int>::max()))
                    {
                        value.arrivalX = arrivalX;
                        localChanged = true;
                    }

                    if (editIntField(
                            session,
                            arrivalYLabel.c_str(),
                            arrivalY,
                            std::numeric_limits<int>::min(),
                            std::numeric_limits<int>::max()))
                    {
                        value.arrivalY = arrivalY;
                        localChanged = true;
                    }

                    if (editIntField(
                            session,
                            arrivalZLabel.c_str(),
                            arrivalZ,
                            std::numeric_limits<int>::min(),
                            std::numeric_limits<int>::max()))
                    {
                        value.arrivalZ = arrivalZ;
                        localChanged = true;
                    }

                    ImGui::EndTable();
                }
            }

            return localChanged;
        };

        ImGui::Separator();
        ImGui::TextUnformatted("Map Transitions");
        changed = renderTransitionEditor("North", packageMetadata.northTransition) || changed;
        changed = renderTransitionEditor("South", packageMetadata.southTransition) || changed;
        changed = renderTransitionEditor("East", packageMetadata.eastTransition) || changed;
        changed = renderTransitionEditor("West", packageMetadata.westTransition) || changed;
    }

    if (changed)
    {
        session.noteDocumentMutated({});
    }
}

void EditorMainWindow::renderIndoorEnvironmentInspector(EditorSession &session) const
{
    Game::IndoorSceneEnvironment &environment = session.document().mutableIndoorSceneData().environment;
    bool changed = false;

    if (beginInspectorSectionBlock("Overview"))
    {
        if (beginInspectorPropertyTable("IndoorEnvironmentFields"))
        {
            changed = editStringField(session, "Sky Texture", environment.skyTexture, 128) || changed;
            changed = editIntField(
                session,
                "Day Bits Raw",
                environment.dayBitsRaw,
                0,
                std::numeric_limits<int32_t>::max()) || changed;
            changed = editUInt32Field(session, "Map Extra Bits Raw", environment.mapExtraBitsRaw) || changed;
            changed = editIntField(
                session,
                "Fog Weak Distance",
                environment.fogWeakDistance,
                0,
                std::numeric_limits<int>::max()) || changed;
            changed = editIntField(
                session,
                "Fog Strong Distance",
                environment.fogStrongDistance,
                0,
                std::numeric_limits<int>::max()) || changed;
            changed = editIntField(
                session,
                "Ceiling",
                environment.ceiling,
                std::numeric_limits<int>::min(),
                std::numeric_limits<int>::max()) || changed;
            ImGui::EndTable();
        }
        endInspectorSectionBlock();
    }

    if (beginInspectorSectionBlock("Flags"))
    {
        if (beginInspectorPropertyTable("IndoorEnvironmentFlags"))
        {
            changed = editBitCheckbox(session, "Foggy", environment.dayBitsRaw, 0x1) || changed;
            changed = editBitCheckbox(session, "Raining", environment.mapExtraBitsRaw, 0x1) || changed;
            changed = editBitCheckbox(session, "Snowing", environment.mapExtraBitsRaw, 0x2) || changed;
            changed = editBitCheckbox(session, "Underwater", environment.mapExtraBitsRaw, 0x4) || changed;
            changed = editBitCheckbox(session, "No Terrain", environment.mapExtraBitsRaw, 0x8) || changed;
            changed = editBitCheckbox(session, "Always Dark", environment.mapExtraBitsRaw, 0x10) || changed;
            changed = editBitCheckbox(session, "Always Light", environment.mapExtraBitsRaw, 0x20) || changed;
            changed = editBitCheckbox(session, "Always Foggy", environment.mapExtraBitsRaw, 0x40) || changed;
            changed = editBitCheckbox(session, "Red Fog", environment.mapExtraBitsRaw, 0x80) || changed;
            ImGui::EndTable();
        }
        endInspectorSectionBlock();
    }

    if (changed)
    {
        session.noteDocumentMutated({});
    }
}

void EditorMainWindow::renderTerrainInspector(EditorSession &session) const
{
    EditorDocument &document = session.document();
    Game::OutdoorSceneData &sceneData = document.mutableOutdoorSceneData();
    Game::OutdoorMapData &outdoorGeometry = document.mutableOutdoorGeometry();
    int cellX = 0;
    int cellY = 0;
    const bool hasSelectedCell = decodeTerrainCellFlatIndex(session.selection().index, cellX, cellY);
    const size_t cellIndex = hasSelectedCell ? terrainCellFlatIndex(cellX, cellY) : 0;
    const uint8_t currentTileId =
        hasSelectedCell && cellIndex < outdoorGeometry.tileMap.size() ? outdoorGeometry.tileMap[cellIndex] : 0;
    const uint8_t baseAttributes =
        hasSelectedCell && cellIndex < outdoorGeometry.attributeMap.size() ? outdoorGeometry.attributeMap[cellIndex] : 0;
    const uint8_t sampleHeight =
        hasSelectedCell && cellIndex < outdoorGeometry.heightMap.size() ? outdoorGeometry.heightMap[cellIndex] : 0;
    Game::OutdoorSceneTerrainAttributeOverride *pOverride =
        hasSelectedCell ? findTerrainOverride(sceneData, cellX, cellY) : nullptr;
    const uint8_t effectiveAttributes = pOverride != nullptr ? pOverride->legacyAttributes : baseAttributes;
    const std::optional<std::vector<std::string>> tileTextureNames =
        session.assetFileSystem() != nullptr
        ? Game::loadTerrainTileTextureNames(*session.assetFileSystem(), outdoorGeometry)
        : std::nullopt;
    bool changed = false;

    static constexpr const char *FalloffModeLabels[] = {"Flat", "Linear", "Smooth"};
    static constexpr const char *FlattenTargetModeLabels[] = {"Sampled", "Numeric"};
    const auto renderTerrainTileBitmapHoverPreview = [this, &session, &tileTextureNames](uint8_t tileId)
    {
        if (!ImGui::IsItemHovered(ImGuiHoveredFlags_Stationary | ImGuiHoveredFlags_DelayShort))
        {
            return;
        }

        if (!tileTextureNames || tileId >= tileTextureNames->size())
        {
            return;
        }

        const std::string &textureName = (*tileTextureNames)[tileId];

        if (textureName.empty() || textureName == "pending")
        {
            return;
        }

        const std::optional<bgfx::TextureHandle> textureHandle = ensureBitmapPreviewTexture(session, textureName);
        const std::optional<std::pair<int, int>> textureSize = bitmapPreviewTextureSize(textureName);

        if (!textureHandle || !textureSize || !bgfx::isValid(*textureHandle))
        {
            return;
        }

        ImGui::BeginTooltip();
        ImGui::Text("Tile %u (0x%02X)", static_cast<unsigned>(tileId), static_cast<unsigned>(tileId));
        ImGui::TextDisabled("%s", textureName.c_str());
        ImGui::Image(
            static_cast<ImTextureID>(static_cast<uintptr_t>(textureHandle->idx + 1)),
            ImVec2(static_cast<float>(textureSize->first), static_cast<float>(textureSize->second)));
        ImGui::EndTooltip();
    };

    if (beginInspectorSectionBlock("Height Sculpt"))
    {
        bool terrainSculptEnabled = session.terrainSculptEnabled();

        if (beginInspectorPropertyTable("TerrainSculptFields"))
        {
            beginInspectorFieldRow("Sculpt In Viewport");
            if (ImGui::Checkbox("##TerrainSculptEnabled", &terrainSculptEnabled))
            {
                session.setTerrainSculptEnabled(terrainSculptEnabled);

                if (terrainSculptEnabled)
                {
                    session.setTerrainPaintEnabled(false);
                }
            }

            const std::array<std::pair<const char *, EditorTerrainSculptMode>, 6> sculptModes = {{
                {"Raise", EditorTerrainSculptMode::Raise},
                {"Lower", EditorTerrainSculptMode::Lower},
                {"Flatten", EditorTerrainSculptMode::Flatten},
                {"Smooth", EditorTerrainSculptMode::Smooth},
                {"Noise", EditorTerrainSculptMode::Noise},
                {"Ramp", EditorTerrainSculptMode::Ramp}
            }};

            beginInspectorFieldRow("Tool");
            for (size_t index = 0; index < sculptModes.size(); ++index)
            {
                const auto &[pLabel, mode] = sculptModes[index];
                const bool selected = session.terrainSculptMode() == mode;

                if (renderIconTogglePill(
                        std::string("TerrainInspectorSculptMode" + std::to_string(index)).c_str(),
                        pLabel,
                        terrainSculptModeIcon(mode),
                        selected))
                {
                    session.setTerrainSculptMode(mode);
                }

                if ((index % 3) != 2 && index + 1 < sculptModes.size())
                {
                    ImGui::SameLine();
                }
            }

            if (session.terrainSculptMode() == EditorTerrainSculptMode::Flatten)
            {
                int flattenTargetMode = static_cast<int>(session.terrainFlattenTargetMode());
                beginInspectorFieldRow("Flatten Target");
                ImGui::SetNextItemWidth(160.0f);

                if (ImGui::Combo(
                        "##TerrainFlattenTargetMode",
                        &flattenTargetMode,
                        FlattenTargetModeLabels,
                        IM_ARRAYSIZE(FlattenTargetModeLabels)))
                {
                    session.setTerrainFlattenTargetMode(static_cast<EditorTerrainFlattenTargetMode>(flattenTargetMode));
                }

                if (session.terrainFlattenTargetMode() == EditorTerrainFlattenTargetMode::Numeric)
                {
                    int targetHeight = session.terrainFlattenTargetHeight();
                    beginInspectorFieldRow("Target Height");
                    ImGui::SetNextItemWidth(120.0f);

                    if (ImGui::InputInt("##TerrainFlattenTargetHeight", &targetHeight, 1, 8))
                    {
                        session.setTerrainFlattenTargetHeight(targetHeight);
                    }
                }
                else
                {
                    beginInspectorFieldRow("Sampled Target");
                    ImGui::Text(
                        "%d (%d world units)",
                        session.terrainFlattenTargetHeight(),
                        session.terrainFlattenTargetHeight() * Game::OutdoorMapData::TerrainHeightScale);

                    beginInspectorFieldRow("Pick Height");
                    const bool canPickSelected =
                        session.selection().kind == EditorSelectionKind::Terrain
                        && session.selection().index
                            < static_cast<size_t>(Game::OutdoorMapData::TerrainWidth * Game::OutdoorMapData::TerrainHeight);
                    ImGui::BeginDisabled(!canPickSelected);

                    if (ImGui::Button("Pick From Selected"))
                    {
                        tryPickFlattenTargetFromSelectedTerrainCell(session);
                    }

                    ImGui::EndDisabled();
                    ImGui::SameLine();
                    ImGui::TextDisabled("Alt+LMB in viewport");
                }
            }

            int terrainSculptRadius = session.terrainSculptRadius();
            beginInspectorFieldRow("Sculpt Radius");
            ImGui::SetNextItemWidth(120.0f);

            if (ImGui::InputInt("##TerrainSculptRadius", &terrainSculptRadius, 1, 4))
            {
                session.setTerrainSculptRadius(terrainSculptRadius);
            }

            int terrainSculptStrength = session.terrainSculptStrength();
            beginInspectorFieldRow("Sculpt Strength");
            ImGui::SetNextItemWidth(120.0f);

            if (ImGui::InputInt("##TerrainSculptStrength", &terrainSculptStrength, 1, 4))
            {
                session.setTerrainSculptStrength(terrainSculptStrength);
            }

            int terrainSculptFalloffMode = static_cast<int>(session.terrainSculptFalloffMode());
            beginInspectorFieldRow("Sculpt Falloff");
            ImGui::SetNextItemWidth(160.0f);

            if (ImGui::Combo(
                    "##TerrainSculptFalloff",
                    &terrainSculptFalloffMode,
                    FalloffModeLabels,
                    IM_ARRAYSIZE(FalloffModeLabels)))
            {
                session.setTerrainSculptFalloffMode(static_cast<EditorTerrainFalloffMode>(terrainSculptFalloffMode));
            }

            ImGui::EndTable();
        }
        endInspectorSectionBlock();
    }

    if (beginInspectorSectionBlock("Tile Paint"))
    {
        bool terrainPaintEnabled = session.terrainPaintEnabled();

        if (beginInspectorPropertyTable("TerrainPaintFields"))
        {
            beginInspectorFieldRow("Paint In Viewport");
            if (ImGui::Checkbox("##TerrainPaintEnabled", &terrainPaintEnabled))
            {
                session.setTerrainPaintEnabled(terrainPaintEnabled);

                if (terrainPaintEnabled)
                {
                    session.setTerrainSculptEnabled(false);
                }
            }

            beginInspectorFieldRow("Use Cell Tile");
            ImGui::BeginDisabled(!hasSelectedCell);
            if (ImGui::Button("Use Selected Cell"))
            {
                session.setTerrainPaintTileId(currentTileId);
            }
            ImGui::EndDisabled();

            const std::array<std::pair<const char *, EditorTerrainPaintMode>, 3> paintModes = {{
                {"Brush", EditorTerrainPaintMode::Brush},
                {"Rect", EditorTerrainPaintMode::Rectangle},
                {"Fill", EditorTerrainPaintMode::Fill}
            }};

            beginInspectorFieldRow("Tool");
            for (size_t index = 0; index < paintModes.size(); ++index)
            {
                const auto &[pLabel, mode] = paintModes[index];
                const bool selected = session.terrainPaintMode() == mode;

                if (renderIconTogglePill(
                        std::string("TerrainInspectorPaintMode" + std::to_string(index)).c_str(),
                        pLabel,
                        terrainPaintModeIcon(mode),
                        selected))
                {
                    session.setTerrainPaintMode(mode);
                }

                if (index + 1 < paintModes.size())
                {
                    ImGui::SameLine();
                }
            }

            int terrainPaintTileId = static_cast<int>(session.terrainPaintTileId());
            beginInspectorFieldRow("Paint Tile Id");
            ImGui::SetNextItemWidth(120.0f);

            if (ImGui::InputInt("##TerrainPaintTileId", &terrainPaintTileId, 1, 16))
            {
                terrainPaintTileId = std::clamp(terrainPaintTileId, 0, 255);
                session.setTerrainPaintTileId(static_cast<uint8_t>(terrainPaintTileId));
            }

            beginInspectorFieldRow("Tile Preview");
            renderTerrainTilePreviewButton(
                m_viewport,
                session.terrainPaintTileId(),
                true,
                ImVec2(36.0f, 36.0f));
            renderTerrainTileBitmapHoverPreview(session.terrainPaintTileId());

            if (session.terrainPaintMode() == EditorTerrainPaintMode::Brush)
            {
                int terrainPaintRadius = session.terrainPaintRadius();
                beginInspectorFieldRow("Paint Brush Radius");
                ImGui::SetNextItemWidth(120.0f);

                if (ImGui::InputInt("##TerrainPaintRadius", &terrainPaintRadius, 1, 4))
                {
                    session.setTerrainPaintRadius(terrainPaintRadius);
                }

                int terrainPaintEdgeNoise = session.terrainPaintEdgeNoise();
                beginInspectorFieldRow("Paint Edge Noise");
                ImGui::SetNextItemWidth(120.0f);

                if (ImGui::SliderInt("##TerrainPaintEdgeNoise", &terrainPaintEdgeNoise, 0, 100))
                {
                    session.setTerrainPaintEdgeNoise(terrainPaintEdgeNoise);
                }
            }

            ImGui::EndTable();
        }

        if (ImGui::BeginChild("TerrainTilePalette", ImVec2(0.0f, 220.0f), ImGuiChildFlags_Borders))
        {
            int visibleTileCountInRow = 0;

            for (int tileId = 0; tileId < 256; ++tileId)
            {
                float u0 = 0.0f;
                float v0 = 0.0f;
                float u1 = 0.0f;
                float v1 = 0.0f;

                if (!m_viewport.tryGetTerrainTilePreviewUv(static_cast<uint8_t>(tileId), u0, v0, u1, v1))
                {
                    continue;
                }

                const bool isSelected = session.terrainPaintTileId() == static_cast<uint8_t>(tileId);

                if (renderTerrainTilePreviewButton(
                        m_viewport,
                        static_cast<uint8_t>(tileId),
                        isSelected,
                        ImVec2(34.0f, 34.0f)))
                {
                    session.setTerrainPaintTileId(static_cast<uint8_t>(tileId));
                }

                renderTerrainTileBitmapHoverPreview(static_cast<uint8_t>(tileId));

                ++visibleTileCountInRow;

                if ((visibleTileCountInRow % 8) != 0)
                {
                    ImGui::SameLine();
                }
            }
        }
        ImGui::EndChild();
        endInspectorSectionBlock();
    }

    if (beginInspectorSectionBlock("Cell Summary"))
    {
        ImGui::Text("Terrain Attribute Overrides: %zu", sceneData.terrainAttributeOverrides.size());

        if (hasSelectedCell)
        {
            ImGui::Text("Cell: (%d, %d)", cellX, cellY);
            ImGui::Text(
                "Current Tile: %u (0x%02X)",
                static_cast<unsigned>(currentTileId),
                static_cast<unsigned>(currentTileId));
            ImGui::Text(
                "Sample Height: %u (%d world units)",
                static_cast<unsigned>(sampleHeight),
                static_cast<int>(sampleHeight) * Game::OutdoorMapData::TerrainHeightScale);
            ImGui::Text("Base Attributes: %u", baseAttributes);
            ImGui::Text("Has Override: %s", pOverride != nullptr ? "yes" : "no");
        }
        else
        {
            ImGui::TextUnformatted("Terrain mode active.");
            ImGui::TextDisabled("Click a terrain cell to inspect its tile, height, and override data.");
        }

        endInspectorSectionBlock();
    }

    if (hasSelectedCell && beginInspectorSectionBlock("Cell Override", false))
    {
        if (pOverride == nullptr)
        {
            if (ImGui::Button("Add Override"))
            {
                session.captureUndoSnapshot();
                sceneData.terrainAttributeOverrides.push_back({cellX, cellY, baseAttributes});
                pOverride = &sceneData.terrainAttributeOverrides.back();
                changed = true;
            }

            ImGui::SameLine();
            ImGui::TextUnformatted("Edits create a scene override for this cell.");
        }
        else if (ImGui::Button("Remove Override"))
        {
            session.captureUndoSnapshot();
            sceneData.terrainAttributeOverrides.erase(
                std::remove_if(
                    sceneData.terrainAttributeOverrides.begin(),
                    sceneData.terrainAttributeOverrides.end(),
                    [cellX, cellY](const Game::OutdoorSceneTerrainAttributeOverride &overrideEntry)
                    {
                        return overrideEntry.x == cellX && overrideEntry.y == cellY;
                    }),
                sceneData.terrainAttributeOverrides.end());
            changed = true;
            pOverride = nullptr;
        }

        if (pOverride != nullptr)
        {
            if (beginInspectorPropertyTable("TerrainOverrideFields"))
            {
                changed = editUInt8Field(session, "Legacy Attributes", pOverride->legacyAttributes) || changed;
                changed = editBitCheckbox(session, "Burn", pOverride->legacyAttributes, static_cast<uint8_t>(0x01))
                    || changed;
                changed = editBitCheckbox(session, "Water", pOverride->legacyAttributes, static_cast<uint8_t>(0x02))
                    || changed;
                ImGui::EndTable();
            }
        }
        else
        {
            ImGui::Text("Effective Attributes: %u", effectiveAttributes);
            ImGui::Text("Burn: %s", ((effectiveAttributes & 0x01) != 0) ? "true" : "false");
            ImGui::Text("Water: %s", ((effectiveAttributes & 0x02) != 0) ? "true" : "false");
        }
        endInspectorSectionBlock();
    }

    if (changed)
    {
        session.noteDocumentMutated({});
    }
}

void EditorMainWindow::renderBModelInspector(EditorSession &session, size_t bmodelIndex) const
{
    EditorDocument &document = session.document();
    Game::OutdoorMapData &outdoorGeometry = document.mutableOutdoorGeometry();
    Game::OutdoorSceneData &sceneData = document.mutableOutdoorSceneData();

    if (bmodelIndex >= outdoorGeometry.bmodels.size())
    {
        ImGui::TextUnformatted("Selected bmodel is out of range.");
        return;
    }

    Game::OutdoorBModel &bmodel = outdoorGeometry.bmodels[bmodelIndex];

    if (m_bmodelTransformEditorIndex != bmodelIndex)
    {
        m_bmodelTransformEditorIndex = bmodelIndex;
        m_bmodelMoveBy[0] = 0;
        m_bmodelMoveBy[1] = 0;
        m_bmodelMoveBy[2] = 0;
        m_bmodelRotateByDegrees[0] = 0.0f;
        m_bmodelRotateByDegrees[1] = 0.0f;
        m_bmodelRotateByDegrees[2] = 0.0f;
    }

    if (m_bmodelBulkEditorIndex != bmodelIndex)
    {
        m_bmodelBulkEditorIndex = bmodelIndex;
        m_bmodelBulkFaceScope = static_cast<int>(BModelBulkFaceScope::All);
        m_bmodelBulkFaceAttributes = 0;
        m_bmodelBulkCogNumber = 0;
        m_bmodelBulkCogTriggeredNumber = 0;
        m_bmodelBulkCogTrigger = 0;

        if (!bmodel.faces.empty())
        {
            m_bmodelBulkFaceAttributes = bmodel.faces.front().attributes & EditableFaceAttributeMask;
            m_bmodelBulkCogNumber = bmodel.faces.front().cogNumber;
            m_bmodelBulkCogTriggeredNumber = bmodel.faces.front().cogTriggeredNumber;
            m_bmodelBulkCogTrigger = bmodel.faces.front().cogTrigger;
        }
    }

    if (m_bmodelImportEditorIndex != bmodelIndex)
    {
        m_bmodelImportEditorIndex = bmodelIndex;
        const std::optional<EditorBModelImportSource> importSource = session.bmodelImportSource(bmodelIndex);
        std::string importPath;
        std::string importDefaultTexture;

        if (importSource)
        {
            importPath = importSource->sourcePath;
            importDefaultTexture = importSource->defaultTextureName;
            m_bmodelImportSelectedMeshName = importSource->sourceMeshName;
            m_bmodelImportScale = importSource->importScale;
            m_bmodelImportMergeCoplanarFaces = importSource->mergeCoplanarFaces;
        }
        else
        {
            m_bmodelImportSelectedMeshName.clear();
            m_bmodelImportScale = 1.0f;
            m_bmodelImportMergeCoplanarFaces = false;

            for (const Game::OutdoorBModelFace &face : bmodel.faces)
            {
                if (!face.textureName.empty())
                {
                    importDefaultTexture = face.textureName;
                    break;
                }
            }

            if (importDefaultTexture.empty())
            {
                const std::vector<std::string> mapTextureNames = session.usedBitmapTextureNamesInMap();
                importDefaultTexture = mapTextureNames.empty() ? "grastyl" : mapTextureNames.front();
            }
        }

        std::snprintf(m_bmodelImportPath, sizeof(m_bmodelImportPath), "%s", importPath.c_str());
        std::snprintf(m_bmodelImportDefaultTexture, sizeof(m_bmodelImportDefaultTexture), "%s", importDefaultTexture.c_str());
    }

    if (beginInspectorSectionBlock("Overview"))
    {
        ImGui::Text("BModel %zu", bmodelIndex);
        ImGui::Text("Name: %s", bmodel.name.empty() ? "<unnamed>" : bmodel.name.c_str());
        ImGui::Text("Faces: %zu", bmodel.faces.size());
        ImGui::Text("Vertices: %zu", bmodel.vertices.size());

        if (beginInspectorPropertyTable("BModelInspector"))
        {
            renderInspectorReadOnlyField("Position", std::to_string(bmodel.positionX) + ", "
                + std::to_string(bmodel.positionY) + ", "
                + std::to_string(bmodel.positionZ));
            renderInspectorReadOnlyField("Bounds Min", std::to_string(bmodel.minX) + ", "
                + std::to_string(bmodel.minY) + ", "
                + std::to_string(bmodel.minZ));
            renderInspectorReadOnlyField("Bounds Max", std::to_string(bmodel.maxX) + ", "
                + std::to_string(bmodel.maxY) + ", "
                + std::to_string(bmodel.maxZ));
            ImGui::EndTable();
        }
        endInspectorSectionBlock();
    }

    const bool hasMove = m_bmodelMoveBy[0] != 0 || m_bmodelMoveBy[1] != 0 || m_bmodelMoveBy[2] != 0;
    const bool hasRotation =
        std::fabs(m_bmodelRotateByDegrees[0]) > 0.0001f
        || std::fabs(m_bmodelRotateByDegrees[1]) > 0.0001f
        || std::fabs(m_bmodelRotateByDegrees[2]) > 0.0001f;
    float actualMinX = std::numeric_limits<float>::max();
    float actualMinY = std::numeric_limits<float>::max();
    float actualMinZ = std::numeric_limits<float>::max();
    float actualMaxX = std::numeric_limits<float>::lowest();
    float actualMaxY = std::numeric_limits<float>::lowest();
    float actualMaxZ = std::numeric_limits<float>::lowest();

    for (const Game::OutdoorBModelVertex &vertex : bmodel.vertices)
    {
        actualMinX = std::min(actualMinX, static_cast<float>(vertex.x));
        actualMinY = std::min(actualMinY, static_cast<float>(vertex.y));
        actualMinZ = std::min(actualMinZ, static_cast<float>(vertex.z));
        actualMaxX = std::max(actualMaxX, static_cast<float>(vertex.x));
        actualMaxY = std::max(actualMaxY, static_cast<float>(vertex.y));
        actualMaxZ = std::max(actualMaxZ, static_cast<float>(vertex.z));
    }

    if (bmodel.vertices.empty())
    {
        actualMinX = static_cast<float>(bmodel.minX);
        actualMinY = static_cast<float>(bmodel.minY);
        actualMinZ = static_cast<float>(bmodel.minZ);
        actualMaxX = static_cast<float>(bmodel.maxX);
        actualMaxY = static_cast<float>(bmodel.maxY);
        actualMaxZ = static_cast<float>(bmodel.maxZ);
    }

    const float bmodelCenterX = (actualMinX + actualMaxX) * 0.5f;
    const float bmodelCenterY = (actualMinY + actualMaxY) * 0.5f;
    const float terrainHeightAtCenter = Game::sampleOutdoorTerrainHeight(outdoorGeometry, bmodelCenterX, bmodelCenterY);
    const int snapBaseZ = static_cast<int>(std::lround(actualMinZ));
    const int snapToGroundDeltaZ = static_cast<int>(std::lround(terrainHeightAtCenter)) - snapBaseZ;

    if (beginInspectorSectionBlock("Transform"))
    {
        if (beginInspectorPropertyTable("BModelTransformFields"))
        {
            beginInspectorFieldRow("Move By");
            ImGui::InputInt3("##Move By", m_bmodelMoveBy);

            beginInspectorFieldRow("Rotate By XYZ");
            ImGui::InputFloat3("##Rotate By XYZ", m_bmodelRotateByDegrees, "%.2f");
            ImGui::EndTable();
        }

        if (ImGui::Button("Apply Transform", ImVec2(160.0f, 0.0f)))
        {
            if (hasMove || hasRotation)
            {
                session.captureUndoSnapshot();
                const bool trackSourceTransform =
                    session.bmodelImportSource(bmodelIndex).has_value()
                    || session.document().outdoorBModelSourceTransform(bmodelIndex).has_value();
                EditorBModelSourceTransform sourceTransform =
                    session.document().outdoorBModelSourceTransform(bmodelIndex).value_or(sourceTransformFromBModel(bmodel));

                float minX = std::numeric_limits<float>::max();
                float minY = std::numeric_limits<float>::max();
                float minZ = std::numeric_limits<float>::max();
                float maxX = std::numeric_limits<float>::lowest();
                float maxY = std::numeric_limits<float>::lowest();
                float maxZ = std::numeric_limits<float>::lowest();

                for (const Game::OutdoorBModelVertex &vertex : bmodel.vertices)
                {
                    minX = std::min(minX, static_cast<float>(vertex.x));
                    minY = std::min(minY, static_cast<float>(vertex.y));
                    minZ = std::min(minZ, static_cast<float>(vertex.z));
                    maxX = std::max(maxX, static_cast<float>(vertex.x));
                    maxY = std::max(maxY, static_cast<float>(vertex.y));
                    maxZ = std::max(maxZ, static_cast<float>(vertex.z));
                }

                const float pivotX = (minX + maxX) * 0.5f;
                const float pivotY = (minY + maxY) * 0.5f;
                const float pivotZ = (minZ + maxZ) * 0.5f;
                const float rotationXRadians = m_bmodelRotateByDegrees[0] * 3.14159265358979323846f / 180.0f;
                const float rotationYRadians = m_bmodelRotateByDegrees[1] * 3.14159265358979323846f / 180.0f;
                const float rotationZRadians = m_bmodelRotateByDegrees[2] * 3.14159265358979323846f / 180.0f;
                const float cosX = std::cos(rotationXRadians);
                const float sinX = std::sin(rotationXRadians);
                const float cosY = std::cos(rotationYRadians);
                const float sinY = std::sin(rotationYRadians);
                const float cosZ = std::cos(rotationZRadians);
                const float sinZ = std::sin(rotationZRadians);

                for (Game::OutdoorBModelVertex &vertex : bmodel.vertices)
                {
                    const float localX = static_cast<float>(vertex.x) - pivotX;
                    const float localY = static_cast<float>(vertex.y) - pivotY;
                    const float localZ = static_cast<float>(vertex.z) - pivotZ;

                    const float rotatedXY = localY * cosX - localZ * sinX;
                    const float rotatedXZ = localY * sinX + localZ * cosX;
                    const float rotatedYX = localX * cosY + rotatedXZ * sinY;
                    const float rotatedYZ = -localX * sinY + rotatedXZ * cosY;
                    const float rotatedZX = rotatedYX * cosZ - rotatedXY * sinZ;
                    const float rotatedZY = rotatedYX * sinZ + rotatedXY * cosZ;

                    const float worldX = pivotX + rotatedZX + static_cast<float>(m_bmodelMoveBy[0]);
                    const float worldY = pivotY + rotatedZY + static_cast<float>(m_bmodelMoveBy[1]);
                    const float worldZ = pivotZ + rotatedYZ + static_cast<float>(m_bmodelMoveBy[2]);
                    vertex.x = static_cast<int>(std::lround(worldX));
                    vertex.y = static_cast<int>(std::lround(worldY));
                    vertex.z = static_cast<int>(std::lround(worldZ));
                }

                recomputeBModelMetadata(bmodel);

                if (trackSourceTransform)
                {
                    sourceTransform.basisX = rotateVectorByEulerDegrees(
                        sourceTransform.basisX,
                        m_bmodelRotateByDegrees[0],
                        m_bmodelRotateByDegrees[1],
                        m_bmodelRotateByDegrees[2]);
                    sourceTransform.basisY = rotateVectorByEulerDegrees(
                        sourceTransform.basisY,
                        m_bmodelRotateByDegrees[0],
                        m_bmodelRotateByDegrees[1],
                        m_bmodelRotateByDegrees[2]);
                    sourceTransform.basisZ = rotateVectorByEulerDegrees(
                        sourceTransform.basisZ,
                        m_bmodelRotateByDegrees[0],
                        m_bmodelRotateByDegrees[1],
                        m_bmodelRotateByDegrees[2]);
                    sourceTransform.originX += static_cast<float>(m_bmodelMoveBy[0]);
                    sourceTransform.originY += static_cast<float>(m_bmodelMoveBy[1]);
                    sourceTransform.originZ += static_cast<float>(m_bmodelMoveBy[2]);
                    session.document().setOutdoorBModelSourceTransform(bmodelIndex, sourceTransform);
                }

                m_bmodelMoveBy[0] = 0;
                m_bmodelMoveBy[1] = 0;
                m_bmodelMoveBy[2] = 0;
                m_bmodelRotateByDegrees[0] = 0.0f;
                m_bmodelRotateByDegrees[1] = 0.0f;
                m_bmodelRotateByDegrees[2] = 0.0f;
                session.noteDocumentMutated({});
            }
        }

        ImGui::SameLine();

        if (ImGui::Button("Snap To Ground", ImVec2(150.0f, 0.0f)))
        {
            if (snapToGroundDeltaZ != 0)
            {
                session.captureUndoSnapshot();
                const bool trackSourceTransform =
                    session.bmodelImportSource(bmodelIndex).has_value()
                    || session.document().outdoorBModelSourceTransform(bmodelIndex).has_value();
                EditorBModelSourceTransform sourceTransform =
                    session.document().outdoorBModelSourceTransform(bmodelIndex).value_or(sourceTransformFromBModel(bmodel));

                for (Game::OutdoorBModelVertex &vertex : bmodel.vertices)
                {
                    vertex.z += snapToGroundDeltaZ;
                }

                bmodel.positionZ += snapToGroundDeltaZ;
                bmodel.minZ += snapToGroundDeltaZ;
                bmodel.maxZ += snapToGroundDeltaZ;
                bmodel.boundingCenterZ += snapToGroundDeltaZ;

                if (trackSourceTransform)
                {
                    sourceTransform.originZ += static_cast<float>(snapToGroundDeltaZ);
                    session.document().setOutdoorBModelSourceTransform(bmodelIndex, sourceTransform);
                }

                session.noteDocumentMutated({});
            }
        }

        ImGui::SameLine();

        if (ImGui::Button("Reset Fields", ImVec2(120.0f, 0.0f)))
        {
            m_bmodelMoveBy[0] = 0;
            m_bmodelMoveBy[1] = 0;
            m_bmodelMoveBy[2] = 0;
            m_bmodelRotateByDegrees[0] = 0.0f;
            m_bmodelRotateByDegrees[1] = 0.0f;
            m_bmodelRotateByDegrees[2] = 0.0f;
        }

        ImGui::Text(
            "Terrain Center: %.0f  |  Base Z: %d  |  Snap Delta Z: %d",
            terrainHeightAtCenter,
            snapBaseZ,
            snapToGroundDeltaZ);

        if (!hasMove && !hasRotation)
        {
            ImGui::TextDisabled("Enter a move delta and/or XYZ rotation delta, then click Apply Transform.");
        }

        endInspectorSectionBlock();
    }

    if (beginInspectorSectionBlock("Face Defaults"))
    {
        if (beginInspectorPropertyTable("BModelFaceDefaults"))
        {
            beginInspectorFieldRow("Scope");
            const char *scopePreview =
                bmodelBulkFaceScopeLabel(static_cast<BModelBulkFaceScope>(m_bmodelBulkFaceScope));

            if (ImGui::BeginCombo("##BModelFaceScope", scopePreview))
            {
                for (int scopeIndex = 0; scopeIndex < 3; ++scopeIndex)
                {
                    const BModelBulkFaceScope scope = static_cast<BModelBulkFaceScope>(scopeIndex);
                    const bool selected = scopeIndex == m_bmodelBulkFaceScope;

                    if (ImGui::Selectable(bmodelBulkFaceScopeLabel(scope), selected))
                    {
                        m_bmodelBulkFaceScope = scopeIndex;
                    }

                    if (selected)
                    {
                        ImGui::SetItemDefaultFocus();
                    }
                }

                ImGui::EndCombo();
            }

            beginInspectorFieldRow("Legacy Event Number");
            int bulkCogNumber = m_bmodelBulkCogNumber;
            if (ImGui::InputInt("##BModelBulkCogNumber", &bulkCogNumber))
            {
                m_bmodelBulkCogNumber = static_cast<uint16_t>(std::clamp(bulkCogNumber, 0, 65535));
            }

            uint16_t bulkCogTriggeredNumber = m_bmodelBulkCogTriggeredNumber;
            if (editMapEventField(session, "Event Id", bulkCogTriggeredNumber))
            {
                m_bmodelBulkCogTriggeredNumber = bulkCogTriggeredNumber;
            }

            renderResolvedMapEventField(session, "Resolved Event", m_bmodelBulkCogTriggeredNumber);

            beginInspectorFieldRow("Legacy Event Trigger");
            int bulkCogTrigger = m_bmodelBulkCogTrigger;
            if (ImGui::InputInt("##BModelBulkCogTrigger", &bulkCogTrigger))
            {
                m_bmodelBulkCogTrigger = static_cast<uint16_t>(std::clamp(bulkCogTrigger, 0, 65535));
            }

            const auto editBulkAttributeCheckbox = [this](const char *pLabel, uint32_t mask)
            {
                bool enabled = (m_bmodelBulkFaceAttributes & mask) != 0;
                beginInspectorFieldRow(pLabel);

                if (!ImGui::Checkbox(inspectorFieldId(pLabel).c_str(), &enabled))
                {
                    return;
                }

                if (enabled)
                {
                    m_bmodelBulkFaceAttributes |= mask;
                }
                else
                {
                    m_bmodelBulkFaceAttributes &= ~mask;
                }
            };

            editBulkAttributeCheckbox("Fluid", FaceAttributeFluid);
            editBulkAttributeCheckbox("Invisible", FaceAttributeInvisible);
            editBulkAttributeCheckbox("Has Hint", FaceAttributeHasHint);
            editBulkAttributeCheckbox("Clickable", FaceAttributeClickable);
            editBulkAttributeCheckbox("Pressure Plate", FaceAttributePressurePlate);
            editBulkAttributeCheckbox("Untouchable", FaceAttributeUntouchable);
            ImGui::EndTable();
        }

        const auto bulkFaceScope = static_cast<BModelBulkFaceScope>(m_bmodelBulkFaceScope);
        size_t scopedFaceCount = 0;

        for (const Game::OutdoorBModelFace &face : bmodel.faces)
        {
            if (bmodelFaceMatchesScope(face, bulkFaceScope))
            {
                ++scopedFaceCount;
            }
        }

        if (ImGui::Button("Apply To Faces", ImVec2(140.0f, 0.0f)))
        {
            if (scopedFaceCount > 0)
            {
                session.captureUndoSnapshot();

                for (size_t currentFaceIndex = 0; currentFaceIndex < bmodel.faces.size(); ++currentFaceIndex)
                {
                    Game::OutdoorBModelFace &face = bmodel.faces[currentFaceIndex];

                    if (!bmodelFaceMatchesScope(face, bulkFaceScope))
                    {
                        continue;
                    }

                    Game::OutdoorSceneInteractiveFace *pInteractiveFace =
                        findInteractiveFace(sceneData, bmodelIndex, currentFaceIndex);

                    if (pInteractiveFace == nullptr)
                    {
                        sceneData.interactiveFaces.push_back(makeInteractiveFaceEntry(
                            bmodelIndex,
                            currentFaceIndex,
                            face));
                        pInteractiveFace = &sceneData.interactiveFaces.back();
                    }

                    pInteractiveFace->legacyAttributes = (pInteractiveFace->legacyAttributes & ~EditableFaceAttributeMask)
                        | (m_bmodelBulkFaceAttributes & EditableFaceAttributeMask);
                    pInteractiveFace->cogNumber = m_bmodelBulkCogNumber;
                    pInteractiveFace->cogTriggeredNumber = m_bmodelBulkCogTriggeredNumber;
                    pInteractiveFace->cogTrigger = m_bmodelBulkCogTrigger;
                }

                session.noteDocumentMutated({});
            }
        }

        ImGui::SameLine();

        if (ImGui::Button("Reset Faces", ImVec2(140.0f, 0.0f)))
        {
            if (scopedFaceCount > 0)
            {
                session.captureUndoSnapshot();
                sceneData.interactiveFaces.erase(
                    std::remove_if(
                        sceneData.interactiveFaces.begin(),
                        sceneData.interactiveFaces.end(),
                        [&bmodel, bmodelIndex, bulkFaceScope](const Game::OutdoorSceneInteractiveFace &interactiveFace)
                        {
                            return interactiveFace.bmodelIndex == bmodelIndex
                                && interactiveFace.faceIndex < bmodel.faces.size()
                                && bmodelFaceMatchesScope(bmodel.faces[interactiveFace.faceIndex], bulkFaceScope);
                        }),
                    sceneData.interactiveFaces.end());

                session.noteDocumentMutated({});
            }
        }
        ImGui::TextDisabled("%zu faces in current scope.", scopedFaceCount);
        endInspectorSectionBlock();
    }

    const bool hasRememberedImportSource = session.bmodelImportSource(bmodelIndex).has_value();
    const bool hasModelImportPath = m_bmodelImportPath[0] != '\0';
    const bool canSplitByMesh = canSplitImportedModelPathByMesh(m_bmodelImportPath);
    const ModelImportInspectionState &inspection =
        ensureModelImportInspection(m_bmodelImportPath, m_bmodelImportInspection);

    if (!trimCopy(m_bmodelImportSelectedMeshName).empty())
    {
        bool foundSelectedMesh = false;

        for (const ModelImportInspectionState::Entry &entry : inspection.entries)
        {
            if (toLowerCopy(trimCopy(entry.name)) == toLowerCopy(trimCopy(m_bmodelImportSelectedMeshName)))
            {
                foundSelectedMesh = true;
                break;
            }
        }

        if (!foundSelectedMesh)
        {
            m_bmodelImportSelectedMeshName.clear();
        }
    }

    if (beginInspectorSectionBlock("Model Import", false))
    {
        if (beginInspectorPropertyTable("BModelModelImport"))
        {
            beginInspectorFieldRow("Model Path");
            ImGui::InputText("##BModelImportPath", m_bmodelImportPath, sizeof(m_bmodelImportPath));

            beginInspectorFieldRow("Import Scale");
            ImGui::InputFloat("##BModelImportScale", &m_bmodelImportScale, 0.1f, 1.0f, "%.3f");

            std::string defaultTextureName = m_bmodelImportDefaultTexture;
            const bool texturePickerChanged =
                renderBitmapTextureSelector(session, "Default Texture (Optional)", defaultTextureName);

            beginInspectorFieldRow("Default Texture Raw");
            char defaultTextureBuffer[64] = {};
            std::snprintf(defaultTextureBuffer, sizeof(defaultTextureBuffer), "%s", defaultTextureName.c_str());
            const bool rawTextureChanged =
                ImGui::InputText("##BModelImportDefaultTextureRaw", defaultTextureBuffer, sizeof(defaultTextureBuffer));

            if (rawTextureChanged)
            {
                defaultTextureName = defaultTextureBuffer;
            }

            if (texturePickerChanged || rawTextureChanged)
            {
                std::snprintf(
                    m_bmodelImportDefaultTexture,
                    sizeof(m_bmodelImportDefaultTexture),
                    "%s",
                    defaultTextureName.c_str());
            }

            beginInspectorFieldRow("Merge Coplanar");
            ImGui::Checkbox("##BModelImportMergeCoplanarFaces", &m_bmodelImportMergeCoplanarFaces);

            if (canSplitByMesh)
            {
                beginInspectorFieldRow("Source Mesh");
                ImGui::BeginDisabled(inspection.entries.empty());
                renderImportedModelSelector(
                    "##BModelImportSourceMesh",
                    inspection,
                    m_bmodelImportSelectedMeshName);
                ImGui::EndDisabled();
            }

            ImGui::EndTable();
        }

        if (canSplitByMesh)
        {
            if (!inspection.errorMessage.empty())
            {
                ImGui::TextColored(colorFromRgb(0xE7A46C), "%s", inspection.errorMessage.c_str());
            }
            else
            {
                ImGui::TextDisabled("%s", importedModelSummaryText(inspection.entries.size()).c_str());

                if (!inspection.entries.empty())
                {
                    renderImportedModelInspectionTable(
                        "BModelImportMeshes",
                        inspection,
                        m_bmodelImportSelectedMeshName,
                        108.0f);
                    renderImportedModelInspectionSummary(inspection, m_bmodelImportSelectedMeshName);
                }
            }
        }

        if (ImGui::Button("Browse...", ImVec2(120.0f, 0.0f)))
        {
            openModelFileBrowser(ModelImportTarget::ReplaceSelectedBModel, m_bmodelImportPath);
        }

        ImGui::SameLine();

        if (ImGui::Button("Replace From Model", ImVec2(150.0f, 0.0f)))
        {
            std::string errorMessage;
            const std::string sourceMeshName =
                canSplitByMesh ? m_bmodelImportSelectedMeshName : std::string();

            if (!session.replaceSelectedBModelFromModel(
                    m_bmodelImportPath,
                    m_bmodelImportScale,
                    m_bmodelImportDefaultTexture,
                    sourceMeshName,
                    m_bmodelImportMergeCoplanarFaces,
                    errorMessage))
            {
                session.logError(errorMessage);
            }
            else
            {
                rememberModelImportDirectory(m_bmodelImportPath);
            }
        }

        ImGui::SameLine();

        if (!hasRememberedImportSource)
        {
            ImGui::BeginDisabled();
        }

        if (ImGui::Button("Reimport", ImVec2(110.0f, 0.0f)))
        {
            std::string errorMessage;
            const std::optional<EditorBModelImportSource> importSource = session.bmodelImportSource(bmodelIndex);

            if (!session.reimportSelectedBModel(errorMessage))
            {
                session.logError(errorMessage);
            }
            else if (importSource)
            {
                rememberModelImportDirectory(importSource->sourcePath.c_str());
            }
        }

        if (!hasRememberedImportSource)
        {
            ImGui::EndDisabled();
        }

        if (const std::optional<EditorBModelImportSource> importSource = session.bmodelImportSource(bmodelIndex))
        {
            ImGui::TextWrapped("Remembered Source: %s", importSource->sourcePath.c_str());

            EditorBModelImportSource updatedImportSource = *importSource;
            bool importSourceChanged = false;

            if (beginInspectorPropertyTable("BModelRememberedImportSettings"))
            {
                if (!trimCopy(updatedImportSource.sourceMeshName).empty())
                {
                    beginInspectorFieldRow("Remembered Mesh");
                    ImGui::TextUnformatted(updatedImportSource.sourceMeshName.c_str());
                }

                std::string rememberedDefaultTextureName = updatedImportSource.defaultTextureName;
                const bool rememberedTexturePickerChanged =
                    renderBitmapTextureSelector(
                        session,
                        "Remembered Default Texture (Optional)",
                        rememberedDefaultTextureName);

                beginInspectorFieldRow("Remembered Default Raw");
                char rememberedTextureBuffer[64] = {};
                std::snprintf(
                    rememberedTextureBuffer,
                    sizeof(rememberedTextureBuffer),
                    "%s",
                    rememberedDefaultTextureName.c_str());
                const bool rememberedTextureRawChanged = ImGui::InputText(
                    "##BModelRememberedDefaultTextureRaw",
                    rememberedTextureBuffer,
                    sizeof(rememberedTextureBuffer));

                if (rememberedTextureRawChanged)
                {
                    rememberedDefaultTextureName = rememberedTextureBuffer;
                }

                if (rememberedTexturePickerChanged || rememberedTextureRawChanged)
                {
                    updatedImportSource.defaultTextureName = rememberedDefaultTextureName;
                    importSourceChanged = true;
                }

                ImGui::EndTable();
            }

            const std::vector<EditorImportedMaterialDiagnostic> materialDiagnostics =
                session.importedMaterialDiagnostics(bmodelIndex);
            std::unordered_map<std::string, EditorImportedMaterialDiagnostic> diagnosticByMaterial;

            for (const EditorImportedMaterialDiagnostic &diagnostic : materialDiagnostics)
            {
                diagnosticByMaterial.emplace(
                    toLowerCopy(trimCopy(diagnostic.sourceMaterialName)),
                    diagnostic);
            }

            ImGui::TextDisabled("Material Remaps");

            if (ImGui::BeginTable("BModelMaterialRemaps", 3, ImGuiTableFlags_SizingStretchProp))
            {
                ImGui::TableSetupColumn("Material", ImGuiTableColumnFlags_WidthStretch, 0.45f);
                ImGui::TableSetupColumn("Texture", ImGuiTableColumnFlags_WidthStretch, 0.45f);
                ImGui::TableSetupColumn("Action", ImGuiTableColumnFlags_WidthFixed, 64.0f);
                ImGui::TableHeadersRow();

                for (size_t remapIndex = 0; remapIndex < updatedImportSource.materialRemaps.size(); ++remapIndex)
                {
                    EditorMaterialTextureRemap &remap = updatedImportSource.materialRemaps[remapIndex];
                    const std::string remapKey = toLowerCopy(trimCopy(remap.sourceMaterialName));
                    const auto diagnosticIt = diagnosticByMaterial.find(remapKey);
                    const bool hasDiagnostic = diagnosticIt != diagnosticByMaterial.end();
                    const bool unresolvedRow = hasDiagnostic && !diagnosticIt->second.resolvesToKnownBitmap;
                    const bool defaultFallbackRow = hasDiagnostic && diagnosticIt->second.usesDefaultFallback;
                    ImGui::PushID(static_cast<int>(remapIndex));
                    ImGui::TableNextRow();

                    if (unresolvedRow)
                    {
                        ImGui::TableSetBgColor(ImGuiTableBgTarget_RowBg0, ImGui::GetColorU32(colorFromRgb(0x3E2A24)));
                    }
                    else if (defaultFallbackRow)
                    {
                        ImGui::TableSetBgColor(ImGuiTableBgTarget_RowBg0, ImGui::GetColorU32(colorFromRgb(0x353123)));
                    }

                    ImGui::TableSetColumnIndex(0);
                    char materialBuffer[128] = {};
                    std::snprintf(materialBuffer, sizeof(materialBuffer), "%s", remap.sourceMaterialName.c_str());

                    if (ImGui::InputText("##Material", materialBuffer, sizeof(materialBuffer)))
                    {
                        remap.sourceMaterialName = materialBuffer;
                        importSourceChanged = true;
                    }

                    if (hasDiagnostic && ImGui::IsItemHovered())
                    {
                        ImGui::SetTooltip(
                            "%s",
                            unresolvedRow ? "Material does not resolve to a known bitmap."
                            : (defaultFallbackRow
                                ? "Material currently falls back to the remembered default texture."
                                : "Material resolves cleanly."));
                    }

                    ImGui::TableSetColumnIndex(1);
                    if (renderInlineBitmapTextureSelector(session, "##Texture", remap.textureName, bmodelIndex))
                    {
                        importSourceChanged = true;
                    }

                    ImGui::TableSetColumnIndex(2);

                    if (ImGui::Button("Remove"))
                    {
                        updatedImportSource.materialRemaps.erase(
                            updatedImportSource.materialRemaps.begin() + static_cast<ptrdiff_t>(remapIndex));
                        importSourceChanged = true;
                        ImGui::PopID();
                        break;
                    }

                    ImGui::PopID();
                }

                ImGui::EndTable();
            }

            if (ImGui::Button("Add Remap", ImVec2(120.0f, 0.0f)))
            {
                updatedImportSource.materialRemaps.push_back({});
                importSourceChanged = true;
            }

            ImGui::SameLine();

            if (ImGui::Button("Apply Default To Unresolved", ImVec2(190.0f, 0.0f)))
            {
                for (EditorMaterialTextureRemap &remap : updatedImportSource.materialRemaps)
                {
                    const std::string remapKey = toLowerCopy(trimCopy(remap.sourceMaterialName));
                    const auto diagnosticIt = diagnosticByMaterial.find(remapKey);
                    const bool unresolvedRow =
                        diagnosticIt != diagnosticByMaterial.end()
                        && (!diagnosticIt->second.resolvesToKnownBitmap || diagnosticIt->second.usesDefaultFallback);

                    if (unresolvedRow || trimCopy(remap.textureName).empty())
                    {
                        remap.textureName = updatedImportSource.defaultTextureName;
                        importSourceChanged = true;
                    }
                }
            }

            ImGui::SameLine();

            if (ImGui::Button("Clear Remaps", ImVec2(120.0f, 0.0f)))
            {
                if (!updatedImportSource.materialRemaps.empty())
                {
                    updatedImportSource.materialRemaps.clear();
                    importSourceChanged = true;
                }
            }

            if (!materialDiagnostics.empty())
            {
                ImGui::Spacing();
                ImGui::TextDisabled("Source Material Status");

                if (ImGui::BeginTable("BModelMaterialDiagnostics", 3, ImGuiTableFlags_SizingStretchProp))
                {
                    ImGui::TableSetupColumn("Material", ImGuiTableColumnFlags_WidthStretch, 0.4f);
                    ImGui::TableSetupColumn("Resolved", ImGuiTableColumnFlags_WidthStretch, 0.35f);
                    ImGui::TableSetupColumn("Status", ImGuiTableColumnFlags_WidthStretch, 0.25f);
                    ImGui::TableHeadersRow();

                    for (const EditorImportedMaterialDiagnostic &diagnostic : materialDiagnostics)
                    {
                        const ImVec4 statusColor = !diagnostic.resolvesToKnownBitmap
                            ? colorFromRgb(0xE7A46C)
                            : (diagnostic.usesDefaultFallback
                                ? colorFromRgb(0xD8C38A)
                                : colorFromRgb(0xC7D2DC));
                        const char *pStatusText = !diagnostic.resolvesToKnownBitmap
                            ? "Missing"
                            : (diagnostic.usesDefaultFallback
                                ? "Default"
                                : (diagnostic.hasExplicitRemap ? "Remapped" : "Direct"));

                        ImGui::TableNextRow();
                        ImGui::TableSetColumnIndex(0);
                        ImGui::TextUnformatted(diagnostic.sourceMaterialName.c_str());
                        ImGui::TableSetColumnIndex(1);
                        ImGui::TextUnformatted(
                            diagnostic.resolvedTextureName.empty() ? "<none>" : diagnostic.resolvedTextureName.c_str());
                        ImGui::TableSetColumnIndex(2);
                        ImGui::TextColored(statusColor, "%s", pStatusText);
                    }

                    ImGui::EndTable();
                }

                if (ImGui::Button("Add Unresolved To Remaps", ImVec2(190.0f, 0.0f)))
                {
                    std::unordered_set<std::string> existingRemaps;

                    for (const EditorMaterialTextureRemap &remap : updatedImportSource.materialRemaps)
                    {
                        existingRemaps.insert(toLowerCopy(trimCopy(remap.sourceMaterialName)));
                    }

                    for (const EditorImportedMaterialDiagnostic &diagnostic : materialDiagnostics)
                    {
                        const std::string remapKey = toLowerCopy(trimCopy(diagnostic.sourceMaterialName));

                        if (existingRemaps.contains(remapKey))
                        {
                            continue;
                        }

                        if (diagnostic.resolvesToKnownBitmap && !diagnostic.usesDefaultFallback)
                        {
                            continue;
                        }

                        updatedImportSource.materialRemaps.push_back(
                            {diagnostic.sourceMaterialName, updatedImportSource.defaultTextureName});
                        existingRemaps.insert(remapKey);
                        importSourceChanged = true;
                    }
                }
            }

            if (ImGui::Button("Capture Current Face Textures", ImVec2(220.0f, 0.0f)))
            {
                std::string errorMessage;

                if (!session.captureSelectedBModelMaterialRemaps(errorMessage))
                {
                    session.logError(errorMessage);
                }
            }

            if (importSourceChanged)
            {
                session.captureUndoSnapshot();
                session.document().setOutdoorBModelImportSource(bmodelIndex, updatedImportSource);
                session.noteDocumentMutated({});
            }
        }
        else if (!hasModelImportPath)
        {
            ImGui::TextDisabled("Enter a model path or use Browse... .");
        }

        ImGui::TextDisabled("Use Create -> Import BModel... to append a new bmodel.");
        endInspectorSectionBlock();
    }
}

void EditorMainWindow::renderInteractiveFaceInspector(EditorSession &session)
{
    if (session.document().kind() == EditorDocument::Kind::Indoor)
    {
        EditorDocument &document = session.document();
        Game::IndoorSceneData &sceneData = document.mutableIndoorSceneData();
        const Game::IndoorMapData &indoorGeometry = session.document().indoorGeometry();

        if (session.selection().index >= indoorGeometry.faces.size())
        {
            ImGui::TextUnformatted("Selected face is out of range.");
            return;
        }

        const size_t faceIndex = session.selection().index;
        const Game::IndoorFace &face = indoorGeometry.faces[faceIndex];
        Game::IndoorFace effectiveFace = effectiveIndoorFace(sceneData, indoorGeometry, faceIndex);
        std::vector<size_t> selectedFaceIndices = session.selectedInteractiveFaceIndices();

        if (selectedFaceIndices.empty())
        {
            selectedFaceIndices.push_back(faceIndex);
        }

        const bool multiSelection = selectedFaceIndices.size() > 1;
        const Game::IndoorSceneFaceAttributeOverride *pAttributeOverride =
            findIndoorFaceAttributeOverride(sceneData, faceIndex);
        uint32_t effectiveAttributes = effectiveIndoorFaceAttributes(sceneData, face, faceIndex);
        const bool effectivePortal =
            face.isPortal || Game::hasFaceAttribute(effectiveAttributes, Game::FaceAttribute::IsPortal);
        Game::IndoorFaceGeometryData geometry = {};
        const bool hasGeometry = Game::buildIndoorFaceGeometry(indoorGeometry, indoorGeometry.vertices, faceIndex, geometry);
        const bool currentRoomValid = face.roomNumber < indoorGeometry.sectors.size();
        const bool behindRoomValid = face.roomBehindNumber < indoorGeometry.sectors.size();
        const std::vector<uint16_t> currentRoomFaceIds =
            currentRoomValid ? indoorSectorFaceIds(indoorGeometry, face.roomNumber) : std::vector<uint16_t>{};
        const std::vector<uint16_t> behindRoomFaceIds =
            behindRoomValid ? indoorSectorFaceIds(indoorGeometry, face.roomBehindNumber) : std::vector<uint16_t>{};
        const std::vector<uint16_t> connectedRoomIds =
            currentRoomValid ? connectedIndoorRoomIds(indoorGeometry, face.roomNumber) : std::vector<uint16_t>{};
        const bool roomIsolated =
            m_viewport.isolatedIndoorRoomId().has_value() && *m_viewport.isolatedIndoorRoomId() == face.roomNumber;
        const bool behindRoomIsolated =
            m_viewport.isolatedIndoorRoomId().has_value()
            && *m_viewport.isolatedIndoorRoomId() == face.roomBehindNumber;
        const std::vector<size_t> linkedDoorIndices =
            collectLinkedIndoorMechanismIndicesForFaces(sceneData, selectedFaceIndices);
        const std::vector<uint16_t> selectedEventIds =
            collectIndoorFaceEventIds(sceneData, indoorGeometry, selectedFaceIndices);

        if (multiSelection)
        {
            std::unordered_set<uint16_t> selectedRoomIds;
            std::unordered_set<std::string> selectedTextureNames;
            size_t faceOverrideCount = 0;
            size_t eventFaceCount = 0;
            size_t portalFaceCount = 0;

            for (size_t selectedFaceIndex : selectedFaceIndices)
            {
                if (selectedFaceIndex >= indoorGeometry.faces.size())
                {
                    continue;
                }

                const Game::IndoorFace &selectedFace = indoorGeometry.faces[selectedFaceIndex];
                const Game::IndoorFace selectedEffectiveFace =
                    effectiveIndoorFace(sceneData, indoorGeometry, selectedFaceIndex);
                const uint32_t selectedEffectiveAttributes =
                    effectiveIndoorFaceAttributes(sceneData, selectedFace, selectedFaceIndex);

                if (findIndoorFaceAttributeOverride(sceneData, selectedFaceIndex) != nullptr)
                {
                    ++faceOverrideCount;
                }

                if (selectedEffectiveFace.cogTriggered != 0)
                {
                    ++eventFaceCount;
                }

                if (selectedFace.isPortal
                    || Game::hasFaceAttribute(selectedEffectiveAttributes, Game::FaceAttribute::IsPortal))
                {
                    ++portalFaceCount;
                }

                if (!selectedFace.textureName.empty())
                {
                    selectedTextureNames.insert(selectedFace.textureName);
                }

                if (selectedFace.roomNumber < indoorGeometry.sectors.size())
                {
                    selectedRoomIds.insert(selectedFace.roomNumber);
                }

                if (selectedFace.roomBehindNumber < indoorGeometry.sectors.size())
                {
                    selectedRoomIds.insert(selectedFace.roomBehindNumber);
                }
            }

            if (beginInspectorSectionBlock("Selected Faces"))
            {
                if (beginInspectorPropertyTable("IndoorSelectedFaceSummary"))
                {
                    renderInspectorReadOnlyField("Face Count", std::to_string(selectedFaceIndices.size()));
                    renderInspectorReadOnlyField("Rooms Touched", std::to_string(selectedRoomIds.size()));
                    renderInspectorReadOnlyField("Textures", std::to_string(selectedTextureNames.size()));
                    renderInspectorReadOnlyField("Overrides", std::to_string(faceOverrideCount));
                    renderInspectorReadOnlyField("Faces With Events", std::to_string(eventFaceCount));
                    renderInspectorReadOnlyField("Portals", std::to_string(portalFaceCount));
                    renderInspectorReadOnlyField("Linked Mechanisms", std::to_string(linkedDoorIndices.size()));
                    ImGui::EndTable();
                }

                if (ImGui::Button("Reset Selected To Base Flags"))
                {
                    session.captureUndoSnapshot();

                    if (resetIndoorFaceAttributeSelectionToBase(sceneData, indoorGeometry, selectedFaceIndices))
                    {
                        session.noteDocumentMutated("Reset selected indoor face flags");
                        pAttributeOverride = findIndoorFaceAttributeOverride(sceneData, faceIndex);
                        effectiveAttributes = effectiveIndoorFaceAttributes(sceneData, face, faceIndex);
                    }
                }

                endInspectorSectionBlock();
            }

            if (beginInspectorSectionBlock("Bulk Flags"))
            {
                const auto renderBulkGroup =
                    [&](const char *pTableId, const char *pGroupLabel, std::initializer_list<Game::FaceAttribute> attributes)
                {
                    renderInspectorSectionHeader(pGroupLabel);

                    if (!ImGui::BeginTable(pTableId, 4, ImGuiTableFlags_SizingStretchProp))
                    {
                        return;
                    }

                    ImGui::TableSetupColumn("Flag", ImGuiTableColumnFlags_WidthStretch, 2.2f);
                    ImGui::TableSetupColumn("State", ImGuiTableColumnFlags_WidthStretch, 1.0f);
                    ImGui::TableSetupColumn("Set", ImGuiTableColumnFlags_WidthFixed, 52.0f);
                    ImGui::TableSetupColumn("Clear", ImGuiTableColumnFlags_WidthFixed, 58.0f);

                    for (Game::FaceAttribute attribute : attributes)
                    {
                        size_t enabledCount = 0;
                        const uint32_t attributeBit = Game::faceAttributeBit(attribute);

                        for (size_t selectedFaceIndex : selectedFaceIndices)
                        {
                            if (selectedFaceIndex >= indoorGeometry.faces.size())
                            {
                                continue;
                            }

                            const Game::IndoorFace &selectedFace = indoorGeometry.faces[selectedFaceIndex];
                            const uint32_t selectedEffectiveAttributes =
                                effectiveIndoorFaceAttributes(sceneData, selectedFace, selectedFaceIndex);

                            if ((selectedEffectiveAttributes & attributeBit) != 0)
                            {
                                ++enabledCount;
                            }
                        }

                        const bool allEnabled = enabledCount == selectedFaceIndices.size();
                        const bool allDisabled = enabledCount == 0;
                        const char *pStateLabel = allEnabled ? "On" : (allDisabled ? "Off" : "Mixed");
                        const ImVec4 stateColor = allEnabled
                            ? colorFromRgb(0xA8D6A1)
                            : (allDisabled ? colorFromRgb(0x98A4B3) : colorFromRgb(0xE5C07B));

                        ImGui::PushID(static_cast<int>(attribute));
                        ImGui::TableNextRow();
                        ImGui::TableSetColumnIndex(0);
                        ImGui::TextUnformatted(indoorFaceAttributeLabel(attribute));
                        ImGui::TableSetColumnIndex(1);
                        ImGui::TextColored(stateColor, "%s", pStateLabel);
                        ImGui::TableSetColumnIndex(2);

                        if (ImGui::Button("Set"))
                        {
                            session.captureUndoSnapshot();

                            if (applyIndoorFaceAttributeMaskToSelection(
                                    sceneData,
                                    indoorGeometry,
                                    selectedFaceIndices,
                                    attributeBit,
                                    true))
                            {
                                session.noteDocumentMutated("Set indoor face flags");
                                pAttributeOverride = findIndoorFaceAttributeOverride(sceneData, faceIndex);
                                effectiveAttributes = effectiveIndoorFaceAttributes(sceneData, face, faceIndex);
                            }
                        }

                        ImGui::TableSetColumnIndex(3);

                        if (ImGui::Button("Clear"))
                        {
                            session.captureUndoSnapshot();

                            if (applyIndoorFaceAttributeMaskToSelection(
                                    sceneData,
                                    indoorGeometry,
                                    selectedFaceIndices,
                                    attributeBit,
                                    false))
                            {
                                session.noteDocumentMutated("Cleared indoor face flags");
                                pAttributeOverride = findIndoorFaceAttributeOverride(sceneData, faceIndex);
                                effectiveAttributes = effectiveIndoorFaceAttributes(sceneData, face, faceIndex);
                            }
                        }

                        ImGui::PopID();
                    }

                    ImGui::EndTable();
                };

                renderBulkGroup(
                    "IndoorFaceBulkInteraction",
                    "Interaction",
                    {
                        Game::FaceAttribute::IsPortal,
                        Game::FaceAttribute::IsSecret,
                        Game::FaceAttribute::Clickable,
                        Game::FaceAttribute::PressurePlate,
                        Game::FaceAttribute::HasHint,
                        Game::FaceAttribute::TriggerByTouch,
                        Game::FaceAttribute::TriggerByMonster,
                        Game::FaceAttribute::TriggerByObject,
                        Game::FaceAttribute::Untouchable
                    });
                renderBulkGroup(
                    "IndoorFaceBulkSurface",
                    "Surface",
                    {
                        Game::FaceAttribute::Fluid,
                        Game::FaceAttribute::Lava,
                        Game::FaceAttribute::FlowUp,
                        Game::FaceAttribute::FlowDown,
                        Game::FaceAttribute::FlowLeft,
                        Game::FaceAttribute::FlowRight,
                        Game::FaceAttribute::IndoorCarpet,
                        Game::FaceAttribute::IndoorSky
                    });
                renderBulkGroup(
                    "IndoorFaceBulkTexture",
                    "Texture / UV",
                    {
                        Game::FaceAttribute::Animated,
                        Game::FaceAttribute::TextureMoveByDoor,
                        Game::FaceAttribute::TextureAlignLeft,
                        Game::FaceAttribute::TextureAlignRight,
                        Game::FaceAttribute::TextureAlignDown,
                        Game::FaceAttribute::TextureAlignBottom,
                        Game::FaceAttribute::FlipNormalU,
                        Game::FaceAttribute::FlipNormalV
                    });
                renderBulkGroup(
                    "IndoorFaceBulkState",
                    "State / Legacy",
                    {
                        Game::FaceAttribute::Invisible,
                        Game::FaceAttribute::Outlined,
                        Game::FaceAttribute::XYPlane,
                        Game::FaceAttribute::XZPlane,
                        Game::FaceAttribute::YZPlane,
                        Game::FaceAttribute::SeenByParty,
                        Game::FaceAttribute::Picked
                    });
                endInspectorSectionBlock();
            }

            if (beginInspectorSectionBlock("Selected Links", false))
            {
                ImGui::Text("Event Ids: %zu", selectedEventIds.size());

                if (selectedEventIds.empty())
                {
                    ImGui::TextDisabled("No selected face references a map event.");
                }
                else
                {
                    for (uint16_t eventId : selectedEventIds)
                    {
                        const std::string buttonLabel = "Preview " + std::to_string(eventId) + "##FaceEvent" + std::to_string(eventId);

                        if (ImGui::Button(buttonLabel.c_str()))
                        {
                            syncIndoorEventPreviewFromViewport(session);
                            std::string errorMessage;

                            if (!session.simulateMapEvent(eventId, errorMessage))
                            {
                                session.logError(errorMessage);
                            }
                            else
                            {
                                applyIndoorEventPreviewToViewport(session);
                            }
                        }

                        ImGui::SameLine();
                        const std::optional<std::string> description = session.describeMapEvent(eventId);
                        ImGui::TextUnformatted(description ? description->c_str() : "<unresolved>");
                    }
                }

                ImGui::Spacing();
                ImGui::Text("Linked Mechanisms: %zu", linkedDoorIndices.size());

                if (linkedDoorIndices.empty())
                {
                    ImGui::TextDisabled("No door/mechanism record references the selected faces.");
                }
                else
                {
                    for (size_t linkedDoorIndex : linkedDoorIndices)
                    {
                        const Game::IndoorSceneDoor &linkedDoor = sceneData.initialState.doors[linkedDoorIndex];
                        const std::string buttonLabel =
                            "Select Door " + std::to_string(linkedDoor.doorIndex) + "##SelectedFaceDoor"
                                + std::to_string(linkedDoorIndex);

                        if (ImGui::Button(buttonLabel.c_str()))
                        {
                            session.select(EditorSelectionKind::Door, linkedDoorIndex);
                        }

                        ImGui::SameLine();
                        ImGui::Text(
                            "doorId %u  faces %zu",
                            linkedDoor.door.doorId,
                            linkedDoor.door.faceIds.size());
                    }
                }

                endInspectorSectionBlock();
            }
        }

        if (beginInspectorSectionBlock("Overview"))
        {
            if (beginInspectorPropertyTable("IndoorFaceOverview"))
            {
                renderInspectorReadOnlyField("Face Index", std::to_string(faceIndex));
                renderInspectorReadOnlyField("Selected Faces", std::to_string(selectedFaceIndices.size()));
                renderInspectorReadOnlyField("Texture", face.textureName.empty() ? "<none>" : face.textureName);
                renderInspectorReadOnlyField("Has Attribute Override", pAttributeOverride != nullptr ? "Yes" : "No");
                renderInspectorReadOnlyField(
                    "Has Trigger Override",
                    pAttributeOverride != nullptr
                            && (pAttributeOverride->textureFrameTableCog.has_value()
                                || pAttributeOverride->cogNumber.has_value()
                                || pAttributeOverride->cogTriggered.has_value()
                                || pAttributeOverride->cogTriggerType.has_value())
                        ? "Yes"
                        : "No");
                renderInspectorReadOnlyField("Effective Attributes", std::to_string(effectiveAttributes));
                renderInspectorReadOnlyField("Base Attributes", std::to_string(face.attributes));
                renderInspectorReadOnlyField("Facet Type", std::to_string(face.facetType));
                renderInspectorReadOnlyField("Vertices", std::to_string(face.vertexIndices.size()));
                ImGui::EndTable();
            }
            endInspectorSectionBlock();
        }

        if (beginInspectorSectionBlock("Room / Portal"))
        {
            if (beginInspectorPropertyTable("IndoorFaceRoomPortal"))
            {
                renderInspectorReadOnlyField("Room", currentRoomValid ? std::to_string(face.roomNumber) : "<invalid>");
                renderInspectorReadOnlyField(
                    "Behind Room",
                    behindRoomValid ? std::to_string(face.roomBehindNumber) : "<invalid>");
                renderInspectorReadOnlyField("Portal", effectivePortal ? "true" : "false");
                renderInspectorReadOnlyField("Connected Rooms", formatIndoorRoomList(connectedRoomIds));
                renderInspectorReadOnlyField("Room Face Count", std::to_string(currentRoomFaceIds.size()));

                if (currentRoomValid)
                {
                    const Game::IndoorSector &room = indoorGeometry.sectors[face.roomNumber];
                    renderInspectorReadOnlyField(
                        "Room Bounds",
                        std::to_string(room.minX) + ", "
                            + std::to_string(room.minY) + ", "
                            + std::to_string(room.minZ) + "  ..  "
                            + std::to_string(room.maxX) + ", "
                            + std::to_string(room.maxY) + ", "
                            + std::to_string(room.maxZ));
                }

                if (effectivePortal && behindRoomValid && face.roomBehindNumber != face.roomNumber)
                {
                    const Game::IndoorSector &behindRoom = indoorGeometry.sectors[face.roomBehindNumber];
                    renderInspectorReadOnlyField(
                        "Other Side Bounds",
                        std::to_string(behindRoom.minX) + ", "
                            + std::to_string(behindRoom.minY) + ", "
                            + std::to_string(behindRoom.minZ) + "  ..  "
                            + std::to_string(behindRoom.maxX) + ", "
                            + std::to_string(behindRoom.maxY) + ", "
                            + std::to_string(behindRoom.maxZ));
                }

                ImGui::EndTable();
            }

            ImGui::BeginDisabled(currentRoomFaceIds.empty());

            if (ImGui::Button("Select Room Faces"))
            {
                session.replaceInteractiveFaceSelection(currentRoomFaceIds.front());

                for (size_t roomFaceIndex = 1; roomFaceIndex < currentRoomFaceIds.size(); ++roomFaceIndex)
                {
                    session.addInteractiveFaceSelection(currentRoomFaceIds[roomFaceIndex]);
                }
            }

            ImGui::EndDisabled();

            if (currentRoomValid)
            {
                ImGui::SameLine();

                if (ImGui::Button(roomIsolated ? "Show All Rooms" : "Isolate Room"))
                {
                    m_viewport.setIsolatedIndoorRoomId(roomIsolated ? std::nullopt : std::optional<uint16_t>(face.roomNumber));
                }
            }

            if (effectivePortal && behindRoomValid && face.roomBehindNumber != face.roomNumber)
            {
                ImGui::SameLine();
                ImGui::BeginDisabled(behindRoomFaceIds.empty());

                if (ImGui::Button("Select Other Side"))
                {
                    session.replaceInteractiveFaceSelection(behindRoomFaceIds.front());

                    for (size_t roomFaceIndex = 1; roomFaceIndex < behindRoomFaceIds.size(); ++roomFaceIndex)
                    {
                        session.addInteractiveFaceSelection(behindRoomFaceIds[roomFaceIndex]);
                    }
                }

                ImGui::EndDisabled();

                ImGui::SameLine();

                if (ImGui::Button(behindRoomIsolated ? "Show All Rooms##Behind" : "Isolate Other Side"))
                {
                    m_viewport.setIsolatedIndoorRoomId(
                        behindRoomIsolated ? std::nullopt : std::optional<uint16_t>(face.roomBehindNumber));
                }
            }

            if (currentRoomValid)
            {
                if (ImGui::Button("Append Room Geometry Snapshot"))
                {
                    std::filesystem::path outputPath;
                    std::string errorMessage;

                    if (appendIndoorRoomGeometryDiagnostic(
                            session,
                            face.roomNumber,
                            faceIndex,
                            outputPath,
                            errorMessage))
                    {
                        const std::string message = "Appended room geometry snapshot to " + outputPath.string();
                        session.logInfo(message);
                        setStatusMessage(StatusMessageKind::Success, message);
                    }
                    else
                    {
                        session.logError(errorMessage);
                        setStatusMessage(StatusMessageKind::Error, errorMessage);
                    }
                }
            }

            if (effectivePortal && behindRoomValid && face.roomBehindNumber != face.roomNumber)
            {
                ImGui::SameLine();

                if (ImGui::Button("Append Other Side Snapshot"))
                {
                    std::filesystem::path outputPath;
                    std::string errorMessage;

                    if (appendIndoorRoomGeometryDiagnostic(
                            session,
                            face.roomBehindNumber,
                            faceIndex,
                            outputPath,
                            errorMessage))
                    {
                        const std::string message = "Appended other-side room snapshot to " + outputPath.string();
                        session.logInfo(message);
                        setStatusMessage(StatusMessageKind::Success, message);
                    }
                    else
                    {
                        session.logError(errorMessage);
                        setStatusMessage(StatusMessageKind::Error, errorMessage);
                    }
                }
            }

            endInspectorSectionBlock();
        }

        bool changed = false;

        if (beginInspectorSectionBlock("Flags"))
        {
            const bool hasAttributeOverride =
                pAttributeOverride != nullptr && pAttributeOverride->legacyAttributes.has_value();

            ImGui::TextDisabled(
                "%s",
                hasAttributeOverride
                    ? "Scene YML overrides these base BLV face flags."
                    : "Using base BLV face flags. Editing below creates a scene override.");

            if (pAttributeOverride != nullptr && ImGui::Button("Reset To Base Flags"))
            {
                session.captureUndoSnapshot();
                synchronizeIndoorFaceAttributeOverride(sceneData, faceIndex, face.attributes, face.attributes);
                effectiveAttributes = face.attributes;
                pAttributeOverride = findIndoorFaceAttributeOverride(sceneData, faceIndex);
                session.noteDocumentMutated("Reset indoor face flags");
                effectiveFace = effectiveIndoorFace(sceneData, indoorGeometry, faceIndex);
            }

            if (beginInspectorPropertyTable("IndoorFaceFlagBase"))
            {
                renderInspectorReadOnlyField("Base Legacy Attributes", std::to_string(face.attributes));
                renderInspectorReadOnlyField("Base Active Flags", formatIndoorFaceAttributeList(face.attributes));
                ImGui::EndTable();
            }

            if (beginInspectorPropertyTable("IndoorFaceFlagOverrides"))
            {
                renderInspectorReadOnlyField("Flag Source", hasAttributeOverride ? "Scene Override" : "Base BLV");
                renderInspectorReadOnlyField("Effective Attributes", std::to_string(effectiveAttributes));
                renderInspectorReadOnlyField("Effective Active Flags", formatIndoorFaceAttributeList(effectiveAttributes));
                ImGui::EndTable();
            }

            if (beginInspectorPropertyTable("IndoorFaceFlagsEditor"))
            {
                const auto editAttribute = [&](Game::FaceAttribute attribute)
                {
                    if (editBitCheckbox(
                            session,
                            indoorFaceAttributeLabel(attribute),
                            effectiveAttributes,
                            Game::faceAttributeBit(attribute)))
                    {
                        changed = true;
                    }
                };

                editAttribute(Game::FaceAttribute::IsPortal);
                editAttribute(Game::FaceAttribute::IsSecret);
                editAttribute(Game::FaceAttribute::Invisible);
                editAttribute(Game::FaceAttribute::Clickable);
                editAttribute(Game::FaceAttribute::PressurePlate);
                editAttribute(Game::FaceAttribute::HasHint);
                editAttribute(Game::FaceAttribute::TriggerByTouch);
                editAttribute(Game::FaceAttribute::TriggerByMonster);
                editAttribute(Game::FaceAttribute::TriggerByObject);
                editAttribute(Game::FaceAttribute::Untouchable);
                editAttribute(Game::FaceAttribute::Animated);
                editAttribute(Game::FaceAttribute::Outlined);
                editAttribute(Game::FaceAttribute::TextureMoveByDoor);
                editAttribute(Game::FaceAttribute::TextureAlignLeft);
                editAttribute(Game::FaceAttribute::TextureAlignRight);
                editAttribute(Game::FaceAttribute::TextureAlignDown);
                editAttribute(Game::FaceAttribute::TextureAlignBottom);
                editAttribute(Game::FaceAttribute::FlipNormalU);
                editAttribute(Game::FaceAttribute::FlipNormalV);
                editAttribute(Game::FaceAttribute::Fluid);
                editAttribute(Game::FaceAttribute::Lava);
                editAttribute(Game::FaceAttribute::FlowUp);
                editAttribute(Game::FaceAttribute::FlowDown);
                editAttribute(Game::FaceAttribute::FlowLeft);
                editAttribute(Game::FaceAttribute::FlowRight);
                editAttribute(Game::FaceAttribute::XYPlane);
                editAttribute(Game::FaceAttribute::XZPlane);
                editAttribute(Game::FaceAttribute::YZPlane);
                editAttribute(Game::FaceAttribute::IndoorCarpet);
                editAttribute(Game::FaceAttribute::IndoorSky);
                editAttribute(Game::FaceAttribute::SeenByParty);
                editAttribute(Game::FaceAttribute::Picked);
                ImGui::EndTable();
            }

            endInspectorSectionBlock();
        }

        if (changed)
        {
            synchronizeIndoorFaceAttributeOverride(sceneData, faceIndex, effectiveAttributes, face.attributes);
            session.noteDocumentMutated({});
            pAttributeOverride = findIndoorFaceAttributeOverride(sceneData, faceIndex);
            effectiveFace = effectiveIndoorFace(sceneData, indoorGeometry, faceIndex);
        }

        if (beginInspectorSectionBlock("Triggers"))
        {
            bool triggerChanged = false;
            uint16_t effectiveTextureFrameTableCog = effectiveFace.textureFrameTableCog;
            uint16_t effectiveCogNumber = effectiveFace.cogNumber;
            uint16_t effectiveCogTriggered = effectiveFace.cogTriggered;
            uint16_t effectiveCogTriggerType = effectiveFace.cogTriggerType;
            const bool hasTriggerOverride =
                pAttributeOverride != nullptr
                && (pAttributeOverride->textureFrameTableCog.has_value()
                    || pAttributeOverride->cogNumber.has_value()
                    || pAttributeOverride->cogTriggered.has_value()
                    || pAttributeOverride->cogTriggerType.has_value());

            ImGui::TextDisabled(
                "%s",
                hasTriggerOverride
                    ? "Scene YML overrides these base BLV trigger fields."
                    : "Using base BLV trigger fields. Editing below creates a scene override.");

            if (hasTriggerOverride && ImGui::Button("Reset To Base Triggers"))
            {
                session.captureUndoSnapshot();
                synchronizeIndoorFaceTriggerOverride(
                    sceneData,
                    face,
                    faceIndex,
                    face.textureFrameTableCog,
                    face.cogNumber,
                    face.cogTriggered,
                    face.cogTriggerType);
                pAttributeOverride = findIndoorFaceAttributeOverride(sceneData, faceIndex);
                effectiveFace = effectiveIndoorFace(sceneData, indoorGeometry, faceIndex);
                session.noteDocumentMutated("Reset indoor face triggers");
                effectiveTextureFrameTableCog = effectiveFace.textureFrameTableCog;
                effectiveCogNumber = effectiveFace.cogNumber;
                effectiveCogTriggered = effectiveFace.cogTriggered;
                effectiveCogTriggerType = effectiveFace.cogTriggerType;
            }

            if (beginInspectorPropertyTable("IndoorFaceTriggerBase"))
            {
                renderInspectorReadOnlyField("Base Legacy Event Number", std::to_string(face.cogNumber));
                renderInspectorReadOnlyField("Base Event Id", std::to_string(face.cogTriggered));
                renderResolvedMapEventField(session, "Base Event", face.cogTriggered);
                renderInspectorReadOnlyField("Base Trigger Type", std::to_string(face.cogTriggerType));
                renderInspectorReadOnlyField("Base Texture Frame Cog", std::to_string(face.textureFrameTableCog));
                ImGui::EndTable();
            }

            if (beginInspectorPropertyTable("IndoorFaceTriggerOverrides"))
            {
                renderInspectorReadOnlyField("Trigger Source", hasTriggerOverride ? "Scene Override" : "Base BLV");
                triggerChanged =
                    editUInt16Field(session, "Scene Legacy Event Number", effectiveCogNumber) || triggerChanged;
                triggerChanged = editUInt16Field(session, "Scene Event Id", effectiveCogTriggered) || triggerChanged;
                renderResolvedMapEventField(session, "Effective Event", effectiveCogTriggered);
                triggerChanged =
                    editUInt16Field(session, "Scene Event Trigger Type", effectiveCogTriggerType) || triggerChanged;
                triggerChanged =
                    editUInt16Field(session, "Scene Texture Frame Cog", effectiveTextureFrameTableCog) || triggerChanged;
                ImGui::EndTable();
            }

            if (triggerChanged)
            {
                synchronizeIndoorFaceTriggerOverride(
                    sceneData,
                    face,
                    faceIndex,
                    effectiveTextureFrameTableCog,
                    effectiveCogNumber,
                    effectiveCogTriggered,
                    effectiveCogTriggerType);
                session.noteDocumentMutated("Updated indoor face triggers");
                pAttributeOverride = findIndoorFaceAttributeOverride(sceneData, faceIndex);
                effectiveFace = effectiveIndoorFace(sceneData, indoorGeometry, faceIndex);
            }

            endInspectorSectionBlock();
        }

        if (beginInspectorSectionBlock("Event Preview", false))
        {
            if (effectiveFace.cogTriggered == 0)
            {
                ImGui::TextDisabled("This face does not reference a map event.");
            }
            else
            {
                if (ImGui::Button("Simulate Face Click"))
                {
                    syncIndoorEventPreviewFromViewport(session);
                    std::string errorMessage;

                    if (!session.simulateMapEvent(effectiveFace.cogTriggered, errorMessage))
                    {
                        session.logError(errorMessage);
                    }
                    else
                    {
                        applyIndoorEventPreviewToViewport(session);
                    }
                }

                ImGui::SameLine();

                if (ImGui::Button("Reset Preview"))
                {
                    session.resetPreviewEventRuntimeState();
                    m_viewport.clearIndoorMechanismPreview(session.document());
                }

                if (session.lastPreviewEventId().has_value())
                {
                    ImGui::Text(
                        "Last Event: %u",
                        static_cast<unsigned>(*session.lastPreviewEventId()));
                }

                const std::vector<std::string> &statusMessages = session.lastPreviewEventStatusMessages();
                const std::vector<std::string> &messages = session.lastPreviewEventMessages();

                if (statusMessages.empty() && messages.empty())
                {
                    ImGui::TextDisabled("No preview messages captured.");
                }
                else
                {
                    for (const std::string &message : statusMessages)
                    {
                        ImGui::Text("Status: %s", message.c_str());
                    }

                    for (const std::string &message : messages)
                    {
                        ImGui::TextWrapped("%s", message.c_str());
                    }
                }
            }

            endInspectorSectionBlock();
        }

        if (beginInspectorSectionBlock("Linked Mechanisms", false))
        {
            ImGui::Text("Mechanisms Using Selection: %zu", linkedDoorIndices.size());

            if (linkedDoorIndices.empty())
            {
                ImGui::TextDisabled("No door/mechanism record references this face.");
            }
            else
            {
                for (size_t doorIndex : linkedDoorIndices)
                {
                    const Game::IndoorSceneDoor &door = sceneData.initialState.doors[doorIndex];
                    const std::string buttonLabel =
                        "Select Door " + std::to_string(door.doorIndex) + "##FaceDoor" + std::to_string(doorIndex);

                    if (ImGui::Button(buttonLabel.c_str()))
                    {
                        session.select(EditorSelectionKind::Door, doorIndex);
                    }

                    ImGui::SameLine();
                    ImGui::Text(
                        "doorId %u  state %u  faces %zu",
                        door.door.doorId,
                        static_cast<unsigned>(door.door.state),
                        door.door.faceIds.size());
                }
            }

            endInspectorSectionBlock();
        }

        if (hasGeometry && beginInspectorSectionBlock("Geometry", false))
        {
            if (beginInspectorPropertyTable("IndoorFaceGeometry"))
            {
                renderInspectorReadOnlyField("Bounds Min",
                    std::to_string(static_cast<int>(geometry.minX)) + ", "
                        + std::to_string(static_cast<int>(geometry.minY)) + ", "
                        + std::to_string(static_cast<int>(geometry.minZ)));
                renderInspectorReadOnlyField("Bounds Max",
                    std::to_string(static_cast<int>(geometry.maxX)) + ", "
                        + std::to_string(static_cast<int>(geometry.maxY)) + ", "
                        + std::to_string(static_cast<int>(geometry.maxZ)));
                renderInspectorReadOnlyField("Normal",
                    std::to_string(geometry.normal.x) + ", "
                        + std::to_string(geometry.normal.y) + ", "
                        + std::to_string(geometry.normal.z));
                ImGui::EndTable();
            }
            endInspectorSectionBlock();
        }

        return;
    }

    EditorDocument &document = session.document();
    Game::OutdoorSceneData &sceneData = document.mutableOutdoorSceneData();
    Game::OutdoorMapData &outdoorGeometry = document.mutableOutdoorGeometry();
    size_t bmodelIndex = 0;
    size_t faceIndex = 0;

    if (!decodeFlattenedOutdoorFaceIndex(outdoorGeometry, session.selection().index, bmodelIndex, faceIndex))
    {
        ImGui::TextUnformatted("Select a bmodel face from the viewport in Face mode.");
        return;
    }

    if (bmodelIndex >= outdoorGeometry.bmodels.size() || faceIndex >= outdoorGeometry.bmodels[bmodelIndex].faces.size())
    {
        ImGui::TextUnformatted("Selected face is out of range.");
        return;
    }

    Game::OutdoorBModelFace &baseFace = outdoorGeometry.bmodels[bmodelIndex].faces[faceIndex];
    Game::OutdoorSceneInteractiveFace *pInteractiveFace = findInteractiveFace(sceneData, bmodelIndex, faceIndex);
    const Game::OutdoorSceneBModelFaceSource *pFaceSource = findBModelFaceSource(sceneData, bmodelIndex, faceIndex);
    const std::vector<size_t> &selectedFaceIndices = session.selectedInteractiveFaceIndices();
    bool changed = false;

    ImGui::Text("BModel: %zu", bmodelIndex);
    ImGui::Text("Face: %zu", faceIndex);
    ImGui::Text("Texture: %s", baseFace.textureName.empty() ? "<none>" : baseFace.textureName.c_str());
    ImGui::Text("Polygon Type: %u", baseFace.polygonType);
    ImGui::Text("Walkable: %s", Game::isOutdoorWalkablePolygonType(baseFace.polygonType) ? "yes" : "no");
    ImGui::Text("Has Scene Entry: %s", pInteractiveFace != nullptr ? "yes" : "no");

    if (pFaceSource != nullptr)
    {
        ImGui::Text(
            "Source: %s model %zu poly %zu",
            pFaceSource->sourceKind.c_str(),
            pFaceSource->sourceModelIndex,
            pFaceSource->sourcePolyIndex);
    }
    else
    {
        ImGui::TextDisabled("Source: <none>");
    }

    const auto forEachSelectedFace =
        [&](const auto &callback)
    {
        for (size_t flatIndex : selectedFaceIndices)
        {
            size_t selectedBModelIndex = 0;
            size_t selectedFaceIndex = 0;

            if (!decodeFlattenedOutdoorFaceIndex(
                    outdoorGeometry,
                    flatIndex,
                    selectedBModelIndex,
                    selectedFaceIndex))
            {
                continue;
            }

            callback(
                flatIndex,
                selectedBModelIndex,
                selectedFaceIndex,
                outdoorGeometry.bmodels[selectedBModelIndex].faces[selectedFaceIndex]);
        }
    };

    renderInspectorSectionHeader("Selection");
    ImGui::Text("Selected Faces: %zu", selectedFaceIndices.size());

    if (ImGui::Button("Select All On BModel", ImVec2(170.0f, 0.0f)))
    {
        session.clearInteractiveFaceSelection();

        for (size_t currentFaceIndex = 0; currentFaceIndex < outdoorGeometry.bmodels[bmodelIndex].faces.size(); ++currentFaceIndex)
        {
            session.addInteractiveFaceSelection(flattenedOutdoorFaceIndex(outdoorGeometry, bmodelIndex, currentFaceIndex));
        }
    }

    ImGui::SameLine();

    if (ImGui::Button("Keep Only Current", ImVec2(160.0f, 0.0f)))
    {
        session.replaceInteractiveFaceSelection(flattenedOutdoorFaceIndex(outdoorGeometry, bmodelIndex, faceIndex));
    }

    renderInspectorSectionHeader("Selection Actions");

    if (ImGui::Button("Apply Texture To Selected", ImVec2(190.0f, 0.0f)))
    {
        session.captureUndoSnapshot();
        forEachSelectedFace(
            [&](size_t, size_t, size_t, Game::OutdoorBModelFace &selectedFace)
            {
                selectedFace.textureName = baseFace.textureName;
            });
        changed = true;
    }

    ImGui::SameLine();

    if (ImGui::Button("Apply Mapping To Selected", ImVec2(190.0f, 0.0f)))
    {
        session.captureUndoSnapshot();
        forEachSelectedFace(
            [&](size_t, size_t, size_t, Game::OutdoorBModelFace &selectedFace)
            {
                if (selectedFace.vertexIndices.size() != baseFace.vertexIndices.size())
                {
                    return;
                }

                selectedFace.textureUs = baseFace.textureUs;
                selectedFace.textureVs = baseFace.textureVs;
                selectedFace.textureDeltaU = baseFace.textureDeltaU;
                selectedFace.textureDeltaV = baseFace.textureDeltaV;
            });
        changed = true;
    }

    if (ImGui::Button("Apply Scene Override To Selected", ImVec2(220.0f, 0.0f)))
    {
        if (pInteractiveFace != nullptr)
        {
            session.captureUndoSnapshot();
            forEachSelectedFace(
                [&](size_t, size_t selectedBModelIndex, size_t selectedFaceIndex, Game::OutdoorBModelFace &selectedFace)
                {
                    Game::OutdoorSceneInteractiveFace *pSelectedInteractiveFace =
                        findInteractiveFace(sceneData, selectedBModelIndex, selectedFaceIndex);

                    if (pSelectedInteractiveFace == nullptr)
                    {
                        sceneData.interactiveFaces.push_back(makeInteractiveFaceEntry(
                            selectedBModelIndex,
                            selectedFaceIndex,
                            selectedFace));
                        pSelectedInteractiveFace = &sceneData.interactiveFaces.back();
                    }

                    pSelectedInteractiveFace->legacyAttributes = pInteractiveFace->legacyAttributes;
                    pSelectedInteractiveFace->cogNumber = pInteractiveFace->cogNumber;
                    pSelectedInteractiveFace->cogTriggeredNumber = pInteractiveFace->cogTriggeredNumber;
                    pSelectedInteractiveFace->cogTrigger = pInteractiveFace->cogTrigger;
                });
            changed = true;
        }
    }

    ImGui::BeginDisabled(pInteractiveFace == nullptr);
    ImGui::SameLine();
    if (ImGui::Button("Reset Selected Scene Overrides", ImVec2(230.0f, 0.0f)))
    {
        session.captureUndoSnapshot();
        sceneData.interactiveFaces.erase(
            std::remove_if(
                sceneData.interactiveFaces.begin(),
                sceneData.interactiveFaces.end(),
                [&session, &outdoorGeometry](const Game::OutdoorSceneInteractiveFace &interactiveFace)
                {
                    const size_t flatIndex = flattenedOutdoorFaceIndex(
                        outdoorGeometry,
                        interactiveFace.bmodelIndex,
                        interactiveFace.faceIndex);
                    return session.isInteractiveFaceSelected(flatIndex);
                }),
            sceneData.interactiveFaces.end());
        changed = true;
        pInteractiveFace = findInteractiveFace(sceneData, bmodelIndex, faceIndex);
    }
    ImGui::EndDisabled();

    renderInspectorSectionHeader("Clipboard");

    if (ImGui::Button("Copy Face Setup", ImVec2(150.0f, 0.0f)))
    {
        m_faceClipboard.valid = true;
        m_faceClipboard.textureName = baseFace.textureName;
        m_faceClipboard.textureUs = baseFace.textureUs;
        m_faceClipboard.textureVs = baseFace.textureVs;
        m_faceClipboard.textureDeltaU = baseFace.textureDeltaU;
        m_faceClipboard.textureDeltaV = baseFace.textureDeltaV;
        m_faceClipboard.hasSceneOverride = pInteractiveFace != nullptr;
        m_faceClipboard.sceneLegacyAttributes = pInteractiveFace != nullptr ? pInteractiveFace->legacyAttributes : 0;
        m_faceClipboard.sceneCogNumber = pInteractiveFace != nullptr ? pInteractiveFace->cogNumber : 0;
        m_faceClipboard.sceneCogTriggeredNumber = pInteractiveFace != nullptr ? pInteractiveFace->cogTriggeredNumber : 0;
        m_faceClipboard.sceneCogTrigger = pInteractiveFace != nullptr ? pInteractiveFace->cogTrigger : 0;
    }

    ImGui::BeginDisabled(!m_faceClipboard.valid);
    ImGui::SameLine();
    if (ImGui::Button("Paste Visual", ImVec2(120.0f, 0.0f)))
    {
        session.captureUndoSnapshot();
        forEachSelectedFace(
            [this](size_t, size_t, size_t, Game::OutdoorBModelFace &selectedFace)
            {
                selectedFace.textureName = m_faceClipboard.textureName;

                if (selectedFace.vertexIndices.size() == m_faceClipboard.textureUs.size())
                {
                    selectedFace.textureUs = m_faceClipboard.textureUs;
                    selectedFace.textureVs = m_faceClipboard.textureVs;
                }

                selectedFace.textureDeltaU = m_faceClipboard.textureDeltaU;
                selectedFace.textureDeltaV = m_faceClipboard.textureDeltaV;
            });
        changed = true;
    }

    if (ImGui::Button("Paste Gameplay", ImVec2(130.0f, 0.0f)))
    {
        if (m_faceClipboard.hasSceneOverride)
        {
            session.captureUndoSnapshot();
            forEachSelectedFace(
                [this, &sceneData](size_t, size_t selectedBModelIndex, size_t selectedFaceIndex, Game::OutdoorBModelFace &selectedFace)
                {
                    Game::OutdoorSceneInteractiveFace *pSelectedInteractiveFace =
                        findInteractiveFace(sceneData, selectedBModelIndex, selectedFaceIndex);

                    if (pSelectedInteractiveFace == nullptr)
                    {
                        sceneData.interactiveFaces.push_back(makeInteractiveFaceEntry(
                            selectedBModelIndex,
                            selectedFaceIndex,
                            selectedFace));
                        pSelectedInteractiveFace = &sceneData.interactiveFaces.back();
                    }

                    pSelectedInteractiveFace->legacyAttributes = m_faceClipboard.sceneLegacyAttributes;
                    pSelectedInteractiveFace->cogNumber = m_faceClipboard.sceneCogNumber;
                    pSelectedInteractiveFace->cogTriggeredNumber = m_faceClipboard.sceneCogTriggeredNumber;
                    pSelectedInteractiveFace->cogTrigger = m_faceClipboard.sceneCogTrigger;
                });
            changed = true;
            pInteractiveFace = findInteractiveFace(sceneData, bmodelIndex, faceIndex);
        }
    }

    ImGui::SameLine();

    if (ImGui::Button("Paste All", ImVec2(110.0f, 0.0f)))
    {
        session.captureUndoSnapshot();
        forEachSelectedFace(
            [this, &sceneData](size_t, size_t selectedBModelIndex, size_t selectedFaceIndex, Game::OutdoorBModelFace &selectedFace)
            {
                selectedFace.textureName = m_faceClipboard.textureName;

                if (selectedFace.vertexIndices.size() == m_faceClipboard.textureUs.size())
                {
                    selectedFace.textureUs = m_faceClipboard.textureUs;
                    selectedFace.textureVs = m_faceClipboard.textureVs;
                }

                selectedFace.textureDeltaU = m_faceClipboard.textureDeltaU;
                selectedFace.textureDeltaV = m_faceClipboard.textureDeltaV;

                if (!m_faceClipboard.hasSceneOverride)
                {
                    return;
                }

                Game::OutdoorSceneInteractiveFace *pSelectedInteractiveFace =
                    findInteractiveFace(sceneData, selectedBModelIndex, selectedFaceIndex);

                if (pSelectedInteractiveFace == nullptr)
                {
                    sceneData.interactiveFaces.push_back(makeInteractiveFaceEntry(
                        selectedBModelIndex,
                        selectedFaceIndex,
                        selectedFace));
                    pSelectedInteractiveFace = &sceneData.interactiveFaces.back();
                }

                pSelectedInteractiveFace->legacyAttributes = m_faceClipboard.sceneLegacyAttributes;
                pSelectedInteractiveFace->cogNumber = m_faceClipboard.sceneCogNumber;
                pSelectedInteractiveFace->cogTriggeredNumber = m_faceClipboard.sceneCogTriggeredNumber;
                pSelectedInteractiveFace->cogTrigger = m_faceClipboard.sceneCogTrigger;
            });
        changed = true;
        pInteractiveFace = findInteractiveFace(sceneData, bmodelIndex, faceIndex);
    }
    ImGui::EndDisabled();

    renderInspectorSectionHeader("Visual");
    if (beginInspectorPropertyTable("InteractiveFaceVisualFields"))
    {
        changed = renderBitmapTextureSelector(session, "Texture", baseFace.textureName, bmodelIndex) || changed;
        changed = editStringField(session, "Texture Name Raw", baseFace.textureName, 11) || changed;
        ImGui::EndTable();
    }

    if (pInteractiveFace == nullptr)
    {
        if (ImGui::Button("Add Interactive Face Entry"))
        {
            session.captureUndoSnapshot();
            sceneData.interactiveFaces.push_back(makeInteractiveFaceEntry(
                bmodelIndex,
                faceIndex,
                baseFace));
            pInteractiveFace = &sceneData.interactiveFaces.back();
            changed = true;
        }
    }
    else if (ImGui::Button("Remove Interactive Face Entry"))
    {
        session.captureUndoSnapshot();
        sceneData.interactiveFaces.erase(
            std::remove_if(
                sceneData.interactiveFaces.begin(),
                sceneData.interactiveFaces.end(),
                [bmodelIndex, faceIndex](const Game::OutdoorSceneInteractiveFace &interactiveFace)
                {
                    return interactiveFace.bmodelIndex == bmodelIndex && interactiveFace.faceIndex == faceIndex;
                }),
            sceneData.interactiveFaces.end());
        changed = true;
        pInteractiveFace = nullptr;
    }

    ImGui::SameLine();

    if (ImGui::Button("Delete Face", ImVec2(140.0f, 0.0f)))
    {
        session.captureUndoSnapshot();
        Game::OutdoorBModel &bmodel = outdoorGeometry.bmodels[bmodelIndex];
        bmodel.faces.erase(bmodel.faces.begin() + static_cast<ptrdiff_t>(faceIndex));
        bmodel.bspNodes.clear();
        repairOutdoorSceneFaceReferencesAfterDelete(sceneData, bmodelIndex, faceIndex);
        recomputeBModelMetadata(bmodel);

        if (!bmodel.faces.empty())
        {
            const size_t replacementFaceIndex = std::min(faceIndex, bmodel.faces.size() - 1);
            session.select(
                EditorSelectionKind::InteractiveFace,
                flattenedOutdoorFaceIndex(outdoorGeometry, bmodelIndex, replacementFaceIndex));
        }
        else
        {
            session.select(EditorSelectionKind::BModel, bmodelIndex);
        }

        changed = true;
        pInteractiveFace = nullptr;
    }

    if (pInteractiveFace != nullptr)
    {
        renderInspectorSectionHeader("Scene Override");
        ImGui::PushID("SceneOverride");
        if (beginInspectorPropertyTable("InteractiveFaceFields"))
        {
            changed = editBitCheckbox(session, "Fluid", pInteractiveFace->legacyAttributes, FaceAttributeFluid) || changed;
            changed =
                editBitCheckbox(session, "Invisible", pInteractiveFace->legacyAttributes, FaceAttributeInvisible)
                || changed;
            changed =
                editBitCheckbox(session, "Has Hint", pInteractiveFace->legacyAttributes, FaceAttributeHasHint)
                || changed;
            changed =
                editBitCheckbox(session, "Clickable", pInteractiveFace->legacyAttributes, FaceAttributeClickable)
                || changed;
            changed = editBitCheckbox(
                session,
                "Pressure Plate",
                pInteractiveFace->legacyAttributes,
                FaceAttributePressurePlate) || changed;
            changed = editBitCheckbox(
                session,
                "Untouchable",
                pInteractiveFace->legacyAttributes,
                FaceAttributeUntouchable) || changed;
            changed = editUInt32Field(session, "Legacy Attributes", pInteractiveFace->legacyAttributes) || changed;
            changed = editUInt16Field(session, "Legacy Event Number", pInteractiveFace->cogNumber) || changed;
            changed = editMapEventField(
                session,
                "Event Id",
                pInteractiveFace->cogTriggeredNumber) || changed;
            renderResolvedMapEventField(session, "Resolved Event", pInteractiveFace->cogTriggeredNumber);
            changed = editUInt16Field(session, "Legacy Event Trigger", pInteractiveFace->cogTrigger) || changed;
            ImGui::EndTable();
        }
        ImGui::PopID();
    }
    else
    {
        ImGui::Spacing();
        ImGui::TextDisabled("No scene override. Add an Interactive Face Entry for gameplay-visible changes.");
    }

    if (pFaceSource != nullptr)
    {
        ImGui::SetNextItemOpen(true, ImGuiCond_FirstUseEver);
        if (ImGui::CollapsingHeader("Source Face"))
        {
            if (beginInspectorPropertyTable("InteractiveFaceSourceFields"))
            {
                renderInspectorReadOnlyField("Source Kind", pFaceSource->sourceKind);
                renderInspectorReadOnlyField("Source Model Index", std::to_string(pFaceSource->sourceModelIndex));
                renderInspectorReadOnlyField("Source Model Name", pFaceSource->sourceModelName);
                renderInspectorReadOnlyField("Source Poly Index", std::to_string(pFaceSource->sourcePolyIndex));
                renderInspectorReadOnlyField("Texture Alias", pFaceSource->textureAlias);
                ImGui::EndTable();
            }
        }
    }

    ImGui::SetNextItemOpen(false, ImGuiCond_FirstUseEver);
    if (ImGui::CollapsingHeader("Base ODM Face"))
    {
        if (beginInspectorPropertyTable("InteractiveFaceBaseFields"))
        {
            const bx::Vec3 baseNormal = faceNormal(outdoorGeometry.bmodels[bmodelIndex].vertices, baseFace);
            const float outwardDot = faceOutwardDot(
                outdoorGeometry.bmodels[bmodelIndex].vertices,
                baseFace,
                static_cast<float>(outdoorGeometry.bmodels[bmodelIndex].boundingCenterX),
                static_cast<float>(outdoorGeometry.bmodels[bmodelIndex].boundingCenterY),
                static_cast<float>(outdoorGeometry.bmodels[bmodelIndex].boundingCenterZ));
            renderInspectorReadOnlyField(
                "Normal",
                std::to_string(baseNormal.x).substr(0, 5) + ", "
                    + std::to_string(baseNormal.y).substr(0, 5) + ", "
                    + std::to_string(baseNormal.z).substr(0, 5));
            renderInspectorReadOnlyField("Outward Dot", std::to_string(outwardDot));
            renderInspectorReadOnlyField("Legacy Attributes Raw", std::to_string(baseFace.attributes));
            renderInspectorReadOnlyField("Legacy Event Number", std::to_string(baseFace.cogNumber));
            renderInspectorReadOnlyField("Event Id", std::to_string(baseFace.cogTriggeredNumber));
            renderInspectorReadOnlyField("Legacy Event Trigger", std::to_string(baseFace.cogTrigger));
            renderInspectorReadOnlyField("Fluid", (baseFace.attributes & FaceAttributeFluid) != 0 ? "true" : "false");
            renderInspectorReadOnlyField(
                "Invisible",
                (baseFace.attributes & FaceAttributeInvisible) != 0 ? "true" : "false");
            renderInspectorReadOnlyField(
                "Has Hint",
                (baseFace.attributes & FaceAttributeHasHint) != 0 ? "true" : "false");
            renderInspectorReadOnlyField(
                "Clickable",
                (baseFace.attributes & FaceAttributeClickable) != 0 ? "true" : "false");
            renderInspectorReadOnlyField(
                "Pressure Plate",
                (baseFace.attributes & FaceAttributePressurePlate) != 0 ? "true" : "false");
            renderInspectorReadOnlyField(
                "Untouchable",
                (baseFace.attributes & FaceAttributeUntouchable) != 0 ? "true" : "false");
            ImGui::EndTable();
        }

        ImGui::TextDisabled("Outdoor gameplay uses the scene override entry above, not the raw ODM face values.");

        if (ImGui::Button("Flip Selected Faces", ImVec2(170.0f, 0.0f)))
        {
            session.captureUndoSnapshot();
            forEachSelectedFace(
                [&](size_t, size_t, size_t, Game::OutdoorBModelFace &selectedFace)
                {
                    reverseFaceWinding(selectedFace);
                });
            changed = true;
        }

        ImGui::SameLine();

        if (ImGui::Button("Recompute Outward On BModel", ImVec2(230.0f, 0.0f)))
        {
            session.captureUndoSnapshot();
            Game::OutdoorBModel &bmodel = outdoorGeometry.bmodels[bmodelIndex];
            const float modelCenterX = static_cast<float>(bmodel.boundingCenterX);
            const float modelCenterY = static_cast<float>(bmodel.boundingCenterY);
            const float modelCenterZ = static_cast<float>(bmodel.boundingCenterZ);

            for (Game::OutdoorBModelFace &face : bmodel.faces)
            {
                orientFaceWindingOutward(bmodel.vertices, face, modelCenterX, modelCenterY, modelCenterZ);
            }

            changed = true;
        }
    }

    ImGui::SetNextItemOpen(false, ImGuiCond_FirstUseEver);
    if (ImGui::CollapsingHeader("Texture Mapping"))
    {
        int textureWidth = 256;
        int textureHeight = 256;
        ensureBitmapPreviewTexture(session, baseFace.textureName);

        if (const std::optional<std::pair<int, int>> size = bitmapPreviewTextureSize(baseFace.textureName))
        {
            textureWidth = size->first;
            textureHeight = size->second;
        }

        if (beginInspectorPropertyTable("InteractiveFaceTextureMappingFields"))
        {
            changed = editInt16Field(session, "Offset U", baseFace.textureDeltaU) || changed;
            changed = editInt16Field(session, "Offset V", baseFace.textureDeltaV) || changed;

            const auto [minU, maxU] = faceTextureCoordinateRange(baseFace.textureUs);
            const auto [minV, maxV] = faceTextureCoordinateRange(baseFace.textureVs);
            renderInspectorReadOnlyField("U Range", std::to_string(minU) + " .. " + std::to_string(maxU));
            renderInspectorReadOnlyField("V Range", std::to_string(minV) + " .. " + std::to_string(maxV));
            renderInspectorReadOnlyField(
                "Texture Size",
                std::to_string(textureWidth) + " x " + std::to_string(textureHeight));
            ImGui::EndTable();
        }

        const auto applyTextureMappingAction = [&session, &changed](auto action)
        {
            session.captureUndoSnapshot();
            action();
            changed = true;
        };

        if (ImGui::Button("Flip U", ImVec2(110.0f, 0.0f)))
        {
            applyTextureMappingAction([&baseFace]()
            {
                flipFaceTextureAxis(baseFace.textureUs);
            });
        }

        ImGui::SameLine();

        if (ImGui::Button("Flip V", ImVec2(110.0f, 0.0f)))
        {
            applyTextureMappingAction([&baseFace]()
            {
                flipFaceTextureAxis(baseFace.textureVs);
            });
        }

        ImGui::SameLine();

        if (ImGui::Button("Rotate UV 90", ImVec2(120.0f, 0.0f)))
        {
            applyTextureMappingAction([&baseFace, textureWidth, textureHeight]()
            {
                for (size_t index = 0; index < baseFace.textureUs.size() && index < baseFace.textureVs.size(); ++index)
                {
                    const int oldU = baseFace.textureUs[index];
                    const int oldV = baseFace.textureVs[index];
                    baseFace.textureUs[index] = clampToInt16(textureWidth - oldV);
                    baseFace.textureVs[index] = clampToInt16(oldU);
                }
            });
        }

        if (ImGui::Button("Fit Once", ImVec2(110.0f, 0.0f)))
        {
            applyTextureMappingAction([&baseFace, textureWidth, textureHeight]()
            {
                fitFaceTextureAxis(baseFace.textureUs, textureWidth);
                fitFaceTextureAxis(baseFace.textureVs, textureHeight);
                baseFace.textureDeltaU = 0;
                baseFace.textureDeltaV = 0;
            });
        }

        ImGui::SameLine();

        if (ImGui::Button("Reset Mapping", ImVec2(120.0f, 0.0f)))
        {
            applyTextureMappingAction([&outdoorGeometry, &baseFace, bmodelIndex]()
            {
                resetFaceTextureMappingFromGeometry(outdoorGeometry.bmodels[bmodelIndex].vertices, baseFace);
            });
        }

        ImGui::SameLine();

        if (ImGui::Button("Tile U x2", ImVec2(110.0f, 0.0f)))
        {
            applyTextureMappingAction([&baseFace]()
            {
                scaleFaceTextureAxis(baseFace.textureUs, 2.0f);
            });
        }

        ImGui::SameLine();

        if (ImGui::Button("Tile V x2", ImVec2(110.0f, 0.0f)))
        {
            applyTextureMappingAction([&baseFace]()
            {
                scaleFaceTextureAxis(baseFace.textureVs, 2.0f);
            });
        }

        if (ImGui::Button("Stretch U", ImVec2(110.0f, 0.0f)))
        {
            applyTextureMappingAction([&baseFace]()
            {
                scaleFaceTextureAxis(baseFace.textureUs, 0.5f);
            });
        }

        ImGui::SameLine();

        if (ImGui::Button("Stretch V", ImVec2(110.0f, 0.0f)))
        {
            applyTextureMappingAction([&baseFace]()
            {
                scaleFaceTextureAxis(baseFace.textureVs, 0.5f);
            });
        }

        ImGui::SameLine();

        if (ImGui::Button("Reset Offset", ImVec2(120.0f, 0.0f)))
        {
            applyTextureMappingAction([&baseFace]()
            {
                baseFace.textureDeltaU = 0;
                baseFace.textureDeltaV = 0;
            });
        }
    }

    if (changed)
    {
        if (baseFace.textureName.size() > 10)
        {
            baseFace.textureName.resize(10);
        }

        session.noteDocumentMutated({});
    }
}

void EditorMainWindow::renderEntityInspector(EditorSession &session, size_t entityIndex) const
{
    std::vector<Game::OutdoorSceneEntity> &entities = session.document().mutableOutdoorSceneData().entities;

    if (entityIndex >= entities.size())
    {
        ImGui::TextUnformatted("Selected entity index is out of range.");
        return;
    }

    Game::OutdoorSceneEntity &entity = entities[entityIndex];
    bool changed = false;

    if (beginInspectorSectionBlock("Overview"))
    {
        if (beginInspectorPropertyTable("EntityFields"))
        {
            const uint16_t originalDecorationListId = entity.entity.decorationListId;
            const bool decorationChanged = renderDecorationSelector(
                session,
                "Decoration",
                entity.entity.decorationListId,
                false);
            changed = decorationChanged || changed;

            if (decorationChanged)
            {
                if (const Game::DecorationEntry *pDecoration = session.decorationTable().get(entity.entity.decorationListId))
                {
                    entity.entity.name = pDecoration->internalName;
                }
                else if (entity.entity.decorationListId != originalDecorationListId)
                {
                    entity.entity.name.clear();
                }
            }

            renderInspectorReadOnlyField("Entity Index", std::to_string(entity.entityIndex));
            changed = editStringField(session, "Name", entity.entity.name, 128) || changed;
            renderInspectorReadOnlyField("Decoration List Id", std::to_string(entity.entity.decorationListId));
            renderInspectorReadOnlyField(
                "Resolved Hint",
                [&session, &entity]()
                {
                    const Game::DecorationEntry *pDecoration = session.decorationTable().get(entity.entity.decorationListId);
                    return pDecoration != nullptr && !pDecoration->hint.empty() ? pDecoration->hint : std::string("<none>");
                }());
            ImGui::EndTable();
        }
        endInspectorSectionBlock();
    }

    if (beginInspectorSectionBlock("Placement"))
    {
        if (beginInspectorPropertyTable("EntityPlacementFields"))
        {
            changed = editPositionField(session, "Position", entity.entity.x, entity.entity.y, entity.entity.z) || changed;
            changed = editIntField(
                session,
                "Facing",
                entity.entity.facing,
                std::numeric_limits<int>::min(),
                std::numeric_limits<int>::max()) || changed;
            ImGui::EndTable();
        }
        endInspectorSectionBlock();
    }

    if (beginInspectorSectionBlock("Behavior"))
    {
        if (beginInspectorPropertyTable("EntityBehaviorFields"))
        {
            changed = editUInt16Field(session, "AI Attributes", entity.entity.aiAttributes) || changed;
            changed = editUInt16Field(session, "Variable Primary", entity.entity.variablePrimary) || changed;
            changed = editUInt16Field(session, "Variable Secondary", entity.entity.variableSecondary) || changed;
            changed = editUInt16Field(session, "Special Trigger", entity.entity.specialTrigger) || changed;
            changed = editUInt16Field(session, "Initial Decoration Flag", entity.initialDecorationFlag) || changed;
            ImGui::EndTable();
        }
        endInspectorSectionBlock();
    }

    if (beginInspectorSectionBlock("Events"))
    {
        if (beginInspectorPropertyTable("EntityEventFields"))
        {
            changed = editMapEventField(session, "Event Primary", entity.entity.eventIdPrimary) || changed;
            renderResolvedMapEventField(session, "Primary Event Label", entity.entity.eventIdPrimary);
            changed = editMapEventField(session, "Event Secondary", entity.entity.eventIdSecondary) || changed;
            renderResolvedMapEventField(session, "Secondary Event Label", entity.entity.eventIdSecondary);
            ImGui::EndTable();
        }
        endInspectorSectionBlock();
    }

    if (changed)
    {
        session.setPendingEntityDecorationListId(entity.entity.decorationListId);
        session.noteDocumentMutated({});
    }
}

void EditorMainWindow::renderEntityPlacementInspector(EditorSession &session) const
{
    uint32_t selectedId = session.pendingEntityDecorationListId();

    ImGui::TextUnformatted("Entity Placement");
    ImGui::Separator();
    ImGui::TextWrapped("Choose a decoration, then click in the viewport to place the entity. The entity preview "
                       "follows the cursor while placement mode is active.");

    renderInspectorSectionHeader("Decoration");

    if (beginInspectorPropertyTable("EntityPlacementSelection"))
    {
        uint16_t pendingDecorationId = static_cast<uint16_t>(std::min<uint32_t>(selectedId, 65535));

        if (renderDecorationSelector(session, "Decoration", pendingDecorationId, true))
        {
            selectedId = pendingDecorationId;
            session.setPendingEntityDecorationListId(pendingDecorationId);
        }

        renderInspectorReadOnlyField("Pending Decoration Id", std::to_string(selectedId));

        const Game::DecorationEntry *pDecoration =
            session.decorationTable().get(static_cast<uint16_t>(std::min<uint32_t>(selectedId, 65535)));
        renderInspectorReadOnlyField("Sprite Id", pDecoration != nullptr ? std::to_string(pDecoration->spriteId) : "0");
        renderInspectorReadOnlyField(
            "Internal Name",
            pDecoration != nullptr && !pDecoration->internalName.empty() ? pDecoration->internalName : "(none)");
        renderInspectorReadOnlyField(
            "Hint",
            pDecoration != nullptr && !pDecoration->hint.empty() ? pDecoration->hint : "(none)");
        ImGui::EndTable();
    }
}

void EditorMainWindow::renderSpawnPlacementInspector(EditorSession &session) const
{
    Game::OutdoorSpawn &spawn = session.mutablePendingSpawn();
    const Game::MapStatsEntry *pMapEntry = session.currentMapStatsEntry();
    const Game::SpawnPreview preview = pMapEntry != nullptr
        ? Game::SpawnPreviewResolver::describe(
            *pMapEntry,
            &session.monsterTable(),
            spawn.typeId,
            spawn.index,
            spawn.attributes,
            spawn.group)
        : Game::SpawnPreview {};

    ImGui::TextUnformatted("Spawn Placement");
    ImGui::Separator();
    ImGui::TextWrapped("Configure the spawn defaults, then click in the viewport to place it. The full placed spawn "
                       "can still be edited afterward.");

    if (pMapEntry == nullptr)
    {
        ImGui::Spacing();
        ImGui::PushStyleColor(ImGuiCol_Text, colorFromRgb(0xD8B277));
        ImGui::TextUnformatted("Map stats entry is unavailable. Encounter labels may be incomplete.");
        ImGui::PopStyleColor();
    }

    if (beginInspectorSectionBlock("Overview"))
    {
        if (beginInspectorPropertyTable("SpawnPlacementOverview"))
        {
            editTransientSpawnTypeField(spawn);

            if (spawn.typeId == 3 && pMapEntry != nullptr)
            {
                editTransientActorSpawnEncounterField(*pMapEntry, spawn);
            }
            else if (spawn.typeId == 2)
            {
                editTransientSpawnTreasureLevelField(spawn);
            }
            else
            {
                editTransientUInt16Field("Index", spawn.index);
            }

            renderInspectorReadOnlyField("Type Label", preview.typeName.empty() ? "<unknown>" : preview.typeName);
            renderInspectorReadOnlyField("Summary", preview.summary.empty() ? "<unresolved>" : preview.summary);
            renderInspectorReadOnlyField("Detail", preview.detail.empty() ? "<none>" : preview.detail);
            ImGui::EndTable();
        }
        endInspectorSectionBlock();
    }

    if (beginInspectorSectionBlock("Defaults"))
    {
        if (beginInspectorPropertyTable("SpawnPlacementDefaults"))
        {
            editTransientUInt16Field("Radius", spawn.radius);
            editTransientUInt32Field("Group", spawn.group);
            editTransientUInt16Field("Attributes", spawn.attributes);
            ImGui::EndTable();
        }
        endInspectorSectionBlock();
    }
}

void EditorMainWindow::renderSpawnInspector(EditorSession &session, size_t spawnIndex) const
{
    std::vector<Game::OutdoorSceneSpawn> &spawns = session.document().mutableOutdoorSceneData().spawns;

    if (spawnIndex >= spawns.size())
    {
        ImGui::TextUnformatted("Selected spawn index is out of range.");
        return;
    }

    Game::OutdoorSceneSpawn &spawn = spawns[spawnIndex];
    const Game::MapStatsEntry *pMapEntry = session.currentMapStatsEntry();
    const Game::SpawnPreview preview = pMapEntry != nullptr
        ? Game::SpawnPreviewResolver::describe(
            *pMapEntry,
            &session.monsterTable(),
            spawn.spawn.typeId,
            spawn.spawn.index,
            spawn.spawn.attributes,
            spawn.spawn.group)
        : Game::SpawnPreview {};
    bool changed = false;

    if (pMapEntry == nullptr)
    {
        ImGui::TextUnformatted("Map stats entry is unavailable. Spawn semantics may be incomplete.");
    }

    if (beginInspectorSectionBlock("Overview"))
    {
        if (beginInspectorPropertyTable("SpawnIdentityFields"))
        {
            renderInspectorReadOnlyField("Spawn Index", std::to_string(spawn.spawnIndex));
            changed = editSpawnTypeField(session, spawn.spawn) || changed;

            if (spawn.spawn.typeId == 3 && pMapEntry != nullptr)
            {
                changed = editActorSpawnEncounterField(session, *pMapEntry, spawn.spawn) || changed;
            }
            else if (spawn.spawn.typeId == 2)
            {
                changed = editSpawnTreasureLevelField(session, spawn.spawn) || changed;
            }
            else
            {
                changed = editUInt16Field(session, "Index", spawn.spawn.index) || changed;
            }

            renderInspectorReadOnlyField("Type Label", preview.typeName.empty() ? "<unknown>" : preview.typeName);
            renderInspectorReadOnlyField("Summary", preview.summary.empty() ? "<unresolved>" : preview.summary);
            renderInspectorReadOnlyField("Detail", preview.detail.empty() ? "<none>" : preview.detail);
            ImGui::EndTable();
        }
        endInspectorSectionBlock();
    }

    if (beginInspectorSectionBlock("Placement"))
    {
        if (beginInspectorPropertyTable("SpawnPlacementFields"))
        {
            changed = editPositionField(session, "Position", spawn.spawn.x, spawn.spawn.y, spawn.spawn.z) || changed;
            changed = editUInt16Field(session, "Radius", spawn.spawn.radius) || changed;
            changed = editUInt32Field(session, "Group", spawn.spawn.group) || changed;
            ImGui::EndTable();
        }
        endInspectorSectionBlock();
    }

    if (beginInspectorSectionBlock("Behavior"))
    {
        if (beginInspectorPropertyTable("SpawnBehaviorFields"))
        {
            changed = editUInt16Field(session, "Attributes", spawn.spawn.attributes) || changed;
            ImGui::EndTable();
        }
        endInspectorSectionBlock();
    }

    if (beginInspectorSectionBlock("Overrides And Legacy", false))
    {
        if (beginInspectorPropertyTable("SpawnLegacyFields"))
        {
            changed = editUInt16Field(session, "Type Id Raw", spawn.spawn.typeId) || changed;
            changed = editUInt16Field(session, "Index Raw", spawn.spawn.index) || changed;
            renderInspectorReadOnlyField("Resolved Type", preview.typeName.empty() ? "<unknown>" : preview.typeName);
            renderInspectorReadOnlyField("Resolved Summary", preview.summary.empty() ? "<unresolved>" : preview.summary);
            ImGui::EndTable();
        }
        endInspectorSectionBlock();
    }

    if (changed)
    {
        session.noteDocumentMutated({});
    }
}

void EditorMainWindow::renderActorPlacementInspector(EditorSession &session) const
{
    Game::MapDeltaActor &actor = session.mutablePendingActor();
    const Game::MonsterTable &monsterTable = session.monsterTable();
    const std::string displayLabel = actorDisplayLabel(&monsterTable, actor, 0);
    const std::string templateLabel = actorMonsterTemplateLabel(&monsterTable, actor);
    const std::string npcIdLabel = actor.npcId == 0 ? "<none>" : std::to_string(actor.npcId);

    ImGui::TextUnformatted("Actor Placement");
    ImGui::Separator();
    ImGui::TextWrapped("Configure the actor defaults, then click in the viewport to place it. The full placed actor "
                       "can still be edited afterward.");

    if (beginInspectorSectionBlock("Overview"))
    {
        if (beginInspectorPropertyTable("ActorPlacementOverview"))
        {
            renderMonsterTemplateSelector(session, "Monster Template", actor, true);
            editTransientInt16Field("NPC Id", actor.npcId);
            editTransientIntField(
                "Unique Name Index",
                actor.uniqueNameIndex,
                std::numeric_limits<int32_t>::min(),
                std::numeric_limits<int32_t>::max());
            editTransientStringField("Raw Name Override", actor.name, 128);
            renderInspectorReadOnlyField("Resolved Name", displayLabel);
            renderInspectorReadOnlyField("Template", templateLabel.empty() ? "<unresolved>" : templateLabel);
            renderInspectorReadOnlyField("Monster Info Id", std::to_string(actor.monsterInfoId));
            renderInspectorReadOnlyField("Monster Id", std::to_string(actor.monsterId));
            renderInspectorReadOnlyField("NPC Link", npcIdLabel);
            ImGui::EndTable();
        }
        endInspectorSectionBlock();
    }

    if (beginInspectorSectionBlock("Defaults"))
    {
        if (beginInspectorPropertyTable("ActorPlacementDefaults"))
        {
            int hostilityType = actor.hostilityType;

            if (editTransientIntField("Hostility Type", hostilityType, 0, 255))
            {
                actor.hostilityType = static_cast<uint8_t>(hostilityType);
            }

            editTransientUInt16Field("Radius", actor.radius);
            editTransientUInt16Field("Height", actor.height);
            editTransientUInt16Field("Move Speed", actor.moveSpeed);
            editTransientUInt32Field("Group", actor.group);
            editTransientUInt32Field("Ally", actor.ally);
            renderInspectorReadOnlyField("Hostility Label", hostilityTypeLabel(actor.hostilityType));
            ImGui::EndTable();
        }
        endInspectorSectionBlock();
    }
}

void EditorMainWindow::renderActorInspector(EditorSession &session, size_t actorIndex) const
{
    std::vector<Game::MapDeltaActor> &actors =
        session.document().kind() == EditorDocument::Kind::Indoor
        ? session.document().mutableIndoorSceneData().initialState.actors
        : session.document().mutableOutdoorSceneData().initialState.actors;

    if (actorIndex >= actors.size())
    {
        ImGui::TextUnformatted("Selected actor index is out of range.");
        return;
    }

    Game::MapDeltaActor &actor = actors[actorIndex];
    const int originalX = actor.x;
    const int originalY = actor.y;
    const int originalZ = actor.z;
    const Game::MonsterTable &monsterTable = session.monsterTable();
    const std::string displayLabel = actorDisplayLabel(&monsterTable, actor, actorIndex);
    const std::string templateLabel = actorMonsterTemplateLabel(&monsterTable, actor);
    const std::string npcIdLabel = actor.npcId == 0 ? "<none>" : std::to_string(actor.npcId);
    bool changed = false;

    if (beginInspectorSectionBlock("Overview"))
    {
        if (beginInspectorPropertyTable("ActorIdentityFields"))
        {
            renderInspectorReadOnlyField("Actor Index", std::to_string(actorIndex));
            changed = renderMonsterTemplateSelector(session, "Monster Template", actor, false) || changed;
            changed = editInt16Field(session, "NPC Id", actor.npcId) || changed;
            changed = editIntField(
                session,
                "Unique Name Index",
                actor.uniqueNameIndex,
                std::numeric_limits<int32_t>::min(),
                std::numeric_limits<int32_t>::max()) || changed;
            changed = editStringField(session, "Raw Name Override", actor.name, 128) || changed;
            renderInspectorReadOnlyField("Resolved Name", displayLabel);
            renderInspectorReadOnlyField("Template", templateLabel.empty() ? "<unresolved>" : templateLabel.c_str());
            renderInspectorReadOnlyField("Monster Info Id", std::to_string(actor.monsterInfoId));
            renderInspectorReadOnlyField("Monster Id", std::to_string(actor.monsterId));
            renderInspectorReadOnlyField("NPC Link", npcIdLabel);
            ImGui::EndTable();
        }
        endInspectorSectionBlock();
    }

    if (beginInspectorSectionBlock("Placement"))
    {
        if (beginInspectorPropertyTable("ActorPlacementFields"))
        {
            changed = editPositionField(session, "Position", actor.x, actor.y, actor.z) || changed;
            changed = editUInt16Field(session, "Radius", actor.radius) || changed;
            changed = editUInt16Field(session, "Height", actor.height) || changed;
            ImGui::EndTable();
        }
        endInspectorSectionBlock();
    }

    if (beginInspectorSectionBlock("Behavior"))
    {
        if (beginInspectorPropertyTable("ActorBehaviorFields"))
        {
            changed = editActorHostilityTypeField(session, actor.hostilityType) || changed;
            changed = editUInt32Field(session, "Group", actor.group) || changed;
            changed = editUInt32Field(session, "Ally", actor.ally) || changed;
            renderInspectorReadOnlyField("Hostility Label", hostilityTypeLabel(actor.hostilityType));
            ImGui::EndTable();
        }
        endInspectorSectionBlock();
    }

    if (beginInspectorSectionBlock("Visibility And Faction"))
    {
        if (beginInspectorPropertyTable("ActorFlags"))
        {
            changed = editBitCheckbox(session, "Show On Map", actor.attributes, MonsterBitShowOnMap) || changed;
            changed = editBitCheckbox(session, "Invisible", actor.attributes, MonsterBitInvisible) || changed;
            changed = editBitCheckbox(session, "No Flee", actor.attributes, MonsterBitNoFlee) || changed;
            changed = editBitCheckbox(session, "Hostile", actor.attributes, MonsterBitHostile) || changed;
            changed = editBitCheckbox(session, "On Alert Map", actor.attributes, MonsterBitOnAlertMap) || changed;
            changed = editBitCheckbox(session, "Treasure Generated", actor.attributes, MonsterBitTreasureGenerated)
                || changed;
            changed = editBitCheckbox(session, "Show As Hostile", actor.attributes, MonsterBitShowAsHostile)
                || changed;
            ImGui::EndTable();
        }
        endInspectorSectionBlock();
    }

    if (beginInspectorSectionBlock("Overrides And Legacy", false))
    {
        if (beginInspectorPropertyTable("ActorLegacyFields"))
        {
            changed = editInt16Field(session, "Monster Info Id Raw", actor.monsterInfoId) || changed;
            changed = editInt16Field(session, "Monster Id Raw", actor.monsterId) || changed;
            changed = editInt16Field(session, "HP Override", actor.hp) || changed;
            changed = editUInt16Field(session, "Move Speed Override", actor.moveSpeed) || changed;
            changed = editUInt16Array4Field(session, "Sprite Id Overrides", actor.spriteIds) || changed;
            changed = editInt16Field(session, "Sector Id", actor.sectorId) || changed;
            changed = editUInt16Field(session, "Current Animation", actor.currentActionAnimation) || changed;
            changed = editUInt32Field(session, "Attributes Raw", actor.attributes) || changed;
            renderInspectorReadOnlyField("Display Label", displayLabel);
            renderInspectorReadOnlyField("NPC Link", npcIdLabel);
            renderInspectorReadOnlyField("Hostility Label", hostilityTypeLabel(actor.hostilityType));
            ImGui::EndTable();
        }
        endInspectorSectionBlock();
    }

    if (changed)
    {
        if (session.document().kind() == EditorDocument::Kind::Indoor)
        {
            const int snappedZ =
                snapIndoorActorZToFloor(session.document().indoorGeometry(), actor.x, actor.y, actor.z);

            if (snappedZ != actor.z)
            {
                actor.z = snappedZ;
                changed = true;
            }

            if (actor.x != originalX || actor.y != originalY || actor.z != originalZ)
            {
                Game::IndoorMapData &indoorGeometry = session.document().mutableIndoorGeometry();
                const std::optional<int16_t> sectorId = Game::findIndoorSectorForPoint(
                    indoorGeometry,
                    indoorGeometry.vertices,
                    {
                        static_cast<float>(actor.x),
                        static_cast<float>(actor.y),
                        static_cast<float>(actor.z)
                    });
                actor.sectorId = sectorId.value_or(-1);
            }
        }

        session.noteDocumentMutated({});
    }
}

void EditorMainWindow::renderSpriteObjectPlacementInspector(EditorSession &session) const
{
    uint32_t selectedItemId = session.pendingSpriteObjectItemId();

    ImGui::TextUnformatted("Item Placement");
    ImGui::Separator();
    ImGui::TextWrapped("Choose a contained item, then click in the viewport to place it. The sprite preview follows "
                       "the cursor while placement mode is active.");

    renderInspectorSectionHeader("Contained Item");

    if (beginInspectorPropertyTable("SpriteObjectPlacementSelection"))
    {
        editTransientSpriteObjectContainedItemField(session, selectedItemId);
        renderInspectorReadOnlyField("Pending Item Id", std::to_string(selectedItemId));

        const Game::ObjectEntry *pObjectEntry =
            session.objectTable().get(session.pendingSpriteObjectDescriptionId());
        renderInspectorReadOnlyField(
            "Visual Object Descriptor",
            pObjectEntry != nullptr && !pObjectEntry->internalName.empty()
                ? pObjectEntry->internalName + " (#" + std::to_string(session.pendingSpriteObjectDescriptionId()) + ")"
                : "Object #" + std::to_string(session.pendingSpriteObjectDescriptionId()));
        renderInspectorReadOnlyField("Sprite Id", pObjectEntry != nullptr ? std::to_string(pObjectEntry->spriteId) : "0");
        renderInspectorReadOnlyField(
            "Sprite Name",
            pObjectEntry != nullptr && !pObjectEntry->spriteName.empty() ? pObjectEntry->spriteName : "(none)");
        renderInspectorReadOnlyField(
            "Flags",
            pObjectEntry != nullptr ? std::to_string(pObjectEntry->flags) : "0");
        ImGui::EndTable();
    }
}

void EditorMainWindow::renderSpriteObjectInspector(EditorSession &session, size_t spriteObjectIndex) const
{
    std::vector<Game::MapDeltaSpriteObject> &spriteObjects =
        session.document().kind() == EditorDocument::Kind::Indoor
        ? session.document().mutableIndoorSceneData().initialState.spriteObjects
        : session.document().mutableOutdoorSceneData().initialState.spriteObjects;

    if (spriteObjectIndex >= spriteObjects.size())
    {
        ImGui::TextUnformatted("Selected sprite object index is out of range.");
        return;
    }

    Game::MapDeltaSpriteObject &spriteObject = spriteObjects[spriteObjectIndex];
    bool changed = false;

    if (beginInspectorSectionBlock("Overview"))
    {
        if (beginInspectorPropertyTable("SpriteObjectIdentityFields"))
        {
            changed = editSpriteObjectContainedItemField(session, spriteObject) || changed;

            renderInspectorReadOnlyField(
                "Display Name",
                spriteObjectDisplayLabel(session, spriteObject, spriteObjectIndex));
            renderInspectorReadOnlyField(
                "Contained Item Id",
                std::to_string(Game::spriteObjectContainedItemId(spriteObject.rawContainingItem)));
            const uint16_t resolvedObjectDescriptionId =
                session.resolvedSpriteObjectObjectDescriptionId(spriteObject);
            const Game::ObjectEntry *pObjectEntry = session.objectTable().get(resolvedObjectDescriptionId);
            renderInspectorReadOnlyField(
                "Resolved Visual Descriptor",
                pObjectEntry != nullptr && !pObjectEntry->internalName.empty()
                    ? pObjectEntry->internalName + " (#" + std::to_string(resolvedObjectDescriptionId) + ")"
                    : "Object #" + std::to_string(resolvedObjectDescriptionId));
            changed = editUInt16Field(session, "Yaw Angle", spriteObject.yawAngle) || changed;
            changed = editUInt16Field(session, "Sound Id", spriteObject.soundId) || changed;
            renderInspectorReadOnlyField("Sprite Id", std::to_string(spriteObject.spriteId));
            ImGui::EndTable();
        }
        endInspectorSectionBlock();
    }

    if (beginInspectorSectionBlock("Placement"))
    {
        if (beginInspectorPropertyTable("SpriteObjectPlacementFields"))
        {
            changed = editPositionField(session, "Position", spriteObject.x, spriteObject.y, spriteObject.z) || changed;
            changed = editPositionField(
                session,
                "Initial Position",
                spriteObject.initialX,
                spriteObject.initialY,
                spriteObject.initialZ) || changed;
            ImGui::EndTable();
        }
        endInspectorSectionBlock();
    }

    if (beginInspectorSectionBlock("Motion And Lifetime"))
    {
        if (beginInspectorPropertyTable("SpriteObjectMotionFields"))
        {
            changed = editInt16PositionField(
                session,
                "Velocity",
                spriteObject.velocityX,
                spriteObject.velocityY,
                spriteObject.velocityZ) || changed;
            changed = editUInt16Field(session, "Time Since Created", spriteObject.timeSinceCreated) || changed;
            changed = editInt16Field(session, "Temporary Lifetime", spriteObject.temporaryLifetime) || changed;
            changed = editInt16Field(session, "Glow Radius Multiplier", spriteObject.glowRadiusMultiplier) || changed;
            ImGui::EndTable();
        }
        endInspectorSectionBlock();
    }

    if (beginInspectorSectionBlock("Visibility And Object Flags"))
    {
        if (beginInspectorPropertyTable("SpriteObjectFlags"))
        {
            changed = editBitCheckbox(session, "Visible", spriteObject.attributes, ObjectBitVisible) || changed;
            changed = editBitCheckbox(session, "Temporary", spriteObject.attributes, ObjectBitTemporary) || changed;
            changed = editBitCheckbox(session, "Halt Turn-Based", spriteObject.attributes, ObjectBitHaltTurnBased)
                || changed;
            changed = editBitCheckbox(session, "Dropped By Player", spriteObject.attributes, ObjectBitDroppedByPlayer)
                || changed;
            changed = editBitCheckbox(session, "Ignore Range", spriteObject.attributes, ObjectBitIgnoreRange)
                || changed;
            changed = editBitCheckbox(session, "No Z-Buffer", spriteObject.attributes, ObjectBitNoZBuffer)
                || changed;
            changed = editBitCheckbox(session, "Skip A Frame", spriteObject.attributes, ObjectBitSkipAFrame)
                || changed;
            changed = editBitCheckbox(session, "Attach To Head", spriteObject.attributes, ObjectBitAttachToHead)
                || changed;
            changed = editBitCheckbox(session, "Missile", spriteObject.attributes, ObjectBitMissile) || changed;
            changed = editBitCheckbox(session, "Removed", spriteObject.attributes, ObjectBitRemoved) || changed;
            ImGui::EndTable();
        }
        endInspectorSectionBlock();
    }

    if (beginInspectorSectionBlock("Spell And Ownership"))
    {
        if (beginInspectorPropertyTable("SpriteObjectPayloadFields"))
        {
            changed = editIntField(
                session,
                "Spell Id",
                spriteObject.spellId,
                std::numeric_limits<int32_t>::min(),
                std::numeric_limits<int32_t>::max()) || changed;
            changed = editIntField(
                session,
                "Spell Level",
                spriteObject.spellLevel,
                std::numeric_limits<int32_t>::min(),
                std::numeric_limits<int32_t>::max()) || changed;
            changed = editIntField(
                session,
                "Spell Skill",
                spriteObject.spellSkill,
                std::numeric_limits<int32_t>::min(),
                std::numeric_limits<int32_t>::max()) || changed;
            changed = editIntField(
                session,
                "Field54",
                spriteObject.field54,
                std::numeric_limits<int32_t>::min(),
                std::numeric_limits<int32_t>::max()) || changed;
            changed = editIntField(
                session,
                "Spell Caster PID",
                spriteObject.spellCasterPid,
                std::numeric_limits<int32_t>::min(),
                std::numeric_limits<int32_t>::max()) || changed;
            changed = editIntField(
                session,
                "Spell Target PID",
                spriteObject.spellTargetPid,
                std::numeric_limits<int32_t>::min(),
                std::numeric_limits<int32_t>::max()) || changed;
            renderInspectorReadOnlyField("Lod Distance", std::to_string(static_cast<int>(spriteObject.lodDistance)));
            renderInspectorReadOnlyField(
                "Spell Caster Ability",
                std::to_string(static_cast<int>(spriteObject.spellCasterAbility)));
            ImGui::EndTable();
        }
        endInspectorSectionBlock();
    }

    if (beginInspectorSectionBlock("Overrides And Legacy", false))
    {
        if (beginInspectorPropertyTable("SpriteObjectLegacyPayload"))
        {
            const uint16_t originalObjectDescriptionId = spriteObject.objectDescriptionId;
            const bool objectDescriptionChanged = renderObjectSelector(
                session,
                "Visual Object Descriptor Raw",
                spriteObject.objectDescriptionId,
                false);
            changed = objectDescriptionChanged || changed;

            if (objectDescriptionChanged || spriteObject.objectDescriptionId != originalObjectDescriptionId)
            {
                applySpriteObjectVisualDescriptor(session, spriteObject);
            }

            changed = editUInt16Field(session, "Sprite Id Raw", spriteObject.spriteId) || changed;
            changed = editInt16Field(session, "Sector Id", spriteObject.sectorId) || changed;
            changed = editUInt16Field(session, "Attributes Raw", spriteObject.attributes) || changed;
            renderInspectorReadOnlyField(
                "Contained Item Raw",
                std::to_string(Game::spriteObjectContainedItemId(spriteObject.rawContainingItem)));
            renderInspectorReadOnlyField("Containing Item Bytes", std::to_string(spriteObject.rawContainingItem.size()));
            ImGui::EndTable();
        }
        endInspectorSectionBlock();
    }

    if (changed)
    {
        session.setPendingSpriteObjectItemId(Game::spriteObjectContainedItemId(spriteObject.rawContainingItem));
        session.setPendingSpriteObjectDescriptionId(spriteObject.objectDescriptionId);
        session.noteDocumentMutated({});
    }
}

void EditorMainWindow::renderChestInspector(EditorSession &session, size_t chestIndex) const
{
    std::vector<Game::MapDeltaChest> &chests =
        session.document().kind() == EditorDocument::Kind::Indoor
        ? session.document().mutableIndoorSceneData().initialState.chests
        : session.document().mutableOutdoorSceneData().initialState.chests;
    const bool showLinkedOpeners = session.document().kind() == EditorDocument::Kind::Outdoor;

    if (chestIndex >= chests.size())
    {
        ImGui::TextUnformatted("Selected chest index is out of range.");
        return;
    }

    Game::MapDeltaChest &chest = chests[chestIndex];
    const Game::ChestEntry *pChestEntry = session.chestTable().get(chest.chestTypeId);
    size_t occupiedSlots = 0;
    bool changed = false;

    for (int16_t itemIndex : chest.inventoryMatrix)
    {
        if (itemIndex > 0)
        {
            ++occupiedSlots;
        }
    }

    if (beginInspectorSectionBlock("Overview"))
    {
        if (beginInspectorPropertyTable("ChestIdentity"))
        {
            changed = editChestPictureField(session, chest.chestTypeId) || changed;
            renderInspectorReadOnlyField(
                "Chest Type Name",
                pChestEntry != nullptr && !pChestEntry->name.empty() ? pChestEntry->name : "<unknown>");
            renderInspectorReadOnlyField("Chest Type Id", std::to_string(chest.chestTypeId));
            renderInspectorReadOnlyField("Occupied Inventory Slots", std::to_string(occupiedSlots));
            renderInspectorReadOnlyField("Inventory Cells", std::to_string(chest.inventoryMatrix.size()));
            ImGui::EndTable();
        }
        endInspectorSectionBlock();
    }

    if (beginInspectorSectionBlock("Flags"))
    {
        if (beginInspectorPropertyTable("ChestFlags"))
        {
            changed = editBitCheckbox(session, "Trapped", chest.flags, ChestBitTrapped) || changed;
            changed = editBitCheckbox(session, "Items Placed", chest.flags, ChestBitItemsPlaced) || changed;
            changed = editBitCheckbox(session, "Identified", chest.flags, ChestBitIdentified) || changed;
            ImGui::EndTable();
        }
        endInspectorSectionBlock();
    }

    if (beginInspectorSectionBlock("Contents", false))
    {
        const std::vector<EditorChestContentRecord> contentRecords = session.decodeChestContents(chestIndex);
        size_t fixedRecordCount = 0;
        size_t randomRecordCount = 0;

        for (const EditorChestContentRecord &record : contentRecords)
        {
            if (record.rawItemId > 0)
            {
                ++fixedRecordCount;
            }
            else if (record.rawItemId < 0)
            {
                ++randomRecordCount;
            }
        }

        ImGui::Text("Decoded Records: %zu", contentRecords.size());
        ImGui::Text("Fixed: %zu", fixedRecordCount);
        ImGui::SameLine();
        ImGui::Text("Random: %zu", randomRecordCount);

        if (ImGui::Button("Add Fixed Item"))
        {
            const std::optional<size_t> recordIndex = findFirstEmptyChestRecord(chest);

            if (recordIndex)
            {
                session.captureUndoSnapshot();
                clearChestRecord(chest, *recordIndex);
                writeChestRecordId(chest, *recordIndex, 1);
                changed = true;
            }
            else
            {
                session.logError("Chest has no free item records.");
            }
        }

        ImGui::SameLine();

        if (ImGui::BeginCombo("Add Random Treasure", "Select Level"))
        {
            for (int treasureLevel = 1; treasureLevel <= 7; ++treasureLevel)
            {
                const std::string levelLabel = "Level " + std::to_string(treasureLevel);

                if (ImGui::Selectable(levelLabel.c_str()))
                {
                    const std::optional<size_t> recordIndex = findFirstEmptyChestRecord(chest);

                    if (recordIndex)
                    {
                        session.captureUndoSnapshot();
                        clearChestRecord(chest, *recordIndex);
                        writeChestRecordId(chest, *recordIndex, -treasureLevel);
                        changed = true;
                    }
                    else
                    {
                        session.logError("Chest has no free item records.");
                    }
                }
            }

            ImGui::EndCombo();
        }

        if (contentRecords.empty())
        {
            ImGui::TextUnformatted("No non-empty chest records.");
        }
        else
        {
            for (const EditorChestContentRecord &record : contentRecords)
            {
                ImGui::PushID(static_cast<int>(record.recordIndex));
                const std::string headerLabel =
                    "Record " + std::to_string(record.recordIndex) + " - " + record.summary;

                if (ImGui::TreeNodeEx(headerLabel.c_str(), ImGuiTreeNodeFlags_DefaultOpen))
                {
                    int recordMode = 2;

                    if (record.rawItemId > 0)
                    {
                        recordMode = 0;
                    }
                    else if (record.rawItemId >= -7)
                    {
                        recordMode = 1;
                    }

                    if (beginInspectorPropertyTable("ChestRecordEditor"))
                    {
                        renderInspectorReadOnlyField("Anchor", record.anchor);

                        beginInspectorFieldRow("Mode");
                        static const char *Modes[] = {"Fixed Item", "Random Treasure", "Legacy Raw"};

                        if (ImGui::Combo("##ChestRecordMode", &recordMode, Modes, IM_ARRAYSIZE(Modes)))
                        {
                            session.captureUndoSnapshot();

                            if (recordMode == 0)
                            {
                                writeChestRecordId(chest, record.recordIndex, 1);
                            }
                            else if (recordMode == 1)
                            {
                                writeChestRecordId(chest, record.recordIndex, -1);
                            }

                            changed = true;
                        }

                        int rawValue = record.rawItemId;

                        if (recordMode == 0)
                        {
                            changed = editFixedItemSelectorField(session, "Item", rawValue) || changed;

                            if (rawValue != record.rawItemId)
                            {
                                writeChestRecordId(chest, record.recordIndex, rawValue);
                            }

                            renderInspectorReadOnlyField("Item Id", std::to_string(rawValue));
                            renderInspectorReadOnlyField("Item Name", session.itemDisplayName(rawValue));
                        }
                        else if (recordMode == 1)
                        {
                            int treasureLevel = std::clamp(-record.rawItemId, 1, 7);
                            beginInspectorFieldRow("Treasure Level");

                            if (ImGui::SliderInt("##ChestRandomLevel", &treasureLevel, 1, 7))
                            {
                                session.captureUndoSnapshot();
                                writeChestRecordId(chest, record.recordIndex, -treasureLevel);
                                changed = true;
                            }
                        }
                        else
                        {
                            beginInspectorFieldRow("Raw Item Id");

                            if (ImGui::InputInt("##ChestLegacyRawId", &rawValue))
                            {
                                if (rawValue != record.rawItemId)
                                {
                                    session.captureUndoSnapshot();
                                    writeChestRecordId(chest, record.recordIndex, rawValue);
                                    changed = true;
                                }
                            }
                        }

                        ImGui::EndTable();
                    }

                    if (ImGui::Button("Clear Record"))
                    {
                        session.captureUndoSnapshot();
                        clearChestRecord(chest, record.recordIndex);
                        changed = true;
                    }

                    ImGui::TreePop();
                }

                ImGui::PopID();
            }
        }
        endInspectorSectionBlock();
    }

    if (showLinkedOpeners && beginInspectorSectionBlock("Linked Openers", false))
    {
        const std::vector<EditorChestLink> chestLinks = session.findChestLinks(chestIndex);

        if (chestLinks.empty())
        {
            ImGui::TextUnformatted("No linked entity or face opener found.");
        }
        else
        {
            for (const EditorChestLink &link : chestLinks)
            {
                if (link.kind == EditorChestLink::Kind::Entity)
                {
                    std::string buttonLabel = "Select Entity " + std::to_string(link.entityIndex)
                        + "##ChestLinkEntity" + std::to_string(chestIndex) + "_" + std::to_string(link.entityIndex);

                    if (ImGui::Button(buttonLabel.c_str()))
                    {
                        session.select(EditorSelectionKind::Entity, link.entityIndex);
                    }

                    ImGui::SameLine();
                    ImGui::Text("event %u", link.eventId);
                }
                else
                {
                    const size_t flatIndex = flattenedOutdoorFaceIndex(
                        session.document().outdoorGeometry(),
                        link.bmodelIndex,
                        link.faceIndex);
                    std::string buttonLabel = "Select Face "
                        + std::to_string(link.bmodelIndex)
                        + ":"
                        + std::to_string(link.faceIndex)
                        + "##ChestLinkFace"
                        + std::to_string(chestIndex)
                        + "_"
                        + std::to_string(link.bmodelIndex)
                        + "_"
                        + std::to_string(link.faceIndex);

                    if (ImGui::Button(buttonLabel.c_str()))
                    {
                        session.select(EditorSelectionKind::InteractiveFace, flatIndex);
                    }

                    ImGui::SameLine();
                    ImGui::Text("event %u", link.eventId);
                }
            }
        }
        endInspectorSectionBlock();
    }

    if (beginInspectorSectionBlock("Layout And Matrix", false))
    {
        if (ImGui::BeginTable("ChestInventoryMatrix", 14, ImGuiTableFlags_Borders | ImGuiTableFlags_SizingFixedFit))
        {
            for (size_t slotIndex = 0; slotIndex < chest.inventoryMatrix.size(); ++slotIndex)
            {
                if ((slotIndex % 14) == 0)
                {
                    ImGui::TableNextRow();
                }

                ImGui::TableSetColumnIndex(static_cast<int>(slotIndex % 14));
                ImGui::Text("%d", chest.inventoryMatrix[slotIndex]);
            }

            ImGui::EndTable();
        }
        endInspectorSectionBlock();
    }

    if (beginInspectorSectionBlock("Overrides And Legacy", false))
    {
        if (beginInspectorPropertyTable("ChestLegacyFields"))
        {
            changed = editUInt16Field(session, "Chest Type Id Raw", chest.chestTypeId) || changed;
            changed = editUInt16Field(session, "Flags Raw", chest.flags) || changed;
            renderInspectorReadOnlyField("Raw Item Bytes", std::to_string(chest.rawItems.size()));
            renderInspectorReadOnlyField("Raw Record Count", std::to_string(chest.rawItems.size() / 36));
            ImGui::EndTable();
        }
        endInspectorSectionBlock();
    }

    if (changed)
    {
        session.noteDocumentMutated({});
    }
}

void EditorMainWindow::renderIndoorEntityInspector(EditorSession &session, size_t entityIndex) const
{
    Game::IndoorMapData &indoorGeometry = session.document().mutableIndoorGeometry();

    if (entityIndex >= indoorGeometry.entities.size())
    {
        ImGui::TextUnformatted("Selected entity index is out of range.");
        return;
    }

    Game::IndoorEntity &entity = indoorGeometry.entities[entityIndex];
    const int originalX = entity.x;
    const int originalY = entity.y;
    const int originalZ = entity.z;
    bool changed = false;

    if (beginInspectorSectionBlock("Overview"))
    {
        if (beginInspectorPropertyTable("IndoorEntityOverviewFields"))
        {
            const uint16_t originalDecorationListId = entity.decorationListId;
            const bool decorationChanged = renderDecorationSelector(
                session,
                "Decoration",
                entity.decorationListId,
                false);
            changed = decorationChanged || changed;

            if (decorationChanged)
            {
                if (const Game::DecorationEntry *pDecoration = session.decorationTable().get(entity.decorationListId))
                {
                    entity.name = pDecoration->internalName;
                }
                else if (entity.decorationListId != originalDecorationListId)
                {
                    entity.name.clear();
                }
            }

            renderInspectorReadOnlyField("Entity Index", std::to_string(entityIndex));
            changed = editStringField(session, "Name", entity.name, 128) || changed;
            renderInspectorReadOnlyField("Decoration List Id", std::to_string(entity.decorationListId));
            renderInspectorReadOnlyField(
                "Resolved Hint",
                [&session, &entity]()
                {
                    const Game::DecorationEntry *pDecoration = session.decorationTable().get(entity.decorationListId);
                    return pDecoration != nullptr && !pDecoration->hint.empty()
                        ? pDecoration->hint
                        : std::string("<none>");
                }());

            Game::IndoorFaceGeometryCache geometryCache(indoorGeometry.faces.size());
            const std::optional<uint16_t> roomId =
                findIndoorRoomIdForPoint(indoorGeometry, entity.x, entity.y, entity.z, geometryCache);
            renderInspectorReadOnlyField("Room", roomId ? std::to_string(*roomId) : std::string("<unknown>"));
            ImGui::EndTable();
        }
        endInspectorSectionBlock();
    }

    if (beginInspectorSectionBlock("Placement"))
    {
        if (beginInspectorPropertyTable("IndoorEntityPlacementFields"))
        {
            changed = editPositionField(session, "Position", entity.x, entity.y, entity.z) || changed;
            changed = editIntField(
                session,
                "Facing",
                entity.facing,
                std::numeric_limits<int>::min(),
                std::numeric_limits<int>::max()) || changed;
            ImGui::EndTable();
        }
        endInspectorSectionBlock();
    }

    if (beginInspectorSectionBlock("Behavior"))
    {
        if (beginInspectorPropertyTable("IndoorEntityBehaviorFields"))
        {
            changed = editUInt16Field(session, "AI Attributes", entity.aiAttributes) || changed;
            changed = editUInt16Field(session, "Variable Primary", entity.variablePrimary) || changed;
            changed = editUInt16Field(session, "Variable Secondary", entity.variableSecondary) || changed;
            changed = editUInt16Field(session, "Special Trigger", entity.specialTrigger) || changed;
            ImGui::EndTable();
        }
        endInspectorSectionBlock();
    }

    if (beginInspectorSectionBlock("Events"))
    {
        if (beginInspectorPropertyTable("IndoorEntityEventFields"))
        {
            changed = editMapEventField(session, "Event Primary", entity.eventIdPrimary) || changed;
            renderResolvedMapEventField(session, "Primary Event Label", entity.eventIdPrimary);
            changed = editMapEventField(session, "Event Secondary", entity.eventIdSecondary) || changed;
            renderResolvedMapEventField(session, "Secondary Event Label", entity.eventIdSecondary);
            ImGui::EndTable();
        }
        endInspectorSectionBlock();
    }

    if (changed)
    {
        if (entity.x != originalX || entity.y != originalY || entity.z != originalZ)
        {
            assignIndoorEntityToSector(indoorGeometry, entityIndex);
        }

        session.setPendingEntityDecorationListId(entity.decorationListId);
        indoorGeometry.spriteCount = indoorGeometry.entities.size();
        session.noteDocumentMutated({});
    }
}

void EditorMainWindow::renderIndoorSpawnInspector(EditorSession &session, size_t spawnIndex) const
{
    Game::IndoorMapData &indoorGeometry = session.document().mutableIndoorGeometry();

    if (spawnIndex >= indoorGeometry.spawns.size())
    {
        ImGui::TextUnformatted("Selected spawn index is out of range.");
        return;
    }

    Game::IndoorSpawn &spawn = indoorGeometry.spawns[spawnIndex];
    Game::OutdoorSpawn editableSpawn = {};
    editableSpawn.x = spawn.x;
    editableSpawn.y = spawn.y;
    editableSpawn.z = spawn.z;
    editableSpawn.radius = spawn.radius;
    editableSpawn.typeId = spawn.typeId;
    editableSpawn.index = spawn.index;
    editableSpawn.attributes = spawn.attributes;
    editableSpawn.group = spawn.group;

    const Game::MapStatsEntry *pMapEntry = session.currentMapStatsEntry();
    const Game::SpawnPreview preview = pMapEntry != nullptr
        ? Game::SpawnPreviewResolver::describe(
            *pMapEntry,
            &session.monsterTable(),
            spawn.typeId,
            spawn.index,
            spawn.attributes,
            spawn.group)
        : Game::SpawnPreview {};
    bool changed = false;

    if (pMapEntry == nullptr)
    {
        ImGui::TextUnformatted("Map stats entry is unavailable. Spawn semantics may be incomplete.");
    }

    const auto applyEditableSpawn =
        [&spawn, &editableSpawn]()
    {
        spawn.x = editableSpawn.x;
        spawn.y = editableSpawn.y;
        spawn.z = editableSpawn.z;
        spawn.radius = editableSpawn.radius;
        spawn.typeId = editableSpawn.typeId;
        spawn.index = editableSpawn.index;
        spawn.attributes = editableSpawn.attributes;
        spawn.group = editableSpawn.group;
    };

    if (beginInspectorSectionBlock("Overview"))
    {
        if (beginInspectorPropertyTable("IndoorSpawnIdentityFields"))
        {
            renderInspectorReadOnlyField("Spawn Index", std::to_string(spawnIndex));
            changed = editSpawnTypeField(session, editableSpawn) || changed;

            if (editableSpawn.typeId == 3 && pMapEntry != nullptr)
            {
                changed = editActorSpawnEncounterField(session, *pMapEntry, editableSpawn) || changed;
            }
            else if (editableSpawn.typeId == 2)
            {
                changed = editSpawnTreasureLevelField(session, editableSpawn) || changed;
            }
            else
            {
                changed = editUInt16Field(session, "Index", editableSpawn.index) || changed;
            }

            renderInspectorReadOnlyField("Type Label", preview.typeName.empty() ? "<unknown>" : preview.typeName);
            renderInspectorReadOnlyField("Summary", preview.summary.empty() ? "<unresolved>" : preview.summary);
            renderInspectorReadOnlyField("Detail", preview.detail.empty() ? "<none>" : preview.detail);
            ImGui::EndTable();
        }
        endInspectorSectionBlock();
    }

    if (beginInspectorSectionBlock("Placement"))
    {
        if (beginInspectorPropertyTable("IndoorSpawnPlacementFields"))
        {
            changed = editPositionField(session, "Position", editableSpawn.x, editableSpawn.y, editableSpawn.z)
                || changed;
            changed = editUInt16Field(session, "Radius", editableSpawn.radius) || changed;
            changed = editUInt32Field(session, "Group", editableSpawn.group) || changed;
            ImGui::EndTable();
        }
        endInspectorSectionBlock();
    }

    if (beginInspectorSectionBlock("Behavior"))
    {
        if (beginInspectorPropertyTable("IndoorSpawnBehaviorFields"))
        {
            changed = editUInt16Field(session, "Attributes", editableSpawn.attributes) || changed;
            ImGui::EndTable();
        }
        endInspectorSectionBlock();
    }

    if (beginInspectorSectionBlock("Overrides And Legacy", false))
    {
        if (beginInspectorPropertyTable("IndoorSpawnLegacyFields"))
        {
            changed = editUInt16Field(session, "Type Id Raw", editableSpawn.typeId) || changed;
            changed = editUInt16Field(session, "Index Raw", editableSpawn.index) || changed;
            renderInspectorReadOnlyField("Resolved Type", preview.typeName.empty() ? "<unknown>" : preview.typeName);
            renderInspectorReadOnlyField("Resolved Summary", preview.summary.empty() ? "<unresolved>" : preview.summary);
            ImGui::EndTable();
        }
        endInspectorSectionBlock();
    }

    if (changed)
    {
        editableSpawn.z = snapIndoorActorZToFloor(
            indoorGeometry,
            editableSpawn.x,
            editableSpawn.y,
            editableSpawn.z);

        applyEditableSpawn();
        session.setPendingSpawn(editableSpawn);
        indoorGeometry.spawnCount = indoorGeometry.spawns.size();
        session.noteDocumentMutated({});
    }
}

void EditorMainWindow::renderIndoorActorInspector(EditorSession &session, size_t actorIndex) const
{
    renderActorInspector(session, actorIndex);
}

void EditorMainWindow::renderIndoorSpriteObjectInspector(EditorSession &session, size_t spriteObjectIndex) const
{
    renderSpriteObjectInspector(session, spriteObjectIndex);
}

void EditorMainWindow::renderIndoorChestInspector(EditorSession &session, size_t chestIndex) const
{
    renderChestInspector(session, chestIndex);
}

void EditorMainWindow::renderIndoorLightInspector(EditorSession &session, size_t lightIndex) const
{
    const Game::IndoorMapData &indoorGeometry = session.document().indoorGeometry();

    if (lightIndex >= indoorGeometry.lights.size())
    {
        ImGui::TextUnformatted("Selected light index is out of range.");
        return;
    }

    const Game::IndoorLight &light = indoorGeometry.lights[lightIndex];

    if (beginInspectorPropertyTable("IndoorLightFields"))
    {
        renderInspectorReadOnlyField("Position",
            std::to_string(light.x) + ", " + std::to_string(light.y) + ", " + std::to_string(light.z));
        renderInspectorReadOnlyField("Radius", std::to_string(light.radius));
        renderInspectorReadOnlyField("Color",
            std::to_string(light.red) + ", " + std::to_string(light.green) + ", " + std::to_string(light.blue));
        renderInspectorReadOnlyField("Type", std::to_string(light.type));
        renderInspectorReadOnlyField("Attributes", std::to_string(light.attributes));
        renderInspectorReadOnlyField("Brightness", std::to_string(light.brightness));
        ImGui::EndTable();
    }
}

void EditorMainWindow::syncIndoorEventPreviewFromViewport(EditorSession &session)
{
    if (session.document().kind() != EditorDocument::Kind::Indoor)
    {
        return;
    }

    std::string errorMessage;

    if (!session.ensurePreviewEventRuntimeState(errorMessage))
    {
        session.logError(errorMessage);
        return;
    }

    const Game::IndoorSceneData &sceneData = session.document().indoorSceneData();

    for (size_t doorIndex = 0; doorIndex < sceneData.initialState.doors.size(); ++doorIndex)
    {
        uint16_t state = 0;
        float timeSinceTriggeredMs = 0.0f;
        float distance = 0.0f;
        bool isMoving = false;

        if (!m_viewport.tryGetIndoorMechanismPreview(
                session.document(),
                doorIndex,
                state,
                timeSinceTriggeredMs,
                distance,
                isMoving))
        {
            continue;
        }

        session.syncPreviewMechanismState(
            sceneData.initialState.doors[doorIndex].door.doorId,
            state,
            timeSinceTriggeredMs,
            distance,
            isMoving);
    }
}

void EditorMainWindow::applyIndoorEventPreviewToViewport(EditorSession &session)
{
    if (session.document().kind() != EditorDocument::Kind::Indoor)
    {
        return;
    }

    if (!session.lastPreviewEventId().has_value())
    {
        m_viewport.clearIndoorMechanismPreview(session.document());
        return;
    }

    const Game::IndoorSceneData &sceneData = session.document().indoorSceneData();

    for (size_t doorIndex = 0; doorIndex < sceneData.initialState.doors.size(); ++doorIndex)
    {
        const Game::IndoorSceneDoor &door = sceneData.initialState.doors[doorIndex];
        const std::optional<EditorPreviewMechanismState> previewState =
            session.previewMechanismState(door.door.doorId);

        if (!previewState)
        {
            continue;
        }

        Game::RuntimeMechanismState viewportState = {};
        viewportState.state = previewState->state;
        viewportState.timeSinceTriggeredMs = previewState->timeSinceTriggeredMs;
        viewportState.currentDistance = previewState->currentDistance;
        viewportState.isMoving = previewState->isMoving;
        m_viewport.setIndoorMechanismPreviewState(session.document(), doorIndex, viewportState);
    }
}

void EditorMainWindow::renderIndoorDoorInspector(EditorSession &session, size_t doorIndex)
{
    Game::IndoorSceneData &sceneData = session.document().mutableIndoorSceneData();
    const Game::IndoorMapData &indoorGeometry = session.document().indoorGeometry();

    if (doorIndex >= sceneData.initialState.doors.size())
    {
        ImGui::TextUnformatted("Selected door index is out of range.");
        return;
    }

    Game::IndoorSceneDoor &door = sceneData.initialState.doors[doorIndex];
    const std::vector<uint16_t> affectedRoomIds = collectIndoorDoorRoomIds(indoorGeometry, door.door);
    std::vector<size_t> affectedFaceIndices;
    affectedFaceIndices.reserve(door.door.faceIds.size());

    for (uint16_t faceId : door.door.faceIds)
    {
        affectedFaceIndices.push_back(faceId);
    }

    const std::vector<uint16_t> linkedEventIds = collectIndoorFaceEventIds(sceneData, indoorGeometry, affectedFaceIndices);
    const float directionX = static_cast<float>(door.door.directionX) / 65536.0f;
    const float directionY = static_cast<float>(door.door.directionY) / 65536.0f;
    const float directionZ = static_cast<float>(door.door.directionZ) / 65536.0f;
    const float directionLength = std::sqrt(
        directionX * directionX
        + directionY * directionY
        + directionZ * directionZ);
    const float travelX = directionX * static_cast<float>(door.door.moveLength);
    const float travelY = directionY * static_cast<float>(door.door.moveLength);
    const float travelZ = directionZ * static_cast<float>(door.door.moveLength);
    const float travelLength = std::sqrt(
        travelX * travelX
        + travelY * travelY
        + travelZ * travelZ);
    float currentDistance = 0.0f;
    bool previewMoving = false;
    uint16_t previewState = door.door.state;
    float previewTimeSinceTriggeredMs = 0.0f;
    bool hasPreviewState = m_viewport.tryGetIndoorMechanismPreview(
        session.document(),
        doorIndex,
        previewState,
        previewTimeSinceTriggeredMs,
        currentDistance,
        previewMoving);

    if (!hasPreviewState)
    {
        if (door.door.state == static_cast<uint16_t>(Game::EvtMechanismState::Open))
        {
            currentDistance = 0.0f;
        }
        else if (door.door.state == static_cast<uint16_t>(Game::EvtMechanismState::Closing))
        {
            currentDistance = std::min(
                static_cast<float>(door.door.timeSinceTriggered) * static_cast<float>(door.door.closeSpeed) / 1000.0f,
                static_cast<float>(door.door.moveLength));
        }
        else if (door.door.state == static_cast<uint16_t>(Game::EvtMechanismState::Opening))
        {
            currentDistance = std::max(
                0.0f,
                static_cast<float>(door.door.moveLength)
                    - static_cast<float>(door.door.timeSinceTriggered)
                        * static_cast<float>(door.door.openSpeed) / 1000.0f);
        }
        else if (door.door.state == static_cast<uint16_t>(Game::EvtMechanismState::Closed)
            || (door.door.attributes & 0x2) != 0)
        {
            currentDistance = static_cast<float>(door.door.moveLength);
        }
    }

    const char *pPreviewStateLabel = "Unknown";

    switch (previewState)
    {
    case static_cast<uint16_t>(Game::EvtMechanismState::Open):
        pPreviewStateLabel = "Open";
        break;

    case static_cast<uint16_t>(Game::EvtMechanismState::Closing):
        pPreviewStateLabel = "Closing";
        break;

    case static_cast<uint16_t>(Game::EvtMechanismState::Closed):
        pPreviewStateLabel = "Closed";
        break;

    case static_cast<uint16_t>(Game::EvtMechanismState::Opening):
        pPreviewStateLabel = "Opening";
        break;
    }

    bool changed = false;

    if (beginInspectorSectionBlock("Overview"))
    {
        if (ImGui::Button("Close"))
        {
            m_viewport.previewIndoorMechanismClose(session.document(), doorIndex);
        }

        ImGui::SameLine();

        if (ImGui::Button("Open"))
        {
            m_viewport.previewIndoorMechanismOpen(session.document(), doorIndex);
        }

        ImGui::SameLine();

        if (ImGui::Button("Simulate"))
        {
            m_viewport.previewIndoorMechanismSimulate(session.document(), doorIndex);
        }

        ImGui::Spacing();

        if (beginInspectorPropertyTable("IndoorDoorFields"))
        {
            int doorSlot = static_cast<int>(door.doorIndex);

            if (editIntField(
                    session,
                    "Door Index",
                    doorSlot,
                    0,
                    std::numeric_limits<int>::max()))
            {
                door.doorIndex = static_cast<size_t>(doorSlot);
                door.door.slotIndex = static_cast<size_t>(doorSlot);
                changed = true;
            }

            renderInspectorReadOnlyField("Slot Index", std::to_string(door.door.slotIndex));
            changed = editUInt32Field(session, "Door Id", door.door.doorId) || changed;
            changed = editUInt32Field(session, "Attributes", door.door.attributes) || changed;
            changed = editUInt16Field(session, "State", door.door.state) || changed;
            changed = editIntField(
                session,
                "Direction X",
                door.door.directionX,
                std::numeric_limits<int>::min(),
                std::numeric_limits<int>::max()) || changed;
            changed = editIntField(
                session,
                "Direction Y",
                door.door.directionY,
                std::numeric_limits<int>::min(),
                std::numeric_limits<int>::max()) || changed;
            changed = editIntField(
                session,
                "Direction Z",
                door.door.directionZ,
                std::numeric_limits<int>::min(),
                std::numeric_limits<int>::max()) || changed;
            changed = editUInt32Field(session, "Move Length", door.door.moveLength) || changed;
            changed = editUInt32Field(session, "Open Speed", door.door.openSpeed) || changed;
            changed = editUInt32Field(session, "Close Speed", door.door.closeSpeed) || changed;
            changed = editUInt32Field(session, "Time Since Triggered", door.door.timeSinceTriggered) || changed;
            renderInspectorReadOnlyField(
                "Direction Normalized",
                std::to_string(directionX) + ", "
                    + std::to_string(directionY) + ", "
                    + std::to_string(directionZ));
            renderInspectorReadOnlyField("Direction Length", std::to_string(directionLength));
            renderInspectorReadOnlyField(
                "Travel Vector",
                std::to_string(travelX) + ", "
                    + std::to_string(travelY) + ", "
                    + std::to_string(travelZ));
            renderInspectorReadOnlyField("Travel Length", std::to_string(travelLength));
            renderInspectorReadOnlyField(
                "Current Distance",
                std::to_string(currentDistance));
            renderInspectorReadOnlyField("Preview State", pPreviewStateLabel);
            renderInspectorReadOnlyField("Preview Moving", previewMoving ? "Yes" : "No");
            renderInspectorReadOnlyField("Faces", std::to_string(door.door.faceIds.size()));
            renderInspectorReadOnlyField("Vertices", std::to_string(door.door.vertexIds.size()));
            renderInspectorReadOnlyField("Sectors", std::to_string(door.door.sectorIds.size()));
            renderInspectorReadOnlyField("Affected Rooms", formatIndoorRoomList(affectedRoomIds));
            renderInspectorReadOnlyField("Linked Events", std::to_string(linkedEventIds.size()));
            ImGui::EndTable();
        }

        if (!affectedRoomIds.empty())
        {
            ImGui::Spacing();

            for (size_t roomIndex = 0; roomIndex < affectedRoomIds.size(); ++roomIndex)
            {
                const uint16_t roomId = affectedRoomIds[roomIndex];
                const bool isolated =
                    m_viewport.isolatedIndoorRoomId().has_value() && *m_viewport.isolatedIndoorRoomId() == roomId;
                const std::string label =
                    isolated ? "Show All Rooms##DoorRoom" + std::to_string(roomId)
                             : "Isolate Room " + std::to_string(roomId);

                if (ImGui::Button(label.c_str()))
                {
                    m_viewport.setIsolatedIndoorRoomId(isolated ? std::nullopt : std::optional<uint16_t>(roomId));
                }

                if (roomIndex + 1 < affectedRoomIds.size())
                {
                    ImGui::SameLine();
                }
            }
        }

        endInspectorSectionBlock();
    }

    if (beginInspectorSectionBlock("Affected Faces"))
    {
        const bool addPickingActive =
            m_viewport.indoorDoorFaceEditMode() == EditorOutdoorViewport::IndoorDoorFaceEditMode::Add
            && m_viewport.indoorDoorFaceEditDoorIndex() == doorIndex;
        const bool removePickingActive =
            m_viewport.indoorDoorFaceEditMode() == EditorOutdoorViewport::IndoorDoorFaceEditMode::Remove
            && m_viewport.indoorDoorFaceEditDoorIndex() == doorIndex;

        ImGui::Text("Affected Face Count: %zu", door.door.faceIds.size());
        ImGui::TextDisabled("Use Face mode, keep the door selected, then click faces to add/remove.");

        if (renderIconTogglePill(
                "PickAddDoorFaces",
                addPickingActive ? "Stop Add Picking" : "Pick Add Faces",
                UiIcon::Face,
                addPickingActive))
        {
            m_viewport.setPlacementKind(EditorSelectionKind::InteractiveFace);
            m_viewport.setIndoorDoorFaceEditMode(
                addPickingActive
                    ? EditorOutdoorViewport::IndoorDoorFaceEditMode::None
                    : EditorOutdoorViewport::IndoorDoorFaceEditMode::Add,
                addPickingActive ? std::nullopt : std::optional<size_t>(doorIndex));
        }

        ImGui::SameLine();

        if (renderIconTogglePill(
                "PickRemoveDoorFaces",
                removePickingActive ? "Stop Remove Picking" : "Pick Remove Faces",
                UiIcon::Face,
                removePickingActive))
        {
            m_viewport.setPlacementKind(EditorSelectionKind::InteractiveFace);
            m_viewport.setIndoorDoorFaceEditMode(
                removePickingActive
                    ? EditorOutdoorViewport::IndoorDoorFaceEditMode::None
                    : EditorOutdoorViewport::IndoorDoorFaceEditMode::Remove,
                removePickingActive ? std::nullopt : std::optional<size_t>(doorIndex));
        }

        if (door.door.faceIds.empty())
        {
            ImGui::TextDisabled("No face ids are assigned to this mechanism.");
        }
        else
        {
            if (ImGui::Button("Select All Affected Faces"))
            {
                session.replaceInteractiveFaceSelection(door.door.faceIds.front());

                for (size_t faceListIndex = 1; faceListIndex < door.door.faceIds.size(); ++faceListIndex)
                {
                    session.addInteractiveFaceSelection(door.door.faceIds[faceListIndex]);
                }
            }

            ImGui::SameLine();

            if (ImGui::Button("Clear All Affected Faces"))
            {
                session.captureUndoSnapshot();
                door.door.faceIds.clear();
                synchronizeIndoorDoorFaceArraySizes(door.door);
                session.noteDocumentMutated("Cleared mechanism faces");
            }

            for (size_t faceListIndex = 0; faceListIndex < door.door.faceIds.size(); ++faceListIndex)
            {
                const uint16_t faceId = door.door.faceIds[faceListIndex];
                std::string faceLabel = "Face " + std::to_string(faceId);

                if (faceId < indoorGeometry.faces.size())
                {
                    const Game::IndoorFace &face = indoorGeometry.faces[faceId];
                    faceLabel += " - " + trimCopy(face.textureName);
                }

                const std::string buttonLabel =
                    "Select##DoorFace" + std::to_string(doorIndex) + "_" + std::to_string(faceListIndex);

                if (ImGui::Button(buttonLabel.c_str()))
                {
                    session.select(EditorSelectionKind::InteractiveFace, faceId);
                }

                ImGui::SameLine();
                ImGui::TextUnformatted(faceLabel.c_str());
                ImGui::SameLine();

                const std::string removeLabel =
                    "Remove##DoorFaceRemove" + std::to_string(doorIndex) + "_" + std::to_string(faceListIndex);

                if (ImGui::Button(removeLabel.c_str()))
                {
                    session.captureUndoSnapshot();
                    removeIndoorDoorFace(door.door, faceId);
                    session.noteDocumentMutated("Removed mechanism face");
                    --faceListIndex;
                }
            }
        }

        endInspectorSectionBlock();
    }

    if (beginInspectorSectionBlock("Affected Face Triggers", false))
    {
        bool foundTriggerFace = false;

        for (size_t faceListIndex = 0; faceListIndex < door.door.faceIds.size(); ++faceListIndex)
        {
            const uint16_t faceId = door.door.faceIds[faceListIndex];

            if (faceId >= indoorGeometry.faces.size())
            {
                continue;
            }

            const Game::IndoorFace effectiveFace = effectiveIndoorFace(sceneData, indoorGeometry, faceId);

            if (effectiveFace.cogTriggered == 0 && effectiveFace.cogNumber == 0)
            {
                continue;
            }

            foundTriggerFace = true;
            const std::string buttonLabel =
                "Select Face " + std::to_string(faceId) + "##DoorTriggerFace" + std::to_string(doorIndex)
                    + "_" + std::to_string(faceListIndex);

            if (ImGui::Button(buttonLabel.c_str()))
            {
                session.select(EditorSelectionKind::InteractiveFace, faceId);
            }

            ImGui::SameLine();
            ImGui::Text(
                "cog %u  evt %u  trigType %u",
                effectiveFace.cogNumber,
                effectiveFace.cogTriggered,
                effectiveFace.cogTriggerType);

            if (effectiveFace.cogTriggered != 0)
            {
                const std::optional<std::string> description = session.describeMapEvent(effectiveFace.cogTriggered);

                if (description)
                {
                    ImGui::TextDisabled("%s", description->c_str());
                }
            }
        }

        if (!foundTriggerFace)
        {
            ImGui::TextDisabled("No affected face has explicit cog/event trigger data.");
        }

        endInspectorSectionBlock();
    }

    if (beginInspectorSectionBlock("Linked Events", false))
    {
        if (linkedEventIds.empty())
        {
            ImGui::TextDisabled("No affected face references a map event.");
        }
        else
        {
            for (uint16_t eventId : linkedEventIds)
            {
                const std::string previewLabel =
                    "Preview " + std::to_string(eventId) + "##DoorLinkedEvent" + std::to_string(eventId);

                if (ImGui::Button(previewLabel.c_str()))
                {
                    syncIndoorEventPreviewFromViewport(session);
                    std::string errorMessage;

                    if (!session.simulateMapEvent(eventId, errorMessage))
                    {
                        session.logError(errorMessage);
                    }
                    else
                    {
                        applyIndoorEventPreviewToViewport(session);
                    }
                }

                ImGui::SameLine();
                const std::optional<std::string> description = session.describeMapEvent(eventId);
                ImGui::TextUnformatted(description ? description->c_str() : "<unresolved>");
            }
        }

        endInspectorSectionBlock();
    }

    if (beginInspectorSectionBlock("Offsets", false))
    {
        if (beginInspectorPropertyTable("IndoorDoorOffsetFields"))
        {
            renderInspectorReadOnlyField("X Offsets", std::to_string(door.door.xOffsets.size()));
            renderInspectorReadOnlyField("Y Offsets", std::to_string(door.door.yOffsets.size()));
            renderInspectorReadOnlyField("Z Offsets", std::to_string(door.door.zOffsets.size()));
            renderInspectorReadOnlyField("Delta U Values", std::to_string(door.door.deltaUs.size()));
            renderInspectorReadOnlyField("Delta V Values", std::to_string(door.door.deltaVs.size()));
            ImGui::EndTable();
        }
        endInspectorSectionBlock();
    }

    if (changed)
    {
        session.noteDocumentMutated({});
    }
}
}
