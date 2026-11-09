#pragma once

#include <cstdint>
#include <functional>
#include <map>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
// The quest bits that count as one class kind's promotion completed on each world (rulesets/maw/data/promotions.yml,
// CL:7-60).
struct MawPromotionKind
{
    std::vector<uint32_t> mm6;
    std::vector<uint32_t> mm7;
    uint32_t mm8 = 0;
    // MM8's alternative: an award any member holds, or a second quest bit (0 for none).
    uint32_t mm8Award = 0;
    uint32_t mm8SecondBit = 0;
    // MM9 (Chedian, MAW's fourth continent): the done keys (QBit 90000 + key) of the MM9 promotion quests closest to
    // the kind's line; any one.
    std::vector<uint32_t> mm9;
    // MAW's own kinds: the first-tier bits of the line they borrow, which promote step 0 to step 1.
    std::vector<uint32_t> mid;
};

struct MawPromotionData
{
    std::map<uint32_t, MawPromotionKind> kinds;

    bool loadFromYaml(const std::string &text, std::string &errorMessage);
};

// How many worlds have completed the kind's promotion (0-4): any MM6 bit, any MM7 bit, MM8's bit or its alternative,
// any MM9 bit.
int mawPromotionWorlds(
    const MawPromotionKind &kind,
    const std::function<bool(uint32_t)> &hasQuestBit,
    const std::function<bool(uint32_t)> &hasAward);
}
