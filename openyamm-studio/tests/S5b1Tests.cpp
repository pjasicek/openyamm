// S5b1, the core of indoor authoring (devdocs/map_studio/S5_BROWSER_EDITOR.md 6.4): keys of format 1 and keyed
// patches, ids given by the core, rename (references, the lock and the pins follow; its undo is the opposite rename),
// the append-only history (undo, redo and revert as entries, object by object; the snapshot restore as the oracle),
// merging of repeated edits, rebase, two writers, and the hand-edit mark.
#include "doctest/doctest.h"

#include "core/CanonicalYaml.h"
#include "core/History.h"
#include "core/IndoorBuild.h"
#include "core/Keys.h"
#include "core/Ops.h"
#include "core/Pins.h"
#include "core/Project.h"

#include <algorithm>
#include <filesystem>
#include <fstream>
#include <random>

using namespace OpenYAMM::Studio;

namespace
{
const char *CardText = "format: 0\nid: keymap\nworld: mm6\nkind: indoor\n";
const char *RoomsText =
    "format: 0\n"
    "themes:\n"
    "  - id: theme:plain\n"
    "    wall: {texture: wall, size: [128, 128]}\n"
    "    floor: {texture: floor, size: [128, 128]}\n"
    "    ceiling: {texture: ceil, size: [128, 128]}\n"
    "defaults: {theme: theme:plain}\n"
    "rooms:\n"
    "  - id: room:a\n"
    "    outline: [[0, 0], [1024, 0], [1024, 1024], [0, 1024]]\n"
    "    floor: 0\n"
    "    ceiling: 512\n"
    "    pillars:\n"
    "      - {at: [256, 256], size: [64, 64]}\n"
    "      - {at: [768, 256], size: [64, 64]}\n"
    "    platforms:\n"
    "      - {at: [512, 768], size: [256, 128], rise: 32}\n"
    "  - {id: room:b, outline: [[1088, 0], [1600, 0], [1600, 512], [1088, 512]], floor: 0, ceiling: 384}\n"
    "openings:\n"
    "  - {id: open:ab, from: room:a, to: room:b, width: 128, height: 256}\n";
const char *ObjectsText =
    "format: 0\nstart: {room: room:a}\ndoors:\n  - {id: door:ab, opening: open:ab, speed: 96}\n"
    "lights:\n  - {id: light:a, room: room:a, offset: [0, 0], radius: 512}\n";
const char *WiringText =
    "format: 0\nevents:\n  - {id: evt:open_ab, preset: door, source: door:ab, opens: [door:ab]}\n";

std::filesystem::path scratchFolder(const std::string &name)
{
    const std::filesystem::path root = std::filesystem::temp_directory_path()
        / ("oymap_s5b1_" + name + "_" + std::to_string(std::random_device{}()));
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
    writeText(root / "objects.yml", ObjectsText);
    writeText(root / "wiring.yml", WiringText);
    return root;
}

// Every source file's bytes, by name.
std::map<std::string, std::string> sourceBytes(const std::filesystem::path &root)
{
    std::map<std::string, std::string> bytes;

    for (const char *pName : {"project.yml", "rooms.yml", "objects.yml", "wiring.yml", "plan.yml"})
    {
        if (std::filesystem::exists(root / pName))
        {
            bytes[pName] = readText(root / pName);
        }
    }

    return bytes;
}

TransactionResult edit(const std::filesystem::path &root, const std::string &operations,
    const std::string &author = "agent:test", bool allowErrors = true)
{
    TransactionOptions options;
    options.author = author;
    options.allowNewIssues = allowErrors;
    TransactionResult result;
    INFO(operations);
    const bool ok = applyTransaction(root, YAML::Load(operations), options, result);
    const std::string firstError = result.errors.empty() ? std::string() : result.errors.front();
    INFO(firstError);
    CHECK(ok);
    return result;
}

TransactionResult revert(const std::filesystem::path &root, RevertKind kind, const std::string &author,
    int sequence = 0, bool force = false)
{
    RevertRequest request;
    request.kind = kind;
    request.sequence = sequence;
    request.force = force;
    TransactionOptions options;
    options.author = author;
    options.allowNewIssues = true;
    TransactionResult result;
    revertProject(root, request, options, result);
    return result;
}

ProjectStatus statusOf(const std::filesystem::path &root)
{
    ProjectStatus status;
    std::string errorMessage;
    REQUIRE(projectStatus(root, status, errorMessage));
    return status;
}

bool hasLine(const std::vector<std::string> &lines, const std::string &fragment)
{
    return std::any_of(lines.begin(), lines.end(), [&fragment](const std::string &line)
    {
        return line.find(fragment) != std::string::npos;
    });
}
}

TEST_CASE("S5b1: keys of format 1: derived where not written, patched by key, written on the core's next write")
{
    const std::filesystem::path root = writeProject("keys");
    Project project;
    std::vector<ProjectIssue> issues;
    REQUIRE(loadProject(root, project, issues));
    const std::vector<std::string> addresses = subObjectAddresses(project.document("rooms.yml"), "rooms.schema.json");
    CHECK(std::find(addresses.begin(), addresses.end(), "room:a/pillars/pillar2") != addresses.end());
    CHECK(std::find(addresses.begin(), addresses.end(), "room:a/platforms/platform1") != addresses.end());
    CHECK(writtenKeyAddresses(project.document("rooms.yml"), "rooms.schema.json").empty());
    CHECK(fileHasKeyedLists("rooms.schema.json"));
    CHECK(fileHasKeyedLists("objects.schema.json"));
    CHECK_FALSE(fileHasKeyedLists("wiring.schema.json"));

    // A patch addresses the second pillar by its key, though no key is written yet; the write fills them all.
    const TransactionResult moved = edit(root, "[{op: patch, id: room:a, patch: [{op: test, path: /pillars/pillar2/at, "
        "value: [768, 256]}, {op: replace, path: /pillars/pillar2/at, value: [768, 320]}]}]");
    CHECK(moved.applied);
    CHECK(hasLine(moved.keysAllocated, "pillar2"));
    CHECK(hasLine(moved.changes, "keys written for 3 sub-object(s) (format 1)"));
    const std::string rooms = readText(root / "rooms.yml");
    CHECK(rooms.find("format: 1") != std::string::npos);
    CHECK(rooms.find("{key: pillar2, at: [768, 320]") != std::string::npos);
    // Files the transaction did not touch keep their bytes and format.
    CHECK(readText(root / "objects.yml") == ObjectsText);

    // Inserting before it does not move the address: keys are written now.
    edit(root, "[{op: patch, id: room:a, patch: [{op: add, path: /pillars/0, value: {at: [100, 100], size: [32, 32]}}]}]");
    edit(root, "[{op: patch, id: room:a, patch: [{op: replace, path: /pillars/pillar2/size, value: [80, 80]}]}]");
    CHECK(readText(root / "rooms.yml").find("{key: pillar2, at: [768, 320], size: [80, 80]}") != std::string::npos);
    // The new pillar got the next free key; a key is changed by rename, never by a patch.
    CHECK(readText(root / "rooms.yml").find("{key: pillar3, at: [100, 100]") != std::string::npos);
    TransactionOptions options;
    TransactionResult refused;
    CHECK_FALSE(applyTransaction(root, YAML::Load("[{op: patch, id: room:a, patch: [{op: replace, path: "
        "/pillars/pillar2/key, value: big}]}]"), options, refused));
    CHECK(refused.errors.front().find("op rename") != std::string::npos);
    CHECK_FALSE(applyTransaction(root, YAML::Load("[{op: patch, id: room:a, patch: [{op: add, path: /pillars/-, "
        "value: {key: pillar2, at: [10, 10], size: [8, 8]}}]}]"), options, refused));
    CHECK(refused.errors.front().find("already used") != std::string::npos);
    std::filesystem::remove_all(root);
}

TEST_CASE("S5b1: the core gives ids to added objects, named after the room they stand in")
{
    const std::filesystem::path root = writeProject("ids");
    const TransactionResult first = edit(root, "[{op: add, to: lights, value: {room: room:b, offset: [0, 0]}},"
        "{op: add, to: lights, value: {room: room:b, offset: [64, 0]}}, {op: add, to: switches, value: {wall: [room:a, 0], "
        "along: 0.5}}]");
    REQUIRE(first.idsAllocated.size() == 3);
    CHECK(first.idsAllocated[0] == "objects.yml#light:b_1");
    CHECK(first.idsAllocated[1] == "objects.yml#light:b_2");
    CHECK(first.idsAllocated[2] == "objects.yml#switch:switch_1");
    CHECK(readText(root / "objects.yml").find("id: light:b_2") != std::string::npos);
    std::filesystem::remove_all(root);
}

TEST_CASE("S5b1: rename changes every reference; the lock keeps the number under the new name and the pins follow; "
          "its undo is the opposite rename")
{
    const std::filesystem::path root = writeProject("rename");
    writeText(root / "ids.lock.yml", "format: 0\ndoors: {door:ab: 7, door:ab.leaf2: 8}\nevents: {evt:open_ab: 3}\n");
    NewPin pin;
    pin.text = "too slow";
    pin.on = "door:ab";
    PinResult pinned;
    REQUIRE(addPin(root, pin, pinned));
    pin.on = "room:a/pillars/pillar1";
    pin.text = "too thin";
    REQUIRE(addPin(root, pin, pinned));

    const TransactionResult renamed = edit(root, "[{op: rename, from: door:ab, to: door:gate}]", "user");
    CHECK(renamed.applied);
    CHECK(readText(root / "objects.yml").find("door:gate") != std::string::npos);
    CHECK(readText(root / "wiring.yml").find("source: door:gate") != std::string::npos);
    CHECK(readText(root / "wiring.yml").find("opens: [door:gate]") != std::string::npos);
    CHECK(readText(root / "ids.lock.yml").find("door:gate: 7") != std::string::npos);
    CHECK(readText(root / "ids.lock.yml").find("door:gate.leaf2: 8") != std::string::npos);
    CHECK(readText(root / "review/pins.yml").find("on: door:gate") != std::string::npos);
    CHECK(hasLine(renamed.notes, "doors: door:ab -> door:gate 7"));

    // A key renamed: the pin on it follows.
    edit(root, "[{op: rename, id: room:a, path: /pillars/pillar1, to: big}]", "user");
    CHECK(readText(root / "rooms.yml").find("{key: big, at: [256, 256]") != std::string::npos);
    CHECK(readText(root / "review/pins.yml").find("on: room:a/pillars/big") != std::string::npos);

    // Undo runs the opposite renames, newest first: the key, then the id; the numbers stay.
    TransactionResult undone = revert(root, RevertKind::Undo, "user");
    CHECK(undone.applied);
    CHECK(readText(root / "review/pins.yml").find("on: room:a/pillars/pillar1") != std::string::npos);
    undone = revert(root, RevertKind::Undo, "user");
    CHECK(undone.applied);
    CHECK(readText(root / "objects.yml").find("door:ab") != std::string::npos);
    CHECK(readText(root / "wiring.yml").find("source: door:ab") != std::string::npos);
    CHECK(readText(root / "ids.lock.yml").find("door:ab: 7") != std::string::npos);
    CHECK(readText(root / "ids.lock.yml").find("door:ab.leaf2: 8") != std::string::npos);
    CHECK(readText(root / "review/pins.yml").find("on: door:ab") != std::string::npos);
    // Redo renames again.
    CHECK(revert(root, RevertKind::Redo, "user").applied);
    CHECK(readText(root / "ids.lock.yml").find("door:gate: 7") != std::string::npos);
    std::filesystem::remove_all(root);
}

TEST_CASE("S5b1: reverting the latest entry gives the bytes the snapshot restore gives, for every kind of operation")
{
    const std::vector<std::string> operations = {
        "[{op: add, to: lights, value: {id: light:new, room: room:b, offset: [0, 0]}}]",
        "[{op: add, to: lights, value: {room: room:b, offset: [0, 0]}}]",
        "[{op: set, id: door:ab, fields: {speed: 64, notes: slower}}]",
        "[{op: replace, id: light:a, value: {room: room:a, offset: [32, 32], radius: 800}}]",
        "[{op: remove, id: light:a}]",
        "[{op: set_value, file: project.yml, path: map_stats.treasure_level, value: 2}]",
        "[{op: patch, id: room:a, patch: [{op: replace, path: /outline/1, value: [1040, 0]}]}]",
        "[{op: patch, id: room:a, patch: [{op: remove, path: /pillars/pillar1}]}]",
        "[{op: patch, file: rooms.yml, patch: [{op: replace, path: /defaults/theme, value: theme:plain}, "
        "{op: add, path: /notes, value: a note}]}]",
        "[{op: rename, from: light:a, to: light:hall}]",
        "[{op: rename, id: room:a, path: /platforms/platform1, to: dais}]",
        "[{op: replace_file, file: wiring.yml, text: \"format: 0\\nevents: []\\n\"}]",
        "[{op: add, to: spaces, value: {id: room:a, name: The hall}}]",
    };

    for (const std::string &text : operations)
    {
        INFO(text);

        for (const char *pAuthor : {"agent:test", "user"})
        {
            const std::filesystem::path root = writeProject("oracle");
            writeText(root / "ids.lock.yml", "format: 0\nevents: {evt:open_ab: 3}\n");
            // A first change, so the files are the core's own (canonical, keyed) before the one checked.
            edit(root, "[{op: set, id: door:ab, fields: {speed: 90}}]", pAuthor);
            const std::map<std::string, std::string> before = sourceBytes(root);
            const TransactionResult done = edit(root, text, pAuthor);
            REQUIRE(done.applied);
            StoredHistoryEntry entry;
            std::string errorMessage;
            REQUIRE(readHistoryEntry(root, done.sequence, true, entry, errorMessage));

            // The snapshot restore: the entry's before texts, the files it did not change as they are.
            std::map<std::string, std::string> snapshot = sourceBytes(root);

            for (const auto &file : entry.before)
            {
                if (file.second)
                {
                    snapshot[file.first] = *file.second;
                }
                else
                {
                    snapshot.erase(file.first);
                }
            }

            const TransactionResult undone = revert(root, RevertKind::Undo, pAuthor);
            CHECK(undone.applied);
            CHECK(undone.conflicts.empty());
            CHECK(sourceBytes(root) == snapshot);
            CHECK(sourceBytes(root) == before);
            // The redo gives the change back, byte for byte.
            const std::map<std::string, std::string> afterChange = [&entry, &root]()
            {
                std::map<std::string, std::string> files = sourceBytes(root);

                for (const auto &file : entry.after)
                {
                    if (file.second)
                    {
                        files[file.first] = *file.second;
                    }
                    else
                    {
                        files.erase(file.first);
                    }
                }

                return files;
            }();
            CHECK(revert(root, RevertKind::Redo, pAuthor).applied);
            CHECK(sourceBytes(root) == afterChange);
            std::filesystem::remove_all(root);
        }
    }
}

TEST_CASE("S5b1: two writers: a person's undo takes the person's change only; a change made since is a conflict")
{
    const std::filesystem::path root = writeProject("writers");
    edit(root, "[{op: set, id: light:a, fields: {radius: 700}}]", "user");
    edit(root, "[{op: set, id: door:ab, fields: {speed: 50}}]", "agent:dress");
    edit(root, "[{op: set, id: room:b, file: rooms.yml, fields: {ceiling: 400}}]", "user");

    // The person's Ctrl Z: room:b's ceiling, not the agent's door.
    TransactionResult undone = revert(root, RevertKind::Undo, "user");
    CHECK(undone.applied);
    CHECK(hasLine(undone.changes, "room:b changed ceiling (400 -> 384)"));
    CHECK(readText(root / "objects.yml").find("speed: 50") != std::string::npos);
    // Again: the light, past the agent's entry.
    undone = revert(root, RevertKind::Undo, "user");
    CHECK(hasLine(undone.changes, "light:a changed radius (700 -> 512)"));
    CHECK(readText(root / "objects.yml").find("speed: 50") != std::string::npos);
    // Redo, in order; a new change of the person's ends the redo chain.
    CHECK(hasLine(revert(root, RevertKind::Redo, "user").changes, "radius (512 -> 700)"));
    edit(root, "[{op: set, id: room:a, file: rooms.yml, fields: {notes: big hall}}]", "user");
    const TransactionResult noRedo = revert(root, RevertKind::Redo, "user");
    CHECK_FALSE(noRedo.applied);
    CHECK(noRedo.refusal == TransactionRefusal::NothingToRevert);

    // The agent changes the light after the person: the person's revert of their light change is a conflict.
    edit(root, "[{op: set, id: light:a, fields: {radius: 900}}]", "agent:dress");
    const ProjectStatus status = statusOf(root);
    int lightEntry = 0;

    for (const HistoryEntry &entry : status.history)
    {
        if (entry.author == "user" && hasLine(entry.changes, "radius (512 -> 700)") && entry.reverts == 0)
        {
            lightEntry = entry.sequence;
        }
    }

    REQUIRE(lightEntry > 0);
    TransactionResult conflicted = revert(root, RevertKind::Revert, "user", lightEntry);
    CHECK(conflicted.conflicts == std::vector<std::string>{"objects.yml#light:a"});
    CHECK(readText(root / "objects.yml").find("radius: 900") != std::string::npos);
    conflicted = revert(root, RevertKind::Revert, "user", lightEntry, true);
    CHECK(readText(root / "objects.yml").find("radius: 512") != std::string::npos);
    std::filesystem::remove_all(root);
}

TEST_CASE("S5b1: an object removed and brought back by a revert takes its old place; the history is append-only")
{
    const std::filesystem::path root = writeProject("place");
    edit(root, "[{op: add, to: lights, value: {id: light:b, room: room:b, offset: [0, 0]}},"
        "{op: add, to: lights, value: {id: light:c, room: room:b, offset: [8, 0]}}]");
    const TransactionResult removed = edit(root, "[{op: remove, id: light:b}]", "user");
    edit(root, "[{op: set, id: light:c, fields: {radius: 300}}]", "agent:other");
    const TransactionResult back = revert(root, RevertKind::Revert, "user", removed.sequence);
    CHECK(back.applied);
    const std::string objects = readText(root / "objects.yml");
    CHECK(objects.find("light:a") < objects.find("light:b"));
    CHECK(objects.find("light:b") < objects.find("light:c"));
    CHECK(objects.find("radius: 300") != std::string::npos);
    const ProjectStatus status = statusOf(root);
    // Nothing was cut off or rewritten: every entry is there, the reverted one marked undone.
    CHECK(status.history.back().reverts == removed.sequence);
    CHECK(status.history.back().revertKind == "revert");
    CHECK(std::any_of(status.history.begin(), status.history.end(), [&removed](const HistoryEntry &entry)
    {
        return entry.sequence == removed.sequence && entry.undone;
    }));
    // Each file version is kept once, compressed.
    CHECK(std::filesystem::exists(root / ".oymap" / "history" / "blobs"));
    std::filesystem::remove_all(root);
}

TEST_CASE("S5b1: repeated edits with a merge key fold into one entry")
{
    const std::filesystem::path root = writeProject("merge");
    TransactionOptions options;
    options.author = "user";
    options.mergeKey = "drag door:ab speed";
    TransactionResult result;

    for (const int speed : {80, 70, 60, 50})
    {
        REQUIRE(applyTransaction(root, YAML::Load("[{op: set, id: door:ab, fields: {speed: " + std::to_string(speed)
            + "}}]"), options, result));
    }

    // The first marked the project (not merged into); the other three folded into one entry.
    const ProjectStatus status = statusOf(root);
    CHECK(status.history.back().merged == 3);
    CHECK(result.merged);
    // One undo takes all three back to the first one's speed.
    CHECK(revert(root, RevertKind::Undo, "user").applied);
    CHECK(readText(root / "objects.yml").find("speed: 80") != std::string::npos);
    std::filesystem::remove_all(root);
}

TEST_CASE("S5b1: a stale change is rebased when nothing it touches changed since, and refused when something did")
{
    const std::filesystem::path root = writeProject("rebase");
    const std::string start = statusOf(root).revision;
    edit(root, "[{op: set, id: door:ab, fields: {speed: 50}}]", "agent:other");
    TransactionOptions options;
    options.author = "user";
    options.expectRevision = start;
    options.rebase = true;
    TransactionResult result;
    CHECK(applyTransaction(root, YAML::Load("[{op: set, id: light:a, fields: {radius: 600}}]"), options, result));
    CHECK(result.rebasedOver.size() == 1);
    CHECK_FALSE(applyTransaction(root, YAML::Load("[{op: set, id: door:ab, fields: {speed: 40}}]"), options, result));
    CHECK(result.refusal == TransactionRefusal::StaleRevision);
    CHECK(result.clashes == std::vector<std::string>{"objects.yml#door:ab"});
    // With a test step that still holds, a clash is applied at the value level.
    CHECK(applyTransaction(root, YAML::Load("[{op: patch, id: door:ab, patch: [{op: test, path: /speed, value: 50}, "
        "{op: replace, path: /speed, value: 40}]}]"), options, result));
    options.rebase = false;
    CHECK_FALSE(applyTransaction(root, YAML::Load("[{op: set, id: light:a, fields: {radius: 1}}]"), options, result));
    CHECK(result.refusal == TransactionRefusal::StaleRevision);
    std::filesystem::remove_all(root);
}

TEST_CASE("S5b1: the hand-edit mark: set by a person's first change, kept by its undo, told to agents, protect and "
          "clear; an outside rewrite of a marked project carries a notice")
{
    const std::filesystem::path root = writeProject("mark");
    const std::string agentsOnly = statusOf(root).revision;
    edit(root, "[{op: set, id: door:ab, fields: {speed: 64}}]", "agent:base");
    CHECK_FALSE(statusOf(root).mark.marked);
    const std::string beforeHand = statusOf(root).revision;
    const TransactionResult first = edit(root, "[{op: set, id: light:a, fields: {radius: 640}}]", "user");
    CHECK(first.mark.setNow);
    CHECK(first.mark.revision == beforeHand);
    CHECK(readText(root / "project.yml").find("edited_by_hand: {since: ") != std::string::npos);
    CHECK(agentsOnly != beforeHand);

    // An agent changing the light is told a person changed it last.
    const TransactionResult agent = edit(root, "[{op: set, id: light:a, fields: {radius: 650}}]", "agent:dress");
    CHECK(agent.mark.marked);
    CHECK(agent.handObjects == std::vector<std::string>{"objects.yml#light:a"});
    const TransactionResult agentDoor = edit(root, "[{op: set, id: door:ab, fields: {speed: 66}}]", "agent:dress");
    CHECK(agentDoor.handObjects.empty());

    // Undoing the person's change keeps the mark.
    edit(root, "[{op: set, id: room:b, file: rooms.yml, fields: {notes: by hand}}]", "user");
    CHECK(revert(root, RevertKind::Undo, "user").applied);
    CHECK(readText(root / "project.yml").find("edited_by_hand") != std::string::npos);

    // A generator rewrites objects.yml from outside: the light a person changed last ... and the notice says so.
    edit(root, "[{op: set, id: light:a, fields: {radius: 641}}]", "user");
    writeText(root / "objects.yml", ObjectsText);
    const ProjectStatus status = statusOf(root);
    REQUIRE(status.outsideNotice.size() == 1);
    CHECK(status.outsideNotice[0].find("objects.yml#light:a") != std::string::npos);
    CHECK(status.outsideNotice[0].find("edit.revert {sequence: " + std::to_string(status.outsideSequence))
        != std::string::npos);
    // The one step back.
    CHECK(revert(root, RevertKind::Revert, "user", status.outsideSequence).applied);
    CHECK(readText(root / "objects.yml").find("radius: 641") != std::string::npos);

    // A person clears the mark, and protects the project again by hand.
    TransactionResult protectedResult;
    REQUIRE(protectProject(root, true, protectedResult));
    CHECK_FALSE(protectedResult.mark.marked);
    CHECK(readText(root / "project.yml").find("edited_by_hand") == std::string::npos);
    REQUIRE(protectProject(root, false, protectedResult));
    CHECK(protectedResult.mark.marked);
    CHECK(protectedResult.mark.historyKnown);
    std::filesystem::remove_all(root);
}

TEST_CASE("S5b1: a history kept as a cursor becomes append-only; blobs hold each version once")
{
    const std::filesystem::path root = writeProject("cursor");
    edit(root, "[{op: set, id: door:ab, fields: {speed: 64}}]");
    HistoryHead head = readHistoryHead(root);
    REQUIRE(head.count == 1);
    // As an older core left it: an entry undone above the cursor.
    writeText(root / ".oymap" / "head.yml", "revision: \"" + head.revision + "\"\nscheme: source-sha256-128\n"
        "cursor: 0\ncount: 1\n");
    const ProjectStatus status = statusOf(root);
    CHECK(status.history.empty());
    CHECK(readText(root / ".oymap" / "migrations.log").find("append-only") != std::string::npos);
    CHECK(compressText("") .size() > 0);
    std::string text;
    CHECK(decompressText(compressText("abc abc abc"), text));
    CHECK(text == "abc abc abc");
    std::filesystem::remove_all(root);
}

TEST_CASE("S5b1: the lowering skips a room it cannot lower (and what depends on it) and builds the rest as a view")
{
    const std::filesystem::path root = writeProject("skip");
    Project project;
    std::vector<ProjectIssue> issues;
    REQUIRE(loadProject(root, project, issues));
    const auto check = [&root](const std::string &roomB, std::vector<std::string> &skipped,
        std::vector<ProjectIssue> &found)
    {
        std::string rooms = RoomsText;
        const std::string original =
            "  - {id: room:b, outline: [[1088, 0], [1600, 0], [1600, 512], [1088, 512]], floor: 0, ceiling: 384}\n";
        rooms.replace(rooms.find(original), original.size(), roomB);
        writeText(root / "rooms.yml", rooms);
        Project changed;
        std::vector<ProjectIssue> unused;
        REQUIRE(loadProject(root, changed, unused));
        ValidationParts parts;
        ValidationViews views;
        found.clear();
        validateProjectParts(changed, BuildOptions(), nullptr, nullptr, parts, found, &views);
        // What the view build found besides is kept with the view.
        found.insert(found.end(), views.skippedIssues.begin(), views.skippedIssues.end());
        skipped = views.skipped;
        return views.indoor != nullptr;
    };
    std::vector<std::string> skipped;
    std::vector<ProjectIssue> found;

    // A bow tie: said as such, the room and the opening into it left out, room:a still lowered.
    CHECK(check("  - {id: room:b, outline: [[1088, 0], [1600, 512], [1600, 0], [1088, 512]], floor: 0, ceiling: 384}\n",
        skipped, found));
    CHECK(std::find(skipped.begin(), skipped.end(), "room:b") != skipped.end());
    CHECK(std::find(skipped.begin(), skipped.end(), "open:ab") != skipped.end());
    CHECK(std::any_of(found.begin(), found.end(), [](const ProjectIssue &issue)
    {
        return issue.message.find("crosses or touches itself") != std::string::npos && issue.isError();
    }));
    CHECK(std::any_of(found.begin(), found.end(), [](const ProjectIssue &issue)
    {
        return issue.code == "skipped" && issue.severity == IssueSeverity::Note;
    }));
    // Points on one line: no area.
    CHECK(check("  - {id: room:b, outline: [[1088, 0], [1300, 0], [1600, 0]], floor: 0, ceiling: 384}\n",
        skipped, found));
    CHECK(std::any_of(found.begin(), found.end(), [](const ProjectIssue &issue)
    {
        return issue.message.find("has no area") != std::string::npos;
    }));
    // A schema error (no ceiling) on one room: that room is skipped too.
    CHECK(check("  - {id: room:b, outline: [[1088, 0], [1600, 0], [1600, 512], [1088, 512]], floor: 0}\n",
        skipped, found));
    CHECK(std::find(skipped.begin(), skipped.end(), "room:b") != skipped.end());
    std::filesystem::remove_all(root);
}

TEST_CASE("S5b1: an append makes a list the object does not have yet; overlapping rooms skip the later one")
{
    const std::filesystem::path root = writeProject("append");
    const TransactionResult added = edit(root, "[{op: patch, id: room:b, file: rooms.yml, patch: [{op: add, path: "
        "/pillars/-, value: {at: [1300, 200], size: [32, 32]}}]}]", "user");
    CHECK(added.applied);
    CHECK(readText(root / "rooms.yml").find("{key: pillar1, at: [1300, 200]") != std::string::npos);

    // A third room drawn over room:a: the view build leaves out the new room only.
    edit(root, "[{op: add, to: rooms, value: {id: room:c, outline: [[100, 100], [300, 100], [300, 300], [100, 300]], "
        "floor: 0, ceiling: 300}}]", "user");
    Project project;
    std::vector<ProjectIssue> issues;
    REQUIRE(loadProject(root, project, issues));
    ValidationParts parts;
    ValidationViews views;
    validateProjectParts(project, BuildOptions(), nullptr, nullptr, parts, issues, &views);
    CHECK(views.indoor != nullptr);
    std::string skippedText;

    for (const std::string &id : views.skipped)
    {
        skippedText += id + " ";
    }

    for (const ProjectIssue &issue : issues)
    {
        skippedText += "| " + issue.path + ": " + issue.message;
    }

    INFO(skippedText);
    CHECK(views.skipped == std::vector<std::string>{"room:c"});
    REQUIRE_FALSE(views.skippedIssues.empty());
    CHECK(views.skippedIssues.back().message.find("overlap") != std::string::npos);
    std::filesystem::remove_all(root);
}
