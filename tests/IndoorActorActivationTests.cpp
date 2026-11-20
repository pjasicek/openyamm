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

TEST_CASE("Wizard Eye actor markers include corpses with loot and Nearby actors")
{
    using OpenYAMM::Game::wizardEyeShowsActorMarker;

    CHECK(wizardEyeShowsActorMarker(true, false, false));
    CHECK_FALSE(wizardEyeShowsActorMarker(true, true, false));
    CHECK_FALSE(wizardEyeShowsActorMarker(true, true, true));
    CHECK(wizardEyeShowsActorMarker(false, false, true));
    CHECK_FALSE(wizardEyeShowsActorMarker(false, false, false));
}
