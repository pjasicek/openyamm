#include "game/ui/screens/MainMenuScreen.h"

#include "engine/Localization.h"

#include <array>
#include <string>
#include <utility>
#include <vector>

namespace OpenYAMM::Game
{
namespace
{
// The study's colours (level_generation/ui/maw_loot_progress_20261025/index.html), ABGR.
// The window's small text: the Progress tab's heavier Alegreya instead of Lucida (readable at small resolutions).
constexpr char TextFont[] = "alegreya_semibold";
constexpr uint32_t IvoryColor = 0xffc6dfeau;
constexpr uint32_t MutedColor = 0xffb8c7c2u;
constexpr uint32_t DimColor = 0xff6b777au;
constexpr uint32_t HeadingColor = 0xff95c4d9u;
constexpr uint32_t AmountColor = 0xff6be6ffu;
constexpr uint32_t RuleColor = 0xff3d5163u;
constexpr uint32_t ChosenColor = 0xffb0e7ffu;
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
// The level conditions a rule offers (0: any level).
constexpr std::array<int, 5> LevelSteps = {0, 10, 20, 30, 40};

std::string withThousands(int value)
{
    std::string digits = std::to_string(value);

    for (int index = int(digits.size()) - 3; index > 0; index -= 3)
    {
        digits.insert(size_t(index), ",");
    }

    return digits;
}

std::string actionText(LootFilterAction action)
{
    return action == LootFilterAction::Gold ? Engine::tr("Turn into gold")
        : action == LootFilterAction::Ground ? Engine::tr("Leave on the ground")
                                             : Engine::tr("Keep");
}

uint32_t actionColor(LootFilterAction action)
{
    return action == LootFilterAction::Gold ? GoldTextColor
        : action == LootFilterAction::Ground ? LevelTextColor
                                             : KeepTextColor;
}

// "Weapons, Ring, Scrolls": whole groups by their name, the rest type by type.
std::string typesText(uint32_t types)
{
    std::string text;
    uint32_t rest = types;
    const auto append = [&text](const std::string &part) { text += (text.empty() ? "" : ", ") + part; };

    for (size_t group = 0; group < LootFilterGroupCount; ++group)
    {
        const uint32_t bits = lootItemTypesOfGroup(LootFilterGroup(group));

        if ((types & bits) == bits)
        {
            append(Engine::tr(lootFilterGroupName(LootFilterGroup(group))));
            rest &= ~bits;
        }
    }

    for (size_t type = 0; type < LootItemTypeCount; ++type)
    {
        if ((rest & (1u << type)) != 0)
        {
            append(Engine::tr(lootItemTypeName(LootItemType(type))));
        }
    }

    return text;
}

// "Uncommon or below · Weapons, Armour, 20+ levels below"; the kinds without rarity name no rarity.
std::string ruleText(const RulesetLootFilterRule &rule)
{
    if (rule.types == 0)
    {
        return Engine::tr("No item types yet");
    }

    std::string text;

    if ((rule.types & ~lootItemTypesWithoutRarity()) != 0)
    {
        text = Engine::tr("{rarity} or below", {{"rarity", Engine::tr(lootFilterRarityName(rule.rarityAtMost))}})
            + " · ";
    }

    text += typesText(rule.types);

    if (rule.levelsBelow > 0)
    {
        text += ", " + Engine::tr("{levels}+ levels below", {{"levels", int(rule.levelsBelow)}});
    }

    return text;
}

// The rules editor's item types, row by row: weapons, armour, jewellery and the kinds without rarity. A group's last
// row ends with a chip that takes or drops the whole group.
struct TypeRow
{
    std::vector<LootItemType> types;
    std::optional<LootFilterGroup> wholeGroup;
};

const std::array<TypeRow, 6> &typeRows()
{
    using T = LootItemType;
    static const std::array<TypeRow, 6> Rows = {{
        {{T::Sword, T::Dagger, T::Axe, T::Spear, T::Mace}, std::nullopt},
        {{T::Club, T::Staff, T::Bow, T::Throwing}, LootFilterGroup::Weapons},
        {{T::Leather, T::Chain, T::Plate, T::Shield, T::Helm}, std::nullopt},
        {{T::Belt, T::Cloak, T::Gauntlets, T::Boots}, LootFilterGroup::Armour},
        {{T::Ring, T::Amulet}, LootFilterGroup::Jewellery},
        {{T::Wands, T::Scrolls, T::Potions, T::Reagents, T::Gems}, std::nullopt},
    }};
    return Rows;
}
}

void MainMenuScreen::drawLootFilter()
{
    if (m_lootFilterRules)
    {
        drawLootFilterRules();
        return;
    }

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

    // Strictness: the presets with their one line and a four-step marker; Custom opens the rules.
    textInRect(at(22, 70, 200, 16), Engine::tr("Strictness"), "fondamento", 13.5f, HeadingColor);

    for (size_t index = 0; index <= size_t(RulesetLootFilterPreset::Custom); ++index)
    {
        const RulesetLootFilterPreset preset = RulesetLootFilterPreset(index);
        const LootFilterPresetDefinition &definition = lootFilterPreset(preset);
        const bool selected = filter.preset == preset;
        const Rect row = at(20, 90 + float(index) * 37.5f, 212, 35);

        if (button("loot-preset-" + std::to_string(index), row, "", "save_row", true, selected))
        {
            if (preset == RulesetLootFilterPreset::Custom)
            {
                filter = lootFilterAsCustom(filter);
                m_lootFilterRules = true;
                m_lootFilterRule = filter.rules.empty() ? -1 : 0;
            }
            else if (!selected)
            {
                filter = rulesetLootFilterWithPreset(preset, filter.leaveOnGround);
            }
        }

        const Rect pip = at(27, 90 + float(index) * 37.5f + 6, 6, 6);
        outline(pip, 0xff8aa4b0u);

        if (selected)
        {
            drawSolidRect({pip.x + designScale(), pip.y + designScale(), pip.width - 2 * designScale(),
                              pip.height - 2 * designScale()},
                ChosenColor);
        }

        textInRect(at(39, 90 + float(index) * 37.5f + 2, 130, 14),
            Engine::tr(rulesetLootFilterPresetName(preset)), "fondamento", 12, IvoryColor);
        textInRect(at(39, 90 + float(index) * 37.5f + 16.5f, 186, 19), Engine::tr(definition.description), TextFont,
            7.8f, MutedColor);

        for (int step = 0; step < 4 && definition.strictness >= 0; ++step)
        {
            drawSolidRect(at(207 + float(step) * 5.5f, 90 + float(index) * 37.5f + 5, 3.8f, 7.5f),
                step < definition.strictness ? PipOnColor : PipOffColor);
        }
    }

    const float gridX = 248;

    if (filter.preset == RulesetLootFilterPreset::Custom)
    {
        // Custom: its rules in order, edited in the rules view.
        textInRect(at(gridX, 70, 300, 16), Engine::tr("Your rules"), "fondamento", 13.5f, HeadingColor);
        float y = 92;
        const auto line = [&](const std::string &text, LootFilterAction action)
        {
            textInRect(at(gridX + 2, y, 280, 14), text, TextFont, 8.5f, IvoryColor);
            textInRect(at(gridX + 288, y, 105, 14), actionText(action), TextFont, 8.5f, actionColor(action));
            y += 15;
        };
        line(Engine::tr("Legendary, Celestial or artifact"), LootFilterAction::Keep);

        for (const RulesetLootFilterRule &rule : filter.rules)
        {
            line(ruleText(rule), rule.action);
        }

        line(Engine::tr("Everything else"), filter.otherwise);

        if (button("loot-edit-rules", at(gridX, y + 8, 130, 24), Engine::tr("Edit rules"), "button"))
        {
            m_lootFilterRules = true;
            m_lootFilterRule = filter.rules.empty() ? -1 : 0;
        }
    }
    else
    {
        // What it filters: rarity against weapons, armour and jewellery.
        textInRect(at(gridX, 70, 300, 16), Engine::tr("What it filters"), "fondamento", 13.5f, HeadingColor);

        for (size_t group = 0; group < LootFilterGroupCount; ++group)
        {
            textInRect(at(gridX + 64 + float(group) * 106, 90, 104, 12),
                Engine::tr(lootFilterGroupName(LootFilterGroup(group))), TextFont, 8.5f, MutedColor, true);
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
                    ChosenColor);
            }

            textInRect(at(gridX + float(kind) * 76 + 17, 252, 52, 12),
                Engine::tr(lootFilterKindName(RulesetLootKind(kind))), TextFont, 8.5f, on ? IvoryColor : MutedColor);
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
    }

    // The filter tried on this session's drops.
    drawSolidRect(at(20, 318, 621, 0.6f), RuleColor);
    const std::deque<RecentLootDrop> &drops = m_currentGame->recentLootDrops;
    textInRect(at(22, 324, 400, 16),
        Engine::tr("Your last {count} drops with this filter", {{"count", RecentLootDrops::MaxDrops}}), "fondamento",
        13.5f, HeadingColor);
    const LootFilterTrial trial = tryLootFilter(filter, drops);
    textInRect(at(22, 344, 440, 14),
        drops.empty() ? Engine::tr("No drops yet this session: the filter is tried on the drops to come.")
        : filter.leaveOnGround && filter.preset != RulesetLootFilterPreset::Custom
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

void MainMenuScreen::drawLootFilterRules()
{
    RulesetLootFilter &filter = m_rulesetDraft.preferences.lootFilter;
    std::vector<RulesetLootFilterRule> &rules = filter.rules;
    const Rect window = canvasRect(96, 50, 661, 380);
    const auto at = [this](float x, float y, float width, float height)
    { return canvasRect(96 + x, 50 + y, width, height); };
    // A small toggle: the tab plate, a bright outline when on.
    const auto chip = [&](const std::string &id, const Rect &rect, const std::string &text, bool on, uint32_t color)
    {
        const bool clicked = button(id, rect, "", "tab", true, on);
        outline(rect, on ? ChosenColor : RuleColor);
        textInRect(rect, text, TextFont, 8, on ? color : MutedColor, true);
        return clicked;
    };

    if (m_lootFilterRule >= int(rules.size()))
    {
        m_lootFilterRule = -1;
    }

    drawTexture("hud_x2/menus/omenu_modal_veil.png", {0, 0, float(frameWidth()), float(frameHeight())});
    drawTexture("hud_x2/menus/omenu_frame.png", window);
    textInRect(at(24, 16, 400, 24), Engine::tr("Loot filter · rules"), "fondamento", 21, IvoryColor);
    textInRect(at(24, 40, 500, 22),
        Engine::tr("Every drop is checked against these rules from the top; the first rule that fits decides. Quest "
                   "items, spellbooks and crafting materials are never filtered."),
        TextFont, 9.5f, MutedColor);

    if (button("loot-presets", at(531, 16, 110, 24), Engine::tr("Presets"), "button"))
    {
        m_lootFilterRules = false;
    }

    drawSolidRect(at(20, 64, 621, 0.6f), RuleColor);

    // The rules: the fixed first row, the player's rules with move and remove, and "Everything else".
    textInRect(at(22, 70, 200, 16), Engine::tr("Rules"), "fondamento", 13.5f, HeadingColor);
    constexpr float RowStep = 21;
    constexpr float RowHeight = 19;
    float y = 90;
    textInRect(at(26, y + 3, 12, 13), "1", TextFont, 8.5f, DimColor);
    textInRect(at(38, y + 3, 168, 13), Engine::tr("Legendary, Celestial or artifact"), TextFont, 8.5f, MutedColor);
    textInRect(at(208, y + 3, 62, 13), actionText(LootFilterAction::Keep), TextFont, 8.5f, KeepTextColor);
    y += RowStep;
    std::optional<std::pair<size_t, size_t>> swap;
    std::optional<size_t> removed;

    for (size_t index = 0; index < rules.size(); ++index, y += RowStep)
    {
        const RulesetLootFilterRule &rule = rules[index];
        const bool selected = m_lootFilterRule == int(index);

        if (button("loot-rule-" + std::to_string(index), at(20, y, 250, RowHeight), "", "save_row", true, selected))
        {
            m_lootFilterRule = int(index);
        }

        textInRect(at(26, y + 3, 12, 13), std::to_string(index + 2), TextFont, 8.5f, DimColor);
        textInRect(at(38, y + 1, 168, RowHeight - 2), ruleText(rule), TextFont, 7.8f,
            rule.types == 0 ? DimColor : IvoryColor);
        textInRect(at(208, y + 3, 62, 13), actionText(rule.action), TextFont, 8, actionColor(rule.action));

        // Up, down and remove: glyphs that brighten under the pointer.
        const std::array<std::pair<const char *, bool>, 3> Glyphs = {{{"omenu_glyph_up.png", index > 0},
            {"omenu_glyph_down.png", index + 1 < rules.size()}, {"omenu_glyph_minus.png", true}}};

        for (size_t glyph = 0; glyph < Glyphs.size(); ++glyph)
        {
            const Rect rect = at(274 + float(glyph) * 16, y + 2, 15, 15);
            const Hotspot input =
                hotspot("loot-rule-" + std::to_string(index) + "-" + std::to_string(glyph), rect, Glyphs[glyph].second);
            drawTextureColor(std::string("hud_x2/menus/") + Glyphs[glyph].first,
                {rect.x + 2 * designScale(), rect.y + 2 * designScale(), 11 * designScale(), 11 * designScale()},
                !Glyphs[glyph].second ? PipOffColor : input.hovered ? ChosenColor : MutedColor);

            if (input.activated)
            {
                if (glyph == 2)
                {
                    removed = index;
                }
                else
                {
                    swap = {index, glyph == 0 ? index - 1 : index + 1};
                }
            }
        }
    }

    if (button("loot-rule-otherwise", at(20, y, 250, RowHeight), "", "save_row", true, m_lootFilterRule < 0))
    {
        m_lootFilterRule = -1;
    }

    textInRect(at(26, y + 3, 12, 13), std::to_string(rules.size() + 2), TextFont, 8.5f, DimColor);
    textInRect(at(38, y + 3, 168, 13), Engine::tr("Everything else"), TextFont, 8.5f, IvoryColor);
    textInRect(at(208, y + 3, 62, 13), actionText(filter.otherwise), TextFont, 8, actionColor(filter.otherwise));
    y += RowStep + 4;

    if (button("loot-rule-add", at(20, y, 120, 22), Engine::tr("Add rule"), "button",
            rules.size() < RulesetLootFilterMaxRules))
    {
        // A new rule goes above "Everything else" and takes what a preset's filtered drops did.
        RulesetLootFilterRule rule;
        rule.action = filter.leaveOnGround ? LootFilterAction::Ground : LootFilterAction::Gold;
        rules.push_back(rule);
        m_lootFilterRule = int(rules.size()) - 1;
    }

    if (swap)
    {
        std::swap(rules[swap->first], rules[swap->second]);
        m_lootFilterRule = m_lootFilterRule == int(swap->first) ? int(swap->second)
            : m_lootFilterRule == int(swap->second)              ? int(swap->first)
                                                                 : m_lootFilterRule;
    }
    else if (removed)
    {
        rules.erase(rules.begin() + std::ptrdiff_t(*removed));
        m_lootFilterRule = rules.empty() ? -1 : std::min(int(*removed), int(rules.size()) - 1);
    }

    // The chosen rule's editor.
    drawSolidRect(at(326, 72, 0.6f, 250), RuleColor);
    const float x = 340;
    const std::deque<RecentLootDrop> &drops = m_currentGame->recentLootDrops;
    const LootFilterTrial trial = tryLootFilter(filter, drops);
    LootFilterAction *pAction = &filter.otherwise;
    size_t decided = trial.byOtherwise;

    if (m_lootFilterRule >= 0)
    {
        RulesetLootFilterRule &rule = rules[size_t(m_lootFilterRule)];
        pAction = &rule.action;
        decided = trial.byRule[size_t(m_lootFilterRule)];
        textInRect(at(x, 70, 290, 16), Engine::tr("Rule {number}", {{"number", m_lootFilterRule + 2}}), "fondamento",
            13.5f, HeadingColor);

        textInRect(at(x, 89, 300, 12), Engine::tr("Rarity at most (weapons, armour and jewellery)"), TextFont, 8.5f,
            MutedColor);

        for (int rarity = 1; rarity <= LootFilterRarityCount; ++rarity)
        {
            const Rect rect = at(x + float((rarity - 1) % 3) * 100, 102 + float((rarity - 1) / 3) * 17, 96, 15);

            if (chip("loot-rarity-" + std::to_string(rarity), rect, Engine::tr(lootFilterRarityName(rarity)),
                    rule.rarityAtMost == rarity, RarityColors[size_t(rarity - 1)]))
            {
                rule.rarityAtMost = uint8_t(rarity);
            }
        }

        textInRect(at(x, 139, 300, 12), Engine::tr("Item types"), TextFont, 8.5f, MutedColor);
        float rowY = 152;

        for (const TypeRow &row : typeRows())
        {
            float chipX = x;

            for (const LootItemType type : row.types)
            {
                const uint32_t bit = 1u << unsigned(type);

                if (chip("loot-type-" + std::to_string(size_t(type)), at(chipX, rowY, 57, 14),
                        Engine::tr(lootItemTypeName(type)), (rule.types & bit) != 0, IvoryColor))
                {
                    rule.types ^= bit;
                }

                chipX += 60;
            }

            if (row.wholeGroup)
            {
                // "All weapons": takes the whole group, or drops it when it is all taken.
                const uint32_t bits = lootItemTypesOfGroup(*row.wholeGroup);
                const bool all = (rule.types & bits) == bits;
                const std::string name = *row.wholeGroup == LootFilterGroup::Weapons ? Engine::tr("All weapons")
                    : *row.wholeGroup == LootFilterGroup::Armour                     ? Engine::tr("All armour")
                                                                                     : Engine::tr("All jewellery");

                if (chip("loot-group-" + std::to_string(size_t(*row.wholeGroup)),
                        at(chipX, rowY, 297 - (chipX - x), 14), name, all, AmountColor))
                {
                    rule.types = all ? rule.types & ~bits : rule.types | bits;
                }
            }

            rowY += 16;
        }

        textInRect(at(x, 250, 300, 12), Engine::tr("Item level"), TextFont, 8.5f, MutedColor);

        for (size_t step = 0; step < LevelSteps.size(); ++step)
        {
            const int levels = LevelSteps[step];
            const std::string text =
                levels == 0 ? Engine::tr("Any level") : Engine::tr("{levels}+ below", {{"levels", levels}});

            if (chip("loot-level-" + std::to_string(step), at(x + float(step) * 60, 263, 57, 14), text,
                    rule.levelsBelow == levels, IvoryColor))
            {
                rule.levelsBelow = uint8_t(levels);
            }
        }
    }
    else
    {
        textInRect(at(x, 70, 290, 16), Engine::tr("Everything else"), "fondamento", 13.5f, HeadingColor);
        textInRect(at(x, 92, 295, 40),
            Engine::tr("What becomes of a drop that no rule above takes. Below Legendary, items of a type no rule "
                       "names come here too."),
            TextFont, 8.5f, MutedColor);
    }

    // What the rule does, and how many of the recent drops it decided.
    textInRect(at(x, 283, 300, 12), Engine::tr("Then"), TextFont, 8.5f, MutedColor);
    const std::array<std::pair<LootFilterAction, float>, 3> Actions = {
        {{LootFilterAction::Keep, 70}, {LootFilterAction::Gold, 100}, {LootFilterAction::Ground, 121}}};
    float actionX = x;

    for (const auto &[action, width] : Actions)
    {
        if (chip("loot-action-" + std::to_string(int(action)), at(actionX, 296, width, 15), actionText(action),
                *pAction == action, actionColor(action)))
        {
            *pAction = action;
        }

        actionX += width + 3;
    }

    if (!drops.empty())
    {
        textInRect(at(x, 314, 300, 12),
            Engine::tr("Decided {decided} of your last {count} drops.", {{"decided", decided}, {"count", drops.size()}}),
            TextFont, 8, MutedColor);
    }

    // The whole filter tried on this session's drops.
    drawSolidRect(at(20, 330, 621, 0.6f), RuleColor);
    textInRect(at(22, 340, 480, 14),
        drops.empty() ? Engine::tr("No drops yet this session: the filter is tried on the drops to come.")
                      : Engine::tr("Your last {count} drops: {filtered} filtered ({gold} gold), {kept} kept.",
                            {{"count", trial.drops}, {"filtered", trial.filtered},
                                {"gold", withThousands(trial.gold)}, {"kept", trial.drops - trial.filtered}}),
        TextFont, 9.5f, drops.empty() ? MutedColor : AmountColor);

    if (button("loot-done", at(531, 338, 110, 24), Engine::tr("Done"), "button") || keyPressed(SDL_SCANCODE_ESCAPE))
    {
        m_lootFilterOpen = false;
        m_lootFilterRules = false;
    }
}
}
