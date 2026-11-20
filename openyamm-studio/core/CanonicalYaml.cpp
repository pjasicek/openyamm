#include "core/CanonicalYaml.h"

#include "core/Json.h"

#include <algorithm>
#include <charconv>

namespace OpenYAMM::Studio
{
namespace
{
class Writer
{
public:
    explicit Writer(const SchemaSet *pSchemas)
        : m_pSchemas(pSchemas)
    {
    }

    std::string write(const YAML::Node &document, const YAML::Node &schema, const std::string &fileName)
    {
        if (document.IsMap() && document.size() > 0)
        {
            blockMap(document, schema, fileName, 0);
        }
        else if (document.IsSequence() && document.size() > 0 && !isFlowSequence(document))
        {
            blockSequence(document, schema, fileName, 0);
        }
        else
        {
            m_text += inlineText(document, schema, fileName);
            m_text.push_back('\n');
        }

        return std::move(m_text);
    }

private:
    YAML::Node resolved(const YAML::Node &schema, std::string &fileName) const
    {
        if (m_pSchemas == nullptr || !schema.IsDefined())
        {
            return YAML::Node(YAML::NodeType::Undefined);
        }

        return m_pSchemas->resolve(schema, fileName);
    }

    static YAML::Node child(const YAML::Node &schema, const char *pKey)
    {
        if (schema.IsDefined() && schema.IsMap())
        {
            return schema[pKey];
        }

        return YAML::Node(YAML::NodeType::Undefined);
    }

    static bool isFlowSequence(const YAML::Node &sequence)
    {
        for (const YAML::Node &item : sequence)
        {
            if (item.IsMap() || item.IsSequence() || isBlockText(item))
            {
                return false;
            }
        }

        return true;
    }

    static bool wantsString(const YAML::Node &schema)
    {
        const YAML::Node type = child(schema, "type");
        return type.IsDefined() && type.IsScalar() && type.Scalar() == "string";
    }

    static bool isPlainSafe(const std::string &text)
    {
        if (text.empty() || text.front() == ' ' || text.back() == ' ' || text.back() == ':')
        {
            return false;
        }

        const char first = text.front();
        const bool firstIsSafe =
            (first >= 'A' && first <= 'Z') || (first >= 'a' && first <= 'z') || (first >= '0' && first <= '9')
            || first == '_' || first == '/' || first == '.';

        if (!firstIsSafe)
        {
            return false;
        }

        for (size_t index = 0; index < text.size(); ++index)
        {
            const char character = text[index];
            const bool isSafe =
                (character >= 'A' && character <= 'Z') || (character >= 'a' && character <= 'z')
                || (character >= '0' && character <= '9') || character == '_' || character == ' '
                || character == '.' || character == '/' || character == '-' || character == '(' || character == ')'
                || character == '\'' || character == ':' || character == '+' || character == '%'
                || static_cast<unsigned char>(character) >= 0x80;

            if (!isSafe)
            {
                return false;
            }

            if (character == ':' && index + 1 < text.size() && text[index + 1] == ' ')
            {
                return false;
            }
        }

        // A plain scalar that would read back as something other than a string must be quoted.
        const YAML::Node probe(text);
        return classifyScalar(probe) == ScalarKind::String;
    }

    static std::string stringText(const std::string &text)
    {
        return isPlainSafe(text) ? text : jsonQuote(text);
    }

    static std::string scalarText(const YAML::Node &value, const YAML::Node &schema)
    {
        const ScalarKind kind = classifyScalar(value);

        if (kind == ScalarKind::Null && !(wantsString(schema) && value.IsScalar()))
        {
            return "null";
        }

        if (wantsString(schema) || kind == ScalarKind::String)
        {
            return stringText(value.Scalar());
        }

        if (kind == ScalarKind::Boolean)
        {
            return value.Scalar();
        }

        const std::string &text = value.Scalar();
        double parsed = 0.0;
        const char *pBegin = text.data() + (text[0] == '+' ? 1 : 0);
        std::from_chars(pBegin, text.data() + text.size(), parsed);
        return formatNumber(parsed);
    }

    struct Entry
    {
        std::string key;
        YAML::Node value;
        YAML::Node schema;
    };

    std::vector<Entry> orderedEntries(const YAML::Node &map, const YAML::Node &schema) const
    {
        const YAML::Node properties = child(schema, "properties");
        const YAML::Node additional = child(schema, "additionalProperties");
        std::vector<Entry> entries;
        std::vector<std::string> known;

        if (properties.IsDefined() && properties.IsMap())
        {
            for (YAML::const_iterator iterator = properties.begin(); iterator != properties.end(); ++iterator)
            {
                const std::string key = iterator->first.Scalar();
                known.push_back(key);

                if (map[key])
                {
                    entries.push_back({key, map[key], iterator->second});
                }
            }
        }

        std::vector<Entry> others;

        for (YAML::const_iterator iterator = map.begin(); iterator != map.end(); ++iterator)
        {
            const std::string key = iterator->first.Scalar();

            if (std::find(known.begin(), known.end(), key) == known.end())
            {
                others.push_back({
                    key,
                    iterator->second,
                    additional.IsDefined() && additional.IsMap() ? additional : YAML::Node(YAML::NodeType::Undefined)});
            }
        }

        // With a schema, keys it does not name are ordered by name; without one the document's order is kept.
        // Positions are sorted, never the nodes: assigning one yaml-cpp node to another rewrites the tree it aliases.
        std::vector<size_t> order(others.size());

        for (size_t index = 0; index < order.size(); ++index)
        {
            order[index] = index;
        }

        if (schema.IsDefined())
        {
            std::stable_sort(
                order.begin(),
                order.end(),
                [&others](size_t left, size_t right)
                {
                    return others[left].key < others[right].key;
                });
        }

        for (const size_t index : order)
        {
            entries.push_back(others[index]);
        }

        return entries;
    }

    std::vector<YAML::Node> orderedItems(const YAML::Node &sequence, const YAML::Node &schema) const
    {
        std::vector<YAML::Node> items;
        std::vector<std::string> keys;
        const YAML::Node sortKey = child(schema, "x-sort");
        const bool sorted = sortKey.IsDefined() && sortKey.IsScalar();

        for (const YAML::Node &item : sequence)
        {
            items.push_back(item);
            const YAML::Node key =
                sorted && item.IsMap() ? item[sortKey.Scalar()] : YAML::Node(YAML::NodeType::Undefined);
            keys.push_back(key.IsDefined() && key.IsScalar() ? key.Scalar() : std::string());
        }

        if (!sorted)
        {
            return items;
        }

        // Positions are sorted, never the nodes (see orderedEntries).
        std::vector<size_t> order(items.size());

        for (size_t index = 0; index < order.size(); ++index)
        {
            order[index] = index;
        }

        std::stable_sort(
            order.begin(),
            order.end(),
            [&keys](size_t left, size_t right)
            {
                return keys[left] < keys[right];
            });
        std::vector<YAML::Node> ordered;

        for (const size_t index : order)
        {
            ordered.push_back(items[index]);
        }

        return ordered;
    }

    // A value written on one line: a scalar, an empty container, a list of scalars or a flow map.
    std::string inlineText(const YAML::Node &value, const YAML::Node &unresolvedSchema, std::string fileName) const
    {
        const YAML::Node schema = resolved(unresolvedSchema, fileName);

        if (value.IsMap())
        {
            std::string text = "{";
            bool first = true;

            for (const Entry &entry : orderedEntries(value, schema))
            {
                text += first ? "" : ", ";
                text += stringText(entry.key) + ": " + inlineText(entry.value, entry.schema, fileName);
                first = false;
            }

            return text + "}";
        }

        if (value.IsSequence())
        {
            std::string text = "[";
            bool first = true;
            const YAML::Node items = child(schema, "items");

            for (const YAML::Node &item : orderedItems(value, schema))
            {
                text += first ? "" : ", ";
                text += inlineText(item, items, fileName);
                first = false;
            }

            return text + "]";
        }

        if (!value.IsDefined())
        {
            return "null";
        }

        return scalarText(value, schema);
    }

    // A list of points: every item a list of two or three scalars.
    static bool isPointList(const YAML::Node &value)
    {
        for (const YAML::Node &item : value)
        {
            if (!item.IsSequence() || item.size() < 2 || item.size() > 3)
            {
                return false;
            }

            for (const YAML::Node &coordinate : item)
            {
                if (!coordinate.IsScalar())
                {
                    return false;
                }
            }
        }

        return value.size() > 0;
    }

    bool isInline(const YAML::Node &value, const YAML::Node &schema) const
    {
        if (value.IsMap())
        {
            const YAML::Node flow = child(schema, "x-flow");
            return value.size() == 0 || (flow.IsDefined() && flow.IsScalar() && flow.Scalar() == "true");
        }

        if (value.IsSequence())
        {
            // A list of points stays on one line, marked "x-flow" or not: a polygon reads as one thing, and moving
            // it is one changed line.
            const YAML::Node flow = child(schema, "x-flow");
            return value.size() == 0 || isFlowSequence(value) || isPointList(value)
                || (flow.IsDefined() && flow.IsScalar() && flow.Scalar() == "true");
        }

        return true;
    }

    // A text of several lines is written as a literal block (`|-`, or `|` when it ends with a line break), so it
    // stays readable; texts a block cannot carry exactly (trailing spaces, tabs, a first line starting with a
    // space, more than one closing line break) stay quoted.
    static bool isBlockText(const YAML::Node &value)
    {
        if (!value.IsScalar() || classifyScalar(value) != ScalarKind::String)
        {
            return false;
        }

        const std::string &text = value.Scalar();

        if (text.find('\n') == std::string::npos || text.front() == ' ' || text.front() == '\n'
            || text.find('\t') != std::string::npos || text.find('\r') != std::string::npos
            || text.find(" \n") != std::string::npos || text.back() == ' '
            || (text.size() >= 2 && text[text.size() - 1] == '\n' && text[text.size() - 2] == '\n'))
        {
            return false;
        }

        return true;
    }

    void blockText(const std::string &text, size_t depth)
    {
        const bool endsWithBreak = text.back() == '\n';
        m_text += endsWithBreak ? "|\n" : "|-\n";
        size_t begin = 0;
        const size_t end = endsWithBreak ? text.size() - 1 : text.size();

        while (begin <= end)
        {
            size_t lineEnd = text.find('\n', begin);

            if (lineEnd == std::string::npos || lineEnd > end)
            {
                lineEnd = end;
            }

            if (lineEnd > begin)
            {
                indent(depth);
                m_text.append(text, begin, lineEnd - begin);
            }

            m_text.push_back('\n');
            begin = lineEnd + 1;
        }
    }

    void indent(size_t depth)
    {
        m_text.append(depth * 2, ' ');
    }

    // Writes "key: value" lines of a map at `depth`. When `firstInline` is set the first key continues the current
    // line (after a list item's "- ").
    void blockMap(
        const YAML::Node &map,
        const YAML::Node &unresolvedSchema,
        std::string fileName,
        size_t depth,
        bool firstInline = false)
    {
        const YAML::Node schema = resolved(unresolvedSchema, fileName);
        bool first = true;

        for (const Entry &entry : orderedEntries(map, schema))
        {
            if (!(first && firstInline))
            {
                indent(depth);
            }

            first = false;
            m_text += stringText(entry.key);
            m_text.push_back(':');
            std::string childFile = fileName;
            const YAML::Node childSchema = resolved(entry.schema, childFile);

            if (isBlockText(entry.value))
            {
                m_text.push_back(' ');
                blockText(entry.value.Scalar(), depth + 1);
            }
            else if (isInline(entry.value, childSchema))
            {
                m_text.push_back(' ');
                m_text += inlineText(entry.value, childSchema, childFile);
                m_text.push_back('\n');
            }
            else if (entry.value.IsMap())
            {
                m_text.push_back('\n');
                blockMap(entry.value, childSchema, childFile, depth + 1);
            }
            else
            {
                m_text.push_back('\n');
                blockSequence(entry.value, childSchema, childFile, depth + 1);
            }
        }
    }

    void blockSequence(
        const YAML::Node &sequence, const YAML::Node &unresolvedSchema, std::string fileName, size_t depth)
    {
        const YAML::Node schema = resolved(unresolvedSchema, fileName);
        const YAML::Node items = child(schema, "items");

        for (const YAML::Node &item : orderedItems(sequence, schema))
        {
            std::string itemFile = fileName;
            const YAML::Node itemSchema = resolved(items, itemFile);
            indent(depth);
            m_text += "- ";

            if (isBlockText(item))
            {
                blockText(item.Scalar(), depth + 1);
            }
            else if (isInline(item, itemSchema))
            {
                m_text += inlineText(item, itemSchema, itemFile);
                m_text.push_back('\n');
            }
            else if (item.IsMap())
            {
                blockMap(item, itemSchema, itemFile, depth + 1, true);
            }
            else
            {
                // A list inside a list: its items go on their own lines, one level in.
                m_text.erase(m_text.size() - 1);
                m_text.push_back('\n');
                blockSequence(item, itemSchema, itemFile, depth + 1);
            }
        }
    }

    const SchemaSet *m_pSchemas = nullptr;
    std::string m_text;
};
}

std::string writeCanonicalYaml(const YAML::Node &document, const SchemaSet &schemas, const std::string &schemaFile)
{
    Writer writer(&schemas);
    return writer.write(document, schemas.root(schemaFile), schemaFile);
}

std::string writeCanonicalYaml(const YAML::Node &document)
{
    Writer writer(nullptr);
    return writer.write(document, YAML::Node(YAML::NodeType::Undefined), "");
}

bool sameYaml(const YAML::Node &left, const YAML::Node &right, std::string &where)
{
    if (left.IsMap() || right.IsMap())
    {
        if (!left.IsMap() || !right.IsMap() || left.size() != right.size())
        {
            return false;
        }

        for (YAML::const_iterator iterator = left.begin(); iterator != left.end(); ++iterator)
        {
            const std::string key = iterator->first.Scalar();
            const YAML::Node other = right[key];
            const std::string here = where;
            where += (where.empty() ? "" : ".") + key;

            if (!other.IsDefined() || !sameYaml(iterator->second, other, where))
            {
                return false;
            }

            where = here;
        }

        return true;
    }

    if (left.IsSequence() || right.IsSequence())
    {
        if (!left.IsSequence() || !right.IsSequence() || left.size() != right.size())
        {
            return false;
        }

        for (size_t index = 0; index < left.size(); ++index)
        {
            const std::string here = where;
            where += "[" + std::to_string(index) + "]";

            if (!sameYaml(left[index], right[index], where))
            {
                return false;
            }

            where = here;
        }

        return true;
    }

    const ScalarKind leftKind = classifyScalar(left);
    const ScalarKind rightKind = classifyScalar(right);
    const bool leftNumber = leftKind == ScalarKind::Integer || leftKind == ScalarKind::Number;
    const bool rightNumber = rightKind == ScalarKind::Integer || rightKind == ScalarKind::Number;

    if (leftNumber && rightNumber)
    {
        double leftValue = 0.0;
        double rightValue = 0.0;
        const std::string &leftText = left.Scalar();
        const std::string &rightText = right.Scalar();
        std::from_chars(leftText.data() + (leftText[0] == '+' ? 1 : 0), leftText.data() + leftText.size(), leftValue);
        std::from_chars(
            rightText.data() + (rightText[0] == '+' ? 1 : 0), rightText.data() + rightText.size(), rightValue);
        return leftValue == rightValue;
    }

    if (leftKind != rightKind)
    {
        return false;
    }

    return leftKind == ScalarKind::Null || left.Scalar() == right.Scalar();
}
}
