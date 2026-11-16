#pragma once

#include "core/Schema.h"

#include <yaml-cpp/yaml.h>

#include <string>

namespace OpenYAMM::Studio
{
// The one form every project file is written in (PLAN.md section 4, "Canonical form"), so that a diff shows a change
// and nothing else:
//   - keys in the order of the schema's "properties", unknown keys after them in alphabetical order;
//   - two-space indentation, block maps and lists; a list of scalars and a map marked "x-flow" on one line;
//   - lists whose schema names an "x-sort" key ordered by that key;
//   - numbers in their shortest exact form, strings plain where that is unambiguous and double-quoted otherwise;
//   - no comments (yaml-cpp cannot keep them; objects carry a `notes` field instead).
// Writing the result again gives the same bytes.
std::string writeCanonicalYaml(const YAML::Node &document, const SchemaSet &schemas, const std::string &schemaFile);

// Without a schema: keys keep their order.
std::string writeCanonicalYaml(const YAML::Node &document);

// Whether two documents say the same: the same maps (in any key order), lists in the same order, and scalars of the
// same kind and value (numbers by value, so 1.50 equals 1.5; text exactly). On a difference `where` is its path.
bool sameYaml(const YAML::Node &left, const YAML::Node &right, std::string &where);
}
