#include <doctest/doctest.h>

#include "game/indoor/IndoorActorActivation.h"
#include "game/ui/WizardEyeMinimapRules.h"

namespace
{
uint32_t attr(OpenYAMM::Game::EvtActorAttribute attribute)
{
    return static_cast<uint32_t>(attribute);
}
}

TEST_CASE("OE indoor generated actors are not born active or detected")
{
    using OpenYAMM::Game::EvtActorAttribute;
    using OpenYAMM::Game::indoorGeneratedActorAttributes;

    const uint32_t friendlyAttributes = indoorGeneratedActorAttributes(false);
    CHECK_EQ(friendlyAttributes, 0u);

    const uint32_t hostileAttributes = indoorGeneratedActorAttributes(true);
    CHECK((hostileAttributes & attr(EvtActorAttribute::Aggressor)) != 0);
    CHECK((hostileAttributes & attr(EvtActorAttribute::Active)) == 0);
    CHECK((hostileAttributes & attr(EvtActorAttribute::FullAi)) == 0);
    CHECK((hostileAttributes & attr(EvtActorAttribute::Nearby)) == 0);
    CHECK((hostileAttributes & attr(EvtActorAttribute::Hostile)) == 0);
}

TEST_CASE("OE indoor detection shortcut uses Nearby but not Aggressor")
{
    using OpenYAMM::Game::EvtActorAttribute;
    using OpenYAMM::Game::indoorActorHasPreviouslyDetectedParty;

    CHECK_FALSE(indoorActorHasPreviouslyDetectedParty(attr(EvtActorAttribute::Aggressor), true));
    CHECK(indoorActorHasPreviouslyDetectedParty(attr(EvtActorAttribute::Nearby), true));
    CHECK_FALSE(indoorActorHasPreviouslyDetectedParty(attr(EvtActorAttribute::Nearby), false));
}

TEST_CASE("Wizard Eye actor markers include corpses, detected hostiles, and friendly actors")
{
    using OpenYAMM::Game::wizardEyeShowsActorMarker;

    CHECK(wizardEyeShowsActorMarker(true, false, true, true));
    CHECK(wizardEyeShowsActorMarker(false, true, true, false));
    CHECK(wizardEyeShowsActorMarker(false, false, false, false));
    CHECK_FALSE(wizardEyeShowsActorMarker(false, false, true, false));
}

TEST_CASE("Wizard Eye hides empty corpses even for detected or friendly actors")
{
    using OpenYAMM::Game::wizardEyeShowsActorMarker;

    CHECK_FALSE(wizardEyeShowsActorMarker(true, false, true, false));
    CHECK_FALSE(wizardEyeShowsActorMarker(true, true, true, false));
    CHECK_FALSE(wizardEyeShowsActorMarker(true, false, false, false));
    CHECK_FALSE(wizardEyeShowsActorMarker(true, true, false, false));
    CHECK(wizardEyeShowsActorMarker(true, true, true, true));
    CHECK(wizardEyeShowsActorMarker(true, false, false, true));
}
