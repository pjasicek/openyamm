#include "game/ui/GameplayPartyOverlayRenderer.h"

#include "game/gameplay/GameMechanics.h"
#include "game/gameplay/StoryTextFormatter.h"
#include "game/events/EvtEnums.h"
#include "game/items/ItemEnchantRuntime.h"
#include "game/items/ItemRuntime.h"
#include "game/outdoor/OutdoorGameView.h"
#include "game/outdoor/OutdoorBillboardRenderer.h"
#include "game/outdoor/OutdoorPartyRuntime.h"
#include "game/items/PriceCalculator.h"
#include "game/party/SkillData.h"
#include "game/render/TextureFiltering.h"
#include "game/ui/GameplayOverlayContext.h"
#include "game/ui/SpellbookUiLayout.h"
#include "game/StringUtils.h"
#include "game/ui/HudUiService.h"
#include "game/ui/KeyboardScreenLayout.h"

#include <SDL3/SDL.h>
#include <bx/math.h>

#include <algorithm>
#include <array>
#include <cstdio>
#include <cctype>
#include <cmath>
#include <cstring>
#include <cstdint>
#include <cstdlib>
#include <functional>
#include <filesystem>
#include <optional>
#include <string>
#include <tuple>
#include <unordered_map>
#include <unordered_set>
#include <vector>

namespace OpenYAMM::Game
{
namespace
{
constexpr uint16_t HudViewId = 2;
constexpr float HudReferenceWidth = 640.0f;
constexpr float HudReferenceHeight = 480.0f;
constexpr float MaxUiViewportAspect = 4.0f / 3.0f;
constexpr float HudFontIntegerSnapThreshold = 0.1f;
constexpr uint32_t BrokenItemTintColorAbgr = 0x800000ffu;
constexpr uint32_t UnidentifiedItemTintColorAbgr = 0x80ff0000u;
constexpr int RestSkyFrameCount = 244;
constexpr int RestHourglassFirstFrame = 60;
constexpr int RestHourglassLastFrame = 119;
constexpr float RestHourglassLoopSeconds = 4.0f;
constexpr int RestDaysPerMonth = 28;
constexpr int RestMonthsPerYear = 12;
constexpr int RestStartingYear = 1168;
constexpr int JournalRevealWidth = 88;
constexpr int JournalRevealHeight = 88;
constexpr int JournalMapBaseZoom = 384;
constexpr float JournalMainIconAnimationFps = 10.0f;
constexpr float JournalMapWorldHalfExtent = 32768.0f;
constexpr char JournalMapTextureCacheName[] = "__journal_map_composited__";
constexpr std::array<int, 3> JournalMapZoomLevels = {384, 768, 1536};
constexpr float Pi = 3.14159265358979323846f;

uint32_t currentAnimationTicks()
{
    return static_cast<uint32_t>((static_cast<uint64_t>(SDL_GetTicks()) * 128ULL) / 1000ULL);
}

int outdoorMinimapArrowIndex(float yawRadians)
{
    float normalizedYaw = std::fmod(yawRadians, Pi * 2.0f);

    if (normalizedYaw < 0.0f)
    {
        normalizedYaw += Pi * 2.0f;
    }

    const int octant = static_cast<int>(std::floor((normalizedYaw + Pi * 0.125f) / (Pi * 0.25f))) % 8;
    return (octant + 7) % 8;
}

struct UiViewportRect
{
    float x = 0.0f;
    float y = 0.0f;
    float width = 0.0f;
    float height = 0.0f;
};

enum class ItemTintContext
{
    None,
    Held,
    Equipped,
    ShopIdentify,
    ShopRepair,
};

UiViewportRect computeUiViewportRect(int screenWidth, int screenHeight)
{
    UiViewportRect viewport = {};
    viewport.x = 0.0f;
    viewport.y = 0.0f;
    viewport.width = static_cast<float>(screenWidth);
    viewport.height = static_cast<float>(screenHeight);

    if (screenHeight > 0)
    {
        const float maxWidthForHeight = viewport.height * MaxUiViewportAspect;

        if (viewport.width > maxWidthForHeight)
        {
            viewport.width = maxWidthForHeight;
            viewport.x = (static_cast<float>(screenWidth) - viewport.width) * 0.5f;
        }
    }

    return viewport;
}

void renderViewportParchmentSidePanels(const OutdoorGameView &view, int width, int height)
{
    HudUiService::renderViewportSidePanels(view, width, height, "UI-Parch");
}

void renderViewportParchmentSidePanels(GameplayOverlayContext &view, int width, int height)
{
    HudUiService::renderViewportSidePanels(view, width, height, "UI-Parch");
}


float snappedHudFontScale(float scale)
{
    const float roundedScale = std::round(scale);

    if (std::abs(scale - roundedScale) <= HudFontIntegerSnapThreshold)
    {
        return std::max(1.0f, roundedScale);
    }

    return std::max(1.0f, scale);
}

uint32_t itemTintColorAbgr(
    const InventoryItem *pItemState,
    const ItemDefinition *pItemDefinition,
    ItemTintContext context)
{
    if (pItemState == nullptr || pItemDefinition == nullptr)
    {
        return 0xffffffffu;
    }

    const bool isBroken = pItemState->broken;
    const bool isUnidentified = !pItemState->identified && ItemRuntime::requiresIdentification(*pItemDefinition);

    switch (context)
    {
        case ItemTintContext::Held:
        case ItemTintContext::Equipped:
            if (isBroken)
            {
                return BrokenItemTintColorAbgr;
            }

            if (isUnidentified)
            {
                return UnidentifiedItemTintColorAbgr;
            }

            break;

        case ItemTintContext::ShopIdentify:
            if (isUnidentified)
            {
                return UnidentifiedItemTintColorAbgr;
            }

            break;

        case ItemTintContext::ShopRepair:
            if (isBroken)
            {
                return BrokenItemTintColorAbgr;
            }

            break;

        case ItemTintContext::None:
            break;
    }

    return 0xffffffffu;
}

uint32_t makeAbgrColor(uint8_t red, uint8_t green, uint8_t blue, uint8_t alpha = 255)
{
    return static_cast<uint32_t>(alpha) << 24
        | static_cast<uint32_t>(blue) << 16
        | static_cast<uint32_t>(green) << 8
        | static_cast<uint32_t>(red);
}

uint32_t packHudColorAbgr(uint8_t red, uint8_t green, uint8_t blue)
{
    return static_cast<uint32_t>(red)
        | (static_cast<uint32_t>(green) << 8)
        | (static_cast<uint32_t>(blue) << 16)
        | 0xff000000u;
}

std::string replaceAllText(std::string text, const std::string &from, const std::string &to)
{
    size_t position = 0;

    while ((position = text.find(from, position)) != std::string::npos)
    {
        text.replace(position, from.size(), to);
        position += to.size();
    }

    return text;
}

std::string formatRestSkyTextureName(float gameMinutes)
{
    const float positiveMinutes = std::max(0.0f, gameMinutes);
    const float minutesOfDay = std::fmod(positiveMinutes, 1440.0f);
    int frameIndex = static_cast<int>((minutesOfDay / 1440.0f) * static_cast<float>(RestSkyFrameCount));
    frameIndex = std::clamp(frameIndex, 0, RestSkyFrameCount - 1);

    char textureName[16] = {};
    std::snprintf(textureName, sizeof(textureName), "terra%04d", frameIndex);
    return textureName;
}

std::string formatRestHourglassTextureName(const GameplayUiController::RestScreenState &restScreen)
{
    const float loopSeconds = std::fmod(
        std::max(0.0f, restScreen.hourglassElapsedSeconds),
        RestHourglassLoopSeconds);
    const int frameCount = RestHourglassLastFrame - RestHourglassFirstFrame + 1;
    int frameIndex = RestHourglassFirstFrame
        + static_cast<int>(std::floor((loopSeconds / RestHourglassLoopSeconds) * static_cast<float>(frameCount)));
    frameIndex = std::clamp(frameIndex, RestHourglassFirstFrame, RestHourglassLastFrame);

    char textureName[16] = {};
    std::snprintf(textureName, sizeof(textureName), "HGLAS%03d", frameIndex);
    return textureName;
}

bool packedRevealBit(const std::vector<uint8_t> &bytes, size_t index)
{
    const size_t byteIndex = index / 8;

    if (byteIndex >= bytes.size())
    {
        return false;
    }

    const uint8_t mask = static_cast<uint8_t>(1u << (7u - static_cast<unsigned>(index % 8)));
    return (bytes[byteIndex] & mask) != 0;
}

int clampedJournalMapZoomValue(int zoomStep)
{
    const int clampedStep = std::clamp(zoomStep, 0, static_cast<int>(JournalMapZoomLevels.size()) - 1);
    return JournalMapZoomLevels[clampedStep];
}

std::string journalMainIconTextureName(
    const std::string &prefix,
    int frameCount,
    bool hovered,
    float elapsedSeconds)
{
    int frameIndex = 1;

    if (hovered && frameCount > 1)
    {
        frameIndex = 1 + (static_cast<int>(std::floor(elapsedSeconds * JournalMainIconAnimationFps)) % frameCount);
    }

    char buffer[32] = {};
    std::snprintf(buffer, sizeof(buffer), "%s_%02d", prefix.c_str(), frameIndex);
    return buffer;
}

std::string journalNotesCategoryTitle(GameplayUiController::JournalNotesCategory category)
{
    switch (category)
    {
        case GameplayUiController::JournalNotesCategory::Potion:
            return "Potion Notes";
        case GameplayUiController::JournalNotesCategory::Fountain:
            return "Fountains";
        case GameplayUiController::JournalNotesCategory::Obelisk:
            return "Obelisk Notes";
        case GameplayUiController::JournalNotesCategory::Seer:
            return "Seer Notes";
        case GameplayUiController::JournalNotesCategory::Misc:
            return "Miscellaneous";
        case GameplayUiController::JournalNotesCategory::Trainer:
            return "Teacher Locations";
    }

    return "Notes";
}

struct JournalStackedPageEntry
{
    std::vector<std::string> lines;
};

struct JournalStackedPage
{
    std::vector<JournalStackedPageEntry> entries;
};

struct JournalStoryPage
{
    std::string title;
    std::vector<std::string> lines;
};

std::vector<JournalStackedPage> buildJournalStackedPages(
    const GameplayOverlayContext &context,
    const auto &font,
    const std::vector<std::string> &texts,
    float pageWidthPixels,
    float pageHeightPixels,
    float fontScale)
{
    std::vector<JournalStackedPage> pages;

    if (texts.empty())
    {
        return pages;
    }

    const float wrapWidth = std::max(1.0f, pageWidthPixels / std::max(0.1f, fontScale));
    const float lineHeight = std::max(1.0f, static_cast<float>(font.fontHeight) * fontScale);
    const float dividerGap = std::max(10.0f, 12.0f * fontScale);
    const size_t maxLinesPerPage = std::max<size_t>(1, static_cast<size_t>(std::floor(pageHeightPixels / lineHeight)));
    JournalStackedPage currentPage = {};
    float currentHeight = 0.0f;

    for (const std::string &text : texts)
    {
        std::vector<std::string> wrappedLines = context.wrapHudTextToWidth(font, text, wrapWidth);

        if (wrappedLines.empty())
        {
            wrappedLines.push_back("");
        }

        if (wrappedLines.size() > maxLinesPerPage)
        {
            wrappedLines.resize(maxLinesPerPage);
        }

        const float entryHeight = static_cast<float>(wrappedLines.size()) * lineHeight;
        const float additionalHeight = currentPage.entries.empty() ? entryHeight : dividerGap + entryHeight;

        if (!currentPage.entries.empty() && currentHeight + additionalHeight > pageHeightPixels)
        {
            pages.push_back(std::move(currentPage));
            currentPage = {};
            currentHeight = 0.0f;
        }

        JournalStackedPageEntry entry = {};
        entry.lines = std::move(wrappedLines);
        currentPage.entries.push_back(std::move(entry));
        currentHeight += currentPage.entries.size() == 1 ? entryHeight : dividerGap + entryHeight;
    }

    if (!currentPage.entries.empty())
    {
        pages.push_back(std::move(currentPage));
    }

    return pages;
}

std::vector<JournalStoryPage> buildJournalStoryPages(
    const GameplayOverlayContext &context,
    const auto &font,
    const JournalHistoryTable &historyTable,
    const EventRuntimeState *pEventRuntimeState,
    const Party *pParty,
    float pageWidthPixels,
    float pageHeightPixels,
    float fontScale)
{
    std::vector<JournalStoryPage> pages;

    if (pEventRuntimeState == nullptr || pParty == nullptr)
    {
        return pages;
    }

    const float wrapWidth = std::max(1.0f, pageWidthPixels / std::max(0.1f, fontScale));
    const size_t linesPerPage = std::max<size_t>(
        1,
        static_cast<size_t>(std::floor(pageHeightPixels / std::max(1.0f, static_cast<float>(font.fontHeight) * fontScale))));

    for (const JournalHistoryEntry &entry : historyTable.entries())
    {
        const auto historyTimeIt = pEventRuntimeState->historyEventTimes.find(entry.id);

        if (historyTimeIt == pEventRuntimeState->historyEventTimes.end())
        {
            continue;
        }

        std::vector<std::string> wrappedLines = context.wrapHudTextToWidth(
            font,
            StoryTextFormatter::format(entry.text, *pParty, historyTimeIt->second),
            wrapWidth);

        if (wrappedLines.empty())
        {
            wrappedLines.push_back("");
        }

        for (size_t lineIndex = 0; lineIndex < wrappedLines.size(); lineIndex += linesPerPage)
        {
            JournalStoryPage page = {};
            page.title = entry.pageTitle;

            const size_t endIndex = std::min(wrappedLines.size(), lineIndex + linesPerPage);

            for (size_t chunkIndex = lineIndex; chunkIndex < endIndex; ++chunkIndex)
            {
                page.lines.push_back(wrappedLines[chunkIndex]);
            }

            pages.push_back(std::move(page));
        }
    }

    return pages;
}

struct UtilityOverlayRenderLayout
{
    float panelX = 0.0f;
    float panelY = 0.0f;
    float panelWidth = 0.0f;
    float panelHeight = 0.0f;
    float closeX = 0.0f;
    float closeY = 0.0f;
    float closeSize = 0.0f;
    float titleX = 0.0f;
    float titleY = 0.0f;
    float contentX = 0.0f;
    float contentY = 0.0f;
    float contentWidth = 0.0f;
    float rowHeight = 0.0f;
    float rowGap = 0.0f;
    float tabWidth = 0.0f;
    float tabHeight = 0.0f;
    float tabGap = 0.0f;
    float scale = 1.0f;
};

UtilityOverlayRenderLayout computeUtilityOverlayRenderLayout(int screenWidth, int screenHeight)
{
    const float width = static_cast<float>(std::max(screenWidth, 1));
    const float height = static_cast<float>(std::max(screenHeight, 1));
    const float scale = std::clamp(std::min(width / 640.0f, height / 480.0f), 0.8f, 2.0f);

    UtilityOverlayRenderLayout layout = {};
    layout.scale = scale;
    layout.panelWidth = std::round(380.0f * scale);
    layout.panelHeight = std::round(320.0f * scale);
    layout.panelX = std::round((width - layout.panelWidth) * 0.5f);
    layout.panelY = std::round((height - layout.panelHeight) * 0.5f);
    layout.closeSize = std::round(24.0f * scale);
    layout.closeX = std::round(layout.panelX + layout.panelWidth - layout.closeSize - 12.0f * scale);
    layout.closeY = std::round(layout.panelY + 12.0f * scale);
    layout.titleX = std::round(layout.panelX + 24.0f * scale);
    layout.titleY = std::round(layout.panelY + 20.0f * scale);
    layout.contentX = std::round(layout.panelX + 24.0f * scale);
    layout.contentY = std::round(layout.panelY + 82.0f * scale);
    layout.contentWidth = std::round(layout.panelWidth - 48.0f * scale);
    layout.rowHeight = std::round(42.0f * scale);
    layout.rowGap = std::round(6.0f * scale);
    layout.tabWidth = std::round(120.0f * scale);
    layout.tabHeight = std::round(28.0f * scale);
    layout.tabGap = std::round(10.0f * scale);
    return layout;
}

bool utilityOverlayPointInsideRect(float x, float y, float rectX, float rectY, float rectWidth, float rectHeight)
{
    return x >= rectX && x < rectX + rectWidth && y >= rectY && y < rectY + rectHeight;
}

bool isUtilityTownPortalDestinationUnlocked(
    const Party *pParty,
    const OutdoorGameView::TownPortalDestination &destination)
{
    if (destination.unlockQBitId == 0)
    {
        return true;
    }

    if (pParty == nullptr)
    {
        return false;
    }

    return pParty->hasQuestBit(destination.unlockQBitId);
}

size_t utilityOverlayMaxLloydBeaconSlots(const Character *pCharacter)
{
    if (pCharacter == nullptr)
    {
        return 1;
    }

    const CharacterSkill *pWaterSkill = pCharacter->findSkill("WaterMagic");

    if (pWaterSkill == nullptr)
    {
        return 1;
    }

    switch (pWaterSkill->mastery)
    {
        case SkillMastery::Master:
        case SkillMastery::Grandmaster:
            return 5;

        case SkillMastery::Expert:
            return 3;

        case SkillMastery::Normal:
        case SkillMastery::None:
        default:
            return 1;
    }
}

std::string formatUtilityDurationText(float remainingSeconds)
{
    const int totalSeconds = std::max(0, static_cast<int>(std::ceil(remainingSeconds)));
    const int totalHours = (totalSeconds + 3599) / 3600;
    const int days = totalHours / 24;
    const int hours = totalHours % 24;

    if (days > 0 && hours > 0)
    {
        return std::to_string(days) + "d " + std::to_string(hours) + "h";
    }

    if (days > 0)
    {
        return std::to_string(days) + "d";
    }

    return std::to_string(std::max(1, totalHours)) + "h";
}

void renderHudLines(
    const OutdoorGameView &view,
    const auto &font,
    uint32_t colorAbgr,
    const std::vector<std::string> &lines,
    float x,
    float y,
    float fontScale)
{
    bgfx::TextureHandle coloredMainTextureHandle = HudUiService::ensureHudFontMainTextureColor(view, font, colorAbgr);

    if (!bgfx::isValid(coloredMainTextureHandle))
    {
        coloredMainTextureHandle = font.mainTextureHandle;
    }

    const float lineHeight = static_cast<float>(font.fontHeight) * fontScale;

    for (size_t index = 0; index < lines.size(); ++index)
    {
        const float lineY = y + static_cast<float>(index) * lineHeight;
        HudUiService::renderHudFontLayer(view, font, font.shadowTextureHandle, lines[index], x, lineY, fontScale);
        HudUiService::renderHudFontLayer(view, font, coloredMainTextureHandle, lines[index], x, lineY, fontScale);
    }
}

void renderHudLines(
    const GameplayOverlayContext &context,
    const auto &font,
    uint32_t colorAbgr,
    const std::vector<std::string> &lines,
    float x,
    float y,
    float fontScale)
{
    bgfx::TextureHandle coloredMainTextureHandle = context.ensureHudFontMainTextureColor(font, colorAbgr);

    if (!bgfx::isValid(coloredMainTextureHandle))
    {
        coloredMainTextureHandle = font.mainTextureHandle;
    }

    const float lineHeight = static_cast<float>(font.fontHeight) * fontScale;

    for (size_t index = 0; index < lines.size(); ++index)
    {
        const float lineY = y + static_cast<float>(index) * lineHeight;
        context.renderHudFontLayer(font, font.shadowTextureHandle, lines[index], x, lineY, fontScale);
        context.renderHudFontLayer(font, coloredMainTextureHandle, lines[index], x, lineY, fontScale);
    }
}

std::string formatRestTimeText(float gameMinutes)
{
    const int totalMinutes = std::max(0, static_cast<int>(std::floor(gameMinutes + 0.5f)));
    const int minuteOfDay = totalMinutes % 1440;
    const int hour24 = minuteOfDay / 60;
    const int minute = minuteOfDay % 60;
    const int hour12 = hour24 == 0 ? 12 : hour24 > 12 ? hour24 - 12 : hour24;
    const char *pMeridiem = hour24 >= 12 ? "pm" : "am";

    char timeText[16] = {};
    std::snprintf(timeText, sizeof(timeText), "%d:%02d %s", hour12, minute, pMeridiem);
    return timeText;
}

struct RestDateText
{
    int day = 1;
    int month = 1;
    int year = RestStartingYear;
};

RestDateText formatRestDateText(float gameMinutes)
{
    const int totalDays = std::max(0, static_cast<int>(std::floor(gameMinutes / 1440.0f)));
    RestDateText result = {};
    result.year = RestStartingYear + totalDays / (RestDaysPerMonth * RestMonthsPerYear);
    result.month = 1 + (totalDays / RestDaysPerMonth) % RestMonthsPerYear;
    result.day = 1 + totalDays % RestDaysPerMonth;
    return result;
}

bool tryParseInteger(const std::string &value, int &parsedValue)
{
    if (value.empty())
    {
        return false;
    }

    size_t parsedCharacters = 0;

    try
    {
        parsedValue = std::stoi(value, &parsedCharacters);
    }
    catch (...)
    {
        return false;
    }

    return parsedCharacters == value.size();
}

struct InventoryGridMetrics
{
    float x = 0.0f;
    float y = 0.0f;
    float cellWidth = 0.0f;
    float cellHeight = 0.0f;
    float scale = 1.0f;
};

struct InventoryItemScreenRect
{
    float x = 0.0f;
    float y = 0.0f;
    float width = 0.0f;
    float height = 0.0f;
};

struct CharacterSkillUiRow
{
    std::string canonicalName;
    std::string label;
    std::string level;
    bool upgradeable = false;
};

struct CharacterSkillUiData
{
    std::vector<CharacterSkillUiRow> weaponRows;
    std::vector<CharacterSkillUiRow> magicRows;
    std::vector<CharacterSkillUiRow> armorRows;
    std::vector<CharacterSkillUiRow> miscRows;
};

constexpr size_t AdventurersInnVisibleRows = 4;
constexpr size_t AdventurersInnVisibleColumns = 2;
constexpr size_t AdventurersInnVisibleCount = AdventurersInnVisibleRows * AdventurersInnVisibleColumns;
constexpr float AdventurersInnPortraitX = 34.0f;
constexpr float AdventurersInnPortraitY = 47.0f;
constexpr float AdventurersInnPortraitWidth = 62.0f;
constexpr float AdventurersInnPortraitHeight = 72.0f;
constexpr float AdventurersInnPortraitGapX = 3.0f;
constexpr float AdventurersInnPortraitGapY = 3.0f;
constexpr float AdventurersInnColumn1X = 200.0f;
constexpr float AdventurersInnColumn1Y = 50.0f;
constexpr float AdventurersInnColumn2X = 330.0f;
constexpr float AdventurersInnColumn2Y = 82.0f;
constexpr float AdventurersInnBlurbX = 200.0f;
constexpr float AdventurersInnBlurbY = 210.0f;
constexpr float AdventurersInnBlurbWidth = 236.0f;
constexpr float AdventurersInnColumnLineStep = 16.0f;
constexpr uint32_t AdventurersInnSelectionColorAbgr = 0xff8ed9e9u;
constexpr uint32_t AdventurersInnTextColorAbgr = 0xffffffffu;
constexpr float AdventurersInnSelectionThickness = 2.0f;
constexpr uint32_t CharacterDetailGoldColorAbgr = 0xff8ed9e9u;

struct SplitCharacterStatValue
{
    std::string actualText = "0";
    std::string baseText = "0";
    uint32_t actualColorAbgr = 0xffffffffu;
    bool active = false;
};

SplitCharacterStatValue makeSplitCharacterStatValue(const CharacterSheetValue &value)
{
    SplitCharacterStatValue result = {};
    result.active = true;
    result.baseText = std::to_string(value.base);
    result.actualText = value.infinite ? "INF" : std::to_string(value.actual);

    if (!value.infinite)
    {
        if (value.actual > value.base)
        {
            result.actualColorAbgr = makeAbgrColor(0, 255, 0);
        }
        else if (value.actual < value.base)
        {
            result.actualColorAbgr = makeAbgrColor(255, 0, 0);
        }
    }

    return result;
}

SplitCharacterStatValue makeSplitCharacterResourceValue(int currentValue, int maximumValue)
{
    SplitCharacterStatValue result = {};
    result.active = true;
    result.actualText = std::to_string(currentValue);
    result.baseText = std::to_string(maximumValue);

    if (currentValue <= 0)
    {
        result.actualColorAbgr = makeAbgrColor(255, 0, 0);
    }
    else if (maximumValue > 0 && currentValue * 2 < maximumValue)
    {
        result.actualColorAbgr = makeAbgrColor(255, 255, 0);
    }

    return result;
}

bool tryGetSplitCharacterStatValue(
    const std::string &normalizedLayoutId,
    const CharacterSheetSummary &summary,
    SplitCharacterStatValue &value)
{
    if (normalizedLayoutId == "characterstatmightvalue")
    {
        value = makeSplitCharacterStatValue(summary.might);
        return true;
    }

    if (normalizedLayoutId == "characterstatintellectvalue")
    {
        value = makeSplitCharacterStatValue(summary.intellect);
        return true;
    }

    if (normalizedLayoutId == "characterstatpersonalityvalue")
    {
        value = makeSplitCharacterStatValue(summary.personality);
        return true;
    }

    if (normalizedLayoutId == "characterstatendurancevalue")
    {
        value = makeSplitCharacterStatValue(summary.endurance);
        return true;
    }

    if (normalizedLayoutId == "characterstataccuracyvalue")
    {
        value = makeSplitCharacterStatValue(summary.accuracy);
        return true;
    }

    if (normalizedLayoutId == "characterstatspeedvalue")
    {
        value = makeSplitCharacterStatValue(summary.speed);
        return true;
    }

    if (normalizedLayoutId == "characterstatluckvalue")
    {
        value = makeSplitCharacterStatValue(summary.luck);
        return true;
    }

    if (normalizedLayoutId == "characterstathitpointsvalue")
    {
        value = makeSplitCharacterResourceValue(summary.health.current, summary.health.maximum);
        return true;
    }

    if (normalizedLayoutId == "characterstatlevelvalue")
    {
        value = makeSplitCharacterStatValue(summary.level);
        return true;
    }

    if (normalizedLayoutId == "characterstatfireresistancevalue")
    {
        value = makeSplitCharacterStatValue(summary.fireResistance);
        return true;
    }

    if (normalizedLayoutId == "characterstatairresistancevalue")
    {
        value = makeSplitCharacterStatValue(summary.airResistance);
        return true;
    }

    if (normalizedLayoutId == "characterstatwaterresistancevalue")
    {
        value = makeSplitCharacterStatValue(summary.waterResistance);
        return true;
    }

    if (normalizedLayoutId == "characterstatearthresistancevalue")
    {
        value = makeSplitCharacterStatValue(summary.earthResistance);
        return true;
    }

    if (normalizedLayoutId == "characterstatmindresistancevalue")
    {
        value = makeSplitCharacterStatValue(summary.mindResistance);
        return true;
    }

    if (normalizedLayoutId == "characterstatbodyresistancevalue")
    {
        value = makeSplitCharacterStatValue(summary.bodyResistance);
        return true;
    }

    return false;
}

bool shouldRenderCharacterLayoutInAdventurersInn(const std::string &normalizedLayoutId)
{
    return normalizedLayoutId.starts_with("adventurersinn")
        || normalizedLayoutId.starts_with("characterdoll")
        || normalizedLayoutId == "characterroot"
        || normalizedLayoutId == "charactertopbar"
        || normalizedLayoutId == "charactergoldfoodicon"
        || normalizedLayoutId == "charactergoldlabel"
        || normalizedLayoutId == "characterfoodlabel";
}

std::string npcPortraitTextureName(uint32_t pictureId)
{
    if (pictureId == 0)
    {
        return {};
    }

    char buffer[16] = {};
    std::snprintf(buffer, sizeof(buffer), "npc%04u", pictureId);
    return buffer;
}

constexpr const char *WeaponSkillNames[] = {
    "Axe",
    "Bow",
    "Dagger",
    "Mace",
    "Spear",
    "Staff",
    "Sword",
    "Unarmed",
    "Blaster",
};

constexpr const char *MagicSkillNames[] = {
    "FireMagic",
    "AirMagic",
    "WaterMagic",
    "EarthMagic",
    "SpiritMagic",
    "MindMagic",
    "BodyMagic",
    "LightMagic",
    "DarkMagic",
};

constexpr const char *ArmorSkillNames[] = {
    "LeatherArmor",
    "ChainArmor",
    "PlateArmor",
    "Shield",
    "Dodging",
};

constexpr const char *MiscSkillNames[] = {
    "Alchemy",
    "Armsmaster",
    "Bodybuilding",
    "IdentifyItem",
    "IdentifyMonster",
    "Learning",
    "DisarmTraps",
    "Meditation",
    "Merchant",
    "Perception",
    "RepairItem",
    "Stealing",
};

InventoryGridMetrics computeInventoryGridMetrics(
    float x,
    float y,
    float width,
    float height,
    float scale,
    int columns,
    int rows)
{
    InventoryGridMetrics metrics = {};
    metrics.x = x;
    metrics.y = y;
    metrics.cellWidth = width / static_cast<float>(std::max(1, columns));
    metrics.cellHeight = height / static_cast<float>(std::max(1, rows));
    metrics.scale = scale;
    return metrics;
}

InventoryGridMetrics computeInventoryGridMetrics(
    float x,
    float y,
    float width,
    float height,
    float scale)
{
    return computeInventoryGridMetrics(
        x,
        y,
        width,
        height,
        scale,
        Character::InventoryWidth,
        Character::InventoryHeight);
}

InventoryItemScreenRect computeInventoryItemScreenRect(
    const InventoryGridMetrics &gridMetrics,
    const InventoryItem &item,
    float textureWidth,
    float textureHeight)
{
    const float slotSpanWidth = static_cast<float>(item.width) * gridMetrics.cellWidth;
    const float slotSpanHeight = static_cast<float>(item.height) * gridMetrics.cellHeight;
    const float offsetX = (slotSpanWidth - textureWidth) * 0.5f;
    const float offsetY = (slotSpanHeight - textureHeight) * 0.5f;

    InventoryItemScreenRect rect = {};
    rect.x = std::round(
        gridMetrics.x + static_cast<float>(item.gridX) * gridMetrics.cellWidth + offsetX);
    rect.y = std::round(
        gridMetrics.y + static_cast<float>(item.gridY) * gridMetrics.cellHeight + offsetY);
    rect.width = textureWidth;
    rect.height = textureHeight;
    return rect;
}

uint32_t equippedItemId(const CharacterEquipment &equipment, EquipmentSlot slot)
{
    switch (slot)
    {
        case EquipmentSlot::OffHand:
            return equipment.offHand;
        case EquipmentSlot::MainHand:
            return equipment.mainHand;
        case EquipmentSlot::Bow:
            return equipment.bow;
        case EquipmentSlot::Armor:
            return equipment.armor;
        case EquipmentSlot::Helm:
            return equipment.helm;
        case EquipmentSlot::Belt:
            return equipment.belt;
        case EquipmentSlot::Cloak:
            return equipment.cloak;
        case EquipmentSlot::Gauntlets:
            return equipment.gauntlets;
        case EquipmentSlot::Boots:
            return equipment.boots;
        case EquipmentSlot::Amulet:
            return equipment.amulet;
        case EquipmentSlot::Ring1:
            return equipment.ring1;
        case EquipmentSlot::Ring2:
            return equipment.ring2;
        case EquipmentSlot::Ring3:
            return equipment.ring3;
        case EquipmentSlot::Ring4:
            return equipment.ring4;
        case EquipmentSlot::Ring5:
            return equipment.ring5;
        case EquipmentSlot::Ring6:
            return equipment.ring6;
    }

    return 0;
}

std::optional<EquipmentSlot> characterEquipmentSlotForLayoutId(const std::string &layoutId)
{
    const std::string normalized = toLowerCopy(layoutId);

    if (normalized == "characterdollbowslot")
    {
        return EquipmentSlot::Bow;
    }

    if (normalized == "characterdollrighthandslot")
    {
        return EquipmentSlot::MainHand;
    }

    if (normalized == "characterdolllefthandslot")
    {
        return EquipmentSlot::OffHand;
    }

    if (normalized == "characterdollarmorslot")
    {
        return EquipmentSlot::Armor;
    }

    if (normalized == "characterdollhelmetslot")
    {
        return EquipmentSlot::Helm;
    }

    if (normalized == "characterdollbeltslot")
    {
        return EquipmentSlot::Belt;
    }

    if (normalized == "characterdollcloakslot")
    {
        return EquipmentSlot::Cloak;
    }

    if (normalized == "characterdollbootsslot")
    {
        return EquipmentSlot::Boots;
    }

    if (normalized == "characterdollamuletslot")
    {
        return EquipmentSlot::Amulet;
    }

    if (normalized == "characterdollgauntletsslot")
    {
        return EquipmentSlot::Gauntlets;
    }

    if (normalized == "characterdollring1slot")
    {
        return EquipmentSlot::Ring1;
    }

    if (normalized == "characterdollring2slot")
    {
        return EquipmentSlot::Ring2;
    }

    if (normalized == "characterdollring3slot")
    {
        return EquipmentSlot::Ring3;
    }

    if (normalized == "characterdollring4slot")
    {
        return EquipmentSlot::Ring4;
    }

    if (normalized == "characterdollring5slot")
    {
        return EquipmentSlot::Ring5;
    }

    if (normalized == "characterdollring6slot")
    {
        return EquipmentSlot::Ring6;
    }

    return std::nullopt;
}

const char *equipmentSlotName(EquipmentSlot slot)
{
    switch (slot)
    {
        case EquipmentSlot::OffHand:
            return "OffHand";
        case EquipmentSlot::MainHand:
            return "MainHand";
        case EquipmentSlot::Bow:
            return "Bow";
        case EquipmentSlot::Armor:
            return "Armor";
        case EquipmentSlot::Helm:
            return "Helm";
        case EquipmentSlot::Belt:
            return "Belt";
        case EquipmentSlot::Cloak:
            return "Cloak";
        case EquipmentSlot::Gauntlets:
            return "Gauntlets";
        case EquipmentSlot::Boots:
            return "Boots";
        case EquipmentSlot::Amulet:
            return "Amulet";
        case EquipmentSlot::Ring1:
            return "Ring1";
        case EquipmentSlot::Ring2:
            return "Ring2";
        case EquipmentSlot::Ring3:
            return "Ring3";
        case EquipmentSlot::Ring4:
            return "Ring4";
        case EquipmentSlot::Ring5:
            return "Ring5";
        case EquipmentSlot::Ring6:
            return "Ring6";
    }

    return "Unknown";
}

void logCharacterEquipmentRender(
    const std::string &renderKey,
    const std::string &parentId,
    const std::string &assetName,
    float x,
    float y,
    float width,
    float height,
    int zIndex,
    float logicalX,
    float logicalY,
    float logicalWidth,
    float logicalHeight)
{
    static_cast<void>(renderKey);
    static_cast<void>(parentId);
    static_cast<void>(assetName);
    static_cast<void>(x);
    static_cast<void>(y);
    static_cast<void>(width);
    static_cast<void>(height);
    static_cast<void>(zIndex);
    static_cast<void>(logicalX);
    static_cast<void>(logicalY);
    static_cast<void>(logicalWidth);
    static_cast<void>(logicalHeight);
}

std::optional<uint32_t> parseCharacterDataIdFromPortraitTextureName(const std::string &portraitTextureName)
{
    const std::string normalized = toLowerCopy(portraitTextureName);

    if (normalized.size() < 4 || !normalized.starts_with("pc"))
    {
        return std::nullopt;
    }

    std::string digits;

    for (size_t index = 2; index < normalized.size(); ++index)
    {
        const unsigned char character = static_cast<unsigned char>(normalized[index]);

        if (!std::isdigit(character))
        {
            break;
        }

        digits.push_back(normalized[index]);
    }

    if (digits.empty())
    {
        return std::nullopt;
    }

    char *pEnd = nullptr;
    const unsigned long parsed = std::strtoul(digits.c_str(), &pEnd, 10);

    if (pEnd == digits.c_str() || *pEnd != '\0')
    {
        return std::nullopt;
    }

    return static_cast<uint32_t>(parsed);
}

const CharacterDollEntry *resolveCharacterDollEntry(
    const CharacterDollTable *pCharacterDollTable,
    const Character *pCharacter)
{
    if (pCharacterDollTable == nullptr || pCharacter == nullptr)
    {
        return nullptr;
    }

    if (pCharacter->characterDataId != 0)
    {
        const CharacterDollEntry *pEntry = pCharacterDollTable->getCharacter(pCharacter->characterDataId);

        if (pEntry != nullptr)
        {
            return pEntry;
        }
    }

    const std::optional<uint32_t> portraitCharacterDataId =
        parseCharacterDataIdFromPortraitTextureName(pCharacter->portraitTextureName);

    if (portraitCharacterDataId)
    {
        const CharacterDollEntry *pEntry = pCharacterDollTable->getCharacter(*portraitCharacterDataId);

        if (pEntry != nullptr)
        {
            return pEntry;
        }
    }

    return pCharacterDollTable->getCharacter(1);
}

std::string skillPageMasteryDisplayName(SkillMastery mastery)
{
    const std::string displayName = masteryDisplayName(mastery);

    if (displayName == "Grandmaster")
    {
        return "Grand";
    }

    return displayName;
}

void appendCharacterSkillUiRows(
    const Character &character,
    std::vector<CharacterSkillUiRow> &rows,
    std::unordered_set<std::string> &shownSkillNames,
    const char *const *pSkillNames,
    size_t skillCount)
{
    for (size_t skillIndex = 0; skillIndex < skillCount; ++skillIndex)
    {
        const std::string canonicalName = pSkillNames[skillIndex];
        const CharacterSkill *pSkill = character.findSkillByCanonicalName(canonicalName);

        if (pSkill == nullptr)
        {
            continue;
        }

        CharacterSkillUiRow row = {};
        row.canonicalName = canonicalName;
        row.label = displaySkillName(pSkill->name);

        if (pSkill->mastery != SkillMastery::None && pSkill->mastery != SkillMastery::Normal)
        {
            row.label += " " + skillPageMasteryDisplayName(pSkill->mastery);
        }

        row.level = std::to_string(pSkill->level);
        row.upgradeable = character.skillPoints > pSkill->level;
        rows.push_back(std::move(row));
        shownSkillNames.insert(canonicalName);
    }
}

CharacterSkillUiData buildCharacterSkillUiData(const Character *pCharacter)
{
    CharacterSkillUiData data = {};

    if (pCharacter == nullptr)
    {
        return data;
    }

    std::unordered_set<std::string> shownSkillNames;
    appendCharacterSkillUiRows(
        *pCharacter,
        data.weaponRows,
        shownSkillNames,
        WeaponSkillNames,
        std::size(WeaponSkillNames));
    appendCharacterSkillUiRows(
        *pCharacter,
        data.magicRows,
        shownSkillNames,
        MagicSkillNames,
        std::size(MagicSkillNames));
    appendCharacterSkillUiRows(
        *pCharacter,
        data.armorRows,
        shownSkillNames,
        ArmorSkillNames,
        std::size(ArmorSkillNames));
    appendCharacterSkillUiRows(
        *pCharacter,
        data.miscRows,
        shownSkillNames,
        MiscSkillNames,
        std::size(MiscSkillNames));

    std::vector<CharacterSkillUiRow> extraMiscRows;

    for (const auto &[ignoredSkillName, skill] : pCharacter->skills)
    {
        const std::string &canonicalName = ignoredSkillName;

        if (shownSkillNames.contains(canonicalName))
        {
            continue;
        }

        CharacterSkillUiRow row = {};
        row.canonicalName = canonicalName;
        row.label = displaySkillName(skill.name);

        if (skill.mastery != SkillMastery::None && skill.mastery != SkillMastery::Normal)
        {
            row.label += " " + skillPageMasteryDisplayName(skill.mastery);
        }

        row.level = std::to_string(skill.level);
        row.upgradeable = pCharacter->skillPoints > skill.level;
        extraMiscRows.push_back(std::move(row));
    }

    std::sort(
        extraMiscRows.begin(),
        extraMiscRows.end(),
        [](const CharacterSkillUiRow &left, const CharacterSkillUiRow &right)
        {
            return left.label < right.label;
        });

    data.miscRows.insert(data.miscRows.end(), extraMiscRows.begin(), extraMiscRows.end());
    return data;
}

bool isBodyEquipmentVisualSlot(EquipmentSlot slot)
{
    switch (slot)
    {
        case EquipmentSlot::OffHand:
        case EquipmentSlot::MainHand:
        case EquipmentSlot::Bow:
        case EquipmentSlot::Armor:
        case EquipmentSlot::Helm:
        case EquipmentSlot::Belt:
        case EquipmentSlot::Cloak:
        case EquipmentSlot::Gauntlets:
        case EquipmentSlot::Boots:
            return true;

        case EquipmentSlot::Amulet:
        case EquipmentSlot::Ring1:
        case EquipmentSlot::Ring2:
        case EquipmentSlot::Ring3:
        case EquipmentSlot::Ring4:
        case EquipmentSlot::Ring5:
        case EquipmentSlot::Ring6:
            return false;
    }

    return false;
}

bool isJewelryOverlayEquipmentSlot(EquipmentSlot slot)
{
    switch (slot)
    {
        case EquipmentSlot::Gauntlets:
        case EquipmentSlot::Amulet:
        case EquipmentSlot::Ring1:
        case EquipmentSlot::Ring2:
        case EquipmentSlot::Ring3:
        case EquipmentSlot::Ring4:
        case EquipmentSlot::Ring5:
        case EquipmentSlot::Ring6:
            return true;

        case EquipmentSlot::OffHand:
        case EquipmentSlot::MainHand:
        case EquipmentSlot::Bow:
        case EquipmentSlot::Armor:
        case EquipmentSlot::Helm:
        case EquipmentSlot::Belt:
        case EquipmentSlot::Cloak:
        case EquipmentSlot::Boots:
            return false;
    }

    return false;
}

bool isVisibleInCharacterDollOverlay(EquipmentSlot slot, bool jewelryOverlayOpen)
{
    return jewelryOverlayOpen ? isJewelryOverlayEquipmentSlot(slot) : !isJewelryOverlayEquipmentSlot(slot);
}

bool usesAlternateCloakBeltEquippedVariant(EquipmentSlot slot)
{
    return slot == EquipmentSlot::Cloak || slot == EquipmentSlot::Belt;
}

void setCharacterSkillRegionHeight(
    std::unordered_map<std::string, float> &runtimeHeightOverrides,
    float skillRowHeight,
    const char *pLayoutId,
    size_t rowCount)
{
    runtimeHeightOverrides[toLowerCopy(pLayoutId)] =
        skillRowHeight * static_cast<float>(std::max<size_t>(1, rowCount));
}

std::string formatMonsterDamageText(const MonsterTable::MonsterStatsEntry::DamageProfile &damage)
{
    if (damage.diceRolls <= 0 || damage.diceSides <= 0)
    {
        return "-";
    }

    std::string text = std::to_string(damage.diceRolls) + "D" + std::to_string(damage.diceSides);

    if (damage.bonus > 0)
    {
        text += "+" + std::to_string(damage.bonus);
    }
    else if (damage.bonus < 0)
    {
        text += std::to_string(damage.bonus);
    }

    return text;
}

std::string joinNonEmptyTexts(const std::vector<std::string> &parts)
{
    std::string result;

    for (const std::string &part : parts)
    {
        if (part.empty() || part == "-" || part == "0")
        {
            continue;
        }

        if (!result.empty())
        {
            result += ", ";
        }

        result += part;
    }

    return result.empty() ? "-" : result;
}

std::string formatMonsterResistanceText(int value)
{
    return value >= 200 ? "Imm" : std::to_string(value);
}

std::string resolveItemInspectTypeText(const InventoryItem *pItemState, const ItemDefinition &itemDefinition)
{
    if (pItemState != nullptr && !pItemState->identified && ItemRuntime::requiresIdentification(itemDefinition))
    {
        return "Not identified";
    }

    if (!itemDefinition.skillGroup.empty()
        && itemDefinition.skillGroup != "0"
        && itemDefinition.skillGroup != "Misc")
    {
        return itemDefinition.skillGroup;
    }

    if (!itemDefinition.equipStat.empty()
        && itemDefinition.equipStat != "0"
        && itemDefinition.equipStat != "N / A")
    {
        return itemDefinition.equipStat;
    }

    return "Misc";
}

std::string formatItemInspectDamageText(const std::string &damageDice, int bonus)
{
    if (damageDice.empty() || damageDice == "0")
    {
        if (bonus <= 0)
        {
            return {};
        }

        return std::to_string(bonus);
    }

    if (bonus <= 0)
    {
        return damageDice;
    }

    return damageDice + "+" + std::to_string(bonus);
}

std::string resolveItemInspectDetailText(const InventoryItem *pItemState, const ItemDefinition &itemDefinition)
{
    const bool isBroken = pItemState != nullptr && pItemState->broken;
    const std::string &equipStat = itemDefinition.equipStat;
    int mod1Value = 0;
    int mod2Value = 0;
    const bool hasMod1Int = tryParseInteger(itemDefinition.mod1, mod1Value);
    const bool hasMod2Int = tryParseInteger(itemDefinition.mod2, mod2Value);

    if (equipStat == "Weapon" || equipStat == "Weapon2" || equipStat == "Weapon1or2")
    {
        const int attackBonus = hasMod2Int ? mod2Value : 0;
        const std::string damageText = formatItemInspectDamageText(itemDefinition.mod1, attackBonus);

        if (damageText.empty())
        {
            return isBroken ? "Broken" : std::string {};
        }

        const std::string detail = "Attack: +" + std::to_string(attackBonus) + "   Damage: " + damageText;
        return isBroken ? "Broken   " + detail : detail;
    }

    if (equipStat == "Missile")
    {
        const int shootBonus = hasMod2Int ? mod2Value : 0;
        const std::string damageText = formatItemInspectDamageText(itemDefinition.mod1, shootBonus);

        if (damageText.empty())
        {
            return isBroken ? "Broken" : std::string {};
        }

        const std::string detail = "Shoot: +" + std::to_string(shootBonus) + "   Damage: " + damageText;
        return isBroken ? "Broken   " + detail : detail;
    }

    if (equipStat == "WeaponW")
    {
        if (hasMod2Int && mod2Value > 0)
        {
            const std::string detail = "Charges: " + std::to_string(mod2Value);
            return isBroken ? "Broken   " + detail : detail;
        }

        return isBroken ? "Broken" : std::string {};
    }

    if (equipStat == "Armor"
        || equipStat == "Shield"
        || equipStat == "Helm"
        || equipStat == "Belt"
        || equipStat == "Cloak"
        || equipStat == "Gauntlets"
        || equipStat == "Boots"
        || equipStat == "Ring"
        || equipStat == "Amulet")
    {
        const int armorValue = (hasMod1Int ? mod1Value : 0) + (hasMod2Int ? mod2Value : 0);

        if (armorValue > 0)
        {
            const std::string detail = "Armor: +" + std::to_string(armorValue);
            return isBroken ? "Broken   " + detail : detail;
        }

        return isBroken ? "Broken" : std::string {};
    }

    return isBroken ? "Broken" : std::string {};
}

void setupHudProjection(int width, int height)
{
    float projectionMatrix[16] = {};
    bx::mtxOrtho(
        projectionMatrix,
        0.0f,
        static_cast<float>(width),
        static_cast<float>(height),
        0.0f,
        0.0f,
        1000.0f,
        0.0f,
        bgfx::getCaps()->homogeneousDepth);
    bgfx::setViewRect(HudViewId, 0, 0, static_cast<uint16_t>(width), static_cast<uint16_t>(height));
    bgfx::setViewTransform(HudViewId, nullptr, projectionMatrix);
    bgfx::touch(HudViewId);
}

} // namespace

void GameplayPartyOverlayRenderer::renderRestOverlay(GameplayOverlayContext &context, int width, int height)
{
    const GameplayUiController::RestScreenState &restScreen = context.restScreenState();

    if (!restScreen.active || width <= 0 || height <= 0)
    {
        return;
    }

    const GameplayOverlayContext::HudLayoutElement *pRootLayout = context.findHudLayoutElement("RestRoot");

    if (pRootLayout == nullptr)
    {
        return;
    }

    setupHudProjection(width, height);
    HudUiService::renderViewportSidePanels(context, width, height, "UI-Parch");

    float mouseX = 0.0f;
    float mouseY = 0.0f;
    const SDL_MouseButtonFlags mouseButtons = SDL_GetMouseState(&mouseX, &mouseY);
    const bool isLeftMousePressed = (mouseButtons & SDL_BUTTON_LMASK) != 0;
    const float gameMinutes = context.worldRuntime() != nullptr ? context.worldRuntime()->gameMinutes() : 0.0f;
    const RestDateText dateText = formatRestDateText(gameMinutes);
    const std::string timeText = formatRestTimeText(gameMinutes);
    const std::vector<std::string> orderedLayoutIds = context.sortedHudLayoutIdsForScreen("Rest");

    for (const std::string &layoutId : orderedLayoutIds)
    {
        const GameplayOverlayContext::HudLayoutElement *pLayout = context.findHudLayoutElement(layoutId);

        if (pLayout == nullptr || !pLayout->visible || toLowerCopy(pLayout->id) == "restroot")
        {
            continue;
        }

        std::string textureName = pLayout->primaryAsset;

        if (pLayout->id == "RestSkyAnimation")
        {
            textureName = formatRestSkyTextureName(gameMinutes);
        }
        else if (pLayout->id == "RestHourglass")
        {
            textureName = formatRestHourglassTextureName(restScreen);
        }

        if (!textureName.empty())
        {
            if (pLayout->interactive)
            {
                const std::optional<GameplayOverlayContext::ResolvedHudLayoutElement> interactiveResolved =
                    context.resolveHudLayoutElement(layoutId, width, height, pLayout->width, pLayout->height);
                const std::string *pAssetName =
                    interactiveResolved
                        ? context.resolveInteractiveAssetName(
                            *pLayout,
                            *interactiveResolved,
                            mouseX,
                            mouseY,
                            isLeftMousePressed)
                        : nullptr;

                if (pAssetName != nullptr)
                {
                    textureName = *pAssetName;
                }
            }

            const std::optional<GameplayOverlayContext::HudTextureHandle> texture =
                context.ensureHudTextureLoaded(textureName);

            if (texture)
            {
                const float fallbackWidth = pLayout->width > 0.0f
                    ? pLayout->width
                    : static_cast<float>(texture->width);
                const float fallbackHeight = pLayout->height > 0.0f
                    ? pLayout->height
                    : static_cast<float>(texture->height);
                const std::optional<GameplayOverlayContext::ResolvedHudLayoutElement> resolved =
                    context.resolveHudLayoutElement(layoutId, width, height, fallbackWidth, fallbackHeight);

                if (resolved)
                {
                    context.submitHudTexturedQuad(*texture, resolved->x, resolved->y, resolved->width, resolved->height);
                }
            }
        }

        if (!pLayout->labelText.empty())
        {
            std::string label = pLayout->labelText;
            label = replaceAllText(label, "{time}", timeText);
            label = replaceAllText(label, "{day_num}", std::to_string(dateText.day));
            label = replaceAllText(label, "{month_num}", std::to_string(dateText.month));
            label = replaceAllText(label, "{year_num}", std::to_string(dateText.year));
            label = replaceAllText(label, "{rest_food_cost}", std::to_string(context.restFoodRequired()));

            const std::optional<GameplayOverlayContext::ResolvedHudLayoutElement> resolved =
                context.resolveHudLayoutElement(layoutId, width, height, pLayout->width, pLayout->height);

            if (resolved)
            {
                context.renderLayoutLabel(*pLayout, *resolved, label);
            }
        }
    }
}

void GameplayPartyOverlayRenderer::renderMenuOverlay(GameplayOverlayContext &context, int width, int height)
{
    const GameplayUiController::MenuScreenState &menuScreen = context.menuScreenState();

    if (!menuScreen.active || width <= 0 || height <= 0)
    {
        return;
    }

    const GameplayOverlayContext::HudLayoutElement *pRootLayout = context.findHudLayoutElement("MenuRoot");

    if (pRootLayout == nullptr)
    {
        return;
    }

    setupHudProjection(width, height);
    HudUiService::renderViewportSidePanels(context, width, height, "UI-Parch");

    float mouseX = 0.0f;
    float mouseY = 0.0f;
    const SDL_MouseButtonFlags mouseButtons = SDL_GetMouseState(&mouseX, &mouseY);
    const bool isLeftMousePressed = (mouseButtons & SDL_BUTTON_LMASK) != 0;
    const std::vector<std::string> orderedLayoutIds = context.sortedHudLayoutIdsForScreen("Menu");

    for (const std::string &layoutId : orderedLayoutIds)
    {
        const GameplayOverlayContext::HudLayoutElement *pLayout = context.findHudLayoutElement(layoutId);

        if (pLayout == nullptr || !pLayout->visible || toLowerCopy(pLayout->id) == "menuroot")
        {
            continue;
        }

        if (!pLayout->primaryAsset.empty())
        {
            std::string textureName = pLayout->primaryAsset;

            if (pLayout->interactive)
            {
                const std::optional<GameplayOverlayContext::ResolvedHudLayoutElement> interactiveResolved =
                    context.resolveHudLayoutElement(layoutId, width, height, pLayout->width, pLayout->height);
                const std::string *pAssetName =
                    interactiveResolved
                        ? context.resolveInteractiveAssetName(
                            *pLayout,
                            *interactiveResolved,
                            mouseX,
                            mouseY,
                            isLeftMousePressed)
                        : nullptr;

                if (pAssetName != nullptr)
                {
                    textureName = *pAssetName;
                }
            }

            const std::optional<GameplayOverlayContext::HudTextureHandle> texture =
                context.ensureHudTextureLoaded(textureName);

            if (texture)
            {
                const float fallbackWidth = pLayout->width > 0.0f
                    ? pLayout->width
                    : static_cast<float>(texture->width);
                const float fallbackHeight = pLayout->height > 0.0f
                    ? pLayout->height
                    : static_cast<float>(texture->height);
                const std::optional<GameplayOverlayContext::ResolvedHudLayoutElement> resolved =
                    context.resolveHudLayoutElement(layoutId, width, height, fallbackWidth, fallbackHeight);

                if (resolved)
                {
                    context.submitHudTexturedQuad(*texture, resolved->x, resolved->y, resolved->width, resolved->height);
                }
            }
        }

        if (pLayout->id == "MenuBottomBarText")
        {
            const std::optional<GameplayOverlayContext::ResolvedHudLayoutElement> resolved =
                context.resolveHudLayoutElement(layoutId, width, height, pLayout->width, pLayout->height);

            if (resolved)
            {
                GameplayOverlayContext::HudLayoutElement layout = *pLayout;

                if (menuScreen.bottomBarTextUseWhite)
                {
                    layout.textColorAbgr = 0xffffffffu;
                }

                context.renderLayoutLabel(layout, *resolved, menuScreen.bottomBarText);
            }
        }
    }
}

void GameplayPartyOverlayRenderer::renderControlsOverlay(GameplayOverlayContext &context, int width, int height)
{
    if (!context.controlsScreenState().active || width <= 0 || height <= 0)
    {
        return;
    }

    static const std::array<const char *, 10> VolumeIndicatorAssetNames = {
        "convol10",
        "convol20",
        "convol30",
        "convol40",
        "convol50",
        "convol60",
        "convol70",
        "convol80",
        "convol90",
        "convol00"
    };

    const GameplayOverlayContext::HudLayoutElement *pRootLayout = context.findHudLayoutElement("ControlsRoot");

    if (pRootLayout == nullptr)
    {
        return;
    }

    setupHudProjection(width, height);
    HudUiService::renderViewportSidePanels(context, width, height, "UI-Parch");

    float mouseX = 0.0f;
    float mouseY = 0.0f;
    const SDL_MouseButtonFlags mouseButtons = SDL_GetMouseState(&mouseX, &mouseY);
    const bool isLeftMousePressed = (mouseButtons & SDL_BUTTON_LMASK) != 0;
    const std::vector<std::string> orderedLayoutIds = context.sortedHudLayoutIdsForScreen("Controls");
    const GameSettings &settings = context.settingsSnapshot();
    const auto isStateButtonLayoutId =
        [](const std::string &layoutId) -> bool
        {
            return layoutId == "ControlsTurnRate16Button"
                || layoutId == "ControlsTurnRate32Button"
                || layoutId == "ControlsTurnRateSmoothButton"
                || layoutId == "ControlsWalkSoundButton"
                || layoutId == "ControlsShowHitsButton"
                || layoutId == "ControlsAlwaysRunButton"
                || layoutId == "ControlsFlipOnExitButton";
        };

    const auto resolveLayout =
        [&context, width, height](const std::string &layoutId) -> std::optional<GameplayOverlayContext::ResolvedHudLayoutElement>
        {
            const GameplayOverlayContext::HudLayoutElement *pLayout = context.findHudLayoutElement(layoutId);

            if (pLayout == nullptr)
            {
                return std::nullopt;
            }

            return context.resolveHudLayoutElement(layoutId, width, height, pLayout->width, pLayout->height);
        };

    for (const std::string &layoutId : orderedLayoutIds)
    {
        const GameplayOverlayContext::HudLayoutElement *pLayout = context.findHudLayoutElement(layoutId);

        if (pLayout == nullptr
            || !pLayout->visible
            || toLowerCopy(pLayout->id) == "controlsroot"
            || isStateButtonLayoutId(layoutId))
        {
            continue;
        }

        if (pLayout->primaryAsset.empty())
        {
            continue;
        }

        std::string textureName = pLayout->primaryAsset;

        if (pLayout->interactive)
        {
            const std::optional<GameplayOverlayContext::ResolvedHudLayoutElement> interactiveResolved =
                context.resolveHudLayoutElement(layoutId, width, height, pLayout->width, pLayout->height);
            const std::string *pAssetName =
                interactiveResolved
                    ? context.resolveInteractiveAssetName(
                        *pLayout,
                        *interactiveResolved,
                        mouseX,
                        mouseY,
                        isLeftMousePressed)
                    : nullptr;

            if (pAssetName != nullptr)
            {
                textureName = *pAssetName;
            }
        }

        const std::optional<GameplayOverlayContext::HudTextureHandle> texture = context.ensureHudTextureLoaded(textureName);

        if (!texture)
        {
            continue;
        }

        const std::optional<GameplayOverlayContext::ResolvedHudLayoutElement> resolved =
            context.resolveHudLayoutElement(
                layoutId,
                width,
                height,
                static_cast<float>(texture->width),
                static_cast<float>(texture->height));

        if (resolved)
        {
            context.submitHudTexturedQuad(*texture, resolved->x, resolved->y, resolved->width, resolved->height);
        }
    }

    const auto drawStateButton =
        [&context, &resolveLayout, mouseX, mouseY, isLeftMousePressed](
            const char *pButtonLayoutId,
            GameplayControlsRenderButton button,
            const char *pUpAsset,
            const char *pDownAsset,
            bool active)
        {
            const std::optional<GameplayOverlayContext::ResolvedHudLayoutElement> hitRect = resolveLayout(pButtonLayoutId);

            if (!hitRect)
            {
                return;
            }

            const bool hovered = context.isPointerInsideResolvedElement(*hitRect, mouseX, mouseY);
            const bool pressed =
                hovered
                && isLeftMousePressed
                && context.isControlsRenderButtonPressed(button);
            const char *pAssetName = (active && !pressed) ? pUpAsset : pDownAsset;
            const std::optional<GameplayOverlayContext::HudTextureHandle> texture =
                context.ensureHudTextureLoaded(pAssetName);

            if (!texture)
            {
                return;
            }

            context.submitHudTexturedQuad(
                *texture,
                hitRect->x,
                hitRect->y,
                hitRect->width,
                hitRect->height);
        };

    drawStateButton(
        "ControlsTurnRate16Button",
        GameplayControlsRenderButton::TurnRate16,
        "bt_16xU",
        "bt_16xD",
        settings.turnRate == TurnRateMode::X16);
    drawStateButton(
        "ControlsTurnRate32Button",
        GameplayControlsRenderButton::TurnRate32,
        "bt_32xU",
        "bt_32xD",
        settings.turnRate == TurnRateMode::X32);
    drawStateButton(
        "ControlsTurnRateSmoothButton",
        GameplayControlsRenderButton::TurnRateSmooth,
        "bt_smooU",
        "bt_smooD",
        settings.turnRate == TurnRateMode::Smooth);
    drawStateButton(
        "ControlsWalkSoundButton",
        GameplayControlsRenderButton::WalkSound,
        "bt_wksdU",
        "bt_wksdD",
        settings.walksound);
    drawStateButton(
        "ControlsShowHitsButton",
        GameplayControlsRenderButton::ShowHits,
        "bt_hitsU",
        "bt_hitsD",
        settings.showHits);
    drawStateButton(
        "ControlsAlwaysRunButton",
        GameplayControlsRenderButton::AlwaysRun,
        "bt_runU",
        "bt_runD",
        settings.alwaysRun);
    drawStateButton(
        "ControlsFlipOnExitButton",
        GameplayControlsRenderButton::FlipOnExit,
        "bt_flipU",
        "bt_flipD",
        settings.flipOnExit);

    const auto drawVolumeMarker =
        [&context, &resolveLayout](const char *pTrackLayoutId, int level)
        {
            const std::optional<GameplayOverlayContext::ResolvedHudLayoutElement> trackRect = resolveLayout(pTrackLayoutId);

            if (!trackRect)
            {
                return;
            }

            const int clampedLevel = std::clamp(level, 0, 9);
            const std::optional<GameplayOverlayContext::HudTextureHandle> texture =
                context.ensureHudTextureLoaded(VolumeIndicatorAssetNames[clampedLevel]);

            if (!texture)
            {
                return;
            }

            const float logicalKnobHeight = 18.0f;
            const float knobScale = logicalKnobHeight > 0.0f ? trackRect->height / logicalKnobHeight : 1.0f;
            const float drawWidth = static_cast<float>(texture->width) * knobScale;
            const float drawHeight = static_cast<float>(texture->height) * knobScale;
            const float t = static_cast<float>(clampedLevel) / 9.0f;
            const float drawX = std::round(trackRect->x + (trackRect->width - drawWidth) * t);
            const float drawY = std::round(trackRect->y + (trackRect->height - drawHeight) * 0.5f);
            context.submitHudTexturedQuad(
                *texture,
                drawX,
                drawY,
                drawWidth,
                drawHeight);
        };

    drawVolumeMarker("ControlsSoundKnobLane", settings.soundVolume);
    drawVolumeMarker("ControlsMusicKnobLane", settings.musicVolume);
    drawVolumeMarker("ControlsVoiceKnobLane", settings.voiceVolume);
}

void GameplayPartyOverlayRenderer::renderKeyboardOverlay(GameplayOverlayContext &context, int width, int height)
{
    const GameplayUiController::KeyboardScreenState &keyboardScreen = context.keyboardScreenState();

    if (!keyboardScreen.active || width <= 0 || height <= 0)
    {
        return;
    }

    const GameplayOverlayContext::HudLayoutElement *pRootLayout = context.findHudLayoutElement("KeyboardRoot");

    if (pRootLayout == nullptr)
    {
        return;
    }

    setupHudProjection(width, height);
    HudUiService::renderViewportSidePanels(context, width, height, "UI-Parch");

    float mouseX = 0.0f;
    float mouseY = 0.0f;
    const SDL_MouseButtonFlags mouseButtons = SDL_GetMouseState(&mouseX, &mouseY);
    const bool isLeftMousePressed = (mouseButtons & SDL_BUTTON_LMASK) != 0;
    const std::vector<std::string> orderedLayoutIds = context.sortedHudLayoutIdsForScreen("Keyboard");

    const auto resolveLayout =
        [&context, width, height](const std::string &layoutId) -> std::optional<GameplayOverlayContext::ResolvedHudLayoutElement>
        {
            const GameplayOverlayContext::HudLayoutElement *pLayout = context.findHudLayoutElement(layoutId);

            if (pLayout == nullptr)
            {
                return std::nullopt;
            }

            return context.resolveHudLayoutElement(layoutId, width, height, pLayout->width, pLayout->height);
        };

    for (const std::string &layoutId : orderedLayoutIds)
    {
        const GameplayOverlayContext::HudLayoutElement *pLayout = context.findHudLayoutElement(layoutId);

        if (pLayout == nullptr
            || !pLayout->visible
            || toLowerCopy(pLayout->id) == "keyboardroot"
            || pLayout->primaryAsset.empty())
        {
            continue;
        }

        std::string textureName = pLayout->primaryAsset;

        if (pLayout->interactive)
        {
            const std::optional<GameplayOverlayContext::ResolvedHudLayoutElement> interactiveResolved =
                context.resolveHudLayoutElement(layoutId, width, height, pLayout->width, pLayout->height);
            const std::string *pAssetName =
                interactiveResolved
                    ? context.resolveInteractiveAssetName(
                        *pLayout,
                        *interactiveResolved,
                        mouseX,
                        mouseY,
                        isLeftMousePressed)
                    : nullptr;

            if (pAssetName != nullptr)
            {
                textureName = *pAssetName;
            }
        }

        const std::optional<GameplayOverlayContext::HudTextureHandle> texture =
            context.ensureHudTextureLoaded(textureName);

        if (!texture)
        {
            continue;
        }

        const std::optional<GameplayOverlayContext::ResolvedHudLayoutElement> resolved =
            context.resolveHudLayoutElement(
                layoutId,
                width,
                height,
                static_cast<float>(texture->width),
                static_cast<float>(texture->height));

        if (resolved)
        {
            context.submitHudTexturedQuad(*texture, resolved->x, resolved->y, resolved->width, resolved->height);
        }
    }

    const std::optional<KeyboardScreenLayout> keyboardLayout = resolveKeyboardScreenLayout(context, width, height);

    if (!keyboardLayout)
    {
        return;
    }

    const std::optional<GameplayOverlayContext::HudFontHandle> font = context.findHudFont("Create");

    if (!font)
    {
        return;
    }

    const float rootScale = keyboardLayout->rootScale;
    const float fontScale = 1.0f * rootScale;
    const float lineHeight = static_cast<float>(font->fontHeight) * fontScale;
    const GameSettings &settings = context.settingsSnapshot();

    for (const KeyboardBindingDefinition &definition : keyboardBindingDefinitions())
    {
        if (definition.page != keyboardScreen.page)
        {
            continue;
        }

        const float labelX = keyboardLayout->labelColumnX(definition.column);
        const float valueX = keyboardLayout->valueColumnX(definition.column);
        const float rowY = keyboardLayout->rowY(definition.row);
        const bool highlighted =
            keyboardScreen.waitingForBinding
            && keyboardScreen.pendingAction == definition.action;

        const uint32_t labelColor = definition.implemented ? 0xffffffffu : 0xffc8c8c8u;
        const uint32_t valueColor = highlighted ? 0xff9bffffu : 0xffffffffu;
        const float textY = rowY
            + keyboardLayout->textPaddingY
            + std::max(0.0f, (keyboardLayout->rowHeight - lineHeight) * 0.15f);

        renderHudLines(
            context,
            *font,
            labelColor,
            std::vector<std::string>{std::string(definition.label)},
            labelX + keyboardLayout->textPaddingX,
            textY,
            fontScale);
        renderHudLines(
            context,
            *font,
            valueColor,
            std::vector<std::string>{
                highlighted
                    ? std::string("Press Key")
                    : keyboardBindingDisplayName(settings.keyboard.binding(definition.action))
            },
            valueX + keyboardLayout->textPaddingX,
            textY,
            fontScale);
    }

}

void GameplayPartyOverlayRenderer::renderVideoOptionsOverlay(GameplayOverlayContext &context, int width, int height)
{
    if (!context.videoOptionsScreenState().active || width <= 0 || height <= 0)
    {
        return;
    }

    const GameplayOverlayContext::HudLayoutElement *pRootLayout = context.findHudLayoutElement("VideoOptionsRoot");

    if (pRootLayout == nullptr)
    {
        return;
    }

    setupHudProjection(width, height);
    HudUiService::renderViewportSidePanels(context, width, height, "UI-Parch");

    float mouseX = 0.0f;
    float mouseY = 0.0f;
    const SDL_MouseButtonFlags mouseButtons = SDL_GetMouseState(&mouseX, &mouseY);
    const bool isLeftMousePressed = (mouseButtons & SDL_BUTTON_LMASK) != 0;
    const std::vector<std::string> orderedLayoutIds = context.sortedHudLayoutIdsForScreen("VideoOptions");
    const GameSettings &settings = context.settingsSnapshot();

    const auto isStateButtonLayoutId =
        [](const std::string &layoutId) -> bool
        {
            return layoutId == "VideoOptionsBloodSplatsButton"
                || layoutId == "VideoOptionsColoredLightsButton"
                || layoutId == "VideoOptionsTintingButton";
        };

    const auto resolveLayout =
        [&context, width, height](const std::string &layoutId) -> std::optional<GameplayOverlayContext::ResolvedHudLayoutElement>
        {
            const GameplayOverlayContext::HudLayoutElement *pLayout = context.findHudLayoutElement(layoutId);

            if (pLayout == nullptr)
            {
                return std::nullopt;
            }

            return context.resolveHudLayoutElement(layoutId, width, height, pLayout->width, pLayout->height);
        };

    for (const std::string &layoutId : orderedLayoutIds)
    {
        const GameplayOverlayContext::HudLayoutElement *pLayout = context.findHudLayoutElement(layoutId);

        if (pLayout == nullptr
            || !pLayout->visible
            || toLowerCopy(pLayout->id) == "videooptionsroot"
            || isStateButtonLayoutId(layoutId))
        {
            continue;
        }

        if (pLayout->primaryAsset.empty())
        {
            continue;
        }

        std::string textureName = pLayout->primaryAsset;

        if (pLayout->interactive)
        {
            const std::optional<GameplayOverlayContext::ResolvedHudLayoutElement> interactiveResolved =
                context.resolveHudLayoutElement(layoutId, width, height, pLayout->width, pLayout->height);
            const std::string *pAssetName =
                interactiveResolved
                    ? context.resolveInteractiveAssetName(
                        *pLayout,
                        *interactiveResolved,
                        mouseX,
                        mouseY,
                        isLeftMousePressed)
                    : nullptr;

            if (pAssetName != nullptr)
            {
                textureName = *pAssetName;
            }
        }

        const std::optional<GameplayOverlayContext::HudTextureHandle> texture =
            context.ensureHudTextureLoaded(textureName);

        if (!texture)
        {
            continue;
        }

        const std::optional<GameplayOverlayContext::ResolvedHudLayoutElement> resolved =
            context.resolveHudLayoutElement(
                layoutId,
                width,
                height,
                static_cast<float>(texture->width),
                static_cast<float>(texture->height));

        if (resolved)
        {
            context.submitHudTexturedQuad(*texture, resolved->x, resolved->y, resolved->width, resolved->height);
        }
    }

    const auto drawStateButton =
        [&context, &resolveLayout, mouseX, mouseY, isLeftMousePressed](
            const char *pButtonLayoutId,
            GameplayVideoOptionsRenderButton button,
            bool active)
        {
            const std::optional<GameplayOverlayContext::ResolvedHudLayoutElement> hitRect = resolveLayout(pButtonLayoutId);

            if (!hitRect)
            {
                return;
            }

            const GameplayOverlayContext::HudLayoutElement *pLayout = context.findHudLayoutElement(pButtonLayoutId);

            if (pLayout == nullptr || pLayout->primaryAsset.empty())
            {
                return;
            }

            const bool hovered = context.isPointerInsideResolvedElement(*hitRect, mouseX, mouseY);
            const bool pressed =
                hovered
                && isLeftMousePressed
                && context.isVideoOptionsRenderButtonPressed(button);
            const std::string *pAssetName =
                active || pLayout->pressedAsset.empty() ? &pLayout->primaryAsset : &pLayout->pressedAsset;

            if (pressed && !pLayout->pressedAsset.empty())
            {
                pAssetName = &pLayout->pressedAsset;
            }

            const std::optional<GameplayOverlayContext::HudTextureHandle> texture =
                context.ensureHudTextureLoaded(*pAssetName);

            if (!texture)
            {
                return;
            }

            context.submitHudTexturedQuad(
                *texture,
                hitRect->x,
                hitRect->y,
                hitRect->width,
                hitRect->height);
        };

    drawStateButton(
        "VideoOptionsBloodSplatsButton",
        GameplayVideoOptionsRenderButton::BloodSplats,
        settings.bloodSplats);
    drawStateButton(
        "VideoOptionsColoredLightsButton",
        GameplayVideoOptionsRenderButton::ColoredLights,
        settings.coloredLights);
    drawStateButton(
        "VideoOptionsTintingButton",
        GameplayVideoOptionsRenderButton::Tinting,
        settings.tinting);
}

constexpr size_t SaveLoadVisibleSlotCount = 10;

void GameplayPartyOverlayRenderer::renderSaveLoadOverlay(
    GameplayOverlayContext &context,
    int width,
    int height,
    const char *pScreenName,
    const char *pRootId,
    const char *pThumbId,
    const char *pScrollUpId,
    const char *pScrollDownId,
    const char *pPreviewRectId,
    const char *pSelectedNameId,
    const char *pPreviewLine1Id,
    const char *pPreviewLine2Id,
    const char *pRowPrefix,
    const std::vector<GameplayUiController::SaveSlotSummary> &slots,
    size_t scrollOffset,
    size_t selectedIndex,
    bool renderSelectedDetails,
    const GameplayUiController::SaveGameScreenState *pSaveGameScreen)
{
    const GameplayOverlayContext::HudLayoutElement *pRootLayout = context.findHudLayoutElement(pRootId);

    if (pRootLayout == nullptr)
    {
        return;
    }

    setupHudProjection(width, height);
    HudUiService::renderViewportSidePanels(context, width, height, "UI-Parch");

    float mouseX = 0.0f;
    float mouseY = 0.0f;
    const SDL_MouseButtonFlags mouseButtons = SDL_GetMouseState(&mouseX, &mouseY);
    const bool isLeftMousePressed = (mouseButtons & SDL_BUTTON_LMASK) != 0;
    const std::vector<std::string> orderedLayoutIds = context.sortedHudLayoutIdsForScreen(pScreenName);
    const uint32_t rowColor = makeAbgrColor(255, 255, 255);
    const uint32_t selectedRowColor = makeAbgrColor(255, 255, 0);

    const auto resolveLayout =
        [&context, width, height](const std::string &layoutId) -> std::optional<GameplayOverlayContext::ResolvedHudLayoutElement>
        {
            const GameplayOverlayContext::HudLayoutElement *pLayout = context.findHudLayoutElement(layoutId);

            if (pLayout == nullptr)
            {
                return std::nullopt;
            }

            return context.resolveHudLayoutElement(layoutId, width, height, pLayout->width, pLayout->height);
        };
    const auto submitSolidQuad =
        [&context](float x, float y, float quadWidth, float quadHeight, uint32_t abgr)
        {
            if (quadWidth <= 0.0f || quadHeight <= 0.0f)
            {
                return;
            }

            const std::string textureName = "__save_load_solid_" + std::to_string(abgr);
            const std::optional<GameplayOverlayContext::HudTextureHandle> solidTexture =
                context.ensureSolidHudTextureLoaded(textureName, abgr);

            if (solidTexture)
            {
                context.submitHudTexturedQuad(*solidTexture, x, y, quadWidth, quadHeight);
            }
        };

    for (const std::string &layoutId : orderedLayoutIds)
    {
        const GameplayOverlayContext::HudLayoutElement *pLayout = context.findHudLayoutElement(layoutId);

        if (pLayout == nullptr || !pLayout->visible)
        {
            continue;
        }

        const std::string normalizedId = toLowerCopy(pLayout->id);

        if (normalizedId == toLowerCopy(pRootId)
            || normalizedId == toLowerCopy(pThumbId)
            || normalizedId == toLowerCopy(pSelectedNameId)
            || normalizedId == toLowerCopy(pPreviewLine1Id)
            || normalizedId == toLowerCopy(pPreviewLine2Id)
            || normalizedId == toLowerCopy(pPreviewRectId)
            || normalizedId.rfind(toLowerCopy(pRowPrefix), 0) == 0)
        {
            continue;
        }

        if (!pLayout->primaryAsset.empty())
        {
            std::string textureName = pLayout->primaryAsset;

            if (pLayout->interactive)
            {
                const std::optional<GameplayOverlayContext::ResolvedHudLayoutElement> interactiveResolved =
                    resolveLayout(layoutId);
                const std::string *pAssetName =
                    interactiveResolved
                        ? context.resolveInteractiveAssetName(
                            *pLayout,
                            *interactiveResolved,
                            mouseX,
                            mouseY,
                            isLeftMousePressed)
                        : nullptr;

                if (pAssetName != nullptr)
                {
                    textureName = *pAssetName;
                }
            }

            const std::optional<GameplayOverlayContext::HudTextureHandle> texture =
                context.ensureHudTextureLoaded(textureName);
            const std::optional<GameplayOverlayContext::ResolvedHudLayoutElement> resolved = resolveLayout(layoutId);

            if (texture && resolved)
            {
                context.submitHudTexturedQuad(*texture, resolved->x, resolved->y, resolved->width, resolved->height);
            }
        }
    }

    const size_t clampedSelectedIndex = slots.empty() ? 0 : std::min(selectedIndex, slots.size() - 1);

    if (const std::optional<GameplayOverlayContext::ResolvedHudLayoutElement> previewRect = resolveLayout(pPreviewRectId))
    {
        submitSolidQuad(previewRect->x, previewRect->y, previewRect->width, previewRect->height, makeAbgrColor(0, 0, 0));

        if (!slots.empty())
        {
            const GameplayUiController::SaveSlotSummary &selectedSlot = slots[clampedSelectedIndex];

            if (selectedSlot.previewWidth > 0
                && selectedSlot.previewHeight > 0
                && !selectedSlot.previewPixelsBgra.empty())
            {
                const std::string cacheName = std::string("__save_load_preview_") + toLowerCopy(pScreenName);
                const std::optional<GameplayOverlayContext::HudTextureHandle> texture =
                    context.ensureDynamicHudTexture(
                        cacheName,
                        selectedSlot.previewWidth,
                        selectedSlot.previewHeight,
                        selectedSlot.previewPixelsBgra);

                if (texture && bgfx::isValid(texture->textureHandle))
                {
                    const float previewScale = std::min(
                        previewRect->width / static_cast<float>(selectedSlot.previewWidth),
                        previewRect->height / static_cast<float>(selectedSlot.previewHeight));
                    const float drawWidth = static_cast<float>(selectedSlot.previewWidth) * previewScale;
                    const float drawHeight = static_cast<float>(selectedSlot.previewHeight) * previewScale;
                    const float drawX = std::round(previewRect->x + (previewRect->width - drawWidth) * 0.5f);
                    const float drawY = std::round(previewRect->y + (previewRect->height - drawHeight) * 0.5f);
                    context.submitHudTexturedQuad(*texture, drawX, drawY, drawWidth, drawHeight);
                }
            }
        }
    }

    if (renderSelectedDetails && !slots.empty())
    {
        const GameplayUiController::SaveSlotSummary &selectedSlot = slots[clampedSelectedIndex];

        if (const GameplayOverlayContext::HudLayoutElement *pLayout = context.findHudLayoutElement(pSelectedNameId))
        {
            if (const std::optional<GameplayOverlayContext::ResolvedHudLayoutElement> resolved = resolveLayout(pSelectedNameId))
            {
                context.renderLayoutLabel(*pLayout, *resolved, selectedSlot.locationName);
            }
        }

        if (const GameplayOverlayContext::HudLayoutElement *pLayout = context.findHudLayoutElement(pPreviewLine1Id))
        {
            if (const std::optional<GameplayOverlayContext::ResolvedHudLayoutElement> resolved = resolveLayout(pPreviewLine1Id))
            {
                context.renderLayoutLabel(*pLayout, *resolved, selectedSlot.weekdayClockText);
            }
        }

        if (const GameplayOverlayContext::HudLayoutElement *pLayout = context.findHudLayoutElement(pPreviewLine2Id))
        {
            if (const std::optional<GameplayOverlayContext::ResolvedHudLayoutElement> resolved = resolveLayout(pPreviewLine2Id))
            {
                context.renderLayoutLabel(*pLayout, *resolved, selectedSlot.dateText);
            }
        }
    }

    for (size_t row = 0; row < SaveLoadVisibleSlotCount; ++row)
    {
        const size_t slotIndex = scrollOffset + row;
        const std::string layoutId = std::string(pRowPrefix) + std::to_string(row);
        const GameplayOverlayContext::HudLayoutElement *pLayout = context.findHudLayoutElement(layoutId);
        const std::optional<GameplayOverlayContext::ResolvedHudLayoutElement> resolved = resolveLayout(layoutId);

        if (pLayout == nullptr || !resolved)
        {
            continue;
        }

        std::string label = slotIndex < slots.size() ? slots[slotIndex].fileLabel : std::string();

        if (std::strcmp(pScreenName, "SaveGame") == 0
            && pSaveGameScreen != nullptr
            && pSaveGameScreen->editActive
            && slotIndex == pSaveGameScreen->editSlotIndex)
        {
            label = pSaveGameScreen->editBuffer;

            if ((SDL_GetTicks() / 500u) % 2u == 0u)
            {
                label += "_";
            }
        }

        if (label.empty())
        {
            continue;
        }

        GameplayOverlayContext::HudLayoutElement rowLayout = *pLayout;
        rowLayout.textColorAbgr = slotIndex == clampedSelectedIndex ? selectedRowColor : rowColor;
        context.renderLayoutLabel(rowLayout, *resolved, label);
    }

    const GameplayOverlayContext::HudLayoutElement *pThumbLayout = context.findHudLayoutElement(pThumbId);
    const std::optional<GameplayOverlayContext::ResolvedHudLayoutElement> baseThumbRect = resolveLayout(pThumbId);
    const std::optional<GameplayOverlayContext::ResolvedHudLayoutElement> upButtonRect = resolveLayout(pScrollUpId);
    const std::optional<GameplayOverlayContext::ResolvedHudLayoutElement> downButtonRect = resolveLayout(pScrollDownId);

    if (pThumbLayout != nullptr && baseThumbRect && upButtonRect && downButtonRect)
    {
        const std::optional<GameplayOverlayContext::HudTextureHandle> texture =
            context.ensureHudTextureLoaded(pThumbLayout->primaryAsset);

        if (texture)
        {
            float thumbY = baseThumbRect->y;

            if (slots.size() > SaveLoadVisibleSlotCount)
            {
                const float trackTop = upButtonRect->y + upButtonRect->height;
                const float trackBottom = downButtonRect->y;
                const float travel = std::max(0.0f, trackBottom - trackTop - baseThumbRect->height);
                const float maxOffset = static_cast<float>(slots.size() - SaveLoadVisibleSlotCount);
                const float t = maxOffset > 0.0f ? static_cast<float>(scrollOffset) / maxOffset : 0.0f;
                thumbY = std::round(trackTop + travel * t);
            }

            context.submitHudTexturedQuad(*texture, baseThumbRect->x, thumbY, baseThumbRect->width, baseThumbRect->height);
        }
    }
}

void GameplayPartyOverlayRenderer::renderSaveGameOverlay(GameplayOverlayContext &context, int width, int height)
{
    const GameplayUiController::SaveGameScreenState &saveGameScreen = context.saveGameScreenState();

    if (!saveGameScreen.active || width <= 0 || height <= 0)
    {
        return;
    }

    renderSaveLoadOverlay(
        context,
        width,
        height,
        "SaveGame",
        "SaveGameRoot",
        "SaveGameScrollThumb",
        "SaveGameScrollUpButton",
        "SaveGameScrollDownButton",
        "SaveGamePreviewRect",
        "SaveGameSelectedName",
        "SaveGamePreviewLine1",
        "SaveGamePreviewLine2",
        "SaveGameSlotRow",
        saveGameScreen.slots,
        saveGameScreen.scrollOffset,
        saveGameScreen.selectedIndex,
        true,
        &saveGameScreen);
}

void GameplayPartyOverlayRenderer::renderLoadGameOverlay(GameplayOverlayContext &context, int width, int height)
{
    const GameplayUiController::LoadGameScreenState &loadGameScreen = context.loadGameScreenState();

    if (!loadGameScreen.active || width <= 0 || height <= 0)
    {
        return;
    }

    renderSaveLoadOverlay(
        context,
        width,
        height,
        "LoadGame",
        "LoadGameRoot",
        "LoadGameScrollThumb",
        "LoadGameScrollUpButton",
        "LoadGameScrollDownButton",
        "LoadGamePreviewRect",
        "LoadGameSelectedName",
        "LoadGamePreviewLine1",
        "LoadGamePreviewLine2",
        "LoadGameSlotRow",
        loadGameScreen.slots,
        loadGameScreen.scrollOffset,
        loadGameScreen.selectedIndex,
        true,
        nullptr);
}

void GameplayPartyOverlayRenderer::renderJournalOverlay(GameplayOverlayContext &context, int width, int height)
{
    GameplayUiController::JournalScreenState &journalScreen = context.journalScreenState();

    if (!journalScreen.active || width <= 0 || height <= 0)
    {
        return;
    }

    const GameplayOverlayContext::HudLayoutElement *pRootLayout = context.findHudLayoutElement("JournalRoot");

    if (pRootLayout == nullptr)
    {
        return;
    }

    setupHudProjection(width, height);
    HudUiService::renderViewportSidePanels(context, width, height, "UI-Parch");

    float mouseX = 0.0f;
    float mouseY = 0.0f;
    const SDL_MouseButtonFlags mouseButtons = SDL_GetMouseState(&mouseX, &mouseY);
    const bool isLeftMousePressed = (mouseButtons & SDL_BUTTON_LMASK) != 0;

    const auto loadHudTexture =
        [&context](const std::string &textureName) -> std::optional<GameplayOverlayContext::HudTextureHandle>
        {
            return context.ensureHudTextureLoaded(textureName);
        };

    const auto resolveLayout =
        [&context, width, height](const std::string &layoutId)
        -> std::optional<GameplayOverlayContext::ResolvedHudLayoutElement>
        {
            const GameplayOverlayContext::HudLayoutElement *pLayout = context.findHudLayoutElement(layoutId);

            if (pLayout == nullptr)
            {
                return std::nullopt;
            }

            return context.resolveHudLayoutElement(layoutId, width, height, pLayout->width, pLayout->height);
        };

    const auto renderTextureLayout =
        [&context, &loadHudTexture, &resolveLayout](const std::string &layoutId, const std::string &textureName)
        {
            const std::optional<GameplayOverlayContext::HudTextureHandle> texture = loadHudTexture(textureName);
            const std::optional<GameplayOverlayContext::ResolvedHudLayoutElement> resolved = resolveLayout(layoutId);

            if (!texture || !resolved)
            {
                return;
            }

            context.submitHudTexturedQuad(*texture, resolved->x, resolved->y, resolved->width, resolved->height);
        };

    const auto renderInteractiveTextureLayout =
        [&context, &loadHudTexture, &resolveLayout, mouseX, mouseY, isLeftMousePressed](
            const std::string &layoutId,
            const std::string *pOverrideTextureName = nullptr)
        {
            const GameplayOverlayContext::HudLayoutElement *pLayout = context.findHudLayoutElement(layoutId);
            const std::optional<GameplayOverlayContext::ResolvedHudLayoutElement> resolved = resolveLayout(layoutId);

            if (pLayout == nullptr || !resolved)
            {
                return;
            }

            std::string textureName = pOverrideTextureName != nullptr ? *pOverrideTextureName : pLayout->primaryAsset;

            if (pOverrideTextureName == nullptr && pLayout->interactive)
            {
                const std::string *pInteractiveTextureName =
                    context.resolveInteractiveAssetName(*pLayout, *resolved, mouseX, mouseY, isLeftMousePressed);

                if (pInteractiveTextureName != nullptr)
                {
                    textureName = *pInteractiveTextureName;
                }
            }

            const std::optional<GameplayOverlayContext::HudTextureHandle> texture = loadHudTexture(textureName);

            if (!texture)
            {
                return;
            }

            context.submitHudTexturedQuad(*texture, resolved->x, resolved->y, resolved->width, resolved->height);
        };

    const auto submitTexturedQuadUv =
        [&context](const GameplayOverlayContext::HudTextureHandle &texture,
                   float x,
                   float y,
                   float quadWidth,
                   float quadHeight,
                   float u0,
                   float v0,
                   float u1,
                   float v1)
        {
            if (!bgfx::isValid(texture.textureHandle))
            {
                return;
            }

            context.submitWorldTextureQuad(texture.textureHandle, x, y, quadWidth, quadHeight, u0, v0, u1, v1);
        };

    const auto submitTexturedQuadClipped =
        [&submitTexturedQuadUv](const GameplayOverlayContext::HudTextureHandle &texture,
                                float x,
                                float y,
                                float quadWidth,
                                float quadHeight,
                                float clipX,
                                float clipY,
                                float clipWidth,
                                float clipHeight)
        {
            const float quadRight = x + quadWidth;
            const float quadBottom = y + quadHeight;
            const float clipRight = clipX + clipWidth;
            const float clipBottom = clipY + clipHeight;
            const float clippedLeft = std::max(x, clipX);
            const float clippedTop = std::max(y, clipY);
            const float clippedRight = std::min(quadRight, clipRight);
            const float clippedBottom = std::min(quadBottom, clipBottom);

            if (clippedLeft >= clippedRight || clippedTop >= clippedBottom || quadWidth <= 0.0f || quadHeight <= 0.0f)
            {
                return;
            }

            const float u0 = (clippedLeft - x) / quadWidth;
            const float v0 = (clippedTop - y) / quadHeight;
            const float u1 = (clippedRight - x) / quadWidth;
            const float v1 = (clippedBottom - y) / quadHeight;
            submitTexturedQuadUv(
                texture,
                clippedLeft,
                clippedTop,
                clippedRight - clippedLeft,
                clippedBottom - clippedTop,
                u0,
                v0,
                u1,
                v1);
        };

    renderTextureLayout("JournalBackground", "IRBgrnd");

    const std::optional<GameplayOverlayContext::ResolvedHudLayoutElement> mapMainResolved =
        resolveLayout("JournalMainViewMap");
    const std::optional<GameplayOverlayContext::ResolvedHudLayoutElement> questsMainResolved =
        resolveLayout("JournalMainViewQuests");
    const std::optional<GameplayOverlayContext::ResolvedHudLayoutElement> storyMainResolved =
        resolveLayout("JournalMainViewStory");
    const std::optional<GameplayOverlayContext::ResolvedHudLayoutElement> notesMainResolved =
        resolveLayout("JournalMainViewNotes");
    const bool hoverMap =
        mapMainResolved && context.isPointerInsideResolvedElement(*mapMainResolved, mouseX, mouseY);
    const bool hoverQuests =
        questsMainResolved && context.isPointerInsideResolvedElement(*questsMainResolved, mouseX, mouseY);
    const bool hoverStory =
        storyMainResolved && context.isPointerInsideResolvedElement(*storyMainResolved, mouseX, mouseY);
    const bool hoverNotes =
        notesMainResolved && context.isPointerInsideResolvedElement(*notesMainResolved, mouseX, mouseY);
    const std::string mapIconTexture =
        journalMainIconTextureName("IRA-1", 10, hoverMap, journalScreen.hoverAnimationElapsedSeconds);
    const std::string questsIconTexture =
        journalMainIconTextureName("IRA-2", 10, hoverQuests, journalScreen.hoverAnimationElapsedSeconds);
    const std::string storyIconTexture =
        journalMainIconTextureName("IRA-3", 9, hoverStory, journalScreen.hoverAnimationElapsedSeconds);
    const std::string notesIconTexture =
        journalMainIconTextureName("IRA-4", 11, hoverNotes, journalScreen.hoverAnimationElapsedSeconds);

    renderInteractiveTextureLayout("JournalMainViewMap", &mapIconTexture);
    renderInteractiveTextureLayout("JournalMainViewQuests", &questsIconTexture);
    renderInteractiveTextureLayout("JournalMainViewStory", &storyIconTexture);
    renderInteractiveTextureLayout("JournalMainViewNotes", &notesIconTexture);

    switch (journalScreen.view)
    {
        case GameplayUiController::JournalView::Map:
            break;
        case GameplayUiController::JournalView::Quests:
            renderTextureLayout("JournalQuestsTopLeftArt", "IRB-2");
            break;
        case GameplayUiController::JournalView::Story:
            renderTextureLayout("JournalStoryTopLeftArt", "IRB-3");
            break;
        case GameplayUiController::JournalView::Notes:
            renderTextureLayout("JournalNotesTopLeftArt", "IRB-4");
            break;
    }

    const GameplayOverlayContext::HudLayoutElement *pTitleLayout = context.findHudLayoutElement("JournalTitleText");
    const GameplayOverlayContext::HudLayoutElement *pTextLayout = context.findHudLayoutElement("JournalTextViewport");
    const std::optional<GameplayOverlayContext::ResolvedHudLayoutElement> titleResolved = resolveLayout("JournalTitleText");
    const std::optional<GameplayOverlayContext::ResolvedHudLayoutElement> textResolved = resolveLayout("JournalTextViewport");
    const std::optional<GameplayOverlayContext::HudFontHandle> bodyFont =
        pTextLayout != nullptr ? context.findHudFont(pTextLayout->fontName) : std::nullopt;

    if (journalScreen.view == GameplayUiController::JournalView::Map)
    {
        renderInteractiveTextureLayout("JournalMapZoomInButton");
        renderInteractiveTextureLayout("JournalMapZoomOutButton");

        const std::optional<GameplayOverlayContext::ResolvedHudLayoutElement> mapResolved = resolveLayout("JournalMapViewport");
        const GameplayOverlayContext::HudLayoutElement *pMapTitleLayout = context.findHudLayoutElement("JournalMapTitleText");
        const std::optional<GameplayOverlayContext::ResolvedHudLayoutElement> mapTitleResolved =
            resolveLayout("JournalMapTitleText");
        IGameplayWorldRuntime *pWorldRuntime = context.worldRuntime();

        if (pMapTitleLayout != nullptr && mapTitleResolved && pWorldRuntime != nullptr)
        {
            context.renderLayoutLabel(*pMapTitleLayout, *mapTitleResolved, pWorldRuntime->mapName());
        }

        if (mapResolved)
        {
            const std::string mapTextureName = toLowerCopy(std::filesystem::path(context.currentMapFileName()).stem().string());
            int mapTextureWidth = 0;
            int mapTextureHeight = 0;
            const std::vector<uint8_t> *pMapPixels =
                mapTextureName.empty() ? nullptr : context.hudTexturePixels(mapTextureName, mapTextureWidth, mapTextureHeight);

            if (pMapPixels != nullptr)
            {
                const int zoom = clampedJournalMapZoomValue(journalScreen.mapZoomStep);
                const int mapPixelWidth = std::max(1, static_cast<int>(std::lround(mapResolved->width)));
                const int mapPixelHeight = std::max(1, static_cast<int>(std::lround(mapResolved->height)));
                const bool needsMapRebuild =
                    !journalScreen.cachedMapValid
                    || journalScreen.cachedMapWidth != mapPixelWidth
                    || journalScreen.cachedMapHeight != mapPixelHeight
                    || journalScreen.cachedMapZoomStep != journalScreen.mapZoomStep
                    || std::abs(journalScreen.cachedMapCenterX - journalScreen.mapCenterX) > 0.01f
                    || std::abs(journalScreen.cachedMapCenterY - journalScreen.mapCenterY) > 0.01f;
                std::optional<GameplayOverlayContext::HudTextureHandle> journalMapTexture =
                    context.ensureHudTextureLoaded(JournalMapTextureCacheName);

                if (needsMapRebuild)
                {
                    const float zoomFactor = static_cast<float>(zoom) / static_cast<float>(JournalMapBaseZoom);
                    const float sourceCenterX =
                        ((journalScreen.mapCenterX + JournalMapWorldHalfExtent) / (JournalMapWorldHalfExtent * 2.0f))
                        * static_cast<float>(mapTextureWidth);
                    const float sourceCenterY =
                        ((JournalMapWorldHalfExtent - journalScreen.mapCenterY) / (JournalMapWorldHalfExtent * 2.0f))
                        * static_cast<float>(mapTextureHeight);
                    const float sourceWindowWidth =
                        static_cast<float>(mapTextureWidth) / std::max(zoomFactor, 0.000001f);
                    const float sourceWindowHeight =
                        static_cast<float>(mapTextureHeight) / std::max(zoomFactor, 0.000001f);
                    const float sourceOriginX = sourceCenterX - sourceWindowWidth * 0.5f;
                    const float sourceOriginY = sourceCenterY - sourceWindowHeight * 0.5f;
                    std::vector<uint8_t> composedMapPixels(
                        static_cast<size_t>(mapPixelWidth) * static_cast<size_t>(mapPixelHeight) * 4,
                        0);
                    const std::vector<uint8_t> *pFullyRevealedCells = context.journalMapFullyRevealedCells();
                    const std::vector<uint8_t> *pPartiallyRevealedCells = context.journalMapPartiallyRevealedCells();

                    for (int pixelY = 0; pixelY < mapPixelHeight; ++pixelY)
                    {
                        const float sourceYFloat =
                            sourceOriginY
                            + ((static_cast<float>(pixelY) + 0.5f) / static_cast<float>(mapPixelHeight))
                                * sourceWindowHeight;
                        const int sourceY = static_cast<int>(std::floor(sourceYFloat));
                        const float revealV =
                            std::clamp(sourceYFloat / static_cast<float>(mapTextureHeight), 0.0f, 0.999999f);
                        const int revealCellY =
                            static_cast<int>(std::floor(revealV * static_cast<float>(JournalRevealHeight)));

                        for (int pixelX = 0; pixelX < mapPixelWidth; ++pixelX)
                        {
                            const float sourceXFloat =
                                sourceOriginX
                                + ((static_cast<float>(pixelX) + 0.5f) / static_cast<float>(mapPixelWidth))
                                    * sourceWindowWidth;
                            const int sourceX = static_cast<int>(std::floor(sourceXFloat));
                            const float revealU =
                                std::clamp(sourceXFloat / static_cast<float>(mapTextureWidth), 0.0f, 0.999999f);
                            const int revealCellX =
                                static_cast<int>(std::floor(revealU * static_cast<float>(JournalRevealWidth)));
                            const size_t targetOffset =
                                (static_cast<size_t>(pixelY) * static_cast<size_t>(mapPixelWidth)
                                    + static_cast<size_t>(pixelX))
                                * 4;
                            bool fullyRevealed = false;
                            bool partiallyRevealed = false;

                            if (pFullyRevealedCells != nullptr
                                && pPartiallyRevealedCells != nullptr
                                && revealCellX >= 0 && revealCellX < JournalRevealWidth
                                && revealCellY >= 0 && revealCellY < JournalRevealHeight)
                            {
                                const size_t revealIndex =
                                    static_cast<size_t>(revealCellY * JournalRevealWidth + revealCellX);
                                fullyRevealed = packedRevealBit(*pFullyRevealedCells, revealIndex);
                                partiallyRevealed = packedRevealBit(*pPartiallyRevealedCells, revealIndex);
                            }
                            else if (pFullyRevealedCells == nullptr || pPartiallyRevealedCells == nullptr)
                            {
                                fullyRevealed = true;
                            }

                            if (!fullyRevealed && !partiallyRevealed)
                            {
                                composedMapPixels[targetOffset + 3] = 255;
                                continue;
                            }

                            if (sourceX < 0 || sourceX >= mapTextureWidth || sourceY < 0 || sourceY >= mapTextureHeight)
                            {
                                composedMapPixels[targetOffset + 3] = 255;
                                continue;
                            }

                            const bool drawBlackChecker = partiallyRevealed
                                && (((pixelX + pixelY + mapPixelWidth / 2) % 2) == 0);

                            if (drawBlackChecker)
                            {
                                composedMapPixels[targetOffset + 3] = 255;
                                continue;
                            }

                            const size_t sourceOffset =
                                (static_cast<size_t>(sourceY) * static_cast<size_t>(mapTextureWidth)
                                    + static_cast<size_t>(sourceX))
                                * 4;
                            composedMapPixels[targetOffset + 0] = (*pMapPixels)[sourceOffset + 0];
                            composedMapPixels[targetOffset + 1] = (*pMapPixels)[sourceOffset + 1];
                            composedMapPixels[targetOffset + 2] = (*pMapPixels)[sourceOffset + 2];
                            composedMapPixels[targetOffset + 3] = 255;
                        }
                    }

                    journalMapTexture =
                        context.ensureDynamicHudTexture(JournalMapTextureCacheName, mapPixelWidth, mapPixelHeight, composedMapPixels);

                    if (journalMapTexture)
                    {
                        journalScreen.cachedMapValid = true;
                        journalScreen.cachedMapWidth = mapPixelWidth;
                        journalScreen.cachedMapHeight = mapPixelHeight;
                        journalScreen.cachedMapZoomStep = journalScreen.mapZoomStep;
                        journalScreen.cachedMapCenterX = journalScreen.mapCenterX;
                        journalScreen.cachedMapCenterY = journalScreen.mapCenterY;
                    }
                    else
                    {
                        journalScreen.cachedMapValid = false;
                    }
                }

                if (journalMapTexture)
                {
                    context.submitHudTexturedQuad(
                        *journalMapTexture,
                        mapResolved->x,
                        mapResolved->y,
                        mapResolved->width,
                        mapResolved->height);
                }

                if (pWorldRuntime != nullptr && context.partyReadOnly() != nullptr)
                {
                    const float zoomFactor = static_cast<float>(zoom) / static_cast<float>(JournalMapBaseZoom);
                    const float sourceCenterX =
                        ((journalScreen.mapCenterX + JournalMapWorldHalfExtent) / (JournalMapWorldHalfExtent * 2.0f))
                        * static_cast<float>(mapTextureWidth);
                    const float sourceCenterY =
                        ((JournalMapWorldHalfExtent - journalScreen.mapCenterY) / (JournalMapWorldHalfExtent * 2.0f))
                        * static_cast<float>(mapTextureHeight);
                    const float sourceWindowWidth =
                        static_cast<float>(mapTextureWidth) / std::max(zoomFactor, 0.000001f);
                    const float sourceWindowHeight =
                        static_cast<float>(mapTextureHeight) / std::max(zoomFactor, 0.000001f);
                    const float sourceOriginX = sourceCenterX - sourceWindowWidth * 0.5f;
                    const float sourceOriginY = sourceCenterY - sourceWindowHeight * 0.5f;
                    const float partySourceX =
                        ((context.partyX() + JournalMapWorldHalfExtent) / (JournalMapWorldHalfExtent * 2.0f))
                        * static_cast<float>(mapTextureWidth);
                    const float partySourceY =
                        ((JournalMapWorldHalfExtent - context.partyY()) / (JournalMapWorldHalfExtent * 2.0f))
                        * static_cast<float>(mapTextureHeight);
                    const float markerX =
                        mapResolved->x
                        + ((partySourceX - sourceOriginX) / std::max(sourceWindowWidth, 0.000001f))
                            * mapResolved->width;
                    const float markerY =
                        mapResolved->y
                        + ((partySourceY - sourceOriginY) / std::max(sourceWindowHeight, 0.000001f))
                            * mapResolved->height;
                    const int arrowIndex = outdoorMinimapArrowIndex(context.gameplayCameraYawRadians());
                    const std::optional<GameplayOverlayContext::HudTextureHandle> arrowTexture =
                        loadHudTexture("MAPDIR" + std::to_string(arrowIndex + 1));

                    if (arrowTexture)
                    {
                        const float arrowWidth = static_cast<float>(arrowTexture->width) * mapResolved->scale;
                        const float arrowHeight = static_cast<float>(arrowTexture->height) * mapResolved->scale;
                        submitTexturedQuadClipped(
                            *arrowTexture,
                            markerX - arrowWidth * 0.5f,
                            markerY - arrowHeight * 0.5f,
                            arrowWidth,
                            arrowHeight,
                            mapResolved->x,
                            mapResolved->y,
                            mapResolved->width,
                            mapResolved->height);
                    }

                    const GameplayOverlayContext::HudLayoutElement *pCoordsLayout =
                        context.findHudLayoutElement("JournalMapCoordinatesText");
                    const std::optional<GameplayOverlayContext::ResolvedHudLayoutElement> coordsResolved =
                        resolveLayout("JournalMapCoordinatesText");

                    if (pCoordsLayout != nullptr && coordsResolved)
                    {
                        const std::string coordsText =
                            "X: " + std::to_string(static_cast<int>(std::round(context.partyX())))
                            + "  Y: " + std::to_string(static_cast<int>(std::round(context.partyY())))
                            + "  Z: " + std::to_string(zoom);
                        context.renderLayoutLabel(*pCoordsLayout, *coordsResolved, coordsText);
                    }
                }
            }
        }
    }
    else if (pTitleLayout != nullptr && titleResolved && pTextLayout != nullptr && textResolved && bodyFont)
    {
        const float bodyFontScale = textResolved->scale >= 1.0f
            ? snappedHudFontScale(textResolved->scale)
            : std::max(0.5f, textResolved->scale);
        const IGameplayWorldRuntime *pWorldRuntime = context.worldRuntime();
        const EventRuntimeState *pEventRuntimeState = pWorldRuntime != nullptr ? pWorldRuntime->eventRuntimeState() : nullptr;
        const Party *pParty = context.partyReadOnly();
        std::vector<std::string> bodyLines;
        std::string titleText;

        if (journalScreen.view == GameplayUiController::JournalView::Quests)
        {
            titleText = "Current Quests";
            renderInteractiveTextureLayout("JournalPrevPageButton");
            renderInteractiveTextureLayout("JournalNextPageButton");

            std::vector<std::string> questTexts;
            const JournalQuestTable *pJournalQuestTable = context.journalQuestTable();

            if (pJournalQuestTable != nullptr && pEventRuntimeState != nullptr)
            {
                for (const JournalQuestEntry &entry : pJournalQuestTable->entries())
                {
                    const auto variableIt = pEventRuntimeState->variables.find(entry.qbitId);

                    if (variableIt != pEventRuntimeState->variables.end() && variableIt->second != 0)
                    {
                        questTexts.push_back(entry.text);
                    }
                }
            }

            const std::vector<JournalStackedPage> pages = buildJournalStackedPages(
                context,
                *bodyFont,
                questTexts,
                textResolved->width,
                textResolved->height,
                bodyFontScale);
            const size_t pageIndex = pages.empty() ? 0 : std::min(journalScreen.questPage, pages.size() - 1);

            if (!pages.empty())
            {
                float textY = textResolved->y;
                const float lineHeight = static_cast<float>(bodyFont->fontHeight) * bodyFontScale;
                const std::optional<GameplayOverlayContext::HudTextureHandle> dividerTexture = loadHudTexture("DIVBAR");

                for (size_t entryIndex = 0; entryIndex < pages[pageIndex].entries.size(); ++entryIndex)
                {
                    const JournalStackedPageEntry &entry = pages[pageIndex].entries[entryIndex];
                    renderHudLines(context, *bodyFont, pTextLayout->textColorAbgr, entry.lines, textResolved->x, textY, bodyFontScale);
                    textY += static_cast<float>(entry.lines.size()) * lineHeight;

                    if (entryIndex + 1 < pages[pageIndex].entries.size() && dividerTexture)
                    {
                        const float dividerWidth =
                            std::min(textResolved->width, static_cast<float>(dividerTexture->width) * textResolved->scale);
                        const float dividerHeight = static_cast<float>(dividerTexture->height) * textResolved->scale;
                        const float dividerX = textResolved->x + (textResolved->width - dividerWidth) * 0.5f;
                        textY += 7.0f * bodyFontScale;
                        context.submitHudTexturedQuad(*dividerTexture, dividerX, textY, dividerWidth, dividerHeight);
                        textY += dividerHeight + 9.0f * bodyFontScale;
                    }
                }
            }
        }
        else if (journalScreen.view == GameplayUiController::JournalView::Story)
        {
            renderInteractiveTextureLayout("JournalPrevPageButton");
            renderInteractiveTextureLayout("JournalNextPageButton");

            const JournalHistoryTable *pJournalHistoryTable = context.journalHistoryTable();
            const std::vector<JournalStoryPage> pages =
                pJournalHistoryTable != nullptr
                    ? buildJournalStoryPages(
                        context,
                        *bodyFont,
                        *pJournalHistoryTable,
                        pEventRuntimeState,
                        pParty,
                        textResolved->width,
                        textResolved->height,
                        bodyFontScale)
                    : std::vector<JournalStoryPage>{};
            const size_t pageIndex = pages.empty() ? 0 : std::min(journalScreen.storyPage, pages.size() - 1);

            if (!pages.empty())
            {
                titleText = pages[pageIndex].title;
                bodyLines = pages[pageIndex].lines;
            }
            else
            {
                titleText = "Story";
            }
        }
        else
        {
            titleText = journalNotesCategoryTitle(journalScreen.notesCategory);
            renderInteractiveTextureLayout("JournalPrevPageButton");
            renderInteractiveTextureLayout("JournalNextPageButton");
            renderInteractiveTextureLayout("JournalNotesPotionButton");
            renderInteractiveTextureLayout("JournalNotesFountainButton");
            renderInteractiveTextureLayout("JournalNotesObeliskButton");
            renderInteractiveTextureLayout("JournalNotesSeerButton");
            renderInteractiveTextureLayout("JournalNotesMiscButton");
            renderInteractiveTextureLayout("JournalNotesTrainerButton");

            std::vector<std::string> noteTexts;
            const JournalAutonoteTable *pJournalAutonoteTable = context.journalAutonoteTable();

            if (pJournalAutonoteTable != nullptr && pEventRuntimeState != nullptr)
            {
                for (const JournalAutonoteEntry &entry : pJournalAutonoteTable->entries())
                {
                    const auto variableIt = pEventRuntimeState->variables.find(entry.noteBit);

                    if (variableIt == pEventRuntimeState->variables.end() || variableIt->second == 0)
                    {
                        continue;
                    }

                    const bool categoryMatches =
                        (entry.category == JournalAutonoteCategory::Potion
                            && journalScreen.notesCategory == GameplayUiController::JournalNotesCategory::Potion)
                        || (entry.category == JournalAutonoteCategory::Fountain
                            && journalScreen.notesCategory == GameplayUiController::JournalNotesCategory::Fountain)
                        || (entry.category == JournalAutonoteCategory::Obelisk
                            && journalScreen.notesCategory == GameplayUiController::JournalNotesCategory::Obelisk)
                        || (entry.category == JournalAutonoteCategory::Seer
                            && journalScreen.notesCategory == GameplayUiController::JournalNotesCategory::Seer)
                        || (entry.category == JournalAutonoteCategory::Misc
                            && journalScreen.notesCategory == GameplayUiController::JournalNotesCategory::Misc)
                        || (entry.category == JournalAutonoteCategory::Trainer
                            && journalScreen.notesCategory == GameplayUiController::JournalNotesCategory::Trainer);

                    if (categoryMatches)
                    {
                        noteTexts.push_back(entry.text);
                    }
                }
            }

            const std::vector<JournalStackedPage> pages = buildJournalStackedPages(
                context,
                *bodyFont,
                noteTexts,
                textResolved->width,
                textResolved->height,
                bodyFontScale);
            const size_t pageIndex = pages.empty() ? 0 : std::min(journalScreen.notesPage, pages.size() - 1);

            if (!pages.empty())
            {
                float textY = textResolved->y;
                const float lineHeight = static_cast<float>(bodyFont->fontHeight) * bodyFontScale;
                const std::optional<GameplayOverlayContext::HudTextureHandle> dividerTexture = loadHudTexture("DIVBAR");

                for (size_t entryIndex = 0; entryIndex < pages[pageIndex].entries.size(); ++entryIndex)
                {
                    const JournalStackedPageEntry &entry = pages[pageIndex].entries[entryIndex];
                    renderHudLines(context, *bodyFont, pTextLayout->textColorAbgr, entry.lines, textResolved->x, textY, bodyFontScale);
                    textY += static_cast<float>(entry.lines.size()) * lineHeight;

                    if (entryIndex + 1 < pages[pageIndex].entries.size() && dividerTexture)
                    {
                        const float dividerWidth =
                            std::min(textResolved->width, static_cast<float>(dividerTexture->width) * textResolved->scale);
                        const float dividerHeight = static_cast<float>(dividerTexture->height) * textResolved->scale;
                        const float dividerX = textResolved->x + (textResolved->width - dividerWidth) * 0.5f;
                        textY += 7.0f * bodyFontScale;
                        context.submitHudTexturedQuad(*dividerTexture, dividerX, textY, dividerWidth, dividerHeight);
                        textY += dividerHeight + 9.0f * bodyFontScale;
                    }
                }
            }
        }

        context.renderLayoutLabel(*pTitleLayout, *titleResolved, titleText);

        if (!bodyLines.empty())
        {
            renderHudLines(context, *bodyFont, pTextLayout->textColorAbgr, bodyLines, textResolved->x, textResolved->y, bodyFontScale);
        }
    }

    renderInteractiveTextureLayout("JournalCloseButton");
}

void GameplayPartyOverlayRenderer::renderUtilitySpellOverlay(const OutdoorGameView &view, int width, int height)
{
    if (!view.m_utilitySpellOverlay.active
        || view.m_utilitySpellOverlay.mode == OutdoorGameView::UtilitySpellOverlayMode::InventoryTarget
        || !bgfx::isValid(view.m_texturedTerrainProgramHandle)
        || !bgfx::isValid(view.m_terrainTextureSamplerHandle)
        || width <= 0
        || height <= 0)
    {
        return;
    }

    setupHudProjection(width, height);
    renderViewportParchmentSidePanels(view, width, height);

    float mouseX = 0.0f;
    float mouseY = 0.0f;
    const SDL_MouseButtonFlags mouseButtons = SDL_GetMouseState(&mouseX, &mouseY);
    const bool isLeftMousePressed = (mouseButtons & SDL_BUTTON_LMASK) != 0;
    const EventRuntimeState *pEventRuntimeState =
        view.m_pOutdoorWorldRuntime != nullptr ? view.m_pOutdoorWorldRuntime->eventRuntimeState() : nullptr;

    if (view.m_utilitySpellOverlay.mode == OutdoorGameView::UtilitySpellOverlayMode::TownPortal)
    {
        const Party *pParty = view.m_pOutdoorPartyRuntime != nullptr ? &view.m_pOutdoorPartyRuntime->party() : nullptr;
        const std::vector<std::string> orderedLayoutIds = HudUiService::sortedHudLayoutIdsForScreen(view, "TownPortal");
        const auto findDestinationByLayoutId =
            [&view](const std::string &layoutId) -> const OutdoorGameView::TownPortalDestination *
            {
                const std::string normalizedLayoutId = toLowerCopy(layoutId);

                for (const OutdoorGameView::TownPortalDestination &destination : view.m_townPortalDestinations)
                {
                    if (toLowerCopy(destination.buttonLayoutId) == normalizedLayoutId)
                    {
                        return &destination;
                    }
                }

                return nullptr;
            };
        const auto resolveLayout =
            [&view, width, height](const std::string &layoutId) -> std::optional<OutdoorGameView::ResolvedHudLayoutElement>
            {
                const OutdoorGameView::HudLayoutElement *pLayout = HudUiService::findHudLayoutElement(view, layoutId);

                if (pLayout == nullptr)
                {
                    return std::nullopt;
                }

                return HudUiService::resolveHudLayoutElement(view, layoutId, width, height, pLayout->width, pLayout->height);
            };

        for (const std::string &layoutId : orderedLayoutIds)
        {
            const OutdoorGameView::HudLayoutElement *pLayout = HudUiService::findHudLayoutElement(view, layoutId);

            if (pLayout == nullptr || !pLayout->visible)
            {
                continue;
            }

            const OutdoorGameView::TownPortalDestination *pDestination = findDestinationByLayoutId(layoutId);

            if (pDestination != nullptr && !isUtilityTownPortalDestinationUnlocked(pParty, *pDestination))
            {
                continue;
            }

            const std::optional<OutdoorGameView::ResolvedHudLayoutElement> resolved = resolveLayout(layoutId);

            if (!resolved.has_value())
            {
                continue;
            }

            const std::string *pAssetName =
                pLayout->interactive
                    ? HudUiService::resolveInteractiveAssetName(*pLayout, *resolved, mouseX, mouseY, isLeftMousePressed)
                    : &pLayout->primaryAsset;

            if (pAssetName == nullptr || pAssetName->empty())
            {
                continue;
            }

            const OutdoorGameView::HudTextureHandle *pTexture =
                HudUiService::ensureHudTextureLoaded(const_cast<OutdoorGameView &>(view), *pAssetName);

            if (pTexture == nullptr)
            {
                continue;
            }

            view.submitHudTexturedQuad(*pTexture, resolved->x, resolved->y, resolved->width, resolved->height);
        }

        return;
    }

    const UtilityOverlayRenderLayout layout = computeUtilityOverlayRenderLayout(width, height);
    const uint32_t screenShadeColor = makeAbgrColor(0, 0, 0, 144);
    const uint32_t panelColor = makeAbgrColor(18, 24, 32, 235);
    const uint32_t borderColor = makeAbgrColor(100, 134, 170, 255);
    const uint32_t titleColor = makeAbgrColor(255, 228, 176);
    const uint32_t textColor = makeAbgrColor(232, 236, 242);
    const uint32_t mutedColor = makeAbgrColor(150, 160, 174);
    const uint32_t rowColor = makeAbgrColor(34, 43, 57, 220);
    const uint32_t hoverRowColor = makeAbgrColor(52, 69, 92, 235);
    const uint32_t activeTabColor = makeAbgrColor(80, 112, 148, 255);
    const uint32_t inactiveTabColor = makeAbgrColor(42, 54, 70, 230);
    const uint32_t closeHoverColor = makeAbgrColor(128, 52, 52, 255);
    const float borderThickness = std::max(1.0f, std::round(2.0f * layout.scale));

    const auto submitSolidQuad =
        [&view](float x, float y, float quadWidth, float quadHeight, uint32_t abgr)
        {
            if (quadWidth <= 0.0f || quadHeight <= 0.0f)
            {
                return;
            }

            const std::string textureName = "__utility_overlay_solid_" + std::to_string(abgr);
            const OutdoorGameView::HudTextureHandle *pTexture =
                HudUiService::ensureSolidHudTextureLoaded(
                    const_cast<OutdoorGameView &>(view),
                    textureName,
                    abgr);

            if (pTexture != nullptr)
            {
                view.submitHudTexturedQuad(*pTexture, x, y, quadWidth, quadHeight);
            }
        };
    const auto renderLabel =
        [&view](const std::string &text,
            float x,
            float y,
            float rectWidth,
            float rectHeight,
            float scale,
            const char *pFontName,
            uint32_t colorAbgr,
            OutdoorGameView::HudTextAlignX alignX,
            OutdoorGameView::HudTextAlignY alignY)
        {
            OutdoorGameView::HudLayoutElement labelLayout = {};
            labelLayout.fontName = pFontName;
            labelLayout.textColorAbgr = colorAbgr;
            labelLayout.textAlignX = alignX;
            labelLayout.textAlignY = alignY;

            OutdoorGameView::ResolvedHudLayoutElement labelRect = {};
            labelRect.x = x;
            labelRect.y = y;
            labelRect.width = rectWidth;
            labelRect.height = rectHeight;
            labelRect.scale = scale;
            HudUiService::renderLayoutLabel(view, labelLayout, labelRect, text);
        };

    submitSolidQuad(0.0f, 0.0f, static_cast<float>(width), static_cast<float>(height), screenShadeColor);
    submitSolidQuad(layout.panelX, layout.panelY, layout.panelWidth, layout.panelHeight, panelColor);
    submitSolidQuad(layout.panelX, layout.panelY, layout.panelWidth, borderThickness, borderColor);
    submitSolidQuad(layout.panelX, layout.panelY + layout.panelHeight - borderThickness, layout.panelWidth, borderThickness, borderColor);
    submitSolidQuad(layout.panelX, layout.panelY, borderThickness, layout.panelHeight, borderColor);
    submitSolidQuad(
        layout.panelX + layout.panelWidth - borderThickness,
        layout.panelY,
        borderThickness,
        layout.panelHeight,
        borderColor);

    const bool closeHovered =
        utilityOverlayPointInsideRect(mouseX, mouseY, layout.closeX, layout.closeY, layout.closeSize, layout.closeSize);
    submitSolidQuad(
        layout.closeX,
        layout.closeY,
        layout.closeSize,
        layout.closeSize,
        closeHovered ? closeHoverColor : inactiveTabColor);
    renderLabel(
        "X",
        layout.closeX,
        layout.closeY,
        layout.closeSize,
        layout.closeSize,
        layout.scale,
        "arrus",
        makeAbgrColor(255, 255, 255),
        OutdoorGameView::HudTextAlignX::Center,
        OutdoorGameView::HudTextAlignY::Middle);

    if (view.m_utilitySpellOverlay.mode != OutdoorGameView::UtilitySpellOverlayMode::LloydsBeacon)
    {
        return;
    }

    renderLabel(
        "Lloyd's Beacon",
        layout.titleX,
        layout.titleY,
        layout.contentWidth,
        24.0f * layout.scale,
        layout.scale,
        "arrus",
        titleColor,
        OutdoorGameView::HudTextAlignX::Left,
        OutdoorGameView::HudTextAlignY::Top);

    const float tabY = layout.panelY + 48.0f * layout.scale;
    const float setTabX = layout.contentX;
    const float recallTabX = setTabX + layout.tabWidth + layout.tabGap;
    const bool setHovered =
        utilityOverlayPointInsideRect(mouseX, mouseY, setTabX, tabY, layout.tabWidth, layout.tabHeight);
    const bool recallHovered =
        utilityOverlayPointInsideRect(mouseX, mouseY, recallTabX, tabY, layout.tabWidth, layout.tabHeight);
    const bool recallMode = view.m_utilitySpellOverlay.lloydRecallMode;

    submitSolidQuad(
        setTabX,
        tabY,
        layout.tabWidth,
        layout.tabHeight,
        !recallMode ? activeTabColor : (setHovered ? hoverRowColor : inactiveTabColor));
    submitSolidQuad(
        recallTabX,
        tabY,
        layout.tabWidth,
        layout.tabHeight,
        recallMode ? activeTabColor : (recallHovered ? hoverRowColor : inactiveTabColor));
    renderLabel(
        "Set",
        setTabX,
        tabY,
        layout.tabWidth,
        layout.tabHeight,
        layout.scale,
        "Lucida",
        textColor,
        OutdoorGameView::HudTextAlignX::Center,
        OutdoorGameView::HudTextAlignY::Middle);
    renderLabel(
        "Recall",
        recallTabX,
        tabY,
        layout.tabWidth,
        layout.tabHeight,
        layout.scale,
        "Lucida",
        textColor,
        OutdoorGameView::HudTextAlignX::Center,
        OutdoorGameView::HudTextAlignY::Middle);

    const Character *pCaster =
        view.m_pOutdoorPartyRuntime != nullptr
            ? view.m_pOutdoorPartyRuntime->party().member(view.m_utilitySpellOverlay.casterMemberIndex)
            : nullptr;
    const size_t slotCount = utilityOverlayMaxLloydBeaconSlots(pCaster);

    for (size_t index = 0; index < slotCount; ++index)
    {
        const float rowY = layout.contentY + static_cast<float>(index) * (layout.rowHeight + layout.rowGap);
        const bool hovered =
            utilityOverlayPointInsideRect(mouseX, mouseY, layout.contentX, rowY, layout.contentWidth, layout.rowHeight);
        submitSolidQuad(
            layout.contentX,
            rowY,
            layout.contentWidth,
            layout.rowHeight,
            hovered ? hoverRowColor : rowColor);

        const float leftPadding = 12.0f * layout.scale;
        renderLabel(
            "Beacon " + std::to_string(index + 1),
            layout.contentX + leftPadding,
            rowY + 2.0f * layout.scale,
            90.0f * layout.scale,
            layout.rowHeight - 4.0f * layout.scale,
            layout.scale,
            "Lucida",
            mutedColor,
            OutdoorGameView::HudTextAlignX::Left,
            OutdoorGameView::HudTextAlignY::Middle);

        std::string primaryText = "Available";
        std::string secondaryText = recallMode ? "Empty" : "Set beacon here";
        uint32_t primaryColor = textColor;
        uint32_t secondaryColor = mutedColor;

        if (pCaster != nullptr && pCaster->lloydsBeacons[index].has_value())
        {
            const LloydBeacon &beacon = *pCaster->lloydsBeacons[index];
            primaryText = beacon.locationName.empty() ? beacon.mapName : beacon.locationName;
            secondaryText = formatUtilityDurationText(beacon.remainingSeconds) + " remaining";
            primaryColor = textColor;
            secondaryColor = makeAbgrColor(122, 204, 136);
        }
        else if (recallMode)
        {
            primaryColor = mutedColor;
            secondaryColor = mutedColor;
        }

        renderLabel(
            primaryText,
            layout.contentX + 104.0f * layout.scale,
            rowY + 2.0f * layout.scale,
            layout.contentWidth - 116.0f * layout.scale,
            layout.rowHeight * 0.55f,
            layout.scale,
            "Lucida",
            primaryColor,
            OutdoorGameView::HudTextAlignX::Left,
            OutdoorGameView::HudTextAlignY::Middle);
        renderLabel(
            secondaryText,
            layout.contentX + 104.0f * layout.scale,
            rowY + layout.rowHeight * 0.45f,
            layout.contentWidth - 116.0f * layout.scale,
            layout.rowHeight * 0.45f,
            layout.scale,
            "Lucida",
            secondaryColor,
            OutdoorGameView::HudTextAlignX::Left,
            OutdoorGameView::HudTextAlignY::Middle);
    }
}

void GameplayPartyOverlayRenderer::renderSpellbookOverlay(GameplayOverlayContext &context, int width, int height)
{
    if (!context.spellbookReadOnly().active
        || !context.hasHudRenderResources()
        || width <= 0
        || height <= 0)
    {
        return;
    }

    const GameplayOverlayContext::HudLayoutElement *pRootLayout = context.findHudLayoutElement("SpellbookRoot");

    if (pRootLayout == nullptr)
    {
        return;
    }

    const std::optional<GameplayOverlayContext::ResolvedHudLayoutElement> resolvedRoot =
        context.resolveHudLayoutElement("SpellbookRoot", width, height, pRootLayout->width, pRootLayout->height);

    if (!resolvedRoot)
    {
        return;
    }

    const auto loadHudTexture =
        [&context](const std::string &textureName) -> std::optional<GameplayOverlayContext::HudTextureHandle>
        {
            return context.ensureHudTextureLoaded(textureName);
        };

    setupHudProjection(width, height);
    renderViewportParchmentSidePanels(context, width, height);

    float mouseX = 0.0f;
    float mouseY = 0.0f;
    const SDL_MouseButtonFlags mouseButtons = SDL_GetMouseState(&mouseX, &mouseY);
    const bool isLeftMousePressed = (mouseButtons & SDL_BUTTON_LMASK) != 0;

    const auto submitTexturedQuad =
        [&context](const GameplayOverlayContext::HudTextureHandle &texture, float x, float y, float quadWidth, float quadHeight)
        {
            context.submitHudTexturedQuad(texture, x, y, quadWidth, quadHeight);
        };

    const auto renderLayoutPrimaryAsset =
        [&context, width, height, &loadHudTexture, &submitTexturedQuad](const std::string &layoutId)
        {
            const GameplayOverlayContext::HudLayoutElement *pLayout = context.findHudLayoutElement(layoutId);

            if (pLayout == nullptr || pLayout->primaryAsset.empty())
            {
                return;
            }

            const std::optional<GameplayOverlayContext::HudTextureHandle> texture = loadHudTexture(pLayout->primaryAsset);

            if (!texture)
            {
                return;
            }

            const std::optional<GameplayOverlayContext::ResolvedHudLayoutElement> resolved =
                context.resolveHudLayoutElement(
                    layoutId,
                    width,
                    height,
                    pLayout->width > 0.0f ? pLayout->width : static_cast<float>(texture->width),
                    pLayout->height > 0.0f ? pLayout->height : static_cast<float>(texture->height));

            if (!resolved)
            {
                return;
            }

            submitTexturedQuad(*texture, resolved->x, resolved->y, resolved->width, resolved->height);
        };

    const GameplayUiController::SpellbookState &spellbook = context.spellbookReadOnly();
    const SpellbookSchoolUiDefinition *pSchoolDefinition = findSpellbookSchoolUiDefinition(spellbook.school);

    if (pSchoolDefinition == nullptr)
    {
        return;
    }

    renderLayoutPrimaryAsset(pSchoolDefinition->pPageLayoutId);

    bool hasAnySpellbookSchool = false;

    for (const SpellbookSchoolUiDefinition &definition : spellbookSchoolUiDefinitions())
    {
        if (context.activeMemberHasSpellbookSchool(definition.school))
        {
            hasAnySpellbookSchool = true;
            break;
        }
    }

    for (const SpellbookSchoolUiDefinition &definition : spellbookSchoolUiDefinitions())
    {
        if (!context.activeMemberHasSpellbookSchool(definition.school)
            && !(definition.school == GameplayUiController::SpellbookSchool::Fire && !hasAnySpellbookSchool))
        {
            continue;
        }

        const GameplayOverlayContext::HudLayoutElement *pLayout = context.findHudLayoutElement(definition.pButtonLayoutId);

        if (pLayout == nullptr || pLayout->primaryAsset.empty())
        {
            continue;
        }

        const std::optional<GameplayOverlayContext::HudTextureHandle> defaultTexture =
            loadHudTexture(pLayout->primaryAsset);

        if (!defaultTexture)
        {
            continue;
        }

        const std::optional<GameplayOverlayContext::ResolvedHudLayoutElement> resolved =
            context.resolveHudLayoutElement(
                definition.pButtonLayoutId,
                width,
                height,
                pLayout->width > 0.0f ? pLayout->width : static_cast<float>(defaultTexture->width),
                pLayout->height > 0.0f ? pLayout->height : static_cast<float>(defaultTexture->height));

        if (!resolved)
        {
            continue;
        }

        const bool isActive = definition.school == spellbook.school;
        const std::string *pInteractiveAssetName = context.resolveInteractiveAssetName(
            *pLayout,
            *resolved,
            mouseX,
            mouseY,
            isLeftMousePressed);
        const std::string *pSelectedAssetName =
            !pLayout->pressedAsset.empty()
                ? &pLayout->pressedAsset
                : (!pLayout->hoverAsset.empty() ? &pLayout->hoverAsset : &pLayout->primaryAsset);
        const std::string *pAssetName = isActive ? pSelectedAssetName : pInteractiveAssetName;
        const std::optional<GameplayOverlayContext::HudTextureHandle> texture =
            pAssetName != nullptr ? loadHudTexture(*pAssetName) : defaultTexture;

        if (texture)
        {
            submitTexturedQuad(*texture, resolved->x, resolved->y, resolved->width, resolved->height);
        }
    }

    const auto renderInteractiveButton =
        [&context, width, height, mouseX, mouseY, isLeftMousePressed, &loadHudTexture, &submitTexturedQuad](
            const std::string &layoutId)
        {
            const GameplayOverlayContext::HudLayoutElement *pLayout = context.findHudLayoutElement(layoutId);

            if (pLayout == nullptr || pLayout->primaryAsset.empty())
            {
                return;
            }

            const std::optional<GameplayOverlayContext::HudTextureHandle> defaultTexture =
                loadHudTexture(pLayout->primaryAsset);

            if (!defaultTexture)
            {
                return;
            }

            const std::optional<GameplayOverlayContext::ResolvedHudLayoutElement> resolved =
                context.resolveHudLayoutElement(
                    layoutId,
                    width,
                    height,
                    pLayout->width > 0.0f ? pLayout->width : static_cast<float>(defaultTexture->width),
                    pLayout->height > 0.0f ? pLayout->height : static_cast<float>(defaultTexture->height));

            if (!resolved)
            {
                return;
            }

            const std::string *pAssetName = context.resolveInteractiveAssetName(
                *pLayout,
                *resolved,
                mouseX,
                mouseY,
                isLeftMousePressed);
            const std::optional<GameplayOverlayContext::HudTextureHandle> texture =
                pAssetName != nullptr ? loadHudTexture(*pAssetName) : defaultTexture;

            if (texture)
            {
                submitTexturedQuad(*texture, resolved->x, resolved->y, resolved->width, resolved->height);
            }
        };

    renderInteractiveButton("SpellbookCloseButton");
    renderInteractiveButton("SpellbookQuickCastButton");
    renderInteractiveButton("SpellbookAttackCastButton");

    for (uint32_t spellOffset = 0; spellOffset < pSchoolDefinition->spellCount; ++spellOffset)
    {
        const uint32_t spellOrdinal = spellOffset + 1;
        const uint32_t spellId = pSchoolDefinition->firstSpellId + spellOffset;

        if (!context.activeMemberKnowsSpell(spellId))
        {
            continue;
        }

        const std::string layoutId = spellbookSpellLayoutId(spellbook.school, spellOrdinal);
        const GameplayOverlayContext::HudLayoutElement *pLayout = context.findHudLayoutElement(layoutId);

        if (pLayout == nullptr)
        {
            continue;
        }

        const std::optional<GameplayOverlayContext::HudTextureHandle> defaultTexture =
            loadHudTexture(pLayout->primaryAsset);

        if (!defaultTexture)
        {
            continue;
        }

        const std::optional<GameplayOverlayContext::ResolvedHudLayoutElement> resolved =
            context.resolveHudLayoutElement(
                layoutId,
                width,
                height,
                pLayout->width > 0.0f ? pLayout->width : static_cast<float>(defaultTexture->width),
                pLayout->height > 0.0f ? pLayout->height : static_cast<float>(defaultTexture->height));

        if (!resolved)
        {
            continue;
        }

        const bool isSelected = spellbook.selectedSpellId == spellId;
        const std::string *pInteractiveAssetName = context.resolveInteractiveAssetName(
            *pLayout,
            *resolved,
            mouseX,
            mouseY,
            isLeftMousePressed);
        const std::string *pSelectedAssetName =
            !pLayout->pressedAsset.empty()
                ? &pLayout->pressedAsset
                : (!pLayout->hoverAsset.empty() ? &pLayout->hoverAsset : &pLayout->primaryAsset);
        const std::string *pAssetName = isSelected ? pSelectedAssetName : pInteractiveAssetName;
        const std::optional<GameplayOverlayContext::HudTextureHandle> texture =
            pAssetName != nullptr ? loadHudTexture(*pAssetName) : defaultTexture;

        if (texture)
        {
            submitTexturedQuad(*texture, resolved->x, resolved->y, resolved->width, resolved->height);
        }
    }
}

void GameplayPartyOverlayRenderer::renderHeldInventoryItem(GameplayOverlayContext &context, int width, int height)
{
    const GameplayUiController::HeldInventoryItemState &heldItem = context.heldInventoryItem();

    if (!heldItem.active
        || context.itemTable() == nullptr
        || !context.hasHudRenderResources()
        || width <= 0
        || height <= 0)
    {
        return;
    }

    const ItemDefinition *pItemDefinition = context.itemTable()->get(heldItem.item.objectDescriptionId);

    if (pItemDefinition == nullptr || pItemDefinition->iconName.empty())
    {
        return;
    }

    const std::optional<GameplayOverlayContext::HudTextureHandle> texture =
        context.ensureHudTextureLoaded(pItemDefinition->iconName);

    if (!texture)
    {
        return;
    }

    setupHudProjection(width, height);

    const UiViewportRect uiViewport = computeUiViewportRect(width, height);
    const float scale = std::min(uiViewport.width / HudReferenceWidth, uiViewport.height / HudReferenceHeight);
    float mouseX = 0.0f;
    float mouseY = 0.0f;
    SDL_GetMouseState(&mouseX, &mouseY);
    const float itemX = std::round(mouseX - heldItem.grabOffsetX);
    const float itemY = std::round(mouseY - heldItem.grabOffsetY);
    const float itemWidth = static_cast<float>(texture->width) * scale;
    const float itemHeight = static_cast<float>(texture->height) * scale;

    context.submitHudTexturedQuad(*texture, itemX, itemY, itemWidth, itemHeight);

    const bgfx::TextureHandle tintedTextureHandle = context.ensureHudTextureColor(
        *texture,
        itemTintColorAbgr(&heldItem.item, pItemDefinition, ItemTintContext::Held));

    if (bgfx::isValid(tintedTextureHandle) && tintedTextureHandle.idx != texture->textureHandle.idx)
    {
        GameplayOverlayContext::HudTextureHandle tintedTexture = *texture;
        tintedTexture.textureHandle = tintedTextureHandle;
        context.submitHudTexturedQuad(tintedTexture, itemX, itemY, itemWidth, itemHeight);
    }
}

void GameplayPartyOverlayRenderer::renderItemInspectOverlay(GameplayOverlayContext &context, int width, int height)
{
    const GameplayUiController::ItemInspectOverlayState &overlay = context.itemInspectOverlayReadOnly();

    if (!overlay.active
        || context.itemTable() == nullptr
        || !context.hasHudRenderResources()
        || width <= 0
        || height <= 0)
    {
        return;
    }

    const ItemDefinition *pItemDefinition = context.itemTable()->get(overlay.objectDescriptionId);

    if (pItemDefinition == nullptr)
    {
        return;
    }

    const GameplayOverlayContext::HudLayoutElement *pRootLayout = context.findHudLayoutElement("ItemInspectRoot");

    if (pRootLayout == nullptr)
    {
        return;
    }

    const UiViewportRect uiViewport = computeUiViewportRect(width, height);
    const float baseScale = std::min(uiViewport.width / HudReferenceWidth, uiViewport.height / HudReferenceHeight);
    const float popupScale = std::clamp(baseScale, pRootLayout->minScale, pRootLayout->maxScale);
    const InventoryItem *pItemState = overlay.hasItemState ? &overlay.itemState : nullptr;
    InventoryItem defaultItemState = {};
    defaultItemState.objectDescriptionId = overlay.objectDescriptionId;
    defaultItemState.identified = true;
    const InventoryItem &resolvedItemState = pItemState != nullptr ? *pItemState : defaultItemState;
    const bool showBrokenOnly = pItemState != nullptr && pItemState->broken;
    const bool showUnidentifiedOnly =
        !showBrokenOnly
        && pItemState != nullptr
        && !pItemState->identified
        && ItemRuntime::requiresIdentification(*pItemDefinition);
    const std::string itemName = ItemRuntime::displayName(
        resolvedItemState,
        *pItemDefinition,
        context.standardItemEnchantTable(),
        context.specialItemEnchantTable());
    const std::string itemType =
        showBrokenOnly || showUnidentifiedOnly ? std::string {} : resolveItemInspectTypeText(pItemState, *pItemDefinition);
    const std::string itemDetail =
        showBrokenOnly || showUnidentifiedOnly ? std::string {} : resolveItemInspectDetailText(pItemState, *pItemDefinition);
    const std::string enchantDescription = ItemEnchantRuntime::buildEnchantDescription(
        resolvedItemState,
        context.standardItemEnchantTable(),
        context.specialItemEnchantTable());
    const std::string itemSpecialDetail =
        showBrokenOnly || showUnidentifiedOnly || enchantDescription.empty() ? std::string {} : "Special: " + enchantDescription;
    const std::string itemDescription =
        showBrokenOnly ? "Broken item" : (showUnidentifiedOnly ? "Not identified" : pItemDefinition->notes);
    const int resolvedItemValue =
        overlay.hasValueOverride
            ? overlay.valueOverride
            : PriceCalculator::itemValue(
                resolvedItemState,
                *pItemDefinition,
                context.standardItemEnchantTable(),
                context.specialItemEnchantTable());
    const std::string itemValue = std::to_string(std::max(0, resolvedItemValue));
    const std::optional<GameplayOverlayContext::HudTextureHandle> itemTexture =
        !pItemDefinition->iconName.empty() ? context.ensureHudTextureLoaded(pItemDefinition->iconName) : std::nullopt;
    const std::optional<GameplayOverlayContext::HudFontHandle> bodyFont = context.findHudFont("SMALLNUM");
    const GameplayOverlayContext::HudFontHandle *pBodyFont = bodyFont ? &*bodyFont : nullptr;
    const float bodyLineHeight =
        pBodyFont != nullptr ? static_cast<float>(pBodyFont->fontHeight) * popupScale : 12.0f * popupScale;

    const GameplayOverlayContext::HudLayoutElement *pPreviewLayout = context.findHudLayoutElement("ItemInspectPreviewImage");
    const GameplayOverlayContext::HudLayoutElement *pTypeLayout = context.findHudLayoutElement("ItemInspectType");
    const GameplayOverlayContext::HudLayoutElement *pDetailRowLayout = context.findHudLayoutElement("ItemInspectDetailRow");
    const GameplayOverlayContext::HudLayoutElement *pDetailValueLayout = context.findHudLayoutElement("ItemInspectDetailValue");
    const GameplayOverlayContext::HudLayoutElement *pDescriptionLayout = context.findHudLayoutElement("ItemInspectDescription");
    const GameplayOverlayContext::HudLayoutElement *pValueLayout = context.findHudLayoutElement("ItemInspectValue");

    if (pPreviewLayout == nullptr
        || pTypeLayout == nullptr
        || pDetailRowLayout == nullptr
        || pDetailValueLayout == nullptr
        || pDescriptionLayout == nullptr
        || pValueLayout == nullptr)
    {
        return;
    }

    const float previewImageWidth =
        itemTexture ? static_cast<float>(itemTexture->width) * popupScale : pPreviewLayout->width * popupScale;
    const float previewImageHeight =
        itemTexture ? static_cast<float>(itemTexture->height) * popupScale : pPreviewLayout->height * popupScale;
    const GameplayOverlayContext::ResolvedHudLayoutElement provisionalRoot = {
        0.0f,
        0.0f,
        pRootLayout->width * popupScale,
        pRootLayout->height * popupScale,
        popupScale
    };
    const GameplayOverlayContext::ResolvedHudLayoutElement previewRectForSizing =
        GameplayHudCommon::resolveAttachedHudLayoutRect(
            pPreviewLayout->attachTo,
            provisionalRoot,
            previewImageWidth,
            previewImageHeight,
            pPreviewLayout->gapX,
            pPreviewLayout->gapY,
            popupScale);
    const GameplayOverlayContext::ResolvedHudLayoutElement typeRectForSizing =
        GameplayHudCommon::resolveAttachedHudLayoutRect(
            pTypeLayout->attachTo,
            provisionalRoot,
            pTypeLayout->width * popupScale,
            pTypeLayout->height * popupScale,
            pTypeLayout->gapX,
            pTypeLayout->gapY,
            popupScale);
    const GameplayOverlayContext::ResolvedHudLayoutElement descriptionRectForSizing =
        GameplayHudCommon::resolveAttachedHudLayoutRect(
            pDescriptionLayout->attachTo,
            provisionalRoot,
            pDescriptionLayout->width * popupScale,
            pDescriptionLayout->height * popupScale,
            pDescriptionLayout->gapX,
            pDescriptionLayout->gapY,
            popupScale);
    const float descriptionWidthScaled =
        std::max(0.0f, descriptionRectForSizing.width - std::abs(pDescriptionLayout->textPadX * popupScale) * 2.0f);
    const float descriptionWidth = std::max(0.0f, descriptionWidthScaled / std::max(1.0f, popupScale));
    const std::vector<std::string> descriptionLines =
        pBodyFont != nullptr
            ? context.wrapHudTextToWidth(*pBodyFont, itemDescription, descriptionWidth)
            : std::vector<std::string>{itemDescription};
    const bool showDetail = !itemDetail.empty();
    const bool showSpecialDetail = !itemSpecialDetail.empty();
    const float descriptionHeight =
        itemDescription.empty() || descriptionLines.empty() ? 0.0f : bodyLineHeight * static_cast<float>(descriptionLines.size());
    const float detailRowHeight = pDetailRowLayout->height * popupScale;
    const std::optional<GameplayOverlayContext::HudFontHandle> detailFont =
        context.findHudFont(pDetailValueLayout->fontName);
    const GameplayOverlayContext::HudFontHandle *pDetailFont = detailFont ? &*detailFont : nullptr;
    float detailFontScale = popupScale * std::max(0.1f, pDetailValueLayout->textScale);

    if (detailFontScale >= 1.0f)
    {
        detailFontScale = snappedHudFontScale(detailFontScale);
    }
    else
    {
        detailFontScale = std::max(0.5f, detailFontScale);
    }

    const float detailLineHeight =
        pDetailFont != nullptr ? static_cast<float>(pDetailFont->fontHeight) * detailFontScale : detailRowHeight;
    const float detailTextWidthScaled = std::max(
        0.0f,
        pDetailValueLayout->width * popupScale - std::abs(pDetailValueLayout->textPadX * popupScale) * 2.0f);
    const float detailTextWidth = std::max(0.0f, detailTextWidthScaled / std::max(0.1f, detailFontScale));
    const std::vector<std::string> specialDetailLines =
        showSpecialDetail && pDetailFont != nullptr
            ? context.wrapHudTextToWidth(*pDetailFont, itemSpecialDetail, detailTextWidth)
            : std::vector<std::string>{itemSpecialDetail};
    const float specialDetailHeight = showSpecialDetail
        ? std::max(detailRowHeight, detailLineHeight * static_cast<float>(std::max<size_t>(1, specialDetailLines.size())))
        : 0.0f;
    const int detailRowCount = (showDetail ? 1 : 0) + (showSpecialDetail ? 1 : 0);
    static constexpr float ItemInspectTypeToDetailGap = 3.0f;
    static constexpr float ItemInspectDetailToDescriptionGap = 8.0f;
    static constexpr float ItemInspectDescriptionToValueGap = 8.0f;
    static constexpr float ItemInspectBottomPadding = 8.0f;
    const float detailSectionHeight = detailRowCount > 0
        ? ItemInspectTypeToDetailGap * popupScale
            + (showDetail ? detailRowHeight : 0.0f)
            + (showSpecialDetail ? specialDetailHeight : 0.0f)
            + ItemInspectTypeToDetailGap * popupScale * static_cast<float>(detailRowCount - 1)
        : 0.0f;
    const float descriptionSectionHeight =
        descriptionHeight > 0.0f ? ItemInspectDetailToDescriptionGap * popupScale + descriptionHeight : 0.0f;
    const float previewContentHeight = previewImageHeight + 20.0f * popupScale;
    const float textContentHeight =
        typeRectForSizing.y
        + typeRectForSizing.height
        + detailSectionHeight
        + descriptionSectionHeight
        + ItemInspectDescriptionToValueGap * popupScale
        + pValueLayout->height * popupScale
        + ItemInspectBottomPadding * popupScale;
    const float rootWidth = provisionalRoot.width;
    const float rootHeight = std::max(previewContentHeight, textContentHeight);
    const float popupGap = 12.0f * popupScale;
    float rootX = overlay.sourceX + overlay.sourceWidth + popupGap;

    if (rootX + rootWidth > uiViewport.x + uiViewport.width)
    {
        rootX = overlay.sourceX - rootWidth - popupGap;
    }

    rootX = std::clamp(rootX, uiViewport.x, uiViewport.x + uiViewport.width - rootWidth);
    float rootY = overlay.sourceY + (overlay.sourceHeight - rootHeight) * 0.5f;
    rootY = std::clamp(rootY, uiViewport.y, uiViewport.y + uiViewport.height - rootHeight);
    const GameplayOverlayContext::ResolvedHudLayoutElement rootRect = {
        std::round(rootX),
        std::round(rootY),
        std::round(rootWidth),
        std::round(rootHeight),
        popupScale
    };

    setupHudProjection(width, height);

    const std::optional<GameplayOverlayContext::HudTextureHandle> backgroundTexture =
        context.ensureHudTextureLoaded(pRootLayout->primaryAsset);

    if (backgroundTexture)
    {
        context.submitHudTexturedQuad(*backgroundTexture, rootRect.x, rootRect.y, rootRect.width, rootRect.height);
    }

    std::function<std::optional<GameplayOverlayContext::ResolvedHudLayoutElement>(const std::string &)> resolveItemInspectLayout =
        [&context,
         &rootRect,
         &resolveItemInspectLayout,
         previewImageWidth,
         previewImageHeight,
         popupScale](
            const std::string &layoutId) -> std::optional<GameplayOverlayContext::ResolvedHudLayoutElement>
        {
            const GameplayOverlayContext::HudLayoutElement *pLayout = context.findHudLayoutElement(layoutId);

            if (pLayout == nullptr)
            {
                return std::nullopt;
            }

            const std::string normalizedLayoutId = toLowerCopy(layoutId);
            std::optional<GameplayOverlayContext::HudTextureHandle> baseTexture;

            if ((pLayout->width <= 0.0f || pLayout->height <= 0.0f) && !pLayout->primaryAsset.empty())
            {
                baseTexture = context.ensureHudTextureLoaded(pLayout->primaryAsset);
            }

            float resolvedWidth =
                normalizedLayoutId == "iteminspectpreviewimage"
                    ? previewImageWidth
                    : (pLayout->width > 0.0f
                        ? pLayout->width * popupScale
                        : (baseTexture ? static_cast<float>(baseTexture->width) * popupScale : 0.0f));
            float resolvedHeight =
                normalizedLayoutId == "iteminspectpreviewimage"
                    ? previewImageHeight
                    : (pLayout->height > 0.0f
                        ? pLayout->height * popupScale
                        : (baseTexture ? static_cast<float>(baseTexture->height) * popupScale : 0.0f));

            if (normalizedLayoutId == "iteminspectcorner_topedge"
                || normalizedLayoutId == "iteminspectcorner_bottomedge")
            {
                resolvedWidth = rootRect.width;
            }

            if (normalizedLayoutId == "iteminspectcorner_leftedge"
                || normalizedLayoutId == "iteminspectcorner_rightedge")
            {
                resolvedHeight = rootRect.height;
            }

            if (pLayout->parentId.empty() || toLowerCopy(pLayout->parentId) == "iteminspectroot")
            {
                return GameplayHudCommon::resolveAttachedHudLayoutRect(
                    pLayout->attachTo,
                    rootRect,
                    resolvedWidth,
                    resolvedHeight,
                    pLayout->gapX,
                    pLayout->gapY,
                    popupScale);
            }

            const std::optional<GameplayOverlayContext::ResolvedHudLayoutElement> parentRect =
                resolveItemInspectLayout(pLayout->parentId);

            if (!parentRect)
            {
                return std::nullopt;
            }

            return GameplayHudCommon::resolveAttachedHudLayoutRect(
                pLayout->attachTo,
                *parentRect,
                resolvedWidth,
                resolvedHeight,
                pLayout->gapX,
                pLayout->gapY,
                popupScale);
        };

    const auto isItemInspectRootDescendant =
        [&context](const GameplayOverlayContext::HudLayoutElement &layout) -> bool
        {
            std::string currentLayoutId = layout.id;

            while (!currentLayoutId.empty())
            {
                if (toLowerCopy(currentLayoutId) == "iteminspectroot")
                {
                    return true;
                }

                const GameplayOverlayContext::HudLayoutElement *pCurrentLayout =
                    context.findHudLayoutElement(currentLayoutId);

                if (pCurrentLayout == nullptr || pCurrentLayout->parentId.empty())
                {
                    break;
                }

                currentLayoutId = pCurrentLayout->parentId;
            }

            return false;
        };

    const std::vector<std::string> orderedItemInspectLayoutIds = context.sortedHudLayoutIdsForScreen("ItemInspect");

    for (const std::string &layoutId : orderedItemInspectLayoutIds)
    {
        const GameplayOverlayContext::HudLayoutElement *pLayout = context.findHudLayoutElement(layoutId);

        if (pLayout == nullptr
            || !pLayout->visible
            || pLayout->primaryAsset.empty()
            || toLowerCopy(pLayout->id) == "iteminspectroot"
            || toLowerCopy(pLayout->id) == "iteminspectpreviewimage"
            || !isItemInspectRootDescendant(*pLayout))
        {
            continue;
        }

        const std::optional<GameplayOverlayContext::HudTextureHandle> texture =
            context.ensureHudTextureLoaded(pLayout->primaryAsset);
        const std::optional<GameplayOverlayContext::ResolvedHudLayoutElement> resolved =
            resolveItemInspectLayout(layoutId);

        if (!texture || !resolved || resolved->width <= 0.0f || resolved->height <= 0.0f)
        {
            continue;
        }

        context.submitHudTexturedQuad(*texture, resolved->x, resolved->y, resolved->width, resolved->height);
    }

    const auto renderSingleLine =
        [&context, &resolveItemInspectLayout](const char *pLayoutId, const std::string &text)
        {
            const GameplayOverlayContext::HudLayoutElement *pLayout = context.findHudLayoutElement(pLayoutId);
            const std::optional<GameplayOverlayContext::ResolvedHudLayoutElement> resolved =
                resolveItemInspectLayout(pLayoutId);

            if (pLayout == nullptr || !resolved)
            {
                return;
            }

            context.renderLayoutLabel(*pLayout, *resolved, text);
        };

    renderSingleLine("ItemInspectName", itemName);
    renderSingleLine("ItemInspectType", "Type: " + itemType);

    const std::optional<GameplayOverlayContext::ResolvedHudLayoutElement> previewRect =
        resolveItemInspectLayout("ItemInspectPreviewImage");

    if (previewRect && itemTexture && itemTexture->width > 0 && itemTexture->height > 0)
    {
        context.submitHudTexturedQuad(*itemTexture, previewRect->x, previewRect->y, previewRect->width, previewRect->height);
    }

    const std::optional<GameplayOverlayContext::ResolvedHudLayoutElement> typeRect =
        resolveItemInspectLayout("ItemInspectType");
    const std::optional<GameplayOverlayContext::ResolvedHudLayoutElement> detailRowBaseRect =
        resolveItemInspectLayout("ItemInspectDetailRow");
    const std::optional<GameplayOverlayContext::ResolvedHudLayoutElement> descriptionBaseRect =
        resolveItemInspectLayout("ItemInspectDescription");
    const std::optional<GameplayOverlayContext::ResolvedHudLayoutElement> valueBaseRect =
        resolveItemInspectLayout("ItemInspectValue");

    if (showDetail && typeRect && detailRowBaseRect)
    {
        GameplayOverlayContext::ResolvedHudLayoutElement detailRowRect = *detailRowBaseRect;
        detailRowRect.y = std::round(typeRect->y + typeRect->height + ItemInspectTypeToDetailGap * popupScale);
        const GameplayOverlayContext::ResolvedHudLayoutElement detailValueRect =
            GameplayHudCommon::resolveAttachedHudLayoutRect(
                pDetailValueLayout->attachTo,
                detailRowRect,
                pDetailValueLayout->width * popupScale,
                pDetailValueLayout->height * popupScale,
                pDetailValueLayout->gapX,
                pDetailValueLayout->gapY,
                popupScale);
        context.renderLayoutLabel(*pDetailValueLayout, detailValueRect, itemDetail);
    }

    if (showSpecialDetail && typeRect && detailRowBaseRect)
    {
        GameplayOverlayContext::ResolvedHudLayoutElement specialRowRect = *detailRowBaseRect;
        specialRowRect.y = std::round(
            typeRect->y
            + typeRect->height
            + ItemInspectTypeToDetailGap * popupScale
            + (showDetail ? detailRowHeight + ItemInspectTypeToDetailGap * popupScale : 0.0f));
        specialRowRect.height = std::round(specialDetailHeight);
        const GameplayOverlayContext::ResolvedHudLayoutElement specialValueRect =
            GameplayHudCommon::resolveAttachedHudLayoutRect(
                pDetailValueLayout->attachTo,
                specialRowRect,
                pDetailValueLayout->width * popupScale,
                specialRowRect.height,
                pDetailValueLayout->gapX,
                pDetailValueLayout->gapY,
                popupScale);

        if (pDetailFont != nullptr && !specialDetailLines.empty())
        {
            bgfx::TextureHandle coloredMainTextureHandle =
                context.ensureHudFontMainTextureColor(*pDetailFont, pDetailValueLayout->textColorAbgr);

            if (!bgfx::isValid(coloredMainTextureHandle))
            {
                coloredMainTextureHandle = pDetailFont->mainTextureHandle;
            }

            const float totalSpecialTextHeight =
                detailLineHeight * static_cast<float>(std::max<size_t>(1, specialDetailLines.size()));
            float textX = std::round(specialValueRect.x + pDetailValueLayout->textPadX * popupScale);
            float textY = specialValueRect.y + pDetailValueLayout->textPadY * popupScale;

            switch (pDetailValueLayout->textAlignY)
            {
                case UiLayoutManager::TextAlignY::Top:
                    break;

                case UiLayoutManager::TextAlignY::Middle:
                    textY =
                        specialValueRect.y
                        + (specialValueRect.height - totalSpecialTextHeight) * 0.5f
                        + pDetailValueLayout->textPadY * popupScale;
                    break;

                case UiLayoutManager::TextAlignY::Bottom:
                    textY =
                        specialValueRect.y
                        + specialValueRect.height
                        - totalSpecialTextHeight
                        + pDetailValueLayout->textPadY * popupScale;
                    break;
            }

            textY = std::round(textY);

            for (const std::string &wrappedLine : specialDetailLines)
            {
                context.renderHudFontLayer(*pDetailFont, pDetailFont->shadowTextureHandle, wrappedLine, textX, textY, detailFontScale);
                context.renderHudFontLayer(*pDetailFont, coloredMainTextureHandle, wrappedLine, textX, textY, detailFontScale);
                textY += detailLineHeight;
            }
        }
        else
        {
            context.renderLayoutLabel(*pDetailValueLayout, specialValueRect, itemSpecialDetail);
        }
    }

    const float dynamicDescriptionY = typeRect
        ? std::round(
            typeRect->y
            + typeRect->height
            + detailSectionHeight
            + (descriptionHeight > 0.0f ? ItemInspectDetailToDescriptionGap * popupScale : 0.0f))
        : 0.0f;
    const std::optional<GameplayOverlayContext::ResolvedHudLayoutElement> resolvedDescription =
        descriptionBaseRect
            ? std::optional<GameplayOverlayContext::ResolvedHudLayoutElement>(GameplayOverlayContext::ResolvedHudLayoutElement{
                descriptionBaseRect->x,
                dynamicDescriptionY,
                descriptionBaseRect->width,
                descriptionBaseRect->height,
                descriptionBaseRect->scale})
            : std::nullopt;

    if (!itemDescription.empty() && pBodyFont != nullptr && resolvedDescription)
    {
        bgfx::TextureHandle coloredMainTextureHandle =
            context.ensureHudFontMainTextureColor(*pBodyFont, pDescriptionLayout->textColorAbgr);

        if (!bgfx::isValid(coloredMainTextureHandle))
        {
            coloredMainTextureHandle = pBodyFont->mainTextureHandle;
        }

        float textX = std::round(resolvedDescription->x + pDescriptionLayout->textPadX * popupScale);
        float textY = std::round(resolvedDescription->y + pDescriptionLayout->textPadY * popupScale);

        for (const std::string &line : descriptionLines)
        {
            context.renderHudFontLayer(*pBodyFont, pBodyFont->shadowTextureHandle, line, textX, textY, popupScale);
            context.renderHudFontLayer(*pBodyFont, coloredMainTextureHandle, line, textX, textY, popupScale);
            textY += bodyLineHeight;
        }
    }

    if (valueBaseRect)
    {
        GameplayOverlayContext::ResolvedHudLayoutElement valueRect = *valueBaseRect;
        const float minimumValueY = dynamicDescriptionY + descriptionHeight + ItemInspectDescriptionToValueGap * popupScale;
        const float anchoredValueY =
            rootRect.y + rootRect.height - ItemInspectBottomPadding * popupScale - valueRect.height;
        valueRect.y = std::round(std::max(minimumValueY, anchoredValueY));
        context.renderLayoutLabel(*pValueLayout, valueRect, "Value: " + itemValue);
    }
}

void GameplayPartyOverlayRenderer::renderCharacterInspectOverlay(const OutdoorGameView &view, int width, int height)
{
    if (!view.m_characterInspectOverlay.active
        || !bgfx::isValid(view.m_texturedTerrainProgramHandle)
        || !bgfx::isValid(view.m_terrainTextureSamplerHandle)
        || width <= 0
        || height <= 0)
    {
        return;
    }

    const OutdoorGameView::HudLayoutElement *pRootLayout = HudUiService::findHudLayoutElement(view, "CharacterInspectRoot");
    const OutdoorGameView::HudLayoutElement *pTitleLayout = HudUiService::findHudLayoutElement(view, "CharacterInspectTitle");
    const OutdoorGameView::HudLayoutElement *pBodyLayout = HudUiService::findHudLayoutElement(view, "CharacterInspectBody");
    const OutdoorGameView::HudLayoutElement *pExpertLayout = HudUiService::findHudLayoutElement(view, "CharacterInspectExpert");
    const OutdoorGameView::HudLayoutElement *pMasterLayout = HudUiService::findHudLayoutElement(view, "CharacterInspectMaster");
    const OutdoorGameView::HudLayoutElement *pGrandmasterLayout =
        HudUiService::findHudLayoutElement(view, "CharacterInspectGrandmaster");

    if (pRootLayout == nullptr
        || pTitleLayout == nullptr
        || pBodyLayout == nullptr
        || pExpertLayout == nullptr
        || pMasterLayout == nullptr
        || pGrandmasterLayout == nullptr)
    {
        return;
    }

    const UiViewportRect uiViewport = computeUiViewportRect(width, height);
    const float baseScale = std::min(uiViewport.width / HudReferenceWidth, uiViewport.height / HudReferenceHeight);
    const float popupScale = std::clamp(baseScale, pRootLayout->minScale, pRootLayout->maxScale);
    const OutdoorGameView::ResolvedHudLayoutElement provisionalRoot = {
        0.0f,
        0.0f,
        pRootLayout->width * popupScale,
        pRootLayout->height * popupScale,
        popupScale
    };
    const OutdoorGameView::HudFontHandle *pBodyFont = HudUiService::findHudFont(view, "SMALLNUM");
    const float bodyLineHeight =
        pBodyFont != nullptr ? static_cast<float>(pBodyFont->fontHeight) * popupScale : 12.0f * popupScale;
    const OutdoorGameView::ResolvedHudLayoutElement bodyRectForSizing = OutdoorGameView::resolveAttachedHudLayoutRect(
        pBodyLayout->attachTo,
        provisionalRoot,
        pBodyLayout->width * popupScale,
        pBodyLayout->height * popupScale,
        pBodyLayout->gapX,
        pBodyLayout->gapY,
        popupScale);
    const float bodyWidthScaled =
        std::max(0.0f, bodyRectForSizing.width - std::abs(pBodyLayout->textPadX * popupScale) * 2.0f);
    const float bodyWidth = std::max(0.0f, bodyWidthScaled / std::max(1.0f, popupScale));
    const std::vector<std::string> bodyLines =
        pBodyFont != nullptr
            ? HudUiService::wrapHudTextToWidth(view, *pBodyFont, view.m_characterInspectOverlay.body, bodyWidth)
            : std::vector<std::string>{view.m_characterInspectOverlay.body};
    const float bodyHeight = bodyLines.empty() ? bodyLineHeight : bodyLineHeight * static_cast<float>(bodyLines.size());
    const bool showExpert =
        view.m_characterInspectOverlay.expert.visible && !view.m_characterInspectOverlay.expert.text.empty();
    const bool showMaster =
        view.m_characterInspectOverlay.master.visible && !view.m_characterInspectOverlay.master.text.empty();
    const bool showGrandmaster =
        view.m_characterInspectOverlay.grandmaster.visible && !view.m_characterInspectOverlay.grandmaster.text.empty();
    static constexpr float CharacterInspectBodyToRowsGap = 10.0f;
    static constexpr float CharacterInspectRowGap = 2.0f;
    static constexpr float CharacterInspectBottomPadding = 15.0f;

    const auto resolveWrappedMasteryLines =
        [&view, popupScale](const OutdoorGameView::HudLayoutElement &layout, const std::string &text) -> std::vector<std::string>
        {
            const OutdoorGameView::HudFontHandle *pFont = HudUiService::findHudFont(view, layout.fontName);

            if (pFont == nullptr)
            {
                return {text};
            }

            const float maxWidthScaled =
                std::max(0.0f, layout.width * popupScale - std::abs(layout.textPadX * popupScale) * 2.0f);
            const float maxWidth = std::max(0.0f, maxWidthScaled / std::max(1.0f, popupScale));
            return HudUiService::wrapHudTextToWidth(view, *pFont, text, maxWidth);
        };

    const auto masteryRowHeight =
        [&view, popupScale](const OutdoorGameView::HudLayoutElement &layout, const std::vector<std::string> &lines) -> float
        {
            const OutdoorGameView::HudFontHandle *pFont = HudUiService::findHudFont(view, layout.fontName);
            const float lineHeight =
                pFont != nullptr ? static_cast<float>(pFont->fontHeight) * popupScale : layout.height * popupScale;
            return std::max(lineHeight, lineHeight * static_cast<float>(std::max<size_t>(1, lines.size())));
        };

    const std::vector<std::string> expertLines =
        showExpert
            ? resolveWrappedMasteryLines(*pExpertLayout, view.m_characterInspectOverlay.expert.text)
            : std::vector<std::string>{};
    const std::vector<std::string> masterLines =
        showMaster
            ? resolveWrappedMasteryLines(*pMasterLayout, view.m_characterInspectOverlay.master.text)
            : std::vector<std::string>{};
    const std::vector<std::string> grandmasterLines =
        showGrandmaster
            ? resolveWrappedMasteryLines(*pGrandmasterLayout, view.m_characterInspectOverlay.grandmaster.text)
            : std::vector<std::string>{};
    float masteryHeight = 0.0f;
    bool hasAnyMasteryRows = false;

    for (const auto &[showRow, pLayout, pLines] : {
             std::tuple<bool, const OutdoorGameView::HudLayoutElement *, const std::vector<std::string> *>{
                 showExpert, pExpertLayout, &expertLines},
             std::tuple<bool, const OutdoorGameView::HudLayoutElement *, const std::vector<std::string> *>{
                 showMaster, pMasterLayout, &masterLines},
             std::tuple<bool, const OutdoorGameView::HudLayoutElement *, const std::vector<std::string> *>{
                 showGrandmaster, pGrandmasterLayout, &grandmasterLines}})
    {
        if (!showRow)
        {
            continue;
        }

        if (hasAnyMasteryRows)
        {
            masteryHeight += CharacterInspectRowGap * popupScale;
        }

        masteryHeight += masteryRowHeight(*pLayout, *pLines);
        hasAnyMasteryRows = true;
    }

    const float rootWidth = provisionalRoot.width;
    const float rootHeight =
        bodyRectForSizing.y
        + bodyHeight
        + (hasAnyMasteryRows ? CharacterInspectBodyToRowsGap * popupScale + masteryHeight : 0.0f)
        + CharacterInspectBottomPadding * popupScale;
    const float popupGap = 12.0f * popupScale;
    float rootX = view.m_characterInspectOverlay.sourceX + view.m_characterInspectOverlay.sourceWidth + popupGap;

    if (rootX + rootWidth > uiViewport.x + uiViewport.width)
    {
        rootX = view.m_characterInspectOverlay.sourceX - rootWidth - popupGap;
    }

    rootX = std::clamp(rootX, uiViewport.x, uiViewport.x + uiViewport.width - rootWidth);
    float rootY =
        view.m_characterInspectOverlay.sourceY + (view.m_characterInspectOverlay.sourceHeight - rootHeight) * 0.5f;
    rootY = std::clamp(rootY, uiViewport.y, uiViewport.y + uiViewport.height - rootHeight);
    const OutdoorGameView::ResolvedHudLayoutElement rootRect = {
        std::round(rootX),
        std::round(rootY),
        std::round(rootWidth),
        std::round(rootHeight),
        popupScale
    };

    setupHudProjection(width, height);

    const OutdoorGameView::HudTextureHandle *pBackgroundTexture =
        HudUiService::ensureHudTextureLoaded(const_cast<OutdoorGameView &>(view), pRootLayout->primaryAsset);

    if (pBackgroundTexture != nullptr)
    {
        view.submitHudTexturedQuad(*pBackgroundTexture, rootRect.x, rootRect.y, rootRect.width, rootRect.height);
    }

    std::function<std::optional<OutdoorGameView::ResolvedHudLayoutElement>(const std::string &)> resolveLayout;
    resolveLayout =
        [&view, &rootRect, popupScale, &resolveLayout](
            const std::string &layoutId) -> std::optional<OutdoorGameView::ResolvedHudLayoutElement>
        {
            const OutdoorGameView::HudLayoutElement *pLayout = HudUiService::findHudLayoutElement(view, layoutId);

            if (pLayout == nullptr)
            {
                return std::nullopt;
            }

            float resolvedWidth = pLayout->width * popupScale;
            float resolvedHeight = pLayout->height * popupScale;
            const std::string normalizedLayoutId = toLowerCopy(layoutId);

            if ((pLayout->width <= 0.0f || pLayout->height <= 0.0f) && !pLayout->primaryAsset.empty())
            {
                const OutdoorGameView::HudTextureHandle *pTexture =
                    HudUiService::ensureHudTextureLoaded(const_cast<OutdoorGameView &>(view), pLayout->primaryAsset);

                if (pTexture != nullptr)
                {
                    if (pLayout->width <= 0.0f)
                    {
                        resolvedWidth = static_cast<float>(pTexture->width) * popupScale;
                    }

                    if (pLayout->height <= 0.0f)
                    {
                        resolvedHeight = static_cast<float>(pTexture->height) * popupScale;
                    }
                }
            }

            if (normalizedLayoutId == "characterinspectcorner_topedge"
                || normalizedLayoutId == "characterinspectcorner_bottomedge")
            {
                resolvedWidth = rootRect.width;
            }

            if (normalizedLayoutId == "characterinspectcorner_leftedge"
                || normalizedLayoutId == "characterinspectcorner_rightedge")
            {
                resolvedHeight = rootRect.height;
            }

            OutdoorGameView::ResolvedHudLayoutElement parent = rootRect;

            if (!pLayout->parentId.empty() && toLowerCopy(pLayout->parentId) != "characterinspectroot")
            {
                const std::optional<OutdoorGameView::ResolvedHudLayoutElement> resolvedParent =
                    resolveLayout(pLayout->parentId);

                if (resolvedParent)
                {
                    parent = *resolvedParent;
                }
            }

            return OutdoorGameView::resolveAttachedHudLayoutRect(
                pLayout->attachTo,
                parent,
                resolvedWidth,
                resolvedHeight,
                pLayout->gapX,
                pLayout->gapY,
                popupScale);
        };

    const std::vector<std::string> orderedLayoutIds = HudUiService::sortedHudLayoutIdsForScreen(view, "CharacterInspect");

    for (const std::string &layoutId : orderedLayoutIds)
    {
        const OutdoorGameView::HudLayoutElement *pLayout = HudUiService::findHudLayoutElement(view, layoutId);

        if (pLayout == nullptr
            || !pLayout->visible
            || pLayout->primaryAsset.empty()
            || toLowerCopy(pLayout->id) == "characterinspectroot")
        {
            continue;
        }

        const OutdoorGameView::HudTextureHandle *pTexture =
            HudUiService::ensureHudTextureLoaded(const_cast<OutdoorGameView &>(view), pLayout->primaryAsset);
        const std::optional<OutdoorGameView::ResolvedHudLayoutElement> resolved = resolveLayout(layoutId);

        if (pTexture == nullptr || !resolved)
        {
            continue;
        }

        view.submitHudTexturedQuad(*pTexture, resolved->x, resolved->y, resolved->width, resolved->height);
    }

    const auto renderSingleLine =
        [&view, &resolveLayout](const char *pLayoutId, const std::string &text)
        {
            const OutdoorGameView::HudLayoutElement *pLayout = HudUiService::findHudLayoutElement(view, pLayoutId);
            const std::optional<OutdoorGameView::ResolvedHudLayoutElement> resolved = resolveLayout(pLayoutId);

            if (pLayout == nullptr || !resolved || text.empty())
            {
                return;
            }

            HudUiService::renderLayoutLabel(view, *pLayout, *resolved, text);
        };

    renderSingleLine("CharacterInspectTitle", view.m_characterInspectOverlay.title);

    const std::optional<OutdoorGameView::ResolvedHudLayoutElement> bodyBaseRect = resolveLayout("CharacterInspectBody");

    if (bodyBaseRect && pBodyFont != nullptr)
    {
        bgfx::TextureHandle coloredMainTextureHandle =
            HudUiService::ensureHudFontMainTextureColor(view, *pBodyFont, pBodyLayout->textColorAbgr);

        if (!bgfx::isValid(coloredMainTextureHandle))
        {
            coloredMainTextureHandle = pBodyFont->mainTextureHandle;
        }

        float textX = std::round(bodyBaseRect->x + pBodyLayout->textPadX * popupScale);
        float textY = std::round(bodyBaseRect->y + pBodyLayout->textPadY * popupScale);

        for (const std::string &line : bodyLines)
        {
            HudUiService::renderHudFontLayer(view, *pBodyFont, pBodyFont->shadowTextureHandle, line, textX, textY, popupScale);
            HudUiService::renderHudFontLayer(view, *pBodyFont, coloredMainTextureHandle, line, textX, textY, popupScale);
            textY += bodyLineHeight;
        }

        const auto masteryColorForAvailability =
            [](int availability) -> uint32_t
            {
                switch (availability)
                {
                    case 0:
                        return 0xffffffffu;

                    case 1:
                        return packHudColorAbgr(255, 255, 0);

                    case 2:
                        return packHudColorAbgr(255, 0, 0);

                    default:
                        return 0xffffffffu;
                }
            };

        float nextRowY = std::round(bodyBaseRect->y + bodyHeight + CharacterInspectBodyToRowsGap * popupScale);
        const auto renderMasteryRow =
            [&view, popupScale, &masteryColorForAvailability](
                const OutdoorGameView::HudLayoutElement &baseLayout,
                const OutdoorGameView::ResolvedHudLayoutElement &baseResolved,
                float rowY,
                const OutdoorGameView::CharacterInspectMasteryLine &line,
                const std::vector<std::string> &wrappedLines) -> float
            {
                if (!line.visible || line.text.empty())
                {
                    return rowY;
                }

                const OutdoorGameView::HudFontHandle *pFont = HudUiService::findHudFont(view, baseLayout.fontName);

                if (pFont == nullptr)
                {
                    return rowY;
                }

                bgfx::TextureHandle coloredMainTextureHandle =
                    HudUiService::ensureHudFontMainTextureColor(view, 
                        *pFont,
                        masteryColorForAvailability(line.availability));

                if (!bgfx::isValid(coloredMainTextureHandle))
                {
                    coloredMainTextureHandle = pFont->mainTextureHandle;
                }

                const float lineHeight = static_cast<float>(pFont->fontHeight) * popupScale;
                float textX = std::round(baseResolved.x + baseLayout.textPadX * popupScale);
                float textY = std::round(rowY + baseLayout.textPadY * popupScale);

                for (const std::string &wrappedLine : wrappedLines)
                {
                    HudUiService::renderHudFontLayer(view, *pFont, pFont->shadowTextureHandle, wrappedLine, textX, textY, popupScale);
                    HudUiService::renderHudFontLayer(view, *pFont, coloredMainTextureHandle, wrappedLine, textX, textY, popupScale);
                    textY += lineHeight;
                }

                return rowY + lineHeight * static_cast<float>(std::max<size_t>(1, wrappedLines.size()));
            };

        const std::optional<OutdoorGameView::ResolvedHudLayoutElement> expertRect = resolveLayout("CharacterInspectExpert");
        const std::optional<OutdoorGameView::ResolvedHudLayoutElement> masterRect = resolveLayout("CharacterInspectMaster");
        const std::optional<OutdoorGameView::ResolvedHudLayoutElement> grandmasterRect =
            resolveLayout("CharacterInspectGrandmaster");

        if (expertRect)
        {
            nextRowY = renderMasteryRow(
                *pExpertLayout,
                *expertRect,
                nextRowY,
                view.m_characterInspectOverlay.expert,
                expertLines);

            if (showExpert)
            {
                nextRowY += CharacterInspectRowGap * popupScale;
            }
        }

        if (masterRect)
        {
            nextRowY = renderMasteryRow(
                *pMasterLayout,
                *masterRect,
                nextRowY,
                view.m_characterInspectOverlay.master,
                masterLines);

            if (showMaster)
            {
                nextRowY += CharacterInspectRowGap * popupScale;
            }
        }

        if (grandmasterRect)
        {
            renderMasteryRow(
                *pGrandmasterLayout,
                *grandmasterRect,
                nextRowY,
                view.m_characterInspectOverlay.grandmaster,
                grandmasterLines);
        }
    }
}

void GameplayPartyOverlayRenderer::renderSpellInspectOverlay(const OutdoorGameView &view, int width, int height)
{
    if (!view.m_spellInspectOverlay.active
        || !bgfx::isValid(view.m_texturedTerrainProgramHandle)
        || !bgfx::isValid(view.m_terrainTextureSamplerHandle)
        || width <= 0
        || height <= 0)
    {
        return;
    }

    const OutdoorGameView::HudLayoutElement *pRootLayout = HudUiService::findHudLayoutElement(view, "SpellInspectRoot");
    const OutdoorGameView::HudLayoutElement *pTitleLayout = HudUiService::findHudLayoutElement(view, "SpellInspectTitle");
    const OutdoorGameView::HudLayoutElement *pBodyLayout = HudUiService::findHudLayoutElement(view, "SpellInspectBody");
    const OutdoorGameView::HudLayoutElement *pNormalLayout = HudUiService::findHudLayoutElement(view, "SpellInspectNormal");
    const OutdoorGameView::HudLayoutElement *pExpertLayout = HudUiService::findHudLayoutElement(view, "SpellInspectExpert");
    const OutdoorGameView::HudLayoutElement *pMasterLayout = HudUiService::findHudLayoutElement(view, "SpellInspectMaster");
    const OutdoorGameView::HudLayoutElement *pGrandmasterLayout = HudUiService::findHudLayoutElement(view, "SpellInspectGrandmaster");

    if (pRootLayout == nullptr
        || pTitleLayout == nullptr
        || pBodyLayout == nullptr
        || pNormalLayout == nullptr
        || pExpertLayout == nullptr
        || pMasterLayout == nullptr
        || pGrandmasterLayout == nullptr)
    {
        return;
    }

    const UiViewportRect uiViewport = computeUiViewportRect(width, height);
    const float baseScale = std::min(uiViewport.width / HudReferenceWidth, uiViewport.height / HudReferenceHeight);
    const float popupScale = std::clamp(baseScale, pRootLayout->minScale, pRootLayout->maxScale);
    const OutdoorGameView::ResolvedHudLayoutElement provisionalRoot = {
        0.0f,
        0.0f,
        pRootLayout->width * popupScale,
        pRootLayout->height * popupScale,
        popupScale
    };
    const OutdoorGameView::HudFontHandle *pBodyFont = HudUiService::findHudFont(view, "SMALLNUM");
    const float bodyLineHeight =
        pBodyFont != nullptr ? static_cast<float>(pBodyFont->fontHeight) * popupScale : 12.0f * popupScale;
    const OutdoorGameView::ResolvedHudLayoutElement bodyRectForSizing = OutdoorGameView::resolveAttachedHudLayoutRect(
        pBodyLayout->attachTo,
        provisionalRoot,
        pBodyLayout->width * popupScale,
        pBodyLayout->height * popupScale,
        pBodyLayout->gapX,
        pBodyLayout->gapY,
        popupScale);
    const float bodyWidthScaled =
        std::max(0.0f, bodyRectForSizing.width - std::abs(pBodyLayout->textPadX * popupScale) * 2.0f);
    const float bodyWidth = std::max(0.0f, bodyWidthScaled / std::max(1.0f, popupScale));
    const std::vector<std::string> bodyLines =
        pBodyFont != nullptr
            ? HudUiService::wrapHudTextToWidth(view, *pBodyFont, view.m_spellInspectOverlay.body, bodyWidth)
            : std::vector<std::string>{view.m_spellInspectOverlay.body};
    const float bodyHeight = bodyLines.empty() ? bodyLineHeight : bodyLineHeight * static_cast<float>(bodyLines.size());
    static constexpr float SpellInspectBodyToRowsGap = 10.0f;
    static constexpr float SpellInspectRowGap = 2.0f;
    static constexpr float SpellInspectBottomPadding = 15.0f;

    const auto resolveWrappedLines =
        [&view, popupScale](const OutdoorGameView::HudLayoutElement &layout, const std::string &text) -> std::vector<std::string>
        {
            const OutdoorGameView::HudFontHandle *pFont = HudUiService::findHudFont(view, layout.fontName);

            if (pFont == nullptr)
            {
                return {text};
            }

            const float maxWidthScaled =
                std::max(0.0f, layout.width * popupScale - std::abs(layout.textPadX * popupScale) * 2.0f);
            const float maxWidth = std::max(0.0f, maxWidthScaled / std::max(1.0f, popupScale));
            return HudUiService::wrapHudTextToWidth(view, *pFont, text, maxWidth);
        };

    const auto rowHeight =
        [&view, popupScale](const OutdoorGameView::HudLayoutElement &layout, const std::vector<std::string> &lines) -> float
        {
            const OutdoorGameView::HudFontHandle *pFont = HudUiService::findHudFont(view, layout.fontName);
            const float lineHeight =
                pFont != nullptr ? static_cast<float>(pFont->fontHeight) * popupScale : layout.height * popupScale;
            return std::max(lineHeight, lineHeight * static_cast<float>(std::max<size_t>(1, lines.size())));
        };

    const bool showNormal = !view.m_spellInspectOverlay.normal.empty();
    const bool showExpert = !view.m_spellInspectOverlay.expert.empty();
    const bool showMaster = !view.m_spellInspectOverlay.master.empty();
    const bool showGrandmaster = !view.m_spellInspectOverlay.grandmaster.empty();
    const std::vector<std::string> normalLines =
        showNormal ? resolveWrappedLines(*pNormalLayout, view.m_spellInspectOverlay.normal) : std::vector<std::string>{};
    const std::vector<std::string> expertLines =
        showExpert ? resolveWrappedLines(*pExpertLayout, view.m_spellInspectOverlay.expert) : std::vector<std::string>{};
    const std::vector<std::string> masterLines =
        showMaster ? resolveWrappedLines(*pMasterLayout, view.m_spellInspectOverlay.master) : std::vector<std::string>{};
    const std::vector<std::string> grandmasterLines =
        showGrandmaster
            ? resolveWrappedLines(*pGrandmasterLayout, view.m_spellInspectOverlay.grandmaster)
            : std::vector<std::string>{};
    float rowsHeight = 0.0f;
    bool hasRows = false;

    for (const auto &[showRow, pLayout, pLines] : {
             std::tuple<bool, const OutdoorGameView::HudLayoutElement *, const std::vector<std::string> *>{
                 showNormal, pNormalLayout, &normalLines},
             std::tuple<bool, const OutdoorGameView::HudLayoutElement *, const std::vector<std::string> *>{
                 showExpert, pExpertLayout, &expertLines},
             std::tuple<bool, const OutdoorGameView::HudLayoutElement *, const std::vector<std::string> *>{
                 showMaster, pMasterLayout, &masterLines},
             std::tuple<bool, const OutdoorGameView::HudLayoutElement *, const std::vector<std::string> *>{
                 showGrandmaster, pGrandmasterLayout, &grandmasterLines}})
    {
        if (!showRow)
        {
            continue;
        }

        if (hasRows)
        {
            rowsHeight += SpellInspectRowGap * popupScale;
        }

        rowsHeight += rowHeight(*pLayout, *pLines);
        hasRows = true;
    }

    const float rootWidth = provisionalRoot.width;
    const float rootHeight =
        bodyRectForSizing.y
        + bodyHeight
        + (hasRows ? SpellInspectBodyToRowsGap * popupScale + rowsHeight : 0.0f)
        + SpellInspectBottomPadding * popupScale;
    const float popupGap = 12.0f * popupScale;
    float rootX = view.m_spellInspectOverlay.sourceX + view.m_spellInspectOverlay.sourceWidth + popupGap;

    if (rootX + rootWidth > uiViewport.x + uiViewport.width)
    {
        rootX = view.m_spellInspectOverlay.sourceX - rootWidth - popupGap;
    }

    rootX = std::clamp(rootX, uiViewport.x, uiViewport.x + uiViewport.width - rootWidth);
    float rootY = view.m_spellInspectOverlay.sourceY + (view.m_spellInspectOverlay.sourceHeight - rootHeight) * 0.5f;
    rootY = std::clamp(rootY, uiViewport.y, uiViewport.y + uiViewport.height - rootHeight);
    const OutdoorGameView::ResolvedHudLayoutElement rootRect = {
        std::round(rootX),
        std::round(rootY),
        std::round(rootWidth),
        std::round(rootHeight),
        popupScale
    };

    setupHudProjection(width, height);

    const OutdoorGameView::HudTextureHandle *pBackgroundTexture =
        HudUiService::ensureHudTextureLoaded(const_cast<OutdoorGameView &>(view), pRootLayout->primaryAsset);

    if (pBackgroundTexture != nullptr)
    {
        view.submitHudTexturedQuad(*pBackgroundTexture, rootRect.x, rootRect.y, rootRect.width, rootRect.height);
    }

    std::function<std::optional<OutdoorGameView::ResolvedHudLayoutElement>(const std::string &)> resolveLayout;
    resolveLayout =
        [&view, &rootRect, popupScale, &resolveLayout](
            const std::string &layoutId) -> std::optional<OutdoorGameView::ResolvedHudLayoutElement>
        {
            const OutdoorGameView::HudLayoutElement *pLayout = HudUiService::findHudLayoutElement(view, layoutId);

            if (pLayout == nullptr)
            {
                return std::nullopt;
            }

            float resolvedWidth = pLayout->width * popupScale;
            float resolvedHeight = pLayout->height * popupScale;
            const std::string normalizedLayoutId = toLowerCopy(layoutId);

            if ((pLayout->width <= 0.0f || pLayout->height <= 0.0f) && !pLayout->primaryAsset.empty())
            {
                const OutdoorGameView::HudTextureHandle *pTexture =
                    HudUiService::ensureHudTextureLoaded(const_cast<OutdoorGameView &>(view), pLayout->primaryAsset);

                if (pTexture != nullptr)
                {
                    if (pLayout->width <= 0.0f)
                    {
                        resolvedWidth = static_cast<float>(pTexture->width) * popupScale;
                    }

                    if (pLayout->height <= 0.0f)
                    {
                        resolvedHeight = static_cast<float>(pTexture->height) * popupScale;
                    }
                }
            }

            if (normalizedLayoutId == "spellinspectcorner_topedge"
                || normalizedLayoutId == "spellinspectcorner_bottomedge")
            {
                resolvedWidth = rootRect.width;
            }

            if (normalizedLayoutId == "spellinspectcorner_leftedge"
                || normalizedLayoutId == "spellinspectcorner_rightedge")
            {
                resolvedHeight = rootRect.height;
            }

            OutdoorGameView::ResolvedHudLayoutElement parent = rootRect;

            if (!pLayout->parentId.empty() && toLowerCopy(pLayout->parentId) != "spellinspectroot")
            {
                const std::optional<OutdoorGameView::ResolvedHudLayoutElement> resolvedParent =
                    resolveLayout(pLayout->parentId);

                if (resolvedParent)
                {
                    parent = *resolvedParent;
                }
            }

            return OutdoorGameView::resolveAttachedHudLayoutRect(
                pLayout->attachTo,
                parent,
                resolvedWidth,
                resolvedHeight,
                pLayout->gapX,
                pLayout->gapY,
                popupScale);
        };

    const std::vector<std::string> orderedLayoutIds = HudUiService::sortedHudLayoutIdsForScreen(view, "SpellInspect");

    for (const std::string &layoutId : orderedLayoutIds)
    {
        const OutdoorGameView::HudLayoutElement *pLayout = HudUiService::findHudLayoutElement(view, layoutId);

        if (pLayout == nullptr
            || !pLayout->visible
            || pLayout->primaryAsset.empty()
            || toLowerCopy(pLayout->id) == "spellinspectroot")
        {
            continue;
        }

        const OutdoorGameView::HudTextureHandle *pTexture =
            HudUiService::ensureHudTextureLoaded(const_cast<OutdoorGameView &>(view), pLayout->primaryAsset);
        const std::optional<OutdoorGameView::ResolvedHudLayoutElement> resolved = resolveLayout(layoutId);

        if (pTexture == nullptr || !resolved)
        {
            continue;
        }

        view.submitHudTexturedQuad(*pTexture, resolved->x, resolved->y, resolved->width, resolved->height);
    }

    const auto renderSingleLine =
        [&view, &resolveLayout](const char *pLayoutId, const std::string &text)
        {
            const OutdoorGameView::HudLayoutElement *pLayout = HudUiService::findHudLayoutElement(view, pLayoutId);
            const std::optional<OutdoorGameView::ResolvedHudLayoutElement> resolved = resolveLayout(pLayoutId);

            if (pLayout == nullptr || !resolved || text.empty())
            {
                return;
            }

            HudUiService::renderLayoutLabel(view, *pLayout, *resolved, text);
        };

    renderSingleLine("SpellInspectTitle", view.m_spellInspectOverlay.title);

    if (pBodyFont != nullptr)
    {
        const std::optional<OutdoorGameView::ResolvedHudLayoutElement> bodyBaseRect = resolveLayout("SpellInspectBody");

        if (bodyBaseRect)
        {
            bgfx::TextureHandle coloredMainTextureHandle =
                HudUiService::ensureHudFontMainTextureColor(view, *pBodyFont, pBodyLayout->textColorAbgr);

            if (!bgfx::isValid(coloredMainTextureHandle))
            {
                coloredMainTextureHandle = pBodyFont->mainTextureHandle;
            }

            float textX = std::round(bodyBaseRect->x + pBodyLayout->textPadX * popupScale);
            float textY = std::round(bodyBaseRect->y + pBodyLayout->textPadY * popupScale);

            for (const std::string &line : bodyLines)
            {
                HudUiService::renderHudFontLayer(view, *pBodyFont, pBodyFont->shadowTextureHandle, line, textX, textY, popupScale);
                HudUiService::renderHudFontLayer(view, *pBodyFont, coloredMainTextureHandle, line, textX, textY, popupScale);
                textY += bodyLineHeight;
            }

            const auto renderWrappedRow =
                [&view, popupScale](
                    const OutdoorGameView::HudLayoutElement &layout,
                    const OutdoorGameView::ResolvedHudLayoutElement &baseResolved,
                    float rowY,
                    const std::vector<std::string> &wrappedLines) -> float
                {
                    if (wrappedLines.empty())
                    {
                        return rowY;
                    }

                    const OutdoorGameView::HudFontHandle *pFont = HudUiService::findHudFont(view, layout.fontName);

                    if (pFont == nullptr)
                    {
                        return rowY;
                    }

                    bgfx::TextureHandle coloredMainTextureHandle =
                        HudUiService::ensureHudFontMainTextureColor(view, *pFont, layout.textColorAbgr);

                    if (!bgfx::isValid(coloredMainTextureHandle))
                    {
                        coloredMainTextureHandle = pFont->mainTextureHandle;
                    }

                    const float lineHeight = static_cast<float>(pFont->fontHeight) * popupScale;
                    float textX = std::round(baseResolved.x + layout.textPadX * popupScale);
                    float textY = std::round(rowY + layout.textPadY * popupScale);

                    for (const std::string &wrappedLine : wrappedLines)
                    {
                        HudUiService::renderHudFontLayer(view, *pFont, pFont->shadowTextureHandle, wrappedLine, textX, textY, popupScale);
                        HudUiService::renderHudFontLayer(view, *pFont, coloredMainTextureHandle, wrappedLine, textX, textY, popupScale);
                        textY += lineHeight;
                    }

                    return rowY + lineHeight * static_cast<float>(std::max<size_t>(1, wrappedLines.size()));
                };

            float nextRowY = std::round(bodyBaseRect->y + bodyHeight + SpellInspectBodyToRowsGap * popupScale);
            const std::optional<OutdoorGameView::ResolvedHudLayoutElement> normalRect = resolveLayout("SpellInspectNormal");
            const std::optional<OutdoorGameView::ResolvedHudLayoutElement> expertRect = resolveLayout("SpellInspectExpert");
            const std::optional<OutdoorGameView::ResolvedHudLayoutElement> masterRect = resolveLayout("SpellInspectMaster");
            const std::optional<OutdoorGameView::ResolvedHudLayoutElement> grandmasterRect =
                resolveLayout("SpellInspectGrandmaster");

            if (normalRect)
            {
                nextRowY = renderWrappedRow(*pNormalLayout, *normalRect, nextRowY, normalLines);

                if (showNormal)
                {
                    nextRowY += SpellInspectRowGap * popupScale;
                }
            }

            if (expertRect)
            {
                nextRowY = renderWrappedRow(*pExpertLayout, *expertRect, nextRowY, expertLines);

                if (showExpert)
                {
                    nextRowY += SpellInspectRowGap * popupScale;
                }
            }

            if (masterRect)
            {
                nextRowY = renderWrappedRow(*pMasterLayout, *masterRect, nextRowY, masterLines);

                if (showMaster)
                {
                    nextRowY += SpellInspectRowGap * popupScale;
                }
            }

            if (grandmasterRect)
            {
                renderWrappedRow(*pGrandmasterLayout, *grandmasterRect, nextRowY, grandmasterLines);
            }
        }
    }
}

void GameplayPartyOverlayRenderer::renderReadableScrollOverlay(const OutdoorGameView &view, int width, int height)
{
    if (!view.m_readableScrollOverlay.active
        || !bgfx::isValid(view.m_texturedTerrainProgramHandle)
        || !bgfx::isValid(view.m_terrainTextureSamplerHandle)
        || width <= 0
        || height <= 0)
    {
        return;
    }

    const OutdoorGameView::HudLayoutElement *pRootLayout = HudUiService::findHudLayoutElement(view, "SpellInspectRoot");
    const OutdoorGameView::HudLayoutElement *pTitleLayout = HudUiService::findHudLayoutElement(view, "SpellInspectTitle");
    const OutdoorGameView::HudLayoutElement *pBodyLayout = HudUiService::findHudLayoutElement(view, "SpellInspectBody");

    if (pRootLayout == nullptr || pTitleLayout == nullptr || pBodyLayout == nullptr)
    {
        return;
    }

    const UiViewportRect uiViewport = computeUiViewportRect(width, height);
    const float baseScale = std::min(uiViewport.width / HudReferenceWidth, uiViewport.height / HudReferenceHeight);
    const float popupScale = std::clamp(baseScale, pRootLayout->minScale, pRootLayout->maxScale);
    const OutdoorGameView::ResolvedHudLayoutElement provisionalRoot = {
        0.0f,
        0.0f,
        pRootLayout->width * popupScale,
        pRootLayout->height * popupScale,
        popupScale
    };
    const OutdoorGameView::HudFontHandle *pBodyFont = HudUiService::findHudFont(view, "SMALLNUM");
    const float bodyLineHeight =
        pBodyFont != nullptr ? static_cast<float>(pBodyFont->fontHeight) * popupScale : 12.0f * popupScale;
    const OutdoorGameView::ResolvedHudLayoutElement bodyRectForSizing = OutdoorGameView::resolveAttachedHudLayoutRect(
        pBodyLayout->attachTo,
        provisionalRoot,
        pBodyLayout->width * popupScale,
        pBodyLayout->height * popupScale,
        pBodyLayout->gapX,
        pBodyLayout->gapY,
        popupScale);
    const float bodyWidthScaled =
        std::max(0.0f, bodyRectForSizing.width - std::abs(pBodyLayout->textPadX * popupScale) * 2.0f);
    const float bodyWidth = std::max(0.0f, bodyWidthScaled / std::max(1.0f, popupScale));
    const std::vector<std::string> bodyLines =
        pBodyFont != nullptr
            ? HudUiService::wrapHudTextToWidth(view, *pBodyFont, view.m_readableScrollOverlay.body, bodyWidth)
            : std::vector<std::string>{view.m_readableScrollOverlay.body};
    const float bodyHeight = bodyLines.empty() ? bodyLineHeight : bodyLineHeight * static_cast<float>(bodyLines.size());
    static constexpr float ReadableScrollBottomPadding = 15.0f;
    const float rootWidth = provisionalRoot.width;
    const float rootHeight = std::max(
        provisionalRoot.height,
        bodyRectForSizing.y + bodyHeight + ReadableScrollBottomPadding * popupScale);
    const float rootX = std::round(uiViewport.x + (uiViewport.width - rootWidth) * 0.5f);
    const float rootY = std::round(uiViewport.y + (uiViewport.height - rootHeight) * 0.5f);
    const OutdoorGameView::ResolvedHudLayoutElement rootRect = {rootX, rootY, rootWidth, rootHeight, popupScale};

    setupHudProjection(width, height);

    const OutdoorGameView::HudTextureHandle *pBackgroundTexture =
        HudUiService::ensureHudTextureLoaded(const_cast<OutdoorGameView &>(view), pRootLayout->primaryAsset);

    if (pBackgroundTexture != nullptr)
    {
        view.submitHudTexturedQuad(*pBackgroundTexture, rootRect.x, rootRect.y, rootRect.width, rootRect.height);
    }

    std::function<std::optional<OutdoorGameView::ResolvedHudLayoutElement>(const std::string &)> resolveLayout;
    resolveLayout =
        [&view, &rootRect, popupScale, &resolveLayout](
            const std::string &layoutId) -> std::optional<OutdoorGameView::ResolvedHudLayoutElement>
        {
            const OutdoorGameView::HudLayoutElement *pLayout = HudUiService::findHudLayoutElement(view, layoutId);

            if (pLayout == nullptr)
            {
                return std::nullopt;
            }

            float resolvedWidth = pLayout->width * popupScale;
            float resolvedHeight = pLayout->height * popupScale;
            const std::string normalizedLayoutId = toLowerCopy(layoutId);

            if ((pLayout->width <= 0.0f || pLayout->height <= 0.0f) && !pLayout->primaryAsset.empty())
            {
                const OutdoorGameView::HudTextureHandle *pTexture =
                    HudUiService::ensureHudTextureLoaded(const_cast<OutdoorGameView &>(view), pLayout->primaryAsset);

                if (pTexture != nullptr)
                {
                    if (pLayout->width <= 0.0f)
                    {
                        resolvedWidth = static_cast<float>(pTexture->width) * popupScale;
                    }

                    if (pLayout->height <= 0.0f)
                    {
                        resolvedHeight = static_cast<float>(pTexture->height) * popupScale;
                    }
                }
            }

            if (normalizedLayoutId == "spellinspectcorner_topedge"
                || normalizedLayoutId == "spellinspectcorner_bottomedge")
            {
                resolvedWidth = rootRect.width;
            }

            if (normalizedLayoutId == "spellinspectcorner_leftedge"
                || normalizedLayoutId == "spellinspectcorner_rightedge")
            {
                resolvedHeight = rootRect.height;
            }

            OutdoorGameView::ResolvedHudLayoutElement parent = rootRect;

            if (!pLayout->parentId.empty() && toLowerCopy(pLayout->parentId) != "spellinspectroot")
            {
                const std::optional<OutdoorGameView::ResolvedHudLayoutElement> resolvedParent = resolveLayout(pLayout->parentId);

                if (resolvedParent)
                {
                    parent = *resolvedParent;
                }
            }

            return OutdoorGameView::resolveAttachedHudLayoutRect(
                pLayout->attachTo,
                parent,
                resolvedWidth,
                resolvedHeight,
                pLayout->gapX,
                pLayout->gapY,
                popupScale);
        };

    const std::vector<std::string> orderedLayoutIds = HudUiService::sortedHudLayoutIdsForScreen(view, "SpellInspect");

    for (const std::string &layoutId : orderedLayoutIds)
    {
        const OutdoorGameView::HudLayoutElement *pLayout = HudUiService::findHudLayoutElement(view, layoutId);

        if (pLayout == nullptr
            || !pLayout->visible
            || pLayout->primaryAsset.empty()
            || toLowerCopy(pLayout->id) == "spellinspectroot")
        {
            continue;
        }

        const OutdoorGameView::HudTextureHandle *pTexture =
            HudUiService::ensureHudTextureLoaded(const_cast<OutdoorGameView &>(view), pLayout->primaryAsset);
        const std::optional<OutdoorGameView::ResolvedHudLayoutElement> resolved = resolveLayout(layoutId);

        if (pTexture == nullptr || !resolved)
        {
            continue;
        }

        view.submitHudTexturedQuad(*pTexture, resolved->x, resolved->y, resolved->width, resolved->height);
    }

    const std::optional<OutdoorGameView::ResolvedHudLayoutElement> titleRect = resolveLayout("SpellInspectTitle");

    if (titleRect)
    {
        HudUiService::renderLayoutLabel(view, *pTitleLayout, *titleRect, view.m_readableScrollOverlay.title);
    }

    if (pBodyFont == nullptr)
    {
        return;
    }

    const std::optional<OutdoorGameView::ResolvedHudLayoutElement> bodyBaseRect = resolveLayout("SpellInspectBody");

    if (!bodyBaseRect)
    {
        return;
    }

    bgfx::TextureHandle coloredMainTextureHandle =
        HudUiService::ensureHudFontMainTextureColor(view, *pBodyFont, pBodyLayout->textColorAbgr);

    if (!bgfx::isValid(coloredMainTextureHandle))
    {
        coloredMainTextureHandle = pBodyFont->mainTextureHandle;
    }

    float textX = std::round(bodyBaseRect->x + pBodyLayout->textPadX * popupScale);
    float textY = std::round(bodyBaseRect->y + pBodyLayout->textPadY * popupScale);

    for (const std::string &line : bodyLines)
    {
        HudUiService::renderHudFontLayer(view, *pBodyFont, pBodyFont->shadowTextureHandle, line, textX, textY, popupScale);
        HudUiService::renderHudFontLayer(view, *pBodyFont, coloredMainTextureHandle, line, textX, textY, popupScale);
        textY += bodyLineHeight;
    }
}

void GameplayPartyOverlayRenderer::renderBuffInspectOverlay(const OutdoorGameView &view, int width, int height)
{
    if (!view.m_buffInspectOverlay.active
        || !bgfx::isValid(view.m_texturedTerrainProgramHandle)
        || !bgfx::isValid(view.m_terrainTextureSamplerHandle)
        || width <= 0
        || height <= 0)
    {
        return;
    }

    const OutdoorGameView::HudLayoutElement *pRootLayout = HudUiService::findHudLayoutElement(view, "BuffInspectRoot");
    const OutdoorGameView::HudLayoutElement *pTitleLayout = HudUiService::findHudLayoutElement(view, "BuffInspectTitle");
    const OutdoorGameView::HudLayoutElement *pBodyLayout = HudUiService::findHudLayoutElement(view, "BuffInspectBody");

    if (pRootLayout == nullptr || pTitleLayout == nullptr || pBodyLayout == nullptr)
    {
        return;
    }

    const UiViewportRect uiViewport = computeUiViewportRect(width, height);
    const float baseScale = std::min(uiViewport.width / HudReferenceWidth, uiViewport.height / HudReferenceHeight);
    const float popupScale = std::clamp(baseScale, pRootLayout->minScale, pRootLayout->maxScale);
    const OutdoorGameView::ResolvedHudLayoutElement provisionalRoot = {
        0.0f,
        0.0f,
        pRootLayout->width * popupScale,
        pRootLayout->height * popupScale,
        popupScale
    };
    const OutdoorGameView::HudFontHandle *pBodyFont = HudUiService::findHudFont(view, "SMALLNUM");
    const float bodyLineHeight =
        pBodyFont != nullptr ? static_cast<float>(pBodyFont->fontHeight) * popupScale : 12.0f * popupScale;
    const OutdoorGameView::ResolvedHudLayoutElement bodyRectForSizing = OutdoorGameView::resolveAttachedHudLayoutRect(
        pBodyLayout->attachTo,
        provisionalRoot,
        pBodyLayout->width * popupScale,
        pBodyLayout->height * popupScale,
        pBodyLayout->gapX,
        pBodyLayout->gapY,
        popupScale);
    const float bodyWidthScaled =
        std::max(0.0f, bodyRectForSizing.width - std::abs(pBodyLayout->textPadX * popupScale) * 2.0f);
    const float bodyWidth = std::max(0.0f, bodyWidthScaled / std::max(1.0f, popupScale));
    const std::vector<std::string> bodyLines =
        pBodyFont != nullptr
            ? HudUiService::wrapHudTextToWidth(view, *pBodyFont, view.m_buffInspectOverlay.body, bodyWidth)
            : std::vector<std::string>{view.m_buffInspectOverlay.body};
    const float bodyHeight = bodyLines.empty() ? bodyLineHeight : bodyLineHeight * static_cast<float>(bodyLines.size());
    static constexpr float BuffInspectBottomPadding = 14.0f;
    const float rootWidth = provisionalRoot.width;
    const float rootHeight = std::max(
        provisionalRoot.height,
        bodyRectForSizing.y + bodyHeight + BuffInspectBottomPadding * popupScale);
    const float popupGap = 10.0f * popupScale;
    float rootX = view.m_buffInspectOverlay.sourceX + view.m_buffInspectOverlay.sourceWidth + popupGap;

    if (rootX + rootWidth > uiViewport.x + uiViewport.width)
    {
        rootX = view.m_buffInspectOverlay.sourceX - rootWidth - popupGap;
    }

    rootX = std::clamp(rootX, uiViewport.x, uiViewport.x + uiViewport.width - rootWidth);
    float rootY = view.m_buffInspectOverlay.sourceY + (view.m_buffInspectOverlay.sourceHeight - rootHeight) * 0.5f;
    rootY = std::clamp(rootY, uiViewport.y, uiViewport.y + uiViewport.height - rootHeight);
    const OutdoorGameView::ResolvedHudLayoutElement rootRect = {
        std::round(rootX),
        std::round(rootY),
        std::round(rootWidth),
        std::round(rootHeight),
        popupScale
    };

    setupHudProjection(width, height);

    const OutdoorGameView::HudTextureHandle *pBackgroundTexture =
        HudUiService::ensureHudTextureLoaded(const_cast<OutdoorGameView &>(view), pRootLayout->primaryAsset);

    if (pBackgroundTexture != nullptr)
    {
        view.submitHudTexturedQuad(*pBackgroundTexture, rootRect.x, rootRect.y, rootRect.width, rootRect.height);
    }

    std::function<std::optional<OutdoorGameView::ResolvedHudLayoutElement>(const std::string &)> resolveLayout;
    resolveLayout =
        [&view, &rootRect, popupScale, &resolveLayout](
            const std::string &layoutId) -> std::optional<OutdoorGameView::ResolvedHudLayoutElement>
        {
            const OutdoorGameView::HudLayoutElement *pLayout = HudUiService::findHudLayoutElement(view, layoutId);

            if (pLayout == nullptr)
            {
                return std::nullopt;
            }

            float resolvedWidth = pLayout->width * popupScale;
            float resolvedHeight = pLayout->height * popupScale;
            const std::string normalizedLayoutId = toLowerCopy(layoutId);

            if (normalizedLayoutId == "buffinspectcorner_topedge"
                || normalizedLayoutId == "buffinspectcorner_bottomedge")
            {
                resolvedWidth = rootRect.width;
            }

            if (normalizedLayoutId == "buffinspectcorner_leftedge"
                || normalizedLayoutId == "buffinspectcorner_rightedge")
            {
                resolvedHeight = rootRect.height;
            }

            OutdoorGameView::ResolvedHudLayoutElement parent = rootRect;

            if (!pLayout->parentId.empty() && toLowerCopy(pLayout->parentId) != "buffinspectroot")
            {
                const std::optional<OutdoorGameView::ResolvedHudLayoutElement> resolvedParent = resolveLayout(pLayout->parentId);

                if (resolvedParent)
                {
                    parent = *resolvedParent;
                }
            }

            return OutdoorGameView::resolveAttachedHudLayoutRect(
                pLayout->attachTo,
                parent,
                resolvedWidth,
                resolvedHeight,
                pLayout->gapX,
                pLayout->gapY,
                popupScale);
        };

    const std::vector<std::string> orderedLayoutIds = HudUiService::sortedHudLayoutIdsForScreen(view, "BuffInspect");

    for (const std::string &layoutId : orderedLayoutIds)
    {
        const OutdoorGameView::HudLayoutElement *pLayout = HudUiService::findHudLayoutElement(view, layoutId);

        if (pLayout == nullptr
            || !pLayout->visible
            || pLayout->primaryAsset.empty()
            || toLowerCopy(pLayout->id) == "buffinspectroot")
        {
            continue;
        }

        const OutdoorGameView::HudTextureHandle *pTexture =
            HudUiService::ensureHudTextureLoaded(const_cast<OutdoorGameView &>(view), pLayout->primaryAsset);
        const std::optional<OutdoorGameView::ResolvedHudLayoutElement> resolved = resolveLayout(layoutId);

        if (pTexture == nullptr || !resolved)
        {
            continue;
        }

        view.submitHudTexturedQuad(*pTexture, resolved->x, resolved->y, resolved->width, resolved->height);
    }

    const std::optional<OutdoorGameView::ResolvedHudLayoutElement> titleRect = resolveLayout("BuffInspectTitle");

    if (titleRect)
    {
        HudUiService::renderLayoutLabel(view, *pTitleLayout, *titleRect, view.m_buffInspectOverlay.title);
    }

    if (pBodyFont == nullptr)
    {
        return;
    }

    const std::optional<OutdoorGameView::ResolvedHudLayoutElement> bodyBaseRect = resolveLayout("BuffInspectBody");

    if (!bodyBaseRect)
    {
        return;
    }

    bgfx::TextureHandle coloredMainTextureHandle =
        HudUiService::ensureHudFontMainTextureColor(view, *pBodyFont, pBodyLayout->textColorAbgr);

    if (!bgfx::isValid(coloredMainTextureHandle))
    {
        coloredMainTextureHandle = pBodyFont->mainTextureHandle;
    }

    float textX = std::round(bodyBaseRect->x + pBodyLayout->textPadX * popupScale);
    float textY = std::round(bodyBaseRect->y + pBodyLayout->textPadY * popupScale);

    for (const std::string &line : bodyLines)
    {
        HudUiService::renderHudFontLayer(view, *pBodyFont, pBodyFont->shadowTextureHandle, line, textX, textY, popupScale);
        HudUiService::renderHudFontLayer(view, *pBodyFont, coloredMainTextureHandle, line, textX, textY, popupScale);
        textY += bodyLineHeight;
    }
}

void GameplayPartyOverlayRenderer::renderCharacterDetailOverlay(const OutdoorGameView &view, int width, int height)
{
    if (!view.m_characterDetailOverlay.active
        || !bgfx::isValid(view.m_texturedTerrainProgramHandle)
        || !bgfx::isValid(view.m_terrainTextureSamplerHandle)
        || width <= 0
        || height <= 0)
    {
        return;
    }

    const OutdoorGameView::HudLayoutElement *pRootLayout = HudUiService::findHudLayoutElement(view, "CharacterDetailRoot");
    const OutdoorGameView::HudLayoutElement *pTitleLayout = HudUiService::findHudLayoutElement(view, "CharacterDetailTitle");
    const OutdoorGameView::HudLayoutElement *pBodyLayout = HudUiService::findHudLayoutElement(view, "CharacterDetailBody");

    if (pRootLayout == nullptr || pTitleLayout == nullptr || pBodyLayout == nullptr)
    {
        return;
    }

    const UiViewportRect uiViewport = computeUiViewportRect(width, height);
    const float baseScale = std::min(uiViewport.width / HudReferenceWidth, uiViewport.height / HudReferenceHeight);
    const float popupScale = std::clamp(baseScale, pRootLayout->minScale, pRootLayout->maxScale);
    const OutdoorGameView::HudFontHandle *pTitleFont = HudUiService::findHudFont(view, "Create");
    const OutdoorGameView::HudFontHandle *pBodyFont =
        HudUiService::findHudFont(view, pBodyLayout->fontName.empty() ? "Create" : pBodyLayout->fontName);
    const OutdoorGameView::HudFontHandle *pSpellValueFont = HudUiService::findHudFont(view, "SMALLNUM");

    if (pTitleFont == nullptr || pBodyFont == nullptr || pSpellValueFont == nullptr)
    {
        return;
    }

    const float titleFontScale = popupScale;
    const float bodyFontScale = popupScale;
    const float spellValueFontScale = popupScale;
    const float titleLineHeight = static_cast<float>(pTitleFont->fontHeight) * titleFontScale;
    const float bodyLineHeight = static_cast<float>(pBodyFont->fontHeight) * bodyFontScale;
    const float spellValueLineHeight = static_cast<float>(pSpellValueFont->fontHeight) * spellValueFontScale;
    const size_t activeSpellRows = std::max<size_t>(1, view.m_characterDetailOverlay.activeSpells.size());
    const float spellRowsHeight = spellValueLineHeight * static_cast<float>(activeSpellRows);
    const float rootWidth = std::max(425.0f * popupScale, pRootLayout->width * popupScale);
    const float rootHeight = std::max(200.0f * popupScale, 112.0f * popupScale + spellRowsHeight + 14.0f * popupScale);
    const float popupGap = 12.0f * popupScale;
    float rootX = view.m_characterDetailOverlay.sourceX + view.m_characterDetailOverlay.sourceWidth + popupGap;

    if (rootX + rootWidth > uiViewport.x + uiViewport.width)
    {
        rootX = view.m_characterDetailOverlay.sourceX - rootWidth - popupGap;
    }

    rootX = std::clamp(rootX, uiViewport.x, uiViewport.x + uiViewport.width - rootWidth);
    float rootY = view.m_characterDetailOverlay.sourceY + (view.m_characterDetailOverlay.sourceHeight - rootHeight) * 0.5f;
    rootY = std::clamp(rootY, uiViewport.y, uiViewport.y + uiViewport.height - rootHeight);
    const OutdoorGameView::ResolvedHudLayoutElement rootRect = {
        std::round(rootX),
        std::round(rootY),
        std::round(rootWidth),
        std::round(rootHeight),
        popupScale
    };

    setupHudProjection(width, height);

    const OutdoorGameView::HudTextureHandle *pBackgroundTexture =
        HudUiService::ensureHudTextureLoaded(const_cast<OutdoorGameView &>(view), pRootLayout->primaryAsset);

    if (pBackgroundTexture != nullptr)
    {
        view.submitHudTexturedQuad(*pBackgroundTexture, rootRect.x, rootRect.y, rootRect.width, rootRect.height);
    }

    std::function<std::optional<OutdoorGameView::ResolvedHudLayoutElement>(const std::string &)> resolveLayout;
    resolveLayout =
        [&view, &rootRect, popupScale, &resolveLayout](
            const std::string &layoutId) -> std::optional<OutdoorGameView::ResolvedHudLayoutElement>
        {
            const OutdoorGameView::HudLayoutElement *pLayout = HudUiService::findHudLayoutElement(view, layoutId);

            if (pLayout == nullptr)
            {
                return std::nullopt;
            }

            float resolvedWidth = pLayout->width * popupScale;
            float resolvedHeight = pLayout->height * popupScale;
            const std::string normalizedLayoutId = toLowerCopy(layoutId);

            if (normalizedLayoutId == "characterdetailcorner_topedge"
                || normalizedLayoutId == "characterdetailcorner_bottomedge")
            {
                resolvedWidth = rootRect.width;
            }

            if (normalizedLayoutId == "characterdetailcorner_leftedge"
                || normalizedLayoutId == "characterdetailcorner_rightedge")
            {
                resolvedHeight = rootRect.height;
            }

            OutdoorGameView::ResolvedHudLayoutElement parent = rootRect;

            if (!pLayout->parentId.empty() && toLowerCopy(pLayout->parentId) != "characterdetailroot")
            {
                const std::optional<OutdoorGameView::ResolvedHudLayoutElement> resolvedParent = resolveLayout(pLayout->parentId);

                if (resolvedParent)
                {
                    parent = *resolvedParent;
                }
            }

            return OutdoorGameView::resolveAttachedHudLayoutRect(
                pLayout->attachTo,
                parent,
                resolvedWidth,
                resolvedHeight,
                pLayout->gapX,
                pLayout->gapY,
                popupScale);
        };

    const std::vector<std::string> orderedLayoutIds = HudUiService::sortedHudLayoutIdsForScreen(view, "CharacterDetail");

    for (const std::string &layoutId : orderedLayoutIds)
    {
        const OutdoorGameView::HudLayoutElement *pLayout = HudUiService::findHudLayoutElement(view, layoutId);

        if (pLayout == nullptr
            || !pLayout->visible
            || pLayout->primaryAsset.empty()
            || toLowerCopy(pLayout->id) == "characterdetailroot")
        {
            continue;
        }

        const OutdoorGameView::HudTextureHandle *pTexture =
            HudUiService::ensureHudTextureLoaded(const_cast<OutdoorGameView &>(view), pLayout->primaryAsset);
        const std::optional<OutdoorGameView::ResolvedHudLayoutElement> resolved = resolveLayout(layoutId);

        if (pTexture == nullptr || !resolved)
        {
            continue;
        }

        view.submitHudTexturedQuad(*pTexture, resolved->x, resolved->y, resolved->width, resolved->height);
    }

    const auto renderHudText =
        [&view](
            const OutdoorGameView::HudFontHandle &font,
            const std::string &text,
            float textX,
            float textY,
            float fontScale,
            uint32_t colorAbgr)
        {
            if (text.empty())
            {
                return;
            }

            bgfx::TextureHandle coloredMainTextureHandle =
                HudUiService::ensureHudFontMainTextureColor(view, font, colorAbgr);

            if (!bgfx::isValid(coloredMainTextureHandle))
            {
                coloredMainTextureHandle = font.mainTextureHandle;
            }

            HudUiService::renderHudFontLayer(view, font, font.shadowTextureHandle, text, textX, textY, fontScale);
            HudUiService::renderHudFontLayer(view, font, coloredMainTextureHandle, text, textX, textY, fontScale);
        };
    const auto submitSolidQuad =
        [&view](float x, float y, float quadWidth, float quadHeight, uint32_t abgr)
        {
            if (quadWidth <= 0.0f || quadHeight <= 0.0f)
            {
                return;
            }

            const std::string textureName = "__character_detail_solid_" + std::to_string(abgr);
            const OutdoorGameView::HudTextureHandle *pSolidTexture =
                HudUiService::ensureSolidHudTextureLoaded(
                    const_cast<OutdoorGameView &>(view),
                    textureName,
                    abgr);

            if (pSolidTexture == nullptr)
            {
                return;
            }

            view.submitHudTexturedQuad(*pSolidTexture, x, y, quadWidth, quadHeight);
        };

    const float portraitFrameX = std::round(rootRect.x + 20.0f * popupScale);
    const float portraitFrameY = std::round(rootRect.y + 18.0f * popupScale);
    const float portraitFrameWidth = std::round(50.0f * popupScale);
    const float portraitFrameHeight = std::round(64.0f * popupScale);
    const float portraitBorderThickness = std::max(1.0f, std::round(popupScale));

    submitSolidQuad(
        portraitFrameX - portraitBorderThickness,
        portraitFrameY - portraitBorderThickness,
        portraitFrameWidth + portraitBorderThickness * 2.0f,
        portraitFrameHeight + portraitBorderThickness * 2.0f,
        CharacterDetailGoldColorAbgr);
    submitSolidQuad(
        portraitFrameX,
        portraitFrameY,
        portraitFrameWidth,
        portraitFrameHeight,
        makeAbgrColor(0, 0, 0));

    OutdoorGameView &mutableView = const_cast<OutdoorGameView &>(view);
    const OutdoorGameView::HudTextureHandle *pPortraitTexture =
        HudUiService::ensureHudTextureLoaded(mutableView, view.m_characterDetailOverlay.portraitTextureName);

    if (pPortraitTexture != nullptr && pPortraitTexture->width > 0 && pPortraitTexture->height > 0)
    {
        const float portraitScale = std::min(
            portraitFrameWidth / static_cast<float>(pPortraitTexture->width),
            portraitFrameHeight / static_cast<float>(pPortraitTexture->height));
        const float portraitWidth = static_cast<float>(pPortraitTexture->width) * portraitScale;
        const float portraitHeight = static_cast<float>(pPortraitTexture->height) * portraitScale;
        const float portraitX = std::round(portraitFrameX + (portraitFrameWidth - portraitWidth) * 0.5f);
        const float portraitY = std::round(portraitFrameY + (portraitFrameHeight - portraitHeight) * 0.5f);
        view.submitHudTexturedQuad(*pPortraitTexture, portraitX, portraitY, portraitWidth, portraitHeight);
    }

    const float infoX = std::round(rootRect.x + 102.0f * popupScale);
    const float titleY = std::round(rootRect.y + 18.0f * popupScale);
    const float titleAvailableWidth = std::max(0.0f, rootRect.width - (infoX - rootRect.x) - 12.0f * popupScale);
    std::string titleText = HudUiService::clampHudTextToWidth(
        view,
        *pTitleFont,
        view.m_characterDetailOverlay.title,
        titleAvailableWidth / titleFontScale);

    if (titleText.empty())
    {
        titleText = view.m_characterDetailOverlay.title;
    }

    renderHudText(*pTitleFont, titleText, infoX, titleY, titleFontScale, CharacterDetailGoldColorAbgr);

    const float statsX = infoX;
    const float statsLineAdvance = std::round(15.0f * popupScale);
    float statsY = std::round(rootRect.y + 35.0f * popupScale);
    renderHudText(
        *pBodyFont,
        "Hit Points : " + view.m_characterDetailOverlay.hitPointsText,
        statsX,
        statsY,
        bodyFontScale,
        pBodyLayout->textColorAbgr);
    statsY += statsLineAdvance;
    renderHudText(
        *pBodyFont,
        "Spell Points : " + view.m_characterDetailOverlay.spellPointsText,
        statsX,
        statsY,
        bodyFontScale,
        pBodyLayout->textColorAbgr);
    statsY += statsLineAdvance;
    renderHudText(
        *pBodyFont,
        "Condition: " + view.m_characterDetailOverlay.conditionText,
        statsX,
        statsY,
        bodyFontScale,
        pBodyLayout->textColorAbgr);
    statsY += statsLineAdvance;
    renderHudText(
        *pBodyFont,
        "Quick Spell: " + view.m_characterDetailOverlay.quickSpellText,
        statsX,
        statsY,
        bodyFontScale,
        pBodyLayout->textColorAbgr);

    const float activeSpellsHeaderX = std::round(rootRect.x + 12.0f * popupScale);
    const float activeSpellsHeaderY = std::round(rootRect.y + 100.0f * popupScale);
    renderHudText(
        *pBodyFont,
        "Active Spells:",
        activeSpellsHeaderX,
        activeSpellsHeaderY,
        bodyFontScale,
        pBodyLayout->textColorAbgr);

    const float spellNameX = std::round(rootRect.x + 31.0f * popupScale);
    const float spellDurationRightX = std::round(rootRect.x + rootRect.width - 27.0f * popupScale);
    float spellRowY = std::round(rootRect.y + 121.0f * popupScale);

    if (view.m_characterDetailOverlay.activeSpells.empty())
    {
        renderHudText(
            *pSpellValueFont,
            "None",
            spellNameX,
            spellRowY,
            spellValueFontScale,
            pBodyLayout->textColorAbgr);
        return;
    }

    for (const OutdoorGameView::CharacterDetailOverlayState::ActiveSpellLine &spellLine :
         view.m_characterDetailOverlay.activeSpells)
    {
        renderHudText(
            *pSpellValueFont,
            spellLine.name,
            spellNameX,
            spellRowY,
            spellValueFontScale,
            pBodyLayout->textColorAbgr);
        const float durationWidth =
            HudUiService::measureHudTextWidth(view, *pSpellValueFont, spellLine.duration) * spellValueFontScale;
        const float durationX = std::round(spellDurationRightX - durationWidth);
        renderHudText(
            *pSpellValueFont,
            spellLine.duration,
            durationX,
            spellRowY,
            spellValueFontScale,
            pBodyLayout->textColorAbgr);
        spellRowY += spellValueLineHeight;
    }
}

void GameplayPartyOverlayRenderer::renderCharacterOverlay(
    GameplayOverlayContext &context,
    int width,
    int height,
    bool renderAboveHud)
{
    if (context.currentHudScreenState() != GameplayHudScreenState::Character
        || context.partyReadOnly() == nullptr
        || !context.hasHudRenderResources()
        || width <= 0
        || height <= 0
        || context.isAdventurersInnScreenActive())
    {
        return;
    }

    context.prepareHudView(width, height);
    renderViewportParchmentSidePanels(context, width, height);

    const UiViewportRect uiViewport = computeUiViewportRect(width, height);
    const float baseScale = std::min(uiViewport.width / HudReferenceWidth, uiViewport.height / HudReferenceHeight);
    float characterMouseX = 0.0f;
    float characterMouseY = 0.0f;
    const SDL_MouseButtonFlags characterMouseButtons = SDL_GetMouseState(&characterMouseX, &characterMouseY);
    const bool isLeftMousePressed = (characterMouseButtons & SDL_BUTTON_LMASK) != 0;

    const auto submitSolidHudQuad =
        [&context](const std::string &textureName, float x, float y, float quadWidth, float quadHeight, uint32_t abgr)
        {
            if (quadWidth <= 0.0f || quadHeight <= 0.0f)
            {
                return;
            }

            const std::optional<GameplayHudTextureHandle> solidTexture =
                context.ensureSolidHudTextureLoaded(textureName, abgr);

            if (!solidTexture.has_value())
            {
                return;
            }

            context.submitHudTexturedQuad(*solidTexture, x, y, quadWidth, quadHeight);
        };
    const auto renderInventoryTargetCrosshair =
        [&submitSolidHudQuad](float centerX, float centerY, float overlayScale, uint32_t crosshairColor, uint32_t shadowColor)
        {
            const float armLength = std::round(10.0f * overlayScale);
            const float armGap = std::round(4.0f * overlayScale);
            const float stroke = std::max(1.0f, std::round(2.0f * overlayScale));
            const auto submitCrosshairLine =
                [&submitSolidHudQuad, crosshairColor, shadowColor](float x, float y, float quadWidth, float quadHeight)
                {
                    submitSolidHudQuad(
                        "__inventory_target_crosshair_shadow__",
                        x + 1.0f,
                        y + 1.0f,
                        quadWidth,
                        quadHeight,
                        shadowColor);
                    submitSolidHudQuad(
                        "__inventory_target_crosshair__",
                        x,
                        y,
                        quadWidth,
                        quadHeight,
                        crosshairColor);
                };

            submitCrosshairLine(centerX - armGap - armLength, centerY - stroke * 0.5f, armLength, stroke);
            submitCrosshairLine(centerX + armGap, centerY - stroke * 0.5f, armLength, stroke);
            submitCrosshairLine(centerX - stroke * 0.5f, centerY - armGap - armLength, stroke, armLength);
            submitCrosshairLine(centerX - stroke * 0.5f, centerY + armGap, stroke, armLength);
        };
    const auto renderInventoryTargetFrame =
        [&submitSolidHudQuad](float x, float y, float rectWidth, float rectHeight, float overlayScale, uint32_t frameColor, uint32_t shadowColor)
        {
            const float thickness = std::max(1.0f, std::round(2.0f * overlayScale));
            const auto submitFrameQuad =
                [&submitSolidHudQuad, frameColor, shadowColor](
                    float quadX,
                    float quadY,
                    float quadWidth,
                    float quadHeight)
                {
                    submitSolidHudQuad(
                        "__inventory_target_frame_shadow__",
                        quadX + 1.0f,
                        quadY + 1.0f,
                        quadWidth,
                        quadHeight,
                        shadowColor);
                    submitSolidHudQuad(
                        "__inventory_target_frame__",
                        quadX,
                        quadY,
                        quadWidth,
                        quadHeight,
                        frameColor);
                };

            submitFrameQuad(x - thickness, y - thickness, rectWidth + thickness * 2.0f, thickness);
            submitFrameQuad(x - thickness, y + rectHeight, rectWidth + thickness * 2.0f, thickness);
            submitFrameQuad(x - thickness, y, thickness, rectHeight);
            submitFrameQuad(x + rectWidth, y, thickness, rectHeight);
        };

    const GameplayUiController::CharacterScreenState &characterScreen = context.characterScreenReadOnly();
    const std::string activePageRootId =
        characterScreen.page == GameplayUiController::CharacterPage::Stats
            ? "characterstatspage"
            : (characterScreen.page == GameplayUiController::CharacterPage::Skills
                ? "characterskillspage"
                : (characterScreen.page == GameplayUiController::CharacterPage::Inventory
                    ? "characterinventorypage"
                    : "characterawardspage"));
    std::unordered_map<std::string, bool> visibleCharacterAncestorCache;
    std::function<bool(const UiLayoutManager::LayoutElement &)> hasVisibleCharacterAncestors;
    hasVisibleCharacterAncestors =
        [&context, &activePageRootId, &visibleCharacterAncestorCache, &hasVisibleCharacterAncestors](
            const UiLayoutManager::LayoutElement &layout) -> bool
        {
            const std::string normalizedId = toLowerCopy(layout.id);
            const auto cachedIterator = visibleCharacterAncestorCache.find(normalizedId);

            if (cachedIterator != visibleCharacterAncestorCache.end())
            {
                return cachedIterator->second;
            }

            bool result = layout.visible && toLowerCopy(layout.screen) == "character";

            if (result
                && (normalizedId == "characterstatspage"
                    || normalizedId == "characterskillspage"
                    || normalizedId == "characterinventorypage"
                    || normalizedId == "characterawardspage"))
            {
                result = normalizedId == activePageRootId;
            }

            if (result && !layout.parentId.empty())
            {
                const UiLayoutManager::LayoutElement *pParent = context.findHudLayoutElement(layout.parentId);
                result = pParent != nullptr && hasVisibleCharacterAncestors(*pParent);
            }

            visibleCharacterAncestorCache[normalizedId] = result;
            return result;
        };

    const Party &party = *context.partyReadOnly();
    const Character *pCharacter = context.selectedCharacterScreenCharacter();
    const std::vector<std::string> orderedCharacterLayoutIds = context.sortedHudLayoutIdsForScreen("Character");
    const int hudZThreshold = context.defaultHudLayoutZIndexForScreen("OutdoorHud");
    const auto shouldRenderInCurrentPass =
        [renderAboveHud, hudZThreshold](int zIndex) -> bool
        {
            return renderAboveHud ? zIndex >= hudZThreshold : zIndex < hudZThreshold;
        };
    const size_t characterSourceIndex = context.selectedCharacterScreenSourceIndex();

    CharacterSheetSummary summary = {};
    std::string mightValue = "0 / 0";
    std::string intellectValue = "0 / 0";
    std::string personalityValue = "0 / 0";
    std::string enduranceValue = "0 / 0";
    std::string accuracyValue = "0 / 0";
    std::string speedValue = "0 / 0";
    std::string luckValue = "0 / 0";
    std::string hitPointsValue = "0 / 0";
    std::string spellPointsValue = "0 / 0";
    std::string armorClassValue = "0 / 0";
    std::string conditionValue = "-";
    std::string quickSpellValue = "-";
    std::string ageValue = "-";
    std::string levelValue = "0 / 0";
    std::string experienceValue = "-";
    std::string attackValue = "-";
    std::string meleeDamageValue = "-";
    std::string shootValue = "-";
    std::string rangedDamageValue = "-";
    std::string fireResistanceValue = "0 / 0";
    std::string airResistanceValue = "0 / 0";
    std::string waterResistanceValue = "0 / 0";
    std::string earthResistanceValue = "0 / 0";
    std::string mindResistanceValue = "0 / 0";
    std::string bodyResistanceValue = "0 / 0";
    std::string awards;
    std::string inventoryInfo;
    bool canTrainToNextLevel = false;

    if (pCharacter != nullptr)
    {
        summary = GameMechanics::buildCharacterSheetSummary(
            *pCharacter,
            context.itemTable(),
            context.standardItemEnchantTable(),
            context.specialItemEnchantTable());

        const auto formatPair = [](int actualValue, int baseValue) -> std::string
        {
            return std::to_string(actualValue) + " / " + std::to_string(baseValue);
        };
        const auto formatSheetValue = [&formatPair](const CharacterSheetValue &value) -> std::string
        {
            if (value.infinite)
            {
                return "INF";
            }

            return formatPair(value.actual, value.base);
        };

        mightValue = formatSheetValue(summary.might);
        intellectValue = formatSheetValue(summary.intellect);
        personalityValue = formatSheetValue(summary.personality);
        enduranceValue = formatSheetValue(summary.endurance);
        accuracyValue = formatSheetValue(summary.accuracy);
        speedValue = formatSheetValue(summary.speed);
        luckValue = formatSheetValue(summary.luck);
        hitPointsValue = std::to_string(summary.health.current) + " / " + std::to_string(summary.health.maximum);
        spellPointsValue =
            std::to_string(summary.spellPoints.current) + " / " + std::to_string(summary.spellPoints.maximum);
        armorClassValue = formatSheetValue(summary.armorClass);
        conditionValue = summary.conditionText;
        quickSpellValue = summary.quickSpellText;
        ageValue = summary.ageText;
        levelValue = formatSheetValue(summary.level);
        experienceValue = summary.experienceText;
        canTrainToNextLevel = summary.canTrainToNextLevel;
        attackValue = std::to_string(summary.combat.attack);
        meleeDamageValue = summary.combat.meleeDamageText;
        shootValue = summary.combat.shoot ? std::to_string(*summary.combat.shoot) : "N/A";
        rangedDamageValue = summary.combat.rangedDamageText;
        fireResistanceValue = formatSheetValue(summary.fireResistance);
        airResistanceValue = formatSheetValue(summary.airResistance);
        waterResistanceValue = formatSheetValue(summary.waterResistance);
        earthResistanceValue = formatSheetValue(summary.earthResistance);
        mindResistanceValue = formatSheetValue(summary.mindResistance);
        bodyResistanceValue = formatSheetValue(summary.bodyResistance);
        awards = "Awards earned: " + std::to_string(pCharacter->awards.size());
    }

    const CharacterSkillUiData skillUiData = buildCharacterSkillUiData(pCharacter);
    const std::optional<GameplayHudFontHandle> skillRowFont = context.findHudFont("Lucida");
    const float skillRowHeight =
        skillRowFont.has_value() ? static_cast<float>(std::max(1, skillRowFont->fontHeight - 3)) : 11.0f;
    context.clearHudLayoutRuntimeHeightOverrides();
    context.setHudLayoutRuntimeHeightOverride(
        "CharacterSkillsWeaponsListRegion",
        skillRowHeight * static_cast<float>(std::max<size_t>(1, skillUiData.weaponRows.size())));
    context.setHudLayoutRuntimeHeightOverride(
        "CharacterSkillsMagicListRegion",
        skillRowHeight * static_cast<float>(std::max<size_t>(1, skillUiData.magicRows.size())));
    context.setHudLayoutRuntimeHeightOverride(
        "CharacterSkillsArmorListRegion",
        skillRowHeight * static_cast<float>(std::max<size_t>(1, skillUiData.armorRows.size())));
    context.setHudLayoutRuntimeHeightOverride(
        "CharacterSkillsMiscListRegion",
        skillRowHeight * static_cast<float>(std::max<size_t>(1, skillUiData.miscRows.size())));

    const uint32_t skillPointsValueColorAbgr =
        pCharacter != nullptr && pCharacter->skillPoints > 0
            ? packHudColorAbgr(0, 255, 0)
            : packHudColorAbgr(255, 255, 255);
    const uint32_t experienceValueColorAbgr =
        canTrainToNextLevel ? packHudColorAbgr(0, 255, 0) : packHudColorAbgr(255, 255, 255);
    const CharacterDollEntry *pCharacterDollEntry =
        resolveCharacterDollEntry(context.characterDollTable(), pCharacter);
    const CharacterDollTypeEntry *pCharacterDollType =
        pCharacterDollEntry != nullptr && context.characterDollTable() != nullptr
            ? context.characterDollTable()->getDollType(pCharacterDollEntry->dollTypeId)
            : nullptr;
    const ItemDefinition *pMainHandItem =
        pCharacter != nullptr && context.itemTable() != nullptr ? context.itemTable()->get(pCharacter->equipment.mainHand) : nullptr;
    const ItemDefinition *pOffHandItem =
        pCharacter != nullptr && context.itemTable() != nullptr ? context.itemTable()->get(pCharacter->equipment.offHand) : nullptr;
    SkillMastery spearMastery = SkillMastery::None;

    if (pCharacter != nullptr)
    {
        const CharacterSkill *pSpearSkill = pCharacter->findSkill("Spear");

        if (pSpearSkill != nullptr)
        {
            spearMastery = pSpearSkill->mastery;
        }
    }

    const bool leftHandDisabled =
        pMainHandItem != nullptr
        && (pMainHandItem->equipStat == "Weapon2"
            || (canonicalSkillName(pMainHandItem->skillGroup) == "Spear" && spearMastery < SkillMastery::Master));
    const auto submitCharacterDollLayer =
        [&context](
            const UiLayoutManager::LayoutElement &layout,
            const GameplayResolvedHudLayoutElement &resolvedAnchor,
            const std::string &assetName,
            int offsetX,
            int offsetY)
        {
            if (assetName.empty() || assetName == "none")
            {
                return;
            }

            const std::optional<GameplayHudTextureHandle> texture = context.ensureHudTextureLoaded(assetName);

            if (!texture.has_value() || texture->width <= 0 || texture->height <= 0)
            {
                return;
            }

            float anchorX = resolvedAnchor.x + resolvedAnchor.width * 0.5f;
            float anchorY = resolvedAnchor.y + resolvedAnchor.height * 0.5f;
            const auto setAnchorPoint = [&](float normalizedX, float normalizedY)
            {
                anchorX = resolvedAnchor.x + resolvedAnchor.width * normalizedX;
                anchorY = resolvedAnchor.y + resolvedAnchor.height * normalizedY;
            };

            if (!layout.parentId.empty())
            {
                switch (layout.attachTo)
                {
                    case UiLayoutManager::LayoutAttachMode::None:
                    case UiLayoutManager::LayoutAttachMode::CenterIn:
                        setAnchorPoint(0.5f, 0.5f);
                        break;
                    case UiLayoutManager::LayoutAttachMode::RightOf:
                    case UiLayoutManager::LayoutAttachMode::Below:
                    case UiLayoutManager::LayoutAttachMode::InsideTopLeft:
                        setAnchorPoint(0.0f, 0.0f);
                        break;
                    case UiLayoutManager::LayoutAttachMode::LeftOf:
                    case UiLayoutManager::LayoutAttachMode::InsideTopRight:
                        setAnchorPoint(1.0f, 0.0f);
                        break;
                    case UiLayoutManager::LayoutAttachMode::Above:
                        setAnchorPoint(0.0f, 1.0f);
                        break;
                    case UiLayoutManager::LayoutAttachMode::CenterAbove:
                    case UiLayoutManager::LayoutAttachMode::InsideBottomCenter:
                        setAnchorPoint(0.5f, 1.0f);
                        break;
                    case UiLayoutManager::LayoutAttachMode::CenterBelow:
                    case UiLayoutManager::LayoutAttachMode::InsideTopCenter:
                        setAnchorPoint(0.5f, 0.0f);
                        break;
                    case UiLayoutManager::LayoutAttachMode::InsideLeft:
                        setAnchorPoint(0.0f, 0.5f);
                        break;
                    case UiLayoutManager::LayoutAttachMode::InsideRight:
                        setAnchorPoint(1.0f, 0.5f);
                        break;
                    case UiLayoutManager::LayoutAttachMode::InsideBottomLeft:
                        setAnchorPoint(0.0f, 1.0f);
                        break;
                    case UiLayoutManager::LayoutAttachMode::InsideBottomRight:
                        setAnchorPoint(1.0f, 1.0f);
                        break;
                }
            }
            else
            {
                switch (layout.anchor)
                {
                    case UiLayoutManager::LayoutAnchor::TopLeft:
                        setAnchorPoint(0.0f, 0.0f);
                        break;
                    case UiLayoutManager::LayoutAnchor::TopCenter:
                        setAnchorPoint(0.5f, 0.0f);
                        break;
                    case UiLayoutManager::LayoutAnchor::TopRight:
                        setAnchorPoint(1.0f, 0.0f);
                        break;
                    case UiLayoutManager::LayoutAnchor::Left:
                        setAnchorPoint(0.0f, 0.5f);
                        break;
                    case UiLayoutManager::LayoutAnchor::Center:
                        setAnchorPoint(0.5f, 0.5f);
                        break;
                    case UiLayoutManager::LayoutAnchor::Right:
                        setAnchorPoint(1.0f, 0.5f);
                        break;
                    case UiLayoutManager::LayoutAnchor::BottomLeft:
                        setAnchorPoint(0.0f, 1.0f);
                        break;
                    case UiLayoutManager::LayoutAnchor::BottomCenter:
                        setAnchorPoint(0.5f, 1.0f);
                        break;
                    case UiLayoutManager::LayoutAnchor::BottomRight:
                        setAnchorPoint(1.0f, 1.0f);
                        break;
                }
            }

            anchorX += static_cast<float>(offsetX) * resolvedAnchor.scale;
            anchorY += static_cast<float>(offsetY) * resolvedAnchor.scale;
            const float layerWidth = static_cast<float>(texture->width) * resolvedAnchor.scale;
            const float layerHeight = static_cast<float>(texture->height) * resolvedAnchor.scale;
            float layerX = std::round(anchorX - layerWidth * 0.5f);
            float layerY = std::round(anchorY - layerHeight * 0.5f);

            if (!layout.parentId.empty())
            {
                switch (layout.attachTo)
                {
                    case UiLayoutManager::LayoutAttachMode::RightOf:
                    case UiLayoutManager::LayoutAttachMode::Below:
                    case UiLayoutManager::LayoutAttachMode::InsideTopLeft:
                        layerX = std::round(anchorX);
                        layerY = std::round(anchorY);
                        break;
                    case UiLayoutManager::LayoutAttachMode::LeftOf:
                    case UiLayoutManager::LayoutAttachMode::InsideTopRight:
                        layerX = std::round(anchorX - layerWidth);
                        layerY = std::round(anchorY);
                        break;
                    case UiLayoutManager::LayoutAttachMode::Above:
                        layerX = std::round(anchorX);
                        layerY = std::round(anchorY - layerHeight);
                        break;
                    case UiLayoutManager::LayoutAttachMode::CenterAbove:
                        layerY = std::round(anchorY - layerHeight);
                        break;
                    case UiLayoutManager::LayoutAttachMode::CenterBelow:
                    case UiLayoutManager::LayoutAttachMode::InsideTopCenter:
                        layerY = std::round(anchorY);
                        break;
                    case UiLayoutManager::LayoutAttachMode::InsideLeft:
                        layerX = std::round(anchorX);
                        break;
                    case UiLayoutManager::LayoutAttachMode::InsideRight:
                        layerX = std::round(anchorX - layerWidth);
                        break;
                    case UiLayoutManager::LayoutAttachMode::InsideBottomLeft:
                        layerX = std::round(anchorX);
                        layerY = std::round(anchorY - layerHeight);
                        break;
                    case UiLayoutManager::LayoutAttachMode::InsideBottomCenter:
                        layerY = std::round(anchorY - layerHeight);
                        break;
                    case UiLayoutManager::LayoutAttachMode::InsideBottomRight:
                        layerX = std::round(anchorX - layerWidth);
                        layerY = std::round(anchorY - layerHeight);
                        break;
                    case UiLayoutManager::LayoutAttachMode::None:
                    case UiLayoutManager::LayoutAttachMode::CenterIn:
                        break;
                }
            }
            else
            {
                switch (layout.anchor)
                {
                    case UiLayoutManager::LayoutAnchor::TopLeft:
                        layerX = std::round(anchorX);
                        layerY = std::round(anchorY);
                        break;
                    case UiLayoutManager::LayoutAnchor::TopCenter:
                        layerY = std::round(anchorY);
                        break;
                    case UiLayoutManager::LayoutAnchor::TopRight:
                        layerX = std::round(anchorX - layerWidth);
                        layerY = std::round(anchorY);
                        break;
                    case UiLayoutManager::LayoutAnchor::Left:
                        layerX = std::round(anchorX);
                        break;
                    case UiLayoutManager::LayoutAnchor::Center:
                        break;
                    case UiLayoutManager::LayoutAnchor::Right:
                        layerX = std::round(anchorX - layerWidth);
                        break;
                    case UiLayoutManager::LayoutAnchor::BottomLeft:
                        layerX = std::round(anchorX);
                        layerY = std::round(anchorY - layerHeight);
                        break;
                    case UiLayoutManager::LayoutAnchor::BottomCenter:
                        layerY = std::round(anchorY - layerHeight);
                        break;
                    case UiLayoutManager::LayoutAnchor::BottomRight:
                        layerX = std::round(anchorX - layerWidth);
                        layerY = std::round(anchorY - layerHeight);
                        break;
                }
            }

            context.submitHudTexturedQuad(*texture, layerX, layerY, layerWidth, layerHeight);
        };
    const auto renderSplitCharacterStatLabel =
        [&context](
            const UiLayoutManager::LayoutElement &layout,
            const GameplayResolvedHudLayoutElement &resolved,
            const SplitCharacterStatValue &value)
        {
            const std::optional<GameplayHudFontHandle> font = context.findHudFont(layout.fontName);

            if (!font.has_value())
            {
                return;
            }

            float fontScale = resolved.scale * std::max(0.1f, layout.textScale);

            if (fontScale >= 1.0f)
            {
                fontScale = snappedHudFontScale(fontScale);
            }
            else
            {
                fontScale = std::max(0.5f, fontScale);
            }

            const std::string separatorText = " / ";
            const float actualWidth = context.measureHudTextWidth(*font, value.actualText) * fontScale;
            const float separatorWidth = context.measureHudTextWidth(*font, separatorText) * fontScale;
            const float baseWidth = context.measureHudTextWidth(*font, value.baseText) * fontScale;
            const float totalWidth = actualWidth + separatorWidth + baseWidth;
            const float labelHeightPixels = static_cast<float>(font->fontHeight) * fontScale;
            float textX = resolved.x + layout.textPadX * resolved.scale;
            float textY = resolved.y + layout.textPadY * resolved.scale;

            switch (layout.textAlignX)
            {
                case UiLayoutManager::TextAlignX::Left:
                    break;
                case UiLayoutManager::TextAlignX::Center:
                    textX = resolved.x + (resolved.width - totalWidth) * 0.5f + layout.textPadX * resolved.scale;
                    break;
                case UiLayoutManager::TextAlignX::Right:
                    textX = resolved.x + resolved.width - totalWidth + layout.textPadX * resolved.scale;
                    break;
            }

            switch (layout.textAlignY)
            {
                case UiLayoutManager::TextAlignY::Top:
                    break;
                case UiLayoutManager::TextAlignY::Middle:
                    textY = resolved.y + (resolved.height - labelHeightPixels) * 0.5f + layout.textPadY * resolved.scale;
                    break;
                case UiLayoutManager::TextAlignY::Bottom:
                    textY = resolved.y + resolved.height - labelHeightPixels + layout.textPadY * resolved.scale;
                    break;
            }

            textX = std::round(textX);
            textY = std::round(textY);
            bgfx::TextureHandle actualTexture = context.ensureHudFontMainTextureColor(*font, value.actualColorAbgr);
            bgfx::TextureHandle baseTexture = context.ensureHudFontMainTextureColor(*font, layout.textColorAbgr);

            if (!bgfx::isValid(actualTexture))
            {
                actualTexture = font->mainTextureHandle;
            }

            if (!bgfx::isValid(baseTexture))
            {
                baseTexture = font->mainTextureHandle;
            }

            context.renderHudFontLayer(*font, font->shadowTextureHandle, value.actualText, textX, textY, fontScale);
            context.renderHudFontLayer(*font, actualTexture, value.actualText, textX, textY, fontScale);
            textX += actualWidth;
            context.renderHudFontLayer(*font, font->shadowTextureHandle, separatorText, textX, textY, fontScale);
            context.renderHudFontLayer(*font, baseTexture, separatorText, textX, textY, fontScale);
            textX += separatorWidth;
            context.renderHudFontLayer(*font, font->shadowTextureHandle, value.baseText, textX, textY, fontScale);
            context.renderHudFontLayer(*font, baseTexture, value.baseText, textX, textY, fontScale);
        };

    for (const std::string &layoutId : orderedCharacterLayoutIds)
    {
        const UiLayoutManager::LayoutElement *pLayout = context.findHudLayoutElement(layoutId);

        if (pLayout == nullptr
            || !hasVisibleCharacterAncestors(*pLayout)
            || !shouldRenderInCurrentPass(pLayout->zIndex))
        {
            continue;
        }

        const std::optional<GameplayResolvedHudLayoutElement> resolved =
            context.resolveHudLayoutElement(layoutId, width, height, pLayout->width, pLayout->height);

        if (!resolved.has_value())
        {
            continue;
        }

        const std::string normalizedLayoutId = toLowerCopy(pLayout->id);

        if (normalizedLayoutId.starts_with("adventurersinn"))
        {
            continue;
        }

        if (normalizedLayoutId == "characterdolljewelryoverlaypanel" && !characterScreen.dollJewelryOverlayOpen)
        {
            continue;
        }

        if (normalizedLayoutId == "characterdollbackground")
        {
            std::string assetName = pLayout->primaryAsset;

            if (pCharacterDollEntry != nullptr
                && !pCharacterDollEntry->backgroundAsset.empty()
                && pCharacterDollEntry->backgroundAsset != "none")
            {
                assetName = pCharacterDollEntry->backgroundAsset;
            }

            if (!assetName.empty())
            {
                const std::optional<GameplayHudTextureHandle> texture = context.ensureHudTextureLoaded(assetName);

                if (texture.has_value())
                {
                    context.submitHudTexturedQuad(*texture, resolved->x, resolved->y, resolved->width, resolved->height);
                }
            }

            continue;
        }

        if (normalizedLayoutId == "characterdollbody" && pCharacterDollEntry != nullptr)
        {
            submitCharacterDollLayer(
                *pLayout,
                *resolved,
                pCharacterDollEntry->bodyAsset,
                pCharacterDollEntry->bodyOffsetX,
                pCharacterDollEntry->bodyOffsetY);
            continue;
        }

        if (normalizedLayoutId == "characterdollrighthand"
            && pCharacterDollEntry != nullptr
            && pCharacterDollType != nullptr)
        {
            submitCharacterDollLayer(
                *pLayout,
                *resolved,
                pMainHandItem != nullptr ? pCharacterDollEntry->rightHandHoldAsset : pCharacterDollEntry->rightHandOpenAsset,
                pMainHandItem != nullptr ? pCharacterDollType->rightHandClosedX : pCharacterDollType->rightHandOpenX,
                pMainHandItem != nullptr ? pCharacterDollType->rightHandClosedY : pCharacterDollType->rightHandOpenY);
            continue;
        }

        if (normalizedLayoutId == "characterdolllefthand"
            && pCharacterDollEntry != nullptr
            && pCharacterDollType != nullptr)
        {
            if (pOffHandItem != nullptr)
            {
                submitCharacterDollLayer(
                    *pLayout,
                    *resolved,
                    pCharacterDollEntry->leftHandHoldAsset,
                    pCharacterDollType->leftHandOpenX,
                    pCharacterDollType->leftHandOpenY);
            }
            else if (leftHandDisabled)
            {
                submitCharacterDollLayer(
                    *pLayout,
                    *resolved,
                    pCharacterDollEntry->leftHandClosedAsset,
                    pCharacterDollType->leftHandClosedX,
                    pCharacterDollType->leftHandClosedY);
            }
            else
            {
                submitCharacterDollLayer(
                    *pLayout,
                    *resolved,
                    pCharacterDollEntry->leftHandOpenAsset,
                    pCharacterDollType->leftHandFingersX,
                    pCharacterDollType->leftHandFingersY);
            }

            continue;
        }

        if (normalizedLayoutId == "characterdollrighthandfingers"
            && pCharacterDollEntry != nullptr
            && pCharacterDollType != nullptr
            && pMainHandItem != nullptr)
        {
            submitCharacterDollLayer(
                *pLayout,
                *resolved,
                pCharacterDollEntry->rightHandFingersAsset,
                pCharacterDollType->rightHandFingersX,
                pCharacterDollType->rightHandFingersY);
            continue;
        }

        if (!pLayout->primaryAsset.empty())
        {
            std::optional<GameplayHudTextureHandle> texture = context.ensureHudTextureLoaded(pLayout->primaryAsset);

            if (pLayout->interactive)
            {
                const std::string *pInteractiveAsset = context.resolveInteractiveAssetName(
                    *pLayout,
                    *resolved,
                    characterMouseX,
                    characterMouseY,
                    isLeftMousePressed);

                if (normalizedLayoutId == "characterinventorybutton"
                    && characterScreen.page == GameplayUiController::CharacterPage::Inventory
                    && !pLayout->pressedAsset.empty())
                {
                    texture = context.ensureHudTextureLoaded(pLayout->pressedAsset);
                }
                else if (normalizedLayoutId == "characterstatsbutton"
                    && characterScreen.page == GameplayUiController::CharacterPage::Stats
                    && !pLayout->pressedAsset.empty())
                {
                    texture = context.ensureHudTextureLoaded(pLayout->pressedAsset);
                }
                else if (normalizedLayoutId == "characterskillsbutton"
                    && characterScreen.page == GameplayUiController::CharacterPage::Skills
                    && !pLayout->pressedAsset.empty())
                {
                    texture = context.ensureHudTextureLoaded(pLayout->pressedAsset);
                }
                else if (normalizedLayoutId == "characterawardsbutton"
                    && characterScreen.page == GameplayUiController::CharacterPage::Awards
                    && !pLayout->pressedAsset.empty())
                {
                    texture = context.ensureHudTextureLoaded(pLayout->pressedAsset);
                }
                else if (pInteractiveAsset != nullptr)
                {
                    texture = context.ensureHudTextureLoaded(*pInteractiveAsset);
                }
            }

            if (texture.has_value())
            {
                context.submitHudTexturedQuad(*texture, resolved->x, resolved->y, resolved->width, resolved->height);
            }
        }

        const std::optional<EquipmentSlot> slot = characterEquipmentSlotForLayoutId(pLayout->id);

        if (slot.has_value() && pCharacter != nullptr && isVisibleInCharacterDollOverlay(*slot, characterScreen.dollJewelryOverlayOpen))
        {
            const uint32_t equippedId = equippedItemId(pCharacter->equipment, *slot);
            const ItemDefinition *pItemDefinition =
                equippedId != 0 && context.itemTable() != nullptr ? context.itemTable()->get(equippedId) : nullptr;

            if (pItemDefinition != nullptr && !pItemDefinition->iconName.empty())
            {
                const bool hasRightHandWeapon = pCharacter->equipment.mainHand != 0;
                const uint32_t dollTypeId = pCharacterDollType != nullptr ? pCharacterDollType->id : 0;
                const std::string textureName =
                    context.resolveEquippedItemHudTextureName(*pItemDefinition, dollTypeId, hasRightHandWeapon, *slot);
                const std::optional<GameplayHudTextureHandle> itemTexture = context.ensureHudTextureLoaded(textureName);

                if (itemTexture.has_value())
                {
                    const std::optional<GameplayResolvedHudLayoutElement> iconRect =
                        context.resolveCharacterEquipmentRenderRect(
                            *pLayout,
                            *pItemDefinition,
                            *itemTexture,
                            pCharacterDollType,
                            *slot,
                            width,
                            height);

                    if (iconRect.has_value())
                    {
                        context.submitHudTexturedQuad(
                            *itemTexture,
                            iconRect->x,
                            iconRect->y,
                            iconRect->width,
                            iconRect->height);

                        GameplayRenderedInspectableHudItem inspectableItem = {};
                        inspectableItem.objectDescriptionId = pItemDefinition->itemId;
                        inspectableItem.hasItemState = true;
                        const std::optional<InventoryItem> equippedItemState =
                            context.partyReadOnly()->equippedItem(characterSourceIndex, *slot);

                        if (equippedItemState.has_value())
                        {
                            inspectableItem.itemState = *equippedItemState;
                        }

                        inspectableItem.sourceType = GameplayUiController::ItemInspectSourceType::Equipment;
                        inspectableItem.sourceMemberIndex = characterSourceIndex;
                        inspectableItem.equipmentSlot = *slot;
                        inspectableItem.textureName = textureName;
                        inspectableItem.x = iconRect->x;
                        inspectableItem.y = iconRect->y;
                        inspectableItem.width = iconRect->width;
                        inspectableItem.height = iconRect->height;
                        context.addRenderedInspectableHudItem(inspectableItem);
                    }
                }
            }
        }

        if (!pLayout->labelText.empty())
        {
            UiLayoutManager::LayoutElement layoutForRender = *pLayout;

            if (normalizedLayoutId == "characterstatsskillpointsvalue"
                || normalizedLayoutId == "characterskillsskillpointsvalue")
            {
                layoutForRender.textColorAbgr = skillPointsValueColorAbgr;
            }
            else if (normalizedLayoutId == "characterstatexperiencevalue")
            {
                layoutForRender.textColorAbgr = experienceValueColorAbgr;
            }

            std::string label = pLayout->labelText;
            label = replaceAllText(label, "{gold}", std::to_string(party.gold()));
            label = replaceAllText(label, "{food}", std::to_string(party.food()));
            label = replaceAllText(label, "{character_name}", pCharacter != nullptr ? pCharacter->name : "");
            label = replaceAllText(
                label,
                "{stats_skill_points}",
                pCharacter != nullptr ? "Skill Points: " + std::to_string(pCharacter->skillPoints) : "Skill Points: 0");
            label = replaceAllText(
                label,
                "{stats_skill_points_value}",
                pCharacter != nullptr ? std::to_string(pCharacter->skillPoints) : "0");
            label = replaceAllText(
                label,
                "{character_class_race}",
                pCharacter != nullptr ? (!pCharacter->className.empty() ? pCharacter->className : pCharacter->role) : "");
            label = replaceAllText(
                label,
                "{quick_stats}",
                pCharacter != nullptr
                    ? ("HP " + std::to_string(pCharacter->health) + "/" + std::to_string(pCharacter->maxHealth)
                        + "\nSP " + std::to_string(pCharacter->spellPoints) + "/" + std::to_string(pCharacter->maxSpellPoints))
                    : "");
            label = replaceAllText(label, "{might_value}", mightValue);
            label = replaceAllText(label, "{intellect_value}", intellectValue);
            label = replaceAllText(label, "{personality_value}", personalityValue);
            label = replaceAllText(label, "{endurance_value}", enduranceValue);
            label = replaceAllText(label, "{accuracy_value}", accuracyValue);
            label = replaceAllText(label, "{speed_value}", speedValue);
            label = replaceAllText(label, "{luck_value}", luckValue);
            label = replaceAllText(label, "{hit_points_value}", hitPointsValue);
            label = replaceAllText(label, "{spell_points_value}", spellPointsValue);
            label = replaceAllText(label, "{armor_class_value}", armorClassValue);
            label = replaceAllText(label, "{condition_value}", conditionValue);
            label = replaceAllText(label, "{quick_spell_value}", quickSpellValue);
            label = replaceAllText(label, "{age_value}", ageValue);
            label = replaceAllText(label, "{level_value}", levelValue);
            label = replaceAllText(label, "{experience_value}", experienceValue);
            label = replaceAllText(label, "{attack_value}", attackValue);
            label = replaceAllText(label, "{melee_damage_value}", meleeDamageValue);
            label = replaceAllText(label, "{shoot_value}", shootValue);
            label = replaceAllText(label, "{ranged_damage_value}", rangedDamageValue);
            label = replaceAllText(label, "{fire_resistance_value}", fireResistanceValue);
            label = replaceAllText(label, "{air_resistance_value}", airResistanceValue);
            label = replaceAllText(label, "{water_resistance_value}", waterResistanceValue);
            label = replaceAllText(label, "{earth_resistance_value}", earthResistanceValue);
            label = replaceAllText(label, "{mind_resistance_value}", mindResistanceValue);
            label = replaceAllText(label, "{body_resistance_value}", bodyResistanceValue);
            label = replaceAllText(label, "{awards}", awards);
            label = replaceAllText(label, "{award_detail}", "");
            label = replaceAllText(label, "{inventory_info}", inventoryInfo);

            if (label.find('{') != std::string::npos)
            {
                label.clear();
            }

            SplitCharacterStatValue splitValue = {};

            if (tryGetSplitCharacterStatValue(normalizedLayoutId, summary, splitValue))
            {
                renderSplitCharacterStatLabel(layoutForRender, *resolved, splitValue);
            }
            else
            {
                context.renderLayoutLabel(layoutForRender, *resolved, label);
            }
        }
    }

    if (characterScreen.page == GameplayUiController::CharacterPage::Inventory && pCharacter != nullptr && context.itemTable() != nullptr)
    {
        const UiLayoutManager::LayoutElement *pInventoryGridLayout = context.findHudLayoutElement("CharacterInventoryGrid");

        if (pInventoryGridLayout != nullptr && shouldRenderInCurrentPass(pInventoryGridLayout->zIndex))
        {
            const std::optional<GameplayResolvedHudLayoutElement> resolvedInventoryGrid =
                context.resolveHudLayoutElement(
                    "CharacterInventoryGrid",
                    width,
                    height,
                    pInventoryGridLayout->width,
                    pInventoryGridLayout->height);

            if (resolvedInventoryGrid.has_value())
            {
                const InventoryGridMetrics gridMetrics = computeInventoryGridMetrics(
                    resolvedInventoryGrid->x,
                    resolvedInventoryGrid->y,
                    resolvedInventoryGrid->width,
                    resolvedInventoryGrid->height,
                    resolvedInventoryGrid->scale);

                for (const InventoryItem &item : pCharacter->inventory)
                {
                    const ItemDefinition *pItemDefinition = context.itemTable()->get(item.objectDescriptionId);

                    if (pItemDefinition == nullptr || pItemDefinition->iconName.empty())
                    {
                        continue;
                    }

                    const std::optional<GameplayHudTextureHandle> itemTexture =
                        context.ensureHudTextureLoaded(pItemDefinition->iconName);

                    if (!itemTexture.has_value())
                    {
                        continue;
                    }

                    const float itemWidth = static_cast<float>(itemTexture->width) * gridMetrics.scale;
                    const float itemHeight = static_cast<float>(itemTexture->height) * gridMetrics.scale;
                    const InventoryItemScreenRect itemRect =
                        computeInventoryItemScreenRect(gridMetrics, item, itemWidth, itemHeight);
                    context.submitHudTexturedQuad(*itemTexture, itemRect.x, itemRect.y, itemRect.width, itemRect.height);

                    GameplayRenderedInspectableHudItem inspectableItem = {};
                    inspectableItem.objectDescriptionId = item.objectDescriptionId;
                    inspectableItem.hasItemState = true;
                    inspectableItem.itemState = item;
                    inspectableItem.sourceType =
                        context.isAdventurersInnCharacterSourceActive()
                            ? GameplayUiController::ItemInspectSourceType::None
                            : GameplayUiController::ItemInspectSourceType::Inventory;
                    inspectableItem.sourceMemberIndex = characterSourceIndex;
                    inspectableItem.sourceGridX = item.gridX;
                    inspectableItem.sourceGridY = item.gridY;
                    inspectableItem.textureName = pItemDefinition->iconName;
                    inspectableItem.x = itemRect.x;
                    inspectableItem.y = itemRect.y;
                    inspectableItem.width = itemRect.width;
                    inspectableItem.height = itemRect.height;
                    context.addRenderedInspectableHudItem(inspectableItem);
                }
            }
        }
    }

    const bool isInventorySpellTargetMode =
        context.utilitySpellOverlayReadOnly().active
        && context.utilitySpellOverlayReadOnly().mode == GameplayUiController::UtilitySpellOverlayMode::InventoryTarget
        && characterScreen.page == GameplayUiController::CharacterPage::Inventory
        && pCharacter != nullptr;

    if (renderAboveHud && isInventorySpellTargetMode)
    {
        const uint32_t pickerColor = makeAbgrColor(255, 255, 155);
        const uint32_t shadowColor = 0xc0000000u;
        const float overlayScale = std::clamp(baseScale, 0.75f, 2.0f);
        const GameplayRenderedInspectableHudItem *pHoveredItem = nullptr;

        for (auto it = context.renderedInspectableHudItems().rbegin();
             it != context.renderedInspectableHudItems().rend();
             ++it)
        {
            if (it->sourceMemberIndex != characterSourceIndex)
            {
                continue;
            }

            if (it->sourceType != GameplayUiController::ItemInspectSourceType::Inventory
                && it->sourceType != GameplayUiController::ItemInspectSourceType::Equipment)
            {
                continue;
            }

            const bool isHovered =
                it->sourceType == GameplayUiController::ItemInspectSourceType::Equipment
                    ? context.isOpaqueHudPixelAtPoint(*it, characterMouseX, characterMouseY)
                    : characterMouseX >= it->x
                        && characterMouseX < it->x + it->width
                        && characterMouseY >= it->y
                        && characterMouseY < it->y + it->height;

            if (isHovered)
            {
                pHoveredItem = &*it;
                break;
            }
        }

        if (pHoveredItem != nullptr)
        {
            renderInventoryTargetFrame(
                pHoveredItem->x,
                pHoveredItem->y,
                pHoveredItem->width,
                pHoveredItem->height,
                overlayScale,
                pickerColor,
                shadowColor);
        }

        renderInventoryTargetCrosshair(
            characterMouseX,
            characterMouseY,
            overlayScale,
            pickerColor,
            shadowColor);

        UiLayoutManager::LayoutElement promptLayout = {};
        promptLayout.fontName = "arrus";
        promptLayout.textColorAbgr = pickerColor;
        promptLayout.textAlignX = UiLayoutManager::TextAlignX::Center;
        promptLayout.textAlignY = UiLayoutManager::TextAlignY::Top;
        GameplayResolvedHudLayoutElement promptRect = {};
        promptRect.x = uiViewport.x;
        promptRect.y = uiViewport.y + std::round(18.0f * overlayScale);
        promptRect.width = uiViewport.width;
        promptRect.height = std::round(24.0f * overlayScale);
        promptRect.scale = overlayScale;
        context.renderLayoutLabel(promptLayout, promptRect, "Select item target  LMB cast  Esc cancel");
    }

    const auto renderSkillGroup =
        [&context, width, height, &hasVisibleCharacterAncestors, &shouldRenderInCurrentPass, skillRowHeight](
            const char *pRegionId,
            const char *pLevelHeaderId,
            const std::vector<CharacterSkillUiRow> &rows)
        {
            const UiLayoutManager::LayoutElement *pRegionLayout = context.findHudLayoutElement(pRegionId);
            const UiLayoutManager::LayoutElement *pLevelLayout = context.findHudLayoutElement(pLevelHeaderId);

            if (pRegionLayout == nullptr
                || pLevelLayout == nullptr
                || !hasVisibleCharacterAncestors(*pRegionLayout)
                || !hasVisibleCharacterAncestors(*pLevelLayout)
                || !shouldRenderInCurrentPass(pRegionLayout->zIndex))
            {
                return;
            }

            const std::optional<GameplayResolvedHudLayoutElement> resolvedRegion =
                context.resolveHudLayoutElement(pRegionId, width, height, pRegionLayout->width, pRegionLayout->height);
            const std::optional<GameplayResolvedHudLayoutElement> resolvedLevelHeader =
                context.resolveHudLayoutElement(pLevelHeaderId, width, height, pLevelLayout->width, pLevelLayout->height);

            if (!resolvedRegion.has_value() || !resolvedLevelHeader.has_value())
            {
                return;
            }

            const float rowHeightPixels = skillRowHeight * resolvedRegion->scale;
            const float nameWidth =
                std::max(0.0f, resolvedLevelHeader->x - resolvedRegion->x - 6.0f * resolvedRegion->scale);
            const std::vector<CharacterSkillUiRow> displayRows =
                rows.empty() ? std::vector<CharacterSkillUiRow>{{"", "None", "", false}} : rows;

            for (size_t rowIndex = 0; rowIndex < displayRows.size(); ++rowIndex)
            {
                const CharacterSkillUiRow &row = displayRows[rowIndex];
                const uint32_t textColorAbgr = row.upgradeable ? 0xffff784au : 0xffffffffu;

                UiLayoutManager::LayoutElement nameLayout = {};
                nameLayout.fontName = "Lucida";
                nameLayout.textColorAbgr = textColorAbgr;
                nameLayout.textAlignX = UiLayoutManager::TextAlignX::Left;
                nameLayout.textAlignY = UiLayoutManager::TextAlignY::Middle;
                GameplayResolvedHudLayoutElement nameResolved = {};
                nameResolved.x = resolvedRegion->x;
                nameResolved.y = resolvedRegion->y + static_cast<float>(rowIndex) * rowHeightPixels;
                nameResolved.width = nameWidth;
                nameResolved.height = rowHeightPixels;
                nameResolved.scale = resolvedRegion->scale;
                context.renderLayoutLabel(nameLayout, nameResolved, row.label);

                if (!row.level.empty())
                {
                    UiLayoutManager::LayoutElement levelLayout = {};
                    levelLayout.fontName = "Lucida";
                    levelLayout.textColorAbgr = textColorAbgr;
                    levelLayout.textAlignX = UiLayoutManager::TextAlignX::Right;
                    levelLayout.textAlignY = UiLayoutManager::TextAlignY::Middle;
                    GameplayResolvedHudLayoutElement levelResolved = {};
                    levelResolved.x = resolvedLevelHeader->x;
                    levelResolved.y = nameResolved.y;
                    levelResolved.width = resolvedLevelHeader->width;
                    levelResolved.height = rowHeightPixels;
                    levelResolved.scale = resolvedLevelHeader->scale;
                    context.renderLayoutLabel(levelLayout, levelResolved, row.level);
                }
            }
        };

    renderSkillGroup("CharacterSkillsWeaponsListRegion", "CharacterSkillsWeaponsLevelHeader", skillUiData.weaponRows);
    renderSkillGroup("CharacterSkillsMagicListRegion", "CharacterSkillsMagicLevelHeader", skillUiData.magicRows);
    renderSkillGroup("CharacterSkillsArmorListRegion", "CharacterSkillsArmorLevelHeader", skillUiData.armorRows);
    renderSkillGroup("CharacterSkillsMiscListRegion", "CharacterSkillsMiscLevelHeader", skillUiData.miscRows);
}

void GameplayPartyOverlayRenderer::renderCharacterOverlay(
    const OutdoorGameView &view,
    int width,
    int height,
    bool renderAboveHud)
{
    if (view.currentHudScreenState() != OutdoorGameView::HudScreenState::Character
        || view.m_pOutdoorPartyRuntime == nullptr
        || !bgfx::isValid(view.m_texturedTerrainProgramHandle)
        || !bgfx::isValid(view.m_terrainTextureSamplerHandle)
        || width <= 0
        || height <= 0)
    {
        return;
    }

    OutdoorGameView &mutableView = const_cast<OutdoorGameView &>(view);
    GameplayOverlayContext overlayContext = mutableView.createGameplayOverlayContext();
    setupHudProjection(width, height);
    renderViewportParchmentSidePanels(view, width, height);

    const UiViewportRect uiViewport = computeUiViewportRect(width, height);
    const float baseScale = std::min(uiViewport.width / HudReferenceWidth, uiViewport.height / HudReferenceHeight);
    float characterMouseX = 0.0f;
    float characterMouseY = 0.0f;
    const SDL_MouseButtonFlags characterMouseButtons = SDL_GetMouseState(&characterMouseX, &characterMouseY);
    const bool isLeftMousePressed = (characterMouseButtons & SDL_BUTTON_LMASK) != 0;

    const auto replaceAll = [](std::string text, const std::string &from, const std::string &to) -> std::string
    {
        size_t position = 0;

        while ((position = text.find(from, position)) != std::string::npos)
        {
            text.replace(position, from.size(), to);
            position += to.size();
        }

        return text;
    };
    const auto submitSolidHudQuad =
        [&view](const std::string &textureName, float x, float y, float quadWidth, float quadHeight, uint32_t abgr)
        {
            if (quadWidth <= 0.0f || quadHeight <= 0.0f)
            {
                return;
            }

            const OutdoorGameView::HudTextureHandle *pSolidTexture =
                HudUiService::ensureSolidHudTextureLoaded(
                    const_cast<OutdoorGameView &>(view),
                    textureName,
                    abgr);

            if (pSolidTexture == nullptr)
            {
                return;
            }

            view.submitHudTexturedQuad(*pSolidTexture, x, y, quadWidth, quadHeight);
        };
    const auto renderInventoryTargetCrosshair =
        [&submitSolidHudQuad](float centerX, float centerY, float overlayScale, uint32_t crosshairColor, uint32_t shadowColor)
        {
            const float armLength = std::round(10.0f * overlayScale);
            const float armGap = std::round(4.0f * overlayScale);
            const float stroke = std::max(1.0f, std::round(2.0f * overlayScale));
            const auto submitCrosshairLine =
                [&submitSolidHudQuad, crosshairColor, shadowColor](float x, float y, float quadWidth, float quadHeight)
                {
                    submitSolidHudQuad(
                        "__inventory_target_crosshair_shadow__",
                        x + 1.0f,
                        y + 1.0f,
                        quadWidth,
                        quadHeight,
                        shadowColor);
                    submitSolidHudQuad(
                        "__inventory_target_crosshair__",
                        x,
                        y,
                        quadWidth,
                        quadHeight,
                        crosshairColor);
                };

            submitCrosshairLine(centerX - armGap - armLength, centerY - stroke * 0.5f, armLength, stroke);
            submitCrosshairLine(centerX + armGap, centerY - stroke * 0.5f, armLength, stroke);
            submitCrosshairLine(centerX - stroke * 0.5f, centerY - armGap - armLength, stroke, armLength);
            submitCrosshairLine(centerX - stroke * 0.5f, centerY + armGap, stroke, armLength);
        };
    const auto renderInventoryTargetFrame =
        [&submitSolidHudQuad](float x, float y, float rectWidth, float rectHeight, float overlayScale, uint32_t frameColor, uint32_t shadowColor)
        {
            const float thickness = std::max(1.0f, std::round(2.0f * overlayScale));
            const auto submitFrameQuad =
                [&submitSolidHudQuad, frameColor, shadowColor](
                    float quadX,
                    float quadY,
                    float quadWidth,
                    float quadHeight)
                {
                    submitSolidHudQuad(
                        "__inventory_target_frame_shadow__",
                        quadX + 1.0f,
                        quadY + 1.0f,
                        quadWidth,
                        quadHeight,
                        shadowColor);
                    submitSolidHudQuad(
                        "__inventory_target_frame__",
                        quadX,
                        quadY,
                        quadWidth,
                        quadHeight,
                        frameColor);
                };

            submitFrameQuad(x - thickness, y - thickness, rectWidth + thickness * 2.0f, thickness);
            submitFrameQuad(x - thickness, y + rectHeight, rectWidth + thickness * 2.0f, thickness);
            submitFrameQuad(x - thickness, y, thickness, rectHeight);
            submitFrameQuad(x + rectWidth, y, thickness, rectHeight);
        };

    const std::string activePageRootId =
        view.m_characterPage == OutdoorGameView::CharacterPage::Stats
            ? "characterstatspage"
            : (view.m_characterPage == OutdoorGameView::CharacterPage::Skills
                ? "characterskillspage"
                : (view.m_characterPage == OutdoorGameView::CharacterPage::Inventory
                    ? "characterinventorypage"
                    : "characterawardspage"));
    std::unordered_map<std::string, bool> visibleCharacterAncestorCache;
    std::function<bool(const OutdoorGameView::HudLayoutElement &)> hasVisibleCharacterAncestors;
    hasVisibleCharacterAncestors =
        [&view, &activePageRootId, &visibleCharacterAncestorCache, &hasVisibleCharacterAncestors](
            const OutdoorGameView::HudLayoutElement &layout) -> bool
        {
            const std::string normalizedId = toLowerCopy(layout.id);
            const auto cachedIterator = visibleCharacterAncestorCache.find(normalizedId);

            if (cachedIterator != visibleCharacterAncestorCache.end())
            {
                return cachedIterator->second;
            }

            bool result = layout.visible && toLowerCopy(layout.screen) == "character";

            if (result
                && (normalizedId == "characterstatspage"
                    || normalizedId == "characterskillspage"
                    || normalizedId == "characterinventorypage"
                    || normalizedId == "characterawardspage"))
            {
                result = normalizedId == activePageRootId;
            }

            if (result && !layout.parentId.empty())
            {
                const OutdoorGameView::HudLayoutElement *pParent = HudUiService::findHudLayoutElement(view, layout.parentId);
                result = pParent != nullptr && hasVisibleCharacterAncestors(*pParent);
            }

            visibleCharacterAncestorCache[normalizedId] = result;
            return result;
        };

    const Party &party = view.m_pOutdoorPartyRuntime->party();
    const bool isAdventurersInnActive = overlayContext.isAdventurersInnScreenActive();
    const Character *pCharacter = overlayContext.selectedCharacterScreenCharacter();
    const std::vector<std::string> orderedCharacterLayoutIds = HudUiService::sortedHudLayoutIdsForScreen(view, "Character");
    const int hudZThreshold = HudUiService::defaultHudLayoutZIndexForScreen("OutdoorHud");
    const auto shouldRenderInCurrentPass =
        [renderAboveHud, hudZThreshold](int zIndex) -> bool
        {
            return renderAboveHud ? zIndex >= hudZThreshold : zIndex < hudZThreshold;
        };
    const size_t characterSourceIndex = overlayContext.selectedCharacterScreenSourceIndex();
    const auto formatPair = [](int actualValue, int baseValue) -> std::string
    {
        return std::to_string(actualValue) + " / " + std::to_string(baseValue);
    };
    const auto formatSheetValue = [&formatPair](const CharacterSheetValue &value) -> std::string
    {
        if (value.infinite)
        {
            return "INF";
        }

        return formatPair(value.actual, value.base);
    };

    std::string mightValue = "0 / 0";
    std::string intellectValue = "0 / 0";
    std::string personalityValue = "0 / 0";
    std::string enduranceValue = "0 / 0";
    std::string accuracyValue = "0 / 0";
    std::string speedValue = "0 / 0";
    std::string luckValue = "0 / 0";
    std::string hitPointsValue = "0 / 0";
    std::string spellPointsValue = "0 / 0";
    std::string armorClassValue = "0 / 0";
    std::string conditionValue = "-";
    std::string quickSpellValue = "-";
    std::string ageValue = "-";
    std::string levelValue = "0 / 0";
    std::string experienceValue = "-";
    std::string attackValue = "-";
    std::string meleeDamageValue = "-";
    std::string shootValue = "-";
    std::string rangedDamageValue = "-";
    std::string fireResistanceValue = "0 / 0";
    std::string airResistanceValue = "0 / 0";
    std::string waterResistanceValue = "0 / 0";
    std::string earthResistanceValue = "0 / 0";
    std::string mindResistanceValue = "0 / 0";
    std::string bodyResistanceValue = "0 / 0";
    std::string awards;
    std::string inventoryInfo;
    std::string adventurersInnBlurb;
    bool canTrainToNextLevel = false;
    CharacterSheetSummary summary = {};
    const OutdoorGameView::HudFontHandle *pSkillRowFont = HudUiService::findHudFont(view, "Lucida");
    const float skillRowHeight =
        pSkillRowFont != nullptr ? static_cast<float>(std::max(1, pSkillRowFont->fontHeight - 3)) : 11.0f;
    const CharacterDollEntry *pCharacterDollEntry = resolveCharacterDollEntry(view.m_pCharacterDollTable, pCharacter);
    const CharacterDollTypeEntry *pCharacterDollType =
        pCharacterDollEntry != nullptr && view.m_pCharacterDollTable != nullptr
            ? view.m_pCharacterDollTable->getDollType(pCharacterDollEntry->dollTypeId)
            : nullptr;

    if (pCharacter != nullptr)
    {
        summary = GameMechanics::buildCharacterSheetSummary(
            *pCharacter,
            view.m_pItemTable,
            view.m_pStandardItemEnchantTable,
            view.m_pSpecialItemEnchantTable);
        mightValue = formatSheetValue(summary.might);
        intellectValue = formatSheetValue(summary.intellect);
        personalityValue = formatSheetValue(summary.personality);
        enduranceValue = formatSheetValue(summary.endurance);
        accuracyValue = formatSheetValue(summary.accuracy);
        speedValue = formatSheetValue(summary.speed);
        luckValue = formatSheetValue(summary.luck);
        hitPointsValue =
            std::to_string(summary.health.current) + " / " + std::to_string(summary.health.maximum);
        spellPointsValue =
            std::to_string(summary.spellPoints.current) + " / " + std::to_string(summary.spellPoints.maximum);
        armorClassValue = formatSheetValue(summary.armorClass);
        conditionValue = summary.conditionText;
        quickSpellValue = summary.quickSpellText;
        ageValue = summary.ageText;
        levelValue = formatSheetValue(summary.level);
        experienceValue = summary.experienceText;
        canTrainToNextLevel = summary.canTrainToNextLevel;
        attackValue = std::to_string(summary.combat.attack);
        meleeDamageValue = summary.combat.meleeDamageText;
        shootValue = summary.combat.shoot ? std::to_string(*summary.combat.shoot) : "N/A";
        rangedDamageValue = summary.combat.rangedDamageText;
        fireResistanceValue = formatSheetValue(summary.fireResistance);
        airResistanceValue = formatSheetValue(summary.airResistance);
        waterResistanceValue = formatSheetValue(summary.waterResistance);
        earthResistanceValue = formatSheetValue(summary.earthResistance);
        mindResistanceValue = formatSheetValue(summary.mindResistance);
        bodyResistanceValue = formatSheetValue(summary.bodyResistance);
        awards = "Awards earned: " + std::to_string(pCharacter->awards.size());

        if (view.m_pRosterTable != nullptr && pCharacter->rosterId != 0)
        {
            const RosterEntry *pRosterEntry = view.m_pRosterTable->get(pCharacter->rosterId);
            adventurersInnBlurb = pRosterEntry != nullptr ? pRosterEntry->blurb : "";
        }
    }

    const CharacterSkillUiData skillUiData = buildCharacterSkillUiData(pCharacter);
    mutableView.m_hudLayoutRuntimeHeightOverrides.clear();
    const uint32_t skillPointsValueColorAbgr =
        pCharacter != nullptr && pCharacter->skillPoints > 0 ? makeAbgrColor(0, 255, 0) : makeAbgrColor(255, 255, 255);
    const uint32_t experienceValueColorAbgr =
        pCharacter != nullptr && canTrainToNextLevel ? makeAbgrColor(0, 255, 0) : makeAbgrColor(255, 255, 255);

    setCharacterSkillRegionHeight(
        mutableView.m_hudLayoutRuntimeHeightOverrides,
        skillRowHeight,
        "CharacterSkillsWeaponsListRegion",
        skillUiData.weaponRows.size());
    setCharacterSkillRegionHeight(
        mutableView.m_hudLayoutRuntimeHeightOverrides,
        skillRowHeight,
        "CharacterSkillsMagicListRegion",
        skillUiData.magicRows.size());
    setCharacterSkillRegionHeight(
        mutableView.m_hudLayoutRuntimeHeightOverrides,
        skillRowHeight,
        "CharacterSkillsArmorListRegion",
        skillUiData.armorRows.size());
    setCharacterSkillRegionHeight(
        mutableView.m_hudLayoutRuntimeHeightOverrides,
        skillRowHeight,
        "CharacterSkillsMiscListRegion",
        skillUiData.miscRows.size());

    const auto submitCharacterDollLayer =
        [&view, &mutableView, uiViewport, baseScale](
            const OutdoorGameView::HudLayoutElement &layout,
            const OutdoorGameView::ResolvedHudLayoutElement &resolvedAnchor,
            const std::string &assetName,
            int offsetX,
            int offsetY,
            const char *pRenderKey = nullptr)
        {
            if (assetName.empty() || assetName == "none")
            {
                return;
            }

            const OutdoorGameView::HudTextureHandle *pTexture = HudUiService::ensureHudTextureLoaded(mutableView, assetName);

            if (pTexture == nullptr || pTexture->width <= 0 || pTexture->height <= 0)
            {
                return;
            }

            const float centerX = resolvedAnchor.x + resolvedAnchor.width * 0.5f;
            const float centerY = resolvedAnchor.y + resolvedAnchor.height * 0.5f;
            const float scale = resolvedAnchor.scale;
            const float layerWidth = static_cast<float>(pTexture->width) * scale;
            const float layerHeight = static_cast<float>(pTexture->height) * scale;
            float anchorX = centerX;
            float anchorY = centerY;
            const auto setAnchorPoint = [&](float normalizedX, float normalizedY)
            {
                anchorX = resolvedAnchor.x + resolvedAnchor.width * normalizedX;
                anchorY = resolvedAnchor.y + resolvedAnchor.height * normalizedY;
            };

            if (!layout.parentId.empty())
            {
                switch (layout.attachTo)
                {
                    case OutdoorGameView::HudLayoutAttachMode::None:
                    case OutdoorGameView::HudLayoutAttachMode::CenterIn:
                        setAnchorPoint(0.5f, 0.5f);
                        break;
                    case OutdoorGameView::HudLayoutAttachMode::RightOf:
                    case OutdoorGameView::HudLayoutAttachMode::Below:
                    case OutdoorGameView::HudLayoutAttachMode::InsideTopLeft:
                        setAnchorPoint(0.0f, 0.0f);
                        break;
                    case OutdoorGameView::HudLayoutAttachMode::LeftOf:
                    case OutdoorGameView::HudLayoutAttachMode::InsideTopRight:
                        setAnchorPoint(1.0f, 0.0f);
                        break;
                    case OutdoorGameView::HudLayoutAttachMode::Above:
                        setAnchorPoint(0.0f, 1.0f);
                        break;
                    case OutdoorGameView::HudLayoutAttachMode::CenterAbove:
                    case OutdoorGameView::HudLayoutAttachMode::InsideBottomCenter:
                        setAnchorPoint(0.5f, 1.0f);
                        break;
                    case OutdoorGameView::HudLayoutAttachMode::CenterBelow:
                    case OutdoorGameView::HudLayoutAttachMode::InsideTopCenter:
                        setAnchorPoint(0.5f, 0.0f);
                        break;
                    case OutdoorGameView::HudLayoutAttachMode::InsideLeft:
                        setAnchorPoint(0.0f, 0.5f);
                        break;
                    case OutdoorGameView::HudLayoutAttachMode::InsideRight:
                        setAnchorPoint(1.0f, 0.5f);
                        break;
                    case OutdoorGameView::HudLayoutAttachMode::InsideBottomLeft:
                        setAnchorPoint(0.0f, 1.0f);
                        break;
                    case OutdoorGameView::HudLayoutAttachMode::InsideBottomRight:
                        setAnchorPoint(1.0f, 1.0f);
                        break;
                }
            }
            else
            {
                switch (layout.anchor)
                {
                    case OutdoorGameView::HudLayoutAnchor::TopLeft:
                        setAnchorPoint(0.0f, 0.0f);
                        break;
                    case OutdoorGameView::HudLayoutAnchor::TopCenter:
                        setAnchorPoint(0.5f, 0.0f);
                        break;
                    case OutdoorGameView::HudLayoutAnchor::TopRight:
                        setAnchorPoint(1.0f, 0.0f);
                        break;
                    case OutdoorGameView::HudLayoutAnchor::Left:
                        setAnchorPoint(0.0f, 0.5f);
                        break;
                    case OutdoorGameView::HudLayoutAnchor::Center:
                        setAnchorPoint(0.5f, 0.5f);
                        break;
                    case OutdoorGameView::HudLayoutAnchor::Right:
                        setAnchorPoint(1.0f, 0.5f);
                        break;
                    case OutdoorGameView::HudLayoutAnchor::BottomLeft:
                        setAnchorPoint(0.0f, 1.0f);
                        break;
                    case OutdoorGameView::HudLayoutAnchor::BottomCenter:
                        setAnchorPoint(0.5f, 1.0f);
                        break;
                    case OutdoorGameView::HudLayoutAnchor::BottomRight:
                        setAnchorPoint(1.0f, 1.0f);
                        break;
                }
            }

            anchorX += static_cast<float>(offsetX) * scale;
            anchorY += static_cast<float>(offsetY) * scale;
            float layerX = std::round(anchorX - layerWidth * 0.5f);
            float layerY = std::round(anchorY - layerHeight * 0.5f);

            if (!layout.parentId.empty())
            {
                switch (layout.attachTo)
                {
                    case OutdoorGameView::HudLayoutAttachMode::RightOf:
                    case OutdoorGameView::HudLayoutAttachMode::Below:
                    case OutdoorGameView::HudLayoutAttachMode::InsideTopLeft:
                        layerX = std::round(anchorX);
                        layerY = std::round(anchorY);
                        break;

                    case OutdoorGameView::HudLayoutAttachMode::LeftOf:
                    case OutdoorGameView::HudLayoutAttachMode::InsideTopRight:
                        layerX = std::round(anchorX - layerWidth);
                        layerY = std::round(anchorY);
                        break;

                    case OutdoorGameView::HudLayoutAttachMode::Above:
                        layerX = std::round(anchorX);
                        layerY = std::round(anchorY - layerHeight);
                        break;

                    case OutdoorGameView::HudLayoutAttachMode::CenterAbove:
                        layerY = std::round(anchorY - layerHeight);
                        break;

                    case OutdoorGameView::HudLayoutAttachMode::CenterBelow:
                    case OutdoorGameView::HudLayoutAttachMode::InsideTopCenter:
                        layerY = std::round(anchorY);
                        break;

                    case OutdoorGameView::HudLayoutAttachMode::InsideLeft:
                        layerX = std::round(anchorX);
                        break;

                    case OutdoorGameView::HudLayoutAttachMode::InsideRight:
                        layerX = std::round(anchorX - layerWidth);
                        break;

                    case OutdoorGameView::HudLayoutAttachMode::InsideBottomLeft:
                        layerX = std::round(anchorX);
                        layerY = std::round(anchorY - layerHeight);
                        break;

                    case OutdoorGameView::HudLayoutAttachMode::InsideBottomCenter:
                        layerY = std::round(anchorY - layerHeight);
                        break;

                    case OutdoorGameView::HudLayoutAttachMode::InsideBottomRight:
                        layerX = std::round(anchorX - layerWidth);
                        layerY = std::round(anchorY - layerHeight);
                        break;

                    case OutdoorGameView::HudLayoutAttachMode::None:
                    case OutdoorGameView::HudLayoutAttachMode::CenterIn:
                        break;
                }
            }
            else
            {
                switch (layout.anchor)
                {
                    case OutdoorGameView::HudLayoutAnchor::TopLeft:
                        layerX = std::round(anchorX);
                        layerY = std::round(anchorY);
                        break;

                    case OutdoorGameView::HudLayoutAnchor::TopCenter:
                        layerY = std::round(anchorY);
                        break;

                    case OutdoorGameView::HudLayoutAnchor::TopRight:
                        layerX = std::round(anchorX - layerWidth);
                        layerY = std::round(anchorY);
                        break;

                    case OutdoorGameView::HudLayoutAnchor::Left:
                        layerX = std::round(anchorX);
                        break;

                    case OutdoorGameView::HudLayoutAnchor::Center:
                        break;

                    case OutdoorGameView::HudLayoutAnchor::Right:
                        layerX = std::round(anchorX - layerWidth);
                        break;

                    case OutdoorGameView::HudLayoutAnchor::BottomLeft:
                        layerX = std::round(anchorX);
                        layerY = std::round(anchorY - layerHeight);
                        break;

                    case OutdoorGameView::HudLayoutAnchor::BottomCenter:
                        layerY = std::round(anchorY - layerHeight);
                        break;

                    case OutdoorGameView::HudLayoutAnchor::BottomRight:
                        layerX = std::round(anchorX - layerWidth);
                        layerY = std::round(anchorY - layerHeight);
                        break;
                }
            }

            if (pRenderKey != nullptr)
            {
                logCharacterEquipmentRender(
                    pRenderKey,
                    layout.parentId,
                    assetName,
                    layerX,
                    layerY,
                    layerWidth,
                    layerHeight,
                    layout.zIndex,
                    baseScale > 0.0f ? (layerX - uiViewport.x) / baseScale : layerX,
                    baseScale > 0.0f ? (layerY - uiViewport.y) / baseScale : layerY,
                    baseScale > 0.0f ? layerWidth / baseScale : layerWidth,
                    baseScale > 0.0f ? layerHeight / baseScale : layerHeight);
            }

            view.submitHudTexturedQuad(*pTexture, layerX, layerY, layerWidth, layerHeight);
        };

    const auto getEquippedItemDefinition =
        [&view, pCharacter](EquipmentSlot slot) -> const ItemDefinition *
        {
            if (pCharacter == nullptr || view.m_pItemTable == nullptr)
            {
                return nullptr;
            }

            const uint32_t itemId = equippedItemId(pCharacter->equipment, slot);
            return itemId != 0 ? view.m_pItemTable->get(itemId) : nullptr;
        };
    const auto renderSplitCharacterStatLabel =
        [&view](
            const OutdoorGameView::HudLayoutElement &layout,
            const OutdoorGameView::ResolvedHudLayoutElement &resolved,
            const SplitCharacterStatValue &value)
        {
            const OutdoorGameView::HudFontHandle *pFont = HudUiService::findHudFont(view, layout.fontName);

            if (pFont == nullptr)
            {
                return;
            }

            float fontScale = resolved.scale * std::max(0.1f, layout.textScale);

            if (fontScale >= 1.0f)
            {
                fontScale = snappedHudFontScale(fontScale);
            }
            else
            {
                fontScale = std::max(0.5f, fontScale);
            }

            const std::string separatorText = " / ";
            const float actualWidth = HudUiService::measureHudTextWidth(view, *pFont, value.actualText) * fontScale;
            const float separatorWidth = HudUiService::measureHudTextWidth(view, *pFont, separatorText) * fontScale;
            const float baseWidth = HudUiService::measureHudTextWidth(view, *pFont, value.baseText) * fontScale;
            const float totalWidth = actualWidth + separatorWidth + baseWidth;
            const float labelHeightPixels = static_cast<float>(pFont->fontHeight) * fontScale;
            float textX = resolved.x + layout.textPadX * resolved.scale;
            float textY = resolved.y + layout.textPadY * resolved.scale;

            switch (layout.textAlignX)
            {
            case OutdoorGameView::HudTextAlignX::Left:
                break;

            case OutdoorGameView::HudTextAlignX::Center:
                textX = resolved.x + (resolved.width - totalWidth) * 0.5f + layout.textPadX * resolved.scale;
                break;

            case OutdoorGameView::HudTextAlignX::Right:
                textX = resolved.x + resolved.width - totalWidth + layout.textPadX * resolved.scale;
                break;
            }

            switch (layout.textAlignY)
            {
            case OutdoorGameView::HudTextAlignY::Top:
                break;

            case OutdoorGameView::HudTextAlignY::Middle:
                textY = resolved.y + (resolved.height - labelHeightPixels) * 0.5f + layout.textPadY * resolved.scale;
                break;

            case OutdoorGameView::HudTextAlignY::Bottom:
                textY = resolved.y + resolved.height - labelHeightPixels + layout.textPadY * resolved.scale;
                break;
            }

            textX = std::round(textX);
            textY = std::round(textY);

            bgfx::TextureHandle actualTexture =
                HudUiService::ensureHudFontMainTextureColor(view, *pFont, value.actualColorAbgr);
            bgfx::TextureHandle baseTexture =
                HudUiService::ensureHudFontMainTextureColor(view, *pFont, layout.textColorAbgr);

            if (!bgfx::isValid(actualTexture))
            {
                actualTexture = pFont->mainTextureHandle;
            }

            if (!bgfx::isValid(baseTexture))
            {
                baseTexture = pFont->mainTextureHandle;
            }

            HudUiService::renderHudFontLayer(
                view,
                *pFont,
                pFont->shadowTextureHandle,
                value.actualText,
                textX,
                textY,
                fontScale);
            HudUiService::renderHudFontLayer(view, *pFont, actualTexture, value.actualText, textX, textY, fontScale);
            textX += actualWidth;
            HudUiService::renderHudFontLayer(
                view,
                *pFont,
                pFont->shadowTextureHandle,
                separatorText,
                textX,
                textY,
                fontScale);
            HudUiService::renderHudFontLayer(view, *pFont, baseTexture, separatorText, textX, textY, fontScale);
            textX += separatorWidth;
            HudUiService::renderHudFontLayer(
                view,
                *pFont,
                pFont->shadowTextureHandle,
                value.baseText,
                textX,
                textY,
                fontScale);
            HudUiService::renderHudFontLayer(view, *pFont, baseTexture, value.baseText, textX, textY, fontScale);
        };

    const ItemDefinition *pMainHandItem = getEquippedItemDefinition(EquipmentSlot::MainHand);
    const ItemDefinition *pOffHandItem = getEquippedItemDefinition(EquipmentSlot::OffHand);
    SkillMastery spearMastery = SkillMastery::None;

    if (pCharacter != nullptr)
    {
        const CharacterSkill *pSpearSkill = pCharacter->findSkill("Spear");

        if (pSpearSkill != nullptr)
        {
            spearMastery = pSpearSkill->mastery;
        }
    }

    const bool leftHandDisabled =
        pMainHandItem != nullptr
        && (pMainHandItem->equipStat == "Weapon2"
            || (canonicalSkillName(pMainHandItem->skillGroup) == "Spear" && spearMastery < SkillMastery::Master));

    struct CharacterLayoutPassEntry
    {
        const OutdoorGameView::HudLayoutElement *pLayout = nullptr;
        std::string normalizedId;
        OutdoorGameView::ResolvedHudLayoutElement resolved;
    };

    std::vector<CharacterLayoutPassEntry> characterLayoutPassEntries;
    characterLayoutPassEntries.reserve(orderedCharacterLayoutIds.size());

    for (const std::string &layoutId : orderedCharacterLayoutIds)
    {
        const OutdoorGameView::HudLayoutElement *pLayout = HudUiService::findHudLayoutElement(view, layoutId);

        if (pLayout == nullptr || !hasVisibleCharacterAncestors(*pLayout) || !shouldRenderInCurrentPass(pLayout->zIndex))
        {
            continue;
        }

        const std::optional<OutdoorGameView::ResolvedHudLayoutElement> resolved =
            HudUiService::resolveHudLayoutElement(
                view,
                pLayout->id,
                width,
                height,
                pLayout->width,
                pLayout->height);

        if (!resolved)
        {
            continue;
        }

        const std::string normalizedLayoutId = toLowerCopy(pLayout->id);

        if (isAdventurersInnActive && !shouldRenderCharacterLayoutInAdventurersInn(normalizedLayoutId))
        {
            continue;
        }

        if (normalizedLayoutId.starts_with("adventurersinn"))
        {
            if (!isAdventurersInnActive)
            {
                continue;
            }

            if (normalizedLayoutId == "adventurersinnhirebutton" && party.isFull())
            {
                continue;
            }
        }

        if (normalizedLayoutId == "characterdismissbutton"
            && (overlayContext.isAdventurersInnCharacterSourceActive() || party.activeMemberIndex() == 0))
        {
            continue;
        }

        if (normalizedLayoutId == "characterdolljewelryoverlaypanel" && !view.m_characterDollJewelryOverlayOpen)
        {
            continue;
        }

        if (isAdventurersInnActive && normalizedLayoutId == "charactermagnifybutton")
        {
            continue;
        }

        CharacterLayoutPassEntry entry = {};
        entry.pLayout = pLayout;
        entry.normalizedId = normalizedLayoutId;
        entry.resolved = *resolved;
        characterLayoutPassEntries.push_back(std::move(entry));
    }

    for (const CharacterLayoutPassEntry &entry : characterLayoutPassEntries)
    {
        const OutdoorGameView::HudLayoutElement *pLayout = entry.pLayout;
        const OutdoorGameView::ResolvedHudLayoutElement &resolved = entry.resolved;
        const std::string &normalizedLayoutId = entry.normalizedId;

        if (normalizedLayoutId == "characterdollbackground")
        {
            std::string assetName = pLayout->primaryAsset;

            if (pCharacterDollEntry != nullptr
                && !pCharacterDollEntry->backgroundAsset.empty()
                && pCharacterDollEntry->backgroundAsset != "none")
            {
                const OutdoorGameView::HudTextureHandle *pBackgroundTexture =
                    HudUiService::ensureHudTextureLoaded(mutableView, pCharacterDollEntry->backgroundAsset);

                if (pBackgroundTexture != nullptr)
                {
                    assetName = pCharacterDollEntry->backgroundAsset;
                }
            }

            if (!assetName.empty())
            {
                const OutdoorGameView::HudTextureHandle *pTexture = HudUiService::ensureHudTextureLoaded(mutableView, assetName);

                if (pTexture != nullptr)
                {
                    view.submitHudTexturedQuad(*pTexture, resolved.x, resolved.y, resolved.width, resolved.height);
                }
            }

            continue;
        }

        if (normalizedLayoutId == "characterdollbody" && pCharacterDollEntry != nullptr)
        {
            submitCharacterDollLayer(
                *pLayout,
                resolved,
                pCharacterDollEntry->bodyAsset,
                pCharacterDollEntry->bodyOffsetX,
                pCharacterDollEntry->bodyOffsetY);
            continue;
        }

        if (normalizedLayoutId == "characterdollrighthand"
            && pCharacterDollEntry != nullptr
            && pCharacterDollType != nullptr)
        {
            submitCharacterDollLayer(
                *pLayout,
                resolved,
                pMainHandItem != nullptr ? pCharacterDollEntry->rightHandHoldAsset : pCharacterDollEntry->rightHandOpenAsset,
                pMainHandItem != nullptr ? pCharacterDollType->rightHandClosedX : pCharacterDollType->rightHandOpenX,
                pMainHandItem != nullptr ? pCharacterDollType->rightHandClosedY : pCharacterDollType->rightHandOpenY);
            continue;
        }

        if (normalizedLayoutId == "characterdolllefthand"
            && pCharacterDollEntry != nullptr
            && pCharacterDollType != nullptr)
        {
            if (pOffHandItem != nullptr)
            {
                submitCharacterDollLayer(
                    *pLayout,
                    resolved,
                    pCharacterDollEntry->leftHandHoldAsset,
                    pCharacterDollType->leftHandOpenX,
                    pCharacterDollType->leftHandOpenY);
            }
            else if (leftHandDisabled)
            {
                submitCharacterDollLayer(
                    *pLayout,
                    resolved,
                    pCharacterDollEntry->leftHandClosedAsset,
                    pCharacterDollType->leftHandClosedX,
                    pCharacterDollType->leftHandClosedY);
            }
            else
            {
                submitCharacterDollLayer(
                    *pLayout,
                    resolved,
                    pCharacterDollEntry->leftHandOpenAsset,
                    pCharacterDollType->leftHandFingersX,
                    pCharacterDollType->leftHandFingersY);
            }
            continue;
        }

        if (normalizedLayoutId == "characterdollrighthandfingers"
            && pCharacterDollEntry != nullptr
            && pCharacterDollType != nullptr
            && getEquippedItemDefinition(EquipmentSlot::MainHand) != nullptr)
        {
            submitCharacterDollLayer(
                *pLayout,
                resolved,
                pCharacterDollEntry->rightHandFingersAsset,
                pCharacterDollType->rightHandFingersX,
                pCharacterDollType->rightHandFingersY);
            continue;
        }

        if (normalizedLayoutId == "characterpaperdollregion"
            && pCharacter != nullptr
            && !pCharacter->portraitTextureName.empty())
        {
            const std::string portraitTextureName = view.resolvePortraitTextureName(*pCharacter);
            const OutdoorGameView::HudTextureHandle *pPortraitTexture = HudUiService::ensureHudTextureLoaded(mutableView, portraitTextureName);

            if (pPortraitTexture != nullptr && pPortraitTexture->width > 0 && pPortraitTexture->height > 0)
            {
                const float scale = std::min(
                    resolved.width / static_cast<float>(pPortraitTexture->width),
                    resolved.height / static_cast<float>(pPortraitTexture->height));
                const float portraitWidth = static_cast<float>(pPortraitTexture->width) * scale;
                const float portraitHeight = static_cast<float>(pPortraitTexture->height) * scale;
                const float portraitX = resolved.x + (resolved.width - portraitWidth) * 0.5f;
                const float portraitY = resolved.y + (resolved.height - portraitHeight) * 0.5f;
                view.submitHudTexturedQuad(*pPortraitTexture, portraitX, portraitY, portraitWidth, portraitHeight);
            }
        }

        const std::string *pAssetName =
            HudUiService::resolveInteractiveAssetName(*pLayout, resolved, characterMouseX, characterMouseY, isLeftMousePressed);

        if (!pAssetName->empty())
        {
            const OutdoorGameView::HudTextureHandle *pTexture = HudUiService::ensureHudTextureLoaded(mutableView, *pAssetName);

            if (pTexture != nullptr)
            {
                view.submitHudTexturedQuad(*pTexture, resolved.x, resolved.y, resolved.width, resolved.height);
            }
        }

        const std::optional<EquipmentSlot> slot = characterEquipmentSlotForLayoutId(pLayout->id);

        if (slot && isVisibleInCharacterDollOverlay(*slot, view.m_characterDollJewelryOverlayOpen))
        {
            const ItemDefinition *pItemDefinition = getEquippedItemDefinition(*slot);

            if (pItemDefinition != nullptr && !pItemDefinition->iconName.empty())
            {
                const bool hasRightHandWeapon = pCharacter != nullptr && pCharacter->equipment.mainHand != 0;
                const uint32_t dollTypeId = pCharacterDollType != nullptr ? pCharacterDollType->id : 0;
                const std::string textureName =
                    overlayContext.resolveEquippedItemHudTextureName(*pItemDefinition, dollTypeId, hasRightHandWeapon, *slot);
                const OutdoorGameView::HudTextureHandle *pTexture = HudUiService::ensureHudTextureLoaded(mutableView, textureName);

                if (pTexture != nullptr)
                {
                    const std::optional<OutdoorGameView::ResolvedHudLayoutElement> iconRect =
                        overlayContext.resolveCharacterEquipmentRenderRect(
                            *pLayout,
                            *pItemDefinition,
                            GameplayHudTextureHandle{
                                .textureName = pTexture->textureName,
                                .width = pTexture->width,
                                .height = pTexture->height,
                                .textureHandle = pTexture->textureHandle
                            },
                            pCharacterDollType,
                            *slot,
                            width,
                            height);

                    if (iconRect)
                    {
                        logCharacterEquipmentRender(
                            "slot." + std::string(equipmentSlotName(*slot)),
                            pLayout->parentId,
                            textureName,
                            iconRect->x,
                            iconRect->y,
                            iconRect->width,
                            iconRect->height,
                            pLayout->zIndex,
                            baseScale > 0.0f ? (iconRect->x - uiViewport.x) / baseScale : iconRect->x,
                            baseScale > 0.0f ? (iconRect->y - uiViewport.y) / baseScale : iconRect->y,
                            baseScale > 0.0f ? iconRect->width / baseScale : iconRect->width,
                            baseScale > 0.0f ? iconRect->height / baseScale : iconRect->height);
                        const std::optional<InventoryItem> equippedItemState =
                            !overlayContext.isAdventurersInnCharacterSourceActive() && view.m_pOutdoorPartyRuntime != nullptr
                                ? view.m_pOutdoorPartyRuntime->party().equippedItem(
                                    view.m_pOutdoorPartyRuntime->party().activeMemberIndex(),
                                    *slot)
                                : std::nullopt;
                        view.submitHudTexturedQuad(*pTexture, iconRect->x, iconRect->y, iconRect->width, iconRect->height);

                        const bgfx::TextureHandle tintedTextureHandle = HudUiService::ensureHudTextureColor(mutableView, 
                            *pTexture,
                            itemTintColorAbgr(
                                equippedItemState.has_value() ? &*equippedItemState : nullptr,
                                pItemDefinition,
                                ItemTintContext::Equipped));

                        if (bgfx::isValid(tintedTextureHandle) && tintedTextureHandle.idx != pTexture->textureHandle.idx)
                        {
                            OutdoorGameView::HudTextureHandle tintedTexture = *pTexture;
                            tintedTexture.textureHandle = tintedTextureHandle;
                            view.submitHudTexturedQuad(tintedTexture, iconRect->x, iconRect->y, iconRect->width, iconRect->height);
                        }

                        if (pItemDefinition->itemId != 0)
                        {
                            OutdoorGameView::RenderedInspectableHudItem inspectableItem = {};
                            inspectableItem.objectDescriptionId = pItemDefinition->itemId;

                            if (equippedItemState.has_value())
                            {
                                inspectableItem.hasItemState = true;
                                inspectableItem.itemState = *equippedItemState;
                            }

                            inspectableItem.sourceType =
                                overlayContext.isAdventurersInnCharacterSourceActive()
                                    ? OutdoorGameView::ItemInspectSourceType::None
                                    : OutdoorGameView::ItemInspectSourceType::Equipment;
                            inspectableItem.sourceMemberIndex = characterSourceIndex;
                            inspectableItem.equipmentSlot = *slot;
                            inspectableItem.textureName = textureName;
                            inspectableItem.x = iconRect->x;
                            inspectableItem.y = iconRect->y;
                            inspectableItem.width = iconRect->width;
                            inspectableItem.height = iconRect->height;
                            view.m_renderedInspectableHudItems.push_back(std::move(inspectableItem));
                        }
                    }
                }
            }
        }
    }

    if (!isAdventurersInnActive
        && view.m_characterPage == OutdoorGameView::CharacterPage::Inventory
        && pCharacter != nullptr)
    {
        const OutdoorGameView::HudLayoutElement *pInventoryGridLayout = HudUiService::findHudLayoutElement(view, "CharacterInventoryGrid");
        const std::optional<OutdoorGameView::ResolvedHudLayoutElement> resolvedInventoryGrid =
            pInventoryGridLayout != nullptr
                ? HudUiService::resolveHudLayoutElement(view, 
                    "CharacterInventoryGrid",
                    width,
                    height,
                    pInventoryGridLayout->width,
                    pInventoryGridLayout->height)
                : std::nullopt;

        if (resolvedInventoryGrid)
        {
            const InventoryGridMetrics gridMetrics = computeInventoryGridMetrics(
                resolvedInventoryGrid->x,
                resolvedInventoryGrid->y,
                resolvedInventoryGrid->width,
                resolvedInventoryGrid->height,
                resolvedInventoryGrid->scale);

            for (const InventoryItem &item : pCharacter->inventory)
            {
                const ItemDefinition *pItemDefinition =
                    view.m_pItemTable != nullptr ? view.m_pItemTable->get(item.objectDescriptionId) : nullptr;

                if (pItemDefinition == nullptr || pItemDefinition->iconName.empty())
                {
                    continue;
                }

                const OutdoorGameView::HudTextureHandle *pItemTexture =
                    HudUiService::ensureHudTextureLoaded(mutableView, pItemDefinition->iconName);

                if (pItemTexture == nullptr)
                {
                    continue;
                }

                const float itemWidth = static_cast<float>(pItemTexture->width) * gridMetrics.scale;
                const float itemHeight = static_cast<float>(pItemTexture->height) * gridMetrics.scale;
                const InventoryItemScreenRect itemRect =
                    computeInventoryItemScreenRect(gridMetrics, item, itemWidth, itemHeight);
                view.submitHudTexturedQuad(*pItemTexture, itemRect.x, itemRect.y, itemRect.width, itemRect.height);

                if (pItemDefinition->itemId != 0)
                {
                    OutdoorGameView::RenderedInspectableHudItem inspectableItem = {};
                    inspectableItem.objectDescriptionId = pItemDefinition->itemId;
                    inspectableItem.hasItemState = true;
                    inspectableItem.itemState = item;
                    inspectableItem.sourceType =
                        overlayContext.isAdventurersInnCharacterSourceActive()
                            ? OutdoorGameView::ItemInspectSourceType::None
                            : OutdoorGameView::ItemInspectSourceType::Inventory;
                    inspectableItem.sourceMemberIndex = characterSourceIndex;
                    inspectableItem.sourceGridX = item.gridX;
                    inspectableItem.sourceGridY = item.gridY;
                    inspectableItem.textureName = pItemDefinition->iconName;
                    inspectableItem.x = itemRect.x;
                    inspectableItem.y = itemRect.y;
                    inspectableItem.width = itemRect.width;
                    inspectableItem.height = itemRect.height;
                    view.m_renderedInspectableHudItems.push_back(std::move(inspectableItem));
                }
            }
        }
    }

    const bool isInventorySpellTargetMode =
        view.m_utilitySpellOverlay.active
        && view.m_utilitySpellOverlay.mode == OutdoorGameView::UtilitySpellOverlayMode::InventoryTarget
        && view.m_characterPage == OutdoorGameView::CharacterPage::Inventory
        && pCharacter != nullptr;

    if (renderAboveHud && isInventorySpellTargetMode)
    {
        const uint32_t pickerColor = makeAbgrColor(255, 255, 155);
        const uint32_t shadowColor = 0xc0000000u;
        const float overlayScale = std::clamp(baseScale, 0.75f, 2.0f);
        float pickerCenterX = characterMouseX;
        float pickerCenterY = characterMouseY;
        const OutdoorGameView::RenderedInspectableHudItem *pHoveredItem = nullptr;

        for (auto it = view.m_renderedInspectableHudItems.rbegin(); it != view.m_renderedInspectableHudItems.rend(); ++it)
        {
            if (it->sourceMemberIndex != characterSourceIndex)
            {
                continue;
            }

            if (it->sourceType != OutdoorGameView::ItemInspectSourceType::Inventory
                && it->sourceType != OutdoorGameView::ItemInspectSourceType::Equipment)
            {
                continue;
            }

            const bool isHovered =
                it->sourceType == OutdoorGameView::ItemInspectSourceType::Equipment
                    ? view.isOpaqueHudPixelAtPoint(*it, characterMouseX, characterMouseY)
                    : characterMouseX >= it->x
                        && characterMouseX < it->x + it->width
                        && characterMouseY >= it->y
                        && characterMouseY < it->y + it->height;

            if (!isHovered)
            {
                continue;
            }

            pHoveredItem = &*it;
            break;
        }

        if (pHoveredItem != nullptr)
        {
            renderInventoryTargetFrame(
                pHoveredItem->x,
                pHoveredItem->y,
                pHoveredItem->width,
                pHoveredItem->height,
                overlayScale,
                pickerColor,
                shadowColor);
        }

        renderInventoryTargetCrosshair(
            pickerCenterX,
            pickerCenterY,
            overlayScale,
            pickerColor,
            shadowColor);

        OutdoorGameView::HudLayoutElement promptLayout = {};
        promptLayout.fontName = "arrus";
        promptLayout.textColorAbgr = pickerColor;
        promptLayout.textAlignX = OutdoorGameView::HudTextAlignX::Center;
        promptLayout.textAlignY = OutdoorGameView::HudTextAlignY::Top;
        OutdoorGameView::ResolvedHudLayoutElement promptRect = {};
        promptRect.x = uiViewport.x;
        promptRect.y = uiViewport.y + std::round(18.0f * overlayScale);
        promptRect.width = uiViewport.width;
        promptRect.height = std::round(24.0f * overlayScale);
        promptRect.scale = overlayScale;
        HudUiService::renderLayoutLabel(
            view,
            promptLayout,
            promptRect,
            "Select item target  LMB cast  Esc cancel");
    }

    for (const CharacterLayoutPassEntry &entry : characterLayoutPassEntries)
    {
        const OutdoorGameView::HudLayoutElement *pLayout = entry.pLayout;

        if (pLayout == nullptr || pLayout->labelText.empty())
        {
            continue;
        }

        OutdoorGameView::HudLayoutElement layoutForRender = *pLayout;
        const std::string &normalizedLayoutId = entry.normalizedId;
        const OutdoorGameView::ResolvedHudLayoutElement &resolved = entry.resolved;

        if (normalizedLayoutId == "characterstatsskillpointsvalue"
            || normalizedLayoutId == "characterskillsskillpointsvalue")
        {
            layoutForRender.textColorAbgr = skillPointsValueColorAbgr;
        }
        else if (normalizedLayoutId == "characterstatexperiencevalue")
        {
            layoutForRender.textColorAbgr = experienceValueColorAbgr;
        }

        std::string label = pLayout->labelText;
        label = replaceAll(label, "{gold}", std::to_string(party.gold()));
        label = replaceAll(label, "{food}", std::to_string(party.food()));
        label = replaceAll(label, "{character_name}", pCharacter != nullptr ? pCharacter->name : "");
        label = replaceAll(
            label,
            "{stats_skill_points}",
            pCharacter != nullptr ? "Skill Points: " + std::to_string(pCharacter->skillPoints) : "Skill Points: 0");
        label = replaceAll(
            label,
            "{stats_skill_points_value}",
            pCharacter != nullptr ? std::to_string(pCharacter->skillPoints) : "0");
        label = replaceAll(
            label,
            "{character_class_race}",
            pCharacter != nullptr ? (!pCharacter->className.empty() ? pCharacter->className : pCharacter->role) : "");
        label = replaceAll(
            label,
            "{quick_stats}",
            pCharacter != nullptr
                ? ("HP " + std::to_string(pCharacter->health) + "/" + std::to_string(pCharacter->maxHealth)
                    + "\nSP " + std::to_string(pCharacter->spellPoints) + "/" + std::to_string(pCharacter->maxSpellPoints))
                : "");
        label = replaceAll(label, "{might_value}", mightValue);
        label = replaceAll(label, "{intellect_value}", intellectValue);
        label = replaceAll(label, "{personality_value}", personalityValue);
        label = replaceAll(label, "{endurance_value}", enduranceValue);
        label = replaceAll(label, "{accuracy_value}", accuracyValue);
        label = replaceAll(label, "{speed_value}", speedValue);
        label = replaceAll(label, "{luck_value}", luckValue);
        label = replaceAll(label, "{hit_points_value}", hitPointsValue);
        label = replaceAll(label, "{spell_points_value}", spellPointsValue);
        label = replaceAll(label, "{armor_class_value}", armorClassValue);
        label = replaceAll(label, "{condition_value}", conditionValue);
        label = replaceAll(label, "{quick_spell_value}", quickSpellValue);
        label = replaceAll(label, "{age_value}", ageValue);
        label = replaceAll(label, "{level_value}", levelValue);
        label = replaceAll(label, "{experience_value}", experienceValue);
        label = replaceAll(label, "{attack_value}", attackValue);
        label = replaceAll(label, "{melee_damage_value}", meleeDamageValue);
        label = replaceAll(label, "{shoot_value}", shootValue);
        label = replaceAll(label, "{ranged_damage_value}", rangedDamageValue);
        label = replaceAll(label, "{fire_resistance_value}", fireResistanceValue);
        label = replaceAll(label, "{air_resistance_value}", airResistanceValue);
        label = replaceAll(label, "{water_resistance_value}", waterResistanceValue);
        label = replaceAll(label, "{earth_resistance_value}", earthResistanceValue);
        label = replaceAll(label, "{mind_resistance_value}", mindResistanceValue);
        label = replaceAll(label, "{body_resistance_value}", bodyResistanceValue);
        label = replaceAll(label, "{awards}", awards);
        label = replaceAll(label, "{award_detail}", "");
        label = replaceAll(label, "{inventory_info}", inventoryInfo);

        if (label.find('{') != std::string::npos)
        {
            label.clear();
        }

        SplitCharacterStatValue splitValue = {};

        if (tryGetSplitCharacterStatValue(normalizedLayoutId, summary, splitValue))
        {
            renderSplitCharacterStatLabel(layoutForRender, resolved, splitValue);
            continue;
        }

        HudUiService::renderLayoutLabel(view, layoutForRender, resolved, label);
    }

    if (isAdventurersInnActive)
    {
        const std::vector<AdventurersInnMember> &innMembers = party.adventurersInnMembers();
        const size_t maximumScrollOffset =
            innMembers.size() > AdventurersInnVisibleCount ? innMembers.size() - AdventurersInnVisibleCount : 0;
        const size_t scrollOffset = std::min(view.m_adventurersInnScrollOffset, maximumScrollOffset);
        const OutdoorGameView::HudFontHandle *pFont = HudUiService::findHudFont(view, "SMALLNUM");

        const auto renderInnLabel =
            [&view, baseScale](const std::string &text, float x, float y, float width, float height)
            {
                OutdoorGameView::HudLayoutElement layout = {};
                layout.fontName = "SMALLNUM";
                layout.textColorAbgr = AdventurersInnTextColorAbgr;
                layout.textAlignX = OutdoorGameView::HudTextAlignX::Left;
                layout.textAlignY = OutdoorGameView::HudTextAlignY::Top;
                OutdoorGameView::ResolvedHudLayoutElement resolved = {};
                resolved.x = std::round(x * baseScale);
                resolved.y = std::round(y * baseScale);
                resolved.width = width * baseScale;
                resolved.height = height * baseScale;
                resolved.scale = baseScale;
                HudUiService::renderLayoutLabel(view, layout, resolved, text);
            };

        for (size_t visibleIndex = 0; visibleIndex < AdventurersInnVisibleCount; ++visibleIndex)
        {
            const size_t innIndex = scrollOffset + visibleIndex;

            if (innIndex >= innMembers.size())
            {
                continue;
            }

            const size_t column = visibleIndex % AdventurersInnVisibleColumns;
            const size_t row = visibleIndex / AdventurersInnVisibleColumns;
            const float portraitX =
                uiViewport.x
                + (AdventurersInnPortraitX
                    + static_cast<float>(column) * (AdventurersInnPortraitWidth + AdventurersInnPortraitGapX)) * baseScale;
            const float portraitY =
                uiViewport.y
                + (AdventurersInnPortraitY
                    + static_cast<float>(row) * (AdventurersInnPortraitHeight + AdventurersInnPortraitGapY)) * baseScale;
            const float portraitWidth = AdventurersInnPortraitWidth * baseScale;
            const float portraitHeight = AdventurersInnPortraitHeight * baseScale;
            std::string textureName = npcPortraitTextureName(innMembers[innIndex].portraitPictureId);

            if (textureName.empty())
            {
                textureName = view.resolvePortraitTextureName(innMembers[innIndex].character);
            }

            const OutdoorGameView::HudTextureHandle *pPortraitTexture =
                HudUiService::ensureHudTextureLoaded(mutableView, textureName);

            if (pPortraitTexture != nullptr)
            {
                view.submitHudTexturedQuad(*pPortraitTexture, portraitX, portraitY, portraitWidth, portraitHeight);
            }

            if (innIndex == view.m_characterScreenSourceIndex)
            {
                const OutdoorGameView::HudTextureHandle *pSelectionTexture =
                    HudUiService::ensureSolidHudTextureLoaded(
                        mutableView,
                        "__adventurers_inn_selection__",
                        AdventurersInnSelectionColorAbgr);

                if (pSelectionTexture != nullptr)
                {
                    const float thickness = std::max(1.0f, AdventurersInnSelectionThickness * baseScale);
                    view.submitHudTexturedQuad(
                        *pSelectionTexture,
                        portraitX - thickness,
                        portraitY - thickness,
                        portraitWidth + thickness * 2.0f,
                        thickness);
                    view.submitHudTexturedQuad(
                        *pSelectionTexture,
                        portraitX - thickness,
                        portraitY + portraitHeight,
                        portraitWidth + thickness * 2.0f,
                        thickness);
                    view.submitHudTexturedQuad(*pSelectionTexture, portraitX - thickness, portraitY, thickness, portraitHeight);
                    view.submitHudTexturedQuad(*pSelectionTexture, portraitX + portraitWidth, portraitY, thickness, portraitHeight);
                }
            }
        }

        if (pCharacter != nullptr)
        {
            const auto formatSignedValue = [](const std::string &value) -> std::string
            {
                int parsedValue = 0;
                return tryParseInteger(value, parsedValue) && parsedValue > 0 ? "+" + value : value;
            };

            renderInnLabel(
                "Name: " + pCharacter->name,
                AdventurersInnColumn1X + uiViewport.x / baseScale,
                AdventurersInnColumn1Y + uiViewport.y / baseScale,
                170.0f,
                16.0f);
            renderInnLabel(
                "Class: " + (!pCharacter->className.empty() ? pCharacter->className : pCharacter->role),
                AdventurersInnColumn1X + uiViewport.x / baseScale,
                AdventurersInnColumn1Y + AdventurersInnColumnLineStep + uiViewport.y / baseScale,
                170.0f,
                16.0f);
            renderInnLabel(
                "HP: " + std::to_string(pCharacter->health),
                AdventurersInnColumn1X + uiViewport.x / baseScale,
                AdventurersInnColumn1Y + AdventurersInnColumnLineStep * 2.0f + uiViewport.y / baseScale,
                170.0f,
                16.0f);
            renderInnLabel(
                "AC: " + armorClassValue,
                AdventurersInnColumn1X + uiViewport.x / baseScale,
                AdventurersInnColumn1Y + AdventurersInnColumnLineStep * 3.0f + uiViewport.y / baseScale,
                170.0f,
                16.0f);
            renderInnLabel(
                "Attack: " + formatSignedValue(attackValue),
                AdventurersInnColumn1X + uiViewport.x / baseScale,
                AdventurersInnColumn1Y + AdventurersInnColumnLineStep * 4.0f + uiViewport.y / baseScale,
                170.0f,
                16.0f);
            renderInnLabel(
                "Shoot: " + formatSignedValue(shootValue),
                AdventurersInnColumn1X + uiViewport.x / baseScale,
                AdventurersInnColumn1Y + AdventurersInnColumnLineStep * 5.0f + uiViewport.y / baseScale,
                170.0f,
                16.0f);
            renderInnLabel(
                "Skills: " + std::to_string(pCharacter->skills.size()),
                AdventurersInnColumn1X + uiViewport.x / baseScale,
                AdventurersInnColumn1Y + AdventurersInnColumnLineStep * 6.0f + uiViewport.y / baseScale,
                170.0f,
                16.0f);
            renderInnLabel(
                "Cond: " + conditionValue,
                AdventurersInnColumn1X + uiViewport.x / baseScale,
                AdventurersInnColumn1Y + AdventurersInnColumnLineStep * 7.0f + uiViewport.y / baseScale,
                170.0f,
                16.0f);
            renderInnLabel(
                "QSpell: " + quickSpellValue,
                AdventurersInnColumn1X + uiViewport.x / baseScale,
                AdventurersInnColumn1Y + AdventurersInnColumnLineStep * 8.0f + uiViewport.y / baseScale,
                170.0f,
                16.0f);

            renderInnLabel(
                "Level: " + std::to_string(pCharacter->level),
                AdventurersInnColumn2X + uiViewport.x / baseScale,
                AdventurersInnColumn2Y + uiViewport.y / baseScale,
                130.0f,
                16.0f);
            renderInnLabel(
                "SP: " + std::to_string(pCharacter->spellPoints),
                AdventurersInnColumn2X + uiViewport.x / baseScale,
                AdventurersInnColumn2Y + AdventurersInnColumnLineStep + uiViewport.y / baseScale,
                130.0f,
                16.0f);
            renderInnLabel(
                "Dmg: " + meleeDamageValue,
                AdventurersInnColumn2X + uiViewport.x / baseScale,
                AdventurersInnColumn2Y + AdventurersInnColumnLineStep * 2.0f + uiViewport.y / baseScale,
                130.0f,
                16.0f);
            renderInnLabel(
                "Dmg: " + rangedDamageValue,
                AdventurersInnColumn2X + uiViewport.x / baseScale,
                AdventurersInnColumn2Y + AdventurersInnColumnLineStep * 3.0f + uiViewport.y / baseScale,
                130.0f,
                16.0f);
            renderInnLabel(
                "Points: " + std::to_string(pCharacter->skillPoints),
                AdventurersInnColumn2X + uiViewport.x / baseScale,
                AdventurersInnColumn2Y + AdventurersInnColumnLineStep * 4.0f + uiViewport.y / baseScale,
                130.0f,
                16.0f);

            if (pFont != nullptr && !adventurersInnBlurb.empty())
            {
                float fontScale = baseScale >= 1.0f ? snappedHudFontScale(baseScale) : std::max(0.5f, baseScale);
                const float lineHeight = std::max(1.0f, static_cast<float>(pFont->fontHeight - 2)) * fontScale;
                const float wrapWidth =
                    std::max(1.0f, (AdventurersInnBlurbWidth * baseScale) / std::max(0.5f, fontScale));
                const std::vector<std::string> wrappedLines =
                    HudUiService::wrapHudTextToWidth(view, *pFont, adventurersInnBlurb, wrapWidth);
                bgfx::TextureHandle coloredTextureHandle =
                    HudUiService::ensureHudFontMainTextureColor(view, *pFont, AdventurersInnTextColorAbgr);

                if (!bgfx::isValid(coloredTextureHandle))
                {
                    coloredTextureHandle = pFont->mainTextureHandle;
                }

                float blurbX = std::round(uiViewport.x + AdventurersInnBlurbX * baseScale);
                float blurbY = std::round(uiViewport.y + AdventurersInnBlurbY * baseScale);

                for (const std::string &line : wrappedLines)
                {
                    HudUiService::renderHudFontLayer(view, *pFont, pFont->shadowTextureHandle, line, blurbX, blurbY, fontScale);
                    HudUiService::renderHudFontLayer(view, *pFont, coloredTextureHandle, line, blurbX, blurbY, fontScale);
                    blurbY += lineHeight;
                }
            }
        }
    }

    const auto renderSkillGroup =
        [&view, width, height, &hasVisibleCharacterAncestors, &shouldRenderInCurrentPass, skillRowHeight](
            const char *pRegionId,
            const char *pLevelHeaderId,
            const std::vector<CharacterSkillUiRow> &rows)
        {
            const OutdoorGameView::HudLayoutElement *pRegionLayout = HudUiService::findHudLayoutElement(view, pRegionId);
            const OutdoorGameView::HudLayoutElement *pLevelLayout = HudUiService::findHudLayoutElement(view, pLevelHeaderId);

            if (pRegionLayout == nullptr
                || pLevelLayout == nullptr
                || !hasVisibleCharacterAncestors(*pRegionLayout)
                || !hasVisibleCharacterAncestors(*pLevelLayout)
                || !shouldRenderInCurrentPass(pRegionLayout->zIndex))
            {
                return;
            }

            const std::optional<OutdoorGameView::ResolvedHudLayoutElement> resolvedRegion = HudUiService::resolveHudLayoutElement(view, 
                pRegionId,
                width,
                height,
                pRegionLayout->width,
                pRegionLayout->height);
            const std::optional<OutdoorGameView::ResolvedHudLayoutElement> resolvedLevelHeader =
                HudUiService::resolveHudLayoutElement(view, 
                    pLevelHeaderId,
                    width,
                    height,
                    pLevelLayout->width,
                    pLevelLayout->height);

            if (!resolvedRegion || !resolvedLevelHeader)
            {
                return;
            }

            const float rowHeightPixels = skillRowHeight * resolvedRegion->scale;
            const float nameWidth =
                std::max(0.0f, resolvedLevelHeader->x - resolvedRegion->x - 6.0f * resolvedRegion->scale);
            const std::vector<CharacterSkillUiRow> displayRows =
                rows.empty() ? std::vector<CharacterSkillUiRow>{{"", "None", "", false}} : rows;

            for (size_t rowIndex = 0; rowIndex < displayRows.size(); ++rowIndex)
            {
                const CharacterSkillUiRow &row = displayRows[rowIndex];
                const uint32_t textColorAbgr = row.upgradeable ? 0xffff784au : 0xffffffffu;

                OutdoorGameView::HudLayoutElement nameLayout = {};
                nameLayout.fontName = "Lucida";
                nameLayout.textColorAbgr = textColorAbgr;
                nameLayout.textAlignX = OutdoorGameView::HudTextAlignX::Left;
                nameLayout.textAlignY = OutdoorGameView::HudTextAlignY::Middle;
                OutdoorGameView::ResolvedHudLayoutElement nameResolved = {};
                nameResolved.x = resolvedRegion->x;
                nameResolved.y = resolvedRegion->y + static_cast<float>(rowIndex) * rowHeightPixels;
                nameResolved.width = nameWidth;
                nameResolved.height = rowHeightPixels;
                nameResolved.scale = resolvedRegion->scale;
                HudUiService::renderLayoutLabel(view, nameLayout, nameResolved, row.label);

                if (!row.level.empty())
                {
                    OutdoorGameView::HudLayoutElement levelLayout = {};
                    levelLayout.fontName = "Lucida";
                    levelLayout.textColorAbgr = textColorAbgr;
                    levelLayout.textAlignX = OutdoorGameView::HudTextAlignX::Right;
                    levelLayout.textAlignY = OutdoorGameView::HudTextAlignY::Middle;
                    OutdoorGameView::ResolvedHudLayoutElement levelResolved = {};
                    levelResolved.x = resolvedLevelHeader->x;
                    levelResolved.y = nameResolved.y;
                    levelResolved.width = resolvedLevelHeader->width;
                    levelResolved.height = rowHeightPixels;
                    levelResolved.scale = resolvedLevelHeader->scale;
                    HudUiService::renderLayoutLabel(view, levelLayout, levelResolved, row.level);
                }
            }
        };

    renderSkillGroup("CharacterSkillsWeaponsListRegion", "CharacterSkillsWeaponsLevelHeader", skillUiData.weaponRows);
    renderSkillGroup("CharacterSkillsMagicListRegion", "CharacterSkillsMagicLevelHeader", skillUiData.magicRows);
    renderSkillGroup("CharacterSkillsArmorListRegion", "CharacterSkillsArmorLevelHeader", skillUiData.armorRows);
    renderSkillGroup("CharacterSkillsMiscListRegion", "CharacterSkillsMiscLevelHeader", skillUiData.miscRows);
}

void GameplayPartyOverlayRenderer::renderActorInspectOverlay(OutdoorGameView &view, int width, int height)
{
    if (!view.m_actorInspectOverlay.active
        || view.m_pOutdoorWorldRuntime == nullptr
        || !view.m_monsterTable.has_value()
        || !bgfx::isValid(view.m_programHandle)
        || !bgfx::isValid(view.m_texturedTerrainProgramHandle)
        || !bgfx::isValid(view.m_terrainTextureSamplerHandle)
        || width <= 0
        || height <= 0)
    {
        return;
    }

    const OutdoorWorldRuntime::MapActorState *pActorState =
        view.m_pOutdoorWorldRuntime->mapActorState(view.m_actorInspectOverlay.runtimeActorIndex);

    if (pActorState == nullptr)
    {
        return;
    }

    const MonsterTable::MonsterStatsEntry *pStats = view.m_monsterTable->findStatsById(pActorState->monsterId);

    if (pStats == nullptr)
    {
        return;
    }

    const OutdoorGameView::HudLayoutElement *pRootLayout = HudUiService::findHudLayoutElement(view, "ActorInspectRoot");
    const OutdoorGameView::HudLayoutElement *pPreviewLayout = HudUiService::findHudLayoutElement(view, "ActorInspectPreviewFrame");
    const OutdoorGameView::HudLayoutElement *pHealthBarBackgroundLayout =
        HudUiService::findHudLayoutElement(view, "ActorInspectHealthBarBackground");
    const OutdoorGameView::HudLayoutElement *pHealthBarFillLayout =
        HudUiService::findHudLayoutElement(view, "ActorInspectHealthBarFill");

    if (pRootLayout == nullptr
        || pPreviewLayout == nullptr
        || pHealthBarBackgroundLayout == nullptr
        || pHealthBarFillLayout == nullptr)
    {
        return;
    }

    const UiViewportRect uiViewport = computeUiViewportRect(width, height);
    const float baseScale = std::min(uiViewport.width / HudReferenceWidth, uiViewport.height / HudReferenceHeight);
    const float popupScale = std::clamp(baseScale, pRootLayout->minScale, pRootLayout->maxScale);
    const float rootWidth = pRootLayout->width * popupScale;
    const float rootHeight = pRootLayout->height * popupScale;
    const float popupGap = 12.0f * popupScale;
    float rootX = view.m_actorInspectOverlay.sourceX + view.m_actorInspectOverlay.sourceWidth + popupGap;

    if (rootX + rootWidth > uiViewport.x + uiViewport.width)
    {
        rootX = view.m_actorInspectOverlay.sourceX - rootWidth - popupGap;
    }

    rootX = std::clamp(rootX, uiViewport.x, uiViewport.x + uiViewport.width - rootWidth);
    float rootY = view.m_actorInspectOverlay.sourceY + (view.m_actorInspectOverlay.sourceHeight - rootHeight) * 0.5f;
    rootY = std::clamp(rootY, uiViewport.y, uiViewport.y + uiViewport.height - rootHeight);
    const OutdoorGameView::ResolvedHudLayoutElement rootRect = {
        std::round(rootX),
        std::round(rootY),
        std::round(rootWidth),
        std::round(rootHeight),
        popupScale
    };

    setupHudProjection(width, height);

    const auto submitSolidQuad =
        [&view](float x, float y, float quadWidth, float quadHeight, uint32_t abgr)
        {
            if (quadWidth <= 0.0f || quadHeight <= 0.0f)
            {
                return;
            }

            const std::string textureName = "__actor_inspect_solid_" + std::to_string(abgr);
            const OutdoorGameView::HudTextureHandle *pSolidTexture =
                HudUiService::ensureSolidHudTextureLoaded(
                    const_cast<OutdoorGameView &>(view),
                    textureName,
                    abgr);

            if (pSolidTexture == nullptr)
            {
                return;
            }

            view.submitHudTexturedQuad(*pSolidTexture, x, y, quadWidth, quadHeight);
        };

    std::function<std::optional<OutdoorGameView::ResolvedHudLayoutElement>(const std::string &)> resolveLayout;
    resolveLayout =
        [&view, &rootRect, popupScale, &resolveLayout](
            const std::string &layoutId) -> std::optional<OutdoorGameView::ResolvedHudLayoutElement>
        {
            const OutdoorGameView::HudLayoutElement *pLayout = HudUiService::findHudLayoutElement(view, layoutId);

            if (pLayout == nullptr)
            {
                return std::nullopt;
            }

            float resolvedWidth = pLayout->width * popupScale;
            float resolvedHeight = pLayout->height * popupScale;
            const std::string normalizedLayoutId = toLowerCopy(layoutId);

            if ((pLayout->width <= 0.0f || pLayout->height <= 0.0f) && !pLayout->primaryAsset.empty())
            {
                const OutdoorGameView::HudTextureHandle *pTexture = HudUiService::ensureHudTextureLoaded(const_cast<OutdoorGameView &>(view), pLayout->primaryAsset);

                if (pTexture != nullptr)
                {
                    if (pLayout->width <= 0.0f)
                    {
                        resolvedWidth = static_cast<float>(pTexture->width) * popupScale;
                    }

                    if (pLayout->height <= 0.0f)
                    {
                        resolvedHeight = static_cast<float>(pTexture->height) * popupScale;
                    }
                }
            }

            if (normalizedLayoutId == "actorinspectcorner_topedge"
                || normalizedLayoutId == "actorinspectcorner_bottomedge")
            {
                resolvedWidth = rootRect.width;
            }

            if (normalizedLayoutId == "actorinspectcorner_leftedge"
                || normalizedLayoutId == "actorinspectcorner_rightedge")
            {
                resolvedHeight = rootRect.height;
            }

            OutdoorGameView::ResolvedHudLayoutElement parent = rootRect;

            if (!pLayout->parentId.empty() && toLowerCopy(pLayout->parentId) != "actorinspectroot")
            {
                const std::optional<OutdoorGameView::ResolvedHudLayoutElement> resolvedParent =
                    resolveLayout(pLayout->parentId);

                if (resolvedParent)
                {
                    parent = *resolvedParent;
                }
            }

            return OutdoorGameView::resolveAttachedHudLayoutRect(
                pLayout->attachTo,
                parent,
                resolvedWidth,
                resolvedHeight,
                pLayout->gapX,
                pLayout->gapY,
                popupScale);
        };

    const std::optional<OutdoorGameView::ResolvedHudLayoutElement> previewRect =
        resolveLayout("ActorInspectPreviewFrame");
    const float previewBorderThickness = std::max(1.0f, std::round(0.125f * popupScale));
    const float previewInnerInset = previewBorderThickness;
    const uint32_t previewBackgroundColor = makeAbgrColor(0, 0, 0, 255);
    const uint32_t previewBorderColor = makeAbgrColor(255, 255, 155, 255);
    const OutdoorGameView::HudTextureHandle *pBackgroundTexture =
        HudUiService::ensureHudTextureLoaded(const_cast<OutdoorGameView &>(view), pRootLayout->primaryAsset);

    if (pBackgroundTexture != nullptr)
    {
        view.submitHudTexturedQuad(*pBackgroundTexture, rootRect.x, rootRect.y, rootRect.width, rootRect.height);
    }

    const std::vector<std::string> orderedLayoutIds = HudUiService::sortedHudLayoutIdsForScreen(view, "ActorInspect");

    for (const std::string &layoutId : orderedLayoutIds)
    {
        const OutdoorGameView::HudLayoutElement *pLayout = HudUiService::findHudLayoutElement(view, layoutId);

        if (pLayout == nullptr
            || !pLayout->visible
            || pLayout->primaryAsset.empty()
            || toLowerCopy(pLayout->id) == "actorinspectroot"
            || toLowerCopy(pLayout->id) == "actorinspectpreviewframe")
        {
            continue;
        }

        const OutdoorGameView::HudTextureHandle *pTexture = HudUiService::ensureHudTextureLoaded(const_cast<OutdoorGameView &>(view), pLayout->primaryAsset);
        const std::optional<OutdoorGameView::ResolvedHudLayoutElement> resolved = resolveLayout(layoutId);

        if (pTexture == nullptr || !resolved)
        {
            continue;
        }

        view.submitHudTexturedQuad(*pTexture, resolved->x, resolved->y, resolved->width, resolved->height);
    }

    const float healthRatio = pActorState->maxHp > 0
        ? std::clamp(
            static_cast<float>(pActorState->currentHp) / static_cast<float>(pActorState->maxHp),
            0.0f,
            1.0f)
        : 0.0f;
    uint32_t healthBarColor = makeAbgrColor(0, 255, 0);

    if (healthRatio < 0.25f)
    {
        healthBarColor = makeAbgrColor(255, 0, 0);
    }
    else if (healthRatio < 0.5f)
    {
        healthBarColor = makeAbgrColor(255, 255, 0);
    }

    if (const std::optional<OutdoorGameView::ResolvedHudLayoutElement> healthBackgroundRect =
            resolveLayout("ActorInspectHealthBarBackground"))
    {
        submitSolidQuad(
            healthBackgroundRect->x,
            healthBackgroundRect->y,
            healthBackgroundRect->width,
            healthBackgroundRect->height,
            makeAbgrColor(32, 32, 32, 220));
    }

    if (const std::optional<OutdoorGameView::ResolvedHudLayoutElement> healthFillRect =
            resolveLayout("ActorInspectHealthBarFill"))
    {
        submitSolidQuad(
            healthFillRect->x,
            healthFillRect->y,
            healthFillRect->width * healthRatio,
            healthFillRect->height,
            healthBarColor);
    }

    if (previewRect)
    {
        submitSolidQuad(previewRect->x, previewRect->y, previewRect->width, previewRect->height, previewBorderColor);
        submitSolidQuad(
            previewRect->x + previewInnerInset,
            previewRect->y + previewInnerInset,
            std::max(1.0f, previewRect->width - previewInnerInset * 2.0f),
            std::max(1.0f, previewRect->height - previewInnerInset * 2.0f),
            previewBackgroundColor);
    }

    if (view.m_outdoorActorPreviewBillboardSet)
    {
        uint16_t spriteFrameIndex = pActorState->spriteFrameIndex;
        const size_t walkingAnimationIndex = static_cast<size_t>(OutdoorWorldRuntime::ActorAnimation::Walking);

        if (walkingAnimationIndex < pActorState->actionSpriteFrameIndices.size()
            && pActorState->actionSpriteFrameIndices[walkingAnimationIndex] != 0)
        {
            spriteFrameIndex = pActorState->actionSpriteFrameIndices[walkingAnimationIndex];
        }

        const SpriteFrameEntry *pFrame =
            view.m_outdoorActorPreviewBillboardSet->spriteFrameTable.getFrame(spriteFrameIndex, currentAnimationTicks());

        if (pFrame == nullptr)
        {
            pFrame = view.m_outdoorActorPreviewBillboardSet->spriteFrameTable.getFrame(spriteFrameIndex, 0);
        }

        if (pFrame != nullptr && previewRect)
        {
            static constexpr int PreviewFacingOctant = 0;
            const ResolvedSpriteTexture resolvedTexture =
                SpriteFrameTable::resolveTexture(*pFrame, PreviewFacingOctant);
            const OutdoorGameView::BillboardTextureHandle *pExistingTexture =
                view.findBillboardTexture(resolvedTexture.textureName, pFrame->paletteId);
            const OutdoorGameView::BillboardTextureHandle *pTexture =
                pExistingTexture != nullptr
                    ? pExistingTexture
                    : OutdoorBillboardRenderer::ensureSpriteBillboardTexture(
                        view,
                        resolvedTexture.textureName,
                        pFrame->paletteId);

            if (pTexture != nullptr && bgfx::isValid(pTexture->textureHandle))
            {
                const float previewPadding = std::round(4.0f * popupScale);
                const float baseAvailableWidth = std::max(1.0f, previewRect->width - previewPadding * 2.0f);
                const float baseAvailableHeight = std::max(1.0f, previewRect->height - previewPadding * 2.0f);
                const float expandedAvailableWidth = std::max(1.0f, previewRect->width * 1.4f);
                const float expandedAvailableHeight = std::max(1.0f, previewRect->height * 1.4f);
                const float fitScale = std::min(
                    baseAvailableWidth / static_cast<float>(std::max(1, pTexture->width)),
                    baseAvailableHeight / static_cast<float>(std::max(1, pTexture->height)));
                const float boostedScale = std::min(
                    fitScale * 1.4f,
                    std::min(
                        expandedAvailableWidth / static_cast<float>(std::max(1, pTexture->width)),
                        expandedAvailableHeight / static_cast<float>(std::max(1, pTexture->height))));
                const float portraitZoomScale = boostedScale * 1.45f;
                const float previewWidth = static_cast<float>(pTexture->width) * portraitZoomScale;
                const float previewHeight = static_cast<float>(pTexture->height) * portraitZoomScale;
                const float previewX = std::round(previewRect->x + (previewRect->width - previewWidth) * 0.5f);
                const uint16_t scissorX = static_cast<uint16_t>(
                    std::clamp(std::lround(previewRect->x + previewInnerInset), 0l, long(width)));
                const uint16_t scissorY = static_cast<uint16_t>(
                    std::clamp(std::lround(previewRect->y + previewInnerInset), 0l, long(height)));
                const uint16_t scissorWidth = static_cast<uint16_t>(
                    std::clamp(
                        std::lround(std::max(1.0f, previewRect->width - previewInnerInset * 2.0f)),
                        1l,
                        long(width)));
                const uint16_t scissorHeight = static_cast<uint16_t>(
                    std::clamp(
                        std::lround(std::max(1.0f, previewRect->height - previewInnerInset * 2.0f)),
                        1l,
                        long(height)));
                const float visibleCenterY =
                    static_cast<float>(scissorY) + static_cast<float>(scissorHeight) * 0.5f;
                const float previewY = std::round(visibleCenterY - previewHeight * 0.48f);

                if (bgfx::getAvailTransientVertexBuffer(6, OutdoorGameView::TexturedTerrainVertex::ms_layout) >= 6)
                {
                    bgfx::TransientVertexBuffer transientVertexBuffer = {};
                    bgfx::allocTransientVertexBuffer(
                        &transientVertexBuffer,
                        6,
                        OutdoorGameView::TexturedTerrainVertex::ms_layout);
                    OutdoorGameView::TexturedTerrainVertex *pVertices =
                        reinterpret_cast<OutdoorGameView::TexturedTerrainVertex *>(transientVertexBuffer.data);
                    pVertices[0] = {previewX, previewY, 0.0f, 0.0f, 0.0f};
                    pVertices[1] = {previewX + previewWidth, previewY, 0.0f, 1.0f, 0.0f};
                    pVertices[2] = {previewX + previewWidth, previewY + previewHeight, 0.0f, 1.0f, 1.0f};
                    pVertices[3] = {previewX, previewY, 0.0f, 0.0f, 0.0f};
                    pVertices[4] = {previewX + previewWidth, previewY + previewHeight, 0.0f, 1.0f, 1.0f};
                    pVertices[5] = {previewX, previewY + previewHeight, 0.0f, 0.0f, 1.0f};
                    float modelMatrix[16] = {};
                    bx::mtxIdentity(modelMatrix);
                    bgfx::setTransform(modelMatrix);
                    bgfx::setVertexBuffer(0, &transientVertexBuffer);
                    bindTexture(
                        0,
                        view.m_terrainTextureSamplerHandle,
                        pTexture->textureHandle,
                        TextureFilterProfile::Billboard,
                        BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP);
                    bgfx::setScissor(scissorX, scissorY, scissorWidth, scissorHeight);
                    bgfx::setState(BGFX_STATE_WRITE_RGB | BGFX_STATE_WRITE_A | BGFX_STATE_BLEND_ALPHA);
                    bgfx::submit(HudViewId, view.m_texturedTerrainProgramHandle);
                    bgfx::setScissor(0, 0, static_cast<uint16_t>(width), static_cast<uint16_t>(height));
                }
            }
        }
    }

    if (previewRect)
    {
        submitSolidQuad(previewRect->x, previewRect->y, previewRect->width, previewBorderThickness, previewBorderColor);
        submitSolidQuad(
            previewRect->x,
            previewRect->y + previewRect->height - previewBorderThickness,
            previewRect->width,
            previewBorderThickness,
            previewBorderColor);
        submitSolidQuad(
            previewRect->x,
            previewRect->y,
            previewBorderThickness,
            previewRect->height,
            previewBorderColor);
        submitSolidQuad(
            previewRect->x + previewRect->width - previewBorderThickness,
            previewRect->y,
            previewBorderThickness,
            previewRect->height,
            previewBorderColor);
    }

    const std::string attackText = joinNonEmptyTexts({
        pStats->attack1Type,
        (pStats->attack2Chance > 0 || !pStats->attack2Type.empty()) ? pStats->attack2Type : std::string()});
    const std::string damageText = joinNonEmptyTexts({
        formatMonsterDamageText(pStats->attack1Damage),
        (pStats->attack2Chance > 0 || pStats->attack2Damage.diceRolls > 0)
            ? formatMonsterDamageText(pStats->attack2Damage)
            : std::string()});
    const std::string spellText = joinNonEmptyTexts({
        pStats->hasSpell1 ? pStats->spell1Name : std::string(),
        pStats->hasSpell2 ? pStats->spell2Name : std::string()});
    std::vector<std::string> activeEffects;

    if (pActorState->isDead)
    {
        activeEffects.push_back("Dead");
    }
    else
    {
        if (pActorState->stunRemainingSeconds > 0.0f)
        {
            activeEffects.push_back("Stunned");
        }

        if (pActorState->paralyzeRemainingSeconds > 0.0f)
        {
            activeEffects.push_back("Paralyzed");
        }

        if (pActorState->slowRemainingSeconds > 0.0f)
        {
            activeEffects.push_back("Slow");
        }

        if (pActorState->fearRemainingSeconds > 0.0f)
        {
            activeEffects.push_back("Afraid");
        }

        if (pActorState->shrinkRemainingSeconds > 0.0f)
        {
            activeEffects.push_back("Shrunk");
        }

        if (pActorState->darkGraspRemainingSeconds > 0.0f)
        {
            activeEffects.push_back("Dark Grasp");
        }

        switch (pActorState->controlMode)
        {
            case OutdoorWorldRuntime::ActorControlMode::Charm:
                activeEffects.push_back("Charmed");
                break;
            case OutdoorWorldRuntime::ActorControlMode::Berserk:
                activeEffects.push_back("Berserk");
                break;
            case OutdoorWorldRuntime::ActorControlMode::Enslaved:
                activeEffects.push_back("Enslaved");
                break;
            case OutdoorWorldRuntime::ActorControlMode::ControlUndead:
                activeEffects.push_back("Controlled");
                break;
            case OutdoorWorldRuntime::ActorControlMode::Reanimated:
                activeEffects.push_back("Reanimated");
                break;
            case OutdoorWorldRuntime::ActorControlMode::None:
                break;
        }
    }

    const std::string effectsText = activeEffects.empty() ? "None" : joinNonEmptyTexts(activeEffects);
    const auto renderTextForLayout =
        [&view, &resolveLayout](const char *pLayoutId, const std::string &text)
        {
            const OutdoorGameView::HudLayoutElement *pLayout = HudUiService::findHudLayoutElement(view, pLayoutId);
            const std::optional<OutdoorGameView::ResolvedHudLayoutElement> resolved = resolveLayout(pLayoutId);

            if (pLayout == nullptr || !resolved || text.empty())
            {
                return;
            }

            HudUiService::renderLayoutLabel(view, *pLayout, *resolved, text);
        };

    for (const char *pLabelId : {
             "ActorInspectHitPointsLabel",
             "ActorInspectArmorClassLabel",
             "ActorInspectAttackLabel",
             "ActorInspectDamageLabel",
             "ActorInspectSpellLabel",
             "ActorInspectEffectsHeader",
             "ActorInspectResistancesHeader",
             "ActorInspectResistanceFireLabel",
             "ActorInspectResistanceAirLabel",
             "ActorInspectResistanceWaterLabel",
             "ActorInspectResistanceEarthLabel",
             "ActorInspectResistanceMindLabel",
             "ActorInspectResistanceSpiritLabel",
             "ActorInspectResistanceBodyLabel",
             "ActorInspectResistanceLightLabel",
             "ActorInspectResistanceDarkLabel",
             "ActorInspectResistancePhysicalLabel"})
    {
        const OutdoorGameView::HudLayoutElement *pLayout = HudUiService::findHudLayoutElement(view, pLabelId);

        if (pLayout != nullptr)
        {
            renderTextForLayout(pLabelId, pLayout->labelText);
        }
    }

    renderTextForLayout("ActorInspectTitle", pActorState->displayName);
    renderTextForLayout(
        "ActorInspectHitPointsValue",
        std::to_string(std::max(0, pActorState->currentHp))
            + " / "
            + std::to_string(std::max(0, pActorState->maxHp)));
    renderTextForLayout(
        "ActorInspectArmorClassValue",
        std::to_string(view.m_pOutdoorWorldRuntime->effectiveMapActorArmorClass(view.m_actorInspectOverlay.runtimeActorIndex)));
    renderTextForLayout("ActorInspectAttackValue", attackText);
    renderTextForLayout("ActorInspectDamageValue", damageText);
    renderTextForLayout("ActorInspectSpellValue", spellText);
    renderTextForLayout("ActorInspectEffectsBody", effectsText);
    renderTextForLayout("ActorInspectResistanceFireValue", formatMonsterResistanceText(pStats->fireResistance));
    renderTextForLayout("ActorInspectResistanceAirValue", formatMonsterResistanceText(pStats->airResistance));
    renderTextForLayout("ActorInspectResistanceWaterValue", formatMonsterResistanceText(pStats->waterResistance));
    renderTextForLayout("ActorInspectResistanceEarthValue", formatMonsterResistanceText(pStats->earthResistance));
    renderTextForLayout("ActorInspectResistanceMindValue", formatMonsterResistanceText(pStats->mindResistance));
    renderTextForLayout("ActorInspectResistanceSpiritValue", formatMonsterResistanceText(pStats->spiritResistance));
    renderTextForLayout("ActorInspectResistanceBodyValue", formatMonsterResistanceText(pStats->bodyResistance));
    renderTextForLayout("ActorInspectResistanceLightValue", formatMonsterResistanceText(pStats->lightResistance));
    renderTextForLayout("ActorInspectResistanceDarkValue", formatMonsterResistanceText(pStats->darkResistance));
    renderTextForLayout("ActorInspectResistancePhysicalValue", formatMonsterResistanceText(pStats->physicalResistance));
}
} // namespace OpenYAMM::Game
