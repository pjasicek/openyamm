#include "game/ui/GameplayHudOverlaySupport.h"

#include "game/gameplay/GameMechanics.h"
#include "game/party/SkillData.h"
#include "game/ui/GameplayHudCommon.h"
#include "game/gameplay/GameplayScreenRuntime.h"
#include "game/ui/SpellbookUiLayout.h"

#include <SDL3/SDL.h>
#include <bx/math.h>

#include <algorithm>
#include <array>
#include <cmath>
#include <unordered_set>

namespace OpenYAMM::Game
{
namespace
{
constexpr float HudReferenceWidth = 640.0f;
constexpr float HudReferenceHeight = 480.0f;
constexpr uint16_t HudViewId = 2;

uint32_t packHudColorAbgr(uint8_t red, uint8_t green, uint8_t blue)
{
    return 0xff000000u | (uint32_t(blue) << 16) | (uint32_t(green) << 8) | uint32_t(red);
}

const char *activeBuffLayoutId(
    const GameplayScreenRuntime &context,
    const char *pWideId,
    const char *pStandardId)
{
    return context.settingsSnapshot().gameplayUiLayout == GameplayUiLayout::Standard ? pStandardId : pWideId;
}

void appendPopupBodyLine(std::string &body, const std::string &line)
{
    if (line.empty())
    {
        return;
    }

    if (!body.empty())
    {
        body.push_back('\n');
    }

    body += line;
}

std::string formatRemainingDuration(float remainingSeconds)
{
    const int totalSeconds = std::max(0, int(std::lround(remainingSeconds)));
    const int hours = totalSeconds / 3600;
    const int minutes = (totalSeconds % 3600) / 60;
    const int seconds = totalSeconds % 60;

    if (hours > 0)
    {
        if (minutes > 0)
        {
            return std::to_string(hours) + "h " + std::to_string(minutes) + "m";
        }

        return std::to_string(hours) + "h";
    }

    if (minutes > 0)
    {
        if (seconds > 0 && minutes < 5)
        {
            return std::to_string(minutes) + "m " + std::to_string(seconds) + "s";
        }

        return std::to_string(minutes) + "m";
    }

    return std::to_string(seconds) + "s";
}

std::string formatCharacterDetailDuration(float remainingSeconds)
{
    const int totalSeconds = std::max(0, int(std::lround(remainingSeconds)));
    const int hours = totalSeconds / 3600;
    const int minutes = (totalSeconds % 3600) / 60;
    const int seconds = totalSeconds % 60;
    std::vector<std::string> parts;

    if (hours > 0)
    {
        parts.push_back(std::to_string(hours) + (hours == 1 ? " Hour" : " Hours"));
    }

    if (minutes > 0)
    {
        parts.push_back(std::to_string(minutes) + (minutes == 1 ? " Minute" : " Minutes"));
    }

    if (hours == 0 && seconds > 0)
    {
        parts.push_back(std::to_string(seconds) + (seconds == 1 ? " Second" : " Seconds"));
    }

    if (parts.empty())
    {
        return "0 Seconds";
    }

    std::string result;

    for (const std::string &part : parts)
    {
        if (!result.empty())
        {
            result += ' ';
        }

        result += part;
    }

    return result;
}

std::string defaultCharacterPortraitTextureName(const Character &character)
{
    char buffer[16] = {};
    std::snprintf(buffer, sizeof(buffer), "PC%02u-01", character.portraitPictureId + 1);
    return buffer;
}

struct CharacterSkillUiRow
{
    std::string canonicalName;
    std::string label;
    std::string level;
};

struct CharacterSkillUiData
{
    std::vector<CharacterSkillUiRow> weaponRows;
    std::vector<CharacterSkillUiRow> magicRows;
    std::vector<CharacterSkillUiRow> armorRows;
    std::vector<CharacterSkillUiRow> miscRows;
};

struct CharacterStatRowDefinition
{
    const char *pStatName;
    const char *pLabelId;
    const char *pValueId;
};

constexpr std::array<CharacterStatRowDefinition, 26> CharacterStatRows = {{
    {"SkillPoints", "CharacterStatsSkillPointsTextLabel", "CharacterStatsSkillPointsValue"},
    {"Might", "CharacterStatMightLabel", "CharacterStatMightValue"},
    {"Intellect", "CharacterStatIntellectLabel", "CharacterStatIntellectValue"},
    {"Personality", "CharacterStatPersonalityLabel", "CharacterStatPersonalityValue"},
    {"Endurance", "CharacterStatEnduranceLabel", "CharacterStatEnduranceValue"},
    {"Accuracy", "CharacterStatAccuracyLabel", "CharacterStatAccuracyValue"},
    {"Speed", "CharacterStatSpeedLabel", "CharacterStatSpeedValue"},
    {"Luck", "CharacterStatLuckLabel", "CharacterStatLuckValue"},
    {"HitPoints", "CharacterStatHitPointsLabel", "CharacterStatHitPointsValue"},
    {"SpellPoints", "CharacterStatSpellPointsLabel", "CharacterStatSpellPointsValue"},
    {"ArmorClass", "CharacterStatArmorClassLabel", "CharacterStatArmorClassValue"},
    {"Condition", "CharacterStatConditionLabel", "CharacterStatConditionValue"},
    {"QuickSpell", "CharacterStatQuickSpellLabel", "CharacterStatQuickSpellValue"},
    {"Age", "CharacterStatAgeLabel", "CharacterStatAgeValue"},
    {"Level", "CharacterStatLevelLabel", "CharacterStatLevelValue"},
    {"Experience", "CharacterStatExperienceLabel", "CharacterStatExperienceValue"},
    {"Attack", "CharacterStatAttackLabel", "CharacterStatAttackValue"},
    {"MeleeDamage", "CharacterStatMeleeDamageLabel", "CharacterStatMeleeDamageValue"},
    {"Shoot", "CharacterStatShootLabel", "CharacterStatShootValue"},
    {"RangedDamage", "CharacterStatRangedDamageLabel", "CharacterStatRangedDamageValue"},
    {"FireResistance", "CharacterStatFireResistanceLabel", "CharacterStatFireResistanceValue"},
    {"AirResistance", "CharacterStatAirResistanceLabel", "CharacterStatAirResistanceValue"},
    {"WaterResistance", "CharacterStatWaterResistanceLabel", "CharacterStatWaterResistanceValue"},
    {"EarthResistance", "CharacterStatEarthResistanceLabel", "CharacterStatEarthResistanceValue"},
    {"MindResistance", "CharacterStatMindResistanceLabel", "CharacterStatMindResistanceValue"},
    {"BodyResistance", "CharacterStatBodyResistanceLabel", "CharacterStatBodyResistanceValue"},
}};

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
        rows.push_back(std::move(row));
        shownSkillNames.insert(canonicalName);
    }
}

CharacterSkillUiData buildCharacterSkillUiData(const Character *pCharacter)
{
    static constexpr const char *WeaponSkillNames[] = {
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
    static constexpr const char *MagicSkillNames[] = {
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
    static constexpr const char *ArmorSkillNames[] = {
        "LeatherArmor",
        "ChainArmor",
        "PlateArmor",
        "Shield",
        "Dodging",
    };
    static constexpr const char *MiscSkillNames[] = {
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

    for (const auto &[skillName, skill] : pCharacter->skills)
    {
        if (shownSkillNames.contains(skillName))
        {
            continue;
        }

        CharacterSkillUiRow row = {};
        row.canonicalName = skillName;
        row.label = displaySkillName(skill.name);

        if (skill.mastery != SkillMastery::None && skill.mastery != SkillMastery::Normal)
        {
            row.label += " " + skillPageMasteryDisplayName(skill.mastery);
        }

        row.level = std::to_string(skill.level);
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

int skillMasteryAvailability(
    const ClassSkillTable *pClassSkillTable,
    const Character *pCharacter,
    const std::string &skillName,
    SkillMastery mastery)
{
    if (pClassSkillTable == nullptr || pCharacter == nullptr)
    {
        return 0;
    }

    if (pClassSkillTable->getClassCap(pCharacter->className, skillName) >= mastery)
    {
        return 0;
    }

    if (pClassSkillTable->getHighestPromotionCap(pCharacter->className, skillName) >= mastery)
    {
        return 1;
    }

    return 2;
}
}

bool GameplayHudOverlaySupport::tryPopulateItemInspectOverlayFromRenderedHudItems(
    GameplayScreenRuntime &context,
    int width,
    int height,
    bool requireOpaqueHitTest)
{
    GameplayUiController::ItemInspectOverlayState &overlay = context.itemInspectOverlay();
    overlay = {};

    if (width <= 0
        || height <= 0
        || context.itemTable() == nullptr
        || context.currentHudScreenState() != context.renderedInspectableHudScreenState())
    {
        return false;
    }

    float mouseX = 0.0f;
    float mouseY = 0.0f;
    const SDL_MouseButtonFlags mouseButtons = SDL_GetMouseState(&mouseX, &mouseY);

    if ((mouseButtons & SDL_BUTTON_RMASK) == 0)
    {
        return false;
    }

    for (auto it = context.renderedInspectableHudItems().rbegin();
         it != context.renderedInspectableHudItems().rend();
         ++it)
    {
        if (mouseX < it->x
            || mouseX >= it->x + it->width
            || mouseY < it->y
            || mouseY >= it->y + it->height)
        {
            continue;
        }

        if (requireOpaqueHitTest && !context.isOpaqueHudPixelAtPoint(*it, mouseX, mouseY))
        {
            continue;
        }

        overlay.active = true;
        overlay.objectDescriptionId = it->objectDescriptionId;
        overlay.hasItemState = it->hasItemState;
        overlay.itemState = it->itemState;
        overlay.sourceType = it->sourceType;
        overlay.sourceMemberIndex = it->sourceMemberIndex;
        overlay.sourceGridX = it->sourceGridX;
        overlay.sourceGridY = it->sourceGridY;
        overlay.sourceEquipmentSlot = it->equipmentSlot;
        overlay.sourceLootItemIndex = it->sourceLootItemIndex;
        overlay.hasValueOverride = it->hasValueOverride;
        overlay.valueOverride = it->valueOverride;
        overlay.sourceX = it->x;
        overlay.sourceY = it->y;
        overlay.sourceWidth = it->width;
        overlay.sourceHeight = it->height;
        return true;
    }

    return false;
}

void GameplayHudOverlaySupport::updateCharacterInspectOverlay(
    GameplayScreenRuntime &context,
    int width,
    int height)
{
    GameplayUiController::CharacterInspectOverlayState &overlay = context.characterInspectOverlay();
    overlay = {};

    const auto combineResolvedRects =
        [](const GameplayScreenRuntime::ResolvedHudLayoutElement &left,
           const GameplayScreenRuntime::ResolvedHudLayoutElement &right)
            -> GameplayScreenRuntime::ResolvedHudLayoutElement
        {
            const float minX = std::min(left.x, right.x);
            const float minY = std::min(left.y, right.y);
            const float maxX = std::max(left.x + left.width, right.x + right.width);
            const float maxY = std::max(left.y + left.height, right.y + right.height);

            return {
                minX,
                minY,
                maxX - minX,
                maxY - minY,
                left.scale
            };
        };
    const auto inflateResolvedRect =
        [](const GameplayScreenRuntime::ResolvedHudLayoutElement &rect,
           float horizontalPadding,
           float verticalPadding)
            -> GameplayScreenRuntime::ResolvedHudLayoutElement
        {
            return {
                rect.x - horizontalPadding,
                rect.y - verticalPadding,
                rect.width + horizontalPadding * 2.0f,
                rect.height + verticalPadding * 2.0f,
                rect.scale
            };
        };

    if (width <= 0
        || height <= 0
        || !context.characterScreenReadOnly().open
        || context.partyReadOnly() == nullptr
        || context.isAdventurersInnScreenActive()
        || context.characterInspectTable() == nullptr)
    {
        return;
    }

    float mouseX = 0.0f;
    float mouseY = 0.0f;
    const SDL_MouseButtonFlags mouseButtons = SDL_GetMouseState(&mouseX, &mouseY);

    if ((mouseButtons & SDL_BUTTON_RMASK) == 0)
    {
        return;
    }

    const Character *pCharacter = context.selectedCharacterScreenCharacter();

    if (pCharacter == nullptr)
    {
        return;
    }

    if (context.characterScreenReadOnly().page == GameplayUiController::CharacterPage::Stats)
    {
        for (const CharacterStatRowDefinition &row : CharacterStatRows)
        {
            const GameplayScreenRuntime::HudLayoutElement *pLabelLayout = context.findHudLayoutElement(row.pLabelId);
            const GameplayScreenRuntime::HudLayoutElement *pValueLayout = context.findHudLayoutElement(row.pValueId);

            if (pLabelLayout == nullptr || pValueLayout == nullptr)
            {
                continue;
            }

            const std::optional<GameplayScreenRuntime::ResolvedHudLayoutElement> resolvedLabel =
                context.resolveHudLayoutElement(
                    row.pLabelId,
                    width,
                    height,
                    pLabelLayout->width,
                    pLabelLayout->height);
            const std::optional<GameplayScreenRuntime::ResolvedHudLayoutElement> resolvedValue =
                context.resolveHudLayoutElement(
                    row.pValueId,
                    width,
                    height,
                    pValueLayout->width,
                    pValueLayout->height);

            if (!resolvedLabel || !resolvedValue)
            {
                continue;
            }

            const GameplayScreenRuntime::ResolvedHudLayoutElement rowRect =
                inflateResolvedRect(combineResolvedRects(*resolvedLabel, *resolvedValue), 6.0f, 3.0f);

            if (!GameplayHudCommon::isPointerInsideResolvedElement(rowRect, mouseX, mouseY))
            {
                continue;
            }

            const StatInspectEntry *pEntry = context.characterInspectTable()->getStat(row.pStatName);

            if (pEntry == nullptr || pEntry->description.empty())
            {
                return;
            }

            overlay.active = true;
            overlay.title = pEntry->name;
            overlay.body = pEntry->description;

            if (std::string_view(row.pStatName) == "Experience")
            {
                const std::string supplement = GameMechanics::buildExperienceInspectSupplement(*pCharacter);

                if (!supplement.empty())
                {
                    overlay.body += "\n" + supplement;
                }
            }

            overlay.sourceX = rowRect.x;
            overlay.sourceY = rowRect.y;
            overlay.sourceWidth = rowRect.width;
            overlay.sourceHeight = rowRect.height;
            return;
        }

        return;
    }

    if (context.characterScreenReadOnly().page != GameplayUiController::CharacterPage::Skills)
    {
        return;
    }

    const CharacterSkillUiData skillUiData = buildCharacterSkillUiData(pCharacter);
    const std::optional<GameplayScreenRuntime::HudFontHandle> skillRowFont = context.findHudFont("Lucida");
    const float skillRowHeight = skillRowFont.has_value()
        ? float(std::max(1, skillRowFont->fontHeight - 3))
        : 11.0f;

    const auto tryShowSkillPopup =
        [&context, &overlay, width, height, mouseX, mouseY, pCharacter, skillRowHeight](
            const char *pRegionId,
            const char *pLevelHeaderId,
            const std::vector<CharacterSkillUiRow> &rows) -> bool
        {
            if (rows.empty())
            {
                return false;
            }

            const GameplayScreenRuntime::HudLayoutElement *pRegionLayout = context.findHudLayoutElement(pRegionId);
            const GameplayScreenRuntime::HudLayoutElement *pLevelLayout = context.findHudLayoutElement(pLevelHeaderId);

            if (pRegionLayout == nullptr || pLevelLayout == nullptr)
            {
                return false;
            }

            const std::optional<GameplayScreenRuntime::ResolvedHudLayoutElement> resolvedRegion =
                context.resolveHudLayoutElement(
                    pRegionId,
                    width,
                    height,
                    pRegionLayout->width,
                    pRegionLayout->height);
            const std::optional<GameplayScreenRuntime::ResolvedHudLayoutElement> resolvedLevelHeader =
                context.resolveHudLayoutElement(
                    pLevelHeaderId,
                    width,
                    height,
                    pLevelLayout->width,
                    pLevelLayout->height);

            if (!resolvedRegion || !resolvedLevelHeader)
            {
                return false;
            }

            const float rowHeightPixels = skillRowHeight * resolvedRegion->scale;
            const float rowWidth = resolvedLevelHeader->x + resolvedLevelHeader->width - resolvedRegion->x;

            for (size_t rowIndex = 0; rowIndex < rows.size(); ++rowIndex)
            {
                const CharacterSkillUiRow &row = rows[rowIndex];
                const float rowY = resolvedRegion->y + float(rowIndex) * rowHeightPixels;
                const GameplayScreenRuntime::ResolvedHudLayoutElement rowRect = {
                    resolvedRegion->x,
                    rowY,
                    rowWidth,
                    rowHeightPixels,
                    resolvedRegion->scale
                };

                if (!GameplayHudCommon::isPointerInsideResolvedElement(rowRect, mouseX, mouseY))
                {
                    continue;
                }

                const SkillInspectEntry *pEntry =
                    context.characterInspectTable() != nullptr
                    ? context.characterInspectTable()->getSkill(row.canonicalName)
                    : nullptr;

                if (pEntry == nullptr || pEntry->description.empty())
                {
                    return false;
                }

                overlay.active = true;
                overlay.title = pEntry->name;
                overlay.body = pEntry->description;
                overlay.expert.text = "Expert: " + pEntry->expertDescription;
                overlay.expert.availability = skillMasteryAvailability(
                    context.classSkillTable(),
                    pCharacter,
                    row.canonicalName,
                    SkillMastery::Expert);
                overlay.expert.visible = !pEntry->expertDescription.empty();
                overlay.master.text = "Master: " + pEntry->masterDescription;
                overlay.master.availability = skillMasteryAvailability(
                    context.classSkillTable(),
                    pCharacter,
                    row.canonicalName,
                    SkillMastery::Master);
                overlay.master.visible = !pEntry->masterDescription.empty();
                overlay.grandmaster.text = "Grandmaster: " + pEntry->grandmasterDescription;
                overlay.grandmaster.availability = skillMasteryAvailability(
                    context.classSkillTable(),
                    pCharacter,
                    row.canonicalName,
                    SkillMastery::Grandmaster);
                overlay.grandmaster.visible = !pEntry->grandmasterDescription.empty();
                overlay.sourceX = rowRect.x;
                overlay.sourceY = rowRect.y;
                overlay.sourceWidth = rowRect.width;
                overlay.sourceHeight = rowRect.height;
                return true;
            }

            return false;
        };

    if (tryShowSkillPopup("CharacterSkillsWeaponsListRegion", "CharacterSkillsWeaponsLevelHeader", skillUiData.weaponRows))
    {
        return;
    }

    if (tryShowSkillPopup("CharacterSkillsMagicListRegion", "CharacterSkillsMagicLevelHeader", skillUiData.magicRows))
    {
        return;
    }

    if (tryShowSkillPopup("CharacterSkillsArmorListRegion", "CharacterSkillsArmorLevelHeader", skillUiData.armorRows))
    {
        return;
    }

    tryShowSkillPopup("CharacterSkillsMiscListRegion", "CharacterSkillsMiscLevelHeader", skillUiData.miscRows);
}

void GameplayHudOverlaySupport::updateBuffInspectOverlay(
    GameplayScreenRuntime &context,
    int width,
    int height,
    bool showGameplayHud)
{
    GameplayUiController::BuffInspectOverlayState &overlay = context.buffInspectOverlay();
    overlay = {};

    if (width <= 0
        || height <= 0
        || context.partyReadOnly() == nullptr
        || !showGameplayHud
        || context.currentHudScreenState() != GameplayHudScreenState::Gameplay
        || context.characterScreenReadOnly().open
        || context.activeEventDialog().isActive
        || context.spellbookReadOnly().active
        || context.controlsScreenState().active
        || context.keyboardScreenState().active
        || context.menuScreenState().active
        || context.saveGameScreenState().active
        || context.loadGameScreenState().active)
    {
        return;
    }

    float mouseX = 0.0f;
    float mouseY = 0.0f;
    const SDL_MouseButtonFlags mouseButtons = SDL_GetMouseState(&mouseX, &mouseY);

    if ((mouseButtons & (SDL_BUTTON_RMASK | SDL_BUTTON_LMASK)) == 0 || context.itemInspectOverlayReadOnly().active)
    {
        return;
    }

    const Party &party = *context.partyReadOnly();

    struct PartyBuffInspectTarget
    {
        const char *pWideLayoutId;
        const char *pStandardLayoutId;
        const char *pLabel;
        PartyBuffId buffId;
        bool skullPanel;
    };

    static constexpr PartyBuffInspectTarget BuffTargets[] = {
        {"OutdoorBuffSkull_Torchlight", "OutdoorStandardBuffSkull_Torchlight", "Torch Light", PartyBuffId::TorchLight, true},
        {"OutdoorBuffSkull_WizardEye", "OutdoorStandardBuffSkull_WizardEye", "Wizard Eye", PartyBuffId::WizardEye, true},
        {"OutdoorBuffSkull_Featherfall", "OutdoorStandardBuffSkull_FeatherFall", "Feather Fall", PartyBuffId::FeatherFall, true},
        {"OutdoorBuffSkull_Stoneskin", "OutdoorStandardBuffSkull_Stoneskin", "Stoneskin", PartyBuffId::Stoneskin, true},
        {"OutdoorBuffSkull_DayOfGods", "OutdoorStandardBuffSkull_DayOfGods", "Day of the Gods", PartyBuffId::DayOfGods, true},
        {
            "OutdoorBuffSkull_ProtectionFromGods",
            "OutdoorStandardBuffSkull_ProtectionFromGods",
            "Protection from Magic",
            PartyBuffId::ProtectionFromMagic,
            true
        },
        {
            "OutdoorBuffBody_FireResistance",
            "OutdoorStandardBuffBody_FireResistance",
            "Fire Resistance",
            PartyBuffId::FireResistance,
            false
        },
        {
            "OutdoorBuffBody_WaterResistance",
            "OutdoorStandardBuffBody_WaterResistance",
            "Water Resistance",
            PartyBuffId::WaterResistance,
            false
        },
        {"OutdoorBuffBody_AirResistance", "OutdoorStandardBuffBody_AirResistance", "Air Resistance", PartyBuffId::AirResistance, false},
        {
            "OutdoorBuffBody_EarthResistance",
            "OutdoorStandardBuffBody_EarthResistance",
            "Earth Resistance",
            PartyBuffId::EarthResistance,
            false
        },
        {
            "OutdoorBuffBody_MindResistance",
            "OutdoorStandardBuffBody_MindResistance",
            "Mind Resistance",
            PartyBuffId::MindResistance,
            false
        },
        {
            "OutdoorBuffBody_BodyResistance",
            "OutdoorStandardBuffBody_BodyResistance",
            "Body Resistance",
            PartyBuffId::BodyResistance,
            false
        },
        {"OutdoorBuffBody_Shield", "OutdoorStandardBuffBody_Shield", "Shield", PartyBuffId::Shield, false},
        {"OutdoorBuffBody_Heroism", "OutdoorStandardBuffBody_Heroism", "Heroism", PartyBuffId::Heroism, false},
        {"OutdoorBuffBody_Haste", "OutdoorStandardBuffBody_Haste", "Haste", PartyBuffId::Haste, false},
        {"OutdoorBuffBody_Immolation", "OutdoorStandardBuffBody_Immolation", "Immolation", PartyBuffId::Immolation, false},
    };

    const auto populateBuffPanelOverlay =
        [&overlay, &party](bool skullPanel, const GameplayScreenRuntime::ResolvedHudLayoutElement &rect)
        {
            std::string body;

            for (const PartyBuffInspectTarget &target : BuffTargets)
            {
                if (target.skullPanel != skullPanel)
                {
                    continue;
                }

                const PartyBuffState *pBuff = party.partyBuff(target.buffId);

                if (pBuff == nullptr)
                {
                    continue;
                }

                appendPopupBodyLine(
                    body,
                    std::string(target.pLabel) + " - " + formatRemainingDuration(pBuff->remainingSeconds));
            }

            if (body.empty())
            {
                body = "No active buffs";
            }

            overlay.active = true;
            overlay.title = "Active Buffs";
            overlay.body = body;
            overlay.sourceX = rect.x;
            overlay.sourceY = rect.y;
            overlay.sourceWidth = rect.width;
            overlay.sourceHeight = rect.height;
        };

    for (const PartyBuffInspectTarget &target : BuffTargets)
    {
        const PartyBuffState *pBuff = party.partyBuff(target.buffId);

        if (pBuff == nullptr)
        {
            continue;
        }

        const char *pLayoutId = activeBuffLayoutId(context, target.pWideLayoutId, target.pStandardLayoutId);
        const GameplayScreenRuntime::HudLayoutElement *pLayout = context.findHudLayoutElement(pLayoutId);

        if (pLayout == nullptr)
        {
            continue;
        }

        const std::optional<GameplayScreenRuntime::ResolvedHudLayoutElement> resolved = context.resolveHudLayoutElement(
            pLayoutId,
            width,
            height,
            pLayout->width,
            pLayout->height);

        if (!resolved || !GameplayHudCommon::isPointerInsideResolvedElement(*resolved, mouseX, mouseY))
        {
            continue;
        }

        populateBuffPanelOverlay(target.skullPanel, *resolved);
        return;
    }

    struct BuffPanelTarget
    {
        const char *pWideLayoutId;
        const char *pStandardLayoutId;
        bool skullPanel;
    };

    static constexpr BuffPanelTarget PanelTargets[] = {
        {"OutdoorBuffSkullPanel", "OutdoorStandardBuffSkullPanel", true},
        {"OutdoorBuffBodyPanel", "OutdoorStandardBuffBodyPanel", false},
    };

    for (const BuffPanelTarget &panelTarget : PanelTargets)
    {
        const char *pLayoutId = activeBuffLayoutId(context, panelTarget.pWideLayoutId, panelTarget.pStandardLayoutId);
        const GameplayScreenRuntime::HudLayoutElement *pPanelLayout = context.findHudLayoutElement(pLayoutId);

        if (pPanelLayout == nullptr)
        {
            continue;
        }

        const std::optional<GameplayScreenRuntime::ResolvedHudLayoutElement> resolvedPanel =
            context.resolveHudLayoutElement(
                pLayoutId,
                width,
                height,
                pPanelLayout->width,
                pPanelLayout->height);

        if (!resolvedPanel || !GameplayHudCommon::isPointerInsideResolvedElement(*resolvedPanel, mouseX, mouseY))
        {
            continue;
        }

        populateBuffPanelOverlay(panelTarget.skullPanel, *resolvedPanel);
        return;
    }
}

void GameplayHudOverlaySupport::updateCharacterDetailOverlay(
    GameplayScreenRuntime &context,
    int width,
    int height)
{
    GameplayUiController::CharacterDetailOverlayState &overlay = context.characterDetailOverlay();
    overlay = {};

    if (width <= 0 || height <= 0 || context.partyReadOnly() == nullptr)
    {
        return;
    }

    float mouseX = 0.0f;
    float mouseY = 0.0f;
    const SDL_MouseButtonFlags mouseButtons = SDL_GetMouseState(&mouseX, &mouseY);

    if ((mouseButtons & SDL_BUTTON_RMASK) == 0
        || context.itemInspectOverlayReadOnly().active
        || context.characterInspectOverlayReadOnly().active
        || context.buffInspectOverlayReadOnly().active
        || context.spellInspectOverlayReadOnly().active
        || context.activeEventDialog().isActive
        || context.spellbookReadOnly().active
        || context.controlsScreenState().active
        || context.keyboardScreenState().active
        || context.menuScreenState().active
        || context.saveGameScreenState().active
        || context.loadGameScreenState().active)
    {
        return;
    }

    const Party &party = *context.partyReadOnly();
    const Character *pCharacter = nullptr;
    std::optional<GameplayScreenRuntime::ResolvedHudLayoutElement> sourceRect;
    std::optional<size_t> memberIndex;

    if (context.characterScreenReadOnly().open)
    {
        pCharacter = context.selectedCharacterScreenCharacter();
        const GameplayScreenRuntime::HudLayoutElement *pDollLayout = context.findHudLayoutElement("CharacterDollPanel");

        if (!context.isAdventurersInnCharacterSourceActive())
        {
            memberIndex = party.activeMemberIndex();
        }

        if (pCharacter != nullptr && pDollLayout != nullptr)
        {
            sourceRect = context.resolveHudLayoutElement(
                "CharacterDollPanel",
                width,
                height,
                pDollLayout->width,
                pDollLayout->height);
        }
    }
    else if (context.currentHudScreenState() == GameplayHudScreenState::Gameplay)
    {
        memberIndex = context.resolvePartyPortraitIndexAtPoint(width, height, mouseX, mouseY);

        if (memberIndex)
        {
            pCharacter = party.member(*memberIndex);
            sourceRect = context.resolvePartyPortraitRect(width, height, *memberIndex);
        }
    }

    if (pCharacter == nullptr
        || !sourceRect
        || !GameplayHudCommon::isPointerInsideResolvedElement(*sourceRect, mouseX, mouseY))
    {
        return;
    }

    const CharacterSheetSummary summary = GameMechanics::buildCharacterSheetSummary(*pCharacter, context.itemTable());

    overlay.active = true;
    const std::string characterName = pCharacter->name.empty() ? "Member" : pCharacter->name;
    const std::string characterClass = !pCharacter->className.empty() ? pCharacter->className : pCharacter->role;
    overlay.title = characterClass.empty() ? characterName : characterName + " the " + characterClass;
    overlay.body.clear();
    overlay.portraitTextureName = defaultCharacterPortraitTextureName(*pCharacter);
    overlay.hitPointsText = std::to_string(summary.health.current) + " / " + std::to_string(summary.health.maximum);
    overlay.spellPointsText =
        std::to_string(summary.spellPoints.current) + " / " + std::to_string(summary.spellPoints.maximum);
    overlay.conditionText = summary.conditionText;
    overlay.quickSpellText = summary.quickSpellText;
    overlay.activeSpells.clear();

    struct CharacterBuffInspectLine
    {
        const char *pLabel;
        CharacterBuffId buffId;
    };

    static constexpr CharacterBuffInspectLine CharacterBuffLines[] = {
        {"Bless", CharacterBuffId::Bless},
        {"Fate", CharacterBuffId::Fate},
        {"Preservation", CharacterBuffId::Preservation},
        {"Regeneration", CharacterBuffId::Regeneration},
        {"Hammerhands", CharacterBuffId::Hammerhands},
        {"Pain Reflection", CharacterBuffId::PainReflection},
        {"Fire Aura", CharacterBuffId::FireAura},
        {"Vampiric Weapon", CharacterBuffId::VampiricWeapon},
        {"Mistform", CharacterBuffId::Mistform},
        {"Glamour", CharacterBuffId::Glamour},
    };

    if (memberIndex)
    {
        for (const CharacterBuffInspectLine &buffLine : CharacterBuffLines)
        {
            const CharacterBuffState *pBuff = party.characterBuff(*memberIndex, buffLine.buffId);

            if (pBuff == nullptr)
            {
                continue;
            }

            GameplayUiController::CharacterDetailOverlayState::ActiveSpellLine line = {};
            line.name = buffLine.pLabel;
            line.duration = formatCharacterDetailDuration(pBuff->remainingSeconds);
            overlay.activeSpells.push_back(std::move(line));
        }
    }

    overlay.sourceX = sourceRect->x;
    overlay.sourceY = sourceRect->y;
    overlay.sourceWidth = sourceRect->width;
    overlay.sourceHeight = sourceRect->height;
}

void GameplayHudOverlaySupport::updateSpellInspectOverlay(
    GameplayScreenRuntime &context,
    int width,
    int height)
{
    GameplayUiController::SpellInspectOverlayState &overlay = context.spellInspectOverlay();
    overlay = {};

    if (width <= 0 || height <= 0 || !context.spellbookReadOnly().active || context.spellTable() == nullptr)
    {
        return;
    }

    float mouseX = 0.0f;
    float mouseY = 0.0f;
    const SDL_MouseButtonFlags mouseButtons = SDL_GetMouseState(&mouseX, &mouseY);

    if ((mouseButtons & SDL_BUTTON_RMASK) == 0)
    {
        return;
    }

    const SpellbookSchoolUiDefinition *pDefinition = findSpellbookSchoolUiDefinition(context.spellbookReadOnly().school);

    if (pDefinition == nullptr || !context.activeMemberHasSpellbookSchool(context.spellbookReadOnly().school))
    {
        return;
    }

    for (uint32_t spellOffset = 0; spellOffset < pDefinition->spellCount; ++spellOffset)
    {
        const uint32_t spellId = pDefinition->firstSpellId + spellOffset;

        if (!context.activeMemberKnowsSpell(spellId))
        {
            continue;
        }

        const uint32_t spellOrdinal = spellOffset + 1;
        const std::string layoutId = spellbookSpellLayoutId(context.spellbookReadOnly().school, spellOrdinal);
        const GameplayScreenRuntime::HudLayoutElement *pLayout = context.findHudLayoutElement(layoutId);

        if (pLayout == nullptr)
        {
            continue;
        }

        const std::optional<GameplayScreenRuntime::ResolvedHudLayoutElement> resolved = context.resolveHudLayoutElement(
            layoutId,
            width,
            height,
            pLayout->width,
            pLayout->height);

        if (!resolved || !GameplayHudCommon::isPointerInsideResolvedElement(*resolved, mouseX, mouseY))
        {
            continue;
        }

        const SpellEntry *pSpellEntry = context.spellTable()->findById(spellId);

        if (pSpellEntry == nullptr)
        {
            return;
        }

        overlay.active = true;
        overlay.spellId = spellId;
        overlay.title = pSpellEntry->name;
        overlay.body = pSpellEntry->description;
        overlay.normal = pSpellEntry->normalText.empty() ? "" : "Normal: " + pSpellEntry->normalText;
        overlay.expert = pSpellEntry->expertText.empty() ? "" : "Expert: " + pSpellEntry->expertText;
        overlay.master = pSpellEntry->masterText.empty() ? "" : "Master: " + pSpellEntry->masterText;
        overlay.grandmaster =
            pSpellEntry->grandmasterText.empty() ? "" : "Grand Master: " + pSpellEntry->grandmasterText;
        overlay.sourceX = resolved->x;
        overlay.sourceY = resolved->y;
        overlay.sourceWidth = std::max(1.0f, resolved->width);
        overlay.sourceHeight = std::max(1.0f, resolved->height);
        return;
    }
}

void GameplayHudOverlaySupport::renderGameplayMouseLookOverlay(
    GameplayScreenRuntime &context,
    int width,
    int height,
    bool active)
{
    if (!active || width <= 0 || height <= 0)
    {
        return;
    }

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

    const GameplayUiViewportRect uiViewport = GameplayHudCommon::computeUiViewportRect(width, height);
    const float baseScale = std::min(uiViewport.width / HudReferenceWidth, uiViewport.height / HudReferenceHeight);
    const float overlayScale = std::clamp(baseScale, 0.75f, 2.0f);
    const float centerX = std::round(static_cast<float>(width) * 0.5f);
    const float centerY = std::round(static_cast<float>(height) * 0.5f);
    const float armLength = std::round(3.0f * overlayScale);
    const float armGap = std::round(1.0f * overlayScale);
    const float stroke = std::max(1.0f, std::round(1.0f * overlayScale));
    const uint32_t dotColor = packHudColorAbgr(255, 255, 180);
    const uint32_t shadowColor = 0xc0000000u;
    const std::optional<GameplayScreenRuntime::HudTextureHandle> dotTexture =
        context.ensureSolidHudTextureLoaded("__gameplay_mouse_look_marker__", dotColor);
    const std::optional<GameplayScreenRuntime::HudTextureHandle> shadowTexture =
        context.ensureSolidHudTextureLoaded("__gameplay_mouse_look_marker_shadow__", shadowColor);

    if (!dotTexture || !shadowTexture)
    {
        return;
    }

    const auto submitQuad =
        [&context](const GameplayScreenRuntime::HudTextureHandle &texture, float x, float y, float quadWidth, float quadHeight)
        {
            context.submitHudTexturedQuad(texture, x, y, quadWidth, quadHeight);
        };

    submitQuad(*shadowTexture, centerX - stroke * 0.5f + 1.0f, centerY - armGap - armLength + 1.0f, stroke, armLength);
    submitQuad(*shadowTexture, centerX - stroke * 0.5f + 1.0f, centerY + armGap + 1.0f, stroke, armLength);
    submitQuad(*shadowTexture, centerX - armGap - armLength + 1.0f, centerY - stroke * 0.5f + 1.0f, armLength, stroke);
    submitQuad(*shadowTexture, centerX + armGap + 1.0f, centerY - stroke * 0.5f + 1.0f, armLength, stroke);

    submitQuad(*dotTexture, centerX - stroke * 0.5f, centerY - armGap - armLength, stroke, armLength);
    submitQuad(*dotTexture, centerX - stroke * 0.5f, centerY + armGap, stroke, armLength);
    submitQuad(*dotTexture, centerX - armGap - armLength, centerY - stroke * 0.5f, armLength, stroke);
    submitQuad(*dotTexture, centerX + armGap, centerY - stroke * 0.5f, armLength, stroke);
}
} // namespace OpenYAMM::Game
