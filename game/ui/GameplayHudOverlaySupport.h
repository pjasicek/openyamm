#pragma once

#include "game/items/ItemSearch.h"

#include <cstdint>
#include <functional>
#include <optional>
#include <string>

namespace OpenYAMM::Game
{
class GameplayScreenRuntime;
struct Character;
struct InventoryItem;
enum class BagTag : uint8_t;
struct GameplayHudTextureHandle;
struct GameplayResolvedHudLayoutElement;

namespace InventoryBagOverview
{
struct Slot;
}

class GameplayHudOverlaySupport
{
public:
    // Time left on a buff or effect for popups: "1h 5m", "3m 20s", "45s", or "Constant".
    static std::string formatRemainingDuration(float remainingSeconds);

    static bool tryPopulateItemInspectOverlayFromRenderedHudItems(
        GameplayScreenRuntime &context,
        int width,
        int height,
        bool requireOpaqueHitTest);

    static void updateCharacterInspectOverlay(
        GameplayScreenRuntime &context,
        int width,
        int height);

    static void updateBuffInspectOverlay(
        GameplayScreenRuntime &context,
        int width,
        int height,
        bool showGameplayHud);

    static void updateCharacterDetailOverlay(
        GameplayScreenRuntime &context,
        int width,
        int height);

    static void updateSpellInspectOverlay(
        GameplayScreenRuntime &context,
        int width,
        int height);

    // A glow around an item's icon in the colour the rules give its name (MAW's rarities, none for Common), else teal for
    // an artifact, relic or special item, drawn just before the icon: its silhouette in that colour in two rings around
    // it. The rarity_glow setting: always, while the Show Item Rarity key is held, or never.
    static void renderItemRarityGlow(
        GameplayScreenRuntime &context,
        const InventoryItem &item,
        const GameplayHudTextureHandle &icon,
        float x,
        float y,
        float width,
        float height,
        float scale);

    // The inventory page shows the bag overview (InventoryBagOverview): a ruleset with several bags, desktop, a party
    // member (not the Adventurers' Inn roster) and no bag zoomed; a spell picking an inventory item shows the open bag
    // at full size.
    static bool bagOverviewActive(const GameplayScreenRuntime &context);
    // A shop's party inventory (display, sell, identify, repair) shows the bag overview too: several bags, desktop and
    // no bag zoomed with its button.
    static bool shopBagOverviewActive(const GameplayScreenRuntime &context);
    // The inventory page shows the tab buttons (CharacterInventoryTab1-5): a party of one with more than four bags
    // (InventoryBags::TabBags) and not the Adventurers' Inn roster.
    static bool inventoryTabsShown(const GameplayScreenRuntime &context);
    // The item search's box (CharacterInventorySearch), starting after the tab buttons while they show.
    static std::optional<GameplayResolvedHudLayoutElement> inventorySearchBox(
        const GameplayScreenRuntime &context,
        int width,
        int height);
    // The bag overview's frame (InventoryBagOverview) inside `grid`: the four bags' surfaces and edges with their tags,
    // a bronze divider between them; renderBag draws each bag's items on its slot.
    static void renderBagOverview(
        GameplayScreenRuntime &context,
        const GameplayResolvedHudLayoutElement &grid,
        const Character &character,
        const std::function<void(const InventoryBagOverview::Slot &, uint8_t)> &renderBag);

    struct InventoryCell
    {
        uint8_t bag = 0;
        uint8_t gridX = 0;
        uint8_t gridY = 0;
    };

    // The active member's bag and cell under the point in a chest's or shop's party inventory: on one of the four bags
    // of the shop's overview, else on the open bag's full-size grid; none off the grids.
    static std::optional<InventoryCell> nestedInventoryCellAt(
        const GameplayScreenRuntime &context,
        int width,
        int height,
        float x,
        float y);
    // The inventory's item search while it filters (the inventory page, something typed), parsed; none otherwise.
    static std::optional<ItemSearch::Query> inventorySearchQuery(const GameplayScreenRuntime &context);
    // What the item search looks through, in lower case: the item's name, type and rarity, its enchantments and the
    // rules' popup lines (MAW's stats and affixes) as `pViewer` reads them; only the name and type while it is not
    // identified.
    static std::string itemSearchText(
        const GameplayScreenRuntime &context,
        const InventoryItem &item,
        const Character *pViewer);
    // Draws an inventory icon faded, for an item the search leaves out.
    static void renderSearchDimmedItem(
        GameplayScreenRuntime &context,
        const GameplayHudTextureHandle &icon,
        float x,
        float y,
        float width,
        float height);
    // A bag tag's icon (the hammer of a crafting bag, the potion of an alchemy bag) in the square at x, y.
    static void renderBagTagIcon(GameplayScreenRuntime &context, BagTag tag, float x, float y, float size);
    // The tags of `bag` as small icons in the top corners of the box at x, y: the crafting bag's left, the alchemy
    // bag's right.
    static void renderBagTagMarks(
        GameplayScreenRuntime &context,
        const Character &character,
        uint8_t bag,
        float x,
        float y,
        float width,
        float size);

    // The on/off switch of a skills page row (MAW's Cover and Mana Shield) and of the Magic heading (an Elementalist's
    // rotation), in logical pixels. A switch row's gem sits at the list's left edge and its name starts
    // SkillSwitchIndent right of it (so do the other names of its group). A click from SkillSwitchReach left of the
    // gem to its right edge flips the switch; the strip from the gem to the indent takes no clicks, so a slightly
    // missed click neither flips the switch nor raises the skill. Touch reaches further into the column gap.
    static constexpr float SkillSwitchGemWidth = 13.0f;
    static constexpr float SkillSwitchIndent = 18.0f;
#if defined(__ANDROID__) || defined(OPENYAMM_IOS)
    static constexpr float SkillSwitchReach = 10.0f;
#else
    static constexpr float SkillSwitchReach = 6.0f;
#endif
    static constexpr float SkillRotationLabelScale = 0.8f;
    // The Magic heading's rotation switch: its "Rotation" label from labelLeft, then the gem at gemX, right-aligned
    // with the magic levels. The label and the gem take clicks alike (a heading raises nothing).
    struct SkillRotationSwitchRect
    {
        float labelLeft = 0;
        float gemX = 0;
        float right = 0;
        float y = 0;
        float height = 0;
        float scale = 1;
    };
    static std::optional<SkillRotationSwitchRect> skillRotationSwitchRect(
        GameplayScreenRuntime &context,
        int width,
        int height);
    // The lit or unlit gem with its left edge at x, centred on centerY, clipped to pClip when given.
    static void renderSkillSwitchGem(
        GameplayScreenRuntime &context,
        bool on,
        float x,
        float centerY,
        float scale,
        const GameplayResolvedHudLayoutElement *pClip);

    static void renderGameplayMouseLookOverlay(
        GameplayScreenRuntime &context,
        int width,
        int height,
        bool active);
};
} // namespace OpenYAMM::Game
