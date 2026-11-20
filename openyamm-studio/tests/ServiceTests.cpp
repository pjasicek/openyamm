// S5a2, open and look (devdocs/map_studio/S5_BROWSER_EDITOR.md 6.4): severities set where each issue is found, the
// validation kept file by file, the service that keeps projects between calls (and an edit through it that does what
// applyTransaction does), the asset tables parsed once, and the view (mesh and layout) made from the lowering.
#include "doctest/doctest.h"

#include "core/IndoorBuild.h"
#include "core/IndoorLowering.h"
#include "core/Ops.h"
#include "core/Polygon.h"
#include "core/Project.h"
#include "core/Service.h"
#include "core/Sketch.h"
#include "core/View.h"

#include <algorithm>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <map>
#include <random>
#include <thread>

using namespace OpenYAMM::Studio;

namespace
{
const char *CardText = "format: 0\nid: viewtest\nworld: mm6\nkind: indoor\n";
const char *RoomsText =
    "format: 0\n"
    "themes:\n"
    "  - id: theme:plain\n"
    "    wall: {texture: wall, size: [128, 128]}\n"
    "    floor: {texture: floor, size: [256, 128]}\n"
    "    ceiling: {texture: ceil, size: [128, 128]}\n"
    "defaults: {theme: theme:plain}\n"
    "rooms:\n"
    "  - {id: room:a, outline: [[0, 0], [512, 0], [512, 512], [0, 512]], floor: 0, ceiling: 384}\n"
    "  - {id: room:b, outline: [[576, 0], [1088, 0], [1088, 512], [576, 512]], floor: 0, ceiling: 384}\n"
    "openings:\n"
    "  - {id: open:ab, from: room:a, to: room:b, width: 128, height: 256}\n";
const char *ObjectsText =
    "format: 0\nstart: {room: room:a}\ndoors:\n  - {id: door:ab, opening: open:ab, speed: 96}\n";

std::filesystem::path scratchFolder(const std::string &name)
{
    const std::filesystem::path root = std::filesystem::temp_directory_path()
        / ("oymap_s5a2_" + name + "_" + std::to_string(std::random_device{}()));
    std::filesystem::create_directories(root);
    return root;
}

void writeText(const std::filesystem::path &path, const std::string &text)
{
    std::filesystem::create_directories(path.parent_path());
    std::ofstream(path, std::ios::binary) << text;
}

std::string readText(const std::filesystem::path &path)
{
    std::ifstream stream(path, std::ios::binary);
    return std::string(std::istreambuf_iterator<char>(stream), std::istreambuf_iterator<char>());
}

std::filesystem::path writeProject(const std::filesystem::path &root)
{
    writeText(root / "project.yml", CardText);
    writeText(root / "rooms.yml", RoomsText);
    writeText(root / "objects.yml", ObjectsText);
    return root;
}

Project loaded(const std::filesystem::path &root)
{
    Project project;
    std::vector<ProjectIssue> issues;
    REQUIRE(loadProject(root, project, issues));
    REQUIRE(issues.empty());
    return project;
}

std::string described(const std::vector<ProjectIssue> &issues)
{
    std::string text;

    for (const ProjectIssue &issue : issues)
    {
        text += std::string(severityName(issue.severity)) + " " + issue.code + " " + issue.file + ": " + issue.path
            + ": " + issue.message + "\n";
    }

    return text;
}

// The source files of a project folder and its history's entries (without their time), for comparing two folders.
std::string folderState(const std::filesystem::path &root)
{
    std::string state;

    for (const char *pName : {"project.yml", "rooms.yml", "objects.yml", "wiring.yml", "plan.yml", "ids.lock.yml"})
    {
        state += std::string("== ") + pName + "\n" + readText(root / pName);
    }

    for (int sequence = 1; sequence < 10; ++sequence)
    {
        char name[16];
        std::snprintf(name, sizeof(name), "%04d", sequence);
        const std::filesystem::path entry = root / ".oymap" / "history" / name / "entry.yml";

        if (std::filesystem::exists(entry))
        {
            state += std::string("== history ") + name + "\n" + readText(entry);
        }
    }

    state += "== head\n" + readText(root / ".oymap" / "head.yml");
    return state;
}

// Moves a file's modification time on, as a later write would (the service notices a change by size and time).
void touchLater(const std::filesystem::path &path)
{
    std::filesystem::last_write_time(path, std::filesystem::last_write_time(path) + std::chrono::seconds(2));
}
}

TEST_CASE("S5a2: severities are set where an issue is found: a sketch's heights finding is a warning, errors stay")
{
    ProjectIssue plain{"rooms.yml", "rooms[0]", "a problem", "geometry"};
    CHECK(plain.severity == IssueSeverity::Error);
    CHECK(plain.isError());
    CHECK(std::string(severityName(IssueSeverity::Warning)) == "warning");
    CHECK(std::string(severityName(IssueSeverity::Note)) == "note");
    CHECK_FALSE(hasErrors({{"sketch.yml", "", "x", "heights", IssueSeverity::Warning}}));
    CHECK(hasErrors({{"sketch.yml", "", "x", "heights", IssueSeverity::Warning}, plain}));

    // A cliff that ends short of another: the sketch checks find it on `heights` and the build takes it as drawn.
    Project project;
    const std::vector<std::pair<std::string, std::string>> files = {
        {"project.yml", "format: 0\nid: sevtest\nworld: mm8\nkind: outdoor\n"},
        {"plan.yml", "format: 0\nentrances:\n  - {id: entrance:north, kind: arrival, facing: s}\n"
            "height_bands:\n  - {id: band:low, range: [576, 704]}\n"},
        {"sketch.yml", "format: 0\npoints:\n  - {id: entrance:north, at: [100, 50], facing: s}\n"
            "heights:\n  bands:\n    - {band: band:low, polygon: [[0, 0], [128, 0], [128, 128], [0, 128]]}\n"
            "  cliffs:\n    - {line: [[30, 10], [30, 38]], drop: 800}\n    - {line: [[10, 40], [32, 40]], drop: 800}\n"
            "  grid: {step: 7, rows: []}\n"},
    };

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

    std::vector<ProjectIssue> issues;
    validateSketch(project, issues);
    size_t heights = 0;

    for (const ProjectIssue &issue : issues)
    {
        if (issue.code == "heights")
        {
            ++heights;
            CHECK(issue.severity == IssueSeverity::Warning);
        }
        else
        {
            CHECK(issue.severity == IssueSeverity::Error);
        }
    }

    CHECK(heights >= 2);
}

TEST_CASE("S5a2: the validation kept file by file gives what a full validation gives, after any change")
{
    const std::filesystem::path root = writeProject(scratchFolder("parts"));
    writeText(root / "wiring.yml", "format: 0\nevents:\n  - {id: evt:gate, preset: door, door: door:ab}\n");
    BuildOptions options;
    Project project = loaded(root);
    ValidationParts parts;
    std::vector<ProjectIssue> issues;
    validateProjectParts(project, options, nullptr, nullptr, parts, issues, nullptr);
    std::vector<ProjectIssue> full;
    validateProject(project, options, full);
    CHECK(described(issues) == described(full));
    REQUIRE(parts.valid);

    // Each change: the file rewritten, then the kept parts against a full validation of the new state.
    const std::vector<std::pair<std::string, std::string>> changes = {
        // A room moved: only rooms.yml is walked again (the ids are the same).
        {"rooms.yml", std::string(RoomsText).replace(std::string(RoomsText).find("[0, 512]]"), 9, "[0, 500]]")},
        // A reference to nothing in wiring.yml.
        {"wiring.yml", "format: 0\nevents:\n  - {id: evt:gate, preset: door, door: door:nothing}\n"},
        // An id removed that another file refers to: every file is walked again.
        {"objects.yml", "format: 0\nstart: {room: room:a}\n"},
        // A schema issue: the check stops at the schemas, as before.
        {"objects.yml", "format: 0\nstart: {room: room:a}\ndoors: [{id: door:ab}]\nnot_a_key: 1\n"},
        // And back.
        {"objects.yml", ObjectsText},
        {"wiring.yml", "format: 0\nevents:\n  - {id: evt:gate, preset: door, door: door:ab}\n"},
    };
    std::set<std::string> changedSince;

    for (const std::pair<std::string, std::string> &change : changes)
    {
        writeText(root / change.first, change.second);
        changedSince.insert(change.first);
        project = loaded(root);
        ValidationParts next;
        std::vector<ProjectIssue> kept;
        validateProjectParts(project, options, &parts, &changedSince, next, kept, nullptr);
        std::vector<ProjectIssue> fresh;
        validateProject(project, options, fresh);
        INFO(change.first);
        CHECK(described(kept) == described(fresh));

        if (next.valid)
        {
            parts = next;
            changedSince.clear();
        }
    }
}

TEST_CASE("S5a2: an edit through the service writes and records what applyTransaction does, and keeps the project")
{
    const std::filesystem::path base = scratchFolder("service");
    const std::filesystem::path first = writeProject(base / "first");
    const std::filesystem::path second = writeProject(base / "second");
    StudioService service;
    const std::vector<std::string> transactions = {
        // A field changed, a field added (its key out of the canonical order until read back), an object added.
        R"([{"op":"set","id":"door:ab","fields":{"speed":128}}])",
        R"([{"op":"set","id":"room:a","file":"rooms.yml","fields":{"notes":"the hall"}},)"
            R"({"op":"add","to":"lights","value":{"id":"light:lamp","room":"room:a","offset":[0,0]}}])",
        // A patch of an outline.
        R"([{"op":"patch","id":"room:b","file":"rooms.yml","patch":[{"op":"replace","path":"/outline/1","value":[1104,0]}]}])",
        // Refused: a new error (a door on no opening).
        R"([{"op":"add","to":"doors","value":{"id":"door:nowhere","opening":"open:none"}}])",
        // Refused: a bad operation.
        R"([{"op":"set","id":"door:missing","fields":{"speed":1}}])",
    };

    for (const std::string &text : transactions)
    {
        const YAML::Node operations = YAML::Load(text);
        TransactionOptions options;
        options.author = "user";
        options.label = "test";
        TransactionResult expected;
        const bool expectedOk = applyTransaction(first, operations, options, expected);
        std::vector<ProjectIssue> unused;
        StudioService::Entry *pEntry = service.project(second, unused);
        REQUIRE(pEntry != nullptr);
        TransactionResult result;
        bool ok = false;
        {
            ProjectWriteLock lock(second);
            REQUIRE(lock.held());
            ok = service.applyTransaction(*pEntry, operations, options, result);
        }
        INFO(text);
        CHECK(ok == expectedOk);
        CHECK(result.applied == expected.applied);
        CHECK(result.refusal == expected.refusal);
        CHECK(result.revisionBefore == expected.revisionBefore);
        CHECK(result.revisionAfter == expected.revisionAfter);
        CHECK(result.changes == expected.changes);
        CHECK(result.errors == expected.errors);
        CHECK(described(result.newIssues) == described(expected.newIssues));
        CHECK(described(result.fixedIssues) == described(expected.fixedIssues));
        CHECK(result.filesAfter == expected.filesAfter);
        // The history's entries hold a time: compared without it.
        std::string firstState = folderState(first);
        std::string secondState = folderState(second);

        for (std::string *pState : {&firstState, &secondState})
        {
            size_t at = 0;

            while ((at = pState->find("time: ", at)) != std::string::npos)
            {
                pState->erase(at, pState->find('\n', at) - at);
            }
        }

        CHECK(firstState == secondState);
        // The kept project is the one on disk.
        service.idle();
        StudioService::Entry *pAfter = service.project(second, unused);
        REQUIRE(pAfter != nullptr);
        CHECK(pAfter->memory.revision == projectRevision(loaded(second)));
    }
}

TEST_CASE("S5a2: the service reads a file again only when its bytes changed, and finds edits made with other tools")
{
    const std::filesystem::path root = writeProject(scratchFolder("stamps"));
    StudioService service;
    std::vector<ProjectIssue> issues;
    StudioService::Entry *pEntry = service.project(root, issues);
    REQUIRE(pEntry != nullptr);
    const std::string revision = pEntry->memory.revision;
    CHECK(revision == projectRevision(loaded(root)));
    const std::vector<ProjectIssue> &validated = service.validate(*pEntry, false);
    CHECK_FALSE(hasErrors(validated));
    CHECK(pEntry->validated);

    // A file written again with the same bytes: the validation is kept.
    touchLater(root / "rooms.yml");
    pEntry = service.project(root, issues);
    REQUIRE(pEntry != nullptr);
    CHECK(pEntry->memory.revision == revision);
    CHECK(pEntry->validated);

    // A real change: read again, a new revision, the validation dropped.
    writeText(root / "objects.yml", std::string(ObjectsText) + "notes: changed by hand\n");
    touchLater(root / "objects.yml");
    pEntry = service.project(root, issues);
    REQUIRE(pEntry != nullptr);
    CHECK(pEntry->memory.revision != revision);
    CHECK(pEntry->memory.revision == projectRevision(loaded(root)));
    CHECK_FALSE(pEntry->validated);

    // A file that does not parse: an issue of the reading, the project still opens.
    writeText(root / "wiring.yml", "format: 0\nevents: [unclosed\n");
    pEntry = service.project(root, issues);
    REQUIRE(pEntry != nullptr);
    const std::vector<ProjectIssue> reading = service.readingIssues(*pEntry);
    REQUIRE_FALSE(reading.empty());
    CHECK(reading.front().file == "wiring.yml");
    CHECK(reading.front().code == "yaml");

    // No folder: not a project, and no absolute path in what is said.
    issues.clear();
    CHECK(service.project(root / "nothing", issues) == nullptr);
    REQUIRE_FALSE(issues.empty());
    CHECK(issues.front().message.find(root.string()) == std::string::npos);
}

TEST_CASE("S5a2: the asset tables are parsed once with their lookups, each the first row that fits")
{
    LoweringOptions options;
    options.decorationTableText =
        "1\tBarrel\tbarrel\t0\t40\t96\n"
        "2\tbarrel\tsecond barrel\t0\t50\t100\n"
        "0\tTorch\ttorch\n"
        "3\tTORCH\tlit torch\t0\t10\t60\n"
        "x\tnone\n";
    options.monsterTableText = "// comment\n\nId\tName\n1\tGoblin\n";
    const std::shared_ptr<const LoweringTables> tables = parseLoweringTables(options);
    CHECK(tables->decorationListIds.at("barrel") == 0);
    // Row 0 has no number above 0: the next row of the name gives the id.
    CHECK(tables->decorationListIds.at("torch") == 2);
    CHECK(tables->decorationHints.at("barrel") == "barrel");
    CHECK(tables->decorationHints.at("torch") == "torch");
    CHECK(tables->decorationShapes.at("barrel").radius == doctest::Approx(40.0));
    CHECK(tables->decorationShapes.at("barrel").top == doctest::Approx(96.0));
    // The first row of torch has three cells: its shape is the next row's.
    CHECK(tables->decorationShapes.at("torch").top == doctest::Approx(60.0));
    CHECK_FALSE(tables->decorationListIds.contains("none"));
    REQUIRE(tables->monsterRows.size() == 2);
    CHECK(tables->monsterRows[1][1] == "Goblin");
}

TEST_CASE("S5a2: polygons whose boxes only touch do not overlap; overlapping ones still do")
{
    const std::vector<Point2> a = {{0, 0}, {512, 0}, {512, 512}, {0, 512}};
    const std::vector<Point2> touching = {{512, 0}, {1024, 0}, {1024, 512}, {512, 512}};
    const std::vector<Point2> apart = {{600, 600}, {700, 600}, {700, 700}, {600, 700}};
    const std::vector<Point2> inside = {{100, 100}, {200, 100}, {200, 200}, {100, 200}};
    // An L whose box covers the square's corner but whose arms miss it.
    const std::vector<Point2> ell = {{600, -100}, {700, -100}, {700, 700}, {-100, 700}, {-100, 600}, {600, 600}};
    CHECK_FALSE(polygonsOverlap(a, touching));
    CHECK_FALSE(polygonsOverlap(a, apart));
    CHECK(polygonsOverlap(a, inside));
    CHECK_FALSE(polygonsOverlap(a, ell));
    CHECK_FALSE(polygonsOverlap(a, {}));
}

TEST_CASE("S5a2: the view mesh is the lowering's visible faces with their owners; the layout places every object")
{
    const std::filesystem::path root = writeProject(scratchFolder("view"));
    writeText(root / "objects.yml", std::string(ObjectsText)
        + "chests:\n  - {id: chest:box, room: room:b, offset: [0, 0]}\n");
    const Project project = loaded(root);
    LoweredIndoorMap lowered;
    std::vector<ProjectIssue> issues;
    REQUIRE(lowerIndoorProject(project, LoweringOptions(), lowered, issues));
    REQUIRE(issues.empty());

    // Faces stamped with their objects: rooms, walls, the opening's portal, the door.
    std::set<std::string> owners;
    size_t visible = 0;

    for (const GlbNode &node : lowered.nodes)
    {
        for (const GlbFace &face : node.faces)
        {
            owners.insert(face.owner);
            visible += node.name.rfind("PORTAL_", 0) == 0 ? 0 : 1;
        }
    }

    CHECK(owners.contains("room:a"));
    CHECK(owners.contains("room:a/walls/0"));
    CHECK(owners.contains("open:ab"));
    CHECK(owners.contains("door:ab"));

    const ViewMesh mesh = indoorViewMesh(lowered, LiquidTextures());
    CHECK(mesh.faces == visible);
    CHECK(mesh.vertices * 3 == mesh.positions.count);
    CHECK(mesh.normals.count == mesh.positions.count);
    CHECK(mesh.uvs.count == mesh.vertices * 2);
    CHECK(mesh.indices.count == mesh.triangles * 3);
    CHECK(mesh.triangleFaces.count == mesh.triangles);
    CHECK(mesh.faceOwners.count == mesh.faces);
    CHECK(mesh.bytes.size() == mesh.faceOwners.offset + mesh.faceOwners.count * 4);

    for (const ViewMesh::Section *pSection : {&mesh.positions, &mesh.normals, &mesh.uvs, &mesh.indices,
             &mesh.triangleFaces, &mesh.faceOwners})
    {
        CHECK(pSection->offset % 4 == 0);
    }

    // Every triangle names a face, every face an owner; groups cover the indices in order.
    std::vector<uint32_t> triangleFaces(mesh.triangles);
    std::memcpy(triangleFaces.data(), mesh.bytes.data() + mesh.triangleFaces.offset, mesh.triangles * 4);
    CHECK(std::all_of(triangleFaces.begin(), triangleFaces.end(), [&mesh](uint32_t face) { return face < mesh.faces; }));
    std::vector<uint32_t> faceOwners(mesh.faces);
    std::memcpy(faceOwners.data(), mesh.bytes.data() + mesh.faceOwners.offset, mesh.faces * 4);
    CHECK(std::all_of(faceOwners.begin(), faceOwners.end(),
        [&mesh](uint32_t owner) { return owner < mesh.owners.size(); }));
    size_t next = 0;

    for (const ViewMesh::Group &group : mesh.groups)
    {
        CHECK(group.first == next);
        next += group.count;
    }

    CHECK(next == mesh.indices.count);
    CHECK(mesh.owners.front().id.empty());
    // Texture coordinates in texels: the floor's texture is 256 wide, so a room 512 across spans two of its widths.
    const auto floor = std::find_if(mesh.groups.begin(), mesh.groups.end(),
        [](const ViewMesh::Group &group) { return group.texture == "floor"; });
    REQUIRE(floor != mesh.groups.end());
    CHECK_FALSE(floor->unitUv);
    std::vector<float> uvs(mesh.uvs.count);
    std::memcpy(uvs.data(), mesh.bytes.data() + mesh.uvs.offset, mesh.uvs.count * 4);
    std::vector<uint32_t> indices(mesh.indices.count);
    std::memcpy(indices.data(), mesh.bytes.data() + mesh.indices.offset, mesh.indices.count * 4);
    // The span of u over each face of the group (faces are moved by whole repeats, so only a face's own span says).
    std::map<uint32_t, std::pair<float, float>> spans;

    for (size_t index = floor->first; index < floor->first + floor->count; ++index)
    {
        const float u = uvs[indices[index] * 2];
        const auto found = spans.try_emplace(triangleFaces[index / 3], u, u).first;
        found->second.first = std::min(found->second.first, u);
        found->second.second = std::max(found->second.second, u);
    }

    CHECK(std::any_of(spans.begin(), spans.end(), [](const std::pair<const uint32_t, std::pair<float, float>> &span)
    {
        return span.second.second - span.second.first == doctest::Approx(512.0f);
    }));
    CHECK(mesh.min[0] == 0);
    CHECK(mesh.max[0] == 1088);

    JsonWriter writer;
    writer.beginObject();
    writeIndoorLayout(writer, lowered);
    writer.endObject();
    const YAML::Node layout = YAML::Load(writer.take());
    REQUIRE(layout["rooms"].size() == 2);
    CHECK(layout["rooms"][0]["id"].Scalar() == "room:a");
    CHECK(layout["rooms"][0]["outline"].size() == 4);
    REQUIRE(layout["openings"].size() == 1);
    CHECK(layout["openings"][0]["from"].Scalar() == "room:a");
    CHECK(layout["openings"][0]["a"][0].as<int>() == 512);
    CHECK(layout["doors"][0]["opening"].Scalar() == "open:ab");
    bool chest = false;

    for (const YAML::Node &thing : layout["things"])
    {
        chest = chest || (thing["id"].Scalar() == "chest:box" && thing["kind"].Scalar() == "chest");
    }

    CHECK(chest);
    CHECK(layout["start"]["at"].size() == 3);
}

TEST_CASE("S5a2: the service's view is the current state's, or the last one that lowered, marked by its revision")
{
    const std::filesystem::path root = writeProject(scratchFolder("stale"));
    StudioService service;
    std::vector<ProjectIssue> issues;
    StudioService::Entry *pEntry = service.project(root, issues);
    REQUIRE(pEntry != nullptr);
    std::shared_ptr<StudioService::View> view = service.view(*pEntry);
    REQUIRE(view);
    CHECK(view->revision == pEntry->memory.revision);
    std::string errorMessage;
    REQUIRE(service.makeMesh(*pEntry, *view, errorMessage));
    CHECK(std::filesystem::exists(root / view->meshFile));
    CHECK(view->meshFile.rfind(".oymap/view/" + view->revision + "-", 0) == 0);
    const std::string good = view->revision;

    // A room that does not lower (S5b1, 2.4.2): a view build of the new revision without it.
    writeText(root / "rooms.yml", std::string(RoomsText) + "  - {id: room:c, outline: [[0, 0], [10, 0]], floor: 0, "
        "ceiling: 384}\n");
    touchLater(root / "rooms.yml");
    pEntry = service.project(root, issues);
    REQUIRE(pEntry != nullptr);
    view = service.view(*pEntry);
    REQUIRE(view);
    CHECK(view->revision == pEntry->memory.revision);
    CHECK(view->lowered.skipped == std::vector<std::string>{"room:c"});
    CHECK(hasErrors(pEntry->issues));

    // An error that names no object (the file's format): the view stays the last one that lowered, now stale.
    const std::string skippedRevision = view->revision;
    std::string rooms = RoomsText;
    rooms.replace(0, rooms.find('\n'), "format: 7");
    writeText(root / "rooms.yml", rooms);
    touchLater(root / "rooms.yml");
    pEntry = service.project(root, issues);
    REQUIRE(pEntry != nullptr);
    view = service.view(*pEntry);
    REQUIRE(view);
    CHECK(view->revision == skippedRevision);
    CHECK(pEntry->memory.revision != skippedRevision);
    CHECK(pEntry->memory.revision != good);
}
