#include "core/Pins.h"

#include "core/CanonicalYaml.h"
#include "core/Json.h"
#include "core/Keys.h"
#include "core/Ops.h"
#include "core/Project.h"
#include "core/Schema.h"

#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdio>
#include <ctime>
#include <map>
#include <set>

namespace OpenYAMM::Studio
{
namespace
{
const char *const PinsFile = "review/pins.yml";

YAML::Node childOf(const YAML::Node &node, const char *pKey)
{
    return node.IsDefined() && node.IsMap() ? node[pKey] : YAML::Node(YAML::NodeType::Undefined);
}

std::string textOf(const YAML::Node &node, const char *pKey)
{
    const YAML::Node value = childOf(node, pKey);
    return value.IsDefined() && value.IsScalar() ? value.Scalar() : std::string();
}

// A text scalar that stays a text whatever it reads like (a revision of digits, "yes").
YAML::Node textNode(const std::string &text)
{
    YAML::Node node(text);
    node.SetTag("!");
    return node;
}

// A number with at most `decimals` decimals, without trailing zeros.
YAML::Node numberNode(double value, int decimals)
{
    char text[64];
    std::snprintf(text, sizeof(text), "%.*f", decimals, value);
    std::string written = text;

    if (written.find('.') != std::string::npos)
    {
        while (written.back() == '0')
        {
            written.pop_back();
        }

        if (written.back() == '.')
        {
            written.pop_back();
        }
    }

    if (written == "-0")
    {
        written = "0";
    }

    return YAML::Node(written);
}

std::string localTimestamp()
{
    const std::time_t now = std::chrono::system_clock::to_time_t(std::chrono::system_clock::now());
    const std::tm *pLocal = std::localtime(&now);
    char text[32] = {};

    if (pLocal != nullptr)
    {
        std::strftime(text, sizeof(text), "%Y-%m-%dT%H:%M:%S", pLocal);
    }

    return text;
}

std::string statusOf(const YAML::Node &pin)
{
    const std::string status = textOf(pin, "status");
    return status.empty() ? std::string("open") : status;
}

YAML::Node emptyDocument()
{
    YAML::Node document(YAML::NodeType::Map);
    document["format"] = 1;
    document["counter"] = 0;
    return document;
}

// The short name of a pin for its picture files: pin:p7 -> p7.
std::string pictureStem(const std::string &pinId)
{
    const size_t colon = pinId.find(':');
    return colon == std::string::npos ? pinId : pinId.substr(colon + 1);
}

bool moveFile(const std::filesystem::path &from, const std::filesystem::path &to, std::string &errorMessage)
{
    std::error_code error;
    std::filesystem::create_directories(to.parent_path(), error);
    std::filesystem::rename(from, to, error);

    if (!error)
    {
        return true;
    }

    // Across file systems: copy, then remove.
    error.clear();
    std::filesystem::copy_file(from, to, std::filesystem::copy_options::overwrite_existing, error);

    if (error)
    {
        errorMessage = "could not move " + from.filename().string() + ": " + error.message();
        return false;
    }

    std::filesystem::remove(from, error);
    return true;
}

bool copyPicture(const std::filesystem::path &from, const std::filesystem::path &to, std::string &errorMessage)
{
    std::error_code error;

    if (!std::filesystem::is_regular_file(from, error))
    {
        errorMessage = "no picture at " + from.filename().string();
        return false;
    }

    std::filesystem::create_directories(to.parent_path(), error);
    std::filesystem::copy_file(from, to, std::filesystem::copy_options::overwrite_existing, error);

    if (error)
    {
        errorMessage = "could not copy the picture " + from.filename().string() + ": " + error.message();
        return false;
    }

    return true;
}

bool isPng(const std::string &bytes)
{
    return bytes.size() >= 8 && bytes.compare(0, 8, "\x89PNG\r\n\x1a\n") == 0;
}

bool isJpeg(const std::string &bytes)
{
    return bytes.size() >= 3 && static_cast<unsigned char>(bytes[0]) == 0xff
        && static_cast<unsigned char>(bytes[1]) == 0xd8 && static_cast<unsigned char>(bytes[2]) == 0xff;
}

// Writes a picture given with a pin or a reply to `to` (in the project's .oymap/pins/pictures/).
bool writePicture(const PinPicture &picture, const std::filesystem::path &to, std::string &errorMessage)
{
    if (!picture.file.empty())
    {
        return copyPicture(picture.file, to, errorMessage);
    }

    if (picture.bytes.size() > MaxPinPictureBytes)
    {
        errorMessage = "the picture is larger than " + std::to_string(MaxPinPictureBytes / (1024 * 1024)) + " MB";
        return false;
    }

    if (!isPng(picture.bytes) && !isJpeg(picture.bytes))
    {
        errorMessage = "the picture is neither PNG nor JPEG";
        return false;
    }

    std::error_code error;
    std::filesystem::create_directories(to.parent_path(), error);
    return writeTextFileAtomically(to, picture.bytes, errorMessage);
}

// The document as written: checked against the schema, in canonical form.
bool writePinsDocument(const std::filesystem::path &projectRoot, const YAML::Node &document, std::string &errorMessage)
{
    const std::vector<SchemaIssue> issues = SchemaSet::builtIn().validate(document, "pins.schema.json");

    if (!issues.empty())
    {
        errorMessage = "the pins document would not match its schema: " + issues.front().path + ": "
            + issues.front().message;
        return false;
    }

    return writeTextFileAtomically(projectRoot / PinsFile,
        writeCanonicalYaml(document, SchemaSet::builtIn(), "pins.schema.json"), errorMessage);
}

bool appendPinsLog(
    const std::filesystem::path &projectRoot,
    int counter,
    const std::string &action,
    const std::string &pinId,
    const std::string &author,
    const std::string &status,
    const std::string &text,
    std::string &errorMessage)
{
    JsonWriter line;
    line.beginObject();
    line.field("counter", counter);
    line.field("time", localTimestamp());
    line.field("action", action);
    line.field("pin", pinId);
    line.field("author", author);
    line.field("status", status);

    if (!text.empty())
    {
        line.field("text", text);
    }

    line.endObject();
    const std::filesystem::path path = projectStateRoot(projectRoot, true) / "pins" / "log.jsonl";
    std::string existing;
    readTextFile(path, existing);
    return writeTextFileAtomically(path, existing + line.take() + "\n", errorMessage);
}

// Where a pin is in the document's list, or -1.
int findPin(const YAML::Node &document, const std::string &pinId)
{
    const YAML::Node pins = childOf(document, "pins");

    if (!pins.IsDefined() || !pins.IsSequence())
    {
        return -1;
    }

    for (size_t index = 0; index < pins.size(); ++index)
    {
        if (textOf(pins[index], "id") == pinId)
        {
            return static_cast<int>(index);
        }
    }

    return -1;
}

std::string nextPinId(const YAML::Node &document)
{
    int highest = 0;

    for (const YAML::Node &pin : childOf(document, "pins"))
    {
        const std::string id = textOf(pin, "id");

        if (id.rfind("pin:p", 0) == 0 && id.size() > 5
            && std::all_of(id.begin() + 5, id.end(), [](char letter) { return letter >= '0' && letter <= '9'; }))
        {
            highest = std::max(highest, std::stoi(id.substr(5)));
        }
    }

    return "pin:p" + std::to_string(highest + 1);
}

// The current source revision and lock hash of the project (for a pin or a reply made now).
bool currentRevision(const std::filesystem::path &projectRoot, Project &project, std::string &revision,
    std::string &errorMessage)
{
    std::vector<ProjectIssue> issues;

    if (!loadProject(projectRoot, project, issues))
    {
        errorMessage = issues.empty() ? "not a project" : issues.front().message;
        return false;
    }

    revision = projectRevision(project);
    return true;
}

// Where a top-level id is: the source files that hold it.
std::vector<std::string> filesWithId(const Project &project, const std::string &id)
{
    std::vector<std::string> found;

    for (const std::pair<const std::string, ProjectFile> &file : project.files)
    {
        if (!isSourceFile(file.first) || !file.second.document.IsMap())
        {
            continue;
        }

        bool has = false;

        for (YAML::const_iterator list = file.second.document.begin(); list != file.second.document.end() && !has;
             ++list)
        {
            if (!list->second.IsSequence())
            {
                continue;
            }

            // A copy of the node: `list->second` lives in a temporary the loop would outlive.
            const YAML::Node items = list->second;

            for (const YAML::Node &item : items)
            {
                if (textOf(item, "id") == id)
                {
                    has = true;
                    break;
                }
            }
        }

        if (has)
        {
            found.push_back(file.first);
        }
    }

    return found;
}

// Reads, checks and changes the document under the project lock, then writes it with the counter one higher and
// logs the change. `change` returns false with a refusal set in `result`.
template <typename Change>
bool changePins(
    const std::filesystem::path &projectRoot,
    const std::string &action,
    const std::string &author,
    PinResult &result,
    Change change)
{
    result = {};
    std::error_code fileError;

    if (!std::filesystem::is_regular_file(projectRoot / "project.yml", fileError))
    {
        result.refusal = PinRefusal::NotAProject;
        result.message = "not a project folder (no project.yml): " + projectRoot.filename().string();
        return false;
    }

    ProjectWriteLock lock(projectRoot, 2000);

    if (!lock.held())
    {
        result.refusal = PinRefusal::Locked;
        result.message = ProjectLockedMessage;
        return false;
    }

    YAML::Node document;
    std::string errorMessage;

    if (!readPinsDocument(projectRoot, document, errorMessage))
    {
        result.refusal = PinRefusal::Failed;
        result.message = errorMessage;
        return false;
    }

    std::string pinId;
    std::string text;

    if (!change(document, pinId, text))
    {
        return false;
    }

    const int counter = (childOf(document, "counter").IsDefined() ? document["counter"].as<int>() : 0) + 1;
    document["counter"] = counter;
    const int index = findPin(document, pinId);
    const YAML::Node pin = index >= 0 ? YAML::Node(document["pins"][static_cast<size_t>(index)]) : YAML::Node();

    if (!writePinsDocument(projectRoot, document, errorMessage)
        || !appendPinsLog(projectRoot, counter, action, pinId, author, statusOf(pin), text, errorMessage))
    {
        result.refusal = PinRefusal::Failed;
        result.message = errorMessage;
        return false;
    }

    result.counter = counter;
    // Read back as written, so the caller shows what the file holds.
    YAML::Node written;

    if (readPinsDocument(projectRoot, written, errorMessage))
    {
        const int writtenIndex = findPin(written, pinId);
        result.pin = writtenIndex >= 0 ? YAML::Clone(written["pins"][static_cast<size_t>(writtenIndex)]) : YAML::Node();
    }

    return true;
}

bool refuse(PinResult &result, PinRefusal refusal, const std::string &message)
{
    result.refusal = refusal;
    result.message = message;
    return false;
}

YAML::Node replyNode(const std::string &author, const std::string &text, const std::string &revision,
    const std::string &status)
{
    YAML::Node reply(YAML::NodeType::Map);
    reply["author"] = textNode(author);

    if (!text.empty())
    {
        reply["text"] = textNode(text);
    }

    reply["created"] = textNode(localTimestamp());

    if (!revision.empty())
    {
        reply["revision"] = textNode(revision);
    }

    if (!status.empty())
    {
        reply["status"] = status;
    }

    return reply;
}
}

YAML::Node migratePinsDocument(const YAML::Node &document)
{
    YAML::Node migrated = YAML::Clone(document);

    if (!migrated.IsDefined() || !migrated.IsMap())
    {
        return emptyDocument();
    }

    const YAML::Node format = childOf(migrated, "format");

    if (format.IsDefined() && format.Scalar() != "0")
    {
        return migrated;
    }

    // Format 0: `reply` was one text; there was no counter, no claim and no accept.
    migrated["format"] = 1;

    if (!childOf(migrated, "counter").IsDefined())
    {
        migrated["counter"] = 0;
    }

    if (childOf(migrated, "pins").IsDefined())
    {
        for (YAML::Node pin : migrated["pins"])
        {
            const YAML::Node reply = childOf(pin, "reply");

            if (reply.IsDefined())
            {
                YAML::Node entry(YAML::NodeType::Map);
                entry["author"] = textNode("unknown");
                entry["text"] = textNode(reply.Scalar());

                if (statusOf(pin) != "open")
                {
                    entry["status"] = statusOf(pin);
                }

                pin["replies"].push_back(entry);
                pin.remove("reply");
            }
        }
    }

    return migrated;
}

bool readPinsDocument(const std::filesystem::path &projectRoot, YAML::Node &document, std::string &errorMessage)
{
    std::string text;

    if (!readTextFile(projectRoot / PinsFile, text))
    {
        document = emptyDocument();
        return true;
    }

    try
    {
        document = migratePinsDocument(YAML::Load(text));
    }
    catch (const YAML::Exception &exception)
    {
        errorMessage = std::string(PinsFile) + " is not valid YAML: " + exception.what();
        return false;
    }

    const std::vector<SchemaIssue> issues = SchemaSet::builtIn().validate(document, "pins.schema.json");

    if (!issues.empty())
    {
        errorMessage = std::string(PinsFile) + " does not match pins.schema.json: " + issues.front().path + ": "
            + issues.front().message;
        return false;
    }

    return true;
}

std::vector<YAML::Node> pinsWithStatus(const YAML::Node &document, const std::string &status)
{
    std::vector<YAML::Node> found;

    for (const YAML::Node &pin : childOf(document, "pins"))
    {
        if (status.empty() || statusOf(pin) == status)
        {
            found.push_back(pin);
        }
    }

    return found;
}

std::string PinPicture::extension() const
{
    if (file.empty())
    {
        return isJpeg(bytes) ? ".jpg" : ".png";
    }

    const std::string given = file.extension().string();
    return given.empty() ? std::string(".png") : given;
}

bool addPin(const std::filesystem::path &projectRoot, const NewPin &newPin, PinResult &result)
{
    return changePins(projectRoot, "add", newPin.author, result,
        [&](YAML::Node &document, std::string &pinId, std::string &text)
        {
            if (newPin.text.empty())
            {
                return refuse(result, PinRefusal::BadRequest, "a pin needs a text");
            }

            Project project;
            std::string revision;
            std::string errorMessage;

            if (!currentRevision(projectRoot, project, revision, errorMessage))
            {
                return refuse(result, PinRefusal::NotAProject, errorMessage);
            }

            std::string file = newPin.file;
            // A keyed sub-object (room:hall/pillars/pillar2): its owner's id, and the address among the owner file's
            // keyed sub-objects (the keys of format 1; a key not written yet reads as the one the core gives).
            const size_t slash = newPin.on.find('/');
            const std::string owner = newPin.on.substr(0, slash);

            if (slash != std::string::npos)
            {
                bool found = false;

                for (const std::string &name : filesWithId(project, owner))
                {
                    if (file.empty() || file == name)
                    {
                        const std::string schemaFile = project.files.at(name).schema;

                        for (const std::string &address : subObjectAddresses(project.document(name), schemaFile))
                        {
                            found = found || address == newPin.on;
                        }
                    }
                }

                if (!found)
                {
                    return refuse(result, PinRefusal::BadRequest, "nothing in the project has the sub-object "
                        + newPin.on + " (a sub-object is named by its owner's id and the path of keys, as "
                        "room:hall/pillars/pillar2)");
                }
            }

            if (!newPin.on.empty())
            {
                const std::vector<std::string> files = filesWithId(project, owner);

                if (!file.empty() && std::find(files.begin(), files.end(), file) == files.end())
                {
                    return refuse(result, PinRefusal::BadRequest, "nothing in " + file + " has the id " + newPin.on);
                }

                if (files.empty())
                {
                    return refuse(result, PinRefusal::BadRequest, "nothing in the project has the id " + newPin.on);
                }

                // Ids are unique per file: the file is named where the id alone does not say which object.
                if (file.empty() && files.size() > 1)
                {
                    return refuse(result, PinRefusal::BadRequest, "the id " + newPin.on + " is in " + files[0]
                        + " and " + files[1] + ": name the one meant with `file`");
                }

                if (files.size() == 1)
                {
                    file.clear();
                }
            }

            pinId = nextPinId(document);
            text = newPin.text;
            YAML::Node pin(YAML::NodeType::Map);
            pin["id"] = pinId;
            pin["text"] = textNode(newPin.text);

            if (!newPin.on.empty())
            {
                pin["on"] = newPin.on;
            }

            if (!file.empty())
            {
                pin["file"] = file;
            }

            if (newPin.at)
            {
                for (const double value : *newPin.at)
                {
                    pin["at"].push_back(numberNode(value, 0));
                }
            }

            pin["source"] = newPin.source.empty() ? std::string("agent") : newPin.source;

            if (!newPin.world.empty())
            {
                pin["world"] = textNode(newPin.world);
            }

            if (!newPin.map.empty())
            {
                pin["map"] = textNode(newPin.map);
            }

            if (newPin.position)
            {
                YAML::Node pose(YAML::NodeType::Map);

                for (const double value : *newPin.position)
                {
                    pose["position"].push_back(numberNode(value, 3));
                }

                if (newPin.yawRadians)
                {
                    pose["yaw_radians"] = numberNode(*newPin.yawRadians, 4);
                }

                if (newPin.pitchDegrees)
                {
                    pose["pitch_degrees"] = numberNode(*newPin.pitchDegrees, 3);
                }

                if (newPin.headingYawUnits)
                {
                    pose["heading_yaw_units"] = *newPin.headingYawUnits;
                }

                pin["pose"] = pose;
            }

            if (!newPin.picture.empty())
            {
                const std::string relative = ".oymap/pins/pictures/" + pictureStem(pinId)
                    + newPin.picture.extension();

                if (!writePicture(newPin.picture, projectRoot / relative, errorMessage))
                {
                    return refuse(result, PinRefusal::BadRequest, errorMessage);
                }

                pin["picture"] = relative;
            }

            pin["author"] = textNode(newPin.author.empty() ? std::string("agent") : newPin.author);
            pin["created"] = textNode(newPin.created.empty() ? localTimestamp() : newPin.created);
            const bool now = newPin.revision.empty() && newPin.stampRevision;
            const std::string pinRevision = now ? revision : newPin.revision;
            const std::string pinLock = now ? projectLockHash(projectRoot) : newPin.lockHash;

            if (!pinRevision.empty())
            {
                pin["revision"] = textNode(pinRevision);
            }

            if (!pinLock.empty())
            {
                pin["lock_hash"] = textNode(pinLock);
            }

            pin["status"] = "open";

            if (!newPin.from.empty())
            {
                pin["from"] = textNode(newPin.from);
            }

            document["pins"].push_back(pin);
            return true;
        });
}

bool claimPin(
    const std::filesystem::path &projectRoot,
    const std::string &pinId,
    const std::string &by,
    bool force,
    PinResult &result)
{
    return changePins(projectRoot, "claim", by, result,
        [&](YAML::Node &document, std::string &changedId, std::string &)
        {
            changedId = pinId;
            const int index = findPin(document, pinId);

            if (index < 0)
            {
                return refuse(result, PinRefusal::NoSuchPin, "the project has no pin " + pinId);
            }

            if (by.empty())
            {
                return refuse(result, PinRefusal::BadRequest, "a claim needs who takes the pin (agent:<name>)");
            }

            YAML::Node pin = document["pins"][static_cast<size_t>(index)];
            const std::string status = statusOf(pin);
            const std::string holder = textOf(pin, "claimed_by");

            if (status != "open" && status != "claimed")
            {
                return refuse(result, PinRefusal::WrongState, pinId + " is " + status
                    + ": only an open pin is claimed (reopen it first)");
            }

            if (status == "claimed" && holder != by && !force)
            {
                return refuse(result, PinRefusal::WrongState, pinId + " is claimed by " + holder
                    + " (take it over with force)");
            }

            pin["status"] = "claimed";
            pin["claimed_by"] = textNode(by);
            return true;
        });
}

bool actOnPin(
    const std::filesystem::path &projectRoot,
    const std::string &pinId,
    PinAction action,
    const std::string &author,
    const std::string &text,
    const std::vector<PinPicture> &pictures,
    PinResult &result)
{
    const char *pActionName = action == PinAction::Reply ? "reply"
        : action == PinAction::Resolve                  ? "resolve"
        : action == PinAction::Accept                   ? "accept"
        : action == PinAction::Reopen                   ? "reopen"
                                                        : "decline";
    return changePins(projectRoot, pActionName, author, result,
        [&](YAML::Node &document, std::string &changedId, std::string &loggedText)
        {
            changedId = pinId;
            loggedText = text;
            const int index = findPin(document, pinId);

            if (index < 0)
            {
                return refuse(result, PinRefusal::NoSuchPin, "the project has no pin " + pinId);
            }

            if (author.empty())
            {
                return refuse(result, PinRefusal::BadRequest, "say who answers (user, or agent:<name>)");
            }

            YAML::Node pin = document["pins"][static_cast<size_t>(index)];
            const std::string status = statusOf(pin);
            std::string newStatus;

            switch (action)
            {
            case PinAction::Reply:
                if (text.empty() && pictures.empty())
                {
                    return refuse(result, PinRefusal::BadRequest, "a reply needs a text or a picture");
                }

                break;

            case PinAction::Resolve:
                if (status != "open" && status != "claimed")
                {
                    return refuse(result, PinRefusal::WrongState, pinId + " is " + status
                        + ": only an open or claimed pin is resolved");
                }

                if (status == "claimed" && textOf(pin, "claimed_by") != author)
                {
                    return refuse(result, PinRefusal::WrongState, pinId + " is claimed by "
                        + textOf(pin, "claimed_by") + ", not " + author);
                }

                if (text.empty())
                {
                    return refuse(result, PinRefusal::BadRequest, "say what was done (a reply text) when resolving");
                }

                newStatus = "resolved";
                break;

            case PinAction::Accept:
                if (status != "resolved")
                {
                    return refuse(result, PinRefusal::WrongState, pinId + " is " + status
                        + ": only a resolved pin is accepted");
                }

                newStatus = "accepted";
                break;

            case PinAction::Reopen:
                if (status != "resolved" && status != "accepted" && status != "declined")
                {
                    return refuse(result, PinRefusal::WrongState, pinId + " is " + status + ": it is open already");
                }

                newStatus = "open";
                break;

            case PinAction::Decline:
                if (status == "accepted" || status == "declined")
                {
                    return refuse(result, PinRefusal::WrongState, pinId + " is " + status + " already");
                }

                if (text.empty())
                {
                    return refuse(result, PinRefusal::BadRequest, "say why the pin is declined (a reply text)");
                }

                newStatus = "declined";
                break;
            }

            Project project;
            std::string revision;
            std::string errorMessage;

            if (!currentRevision(projectRoot, project, revision, errorMessage))
            {
                return refuse(result, PinRefusal::NotAProject, errorMessage);
            }

            if (!text.empty() || !pictures.empty() || action != PinAction::Reply)
            {
                YAML::Node reply = replyNode(author, text, revision, newStatus);
                const size_t replyNumber = childOf(pin, "replies").IsDefined() ? pin["replies"].size() + 1 : 1;
                size_t pictureNumber = 0;

                for (const PinPicture &picture : pictures)
                {
                    ++pictureNumber;
                    const std::string relative = ".oymap/pins/pictures/" + pictureStem(pinId) + "-r"
                        + std::to_string(replyNumber) + (pictureNumber > 1 ? "-" + std::to_string(pictureNumber) : "")
                        + picture.extension();

                    if (!writePicture(picture, projectRoot / relative, errorMessage))
                    {
                        return refuse(result, PinRefusal::BadRequest, errorMessage);
                    }

                    reply["pictures"].push_back(relative);
                }

                pin["replies"].push_back(reply);
            }

            if (!newStatus.empty())
            {
                pin["status"] = newStatus;

                if (newStatus == "open")
                {
                    pin.remove("claimed_by");
                }
            }

            return true;
        });
}

bool keepPinPicture(const std::filesystem::path &projectRoot, const std::string &pinId, PinResult &result)
{
    return changePins(projectRoot, "keep", "user", result,
        [&](YAML::Node &document, std::string &changedId, std::string &)
        {
            changedId = pinId;
            const int index = findPin(document, pinId);

            if (index < 0)
            {
                return refuse(result, PinRefusal::NoSuchPin, "the project has no pin " + pinId);
            }

            YAML::Node pin = document["pins"][static_cast<size_t>(index)];
            const std::string picture = textOf(pin, "picture");

            if (picture.empty())
            {
                return refuse(result, PinRefusal::BadRequest, pinId + " has no picture");
            }

            const std::string kept = "review/pictures/" + pictureStem(pinId)
                + std::filesystem::path(picture).extension().string();
            std::string errorMessage;

            if (!copyPicture(projectRoot / picture, projectRoot / kept, errorMessage))
            {
                return refuse(result, PinRefusal::BadRequest, errorMessage + " (the picture is not on this machine)");
            }

            pin["picture"] = kept;
            pin["keep"] = true;
            return true;
        });
}

std::vector<std::filesystem::path> findProjects(const std::filesystem::path &root, int depth)
{
    std::vector<std::filesystem::path> found;
    std::error_code error;

    if (!std::filesystem::is_directory(root, error))
    {
        return found;
    }

    if (std::filesystem::is_regular_file(root / "project.yml", error))
    {
        found.push_back(root);
        return found;
    }

    if (depth <= 0)
    {
        return found;
    }

    std::vector<std::filesystem::path> children;

    for (const std::filesystem::directory_entry &entry : std::filesystem::directory_iterator(root, error))
    {
        const std::string name = entry.path().filename().string();

        if (entry.is_directory(error) && !entry.is_symlink(error) && name != ".oymap" && name != "build"
            && name != "node_modules" && name.front() != '.')
        {
            children.push_back(entry.path());
        }
    }

    std::sort(children.begin(), children.end());

    for (const std::filesystem::path &child : children)
    {
        for (const std::filesystem::path &project : findProjects(child, depth - 1))
        {
            found.push_back(project);
        }
    }

    return found;
}

namespace
{
std::filesystem::path canonicalOr(const std::filesystem::path &path)
{
    std::error_code error;
    const std::filesystem::path canonical = std::filesystem::weakly_canonical(std::filesystem::absolute(path), error);
    return error ? path : canonical;
}

// The map file a project builds or overlays ("6d01.blv"), and its world.
struct ProjectMap
{
    std::string given;
    std::filesystem::path folder;
    std::string map;
    std::string world;
};

std::optional<ProjectMap> projectMapOf(const std::string &given)
{
    std::string text;
    const std::filesystem::path folder = canonicalOr(given);

    if (!readTextFile(folder / "project.yml", text))
    {
        return std::nullopt;
    }

    try
    {
        const YAML::Node card = YAML::Load(text);
        ProjectMap found;
        found.given = given;
        found.folder = folder;
        found.world = textOf(card, "world");
        const std::string base = textOf(card, "base");
        const std::string kind = textOf(card, "kind");
        std::error_code error;
        const bool outdoor = kind == "outdoor" || std::filesystem::exists(folder / "sketch.yml", error);
        found.map = !base.empty() ? base : textOf(card, "id") + (outdoor ? ".odm" : ".blv");
        return found;
    }
    catch (const YAML::Exception &)
    {
        return std::nullopt;
    }
}

std::string lower(std::string text)
{
    std::transform(text.begin(), text.end(), text.begin(), [](unsigned char letter)
    {
        return static_cast<char>(std::tolower(letter));
    });
    return text;
}
}

bool importPinInbox(
    const std::filesystem::path &inbox,
    const InboxOptions &options,
    InboxResult &result,
    std::string &errorMessage)
{
    result = {};
    std::error_code error;

    if (!std::filesystem::is_directory(inbox, error))
    {
        errorMessage = "no inbox folder at " + inbox.string();
        return false;
    }

    std::vector<ProjectMap> candidates;

    for (const std::string &given : options.projects)
    {
        if (const std::optional<ProjectMap> found = projectMapOf(given))
        {
            candidates.push_back(*found);
        }
    }

    std::vector<std::filesystem::path> files;

    for (const std::filesystem::directory_entry &entry : std::filesystem::directory_iterator(inbox, error))
    {
        if (entry.is_regular_file(error) && entry.path().extension() == ".yml")
        {
            files.push_back(entry.path());
        }
    }

    std::sort(files.begin(), files.end());

    for (const std::filesystem::path &path : files)
    {
        const std::string fileName = path.filename().string();
        std::string text;
        YAML::Node pinFile;

        try
        {
            if (!readTextFile(path, text))
            {
                throw YAML::Exception(YAML::Mark::null_mark(), "unreadable");
            }

            pinFile = YAML::Load(text);
        }
        catch (const YAML::Exception &exception)
        {
            result.skipped.push_back({fileName, std::string("not a pin file: ") + exception.what()});
            continue;
        }

        if (!pinFile.IsMap() || textOf(pinFile, "text").empty() || textOf(pinFile, "format") != "1")
        {
            result.skipped.push_back({fileName, "not a pin file of format 1 (format, text)"});
            continue;
        }

        // The project: the one the pin names (from the map's <stem>.studio.yml), else the one whose map it is.
        const std::string named = textOf(pinFile, "project");
        const std::string map = lower(textOf(pinFile, "map"));
        const std::string world = textOf(pinFile, "world");
        std::optional<ProjectMap> target;
        std::string matchedBy;

        if (!named.empty())
        {
            const std::filesystem::path namedFolder = canonicalOr(named);

            for (const ProjectMap &candidate : candidates)
            {
                if (candidate.folder == namedFolder)
                {
                    target = candidate;
                }
            }

            if (!target && options.trustPinProject)
            {
                target = projectMapOf(named);
            }

            matchedBy = "studio file";

            if (!target)
            {
                result.skipped.push_back({fileName, "the pin names the project " + named + (options.trustPinProject
                    ? std::string(", which is not a project folder here") : std::string(", which is not one of the "
                        "projects given"))});
                continue;
            }
        }
        else
        {
            std::vector<ProjectMap> matches;

            for (const ProjectMap &candidate : candidates)
            {
                if (lower(candidate.map) == map && (world.empty() || candidate.world.empty() || candidate.world == world))
                {
                    matches.push_back(candidate);
                }
            }

            if (matches.size() != 1)
            {
                std::string names;

                for (const ProjectMap &match : matches)
                {
                    names += (names.empty() ? "" : ", ") + match.given;
                }

                result.skipped.push_back({fileName, matches.empty()
                    ? "no project builds or overlays " + textOf(pinFile, "map") + " (the map had no <stem>.studio.yml: "
                        "install it with oymap install, or name the project with --project)"
                    : "several projects build " + textOf(pinFile, "map") + ": " + names + "; name the one meant with "
                        "--project"});
                continue;
            }

            target = matches.front();
            matchedBy = "map";
        }

        const std::string pictureName = textOf(pinFile, "picture");
        const std::filesystem::path picturePath = pictureName.empty() ? std::filesystem::path()
            : inbox / std::filesystem::path(pictureName).filename();
        const bool hasPicture = !pictureName.empty() && std::filesystem::is_regular_file(picturePath, error);

        if (!pictureName.empty() && !hasPicture)
        {
            const std::filesystem::file_time_type written = std::filesystem::last_write_time(path, error);
            const auto age = std::filesystem::file_time_type::clock::now() - written;

            if (!error && age < std::chrono::seconds(options.pictureWaitSeconds))
            {
                result.skipped.push_back({fileName, "waiting for its picture (" + pictureName + ")"});
                continue;
            }
        }

        InboxImported imported;
        imported.file = fileName;
        imported.project = target->given;
        imported.matchedBy = matchedBy;
        imported.picture = hasPicture;

        if (options.dryRun)
        {
            result.imported.push_back(imported);
            continue;
        }

        NewPin pin;
        pin.text = textOf(pinFile, "text");
        pin.source = textOf(pinFile, "source").empty() ? std::string("game") : textOf(pinFile, "source");
        pin.author = textOf(pinFile, "author").empty() ? std::string("user") : textOf(pinFile, "author");
        pin.world = world;
        pin.map = textOf(pinFile, "map");
        pin.created = textOf(pinFile, "created");
        // The revision and lock the installed map was built from (the studio file); none for a matched map.
        pin.revision = textOf(pinFile, "revision");
        pin.lockHash = textOf(pinFile, "lock_hash");
        pin.stampRevision = false;
        pin.from = fileName;
        const YAML::Node pose = childOf(pinFile, "pose");

        try
        {
            if (childOf(pose, "position").IsSequence() && pose["position"].size() == 3)
            {
                pin.position = std::vector<double>{pose["position"][0].as<double>(), pose["position"][1].as<double>(),
                    pose["position"][2].as<double>()};
            }

            if (childOf(pose, "yaw_radians").IsDefined())
            {
                pin.yawRadians = pose["yaw_radians"].as<double>();
            }

            if (childOf(pose, "pitch_degrees").IsDefined())
            {
                pin.pitchDegrees = pose["pitch_degrees"].as<double>();
            }

            if (childOf(pose, "heading_yaw_units").IsDefined())
            {
                pin.headingYawUnits = pose["heading_yaw_units"].as<int>();
            }
        }
        catch (const YAML::Exception &exception)
        {
            result.skipped.push_back({fileName, std::string("its pose is not numbers: ") + exception.what()});
            continue;
        }

        if (hasPicture)
        {
            pin.picture = picturePath;
        }

        PinResult added;

        if (!addPin(target->folder, pin, added))
        {
            result.skipped.push_back({fileName, "not added to " + target->given + ": " + added.message});
            continue;
        }

        imported.pin = textOf(added.pin, "id");
        std::string moveError;
        // The picture now lives beside the project's pins (addPin copied it); the pin file goes to imported/ so the
        // inbox keeps a record and a second import does not file it twice.
        std::error_code removeError;

        if ((hasPicture && !std::filesystem::remove(picturePath, removeError))
            || !moveFile(path, inbox / "imported" / fileName, moveError))
        {
            result.skipped.push_back({fileName, "filed as " + imported.pin + " in " + target->given
                + ", but the inbox files could not be moved: " + (moveError.empty() ? removeError.message()
                    : moveError)});
            continue;
        }

        result.imported.push_back(imported);
    }

    return true;
}

std::string pinsTourText(
    const YAML::Node &document,
    const std::vector<std::string> &pinIds,
    const std::vector<std::string> &statuses,
    const std::filesystem::path &outputDirectory,
    std::vector<std::string> &skipped)
{
    YAML::Node tour(YAML::NodeType::Map);
    tour["output_dir"] = textNode(outputDirectory.generic_string());
    tour["settle_seconds"] = 1.5;
    tour["exit"] = true;
    tour["shots"] = YAML::Node(YAML::NodeType::Sequence);
    const std::set<std::string> wantedIds(pinIds.begin(), pinIds.end());
    const std::set<std::string> wantedStatuses(statuses.begin(), statuses.end());

    for (const YAML::Node &pin : childOf(document, "pins"))
    {
        const std::string id = textOf(pin, "id");

        if (!wantedIds.empty() ? !wantedIds.contains(id)
                               : !wantedStatuses.empty() && !wantedStatuses.contains(statusOf(pin)))
        {
            continue;
        }

        const YAML::Node pose = childOf(pin, "pose");

        if (!childOf(pose, "position").IsSequence() || pose["position"].size() != 3)
        {
            skipped.push_back(id);
            continue;
        }

        YAML::Node shot(YAML::NodeType::Map);
        shot["name"] = pictureStem(id);
        YAML::Node position(YAML::NodeType::Sequence);

        for (size_t axis = 0; axis < 3; ++axis)
        {
            position.push_back(pose["position"][axis]);
        }

        position.SetStyle(YAML::EmitterStyle::Flow);
        shot["position"] = position;
        shot["yaw"] = childOf(pose, "yaw_radians").IsDefined() ? YAML::Node(pose["yaw_radians"]) : numberNode(0, 0);
        // The pin keeps `loc`'s degrees; a tour takes radians.
        const double pitchDegrees = childOf(pose, "pitch_degrees").IsDefined() ? pose["pitch_degrees"].as<double>()
                                                                               : 0.0;
        shot["pitch"] = numberNode(pitchDegrees * 3.14159265358979323846 / 180.0, 6);
        tour["shots"].push_back(shot);
    }

    YAML::Emitter emitter;
    emitter << tour;
    return std::string("# A screenshot tour at the pins' poses (oymap pins tour): run it on the pins' map with\n"
                       "# --set debug.screenshot_tour_path=<this file> (tools/RUN_GAME.md, \"Gameplay screenshot tours\").\n")
        + emitter.c_str() + "\n";
}

bool renamePinAnchors(
    const std::filesystem::path &projectRoot,
    const std::vector<std::pair<std::string, std::string>> &renames,
    std::vector<std::string> &renamed,
    std::string &errorMessage)
{
    renamed.clear();
    std::error_code fileError;

    if (renames.empty() || !std::filesystem::is_regular_file(projectRoot / PinsFile, fileError))
    {
        return true;
    }

    YAML::Node document;

    if (!readPinsDocument(projectRoot, document, errorMessage))
    {
        return false;
    }

    YAML::Node pins = childOf(document, "pins");

    for (size_t index = 0; pins.IsDefined() && pins.IsSequence() && index < pins.size(); ++index)
    {
        YAML::Node pin = pins[index];
        std::string on = textOf(pin, "on");

        if (on.empty())
        {
            continue;
        }

        const std::string was = on;

        // In order: a later rename may name what an earlier one made. An anchor follows its object and the
        // object's sub-objects (`from` itself, or `from/...`).
        for (const std::pair<std::string, std::string> &rename : renames)
        {
            if (on == rename.first)
            {
                on = rename.second;
            }
            else if (on.size() > rename.first.size() && on.compare(0, rename.first.size(), rename.first) == 0
                && on[rename.first.size()] == '/')
            {
                on = rename.second + on.substr(rename.first.size());
            }
        }

        if (on != was)
        {
            pin["on"] = on;
            renamed.push_back(textOf(pin, "id") + ": " + was + " -> " + on);
        }
    }

    if (renamed.empty())
    {
        return true;
    }

    const int counter = (childOf(document, "counter").IsDefined() ? document["counter"].as<int>() : 0) + 1;
    document["counter"] = counter;
    std::string lines;

    for (const std::string &line : renamed)
    {
        lines += (lines.empty() ? "" : "; ") + line;
    }

    return writePinsDocument(projectRoot, document, errorMessage)
        && appendPinsLog(projectRoot, counter, "rename", "", "core", "", lines, errorMessage);
}
}
