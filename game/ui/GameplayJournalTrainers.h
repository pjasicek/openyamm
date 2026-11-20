#pragma once

#include "game/ui/GameplayOverlayTypes.h"
#include "game/ui/GameplayUiController.h"

#include <cstddef>
#include <cstdint>

namespace OpenYAMM::Game
{
class GameplayScreenRuntime;

// The journal's Notes > Trainers page as a trainer finder (level_generation/ui/journal_trainers_20261105, approved
// 2026-11-05): continent tabs, a search over skill, mastery, trainer and town, Expert/Master/Grand Master toggles and
// the list by skill, paged; a click shows the trainer's outdoor map with a marker on the door or entrance, zoomed and
// dragged as the Map view. Without a continent's Ledger of Teachers only the trainers the party has found are listed
// (TrainerDirectory.h trainerKnown). Laid out in the JournalTrainerPage area; the renderer and the journal input share
// the layout below. The search text is the journal's notesSearch.
enum class JournalTrainerTargetKind : uint8_t
{
    None,
    Continent,
    Mastery,
    Search,
    // A trainer row of the shown page (index into its rows).
    Row,
    // The map's Close button.
    CloseMap,
    // The map itself, which drags.
    Map,
};

struct JournalTrainerTarget
{
    JournalTrainerTargetKind kind = JournalTrainerTargetKind::None;
    size_t index = 0;
};

bool journalOwnerTabsShown(const GameplayUiController::JournalScreenState &journal);
std::string journalOwner(const GameplayScreenRuntime &context,
    const GameplayUiController::JournalScreenState &journal);
uint32_t journalOwnerTargetAt(const GameplayResolvedHudLayoutElement &page, float x, float y);
void renderJournalOwners(GameplayScreenRuntime &context, const GameplayUiController::JournalScreenState &journal,
    const GameplayResolvedHudLayoutElement &page, float x, float y);

uint32_t packJournalTrainerTarget(const JournalTrainerTarget &target);
JournalTrainerTarget unpackJournalTrainerTarget(uint32_t packed);

// Whether the Trainers notes are shown (the Notes view on the Trainers category).
bool journalTrainersShown(const GameplayUiController::JournalScreenState &journal);
// Whether a trainer's map is shown in place of the list.
bool journalTrainerMapShown(const GameplayUiController::JournalScreenState &journal);
// The category opened: the party's continent, the first page, the list.
void openJournalTrainers(const GameplayScreenRuntime &context, GameplayUiController::JournalScreenState &journal);

JournalTrainerTarget journalTrainerTargetAt(
    const GameplayScreenRuntime &context,
    const GameplayUiController::JournalScreenState &journal,
    const GameplayResolvedHudLayoutElement &page,
    float x,
    float y);
void activateJournalTrainerTarget(
    const GameplayScreenRuntime &context,
    GameplayUiController::JournalScreenState &journal,
    const GameplayResolvedHudLayoutElement &page,
    const JournalTrainerTarget &target);
// Previous/Next and the wheel on the list; the zoom buttons and the wheel on the map (one of the Map view's levels).
void turnJournalTrainerPage(GameplayUiController::JournalScreenState &journal, int delta);
void zoomJournalTrainerMap(GameplayUiController::JournalScreenState &journal, int delta);
// Drags the map: the pointer moved by (deltaX, deltaY) screen pixels since the drag started at the given centre.
void dragJournalTrainerMap(
    GameplayUiController::JournalScreenState &journal,
    const GameplayResolvedHudLayoutElement &page,
    float startCenterX,
    float startCenterY,
    float deltaX,
    float deltaY);
// The list's page count (the renderer clamps the page to it).
size_t journalTrainerPageCount(
    const GameplayScreenRuntime &context,
    const GameplayUiController::JournalScreenState &journal,
    const GameplayResolvedHudLayoutElement &page);
// Draws the page, the status strip and the page number; also the rail's Previous/Next or, on a map, Zoom in/out.
void renderJournalTrainers(
    GameplayScreenRuntime &context,
    GameplayUiController::JournalScreenState &journal,
    const GameplayResolvedHudLayoutElement &page,
    int screenWidth,
    int screenHeight,
    float pointerX,
    float pointerY);
}
