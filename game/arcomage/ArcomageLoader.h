#pragma once

#include "game/arcomage/ArcomageTypes.h"

#include <vector>

namespace OpenYAMM::Game
{
class ArcomageLoader
{
public:
    bool load(
        const std::vector<std::vector<std::string>> &ruleRows,
        const std::vector<std::vector<std::string>> &cardRows
    );

    const ArcomageLibrary &library() const;

private:
    bool loadRules(const std::vector<std::vector<std::string>> &rows);
    bool loadCards(const std::vector<std::vector<std::string>> &rows);

    ArcomageLibrary m_library;
};
}
