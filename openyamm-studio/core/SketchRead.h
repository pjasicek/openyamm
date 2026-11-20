#pragma once

#include <yaml-cpp/yaml.h>

#include <cstddef>
#include <map>
#include <string>
#include <vector>

namespace OpenYAMM::Studio
{
// How the outdoor lowering reads the words of a project's files (S5_BROWSER_EDITOR.md 3.8, "What the lowering
// reads, recorded"): one `childOf` and one `textOf` for every outdoor source file, in place of their own copies, so
// that a checking mode can record which words of the sketch the lowering read. A direct walk over a map's keys (a
// part's textures, an event's steps) notes each value it visits with `noteRead`.

// The value of `key` in a map, or an undefined node (never a zombie: every accessor of the result is safe).
YAML::Node childOf(const YAML::Node &node, const std::string &key);
YAML::Node childOf(const YAML::Node &node, const char *pKey);
// The scalar text of `key` in a map, or `fallback`.
std::string textOf(const YAML::Node &node, const std::string &key, const std::string &fallback = {});
std::string textOf(const YAML::Node &node, const char *pKey, const std::string &fallback = {});
// A value read without childOf (a walk over a map's entries).
void noteRead(const YAML::Node &value);

// One word written on one object of the sketch, and whether the lowering read it.
struct SketchWord
{
    // The object's path (`structures[3].parts[1]`) and its place in the schema (`structures[].parts[]`).
    std::string object;
    std::string place;
    // The object's own kind-like words, as written (empty when not): `kind`, `shape`, `form`.
    std::map<std::string, std::string> kinds;
    std::string word;
    bool read = false;
};

// Records, while it lives, which values of one document the reads above return (S5b2's checking mode). The values
// are known by their node (yaml-cpp's identity), looked up by their place in the parsed text: a document made in
// memory (an edited tree) has no places and records nothing. One record at a time; reads outside its life and
// while paused (`SketchReadPause`) are not recorded.
class SketchReadRecord
{
public:
    explicit SketchReadRecord(const YAML::Node &document);
    ~SketchReadRecord();
    SketchReadRecord(const SketchReadRecord &) = delete;
    SketchReadRecord &operator=(const SketchReadRecord &) = delete;

    // Every word of every object of the document, in document order.
    const std::vector<SketchWord> &words() const;
    // How many values had no place in the text (a document made in memory: nothing can be recorded).
    size_t unplaced() const;

    void hit(const YAML::Node &value);

private:
    void walk(const YAML::Node &node, const std::string &path, const std::string &place);

    std::vector<SketchWord> m_words;
    // By the value's offset in the text: the values there and the word each is.
    std::map<long, std::vector<std::pair<YAML::Node, size_t>>> m_byPlace;
    size_t m_unplaced = 0;
    SketchReadRecord *m_pPrevious = nullptr;
};

// Reads made while one lives are not recorded (the sketch's checks, which read words to check them, not to build).
class SketchReadPause
{
public:
    SketchReadPause();
    ~SketchReadPause();
    SketchReadPause(const SketchReadPause &) = delete;
    SketchReadPause &operator=(const SketchReadPause &) = delete;

private:
    SketchReadRecord *m_pPaused = nullptr;
};
}
