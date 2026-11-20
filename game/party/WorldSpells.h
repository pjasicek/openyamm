#pragma once

#include "game/party/SkillData.h"

#include <cstdint>
#include <string>

namespace OpenYAMM::Game
{
class Party;
struct Character;
struct SpellEntry;
struct SpellTooltipText;

// A world's own spell in a shared spell slot. MM9 (world.yml fleetFoot, Party::fleetFootWorld) has no Fly: its Fleet
// Foot takes Fly's slot (Air, spell 21). The slot keeps the spell table's id, name key ("Fly", what saves, quick spells
// and battle orders hold), school, required mastery, cost and recovery; the name and texts shown, the spellbook picture
// (worlds/mm9/icons_x2 sba10a/sba10b over the engine's) and the effect are MM9's. Nothing changes in any other world.

// Whether the party casts MM9's Fleet Foot with this spell: Fly's slot, or the Dragon's Flight, in a Fleet Foot world.
// Any other Fly buff there (a potion, an event's) becomes Fleet Foot too (Party::applyPartyBuff).
bool castsFleetFoot(const Party &party, uint32_t spellId);
// MM9's SPELL.txt row 21: the party's speed in percent, 125 at Expert, 150 at Master, 175 at Grandmaster (below
// Expert, as from a scroll, Expert's).
int fleetFootSpeedPercent(SkillMastery mastery);
// MM9's duration in game seconds: 30 minutes per 2 points of skill at Expert (and below), 60 per 2 at Master, 60 per
// point at Grandmaster.
float fleetFootDurationSeconds(uint32_t skillLevel, SkillMastery mastery);
// The party's movement multiplier under a Fleet Foot of the given speed. The speed-up is a quarter larger while no
// hostile is near (the HUD's green state: partyHasGreenAlert), the user's adaptation (2026-11-09): 125 % gives 131.25 %.
float fleetFootSpeedMultiplier(int speedPercent, bool greenAlert);

// The spell's name as the party's world and rules give it, in English (callers translate it where they show it):
// "Fleet Foot" for Fly's slot in MM9, else the rules' (SpellRules::spellName). A null party: the Standard rules'.
std::string partySpellName(const Party *pParty, const Character &caster, const SpellEntry &spell);
// The spellbook tooltip of the spell for a caster in the party: Fleet Foot's texts for Fly's slot in MM9, else the
// rules' (SpellRules::spellTooltip).
SpellTooltipText partySpellTooltip(const Party &party, const Character &caster, const SpellEntry &spell);
}
