// `oymap pins`, `oymap record` and `oymap lock`: the review pins, the attribution of outside edits and the id lock as
// a record (S5_BROWSER_EDITOR.md 2.4.1, 2.6 item 7, 2.10 and 3.13; slice S5a1).
#include "cli/Commands.h"

#include "core/Json.h"
#include "core/Ops.h"
#include "core/Pins.h"
#include "core/Project.h"

#include <cstdlib>
#include <iostream>
#include <sstream>

namespace OpenYAMM::Studio
{
namespace
{
std::string textOf(const YAML::Node &node, const char *pKey)
{
    const YAML::Node value = node.IsDefined() && node.IsMap() ? node[pKey] : YAML::Node();
    return value.IsDefined() && value.IsScalar() ? value.Scalar() : std::string();
}

// Every value of a repeated option.
std::vector<std::string> takeOptions(std::vector<std::string> &arguments, const std::string &option)
{
    std::vector<std::string> values;
    std::string value;

    while (takeOption(arguments, option, value))
    {
        values.push_back(value);
    }

    return values;
}

bool parseNumbers(const std::string &text, std::vector<double> &numbers)
{
    numbers.clear();
    std::stringstream stream(text);
    std::string part;

    while (std::getline(stream, part, ','))
    {
        char *pEnd = nullptr;
        const double value = std::strtod(part.c_str(), &pEnd);

        if (part.empty() || pEnd == part.c_str() || *pEnd != '\0')
        {
            return false;
        }

        numbers.push_back(value);
    }

    return true;
}

void printPin(const YAML::Node &pin)
{
    const std::string status = textOf(pin, "status").empty() ? std::string("open") : textOf(pin, "status");
    std::cout << textOf(pin, "id") << " [" << status
              << (textOf(pin, "claimed_by").empty() ? "" : " by " + textOf(pin, "claimed_by")) << "] "
              << textOf(pin, "author") << (textOf(pin, "source").empty() ? "" : ", " + textOf(pin, "source"))
              << (textOf(pin, "created").empty() ? "" : ", " + textOf(pin, "created")) << "\n";
    std::cout << "    " << textOf(pin, "text") << "\n";

    if (!textOf(pin, "on").empty())
    {
        std::cout << "    on " << textOf(pin, "on")
                  << (textOf(pin, "file").empty() ? "" : " (" + textOf(pin, "file") + ")") << "\n";
    }

    if (pin["at"])
    {
        std::cout << "    at " << pin["at"][0].Scalar() << ", " << pin["at"][1].Scalar() << ", " << pin["at"][2].Scalar()
                  << "\n";
    }

    if (const YAML::Node pose = pin["pose"]; pose && pose["position"])
    {
        std::cout << "    pose " << pose["position"][0].Scalar() << ", " << pose["position"][1].Scalar() << ", "
                  << pose["position"][2].Scalar() << (pose["yaw_radians"] ? " yaw " + pose["yaw_radians"].Scalar() : "")
                  << (pose["pitch_degrees"] ? " pitch " + pose["pitch_degrees"].Scalar() + " degrees" : "")
                  << (textOf(pin, "map").empty() ? "" : " on " + textOf(pin, "map"))
                  << (textOf(pin, "world").empty() ? "" : " (" + textOf(pin, "world") + ")") << "\n";
    }

    if (!textOf(pin, "picture").empty())
    {
        std::cout << "    picture " << textOf(pin, "picture") << "\n";
    }

    if (!textOf(pin, "revision").empty())
    {
        std::cout << "    made against revision " << textOf(pin, "revision") << "\n";
    }

    for (const YAML::Node &reply : pin["replies"])
    {
        std::cout << "    > " << textOf(reply, "author")
                  << (textOf(reply, "status").empty() ? "" : " (" + textOf(reply, "status") + ")") << ": "
                  << textOf(reply, "text") << "\n";

        for (const YAML::Node &picture : reply["pictures"])
        {
            std::cout << "      picture " << picture.Scalar() << "\n";
        }
    }
}

void writePinJson(JsonWriter &writer, const YAML::Node &pin)
{
    writer.node(pin);
}

int reportPinResult(const PinResult &result, bool ok, bool asJson, const std::string &command)
{
    if (asJson)
    {
        JsonWriter writer(true);
        writer.beginObject();
        writer.field("ok", ok);

        if (ok)
        {
            writer.field("counter", result.counter);
            writer.key("pin");
            writePinJson(writer, result.pin);
        }
        else
        {
            writer.field("error", result.message);
        }

        writer.endObject();
        std::cout << writer.text() << "\n";
        return ok ? 0 : 1;
    }

    if (!ok)
    {
        std::cerr << "oymap pins " << command << ": " << result.message << "\n";
        return 1;
    }

    printPin(result.pin);
    std::cout << "pins counter " << result.counter << "\n";
    return 0;
}

const char *const PinsUsage =
    "usage: oymap pins <action> ...\n"
    "  list <project> [--status open|claimed|resolved|accepted|declined] [--json]\n"
    "  show <project> <pin> [--json]\n"
    "  import <inbox> [--project <folder>]... [--search <folder>]... [--dry-run] [--json]\n"
    "      files the game's pins (`pin <text>` in the console; pins_inbox/ by default) into their projects: by the\n"
    "      project the map's <stem>.studio.yml names, else by the map's name among the projects given or found\n"
    "      (--search, else OYMAP_PROJECT_ROOTS, else devdocs/map_studio/briefs and devdocs/xeen/briefs under the\n"
    "      current folder: the projects the play copies are installed from, not the scratch copies of\n"
    "      output/studio_cal); pictures go to <project>/.oymap/pins/pictures/\n"
    "  add <project> --text <text> [--on <id> [--file <file>]] [--at x,y,z] [--pose x,y,z[,yaw_radians,pitch_degrees]]\n"
    "      [--map <file> --world <world>] [--picture <png>] [--by <author>]\n"
    "  claim <project> <pin> --by agent:<name> [--force]\n"
    "  reply <project> <pin> --by <author> --text <text> [--picture <png>]...\n"
    "  resolve <project> <pin> --by agent:<name> --text <what was done> [--picture <png>]...\n"
    "  accept <project> <pin> [--by user] [--text <text>]\n"
    "  reopen <project> <pin> [--by user] --text <why>\n"
    "  decline <project> <pin> --by <author> --text <why>\n"
    "  keep <project> <pin>          keep the pin's picture in review/pictures/ (in git)\n"
    "  tour <project> --out <tour.yml> --shots <folder> [--pin <pin>]... [--status <status,...>]\n"
    "      a screenshot tour at the pins' poses (default: open, claimed and resolved pins), for\n"
    "      tools/run_game.sh ... --set debug.screenshot_tour_path=<tour.yml>\n";

int pinsList(std::vector<std::string> arguments, bool asJson, bool show)
{
    std::string status;
    takeOption(arguments, "--status", status);

    if (arguments.size() != (show ? 2u : 1u))
    {
        std::cerr << PinsUsage;
        return 2;
    }

    YAML::Node document;
    std::string errorMessage;
    std::error_code error;

    if (!std::filesystem::is_regular_file(std::filesystem::path(arguments[0]) / "project.yml", error))
    {
        std::cerr << "oymap pins: not a project folder: " << arguments[0] << "\n";
        return 1;
    }

    if (!readPinsDocument(arguments[0], document, errorMessage))
    {
        std::cerr << "oymap pins: " << errorMessage << "\n";
        return 1;
    }

    std::vector<YAML::Node> pins = pinsWithStatus(document, status);

    if (show)
    {
        std::vector<YAML::Node> one;

        for (const YAML::Node &pin : pins)
        {
            if (textOf(pin, "id") == arguments[1])
            {
                one.push_back(pin);
            }
        }

        if (one.empty())
        {
            std::cerr << "oymap pins show: the project has no pin " << arguments[1] << "\n";
            return 1;
        }

        pins = one;
    }

    const int counter = document["counter"] ? document["counter"].as<int>() : 0;

    if (asJson)
    {
        JsonWriter writer(true);
        writer.beginObject();
        writer.field("counter", counter);
        writer.key("pins");
        writer.beginArray();

        for (const YAML::Node &pin : pins)
        {
            writePinJson(writer, pin);
        }

        writer.endArray();
        writer.endObject();
        std::cout << writer.text() << "\n";
        return 0;
    }

    for (const YAML::Node &pin : pins)
    {
        printPin(pin);
    }

    if (!show)
    {
        std::cout << pins.size() << " pin(s)" << (status.empty() ? "" : " " + status) << "; pins counter " << counter
                  << "\n";
    }

    return 0;
}

std::vector<std::string> defaultSearchRoots()
{
    std::vector<std::string> roots;

    if (const char *pRoots = std::getenv("OYMAP_PROJECT_ROOTS"); pRoots != nullptr && *pRoots != '\0')
    {
        std::stringstream stream(pRoots);
        std::string root;

        while (std::getline(stream, root, ':'))
        {
            if (!root.empty())
            {
                roots.push_back(root);
            }
        }

        return roots;
    }

    // The projects the play copies are installed from; output/studio_cal holds many scratch copies of each, which
    // would make every match by map name ambiguous (search it with --search where a pin belongs there).
    for (const char *pRoot : {"devdocs/map_studio/briefs", "devdocs/xeen/briefs"})
    {
        std::error_code error;

        if (std::filesystem::is_directory(pRoot, error))
        {
            roots.push_back(pRoot);
        }
    }

    return roots;
}

int pinsImport(std::vector<std::string> arguments, bool asJson)
{
    InboxOptions options;
    options.dryRun = takeFlag(arguments, "--dry-run");
    options.projects = takeOptions(arguments, "--project");
    std::vector<std::string> searchRoots = takeOptions(arguments, "--search");

    if (arguments.size() != 1)
    {
        std::cerr << PinsUsage;
        return 2;
    }

    // Projects named on the command line are the only candidates; else those found under the search roots.
    if (options.projects.empty())
    {
        if (searchRoots.empty())
        {
            searchRoots = defaultSearchRoots();
        }

        for (const std::string &root : searchRoots)
        {
            for (const std::filesystem::path &project : findProjects(root, 3))
            {
                options.projects.push_back(project.string());
            }
        }
    }

    InboxResult result;
    std::string errorMessage;

    if (!importPinInbox(arguments[0], options, result, errorMessage))
    {
        std::cerr << "oymap pins import: " << errorMessage << "\n";
        return 1;
    }

    if (asJson)
    {
        JsonWriter writer(true);
        writer.beginObject();
        writer.field("dry_run", options.dryRun);
        writer.key("imported");
        writer.beginArray();

        for (const InboxImported &imported : result.imported)
        {
            writer.beginObject();
            writer.field("file", imported.file);
            writer.field("project", imported.project);
            writer.field("pin", imported.pin);
            writer.field("matched_by", imported.matchedBy);
            writer.field("picture", imported.picture);
            writer.endObject();
        }

        writer.endArray();
        writer.key("skipped");
        writer.beginArray();

        for (const InboxSkipped &skipped : result.skipped)
        {
            writer.beginObject();
            writer.field("file", skipped.file);
            writer.field("reason", skipped.reason);
            writer.endObject();
        }

        writer.endArray();
        writer.endObject();
        std::cout << writer.text() << "\n";
        return 0;
    }

    for (const InboxImported &imported : result.imported)
    {
        std::cout << (options.dryRun ? "would file " : "filed ") << imported.file << " -> " << imported.project
                  << (imported.pin.empty() ? "" : " as " + imported.pin) << " (by its " << imported.matchedBy
                  << (imported.picture ? ", with its picture)" : ", no picture)") << "\n";
    }

    for (const InboxSkipped &skipped : result.skipped)
    {
        std::cout << "left in the inbox: " << skipped.file << ": " << skipped.reason << "\n";
    }

    std::cout << result.imported.size() << " pin(s) " << (options.dryRun ? "would be " : "") << "filed, "
              << result.skipped.size() << " left in the inbox\n";
    return 0;
}

int pinsAdd(std::vector<std::string> arguments, bool asJson)
{
    NewPin pin;
    std::string at;
    std::string pose;
    std::string picture;
    takeOption(arguments, "--text", pin.text);
    takeOption(arguments, "--on", pin.on);
    takeOption(arguments, "--file", pin.file);
    takeOption(arguments, "--at", at);
    takeOption(arguments, "--pose", pose);
    takeOption(arguments, "--picture", picture);
    takeOption(arguments, "--map", pin.map);
    takeOption(arguments, "--world", pin.world);
    takeOption(arguments, "--by", pin.author);
    pin.source = "agent";

    if (pin.author == "user")
    {
        pin.source = "studio";
    }

    if (arguments.size() != 1 || pin.text.empty())
    {
        std::cerr << PinsUsage;
        return 2;
    }

    std::vector<double> numbers;

    if (!at.empty())
    {
        if (!parseNumbers(at, numbers) || numbers.size() != 3)
        {
            std::cerr << "oymap pins add: --at is x,y,z\n";
            return 2;
        }

        pin.at = numbers;
    }

    if (!pose.empty())
    {
        if (!parseNumbers(pose, numbers) || (numbers.size() != 3 && numbers.size() != 5))
        {
            std::cerr << "oymap pins add: --pose is x,y,z or x,y,z,yaw_radians,pitch_degrees (as `loc` prints)\n";
            return 2;
        }

        pin.position = std::vector<double>(numbers.begin(), numbers.begin() + 3);

        if (numbers.size() == 5)
        {
            pin.yawRadians = numbers[3];
            pin.pitchDegrees = numbers[4];
        }
    }

    pin.picture = std::filesystem::path(picture);
    PinResult result;
    const bool ok = addPin(arguments[0], pin, result);
    return reportPinResult(result, ok, asJson, "add");
}

int pinsTour(std::vector<std::string> arguments)
{
    std::string out;
    std::string shots;
    std::string statusList;
    takeOption(arguments, "--out", out);
    takeOption(arguments, "--shots", shots);
    takeOption(arguments, "--status", statusList);
    const std::vector<std::string> pinIds = takeOptions(arguments, "--pin");

    if (arguments.size() != 1 || out.empty() || shots.empty())
    {
        std::cerr << PinsUsage;
        return 2;
    }

    YAML::Node document;
    std::string errorMessage;

    if (!readPinsDocument(arguments[0], document, errorMessage))
    {
        std::cerr << "oymap pins tour: " << errorMessage << "\n";
        return 1;
    }

    std::vector<std::string> statuses;
    std::stringstream stream(statusList.empty() ? std::string("open,claimed,resolved") : statusList);

    for (std::string status; std::getline(stream, status, ',');)
    {
        statuses.push_back(status);
    }

    std::vector<std::string> skipped;
    const std::filesystem::path shotsFolder = std::filesystem::absolute(shots);
    const std::string text = pinsTourText(document, pinIds, statuses, shotsFolder, skipped);

    if (!writeTextFileAtomically(out, text, errorMessage))
    {
        std::cerr << "oymap pins tour: " << errorMessage << "\n";
        return 1;
    }

    const YAML::Node tour = YAML::Load(text);
    std::cout << "wrote " << out << ": " << tour["shots"].size() << " shot(s) into " << shotsFolder.string() << "\n";

    for (const std::string &id : skipped)
    {
        std::cout << "no pose, no shot: " << id << "\n";
    }

    // The map the pins were made on, for the command line that takes the pictures.
    std::string map;
    std::string world;

    for (const YAML::Node &pin : document["pins"])
    {
        if (map.empty() && !textOf(pin, "map").empty())
        {
            map = textOf(pin, "map");
            world = textOf(pin, "world");
        }
    }

    if (tour["shots"].size() > 0)
    {
        std::cout << "take the pictures: ./tools/run_game.sh --isolated pins --world "
                  << (world.empty() ? "<world>" : world) << " --map " << (map.empty() ? "<map>" : map)
                  << " --assets <root with the map installed> --seconds 120 --set debug.screenshot_tour_path="
                  << std::filesystem::absolute(out).string() << "\n";
    }

    return 0;
}
}

int runPins(const std::vector<std::string> &rawArguments)
{
    std::vector<std::string> arguments = rawArguments;
    const bool asJson = takeFlag(arguments, "--json");

    if (arguments.empty())
    {
        std::cerr << PinsUsage;
        return 2;
    }

    const std::string action = arguments.front();
    arguments.erase(arguments.begin());

    if (action == "list" || action == "show")
    {
        return pinsList(arguments, asJson, action == "show");
    }

    if (action == "import")
    {
        return pinsImport(arguments, asJson);
    }

    if (action == "add")
    {
        return pinsAdd(arguments, asJson);
    }

    if (action == "tour")
    {
        return pinsTour(arguments);
    }

    std::string by;
    std::string text;
    takeOption(arguments, "--by", by);
    takeOption(arguments, "--text", text);
    const bool force = takeFlag(arguments, "--force");
    std::vector<PinPicture> pictures;

    for (const std::string &picture : takeOptions(arguments, "--picture"))
    {
        pictures.emplace_back(picture);
    }

    if (arguments.size() != 2)
    {
        std::cerr << PinsUsage;
        return 2;
    }

    PinResult result;
    bool ok = false;

    if (action == "claim")
    {
        ok = claimPin(arguments[0], arguments[1], by, force, result);
    }
    else if (action == "keep")
    {
        ok = keepPinPicture(arguments[0], arguments[1], result);
    }
    else
    {
        PinAction pinAction = PinAction::Reply;

        if (action == "resolve")
        {
            pinAction = PinAction::Resolve;
        }
        else if (action == "accept")
        {
            pinAction = PinAction::Accept;
        }
        else if (action == "reopen")
        {
            pinAction = PinAction::Reopen;
        }
        else if (action == "decline")
        {
            pinAction = PinAction::Decline;
        }
        else if (action != "reply")
        {
            std::cerr << "oymap pins: unknown action '" << action << "'\n" << PinsUsage;
            return 2;
        }

        // Accepting and reopening are the person's.
        if (by.empty() && (pinAction == PinAction::Accept || pinAction == PinAction::Reopen))
        {
            by = "user";
        }

        ok = actOnPin(arguments[0], arguments[1], pinAction, by, text, pictures, result);
    }

    return reportPinResult(result, ok, asJson, action);
}

int runRecord(const std::vector<std::string> &rawArguments)
{
    std::vector<std::string> arguments = rawArguments;
    const bool asJson = takeFlag(arguments, "--json");
    std::string author;
    std::string label;
    takeOption(arguments, "--author", author);
    takeOption(arguments, "--label", label);

    if (arguments.size() != 1 || author.empty())
    {
        std::cerr << "usage: oymap record <project> --author <agent:name|user> [--label <what>] [--json]\n"
                     "  puts the author and label on the edits made outside the tool (a generator run, a text editor):\n"
                     "  the change on disk now, and every unattributed outside entry since that author's last entry.\n";
        return 2;
    }

    RecordResult result;
    std::string errorMessage;

    if (!recordOutsideEdits(arguments[0], author, label, result, errorMessage))
    {
        std::cerr << "oymap record: " << errorMessage << "\n";
        return 1;
    }

    if (asJson)
    {
        JsonWriter writer(true);
        writer.beginObject();
        writer.field("revision", result.revision);
        writer.key("recorded");
        writer.beginArray();

        for (const HistoryEntry &entry : result.taken)
        {
            writer.beginObject();
            writer.field("sequence", entry.sequence);
            writer.field("revision_before", entry.revisionBefore);
            writer.field("revision", entry.revisionAfter);
            writer.key("changes");
            writer.beginArray();

            for (const std::string &change : entry.changes)
            {
                writer.value(change);
            }

            writer.endArray();
            writer.endObject();
        }

        writer.endArray();
        writer.endObject();
        std::cout << writer.text() << "\n";
        return 0;
    }

    if (result.taken.empty())
    {
        std::cout << "nothing to record: no unattributed outside edit since " << author << "'s last entry (revision "
                  << result.revision << ")\n";
        return 0;
    }

    for (const HistoryEntry &entry : result.taken)
    {
        std::cout << "recorded entry " << entry.sequence << " as " << author
                  << (label.empty() ? "" : " \"" + label + "\"") << " (" << entry.revisionBefore << " -> "
                  << entry.revisionAfter << ")\n";

        for (const std::string &change : entry.changes)
        {
            std::cout << "    " << change << "\n";
        }
    }

    std::cout << "revision " << result.revision << "\n";
    return 0;
}

int runLock(const std::vector<std::string> &rawArguments)
{
    std::vector<std::string> arguments = rawArguments;
    const bool asJson = takeFlag(arguments, "--json");
    const bool dryRun = takeFlag(arguments, "--dry-run");

    if (arguments.size() != 2 || arguments[0] != "prune")
    {
        std::cerr << "usage: oymap lock prune <project> [--dry-run] [--json]\n"
                     "  drops the entries of ids.lock.yml whose ids the project no longer has. Builds keep them, so a\n"
                     "  number once given stays through undo; prune before sharing or shipping a map, or when a\n"
                     "  build says a table has no free number left.\n";
        return 2;
    }

    LockPruneResult result;
    std::string errorMessage;

    if (!pruneProjectLock(arguments[1], dryRun, result, errorMessage))
    {
        std::cerr << "oymap lock prune: " << errorMessage << "\n";
        return 1;
    }

    if (asJson)
    {
        JsonWriter writer(true);
        writer.beginObject();
        writer.field("dry_run", dryRun);
        writer.key("dropped");
        writer.beginArray();

        for (const std::string &entry : result.dropped)
        {
            writer.value(entry);
        }

        writer.endArray();
        writer.field("lock_hash_before", result.lockHashBefore);
        writer.field("lock_hash", result.lockHashAfter);

        if (!result.note.empty())
        {
            writer.field("note", result.note);
        }

        writer.endObject();
        std::cout << writer.text() << "\n";
        return 0;
    }

    if (!result.note.empty())
    {
        std::cout << result.note << "\n";
    }

    for (const std::string &entry : result.dropped)
    {
        std::cout << (dryRun ? "would drop " : "dropped ") << entry << "\n";
    }

    std::cout << result.dropped.size() << " entr" << (result.dropped.size() == 1 ? "y" : "ies")
              << (dryRun ? " would be dropped" : " dropped") << "; lock " << result.lockHashBefore << " -> "
              << result.lockHashAfter << "\n";
    return 0;
}
}
