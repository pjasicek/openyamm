#include "game/ui/GameplayBuffHud.h"
#include "engine/Localization.h"
#include "game/ui/GameplayHudOverlaySupport.h"

#include "game/gameplay/GameMechanics.h"
#include "game/gameplay/GameplayInputFrame.h"
#include "game/items/InventoryBags.h"
#include "game/items/ItemRuntime.h"
#include "game/mm9/Mm9HirelingHud.h"
#include "game/mm9/Mm9HirelingTable.h"
#include "game/party/PartySpellSystem.h"
#include "game/party/SkillData.h"
#include "game/party/SpellSchool.h"
#include "game/rules/GameRules.h"
#include "game/tables/ItemTable.h"
#include "game/ui/GameplayHudCommon.h"
#include "game/ui/GameplayJournalAuras.h"
#include "game/ui/GameplayMapProgressBar.h"
#include "game/ui/GameplayPortraitGems.h"
#include "game/ui/InventoryBagOverview.h"
#include "game/gameplay/GameplayScreenRuntime.h"
#include "game/ui/SpellbookUiLayout.h"

#include <bx/math.h>

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <span>
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
    const std::string skillName = pMainHandItem != nullptr ? canonicalSkillName(pMainHandItem->skillGroup) : "";
    return skillName == "Blaster";
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

    // Rules that decide the recovery themselves (MAW: weapon delay, speed, Haste) show theirs.
    const CombatRules &combatRules = boundGameRules().combat;
    const bool blasterMelee = mainHandAttackUsesBlasterRecovery(character, *context.itemTable());

    if (const std::optional<int> ticks = combatRules.characterAttackRecoveryTicks(character,
            statName == "Attack" && !blasterMelee ? CharacterAttackMode::Melee
                : blasterMelee                    ? CharacterAttackMode::Blaster
                                                  : CharacterAttackMode::Bow,
            *context.itemTable(), context.standardItemEnchantTable(), context.specialItemEnchantTable());
        ticks && (statName == "Attack" || profile.canShoot))
    {
        return Engine::tr("Recovery time: {ticks}", {{"ticks", int64_t(*ticks)}});
    }

    if (statName == "Attack")
    {
        const float recoverySeconds =
            mainHandAttackUsesBlasterRecovery(character, *context.itemTable())
                ? profile.rangedRecoverySeconds
                : profile.meleeRecoverySeconds;
        return Engine::tr("Recovery time: {ticks}", {{"ticks", recoveryTicksFromSeconds(recoverySeconds)}});
    }

    if (!profile.canShoot)
    {
        return Engine::tr("Recovery time: N/A");
    }

    return Engine::tr("Recovery time: {ticks}", {{"ticks", recoveryTicksFromSeconds(profile.rangedRecoverySeconds)}});
}

// A member buff's name: the rules' name for its spell when they rename it (MAW's Vampiric Aura), else the slot's.
std::string personalBuffName(
    const SpellTable *pSpellTable,
    const Party &party,
    const Character &member,
    size_t buffIndex,
    const CharacterBuffState &buff)
{
    const SpellEntry *pSpell =
        buff.spellId != 0 && pSpellTable != nullptr ? pSpellTable->findById(int(buff.spellId)) : nullptr;

    if (pSpell != nullptr)
    {
        const std::string name = gameRulesFor(&party).spells.spellName(member, *pSpell);

        if (name != pSpell->name)
        {
            return name;
        }
    }

    return GameplayPersonalBuffNames[buffIndex];
}

// A buff's time left, or the rules' text while a member holds it as an aura.
std::string formatBuffDuration(
    const Party &party,
    uint32_t spellId,
    float remainingSeconds,
    std::string (*pFormat)(float))
{
    const std::optional<std::string> held = gameRulesFor(&party).spells.heldBuffText(party, spellId);
    return held ? *held : pFormat(remainingSeconds);
}

std::string formatCharacterDetailDuration(float remainingSeconds)
{
    if (std::isinf(remainingSeconds))
    {
        return Engine::tr("Constant");
    }
    const int totalSeconds = std::max(0, int(std::lround(remainingSeconds)));
    const int hours = totalSeconds / 3600;
    const int minutes = (totalSeconds % 3600) / 60;
    const int seconds = totalSeconds % 60;
    std::vector<std::string> parts;

    if (hours > 0)
    {
        parts.push_back(Engine::trn("{value} Hour", "{value} Hours", uint64_t(hours), {{"value", hours}}));
    }

    if (minutes > 0)
    {
        parts.push_back(Engine::trn("{value} Minute", "{value} Minutes", uint64_t(minutes), {{"value", minutes}}));
    }

    if (hours == 0 && seconds > 0)
    {
        parts.push_back(Engine::trn("{value} Second", "{value} Seconds", uint64_t(seconds), {{"value", seconds}}));
    }

    if (parts.empty())
    {
        return Engine::trn("{value} Second", "{value} Seconds", uint64_t(int64_t(0)), {{"value", int64_t(0)}});
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

// The held-RMB inspection of an MM9 hireling (devdocs/mm9/MM9_HIRELINGS_PLAN.md phase 6): the members' popup with the
// hireling's rows from its table row and its state (shared formulas: armour class and resistances with buffs).
void fillHirelingDetailOverlay(
    const GameplayScreenRuntime &context,
    const Party &party,
    size_t combatantIndex,
    GameplayUiController::CharacterDetailOverlayState &overlay)
{
    const Mm9PartyHireling *pHireling = party.hirelingCombatant(combatantIndex);

    if (pHireling == nullptr)
    {
        return;
    }

    const Character &hireling = pHireling->character;
    const Mm9HirelingTable *pTable = context.mm9HirelingTable();
    const Mm9Hireling *pRow = pTable != nullptr ? pTable->find(pHireling->rudeId) : nullptr;
    const CharacterSheetSummary summary = GameMechanics::buildCharacterSheetSummary(
        hireling, context.itemTable(), nullptr, nullptr, characterAttackTuningFromSettings(context.settingsSnapshot()));
    overlay.active = true;
    overlay.title = Engine::localize(hireling.name);
    overlay.portraitTextureName = hireling.portraitTextureName;
    std::vector<std::string> &lines = overlay.statLines;
    lines.push_back(Engine::tr("Level: {value}", {{"value", hireling.level}}));
    lines.push_back(Engine::tr("Hit Points : {value}",
        {{"value", std::to_string(summary.health.current) + " / " + std::to_string(summary.health.maximum)}}));
    // The row's armour class sits in armorClassModifier, on top of the sheet's (as the monster hit check reads it).
    lines.push_back(Engine::tr("Armor Class : {value}",
        {{"value", summary.armorClass.actual + hireling.armorClassModifier}}));
    lines.push_back(Engine::tr("Condition: {condition}",
        {{"condition", Engine::localizeKnown(summary.conditionText)}}));

    if (pRow != nullptr)
    {
        const std::string melee = formatMm9HirelingAttack(pRow->attack1);
        const std::string ranged = formatMm9HirelingAttack(pRow->attack2);

        if (!melee.empty())
        {
            lines.push_back(Engine::tr("Attack: {attack}", {{"attack", melee}}));
        }

        if (!ranged.empty())
        {
            lines.push_back(Engine::tr("Ranged: {attack}", {{"attack", ranged}}));
        }

        for (const Mm9HirelingSpell &spell : pRow->spells)
        {
            const SpellEntry *pSpell = context.spellTable() != nullptr
                ? context.spellTable()->findByName(spell.name) : nullptr;
            const std::string spellName = pSpell != nullptr ? Engine::localize(pSpell->name, "spell") : std::string();
            lines.push_back(Engine::tr("Spell: {spell}", {{"spell", formatMm9HirelingSpell(spell, spellName)}}));
        }
    }

    // One item of a list joined with ", ": the school's name and its value.
    const auto resistance = [](std::string_view name, const CharacterSheetValue &value)
    {
        return Engine::tr("{school} {value}",
            {{"school", Engine::tr(name)},
             {"value", value.infinite ? Engine::tr("Immune") : std::to_string(value.actual)}});
    };
    lines.push_back(Engine::tr("Resist: {resistances}",
        {{"resistances", resistance(Engine::trNoop("Fire"), summary.fireResistance) + ", "
            + resistance(Engine::trNoop("Air"), summary.airResistance) + ", "
            + resistance(Engine::trNoop("Water"), summary.waterResistance) + ", "
            + resistance(Engine::trNoop("Earth"), summary.earthResistance)}}));
    // The six schools the shared damage rules read; they take Spirit as Body and give Light, Dark and Physical none,
    // so the row's values for those are not shown. The second row is indented under the first's list.
    lines.push_back("        " + resistance(Engine::trNoop("Mind"), summary.mindResistance) + ", "
        + resistance(Engine::trNoop("Body"), summary.bodyResistance));

    for (size_t buffIndex = 0; buffIndex < CharacterBuffCount; ++buffIndex)
    {
        const CharacterBuffState *pBuff = party.characterBuff(combatantIndex, static_cast<CharacterBuffId>(buffIndex));

        if (pBuff == nullptr)
        {
            continue;
        }

        GameplayUiController::CharacterDetailOverlayState::ActiveSpellLine line = {};
        line.name = personalBuffName(context.spellTable(), party, hireling, buffIndex, *pBuff);
        line.duration =
            formatBuffDuration(party, pBuff->spellId, pBuff->remainingSeconds, formatCharacterDetailDuration);
        overlay.activeSpells.push_back(std::move(line));
    }
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
    std::vector<CharacterSkillUiRow> techRows;
};

// Which rows a stats page shows: always, only the usual Condition and Quick Spell rows, or only the four tighter rows
// of powers that replace them (SkillRules::compactStatPowerRows, MAW).
enum class CharacterStatRowMode : uint8_t
{
    Always,
    Usual,
    PowerRows,
};

struct CharacterStatRowDefinition
{
    const char *pStatName;
    const char *pLabelId;
    const char *pValueId;
    CharacterStatRowMode mode = CharacterStatRowMode::Always;
};

constexpr std::array<CharacterStatRowDefinition, 30> CharacterStatRows = {{
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
    {"Condition", "CharacterStatConditionLabel", "CharacterStatConditionValue", CharacterStatRowMode::Usual},
    {"QuickSpell", "CharacterStatQuickSpellLabel", "CharacterStatQuickSpellValue", CharacterStatRowMode::Usual},
    // The rows of powers (MAW); Spell Power and Vitality have no stat table entries.
    {"Condition", "CharacterStatPowerRow1Label", "CharacterStatPowerRow1Value", CharacterStatRowMode::PowerRows},
    {"QuickSpell", "CharacterStatPowerRow2Label", "CharacterStatPowerRow2Value", CharacterStatRowMode::PowerRows},
    {"SpellPower", "CharacterStatPowerRow3Label", "CharacterStatPowerRow3Value", CharacterStatRowMode::PowerRows},
    {"Vitality", "CharacterStatPowerRow4Label", "CharacterStatPowerRow4Value", CharacterStatRowMode::PowerRows},
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
    if (mastery == SkillMastery::Grandmaster)
    {
        return Engine::tr("Grand");
    }

    return Engine::localize(masteryDisplayName(mastery), "mastery");
}

void appendCharacterSkillUiRows(
    const Character &character,
    std::vector<CharacterSkillUiRow> &rows,
    std::unordered_set<std::string> &shownSkillNames,
    const std::vector<std::string> &skillNames)
{
    for (const std::string &canonicalName : skillNames)
    {
        const CharacterSkill *pSkill = character.findSkillByCanonicalName(canonicalName);

        if (pSkill == nullptr)
        {
            continue;
        }

        CharacterSkillUiRow row = {};
        row.canonicalName = canonicalName;
        row.label = Engine::localize(displaySkillName(pSkill->name), "skill");

        if (pSkill->mastery != SkillMastery::None && pSkill->mastery != SkillMastery::Normal)
        {
            row.label = Engine::tr("{skill} {mastery}",
                {{"skill", row.label}, {"mastery", skillPageMasteryDisplayName(pSkill->mastery)}});
        }

        row.level = std::to_string(pSkill->level);
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
        skillSheetGroupSkillNames(SkillSheetGroup::Weapons));
    appendCharacterSkillUiRows(
        *pCharacter,
        data.magicRows,
        shownSkillNames,
        skillSheetGroupSkillNames(SkillSheetGroup::Magic));
    appendCharacterSkillUiRows(
        *pCharacter,
        data.armorRows,
        shownSkillNames,
        skillSheetGroupSkillNames(SkillSheetGroup::Armor));
    appendCharacterSkillUiRows(
        *pCharacter,
        data.miscRows,
        shownSkillNames,
        skillSheetGroupSkillNames(SkillSheetGroup::Misc));
    appendCharacterSkillUiRows(
        *pCharacter,
        data.techRows,
        shownSkillNames,
        skillSheetGroupSkillNames(SkillSheetGroup::Technology));

    std::vector<CharacterSkillUiRow> extraMiscRows;

    for (const auto &[skillName, skill] : pCharacter->skills)
    {
        if (shownSkillNames.contains(skillName))
        {
            continue;
        }

        CharacterSkillUiRow row = {};
        row.canonicalName = skillName;
        row.label = Engine::localize(displaySkillName(skill.name), "skill");

        if (skill.mastery != SkillMastery::None && skill.mastery != SkillMastery::Normal)
        {
            row.label = Engine::tr("{skill} {mastery}",
                {{"skill", row.label}, {"mastery", skillPageMasteryDisplayName(skill.mastery)}});
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

std::string GameplayHudOverlaySupport::formatRemainingDuration(float remainingSeconds)
{
    if (std::isinf(remainingSeconds))
    {
        return Engine::tr("Constant");
    }
    const int totalSeconds = std::max(0, int(std::lround(remainingSeconds)));
    const int hours = totalSeconds / 3600;
    const int minutes = (totalSeconds % 3600) / 60;
    const int seconds = totalSeconds % 60;

    if (hours > 0)
    {
        if (minutes > 0)
        {
            return Engine::tr("{hours}h {minutes}m", {{"hours", hours}, {"minutes", minutes}});
        }

        return Engine::tr("{hours}h", {{"hours", hours}});
    }

    if (minutes > 0)
    {
        if (seconds > 0 && minutes < 5)
        {
            return Engine::tr("{minutes}m {seconds}s", {{"minutes", minutes}, {"seconds", seconds}});
        }

        return Engine::tr("{minutes}m", {{"minutes", minutes}});
    }

    return Engine::tr("{seconds}s", {{"seconds", seconds}});
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

        if (requireOpaqueHitTest && !it->wholeAreaHits && !context.isOpaqueHudPixelAtPoint(*it, mouseX, mouseY))
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
        overlay.sourceBag = it->sourceBag;
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
        const bool powerRows = gameRulesFor(context.partyReadOnly()).skills.compactStatPowerRows();

        for (const CharacterStatRowDefinition &row : CharacterStatRows)
        {
            if (row.mode != CharacterStatRowMode::Always
                && (row.mode == CharacterStatRowMode::PowerRows) != powerRows)
            {
                continue;
            }

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
            const Party *pStatParty = context.partyReadOnly();
            // A row the rules relabel or add names and explains itself (MAW: the powers and Vitality).
            const std::optional<CharacterStatRowText> relabelled = pStatParty != nullptr
                ? gameRulesFor(pStatParty).skills.statRowText(*pStatParty, *pCharacter, row.pStatName)
                : std::nullopt;

            if ((pEntry == nullptr || pEntry->description.empty()) && !(relabelled && !relabelled->popupTitle.empty()))
            {
                return;
            }

            overlay.active = true;
            overlay.title = Engine::localize(
                relabelled && !relabelled->popupTitle.empty() ? relabelled->popupTitle : pEntry->name, "stat");
            overlay.body = pEntry != nullptr ? Engine::localize(pEntry->description) : std::string();

            if (pStatParty != nullptr)
            {
                overlay.body =
                    gameRulesFor(pStatParty).skills.statTooltip(*pStatParty, *pCharacter, row.pStatName, overlay.body);
            }

            if (std::string_view(row.pStatName) == "Experience")
            {
                const std::string supplement = GameMechanics::buildExperienceInspectSupplement(
                    *pCharacter,
                    gameRulesFor(context.partyReadOnly()).experience);

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
                // The rules may rename a skill (a class's own school name); the row's label also carries the mastery,
                // so it is not the title (audit STD2-U1).
                const std::string ruledName = pCharacter != nullptr
                    ? gameRulesFor(context.partyReadOnly()).skills.skillDisplayName(*pCharacter, row.canonicalName)
                    : displaySkillName(row.canonicalName);
                overlay.title = Engine::localize(
                    ruledName != displaySkillName(row.canonicalName) ? ruledName : pEntry->name, "skill");
                overlay.body = Engine::localize(pEntry->description);
                std::string normalDescription = Engine::localize(pEntry->normalDescription);
                std::string expertDescription = Engine::localize(pEntry->expertDescription);
                std::string masterDescription = Engine::localize(pEntry->masterDescription);
                std::string grandmasterDescription = Engine::localize(pEntry->grandmasterDescription);

                if (row.canonicalName == "Blaster"
                    && context.settingsSnapshot().blasterSkillScaling == BlasterSkillScalingMode::ScalingDamage)
                {
                    overlay.body = Engine::tr("Blaster weapons provide an accurate ranged attack. With scaling damage "
                                              "enabled, only Grandmaster rank adds damage per skill point.");
                    expertDescription = Engine::tr("Skill added to Attack Bonus (double effect)");
                    masterDescription = Engine::tr("Skill added to Attack Bonus (triple effect)");
                    grandmasterDescription =
                        Engine::tr("Skill added to Attack Bonus (quintuple effect); +1 damage per skill point");
                }

                // The rules' own text over the table's (MAW: its descriptions with the character's numbers).
                if (const Party *pPopupParty = context.partyReadOnly())
                {
                    const SkillTooltipText ruled = gameRulesFor(pPopupParty).skills.skillTooltip(*pPopupParty,
                        *pCharacter, row.canonicalName,
                        {overlay.body, {normalDescription, expertDescription, masterDescription,
                            grandmasterDescription}});
                    overlay.body = ruled.description;
                    normalDescription = ruled.masteryLines[0];
                    expertDescription = ruled.masteryLines[1];
                    masterDescription = ruled.masteryLines[2];
                    grandmasterDescription = ruled.masteryLines[3];
                    overlay.footer = ruled.footer;
                }

                overlay.normal.text = Engine::tr("Normal: {effect}", {{"effect", normalDescription}});
                overlay.normal.availability = skillMasteryAvailability(
                    context.classSkillTable(),
                    pCharacter,
                    row.canonicalName,
                    SkillMastery::Normal);
                overlay.normal.visible = !normalDescription.empty();
                overlay.expert.text = Engine::tr("Expert: {effect}", {{"effect", expertDescription}});
                overlay.expert.availability = skillMasteryAvailability(
                    context.classSkillTable(),
                    pCharacter,
                    row.canonicalName,
                    SkillMastery::Expert);
                overlay.expert.visible = !expertDescription.empty();
                overlay.master.text = Engine::tr("Master: {effect}", {{"effect", masterDescription}});
                overlay.master.availability = skillMasteryAvailability(
                    context.classSkillTable(),
                    pCharacter,
                    row.canonicalName,
                    SkillMastery::Master);
                overlay.master.visible = !masterDescription.empty();
                overlay.grandmaster.text = Engine::tr("Grandmaster: {effect}", {{"effect", grandmasterDescription}});
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

    if (tryShowSkillPopup("CharacterSkillsMiscListRegion", "CharacterSkillsMiscLevelHeader", skillUiData.miscRows))
    {
        return;
    }

    tryShowSkillPopup("CharacterSkillsTechListRegion", "CharacterSkillsTechLevelHeader", skillUiData.techRows);
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
                    const std::string duration =
                        formatBuffDuration(*pParty, pBuff->spellId, pBuff->remainingSeconds, formatRemainingDuration);
                    const std::string buffName = Engine::localize(
                        personalBuffName(context.spellTable(), *pParty, *pCharacter, b, *pBuff), "spell");
                    appendPopupBodyLine(overlay.body,
                        Engine::tr("{buff} - {duration}", {{"buff", buffName}, {"duration", duration}}));
                }
            }

            for (const GameplayPotionEffectLine &line : gameplayPotionEffectLines(*pCharacter, context.spellTable()))
            {
                appendPopupBodyLine(overlay.body, line.name + " - " + formatRemainingDuration(line.remainingSeconds));
            }

            for (const GameplayAuraLine &line : gameplayUnslottedAuraLines(*pParty, *pCharacter, context.spellTable()))
            {
                appendPopupBodyLine(overlay.body, line.name + " - " + line.heldText);
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
    // The map progress bar's popup, on hover.
    if (!overlay.active)
    {
        if (const std::optional<GameplayMapProgressBar::Popup> popup =
                GameplayMapProgressBar::popupAt(context, width, height, pInput->pointerX, pInput->pointerY))
        {
            overlay.title = popup->title;
            overlay.body = popup->body;
            overlay.above = true;
            anchor({popup->x, popup->y, popup->width, popup->height, 1.0f});
        }
    }
    // A class counter's popup, on hover over its gems.
    for (size_t i = 0; !overlay.active && i < std::min<size_t>(5, pParty->members().size()); ++i)
    {
        const PortraitCounter counter = pParty->rules().classes.portraitCounter(pParty->members()[i]);
        const std::string id = std::string(context.currentHudScreenState() == GameplayHudScreenState::Gameplay
            ? "ObsidianPc" : "ObsidianOverlayPc") + std::to_string(i + 1) + "Health";
        const UiLayoutManager::LayoutElement *pLayout =
            counter.kind != PortraitCounterKind::None ? context.findHudLayoutElement(id) : nullptr;
        const std::optional<GameplayResolvedHudLayoutElement> arc = pLayout != nullptr && pLayout->meterArc
            ? context.resolveHudLayoutElement(id, width, height, 0, 0) : std::nullopt;
        const std::optional<GameplayResolvedHudLayoutElement> gems =
            arc ? portraitCounterGemBounds(counter, *arc, pLayout->meterArc->strokeWidth) : std::nullopt;
        if (gems && GameplayHudCommon::isPointerInsideResolvedElement(*gems, pInput->pointerX, pInput->pointerY))
        {
            overlay.title = counter.title;
            for (const std::string &line : counter.notes)
            {
                appendPopupBodyLine(overlay.body, line);
            }
            overlay.above = true;
            anchor(*gems);
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
        overlay.title = Engine::tr("Active Party Buffs");
        overlay.body.clear();
        for (PartyBuffId id : sortedGameplayBuffs(*pParty))
        {
            const GameplayBuffHudDefinition &definition = GameplayBuffHudDefinitions[size_t(id)];
            if (definition.presentation == panel)
            {
                const PartyBuffState &buff = *pParty->partyBuff(id);
                appendPopupBodyLine(overlay.body, Engine::tr("{buff} - {duration}",
                    {{"buff", Engine::localize(definition.pName, "spell")},
                    {"duration",
                        formatBuffDuration(*pParty, buff.spellId, buff.remainingSeconds, formatRemainingDuration)}}));
            }
        }
        if (overlay.body.empty())
        {
            overlay.body = Engine::tr("No active buffs");
        }
        if (journalHasAuraPanel(context))
        {
            appendPopupBodyLine(overlay.body, Engine::tr("Click: open the aura panel"));
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
        overlay.title = Engine::localize(GameplayBuffHudDefinitions[size_t(inspected->id)].pName, "spell");
        overlay.body = formatBuffDuration(*pParty, pBuff->spellId, pBuff->remainingSeconds, formatRemainingDuration);
        if (pBuff->power > 0)
        {
            appendPopupBodyLine(overlay.body, Engine::tr("Power: {power}", {{"power", int64_t(pBuff->power)}}));
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
        else if (const std::optional<size_t> combatant =
                     context.resolveCombatantPortraitIndexAtPoint(width, height, mouseX, mouseY))
        {
            const std::optional<GameplayScreenRuntime::ResolvedHudLayoutElement> slot =
                context.resolveHirelingSlotRect(width, height, *combatant - party.members().size());

            if (slot)
            {
                fillHirelingDetailOverlay(context, party, *combatant, overlay);
                overlay.sourceX = slot->x;
                overlay.sourceY = slot->y;
                overlay.sourceWidth = slot->width;
                overlay.sourceHeight = slot->height;
            }

            return;
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
    const std::string characterName = pCharacter->name.empty() ? Engine::tr("Member") : pCharacter->name;
    // The rules name the class translated.
    const std::string characterClass = party.rules().classes.displayName(party, *pCharacter);
    overlay.title = characterClass.empty()
        ? characterName
        : Engine::tr("{name} the {class}", {{"name", characterName}, {"class", characterClass}});
    overlay.body.clear();
    overlay.portraitTextureName = defaultCharacterPortraitTextureName(*pCharacter);
    overlay.hitPointsText = std::to_string(summary.health.current) + " / " + std::to_string(summary.health.maximum);
    overlay.spellPointsText =
        std::to_string(summary.spellPoints.current) + " / " + std::to_string(summary.spellPoints.maximum);

    if (memberIndex)
    {
        // The share the member's auras hold, which the pool cannot fill (the hatched end of the portrait gauge).
        const int heldHitPoints = party.rules().spells.reservedHitPoints(party, *memberIndex);
        const int heldSpellPoints = party.rules().spells.reservedSpellPoints(party, *memberIndex);

        if (heldHitPoints > 0)
        {
            overlay.hitPointsText += " " + Engine::tr("({points} held)", {{"points", heldHitPoints}});
        }

        if (heldSpellPoints > 0)
        {
            overlay.spellPointsText += " " + Engine::tr("({points} held)", {{"points", heldSpellPoints}});
        }
    }
    // The detail overlay holds display text: the sheet summary's English names are translated here.
    overlay.conditionText = Engine::localizeKnown(summary.conditionText);
    overlay.quickSpellText = Engine::localizeKnown(summary.quickSpellText, "spell");

    if (const SpellEntry *pQuickSpell = context.spellTable() != nullptr && !pCharacter->quickSpellName.empty()
            ? context.spellTable()->findByName(pCharacter->quickSpellName, spellKnownBy(*pCharacter))
            : nullptr)
    {
        overlay.quickSpellText = Engine::localize(
            gameRulesFor(context.partyReadOnly()).spells.spellName(*pCharacter, *pQuickSpell), "spell");
    }
    overlay.activeSpells.clear();

    if (memberIndex)
    {
        for (size_t buffIndex = 0; buffIndex < CharacterBuffCount; ++buffIndex)
        {
            const CharacterBuffState *pBuff =
                party.characterBuff(*memberIndex, static_cast<CharacterBuffId>(buffIndex));

            if (pBuff == nullptr)
            {
                continue;
            }

            GameplayUiController::CharacterDetailOverlayState::ActiveSpellLine line = {};
            line.name = Engine::localize(
                personalBuffName(context.spellTable(), party, *pCharacter, buffIndex, *pBuff), "spell");
            line.duration =
                formatBuffDuration(party, pBuff->spellId, pBuff->remainingSeconds, formatCharacterDetailDuration);
            overlay.activeSpells.push_back(std::move(line));
        }

        if (const Character *pMember = party.member(*memberIndex))
        {
            for (const GameplayPotionEffectLine &potion : gameplayPotionEffectLines(*pMember, context.spellTable()))
            {
                GameplayUiController::CharacterDetailOverlayState::ActiveSpellLine line = {};
                line.name = potion.name;
                line.duration = formatCharacterDetailDuration(potion.remainingSeconds);
                overlay.activeSpells.push_back(std::move(line));
            }

            for (const GameplayAuraLine &aura : gameplayUnslottedAuraLines(party, *pMember, context.spellTable()))
            {
                GameplayUiController::CharacterDetailOverlayState::ActiveSpellLine line = {};
                line.name = aura.name;
                line.duration = aura.heldText;
                overlay.activeSpells.push_back(std::move(line));
            }
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
        const Party *pParty = context.partyReadOnly();
        const Character *pActiveMember = pParty != nullptr ? pParty->activeMember() : nullptr;
        const SkillMastery casterMastery = spellInspectCasterMasteryForSpell(pActiveMember, spellId);
        const GameRules &rules = gameRulesFor(pParty);
        const std::optional<std::string> schoolSkill = resolveMagicSkillName(spellId);
        // The cost the caster would pay (the rules may change it); the table cost when they cannot cast it.
        const std::optional<uint32_t> casterManaCost = pActiveMember != nullptr
            ? PartySpellSystem::manaCost(*pParty, *pActiveMember, *context.spellTable(), spellId)
            : std::nullopt;

        overlay.school = Engine::localize(spellbookSchoolDisplayName(spellSchool), "skill");

        if (pActiveMember != nullptr && schoolSkill)
        {
            const std::string schoolName = rules.skills.skillDisplayName(*pActiveMember, *schoolSkill);

            if (schoolName != displaySkillName(*schoolSkill))
            {
                overlay.school = Engine::localize(schoolName, "skill");
            }
        }

        overlay.manaCost = casterManaCost
            ? int(*casterManaCost)
            : std::max(0, spellInspectManaCostForMastery(*pSpellEntry, casterMastery));
        overlay.hasManaCost = true;
        const SpellTooltipText text = pActiveMember != nullptr
            ? rules.spells.spellTooltip(*pParty, *pActiveMember, *pSpellEntry)
            : SpellTooltipText {pSpellEntry->name, pSpellEntry->description,
                  {pSpellEntry->normalText, pSpellEntry->expertText, pSpellEntry->masterText,
                      pSpellEntry->grandmasterText}};
        // The table's text in the interface language; a ruleset's own text (MAW) arrives translated and filled in.
        const auto masteryLine = [&text](size_t mastery, std::string label)
        {
            return text.masteryLines[mastery].empty()
                ? std::string()
                : Engine::tr("{mastery}: {text}",
                             {{"mastery", label}, {"text", Engine::localizeKnown(text.masteryLines[mastery])}});
        };
        overlay.title = Engine::localize(text.name);
        overlay.body = Engine::localizeKnown(text.description);
        overlay.normal = masteryLine(0, Engine::tr("Normal"));
        overlay.expert = masteryLine(1, Engine::tr("Expert"));
        overlay.master = masteryLine(2, Engine::tr("Master"));
        overlay.grandmaster = masteryLine(3, Engine::tr("Grand Master"));
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

void GameplayHudOverlaySupport::renderItemRarityGlow(
    GameplayScreenRuntime &context,
    const InventoryItem &item,
    const GameplayHudTextureHandle &icon,
    float x,
    float y,
    float width,
    float height,
    float scale)
{
    const ItemRules &rules = gameRulesFor(context.partyReadOnly()).items;
    const std::string &mode = context.settingsSnapshot().rarityGlow;
    const GameplayInputFrame *pInput = context.currentGameplayInputFrame();

    if (!rules.glowsItemRarity())
    {
        return;
    }

    if (mode != "always"
        && !(mode == "hold" && pInput != nullptr && pInput->action(KeyboardAction::ShowItemRarity).held))
    {
        return;
    }

    // A drop the loot filter left where it fell is outlined grey instead (RulesetLootFilter::leaveOnGround).
    std::optional<uint32_t> color = item.rulesetFields.lootFiltered != 0
        ? std::optional<uint32_t>(0x8c8c8cu)
        : rules.nameColor(item);

    // Artifacts, relics and special items (the item table's material: Cycle of Life) without a colour of the rules
    // glow teal.
    const ItemDefinition *pDefinition =
        context.itemTable() != nullptr ? context.itemTable()->get(item.objectDescriptionId) : nullptr;

    if (!color && pDefinition != nullptr && pDefinition->rarity != ItemRarity::Common)
    {
        color = 0x20d8b8u;
    }

    if (!color)
    {
        return;
    }

    // nameColor is 0xRRGGBB; the HUD textures are ABGR.
    const uint32_t colorAbgr = 0xff000000u | ((*color & 0xffu) << 16) | (*color & 0xff00u) | ((*color >> 16) & 0xffu);
    const bgfx::TextureHandle silhouette = context.gameplayUiRuntime().ensureHudTextureColor(icon, colorAbgr);

    if (!bgfx::isValid(silhouette))
    {
        return;
    }

    // A faint outer ring and a stronger inner one, each the silhouette shifted eight ways.
    struct Ring
    {
        float radius;
        uint32_t alpha;
    };
    constexpr std::array<Ring, 2> Rings = {Ring{2.4f, 0x55}, Ring{1.2f, 0xc0}};
    constexpr float Diagonal = 0.70710678f;
    constexpr std::array<std::pair<float, float>, 8> Directions = {{
        {1, 0}, {-1, 0}, {0, 1}, {0, -1}, {Diagonal, Diagonal}, {Diagonal, -Diagonal}, {-Diagonal, Diagonal},
        {-Diagonal, -Diagonal}}};
    std::array<GameplayHudBatchQuad, Rings.size() * Directions.size()> quads;
    size_t index = 0;

    for (const Ring &ring : Rings)
    {
        const float radius = std::max(1.0f, ring.radius * scale);

        for (const auto &[directionX, directionY] : Directions)
        {
            GameplayHudBatchQuad &quad = quads[index++];
            quad.textureHandle = silhouette;
            quad.x = x + directionX * radius;
            quad.y = y + directionY * radius;
            quad.width = width;
            quad.height = height;
            quad.tintAbgr = (ring.alpha << 24) | 0x00ffffffu;
        }
    }

    context.gameplayUiRuntime().submitHudQuadBatch(quads);
}

bool GameplayHudOverlaySupport::bagOverviewActive(const GameplayScreenRuntime &context)
{
#if defined(__ANDROID__)
    // Half-size cells are too small to touch; Android shows one bag at full size.
    static_cast<void>(context);
    return false;
#else
    const Party *pParty = context.partyReadOnly();
    return pParty != nullptr && !context.characterScreenReadOnly().inventoryBagZoomed
        && context.characterScreenReadOnly().page == GameplayUiController::CharacterPage::Inventory
        && !context.isAdventurersInnCharacterSourceActive()
        && !(context.utilitySpellOverlayReadOnly().active
            && context.utilitySpellOverlayReadOnly().mode
                == GameplayUiController::UtilitySpellOverlayMode::InventoryTarget)
        && gameRulesFor(pParty).items.bagCount(*pParty) > 1;
#endif
}

bool GameplayHudOverlaySupport::shopBagOverviewActive(const GameplayScreenRuntime &context)
{
#if defined(__ANDROID__)
    static_cast<void>(context);
    return false;
#else
    const GameplayUiController::InventoryNestedOverlayState &overlay = context.inventoryNestedOverlay();
    const Party *pParty = context.partyReadOnly();
    return pParty != nullptr && overlay.active && !overlay.bagZoomed
        && (overlay.mode == GameplayUiController::InventoryNestedOverlayMode::ShopDisplay
            || overlay.mode == GameplayUiController::InventoryNestedOverlayMode::ShopSell
            || overlay.mode == GameplayUiController::InventoryNestedOverlayMode::ShopIdentify
            || overlay.mode == GameplayUiController::InventoryNestedOverlayMode::ShopRepair)
        && gameRulesFor(pParty).items.bagCount(*pParty) > 1;
#endif
}

bool GameplayHudOverlaySupport::inventoryTabsShown(const GameplayScreenRuntime &context)
{
    const Party *pParty = context.partyReadOnly();
    return pParty != nullptr && context.characterScreenReadOnly().open
        && context.characterScreenReadOnly().page == GameplayUiController::CharacterPage::Inventory
        && !context.isAdventurersInnCharacterSourceActive()
        && InventoryBags::tabCount(gameRulesFor(pParty).items.bagCount(*pParty)) > 1;
}

std::optional<GameplayResolvedHudLayoutElement> GameplayHudOverlaySupport::inventorySearchBox(
    const GameplayScreenRuntime &context,
    int width,
    int height)
{
    std::optional<GameplayResolvedHudLayoutElement> box =
        context.resolveHudLayoutElement("CharacterInventorySearch", width, height, 0, 0);

    if (!box || !inventoryTabsShown(context))
    {
        return box;
    }

    const std::optional<GameplayResolvedHudLayoutElement> lastTab =
        context.resolveHudLayoutElement("CharacterInventoryTab5", width, height, 0, 0);

    if (lastTab)
    {
        const float left = lastTab->x + lastTab->width + std::round(8.0f * box->scale);
        box->width = std::max(0.0f, box->x + box->width - left);
        box->x = left;
    }

    return box;
}

void GameplayHudOverlaySupport::renderBagOverview(
    GameplayScreenRuntime &context,
    const GameplayResolvedHudLayoutElement &grid,
    const Character &character,
    const std::function<void(const InventoryBagOverview::Slot &, uint8_t)> &renderBag)
{
    GameplayUiRuntime &ui = context.gameplayUiRuntime();
    const float scale = grid.scale;
    const std::optional<GameplayHudTextureHandle> backdrop =
        ui.ensureSolidHudTextureLoaded("__bag_overview_backdrop__", 0xff121714u);
    const std::optional<GameplayHudTextureHandle> bronze =
        ui.ensureSolidHudTextureLoaded("__bag_overview_divider__", 0xff4f7d98u);
    const std::optional<GameplayHudTextureHandle> edge =
        ui.ensureSolidHudTextureLoaded("__bag_overview_edge__", 0xff2c3a40u);
    const std::optional<GameplayHudTextureHandle> surface = ui.ensureHudTextureLoaded("obsidian_inventory_surface");

    if (backdrop)
    {
        context.submitHudTexturedQuad(*backdrop, grid.x, grid.y, grid.width, grid.height);
    }

    // The grid part of the inventory page's surface (CharacterInventoryGrid at 7,8 on the 468 x 346 page).
    constexpr float PageWidth = 468.0f;
    constexpr float PageHeight = 346.0f;
    constexpr float GridLeft = 7.0f;
    constexpr float GridTop = 8.0f;
    constexpr float GridWidth = 448.0f;
    constexpr float GridHeight = 288.0f;
    const float line = std::max(1.0f, std::round(scale));

    const int firstBag = InventoryBagOverview::firstBag(character);

    for (int bag = firstBag; bag < firstBag + InventoryBagOverview::Bags; ++bag)
    {
        const InventoryBagOverview::Slot slot = InventoryBagOverview::slot(grid, bag);

        if (surface)
        {
            ui.submitHudTexturedQuad(surface->textureHandle, slot.x, slot.y, slot.width, slot.height,
                GridLeft / PageWidth, GridTop / PageHeight, (GridLeft + GridWidth) / PageWidth,
                (GridTop + GridHeight) / PageHeight);
        }

        if (edge)
        {
            context.submitHudTexturedQuad(*edge, slot.x - line, slot.y - line, slot.width + 2 * line, line);
            context.submitHudTexturedQuad(*edge, slot.x - line, slot.y + slot.height, slot.width + 2 * line, line);
            context.submitHudTexturedQuad(*edge, slot.x - line, slot.y, line, slot.height);
            context.submitHudTexturedQuad(*edge, slot.x + slot.width, slot.y, line, slot.height);
        }

        renderBag(slot, uint8_t(bag));
        // The bag's tags in its bottom right corner, the place a bag fills last.
        const float tagSize = std::round(16.0f * scale);
        const float tagInset = std::round(2.0f * scale);
        renderBagTagMarks(context, character, uint8_t(bag), slot.x + slot.width - 2 * tagSize - tagInset,
            slot.y + slot.height - tagSize - tagInset, 2 * tagSize, tagSize);
    }

    // The dividers: a bronze rule down the middle of each gap between the bags.
    if (bronze)
    {
        const InventoryBagOverview::Slot first = InventoryBagOverview::slot(grid, 0);
        const InventoryBagOverview::Slot last = InventoryBagOverview::slot(grid, InventoryBagOverview::Bags - 1);
        const float rule = std::max(2.0f, std::round(2.0f * scale));
        const float middleX = std::round((first.x + first.width + last.x - rule) * 0.5f);
        const float middleY = std::round((first.y + first.height + last.y - rule) * 0.5f);
        const float right = last.x + last.width;
        const float bottom = last.y + last.height;
        context.submitHudTexturedQuad(*bronze, middleX, first.y, rule, bottom - first.y);
        context.submitHudTexturedQuad(*bronze, first.x, middleY, right - first.x, rule);
    }
}

std::optional<GameplayHudOverlaySupport::InventoryCell> GameplayHudOverlaySupport::nestedInventoryCellAt(
    const GameplayScreenRuntime &context,
    int width,
    int height,
    float x,
    float y)
{
    const Party *pParty = context.partyReadOnly();
    const Character *pCharacter = pParty != nullptr ? pParty->activeMember() : nullptr;
    const std::optional<GameplayResolvedHudLayoutElement> grid =
        context.resolveInventoryNestedOverlayGridArea(width, height);

    if (pCharacter == nullptr || !grid)
    {
        return std::nullopt;
    }

    if (shopBagOverviewActive(context))
    {
        const int firstBag = InventoryBagOverview::firstBag(*pCharacter);

        for (int bag = firstBag; bag < firstBag + InventoryBagOverview::Bags; ++bag)
        {
            const InventoryBagOverview::Slot slot = InventoryBagOverview::slot(*grid, bag);

            if (InventoryBagOverview::insideGrid(slot, x, y))
            {
                const auto [gridX, gridY] = InventoryBagOverview::cellAt(slot, x, y);
                return InventoryCell{uint8_t(bag), gridX, gridY};
            }
        }

        return std::nullopt;
    }

    if (x < grid->x || x >= grid->x + grid->width || y < grid->y || y >= grid->y + grid->height)
    {
        return std::nullopt;
    }

    const float cellWidth = grid->width / float(Character::InventoryWidth);
    const float cellHeight = grid->height / float(Character::InventoryHeight);
    return InventoryCell{pCharacter->rulesetState.currentBag,
        uint8_t(std::clamp(int((x - grid->x) / cellWidth), 0, Character::InventoryWidth - 1)),
        uint8_t(std::clamp(int((y - grid->y) / cellHeight), 0, Character::InventoryHeight - 1))};
}

std::optional<ItemSearch::Query> GameplayHudOverlaySupport::inventorySearchQuery(const GameplayScreenRuntime &context)
{
    const GameplayUiController::CharacterScreenState &screen = context.characterScreenReadOnly();

    if (!screen.open || screen.page != GameplayUiController::CharacterPage::Inventory
        || context.isAdventurersInnCharacterSourceActive()
        || !gameRulesFor(context.partyReadOnly()).items.inventorySearch())
    {
        return std::nullopt;
    }

    ItemSearch::Query query = ItemSearch::parse(screen.inventorySearch);
    return query.empty() ? std::nullopt : std::optional<ItemSearch::Query>(std::move(query));
}

std::string GameplayHudOverlaySupport::itemSearchText(
    const GameplayScreenRuntime &context,
    const InventoryItem &item,
    const Character *pViewer)
{
    const ItemDefinition *pDefinition =
        context.itemTable() != nullptr ? context.itemTable()->get(item.objectDescriptionId) : nullptr;

    if (pDefinition == nullptr)
    {
        return {};
    }

    // One field a line, so that a quoted phrase stays within a field.
    std::string text = ItemRuntime::displayName(
        item, *pDefinition, context.standardItemEnchantTable(), context.specialItemEnchantTable());
    const auto add =
        [&text](const std::string &part)
        {
            if (!part.empty() && part != "0" && part != "N / A")
            {
                text += '\n';
                text += part;
            }
        };

    add(Engine::localize(pDefinition->unidentifiedName));
    add(pDefinition->skillGroup);
    add(pDefinition->equipStat);

    if (pDefinition->rarity != ItemRarity::Common)
    {
        add(Engine::localize(pDefinition->materialName));
    }

    if (item.broken)
    {
        add(Engine::tr("Broken"));
    }

    if (!item.identified && ItemRuntime::requiresIdentification(*pDefinition))
    {
        add(Engine::tr("Not identified"));
        return ItemSearch::toLower(text);
    }

    const ItemRules &rules = gameRulesFor(context.partyReadOnly()).items;
    add(rules.enchantDescription(
        item, *pDefinition, context.standardItemEnchantTable(), context.specialItemEnchantTable(), pViewer));

    for (const ItemInspectLine &line : rules.inspectLines(
             item, *pDefinition, context.standardItemEnchantTable(), context.specialItemEnchantTable(), pViewer))
    {
        add(line.text);
    }

    return ItemSearch::toLower(text);
}

void GameplayHudOverlaySupport::renderSearchDimmedItem(
    GameplayScreenRuntime &context,
    const GameplayHudTextureHandle &icon,
    float x,
    float y,
    float width,
    float height)
{
    GameplayHudBatchQuad quad;
    quad.textureHandle = icon.textureHandle;
    quad.x = x;
    quad.y = y;
    quad.width = width;
    quad.height = height;
    quad.tintAbgr = 0x5cffffffu;
    context.gameplayUiRuntime().submitHudQuadBatch(std::span<const GameplayHudBatchQuad>(&quad, 1));
}

void GameplayHudOverlaySupport::renderBagTagIcon(
    GameplayScreenRuntime &context,
    BagTag tag,
    float x,
    float y,
    float size)
{
    const std::optional<GameplayHudTextureHandle> icon = context.gameplayUiRuntime().ensureHudTextureLoaded(
        tag == BagTag::Crafting ? "obsidian_bag_tag_crafting" : "obsidian_bag_tag_alchemy");

    if (icon)
    {
        context.submitHudTexturedQuad(*icon, std::round(x), std::round(y), std::round(size), std::round(size));
    }
}

void GameplayHudOverlaySupport::renderBagTagMarks(
    GameplayScreenRuntime &context,
    const Character &character,
    uint8_t bag,
    float x,
    float y,
    float width,
    float size)
{
    if (InventoryBags::hasTag(character, bag, BagTag::Crafting))
    {
        renderBagTagIcon(context, BagTag::Crafting, x, y, size);
    }

    if (InventoryBags::hasTag(character, bag, BagTag::Alchemy))
    {
        renderBagTagIcon(context, BagTag::Alchemy, x + width - size, y, size);
    }
}
} // namespace OpenYAMM::Game
