#include "doctest/doctest.h"

#include "engine/AssetFileSystem.h"
#include "game/app/GameSession.h"
#include "game/gameplay/GameplayInputFrame.h"
#include "game/gameplay/GameplayMapNotes.h"
#include "game/gameplay/GameplayOverlayInputController.h"
#include "game/gameplay/GameplayScreenRuntime.h"
#include "game/ui/GameplayJournalMapUi.h"

using namespace OpenYAMM::Game;

TEST_CASE("player map note input creates edits cancels and deletes through journal buttons")
{
    OpenYAMM::Engine::AssetFileSystem assets;
    const std::filesystem::path root = OPENYAMM_SOURCE_DIR;
    REQUIRE(assets.initialize(root, root / "assets_dev", OpenYAMM::Engine::AssetScaleTier::X1));
    GameDataRepository data;
    GameSession session;
    session.bindDataRepository(&data);
    session.gameplayUiRuntime().bindAssetFileSystem(&assets);
    REQUIRE(session.gameplayUiRuntime().ensureGameplayLayoutsLoaded(session.gameplayUiController()));
    Party party;
    MapStatsEntry map;
    map.fileName = "6d01.blv";
    const IndoorMapData geometry;
    const MonsterTable monsters;
    const ObjectTable objects;
    const ItemTable items;
    const ChestTable chests;
    IndoorSceneRuntime scene(map.fileName, map, geometry, monsters, objects, items, chests, party,
        std::nullopt, EventRuntimeState {}, std::nullopt, std::nullopt, &session.gameplayActorService());
    session.setCurrentMapFileName(map.fileName);
    session.bindActiveWorldRuntime(&scene.worldRuntime());
    GameplayScreenRuntime &view = session.gameplayScreenRuntime();
    GameplayUiController::JournalScreenState &screen = view.journalScreenState();
    screen.active = true;
    GameplayInputFrame input;
    input.screenWidth = 1280;
    input.screenHeight = 960;
    const auto frame = [&]()
    {
        REQUIRE(GameplayOverlayInputController::handleJournalOverlayInput(
            view, input, true, false, false, false, false, false, 0));
    };
    const auto click = [&](const std::string &id)
    {
        const auto rect = view.resolveHudLayoutElement(id, input.screenWidth, input.screenHeight, 0, 0);
        REQUIRE(rect.has_value());
        input.pointerX = rect->x + rect->width * 0.5f;
        input.pointerY = rect->y + rect->height * 0.5f;
        input.leftMouseButton = {true, true, false};
        frame();
        input.leftMouseButton = {false, false, true};
        frame();
        input.leftMouseButton = {};
    };
    click("JournalMapAddNoteButton");
    REQUIRE(screen.mapNotePlacementActive);
    click("JournalMapViewport");
    REQUIRE(screen.mapNoteEditActive);
    click("JournalMapSaveNoteButton");
    REQUIRE(screen.mapNoteEditActive);
    CHECK(scene.eventRuntimeState()->runtimeMapNotes.empty());
    REQUIRE(GameplayOverlayInputController::handleJournalOverlayInput(
        view, input, true, true, false, false, false, false, 0));
    CHECK(screen.active);
    CHECK(screen.mapNoteEditActive);
    input.textInput = "Тайник";
    frame();
    input.textInput.clear();
    CHECK(screen.mapNoteEditBuffer == "Тайник");
    CHECK(scene.eventRuntimeState()->runtimeMapNotes.empty());
    click("JournalMapSaveNoteButton");
    REQUIRE_FALSE(screen.mapNoteEditActive);
    const uint32_t id = screen.selectedMapNoteId;
    REQUIRE(id != 0);
    CHECK(scene.eventRuntimeState()->runtimeMapNotes.at(id).text == "Тайник");
    click("JournalMapEditNoteButton");
    REQUIRE(screen.mapNoteEditActive);
    input.keyboardPressCounts[SDL_SCANCODE_BACKSPACE] = 1;
    frame();
    input.keyboardPressCounts.fill(0);
    CHECK(screen.mapNoteEditBuffer == "Тайни");
    input.textInput = "к найден";
    frame();
    input.textInput.clear();
    input.keyboardPressCounts[SDL_SCANCODE_RETURN] = 1;
    frame();
    input.keyboardPressCounts.fill(0);
    CHECK(scene.eventRuntimeState()->runtimeMapNotes.at(id).text == "Тайник найден");
    click("JournalMapEditNoteButton");
    input.textInput = "xxx";
    frame();
    input.textInput.clear();
    input.keyboardHeld[SDL_SCANCODE_ESCAPE] = true;
    frame();
    input.keyboardHeld.fill(false);
    frame();
    CHECK(screen.active);
    CHECK_FALSE(screen.mapNoteEditActive);
    CHECK(scene.eventRuntimeState()->runtimeMapNotes.at(id).text == "Тайник найден");
    click("JournalMapDeleteNoteButton");
    CHECK(scene.eventRuntimeState()->runtimeMapNotes.empty());
    click("JournalMapAddNoteButton");
    click("JournalMapCancelNoteButton");
    CHECK_FALSE(screen.mapNotePlacementActive);
    CHECK(scene.eventRuntimeState()->runtimeMapNotes.empty());
    session.bindActiveWorldRuntime(nullptr);
}
