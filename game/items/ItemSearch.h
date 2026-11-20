#pragma once

#include <string>
#include <string_view>
#include <vector>

namespace OpenYAMM::Game
{
// The inventory's item search, in the manner of Path of Exile's stash search: the words of the query must all appear
// in the item's text (its name, type, enchantments and the rules' popup lines), in any order and case. A word may name
// alternatives with | ("endurance|luck"), ! in front of a word asks for items without it, and quotes keep a phrase with
// spaces together ("of the gods").
namespace ItemSearch
{
struct Term
{
    std::vector<std::string> alternatives;
    bool negated = false;
};

struct Query
{
    std::vector<Term> terms;

    bool empty() const
    {
        return terms.empty();
    }
};

Query parse(std::string_view text);
// Whether the item text (in lower case, as itemText gives it) satisfies every term of the query.
bool matches(const Query &query, std::string_view lowerItemText);
std::string toLower(std::string_view text);
}
}
