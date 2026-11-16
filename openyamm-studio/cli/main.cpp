#include "cli/Commands.h"
#include "cli/GroundCommands.h"
#include "cli/Rpc.h"

#include "core/Json.h"

#include <yaml-cpp/yaml.h>

#include <cerrno>
#include <cstdlib>
#include <cstring>
#include <filesystem>
#include <iostream>
#include <iterator>
#include <sstream>
#include <string>
#include <vector>

#ifndef __EMSCRIPTEN__
#include <unistd.h>
#endif

using OpenYAMM::Studio::callRpcMethod;

namespace
{
struct Command
{
    const char *pName;
    const char *pUsage;
    const char *pSummary;
    int (*pRun)(const std::vector<std::string> &arguments);
};

const Command Commands[] = {
    {"export", "export <map.odm|map.blv | project> [--world <world> --assets <root> [--mount <folder>]] [--summary] "
               "[--pretty] [--out <file>]",
        "a shipped or built map as JSON; with a world and an asset root also its door records",
        OpenYAMM::Studio::runExport},
    {"audit",
        "audit <map file> --world <world> --assets <asset root> [--reach] [--solve] [--json] [--original <map>] "
        "[--strict]",
        "a shipped or installed map as the game reads it: overview and wiring checks", OpenYAMM::Studio::runAudit},
    {"things", "things <map file> --world <world> | <project> --assets <asset root> [--json]",
        "every interactive thing of an indoor or outdoor map: kind, textures, what it changes, where a player uses "
        "it from, faces over it (indoors)", OpenYAMM::Studio::runThings},
    {"flow", "flow <map file> --world <world> --assets <asset root> [--event <number>]",
        "what each event handler tests and does, found by running it in a sandbox", OpenYAMM::Studio::runFlow},
    {"metrics", "metrics <map file> --world <world> --assets <asset root> [--reach] [--out <file>]",
        "the comparison metrics of a map (structure, scale, mechanisms, density, palette, play) as JSON",
        OpenYAMM::Studio::runMetrics},
    {"solve", "solve <map file> --world <world> --assets <asset root> [--json]",
        "the order an indoor map opens up from its start: which events open what, and what they need",
        OpenYAMM::Studio::runSolve},
    {"compare", "compare <original map file> --world <world> --with <project | second map file> --assets <asset root> "
                "[--out <folder>] [--step <units>] [--json] [--without <list>]",
        "how alike two indoor maps in one coordinate frame are: rays from every stand point, scores, worst points, "
        "and with --out every differing point by sector (points.json)",
        OpenYAMM::Studio::runCompare},
    {"render", "render <map file> --world <world> --assets <asset root> --out <file.png> [--view plan|iso] "
               "[--size <pixels>] [--no-labels]",
        "a labelled drawing of a map from its data: sectors, doors, portals, start, spawn points",
        OpenYAMM::Studio::runRender},
    {"render-sketch", "render-sketch <project> --out <file.png> [--size <pixels>] [--region <x,y,width,depth>] "
                      "[--no-labels]",
        "the plan picture of an outdoor project's sketch.yml: land, water, roads, districts, plots, points, areas",
        OpenYAMM::Studio::runRenderSketch},
    {"scene-roundtrip", "scene-roundtrip <scene.yml> [more files ...]",
        "check that the core's YAML writer loses nothing of these scene files", OpenYAMM::Studio::runSceneRoundTrip},
    {"probe", "probe <map file> --world <world> --assets <asset root> --from x,y,z --to x,y,z [--doors-open]",
        "why the party can or cannot walk between two points of an indoor map", OpenYAMM::Studio::runProbe},
    {"edit", "edit <project> --ops <file|-> [--dry-run] [--expect <revision>] [--rebase] [--allow-issues] "
             "[--author <user|agent:name>] [--label <text>] [--merge-key <text>] [--json]",
        "apply operations (add, set, replace, remove, set_value, patch, rename) as one checked transaction",
        OpenYAMM::Studio::runEdit},
    {"record", "record <project> --author <agent:name|user> [--label <what>] [--json]",
        "put an author and a label on the edits made outside the tool (run it after a generator run)",
        OpenYAMM::Studio::runRecord},
    {"pins", "pins list|show|import|add|claim|reply|resolve|accept|reopen|decline|keep|tour ... (oymap pins for more)",
        "the review pins: the game's pins filed from the inbox, claimed, answered with pictures, accepted",
        OpenYAMM::Studio::runPins},
    {"lock", "lock prune <project> [--dry-run] [--json]",
        "drop the id lock's entries of ids the project no longer has (builds keep them)", OpenYAMM::Studio::runLock},
    {"mod", "mod pack <project>... --id <mod> --out <folder> --assets <root> [--name <n>] [--version <v>] [--author <a>]"
            " [--maps <first>-<last>] [--build] | mod map-number --world <w> --assets <root> [--mods <folder>] [--mod <id>]"
            " [<project>...] | mod install <mod folder> --mods <mods folder> --assets <root> [--layout merged|named]"
            " | mod disable|enable <id> --mods <mods folder> --assets <root> | mod list --mods <mods folder>",
        "named mods and sharing: builds packed into a mod folder, installed into a game's mods folder, switched off and "
        "on; a free map number from the mod's or the world's declared range", OpenYAMM::Studio::runMod},
    {"status", "status <project> [--json]",
        "the project's revision, edits made outside the tool, and its history", OpenYAMM::Studio::runStatus},
    {"undo", "undo <project>", "revert the latest change (an entry of its own; anybody's, outside edits too)",
        OpenYAMM::Studio::runUndo},
    {"redo", "redo <project>", "apply again the change last undone", OpenYAMM::Studio::runRedo},
    {"revert", "revert <project> <sequence> [--force] [--allow-issues] [--author <a>]",
        "revert one history entry object by object (an undo of any entry)", OpenYAMM::Studio::runRevert},
    {"protect", "protect <project> [--clear]",
        "a person marks the project as edited by hand: agents change it only by operations", OpenYAMM::Studio::runProtect},
    {"migrate", "migrate <project> [--dry-run]",
        "write the files in canonical form with the keys of format 1, as one history entry", OpenYAMM::Studio::runMigrate},
    {"query", "query <project> [--id <id> | --list <key>]",
        "read a project: its summary, one object, or one list", OpenYAMM::Studio::runQuery},
    {"assets", "assets <text> --assets <asset root> [--world <w>] [--kind decoration|texture] [--limit <n>]",
        "search the asset catalogue: decorations and face textures with their sizes", OpenYAMM::Studio::runAssets},
    {"script-reference", "script-reference --assets <asset root> [--world <w>]",
        "what a hand-written handler may use: the scripts' helpers, selectors and enumerations",
        OpenYAMM::Studio::runScriptReference},
    {"event-functions", "event-functions",
        "the names of the functions the game gives event scripts (evt.<name>)", OpenYAMM::Studio::runEventFunctions},
    {"fmt", "fmt <project> [--check]",
        "rewrite a project's files in canonical form", OpenYAMM::Studio::runFmt},
    {"reads", "reads <outdoor project> [--assets <asset root>] [--land] [--json]",
        "the words of a sketch's objects its build never reads (the read record; --json: every word)",
        OpenYAMM::Studio::runReads},
    {"validate", "validate <project> [--assets <asset root>] [--mount <folder>] [--json]",
        "check a project's files against the schemas and each other", OpenYAMM::Studio::runValidate},
    {"build", "build <project> [--out <dir>] [--assets <asset root>] [--mount <folder>] [--dry-run] [--json]",
        "compile a project to its map files (BLV, scene, Lua)", OpenYAMM::Studio::runBuild},
    {"new",
        "new <project folder> --id <map stem> --name <name> [--world <w>] [--reference <shipped map>] "
        "[--stats-id <n>]",
        "an empty indoor project to draw rooms into: a map card, one theme, no rooms yet",
        OpenYAMM::Studio::runNew},
    {"import", "import <map file> --world <world> --assets <asset root> --to <project folder>",
        "a shipped map as an overlay project: map card, derived room graph, the map's numbers under stable ids",
        OpenYAMM::Studio::runImport},
    {"install", "install <project> --root <scratch asset root> | --mount <folder> --assets <asset root> [--build <dir>]",
        "copy a built map into a scratch asset root or a mount folder, register it in map_stats.txt and write "
        "<stem>.studio.yml beside it (the project, revision and lock hash the game's pins carry)",
        OpenYAMM::Studio::runInstall},
    {"build-map", "build-map <map.yml-or-scene.yml> [--asset-root <dir>] [--world <id>]",
        "legacy outdoor build (the editor's --headless-build-map, same inputs and files)",
        OpenYAMM::Studio::runBuildMap},
    {"compile-indoor", "compile-indoor <source.glb> <geometry.yml> <output.blv> [doors.yml] [face_groups.yml]",
        "legacy indoor build (same inputs and output as mm9_compile_indoor_source)",
        OpenYAMM::Studio::runCompileIndoor},
    {"schema", "schema [<name>]",
        "list the project format's schemas, or print one", OpenYAMM::Studio::runSchema},
    {"ground", "ground <map.blv> --ground <ground.yml> --world <w> --assets <root> --out <folder> [--stem <stem>] "
               "[--world-materials <world.yml>] [--exclude <faces file>]",
        "an open-air map's ground weights and material file from a `ground` block over a built BLV (the build's "
        "rasteriser outside a project)", OpenYAMM::Studio::runGround},
};

void printUsage()
{
    std::cout << "oymap: OpenYAMM Map Studio command line\n\nusage: oymap <command> [arguments]\n\n"
              << "  oymap serve [--assets <asset root>] [--mount <folder>]\n      the core as a long-lived process: JSON-RPC on standard "
                 "input and output (the request list, schema/rpc/)\n"
              << "  oymap call <method> [<params JSON> | -] [--assets <asset root>]\n      one method of the request "
                 "list\n"
              << "  oymap studio [host options]\n      the browser editor's local host (Node; prints the address to "
                 "open)\n"
              << "  oymap mcp [host options]\n      MCP for agents on standard input and output, relayed to the "
                 "running studio host (else served in that process)\n";

    for (const Command &command : Commands)
    {
        std::cout << "  oymap " << command.pUsage << "\n      " << command.pSummary << "\n";
    }
}

int runCommand(const std::string &name, const std::vector<std::string> &arguments, bool &known)
{
    for (const Command &command : Commands)
    {
        if (name == command.pName)
        {
            known = true;

            try
            {
                return command.pRun(arguments);
            }
            catch (const std::exception &exception)
            {
                std::cerr << "oymap " << command.pName << ": " << exception.what() << "\n";
                return 1;
            }
        }
    }

    known = false;
    return 2;
}

// `oymap serve`: the core as a long-lived process for the host (PLAN.md section 8). JSON-RPC 2.0, one message a
// line, on standard input and output. Methods: every method of the typed request list (schema/rpc/, cli/Rpc.h),
// and the command-line bridge the MCP host still uses until it moves onto the list (S5a2):
//   run       {command, args: [...]}  any oymap command; the result is {exit, stdout, stderr}
//   commands  {}                      the commands with their usage and summary
//   ping      {}
// The process keeps what it read of each project between calls (core/Service.h), checked against the files on every
// call: the files are the state, so the host may restart it at any time.
int runServe()
{
    std::string line;

    while (std::getline(std::cin, line))
    {
        if (line.empty())
        {
            continue;
        }

        OpenYAMM::Studio::JsonWriter response;
        response.beginObject();
        response.field("jsonrpc", "2.0");

        try
        {
            const YAML::Node request = YAML::Load(line);
            const YAML::Node id = request["id"];
            const std::string method = request["method"] ? request["method"].Scalar() : std::string();
            const YAML::Node params = request["params"];

            // Every method but the three of the command-line bridge is one of the typed request list (an unknown one
            // is answered by it too): {"result": ...} or {"error": ...} after the id.
            if (method != "run" && method != "commands" && method != "ping")
            {
                const std::string answer = callRpcMethod(method, params);
                OpenYAMM::Studio::JsonWriter idWriter;

                if (id.IsDefined())
                {
                    idWriter.node(id);
                }
                else
                {
                    idWriter.null();
                }

                std::cout << "{\"jsonrpc\":\"2.0\",\"id\":" << idWriter.take() << "," << answer.substr(1) << std::endl;
                // With the answer out, what the core left for later (trees read back after an edit).
                OpenYAMM::Studio::rpcIdle();
                continue;
            }

            response.key("id");

            if (id.IsDefined())
            {
                response.node(id);
            }
            else
            {
                response.null();
            }

            if (method == "ping")
            {
                response.field("result", "pong");
            }
            else if (method == "commands")
            {
                response.key("result");
                response.beginArray();

                for (const Command &command : Commands)
                {
                    response.beginObject();
                    response.field("name", command.pName);
                    response.field("usage", command.pUsage);
                    response.field("summary", command.pSummary);
                    response.endObject();
                }

                response.endArray();
            }
            else if (method == "run" && params && params["command"])
            {
                std::vector<std::string> arguments;

                if (params["args"])
                {
                    for (const YAML::Node &argument : params["args"])
                    {
                        arguments.push_back(argument.Scalar());
                    }
                }

                // The command writes to the streams as on the command line; here they are collected.
                std::ostringstream output;
                std::ostringstream errors;
                std::streambuf *pOutput = std::cout.rdbuf(output.rdbuf());
                std::streambuf *pErrors = std::cerr.rdbuf(errors.rdbuf());
                bool known = false;
                const int exitCode = runCommand(params["command"].Scalar(), arguments, known);
                std::cout.rdbuf(pOutput);
                std::cerr.rdbuf(pErrors);

                if (!known)
                {
                    response.key("error");
                    response.beginObject();
                    response.field("code", -32602);
                    response.field("message", "unknown oymap command '" + params["command"].Scalar() + "'");
                    response.endObject();
                }
                else
                {
                    response.key("result");
                    response.beginObject();
                    response.field("exit", exitCode);
                    response.field("stdout", output.str());
                    response.field("stderr", errors.str());
                    response.endObject();
                }
            }
            else
            {
                response.key("error");
                response.beginObject();
                response.field("code", -32601);
                response.field("message", "unknown method '" + method + "' (methods: run, commands, ping)");
                response.endObject();
            }
        }
        catch (const YAML::Exception &exception)
        {
            response.key("id");
            response.null();
            response.key("error");
            response.beginObject();
            response.field("code", -32700);
            response.field("message", std::string("not a JSON message: ") + exception.what());
            response.endObject();
        }

        response.endObject();
        std::cout << response.text() << std::endl;
    }

    return 0;
}
}

#ifndef __EMSCRIPTEN__
// `oymap studio` and `oymap mcp`: the host (host/src/host.mjs beside this binary's build folder, or OYMAP_HOST) run
// with Node, with this binary as its core unless --oymap is given. Returns only when Node could not be started.
int runHost(const char *pMode, int argc, char **argv)
{
    std::error_code error;
    const std::filesystem::path self = std::filesystem::canonical("/proc/self/exe", error);
    const char *pGiven = std::getenv("OYMAP_HOST");
    const std::filesystem::path script = pGiven != nullptr ? std::filesystem::path(pGiven)
        : self.parent_path().parent_path() / "host" / "src" / "host.mjs";

    if (!std::filesystem::is_regular_file(script, error))
    {
        std::cerr << "oymap " << pMode << ": no host at " << script.string() << " (set OYMAP_HOST)\n";
        return 1;
    }

    std::vector<std::string> arguments = {"node", script.string(), pMode};
    bool oymapGiven = false;

    for (int index = 2; index < argc; ++index)
    {
        oymapGiven = oymapGiven || std::strcmp(argv[index], "--oymap") == 0;
        arguments.emplace_back(argv[index]);
    }

    if (!oymapGiven && !self.empty())
    {
        arguments.emplace_back("--oymap");
        arguments.push_back(self.string());
    }

    std::vector<char *> pointers;

    for (std::string &argument : arguments)
    {
        pointers.push_back(argument.data());
    }

    pointers.push_back(nullptr);
    execvp("node", pointers.data());
    std::cerr << "oymap " << pMode << ": could not start node: " << std::strerror(errno) << "\n";
    return 1;
}
#endif

int main(int argc, char **argv)
{
    if (argc < 2 || std::strcmp(argv[1], "--help") == 0 || std::strcmp(argv[1], "help") == 0)
    {
        printUsage();
        return argc < 2 ? 2 : 0;
    }

#ifndef __EMSCRIPTEN__
    if (std::strcmp(argv[1], "studio") == 0 || std::strcmp(argv[1], "mcp") == 0)
    {
        return runHost(std::strcmp(argv[1], "mcp") == 0 ? "relay" : "studio", argc, argv);
    }
#endif

    // `oymap serve [--assets <root>] [--mount <folder>]`: the asset root and the mount of builds are the session's
    // (session.configure) from the start.
    if (std::strcmp(argv[1], "serve") == 0)
    {
        std::vector<std::string> arguments(argv + 2, argv + argc);
        std::string assetRoot;
        std::string mount;
        OpenYAMM::Studio::takeOption(arguments, "--assets", assetRoot);
        OpenYAMM::Studio::takeOption(arguments, "--mount", mount);

        if (!arguments.empty())
        {
            std::cerr << "usage: oymap serve [--assets <asset root>] [--mount <folder>]\n";
            return 2;
        }

        if (!assetRoot.empty() || !mount.empty())
        {
            std::string params = "{";

            if (!assetRoot.empty())
            {
                params += "\"asset_root\":" + OpenYAMM::Studio::jsonQuote(assetRoot);
            }

            if (!mount.empty())
            {
                params += std::string(assetRoot.empty() ? "" : ",") + "\"mount\":" + OpenYAMM::Studio::jsonQuote(mount);
            }

            const std::string answer = callRpcMethod("session.configure", params + "}");

            if (answer.rfind("{\"error\"", 0) == 0)
            {
                std::cerr << "oymap serve: " << answer << "\n";
                return 1;
            }
        }

        return runServe();
    }

    // `oymap call <method> [<params JSON> | -] [--assets <root>]`: one method of the request list from a shell.
    if (std::strcmp(argv[1], "call") == 0)
    {
        std::vector<std::string> arguments(argv + 2, argv + argc);
        const std::filesystem::path assetRoot = OpenYAMM::Studio::takeAssetRoot(arguments);

        if (arguments.empty() || arguments.size() > 2)
        {
            std::cerr << "usage: oymap call <method> [<params JSON> | -] [--assets <asset root>]\n";
            return 2;
        }

        if (!assetRoot.empty())
        {
            const std::string answer = callRpcMethod("session.configure",
                std::string("{\"asset_root\":") + OpenYAMM::Studio::jsonQuote(assetRoot.string()) + "}");

            if (answer.rfind("{\"error\"", 0) == 0)
            {
                std::cout << answer << "\n";
                return 1;
            }
        }

        std::string params = arguments.size() == 2 ? arguments[1] : std::string("{}");

        if (params == "-")
        {
            params.assign(std::istreambuf_iterator<char>(std::cin), std::istreambuf_iterator<char>());
        }

        const std::string answer = callRpcMethod(arguments[0], params);
        std::cout << answer << "\n";
        return answer.rfind("{\"result\"", 0) == 0 ? 0 : 1;
    }

    const std::vector<std::string> arguments(argv + 2, argv + argc);
    bool known = false;
    const int exitCode = runCommand(argv[1], arguments, known);

    if (known)
    {
        return exitCode;
    }

    std::cerr << "oymap: unknown command '" << argv[1] << "'\n";
    printUsage();
    return 2;
}
