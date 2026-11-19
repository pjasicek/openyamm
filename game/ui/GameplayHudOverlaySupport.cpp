#include "game/ui/GameplayBuffHud.h"
#include "game/ui/GameplayHudOverlaySupport.h"

#include "game/gameplay/GameMechanics.h"
#include "game/gameplay/GameplayInputFrame.h"
#include "game/party/SkillData.h"
#include "game/party/SpellSchool.h"
#include "game/tables/ItemTable.h"
#include "game/ui/GameplayHudCommon.h"
#include "game/gameplay/GameplayScreenRuntime.h"
#include "game/ui/SpellbookUiLayout.h"

#include <bx/math.h>

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <unordered_set>

namespace OpenYAMM::Game
{
namespace
{
constexpr float HudReferenceWidth = 640.0f;
constexpr float HudReferenceHeight = 480.0f;
constexpr float MaxUiScale = 8.0f;
constexpr uint16_t HudViewId = 2;
constexpr float OeRealtimeRecoveryScale = 2.133333333333333f;

uint32_t packHudColorAbgr(uint8_t red, uint8_t green, uint8_t blue)
{
    return 0xff000000u | (uint32_t(blue) << 16) | (uint32_t(green) << 8) | uint32_t(red);
}

int spellInspectManaCostForMastery(const SpellEntry &spellEntry, SkillMastery mastery)
{
    switch (mastery)
    {
        case SkillMastery::Expert:
            return spellEntry.expertManaCost;
        case SkillMastery::Master:
            return spellEntry.masterManaCost;
        case SkillMastery::Grandmaster:
            return spellEntry.grandmasterManaCost;
        case SkillMastery::Normal:
        case SkillMastery::None:
        default:
            return spellEntry.normalManaCost;
    }
}

SkillMastery spellInspectCasterMasteryForSpell(const Character *pCaster, uint32_t spellId)
{
    if (pCaster == nullptr)
    {
        return SkillMastery::Normal;
    }

    const std::optional<std::string> skillName = resolveMagicSkillName(spellId);

    if (!skillName)
    {
        return SkillMastery::Normal;
    }

    const CharacterSkill *pSkill = pCaster->findSkill(*skillName);

    if (pSkill == nullptr || pSkill->level == 0 || pSkill->mastery == SkillMastery::None)
    {
        return SkillMastery::Normal;
    }

    return pSkill->mastery;
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

int recoveryTicksFromSeconds(float recoverySeconds)
{
    return std::max(
        0,
        int(std::lround(std::max(0.0f, recoverySeconds) / OeRealtimeRecoveryScale * 128.0f)));
}

bool mainHandAttackUsesBlasterRecovery(const Character &character, const ItemTable &itemTable)
{
    const ItemDefinition *pMainHandItem = itemTable.get(character.equipment.mainHand);
    return pMainHandItem != nullptr && canonicalSkillName(pMainHandItem->skillGroup) == "Blaster";
}

std::string attackRecoveryInspectSupplement(
    const Character &character,
    const GameplayScreenRuntime &context,
    std::string_view statName)
{
    if (statName != "Attack" && statName != "Shoot")
    {
        return {};
    }

    if (context.itemTable() == nullptr)
    {
        return {};
    }

    const CharacterAttackProfile profile = GameMechanics::buildCharacterAttackProfile(
        character,
        context.itemTable(),
        context.spellTable(),
        characterAttackTuningFromSettings(context.settingsSnapshot()));

    if (statName == "Attack")
    {
        const float recoverySeconds =
            mainHandAttackUsesBlasterRecovery(character, *context.itemTable())
                ? profile.rangedRecoverySeconds
                : profile.meleeRecoverySeconds;
        return "Recovery time: " + std::to_string(recoveryTicksFromSeconds(recoverySeconds));
    }

    if (!profile.canShoot)
    {
        return "Recovery time: N/A";
    }

    return "Recovery time: " + std::to_string(recoveryTicksFromSeconds(profile.rangedRecoverySeconds));
}

std::string formatRemainingDuration(const GameplayScreenRuntime &context, float remainingSeconds)
{
    if (std::isinf(remainingSeconds))
    {
        return context.localizeHudText("Constant");
    }
    const int totalSeconds = std::max(0, int(std::lround(remainingSeconds)));
    const int hours = totalSeconds / 3600;
    const int minutes = (totalSeconds % 3600) / 60;
    const int seconds = totalSeconds % 60;

    if (hours > 0)
    {
        if (minutes > 0)
        {
            return context.localizeHudText(std::to_string(hours) + "h") + " "
                + context.localizeHudText(std::to_string(minutes) + "m");
        }

        return context.localizeHudText(std::to_string(hours) + "h");
    }

    if (minutes > 0)
    {
        if (seconds > 0 && minutes < 5)
        {
            return context.localizeHudText(std::to_string(minutes) + "m") + " "
                + context.localizeHudText(std::to_string(seconds) + "s");
        }

        return context.localizeHudText(std::to_string(minutes) + "m");
    }

    return context.localizeHudText(std::to_string(seconds) + "s");
}

std::string formatCharacterDetailDuration(const GameplayScreenRuntime &context, float remainingSeconds)
{
    if (std::isinf(remainingSeconds))
    {
        return context.localizeHudText("Constant");
    }
    const int totalSeconds = std::max(0, int(std::lround(remainingSeconds)));
    const int hours = totalSeconds / 3600;
    const int minutes = (totalSeconds % 3600) / 60;
    const int seconds = totalSeconds % 60;
    std::vector<std::string> parts;

    if (hours > 0)
    {
        parts.push_back(context.localizeHudText(std::to_string(hours) + (hours == 1 ? " Hour" : " Hours")));
    }

    if (minutes > 0)
    {
        parts.push_back(context.localizeHudText(std::to_string(minutes) + (minutes == 1 ? " Minute" : " Minutes")));
    }

    if (hours == 0 && seconds > 0)
    {
        parts.push_back(context.localizeHudText(std::to_string(seconds) + (seconds == 1 ? " Second" : " Seconds")));
    }

    if (parts.empty())
    {
        return context.localizeHudText("0 Seconds");
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
    if (!character.portraitTextureName.empty())
    {
        return character.portraitTextureName;
    }

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
            row.label = masteryDisplayName(pSkill->mastery) + ": " + row.label;
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
        "Throwing",
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
            row.label = masteryDisplayName(skill.mastery) + ": " + row.label;
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

    if (pClassSkillTable->getEffectiveCap(pCharacter->className, pCharacter->raceId, skillName) >= mastery)
    {
        return 0;
    }

    if (pClassSkillTable->getHighestPromotionEffectiveCap(pCharacter->className, pCharacter->raceId, skillName)
        >= mastery)
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

    const GameplayInputFrame *pInput = context.currentGameplayInputFrame();

    if (pInput == nullptr || !pInput->rightMouseButton.held)
    {
        return false;
    }

    const float mouseX = pInput->pointerX;
    const float mouseY = pInput->pointerY;

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
        || context.characterScreenReadOnly().alchemyBench.active
        || context.partyReadOnly() == nullptr
        || context.isAdventurersInnScreenActive()
        || context.characterInspectTable() == nullptr)
    {
        return;
    }

    const GameplayInputFrame *pInput = context.currentGameplayInputFrame();

    if (pInput == nullptr || !pInput->rightMouseButton.held)
    {
        return;
    }

    const float mouseX = pInput->pointerX;
    const float mouseY = pInput->pointerY;

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
                const std::string supplement =
                    context.localizeHudText(GameMechanics::buildExperienceInspectSupplement(*pCharacter));

                if (!supplement.empty())
                {
                    overlay.body += "\n" + supplement;
                }
            }

            const std::string recoverySupplement =
                attackRecoveryInspectSupplement(*pCharacter, context, row.pStatName);

            if (!recoverySupplement.empty())
            {
                overlay.body += "\n\n" + recoverySupplement;
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
    const std::optional<GameplayResolvedHudLayoutElement> viewport =
        context.resolveHudLayoutElement("CharacterSkillsViewport", width, height, 0, 0);
    if (!viewport || !GameplayHudCommon::isPointerInsideResolvedElement(*viewport, mouseX, mouseY))
    {
        return;
    }

    const CharacterSkillUiData skillUiData = buildCharacterSkillUiData(pCharacter);
    const float skillRowHeight = context.characterSkillRowHeight();

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
                std::string normalDescription = pEntry->normalDescription;
                std::string expertDescription = pEntry->expertDescription;
                std::string masterDescription = pEntry->masterDescription;
                std::string grandmasterDescription = pEntry->grandmasterDescription;

                if (row.canonicalName == "Blaster"
                    && context.settingsSnapshot().blasterSkillScaling == BlasterSkillScalingMode::ScalingDamage)
                {
                    overlay.body = context.localizeHudText(
                        "Blaster weapons provide an accurate ranged attack. With scaling damage enabled, only "
                        "Grandmaster rank adds damage per skill point.");
                    grandmasterDescription += "; " + context.localizeHudText("+1 damage per skill point");
                }

                overlay.normal.text = context.localizeHudText("Normal") + ": " + normalDescription;
                overlay.normal.availability = skillMasteryAvailability(
                    context.classSkillTable(),
                    pCharacter,
                    row.canonicalName,
                    SkillMastery::Normal);
                overlay.normal.visible = !normalDescription.empty();
                overlay.expert.text = context.localizeHudText("Expert") + ": " + expertDescription;
                overlay.expert.availability = skillMasteryAvailability(
                    context.classSkillTable(),
                    pCharacter,
                    row.canonicalName,
                    SkillMastery::Expert);
                overlay.expert.visible = !expertDescription.empty();
                overlay.master.text = context.localizeHudText("Master") + ": " + masterDescription;
                overlay.master.availability = skillMasteryAvailability(
                    context.classSkillTable(),
                    pCharacter,
                    row.canonicalName,
                    SkillMastery::Master);
                overlay.master.visible = !masterDescription.empty();
                overlay.grandmaster.text = context.localizeHudText("Grandmaster") + ": " + grandmasterDescription;
                overlay.grandmaster.availability = skillMasteryAvailability(
                    context.classSkillTable(),
                    pCharacter,
                    row.canonicalName,
                    SkillMastery::Grandmaster);
                overlay.grandmaster.visible = !grandmasterDescription.empty();
                overlay.skillBonus = pCharacter->skillBonus(row.canonicalName);
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
    GameplayScreenRuntime &context, int width, int height, bool showGameplayHud)
{
    GameplayUiController::BuffInspectOverlayState &overlay = context.buffInspectOverlay();
    overlay = {};
    const Party *pParty = context.partyReadOnly();
    const GameplayInputFrame *pInput = context.currentGameplayInputFrame();
    if (width <= 0 || height <= 0 || pParty == nullptr || pInput == nullptr || !showGameplayHud
        || context.itemInspectOverlayReadOnly().active)
    {
        return;
    }
    const auto anchor = [&](const GameplayResolvedHudLayoutElement &rect)
    {
        overlay.active = true;
        overlay.sourceX = rect.x;
        overlay.sourceY = rect.y;
        overlay.sourceWidth = rect.width;
        overlay.sourceHeight = rect.height;
    };
    const auto buffName = [&context](const char *pName)
    {
        const SpellTable *pSpells = context.spellTable();
        const SpellEntry *pSpell = pSpells != nullptr ? pSpells->findByName(pName) : nullptr;
        return pSpell != nullptr ? pSpell->name : context.localizeHudText(pName);
    };
    if (context.interactionState().personalBuffPopupMember)
    {
        const size_t member = *context.interactionState().personalBuffPopupMember;
        const Character *pCharacter = pParty->member(member);
        const std::optional<GameplayResolvedHudLayoutElement> rect =
            context.resolvePartyPortraitRect(width, height, member);
        if (pCharacter != nullptr && rect)
        {
            overlay.title = pCharacter->name;
            for (size_t b = 0; b < CharacterBuffCount; ++b)
            {
                const CharacterBuffState *pBuff = pParty->characterBuff(member, static_cast<CharacterBuffId>(b));
                if (pBuff != nullptr)
                {
                    appendPopupBodyLine(overlay.body, buffName(GameplayPersonalBuffNames[b]) + " - "
                        + formatRemainingDuration(context, pBuff->remainingSeconds));
                }
            }
            if (!overlay.body.empty())
            {
                anchor(*rect);
            }
            else
            {
                context.interactionState().personalBuffPopupMember.reset();
            }
        }
    }
    if (!pInput->rightMouseButton.held || context.currentHudScreenState() != GameplayHudScreenState::Gameplay)
    {
        return;
    }
    for (GameplayBuffPresentation panel : {GameplayBuffPresentation::Hero, GameplayBuffPresentation::Skull})
    {
        const std::optional<GameplayResolvedHudLayoutElement> rect =
            context.resolveHudLayoutElement(gameplayBuffPanelLayoutId(panel), width, height, 0, 0);
        if (!rect || !GameplayHudCommon::isPointerInsideResolvedElement(*rect, pInput->pointerX, pInput->pointerY))
        {
            continue;
        }
        overlay.title = context.localizeHudText("Active Party Buffs");
        overlay.body.clear();
        for (PartyBuffId id : sortedGameplayBuffs(*pParty))
        {
            const GameplayBuffHudDefinition &definition = GameplayBuffHudDefinitions[size_t(id)];
            if (definition.presentation == panel)
            {
                appendPopupBodyLine(overlay.body, buffName(definition.pName) + " - "
                    + formatRemainingDuration(context, pParty->partyBuff(id)->remainingSeconds));
            }
        }
        if (overlay.body.empty())
        {
            overlay.body = context.localizeHudText("No active buffs");
        }
        anchor(*rect);
        return;
    }
    std::optional<GameplayBuffHudEntry> inspected =
        gameplayMovementBuffAtPoint(context, width, height, pInput->pointerX, pInput->pointerY);
    for (const GameplayBuffHudEntry &entry : gameplayBuffHudEntries(context, width, height))
    {
        if (!GameplayHudCommon::isPointerInsideResolvedElement(entry.rect, pInput->pointerX, pInput->pointerY))
        {
            continue;
        }
        inspected = entry;
        break;
    }
    if (inspected)
    {
        const PartyBuffState *pBuff = pParty->partyBuff(inspected->id);
        overlay.title = buffName(GameplayBuffHudDefinitions[size_t(inspected->id)].pName);
        overlay.body = formatRemainingDuration(context, pBuff->remainingSeconds);
        if (pBuff->power > 0)
        {
            appendPopupBodyLine(overlay.body, context.localizeHudText("Power: " + std::to_string(pBuff->power)));
        }
        anchor(inspected->rect);
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

    const GameplayInputFrame *pInput = context.currentGameplayInputFrame();

    if (pInput == nullptr
        || !pInput->rightMouseButton.held
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
        || context.loadGameScreenState().active
        || context.interactionState().partyPortraitRightClickItemUseLatch)
    {
        return;
    }

    const float mouseX = pInput->pointerX;
    const float mouseY = pInput->pointerY;

    const Party &party = *context.partyReadOnly();
    const Character *pCharacter = nullptr;
    std::optional<GameplayScreenRuntime::ResolvedHudLayoutElement> sourceRect;
    std::optional<size_t> memberIndex;

    if (context.characterScreenReadOnly().open)
    {
        return;
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

    const CharacterSheetSummary summary = GameMechanics::buildCharacterSheetSummary(
        *pCharacter,
        context.itemTable(),
        nullptr,
        nullptr,
        characterAttackTuningFromSettings(context.settingsSnapshot()));

    overlay.active = true;
    const std::string characterName = pCharacter->name.empty() ? context.localizeHudText("Member") : pCharacter->name;
    const std::string characterClass =
        context.localizeHudText(displayClassName(
            !pCharacter->className.empty() ? pCharacter->className : pCharacter->role));
    overlay.title = characterClass.empty() ? characterName
        : characterName + " " + context.localizeHudText("the " + characterClass);
    overlay.body.clear();
    overlay.portraitTextureName = defaultCharacterPortraitTextureName(*pCharacter);
    overlay.hitPointsText = std::to_string(summary.health.current) + " / " + std::to_string(summary.health.maximum);
    overlay.spellPointsText =
        std::to_string(summary.spellPoints.current) + " / " + std::to_string(summary.spellPoints.maximum);
    overlay.conditionText = context.localizeHudText(summary.conditionText);
    overlay.quickSpellText = context.localizeHudText(summary.quickSpellText);
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
            line.name = context.localizeHudText(buffLine.pLabel);
            line.duration = formatCharacterDetailDuration(context, pBuff->remainingSeconds);
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

    const GameplayInputFrame *pInput = context.currentGameplayInputFrame();

    if (pInput == nullptr || !pInput->rightMouseButton.held)
    {
        return;
    }

    const float mouseX = pInput->pointerX;
    const float mouseY = pInput->pointerY;

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
        const SpellbookSchoolUiDefinition *pSpellSchoolDefinition = findSpellbookSchoolUiDefinitionForSpellId(spellId);
        const GameplayUiController::SpellbookSchool spellSchool =
            pSpellSchoolDefinition != nullptr ? pSpellSchoolDefinition->school : context.spellbookReadOnly().school;
        const Character *pActiveMember =
            context.partyReadOnly() != nullptr ? context.partyReadOnly()->activeMember() : nullptr;
        const SkillMastery casterMastery = spellInspectCasterMasteryForSpell(pActiveMember, spellId);

        overlay.school = spellbookSchoolDisplayName(spellSchool);
        overlay.manaCost = std::max(0, spellInspectManaCostForMastery(*pSpellEntry, casterMastery));
        overlay.hasManaCost = true;
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
    const float overlayScale = std::clamp(baseScale, 0.75f, MaxUiScale);
    const float centerX = std::round(static_cast<float>(width) * 0.5f);
    const float centerY = std::round(static_cast<float>(height) * 0.5f);
    const float armLength = std::round(3.0f * overlayScale);
    const float outlineWidth = 1.0f;
    const float armGap = std::max(outlineWidth + 1.0f, std::round(1.0f * overlayScale));
    const float stroke = std::max(1.0f, std::round(1.0f * overlayScale));
    const uint32_t dotColor = packHudColorAbgr(255, 250, 224);
    const uint32_t outlineColor = packHudColorAbgr(16, 20, 17);
    const std::optional<GameplayHudPaletteColor> dotColorTexel =
        context.gameplayUiRuntime().ensureHudPaletteColor(dotColor);
    const std::optional<GameplayHudPaletteColor> outlineColorTexel =
        context.gameplayUiRuntime().ensureHudPaletteColor(outlineColor);

    if (!dotColorTexel || !outlineColorTexel)
    {
        return;
    }

    // Keep the aiming center open, with a complete dark contour on every ivory arm.
    const float outlineStroke = stroke + outlineWidth * 2.0f;
    const float outlineArm = armLength + outlineWidth * 2.0f;
    const std::vector<GameplayHudBatchQuad> quads = {
        gameplayHudPaletteQuad(*outlineColorTexel, centerX - stroke * 0.5f - outlineWidth,
            centerY - armGap - armLength - outlineWidth, outlineStroke, outlineArm),
        gameplayHudPaletteQuad(*outlineColorTexel, centerX - stroke * 0.5f - outlineWidth,
            centerY + armGap - outlineWidth, outlineStroke, outlineArm),
        gameplayHudPaletteQuad(*outlineColorTexel, centerX - armGap - armLength - outlineWidth,
            centerY - stroke * 0.5f - outlineWidth, outlineArm, outlineStroke),
        gameplayHudPaletteQuad(*outlineColorTexel, centerX + armGap - outlineWidth,
            centerY - stroke * 0.5f - outlineWidth, outlineArm, outlineStroke),
        gameplayHudPaletteQuad(*dotColorTexel, centerX - stroke * 0.5f, centerY - armGap - armLength,
            stroke, armLength),
        gameplayHudPaletteQuad(*dotColorTexel, centerX - stroke * 0.5f, centerY + armGap, stroke, armLength),
        gameplayHudPaletteQuad(*dotColorTexel, centerX - armGap - armLength, centerY - stroke * 0.5f,
            armLength, stroke),
        gameplayHudPaletteQuad(*dotColorTexel, centerX + armGap, centerY - stroke * 0.5f, armLength, stroke)};
    context.submitHudQuadBatch(quads);
}
} // namespace OpenYAMM::Game
