#pragma once

#include "game/gameplay/PlayerId.h"
#include <bx/math.h>

#include <functional>
#include <optional>
#include <span>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
class GameplayScreenRuntime;
class ItemTable;
struct Character;
struct HeldSkinRules;

// The creature model that stands for another player's character in the world: one of the monsters' and townsfolk's
// models (the user's choice of 2026-11-21, instead of bodies made for players). The race decides first (a Minotaur
// mage is a minotaur, a Dwarf a dwarf); for a human, and where the mounted worlds have no model of the race, the
// kind of class decides (a Cleric and a Druid are a cleric, a Knight and a Paladin a knight in plate), with a
// woman's model where there is a fitting one. A class and its promotions share a body. `raceId` and `sexId` are the
// character's (Character::raceId, Character::sexId). `binds` says whether a model is mounted under a name
// (actors.yml). Empty when no candidate is.
std::string coopBodyDescriptor(
    uint32_t raceId,
    uint32_t sexId,
    const std::string &className,
    const std::function<bool(const std::string &)> &binds);

// How tall another player's body is drawn, in game units to the top of its standing pose: one height for a race and
// a sex, whatever the monster's own size (the user, 2026-11-21: a woman knight's model stood 164 units and a
// minotaur's 309). A human stands 190, eye height being 176. A dragon is 370 to its wing tips, half the Hatchling.
float coopBodyHeight(uint32_t raceId, uint32_t sexId);

// How good what a player's party wears is, for the glow of its body in the other players' games: the average skin
// tier of every member's weapons and armour pieces, rounded (halves up). The whole party counts, not the member that
// stands for it alone (the user, 2026-11-21): the others see one body for a player. A piece's tier is the one the
// first-person weapons are drawn in (heldSkinTier: by its value, its being an artifact, its enchantment and its loot
// rarity). The pieces are each member's unbroken main hand, off hand, bow, body armour, helm, belt, cloak, gauntlets
// and boots; rings and amulets are not seen on a body and are left out. 0 with nothing worn.
uint8_t coopGearTier(std::span<const uint8_t> pieceTiers);
uint8_t coopPartyGearTier(std::span<const Character> members, const ItemTable &itemTable,
    const HeldSkinRules &rules);

// Another player's name above its body.
struct CoopPlayerLabel
{
    std::string name;
    // The body's head.
    float x = 0.0f;
    float y = 0.0f;
    float z = 0.0f;
    bool down = false;
    // A place a player points at, not a player: its own colour, and "name: here".
    bool ping = false;
};

// Another player as the HUD's players panel and the minimap show it.
struct CoopHudPlayer
{
    std::string name;
    // Its resting face, as a texture's name (GameplayUiRuntime::restingPortraitTextureName).
    std::string portraitTextureName;
    // Its health as a share of its most, 0 to 1.
    float healthShare = 0.0f;
    // Its spell points as a share of its most; none when it has no spell points at all.
    std::optional<float> spellPointShare;
    // What ails it, as the character sheet names it; empty when nothing does.
    std::string condition;
    bool down = false;
    bool loadingMap = false;
    float x = 0.0f;
    float y = 0.0f;
    // The party's other members, drawn as small faces beside its first: the face, the health share and whether it
    // is out of the fight.
    struct Mate
    {
        std::string portraitTextureName;
        float healthShare = 0.0f;
        bool down = false;
    };
    std::vector<Mate> mates;
};

// Another player's character as a spell cast on it needs to know it (GameplaySpellService::coopCharacterTarget):
// who it is in the session, where it stands, and each member's hit points and what ails it (one more than the
// condition's number, 0 for nothing). Only the players on the map: not those loading it or stepped out. Set with the session's update,
// so a game that draws nothing has it too.
struct CoopAidPlayer
{
    PlayerId player = LocalPlayer;
    float x = 0.0f;
    float y = 0.0f;
    float footZ = 0.0f;
    // Its members in their order, the first first.
    struct Member
    {
        int32_t health = 0;
        int32_t maxHealth = 0;
        uint8_t conditionCode = 0;
    };
    std::vector<Member> members;
    bool down = false;
};

// A place a player points the others at, for the minimap.
struct CoopHudPing
{
    float x = 0.0f;
    float y = 0.0f;
    // How long it has been shown, of CoopSession::PingSeconds.
    float ageSeconds = 0.0f;
};

void renderCoopPlayerLabels(
    const GameplayScreenRuntime &screenRuntime,
    const std::vector<CoopPlayerLabel> &labels,
    const std::function<bool(const bx::Vec3 &, float &, float &)> &project);
}
