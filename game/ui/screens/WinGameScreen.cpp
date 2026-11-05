#include "game/ui/screens/WinGameScreen.h"

#include "engine/Utf8Text.h"

#include <SDL3/SDL.h>

#include <algorithm>
#include <cmath>
#include <string>

namespace OpenYAMM::Game
{
namespace
{
// OpenYAMM's certificate art and the zones its painting keeps (level_generation/ui/certificates_20261031).
constexpr float DesignArtWidth = 1536.0f;
constexpr float DesignArtHeight = 1024.0f;
constexpr float DesignSealCenterX = 768.0f;
constexpr float DesignSealCenterY = 132.0f;
constexpr float DesignSealSize = 120.0f;
constexpr float DesignTextLeft = 330.0f;
constexpr float DesignTextRight = 1206.0f;
constexpr float DesignTextTop = 236.0f;
constexpr float DesignTextBottom = 900.0f;
// The installed grand painting's medallion ornaments start at y 766.
constexpr float GrandTextBottom = 750.0f;
// An original game's certificate background.
constexpr float OriginalArtWidth = 640.0f;
constexpr float OriginalArtHeight = 480.0f;
// Smallest share of the designed sizes a crowded certificate shrinks to.
constexpr float MinimumFit = 0.7f;
constexpr float CloseDelaySeconds = 0.6f;
constexpr const char *SealTexture = "hud_x2/menus/omenu_seal.png";
constexpr const char *HeadingFont = "fondamento";
constexpr const char *BodyFont = "alegreya_semibold";
constexpr const char *OriginalFont = "ENDGAME";
constexpr uint32_t InkColor = 0xff0e1d2bu;
constexpr uint32_t AccentColor = 0xff24557au;
constexpr uint32_t MutedColor = 0xff30465au;
constexpr uint32_t OriginalInkColor = 0xff0a121cu;
constexpr uint32_t OriginalMarkColor = 0xff2a4462u;
constexpr uint32_t ParchmentColor = 0xffb2d4e2u;
}

WinGameScreen::WinGameScreen(
    const Engine::AssetFileSystem &assetFileSystem,
    const CompletionCertificate &certificate,
    AppMode mode)
    : MenuScreenBase(assetFileSystem)
    , m_certificate(certificate)
    , m_mode(mode)
{
}

AppMode WinGameScreen::mode() const
{
    return m_mode;
}

bool WinGameScreen::shouldClose() const
{
    return m_shouldClose;
}

const CompletionCertificate &WinGameScreen::certificate() const
{
    return m_certificate;
}

std::optional<ScreenshotCaptureService::Region> WinGameScreen::takeCaptureRegion()
{
    // The second frame: the art and every font are loaded by then.
    if (m_captureTaken || m_drawnFrames < 2)
    {
        return std::nullopt;
    }

    m_captureTaken = true;
    return m_certificateRegion;
}

void WinGameScreen::handleSdlEvent(const SDL_Event &event)
{
    // The click or key that ended the ending movie must not close the certificate too.
    if (m_shownSeconds < CloseDelaySeconds)
    {
        return;
    }

    if (event.type == SDL_EVENT_KEY_DOWN
        && (event.key.key == SDLK_ESCAPE
            || event.key.key == SDLK_RETURN
            || event.key.key == SDLK_KP_ENTER
            || event.key.key == SDLK_SPACE))
    {
        m_shouldClose = true;
    }
    else if (event.type == SDL_EVENT_MOUSE_BUTTON_DOWN || event.type == SDL_EVENT_FINGER_UP)
    {
        m_shouldClose = true;
    }
}

std::string WinGameScreen::wordmark() const
{
    return m_certificate.rulesetLabel.empty() ? "OpenYAMM" : "OpenYAMM - " + m_certificate.rulesetLabel;
}

std::vector<WinGameScreen::TextLine> WinGameScreen::layoutLines(float zoneWidth)
{
    // Sizes in art units: OpenYAMM's 1536 x 1024 art, or an original's 640 x 480 in the original ENDGAME font.
    const bool original = m_certificate.originalLayout.declared;
    const float unit = original ? 0.32f : 1.0f;
    const char *pHeadingFont = original ? OriginalFont : HeadingFont;
    const char *pBodyFont = original ? OriginalFont : BodyFont;
    const uint32_t inkColor = original ? OriginalInkColor : InkColor;
    const uint32_t mutedColor = original ? OriginalInkColor : MutedColor;
    std::vector<TextLine> lines;
    bool header = true;
    const auto add =
        [&lines, &header, unit](const std::string &text, const char *pFont, float size, uint32_t color, float gapAbove)
        {
            if (!text.empty())
            {
                lines.push_back({text, pFont, size * unit, color, gapAbove * unit, header});
            }
        };

    if (!original)
    {
        add(wordmark(), HeadingFont, 42.0f, AccentColor, 0.0f);
        add("Certificate of Completion", BodyFont, 24.0f, AccentColor, 2.0f);
    }

    add(m_certificate.headline, pHeadingFont, original ? 76.0f : 62.0f, inkColor, original ? 0.0f : 14.0f);
    header = false;

    for (size_t index = 0; index < m_certificate.worldLines.size(); ++index)
    {
        add(m_certificate.worldLines[index], pBodyFont, 26.0f, mutedColor, index == 0 ? 12.0f : 2.0f);
    }

    const float partySize = original ? 60.0f : 27.0f;

    for (size_t index = 0; index < m_certificate.partyLines.size(); ++index)
    {
        add(m_certificate.partyLines[index], pBodyFont, partySize, inkColor, index == 0 ? 22.0f : 4.0f);
    }

    const float textSize = original ? 56.0f : 25.0f;
    const float textScale = textSize * unit / float(std::max(1, fontHeight(pBodyFont)));
    const std::vector<std::string> textLines = Engine::Utf8::wrap(m_certificate.text, zoneWidth,
        [this, pBodyFont, textScale](const std::string &line)
        {
            return measureTextWidth(pBodyFont, line, textScale);
        });

    for (size_t index = 0; index < textLines.size(); ++index)
    {
        add(textLines[index], pBodyFont, textSize, inkColor, index == 0 ? 22.0f : 4.0f);
    }

    const float resultSize = original ? 60.0f : 26.0f;

    if (original)
    {
        // The originals give the time and the score on lines of their own.
        add(m_certificate.timeLine, pBodyFont, resultSize, inkColor, 24.0f);
        add(m_certificate.scoreLine, pBodyFont, resultSize, inkColor, 6.0f);
    }
    else
    {
        std::string results = m_certificate.timeLine;

        if (!m_certificate.scoreLine.empty())
        {
            results += (results.empty() ? "" : "   \xc2\xb7   ") + m_certificate.scoreLine;
        }

        add(results, pBodyFont, resultSize, inkColor, 24.0f);
    }

    add(m_certificate.dateLine.empty() ? "" : "Completed on " + m_certificate.dateLine,
        pBodyFont, original ? 46.0f : 22.0f, mutedColor, 6.0f);
    return lines;
}

void WinGameScreen::drawScreen(float deltaSeconds)
{
    m_shownSeconds += deltaSeconds;
    const WorldCompletionDefinition::Layout &originalLayout = m_certificate.originalLayout;
    const bool original = originalLayout.declared;
    const float artWidth = original ? OriginalArtWidth : DesignArtWidth;
    const float artHeight = original ? OriginalArtHeight : DesignArtHeight;
    const float frameWidthPixels = float(frameWidth());
    const float frameHeightPixels = float(frameHeight());
    drawPixelsBgra("__wingame_black__", 1, 1, m_blackPixel, {0.0f, 0.0f, frameWidthPixels, frameHeightPixels});

    const float scale = std::min(frameWidthPixels / artWidth, frameHeightPixels / artHeight);
    const float artX = std::round((frameWidthPixels - artWidth * scale) * 0.5f);
    const float artY = std::round((frameHeightPixels - artHeight * scale) * 0.5f);
    const Rect artRect = {artX, artY, std::round(artWidth * scale), std::round(artHeight * scale)};
    m_certificateRegion = {
        artRect.x / frameWidthPixels,
        artRect.y / frameHeightPixels,
        artRect.width / frameWidthPixels,
        artRect.height / frameHeightPixels};

    if (textureSize(m_certificate.art))
    {
        drawTexture(m_certificate.art, artRect);
    }
    else
    {
        drawSolidRect(artRect, ParchmentColor);
    }

    if (original)
    {
        // The OpenYAMM mark: the seal and the wordmark beside it, centred on layout.mark.
        const float markHeight = originalLayout.mark[2] * scale;
        const float wordmarkScale = markHeight * 0.62f / float(std::max(1, fontHeight(HeadingFont)));
        const std::string markText = wordmark();
        const float wordmarkWidth = measureTextWidth(HeadingFont, markText, wordmarkScale);
        const float gap = markHeight * 0.18f;
        const float left = artX + originalLayout.mark[0] * scale - (markHeight + gap + wordmarkWidth) * 0.5f;
        const float top = artY + originalLayout.mark[1] * scale - markHeight * 0.5f;
        drawTexture(SealTexture, {left, top, markHeight, markHeight});
        drawText(HeadingFont, markText, std::round(left + markHeight + gap),
            std::round(top + markHeight * 0.2f), OriginalMarkColor, wordmarkScale, false);
    }
    else
    {
        const float sealSize = DesignSealSize * scale;
        drawTexture(
            SealTexture,
            {artX + DesignSealCenterX * scale - sealSize * 0.5f, artY + DesignSealCenterY * scale - sealSize * 0.5f,
             sealSize, sealSize});
    }

    // The header stays at the top of the zone and the rest is centred below it; the lines shrink together when a
    // large party or a long text would overrun the zone.
    const float zoneLeft = original ? originalLayout.text[0] : DesignTextLeft;
    const float zoneTop = original ? originalLayout.text[1] : DesignTextTop;
    const float zoneRight = original ? originalLayout.text[2] : DesignTextRight;
    const float designBottom = m_certificate.grand ? GrandTextBottom : DesignTextBottom;
    const float zoneBottom = original ? originalLayout.text[3] : designBottom;
    const float zoneWidth = zoneRight - zoneLeft;
    const float zoneHeight = zoneBottom - zoneTop;
    const std::vector<TextLine> lines = layoutLines(zoneWidth);
    float headerHeight = 0.0f;
    float bodyHeight = 0.0f;

    for (const TextLine &line : lines)
    {
        (line.header ? headerHeight : bodyHeight) += line.gapAbove + line.size;
    }

    const float fit = std::clamp(zoneHeight / std::max(1.0f, headerHeight + bodyHeight), MinimumFit, 1.0f);
    const float bodyOffset = std::max(0.0f, (zoneHeight - (headerHeight + bodyHeight) * fit) * 0.5f);
    float y = zoneTop;
    bool inHeader = true;

    for (const TextLine &line : lines)
    {
        if (inHeader && !line.header)
        {
            inHeader = false;
            y += bodyOffset;
        }

        y += line.gapAbove * fit;
        const float size = line.size * fit;
        const float textScale = size * scale / float(std::max(1, fontHeight(line.fontName)));
        const float width = measureTextWidth(line.fontName, line.text, textScale);
        const float x = std::round(artX + (zoneLeft + zoneWidth * 0.5f) * scale - width * 0.5f);
        drawText(line.fontName, line.text, x, std::round(artY + y * scale), line.colorAbgr, textScale, false);
        y += size;
    }

    ++m_drawnFrames;
}
}
