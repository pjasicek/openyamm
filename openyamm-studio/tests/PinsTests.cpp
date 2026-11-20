// S5a1, pins from the game (devdocs/map_studio/S5_BROWSER_EDITOR.md 6.4): the three classes of file and the source
// revision, the lock as a record that keeps removed ids until a prune, pins format 1 and `oymap pins`, `oymap record`,
// and <stem>.studio.yml on every install route.
#include "doctest/doctest.h"

#include "core/CanonicalYaml.h"
#include "core/IndoorBuild.h"
#include "core/IndoorLowering.h"
#include "core/Ops.h"
#include "core/Pins.h"
#include "core/Project.h"

#include <algorithm>
#include <filesystem>
#include <fstream>
#include <random>
#include <thread>

using namespace OpenYAMM::Studio;

namespace
{
const char *CardText = "format: 0\nid: testmap\nworld: mm6\nkind: indoor\n";
const char *RoomsText =
    "format: 0\n"
    "themes:\n"
    "  - id: theme:plain\n"
    "    wall: {texture: wall, size: [128, 128]}\n"
    "    floor: {texture: floor, size: [128, 128]}\n"
    "    ceiling: {texture: ceil, size: [128, 128]}\n"
    "defaults: {theme: theme:plain}\n"
    "rooms:\n"
    "  - {id: room:a, outline: [[0, 0], [512, 0], [512, 512], [0, 512]], floor: 0, ceiling: 384}\n"
    "  - {id: room:b, outline: [[576, 0], [1088, 0], [1088, 512], [576, 512]], floor: 0, ceiling: 384}\n"
    "openings:\n"
    "  - {id: open:ab, from: room:a, to: room:b, width: 128, height: 256}\n";

std::filesystem::path scratchFolder(const std::string &name)
{
    const std::filesystem::path root = std::filesystem::temp_directory_path()
        / ("oymap_s5a1_" + name + "_" + std::to_string(std::random_device{}()));
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

std::filesystem::path writeProject(const std::string &name)
{
    const std::filesystem::path root = scratchFolder(name);
    writeText(root / "project.yml", CardText);
    writeText(root / "rooms.yml", RoomsText);
    writeText(root / "objects.yml",
        "format: 0\nstart: {room: room:a}\ndoors:\n  - {id: door:ab, opening: open:ab, speed: 96}\n");
    return root;
}

bool hasLine(const std::vector<std::string> &lines, const std::string &fragment)
{
    return std::any_of(lines.begin(), lines.end(), [&fragment](const std::string &line)
    {
        return line.find(fragment) != std::string::npos;
    });
}

size_t lineCount(const std::string &text)
{
    return static_cast<size_t>(std::count(text.begin(), text.end(), '\n'));
}

ProjectStatus statusOf(const std::filesystem::path &root)
{
    ProjectStatus status;
    std::string errorMessage;
    REQUIRE(projectStatus(root, status, errorMessage));
    return status;
}

bool isHex(const std::string &text, size_t length)
{
    return text.size() == length && std::all_of(text.begin(), text.end(), [](char letter)
    {
        return (letter >= '0' && letter <= '9') || (letter >= 'a' && letter <= 'f');
    });
}

// A PNG-shaped file: the importer and the pins only move and copy pictures.
void writePicture(const std::filesystem::path &path, const std::string &marker)
{
    writeText(path, "\x89PNG\r\n\x1a\n" + marker);
}
}

TEST_CASE("S5a1: the source revision is 128 bits over the source files; the lock and the pins never move it")
{
    const std::filesystem::path root = writeProject("revision");
    const ProjectStatus first = statusOf(root);
    CHECK(isHex(first.revision, 32));
    CHECK(first.lockHash == "none");
    CHECK(contentHash128("abc") == "ba7816bf8f01cfea414140de5dae2223");

    // A lock written from outside (a git checkout): the new record, noted in lock.log, no history entry.
    writeText(root / "ids.lock.yml", "format: 0\ndoors: {door:ab: 4}\n");
    const ProjectStatus afterLock = statusOf(root);
    CHECK(afterLock.revision == first.revision);
    CHECK(afterLock.history.empty());
    CHECK(afterLock.outsideChanges.empty());
    CHECK(isHex(afterLock.lockHash, 32));
    CHECK(readText(root / ".oymap" / "lock.log").find("\"by\":\"outside\"") != std::string::npos);
    CHECK(readText(root / ".oymap" / ".gitignore") == "*\n");

    // A pin changes the pins document's counter, not the revision.
    NewPin pin;
    pin.text = "The gate reads as a wall.";
    pin.on = "door:ab";
    PinResult added;
    REQUIRE(addPin(root, pin, added));
    CHECK(added.counter == 1);
    const ProjectStatus afterPin = statusOf(root);
    CHECK(afterPin.revision == first.revision);
    CHECK(afterPin.history.empty());

    // A transaction does move it; its entry carries the author and label, and expect_revision is the source one.
    TransactionOptions options;
    options.author = "agent:test";
    options.label = "slower gate";
    options.expectRevision = first.revision;
    TransactionResult result;
    REQUIRE(applyTransaction(root, YAML::Load("[{op: set, id: door:ab, fields: {speed: 64}}]"), options, result));
    CHECK(result.revisionAfter != first.revision);
    CHECK(isHex(result.revisionAfter, 32));
    CHECK(result.filesAfter.contains("objects.yml"));
    const ProjectStatus afterEdit = statusOf(root);
    REQUIRE(afterEdit.history.size() == 1);
    CHECK(afterEdit.history[0].author == "agent:test");
    CHECK(afterEdit.history[0].label == "slower gate");

    // Pins and the lock are not files an operation changes.
    TransactionResult refused;
    CHECK_FALSE(applyTransaction(root, YAML::Load(
        "[{op: set_value, file: review/pins.yml, path: notes, value: x}]"), {}, refused));
    CHECK(refused.refusal == TransactionRefusal::BadOperation);
    CHECK(hasLine(refused.errors, "oymap pins"));
    CHECK_FALSE(applyTransaction(root, YAML::Load("[{op: pin.add, value: {id: pin:x, text: y}}]"), {}, refused));
    std::filesystem::remove_all(root);
}

TEST_CASE("S5a1: a history kept before the split is re-keyed once, and undo passes over the lock's build entries")
{
    const std::filesystem::path root = writeProject("migrate");
    const std::string lockBefore = "format: 0\ndoors: {door:ab: 1}\n";
    const std::string lockAfter = "format: 0\ndoors: {door:ab: 1, door:cd: 2}\n";
    writeText(root / "ids.lock.yml", lockAfter);
    // As an older core left it: a head over every file, the lock in last/, and a `build` entry for a lock change.
    writeText(root / ".oymap" / "head.yml", "revision: \"0123456789ab\"\ncursor: 1\ncount: 1\n");

    for (const char *pName : {"project.yml", "rooms.yml", "objects.yml"})
    {
        writeText(root / ".oymap" / "last" / pName, readText(root / pName));
    }

    writeText(root / ".oymap" / "last" / "ids.lock.yml", lockAfter);
    writeText(root / ".oymap" / "history" / "0001" / "entry.yml",
        "sequence: 1\nkind: build\nrevision_before: \"ba9876543210\"\nrevision_after: \"0123456789ab\"\n"
        "changes: [\"ids.lock.yml: changed doors\"]\nfiles: [ids.lock.yml]\n");
    writeText(root / ".oymap" / "history" / "0001" / "before" / "ids.lock.yml", lockBefore);
    writeText(root / ".oymap" / "history" / "0001" / "after" / "ids.lock.yml", lockAfter);

    const ProjectStatus status = statusOf(root);
    CHECK(isHex(status.revision, 32));
    CHECK(status.outsideChanges.empty());
    REQUIRE(status.history.size() == 1);
    CHECK(status.history[0].kind == "build");
    CHECK(readText(root / ".oymap" / "migrations.log").find("re-keyed from 0123456789ab") != std::string::npos);
    CHECK(readText(root / ".oymap" / "head.yml").find("scheme: source-sha256-128") != std::string::npos);

    // Nothing of the source to undo: the lock stays.
    std::vector<std::string> changes;
    std::string errorMessage;
    CHECK_FALSE(undoProject(root, changes, errorMessage));
    CHECK(errorMessage == "nothing to undo");
    CHECK(readText(root / "ids.lock.yml") == lockAfter);

    // A source change undone puts the source back and leaves the lock alone.
    TransactionResult result;
    REQUIRE(applyTransaction(root, YAML::Load("[{op: set, id: door:ab, fields: {speed: 200}}]"), {}, result));
    writeText(root / "ids.lock.yml", lockBefore);
    REQUIRE(undoProject(root, changes, errorMessage));
    CHECK(readText(root / "objects.yml").find("speed: 96") != std::string::npos);
    CHECK(readText(root / "ids.lock.yml") == lockBefore);
    CHECK(statusOf(root).revision == status.revision);
    REQUIRE(redoProject(root, changes, errorMessage));
    CHECK(readText(root / "objects.yml").find("speed: 200") != std::string::npos);
    std::filesystem::remove_all(root);
}

TEST_CASE("S5a1: undo never changes a number: an event removed and brought back keeps it, a new one takes another")
{
    const auto lowerWith = [](const std::string &events, const std::string &lock, IdsLock &ids)
    {
        std::vector<std::pair<std::string, std::string>> files = {{"project.yml", CardText}, {"rooms.yml", RoomsText},
            {"objects.yml", "format: 0\nstart: {room: room:a}\n"},
            {"wiring.yml", "format: 0\nevents:\n" + events}};

        if (!lock.empty())
        {
            files.emplace_back("ids.lock.yml", lock);
        }

        Project project;

        for (const std::pair<std::string, std::string> &file : files)
        {
            ProjectFile entry;
            entry.name = file.first;
            entry.text = file.second;
            entry.document = YAML::Load(file.second);

            for (const ProjectFileKind &kind : projectFileKinds())
            {
                if (entry.name == kind.pName)
                {
                    entry.schema = kind.pSchema;
                }
            }

            project.files[entry.name] = entry;
        }

        std::vector<ProjectIssue> issues;
        LoweredIndoorMap lowered;
        REQUIRE(lowerIndoorProject(project, {}, lowered, issues));
        ids = lowered.ids;
        return writeCanonicalYaml(ids.toDocument(), SchemaSet::builtIn(), "ids_lock.schema.json");
    };
    IdsLock ids;
    const std::string first = lowerWith("  - {id: evt:hello, preset: text, trigger: load, text: Hello}\n", "", ids);
    CHECK(ids.events.at("evt:hello") == 1);
    // Removed, and another event added: the removed one's number stays in the lock and is not given away.
    const std::string second = lowerWith("  - {id: evt:bye, preset: text, trigger: load, text: Bye}\n", first, ids);
    CHECK(ids.events.at("evt:hello") == 1);
    CHECK(ids.events.at("evt:bye") == 2);
    // The undo brings it back: the same number.
    lowerWith("  - {id: evt:hello, preset: text, trigger: load, text: Hello}\n", second, ids);
    CHECK(ids.events.at("evt:hello") == 1);
    CHECK(ids.events.at("evt:bye") == 2);
}

TEST_CASE("S5a1: the lock is written as a record and logged; oymap lock prune drops only what the project lacks")
{
    const std::filesystem::path root = writeProject("lock");
    writeText(root / "wiring.yml", "format: 0\nevents:\n  - {id: evt:hello, preset: text, trigger: load, text: Hi}\n");
    const std::string lock = "format: 0\nevents:\n  evt:gone: 2\n  evt:hello: 1\n";
    bool changed = false;
    std::string errorMessage;
    REQUIRE(writeLockRecord(root, lock, "0123456789abcdef0123456789abcdef", "build", changed, errorMessage));
    CHECK(changed);
    REQUIRE(writeLockRecord(root, lock, "0123456789abcdef0123456789abcdef", "build", changed, errorMessage));
    CHECK_FALSE(changed);
    const std::string log = readText(root / ".oymap" / "lock.log");
    CHECK(lineCount(log) == 1);
    CHECK(log.find("\"by\":\"build\"") != std::string::npos);
    CHECK(log.find("events: evt:gone 2 added") != std::string::npos);
    CHECK(lockDifferences("format: 0\nevents: {evt:a: 1, evt:b: 2}\n", "format: 0\nevents: {evt:a: 3, evt:c: 4}\n")
        == std::vector<std::string>{"events: evt:a 1 -> 3", "events: evt:c 4 added", "events: evt:b 2 dropped"});
    // The status sees the build's own write as no outside change.
    const ProjectStatus status = statusOf(root);
    CHECK(lineCount(readText(root / ".oymap" / "lock.log")) == 1);
    CHECK(status.lockHash == lockHashOfText(&lock));

    LockPruneResult listed;
    REQUIRE(pruneProjectLock(root, true, listed, errorMessage));
    CHECK(listed.dropped == std::vector<std::string>{"events: evt:gone 2"});
    CHECK(readText(root / "ids.lock.yml") == lock);
    LockPruneResult pruned;
    REQUIRE(pruneProjectLock(root, false, pruned, errorMessage));
    CHECK(pruned.dropped == listed.dropped);
    CHECK(readText(root / "ids.lock.yml").find("evt:gone") == std::string::npos);
    CHECK(readText(root / "ids.lock.yml").find("evt:hello: 1") != std::string::npos);
    CHECK(pruned.lockHashAfter != pruned.lockHashBefore);
    CHECK(readText(root / ".oymap" / "lock.log").find("\"by\":\"prune\"") != std::string::npos);
    // Never a history entry, and the revision stays.
    CHECK(statusOf(root).history.empty());
    CHECK(statusOf(root).revision == status.revision);

    // An outdoor project keeps every entry.
    writeText(root / "sketch.yml", "format: 0\n");
    LockPruneResult outdoor;
    REQUIRE(pruneProjectLock(root, false, outdoor, errorMessage));
    CHECK(outdoor.dropped.empty());
    CHECK(outdoor.note.find("outdoor") != std::string::npos);
    std::filesystem::remove_all(root);
}

TEST_CASE("S5a1: a map with more than 75 variables names the variables the lock keeps for removed ones, and the prune")
{
    std::string wiring = "format: 0\nvariables: [";
    std::string lock = "format: 0\nmap_vars:\n";

    for (int index = 0; index < 75; ++index)
    {
        wiring += std::string(index == 0 ? "" : ", ") + "v" + std::to_string(index);
        // The lock holds the 75 numbers: 74 for live variables, one for a variable renamed away.
        lock += "  " + (index == 3 ? std::string("old_name") : "v" + std::to_string(index)) + ": "
            + std::to_string(index) + "\n";
    }

    wiring += "]\nevents:\n  - {id: evt:set, preset: script, trigger: load, lua: \"evt.Set(MapVar(v3), 1)\"}\n";
    Project project;

    for (const std::pair<std::string, std::string> &file : std::vector<std::pair<std::string, std::string>>{
             {"project.yml", CardText}, {"rooms.yml", RoomsText}, {"objects.yml", "format: 0\nstart: {room: room:a}\n"},
             {"wiring.yml", wiring}, {"ids.lock.yml", lock}})
    {
        ProjectFile entry;
        entry.name = file.first;
        entry.text = file.second;
        entry.document = YAML::Load(file.second);
        project.files[entry.name] = entry;
    }

    std::vector<ProjectIssue> issues;
    LoweredIndoorMap lowered;
    lowerIndoorProject(project, {}, lowered, issues);
    const bool named = std::any_of(issues.begin(), issues.end(), [](const ProjectIssue &issue)
    {
        return issue.message.find("more than 75 variables") != std::string::npos
            && issue.message.find("old_name 3") != std::string::npos
            && issue.message.find("oymap lock prune") != std::string::npos;
    });
    CHECK(named);
}

TEST_CASE("S5a1: pins format 1: add, claim, resolve with a picture, accept, reopen and decline, each counted and logged")
{
    const std::filesystem::path root = writeProject("pins");
    writeText(root / "plan.yml", "format: 0\nspaces:\n  - {id: room:a, name: A, kind: room, size: S}\n");
    const std::string revision = statusOf(root).revision;

    NewPin pin;
    pin.text = "The gate reads as a wall.";
    pin.on = "door:ab";
    pin.position = std::vector<double>{256.5, 128.25, 0};
    pin.yawRadians = 1.5708;
    pin.pitchDegrees = -3;
    PinResult result;
    REQUIRE(addPin(root, pin, result));
    CHECK(result.pin["id"].Scalar() == "pin:p1");
    CHECK(result.pin["status"].Scalar() == "open");
    CHECK(result.pin["revision"].Scalar() == revision);
    CHECK(result.pin["pose"]["position"][0].Scalar() == "256.5");
    CHECK(result.pin["author"].Scalar() == "agent");
    CHECK(result.counter == 1);

    // `on` must name a top-level id the project has, with its file where two files share it; no keyed parts yet.
    NewPin wrong;
    wrong.text = "x";
    wrong.on = "door:none";
    CHECK_FALSE(addPin(root, wrong, result));
    CHECK(result.refusal == PinRefusal::BadRequest);
    wrong.on = "room:a";
    CHECK_FALSE(addPin(root, wrong, result));
    CHECK(result.message.find("name the one meant with `file`") != std::string::npos);
    wrong.file = "rooms.yml";
    REQUIRE(addPin(root, wrong, result));
    CHECK(result.pin["file"].Scalar() == "rooms.yml");
    CHECK(result.pin["id"].Scalar() == "pin:p2");
    wrong.on = "thing:building_2/parts/p3";
    CHECK_FALSE(addPin(root, wrong, result));
    CHECK(result.message.find("nothing in the project has the sub-object") != std::string::npos);

    REQUIRE(claimPin(root, "pin:p1", "agent:fixer", false, result));
    CHECK(result.pin["status"].Scalar() == "claimed");
    CHECK(result.pin["claimed_by"].Scalar() == "agent:fixer");
    CHECK_FALSE(claimPin(root, "pin:p1", "agent:other", false, result));
    CHECK(result.refusal == PinRefusal::WrongState);
    CHECK_FALSE(actOnPin(root, "pin:p1", PinAction::Resolve, "agent:other", "done", {}, result));
    CHECK(result.refusal == PinRefusal::WrongState);
    CHECK_FALSE(actOnPin(root, "pin:p1", PinAction::Accept, "user", "", {}, result));
    CHECK(result.refusal == PinRefusal::WrongState);
    CHECK_FALSE(claimPin(root, "pin:p9", "agent:fixer", false, result));
    CHECK(result.refusal == PinRefusal::NoSuchPin);

    // The fix is an edit of the source; then the reply carries the revision after it and the game's picture.
    TransactionResult edit;
    REQUIRE(applyTransaction(root, YAML::Load("[{op: set, id: door:ab, fields: {speed: 64}}]"), {}, edit));
    const std::filesystem::path after = root / "after.png";
    writePicture(after, "after");
    REQUIRE(actOnPin(root, "pin:p1", PinAction::Resolve, "agent:fixer", "Framed the gate.", {after}, result));
    CHECK(result.pin["status"].Scalar() == "resolved");
    REQUIRE(result.pin["replies"].size() == 1);
    CHECK(result.pin["replies"][0]["revision"].Scalar() == edit.revisionAfter);
    CHECK(result.pin["replies"][0]["status"].Scalar() == "resolved");
    CHECK(result.pin["replies"][0]["pictures"][0].Scalar() == ".oymap/pins/pictures/p1-r1.png");
    CHECK(readText(root / ".oymap" / "pins" / "pictures" / "p1-r1.png") == readText(after));

    REQUIRE(actOnPin(root, "pin:p1", PinAction::Reopen, "user", "Still flickers.", {}, result));
    CHECK(result.pin["status"].Scalar() == "open");
    CHECK_FALSE(result.pin["claimed_by"].IsDefined());
    REQUIRE(actOnPin(root, "pin:p1", PinAction::Resolve, "agent:fixer", "Moved the leaf.", {}, result));
    REQUIRE(actOnPin(root, "pin:p1", PinAction::Accept, "user", "", {}, result));
    CHECK(result.pin["status"].Scalar() == "accepted");
    CHECK_FALSE(actOnPin(root, "pin:p2", PinAction::Decline, "agent:fixer", "", {}, result));
    REQUIRE(actOnPin(root, "pin:p2", PinAction::Decline, "agent:fixer", "The room is as the original's.", {},
        result));
    CHECK(result.pin["status"].Scalar() == "declined");

    // Eight changes: two adds, a claim, resolve, reopen, resolve, accept, decline; each a log line (the refused
    // ones are neither counted nor logged). The source revision moved only with the edit.
    YAML::Node document;
    std::string errorMessage;
    REQUIRE(readPinsDocument(root, document, errorMessage));
    CHECK(document["counter"].as<int>() == 8);
    CHECK(lineCount(readText(root / ".oymap" / "pins" / "log.jsonl")) == 8);
    CHECK(statusOf(root).revision == edit.revisionAfter);
    CHECK(statusOf(root).history.size() == 1);
    CHECK(pinsWithStatus(document, "accepted").size() == 1);
    CHECK(pinsWithStatus(document, "").size() == 2);
    // The document is canonical and valid; the project validates with it.
    CHECK(SchemaSet::builtIn().validate(YAML::LoadFile((root / "review" / "pins.yml").string()), "pins.schema.json")
        .empty());

    // Keeping a picture copies it into review/pictures/, which travels with git.
    writePicture(root / "before.png", "before");
    NewPin pictured;
    pictured.text = "Dark corner.";
    pictured.at = std::vector<double>{100, 200, 0};
    pictured.picture = root / "before.png";
    REQUIRE(addPin(root, pictured, result));
    CHECK(result.pin["picture"].Scalar() == ".oymap/pins/pictures/p3.png");
    REQUIRE(keepPinPicture(root, "pin:p3", result));
    CHECK(result.pin["keep"].as<bool>());
    CHECK(readText(root / "review" / "pictures" / "p3.png") == readText(root / "before.png"));
    std::filesystem::remove_all(root);
}

TEST_CASE("S5a1: a pins document of format 0 is read as format 1 and written as format 1 on its next change")
{
    const std::filesystem::path root = writeProject("format0");
    writeText(root / "review" / "pins.yml",
        "format: 0\npins:\n  - {id: pin:gate, text: Too slow., on: door:ab, status: resolved, author: user,\n"
        "     reply: Faster now., revision: \"0123456789ab\"}\n");
    YAML::Node document;
    std::string errorMessage;
    REQUIRE(readPinsDocument(root, document, errorMessage));
    CHECK(document["format"].as<int>() == 1);
    CHECK(document["pins"][0]["replies"][0]["text"].Scalar() == "Faster now.");
    CHECK(document["pins"][0]["replies"][0]["status"].Scalar() == "resolved");
    CHECK_FALSE(document["pins"][0]["reply"].IsDefined());
    // The project validates with it as it is on disk.
    Project project;
    std::vector<ProjectIssue> issues;
    REQUIRE(loadProject(root, project, issues));
    validateProjectSchemas(project, issues);
    CHECK(issues.empty());
    PinResult result;
    REQUIRE(actOnPin(root, "pin:gate", PinAction::Accept, "user", "", {}, result));
    const std::string written = readText(root / "review" / "pins.yml");
    CHECK(written.find("format: 1") == 0);
    CHECK(written.find("counter: 1") != std::string::npos);
    CHECK(written.find("reply:") == std::string::npos);
    std::filesystem::remove_all(root);
}

TEST_CASE("S5a1: the game's inbox is filed by the studio file's project, else by the map; the rest stays")
{
    const std::filesystem::path root = writeProject("inbox_project");
    const std::filesystem::path other = writeProject("inbox_other");
    writeText(other / "project.yml", "format: 0\nid: othermap\nworld: mm6\nkind: indoor\n");
    const std::filesystem::path inbox = scratchFolder("inbox");
    const auto pinFile = [](const std::string &text, const std::string &map, const std::string &picture,
                             const std::string &project)
    {
        return "format: 1\nsource: game\nauthor: user\ncreated: \"2026-11-14T19:00:00\"\ntext: \"" + text + "\"\n"
            "world: \"mm6\"\nmap: \"" + map + "\"\npose:\n  position: [1024.000, 256.500, 0.000]\n"
            "  yaw_radians: 1.571\n  pitch_degrees: -3.000\n  heading_yaw_units: 512\npicture: \"" + picture + "\"\n"
            + (project.empty() ? std::string() : "project: \"" + project + "\"\nrevision: \"abcdef0123456789"
                "abcdef0123456789\"\nlock_hash: \"none\"\n");
    };
    writeText(inbox / "20261114-190000-testmap.yml",
        pinFile("The gate flickers.", "testmap.blv", "20261114-190000-testmap.png", root.string()));
    writePicture(inbox / "20261114-190000-testmap.png", "one");
    writeText(inbox / "20261114-190100-othermap.yml",
        pinFile("Too dark here.", "othermap.blv", "20261114-190100-othermap.png", ""));
    writePicture(inbox / "20261114-190100-othermap.png", "two");
    writeText(inbox / "20261114-190200-6d01.yml", pinFile("A shipped map.", "6d01.blv", "20261114-190200-6d01.png",
        ""));
    writePicture(inbox / "20261114-190200-6d01.png", "three");
    // Written a moment ago, its picture not yet: it waits.
    writeText(inbox / "20261114-190300-testmap.yml",
        pinFile("Just now.", "testmap.blv", "20261114-190300-testmap.png", root.string()));
    writeText(inbox / "notes.txt", "not a pin");

    InboxOptions options;
    options.projects = {root.string(), other.string()};
    InboxResult dry;
    std::string errorMessage;
    options.dryRun = true;
    REQUIRE(importPinInbox(inbox, options, dry, errorMessage));
    CHECK(dry.imported.size() == 2);
    CHECK(std::filesystem::exists(inbox / "20261114-190000-testmap.yml"));

    options.dryRun = false;
    InboxResult result;
    REQUIRE(importPinInbox(inbox, options, result, errorMessage));
    REQUIRE(result.imported.size() == 2);
    CHECK(result.imported[0].file == "20261114-190000-testmap.yml");
    CHECK(result.imported[0].matchedBy == "studio file");
    CHECK(result.imported[0].pin == "pin:p1");
    CHECK(result.imported[1].matchedBy == "map");
    CHECK(result.imported[1].project == other.string());
    REQUIRE(result.skipped.size() == 2);
    CHECK(result.skipped[0].reason.find("no project builds or overlays 6d01.blv") != std::string::npos);
    CHECK(result.skipped[1].reason.find("waiting for its picture") != std::string::npos);

    // The pin as filed: the game's pose, text, map and the revision of the build the map was installed from.
    YAML::Node document;
    REQUIRE(readPinsDocument(root, document, errorMessage));
    REQUIRE(document["pins"].size() == 1);
    const YAML::Node filed = document["pins"][0];
    CHECK(filed["source"].Scalar() == "game");
    CHECK(filed["author"].Scalar() == "user");
    CHECK(filed["map"].Scalar() == "testmap.blv");
    CHECK(filed["pose"]["position"][1].Scalar() == "256.5");
    CHECK(filed["pose"]["heading_yaw_units"].as<int>() == 512);
    CHECK(filed["revision"].Scalar() == "abcdef0123456789abcdef0123456789");
    CHECK(filed["created"].Scalar() == "2026-11-14T19:00:00");
    CHECK(filed["from"].Scalar() == "20261114-190000-testmap.yml");
    CHECK(filed["picture"].Scalar() == ".oymap/pins/pictures/p1.png");
    CHECK(readText(root / ".oymap" / "pins" / "pictures" / "p1.png").find("one") != std::string::npos);
    CHECK_FALSE(std::filesystem::exists(inbox / "20261114-190000-testmap.png"));
    CHECK(std::filesystem::exists(inbox / "imported" / "20261114-190000-testmap.yml"));
    // A pin matched by its map has no revision of its own: nothing said what the map was built from.
    YAML::Node otherDocument;
    REQUIRE(readPinsDocument(other, otherDocument, errorMessage));
    CHECK_FALSE(otherDocument["pins"][0]["revision"].IsDefined());

    // Two projects of the same map: the pin waits for --project.
    const std::filesystem::path twin = writeProject("inbox_twin");
    writeText(twin / "project.yml", "format: 0\nid: othermap\nworld: mm6\nkind: indoor\n");
    writeText(inbox / "20261114-190400-othermap.yml",
        pinFile("Which one?", "othermap.blv", "20261114-190400-othermap.png", ""));
    writePicture(inbox / "20261114-190400-othermap.png", "four");
    options.projects = {root.string(), other.string(), twin.string()};
    InboxResult ambiguous;
    REQUIRE(importPinInbox(inbox, options, ambiguous, errorMessage));
    CHECK(ambiguous.imported.empty());
    CHECK(std::any_of(ambiguous.skipped.begin(), ambiguous.skipped.end(), [](const InboxSkipped &skipped)
    {
        return skipped.reason.find("several projects build othermap.blv") != std::string::npos;
    }));

    // The request list's import takes only the projects it is given, not a path a pin names.
    options.projects = {other.string()};
    options.trustPinProject = false;
    writePicture(inbox / "20261114-190300-testmap.png", "late");
    InboxResult jailed;
    REQUIRE(importPinInbox(inbox, options, jailed, errorMessage));
    CHECK(std::any_of(jailed.skipped.begin(), jailed.skipped.end(), [](const InboxSkipped &skipped)
    {
        return skipped.reason.find("not one of the projects given") != std::string::npos;
    }));

    CHECK(findProjects(root.parent_path() / root.filename(), 0) == std::vector<std::filesystem::path>{root});
    for (const std::filesystem::path &folder : {root, other, twin, inbox})
    {
        std::filesystem::remove_all(folder);
    }
}

TEST_CASE("S5a1: a tour at the pins' poses takes the game's pitch in radians and skips pins without a pose")
{
    const YAML::Node document = YAML::Load(
        "format: 1\ncounter: 3\npins:\n"
        "  - {id: pin:p1, text: a, status: resolved, pose: {position: [10, 20, 30], yaw_radians: 1.5, "
        "pitch_degrees: -3}}\n"
        "  - {id: pin:p2, text: b, at: [1, 2, 3]}\n"
        "  - {id: pin:p3, text: c, status: accepted, pose: {position: [1, 1, 1]}}\n");
    std::vector<std::string> skipped;
    const YAML::Node tour = YAML::Load(pinsTourText(document, {}, {"open", "resolved"}, "/shots", skipped));
    REQUIRE(tour["shots"].size() == 1);
    CHECK(tour["shots"][0]["name"].Scalar() == "p1");
    CHECK(tour["shots"][0]["position"][2].as<double>() == 30);
    CHECK(tour["shots"][0]["yaw"].as<double>() == 1.5);
    CHECK(tour["shots"][0]["pitch"].as<double>() == doctest::Approx(-0.05236).epsilon(0.0001));
    CHECK(tour["exit"].as<bool>());
    CHECK(tour["output_dir"].Scalar() == "/shots");
    CHECK(skipped == std::vector<std::string>{"pin:p2"});
    skipped.clear();
    CHECK(YAML::Load(pinsTourText(document, {"pin:p3"}, {}, "/shots", skipped))["shots"].size() == 1);
}

TEST_CASE("S5a1: oymap record attributes the unattributed outside entries since that author's last entry")
{
    const std::filesystem::path root = writeProject("record");
    statusOf(root);
    const auto editOutside = [&root](const std::string &from, const std::string &to)
    {
        std::string objects = readText(root / "objects.yml");
        REQUIRE(objects.find(from) != std::string::npos);
        objects.replace(objects.find(from), from.size(), to);
        writeText(root / "objects.yml", objects);
    };

    // A generator ran: the watcher (any read) records it as `outside` first; record finds it and names it.
    editOutside("speed: 96", "speed: 100");
    statusOf(root);
    RecordResult recorded;
    std::string errorMessage;
    REQUIRE(recordOutsideEdits(root, "agent:gen", "generator run 1", recorded, errorMessage));
    REQUIRE(recorded.taken.size() == 1);
    CHECK(recorded.taken[0].sequence == 1);
    CHECK(hasLine(recorded.taken[0].changes, "door:ab changed speed"));

    // The change on disk now is recorded by the call itself.
    editOutside("speed: 100", "speed: 110");
    REQUIRE(recordOutsideEdits(root, "agent:gen", "generator run 2", recorded, errorMessage));
    REQUIRE(recorded.taken.size() == 1);
    CHECK(recorded.taken[0].sequence == 2);

    // Another tool's edit, then the generator's own transaction, then an outside edit: only the last is taken,
    // the one before the author's transaction stays unattributed.
    editOutside("speed: 110", "speed: 120");
    statusOf(root);
    TransactionOptions options;
    options.author = "agent:gen";
    TransactionResult transaction;
    REQUIRE(applyTransaction(root, YAML::Load("[{op: set, id: door:ab, fields: {speed: 130}}]"), options, transaction));
    editOutside("speed: 130", "speed: 140");
    REQUIRE(recordOutsideEdits(root, "agent:gen", "generator run 3", recorded, errorMessage));
    REQUIRE(recorded.taken.size() == 1);
    CHECK(recorded.taken[0].sequence == 5);
    const ProjectStatus status = statusOf(root);
    REQUIRE(status.history.size() == 5);
    CHECK(status.history[0].author == "agent:gen");
    CHECK(status.history[0].label == "generator run 1");
    CHECK(status.history[2].author == "outside");
    CHECK(status.history[3].kind == "transaction");
    CHECK(status.history[4].label == "generator run 3");
    // What an entry changed is never touched.
    CHECK(status.history[4].changes == recorded.taken[0].changes);
    CHECK_FALSE(recordOutsideEdits(root, "outside", "", recorded, errorMessage));
    std::filesystem::remove_all(root);
}

TEST_CASE("S5a1: every install route writes <stem>.studio.yml with the project, the build's revision and lock hash")
{
    const std::filesystem::path root = writeProject("install");
    const std::filesystem::path build = scratchFolder("install_build");
    const std::filesystem::path assets = scratchFolder("install_assets");
    const std::filesystem::path mount = scratchFolder("install_mount");
    writeText(build / "testmap.blv", "blv");
    writeText(build / "testmap.scene.yml", "scene");
    writeText(build / "testmap.lua", "lua");
    writeText(build / "build.json", "{\"ok\": true, \"map\": \"testmap.blv\", \"source_revision\": "
        "\"0123456789abcdef0123456789abcdef\", \"lock_hash\": \"none\"}\n");
    writeText(assets / "engine" / "data_tables" / "map_stats.txt", "header\n");
    std::filesystem::create_directories(assets / "worlds" / "mm6");
    Project project;
    std::vector<ProjectIssue> issues;
    REQUIRE(loadProject(root, project, issues));

    std::vector<std::string> installed;
    std::string errorMessage;
    REQUIRE(installBuild(project, build, assets, installed, errorMessage, true));
    CHECK(std::find(installed.begin(), installed.end(), "worlds/mm6/maps/testmap.studio.yml") != installed.end());
    const YAML::Node rooted = YAML::LoadFile((assets / "worlds" / "mm6" / "maps" / "testmap.studio.yml").string());
    CHECK(rooted["project"].Scalar() == std::filesystem::weakly_canonical(root).generic_string());
    CHECK(rooted["revision"].Scalar() == "0123456789abcdef0123456789abcdef");
    CHECK(rooted["lock_hash"].Scalar() == "none");

    REQUIRE(installBuildIntoMount(project, build, mount, assets, installed, errorMessage, true));
    const YAML::Node mounted = YAML::LoadFile((mount / "worlds" / "mm6" / "maps" / "testmap.studio.yml").string());
    CHECK(mounted["revision"].Scalar() == "0123456789abcdef0123456789abcdef");

    // A build made before builds recorded their revision: the project's as it is now.
    writeText(build / "build.json", "{\"ok\": true, \"map\": \"testmap.blv\"}\n");
    REQUIRE(installBuildIntoMount(project, build, mount, assets, installed, errorMessage, true));
    CHECK(YAML::LoadFile((mount / "worlds" / "mm6" / "maps" / "testmap.studio.yml").string())["revision"].Scalar()
        == projectRevision(project));

    for (const std::filesystem::path &folder : {root, build, assets, mount})
    {
        std::filesystem::remove_all(folder);
    }
}

TEST_CASE("S5a1: patch changes part of an object, and a failing step names its operation and step")
{
    const std::filesystem::path root = writeProject("patch");
    TransactionResult result;
    REQUIRE(applyTransaction(root, YAML::Load("[{op: patch, id: room:a, patch: [{op: test, path: /ceiling, value: 384},"
        " {op: replace, path: /ceiling, value: 400}]}]"), {}, result));
    CHECK(readText(root / "rooms.yml").find("ceiling: 400") != std::string::npos);
    TransactionResult refused;
    CHECK_FALSE(applyTransaction(root, YAML::Load("[{op: set, id: door:ab, fields: {speed: 1}}, {op: patch, id: room:a, "
        "patch: [{op: replace, path: /floor, value: 8}, {op: test, path: /ceiling, value: 1}]}]"), {}, refused));
    CHECK(refused.refusal == TransactionRefusal::BadOperation);
    CHECK(refused.failedOperation == 1);
    CHECK(refused.failedStep == 1);
    CHECK_FALSE(applyTransaction(root, YAML::Load("[{op: patch, file: ids.lock.yml, patch: [{op: add, path: /x, "
        "value: 1}]}]"), {}, refused));
    std::filesystem::remove_all(root);
}
