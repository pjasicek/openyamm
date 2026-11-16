#pragma once

#include <yaml-cpp/yaml.h>

#include <map>
#include <string>
#include <string_view>
#include <vector>

namespace OpenYAMM::Studio
{
struct SchemaIssue
{
    // Where in the document, as "rooms[3].floor".
    std::string path;
    std::string message;
};

// The JSON Schemas of the project format (openyamm-studio/schema/*.schema.json), compiled into the binary so the
// command line, the host and the WebAssembly core validate against the same text.
//
// Supported keywords (a subset of JSON Schema 2020-12, enough for the project format): type, properties, required,
// additionalProperties, items, enum, const, minimum, maximum, exclusiveMinimum, minItems, maxItems, minLength,
// pattern, oneOf, anyOf, $ref ("#/$defs/name" or "file.schema.json#/$defs/name" or "file.schema.json").
// Extensions, ignored by other validators: "x-flow" (write this map on one line), "x-sort" (name of the key a list is
// ordered by in canonical form).
class SchemaSet
{
public:
    // The embedded schemas.
    static const SchemaSet &builtIn();

    bool add(const std::string &fileName, const std::string &jsonText, std::string &errorMessage);

    bool has(const std::string &fileName) const;
    // The root schema node of a file, or an undefined node.
    YAML::Node root(const std::string &fileName) const;
    // Follows $ref until a schema without one. `fileName` is the file the schema node came from and is updated when a
    // reference leaves it.
    YAML::Node resolve(const YAML::Node &schema, std::string &fileName) const;

    std::vector<SchemaIssue> validate(const YAML::Node &document, const std::string &fileName) const;
    // Against the schema a reference names ("edit.rpc.json#/methods/apply/params").
    std::vector<SchemaIssue> validateAt(const YAML::Node &document, const std::string &reference) const;

    std::vector<std::string> fileNames() const;
    const std::string &text(const std::string &fileName) const;

private:
    void validateNode(
        const YAML::Node &value,
        const YAML::Node &schema,
        std::string fileName,
        const std::string &path,
        std::vector<SchemaIssue> &issues) const;

    std::map<std::string, YAML::Node> m_roots;
    std::map<std::string, std::string> m_texts;
};

struct EmbeddedSchema
{
    const char *pFileName;
    const char *pText;
};

// Generated at build time from openyamm-studio/schema/.
extern const EmbeddedSchema EmbeddedSchemas[];
extern const size_t EmbeddedSchemaCount;
// The request list (openyamm-studio/schema/rpc/*.rpc.json).
extern const EmbeddedSchema EmbeddedRpcSchemas[];
extern const size_t EmbeddedRpcSchemaCount;
}
