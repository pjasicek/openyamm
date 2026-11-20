#pragma once

#include "game/content/ContentManifest.h"
#include "game/tables/SpriteTables.h"

#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <string>
#include <vector>

namespace OpenYAMM::Engine
{
class AssetFileSystem;
}

namespace OpenYAMM::Game
{
// The decoration table a world sees (devdocs/WORLD_DECORATION_CONTRIBUTIONS.md): the engine's decoration_data.txt,
// then the rows the active world adds through world.yml (tableContributions: table decorations, mode append, in its
// idRanges decorations). A row's '#' is its decoration number, a map entity's decoration_list_id plus one.
inline constexpr const char *EngineDecorationTablePath = "engine/data_tables/decoration_data.txt";
inline constexpr const char *DecorationContributionTable = "decorations";

// One world's decoration rows (the file's header lines are skipped) and the range it declared for them.
struct WorldDecorationRows
{
    std::string packageId;
    ContentIdRangeDefinition idRange;
    std::vector<std::vector<std::string>> rows;
};

// The engine rows, then the world's (none: the engine rows unchanged). Fails, with a message, on a world range that
// does not start past the engine's last decoration or ends past the largest id, a world row outside the range or not
// in increasing order, and a world decoration name the engine table or an earlier world row already has.
bool composeDecorationTableRows(
    const std::vector<std::vector<std::string>> &engineRows,
    const WorldDecorationRows *pWorldRows,
    std::vector<std::vector<std::string>> &composedRows,
    std::string &errorMessage);

// The rows every decoration table is loaded from: the engine table and the active world's contribution.
bool loadDecorationTableRows(
    const Engine::AssetFileSystem &assetFileSystem,
    std::vector<std::vector<std::string>> &rows,
    std::string &errorMessage);

// The active world's decoration sprites (worlds/<world>/rendering/sprite_frame_data_world_decorations.yml, for the
// sprite ids its decoration rows name), added to a loaded sprite frame table. A world without the file adds nothing.
bool appendWorldDecorationSpriteFrames(
    const Engine::AssetFileSystem &assetFileSystem,
    SpriteFrameTable &spriteFrameTable,
    std::string &errorMessage);

// A decoration id map entities place that the table does not have (skipped by its rows, or past its end).
struct UnresolvedMapDecoration
{
    uint16_t decorationId = 0;
    std::string firstEntityName;
    size_t entityCount = 0;
};

// Each unresolved decoration id of a map's entities once, in the order of first use.
template <typename Entity>
std::vector<UnresolvedMapDecoration> unresolvedMapDecorations(
    const DecorationTable &decorationTable,
    const std::vector<Entity> &entities)
{
    std::vector<UnresolvedMapDecoration> unresolved;

    for (const Entity &entity : entities)
    {
        if (decorationTable.resolveMapDecoration(entity.decorationListId, entity.name).pEntry != nullptr)
        {
            continue;
        }

        const auto found = std::find_if(unresolved.begin(), unresolved.end(),
            [&entity](const UnresolvedMapDecoration &decoration)
            {
                return decoration.decorationId == entity.decorationListId;
            });

        if (found != unresolved.end())
        {
            ++found->entityCount;
        }
        else
        {
            unresolved.push_back({entity.decorationListId, entity.name, 1});
        }
    }

    return unresolved;
}
}
