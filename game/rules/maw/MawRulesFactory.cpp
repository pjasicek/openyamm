#include "game/rules/maw/MawRulesFactory.h"

#include "game/data/GameDataRepository.h"
#include "game/rules/maw/MawRules.h"

namespace OpenYAMM::Game
{
std::unique_ptr<MawRules> createMawRules(const GameDataRepository &data, const RulesetOptions &options)
{
    const MawMapLevels *pMapLevels = data.mawMapLevels();

    if (pMapLevels == nullptr)
    {
        return nullptr;
    }

    const MawItemData *pItemData = data.mawItemData();
    const MawPromotionData *pPromotionData = data.mawPromotionData();
    const MawCraftingData *pCraftingData = data.mawCraftingData();
    const MawTextData *pTextData = data.mawTextData();
    const MawDimensionData *pDimensionData = data.mawDimensionData();
    std::unique_ptr<MawRules> pRules = std::make_unique<MawRules>(
        options,
        *pMapLevels,
        pItemData != nullptr ? *pItemData : MawItemData{},
        pPromotionData != nullptr ? *pPromotionData : MawPromotionData{},
        pCraftingData != nullptr ? *pCraftingData : MawCraftingData{},
        pTextData != nullptr ? *pTextData : MawTextData{},
        pDimensionData != nullptr ? *pDimensionData : MawDimensionData{});
    pRules->setMapTable(&data.mapStats());
    pRules->setSpellTable(&data.spellTable());
    pRules->setItemTable(&data.itemTable());
    pRules->setClassMultiplierTable(&data.classMultiplierTable());
    pRules->setItemEnchantTables(&data.standardItemEnchantTable(), &data.specialItemEnchantTable());
    pRules->setTrainerHints({&data.classSkillTable(), &data.mapStats()});
    return pRules;
}
}
