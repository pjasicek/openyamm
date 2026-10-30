#include "doctest/doctest.h"

#include "game/gameplay/GameplayMapNotes.h"
#include "game/ui/GameplayJournalMapUi.h"
#include "game/maps/SaveGame.h"

#include <cstring>
#include <fstream>
#include <iterator>

using namespace OpenYAMM::Game;

TEST_CASE("player map notes protect automatic notes and keep their map position when edited")
{
    EventRuntimeState state = {};
    EventRuntimeState::RuntimeMapNote teacher = {};
    teacher.id = 1118;
    teacher.active = true;
    teacher.mapFileName = "oute3.odm";
    teacher.text = "Body Magic - Expert";
    state.runtimeMapNotes.emplace(teacher.id, teacher);
    CHECK(saveGameplayUserMapNote(state, teacher.id, teacher.mapFileName, 1, 2, "Changed") == 0);
    CHECK_FALSE(deleteGameplayUserMapNote(state, teacher.id, teacher.mapFileName));
    CHECK(state.runtimeMapNotes.at(teacher.id).text == teacher.text);

    const uint32_t first = saveGameplayUserMapNote(state, 0, "OUTE3.ODM", 123, -456, "  Тайник у дерева  ");
    REQUIRE(first >= GameplayUserMapNoteFirstId);
    CHECK(state.runtimeMapNotes.at(first).text == "Тайник у дерева");
    const uint32_t second = saveGameplayUserMapNote(state, 0, "oute3.odm", 0, 0, "Second");
    REQUIRE(second != 0);
    CHECK(first != second);
    CHECK(saveGameplayUserMapNote(state, first, "oute3.odm", 900, 900, "Проверено") == first);
    CHECK(state.runtimeMapNotes.at(first).x == 123);
    CHECK(state.runtimeMapNotes.at(first).y == -456);
    CHECK(saveGameplayUserMapNote(state, first, "6d01.blv", 0, 0, "Wrong map") == 0);
    CHECK_FALSE(deleteGameplayUserMapNote(state, first, "6d01.blv"));
    CHECK(deleteGameplayUserMapNote(state, first, "OUTE3.ODM"));
    CHECK_FALSE(state.runtimeMapNotes.contains(first));
    CHECK(state.runtimeMapNotes.contains(second));
}

TEST_CASE("player map notes reject blank labels and cap UTF-8 by characters")
{
    EventRuntimeState state = {};
    CHECK(saveGameplayUserMapNote(state, 0, "oute3.odm", 0, 0, " \r\n\t ") == 0);
    CHECK(saveGameplayUserMapNote(state, 0, "", 0, 0, "Text") == 0);
    std::string text;
    for (size_t i = 0; i < 70; ++i)
    {
        text += "Я";
    }
    const uint32_t id = saveGameplayUserMapNote(state, 0, "6d01.blv", 0, 0, text);
    REQUIRE(id != 0);
    const std::string &savedText = state.runtimeMapNotes.at(id).text;
    CHECK(OpenYAMM::Engine::utf8Length(savedText) == GameplayMapNoteMaximumLength);
    CHECK(savedText.size() == GameplayMapNoteMaximumLength * 2);
    CHECK(state.runtimeMapNotes.size() == 1);
}

TEST_CASE("player map notes survive outdoor and cached indoor save snapshots")
{
    GameSaveData save = {};
    save.mapFileName = "oute3.odm";
    save.hasOutdoorRuntimeState = true;
    save.outdoorWorld.eventRuntimeState = EventRuntimeState {};
    EventRuntimeState &outdoor = *save.outdoorWorld.eventRuntimeState;
    const uint32_t outdoorId = saveGameplayUserMapNote(outdoor, 0, "oute3.odm", 1234, -5678, "Вернуться сюда");
    IndoorSceneRuntime::Snapshot indoor = {};
    indoor.eventRuntimeState = EventRuntimeState {};
    const uint32_t indoorId = saveGameplayUserMapNote(*indoor.eventRuntimeState, 0, "6d01.blv", -100, 200, "Дверь");
    save.indoorSceneStates.emplace("mm6:6d01.blv", indoor);
    const std::filesystem::path path = std::filesystem::temp_directory_path() / "openyamm_player_map_notes.oysav";
    std::string error;
    REQUIRE(saveGameDataToPath(path, save, error));
    const std::optional<GameSaveData> loaded = loadGameDataFromPath(path, error);
    std::filesystem::remove(path);
    REQUIRE_MESSAGE(loaded.has_value(), error);
    REQUIRE(loaded->outdoorWorld.eventRuntimeState.has_value());
    const EventRuntimeState::RuntimeMapNote &note =
        loaded->outdoorWorld.eventRuntimeState->runtimeMapNotes.at(outdoorId);
    CHECK(note.userCreated);
    CHECK(note.active);
    CHECK(note.x == 1234);
    CHECK(note.y == -5678);
    CHECK(note.text == "Вернуться сюда");
    CHECK(note.mapFileName == "oute3.odm");
    const EventRuntimeState::RuntimeMapNote &indoorNote =
        loaded->indoorSceneStates.at("mm6:6d01.blv").eventRuntimeState->runtimeMapNotes.at(indoorId);
    CHECK(indoorNote.userCreated);
    CHECK(indoorNote.text == "Дверь");
}

TEST_CASE("player map note placement round trips through zoomed indoor and outdoor transforms")
{
    GameplayUiController::JournalScreenState screen = {};
    screen.mapCenterX = 200;
    screen.mapCenterY = -300;
    for (int zoom = 0; zoom < int(GameplayJournalMapZoomLevels.size()); ++zoom)
    {
        screen.mapZoomStep = zoom;
        GameplayMinimapState indoor = {};
        indoor.worldMinX = -1000;
        indoor.worldMaxX = 2000;
        indoor.worldMinY = -5000;
        indoor.worldMaxY = 1000;
        indoor.zoomWidth = 300;
        indoor.zoomHeight = 600;
        const GameplayMinimapState *maps[] = {nullptr, &indoor};
        for (const GameplayMinimapState *pMap : maps)
        {
            const GameplayJournalMapPoint world = gameplayJournalScreenToWorld(
                270, 310, 100, 150, 300, 300, screen, pMap);
            const GameplayJournalMapPoint pixel = gameplayJournalWorldToScreen(
                world.x, world.y, 100, 150, 300, 300, screen, pMap);
            CHECK(pixel.x == doctest::Approx(270).epsilon(0.0001));
            CHECK(pixel.y == doctest::Approx(310).epsilon(0.0001));
        }
    }
}

TEST_CASE("player map notes load version 88 automatic notes as read only")
{
    GameSaveData save = {};
    constexpr uint64_t PartyTailMarker = 0x12345678abcdef01ull;
    save.party.explosiveMixes.insert(PartyTailMarker);
    save.mapFileName = "oute3.odm";
    save.hasOutdoorRuntimeState = true;
    save.outdoorWorld.eventRuntimeState = EventRuntimeState {};
    EventRuntimeState::RuntimeMapNote teacher = {};
    teacher.id = 1118;
    teacher.mapFileName = save.mapFileName;
    teacher.text = "Legacy map note compatibility fixture";
    teacher.active = true;
    save.outdoorWorld.eventRuntimeState->runtimeMapNotes.emplace(teacher.id, teacher);
    const std::filesystem::path path = std::filesystem::temp_directory_path() / "openyamm_map_notes_v88.oysav";
    std::string error;
    REQUIRE(saveGameDataToPath(path, save, error));
    std::ifstream input(path, std::ios::binary);
    std::string bytes((std::istreambuf_iterator<char>(input)), std::istreambuf_iterator<char>());
    input.close();
    const size_t labelOffset = bytes.find(teacher.text);
    REQUIRE(labelOffset != std::string::npos);
    // Version 89 adds one ownership bool after active. Remove it to reproduce the version 88 layout.
    bytes.erase(labelOffset + teacher.text.size() + sizeof(bool), sizeof(bool));
    const size_t partyTailOffset = bytes.find(
        std::string(reinterpret_cast<const char *>(&PartyTailMarker), sizeof(PartyTailMarker)));
    REQUIRE(partyTailOffset != std::string::npos);
    // Version 90 adds the party's autonote map, empty in this fixture.
    bytes.erase(partyTailOffset + sizeof(PartyTailMarker), sizeof(uint64_t));
    const uint32_t version = 88;
    std::memcpy(bytes.data() + 8, &version, sizeof(version));
    std::ofstream output(path, std::ios::binary | std::ios::trunc);
    output.write(bytes.data(), std::streamsize(bytes.size()));
    output.close();
    const std::optional<GameSaveData> loaded = loadGameDataFromPath(path, error);
    std::filesystem::remove(path);
    REQUIRE_MESSAGE(loaded.has_value(), error);
    REQUIRE(loaded->outdoorWorld.eventRuntimeState.has_value());
    const EventRuntimeState::RuntimeMapNote &note = loaded->outdoorWorld.eventRuntimeState->runtimeMapNotes.at(1118);
    CHECK_FALSE(note.userCreated);
    CHECK(note.active);
    CHECK(note.text == teacher.text);
}
