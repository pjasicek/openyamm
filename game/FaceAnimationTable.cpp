#include "game/FaceAnimationTable.h"

#include <cctype>

namespace OpenYAMM::Game
{
namespace
{
bool isNumericString(const std::string &value)
{
    if (value.empty())
    {
        return false;
    }

    for (char character : value)
    {
        if (!std::isdigit(static_cast<unsigned char>(character)))
        {
            return false;
        }
    }

    return true;
}

std::vector<PortraitId> parsePortraitIdList(const std::string &text)
{
    std::vector<PortraitId> result;
    std::string currentToken;

    const auto flushToken =
        [&]()
        {
            if (currentToken.empty())
            {
                return;
            }

            if (isNumericString(currentToken))
            {
                result.push_back(static_cast<PortraitId>(std::stoul(currentToken)));
            }
            else if (const std::optional<PortraitId> portraitId = portraitIdFromName(currentToken))
            {
                result.push_back(*portraitId);
            }

            currentToken.clear();
        };

    for (char character : text)
    {
        if (character == ',' || character == ';' || std::isspace(static_cast<unsigned char>(character)))
        {
            flushToken();
            continue;
        }

        currentToken.push_back(character);
    }

    flushToken();
    return result;
}
}

bool FaceAnimationTable::loadFromRows(const std::vector<std::vector<std::string>> &rows)
{
    m_entries.clear();
    m_entryIndexByAnimationId.clear();

    for (const std::vector<std::string> &row : rows)
    {
        if (row.size() < 3 || row[2].empty())
        {
            continue;
        }

        std::optional<FaceAnimationId> animationId;

        if (isNumericString(row[0]))
        {
            animationId = static_cast<FaceAnimationId>(std::stoul(row[0]));
        }
        else
        {
            animationId = faceAnimationIdFromName(row[0]);
        }

        if (!animationId)
        {
            animationId = faceAnimationIdFromName(row[1]);
        }

        if (!animationId)
        {
            continue;
        }

        FaceAnimationEntry entry = {};
        entry.animationId = *animationId;
        entry.animationName = row[1];
        entry.portraitIds = parsePortraitIdList(row[2]);

        if (entry.portraitIds.empty())
        {
            continue;
        }

        m_entryIndexByAnimationId[static_cast<uint16_t>(entry.animationId)] = m_entries.size();
        m_entries.push_back(std::move(entry));
    }

    return !m_entries.empty();
}

const FaceAnimationEntry *FaceAnimationTable::find(FaceAnimationId animationId) const
{
    const auto entryIt = m_entryIndexByAnimationId.find(static_cast<uint16_t>(animationId));

    if (entryIt == m_entryIndexByAnimationId.end())
    {
        return nullptr;
    }

    return &m_entries[entryIt->second];
}
}
