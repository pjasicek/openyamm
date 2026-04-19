#include "game/ui/screens/LoadGameScreen.h"

#include "game/maps/SaveGame.h"

#include <SDL3/SDL.h>

#include <algorithm>
#include <array>
#include <cctype>
#include <cmath>
#include <cstdio>
#include <cstring>
#include <optional>
#include <string_view>
#include <unordered_set>
#include <utility>

namespace OpenYAMM::Game
{
namespace
{
constexpr float ReferenceWidth = 640.0f;
constexpr float ReferenceHeight = 480.0f;
constexpr const char *LoadGameLayoutPath = "Data/ui/gameplay/load_game.yml";
constexpr size_t VisibleSlotCount = 10;
constexpr uint64_t SlotDoubleClickWindowMs = 500;
constexpr uint32_t WhiteColorAbgr = 0xffffffffu;
constexpr uint32_t SelectedRowColorAbgr = 0xff00ffffu;

struct CivilTime
{
    int year = 1168;
    int month = 1;
    int day = 1;
    int dayOfWeek = 1;
    int hour24 = 9;
    int hour12 = 9;
    int minute = 0;
    bool isPm = false;
};

struct ResolvedLayoutElement
{
    float x = 0.0f;
    float y = 0.0f;
    float width = 0.0f;
    float height = 0.0f;
    float scale = 1.0f;
};

std::string toLowerCopy(const std::string &value)
{
    std::string normalized = value;

    for (char &character : normalized)
    {
        character = static_cast<char>(std::tolower(static_cast<unsigned char>(character)));
    }

    return normalized;
}

CivilTime civilTimeFromGameMinutes(float gameMinutes)
{
    const int totalMinutes = std::max(0, static_cast<int>(std::floor(gameMinutes)));
    const int totalDays = totalMinutes / (24 * 60);
    CivilTime time = {};
    time.year = 1168 + totalDays / (12 * 28);
    time.month = 1 + (totalDays / 28) % 12;
    time.day = 1 + totalDays % 28;
    time.dayOfWeek = 1 + totalDays % 7;
    time.hour24 = (totalMinutes / 60) % 24;
    time.minute = totalMinutes % 60;
    time.isPm = time.hour24 >= 12;
    time.hour12 = time.hour24 % 12;

    if (time.hour12 == 0)
    {
        time.hour12 = 12;
    }

    return time;
}

std::string weekdayName(int dayOfWeek)
{
    static const std::array<const char *, 7> names = {
        "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"
    };
    return names[std::clamp(dayOfWeek, 1, 7) - 1];
}

std::string monthName(int month)
{
    static const std::array<const char *, 12> names = {
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    };
    return names[std::clamp(month, 1, 12) - 1];
}

std::string formatClock(const CivilTime &time)
{
    char buffer[32] = {};
    std::snprintf(
        buffer,
        sizeof(buffer),
        "%s %02d:%02d%s",
        weekdayName(time.dayOfWeek).c_str(),
        time.hour12,
        time.minute,
        time.isPm ? "PM" : "AM");
    return buffer;
}

std::string formatDate(const CivilTime &time)
{
    char buffer[64] = {};
    std::snprintf(buffer, sizeof(buffer), "%d %s %d", time.day, monthName(time.month).c_str(), time.year);
    return buffer;
}

std::string friendlySaveFileLabel(const std::filesystem::path &path)
{
    const std::string stem = toLowerCopy(path.stem().string());

    if (stem == "autosave")
    {
        return "Autosave";
    }

    if (stem == "quicksave")
    {
        return "Quicksave";
    }

    if (stem.rfind("save", 0) == 0 && stem.size() > 4)
    {
        const std::string suffix = stem.substr(4);
        const bool allDigits = std::all_of(
            suffix.begin(),
            suffix.end(),
            [](char character)
            {
                return std::isdigit(static_cast<unsigned char>(character)) != 0;
            });

        if (allDigits)
        {
            return "Save " + std::to_string(std::max(1, std::stoi(suffix)));
        }
    }

    std::string label = path.stem().string();

    if (!label.empty())
    {
        label[0] = static_cast<char>(std::toupper(static_cast<unsigned char>(label[0])));
    }

    return label;
}

bool decodeBmpBytesToBgra(
    const std::vector<uint8_t> &bmpBytes,
    int &width,
    int &height,
    std::vector<uint8_t> &pixels)
{
    SDL_IOStream *pIoStream = SDL_IOFromConstMem(bmpBytes.data(), bmpBytes.size());

    if (pIoStream == nullptr)
    {
        return false;
    }

    SDL_Surface *pLoadedSurface = SDL_LoadBMP_IO(pIoStream, true);

    if (pLoadedSurface == nullptr)
    {
        return false;
    }

    SDL_Surface *pConvertedSurface = SDL_ConvertSurface(pLoadedSurface, SDL_PIXELFORMAT_BGRA32);
    SDL_DestroySurface(pLoadedSurface);

    if (pConvertedSurface == nullptr)
    {
        return false;
    }

    width = pConvertedSurface->w;
    height = pConvertedSurface->h;
    const size_t pixelCount = static_cast<size_t>(width) * static_cast<size_t>(height) * 4;
    pixels.resize(pixelCount);
    std::memcpy(pixels.data(), pConvertedSurface->pixels, pixelCount);
    SDL_DestroySurface(pConvertedSurface);
    return true;
}

ResolvedLayoutElement resolveAttachedLayoutRect(
    UiLayoutManager::LayoutAttachMode attachTo,
    const ResolvedLayoutElement &parent,
    float width,
    float height,
    float gapX,
    float gapY,
    float scale)
{
    ResolvedLayoutElement resolved = {};
    resolved.width = width;
    resolved.height = height;
    resolved.scale = scale;

    switch (attachTo)
    {
        case UiLayoutManager::LayoutAttachMode::None:
            resolved.x = parent.x + gapX * scale;
            resolved.y = parent.y + gapY * scale;
            break;

        case UiLayoutManager::LayoutAttachMode::RightOf:
            resolved.x = parent.x + parent.width + gapX * scale;
            resolved.y = parent.y + gapY * scale;
            break;

        case UiLayoutManager::LayoutAttachMode::LeftOf:
            resolved.x = parent.x - resolved.width + gapX * scale;
            resolved.y = parent.y + gapY * scale;
            break;

        case UiLayoutManager::LayoutAttachMode::Above:
            resolved.x = parent.x + gapX * scale;
            resolved.y = parent.y - resolved.height + gapY * scale;
            break;

        case UiLayoutManager::LayoutAttachMode::Below:
            resolved.x = parent.x + gapX * scale;
            resolved.y = parent.y + parent.height + gapY * scale;
            break;

        case UiLayoutManager::LayoutAttachMode::CenterAbove:
            resolved.x = parent.x + (parent.width - resolved.width) * 0.5f + gapX * scale;
            resolved.y = parent.y - resolved.height + gapY * scale;
            break;

        case UiLayoutManager::LayoutAttachMode::CenterBelow:
            resolved.x = parent.x + (parent.width - resolved.width) * 0.5f + gapX * scale;
            resolved.y = parent.y + parent.height + gapY * scale;
            break;

        case UiLayoutManager::LayoutAttachMode::InsideLeft:
            resolved.x = parent.x + gapX * scale;
            resolved.y = parent.y + (parent.height - resolved.height) * 0.5f + gapY * scale;
            break;

        case UiLayoutManager::LayoutAttachMode::InsideRight:
            resolved.x = parent.x + parent.width - resolved.width + gapX * scale;
            resolved.y = parent.y + (parent.height - resolved.height) * 0.5f + gapY * scale;
            break;

        case UiLayoutManager::LayoutAttachMode::InsideTopCenter:
            resolved.x = parent.x + (parent.width - resolved.width) * 0.5f + gapX * scale;
            resolved.y = parent.y + gapY * scale;
            break;

        case UiLayoutManager::LayoutAttachMode::InsideTopLeft:
            resolved.x = parent.x + gapX * scale;
            resolved.y = parent.y + gapY * scale;
            break;

        case UiLayoutManager::LayoutAttachMode::InsideTopRight:
            resolved.x = parent.x + parent.width - resolved.width + gapX * scale;
            resolved.y = parent.y + gapY * scale;
            break;

        case UiLayoutManager::LayoutAttachMode::InsideBottomLeft:
            resolved.x = parent.x + gapX * scale;
            resolved.y = parent.y + parent.height - resolved.height + gapY * scale;
            break;

        case UiLayoutManager::LayoutAttachMode::InsideBottomCenter:
            resolved.x = parent.x + (parent.width - resolved.width) * 0.5f + gapX * scale;
            resolved.y = parent.y + parent.height - resolved.height + gapY * scale;
            break;

        case UiLayoutManager::LayoutAttachMode::InsideBottomRight:
            resolved.x = parent.x + parent.width - resolved.width + gapX * scale;
            resolved.y = parent.y + parent.height - resolved.height + gapY * scale;
            break;

        case UiLayoutManager::LayoutAttachMode::CenterIn:
            resolved.x = parent.x + (parent.width - resolved.width) * 0.5f + gapX * scale;
            resolved.y = parent.y + (parent.height - resolved.height) * 0.5f + gapY * scale;
            break;
    }

    return resolved;
}

std::optional<ResolvedLayoutElement> resolveLayoutElementRecursive(
    const UiLayoutManager &layoutManager,
    const std::string &layoutId,
    int screenWidth,
    int screenHeight,
    float fallbackWidth,
    float fallbackHeight,
    std::unordered_set<std::string> &visited)
{
    if (visited.contains(layoutId))
    {
        return std::nullopt;
    }

    visited.insert(layoutId);
    const UiLayoutManager::LayoutElement *pElement = layoutManager.findElement(layoutId);

    if (pElement == nullptr)
    {
        visited.erase(layoutId);
        return std::nullopt;
    }

    const UiLayoutManager::LayoutElement &element = *pElement;
    const float baseScale = std::min(
        static_cast<float>(screenWidth) / ReferenceWidth,
        static_cast<float>(screenHeight) / ReferenceHeight);
    const float viewportWidth = ReferenceWidth * baseScale;
    const float viewportHeight = ReferenceHeight * baseScale;
    const float viewportX = (static_cast<float>(screenWidth) - viewportWidth) * 0.5f;
    const float viewportY = (static_cast<float>(screenHeight) - viewportHeight) * 0.5f;
    ResolvedLayoutElement resolved = {};

    if (!element.parentId.empty())
    {
        const UiLayoutManager::LayoutElement *pParent = layoutManager.findElement(element.parentId);

        if (pParent == nullptr)
        {
            visited.erase(layoutId);
            return std::nullopt;
        }

        const std::optional<ResolvedLayoutElement> parent = resolveLayoutElementRecursive(
            layoutManager,
            element.parentId,
            screenWidth,
            screenHeight,
            pParent->width,
            pParent->height,
            visited);

        if (!parent.has_value())
        {
            visited.erase(layoutId);
            return std::nullopt;
        }

        resolved.scale = element.hasExplicitScale
            ? std::clamp(baseScale, element.minScale, element.maxScale)
            : parent->scale;
        resolved.width = (element.width > 0.0f ? element.width : fallbackWidth) * resolved.scale;
        resolved.height = (element.height > 0.0f ? element.height : fallbackHeight) * resolved.scale;
        resolved = resolveAttachedLayoutRect(
            element.attachTo,
            *parent,
            resolved.width,
            resolved.height,
            element.gapX,
            element.gapY,
            resolved.scale);
        visited.erase(layoutId);
        return resolved;
    }

    resolved.scale = std::clamp(baseScale, element.minScale, element.maxScale);
    resolved.width = (element.width > 0.0f ? element.width : fallbackWidth) * resolved.scale;
    resolved.height = (element.height > 0.0f ? element.height : fallbackHeight) * resolved.scale;

    switch (element.anchor)
    {
        case UiLayoutManager::LayoutAnchor::TopLeft:
            resolved.x = viewportX + element.offsetX * resolved.scale;
            resolved.y = viewportY + element.offsetY * resolved.scale;
            break;

        case UiLayoutManager::LayoutAnchor::TopCenter:
            resolved.x = viewportX + viewportWidth * 0.5f - resolved.width * 0.5f + element.offsetX * resolved.scale;
            resolved.y = viewportY + element.offsetY * resolved.scale;
            break;

        case UiLayoutManager::LayoutAnchor::TopRight:
            resolved.x = viewportX + viewportWidth - resolved.width + element.offsetX * resolved.scale;
            resolved.y = viewportY + element.offsetY * resolved.scale;
            break;

        case UiLayoutManager::LayoutAnchor::Left:
            resolved.x = viewportX + element.offsetX * resolved.scale;
            resolved.y = viewportY + viewportHeight * 0.5f - resolved.height * 0.5f + element.offsetY * resolved.scale;
            break;

        case UiLayoutManager::LayoutAnchor::Center:
            resolved.x = viewportX + viewportWidth * 0.5f - resolved.width * 0.5f + element.offsetX * resolved.scale;
            resolved.y = viewportY + viewportHeight * 0.5f - resolved.height * 0.5f + element.offsetY * resolved.scale;
            break;

        case UiLayoutManager::LayoutAnchor::Right:
            resolved.x = viewportX + viewportWidth - resolved.width + element.offsetX * resolved.scale;
            resolved.y = viewportY + viewportHeight * 0.5f - resolved.height * 0.5f + element.offsetY * resolved.scale;
            break;

        case UiLayoutManager::LayoutAnchor::BottomLeft:
            resolved.x = viewportX + element.offsetX * resolved.scale;
            resolved.y = viewportY + viewportHeight - resolved.height + element.offsetY * resolved.scale;
            break;

        case UiLayoutManager::LayoutAnchor::BottomCenter:
            resolved.x = viewportX + viewportWidth * 0.5f - resolved.width * 0.5f + element.offsetX * resolved.scale;
            resolved.y = viewportY + viewportHeight - resolved.height + element.offsetY * resolved.scale;
            break;

        case UiLayoutManager::LayoutAnchor::BottomRight:
            resolved.x = viewportX + viewportWidth - resolved.width + element.offsetX * resolved.scale;
            resolved.y = viewportY + viewportHeight - resolved.height + element.offsetY * resolved.scale;
            break;
    }

    visited.erase(layoutId);
    return resolved;
}

MenuScreenBase::Rect toRect(const ResolvedLayoutElement &resolved)
{
    return MenuScreenBase::Rect{
        std::round(resolved.x),
        std::round(resolved.y),
        std::round(resolved.width),
        std::round(resolved.height)
    };
}
}

LoadGameScreen::LoadGameScreen(
    const Engine::AssetFileSystem &assetFileSystem,
    const GameDataRepository &gameData,
    LoadAction loadAction,
    CancelAction cancelAction)
    : MenuScreenBase(assetFileSystem)
    , m_pGameData(&gameData)
    , m_loadAction(std::move(loadAction))
    , m_cancelAction(std::move(cancelAction))
{
}

AppMode LoadGameScreen::mode() const
{
    return AppMode::LoadMenu;
}

void LoadGameScreen::onEnter()
{
    refreshSaveSlots();
}

void LoadGameScreen::drawScreen(float deltaSeconds)
{
    static_cast<void>(deltaSeconds);

    ensureLayoutLoaded();
    const bool *pKeyboardState = SDL_GetKeyboardState(nullptr);
    const bool escapePressed = pKeyboardState != nullptr && pKeyboardState[SDL_SCANCODE_ESCAPE];
    const bool returnPressed = pKeyboardState != nullptr && pKeyboardState[SDL_SCANCODE_RETURN];

    if (escapePressed)
    {
        if (!m_escapePressed)
        {
            cancel();
            m_escapePressed = true;
            return;
        }
    }
    else
    {
        m_escapePressed = false;
    }

    if (returnPressed)
    {
        if (!m_returnPressed)
        {
            tryLoadSelectedSlot();
            m_returnPressed = true;
            return;
        }
    }
    else
    {
        m_returnPressed = false;
    }

    if (mouseWheelDelta() > 0.0f && m_scrollOffset > 0)
    {
        --m_scrollOffset;
    }
    else if (mouseWheelDelta() < 0.0f && m_scrollOffset + VisibleSlotCount < m_slots.size())
    {
        ++m_scrollOffset;
    }

    const Rect rootRect = resolveLayoutRect("LoadGameRoot", ReferenceWidth, ReferenceHeight).value_or(
        Rect{0.0f, 0.0f, ReferenceWidth, ReferenceHeight});

    drawViewportSidePanels("UI-Parch", ReferenceWidth, ReferenceHeight);
    drawTexture(resolveAssetName("LoadGameBackground", "Lsave640"), rootRect);

    if (const std::optional<Rect> titleRect = resolveLayoutRect("LoadGameTitle"))
    {
        drawTexture(resolveAssetName("LoadGameTitle", "bt_loagU"), *titleRect);
    }

    const ButtonState confirmButton = drawButton(
        resolveButtonVisuals("LoadGameConfirmButton", ButtonVisualSet{"bt_loadU", "bt_loadH", "bt_loadD"}),
        resolveLayoutRect("LoadGameConfirmButton", 106.0f, 37.0f).value_or(Rect{}));
    const ButtonState cancelButton = drawButton(
        resolveButtonVisuals("LoadGameCancelButton", ButtonVisualSet{"bt_cnclU", "bt_cnclH", "bt_cnclD"}),
        resolveLayoutRect("LoadGameCancelButton", 106.0f, 37.0f).value_or(Rect{}));

    const std::optional<Rect> scrollUpRect = resolveLayoutRect("LoadGameScrollUpButton", 18.0f, 16.0f);
    const std::optional<Rect> scrollDownRect = resolveLayoutRect("LoadGameScrollDownButton", 18.0f, 16.0f);
    const std::optional<Rect> previewRect = resolveLayoutRect("LoadGamePreviewRect", 272.0f, 169.0f);
    const std::optional<Rect> thumbRect = resolveLayoutRect("LoadGameScrollThumb", 17.0f, 17.0f);

    if (scrollUpRect && hitTest(*scrollUpRect) && leftMouseJustReleased() && m_scrollOffset > 0)
    {
        --m_scrollOffset;
    }

    if (scrollDownRect
        && hitTest(*scrollDownRect)
        && leftMouseJustReleased()
        && m_scrollOffset + VisibleSlotCount < m_slots.size())
    {
        ++m_scrollOffset;
    }

    if (previewRect)
    {
        static const std::vector<uint8_t> blackPixel = {0, 0, 0, 255};
        drawPixelsBgra("__load_game_preview_backdrop__", 1, 1, blackPixel, *previewRect);

        if (!m_slots.empty())
        {
            const SaveSlotSummary &slot = m_slots[std::min(m_selectedIndex, m_slots.size() - 1)];

            if (slot.previewWidth > 0 && slot.previewHeight > 0 && !slot.previewPixelsBgra.empty())
            {
                const float previewScale = std::min(
                    previewRect->width / static_cast<float>(slot.previewWidth),
                    previewRect->height / static_cast<float>(slot.previewHeight));
                const float drawWidth = static_cast<float>(slot.previewWidth) * previewScale;
                const float drawHeight = static_cast<float>(slot.previewHeight) * previewScale;
                const Rect drawRect = {
                    std::round(previewRect->x + (previewRect->width - drawWidth) * 0.5f),
                    std::round(previewRect->y + (previewRect->height - drawHeight) * 0.5f),
                    std::round(drawWidth),
                    std::round(drawHeight)
                };
                drawPixelsBgra(
                    "__load_game_preview__",
                    slot.previewWidth,
                    slot.previewHeight,
                    slot.previewPixelsBgra,
                    drawRect);
            }
        }
    }

    if (thumbRect && scrollUpRect && scrollDownRect)
    {
        float thumbY = thumbRect->y;

        if (m_slots.size() > VisibleSlotCount)
        {
            const float trackTop = scrollUpRect->y + scrollUpRect->height;
            const float trackBottom = scrollDownRect->y;
            const float travel = std::max(0.0f, trackBottom - trackTop - thumbRect->height);
            const float maxOffset = static_cast<float>(m_slots.size() - VisibleSlotCount);
            const float t = maxOffset > 0.0f ? static_cast<float>(m_scrollOffset) / maxOffset : 0.0f;
            thumbY = std::round(trackTop + travel * t);
        }

        Rect drawRect = *thumbRect;
        drawRect.y = thumbY;
        drawTexture(resolveAssetName("LoadGameScrollThumb", "but_thum"), drawRect);
    }

    bool shouldLoadSelectedSlot = false;

    for (size_t row = 0; row < VisibleSlotCount; ++row)
    {
        const size_t slotIndex = m_scrollOffset + row;
        const std::string layoutId = "LoadGameSlotRow" + std::to_string(row);
        const std::optional<Rect> rowRect = resolveLayoutRect(layoutId, 205.0f, 22.0f);

        if (!rowRect)
        {
            continue;
        }

        if (hitTest(*rowRect) && leftMouseJustReleased() && slotIndex < m_slots.size())
        {
            m_selectedIndex = slotIndex;
            const uint64_t nowTicks = SDL_GetTicks();

            if (m_lastClickedSlotIndex == slotIndex
                && nowTicks - m_lastClickedSlotTicks <= SlotDoubleClickWindowMs)
            {
                shouldLoadSelectedSlot = true;
            }

            m_lastClickedSlotIndex = slotIndex;
            m_lastClickedSlotTicks = nowTicks;
        }

        if (slotIndex >= m_slots.size() || m_slots[slotIndex].fileLabel.empty())
        {
            continue;
        }

        const uint32_t rowColor = slotIndex == std::min(m_selectedIndex, m_slots.size() - 1)
            ? SelectedRowColorAbgr
            : WhiteColorAbgr;
        drawLayoutText(layoutId, m_slots[slotIndex].fileLabel, rowColor);
    }

    if (!m_slots.empty())
    {
        const SaveSlotSummary &slot = m_slots[std::min(m_selectedIndex, m_slots.size() - 1)];
        drawLayoutText("LoadGameSelectedName", slot.locationName);
        drawLayoutText("LoadGamePreviewLine1", slot.weekdayClockText);
        drawLayoutText("LoadGamePreviewLine2", slot.dateText);
    }

    if (confirmButton.clicked)
    {
        shouldLoadSelectedSlot = true;
    }

    if (cancelButton.clicked)
    {
        cancel();
        return;
    }

    if (shouldLoadSelectedSlot)
    {
        tryLoadSelectedSlot();
        return;
    }
}

void LoadGameScreen::refreshSaveSlots()
{
    m_slots.clear();
    std::filesystem::create_directories("saves");

    for (const std::filesystem::directory_entry &entry : std::filesystem::directory_iterator("saves"))
    {
        if (!entry.is_regular_file() || toLowerCopy(entry.path().extension().string()) != ".oysav")
        {
            continue;
        }

        std::string error;
        const std::optional<GameSaveData> saveData = loadGameDataFromPath(entry.path(), error);

        if (!saveData)
        {
            continue;
        }

        SaveSlotSummary slot = {};
        slot.path = entry.path();
        slot.fileLabel = !saveData->saveName.empty() ? saveData->saveName : friendlySaveFileLabel(entry.path());
        slot.locationName = saveData->mapFileName;
        slot.populated = true;
        const CivilTime civilTime = civilTimeFromGameMinutes(saveData->savedGameMinutes);
        slot.weekdayClockText = formatClock(civilTime);
        slot.dateText = formatDate(civilTime);

        if (m_pGameData != nullptr)
        {
            for (const MapStatsEntry &entryMap : m_pGameData->mapEntries())
            {
                if (toLowerCopy(entryMap.fileName) == toLowerCopy(saveData->mapFileName))
                {
                    slot.locationName = entryMap.name;
                    break;
                }
            }
        }

        if (!saveData->previewBmp.empty())
        {
            decodeBmpBytesToBgra(
                saveData->previewBmp,
                slot.previewWidth,
                slot.previewHeight,
                slot.previewPixelsBgra);
        }

        m_slots.push_back(std::move(slot));
    }

    std::sort(
        m_slots.begin(),
        m_slots.end(),
        [](const SaveSlotSummary &left, const SaveSlotSummary &right)
        {
            return compareSavePathsForDisplay(left.path, right.path);
        });

    if (m_selectedIndex >= m_slots.size())
    {
        m_selectedIndex = 0;
    }

    m_scrollOffset = 0;
    m_lastClickedSlotIndex = static_cast<size_t>(-1);
    m_lastClickedSlotTicks = 0;
}

bool LoadGameScreen::tryLoadSelectedSlot()
{
    if (m_slots.empty() || m_selectedIndex >= m_slots.size() || !m_loadAction)
    {
        return false;
    }

    return m_loadAction(m_slots[m_selectedIndex].path);
}

void LoadGameScreen::cancel()
{
    if (m_cancelAction)
    {
        m_cancelAction();
    }
}

bool LoadGameScreen::ensureLayoutLoaded()
{
    if (m_layoutLoaded)
    {
        return true;
    }

    m_layoutManager.clear();
    m_layoutLoaded = m_layoutManager.loadLayoutFile(assetFileSystem(), LoadGameLayoutPath);
    return m_layoutLoaded;
}

std::optional<MenuScreenBase::Rect> LoadGameScreen::resolveLayoutRect(
    const std::string &layoutId,
    float fallbackWidth,
    float fallbackHeight) const
{
    if (!m_layoutLoaded)
    {
        return std::nullopt;
    }

    std::unordered_set<std::string> visited;
    const std::optional<ResolvedLayoutElement> resolved = resolveLayoutElementRecursive(
        m_layoutManager,
        layoutId,
        frameWidth(),
        frameHeight(),
        fallbackWidth,
        fallbackHeight,
        visited);

    if (!resolved.has_value())
    {
        return std::nullopt;
    }

    return toRect(*resolved);
}

MenuScreenBase::ButtonVisualSet LoadGameScreen::resolveButtonVisuals(
    const std::string &layoutId,
    const ButtonVisualSet &fallbackVisuals) const
{
    if (!m_layoutLoaded)
    {
        return fallbackVisuals;
    }

    const UiLayoutManager::LayoutElement *pLayout = m_layoutManager.findElement(layoutId);

    if (pLayout == nullptr)
    {
        return fallbackVisuals;
    }

    ButtonVisualSet visuals = fallbackVisuals;

    if (!pLayout->primaryAsset.empty())
    {
        visuals.defaultTextureName = pLayout->primaryAsset;
    }

    if (!pLayout->hoverAsset.empty())
    {
        visuals.highlightedTextureName = pLayout->hoverAsset;
    }

    if (!pLayout->pressedAsset.empty())
    {
        visuals.pressedTextureName = pLayout->pressedAsset;
    }

    return visuals;
}

std::string LoadGameScreen::resolveAssetName(const std::string &layoutId, const std::string &fallbackAssetName) const
{
    if (!m_layoutLoaded)
    {
        return fallbackAssetName;
    }

    const UiLayoutManager::LayoutElement *pLayout = m_layoutManager.findElement(layoutId);

    if (pLayout == nullptr || pLayout->primaryAsset.empty())
    {
        return fallbackAssetName;
    }

    return pLayout->primaryAsset;
}

void LoadGameScreen::drawLayoutText(
    const std::string &layoutId,
    const std::string &text,
    uint32_t colorAbgrOverride) const
{
    if (!m_layoutLoaded || text.empty())
    {
        return;
    }

    const UiLayoutManager::LayoutElement *pLayout = m_layoutManager.findElement(layoutId);

    if (pLayout == nullptr)
    {
        return;
    }

    std::unordered_set<std::string> visited;
    const std::optional<ResolvedLayoutElement> resolved = resolveLayoutElementRecursive(
        m_layoutManager,
        layoutId,
        frameWidth(),
        frameHeight(),
        0.0f,
        0.0f,
        visited);

    if (!resolved.has_value())
    {
        return;
    }

    const std::string fontName = pLayout->fontName.empty() ? "Create" : pLayout->fontName;
    const uint32_t color = colorAbgrOverride != 0 ? colorAbgrOverride : pLayout->textColorAbgr;
    const float fontScale = resolved->scale * std::max(0.1f, pLayout->textScale);
    const float padX = pLayout->textPadX * resolved->scale;
    const float padY = pLayout->textPadY * resolved->scale;
    float drawX = resolved->x + padX;
    float drawY = resolved->y + padY;
    LoadGameScreen *pMutableScreen = const_cast<LoadGameScreen *>(this);
    const float textWidth = pMutableScreen->measureTextWidth(fontName, text, fontScale);
    const float textHeight = static_cast<float>(pMutableScreen->fontHeight(fontName)) * fontScale;

    if (pLayout->textAlignX == UiLayoutManager::TextAlignX::Center)
    {
        drawX = resolved->x + (resolved->width - textWidth) * 0.5f + padX;
    }
    else if (pLayout->textAlignX == UiLayoutManager::TextAlignX::Right)
    {
        drawX = resolved->x + resolved->width - textWidth - padX;
    }

    if (pLayout->textAlignY == UiLayoutManager::TextAlignY::Middle)
    {
        drawY = resolved->y + (resolved->height - textHeight) * 0.5f + padY;
    }
    else if (pLayout->textAlignY == UiLayoutManager::TextAlignY::Bottom)
    {
        drawY = resolved->y + resolved->height - textHeight - padY;
    }

    pMutableScreen->drawText(fontName, text, drawX, drawY, color, fontScale);
}
}
