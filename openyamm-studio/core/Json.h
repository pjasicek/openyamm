#pragma once

#include <yaml-cpp/yaml.h>

#include <cstdint>
#include <string>
#include <string_view>
#include <vector>

namespace OpenYAMM::Studio
{
// Streaming JSON text writer. Every oymap command prints its result through it, so the output of one build is the
// same on every platform: keys in call order, integers as written, floats in the shortest form that reads back to
// the same value.
class JsonWriter
{
public:
    explicit JsonWriter(bool pretty = false);

    void beginObject();
    void endObject();
    void beginArray();
    void endArray();
    void key(std::string_view name);

    void value(std::string_view text);
    void value(const char *pText);
    void value(const std::string &text);
    void value(bool flag);
    void value(int64_t number);
    void value(uint64_t number);
    void value(int number);
    void value(unsigned number);
    void value(double number);
    void value(float number);
    void null();
    // A value already written as JSON text (compact): copied in as it is.
    void raw(std::string_view json);
    // Members of the open object already written as JSON text (`"a":1,"b":[2]`, compact): copied in after the
    // members written so far.
    void rawMembers(std::string_view members);

    template <typename Value>
    void field(std::string_view name, const Value &fieldValue)
    {
        key(name);
        value(fieldValue);
    }

    // A YAML tree as JSON: maps keep their order, plain scalars become numbers, booleans or null where they read as
    // such, quoted scalars stay strings.
    void node(const YAML::Node &yamlNode);

    const std::string &text() const;
    std::string take();

private:
    void beforeValue();
    void newLine();

    struct Level
    {
        bool isObject = false;
        bool hasItems = false;
        // An array of scalars is written on one line even when pretty.
        bool compact = false;
    };

    std::string m_text;
    std::vector<Level> m_levels;
    bool m_pretty = false;
    bool m_afterKey = false;
};

std::string jsonQuote(std::string_view text);
// Shortest decimal text that reads back to the same double; integral values without a fraction or exponent.
std::string formatNumber(double number);
std::string toJson(const YAML::Node &yamlNode, bool pretty = true);

enum class ScalarKind
{
    String,
    Integer,
    Number,
    Boolean,
    Null,
};

// What a YAML scalar means under the core's rules (YAML 1.2 core schema; quoted scalars are always strings).
ScalarKind classifyScalar(const YAML::Node &yamlNode);
}
