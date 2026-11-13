#pragma once

#include "engine/Localization.h"
#include "game/party/Party.h"
#include "game/party/SpellIds.h"
#include "game/ui/GameplayOverlayTypes.h"
#include <algorithm>
#include <array>
#include <vector>

namespace OpenYAMM::Game
{
class GameplayScreenRuntime;
class SpellTable;

struct GameplayBuffHudEntry
{
    PartyBuffId id;
    GameplayResolvedHudLayoutElement rect;
};

enum class GameplayBuffPresentation
{
    Hero,
    Skull,
    Movement,
    Special
};

enum class GameplayBuffHudLayerPass
{
    Underlay,
    Base,
    Overlay
};

struct GameplayBuffHudRegion
{
    float x;
    float y;
    float width;
    float height;
};

struct GameplayBuffHudLayer
{
    const char *pAsset;
    GameplayBuffHudRegion uv;
    GameplayBuffHudRegion placement;
    GameplayBuffHudLayerPass pass = GameplayBuffHudLayerPass::Overlay;
};

// Source UVs select individual foreground sprites from unchanged RGBA atlases.
// Placement uses the old 128-square panel coordinates. Soft effects draw behind the base.
// Resistance gems share a 24-square size budget; teardrops keep their narrower shape.
inline constexpr GameplayBuffHudLayer GameplayBuffHudFireResistance = {
    "obsidian_buff_resistances", {82 / 1536.0f, 78 / 1024.0f, 374 / 1536.0f, 369 / 1024.0f},
    {5.5f, 69, 24, 24}};
inline constexpr GameplayBuffHudLayer GameplayBuffHudWaterResistance = {
    "obsidian_buff_resistances", {616 / 1536.0f, 50 / 1024.0f, 305 / 1536.0f, 415 / 1024.0f},
    {3, 37, 18, 24}};
inline constexpr GameplayBuffHudLayer GameplayBuffHudAirResistance = {
    "obsidian_buff_resistances", {1085 / 1536.0f, 83 / 1024.0f, 358 / 1536.0f, 358 / 1024.0f},
    {23, 6.5f, 24, 24}};
inline constexpr GameplayBuffHudLayer GameplayBuffHudEarthResistance = {
    "obsidian_buff_resistances", {105 / 1536.0f, 556 / 1024.0f, 299 / 1536.0f, 400 / 1024.0f},
    {82, 4.5f, 18, 24}};
inline constexpr GameplayBuffHudLayer GameplayBuffHudMindResistance = {
    "obsidian_buff_resistances", {587 / 1536.0f, 575 / 1024.0f, 361 / 1536.0f, 360 / 1024.0f},
    {99.5f, 29, 24, 24}};
inline constexpr GameplayBuffHudLayer GameplayBuffHudBodyResistance = {
    "obsidian_buff_resistances", {1105 / 1536.0f, 568 / 1024.0f, 358 / 1536.0f, 370 / 1024.0f},
    {97, 61.5f, 24, 24}};
inline constexpr GameplayBuffHudLayer GameplayBuffHudSword = {
    "obsidian_buff_combat", {75 / 1254.0f, 51 / 1254.0f, 505 / 1254.0f, 565 / 1254.0f},
    {11, 6, 45, 80}};
inline constexpr GameplayBuffHudLayer GameplayBuffHudShield = {
    "obsidian_buff_combat", {764 / 1254.0f, 130 / 1254.0f, 374 / 1254.0f, 449 / 1254.0f},
    {57, 24, 52, 62}};
inline constexpr GameplayBuffHudLayer GameplayBuffHudWings = {
    "obsidian_buff_combat", {51 / 1254.0f, 775 / 1254.0f, 525 / 1254.0f, 373 / 1254.0f},
    {48, 81, 40, 35}};
inline constexpr GameplayBuffHudLayer GameplayBuffHudFlames = {
    "obsidian_buff_combat", {644 / 1254.0f, 717 / 1254.0f, 599 / 1254.0f, 482 / 1254.0f},
    {9, 77, 114, 51}, GameplayBuffHudLayerPass::Underlay};
inline constexpr GameplayBuffHudLayer GameplayBuffHudNearEye = {
    "obsidian_buff_skull_effects", {74 / 1536.0f, 89 / 1024.0f, 366 / 1536.0f, 335 / 1024.0f},
    {44, 55, 43, 35}};
inline constexpr GameplayBuffHudLayer GameplayBuffHudFarEye = {
    "obsidian_buff_skull_effects", {661 / 1536.0f, 151 / 1024.0f, 214 / 1536.0f, 214 / 1024.0f},
    {23, 57, 23, 26}};
inline constexpr GameplayBuffHudLayer GameplayBuffHudGarland = {
    "obsidian_buff_skull_effects", {1025 / 1536.0f, 103 / 1024.0f, 495 / 1536.0f, 303 / 1024.0f},
    {24, 30, 81, 37}};
inline constexpr GameplayBuffHudLayer GameplayBuffHudHalo = {
    "obsidian_buff_skull_effects", {29 / 1536.0f, 603 / 1024.0f, 472 / 1536.0f, 295 / 1024.0f},
    {10, 0, 118, 60}};
inline constexpr GameplayBuffHudLayer GameplayBuffHudTorch = {
    "obsidian_buff_skull_effects", {512 / 1536.0f, 517 / 1024.0f, 496 / 1536.0f, 461 / 1024.0f},
    {0, 23, 128, 72}, GameplayBuffHudLayerPass::Underlay};
inline constexpr GameplayBuffHudLayer GameplayBuffHudClouds = {
    "obsidian_buff_skull_effects", {1025 / 1536.0f, 657 / 1024.0f, 505 / 1536.0f, 288 / 1024.0f},
    {0, 79, 128, 49}, GameplayBuffHudLayerPass::Underlay};
inline constexpr GameplayBuffHudLayer GameplayBuffHudStone = {
    "obsidian_buff_skull_stone", {0 / 1254.0f, 0 / 1254.0f, 1254 / 1254.0f, 1254 / 1254.0f},
    {0, 0, 128, 128}, GameplayBuffHudLayerPass::Base};

struct GameplayBuffHudDefinition
{
    const char *pName;
    const char *pIcon;
    GameplayBuffPresentation presentation;
    const GameplayBuffHudLayer *pLayer = nullptr;
    float badgeX = 0;
    float badgeY = 0;
    bool cornerBadge = true;
};

// Preserve the desktop skull mapping; the old Android YAML incorrectly assigned these layers to other spells.
// The far eye extends that mapping for Detect Life; badges cover effects without a legacy desktop layer.
// Invisibility draws no badge: the party portraits show it.
// Flight and Water Walk retain separate animated indicators. Special is reserved for future modifiers.
inline constexpr std::array<GameplayBuffHudDefinition, PartyBuffCount> GameplayBuffHudDefinitions = {{
    {Engine::trNoop("Torch Light").data(),
        "obsidian_buff_sbf01a", GameplayBuffPresentation::Skull, &GameplayBuffHudTorch},
    {Engine::trNoop("Wizard Eye").data(),
        "obsidian_buff_sba01a", GameplayBuffPresentation::Skull, &GameplayBuffHudNearEye},
    {Engine::trNoop("Feather Fall").data(),
        "obsidian_buff_sba02a", GameplayBuffPresentation::Skull, &GameplayBuffHudClouds},
    {Engine::trNoop("Detect Life").data(),
        "obsidian_buff_sbs01a", GameplayBuffPresentation::Skull, &GameplayBuffHudFarEye},
    {Engine::trNoop("Water Walk").data(), "obsidian_buff_sbw05a", GameplayBuffPresentation::Movement},
    {Engine::trNoop("Fly").data(), "obsidian_buff_sba10a", GameplayBuffPresentation::Movement},
    {Engine::trNoop("Invisibility").data(),
        "obsidian_buff_sba08a", GameplayBuffPresentation::Skull, nullptr, 0, 0, false},
    {Engine::trNoop("Stoneskin").data(),
        "obsidian_buff_sbe05a", GameplayBuffPresentation::Skull, &GameplayBuffHudStone},
    {Engine::trNoop("Day of the Gods").data(),
        "obsidian_buff_sbl06a", GameplayBuffPresentation::Skull, &GameplayBuffHudHalo},
    {Engine::trNoop("Protection from Magic").data(),
        "obsidian_buff_sbb09a", GameplayBuffPresentation::Skull, &GameplayBuffHudGarland},
    {Engine::trNoop("Fire Resistance").data(),
        "obsidian_buff_sbf03a", GameplayBuffPresentation::Hero, &GameplayBuffHudFireResistance},
    {Engine::trNoop("Water Resistance").data(),
        "obsidian_buff_sbw03a", GameplayBuffPresentation::Hero, &GameplayBuffHudWaterResistance},
    {Engine::trNoop("Air Resistance").data(),
        "obsidian_buff_sba03a", GameplayBuffPresentation::Hero, &GameplayBuffHudAirResistance},
    {Engine::trNoop("Earth Resistance").data(),
        "obsidian_buff_sbe03a", GameplayBuffPresentation::Hero, &GameplayBuffHudEarthResistance},
    {Engine::trNoop("Mind Resistance").data(),
        "obsidian_buff_sbm03a", GameplayBuffPresentation::Hero, &GameplayBuffHudMindResistance},
    {Engine::trNoop("Body Resistance").data(),
        "obsidian_buff_sbb03a", GameplayBuffPresentation::Hero, &GameplayBuffHudBodyResistance},
    {Engine::trNoop("Shield").data(), "obsidian_buff_sba06a", GameplayBuffPresentation::Hero, &GameplayBuffHudShield},
    {Engine::trNoop("Heroism").data(), "obsidian_buff_sbs07a", GameplayBuffPresentation::Hero, &GameplayBuffHudSword},
    {Engine::trNoop("Haste").data(), "obsidian_buff_sbf05a", GameplayBuffPresentation::Hero, &GameplayBuffHudWings},
    {Engine::trNoop("Immolation").data(),
        "obsidian_buff_sbf08a", GameplayBuffPresentation::Hero, &GameplayBuffHudFlames},
    {Engine::trNoop("Glamour").data(), "obsidian_buff_sbde01a", GameplayBuffPresentation::Hero, nullptr, 46, 46},
    {Engine::trNoop("Levitate").data(), "obsidian_buff_sbv02a", GameplayBuffPresentation::Movement},
    // MM9's own indicator (worlds/mm9/icons_x2): the buff exists only in that world.
    {Engine::trNoop("Fleet Foot").data(), "fleetfoot01", GameplayBuffPresentation::Movement}
}};

inline const char *gameplayBuffPanelLayoutId(GameplayBuffPresentation presentation)
{
    switch (presentation)
    {
        case GameplayBuffPresentation::Hero: return "ObsidianHeroBuffPanel";
        case GameplayBuffPresentation::Skull: return "ObsidianSkullBuffPanel";
        case GameplayBuffPresentation::Movement: return nullptr;
        case GameplayBuffPresentation::Special: return nullptr;
    }
    return nullptr;
}

struct GameplayMovementIndicator
{
    const char *pLayoutId = nullptr;
    PartyBuffId buff = PartyBuffId::Fly;
};

// Fly and Wizard Eye warn before they end (OY-508): in their last ten game minutes their indicator (Fly's icon, Wizard
// Eye's skull layer) blinks, half a real second on and half off (15 game seconds each). Only the drawing of those
// indicators asks, so the warning costs nothing per frame elsewhere.
inline constexpr float GameplayBuffExpiryWarningSeconds = 600.0f;

inline bool gameplayBuffIndicatorLit(const Party &party, PartyBuffId buff)
{
    if (buff != PartyBuffId::Fly && buff != PartyBuffId::WizardEye)
    {
        return true;
    }

    const PartyBuffState *pBuff = party.partyBuff(buff);
    return pBuff == nullptr || pBuff->remainingSeconds > GameplayBuffExpiryWarningSeconds
        || int(pBuff->remainingSeconds / 15.0f) % 2 == 0;
}

// The movement indicators beside the skull, left to right without gaps: Fly, Levitate, Water Walk and MM9's Fleet
// Foot, each while active. Levitate applies Water Walk too; that one is Levitate's own and shows only as Levitate (the
// buff keeps the spell that applied it last, so a Water Walk cast afterwards shows).
inline std::vector<GameplayMovementIndicator> gameplayMovementIndicators(const Party &party)
{
    std::vector<GameplayMovementIndicator> indicators;

    if (party.hasPartyBuff(PartyBuffId::Fly))
    {
        indicators.push_back({"OutdoorFlyBuffIcon", PartyBuffId::Fly});
    }

    if (party.hasPartyBuff(PartyBuffId::Levitate))
    {
        indicators.push_back({"OutdoorLevitateBuffIcon", PartyBuffId::Levitate});
    }

    const PartyBuffState *pWaterWalk = party.partyBuff(PartyBuffId::WaterWalk);

    if (pWaterWalk != nullptr && pWaterWalk->active() && pWaterWalk->spellId != spellIdValue(SpellId::Levitate))
    {
        indicators.push_back({"OutdoorWaterWalkBuffIcon", PartyBuffId::WaterWalk});
    }

    if (party.hasPartyBuff(PartyBuffId::FleetFoot))
    {
        indicators.push_back({"OutdoorFleetFootBuffIcon", PartyBuffId::FleetFoot});
    }

    return indicators;
}

extern const std::array<const char *, CharacterBuffCount> GameplayPersonalBuffNames;
inline std::vector<PartyBuffId> sortedGameplayBuffs(const Party &party)
{
    std::vector<PartyBuffId> result;
    for (size_t i = 0; i < PartyBuffCount; ++i)
    {
        const PartyBuffId id = static_cast<PartyBuffId>(i);
        if (party.partyBuff(id) != nullptr)
        {
            result.push_back(id);
        }
    }
    std::stable_sort(result.begin(), result.end(), [&party](PartyBuffId left, PartyBuffId right)
    {
        return party.partyBuff(left)->remainingSeconds < party.partyBuff(right)->remainingSeconds;
    });
    return result;
}
inline std::vector<PartyBuffId> sortedGameplaySpecialBuffs(const Party &party)
{
    std::vector<PartyBuffId> result = sortedGameplayBuffs(party);
    std::erase_if(result, [](PartyBuffId id)
    {
        return GameplayBuffHudDefinitions[size_t(id)].presentation != GameplayBuffPresentation::Special;
    });
    return result;
}
std::vector<GameplayBuffHudEntry> gameplayBuffHudEntries(GameplayScreenRuntime &context, int width, int height);

// What potions left on a member (a ruleset's timed immunities, aura copies, skill bonuses, regeneration), as
// personal-buff lines: a name and the game seconds left.
struct GameplayPotionEffectLine
{
    std::string name;
    float remainingSeconds = 0;
};

std::vector<GameplayPotionEffectLine> gameplayPotionEffectLines(const Character &member, const SpellTable *pSpellTable);

// An aura the rules hold without a buff slot (MAW's Empower Magic and Meditation), as every member's popup lists it.
struct GameplayAuraLine
{
    std::string name;
    std::string heldText;
};

std::vector<GameplayAuraLine> gameplayUnslottedAuraLines(
    const Party &party,
    const Character &member,
    const SpellTable *pSpellTable);
std::optional<GameplayBuffHudEntry> gameplayMovementBuffAtPoint(GameplayScreenRuntime &context,
    int width, int height, float x, float y);
void renderGameplayBuffHud(GameplayScreenRuntime &context, int width, int height);
GameplayHudPointerTarget gameplayBuffHudTarget(GameplayScreenRuntime &context,
    int width, int height, float x, float y);
}
