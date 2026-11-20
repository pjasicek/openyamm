#include "core/Keys.h"

#include <map>
#include <set>

namespace OpenYAMM::Studio
{
namespace
{
YAML::Node childOf(const YAML::Node &node, const std::string &key)
{
    return node.IsDefined() && node.IsMap() ? node[key] : YAML::Node(YAML::NodeType::Undefined);
}

std::string scalarOf(const YAML::Node &node)
{
    return node.IsDefined() && node.IsScalar() ? node.Scalar() : std::string();
}

bool hasKeyedLists(const SchemaSet &schemas, const YAML::Node &unresolved, std::string fileName, int depth);

// Whether the schema below a place of a document (named by its path without list positions) has keyed lists:
// worked out once per place, so a write walks only the parts of a file that can hold keys.
bool mayHoldKeys(const SchemaSet &schemas, const YAML::Node &schema, const std::string &fileName,
    const std::string &place)
{
    static std::map<std::string, bool> known;
    const std::string name = fileName + "#" + place;
    const std::map<std::string, bool>::const_iterator found = known.find(name);

    if (found != known.end())
    {
        return found->second;
    }

    const bool holds = hasKeyedLists(schemas, schema, fileName, 0);
    known.emplace(name, holds);
    return holds;
}

// Fills the keys of the lists in `node` (a value of `schema`, unresolved), depth first.
void fillIn(const SchemaSet &schemas, YAML::Node node, const YAML::Node &unresolved, std::string fileName,
    const std::string &path, const std::string &place, size_t &count, std::vector<std::string> *pFilled)
{
    const YAML::Node schema = schemas.resolve(unresolved, fileName);

    if (!schema.IsDefined() || !schema.IsMap())
    {
        return;
    }

    if (node.IsMap())
    {
        for (YAML::iterator iterator = node.begin(); iterator != node.end(); ++iterator)
        {
            const std::string key = iterator->first.Scalar();
            std::string childFile = fileName;
            const YAML::Node childSchema = propertySchema(schemas, schema, key, childFile);

            if (childSchema.IsDefined() && mayHoldKeys(schemas, childSchema, childFile, place + "/" + key))
            {
                fillIn(schemas, iterator->second, childSchema, childFile, path.empty() ? key : path + "." + key,
                    place + "/" + key, count, pFilled);
            }
        }

        return;
    }

    if (!node.IsSequence())
    {
        return;
    }

    const ListKey key = listKeyOf(schema);
    std::string itemFile = fileName;
    const YAML::Node items = itemsSchema(schemas, schema, itemFile);

    if (key.keyed() && key.field != "id")
    {
        const std::vector<std::string> keys = itemKeys(node, key);

        for (size_t index = 0; index < node.size(); ++index)
        {
            YAML::Node item = node[index];

            if (item.IsMap() && !childOf(item, key.field).IsDefined())
            {
                // The key goes first, as the schema lists it (the canonical writer orders the keys anyway).
                item[key.field] = keys[index];
                ++count;

                if (pFilled != nullptr)
                {
                    pFilled->push_back(path + "[" + std::to_string(index) + "]: " + keys[index]);
                }
            }
        }
    }

    if (!items.IsDefined())
    {
        return;
    }

    if (!mayHoldKeys(schemas, items, itemFile, place + "[]"))
    {
        return;
    }

    for (size_t index = 0; index < node.size(); ++index)
    {
        fillIn(schemas, node[index], items, itemFile, path + "[" + std::to_string(index) + "]", place + "[]", count,
            pFilled);
    }
}

// `depth` ends the walk in schemas that refer to themselves (a condition's `any`).
bool hasKeyedLists(const SchemaSet &schemas, const YAML::Node &unresolved, std::string fileName, int depth)
{
    const YAML::Node schema = schemas.resolve(unresolved, fileName);

    if (!schema.IsDefined() || !schema.IsMap() || depth > 8)
    {
        return false;
    }

    const ListKey key = listKeyOf(schema);

    if (key.keyed() && key.field != "id")
    {
        return true;
    }

    for (const char *pWord : {"properties", "$defs"})
    {
        const YAML::Node children = childOf(schema, pWord);

        if (children.IsDefined() && children.IsMap())
        {
            for (YAML::const_iterator iterator = children.begin(); iterator != children.end(); ++iterator)
            {
                if (hasKeyedLists(schemas, iterator->second, fileName, depth + 1))
                {
                    return true;
                }
            }
        }
    }

    const YAML::Node items = childOf(schema, "items");
    return items.IsDefined() && hasKeyedLists(schemas, items, fileName, depth + 1);
}

void addressesIn(const SchemaSet &schemas, const YAML::Node &node, const YAML::Node &unresolved, std::string fileName,
    const std::string &address, bool writtenOnly, std::vector<std::string> &addresses)
{
    const YAML::Node schema = schemas.resolve(unresolved, fileName);

    if (!schema.IsDefined() || !schema.IsMap())
    {
        return;
    }

    if (node.IsMap())
    {
        for (YAML::const_iterator iterator = node.begin(); iterator != node.end(); ++iterator)
        {
            const std::string key = iterator->first.Scalar();
            std::string childFile = fileName;
            const YAML::Node childSchema = propertySchema(schemas, schema, key, childFile);

            if (childSchema.IsDefined())
            {
                addressesIn(schemas, iterator->second, childSchema, childFile, address + "/" + key, writtenOnly,
                    addresses);
            }
        }

        return;
    }

    if (!node.IsSequence())
    {
        return;
    }

    const ListKey key = listKeyOf(schema);
    std::string itemFile = fileName;
    const YAML::Node items = itemsSchema(schemas, schema, itemFile);

    if (!key.keyed() || !items.IsDefined())
    {
        return;
    }

    const std::vector<std::string> keys = itemKeys(node, key);

    for (size_t index = 0; index < node.size(); ++index)
    {
        // A top-level object's address is its id; a sub-object's, its owner's address and the path of keys.
        const std::string itemAddress = key.field == "id" && address.find('/', 1) == std::string::npos
            ? keys[index] : address + "/" + keys[index];

        if (!(key.field == "id" && address.find('/', 1) == std::string::npos)
            && (!writtenOnly || childOf(node[index], key.field).IsDefined()))
        {
            addresses.push_back(itemAddress);
        }

        addressesIn(schemas, node[index], items, itemFile, itemAddress, writtenOnly, addresses);
    }
}
}

ListKey listKeyOf(const YAML::Node &arraySchema)
{
    ListKey key;
    key.field = scalarOf(childOf(arraySchema, "x-key"));
    key.prefix = scalarOf(childOf(arraySchema, "x-key-prefix"));
    return key;
}

std::vector<std::string> itemKeys(const YAML::Node &list, const ListKey &key)
{
    std::vector<std::string> keys(list.size());
    std::set<std::string> taken;

    for (size_t index = 0; index < list.size(); ++index)
    {
        keys[index] = scalarOf(childOf(list[index], key.field));

        if (!keys[index].empty())
        {
            taken.insert(keys[index]);
        }
    }

    if (key.prefix.empty())
    {
        return keys;
    }

    for (size_t index = 0; index < list.size(); ++index)
    {
        if (!keys[index].empty())
        {
            continue;
        }

        size_t number = index + 1;

        while (taken.contains(key.prefix + std::to_string(number)))
        {
            ++number;
        }

        keys[index] = key.prefix + std::to_string(number);
        taken.insert(keys[index]);
    }

    return keys;
}

long findKeyed(const YAML::Node &list, const ListKey &key, const std::string &wanted)
{
    const std::vector<std::string> keys = itemKeys(list, key);

    for (size_t index = 0; index < keys.size(); ++index)
    {
        if (keys[index] == wanted)
        {
            return static_cast<long>(index);
        }
    }

    return -1;
}

YAML::Node propertySchema(const SchemaSet &schemas, const YAML::Node &mapSchema, const std::string &property,
    std::string &fileName)
{
    const YAML::Node resolved = schemas.resolve(mapSchema, fileName);
    const YAML::Node properties = childOf(resolved, "properties");
    const YAML::Node child = childOf(properties, property);

    if (!child.IsDefined())
    {
        return YAML::Node(YAML::NodeType::Undefined);
    }

    return schemas.resolve(child, fileName);
}

YAML::Node itemsSchema(const SchemaSet &schemas, const YAML::Node &arraySchema, std::string &fileName)
{
    const YAML::Node resolved = schemas.resolve(arraySchema, fileName);
    const YAML::Node items = childOf(resolved, "items");

    if (!items.IsDefined() || !items.IsMap())
    {
        return YAML::Node(YAML::NodeType::Undefined);
    }

    return schemas.resolve(items, fileName);
}

size_t fillMissingKeys(YAML::Node &document, const std::string &schemaFile, std::vector<std::string> *pFilled)
{
    const SchemaSet &schemas = SchemaSet::builtIn();
    size_t count = 0;

    if (schemas.has(schemaFile) && document.IsMap())
    {
        fillIn(schemas, document, schemas.root(schemaFile), schemaFile, "", "", count, pFilled);
    }

    return count;
}

bool fileHasKeyedLists(const std::string &schemaFile)
{
    const SchemaSet &schemas = SchemaSet::builtIn();
    return schemas.has(schemaFile) && hasKeyedLists(schemas, schemas.root(schemaFile), schemaFile, 0);
}

std::vector<std::string> subObjectAddresses(const YAML::Node &document, const std::string &schemaFile)
{
    const SchemaSet &schemas = SchemaSet::builtIn();
    std::vector<std::string> addresses;

    if (schemas.has(schemaFile))
    {
        addressesIn(schemas, document, schemas.root(schemaFile), schemaFile, "", false, addresses);
    }

    return addresses;
}

std::vector<std::string> writtenKeyAddresses(const YAML::Node &document, const std::string &schemaFile)
{
    const SchemaSet &schemas = SchemaSet::builtIn();
    std::vector<std::string> addresses;

    if (schemas.has(schemaFile))
    {
        addressesIn(schemas, document, schemas.root(schemaFile), schemaFile, "", true, addresses);
    }

    return addresses;
}
}
