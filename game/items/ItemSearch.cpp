#include "game/items/ItemSearch.h"

#include "engine/Utf8Text.h"

#include <algorithm>
#include <cctype>

namespace OpenYAMM::Game::ItemSearch
{
namespace
{
// The query's words: split on spaces outside quotes, the quotes dropped.
std::vector<std::string> splitWords(std::string_view text)
{
    std::vector<std::string> words;
    std::string word;
    bool quoted = false;

    for (const char character : text)
    {
        if (character == '"')
        {
            quoted = !quoted;
        }
        else if (!quoted && std::isspace(static_cast<unsigned char>(character)))
        {
            if (!word.empty())
            {
                words.push_back(std::move(word));
                word.clear();
            }
        }
        else
        {
            word.push_back(character);
        }
    }

    if (!word.empty())
    {
        words.push_back(std::move(word));
    }

    return words;
}
}

std::string toLower(std::string_view text)
{
    return Engine::Utf8::lower(text);
}

Query parse(std::string_view text)
{
    Query query;

    for (std::string word : splitWords(toLower(text)))
    {
        Term term;

        if (word.front() == '!')
        {
            term.negated = true;
            word.erase(word.begin());
        }

        size_t start = 0;

        while (start <= word.size())
        {
            const size_t bar = std::min(word.find('|', start), word.size());

            if (bar > start)
            {
                term.alternatives.push_back(word.substr(start, bar - start));
            }

            start = bar + 1;
        }

        if (!term.alternatives.empty())
        {
            query.terms.push_back(std::move(term));
        }
    }

    return query;
}

bool matches(const Query &query, std::string_view lowerItemText)
{
    for (const Term &term : query.terms)
    {
        const bool found = std::any_of(term.alternatives.begin(), term.alternatives.end(),
            [lowerItemText](const std::string &alternative)
            {
                return lowerItemText.find(alternative) != std::string_view::npos;
            });

        if (found == term.negated)
        {
            return false;
        }
    }

    return true;
}
}
