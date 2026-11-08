#include "game/events/EventDialogContent.h"
#include "game/fx/TalkPortraitFrame.h"
#include "game/gameplay/Mm9DialogueSpeaker.h"

#include <doctest/doctest.h>

#include <algorithm>
#include <array>
#include <vector>

using namespace OpenYAMM::Game;

namespace
{
std::array<float, 3> frameMinimum(const std::vector<std::array<float, 3>> &corners)
{
    std::array<float, 3> minimum = corners.front();
    for (const std::array<float, 3> &corner : corners)
    {
        for (size_t axis = 0; axis < 3; ++axis)
        {
            minimum[axis] = std::min(minimum[axis], corner[axis]);
        }
    }
    return minimum;
}

std::array<float, 3> frameMaximum(const std::vector<std::array<float, 3>> &corners)
{
    std::array<float, 3> maximum = corners.front();
    for (const std::array<float, 3> &corner : corners)
    {
        for (size_t axis = 0; axis < 3; ++axis)
        {
            maximum[axis] = std::max(maximum[axis], corner[axis]);
        }
    }
    return maximum;
}
}

TEST_CASE("talk portrait frames a static figure's head and shoulders")
{
    // A 100-tall figure: a wide body and, over its top 14, a narrow head at x 10, y -5.
    std::vector<std::array<float, 3>> points = {{-30.0f, -20.0f, 0.0f}, {30.0f, 20.0f, 0.0f},
        {-30.0f, -20.0f, 80.0f}, {30.0f, 20.0f, 80.0f}, {5.0f, -10.0f, 88.0f}, {15.0f, 0.0f, 100.0f}};
    const std::vector<std::array<float, 3>> frame = talkPortraitStaticFigureFrame(points);
    REQUIRE(frame.size() == 8);
    const std::array<float, 3> minimum = frameMinimum(frame);
    const std::array<float, 3> maximum = frameMaximum(frame);
    // The top 14 (from 86) holds the head's points, 88..100 (12 tall): from 0.6 head heights below its lowest point to
    // 0.12 above the crown, 1.5 head heights wide, centred on it.
    CHECK(minimum[2] == doctest::Approx(88.0f - 0.6f * 12.0f));
    CHECK(maximum[2] == doctest::Approx(100.0f + 0.12f * 12.0f));
    CHECK((minimum[0] + maximum[0]) * 0.5f == doctest::Approx(10.0f));
    CHECK((minimum[1] + maximum[1]) * 0.5f == doctest::Approx(-5.0f));
    CHECK(maximum[0] - minimum[0] == doctest::Approx(1.5f * 12.0f));
    CHECK(talkPortraitStaticFigureFrame({}).empty());
}

TEST_CASE("mm9 dialogue speaker: the talking prop whose click opened the talk")
{
    EventDialogContent dialog;
    dialog.isActive = true;
    dialog.presentation = EventDialogPresentation::Mm9Rude;
    dialog.sourceId = 57;
    EventRuntimeState::DialogueRuntimeState state;
    CHECK_FALSE(findMm9DialogueSpeakerDecoration(dialog, state));

    state.mm9RudeSourceDecorationKey = 300;
    CHECK(findMm9DialogueSpeakerDecoration(dialog, state) == 300u);

    // Opened on an actor: the actor speaks.
    dialog.sourceActorIndex = 4;
    CHECK_FALSE(findMm9DialogueSpeakerDecoration(dialog, state));
    dialog.sourceActorIndex.reset();

    // The innkeeper's inn, opened from his talk: still him; a venue entered by its door: nobody.
    EventDialogContent house;
    house.isActive = true;
    house.isHouseDialog = true;
    CHECK_FALSE(findMm9DialogueSpeakerDecoration(house, state));
    state.suspendedMm9RudeDialogue = EventRuntimeState::SuspendedMm9RudeDialogue{.rudeId = 57};
    CHECK(findMm9DialogueSpeakerDecoration(house, state) == 300u);
    state.suspendedMm9RudeDialogue->sourceActorIndex = 2;
    CHECK_FALSE(findMm9DialogueSpeakerDecoration(house, state));

    // A standard (MM6-MM8) dialogue never takes it.
    EventDialogContent standard;
    standard.isActive = true;
    CHECK_FALSE(findMm9DialogueSpeakerDecoration(standard, state));
    dialog.isActive = false;
    CHECK_FALSE(findMm9DialogueSpeakerDecoration(dialog, state));
}
