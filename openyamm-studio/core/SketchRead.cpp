#include "core/SketchRead.h"

namespace OpenYAMM::Studio
{
namespace
{
// The record in force (the core is single-threaded: one lowering at a time).
SketchReadRecord *g_pRecord = nullptr;

const char *const KindWords[] = {"kind", "shape", "form"};
}

YAML::Node childOf(const YAML::Node &node, const std::string &key)
{
    return childOf(node, key.c_str());
}

YAML::Node childOf(const YAML::Node &node, const char *pKey)
{
    if (node.IsDefined() && node.IsMap())
    {
        const YAML::Node value = node[pKey];

        if (value.IsDefined())
        {
            if (g_pRecord != nullptr)
            {
                g_pRecord->hit(value);
            }

            return value;
        }
    }

    return YAML::Node(YAML::NodeType::Undefined);
}

std::string textOf(const YAML::Node &node, const std::string &key, const std::string &fallback)
{
    return textOf(node, key.c_str(), fallback);
}

std::string textOf(const YAML::Node &node, const char *pKey, const std::string &fallback)
{
    const YAML::Node value = childOf(node, pKey);
    return value.IsDefined() && value.IsScalar() ? value.Scalar() : fallback;
}

void noteRead(const YAML::Node &value)
{
    if (g_pRecord != nullptr && value.IsDefined())
    {
        g_pRecord->hit(value);
    }
}

SketchReadRecord::SketchReadRecord(const YAML::Node &document)
{
    walk(document, "", "");
    m_pPrevious = g_pRecord;
    g_pRecord = this;
}

SketchReadRecord::~SketchReadRecord()
{
    g_pRecord = m_pPrevious;
}

const std::vector<SketchWord> &SketchReadRecord::words() const
{
    return m_words;
}

size_t SketchReadRecord::unplaced() const
{
    return m_unplaced;
}

void SketchReadRecord::hit(const YAML::Node &value)
{
    const YAML::Mark mark = value.Mark();

    if (mark.is_null())
    {
        return;
    }

    const auto found = m_byPlace.find(mark.pos);

    if (found == m_byPlace.end())
    {
        return;
    }

    for (const std::pair<YAML::Node, size_t> &entry : found->second)
    {
        if (entry.first.is(value))
        {
            m_words[entry.second].read = true;
        }
    }
}

void SketchReadRecord::walk(const YAML::Node &node, const std::string &path, const std::string &place)
{
    if (node.IsSequence())
    {
        for (size_t index = 0; index < node.size(); ++index)
        {
            walk(node[index], path + "[" + std::to_string(index) + "]", place + "[]");
        }

        return;
    }

    if (!node.IsMap())
    {
        return;
    }

    std::map<std::string, std::string> kinds;

    for (const char *pKind : KindWords)
    {
        const YAML::Node value = node[pKind];

        if (value.IsDefined() && value.IsScalar())
        {
            kinds[pKind] = value.Scalar();
        }
    }

    for (YAML::const_iterator entry = node.begin(); entry != node.end(); ++entry)
    {
        const std::string key = entry->first.IsScalar() ? entry->first.Scalar() : std::string();
        // A copy of the handle: `entry->second` lives in a temporary the loop would outlive.
        const YAML::Node value = entry->second;
        SketchWord word;
        word.object = path;
        word.place = place;
        word.kinds = kinds;
        word.word = key;
        const YAML::Mark mark = value.Mark();

        if (mark.is_null())
        {
            ++m_unplaced;
        }
        else
        {
            m_byPlace[mark.pos].push_back({value, m_words.size()});
        }

        m_words.push_back(word);
        walk(value, path.empty() ? key : path + "." + key, place.empty() ? key : place + "." + key);
    }
}

SketchReadPause::SketchReadPause()
    : m_pPaused(g_pRecord)
{
    g_pRecord = nullptr;
}

SketchReadPause::~SketchReadPause()
{
    g_pRecord = m_pPaused;
}
}
