#include "core/Kinds.h"

#include "core/Keys.h"
#include "core/Schema.h"

#include <map>
#include <string>

namespace OpenYAMM::Studio
{
namespace
{
YAML::Node childOf(const YAML::Node &node, const std::string &key)
{
    return node.IsDefined() && node.IsMap() ? node[key] : YAML::Node(YAML::NodeType::Undefined);
}

bool listsKind(const YAML::Node &kinds, const std::string &kind)
{
    if (!kinds.IsDefined() || !kinds.IsSequence())
    {
        return true;
    }

    for (const YAML::Node &each : kinds)
    {
        if (each.IsScalar() && (each.Scalar() == kind || each.Scalar() == "all"))
        {
            return true;
        }
    }

    return false;
}

// Whether a discriminated object can be at or below a schema (its kind words checked), walked once per place of
// a document (its path without list positions), so a check walks only the parts of a file that can hold one.
bool hasDiscriminator(const SchemaSet &schemas, const YAML::Node &unresolved, std::string fileName, int depth)
{
    const YAML::Node schema = schemas.resolve(unresolved, fileName);

    if (!schema.IsDefined() || !schema.IsMap() || depth > 8)
    {
        return false;
    }

    if (childOf(schema, "x-discriminator").IsDefined())
    {
        return true;
    }

    const YAML::Node properties = childOf(schema, "properties");

    if (properties.IsDefined() && properties.IsMap())
    {
        for (YAML::const_iterator property = properties.begin(); property != properties.end(); ++property)
        {
            if (hasDiscriminator(schemas, property->second, fileName, depth + 1))
            {
                return true;
            }
        }
    }

    const YAML::Node items = childOf(schema, "items");
    return items.IsDefined() && hasDiscriminator(schemas, items, fileName, depth + 1);
}

bool mayHoldKinds(const SchemaSet &schemas, const YAML::Node &schema, const std::string &fileName,
    const std::string &place)
{
    static std::map<std::string, bool> known;
    const std::string name = fileName + "#" + place;
    const std::map<std::string, bool>::const_iterator found = known.find(name);

    if (found != known.end())
    {
        return found->second;
    }

    const bool holds = hasDiscriminator(schemas, schema, fileName, 0);
    known.emplace(name, holds);
    return holds;
}

void checkNode(const SchemaSet &schemas, const YAML::Node &node, const YAML::Node &unresolved, std::string fileName,
    const std::string &name, const std::string &path, const std::string &place, std::vector<ProjectIssue> &issues,
    int depth)
{
    const YAML::Node schema = schemas.resolve(unresolved, fileName);

    if (!schema.IsDefined() || !schema.IsMap() || depth > 12 || !mayHoldKinds(schemas, schema, fileName, place))
    {
        return;
    }

    if (node.IsSequence())
    {
        std::string itemFile = fileName;
        const YAML::Node items = itemsSchema(schemas, schema, itemFile);

        for (size_t index = 0; items.IsDefined() && index < node.size(); ++index)
        {
            checkNode(schemas, node[index], items, itemFile, name, path + "[" + std::to_string(index) + "]",
                place + "[]", issues, depth + 1);
        }

        return;
    }

    if (!node.IsMap())
    {
        return;
    }

    const YAML::Node discriminator = childOf(schema, "x-discriminator");
    std::string kind;

    if (discriminator.IsDefined() && discriminator.IsMap())
    {
        const std::string property = childOf(discriminator, "property").IsDefined()
            ? discriminator["property"].Scalar() : std::string("kind");
        const YAML::Node written = childOf(node, property);
        kind = written.IsDefined() && written.IsScalar() ? written.Scalar()
            : childOf(discriminator, "default").IsDefined() ? discriminator["default"].Scalar() : std::string();
    }

    const YAML::Node properties = childOf(schema, "properties");

    for (YAML::const_iterator field = node.begin(); field != node.end(); ++field)
    {
        const std::string word = field->first.Scalar();
        const YAML::Node property = childOf(properties, word);

        if (!property.IsDefined())
        {
            continue;
        }

        if (!kind.empty() && !listsKind(childOf(property, "x-kinds"), kind))
        {
            issues.push_back({name, path.empty() ? word : path + "." + word, "the word `" + word
                + "` does not apply to kind " + kind + ": the build does not read it there (drop it, or change "
                "the kind)", "kind", IssueSeverity::Warning});
        }

        checkNode(schemas, field->second, property, fileName, name, path.empty() ? word : path + "." + word,
            place + "/" + word, issues, depth + 1);
    }
}
}

void checkWordKinds(const ProjectFile &file, std::vector<ProjectIssue> &issues)
{
    const SchemaSet &schemas = SchemaSet::builtIn();

    if (!schemas.has(file.schema) || !file.document.IsMap())
    {
        return;
    }

    checkNode(schemas, file.document, schemas.root(file.schema), file.schema, file.name, "", "", issues, 0);
}
}
