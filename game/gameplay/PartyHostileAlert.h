#pragma once

#include "game/gameplay/GameplayRuntimeInterfaces.h"

namespace OpenYAMM::Game
{
// Original yellow alert range: a hostile actor this close (edge distance) blocks Town Portal, Invisibility and
// leaving an indoor map.
constexpr float PartyYellowAlertDistance = 5120.0f;
// Red alert: a hostile actor within melee range.
constexpr float PartyRedAlertDistance = 307.2f;

bool actorRaisesPartyYellowAlert(
    const GameplayActorRulesView &actor,
    float partyX,
    float partyY,
    float partyFootZ);
bool partyHasYellowAlert(const IGameplayWorldRuntime &worldRuntime);
bool partyHasRedAlert(const IGameplayWorldRuntime &worldRuntime);
// The edge distance of the nearest living, visible hostile actor, whether or not it has seen the party; the float
// maximum for none. The HUD's portrait gems read their colour from it.
float nearestHostileDistanceToParty(const IGameplayWorldRuntime &worldRuntime);
// The HUD's green state: no living, visible hostile within the world's engagement range or the yellow alert range,
// whichever is shorter (MM9: 3800). MM9's Fleet Foot runs faster in it (game/party/WorldSpells.h).
bool partyHasGreenAlert(const IGameplayWorldRuntime &worldRuntime);
}
