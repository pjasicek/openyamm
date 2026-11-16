// S5b2 (devdocs/map_studio/S5_BROWSER_EDITOR.md 6.4, 3.8, 3.18, 2.4.2, 2.4.3): the outdoor lowering's read record
// (one shared childOf/textOf, "word X was never read on this object"), the kind check on the sketch's structures, the
// land kept up to the peaks (byte-identical to a fresh lowering, keyed by the land words), the land made by hand
// (strokes as differences, smoothed areas, bounded patches, the hand-made mark), the test D15 asked for (an agent
// moves a ridge under a raised and under a smoothed patch, and the strokes stay), the view build that leaves out a
// structure it cannot build, and the sketch's keys.
#include "doctest/doctest.h"

#include "core/IndoorBuild.h"
#include "core/Keys.h"
#include "core/OutdoorBuild.h"
#include "core/OutdoorLowering.h"
#include "core/SketchRead.h"
#include "core/View.h"

#include <yaml-cpp/yaml.h>

#include <algorithm>
#include <cmath>
#include <string>
#include <vector>

using namespace OpenYAMM::Studio;

namespace
{
constexpr int Side = 128;

Project sketchProject(const std::string &sketch, const std::string &more = {})
{
    const std::vector<std::pair<std::string, std::string>> files = {
        {"project.yml", "format: 0\nid: sculpttest\nworld: mm8\nkind: outdoor\n" + more},
        {"plan.yml", "format: 0\nspaces:\n  - {id: zone:land, kind: zone}\nentrances:\n"
            "  - {id: entrance:north, kind: arrival, space: zone:land, facing: s}\n"
            "height_bands:\n  - {id: band:low, range: [576, 704]}\n"},
        {"sketch.yml", "format: 0\npoints:\n  - {id: entrance:north, at: [100, 50], facing: s}\n" + sketch},
    };
    Project project;

    for (const std::pair<std::string, std::string> &entry : files)
    {
        ProjectFile file;
        file.name = entry.first;
        file.text = entry.second;
        file.document = YAML::Load(entry.second);

        for (const ProjectFileKind &kind : projectFileKinds())
        {
            if (file.name == kind.pName)
            {
                file.schema = kind.pSchema;
            }
        }

        project.files[file.name] = file;
    }

    return project;
}

// Level land 640 high.
const std::string Level = "heights:\n  bands:\n    - {band: band:low, polygon: [[0, 0], [128, 0], [128, 128], [0, 128]]}\n";

LoweredOutdoorMap lowered(const Project &project, std::vector<ProjectIssue> *pIssues = nullptr,
    OutdoorLandCache *pLand = nullptr)
{
    LoweredOutdoorMap map;
    std::vector<ProjectIssue> issues;
    const bool ok = lowerOutdoorProject(project, map, issues, pLand);

    for (const ProjectIssue &issue : issues)
    {
        MESSAGE(issue.path << ": " << issue.message);
    }

    if (pIssues != nullptr)
    {
        *pIssues = issues;
    }
    else
    {
        REQUIRE(ok);
    }

    return map;
}

bool anyIssue(const std::vector<ProjectIssue> &issues, const std::string &fragment)
{
    return std::any_of(issues.begin(), issues.end(), [&fragment](const ProjectIssue &issue)
    {
        return issue.message.find(fragment) != std::string::npos;
    });
}

double groundAt(const LoweredOutdoorMap &map, int x, int y)
{
    return map.ground[static_cast<size_t>(y) * Side + x];
}

bool sameMap(const LoweredOutdoorMap &first, const LoweredOutdoorMap &second)
{
    return first.ground == second.ground && first.samples == second.samples && first.tiles == second.tiles
        && first.water == second.water && first.waterCorners == second.waterCorners
        && first.warnings == second.warnings && first.roadCells == second.roadCells
        && first.buildings.size() == second.buildings.size();
}
}

TEST_CASE("the read record: what the outdoor lowering read of each object, and what it never read")
{
    // A structure's notes are for its author; a bridge never reads a walkway's pier radius (S8d: it reads
    // `kerb_width` since then).
    Project project = sketchProject(Level + "structures:\n"
        "  - {id: thing:well, kind: well, at: [60, 60], notes: the village well}\n"
        "  - {id: thing:span, kind: bridge, line: [[70, 60], [76, 60]], height: 64, pier_radius: 48}\n");
    std::vector<SketchWord> words;

    {
        SketchReadRecord record(project.document("sketch.yml"));
        BuildOptions options;
        options.dryRun = true;
        BuildResult result;
        buildOutdoorProject(project, options, result);
        words = record.words();
        CHECK(record.unplaced() == 0);
    }

    const auto readOf = [&words](const std::string &object, const std::string &word)
    {
        const auto found = std::find_if(words.begin(), words.end(), [&](const SketchWord &each)
        {
            return each.object == object && each.word == word;
        });
        REQUIRE(found != words.end());
        return found->read;
    };
    CHECK(readOf("structures[0]", "at"));
    CHECK(readOf("structures[0]", "kind"));
    CHECK_FALSE(readOf("structures[0]", "notes"));
    CHECK(readOf("structures[1]", "line"));
    CHECK_FALSE(readOf("structures[1]", "pier_radius"));
    CHECK(words[0].place.empty());
    const auto bridge = std::find_if(words.begin(), words.end(), [](const SketchWord &each)
    {
        return each.object == "structures[1]";
    });
    CHECK(bridge->place == "structures[]");
    CHECK(bridge->kinds.at("kind") == "bridge");

    // Outside a record (and while paused) nothing is recorded, and a tree made in memory has no places.
    SketchReadRecord made(YAML::Load("{a: 1}"));
    YAML::Node memory(YAML::NodeType::Map);
    memory["b"] = 2;
    SketchReadRecord inMemory(memory);
    CHECK(inMemory.unplaced() == 1);
}

TEST_CASE("the sketch's kind table: a word on a structure of a kind that does not read it is a warning")
{
    Project project = sketchProject(Level + "structures:\n"
        "  - {id: thing:span, kind: bridge, line: [[70, 60], [76, 60]], height: 64, pier_radius: 48}\n"
        "  - {id: thing:walk, kind: walkway, line: [[70, 70], [76, 70]], height: 64, pier_radius: 48}\n");
    std::vector<ProjectIssue> issues;
    validateProject(project, BuildOptions(), issues);

    for (const ProjectIssue &issue : issues)
    {
        MESSAGE(issue.path << ": " << issue.message);
    }

    const auto kinds = std::count_if(issues.begin(), issues.end(), [](const ProjectIssue &issue)
    {
        return issue.code == "kind";
    });
    CHECK(kinds == 1);
    CHECK(anyIssue(issues, "the word `pier_radius` does not apply to kind bridge"));
    CHECK_FALSE(anyIssue(issues, "does not apply to kind walkway"));
}

TEST_CASE("the land is kept up to the peaks: a structure edit starts from it and gives the same map")
{
    const std::string land = Level + "  points:\n    - {at: [40, 40], h: 1600}\n"
        "  ridges:\n    - {line: [[30, 70], [90, 70]], height: 1280, slope: 3}\n";
    const std::string well = "structures:\n  - {id: thing:well, kind: well, at: [60, 60]}\n";
    const std::string well2 = "structures:\n  - {id: thing:well, kind: well, at: [62, 58]}\n";
    OutdoorLandCache cache;
    const LoweredOutdoorMap first = lowered(sketchProject(land + well), nullptr, &cache);
    CHECK(cache.misses == 1);
    CHECK(cache.hits == 0);
    CHECK(sameMap(first, lowered(sketchProject(land + well))));

    // The structure moved: the land comes from the cache, and the map is what a fresh lowering gives.
    const LoweredOutdoorMap second = lowered(sketchProject(land + well2), nullptr, &cache);
    CHECK(cache.hits == 1);
    CHECK(sameMap(second, lowered(sketchProject(land + well2))));

    // Node blocks and strokes are applied after the kept land: no new lowering of the land.
    const std::string nodes = "  nodes:\n    - {at: [50, 50], rows: [[30, 31], [32, 33]]}\n";
    const LoweredOutdoorMap third = lowered(sketchProject(land + nodes + well2), nullptr, &cache);
    CHECK(cache.hits == 2);
    CHECK(sameMap(third, lowered(sketchProject(land + nodes + well2))));
    CHECK(groundAt(third, 51, 51) == 33 * 32);

    // A land word changed: the land is lowered again.
    const std::string moved = Level + "  points:\n    - {at: [40, 42], h: 1600}\n"
        "  ridges:\n    - {line: [[30, 70], [90, 70]], height: 1280, slope: 3}\n";
    lowered(sketchProject(moved + well2), nullptr, &cache);
    CHECK(cache.misses == 2);
}

TEST_CASE("the land key: the land words, and the roads only where the rim reads them")
{
    const std::string base = Level + "frame:\n  playable: [19, 19, 109, 109]\n";
    const auto keyOf = [](const std::string &sketch)
    {
        return outdoorLandKey(sketchProject(sketch));
    };
    const std::string inside = "roads:\n  - {line: [[40, 40], [60, 40]], surface: dirt}\n";
    const std::string insideMoved = "roads:\n  - {line: [[40, 42], [60, 42]], surface: dirt}\n";
    const std::string out = "roads:\n  - {line: [[40, 40], [125, 40]], surface: dirt}\n";
    const std::string outMoved = "roads:\n  - {line: [[40, 44], [125, 44]], surface: dirt}\n";
    // Without rim strips or edge heights no road counts.
    CHECK(keyOf(base + out) == keyOf(base + outMoved));
    // With edge heights the rim reads the roads that run out of the square, and only those.
    const std::string edged = base + "  edge: {north: 640}\n";
    CHECK(keyOf(edged + inside) == keyOf(edged + insideMoved));
    CHECK(keyOf(edged + out) != keyOf(edged + outMoved));
    // The words applied after the kept land are outside the key; the others inside.
    CHECK(keyOf(Level + "  nodes:\n    - {at: [5, 5], rows: [[1]]}\n") == keyOf(Level));
    CHECK(keyOf(Level + "  strokes:\n    - {at: [5, 5], rows: [[1]]}\n  hand_made: true\n") == keyOf(Level));
    CHECK(keyOf(Level + "  points:\n    - {at: [5, 5], h: 64}\n") != keyOf(Level));
    CHECK(keyOf(Level + "water:\n  bodies:\n    - {id: water:a, kind: lake, level: 0, polygon: [[1, 1], [9, 1], [9, 9]]}\n")
        != keyOf(Level));
}

TEST_CASE("land made by hand: strokes move the land inside patches; hand-made land anywhere; never on a rebuild")
{
    const std::string patch = "  patches:\n    - {key: hill, polygon: [[50, 50], [60, 50], [60, 60], [50, 60]]}\n";
    const std::string stroke = "  strokes:\n    - {key: stroke1, at: [54, 54], rows: [[4, 4], [4, ~]]}\n";
    const LoweredOutdoorMap plain = lowered(sketchProject(Level));
    const LoweredOutdoorMap raised = lowered(sketchProject(Level + patch + stroke));
    CHECK(groundAt(raised, 54, 54) == groundAt(plain, 54, 54) + 4 * 32);
    CHECK(groundAt(raised, 55, 55) == groundAt(plain, 55, 55));
    CHECK(groundAt(raised, 53, 54) == groundAt(plain, 53, 54));

    // Outside every patch: refused on described land, taken on land marked as made by hand.
    std::vector<ProjectIssue> issues;
    lowered(sketchProject(Level + "  strokes:\n    - {at: [80, 80], rows: [[2]]}\n" + patch), &issues);
    CHECK(anyIssue(issues, "a stroke lies outside every sculpt patch"));
    const LoweredOutdoorMap anywhere = lowered(sketchProject(Level + "  strokes:\n    - {at: [80, 80], rows: [[2]]}\n"
        "  hand_made: true\n"));
    CHECK(groundAt(anywhere, 80, 80) == groundAt(plain, 80, 80) + 64);

    // A patch is bounded; a rebuild's land is never made by hand.
    lowered(sketchProject(Level + "  patches:\n    - {polygon: [[10, 10], [60, 10], [60, 20]]}\n"), &issues);
    CHECK(anyIssue(issues, "a sculpt patch is bounded"));
    lowered(sketchProject(Level + "  hand_made: true\n", "map_stats: {id: 9999, reference: oute3.odm}\n"), &issues);
    CHECK(anyIssue(issues, "a rebuild's land is described"));

    // A smoothed area takes the bumps out of the land inside it.
    const std::string bump = "  points:\n    - {at: [55, 55], h: 2400}\n";
    const LoweredOutdoorMap bumpy = lowered(sketchProject(Level + bump));
    const LoweredOutdoorMap smoothed = lowered(sketchProject(Level + bump + patch
        + "  smooth:\n    - {polygon: [[52, 52], [58, 52], [58, 58], [52, 58]], passes: 4}\n"));
    CHECK(groundAt(smoothed, 55, 55) < groundAt(bumpy, 55, 55) - 200);
    CHECK(groundAt(smoothed, 45, 45) == groundAt(bumpy, 45, 45));
}

TEST_CASE("D15's test: an agent moves a ridge under a raised and under a smoothed patch, and the strokes stay")
{
    // A person's patch over a ridge, raised by a stroke; an agent then moves the ridge two cells south.
    const std::string patch = "  hand_made: true\n";
    const auto ridgeAt = [](int y)
    {
        return "  ridges:\n    - {key: crest, line: [[30, " + std::to_string(y) + "], [90, " + std::to_string(y)
            + "]], height: 1920, slope: 4}\n";
    };
    std::string stroke = "  strokes:\n    - {key: raise, at: [56, 56], rows: [";

    for (int row = 0; row < 9; ++row)
    {
        stroke += row == 0 ? "[" : ", [";

        for (int column = 0; column < 9; ++column)
        {
            stroke += (column == 0 ? "" : ", ") + std::to_string(5 - std::max(std::abs(row - 4), std::abs(column - 4)));
        }

        stroke += "]";
    }

    stroke += "]}\n";
    const LoweredOutdoorMap before = lowered(sketchProject(Level + ridgeAt(60) + patch + stroke));
    const LoweredOutdoorMap beforePlain = lowered(sketchProject(Level + ridgeAt(60) + patch));
    const LoweredOutdoorMap after = lowered(sketchProject(Level + ridgeAt(62) + patch + stroke));
    const LoweredOutdoorMap afterPlain = lowered(sketchProject(Level + ridgeAt(62) + patch));

    // Raised: the stroke's difference stands on the moved ridge, node for node.
    for (int y = 56; y <= 64; ++y)
    {
        for (int x = 56; x <= 64; ++x)
        {
            const double strokeHeight = (5 - std::max(std::abs(y - 60), std::abs(x - 60))) * 32.0;
            CHECK(groundAt(before, x, y) - groundAt(beforePlain, x, y) == doctest::Approx(strokeHeight));
            CHECK(groundAt(after, x, y) - groundAt(afterPlain, x, y) == doctest::Approx(strokeHeight));
        }
    }

    CHECK(groundAt(after, 60, 62) != groundAt(before, 60, 62));

    // Smoothed: kept as its area (heights.smooth), the smoothing follows the moved ridge: the result is the smoothing
    // of the land as it is now. Kept as differences (the land as smoothed minus the land as it was), it would carry
    // the old ridge's bumps, inverted, onto the moved one: ripples.
    const std::string smooth = "  smooth:\n    - {key: soft, polygon: [[50, 52], [70, 52], [70, 70], [50, 70]], passes: 3}\n";
    const LoweredOutdoorMap smoothBefore = lowered(sketchProject(Level + ridgeAt(60) + patch + smooth));
    const LoweredOutdoorMap smoothAfter = lowered(sketchProject(Level + ridgeAt(62) + patch + smooth));
    // The ripple: the land's bend (the most a node stands off the mean of its four neighbours) inside the area.
    const auto bend = [](const std::vector<double> &field)
    {
        double most = 0.0;

        for (int y = 54; y <= 68; ++y)
        {
            for (int x = 52; x <= 68; ++x)
            {
                const auto at = [&field](int nodeX, int nodeY) { return field[static_cast<size_t>(nodeY) * Side + nodeX]; };
                most = std::max(most, std::abs(at(x, y) - (at(x - 1, y) + at(x + 1, y) + at(x, y - 1) + at(x, y + 1)) / 4.0));
            }
        }

        return most;
    };
    std::vector<double> asDifference = afterPlain.ground;

    for (size_t node = 0; node < asDifference.size(); ++node)
    {
        asDifference[node] += smoothBefore.ground[node] - beforePlain.ground[node];
    }

    const double rippleAsArea = bend(smoothAfter.ground);
    const double rippleAsDifference = bend(asDifference);
    MESSAGE("bend inside the smoothed area after the ridge moved: kept as its area " << rippleAsArea
        << ", kept as differences " << rippleAsDifference << " (the plain moved ridge " << bend(afterPlain.ground)
        << ")");
    CHECK(rippleAsArea < bend(afterPlain.ground));
    CHECK(rippleAsDifference > 2.0 * rippleAsArea);
    // The smoothed ridge stays smooth where it moved to: its crest lower than the plain ridge's, its sides softer.
    CHECK(groundAt(smoothAfter, 60, 62) < groundAt(afterPlain, 60, 62));
}

TEST_CASE("the outdoor view build leaves out a structure it cannot build and draws the rest")
{
    Project project = sketchProject(Level + "structures:\n"
        "  - {id: thing:well, kind: well, at: [60, 60]}\n"
        "  - {id: thing:span, kind: bridge, line: [[70, 60], [76, 60]], height: 64, kerb: 900}\n");
    ValidationParts parts;
    std::vector<ProjectIssue> issues;
    ValidationViews views;
    validateProjectParts(project, BuildOptions(), nullptr, nullptr, parts, issues, &views);
    CHECK(std::any_of(issues.begin(), issues.end(), [](const ProjectIssue &issue) { return issue.isError(); }));
    REQUIRE(views.outdoor != nullptr);
    CHECK(views.skipped == std::vector<std::string>{"thing:span"});
    CHECK(anyIssue(views.skippedIssues, "thing:span is left out of the view"));
    // The well is still there: one model.
    CHECK(views.outdoor->map.bmodels.size() == 1);

    // A schema error on one structure: that structure alone is left out.
    Project schemaBroken = sketchProject(Level + "structures:\n"
        "  - {id: thing:well, kind: well, at: [60, 60]}\n"
        "  - {id: thing:odd, kind: well, at: [64, 60], unknown_word: 3}\n");
    ValidationViews schemaViews;
    issues.clear();
    validateProjectParts(schemaBroken, BuildOptions(), nullptr, nullptr, parts, issues, &schemaViews);
    REQUIRE(schemaViews.outdoor != nullptr);
    CHECK(schemaViews.skipped == std::vector<std::string>{"thing:odd"});
}

TEST_CASE("the sketch's keys: lists a person selects are keyed, written on the core's next write")
{
    YAML::Node sketch = YAML::Load("format: 0\nheights:\n  ridges:\n    - {line: [[1, 1], [5, 5]], height: 64}\n"
        "    - {key: crest, line: [[1, 9], [5, 9]], height: 64}\n  strokes:\n    - {at: [3, 3], rows: [[1]]}\n"
        "roads:\n  - {line: [[1, 1], [9, 1]]}\nstructures:\n  - id: thing:hall\n    kind: building\n    at: [10, 10]\n"
        "    parts:\n      - {id: nave, size: [512, 512]}\n      - {size: [256, 256], porches: [{wall: s}]}\n");
    CHECK(fileHasKeyedLists("sketch.schema.json"));
    std::vector<std::string> filled;
    fillMissingKeys(sketch, "sketch.schema.json", &filled);
    CHECK(sketch["heights"]["ridges"][0]["key"].Scalar() == "ridge1");
    CHECK(sketch["heights"]["ridges"][1]["key"].Scalar() == "crest");
    CHECK(sketch["heights"]["strokes"][0]["key"].Scalar() == "stroke1");
    CHECK(sketch["roads"][0]["key"].Scalar() == "road1");
    // Parts are named by their ids: none is written (an id is the author's), the second reads as part2.
    CHECK_FALSE(sketch["structures"][0]["parts"][1]["id"].IsDefined());
    CHECK(sketch["structures"][0]["parts"][1]["porches"][0]["key"].Scalar() == "porch1");
    const std::vector<std::string> addresses = subObjectAddresses(sketch, "sketch.schema.json");
    CHECK(std::find(addresses.begin(), addresses.end(), "thing:hall/parts/part2/porches/porch1") != addresses.end());
    CHECK(std::find(addresses.begin(), addresses.end(), "/heights/ridges/crest") != addresses.end());
}
