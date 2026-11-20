#include "core/Schema.h"

#include "core/Json.h"

#include <charconv>
#include <regex>
#include <stdexcept>

namespace OpenYAMM::Studio
{
namespace
{
const std::string EmptyText;

double scalarNumber(const YAML::Node &node)
{
    const std::string &text = node.Scalar();
    double parsed = 0.0;
    const char *pBegin = text.data() + ((!text.empty() && text[0] == '+') ? 1 : 0);
    std::from_chars(pBegin, text.data() + text.size(), parsed);
    return parsed;
}

std::string typeNameOf(const YAML::Node &value)
{
    if (value.IsMap())
    {
        return "object";
    }

    if (value.IsSequence())
    {
        return "array";
    }

    switch (classifyScalar(value))
    {
    case ScalarKind::Null:
        return "null";

    case ScalarKind::Boolean:
        return "boolean";

    case ScalarKind::Integer:
        return "integer";

    case ScalarKind::Number:
        return "number";

    case ScalarKind::String:
        break;
    }

    return "string";
}

bool typeMatches(const std::string &actual, const std::string &wanted)
{
    return actual == wanted || (wanted == "number" && actual == "integer");
}

bool scalarEquals(const YAML::Node &value, const YAML::Node &expected)
{
    if (!value.IsScalar() && !value.IsNull())
    {
        return false;
    }

    const ScalarKind valueKind = classifyScalar(value);
    const ScalarKind expectedKind = classifyScalar(expected);
    const bool valueIsNumber = valueKind == ScalarKind::Integer || valueKind == ScalarKind::Number;
    const bool expectedIsNumber = expectedKind == ScalarKind::Integer || expectedKind == ScalarKind::Number;

    if (valueIsNumber && expectedIsNumber)
    {
        return scalarNumber(value) == scalarNumber(expected);
    }

    return valueKind == expectedKind && value.Scalar() == expected.Scalar();
}

std::string joinPath(const std::string &path, const std::string &key)
{
    return path.empty() ? key : path + "." + key;
}
}

const SchemaSet &SchemaSet::builtIn()
{
    static const SchemaSet instance = []()
    {
        SchemaSet schemas;

        for (size_t index = 0; index < EmbeddedSchemaCount; ++index)
        {
            std::string errorMessage;

            if (!schemas.add(EmbeddedSchemas[index].pFileName, EmbeddedSchemas[index].pText, errorMessage))
            {
                throw std::runtime_error(errorMessage);
            }
        }

        return schemas;
    }();

    return instance;
}

bool SchemaSet::add(const std::string &fileName, const std::string &jsonText, std::string &errorMessage)
{
    try
    {
        m_roots[fileName] = YAML::Load(jsonText);
        m_texts[fileName] = jsonText;
    }
    catch (const YAML::Exception &exception)
    {
        errorMessage = fileName + ": " + exception.what();
        return false;
    }

    return true;
}

bool SchemaSet::has(const std::string &fileName) const
{
    return m_roots.contains(fileName);
}

YAML::Node SchemaSet::root(const std::string &fileName) const
{
    const std::map<std::string, YAML::Node>::const_iterator iterator = m_roots.find(fileName);
    return iterator == m_roots.end() ? YAML::Node(YAML::NodeType::Undefined) : iterator->second;
}

std::vector<std::string> SchemaSet::fileNames() const
{
    std::vector<std::string> names;

    for (const std::pair<const std::string, YAML::Node> &entry : m_roots)
    {
        names.push_back(entry.first);
    }

    return names;
}

const std::string &SchemaSet::text(const std::string &fileName) const
{
    const std::map<std::string, std::string>::const_iterator iterator = m_texts.find(fileName);
    return iterator == m_texts.end() ? EmptyText : iterator->second;
}

YAML::Node SchemaSet::resolve(const YAML::Node &schema, std::string &fileName) const
{
    YAML::Node current = schema;

    for (int depth = 0; depth < 16 && current.IsMap() && current["$ref"]; ++depth)
    {
        const std::string reference = current["$ref"].Scalar();
        const size_t hash = reference.find('#');
        const std::string file = reference.substr(0, hash);
        const std::string pointer = hash == std::string::npos ? "" : reference.substr(hash + 1);

        if (!file.empty())
        {
            fileName = file;
        }

        YAML::Node target = root(fileName);
        size_t position = 0;

        while (position < pointer.size() && target.IsDefined())
        {
            if (pointer[position] == '/')
            {
                ++position;
                continue;
            }

            const size_t next = pointer.find('/', position);
            const std::string part = pointer.substr(position, next == std::string::npos ? next : next - position);
            // Reset rather than assign: assigning to a yaml-cpp node rewrites the tree it aliases.
            const YAML::Node &constTarget = target;
            target.reset(constTarget.IsMap() ? constTarget[part] : YAML::Node(YAML::NodeType::Undefined));
            position = next == std::string::npos ? pointer.size() : next;
        }

        if (!target.IsDefined())
        {
            return YAML::Node(YAML::NodeType::Undefined);
        }

        current.reset(target);
    }

    return current;
}

std::vector<SchemaIssue> SchemaSet::validate(const YAML::Node &document, const std::string &fileName) const
{
    std::vector<SchemaIssue> issues;
    const YAML::Node schema = root(fileName);

    if (!schema.IsDefined())
    {
        issues.push_back({"", "no schema named " + fileName});
        return issues;
    }

    validateNode(document, schema, fileName, "", issues);
    return issues;
}

std::vector<SchemaIssue> SchemaSet::validateAt(const YAML::Node &document, const std::string &reference) const
{
    std::vector<SchemaIssue> issues;
    YAML::Node schema(YAML::NodeType::Map);
    schema["$ref"] = reference;
    validateNode(document, schema, std::string(), "", issues);
    return issues;
}

void SchemaSet::validateNode(
    const YAML::Node &value,
    const YAML::Node &unresolvedSchema,
    std::string fileName,
    const std::string &path,
    std::vector<SchemaIssue> &issues) const
{
    const YAML::Node schema = resolve(unresolvedSchema, fileName);

    if (!schema.IsDefined())
    {
        issues.push_back({path, "the schema has a reference that does not resolve"});
        return;
    }

    if (!schema.IsMap())
    {
        return;
    }

    const std::string actualType = typeNameOf(value);

    if (const YAML::Node type = schema["type"])
    {
        bool matched = false;
        std::string wantedText;

        if (type.IsSequence())
        {
            for (const YAML::Node &option : type)
            {
                matched = matched || typeMatches(actualType, option.Scalar());
                wantedText += (wantedText.empty() ? "" : " or ") + option.Scalar();
            }
        }
        else
        {
            matched = typeMatches(actualType, type.Scalar());
            wantedText = type.Scalar();
        }

        if (!matched)
        {
            issues.push_back({path, "expected " + wantedText + ", found " + actualType});
            return;
        }
    }

    if (const YAML::Node options = schema["enum"])
    {
        bool matched = false;
        std::string allowed;

        for (const YAML::Node &option : options)
        {
            matched = matched || scalarEquals(value, option);
            allowed += (allowed.empty() ? "" : ", ") + option.Scalar();
        }

        if (!matched)
        {
            issues.push_back({path, "must be one of: " + allowed});
        }
    }

    if (const YAML::Node constant = schema["const"])
    {
        if (!scalarEquals(value, constant))
        {
            issues.push_back({path, "must be " + constant.Scalar()});
        }
    }

    for (const char *pKeyword : {"oneOf", "anyOf"})
    {
        const YAML::Node alternatives = schema[pKeyword];

        if (!alternatives)
        {
            continue;
        }

        size_t matches = 0;
        std::vector<SchemaIssue> closest;

        for (const YAML::Node &alternative : alternatives)
        {
            std::vector<SchemaIssue> attempt;
            validateNode(value, alternative, fileName, path, attempt);

            if (attempt.empty())
            {
                ++matches;
            }
            else if (closest.empty() || attempt.size() < closest.size())
            {
                closest = attempt;
            }
        }

        if (matches == 0)
        {
            issues.push_back({path, std::string("matches none of the allowed forms (") + pKeyword + ")"});
            issues.insert(issues.end(), closest.begin(), closest.end());
        }
        else if (matches > 1 && std::string(pKeyword) == "oneOf")
        {
            issues.push_back({path, "matches more than one of the allowed forms (oneOf)"});
        }
    }

    if (value.IsMap())
    {
        const YAML::Node properties = schema["properties"];

        if (const YAML::Node required = schema["required"])
        {
            for (const YAML::Node &name : required)
            {
                if (!value[name.Scalar()])
                {
                    issues.push_back({path, "missing required key '" + name.Scalar() + "'"});
                }
            }
        }

        const YAML::Node additional = schema["additionalProperties"];

        for (YAML::const_iterator iterator = value.begin(); iterator != value.end(); ++iterator)
        {
            const std::string key = iterator->first.Scalar();
            const std::string childPath = joinPath(path, key);

            if (properties && properties[key])
            {
                validateNode(iterator->second, properties[key], fileName, childPath, issues);
            }
            else if (additional && additional.IsMap())
            {
                validateNode(iterator->second, additional, fileName, childPath, issues);
            }
            else if (additional && additional.IsScalar() && additional.Scalar() == "false")
            {
                issues.push_back({childPath, "unknown key"});
            }
        }

        return;
    }

    if (value.IsSequence())
    {
        if (const YAML::Node minimum = schema["minItems"])
        {
            if (value.size() < minimum.as<size_t>())
            {
                issues.push_back({path, "needs at least " + minimum.Scalar() + " items"});
            }
        }

        if (const YAML::Node maximum = schema["maxItems"])
        {
            if (value.size() > maximum.as<size_t>())
            {
                issues.push_back({path, "allows at most " + maximum.Scalar() + " items"});
            }
        }

        if (const YAML::Node items = schema["items"])
        {
            size_t index = 0;

            for (const YAML::Node &item : value)
            {
                validateNode(item, items, fileName, path + "[" + std::to_string(index) + "]", issues);
                ++index;
            }
        }

        return;
    }

    if (actualType == "integer" || actualType == "number")
    {
        const double number = scalarNumber(value);

        if (const YAML::Node minimum = schema["minimum"])
        {
            if (number < scalarNumber(minimum))
            {
                issues.push_back({path, "must be at least " + minimum.Scalar()});
            }
        }

        if (const YAML::Node maximum = schema["maximum"])
        {
            if (number > scalarNumber(maximum))
            {
                issues.push_back({path, "must be at most " + maximum.Scalar()});
            }
        }

        if (const YAML::Node minimum = schema["exclusiveMinimum"])
        {
            if (number <= scalarNumber(minimum))
            {
                issues.push_back({path, "must be greater than " + minimum.Scalar()});
            }
        }

        return;
    }

    if (actualType == "string")
    {
        if (const YAML::Node minimum = schema["minLength"])
        {
            if (value.Scalar().size() < minimum.as<size_t>())
            {
                issues.push_back({path, "must not be empty"});
            }
        }

        if (const YAML::Node pattern = schema["pattern"])
        {
            if (!std::regex_search(value.Scalar(), std::regex(pattern.Scalar(), std::regex::ECMAScript)))
            {
                issues.push_back({path, "'" + value.Scalar() + "' does not match " + pattern.Scalar()});
            }
        }
    }
}
}
