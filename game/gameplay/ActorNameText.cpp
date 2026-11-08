#include "game/gameplay/ActorNameText.h"

#include "engine/Localization.h"
#include "game/rules/maw/MawMonsterRules.h"

#include <string_view>

namespace OpenYAMM::Game
{
std::string localizedActorName(const std::string &englishName)
{
    const std::string whole = Engine::localizeKnown(englishName);

    if (whole != englishName)
    {
        return whole;
    }

    constexpr std::string_view Risen = "Resurrected ";

    if (englishName.starts_with(Risen))
    {
        return Engine::tr("Resurrected {monster}", {{"monster", localizedActorName(englishName.substr(Risen.size()))}});
    }

    for (uint8_t affix = 1; affix <= uint8_t(MawBossAffix::Skilled); ++affix)
    {
        const std::string affixName = mawBossAffixName(MawBossAffix(affix));

        if (!affixName.empty() && englishName.size() > affixName.size() + 1 && englishName.starts_with(affixName + " "))
        {
            return Engine::tr("{affix} {monster}",
                              {{"affix", Engine::trc("monster affix", affixName)},
                               {"monster", Engine::localize(englishName.substr(affixName.size() + 1))}});
        }
    }

    return Engine::localize(englishName);
}
}
