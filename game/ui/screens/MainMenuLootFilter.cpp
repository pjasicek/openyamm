#include "game/ui/screens/MainMenuScreen.h"

#include "engine/Localization.h"

#include <array>
#include <string>

namespace OpenYAMM::Game
{
namespace
{
// The study's colours (level_generation/ui/maw_loot_progress_20261025/index.html), ABGR.
// The window's small text: the Progress tab's heavier Alegreya instead of Lucida (readable at small resolutions).
constexpr char TextFont[] = "alegreya_semibold";
constexpr uint32_t IvoryColor = 0xffc6dfeau;
constexpr uint32_t MutedColor = 0xffb8c7c2u;
constexpr uint32_t HeadingColor = 0xff95c4d9u;
constexpr uint32_t AmountColor = 0xff6be6ffu;
constexpr uint32_t RuleColor = 0xff3d5163u;
constexpr uint32_t PipOnColor = 0xff5ca2c9u;
constexpr uint32_t PipOffColor = 0xff38443bu;
constexpr uint32_t GoldCellColor = 0xff1f4a5cu;
constexpr uint32_t GoldTextColor = 0xff8ad4f0u;
constexpr uint32_t LevelCellColor = 0xff243f42u;
constexpr uint32_t LevelTextColor = 0xff79c4e0u;
constexpr uint32_t KeepCellColor = 0xff213322u;
constexpr uint32_t KeepTextColor = 0xff9ad08au;
// MAW's rarity colours (MawItemRules::nameColor), Common light grey.
constexpr std::array<uint32_t, LootFilterRarityCount> RarityColors = {
    0xffc9c9c9u, 0xff00ff1eu, 0xffff9600u, 0xffee35a3u, 0xff0080ffu, 0xff3232ffu};

std::string withThousands(int value)
{
    std::string digits = std::to_string(value);

    for (int index = int(digits.size()) - 3; index > 0; index -= 3)
    {
        digits.insert(size_t(index), ",");
    }

    return digits;
}
}

void MainMenuScreen::drawLootFilter()
{
    RulesetLootFilter &filter = m_rulesetDraft.preferences.lootFilter;
    const Rect window = canvasRect(96, 50, 661, 380);
    const auto at = [this](float x, float y, float width, float height)
    { return canvasRect(96 + x, 50 + y, width, height); };

    drawTexture("hud_x2/menus/omenu_modal_veil.png", {0, 0, float(frameWidth()), float(frameHeight())});
    drawTexture("hud_x2/menus/omenu_frame.png", window);
    textInRect(at(24, 16, 300, 24), Engine::tr("Loot filter"), "fondamento", 21, IvoryColor);
    textInRect(at(24, 40, 610, 22),
        Engine::tr("Drops you would rather not carry turn into gold (40 % of their value). The levels follow your "
                   "party, so a preset stays right as you grow."),
        TextFont, 9.5f, MutedColor);
    drawSolidRect(at(20, 64, 621, 0.6f), RuleColor);

    // Strictness: the presets with their one line and a four-step marker. Custom rules come with the rule editor.
    textInRect(at(22, 70, 200, 16), Engine::tr("Strictness"), "fondamento", 13.5f, HeadingColor);

    for (size_t index = 0; index <= size_t(RulesetLootFilterPreset::Custom); ++index)
    {
        const RulesetLootFilterPreset preset = RulesetLootFilterPreset(index);
        const LootFilterPresetDefinition &definition = lootFilterPreset(preset);
        const bool selected = filter.preset == preset;
        const bool available = preset != RulesetLootFilterPreset::Custom;
        const Rect row = at(20, 90 + float(index) * 37.5f, 212, 35);

        if (button("loot-preset-" + std::to_string(index), row, "", "save_row", available, selected) && !selected)
        {
            filter = rulesetLootFilterWithPreset(preset, filter.leaveOnGround);
        }

        const Rect pip = at(27, 90 + float(index) * 37.5f + 6, 6, 6);
        outline(pip, available ? 0xff8aa4b0u : 0xff4a5550u);

        if (selected)
        {
            drawSolidRect({pip.x + designScale(), pip.y + designScale(), pip.width - 2 * designScale(),
                              pip.height - 2 * designScale()},
                0xffb0e7ffu);
        }

        const uint32_t nameColor = available ? IvoryColor : 0xff6b777au;
        textInRect(at(39, 90 + float(index) * 37.5f + 2, 130, 14),
            Engine::tr(rulesetLootFilterPresetName(preset)), "fondamento", 12, nameColor);
        textInRect(at(39, 90 + float(index) * 37.5f + 16.5f, 186, 19),
            available ? Engine::tr(definition.description)
                      : Engine::tr("Your own rules, from the preset you had. Coming next."),
            TextFont, 7.8f, available ? MutedColor : 0xff6b777au);

        for (int step = 0; step < 4 && definition.strictness >= 0; ++step)
        {
            drawSolidRect(at(207 + float(step) * 5.5f, 90 + float(index) * 37.5f + 5, 3.8f, 7.5f),
                step < definition.strictness ? PipOnColor : PipOffColor);
        }
    }

    // What it filters: rarity against weapons, armour and jewellery.
    const float gridX = 248;
    textInRect(at(gridX, 70, 300, 16), Engine::tr("What it filters"), "fondamento", 13.5f, HeadingColor);

    for (size_t group = 0; group < LootFilterGroupCount; ++group)
    {
        textInRect(at(gridX + 64 + float(group) * 106, 90, 104, 12),
            Engine::tr(lootFilterGroupName(LootFilterGroup(group))),
            TextFont, 8.5f, MutedColor, true);
    }

    for (int rarity = 1; rarity <= LootFilterRarityCount; ++rarity)
    {
        const float y = 104 + float(rarity - 1) * 16;
        textInRect(at(gridX + 2, y + 1, 62, 12), Engine::tr(lootFilterRarityName(rarity)), TextFont, 8.5f,
            RarityColors[size_t(rarity - 1)]);

        for (size_t group = 0; group < LootFilterGroupCount; ++group)
        {
            const std::string text = lootFilterCellText(filter.preset, LootFilterGroup(group), rarity);
            const bool gold = text == "gold";
            const bool keep = text == "keep";
            const int gap = lootFilterPreset(filter.preset).columns[group].levelGap;
            const std::string shown = gold ? Engine::tr("gold")
                : keep ? Engine::tr("keep")
                       : Engine::tr("gold if {levels}+ levels below", {{"levels", gap}});
            const Rect cell = at(gridX + 64 + float(group) * 106, y, 104, 14);
            drawSolidRect(cell, gold ? GoldCellColor : keep ? KeepCellColor : LevelCellColor);
            textInRect(cell, shown, TextFont, 8.5f, gold ? GoldTextColor : keep ? KeepTextColor : LevelTextColor,
                true);
        }
    }

    // The note names the preset's own level gap.
    int levelGap = 0;

    for (const LootFilterPresetColumn &column : lootFilterPreset(filter.preset).columns)
    {
        levelGap = levelGap == 0 ? column.levelGap : levelGap;
    }

    textInRect(at(gridX, 202, 380, 22),
        levelGap == 0 ? Engine::tr("Nothing is filtered by rarity.")
                      : Engine::tr("\"Gold if {levels}+ levels below\": only once its level is that far below the "
                                   "party's, so older gear goes as you grow.",
                                   {{"levels", levelGap}}),
        TextFont, 8.5f, MutedColor);

    // The kinds without rarity, each turned into gold or not.
    textInRect(at(gridX, 230, 395, 16), Engine::tr("Items without rarity: turn into gold"), "fondamento", 13.5f,
        HeadingColor);

    for (size_t kind = 0; kind < RulesetLootKindCount; ++kind)
    {
        const bool on = filter.turnsKindIntoGold(RulesetLootKind(kind));
        const Rect chip = at(gridX + float(kind) * 76, 250, 72, 16);

        if (button("loot-kind-" + std::to_string(kind), chip, "", "tab", true, on))
        {
            filter.goldKinds ^= uint8_t(1u << kind);
        }

        outline(chip, RuleColor);

        const Rect box = at(gridX + float(kind) * 76 + 7, 255, 6, 6);
        outline(box, 0xff8aa4b0u);

        if (on)
        {
            drawSolidRect({box.x + designScale(), box.y + designScale(), box.width - 2 * designScale(),
                              box.height - 2 * designScale()},
                0xffb0e7ffu);
        }

        textInRect(at(gridX + float(kind) * 76 + 17, 252, 52, 12),
            Engine::tr(lootFilterKindName(RulesetLootKind(kind))),
            TextFont, 8.5f, on ? IvoryColor : MutedColor);
    }

    textInRect(at(gridX, 272, 395, 12),
        Engine::tr("Always kept: legendary and Celestial items, artifacts, quest items and spellbooks."), TextFont,
        8.5f, MutedColor);

    // What becomes of a filtered drop.
    textInRect(at(gridX, 293, 70, 12), Engine::tr("Filtered items"), TextFont, 8.5f, MutedColor);

    if (button("loot-gold", at(gridX + 72, 290, 92, 16), "", "tab", true, !filter.leaveOnGround))
    {
        filter.leaveOnGround = false;
    }

    outline(at(gridX + 72, 290, 92, 16), RuleColor);

    textInRect(at(gridX + 72, 292, 92, 12), Engine::tr("turn into gold"), TextFont, 8.5f,
        filter.leaveOnGround ? MutedColor : IvoryColor, true);

    if (button("loot-ground", at(gridX + 168, 290, 150, 16), "", "tab", true, filter.leaveOnGround))
    {
        filter.leaveOnGround = true;
    }

    outline(at(gridX + 168, 290, 150, 16), RuleColor);

    textInRect(at(gridX + 168, 292, 150, 12), Engine::tr("stay on the ground, greyed"), TextFont, 8.5f,
        filter.leaveOnGround ? IvoryColor : MutedColor, true);

    // The filter tried on this session's drops.
    drawSolidRect(at(20, 318, 621, 0.6f), RuleColor);
    const std::deque<RecentLootDrop> &drops = m_currentGame->recentLootDrops;
    textInRect(at(22, 324, 400, 16),
        Engine::tr("Your last {count} drops with this filter", {{"count", RecentLootDrops::MaxDrops}}), "fondamento",
        13.5f, HeadingColor);
    const LootFilterTrial trial = tryLootFilter(filter, drops);
    textInRect(at(22, 344, 440, 14),
        drops.empty() ? Engine::tr("No drops yet this session: the filter is tried on the drops to come.")
        : filter.leaveOnGround
            ? Engine::tr("{filtered} left on the ground, {kept} kept, of {count}. Try a preset here before choosing "
                         "it.",
                {{"filtered", trial.filtered}, {"kept", trial.drops - trial.filtered}, {"count", trial.drops}})
            : Engine::tr("{filtered} turned into {gold} gold, {kept} kept, of {count}. Try a preset here before "
                         "choosing it.",
                {{"filtered", trial.filtered}, {"gold", withThousands(trial.gold)},
                    {"kept", trial.drops - trial.filtered}, {"count", trial.drops}}),
        TextFont, 9.5f, drops.empty() ? MutedColor : AmountColor);

    // Done returns to Settings, where Apply keeps the choice.
    if (button("loot-done", at(531, 334, 110, 24), Engine::tr("Done"), "button") || keyPressed(SDL_SCANCODE_ESCAPE))
    {
        m_lootFilterOpen = false;
    }
}
}
