// The party creation sheet: approach C2 of level_generation/ui/party_creation_study_20261101 (c2.html). Regions come
// from character_creation.yml; rows inside them are laid out here in the mockup's 1600x900 pixels.
#include "game/ui/screens/NewGameScreen.h"

#include "engine/Localization.h"
#include "engine/Utf8Text.h"
#include "game/rules/GameRules.h"
#include "game/ui/GameplayUiSkin.h"

#include <algorithm>
#include <cmath>
#include <sstream>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
namespace
{
constexpr float BrowserToLogical = 8.0f / 15.0f;
// The mockup's Arrus and Lucida are the faithful TTFs at size-adjust 120%; Fondamento is unadjusted.
constexpr float FaithfulFontScale = 1.2f;
// The smallest share of its size a label is set at to fit its place (a longer language) before it is cut.
constexpr float MinimumFit = 0.6f;

// The voice lines a voice card plays.
constexpr std::array<std::pair<std::string_view, SpeechId>, 3> VoiceLines = {{
    {Engine::trNoop("Choose me"), SpeechId::SelectCharacter},
    {Engine::trNoop("Hello"), SpeechId::HelloDay},
    {Engine::trNoop("Yes"), SpeechId::Yes},
}};
// How long the pointer rests on a skill before its card opens (the right button opens it at once).
constexpr float SkillCardDelaySeconds = 0.35f;

// Colours (ABGR) from c2.html.
constexpr uint32_t Ivory = 0xffc6dfeau;
constexpr uint32_t NameText = 0xffc2e3f1u;
constexpr uint32_t ClassText = 0xff94c9e1u;
constexpr uint32_t RaceText = 0xff9ab3aeu;
constexpr uint32_t WarnText = 0xff5fa3e8u;
constexpr uint32_t OkText = 0xff86cf8fu;
constexpr uint32_t CaptionText = 0xff7f9793u;
constexpr uint32_t Gold = 0xff8dc5e1u;
constexpr uint32_t HoverEdge = 0xffc0f0ffu;
constexpr uint32_t PortraitEdge = 0xff527a8du;
constexpr uint32_t MarkerGold = 0xff86bfd8u;
constexpr uint32_t PointsText = 0xff91cfe9u;
constexpr uint32_t StatUp = 0xff9be3b9u;
constexpr uint32_t StatDown = 0xff8fa5f0u;
constexpr uint32_t TrendUp = 0xff7fd59fu;
constexpr uint32_t TrendDown = 0xff7a8feeu;
constexpr uint32_t Separator = 0x12ffffffu;
constexpr uint32_t TagFill = 0xff8ad3b7u;
constexpr uint32_t TagText = 0xff12140du;
constexpr uint32_t CardFill = 0xf712140bu;
constexpr uint32_t CardEdge = 0xff5d8da4u;
constexpr uint32_t ChevronColour = 0xff7aa2b9u;
constexpr uint32_t TitleText = 0xffa8d1e6u;
// The best mastery a skill reaches: grey Normal, white Expert, turquoise Master, gold Grandmaster.
constexpr std::array<uint32_t, 5> MasteryColours = {0xff6c766fu, 0xff929e9cu, 0xffe2ecf0u, 0xffccd88fu, 0xff4cc9f2u};
constexpr std::array<std::string_view, 5> MasteryNames = {"", Engine::trNoop("Normal"), Engine::trNoop("Expert"),
    Engine::trNoop("Master"), Engine::trNoop("Grandmaster")};

// A mastery's letter in the mastery tables.
std::string masteryLetter(SkillMastery mastery)
{
    switch (mastery)
    {
    case SkillMastery::Normal:
        return Engine::trc("mastery letter", "N");
    case SkillMastery::Expert:
        return Engine::trc("mastery letter", "E");
    case SkillMastery::Master:
        return Engine::trc("mastery letter", "M");
    case SkillMastery::Grandmaster:
        return Engine::trc("mastery letter", "G");
    default:
        return {};
    }
}

// The opacity of a skill that is no choice now, only later from a teacher.
constexpr uint32_t LaterSkillAlpha = 0x78;

uint32_t masteryColour(SkillMastery mastery)
{
    return MasteryColours[std::min<size_t>(size_t(mastery), MasteryColours.size() - 1)];
}

uint32_t mixColour(uint32_t from, uint32_t to, float t)
{
    uint32_t result = 0;

    for (int shift = 0; shift < 32; shift += 8)
    {
        const float a = float((from >> shift) & 0xff);
        const float b = float((to >> shift) & 0xff);
        result |= uint32_t(std::lround(a + (b - a) * t)) << shift;
    }

    return result;
}

// The first letters of a shown name ("Dwa" of "Dwarf"), whole characters of any language.
std::string firstLetters(const std::string &text, size_t count)
{
    size_t offset = 0;

    for (size_t letter = 0; letter < count && offset < text.size(); ++letter)
    {
        Engine::Utf8::next(text, offset);
    }

    return text.substr(0, offset);
}

// Capitals of the shown (translated) text: every letter, not only ASCII ones.
std::string upperCase(const std::string &text)
{
    return Engine::Utf8::upper(text);
}

std::string joinedNames(const std::vector<std::string> &names, const std::string &separator)
{
    std::string text;

    for (const std::string &name : names)
    {
        text += (text.empty() ? "" : separator) + name;
    }

    return text;
}

bool sameSkill(const std::vector<std::string> &skills, const std::string &skill)
{
    return std::find(skills.begin(), skills.end(), skill) != skills.end();
}
} // namespace

float NewGameScreen::sheetPx(float browserPixels) const
{
    return browserPixels * BrowserToLogical * designScale();
}

MenuScreenBase::Rect NewGameScreen::sheetRect(float x, float y, float width, float height) const
{
    return canvasRect(x * BrowserToLogical, y * BrowserToLogical, width * BrowserToLogical, height * BrowserToLogical);
}

void NewGameScreen::sheetText(const Rect &rect, const std::string &text, const std::string &font, float cssPixels,
                              uint32_t color, int align)
{
    float logicalSize = cssPixels * BrowserToLogical * (font == "fondamento" ? 1.0f : FaithfulFontScale);

    // A one-line label longer than its place (a longer language) is set smaller before it is cut with an ellipsis.
    if (text.find('\n') == std::string::npos && rect.height < logicalSize * designScale() * 1.9f)
    {
        const float full = measureTextWidth(font, text, designScale() * logicalSize / std::max(1, fontHeight(font)));

        if (full > rect.width && full > 0)
        {
            logicalSize *= std::max(MinimumFit, rect.width / full);
        }
    }

    if (align > 0)
    {
        const float width =
            measureTextWidth(font, text, designScale() * logicalSize / std::max(1, fontHeight(font)));
        const float shift = std::max(0.0f, rect.width - width);
        textInRect({rect.x + shift, rect.y, rect.width - shift, rect.height}, text, font, logicalSize, color);
        return;
    }

    textInRect(rect, text, font, logicalSize, color, align == 0);
}

float NewGameScreen::voiceLineSize(float rowWidth)
{
    const float u = sheetPx(1);
    float textWidth = 0;
    float fixedWidth = 0;

    for (const auto &[english, speech] : VoiceLines)
    {
        textWidth += sheetTextWidth(Engine::tr(english), "menu_lucida", 15);
        fixedWidth += 36 * u;
    }

    return textWidth + fixedWidth <= rowWidth || textWidth <= 0
        ? 15.0f
        : std::max(15.0f * MinimumFit, 15.0f * (rowWidth - fixedWidth) / textWidth);
}

float NewGameScreen::labelButtonWidth(const std::string &text, float minimum)
{
    // Buttons set their label in Fondamento at 13.87 logical pixels: 26 of the sheet's.
    return std::max(minimum, sheetTextWidth(text, "fondamento", 26) + sheetPx(34));
}

float NewGameScreen::sheetTextWidth(const std::string &text, const std::string &font, float cssPixels)
{
    const float logicalSize = cssPixels * BrowserToLogical * (font == "fondamento" ? 1.0f : FaithfulFontScale);
    return measureTextWidth(font, text, designScale() * logicalSize / std::max(1, fontHeight(font)));
}

void NewGameScreen::glyph(const std::string &name, const Rect &rect, uint32_t color)
{
    drawTextureColor("hud_x2/menus/omenu_glyph_" + name + ".png", rect, color);
}

void NewGameScreen::horizontalGradient(const Rect &rect, uint32_t left, uint32_t right)
{
    constexpr int Strips = 16;

    for (int strip = 0; strip < Strips; ++strip)
    {
        const float x0 = std::round(rect.x + rect.width * strip / Strips);
        const float x1 = std::round(rect.x + rect.width * (strip + 1) / Strips);
        drawSolidRect({x0, rect.y, x1 - x0, rect.height}, mixColour(left, right, (strip + 0.5f) / Strips));
    }
}

void NewGameScreen::verticalGradient(const Rect &rect, uint32_t top, uint32_t bottom)
{
    constexpr int Strips = 16;

    for (int strip = 0; strip < Strips; ++strip)
    {
        const float y0 = std::round(rect.y + rect.height * strip / Strips);
        const float y1 = std::round(rect.y + rect.height * (strip + 1) / Strips);
        drawSolidRect({rect.x, y0, rect.width, y1 - y0}, mixColour(top, bottom, (strip + 0.5f) / Strips));
    }
}

std::string NewGameScreen::voiceLabel(int voiceId) const
{
    // A named voice set (MM9's personalities) by its name, the others by number.
    if (m_pGameData != nullptr && voiceId >= 0)
    {
        const std::string name = m_pGameData->characterVoiceTable().voiceSetProperty(uint32_t(voiceId), "Name");

        if (!name.empty())
        {
            return Engine::localize(name, "voice");
        }
    }

    return Engine::tr("Voice {number}", {{"number", voiceDisplayNumber(voiceId)}});
}

int NewGameScreen::voiceDisplayNumber(int voiceId) const
{
    if (m_pGameData != nullptr)
    {
        uint32_t owner = 0;

        for (const auto &[id, entry] : m_pGameData->characterDollTable().characters())
        {
            if (int(entry.defaultVoiceId) == voiceId && (owner == 0 || id < owner))
            {
                owner = id;
            }
        }

        if (owner != 0)
        {
            return int(owner);
        }
    }

    return voiceId + 1;
}

void NewGameScreen::openSheetPopup(SheetPopup popup)
{
    endNameEditing(true);
    m_sheetPopup = popup;
    m_popupScroll = 0;
    m_popupContentHeight = 0;
    m_tableScroll = 0;
    m_tableContentHeight = 0;
    m_hoverSkill.clear();
    m_hoverSkillSeconds = 0;
}

void NewGameScreen::drawCharacterCreation(float deltaSeconds)
{
    initializeCharacterCreationForSelectedContinent();
    loadDesign("gameplay/character_creation");
    beginDesign("CharacterCreation");
    drawDesign();
    updateNameBackspaceRepeat(deltaSeconds);
    m_frameSeconds = deltaSeconds;
    m_help = {};
    const bool wasEditing = m_state.nameEditing;

    if (m_escapePressed && !modalOpen())
    {
        m_escapePressed = false;

        if (m_sheetPopup != SheetPopup::None)
        {
            m_sheetPopup = SheetPopup::None;
        }
        else if (wasEditing)
        {
            endNameEditing(true);
        }
        else
        {
            cancelCreation();
            return;
        }
    }

    if (m_returnPressed && wasEditing)
    {
        endNameEditing(true);
    }

    m_returnPressed = false;
    m_escapePressed = false;
    const bool input = m_sheetPopup == SheetPopup::None && !modalOpen();
    drawCreationHeader();
    drawCreationRoster(input);
    drawCreationIdentity(input);
    drawCreationAttributes(input);
    drawCreationRaceCard(input);
    drawCreationSkills(input, deltaSeconds);
    drawCreationDoll(input);
    saveActivePartyState();

    if (!drawCreationFooter(input))
    {
        return;
    }

    if (input && !m_hoverSkill.empty() && (m_hoverSkillSeconds >= SkillCardDelaySeconds || rightMouseDown()))
    {
        drawCreationSkillCard(m_hoverSkillSlot, m_hoverSkill, m_hoverSkillAnchor);
    }

    drawCreationHelp();

    switch (m_sheetPopup)
    {
    case SheetPopup::Portrait:
        drawPortraitPicker();
        break;
    case SheetPopup::Voice:
        drawVoicePicker();
        break;
    case SheetPopup::Class:
        drawClassPicker();
        break;
    case SheetPopup::MasteryTable:
        drawMasteryTablePopup();
        break;
    case SheetPopup::PartyBoard:
        drawPartyBoard();
        break;
    case SheetPopup::None:
        break;
    }

    drawConfirmation();
}

void NewGameScreen::drawCreationHeader()
{
    label("CharacterCreationContinent", Engine::localizeKnown(m_selectedContinent.name) + " · "
                                             + Engine::localize(chosenRulesetDefinition().name));
    size_t ready = 0;

    for (size_t slotIndex = 0; slotIndex < m_partySize; ++slotIndex)
    {
        ready += stateComplete(slotIndex == m_activePartySlot ? m_state : m_partyStates[slotIndex]) ? 1 : 0;
    }

    std::string summary;

    if (m_pGameData != nullptr && !isGodLichSelected())
    {
        const CreationPartyCoverage coverage =
            creationPartyCoverage(m_pGameData->classSkillTable(), creationPartyMembers());
        summary = Engine::tr("Party covers {covered} of {reachable} reachable skills · {grandmaster} to Grandmaster",
                             {{"covered", coverage.covered}, {"reachable", coverage.reachable},
                              {"grandmaster", coverage.grandmaster}})
            + " · ";
    }

    label("CharacterCreationPartySummary",
          summary + Engine::tr("{size} / 5 adventurers · {ready} ready", {{"size", m_partySize}, {"ready", ready}}));
}

void NewGameScreen::drawCreationRoster(bool input)
{
    const Rect roster = designRect("CharacterCreationRoster");
    const float u = sheetPx(1);
    const bool godLich = isGodLichSelected();

    for (size_t slotIndex = 0; slotIndex < m_partySize && slotIndex < m_partyStates.size(); ++slotIndex)
    {
        const CreationState &state = slotIndex == m_activePartySlot ? m_state : m_partyStates[slotIndex];
        const bool selected = slotIndex == m_activePartySlot;
        const Rect card{roster.x, roster.y + slotIndex * 137 * u, roster.width, 130 * u};
        const Rect portrait{card.x + 7 * u, card.y + 7 * u, 82 * u, 114 * u};
        const Hotspot cardInput = hotspot("card-" + std::to_string(slotIndex), card, input);
        skin(selected ? "save_row_selected" : "save_row", card, true);

        if (cardInput.hovered && !selected)
        {
            outline(card, 0xff6a8a9au);
        }

        drawSolidRect(portrait, 0xff10110au);

        if (const CharacterDollEntry *pEntry = characterEntryForState(state))
        {
            drawTexture(portraitTextureNameForEntry(*pEntry), portrait);
        }

        outline(portrait, PortraitEdge);

        // The selected adventurer's portrait opens the portrait grid.
        const bool portraitHover = selected && input && !godLich && pointerInside(portrait);

        if (portraitHover)
        {
            const Rect bar{portrait.x, portrait.y + portrait.height - 17 * u, portrait.width, 17 * u};
            drawSolidRect(bar, 0xcc0e100bu);
            sheetText(bar, Engine::tr("change"), "menu_lucida", 13, NameText, 0);
        }

        const float textX = card.x + 97 * u;
        const float textWidth = card.x + card.width - textX - 30 * u;
        sheetText({textX, card.y + 7 * u, textWidth, 26 * u}, state.name, "menu_arrus", 20, NameText);
        const std::string className = classNameForState(state);
        drawTexture(classIconTextureName(className), {textX, card.y + 36 * u, 20 * u, 20 * u});
        sheetText({textX + 24 * u, card.y + 34 * u, textWidth + 4 * u, 24 * u},
                  Engine::localize(displayClassName(className)), "fondamento", 17, ClassText);
        const CharacterDollEntry *pEntry = characterEntryForState(state);
        const bool female = pEntry != nullptr && pEntry->defaultSex == 1;
        sheetText({textX, card.y + 60 * u, card.x + card.width - textX - 6 * u, 18 * u},
                  Engine::localizeKnown(candidateForState(state).raceName) + " · "
                      + (female ? Engine::tr("female") : Engine::tr("male")),
                  "menu_lucida", 13, RaceText);

        const int pool = bonusPoolForState(state);
        const size_t required = requiredSkillCount(state);
        const size_t skillsLeft = required - std::min(required, state.selectedOptionalSkills.size());
        const Rect status{textX, card.y + 90 * u, card.x + card.width - textX - 6 * u, 34 * u};

        if (stateComplete(state))
        {
            glyph("check", {textX, status.y + status.height / 2 - 6 * u, 12 * u, 12 * u}, OkText);
            sheetText({textX + 16 * u, status.y, status.width - 16 * u, status.height}, Engine::tr("ready"),
                      "menu_lucida", 13, OkText);
        }
        else
        {
            std::vector<std::string> parts;

            if (pool > 0)
            {
                parts.push_back(Engine::tr("{points} pts", {{"points", pool}}));
            }

            if (skillsLeft > 0)
            {
                parts.push_back(Engine::trn("{count} skill", "{count} skills", skillsLeft, {{"count", skillsLeft}}));
            }

            sheetText(status,
                      parts.empty() ? Engine::tr("needs a name")
                                    : Engine::tr("{left} to go", {{"left", joinedNames(parts, " · ")}}),
                      "menu_lucida", 13, WarnText);
        }

        if (selected)
        {
            glyph("play", {card.x + card.width + 1 * u, card.y + card.height / 2 - 9 * u, 10 * u, 18 * u}, Gold);
        }

        // The corner minus removes this adventurer.
        if (m_partySize > 1 && !godLich)
        {
            const Rect remove{card.x + card.width - 28 * u, card.y + 4 * u, 24 * u, 24 * u};
            const Hotspot removeInput = hotspot("remove-" + std::to_string(slotIndex), remove, input);
            drawSolidRect(remove, 0xe614160eu);
            outline(remove, removeInput.hovered ? 0xff7582eeu : 0xff4a5a5bu);
            glyph("minus", {remove.x + 5 * u, remove.y + 5 * u, 14 * u, 14 * u},
                  removeInput.hovered ? 0xff7582eeu : 0xff9ab0b8u);

            if (removeInput.activated)
            {
                removePartySlotAt(slotIndex);
                return;
            }
        }

        if (cardInput.activated)
        {
            if (selected && !godLich && pointerInside(portrait))
            {
                openSheetPopup(SheetPopup::Portrait);
            }
            else
            {
                switchActivePartySlot(slotIndex);
            }

            return;
        }
    }

    if (m_partySize < 5 && !godLich)
    {
        const Rect add{roster.x, roster.y + m_partySize * 137 * u, roster.width, 70 * u};
        const Hotspot addInput = hotspot("add-adventurer", add, input);
        skin("save_row", add, true);
        outline(add, addInput.hovered ? Gold : 0xff4a5649u);
        sheetText(add, Engine::tr("+ Add adventurer"), "fondamento", 22, addInput.hovered ? HoverEdge : 0xff93aeb6u, 0);

        if (addInput.activated)
        {
            addPartySlot();
        }
    }
}

void NewGameScreen::drawCreationIdentity(bool input)
{
    const float u = sheetPx(1);
    const bool godLich = isGodLichSelected();
    const Rect nameRect = designRect("CharacterCreationNameField");

    if (m_state.nameEditing && (keyPressed(SDL_SCANCODE_TAB) || (leftMouseJustPressed() && !pointerInside(nameRect))))
    {
        endNameEditing(true);
    }

    if (button("name", nameRect, "", "text_field", input && !godLich))
    {
        beginNameEditing();
    }

    sheetText({nameRect.x + 10 * u, nameRect.y, nameRect.width - 20 * u, nameRect.height},
              m_state.nameEditing ? m_state.nameEditBuffer + "_" : m_state.name, "menu_arrus", 23, NameText);
    setTextEditing(m_state.nameEditing);

    const Rect classRect = designRect("CharacterCreationClassValue");
    const bool classEnabled = input && !godLich && !selectedCandidate().availableClassIds.empty();

    if (button("class", classRect, "", "button_quiet", classEnabled))
    {
        m_classPreviewId = m_state.selectedClassId;
        openSheetPopup(SheetPopup::Class);
    }

    drawTexture(classIconTextureName(selectedClassName()),
                {classRect.x + 10 * u, classRect.y + (classRect.height - 34 * u) / 2, 34 * u, 34 * u});
    sheetText({classRect.x + 54 * u, classRect.y, classRect.width - 90 * u, classRect.height},
              Engine::localize(displayClassName(selectedClassName())), "fondamento", 27,
              pointerInside(classRect) && classEnabled
                  ? HoverEdge : 0xffa6d5ecu);
    drawTextureColor("hud_x2/menus/omenu_chevron_down.png",
                     {classRect.x + classRect.width - 28 * u, classRect.y + classRect.height / 2 - 5 * u, 15 * u,
                      10 * u}, ChevronColour);

    if (rightMouseDown() && input && pointerInside(classRect) && m_pGameData != nullptr)
    {
        if (const ClassInspectEntry *pHelp = m_pGameData->characterInspectTable().getClass(selectedClassName()))
        {
            m_help.title = Engine::localize(pHelp->name);
            m_help.body = Engine::localize(pHelp->description);
            m_help.anchor = classRect;

            if (creationRules().classes.showsCreationSkillMatrix())
            {
                m_help.lines = creationSkillMatrixLines(buildCharacter());
            }
        }
    }

    // The voice card: the title opens the voice picker, the lines play the voice.
    const Rect voice = designRect("CharacterCreationVoiceCard");
    drawSolidRect(voice, 0xff171910u);
    outline(voice, 0xff4d5b53u);
    const Rect title{voice.x + 8 * u, voice.y + 5 * u, voice.width - 16 * u, 30 * u};
    const Hotspot titleInput = hotspot("voice", title, input && !godLich);
    sheetText({title.x + 2 * u, title.y, title.width - 30 * u, title.height},
              voiceLabel(m_state.selectedVoiceId), "fondamento", 22,
              titleInput.hovered ? HoverEdge : 0xffa3d3eau);
    drawTextureColor("hud_x2/menus/omenu_chevron_down.png",
                     {title.x + title.width - 22 * u, title.y + title.height / 2 - 5 * u, 15 * u, 10 * u},
                     titleInput.hovered ? HoverEdge : ChevronColour);

    if (titleInput.activated)
    {
        openSheetPopup(SheetPopup::Voice);
    }

    float x = voice.x + 10 * u;
    const float lineSize = voiceLineSize(voice.width - 20 * u);

    for (const auto &[english, speech] : VoiceLines)
    {
        const std::string text = Engine::tr(english);
        const float width = sheetTextWidth(text, "menu_lucida", lineSize) + 30 * u;
        const Rect line{x, voice.y + 42 * u, width, 30 * u};
        const Hotspot lineInput = hotspot("line-" + std::string(english), line, input);
        drawSolidRect(line, 0xff1b1d12u);
        outline(line, lineInput.hovered ? PointsText : 0xff50615au);
        glyph("play", {line.x + 7 * u, line.y + line.height / 2 - 5 * u, 9 * u, 10 * u}, 0xff84bdd6u);
        sheetText({line.x + 20 * u, line.y, width - 24 * u, line.height}, text, "menu_lucida", lineSize,
                  lineInput.hovered ? HoverEdge : 0xffb5cfd9u);

        if (lineInput.activated)
        {
            playCreationVoiceLine(m_state.selectedVoiceId, speech);
        }

        x += width + 6 * u;
    }
}

void NewGameScreen::drawCreationAttributes(bool input)
{
    const float u = sheetPx(1);
    const Rect area = designRect("CharacterCreationAttributes");
    const bool godLich = isGodLichSelected();
    const int pool = currentBonusPool();
    sheetText({area.x, area.y, area.width, 22 * u},
              godLich ? Engine::tr("Preset")
                      : Engine::trn("{count} bonus point left", "{count} bonus points left",
                                    uint64_t(std::max(0, pool)), {{"count", pool}}),
              "menu_lucida", 18, pool == 0 || godLich ? OkText : PointsText, 1);
    const std::array<RaceStatLine, CreationStatCount> lines = raceStatLinesForState(m_state);
    const Character preset = godLich ? buildCharacter() : Character{};

    for (size_t index = 0; index < CreationStatCount; ++index)
    {
        const Rect row{area.x, area.y + (22 + index * 34) * u, area.width, 34 * u};
        const Rect plus{row.x + row.width - 44 * u, row.y + 1.5f * u, 44 * u, 31 * u};
        const Rect value{plus.x - 46 * u, row.y, 40 * u, row.height};
        const Rect minus{value.x - 50 * u, plus.y, 44 * u, 31 * u};
        const Rect trend{minus.x - 20 * u, row.y + row.height / 2 - 6 * u, 12 * u, 12 * u};
        const Rect name{row.x, row.y, trend.x - row.x - 4 * u, row.height};
        sheetText(name, Engine::tr(creationStatNames()[index]), "menu_arrus", 21, Ivory);

        if (raceStatTrend(lines[index]) > 0)
        {
            glyph("up", trend, TrendUp);
        }
        else if (raceStatTrend(lines[index]) < 0)
        {
            glyph("down", trend, TrendDown);
        }

        const int current = m_state.currentStats[index];
        const int base = m_state.baseStats[index];
        const std::array<uint32_t, 7> presetValues = {preset.might, preset.intellect, preset.personality,
                                                      preset.endurance, preset.accuracy, preset.speed, preset.luck};
        sheetText(value, std::to_string(godLich ? int(presetValues[index]) : current), "menu_arrus", 23,
                  current > base ? StatUp : current < base ? StatDown : Ivory, 0);

        if (button("dec-" + std::to_string(index), minus, "", "button_square", input && !godLich))
        {
            tryDecreaseStat(StatId(index));
        }

        sheetText(minus, "-", "menu_arrus", 24, input && !godLich ? Ivory : 0xff6b777au, 0);

        if (button("inc-" + std::to_string(index), plus, "", "button_square", input && !godLich && pool > 0))
        {
            tryIncreaseStat(StatId(index));
        }

        sheetText(plus, "+", "menu_arrus", 24, input && !godLich && pool > 0 ? Ivory : 0xff6b777au, 0);

        if (rightMouseDown() && input && pointerInside(name) && m_pGameData != nullptr)
        {
            if (const StatInspectEntry *pHelp =
                    m_pGameData->characterInspectTable().getStat(creationStatNames()[index]))
            {
                m_help.title = Engine::localize(pHelp->name);
                m_help.body = Engine::localize(pHelp->description);
                m_help.anchor = name;
                m_help.lines.emplace_back(
                    Engine::tr("{race}: {base}, {trend}, max {maximum}",
                               {{"race", Engine::localizeKnown(selectedCandidate().raceName)},
                                {"base", lines[index].base}, {"trend", raceStatTrendText(lines[index])},
                                {"maximum", lines[index].maximum}}),
                    GameplayUiSkin::Low);
            }
        }
    }
}

void NewGameScreen::drawCreationRaceCard(bool input)
{
    if (m_pGameData == nullptr)
    {
        return;
    }

    const float u = sheetPx(1);
    const Rect card = designRect("CharacterCreationRaceCard");
    verticalGradient(card, 0xe01c2a1bu, 0xe014170fu);
    outline(card, 0xff4c6b5du);
    const Character character = buildCharacter();
    const std::string raceName = m_pGameData->mergedCharacterSelectionTable().raceNameForId(character.raceId).value_or(
        selectedCandidate().raceName);
    sheetText({card.x + 12 * u, card.y + 4 * u, card.width - 24 * u, 32 * u}, Engine::localizeKnown(raceName),
              "fondamento", 26,
              0xffb7e7d9u);
    const std::vector<RaceCardLine> lines =
        raceCardLines(raceStatLinesForState(m_state), creationStatNames(),
                      m_pGameData->mergedRaceSkillTable().overrides(), character.raceId,
                      m_pGameData->classSkillTable(), creationRules().classes.raceNotes(character));
    const float textSize = 14 * BrowserToLogical * FaithfulFontScale;

    if (m_raceCardRaceId != character.raceId)
    {
        m_raceCardRaceId = character.raceId;
        m_raceCardScroll = 0;
    }

    // The lines below the race name; a race with more rules than fit scrolls them, and the text then leaves room
    // for the scrollbar.
    const Rect viewport{card.x + 1 * u, card.y + 38 * u, card.width - 2 * u, card.height - 39 * u};
    const auto contentHeight = [&](float textWidth)
    {
        float height = 0;

        for (const RaceCardLine &line : lines)
        {
            height += 8 * u + textBlockHeight(line.text, "menu_lucida", textSize, textWidth);
        }

        return height;
    };
    float textWidth = card.width - 44 * u;
    const bool scrolls = contentHeight(textWidth) > viewport.height;

    if (scrolls)
    {
        textWidth -= 12 * designScale();
    }

    scrollViewport(viewport, contentHeight(textWidth) / designScale(), m_raceCardScroll, 30, input);
    const float ruleWidth = card.width - 24 * u - (scrolls ? 12 * designScale() : 0);
    float y = viewport.y - m_raceCardScroll * designScale();
    setDesignClip(viewport);

    for (const RaceCardLine &line : lines)
    {
        const float height = textBlockHeight(line.text, "menu_lucida", textSize, textWidth);
        drawSolidRect({card.x + 12 * u, y, ruleWidth, std::max(1.0f, designScale() * 0.5f)}, Separator);
        y += 4 * u;
        uint32_t color = 0xff6c766fu;
        const Rect mark{card.x + 13 * u, y + 1 * u, 12 * u, 12 * u};

        switch (line.kind)
        {
        case RaceCardLine::Kind::Even:
            sheetText({mark.x, y, 14 * u, 14 * u}, "=", "menu_lucida", 14, color, 0);
            break;
        case RaceCardLine::Kind::Strong:
            color = 0xff87dca8u;
            glyph("up", mark, color);
            break;
        case RaceCardLine::Kind::Weak:
            color = 0xff8ba0f0u;
            glyph("down", mark, color);
            break;
        case RaceCardLine::Kind::Skill:
            color = 0xff8ad3b7u;
            glyph("star", mark, color);
            break;
        case RaceCardLine::Kind::Note:
            color = 0xffe0cf9fu;
            glyph("spark", mark, color);
            break;
        }

        textInRect({card.x + 32 * u, y, textWidth, height}, line.text, "menu_lucida", textSize, color);
        y += height + 4 * u;
    }

    setDesignClip(std::nullopt);
}

void NewGameScreen::drawCreationSkills(bool input, float deltaSeconds)
{
    const float u = sheetPx(1);
    const Rect panel = designRect("CharacterCreationSkills");
    skin("world_card", panel, true);
    const bool godLich = isGodLichSelected();

    // Header: the title again over the panel, picks, the legend and the two tables.
    label("CharacterCreationSkillsTitle", Engine::tr("Skills"));
    const Rect title = designRect("CharacterCreationSkillsTitle");
    float x = title.x + sheetTextWidth(Engine::tr("Skills"), "fondamento", 25) + 12 * u;
    const size_t required = requiredSkillCount(m_state);

    if (!godLich)
    {
        const std::string picks = required == 0 ? Engine::tr("no choices")
            : Engine::tr("{picked} of {required} picked",
                         {{"picked", m_state.selectedOptionalSkills.size()}, {"required", required}});
        const bool done = m_state.selectedOptionalSkills.size() >= required;
        sheetText({x, title.y, 120 * u, title.height}, picks, "menu_lucida", 15, done ? OkText : PointsText);
        x += sheetTextWidth(picks, "menu_lucida", 15) + 16 * u;
        // The legend: what the marks mean and the mastery colours, set smaller when a longer language would run it
        // under the buttons at the panel's right.
        struct LegendItem
        {
            const char *pGlyph = nullptr;
            std::string text;
            uint32_t color = 0;
        };
        std::vector<LegendItem> items = {{"diamond", Engine::tr("starting"), 0xff9aa9a9u},
                                         {"ring", Engine::tr("can pick"), 0xff9aa9a9u}};

        for (size_t level = 1; level < MasteryNames.size(); ++level)
        {
            items.push_back({nullptr, Engine::tr(MasteryNames[level]), MasteryColours[level]});
        }

        float textWidth = 0;
        float fixedWidth = 0;

        for (const LegendItem &item : items)
        {
            textWidth += sheetTextWidth(item.text, "menu_lucida", 13);
            fixedWidth += (item.pGlyph != nullptr ? 13 * u : 0) + 9 * u;
        }

        const float available = designRect("CharacterCreationMasteryTableButton").x - 8 * u - x;
        const float size = textWidth + fixedWidth <= available || textWidth <= 0
            ? 13.0f
            : std::max(13.0f * 0.5f, 13.0f * (available - fixedWidth) / textWidth);

        for (const LegendItem &item : items)
        {
            if (item.pGlyph != nullptr)
            {
                glyph(item.pGlyph, {x, title.y + title.height / 2 - 5 * u, 10 * u, 10 * u}, MarkerGold);
                x += 13 * u;
            }

            const float width = sheetTextWidth(item.text, "menu_lucida", size);
            sheetText({x, title.y, width + 2 * u, title.height}, item.text, "menu_lucida", size, item.color);
            x += width + 9 * u;
        }
    }

    if (action("CharacterCreationMasteryTableButton", input && !godLich))
    {
        openSheetPopup(SheetPopup::MasteryTable);
    }

    if (action("CharacterCreationPartyBoardButton", input && !godLich))
    {
        openSheetPopup(SheetPopup::PartyBoard);
    }

    const Rect list{panel.x + 12 * u, panel.y + 44 * u, panel.width - 24 * u, 368 * u};

    if (godLich)
    {
        sheetText(list,
                  Engine::tr("All skills - Grandmaster\n"
                             "Every skill is granted at level 200 and all spells are learned."),
                  "menu_lucida", 16, Ivory, 0);
        m_hoverSkill.clear();
        return;
    }

    if (m_pGameData == nullptr)
    {
        return;
    }

    // The skills this class line can learn, grouped; a group header stays with its first skill.
    struct Item
    {
        std::string text;
        bool header = false;
        CreationSkillState state = CreationSkillState::Never;
        CreationSkillReach reach;
    };
    std::vector<Item> items;
    size_t rowCount = 0;
    const ClassSkillTable &table = m_pGameData->classSkillTable();
    const std::string className = selectedClassName();
    const uint32_t raceId = selectedCandidate().raceId;

    for (const CreationSkillGroup &group : creationSkillGroups())
    {
        bool headerAdded = false;

        for (const std::string &skill : group.skills)
        {
            const CreationSkillReach reach = creationSkillReach(table, className, raceId, skill);
            const CreationSkillState state = creationSkillState(
                m_state.defaultSkills, m_state.optionalSkills, m_state.selectedOptionalSkills, reach, skill);

            if (state == CreationSkillState::Never)
            {
                continue;
            }

            if (!headerAdded)
            {
                items.push_back({upperCase(Engine::tr(group.title)), true});
                headerAdded = true;
            }

            items.push_back({skill, false, state, reach});
            ++rowCount;
        }
    }

    // Rows tighten for long lists (up to 37 skills in MAW) so three columns always fit.
    const float rowHeight = rowCount > 30 ? 25 : rowCount > 25 ? 28 : 34;
    const float headerHeight = rowCount > 30 ? 18 : 20;
    const float fontSize = rowCount > 30 ? 16.5f : rowCount > 25 ? 17.5f : 19;
    const float columnGap = 16;
    const float columnWidth = (list.width / u - 2 * columnGap) / 3;
    const auto height = [&](const Item &item)
    {
        return item.header ? headerHeight : rowHeight;
    };
    float total = 0;

    for (const Item &item : items)
    {
        total += height(item);
    }

    // The shortest column height that fits the list in three columns.
    std::vector<int> columnOf(items.size(), 0);

    for (float target = std::ceil(total / 3);; target += 1)
    {
        int column = 0;
        float y = 0;

        for (size_t index = 0; index < items.size(); ++index)
        {
            const float need = height(items[index]) + (items[index].header ? rowHeight : 0);

            if (y > 0 && y + need > target)
            {
                ++column;
                y = 0;
            }

            columnOf[index] = column;
            y += height(items[index]);
        }

        if (column < 3 || target > list.height / u)
        {
            break;
        }
    }

    std::array<float, 3> columnY = {0, 0, 0};
    std::string hovered;
    Rect hoveredRect;

    for (size_t index = 0; index < items.size(); ++index)
    {
        const Item &item = items[index];
        const int column = std::min(columnOf[index], 2);
        const Rect rect{list.x + column * (columnWidth + columnGap) * u, list.y + columnY[size_t(column)] * u,
                        columnWidth * u, height(item) * u};
        columnY[size_t(column)] += height(item);

        if (item.header)
        {
            sheetText({rect.x, rect.y, rect.width, rect.height - 2 * u}, item.text, "menu_lucida", 12, CaptionText);
            drawSolidRect({rect.x, rect.y + rect.height - 1 * u, rect.width, std::max(1.0f, designScale() * 0.5f)},
                          0x1affffffu);
            continue;
        }

        const Rect row{rect.x, rect.y + 1 * u, rect.width, rect.height - 2 * u};
        const Hotspot rowInput = hotspot("skill-" + item.text, row, input);

        switch (item.state)
        {
        case CreationSkillState::Fixed:
            skin("assigned_skill", row, true);
            glyph("diamond", {row.x + 8 * u, row.y + row.height / 2 - 6 * u, 12 * u, 12 * u}, MarkerGold);
            break;
        case CreationSkillState::Chosen:
            skin("skill_selected", row, true);
            glyph("check", {row.x + 7 * u, row.y + row.height / 2 - 7 * u, 14 * u, 14 * u}, MarkerGold);
            break;
        case CreationSkillState::Option:
            skin("skill", row, true);
            glyph("ring", {row.x + 8 * u, row.y + row.height / 2 - 6 * u, 12 * u, 12 * u}, MarkerGold);
            break;
        case CreationSkillState::Later:
        case CreationSkillState::Never:
            drawSolidRect({row.x, row.y + row.height, row.width, std::max(1.0f, designScale() * 0.5f)}, 0x0bffffffu);
            break;
        }

        if (rowInput.hovered
            && (item.state == CreationSkillState::Option || item.state == CreationSkillState::Chosen))
        {
            outline(row, HoverEdge);
        }

        const std::string name = Engine::localize(displaySkillName(item.text));
        const float nameX = row.x + 28 * u;
        const float tagWidth = creationRaceChangesSkill(table, className, raceId, item.text) ? 38 * u : 0;
        // A skill a teacher can teach later is not a choice now: faded, keeping its mastery colour (user,
        // 2026-11-02).
        const auto faded = [&item](uint32_t colour)
        {
            return item.state == CreationSkillState::Later ? (colour & 0x00ffffffu) | (LaterSkillAlpha << 24) : colour;
        };
        sheetText({nameX, row.y, row.width - 34 * u - tagWidth, row.height}, name, "menu_arrus", fontSize,
                  faded(masteryColour(item.reach.best)));

        if (tagWidth > 0)
        {
            const std::string tag = firstLetters(Engine::localizeKnown(selectedCandidate().raceName), 3);
            const float tagX = std::min(nameX + sheetTextWidth(name, "menu_arrus", fontSize) + 5 * u,
                                        row.x + row.width - tagWidth);
            const Rect tagRect{tagX, row.y + row.height / 2 - 8 * u, 33 * u, 16 * u};
            drawSolidRect(tagRect, faded(TagFill));
            sheetText(tagRect, tag, "menu_lucida", 12, faded(TagText), 0);
        }

        if (rowInput.hovered)
        {
            hovered = item.text;
            hoveredRect = row;
        }

        if (rowInput.activated)
        {
            switch (item.state)
            {
            case CreationSkillState::Option:
            case CreationSkillState::Chosen:
                tryToggleOptionalSkill(item.text);
                break;
            case CreationSkillState::Fixed:
                m_state.statusMessage =
                    Engine::tr("{skill} is a starting skill of the {class}.",
                               {{"skill", name}, {"class", Engine::localize(displayClassName(className))}});
                break;
            case CreationSkillState::Later:
                m_state.statusMessage = item.reach.now > SkillMastery::None
                    ? Engine::tr("{skill} is not a starting choice; a teacher can teach it later.", {{"skill", name}})
                    : Engine::tr("{skill} opens after a promotion.", {{"skill", name}});
                break;
            case CreationSkillState::Never:
                break;
            }
        }
    }

    // A popup (the party board) owns the hover state while it is open.
    if (!input)
    {
        return;
    }

    if (hovered != m_hoverSkill || m_hoverSkillSlot != m_activePartySlot)
    {
        m_hoverSkill = hovered;
        m_hoverSkillSlot = m_activePartySlot;
        m_hoverSkillSeconds = 0;
    }
    else
    {
        m_hoverSkillSeconds += deltaSeconds;
    }

    m_hoverSkillAnchor = hoveredRect;
}

void NewGameScreen::drawCreationDoll(bool input)
{
    const float u = sheetPx(1);
    const bool godLich = isGodLichSelected();
    skin("world_card", designRect("CharacterCreationDollColumn"), true);
    const Rect box = designRect("CharacterCreationDoll");
    drawSolidRect(box, 0xff0d1110u);
    const Hotspot dollInput = hotspot("doll", box, input && !godLich);

    if (const CharacterDollEntry *pEntry = selectedCharacterEntry())
    {
        const std::string compositeKey = std::to_string(pEntry->id) + ":" + pEntry->bodyAsset;

        if (compositeKey != m_creationPreviewDollCacheKey)
        {
            m_creationPreviewDollPixels = buildCreationPreviewDollPixels(
                *pEntry, m_pGameData->characterDollTable().getDollType(pEntry->dollTypeId));
            m_creationPreviewDollCacheKey = compositeKey;
        }

        if (m_creationPreviewDollPixels)
        {
            const TexturePixelsBgra &pixels = *m_creationPreviewDollPixels;
            const float fit = std::min(box.width / pixels.logicalWidth, box.height / pixels.logicalHeight);
            const Rect doll{box.x + (box.width - pixels.logicalWidth * fit) / 2,
                            box.y + (box.height - pixels.logicalHeight * fit) / 2, pixels.logicalWidth * fit,
                            pixels.logicalHeight * fit};
            drawPixelsBgra("new_game_creation_doll:" + compositeKey, pixels.physicalWidth, pixels.physicalHeight,
                           pixels.pixels, doll);
        }
    }

    outline(box, dollInput.hovered ? Gold : 0xff475a5du);

    if (dollInput.hovered)
    {
        const Rect bar{box.x, box.y + box.height - 22 * u, box.width, 22 * u};
        drawSolidRect(bar, 0xcc0e100bu);
        sheetText(bar, Engine::tr("change portrait"), "menu_lucida", 15, NameText, 0);
    }

    if (dollInput.activated || action("CharacterCreationChangePortraitButton", input && !godLich))
    {
        openSheetPopup(SheetPopup::Portrait);
    }

    if (action("CharacterCreationResetCharacterButton", input))
    {
        resetCurrentState(true);
    }

    if (action("CharacterCreationRemoveCharacterButton", input && m_partySize > 1 && !godLich))
    {
        removePartySlotAt(m_activePartySlot);
    }
}

bool NewGameScreen::drawCreationFooter(bool input)
{
    if (action("CharacterCreationCancelButton", input))
    {
        cancelCreation();
        return false;
    }

    // The first adventurer who is not ready, and what they still need.
    size_t ready = 0;
    std::string pending;

    for (size_t slotIndex = 0; slotIndex < m_partySize; ++slotIndex)
    {
        const CreationState &state = slotIndex == m_activePartySlot ? m_state : m_partyStates[slotIndex];

        if (stateComplete(state))
        {
            ++ready;
            continue;
        }

        if (!pending.empty())
        {
            continue;
        }

        std::vector<std::string> needs;
        const int pool = bonusPoolForState(state);
        const size_t required = requiredSkillCount(state);
        const size_t skillsLeft = required - std::min(required, state.selectedOptionalSkills.size());

        if (pool > 0)
        {
            needs.push_back(
                Engine::trn("{count} bonus point", "{count} bonus points", uint64_t(pool), {{"count", pool}}));
        }

        if (skillsLeft > 0)
        {
            needs.push_back(
                Engine::trn("{count} skill choice", "{count} skill choices", skillsLeft, {{"count", skillsLeft}}));
        }

        const std::string name = state.name.empty() ? Engine::tr("An adventurer") : state.name;

        if (needs.empty())
        {
            pending = Engine::tr("{name} needs a name", {{"name", name}});
        }
        else if (needs.size() == 1)
        {
            pending = Engine::tr("{name} still needs {need}", {{"name", name}, {"need", needs[0]}});
        }
        else
        {
            pending = Engine::tr("{name} still needs {need} and {otherNeed}",
                                 {{"name", name}, {"need", needs[0]}, {"otherNeed", needs[1]}});
        }
    }

    std::string message = m_state.statusMessage;

    if (message.empty())
    {
        message = ready == m_partySize
            ? Engine::tr("Your party is ready.")
            : Engine::tr("{pending}. ({count} not ready)", {{"pending", pending}, {"count", m_partySize - ready}});
    }

    label("CharacterCreationReadiness", message);

    if (action("CharacterCreationConfirmButton", input && (ready == m_partySize || isGodLichSelected())))
    {
        confirmCreation();
    }

    return true;
}

void NewGameScreen::drawCreationSkillCard(size_t slotIndex, const std::string &skill, const Rect &anchor)
{
    if (m_pGameData == nullptr || slotIndex >= m_partyStates.size())
    {
        return;
    }

    const SkillInspectEntry *pHelp = m_pGameData->characterInspectTable().getSkill(skill);

    if (pHelp == nullptr)
    {
        return;
    }

    const CreationState &state = slotIndex == m_activePartySlot ? m_state : m_partyStates[slotIndex];
    const Character character = buildCharacterFromState(state);
    // skill_des.txt is English; the card shows it in the interface language.
    SkillTooltipText text = {Engine::localize(pHelp->description),
                             {Engine::localize(pHelp->normalDescription), Engine::localize(pHelp->expertDescription),
                              Engine::localize(pHelp->masterDescription),
                              Engine::localize(pHelp->grandmasterDescription)}};

    // The ruleset's own text (MAW: a class school's perks with the new character's numbers).
    if (const GameRules &rules = creationRules(); &rules != &standardGameRules())
    {
        PartySeed seed = {};
        seed.members = {character};
        Party party = {};
        party.seed(seed);
        party.setItemTable(&m_pGameData->itemTable());
        party.setRules(&rules);
        text = rules.skills.skillTooltip(party, *party.member(0), skill, text);
    }

    const ClassSkillTable &table = m_pGameData->classSkillTable();
    const std::string className = classNameForState(state);
    const uint32_t raceId = candidateForState(state).raceId;
    const CreationSkillReach reach = creationSkillReach(table, className, raceId, skill);
    const CreationSkillState skillState = creationSkillState(
        state.defaultSkills, state.optionalSkills, state.selectedOptionalSkills, reach, skill);
    const float u = sheetPx(1);
    const float width = 470 * u;
    const float pad = 16 * u;
    const float inner = width - 2 * pad;
    const float bodySize = 15 * BrowserToLogical * FaithfulFontScale;
    const float levelWidth = 122 * u;
    const float reachWidth = 112 * u;
    const float descriptionWidth = inner - levelWidth - reachWidth - 8 * u;

    std::string stateText;

    switch (skillState)
    {
    case CreationSkillState::Fixed:
        stateText = Engine::tr("Fixed starting skill");
        break;
    case CreationSkillState::Chosen:
        stateText = Engine::tr("Chosen starting skill");
        break;
    case CreationSkillState::Option:
        stateText = Engine::tr("Can be chosen as a starting skill");
        break;
    case CreationSkillState::Later:
        stateText = reach.now > SkillMastery::None ? Engine::tr("Learnable later from a teacher")
                                                   : Engine::tr("Learnable after promotion");
        break;
    case CreationSkillState::Never:
        stateText = Engine::tr("Never learnable for this class");
        break;
    }

    // Each mastery: its name, what it does, and when this adventurer reaches it.
    struct LevelRow
    {
        SkillMastery mastery;
        std::string description;
        std::string reach;
        int availability = 0;
        float height = 0;
    };
    std::vector<LevelRow> rows;
    float height = pad + 32 * u;
    height += textBlockHeight(text.description, "menu_lucida", bodySize, inner) + 12 * u;
    height += 20 * u;

    for (int level = 1; level <= 4; ++level)
    {
        LevelRow row;
        row.mastery = SkillMastery(level);
        row.description = text.masteryLines[size_t(level - 1)];
        row.availability = creationMasteryAvailability(table, className, raceId, skill, row.mastery);

        if (row.availability == 0)
        {
            row.reach = Engine::tr("now");
        }
        else if (row.availability == 1)
        {
            std::vector<std::string> promotions;

            for (const std::string &promotion :
                 table.getClosestPromotionClassesWithEffectiveCap(className, raceId, skill, row.mastery))
            {
                promotions.push_back(Engine::localize(displayClassName(promotion)));
            }

            row.reach = promotions.empty() ? Engine::tr("promotion") : joinedNames(promotions, " / ");
        }
        else
        {
            row.reach = Engine::tr("never");
        }

        row.height = std::max({textBlockHeight(row.description, "menu_lucida", bodySize, descriptionWidth),
                               textBlockHeight(row.reach, "menu_lucida", 13 * BrowserToLogical * FaithfulFontScale,
                                               reachWidth),
                               bodySize * designScale()})
            + 8 * u;
        height += row.height;
        rows.push_back(row);
    }

    std::vector<std::string> holders;

    for (size_t index = 0; index < std::min(m_partySize, m_partyStates.size()); ++index)
    {
        const CreationState &member = index == m_activePartySlot ? m_state : m_partyStates[index];

        if (sameSkill(member.defaultSkills, skill) || sameSkill(member.selectedOptionalSkills, skill))
        {
            holders.push_back(member.name);
        }
    }

    height += 26 * u + pad;
    const float x = anchor.x + anchor.width + 12 * u + width < frameWidth()
        ? anchor.x + anchor.width + 12 * u
        : anchor.x - width - 12 * u;
    const Rect panel{std::clamp(x, 8 * u, std::max(8 * u, frameWidth() - width - 8 * u)),
                     std::clamp(anchor.y - 20 * u, 8 * u, std::max(8 * u, frameHeight() - height - 8 * u)), width,
                     height};
    drawSolidRect(panel, CardFill);
    outline(panel, CardEdge);
    outline({panel.x + 2 * u, panel.y + 2 * u, panel.width - 4 * u, panel.height - 4 * u}, 0xff090a05u);

    float y = panel.y + pad;
    sheetText({panel.x + pad, y, inner * 0.6f, 30 * u}, Engine::localize(displaySkillName(skill)), "fondamento", 27,
              TitleText);
    sheetText({panel.x + pad, y, inner, 30 * u},
              upperCase(state.name + " · " + Engine::localize(displayClassName(className))),
              "menu_lucida", 12, CaptionText, 1);
    y += 32 * u;
    const float descriptionHeight = textBlockHeight(text.description, "menu_lucida", bodySize, inner);
    textInRect({panel.x + pad, y, inner, descriptionHeight}, text.description, "menu_lucida", bodySize, 0xffb1c7cfu);
    y += descriptionHeight + 12 * u;
    sheetText({panel.x + pad, y, inner, 16 * u}, upperCase(stateText), "menu_lucida", 12, CaptionText);
    y += 20 * u;

    for (const LevelRow &row : rows)
    {
        const bool never = row.availability == 2;
        const uint32_t textColour = never ? GameplayUiSkin::Penalty : 0xffb5cfd9u;
        drawSolidRect({panel.x + pad, y, inner, std::max(1.0f, designScale() * 0.5f)}, Separator);
        const float top = y + 4 * u;
        sheetText({panel.x + pad, top, levelWidth, bodySize * designScale()},
                  Engine::tr(MasteryNames[size_t(row.mastery)]),
                  "menu_lucida", 15, never ? GameplayUiSkin::Penalty : masteryColour(row.mastery));
        const float descriptionHeightRow =
            textBlockHeight(row.description, "menu_lucida", bodySize, descriptionWidth);
        textInRect({panel.x + pad + levelWidth, top, descriptionWidth, descriptionHeightRow}, row.description,
                   "menu_lucida", bodySize, textColour);
        const Rect reachRect{panel.x + pad + inner - reachWidth, top, reachWidth, bodySize * designScale()};

        if (row.availability == 0)
        {
            const float textW = sheetTextWidth(row.reach, "menu_lucida", 13);
            glyph("check", {reachRect.x + reachRect.width - textW - 15 * u, top + 1 * u, 11 * u, 11 * u}, Ivory);
            sheetText(reachRect, row.reach, "menu_lucida", 13, Ivory, 1);
        }
        else
        {
            // Promotion names wrap in their column.
            const float reachSize = 13 * BrowserToLogical * FaithfulFontScale;
            textInRect({reachRect.x, top, reachWidth, textBlockHeight(row.reach, "menu_lucida", reachSize,
                                                                      reachWidth)},
                       row.reach, "menu_lucida", reachSize, never ? GameplayUiSkin::Penalty : 0xffb5cfd9u);
        }

        y += row.height;
    }

    drawSolidRect({panel.x + pad, y, inner, std::max(1.0f, designScale() * 0.5f)}, Separator);
    y += 6 * u;
    sheetText({panel.x + pad, y, 60 * u, 18 * u}, upperCase(Engine::tr("Party")), "menu_lucida", 12, CaptionText);
    sheetText({panel.x + pad + 56 * u, y, inner - 56 * u, 18 * u},
              holders.empty() ? Engine::tr("nobody yet") : joinedNames(holders, ", "), "menu_lucida", 14,
              0xff99aeb3u);
}

void NewGameScreen::drawCreationHelp()
{
    if (m_help.body.empty())
    {
        return;
    }

    const float scale = designScale();
    const float width = 425 * scale;
    const float horizontalPadding = 32 * scale;
    const float bodyTop = 56 * scale;
    const float lineHeight = (fontHeight("SMALLNUM") + 2) * scale;
    const float bodyWidth = width - 2 * horizontalPadding;
    const std::vector<std::string> lines = wrapTextToWidth("SMALLNUM", m_help.body, bodyWidth, scale);
    const float bottomPadding = creationRules().classes.showsCreationSkillMatrix() ? 40 : 28;
    float height = bodyTop + bottomPadding * scale + lines.size() * lineHeight;
    std::vector<std::pair<std::vector<std::string>, uint32_t>> extraLines;

    for (const auto &[text, color] : m_help.lines)
    {
        extraLines.emplace_back(wrapTextToWidth("SMALLNUM", text, bodyWidth, scale), color);
        height += extraLines.back().first.size() * lineHeight + 6 * scale;
    }

    if (!extraLines.empty())
    {
        height += 8 * scale;
    }

    const Rect &anchor = m_help.anchor;
    const float x = anchor.x + anchor.width + width + 12 * scale < frameWidth()
        ? anchor.x + anchor.width + 12 * scale
        : anchor.x - width - 12 * scale;
    const Rect panel{std::clamp(x, 8 * scale, std::max(8 * scale, frameWidth() - width - 8 * scale)),
                     std::clamp(anchor.y + (anchor.height - height) / 2, 8 * scale,
                                std::max(8 * scale, frameHeight() - height - 8 * scale)),
                     width, height};
    skin("modal", panel);
    drawText("Create", m_help.title, panel.x + (width - measureTextWidth("Create", m_help.title, scale)) / 2,
             panel.y + 22 * scale, GameplayUiSkin::Gold, scale);
    float textY = panel.y + bodyTop;

    for (const std::string &line : lines)
    {
        drawText("SMALLNUM", line, panel.x + horizontalPadding, textY, GameplayUiSkin::Ivory, scale);
        textY += lineHeight;
    }

    textY += 8 * scale;

    for (const auto &[wrappedLines, color] : extraLines)
    {
        textY += 6 * scale;

        for (const std::string &line : wrappedLines)
        {
            drawText("SMALLNUM", line, panel.x + horizontalPadding, textY, color, scale);
            textY += lineHeight;
        }
    }
}

bool NewGameScreen::drawPopupFrame(const std::string &title, float x, float y, float width, float height)
{
    drawTexture("hud_x2/menus/omenu_modal_veil.png", {0, 0, float(frameWidth()), float(frameHeight())});
    const Rect panel = sheetRect(x, y, width, height);
    drawTexture("hud_x2/menus/omenu_party_frame.png", panel);
    sheetText(sheetRect(x + 44, y + 30, width * 0.4f, 50), title, "fondamento", 32, TitleText);

    if (button("popup-close", sheetRect(x + width - 44 - 100, y + 32, 100, 40), Engine::tr("Close"), "button_quiet"))
    {
        m_sheetPopup = SheetPopup::None;
        return false;
    }

    return true;
}

void NewGameScreen::drawPortraitPicker()
{
    constexpr float X = 70;
    constexpr float Y = 40;
    constexpr float W = 1460;
    constexpr float H = 820;

    if (!drawPopupFrame(Engine::tr("Choose Portrait"), X, Y, W, H) || m_pGameData == nullptr)
    {
        return;
    }

    const float u = sheetPx(1);
    const std::array<std::string_view, 3> filters = {Engine::trNoop("All"), Engine::trNoop("Male"),
        Engine::trNoop("Female")};

    for (size_t index = 0; index < filters.size(); ++index)
    {
        const Rect rect = sheetRect(X + 330 + index * 92, Y + 38, 84, 34);

        if (button("filter-" + std::string(filters[index]), rect, Engine::tr(filters[index]), "button_small"))
        {
            m_portraitFilter = int(index);
            m_popupScroll = 0;
        }

        if (m_portraitFilter == int(index))
        {
            outline(rect, Gold);
        }
    }

    // World filter: the worlds whose portraits are offered here, by their continents.
    struct PortraitWorld
    {
        const char *pWorldId;
        const char *pLabel;
        float width;
    };
    constexpr std::array<PortraitWorld, 5> worlds = {{{"", Engine::trNoop("All worlds").data(), 132},
        {"mm6", Engine::trNoop("Enroth").data(), 104}, {"mm7", Engine::trNoop("Antagarich").data(), 134},
        {"mm8", Engine::trNoop("Jadame").data(), 108}, {"mm9", Engine::trNoop("Chedian").data(), 112}}};
    float worldX = X + 676;
    sheetText(sheetRect(X + 620, Y + 38, 50, 34), upperCase(Engine::tr("World")), "menu_lucida", 11, CaptionText);

    for (const PortraitWorld &world : worlds)
    {
        const std::string worldId = world.pWorldId;
        bool offered = worldId.empty();

        for (size_t index = 0; index < candidateCount() && !offered; ++index)
        {
            const CharacterDollEntry *pEntry =
                m_pGameData->characterDollTable().getCharacter(candidateAt(index).characterDataId);
            offered = pEntry != nullptr && pEntry->worldId == worldId;
        }

        if (!offered)
        {
            continue;
        }

        const Rect rect = sheetRect(worldX, Y + 38, world.width, 34);

        if (button(std::string("world-") + world.pLabel, rect, Engine::tr(world.pLabel), "button_small"))
        {
            m_portraitWorldFilter = worldId;
            m_popupScroll = 0;
        }

        if (m_portraitWorldFilter == worldId)
        {
            outline(rect, Gold);
        }

        worldX += world.width + 8;
    }

    sheetText(sheetRect(X + 44, Y + 74, 760, 16),
              upperCase(Engine::tr("The portrait sets the race · the voice shown is its own")), "menu_lucida", 11,
              CaptionText);

    const Rect viewport = sheetRect(X + 44, Y + 92, W - 88, H - 126);
    scrollViewport(viewport, m_popupContentHeight, m_popupScroll, 60);
    setDesignClip(viewport);
    const float top = viewport.y - m_popupScroll * designScale();
    float y = top;

    // Races in the order their portraits come.
    std::vector<uint32_t> raceOrder;

    for (size_t index = 0; index < candidateCount(); ++index)
    {
        const uint32_t raceId = candidateAt(index).raceId;

        if (std::find(raceOrder.begin(), raceOrder.end(), raceId) == raceOrder.end())
        {
            raceOrder.push_back(raceId);
        }
    }

    constexpr float TileWidth = 92;
    constexpr float TileHeight = 116;
    constexpr float TilePitchX = 102;
    constexpr float TilePitchY = 148;
    const int perRow = std::max(1, int((W - 88 + 10) / TilePitchX));
    const uint32_t selectedId = selectedCandidate().characterDataId;

    for (const uint32_t raceId : raceOrder)
    {
        std::vector<size_t> members;

        for (size_t index = 0; index < candidateCount(); ++index)
        {
            const CreationCandidate &candidate = candidateAt(index);
            const CharacterDollEntry *pEntry =
                m_pGameData->characterDollTable().getCharacter(candidate.characterDataId);

            if (candidate.raceId != raceId || pEntry == nullptr)
            {
                continue;
            }

            if ((m_portraitFilter == 1 && pEntry->defaultSex != 0)
                || (m_portraitFilter == 2 && pEntry->defaultSex != 1)
                || (!m_portraitWorldFilter.empty() && pEntry->worldId != m_portraitWorldFilter))
            {
                continue;
            }

            members.push_back(index);
        }

        if (members.empty())
        {
            continue;
        }

        // The race header: its attribute trends and skill rules.
        const CreationCandidate &first = candidateAt(members.front());
        const std::string raceName = Engine::localizeKnown(first.raceName);
        sheetText({viewport.x, y, 200 * u, 34 * u}, raceName, "fondamento", 24, 0xffa8d1e6u);
        float x = viewport.x + sheetTextWidth(raceName, "fondamento", 24) + 14 * u;
        CreationState probe = {};
        probe.selectedCandidateIndex = members.front();
        probe.baseStats = statsForRace(first.raceName);
        const std::array<RaceStatLine, CreationStatCount> stats = raceStatLinesForState(probe);

        for (size_t stat = 0; stat < CreationStatCount; ++stat)
        {
            const int trend = raceStatTrend(stats[stat]);

            if (trend == 0)
            {
                continue;
            }

            const uint32_t color = trend > 0 ? TrendUp : TrendDown;
            glyph(trend > 0 ? "up" : "down", {x, y + 12 * u, 10 * u, 10 * u}, color);
            const std::string name = firstLetters(Engine::tr(creationStatNames()[stat]), 3);
            sheetText({x + 12 * u, y, 60 * u, 34 * u}, name, "menu_lucida", 14, color);
            x += 12 * u + sheetTextWidth(name, "menu_lucida", 14) + 10 * u;
        }

        y += 38 * u;

        for (size_t tile = 0; tile < members.size(); ++tile)
        {
            const size_t candidateIndex = members[tile];
            const CreationCandidate &candidate = candidateAt(candidateIndex);
            const CharacterDollEntry *pEntry =
                m_pGameData->characterDollTable().getCharacter(candidate.characterDataId);
            const Rect rect{viewport.x + (tile % size_t(perRow)) * TilePitchX * u,
                            y + (tile / size_t(perRow)) * TilePitchY * u, TileWidth * u, TileHeight * u};
            const Hotspot tileInput =
                hotspot("portrait-" + std::to_string(candidateIndex), rect, pointerInside(viewport));
            drawSolidRect(rect, 0xff10110au);
            drawTexture(portraitTextureNameForEntry(*pEntry), rect);
            const bool current = candidate.characterDataId == selectedId;
            outline(rect, current ? Gold : tileInput.hovered ? HoverEdge : PortraitEdge);

            if (current)
            {
                outline({rect.x - 2 * u, rect.y - 2 * u, rect.width + 4 * u, rect.height + 4 * u}, Gold);
            }

            // Another adventurer already uses this portrait.
            for (size_t slotIndex = 0; slotIndex < m_partySize; ++slotIndex)
            {
                const CreationState &state = slotIndex == m_activePartySlot ? m_state : m_partyStates[slotIndex];

                if (slotIndex != m_activePartySlot && candidateForState(state).characterDataId
                    == candidate.characterDataId)
                {
                    const Rect badge{rect.x + 3 * u, rect.y + 3 * u, 18 * u, 18 * u};
                    drawSolidRect(badge, 0xff4cc9f2u);
                    sheetText(badge, std::to_string(slotIndex + 1), "menu_lucida", 12, TagText, 0);
                }
            }

            sheetText({rect.x - 4 * u, rect.y + rect.height + 2 * u, rect.width + 8 * u, 20 * u},
                      voiceLabel(int(pEntry->defaultVoiceId)),
                      "menu_lucida", 13, 0xff9fb6bdu, 0);

            if (tileInput.activated)
            {
                chooseCandidateForActiveSlot(candidateIndex);
                playCreationVoiceLine(m_state.selectedVoiceId, SpeechId::SelectCharacter);
                m_sheetPopup = SheetPopup::None;
            }
        }

        y += ((members.size() + size_t(perRow) - 1) / size_t(perRow)) * TilePitchY * u + 6 * u;
    }

    m_popupContentHeight = (y - top) / designScale();
    setDesignClip(std::nullopt);
}

void NewGameScreen::drawVoicePicker()
{
    constexpr float X = 70;
    constexpr float Y = 40;
    constexpr float W = 1460;
    constexpr float H = 820;

    if (!drawPopupFrame(Engine::tr("Choose Voice"), X, Y, W, H) || m_pGameData == nullptr)
    {
        return;
    }

    const float u = sheetPx(1);
    sheetText(sheetRect(X + 330, Y + 38, 800, 34),
              upperCase(Engine::tr("Voices of the portrait's race and sex · play a line to hear it")), "menu_lucida",
              12, CaptionText);
    const Rect viewport = sheetRect(X + 44, Y + 92, W - 88, H - 126);
    scrollViewport(viewport, m_popupContentHeight, m_popupScroll, 60);
    setDesignClip(viewport);
    const float top = viewport.y - m_popupScroll * designScale();
    const std::vector<int> voices = availableVoiceIdsForSelectedCandidate();
    const float cardWidth = (viewport.width / u - 24 - 14) / 2;
    constexpr float CardHeight = 128;
    constexpr float CardPitch = 138;

    for (size_t index = 0; index < voices.size(); ++index)
    {
        const int voiceId = voices[index];
        const Rect card{viewport.x + (index % 2) * (cardWidth + 14) * u, top + (index / 2) * CardPitch * u,
                        cardWidth * u, CardHeight * u};
        const bool current = voiceId == m_state.selectedVoiceId;
        skin(current ? "save_row_selected" : "save_row", card, true);
        sheetText({card.x + 14 * u, card.y + 8 * u, 300 * u, 36 * u},
                  voiceLabel(voiceId), "fondamento", 26,
                  TitleText);

        if (current)
        {
            sheetText({card.x + 150 * u, card.y + 8 * u, 200 * u, 36 * u}, Engine::tr("current"), "menu_lucida", 13,
                      CaptionText);
        }

        // The portraits whose own voice it is.
        float x = card.x + 14 * u;

        for (size_t candidateIndex = 0; candidateIndex < candidateCount() && x < card.x + card.width * 0.6f;
             ++candidateIndex)
        {
            const CharacterDollEntry *pEntry =
                m_pGameData->characterDollTable().getCharacter(candidateAt(candidateIndex).characterDataId);

            if (pEntry != nullptr && int(pEntry->defaultVoiceId) == voiceId)
            {
                const Rect thumb{x, card.y + 46 * u, 30 * u, 38 * u};
                drawTexture(portraitTextureNameForEntry(*pEntry), thumb);
                outline(thumb, PortraitEdge);
                x += 36 * u;
            }
        }

        x = card.x + 14 * u;
        const float lineSize = voiceLineSize(card.width * 0.75f);

        for (const auto &[english, speech] : VoiceLines)
        {
            const std::string text = Engine::tr(english);
            const float width = sheetTextWidth(text, "menu_lucida", lineSize) + 30 * u;
            const Rect line{x, card.y + 90 * u, width, 28 * u};
            const Hotspot lineInput = hotspot("voice-" + std::to_string(voiceId) + std::string(english), line,
                                              pointerInside(viewport));
            drawSolidRect(line, 0xff1b1d12u);
            outline(line, lineInput.hovered ? PointsText : 0xff50615au);
            glyph("play", {line.x + 7 * u, line.y + line.height / 2 - 5 * u, 9 * u, 10 * u}, 0xff84bdd6u);
            sheetText({line.x + 20 * u, line.y, width - 24 * u, line.height}, text, "menu_lucida", lineSize,
                      lineInput.hovered ? HoverEdge : 0xffb5cfd9u);

            if (lineInput.activated)
            {
                playCreationVoiceLine(voiceId, speech);
            }

            x += width + 6 * u;
        }

        const std::string useLabel = current ? Engine::tr("Keep") : Engine::tr("Use");
        const float useWidth = labelButtonWidth(useLabel, 86 * u);

        if (button("use-voice-" + std::to_string(voiceId),
                   {card.x + card.width - 14 * u - useWidth, card.y + 12 * u, useWidth, 36 * u}, useLabel,
                   "button_quiet", pointerInside(viewport)))
        {
            m_state.selectedVoiceId = voiceId;
            playCreationVoiceLine(voiceId, SpeechId::SelectCharacter);
            m_sheetPopup = SheetPopup::None;
        }
    }

    m_popupContentHeight = (((voices.size() + 1) / 2) * CardPitch) * BrowserToLogical;
    setDesignClip(std::nullopt);
}

float NewGameScreen::drawClassLineTable(float x, float y, float width, uint32_t raceId, const std::string &className,
                                        uint32_t startingClassId)
{
    if (m_pGameData == nullptr)
    {
        return 0;
    }

    const float u = sheetPx(1);
    const ClassSkillTable &table = m_pGameData->classSkillTable();
    const std::optional<std::string> startingClass = table.classNameForId(startingClassId);
    std::vector<std::string> classes;

    for (const std::vector<std::string> &step : creationClassLine(table, className))
    {
        classes.insert(classes.end(), step.begin(), step.end());
    }

    constexpr float SkillColumn = 190;
    constexpr float MarkColumn = 26;
    const float classColumn = (width - SkillColumn - MarkColumn) / std::max<size_t>(1, classes.size());
    const Rect origin = sheetRect(x, y, width, 0);
    float rowY = origin.y;

    // The class names stand on the table's top rule: a name that wraps in its column grows upward, and the header
    // grows with the longest one, so every name ends on the same line. A word longer than its column is set smaller.
    std::vector<std::string> names;
    std::vector<float> nameSizes;
    std::vector<float> nameHeights;
    float headerHeight = 30 * u;

    for (const std::string &line : classes)
    {
        names.push_back(Engine::localize(displayClassName(line)));
        float size = 13;
        std::istringstream words(names.back());
        std::string word;

        while (words >> word)
        {
            const float wordWidth = sheetTextWidth(word, "menu_lucida", size);

            if (wordWidth > classColumn * u - 4 * u && wordWidth > 0)
            {
                size = std::max(13 * MinimumFit, size * (classColumn * u - 4 * u) / wordWidth);
            }
        }

        nameSizes.push_back(size * BrowserToLogical * FaithfulFontScale);
        nameHeights.push_back(textBlockHeight(names.back(), "menu_lucida", nameSizes.back(), classColumn * u));
        headerHeight = std::max(headerHeight, nameHeights.back() + 8 * u);
    }

    for (size_t index = 0; index < classes.size(); ++index)
    {
        textInRect({origin.x + (SkillColumn + MarkColumn + index * classColumn) * u,
                       rowY + headerHeight - nameHeights[index] - 5 * u, classColumn * u, nameHeights[index]},
            names[index], "menu_lucida", nameSizes[index], 0xff92abb2u, true);
    }

    rowY += headerHeight;
    drawSolidRect({origin.x, rowY - 1 * u, width * u, std::max(1.0f, designScale() * 0.5f)}, 0xff47636du);

    for (const CreationSkillGroup &group : creationSkillGroups())
    {
        bool headerDrawn = false;

        for (const std::string &skill : group.skills)
        {
            SkillMastery best = SkillMastery::None;

            for (const std::string &line : classes)
            {
                best = std::max(best, table.getEffectiveCap(line, raceId, skill));
            }

            if (best == SkillMastery::None)
            {
                continue;
            }

            if (!headerDrawn)
            {
                sheetText({origin.x, rowY + 6 * u, width * u, 18 * u}, upperCase(Engine::tr(group.title)),
                          "menu_lucida", 12, CaptionText);
                rowY += 24 * u;
                drawSolidRect({origin.x, rowY - 1 * u, width * u, std::max(1.0f, designScale() * 0.5f)}, 0x1affffffu);
                headerDrawn = true;
            }

            const SkillMastery start = table.getEffectiveCap(className, raceId, skill);

            for (size_t index = 0; index < classes.size(); ++index)
            {
                const SkillMastery cap = table.getEffectiveCap(classes[index], raceId, skill);
                const Rect cell{origin.x + (SkillColumn + MarkColumn + index * classColumn) * u, rowY,
                                classColumn * u, 25 * u};

                if (index > 0 && cap > start)
                {
                    drawSolidRect(cell, 0x245ac4e9u);
                }

                sheetText(cell, cap == SkillMastery::None ? std::string("·") : masteryLetter(cap), "menu_lucida", 16,
                          cap == SkillMastery::None ? 0xff4a504au : masteryColour(cap), 0);
            }

            sheetText({origin.x + 4 * u, rowY, SkillColumn * u, 25 * u}, Engine::localize(displaySkillName(skill)),
                      "menu_arrus", 17,
                      0xffbbd3ddu);

            if (startingClass)
            {
                const StartingSkillAvailability availability =
                    table.getEffectiveStartingSkillAvailability(*startingClass, raceId, skill);
                const Rect mark{origin.x + (SkillColumn + 6) * u, rowY + 7 * u, 11 * u, 11 * u};

                if (availability == StartingSkillAvailability::HasByDefault)
                {
                    glyph("diamond", mark, MarkerGold);
                }
                else if (availability == StartingSkillAvailability::CanLearn)
                {
                    glyph("ring", mark, MarkerGold);
                }
            }

            rowY += 25 * u;
            drawSolidRect({origin.x, rowY - 1 * u, width * u, std::max(1.0f, designScale() * 0.5f)}, 0x0dffffffu);
        }
    }

    return (rowY - origin.y) / u;
}

void NewGameScreen::drawClassPicker()
{
    constexpr float X = 70;
    constexpr float Y = 40;
    constexpr float W = 1460;
    constexpr float H = 820;

    if (!drawPopupFrame(Engine::tr("Choose Class"), X, Y, W, H) || m_pGameData == nullptr)
    {
        return;
    }

    const float u = sheetPx(1);
    const CreationCandidate &candidate = selectedCandidate();
    const std::vector<uint32_t> &classIds = candidate.availableClassIds;
    sheetText(sheetRect(X + 310, Y + 38, 700, 34),
              upperCase(Engine::localizeKnown(candidate.raceName) + " · "
                        + Engine::tr("{count} classes · the table shows this race", {{"count", classIds.size()}})),
              "menu_lucida", 12, CaptionText);

    if (std::find(classIds.begin(), classIds.end(), m_classPreviewId) == classIds.end())
    {
        m_classPreviewId = m_state.selectedClassId;
    }

    // The classes: two columns of cards with the skills each takes to Grandmaster.
    const Rect list = sheetRect(X + 44, Y + 92, 720, H - 126);
    scrollViewport(list, m_popupContentHeight, m_popupScroll, 60);
    setDesignClip(list);
    const float top = list.y - m_popupScroll * designScale();
    const ClassSkillTable &table = m_pGameData->classSkillTable();
    constexpr float CardWidth = 346;
    constexpr float CardHeight = 92;

    for (size_t index = 0; index < classIds.size(); ++index)
    {
        const std::string className = table.classNameForId(classIds[index]).value_or("");
        const Rect card{list.x + (index % 2) * (CardWidth + 12) * u, top + (index / 2) * (CardHeight + 10) * u,
                        CardWidth * u, CardHeight * u};
        const Hotspot cardInput = hotspot("class-" + std::to_string(classIds[index]), card, pointerInside(list));
        const bool previewed = classIds[index] == m_classPreviewId;
        skin(previewed ? "save_row_selected" : "save_row", card, true);

        if (cardInput.hovered && !previewed)
        {
            outline(card, 0xff6a8a9au);
        }

        drawTexture(classIconTextureName(className), {card.x + 10 * u, card.y + (card.height - 34 * u) / 2, 34 * u,
                                                      34 * u});
        const std::string shownClass = Engine::localize(displayClassName(className));
        sheetText({card.x + 56 * u, card.y + 6 * u, 260 * u, 32 * u}, shownClass, "fondamento", 24,
                  previewed ? HoverEdge : TitleText);

        if (classIds[index] == m_state.selectedClassId)
        {
            sheetText({card.x + 56 * u + sheetTextWidth(shownClass, "fondamento", 24) + 8 * u, card.y + 6 * u,
                       100 * u, 32 * u},
                      Engine::tr("current"), "menu_lucida", 13, CaptionText);
        }

        std::vector<std::string> grandmaster;

        for (const CreationSkillGroup &group : creationSkillGroups())
        {
            for (const std::string &skill : group.skills)
            {
                if (creationSkillReach(table, className, candidate.raceId, skill).best == SkillMastery::Grandmaster)
                {
                    grandmaster.push_back(Engine::localize(displaySkillName(skill)));
                }
            }
        }

        const size_t shown = std::min<size_t>(grandmaster.size(), 5);
        std::string skills = joinedNames({grandmaster.begin(), grandmaster.begin() + std::ptrdiff_t(shown)}, ", ");

        if (grandmaster.size() > shown)
        {
            skills += " +" + std::to_string(grandmaster.size() - shown);
        }

        const std::string summary = Engine::tr("GM: {skills}", {{"skills", skills}});

        textInRect({card.x + 56 * u, card.y + 38 * u, card.width - 66 * u, 46 * u}, grandmaster.empty() ? "" : summary,
                   "menu_lucida", 13 * BrowserToLogical * FaithfulFontScale, 0xff9ab3aeu);

        if (cardInput.activated)
        {
            m_classPreviewId = classIds[index];
            m_tableScroll = 0;
        }
    }

    m_popupContentHeight = ((classIds.size() + 1) / 2) * (CardHeight + 10) * BrowserToLogical;
    setDesignClip(std::nullopt);

    // The previewed class: its description and its line's mastery table for this race.
    const std::string previewName = table.classNameForId(m_classPreviewId).value_or(selectedClassName());
    const float panelX = X + 790;
    const float panelWidth = W - 790 - 44;
    drawTexture(classIconTextureName(previewName), sheetRect(panelX, Y + 96, 40, 40));
    const std::string previewClass = Engine::localize(displayClassName(previewName));
    sheetText(sheetRect(panelX + 52, Y + 92, 360, 48), previewClass, "fondamento", 32, TitleText);
    const bool keep = m_classPreviewId == m_state.selectedClassId;

    if (button("class-choose", sheetRect(panelX + panelWidth - 250, Y + 96, 250, 40),
               keep ? Engine::tr("Keep {class}", {{"class", previewClass}})
                    : Engine::tr("Choose {class}", {{"class", previewClass}}),
               "button_primary"))
    {
        if (!keep)
        {
            m_state.selectedClassId = m_classPreviewId;
            refreshSkillChoices(true);
        }

        m_sheetPopup = SheetPopup::None;
        return;
    }

    float descriptionHeight = 0;

    if (const ClassInspectEntry *pHelp = m_pGameData->characterInspectTable().getClass(previewName))
    {
        const float size = 14 * BrowserToLogical * FaithfulFontScale;
        const Rect text = sheetRect(panelX, Y + 148, panelWidth, 0);
        const std::string description = Engine::localize(pHelp->description);
        descriptionHeight = textBlockHeight(description, "menu_lucida", size, text.width);
        textInRect({text.x, text.y, text.width, descriptionHeight}, description, "menu_lucida", size, 0xffb1c7cfu);
    }

    const float tableTop = Y + 158 + descriptionHeight / u;
    const Rect viewport = sheetRect(panelX, tableTop, panelWidth, std::max(80.0f, Y + H - 34 - tableTop));
    scrollViewport(viewport, m_tableContentHeight, m_tableScroll, 50);
    setDesignClip(viewport);
    const float height = drawClassLineTable(panelX, tableTop - m_tableScroll / BrowserToLogical, panelWidth - 14,
                                            candidate.raceId, previewName, m_classPreviewId);
    m_tableContentHeight = height * BrowserToLogical;
    setDesignClip(std::nullopt);
}

void NewGameScreen::drawMasteryTablePopup()
{
    constexpr float X = 70;
    constexpr float Y = 40;
    constexpr float W = 1460;
    constexpr float H = 820;

    if (!drawPopupFrame(Engine::tr("Mastery Table"), X, Y, W, H))
    {
        return;
    }

    sheetText(sheetRect(X + 330, Y + 38, 900, 34),
              upperCase(Engine::localizeKnown(selectedCandidate().raceName) + " · "
                        + Engine::localize(displayClassName(selectedClassName())) + " · "
                        + Engine::tr("starting class and its promotions, shaded where a promotion adds rank")),
              "menu_lucida", 12, CaptionText);
    const float tableTop = Y + 96;
    const Rect viewport = sheetRect(X + 44, tableTop, W - 88, H - 130);
    scrollViewport(viewport, m_popupContentHeight, m_popupScroll, 60);
    setDesignClip(viewport);
    const float height = drawClassLineTable(X + 44, tableTop - m_popupScroll / BrowserToLogical, W - 88 - 20,
                                            selectedCandidate().raceId, selectedClassName(), m_state.selectedClassId);
    m_popupContentHeight = height * BrowserToLogical;
    setDesignClip(std::nullopt);
}

void NewGameScreen::drawPartyBoard()
{
    constexpr float X = 56;
    constexpr float Y = 26;
    constexpr float W = 1488;
    constexpr float H = 848;

    if (!drawPopupFrame(Engine::tr("Party Skills"), X, Y, W, H) || m_pGameData == nullptr)
    {
        return;
    }

    const float u = sheetPx(1);
    const ClassSkillTable &table = m_pGameData->classSkillTable();
    const std::vector<CreationPartyMember> members = creationPartyMembers();
    const CreationPartyCoverage coverage = creationPartyCoverage(table, members);
    sheetText(sheetRect(X + 300, Y + 38, 900, 34),
              upperCase(Engine::tr("Party covers {covered} of {reachable} reachable skills · {grandmaster} to "
                                   "Grandmaster",
                                   {{"covered", coverage.covered}, {"reachable", coverage.reachable},
                                    {"grandmaster", coverage.grandmaster}})
                        + " · " + Engine::tr("click a circle to choose")),
              "menu_lucida", 12, CaptionText);

    const std::array<std::vector<std::string>, 2> halves = {{{"Weapons", "Armour", "Racial"}, {"Magic", "Misc"}}};
    const float halfWidth = (W - 88 - 20) / 2;
    std::string hovered;
    size_t hoveredSlot = 0;
    Rect hoveredRect;

    for (size_t half = 0; half < halves.size(); ++half)
    {
        const float left = X + 44 + half * (halfWidth + 20);
        constexpr float SkillColumn = 180;
        constexpr float PartyColumn = 56;
        const float memberColumn = (halfWidth - SkillColumn - PartyColumn) / std::max<size_t>(1, members.size());
        float y = Y + 96;

        // The member columns: portrait and class.
        for (size_t slot = 0; slot < members.size(); ++slot)
        {
            const CreationState &state = slot == m_activePartySlot ? m_state : m_partyStates[slot];
            const float cx = left + SkillColumn + slot * memberColumn + memberColumn / 2;

            if (const CharacterDollEntry *pEntry = characterEntryForState(state))
            {
                const Rect thumb = sheetRect(cx - 18, y, 36, 46);
                drawTexture(portraitTextureNameForEntry(*pEntry), thumb);
                outline(thumb, slot == m_activePartySlot ? Gold : PortraitEdge);
            }

            sheetText(sheetRect(cx - memberColumn / 2, y + 48, memberColumn, 18),
                      Engine::localize(displayClassName(members[slot].className)), "menu_lucida", 11, 0xff92abb2u,
                      0);
        }

        sheetText(sheetRect(left + halfWidth - PartyColumn, y + 30, PartyColumn, 18), upperCase(Engine::tr("Party")),
                  "menu_lucida", 11,
                  CaptionText, 0);
        y += 72;

        for (const CreationSkillGroup &group : creationSkillGroups())
        {
            if (std::find(halves[half].begin(), halves[half].end(), group.title) == halves[half].end())
            {
                continue;
            }

            bool headerDrawn = false;

            for (const std::string &skill : group.skills)
            {
                std::vector<CreationSkillReach> reaches;
                std::vector<CreationSkillState> states;
                SkillMastery partyBest = SkillMastery::None;
                SkillMastery coveredBest = SkillMastery::None;
                bool covered = false;

                for (const CreationPartyMember &member : members)
                {
                    reaches.push_back(creationSkillReach(table, member.className, member.raceId, skill));
                    states.push_back(creationSkillState(member.fixedSkills, member.optionalSkills, member.chosenSkills,
                                                        reaches.back(), skill));
                    partyBest = std::max(partyBest, reaches.back().best);

                    if (states.back() == CreationSkillState::Fixed || states.back() == CreationSkillState::Chosen)
                    {
                        covered = true;
                        coveredBest = std::max(coveredBest, reaches.back().best);
                    }
                }

                if (partyBest == SkillMastery::None)
                {
                    continue;
                }

                if (!headerDrawn)
                {
                    sheetText(sheetRect(left, y + 4, halfWidth, 16), upperCase(Engine::tr(group.title)), "menu_lucida",
                              11,
                              CaptionText);
                    y += 22;
                    headerDrawn = true;
                }

                constexpr float RowHeight = 23;
                const Rect row = sheetRect(left, y, halfWidth, RowHeight);
                drawSolidRect({row.x, row.y + row.height - 1 * u, row.width, std::max(1.0f, designScale() * 0.5f)},
                              0x09ffffffu);

                if (covered)
                {
                    glyph("diamond", sheetRect(left + 2, y + 8, 7, 7), MarkerGold);
                }

                sheetText(sheetRect(left + 14, y, SkillColumn - 16, RowHeight),
                          Engine::localize(displaySkillName(skill)), "menu_arrus", 16,
                          covered ? 0xffcce8f3u : 0xff858f8fu);

                for (size_t slot = 0; slot < members.size(); ++slot)
                {
                    const Rect cell = sheetRect(left + SkillColumn + slot * memberColumn + 2, y + 1, memberColumn - 4,
                                                RowHeight - 2);
                    const CreationSkillState state = states[slot];
                    const uint32_t colour = masteryColour(reaches[slot].best);

                    if (slot == m_activePartySlot)
                    {
                        drawSolidRect(cell, 0x147ec2e2u);
                    }

                    const bool choosable = state == CreationSkillState::Option || state == CreationSkillState::Chosen;
                    const Hotspot cellInput = hotspot("board-" + std::to_string(slot) + skill, cell,
                                                      state != CreationSkillState::Never);
                    const Rect mark{cell.x + cell.width / 2 - 6 * u, cell.y + cell.height / 2 - 6 * u, 12 * u, 12 * u};

                    switch (state)
                    {
                    case CreationSkillState::Fixed:
                        drawSolidRect(cell, 0x802a4b5au);
                        glyph("diamond", mark, colour);
                        break;
                    case CreationSkillState::Chosen:
                        outline(cell, 0xff9ed2e6u);
                        glyph("check", mark, colour);
                        break;
                    case CreationSkillState::Option:
                        outline(cell, cellInput.hovered ? HoverEdge : 0xff556c6fu);
                        glyph("ring", mark, colour);
                        break;
                    case CreationSkillState::Later:
                        glyph("dot", {mark.x + 3 * u, mark.y + 3 * u, 6 * u, 6 * u}, colour);
                        break;
                    case CreationSkillState::Never:
                        break;
                    }

                    if (cellInput.hovered)
                    {
                        hovered = skill;
                        hoveredSlot = slot;
                        hoveredRect = cell;
                    }

                    if (cellInput.activated && choosable)
                    {
                        toggleOptionalSkillForSlot(slot, skill);
                    }
                }

                const Rect party = sheetRect(left + halfWidth - PartyColumn, y, PartyColumn, RowHeight);

                if (covered)
                {
                    glyph("diamond", {party.x + party.width / 2 - 6 * u, party.y + party.height / 2 - 6 * u, 12 * u,
                                      12 * u},
                          masteryColour(coveredBest));
                }
                else
                {
                    sheetText(party, "-", "menu_lucida", 14, 0xff4a504au, 0);
                }

                y += RowHeight;
            }
        }
    }

    sheetText(sheetRect(X + 44, Y + H - 62, W - 88, 22),
              Engine::tr("Diamond: starts with it · tick: chosen · circle: can pick · dot: a teacher later · colour: "
                         "the best mastery it reaches (grey Normal, white Expert, turquoise Master, gold Grandmaster)"),
              "menu_lucida", 12, CaptionText, 0);

    if (hovered != m_hoverSkill || hoveredSlot != m_hoverSkillSlot)
    {
        m_hoverSkill = hovered;
        m_hoverSkillSlot = hoveredSlot;
        m_hoverSkillSeconds = 0;
    }
    else if (!hovered.empty())
    {
        m_hoverSkillSeconds += m_frameSeconds;
    }

    if (!hovered.empty() && (m_hoverSkillSeconds >= SkillCardDelaySeconds || rightMouseDown()))
    {
        drawCreationSkillCard(hoveredSlot, hovered, hoveredRect);
    }
}
} // namespace OpenYAMM::Game
