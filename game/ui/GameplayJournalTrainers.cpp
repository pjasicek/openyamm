#include "game/ui/GameplayJournalTrainers.h"

#include "engine/Localization.h"
#include "engine/Utf8Text.h"
#include "game/gameplay/GameplayInputFrame.h"
#include "game/gameplay/GameplayScreenRuntime.h"
#include "game/gameplay/MasteryTeacherDialog.h"
#include "game/gameplay/TrainerDirectory.h"
#include "game/party/Party.h"
#include "game/rules/GameRules.h"
#include "game/rules/SkillRules.h"
#include "game/tables/MapStats.h"
#include "game/ui/GameplayHudCommon.h"
#include "game/ui/GameplayJournalMapUi.h"
#include "game/ui/GameplayUiRuntime.h"
#include "game/ui/GameplayUiSkin.h"

#include <algorithm>
#include <array>
#include <chrono>
#include <cmath>
#include <cstdio>
#include <filesystem>
#include <memory>
#include <string>
#include <tuple>
#include <vector>

namespace OpenYAMM::Game
{
namespace
{
// The approved study's colours (journal_trainers_20261105 index.html), as ABGR.
constexpr uint32_t abgr(uint32_t rgb, uint32_t alpha = 0xff)
{
    return alpha << 24 | (rgb & 0xffu) << 16 | (rgb & 0xff00u) | (rgb >> 16 & 0xffu);
}

constexpr uint32_t Ink = abgr(0xe5dcc7);
constexpr uint32_t Heading = abgr(0xe4c793);
constexpr uint32_t Dim = abgr(0xa99f86);
constexpr uint32_t Brass = abgr(0xd9bd88);
constexpr uint32_t ButtonText = abgr(0xe8d1a4);
constexpr uint32_t ButtonHover = abgr(0xffe7b8);
constexpr uint32_t Placeholder = abgr(0x8f8670);
constexpr uint32_t WellFill = abgr(0x0b130d, 0xee);
constexpr uint32_t WellBorder = abgr(0x9f8d63, 0x85);
constexpr uint32_t RowHoverFill = abgr(0xc9a85e, 0x26);
constexpr uint32_t RowHoverBorder = abgr(0xb39a66, 0x99);
constexpr uint32_t MatchFill = abgr(0xc9a85e, 0x55);
constexpr uint32_t MoreFill = abgr(0x0e1710, 0xaa);
constexpr uint32_t MoreBorder = abgr(0x9f8d63, 0x99);
constexpr uint32_t MapFill = abgr(0x040704);
constexpr uint32_t MapBorder = abgr(0xa68f63, 0x6b);
constexpr uint32_t Marker = abgr(0xff5a3c);
constexpr uint32_t MarkerRim = abgr(0xfff4d6);
constexpr uint32_t LabelFill = abgr(0x0b120d, 0xee);
constexpr uint32_t LabelBorder = abgr(0xb39a66, 0xaa);
constexpr uint32_t SealGold = abgr(0xe0b860);
constexpr uint32_t SealRim = abgr(0x2b200c);
// The party creation screen's mastery colours: white Expert, turquoise Master, gold Grand Master.
constexpr std::array<uint32_t, 3> MasteryColours = {0xffe2ecf0u, 0xffccd88fu, 0xff4cc9f2u};
constexpr std::array<std::string_view, 3> MasteryNames = {Engine::trNoop("Expert"), Engine::trNoop("Master"),
    Engine::trNoop("Grand Master")};

// The mastery toggles' letters.
std::string masteryLetter(size_t index)
{
    return index == 0 ? Engine::trc("mastery letter", "E")
        : index == 1 ? Engine::trc("mastery letter", "M") : Engine::trc("mastery letter", "G");
}

constexpr char BodyFont[] = "AUTONOTE";
constexpr char LabelFont[] = "Create";
constexpr char ButtonFont[] = "Fondamento";
constexpr char NumberFont[] = "SMALLNUM";

// The layout in the page's logical units (364 x 360, JournalTrainerPage at the journal's (98, 92)).
constexpr float PageWidth = 364;
constexpr float ContentLeft = 3;
constexpr float ContentWidth = 358;
constexpr float TabTop = 0;
constexpr float TabHeight = 22;
constexpr float TabGap = 4;
constexpr float SearchTop = 27;
constexpr float SearchHeight = 20;
constexpr float ToggleWidth = 24;
constexpr float ToggleGap = 4;
constexpr float ListTop = 53;
constexpr float ListHeight = 257;
constexpr float SkillColumnWidth = 76;
constexpr float MasteryLeft = 82;
constexpr float NameLeft = 152;
constexpr float RowHeight = 14;
constexpr float BlockPad = 4;
constexpr float StatusTop = 316;
constexpr float StatusHeight = 24;
constexpr float PageNumberTop = 344;
constexpr float HeaderHeight = 20;
constexpr float CloseWidth = 60;
constexpr float MapLeft = 43;
constexpr float MapTop = 26;
constexpr float MapSize = 278;
// The Map view's frame (obsidian_journal_map_frame) is 325.6 around a 300 viewport.
constexpr float MapFrameRatio = 325.6f / 300.0f;

constexpr float RowText = 12.5f;
constexpr float SkillText = 13.5f;
constexpr float LabelText = 12.0f;
constexpr float ButtonTextHeight = 12.0f;

struct Rect
{
    float x = 0;
    float y = 0;
    float width = 0;
    float height = 0;

    bool contains(float pointX, float pointY) const
    {
        return pointX >= x && pointX < x + width && pointY >= y && pointY < y + height;
    }
};

Rect pageRect(const GameplayResolvedHudLayoutElement &page, float x, float y, float width, float height)
{
    return {page.x + x * page.scale, page.y + y * page.scale, width * page.scale, height * page.scale};
}

// The search matches the shown (translated) text, so it lowers every letter, not only ASCII ones.
std::string lowerCopy(const std::string &text)
{
    return Engine::Utf8::lower(text);
}

std::vector<std::string> searchWords(const std::string &search)
{
    std::vector<std::string> words;
    std::string word;

    for (const char c : lowerCopy(search) + " ")
    {
        if (c == ' ')
        {
            if (!word.empty())
            {
                words.push_back(word);
            }

            word.clear();
        }
        else
        {
            word += c;
        }
    }

    return words;
}

size_t masteryIndex(SkillMastery mastery)
{
    return size_t(std::clamp(int(mastery) - int(SkillMastery::Expert), 0, 2));
}

float fontScale(const GameplayScreenRuntime &context, const std::string &font, float logicalHeight, float scale)
{
    const int height = std::max(1, context.hudFontHeight(font));
    const float wanted = logicalHeight * scale / float(height);
    return wanted >= 1.0f ? GameplayHudCommon::snappedHudFontScale(wanted) : std::max(0.5f, wanted);
}

// One line of the list: a trainer, or under MAW a skill that gains the mastery by level alone.
struct FinderRow
{
    const TrainerEntry *pEntry = nullptr;
    std::string skillName;
    SkillMastery mastery = SkillMastery::None;
    std::string name;
    std::string town;
};

// A skill with its rows, or a message (nothing found, the ledger line).
struct FinderBlock
{
    std::string skillName;
    std::vector<std::string> skillLines;
    std::vector<FinderRow> rows;
    std::vector<std::string> messageLines;
    bool ledgerLine = false;
    float height = 0;
};

struct FinderModel
{
    uint32_t continent = 0;
    std::string continentName;
    bool ledger = false;
    size_t trainerRows = 0;
    std::vector<FinderBlock> blocks;
    // Each page's blocks, by index.
    std::vector<std::vector<size_t>> pages;
};

uint32_t shownContinent(const GameplayScreenRuntime &context, const GameplayUiController::JournalScreenState &journal)
{
    if (journal.trainerContinent != 0)
    {
        return journal.trainerContinent;
    }

    const MapStatsEntry *pMap = context.mapStats().findByFileName(context.currentMapFileName());
    const uint32_t continent = pMap != nullptr ? pMap->mergedContinentId : 0;
    return std::find(TrainerContinents.begin(), TrainerContinents.end(), continent) != TrainerContinents.end()
        ? continent
        : TrainerContinents.front();
}

// Where the list says the trainer is: the outdoor map with the door, or the dungeon or castle.
std::string trainerTown(const TrainerEntry &entry)
{
    if (entry.place && entry.place->kind == TrainerPlaceKind::Door && !entry.markerMapName.empty())
    {
        return Engine::localize(entry.markerMapName);
    }

    return Engine::localize(entry.mapName);
}

std::string trainerHouse(const TrainerEntry &entry)
{
    if (entry.rudeId != 0)
        return Engine::localize(entry.name);
    return entry.houseName.empty() ? Engine::tr("{name}'s home", {{"name", Engine::localize(entry.name)}})
                                   : Engine::localize(entry.houseName);
}

// The house and the map it stands on, as the list shows them.
std::string trainerPlace(const TrainerEntry &entry)
{
    const std::string map = Engine::localize(entry.mapName);
    return entry.houseName.empty() ? map : Engine::localize(entry.houseName) + ", " + map;
}

// What the teacher asks: the skill level, the price (the ruleset's, for the active member) and the mastery before.
std::string requirementText(const Party &party, const TrainerEntry &entry)
{
    const SkillRules &skills = party.rules().skills;
    const uint32_t level = std::max(entry.requiredSkill, skills.masteryRequiredLevel(entry.skill, entry.mastery));
    int price = entry.requiredGold != 0 ? int(entry.requiredGold) : masteryTeacherStandardCost(entry.skill,
        entry.mastery);

    if (const Character *pMember = party.activeMember())
    {
        price = skills.masteryTeacherCost(*pMember, entry.skill, entry.mastery, price);
    }

    std::string text = Engine::tr("skill {level}", {{"level", level}});

    if (price > 0)
    {
        text += ", " + Engine::tr("{price} gold", {{"price", price}});
    }

    if (entry.mastery > SkillMastery::Expert)
    {
        text += ", "
            + Engine::tr("{mastery} first", {{"mastery", Engine::tr(MasteryNames[masteryIndex(entry.mastery) - 1])}});
    }

    return text;
}

class Painter
{
public:
    Painter(GameplayScreenRuntime &context, const GameplayResolvedHudLayoutElement &page)
        : m_context(context)
        , m_page(page)
    {
    }

    void fill(const Rect &rect, uint32_t colour) const
    {
        if (rect.width <= 0 || rect.height <= 0)
        {
            return;
        }

        if (const std::optional<GameplayHudTextureHandle> texture = solid(colour))
        {
            m_context.submitHudTexturedQuad(*texture, rect.x, rect.y, rect.width, rect.height);
        }
    }

    void frame(const Rect &rect, uint32_t colour) const
    {
        const float line = std::max(1.0f, std::round(m_page.scale * 0.75f));
        fill({rect.x, rect.y, rect.width, line}, colour);
        fill({rect.x, rect.y + rect.height - line, rect.width, line}, colour);
        fill({rect.x, rect.y, line, rect.height}, colour);
        fill({rect.x + rect.width - line, rect.y, line, rect.height}, colour);
    }

    void texture(const std::string &name, const Rect &rect) const
    {
        if (const std::optional<GameplayHudTextureHandle> handle =
                m_context.gameplayUiRuntime().ensureHudTextureLoaded(name))
        {
            m_context.submitHudTexturedQuad(*handle, rect.x, rect.y, rect.width, rect.height);
        }
    }

    float width(const std::string &font, float height, const std::string &value) const
    {
        return m_context.measureHudTextWidth(font, value) * fontScale(m_context, font, height, m_page.scale)
            / m_page.scale;
    }

    // Text with its top left at page units (x, y); align 0 left, 1 centred on x, 2 ending at x. Returns its width.
    float text(const std::string &font, float height, uint32_t colour, const std::string &value, float x, float y,
        int align = 0) const
    {
        const float scale = fontScale(m_context, font, height, m_page.scale);
        const float textWidth = m_context.measureHudTextWidth(font, value) * scale;
        float left = m_page.x + x * m_page.scale;
        left -= align == 1 ? textWidth / 2 : align == 2 ? textWidth : 0;
        m_context.renderHudTextLine(font, colour, value, std::round(left), std::round(m_page.y + y * m_page.scale),
            scale);
        return textWidth / m_page.scale;
    }

    // As text, with the search's words marked behind it.
    float marked(const std::string &font, float height, uint32_t colour, const std::string &value, float x, float y,
        const std::vector<std::string> &words, int align = 0) const
    {
        const float total = width(font, height, value);
        const float left = x - (align == 1 ? total / 2 : align == 2 ? total : 0);
        const std::string lower = lowerCopy(value);

        for (const std::string &word : words)
        {
            const size_t at = lower.find(word);

            if (at != std::string::npos)
            {
                const float start = width(font, height, value.substr(0, at));
                const float span = width(font, height, value.substr(at, word.size()));
                fill(rect(left + start - 0.5f, y - 1, span + 1, height + 2), MatchFill);
            }
        }

        return text(font, height, colour, value, left, y);
    }

    std::string fitted(const std::string &font, float height, const std::string &value, float maxWidth) const
    {
        if (width(font, height, value) <= maxWidth)
        {
            return value;
        }

        std::string result = value;

        while (result.size() > 1)
        {
            // A whole character: shown names may be translated into letters of several bytes.
            Engine::Utf8::popBack(result);

            while (!result.empty() && result.back() == ' ')
            {
                result.pop_back();
            }

            if (width(font, height, result + "...") <= maxWidth)
            {
                return result + "...";
            }
        }

        return result;
    }

    std::vector<std::string> wrapped(const std::string &font, float height, const std::string &value,
        float maxWidth) const
    {
        const float scale = fontScale(m_context, font, height, m_page.scale);
        return m_context.wrapHudTextToWidth(font, value, maxWidth * m_page.scale / scale);
    }

    Rect rect(float x, float y, float width, float height) const
    {
        return pageRect(m_page, x, y, width, height);
    }

    void disc(float cx, float cy, float radius, uint32_t colour) const
    {
        if (const std::optional<GameplayHudTextureHandle> texture = solid(colour))
        {
            m_context.gameplayUiRuntime().submitHudTexturedEllipse(texture->textureHandle,
                m_page.x + (cx - radius) * m_page.scale, m_page.y + (cy - radius) * m_page.scale,
                2 * radius * m_page.scale, 2 * radius * m_page.scale);
        }
    }

    // A circle outline of `segments` lines in page units.
    void ring(float cx, float cy, float radius, uint32_t colour, float lineWidth, int segments = 28) const
    {
        const std::optional<GameplayHudTextureHandle> texture = solid(colour);

        if (!texture || radius <= 0)
        {
            return;
        }

        std::vector<GameplayHudBatchQuad> quads;

        for (int step = 0; step < segments; ++step)
        {
            const float a = 6.2831853f * float(step) / float(segments);
            const float b = 6.2831853f * float(step + 1) / float(segments);
            GameplayHudBatchQuad quad;
            quad.textureHandle = texture->textureHandle;
            quad.line = true;
            quad.width = std::max(1.0f, lineWidth * m_page.scale);
            quad.x = m_page.x + (cx + radius * std::cos(a)) * m_page.scale;
            quad.y = m_page.y + (cy + radius * std::sin(a)) * m_page.scale;
            quad.x2 = m_page.x + (cx + radius * std::cos(b)) * m_page.scale;
            quad.y2 = m_page.y + (cy + radius * std::sin(b)) * m_page.scale;
            quads.push_back(quad);
        }

        m_context.submitHudQuadBatch(quads);
    }

    void line(float x1, float y1, float x2, float y2, uint32_t colour, float lineWidth) const
    {
        const std::optional<GameplayHudTextureHandle> texture = solid(colour);

        if (!texture)
        {
            return;
        }

        GameplayHudBatchQuad quad;
        quad.textureHandle = texture->textureHandle;
        quad.line = true;
        quad.width = std::max(1.0f, lineWidth * m_page.scale);
        quad.x = m_page.x + x1 * m_page.scale;
        quad.y = m_page.y + y1 * m_page.scale;
        quad.x2 = m_page.x + x2 * m_page.scale;
        quad.y2 = m_page.y + y2 * m_page.scale;
        m_context.submitHudQuadBatch({quad});
    }

    // An Obsidian tab plate with a centred Fondamento label (the Lloyd's Beacon tabs' plates).
    void button(const Rect &area, const std::string &label, bool selected, bool hovered, bool pressed,
        uint32_t labelColour = ButtonText) const
    {
        texture(pressed ? "obsidian_button_tab_pressed" : hovered ? "obsidian_button_tab_hover"
            : selected ? "obsidian_button_tab_selected" : "obsidian_button_tab_normal", area);
        const float x = (area.x - m_page.x) / m_page.scale + area.width / m_page.scale / 2;
        const float y = (area.y - m_page.y) / m_page.scale + (area.height / m_page.scale - ButtonTextHeight) / 2
            + (pressed ? 1.0f : 0.0f);
        text(ButtonFont, ButtonTextHeight, hovered ? ButtonHover : labelColour, label, x, y, 1);
    }

private:
    std::optional<GameplayHudTextureHandle> solid(uint32_t colour) const
    {
        char name[48] = {};
        std::snprintf(name, sizeof(name), "__journal_trainers_%08x", colour);
        return m_context.gameplayUiRuntime().ensureSolidHudTextureLoaded(name, colour);
    }

    GameplayScreenRuntime &m_context;
    const GameplayResolvedHudLayoutElement &m_page;
};

Rect tabRect(const GameplayResolvedHudLayoutElement &page, size_t index, size_t count = TrainerContinents.size())
{
    const float width = (ContentWidth - float(count - 1) * TabGap) / float(count);
    return pageRect(page, ContentLeft + index * (width + TabGap), TabTop, width, TabHeight);
}

Rect toggleRect(const GameplayResolvedHudLayoutElement &page, size_t index)
{
    const float left = ContentLeft + ContentWidth - 3 * ToggleWidth - 2 * ToggleGap;
    return pageRect(page, left + index * (ToggleWidth + ToggleGap), SearchTop, ToggleWidth, SearchHeight);
}

Rect searchRect(const GameplayResolvedHudLayoutElement &page)
{
    return pageRect(page, ContentLeft, SearchTop, ContentWidth - 3 * ToggleWidth - 2 * ToggleGap - 6, SearchHeight);
}

Rect closeRect(const GameplayResolvedHudLayoutElement &page)
{
    return pageRect(page, ContentLeft + ContentWidth - CloseWidth, 0, CloseWidth, HeaderHeight);
}

Rect mapRect(const GameplayResolvedHudLayoutElement &page)
{
    return pageRect(page, MapLeft, MapTop, MapSize, MapSize);
}

// The outdoor map transform of MM6-MM8 maps (OutdoorWorldRuntime::tryGetGameplayMinimapState), images square.
GameplayMinimapState trainerMinimapState(const GameplayUiController::JournalScreenState &journal)
{
    GameplayMinimapState state;
    if (journal.trainerShown && journal.trainerShown->mapPresentation)
    {
        const TrainerEntry &entry = *journal.trainerShown;
        applyMapPresentationToMinimapState(*entry.mapPresentation, entry.z, state);
    }
    return state;
}

GameplayJournalMapView trainerMapView(const GameplayUiController::JournalScreenState &journal)
{
    GameplayJournalMapView view = {journal.trainerMapZoomStep, journal.trainerMapCenterX, journal.trainerMapCenterY};
    clampGameplayJournalMapView(view, trainerMinimapState(journal));
    return view;
}

FinderModel buildModel(
    const GameplayScreenRuntime &context,
    const GameplayUiController::JournalScreenState &journal,
    const Painter &paint)
{
    FinderModel model;
    model.continent = shownContinent(context, journal);
    model.continentName = Engine::localizeKnown(trainerContinentName(model.continent));
    const Party *pParty = context.partyReadOnly();

    if (pParty == nullptr || pParty->trainerDirectory() == nullptr)
    {
        FinderBlock block;
        block.messageLines = {Engine::tr("The trainer list is not available.")};
        block.height = RowHeight + 2 * BlockPad;
        model.blocks.push_back(block);
        model.pages = {{0}};
        return model;
    }

    const Party &party = *pParty;
    const TrainerDirectory &directory = party.trainerDirectory()->forParty(party);
    model.ledger = party.hasTeacherLedger(model.continent);
    const std::vector<std::string> words = searchWords(journal.notesSearch);
    const SkillMastery masteryFilter = SkillMastery(journal.trainerMastery);
    const auto matches = [&journal, masteryFilter](const FinderRow &row, const std::string &house,
        const std::string &map)
    {
        return (masteryFilter == SkillMastery::None || row.mastery == masteryFilter)
            && trainerSearchMatches(journal.notesSearch,
                {row.skillName, Engine::tr(MasteryNames[masteryIndex(row.mastery)]),
                    Engine::tr(masteryDisplayName(row.mastery)), row.name, row.town, house, map});
    };

    std::vector<FinderRow> rows;
    size_t known = 0;

    for (const auto &[skill, masteries] : directory.skills())
    {
        for (const std::vector<TrainerEntry> &entries : masteries)
        {
            for (const TrainerEntry &entry : entries)
            {
                if (entry.continent != model.continent)
                {
                    continue;
                }

                ++model.trainerRows;

                if (!trainerKnown(entry, party))
                {
                    continue;
                }

                ++known;
                FinderRow row;
                row.pEntry = &entry;
                // The search matches what the list shows.
                row.skillName = Engine::localize(displaySkillName(entry.skill));
                row.mastery = entry.mastery;
                row.name = Engine::localize(entry.name);
                row.town = trainerTown(entry);

                if (matches(row, Engine::localize(entry.houseName), Engine::localize(entry.mapName)))
                {
                    rows.push_back(std::move(row));
                }
            }
        }
    }

    // The ruleset's skills that gain their masteries by level (MAW), on every continent.
    for (const auto &[skill, levels] : party.rules().skills.teacherlessMasteryLadders())
    {
        for (size_t index = 0; index < levels.size(); ++index)
        {
            FinderRow row;
            row.skillName = Engine::localize(displaySkillName(skill));
            row.mastery = SkillMastery(int(SkillMastery::Expert) + int(index));
            row.name = Engine::tr("learned at skill {level}", {{"level", levels[index]}});
            row.town = Engine::tr("no trainer");

            if (matches(row, {}, {}))
            {
                rows.push_back(std::move(row));
            }
        }
    }

    std::sort(rows.begin(), rows.end(), [](const FinderRow &left, const FinderRow &right)
    {
        return std::tie(left.skillName, left.mastery, left.name, left.town)
            < std::tie(right.skillName, right.mastery, right.name, right.town);
    });

    for (FinderRow &row : rows)
    {
        if (model.blocks.empty() || model.blocks.back().skillName != row.skillName
            || model.blocks.back().rows.size() >= 16)
        {
            FinderBlock block;
            block.skillName = row.skillName;
            block.skillLines = paint.wrapped(BodyFont, SkillText, row.skillName, SkillColumnWidth);
            model.blocks.push_back(std::move(block));
        }

        model.blocks.back().rows.push_back(std::move(row));
    }

    for (FinderBlock &block : model.blocks)
    {
        block.height = std::max(float(block.rows.size()) * RowHeight, float(block.skillLines.size()) * (SkillText + 1))
            + 2 * BlockPad;
    }

    const auto addMessage = [&](const std::string &text, bool ledgerLine)
    {
        FinderBlock block;
        block.messageLines = paint.wrapped(BodyFont, RowText, text, ContentWidth - 16);
        block.ledgerLine = ledgerLine;
        block.height = float(block.messageLines.size()) * (RowText + 1.5f) + 12 + BlockPad;
        model.blocks.push_back(std::move(block));
    };

    if (rows.empty())
    {
        addMessage(!words.empty() || masteryFilter != SkillMastery::None
                ? Engine::tr("No trainer you know on {continent} matches.", {{"continent", model.continentName}})
                : Engine::tr("You have not found any trainer on {continent} yet.",
                    {{"continent", model.continentName}}),
            false);
    }

    if (!model.ledger)
    {
        addMessage(Engine::tr("You have found {known} of the {count} trainers on {continent}. The Ledger of Teachers "
                              "names them all: ask for it in any tavern on {continent}.",
                       {{"known", known}, {"count", model.trainerRows}, {"continent", model.continentName}}),
            true);
    }

    float used = 0;
    model.pages.emplace_back();

    for (size_t index = 0; index < model.blocks.size(); ++index)
    {
        if (used + model.blocks[index].height > ListHeight && !model.pages.back().empty())
        {
            model.pages.emplace_back();
            used = 0;
        }

        model.pages.back().push_back(index);
        used += model.blocks[index].height;
    }

    return model;
}

struct PlacedRow
{
    const FinderRow *pRow = nullptr;
    Rect area;
    float y = 0;
};

// The rows of the shown page and where each is, in page units (area in screen pixels).
std::vector<PlacedRow> placeRows(
    const FinderModel &model,
    size_t pageIndex,
    const GameplayResolvedHudLayoutElement &page)
{
    std::vector<PlacedRow> placed;

    if (pageIndex >= model.pages.size())
    {
        return placed;
    }

    float y = ListTop;

    for (size_t blockIndex : model.pages[pageIndex])
    {
        const FinderBlock &block = model.blocks[blockIndex];

        for (size_t row = 0; row < block.rows.size(); ++row)
        {
            const float rowY = y + BlockPad + float(row) * RowHeight;
            placed.push_back({&block.rows[row],
                pageRect(page, MasteryLeft - 4, rowY - 1, ContentLeft + ContentWidth - MasteryLeft + 4, RowHeight),
                rowY});
        }

        y += block.height;
    }

    return placed;
}

size_t clampedPage(const FinderModel &model, size_t page)
{
    return model.pages.empty() ? 0 : std::min(page, model.pages.size() - 1);
}

std::string statusForMap(const TrainerEntry &entry)
{
    const std::string place = trainerPlace(entry);

    if (entry.place && entry.place->kind == TrainerPlaceKind::Entrance)
    {
        return place + " \xB7 "
            + Engine::tr("inside, through the marked entrance on {map}",
                {{"map", Engine::localize(entry.markerMapName)}});
    }

    if (entry.place && entry.place->kind == TrainerPlaceKind::Door && !entry.markerMapName.empty()
        && entry.markerMapName != entry.mapName)
    {
        return place + " \xB7 " + Engine::localize(entry.markerMapName);
    }

    return place;
}

void renderStatus(const Painter &paint, const std::string &text)
{
    paint.texture("obsidian_journal_note_bar", paint.rect(0, StatusTop, PageWidth, StatusHeight));
    paint.text(LabelFont, LabelText + 1, Ink, paint.fitted(LabelFont, LabelText + 1, text, PageWidth - 16), 8,
        StatusTop + (StatusHeight - LabelText - 1) / 2);
}

void renderMap(
    GameplayScreenRuntime &context,
    GameplayUiController::JournalScreenState &journal,
    const GameplayResolvedHudLayoutElement &page,
    const Painter &paint,
    float pointerX,
    float pointerY,
    bool leftHeld)
{
    const TrainerEntry &entry = *journal.trainerShown;

    // The header: the lesson and the teacher, and Close.
    const std::string lesson = Engine::tr("{mastery} {skill}",
        {{"mastery", Engine::tr(MasteryNames[masteryIndex(entry.mastery)])},
            {"skill", Engine::localize(displaySkillName(entry.skill))}});
    const float headerY = (HeaderHeight - SkillText) / 2;
    const float lessonWidth = paint.text(BodyFont, SkillText, Heading, lesson, ContentLeft + 2, headerY);
    paint.text(BodyFont, SkillText, Ink,
        paint.fitted(BodyFont, SkillText, " \xB7 " + Engine::localize(entry.name),
            ContentWidth - CloseWidth - lessonWidth - 10),
        ContentLeft + 2 + lessonWidth, headerY);
    const Rect close = closeRect(page);
    const bool closeHovered = close.contains(pointerX, pointerY);
    paint.button(close, Engine::tr("Close"), false, closeHovered, closeHovered && leftHeld);

    // The map, framed as the Map view's.
    const Rect area = mapRect(page);
    const float frameSize = MapSize * MapFrameRatio;
    paint.fill(area, MapFill);
    const std::string mapStem = entry.place
        ? std::filesystem::path(entry.place->markerMapFileName).stem().string() : std::string();
    const GameplayMinimapState state = trainerMinimapState(journal);
    const std::string texture = state.textureName.empty() ? mapStem : state.textureName;
    const std::optional<GameplayHudTextureHandle> image = texture.empty()
        ? std::nullopt : context.gameplayUiRuntime().ensureHudTextureLoaded(texture);

    if (image && entry.place->kind != TrainerPlaceKind::Indoor)
    {
        // The shown view keeps to the image; the stored centre stays where the marker or the drag put it.
        const GameplayJournalMapView view = trainerMapView(journal);
        const GameplayJournalMapTransform transform =
            gameplayJournalMapTransform(view, &state, area.width, area.height);
        // The whole image's place on screen, clipped to the viewport.
        const float imageLeft = area.x - transform.uOrigin / transform.uSpan * area.width;
        const float imageTop = area.y - transform.vOrigin / transform.vSpan * area.height;
        const float imageWidth = area.width / transform.uSpan;
        const float imageHeight = area.height / transform.vSpan;
        const float left = std::max(area.x, imageLeft);
        const float top = std::max(area.y, imageTop);
        const float right = std::min(area.x + area.width, imageLeft + imageWidth);
        const float bottom = std::min(area.y + area.height, imageTop + imageHeight);

        if (left < right && top < bottom)
        {
            context.submitWorldTextureQuad(image->textureHandle, left, top, right - left, bottom - top,
                (left - imageLeft) / imageWidth, (top - imageTop) / imageHeight, (right - imageLeft) / imageWidth,
                (bottom - imageTop) / imageHeight);
        }

        const GameplayJournalMapPoint point = gameplayJournalWorldToScreen(entry.place->x, entry.place->y, area.x,
            area.y, area.width, area.height, view, &state);

        if (area.contains(point.x, point.y))
        {
            const float cx = (point.x - page.x) / page.scale;
            const float cy = (point.y - page.y) / page.scale;
            // A ring widening and fading every 1.6 seconds around a dot.
            const double seconds = std::chrono::duration<double>(
                std::chrono::steady_clock::now().time_since_epoch()).count();
            const float phase = float(std::fmod(seconds, 1.6) / 1.6);
            const uint32_t ringAlpha = uint32_t(std::lround(242.0f * (1.0f - phase)));
            paint.ring(cx, cy, 13.9f * (0.4f + 0.85f * phase), (Marker & 0x00ffffffu) | ringAlpha << 24, 1.6f);
            paint.disc(cx, cy, 7.2f, abgr(0x000000, 0xaa));
            paint.disc(cx, cy, 6.2f, MarkerRim);
            paint.disc(cx, cy, 4.6f, Marker);

            const std::string fullLabel = entry.place->kind == TrainerPlaceKind::Entrance
                ? Engine::tr("Entrance: {map}", {{"map", Engine::localize(entry.mapName)}}) : trainerHouse(entry);
            const std::string label = paint.fitted(LabelFont, LabelText, fullLabel, MapSize - 14);
            const float labelWidth = paint.width(LabelFont, LabelText, label) + 10;
            const float labelHeight = LabelText + 6;
            const float labelX = std::clamp(cx - labelWidth / 2, MapLeft + 2, MapLeft + MapSize - labelWidth - 2);
            const float labelY = cy - 12 - labelHeight >= MapTop + 2 ? cy - 12 - labelHeight : cy + 12;
            paint.fill(paint.rect(labelX, labelY, labelWidth, labelHeight), LabelFill);
            paint.frame(paint.rect(labelX, labelY, labelWidth, labelHeight), LabelBorder);
            paint.text(LabelFont, LabelText, Ink, label, labelX + 5, labelY + 3);
        }
    }
    else
    {
        paint.text(BodyFont, RowText, Dim, trainerPlace(entry), MapLeft + MapSize / 2, MapTop + MapSize / 2 - RowText,
            1);
        paint.text(BodyFont, RowText, Dim, Engine::tr("No map of this place yet."), MapLeft + MapSize / 2,
            MapTop + MapSize / 2 + 2, 1);
    }

    paint.frame(area, MapBorder);
    paint.texture("obsidian_journal_map_frame", paint.rect(MapLeft - (frameSize - MapSize) / 2,
        MapTop - (frameSize - MapSize) / 2, frameSize, frameSize));
    renderStatus(paint, statusForMap(entry));
}
}

bool journalOwnerTabsShown(const GameplayUiController::JournalScreenState &journal)
{
    return journal.view == GameplayUiController::JournalView::Quests
        || (journal.view == GameplayUiController::JournalView::Notes
            && journal.notesCategory != GameplayUiController::JournalNotesCategory::Trainer
            && journal.notesCategory != GameplayUiController::JournalNotesCategory::Arcomage);
}

std::string journalOwner(const GameplayScreenRuntime &context,
    const GameplayUiController::JournalScreenState &journal)
{
    uint32_t continent = journal.view == GameplayUiController::JournalView::Quests
        ? journal.questContinent : journal.notesContinent;
    if (continent == 0 && journal.view == GameplayUiController::JournalView::Notes
        && journal.notesCategory == GameplayUiController::JournalNotesCategory::Potion)
        return "Shared";
    if (continent == 0)
    {
        const MapStatsEntry *map = context.mapStats().findByFileName(context.currentMapFileName());
        continent = map != nullptr ? map->mergedContinentId : 4;
    }
    const std::string name = trainerContinentName(continent);
    return name.empty() ? "Shared" : name;
}

uint32_t journalOwnerTargetAt(const GameplayResolvedHudLayoutElement &page, float x, float y)
{
    for (size_t i = 0; i < 5; ++i)
        if (tabRect(page, i, 5).contains(x, y))
            return i < TrainerContinents.size() ? TrainerContinents[i] : 4;
    return 0;
}

void renderJournalOwners(GameplayScreenRuntime &context, const GameplayUiController::JournalScreenState &journal,
    const GameplayResolvedHudLayoutElement &page, float x, float y)
{
    Painter paint(context, page);
    const std::string selected = journalOwner(context, journal);
    for (size_t i = 0; i < 5; ++i)
    {
        const std::string name = i < TrainerContinents.size() ? trainerContinentName(TrainerContinents[i]) : "Shared";
        const Rect tab = tabRect(page, i, 5);
        paint.button(tab, name == "Shared" ? Engine::tr("Shared") : Engine::localizeKnown(name),
            name == selected, tab.contains(x, y), false);
    }
}

uint32_t packJournalTrainerTarget(const JournalTrainerTarget &target)
{
    return uint32_t(target.kind) << 24 | uint32_t(target.index & 0xffffffu);
}

JournalTrainerTarget unpackJournalTrainerTarget(uint32_t packed)
{
    return {JournalTrainerTargetKind(packed >> 24), size_t(packed & 0xffffffu)};
}

bool journalTrainersShown(const GameplayUiController::JournalScreenState &journal)
{
    return journal.view == GameplayUiController::JournalView::Notes
        && journal.notesCategory == GameplayUiController::JournalNotesCategory::Trainer;
}

bool journalTrainerMapShown(const GameplayUiController::JournalScreenState &journal)
{
    return journalTrainersShown(journal) && journal.trainerShown != nullptr;
}

void openJournalTrainers(const GameplayScreenRuntime &, GameplayUiController::JournalScreenState &journal)
{
    journal.trainerContinent = 0;
    journal.trainerPage = 0;
    journal.trainerShown.reset();
}

JournalTrainerTarget journalTrainerTargetAt(
    const GameplayScreenRuntime &context,
    const GameplayUiController::JournalScreenState &journal,
    const GameplayResolvedHudLayoutElement &page,
    float x,
    float y)
{
    if (journalTrainerMapShown(journal))
    {
        if (closeRect(page).contains(x, y))
        {
            return {JournalTrainerTargetKind::CloseMap, 0};
        }

        return mapRect(page).contains(x, y) ? JournalTrainerTarget{JournalTrainerTargetKind::Map, 0}
                                            : JournalTrainerTarget{};
    }

    for (size_t index = 0; index < TrainerContinents.size(); ++index)
    {
        if (tabRect(page, index).contains(x, y))
        {
            return {JournalTrainerTargetKind::Continent, index};
        }

        if (index < 3 && toggleRect(page, index).contains(x, y))
        {
            return {JournalTrainerTargetKind::Mastery, index};
        }
    }

    if (searchRect(page).contains(x, y))
    {
        return {JournalTrainerTargetKind::Search, 0};
    }

    if (!pageRect(page, 0, ListTop, PageWidth, ListHeight).contains(x, y))
    {
        return {};
    }

    // The model needs the fonts, which only a renderable context has.
    GameplayScreenRuntime &mutableContext = const_cast<GameplayScreenRuntime &>(context);
    const Painter paint(mutableContext, page);
    const FinderModel model = buildModel(context, journal, paint);
    const std::vector<PlacedRow> rows = placeRows(model, clampedPage(model, journal.trainerPage), page);

    for (size_t index = 0; index < rows.size(); ++index)
    {
        if (rows[index].pRow->pEntry != nullptr && rows[index].area.contains(x, y))
        {
            return {JournalTrainerTargetKind::Row, index};
        }
    }

    return {};
}

void activateJournalTrainerTarget(
    const GameplayScreenRuntime &context,
    GameplayUiController::JournalScreenState &journal,
    const GameplayResolvedHudLayoutElement &page,
    const JournalTrainerTarget &target)
{
    switch (target.kind)
    {
        case JournalTrainerTargetKind::Continent:
            journal.trainerContinent = TrainerContinents[std::min(target.index, TrainerContinents.size() - 1)];
            journal.trainerPage = 0;
            break;
        case JournalTrainerTargetKind::Mastery:
        {
            const uint8_t mastery = uint8_t(int(SkillMastery::Expert) + int(std::min<size_t>(target.index, 2)));
            journal.trainerMastery = journal.trainerMastery == mastery ? 0 : mastery;
            journal.trainerPage = 0;
            break;
        }
        case JournalTrainerTargetKind::Search:
            journal.notesSearchActive = true;
            break;
        case JournalTrainerTargetKind::Row:
        {
            GameplayScreenRuntime &mutableContext = const_cast<GameplayScreenRuntime &>(context);
            const Painter paint(mutableContext, page);
            const FinderModel model = buildModel(context, journal, paint);
            const std::vector<PlacedRow> rows = placeRows(model, clampedPage(model, journal.trainerPage), page);

            if (target.index < rows.size() && rows[target.index].pRow->pEntry != nullptr)
            {
                const TrainerEntry &entry = *rows[target.index].pRow->pEntry;
                journal.trainerShown = std::make_shared<const TrainerEntry>(entry);
                journal.trainerMapZoomStep = 0;
                journal.trainerMapCenterX = entry.place ? entry.place->x : 0.0f;
                journal.trainerMapCenterY = entry.place ? entry.place->y : 0.0f;
            }

            break;
        }
        case JournalTrainerTargetKind::CloseMap:
            journal.trainerShown.reset();
            break;
        case JournalTrainerTargetKind::Map:
        case JournalTrainerTargetKind::None:
            break;
    }
}

void turnJournalTrainerPage(GameplayUiController::JournalScreenState &journal, int delta)
{
    if (delta < 0 && journal.trainerPage > 0)
    {
        --journal.trainerPage;
    }
    else if (delta > 0)
    {
        // The renderer clamps it to the last page.
        ++journal.trainerPage;
    }
}

void zoomJournalTrainerMap(GameplayUiController::JournalScreenState &journal, int delta)
{
    // About the stored centre (the marker until a drag), which the shown view keeps to the image.
    journal.trainerMapZoomStep =
        std::clamp(journal.trainerMapZoomStep + delta, 0, int(GameplayJournalMapZoomLevels.size()) - 1);
}

void dragJournalTrainerMap(
    GameplayUiController::JournalScreenState &journal,
    const GameplayResolvedHudLayoutElement &page,
    float startCenterX,
    float startCenterY,
    float deltaX,
    float deltaY)
{
    const Rect area = mapRect(page);
    const GameplayMinimapState state = trainerMinimapState(journal);
    GameplayJournalMapView start = {journal.trainerMapZoomStep, startCenterX, startCenterY};
    clampGameplayJournalMapView(start, state);
    const GameplayJournalMapTransform transform = gameplayJournalMapTransform(start, &state, area.width, area.height);
    const float centerU = transform.uOrigin + transform.uSpan * 0.5f - deltaX * transform.uSpan / area.width;
    const float centerV = transform.vOrigin + transform.vSpan * 0.5f - deltaY * transform.vSpan / area.height;
    const GameplayMinimapPoint center = gameplayMinimapUvToWorld(state, centerU, centerV);
    GameplayJournalMapView view = {journal.trainerMapZoomStep, center.x, center.y};
    clampGameplayJournalMapView(view, state);
    journal.trainerMapCenterX = view.centerX;
    journal.trainerMapCenterY = view.centerY;
}

size_t journalTrainerPageCount(
    const GameplayScreenRuntime &context,
    const GameplayUiController::JournalScreenState &journal,
    const GameplayResolvedHudLayoutElement &page)
{
    GameplayScreenRuntime &mutableContext = const_cast<GameplayScreenRuntime &>(context);
    const Painter paint(mutableContext, page);
    return buildModel(context, journal, paint).pages.size();
}

void renderJournalTrainers(
    GameplayScreenRuntime &context,
    GameplayUiController::JournalScreenState &journal,
    const GameplayResolvedHudLayoutElement &page,
    int screenWidth,
    int screenHeight,
    float pointerX,
    float pointerY)
{
    const Painter paint(context, page);
    const GameplayInputFrame *pInput = context.currentGameplayInputFrame();
    const bool leftHeld = pInput != nullptr && pInput->leftMouseButton.held;

    if (journalTrainerMapShown(journal))
    {
        const int maxZoom = int(GameplayJournalMapZoomLevels.size()) - 1;
        GameplayUiSkin::renderButton(context, "JournalMapZoomInButton", screenWidth, screenHeight, false,
            journal.trainerMapZoomStep < maxZoom);
        GameplayUiSkin::renderButton(context, "JournalMapZoomOutButton", screenWidth, screenHeight, false,
            journal.trainerMapZoomStep > 0);
        renderMap(context, journal, page, paint, pointerX, pointerY, leftHeld);
        return;
    }

    const FinderModel model = buildModel(context, journal, paint);
    journal.trainerPage = clampedPage(model, journal.trainerPage);
    GameplayUiSkin::renderButton(context, "JournalPrevPageButton", screenWidth, screenHeight, false,
        journal.trainerPage > 0);
    GameplayUiSkin::renderButton(context, "JournalNextPageButton", screenWidth, screenHeight, false,
        journal.trainerPage + 1 < model.pages.size());
    const Party *pParty = context.partyReadOnly();

    // The continents, a seal on those whose ledger the party has.
    for (size_t index = 0; index < TrainerContinents.size(); ++index)
    {
        const uint32_t continent = TrainerContinents[index];
        const Rect tab = tabRect(page, index);
        const bool hovered = tab.contains(pointerX, pointerY);
        paint.button(tab, Engine::localizeKnown(trainerContinentName(continent)), continent == model.continent, hovered,
            hovered && leftHeld);

        if (pParty != nullptr && pParty->hasTeacherLedger(continent))
        {
            const float cx = (tab.x - page.x) / page.scale + 9;
            const float cy = (tab.y - page.y) / page.scale + TabHeight / 2;
            paint.disc(cx, cy, 5.2f, SealRim);
            paint.disc(cx, cy, 4.2f, SealGold);
            paint.disc(cx - 1.2f, cy - 1.2f, 1.6f, abgr(0xf6dc96));
        }
    }

    // The search well and the mastery toggles.
    const Rect search = searchRect(page);
    paint.fill(search, WellFill);
    paint.frame(search, journal.notesSearchActive ? Brass : WellBorder);
    const float searchX = (search.x - page.x) / page.scale;
    const float searchY = (search.y - page.y) / page.scale;
    paint.ring(searchX + 9, searchY + 9, 4.2f, abgr(0xbfa772), 1.3f, 16);
    paint.line(searchX + 12, searchY + 12, searchX + 16, searchY + 16, abgr(0xbfa772), 1.5f);
    const float textY = searchY + (SearchHeight - LabelText - 1) / 2;
    const float searchWidth = search.width / page.scale - 28;

    if (journal.notesSearch.empty() && !journal.notesSearchActive)
    {
        paint.text(LabelFont, LabelText + 1, Placeholder, Engine::tr("Skill, mastery, trainer or town"), searchX + 22,
            textY);
    }
    else
    {
        paint.text(LabelFont, LabelText + 1, Ink, paint.fitted(LabelFont, LabelText + 1,
            journal.notesSearch + (journal.notesSearchActive ? "_" : ""), searchWidth), searchX + 22, textY);
    }

    for (size_t index = 0; index < MasteryNames.size(); ++index)
    {
        const Rect toggle = toggleRect(page, index);
        const bool on = journal.trainerMastery == uint8_t(int(SkillMastery::Expert) + int(index));
        const bool hovered = toggle.contains(pointerX, pointerY);
        paint.button(toggle, masteryLetter(index), on, hovered, hovered && leftHeld, MasteryColours[index]);

        if (on)
        {
            paint.frame(toggle, Brass);
        }
    }

    // The page of the list.
    const std::vector<std::string> words = searchWords(journal.notesSearch);
    const std::optional<GameplayHudTextureHandle> divider =
        context.gameplayUiRuntime().ensureHudTextureLoaded("obsidian_value_divider");
    const FinderRow *pHovered = nullptr;
    float y = ListTop;

    for (size_t position = 0; position < model.pages[journal.trainerPage].size(); ++position)
    {
        const FinderBlock &block = model.blocks[model.pages[journal.trainerPage][position]];

        if (position > 0 && divider && !block.ledgerLine)
        {
            const float width = ContentWidth * 0.76f;
            const Rect line = paint.rect(ContentLeft + (ContentWidth - width) / 2, y - 0.5f, width, 0.5333f);
            context.submitHudTexturedQuad(*divider, line.x, line.y, line.width, line.height);
        }

        if (!block.messageLines.empty())
        {
            const Rect box = paint.rect(ContentLeft, y + BlockPad, ContentWidth, block.height - BlockPad - 2);

            if (block.ledgerLine)
            {
                paint.fill(box, MoreFill);
                paint.frame(box, MoreBorder);
            }

            float lineY = y + BlockPad + 6;

            for (const std::string &line : block.messageLines)
            {
                paint.text(BodyFont, RowText, Dim, line, ContentLeft + 8, lineY);
                lineY += RowText + 1.5f;
            }
        }
        else
        {
            float skillY = y + BlockPad;

            for (const std::string &line : block.skillLines)
            {
                paint.marked(BodyFont, SkillText, Heading, line, ContentLeft + 2, skillY, words);
                skillY += SkillText + 1;
            }
        }

        y += block.height;
    }

    for (const PlacedRow &placed : placeRows(model, journal.trainerPage, page))
    {
        const FinderRow &row = *placed.pRow;
        const bool hovered = row.pEntry != nullptr && placed.area.contains(pointerX, pointerY);

        if (hovered)
        {
            pHovered = &row;
            paint.fill(placed.area, RowHoverFill);
            paint.frame(placed.area, RowHoverBorder);
        }

        const size_t mastery = masteryIndex(row.mastery);
        const float labelY = placed.y + (RowText - LabelText) / 2 + 0.5f;
        paint.marked(LabelFont, LabelText, MasteryColours[mastery], Engine::tr(MasteryNames[mastery]), MasteryLeft,
            labelY, words);
        const float right = ContentLeft + ContentWidth - 4;
        const std::string town = paint.fitted(LabelFont, LabelText, row.town, 118);
        const float townWidth = paint.width(LabelFont, LabelText, town);
        paint.marked(LabelFont, LabelText, Dim, town, right, labelY, words, 2);
        paint.marked(BodyFont, RowText, row.pEntry != nullptr ? Ink : Dim,
            paint.fitted(BodyFont, RowText, row.name, right - townWidth - 8 - NameLeft), NameLeft, placed.y, words);
    }

    // The status strip: the trainer under the pointer, else how many there are.
    std::string status;

    if (pHovered != nullptr && pParty != nullptr)
    {
        const TrainerEntry &entry = *pHovered->pEntry;
        status = trainerPlace(entry) + " \xB7 " + requirementText(*pParty, entry);
    }
    else
    {
        size_t count = 0;

        for (const FinderBlock &block : model.blocks)
        {
            count += size_t(std::count_if(block.rows.begin(), block.rows.end(),
                [](const FinderRow &row) { return row.pEntry != nullptr; }));
        }

        status = count > 0
            ? Engine::trn("{count} trainer on {continent}. Click one to see where.",
                "{count} trainers on {continent}. Click one to see where.", count,
                {{"count", count}, {"continent", model.continentName}})
            : Engine::tr("Try another word, or clear the search.");
    }

    renderStatus(paint, status);

    if (model.pages.size() > 1)
    {
        paint.text(NumberFont, 9.6f, abgr(0xb4ad95),
            std::to_string(journal.trainerPage + 1) + " / " + std::to_string(model.pages.size()), PageWidth / 2,
            PageNumberTop, 1);
    }
}
}
