#include "game/rules/maw/MawPromotions.h"

#include <yaml-cpp/yaml.h>

#include <algorithm>
#include <exception>

namespace OpenYAMM::Game
{
bool MawPromotionData::loadFromYaml(const std::string &text, std::string &errorMessage)
{
    try
    {
        for (const auto &entry : YAML::Load(text)["kinds"])
        {
            const YAML::Node &node = entry.second;
            MawPromotionKind kind;
            kind.mm6 = node["mm6"].as<std::vector<uint32_t>>();
            kind.mm7 = node["mm7"].as<std::vector<uint32_t>>();
            kind.mm8 = node["mm8"].as<uint32_t>();
            kind.mm8Award = node["mm8_award"] ? node["mm8_award"].as<uint32_t>() : 0;
            kind.mm8SecondBit = node["mm8_qbit2"] ? node["mm8_qbit2"].as<uint32_t>() : 0;
            kind.mm9 = node["mm9"] ? node["mm9"].as<std::vector<uint32_t>>() : std::vector<uint32_t> {};
            kind.mid = node["mid"] ? node["mid"].as<std::vector<uint32_t>>() : std::vector<uint32_t> {};
            kinds[entry.first.as<uint32_t>()] = std::move(kind);
        }
    }
    catch (const std::exception &exception)
    {
        errorMessage = exception.what();
        return false;
    }

    return true;
}

int mawPromotionWorlds(
    const MawPromotionKind &kind,
    const std::function<bool(uint32_t)> &hasQuestBit,
    const std::function<bool(uint32_t)> &hasAward)
{
    const auto any = [&hasQuestBit](const std::vector<uint32_t> &bits)
    {
        return std::any_of(bits.begin(), bits.end(), hasQuestBit);
    };
    const bool mm8 = hasQuestBit(kind.mm8) || (kind.mm8Award != 0 && hasAward(kind.mm8Award))
        || (kind.mm8SecondBit != 0 && hasQuestBit(kind.mm8SecondBit));
    return int(any(kind.mm6)) + int(any(kind.mm7)) + int(mm8) + int(any(kind.mm9));
}
}
