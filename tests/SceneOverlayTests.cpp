#include "doctest/doctest.h"

#include "game/gameplay/CinematicLibrary.h"
#include "game/indoor/IndoorMapData.h"
#include "game/maps/IndoorSceneYml.h"
#include "game/maps/MapLayoutIdentity.h"
#include "game/maps/OutdoorSceneYml.h"
#include "game/maps/SceneOverlayPaths.h"
#include "game/outdoor/OutdoorMapData.h"

#include <algorithm>
#include <filesystem>
#include <fstream>
#include <iterator>
#include <optional>
#include <sstream>
#include <string>
#include <vector>

using namespace OpenYAMM::Game;

// Scene and cinematics overlays (devdocs/map_studio/S6_PLAN.md G1, G2, G5): ladders replace the base scene's,
// cinematics merge by id, actors and floor items append after the base map's, and a map's layout identity counts them.
namespace
{
std::filesystem::path assetPath(const char *pRelativePath)
{
    return std::filesystem::path(OPENYAMM_SOURCE_DIR) / "assets_dev" / pRelativePath;
}

std::string readText(const char *pRelativePath)
{
    std::ifstream stream(assetPath(pRelativePath), std::ios::binary);
    REQUIRE(stream.good());
    std::ostringstream text;
    text << stream.rdbuf();
    return text.str();
}

std::vector<uint8_t> readBytes(const char *pRelativePath)
{
    std::ifstream stream(assetPath(pRelativePath), std::ios::binary);
    REQUIRE(stream.good());
    return std::vector<uint8_t>(std::istreambuf_iterator<char>(stream), std::istreambuf_iterator<char>());
}

const char *IndoorOverlayHeader = "format_version: 1\nkind: indoor_scene_overlay\n";
const char *OutdoorOverlayHeader = "format_version: 1\nkind: outdoor_scene_overlay\n";

const char *OverlayLadders = R"(ladders:
  - {id: overlay_a, bottom: [0, 0, 0], top: [0, 0, 400], facing_degrees: 90, width: 80, reach: 48,
     top_exit: [0, 100, 400], grab_at_top: true}
  - {id: overlay_b, bottom: [500, 0, 0], top: [500, 0, 300], facing_degrees: 0, top_exit: [600, 0, 300]}
)";

// A copy of 6d02's one actor, elsewhere in its room and named, and a floor item (an Iron Longsword, item 1).
const char *OverlayActor = R"(
    - {name: "Overlay Sentry", npc_id: 0, attributes: 0, hp: 50, hostility_type: 0, monster_info_id: 636,
       monster_id: 0, radius: 109, height: 64, move_speed: 24, position: {x: -29280, y: -10496, z: -2201},
       sprite_ids: [3060, 3061, 3062, 3063], sector_id: 1, current_action_animation: 0, carried_item_id: 0,
       group: 85, ally: 0, unique_name_index: 0})";

const char *OverlayItem = R"(
    - {sprite_id: 1, object_description_id: 1, position: {x: -24192, y: -7680, z: -2201},
       velocity: {x: 0, y: 0, z: 0}, yaw_angle: 0, sound_id: 0, attributes: 0, sector_id: 3, time_since_created: 0,
       temporary_lifetime: 0, glow_radius_multiplier: 0, spell_id: 0, spell_level: 0, spell_skill: 0, field54: 0,
       spell_caster_pid: 0, spell_target_pid: 0, lod_distance: 0, spell_caster_ability: 0,
       initial_position: {x: 0, y: 0, z: 0},
       raw_containing_item_hex: "010000000000000000000000000000000000000000000000000000000000000000000000"})";

std::string indoorOverlay(const std::string &body)
{
    return std::string(IndoorOverlayHeader) + body;
}

IndoorSceneData loadIndoorScene(const char *pRelativePath)
{
    std::string error;
    std::optional<IndoorSceneData> scene = IndoorSceneYmlLoader{}.loadFromText(readText(pRelativePath), error);
    REQUIRE_MESSAGE(scene, error);
    return std::move(*scene);
}

// 6d02 (the Abandoned Temple) as the game loads it: its scene, its shipped mist overlay, then the given overlays.
uint64_t indoorIdentity(const std::vector<std::string> &overlays)
{
    IndoorSceneData scene = loadIndoorScene("worlds/mm6/maps/6d02.scene.yml");
    std::string error;
    REQUIRE_MESSAGE(IndoorSceneYmlLoader{}.applyOverlayFromText(
        scene, readText("worlds/mm6/maps/6d02_mist.scene.yml"), error), error);

    for (const std::string &overlay : overlays)
    {
        REQUIRE_MESSAGE(IndoorSceneYmlLoader{}.applyOverlayFromText(scene, overlay, error), error);
    }

    std::optional<IndoorMapData> map = IndoorMapDataLoader{}.loadFromBytes(readBytes("worlds/mm6/maps/6d02.blv"));
    REQUIRE(map);
    std::optional<MapDeltaData> state = MapDeltaData{};
    REQUIRE_MESSAGE(buildIndoorMapStateFromScene(scene, *map, *state, error), error);
    return computeIndoorMapLayoutIdentity(*map, state);
}

uint64_t outdoorIdentity(const std::vector<std::string> &overlays)
{
    std::string error;
    std::optional<OutdoorSceneData> scene =
        OutdoorSceneYmlLoader{}.loadFromText(readText("worlds/mm6/maps/oute3.scene.yml"), error);
    REQUIRE_MESSAGE(scene, error);

    for (const std::string &overlay : overlays)
    {
        REQUIRE_MESSAGE(OutdoorSceneYmlLoader{}.applyOverlayFromText(*scene, overlay, error), error);
    }

    std::optional<OutdoorMapData> map = OutdoorMapDataLoader{}.loadFromBytes(readBytes("worlds/mm6/maps/oute3.odm"));
    REQUIRE(map);
    std::optional<MapDeltaData> state = MapDeltaData{};
    REQUIRE_MESSAGE(buildOutdoorMapStateFromScene(*scene, *map, *state, error), error);
    return computeOutdoorMapLayoutIdentity(*map, state);
}

std::string cinematicsFile(const std::string &body)
{
    return "format_version: 1\nkind: openyamm_cinematics\ncinematics:\n" + body;
}
}

TEST_CASE("scene overlay ladders replace the base scene's list; an overlay without them keeps it")
{
    const IndoorSceneData base = loadIndoorScene("worlds/mm6/maps/6d02.scene.yml");
    REQUIRE(base.ladders.empty());
    std::string error;

    IndoorSceneData overlaid = base;
    REQUIRE_MESSAGE(IndoorSceneYmlLoader{}.applyOverlayFromText(overlaid, indoorOverlay(OverlayLadders), error), error);
    REQUIRE_EQ(overlaid.ladders.size(), 2u);
    CHECK_EQ(overlaid.ladders[0].id, "overlay_a");
    CHECK(overlaid.ladders[0].grabAtTop);
    CHECK_EQ(overlaid.ladders[0].width, 80.0f);
    CHECK_EQ(overlaid.ladders[1].id, "overlay_b");
    CHECK_EQ(overlaid.ladders[1].top[2], 300.0f);

    // A second overlay's list replaces the first's, it does not add to it.
    REQUIRE_MESSAGE(IndoorSceneYmlLoader{}.applyOverlayFromText(overlaid, indoorOverlay(
        "ladders:\n  - {id: overlay_c, bottom: [0, 0, 0], top: [0, 0, 200], facing_degrees: 0, "
        "top_exit: [50, 0, 200]}\n"), error), error);
    REQUIRE_EQ(overlaid.ladders.size(), 1u);
    CHECK_EQ(overlaid.ladders[0].id, "overlay_c");

    // No ladders key: the list stays; an empty list removes every ladder.
    REQUIRE_MESSAGE(IndoorSceneYmlLoader{}.applyOverlayFromText(overlaid, indoorOverlay(""), error), error);
    CHECK_EQ(overlaid.ladders.size(), 1u);
    REQUIRE_MESSAGE(IndoorSceneYmlLoader{}.applyOverlayFromText(overlaid, indoorOverlay("ladders: []\n"), error),
        error);
    CHECK(overlaid.ladders.empty());

    // A bad ladder is refused and leaves the list as it was.
    IndoorSceneData refused = base;
    REQUIRE_MESSAGE(IndoorSceneYmlLoader{}.applyOverlayFromText(refused, indoorOverlay(OverlayLadders), error), error);
    CHECK_FALSE(IndoorSceneYmlLoader{}.applyOverlayFromText(refused, indoorOverlay(
        "ladders:\n  - {id: low, bottom: [0, 0, 100], top: [0, 0, 50], facing_degrees: 0, top_exit: [0, 0, 0]}\n"),
        error));
    CHECK_EQ(refused.ladders.size(), 2u);
    CHECK_FALSE(IndoorSceneYmlLoader{}.applyOverlayFromText(refused, indoorOverlay("ladders: {id: x}\n"), error));

    // The built map carries the overlay's ladders.
    std::optional<IndoorMapData> map = IndoorMapDataLoader{}.loadFromBytes(readBytes("worlds/mm6/maps/6d02.blv"));
    REQUIRE(map);
    MapDeltaData state = {};
    REQUIRE_MESSAGE(buildIndoorMapStateFromScene(refused, *map, state, error), error);
    REQUIRE_EQ(map->ladders.size(), 2u);
    CHECK_EQ(map->ladders[1].id, "overlay_b");
}

TEST_CASE("indoor scene overlays append actors and floor items after the base map's, whose indices stay")
{
    const IndoorSceneData base = loadIndoorScene("worlds/mm6/maps/6d02.scene.yml");
    REQUIRE_EQ(base.initialState.actors.size(), 1u);
    REQUIRE_EQ(base.initialState.spriteObjects.size(), 6u);
    CHECK_EQ(base.initialState.overlayActorCount, 0u);
    std::string error;

    IndoorSceneData overlaid = base;
    REQUIRE_MESSAGE(IndoorSceneYmlLoader{}.applyOverlayFromText(overlaid, indoorOverlay(
        std::string("authored_content:\n  actors:") + OverlayActor + "\n  sprite_objects:" + OverlayItem + "\n"),
        error), error);
    REQUIRE_EQ(overlaid.initialState.actors.size(), 2u);
    CHECK_EQ(overlaid.initialState.overlayActorCount, 1u);
    // The base actor stays first and unchanged.
    CHECK_EQ(overlaid.initialState.actors[0].name, base.initialState.actors[0].name);
    CHECK_EQ(overlaid.initialState.actors[0].y, base.initialState.actors[0].y);
    CHECK_EQ(overlaid.initialState.actors[0].carriedItemId, 2101u);
    CHECK_EQ(overlaid.initialState.actors[1].name, "Overlay Sentry");
    CHECK_EQ(overlaid.initialState.actors[1].y, -10496);
    CHECK_EQ(overlaid.initialState.actors[1].diagnosticSourceActorIndex, 1u);
    REQUIRE_EQ(overlaid.initialState.spriteObjects.size(), 7u);

    for (size_t index = 0; index < base.initialState.spriteObjects.size(); ++index)
    {
        CHECK_EQ(overlaid.initialState.spriteObjects[index].x, base.initialState.spriteObjects[index].x);
        CHECK_EQ(overlaid.initialState.spriteObjects[index].rawContainingItem,
            base.initialState.spriteObjects[index].rawContainingItem);
    }

    const MapDeltaSpriteObject &added = overlaid.initialState.spriteObjects.back();
    CHECK_EQ(added.x, -24192);
    CHECK_EQ(added.objectDescriptionId, 1u);
    REQUIRE_EQ(added.rawContainingItem.size(), 36u);
    CHECK_EQ(added.rawContainingItem[0], 1u);

    // A second overlay appends after the first's.
    REQUIRE_MESSAGE(IndoorSceneYmlLoader{}.applyOverlayFromText(overlaid, indoorOverlay(
        std::string("authored_content:\n  actors:") + OverlayActor + "\n"), error), error);
    REQUIRE_EQ(overlaid.initialState.actors.size(), 3u);
    CHECK_EQ(overlaid.initialState.overlayActorCount, 2u);
    CHECK_EQ(overlaid.initialState.actors[2].diagnosticSourceActorIndex, 2u);

    // The built map state holds them in that order.
    std::optional<IndoorMapData> map = IndoorMapDataLoader{}.loadFromBytes(readBytes("worlds/mm6/maps/6d02.blv"));
    REQUIRE(map);
    MapDeltaData state = {};
    REQUIRE_MESSAGE(buildIndoorMapStateFromScene(overlaid, *map, state, error), error);
    REQUIRE_EQ(state.actors.size(), 3u);
    CHECK_EQ(state.actors[0].carriedItemId, 2101u);
    CHECK_EQ(state.actors[1].name, "Overlay Sentry");
    CHECK_EQ(state.spriteObjects.size(), 7u);

    // Malformed records are refused.
    IndoorSceneData refused = base;
    CHECK_FALSE(IndoorSceneYmlLoader{}.applyOverlayFromText(refused, indoorOverlay(
        "authored_content:\n  actors: {name: x}\n"), error));
    CHECK_FALSE(IndoorSceneYmlLoader{}.applyOverlayFromText(refused, indoorOverlay(
        "authored_content:\n  actors:\n    - {name: x, hp: 5}\n"), error));
    CHECK(error.starts_with("authored_content.actors: "));
    CHECK_FALSE(IndoorSceneYmlLoader{}.applyOverlayFromText(refused, indoorOverlay(
        "authored_content:\n  sprite_objects:\n    - {sprite_id: 1}\n"), error));
    CHECK(error.starts_with("authored_content.sprite_objects: "));
}

TEST_CASE("a world overlay's actors do not void a ruleset's pack reserve made against the scene file's actors")
{
    const std::string reserve = readText("engine/rulesets/maw/maps/bathhouse_zz_maw.scene.yml");
    std::string error;

    IndoorSceneData plain = loadIndoorScene("worlds/mm9/maps/bathhouse.scene.yml");
    const size_t sceneActors = plain.initialState.actors.size();
    REQUIRE_MESSAGE(IndoorSceneYmlLoader{}.applyOverlayFromText(plain, reserve, error), error);
    REQUIRE_FALSE(plain.initialState.packReserve.empty());

    IndoorSceneData withActor = loadIndoorScene("worlds/mm9/maps/bathhouse.scene.yml");
    REQUIRE_MESSAGE(IndoorSceneYmlLoader{}.applyOverlayFromText(withActor, indoorOverlay(
        std::string("authored_content:\n  actors:") + OverlayActor + "\n"), error), error);
    REQUIRE_MESSAGE(IndoorSceneYmlLoader{}.applyOverlayFromText(withActor, reserve, error), error);
    CHECK_EQ(withActor.initialState.actors.size(), sceneActors + 1);
    CHECK_EQ(withActor.initialState.packReserve.size(), plain.initialState.packReserve.size());
}

TEST_CASE("outdoor scene overlays append actors and floor items after the base map's")
{
    std::string error;
    std::optional<OutdoorSceneData> base =
        OutdoorSceneYmlLoader{}.loadFromText(readText("worlds/mm6/maps/oute3.scene.yml"), error);
    REQUIRE_MESSAGE(base, error);
    const size_t actorCount = base->initialState.actors.size();
    const size_t itemCount = base->initialState.spriteObjects.size();
    REQUIRE(actorCount > 0);

    OutdoorSceneData overlaid = *base;
    REQUIRE_MESSAGE(OutdoorSceneYmlLoader{}.applyOverlayFromText(overlaid, std::string(OutdoorOverlayHeader)
        + "authored_content:\n  actors:" + OverlayActor + "\n  sprite_objects:" + OverlayItem + "\n", error), error);
    REQUIRE_EQ(overlaid.initialState.actors.size(), actorCount + 1);
    REQUIRE_EQ(overlaid.initialState.spriteObjects.size(), itemCount + 1);

    for (size_t index = 0; index < actorCount; ++index)
    {
        CHECK_EQ(overlaid.initialState.actors[index].x, base->initialState.actors[index].x);
        CHECK_EQ(overlaid.initialState.actors[index].monsterInfoId, base->initialState.actors[index].monsterInfoId);
    }

    CHECK_EQ(overlaid.initialState.actors.back().name, "Overlay Sentry");
    CHECK_EQ(overlaid.initialState.spriteObjects.back().x, -24192);
}

TEST_CASE("a map's layout identity counts an overlay's actors and items, not its ladders")
{
    const uint64_t shipped = indoorIdentity({});
    CHECK_EQ(indoorIdentity({indoorOverlay("")}), shipped);
    CHECK_EQ(indoorIdentity({indoorOverlay(OverlayLadders)}), shipped);

    const uint64_t withActor = indoorIdentity({indoorOverlay(std::string("authored_content:\n  actors:") + OverlayActor
        + "\n")});
    const uint64_t withItem = indoorIdentity({indoorOverlay(std::string("authored_content:\n  sprite_objects:")
        + OverlayItem + "\n")});
    CHECK_NE(withActor, shipped);
    CHECK_NE(withItem, shipped);
    CHECK_NE(withActor, withItem);
    // The same overlay gives the same identity on every load.
    CHECK_EQ(indoorIdentity({indoorOverlay(std::string("authored_content:\n  actors:") + OverlayActor + "\n")}),
        withActor);
    // A saved state of the map made without the overlay is reset with it, and the other way round.
    CHECK(judgeSavedMapState(shipped, withActor, "mm6") == SavedMapStateVerdict::ResetChanged);
    CHECK(judgeSavedMapState(withActor, shipped, "mm6") == SavedMapStateVerdict::ResetChanged);
    CHECK(judgeSavedMapState(withActor, withActor, "mm6") == SavedMapStateVerdict::Keep);

    const uint64_t outdoorShipped = outdoorIdentity({});
    CHECK_EQ(outdoorIdentity({std::string(OutdoorOverlayHeader)}), outdoorShipped);
    CHECK_NE(outdoorIdentity({std::string(OutdoorOverlayHeader) + "authored_content:\n  actors:" + OverlayActor
        + "\n"}), outdoorShipped);
    CHECK_NE(outdoorIdentity({std::string(OutdoorOverlayHeader) + "authored_content:\n  sprite_objects:"
        + OverlayItem + "\n"}), outdoorShipped);
}

TEST_CASE("cinematics overlays: the file names that count and the merge by id")
{
    CHECK(isCinematicsOverlayFileName("d01_mymod.cinematics.yml", "d01.cinematics.yml"));
    CHECK(isCinematicsOverlayFileName("D01_MyMod.Cinematics.yml", "d01.cinematics.yml"));
    CHECK_FALSE(isCinematicsOverlayFileName("d01.cinematics.yml", "d01.cinematics.yml"));
    CHECK_FALSE(isCinematicsOverlayFileName("d01_.cinematics.yml", "d01.cinematics.yml"));
    CHECK_FALSE(isCinematicsOverlayFileName("d011.cinematics.yml", "d01.cinematics.yml"));
    CHECK_FALSE(isCinematicsOverlayFileName("d01_mymod.scene.yml", "d01.cinematics.yml"));
    CHECK_FALSE(isCinematicsOverlayFileName("d02_mymod.cinematics.yml", "d01.cinematics.yml"));
    // The scene overlays' rule is unchanged.
    CHECK(isSceneOverlayFileName("d01_mymod.scene.yml", "d01.scene.yml"));
    CHECK(isSceneOverlayFileName("d01.scene.mymod.yml", "d01.scene.yml"));
    CHECK_FALSE(isSceneOverlayFileName("d01_mymod.cinematics.yml", "d01.scene.yml"));
    CHECK_FALSE(isSceneOverlayFileName("d01.scene.yml", "d01.scene.yml"));

    std::string error;
    std::optional<CinematicLibrary> library = parseCinematicLibrary(cinematicsFile(
        "  first: {shots: [{duration: 2, position: [0, 0, 0], direction: [1, 0, 0]}]}\n"
        "  second: {shots: [{duration: 3, position: [0, 0, 0], direction: [1, 0, 0]}]}\n"
        "  third: {cues: [{at: 1, subtitle: base, seconds: 1}]}\n"), error);
    REQUIRE_MESSAGE(library, error);
    std::optional<CinematicLibrary> overlay = parseCinematicLibrary(cinematicsFile(
        "  added: {shots: [{duration: 1, position: [0, 0, 0], direction: [1, 0, 0]}]}\n"
        "  second: {skippable: false, shots: [{duration: 7, position: [5, 5, 5], direction: [0, 1, 0]}]}\n"), error);
    REQUIRE_MESSAGE(overlay, error);

    mergeCinematicLibrary(*library, std::move(*overlay));
    REQUIRE_EQ(library->cinematics.size(), 4u);
    // A replaced cinematic keeps its place; a new one goes last.
    CHECK_EQ(library->cinematics[0].id, "first");
    CHECK_EQ(library->cinematics[1].id, "second");
    CHECK_EQ(library->cinematics[2].id, "third");
    CHECK_EQ(library->cinematics[3].id, "added");
    CHECK_EQ(library->cinematics[0].durationSeconds, 2.0f);
    CHECK_EQ(library->cinematics[1].durationSeconds, 7.0f);
    CHECK_FALSE(library->cinematics[1].skippable);
    CHECK_EQ(library->cinematics[1].shots[0].keys[0].position.x, 5.0f);
    const CinematicDefinition *pThird = library->find("third");
    REQUIRE(pThird != nullptr);
    const auto subtitle = std::find_if(pThird->cues.begin(), pThird->cues.end(),
        [](const CinematicCue &cue) { return cue.kind == CinematicCueKind::Subtitle; });
    REQUIRE(subtitle != pThird->cues.end());
    CHECK_EQ(subtitle->text, "base");

    // Merging an empty overlay changes nothing; an overlay into an empty library is the overlay.
    std::optional<CinematicLibrary> empty = parseCinematicLibrary(cinematicsFile("  {}\n"), error);
    REQUIRE_MESSAGE(empty, error);
    mergeCinematicLibrary(*library, std::move(*empty));
    CHECK_EQ(library->cinematics.size(), 4u);
    CinematicLibrary fresh = {};
    mergeCinematicLibrary(fresh, CinematicLibrary(*library));
    CHECK_EQ(fresh.cinematics.size(), 4u);
    CHECK_EQ(fresh.cinematics[3].id, "added");
}
