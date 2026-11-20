#pragma once

#include <yaml-cpp/yaml.h>

#include <filesystem>
#include <optional>
#include <string>
#include <utility>
#include <vector>

namespace OpenYAMM::Studio
{
// The review pins of a project (S5_BROWSER_EDITOR.md 2.4.1 and 3.13): review/pins.yml, pins format 1, is the
// project's review document, not part of its source. It has its own change counter (`counter`, one more for every
// change) and its own append-only log (.oymap/pins/log.jsonl); a pin, a claim or a reply never changes the source
// revision and is never undone with the map. Pictures stay out of git by default: .oymap/pins/pictures/<pin>.png,
// and review/pictures/ only for one kept on purpose (`keep`).
//
// A pin anchors to a top-level id (`on`, with `file` where the id is in more than one file) or to a point (`at`), and
// a pin from the game always has its pose (as `loc` prints it). Keyed sub-objects (`thing:x/parts/p3`) arrive with
// the keys (S5b1 indoor, S5b2 sketch.yml).
//
// Statuses: open -> claimed (an agent took it) -> resolved (the agent says what it did) -> accepted (the person
// agrees); reopen puts a resolved, accepted or declined pin back to open; decline closes a pin that will not be done.

// A format 0 document (`reply` as one text, statuses open|resolved|declined) as format 1. A format 1 document is
// returned as it is (a copy).
YAML::Node migratePinsDocument(const YAML::Node &document);

// Reads the project's pins document as format 1: an empty one when the project has none, a format 0 one migrated
// in memory (written as format 1 on the next change). False with `errorMessage` when the file cannot be read or
// parsed, or does not match pins.schema.json.
bool readPinsDocument(const std::filesystem::path &projectRoot, YAML::Node &document, std::string &errorMessage);

// The pins of a document whose status is `status` (all with an empty one). A pin without a status is open.
std::vector<YAML::Node> pinsWithStatus(const YAML::Node &document, const std::string &status);

enum class PinRefusal
{
    None,
    NotAProject,
    Locked,
    NoSuchPin,
    // The pin is not in a state the action applies to (claiming a resolved pin, accepting an open one).
    WrongState,
    // The request itself is wrong: an empty text, an `on` the project lacks, a picture that cannot be read.
    BadRequest,
    Failed,
};

struct PinResult
{
    PinRefusal refusal = PinRefusal::None;
    std::string message;
    // The pin as written (after the change).
    YAML::Node pin;
    int counter = 0;
};

// A picture given with a pin or a reply: a local file (the command line, the game's inbox), or its bytes (the request
// list: the studio's screenshot of its view). PNG or JPEG; written into .oymap/pins/pictures/.
struct PinPicture
{
    PinPicture() = default;
    PinPicture(std::filesystem::path path)
        : file(std::move(path))
    {
    }

    std::filesystem::path file;
    std::string bytes;

    bool empty() const
    {
        return file.empty() && bytes.empty();
    }

    // ".png" or ".jpg": from the bytes' signature, or the file's extension (".png" when it has none).
    std::string extension() const;
};

// The largest picture the pins take as bytes (a 4K screenshot as PNG is about 12 MB; the studio sends JPEG or PNG
// of its view, well under this).
constexpr size_t MaxPinPictureBytes = 16u * 1024u * 1024u;

// A pin to add. `picture` is copied (or written) into .oymap/pins/pictures/.
struct NewPin
{
    std::string text;
    std::string on;
    std::string file;
    std::optional<std::vector<double>> at;
    // As `loc` prints it: position (party feet), yaw in radians, pitch in degrees, heading in 2048 units.
    std::optional<std::vector<double>> position;
    std::optional<double> yawRadians;
    std::optional<double> pitchDegrees;
    std::optional<int> headingYawUnits;
    std::string source = "agent";
    std::string author = "agent";
    std::string world;
    std::string map;
    std::string created;
    // The source revision and lock hash the pin was made against; the project's current ones when empty and
    // `stampRevision` (a game pin without its map's studio file has none: nothing says what the map was built from).
    std::string revision;
    std::string lockHash;
    bool stampRevision = true;
    PinPicture picture;
    // The inbox file a game pin came from.
    std::string from;
};

bool addPin(const std::filesystem::path &projectRoot, const NewPin &pin, PinResult &result);

// An agent takes an open pin (or one it claimed already). `force` takes it from another claimant.
bool claimPin(
    const std::filesystem::path &projectRoot,
    const std::string &pinId,
    const std::string &by,
    bool force,
    PinResult &result);

// The actions after a claim. Each may carry a reply (`text`, local `pictures` copied beside the pin's own); `reply`
// alone adds a reply and changes no status.
enum class PinAction
{
    Reply,
    Resolve,
    Accept,
    Reopen,
    Decline,
};

bool actOnPin(
    const std::filesystem::path &projectRoot,
    const std::string &pinId,
    PinAction action,
    const std::string &author,
    const std::string &text,
    const std::vector<PinPicture> &pictures,
    PinResult &result);

// Copies the pin's own picture into review/pictures/ (kept in git) and marks the pin `keep: true`.
bool keepPinPicture(const std::filesystem::path &projectRoot, const std::string &pinId, PinResult &result);

// --- the game's inbox -------------------------------------------------------------------------------------------

struct InboxImported
{
    // The inbox file ("20261120-101205-6d01.yml").
    std::string file;
    // The project folder as the candidates list names it, or the pin's own `project` field.
    std::string project;
    std::string pin;
    // "studio file" (the pin named its project), or "map" (matched by the map's name).
    std::string matchedBy;
    bool picture = false;
};

struct InboxSkipped
{
    std::string file;
    std::string reason;
};

struct InboxResult
{
    std::vector<InboxImported> imported;
    std::vector<InboxSkipped> skipped;
};

struct InboxOptions
{
    // The projects a pin may go to (as given; matched by the pin's `project` field and by the map).
    std::vector<std::string> projects;
    // A pin's own `project` field is taken even when it is not among `projects` (the command line; the request list
    // accepts only the projects it is given).
    bool trustPinProject = true;
    bool dryRun = false;
    // A pin's picture may still be on its way (the game writes it a frame later): a pin younger than this without
    // its picture waits for the next import.
    int pictureWaitSeconds = 30;
};

// Files every pin of the inbox (`<inbox>/*.yml`, pins format 1 as the game writes them) into its project's pins
// document: its picture moves into the project's .oymap/pins/pictures/, the pin file into <inbox>/imported/. A pin
// whose project cannot be told (none matches, or several do) is skipped with the reason and stays in the inbox.
bool importPinInbox(
    const std::filesystem::path &inbox,
    const InboxOptions &options,
    InboxResult &result,
    std::string &errorMessage);

// Project folders under `root` (folders holding project.yml, searched `depth` levels down; .oymap, build and
// node_modules are not entered).
std::vector<std::filesystem::path> findProjects(const std::filesystem::path &root, int depth);

// A screenshot tour (debug.screenshot_tour_path, tools/RUN_GAME.md) at the pins' poses: one shot per pin that has a
// pose, named after the pin (p7), exiting after the last. `pinIds` empty: every pin whose status is in `statuses`.
// `skipped` names the pins without a pose.
std::string pinsTourText(
    const YAML::Node &document,
    const std::vector<std::string> &pinIds,
    const std::vector<std::string> &statuses,
    const std::filesystem::path &outputDirectory,
    std::vector<std::string> &skipped);

// Moves the pins anchored to renamed objects (or their sub-objects) to the new names, in order (S5_BROWSER_EDITOR.md
// 2.6 item 4: names in pins follow renames both ways). The caller holds the project's write lock. `renamed` lists
// "pin:p3: room:hall -> room:great_hall". A change of the pins document like any other: its counter and its log.
bool renamePinAnchors(
    const std::filesystem::path &projectRoot,
    const std::vector<std::pair<std::string, std::string>> &renames,
    std::vector<std::string> &renamed,
    std::string &errorMessage);
}
